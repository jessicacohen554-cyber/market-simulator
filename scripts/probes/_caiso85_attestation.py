"""Write the caiso-85 probe attestation.

Derives the bundle's ``calibration_attestation.json`` from the caiso-80 keeper
attestation already committed in the repo (same lever set and DOF ledger — the
probe adds NO free parameter: the single delta is the gated
``caiso_scarcity_import_headroom`` post-solve overlay change,
FINDING-caiso-winter-gas-level-2026-07-15 §3), swapping the ``attested_by`` line
and appending the probe's single-delta note. Deterministic from repo state
(_caiso80/84_attestation.py pattern).

Usage: python scripts/probes/_caiso85_attestation.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
BASE = ROOT / "caiso80_supply_consistent_demand" / "calibration_attestation.json"

DELTA85 = (
    " PLUS the single caiso-85 delta: caiso_scarcity_import_headroom=True "
    "(FINDING-caiso-winter-gas-level-2026-07-15 S3). The CAISO post-solve "
    "scarcity overlay (caiso_scarcity_pricing, on in the recipe) gains the "
    "hourly UNLOADED must-offer import capability in its LOLP reserve measure — "
    "min( sum over import tranches of pmax*availability - import dispatch, the "
    "measured WECC corridor import cap - import dispatch "
    "(eia_loader.measured_corridor_flow_envelope, the same envelope the LP "
    "dispatches under) ). RA imports are must-offer and must exhaust before "
    "CAISO's power-balance penalty prices fire (CPUC D.20-06-028), so the "
    "overlay pricing scarcity while the LP holds unloaded sub-VOLL import supply "
    "is internally inconsistent — this closes that inconsistency. POST-SOLVE "
    "OVERLAY ONLY: the LP dispatch, volumes and C1/C2/C4 are byte-identical to "
    "the keeper (the bundle's tripwire); only the scarcity adder (hence "
    "C3a/C3c) moves. ZERO new free parameters, zero fitted values: the import "
    "capability is measured tranche pmax and the bound is the measured corridor "
    "envelope; nothing tuned to the price residual (rule 14). The DOF ledger is "
    "identical to the caiso-80 keeper (no scalar added). Year-invariant "
    "code-level change (caiso-78 precedent): no per-year LOYO needed."
)

TARGETS = [
    (
        "caiso85_scarcity_import_headroom",
        "caiso-85 scarcity import-headroom probe session 2026-07-15",
        DELTA85,
    ),
]


def main() -> None:
    """Derive and write the probe attestation."""
    base = json.loads(BASE.read_text())
    for bundle, attested_by, delta in TARGETS:
        out_dir = ROOT / bundle
        if not out_dir.exists():
            print(f"[skip] {bundle}: bundle dir absent")
            continue
        d = json.loads(json.dumps(base))
        d["governance"]["attested_by"] = attested_by
        d["governance"]["note"] = d["governance"]["note"] + delta
        (out_dir / "calibration_attestation.json").write_text(json.dumps(d, indent=1))
        print(f"[ok  ] {bundle}")


if __name__ == "__main__":
    main()
