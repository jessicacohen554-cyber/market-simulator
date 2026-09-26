#!/usr/bin/env python3
"""miso-276 phase 0 (zero LP): localize the keeper's C3a 2022 low side (-15.4 %).

Reads only the committed keeper hourly sidecars
(``results/calibration/miso275_span/hourly/system_<Y>.parquet``) and the
committed zonal RT actuals (``data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet``,
the miso-269 construction: zonal hub mean, Plains proxied by MINN+ILLINOIS).

Decomposes the load-weighted mean error (model - actual) into:

* months (share of the annual $/MWh gap each month carries);
* the Elliott window (2022-12-22 .. 12-26) and hours with actual RT > $200
  (the C3c tail object) vs the body;
* actual-price deciles (flat across deciles = a level object; concentrated in
  the top decile = a tail object);
* hour of day.

Run on 2022 and a passing comparison year (2023) so the shape is read against a
year the band accepts.

Usage::

    uv run python scripts/probes/_miso276_c3a2022_phase0.py --years 2022 2023 \
        --out results/calibration/_miso276_c3a2022_phase0.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

KEEPER = REPO / "results/calibration/miso275_span"
ACTUALS = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
PLAINS_PROXY = ("MINN.HUB", "ILLINOIS.HUB")
INTERNAL = (
    "MISO-West", "MISO-Plains", "MISO-Illinois", "MISO-Indiana", "MISO-East", "MISO-South",
)
#: Tail threshold, $/MWh — the value the keeper RESULT and C3c commentary quote (116 h > $200).
TAIL = 200.0


def actual_rt(year: int) -> np.ndarray:
    """(zone, T) zonal RT hub-mean LMP on :data:`INTERNAL`'s order."""
    df = pd.read_parquet(ACTUALS)
    df = df[df["year"] == year]
    pv = df.groupby(["hour", "zone"])["rt"].mean().unstack()
    pv["MISO-Plains"] = df[df["hub"].isin(PLAINS_PROXY)].groupby("hour")["rt"].mean()
    pv = pv.reindex(range(8760))
    return pv[list(INTERNAL)].to_numpy(float).T


def model(year: int) -> tuple[np.ndarray, np.ndarray]:
    """(zone, T) keeper P1 price and demand."""
    s = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    p = s.pivot(index="hour", columns="zone", values="price").reindex(range(8760))
    d = s.pivot(index="hour", columns="zone", values="demand").reindex(range(8760))
    return p[list(INTERNAL)].to_numpy(float).T, d[list(INTERNAL)].to_numpy(float).T


def lw(x: np.ndarray, w: np.ndarray) -> float:
    """Load-weighted mean."""
    return float((x * w).sum() / w.sum()) if w.sum() > 0 else float("nan")


def probe(year: int) -> dict:
    """Decompose the LW mean price error for one year."""
    act = actual_rt(year)
    price, dem = model(year)
    ok = np.isfinite(act)
    w = np.where(ok, dem, 0.0)
    a = np.nan_to_num(act)
    W = w.sum()
    m_lw, a_lw = lw(price, w), lw(a, w)
    ts = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(np.arange(8760), "h")
    month = ts.month.to_numpy()
    hod = ts.hour.to_numpy()
    a_sys = (a * w).sum(axis=0) / np.maximum(w.sum(axis=0), 1e-9)
    m_sys = (price * w).sum(axis=0) / np.maximum(w.sum(axis=0), 1e-9)

    def contrib(mask_t: np.ndarray) -> dict:
        k = mask_t[None, :]
        ww = np.where(k, w, 0.0)
        return {
            "hours": int(mask_t.sum()),
            "load_share": round(float(ww.sum() / W), 4),
            "model_lw": round(lw(price, ww), 2),
            "actual_lw": round(lw(a, ww), 2),
            # contribution to the annual LW gap, $/MWh
            "gap_contrib": round(float(((price - a) * ww).sum() / W), 3),
        }

    out = {
        "model_lw": round(m_lw, 3),
        "actual_lw": round(a_lw, 3),
        "err_pct": round(100 * (m_lw / a_lw - 1), 2),
        "gap": round(m_lw - a_lw, 3),
        "hours_actual_gt_tail": int((a_sys > TAIL).sum()),
        "hours_model_gt_tail": int((m_sys > TAIL).sum()),
        "months": {int(m): contrib(month == m) for m in range(1, 13)},
        "hod": {int(h): contrib(hod == h)["gap_contrib"] for h in range(24)},
    }
    elliott = (ts >= f"{year}-12-22") & (ts < f"{year}-12-27")
    tail = a_sys > TAIL
    out["elliott_window"] = contrib(np.asarray(elliott))
    out["tail_hours"] = contrib(tail)
    out["body_ex_tail"] = contrib(~tail)
    out["body_ex_tail_and_elliott"] = contrib(~tail & ~np.asarray(elliott))
    body = ~tail & ~np.asarray(elliott)
    ww = np.where(body[None, :], w, 0.0)
    out["body_err_pct"] = round(100 * (lw(price, ww) / lw(a, ww) - 1), 2)
    q = np.quantile(a_sys, np.linspace(0, 1, 11))
    dec = np.clip(np.searchsorted(q, a_sys, side="right") - 1, 0, 9)
    out["actual_deciles"] = {
        int(d): {**contrib(dec == d), "actual_sys_range": [round(q[d], 1), round(q[d + 1], 1)]}
        for d in range(10)
    }
    out["model_sys_quantiles"] = [round(float(x), 1) for x in np.quantile(m_sys, [0.5, 0.9, 0.99, 0.999, 1])]
    out["actual_sys_quantiles"] = [round(float(x), 1) for x in np.quantile(a_sys, [0.5, 0.9, 0.99, 0.999, 1])]
    return out


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2022, 2023])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    res = {str(y): probe(y) for y in args.years}
    Path(args.out).write_text(json.dumps(res, indent=1) + "\n")
    for y, r in res.items():
        print(y, {k: r[k] for k in ("model_lw", "actual_lw", "err_pct", "gap", "hours_actual_gt_tail",
                                     "hours_model_gt_tail", "body_err_pct")})
        print("  elliott", r["elliott_window"])
        print("  tail   ", r["tail_hours"])
        print("  body   ", r["body_ex_tail_and_elliott"])
        for m, v in r["months"].items():
            print(f"  m{m:02d}", v)
        for d, v in r["actual_deciles"].items():
            print(f"  d{d}", v)
        print("  hod", r["hod"])
        print("  q model", r["model_sys_quantiles"], "actual", r["actual_sys_quantiles"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
