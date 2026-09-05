"""Generate miso170_membership_B's calibration attestation from the keeper's.

The arm is the miso-169 keeper recipe plus exactly one zero-DOF MEMBERSHIP
correction armed on both mechanisms that floor MISO ST_GAS, so its attestation
is the keeper's with: one MEASURED-identified ledger entry for the lay-up
census (n_scalars 0 — a plant-code SET produced by a conduct test), a rewritten
``governance.attested_by`` for the miso-170 A/B, and the session's disclosures.
The miso-169 entries and every exception carry unchanged.
"""

import json

SRC = "results/calibration/miso169_gated_B/calibration_attestation.json"
DST = "results/calibration/miso170_membership_B/calibration_attestation.json"

d = json.load(open(SRC))

d["free_parameters"]["entries"].append(
    {
        "name": (
            "laid-up plant census (reliability_floor_plant_exclusions + "
            "mustrun_plant_exclusions)"
        ),
        "where": (
            "data/raw/_processed-legacy/campd_bridge_layup_exclusions_MISO.csv "
            "(scripts/data/derive_campd_bridge_layup_exclusions.py) -> "
            "data.bridge_layup_exclusions.load_layup_exclusions('MISO') for the "
            "must-run seams, and the same census written into "
            "data/raw/reference/reliability_floor_coeffs_MISO.csv's "
            "exclude_plant_codes column by that deriver's "
            "--patch-reliability-coeffs step for the reliability floor"
        ),
        "identification": "measured",
        "n_scalars": 0,
        "lineage_solves": (
            "0 (derived from the pooled 2023-2025 CAMPD record BEFORE either "
            "arm solved, and computed WITHOUT reference to which plants the "
            "floors force or to any D-4 verdict; never touched a residual)"
        ),
        "value": (
            "A PLANT-CODE SET, not a scalar: the 15 of 62 covered MISO plants "
            "whose median CAMPD plant gross load is ZERO in every "
            "(year, 4-hour block) cell of 2023-2025 - the nyiso-140 criterion "
            "verbatim, with the per-cell quantifier that separates lay-up from "
            "a low capacity factor. Nearest non-qualifier sits at 16/18 cells. "
            "170, 203, 992, 1104, 1131, 1464, 1702, 1891, 2123, 3992, 6358, "
            "6639, 8054, 8056, 58478. NOT CIRCULAR, which is the point: the "
            "test reads only the meter and then selects 7 of the 8 plants the "
            "D-4 per-unit conduct rider flags - agreement, not fitting. "
            "DELIBERATELY EXCLUDED FROM THE SET: plant 1402 Little Gypsy "
            "(6/18 zero cells, pooled median 45.0 MW, P(on)=0.506) is an "
            "ordinary cycler whose forcing is a WINDOW defect, not a "
            "membership one, and burying that in a membership list is what "
            "rules 1/14 forbid (the nyiso-144 plant-7314 line)."
        ),
    }
)
d["free_parameters"]["n_entries"] = len(d["free_parameters"]["entries"])

d["governance"]["attested_by"] = (
    "ARM - EXACTLY ONE CORRECTION CHANGES, ARMED ON BOTH MECHANISMS THAT "
    "FLOOR THE SAME CLASS: reliability_floor_plant_exclusions=true + "
    "mustrun_plant_exclusions=true, over ONE mechanism-blind lay-up census. "
    "miso-170, 2026-08-19. PREREG "
    "results/calibration/PREREG-miso170-stgas-floor-membership-2026-08-19.md "
    "was committed BEFORE either arm solved, and the gate scorer "
    "scripts/probes/_miso170_membership_ab.py - carrying the kill thresholds "
    "as literals - was committed BEFORE either result was read. Both arms are "
    "replay_keeper re-solves of the 2026-08-19-miso-169-online-gated keeper's "
    "own meta.json at this session's HEAD, --year 2023 2024 2025 in ONE "
    "invocation each, years sequential (rules 12/16); the arm's deltas rode "
    "the sanctioned replay_keeper --set channel. CONTROL BIT-IDENTITY (K-0): "
    "2026-08-19-miso-170-control reproduces the committed keeper with numeric "
    "max|diff|=0 on all 12 scored sidecars of all three years, so the new "
    "field, both arrays.py membership seams and the new CSV column are "
    "PROVABLY INERT at their defaults and this is a clean single-delta A/B. "
    "The correction adds ZERO free parameters (rule 21): a plant-code SET "
    "produced by a conduct test, n_scalars 0, frozen against residuals "
    "(rule 23). GATES: K-2 liveness PASS (shed 0.5295/0.8653/0.9459 TWh "
    "against a pre-registered 0.5044/0.7531/0.7853 +/-50%); K-3 PASS (D-4 "
    "per-unit conduct failures 18 -> 3 with ZERO new and zero new "
    "off-window, the pre-named survivor present); K-5 PASS (zero "
    "record-grain PASS->FAIL flips over 67 records); K-6 PASS (D-1 shape "
    "held). C8 ST_GAS 2024 FAIL -> PASS, the first MISO year ever to clear "
    "C8's grounded-above-budget provenance leg. K-1 (membership exactness) "
    "FAILED AS WRITTEN on two residual plant-1104 reliability_floor rows and "
    "IS NOT REINTERPRETED - see the disclosures. PROMOTED BY OWNER DIRECTION "
    "2026-08-19 ('Is this a recommended keeper candidate? If so plz promote. "
    "If structural integrity improves but gates regress that may still be a "
    "keeper') over the session's own REJECTED-AS-ARMED mechanical verdict; "
    "both records stand. Rule 22: no year outside 2023-2025 was solved, "
    "scored or registered; MISO holds neither complete nor final and the "
    "holdout spend freeze is untouched."
)

