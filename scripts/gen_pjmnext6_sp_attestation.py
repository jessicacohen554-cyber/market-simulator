#!/usr/bin/env python3
"""Write the PJM-NEXT-6 card-1 (F2 split) composite's calibration_attestation.json.

The DOF ledger (``free_parameters``) and governance booleans are carried VERBATIM
from the PJM-NEXT-5 shape keeper (``pjmnext5_sh_span``): card 1 arms two default-off
flags, ``unit_outage_full_rederive`` and ``unit_outage_rederive_peaker_windows``,
which read the F2 full HEAD re-derive of PJM's standard CAMPD outage extract with
the listed gas-steam peakers' measured dead-period windows kept (owner ruling
2026-09-27, "Split") — a measured-input correction with zero parameters. Only the
provenance text and the ``delta_vs_incumbent`` block are rewritten. A composed
bundle inherits no attestation (pjm-h15 trap), so this runs after composition,
before registration.

Usage: python scripts/gen_pjmnext6_sp_attestation.py results/calibration/pjmnext6_sp_span
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEEPER = REPO / "results" / "calibration" / "pjmnext5_sh_span"
PINNED = "81dcf97436735d148ccdf2de2a26a407349bfb73"
PRECOMMIT = "docs/PRECOMMIT-pjm-next-6-card1-f2-split-2026-09-27.md"


def build() -> dict:
    """Return the attestation dict for the PJM-NEXT-6 card-1 (F2 split) composite."""
    a = copy.deepcopy(json.loads((KEEPER / "calibration_attestation.json").read_text()))
    g = a["governance"]
    g["attested_by"] = (
        "PJM-NEXT-6 orchestrator (2026-09-27). The PJM-NEXT-5 keeper recipe 2026-09-27-pjm-next-5-shape "
        f"(results/calibration/pjmnext5_sh_span) replayed at pinned {PINNED} via scripts/replay_keeper.py "
        "--set unit_outage_full_rederive=true --set unit_outage_rederive_peaker_windows=true, ONE YEAR PER "
        "SHARD CONTAINER 2019-2025 (rule 36), ZERO LP IN THE PARENT (rule 32(a)), composed at zero LP by "
        "scripts/probes/_pjmnext6_sp_compose_span.py (recipe check: keeper year plus exactly the arm flags, "
        "offers equal to the keeper's, pinned SHA, one solve-surface fingerprint). CONTROL: the committed "
        "keeper bundle for every year (rule 29(b) form 4), validated by a hunk-by-hunk G-DRIFT audit "
        f"recorded before any solve ({PRECOMMIT} §4)."
    )
    g["note"] = (
        "ONE MEASURED-INPUT CORRECTION (rule 14, owner ruling 2026-09-27 'Split'), pre-registered before "
        "any solve: the PJM standard CAMPD outage extract is the F2 full HEAD re-derive (year-consistent CC "
        "windows, membership union, COAL-SUB fix, unit-scoped peaker skip scope, per-unit fuel routing) with "
        "the listed ST_GAS peakers' measured full-dark (CF < 0.02, >= 5 d) dead-period windows kept. The "
        "companion's control reproduces the committed F2 file byte-for-byte. Zero free parameters added; no "
        "multiplier value changed."
    )
    a["delta_vs_incumbent"] = {
        "keeper": "2026-09-27-pjm-next-5-shape (results/calibration/pjmnext5_sh_span)",
        "config_deltas": [
            "unit_outage_full_rederive: False -> True",
            "unit_outage_rederive_peaker_windows: False -> True",
        ],
        "n_config_deltas": 2,
        "data_deltas": [
            "data/raw/campd-unit-outages-rederive-peakerkeep-unitfuel-PJM.csv (sha256 5171a5fb...)",
            "data/raw/campd-unit-outages-short-rederive-PJM.csv (the F2 short-coal companion)",
        ],
        "code_deltas": [
            "ScenarioConfig.unit_outage_rederive_peaker_windows + outages resolver branch",
            "derive_campd_unit_outages.py --keep-listed-peaker-dead-periods (default off)",
        ],
        "years_added": [],
        "free_parameters_added": 0,
        "dof_ledger": {
            **a.get("delta_vs_incumbent", {}).get("dof_ledger", {}),
            "carried": "VERBATIM from the PJM-NEXT-5 shape keeper; zero entries added.",
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
