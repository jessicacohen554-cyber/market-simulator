"""Add the owner-authorized C3c-2023 exception to the NYISO keeper's ledger.

The designated keeper is unchanged — ``2026-08-06-nyiso-128-solar-basis``
(bundle ``results/calibration/nyiso128_treatment``). nyiso-130's A/B on the
published Zone-K transfer limit was **rejected as armed** (its own pre-registered
kill gate K6 fired), so the incumbent stays. Nothing in the keeper's *results*
is touched by this script: it writes one entry into the ledger, which is the
artifact owner-authorized caveats live in.

**What this resolves.** nyiso-129 WITHHELD the C3c-2023 exception rather than
laundering it: the inherited caveat's own classification reads "five-zone
representation *cannot form* the sub-zonal scarcity", an UNDER-production, while
2023 fails in the OPPOSITE direction (22 h against a measured 10 h, 2.20x
OVER-produced). The exception was missing an authorization, not a justification.

**The authorization, given in session nyiso-130, 2026-08-06, verbatim:**

    "After this run if the only outstanding issue is c3c scarcity tail of +12
    hours in 2023 I want NYISO registered as calibrated with caveats. C3c is an
    acceptable gate failure as a ledgered caveat."

The condition is met exactly as stated: on this keeper C3c is the SOLE failing
criterion (C1/C2/C3a/C3b/C4/C6/C8 all PASS at HEAD under rubric v3.1) and the
2023 miss is +12 hours (22 vs 10). This supplies the IN-TRAINING authorization
CLAUDE.md rule 22's C3c standing rule does not reach — that rule is
out-of-training only.

**Two disciplines are kept, not waived.** (1) The 2023 entry carries its OWN
correctly-signed classification naming the over-production; it does NOT ride
under the 2024 under-production caveat, and the withheld block is preserved as
``_withheld_exception_history`` so the record shows the exception was authorized
rather than quietly widened. (2) The magnitude is recorded at full size.

Run: ``python scripts/gen_nyiso130_keeper_ledger.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results/calibration/nyiso128_treatment"
ATTESTATION = KEEPER / "calibration_attestation.json"

OWNER_DIRECTIVE_VERBATIM = (
    "After this run if the only outstanding issue is c3c scarcity tail of +12 "
    "hours in 2023 I want NYISO registered as calibrated with caveats. C3c is "
    "an acceptable gate failure as a ledgered caveat."
)

ENTRY_2023 = {
    "criterion": "price_tail",
    "year": 2023,
    "metric": (
        "hours RT-expressible LMP > $300/MWh (C3c scarcity tail, actual RT hourly gate)"
    ),
    "magnitude": (
        "model 22 h > $300/MWh against RT actual 10 h (2.20x, +12 h; gate band "
        "[5, 20] h). Recorded at FULL magnitude and NOT softened. This is an "
        "OVER-production — the opposite sign to the 2024 entry."
    ),
    "classification": (
        "MODEL MISS (structural, OVER-production) — ACCEPTED MODEL-CLASS "
        "LIMITATION under the owner directive below. The 2023 miss is NOT the "
        "miss the 2024 caveat licenses and does not ride under it: that entry's "
        "classification reads 'five-zone representation CANNOT FORM the "
        "sub-zonal NYC/LI load-pocket scarcity', an UNDER-production. "
        "nyiso-130 IDENTIFIED the over-production's owner and it is now a "
        "diagnosed defect rather than an unexplained residual: 100 % of the "
        "model's C3c tail hours in ALL THREE years are Long Island, inside the "
        "HB14-21 window, with BOTH Zone-K import paths at their bound — so the "
        "whole modelled tail is formed at the in-window cap on "
        "NYC>Long_Island, and its COUNT is set by how tightly Zone K is bounded "
        "rather than by a sub-zonal pocket the five-zone model lacks."
    ),
    "reason": (
        'OWNER DIRECTIVE, session nyiso-130, 2026-08-06, verbatim: "'
        + OWNER_DIRECTIVE_VERBATIM
        + "\" The directive's own condition is met exactly as stated: C3c is "
        "the SOLE failing criterion on this keeper (C1/C2/C3a/C3b/C4/C6/C8 all "
        "PASS at HEAD under rubric v3.1, C3a +8.8 / +0.8 / -3.2 %) and the 2023 "
        "miss is +12 hours. This supplies the IN-TRAINING authorization rule "
        "22's C3c standing rule does not reach (that rule is out-of-training "
        "only), and it resolves the exception nyiso-129 deliberately withheld — "
        "an authorization was what that entry lacked, not a justification. "
        "THE LANE IS NOT EXHAUSTED AND THIS IS NOT A CLOSURE: nyiso-130 both "
        "identified the object AND tested the obvious fix, which FAILED its own "
        "pre-registered kill gate. NYISO publishes, in TABLE 1 note 2 of the "
        "Locality Bulk Power Transmission Capability Reports (identical in the "
        "2024-25, 2025-26 and 2026-27 editions), that the Zone-K 'Locality "
        "Limit' the cap uses is the transfer limit NET of a 660 MW generation "
        "loss-of-source: 'The true N-1-1 Transmission Security Limit is 940 in "
        "this scenario, the Bulk Transfer Limit accounts for the loss-of-source "
        "of 660 MW'. Arming the published 940 MW (nyiso-130 A/B, run "
        "2026-08-06-nyiso-130-n11-tsl) collapses the tail to 2 / 0 / 5 h "
        "against 10 / 12 / 42 — C3c then fails all three years UNDER-produced, "
        "2024 forming ZERO scarcity hours — and fires kill gate K6: the "
        "downstate ST_GAS reliability floor takes up the slack, forcing "
        "+0.22 / +0.42 / +0.23 TWh more (share 20.4->22.2 / 22.0->26.0 / "
        "15.4->17.0 %). So Zone-K reliability in this model is carried by TWO "
        "proxies — a too-tight transfer bound and a min_gen floor — and "
        "relieving one loads the other. The successor is a JOINT reconciliation "
        "of both under rule 19 [R-ONE-MECH], not a bare number swap; it needs "
        "its own charter and pre-registration. Evidence: "
        "results/calibration/FINDING-nyiso130-li-transfer-security-limit-"
        "2026-08-06.md, PREREG-nyiso130-li-transfer-security-limit-2026-08-06"
        ".md, _nyiso130_li_tsl_identification.json, _nyiso130_ab_gates.json."
    ),
}


def main() -> int:
    """Write the owner-authorized 2023 entry into the keeper's ledger."""
    obj = json.loads(ATTESTATION.read_text())
    existing = {int(e["year"]): e for e in obj.get("exceptions", [])}
    if 2023 in existing:
        print("2023 exception already present — nothing to do")
        return 0

    withheld = obj.pop("_withheld_exception", None)
    if withheld is not None:
        obj["_withheld_exception_history"] = {
            "resolved_by": (
                "OWNER DIRECTIVE, session nyiso-130, 2026-08-06 (quoted in the "
                "2023 exception's reason). The block below is PRESERVED, not "
                "deleted: the record must show the exception was AUTHORIZED, "
                "not quietly widened under the 2024 caveat's classification. "
                "The withheld-exception guard itself stays in force for any "
                "future wrong-sign miss (scripts/gen_nyiso130_attestation.py)."
            ),
            "withheld_block_as_written_by_nyiso_129": withheld,
        }

    obj["exceptions"] = sorted(
        list(obj.get("exceptions", [])) + [ENTRY_2023], key=lambda e: int(e["year"])
    )
    ATTESTATION.write_text(json.dumps(obj, indent=1))
    print(
        f"keeper ledger: {len(obj['exceptions'])} C3c exception(s) "
        f"({', '.join(str(e['year']) for e in obj['exceptions'])}); "
        f"withheld block preserved as history: {withheld is not None}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
