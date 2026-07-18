"""Derive NYISO-native per-class offer-curve heat-rate multipliers from CAMPD CEMS.

The CEMS analogue of ``scripts/data/derive_dam_offer_hrmults.py``. ERCOT publishes
60-Day DAM offer curves, so its per-class ``committed / econ_low / econ_high``
multipliers are grounded in *submitted offers*. NYISO has no equivalent offer
disclosure, so the ``_NYISO_OFFER_CURVE`` bands had to borrow ERCOT's numbers
(e.g. the CC ``econ_high`` 1.21 "reach"). This script removes that cross-ISO
borrow by grounding each NYISO gas class in **NYISO's own measured marginal
heat rate**, taken from the unit-level CAMPD CEMS extracts
(``data/raw/campd-unit-level/{STATE}_{YEAR}.parquet``: grossLoad, heatInput,
opTime, unitType, primaryFuelInfo).

It is a REPORTING / derivation tool only: it reads CEMS and the fleet bin
crosswalk and writes a summary table. It is **default-off in every solve path**
and changes no other ISO's grounding — the only model edit it informs is the
hand-set ``_NYISO_OFFER_CURVE`` in ``scripts/run_calibration.py``, with each
band's derivation cited back to this script.

Method (measured, NOT fit to the LMP/volume residual)
-----------------------------------------------------
1. Map each CAMPD unit to its model class (CC_REGULAR / CC_CHP / ST_GAS /
   CT_PEAKER / ...) via the per-ISO fleet bin crosswalk
   (``data/raw/_processed-legacy/bin_assignments_<ISO>.csv``; ERCOT uses
   ``data/raw/reference/custom-bin-assignments.csv``). A CAMPD facility id is
   the EIA plant code; when one plant spans several model classes (e.g.
   Ravenswood CC + ST_GAS) the unit's CAMPD ``unitType`` picks the family
   (Combined cycle -> CC_*, Combustion turbine -> CT_*, boiler -> ST_*).

2. Per steady-state operating unit-hour (opTime ~ full hour, grossLoad > 0,
   heatInput > 0) the **average** heat rate is ``hr = heatInput / grossLoad``.
   Per unit, position each hour in the operating range by
   ``rel = (grossLoad - LSL) / (HSL - LSL)`` (LSL/HSL = robust low/high
   percentiles of the unit's own grossLoad), and bin into:
     * ``committed`` — at/below LSL min-gen (the must-run floor),
     * ``econ_low``  — rel <= 0.33 (bottom of the economic ramp),
     * ``econ_high`` — rel >= 0.67 (top of the economic ramp).

   Two heat-rate measures are reported per band:
     * ``avg``  — the average heat rate ``heatInput/grossLoad`` in the band.
       Average HR FALLS with load (the part-load no-load-fuel penalty), so it
       is informative for the LEVEL of a band but cannot by itself form the
       model's *rising* offer ramp.
     * ``marg`` — the **incremental / marginal** heat rate, the slope of the
       unit's input-output curve d(heatInput)/d(grossLoad) evaluated at the
       band-representative load from a per-unit quadratic fit. This is the
       short-run marginal energy cost basis and the true analogue of an offer
       curve's marginal-cost ramp; it is ~flat-to-gently-rising with load.

   Every band measure is expressed as a multiple of the class cap-weighted
   ``base_HR`` (the SAME class heat-rate the model later multiplies each
   plant's own HR against), so the output is apples-to-apples with
   ``_NYISO_OFFER_CURVE``.

3. Aggregate per class **capacity-weighted across units** (each unit weighted
   by its HSL), pooled across all available years (2023-2025). Report the
   weighted median plus p25/p75 for both measures.

Usage::

    uv run python scripts/data/derive_campd_marginal_hr.py --iso NYISO
    uv run python scripts/data/derive_campd_marginal_hr.py --iso NYISO --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import (
    CAMPD_BINS_CSV,
    PROCESSED_DIR,
    RAW_DATA_DIR,
    REFERENCE_DIR,
)
from market_sim.data.campd import states_for_iso

UNIT_LEVEL_DIR: Path = RAW_DATA_DIR / "campd-unit-level"

# The gas classes whose offer curve is hand-set per ISO. Other Plant_Groups
# (CT_CHP / ST_CHP / coal) are reported for context but not the tuning target.
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "ST_GAS", "CT_PEAKER")

PCTS = (0.25, 0.50, 0.75)

# Robust operating envelope percentiles: LSL = p3 of the unit's own grossLoad,
# HSL = p97 (trim startup ramps / sensor spikes without chopping the real range).
LSL_PCT, HSL_PCT = 3.0, 97.0
MIN_UNIT_HOURS = 200  # need enough steady-state points to fit an I/O curve
HR_LO, HR_HI = 3.0, 60.0  # plausible average-HR window (MMBtu/MWh) for gas/steam


def _bin_csv_path(iso: str) -> Path:
    """Per-ISO fleet bin crosswalk (ERCOT keeps the legacy reference filename)."""
    if iso.upper() == "ERCOT":
        return CAMPD_BINS_CSV
    return PROCESSED_DIR / f"bin_assignments_{iso.upper()}.csv"


def _unit_family(unit_type: str) -> str | None:
    """Map a CAMPD unitType to a model class family (CC / CT / ST), or None."""
    t = str(unit_type).lower()
    if "combined cycle" in t:
        return "CC"
    if "combustion turbine" in t:
        return "CT"
    if "boiler" in t or "fired" in t:  # tangentially-/wall-fired, CFB, other boiler
        return "ST"
    return None


def load_base_hr_and_class_map(
    iso: str,
) -> tuple[dict[str, float], pd.DataFrame]:
    """Return (class cap-weighted base_HR, per-plant class rows) from the bins."""
    bins = pd.read_csv(_bin_csv_path(iso))
    bins["Plant_Code"] = bins["Plant_Code"].astype(int)
    base_hr: dict[str, float] = {}
    for grp, d in bins.groupby("Plant_Group"):
        w = d["Nameplate_MW"].to_numpy(float)
        hr = d["Plant_Avg_HR_MMBtu_MWh"].to_numpy(float)
        m = np.isfinite(hr) & np.isfinite(w) & (w > 0) & (hr > 0)
        if m.any():
            base_hr[str(grp)] = float(np.average(hr[m], weights=w[m]))
    return base_hr, bins[["Plant_Code", "Plant_Group", "Nameplate_MW"]].copy()


def map_unit_class(
    facility_id: int,
    unit_type: str,
    plant_groups: dict[int, list[str]],
) -> str | None:
    """Resolve a CAMPD unit to one model Plant_Group.

    Single-class plants map directly. Multi-class plants are disambiguated by
    the unit's family (from ``unitType``): the plant's Plant_Group whose prefix
    matches the family (CC_*/CT_*/ST_*). Falls back to the single group when the
    family is ambiguous.
    """
    groups = plant_groups.get(facility_id)
    if not groups:
        return None
    if len(groups) == 1:
        return groups[0]
    fam = _unit_family(unit_type)
    if fam is None:
        return None
    matches = [g for g in groups if g.startswith(fam + "_")]
    if len(matches) == 1:
        return matches[0]
    if matches:  # >1 in the same family: pick the canonical regular/peaker class
        for pref in (f"{fam}_REGULAR", f"{fam}_PEAKER", f"{fam}_GAS"):
            if pref in matches:
                return pref
        return matches[0]
    return None


def load_campd(iso: str, years: tuple[int, ...]) -> pd.DataFrame:
    """Concatenate the steady-state CEMS operating hours for the ISO's states."""
    states = states_for_iso(iso)
    if not states:
        raise SystemExit(f"no CAMPD states registered for ISO {iso}")
    cols = ["facilityId", "unitId", "grossLoad", "heatInput", "opTime", "unitType"]
    frames = []
    for st in states:
        for y in years:
            p = UNIT_LEVEL_DIR / f"{st}_{y}.parquet"
            if not p.exists():
                continue
            df = pd.read_parquet(p, columns=cols)
            df["year"] = y
            frames.append(df)
    if not frames:
        raise SystemExit(f"no CAMPD unit-level parquet for {iso} {years}")
    camp = pd.concat(frames, ignore_index=True)
    camp["facilityId"] = camp["facilityId"].astype(int)
    # steady-state operating hours only: full-hour operation, real output/fuel.
    op = (camp["grossLoad"] > 0) & (camp["heatInput"] > 0) & (camp["opTime"] >= 0.95)
    camp = camp[op].copy()
    camp["hr"] = camp["heatInput"] / camp["grossLoad"]
    camp = camp[(camp["hr"] >= HR_LO) & (camp["hr"] <= HR_HI)].copy()
    return camp


