"""Driver: PJM 81 — Phase 2 per-gen reserve co-optimization probe (G-20).

The pjm-78 SRMC-cycle baseline recipe (= the pjm-77 keeper recipe VERBATIM on
HEAD, the registered same-SHA comparator) with exactly two deltas, together
constituting docs/multi-iso/pjm-reserve-ordc.md Phase 2:

* ``pjm_reserve_supply_cap`` -> ``pjm_reserve_pergen``: the zone-aggregate
  deliverable cap (which cleared $0 every hour, pjm-62) is replaced by the
  per-pool reserve columns — (zone, fuel-class) R columns with joint
  P + R <= cap per pool-hour and hourly availability-scaled ramp bounds, the
  memory tier the miso-39 keeper proved (the plant-in-MAD tier OOM'd in P1,
  2026-07-02 memtest). Reserve competes with energy at the marginal pool and
  the two nested measured Manual-11 balance families (RTO + MAD) price on
  the published two-step ORDC ($850/$300/+190 MW) — no fitted breakpoints.
* ``measured_ramp_capability``: FleetArrays.ramp10's class fractions
  reconciled against the measured ramp-capability datatype (EIA-860 "10M"
  fast-start floor + CAMPD CEMS hourly-envelope ceiling, pooled 2023-2025) —
  rule 14 measured-over-estimate for the deliverability bound.

The ct_netload_drag stays ON, unchanged: this is the single-mechanism-change
arm vs pjm-78; the drag's rule-19 replacement-by-co-opt endgame (C8 memo §6
item 5) is adjudicated only after this mechanism is validated, and is the
owner's call. Registered per rule 15; full span 2023-2025 per rule 16.

Memory: run with MALLOC_ARENA_MAX=1 MARKET_SIM_HIGHS_THREADS=1 and a 10 GB
swapfile (the pjm-78/79 convention on the 15 GB box). Pre-flight on the real
2024 fleet: 39 R columns, 341,640 joint rows (~6.6x fewer than the OOM'd
plant-tier build).
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
from scripts.run_pjm74_cc_ct_rebalance import (  # noqa: E402
    BIT_OVERRIDES,
    OFFER_CURVE_OVERRIDES,
)
from scripts.run_pjm75_ct_drag_cc_cap import (  # noqa: E402
    CONFIG_OVERRIDES,
    CT_DRAG_OVERRIDES,
)


def main() -> int:
    out_dir = Path("results/calibration/pjm81_coopt_pergen")
    reference = _load_reference()
    run_dir = solve_and_persist(
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
        pjm_reserve_pergen=True,
        measured_ramp_capability=True,
        ct_netload_drag=True,
        ct_drag_overrides=CT_DRAG_OVERRIDES,
        note=(
            "PJM 81 Phase-2 per-gen reserve co-opt probe (G-20): pjm-78 "
            "baseline recipe + pjm_reserve_pergen ((zone, fuel-class) pooled "
            "R columns, hourly availability-scaled ramp caps, nested RTO+MAD "
            "measured families on the published two-step ORDC — replaces the "
            "$0-inert zone-aggregate supply cap) + measured_ramp_capability "
            "(EIA-860 fast-start + CAMPD CEMS envelope reconciliation of "
            "ramp10). Drag unchanged; single-mechanism A/B vs pjm-78."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
