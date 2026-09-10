"""Emit the SPP-61 calibration attestation for ``results/calibration/spp61_vintage``.

SPP-61 arms ``eia860_vintage_tracks_solve_year`` on top of the SPP-52a keeper
recipe (``results/calibration/spp52a_fossil93``) and changes nothing else — no
code edit, no shared default, no new tunable.  The DOF ledger is therefore
INHERITED verbatim from that keeper (rule 21 ``[R-DOF]``): the arm introduces
**zero** new free parameters, because the mechanism it turns on is a plain
GATED bool whose content comes entirely from the committed EIA-860 annual
releases.  Only the run identity and the disclosures move.

The arm is owed under rule 14 ``[R-ACCURATE]`` and rule 13 ``[R-MEASURED]``:
the control resolves every backcast year against the canonical 2025 Early
Release snapshot, so its 2023 and 2024 fleets carry a fuel vintage those years
did not have.  The repair makes the C1 fit WORSE and stays in regardless
(rule 1 ``[R-STRUCT]`` first half), exactly as the lane's PRECOMMIT §4
pre-committed before the solve.

Usage:
    python scripts/gen_spp61_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEEPER = REPO / "results/calibration/spp52a_fossil93/calibration_attestation.json"
BUNDLE = REPO / "results/calibration/spp61_vintage"


def build() -> dict:
    """Return the SPP-61 attestation, inheriting SPP-52a's DOF ledger verbatim."""
    att = json.loads(KEEPER.read_text())

    # Rule 21 [R-DOF]: the ledger is unchanged. `eia860_vintage_tracks_solve_year`
    # is a GATED bool with no tunable scalar, identified by the EIA-860 annual
    # releases themselves, so it adds no free parameter and no residual entry.
    att["free_parameters"]["inherited_from"] = "spp52a_fossil93 (SPP keeper 5)"
    att["free_parameters"]["inheritance_basis"] = (
        "SPP-61 is the SPP-52a recipe plus one GATED bool "
        "(eia860_vintage_tracks_solve_year=true) applied through the registered "
        "--set channel. No offer band, structural share, code path or shared "
        "default moves, so every ledger entry and every scalar count carries over "
        "unchanged. n_entries stays 3 and n_residual stays 2."
    )

    att["governance"]["measured_input_switches"] = {
        "eia860_vintage_tracks_solve_year": {
            "value": True,
            "where": "run_config.scenario_config.eia860_vintage_tracks_solve_year",
            "identification": "measured-physical",
            "source": (
                "EIA-860 annual releases, resolved per solve year by "
                "config/paths.py::resolve_backcast_eia860_vintage. Zero scalars, "
                "zero degrees of freedom: the switch selects WHICH committed "
                "release the fleet builder reads, and the content is the release."
            ),
            "warrant": (
                "Rule 14 [R-ACCURATE] and rule 13 [R-MEASURED]. Unarmed, every "
                "backcast year resolves to the canonical 2025 Early Release, so "
                "the 2023 and 2024 fleets carry a fuel vintage and a unit "
                "population those years did not have. The armed registry is the "
                "accurate input; the control's is an estimate silently "
                "compensating elsewhere."
            ),
            "forward_test": (
                "Rule 13's admissibility test is met: the same construction "
                "regenerates for a forecast year from the then-current EIA-860 "
                "release, and responds to changed conditions. This is not an "
                "overlay and pins no outcome to an actual."
            ),
            "iso_scope": (
                "Rule 25 [R-ISO-SCOPE]: armed per-run through --set on SPP's own "
                "bundle. The dataclass default stays False and is registered in "
                "_CACHE_KEY_OPTIONAL_FIELDS at that declared value, so every "
                "pre-existing cache key of all seven ISOs is byte-stable and no "
                "other ISO moves. No fitted number crosses an ISO boundary."
            ),
            "first_arm": "First arm of this field in any committed run, in any ISO.",
        }
    }

    att["disclosures"] = {
        "note": (
            "SPP-61 disclosures — reported, not patched (rules 1 / 13 / 14). "
            "Inherits SPP-52a's, which inherits keeper 4's."
        ),
        "the_repair_makes_the_gated_fit_worse_and_stays_in": (
            "C1 goes from ONE failing row to TWO. Control: 2024 ST_GAS -8.13 TWh "
            "(2023 passing with 1.05 TWh of headroom). Arm: 2023 ST_GAS -8.38 TWh "
            "and 2024 ST_GAS -9.71 TWh, both out of band. The lane's PRECOMMIT §4 "
            "named this exact risk before the solve ('2023 is at real risk and "
            "this lane may break it') and pre-committed to keeping the repair "
            "regardless. Rule 1 [R-STRUCT] forbids rejecting a structurally "
            "correct mechanism because its residual moved the wrong way, and "
            "rule 14 [R-ACCURATE] forbids reverting to the estimate that fit "
            "better. Reported at full magnitude; never absorbed."
        ),
        "what_the_degradation_actually_diagnoses": (
            "Model ST_GAS was ALREADY 6.95 / 8.13 TWh below actual before the arm. "
            "The arm removes 744.5 / 948.4 MW of ST_GAS and 1,308.0 / 1,282.1 MW "
            "of CT_PEAKER capacity that did not exist in 2023 / 2024, which "
            "removes a compensating error rather than creating one. The residual "
            "is a gas-steam merit-order/offer defect, not a fleet-vintage defect. "
            "Routed as the named successor for the C1 ST_GAS row — root-caused, "
            "not buried back in the input."
        ),
        "what_improves": (
            "The control's registry was 60,749.0 / 60,739.9 / 60,739.9 MW across "
            "three years — a fleet that barely evolves, which is the pjm-167 "
            "defect this field was built for. The arm restores real annual "
            "evolution (-2,715.4 MW in 2023, -3,175.3 MW in 2024). D-A 2025 "
            "diurnal phase repairs from OFF to OK, and 2023 / 2024 diurnal "
            "amplitude rises from 36.9 / 35.2 % to 38.5 / 38.1 % of measured."
        ),
        "gates_that_still_fail": (
            "C1 on the 2023 and 2024 ST_GAS rows, and C3c in all three years. "
            "Neither is reachable by the vintage channel. The determination is "
            "NOT-YET, the same determination the control carries; this run is "
            "promoted on structural fidelity (rules 1 / 14), never on its score."
        ),
        "c5a_co2_moves_the_wrong_way": (
            "REPORTED-ONLY (rubric v2.9, contributes no status): -2.6 / -2.0 / "
            "+3.0 % becomes -5.6 / -3.1 / +2.9 %. Reported at full magnitude. It "
            "tracks the same ST_GAS shortfall and is routed with it."
        ),
        "d10_free_class_c1": "15/16 all · 11/12 free becomes 14/16 all · 10/12 free.",
    }

    return att


def main() -> None:
    """Write the attestation into the SPP-61 bundle."""
    out = BUNDLE / "calibration_attestation.json"
    out.write_text(json.dumps(build(), indent=1) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
