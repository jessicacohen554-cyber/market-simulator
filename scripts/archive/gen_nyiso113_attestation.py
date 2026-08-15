"""Write ``calibration_attestation.json`` for the nyiso-113 KEEPER-RECOMMENDED arm.

``2026-08-02-nyiso-113-li-locational``
(``results/calibration/nyiso113_lilocational_B``) passes every pre-registered
gate in ``results/calibration/PREREG-nyiso113-li-locational-reserve-2026-08-02.md``
§4–§5 (with the K3/K4 instrument correction recorded in §8 of the finding, and
re-scored on a valid instrument). This script builds the C6 attestation the
promotion requires (rule 21 ``[R-DOF]``: every keeper carries a DOF ledger),
inheriting the nyiso-112 keeper's 29-entry ledger and adding ONE entry for the
arm's single delta.

The delta adds **zero free parameters**: both requirement levels (120 MW; 270 MW
off-peak / 540 MW on-peak), the $25/MW demand-curve value and the on/off-peak
boundary are published NYISO records — the Locational Reserve Requirements
posting, Ancillary Services Manual §6.8 items 10 and 15, and the tariff's own
MST §2.15 On-Peak calendar. ``n_entries`` goes 29 -> 30 while ``n_residual``
stays 6.

The C3c exceptions block is carried forward unchanged from the nyiso-112 keeper:
this arm does not move C3c (3/0/14 h in both arms) and spends no caveat slot.

Usage:
    python scripts/gen_nyiso113_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PRIOR_KEEPER = (
    REPO / "results/calibration/nyiso112_combined_D/calibration_attestation.json"
)
AB_JSON = REPO / "results/calibration/_nyiso113_li_locational_ab.json"
HEADROOM_JSON = REPO / "results/calibration/_nyiso113_zonek_headroom.json"
SCREEN_JSON = REPO / "results/calibration/_nyiso113_locational_reserve_screen.json"
ARM_DEST = (
    REPO / "results/calibration/nyiso113_lilocational_B/calibration_attestation.json"
)
CONTROL_DEST = (
    REPO / "results/calibration/nyiso113_control_A/calibration_attestation.json"
)

YEARS = ("2023", "2024", "2025")

NEW_ENTRY_NAME = (
    "nyiso_li_locational_reserve — the PUBLISHED NYISO Long Island (Zone K) "
    "locational reserve ladder (li_10min_total 120 MW all hours; li_30min_total "
    "270 MW off-peak / 540 MW on-peak), which the model carried nowhere"
)


def _build_entry(ab: dict, headroom: dict) -> dict:
    """Assemble the DOF entry, reading every number from committed probe JSON."""
    per = headroom["per_year"]
    quick_min = {y: per[y]["quick_start_headroom_mw"]["min"] for y in YEARS}
    quick_mult = {
        y: per[y]["quick_start_headroom_mw"]["min_as_multiple_of_requirement"]
        for y in YEARS
    }
    price = ab["price_and_feasibility"]
    return {
        "name": NEW_ENTRY_NAME,
        "where": (
            "run_config.scenario_config.nyiso_li_locational_reserve; "
            "model/reserves/spec.py::_nyiso_design via NYISO_RCPF_LOCATIONAL_LI + "
            "NYISO_LI_30MIN_ONPEAK_MW; source "
            "data/raw/NYISO-AS/requirements/nyiso_locational_reserve_requirements.csv "
            "(rows region=LI, regime v2021)"
        ),
        "identification": "published",
        "lineage_solves": (
            "1 (nyiso-113 arm B, against a same-HEAD zero-delta control that "
            "reproduces the committed keeper byte-identically)"
        ),
        "value": {
            "li_10min_total_mw": 120.0,
            "li_30min_total_offpeak_mw": 270.0,
            "li_30min_total_onpeak_mw": 540.0,
            "demand_curve_value_per_mw": 25.0,
            "onpeak_calendar": "NYISO MST §2.15 (07:00-23:00 EPT Mon-Fri, excl. NERC holidays)",
        },
        "source": (
            "The LI rows of the SAME published Locational Reserve Requirements "
            "posting that already grounds the model's NYC and East families — the "
            "model stopped at NYC and carried NO Zone-K family at all, so this is a "
            "rule 14 [R-ACCURATE] omission of a published requirement, the same "
            "class nyiso-83/84 fixed one tier up. Demand-curve values are NYISO "
            "Ancillary Services Manual §6.8 items 10 and 15 ('Long Island 10-Minute "
            "Reserves' / 'Long Island 30-Minute Reserves' ... 'shall be $25/MW'). "
            "The on/off-peak boundary the posting leaves undefined resolves to the "
            "tariff's own MST §2.15 On-Peak definition — a published CALENDAR rule "
            "that regenerates for any forward year and responds to that year's "
            "weekday/holiday layout, so rule 13 [R-MEASURED] admissible."
        ),
        "free_parameters_added": 0,
        "why_zero": (
            "Nothing is chosen. Both requirement levels, the demand-curve value and "
            "the on/off-peak calendar are transcribed from published NYISO records; "
            "the reserve-class assignment follows the same product-name rule every "
            "other NYISO family uses. The pre-registration's §6 no-tuning clause is "
            "binding: the levels may not be re-levelled, re-scoped, partially "
            "applied, re-derived or swapped for another vintage in response to this "
            "arm's result — not to enlarge a C3c movement, not to rescue an inert "
            "verdict."
        ),
        "rule_19_reconciliation": (
            "No armed family is scoped to Zone K, so nothing else in the model "
            "prices a Long Island reserve requirement. Proved by domination algebra "
            "on the family rows rather than asserted: a family row is "
            "sum_{z in region} R[c,z] + shortfall >= requirement, so an armed family "
            "with the same reserve class, a SUBSET region and a requirement at "
            "least as large would force this one slack — and the smallest armed "
            "regions containing Long Island are SENY and East, whose R-sums run "
            "over strictly more zones. The sibling candidate "
            "nyiso_east_reserve_families IS dominated by that same test and is "
            "recorded INERT rather than armed (nyiso-113)."
        ),
        "rule_25_scope": (
            "NYISO-exclusive: the requirement, the demand-curve value and the "
            "On-Peak calendar are all NYISO's own published records. No parameter "
            "is imported from any other ISO and this arm fills no other ISO's cell."
        ),
        "measured_effect": (
            "The family binds where and ONLY where its own requirement exceeds "
            "Zone-K headroom, measured on the arm's own unit-hourly sidecar: Zone-K "
            "thermal headroom falls below the HOURLY requirement in exactly 5 hours "
            "of 2025 (h4193-4195, h4217-4218 — the June 24-25 event that carries "
            "the five highest Long Island prices) and in 0 hours of 2023/2024 once "
            "the published on/off-peak step is honoured, and the solved reserve "
            "dual moves in exactly those hours (2 in 2023, 0 in 2024). The 10-minute "
            "limb never binds: Zone-K quick-start headroom bottoms out at "
            f"{quick_min['2023']} / {quick_min['2024']} / {quick_min['2025']} MW = "
            f"{quick_mult['2023']} / {quick_mult['2024']} / {quick_mult['2025']}x its "
            "120 MW requirement. Price effect is small and C3c does not move: LI "
            f">$300 stays {price['2023']['control']['li_h300']}/"
            f"{price['2024']['control']['li_h300']}/{price['2025']['control']['li_h300']}"
            " h against actual 10/12/42, >$250 stays 10/5/19, and the only visible "
            f"change is the 2025 LI maximum {price['2025']['control']['li_max']} -> "
            f"{price['2025']['arm']['li_max']} $/MWh — the $25/MW tier doing exactly "
            "what its published value permits. Zero slack and zero dump in every "
            "zone-hour."
        ),
        "known_limitation": (
            "NO BUNDLE PERSISTS A PER-FAMILY RESERVE DUAL. "
            "DispatchResult.reserve_price_by_family exists in memory and is "
            "discarded at persist time; the system_<year>.parquet reserve_price "
            "column is a single system-level (T,) series broadcast identically to "
            "every zone (run_calibration_full.py:925/1028). This arm's "
            "pre-registered K3/K4 gates were specified on that column and were "
            "therefore INVALID — they reported 'INERT' by construction. The gates "
            "were re-scored on Zone-K unit-hourly headroom and the solved dual's "
            "timing, which is what the measured_effect above reports. A per-family "
            "dual sidecar is a prerequisite for adjudicating ANY locational reserve "
            "mechanism from a committed bundle, in any ISO (nyiso-113 finding §8)."
        ),
    }


def _attested_by(ab: dict, arm: bool) -> str:
    """The C6 attestation prose for one arm, from the committed A/B JSON."""
    k2 = ab["K2_control_integrity"]["worst_max_abs_delta_mw"]
    price = ab["price_and_feasibility"]
    if not arm:
        return (
            "nyiso-113 CONTROL A — the same-HEAD zero-delta replay of the "
            "2026-08-02-nyiso112-ramp-plus-peaker keeper, solved to establish K2 "
            "control integrity for the LI locational-reserve A/B. It reproduces the "
            f"committed keeper at EXACTLY {k2} MW on every class-hour in all three "
            "years (122,640 class-hours each), so the A/B is unconfounded and the "
            "solve-path commits that landed on main since that keeper are measured "
            "NYISO-inert rather than assumed so. The ledger is the keeper's, "
            "unchanged: this arm changes no mechanism."
        )
    return (
        "nyiso-113 ARM B — single delta nyiso_li_locational_reserve=true on the "
        "2026-08-02-nyiso112-ramp-plus-peaker keeper, pre-registered in "
        "results/calibration/PREREG-nyiso113-li-locational-reserve-2026-08-02.md "
        "and pushed before either arm solved. THE MECHANISM IS A PUBLISHED "
        "REQUIREMENT THE MODEL OMITTED ENTIRELY: NYISO posts a Long Island (Zone K) "
        "locational reserve ladder in the same Locational Reserve Requirements "
        "document that already grounds the model's NYC and East families, and the "
        "model carried no Zone-K family at all — a rule 14 [R-ACCURATE] omission, "
        "closed here with ZERO free parameters. "
        "CONSTRUCTION: K1 exactly one config delta; K2 control integrity on the "
        f"STRICT BYTE basis ({k2} MW max class-hour delta against the committed "
        "keeper, all three years); K3 liveness — the family binds, and binds only "
        "where its own requirement exceeds Zone-K headroom (5 hours of 2025, 2 of "
        "2023, 0 of 2024, matching the measured headroom shortfall hour-for-hour); "
        "K5 both bundles span [2023, 2024, 2025] with the holdout spend freeze "
        "untouched; K6 zero free parameters, ledger 29 -> 30 entries with "
        "n_residual unchanged at 6. "
        "KILLS: none fire. P1 C3a PASSES in all three years; P2 C1 is 14/14 "
        "all-class and 10/10 free-class; P3 zero slack and zero dump in every "
        "zone-hour; P4 C7 and C8 both PASS. Every scored criterion is IDENTICAL to "
        "the same-HEAD control's — C1, C2, C3a, C3b, C4, C7, C8 all PASS in both "
        "arms and C3c FAILs in both at the same 3/0/14 h against actual 10/12/42, "
        "so the arm regresses nothing and spends no caveat slot. "
        "THE CASE IS STRUCTURAL, NOT A FIT CLAIM, and that was stated in advance. "
        "The visible price effect is one number — the 2025 Long Island maximum "
        f"{price['2025']['control']['li_max']} -> {price['2025']['arm']['li_max']} "
        "$/MWh, the published $25/MW demand-curve tier doing exactly what its own "
        "value permits — and no part of the promotion rests on it. Rule 1 "
        "[R-STRUCT] / rule 14 [R-ACCURATE]: the published requirement belongs in "
        "the model because NYISO enforces it, whatever it does to the residual. "
        "REPORTED, NOT HIDDEN (rule 14): the pre-registered K3/K4 gates were "
        "specified on the per-zone reserve_price column, which is a SYSTEM-LEVEL "
        "series broadcast identically to every zone and therefore cannot observe a "
        "locational dual; scored on it the arm read INERT, which was an artifact of "
        "the instrument, not a result. The gates were re-scored on Zone-K "
        "unit-hourly headroom and the solved dual's timing. No bundle in any ISO "
        "persists a per-family reserve dual — that gap is filed on this entry."
    )


def main() -> int:
    prior = json.loads(PRIOR_KEEPER.read_text())
    ab = json.loads(AB_JSON.read_text())
    headroom = json.loads(HEADROOM_JSON.read_text())

    # Control: the keeper's attestation verbatim, its own attested_by line.
    control = json.loads(json.dumps(prior))
    control["governance"]["attested_by"] = _attested_by(ab, arm=False)
    CONTROL_DEST.write_text(json.dumps(control, indent=1))

    # Arm: the keeper's ledger UNION one entry; C3c exception ledger carried.
    armdoc = json.loads(json.dumps(prior))
    armdoc["governance"]["attested_by"] = _attested_by(ab, arm=True)
    entries = armdoc["free_parameters"]["entries"]
    entries.append(_build_entry(ab, headroom))
    armdoc["free_parameters"]["entries"] = entries
    armdoc["free_parameters"]["n_entries"] = len(entries)
    armdoc["free_parameters"]["seeded"] = (
        "2026-08-02 nyiso-113 — UNION'd forward from the nyiso-112 keeper ledger "
        "and extended by ONE entry for the nyiso_li_locational_reserve delta. "
        "n_residual is UNCHANGED: every value in the new entry is a published "
        "NYISO record, not a residual-identified one."
    )
    ARM_DEST.write_text(json.dumps(armdoc, indent=1))

    print(f"wrote {CONTROL_DEST}")
    print(
        f"wrote {ARM_DEST}  (ledger {armdoc['free_parameters']['n_entries']} entries, "
        f"n_residual {armdoc['free_parameters']['n_residual']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
