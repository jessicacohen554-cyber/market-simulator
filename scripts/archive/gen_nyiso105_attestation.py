"""Write ``calibration_attestation.json`` for the nyiso-105 KEEPER-RECOMMENDED arm.

``2026-07-31-nyiso105-chp-heat-rates``
(``results/calibration/nyiso105_chpheatrate_B``) passes every pre-registered gate
in ``results/calibration/PREREG-nyiso105-chp-heat-rates-2026-07-31.md`` §4 and
satisfies its §6 promotion rule. This script builds the C6 attestation the
promotion requires (rule 21 ``[R-DOF]``: every keeper carries a DOF ledger),
inheriting the nyiso-100 keeper's ledger and adding ONE entry for the arm's
single delta.

**The delta adds ZERO free parameters.** ``measured_chp_heat_rates`` replaces one
measured input with a strictly more accurate measured input on the same source,
vintage and denominator: eGRID's own published CHP heat-input allocation, undone.
``n_residual`` is unchanged.

**The C3c exceptions block carries forward UNCHANGED.** This arm does not target
C3c, does not move it, and spends no new caveat slot — the ledger stays at 1 of
3 used, exactly as nyiso-104b left it.

Usage:
    python scripts/gen_nyiso105_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PRIOR_KEEPER = (
    REPO / "results/calibration/nyiso100_silretire/calibration_attestation.json"
)
DEST = REPO / "results/calibration/nyiso105_chpheatrate_B/calibration_attestation.json"

NEW_ENTRY = {
    "name": (
        "measured_chp_heat_rates — power-only CHP heat rates from eGRID's own "
        "published CHP heat-input allocation, added back (NYISO artifact)"
    ),
    "where": (
        "ScenarioConfig.measured_chp_heat_rates -> data.chp."
        "apply_measured_chp_heat_rates over data.fleet.campd_bins."
        "measured_chp_heat_rates('NYISO'), applied in fleet.eia860."
        "load_fleet_from_csv; table "
        "data/raw/_processed-legacy/chp_power_only_heat_rates_NYISO.csv from "
        "scripts/data/derive_chp_power_only_heat_rates.py --iso NYISO"
    ),
    "identification": "measured-published",
    "lineage_solves": (
        "1 A/B pair, 0 sweeps. Built to a pre-registration "
        "(results/calibration/PREREG-nyiso105-chp-heat-rates-2026-07-31.md, "
        "committed AND PUSHED before either arm solved) against a same-HEAD "
        "zero-delta control, never the committed keeper (the neiso-69 drift "
        "precedent). No value was swept and none was adjusted after the "
        "result — there is no value to adjust, because every applied rate is "
        "read from eGRID and nothing is fitted."
    ),
    "value": (
        "NO FREE PARAMETER. Per-plant, fully determined by eGRID: "
        "heat_rate = (PLHTIAN + CHPCHTI) / PLNGENAN. 31 (plant, class) rows "
        "derived, 18 applied on flag == 'ok': CC_CHP 11 of 17 plants "
        "(2,984 of 4,309 MW = 69.3 % of class MW), model 6.82 -> measured 8.50 "
        "MMBtu/MWh (incumbent understated 19.8 %); CT_CHP 7 of 14 plants "
        "(384 of 446 MW = 86.2 %), 7.46 -> 11.68 (understated 36.2 %). "
        "Largest repricings are in-city: Linden Cogeneration 915 MW "
        "5.74 -> 9.23, East River 306 MW 7.42 -> 11.80, Brooklyn Navy Yard "
        "260 MW 5.38 -> 8.75. The 13 unapplied rows are excluded by published "
        "flags, not by choice: not_unfired_topping 8, no_egrid_row 2, "
        "no_chp_credit 1, above_physical_band 1, basis_mismatch 1."
    ),
    "source": (
        "eGRID plant sheet, the same vintage and the same NET denominator the "
        "incumbent rate already used. PLHTIAN = heat input allocated to "
        "electricity (what PLHTRT divides by PLNGENAN); CHPCHTI = heat input "
        "eGRID allocated to useful thermal output. Adding CHPCHTI back undoes "
        "eGRID's own CHP credit, so NO gross-to-net factor is involved — that "
        "is what blocked the CEMS route (FINDING-miso98 §6.1). Independently "
        "validated against metered CAMPD heat input: (PLHTIAN + CHPCHTI) "
        "reproduces it within 1 % on 16 of 18 covered NYISO plants, median "
        "ratio 1.00000. Rule 25 [R-ISO-SCOPE]: NYISO's artifact is derived "
        "from NYISO's own plants; no MISO or CAISO value crosses the "
        "boundary. NYISO is NOT in CHP_STEAM_CREDIT_HR_CORRECTION_ISOS "
        "({CAISO, PJM}), so the incumbent here was eGRID's raw credited "
        "PLHTRT — the MISO shape — and no hand factor is involved or retired."
    ),
    "forward_story": (
        "Re-derives for any forward year from each new eGRID vintage by the "
        "same formula, with no residual consulted (rule 23 "
        "[R-FROZEN-DERIVE]). A retired plant leaves the artifact; a new cogen "
        "enters it. This is the same standing on which the MISO (miso-99) and "
        "CAISO (caiso-147) keepers took the mechanism."
    ),
    "rule_13_admissibility": (
        "No measured OUTCOME enters the model. What enters is a measured "
        "PHYSICAL INPUT — the rate at which a machine turns fuel into power — "
        "on a published source, and it responds to changed conditions in a "
        "forecast year. Nothing is pinned to observed generation, and the "
        "scored dispatch is left entirely free: the arm makes CHP more "
        "expensive and the LP decides what to do about it. Indeed the class "
        "the mechanism most affects moves FURTHER from its actual (CT_CHP), "
        "which is definitionally not outcome-pinning."
    ),
}

ATTESTED_BY = (
    "nyiso-105 KEEPER-RECOMMENDED 2026-07-31: the "
    "2026-07-30-nyiso-100-silretire recipe with ONE boolean added, "
    "measured_chp_heat_rates=true, scored against a same-HEAD zero-delta "
    "control (2026-07-31-nyiso105-control) rather than the committed keeper. "
    "EVERY pre-registered construction gate PASSES. K1 flag fidelity: arm B "
    "true / control false, all 18 applied artifact rows flag == 'ok'. K2 "
    "control integrity passes on the STRICT byte basis, not merely the "
    "scorecard one — control minus committed keeper is EXACTLY 0.0 on every "
    "class in all three years, so unlike caiso-146 and neiso-69 there is NO "
    "same-HEAD drift for NYISO and the A/B is unconfounded. K3 liveness: "
    "class-hour |delta| peaks at CC_CHP 727.0 / 578.9 / 660.4 MW and CT_CHP "
    "160.7 / 157.3 / 160.7 MW. K4 single delta: the two run_config scenario "
    "blocks differ in exactly the one boolean. K5 year span: both bundles "
    "[2023, 2024, 2025], nothing else — the holdout spend freeze is ACTIVE "
    "and untouched. K6 pin sensitivity: the movement is NOT confined to the "
    "D-10 pinned classes — CC_REGULAR, ST_GAS and CT_PEAKER are all free "
    "classes and all move, so the verdict does not rest on classes D-10 "
    "discounts. NO CRITERION MOVES AT ALL between control and arm: both score "
    "fuelmix PASS, sysvol PASS, price_mean PASS, price_shape PASS, "
    "dispatch_corr PASS, and C1 all 14/14 / free 10/10. Zero free parameters "
    "added; n_residual unchanged."
)

RESIDUALS_NOTE = (
    "REPORTED, NOT PATCHED (prereg §5, rules 1 [R-STRUCT] and 14 "
    "[R-ACCURATE]). The arm IMPROVES the energy-weighted C1 residual — "
    "3-year mean |error| 9.458 % -> 9.224 %, and per year 7.66 -> 7.60, "
    "5.66 -> 4.76, 15.06 -> 15.31 — with more classes better than worse in "
    "every year (4/3, 5/2, 4/3). Gains: CC_CHP +13.61 -> +10.75, +7.95 -> "
    "+2.74, +31.41 -> +28.21 %; CC_REGULAR -7.93 -> -6.61 and -1.87 -> +0.23 "
    "%; ST_GAS improves in 2024 (-17.79 -> -15.75) and 2025 (-29.69 -> "
    "-27.66); CT_PEAKER improves in all three years. THE ONE CONSISTENT "
    "ADVERSE IS CT_CHP: -49.32 / -52.35 / -38.56 % -> -67.85 / -67.57 / "
    "-61.97 %. It is reported and NOT patched, and it is an OPEN ROOT-CAUSE "
    "ITEM rather than a defect of this mechanism: CT_CHP was ALREADY 39-52 % "
    "under-dispatched BEFORE the arm, so a strictly more accurate offer "
    "EXPOSES a pre-existing miss rather than creating one. Rule 1 both "
    "directions is explicit that a correct measured input stays in and the "
    "real root cause gets found — the named successor is the BTM host-steam "
    "holdout (chp_btm_pct / chp_grid_pmin_mw) and the CT_CHP must-run "
    "treatment, NOT the heat rate. Mean lambda rises 34.660 -> 35.078, "
    "37.667 -> 38.227, 61.974 -> 62.837 $/MWh, as expected when in-city CHP "
    "is repriced up; C3a stays PASS. C3c is NOT targeted, NOT claimed and "
    "NOT moved by this arm."
)

OPEN_ITEMS = [
    "CT_CHP under-dispatch DEEPENS -49.3/-52.4/-38.6 % -> -67.9/-67.6/-62.0 % "
    "(2023/2024/2025). Owner-visible and unpatched. The class was already the "
    "worst-matched CHP group before this arm, so the accurate heat rate is "
    "diagnostic, not causal. Named successor lane: the BTM host-steam holdout "
    "(chp_btm_pct / chp_grid_pmin_mw) and the CT_CHP must-run treatment. "
    "Rule 14 [R-ACCURATE] forbids reverting the measured input to hide it."
]


def main() -> int:
    """Build nyiso-105's attestation from the nyiso-100 keeper's."""
    att = json.loads(PRIOR_KEEPER.read_text())
    gov = dict(att.get("governance", {}))
    gov["attested_by"] = ATTESTED_BY
    gov["residuals_note"] = RESIDUALS_NOTE
    att["governance"] = gov
    att["_open_items"] = OPEN_ITEMS
    # The C3c exceptions block carries forward UNCHANGED — this arm does not
    # target C3c, does not move it, and spends no new caveat slot.
    fp = att["free_parameters"]
    names = {e["name"] for e in fp["entries"]}
    if NEW_ENTRY["name"] not in names:
        fp["entries"] = [*fp["entries"], NEW_ENTRY]
    fp["seeded"] = (
        "2026-07-31 nyiso-105 — UNION'd forward from the nyiso-100 keeper "
        "ledger and NOT rebuilt (a blind build_dof_ledger.py rebuild drops "
        "the curated measured/published entries — the failure mode the "
        "nyiso-81/87/89/92/96/98/99/100 notes all recorded). ONE new entry, "
        "and it adds ZERO free parameters: measured_chp_heat_rates replaces "
        "one measured input with a strictly more accurate measured input on "
        "the SAME source, vintage and net denominator (eGRID's own published "
        "CHP allocation, undone). Every applied value is read, none is "
        "chosen. n_residual is UNCHANGED."
    )
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    DEST.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"wrote {DEST.relative_to(REPO)} — {fp['n_entries']} DOF entries "
        f"({fp['n_residual']} residual-identified)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
