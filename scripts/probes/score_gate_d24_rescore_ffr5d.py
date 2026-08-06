"""D-24 re-emit: the two FFR-5D arms' retirement scorecards, before vs after.

Owner decision **D-24** (sitting Addendum X.6, 2026-08-06) redefines the
>=300 MW retirement recall gate's denominator as the **reachable** set. This
probe re-grades the two already-registered FFR-5D arms under the new member
rule **without re-solving anything**, and prints the before/after so the change
is auditable at the number rather than at the description.

Committed artifacts only, exactly the FFR-7A re-score construction it extends
(``scripts/probes/ffr7a_rescore_ffr5d_arms.py``): the model side is
reconstructed from each arm's own committed ``crossover_score.json`` per-fuel
``model_gw``, and the grading is done by the shipped
``score_capacity_hindcast.score_retirements`` so the numbers come from the
production scorer, not a re-implementation. ``score_retirements`` consumes the
model side only as per-fuel MW for every banded metric, so total / per-fuel /
recall / false-retire are exact; the un-banded ``plant_recall_frac`` needs model
unit ids the registered bundles carry no ledger for, and is ``None`` here (both
arms committed 0.0, and neither retired any fuel the target's >=300 MW units
belong to, so 0.0 stands either way).

The arms' registered bundles are **NOT touched** and nothing is re-registered —
the output table lives in
``docs/handoffs/score-gate-recall-redefinition-2026-08-06.md``.

Usage::

    uv run python scripts/probes/score_gate_d24_rescore_ffr5d.py
    uv run python scripts/probes/score_gate_d24_rescore_ffr5d.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
for _p in (_ROOT / "src", _ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.probes.ffr7a_rescore_ffr5d_arms import (  # noqa: E402
    ARMS,
    committed_score,
    model_frame,
)
from scripts.score_capacity_hindcast import (  # noqa: E402
    THERMAL_FUELS,
    classify_exit_reachability,
    load_actuals,
    load_solved_scenario_config,
    score_retirements,
    vintage_cutoff_of,
)

ISO = "ERCOT"


def _recall_cell(rr: dict) -> str:
    """``matched/members (band)`` — or ``n/a`` when no member is reachable."""
    if rr.get("n_a"):
        return f"n/a (0 of {rr['n_target_large']} reachable)"
    pct = "—" if rr["recall"] is None else format(rr["recall"], ".0%")
    return f"{rr['matched']}/{rr['n_big_actual']} = {pct} ({rr['band']})"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path, default=None, help="also write the payload")
    args = ap.parse_args(argv)

    actuals = load_actuals(ISO)
    act = actuals[actuals["kind"] == "retirement"]
    act_th = act[act["fuel"].isin(THERMAL_FUELS)]
    print(
        f"corrected {ISO} target: {len(act)} retirement rows, thermal "
        f"{act_th['mw'].sum() / 1000.0:.3f} GW over {sorted(set(act['year']))}"
    )

    payload: dict = {"iso": ISO, "arms": {}}
    reach_shared: dict | None = None
    for arm, bundle in ARMS.items():
        bundle = Path(bundle)
        solved = load_solved_scenario_config(bundle)
        reach = classify_exit_reachability(
            ISO,
            actuals,
            vintage_cutoff=vintage_cutoff_of(None, solved),
            solved_config=solved,
        )
        reach_shared = reach_shared or reach
        model = model_frame(committed_score(bundle))
        before = score_retirements(model, actuals)
        after = score_retirements(model, actuals, reach)

        b, a = before["unit_recall_gt300"], after["unit_recall_gt300"]
        print(f"\n=== {arm} ({bundle}) ===")
        print(
            f"  use_campd_bins={(solved or {}).get('use_campd_bins')} "
            f"vintage={(solved or {}).get('eia860_vintage_year')} "
            f"cutoff={reach['vintage_cutoff']}"
        )
        print(f"  recall BEFORE (pre-D-24): {_recall_cell(b)}")
        print(f"  recall AFTER  (D-24)    : {_recall_cell(a)}")
        for key, label in (
            ("total_gw", "thermal GW retired"),
            ("false_retire", "false-retire"),
        ):
            assert before[key] == after[key], f"{key} moved — D-24 is recall-only"
            print(f"  {label}: band {after[key]['band']} (UNCHANGED by D-24)")
        payload["arms"][arm] = {
            "bundle": str(bundle),
            "before": b,
            "after": a,
            "total_gw": after["total_gw"],
            "false_retire": after["false_retire"],
            "per_fuel": after["per_fuel"],
        }

    assert reach_shared is not None
    payload["reachability"] = reach_shared
    print(
        f"\nreachability (identical for both arms — a property of the target and "
        f"the fleet basis, not of the screen): {reach_shared['n_members']} member(s) "
        f"of {reach_shared['n_target_large']} target rows >= "
        f"{reach_shared['large_unit_mw']:.0f} MW; {len(reach_shared['excluded'])} "
        f"unreachable rows reported, {reach_shared['n_excluded_gated']} of them gated."
    )
    print("\n| unit | MW | fuel | exit | reason | gated |")
    print("|---|--:|---|--:|---|:--|")
    for r in reach_shared["excluded"]:
        print(
            f"| `{r['unit_id']}` {r['unit_name']} | {r['mw']} | {r['fuel']} | "
            f"{r['exit_year']} | {r['reason']} | {'yes' if r['gated'] else 'no'} |"
        )

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2, default=str))
        print(f"\n[wrote] {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
