"""PJM-NEXT-24 card 1b (zero LP): is the real fleet's flat response WITHIN plants or ACROSS them?

Card 1 (``_pjmnext24_loading_margin.py``) shows real coal and CT loading respond to the
actual-price margin far less sharply than the keeper's. Two different objects produce that:

- WITHIN-plant: a given plant's own loading barely moves with its own margin over time
  (commitment inertia, uncertainty, reliability runs) - a temporal object;
- ACROSS-plant: each plant follows its margin, but the plants' real cost ordering differs
  from the keeper's offers (per-plant offer level errors) - an ordering object.

Per class and year, margin on actual system RT (``m_rt``) and DA (``m_da``):

- ``within``: capacity-weighted mean over plants of [loading(+10..+40) - loading(-40..-10)]
  using each plant's own hours, plants with >= 100 h in both bins;
- ``across``: OLS slope of plant annual loading on plant mean margin across plants
  (loading per $10), capacity-weighted;
- each for real and keeper output.

Writes ``results/phase0/pjm/_pjmnext24_within_across.json``.
Run: ``python3 scripts/probes/_pjmnext24_within_across.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
from _pjmnext24_loading_margin import ACTUAL, YEARS, plant_hours  # noqa: E402

OUT = REPO / "results/phase0/pjm/_pjmnext24_within_across.json"
MIN_H = 100


def within(p: pd.DataFrame, col: str) -> dict:
    """Capacity-weighted mean within-plant contrast, real and model."""
    rows = []
    for _, g in p.groupby("plant_code"):
        lo = g[(g[col] >= -40) & (g[col] < -10)]
        hi = g[(g[col] >= 10) & (g[col] < 40)]
        if len(lo) < MIN_H or len(hi) < MIN_H:
            continue
        rows.append(
            (
                g.cap.mean(),
                hi.real.sum() / hi.cap.sum() - lo.real.sum() / lo.cap.sum(),
                hi.mw.sum() / hi.cap.sum() - lo.mw.sum() / lo.cap.sum(),
            )
        )
    if not rows:
        return {"plants": 0}
    a = np.array(rows)
    w = a[:, 0] / a[:, 0].sum()
    return {
        "plants": len(rows),
        "real": round(float((w * a[:, 1]).sum()), 3),
        "model": round(float((w * a[:, 2]).sum()), 3),
    }


def across(p: pd.DataFrame, col: str) -> dict:
    """Capacity-weighted OLS slope of plant loading on plant mean margin (per $10)."""
    g = p.groupby("plant_code").agg(
        cap=("cap", "sum"), real=("real", "sum"), mw=("mw", "sum"), m=(col, "mean")
    )
    g = g[g.cap > 0]
    w = g.cap / g.cap.sum()
    x = g.m - (w * g.m).sum()
    out = {"plants": len(g)}
    for who, c in (("real", "real"), ("model", "mw")):
        y = g[c] / g.cap
        out[who] = round(float(10 * (w * x * y).sum() / (w * x * x).sum()), 4)
    return out


def main() -> None:
    """Every year, both classes."""
    act = pd.read_parquet(ACTUAL)
    out: dict = {
        "what": "PJM-NEXT-24 card 1b: within- vs across-plant response. ZERO LP."
    }
    for y in YEARS:
        p = plant_hours(y, act)
        for k, g in p.groupby("k"):
            d = {
                c: {"within": within(g, c), "across": across(g, c)}
                for c in ("m_rt", "m_da")
            }
            out.setdefault(k, {})[str(y)] = d
            print(y, k, d["m_rt"], flush=True)
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
