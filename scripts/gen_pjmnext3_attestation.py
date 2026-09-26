#!/usr/bin/env python3
"""Write the PJM-NEXT-3 card-2 composite's calibration_attestation.json.

The DOF ledger (``free_parameters``) and governance booleans are carried VERBATIM
from the PJM-NEXT-2 keeper (``pjmnext2_joint_span``): card 2 adds one gated,
zero-parameter routing repair of a measured input. Only the provenance text and
the ``delta_vs_incumbent`` block are rewritten. A composed bundle inherits no
attestation (pjm-h15 trap), so this runs after composition, before registration.

Usage: python scripts/gen_pjmnext3_attestation.py results/calibration/pjmnext3_c2_span
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEEPER = REPO / "results" / "calibration" / "pjmnext2_joint_span"


def build() -> dict:
    """Return the attestation dict for the PJM-NEXT-3 card-2 composite."""
    a = copy.deepcopy(json.loads((KEEPER / "calibration_attestation.json").read_text()))
    g = a["governance"]
    g["attested_by"] = (
        "PJM-NEXT-3 orchestrator (2026-09-26). The PJM-NEXT-2 keeper recipe 2026-09-25-pjm-next-2-joint "
        "(results/calibration/pjmnext2_joint_span) replayed at pinned 54849585a6df41c06befac8fa695c5ad15e1a4d4 "
        "via scripts/replay_keeper.py --set unit_outage_unit_fuel_routing=true, ONE YEAR PER SHARD CONTAINER "
        "2019-2025 (rule 36), ZERO LP IN THE PARENT (rule 32(a)), composed at zero LP by "
        "scripts/probes/_pjmnext3_compose_span.py (recipe check: keeper year + exactly the one flag, offers "
        "equal to the keeper's, one solve-surface fingerprint). CONTROL: the committed keeper bundle for every "
        "year (rule 29(b) form 4), validated by a hunk-by-hunk G-DRIFT audit recorded before any solve "
        "(docs/PRECOMMIT-pjm-next-3-card2-unit-fuel-routing-2026-09-26.md §4)."
    )
    g["note"] = (
        "ONE STRUCTURAL REPAIR OF A MEASURED INPUT (rule 14 / rule 19 basis, never the residual), "
        "pre-registered before any solve: unit_outage_unit_fuel_routing - at a plant whose steam generators "
        "burn different fuels in the solved year's EIA-860 vintage (Montour 3149 2023/2024, Brunner Island "
        "3140 2019), each CAMPD outage window now derates its OWN unit's fuel slice instead of the one slice "
        "the facility tag names. 66 of 11,534 extract rows re-tagged; no row added, dropped, moved or "
        "resized. Zero free parameters added."
    )
    a["delta_vs_incumbent"] = {
        "keeper": "2026-09-25-pjm-next-2-joint (results/calibration/pjmnext2_joint_span)",
        "config_deltas": ["unit_outage_unit_fuel_routing: False -> True"],
        "n_config_deltas": 1,
        "code_deltas": [
            "PJM-NEXT-3 54849585: unit_outage_unit_fuel_routing + "
            "campd-unit-outages-memberrepair-unitfuel-PJM.csv (sha ab6e163c) + "
            "scripts/data/build_outage_unit_fuel_routing.py",
        ],
        "years_added": [],
        "free_parameters_added": 0,
        "dof_ledger": {
            **a.get("delta_vs_incumbent", {}).get("dof_ledger", {}),
            "carried": "VERBATIM from the PJM-NEXT-2 keeper; zero entries added.",
        },
        "authorized_price_tuning": {
            "used": False,
            "note": "NO band multiplier was touched: offer_curve_overrides equal to the keeper's on every leg.",
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
