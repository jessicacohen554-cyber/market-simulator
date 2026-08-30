"""Generate miso188_rvs_B's calibration attestation from the keeper's.

The arm is the miso-187 keeper recipe plus exactly one zero-residual-DOF
mechanism (the gen_miso186/187 attestation pattern): its attestation is the
keeper's with one MEASURED-identified ledger entry for the retiree-channel
vintage-status scope (EIA's own contemporaneous vintage generator status as
the membership oracle, zero fitted scalars, zero lineage solves), a
rewritten ``governance.attested_by`` for the miso-188 A/B, and this
session's disclosures appended AT FULL MAGNITUDE (the C3a-2023 adverse face
included). ``n_residual`` is UNCHANGED. Exceptions carry unchanged.
"""

import json

SRC = "results/calibration/miso187_nuc_B/calibration_attestation.json"
DST = "results/calibration/miso188_rvs_B/calibration_attestation.json"

d = json.load(open(SRC))

d["free_parameters"]["entries"].append(
    {
        "name": "retiree_vintage_status_scope (boolean arm)",
        "where": (
            "ScenarioConfig.retiree_vintage_status_scope -> "
            "scripts/run_calibration.py (and runner.py's backcast branch) -> "
            "data/fleet/eia860.py::load_retired_within_window(vintage_status_"
            "scope=) via the _retiree_vintage_status latest-committed-vintage "
            "lookup over data/raw/eia-860/vintage_<year>/ (the SAME "
            "year-matched EIA-860 vintage record carry_operating_mothballs "
            "already reads as its status oracle)"
        ),
        "identification": "measured",
        "lineage_solves": (
            "0 (the phantom was identified by miso-188's zero-solve phase-0 "
            "availability audit — Grand Tower 862 OS in vintage_2023 with "
            "CAMPD 0.0 GWh for 2022, 2023 AND 2024 yet carried in-merit to "
            "its formal 2024-04 retirement — and the oracle form was frozen "
            "in PREREG-miso188 §1/§3 BEFORE the mechanism existed. No LMP, "
            "no residual, no tuned scalar anywhere in the path)"
        ),
        "value": (
            "True (the scope carries no numeric parameter of its own; the "
            "oracle is a status lookup — a retiree-channel unit is dropped "
            "for backcast solve year Y iff its status in the latest "
            "committed vintage <= Y whose operable sheet lists it is non-OP "
            "(OA/OS/SB); unlisted units fail OPEN. For MISO it drops 28 "
            "units / 1,434 MW in every solve year — Grand Tower 862 (4x OS), "
            "Carl Bailey 202 (OS), Baxter Wilson 2050 (SB), Taconite Harbor "
            "10075 (2x SB), LaO GEN1 (OS) and small SB/OS stragglers — and "
            "keeps Rush Island 6155 (OP, measured 892/612 GWh in 2023/2024) "
            "and Lansing 1047 (OP-but-dark 2023: the disclosed accepted "
            "miss — the oracle is status-only and never reads CEMS for "
            "membership))"
        ),
    }
)
d["free_parameters"]["n_entries"] = len(d["free_parameters"]["entries"])

