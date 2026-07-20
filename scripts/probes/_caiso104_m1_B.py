"""caiso-104 M1 B-leg: the keeper recipe + the DA charge-allocation schedule.

Single pre-registered delta vs the same-machine `caiso102_repro_A` baseline
(FINDING-caiso104 §3): RECIPE-IDENTICAL to `_caiso102_repro_A.py main` (the
promoted caiso-102-hourfix keeper recipe) with ONLY
`caiso_charge_allocation_schedule=True` added (the owner-granted M1 belly
mechanism — docs/handoffs/caiso-103-belly-allocation-ask-2026-07-19.md) and
the output directory changed to the registered `caiso104_m1_B`.

Gates are pre-registered in
`results/calibration/FINDING-caiso104-m1-meve1-execution-2026-07-20.md` §3
BEFORE this solve; the run is registered whatever the result (rule 15).

Usage: python scripts/probes/_caiso104_m1_B.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _caiso95_repro_A import BASE, _keeper_overrides  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"


def main() -> None:
    cf = json.loads((BASE / "run_config.json").read_text())["calibration_flags"]
    overrides = _keeper_overrides(cf)
    overrides["caiso_ra_startup_trajectory"] = True  # caiso-96 (owner carry ruling)
    overrides["caiso_dsw_daytime_evening_trim"] = True  # caiso-97 (the WP-2 delta)
    overrides["caiso_storage_shape_anchor"] = True  # caiso-99 (the keeper delta)
    overrides["caiso_charge_allocation_schedule"] = True  # caiso-104 M1 (THE delta)
    out = ROOT / "caiso104_m1_B"
    out.mkdir(parents=True, exist_ok=True)
    note = (
        "caiso-104 M1 B-leg -- keeper recipe + caiso_charge_allocation_schedule "
        "(the owner-granted DA charge-allocation schedule, single delta vs the "
        "same-machine caiso102_repro_A; gates pre-registered in "
        "FINDING-caiso104 s3), 2023-2025"
    )

    solve_and_persist(
        cf["years"],  # all three years in one call (rule 16)
        cf["iso"],
        cf["hours"],
        _load_reference(),
        commitment=cf["commitment"],
        screen_coal=cf["commitment_screen_coal"],
        run_dir=out,
        coal_lignite_mustrun=cf["coal_lignite_mustrun"],
        coal_prb_mustrun=cf["coal_prb_mustrun"],
        coal_prb_passthrough=cf["coal_prb_passthrough"],
        outage_source=cf["outage_source"],
        coal_prb_passthrough_sigmoid=cf["coal_prb_passthrough_sigmoid"],
        coal_mustrun_per_plant=cf["coal_mustrun_per_plant"],
        retiree_cems_cap=cf["retiree_cems_cap"],
        ct_mustrun_per_plant=cf["ct_mustrun_per_plant"],
        ct_mustrun_floor_frac=cf["ct_mustrun_floor_frac"],
        coal_drop_pof=cf["coal_drop_pof"],
        coal_prb_passthrough_tiered=cf["coal_prb_passthrough_tiered"],
        prb_overrides=overrides,
        coal_bit_sigmoid=cf["coal_bit_passthrough_sigmoid"],
        bit_overrides=cf["coal_bit_sigmoid_overrides"],
        ercot_rtordpa_overlay=cf["ercot_rtordpa_overlay"],
        ercot_dam_as_overlay=cf["ercot_dam_as_overlay"],
        ercot_dam_as_overlay_from_year=cf["ercot_dam_as_overlay_from_year"],
        ercot_dam_as_scarcity_threshold=cf["ercot_dam_as_scarcity_threshold"],
        offer_curve_overrides=cf["offer_curve_overrides"],
        offer_curve_deltas=cf["offer_curve_deltas"],
        curve_smoothing={
            "offer_curve_smoothing_n": 6,
            "offer_curve_smoothing_exp": 1.0,
            "offer_curve_smoothing_mid": None,
        },
        priced_interchange=cf["priced_interchange"],
        hydro_backfill_year=2024,
        hydro_eia930_monthly=True,
        capacity_deliverability_limits=True,
        caiso_ra_mustoffer=True,
        caiso_ra_min_load_frac=0.26,
        caiso_ra_startup_bridge=True,
        caiso_ra_bridge_decommit=True,
        caiso_gas_floor_frac=0.8,
        caiso_solar_deliverability=True,
        caiso_solar_endogenous_spill=True,
        caiso_per_hub_intertie=True,
        caiso_perhub_firm_base=True,
        caiso_corridor_flow_limit=True,
        temp_dependent_derate=True,
        ct_netload_drag=False,
        caiso_offer_surface_measured=True,
        caiso_offer_surface_conditional=True,
        note=note,
    )
    print(f"DONE caiso-104 M1 B-leg -> {out}")


if __name__ == "__main__":
    main()