d["disclosures"]["miso170_note"] = (
    "miso-170 disclosures, reported rather than patched. (a) THE K-1 FAILURE "
    "IS AN INSTRUMENT ATTRIBUTION DEFECT, NOT A MEMBERSHIP RESIDUAL, and the "
    "mechanical REJECTED-AS-ARMED verdict is recorded rather than rewritten. "
    "Read at UNIT grain from this bundle's own floors/<year>_P1.npz, plant "
    "1104's ST_GAS rows carry ZERO reliability-floor unit-hours in both "
    "flagged years; the residual is 777 (2023) / 763 (2025) unit-hours on the "
    "plant's CT_PEAKER tranches, entirely inside h15-21 - the MISO-Plains CT "
    "evening-ramp limb, which never leaves its own declared window. D-4 "
    "reports it as 'reliability_floor x ST_GAS' because "
    "legitimacy_diagnostics.aggregate_floors_by_plant collapses a plant's "
    "unit rows into ONE row and labels the plant with its most common unit "
    "group (1104: 4 ST_GAS rows vs 3 CT_PEAKER), so a CT_PEAKER floor is "
    "charged to ST_GAS's provenance leg - and the per-unit conduct rider, "
    "which is deliberately gated to all-hours windows BECAUSE that is where "
    "the off-window test is vacuous, then convicts on a floor whose own "
    "window test is live and passing. This affects any ISO with mixed-class "
    "sites and is an OPEN owner item. (b) C8 STILL FAILS 2023 AND 2025, so "
    "the determination is UNCHANGED at NOT-YET: 2023 on plant 1402 (the "
    "pre-registered expected survivor - a cycler whose forcing is a WINDOW "
    "defect) plus 1104 (a), and 2025 on 1104 alone (a). ST_GAS stays ABOVE "
    "the 30% merchant cap in every year (32.7->31.2 / 34.4->31.9 / "
    "46.2->43.6%) exactly as pre-registered: this correction buys LEGITIMACY, "
    "not budget headroom. (c) C3a-2025 -12.4 -> -12.1%. DISCLOSED, NOT "
    "CLAIMED - it is 0.3pp on a load-bearing miss the miso-163 owner ruling "
    "closed as a model-class limit, and no pre-registered gate rewards it. "
    "(d) NAMED SUCCESSOR, not bundled (rule 19): the per-plant must-run "
    "floor's window is an online_frac POOLED over 2023-2025, while plant "
    "1402's own per-year metered online share is 0.2495/0.6134/0.6548 - so "
    "in 2023 the floor commits it across the top 50.8% of system-load hours "
    "against a plant that ran 25% of the year, a ~2.3x over-commitment "
    "produced by the pooled vintage. A per-year online_frac needs its own "
    "identification, A/B and DOF answer. (e) RHO_CLIP WAS NOT TOUCHED: no "
    "owner ruling on the band exists, so the standing nyiso-144 escalation "
    "holds and both arms solved at the same uncited 0.5 floor the "
    "predecessor keeper did."
)

json.dump(d, open(DST, "w"), indent=1)
print(
    "attestation written;",
    d["free_parameters"]["n_entries"],
    "ledger entries /",
    d["free_parameters"]["n_residual"],
    "residual",
)
