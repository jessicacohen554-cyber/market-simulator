"""Generate the miso-218 PROBE leg's calibration attestation from the keeper's.

miso-218 is a **rule-13 DIAGNOSTIC PROBE, never a keeper** (PREREG §2, declared
before the solve). It exists so the arm can be SCORED — without an attestation the
C6 governance gate reads UNATTESTED and guard (b) of the C3c standing rule blocks
reclassification, which scores C3c FAIL on values identical to the control's (the
miso-200 vacuous-pass trap, hit and documented at miso-217 §5).

**No new ledger entry and no new parameter.** The probe mints nothing: the x1.10
ratio-preserving scale rides the EXISTING ``offer_curve_by_group`` operator channel
and is recorded verbatim in the bundle's ``run_config.json``. ``n_entries`` stays 41
and ``n_residual`` 2 — but see the disclosure: as a *fitted level scalar identified
against a price residual*, this arm is inadmissible as a keeper under rule 1
[R-STRUCT] regardless of what its gates say.

Usage:
    python3 scripts/gen_miso218_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "results/calibration/miso217_intermphys_B/calibration_attestation.json"
ARM = REPO / "results/calibration/miso218_levelscale_B"

DISCLOSURE = (
    "THIS RUN IS A RULE-13 DIAGNOSTIC PROBE AND IS NOT A KEEPER CANDIDATE. Declared "
    "in PREREG-miso218 §2 BEFORE the solve: a uniform multiplicative lift on every "
    "offer curve, chosen to move a price residual, is a FITTED LEVEL SCALAR "
    "identified against that residual. Rule 1 [R-STRUCT]'s second half forecloses it "
    "as a keeper mechanism and rule 13 admits it only as an explicitly-labelled, "
    "default-off diagnostic probe that must never be enabled in a keeper or quoted "
    "as evidence of forecast skill. It was run to BOUND a question the owner posed "
    "and nobody had answered: how much of C3a-2025 can a pure LEVEL lever reach, and "
    "what does it cost. (1) THE ARM: every offer-curve band multiplier (committed, "
    "econ_low, econ_high, peak) of all 13 fossil classes scaled x1.10; within-class "
    "ratios preserved exactly and fossil merit order preserved exactly, since every "
    "class scales by the same factor; structural tranche shares (econ_low_share, "
    "pct_peaking) and the MEASURED phys_* keys untouched. No ScenarioConfig field "
    "minted - the scale rides the existing offer_curve_by_group operator channel and "
    "is recorded verbatim in run_config.json. Ledger 41/2 unchanged. (2) THE OWNER'S "
    "PREMISE HELD AND MY OWN PRE-REGISTERED PREDICTION WAS WRONG, reported against "
    "interest. I predicted C3a-2023 would EXIT the +-10 % band (PREREG P-2, the "
    "decisive prediction). IT DID NOT. Measured C3a: 2023 +1.096 -> +8.402 % PASS, "
    "2024 -2.879 -> +4.396 % PASS, 2025 -12.297 -> -6.313 % PASS. ALL THREE YEARS "
    "INSIDE THE BAND, and the lane's standing C3a-2025 failure is CLOSED. The price "
    "pass-through is +7.23 / +7.49 / +6.82 % (P-1 predicted 7.0-9.5 %: the 2025 leg "
    "at 6.82 is WRONG, low). (3) WHAT IT COSTS, AND WHY THE DETERMINATION DOES NOT "
    "IMPROVE: the arm trades one load-bearing failure for another. C1 fuelmix "
    "ST_GAS-2024 EXITS the +-8.00 TWh band, -7.155 -> -8.030 TWh, PASS -> FAIL - the "
    "only PASS->FAIL flip on the board and a LOAD-BEARING criterion. So the run "
    "closes C3a-2025 and opens C1 ST_GAS-2024; NOT-YET in, NOT-YET out. The "
    "pre-registered named risk did NOT fire: CC_REGULAR-2024, which had only 0.053 "
    "TWh of band left, moved the SAFE way (+7.947 -> +6.564) because the lift "
    "suppresses CC too - P-6 wrong about which cell, right that a C1 cell was the "
    "live risk. (4) C8 RISES ON EVERY CLASS-YEAR, because a uniform lift prices "
    "fossil out and leaves the forced floors a larger share of a smaller class: "
    "CT_PEAKER 0.2280/0.1573/0.1319 -> 0.2571/0.1756/0.1437 (all three now above the "
    "0.15 peaker budget, where only 2023 and 2024 were before), ST_GAS "
    "0.1479/0.1555/0.2070 -> 0.1665/0.1784/0.2162. (5) THE TAIL IS UNTOUCHED, WHICH "
    "IS THE POINT. C3c hours of RT-expressible LMP > $200/MWh: model 3 / 7 / 0 -> 3 / "
    "7 / 1 against an actual 30 / 37 / 88 (PREREG P-5 RIGHT). A 10 % lift on a "
    "$183.22 maximum reaches ~$202. The scarcity tail miso-202/203 measured - top 1 % "
    "of hours carrying 99.9 % of the 2025 mean gap, 13 of 15 scarce hours in h18-h21 "
    "- is exactly as absent as before. C3b price shape: 0.080 -> 0.115 and 0.105 -> "
    "0.111 (WORSE, as PREREG P-4 predicted) but 0.180 -> 0.149 in 2025 (BETTER, which "
    "P-4's reasoning did not anticipate and which is reported against the "
    "prediction). (6) THE HONEST SUMMARY: a pure level lever CAN put all three C3a "
    "years inside the band. It does so by raising a Jun-Jul median that miso-202/203 "
    "measured as ALREADY ABOVE actual (37.47 vs 32.73), it leaves the scarcity tail "
    "untouched, it pushes every C8 class-year further over its budget, and it breaks "
    "a load-bearing C1 cell. That is the definition of moving the residual rather "
    "than the model."
)


def build(dst: Path) -> None:
    d = json.loads(SRC.read_text())
    d["governance"]["attested_by"] = (
        "miso-218 DIAGNOSTIC PROBE (2026-09-05), NOT A KEEPER CANDIDATE (rule 13; "
        "PREREG-miso218 §2, declared before the solve): control = the miso-217 "
        "keeper bundle miso217_intermphys_B itself (already attested, never "
        "re-solved) vs probe miso218_levelscale_B, MISO 2023+2024+2025 in one "
        "invocation, years sequential, solved in-session and never on CI (rules "
        "12/16), from the SAME committed keeper recipe via replay_keeper --set on "
        "the existing offer_curve_by_group operator channel. No ScenarioConfig field "
        "minted, no matrix row, ledger 41/2 unchanged. This attestation exists so "
        "the probe can be SCORED (without it C6 reads UNATTESTED and guard (b) of "
        "the C3c standing rule blocks reclassification); it is NOT a certification "
        "that the arm is admissible, which PREREG §2 forecloses."
    )
    d.setdefault("disclosures", {})["miso218_probe"] = DISCLOSURE
    dst.write_text(json.dumps(d, indent=1))
    print(f"wrote {dst.relative_to(REPO)} "
          f"(n_entries={d['free_parameters']['n_entries']}, "
          f"n_residual={d['free_parameters']['n_residual']})")


if __name__ == "__main__":
    build(ARM / "calibration_attestation.json")
