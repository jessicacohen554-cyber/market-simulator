"""Driver: PJM 64 — offer-curve reshape, raise the CT_PEAKER scarcity ceiling.

Follow-on to pjm 63 (PROBE). pjm 63 lifted the price-duration-curve **body**
~+0.5 $/MWh/yr via CC_REGULAR econ_high 1.38->1.60, but the **top tail stayed
flat/down**: lowering CT_PEAKER (peak 4.0->3.0 among other cuts) pulled the max
*down*, because in the model's tightest hours a CT peaker IS the marginal/ceiling
unit — cutting its offer capped the peaks and partly offset the CC lift.

pjm 64 isolates that one knob: **CT_PEAKER ``peak`` 3.0 -> 5.0**, everything else
verbatim from pjm 63. Raising the duct-firing/scarcity ceiling above pjm 61's 4.0
clears the lifted CC upper econ ramp (econ_high 1.60), so the CC's marginal offer
can set the clearing price in tight afternoons instead of being capped by a low
peaker ceiling. This tests the handoff hypothesis "was CT-lowering the thing
fighting the tail." Still energy-only, no co-opt (pjm 62 cleared reserve $0), no
P2 commitment (user's call). Offer-curve tuning is the CLAUDE.md #1 second step
(a heat-rate/markup statement that responds to forward conditions), not a
residual-fitted adder.

The lower CT_PEAKER committed/econ_low/econ_high (1.10/0.95/1.20 from pjm 63) are
kept so peakers still fill mid-peak cheaper; only the high scarcity tranche is
restored/raised.
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

# Copy pjm 61's curves, then apply the pjm 63 reshape, then the ONE pjm 64 lever
# (CT_PEAKER peak 3.0 -> 5.0). dict-copy per group so we never mutate the pjm 61
# module's objects (they back run_pjm61_consolidate / pjm 62 / pjm 63).
OFFER_CURVE_OVERRIDES = {g: dict(v) for g, v in _PJM61_OFFER_CURVES.items()}
# pjm 63 CC_REGULAR reshape (the body gain — kept): steepen upper econ ramp +
# widen the duct-firing scarcity band.
OFFER_CURVE_OVERRIDES["CC_REGULAR"].update(
    {
        "econ_high": 1.60,  # pjm 63: 1.38 -> 1.60
        "peak": 6.0,  # pjm 63: 5.0 -> 6.0
    }
)
# pjm 63 CT_PEAKER lower body (kept) + pjm 64 ONE lever: peak 3.0 -> 5.0.
OFFER_CURVE_OVERRIDES["CT_PEAKER"].update(
    {
        "committed": 1.10,  # pjm 63: 1.25 -> 1.10 (kept)
        "econ_low": 0.95,  # pjm 63: 1.05 -> 0.95 (kept)
        "econ_high": 1.20,  # pjm 63: 1.40 -> 1.20 (kept)
        "peak": 5.0,  # pjm 64 LEVER: pjm 63 3.0 -> 5.0 (above pjm 61's 4.0) so the
        # peaker scarcity ceiling clears the lifted CC econ_high and lets the CC
        # set the top-tail clearing price instead of capping it.
    }
)


def main() -> int:
    out_dir = Path("results/calibration/pjm64_offercurve")
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
            "pjm 64 offercurve: pjm 63 config + ONE lever, CT_PEAKER peak 3.0->5.0 "
            "(above pjm 61's 4.0). Keeps the pjm 63 CC_REGULAR body gain "
            "(econ_high 1.38->1.60, peak 5.0->6.0) and the lower CT_PEAKER "
            "committed/econ_low/econ_high (1.10/0.95/1.20), but raises the peaker "
            "duct-firing scarcity ceiling so it clears the lifted CC upper econ "
            "ramp — letting the marginal CC set the top-tail clearing price in "
            "tight afternoons instead of being capped by a low peaker ceiling "
            "(pjm 63 diagnosis: lowering CT_PEAKER peak pulled the max down). "
            "Offer-curve tuning (CLAUDE.md #1 second step), not a residual adder. "
            "Energy-only, no co-opt (pjm 62 cleared reserve $0), no P2."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
