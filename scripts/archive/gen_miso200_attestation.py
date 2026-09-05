"""Generate miso200_unitroute_B's calibration attestation from the keeper's.

The arm is the miso-198 keeper recipe plus exactly one ZERO-DOF input repair
(the gen_miso186/187/188/198 attestation pattern): its attestation is the
superseded keeper's with ONE measured-identified ledger entry for the
mixed-gas-facility unit-outage class routing, a rewritten
``governance.attested_by`` for the miso-200 A/B, and this session's
disclosures appended AT FULL MAGNITUDE — including the phase-0 L-3a line that
FIRED and is not renegotiated, the two gates that were scored only after the
diagnostics were generated, and K-6 left UNSCORED.

``n_residual`` is UNCHANGED at 2: the arm changes WHICH MODEL BIN a measured
outage window is charged to, using CAMPD's own published ``unitType``, and
introduces no fitted scalar of any kind.

Run this INSTEAD of scripts/build_dof_ledger.py on the promoted bundle —
build_dof_ledger regenerates from config and would drop the documented entry
(38 -> 25).
"""

import json

SRC = "results/calibration/miso198_oom_B/calibration_attestation.json"
DST = "results/calibration/miso200_unitroute_B/calibration_attestation.json"

d = json.load(open(SRC))

d["free_parameters"]["entries"].append(
    {
        "name": "unit_outage_mixed_gas_routing (boolean arm)",
        "where": (
            "ScenarioConfig.unit_outage_mixed_gas_routing -> "
            "scripts/data/derive_campd_unit_outages.py::_resolve_unit_group"
            "(mixed_gas_routing=) -> the '-unitroute-' companion extracts "
            "selected by outages.unit_outage_csv_for_iso / "
            "unit_outage_maxgen_csv_for_iso -> the shared accumulator in "
            "outages._unit_outage_factors_from_events. Populations "
            "data/raw/campd-unit-outages-unitroute-MISO.csv and "
            "campd-unit-outages-maxgen-unitroute-MISO.csv."
        ),
        "identification": (
            "MEASURED, zero free parameters. _resolve_unit_group short-circuits "
            "on the FACILITY's group, and its own pjm-75 justification states "
            "the premise verbatim — 'single-group gas facilities are "
            "byte-identical'. But group_by_code[plant_code] = g.plant_group is "
            "LAST WRITER WINS over the fleet, so at a facility carrying two or "
            "more model gas bins the premise is FALSE and every unit is handed "
            "to whichever bin's fleet row came last. When armed, the "
            "short-circuit is SKIPPED at such a facility and the resolver falls "
            "through to its OWN pre-existing per-unit routing, whose "
            "discriminator is CAMPD's published unitType — a STATIC unit "
            "attribute, so the input regenerates for any forward year and "
            "responds to a changed fleet (rule 13). No threshold, no scalar, no "
            "per-plant enumeration (rule 24); single-gas facilities are "
            "untouched BY CONSTRUCTION."
        ),
        "evidence": (
            "_miso200_outage_routing_phase0.json, frozen and pushed at c5d1aad1 "
            "before any adjudicating quantity. Exactly TWO MISO facilities "
            "qualify. Ninemile Point 1403 (ST_GAS 1,465.4 MW + CC_REGULAR "
            "649.5 MW, last writer CC_REGULAR) sends its two 'Tangentially-fired' "
            "gas-steam boilers (units 4+5, 1,651.1 MW) onto the 649.5 MW CC bin: "
            "pre-clip removed share 2.588/3.556/2.553, above 1.0 for "
            "5,640/6,192/4,920 h/yr, mean availability 0.352/0.288/0.438 — while "
            "the ST_GAS bin that actually holds them received ZERO rows and read "
            "availability identically 1.0, so its 688 MW must-run floor asserted "
            "straight through every outage. Moselle 2070 sends its 59.0 MW "
            "boiler the same way. 1,740.1/1,719.1/1,717.1 MW mis-routed, "
            "clearing the frozen L-1a line in 3 of 3 years."
        ),
        "residual_dof": 0,
    }
)
d["free_parameters"]["n_entries"] = len(d["free_parameters"]["entries"])

