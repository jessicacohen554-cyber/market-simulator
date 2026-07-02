"""Run ercot 26 = ercot 25 + ercot_gtc_limits_measured=True.

Identical to ercot 25 (ercot 24 ct-drag-v1 base + the measured CHP
steam-following export floor) with the measured ERCOT GTC transfer limits
enabled: the export capability of the links that carry ERCOT's published
Generic Transmission Constraints (PNHNDL -> Panhandle->North, WESTEX -> the
two West export links 8:3, NE_LOB -> Northeast->North) follows the hourly
NP6-86 measured limit series (gtc-limits clean datatype) instead of the
static ttc_mw, with the import direction kept at the static thermal rating
(ScenarioConfig.ercot_gtc_limits_measured).

Motivation (C1 CC_REGULAR 2023, the last hard caveat besides C2 gas 2025):
the model under-curtails 2023 renewables by ~4.1 TWh (2.90 model vs 6.96
ISO-reported; run report [3e]) because the static limit-at-bind means miss
the hourly variation of the stability limits — the Oct-Mar Panhandle/West
GTC season concentrates the miss. The extra renewable energy displaces the
marginal class (CC_REGULAR, -8.56 TWh vs band +/-4.46), which in reality
served that load. Curtailment must emerge endogenously from the binding
measured limits; the reported HSL curtailment totals stay the VALIDATION
target. Requires the NP6-86 archives under
data/raw/iso-specific-transmission/ curated via scripts/curate_gtc_limits.py;
years without the partition (or without measured HSL potential) keep the
static limits, logged.
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

run_dir = REPO / "results/calibration/ercot_gtc_limits_v1"
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
    chp_export_floor_measured=True,
    ercot_gtc_limits_measured=True,
    note="ercot 26 gtc-limits-v1: ercot 25 chp-floor-v1 base + "
    "ercot_gtc_limits_measured=True (measured hourly NP6-86 GTC export "
    "limits on the PNHNDL/WESTEX/NE_LOB links; endogenous West/Panhandle "
    "curtailment from binding published limits)",
)
report_run(run_dir)
print("ercot 26 done:", run_dir)
