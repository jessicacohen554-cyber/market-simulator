"""Driver: PJM 86 — pjm-83 keeper recipe re-solved at HEAD (clean A/B baseline).

The pjm-83 SRMC-reground KEEPER recipe VERBATIM (``run_pjm80_srmc_reground_keeper``
``_solve`` kwargs — the same base the pjm-84/pjm-85 probes layered on), re-solved
on the CURRENT data tree. This is the flag-off side of the pjm-87 per-gen
opportunity-cost A/B, needed because the committed pjm-83 bundle predates two
data-tree moves that the treatment run will carry (the pjm-85 SUMMARY's
data-tree finding, generalized):

* the demand-profile clean-partition regeneration (the committed pjm-83 fell
  back to the corrupted legacy series: CC_CHP/ST_CHP TWh deltas are the data
  tree, not any mechanism), and
* the per-BA EIA-930 PJM demand rewire (``eia_loader._load_pjm_hourly_demand``,
  2026-07-07): the legacy series lagged the renewable/zonal-share clock by
  1-2 h, carried 23/22 zero hours in 2023/2024, and its 2024 gap interpolation
  shaved a real ~104 GW ridge to ~63 GW.

Solving the baseline on the SAME tree makes the pjm-87 A/B single-mechanism
(CLAUDE.md rule 19). Full span 2023-2025 in one bundle (rule 16), years
sequential (rule 12). Registered per rule 15 whatever the outcome.
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
    "PJM 86 pjm-83 keeper recipe VERBATIM re-solved at HEAD: the flag-off "
    "baseline of the pjm-87 per-gen opportunity-cost A/B, on the same data "
    "tree as the treatment (regenerated clean partitions + the per-BA "
    "EIA-930 PJM demand rewire: 1-2h clock lag fixed, 2023/2024 zero-hour "
    "gaps replaced with real meter data, the 2024 interpolation-shaved "
    "~104 GW ridge restored). No mechanism deltas vs pjm-83 — any move vs "
    "the committed pjm-83 bundle is the data tree."
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
    out_dir = Path("results/calibration/pjm86_pjm83_head_baseline")
    run_dir = _solve(out_dir, note=NOTE)
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
