"""Lead-0 probe (part 3) — event-based (like-vs-like) phase tests.

Correlation-lag estimates can be biased by waveform asymmetry (price is a
convex, peak-sharpened function of net load), so this probe uses discrete
daily events instead:

1. Daily-peak/trough hour offsets: model price vs actual RT price, input
   net-load vs actual RT price, model price vs input net-load. Median and
   mode of the circular hour difference per year. A real 1 h phase shift
   moves the whole distribution by 1; waveform asymmetry does not.
2. Solar absolute clock: per-year July/January median first- and last-
   generation positions (2 % of daily max threshold) for NG: SUN on the
   chronological EST clock, against the astronomical envelope of the PJM
   fleet (July: first light ~position 4-5 [NJ/VA sunrise 4:35-5:01 EST],
   last light ~position 19-20 [IL sunset 20:29 EST]). Decides which solar
   vintage (10.9 vs 11.9 centroid) is on the true clock.
3. Same daily-peak test for EIA-930 demand vs PJM's own UTC-stamped meter
   (ground truth control).
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
from _pjm2025_payload_lag import decode_i16, load_payload  # noqa: E402
from _pjm2025_phase_drift import load_metered_total  # noqa: E402

HOURS = 8760
_MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MONTH_START = np.concatenate([[0], np.cumsum(_MONTH_DAYS)[:-1]]) * 24


def daily_extreme_hours(x: np.ndarray, kind: str = "max") -> np.ndarray:
    """Hour-of-day (0..23) of each day's extreme; NaN days -> -1."""
    days = x[: 365 * 24].reshape(365, 24)
    out = np.full(365, -1)
    for i, row in enumerate(days):
        if np.isfinite(row).sum() < 20:
            continue
        out[i] = int(np.nanargmax(row) if kind == "max" else np.nanargmin(row))
    return out


def offset_stats(a: np.ndarray, b: np.ndarray, label: str) -> None:
    """Distribution of circular difference a-b (daily event hours)."""
    ok = (a >= 0) & (b >= 0)
    d = a[ok] - b[ok]
    d = ((d + 12) % 24) - 12  # wrap to [-12, 12)
    vals, counts = np.unique(d, return_counts=True)
    top = sorted(zip(counts, vals), reverse=True)[:4]
    top_s = " ".join(f"{v:+d}h:{c / len(d):.0%}" for c, v in top)
    print(
        f"    {label}: median {np.median(d):+.1f} mean {d.mean():+.2f}"
        f"  [{top_s}] n={len(d)}"
    )


def sun_edges(sun: np.ndarray, months: tuple[int, ...]) -> tuple[float, float]:
    """Median first/last generation position (2% of daily max) over months."""
    firsts, lasts = [], []
    day0 = 0
    for m in range(1, 13):
        for _ in range(_MONTH_DAYS[m - 1]):
            if m in months:
                row = sun[day0 * 24 : (day0 + 1) * 24]
                if np.isfinite(row).sum() >= 20 and np.nanmax(row) > 0:
                    thr = 0.02 * np.nanmax(row)
                    nz = np.where(row > thr)[0]
                    if len(nz):
                        firsts.append(nz[0])
                        lasts.append(nz[-1])
            day0 += 1
    return float(np.median(firsts)), float(np.median(lasts))


def main() -> None:
    payload = load_payload("2026-07-14-pjm-110-bench-hygiene")
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source" / "actual_lmp_hourly_PJM.parquet"
    )
    print("=" * 72)
    print("1+3. Daily-peak-hour offsets (positive = first series peaks LATER)")
    for year in (2023, 2024, 2025):
        delta = decode_i16(payload["years"][str(year)]["lmpDeltaHr"])
        sub = lmp[lmp["year"] == year].set_index("hour")
        rt = np.full(HOURS, np.nan)
        rt[sub.index.to_numpy()] = sub["rt"].to_numpy()
        da = np.full(HOURS, np.nan)
        da[sub.index.to_numpy()] = sub["da"].to_numpy()
        rt_padded = np.where(np.isfinite(rt), rt, da)
        model = rt_padded + delta

        frame = eia_loader._eia_hourly_frame_filled("PJM", year)
        d = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
        w = frame["NG: WND"].interpolate().bfill().ffill().to_numpy(dtype=float)
        s = frame["NG: SUN"].interpolate().bfill().ffill().to_numpy(dtype=float)
        net = d - w - s
        met = load_metered_total(year)

        mp = daily_extreme_hours(model)
        ap = daily_extreme_hours(rt_padded)
        np_ = daily_extreme_hours(net)
        dp = daily_extreme_hours(d)
        metp = daily_extreme_hours(met)
        print(f"  {year}:")
        offset_stats(mp, ap, "model-price peak  vs actual-RT peak ")
        offset_stats(mp, np_, "model-price peak  vs input-netload peak")
        offset_stats(np_, ap, "input-netload peak vs actual-RT peak")
        offset_stats(dp, metp, "930-demand peak   vs PJM-meter peak ")
        # troughs (overnight min) too — phase check away from the peak
        mt = daily_extreme_hours(model, "min")
        at = daily_extreme_hours(rt_padded, "min")
        offset_stats(mt, at, "model-price trough vs actual-RT trough")

    print("=" * 72)
    print("2. NG: SUN first/last generation position (2% threshold, median)")
    print("   expected if aligned: Jul first 4-5 / last 19-20; Jan first 7 / last 17")
    for year in (2022, 2023, 2024, 2025):
        frame = eia_loader._eia_hourly_frame_filled("PJM", year)
        if frame is None:
            continue
        s = frame["NG: SUN"].to_numpy(dtype=float)
        jf, jl = sun_edges(s, (7,))
        wf, wl = sun_edges(s, (1,))
        print(
            f"  {year}: Jul first {jf:.0f} last {jl:.0f} | Jan first {wf:.0f} last {wl:.0f}"
        )


if __name__ == "__main__":
    main()
