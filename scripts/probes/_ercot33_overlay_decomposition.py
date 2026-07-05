"""WS-F / stage 0 decomposition: what the ERCOT keeper's DAM-AS overlay carries.

For every overlay-active hour of the ercot32 keeper (``ercot_dam_as_overlay``,
2024+, threshold $150), classify the hour into exactly one bucket:

  (i)   RT-supported scarcity   — RT actual also elevated (> $150) that hour.
  (ii)  DA-boundary premium     — RT actual NOT elevated (failure mode F6):
        the DAM AS scarcity that fired the overlay did not show up in real
        time, i.e. it is a DAM-vs-RT settlement-boundary artifact.
  (iii) May-2024 discretionary-procurement uplift window (failure mode F7,
        run163: measured up-AS ~8.8 GW vs driver-formula ~7.4 GW on the
        acute evenings) — May 8/24/26 2024, hour-ending 16-21 — carved out of
        bucket (ii) as a distinct, named mechanism.

Priority order: (i) first (RT actually scarce that hour, whatever else is
true), then (iii) the specific named discretionary window, then (ii) the
generic DA-boundary catch-all. Mutually exclusive, covers every overlay-active
hour.

The overlay value itself (``ercot_dam_as_overlay_series``) and hourly system
demand (``load_demand``) are both pure functions of measured input data and the
calendar year — independent of dispatch/solve — so this decomposition does not
require a solved bundle; it reads the same measured series the keeper's
post-solve overlay step reads, plus the actual RT/DA benchmark
(``data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet``).

Usage: python scripts/probes/_ercot33_overlay_decomposition.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/home/user/market-simulator")
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia_loader import load_demand  # noqa: E402
from market_sim.results.scarcity import ercot_dam_as_overlay_series  # noqa: E402

HOURS = 8760
YEARS = [2023, 2024, 2025]
SCARCITY_THRESHOLD = 150.0
FROM_YEAR = 2024

ACTUAL_LMP_PATH = REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"


def _month_day(hours: int) -> tuple[np.ndarray, np.ndarray]:
    """(month, day) arrays for the model's fixed non-leap 8760 clock."""
    base = pd.date_range("2023-01-01", periods=hours, freq="h")
    return base.month.to_numpy(), base.day.to_numpy()


def _hour_of_day(hours: int) -> np.ndarray:
    base = pd.date_range("2023-01-01", periods=hours, freq="h")
    return base.hour.to_numpy()


def _actual_rt_da(year: int, hours: int) -> tuple[np.ndarray, np.ndarray]:
    act = pd.read_parquet(ACTUAL_LMP_PATH)
    act = act[act["year"] == year]
    rt = np.full(hours, np.nan)
    da = np.full(hours, np.nan)
    rt[act["hour"].to_numpy()] = act["rt"].to_numpy()
    da[act["hour"].to_numpy()] = act["da"].to_numpy()
    return rt, da


def _system_demand(year: int, hours: int) -> np.ndarray:
    zonal = load_demand("ERCOT", year)  # (n_zones, HOURS_PER_YEAR)
    return zonal[:, :hours].sum(axis=0)


def classify_hours(year: int) -> pd.DataFrame:
    """One row per overlay-active hour with its bucket and $ contribution."""
    overlay = ercot_dam_as_overlay_series(
        year, HOURS, scarcity_threshold=SCARCITY_THRESHOLD, from_year=FROM_YEAR
    )
    active = overlay > 0.0
    if not active.any():
        return pd.DataFrame(
            columns=[
                "year",
                "hour",
                "month",
                "day",
                "overlay",
                "rt",
                "da",
                "demand",
                "bucket",
            ]
        )

    rt, da = _actual_rt_da(year, HOURS)
    demand = _system_demand(year, HOURS)
    month, day = _month_day(HOURS)
    hod = _hour_of_day(HOURS)

    # May-2024 discretionary window: May 8/24/26, hour-ending 16-21 (run163
    # F7). Hour-ending HE_k covers clock hour (k-1) on the model's 0-indexed
    # hour-of-day, so HE16..HE21 -> hour-of-day 15..20.
    may_window = (
        (year == 2024)
        & (month == 5)
        & np.isin(day, [8, 24, 26])
        & (hod >= 15)
        & (hod <= 20)
    )

    rt_supported = active & np.isfinite(rt) & (rt > SCARCITY_THRESHOLD)
    discretionary = active & ~rt_supported & may_window
    da_boundary = active & ~rt_supported & ~discretionary

    bucket = np.full(HOURS, "", dtype=object)
    bucket[da_boundary] = "ii_da_boundary"
    bucket[discretionary] = "iii_discretionary_may2024"
    bucket[rt_supported] = "i_rt_supported"

    idx = np.where(active)[0]
    return pd.DataFrame(
        {
            "year": year,
            "hour": idx,
            "month": month[idx],
            "day": day[idx],
            "overlay": overlay[idx],
            "rt": rt[idx],
            "da": da[idx],
            "demand": demand[idx],
            "bucket": bucket[idx],
        }
    )


