#!/usr/bin/env python3
"""Write the PJM-NEXT-5 card-1 (shape form) composite's calibration_attestation.json.

The DOF ledger (``free_parameters``) and governance booleans are carried VERBATIM
from the PJM-NEXT-4 keeper (``pjmnext4_c1_span``): card 3(a) arms one default-off
flag, ``unit_outage_full_rederive``, which reads the F2 full HEAD re-derive of the
PJM standard + short-coal CAMPD outage extracts — a measured-input correction
with zero parameters. Only the provenance text and the
``delta_vs_incumbent`` block are rewritten. A composed bundle inherits no
attestation (pjm-h15 trap), so this runs after composition, before registration.

Usage: python scripts/gen_pjmnext5_sh_attestation.py results/calibration/pjmnext5_sh_span
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEEPER = REPO / "results" / "calibration" / "pjmnext4_c1_span"
PINNED = "2111658c67cc2723273c42c8adb839291b6f5470"
PRECOMMIT = "docs/PRECOMMIT-pjm-next-5-card1-shape-2026-09-27.md"


def build() -> dict:
    """Return the attestation dict for the PJM-NEXT-5 card-1 (shape form) composite."""
    a = copy.deepcopy(json.loads((KEEPER / "calibration_attestation.json").read_text()))
    g = a["governance"]
    g["attested_by"] = (
        "PJM-NEXT-5 orchestrator (2026-09-27). The PJM-NEXT-4 keeper recipe 2026-09-26-pjm-next-4-midcurve2019 "
        f"(results/calibration/pjmnext4_c1_span) replayed at pinned {PINNED} via scripts/replay_keeper.py "
        "--set pjm_offer_midcurve_shape_segments=['CC_LIKE'], ONE YEAR PER SHARD CONTAINER 2019-2025 (rule 36), ZERO LP IN "
        "THE PARENT (rule 32(a)), composed at zero LP by scripts/probes/_pjmnext5_sh_compose_span.py (recipe "
        "check: keeper year plus exactly the arm flag, offers equal to the keeper's, pinned SHA, one "
        "solve-surface fingerprint). CONTROL: the committed keeper bundle for every year (rule 29(b) form 4), "
        f"validated by a hunk-by-hunk G-DRIFT audit recorded before any solve ({PRECOMMIT} §5)."
    )
    g["note"] = (
        "ONE STRUCTURAL REPLACEMENT (rule 14, owner ruling 2026-09-27 'Build + solve'), pre-registered before "
        "any solve: pjm_offer_midcurve_shape_segments=['CC_LIKE'] prices every CC_LIKE econ row at the "
        "plant's own committed-rung cost x PJM's measured offer-ladder ratio m(s_g)/m(s_committed) (gas "
        "index cancels), replacing the residual-identified CC econ_low/econ_high ladder on those rows. "
        "Zero free parameters added; no multiplier value changed. retiree_cems_cap deleted at the same pin "
        "(rule 26; measured inert on this keeper in every year)."
    )
    a["delta_vs_incumbent"] = {
        "keeper": "2026-09-26-pjm-next-4-midcurve2019 (results/calibration/pjmnext4_c1_span)",
        "config_deltas": [
            "pjm_offer_midcurve_shape_segments: None -> ['CC_LIKE']",
            "retiree_cems_cap: deleted (rule 26; recorded True measured inert)",
        ],
        "n_config_deltas": 2,
        "data_deltas": [],
        "code_deltas": [
            "ScenarioConfig.pjm_offer_midcurve_shape_segments + offer_surfaces shape branch",
            "retiree_cems_cap removed (field, arrays branch, outages envelope)",
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
