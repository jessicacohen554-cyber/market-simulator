"""Driver: PJM 66 — CC committed raise + CT dispatch fix for CC/CT rebalance.

Addresses the open C1 failure on the pjm-58 keeper: CC_REGULAR over-runs (~73%
CF vs 61% CAMPD, +65 TWh) and CT_PEAKER under-runs (-18%/-33% for 2023/2024).

Two coupled levers, both structurally grounded (CLAUDE.md #1 structure first):

1. **CC_REGULAR committed raise 0.75 → 0.87** (Rank 3 from pjm-cc-overgen-
   recommendation): PJM Manual 15 min-load + no-load cost makes a CC's effective
   min-load $/MWh sit at-or-above full-load SRMC — 0.87 is the physically right
   floor (ERCOT keeper run-157: 0.998). The 0.75 floor clears PJM overnight LMP
   ($20-30), keeping CCs online 87.5% vs the real 78% (miss #1, ~60% of the +65
   TWh gap). Raising to 0.87 pushes the committed band above overnight clearing.

2. **CT_PEAKER dispatch fix** (pjm-59/61, missing from pjm-58 keeper): raise
   committed 0.8784→1.25, econ_low 0.8792→1.05 so CTs price as peakers (~3% CF)
   not baseload. pjm-58 carries the pre-fix CT values (the keeper predates the
   pjm-59 CT structural correction). Without the fix, CT offers are cheaper than
   the CC econ band, so the LP dispatches CCs instead of CTs in peak hours, and
   the freed CT energy appears as CC over-generation while CTs under-run.

Additionally:
- ct_intermediate_split (threshold=30%): 62/70 PJM CT plants are intermediate-
  duty (CAMPD median CF >=30%) → flatter CT_INTERMEDIATE curve; 8 remain true
  peakers with the steep CT_PEAKER curve.
- CC_REGULAR econ_high 1.38→1.50: steepen the upper ramp so the top CC slices
  are priced out of marginal hours (partial fix for miss #2, the 95-100% pile).
- offer_curve_smoothing_mid=0.35: convex econ ramp (pjm-60/61 keeper).
- cc_duct_peaking_cap_pct 18%: uniform duct ceiling (pjm-61).
- CC_REGULAR peak 5.0 (pjm-61): widen duct-firing scarcity markup.
- All coal sigmoids, hydro, congestion, seam-border levers from pjm-58 verbatim.

Predicted sign: CC volume ↓ (higher committed floor + steeper upper ramp), CT
volume ↑ (CT dispatch fix restores correct peaker merit order), coal ↑ slight
(coal backfills decommitted overnight CC — bounded ≤ ~120 TWh / ~20% share).
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
    BIT_OVERRIDES,
    PRB_OVERRIDES,
)

OFFER_CURVE_OVERRIDES = {
    # --- CC_REGULAR: raise committed floor toward SRMC ---
    "CC_REGULAR": {
        "committed": 0.87,  # 0.75 → 0.87: Manual 15 min-load SRMC floor
        "econ_low": 0.92,  # unchanged from pjm-58
        "econ_high": 1.50,  # 1.38 → 1.50: steepen upper ramp (miss #2)
        "peak": 5.0,  # pjm-61: duct-firing scarcity markup
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
    # --- CT_PEAKER: pjm-59/61 dispatch fix (missing from pjm-58) ---
    "CT_CHP": {
        "committed": 0.864,
        "econ_low": 0.864,
        "econ_high": 0.864,
        "peak": 1.008,
        "econ_low_share": 0.5,
    },
    "CT_PEAKER": {
        "committed": 1.25,  # 0.8784 → 1.25: part-load penalty (pjm-59/61)
        "econ_low": 1.05,  # 0.8792 → 1.05: base dispatch above HR (pjm-59/61)
        "econ_high": 1.40,  # pjm-61: economic ramp
        "peak": 4.0,  # pjm-58 keeper ceiling
        "econ_low_share": 0.5,
        "pct_peaking": 15.0,  # pjm-61: wider peaking band
    },
    "CT_INTERMEDIATE": {
        "committed": 1.05,
        "econ_low": 0.97,
        "econ_high": 1.15,
        "peak": 2.0,
        "econ_low_share": 0.5,
        "pct_peaking": 10.0,
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
    out_dir = Path("results/calibration/pjm66_cc_ct_calibration")
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
            "pjm 66 CC/CT calibration: two coupled levers for the C1 CC over-run / "
            "CT under-run. (1) CC_REGULAR committed 0.75→0.87 (Manual 15 SRMC floor, "
            "Rank 3 from pjm-cc-overgen-recommendation; ERCOT keeper 0.998). "
            "(2) CT_PEAKER dispatch fix from pjm-59/61 (committed 0.8784→1.25, "
            "econ_low 0.8792→1.05) so CTs clear as peakers not baseload — the "
            "pjm-58 keeper predates this structural correction. Also: CC econ_high "
            "1.38→1.50 (steepen upper ramp for miss #2), ct_intermediate_split "
            "(threshold=30%), CC peak 5.0, cc_duct_peaking_cap_pct 18%, "
            "offer_curve_smoothing_mid=0.35 (pjm-61). All coal/hydro/congestion/"
            "seam-border levers pjm-58 verbatim. Energy-only, no P2 commitment."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
