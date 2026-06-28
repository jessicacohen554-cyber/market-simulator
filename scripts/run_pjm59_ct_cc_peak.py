"""Driver: PJM 59 — CT dispatch fix + CC peak tranche enhancement, 2023-2025.

Builds on pjm 58 (seam-border NYISO re-anchor) with two independent fixes:

1. CT_PEAKER offer curve overhaul (Priority 1):

   pjm 58 CT_PEAKER committed/econ_low multipliers (0.878/0.879) put ~88% of
   CT capacity at below-base heat rate, making CTs inframarginal in virtually
   all hours — model dispatches CTs at 99.7-100% CF (actual ~5-10%).  Fix:
   raise committed to 1.25 and econ_low to 1.05 so CT marginal cost exceeds
   CC in most hours, restoring peaker-like dispatch.  pct_peaking raised from
   7→15% to widen the scarcity band.

   ct_intermediate_split enabled (threshold=30%): of 70 CAMPD-tracked
   CT_PEAKER plants, 62 plants (19,115 MW) have median CF >= 30% — these are
   intermediate-duty units (local reliability, ancillary services) and get a
   flatter CT_INTERMEDIATE curve.  The remaining 8 plants (3,823 MW, true
   peakers) keep the steep CT_PEAKER curve.  Source: CAMPD thermal tranche
   file (data/raw/_processed-legacy/thermal_tranches_PJM.csv).  The median CF
   is a durable, forward-reproducible duty-role signal (CLAUDE.md #12).

2. CC_REGULAR peak tranche enhancement (Priority 2):

   pjm 58 price duration curve is massively compressed: model p99 $41-63 vs
   actual $87-168; top-100-hour prices $44-68 vs target $80-150+.  The CC
   peak multiplier of 3.40 caps duct-firing/scarcity pricing; raised to 5.0.
   cc_duct_peaking_cap_pct raised from 12→18% to allow more CC capacity to
   set scarcity prices.

Both levers operate on independent capacity bands (CT dispatch level vs CC
peak pricing) — can be attributed jointly.

All other levers — NYISO border re-anchor, CC inframarginal lift, measured
hydro, coal sigmoids — are pjm 58 verbatim.
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
        "peak": 5.0,  # ↑ from 3.40: allow duct-firing/scarcity markup
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
        "committed": 1.25,  # ↑ from 0.878: part-load penalty above base HR
        "econ_low": 1.05,  # ↑ from 0.879: base dispatch above base HR
        "econ_high": 1.40,  # ↑ from 1.466: rising economic ramp
        "peak": 4.0,  # kept: scarcity band
        "econ_low_share": 0.5,
        "pct_peaking": 15.0,  # ↑ from 7.0: wider scarcity band
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
    out_dir = Path("results/calibration/pjm59_ct_cc_peak")
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
        # --- CT intermediate split (new in pjm 59) ---
        ct_intermediate_split=True,
        ct_intermediate_cf_threshold=30.0,
        # --- Offer curves ---
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 18.0,  # ↑ from 12.0
        },
        note=(
            "pjm 59 CT+CC peak: (1) CT_PEAKER offer curve overhaul — "
            "committed 0.878→1.25, econ_low 0.879→1.05 so CTs dispatch as "
            "peakers (~5-10% CF) instead of baseload (99.7%). "
            "ct_intermediate_split enabled (threshold=30%): 62 of 70 plants "
            "(19,115 MW) are intermediate-duty → flatter CT_INTERMEDIATE "
            "curve; 8 plants (3,823 MW) remain true peakers. "
            "pct_peaking 7→15%. (2) CC_REGULAR peak 3.40→5.0, "
            "cc_duct_peaking_cap_pct 12→18% for higher scarcity-hour "
            "pricing. Target: CT CF ~5-10%, top-100-hour prices $80-150+. "
            "All other levers pjm 58 verbatim."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
