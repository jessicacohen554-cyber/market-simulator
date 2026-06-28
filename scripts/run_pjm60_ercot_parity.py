"""Driver: PJM 60 — ERCOT-parity mechanisms for price decompression, 2023-2025.

Builds on pjm 59 (CT dispatch fix + CC peak tranche) by porting calibrated
mechanisms from the ERCOT run-157 keeper that directly address PJM's price
duration curve compression.  pjm 59 fixed CT dispatch (median CF 99.7%→2.7%)
but average prices dipped slightly and the duration curve remains compressed:
model p99 $42-65 vs actual $87-168.

Audit of ERCOT 157 vs PJM 59 identified six gaps, all ported here:

1. CT_PEAKER peak 4.0 → 10.0 (ERCOT uses 13.15).  The scarcity band must
   push prices to $200-500+ in the tightest hours.  With base HR ~10 and
   gas ~$4, peak=10 gives max CT offer ~$400/MWh.  This is the primary
   lever for the top-decile price gap.

2. offer_curve_smoothing_mid = 0.35 (ERCOT uses 0.35; PJM had None/linear).
   Shifts the econ ramp shape so 35% of the lo→hi rise is reached at the
   capacity midpoint — makes the bottom cheap and the top steep (convex).
   Accelerates marginal cost as dispatch tightens.

3. cc_duct_peaking = True (ERCOT uses per-plant EIA-860 duct-burner flags).
   Non-duct CC plants get 0% peaking band instead of the uniform 18% cap.
   Only plants with actual duct burners set scarcity prices — removes
   phantom peak capacity from non-duct CCs.  cc_duct_peaking_cap_pct kept
   at 18% as a physical ceiling on duct-fired plants.

4. battery_dispatch_adder = $10/MWh (ERCOT uses $10).  Reflects cycling
   degradation cost.  Prevents batteries from over-arbitraging and
   compressing the price duration curve.

5. storage_daily_cycling = True (ERCOT uses True).  Constrains storage to
   daily cycling pattern, preventing unrealistic multi-day smoothing.

6. chp_steam_following = True (ERCOT uses True).  Forces CHP plants to
   maintain minimum grid injection (removes behind-the-meter self-supply
   assumption that lets CHPs avoid dispatch).

All other levers — CT dispatch fix (committed=1.25, econ_low=1.05),
ct_intermediate_split (threshold=30%), NYISO border re-anchor, CC
inframarginal lift, measured hydro, coal sigmoids — are pjm 59 verbatim.
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

OFFER_CURVE_OVERRIDES = {
    # --- CC ---
    "CC_REGULAR": {
        "committed": 0.75,
        "econ_low": 0.92,
        "econ_high": 1.38,
        "peak": 5.0,
        "econ_low_share": 0.5,
    },
    "CC_CHP": {
        "committed": 0.6624,
        "econ_low": 0.684,
        "econ_high": 0.8208,
        "peak": 1.62,
        "econ_low_share": 0.5,
        "pct_peaking": 8.0,
    },
    # --- CT ---
    "CT_CHP": {
        "committed": 0.864,
        "econ_low": 0.864,
        "econ_high": 0.864,
        "peak": 1.008,
        "econ_low_share": 0.5,
    },
    "CT_PEAKER": {
        "committed": 1.25,
        "econ_low": 1.05,
        "econ_high": 1.40,
        "peak": 10.0,  # ↑ from 4.0: ERCOT uses 13.15 — scarcity pricing
        "econ_low_share": 0.5,
        "pct_peaking": 15.0,
    },
    "CT_INTERMEDIATE": {
        "committed": 1.05,
        "econ_low": 0.97,
        "econ_high": 1.15,
        "peak": 2.0,
        "econ_low_share": 0.5,
        "pct_peaking": 10.0,
    },
    # --- Gas steam ---
    "ST_GAS": {
        "committed": 0.4752,
        "econ_low": 0.6552,
        "econ_high": 0.9,
        "peak": 3.024,
        "econ_low_share": 0.5,
        "pct_peaking": 15.0,
    },
    # --- Coal (unchanged from pjm 58) ---
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

PRB_OVERRIDES = {
    "wefor_residual": 0.015,
    "coal_sub_passthrough_sigmoid": True,
    "coal_sub_passthrough_floor": 1.10,
}

BIT_OVERRIDES = {"coal_bit_passthrough_floor": 0.55}


def main() -> int:
    out_dir = Path("results/calibration/pjm60_ercot_parity")
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
        # --- CT intermediate split (from pjm 59) ---
        ct_intermediate_split=True,
        ct_intermediate_cf_threshold=30.0,
        # --- Storage (new from ERCOT 157) ---
        storage_daily_cycling=True,
        battery_dispatch_adder=10.0,
        # --- Offer curves ---
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 18.0,
            "cc_duct_peaking": True,  # per-plant EIA-860 duct-burner flags
            "offer_curve_smoothing_mid": 0.35,  # convex ramp shape
            "chp_steam_following": True,  # CHP grid injection floor
        },
        note=(
            "pjm 60 ERCOT-parity: port 6 calibrated mechanisms from ERCOT "
            "run-157 keeper to fix price duration curve compression. "
            "(1) CT peak 4.0→10.0 (ERCOT 13.15) for scarcity pricing. "
            "(2) offer_curve_smoothing_mid=0.35 (convex ramp). "
            "(3) cc_duct_peaking=True (per-plant EIA-860 duct-burner flags). "
            "(4) battery_dispatch_adder=$10 (cycling degradation). "
            "(5) storage_daily_cycling=True. "
            "(6) chp_steam_following=True (CHP grid injection floor). "
            "All other levers pjm 59 verbatim."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
