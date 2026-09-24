#!/usr/bin/env python3
"""Write pjm-h20's governance attestation into the PJM Card C composites.

The C6 governance gate reads ``<bundle>/calibration_attestation.json``. A
COMPOSED bundle does not inherit it, so the parent writes it once, here, from
the incumbent keeper's own ledger (pjm-h15 correction #2).

Rule 21 ``[R-DOF]``: the DOF ledger is CARRIED FORWARD VERBATIM from
``pjm_h19_dbs_span`` because this arm adds **zero** free parameters: both
switches are scopes on the frozen, committed PJM energy-offer corpus
(``derive_pjm_offer_midcurve.py``). ``offer_curve_by_group`` is untouched, so
the rules-1/13 authorized price-tuning channel is not used.

Usage: python3 scripts/gen_pjm_h20_attestation.py [bundle ...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "results/calibration/pjm_h19_dbs_span/calibration_attestation.json"
DEFAULT_OUT = [
    REPO / "results/calibration/pjm_h20_cardc_span",
    REPO / "results/calibration/pjm_h20_cardc_touchpoint",
]

ATTESTED_BY = (
    "pjm-h20 orchestrator (2026-09-24). The incumbent keeper recipe "
    "2026-09-23-pjm-h19-dbs-span (pjm_h19_dbs_span + pjm_h19_dbs_touchpoint) "
    "replayed at pinned HEAD 9f8e95dfebb9c7c6d722f5c4a1ee5845ffe75c3e via "
    "scripts/replay_keeper.py --set pjm_offer_midcurve_level_segments=[CC_LIKE] "
    "--set pjm_ct_measured_max_reprice=true, ONE YEAR PER SHARD CONTAINER (rule "
    "36 (a)), ZERO LP MINUTES IN THE PARENT (rule 32 (a)), composed at zero LP by "
    "scripts/probes/pjm_h20_compose_span.py, benchmark rebuilt with "
    "run_calibration_full.py --rebuild-benchmark, legitimacy_diagnostics.json "
    "REGENERATED over each composite. CONTROL = the committed keeper bundles "
    "(rule 29 (b) form 4); G-DRIFT 2d57aa20 -> 9f8e95df audited (all hunks "
    "SOCO-keyed, INERT for PJM) and recorded in docs/PRECOMMIT-pjm-h20-card-c-"
    "cc-level-ct-max-2026-09-24.md BEFORE any solve, with gates and predictions "
    "fixed ex ante; nothing was amended after a solve number landed."
)

NOTE = (
    "TWO CONFIG DELTAS on the keeper's own recipe, chartered as a pair (Card C): "
    "(1) pjm_offer_midcurve_level_segments None -> [CC_LIKE]: the CC_REGULAR "
    "econ rungs bid PJM's own published offer at the rung's capacity share "
    "(LEVEL form) instead of floor form, which could only raise them - phase 0 "
    "measured the fitted rungs $4.9-6.9/MWh above measured in CC-marginal "
    "hours in every year; (2) pjm_ct_measured_max_reprice False -> True: CT "
    "econ/peak rungs bid max(full P1 bid, PJM's own CT offer), applied after "
    "the startup amortization (rule 19). Rule 14 [R-ACCURATE] measured "
    "identification, ZERO FREE PARAMETERS (rules 21/24). pjm_ct_measured_max_"
    "reprice is a registered backcast-only overlay (rule 13), never the "
    "forecast method. Rule 1 [R-STRUCT]: scored criteria are reported at full "
    "magnitude."
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
                "2026-09-23-pjm-h19-dbs-span "
                "(results/calibration/pjm_h19_dbs_span + pjm_h19_dbs_touchpoint)"
            ),
            "config_deltas": [
                "pjm_offer_midcurve_level_segments: None -> ['CC_LIKE']",
                "pjm_ct_measured_max_reprice: False -> True",
            ],
            "n_config_deltas": 2,
            "code_deltas": [],
            "free_parameters_added": 0,
            "dof_ledger": {
                "n_entries": src["free_parameters"]["n_entries"],
                "n_residual": src["free_parameters"]["n_residual"],
                "carried": "VERBATIM from the incumbent keeper; zero entries added.",
            },
            "authorized_price_tuning": {
                "used": False,
                "note": "NO band multiplier was touched; offer_curve_by_group is "
                "carried byte-identical from the incumbent keeper.",
            },
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
        (d / "calibration_attestation.json").write_text(json.dumps(att, indent=1) + "\n")
        print(f"wrote {d}/calibration_attestation.json")


if __name__ == "__main__":
    main()
