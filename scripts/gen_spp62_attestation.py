"""Emit the SPP-62 calibration attestation for ``results/calibration/spp62_span``.

SPP-62 is the SPP-61 keeper recipe (``results/calibration/spp61_vintage``,
SPP keeper 6 — ``eia860_vintage_tracks_solve_year`` armed) plus **exactly one
change, and it is a DATA-INPUT repair, not a model change**: the coal
supply-class census in ``scripts/data/derive_coal_supply.py`` now reads the
solved span's own EIA-860 releases (``--census-vintage 2023 2024 2025``)
instead of the canonical 2025 Early Release snapshot alone, so
``data/raw/_processed-legacy/coal_supply_SPP.csv`` carries 31 rows rather than
29.  This is the R-ay prerequisite SPP-61's own FINDING §8 named and routed
("a PREREQUISITE, not an alternative") and which keeper 6 was promoted
without.

The DOF ledger is therefore INHERITED verbatim from keeper 6 (rule 21
``[R-DOF]``): the repair introduces **zero** new free parameters.  Its two new
rows are ``prb`` at 100 % of ranked weight, computed by the same arithmetic
that ranks the other 29 plants; selection is by calendar year alone.

Admissibility rests on rule 23 ``[R-FROZEN-DERIVE]`` (the cited trigger is a
change in the DERIVE'S OWN INPUT — its census read a registry measured wrong
for the solved year — never a residual that moved) and rule 14
``[R-ACCURATE]``.  It moves one gated row the WRONG way and stays in
regardless (rule 1 ``[R-STRUCT]``), exactly as the lane's PRECOMMIT §10
pre-committed before the solve.

Usage:
    python scripts/gen_spp62_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEEPER = REPO / "results/calibration/spp61_vintage/calibration_attestation.json"
BUNDLE = REPO / "results/calibration/spp62_span"


def build() -> dict:
    """Return the SPP-62 attestation, inheriting keeper 6's DOF ledger verbatim."""
    att = json.loads(KEEPER.read_text())

    # Rule 21 [R-DOF]: the ledger is unchanged. The census repair is a
    # membership filter over committed EIA-860 releases; it sets no value.
    att["free_parameters"]["inherited_from"] = "spp61_vintage (SPP keeper 6)"
    att["free_parameters"]["inheritance_basis"] = (
        "SPP-62 is the SPP-61 recipe plus ONE DATA-INPUT repair: the coal "
        "supply-class census reads the solved span's own EIA-860 releases "
        "(derive_coal_supply.py --census-vintage 2023 2024 2025). No "
        "ScenarioConfig field, offer band, structural share, shared default or "
        "solve-path code changes, so every ledger entry and every scalar count "
        "carries over unchanged. n_entries stays 3 and n_residual stays 2. The "
        "repair's two added rows carry no settable value: both resolve to 'prb' "
        "at 100 % of ranked EIA-923 weight by the same arithmetic that ranks the "
        "other 29 plants."
    )

    # Name THIS lane. The inherited string still named SPP-52a, two lanes back;
    # C6 is a truthfulness gate, so the attestation must describe the run it sits in.
    att["governance"]["attested_by"] = (
        "SPP-62 (2026-09-10): SPP keeper 6's recipe "
        "(2026-09-10-spp-61-vintage, which arms eia860_vintage_tracks_solve_year "
        "on SPP-52a's authorized offer-curve level, itself on keeper 4's "
        "oversupply curtailment allocation and repaired GMT->fixed-CST "
        "actual-LMP clock) plus ONE change: the R-ay coal supply-class census "
        "repair below, a DATA-INPUT repair with no ScenarioConfig field and no "
        "solve-path code change. ONE --years 2023 2024 2025 invocation, years "
        "sequential (rules 12 / 16), 440 s wall. The authorized price-tuning "
        "channel declared above is replayed VERBATIM at 0.93 on all four bands "
        "of the ten registered fossil classes and is NOT re-cut by this lane; "
        "no multiplier was swept against any gate (rule 1 [R-STRUCT] condition "
        "(c)). Rule 21 [R-DOF]: ledger inherited verbatim, n_entries 3, "
        "n_residual 2. Determination NOT-YET, unchanged from keeper 6, on the "
        "identical basis (fuelmix, price_tail)."
    )

    att["governance"]["measured_input_switches"]["coal_supply_census_vintage"] = {
        "value": [2023, 2024, 2025],
        "where": (
            "data/raw/_processed-legacy/coal_supply_SPP.csv (31 rows), derived by "
            "scripts/data/derive_coal_supply.py --iso SPP --census-vintage "
            "2023 2024 2025. Consumed as resolver step 2 of "
            "data/coal.py::coal_supply_class."
        ),
        "identification": "measured-physical",
        "source": (
            "EIA-923 Page-1 net generation by energy-source code, over the coal "
            "census taken from the UNION of the canonical EIA-860 snapshot and "
            "each solved year's own vintage_<year>/ release. Plant 6193 "
            "(Harrington) resolves prb at 100 % of 26,193,400.3 MWh of reported "
            "SUB; plant 10862 (ADM Lincoln) prb at 100 % of 156,101.0 MWh."
        ),
        "warrant": (
            "Rule 14 [R-ACCURATE] and rule 13 [R-MEASURED]. The census read "
            "load_fleet_from_csv with NO VINTAGE — the canonical 2025 Early "
            "Release — for every solved year, so a plant that burned coal in the "
            "solved year but had been re-fuelled by the snapshot's vintage was "
            "absent from the census, received no rank, fell through all four "
            "resolver steps to '' and reported in a bare COAL class the SPP "
            "EIA-923 benchmark has no row for. Measured on keeper 6: 4.3551 TWh "
            "(2023) and 2.0670 TWh (2024) of coal dispatch in that class, scored "
            "by C1 against NOTHING — it appears in no C1 row, passing or failing. "
            "This run books it in COAL_PRB, the class EIA-923's own fuel code SUB "
            "maps to, so the model reaches the SAME class the benchmark does."
        ),
        "frozen_derive_admissibility": (
            "Rule 23 [R-FROZEN-DERIVE]: the cited trigger is a change in the "
            "DERIVE'S OWN INPUT — its plant census read an EIA-860 registry "
            "measured wrong for the solved year, and the correct release was "
            "already committed on disk — NOT a residual that moved. Three facts "
            "make the argument stand without leaning on any residual: (a) the "
            "rank is not a choice (SUB -> prb at 100 %, zero free values); (b) "
            "the repair is INERT for every committed run (all seven ISOs' fleets "
            "byte-identical; 46 of 46 committed run_configs read the canonical "
            "registry); (c) it moves the target residual the WRONG way. The "
            "--year span is untouched, so the pre-patch script reproduces the "
            "committed CSV byte-identically (md5 "
            "5a71bd95bf10a732af980086e541ffa3) and the 29-row impact census "
            "below is exact rather than approximate."
        ),
        "impact_census": (
            "ALL 29 INCUMBENT ROWS BYTE-IDENTICAL — the re-derive is 2 "
            "insertions(+), 0 deletions. Not luck: the census is a membership "
            "filter and each plant's rank is computed from its own EIA-923 rows "
            "independent of every other plant, so widening it can only ADD rows."
        ),
        "one_mech": (
            "Rule 19 [R-ONE-MECH]: no fifth resolver. The four are the curated "
            "ERCOT map, the EIA-923-derived per-ISO CSV, the EIA-860 retiree "
            "fallback and the flag-gated partial-exit registry. Both new plants "
            "were unresolved by ALL FOUR, so no existing resolution changes "
            "hands: 7902 Pirkey keeps its retiree-fallback lignite and 57937 "
            "stays unresolved (both are coal only in vintage_2020, outside the "
            "solved span)."
        ),
        "forward_test": (
            "Rule 13's admissibility test is met: the same construction "
            "regenerates for a forecast year from the then-current EIA-860 "
            "release and responds to changed conditions. It pins no outcome to "
            "an actual and is not an overlay."
        ),
        "iso_scope": (
            "Rule 25 [R-ISO-SCOPE]: derive_coal_supply.py is SHARED, so the new "
            "--census-vintage argument DEFAULTS to the canonical snapshot alone "
            "— the historical construction. Measured: with the patch applied and "
            "no flag passed, SPP / PJM / MISO / NEISO all re-derive "
            "byte-identically to the pre-patch script at HEAD. Only SPP's CSV "
            "moves, and plant codes 6193 / 10862 appear in SPP's fleet only (3 "
            "and 1 generators) and in NO other ISO's fleet, even though "
            "_derived_coal_supply globs every ISO's CSV into one national map."
        ),
        "registry": (
            "Rule 24 [R-REGISTRY]: through the registered per-ISO derived CSV, "
            "never a per-plant dict. Provenance recorded in "
            "data/raw/_processed-legacy/README.md."
        ),
    }

    att["disclosures"] = {
        "note": (
            "SPP-62 disclosures — reported, not patched (rules 1 / 13 / 14). "
            "Inherits SPP-61's, which inherits SPP-52a's."
        ),
        "the_gated_fit_is_a_WASH_and_one_row_moves_the_wrong_way": (
            "Against keeper 6 the scored change is exactly TWO C1 rows, and they "
            "move in OPPOSITE directions. 2023 COAL_PRB improves 62.522 -> "
            "66.877 against 65.279 actual, i.e. -2.76 -> +1.60 TWh, a 1.16 TWh "
            "reduction in absolute error. 2024 COAL_PRB DEGRADES 59.651 -> "
            "61.718 against 59.953 actual, i.e. -0.30 -> +1.76 TWh, a 1.46 TWh "
            "INCREASE in absolute error. Both stay inside the +/-8.00 TWh band. "
            "The lane's PRECOMMIT §10 pre-committed to keeping the repair "
            "whatever it did to the residual, and the 2024 degradation is "
            "reported at full magnitude rather than absorbed or offset."
        ),
        "it_does_NOT_fix_C1_and_the_determination_does_not_move": (
            "Both ST_GAS rows still FAIL (2023 -8.38 TWh, 2024 -9.71 TWh) — "
            "identical to keeper 6, because the census repair touches coal "
            "classification and not gas dispatch. C3c still FAILS in all three "
            "years (model 0 / 5 / 0 hours above $200 against 42 / 59 / 68 "
            "actual). DETERMINATION NOT-YET, the same as keeper 6. No reader "
            "should infer from 'the keeper improved' that the scoreboard moved: "
            "it did not."
        ),
        "what_it_actually_closes": (
            "A SCORING BLIND SPOT, not a residual. Keeper 6 books 4.3551 TWh "
            "(2023) and 2.0670 TWh (2024) of coal dispatch in a bare COAL class "
            "the SPP benchmark has no row for, so that energy is scored against "
            "nothing and COAL_PRB reads low by exactly the missing amount. The "
            "single-delta A/B against keeper 6 in 2023 is 4.3551 TWh moving from "
            "COAL to COAL_PRB and NOTHING ELSE: all fourteen other classes are "
            "identical to four decimals (ST_GAS 7.0867, CT_PEAKER 16.2967, "
            "CC_REGULAR 42.4877, COAL_LIGNITE 7.2935, wind 113.7572, ...). In "
            "2024 the same re-label moves 2.0670 TWh."
        ),
        "c3_moves_slightly_and_mostly_improves": (
            "C3b monthly load-weighted NRMSE, keeper-5 control -> this run: "
            "0.1647 -> 0.1723 (2023, WORSE), 0.1761 -> 0.1725 (2024, better), "
            "0.1755 -> 0.1669 (2025, better). C3a +2.1 / +1.3 / +2.2 % of "
            "actual. All three years stay far inside their bands; the 2023 "
            "degradation is reported."
        ),
        "gates_that_still_fail": (
            "C1 on the 2023 and 2024 ST_GAS rows, and C3c in all three years. "
            "Neither is reachable by the coal-census channel. Because there are "
            "TWO failing criteria, the rule 22 [R-C3C] standing rule cannot "
            "fire: it requires a LONE failure."
        ),
        "still_open_and_NOT_closed_here": (
            "SPP is NOT calibrated. The ST_GAS offer / commitment defect (the "
            "named successor object, model ST_GAS 6.95 / 8.13 TWh below actual "
            "BEFORE either repair), the absent scarcity mechanism (C3c, "
            "SPP-55/56), the thermal-commitment floor (the LP absorbs 98.2 % of "
            "concentrated curtailment headroom; thermal annual minimum 254.3 MW "
            "across a ~40 GW fleet) and the zonal spread (measured |N-S| 12.13 / "
            "17.23 / 15.18 against a model ~1) are all still open."
        ),
        "routed_not_touched_a_hazard_this_lane_did_not_cause": (
            "Re-deriving PJM or MISO's coal supply CSV at HEAD with NO code "
            "change at all already re-ranks 5 PJM plants (594, 876, 879, 3149, "
            "6166) and 10 MISO plants (1082, 1091, 1733, 2107, 4041, 4078, 6034, "
            "7343, 8023, 56068), because the raw f923_*.zip receipt corpus their "
            "committed CSVs were built from is no longer under data/raw and the "
            "generation fallback disagrees with it. SPP is the clean case "
            "(every row source=generation). No ISO may re-derive without "
            "reconciling that lost source first. Recorded in "
            "data/raw/_processed-legacy/README.md; each desk's own card "
            "(rule 28(d))."
        ),
        "also_routed_a_provenance_gap": (
            "coal_supply_*.csv is a solve-affecting registry table that the capx "
            "D79 solve-surface fingerprint does NOT cover (the surface is seven "
            "config MODULES) and that carries no resolved_inputs sha256 stamp in "
            "run_config.json the way campd-unit-outages-SPP.csv and "
            "thermal_tranches_SPP.csv do. Harmless for this lane — inertness is "
            "proven directly — but a real hole, stated rather than relied on."
        ),
    }

    return att


def main() -> None:
    """Write the attestation into the SPP-62 bundle."""
    out = BUNDLE / "calibration_attestation.json"
    out.write_text(json.dumps(build(), indent=1) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
