"""Driver: PJM 57 — measured EIA-930 hydro + CC inframarginal lift, 2023-2025.

Builds on the pjm-56 CC inframarginal lift (committed 0.6624->0.75, econ_low
0.78->0.92, every other lever pjm-55 verbatim) and adds ONE structural data
correction: pin conventional hydro to the measured EIA-930 NG:WAT monthly total
(``hydro_eia930_monthly=True``).

Why hydro (pjm-56 residuals):

  pjm-56 still over-dispatched gas, worst in 2025 (gas 402.3 vs 360.7 TWh/923,
  +41.6; net export +41.6 vs +18.0). Decomposing the 2025 energy balance exposed
  a structural data gap independent of the seam: model hydro COLLAPSED to 2.29
  TWh vs a measured 15.5 (-13.2), and "other"/oil were short too. The EIA-923
  early-release vintage under-counts conventional hydro for the current year
  (2025 final annual file has not landed; 2023-24 are also ~7 TWh short), and the
  missing inflow is served by GAS — inflating the modeled gas level by ~the same
  magnitude. This is exactly the failure ``_hydro_fleet``'s ``eia930_monthly``
  docstring warns about.

  Fix: repin each hydro plant's monthly energy budget to the measured EIA-930
  hydro total (15.45/15.82/15.50 TWh for 2023/24/25), preserving per-plant
  within-month shares. Measured hydro is a reproducible physical generation input
  with a forward analogue (``forecast_budget`` normal-water-year climatology), so
  it is admissible even in backcast mode (CLAUDE.md rule #12) — a physical
  availability input, NOT an outcome pinned to the price/export residual. The
  ~+6.6/+7.0/+13.2 TWh of must-run hydro displaces marginal gas (largest in 2025,
  where the under-count and the gas miss are both largest) and shrinks the
  surplus the model was pushing onto the over-export.

CC inframarginal lift (pjm-56, retained verbatim):

    CC_REGULAR committed  0.6624 -> 0.75   (less artificial self-schedule discount)
    CC_REGULAR econ_low   0.78   -> 0.92   (low-econ band offered nearer full-load HR)
    CC_REGULAR econ_high  1.38           (unchanged from pjm-55)
    CC_REGULAR peak       3.40           (unchanged from pjm-55)

All other offer curves, coal sigmoids, and structural levers are pjm-55 verbatim.
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
    out_dir = Path("results/calibration/pjm57_hydro_measured")
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
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 12.0,
        },
        note=(
            "pjm 57 measured-hydro + CC inframarginal lift on pjm-55 keeper. "
            "hydro_eia930_monthly=True repins conventional hydro to measured "
            "EIA-930 NG:WAT (15.45/15.82/15.50 TWh) — the EIA-923 early-release "
            "under-counted hydro (model 8.9/8.9/2.3) and gas backfilled the "
            "missing ~7/7/13 TWh of inflow, inflating modeled gas (worst 2025). "
            "Retains pjm-56 CC_REGULAR committed 0.6624->0.75, econ_low 0.78->0.92 "
            "(less artificial self-schedule discount). Measured hydro is a physical "
            "input with a forward analogue (rule #12), not tuned to the residual. "
            "All coal sigmoids/structural levers pjm-55 verbatim."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
