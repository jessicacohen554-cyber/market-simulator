"""Driver: PJM 55 — CC regular offer-curve & coal sigmoid tuning, 2023-2025.

Continuation of the pjm-54 congestion keeper stack (verbatim structural levers),
with offer-curve and sigmoid adjustments targeting three consistent misses:

  1. CC_REGULAR OVERDISPATCH (the dominant miss): extreme overrun at >85% CF
     (duct burner / peaking tranche too cheap), moderate overrun at 70-85% CF
     (econ_high too low), and the resulting over-export in every zone except
     Dominion/SWMAAC.

     Fix — raise the offer-curve top end:
       econ_high  1.1428 → 1.38   (+21%, prices out the 70-85% CF overrun)
       peak       2.77   → 3.40   (+23%, heavily penalises duct-burner dispatch)
       econ_low   0.7644 → 0.78   (slight lift, preserves <50% CF drag hours)

     Fix — per-plant peaking (not blanket pct_peaking):
       Remove the class-wide ``pct_peaking`` override from the CC_REGULAR offer
       curve so each plant's EIA-860 duct-burner share drives its own peak band
       (``cc_duct_peaking=True``, already on from ``_calibration_config``). Raise
       ``cc_duct_peaking_cap_pct`` 8→12: with ``cc_nameplate_summer_derate=True``
       the raw nameplate-vs-net-summer gap no longer folds the ambient summer
       derate, so the cap can safely go higher, letting high-duct plants
       (Guernsey 13%, etc.) price their real duct capacity at the expensive peak
       mult instead of being artificially capped.

     Fix — ``cc_derate_from_top`` (structural): outages reallocated to the
       expensive end of the curve (a multi-train CC sheds its least-efficient
       increments first), further trimming the >85% CF tail.

  2. COAL BITUMINOUS UNDERDISPATCH: consistent underrun across all three years
     and most zones. The take-or-pay BID sigmoid floor is still too high — coal
     doesn't compete in enough cheap-gas hours.

     Fix: deepen the cheap-gas BID discount:
       coal_bit_passthrough_floor  0.68 → 0.55
     (MISO bituminous is 0.60; PJM bit fleet is larger and more baseload).

  3. COAL PRB (subbituminous) UNDERDISPATCH: smaller class, consistent shortfall.

     Fix: lower the cheap-gas markup (the PRB sigmoid marks UP, not down):
       coal_sub_passthrough_floor  1.22 → 1.10   (less markup in cheap gas)
       COAL_PRB econ_high          0.8568 → 0.80  (slightly cheaper econ ramp)

All structural levers from the pjm-54 keeper are preserved verbatim.
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

# pjm-54 base recipe, with CC_REGULAR and COAL_PRB offer curves adjusted.
OFFER_CURVE_OVERRIDES = {
    "CC_REGULAR": {
        "committed": 0.6624,
        "econ_low": 0.78,  # was 0.7644 — slight lift
        "econ_high": 1.38,  # was 1.1428 — prices out 70-85% CF overrun
        "peak": 3.40,  # was 2.77   — penalises duct burner dispatch
        "econ_low_share": 0.5,
        # pct_peaking REMOVED: per-plant EIA-860 duct-burner shares drive each
        # plant's peak band (cc_duct_peaking=True, cap raised 8→12 below).
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
        "econ_high": 0.80,  # was 0.8568 — slightly cheaper econ ramp
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
    "coal_sub_passthrough_floor": 1.10,  # was 1.22 (table default) — less markup
}

BIT_OVERRIDES = {"coal_bit_passthrough_floor": 0.55}  # was 0.68 — deeper take-or-pay


def main() -> int:
    out_dir = Path("results/calibration/pjm55_offer_curves")
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
        cc_derate_from_top=True,  # structural: outages hit expensive tranches first
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 12.0,  # was 8.0 — raise since summer
            # derate no longer folded into duct gap (cc_nameplate_summer_derate)
        },
        note=(
            "pjm 55 offer-curve & coal sigmoid tuning on pjm-54 congestion keeper. "
            "CC_REGULAR: raise econ_high 1.14->1.38 (70-85% CF overrun), peak "
            "2.77->3.40, remove blanket pct_peaking (per-plant EIA-860 duct shares, "
            "cap raised 8->12). econ_low 0.76->0.78 (slight lift). Enable "
            "cc_derate_from_top (outage derate from expensive end — structurally "
            "correct). Coal BIT: deepen sigmoid floor 0.68->0.55 (more take-or-pay "
            "vs MISO 0.60). Coal PRB: lower sub sigmoid floor 1.22->1.10 (less "
            "markup), econ_high 0.8568->0.80 (cheaper ramp). Targets: trim CC "
            "over-export, boost coal BIT+PRB dispatch across all years/zones."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
