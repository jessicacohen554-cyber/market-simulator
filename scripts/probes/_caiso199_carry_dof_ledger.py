"""caiso-199 — carry the keeper's DOF ledger onto an A/B bundle (G-DOF).

`PRECHECK-caiso199-merit-panel-scope-2026-08-16.md` §4 G-DOF: both arms must
carry the caiso-197 composed ledger **unchanged at 10/7** — the pin adds no
parameter and no fitted scalar, and the landing adds DATA, not freedom.

The DOF ledger is a property of the CONFIGURATION, not of a solve: both arms
replay the keeper's own config (G-DELTA leg (d) verifies the control-vs-arm
`scenario_config` diff is EMPTY), so the keeper's ledger IS each arm's ledger.
This carries it across byte-identically rather than regenerating it, which is
exactly what the caiso-198 control did (`caiso198_f0_control`'s attestation is
the keeper's `free_parameters` block, byte-identical and nothing else).

Only `free_parameters` is written. **No governance block is fabricated**: a
non-keeper A/B arm has no attestation sitting, so C6 stays UNATTESTED — the
standard control posture (caiso-198 §2). An attestation is generated AT a
promotion, by the promoting session, never here.

Guard: the target bundle's config is diffed against the keeper's and any
difference beyond an explicit allow-list is reported; the ledger is written
only when the remaining diff is empty. Usage::

    python scripts/probes/_caiso199_carry_dof_ledger.py <bundle-dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results" / "calibration" / "caiso197_w2_r5"

# Fields present in the tree's ScenarioConfig but absent from the committed
# keeper's run_config (it predates them). Both ship default-OFF and neither is
# a CAISO mechanism — `ercot_reserve_supply_cap_net_credits` is ERCOT-scoped by
# name and by rule 25. Their inertness on this ISO is not asserted, it is
# MEASURED: G-CTRL came back bit-zero (max |Δ| = 0.0 over every zone-hour and
# class-hour of all three years, `_caiso199_ctrl_tolerance.json`), which is the
# empirical proof that the head difference changes no CAISO solve.
HEAD_DRIFT_ALLOWED = {
    "commission_year_cod_fallback": (None, False),
    "ercot_reserve_supply_cap_net_credits": (None, False),
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
    unexplained = {k: v for k, v in diff.items() if HEAD_DRIFT_ALLOWED.get(k) != v}
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
                    "free_parameters only — C6 stays UNATTESTED, the standard "
                    "non-keeper A/B control posture (caiso-198 §2)"
                ),
            },
            indent=1,
        )
    )
    print(f"\nwrote {out.relative_to(REPO)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
