#!/usr/bin/env python3
"""Write a PJM-NEXT-16 composite's calibration_attestation.json (arm A or B).

The DOF ledger (``free_parameters``) and governance booleans are carried VERBATIM
from the PJM-NEXT-8 keeper (``pjmnext8_xf_span``). Arm A adds one registry fact
(``ISO_BA_JOINS["PJM"] = {"OVEC": (2019, 1)}``) with zero parameters; arm B adds
the PJM gas commitment bridge, whose two constants are MEASURED (CAMPD plant-basis
derive), not free. Only the provenance text and ``delta_vs_incumbent`` are
rewritten. A composed bundle inherits no attestation (pjm-h15 trap), so this runs
after composition, before registration.

Usage: python scripts/gen_pjmnext16_attestation.py {A|B} results/calibration/pjmnext16_<arm>_span
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEEPER = REPO / "results" / "calibration" / "pjmnext8_xf_span"
PINNED_BY_ARM = {
    "A": "6d4c77491e469e06f3a9c0e3d4f2b7c37b15fba3",
    "B": "42e87bcde2621cdd171b94b8076dac6108fa2771",
}
PRECOMMIT = "docs/records/pjm/PRECOMMIT-pjm-next-16-2026-09-30.md"
OVEC = (
    "ISO_BA_JOINS['PJM'] = {'OVEC': (2019, 1)} (Clifty Creek 983, Kyger Creek 2876; "
    "EIA-860 vintages 2018-2020 code them OVEC although they sit inside PJM's BA); "
    "vintages 2019/2020 rescoped (+11 rows each, strictly additive); outage "
    "apportionment admits joining-BA plants (outages._joining_ba_generators)"
)
BRIDGE = (
    "pjm_gas_commitment_bridge: False -> True with cc_mustrun_per_plant: True -> False "
    "(rule 19 replacement); min-load 0.436 / min-run 11 h MEASURED from CAMPD 2023-2025 "
    "plant basis (constants.PJM_GAS_BRIDGE_*)"
)


def build(arm: str) -> dict:
    """Return the attestation dict for arm ``arm``."""
    a = copy.deepcopy(json.loads((KEEPER / "calibration_attestation.json").read_text()))
    g = a["governance"]
    sets = (
        ""
        if arm == "A"
        else " --set pjm_gas_commitment_bridge=true --set cc_mustrun_per_plant=false"
    )
    g["attested_by"] = (
        f"PJM-NEXT-16 orchestrator (2026-09-30), arm {arm}. The PJM-NEXT-8 keeper recipe "
        "2026-09-28-pjm-next8-exitfix (results/calibration/pjmnext8_xf_span) replayed at "
        f"pinned {PINNED_BY_ARM[arm]} via scripts/replay_keeper.py{sets}, ONE YEAR PER SHARD "
        "CONTAINER 2019-2025 (rule 36), ZERO LP IN THE PARENT (rule 32(a)), composed at "
        "zero LP by scripts/probes/_pjmnext16_compose_span.py. CONTROL: the committed "
        "keeper bundle (rule 29(b) form 4), validated by a hunk-by-hunk G-DRIFT audit "
        f"recorded before any solve ({PRECOMMIT} §4)."
    )
    g["note"] = (
        "Rule 14 fleet-boundary repair (docs/FINDING-pjm-next-16-cc-loading-and-the-"
        "ovec-boundary-2026-09-30.md): OVEC's 2.39 GW, counted by the C1 benchmark and "
        "inside PJM's EIA-930 demand, now dispatches in 2019/2020. Zero free parameters."
        + (
            ""
            if arm == "A"
            else " Plus the owner-chartered PJM CC commitment bridge replacing "
            "cc_mustrun_per_plant's system-load window; two MEASURED constants, zero "
            "free parameters."
        )
    )
    deltas = [] if arm == "A" else [BRIDGE]
    a["delta_vs_incumbent"] = {
        "keeper": "2026-09-28-pjm-next8-exitfix (results/calibration/pjmnext8_xf_span)",
        "config_deltas": deltas,
        "n_config_deltas": len(deltas),
        "data_deltas": [
            "data/raw/eia-860/vintage_2019/eia860_generators.parquet (+11 OVEC rows)",
            "data/raw/eia-860/vintage_2020/eia860_generators.parquet (+11 OVEC rows)",
        ]
        + (
            []
            if arm == "A"
            else [
                "data/raw/_processed-legacy/campd_gas_commitment_params_plant_PJM.csv (new)"
            ]
        ),
        "code_deltas": [OVEC]
        + (
            []
            if arm == "A"
            else [
                "ScenarioConfig.pjm_gas_commitment_bridge; pipeline.commitment."
                "build_pjm_gas_bridge_p1_prep; MECH_PJM_GAS_COMMITMENT_BRIDGE (27)"
            ]
        ),
        "years_added": [],
        "free_parameters_added": 0,
        "dof_ledger": {
            **a.get("delta_vs_incumbent", {}).get("dof_ledger", {}),
            "carried": "VERBATIM from the PJM-NEXT-8 keeper; zero entries added.",
        },
        "authorized_price_tuning": {
            "used": False,
            "note": "NO band multiplier was touched: offer_curve_overrides equal to the keeper's on every leg.",
        },
    }
    return a


def main() -> int:
    """CLI entry point."""
    arm, out = sys.argv[1], Path(sys.argv[2])
    if arm not in ("A", "B"):
        raise SystemExit("arm must be A or B")
    (out / "calibration_attestation.json").write_text(
        json.dumps(build(arm), indent=2) + "\n"
    )
    print(f"wrote {out / 'calibration_attestation.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
