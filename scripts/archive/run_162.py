"""Run 162 = the ENERGY-BASE / merit-order track for the broad ERCOT May.

The reserve-supply track (run161) proved the broad May-2024 residual is an
ENERGY-BASE / merit-order miss, not a reserve/ORDC/scarcity one: the LP runs
too much CC_REGULAR (+9.9%) and too little coal-PRB / ST_GAS (-37%) / CT_PEAKER
(-39%), so on cheap 2024 gas the wrong (too-cheap) unit is marginal and the May
LMP clears low. This run attacks that merit order directly, with ALL price
adders OFF so the merit order is what's tested (pure dispatch):

  * DAM-AS overlay OFF, energy+reserve co-opt OFF, RTORDPA overlay OFF
    -> no reserve/ORDC/AS lift; the energy LMP must rise because the correct,
       pricier unit becomes marginal, not via an adder (CLAUDE.md #1/#11).
  * CC_REGULAR dearer: +0.12 heat-rate-mult delta ADDED on the
    committed / econ_low / econ_high bands (on top of run157's deltas) so the
    over-running combined cycle ranks above coal/steam where it should.
  * Coal-PRB cheaper: coal_prb_passthrough_floor 0.78 -> 0.62 so PRB holds
    baseload against cheap gas and runs more (the floor is the cheap-gas
    passthrough DISCOUNT; lower = cheaper PRB = more dispatch).
  * ST_GAS reliability floor: gas_st_netload_drag ON — the net-load-indexed
    min-gen floor that keeps gas-steam online at part-load (driver (b), the
    local-reliability commitment the energy-only LP can't see).

Score the C1 fuel-mix gate first (scripts/calibration_verdict.py / the volume
check): CC_REGULAR +9.9% -> ~0, coal-PRB / ST_GAS / CT_PEAKER under -> ~0.
Then the May gate (scripts/probes/_eval_may_gate.py <bundle> 2023 2024 2025).
If CT_PEAKER is still short, add the ct_netload_drag floor; if CC is still over
or PRB still short, nudge CC_DELTA up / PRB floor down.

Set KEEPER_YEARS=2024 for a fast single-year diagnostic; default solves all
years (CLAUDE.md #14 — a registered keeper must span every scoreable year).
"""

import copy
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

REPO = Path("/home/user/market-simulator")
cf = json.load(
    open(REPO / "results/calibration/ercot_run157_damas2024/run_config.json")
)["calibration_flags"]

# wefor_residual_groups recorded as a list; the solver wants a frozenset.
prb = dict(cf["coal_prb_sigmoid_overrides"])
if isinstance(prb.get("wefor_residual_groups"), list):
    prb["wefor_residual_groups"] = frozenset(prb["wefor_residual_groups"])

# Lever 2 — coal-PRB cheaper: lower the cheap-gas passthrough discount floor
# (0.78 -> 0.62) so PRB stays in baseload merit on 2024's cheap gas. The PRB
# sigmoid is gas-keyed (gas_mid 2.85, gas_slope 2.5), so the floor only sets the
# CHEAP-gas asymptote: dropping it pulls PRB up in 2024 (gas $2.19, well below
# the midpoint) while 2025 (gas $3.52, above it) sits near the ceiling and barely
# moves — the floor self-targets the years where CC over-runs. The tiered curve's
# low-must-run follower tier gets the same treatment.
PRB_FLOOR = float(os.environ.get("RUN162_PRB_FLOOR", "0.62"))
PRB_FOLLOWER_FLOOR = float(os.environ.get("RUN162_PRB_FOLLOWER_FLOOR", "0.78"))
prb["coal_prb_passthrough_floor"] = PRB_FLOOR
prb["coal_prb_follower_floor"] = PRB_FOLLOWER_FLOOR
# Optional: sharpen the gas-keyed sigmoid knee (default 2.85). Lowering gas_mid
# concentrates the cheap-gas PRB discount nearer 2024's $2.19 gas, so the floor
# cut bites 2024 harder than 2023 ($2.54, past the lower knee) and spares 2025
# ($3.52, near the ceiling) — the multi-year-safe way to pull only 2024 PRB.
PRB_GAS_MID = os.environ.get("RUN162_PRB_GAS_MID")
if PRB_GAS_MID:
    prb["coal_prb_passthrough_gas_mid"] = float(PRB_GAS_MID)
    prb["coal_prb_follower_gas_mid"] = float(PRB_GAS_MID)

# Lever 1 — CC_REGULAR dearer: ADD +0.12 to the run157 committed/econ_low/
# econ_high deltas (deltas are added to the base curve; see
# run_calibration._apply_offer_curve_deltas).
# Lever 3 — CT_PEAKER evening-ramp net-load reliability floor (the forward-native
# replacement for the ct_mustrun_per_plant actuals pin): lifts the deep CT
# under-run toward actual, displacing the over-running CC in peak hours.
CT_DRAG = os.environ.get("RUN162_CT_DRAG", "1") == "1"

