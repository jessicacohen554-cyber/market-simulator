"""Lead-0 probe (part 5) — is the model's "1 h early price" a plateau artifact?

LP duals form exact plateaus (storage water-value / same-marginal-unit hours);
np.argmax on a plateau returns its FIRST hour, biasing daily-peak stats early.
This probe:
  1. measures model-price daily-max plateau width (hours within $0.51 of max,
     int16 rounding) vs the actual RT's plateau width;
  2. recomputes the daily-peak offsets using the plateau CENTER;
  3. cross-correlates first-differenced series (phase-sharp, waveform-robust):
     dModel vs dActual-RT, dModel vs dExact-input, per season/year.
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
from _pjm2025_payload_lag import (  # noqa: E402
    HOURS,
    MONTH_OF_HOY,
    SEASONS,
    best_lag,
    decode_i16,
    load_payload,
)


def plateau_center_hours(x: np.ndarray, tol: float = 0.51) -> tuple[np.ndarray, list]:
    """Center of each day's max plateau (mean of hours within tol of max)."""
    days = x[: 365 * 24].reshape(365, 24)
    out = np.full(365, -1.0)
    widths = []
    for i, row in enumerate(days):
        if np.isfinite(row).sum() < 20:
            continue
        mx = np.nanmax(row)
        plateau = np.where(row >= mx - tol)[0]
        widths.append(len(plateau))
        out[i] = plateau.mean()
    return out, widths


def offset_stats_float(a: np.ndarray, b: np.ndarray, label: str) -> None:
    ok = (a >= 0) & (b >= 0)
    d = a[ok] - b[ok]
    d = ((d + 12) % 24) - 12
    print(f"    {label}: median {np.median(d):+.2f} mean {d.mean():+.2f} n={len(d)}")


def main() -> None:
    payload = load_payload("2026-07-14-pjm-110-bench-hygiene")
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source" / "actual_lmp_hourly_PJM.parquet"
    )
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
        h = frame["NG: WAT"].interpolate().bfill().ffill().to_numpy(dtype=float)
        exp = eia_loader.pjm_net_interchange(year)
        if exp is None:
            exp = np.zeros(HOURS)
        exact_net = d + exp - w - s - h

        mc, mw_ = plateau_center_hours(model)
        ac, aw = plateau_center_hours(rt_padded)
        nc, _ = plateau_center_hours(exact_net, tol=50.0)  # MW tol for load
        print(f"===== {year}")
        print(
            f"  plateau width (h at daily max): model mean {np.mean(mw_):.2f}"
            f" p90 {np.percentile(mw_, 90):.0f} | actual mean {np.mean(aw):.2f}"
        )
        offset_stats_float(mc, ac, "plateau-center: model vs actual-RT ")
        offset_stats_float(mc, nc, "plateau-center: model vs exact-net ")
        # differenced-series lag correlation
        dm = np.diff(model)
        da_ = np.diff(rt_padded)
        dn = np.diff(exact_net)
        for ssn in ("DJF", "MAM", "JJA", "SON"):
            mask = np.isin(MONTH_OF_HOY, SEASONS[ssn])[1:]
            r1 = best_lag(
                np.append(dm, np.nan), np.append(da_, np.nan), np.append(mask, False)
            )
            r2 = best_lag(
                np.append(dm, np.nan), np.append(dn, np.nan), np.append(mask, False)
            )
            print(
                f"  diff {ssn}: dM~dA "
                + " ".join(f"{lag:+d}:{r1[lag]:.3f}" for lag in (-1, 0, 1))
                + f" best={r1['best']:+d} | dM~dN "
                + " ".join(f"{lag:+d}:{r2[lag]:.3f}" for lag in (-1, 0, 1))
                + f" best={r2['best']:+d}"
            )


if __name__ == "__main__":
    main()
