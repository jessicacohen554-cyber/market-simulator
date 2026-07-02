"""Driver: PJM 74 — CC/CT offer-curve rebalance (the run-72 slot's planned work).

Targets the C1 residual left open by keeper pjm-71 (commit 7da5a12: "Remaining
CC_REG/CT imbalance (+21/-10 TWh 2024) is pre-existing and targeted by run-72
CC/CT offer rebalance"): 2024 CC_REGULAR +20.94 TWh / +2.1pp over (335.2 vs
314.3) and CT_PEAKER -9.72 TWh / -1.2pp under (18.1 vs 27.8).

One structurally-motivated step along the pjm-69 axis (CC economic tranches up,
CT curve down), chosen from the offer-curve structure — NOT bisected on the
residual (CLAUDE.md #1):

1. **CC_REGULAR econ_low 0.92 -> 1.00** — Manual-15 composite-cost floor. The
   LP carries no no-load / start-cost variable, so each tranche's offer must be
   the composite cost at that loading point; PJM Manual 15 cost development
   requires no-load + incremental offers to recover total production cost, which
   puts every above-min-load increment at >= 1.0x full-load AHR fuel cost once
   no-load is folded in. The inherited 0.92 ("pjm-58 level",
   docs/parameter-citations.md:809 marks it needs-citation) prices the cheap
   half of the CC econ ramp below composite cost recovery — exactly the band
   that undercuts CT and coal in shoulder hours. Side effect is the right
   direction for C3a: CC-marginal mid-merit hours reprice upward with no fitted
   adder.

2. **CT_PEAKER econ_high 1.40 -> 1.27** — Manual-15 cost-cap ceiling. PJM is a
   cost-capped market (three-pivotal-supplier test); Manual 15 Section 2.3
   limits the cost-based offer adder to 10% of total cost. The worst CT econ
   tranche's incremental heat rate runs ~15% above the class-average AHR
   (oldest frames), so the cost-capped offer ceiling is ~1.15 x 1.10 ~= 1.27x
   AHR fuel. The current 1.40 exceeds what a cost-capped CT can lawfully offer.
   Dominant CT own-knob per the PJM Jacobian (docs/calibration-log.md:1031-1033,
   econ_high ~ -21 TWh/unit own-class -> expected CT ~ +2.7 TWh).

Deliberately NOT moved (structure says stop, even though the residual asks for
more — CLAUDE.md #1/#11):
- CC committed stays 1.00: already at/past the Manual-15 min-load SRMC floor
  (docs/handoffs/pjm-cc-overgen-recommendation-2026-06.md Rank 3, floor ~0.87;
  ERCOT keeper run-157: 0.998). Further raises are year-uniform (pjm-66->67
  moved all three years by ~-8 TWh) and would break the clean 2023 CC fit
  (-2.3 TWh) to chase a 2024-concentrated miss whose root cause is the missing
  commitment / per-gen reserve structure (Rank 1/2, the pjm-reserve-ordc
  Phase 1-2 thread), not the offer level.
- CT peak block stays pct_peaking=20 / peak=4.0: it is the standing proxy for
  reserve-deployment / scarcity offers pending the per-gen R[g] <= ramp10[g]
  co-opt build; the tail is explicitly out of scope for this run
  (docs/multi-iso/pjm-reserve-ordc.md: offer retune is Phase 3, tail
  decompression blocked on Phases 1-2).

Everything else pjm-71 verbatim: coal_bit floor 0.65 sigmoid (ceil 1.32,
gas_mid 3.40, slope 2.5), reserve co-opt ON, historic outages, zonal gas basis,
congestion, priced interchange, seam caps, hydro/BTM backfill 2024.

Predicted signs (evaluate after, keep even if fit worsens where structure is
right): CC down all years (2023 may go more negative — accepted), CT up all
years (2025 may overshoot — accepted), coal up slightly (2024 has -2.0 TWh
headroom), mid-merit prices up (C3a is -9.4%/-14.8% under).
"""

from __future__ import annotations

import copy
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
    PRB_OVERRIDES,
)
from scripts.run_pjm69_interchange_caps import (  # noqa: E402
    OFFER_CURVE_OVERRIDES as _PJM69_OFFER_CURVE_OVERRIDES,
)

BIT_OVERRIDES = {"coal_bit_passthrough_floor": 0.65}

# pjm-69 curve verbatim except the two Manual-15-grounded moves documented in
# the module docstring. Deep-copied so the pjm-69 module dict stays pristine
# for any concurrent import.
OFFER_CURVE_OVERRIDES = copy.deepcopy(_PJM69_OFFER_CURVE_OVERRIDES)
# Manual 15 composite-cost floor: no no-load variable in the LP, so no tranche
# may offer below 1.0x full-load AHR fuel cost (was 0.92, uncited pjm-58 level).
OFFER_CURVE_OVERRIDES["CC_REGULAR"]["econ_low"] = 1.00
# Manual 15 Section 2.3 cost-cap ceiling: 10% adder on incremental cost, worst
# CT tranche IHR ~1.15x class AHR -> 1.15 x 1.10 ~= 1.27 (was 1.40, above cap).
OFFER_CURVE_OVERRIDES["CT_PEAKER"]["econ_high"] = 1.27


def main() -> int:
    out_dir = Path("results/calibration/pjm74_cc_ct_rebalance")
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
        hydro_backfill_year=2024,
        btm_backfill_year=2024,
        reliability_floor=True,
        ct_intermediate_split=True,
        ct_intermediate_cf_threshold=30.0,
        pjm_seam_flow_limit=True,
        pjm_seam_export_limit=True,
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 18.0,
            "offer_curve_smoothing_mid": 0.35,
        },
        energy_reserve_coopt=True,
        pjm_reserve_supply_cap=True,
        note=(
            "PJM 74 CC/CT offer rebalance (planned as run-72): one Manual-15-"
            "grounded step along the pjm-69 axis. CC_REGULAR econ_low 0.92->"
            "1.00 (composite-cost floor: LP has no no-load variable, M15 cost "
            "recovery puts every increment >= 1.0x full-load AHR fuel). "
            "CT_PEAKER econ_high 1.40->1.27 (M15 Sec 2.3 10% cost adder cap "
            "on worst-tranche IHR ~1.15x -> ceiling ~1.27; 1.40 exceeded the "
            "cost cap). CC committed stays 1.00 (at/past M15 min-load floor; "
            "committed raises are year-uniform and would break clean 2023 "
            "CC); CT peak block untouched (scarcity/tail out of scope per "
            "pjm-reserve-ordc Phase 1-2 gate). All else pjm-71 verbatim "
            "(coal_bit floor 0.65, reserve co-opt ON)."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
