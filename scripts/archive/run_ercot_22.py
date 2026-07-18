"""Run ercot 22 = run157 keeper + reliability_floor + moderated CC/coal deltas.

Starting from the run157 keeper config (ercot_run157_damas2024), moderates the
three offer-curve deltas from ercot 21 that overcorrected 2023 ($28.57 vs
$48.36 actual) while keeping the 2024/2025 improvements.

Ercot 21 moved three levers too far — the CC economic tranche got too cheap
at 2023's $2.54/MWh gas, pulling clearing prices down across the board.
This run splits the difference with the keeper (run157) values:

  1. CC_REGULAR econ_high delta: -0.10 (keeper -0.20, ercot 21 0.0)
     Halfway point — CC economic tranche cheaper than keeper but not as
     aggressive as ercot 21.

  2. CC_REGULAR peak delta: +0.25 (keeper +0.32, ercot 21 +0.18)
     Moderates duct-firing discount; keeps some peak-hour improvement.

  3. PRB sigmoid floor: 0.76 (keeper 0.78, ercot 21 0.74)
     Moderate coal bid aggressiveness — less overcorrection in 2023.

  4. reliability_floor=True (carried from ercot 21).
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

# --- Set env vars to match run157's scenario_config features ---
os.environ["ERCOT_ZONAL_GAS"] = "1"
os.environ["ERCOT_OIL_PRIMARY"] = "1"
os.environ["ERCOT_WEST_NETLOAD_GAS"] = "1"
os.environ["ERCOT_WEST_GAS_DELIVERED_FLOOR"] = "0.4"

cf = json.load(
    open(REPO / "results/calibration/ercot_run157_damas2024/run_config.json")
)["calibration_flags"]

# --- Build prb_overrides from the keeper config ---
prb = dict(cf["coal_prb_sigmoid_overrides"])
if isinstance(prb.get("wefor_residual_groups"), list):
    prb["wefor_residual_groups"] = frozenset(prb["wefor_residual_groups"])

# Delta 3: PRB sigmoid floor 0.78 -> 0.76 (split the difference)
prb["coal_prb_passthrough_floor"] = 0.76
prb["coal_prb_follower_floor"] = 0.76

# --- Build offer_curve_deltas with moderated CC_REGULAR changes ---
deltas = copy.deepcopy(cf["offer_curve_deltas"])
# Delta 1: CC_REGULAR econ_high -0.20 -> -0.10 (split the difference)
deltas["CC_REGULAR"]["econ_high"] = -0.10
# Delta 2: CC_REGULAR peak +0.32 -> +0.25 (split the difference)
deltas["CC_REGULAR"]["peak"] = 0.25

run_dir = REPO / "results/calibration/ercot_cc_coal_rebalance_v2"
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
    note="ercot 22 cc-coal-rebalance-v2: run157 base + reliability_floor, "
    "CC_REGULAR econ_high delta -0.10, peak delta +0.25, PRB sigmoid floor 0.76",
)
report_run(run_dir)
print("ercot 22 done:", run_dir)
