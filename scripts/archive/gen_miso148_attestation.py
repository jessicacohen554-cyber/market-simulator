"""Write the miso-148 calibration attestations (control + arm).

Both bundles are ``replay_keeper`` re-solves of the MISO keeper
``2026-08-05-miso-132b-cc-committed``'s own ``meta.json`` at this session's HEAD,
``--year 2023 2024 2025`` in ONE invocation each, years sequential inside the
invocation (rules 12 / 16). The CONTROL carries ZERO deltas; the ARM changes
EXACTLY ONE ``ScenarioConfig`` field, ``summer_derate_basis_aware=true``,
applied through the generic ``prb_overrides`` channel and recorded verbatim in
``run_config.json`` (rule 24 [R-REGISTRY]).

The DOF ledger, disclosures and exceptions are inherited from the keeper's own
attestation — the arm adds ZERO free parameters (a boolean over a data
predicate), so the ledger gains one entry whose identification is *structural*,
never *residual*, and the residual count is unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results" / "calibration" / "miso132_ccmin_B"
CONTROL = REPO / "results" / "calibration" / "miso148_basis_A"
ARM = REPO / "results" / "calibration" / "miso148_basis_B"

_COMMON = (
    "miso-148, 2026-08-09. PREREG "
    "results/calibration/PREREG-miso148-cc-availability-summer-basis-2026-08-09.md "
    "pushed at 456b376 (blob bd0a0a97, 420 lines, verified against the FETCHED "
    "remote ref) BEFORE any adjudicating statistic. Both arms are replay_keeper "
    "re-solves of the 2026-08-05-miso-132b-cc-committed keeper's own meta.json at "
    "this session's HEAD, --year 2023 2024 2025 in ONE invocation each, years "
    "sequential (rules 12 / 16). Rule 22: no year outside 2023-2025 was solved, "
    "scored or registered; MISO holds no calibration-complete marker in either "
    "block. "
    "K0 IS REPORTED AS FAILED AS WRITTEN, NOT REDEFINED: the zero-delta CONTROL "
    "does NOT reproduce the committed keeper's class-hour sidecars (max |delta| "
    "912.5 MW; total absolute class drift 0.54 / 0.14 / 0.46 TWh on ~500 TWh of "
    "annual dispatch, ~0.1 %, largest single class ST_GAS +0.25 TWh against C1's "
    "+/-8 TWh tolerance). CAUSE: HEAD drift since the keeper's own solve "
    "(git_sha 6b05f058, 2026-08-05) — that sha is NOT reachable in this shallow "
    "clone, an instrument limit disclosed rather than papered over, but ~20 "
    "commits touched src/market_sim in the window, at least one backfilling "
    "unit_outage_lp_capacity_basis, which MISO's historic outage overlay "
    "consumes. PROVEN NOT TO BE THIS SESSION'S EDITS, by measurement rather than "
    "assertion: the drift's FULL magnitude appears in non-summer hours of "
    "non-gas classes (7,232 nonzero cells in 2025 alone) — a region "
    "summer_derate_basis_aware cannot reach even when ARMED, and the flag is OFF "
    "in the control, where the off path is identical by construction. "
    "CONSEQUENCE, stated plainly: the A/B remains interpretable because BOTH "
    "arms run at the SAME HEAD and every quoted delta is arm-vs-CONTROL; NO "
    "arm-vs-keeper delta is quoted anywhere. A separate governance observation "
    "for the owner: MISO's designated keeper is not bit-reproducible at HEAD."
)

CONTROL_NOTE = "CONTROL — ZERO DELTAS (scripts/replay_keeper.py, no --set). " + _COMMON

ARM_NOTE = (
    "ARM — EXACTLY ONE MECHANISM CHANGES: summer_derate_basis_aware=true. "
    + _COMMON
    + " "
    "WHAT THE MECHANISM IS, and why it is a rule-14 [R-ACCURATE] correction "
    "rather than a lever. The flat _SUMMER_CLASS_DERATE (CC 10 %, CT 12.5 %) "
    "represents the NAMEPLATE -> SUMMER-PEAK AMBIENT loss, so it is applicable "
    "only to a unit whose LP capacity is carried on a NAMEPLATE basis. On MISO's "
    "per-plant EIA-860 path (plant_level_fleet) pmax IS the published net-summer "
    "rating, which already embeds that loss, so re-applying it is a DOUBLE "
    "COUNT — miso-141 measured the base (net-summer for 100 % of matched "
    "CT_PEAKER / CT_CHP / CC_CHP capacity) and the size (clean nameplate->summer "
    "gaps of 11.40 / 14.34 / 16.35 / 15.25 % by class, against a flat derate of "
    "the same magnitude re-applied on top), and REFUTED the 'incremental ambient "
    "loss' reading on MISO's own slopes and weather (the honest incremental is "
    "an UPRATE of ~2 % CC / ~3.7 % CT; sign inverted in 18 of 18 zone-years). "
    "When armed the flat derate is applied ONLY to units still on a nameplate "
    "basis and suppressed for units already carrying a measured summer "
    "capability, per plant. ZERO CONTINUOUS DEGREES OF FREEDOM (rule 21): a "
    "boolean over a data predicate, with no tunable fraction, per-class scale or "
    "sweepable tolerance — and no parameterised variant was built or solved, "
    "because that would be a channel for fitting the residual. "
    "RULE 19 [R-ONE-MECH]: every mechanism that already derates MISO CC was "
    "enumerated from source before this was built (statistical POF + WEFOR; "
    "wefor_multiplier / wefor_residual, both inert on this keeper; the CAMPD "
    "historic outage overlay incl. short windows and maxgen events; "
    "BIN_FORCED_DERATE_BY_YEAR; the flat derate itself; temp_dependent_derate, "
    "mean-anchored on CT_CHP/ST_CHP so it is a reshape that never touches CC; "
    "gt_ambient_derate, measured PROVABLY INERT for MISO; cc_capacity_reconcile; "
    "the COD ramp). This REPLACES the flat derate's application where the basis "
    "already carries it — it does not stack a second derate — and it is a PURE "
    "basis correction: no POF drop, no age-derate drop, no WEFOR change, no "
    "capacity rescale, and NO off-summer leg (that is a separate defect with its "
    "own mechanism, cc_winter_capability_basis, and MISO's measured Oct-Mar CC "
    "availability headroom is POSITIVE, so no evidence asks for it). "
    "CORRUPT-FILING TREATMENT, explicit rather than by silent clamp (miso-141 "
    "§11.2(c)): plants whose EIA-860 filing puts summed net-summer above summed "
    "nameplate are clipped by the always-on CC guard onto max(nameplate, "
    "demonstrated_peak) — a nameplate-like basis — so they KEEP the flat derate, "
    "as do plants absent from EIA-860. Measured on the real 2025 fleet: 86.9 % "
    "of flat-derate MW admitted, 7,255 MW across 9 CC and 4 CT plants kept. The "
    "predicate reads the guard's OWN recorded decision rather than re-deriving "
    "it from the raw sheet, because the plant-total-on-one-row pattern hides "
    "behind NaN component rows the loader nameplate-fills — 55380 and 55467 read "
    "'clean' on the raw sheet while the loader clips them by 1,028.6 and 353.3 "
    "MW. A re-derived predicate walked straight into that trap during this "
    "session and was replaced; reported against interest. "
    "DIRECTION DISCLOSED IN ADVANCE AND AGAINST INTEREST (PREREG §6 P5, stated "
    "before any solve): the repair ADDS summer capability, so its price effect "
    "is DOWNWARD — the wrong way for a MISO 2025 already -14.1 % low on C3a. It "
    "is filed as rule-14 hygiene and NEVER as progress against the level miss, "
    "and the charter's against-interest bound is restated as binding: 2023 "
    "carries nearly the same CC gap as 2025 and C3a-2023 PASSES, so the "
    "composition defect never predicted closing 2025's -14.1 %."
)

_DOF_ENTRY = {
    "name": "summer_derate_basis_aware",
    "where": "run_config.scenario_config.summer_derate_basis_aware",
    "identification": "measured-physical",
    "lineage_solves": "1 (this arm; no sweep, no variant)",
    "value": True,
    "note": (
        "ZERO CONTINUOUS DOF — a boolean over a data predicate, not a fitted "
        "value. The predicate is 'is this plant's carried pmax already a "
        "measured summer capability?', answered from published EIA-860 ratings "
        "plus the always-on CC guard's own recorded clip decision. Nothing in "
        "it is tunable: there is no derate fraction, no per-class scale and no "
        "sweepable tolerance, so there is no channel through which a residual "
        "could enter. Rule 13/14 forward story: the predicate regenerates for "
        "any forward EIA-860 vintage and responds to re-rates. Identified "
        "against miso-141's measurement of the capacity BASIS (which quantity "
        "pmax is), never against any price or volume residual."
    ),
}


def _build(note: str, armed: bool) -> dict:
    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att["governance"] = dict(att["governance"])
    att["governance"]["attested_by"] = note
    if armed:
        fp = att["free_parameters"]
        fp["entries"] = list(fp["entries"]) + [_DOF_ENTRY]
        fp["n_entries"] = len(fp["entries"])
        # n_residual is UNCHANGED: the new entry is structural, not residual.
    att["disclosures"] = {
        "note": (
            "miso-148 disclosures, reported rather than patched. "
            "(a) K0 FAILED AS WRITTEN — see governance.attested_by; the gate is "
            "reported failed and its cause measured, not redefined to pass. "
            "(b) A PRE-REGISTERED GATE FIRED ON A BOUNDARY IT COULD NOT SEE, "
            "AND THE INSTRUMENT WAS REPAIRED RATHER THAN THE VERDICT REINTERPRETED. "
            "G-L2a's first implementation compared CAMPD CC plants against model "
            "CC-CLASS plants only — narrower than the gate's own pre-registered "
            "wording ('no model counterpart') — and returned branch B-2 "
            "population_defect on 1,466-1,542 MW. Three of the four plants ARE "
            "carried by the model, under CT_CHP / ST_CHP / CT_PEAKER: they are "
            "industrial cogen (1391 Louisiana 1, 50625 ExxonMobil Beaumont) whose "
            "host steam is held out behind the meter, plus 1404 Sterlington, a CC "
            "unit that never ran (peak 0 MW). Corrected to the pre-registered "
            "wording the quantity is ONE plant, 55120 SRO Cogen — itself a "
            "cogen, and absent from EIA-860 entirely — at 484-490 MW, BELOW the "
            "1,000 MW bar, so the branch is B-1 basis_explained and L1 proceeded. "
            "(c) MERCHANT CC RATING IS SOUND BUT DRIFTS: model pmax vs CAMPD p99 "
            "net reads -0.06 GW (-0.21 %) in 2023, -0.54 (-1.96 %) in 2024 and "
            "-1.66 GW (-6.0 %) in 2025; the CHP boundary gap is stable at -2.8 GW "
            "in every year, by design. "
            "(d) AN L2 DATA DEFECT IS REPORTED, NOT REPAIRED, because its fix is "
            "cross-ISO and belongs to its own lane: 2025 has no vintage_2025/ "
            "EIA-860 directory, so the fleet falls back to the canonical (2025 "
            "Early Release) sheet, which re-flags rows OA (standby). The operable "
            "loader carries OP only, and the mechanism BUILT for exactly this "
            "case — load_mothballed_but_operating, armed on this keeper via "
            "carry_operating_mothballs — returns [] because its vintage_<year> "
            "precondition is unmet. 9 rows / 594.7 MW that were OP in "
            "vintage_2024 are dropped from the 2025 fleet, 576.2 MW of it "
            "Cottonwood Energy (55358), which CAMPD shows generating 4.70 TWh at "
            "p99 1,140 MW in that same year. Model availability below observed "
            "generation is indefensible for any outage input, so this is a "
            "standing rule-14 item for the 2025 fleet of EVERY ISO, not MISO's "
            "alone. "
            "(e) THE SUMMER HOLE IS CLOSED; THE S1 HOLE IS NOT. Measured "
            "fleet-side (no LP): monthly AV_CC - A_CC in Jun-Sep 2025 moves from "
            "-2,296 / -2,451 / -2,157 / -1,560 MW to -373 / -369 / -77 / +419 MW, "
            "but the S1 high-price stratum's deficit only closes from -2,614 to "
            "-1,755 MW. S1 spans all twelve months, and its non-summer half is "
            "the commitment/displacement object miso-147 §4 named — L3, "
            "OBSERVATION ONLY this session and deliberately not armed. The "
            "monthly levels here are this probe's own construction and differ "
            "from miso-147's committed table by ~200 MW; the A/B DELTA is the "
            "quantity, measured on one construction throughout, and miso-147's "
            "own table was separately reproduced with ZERO diffs (G-F)."
        )
    }
    return att


def main() -> None:
    for bundle, note, armed in (
        (CONTROL, CONTROL_NOTE, False),
        (ARM, ARM_NOTE, True),
    ):
        att = _build(note, armed)
        out = bundle / "calibration_attestation.json"
        out.write_text(json.dumps(att, indent=1) + "\n")
        print(
            f"wrote {out.relative_to(REPO)} "
            f"(dof entries {att['free_parameters']['n_entries']}, "
            f"residual {att['free_parameters']['n_residual']}, "
            f"exceptions {len(att['exceptions'])})"
        )


if __name__ == "__main__":
    main()
