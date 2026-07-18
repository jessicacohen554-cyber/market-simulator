"""Driver: PJM 87 — per-gen OPPORTUNITY-COST reserve co-opt (G-20b successor).

The pjm-83 SRMC-reground KEEPER recipe VERBATIM (the pjm-86 baseline's exact
kwargs) + the per-gen opportunity-cost build the pjm-84/pjm-85 verdict
relocated the $75-200 afternoon residual to (SUMMARY-g20b-pathb.md: "the
$75-200 residual is the sub-shortage opportunity-cost reserve price, which
requires reserve to compete with energy on the same marginal unit"):

* ``pjm_reserve_pergen=True`` — the (zone, fuel-class) pooled ``R ≤ ramp10``
  co-opt (miso-39 memory tier, pjm-81 layout: joint ``Σ P + R ≤ Σ cap`` per
  pool-hour, measured RTO + MAD Primary families, published two-step ORDC).
* ``pjm_reserve_pergen_sync=True`` (**new**) — the pjm-81 non-fire fix:
  (i) the SYNCHRONIZED sub-product as its own measured balance families
  (RTO ``sr_req_mw`` + MAD ``mad_sr_req_mw``; published Synchronized ORDC
  rows as filed — never forcing the Primary row against a synchronized-only
  supply, the pjm-85 structural warning); (ii) each pool's R column split
  into a SYNC product (online 10-min ramp only) and a NON-SYNC product
  (offline fast-start ramp, Manual 11 sec 4.2), sharing the pool's joint
  P+R headroom row so either award consumes the same iron; (iii) sync caps
  online-scoped at the P0->P1 seam from the model's own P0 run pattern (the
  pjm-85 plant-online derivation, min-down gaps bridged) applied to the
  RESERVE bounds only — energy availability is NOT masked, so P1's free
  energy redispatch around the held reserve is exactly what prices the
  opportunity cost.
* ``measured_ramp_capability=True`` — measured EIA-860 "10M" fast-start
  floor + CAMPD CEMS envelope reconciliation of ``ramp10`` (rule 14, kept
  from pjm-81/84/85).

Published two-step ORDC ($850/$300/+190 MW) unchanged, Synchronized rows
read from the same cited curve CSV — no breakpoint/penalty edit (rule 11).
No MIP; P1 stays the scored pass (the sync-cap override makes P1 a cold
solve; the seam releases the P0 model first). Memory: G-40 subset-build
pattern; profile before the full span (CLAUDE.md #12).

A/B partner: ``run_pjm86_pjm83_head_baseline.py`` (same data tree, flags
off). Full span 2023-2025 in one bundle (rule 16), years sequential
(rule 12). Registered per rule 15 whatever the outcome. Instrumentation
wanted: reserve dual distribution (a $10-80 afternoon opportunity-cost band,
NOT $300-850 penalty spikes), C3a/C3b/C3c, C1/C2 deltas, D-2 CT_PEAKER drag
reconciliation (#1484, rule 19).
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
from scripts.archive.run_pjm74_cc_ct_rebalance import BIT_OVERRIDES  # noqa: E402
from scripts.archive.run_pjm75_ct_drag_cc_cap import (  # noqa: E402
    CONFIG_OVERRIDES,
    CT_DRAG_OVERRIDES,
)
from scripts.archive.run_pjm79_srmc_reground import OFFER_CURVE_OVERRIDES  # noqa: E402

NOTE = (
    "PJM 87 per-gen OPPORTUNITY-COST reserve co-opt (G-20b successor): "
    "pjm-83 keeper recipe VERBATIM (= the pjm-86 same-tree baseline) + "
    "pjm_reserve_pergen ((zone, fuel-class) pooled R<=ramp10 co-opt, "
    "measured RTO+MAD Primary families) + pjm_reserve_pergen_sync (NEW: "
    "measured Synchronized sub-product families sr_req_mw/mad_sr_req_mw on "
    "the published Synchronized ORDC rows; per-pool SYNC/NON-SYNC column "
    "split sharing the joint P+R row — sync servable only by ONLINE 10-min "
    "ramp, scoped at the P0->P1 seam from the P0 run pattern; offline "
    "fast-start ramp serves non-sync Primary per Manual 11 sec 4.2; energy "
    "availability NOT masked so P1 redispatch prices the opportunity cost) "
    "+ measured_ramp_capability (rule 14). Fixes pjm-81's non-fire (joint "
    "headroom let idle capacity back reserve; 1 fired hour / 3 yr) by "
    "composing per-gen ramp limits WITH online scoping. Wanted: $10-80 "
    "afternoon opportunity-cost duals, not $300-850 penalty spikes; single-"
    "mechanism A/B vs pjm-86."
)


def _solve(out_dir: Path, **extra):
    reference = _load_reference()
    return solve_and_persist(
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
        # --- per-gen opportunity-cost deltas vs the pjm-86 baseline ---
        # (pjm_reserve_supply_cap is REPLACED by the per-pool ramp10 bound,
        # the pjm-81 precedent — the zone-aggregate scoping flags are ignored
        # in pergen mode and would only mislead in run_config.json.)
        pjm_reserve_pergen=True,
        pjm_reserve_pergen_sync=True,
        measured_ramp_capability=True,
        ct_netload_drag=True,
        ct_drag_overrides=CT_DRAG_OVERRIDES,
        **extra,
    )


def main() -> int:
    out_dir = Path("results/calibration/pjm87_pergen_oppcost")
    run_dir = _solve(out_dir, note=NOTE)
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
