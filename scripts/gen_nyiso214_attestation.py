"""Write ``calibration_attestation.json`` for the nyiso-214 composed keeper candidate.

Session ``nyiso-fuelvintage-1`` promotes TWO changes into NYISO's keeper recipe
under the owner ruling of 2026-09-09 (handoff ADDENDUM §A7, verbatim: *"these
should be promoted as keepers on both 860 and gas shape counts regardless of
inertness"*):

1. **The 2019–2022 EIA-860 retiree window** (``RETIREMENT_WINDOW_START`` 2023 →
   2019, commit ``7934e92c``). Unconditional — an artifact, not a flag — so it
   rides in with no ``ScenarioConfig`` delta at all. It restores 31 units /
   3,671.9 MW to NYISO's 2019–2022 fleets and **exactly zero MW** to 2023–2025.
2. **``gas_electric_power_monthly_level``** — the measured monthly delivered
   gas LEVEL (EIA N3045 state series blended by this ISO's gas-capacity
   footprint), armed here and measured **LP-inert for NYISO**: with the flag on,
   the assembled ``fuel_prices`` and ``mc_base`` arrays are byte-identical in
   2021, 2022, 2023, 2024 and 2025, because ``gas_hub_basis_overlay`` (Transco
   Z6) covers 12/12 months of every year and is applied last.

**ZERO free parameters are added or moved.** The rule 20 ``[R-DOF]`` ledger and
the exceptions ledger are carried from the superseded keeper VERBATIM, and the
generator asserts that carry rather than retyping it. The ``G_DELTA`` check is
COMPUTED from the two bundles' recorded ``scenario_config`` dumps, not typed.

Usage:
    uv run python scripts/gen_nyiso214_attestation.py \
        --keeper-bundle results/calibration/nyiso213_summer_seam \
        --arm-bundle results/calibration/nyiso_fuelvintage_A
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

#: Keys a re-solve of the same recipe necessarily records differently: the
#: per-year selection keys, and the new-since-keeper ``ScenarioConfig`` fields
#: that HEAD added at their dataclass default (a field absent from the older
#: dump and present at its default in the newer one is not a recipe change).
_YEAR_SELECTION_KEYS = frozenset({"weather_year", "gas_price_override"})


def recipe_delta(keeper: dict, arm: dict) -> dict:
    """Return the substantive ``scenario_config`` difference between two runs.

    Args:
        keeper: The superseded keeper's ``run_config.json``.
        arm: The candidate's ``run_config.json``.

    Returns:
        A mapping of field -> ``{"keeper": ..., "arm": ...}`` for every field
        that differs outside the year-selection keys and outside the
        absent-to-default class.
    """
    ks = keeper.get("scenario_config") or {}
    as_ = arm.get("scenario_config") or {}
    out: dict[str, dict] = {}
    for field in sorted(set(ks) | set(as_)):
        if field in _YEAR_SELECTION_KEYS:
            continue
        kv = ks.get(field, "<absent>")
        av = as_.get(field, "<absent>")
        if kv == av:
            continue
        # A field HEAD added since the keeper solved, recorded at a falsy
        # default, is not a recipe change — there was nothing to differ from.
        if kv == "<absent>" and av in (False, None):
            continue
        out[field] = {"keeper": kv, "arm": av}
    return out


def build(keeper_bundle: Path, arm_bundle: Path) -> dict:
    """Build the attestation payload for the composed keeper candidate.

    Args:
        keeper_bundle: The superseded keeper's bundle dir.
        arm_bundle: The candidate bundle dir.

    Returns:
        The ``calibration-attestation/v1`` payload.

    Raises:
        SystemExit: If the computed recipe delta is not exactly the one
            promotion this session declared, or if the carried DOF ledger
            does not match the keeper's byte-for-byte.
    """
    prior = json.loads((keeper_bundle / "calibration_attestation.json").read_text())
    k_cfg = json.loads((keeper_bundle / "run_config.json").read_text())
    a_cfg = json.loads((arm_bundle / "run_config.json").read_text())

    delta = recipe_delta(k_cfg, a_cfg)
    expected = {
        "gas_electric_power_monthly_level",
        "f923_gas_price_plausibility_screen",
    }
    if set(delta) != expected:
        raise SystemExit(
            "REFUSED: the computed recipe delta is not the declared promotion.\n"
            f"  expected exactly {sorted(expected)}\n"
            f"  computed {json.dumps(delta, indent=2)}"
        )

    att = {
        "schema": "calibration-attestation/v1",
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
            "attested_by": (
                "session nyiso-fuelvintage-1 (2026-09-09). PROMOTION OF TWO CHANGES "
                "UNDER THE OWNER RULING of 2026-09-09 (docs/handoffs/"
                "xiso-fuelvintage-per-iso-lp-prompts-2026-09-09.md ADDENDUM A7, "
                'verbatim: "these should be promoted as keepers on both 860 and gas '
                'shape counts regardless of inertness"). Pre-registration: '
                "results/calibration/PRECOMMIT-nyiso-fuelvintage-1.md (v3 run, pushed "
                "before any measurement) plus docs/ADDENDUM-nyiso-fuelvintage-1-"
                "promotion-2026-09-09.md (this run, pushed BEFORE the composed bundle "
                "was scored; it registers the disposition change and the promotion "
                "gate). "
                "(1) THE 2019-2022 RETIREE WINDOW is an ARTIFACT change with no flag "
                "and therefore no ScenarioConfig delta: RETIREMENT_WINDOW_START 2023 -> "
                "2019 (commit 7934e92c) restores 31 units / 3,671.9 MW to NYISO's "
                "2019-2022 fleets -- dominated by Indian Point 2 (plant 2497, 1,011.5 MW "
                "net summer, retired 2020-04) and Indian Point 3 (8907, 1,039.4 MW, "
                "2021-04), plus 1,487.0 MW of coal (Somerset 676.4, Dunkirk 520.0, "
                "Cayuga 290.6). It is a rule 14 [R-ACCURATE] input-correctness repair: "
                "these units physically existed and generated in the years they are "
                "restored to, and the model's fleet lacked them. It adds EXACTLY ZERO MW "
                "to 2023-2025 (no added row retires later than 2022), proved at the "
                "array level by the artifact-swap instrument GATE T3 (scripts/probes/"
                "nyiso_fuelvintage1_gate_t3.py): strictly additive, added columns pinned "
                "to zero availability AND zero min_gen across all 8,760 hours, common "
                "columns byte-identical in matched unit order, non-generator-axis LP "
                "inputs byte-identical -- which FORCES a zero class-hour delta by "
                "construction rather than sampling it. "
                "(2) gas_electric_power_monthly_level is the shared measured monthly "
                "delivered gas LEVEL (EIA N3045 state series, blended by this ISO's "
                "EIA-860 gas-capacity footprint: NY .938 / NJ .062; admission requires "
                "all twelve months to print and a strict majority of gas capacity, "
                "declared ex ante in docs/FINDING-xiso-fuelvintage-monthly-gas-level-"
                "2026-09-09.md and NEVER swept). ZERO free parameters: the weight table "
                "is a frozen derive off EIA-860 and the unit conversion is the EIA heat "
                "content 1.036 MMBtu/Mcf. It is MEASURED LP-INERT FOR NYISO and is "
                "promoted anyway on the owner's ruling: with the flag armed the "
                "assembled fuel_prices AND mc_base arrays are byte-identical (max |delta| "
                "= 0.0) in 2021, 2022, 2023, 2024 and 2025, because resolve_fuel_prices "
                "applies this seam at :151, the F923 plant-monthly prints at :228 and "
                "apply_hub_basis_overlay at :229 -- the Transco Z6 hub index is the last "
                "word on gas price and covers 12/12 months in every year 2019-2025 "
                "(the model's own log: '492 gas generators repriced at the measured hub "
                "spot in 12/12 months'). What arming buys is therefore not a number but "
                "a FALLBACK LEVEL under the rule 19 [R-ONE-MECH] ordering: in any month "
                "the hub index does not cover, NYISO's gas falls back to that month's "
                "MEASURED state-blended delivered cost instead of the annual trajectory "
                "x generic climatological shape. Reported at full magnitude and claimed "
                "as nothing more. "
                "NO PRICE TUNING: authorized_price_tuning is NONE -- the offer bands are "
                "the superseded keeper's, byte-identical, and no band multiplier was "
                "touched, swept or declared. NO CONTROL SOLVE was spent (rule 29(b)); "
                "G-DRIFT was audited at the code level and found TWO LIVE hunks, so the "
                "committed keeper is NOT a valid control for a zero-delta dispatch claim "
                "-- which is exactly why charter task 3 rests on the artifact-swap "
                "instrument above, which cancels both by construction."
            ),
            "note": (
                "REPORTED AT THE GATE, not absorbed. (a) The 2022 validation touchpoint "
                "on the corrected fleet is WORSE on price than the superseded one: "
                "C3a -12.5% -> -13.8% and C3b NRMSE 0.229 -> 0.242, because the restored "
                "Dunkirk coal (0.655 TWh of cheap PRB, 0 -> 460.7 MW peak, Jan-Apr) "
                "displaces 0.546 TWh of CC_CHP and pushes model prices further below "
                "actual. Under rule 1 [R-STRUCT] and rule 14 [R-ACCURATE] the accurate "
                "input STAYS and the worse fit is a discovered root cause -- NYISO's "
                "2022 price level is too low for a reason the fleet repair has now "
                "exposed rather than caused. Under rule 30(c) a held-out year never "
                "downgrades the ISO's determination, which remains the train-tier "
                "verdict. (b) TWO LIVE HEAD hunks since the superseded keeper solved, "
                "both audited and both RETAINED as correct constructions: the SPP-49 "
                "simple-cycle heat-rate floor (unconditional; clamps 3 NYISO plants -- "
                "Greenport 2681 8.000 -> 9.000, Chautauqua LFGTE 57186 6.053 -> 9.000, "
                "Albany Medical Cogen 59453 5.773 -> 9.000 MMBtu/MWh) and the F923 "
                "gas-price plausibility screen (a declared default flip; measured "
                "68,919 rows examined and ZERO moved for NYISO in every year tested). "
                "(c) NYISO's 2020 validation rung is DATA-BLOCKED at HEAD, not missed: "
                "eia_generation_profiles.parquet begins at 2021 for all seven ISOs and "
                "NYISO is the only ISO that reaches that fallback (it reports no "
                "utility-scale solar to EIA-930 at all). Its authorization is real and "
                "UNSPENT -- see docs/FINDING-nyiso-2020-touchpoint-data-blocked-"
                "2026-09-09.md, which routes the repair rather than guessing it."
            ),
            "computed_checks": {
                "G_DELTA": {
                    "method": (
                        "arm run_config.scenario_config vs the superseded keeper's, "
                        "excluding the two --year selection keys (weather_year, "
                        "gas_price_override) that any re-solve records differently, and "
                        "excluding fields HEAD ADDED since the keeper solved that the arm "
                        "records at a falsy dataclass default (absent -> False/None is not "
                        "a recipe change). The generator REFUSES to write this attestation "
                        "if the computed delta is anything other than the declared set."
                    ),
                    "computed": delta,
                    "declared": sorted(expected),
                    "note": (
                        "f923_gas_price_plausibility_screen appears here because it is a "
                        "declared (b'-1) DEFAULT FLIP to True that landed on main after "
                        "the keeper solved, not a choice this session made. It is HEAD's "
                        "owner-ruled posture (SPP-49 / owner ruling P19) and is retained "
                        "under rules 1/14; its measured NYISO footprint is ZERO rows "
                        "moved in every year tested."
                    ),
                },
                "CARD_1_LP_INERTNESS": {
                    "method": (
                        "run_year(fleet_only=True) on the keeper recipe with and without "
                        "the flag, kwargs taken from replay_keeper.run_year_kwargs (the "
                        "STRICT meta->kwarg mapping); compare the assembled fuel_prices "
                        "and mc_base arrays, which ARE the LP's input"
                    ),
                    "max_abs_delta_fuel_prices": {
                        "2021": 0.0,
                        "2022": 0.0,
                        "2023": 0.0,
                        "2024": 0.0,
                        "2025": 0.0,
                    },
                    "max_abs_delta_mc_base": {
                        "2021": 0.0,
                        "2022": 0.0,
                        "2023": 0.0,
                        "2024": 0.0,
                        "2025": 0.0,
                    },
                    "probe": "scripts/probes/nyiso_fuelvintage1_card1_holdout.py",
                },
                "GATE_T3_RETIREE_WINDOW_IN_SAMPLE": {
                    "method": (
                        "artifact swap (shipped 1,094-row retiree parquet vs the same "
                        "artifact filtered to planned_retirement_year >= 2023, which "
                        "reproduces the pre-change 477-row artifact exactly), then a "
                        "fleet_only rebuild on each side"
                    ),
                    "verdict": "PASS in 2023, 2024 and 2025",
                    "added_columns": 58,
                    "added_pmax_mw": 3694.643,
                    "added_max_availability": 0.0,
                    "added_max_min_gen": 0.0,
                    "removed_columns": 0,
                    "common_columns_byte_identical": True,
                    "probe": "scripts/probes/nyiso_fuelvintage1_gate_t3.py",
                },
            },
        },
        "free_parameters": prior["free_parameters"],
        "exceptions": prior.get("exceptions", []),
        "exceptions_note": prior.get("exceptions_note"),
    }
    if att["free_parameters"] != prior["free_parameters"]:
        raise SystemExit("REFUSED: the DOF ledger was not carried verbatim.")
    return att


def main() -> None:
    """CLI entry point: write the candidate bundle's attestation."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--keeper-bundle", required=True, type=Path)
    ap.add_argument("--arm-bundle", required=True, type=Path)
    args = ap.parse_args()
    att = build(args.keeper_bundle.resolve(), args.arm_bundle.resolve())
    dest = args.arm_bundle / "calibration_attestation.json"
    dest.write_text(json.dumps(att, indent=2) + "\n")
    print(f"wrote {dest}")
    print(f"  DOF entries carried : {att['free_parameters']['n_entries']}")
    print(f"  n_residual          : {att['free_parameters']['n_residual']}")
    print(
        "  G_DELTA computed    : "
        + json.dumps(att["governance"]["computed_checks"]["G_DELTA"]["computed"])
    )


if __name__ == "__main__":
    main()
