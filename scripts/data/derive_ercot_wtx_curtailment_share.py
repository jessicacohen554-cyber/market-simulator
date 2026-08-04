#!/usr/bin/env python
"""Derive the ERCOT West Texas Export corridor VRE curtailment-share driver.

Two products, from strictly separated sources:

1. **SHAPE** — ``data/raw/reference/ercot_wtx_curtailment_share.csv``: the measured
   West-corridor SCED congestion fraction (``data/clean/ercot-wtx-congestion``,
   curated by scripts/data/curate_ercot_wtx_congestion.py) binned by within-year
   net-load percentile decile x hour-of-day x season, pooled across the in-sample
   years. Reads ONLY measured congestion incidence and net-load — never the
   reported curtailment volume. Reproduces the measured binding-frequency
   distribution leave-one-year-out (the anti-residual gate / rule #23).

2. **LEVEL** — the per-tech depth coefficients printed as a paste-ready block for
   ``constants``/``ScenarioConfig``. A single scalar per tech converting congestion
   incidence into curtailed fraction, centred on the measured curtailment MW
   quantity (``HSL - delivered`` from data/raw/ercot-hsl) exactly as the
   RTOLCAP-forward ``deliv`` coefficient is centred on the measured reserve MW
   quantity. This is the ONE coefficient that reads the reported-curtailment
   aggregate; it is a stable structural constant (LOYO-validated below), not a
   per-year residual knob, and ``depth = 0`` is the zero-forcing ablation.

Net-load axis and season/hour-of-day axes are shared with the solve-time reader
(market_sim.data.curtailment_share) so the derived table and the LP consumer bin
identically.

Run ``python scripts/data/derive_ercot_wtx_curtailment_share.py`` for the report +
LOYO validation and to (re)write the reference CSV. Rule #23: re-derive only when
the source data updates (a new NP6-86 year or a rebuilt HSL parquet), never
because a price/backcast residual moved — cite the data change in the commit.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config import paths  # noqa: E402
from market_sim.data.curtailment_share import (  # noqa: E402
    FAMILY_LABELS,
    FAMILY_SHARE_TABLE_NAME,
    PANHANDLE_OWNERS,
    SHARE_TABLE_NAME,
    WEST_CORRIDOR_ZONES,
    corridor_zone_shares,
    family_share_lookup,
    hour_axes,
    net_load_decile,
)
from scripts.lib.clean_io import read_clean  # noqa: E402

IN_SAMPLE_YEARS = (2023, 2024, 2025)  # 2022 / H1-2026 are held-out (rule #22)
_SHARE_KEY = ["net_load_decile", "hour_of_day", "season"]

# The unpooled (ercot-165) products. The clean column each family reads, and the
# family label written to the long-format reference table.
_FAMILY_COLUMNS = {
    "D": "congestion_frac_family_d",
    "N": "congestion_frac_family_n",
    "PNHNDL": "congestion_frac_pnhndl",
}


def _measured_net_load(year: int) -> np.ndarray:
    """System net-load (T,) = EIA-930 ERCOT demand - wind_hsl - solar_hsl.

    The SAME potential-based net-load convention the LP applies at solve time
    (fleet.apply_netload_drag_floors); only the RANK (decile) is consumed, so the
    measured vs model level offset is immaterial.
    """
    hsl = pd.read_parquet(
        paths.RAW_DIR / "ercot-hsl" / f"ercot_{year}_hsl_hourly.parquet"
    ).set_index("hour")
    dem = pd.read_parquet(
        paths.RAW_DIR / "eia-930-hourly" / "ERCO hourly.parquet",
        columns=["Local date", "Hour", "Demand"],
    )
    dem["ld"] = pd.to_datetime(dem["Local date"])
    dem = dem[
        (dem["ld"].dt.year == year)
        & ~((dem["ld"].dt.month == 2) & (dem["ld"].dt.day == 29))
    ].sort_values(["ld", "Hour"])
    demand = dem["Demand"].to_numpy()[:8760]
    if len(demand) < 8760:  # pad a short archive tail with the annual mean
        demand = np.pad(
            demand, (0, 8760 - len(demand)), constant_values=float(np.nanmean(demand))
        )
    return demand - hsl["wind_hsl_mw"].to_numpy() - hsl["solar_hsl_mw"].to_numpy()


def _reported_curtailment(year: int) -> dict[str, np.ndarray]:
    """Measured HSL potential and delivered wind/solar (the LEVEL anchor only)."""
    hsl = pd.read_parquet(
        paths.RAW_DIR / "ercot-hsl" / f"ercot_{year}_hsl_hourly.parquet"
    ).set_index("hour")
    return {
        "wind_hsl": hsl["wind_hsl_mw"].to_numpy(),
        "wind_gen": hsl["wind_gen_mw"].to_numpy(),
        "solar_hsl": hsl["solar_hsl_mw"].to_numpy(),
        "solar_gen": hsl["solar_gen_mw"].to_numpy(),
    }


def _year_frame(year: int) -> pd.DataFrame:
    """Per-hour (decile, hour_of_day, season, congestion_share) for one year."""
    cong = read_clean("ercot-wtx-congestion", iso="ERCOT", year=year)
    cong = cong.sort_values("hour")
    share = cong["congestion_frac"].to_numpy()
    nl = _measured_net_load(year)
    hod, season = hour_axes(len(share))
    return pd.DataFrame(
        {
            "net_load_decile": net_load_decile(nl),
            "hour_of_day": hod,
            "season": season,
            "congestion_share": share,
        }
    )


def build_share_table(years) -> pd.DataFrame:
    """Pool the given years into the (decile x hour x season) congestion table."""
    frames = [_year_frame(y) for y in years]
    pooled = pd.concat(frames, ignore_index=True)
    return (
        pooled.groupby(_SHARE_KEY)["congestion_share"]
        .mean()
        .reset_index()
        .sort_values(_SHARE_KEY, ignore_index=True)
    )


def _apply_table(table: pd.DataFrame, year: int) -> np.ndarray:
    """Look up each hour's congestion share from ``table`` for ``year``."""
    nl = _measured_net_load(year)
    hod, season = hour_axes(len(nl))
    key = pd.DataFrame(
        {"net_load_decile": net_load_decile(nl), "hour_of_day": hod, "season": season}
    )
    merged = key.merge(table, on=_SHARE_KEY, how="left")
    return np.nan_to_num(merged["congestion_share"].to_numpy(dtype=float), nan=0.0)


