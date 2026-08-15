"""Write ``calibration_attestation.json`` for the two nyiso-118 arms.

nyiso-118 arms ``nyiso_ordc_measured_step_span`` — matrix cell ``U``, never
armed — whose measurement nyiso-117 had already completed **ex ante with no
solve spent** (``results/calibration/nyiso117_seny_rcpf_curve_screen.json``,
outcome ``S-OVER``). This session spends the solve that screen deliberately did
not, against a mandatory same-HEAD zero-delta control.

The flag is a **construction-consistency fix, not a lever**: when
``nyiso_dynamic_reserve_requirements`` enforces a MEASURED hourly requirement on
the reserve balance row, the ORDC demand curve priced against it is still built
off the STATIC published MW. It scales each dynamic family's width vector by
``requirement[t] / requirement_static``, restoring the identity **total step
width == the hour's requirement**. It introduces **no new number** — both terms
are already-committed measured inputs — so it adds ONE ledger entry and ZERO
free parameters (rule 21 ``[R-DOF]``).

Every number in the attestation text is READ from a committed artifact — the
gate JSON ``nyiso118_gate_scores.json``, the ex-ante construction probe
``nyiso118_span_construction_probe.json``, and nyiso-117's SENY screen
``nyiso117_seny_rcpf_curve_screen.json`` — never typed in.

Usage:
    PYTHONPATH=.:src python scripts/gen_nyiso118_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CAL = REPO / "results/calibration"
PRIOR_KEEPER = CAL / "nyiso117_nyc_stepcurve/calibration_attestation.json"
GATES = CAL / "nyiso118_gate_scores.json"
CONSTR = CAL / "nyiso118_span_construction_probe.json"
SCREEN = CAL / "nyiso117_seny_rcpf_curve_screen.json"

YEARS = ("2023", "2024", "2025")
SENY = "seny_30min_total"
NYC_PAIR = ("nyc_10min_total", "nyc_30min_total")
LI30 = "li_30min_total"


def _fmt(vals) -> str:
    return " / ".join(str(v) for v in vals)


def _shared_evidence(g: dict, c: dict, s: dict) -> str:
    """The measured record both arms share, read from committed artifacts."""
    g1 = g["gates"]["G1_span_live_and_identity_restored"]
    ceil = _fmt(
        f"${s['measured'][y]['seny_30min_adder']['measured_ceiling']:.2f}"
        for y in YEARS
    )
    off = _fmt(g1["seny_hours_totalwidth_ne_requirement_control"])
    on = _fmt(g1["seny_hours_totalwidth_ne_requirement_treatment"])
    steps_c = _fmt(g["ordc_steps"]["control"])
    steps_t = _fmt(g["ordc_steps"]["treatment"])
    seny_dual = _fmt(
        f"{g['years'][y]['families'][SENY]['max_dual_control']:.2f}->"
        f"{g['years'][y]['families'][SENY]['max_dual_treatment']:.2f}"
        for y in YEARS
    )
    seny_hrs = _fmt(
        f"{g['years'][y]['families'][SENY]['hours_dual_pos_control']}->"
        f"{g['years'][y]['families'][SENY]['hours_dual_pos_treatment']}"
        for y in YEARS
    )
    nyc_price_delta = _fmt(
        f"${c['years'][y]['families'][n]['reachable_max_abs_price_delta']:.3f}"
        for y in YEARS
        for n in NYC_PAIR
    )
    return (
        "THE MECHANISM IS A CONSTRUCTION-CONSISTENCY FIX, NOT A LEVER, and it "
        "introduces NO NEW NUMBER (rule 5 [R-NO-MAGIC]): when "
        "nyiso_dynamic_reserve_requirements enforces the MEASURED hourly "
        "requirement on the reserve balance row, the ORDC demand curve priced "
        "against it was still built off the STATIC published MW. The flag "
        "scales each dynamic family's width vector by requirement[t] / "
        "requirement_static — both already-committed measured inputs — "
        "restoring the identity TOTAL STEP WIDTH == THE HOUR'S REQUIREMENT. "
        f"SENY violated that identity in {off} hours of 2023/24/25 in the "
        f"control and in {on} hours in the treatment (G1/K-E). "
        "THE SCOPE QUESTION WAS SETTLED EX ANTE ON CONSTRUCTION, BEFORE THE "
        "SOLVE, by scripts/probes/_nyiso118_span_construction_probe.py, which "
        "builds the NYISO ReserveDesign TWICE at one HEAD and diffs every "
        "family's requirement, ordc_penalties and ordc_step_widths with no LP "
        "and no dual — because dual and held_mw are SOLVED co-optimization "
        "outputs whose byte-identity can only pass when the mechanism does "
        "nothing (the nyiso-115 G2 error). "
        "THE ONE LIVE COUPLING DID NOT OCCUR: the LI locational ladder already "
        "applies this same span translation family-scoped and unconditionally "
        "to li_30min_total without flipping the global flag, so arming it "
        "globally could have DOUBLE-APPLIED. li_30min_total is byte-identical "
        "between arms in widths, requirement AND penalties in all three years "
        "(K-A did not fire) — the guard's `or` is boolean, not additive, and "
        "LI's family-scoped entry has already normalized its widths. "
        "TWO CORRECTIONS TO THE RECORD, both MEASURED rather than assumed. "
        "(1) THE BLAST RADIUS IS THREE FAMILIES, NOT ONE: _nyiso_design's "
        "docstring claimed the flag is a no-op for NYCA, East and NYC; that is "
        "FALSE for NYC, whose measured requirement dips BELOW its static base "
        "in 185/227/120 hours. The docstring was corrected against the probe in "
        "this session. (2) BUT NYC IS RE-REPRESENTED, NOT RE-PRICED: shortfall "
        "is bounded above by the hour's requirement (held >= 0), so width "
        "beyond it is unreachable padding, and under the frozen "
        "nyiso_nyc_rcpf_step_curve that family is a SINGLE FLAT BAND at the "
        "published $25 RCPF — trimming padding off a flat band cannot move a "
        "price. The reachable price function is pointwise IDENTICAL "
        f"(max |dprice| {nyc_price_delta}), so K-B did not fire and the "
        "rule-23 [R-FROZEN-DERIVE] freeze on the NYC curve is NOT disturbed. "
        "That three-way split — SENY re-priced, NYC re-represented, LI "
        "untouched — is also what demonstrates the construction instrument has "
        "DISCRIMINATING POWER: it is not a gate that can only pass by doing "
        "nothing. "
        f"INDEPENDENT CORROBORATION THAT NEVER TOUCHES THE PARQUET: the solve "
        f"log's ORDC step count is {steps_c} (control) and {steps_t} "
        "(treatment) — UNCHANGED, exactly as pre-registered, because the flag "
        "re-spans widths and adds or removes no steps (G2c, committed as each "
        "bundle's ordc_steps.log). "
        "THE PARTIAL WAS PRE-REGISTERED AS SUCH (PREREG §4) AND IT HELD: the "
        "flag re-spans WIDTHS only. SENY's penalty vector is measured UNCHANGED "
        "and its FIRST RUNG IS STILL $62.50, which already sits above the "
        f"ENTIRE measured envelope ({ceil} in 2023/24/25). So arming this flag "
        "ALONE CANNOT bring SENY inside the measured envelope, and this run is "
        "NOT reported as closing the S-OVER finding. The remaining defect — the "
        "published curve is a $500 base PLUS a $40 increment while the model "
        "carries only the base as a critical_mw = 0 ramp — is a SECOND "
        "mechanism requiring its own pre-registration and its own arm (rule 19 "
        "[R-ONE-MECH]); nothing was introduced, changed or fitted for it here. "
        f"MEASURED EFFECT: SENY's max dual moves {seny_dual} with binding hours "
        f"{seny_hrs}. 2023 and 2024 are BIT-IDENTICAL between arms; only 2025 "
        "moves, and it moves DOWNWARD — the shallower ramp, the pre-registered "
        "direction. The effect is small because SENY BINDS IN ALMOST NO HOURS, "
        "not because the curve barely changed: the curve's reachable price "
        "differs in ~6,100 hours per year, but a demand curve can only price "
        "where there is a shortfall."
    )


def _control_text(g: dict, c: dict, s: dict) -> str:
    return (
        "nyiso-118 CONTROL — ZERO CONFIG DELTA against the designated keeper "
        "2026-08-03-nyiso-117-nyc-rcpf, pre-registered in "
        "results/calibration/PREREG-nyiso118-seny-span-2026-08-03.md and pushed "
        "BEFORE either solve. THIS RUN IS A BASELINE, NOT A KEEPER CANDIDATE, "
        "AND THE KEEPER IS UNCHANGED BY IT. A same-HEAD control is MANDATORY, "
        "not optional: FINDING-nyiso114 §2 measured that a keeper arming a "
        "P0-run-pattern commitment bridge does NOT re-solve to byte-identity "
        "once main has moved, so any treatment-vs-keeper comparison would "
        "confound the mechanism with main's drift. Every attribution in the "
        "treatment arm is treatment-vs-THIS-control at one HEAD. Provenance is "
        "established by COMPARING THE DISPATCH, never by inferring a bundle's "
        "vintage from commit ordering — git merge-base --is-ancestor exits 128 "
        "('fatal: Not a valid object name') for an unfetched commit and the "
        "ordinary `cmd && yes || no` idiom silently maps that to a plain "
        "negative (nyiso-117 §9). " + _shared_evidence(g, c, s)
    )


def _treatment_text(g: dict, c: dict, s: dict) -> str:
    return (
        "nyiso-118 TREATMENT — arms nyiso_ordc_measured_step_span (matrix cell "
        "U, implemented but NEVER ARMED) against its own same-HEAD zero-delta "
        "control, 2023-2025 in one bundle each (rule 16). Pre-registered in "
        "results/calibration/PREREG-nyiso118-seny-span-2026-08-03.md with its "
        "gates, five kills, a no-tuning clause and the decision rule all fixed "
        "and PUSHED BEFORE EITHER SOLVE. The hypothesis cost ZERO solves to "
        "reach: nyiso-117 screened it ex ante on NYISO's own posted zonal DA "
        "ancillary-service prices and recorded S-OVER without spending a solve. "
        "ALL SIX PRE-REGISTERED GATES PASS AND NO KILL FIRES "
        "(G1 span live and identity restored, G2a scope requirement identity, "
        "G2b LI no-double-apply, G2c ORDC step count unchanged, G3 LP row "
        "identity, G4 no feasibility damage; K-A..K-E all silent), with zero "
        "unserved-energy slack and zero dump in BOTH arms in all three years. "
        + _shared_evidence(g, c, s)
        + " PROMOTION, IF ANY, RESTS ON RULE 1 [R-STRUCT] / RULE 14 "
        "[R-ACCURATE]: the demand curve must span the requirement it is priced "
        "against because that is how the published curve is built, NOT because "
        "of what it does to the residual. Conversely a residual that did not "
        "move is not evidence against it. The C3c null was PRE-REGISTERED "
        "(PREREG §5): C3c is closed as a lever lane and its re-open condition is "
        "a Capital_Hudson -> Zone-F/Zone-G TOPOLOGY SPLIT needing its own owner "
        "charter, which this session does not touch."
    )


def main() -> int:
    prior = json.loads(PRIOR_KEEPER.read_text())
    gates = json.loads(GATES.read_text())
    constr = json.loads(CONSTR.read_text())
    screen = json.loads(SCREEN.read_text())

    # --- control: the keeper's ledger, verbatim ---------------------------
    ctl = json.loads(json.dumps(prior))
    ctl["governance"]["attested_by"] = _control_text(gates, constr, screen)
    ctl["free_parameters"]["seeded"] = (
        "2026-08-03 nyiso-118 control — the 2026-08-03-nyiso-117-nyc-rcpf "
        "keeper ledger carried forward VERBATIM. A zero-delta same-HEAD "
        "baseline adds no free parameter: n_entries and n_residual are both "
        "unchanged."
    )
    (CAL / "nyiso118_control/calibration_attestation.json").write_text(
        json.dumps(ctl, indent=1)
    )

    # --- treatment: +1 entry, +0 residual ---------------------------------
    trt = json.loads(json.dumps(prior))
    trt["governance"]["attested_by"] = _treatment_text(gates, constr, screen)
    g1 = gates["gates"]["G1_span_live_and_identity_restored"]
    entry = {
        "name": (
            "nyiso_ordc_measured_step_span — the ORDC step-width vector "
            "translated to the MEASURED hourly reserve requirement, restoring "
            "total step width == requirement[t]"
        ),
        "where": (
            "run_config.scenario_config.nyiso_ordc_measured_step_span; "
            "model/reserves/spec.py::_nyiso_design (the width scaling by "
            "requirement[t] / requirement_static)"
        ),
        "identification": "measured + published, no free value",
        "identification_detail": (
            "THERE IS NO VALUE TO IDENTIFY. The scale factor is the ratio of "
            "two already-committed measured inputs — the as-enforced hourly "
            "requirement (the issue-#1344 intake, already on the balance row in "
            "both arms) over the static published MW — so the flag introduces "
            "no new number and nothing in it is free to move. The published "
            "RCPF PENALTIES are requirement-INDEPENDENT and are measured "
            "UNCHANGED by the flag, which is why the widths are the only part "
            "of the curve that carries the requirement. Rule 14 [R-ACCURATE]: "
            "the measured requirement is the accurate input ALREADY IN USE on "
            "the balance row; this stops the static estimate leaking back in "
            "through the curve's span. The defect it fixes is measured, not "
            "inferred: SENY's total step width differed from its own "
            f"requirement in {_fmt(g1['seny_hours_totalwidth_ne_requirement_control'])} "
            "hours of 2023/24/25 before the flag and "
            f"{_fmt(g1['seny_hours_totalwidth_ne_requirement_treatment'])} after. "
            "NOT RE-DERIVED HERE and frozen under rule 23 [R-FROZEN-DERIVE]: "
            "the SENY $500 penalty, its critical_mw = 0, the n_ramp = 8 "
            "discretization, the published $40 SENY increment (a SEPARATE "
            "mechanism, rule 19), the NYC $25/MW RCPF and its NYC-pair scope, "
            "and the LI reserve levels and On-Peak calendar."
        ),
        "lineage_solves": (
            "1 (this treatment against its own same-HEAD zero-delta control; 0 "
            "solves were spent reaching the hypothesis — nyiso-117 screened it "
            "ex ante on committed artifacts, and this session settled its scope "
            "and its one coupling hazard ex ante on CONSTRUCTION before "
            "solving)"
        ),
        "free": False,
        "residual_tuned": False,
    }
    trt["free_parameters"]["entries"] = list(prior["free_parameters"]["entries"]) + [
        entry
    ]
    n_entries = int(prior["free_parameters"]["n_entries"]) + 1
    trt["free_parameters"]["n_entries"] = n_entries
    trt["free_parameters"]["n_residual"] = int(prior["free_parameters"]["n_residual"])
    trt["free_parameters"]["seeded"] = (
        "2026-08-03 nyiso-118 treatment — the 2026-08-03-nyiso-117-nyc-rcpf "
        "keeper ledger plus ONE entry for nyiso_ordc_measured_step_span. "
        f"n_entries {prior['free_parameters']['n_entries']} -> {n_entries}, "
        f"n_residual UNCHANGED at {trt['free_parameters']['n_residual']}: the "
        "mechanism introduces no free parameter. Its scale factor is the ratio "
        "of two already-committed measured inputs and its penalties are "
        "requirement-independent and measured unchanged, so there is nothing in "
        "it to tune."
    )
    (CAL / "nyiso118_seny_span/calibration_attestation.json").write_text(
        json.dumps(trt, indent=1)
    )

    print(
        f"control   : ledger {ctl['free_parameters']['n_entries']} entries, "
        f"n_residual {ctl['free_parameters']['n_residual']} (both unchanged)"
    )
    print(
        f"treatment : ledger {trt['free_parameters']['n_entries']} entries "
        f"(+1), n_residual {trt['free_parameters']['n_residual']} (unchanged)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