def _wquantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    """Weighted quantile via the cumulative-weight CDF."""
    if len(values) == 0:
        return float("nan")
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cw = np.cumsum(w) - 0.5 * w
    cw /= w.sum()
    return float(np.interp(q, cw, v))


def _capwt(per_unit: pd.DataFrame, col: str) -> dict[str, float]:
    """Capacity-weighted p25/p50/p75 of a per-unit band multiplier."""
    d = per_unit[np.isfinite(per_unit[col]) & np.isfinite(per_unit["cap"])]
    d = d[(d["cap"] > 0) & (d[col] > 0)]
    if d.empty:
        return {f"p{int(p * 100)}": float("nan") for p in PCTS}
    v = d[col].to_numpy(float)
    w = d["cap"].to_numpy(float)
    return {f"p{int(p * 100)}": round(_wquantile(v, w, p), 3) for p in PCTS}


def derive_unit_bands(u: pd.DataFrame, base_hr: float) -> dict[str, float] | None:
    """Per-unit committed/econ_low/econ_high multipliers (avg + marginal HR).

    ``avg_*``  = median average HR in the band / base_HR.
    ``marg_*`` = the **incremental** heat rate d(heatInput)/d(grossLoad) in the
                 band, from a per-unit quadratic fit of heatInput against the
                 unit's NORMALIZED load (which removes the conditioning blow-up a
                 raw-MW polyfit suffers), evaluated at the band-representative
                 load position / base_HR. Monotone by construction (linear
                 marginal curve), so committed <= econ_low <= econ_high tracks
                 the unit's real input-output convexity.
    """
    gl = u["grossLoad"].to_numpy(float)
    hi = u["heatInput"].to_numpy(float)
    hr = u["hr"].to_numpy(float)
    if len(gl) < MIN_UNIT_HOURS:
        return None
    lsl = float(np.percentile(gl, LSL_PCT))
    hsl = float(np.percentile(gl, HSL_PCT))
    if hsl <= lsl:
        return None
    rng = hsl - lsl
    rel = np.clip((gl - lsl) / rng, 0.0, 1.0)

    # --- average HR per band ---
    comm_a = hr[gl <= lsl * 1.05]
    lo_a = hr[rel <= 0.33]
    hi_a = hr[rel >= 0.67]
    avg = {
        "committed": float(np.median(comm_a)) / base_hr if len(comm_a) > 5 else np.nan,
        "econ_low": float(np.median(lo_a)) / base_hr if len(lo_a) > 5 else np.nan,
        "econ_high": float(np.median(hi_a)) / base_hr if len(hi_a) > 5 else np.nan,
    }

    # --- marginal (incremental) HR per band: normalized-quadratic I/O slope ---
    # Fit heatInput against the unit's NORMALIZED load x = (grossLoad-LSL)/range
    # with a quadratic; normalizing x to ~[0,1] removes the conditioning blow-up
    # a raw-MW polyfit suffers (grossLoad^2 ~ 1e5). The incremental heat rate is
    # d(heatInput)/d(grossLoad) = (c1 + 2*c2*x)/range — a LINEAR (hence monotone)
    # marginal curve, evaluated at the band-representative load position:
    # committed at the min-gen floor (x=0), econ_low at mid-ramp (x=0.5),
    # econ_high at the top of the economic ramp (x=0.9). Divided by base_HR.
    marg = {"committed": np.nan, "econ_low": np.nan, "econ_high": np.nan}
    try:
        x = (gl - lsl) / rng
        c2, c1, _c0 = np.polyfit(x, hi, 2)
        mhr = lambda xx: (c1 + 2.0 * c2 * xx) / rng  # noqa: E731 d(hi)/d(gl)
        for b, xpos in (("committed", 0.0), ("econ_low", 0.5), ("econ_high", 0.9)):
            m = float(mhr(xpos)) / base_hr
            marg[b] = m if 0 < m < 5 else np.nan
    except (np.linalg.LinAlgError, ValueError):
        pass

    cap = float(np.percentile(gl, HSL_PCT))  # HSL as the capacity weight
    return {
        "cap": cap,
        "avg_committed": avg["committed"],
        "avg_econ_low": avg["econ_low"],
        "avg_econ_high": avg["econ_high"],
        "marg_committed": marg["committed"],
        "marg_econ_low": marg["econ_low"],
        "marg_econ_high": marg["econ_high"],
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--iso", default="NYISO", help="ISO (default NYISO)")
    ap.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=[2023, 2024, 2025],
        help="CEMS years to pool (default 2023 2024 2025)",
    )
    ap.add_argument(
        "--out-csv",
        default=None,
        help="summary CSV path (default data/raw/reference/"
        "<iso>_campd_marginal_hr_summary.csv)",
    )
    args = ap.parse_args()
    iso = args.iso.upper()
    years = tuple(args.years)

    base_hr, bin_rows = load_base_hr_and_class_map(iso)
    plant_groups: dict[int, list[str]] = (
        bin_rows.groupby("Plant_Code")["Plant_Group"].apply(list).to_dict()
    )
    camp = load_campd(iso, years)
    camp["cls"] = [
        map_unit_class(f, t, plant_groups)
        for f, t in zip(camp["facilityId"], camp["unitType"])
    ]
    camp = camp[camp["cls"].notna()].copy()
    camp["uid"] = camp["facilityId"].astype(str) + "_" + camp["unitId"].astype(str)

    print(f"=== CAMPD marginal-HR derivation: {iso} {years} ===")
    print(f"states {states_for_iso(iso)}  |  {len(camp):,} steady-state unit-hours")
    print("class cap-weighted base_HR (MMBtu/MWh):")
    for g in GAS_CLASSES:
        print(f"  {g:12s} {base_hr.get(g, float('nan')):.3f}")
    print()

    rows = []
    for cls in [c for c in bin_rows["Plant_Group"].unique() if c in base_hr]:
        d = camp[camp["cls"] == cls]
        bh = base_hr[cls]
        per_unit = []
        for _uid, u in d.groupby("uid"):
            r = derive_unit_bands(u, bh)
            if r is not None:
                per_unit.append(r)
        if not per_unit:
            continue
        pu = pd.DataFrame(per_unit)
        row: dict[str, object] = {
            "class": cls,
            "base_hr": round(bh, 3),
            "n_units": len(pu),
        }
        for measure in ("avg", "marg"):
            for band in ("committed", "econ_low", "econ_high"):
                q = _capwt(pu, f"{measure}_{band}")
                row[f"{measure}_{band}_p50"] = q["p50"]
                row[f"{measure}_{band}_p25"] = q["p25"]
                row[f"{measure}_{band}_p75"] = q["p75"]
        rows.append(row)

    summary = pd.DataFrame(rows)
    pd.set_option("display.width", 240)
    pd.set_option("display.max_columns", 60)

    print("=== AVERAGE heat-rate multipliers (cap-weighted median [p25,p75]) ===")
    for _, r in summary.iterrows():
        print(
            f"  {r['class']:12s} base_HR={r['base_hr']:.2f} n={int(r['n_units']):2d}  "
            f"committed={r['avg_committed_p50']:.3f}[{r['avg_committed_p25']:.2f},{r['avg_committed_p75']:.2f}]  "
            f"econ_low={r['avg_econ_low_p50']:.3f}[{r['avg_econ_low_p25']:.2f},{r['avg_econ_low_p75']:.2f}]  "
            f"econ_high={r['avg_econ_high_p50']:.3f}[{r['avg_econ_high_p25']:.2f},{r['avg_econ_high_p75']:.2f}]"
        )
    print(
        "\n=== MARGINAL (incremental) heat-rate multipliers (cap-weighted median [p25,p75]) ==="
    )
    for _, r in summary.iterrows():
        print(
            f"  {r['class']:12s} base_HR={r['base_hr']:.2f} n={int(r['n_units']):2d}  "
            f"committed={r['marg_committed_p50']:.3f}[{r['marg_committed_p25']:.2f},{r['marg_committed_p75']:.2f}]  "
            f"econ_low={r['marg_econ_low_p50']:.3f}[{r['marg_econ_low_p25']:.2f},{r['marg_econ_low_p75']:.2f}]  "
            f"econ_high={r['marg_econ_high_p50']:.3f}[{r['marg_econ_high_p25']:.2f},{r['marg_econ_high_p75']:.2f}]"
        )

    out_csv = (
        Path(args.out_csv)
        if args.out_csv
        else REFERENCE_DIR / f"{iso.lower()}_campd_marginal_hr_summary.csv"
    )
    summary.to_csv(out_csv, index=False)
    print(f"\nWrote {out_csv}")


if __name__ == "__main__":
    main()
