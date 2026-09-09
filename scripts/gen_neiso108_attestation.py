"""Governance attestation for the neiso-108 keeper (session ``neiso-fuelvintage-1``).

neiso-108 is the committed ``neiso106_offerlevel`` recipe replayed full-span
2023/2024/2025 with **exactly one config delta**,
``gas_electric_power_monthly_level=True``, promoted on the owner ruling of
2026-09-09 — plus the flagless 2019-2022 retiree-window widening (commit
``7934e92c``) that reached ``main`` under it. Both were **measured provably
inert** on this ISO's train span before the solve, so the attestation carries
neiso-106's governance forward unchanged and adds only what this session did.

Rule 21 ``[R-DOF]``: neither promoted change adds a free parameter — the seam's
weight table is a frozen derive off EIA-860 and the window is one constant
whose basis is the program's own working span, so ``n_entries`` is untouched.

Usage::

    python3 scripts/gen_neiso108_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "results/calibration/neiso106_offerlevel/calibration_attestation.json"
DST = ROOT / "results/calibration/neiso108_fuelvintage/calibration_attestation.json"
DST_TP = (
    ROOT / "results/calibration/neiso108_fuelvintage_tp/calibration_attestation.json"
)

NEISO108 = {
    "session": "neiso-fuelvintage-1 (2026-09-09)",
    "incumbent": "2026-09-06-neiso-106-fossil-offer",
    "prereg": "docs/PRECOMMIT-neiso-fuelvintage-2026-09-09.md",
    "lineage": [
        "docs/FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09.md",
        "docs/handoffs/xiso-fuelvintage-per-iso-lp-prompts-2026-09-09.md",
        "docs/handoffs/fleet-vintage-retiree-window-charter-2026-08.md",
        "docs/FINDING-pjm-retiree-window-redistribution-2026-09-09.md",
        "docs/FINDING-neiso-index-vs-delivered-gas-2026-09-09.md",
        "docs/RESULT-neiso-fuelvintage-2026-09-09.md",
    ],
    "owner_ruling": (
        "2026-09-09, verbatim: 'these should be promoted as keepers on both 860 and gas shape "
        "counts regardless of inertness.' Both changes are promoted; inertness is reported as a "
        "property of the result, never as a reason to withhold."
    ),
    "config_delta_vs_incumbent": ["gas_electric_power_monthly_level: False -> True"],
    "free_parameters_added": 0,
    "free_parameters_rationale": (
        "Zero, for both promoted changes. The measured monthly gas LEVEL has zero free parameters "
        "(FINDING-xiso-fuelvintage section 4 DOF ledger: the footprint weight table is a frozen "
        "derive off EIA-860, the unit conversion is EIA's 1.036 MMBtu/Mcf heat content, and the two "
        "admission conditions were declared ex ante and never swept). The retiree window is ONE "
        "constant, RETIREMENT_WINDOW_START 2023 -> 2019, whose basis is rule 22's working span "
        "moving by owner amendment (charter section 3), not any residual — rule 23 "
        "[R-FROZEN-DERIVE] satisfied by a span change, never by a score."
    ),
    "measured_inertness": {
        "note": (
            "Both promoted changes were proved inert on 2023-2025 at ZERO LP, before the solve "
            "(rule 29 [R-SCREEN] clause (0)), by building the fleet twice off the incumbent's own "
            "meta.json through run_year(fleet_only=True) and swapping only the one thing under test."
        ),
        "gas_electric_power_monthly_level": {
            "probe": "scripts/probes/_neiso_fuelvintage_census.py",
            "fuel_cells_compared": 22837320,
            "fuel_cells_written": 0,
            "max_abs_delta_fuel_prices": 0.0,
            "max_abs_delta_mc_base": 0.0,
            "full_payload_arrays_compared": 38,
            "full_payload_numeric_cells_compared": 38518653,
            "full_payload_arrays_that_differ": 0,
            "why": (
                "The FINDING section 4 ordering: gas_hub_basis_overlay (Algonquin Citygate via the "
                "ISO-NE MA index) reprices all 463 gas generators at the measured hub spot in 12/12 "
                "months of every year and SUPERSEDES the state-average seam, and "
                "gas_plant_monthly_fuel_pricing overwrites from F923 prints on top. No cell is left "
                "for the seam to reach."
            ),
        },
        "retiree_window_2019_2022": {
            "probe": "scripts/probes/_neiso_retiree_window_delta.py",
            "injected_rows_by_year": {"2023": 59, "2024": 59, "2025": 61},
            "injected_nameplate_mw_by_year": {
                "2023": 1696.374,
                "2024": 1696.374,
                "2025": 1697.490,
            },
            "injected_effective_mwh": 0.0,
            "max_abs_delta_pmax_shared_rows": 0.0,
            "max_abs_delta_availability_shared_rows": 0.0,
            "max_abs_delta_mc_base_shared_rows": 0.0,
            "charter_task_3": "DISCHARGED for NEISO, at the input layer (stronger than the dispatch A/B specified).",
            "pjm_redistribution_exposure": (
                "NOT realised. FINDING-pjm-retiree-window-redistribution-2026-09-09 put NEISO's "
                "exposure at 521.5 MW (Mystic) as an upper bound and told each ISO to measure its "
                "own; NEISO's realised leak is 0.0 MW."
            ),
        },
    },
    "head_drift_disclosure": (
        "REPORTED AT FULL MAGNITUDE, not absorbed. The incumbent's meta.json records "
        "git_sha 70ee7fca, which does not resolve in this repository (the 2026-08-16 history "
        "rewrite), and the bundle predates capx D79 so carries no solve_surface.json — so G-CTRL "
        "form 4's code-level drift audit (rule 29(b) G-DRIFT) CANNOT be run in its literal form, "
        "exactly as the PJM lane found. No control solve was spent, because none is informative: "
        "the arm-vs-control comparison at HEAD is a proven identity across all 38 payload arrays, "
        "so a control would build the same LP. Every difference between this bundle and the "
        "incumbent's committed metrics is therefore HEAD drift from other lanes' commits, and NONE "
        "of it is attributable to either promoted change. Measured against the incumbent's "
        "committed class hourlies: max |class-hour delta| 426.95 MW (2023) / 371.44 MW (2024), "
        "concentrated in CC_REGULAR and hydro (the budget-constrained, flat-cost variable whose "
        "intertemporal placement is a numerical tie); annual class energy moves by at most "
        "0.00067 TWh on 52.7 TWh (13 ppm); mean |price delta| 0.0039 / 0.0055 $/MWh on means of "
        "36.72 / 42.07; slack and dump exactly 0.0 on both sides. The two solutions are alternate "
        "optima of the same LP."
    ),
    "index_vs_delivered": (
        "The program's one unresolved cross-ISO discrepancy is CLOSED by this session, at zero LP: "
        "docs/FINDING-neiso-index-vs-delivered-gas-2026-09-09.md. NEISO's 3.24x January-2023 gap "
        "between the ISO-NE Algonquin index (4.73 $/MMBtu) and the EIA N3045 blend (15.35) is a "
        "respondent-composition artifact in N3045, falsified physically: the index never implies a "
        "marginal heat rate below 7.99 MMBtu/MWh in 84 months, while N3045 implies one below the "
        "6.3 CC floor in 13 of 84 and 3.29 in Jan-2023. The keeper's hub index keeps priority under "
        "rule 14 [R-ACCURATE]'s misalignment exception, now EARNED rather than invoked. The "
        "2.303 $/MMBtu 'level gap' the cross-ISO table reports for NEISO 2023 measures the survey "
        "panel, not the model."
    ),
    "holdout": (
        "The validation touchpoints 2020/2021/2022 are the companion bundle "
        "neiso108_fuelvintage_tp, solved with --holdout-authorized under NEISO's `complete` marker "
        "and stamped to this keeper under rule 30 [R-TOUCHPOINT-FOLD]. Rule 30(c): a held-out year "
        "NEVER downgrades NEISO's determination, which is the train-tier verdict and nothing else. "
        "2019 and H1-2026 are locked-test tier with `final` empty and the freeze ACTIVE: NOT "
        "attempted, NOT designed around, and no result here is evidence about them."
    ),
}


def main() -> None:
    """Write the neiso-108 attestation into the train bundle and its touchpoint twin."""
    att = json.loads(SRC.read_text())
    att.pop("neiso106", None)
    att["neiso108"] = NEISO108
    gov = dict(att["governance"])
    gov["attested_by"] = (
        "neiso-108 (2026-09-09, session neiso-fuelvintage-1) -- the neiso-106 recipe replayed "
        "full-span 2023/2024/2025 with EXACTLY ONE config delta, "
        "gas_electric_power_monthly_level=True, promoted on the owner ruling of 2026-09-09 "
        "together with the flagless 2019-2022 retiree-window widening (commit 7934e92c). BOTH "
        "MEASURED PROVABLY INERT on this span before the solve (see neiso108.measured_inertness): "
        "all 38 fleet_only payload arrays, 38,518,653 numeric cells, bit-identical. Neither adds a "
        "free parameter. The neiso-106 authorized_price_tuning declaration below is CARRIED "
        "FORWARD UNCHANGED -- this session neither re-sized nor re-swept it, and introduced no new "
        "price-tuning channel of its own."
    )
    att["governance"] = gov
    DST.write_text(json.dumps(att, indent=1))
    print("wrote", DST)

    # The touchpoint twin is the SAME recipe on the validation years, so rule 1 (b)'s
    # "ONE config across EVERY scored year" is satisfied in fact — the declaration just has to
    # say so, or C6 fails on a bundle whose config is byte-identical to the one it passes on.
    tp = json.loads(json.dumps(att))
    tp_gov = tp["governance"]
    apt = tp_gov["authorized_price_tuning"]
    # Strict SET EQUALITY against the run's own scored span — the scorer treats years_held as a
    # property of THIS run's configuration, not as a history of where the value came from
    # (calibration_verdict._authorized_tuning_finding; the defect record is
    # FINDING-neiso106-per-year-ladder-governance-defect-2026-09-06.md).
    apt["years_held"] = [2020, 2021, 2022]
    apt["years_held_note"] = (
        "This bundle scores 2020/2021/2022, so years_held names those three. It is a RESTATEMENT, "
        "not a re-declaration: the scalar 0.95470 was set ex ante on the 2023-2025 train span "
        "(PREREG-neiso106, committed 773411e5 before that solve) and is applied here UNCHANGED, "
        "as ONE config, to the validation years the same recipe is replayed on. Nothing was "
        "re-sized, re-swept or re-identified against 2020/2021/2022 — those years were never "
        "consulted in choosing it, which is exactly what rule 1 (b)'s year-invariance condition "
        "asks for. The train bundle's own declaration still reads [2023, 2024, 2025]. Rule 22 "
        "[R-HOLDOUT] and rule 30(c) are unaffected: a validation score is iterable selection "
        "evidence, never a skill claim, and never downgrades NEISO's determination."
    )
    tp_gov["attested_by"] = (
        "neiso-108 touchpoints (2026-09-09, session neiso-fuelvintage-1) -- the neiso-108 keeper "
        "recipe replayed UNCHANGED on the validation years 2020/2021/2022 under NEISO's `complete` "
        "marker with --holdout-authorized. The 2019-2022 retiree window is LIVE here (unlike the "
        "train span, where it is provably inert): +956.0 MW in 2020 and +949.0 MW in 2021, "
        "+201.3 MW in 2022. 2019 and H1-2026 are locked-test tier with `final` empty and the "
        "freeze ACTIVE -- not attempted."
    )
    tp["neiso108"] = dict(tp["neiso108"])
    tp["neiso108"]["bundle_role"] = (
        "VALIDATION TOUCHPOINTS 2020-2022, stamped to the keeper "
        "2026-09-09-neiso-108-fuelvintage under rule 30 [R-TOUCHPOINT-FOLD]."
    )
    DST_TP.write_text(json.dumps(tp, indent=1))
    print("wrote", DST_TP)


if __name__ == "__main__":
    main()
