"""Write ``calibration_attestation.json`` for the caiso-148 keeper candidate.

The caiso-148 arm is the caiso-147 keeper recipe with ONE delta —
``nuclear_unit_availability=true`` on CAISO's own newly-derived NRC artifact —
so this attestation is the caiso-147 keeper's attestation with:

1. a rewritten ``governance.attested_by`` describing the single delta,
2. the caiso-145 **owner** exception ledger **CARRIED FORWARD UNCHANGED IN
   SUBSTANCE**, with each entry's ``magnitude`` re-measured on this bundle, and
3. one new DOF-ledger entry for the mechanism, identification ``measured``.

**On carrying the ledger forward.** The three exceptions were adopted by the
owner at caiso-145 (2026-07-30) — two caveats over three rows: C3c-2023 and
C3c-2024 on caiso-131 §9 disposition A4 with the caiso-144 evidence, and
C3a-2025 on the caiso-141 A2 data wall. This session creates **no new caveat and
spends no new ledger slot**: it re-states the owner's own dispositions against a
bundle whose measurements for both are materially unchanged (C3c is
**bit-identical** — model 0 h in every year of both arms; C3a-2025 stays at
**+11.2 %**, the CA load-weighted λ moving $38.2331 → $38.2506, i.e. **0.0 pp**
against the 1.0 pp materiality trigger the caiso-148 prereg §7 fixed in
advance). Each carried entry records its provenance explicitly so the owner's
act stays attributable and is never mistaken for a fresh grant by this session.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/gen_caiso148_attestation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

SOURCE = REPO / "results/calibration/caiso147_chp_B/calibration_attestation.json"
TARGET = REPO / "results/calibration/caiso148_nucavail_B/calibration_attestation.json"

ATTESTED_BY = (
    "caiso-148 measured per-reactor nuclear availability keeper session "
    "2026-07-31. SINGLE-flag delta on the caiso-147 measured-CHP-heat-rate keeper "
    "recipe: nuclear_unit_availability=true (rule 19 [R-ONE-MECH] — one mechanism, "
    "nothing stacked). ZERO new free parameters, fitted or otherwise (rule 24): the "
    "applied series is CAISO's own artifact, data/raw/nuclear-availability-CAISO.csv, "
    "written by scripts/data/derive_nuclear_availability.py --iso CAISO at this "
    "session's HEAD. NO SOURCE CHANGE WAS NEEDED TO ARM CAISO — the application seam "
    "(data/fleet/arrays.py, the _iso != 'ERCOT' block) and the loader "
    "(data.outages.nuclear_unit_availability_series) were already ISO-generic; the "
    "session's ONLY code delta is a two-row identifier crosswalk in the deriver's "
    "NRC_TO_EIA map ('Diablo Canyon 1' -> (6099, 1), 'Diablo Canyon 2' -> (6099, 2)), "
    "which is an identifier map, not a tunable. The deriver's constants "
    "(EVENT_RAW_MAX 0.90, SCALE_CLIP 1.25, WEDGE_TOL 0.01) are inherited FROZEN from "
    "the ERCOT deriver and were not touched (rule 23 [R-FROZEN-DERIVE]); the PJM and "
    "NYISO extracts reproduce BYTE-FOR-BYTE after the CAISO addition (rule 25 "
    "[R-ISO-SCOPE] — no other ISO's artifact moves, and neither ERCOT's nor NYISO's "
    "K verdict transfers anything here). "
    "WHAT IT REPLACES (rule 14 [R-ACCURATE]): NUCLEAR_MONTHLY_CF_BY_YEAR['CAISO'] "
    "carries the measured EIA-923 monthly fleet energy but SMEARS it uniformly across "
    "both reactors and every hour of the month, so a unit-specific refuel or trip is "
    "invisible inside the month. The overlay keeps that monthly LEVEL (the EIA-923 "
    "anchor owns the level) and replaces the TIMING with the measured per-reactor "
    "daily state from the NRC daily Power Reactor Status Report — the anchor owns the "
    "level, NRC owns the timing. Uncovered dates are NaN and keep the smear. "
    "RULE 13 [R-MEASURED] ADMISSIBILITY: a reactor power state / refuel window is a "
    "physical availability event — the same class as the CAMPD fossil outage windows "
    "and the ERCOT/NYISO nuclear overlays. It is an INPUT, never a measured outcome "
    "fed back to close a residual: it regenerates forward from the static "
    "NUCLEAR_MONTHLY_CF + refuel-block scheduling and responds to changed conditions. "
    "Nothing in it is keyed to a price or volume residual. "
    "EX-ANTE WALL CHECK (the handoff's first requirement, and the reason queue item 5 "
    "cost no solve): nuclear_unit_availability shares NO input and NO detector with "
    "unit_outage_short_windows, which caiso-136 adjudicated INERT on a coal-only CEMS "
    "detector meeting a CEMS-invisible CAISO coal class. Nuclear units carry no CO2 "
    "and are not CEMS reporters in ANY ISO, so CEMS visibility is structurally "
    "irrelevant to this lever everywhere. caiso-136 has no bearing on item 8. "
    "COVERAGE: 1,886 rows / 2 reactors — Diablo Canyon 1 (EIA 6099_1, 1,122 MW) and 2 "
    "(6099_2, 1,118 MW), zone NP15, 2,240 MW = 100 % OF CAISO'S NUCLEAR CAPACITY AND "
    "UNIT COUNT (SONGS 2/3 retired 2013, Rancho Seco 1989; neither carries an NRC row "
    "nor a fleet unit). NRC reports both reactors on 365/366/365 days — no source "
    "gaps. 18 windows in the covered extract, including three refuels (DCPP-1 "
    "2023-09-27..11-17, DCPP-2 2024-04-07..05-25, DCPP-2 2025-10-05..10-31). Covered "
    "days 365/365 (100 %), 366/366 (100 %), 212/365 (58.1 %); 31 of 36 months. "
    "THE FIVE DROPPED MONTHS ARE ALL 2025 AND THE DROP IS CORRECT, NOT A DATA WALL "
    "AND NOT A FIT CHOICE: each holds a real event whose non-event pool is already "
    "saturated at 100 %, so the capped fixed-point cannot scale UP to a clipped-at-1.0 "
    "anchor. This session MEASURED the cause rather than assuming it — EIA-930 CISO "
    "NG:NUC peaks at 2,281/2,279/2,309 MW against the model's 2,240 MW EIA-860 "
    "nameplate, i.e. Diablo runs up to +3.1 % ABOVE nameplate, so a full-power month's "
    "EIA-923 ratio (net gen / nameplate x hours, clipped at 1.0 by its own "
    "construction) hits the clip and NRC-%thermal x nameplate can never express it. "
    "Posting the NRC level there would DELETE REAL CAPABILITY, so the deriver drops "
    "the month and the smear stands — rule 14's misalignment clause operating as "
    "designed. Consequence, stated in the prereg BEFORE either arm solved and not "
    "engineered around: in 2025 the U1 Apr-May refuel, the Jul U2 derate and the Dec "
    "U1 trip keep the smear; only the October U2 refuel carries measured timing. "
    "INDEPENDENT-SOURCE VALIDATION against EIA-930 CISO metered hourly nuclear — a "
    "source independent of BOTH the NRC timing input and the EIA-923 level anchor: "
    "NRC-derived available MW vs metered daily mean over 942 fully-covered days gives "
    "r_day 0.9807 overall (0.9708/0.9918/0.9876), bias -1.8/+13.7/+20.0 MW on a "
    "2,240 MW fleet (<=0.9 %), MAE 43.2/28.7/36.2 MW (1.3-1.9 %). The nyiso-98 "
    "EIA-930 zero-block artifact was SCREENED FOR and does NOT occur in CISO (23 "
    "exact-zero hours in 2023, 0 in 2024 and 2025, against NYISO's 1,179/380/117), so "
    "nyiso-98's gap-masking step is not needed — a CAISO-specific determination that "
    "says nothing about any other ISO's 930 series. "
    "BUILD-TIME GATES (the nyiso-98 set) ALL PASS: G1 raw-NRC r_day lift "
    "+0.184/+0.145/+0.133 (gate >= +0.10); G2 reconciled retention of the raw lift "
    "100.1/100.2/100.1 % (gate >= 70 %; PJM's was NEGATIVE, which is why PJM's cell "
    "stays U); G3 max annual |dTWh| 0.0746 % (gate < 0.5 %). "
    "PRE-REGISTERED IN-SOLVE CHECKS (PREREG-caiso148-nuclear-availability-2026-07-31.md, "
    "committed and pushed BEFORE either arm solved) ALL PASS: R3 the overlay BINDS "
    "(4,368/3,672/2,232 hours move >1 MW, max |delta| 1,075/893/963 MW — not inert); "
    "R4 annual nuclear energy moves +0.0001/-0.0240/-0.0445 % (gate <= 0.5 % — the G3 "
    "gate holds in-solve, so the overlay posts TIMING, not a level); R1/R2 the extract "
    "reproduces and no other ISO's does; R5 no month the wedge fallback dropped is "
    "resurrected. S2 CLOSES IN EVERY YEAR and matches the extract prediction to four "
    "decimals: nuclear dispatch r_day vs EIA-930 metered goes 0.7873 -> 0.9709, "
    "0.8473 -> 0.9921, 0.8550 -> 0.9878 (lift +0.1836/+0.1448/+0.1327), MAE "
    "156.4 -> 47.2, 101.0 -> 31.3, 125.0 -> 39.9 MW. "
    "RESULT: EVERY CRITERION VERDICT IS IDENTICAL to the same-HEAD zero-delta control, "
    "criterion for criterion (C1/C2/C3b/C4/C7/C8 PASS, C3a and C3c unchanged, C6 "
    "UNATTESTED on both in the probe posture). The displaced energy is small and lands "
    "where expected: CC_REGULAR -85.6/-35.8/-13.8 GWh, imports +36.0/+31.7/+16.4, "
    "CT_PEAKER +46.1/+2.7/+6.0 GWh. System demand-weighted price moves "
    "+$0.015/-$0.036/+$0.018 per MWh with p99 essentially unchanged; 3,261/1,897/1,835 "
    "hours repriced. "
    "PROTECTIVE GATES HOLD, ON THE ABSORBING CLASSES (nuclear itself is exempt from "
    "BOTH C7 and C8 by explicit class list — D1_GATED_CLASSES omits it and "
    "D2_EXEMPT_CLASSES contains it — so per the caiso-147 §G binding framing NO "
    "nuclear D-1/D-2 number is quoted here as a passed gate): C7/D-1 CT_PEAKER "
    "profile_r 0.881/0.934/0.864 -> 0.881/0.933/0.866, all above the 0.80 floor, and "
    "2025 — the keeper's most exposed number — IMPROVES; cv_ratio "
    "1.623/1.817/2.178 -> 1.684/1.814/2.175. C8/D-2 CT_PEAKER forced share "
    "0.0016/0.0054/0.0007 -> 0.0015/0.0059/0.0007 against a 0.15 peaker cap. The "
    "ST_GAS 2024/2025 raw D-1 rows read FAIL in BOTH arms identically — pre-existing "
    "and not caused by this lever, and below the rubric's 2 % materiality floor, which "
    "is why C7 scores PASS. "
    "MATERIALITY (prereg §7): C3a moves +3.0 -> +3.0 %, +8.2 -> +8.1 %, "
    "+11.2 -> +11.2 % — max 0.1 pp against the 1.0 pp trigger fixed before the solve, "
    "so no leave-one-year-out re-scoring was required and the lever is NOT offered as "
    "a C3a or C3c lever. It closes neither ledgered caveat and was not selected to. "
    "CARRIED OPEN ITEM RESOLVED, NOT INHERITED: the keeper-reproducibility drift "
    "carried since caiso-146 (the caiso-139 keeper's committed sidecars diverging up "
    "to 3.2 GW on a class-hour at HEAD) does NOT affect the caiso-147 keeper. This "
    "session's zero-delta control reproduces the committed caiso-147 bundle "
    "BIT-EXACTLY — max |class-hour| delta 0.000 MW in all three years and CA "
    "load-weighted lambda identical to four decimals ($55.7916/$37.4222/$38.2331) — so "
    "caiso-147's re-basing onto HEAD closed it for CAISO. The drift's program-wide "
    "charter is unaffected; this is a CAISO observation only. "
    "WHAT THIS LEVER DOES NOT TEST (recorded so it cannot be mis-cited): the handoff "
    "framed Diablo as the 2,240 MW MSSC setting CAISO's entire reserve requirement. "
    "That is NOT how this keeper is wired — energy_reserve_coopt, caiso_reserve_coopt "
    "and as_reserve_formula are all False, and caiso_scarcity_pricing's MCL is a "
    "STATIC 1,400 MW tariff constant, not keyed to Diablo's hourly availability. There "
    "is NO dynamic MSSC channel in this A/B. The live channels are within-month "
    "re-timing (primary) and the caiso_scarcity_pricing overlay's reserve_headroom "
    "(second-order, via displaced gas loading). caiso-148 is not evidence about "
    "CAISO's reserve floor — it tested none."
)

#: Provenance stamp prepended to each carried exception's ``reason``.
CARRY = (
    "CARRIED FORWARD UNCHANGED from the caiso-147 keeper's ledger by caiso-148 "
    "(2026-07-31, single-flag nuclear_unit_availability delta). This session creates "
    "NO new caveat and spends NO new ledger slot — the disposition below is the "
    "OWNER's act of 2026-07-30 (caiso-145), re-stated against a bundle whose "
    "measurement for it is materially unchanged, with the magnitude field re-measured "
    "on this bundle's own bytes. ORIGINAL REASON FOLLOWS. "
)

#: Per-(criterion, year) magnitude re-measured on the caiso-148 arm-B bundle.
REMEASURED = {
    ("price_tail", 2023): (
        "model 0h [energy-only LMP] vs RT actual 47h (0.00x, >$200) — BIT-IDENTICAL "
        "to this session's same-HEAD zero-delta control AND to the caiso-147 keeper; "
        "the nuclear re-timing buys zero tail hours, exactly as the caiso-148 prereg "
        "§4 predicted in advance (an energy-neutral within-month re-arrangement "
        "cannot create a tail). "
    ),
    ("price_tail", 2024): (
        "model 0h [energy-only LMP] vs RT actual 35h (0.00x, >$200) — BIT-IDENTICAL "
        "to this session's same-HEAD zero-delta control AND to the caiso-147 keeper; "
        "the nuclear re-timing buys zero tail hours, exactly as the caiso-148 prereg "
        "§4 predicted in advance (an energy-neutral within-month re-arrangement "
        "cannot create a tail). "
    ),
    ("price_mean", 2025): (
        "model +11.2% vs RT actual $34.39 (band ±10%, so the overshoot beyond band is "
        "+1.2 pt), against this session's own same-HEAD zero-delta control at +11.2% "
        "and the caiso-147 keeper at +11.2%. The measured nuclear re-timing moves it "
        "0.0 pp — INSIDE the 1.0 pp materiality trigger the caiso-148 prereg §7 fixed "
        "before either arm solved, so no leave-one-year-out re-scoring was triggered "
        "and nothing was tuned toward this residual. Directly measured on this "
        "bundle's own sidecars, the CA load-weighted lambda moves "
        "$38.2331 -> $38.2506 (+$0.018); 2023 $55.7916 -> $55.8026 (+$0.011) and 2024 "
        "$37.4222 -> $37.3871 (-$0.035), both of which remain PASS. The mechanism is "
        "energy-neutral by construction (the EIA-923 anchor owns the level), so it "
        "moves the price level only through WHICH HOURS the reactors are available — "
        "which is the point. The caveat stands on the caiso-141 A2 data wall, "
        "unchanged. "
    ),
}

NEW_DOF = {
    "name": "nuclear_unit_availability",
    "where": "run_config.scenario_config.nuclear_unit_availability",
    "identification": "measured",
    "lineage_solves": "1 (caiso-148 A/B, 2026-07-31)",
    "value": True,
    "source": (
        "data/raw/nuclear-availability-CAISO.csv (1,886 rows, 2 reactors — Diablo "
        "Canyon 1+2, EIA plant 6099, 2,240 MW), written by "
        "scripts/data/derive_nuclear_availability.py --iso CAISO. Timing from the NRC "
        "daily Power Reactor Status Report "
        "(data/raw/nrc-reactor-status/<YYYY>PowerStatus.txt, fetched by "
        "scripts/data/fetch_nrc_reactor_status.py from nrc.gov — US-government public "
        "domain); level from the committed EIA-923 anchor "
        "NUCLEAR_MONTHLY_CF_BY_YEAR['CAISO']. Consumed by "
        "data.outages.nuclear_unit_availability_series('CAISO', year) -> "
        "data.fleet.arrays.generators_to_fleet_arrays, applied per (plant_code, "
        "unit_no) before the nuclear must-run floor is built."
    ),
    "note": (
        "NOT a fitted parameter and not a tunable: it is a boolean that selects the "
        "MEASURED per-reactor daily availability over a fleet-month smear of the same "
        "measured monthly energy (rule 14 [R-ACCURATE]). It carries no threshold or "
        "scalar of its own — the deriver's EVENT_RAW_MAX / SCALE_CLIP / WEDGE_TOL are "
        "inherited FROZEN from the ERCOT deriver and were not re-tuned here, and the "
        "monthly level is pinned to the same EIA-923 anchor the smear already used, so "
        "the swap is a pure timing re-arrangement (measured in-solve at "
        "|dTWh| <= 0.045 %). Per rule 23 [R-FROZEN-DERIVE] the artifact re-derives ONLY "
        "when NRC publishes a new year or EIA-923 revises the anchor, never because a "
        "residual moved, and any re-derivation commit must cite the data change. Per "
        "rule 25 [R-ISO-SCOPE] this is CAISO's own artifact from CAISO's own reactors; "
        "the ERCOT and NYISO K verdicts transfer nothing to it."
    ),
    "known_limitation": (
        "2025 coverage is 58.1 % of days (212/365; 31 of 36 months overall), because "
        "five 2025 months — Apr, May, Jul, Nov, Dec — are dropped by the deriver's "
        "thermal-vs-net wedge fallback. The drop is SYSTEMATIC and correct, not "
        "random: each is a month holding a real event whose non-event pool is already "
        "saturated at 100 %, so the capped fixed-point cannot scale up to an anchor "
        "that EIA-923 clipped at 1.0. Measured cause: EIA-930 CISO NG:NUC peaks at "
        "2,281/2,279/2,309 MW against the model's 2,240 MW EIA-860 nameplate, so "
        "Diablo runs up to +3.1 % above nameplate and NRC-%thermal x nameplate cannot "
        "express a full-power month's net energy. Posting the NRC level there would "
        "delete real capability, so the smear (the anchor itself) correctly stands. "
        "The practical consequence, disclosed in the prereg BEFORE the solve: in 2025 "
        "the U1 Apr-May refuel, the Jul U2 derate and the Dec U1 trip keep the smear "
        "and only the October U2 refuel carries measured timing. 2023 and 2024 are "
        "fully covered. The clean fix is a nameplate/uprate basis reconciliation for "
        "Diablo (EIA-860 net summer capacity vs licensed thermal power), which is a "
        "fleet-representation change well outside a single calibration session's "
        "scope and is filed as an open item, not silently absorbed."
    ),
}


def main() -> int:
    """Write the caiso-148 attestation from the caiso-147 keeper's."""
    att = json.loads(SOURCE.read_text())
    att["governance"]["attested_by"] = ATTESTED_BY

    for exc in att["exceptions"]:
        key = (exc.get("criterion"), int(exc.get("year", 0)))
        if key in REMEASURED:
            exc["magnitude"] = REMEASURED[key] + "PRIOR MAGNITUDE: " + exc["magnitude"]
        exc["reason"] = CARRY + exc["reason"]
        exc["carried_from"] = (
            "2026-07-31-caiso147-chp-heat-rates -> 2026-07-29-caiso139-dump-guard-offer"
            " (owner ledger, caiso-145)"
        )

    dof = att["free_parameters"]
    dof["entries"] = [e for e in dof["entries"] if e.get("name") != NEW_DOF["name"]] + [
        NEW_DOF
    ]
    dof["n_entries"] = len(dof["entries"])
    dof["n_residual"] = sum(
        1 for e in dof["entries"] if e.get("identification") == "residual"
    )

    TARGET.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {TARGET}")
    print(f"  exceptions carried: {len(att['exceptions'])}")
    print(
        f"  DOF entries: {dof['n_entries']} ({dof['n_residual']} residual-identified)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
