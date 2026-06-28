"""Driver: PJM 63 — offer-curve reshape (CC_REGULAR top up, CT_PEAKER down).

Pivot from the reserve co-opt track (pjm 62 proved zone-aggregate scoping clears
$0; per-gen + commitment is the only reserve lever, deferred). This run instead
attacks the price-duration-curve compression directly through the **energy offer
curves** — the CLAUDE.md #1 second step (offer-curve tuning, after structure),
not a residual-fitted adder: the multipliers reshape the merit order's marginal
cost, a physical heat-rate/markup statement, and respond to changed conditions in
a forecast.

Baseline = pjm 61 consolidate config VERBATIM (energy-only, no co-opt). The one
lever changed is ``offer_curve_overrides``:

* **CC_REGULAR — steeper top + wider scarcity tranche.** ``econ_high`` 1.38 -> X
  lifts the marginal CC offer when CCs are pushed up the economic ramp in tight
  afternoons (where the model under-prices the $75-200 band); ``peak`` 5.0 -> Y
  widens the duct-firing/scarcity ceiling. The afternoon marginal unit is a
  part-loaded CC, so steepening its upper ramp is what raises the top tail.
* **CT_PEAKER — lower the whole curve.** committed/econ_low/econ_high/peak all
  come down so peakers enter the merit order cheaper and set moderate mid-peak
  prices more often, instead of sitting as a high, rarely-reached ceiling above
  the CC fleet.

Everything else (CT_PEAKER dispatch-as-peaker fix, ct_intermediate_split, coal
sigmoids, convex econ ramp, congestion/basis/interchange) is pjm 61 unchanged.
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
    OFFER_CURVE_OVERRIDES as _PJM61_OFFER_CURVES,
    PRB_OVERRIDES,
)

# Copy pjm 61's curves, then reshape only CC_REGULAR (top up) and CT_PEAKER
# (whole curve down). dict-copy per group so we never mutate the pjm 61 module's
# objects (they back run_pjm61_consolidate / pjm 62).
OFFER_CURVE_OVERRIDES = {g: dict(v) for g, v in _PJM61_OFFER_CURVES.items()}
OFFER_CURVE_OVERRIDES["CC_REGULAR"].update(
    {
        "econ_high": 1.60,  # pjm 63: 1.38 -> 1.60, steepen the CC upper econ ramp
        "peak": 6.0,  # pjm 63: 5.0 -> 6.0, widen the duct-firing scarcity band
    }
)
OFFER_CURVE_OVERRIDES["CT_PEAKER"].update(
    {
        "committed": 1.10,  # pjm 63: 1.25 -> 1.10
        "econ_low": 0.95,  # pjm 63: 1.05 -> 0.95
        "econ_high": 1.20,  # pjm 63: 1.40 -> 1.20
        "peak": 3.0,  # pjm 63: 4.0 -> 3.0
    }
)


def main() -> int:
    out_dir = Path("results/calibration/pjm63_offercurve")
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
        ct_intermediate_split=True,
        ct_intermediate_cf_threshold=30.0,
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 18.0,
            "offer_curve_smoothing_mid": 0.35,
        },
        note=(
            "pjm 63 offercurve: pjm 61 consolidate config + offer-curve reshape "
            "(one lever). CC_REGULAR econ_high 1.38->1.60 + peak 5.0->6.0 "
            "(steepen CC upper econ ramp + widen duct-firing scarcity band so the "
            "afternoon marginal CC lifts the $75-200 top tail); CT_PEAKER "
            "committed 1.25->1.10 / econ_low 1.05->0.95 / econ_high 1.40->1.20 / "
            "peak 4.0->3.0 (lower the whole peaker curve so peakers fill mid-peak "
            "cheaper instead of a rarely-reached ceiling). Offer-curve tuning "
            "(CLAUDE.md #1 second step), not a residual adder. No co-opt (pjm 62 "
            "showed zone-aggregate reserve scoping clears $0)."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
