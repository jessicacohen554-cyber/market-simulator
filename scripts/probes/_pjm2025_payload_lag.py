"""Lead-0 probe (part 2) — reconstruct the pjm-110 keeper model price from the
committed payload and localize the 2025 +1 h phase drift.

model_price[k] = actual_rt_padded[k] + lmpDeltaHr[k] (the 2026-07-15 retrofit
re-paired the payload against the corrected chronological actuals, so adding
the current parquet back recovers the model's own load-weighted system price
exactly, to int16 rounding).

Tests, per year (2023/2024/2025), per season and per month:
  1. model price vs corrected actual RT  (reproduces the log-entry table)
  2. model price vs the CURRENT on-disk input net-load (930 D - W - S)
     -- if the model price is in phase with its own net-load input but early
        vs the actual, the drift is INPUT-CONTENT (the extract), not dispatch;
     -- if the model price is early vs its own input, the drift entered
        between input and dual (dispatch-side), which no input fix explains.
Sign convention: best +1 = actual's features land one slot later = model early.
"""

from __future__ import annotations

import base64
import gzip
import json
import re
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
SEASONS = {"DJF": (12, 1, 2), "MAM": (3, 4, 5), "JJA": (6, 7, 8), "SON": (9, 10, 11)}


def month_of_hoy() -> np.ndarray:
    m = np.zeros(HOURS, dtype=int)
    for i in range(12):
        m[_MONTH_START[i] : _MONTH_START[i] + _MONTH_DAYS[i] * 24] = i + 1
    return m


MONTH_OF_HOY = month_of_hoy()


def best_lag(model: np.ndarray, actual: np.ndarray, mask: np.ndarray) -> dict:
    out = {}
    for lag in range(-3, 4):
        if lag >= 0:
            m, a, k = model[: HOURS - lag], actual[lag:], mask[: HOURS - lag]
        else:
            m, a, k = model[-lag:], actual[: HOURS + lag], mask[-lag:]
        good = k & np.isfinite(m) & np.isfinite(a)
        out[lag] = (
            float(np.corrcoef(m[good], a[good])[0, 1]) if good.sum() >= 50 else np.nan
        )
    best = max((v, k) for k, v in out.items() if np.isfinite(v))
    out["best"] = best[1]
    return out


def load_payload(run_id: str) -> dict:
    raw = (REPO / "frontend/data/backcast/runs" / f"{run_id}.js").read_text()
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', raw)
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def decode_i16(s: str) -> np.ndarray:
    arr = np.frombuffer(base64.b64decode(s), dtype="<i2").astype(float)
    arr = arr.copy()
    arr[arr == -32768] = np.nan  # NaN sentinel
    return arr


def main(run_id: str) -> None:
    payload = load_payload(run_id)
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
        net = d - w - s

        print(f"===== {year} (n model hours: {np.isfinite(model).sum()})")
        print("  season | model vs actual-RT        | model vs own net-load input")
        for ssn, months in SEASONS.items():
            mask = np.isin(MONTH_OF_HOY, months)
            r1 = best_lag(model, rt_padded, mask)
            r2 = best_lag(model, net, mask)
            f1 = " ".join(f"{lag:+d}:{r1[lag]:.3f}" for lag in (-1, 0, 1))
            f2 = " ".join(f"{lag:+d}:{r2[lag]:.3f}" for lag in (-1, 0, 1))
            print(f"  {ssn}: {f1} best={r1['best']:+d} | {f2} best={r2['best']:+d}")
        # per-month best lag vs actual (uniformity check)
        rows = []
        for m in range(1, 13):
            mask = MONTH_OF_HOY == m
            r = best_lag(model, rt_padded, mask)
            rows.append(f"{m}:{r['best']:+d}")
        print("  monthly best-lag vs actual:", " ".join(rows))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2026-07-14-pjm-110-bench-hygiene")
