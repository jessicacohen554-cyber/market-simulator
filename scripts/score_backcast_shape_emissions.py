"""Score a backcast bundle on the three gates the volume gate is blind to.

The dashboard/`_session_score` gate per-class **annual volume**. A class can
pass that on its total while (a) getting the coal/gas split wrong in a way
that cancels in MWh but not in CO2, or (b) getting the hourly operating shape
wrong (the CC_REGULAR ">90% CF" failure). This scorer adds the three checks
recommended in `docs/ercot-backcast-audit-2026-06.md` §D3, computed from a
bundle's committed `plant_hourly_fit.parquet` + the per-plant CEMS emission
intensities, so no LP re-solve is needed:

1. **Carbon-weighted CO2** — per-class, per-fuel (coal/gas) and system-total
   CO2, model vs CAMPD-actual, re-weighting each plant's volume error by its
   measured CO2 intensity. Absolute gates: system total +/-5%, per class
   +/-7%. This is the independent check on the coal/gas split: swapping coal
   MWh for gas MWh (compensation that passes the volume gate) moves total CO2
   because coal is ~2x the intensity of gas.
2. **Operating-shape `cf_emd`** — generation-weighted earth-mover distance
   between the model and CAMPD per-plant CF distributions, per class. Run as a
   **regression gate** against a `--baseline` bundle (the keeper): a class
   fails if its cf_emd worsens by more than `--emd-margin`.
3. **Hourly `pearson_r`** — generation-weighted per-class correlation, also a
   regression gate vs baseline (fail if r drops by more than `--r-margin`).

The actual-CO2 side uses the plant's measured `co2_kg_per_mwh_net`
(`inputs/processed/plant_emission_rates.parquet`, itself derived from CAMPD
co2/gen) applied to the CEMS net generation, so it reconstructs the measured
CAMPD CO2; the model side applies the same per-plant intensity to the model's
dispatched generation. Per plant the CO2 error therefore equals the volume
error; the *new* information is in the carbon-weighted aggregation across
fuels of differing intensity.

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

# Absolute CO2 gates (audit §D3 / peer-review §D.3).
CO2_TOTAL_BAND = 0.05      # system fossil total
CO2_CLASS_BAND = 0.07      # per fuel class
# Regression-gate margins for the shape metrics (seeded at the baseline's
# best-achieved value; a small slack absorbs solver noise).
DEFAULT_EMD_MARGIN = 0.02  # cf_emd may rise at most this much vs baseline
DEFAULT_R_MARGIN = 0.02    # pearson_r may fall at most this much vs baseline

_BIN_SHEET = REPO / "inputs" / "custom-bin-assignments.csv"
_RATES = REPO / "inputs" / "processed" / "plant_emission_rates.parquet"

# Plant_Group -> coarse fuel for the coal/gas CO2 split.
_COAL_GROUPS = {"COAL"}


def _class_map() -> dict[int, str]:
    """Plant_Code -> Plant_Group (the dispatch class), from the ERCOT bin sheet."""
    b = pd.read_csv(_BIN_SHEET)
    return dict(zip(b["Plant_Code"].astype(int), b["Plant_Group"].astype(str)))


def _intensity_map() -> dict[int, float]:
    """Plant_id -> measured CO2 intensity (tonnes/MWh net), CEMS-derived.

    The emission-rate table is keyed (plant_id, year); the intensity is stable
    across the backcast years, so collapse to one value per plant (prefer the
    non-zero-gen rows, mean of what remains). kg/MWh -> tonnes/MWh by /1000.
    """
    r = pd.read_parquet(_RATES)
    r = r[r["co2_kg_per_mwh_net"].notna() & (r["co2_kg_per_mwh_net"] > 0)]
    by_plant = r.groupby("plant_id")["co2_kg_per_mwh_net"].mean() / 1000.0
    return by_plant.to_dict()


def _fuel(group: str) -> str:
    return "coal" if group in _COAL_GROUPS else "gas"


def load_fit(bundle: Path) -> pd.DataFrame:
    """Per-plant fit frame enriched with class, fuel and CO2 intensity."""
    df = pd.read_parquet(bundle / "plant_hourly_fit.parquet").copy()
    cmap, imap = _class_map(), _intensity_map()
    df["group"] = df["plant_code"].astype(int).map(cmap)
    df = df[df["group"].notna()].copy()
    df["fuel"] = df["group"].map(_fuel)
    df["intensity"] = df["plant_code"].astype(int).map(imap)
    # Plants with no CEMS intensity (a handful of tiny CTs) carry no CO2 — drop
    # them from the CO2 aggregation only; they stay in the shape metrics.
    return df


def co2_table(df: pd.DataFrame) -> pd.DataFrame:
    """Model vs actual CO2 (kilotonnes) by year x {fuel, total} with err% + gate."""
    c = df[df["intensity"].notna()].copy()
    # CO2 (tonnes) = generation (GWh) * intensity (tonnes/MWh) * 1000 MWh/GWh,
    # reported in kilotonnes (/1000) -> GWh * intensity.
    c["model_co2_kt"] = c["model_gwh"] * c["intensity"]
    c["actual_co2_kt"] = c["campd_gwh"] * c["intensity"]
    rows = []
    for year, g in c.groupby("year"):
        for fuel in ("coal", "gas"):
            gf = g[g["fuel"] == fuel]
            rows.append(_co2_row(year, fuel, gf, CO2_CLASS_BAND))
        rows.append(_co2_row(year, "TOTAL", g, CO2_TOTAL_BAND))
    return pd.DataFrame(rows)


def _co2_row(year, label, g, band):
    m, a = g["model_co2_kt"].sum(), g["actual_co2_kt"].sum()
    err = (m - a) / a if a else float("nan")
    return {
        "year": year, "fuel": label,
        "model_ktCO2": round(m, 1), "actual_ktCO2": round(a, 1),
        "err_pct": round(100 * err, 1), "band_pct": round(100 * band, 1),
        "gate": "PASS" if abs(err) <= band else "FAIL",
    }


def shape_table(df: pd.DataFrame, base: pd.DataFrame | None,
                emd_margin: float, r_margin: float) -> pd.DataFrame:
    """Generation-weighted per-class cf_emd & pearson_r, with regression gates."""
    rows = []
    base_lookup = {}
    if base is not None:
        for (y, grp), g in base.groupby(["year", "group"]):
            base_lookup[(y, grp)] = (_wmean(g, "cf_emd"), _wmean(g, "pearson_r"))
    for (year, grp), g in df.groupby(["year", "group"]):
        emd, r = _wmean(g, "cf_emd"), _wmean(g, "pearson_r")
        row = {"year": year, "class": grp,
               "model_gwh": round(g["model_gwh"].sum(), 0),
               "cf_emd": round(emd, 3), "pearson_r": round(r, 3)}
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
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("bundle", type=Path)
    p.add_argument("--baseline", type=Path, default=None,
                   help="Keeper bundle for the cf_emd/pearson_r regression gates.")
    p.add_argument("--emd-margin", type=float, default=DEFAULT_EMD_MARGIN)
    p.add_argument("--r-margin", type=float, default=DEFAULT_R_MARGIN)
    args = p.parse_args()

    df = load_fit(args.bundle)
    base = load_fit(args.baseline) if args.baseline else None

    print(f"\n=== Bundle: {args.bundle} ===")
    co2 = co2_table(df)
    print("\n[CO2] carbon-weighted fossil CO2 (kilotonnes), model vs CAMPD-actual")
    print(co2.to_string(index=False))
    n_fail = (co2["gate"] == "FAIL").sum()
    print(f"CO2 gates: {len(co2) - n_fail}/{len(co2)} PASS "
          f"(total +/-{int(CO2_TOTAL_BAND*100)}%, class +/-{int(CO2_CLASS_BAND*100)}%)")

    shape = shape_table(df, base, args.emd_margin, args.r_margin)
    print("\n[SHAPE] generation-weighted per-class operating-shape metrics"
          + (f"  (regression gate vs {args.baseline.name})" if base is not None else ""))
    print(shape.sort_values(["year", "class"]).to_string(index=False))
    if base is not None and "emd_gate" in shape.columns:
        ef = (shape["emd_gate"] == "FAIL").sum()
        rf = (shape["r_gate"] == "FAIL").sum()
        print(f"Shape regression gates: cf_emd {len(shape)-ef}/{len(shape)} PASS, "
              f"pearson_r {len(shape)-rf}/{len(shape)} PASS")


if __name__ == "__main__":
    main()
