"""Driver: PJM 61 — consolidate the structurally-correct fixes, 2023-2025.

pjm 60 ported six ERCOT run-157 mechanisms wholesale to attack the price
duration curve compression; the audit (handoff "pjm 61+") showed the storage
ports were *harmful and structurally unjustified for PJM* — the $10
battery_dispatch_adder killed PJM battery arbitrage (0.11->0.01 TWh discharge)
with no price lift, storage_daily_cycling is an unnecessary constraint on PJM's
small battery fleet, and cc_duct_peaking / chp_steam_following removed effective
peak supply and perversely *dropped* prices.  None of those decompress the
curve, because the compression is not an offer-curve problem (see below).

This run keeps only the structurally-correct levers and adds the one convex-ramp
shape that *is* right, dropping every harmful ERCOT port:

* CT_PEAKER dispatch fix (pjm 59): committed 0.878->1.25, econ_low 0.879->1.05
  so CTs clear as peakers (~3% CF) instead of baseload (~100% CF, the pjm 58
  defect).  ct_intermediate_split (threshold=30%): 62/70 CAMPD plants are
  intermediate-duty -> flatter CT_INTERMEDIATE curve; 8 remain true peakers.
  This is a real structural correction (CLAUDE.md #1) — CTs were dispatching
  against physics — so it makes pjm 61 strictly more faithful than the pjm 58
  keeper regardless of the price residual.
* CC_REGULAR peak 3.4->5.0, cc_duct_peaking_cap_pct 12->18% (pjm 59): widen the
  duct-firing scarcity band (a physical CC capability), kept as a uniform
  ceiling — NOT the per-plant cc_duct_peaking flag that pjm 60 showed removes
  too much marginal supply.
* offer_curve_smoothing_mid=0.35 (the one keeper from pjm 60): a convex econ
  ramp — 35% of the lo->hi rise reached at the capacity midpoint, so the bottom
  is cheap and marginal cost accelerates as dispatch tightens.  Small but
  structurally correct (matches the real heat-rate/output convexity).

Dropped from pjm 60 (harmful ERCOT ports, no PJM justification): the $10
battery_dispatch_adder, storage_daily_cycling, the per-plant cc_duct_peaking
flag, and chp_steam_following.

NOTE ON THE PRICE TAIL (why this run does not close the duration-curve gap, and
why no energy-only run can).  docs/multi-iso/pjm-reserve-ordc.md localizes the
PJM miss as the $75-200 afternoon reserve *opportunity-cost* band: PJM RT price
= energy LMP + a co-optimized Operating-Reserve-Demand-Curve reserve price the
energy-only LP cannot produce.  The structural fix is energy+reserve
co-optimization in the LP (energy_reserve_coopt) — but (a) the zone-aggregate
co-opt OOMs above ~16 GB and the per-gen build is heavier still, so it is not
runnable on the 15 GB box this run executes on, and (b) the binding prerequisite
is commitment posture: the perfect-foresight LP holds ~14 GW online reserve when
PJM's real RT held ~3 GW, so the published vertical ORDC step never fires.  This
run therefore consolidates the structurally-correct level calibration; the tail
is a separate, hardware/commitment-blocked structural build (handoff updated in
docs/multi-iso/pjm-reserve-ordc.md).
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

OFFER_CURVE_OVERRIDES = {
    # --- CC ---
    "CC_REGULAR": {
        "committed": 0.75,
        "econ_low": 0.92,
        "econ_high": 1.38,
        "peak": 5.0,  # pjm 59: widen duct-firing/scarcity markup (physical cap)
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
        "committed": 1.25,  # pjm 59: part-load penalty above base HR (peaker)
        "econ_low": 1.05,  # pjm 59: base dispatch above base HR
        "econ_high": 1.40,
        "peak": 4.0,  # kept (NOT the pjm 60 peak=10 ERCOT scarcity port)
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
    out_dir = Path("results/calibration/pjm61_consolidate")
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
        # --- CT intermediate split (pjm 59) ---
        ct_intermediate_split=True,
        ct_intermediate_cf_threshold=30.0,
        # --- Offer curves ---
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 18.0,  # pjm 59 (uniform ceiling)
            "offer_curve_smoothing_mid": 0.35,  # NEW: convex econ ramp (pjm 60)
        },
        note=(
            "pjm 61 consolidate: keep the structurally-correct pjm 59 fixes "
            "(CT_PEAKER dispatch fix committed 0.878->1.25 / econ_low "
            "0.879->1.05 so CTs clear as ~3% CF peakers not ~100% baseload; "
            "ct_intermediate_split threshold=30%; CC_REGULAR peak 3.4->5.0; "
            "cc_duct_peaking_cap_pct 12->18% uniform ceiling) + add "
            "offer_curve_smoothing_mid=0.35 (convex econ ramp). DROP the "
            "harmful pjm 60 ERCOT ports (battery_dispatch_adder=$10, "
            "storage_daily_cycling, per-plant cc_duct_peaking flag, "
            "chp_steam_following). Price-tail decompression is a separate "
            "structural build (energy+reserve co-opt) blocked on memory "
            "(co-opt OOMs >16 GB) and commitment posture — see "
            "docs/multi-iso/pjm-reserve-ordc.md."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
