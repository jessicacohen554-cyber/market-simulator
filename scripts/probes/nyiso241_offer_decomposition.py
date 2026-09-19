"""NYISO phase 0 (zero LP): split each class's P1 offer into fuel-proportional and fixed parts.

Why this and not the merit table alone. A multiplicative band on a heat rate scales with the
gas price, so if EVERY gas class's offer were purely fuel-proportional the merit ORDER would be
invariant to the gas level and CT_PEAKER could not collapse from 2.43 TWh (2022, Transco Z6 NY
$6.86/MMBtu) to 0.25 TWh (2023, $1.98) against a flat actual. Something in the offer therefore
does NOT scale. This probe identifies what, per LP row, by regressing the row's hourly ``mc``
on the daily delivered gas price the run was built on:

    mc_i(h) = slope_i * gas(date(h)) + intercept_i

``slope_i`` is the row's effective heat rate x band (MMBtu/MWh); ``intercept_i`` is everything
that does not move with gas — VOM, the P0->P1 amortized startup markup, and any emissions
charge. The class-level comparison of intercepts across years is the discriminating measurement:
a fixed adder is a LARGER SHARE of a small offer, so it pushes a class down the merit order
precisely when fuel is cheap.

Reads only committed artifacts (the nyiso-240 MER legs, whose ``dispatch/<yr>_P1.parquet`` are
sha256-identical to the keeper's) plus the committed gas series. No LP is solved and nothing is
swept against any gate.

Usage:
    python3 scripts/probes/nyiso241_offer_decomposition.py \
        --legs results/calibration/nyiso_mer_2026-09-19_{2022,2023,2024,2025} \
        --out results/calibration/_nyiso241_offer_decomposition.json
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

# Transco Zone 6 NY is the delivered-gas hub NYISO's downstate fossil fleet prices against
# (data/raw/gas-prices/SOURCES_nyiso_downstate_ldc_transport.md). Used here ONLY as the
# regressor that separates the fuel-proportional from the fixed part of an offer; no value
# from it enters any config (rule 21 `[R-DOF]`).
GAS_CSV = Path("data/raw/gas-prices/transco_z6_ny_daily.csv")
GAS_COL = "transco_z6_ny_usd_mmbtu"

FOSSIL_CLASSES = ("CT_PEAKER", "ST_GAS", "CC_REGULAR", "CC_CHP")


def load_gas_by_hour(year: int) -> np.ndarray:
    """Return an 8760-long gas price array, forward-filling non-trading days."""
    daily: dict[str, float] = {}
    with GAS_CSV.open() as fh:
        for row in csv.DictReader(fh):
            if row["date"].startswith(str(year)):
                try:
                    daily[row["date"]] = float(row[GAS_COL])
                except (TypeError, ValueError):
                    continue
    index = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    keys = index.strftime("%Y-%m-%d")
    series = pd.Series([daily.get(k, np.nan) for k in keys], index=index)
    return series.ffill().bfill().to_numpy()


def decompose(leg: Path, year: int) -> dict:
    """Regress every LP row's hourly offer on the gas price and aggregate by class."""
    unit = pd.read_parquet(
        leg / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "unit_id", "plant_group", "hour", "mc", "cap_mw"],
    )
    unit = unit[unit["pass"] == "P1"]
    gas = load_gas_by_hour(year)

    mc_wide = unit.pivot_table(index="hour", columns="unit_id", values="mc")
    mc_wide = mc_wide.reindex(range(8760))
    klass_of = unit.groupby("unit_id")["plant_group"].first()
    cap_of = unit.groupby("unit_id")["cap_mw"].max()

    # One least-squares fit per column, vectorised: slope/intercept from the closed form.
    g = gas
    gbar = g.mean()
    gdev = g - gbar
    denom = float((gdev * gdev).sum())
    values = mc_wide.to_numpy()
    mbar = np.nanmean(values, axis=0)
    slope = np.nansum(gdev[:, None] * (values - mbar[None, :]), axis=0) / denom
    intercept = mbar - slope * gbar
    # R^2, so a row whose offer is not affine in gas is visible rather than assumed away.
    pred = slope[None, :] * g[:, None] + intercept[None, :]
    ss_res = np.nansum((values - pred) ** 2, axis=0)
    ss_tot = np.nansum((values - mbar[None, :]) ** 2, axis=0)
    r2 = np.where(ss_tot > 0, 1.0 - ss_res / ss_tot, np.nan)

    fit = pd.DataFrame(
        {"slope": slope, "intercept": intercept, "r2": r2, "mean_mc": mbar},
        index=mc_wide.columns,
    )
    fit["klass"] = klass_of.reindex(fit.index)
    fit["cap_mw"] = cap_of.reindex(fit.index)

    out: dict[str, dict] = {"gas_mean_usd_mmbtu": float(gas.mean())}
    for klass in FOSSIL_CLASSES:
        sub = fit[fit["klass"] == klass].dropna(subset=["slope"])
        if sub.empty:
            continue
        w = sub["cap_mw"].to_numpy()
        wsum = w.sum()
        slope_cw = float((sub["slope"].to_numpy() * w).sum() / wsum)
        inter_cw = float((sub["intercept"].to_numpy() * w).sum() / wsum)
        mean_cw = float((sub["mean_mc"].to_numpy() * w).sum() / wsum)
        out[klass] = {
            "rows": int(len(sub)),
            "cap_mw": float(wsum),
            "slope_capwt_mmbtu_per_mwh": slope_cw,
            "intercept_capwt_usd_per_mwh": inter_cw,
            "mean_offer_capwt_usd_per_mwh": mean_cw,
            "fixed_share_of_offer": inter_cw / mean_cw if mean_cw else float("nan"),
            "r2_median": float(sub["r2"].median()),
        }
    return out


def main() -> None:
    """Decompose every per-year leg and print the class table."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    report: dict[str, dict] = {}
    for leg_str in args.legs:
        leg = Path(leg_str)
        year = int(leg.name.rsplit("_", 1)[-1])
        report[str(year)] = decompose(leg, year)
        print(
            f"--- {year}  gas {report[str(year)]['gas_mean_usd_mmbtu']:.3f} $/MMBtu ---"
        )
        for klass in FOSSIL_CLASSES:
            row = report[str(year)].get(klass)
            if not row:
                continue
            print(
                f"  {klass:<12} HRxband {row['slope_capwt_mmbtu_per_mwh']:>7.3f} "
                f"fixed {row['intercept_capwt_usd_per_mwh']:>8.2f} $/MWh "
                f"({row['fixed_share_of_offer'] * 100:>5.1f} % of a "
                f"{row['mean_offer_capwt_usd_per_mwh']:>7.2f} offer)  r2 {row['r2_median']:.3f}"
            )

    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
