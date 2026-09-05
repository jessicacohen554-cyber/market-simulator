"""Generate the miso-202 A/B legs' calibration attestations from the keeper's.

The gen_miso186/187/188/198/200/201 pattern. Both legs are the miso-201 keeper
recipe re-solved, the arm carrying exactly one ZERO-DOF defect repair, so each
leg's attestation is the keeper's with a rewritten ``governance.attested_by`` and
this session's disclosures appended AT FULL MAGNITUDE; the arm additionally
carries ONE measured-identified ledger entry for the per-unit removal clip.

``n_residual`` is UNCHANGED, and in this case that claim is unusually easy to
audit: the arm introduces no quantity at all. It caps a sum at a bound the data
already carries (the unit's own capacity), so there is nothing that could have
been chosen differently — no threshold, no tolerance, no adjacency window.

Run this INSTEAD of ``scripts/build_dof_ledger.py``, which regenerates the ledger
from config and would drop the documented entries. It also exists because a
``--replay-bundle`` solve writes NO attestation at all, which is what made
miso-200's K-6 unscorable and its K-3/K-4 pass vacuously on the first scoring
run (FINDING-miso200, superseding addendum).

Usage:
    python3 scripts/gen_miso202_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "results/calibration/miso201_stbasis_B/calibration_attestation.json"
CONTROL = REPO / "results/calibration/miso202_control_A"
ARM = REPO / "results/calibration/miso202_unitclip_B"

# Filled from the scored A/B record so the disclosure quotes measured numbers
# rather than restating the PREREG's expectations.
GATES = REPO / "results/calibration/_miso202_ab_gates.json"

LEDGER_ENTRY = {
    "name": "unit_outage_per_unit_clip (boolean arm)",
    "where": (
        "ScenarioConfig.unit_outage_per_unit_clip -> the per-unit accumulation "
        "and ceiling in outages._unit_outage_factors_from_events. Threaded from "
        "config by data/fleet/arrays.py into unit_outage_derate_factors, "
        "unit_outage_short_derate_factors, unit_partial_outage_derate_factors "
        "and unit_layup_removed_fractions; deliberately NOT into "
        "unit_outage_maxgen_derate_factors, which does not share the accumulator "
        "and carries no boundary-day exposure."
    ),
    "identification": (
        "MEASURED, zero free parameters, and stronger than that: the arm "
        "introduces NO QUANTITY AT ALL. It caps each unit's cumulative removed "
        "MW at a bound the data already carries — that unit's own capacity, the "
        "same unit_capacity_mw the unclipped path divides by cap[bin] — so there "
        "is nothing here that could have been chosen differently. No threshold, "
        "no tolerance, no adjacency window, no date arithmetic, no per-plant "
        "enumeration (rule 24 [R-REGISTRY]). The invariant it enforces is not a "
        "modelling judgement but an accounting fact: one unit cannot be more "
        "than 100 % out of service. Rule 13 forward-regenerable in the strongest "
        "sense — it is a property of the accumulator rather than of any year's "
        "data, so it regenerates identically for a forecast year and responds to "
        "changed conditions exactly as the underlying windows do. MONOTONE BY "
        "CONSTRUCTION: a ceiling on a sum can only ever remove LESS, which is "
        "why the A/B could gate it (S-3) on every bin and hour rather than "
        "sampling."
    ),
    "evidence": (
        "_miso202_boundary_day_phase0.json, committed BEFORE the PREREG and "
        "before a line of mechanism code. THE DEFECT: "
        "outages.unit_outage_event_window reconstructs a day-granular extract "
        "row as [outage_start, outage_end + 1 day), so two windows of the SAME "
        "unit sharing a boundary date both cover that day while the accumulator "
        "SUMS row shares rather than unioning them — the unit's capacity is "
        "subtracted TWICE for 24 h. N-1 REPRODUCTION PASS on 589 bins across all "
        "three layers that share the accumulator (every reconstructed pre-clip "
        "share reproduces production's clip(1 - v, 0, 1) exactly). N-2 CENSUS: "
        "845 same-unit overlapping pairs (std5d 648, lay-up 197, short 0), and "
        "the overlap-length histogram is a SINGLE BIN AT EXACTLY 24.0 h, 845/845 "
        "— the fingerprint of the '+ 1 day' artifact and of nothing else, which "
        "is what makes this a defect rather than a judgement call. N-3: the clip "
        "restores 91.1 / 77.6 / 103.4 GWh of capability in 2023/2024/2025, "
        "reaching CC_REGULAR (55.9/17.3/50.2), ST_GAS (32.0/56.3/50.6), COAL, "
        "CC_CHP and ST_CHP — NOT the four steam bins miso-201 could see from its "
        "steam-scoped instrument, which sized the object at '24-72 h/yr per "
        "bin'. The built mechanism reproduces N-3 EXACTLY (91.133/77.570/103.414 "
        "GWh) and its availability delta is >= 0 at every bin-hour on MISO's real "
        "extracts (worst regression 0.00e+00). N-4, measured before the arm "
        "existed: only 1.4 % / 0.0 % / 1.4 % of the restored capability lands in "
        "the keeper's own top-1 % price hours, so C3a was expected to barely "
        "move and a favourable move would not have been evidence. N-5: the "
        "maxgen twin carries ZERO same-unit overlaps over 544 unit-series — its "
        "windows are already hour-granular — so its exclusion is a MEASUREMENT, "
        "not an assumption."
    ),
    "residual_dof": 0,
}


def build(dst: Path, armed: bool, gates: dict) -> None:
    d = json.loads(SRC.read_text())
    if armed:
        d["free_parameters"]["entries"].append(LEDGER_ENTRY)
        d["free_parameters"]["n_entries"] = len(d["free_parameters"]["entries"])

    leg = "ARM leg B (unit_outage_per_unit_clip=True)" if armed else "CONTROL leg A"
    d["governance"]["attested_by"] = (
        f"miso-202 A/B (2026-09-03), {leg}: control miso202_control_A vs arm "
        "miso202_unitclip_B, both MISO 2023+2024+2025 in one invocation, years "
        "sequential, solved in-session and never on CI (rule 12/16), both from "
        "the SAME committed keeper recipe (2026-09-02-miso-201-stbasis) via "
        "--replay-bundle so the delta is provably one ScenarioConfig field. "
        "Scored by scripts/probes/_miso202_ab_gates.py, COMMITTED BLIND with the "
        "PREREG before the mechanism existed and before either leg's numbers, "
        "and deliberately NOT importing _miso198_ab_gates: it orders "
        "kills-silent BEFORE inertness and measures inertness on VALUE MOVEMENT "
        "rather than criterion-status identity. It carries the miso-200 "
        "vacuous-pass refusal forward (K-3/K-4/K-6 report UNSCORED, never PASS, "
        "on empty diagnostics) and adds S-3, a MONOTONICITY VOID this lever "
        "earns: a ceiling on a sum can only ever remove LESS, so the arm's "
        "availability must be >= the control's on every bin, every hour and "
        "every layer, checked off the production loaders before either leg's "
        "dispatch matters. " + str(gates.get("verdict", "verdict pending"))
    )

    d.setdefault("disclosures", {})["miso202_ab"] = DISCLOSURE
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(d, indent=1))
    print(
        f"wrote {dst.relative_to(REPO)} "
        f"(n_entries={d['free_parameters']['n_entries']}, "
        f"n_residual={d['free_parameters']['n_residual']})"
    )


# Rewritten by the session once the pair is scored, so the disclosure quotes
# MEASURED numbers rather than restating the PREREG's expectations. The guard in
# __main__ refuses to write an attestation while this is still the placeholder —
# an attestation carrying placeholder text would be exactly the kind of
# unscorable artifact this script exists to prevent.
_PLACEHOLDER = "PLACEHOLDER"
DISCLOSURE = (
    "REPORTED AT FULL MAGNITUDE. (1) EVERY GATE IS SILENT AND NOTHING REGRESSES "
    "THAT IS GATED. S-0 control integrity PASS, BIT-IDENTICAL to the keeper "
    "across all 9 sidecars (max_abs_diff 0.0) — which is also the end-to-end "
    "proof that the field is byte-inert while off, a full solve carrying it "
    "reproducing the keeper exactly. S-1 exactly one ScenarioConfig field. S-2 "
    "live in both layers phase-0 said carry overlaps (std5d 31 bins gain, "
    "lay-up 12) and DEAD in the one it said does not (short 0) — a falsifiable "
    "phase-0 prediction confirmed against production. S-3 MONOTONICITY PASS on "
    "589 bins: ZERO bin-hours in which the arm removes more capacity than the "
    "control, worst regression exactly 0.000e+00. K-1 through K-5 all PASS. "
    "(2) K-1 HAS NO BAND EXIT ANYWHERE and every pre-registered cell moved "
    "within its stated headroom. THE NAMED RISK behaved exactly as predicted "
    "and is reported as adverse: CC_REGULAR-2024 +6.931 -> +6.942, i.e. "
    "+0.011 TWh further from zero against 1.069 TWh of headroom. The favourable "
    "cells: CC_REGULAR-2023 -3.434 -> -3.408 and CC_REGULAR-2025 -2.194 -> "
    "-2.177, both toward actual. ST_GAS is essentially unmoved (-3.512 -> "
    "-3.516, -7.488 -> -7.487, -6.681 -> -6.684) and the tightest cell on the "
    "board (ST_GAS-2024, 0.512 TWh from the edge) does not move materially. "
    "(3) THE ARM IS SMALL IN DISPATCH AND THIS IS STATED PLAINLY, NOT BURIED: "
    "the phase-0 capability bound was 91.1 / 77.6 / 103.4 GWh and the LP "
    "converted only a fraction of it, the largest C1 move being +0.026 TWh "
    "(CC_REGULAR-2023). The repair is justified as a DEFECT REPAIR, never as a "
    "residual improvement, and its size is not its argument. (4) C8 IS "
    "EFFECTIVELY UNCHANGED — ST_GAS forced share 0.1551/0.1529/0.2713 -> "
    "0.1553/0.1529/0.2714, deltas of +0.00014/+0.00002/+0.00010, all BELOW the "
    "pre-registered inertness epsilon of 0.0005 and far inside the 0.30 "
    "merchant budget. The PREREG named a C8 risk (the clip reduces the laid-up "
    "share, raising the must-run floor's clip basis); it did not materialise. "
    "(5) C3a FACE, reported and NEVER the justification (rule 1 [R-STRUCT]): "
    "2023 +0.1218 UNCHANGED, 2025 -12.3845 UNCHANGED, 2024 -4.5820 -> -4.6130 "
    "(-0.031 pp, slightly worse). This is what phase-0 N-4 predicted before the "
    "arm existed — only 1.4 %/0.0 %/1.4 % of the restored capability lands in "
    "the keeper's own top-1 % price hours — and the session's separate C3a "
    "anatomy explains WHY no outage-family repair can move it: C3a-2025 is "
    "entirely a missing scarcity TAIL, not a level miss. (6) K-3 D-4 conduct: "
    "ZERO new off-window binding and zero cleared. K-4 D-1 shape: zero "
    "PASS->FAIL. K-5: zero PASS->non-PASS on any scored record; the criterion "
    "status map is IDENTICAL and the determination is unchanged. (7) K-6 was "
    "UNSCORED on the first scoring pass because a --replay-bundle solve writes "
    "no attestation; diagnostics (D1=30, D2=23, D4=57 on BOTH legs) and these "
    "attestations were generated for both legs and the pair re-scored, so the "
    "miso-200 vacuous-pass trap stayed closed by construction rather than being "
    "discovered after the fact. (8) MAIN DRIFT MEASURED, NOT ASSUMED: both legs "
    "solve at fe641ebe while origin/main advanced during the session; the only "
    "drift touching src/ or the runners is a blank line in new_entry.py and "
    "additive output-only capacity-evolution ledger fields in runner.py that no "
    "decision reads and that backcast mode never reaches, so both legs remain "
    "one code state."
)


if __name__ == "__main__":
    if DISCLOSURE.startswith(_PLACEHOLDER):
        raise SystemExit(
            "refusing to write: DISCLOSURE is still the placeholder. Score the "
            "pair first, then replace it with the measured disclosure."
        )
    if not GATES.exists():
        raise SystemExit(f"refusing to write: {GATES} does not exist — score first.")
    gates = json.loads(GATES.read_text())
    build(CONTROL / "calibration_attestation.json", False, gates)
    build(ARM / "calibration_attestation.json", True, gates)
