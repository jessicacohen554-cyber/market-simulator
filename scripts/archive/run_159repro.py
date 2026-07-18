"""Re-solve run159 (measured AS requirement) into 159repro for a clean baseline.

Same recipe as run_159.py; separate out-dir so its system.parquet can be diffed
against run163 (forward requirement) in the same environment.
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
run_dir = REPO / "results/calibration/159repro"
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
)
print("159repro done:", run_dir)
