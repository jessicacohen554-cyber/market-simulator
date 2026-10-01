#!/usr/bin/env python3
"""miso-285 phase 0 (ZERO LP): night (h0-5) dispatch by keeper class, model vs CAMPD.

Model side: the keeper's committed P1 ``class_hourly``. Actual side: the
benchmark CAMPD net-MW frame, each plant mapped to its class by the
benchmark's own EIA-923 plant->class rows (``build_benchmark_frames``). CHP
classes carry the host-steam basis caveat (miso-116), so they are reported
but not read as a level. Output: ``results/phase0/miso/_miso285_night_class_census.json``.
Rule 13: nothing here feeds a solve.
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/miso280_span"
CLASSES = [
    "COAL_BIT",
    "COAL_LIGNITE",
    "COAL_PRB",
    "CC_REGULAR",
    "CC_CHP",
    "CT_CHP",
    "ST_CHP",
    "ST_GAS",
    "CT_PEAKER",
    "OTHER",
]


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--bench-pkl", required=True)
    args = ap.parse_args()
    fr = pickle.load(open(args.bench_pkl, "rb"))
    e923, campd = fr["eia923"], fr["campd"]
    out = {}
    for y in range(2019, 2026):
        cls = (
            e923[(e923.year == y) & e923.klass.isin(CLASSES)]
            .sort_values("annual_mwh", ascending=False)
            .drop_duplicates("plant_id")
            .set_index("plant_id")
            .klass
        )
        c = campd[campd.year == y]
        c = c[c.plant_id.isin(cls.index)]
        c = c.assign(klass=cls.reindex(c.plant_id.to_numpy()).to_numpy())
        night = c.hour % 24 < 6
        act = c[night].groupby("klass").net_mw.sum() / (365 * 6)
        actd = c[~night].groupby("klass").net_mw.sum() / (365 * 18)
        ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        n = ch.hour % 24 < 6
        mod = ch[n].groupby("klass", observed=True).mw.sum() / (365 * 6)
        modd = ch[~n].groupby("klass", observed=True).mw.sum() / (365 * 18)
        out[str(y)] = {
            k: {
                "night_model": round(float(mod.get(k, 0)), 0),
                "night_campd": round(float(act.get(k, 0)), 0),
                "day_model": round(float(modd.get(k, 0)), 0),
                "day_campd": round(float(actd.get(k, 0)), 0),
            }
            for k in CLASSES
        }
    (REPO / "results/phase0/miso/_miso285_night_class_census.json").write_text(
        json.dumps(out, indent=1)
    )
    print("night MW  model-campd (campd)   | day model-campd")
    for y, v in out.items():
        print(
            y,
            " ".join(
                f"{k[:7]}:{r['night_model'] - r['night_campd']:+5.0f}({r['night_campd']:5.0f})|{r['day_model'] - r['day_campd']:+5.0f}"
                for k, r in v.items()
            ),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
