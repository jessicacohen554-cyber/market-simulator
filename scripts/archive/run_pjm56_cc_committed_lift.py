"""Driver: PJM 56 — lift CC_REGULAR inframarginal offer, 2023-2025.

Continuation of the pjm-55 offer-curve keeper stack (every structural lever and
coal sigmoid preserved verbatim), with ONE attributable change: raise the
CC_REGULAR committed and econ_low band multipliers so PJM's inframarginal gas is
offered closer to its true marginal cost instead of a deep self-schedule
discount.

Why this lever, and why now (pjm-55 residuals):

  pjm-55 left the dominant miss as CC_REGULAR OVER-DISPATCH and the downstream
  OVER-EXPORT, worst by far in 2025 (gas model 410.2 vs 360.7 TWh actual/923,
  +49.5; net export model +46.4 vs +18.0, +28.5). 2023-24 are only mildly over
  (gas +11/+14, export +6.6/+17.3). The seam is the reference-price node
  (build_reference_price_node): PJM exports to MISO/NYISO and imports from the
  SERC south whenever its LMP clears below / above the neighbor reference. The
  over-export AND the under-import are the SAME symptom — PJM's clearing price
  sits a little too low because its inframarginal CC gas is offered too cheap
  (committed band at 0.6624 x AHR is a deep self-schedule discount). Lifting the
  committed + econ_low bands raises PJM's LMP in exactly the low-price baseload
  hours that drive the export spread, simultaneously closing the export spread
  to MISO/NYISO and opening the import spread from SERC.

  The lift acts on AHR x fuel_price, so its ABSOLUTE size scales with the gas
  price: ~$1.2-1.9/MWh in cheap-gas 2024, ~$2-3/MWh in dear-gas 2025 — i.e. the
  correction is largest exactly where the miss is largest (2025), and gentlest
  where the residual is already small (2023-24). This is the structurally
  faithful direction: a CC's committed/min-load energy carries a HIGHER
  incremental heat rate than its rated full-load HR, so offering it at 0.75 x
  AHR (vs 0.66) is less of an artificial price-taker discount, not more.

    CC_REGULAR committed  0.6624 -> 0.75   (less artificial self-schedule discount)
    CC_REGULAR econ_low   0.78   -> 0.92   (low-econ band offered nearer full-load HR)
    CC_REGULAR econ_high  1.38           (unchanged from pjm-55)
    CC_REGULAR peak       3.40           (unchanged from pjm-55)

All other offer curves, coal sigmoids, and structural levers are pjm-55 verbatim.
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

# pjm-55 recipe verbatim, with CC_REGULAR committed/econ_low lifted.
OFFER_CURVE_OVERRIDES = {
    "CC_REGULAR": {
        "committed": 0.75,  # was 0.6624 — less artificial self-schedule discount
        "econ_low": 0.92,  # was 0.78    — low-econ band offered nearer full-load HR
        "econ_high": 1.38,  # pjm-55: prices out 70-85% CF overrun
        "peak": 3.40,  # pjm-55: penalises duct burner dispatch
        "econ_low_share": 0.5,
        # pct_peaking REMOVED (pjm-55): per-plant EIA-860 duct-burner shares.
    },
    "CC_CHP": {
        "committed": 0.6624,
        "econ_low": 0.684,
        "econ_high": 0.8208,
        "peak": 1.62,
        "econ_low_share": 0.5,
        "pct_peaking": 8.0,
    },
    "CT_CHP": {
        "committed": 0.864,
        "econ_low": 0.864,
        "econ_high": 0.864,
        "peak": 1.008,
        "econ_low_share": 0.5,
    },
    "CT_PEAKER": {
        "committed": 0.8784,
        "econ_low": 0.8792,
        "econ_high": 1.4656,
        "peak": 4.0,
        "econ_low_share": 0.526,
        "pct_peaking": 7.0,
    },
    "ST_GAS": {
        "committed": 0.4752,
        "econ_low": 0.6552,
        "econ_high": 0.9,
        "peak": 3.024,
        "econ_low_share": 0.5,
        "pct_peaking": 15.0,
    },
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
    out_dir = Path("results/calibration/pjm56_cc_committed_lift")
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
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 12.0,
        },
        note=(
            "pjm 56 CC inframarginal lift on pjm-55 keeper. CC_REGULAR committed "
            "0.6624->0.75, econ_low 0.78->0.92 (less artificial self-schedule "
            "discount; offer baseload/low-econ CC nearer true full-load HR). "
            "Raises PJM LMP in low-price hours to close the over-export spread to "
            "MISO/NYISO and open the SERC import spread — the lift scales with gas "
            "price so it cools dear-gas 2025 (the worst miss) most. econ_high/peak "
            "and all coal sigmoids/structural levers pjm-55 verbatim."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
