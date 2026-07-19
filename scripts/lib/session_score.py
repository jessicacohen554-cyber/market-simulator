"""Session-score library: class-table build + size-aware pass/fail judge.

The CLI that prints the report lives in ``scripts/session_score.py``; this
module holds the reusable pieces (``class_table``, ``judge`` and the gate
constants) so the probes and the CLI share one implementation.

GRID-DELIVERED basis (2026-06-14, user directive): the gate judges what the LP
actually dispatches to the grid against what actually reached the grid — model
= the grid LP dispatch (NO behind-the-meter CHP add-back), actual = EIA-923
whole-plant MINUS the per-class BTM host supply (= grid-delivered generation by
class). The BTM host steam is held out of the LP, so crediting the model for it
would score generation the model never optimized; gating grid-vs-grid removes
that. (The absolute miss is identical to the old whole-plant basis — the BTM
cancels — but the percentages are now honest grid-delivered errors.)
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.bundle_io import bundle_input_path  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
CLASSES = [
    "CC_REGULAR",
    "CC_CHP",
    "COAL_PRB",
    "ST_GAS",
    "COAL_LIGNITE",
    "CT_PEAKER",
    "CT_CHP",
]
GUARD_PLANTS = {6146: "Martin Lake", 298: "Limestone"}


def class_table(run: str) -> pd.DataFrame:
    d = ROOT / run
    e923 = pd.read_parquet(bundle_input_path(d, "eia923"))
    btm = pd.read_parquet(d / "btm.parquet")
    rows = []
    for f in sorted((d / "dispatch").glob("*_P1.parquet")):
        disp = pd.read_parquet(f, columns=["year", "klass", "mw"])
        year = int(disp["year"].iloc[0])
        grid = disp.groupby("klass")["mw"].sum() / 1e6
        b = btm[(btm["year"] == year) & (btm["pass"] == "P1")]
        bt = dict(zip(b["klass"], b["btm_twh"]))
        bench = e923[e923["year"] == year].groupby("klass")["annual_mwh"].sum() / 1e6
        # System grid-delivered totals for the 2026-06-15 universal class gate:
        # model = Σ grid-LP over every class; actual = Σ (EIA-923 − BTM). (The
        # authoritative gate, scripts/calibration_verdict.py, takes non-fossil
        # nuclear/wind/solar from EIA-930; this diagnostic stays on the 923 basis
        # it already loads — a sub-percent difference in the system total.)
        m_tot = float(grid.sum())
        a_tot = float(bench.sum()) - sum(bt.values())
        for cls in CLASSES:
            # Grid-delivered: model = grid LP only; actual = 923 whole-plant
            # minus the class's BTM host supply.
            m = grid.get(cls, 0.0)
            a = bench.get(cls, 0.0) - bt.get(cls, 0.0)
            rows.append(
                {
                    "year": year,
                    "class": cls,
                    "model": m,
                    "bench": a,
                    "m_tot": m_tot,
                    "a_tot": a_tot,
                }
            )
    return pd.DataFrame(rows)


# C1 fuel-mix — the universal class gate (matches
# calibration_verdict.score_fuelmix and the run explorer's classInTol,
# docs/codebase-site/backcast-runs.html): a class
# passes iff BOTH its grid-delivered volume miss is within min(2.0% of ISO annual
# generation, 8 TWh) AND its share of total generation is within 3.0 pp of actual.
# (2026-07-02 rubric re-balance: loosened from 1.0%/5 TWh/1.5 pp — must stay in
# lockstep with calibration_verdict.FUELMIX_* constants.)
VOL_GEN_FRAC = 0.02
VOL_CAP_TWH = 8.0
SHARE_PP = 3.0


def judge(row) -> str:
    if row["class"] == "CT_CHP":
        return "excl"
    vol_ok = abs(row["model"] - row["bench"]) <= min(
        VOL_GEN_FRAC * row["a_tot"], VOL_CAP_TWH
    )
    share_pp = 100.0 * row["model"] / row["m_tot"] - 100.0 * row["bench"] / row["a_tot"]
    share_ok = abs(share_pp) <= SHARE_PP
    return "PASS" if vol_ok and share_ok else "FAIL"