d["governance"]["attested_by"] = (
    "ARM - EXACTLY ONE MECHANISM CHANGES: retiree_vintage_status_scope=true. "
    "miso-188, 2026-08-30. PREREG "
    "results/calibration/PREREG-miso188-retiree-vintage-status-scope-"
    "2026-08-30.md was committed, pushed and blob-verified (1c00633) BEFORE "
    "the mechanism was implemented and BEFORE any adjudicating quantity was "
    "computed; the phase-0 characterization it restates was disclosed in its "
    "§0 boundary. Both legs are replay_keeper re-solves of the "
    "2026-08-26-miso-187-nucavail keeper's own recipe, years 2023 2024 2025 "
    "in ONE invocation each, years sequential, legs sequential (rules "
    "12/16); the arm's single delta rode the sanctioned replay_keeper --set "
    "channel and both legs ran at ONE HEAD (post-mechanism commit 48c95b4). "
    "CONTROL VALUE-IDENTITY (S-0): 2026-08-30-miso-188-control reproduces "
    "the committed keeper with numeric max|diff|=0 on every scored sidecar "
    "of every year, despite a disclosed toolchain drift (numpy 2.5.2->2.4.6, "
    "scipy 1.18.1->1.17.1, pydantic 2.13.4->2.13.5, platform v21->v22). "
    "S-1 EXACTNESS PASS (all frozen witnesses: Grand Tower 862 dispatch > 0 "
    "in the control in 2023 AND 2024 and exactly 0 in the arm in both; Carl "
    "Bailey/Baxter Wilson/Taconite Harbor arm dispatch exactly 0 every "
    "year; Rush Island 6155 nonzero in BOTH legs 2023+2024; Lansing 1047 "
    "nonzero in BOTH legs 2023). S-2 STRUCTURE PASS: arm 2024 CC_REGULAR "
    "class energy falls 1.2114 TWh vs the control (152.4707 -> 151.2593; "
    "gate >= 0.10) — near the full 1.229 TWh phantom in-merit availability, "
    "i.e. minimal substitution. S-4 PASS (zero D-4 conduct failures, zero "
    "new; C8 PASS). The charter kill SILENT (S-1 clean). SCORED FACE AT "
    "FULL MAGNITUDE (S-5): C1 fuelmix CC_REGULAR-2024 +8.037 TWh FAIL -> "
    "+6.820 TWh PASS (the single criterion-status flip, in the predicted "
    "direction and inside the PREREG's declared [-1.23,-0.30] range at "
    "-1.217); C3a-2024 -4.6440% -> -4.3034% (toward zero); C3a-2023 "
    "+2.4049% -> +3.5008% (the PREREG's declared adverse face, inside the "
    "+-10% band); C3a-2025 -12.3185% -> -12.2965% (essentially unchanged — "
    "the lever claims nothing on the C3a-2025 object and moves it by 0.02 "
    "pp); ZERO PASS->FAIL flips; the S-5 escalation condition did not fire. "
    "PROMOTED ON THE PREREG'S OWN PRE-REGISTERED RULE (PREREG-miso188 §4: "
    "S-0/S-1/S-2/S-4 clean + charter kill silent + zero PASS->FAIL flips "
    "=> promote), plus rules 1/14: the control dispatches a 511 MW CC "
    "measured dark for three straight years, so the structurally faithful "
    "run is the arm. LOYO within 2023-2025: the mechanism carries ZERO "
    "fitted parameters and its identification (published EIA-860 vintage "
    "status) is year-independent, so no year's parameter was identified "
    "against any year's outcome; per-year effects reported at full "
    "magnitude above. n_residual UNCHANGED. Rule 22: no year outside "
    "2023-2025 was solved, scored or registered; MISO holds neither marker "
    "and the holdout spend freeze is untouched."
)

d["disclosures"]["miso188_ab"] = (
    "A/B verdict record: results/calibration/_miso188_ab_gates.json "
    "(S-0/S-1/S-2/S-4/S-5 + the charter kill, which does not fire). "
    "Disclosures against interest: (1) C3a-2023 worsens +2.4049% -> "
    "+3.5008% — the PREREG's declared adverse face of removing 2.71 TWh of "
    "2023 phantom supply (CC_REGULAR 143.5223 -> 140.8136 TWh), reported at "
    "full magnitude, in-band. (2) The accepted miss stands unrepaired: "
    "Lansing (1047, 241 MW coal) is OP in its latest vintage but measured "
    "dark in 2023 (~0.80 TWh in-merit phantom remains); patching it would "
    "need same-year CEMS darkness as a MEMBERSHIP input, which the PREREG "
    "deliberately refuses. (3) 2025 CC_REGULAR moves 136.4585 -> 136.4246 "
    "TWh (-0.034) although every dropped unit is already ramp-zeroed in "
    "2025 — a small cross-year interaction through pooled constructions "
    "(reserve/floor pool membership), disclosed; no 2025 criterion moves "
    "beyond rounding (C3a-2025 -12.3185 -> -12.2965%). (4) The phase-0 "
    "availability instrument initially mis-keyed weather_year (2023 "
    "overlays applied to a 2024 frame); caught via the Union Power factor "
    "cross-check and fixed before any conclusion rested on it. (5) The "
    "registration date is 2026-08-30 (run ids 2026-08-30-miso-188-control "
    "/ -rvsscope), matching the PREREG's declared ids. (6) The partial-"
    "plant mid-window exit gap (Sherco-2, South Oak Creek 5+6, A B Brown, "
    "Dan E Karn, Big Cajun 2-1 OS: 5.93 TWh of 2023 / 0.57 TWh of 2024 "
    "measured generation the fleet cannot carry) is NAMED, sized and NOT "
    "built — it needs unit-grain exit timing in the plant-keyed COD "
    "mechanism, its own charter."
)

json.dump(d, open(DST, "w"), indent=1)
print(
    f"wrote {DST} (n_entries={d['free_parameters']['n_entries']}, "
    f"n_residual={d['free_parameters']['n_residual']})"
)
