"""Driver: PJM 76 — Chesterfield outage fix (keeper candidate).

The pjm-75 recipe verbatim, re-run on the regenerated
``campd-unit-outages-PJM.csv`` (commit d815a3c, merged via PR #1257): the
``derive_campd_unit_outages.py`` resolver crashed on ``--iso PJM`` (KeyError
``unitType`` — the column was pruned from the parquet loader), so the committed
artifact was never regenerated after the per-unit group routing was added. The
Chesterfield plant 3797's retiring coal units 5/6 now carry COAL outage
windows (skipped by the gas-fleet overlay) instead of blocking the surviving
386 MW gas-CC — the ~2.35 TWh chunk of the pjm-75 2023 CC under-run. 118 rows
removed / 284 added (also corrects Brunner Island, Chalk Point, Gilbert,
Linden, Doswell).

This is a structural improvement (CLAUDE.md #1/#11): the outage resolver now
correctly distinguishes coal-retirement windows from gas-fleet unavailability
at dual-unit plants. No fitted parameters changed.

The per-gen reserve co-opt (``pjm_reserve_pergen``) is NOT included — it
passed the 2024 single-year memtest (peak ~15.14 GB, LEAN=1) but 2025 (the
tightest year, zone-aggregate ~14.5 GB) cannot fit on the 15 GB box. The
merged per-gen code (PR #1251) stays gated ``default off``; Phase 2 requires
a larger box. See ``docs/multi-iso/pjm-reserve-ordc.md`` Phase 2 re-gate.

Everything else pjm-75 verbatim: CT net-load deployment drag, CC
demonstrated-peak cap, M15 offer moves, coal_bit floor 0.65, reserve co-opt
ON (zone-aggregate), historic outages, zonal gas basis, congestion, priced
interchange, seam caps, hydro/BTM backfill 2024, commitment=False.
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
    out_dir = Path("results/calibration/pjm76_outage_fix")
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
            "PJM 76 Chesterfield outage fix: pjm-75 recipe verbatim on "
            "regenerated campd-unit-outages-PJM.csv (d815a3c). Chesterfield "
            "3797 coal units 5/6 now carry COAL outage windows (skipped by "
            "gas overlay) instead of blocking the 386 MW surviving gas-CC. "
            "Corrects ~2.35 TWh of the pjm-75 2023 CC under-run. Also fixes "
            "Brunner Island, Chalk Point, Gilbert, Linden, Doswell outage "
            "routing. Per-gen reserve co-opt NOT included (memory-infeasible "
            "on 15 GB box; see pjm-reserve-ordc.md). All else pjm-75 "
            "verbatim (CT drag, CC cap, M15 offers, coal_bit 0.65, "
            "zone-agg reserve co-opt, commitment=False)."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