def _family_year_frame(year: int) -> pd.DataFrame:
    """Per-hour (decile, hod, season, family, congestion_share) for one year.

    Long format over :data:`_FAMILY_COLUMNS` — one row per (hour, family) — so
    the pooled table's group-by generalizes unchanged.
    """
    cong = read_clean("ercot-wtx-congestion", iso="ERCOT", year=year).sort_values(
        "hour"
    )
    missing = [c for c in _FAMILY_COLUMNS.values() if c not in cong.columns]
    if missing:
        raise KeyError(
            f"ercot-wtx-congestion {year} predates schema v2 (missing {missing}) — "
            "re-run scripts/data/curate_ercot_wtx_congestion.py"
        )
    nl = _measured_net_load(year)
    hod, season = hour_axes(len(cong))
    dec = net_load_decile(nl)
    return pd.concat(
        [
            pd.DataFrame(
                {
                    "family": fam,
                    "net_load_decile": dec,
                    "hour_of_day": hod,
                    "season": season,
                    "congestion_share": cong[col].to_numpy(),
                }
            )
            for fam, col in _FAMILY_COLUMNS.items()
        ],
        ignore_index=True,
    )


def build_family_share_table(years) -> pd.DataFrame:
    """Pool the years into the (family x decile x hour x season) share table."""
    pooled = pd.concat([_family_year_frame(y) for y in years], ignore_index=True)
    key = ["family"] + _SHARE_KEY
    return (
        pooled.groupby(key)["congestion_share"]
        .mean()
        .reset_index()
        .sort_values(key, ignore_index=True)
    )


def _apply_family_table(table: pd.DataFrame, year: int) -> dict[str, np.ndarray]:
    """Look up each hour's per-family share from ``table`` for ``year``."""
    return family_share_lookup(table, _measured_net_load(year))


_ERCOT_VRE_TECHNOLOGY = {
    "wind": ("Onshore Wind Turbine",),
    "solar": ("Solar Photovoltaic",),
}
_CORRIDOR_WEIGHT_CACHE: dict[str, dict[str, float]] = {}


