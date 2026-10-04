#!/usr/bin/env python3
"""closeout-MISO-w2 phase 0 (ZERO LP): decompose C1 CC_REGULAR 2021 by month.

Reads only committed artifacts: the keeper's hourly sidecars
(``results/calibration/closeout_miso_nuc_span``), the outgoing W0 keeper's
sidecars extracted from git (``d57c02e7:results/calibration/w0_miso_span``,
passed as ``--w0-dir``), EIA-923 monthly generation through the benchmark's own
``bench_multiclass.e923_class_monthly`` chain, and the zone-resolved RT price
reference. Per month: model vs EIA-923 by class (keeper class labels), the
nuclear-row change (keeper minus W0) and what it displaced, model vs actual
load-weighted price. Output ``results/phase0/miso/_closeout_miso_w2_cc2021_decomp.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(REPO / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

KEEPER = REPO / "results/calibration/closeout_miso_nuc_span/hourly"
ZONAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
OUT = REPO / "results/phase0/miso/_closeout_miso_w2_cc2021_decomp.json"


def month_of_hour(year: int) -> np.ndarray:
    """Month (1..12) of each of the 8760 model hours (hour 0 = Jan 1 00:00)."""
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    return idx.month.to_numpy()


def class_month(path: Path, year: int) -> pd.DataFrame:
    """TWh per (class, month) from a class_hourly sidecar (P1)."""
    c = pd.read_parquet(path)
    c = c[c["pass"] == "P1"]
    mo = month_of_hour(year)
    c = c.assign(m=mo[c["hour"].to_numpy()])
    return c.groupby(["klass", "m"]).mw.sum().unstack().fillna(0.0) / 1e6


def price_month(path: Path, year: int) -> pd.Series:
    """Model system load-weighted P1 price per month."""
    s = pd.read_parquet(path)
    s = s[(s["pass"] == "P1") & (s["demand"] > 0)]
    mo = month_of_hour(year)
    s = s.assign(m=mo[s["hour"].to_numpy()], pd_=s["price"] * s["demand"])
    g = s.groupby("m")
    return g.pd_.sum() / g.demand.sum()


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--w0-dir", required=True, type=Path)
    ap.add_argument("--years", type=int, nargs="+", default=[2020, 2021])
    a = ap.parse_args()
    from scripts.lib.bench_multiclass import e923_class_monthly

    out: dict = {}
    for y in a.years:
        k = class_month(KEEPER / f"class_hourly_{y}.parquet", y)
        w = class_month(a.w0_dir / f"class_hourly_{y}.parquet", y)
        act: dict[str, np.ndarray] = {}
        for d in e923_class_monthly("MISO", y).values():
            for kl, arr in d.items():
                act[kl] = act.get(kl, 0) + np.asarray(arr, float) / 1e6
        act_df = pd.DataFrame(act).T
        act_df.columns = range(1, 13)
        rows = {}
        for kl in sorted(set(k.index) | set(act_df.index)):
            km = k.loc[kl] if kl in k.index else pd.Series(0.0, index=range(1, 13))
            wm = w.loc[kl] if kl in w.index else pd.Series(0.0, index=range(1, 13))
            am = act_df.loc[kl] if kl in act_df.index else pd.Series(np.nan, index=range(1, 13))
            rows[kl] = {
                "model_twh": round(float(km.sum()), 3),
                "e923_gross_twh": None if am.isna().all() else round(float(am.sum()), 3),
                "model_minus_e923_by_month": [None if np.isnan(v) else round(float(v), 3) for v in (km - am)],
                "keeper_minus_w0_by_month": [round(float(v), 3) for v in (km - wm)],
                "keeper_minus_w0_twh": round(float((km - wm).sum()), 3),
            }
        pk = price_month(KEEPER / f"system_{y}.parquet", y)
        pw = price_month(a.w0_dir / f"system_{y}.parquet", y)
        z = pd.read_parquet(ZONAL)
        out[str(y)] = {
            "classes": rows,
            "model_price_by_month": pk.round(2).tolist(),
            "w0_price_by_month": pw.round(2).tolist(),
            "zonal_columns": list(z.columns)[:12],
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    for y, r in out.items():
        print("==", y)
        for kl, v in r["classes"].items():
            print(f"{kl:13s} model {v['model_twh']:7.2f} e923 {v['e923_gross_twh']}  d(kpr-w0) {v['keeper_minus_w0_twh']:+.2f}")
            print("   m-a:", v["model_minus_e923_by_month"])
            print("   k-w:", v["keeper_minus_w0_by_month"])
        print("price keeper", r["model_price_by_month"])
        print("price w0    ", r["w0_price_by_month"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
