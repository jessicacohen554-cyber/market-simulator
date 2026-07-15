"""Lead-0 probe (part 9) — anchor the 930 wind/solar phase against PJM's own
UTC-stamped Generation-by-Fuel feed (DataMiner2, datetime_beginning_utc).

For each year: build the PJM-feed hourly Wind / Solar / Gas / Coal series on
the chronological EST calendar from the UTC stamps, then find the shift that
best matches the EIA-930 wide-extract columns (diff-series lag r and level r).
Positive best-shift s means 930[k] ~ PJM[k+s], i.e. the 930 content is s
hours EARLY relative to PJM's own meter clock.

Also prints the PJM-feed solar centroid (absolute astronomical sanity) and
the model gas aggregate vs the PJM-feed gas (independent re-test of the
dispatch-phase result without CAMPD).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data import eia_loader  # noqa: E402

from _pjm2025_payload_lag import HOURS, best_lag  # noqa: E402
from _pjm2025_phase_drift import std_hour_index  # noqa: E402

HOUR_OF_DAY = np.arange(HOURS) % 24
GEN_DIR = RAW_DATA_DIR / "ISO-specific-gen-data"


def load_pjm_fuel(year: int) -> pd.DataFrame:
    df = pd.read_csv(
        GEN_DIR / f"PJM_{year}_gen_by_fuel.csv",
        usecols=["datetime_beginning_utc", "fuel_type", "mw"],
    )
    utc = pd.DatetimeIndex(
        pd.to_datetime(df["datetime_beginning_utc"], format="%m/%d/%Y %I:%M:%S %p")
    ).tz_localize("UTC")
    df["hoy"] = std_hour_index(utc, year)
    return df[df["hoy"] >= 0]


def fuel_series(df: pd.DataFrame, fuel: str) -> np.ndarray:
    sub = df[df["fuel_type"] == fuel]
    out = np.full(HOURS, np.nan)
    g = sub.groupby("hoy")["mw"].sum()
    out[g.index.to_numpy()] = g.to_numpy(dtype=float)
    return out


def shift_scan(a930: np.ndarray, ref: np.ndarray, label: str) -> None:
    da = np.append(np.diff(a930), np.nan)
    dr = np.append(np.diff(ref), np.nan)
    r = best_lag(da, dr, np.ones(HOURS, dtype=bool))
    print(
        f"    {label}: "
        + " ".join(f"{lag:+d}:{r[lag]:.3f}" for lag in (-2, -1, 0, 1, 2))
        + f"  best={r['best']:+d}"
    )


def main() -> None:
    for year in (2023, 2024, 2025):
        pj = load_pjm_fuel(year)
        frame = eia_loader._eia_hourly_frame_filled("PJM", year)
        w930 = frame["NG: WND"].to_numpy(dtype=float)
        s930 = frame["NG: SUN"].to_numpy(dtype=float)
        g930 = frame["NG: NG"].to_numpy(dtype=float)
        pw = fuel_series(pj, "Wind")
        ps = fuel_series(pj, "Solar")
        pg = fuel_series(pj, "Gas")
        print(f"===== {year}  (930 series vs PJM UTC-stamped feed)")
        shift_scan(w930, pw, "WIND  930 vs PJM")
        shift_scan(s930, ps, "SOLAR 930 vs PJM")
        shift_scan(g930, pg, "GAS   930 vs PJM")
        # absolute solar centroid of the PJM feed (astro sanity), July
        k = np.isfinite(ps) & (ps > 0)
        for mth, lo, hi in (("Jul", 4344, 5088),):
            kk = k & (np.arange(HOURS) >= lo) & (np.arange(HOURS) < hi)
            c = float((ps[kk] * HOUR_OF_DAY[kk]).sum() / ps[kk].sum())
            print(f"    PJM-feed solar centroid {mth}: {c:.2f}")
        # wind diurnal check: mean by hour, peak hour
        wd = np.array([np.nanmean(pw[HOUR_OF_DAY == h]) for h in range(24)])
        wd930 = np.array([np.nanmean(w930[HOUR_OF_DAY == h]) for h in range(24)])
        print(
            f"    wind diurnal argmax: PJM {int(np.nanargmax(wd))}"
            f" vs 930 {int(np.nanargmax(wd930))};"
            f" trough: PJM {int(np.nanargmin(wd))} vs 930 {int(np.nanargmin(wd930))}"
        )


if __name__ == "__main__":
    main()
