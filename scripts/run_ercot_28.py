"""Run ercot 28 = ercot 26 (gtc-limits) + the P1-ONLY ORDC-era price-formation stack.

The named follow-up from the ercot 27 probe (2026-07-03 calibration-log entry):
adopt the P1-level structure the probe proved (the 2023 scarcity-month
improvement was already present in P1) and make the product-level withholding
AND the lumped ORDC total-reserve family work TOGETHER — in ercot 27 they were
alternatives (the multi-product swap dropped the published RTORPA mechanism and
even P1's deep tail collapsed: Aug-2023 −$88.7 vs keeper −$46, >$1000 hours 28
vs 61). Zero offer-curve retuning, zero fitted parameters, and NO P2 pass of
any kind — P1 (no commitment) is THE main run (CLAUDE.md Dispatch & Commitment;
spec §1.6); the AS-aware commitment route is shelved.

Four structural pieces on the ercot 26 recipe:

* **Multi-product AS co-opt (P1).** ``ercot_multiproduct_as_coopt``: one
  additive, cascading demand curve per AS product (RegUp/RRS/ECRS/NonSpin,
  measured ASPLANNP433 requirements), shared additive headroom (fast/all
  tiers). The product carve-outs withhold capacity from energy endogenously.

* **Published 2023 ECRS deployment design.**
  ``ercot_ecrs_conservative_deployment``: no price-based ECRS release
  2023-06-10 → 2024-07-31 (at-cap demand step per IMM 2023 SOM; the PUCT
  rejected NPRR1224's $750 floor 2024-07-25), standing VOLL-anchored ramp from
  2024-08-01. Published dates only — docs/parameter-citations.md.

* **Lumped ORDC total-reserve family (NEW, the ercot 28 delta).**
  ``ercot_ordc_total_reserve``: the published RTORPA mechanism (NPRR568 /
  OBDRR048) as one extra ALL-CLASS reserve-balance family drawing on the sum
  of every product's cleared reserve — product withholding and the
  total-reserve LOLP×VOLL curve price together, the faithful pre-RTC+B stack.
  No new reserve columns, no new headroom, nothing double-procured.

* **Endogenous storage energy-vs-AS split (G5).**
  ``ercot_storage_as_endogenous``: the battery chooses energy vs AS inside
  the co-opt (the measured award stays validation-only).

The measured RTORDPA overlay (2023-heavy) and DAM-AS overlay (2024+) stay ON
with their series persisted per-column, so the one-event-one-channel overlap
with the endogenous co-opt scarcity can be QUANTIFIED from the bundle.
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
HOURS = int(os.environ.get("ERCOT28_HOURS", "8760"))
run_dir = Path(
    os.environ.get("ERCOT28_OUT", str(REPO / "results/calibration/ercot_ordc_total_v1"))
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
    ercot_storage_as_reserve_from_year=cf.get(
        "ercot_storage_as_reserve_from_year", 2024
    ),
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
    ercot_storage_as_endogenous=True,
    note="ercot 28 ordc-total-v1 (P1-ONLY): ercot 26 gtc-limits base + "
    "multi-product AS co-opt + published 2023 ECRS conservative-deployment "
    "design (no-release at-cap step 2023-06-10..2024-07-31, standing ramp "
    "after) + the lumped ORDC total-reserve family (RTORPA, NPRR568/OBDRR048) "
    "layered on the product stack via an all-class reserve-balance family + "
    "endogenous storage energy-vs-AS (G5). No P2/AS-aware commitment "
    "(shelved per the ercot27 verdict); zero fitted parameters.",
)
report_run(run_dir)
print("ercot 28 done:", run_dir)
