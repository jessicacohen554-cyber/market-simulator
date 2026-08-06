"""FFR-7A re-score: the two FFR-5D arms' retirement scorecards vs the fixed target.

Owner decision D-21(b) corrected the capacity-hindcast scoring target so it
measures **physical** exits (``scripts/data/build_capacity_actuals.py``,
FFR-7A). This probe re-grades the two already-registered FFR-5D arms against
the corrected ERCOT target **without re-solving anything**: the model side is
reconstructed from each arm's own committed ``crossover_score.json``
per-fuel ``model_gw``, and the grading is done by the shipped
``score_capacity_hindcast.score_retirements`` so the numbers come from the
production scorer, not a re-implementation.

What is and is not recomputable from committed artifacts. ``score_retirements``
consumes the model side only as **per-fuel MW** for every banded metric
(total, per-fuel, greedy recall, false-retire), so all four are exact. The one
un-banded diagnostic it derives from model *unit ids* —
``plant_recall_frac`` — is not recomputable here (the registered bundles carry
no evolution ledger) and is reported as ``None``; both arms committed 0.0, and
neither arm retired any of the fuels the target's >=300 MW units belong to, so
0.0 stands either way.

The arms' registered bundles are NOT touched and nothing is re-registered —
the output table lives in ``docs/handoffs/ffr-7a-scoring-target-hygiene-*.md``.

Usage::

    uv run python scripts/probes/ffr7a_rescore_ffr5d_arms.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
for _p in (_ROOT / "src", _ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.score_capacity_hindcast import (  # noqa: E402
    THERMAL_FUELS,
    load_actuals,
    score_retirements,
)

ARMS = {
    "shipped": "results/hindcast/ercot-2021-2025-t1ff-armr-ffr5d-shipped",
    "unified": "results/hindcast/ercot-2021-2025-t1ff-armr-ffr5d-unified",
}


def committed_score(bundle: Path) -> dict:
    """The arm's registered ``crossover_score.json`` (one cache dir per arm)."""
    hits = sorted(bundle.glob("*/*/crossover_score.json"))
    if len(hits) != 1:
        raise SystemExit(f"expected exactly one crossover_score.json under {bundle}")
    return json.loads(hits[0].read_text())


def model_frame(score: dict) -> pd.DataFrame:
    """Model retirements as one row per fuel, from the committed per-fuel MW.

    ``score_retirements`` aggregates the model side to per-fuel MW before any
    banded metric is computed, so one row per fuel reproduces every band the
    registered scorecard reports.
    """
    rows = [
        {
            "unit_id": f"{fuel}_committed_pool",
            "fuel": fuel,
            "mw": float(block["model_gw"]) * 1000.0,
            "year": 0,
            "reason": "economic",
        }
        for fuel, block in score["retirements"]["per_fuel"].items()
        if float(block["model_gw"]) > 0.0
    ]
    return pd.DataFrame(rows, columns=["unit_id", "fuel", "mw", "year", "reason"])


def main() -> int:
    actuals = load_actuals("ERCOT")
    act = actuals[actuals["kind"] == "retirement"]
    act_thermal = act[act["fuel"].isin(THERMAL_FUELS)]
    print(
        f"corrected ERCOT target: {len(act)} retirement rows, "
        f"thermal {act_thermal['mw'].sum() / 1000.0:.3f} GW over "
        f"{sorted(set(act['year']))}"
    )
    print(
        "  thermal GW by fuel: "
        + json.dumps(
            (act_thermal.groupby("fuel")["mw"].sum() / 1000.0).round(3).to_dict()
        )
    )

    for arm, path in ARMS.items():
        score = committed_score(_ROOT / path)
        before = score["retirements"]
        after = score_retirements(model_frame(score), actuals)
        after["unit_recall_gt300"]["plant_recall_frac"] = None
        after["unit_recall_gt300"]["plant_matched"] = None
        print(f"\n=== {arm} ({score['run_id']}) ===")
        print("  BEFORE (registered, old target):")
        print("   " + json.dumps(before["total_gw"]))
        print("   recall " + json.dumps(before["unit_recall_gt300"]))
        print("   false  " + json.dumps(before["false_retire"]))
        print("  AFTER (same model side, corrected target):")
        print("   " + json.dumps(after["total_gw"]))
        print("   recall " + json.dumps(after["unit_recall_gt300"]))
        print("   false  " + json.dumps(after["false_retire"]))
        print("  per-fuel (actual_gw before -> after | model_gw):")
        fuels = sorted(set(before["per_fuel"]) | set(after["per_fuel"]))
        for fuel in fuels:
            b = before["per_fuel"].get(fuel, {})
            a = after["per_fuel"].get(fuel, {})
            print(
                f"    {fuel:9s} {b.get('actual_gw', 0.0):7.3f} -> "
                f"{a.get('actual_gw', 0.0):7.3f} | model {a.get('model_gw', 0.0):7.3f}"
                f"  err {a.get('err_frac')}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
