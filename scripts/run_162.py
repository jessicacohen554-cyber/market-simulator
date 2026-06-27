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
# (0.78 -> 0.62) so PRB stays in baseload merit on 2024's cheap gas.
PRB_FLOOR = float(os.environ.get("RUN162_PRB_FLOOR", "0.62"))
prb["coal_prb_passthrough_floor"] = PRB_FLOOR

# Lever 1 — CC_REGULAR dearer: ADD +0.12 to the run157 committed/econ_low/
# econ_high deltas (deltas are added to the base curve; see
# run_calibration._apply_offer_curve_deltas).
CC_DELTA = float(os.environ.get("RUN162_CC_DELTA", "0.12"))
deltas = copy.deepcopy(cf["offer_curve_deltas"])
cc = deltas.setdefault("CC_REGULAR", {})
for band in ("committed", "econ_low", "econ_high"):
    cc[band] = cc.get(band, 0.0) + CC_DELTA

years = [2023, 2024, 2025]
if os.environ.get("KEEPER_YEARS"):
    years = [int(y) for y in os.environ["KEEPER_YEARS"].split(",")]

out = os.environ.get("RUN162_OUT", "162")
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
    # --- ALL price adders OFF: pure dispatch, merit order under test ---
    ercot_rtordpa_overlay=False,
    ercot_dam_as_overlay=False,
    energy_reserve_coopt=False,
    # --- the structural reliability floor (driver (b)) ---
    gas_st_netload_drag=True,  # net-load-indexed gas-steam min-gen floor
)
print(
    f"162 done: {run_dir} (CC_DELTA=+{CC_DELTA}, PRB_FLOOR={PRB_FLOOR}, "
    f"gas_st_netload_drag=ON, overlays OFF)"
)
