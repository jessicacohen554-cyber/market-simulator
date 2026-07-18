"""ercot41 = the Stage-4 overlay-replacement integration run.

The endogenous multi-product AS co-opt stack REPLACING the measured DAM-AS
overlay (docs/handoffs/ercot-as-coopt-plan-2026-07.md §6). The ercot32 recipe
EXACTLY (P1-only, measured ASPLANNP433 requirements, ercot_load_resource_reserve,
ercot_ordc_total_reserve, ercot_ecrs_conservative_deployment, gas_hh_monthly_shape,
the total ORDC family + products, the measured RTORDPA G2 bridge — all unchanged)
with ONLY these three deltas:

  1. ercot_dam_as_overlay=False        — the measured DAM-AS overlay is retired
                                         (the replacement under test).
  2. ercot_reserve_supply_forward=True — WS-A: the RTOLCAP/RTOFFCAP reserve-supply
                                         cap is sourced from the forward formula
                                         (scarcity.ercot_rtolcap_forward_supply_cap_mw)
                                         instead of the measured parquet. (Stage-1
                                         one-delta probe ercot40 PASSED: Δdw ≤ $0.11.)
  3. Endogenous duration-gated storage AS replacing the measured treatment, as ONE
     CONSISTENT SWAP (never mixed — the ercot30 blow-up):
        storage_as_commitment=False
        ercot_storage_as_reserve=False
        ercot_storage_as_product_credit=False
        ercot_storage_as_endogenous=True
        ercot_storage_as_duration_gate=True   (WS-B, run166: split 1.97x -> 0.55x)

ercot_rtordpa_overlay STAYS (G2 backcast bridge, out of scope — its forward
analogue is RTC+B, already regime-gated forward).

Base recipe is byte-for-byte scripts/archive/run_ercot40_rtolcap_fwd.py (= ercot32 EXACTLY
+ ercot_reserve_supply_forward=True); this script applies deltas 1 and 3 on top.

Honesty gate: nothing on the AS path reads LMP/RTSPP/MCPC/RTORPA. The measured
ASPLANNP433 requirement is an admissible published procurement quantity (like fuel
prices), unchanged from ercot32.

Run: python scripts/archive/run_ercot41_integration.py [2023 2024 2025]
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
HOURS = int(os.environ.get("ERCOT41_HOURS", "8760"))
run_dir = Path(
    os.environ.get(
        "ERCOT41_OUT", str(REPO / "results/calibration/ercot41_integration_2026-07")
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
    # --- delta 3: endogenous duration-gated storage AS (one consistent swap) ---
    storage_as_commitment=False,  # was True (measured treatment OFF)
    ercot_storage_as_reserve=False,  # was True
    ercot_storage_as_product_credit=False,  # was True
    ercot_storage_as_endogenous=True,  # was False (endogenous split ON)
    ercot_storage_as_duration_gate=True,  # WS-B published ESR SOC durations
    ercot_storage_as_reserve_from_year=2023,
    ercot_rtordpa_overlay=cf["ercot_rtordpa_overlay"],  # G2 bridge STAYS
    # --- delta 1: retire the measured DAM-AS overlay ---
    ercot_dam_as_overlay=False,  # was cf["ercot_dam_as_overlay"] (True)
    ercot_dam_as_overlay_from_year=cf["ercot_dam_as_overlay_from_year"],
    ercot_dam_as_scarcity_threshold=cf["ercot_dam_as_scarcity_threshold"],
    energy_reserve_coopt=cf.get("energy_reserve_coopt", True),
    ercot_load_resource_reserve=cf.get("ercot_load_resource_reserve", True),
    ercot_load_resource_reserve_from_year=cf.get(
        "ercot_load_resource_reserve_from_year", 2023
    ),
    reliability_floor=True,
    gas_st_netload_drag=True,
    ct_netload_drag=True,
    chp_export_floor_measured=True,
    ercot_gtc_limits_measured=True,
    ercot_multiproduct_as_coopt=True,
    ercot_as_aware_commitment=False,  # P1 ONLY
    ercot_ecrs_conservative_deployment=True,
    ercot_ordc_total_reserve=True,
    ercot_reserve_supply_cap=True,  # cap lever on…
    # --- delta 2: WS-A forward supply formula (measured cap → formula) ---
    ercot_reserve_supply_forward=True,
    gas_hh_monthly_shape=True,
    note="ercot41 Stage-4 integration (P1-ONLY): ercot32 recipe EXACTLY + THREE "
    "deltas replacing the measured DAM-AS overlay with the endogenous multi-product "
    "AS co-opt stack. (1) ercot_dam_as_overlay=False; (2) ercot_reserve_supply_"
    "forward=True (WS-A: RTOLCAP/RTOFFCAP cap from the forward formula, stage-1 "
    "probe ercot40 PASSED Δdw≤$0.11); (3) endogenous duration-gated storage AS "
    "replacing the measured treatment as one consistent swap (storage_as_commitment/"
    "ercot_storage_as_reserve/ercot_storage_as_product_credit OFF, ercot_storage_as_"
    "endogenous + ercot_storage_as_duration_gate ON; WS-B run166 split 1.97x->0.55x). "
    "RTORDPA G2 bridge STAYS. Measured ASPLANNP433 requirements unchanged (admissible). "
    "Honesty gate: no LMP/RTSPP/MCPC/RTORPA read on the AS path. Scored vs RT actuals, "
    "gates G-1..G-7 (plan §6), against the ercot33 ex-overlay baseline.",
)
report_run(run_dir)
print("ercot41 done:", run_dir)
