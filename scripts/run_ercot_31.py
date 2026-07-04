"""Run ercot 31 = ercot 30 (measured-storage P1 ORDC stack) + product credit + gas shape.

The full measured P1 stack: ercot 28's combined product-withholding +
lumped-ORDC-total structure, with (a) the measured battery AS power
reservation in place of the endogenous split (ercot 30), (b) the measured
battery AS award netted pro-rata off the fast products' requirements
(ercot_storage_as_product_credit - without it the products pull the
batteries' awarded ~2-2.8 GW from thermal headroom the real market never
withheld from SCED), and (c) the measured Henry Hub monthly gas shape
(gas_hh_monthly_shape, level-preserving; ercot 29's delta - kept per rule #14
even where truthful gas exposes other residuals). Scored on all three years.
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

YEARS = [int(y) for y in (sys.argv[1:] or [2023, 2024, 2025])]
HOURS = int(os.environ.get("ERCOT31_HOURS", "8760"))
run_dir = Path(
    os.environ.get(
        "ERCOT31_OUT", str(REPO / "results/calibration/ercot_ordc_total_full_v1")
    )
)
run_dir.mkdir(parents=True, exist_ok=True)

solve_and_persist(
    YEARS,
    "ERCOT",
    HOURS,
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
    # Net every year the award is reserved out of the cap — internal
    # consistency: reserving the measured battery award from the storage cap
    # without netting the requirements over-withholds thermal by exactly the
    # awarded MW (the ercot30 2023 blow-up). The 2023 series is the
    # cross-source-calibrated measured award (build_ercot_as_2023.py).
    ercot_storage_as_reserve_from_year=2023,
    reliability_floor=True,
    gas_st_netload_drag=True,
    ct_netload_drag=True,
    chp_export_floor_measured=True,
    ercot_gtc_limits_measured=True,
    # --- ercot 28 deltas (the P1-only combined ORDC-era stack) ---
    ercot_multiproduct_as_coopt=True,
    ercot_as_aware_commitment=False,  # P1 ONLY — the P2 route is shelved
    ercot_ecrs_conservative_deployment=True,
    ercot_ordc_total_reserve=True,
    ercot_storage_as_endogenous=False,  # measured AS power reservation (rule #12)
    ercot_storage_as_product_credit=True,
    gas_hh_monthly_shape=True,
    note="ercot 31 ordc-total-full-v1 (P1-ONLY): ercot 26 gtc-limits base + "
    "multi-product AS co-opt + published 2023 ECRS conservative-deployment "
    "design (no-release at-cap step 2023-06-10..2024-07-31, standing ramp "
    "after) + the lumped ORDC total-reserve family (RTORPA, NPRR568/OBDRR048) "
    "layered on the product stack via an all-class reserve-balance family + "
    "the MEASURED battery AS power reservation (storage_as_commitment + "
    "ercot_storage_as_reserve, the rule-#12-admissible measured input) in "
    "place of the G5 endogenous split, whose current form lacks the "
    "published per-product duration requirements (ECRS 2h / Non-Spin 4h "
    "sustained) and holds 2.1-2.4x the measured battery AS (ercot28 "
    "storage_as audit), flooding the total-reserve curve. No P2/AS-aware "
    "commitment; zero fitted parameters. Plus: the measured battery AS award "
    "netted pro-rata off the fast products (ercot_storage_as_product_credit "
    "- the multi-product analogue of ercot_storage_as_reserve, so products "
    "do not pull the batteries awarded MW from thermal) and the measured HH "
    "monthly gas shape (gas_hh_monthly_shape, level-preserving, the Run-77 "
    "reconciled variant).",
)
report_run(run_dir)
print("ercot 28 done:", run_dir)
