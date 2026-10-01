"""SPP-57b FINDING §3.3 (the SPP-57 §5.3 form): hours each link's P1 flow sits at/over a set of ratings,
by direction, from the screen bundle's flows.parquet — a REPORT on the construction question, never a
re-cut (a rating read off these flows would be a fitted value; rule 1). Also the flow percentiles.

usage: uv run python docs/handoffs/spp57b/flows_at_ratings.py <bundle_dir> <year>
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

bundle, year = Path(sys.argv[1]), int(sys.argv[2])
fl = pd.read_parquet(bundle / "flows.parquet")
fl = fl[(fl["pass"] == "P1") & (fl["year"] == year)]
RATINGS = (3400, 4000, 4500, 5000, 6000, 6500, 6700, 8000, 10000, 10700)
for (a, b), grp in fl.groupby(["from_zone", "to_zone"]):
    mw = grp.sort_values("hour")["mw"].to_numpy()
    print(f"\n{a} -> {b} (positive = {a[4:]}->{b[4:]}): flow p1 {np.percentile(mw, 1):+.0f} p10 "
          f"{np.percentile(mw, 10):+.0f} p50 {np.median(mw):+.0f} p90 {np.percentile(mw, 90):+.0f} "
          f"p99 {np.percentile(mw, 99):+.0f} min {mw.min():+.0f} max {mw.max():+.0f}")
    for r in RATINGS:
        pos, neg = int((mw >= r - 1.0).sum()), int((mw <= -r + 1.0).sum())
        print(f"   rating {r:>6,}: at/over bound {pos + neg:>5} h  (+ {pos:>5} / - {neg:>5})")
