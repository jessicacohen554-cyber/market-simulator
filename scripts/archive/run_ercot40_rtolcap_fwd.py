"""ercot40 = ercot32 EXACTLY + ercot_reserve_supply_forward=True (the ONLY delta).

The WS-A one-delta backcast probe (run163 pattern,
docs/handoffs/ercot-rtolcap-forward-2026-07.md): the ercot32 recipe with the
single change that the RTOLCAP/RTOFFCAP reserve-supply cap is sourced from the
FORWARD FORMULA (scarcity.ercot_rtolcap_forward_supply_cap_mw) instead of the
measured ercot_<year>_ordc_reserves_hourly.parquet. Everything else — offer
curves, measured requirements, ORDC total family + products + ECRS design, the
measured storage-AS treatment, the DAM-AS overlay — is byte-for-byte ercot32, so
the delta isolates the supply formula as the run163-style single change.

Gate (vs ercot32, the measured-capped baseline): the formula-capped run tracks
the measured-capped baseline (annual demand-weighted price within ~$2, acute days
and tail counts close); differences are root-caused in the handoff.

Run: python scripts/archive/run_ercot40_rtolcap_fwd.py [2023 2024 2025]
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
HOURS = int(os.environ.get("ERCOT40_HOURS", "8760"))
run_dir = Path(
    os.environ.get(
        "ERCOT40_OUT", str(REPO / "results/calibration/ercot_rtolcap_forward_v1")
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
    ercot_storage_as_reserve_from_year=2023,
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
    ercot_reserve_supply_forward=True,  # …sourced from the FORWARD FORMULA (the ONLY delta)
    ercot_storage_as_endogenous=False,
    ercot_storage_as_product_credit=True,
    gas_hh_monthly_shape=True,
    note="ercot40 rtolcap-forward-v1 (P1-ONLY): ercot32 recipe EXACTLY + "
    "ercot_reserve_supply_forward=True — the RTOLCAP/RTOFFCAP reserve-supply cap "
    "is rebuilt from the WS-A forward formula "
    "(scarcity.ercot_rtolcap_forward_supply_cap_mw: derived per-class on-line "
    "headroom-realization shares × the fleet's reserve-eligible capacity, keyed "
    "to the model's own forecast net-load, + the measured storage-AS term) "
    "instead of the measured ercot_<year>_ordc_reserves_hourly.parquet. The one "
    "delta (measured cap → formula cap) isolates the forward supply analogue; "
    "everything else is byte-for-byte ercot32. Identification gate (validate_"
    "ercot_rtolcap_forward.py) PASSED: coverage median ~2.08× (not the ercot27 "
    "1.0× exact-coverage artifact), RTOLCAP annual mean +11/-6/-12% 2023/24/25 "
    "(documented residuals: 2023 real-time scarcity depletion, 2025 storage/"
    "commitment growth beyond the fixed backcast base). Nothing on the path "
    "reads LMP/RTSPP/MCPC/RTORPA (honesty gate).",
)
report_run(run_dir)
print("ercot40 done:", run_dir)
