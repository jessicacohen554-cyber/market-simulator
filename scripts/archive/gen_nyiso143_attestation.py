"""Emit the nyiso-143 arm's ``calibration_attestation.json`` (C6 governance gate).

The nyiso-143 arm is the incumbent keeper's recipe with **one** field flipped —
``nyiso_li_tsl_n11_security`` False -> True — so the NYC->Long_Island HB14-21
import cap reads NYISO's published **N-1-1 Transmission Security Limit**
(940 MW) instead of the Locality Import Limit, which is that same limit **minus
a 660 MW generation loss-of-source the model already carries twice elsewhere**.

Unlike nyiso-142 this IS a mechanism change, so the attestation it derives from
the incumbent is updated in four places rather than three:

1. ``governance.attested_by`` / ``note`` / ``residuals_note`` — what this run
   is, why it is admissible, and (stated against interest) what it costs;
2. the ``price_tail`` exceptions, **rewritten not merely re-measured** — the
   2023 miss FLIPS DIRECTION (over- to under-production) and 2025 moves from
   PASS to FAIL, so inheriting the incumbent's rationale would misdescribe the
   miss being ledgered;
3. ``config_drift_vs_incumbent`` — exactly one differing field, named;
4. ``free_parameters`` — one new DOF-ledger ENTRY for the armed bound, carrying
   its published identification. ``n_residual`` is UNCHANGED: a published
   number identified from a primary document is not a residual-fitted one.

THE GENERATOR IS THE SOURCE OF TRUTH: editing the emitted JSON by hand is
reverted by the next run of this script.

Usage:
    python scripts/gen_nyiso143_attestation.py \\
        --bundle results/calibration/nyiso143_n11tsl_arm \\
        --c3c 2023=2/10 2024=0/13 2025=5/42
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
INCUMBENT = REPO / "results" / "calibration" / "nyiso142_stackdup"

_ATTESTED_BY = (
    "nyiso-143 arm (Zone-K published N-1-1 transmission security limit, "
    "nyiso_li_tsl_n11_security)"
)

_NOTE = (
    "MECHANISM CHANGE, ZERO NEW FREE PARAMETERS (rule 21 [R-DOF]), ONE "
    "DIFFERING CONFIG FIELD. The NYC->Long_Island HB14-21 import cap now reads "
    "NYISO's PUBLISHED Zone-K N-1-1 Transmission Security Limit of 940 MW, "
    "stated in TABLE 1 note 2 of the Locality Bulk Power Transmission "
    "Capability Reports IDENTICALLY across the 2024-25, 2025-26 and 2026-27 "
    "editions, instead of the Locality Import Limit — which is that same "
    "published limit MINUS a 660 MW generation loss-of-source that the model "
    "ALREADY CARRIES TWICE elsewhere. Rule 14 [R-ACCURATE]: this swaps one "
    "published number for another and removes a double count; it fits nothing. "
    "Rule 13 [R-MEASURED]: a published interface limit is a physical/market "
    "INPUT with an exact forward analogue — the same report is issued for "
    "every capability year — never an outcome fed back to move a score. "
    "Rule 21: the value is READ from a primary document, so it enters the DOF "
    "ledger as a published entry and n_residual is UNCHANGED. "
    "PRE-REGISTERED BEFORE EITHER SOLVE at "
    "results/calibration/PREREG-nyiso143-zone-k-transfer-bound-2026-08-18.md; "
    "A/B over 2023+2024+2025 in one bundle (rule 16), years sequential "
    "(rule 12), BOTH arms registered (rule 15) as "
    "2026-08-18-nyiso-143-control and 2026-08-18-nyiso-143-n11tsl-arm. "
    "ALL SIX PRE-REGISTERED KILL GATES ARE SILENT, K6' INCLUDED — the "
    "owner-adopted successor to the K6 that killed this lever's bare form at "
    "nyiso-130. K6' escalated on the pre-registered forced-share rise "
    "(downstate reliability_floor x ST_GAS 0.169->0.185 / 0.190->0.222 / "
    "0.123->0.138) and CLEARED BOTH LEGS: zero NEW D-4 failures in the arm (it "
    "REMOVES three, including Port Jefferson from the gas commitment bridge in "
    "2024 and 2025) and zero new D-1 misses. Rule 28(a) is satisfied three "
    "times over versus nyiso-130: the CONTROL changed (nyiso-140 removed the "
    "plant absorbing 72.6 % of the very floor K6 fired on; nyiso-142 corrected "
    "the 2025 benchmark), the GATE changed (K6 -> K6', adopted at nyiso-140 "
    "§6.3 precisely because 'K6 cannot adjudicate any import-relief lever'), "
    "and K6' leg (a) became NON-VACUOUS for the first time via the D-4 "
    "per-unit conduct rider shipped in the same session."
)

_RESIDUALS_NOTE = (
    "STATED AGAINST INTEREST, AND IT IS THE REASON THIS PROMOTION NEEDED AN "
    "OWNER RULING. The armed bound COSTS the C3c scarcity tail: 21 -> 2 h "
    "(2023), 3 -> 0 h (2024) and 24 -> 5 h (2025) against RT actuals 10/13/42, "
    "so a criterion that missed in two years now misses in three and 2025 goes "
    "PASS -> FAIL. NO OTHER GATED CRITERION REGRESSES — C1/C2/C3a/C3b/C4/C8 "
    "PASS in both arms, mean LMP moves by at most $0.26/MWh, and 2023 C3a "
    "IMPROVES from +9.6 % to +9.0 %, away from the band edge. "
    "THE PROMOTION IS NOT A FIT CLAIM AND MUST NOT BE READ AS ONE: it rests on "
    "rule 1 [R-STRUCT] and rule 14 [R-ACCURATE] — a published input replacing a "
    "netted estimate stays in EVEN THOUGH it makes the residual worse — plus "
    "the owner's own promote criteria, which charter D2 and nyiso-130 §8 fixed "
    "as K1-K6 plus C1/C2/C3a/C3b/C4/C6/C8, 'WHATEVER C3c DOES'. "
    "WHAT THE COST BUYS IS THE DIAGNOSIS: 100 % of the model's C3c tail hours "
    "are Long_Island, in BOTH arms and EVERY year, so NYISO's entire modelled "
    "downstate scarcity formation WAS this one bound binding in 84.5/87.6/"
    "71.1 % of its design-condition hours. Under the published limit that "
    "occupancy falls to 24.8/21.3/6.8 % and the tail goes with it. Rule 14's "
    "own words apply exactly: the worse fit is a DISCOVERED BUG — the tight "
    "estimate was silently standing in for a downstate scarcity mechanism the "
    "model does not have — and the named successor is to build that mechanism, "
    "NOT to revert this input."
)

_DRIFT_NOTE = (
    "EXACTLY ONE differing scenario_config field versus the superseded keeper "
    "2026-08-17-nyiso-142-stackdup, verified by kill gate K1 over the full "
    "config: nyiso_li_tsl_n11_security False -> True. No other field, no "
    "coefficient, no table row."
)

_LEDGER_ENTRY = {
    "name": "nyiso_li_tsl_n11_security",
    "where": "run_config.scenario_config.nyiso_li_tsl_n11_security",
    "identification": "published",
    "lineage_solves": "2 solves (the nyiso-143 A/B pair; nyiso-130 pair, pruned)",
    "value": {"nyiso_li_tsl_n11_security": True, "implied_hb14_21_cap_mw": 940.0},
    "n_scalars": 0,
    "source": (
        "NYISO Locality Bulk Power Transmission Capability Report, TABLE 1 "
        "note 2 — the Zone-K N-1-1 Transmission Security Limit, identical "
        "across the 2024-25, 2025-26 and 2026-27 editions. Identification "
        "record: results/calibration/_nyiso130_li_tsl_identification.json "
        "(probe scripts/probes/_nyiso130_li_tsl_identification.py). The flag "
        "carries NO scalar of its own: it SELECTS which published number the "
        "existing cap reads, so n_scalars is 0 and n_residual is unchanged."
    ),
    "root_cause": (
        "CLOSED as an identification question — the number is published and "
        "the 660 MW loss-of-source it removes is double-counted elsewhere in "
        "the model. OPEN as a consequence: arming it exposes that the model "
        "has no downstate scarcity mechanism other than this bound "
        "(RESULT-nyiso143-zone-k-transfer-bound-ab-2026-08-18.md §4), which is "
        "this keeper's named successor object."
    ),
}

_NEW_OPEN_ITEMS = [
    "SUCCESSOR, opened BY this promotion and the reason it was accepted: THE "
    "DOWNSTATE SCARCITY MECHANISM. 100 % of the model's C3c tail hours are "
    "Long_Island in both arms and every year; with the published bound armed, "
    "in-window at-bound occupancy falls to 24.8/21.3/6.8 % and the model has "
    "no other mechanism that produces downstate scarcity. Same object "
    "nyiso-110 named from the reserve side (missing everyday reserve-price "
    "formation) and nyiso-124 located as a downstate/in-city price-formation "
    "gap. Evidence: RESULT-nyiso143-zone-k-transfer-bound-ab-2026-08-18.md.",
    "OPEN, pre-existing and present identically in both arms — THE nyiso-140 "
    "MEMBERSHIP REPAIR IS INCOMPLETE. reliability_floor_plant_exclusions fixed "
    "one MECHANISM, not the plant: nyiso_gas_commitment_bridge has no "
    "membership-exclusion channel and still floors 2517 Port Jefferson for "
    "0.1495 TWh in 2024 (34.6 % of that bridge leg's forced energy, 4,623 "
    "binding hours, meter 0.000 MW in 71.2 % of them), plus 7314, 8006 Roseton "
    "and 2480 Danskammer. Needs its own identification and its own A/B "
    "(rule 19 [R-ONE-MECH]). Surfaced by the D-4 per-unit conduct rider.",
    "OPEN, and it blocks TWO mechanisms at once — online_rho IS NEVER "
    "IDENTIFIED on this fleet. Its declared cap-weighted (pmax-pmin)/pmin "
    "basis is guarded by (pmin > 0), and only 4 of 851/849/705 LP rows carry "
    "pmin > 0 (the nuclear block), none quick-start eligible, so the value "
    "falls to the hard-coded 1.0 fallback in every year and in both the "
    "path-A and obligation branches. nyiso_synchronised_reserve is inert at "
    "rho >= 3.16 and binds in 90 % of hours at rho = 1.0, so arming it or its "
    "rule-19 sibling nyiso_incity_commitment_obligation today would put an "
    "unidentified scalar on a downstate commitment driver. Evidence: "
    "FINDING-nyiso143-online-rho-unidentified-2026-08-18.md.",
    "GOVERNANCE, filed not fixed: nyiso_iroquois_winter_spread is a "
    "solve-affecting ScenarioConfig field with 0 cells in all six matrix "
    "shards, visible only inside a sibling row's def head, and BOTH guards "
    "pass it. Remedy is the ercot-177 two-row split, out of a single-ISO "
    "lane's scope. Card: "
    "docs/DECISION-CARD-nyiso143-iroquois-taxonomy-gap-2026-08-18.md.",
]

_C3C_CLASSIFICATION = (
    "MODEL MISS (structural, UNDER-production) — ACCEPTED MODEL-CLASS "
    "LIMITATION. THE DIRECTION CHANGED AT THIS PROMOTION AND IS RESTATED "
    "RATHER THAN INHERITED: the superseded keeper's 2023 entry recorded an "
    "OVER-production miss (21 h against 10 h). Under the published Zone-K "
    "bound the model under-produces the tail in ALL THREE years, because the "
    "five-zone representation's only downstate scarcity channel was the "
    "tighter estimate. This is the SAME model-class limitation the NYISO "
    "ledger has carried since nyiso-100 — the five-zone representation cannot "
    "form in-city scarcity prices — now visible in its undisguised form."
)

_C3C_REASON = (
    'OWNER RULING, session nyiso-143, 2026-08-18, verbatim: "Is this a '
    "recommended keeper candidate? If so plz promote. If structural integrity "
    'improves but gates regress that may still be a keeper." The '
    "structure-over-gates clause IS the operative one here and IS needed, "
    "unlike at nyiso-142: C3c regresses in exchange for a published input "
    "replacing a netted estimate. It is ledgered under CLAUDE.md rule 22's "
    "C3c STANDING RULE — a LONE C3c failure with the governance gate passing "
    "is an auto-ledgered caveat that is REPORTED at full magnitude and does "
    "NOT downgrade the determination (rubric v3.3). C3c is the lone failing "
    "criterion on this run, so the rule's real guard holds: it can never mask "
    "a second defect. It still spends the single ledgerable slot and still "
    "reads CAVEAT, never PASS."
)


def _parse_c3c(items: list[str]) -> dict[int, tuple[int, int]]:
    """Parse ``YEAR=MODEL/ACTUAL`` hour counts from the verdict's own output."""
    out: dict[int, tuple[int, int]] = {}
    for item in items:
        year, _, counts = item.partition("=")
        model, _, actual = counts.partition("/")
        out[int(year)] = (int(model), int(actual))
    return out


