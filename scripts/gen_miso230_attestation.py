"""Generate the miso-230 CT-drag + seam PAIR candidate's calibration attestation.

miso-230 is a **KEEPER CANDIDATE** built on the designated keeper's own recipe
(``2026-09-05-miso-220-nonsteam-lift``) with **two** added ``ScenarioConfig``
deltas, applied together because the owner's standing decision of 2026-09-06
names the pair: *fix CT_PEAKER, then promote the seam pair.*

  1. ``ct_netload_drag=true`` with MISO's OWN derived curve and window
     (0.01303 / -0.8108 / 0.4394 over ``[10, 21)`` CST) — the root-cause fix for
     the CT_PEAKER cell that sent miso-227 to NOT-YET.
  2. ``miso_seam_neighbour_anchored_ladder=true`` — the miso-227 seam arm,
     unchanged, which could not promote alone on that cell.

The attestation exists so the arm can be SCORED: ``replay_keeper`` writes none,
and without one the C6 governance gate reads UNATTESTED, guard (b) of the C3c
standing rule blocks reclassification, and C3c scores FAIL on values identical
to the keeper's — the miso-200 vacuous-pass trap, hit at miso-217 §5 and closed
in advance at miso-220 and miso-227.

**Everything the keeper attested about ITS OWN levers is carried forward
unchanged**: this candidate IS the keeper recipe plus two fields, so the
miso-220 x1.10 non-steam offer lift is still in it and its
``authorized_price_tuning`` block and two FALSE governance assertions are copied
verbatim rather than re-litigated or quietly improved.

**No new ledger entry and no new parameter.** The drag's five coefficients are
statistics of measured CAMPD + EIA-930 data under a pre-specified estimator
(``scripts/data/derive_miso_ct_netload_drag.py``, rule 23 frozen), and the
seam ladder is a measured table from a frozen derive. ``n_entries`` stays 41 and
``n_residual`` 2.

Usage:
    python3 scripts/gen_miso230_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "results/calibration/miso220_nonsteamlift_B/calibration_attestation.json"
ARM = REPO / "results/calibration/miso230_ctdrag_seam_K"

DRAG_DISCLOSURE = (
    "DELTA 1 — ct_netload_drag=true on MISO's OWN derived curve and window. The "
    "floor is clip(0.01303*netGW - 0.8108, 0, 0.4394) x available capacity, gated "
    "to [10, 21) local standard (CST), on every non-_peak CT_PEAKER tranche. "
    "WHY IT IS ADMISSIBLE (rule 13 [R-MEASURED], rule 17 [R-FLOOR-WINDOW]): both "
    "the TRIGGER (system net load) and the MAGNITUDE (a physical min-gen) "
    "regenerate for a forward year from a load forecast and a wind/solar build, "
    "and respond to changed conditions - more VRE lowers net load and therefore "
    "the drag. It is explicitly NOT ct_mustrun_per_plant, which floors each plant "
    "at its OBSERVED EIA-923 net generation (rule 13's named forbidden case) and "
    "is D-9 QUARANTINED, machine-asserted False; that lever was REFUSED at "
    "miso-228/229 and is not revived here. "
    "RULE 25 [R-ISO-SCOPE] ON BOTH AXES: PJM's ESTIMATOR is carried "
    "(derive_pjm_ct_netload_drag.py's pure-play plant selection, CF denominator, "
    "2-GW binning and exact-grid-search hinge), and NONE of its numbers - nor "
    "ERCOT's [15, 22) WINDOW, which is justified by a solar-collapse evening ramp "
    "MISO does not have. MISO's midday block is as strongly driven as its evening "
    "(miso-229: rho 0.743/0.691/0.734 vs 0.706/0.636/0.743), so the window was "
    "DERIVED by a rule with ZERO free parameters: the maximal contiguous run of "
    "hours whose pooled mean CF is at or above the fleet's OWN 24-h mean CF "
    "(0.0850) with positive rho(CF, net load). Result [10, 21); re-derived "
    "independently per year by the same rule it reads [9,21)/[10,21)/[11,22), "
    "stable to +/-1 h. "
    "ZERO FITTED SCALARS: every coefficient is a statistic of measured CAMPD + "
    "EIA-930 data under a pre-specified estimator, none identified against a "
    "price or volume residual; the derive is rule-23 frozen and re-derives only "
    "when its source data updates. The floor sits at ~half the measured class "
    "energy (8.406/7.311/7.469 vs 15.037/13.791/14.804 TWh), which is what "
    "distinguishes a minimum from an actuals pin. "
    "RULE 19 [R-ONE-MECH] - REPLACE, NOT STACK, AND IT IS MEASURED: MISO's "
    "reliability_floor already carried net-load-driven CT_PEAKER limbs in all six "
    "zones and the keeper's D-2 attributed 100 % of CT forcing to them. "
    "drop_drag_owned_reliability_specs removes exactly those limbs; the zero-LP "
    "phase 0 measured 18 limbs dropped and reliability_floor x CT_PEAKER going "
    "2.6231 -> 0.0000 TWh, and this bundle's own D-2 confirms ct_netload_drag is "
    "the SOLE CT_PEAKER forcing mechanism in all three years."
)

SEAM_DISCLOSURE = (
    "DELTA 2 — miso_seam_neighbour_anchored_ladder=true, the miso-227 arm "
    "UNCHANGED. Band k of the PJM seam is priced at the quantile of the PJM "
    "WESTERN-BORDER DA whose exceedance duration equals the measured duration of "
    "the seam flowing deeper than the band's midpoint - byte-for-byte the "
    "incumbent Q-Q construction, the ONLY change being which measured price "
    "series the coupling reads. The owner ruled on 2026-09-06 that an import is "
    "offered at the exporting market's own measured price and that this is the "
    "ONE admissible form of the D-2 5(i) object. ZERO fitted scalars; PJM seam "
    "only, a DATA boundary (no measured SPP or SOCO/TVA price series is held "
    "under data/raw), not a choice. "
    "ITS PRE-COMMITTED NON-CLAIM STANDS UNCHANGED (miso-226/227 PREREG §1, §5): "
    "this form repairs the ladder's ANCHOR and leaves its frozen-annual-quantile "
    "SHAPE, so it moves the seam's LEVEL and not its RESPONSIVENESS - "
    "corr(imports, own price) +0.750 -> +0.725 against a MEASURED -0.101, 3 % of "
    "the distance. NO CLAIM is made that the seam is repaired."
)

PAIR_DISCLOSURE = (
    "WHY THE TWO ARE ARMED TOGETHER, and the rule-19 reading of that: they are "
    "not two mechanisms for one phenomenon. The drag is CT_PEAKER commitment; the "
    "seam is import band pricing. They are paired because the OWNER's standing "
    "decision of 2026-09-06 says so - miso-227 solved the seam full-span and "
    "scored NOT-YET on ONE load-bearing cell, CT_PEAKER-2023 at -8.29 TWh against "
    "a +/-8.00 band, so the seam cannot promote alone and the owner directed: fix "
    "CT_PEAKER, then promote the pair. "
    "THE CELL WAS NOT THE SEAM'S FAULT and this is stated against the pair's own "
    "interest: the keeper misses CT_PEAKER by 5.4-8.0 TWh in EVERY year and sat "
    "0.015 TWh inside the band, so MISO's CALIBRATED status hinged on 0.19 % of a "
    "band on a cell wrong by eight; the seam added 0.30 TWh to a 7.99 TWh "
    "pre-existing miss. "
    "SEQUENCING (rule 29 [R-SCREEN]): a zero-LP phase 0 ran first and measured "
    "the rule-19 replacement and a +3.6544 TWh pre-solve lift prediction; the "
    "drag was then SCREENED ALONE on ONE year (2023, named on the mechanism's own "
    "FOOTPRINT before the solve, not on any residual) and cleared five "
    "pre-registered STOP-only gates, with the realized lift +3.948 TWh = 1.08x "
    "the prediction. Only then was the full span spent. The screen bundle was "
    "DELETED before merge (rule 29(c)); PRECOMMIT-miso230-ct-netload-drag-"
    "2026-09-06.md and _miso230_screen_gates.json carry every number."
)

D4_DISCLOSURE = (
    "A SCORING-PATH CHANGE THIS SESSION MADE, DECLARED BECAUSE IT IS ONE. "
    "D4_WINDOWS declared (MECH_CT_NETLOAD_DRAG, None): (15, 22) GLOBALLY - "
    "ERCOT's solar-collapse window. Scoring MISO's derived [10, 21) against it "
    "would have counted h10-h14, which carry 1,744-2,359 MW of mean floor and are "
    "the largest part of the footprint, as OFF-WINDOW binding - i.e. would have "
    "failed the drag for binding in exactly the hours MISO's own driver evidence "
    "says it should. This session added D4_WINDOWS_BY_ISO + resolve_d4_windows "
    "and declared MISO [10, 21) with the measured evidence cited in place. "
    "GUARDS: it is a NO-OP for every other ISO (resolve_d4_windows returns "
    "D4_WINDOWS itself when an ISO has no override; ERCOT still reads (15, 22)) "
    "and for every registered run (the MISO keeper arms no drag, so the row "
    "carries zero floored energy and is skipped) - NO committed bundle's score "
    "moves. It was PUSHED BEFORE THE SOLVE, with the window fixed by the derive's "
    "zero-DOF rule, so it could not be re-chosen after seeing a gate. Like every "
    "windowed row in that registry it is a rule-12/17 DECLARATION and not an "
    "escalation path: the drag is zero outside its configured window BY "
    "CONSTRUCTION (apply_netload_reliability_floor's ramp_window gate), so an "
    "off-window bind is structurally impossible. 117 tests pass."
)

REPORTED_AGAINST = (
    "REPORTED AGAINST THIS CANDIDATE, at full magnitude. "
    "(a) D-1 diurnal shape REGRESSES ON COAL: the keeper carries ONE D-1 FAIL "
    "(COAL_PRB 2025, cv_ratio 0.388); this pair carries FOUR (COAL_PRB 0.488 / "
    "0.492 / 0.389 across 2023-2025 and COAL_BIT 2024 at 0.387), from coal "
    "displaced by the CT floor. These rows do NOT gate - rule 18's shape leg "
    "binds only for a class ABOVE its forced cap and COAL sits at ~0.3 % forced "
    "against a 30 % merchant cap, and the standalone C7 diurnal-shape gate was "
    "RETIRED by the rubric v3.1 owner amendment - but three of the four are NEW, "
    "they are a real structural side-effect of this arm, and two sit within 0.012 "
    "of the line. They are recorded here rather than left to be discovered. "
    "(b) CT_PEAKER FORCED SHARE RISES STEEPLY: 26.5/18.3/15.3 % -> 49.2/31.2/"
    "34.0 %, far above rule 18's 15 % peaker cap, so C8 passes ONLY through the "
    "grounded conditional route. That route is earned on the merits and measured "
    "in this bundle - D-4 off-window share is 0.0000 in all three years against "
    "MISO's own declared window, and the class's D-1 shape IMPROVES (profile_r "
    "0.935/0.962/0.982 -> 0.975/0.984/0.983, cv_ratio 1.335/1.119/1.395 -> "
    "1.792/1.566/1.738) - but the honest statement is that this arm makes the "
    "fleet's largest forced share substantially larger. "
    "(c) C3a-2025 moves AWAY from actual (-7.0 % -> -8.4 %, still inside the "
    "+/-10 % band) while 2023 and 2024 move toward it (+7.2 -> +5.0, +3.4 -> "
    "+2.0 %). "
    "(d) CC_REGULAR-2023 moves 1.87 TWh further from actual (-4.17 -> -6.05) - "
    "the energy-balance counterpart of the CT lift, inside band. "
    "(e) C3c is UNCHANGED, not improved: tail hours 3/7/0 in both bundles, "
    "byte-identical, so the ledgered C3c caveat is carried forward untouched and "
    "this run makes NO scarcity-pricing claim. "
    "(f) 2024 slack is 0.0196 TWh in BOTH bundles - PRE-EXISTING in the keeper, "
    "not introduced here, though it is spread over 9 zone-hours rather than 7."
)


def build(dst: Path) -> None:
    """Copy the keeper's attestation onto the candidate, restamped and disclosed."""
    d = json.loads(SRC.read_text())
    d["governance"]["attested_by"] = (
        "miso-230 KEEPER CANDIDATE (2026-09-06) under the OWNER's standing decision "
        "of 2026-09-06 ('fix CT_PEAKER, then promote the seam pair') and the same "
        "day's rule-1 [R-STRUCT] steer ('if structural integrity improves but gates "
        "regress that may still be a keeper'): control = the miso-220 keeper bundle "
        "miso220_nonsteamlift_B itself (already attested, never re-solved, rule "
        "29(b) form 4, G-DRIFT 4545300d..HEAD ALL INERT with every backcast-path "
        "hunk classified in PRECOMMIT §5, extended over main's later 52 commits "
        "which are forecast-path or a no-op cache-key fingerprint) vs arm "
        "miso230_ctdrag_seam_K, MISO 2023+2024+2025 in ONE invocation, years "
        "sequential, solved in-session and never on CI (rules 12/16), from the SAME "
        "committed keeper recipe via replay_keeper --set on TWO ScenarioConfig "
        "fields. No new ScenarioConfig field minted (ct_netload_drag long predates "
        "this session; miso_seam_neighbour_anchored_ladder was minted by miso-225), "
        "no new matrix row owed - ct_netload_drag is already registered in the "
        "netload_drag_floors row - and the DOF ledger is unchanged at 41/2. This "
        "attestation certifies the run's PROVENANCE, not that its gates pass."
    )
    dis = d.setdefault("disclosures", {})
    dis["miso230_ct_netload_drag"] = DRAG_DISCLOSURE
    dis["miso230_seam_neighbour_anchor"] = SEAM_DISCLOSURE
    dis["miso230_why_paired"] = PAIR_DISCLOSURE
    dis["miso230_d4_window_declaration"] = D4_DISCLOSURE
    dis["miso230_reported_against_the_candidate"] = REPORTED_AGAINST
    dis["miso230_inherited_governance_scope"] = (
        "governance.no_fit_to_price_residuals and levers_trace_to_measured_input are "
        "carried forward FALSE from the miso-220 keeper WITHOUT change. They describe "
        "the INHERITED x1.10 non-steam offer lift, which this candidate still carries "
        "unmodified, not this session's two deltas. BOTH of this session's deltas "
        "assert both flags positively on their own terms - each is a measured table "
        "or a measured-data statistic from a rule-23 frozen derive with zero fitted "
        "scalars, selected by driver evidence and an owner ruling, never against a "
        "residual and never swept - but the flags are not flipped to true because the "
        "run AS A WHOLE does not earn that claim while the inherited lift is in it. "
        "authorized_price_tuning is likewise copied verbatim: same channel, same "
        "x1.10, same three years, same PREREG citation."
    )
    dst.write_text(json.dumps(d, indent=1))
    print(
        f"wrote {dst.relative_to(REPO)} "
        f"(n_entries={d['free_parameters']['n_entries']}, "
        f"n_residual={d['free_parameters']['n_residual']})"
    )


if __name__ == "__main__":
    build(ARM / "calibration_attestation.json")
