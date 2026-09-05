"""Generate the miso-201 A/B legs' calibration attestations from the keeper's.

The gen_miso186/187/188/198/200 pattern. Both legs are the miso-200 keeper recipe
re-solved, the arm carrying exactly one ZERO-DOF input repair, so each leg's
attestation is the keeper's with a rewritten ``governance.attested_by`` and this
session's disclosures appended AT FULL MAGNITUDE; the arm additionally carries
ONE measured-identified ledger entry for the ST-side capacity basis alignment.

``n_residual`` is UNCHANGED: the arm changes the BASIS on which a measured outage
window's removed MW is expressed — from the extract's per-unit EIA-860 nameplate
to the fleet unit's own ``pmax_mw``, the capacity the LP applies the multiplier
to — and introduces no fitted scalar of any kind.

Run this INSTEAD of ``scripts/build_dof_ledger.py``, which regenerates the ledger
from config and would drop the documented entries. It also exists because a
``--replay-bundle`` solve writes NO attestation at all, which is what made
miso-200's K-6 unscorable and its K-3/K-4 pass vacuously on the first scoring
run (FINDING-miso200, superseding addendum).

Usage:
    python3 scripts/gen_miso201_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "results/calibration/miso200_unitroute_B/calibration_attestation.json"
CONTROL = REPO / "results/calibration/miso201_control_A"
ARM = REPO / "results/calibration/miso201_stbasis_B"

# Filled from the scored A/B record so the disclosure quotes measured numbers
# rather than restating the PREREG's expectations.
GATES = REPO / "results/calibration/_miso201_ab_gates.json"

LEDGER_ENTRY = {
    "name": "unit_outage_st_capacity_basis (boolean arm)",
    "where": (
        "ScenarioConfig.unit_outage_st_capacity_basis -> "
        "outages._st_basis_pairmap (eligibility + the 1-1 unit join, built over "
        "outages._iso_plant_unit_capacity, the PER-UNIT companion of the same "
        "fleet load _iso_plant_capacity sums into the derate denominator) -> the "
        "numerator substitution in outages._unit_outage_factors_from_events. "
        "Threaded from config by data/fleet/arrays.py into "
        "unit_outage_derate_factors, unit_outage_short_derate_factors, "
        "unit_partial_outage_derate_factors and unit_layup_removed_fractions."
    ),
    "identification": (
        "MEASURED, zero free parameters. The accumulator derates a bin by "
        "unit_capacity_mw / cap[bin]. For a STEAM bin the numerator is the "
        "extract's per-unit EIA-860 NAMEPLATE (capacity_source eia_exact, written "
        "by derive_campd_unit_outages.build_capacity_index) or a CEMS observed "
        "peak, while cap[bin] is the fleet's NET-SUMMER pmax sum (eia860 sets "
        "pmax = net_summer_capacity_mw) — and unit_outage_lp_capacity_basis "
        "cannot close the gap because _CC_NAMEPLATE_BASIS_GROUPS is "
        "(CC_REGULAR, CC_CHP). When armed, each row's removed MW becomes the "
        "FLEET UNIT'S OWN pmax_mw: not a new quantity, but the very capacity the "
        "availability multiplier is applied to, so numerator and denominator sit "
        "on one basis and a bin all of whose units are out lands on EXACTLY 1.0. "
        "No threshold, no scalar, no per-plant enumeration (rule 24). The join is "
        "the deriver's own normalisation plus a unique 1-1 residual pairing that "
        "is FORCED rather than chosen, and it is ALL-OR-NOTHING per bin — a bin "
        "with any unresolved unit keeps the production basis entirely, so the "
        "flag can never half-align a bin. Rule 13 forward-regenerable: both the "
        "fleet pmax and the extract's unit ids exist for a forecast year, and the "
        "alignment responds to a changed fleet because the fleet does. "
        "Eligibility is computed over the whole extract and is therefore a "
        "static, year-independent property of the bin."
    ),
    "evidence": (
        "_miso201_st_basis_phase0.json, committed at d331c1cb BEFORE the PREREG "
        "and before any mechanism code existed. N-1 reproduction PASS on 988 bins "
        "for BOTH overlays that reach steam bins (the maxgen layer reconstructed "
        "separately because it does NOT share the std accumulator). Root cause "
        "pinned at primary source: EIA-860 Ninemile Point 1403 generator 5 is "
        "nameplate 895.1 MW against net summer 742.6 MW, so unit 5 alone out "
        "removes 895.1/1465.4 = 0.611 of the bin against a correct "
        "742.6/1465.4 = 0.507. THE CHARTER'S CAUTION WAS CONFIRMED AND THEN "
        "SUPERSEDED BY THE SAME MEASUREMENT: at 1403/2070 the pre-clip OVERFLOW "
        "is genuinely inert (the units carrying the windows are the whole bin, so "
        "availability 0.0000 is correct), but the overflow was never the object — "
        "the basis gap over-removes in EVERY hour a steam unit is out and the "
        "clip hides only the extreme, so the lever is live at the very facility "
        "the charter named inert. Coverage 32/55 steam bins, 8,553/12,291 MW "
        "(69.6 %); capability +1,576.0 / +1,968.3 / +1,403.2 GWh for "
        "2023/2024/2025, reproduced EXACTLY by the built mechanism "
        "(+1576.02/+1968.34/+1403.23). The frozen L-3a soundness KILL does NOT "
        "fire: every residual aligned-overflow cell (170, 1104, 2070, 6639) is "
        "100 % explained by same-unit window overlap — the adjacent-window "
        "boundary-day double-count FINDING-miso200 §8 item 2 already names — so "
        "the alignment ISOLATES that defect as the only remaining steam overflow."
    ),
    "residual_dof": 0,
}


def _fmt(v: object, nd: int = 4) -> str:
    return f"{v:+.{nd}f}" if isinstance(v, (int, float)) else str(v)


def build(dst: Path, armed: bool, gates: dict) -> None:
    d = json.loads(SRC.read_text())
    if armed:
        d["free_parameters"]["entries"].append(LEDGER_ENTRY)
        d["free_parameters"]["n_entries"] = len(d["free_parameters"]["entries"])

    leg = "ARM leg B (unit_outage_st_capacity_basis=True)" if armed else "CONTROL leg A"
    d["governance"]["attested_by"] = (
        f"miso-201 A/B (2026-09-02), {leg}: control miso201_control_A vs arm "
        "miso201_stbasis_B, both MISO 2023+2024+2025 in one invocation, years "
        "sequential, solved in-session and never on CI (rule 12/16), both from "
        "the SAME committed keeper recipe via --replay-bundle so the delta is "
        "provably one ScenarioConfig field. Scored by "
        "scripts/probes/_miso201_ab_gates.py, COMMITTED BLIND with the PREREG "
        "before the mechanism existed and before either leg's numbers, and "
        "deliberately NOT importing _miso198_ab_gates: it orders kills-silent "
        "BEFORE inertness and measures inertness on VALUE MOVEMENT rather than "
        "criterion-status identity. It additionally REFUSES to score K-3/K-4/K-6 "
        "unless BOTH legs carry non-empty D1/D4 rows and attestation entries — "
        "the miso-200 vacuous-pass trap, closed in advance rather than "
        "discovered after the fact. " + str(gates.get("verdict", "verdict pending"))
    )

    d.setdefault("disclosures", {})["miso201_ab"] = DISCLOSURE
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
    "REPORTED AT FULL MAGNITUDE. (1) THE FROZEN K-3 KILL FIRED AND IS NOT "
    "RENEGOTIATED. One cell: (2023, unit-conduct, reliability_floor x ST_GAS, "
    "plant 1122), pass -> FAIL. What the D-4 rows show, stated because it cuts "
    "both ways: the arm REDUCED that floor's binding from 10 hours to 2 and its "
    "forced energy from 0.0001 TWh to 0.0000, and the off-window SHARE fell "
    "0.0362 -> 0.0041; the row FAILs because the 2 surviving binding hours are "
    "hours the plant's own meter reads zero (measured_zero_share 1.0, median "
    "0.0 MW), so the ratio test trips on a 2-hour denominator. That is a real "
    "miss on a check the PREREG made a kill, and it is recorded as fired. It is "
    "NOT presented as a pass, and the scorer does not promote on this branch. "
    "(2) K-1 IS SILENT WITH NO BAND EXIT ANYWHERE, and every pre-registered cell "
    "moved in the predicted direction: ST_GAS -3.834/-7.854/-6.862 -> "
    "-3.512/-7.488/-6.681, so the class the model most under-produces moves "
    "TOWARD actual in all three years and the tightest cell on the board "
    "(ST_GAS-2024, 0.146 TWh from the -8.00 edge) moves AWAY from it; "
    "CC_REGULAR-2024 +7.075 -> +6.931. The two NAMED ADVERSE RISKS did move "
    "adversely but stayed far inside: CC_REGULAR-2023 -3.319 -> -3.434 (4.681 "
    "TWh of headroom) and COAL_PRB-2025 -4.865 -> -4.904 (3.135). The capability "
    "bound (+1.576/+1.968/+1.403 TWh) was rigorous and the LP converted "
    "+0.561/+0.782/+0.363 TWh of it, i.e. 36/40/26 percent. (3) C8 MOVES THE "
    "WRONG WAY, SLIGHTLY, and this is the opposite of miso-200's gain: ST_GAS "
    "forced share 0.1496/0.1520/0.2651 -> 0.1551/0.1529/0.2713, +0.5/+0.1/+0.6 "
    "pp, all still well inside the 0.30 merchant budget. Restoring availability "
    "gives the must-run floor more capacity to assert on, so a basis repair that "
    "is right on its own terms can raise forced share; it is reported, not "
    "explained away. (4) C3a FACE, reported and NEVER the justification (rule 1): "
    "2023 +0.2740 -> +0.1218, 2024 -4.3653 -> -4.5820, 2025 -12.2745 -> "
    "-12.3845. The keeper's sole failing criterion gets slightly WORSE, so "
    "nothing here can be read as C3a-driven. (5) NO CRITERION STATUS MOVES; the "
    "determination is unchanged. (6) K-4 D-1 shape is silent and marginally "
    "better (cv_ratio 1.790/1.253/1.494 -> 1.762/1.246/1.485, profile_r "
    "identical). (7) THE ARM'S FIRST SOLVE CRASHED AFTER COMPLETING ALL THREE "
    "YEARS, on a defect in THIS session's own plumbing: the new field's override "
    "was written into _recorded_config in the solve-path style, so run_config.json "
    "was never written. The bug was fixed and the arm re-solved, and the re-solve "
    "is BIT-IDENTICAL to the crashed run across all 18 hourly sidecars "
    "(max_abs_diff 0.0), which is what establishes that the fix is confined to "
    "config recording and that both legs remain one code state. Disclosed rather "
    "than quietly re-run. (8) THE PHASE-0 L-3a SOUNDNESS LINE DID NOT FIRE: every "
    "residual aligned-overflow cell (170, 1104, 2070, 6639) is 100 percent "
    "explained by same-unit window overlap — the adjacent-window boundary-day "
    "double-count FINDING-miso200 section 8 item 2 already names — so the "
    "alignment isolates that defect as the only remaining steam overflow."
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
