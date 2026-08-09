"""Promote the MISO keeper to 2026-08-09-miso-148-basis-aware (miso-148).

Owner decision, 2026-08-09. The session itself ESCALATED rather than promoted —
its PREREG §9(1) conditioned promotion on the fail set staying ⊆ {C3a}, and the
arm's C3b-2025 crosses its gate — so this promotion is taken on the owner's
standing structural-integrity guidance with the regression quoted at full
magnitude.

Edits ONLY MISO's own shard + its run sidecar's ``market_story`` (per-ISO lane
isolation, `frontend/data/backcast/keepers/README.md`). One-shot; kept in-tree
as the record of exactly what the promotion wrote.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SHARD = REPO / "frontend" / "data" / "backcast" / "keepers" / "MISO.json"
SIDECAR = (
    REPO
    / "frontend"
    / "data"
    / "backcast"
    / "registry"
    / "2026-08-09-miso-148-basis-aware.json"
)
KEEPER_ID = "2026-08-09-miso-148-basis-aware"

PROMOTION_NOTE = (
    "PROMOTED 2026-08-09 (miso-148), on an EXPLICIT OWNER DECISION taken after the session "
    "ESCALATED rather than promoted. MISO keeper -> 2026-08-09-miso-148-basis-aware (bundle "
    "results/calibration/miso148_basis_B). THE SINGLE DELTA against the predecessor "
    "2026-08-05-miso-132b-cc-committed is ONE ScenarioConfig field, summer_derate_basis_aware=true, "
    "applied via replay_keeper --set through the generic prb_overrides channel and recorded verbatim "
    "in run_config.json (rule 24 [R-REGISTRY]); scored against a SAME-HEAD ZERO-DELTA CONTROL "
    "(2026-08-09-miso-148-control, bundle miso148_basis_A), never against the committed predecessor "
    "(the miso-124 DO-NOT-MISREAD). "
    "WHAT IT IS. The flat _SUMMER_CLASS_DERATE (CC 10 %, CT 12.5 %) IS the nameplate -> summer-peak "
    "ambient loss, so it belongs only on a NAMEPLATE-basis capacity. On MISO's per-plant EIA-860 path "
    "pmax IS the published net-summer rating, which already embeds that loss, so re-applying it is a "
    "DOUBLE COUNT -- miso-141 measured the base (net-summer for 100 % of matched CT_PEAKER / CT_CHP / "
    "CC_CHP capacity) and the size (clean nameplate->summer gaps 11.40 / 14.34 / 16.35 / 15.25 % by "
    "class), and REFUTED the 'incremental ambient loss below the rating point' reading on MISO's own "
    "slopes and weather: the honest incremental is an UPRATE of ~2 % (CC) / ~3.7 % (CT), because the "
    "mean summer hour sits 8.3-11.9 C BELOW the p99 rating condition in 18 of 18 zone-years. The flag "
    "applies the flat derate ONLY to units still on a nameplate basis and suppresses it where pmax "
    "already IS a measured summer capability. CLASS-AGNOSTIC (CC_REGULAR, CC_CHP, CT_PEAKER, CT_CHP) "
    "-- CT_PEAKER is the LARGEST single contributor, 2,551 MW in 2025, the half miso-141 measured as "
    "having NO mechanism at all -- and a PURE basis correction: no POF drop, no age-derate drop, no "
    "WEFOR change, no capacity rescale and NO off-summer leg (rule 19 [R-ONE-MECH]; the off-summer "
    "half is a separate defect with its own mechanism, cc_winter_capability_basis, and MISO's measured "
    "Oct-Mar CC availability headroom is POSITIVE, so no evidence asks for it). This is the successor "
    "miso-141 section 11.2 specified and refused to build; cc_nameplate_summer_derate stays "
    "DO-NOT-REDO (it reaches ~52 % of the affected MW and bundles four changes into one flag). "
    "ZERO CONTINUOUS DEGREES OF FREEDOM (rule 21 [R-DOF]): a boolean over a data predicate, with no "
    "tunable fraction, per-class scale or sweepable tolerance -- and no parameterised variant was "
    "built or solved, because that would be exactly the channel through which a residual could be "
    "fitted. Corrupt EIA-860 filings are handled EXPLICITLY rather than by silent clamp (miso-141 "
    "section 11.2(c)): plants the always-on CC guard clips onto max(nameplate, demonstrated_peak) "
    "KEEP the flat derate, as do plants absent from EIA-860. Measured on the real 2025 fleet: 86.9 % "
    "of flat-derate MW admitted, 7,255 MW across 9 CC + 4 CT plants kept. The predicate reads the "
    "guard's OWN recorded clip decision rather than re-deriving it from the raw sheet, because the "
    "plant-total-on-one-row pattern hides behind NaN component rows the loader nameplate-fills -- "
    "55380 and 55467 both read 'clean' on the raw sheet while the loader clips them by 1,028.6 and "
    "353.3 MW -- and a re-derived predicate walked straight into that trap in-session and was "
    "replaced. "
    "WHAT IT REPAIRS, and why it is a keeper. Measured fleet-side (no LP), monthly AV_CC - A_CC in "
    "Jun-Sep 2025 moves -2,296 / -2,451 / -2,157 / -1,560 MW -> -373 / -369 / -77 / +419 MW: MODEL "
    "AVAILABLE CC CAPABILITY NO LONGER SITS BELOW REALITY'S OBSERVED CC GENERATION in the months the "
    "double count applied -- the indefensible object miso-147 identified, since availability below "
    "observed output cannot be justified by any outage input. Dispatch moves the way miso-147 "
    "measured the defect: 2023 CC_REGULAR +3.16 TWh displacing COAL_PRB -1.24, import -1.05, ST_GAS "
    "-0.81, COAL_BIT -0.35, CT_PEAKER -0.33. "
    "THE COST, REPORTED AT FULL MAGNITUDE AND KEPT (rules 1 [R-STRUCT] / 14 [R-ACCURATE]): C3a "
    "-0.49 / -6.01 / -14.15 % -> -1.98 / -8.03 / -15.58 %, WORSE IN EVERY YEAR; C3b-2025 NRMSE 0.192 "
    "-> 0.212, THROUGH its 0.200 gate, so C3b joins C3a as a FAIL and the fail set grows {C3a} -> "
    "{C3a, C3b}; ST_GAS forced share +2.4 / +2.8 / +3.7 pp (C8 still PASSES -- every binding mechanism "
    "clears D-4, the D-1 shape gates hold, no new forcing id appears, and the rise is mechanical: "
    "restored CC displaces ST_GAS / CT_PEAKER ECONOMIC energy while their floored energy is "
    "unchanged). Determination is NOT-YET in BOTH arms, so no determination changes. The direction was "
    "DISCLOSED IN ADVANCE and against interest (PREREG section 6 P5 at 0.75: the repair adds "
    "capability, so its price effect is downward -- the wrong way for a 2025 already 14 % low), and "
    "the charter's against-interest bound stands: 2023 carries nearly the same CC gap and C3a-2023 "
    "PASSES, so the composition defect never predicted closing 2025's -14.1 %. Nothing here is offered "
    "as progress against the level miss. "
    "WHY IT IS PROMOTED ANYWAY. Rule 14 [R-ACCURATE] is explicit that when an accurate measured input "
    "makes the backcast WORSE, that is a DISCOVERED BUG -- the estimate was silently compensating for "
    "a real miscalibration elsewhere -- and the accurate input is KEPT rather than buried back inside "
    "an inaccurate one. Rule 1 [R-STRUCT] forbids rejecting a structurally-correct mechanism because "
    "the residual moved the wrong way, and defines a keeper as the MOST STRUCTURALLY FAITHFUL run, not "
    "the lowest-MAE one. SUMMER_CLASS_DERATE is uncited, measured to be the wrong object for MISO, and "
    "was removing 5.7-5.9 GW of real summer capability; the arm is more faithful by construction. The "
    "session itself did NOT promote -- its PREREG section 9(1) conditioned promotion on the fail set "
    "staying a subset of {C3a}, which it did not -- and escalated instead; this promotion is the "
    "OWNER'S call under the standing 2026-08-09 structural-integrity guidance, taken with the C3b "
    "regression quoted at full magnitude. "
    "LEAVE-ONE-YEAR-OUT (rule 22): ZERO fitted parameters and nothing year-specific -- the predicate is "
    "each plant's own published rating -- and the effect is SAME-SIGNED in all three years (AV_CC - "
    "A_CC rises 3/3; C3a moves -1.49 / -2.02 / -1.43 pp; restored summer capability 4,937 / 4,868 / "
    "4,671 MW). C3b's PASS->FAIL flip occurs ONLY in 2025, whose control NRMSE 0.192 already sat 0.008 "
    "from the gate; 2023 and 2024 stay PASS (0.082, 0.125) and C3a stays PASS in both. "
    "K0 FAILED AS WRITTEN AND IS REPORTED, NOT REDEFINED: the zero-delta control does NOT reproduce "
    "the predecessor's committed class-hour sidecars (max |delta| 912.5 MW; total class drift 0.54 / "
    "0.14 / 0.46 TWh on ~500 TWh, ~0.1 %), because of HEAD DRIFT since the predecessor's own solve "
    "(git_sha 6b05f058, NOT reachable in this shallow clone -- an instrument limit disclosed rather "
    "than papered over). PROVEN not to be the session's edits: the drift's full magnitude sits in "
    "non-summer hours of non-gas classes, outside the mechanism's reach even when ARMED, and it is "
    "corroborated by a second instrument (the ERCOT fleet-arrays golden test fails identically at the "
    "pre-session base, on the same availability / min_gen arrays). The scorecard, unlike the sidecars, "
    "barely moves (control C3a -0.49 / -6.01 / -14.15 % against the predecessor's -0.4 / -6.0 / "
    "-14.1), so the drift is immaterial at the gated grain -- but the predecessor was NOT "
    "bit-reproducible at HEAD, which is why every delta quoted here is arm-vs-CONTROL and no "
    "arm-vs-predecessor delta is quoted anywhere. "
    "A MEASURED CORRECTION TO miso-147 section 6 THAT ANY SUCCESSOR MUST CARRY: the mechanism moves "
    "prices in Jun-Sep and NOWHERE ELSE (2025 monthly delta 0, 0, 0, 0, -0.006, -1.836, -2.448, "
    "-1.403, -1.276, -0.003, 0, 0 $/MWh), so MAY IS NOT REACHABLE BY IT -- May-2025 goes +12.43 % -> "
    "+12.41 %. May's CC availability deficit and the summer deficit are the SAME SYMPTOM WITH "
    "DIFFERENT CAUSES; 'one object, both signs' describes the symptom, not the cause, and the May half "
    "remains UNEXPLAINED. "
    "Rule 25 [R-ISO-SCOPE]: the predicate is each MISO plant's own published EIA-860 rating; no "
    "parameter crosses an ISO boundary and no other ISO's cell or shard is touched (CAISO / PJM / "
    "NYISO / NEISO all leave CT_PEAKER / CT_CHP on the flat derate over a net-summer base, so the same "
    "double count is live and UNMEASURED there -- their matrix cells stay U). Rule 22 [R-HOLDOUT]: "
    "2023-2025 only, both arms, one invocation each; MISO holds no calibration-complete marker, so no "
    "out-of-training year was solved, scored or read and the D-5(b) re-key duty does not apply. "
    "Evidence: results/calibration/FINDING-miso148-summer-basis-repair-2026-08-09.md; PREREG "
    "results/calibration/PREREG-miso148-cc-availability-summer-basis-2026-08-09.md @ 456b376."
)

OWN_DELTA = (
    "THIS KEEPER'S OWN DELTA (miso-148): MISO no longer derates its gas fleet for summer ambient loss "
    "TWICE. The flat _SUMMER_CLASS_DERATE (CC 10 %, CT 12.5 %) IS the nameplate -> summer-peak ambient "
    "loss, but MISO's per-plant pmax is ALREADY the published EIA-860 net-summer rating, which embeds "
    "that loss -- so the model was removing it a second time, 5.7-5.9 GW of summer h12-17 capability "
    "(miso-141, which also refuted the 'incremental loss' reading: the honest incremental is an "
    "UPRATE, sign inverted in 18 of 18 zone-years). The new class-agnostic flag applies the flat "
    "derate ONLY to units still carried on a nameplate basis, KEEPS it for corrupt-filing plants the "
    "always-on CC guard clips onto a nameplate-like bound (86.9 % of MW admitted; 7,255 MW kept across "
    "9 CC + 4 CT plants), and changes nothing else -- no POF or age-derate drop, no WEFOR change, no "
    "capacity rescale, no off-summer leg. ZERO free parameters. CT_PEAKER, which had NO mechanism at "
    "all and the largest measured gap, is the biggest single contributor (2,551 MW in 2025). WHAT IT "
    "REPAIRS: monthly AV_CC - A_CC in Jun-Sep 2025 moves -2,296 / -2,451 / -2,157 / -1,560 MW -> -373 "
    "/ -369 / -77 / +419 MW, so model available CC capability no longer sits BELOW reality's observed "
    "CC generation -- availability below observed output is indefensible for any outage input. Against "
    "a same-HEAD zero-delta control the restored CC runs (2023 CC_REGULAR +3.16 TWh) and displaces "
    "COAL_PRB, imports and ST_GAS, exactly the composition defect miso-147 measured. THE COST IS REAL "
    "AND IS KEPT: C3a -0.49 / -6.01 / -14.15 % -> -1.98 / -8.03 / -15.58 %, worse in every year, and "
    "C3b-2025 NRMSE 0.192 -> 0.212 crosses its 0.200 gate, so the fail set grows to {C3a, C3b}; ST_GAS "
    "forced share rises +2.4 / +2.8 / +3.7 pp with C8 still passing and grounded. Determination stays "
    "NOT-YET. The downward price direction was disclosed BEFORE the solve, and nothing here is offered "
    "as progress against the 2025 level miss. Promoted on structural fidelity under rules 1 "
    "[R-STRUCT] / 14 [R-ACCURATE] by explicit OWNER DECISION -- the session escalated rather than "
    "promoted, because its own PREREG conditioned promotion on the fail set staying a subset of "
    "{C3a}. A CORRECTION ANY SUCCESSOR MUST CARRY: the mechanism moves prices in Jun-Sep and nowhere "
    "else, so MAY IS NOT REACHABLE BY IT (+12.43 % -> +12.41 %) -- May and summer are the same symptom "
    "with different causes, and the May half is still unexplained."
)

MARKET_STORY = (
    "CC (combined cycle) -- the class the repair restores. MISO's gas CCs are the mid-merit workhorse "
    "of a summer afternoon: on a hot July day the real market runs them hard, and CAMPD shows the "
    "fleet generating MORE than the model believed it could even be AVAILABLE to produce. That is why "
    "the correction is not a tuning choice -- an availability number below a measured generation "
    "number is not a defensible input. Restoring the double-counted ambient haircut lets the CC fleet "
    "carry the summer afternoon the way its own meters say it does. | "
    "CT_PEAKER / CT_CHP -- the half that had no mechanism. A simple-cycle peaker's published "
    "net-summer rating already IS its hot-day capability; charging it a further 12.5 % made MISO's "
    "peakers look scarcer in exactly the hours they are dispatched, and CT_PEAKER carried both the "
    "largest measured rating gap and the largest idle headroom. | "
    "COAL_PRB / COAL_BIT -- the displaced. With CC capability restored, coal steps back down the stack "
    "in summer afternoons (2023 COAL_PRB -1.24 TWh). MISO's real summer margin is set by gas far more "
    "often than the model had it; this moves the marginal fuel toward reality in the hours that set "
    "the price. | "
    "import -- also displaced (-1.05 TWh in 2023). The model had been buying at the seam what its own "
    "CC fleet should have been generating -- a substitution the seam's real economics do not support "
    "on a summer afternoon. | "
    "ST_GAS -- displaced at the margin (-0.81 TWh), which raises its FORCED share (+2.4 / +2.8 / +3.7 "
    "pp) without any new forcing: the floors are unchanged and it is the economic half of its energy "
    "that leaves. That is a ratio moving because the denominator fell, not a class being propped up. | "
    "WHAT THIS KEEPER DOES NOT CLAIM: the repair makes the price gates WORSE (C3a worse in all three "
    "years, C3b-2025 through its gate). It is kept because removing a measured double count is right, "
    "not because it scores better -- and the remaining 2025 level miss is now one compensating error "
    "closer to its real root cause."
)


def main() -> None:
    shard = json.loads(SHARD.read_text())
    prior = shard["keeper"]
    shard["keeper"] = KEEPER_ID
    shard["promotion_note"] = PROMOTION_NOTE
    shard["note"] = OWN_DELTA + "\n\n" + shard["note"]
    SHARD.write_text(json.dumps(shard, indent=1) + "\n")

    side = json.loads(SIDECAR.read_text())
    side["market_story"] = MARKET_STORY
    SIDECAR.write_text(json.dumps(side, indent=1) + "\n")

    print(f"keeper {prior} -> {shard['keeper']}")
    print(
        f"promotion_note {len(PROMOTION_NOTE)} chars; note {len(shard['note'])} chars"
    )
    print(f"market_story {len(MARKET_STORY)} chars -> {SIDECAR.name}")


if __name__ == "__main__":
    main()
