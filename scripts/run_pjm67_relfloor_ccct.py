"""Driver: PJM 67 — reliability floor + CC/CT offer-curve calibration.

Merges the two open calibration threads:

1. **Reliability floor** (pjm-65): per-(zone, class) temperature-gated
   minimum-generation floors from reliability_floor_coeffs_PJM.csv, applied
   by the generic registry engine (transmission.inject_reliability_floor).
   Structural market-design feature (capacity commitments / must-offer
   obligations force units online during temperature events), not an
   actuals pin — forward-derivable from weather forecasts (CLAUDE.md #11).

2. **CC/CT offer-curve rebalance** (pjm-66 + further tuning):

   CC_REGULAR:
     committed 0.87 → 0.95 — pjm-66 0.87 fixed the 2023 overrun but
     left 2024 at +28 TWh. 2024 gas is $2.19 vs $2.54 (2023), dropping
     the committed floor's absolute $/MWh below PJM overnight LMP.
     0.95 is closer to the Manual 15 SRMC floor (ERCOT keeper 0.998)
     and lifts the floor by ~$1.5/MWh in the cheap-gas year.
     econ_low_share 0.50 → 0.55 — pushes more CC capacity into the
     steeper econ ramp, reducing flat committed-band dispatch.

   CT_PEAKER (8 true peakers, CAMPD median CF < 30%):
     committed 1.25 → 1.10 — 1.25 priced all peaker energy at 1.25×HR
     ×fuel ($34/MWh at $2.19), above most PJM hours and too high for
     even true peaker starts. 1.10 preserves the startup hurdle without
     eliminating all dispatch. pct_peaking 15 → 20 for wider scarcity band.

   CT_INTERMEDIATE (62 intermediate CTs, median CF ≥ 30%):
     committed 1.05 → 0.90 — these units run 30-90% CF in reality; the
     1.05 committed multiplied by CT heat rates (~10 MMBtu/MWh) put their
     floor at $23/MWh, above the CC econ_low range. 0.90 lets them
     dispatch as intermediate units that actually run. econ_low 0.97→0.92,
     econ_high 1.15→1.08, pct_peaking 10→5 (intermediate, not peaker duty).

All coal sigmoids, hydro, congestion, seam-border levers from pjm-58
keeper verbatim.
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
from scripts.run_pjm61_consolidate import (  # noqa: E402
    BIT_OVERRIDES,
    PRB_OVERRIDES,
)

OFFER_CURVE_OVERRIDES = {
    # --- CC_REGULAR: raise committed toward Manual 15 SRMC floor ---
    "CC_REGULAR": {
        "committed": 0.95,  # 0.87 → 0.95: fix 2024 cheap-gas overrun
        "econ_low": 0.92,  # unchanged from pjm-58/66
        "econ_high": 1.50,  # pjm-66: steepen upper ramp (miss #2)
        "peak": 5.0,  # pjm-61: duct-firing scarcity markup
        "econ_low_share": 0.55,  # 0.50 → 0.55: push more into steeper ramp
    },
    "CC_CHP": {
        "committed": 0.6624,
        "econ_low": 0.684,
        "econ_high": 0.8208,
        "peak": 1.62,
        "econ_low_share": 0.5,
        "pct_peaking": 8.0,
    },
    # --- CT_PEAKER: true peakers only (8 plants with CF < 30%) ---
    "CT_CHP": {
        "committed": 0.864,
        "econ_low": 0.864,
        "econ_high": 0.864,
        "peak": 1.008,
        "econ_low_share": 0.5,
    },
    "CT_PEAKER": {
        "committed": 1.10,  # 1.25 → 1.10: startup hurdle without pricing out
        "econ_low": 1.05,  # unchanged from pjm-66
        "econ_high": 1.40,  # pjm-61: economic ramp
        "peak": 4.0,  # pjm-58 keeper ceiling
        "econ_low_share": 0.5,
        "pct_peaking": 20.0,  # 15 → 20: wider scarcity band for true peakers
    },
    # --- CT_INTERMEDIATE: 62 intermediate-duty CTs (median CF ≥ 30%) ---
    "CT_INTERMEDIATE": {
        "committed": 0.90,  # 1.05 → 0.90: intermediate units that run 30-90% CF
        "econ_low": 0.92,  # 0.97 → 0.92: compete with CC econ range
        "econ_high": 1.08,  # 1.15 → 1.08: tighter ramp
        "peak": 2.0,  # pjm-66: modest scarcity
        "econ_low_share": 0.5,
        "pct_peaking": 5.0,  # 10 → 5: intermediate, not peaker duty
    },
    # --- Gas steam (pjm-58 verbatim) ---
    "ST_GAS": {
        "committed": 0.4752,
        "econ_low": 0.6552,
        "econ_high": 0.9,
        "peak": 3.024,
        "econ_low_share": 0.5,
        "pct_peaking": 15.0,
    },
    # --- Coal (pjm-58 verbatim) ---
    "COAL_LIGNITE": {
        "committed": 0.684,
        "econ_low": 0.8208,
        "econ_high": 0.828,
        "peak": 1.116,
        "econ_low_share": 0.556,
    },
    "COAL_PRB": {
        "committed": 0.684,
        "econ_low": 0.5544,
        "econ_high": 0.80,
        "peak": 1.0656,
        "econ_low_share": 0.556,
    },
    "COAL_BIT": {
        "committed": 0.548,
        "econ_low": 0.6556,
        "econ_high": 1.2664,
        "peak": 1.044,
        "econ_low_share": 0.55,
    },
    "COAL_WC": {
        "committed": 0.512,
        "econ_low": 0.548,
        "econ_high": 0.6344,
        "peak": 0.764,
        "econ_low_share": 0.55,
    },
    "COAL": {
        "committed": 0.648,
        "econ_low": 0.684,
        "econ_high": 0.792,
        "peak": 1.044,
        "econ_low_share": 0.55,
    },
}


def main() -> int:
    out_dir = Path("results/calibration/pjm67_relfloor_ccct")
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
        reliability_floor=True,
        ct_intermediate_split=True,
        ct_intermediate_cf_threshold=30.0,
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 18.0,
            "offer_curve_smoothing_mid": 0.35,
        },
        note=(
            "pjm 67 reliability-floor + CC/CT calibration: merges pjm-65 "
            "(reliability_floor=True, per-(zone,class) temp-gated floors) "
            "with CC/CT offer-curve rebalance. CC_REGULAR committed "
            "0.87→0.95 (Manual 15 SRMC, fix 2024 cheap-gas overrun), "
            "econ_low_share 0.50→0.55. CT split: 8 true peakers "
            "(committed 1.10, pct_peaking 20) + 62 intermediate CTs "
            "(committed 0.90, econ_low 0.92, pct_peaking 5) via "
            "ct_intermediate_split threshold=30%. CC econ_high 1.50, "
            "peak 5.0, cc_duct_peaking_cap_pct 18%, smoothing_mid 0.35. "
            "All coal/hydro/congestion/seam-border levers pjm-58 verbatim."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
