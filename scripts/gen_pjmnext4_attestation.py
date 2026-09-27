#!/usr/bin/env python3
"""Write the PJM-NEXT-4 card-1 composite's calibration_attestation.json.

The DOF ledger (``free_parameters``) and governance booleans are carried VERBATIM
from the PJM-NEXT-3 keeper (``pjmnext3_c2_span``): card 1 adds the publisher's own
2019 offers as the 2019 mid-curve table, a measured-input data update with zero
parameters and no config change. Only the provenance text and the
``delta_vs_incumbent`` block are rewritten. A composed bundle inherits no
attestation (pjm-h15 trap), so this runs after composition, before registration.

Usage: python scripts/gen_pjmnext4_attestation.py results/calibration/pjmnext4_c1_span
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEEPER = REPO / "results" / "calibration" / "pjmnext3_c2_span"
PINNED = "7394a2795e0e191dcd341f03863aa1bb82ff7377"
PRECOMMIT = "docs/PRECOMMIT-pjm-next-4-card1-midcurve-2019-2026-09-26.md"


def build() -> dict:
    """Return the attestation dict for the PJM-NEXT-4 card-1 composite."""
    a = copy.deepcopy(json.loads((KEEPER / "calibration_attestation.json").read_text()))
    g = a["governance"]
    g["attested_by"] = (
        "PJM-NEXT-4 orchestrator (2026-09-26). The PJM-NEXT-3 keeper recipe 2026-09-26-pjm-next-3-unitfuel "
        f"(results/calibration/pjmnext3_c2_span) replayed UNCHANGED at pinned {PINNED} via "
        "scripts/replay_keeper.py (no --set), ONE YEAR PER SHARD CONTAINER 2019-2025 (rule 36), ZERO LP IN "
        "THE PARENT (rule 32(a)), composed at zero LP by scripts/probes/_pjmnext4_compose_span.py (recipe "
        "check: keeper year exactly, offers equal to the keeper's, pinned SHA, one solve-surface "
        "fingerprint). CONTROL: the committed keeper bundle for every year (rule 29(b) form 4), validated by "
        f"a hunk-by-hunk G-DRIFT audit recorded before any solve ({PRECOMMIT} §4)."
    )
    g["note"] = (
        "ONE MEASURED-INPUT DATA UPDATE (rule 14 / rule 23 basis, never the residual), pre-registered before "
        "any solve AGAINST INTEREST: the PJM mid-curve offer surface gains a 2019 table derived from PJM "
        "DataMiner2 energy_market_offers 2019 (12 month-files), replacing the pooled 2020-2025 blend 2019 "
        "previously read. Added by derive_pjm_offer_midcurve.py --merge-into-existing: every 2020-2025 "
        "table and the pooled forward ladder byte-identical (surface sha 936db1ba). Zero free parameters "
        "added, zero config fields changed."
    )
    a["delta_vs_incumbent"] = {
        "keeper": "2026-09-26-pjm-next-3-unitfuel (results/calibration/pjmnext3_c2_span)",
        "config_deltas": [],
        "n_config_deltas": 0,
        "data_deltas": [
            "data/raw/_validation-source/pjm_offer_midcurve_condbinned.json: + 2019 per-year ladders "
            "(sha f5426f75 -> 936db1ba); 2020-2025 + pooled unchanged",
        ],
        "code_deltas": [
            "scripts/data/derive_pjm_offer_midcurve.py --merge-into-existing (offline derive only)",
        ],
        "years_added": [],
        "free_parameters_added": 0,
        "dof_ledger": {
            **a.get("delta_vs_incumbent", {}).get("dof_ledger", {}),
            "carried": "VERBATIM from the PJM-NEXT-3 keeper; zero entries added.",
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
