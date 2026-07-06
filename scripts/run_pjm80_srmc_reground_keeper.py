"""Driver: PJM 80 — G-21 SRMC re-grounding, promoted keeper candidate (L-13).

The pjm-79 re-grounding recipe VERBATIM (``run_pjm79_srmc_reground.OFFER_CURVE_
OVERRIDES`` — ST_GAS committed/econ_low/econ_high 0.4752/0.6552/0.90 -> 1.00 and
CT_INTERMEDIATE committed/econ_low 0.9/0.92 -> 1.00), re-solved on HEAD so the
bundle retains its dispatch parquet and is scored under the current rubric
(rubric v2.1: D-2 peaker budget 0.15, owner amendment 2026-07-06). pjm-79 was a
probe scored under the superseded 0.10 peaker gate with its dispatch since
gitignored; this is the promotion-grade re-solve.

The two changes L-13 carries into the keeper vs the pjm-77 parent:

* **G-21 offer re-grounding** (step 2): the two sub-SRMC residual artifacts
  (ST_GAS 0.48x, CT_INTERMEDIATE 0.9x) move to the Manual-15 composite-cost
  floor (1.0x). Correct offer physics (rule 1: a sub-SRMC offer is not real);
  a non-CHP gas steamer's part-load IHR exceeds its full-load AHR, so no tranche
  may clear below 1.0x. C1/C2 (sub-SRMC artifacts) clear.
* **CT_CHP reliability-floor scrub** (step 1): the EMAAC CT_CHP tmax limb is
  disabled in ``reliability_floor_coeffs_PJM.csv`` (all-24h binding, 70.8%
  off-window in every pjm-77 year; the driver evidence says the class's hot-day
  lift is an all-hours steam-host intensification owned by ``chp_steam`` — rule
  19, one mechanism per phenomenon). Baked into this solve's dispatch, so
  ``reliability_floor x CT_CHP`` no longer appears in D-4.

The CT net-load drag (``ct_netload_drag``, window [15,22)) is UNCHANGED: the
L-13 overnight-reliability evidence check (``diag_pjm_ct_overnight_evidence.py``)
confirmed the window is correct (overnight CF a flat ~2%, net-load-insensitive;
the extreme-net-load overnight uptick is 3-5x weaker than the ramp relationship
and belongs to per-gen reserve/ORDC, G-20 Phase 2 — NOT a widened floor).

Registered per rule 15; full span 2023-2025 per rule 16; ablation twin per rule
25 (``run_pjm80_ablation_twin.py``).
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import (  # noqa: E402
    _load_reference,
    report_run,
    solve_and_persist,
)
from scripts.run_pjm74_cc_ct_rebalance import BIT_OVERRIDES  # noqa: E402
from scripts.run_pjm75_ct_drag_cc_cap import (  # noqa: E402
    CONFIG_OVERRIDES,
    CT_DRAG_OVERRIDES,
)
from scripts.run_pjm79_srmc_reground import OFFER_CURVE_OVERRIDES  # noqa: E402

NOTE = (
    "PJM 80 G-21 SRMC re-grounding keeper candidate (L-13): pjm-79 recipe "
    "re-solved on HEAD for promotion-grade scoring (rubric v2.1, D-2 peaker "
    "budget 0.15). ST_GAS committed/econ_low/econ_high 0.4752/0.6552/0.90 -> "
    "1.00 and CT_INTERMEDIATE committed/econ_low 0.9/0.92 -> 1.00 (Manual-15 "
    "floor, rule 1 correct offer physics). CT_CHP EMAAC reliability limb "
    "scrubbed (step 1; owned by chp_steam, rule 19). CT net-load drag window "
    "[15,22) unchanged (overnight-reliability evidence confirms it correct). "
    "Grounded moves (rule 13/14): the ST_GAS de-flood under-runs merit order "
    "and the freed energy goes to CC_REGULAR not CT_PEAKER — the residual CT "
    "under-dispatch is reserve/ORDC deployment owned by G-20 Phase 2, not the "
    "offer axis."
)


def _solve(out_dir: Path, **extra):
    reference = _load_reference()
    return solve_and_persist(
        [2023, 2024, 2025],
        "PJM",
        8760,
        reference,
        commitment=False,
        screen_coal=True,
        run_dir=out_dir,
        outage_source="historic",
        coal_prb_passthrough=1.0,
        coal_prb_passthrough_sigmoid=True,
        coal_mustrun_per_plant=True,
        retiree_cems_cap=True,
        coal_drop_pof=True,
        coal_prb_passthrough_tiered=True,
        prb_overrides=CONFIG_OVERRIDES,
        coal_bit_sigmoid=True,
        bit_overrides=BIT_OVERRIDES,
        coal_mustrun_online_pmin=True,
        coal_sync_srmc_tranche=True,
        gas_monthly_actuals=True,
        pjm_zonal_gas_basis=True,
        pjm_congestion=True,
        reference_price_interface=True,
        priced_interchange=True,
        cc_derate_from_top=True,
        hydro_eia930_monthly=True,
        hydro_backfill_year=2024,
        btm_backfill_year=2024,
        reliability_floor=True,
        ct_intermediate_split=True,
        ct_intermediate_cf_threshold=30.0,
        pjm_seam_flow_limit=True,
        pjm_seam_export_limit=True,
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 18.0,
            "offer_curve_smoothing_mid": 0.35,
        },
        energy_reserve_coopt=True,
        pjm_reserve_supply_cap=True,
        ct_netload_drag=True,
        ct_drag_overrides=CT_DRAG_OVERRIDES,
        **extra,
    )


def main() -> int:
    out_dir = Path("results/calibration/pjm80_srmc_reground_keeper")
    run_dir = _solve(out_dir, note=NOTE)
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
