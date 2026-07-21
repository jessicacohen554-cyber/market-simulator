"""caiso-110 DIAGNOSTIC (throwaway, 2024-only): endogenous WECC-West node smoke test.

Solves ONE year (2024) with the caiso-102 keeper recipe PLUS
``caiso_endogenous_wecc_node=True`` — the WECC_import node becomes a real
co-optimized WECC-West neighbor zone (docs/handoffs/caiso-endogenous-wecc-node-
design-2026-07-21.md). This is a THROWAWAY single-year diagnostic to validate
the wiring (does it solve? is the West zone feasible / no VOLL slack? what is
the net import + belly shape + gas/CO2?) and to calibrate the West thermal MC
BEFORE the full 3-year A/B. NOT registered (rule 16 — a keeper is all-years).

Usage: python scripts/probes/_caiso110_endogenous_diag.py
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
    overrides["caiso_ra_startup_trajectory"] = True  # caiso-96
    overrides["caiso_dsw_daytime_evening_trim"] = True  # caiso-97
    overrides["caiso_storage_shape_anchor"] = True  # caiso-99
    overrides["caiso_endogenous_wecc_node"] = True  # caiso-110 (THE delta)
    out = ROOT / "caiso110_endog_diag"
    out.mkdir(parents=True, exist_ok=True)
    note = (
        "caiso-110 DIAGNOSTIC (throwaway, 2024-only): endogenous WECC-West node "
        "smoke test on the caiso-102 keeper recipe. NOT registered."
    )

    solve_and_persist(
        [2024],  # single-year throwaway diagnostic (NOT a keeper)
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
    print(f"DONE caiso-110 diagnostic -> {out}")


if __name__ == "__main__":
    main()
