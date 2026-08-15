"""Write ``calibration_attestation.json`` for the miso-96 sunk-fixed take-or-pay arm.

The arm is a SINGLE-DELTA A/B on the miso-93 control (itself the
``2026-07-25-miso-88-egrid-hr`` keeper recipe replayed on the guard-corrected
CAMPD extract), so its governance posture, disclosures and inherited exception
ledger are the control's — only the ``attested_by`` narrative and the
delta-specific disclosure change. The ``free_parameters`` DOF ledger is then
refreshed from THIS bundle's ``run_config.json`` by
``scripts/build_dof_ledger.py`` (run separately; this script does not compute
it), so the ledger describes the arm rather than the control.

The delta REMOVES a discount rather than sizing one, so it adds no free
parameter and the ledger is expected to be unchanged from the control's.

Usage:
    python scripts/gen_miso96_attestation.py
    python scripts/build_dof_ledger.py results/calibration/miso96_sunkfixed
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CONTROL = REPO / "results/calibration/miso93_meritguard_a1/calibration_attestation.json"
ARM = REPO / "results/calibration/miso96_sunkfixed/calibration_attestation.json"

ATTESTED_BY = (
    "miso-96 sunk-fixed take-or-pay arm 2026-07-27: the miso-93 control "
    "(= the 2026-07-25-miso-88-egrid-hr keeper recipe on the guard-corrected "
    "CAMPD economic-layup extract) replayed via replay_keeper with ONE delta, "
    "ScenarioConfig.coal_committed_takeorpay_sunk_fixed=true. The delta is a "
    "correction to how an existing measured mechanism enters the offer, not a "
    "new mechanism and not a tuned value. A take-or-pay coal contract is an "
    "obligation over an accounting period (contracted tonnage per year/month): "
    "it is sunk in aggregate and therefore a FIXED cost, so it does not enter "
    "the marginal cost of an incremental MWh for a plant that over-fulfils it "
    "-- that plant buys its marginal ton at spot. The committed-band discount "
    "priced the obligation as an unconditional PER-HOUR MARGINAL subsidy "
    "instead, which pinned 9,403 MW of regulated PRB inframarginal in all 8760 "
    "hours (RE PRB committed $28.09 -> $5.07/MWh at the miso-66 wiring check) "
    "and stopped it de-loading overnight. Measured consequence, invisible "
    "until the rubric v2.8 coal gate widening: D-1 off-peak cv_ratio collapsed "
    "0.880/1.036/0.470 (miso-65) to ~0.45/0.44/0.36 from miso-66 onward, "
    "against a CEMS record showing the same regulated fleet cycling 53.6% -> "
    "66.2% utilisation across the day. Rule 17 [R-FLOOR-WINDOW]: the discount "
    "had a driver and a forward story but NO WINDOW -- it bound in every hour, "
    "including the hours its own driver evidence says the plant de-loads. Rule "
    "19 [R-ONE-MECH]: the contract is already carried ONCE, on the _mustrun "
    "band that is on regardless of price, which this delta leaves untouched. "
    "The mechanism itself is NOT reverted (rules 1 [R-STRUCT] / 14 "
    "[R-ACCURATE]) -- regulated-coal take-or-pay is real and measured from "
    "EIA-860 Regulatory Status plus each plant's own EIA-923 Schedule-5 share. "
    "Zero degrees of freedom added: the delta REMOVES a discount, it does not "
    "size one (rule 24 [R-DOF]). Evidence: "
    "results/calibration/FINDING-miso96-coal-prb-offpeak-2026-07.md."
)

DISCLOSURE = (
    "See metrics.json determination + reasons. This is an A/B ARM, not a "
    "promoted keeper; the designated MISO keeper is unchanged "
    "(2026-07-25-miso-88-egrid-hr). C7 diurnal shape (D-1 COAL_PRB), the "
    "criterion the delta targets, moves 0.453/0.441/0.364 -> 0.792/0.985/0.438 "
    "against a >=0.50 gate: 2023 and 2024 CLEAR, 2025 improves ~20% but still "
    "FAILS. The 2025 residual is NOT re-attacked with a second mechanism "
    "(rule 19 [R-ONE-MECH]) and is NOT ledgered (C7 is protective and hard). "
    "The model's 2025 off-peak CV is 0.033 against a measured 0.075, i.e. the "
    "coal fleet still barely cycles in the one year the standing MISO evidence "
    "says the system is ~10 GW tighter than the model can see at summer peak "
    "(FINDING-miso89 (2), the outage-grain data ask). Ledgered caveats are "
    "inherited from the control unchanged, not widened to absorb this."
)


def main() -> int:
    att = json.loads(CONTROL.read_text())
    att["governance"] = dict(att.get("governance", {}), attested_by=ATTESTED_BY)
    att["disclosures"] = dict(att.get("disclosures", {}), note=DISCLOSURE)
    ARM.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {ARM.relative_to(REPO)}")
    print(
        "now run: python scripts/build_dof_ledger.py results/calibration/miso96_sunkfixed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