d["governance"]["attested_by"] = (
    "miso-200 A/B (2026-09-02): control 2026-09-02-miso-200-control vs arm "
    "2026-09-02-miso-200-unitroute, both MISO 2023+2024+2025 in one invocation, "
    "years sequential, solved in-session and never on CI (rule 12/16). Scored by "
    "scripts/probes/_miso200_ab_gates.py, COMMITTED BLIND before either leg's "
    "numbers existed and deliberately NOT importing _miso198_ab_gates: it orders "
    "kills-silent BEFORE inertness and measures inertness on VALUE MOVEMENT "
    "rather than criterion-status identity, repairing both defects FINDING-miso198 "
    "§5b disclosed in its own scorer. S-0 control integrity PASS — BIT-IDENTICAL "
    "to the keeper's committed sidecars, max_abs_diff 0.0 across 9 sidecars, "
    "which also proves the intervening main drift never reached MISO. S-1 exactly "
    "one of the scenario_config fields differs. S-2 liveness PASS. K-1 through "
    "K-5 ALL SILENT. K-6 UNSCORED and disclosed as such, never counted as a pass."
)

d["disclosures"]["miso200_ab"] = (
    "REPORTED AT FULL MAGNITUDE. (1) THE PHASE-0 L-3a LINE FIRED AND IS NOT "
    "RENEGOTIATED: the repair introduces pre-clip removed share above 1.0 at "
    "(1403, ST_GAS) 1.13 and (2070, ST_GAS) 2.00, at bins that previously had "
    "none, and the PREREG made that a kill. What the A/B adds is a separable "
    "MEASUREMENT, not a reinterpretation: the fleet's ST_GAS bin at 1403 is "
    "EXACTLY the two units carrying those windows (742.6 + 722.8 = 1,465.4 MW) "
    "and at 2070 exactly one (59.0 MW), so a concurrent full stop means the bin "
    "is genuinely 100% out — and availability is exactly 0.0000 in every one of "
    "the 1,728/552/144 and 24/72/24 overflow hours, which is the physically "
    "correct value. The overflow is a bookkeeping artifact with ZERO dispatch "
    "consequence; the residual causes are two PRE-EXISTING defects the "
    "mis-routing was masking (a numerator/denominator basis gap that "
    "unit_outage_lp_capacity_basis cannot reach, since _CC_NAMEPLATE_BASIS_GROUPS "
    "is CC-only, and an adjacent-window boundary-day double-count). (2) K-3 and "
    "K-4 PASSED VACUOUSLY ON THE FIRST SCORING RUN — a --replay-bundle solve "
    "writes no legitimacy_diagnostics.json, so the scorer compared empty against "
    "empty. Disclosed rather than counted: the diagnostics were generated for "
    "BOTH legs (D1=30, D2=23, D4=57 rows each) and the pair re-scored, at which "
    "point S-2, K-3 and K-4 became real PASSes. (3) THE N-4 CAPABILITY BOUND WAS "
    "RIGOROUS BUT VERY LOOSE: it allowed CC_REGULAR-2024 +3.3055 and ST_GAS-2024 "
    "-5.1916 TWh; the LP delivered +0.3270 and -0.1560, i.e. ~10% and ~3% "
    "conversion. The K-1 risk named ex ante did NOT materialise — CC_REGULAR-2024 "
    "+6.748 -> +7.075 (0.33 of 1.25 TWh headroom) and ST_GAS-2024 -7.698 -> "
    "-7.854 (0.16 of 0.45), no band exit anywhere. (4) C3a FACE, reported and "
    "NEVER the justification (rule 1): 2023 +0.1522 -> +0.2740, 2024 -4.4892 -> "
    "-4.3653, and 2025 EXACTLY UNCHANGED at -12.2745 — the keeper's sole failing "
    "criterion does not move, so nothing here can be read as C3a-driven. (5) NO "
    "CRITERION STATUS MOVES AT ALL; the determination is unchanged. (6) THE "
    "STRUCTURAL GAIN IS ON C8: ST_GAS forced share 0.2002/0.2100/0.3187 -> "
    "0.1496/0.1520/0.2651, about -5 pp every year, and 2025 crosses from ABOVE "
    "the 0.30 merchant budget (a grounded over-budget pass) to WITHIN it — the "
    "floor stops forcing energy in hours the plant's own meter says it was out."
)

json.dump(d, open(DST, "w"), indent=1)
print(
    f"wrote {DST} (n_entries={d['free_parameters']['n_entries']}, "
    f"n_residual={d['free_parameters']['n_residual']})"
)
