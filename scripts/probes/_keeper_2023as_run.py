"""Re-solve the run134 keeper recipe from its saved run_config.json.

Reconstructs the ERCOT keeper (run134 = ``ercot_dam_storageas_ccsteam_regen``)
by reading that bundle's ``run_config.json`` ``calibration_flags`` and calling
:func:`run_calibration_full.solve_and_persist` with the same kwargs — so the
*only* input that differs is whatever this campaign changed (the measured 2023
AS series now on disk, and the ``--from-year`` scope below). This avoids
hand-rebuilding the ~30-flag CLI and guarantees 2024/2025 parity with run134
(their AS files are unchanged), isolating the measured-2023 effect.

Usage:
    python scripts/probes/_keeper_2023as_run.py <out_subdir> [storage_as_from_year]

    out_subdir            results/calibration/<out_subdir>
    storage_as_from_year  --ercot-storage-as-reserve-from-year (default 2025,
                          the run134 scope; pass 2023 for the Step-2b probe).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from run_calibration_full import (  # noqa: E402
    _load_reference,
    report_run,
    solve_and_persist,
)

RUN134 = REPO / "results" / "calibration" / "ercot_dam_storageas_ccsteam_regen"


def main(argv: list[str]) -> int:
    out_subdir = argv[0]
    from_year = int(argv[1]) if len(argv) > 1 else 2025
    load_from_year = int(argv[2]) if len(argv) > 2 else 2023
    # Optional argv[3]: JSON of {group: {band: delta}} that OVERWRITES entries in
    # run134's offer_curve_deltas (e.g. '{"ST_GAS": {"committed": 0.0}}' to undo
    # the over-cooled ST_GAS committed offer that over-commits gas steam, run141).
    delta_override = json.loads(argv[3]) if len(argv) > 3 else {}
    # Optional argv[4]: enable the measured ECRS reserve requirement (the
    # demand-side fix for the bimodal monthly shape / 2023-H2 + 2024 mid-range
    # under-price). Off by default = the run143 keeper.
    ercot_ecrs = len(argv) > 4 and argv[4].lower() in ("1", "true", "ecrs", "on")
    cfg = json.loads((RUN134 / "run_config.json").read_text())["calibration_flags"]
    # Optional env overrides for cheap single-lever probes (don't disturb argv):
    #   KEEPER_YEARS="2024"   -> solve only those years
    #   KEEPER_COMMIT=1       -> enable the P2 unit-commitment screen (the keeper
    #                            is dispatch-only; this tests commitment price
    #                            formation for the loose-month under-price).
    years = cfg["years"]
    if os.environ.get("KEEPER_YEARS"):
        years = [int(y) for y in os.environ["KEEPER_YEARS"].split(",")]
    commitment = cfg["commitment"]
    if os.environ.get("KEEPER_COMMIT"):
        commitment = os.environ["KEEPER_COMMIT"].lower() in ("1", "true", "on")
    #   KEEPER_PERSIST_P2=1 -> persist each year's P1 state to <bundle>/p2_state/
    #                          so the P2 commitment screen can be run (and
    #                          re-tuned) modularly later via
    #                          run_calibration_full.py --run-p2 <bundle>, with no
    #                          P0/P1 re-solve. Off by default (the keeper is
    #                          dispatch-only and does not need it).
    persist_p2_state = os.environ.get("KEEPER_PERSIST_P2", "").lower() in (
        "1",
        "true",
        "on",
    )
    #   KEEPER_ORDC_TABLE=<csv> -> use ERCOT's published NP6-576-ER LOLP table in
    #                             the co-opt ORDC curve (grounds mu/sigma; the
    #                             keeper uses the neutral mu=0 fallback).
    ordc_lolp_params_path = os.environ.get("KEEPER_ORDC_TABLE") or None
    #   KEEPER_RTORDPA=1     -> add the measured, regime-gated RTORDPA
    #                          (reliability-deployment price adder) to the model
    #                          system price as a post-solve, additive overlay
    #                          (Track 2: the grounded 2023 market-design adder;
    #                          near-inert in 2024/25). Read per-year from
    #                          data/raw/ercot/ercot_<year>_ordc_reserves_hourly
    #                          .parquet — backcast-able, never a 2023 hard-code.
    ercot_rtordpa_overlay = os.environ.get("KEEPER_RTORDPA", "").lower() in (
        "1",
        "true",
        "on",
    )
    #   KEEPER_STGAS_DRAG=1 -> enable the net-load-indexed ST_GAS reliability-
    #                          drag min-gen floor (the endogenous, weather-driven
    #                          replacement for the seasonal gas_st_summer_mustrun;
    #                          see fleet.apply_gas_st_netload_drag_floor). Optional
    #                          KEEPER_STGAS_DRAG_PARAMS='{"gas_st_drag_slope_per_gw":
    #                          ..., "gas_st_drag_intercept": ..., "gas_st_drag_cap":
    #                          ...}' overrides the CAMPD-fitted curve coefficients.
    gas_st_netload_drag = os.environ.get("KEEPER_STGAS_DRAG", "").lower() in (
        "1",
        "true",
        "on",
    )
    gas_st_drag_overrides = (
        json.loads(os.environ["KEEPER_STGAS_DRAG_PARAMS"])
        if os.environ.get("KEEPER_STGAS_DRAG_PARAMS")
        else None
    )
    #   KEEPER_BATTERY_ADDER=<float> -> override the grid-battery throughput
    #   /cycling adder ($/MWh discharged, ScenarioConfig.battery_dispatch_adder).
    #   The keeper uses 10.0; set 0 to restore arbitrage peak-shaving (the run154
    #   LMP-shape probe: batteries shaved the Aug evening net-load ramp in 2024).
    battery_dispatch_adder = (
        float(os.environ["KEEPER_BATTERY_ADDER"])
        if os.environ.get("KEEPER_BATTERY_ADDER")
        else 10.0
    )
    sm = dict(cfg.get("coal_prb_sigmoid_overrides", {}))
    #   KEEPER_PRB_PARAMS='{"coal_prb_passthrough_floor": 0.78, ...}' -> overlay
    #   the coal PRB passthrough-sigmoid ScenarioConfig params (floor/ceil/gas_mid
    #   /gas_slope for the baseload prb + prb_follower tiers, lignite, etc.) onto
    #   the keeper's coal_prb_sigmoid_overrides. Used to tighten the PRB sigmoid so
    #   out-of-merit PRB baseload backs down at the right price and frees energy
    #   back to the gas family (see docs/binning-methodology.md, the coal over-run
    #   fix). Each key must be a valid ScenarioConfig field (rides prb_overrides ->
    #   config.with_overrides in run_calibration).
    if os.environ.get("KEEPER_PRB_PARAMS"):
        sm.update(json.loads(os.environ["KEEPER_PRB_PARAMS"]))
    deltas = cfg.get("offer_curve_deltas") or {}
    for grp, bands in delta_override.items():
        deltas.setdefault(grp, {}).update(bands)

    run_dir = REPO / "results" / "calibration" / out_subdir
    reference = _load_reference()
    run_dir = solve_and_persist(
        years,
        cfg["iso"],
        cfg["hours"],
        reference,
        commitment=commitment,
        screen_coal=cfg["commitment_screen_coal"],
        run_dir=run_dir,
        persist_p2_state=persist_p2_state,
        coal_lignite_mustrun=cfg.get("coal_lignite_mustrun"),
        coal_prb_mustrun=cfg.get("coal_prb_mustrun"),
        coal_prb_passthrough=cfg["coal_prb_passthrough"],
        outage_source=cfg["outage_source"],
        coal_prb_passthrough_sigmoid=cfg["coal_prb_passthrough_sigmoid"],
        coal_mustrun_per_plant=cfg["coal_mustrun_per_plant"],
        ct_mustrun_per_plant=cfg["ct_mustrun_per_plant"],
        ct_mustrun_floor_frac=cfg["ct_mustrun_floor_frac"],
        coal_drop_pof=cfg["coal_drop_pof"],
        coal_prb_passthrough_tiered=cfg["coal_prb_passthrough_tiered"],
        prb_overrides=sm,
        coal_bit_sigmoid=cfg["coal_bit_passthrough_sigmoid"],
        bit_overrides=cfg.get("coal_bit_sigmoid_overrides") or None,
        storage_daily_cycling=True,
        battery_dispatch_adder=battery_dispatch_adder,
        as_reserve_withholding=False,
        energy_reserve_coopt=True,
        ercot_load_resource_reserve=True,
        ercot_load_resource_reserve_from_year=load_from_year,
        ercot_storage_as_reserve=True,
        ercot_storage_as_reserve_from_year=from_year,
        ercot_ecrs_requirement=ercot_ecrs,
        ercot_ecrs_requirement_from_year=2023,
        ercot_rtordpa_overlay=ercot_rtordpa_overlay,
        gas_st_netload_drag=gas_st_netload_drag,
        gas_st_drag_overrides=gas_st_drag_overrides,
        ordc_lolp_params_path=ordc_lolp_params_path,
        as_reserve_formula=False,
        storage_as_commitment=True,
        gas_offer_curve=False,
        gas_monthly_actuals=False,
        offer_curve_overrides=cfg.get("offer_curve_overrides"),
        offer_curve_deltas=deltas,
        curve_smoothing={
            "offer_curve_smoothing_n": None,
            "offer_curve_smoothing_exp": None,
            "offer_curve_smoothing_mid": 0.35,
        },
        cc_derate_from_top=False,
        priced_interchange=False,
        btm_backfill_year=cfg.get("btm_backfill_year"),
        note=f"run134 recipe re-solved with measured 2023 AS; "
        f"load-RRS-from-year={load_from_year}; storage-AS-from-year={from_year}; "
        f"ecrs-requirement={ercot_ecrs}; battery-adder={battery_dispatch_adder}",
    )
    report_run(run_dir)
    print(f"\nBundle: {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
