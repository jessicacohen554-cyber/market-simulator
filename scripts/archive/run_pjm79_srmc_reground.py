"""Driver: PJM 79 — G-21 SRMC re-grounding of the sub-SRMC ST_GAS / CT_INTERMEDIATE bands.

The pjm-78 baseline recipe with the two rule-13 residual artifacts re-grounded
to the Manual-15 SRMC floor (gap register G-21;
`docs/FINDING-pjm-burndown-2026-07.md` §2):

* **ST_GAS** committed/econ_low/econ_high 0.4752/0.6552/0.90 → **1.00** — a
  non-CHP gas steamer's part-load incremental HR is *above* its full-load AHR,
  so no tranche may offer below 1.0x AHR x delivered fuel (the same Manual-15
  composite-cost floor CC_REGULAR received in pjm-74). econ_high is raised to
  the floor too (0.90 was also sub-SRMC and would invert the band ordering).
  The 0.4752/0.6552 values were residual-set in the pjm-59..74 sweep with no
  physical basis (DOF ledger identification: residual).
* **CT_INTERMEDIATE** committed/econ_low 0.9/0.92 → **1.00** — a non-CHP CT
  below the SRMC floor has no physical basis; econ_high 1.08 and peak 2.0 are
  already above the floor and stay.

Grounding, not a re-tune: both classes move to the same measured/tariff floor
their siblings already carry (generic CT_INTERMEDIATE ships 1.00/1.00; NYISO
SOM-grounded ST_GAS committed is 0.97 on the same physics). Per rule 14, the
fit is expected to get WORSE where the sub-SRMC offers were compensating for
another error (model ST_GAS over-runs actuals by +112/+27/+30 % — the flood
these bands create); the cycle's decomposition attributes that compensation
and opens root-cause issues instead of tuning the bands back down.

Registered per rule 15; full span 2023-2025 per rule 16; keeper decision is a
log recommendation only (no swap in-session).
"""

from __future__ import annotations

import copy
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
from scripts.archive.run_pjm74_cc_ct_rebalance import (  # noqa: E402
    BIT_OVERRIDES,
    OFFER_CURVE_OVERRIDES as _PJM74_OFFER_CURVE_OVERRIDES,
)
from scripts.archive.run_pjm75_ct_drag_cc_cap import (  # noqa: E402
    CONFIG_OVERRIDES,
    CT_DRAG_OVERRIDES,
)

# pjm-74/77/78 curve verbatim except the two G-21 re-groundings documented in
# the module docstring. Deep-copied so the pjm-74 module dict stays pristine.
OFFER_CURVE_OVERRIDES = copy.deepcopy(_PJM74_OFFER_CURVE_OVERRIDES)
# Manual 15 composite-cost floor (no no-load variable in the LP): no ST_GAS
# tranche below 1.0x AHR — part-load IHR of a gas steamer exceeds full-load.
OFFER_CURVE_OVERRIDES["ST_GAS"]["committed"] = 1.00
OFFER_CURVE_OVERRIDES["ST_GAS"]["econ_low"] = 1.00
OFFER_CURVE_OVERRIDES["ST_GAS"]["econ_high"] = 1.00
# Same floor for the intermediate-duty CT cohort (non-CHP CT below SRMC has no
# physical basis); econ_high 1.08 / peak 2.0 already clear the floor and stay.
OFFER_CURVE_OVERRIDES["CT_INTERMEDIATE"]["committed"] = 1.00
OFFER_CURVE_OVERRIDES["CT_INTERMEDIATE"]["econ_low"] = 1.00


def main() -> int:
    out_dir = Path("results/calibration/pjm79_srmc_reground")
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
        prb_overrides=CONFIG_OVERRIDES,
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
        ct_netload_drag=True,
        ct_drag_overrides=CT_DRAG_OVERRIDES,
        note=(
            "PJM 79 G-21 SRMC re-grounding: pjm-78 baseline recipe with the "
            "sub-SRMC residual artifacts re-grounded to the Manual-15 floor — "
            "ST_GAS committed/econ_low/econ_high 0.4752/0.6552/0.90 -> 1.00, "
            "CT_INTERMEDIATE committed/econ_low 0.9/0.92 -> 1.00. Grounded "
            "move (rule 13/14): a worse fit here is a discovered bug to "
            "root-cause, not a reason to revert."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
