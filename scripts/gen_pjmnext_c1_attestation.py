#!/usr/bin/env python3
"""Write the PJM-NEXT card-1 composite's calibration_attestation.json.

The DOF ledger (``free_parameters``) and governance booleans are carried VERBATIM
from the R-PJM-2 keeper (``rpjm2_span``): card 1 adds three measured-input
switches and zero free parameters. Only the provenance text and the
``delta_vs_incumbent`` block are rewritten. A composed bundle inherits no
attestation (pjm-h15 trap), so this runs after composition, before registration.

Usage: python scripts/gen_pjmnext_c1_attestation.py results/calibration/pjmnext_c1_span
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEEPER = REPO / "results" / "calibration" / "rpjm2_span"


def build() -> dict:
    """Return the attestation dict for the card-1 composite."""
    a = copy.deepcopy(json.loads((KEEPER / "calibration_attestation.json").read_text()))
    g = a["governance"]
    g["attested_by"] = (
        "PJM-NEXT orchestrator (2026-09-25). The R-PJM-2 keeper recipe 2026-09-25-pjm-r-pjm-2 "
        "(results/calibration/rpjm2_span) replayed at pinned 7f0953845350089732892f83248726d4b04fb84f via "
        "scripts/replay_keeper.py --set mid_vintage_exit_carry=true --set fleet_zone_vintage_coords=true "
        "--set benchmark_membership_vintage_union=true, ONE YEAR PER SHARD CONTAINER 2019-2025 (rule 36), "
        "ZERO LP IN THE PARENT (rule 32(a)), composed at zero LP by scripts/probes/_pjmnext_compose_span.py "
        "(recipe check: keeper year + exactly the three card-1 flags, offer_curve_overrides equal to the "
        "keeper's modulo the COAL-SUB bare-COAL fold, one solve-surface fingerprint, outage sha 312a11b8). "
        "CONTROL: committed keeper for 2023-2025 (form 4); a control SOLVE at the same pin for 2019-2022, "
        "earned by the LIVE COAL-SUB hunks in the G-DRIFT audit recorded BEFORE any solve in "
        "docs/PRECOMMIT-pjm-next-c1-year-correct-membership-2026-09-25.md §3 (+ G1 addendum)."
    )
    g["note"] = (
        "YEAR-CORRECT MEMBERSHIP + ZONING on the current keeper (rule 14 basis, never the residual): "
        "(1) mid_vintage_exit_carry restores plants that retired DURING their own vintage year; "
        "(2) fleet_zone_vintage_coords zones plants eGRID 2023 lacks from the active EIA-860 vintage's own "
        "coordinates instead of the PJM_AEP_Ohio fallback; (3) benchmark_membership_vintage_union puts the "
        "same plants into the EIA-923 actuals. Measured/published inputs only; zero free parameters added."
    )
    a["delta_vs_incumbent"] = {
        "keeper": "2026-09-25-pjm-r-pjm-2 (results/calibration/rpjm2_span)",
        "config_deltas": [
            "mid_vintage_exit_carry: False -> True",
            "fleet_zone_vintage_coords: False -> True",
            "benchmark_membership_vintage_union: False -> True",
        ],
        "n_config_deltas": 3,
        "code_deltas": [
            "PJM-NEXT 18ab44d2: fleet_zone_vintage_coords (new, gated) + benchmark-union rebuild recovery",
            "COAL-SUB 8eaf34b5/05437cc0: bare COAL class eliminated (LIVE 2019-2022; isolated by the control solve)",
        ],
        "years_added": [],
        "free_parameters_added": 0,
        "dof_ledger": {
            **a["delta_vs_incumbent"].get("dof_ledger", {}),
            "carried": "VERBATIM from the R-PJM-2 keeper; zero entries added.",
        },
        "authorized_price_tuning": {
            "used": False,
            "note": "NO band multiplier was touched: offer_curve_overrides equal to the keeper's on every leg "
            "modulo the COAL-SUB fold of the legacy bare COAL key (rule 1(c)).",
        },
    }
    return a


def main() -> int:
    """CLI entry point."""
    out = Path(sys.argv[1])
    (out / "calibration_attestation.json").write_text(
        json.dumps(build(), indent=2) + "\n"
    )
    print(f"wrote {out / 'calibration_attestation.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
