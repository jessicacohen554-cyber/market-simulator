"""PJM-NEXT-11 card 3 (zero LP): is the C3a/C3b miss variance compression or a level shift?

Model = the keeper's committed ``hourly/system_<y>.parquet`` P1 price, load-weighted across
zones per hour. Actual = ``data/raw/_validation-source/actual_lmp_hourly_PJM.parquet`` RT (the
C3a/C3b bench kind for PJM). Sorted-quantile decomposition: the annual mean error equals the mean
of (sorted model - sorted actual), so its share in each quantile band says whether the miss is a
level shift (spread across bands) or a tail/compression object (concentrated at the ends).
Writes ``results/phase0/pjm/_pjmnext11_c3_compression.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/pjmnext8_xf_span"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
OUT = REPO / "results/phase0/pjm/_pjmnext11_c3_compression.json"
BANDS = ((0.0, 0.10), (0.10, 0.50), (0.50, 0.90), (0.90, 0.99), (0.99, 1.0))


def model_price(y: int) -> tuple[np.ndarray, np.ndarray]:
    """Hourly load-weighted system price and system demand."""
    d = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
    d = d[d["pass"] == "P1"]
    d["pd"] = d.price * d.demand
    g = d.groupby("hour")[["pd", "demand"]].sum().sort_index()
    return (g.pd / g.demand).to_numpy(), g.demand.to_numpy()


def main() -> None:
    """Score every year and write the JSON."""
    act = pd.read_parquet(ACTUAL)
    out = {}
    for y in range(2019, 2026):
        m, load = model_price(y)
        a = act[act.year == y].sort_values("hour").rt.to_numpy()[: len(m)]
        n = min(len(m), len(a))
        m, a, load = m[:n], a[:n], load[:n]
        lw_err = (m * load).sum() / (a * load).sum() - 1
        ms, as_ = np.sort(m), np.sort(a)
        diff = ms - as_
        bands = {}
        for lo, hi in BANDS:
            i, j = int(lo * n), int(hi * n)
            bands[f"q{int(lo * 100)}-{int(hi * 100)}"] = round(
                float(diff[i:j].sum() / n), 2
            )
        mon = pd.DataFrame({"m": m * load, "a": a * load, "l": load})
        mon["mo"] = pd.date_range(f"{y}-01-01", periods=n, freq="h").month
        mm = mon.groupby("mo").sum()
        pm, pa = mm.m / mm.l, mm.a / mm.l
        q = [0.10, 0.50, 0.90, 0.99]
        out[y] = {
            "lw_mean_err_pct": round(100 * lw_err, 1),
            "eq_mean_model": round(m.mean(), 2),
            "eq_mean_actual": round(a.mean(), 2),
            "quantile_ratio": {
                f"p{int(x * 100)}": round(
                    float(np.quantile(m, x) / np.quantile(a, x)), 3
                )
                for x in q
            },
            "mean_gap_by_sorted_band_usd": bands,
            "hourly_pearson": round(float(np.corrcoef(m, a)[0, 1]), 3),
            "std_ratio": round(float(m.std() / a.std()), 3),
            "monthly_model": [round(v, 1) for v in pm],
            "monthly_actual": [round(v, 1) for v in pa],
            "monthly_nrmse": round(
                float(np.sqrt(((pm - pa) ** 2).mean()) / pa.mean()), 3
            ),
        }
        print(y, out[y]["lw_mean_err_pct"], out[y]["quantile_ratio"], bands)
    OUT.write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
