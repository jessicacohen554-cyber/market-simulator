"""MEMORY PROBE: PJM per-gen reserve co-opt, single year 2024 — RSS gate.

The pjm-76 pre-flight required by docs/multi-iso/pjm-reserve-ordc.md Phase 2
and CLAUDE.md #45: the zone-aggregate co-opt peaked ~13.9 GB (2024) / ~14.5 GB
(2025) on the 15 GB calibration box, and the per-gen build adds ~2,600 R
columns + joint P+R rows per hour — UNTESTED at PJM plant-level scale. Before
any 3-year run, solve ONE year (2024) with ``pjm_reserve_pergen=True`` under
``/usr/bin/time -v`` and read the peak RSS.

Recipe: run_pjm75_ct_drag_cc_cap verbatim (imported) + ``pjm_reserve_pergen``.
``pjm_reserve_supply_cap`` stays True as in the keeper recipe — the per-gen
branch in reserve_config._pjm_design supersedes it (the design never computes
the aggregate cap when pergen is on), matching how the pjm-76 driver will run.

Throwaway diagnostic (never registered on the dashboard):
    /usr/bin/time -v python scripts/probes/_pjm76_pergen_memtest.py \
        > /tmp/.../memtest.log 2>&1
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import (  # noqa: E402
    _load_reference,
    solve_and_persist,
)
from scripts.archive.run_pjm74_cc_ct_rebalance import (  # noqa: E402
    BIT_OVERRIDES,
    OFFER_CURVE_OVERRIDES,
)
from scripts.archive.run_pjm75_ct_drag_cc_cap import (  # noqa: E402
    CONFIG_OVERRIDES,
    CT_DRAG_OVERRIDES,
)


def main() -> int:
    out_dir = Path("results/calibration/_pjm76_pergen_memtest")
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
        pjm_reserve_pergen=True,
        ct_netload_drag=True,
        ct_drag_overrides=CT_DRAG_OVERRIDES,
        note=(
            "THROWAWAY memory probe: pjm-75 recipe + pjm_reserve_pergen, "
            "2024 only. Never register."
        ),
    )
    print(f"MEMTEST DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
