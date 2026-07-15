"""Lead-0 probe (part 8) — final localization of the model-side price lead.

1. CLASS-AGGREGATE dispatch phase: sum the payload's per-plant hourly model
   dispatch (CF% x nameplate) over all payload plants present in the bench,
   vs the same-aggregated CAMPD hourly gross. Diff-series best lag per year.
   (Aggregates are smooth; the per-plant test was noisy.)
2. Hour-window localization of the model price lead vs its own input:
   diff-lag restricted to overnight (h0-6), midday (h9-15), evening (h17-22).
   An indexing shift is window-uniform; a ramp/storage mechanism concentrates
   in the ramp windows.
3. BALANCE-2023 solar centroid (is the SOURCE's 2023 solar also ~10.9, i.e.
   1 h early like 2022/2024, before the wide extract's late-shift?).
4. Estimator control: actual DA vs actual RT diff-lag (both real series; a
   non-zero best lag here would flag estimator bias for smooth-vs-spiky
   waveforms).
"""

from __future__ import annotations

import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data import eia_loader  # noqa: E402

from _pjm2025_balance_xcheck import load_balance_pjm, to_hourly  # noqa: E402
from _pjm2025_payload_lag import (  # noqa: E402
    HOURS,
    MONTH_OF_HOY,
    best_lag,
    decode_i16,
    load_payload,
)

BENCH_DIR = REPO / "frontend/data/backcast/bench/PJM"
HOUR_OF_DAY = np.arange(HOURS) % 24


def _dec(s: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(s), dtype=np.uint8).astype(float)


def main() -> None:
    payload = load_payload("2026-07-14-pjm-110-bench-hygiene")
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source" / "actual_lmp_hourly_PJM.parquet"
    )
    print("=" * 72)
    print("1. Class-aggregate model dispatch vs CAMPD aggregate (diff best lag)")
    for year in (2023, 2024, 2025):
        bench = json.loads(
            gzip.decompress((BENCH_DIR / f"{year}.json.gz").read_bytes())
        )
        bp = bench["bench"]["plants"]
        mp = payload["years"][str(year)]["plants"]
        m_tot = np.zeros(HOURS)
        c_tot = np.zeros(HOURS)
        n = 0
        for k, mv in mp.items():
            if k not in bp or "campd" not in bp[k] or bp[k].get("ct_only"):
                continue
            npl = bp[k].get("npl", 1.0)
            m_tot += _dec(mv["m"])[:HOURS] * npl / 100.0
            c_tot += _dec(bp[k]["campd"])[:HOURS] * npl / 100.0
            n += 1
        dm = np.append(np.diff(m_tot), np.nan)
        dc = np.append(np.diff(c_tot), np.nan)
        r = best_lag(dm, dc, np.ones(HOURS, dtype=bool))
        print(
            f"  {year} (n={n}): "
            + " ".join(f"{lag:+d}:{r[lag]:.3f}" for lag in (-2, -1, 0, 1, 2))
            + f" best={r['best']:+d}"
        )

    print("=" * 72)
    print("2. Model price vs exact input net-load: diff-lag by hour window")
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
        exact_net = d + (exp if exp is not None else 0) - w - s - h
        dm = np.append(np.diff(model), np.nan)
        dn = np.append(np.diff(exact_net), np.nan)
        parts = []
        for label, lo, hi in (
            ("h0-6", 0, 6),
            ("h9-15", 9, 15),
            ("h17-22", 17, 22),
        ):
            mask = (HOUR_OF_DAY >= lo) & (HOUR_OF_DAY <= hi)
            r = best_lag(dm, dn, mask)
            parts.append(
                f"{label} "
                + " ".join(f"{lag:+d}:{r[lag]:.2f}" for lag in (-1, 0, 1))
                + f" best={r['best']:+d}"
            )
        print(f"  {year}: " + " | ".join(parts))
        # 4. estimator control on the same year: actual DA vs actual RT
        dda = np.append(np.diff(da), np.nan)
        drt = np.append(np.diff(rt), np.nan)
        r = best_lag(dda, drt, np.ones(HOURS, dtype=bool))
        print(
            "      control dDA~dRT: "
            + " ".join(f"{lag:+d}:{r[lag]:.3f}" for lag in (-1, 0, 1))
            + f" best={r['best']:+d}"
        )

    print("=" * 72)
    print("3. BALANCE solar generation-weighted centroid (source clock)")
    for year in (2023, 2024, 2025):
        bal = load_balance_pjm(year)
        scol = next(
            (
                c
                for c in (
                    "Net Generation (MW) from Solar",
                    "Net Generation (MW) from Solar without Integrated Battery Storage",
                )
                if c in bal.columns
            ),
            None,
        )
        bs = to_hourly(bal, scol, year)
        cents = []
        for mth in (1, 4, 7, 10):
            k = (MONTH_OF_HOY == mth) & np.isfinite(bs) & (bs > 0)
            wgt = bs[k]
            cents.append(
                float((wgt * HOUR_OF_DAY[k]).sum() / wgt.sum())
                if wgt.sum() > 0
                else np.nan
            )
        print(
            f"  {year}: Jan {cents[0]:.2f} Apr {cents[1]:.2f}"
            f" Jul {cents[2]:.2f} Oct {cents[3]:.2f}"
        )


if __name__ == "__main__":
    main()
