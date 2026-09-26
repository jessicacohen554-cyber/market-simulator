#!/usr/bin/env python3
"""Write the PJM-NEXT-2 joint composite's calibration_attestation.json.

The DOF ledger (``free_parameters``) and governance booleans are carried VERBATIM
from the PJM-NEXT keeper (``pjmnext_c1_span``): PJM-NEXT-2 adds three gated,
zero-parameter repairs of measured inputs. Only the provenance text and the
``delta_vs_incumbent`` block are rewritten. A composed bundle inherits no
attestation (pjm-h15 trap), so this runs after composition, before registration.

Usage: python scripts/gen_pjmnext2_attestation.py results/calibration/pjmnext2_joint_span
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEEPER = REPO / "results" / "calibration" / "pjmnext_c1_span"


def build() -> dict:
    """Return the attestation dict for the PJM-NEXT-2 joint composite."""
    a = copy.deepcopy(json.loads((KEEPER / "calibration_attestation.json").read_text()))
    g = a["governance"]
    g["attested_by"] = (
        "PJM-NEXT-2 orchestrator (2026-09-25). The PJM-NEXT keeper recipe 2026-09-25-pjm-next-c1 "
        "(results/calibration/pjmnext_c1_span) replayed at pinned d25a3ebb57c51db7972df77df07615e84f3ce401 "
        "via scripts/replay_keeper.py --set unit_outage_membership_repair=true "
        "--set pjm_zonal_gas_basis_skip_923_priced=true --set nuclear_dormancy_defers_to_vintage_exit=true, "
        "ONE YEAR PER SHARD CONTAINER 2019-2025 (rule 36), ZERO LP IN THE PARENT (rule 32(a)), composed at "
        "zero LP by scripts/probes/_pjmnext2_compose_span.py (recipe check: keeper year + exactly the three "
        "flags, offers equal to the keeper's, one solve-surface fingerprint, outage companion sha c6883c51). "
        "CONTROL: the committed keeper bundle for every year (rule 29(b) form 4), validated by a G-DRIFT "
        "audit recorded before any solve: fleet-only rebuilds of the keeper recipe at the keeper SHA "
        "7f095384 and at HEAD are byte-identical (unit ids, availability, min_gen, offers, fuel, pmax, "
        "demand; 2019 and 2024) - docs/PRECOMMIT-pjm-next-2-card1-outage-membership-2026-09-25.md §5."
    )
    g["note"] = (
        "THREE STRUCTURAL REPAIRS OF MEASURED INPUTS (rule 14 / rule 19 basis, never the residual), each "
        "pre-registered before any solve: (1) unit_outage_membership_repair - the committed CAMPD outage "
        "extract never scanned 21 facilities (pre-exit whole-plant coal retirees; partial-plant coal exits "
        "keyed on their surviving CT class); the -memberrepair- companion adds their measured windows and "
        "leaves every committed row byte-identical; (2) pjm_zonal_gas_basis_skip_923_priced - the zonal "
        "basis is no longer stacked on cells the EIA-923 delivered print already priced (PJM's own twin of "
        "miso-213); (3) nuclear_dormancy_defers_to_vintage_exit - the Crane restart dormancy no longer "
        "erases TMI-1's genuine Jan-Sep 2019 operation. Zero free parameters added."
    )
    a["delta_vs_incumbent"] = {
        "keeper": "2026-09-25-pjm-next-c1 (results/calibration/pjmnext_c1_span)",
        "config_deltas": [
            "unit_outage_membership_repair: False -> True",
            "pjm_zonal_gas_basis_skip_923_priced: False -> True",
            "nuclear_dormancy_defers_to_vintage_exit: False -> True",
        ],
        "n_config_deltas": 3,
        "code_deltas": [
            "PJM-NEXT-2 e8cb6516: unit_outage_membership_repair + companion extract; "
            "pjm_zonal_gas_basis_skip_923_priced; deriver --membership-vintage-union",
            "PJM-NEXT-2 45ede7a7: nuclear_dormancy_defers_to_vintage_exit",
        ],
        "years_added": [],
        "free_parameters_added": 0,
        "dof_ledger": {
            **a["delta_vs_incumbent"].get("dof_ledger", {}),
            "carried": "VERBATIM from the PJM-NEXT keeper; zero entries added.",
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
