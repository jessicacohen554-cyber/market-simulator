#!/usr/bin/env python3
"""Write hydro-2's governance attestation into the PJM ``hydro_ror_split`` composites.

The C6 governance gate reads ``<bundle>/calibration_attestation.json``. A
COMPOSED bundle does not inherit it (``hydro2_pjm_compose_span.py`` copies only
year-scoped files), so the parent writes it once, here, from the incumbent
keeper's own ledger (pjm-h15 correction #2).

Rule 21 ``[R-DOF]``: the DOF ledger is CARRIED FORWARD VERBATIM from
``pjm_h16_coalgrain_span`` because this arm adds **zero** free parameters. The
run-of-river partition is an external per-plant label (ORNL EHA mode, HILARRI
completion — ``scripts/data/curate_hydro_plant_modes.py``), and the flat
treatment sets each RoR plant-month's output to its own EIA-923 monthly budget
over the month's hours: no threshold, share or multiplier is chosen.

Usage: python3 scripts/gen_hydro2_pjm_attestation.py [bundle ...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "results/calibration/pjm_h16_coalgrain_span/calibration_attestation.json"
DEFAULT_OUT = [
    REPO / "results/calibration/hydro2_pjm_ror_span",
    REPO / "results/calibration/hydro2_pjm_ror_touchpoint",
]

ATTESTED_BY = (
    "hydro-2 orchestrator (2026-09-22). The incumbent keeper recipe "
    "2026-09-22-pjm-h16-coalgrain-span (pjm_h16_coalgrain_span + "
    "pjm_h16_coalgrain_touchpoint) replayed at pinned HEAD "
    "152c546a31c2b32191aae643230aa1d32ba5856c via scripts/replay_keeper.py "
    "--set hydro_ror_split=true, ONE YEAR PER SHARD CONTAINER (rule 36 "
    "[R-YEAR-ISOLATION] (a)), ZERO LP MINUTES IN THE PARENT (rule 32 [R-SHARD] "
    "(a)), composed at zero LP by scripts/probes/hydro2_pjm_compose_span.py, "
    "benchmark rebuilt with run_calibration_full.py --rebuild-benchmark, and "
    "legitimacy_diagnostics.json REGENERATED over each composite. CONTROL = the "
    "committed keeper bundles (rule 29 [R-SCREEN] (b) form 4); G-DRIFT "
    "c25d7e50 -> 152c546a audited ALL INERT for a PJM backcast and recorded in "
    "docs/PRECOMMIT-hydro-2-pjm-2026-09-22.md BEFORE any solve. Gates G1-G4 were "
    "fixed ex ante in that PRECOMMIT and not amended after a number landed. "
    "pjm_da_virtual_bids stays TRUE: the gitignored DataMiner2 corpus was "
    "re-fetched per shard, so the A/B is not confounded (disclosed: no "
    "SHA256SUMS exists for byte-identity with the keeper's fetch)."
)

NOTE = (
    "ONE CONFIG DELTA on the keeper's own recipe: hydro_ror_split False -> True. "
    "THE DEFECT: PJM's modelled conventional hydro sat at 0 MW for 1,010-1,867 "
    "hours a year in the keeper, on a fleet 55 % of whose energy ORNL EHA labels "
    "run-of-river or canal-conduit (57 of 82 plants after the HILARRI "
    "completion). A run-of-river plant has no reservoir; its output IS its "
    "inflow. That is a rule-17 driver argument from an external label alone, "
    "with no residual and no reference series in it. The arm flattens each RoR "
    "plant-month to its own monthly budget and leaves reservoir plants "
    "dispatchable. ZERO FREE PARAMETERS (rules 21/24). G2 EXACT: annual hydro "
    "energy unchanged to four decimals in every year, so the mechanism re-times "
    "water without moving a monthly total. NOT ARMED, deliberately: "
    "hydro_min_flow_floor and hydro_dispatch_envelope, because both read EIA-930 "
    "NG: WAT, which folds 5,046 MW of PJM pumped storage "
    "(EIA930_PS_FOLDED_INTO_WAT) - a live code gap recorded, not worked around "
    "(rule 14). Rule 1 [R-STRUCT]: scored criteria are reported at full "
    "magnitude; a wrong-way move keeps the mechanism and opens a root-cause "
    "question."
)


def build(src: dict) -> dict:
    """Attestation dict for the arm composites, derived from the keeper's."""
    return {
        "schema": src["schema"],
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
            "attested_by": ATTESTED_BY,
            "note": NOTE,
        },
        "exceptions": src.get("exceptions", []),
        "free_parameters": src["free_parameters"],
        "delta_vs_incumbent": {
            "keeper": (
                "2026-09-22-pjm-h16-coalgrain-span "
                "(results/calibration/pjm_h16_coalgrain_span + "
                "pjm_h16_coalgrain_touchpoint)"
            ),
            "config_deltas": ["hydro_ror_split: False -> True"],
            "n_config_deltas": 1,
            "code_deltas": [
                "none in this lane: hydro_ror_split and the RoR hybrid-label "
                "repair landed in da38d108 (hydro-1) and are default-off / "
                "read only under the flag",
            ],
            "free_parameters_added": 0,
            "dof_ledger": {
                "n_entries": src["free_parameters"]["n_entries"],
                "n_residual": src["free_parameters"]["n_residual"],
                "carried": "VERBATIM from the incumbent keeper; zero entries added.",
            },
            "authorized_price_tuning": src["delta_vs_incumbent"].get(
                "authorized_price_tuning"
            ),
        },
    }


def main() -> None:
    """Write the attestation into each named (or default) composite bundle."""
    att = build(json.loads(SRC.read_text()))
    outs = [Path(a) for a in sys.argv[1:]] or DEFAULT_OUT
    for d in outs:
        if not d.is_dir():
            print(f"skip {d} (absent)")
            continue
        (d / "calibration_attestation.json").write_text(
            json.dumps(att, indent=1) + "\n"
        )
        print(f"wrote {d}/calibration_attestation.json")


if __name__ == "__main__":
    main()
