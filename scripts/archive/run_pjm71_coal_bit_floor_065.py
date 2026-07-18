"""Driver: PJM 71 coal-bit-floor probe — floor=0.65 (bracket bisection).

Bracket: floor=0.55 (pjm-70) has COAL_BIT +5.72/+6.73 TWh (over), floor=0.75
has COAL_BIT -8.08/-12.60 TWh (under). This bisects at 0.65 to find the sweet
spot that best splits C1-coal and C3a.

Sigmoid params: floor=0.65, ceil=1.32, gas_mid=3.40, gas_slope=2.5.
All other settings pjm-70 verbatim (reserve co-opt ON).
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import (  # noqa: E402
    _load_reference,
    report_run,
    solve_and_persist,
)
from scripts.archive.run_pjm61_consolidate import (  # noqa: E402
    PRB_OVERRIDES,
)
from scripts.archive.run_pjm69_interchange_caps import (  # noqa: E402
    OFFER_CURVE_OVERRIDES,
)

BIT_OVERRIDES = {"coal_bit_passthrough_floor": 0.65}


def main() -> int:
    out_dir = Path("results/calibration/pjm_coal_bit_floor_065")
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
        prb_overrides=PRB_OVERRIDES,
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
        note=(
            "PJM 71 coal-bit-floor 0.65 (bracket bisect): floor=0.75 overshot "
            "(COAL_BIT -8/-13 TWh under). Bisecting the 0.55-0.75 bracket at "
            "0.65 to find the floor that best splits C1-coal-volume and C3a-"
            "price. Sigmoid: floor=0.65, ceil=1.32, gas_mid=3.40, gas_slope="
            "2.5. All other settings pjm-70 verbatim (reserve co-opt ON)."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