def annual_dw_contribution(df: pd.DataFrame, year: int) -> dict:
    """Each bucket's $/MWh contribution to the YEAR's demand-weighted LMP.

    contribution = sum(overlay * demand for hours in bucket) / sum(demand,
    ALL 8760 hours of the year) — so the three buckets sum to the overlay's
    total annual dw-LMP contribution exactly (same denominator throughout).
    """
    demand_all = _system_demand(year, HOURS)
    total_demand = float(demand_all.sum())
    out = {"year": year, "total_demand_denominator_GWh": total_demand / 1e3}
    total = 0.0
    for b in ["i_rt_supported", "ii_da_boundary", "iii_discretionary_may2024"]:
        sub = df[df["bucket"] == b]
        contrib = (
            float((sub["overlay"] * sub["demand"]).sum() / total_demand)
            if total_demand
            else 0.0
        )
        out[b] = contrib
        total += contrib
    out["total_overlay_dw_contribution"] = total
    out["n_hours_active"] = int(len(df))
    for b in ["i_rt_supported", "ii_da_boundary", "iii_discretionary_may2024"]:
        out[f"n_hours_{b}"] = int((df["bucket"] == b).sum())
    return out


def monthly_dw_contribution(df: pd.DataFrame, year: int) -> pd.DataFrame:
    demand_all = _system_demand(year, HOURS)
    month_all, _ = _month_day(HOURS)
    rows = []
    for mo in range(1, 13):
        mo_demand = float(demand_all[month_all == mo].sum())
        row = {"year": year, "month": mo}
        total = 0.0
        for b in ["i_rt_supported", "ii_da_boundary", "iii_discretionary_may2024"]:
            sub = df[(df["bucket"] == b) & (df["month"] == mo)]
            contrib = (
                float((sub["overlay"] * sub["demand"]).sum() / mo_demand)
                if mo_demand
                else 0.0
            )
            row[b] = contrib
            total += contrib
        row["total"] = total
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    annual = []
    monthly = []
    hourly_frames = []
    for year in YEARS:
        df = classify_hours(year)
        hourly_frames.append(df)
        if df.empty:
            annual.append(
                {
                    "year": year,
                    "total_demand_denominator_GWh": None,
                    "i_rt_supported": 0.0,
                    "ii_da_boundary": 0.0,
                    "iii_discretionary_may2024": 0.0,
                    "total_overlay_dw_contribution": 0.0,
                    "n_hours_active": 0,
                    "n_hours_i_rt_supported": 0,
                    "n_hours_ii_da_boundary": 0,
                    "n_hours_iii_discretionary_may2024": 0,
                    "note": "inert (overlay from_year=2024)",
                }
            )
            continue
        annual.append(annual_dw_contribution(df, year))
        monthly.append(monthly_dw_contribution(df, year))

    out_dir = REPO / "results/calibration"
    all_hourly = pd.concat(hourly_frames, ignore_index=True)
    all_hourly.to_csv(out_dir / "ercot33_overlay_decomposition_hourly.csv", index=False)

    annual_df = pd.DataFrame(annual)
    annual_df.to_csv(out_dir / "ercot33_overlay_decomposition_annual.csv", index=False)

    monthly_df = pd.concat(monthly, ignore_index=True) if monthly else pd.DataFrame()
    monthly_df.to_csv(
        out_dir / "ercot33_overlay_decomposition_monthly.csv", index=False
    )

    print("=== annual $/MWh dw-LMP contribution by bucket ===")
    print(annual_df.to_string(index=False))
    print()
    print("=== monthly $/MWh dw-LMP contribution by bucket ===")
    print(monthly_df.to_string(index=False))

    with open(out_dir / "ercot33_overlay_decomposition.json", "w") as f:
        json.dump(
            {
                "annual": annual_df.to_dict(orient="records"),
                "monthly": monthly_df.to_dict(orient="records"),
            },
            f,
            indent=2,
        )


if __name__ == "__main__":
    main()
