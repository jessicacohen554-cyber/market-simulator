"""Emit the nyiso-144 arm's ``calibration_attestation.json`` (C6 governance gate).

The nyiso-144 arm is the incumbent keeper's recipe with **one** field flipped —
``nyiso_gas_bridge_plant_exclusions`` False -> True — which gives the NYISO gas
commitment bridge the laid-up plant MEMBERSHIP correction that previously
existed only on the reliability floor. nyiso-140 repaired one *mechanism*
rather than the plant; this is the other half (rule 19 ``[R-ONE-MECH]``).

Derived from the incumbent (``nyiso143_n11tsl_arm``) and updated in four
places:

1. ``governance.attested_by`` / ``note`` / ``residuals_note`` — what this run
   is, why it is admissible, and (stated against interest) what it costs;
2. the ``price_tail`` exceptions — the MAGNITUDE is re-measured and found
   UNCHANGED (C3c is 2 / 0 / 5 h against RT actual 10 / 13 / 42 h,
   bit-identical to the incumbent's, because this arm touches commitment
   membership and not price formation), while the RATIONALE is **restated
   rather than inherited**. The incumbent's reads "C3c regresses in exchange
   for a published input replacing a netted estimate" — nyiso-143's trade-off,
   not this arm's, which regresses nothing. Carrying that sentence would assert
   a trade-off that did not happen, so the ledger lineage is carried and the
   reason is rewritten (the nyiso-143 generator's own discipline, applied in
   the opposite direction);
3. ``config_drift_vs_incumbent`` — exactly one differing field, named, verified
   by kill gate K1 over the full config;
4. ``free_parameters`` — one new DOF-ledger ENTRY for the membership artifact,
   carrying its measured identification. ``n_residual`` is **UNCHANGED**: the
   entry introduces no scalar at all (it is a plant-code set produced by a
   conduct test), and it is derived BLIND to the mechanism's own behaviour.

THE GENERATOR IS THE SOURCE OF TRUTH: editing the emitted JSON by hand is
reverted by the next run of this script.

Usage:
    python scripts/gen_nyiso144_attestation.py \\
        --bundle results/calibration/nyiso144_layup_arm
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INCUMBENT = REPO / "results" / "calibration" / "nyiso143_n11tsl_arm"
LAYUP_CSV = REPO / "data/raw/_processed-legacy/campd_bridge_layup_exclusions_NYISO.csv"

FIELD = "nyiso_gas_bridge_plant_exclusions"

ATTESTED_BY = (
    "session nyiso-144 (2026-08-18). ARM of the pre-registered bridge lay-up "
    "membership A/B (results/calibration/PREREG-nyiso144-bridge-layup-"
    "membership-2026-08-18.md, committed BEFORE either arm solved), against "
    "same-HEAD control 2026-08-18-nyiso-144-control. ALL SIX pre-registered "
    "kill gates PASS (scripts/probes/_nyiso144_layup_ab.py, "
    "results/calibration/_nyiso144_layup_ab.json)."
)

NOTE = (
    "MEMBERSHIP CORRECTION, not a level or window change. "
    "reliability_floor_plant_exclusions (nyiso-140, keeper) never reached "
    "nyiso_gas_commitment_bridge, so the same economically laid-up stations "
    "stayed floored by the other mechanism that floors the same class — "
    "rule 19 [R-ONE-MECH]'s 'enumerate what already floors the same class', "
    "one mechanism later. A plant in economic lay-up is idle in its own metered "
    "conduct while reading ~100 % available in the outage extract (lay-up is "
    "correctly not booked as a forced outage), so bridging it holds a "
    "mothballed boiler at minimum load across gaps it never operated in — "
    "rule 17 [R-FLOOR-WINDOW] verbatim. "
    "IDENTIFICATION (rules 13/23, source data only, no residual consulted): a "
    "plant qualifies iff its median CAMPD plant gross load is ZERO in every "
    "(year, 4-hour block) cell of 2023-2025 — the nyiso-140 criterion verbatim. "
    "The per-cell quantifier is what makes it a lay-up test rather than a "
    "low-capacity-factor test: on NYISO's own bridge population a POOLED median "
    "of zero also catches ordinary cyclers (Saranac P(on)=0.426, Port Jefferson "
    "P(on)=0.375), which are exactly the population a commitment bridge exists "
    "to hold together. The qualifying set stops at 18/18 zero cells and the "
    "nearest non-qualifier sits at 16/18. "
    "NOT CIRCULAR: the test reads only the meter and is computed WITHOUT "
    "reference to which plants the bridge floors or to any D-4 verdict, which "
    "is what makes its selection of 7 of the bridge's 8 D-4 unit-conduct "
    "FAILURES evidence rather than fitting. "
    "TWO PLANTS ARE DELIBERATELY NOT EXCLUDED, both named in the "
    "pre-registration BEFORE the solve so neither could be added after seeing a "
    "residual: 7314 (the eighth D-4 FAIL, 77.1 % of its floored hours metered "
    "at zero) does not qualify — it is a cycler the model's own P0 over-runs, so "
    "its forcing is an offer/economics defect and excluding it here would bury "
    "that error inside a membership list (rules 1/14); and 2517 Port Jefferson "
    "is excluded from the reliability FLOOR (whose always-on baseline it does "
    "not have) but stays in the BRIDGE population, which is keyed to detected "
    "runs it genuinely performs — its committed D-4 verdict on this mechanism "
    "is `pass` in all three years."
)

RESIDUALS_NOTE = (
    "STATED AGAINST INTEREST — WHAT THE ARM COSTS AND WHAT IT DOES NOT BUY. "
    "It buys NO fit improvement and was not expected to: across BOTH full "
    "calibration_verdict reports the ONLY difference is a SKIPPED, NON-GATED "
    "day-ahead diagnostic line (C3a da_diagnostic +6.7 -> +7.0 % in 2023, "
    "+0.3 -> +0.6 % in 2024, -0.6 -> -0.2 % in 2025). Every gated criterion is "
    "criterion-for-criterion and number-for-number IDENTICAL to the control: "
    "C1/C2/C3a/C3b/C4/C8 PASS, C3c FAIL at 2/0/5 h against RT actual 10/13/42 h "
    "— bit-identical to the incumbent, because this arm touches commitment "
    "membership and not price formation. "
    "WHAT IT DOES BUY IS LEGITIMACY, WHICH IS THE POINT (rule 1 [R-STRUCT]): "
    "the bridge stops manufacturing 0.1201 / 0.1406 / 0.3099 TWh of energy at "
    "plants whose own meter says they were mothballed, and the D-4 unit-conduct "
    "failure count falls from 17 to 3 with ZERO new failures. Every material "
    "class's forced share FALLS (ST_GAS 20.2->19.7 / 24.9->23.9 / 16.7->14.7 %; "
    "CC_REGULAR 4.8->4.4 / 2.6->2.4 / 1.9->1.8 %), so kill gate K6-prime did not "
    "even need to escalate — unlike nyiso-140, where the surviving bridge share "
    "rose. "
    "THE LIVENESS PREDICTION WAS PRE-REGISTERED AND NEARLY EXACT: the shed "
    "predicted from the control's own D-4 rows BEFORE either solve was 0.1186 / "
    "0.1396 / 0.3089 TWh against a +/-50 % band; the measured shed is 0.1201 / "
    "0.1406 / 0.3099 TWh — within 1.3 % in every year. "
    "NO NEW FREE PARAMETER: the artifact is a plant-code set, not a scalar, so "
    "n_residual is unchanged. "
    "OPEN AND NAMED, not fixed here: plant 7314's bridge over-run survives this "
    "arm by design and is an offer/economics successor object."
)


def _layup_rows() -> list[dict]:
    """Return the qualifying lay-up rows from the frozen artifact."""
    with LAYUP_CSV.open(newline="") as fh:
        return [
            r
            for r in csv.DictReader(fh)
            if str(r.get("laid_up", "")).strip().lower() in ("true", "1", "yes")
        ]


def build(bundle: Path) -> dict:
    """Return the arm's attestation, derived from the incumbent keeper's."""
    att = json.loads((INCUMBENT / "calibration_attestation.json").read_text())
    rows = _layup_rows()
    codes = sorted(int(r["plant_code"]) for r in rows)

    att["governance"]["attested_by"] = ATTESTED_BY
    att["governance"]["note"] = NOTE
    att["governance"]["residuals_note"] = RESIDUALS_NOTE

    # The C3c ledger LINEAGE is carried; its RATIONALE is restated, because the
    # incumbent's reads "C3c regresses in exchange for a published input
    # replacing a netted estimate" — nyiso-143's story, not this arm's. This arm
    # does not move C3c at all, so inheriting that sentence would assert a
    # trade-off that did not happen (the nyiso-143 generator's own discipline,
    # applied in the opposite direction).
    c3c = {2023: (2, 10), 2024: (0, 13), 2025: (5, 42)}
    for exc in att.get("exceptions", []):
        if exc.get("criterion") != "price_tail":
            continue
        year = int(exc["year"])
        model_h, actual_h = c3c[year]
        exc["magnitude"] = (
            f"RE-MEASURED on this bundle (nyiso-144 treatment): model {model_h} h "
            f"> $300/MWh against RT actual {actual_h} h "
            f"({model_h / actual_h:.2f}x). UNCHANGED from the superseded keeper "
            "2026-08-18-nyiso-143-n11tsl-arm, bit-identical in all three years."
        )
        exc["classification"] = (
            "MODEL MISS (structural, UNDER-production) — ACCEPTED MODEL-CLASS "
            "LIMITATION. Direction and magnitude are IDENTICAL to the superseded "
            "keeper's; this arm changes commitment membership, not price "
            "formation, and moves no gated criterion at all."
        )
        exc["reason"] = (
            "CARRIED, NOT RE-EARNED. The C3c miss is ledgered under CLAUDE.md "
            "rule 22's C3c STANDING RULE — a LONE C3c failure with the "
            "governance gate passing is an auto-ledgered caveat, REPORTED at "
            "full magnitude, that does not downgrade the determination (rubric "
            "v3.3). C3c is the lone failing criterion on this run, so the "
            "rule's real guard holds: it can never mask a second defect. "
            "THE nyiso-143 STRUCTURE-OVER-GATES CLAUSE IS NOT INVOKED HERE AND "
            "IS NOT NEEDED: that owner ruling bought a C3c regression in "
            "exchange for a published input, whereas this arm regresses "
            "NOTHING — across both full calibration_verdict reports the only "
            "difference is a SKIPPED, non-gated day-ahead diagnostic line. What "
            "this arm buys is legitimacy: 0.1201/0.1406/0.3099 TWh of "
            "manufactured floor energy removed from mothballed plants, and the "
            "D-4 unit-conduct failure count down from 17 to 3 with zero new "
            "failures."
        )
        exc["carried_from"] = (
            "2026-08-18-nyiso-143-n11tsl-arm (NYISO ledger, nyiso-100 onward) — "
            "the LEDGER lineage is carried and the magnitude is re-measured and "
            "found unchanged; the RATIONALE is restated for this run rather "
            "than inherited, because the incumbent's names a trade-off this arm "
            "does not make."
        )
        exc["benchmark_basis_note"] = (
            "The RT ACTUAL side is untouched by this lever: C3c scores against "
            "the hub LMP series (actual_lmp_hourly_NYISO), which no commitment "
            "membership change can move. The MODEL side is likewise unmoved — "
            "2/0/5 h in both arms."
        )

    att["config_drift_vs_incumbent"] = {
        "note": (
            "EXACTLY ONE differing scenario_config field versus the superseded "
            f"keeper 2026-08-18-nyiso-143-n11tsl-arm: {FIELD} False -> True. "
            "No other field, no coefficient, no table row. Verified by kill "
            "gate K1 over the FULL config (scripts/probes/_nyiso144_layup_ab.py): "
            "the only other meta delta is git_sha, and the sole commit between "
            "the two shas (800d475..684f6be) adds the control bundle's own "
            "artifacts and touches nothing under src/, scripts/run_*, "
            "scripts/lib/ or data/raw/."
        ),
        "differing_fields": [FIELD],
        "prior": att.get("config_drift_vs_incumbent", {}).get("prior", {}),
    }

    fp = att["free_parameters"]
    entry = {
        "name": FIELD,
        "kind": "measured membership set (no scalar)",
        "value": f"{len(codes)} EIA plant codes: {codes}",
        "identification": (
            "scripts/data/derive_campd_bridge_layup_exclusions.py over EPA CAMPD "
            "unit-level hourly grossLoad (data/raw/campd-unit-level), units "
            "summed to one PLANT series: a plant qualifies iff median(grossLoad) "
            "== 0 in EVERY (year, 4-hour block) cell of the pooled 2023-2025 "
            "window — the nyiso-140 criterion verbatim. Artifact "
            "data/raw/_processed-legacy/campd_bridge_layup_exclusions_NYISO.csv "
            "(+ _population.csv, the full 30-plant population with its cell "
            "counts, so the 18/18 vs 16/18 separation is auditable rather than "
            "asserted)."
        ),
        "n_scalars": 0,
        "residual_fitted": False,
        "note": (
            "Adds NO degree of freedom: the entry is a set of plant codes "
            "produced by a conduct test on source data, computed BLIND to the "
            "mechanism's own floor pattern and to every D-4 verdict. It "
            "re-derives only when its CAMPD source updates (rule 23 "
            "[R-FROZEN-DERIVE]) and regenerates for a forward year — a plant "
            "returning to service leaves the set on its own meter."
        ),
    }
    fp["entries"] = list(fp.get("entries", [])) + [entry]
    fp["n_entries"] = len(fp["entries"])
    # n_residual is deliberately NOT incremented: n_scalars == 0.
    return att


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--bundle", required=True, help="the arm bundle directory")
    args = ap.parse_args()
    bundle = Path(args.bundle)
    if not bundle.is_dir():
        print(f"no such bundle: {bundle}", file=sys.stderr)
        return 1
    att = build(bundle)
    out = bundle / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=1) + "\n")
    fp = att["free_parameters"]
    print(
        f"wrote {out}\n  DOF ledger: {fp['n_entries']} entries, "
        f"n_residual {fp['n_residual']} (UNCHANGED — the new entry has "
        f"n_scalars 0)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
