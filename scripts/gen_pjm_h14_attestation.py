#!/usr/bin/env python3
"""Write ``calibration_attestation.json`` for the pjm-h14 arm bundles.

The DOF ledger is CARRIED VERBATIM from the incumbent keeper
(``2026-09-20-pjm-h13-meritalloc-span``) because the arm adds **zero** free
parameters (rule 21 ``[R-DOF]``): it asserts no level and introduces no scalar —
it WITHDRAWS an assertion that has no measurement behind it. A blind
``build_dof_ledger.py`` rebuild drops the curated measured/published entries, so
it is never used here (the failure mode the nyiso-8x/9x/10x notes recorded).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
#: DOF ledger source. The incumbent keeper is the origin, but rule 35
#: ``[R-PROMOTE]`` (a) deletes its bundle in the promoting session, so once this
#: lane's own span carries the ledger that copy is the live one (identical bytes,
#: and it survives the prune). First existing path wins.
LEDGER_SOURCES = (
    ROOT / "results/calibration/pjm_h14_coalmustrun_span/calibration_attestation.json",
    ROOT / "results/calibration/pjm_h13_meritalloc_span/calibration_attestation.json",
)

ATTESTED_BY = (
    "pjm-h14 orchestrator (2026-09-20). The incumbent keeper recipe "
    "2026-09-20-pjm-h13-meritalloc-span (pjm_h13_meritalloc_span + "
    "pjm_h13_meritalloc_touchpoint) replayed at pinned HEAD "
    "3b44a752977fc27d667c5b6de1c9f22d77665f00 via scripts/replay_keeper.py --set "
    "coal_mustrun_requires_measured_row=true, ONE YEAR PER SHARD CONTAINER "
    "(rule 36 [R-YEAR-ISOLATION] (a)), ZERO LP MINUTES IN THE PARENT "
    "(rule 32 [R-SHARD] (a)), composed at zero LP by "
    "scripts/probes/pjm_h11_compose_span.py with legitimacy_diagnostics.json "
    "REGENERATED over each composite rather than copied from a leg (pjm-h13 "
    "correction #1). NO CONTROL SOLVES WERE SPENT: G-DRIFT (rule 29 [R-SCREEN] "
    "(b), form 4) holds for PJM on pjm-h12's own measurement (2022 control "
    "reproduced the committed keeper, 0 of 78,840 price cells moved) and "
    "pjm-h13's re-audit, so the incumbent keeper's committed bundle IS the "
    "control. Gates G1-G5 and the reported/gating asymmetry were fixed ex ante "
    "in docs/handoffs/PRECOMMIT-pjm-h14-2026-09-20.md, committed and pushed at "
    "3b44a752 BEFORE any arm result existed, and NEITHER was amended after a "
    "number landed. TWO of the five gates FAIL and both failures are disclosed "
    "rather than argued away (RESULT sec.5)."
)

NOTE = (
    "ONE NEW ScenarioConfig FLAG, GATED DEFAULT FALSE: "
    "coal_mustrun_requires_measured_row False -> True on the keeper's own "
    "recipe. THE DEFECT IT REPAIRS is rule 17 [R-FLOOR-WINDOW] and rule 14 "
    "[R-ACCURATE], read off the MODEL'S OWN FLEET CONSTRUCTION at zero LP and "
    "never off a price or volume residual: a coal plant absent from the ISO's "
    "CAMPD thermal-tranche artifact falls through TWO unmeasured defaults that "
    "COMPOUND — campd_bins._DEFAULT_TRANCHE_PCT_BY_GROUP['COAL'] hands it a "
    "45%-of-nameplate must-run tranche (while that constant's own comment calls "
    "its population 'rarely-online units with no reliable observed floor'), and "
    "assembly.py's coal_sync_online_frac(...).get(code, 1.0) then holds that "
    "tranche in ALL 8760 hours because the online%-scaled rule-17 window also "
    "defaults to force-all with no measured share. The plants with the LEAST "
    "evidence therefore carry the STRONGEST and WIDEST floor. Measured on the "
    "model's own fleet: 2020, 36 uncovered coal plants / 15,774.7 MW asserting "
    "58.04 TWh of must-run against 22.97 TWh of TOTAL metered output (2.5x), "
    "with Bruce Mansfield 2,490 MW asserting 9.82 TWh against 0.00 metered, "
    "Chalk Point Steam 2.64 vs 0.00 and Dickerson 2.05 vs 0.00. The population "
    "is not closeable by re-deriving: the committed artifact's window is "
    "2023-2025 (identified by re-running it against the FROZEN deriver and "
    "recovering a byte-equal key set) and its plant universe is a year-blind "
    "current-vintage EIA-860 fleet, so six per-year re-derives gained ZERO "
    "rows. xiso-5's rule-23 [R-FROZEN-DERIVE] refusal to REGENERATE the "
    "artifact stands untouched and this arm does not need it. A SECOND, "
    "DIAGNOSTIC-ONLY deliverable rides the same commit: (MECH_COAL_MUSTRUN, "
    "None): (0, 24) in legitimacy_diagnostics.D4_WINDOWS, because until now the "
    "coal synchronization floor carried NO D4 entry and was the one commitment "
    "floor the rule-17 diagnostic could not see in ANY ISO. It touches no solve "
    "path; coal's D-2 forced share (0.39-3.74% of class) sits far below rule "
    "20's 30% budget so the escalation that reads D-4 never engages. MEASURED "
    "RESULT, six years, composed vs composed: coal must-run forced share falls "
    "in every year (2020 0.0123 -> 0.0061, 2023 0.0374 -> 0.0268); C1 COAL_BIT "
    "error falls in every year (2020 +28.128 -> +25.422, 2021 +20.744 -> "
    "+19.486, 2023 +2.090 -> +0.650) and the displaced energy lands on "
    "CC_REGULAR, which gets WORSE in every year (2020 +0.265 -> +2.634) — "
    "reported at full magnitude, and C1 was declared REPORTED-ONLY ex ante so "
    "it selected nothing. G2 is exact: ZERO uncovered plants carry a coal "
    "must-run floor on the arm in any year. G4 passes: all three named "
    "zero-metered plants carry no floor. G3 FAILS — 5 residual D-4 coal conduct "
    "FAIL rows remain, and ALL FIVE are on COVERED plants the arm deliberately "
    "does not touch, so the gate was written absolutely over all coal when the "
    "card's population is the uncovered cohort; that is this lane's scoping "
    "error, disclosed, NOT amended. G5 FAILS in 2020 (CT_CHP chp_steam share "
    "0.1793 -> 0.1701, |delta| 0.0092 vs a 0.005 bar) and is ~70% a DENOMINATOR "
    "move (CT_CHP class total 1.6560 -> 1.6928 TWh); no other floor ARRAY is "
    "touched, but the gate stands as FAILED."
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", required=True, type=Path)
    args = ap.parse_args()

    src = next((q for q in LEDGER_SOURCES if q.exists()), None)
    if src is None:
        raise SystemExit(
            "no DOF ledger source found; expected one of: "
            + ", ".join(str(q) for q in LEDGER_SOURCES)
        )
    inc = json.loads(src.read_text())
    att = {
        "schema": "calibration-attestation/v1",
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
            "attested_by": ATTESTED_BY,
            "note": NOTE,
        },
        "exceptions": [],
        "free_parameters": inc["free_parameters"],
        "delta_vs_incumbent": {
            "keeper": (
                "2026-09-20-pjm-h13-meritalloc-span "
                "(results/calibration/pjm_h13_meritalloc_span + pjm_h13_meritalloc_touchpoint)"
            ),
            "config_deltas": ["coal_mustrun_requires_measured_row: False -> True"],
            "n_config_deltas": 1,
            "code_deltas": [
                "src/market_sim/config/scenarios.py: NEW field "
                "coal_mustrun_requires_measured_row (GATED, dataclass default False)",
                "src/market_sim/data/fleet/campd_bins.py::fleet_to_bins: the field's ONE "
                "seam at the existing _DEFAULT_TRANCHE_PCT_BY_GROUP fallback",
                "scripts/legitimacy_diagnostics.py: (MECH_COAL_MUSTRUN, None): (0, 24) in "
                "D4_WINDOWS — DIAGNOSTIC ONLY, no solve path, no dispatch, no criterion",
            ],
            "free_parameters_added": 0,
            "dof_ledger": (
                "CARRIED VERBATIM from the incumbent keeper's ledger "
                "(2026-09-20-pjm-h13-meritalloc-span). The arm adds ZERO free parameters "
                "(rule 21 [R-DOF]): it asserts no level and introduces no scalar — it "
                "WITHDRAWS an assertion that has no measurement behind it, so there is no "
                "value to tune and nothing to sweep. n_entries and n_residual are UNCHANGED "
                f"at {inc['free_parameters']['n_entries']}/"
                f"{inc['free_parameters']['n_residual']}."
            ),
            "authorized_price_tuning": {
                "used": False,
                "note": (
                    "NO band multiplier was touched. The rules 1/13 amendment 2026-09-05 "
                    "authorized channel is NOT used by this card: offer_curve_by_group is "
                    "carried byte-identical from the incumbent keeper."
                ),
            },
        },
    }
    path = args.bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
