#!/usr/bin/env python3
"""Write pjm-h16's governance attestation into the arm composites.

The C6 governance gate reads ``<bundle>/calibration_attestation.json``. A
COMPOSED bundle does not inherit it (``pjm_h16_compose_span.py`` copies only
year-scoped files and concatenates the root parquets), so the parent writes it
once, here, from the incumbent keeper's own ledger (pjm-h15 correction #2).

Rule 21 ``[R-DOF]``: the DOF ledger is CARRIED FORWARD VERBATIM from
``pjm_h15_coalwindow_span`` — unchanged — because this arm adds **zero** free
parameters. It re-grains a window from scattered hours to whole operating days;
``round(k/24)`` is arithmetic on the size the incumbent already chose, and there
is no value to tune. A blind ``build_dof_ledger.py`` rebuild would drop the
curated measured/published entries (the nyiso-8x/9x/10x failure mode), so the
ledger is carried forward rather than rebuilt.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "results/calibration/pjm_h15_coalwindow_span/calibration_attestation.json"
OUT = [
    REPO / "results/calibration/pjm_h16_coalgrain_span",
    REPO / "results/calibration/pjm_h16_coalgrain_touchpoint",
]

ATTESTED_BY = (
    "pjm-h16 orchestrator (2026-09-22). The incumbent keeper recipe "
    "2026-09-20-pjm-h15-coalwindow-span (pjm_h15_coalwindow_span + "
    "pjm_h15_coalwindow_touchpoint) replayed at pinned HEAD "
    "c25d7e500238a953c241271ed91f7c01835f41b5 via scripts/replay_keeper.py "
    "--set coal_sync_window_commitment_grain=true, ONE YEAR PER SHARD CONTAINER "
    "(rule 36 [R-YEAR-ISOLATION] (a)), ZERO LP MINUTES IN THE PARENT (rule 32 "
    "[R-SHARD] (a)), composed at zero LP by "
    "scripts/probes/pjm_h16_compose_span.py with legitimacy_diagnostics.json "
    "REGENERATED over each composite rather than copied from a leg (pjm-h13's "
    "method note: D-4's ct_only vintage guard borrows flags across sibling years, "
    "so per-year leg diagnostics are not comparable to a composed span) and the "
    "benchmark parquets rebuilt with run_calibration_full.py --rebuild-benchmark "
    "(no re-solve; pjm-h15 correction #1). "
    "CONTROL SOLVES WERE SPENT, DELIBERATELY AND AGAINST THE DEFAULT: twelve "
    "shards, six ARM years and six SAME-HEAD CONTROL years, all at the one pinned "
    "SHA. G-DRIFT (rule 29 [R-SCREEN] (b), form 4) was audited over 6de36475 -> "
    "c25d7e50 and classified EVERY hunk INERT for a PJM backcast, so form 4 was "
    "available; the charter spent the controls anyway because (i) the byte "
    "evidence behind the two PERF-C hunks (the un-nested same-year P1 basis seed "
    "and the slim P0 extraction) is CROSS-ISO — a byte gate at atol=rtol=0 on the "
    "NEISO keeper, not on PJM — while model/lp/rows.py, model/lp/model.py and "
    "pipeline/solve.py are genuine edits on the LP build and extract path, and "
    "rule 36(e) is this repo's own record of a basis-neutrality claim that did not "
    "hold once somebody measured it; and (ii) pjm-h15's G2 failed for exactly one "
    "avoidable reason — its 2020-2022 control was a REGENERATION of diagnostics "
    "over a bundle carrying no dispatch/, which read chp_steam x CT_CHP at "
    "0.0145-0.0290 against a committed family of 0.19-0.38 — and a control SOLVE, "
    "whose bundle carries dispatch/<y>_P1.parquet under rule 34(a), makes the arm "
    "and control diagnostics comparable at the root instead of disclosing an "
    "instrument defect after the fact. "
    "THE CONTROLS CAME BACK EXACTLY ZERO AND THAT IS REPORTED, NOT BURIED: the "
    "committed keeper and the same-HEAD control are BIT-IDENTICAL in every year "
    "solved on both sides — max |dMW| 0.000000e+00 over all 166,440 class-hour "
    "cells, 0 cells moved, 2020/2021/2022/2024/2025 — so the G-DRIFT verdict is "
    "now MEASURED ON PJM rather than inferred from NEISO, and a successor PJM lane "
    "may use form 4 across this window with a measurement behind it. "
    "Gates G1-G5 and the reported/gating asymmetry were fixed ex ante in "
    "docs/handoffs/PRECOMMIT-pjm-h16-2026-09-22.md, committed and pushed at "
    "c25d7e50 BEFORE any arm result existed, and NEITHER was amended after a number "
    "landed."
)

NOTE = (
    "ONE NEW ScenarioConfig FLAG, GATED DEFAULT FALSE: "
    "coal_sync_window_commitment_grain False -> True on the keeper's own recipe. "
    "THE DEFECT IT REPAIRS is rule 17 [R-FLOOR-WINDOW] and rule 18 [R-PHYSICS], "
    "measured on PJM's OWN CAMPD record at zero LP and never off a price or volume "
    "residual (scripts/probes/pjm_h16_coalgrain_phase0.py; 29 covered coal plants x "
    "6 years = 173 plant-years, 152 of them reachable). "
    "arrays.py::_compose_min_gen_floors places a coal plant's synchronization floor "
    "in load_rank[:k] — the top k INDIVIDUAL HOURS by the window series — so the "
    "floor carries the diurnal shape of LOAD, while a coal plant's synchronization "
    "is a whole-operating-day decision. RULE 17 (a) DRIVER EVIDENCE: the "
    "peak-to-mean of each plant's ONLINE hour-of-day profile is 1.0001-1.3097 "
    "(median 1.0091, <= 1.10 on 143 of 152) and its overnight(00-05)/afternoon"
    "(14-19) on-share ratio is 0.788-1.027 (median 0.9968, inside [0.9,1.1] on 145 "
    "of 152) — when a PJM coal unit is synchronized it runs THROUGH the overnight "
    "trough — against an incumbent window whose own peak-to-mean is 1.0132-4.8608 "
    "(median 1.3011) and which is MORE PEAKED THAN THE PLANT ON 152 OF 152 "
    "PLANT-YEARS; a whole-day window is 1.0000 by construction. Clause (b) fails in "
    "BOTH directions: the floor binds at the daily peak and is absent overnight on "
    "the SAME committed day. RULE 18 [R-PHYSICS]: the incumbent window implies "
    "3,963 / 4,354 / 4,689 / 5,517 / 4,992 / 4,356 STARTS per year over 2020-2025 "
    "against the fleet's own metered 238 / 290 / 303 / 302 / 302 / 334 — 13.0x to "
    "18.3x — with 253 implied starts on 1,299 MW plant 6264 in 2024 against 4 "
    "measured. A 1,299 MW coal boiler cannot start 253 times a year. THE SHARP "
    "TEST, actuals only: in the hours the incumbent window HOLDS the floor but a "
    "day window RELEASES it the real plants average 267.9 MW and are online 52.17 % "
    "of the time, against 297.2 MW and 67.13 % in the hours a day window HOLDS but "
    "the incumbent RELEASES — +29.4 MW and +15.0 points, in all six years. "
    "ZERO FREE PARAMETERS (rules 21/24): no threshold, share, multiplier or length "
    "— the grain is the operating day and round(k/24) is arithmetic on the size the "
    "incumbent already chose; the helpers (_commitment_day_order, "
    "_mustrun_window_hours) are spp-27's own, reused unchanged. "
    "IT IS NOT A LEVEL CHANNEL, on the operand that cannot hide behind a moving "
    "denominator: total asserted coal floor-HOURS move 0.000 / +0.018 / +0.033 / "
    "-0.025 / -0.046 / +0.019 % across 2020-2025, and the round(k/24)*24 rounding "
    "moves UP in 70 and DOWN in 73 of 152 plant-years. "
    "SCOPE PROVEN THROUGH THE BUILDER, NOT THROUGH ANOTHER MECHANISM'S D-2 "
    "(pjm-h15's generalizable lesson): on a zero-LP fleet_only A/B in every year, "
    "pmax_mw and coal_sync_pmin_mw move by 0.000e+00 and the ONLY mechanism id "
    "whose min_gen cells move is MECH_COAL_MUSTRUN. "
    "RULE 19 [R-ONE-MECH]: the window is REPLACED, never stacked — SIZE "
    "(coal_sync_online_frac, which the keeper already takes per-year), LEVEL "
    "(coal_sync_pmin_mw), MEMBERSHIP and the pmax*availability clip are untouched; "
    "the two GAS seams keep their own grain (mustrun_window_commitment_grain stays "
    "OFF) and SPP-71's coal_sync_ensemble_level — a THIRD placement rule for the "
    "same floor, merged after this charter was pushed and absent from the pinned "
    "SHA — stays OFF and is mutually exclusive by construction. "
    "ITS OWN GATE, NOT A WIDENING of mustrun_window_commitment_grain: the gas "
    "gate's own comment says the coal seam keeps the hour grain because it is a "
    "separate mechanism id carrying separate D-4 evidence, and widening the shared "
    "field would move SPP's DESIGNATED KEEPER, which arms it and has coal, with no "
    "SPP lane measuring anything (rules 25 [R-ISO-SCOPE] / 28(d)). "
    "RULE 13 [R-MEASURED]: forward-native and MODE-BLIND — NOT registered in "
    "_BACKCAST_ONLY_OVERLAY_FIELDS, exactly like its gas sibling, because the day "
    "ranking is computed from the model's OWN window series precisely as the hour "
    "ranking is; nothing measured enters the PLACEMENT, and the CAMPD census above "
    "is the EVIDENCE FOR the change, never an input to it. "
    "REPORTED AT FULL MAGNITUDE AND DECLARED REPORTED-ONLY EX ANTE, so it selected "
    "nothing: C1 COAL_BIT rises by +0.019 to +0.036 TWh and CC_REGULAR falls by "
    "-0.015 to -0.042 TWh in every year solved on both sides — the direction the "
    "charter PREDICTED BEFORE THE SOLVE, at roughly a tenth of the magnitude it "
    "predicted, and against standing PJM COAL_BIT errors of +25.7 (2020) and +19.6 "
    "(2021) TWh, i.e. three orders of magnitude smaller than the residual it sits "
    "inside. The dispatch response is ~20x smaller than the asserted-floor "
    "footprint (+1.2 to +2.8 %), reproducing pjm-h15's floor-vs-band discount: the "
    "arm moves a FLOOR, not a cheap BAND. Rule 1 [R-STRUCT] keeps the mechanism in "
    "regardless of the residual, and the charter said so before the solve."
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
                "2026-09-20-pjm-h15-coalwindow-span "
                "(results/calibration/pjm_h15_coalwindow_span + "
                "pjm_h15_coalwindow_touchpoint)"
            ),
            "config_deltas": ["coal_sync_window_commitment_grain: False -> True"],
            "n_config_deltas": 1,
            "code_deltas": [
                "src/market_sim/config/scenarios.py: NEW field "
                "coal_sync_window_commitment_grain (dataclass default False), "
                "registered in _CACHE_KEY_OPTIONAL_FIELDS + "
                "_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS in the SAME commit (nyiso-119 "
                "discipline). Verified the DIRECT way rather than through the 19 "
                "cache_key pin tests that already fail at origin/main before this "
                "branch touches anything (pjm-h15 correction #8): PJM-backcast "
                "default key c8a2ffdeca6546a6, byte-identical to origin/main; armed "
                "key 63f2f85f710b9ca7, distinct. DELIBERATELY NOT registered in "
                "_BACKCAST_ONLY_OVERLAY_FIELDS — the placement is forward-native "
                "(rule 13).",
                "src/market_sim/data/fleet/arrays.py::_compose_min_gen_floors: ONE "
                "seam in the coal_sync_any block — a coal-scoped _coal_day_grain "
                "gate and a call to the EXISTING _mustrun_window_hours / "
                "_commitment_day_order helpers spp-27 already built. No new helper, "
                "no new artifact, no new loader.",
                "docs/codebase-site/data/mechanism-matrix.js + a cell in all nine "
                "ISO shards, same PR (rule 28(c) [R-MECH-MATRIX]).",
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
