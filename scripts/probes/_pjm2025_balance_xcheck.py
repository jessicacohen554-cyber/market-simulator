"""Lead-0 probe (part 6) — absolute clock anchor via the EIA-930 BALANCE files.

The six-month BALANCE bulk archive carries the same PJM demand/fuel series
with an EXPLICIT hour-ending UTC label ('UTC Time at End of Hour'), giving an
independent absolute-clock copy. For each year (2023/2024/2025):

  1. index BALANCE rows chronologically: value labeled end-of-hour T covers
     [T-1h, T) -> position = std_hour_index(T - 1h);
  2. find the integer shift (-2..+2) that makes the wide extract's Demand and
     NG: SUN columns match the BALANCE series (exact-match fraction);
  3. anchor the BALANCE demand itself against PJM's UTC-stamped meter
     (daily-peak offsets) so the absolute is nailed on BOTH families.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data import eia_loader  # noqa: E402

sys.path.insert(0, str(REPO / "scripts" / "probes"))
from _pjm2025_event_phase import daily_extreme_hours, offset_stats  # noqa: E402
from _pjm2025_phase_drift import (  # noqa: E402
    HOURS,
    load_metered_total,
    std_hour_index,
)

BAL_DIR = RAW_DATA_DIR / "eia-930"


def load_balance_pjm(year: int) -> pd.DataFrame:
    frames = []
    for half in ("Jan_Jun", "Jul_Dec"):
        p = BAL_DIR / f"EIA930_BALANCE_{year}_{half}.parquet"
        if p.exists():
            df = pd.read_parquet(p)
            frames.append(df[df["Balancing Authority"] == "PJM"])
    return pd.concat(frames, ignore_index=True)


def to_hourly(df: pd.DataFrame, col: str, year: int) -> np.ndarray:
    utc_end = pd.DatetimeIndex(
        pd.to_datetime(df["UTC Time at End of Hour"])
    ).tz_localize("UTC")
    start = utc_end - pd.Timedelta(hours=1)
    hoy = std_hour_index(start, year)
    out = np.full(HOURS, np.nan)
    vals = pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float)
    ok = hoy >= 0
    out[hoy[ok]] = vals[ok]
    return out


def match_frac(a: np.ndarray, b: np.ndarray, shift: int) -> float:
    """Fraction of hours where a[k] == b[k+shift] (tol 0.51 MW)."""
    if shift >= 0:
        x, y = a[: HOURS - shift], b[shift:]
    else:
        x, y = a[-shift:], b[: HOURS + shift]
    good = np.isfinite(x) & np.isfinite(y)
    if good.sum() < 100:
        return np.nan
    return float((np.abs(x[good] - y[good]) < 0.51).mean())


def main() -> None:
    solar_cols = [
        "Net Generation (MW) from Solar",
        "Net Generation (MW) from Solar without Integrated Battery Storage",
    ]
    for year in (2023, 2024, 2025):
        bal = load_balance_pjm(year)
        # solar column name differs between taxonomy vintages
        scol = next((c for c in solar_cols if c in bal.columns), None)
        extra = "Net Generation (MW) from Solar with Integrated Battery Storage"
        bd = to_hourly(bal, "Demand (MW)", year)
        bs = to_hourly(bal, scol, year)
        if extra in bal.columns:
            b2 = to_hourly(bal, extra, year)
            bs = np.where(np.isfinite(bs), bs, 0) + np.where(np.isfinite(b2), b2, 0)
            bs[np.isnan(bd)] = np.nan
        frame = eia_loader._eia_hourly_frame_filled("PJM", year)
        wd = frame["Demand"].to_numpy(dtype=float)
        ws = frame["NG: SUN"].to_numpy(dtype=float)
        met = load_metered_total(year)

        print(f"===== {year} (BALANCE rows {len(bal)}, solar col: {scol})")
        for label, wide, balc in (("Demand", wd, bd), ("Solar", ws, bs)):
            fr = {s: match_frac(wide, balc, s) for s in range(-2, 3)}
            best = max(fr, key=lambda s: fr[s] if np.isfinite(fr[s]) else -1)
            print(
                f"  wide vs BALANCE {label}: "
                + " ".join(f"{s:+d}:{fr[s]:.3f}" for s in range(-2, 3))
                + f"  best shift {best:+d}"
            )
        bp = daily_extreme_hours(bd)
        mp = daily_extreme_hours(met)
        offset_stats(bp, mp, "BALANCE demand peak vs PJM meter peak")


if __name__ == "__main__":
    main()