def corridor_zone_weights(tech: str) -> dict[str, float]:
    """Each corridor zone's share of the corridor's ``tech`` nameplate capacity.

    Measured from the EIA-860 operable generator file through the model's OWN
    ``zone_assignment._ercot_zone`` boundaries, so the weight is exactly the
    split the LP applies the per-zone ceilings across. Measured 2026-08-04:
    wind 0.630 West / 0.370 Panhandle; solar 0.969 / 0.031 (the Panhandle
    carries ~244 MW of PV against the Permian/CREZ 7.7 GW), which is why giving
    the Panhandle its own ceiling barely moves solar.

    This replaces an equal-weight convention: the depth is ONE scalar per tech,
    so its denominator must weight the corridor zones by the potential they
    actually expose, or an arm that zeroes one zone's share would be centred on
    a different total than an arm that does not. Forward-admissible — a forecast
    year re-weights from its own evolved fleet.
    """
    if tech in _CORRIDOR_WEIGHT_CACHE:
        return _CORRIDOR_WEIGHT_CACHE[tech]
    from market_sim.data.zone_assignment import _ercot_zone, _oris_to_location

    gen = pd.read_parquet(
        paths.RAW_DIR / "eia-860" / "eia860_generator_operable.parquet",
        columns=["Plant Code", "State", "Technology", "Nameplate Capacity (MW)"],
    )
    gen = gen[
        (gen["State"] == "TX") & gen["Technology"].isin(_ERCOT_VRE_TECHNOLOGY[tech])
    ].copy()
    loc = _oris_to_location()

    def _zone(plant_code) -> str | None:
        v = loc.get(int(plant_code))
        return _ercot_zone(*v) if v else None

    gen["zone"] = gen["Plant Code"].map(_zone)
    cap = gen.groupby("zone")["Nameplate Capacity (MW)"].sum()
    corridor = {z: float(cap.get(z, 0.0)) for z in WEST_CORRIDOR_ZONES}
    total = sum(corridor.values())
    weights = (
        {z: c / total for z, c in corridor.items()}
        if total > 0
        else {z: 1.0 / len(WEST_CORRIDOR_ZONES) for z in WEST_CORRIDOR_ZONES}
    )
    _CORRIDOR_WEIGHT_CACHE[tech] = weights
    return weights


def _effective_share(
    table: pd.DataFrame, year: int, panhandle_owner: str, tech: str
) -> np.ndarray:
    """The capacity-weighted corridor share the unpooled driver applies.

    ``corridor_zone_shares`` gives the per-zone share the LP applies; the depth
    is a single per-tech scalar, so its denominator is that per-zone share
    weighted by :func:`corridor_zone_weights` — the potential each zone actually
    exposes to the ceiling. EVERY corridor zone is counted, including one whose
    share an arm sets to zero, so both arms are centred on the SAME measured
    curtailment total and differ only in how they distribute it.
    """
    zone_share = corridor_zone_shares(_apply_family_table(table, year), panhandle_owner)
    w = corridor_zone_weights(tech)
    return sum(w.get(z, 0.0) * s for z, s in zone_share.items())


def _family_depth(table: pd.DataFrame, years, tech: str, panhandle_owner: str) -> float:
    """Level coefficient for the unpooled driver, per arm.

    Identical construction to :func:`_depth` — ``sum_y(HSL-GEN) /
    sum_y(HSL * share_hat)`` centred on the measured curtailment MW quantity —
    with ``share_hat`` the arm's capacity-weighted corridor share. Still exactly
    two free scalars for the whole driver (one per tech); the arm is a
    structural choice, not a third fitted parameter, and family membership and
    the per-zone assignment are both source-data derives (rule 23).
    """
    num = 0.0
    den = 0.0
    for y in years:
        rep = _reported_curtailment(y)
        share = _effective_share(table, y, panhandle_owner, tech)
        hsl, gen = rep[f"{tech}_hsl"], rep[f"{tech}_gen"]
        num += float(np.clip(hsl - gen, 0, None).sum())
        den += float((hsl * share).sum())
    return num / den if den > 0 else 0.0


def _depth(table: pd.DataFrame, years, tech: str) -> float:
    """Level coefficient: reported curt fraction / potential-weighted mean share.

    Pooled over ``years``: ``depth = sum_y(HSL-GEN) / sum_y(HSL * share_hat)`` so a
    single scalar centres the driver on the measured curtailment MW quantity.
    """
    num = 0.0
    den = 0.0
    for y in years:
        rep = _reported_curtailment(y)
        share = _apply_table(table, y)
        hsl, gen = rep[f"{tech}_hsl"], rep[f"{tech}_gen"]
        num += float(np.clip(hsl - gen, 0, None).sum())
        den += float((hsl * share).sum())
    return num / den if den > 0 else 0.0


def _report() -> pd.DataFrame:
    print("=== SHAPE: measured West-corridor congestion frequency (rule #23) ===")
    full = build_share_table(IN_SAMPLE_YEARS)
    for tech in ("wind", "solar"):
        d = _depth(full, IN_SAMPLE_YEARS, tech)
        print(f"  pooled depth[{tech}] = {d:.4f}")

    print("\n=== LEAVE-ONE-YEAR-OUT validation ===")
    print("  (a) frequency-shape: train-table congestion_share vs held-out actual")
    print("  (b) curtailment-level: train depth x train share vs held-out reported")
    for hold in IN_SAMPLE_YEARS:
        train = [y for y in IN_SAMPLE_YEARS if y != hold]
        table = build_share_table(train)
        # (a) shape: correlate predicted vs actual per-hour congestion share
        pred_share = _apply_table(table, hold)
        actual = _year_frame(hold)["congestion_share"].to_numpy()
        shape_corr = np.corrcoef(pred_share, actual)[0, 1]
        shape_bias = pred_share.mean() - actual.mean()
        # (b) level, per tech
        line = []
        for tech in ("wind", "solar"):
            d = _depth(table, train, tech)
            rep = _reported_curtailment(hold)
            hsl, gen = rep[f"{tech}_hsl"], rep[f"{tech}_gen"]
            pred = d * (hsl * pred_share).sum() / hsl.sum()
            act = np.clip(hsl - gen, 0, None).sum() / hsl.sum()
            line.append(f"{tech}: pred={pred:.4f} act={act:.4f} (d_train={d:.4f})")
        print(
            f"  hold {hold}: shape corr={shape_corr:+.3f} bias={shape_bias:+.3f} | "
            + " | ".join(line)
        )
    return full


