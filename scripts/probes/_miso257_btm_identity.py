#!/usr/bin/env python3
"""Check the identity every MISO bench part's CHP classes must satisfy.

miso-257, phase 0 (rule 29 ``[R-SCREEN]`` clause 0). ZERO LP.

C1 scores a GRID-ONLY model against ``classFull``, which the rubric defines as
the EIA-923 class total MINUS the per-class behind-the-meter CHP host supply
(``btm.parquet``). So for a CHP class the committed bench part must satisfy::

    classFull[k] == e923_class_total[k] - btm[k]

(to within the small multi-class-split adjustments ``build_payload`` applies).
This probe prints both sides per year, and it is what found the defect: the
identity holds to ``-0.0000`` on MISO CC_CHP in 2020 / 2021 / 2022 / 2024 and is
violated by +17.70 TWh in 2023 and +20.18 TWh in 2025, because the miso-255
registration wrote those two parts without the subtrahend
(``docs/RESULT-miso257-c1-2023-was-a-broken-bench-part-2026-09-13.md`` §2.1).

Run ``scripts/probes/_miso257_bench_rebuild.py <bundle>`` first: ``btm.parquet``
is gitignored and a SLIM committed bundle does not carry it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.lib import backcast_artifacts as ba  # noqa: E402

BENCH = REPO / "frontend" / "data" / "backcast" / "bench"
CHP_CLASSES = ("CC_CHP", "CT_CHP", "ST_CHP")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument(
        "--also",
        nargs="*",
        default=["CC_REGULAR", "COAL_PRB"],
        help="extra (non-CHP) classes to print for context",
    )
    args = ap.parse_args()
    bundle = args.bundle if args.bundle.is_absolute() else REPO / args.bundle

    meta = json.loads((bundle / "meta.json").read_text())
    iso = meta["iso"]
    e923 = pd.read_parquet((bundle / meta["shared_inputs"]["eia923"]).resolve())
    btm = pd.read_parquet(bundle / "btm.parquet")
    btm = btm[btm["pass"] == "P1"]

    print(
        f"{'yr':>5} {'class':<12} {'e923_cls':>10} {'btm':>9} "
        f"{'e923-btm':>10} {'committed':>10} {'diff':>10}"
    )
    worst = 0.0
    for year in sorted(int(y) for y in e923["year"].unique()):
        bench = ba.load_bench_part(BENCH / iso / f"{year}.json.gz")["bench"]
        tot = e923[e923["year"] == year].groupby("klass")["annual_mwh"].sum() / 1e6
        sub = btm[btm["year"] == year].set_index("klass")["btm_twh"].to_dict()
        for k in list(CHP_CLASSES) + list(args.also):
            t = float(tot.get(k, 0.0))
            s = float(sub.get(k, 0.0))
            c = float((bench.get("classFull") or {}).get(k, 0.0))
            d = c - (t - s)
            if k in CHP_CLASSES:
                worst = max(worst, abs(d))
            print(
                f"{year:>5} {k:<12} {t:10.4f} {s:9.4f} {t - s:10.4f} {c:10.4f} {d:+10.4f}"
            )
        print()
    print(f"worst |diff| over the CHP classes: {worst:.4f} TWh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
