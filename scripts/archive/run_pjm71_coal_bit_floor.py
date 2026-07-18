"""Driver: PJM 71 — raise coal-bituminous passthrough floor.

One-lever probe: raise ``coal_bit_passthrough_floor`` from the pjm-69/70
value of 0.55 to 0.75.  Everything else — reserve co-opt, interchange caps,
CC/CT rebalance, coal sigmoids, must-run, all pjm-70 settings — is verbatim.

Diagnosis (pjm-70 failure signature):
  * C1 coal over-dispatched: +6.3/+6.9 TWh in 2023/24, +4.9% in 2025.
  * C3a price 10-15% too cheap.
  Both point to the same defect: bituminous coal is offered BELOW its
  delivered marginal cost.  At floor=0.55, when gas is cheap coal passes
  only 55% of delivered fuel cost into its offer — it clears too early and
  caps the marginal price.

Fix: raise the floor so coal offers nearer its true delivered cost.
  * Coal backs off the margin → unwinds C1 coal-over.
  * Gas/coal set a higher clearing price → lifts C3a.

The passthrough floor is a physical fuel-cost fraction (delivered $/MMBtu ×
heat_rate), not a residual-tuned adder — it satisfies the forward-analogue
test (CLAUDE.md #10).  A higher floor is the more-accurate physical input;
per CLAUDE.md #11 if it worsens a fit, that's a discovered bug elsewhere.

Sigmoid params (active): floor=0.75 (CHANGED), ceil=1.32, gas_mid=3.40,
gas_slope=2.5 — all other params from COAL_SIGMOID_DEFAULTS[(PJM, bituminous)].

Reserve co-opt is KEPT ON (energy_reserve_coopt + pjm_reserve_supply_cap)
per CLAUDE.md #11 — structurally correct, both calibrated ISOs run it ON.
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
    PRB_OVERRIDES,
)
from scripts.archive.run_pjm69_interchange_caps import (  # noqa: E402
    OFFER_CURVE_OVERRIDES,
)

BIT_OVERRIDES = {"coal_bit_passthrough_floor": 0.75}


def main() -> int:
    out_dir = Path("results/calibration/pjm_coal_bit_floor")
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
            "PJM 71 coal-bit-floor 0.75: raise coal_bit_passthrough_floor "
            "from 0.55 to 0.75. One-lever probe targeting C1 coal over-dispatch "
            "(+6.3/+6.9 TWh 2023/24) AND C3a price-too-cheap (10-15%). Both "
            "stem from bituminous coal offering below delivered marginal cost at "
            "floor=0.55. Higher floor = coal offers nearer true delivered fuel "
            "cost (physical fuel-passthrough fraction, CLAUDE.md #10 forward-"
            "analogue). Coal backs off margin -> unwinds C1; gas/coal set "
            "higher clearing price -> lifts C3a. All other settings pjm-70 "
            "verbatim (reserve co-opt ON, interchange caps, CC/CT rebalance). "
            "Sigmoid: floor=0.75, ceil=1.32, gas_mid=3.40, gas_slope=2.5."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
