"""Run 159 = run157's exact config with the DAM-AS overlay swapped for the
endogenous multi-product AS co-optimization. Calls solve_and_persist directly
with run157's recorded calibration_flags so the baseline is byte-faithful;
the only deltas are: ercot_dam_as_overlay False (was True), and
energy_reserve_coopt + ercot_multiproduct_as_coopt True (were absent). P1-only.
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

# wefor_residual_groups recorded as a list; the solver wants a frozenset.
prb = dict(cf["coal_prb_sigmoid_overrides"])
if isinstance(prb.get("wefor_residual_groups"), list):
    prb["wefor_residual_groups"] = frozenset(prb["wefor_residual_groups"])

run_dir = REPO / "results/calibration/159"
run_dir.mkdir(parents=True, exist_ok=True)

solve_and_persist(
    [2023, 2024, 2025],
    "ERCOT",
    8760,
    _load_reference(),
    commitment=cf["commitment"],  # False (P1-only)
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
    offer_curve_deltas=cf["offer_curve_deltas"],
    ercot_rtordpa_overlay=cf["ercot_rtordpa_overlay"],  # True (G2 bridge, kept)
    ercot_dam_as_overlay=False,  # SWAP OFF — replaced by the endogenous co-opt
    ercot_dam_as_overlay_from_year=cf["ercot_dam_as_overlay_from_year"],
    ercot_dam_as_scarcity_threshold=cf["ercot_dam_as_scarcity_threshold"],
    energy_reserve_coopt=True,  # ADD
    ercot_multiproduct_as_coopt=True,  # ADD
)
print("159 done:", run_dir)
