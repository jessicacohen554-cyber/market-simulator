"""caiso-200 — carry the keeper's DOF ledger onto an A/B bundle (G-DOF).

`PRECHECK-caiso200-panel-membership-2026-08-17.md` §4 G-DOF: both arms must
carry the caiso-197 composed ledger **unchanged at 10/7** — the fleet-member
panel scope adds no parameter and no fitted scalar (membership is derived from
the fleet registry; the delta content was fixed by the pre-flip caiso-198
run-Y measurement), and the landing moves DATA, not freedom.

The DOF ledger is a property of the CONFIGURATION, not of a solve: both arms
replay the keeper's own config (G-DELTA leg (d) verifies the control-vs-arm
`scenario_config` diff is EMPTY), so the keeper's ledger IS each arm's ledger.
Carried byte-identically rather than regenerated — the caiso-198/199 pattern.

Only `free_parameters` is written here. **No governance block is fabricated**:
an attestation is generated AT a promotion, by the promoting session
(`scripts/gen_caiso200_attestation.py`), never here.

Guard: the target bundle's config is diffed against the keeper's; the ledger
is written only when the diff beyond the MEASURED head-drift allow-list is
empty. Usage::

    python scripts/probes/_caiso200_carry_dof_ledger.py <bundle-dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results" / "calibration" / "caiso197_w2_r5"

# Fields present in the tree's ScenarioConfig but absent from the committed
# keeper's run_config (it predates them). All ship default-OFF and none is a
# CAISO mechanism — `ercot_reserve_supply_cap_net_credits` is ERCOT-scoped by
# name and rule 25; `reliability_floor_plant_exclusions` is the nyiso-140
# field (default off, NYISO-motivated). Their inertness on this ISO is not
# asserted, it is MEASURED: G-CTRL came back bit-zero against the committed
# caiso-199 arm (max |Δ| = 0.0 over every zone-hour and class-hour of all
# three years, `_caiso200_ctrl_tolerance.json`).
HEAD_DRIFT_ALLOWED = {
    "commission_year_cod_fallback": (None, False),
    "ercot_reserve_supply_cap_net_credits": (None, False),
    "reliability_floor_plant_exclusions": (None, False),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", help="bundle dir to write the ledger into")
    args = ap.parse_args()
    bundle = Path(args.bundle)
    if not bundle.is_absolute():
        bundle = REPO / bundle

    keeper_cfg = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    arm_cfg = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    diff = {
        k: (keeper_cfg.get(k), arm_cfg.get(k))
        for k in sorted(set(keeper_cfg) | set(arm_cfg))
        if keeper_cfg.get(k) != arm_cfg.get(k)
    }
    unexplained = {
        k: v for k, v in diff.items() if HEAD_DRIFT_ALLOWED.get(k) != tuple(v)
    }
    if unexplained:
        print(json.dumps({"unexplained_config_diff": unexplained}, indent=1))
        raise SystemExit(
            "config diff beyond the measured head drift — the keeper's ledger "
            "may not be carried onto a bundle whose configuration differs"
        )

    ledger = json.loads((KEEPER / "calibration_attestation.json").read_text())[
        "free_parameters"
    ]
    out = bundle / "calibration_attestation.json"
    out.write_text(json.dumps({"free_parameters": ledger}, indent=1))
    print(
        json.dumps(
            {
                "bundle": bundle.name,
                "n_entries": ledger["n_entries"],
                "n_residual": ledger["n_residual"],
                "carried_from": KEEPER.name,
                "head_drift_fields": sorted(diff),
                "governance_block_written": False,
                "note": (
                    "free_parameters only — C6 stays UNATTESTED until a "
                    "promotion attestation is generated"
                ),
            },
            indent=1,
        )
    )
    print(f"\nwrote {out.relative_to(REPO)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
