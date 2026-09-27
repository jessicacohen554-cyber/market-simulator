#!/usr/bin/env python3
"""Write the PJM-NEXT-5 card-3(a) composite's calibration_attestation.json.

The DOF ledger (``free_parameters``) and governance booleans are carried VERBATIM
from the PJM-NEXT-4 keeper (``pjmnext4_c1_span``): card 3(a) arms one default-off
flag, ``unit_outage_full_rederive``, which reads the F2 full HEAD re-derive of the
PJM standard + short-coal CAMPD outage extracts — a measured-input correction
with zero parameters. Only the provenance text and the
``delta_vs_incumbent`` block are rewritten. A composed bundle inherits no
attestation (pjm-h15 trap), so this runs after composition, before registration.

Usage: python scripts/gen_pjmnext5_attestation.py results/calibration/pjmnext5_f2_span
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEEPER = REPO / "results" / "calibration" / "pjmnext4_c1_span"
PINNED = "e878194dcd9088585708bde7057641df56162087"
PRECOMMIT = "docs/PRECOMMIT-pjm-next-5-card3a-f2-rederive-2026-09-27.md"


def build() -> dict:
    """Return the attestation dict for the PJM-NEXT-5 card-3(a) composite."""
    a = copy.deepcopy(json.loads((KEEPER / "calibration_attestation.json").read_text()))
    g = a["governance"]
    g["attested_by"] = (
        "PJM-NEXT-5 orchestrator (2026-09-27). The PJM-NEXT-4 keeper recipe 2026-09-26-pjm-next-4-midcurve2019 "
        f"(results/calibration/pjmnext4_c1_span) replayed at pinned {PINNED} via scripts/replay_keeper.py "
        "--set unit_outage_full_rederive=true, ONE YEAR PER SHARD CONTAINER 2019-2025 (rule 36), ZERO LP IN "
        "THE PARENT (rule 32(a)), composed at zero LP by scripts/probes/_pjmnext5_compose_span.py (recipe "
        "check: keeper year plus exactly the arm flag, offers equal to the keeper's, pinned SHA, one "
        "solve-surface fingerprint). CONTROL: the committed keeper bundle for every year (rule 29(b) form 4), "
        f"validated by a hunk-by-hunk G-DRIFT audit recorded before any solve ({PRECOMMIT} §5)."
    )
    g["note"] = (
        "ONE MEASURED-INPUT CORRECTION (rule 14 / rule 23 basis, never the residual), owner ruling YES "
        "2026-09-27, pre-registered before any solve: unit_outage_full_rederive selects the F2 full HEAD "
        "re-derive of the PJM standard + short-coal CAMPD outage extracts (membership union, COAL-SUB fix, "
        "unit-scoped ST_GAS_PEAKER_PLANTS skip, then per-unit fuel routing): "
        "campd-unit-outages-rederive-unitfuel-PJM.csv sha a77386d8, campd-unit-outages-short-rederive-PJM.csv "
        "sha 484fe860. Committed extracts byte-unchanged. Zero free parameters added."
    )
    a["delta_vs_incumbent"] = {
        "keeper": "2026-09-26-pjm-next-4-midcurve2019 (results/calibration/pjmnext4_c1_span)",
        "config_deltas": ["unit_outage_full_rederive: False -> True"],
        "n_config_deltas": 1,
        "data_deltas": [
            "data/raw/campd-unit-outages-rederive-unitfuel-PJM.csv (new companion, sha a77386d8)",
            "data/raw/campd-unit-outages-short-rederive-PJM.csv (new companion, sha 484fe860)",
        ],
        "code_deltas": [
            "ScenarioConfig.unit_outage_full_rederive (default off) + outages.py resolvers",
            "scripts/data/derive_campd_unit_outages.py: ST_GAS_PEAKER_PLANTS skip scoped to the ST_GAS slice",
        ],
        "years_added": [],
        "free_parameters_added": 0,
        "dof_ledger": {
            **a.get("delta_vs_incumbent", {}).get("dof_ledger", {}),
            "carried": "VERBATIM from the PJM-NEXT-4 keeper; zero entries added.",
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
