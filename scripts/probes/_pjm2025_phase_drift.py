"""Lead-0 probe — PJM-2025 uniform +1 h phase drift: input-clock or dispatch?

The 2026-07-15 all-ISO scoring-clock fix exposed a UNIFORM (all-four-seasons)
best-lag +1 h in the PJM-2025 keeper price series vs the corrected
chronological actual LMP, flagged as "smells like a 2025-vintage EIA-930
extract phase issue". This probe adjudicates that lead with measured data
only (no LP):

A. Label consistency of the wide `PJM hourly.parquet` extract: Local-UTC
   offset by month/year (a mislabeled UTC column would show here).
B. Astronomical anchor: NG: SUN monthly generation-weighted centroid
   hour-of-day on the chronological clock, per year. Solar noon cannot move
   year-over-year; a uniform 2025 shift marks the extract content.
C. Decisive independent-meter test: EIA-930 Demand vs PJM's own
   `hrl_load_metered` (datetime_beginning_utc-stamped) summed system load,
   cross-correlated at lags -3..+3 on the chronological clock, per
   year/season. PJM's meter export carries real UTC instants, so a non-zero
   best lag isolates which side is drifted.
D. Model-input net-load (930 demand - 930 wind - 930 solar) vs the corrected
   actual RT LMP (`actual_lmp_hourly_PJM.parquet`), lag test per year/season
   — reproduces the payload-side +1 signature from the raw inputs alone if
   the input clock is the carrier.

Sign convention matches the 2026-07-15 log entry: best lag +1 means the
actual's features land one slot LATER than the model series' (model early).
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

HOURS = 8760
_MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MONTH_START = np.concatenate([[0], np.cumsum(_MONTH_DAYS)[:-1]]) * 24
PJM_STD = "Etc/GMT+5"  # EST, fixed — the model's chronological clock
SEASONS = {
    "DJF": (12, 1, 2),
    "MAM": (3, 4, 5),
    "JJA": (6, 7, 8),
    "SON": (9, 10, 11),
}


def std_hour_index(ts: pd.DatetimeIndex, year: int) -> np.ndarray:
    """Chronological hour-of-year (model calendar) for tz-aware instants."""
    std = ts.tz_convert(PJM_STD)
    month = np.asarray(std.month)
    day = np.asarray(std.day)
    idx = _MONTH_START[month - 1] + (day - 1) * 24 + np.asarray(std.hour)
    ok = (np.asarray(std.year) == year) & ~((month == 2) & (day == 29))
    return np.where(ok, idx, -1)


def month_of_hoy() -> np.ndarray:
    """Month (1..12) for each chronological hour-of-year slot."""
    m = np.zeros(HOURS, dtype=int)
    for i in range(12):
        start = _MONTH_START[i]
        end = start + _MONTH_DAYS[i] * 24
        m[start:end] = i + 1
    return m


MONTH_OF_HOY = month_of_hoy()
HOUR_OF_DAY = np.arange(HOURS) % 24


def best_lag(model: np.ndarray, actual: np.ndarray, mask: np.ndarray) -> dict:
    """r at lags -3..+3 of `actual` vs `model` on masked hours.

    Positive lag = actual shifted EARLIER matches model, i.e. the actual's
    features land later than the model's (log-entry sign convention: r@+1
    compares model[k] with actual[k+1]).
    """
    out = {}
    for lag in range(-3, 4):
        if lag >= 0:
            m = model[: HOURS - lag]
            a = actual[lag:]
            k = mask[: HOURS - lag]
        else:
            m = model[-lag:]
            a = actual[: HOURS + lag]
            k = mask[-lag:]
        good = k & np.isfinite(m) & np.isfinite(a)
        if good.sum() < 100:
            out[lag] = np.nan
            continue
        out[lag] = float(np.corrcoef(m[good], a[good])[0, 1])
    best = max((v, k) for k, v in out.items() if np.isfinite(v))
    out["best"] = best[1]
    return out


def season_mask(season: str) -> np.ndarray:
    months = SEASONS[season]
    return np.isin(MONTH_OF_HOY, months)


# ---------------------------------------------------------------- A: labels
def check_labels() -> None:
    print("=" * 72)
    print("A. Wide-extract label consistency (Local time - UTC time, h)")
    df = pd.read_parquet(RAW_DATA_DIR / "eia-930-hourly" / "PJM hourly.parquet")
    df = df[df["Local date"].dt.year.isin([2022, 2023, 2024, 2025, 2026])]
    off = ((df["Local time"] - df["UTC time"]).dt.total_seconds() / 3600.0).astype(int)
    tab = (
        pd.DataFrame(
            {
                "year": df["Local date"].dt.year,
                "month": df["Local date"].dt.month,
                "off": off,
            }
        )
        .groupby(["year", "month"])["off"]
        .agg(["min", "max"])
        .unstack("month")
    )
    print(tab.to_string())
    # Detect any duplicated/missing UTC hours per year
    for y in (2023, 2024, 2025):
        sub = df[df["Local date"].dt.year == y]
        dup = sub["UTC time"].duplicated().sum()
        print(f"  {y}: rows={len(sub)} dup-UTC={dup}")


# ------------------------------------------------------------- B: solar sun
def check_solar_anchor() -> None:
    print("=" * 72)
    print("B. NG: SUN generation-weighted centroid hour (chronological clock)")
    rows = {}
    for y in (2022, 2023, 2024, 2025):
        frame = eia_loader._eia_hourly_frame_filled("PJM", y)
        if frame is None:
            print(f"  {y}: no frame")
            continue
        sun = frame["NG: SUN"].to_numpy(dtype=float)
        cent = []
        for m in range(1, 13):
            k = (MONTH_OF_HOY == m) & np.isfinite(sun) & (sun > 0)
            w = sun[k]
            h = HOUR_OF_DAY[k]
            cent.append(float((w * h).sum() / w.sum()) if w.sum() > 0 else np.nan)
        rows[y] = cent
    tab = pd.DataFrame(rows, index=range(1, 13)).T
    print(tab.round(2).to_string())
    print("  (row = year, col = month; solar noon is astronomically fixed —")
    print("   any uniform year-over-year shift is an extract clock artifact)")


# ----------------------------------------------- C: independent meter check
def load_metered_total(year: int) -> np.ndarray:
    """PJM hrl_load_metered summed system load on the chronological clock."""
    path = RAW_DATA_DIR / "zone-specific-demand" / f"PJM{year}_hrl_load_metered.csv"
    df = pd.read_csv(path, usecols=["datetime_beginning_utc", "mw"])
    utc = pd.DatetimeIndex(
        pd.to_datetime(df["datetime_beginning_utc"], format="%m/%d/%Y %I:%M:%S %p")
    ).tz_localize("UTC")
    hoy = std_hour_index(utc, year)
    out = np.full(HOURS, np.nan)
    tot = pd.Series(df["mw"].to_numpy()).groupby(hoy).sum()
    tot = tot[tot.index >= 0]
    out[tot.index.to_numpy()] = tot.to_numpy()
    return out


def check_meter_vs_930() -> None:
    print("=" * 72)
    print("C. EIA-930 Demand vs PJM hrl_load_metered (UTC-stamped), lag r")
    for y in (2023, 2024, 2025):
        frame = eia_loader._eia_hourly_frame_filled("PJM", y)
        d930 = frame["Demand"].to_numpy(dtype=float)
        met = load_metered_total(y)
        print(f"  {y}:")
        for s in ("DJF", "MAM", "JJA", "SON"):
            r = best_lag(d930, met, season_mask(s))
            print(
                f"    {s}: "
                + " ".join(f"{lag:+d}:{r[lag]:.4f}" for lag in range(-2, 3))
                + f"  best={r['best']:+d}"
            )
        # level check too
        good = np.isfinite(d930) & np.isfinite(met)
        print(
            f"    level: 930 mean {np.nanmean(d930):,.0f} vs meter"
            f" {np.nanmean(met):,.0f} MW; r@0 full-year"
            f" {np.corrcoef(d930[good], met[good])[0, 1]:.4f}"
        )


# ------------------------------------------- D: input net-load vs actual LMP
def check_netload_vs_lmp() -> None:
    print("=" * 72)
    print("D. Model-input net-load (930 D - W - S) vs corrected actual RT LMP")
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source" / "actual_lmp_hourly_PJM.parquet"
    )
    for y in (2023, 2024, 2025):
        frame = eia_loader._eia_hourly_frame_filled("PJM", y)
        d = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
        w = frame["NG: WND"].interpolate().bfill().ffill().to_numpy(dtype=float)
        s = frame["NG: SUN"].interpolate().bfill().ffill().to_numpy(dtype=float)
        net = d - w - s
        sub = lmp[lmp["year"] == y].set_index("hour")
        rt = np.full(HOURS, np.nan)
        rt[sub.index.to_numpy()] = sub["rt"].to_numpy()
        print(f"  {y}:")
        for ssn in ("DJF", "MAM", "JJA", "SON"):
            r = best_lag(net, rt, season_mask(ssn))
            print(
                f"    {ssn}: "
                + " ".join(f"{lag:+d}:{r[lag]:.4f}" for lag in range(-2, 3))
                + f"  best={r['best']:+d}"
            )


if __name__ == "__main__":
    check_labels()
    check_solar_anchor()
    check_meter_vs_930()
    check_netload_vs_lmp()
