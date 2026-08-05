"""Generate the ercot-168 arm attestation from the ercot167 keeper base.

``results/calibration/ercot168_yearcurves_B`` is the ercot167 keeper recipe
plus ONE mechanism delta — ``coal_perplant_offer_yearly=true`` (the matrix
§5.1 item-12 per-year 2023 re-identification of the armed
``coal_perplant_offer_curves``, owner-adjudicated 2026-08-05 OPTION A) — so its
attestation is the committed ercot167 attestation with: (a) one ADDED
measured/physical DOF-ledger entry (n_scalars 0, ``free_parameters_added: 0``;
every curve a verbatim submitted object from the delivery-2023 SCED corpus, the
windows the data's own modal day-majority dominance, rule 23); (b) the
``coal_perplant_offer_curves`` base entry's declared-extrapolation note RETIRED
for 2023 by measured replacement (the ercot-157 corpus re-upload dissolved its
"no 2023 SCED exists" premise — the precommit's stated DOF-ledger consequence);
(c) the governance block re-attested for this run; (d) the three rubric-v3.0
``price_tail`` model-class exceptions entries CARRIED FORWARD with magnitudes
confirmed at THIS run's counts (identical: the arm moves no tail hour).

Reads committed artifacts only; no solve. Run:
    python scripts/gen_ercot168_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "results/calibration/ercot167_socreserve_B/calibration_attestation.json"
DEST = REPO / "results/calibration/ercot168_yearcurves_B/calibration_attestation.json"

# Arm tail counts are byte-identical to the keeper's (G-BIT: 2024/25 sidecars
# sha256-identical; 2023 tail 61 h unchanged A->B), so the magnitudes carry.
MAGS = {
    2023: "model 61 h vs actual RT 181 h > $200/MWh (0.34x; band [0.5x, 2.0x])",
    2024: "model 25 h vs actual RT 53 h > $200/MWh (0.47x; band [0.5x, 2.0x])",
    2025: "model 3 h vs actual RT 31 h > $200/MWh (|delta| 28 > small-count 10)",
}

NEW_ENTRY = {
    "name": "coal_perplant_offer_yearly (per-year 2023 windowed measured TPO curves)",
    "where": (
        "constants.COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO via "
        "run_config.scenario_config.coal_perplant_offer_curves_yearly; applied in "
        "fleet.legacy_bins.apply_coal_tranches (year-present branch; a year absent "
        "from the table falls through to the armed static curves bit-identically "
        "- verified by kill gate G-BIT, sha256 over all twelve 2024/25 hourly "
        "sidecars)"
    ),
    "identification": "measured-physical",
    "lineage_solves": "3 solves (ercot-168: 2023-only probe + full-span A/B)",
    "n_scalars": 0,
    "source": (
        "each plant's per-(month x hour-window) modal 60-Day SCED Submitted TPO "
        "supply curve from the delivery-2023 corpus (data/raw/ercot/SCED/, 315 "
        "publication-month shards, delivery = filename - 2; 731,947 online CLLIG "
        "rows across 365 days) - verbatim submitted conduct at the corpus's own "
        "hourly submission grain under the mode's strict day-majority (>0.5 of "
        "the month's live days) stability license, CPT->CST converted at "
        "derivation; frozen scripts/data/derive_coal_perplant_offer.py --year "
        "2023; provenance data/raw/_processed-legacy/"
        "coal_perplant_offer_curves_2023_ERCOT.json (admitted AND refused cells "
        "with day-shares - the ~15 (0.5,0.55] boundary cells disclosed); "
        "ercot-168, chartered as matrix 5.1 item 12, owner-adjudicated OPTION A "
        "2026-08-05"
    ),
    "note": (
        "re-derive trigger is the delivery-year corpus landing only (rule 23: "
        "the ercot-157 re-upload IS the cited data change), never a residual; "
        "zero new DOF - same modal derive as the armed static mechanism, fed the "
        "year's own rows; the Aug-Oct Oak Grove $60-class overnight repricing is "
        "CONDUCT, not commodity (no measured fuel series moves at any offer "
        "step; no commodity backing claimed - precommit 1f), and 2024/2025 "
        "identification is UNTOUCHED (table carries only 2023). Identification "
        "record: docs/PRECOMMIT-ercot168-coal-perplant-year-curves-2026-08-05.md "
        "(gates pre-registered before any solve) + results/calibration/"
        "FINDING-ercot168-coal-perplant-year-curves-2026-08-05.md."
    ),
}

RETIRE_OLD = (
    "the 2023 application is an extrapolation (no 2023 SCED exists)",
    "the 2023 application WAS a declared extrapolation, RETIRED BY MEASURED "
    "REPLACEMENT at ercot-168 (the ercot-157 delivery-2023 corpus re-upload "
    "dissolved the 'no 2023 SCED exists' premise; 2023 now carries its own "
    "year's measured curves via coal_perplant_offer_yearly, and 2024/25 keep "
    "this entry's identification unchanged)",
)


def main() -> None:
    """Emit the ercot168 arm attestation from the committed ercot167 base."""
    att = json.loads(BASE.read_text())
    fp = att["free_parameters"]
    assert not any(e.get("name") == NEW_ENTRY["name"] for e in fp["entries"]), (
        "entry already present"
    )
    # (b) retire the declared-extrapolation clause on the base per-plant entry.
    hits = 0
    for e in fp["entries"]:
        if "coal_perplant_offer_curves" in e.get("name", ""):
            assert RETIRE_OLD[0] in e["note"], "expected the extrapolation clause"
            e["note"] = e["note"].replace(RETIRE_OLD[0], RETIRE_OLD[1])
            hits += 1
    assert hits == 1, f"expected exactly one base entry, found {hits}"
    fp["entries"].append(NEW_ENTRY)
    fp["n_entries"] = len(fp["entries"])
    gov = att["governance"]
    gov["attested_by"] = (
        "ercot-168 2026-08-05 (KEEPER CANDIDATE - surfaced for owner adjudication, "
        "NOT self-promoted) - the ercot167 keeper recipe with ONE delta: "
        "coal_perplant_offer_yearly=true (matrix 5.1 item 12, owner-adjudicated "
        "OPTION A 2026-08-05: a rule-14/23 data-vintage fix of the armed "
        "coal_perplant_offer_curves K mechanism, whose ERCOT-143 closure premise "
        "'no 2023 SCED exists' was dissolved by the ercot-157 corpus re-upload; "
        "same modal derive, fed the year's own rows, zero new DOF). ALL SEVEN "
        "pre-registered gates GREEN (docs/PRECOMMIT-ercot168-coal-perplant-year-"
        "curves-2026-08-05.md, committed before any solve): G-BIT 2024+2025 "
        "byte-identical A->B (12/12 sidecar sha256s); G-TGT C7 2023 COAL_LIGNITE "
        "cv_ratio 0.331 -> 1.193, clearing the >=0.5 gate with G-SHAPE profile_r "
        "0.897 -> 0.976; G-NEWROWS D-1 failing rows 1 -> 0 (COAL_PRB improves "
        "0.737 -> 0.958); G-NOREG C3a-2023 -32.24 -> -32.23 (+0.01pp), C3b-2023 "
        "0.6026 -> 0.6043 (+0.0017, inside +/-0.02); G-SPUR 3 -> 3; G-SHED "
        "4 -> 4. The 2023 C7 protective FAIL - the determination's only "
        "protective-tier blocker - is CLOSED by the year's own measured conduct: "
        "the LP now backs Oak Grove down to its mustrun floor on ordinary "
        "overnight LMPs exactly as SCED did (the measured Aug-Oct two-shift, "
        "executed through price formation; the Aug 15-19 scarcity-night pause "
        "reproduces endogenously). Zero new free parameters (n_entries 12 -> 13, "
        "n_residual UNCHANGED at 6 - the added entry is measured-physical); the "
        "base per-plant entry's declared-extrapolation note is RETIRED by "
        "measured replacement. LOYO (rule 22): the identification is per-year by "
        "construction - the 2023 table consumes only 2023 rows and 2024/25 are "
        "G-BIT byte-identical - so leave-one-year-out reduces to the per-year "
        "gate table, which is green in every year."
    )
    exceptions = att.get("exceptions", [])
    assert len(exceptions) == 3, "expected the three model-class entries"
    for e in exceptions:
        e["magnitude"] = MAGS[int(e["year"])]
        e["reason"] += (
            " CARRIED ONTO THE ercot-168 CANDIDATE (counts UNCHANGED by the arm: "
            "61/25/3 - the year-curve repricing is deep inframarginal in every "
            "actual tail hour, exactly as the model-class limitation predicts)."
        )
    DEST.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {DEST.relative_to(REPO)} (n_entries {fp['n_entries']})")


if __name__ == "__main__":
    main()
