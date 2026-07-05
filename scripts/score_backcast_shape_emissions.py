"""Score a backcast bundle on the three gates the volume gate is blind to.

The dashboard/`_session_score` gate per-class **annual volume**. A class can
pass that on its total while (a) getting the coal/gas split wrong in a way
that cancels in MWh but not in CO2, or (b) getting the hourly operating shape
wrong (the CC_REGULAR ">90% CF" failure). This scorer adds the three checks
recommended in `docs/ercot-backcast-audit-2026-06.md` §D3, computed from a
bundle's committed `plant_hourly_fit.parquet` + the per-plant CEMS emission
intensities, so no LP re-solve is needed:

1. **Carbon-weighted CO2** (plus **NOx** and **SO2**) — per-class, per-fuel
   (coal/gas) and system-total mass, model vs CAMPD-actual, re-weighting each
   plant's volume error by its measured pollutant intensity. Absolute gates:
   system total +/-5%, per class +/-7%. This is the independent check on the
   coal/gas split: swapping coal MWh for gas MWh (compensation that passes the
   volume gate) moves total CO2 because coal is ~2x the intensity of gas — and
   moves SO2 far more (coal SO2 intensity dwarfs gas), so the SO2 table is the
   sharpest split check. NOx/SO2 are secondary reporting gates (plan §5 R7);
   they never gate a keeper and their intensities come from the same v2 artifact
   as CO2, so the CO2 verdict is unchanged.
2. **Operating-shape `cf_emd`** — generation-weighted earth-mover distance
   between the model and CAMPD per-plant CF distributions, per class. Run as a
   **regression gate** against a `--baseline` bundle (the keeper): a class
   fails if its cf_emd worsens by more than `--emd-margin`.
3. **Hourly `pearson_r`** — generation-weighted per-class correlation, also a
   regression gate vs baseline (fail if r drops by more than `--r-margin`).

The actual side uses the plant's measured `<pollutant>_kg_per_mwh_net`
(`data/raw/_processed-legacy/plant_emission_rates_v2.parquet`, itself derived
from CAMPD mass/gen) applied to the CEMS net generation, so it reconstructs the
measured CAMPD mass; the model side applies the same per-plant intensity to the
model's dispatched generation. Per plant the mass error therefore equals the
volume error; the *new* information is in the intensity-weighted aggregation
across fuels of differing intensity.

Usage:
    uv run python scripts/score_backcast_shape_emissions.py \
        results/calibration/run115b_ccduct_prb73_relief06
    # with regression gates against the keeper:
    uv run python scripts/score_backcast_shape_emissions.py \
        results/calibration/statmode_d1 \
        --baseline results/calibration/run115b_ccduct_prb73_relief06
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config import paths  # noqa: E402

# Absolute CO2 gates (audit §D3 / peer-review §D.3). NOx/SO2 reuse the same
# band shape — they are secondary reporting gates (plan §5 R7), never keeper
# gates; coal's SO2 intensity so dwarfs gas that the SO2 table is the sharpest
# independent check on the coal/gas dispatch split.
CO2_TOTAL_BAND = 0.05  # system fossil total
CO2_CLASS_BAND = 0.07  # per fuel class
# The three pollutants scored, each with its v2 per-net-MWh intensity column.
POLLUTANTS = ("co2", "nox", "so2")
_INTENSITY_COL = {p: f"{p}_kg_per_mwh_net" for p in POLLUTANTS}
# Regression-gate margins for the shape metrics (seeded at the baseline's
# best-achieved value; a small slack absorbs solver noise).
DEFAULT_EMD_MARGIN = 0.02  # cf_emd may rise at most this much vs baseline
DEFAULT_R_MARGIN = 0.02  # pearson_r may fall at most this much vs baseline

_BIN_SHEET = paths.RAW_DATA_DIR / "reference" / "custom-bin-assignments.csv"
_RATES = paths.PROCESSED_DIR / "plant_emission_rates_v2.parquet"

# Plant_Group -> coarse fuel for the coal/gas split.
_COAL_GROUPS = {"COAL"}


def _class_map() -> dict[int, str]:
    """Plant_Code -> Plant_Group (the dispatch class), from the ERCOT bin sheet."""
    b = pd.read_csv(_BIN_SHEET)
    return dict(zip(b["Plant_Code"].astype(int), b["Plant_Group"].astype(str)))


def _intensity_map(pollutant: str, iso: str = "ERCOT") -> dict[int, float]:
    """Plant_id -> measured pollutant intensity (tonnes/MWh net), CEMS-derived.

    The v2 artifact is keyed (iso, plant_id, unit_id, year); the intensity is
    stable across the backcast years, so aggregate to one value per plant on the
    gen-weighted net basis (Σ mass_kg / Σ net_mwh over that ISO's rows), then
    kg/MWh -> tonnes/MWh by /1000. NOx/SO2 mirror CO2 (plan §5 R7).
    """
    r = pd.read_parquet(_RATES)
    r = r[r["iso"].astype(str) == str(iso)]
    mass_col = f"{pollutant}_kg"
    agg = r.groupby("plant_id")[[mass_col, "net_mwh"]].sum()
    agg = agg[agg["net_mwh"] > 0]
    by_plant = (agg[mass_col] / agg["net_mwh"]) / 1000.0
    return by_plant.to_dict()


def _fuel(group: str) -> str:
    return "coal" if group in _COAL_GROUPS else "gas"


def load_fit(bundle: Path) -> pd.DataFrame:
    """Per-plant fit frame enriched with class, fuel and per-pollutant intensity."""
    df = pd.read_parquet(bundle / "plant_hourly_fit.parquet").copy()
    cmap = _class_map()
    df["group"] = df["plant_code"].astype(int).map(cmap)
    df = df[df["group"].notna()].copy()
    df["fuel"] = df["group"].map(_fuel)
    for p in POLLUTANTS:
        df[f"intensity_{p}"] = df["plant_code"].astype(int).map(_intensity_map(p))
    # Plants with no CEMS intensity (a handful of tiny CTs) carry no mass — drop
    # them from the mass aggregation only; they stay in the shape metrics.
    return df


def pollutant_table(df: pd.DataFrame, pollutant: str) -> pd.DataFrame:
    """Model vs actual pollutant mass (kilotonnes) by year x {fuel,total} + gate."""
    icol = f"intensity_{pollutant}"
    c = df[df[icol].notna()].copy()
    # mass (tonnes) = generation (GWh) * intensity (tonnes/MWh) * 1000 MWh/GWh,
    # reported in kilotonnes (/1000) -> GWh * intensity.
    c["model_kt"] = c["model_gwh"] * c[icol]
    c["actual_kt"] = c["campd_gwh"] * c[icol]
    rows = []
    for year, g in c.groupby("year"):
        for fuel in ("coal", "gas"):
            gf = g[g["fuel"] == fuel]
            rows.append(_mass_row(pollutant, year, fuel, gf, CO2_CLASS_BAND))
        rows.append(_mass_row(pollutant, year, "TOTAL", g, CO2_TOTAL_BAND))
    return pd.DataFrame(rows)


def _mass_row(pollutant, year, label, g, band):
    m, a = g["model_kt"].sum(), g["actual_kt"].sum()
    err = (m - a) / a if a else float("nan")
    unit = f"kt{pollutant.upper()}"
    return {
        "year": year,
        "fuel": label,
        f"model_{unit}": round(m, 1),
        f"actual_{unit}": round(a, 1),
        "err_pct": round(100 * err, 1),
        "band_pct": round(100 * band, 1),
        "gate": "PASS" if abs(err) <= band else "FAIL",
    }


def shape_table(
    df: pd.DataFrame, base: pd.DataFrame | None, emd_margin: float, r_margin: float
) -> pd.DataFrame:
    """Generation-weighted per-class cf_emd & pearson_r, with regression gates."""
    rows = []
    base_lookup = {}
    if base is not None:
        for (y, grp), g in base.groupby(["year", "group"]):
            base_lookup[(y, grp)] = (_wmean(g, "cf_emd"), _wmean(g, "pearson_r"))
    for (year, grp), g in df.groupby(["year", "group"]):
        emd, r = _wmean(g, "cf_emd"), _wmean(g, "pearson_r")
        row = {
            "year": year,
            "class": grp,
            "model_gwh": round(g["model_gwh"].sum(), 0),
            "cf_emd": round(emd, 3),
            "pearson_r": round(r, 3),
        }
        if (year, grp) in base_lookup:
            b_emd, b_r = base_lookup[(year, grp)]
            row["base_emd"] = round(b_emd, 3)
            row["base_r"] = round(b_r, 3)
            emd_ok = emd <= b_emd + emd_margin
            r_ok = r >= b_r - r_margin
            row["emd_gate"] = "PASS" if emd_ok else "FAIL"
            row["r_gate"] = "PASS" if r_ok else "FAIL"
        rows.append(row)
    return pd.DataFrame(rows)


def _wmean(g: pd.DataFrame, col: str) -> float:
    """Capacity-weighted mean of a per-plant metric (weights = nameplate MW)."""
    w = g["cap_mw"].clip(lower=0.0)
    return float((g[col] * w).sum() / w.sum()) if w.sum() else float("nan")


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("bundle", type=Path)
    p.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Keeper bundle for the cf_emd/pearson_r regression gates.",
    )
    p.add_argument("--emd-margin", type=float, default=DEFAULT_EMD_MARGIN)
    p.add_argument("--r-margin", type=float, default=DEFAULT_R_MARGIN)
    args = p.parse_args()

    df = load_fit(args.bundle)
    base = load_fit(args.baseline) if args.baseline else None

    print(f"\n=== Bundle: {args.bundle} ===")
    for pollutant in POLLUTANTS:
        tbl = pollutant_table(df, pollutant)
        tag = pollutant.upper()
        kind = "carbon-weighted fossil" if pollutant == "co2" else "intensity-weighted"
        note = "" if pollutant == "co2" else "  [secondary/reporting — R7]"
        print(f"\n[{tag}] {kind} {tag} mass (kilotonnes), model vs CAMPD-actual{note}")
        print(tbl.to_string(index=False))
        n_fail = (tbl["gate"] == "FAIL").sum()
        print(
            f"{tag} gates: {len(tbl) - n_fail}/{len(tbl)} PASS "
            f"(total +/-{int(CO2_TOTAL_BAND * 100)}%, "
            f"class +/-{int(CO2_CLASS_BAND * 100)}%)"
        )

    shape = shape_table(df, base, args.emd_margin, args.r_margin)
    print(
        "\n[SHAPE] generation-weighted per-class operating-shape metrics"
        + (f"  (regression gate vs {args.baseline.name})" if base is not None else "")
    )
    print(shape.sort_values(["year", "class"]).to_string(index=False))
    if base is not None and "emd_gate" in shape.columns:
        ef = (shape["emd_gate"] == "FAIL").sum()
        rf = (shape["r_gate"] == "FAIL").sum()
        print(
            f"Shape regression gates: cf_emd {len(shape) - ef}/{len(shape)} PASS, "
            f"pearson_r {len(shape) - rf}/{len(shape)} PASS"
        )


if __name__ == "__main__":
    main()
