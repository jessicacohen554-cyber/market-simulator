#!/usr/bin/env python3
"""Write the PJM-NEXT-7 (virtual position settled financially) composite's calibration_attestation.json.

The DOF ledger (``free_parameters``) and governance booleans are carried VERBATIM
from the PJM-NEXT-6 keeper (``pjmnext6_sp_span``): this lane arms one default-off
sub-gate, ``pjm_da_virtual_settle_financial`` (owner ruling 2026-09-28, "settle
financially", design A'), with zero parameters. Only the provenance text and the
``delta_vs_incumbent`` block are rewritten. A composed
bundle inherits no attestation (pjm-h15 trap), so this runs after composition,
before registration.

Usage: python scripts/gen_pjmnext7_vs_attestation.py results/calibration/pjmnext7_vs_span
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEEPER = REPO / "results" / "calibration" / "pjmnext6_sp_span"
PINNED = "f2850356a29c3b22c1c1ccd2a0365190e2adb0ca"
PRECOMMIT = "docs/PRECOMMIT-pjm-next-7-virtual-settle-2026-09-28.md"


def build() -> dict:
    """Return the attestation dict for the PJM-NEXT-7 composite."""
    a = copy.deepcopy(json.loads((KEEPER / "calibration_attestation.json").read_text()))
    g = a["governance"]
    g["attested_by"] = (
        "PJM-NEXT-7 orchestrator (2026-09-28). The PJM-NEXT-6 keeper recipe 2026-09-28-pjm-next-6-f2 "
        f"(results/calibration/pjmnext6_sp_span) replayed at pinned {PINNED} via scripts/replay_keeper.py "
        "--set pjm_da_virtual_settle_financial=true, ONE YEAR PER SHARD CONTAINER 2019-2025 (rule 36), "
        "ZERO LP IN THE PARENT (rule 32(a)), composed at zero LP by "
        "scripts/probes/_pjmnext7_vs_compose_span.py (recipe check: keeper year plus exactly the arm flag, "
        "offers equal to the keeper's, pinned SHA, one solve-surface fingerprint). CONTROL: the committed "
        "keeper bundle for every year (rule 29(b) form 4), validated by a hunk-by-hunk G-DRIFT audit "
        f"recorded before any solve ({PRECOMMIT} §3)."
    )
    g["note"] = (
        "ONE STRUCTURAL CORRECTION (rule 1, owner ruling 2026-09-28 'settle financially', design A' "
        "docs/DESIGN-pjm-next-7-virtual-settlement-2026-09-28.md): a cleared PJM INC/DEC is liquidated in "
        "RT, so the scored RT-gated P1 clears without the virtual position (bounds zeroed) while P0, the "
        "DA commitment stage, keeps it. Zero free parameters added; no multiplier value changed."
    )
    a["delta_vs_incumbent"] = {
        "keeper": "2026-09-28-pjm-next-6-f2 (results/calibration/pjmnext6_sp_span)",
        "config_deltas": ["pjm_da_virtual_settle_financial: False -> True"],
        "n_config_deltas": 1,
        "data_deltas": [],
        "code_deltas": [
            "ScenarioConfig.pjm_da_virtual_settle_financial + data.virtual_bids.settle_virtuals_financially "
            "applied in pipeline.solve.run_energy_solve after p1_fleet_prep",
        ],
        "years_added": [],
        "free_parameters_added": 0,
        "dof_ledger": {
            **a.get("delta_vs_incumbent", {}).get("dof_ledger", {}),
            "carried": "VERBATIM from the PJM-NEXT-6 keeper; zero entries added.",
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
