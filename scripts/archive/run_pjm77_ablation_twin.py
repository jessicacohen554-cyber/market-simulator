"""Driver: D-3 zero-forcing ablation twin of the pjm-77 keeper (CLAUDE.md rule 20).

The pjm-77 recipe (``run_pjm77_ct_relfloor_reconcile.py``) VERBATIM, solved with
``zero_forcing_ablation=True``: every merchant floor/bridge/drag neutralized via
``ScenarioConfig.as_zero_forcing_ablation`` (off-list derived from the D-2
mechanism registry), keeping only the structural protected set (nuclear
must-run, CHP steam, coal take-or-pay). The keeper-vs-twin per-class delta
quantifies what each merchant floor buys; registered alongside the keeper so
E9/audit D-3 can score it. No parameter differs from the keeper config — the
transform is applied inside ``run_year``/``solve_and_persist``.
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
from scripts.archive.run_pjm74_cc_ct_rebalance import (  # noqa: E402
    BIT_OVERRIDES,
    OFFER_CURVE_OVERRIDES,
)
from scripts.archive.run_pjm75_ct_drag_cc_cap import (  # noqa: E402
    CONFIG_OVERRIDES,
    CT_DRAG_OVERRIDES,
)


def main() -> int:
    out_dir = Path("results/calibration/pjm77_ct_relfloor_reconcile-ablation")
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
        zero_forcing_ablation=True,
        ablation_of="pjm77_ct_relfloor_reconcile",
        note=(
            "D-3 zero-forcing ablation twin of pjm-77 (CLAUDE.md rule 20): the "
            "pjm77_ct_relfloor_reconcile recipe verbatim with every merchant "
            "floor/bridge/drag neutralized (ScenarioConfig."
            "as_zero_forcing_ablation; off-list from the D-2 mechanism "
            "registry), structural protected set kept. Registered alongside "
            "the keeper for the E9 keeper-vs-twin delta."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