CC_DELTA = float(os.environ.get("RUN162_CC_DELTA", "0.12"))
deltas = copy.deepcopy(cf["offer_curve_deltas"])
cc = deltas.setdefault("CC_REGULAR", {})
for band in ("committed", "econ_low", "econ_high"):
    cc[band] = cc.get(band, 0.0) + CC_DELTA

years = [2023, 2024, 2025]
if os.environ.get("KEEPER_YEARS"):
    years = [int(y) for y in os.environ["KEEPER_YEARS"].split(",")]

# RUN162_OVERLAY=1 produces the KEEPER variant (162f): the corrected merit order
# PLUS run157's measured pre-RTC+B scarcity stack (DAM-AS overlay + single-
# product energy/reserve co-opt + load-resource / storage reserves + RTORDPA
# 2023 bridge), which restores the broad-month PRICE LEVEL on top of the now-
# correct merit order.
# RUN162_FWDAS=1 swaps the measured DAM-AS overlay for the FULL endogenous
# forward-AS co-opt stack (runs 163–165 mechanisms): multi-product co-opt +
# forward AS requirement + storage-AS-endogenous + load-resource RRS-UFR.
# Tests whether the endogenous stack can form the 2025 scarcity signal that
# lifts gas-family dispatch into the C2 band without re-tuning any offer lever.
# Default (both off) = pure dispatch; the merit order isolated for the C1 gate.
OVERLAY = os.environ.get("RUN162_OVERLAY", "0") == "1"
FWDAS = os.environ.get("RUN162_FWDAS", "0") == "1"

if FWDAS:
    # Full endogenous forward-AS co-opt stack: multi-product + forward
    # requirement + storage-AS-endogenous (run164 G5) + load-resource RRS-UFR
    # (run165 G4).  DAM-AS overlay OFF — the endogenous co-opt must form its
    # own scarcity signal.  RTORDPA bridge kept for 2023 (structural: pre-RTC+B
    # era had no ORDC-like scarcity in the base energy LP).
    overlay_kwargs = dict(
        energy_reserve_coopt=True,
        ercot_multiproduct_as_coopt=True,
        ercot_as_forward_requirement=True,
        ercot_storage_as_endogenous=True,
        ercot_reserve_supply_cap=True,
        ercot_reserve_supply_cap_from_year=2023,
        ercot_load_resource_reserve=True,
        ercot_load_resource_reserve_from_year=2023,
        ercot_rtordpa_overlay=True,
        ercot_dam_as_overlay=False,
        battery_dispatch_adder=10.0,
    )
elif OVERLAY:
    overlay_kwargs = dict(
        ercot_rtordpa_overlay=True,
        ercot_dam_as_overlay=True,
        ercot_dam_as_overlay_from_year=cf["ercot_dam_as_overlay_from_year"],
        ercot_dam_as_scarcity_threshold=cf["ercot_dam_as_scarcity_threshold"],
        energy_reserve_coopt=True,
        ercot_load_resource_reserve=True,
        ercot_load_resource_reserve_from_year=2023,
        ercot_storage_as_reserve=True,
        ercot_storage_as_reserve_from_year=2024,
        storage_as_commitment=True,
        battery_dispatch_adder=10.0,
    )
else:
    overlay_kwargs = dict(
        # ALL price adders OFF: pure dispatch, merit order under test.
        ercot_rtordpa_overlay=False,
        ercot_dam_as_overlay=False,
        energy_reserve_coopt=False,
    )

out = os.environ.get("RUN162_OUT", "162fwdas" if FWDAS else "162")
run_dir = REPO / "results/calibration" / out
run_dir.mkdir(parents=True, exist_ok=True)

solve_and_persist(
    years,
    "ERCOT",
    8760,
    _load_reference(),
    commitment=cf["commitment"],  # False (no energy-only P2)
    screen_coal=cf["commitment_screen_coal"],  # True
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
    offer_curve_deltas=deltas,  # CC_REGULAR bands nudged +CC_DELTA dearer
    # --- scarcity overlays: off (pure dispatch) or run157 keeper stack ---
    **overlay_kwargs,
    # --- the structural reliability floors (driver (b)) ---
    gas_st_netload_drag=True,  # net-load-indexed gas-steam min-gen floor
    ct_netload_drag=CT_DRAG,  # evening-ramp net-load CT_PEAKER min-gen floor
)
_mode = "FWDAS" if FWDAS else ("KEEPER" if OVERLAY else "OFF")
print(
    f"162 done: {run_dir} (CC_DELTA=+{CC_DELTA}, PRB_FLOOR={PRB_FLOOR}, "
    f"PRB_FOLLOWER_FLOOR={PRB_FOLLOWER_FLOOR}, gas_st_netload_drag=ON, "
    f"ct_netload_drag={'ON' if CT_DRAG else 'OFF'}, "
    f"overlays={_mode})"
)
