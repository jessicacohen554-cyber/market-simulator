#!/usr/bin/env python3
"""Write pjm-h15's governance attestation into both composite bundles.

The C6 governance gate reads ``<bundle>/calibration_attestation.json``. A
COMPOSED bundle does not inherit it (``pjm_h15_compose_span.py`` copies only
year-scoped files and concatenates the root parquets), so the parent writes it
once, here, from the incumbent keeper's own ledger.

Rule 21 ``[R-DOF]``: the DOF ledger is CARRIED FORWARD VERBATIM from
``pjm_h14_coalmustrun_span`` — 19 entries / 6 residual, unchanged — because this
arm adds **zero** free parameters. It withdraws a pooled-vintage assertion and
replaces it with the same measured statistic at a finer grain; there is no value
to tune. A blind ``build_dof_ledger.py`` rebuild would drop the curated
measured/published entries (the nyiso-8x/9x/10x failure mode), so the ledger is
union'd forward rather than rebuilt.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "results/calibration/pjm_h14_coalmustrun_span/calibration_attestation.json"
OUT = [
    REPO / "results/calibration/pjm_h15_coalwindow_span",
    REPO / "results/calibration/pjm_h15_coalwindow_touchpoint",
]

ATTESTED_BY = (
    "pjm-h15 orchestrator (2026-09-20/21). The incumbent keeper recipe "
    "2026-09-20-pjm-h14-coalmustrun-span (pjm_h14_coalmustrun_span + "
    "pjm_h14_coalmustrun_touchpoint) replayed at pinned HEAD "
    "6de36475e9b89f980927fdf0fcfa196c627f2b6a via scripts/replay_keeper.py "
    "--set coal_sync_online_frac_per_year=true, ONE YEAR PER SHARD CONTAINER "
    "(rule 36 [R-YEAR-ISOLATION] (a)), ZERO LP MINUTES IN THE PARENT (rule 32 "
    "[R-SHARD] (a)), composed at zero LP by scripts/probes/pjm_h15_compose_span.py "
    "with legitimacy_diagnostics.json REGENERATED over each composite rather than "
    "copied from a leg (pjm-h13 correction #1) and the benchmark parquets rebuilt "
    "with run_calibration_full.py --rebuild-benchmark (no re-solve). NO CONTROL "
    "SOLVES WERE SPENT: G-DRIFT (rule 29 [R-SCREEN] (b), form 4) was audited over "
    "3b44a752 -> f083eb32 with EVERY hunk classified INERT for PJM (the CAISO "
    "chp_steam_duty_window family and the SPP vre_reference_rate_year_own family, "
    "both default-off AND absent from this ISO's recipe), so the incumbent keeper's "
    "committed bundles ARE the control; the audit was re-run over the later merge "
    "window f083eb32 -> ebc020cf at the rebase, where measured_cc_heat_rates and "
    "hydro_pondage_bound are likewise default-off and absent from both recipes. "
    "Gates G1-G5 and the reported/gating asymmetry were fixed ex ante in "
    "docs/handoffs/PRECOMMIT-pjm-h15-2026-09-20.md, committed and pushed at "
    "6de36475 BEFORE any arm result existed, and NEITHER was amended after a number "
    "landed. TWO of the five gates FAIL (G2, G4); both failures are this lane's own "
    "and are disclosed rather than argued away (RESULT sec.5)."
)

NOTE = (
    "ONE NEW ScenarioConfig FLAG, GATED DEFAULT FALSE: coal_sync_online_frac_per_year "
    "False -> True on the keeper's own recipe. THE DEFECT IT REPAIRS is rule 17 "
    "[R-FLOOR-WINDOW] and rule 14 [R-ACCURATE], read off the COMMITTED ARTIFACT and "
    "the plants' OWN CEMS at zero LP and never off a price or volume residual: "
    "data/raw/_processed-legacy/thermal_tranches_PJM.csv publishes ONE online_frac "
    "per coal plant, derived on 2023-2025, and arrays.py::_compose_min_gen_floors "
    "applies it as EVERY solve year's commitment window. The derive window was "
    "re-established rather than assumed — re-running 2023-2025 through the FROZEN "
    "deriver and summing its per-year counts reproduces the committed column on 168 "
    "of 168 rows, 0 mismatched (--verify-pooled), which is also the rule-23 identity "
    "proof that the grain refinement moves no committed value. So 2020-2022 are "
    "windowed on a share measured in years those plants had not yet reached: plant "
    "50888 is floored across 68.4% of 2020 by a fraction measured three years later, "
    "in a year whose own meter says it synchronized in 1.3% of the hours; 3118 reads "
    "pooled 0.520 against an own-year 0.951 (2020), 3136 0.413 against 0.906 (2020), "
    "6004 0.319 against 0.943 (2022) and 0.157 (2025), 7213 Clover 0.314 against "
    "0.102 (2023). ZERO FREE PARAMETERS: the arm replaces a measured count ratio with "
    "the SAME measured count ratio at the grain the runtime applies it, adding no "
    "threshold, share or multiplier. IT CANNOT BE A LEVEL CHANNEL, measured on the "
    "operand that cannot hide behind a moving denominator (forced ENERGY, never a "
    "share — pjm-h14 correction #6): the asserted coal-floor energy moves +8.39 / "
    "+13.24 / +9.31 / -2.80 / -1.00 / +3.68 % across 2020-2025, and WITHIN every "
    "single year it moves both ways across plants (2020: 23 up / 15 down; 2023: 12 up "
    "/ 24 down). Through the solver the same holds: D-2 coal_mustrun forced energy "
    "moves -0.134 / +0.038 / +0.155 / -0.594 / -0.024 / +0.310 TWh. "
    "SCOPE IS PROVEN THROUGH THE BUILDER, not by reading the diff (G5, zero LP, all "
    "six years): every coal generator's pmax_mw AND coal_sync_pmin_mw move by exactly "
    "0.000e+00, min_gen moves in 8,202-30,387 cells per year, and the ONLY mechanism "
    "id whose floor array moves is MECH_COAL_MUSTRUN. "
    "REPORTED AT FULL MAGNITUDE AND DECLARED REPORTED-ONLY EX ANTE (PRECOMMIT "
    "sec.4.1): C1 COAL_BIT worsens in five of six years (2020 +25.422 -> +25.704, "
    "2021 +19.486 -> +19.615, 2025 +7.449 -> +7.625) and IMPROVES in 2023 (+0.650 -> "
    "+0.527), while CC_REGULAR improves in five of six. The adverse direction in "
    "2020-2022 was PREDICTED IN THE CHARTER BEFORE THE SOLVE and is rule 14's own "
    "diagnosis — the pooled window was silently compensating — with rule 1 "
    "[R-STRUCT] keeping the mechanism in regardless. The dispatch response is ~20x "
    "SMALLER than the asserted-floor footprint, reproducing pjm-h14's floor-vs-band "
    "discount: the arm moves a FLOOR, not a cheap BAND."
)


def main() -> None:
    src = json.loads(SRC.read_text())
    att = {
        "schema": src["schema"],
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
            "attested_by": ATTESTED_BY,
            "note": NOTE,
        },
        "exceptions": src.get("exceptions", []),
        "free_parameters": src["free_parameters"],
        "delta_vs_incumbent": {
            "keeper": (
                "2026-09-20-pjm-h14-coalmustrun-span "
                "(results/calibration/pjm_h14_coalmustrun_span + "
                "pjm_h14_coalmustrun_touchpoint)"
            ),
            "config_deltas": ["coal_sync_online_frac_per_year: False -> True"],
            "n_config_deltas": 1,
            "code_deltas": [
                "src/market_sim/config/scenarios.py: NEW field "
                "coal_sync_online_frac_per_year (dataclass default False), registered "
                "in _CACHE_KEY_OPTIONAL_FIELDS + _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS + "
                "_BACKCAST_ONLY_OVERLAY_FIELDS in the SAME commit (nyiso-119 "
                "discipline; default cache key byte-identical to origin/main, armed "
                "key distinct)",
                "src/market_sim/data/fleet/arrays.py::_compose_min_gen_floors: ONE "
                "seam in the coal_sync_any block, plus the gather that reads "
                "thermal_tranche_online_frac_by_year filtered to plant_group == COAL",
                "data/raw/_processed-legacy/thermal_tranches_online_frac_by_year_PJM.csv: "
                "NEW additive companion artifact from the FROZEN deriver (rule 23 not "
                "engaged — thermal_tranches_PJM.csv is NOT regenerated and xiso-5's "
                "refusal stands untouched)",
            ],
            "free_parameters_added": 0,
            "dof_ledger": {
                "n_entries": src["free_parameters"]["n_entries"],
                "n_residual": src["free_parameters"]["n_residual"],
                "carried": "VERBATIM from the incumbent keeper; zero entries added.",
            },
            "authorized_price_tuning": src["delta_vs_incumbent"].get(
                "authorized_price_tuning"
            ),
        },
    }
    for d in OUT:
        (d / "calibration_attestation.json").write_text(
            json.dumps(att, indent=1) + "\n"
        )
        print(f"wrote {d}/calibration_attestation.json")


if __name__ == "__main__":
    main()
