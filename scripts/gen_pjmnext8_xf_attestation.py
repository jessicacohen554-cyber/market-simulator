#!/usr/bin/env python3
"""Write the PJM-NEXT-8 (exit-cohort outage repair) composite's calibration_attestation.json.

The DOF ledger (``free_parameters``) and governance booleans are carried VERBATIM
from the PJM-NEXT-7 keeper (``pjmnext7_vs_span``): this lane arms one default-off
measured-input repair, ``unit_outage_exit_cohort_repair`` (owner card 2026-09-28,
"Build + solve"), with zero parameters. Only the provenance text and the
``delta_vs_incumbent`` block are rewritten. A composed bundle inherits no
attestation (pjm-h15 trap), so this runs after composition, before registration.

Usage: python scripts/gen_pjmnext8_xf_attestation.py results/calibration/pjmnext8_xf_span
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEEPER = REPO / "results" / "calibration" / "pjmnext7_vs_span"
PINNED = "e9fc1a5eaf7f0255d1b43bad53851e1aa9500131"
PRECOMMIT = "docs/records/pjm/PRECOMMIT-pjm-next-8-exitfix-2026-09-28.md"


def build() -> dict:
    """Return the attestation dict for the PJM-NEXT-8 composite."""
    a = copy.deepcopy(json.loads((KEEPER / "calibration_attestation.json").read_text()))
    g = a["governance"]
    g["attested_by"] = (
        "PJM-NEXT-8 orchestrator (2026-09-28). The PJM-NEXT-7 keeper recipe 2026-09-28-pjm-next-7-virtual "
        f"(results/calibration/pjmnext7_vs_span) replayed at pinned {PINNED} via scripts/replay_keeper.py "
        "--set unit_outage_exit_cohort_repair=true, ONE YEAR PER SHARD CONTAINER 2019-2025 (rule 36), "
        "ZERO LP IN THE PARENT (rule 32(a)), composed at zero LP by "
        "scripts/probes/_pjmnext8_xf_compose_span.py (recipe check: keeper year plus exactly the arm flag, "
        "offers equal to the keeper's, pinned SHA, one solve-surface fingerprint). CONTROL: the committed "
        "keeper bundle for every year (rule 29(b) form 4), validated by a hunk-by-hunk G-DRIFT audit "
        f"recorded before any solve ({PRECOMMIT} §4)."
    )
    g["note"] = (
        "ONE MEASURED-INPUT REPAIR (rule 14, docs/records/pjm/FINDING-pjm-next-7-coal-phase0-2026-09-28.md §3): the "
        "CAMPD unit-outage layer sizes each unit from the solve year's own EIA-860 vintage, keys dated "
        "exit bins over their own capacity, and windows exit-cohort units dark all year. The companion's "
        "control reproduces the keeper's file byte-for-byte. Zero free parameters added; no multiplier "
        "value changed."
    )
    a["delta_vs_incumbent"] = {
        "keeper": "2026-09-28-pjm-next-7-virtual (results/calibration/pjmnext7_vs_span)",
        "config_deltas": ["unit_outage_exit_cohort_repair: False -> True"],
        "n_config_deltas": 1,
        "data_deltas": [
            "data/raw/campd-unit-outages-rederive-peakerkeep-exitfix-unitfuel-PJM.csv (sha256 02d565cd)",
        ],
        "code_deltas": [
            "ScenarioConfig.unit_outage_exit_cohort_repair; outages.unit_outage_csv_for_iso / "
            "_unit_outage_factors_from_events dated-bin keys; fleet.arrays dated exit-bin shares; "
            "derive_campd_unit_outages.py --exit-cohort-repair",
        ],
        "years_added": [],
        "free_parameters_added": 0,
        "dof_ledger": {
            **a.get("delta_vs_incumbent", {}).get("dof_ledger", {}),
            "carried": "VERBATIM from the PJM-NEXT-7 keeper; zero entries added.",
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