def build(bundle: Path, c3c: dict[int, tuple[int, int]]) -> dict:
    """Return the arm's attestation, derived from the incumbent keeper's."""
    att = json.loads((INCUMBENT / "calibration_attestation.json").read_text())

    att["governance"]["attested_by"] = _ATTESTED_BY
    att["governance"]["note"] = _NOTE
    att["governance"]["residuals_note"] = _RESIDUALS_NOTE

    for exc in att.get("exceptions", []):
        year = int(exc.get("year", 0))
        if exc.get("criterion") != "price_tail" or year not in c3c:
            continue
        model, actual = c3c[year]
        ratio = (model / actual) if actual else float("nan")
        prior = str(exc.get("magnitude", "")).split(". Prior keeper")[0]
        exc["magnitude"] = (
            f"RE-MEASURED on this bundle (nyiso-143 treatment): model {model} h "
            f"> $300/MWh against RT actual {actual} h ({ratio:.2f}x). "
            f"Superseded keeper magnitude, lineage only: {prior}"
        )
        exc["classification"] = _C3C_CLASSIFICATION
        exc["reason"] = _C3C_REASON
        exc["carried_from"] = (
            "2026-08-17-nyiso-142-stackdup (NYISO ledger, nyiso-100 onward) — "
            "the LEDGER lineage is carried; the miss's DIRECTION and RATIONALE "
            "are restated for this run, not inherited."
        )
        exc["benchmark_basis_note"] = (
            "The RT ACTUAL side is untouched by this lever: C3c scores against "
            "the hub LMP series (actual_lmp_hourly_NYISO), which no transfer "
            "bound can move. The whole change is on the MODEL side and is a "
            "dispatch change. Per charter D2 the arm-vs-control DELTA is the "
            "quantity that may be relied on; absolute band membership remains "
            "conditional on the nyiso-139 clock repair, which has landed."
        )

    att["config_drift_vs_incumbent"] = {
        "note": _DRIFT_NOTE,
        "differing_fields": ["nyiso_li_tsl_n11_security"],
        "prior": att.get("config_drift_vs_incumbent", {}).get("prior", {}),
    }

    fp = att.get("free_parameters", {})
    entries = list(fp.get("entries", []))
    entries = [e for e in entries if e.get("name") != _LEDGER_ENTRY["name"]]
    entries.append(dict(_LEDGER_ENTRY))
    fp["entries"] = entries
    fp["n_entries"] = len(entries)
    fp["seeded"] = (
        "One NEW ledger entry versus 2026-08-17-nyiso-142-stackdup — the armed "
        f"published Zone-K bound (n_entries {len(entries) - 1} -> "
        f"{len(entries)}). n_residual is UNCHANGED at {fp.get('n_residual')}: "
        "the entry's identification is a primary published document, not a "
        "residual, and the flag carries no scalar of its own (n_scalars 0)."
    )
    att["free_parameters"] = fp

    att["_open_items"] = [*_NEW_OPEN_ITEMS, *att.get("_open_items", [])]
    return att


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; returns the process exit code."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True, type=Path)
    ap.add_argument(
        "--c3c",
        nargs="+",
        required=True,
        metavar="YEAR=MODEL/ACTUAL",
        help="C3c hour counts as reported by scripts/calibration_verdict.py",
    )
    args = ap.parse_args(argv)

    att = build(args.bundle, _parse_c3c(args.c3c))
    out = args.bundle / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
