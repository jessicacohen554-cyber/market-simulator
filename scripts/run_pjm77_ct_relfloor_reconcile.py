"""Driver: PJM 77 — CT reliability-floor / net-load-drag reconcile (keeper candidate).

The pjm-76 recipe VERBATIM, re-run on the rule-19 reconciliation fix
(``config.iso_configs.drop_drag_owned_reliability_specs``): when the CT_PEAKER
net-load deployment drag is active, the temperature reliability floor's
CT_PEAKER limbs are dropped so the two do not stack into an all-day floor.

pjm-76 FAILED the legitimacy diagnostics on **D-4 off-window binding**:
``reliability_floor x CT_PEAKER`` bound 97-99.7% of its floored MWh OUTSIDE its
justified window h15-21, all three years. Diagnosis
(``docs/FINDING-pjm-burndown-2026-07.md``): the two enabled PJM CT_PEAKER
reliability limbs (EMAAC tmax 0.2838, West_APS tmax 0.3208) have no
start_hour/end_hour, so on a hot day they floored CT_PEAKER at ~0.28-0.32x
available capacity for ALL 24 h — including overnight, where the pjm-75 CT
net-load drag already owns the ramp-window [15,22) commitment and measured
CAMPD CT CF is ~0.016 (h0-6) vs ~0.38 at the afternoon peak. Pjm-75 had ADDED
the drag on top of the pre-existing reliability floor without reconciling them
(CLAUDE.md rule 19). Measured proof (2024 diag): the floor forced 941 MW of
CT_PEAKER overnight (h0-6) in the two zones on hot days vs 34 MW on non-hot
nights (the economic level) — a 28x phantom exactly equal to the 0.12 TWh
reliability_floor x CT_PEAKER D-2 attribution.

The fix drops the two CT_PEAKER limbs (the drag is now the SINGLE CT commitment
mechanism), removing the overnight phantom and clearing the D-4 failure. No
fitted parameter changed; the drag, offer curves, coal sigmoids, outages,
reserve co-opt etc. are all pjm-76 verbatim. This is a structural improvement
(CLAUDE.md rule 1/17/19): a floor removal grounded in CAMPD hot-day CT CF, not
a residual tune. Dispatch change is ~0.12 TWh (the removed overnight phantom).
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
from scripts.run_pjm74_cc_ct_rebalance import (  # noqa: E402
    BIT_OVERRIDES,
    OFFER_CURVE_OVERRIDES,
)
from scripts.run_pjm75_ct_drag_cc_cap import (  # noqa: E402
    CONFIG_OVERRIDES,
    CT_DRAG_OVERRIDES,
)


def main() -> int:
    out_dir = Path("results/calibration/pjm77_ct_relfloor_reconcile")
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
            "PJM 77 CT reliability-floor / net-load-drag reconcile (keeper "
            "candidate): pjm-76 recipe VERBATIM on the rule-19 fix "
            "(drop_drag_owned_reliability_specs). The drag now owns CT_PEAKER "
            "commitment; the two all-day CT_PEAKER reliability limbs (EMAAC, "
            "West_APS) are dropped, clearing the D-4 off-window failure "
            "(97-99.7% off-window, all years) by removing the ~0.12 TWh "
            "overnight phantom the floor forced on hot days. No fitted "
            "parameter changed. See docs/FINDING-pjm-burndown-2026-07.md."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
