"""Run ercot 24 = ercot 23 + ct_netload_drag=True.

Identical to ercot 23 (run157 keeper + reliability_floor + moderated
CC/coal deltas + gas_st_netload_drag) with the CT_PEAKER net-load drag
enabled. The drag applies a per-hour min-gen floor on non-_peak
CT_PEAKER tranches, gated to the evening ramp [15, 22) local-standard:

    floor_frac = clip(0.00703 * netload_GW - 0.1427, 0, 0.47)
             applied for hour-of-day in [15, 22), else 0

This targets the C2 system volume gas caveat by closing the CT_PEAKER
under-run (-30.9% all years) — the same forward-native net-load-keyed
mechanism validated for ST_GAS and CAISO CT.

Default ERCOT coefficients from docs/ercot-ct-netload-drag-2026-06.md.
"""

import copy
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
from run_calibration_full import (  # noqa: E402
    _load_reference,
    report_run,
    solve_and_persist,
)

REPO = Path("/home/user/market-simulator")

os.environ["ERCOT_ZONAL_GAS"] = "1"
os.environ["ERCOT_OIL_PRIMARY"] = "1"
os.environ["ERCOT_WEST_NETLOAD_GAS"] = "1"
os.environ["ERCOT_WEST_GAS_DELIVERED_FLOOR"] = "0.4"

cf = json.load(
    open(REPO / "results/calibration/ercot_run157_damas2024/run_config.json")
)["calibration_flags"]

prb = dict(cf["coal_prb_sigmoid_overrides"])
if isinstance(prb.get("wefor_residual_groups"), list):
    prb["wefor_residual_groups"] = frozenset(prb["wefor_residual_groups"])

prb["coal_prb_passthrough_floor"] = 0.76
prb["coal_prb_follower_floor"] = 0.76

deltas = copy.deepcopy(cf["offer_curve_deltas"])
deltas["CC_REGULAR"]["econ_high"] = -0.13
deltas["CC_REGULAR"]["peak"] = 0.25

run_dir = REPO / "results/calibration/ercot_ct_drag_v1"
run_dir.mkdir(parents=True, exist_ok=True)

solve_and_persist(
    [2023, 2024, 2025],
    "ERCOT",
    8760,
    _load_reference(),
    commitment=cf["commitment"],
    screen_coal=cf["commitment_screen_coal"],
    run_dir=run_dir,
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
    prb_overrides=prb,
    coal_bit_sigmoid=cf["coal_bit_passthrough_sigmoid"],
    bit_overrides=cf["coal_bit_sigmoid_overrides"],
    offer_curve_overrides=cf["offer_curve_overrides"],
    offer_curve_deltas=deltas,
    curve_smoothing={"offer_curve_smoothing_mid": 0.35},
    storage_daily_cycling=True,
    storage_vintage_ramp=True,
    battery_dispatch_adder=10.0,
    storage_as_commitment=True,
    ercot_rtordpa_overlay=cf["ercot_rtordpa_overlay"],
    ercot_dam_as_overlay=cf["ercot_dam_as_overlay"],
    ercot_dam_as_overlay_from_year=cf["ercot_dam_as_overlay_from_year"],
    ercot_dam_as_scarcity_threshold=cf["ercot_dam_as_scarcity_threshold"],
    energy_reserve_coopt=cf.get("energy_reserve_coopt", True),
    ercot_load_resource_reserve=cf.get("ercot_load_resource_reserve", True),
    ercot_load_resource_reserve_from_year=cf.get(
        "ercot_load_resource_reserve_from_year", 2023
    ),
    ercot_storage_as_reserve=cf.get("ercot_storage_as_reserve", True),
    ercot_storage_as_reserve_from_year=cf.get(
        "ercot_storage_as_reserve_from_year", 2024
    ),
    reliability_floor=True,
    gas_st_netload_drag=True,
    ct_netload_drag=True,
    note="ercot 24 ct-drag-v1: ercot 23 base + ct_netload_drag=True "
    "(slope 0.00703, intercept -0.1427, cap 0.47, ramp 15-22h) "
    "+ CC_REGULAR econ_high delta -0.13 (was -0.10)",
)
report_run(run_dir)
print("ercot 24 done:", run_dir)
