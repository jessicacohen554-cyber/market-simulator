"""THROWAWAY DIAGNOSTIC (rule 15): pjm-76 recipe, 2024 only.

Single-year solve to extract per-class hourly dispatch, reliability_floor
CT_PEAKER binding hours, and the CC/CT evening merit ladder for
FINDING-pjm-burndown-2026-07.md. NOT dashboard-registered.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import _load_reference, report_run, solve_and_persist  # noqa: E402
from scripts.archive.run_pjm74_cc_ct_rebalance import (
    BIT_OVERRIDES,
    OFFER_CURVE_OVERRIDES,
)  # noqa: E402
from scripts.archive.run_pjm75_ct_drag_cc_cap import CONFIG_OVERRIDES, CT_DRAG_OVERRIDES  # noqa: E402


def main() -> int:
    out_dir = Path("results/calibration/pjm_diag_burndown_2024")
    reference = _load_reference()
    run_dir = solve_and_persist(
        [2024],
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
        note="THROWAWAY DIAG (rule 15): pjm-76 recipe 2024-only for burndown finding.",
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
