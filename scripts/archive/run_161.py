"""Run 161 = the ERCOT reserve-supply re-scope (RTOLCAP cap + ORDC adder).

run157's keeper recipe with the measured DAM-AS overlay SWAPPED for the
pre-RTC+B ORDC-regime construction the market actually used:

  * energy+reserve co-optimization ON (single lumped contingency-reserve product,
    the published NP6-576-ER ORDC demand curve via ordc_lolp_params_path),
  * the reserve SUPPLY capped at the MEASURED on-line responsive capability
    (RTOLCAP) so modeled reserve tightens into the ~8-12 GW band where ERCOT's
    ORDC adder actually fires (the broad-month phantom-headroom fix), and
  * the capped reserve dual added to the energy LMP as the ORDC price adder
    (RTORPA) for ORDC-regime years (RTSPP = SPP + ORDC(online reserves)) — the
    energy-only-SCED-plus-adder design of 2023-2025, gated OFF for RTC+B.

Measured supply (RTOLCAP) + published-rule demand curve, no price fit. Set
KEEPER_YEARS=2024 for the fast single-year diagnostic; default solves all years.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

REPO = Path("/home/user/market-simulator")
ORDC_TABLE = str(REPO / "data/raw/_validation-source/ercot_ordc_lolp_params.csv")
cf = json.load(
    open(REPO / "results/calibration/ercot_run157_damas2024/run_config.json")
)["calibration_flags"]

# wefor_residual_groups recorded as a list; the solver wants a frozenset.
prb = dict(cf["coal_prb_sigmoid_overrides"])
if isinstance(prb.get("wefor_residual_groups"), list):
    prb["wefor_residual_groups"] = frozenset(prb["wefor_residual_groups"])

years = cf["years"]
if os.environ.get("KEEPER_YEARS"):
    years = [int(y) for y in os.environ["KEEPER_YEARS"].split(",")]

out = os.environ.get("RUN161_OUT", "161")
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
    offer_curve_deltas=cf["offer_curve_deltas"],
    ercot_rtordpa_overlay=cf["ercot_rtordpa_overlay"],  # True (G2 2023 bridge, kept)
    ercot_dam_as_overlay=False,  # SWAP OFF — replaced by the cap+ORDC-adder
    ercot_dam_as_overlay_from_year=cf["ercot_dam_as_overlay_from_year"],
    ercot_dam_as_scarcity_threshold=cf["ercot_dam_as_scarcity_threshold"],
    energy_reserve_coopt=True,
    ercot_multiproduct_as_coopt=False,  # single lumped product + published ORDC
    ercot_reserve_supply_cap=True,  # the lever: cap reserve supply at RTOLCAP
    ercot_reserve_supply_cap_from_year=2023,
    ordc_lolp_params_path=ORDC_TABLE,  # ERCOT's published NP6-576-ER LOLP curve
)
print("161 done:", run_dir)
