#!/usr/bin/env python3
"""Write the pjm-h13 ARM's governance attestation (C6) for both composed bundles.

THE DELTA IS ONE ScenarioConfig FLAG — ``netload_drag_merit_allocation``
False -> True — applied to the PJM keeper's own recipe through
``replay_keeper.py --set``. No code changed on the solve path, no scalar was
derived, and no default was flipped.

Rule 21 ``[R-DOF]``: the swap adds **zero free parameters**. The merit fill's
block sizes are the frozen binning artifact's existing tranche capacities and
the fill order is the fleet's own bid heat rates — nothing is derived, fitted
or swept — so the incumbent keeper's DOF ledger is carried VERBATIM, with
``n_entries`` and ``n_residual`` unchanged.

Rule 19 ``[R-ONE-MECH]``: no new floor, no membership change and no second
mechanism id. Only the level source per row moves, which is the same swap
``st_gas_mustrun_level_p25`` already makes on its own floor. D-2/D-4
attribution is therefore unchanged and the forced share stays measurable.

Rule 13 ``[R-MEASURED]``: forward-native. The field is deliberately NOT in
``_BACKCAST_ONLY_OVERLAY_FIELDS`` — a forecast year has heat rates, a net load
and a tranche structure, so the identical construction regenerates forward.

Usage::

    python scripts/gen_pjm_h13_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INCUMBENT = REPO / "results/calibration/pjm_h11_keeper_span"
TARGETS = (
    REPO / "results/calibration/pjm_h13_meritalloc_span",
    REPO / "results/calibration/pjm_h13_meritalloc_touchpoint",
)

PINNED_SHA = "ed3f5efdbcdd20a6317eb05add357f1909a736d6"

NOTE = (
    "ONE ScenarioConfig FLAG ON THE KEEPER'S OWN RECIPE: "
    "netload_drag_merit_allocation False -> True, applied via "
    "scripts/replay_keeper.py --set. No solve-path code changed, no scalar "
    "derived, no default flipped. THE DEFECT IT REPAIRS is rule 17 "
    "[R-FLOOR-WINDOW] and is read off the INCUMBENT KEEPER'S OWN COMMITTED "
    "legitimacy_diagnostics.json, never off a price or volume residual: "
    "st_netload_drag floors exactly four plants of an 8.95 GW ST_GAS "
    "population, and 3131 Shawville and 3138 New Castle carry a measured "
    "median of EXACTLY 0.000 MW over the hours the floor asserts they must be "
    "online, while 3148 Martins Creek (1700 MW) and 3149 Montour (1504 MW) - "
    "the population's two largest plants, both ST_GAS in the model fleet, "
    "neither in any D-4 skip list - carry no drag floor at all. The error "
    "runs BOTH ways, which identifies it as an ALLOCATION defect rather than "
    "a level one (ercot-259's object; pjm-177 measured the same fact from the "
    "hour axis and recorded it without taking it). "
    "MEASURED RESULT, six years, composed-vs-composed against the incumbent: "
    "D-4 st_netload_drag FAIL rows 12 -> 5, with NO INCREASE IN ANY YEAR "
    "(2020 3->1, 2021 2->2, 2022 2->1, 2023 1->0, 2024 2->0, 2025 2->1); "
    "cc_mustrun_per_plant failures UNCHANGED in all six years, so nothing is "
    "traded away. The single cleanest statement of what the mechanism does: "
    "in 24 OF 24 per-plant-year rows the share of floored hours in which the "
    "plant's own meter reads zero FALLS, and the measured median over those "
    "hours RISES in 19 and never falls. "
    "AGGREGATE NEUTRALITY IS EXACT, verified at zero LP before the solve: the "
    "pre-solve mandate is identical to 0.0000 TWh in all six years, so the "
    "swap provably cannot double as a level knob. "
    "REPORTED AT FULL MAGNITUDE AND NOT TUNED AROUND: D-2 delivered forced "
    "energy RISES (st_netload_drag +12.0% to +111.5%; the ct_netload_drag "
    "limb, which the same flag also governs, +21.9% to +44.3%). That is a "
    "consequence of the reallocation, not a level change - the mandate is "
    "unchanged, and the extra forced energy lands on plants D-4 scores as "
    "metered ON (14 of 17 gaining plant-years pass D-4 on the arm side). "
    "The lane's own G5 gate, which required no OTHER mechanism's D-2 share to "
    "move more than 0.5%, FAILED AS WRITTEN because it scoped 'other "
    "mechanism' by D-2 mechanism id when the net-load drag FAMILY carries two "
    "(floors.py:570 ST_GAS and :646 CT_PEAKER both read this one flag). That "
    "is a charter-scoping error by the lane, disclosed rather than amended "
    "after the fact; outside the drag family the largest D-2 share move in "
    "any year is 0.0007. "
    "3138 New Castle remains the mechanism's named residual defect: it still "
    "FAILS D-4 in 2020-2022, and the cause is the weakness this mechanism was "
    "registered with - heat rate is an imperfect proxy for commitment order, "
    "so a plant that is cheap on paper and idle in fact is filled early."
)

ATTESTED_BY = (
    f"pjm-h13 orchestrator (2026-09-20). The incumbent keeper recipe "
    f"2026-09-19-pjm-h11-c1seam-span (pjm_h11_keeper_span + "
    f"pjm_h11_touchpoint_span) replayed at pinned HEAD {PINNED_SHA} via "
    "scripts/replay_keeper.py --set netload_drag_merit_allocation=true, ONE "
    "YEAR PER SHARD CONTAINER (rule 36 [R-YEAR-ISOLATION] (a)), ZERO LP "
    "MINUTES IN THE PARENT (rule 32 [R-SHARD] (a)), composed at zero LP by "
    "scripts/probes/pjm_h11_compose_span.py with legitimacy_diagnostics.json "
    "REGENERATED over each composite rather than copied from a leg. "
    "NO CONTROL SOLVES WERE SPENT: G-DRIFT (rule 29 [R-SCREEN] (b), form 4) "
    "over 65ab6205..HEAD found every changed hunk INERT for PJM backcast - "
    "constants.py adds NWPP-region capacity factors only, scenarios.py "
    "changes zero executable lines, and hubs.py's single executable hunk sits "
    "inside the caiso_citygate_blackout_bridge branch, a flag absent from "
    "both PJM bundles - so the incumbent keeper's committed bundle IS the "
    "control. Gates G1-G5 and the reported/gating asymmetry were fixed ex "
    "ante in docs/handoffs/PRECOMMIT-pjm-h13-2026-09-20.md and its two "
    "addenda, both committed before any arm result existed."
)


def main() -> None:
    base = json.loads((INCUMBENT / "calibration_attestation.json").read_text())
    for target in TARGETS:
        att = json.loads(json.dumps(base))  # deep copy
        gov = att["governance"]
        # Every flag re-affirmed for THIS delta, not inherited blindly:
        # the lever is a measured tranche structure + measured bid heat rates;
        # it was selected on D-4 conduct evidence, never on a residual; and it
        # pins no output to any actual.
        gov["levers_trace_to_measured_input"] = True
        gov["no_fit_to_price_residuals"] = True
        gov["no_pinning_to_actuals"] = True
        gov["attested_by"] = ATTESTED_BY
        gov["note"] = NOTE
        att["exceptions"] = []
        att["delta_vs_incumbent"] = {
            "keeper": (
                "2026-09-19-pjm-h11-c1seam-span "
                "(results/calibration/pjm_h11_keeper_span + pjm_h11_touchpoint_span)"
            ),
            "config_deltas": ["netload_drag_merit_allocation: False -> True"],
            "n_config_deltas": 1,
            "code_deltas": [],
            "free_parameters_added": 0,
            "dof_ledger": (
                "CARRIED VERBATIM from the incumbent keeper's ledger "
                "(2026-09-19-pjm-h11-c1seam-span). The merit fill adds ZERO free "
                "parameters (rule 21 [R-DOF]): its block sizes are the frozen "
                "binning artifact's existing tranche capacities and its order is "
                "the fleet's own bid heat rates, so nothing is derived, fitted or "
                "swept. n_entries and n_residual are unchanged."
            ),
            "aggregate_neutrality": (
                "EXACT and verified BEFORE the solve at zero LP "
                "(scripts/probes/pjm_h13_drag_allocation_phase0.py, "
                "run_year(..., fleet_only=True)): the pre-solve mandate is "
                "identical between control and arm to 0.0000 TWh in all six years "
                "- 2020 2.7870, 2021 3.0041, 2022 3.2110, 2023 2.8355, "
                "2024 3.1229, 2025 3.5270."
            ),
            "head_drift_disclosed": (
                "NO CONTROL SOLVES. Form 4 (the incumbent keeper's committed "
                "bundle as the control) was validated by a code-level G-DRIFT "
                "audit over 65ab6205..HEAD, every hunk classified INERT for PJM "
                "with its reason. pjm-h12 additionally MEASURED the one hunk this "
                "lane inherits as suspect (hubs.py::_basis_bridge_blackouts): its "
                "2022 control reproduced the committed keeper with 0 of 78,840 "
                "price cells moved."
            ),
        }
        (target / "calibration_attestation.json").write_text(
            json.dumps(att, indent=1) + "\n"
        )
        print(f"wrote {target.name}/calibration_attestation.json")


if __name__ == "__main__":
    main()
