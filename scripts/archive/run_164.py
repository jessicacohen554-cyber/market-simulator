"""Run 164 = run163 + ENDOGENOUS storage energy-vs-AS + RTOLCAP supply cap (G5).

Identical to run_163.py (run157's keeper recipe with the DAM-AS overlay swapped
for the endogenous multi-product AS co-opt, forward AS requirement, P1-only) with
two deltas that make the BATTERY's energy-vs-AS split the LP's choice instead of
the measured 60-Day DAM award:

  * ercot_storage_as_endogenous=True — replaces the measured battery AS-award
    reservation (storage_as_commitment + ercot_storage_as_reserve). The full
    battery power cap is handed to the co-opt and a unit's upward-reserve room
    (cap − discharge + charge) competes with arbitrage on the same cap, priced by
    the per-product AS demand curves. Also writes storage_as.parquet (the
    modeled-vs-measured AS-vs-energy split, the validation artifact).
  * ercot_reserve_supply_cap=True — the cleared storage AS counts toward the
    measured RTOLCAP online-responsive supply (which already includes online
    batteries: RTOLCAP grows 13.5→16.7→19.1 GW with the 2023→25 battery fleet),
    consistent with the 300b89c cap.

The acute/tail scarcity incidence should HOLD vs run163; the measured 60-Day DAM
awards are the backcast realization the chosen split is validated against, never
pinned to it.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

REPO = Path("/home/user/market-simulator")
cf = json.load(
    open(REPO / "results/calibration/ercot_run157_damas2024/run_config.json")
)["calibration_flags"]

prb = dict(cf["coal_prb_sigmoid_overrides"])
if isinstance(prb.get("wefor_residual_groups"), list):
    prb["wefor_residual_groups"] = frozenset(prb["wefor_residual_groups"])

run_dir = REPO / "results/calibration/164"
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
    offer_curve_deltas=cf["offer_curve_deltas"],
    ercot_rtordpa_overlay=cf["ercot_rtordpa_overlay"],
    ercot_dam_as_overlay=False,
    ercot_dam_as_overlay_from_year=cf["ercot_dam_as_overlay_from_year"],
    ercot_dam_as_scarcity_threshold=cf["ercot_dam_as_scarcity_threshold"],
    energy_reserve_coopt=True,
    ercot_multiproduct_as_coopt=True,
    ercot_as_forward_requirement=True,
    ercot_storage_as_endogenous=True,  # delta 1: battery CHOOSES energy vs AS
    ercot_reserve_supply_cap=True,  # delta 2: storage AS counts toward RTOLCAP
    ercot_reserve_supply_cap_from_year=2023,
)
print("164 done:", run_dir)