def _family_report() -> pd.DataFrame:
    """Report + LOYO-validate the UNPOOLED (ercot-165) family share table."""
    print("\n=== UNPOOLED: per-family congestion frequency (ercot-165) ===")
    full = build_family_share_table(IN_SAMPLE_YEARS)
    for fam in FAMILY_LABELS:
        sub = full[full["family"] == fam]
        print(
            f"  family {fam:6s}: {len(sub):4d} cells, mean share {sub['congestion_share'].mean():.4f}"
        )
    for owner in PANHANDLE_OWNERS:
        depths = {
            tech: _family_depth(full, IN_SAMPLE_YEARS, tech, owner)
            for tech in ("wind", "solar")
        }
        print(
            f"  panhandle_owner={owner:6s} -> depth[wind]={depths['wind']:.4f} "
            f"depth[solar]={depths['solar']:.4f}"
        )

    print("\n=== UNPOOLED LEAVE-ONE-YEAR-OUT validation ===")
    print("  (a) per-family frequency-shape: train table vs held-out measured")
    print("  (b) curtailment-level per arm: train depth x train share vs held-out")
    for hold in IN_SAMPLE_YEARS:
        train = [y for y in IN_SAMPLE_YEARS if y != hold]
        table = build_family_share_table(train)
        pred = _apply_family_table(table, hold)
        own = _family_year_frame(hold)
        shape = []
        for fam in FAMILY_LABELS:
            actual = own[own["family"] == fam]["congestion_share"].to_numpy()
            c = float(np.corrcoef(pred[fam], actual)[0, 1]) if actual.std() > 0 else 0.0
            shape.append(
                f"{fam} corr={c:+.3f} bias={pred[fam].mean() - actual.mean():+.3f}"
            )
        print(f"  hold {hold} shape: " + " | ".join(shape))
        for owner in PANHANDLE_OWNERS:
            line = []
            for tech in ("wind", "solar"):
                d = _family_depth(table, train, tech, owner)
                share = _effective_share(table, hold, owner, tech)
                rep = _reported_curtailment(hold)
                hsl, gen = rep[f"{tech}_hsl"], rep[f"{tech}_gen"]
                p = d * (hsl * share).sum() / hsl.sum()
                a = np.clip(hsl - gen, 0, None).sum() / hsl.sum()
                line.append(f"{tech}: pred={p:.4f} act={a:.4f} (d_train={d:.4f})")
            print(f"    owner={owner:6s} " + " | ".join(line))
    return full


def main() -> None:
    """CLI: report + LOYO validation, and (re)write the reference share table(s)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--no-write",
        action="store_true",
        help="Report + validate only; do not (re)write the reference CSV.",
    )
    ap.add_argument(
        "--family",
        action="store_true",
        help="Also build/validate the UNPOOLED diurnal-family share table (ercot-165).",
    )
    ap.add_argument(
        "--family-only",
        action="store_true",
        help=(
            "With --family: write ONLY the family table, leaving the pooled CSV "
            "untouched. Use this whenever the pooled table is a live keeper input "
            "and its source data has NOT changed — rewriting it then would be a "
            "rule 23 [R-FROZEN-DERIVE] re-derivation with no data change to cite. "
            "(The committed pooled table is a 2026-07 vintage that does not "
            "byte-reproduce from today's archives — 870 vs 872 cells, mean "
            "|delta| 0.019 — so an incidental rebuild would silently move the "
            "armed ERCOT keeper's input; see docs/calibration-log/ercot.md, "
            "ercot-165.)"
        ),
    )
    args = ap.parse_args()
    full = _report()
    fam = _family_report() if args.family else None
    if args.no_write:
        return
    if not args.family_only:
        out = paths.RAW_DIR / "reference" / SHARE_TABLE_NAME
        full.to_csv(out, index=False)
        print(f"\nwrote {len(full)} (decile x hour x season) rows -> {out}")
    if fam is not None:
        fout = paths.RAW_DIR / "reference" / FAMILY_SHARE_TABLE_NAME
        fam.to_csv(fout, index=False)
        print(f"wrote {len(fam)} (family x decile x hour x season) rows -> {fout}")


if __name__ == "__main__":
    main()
