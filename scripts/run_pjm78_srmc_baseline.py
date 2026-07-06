"""Driver: PJM 78 — same-SHA baseline for the G-21 SRMC re-grounding cycle.

The pjm-77 keeper recipe VERBATIM, re-solved on current HEAD so the G-21
re-grounding A/B (pjm-79) has an unconfounded same-code comparator (the G-10
lesson: never score a mechanism change against a bundle solved on older code).
The only code/data delta vs the committed pjm-77 bundle is the 2026-07-06
EMAAC CT_CHP tmax reliability-limb scrub (burndown §6 option b, driver-refuted
window — see `docs/FINDING-pjm-burndown-2026-07.md` addendum), whose committed
D-2 attribution was ~0.005-0.0095 TWh/yr, so dispatch is expected ~identical
to pjm-77 outside that phantom.

Registered per rule 15 (every completed solve, keeper or probe, goes on the
dashboard). Full span 2023-2025 per rule 16.
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
    out_dir = Path("results/calibration/pjm78_srmc_baseline")
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
        pjm_reserve_supply_cap=True,
        ct_netload_drag=True,
        ct_drag_overrides=CT_DRAG_OVERRIDES,
        note=(
            "PJM 78 SRMC-cycle baseline: pjm-77 keeper recipe VERBATIM on "
            "current HEAD (carries the 2026-07-06 EMAAC CT_CHP tmax limb "
            "scrub, burndown §6 option b). Same-SHA comparator for the G-21 "
            "sub-SRMC re-grounding A/B (pjm-79); no offer band changed vs "
            "pjm-77."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
