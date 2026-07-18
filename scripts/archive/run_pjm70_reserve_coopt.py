"""Driver: PJM 70 — energy+reserve co-optimization (reserve-demand co-opt).

Layers the PJM energy+reserve co-optimization onto the pjm-69 keeper baseline
(interchange caps + CC/CT rebalance), changing exactly two things:

1. **``energy_reserve_coopt=True``** — turn on the co-optimized reserve balance
   row inside the LP. PJM's reserve design (``reserve_config._pjm_design``) is
   the measured PJM_RTO Primary Reserve requirement (a published Manual-13
   reliability quantity; forecast path falls back to the fleet-responsive
   1.5×-MSSC formula) priced by the published two-step ORDC demand curve
   (``$850`` inside the requirement, ``$300`` for the next 190 MW, ``$0`` beyond
   — PJM Manual 11 §4.3.3, FERC EL19-58/ER19-1486). Reserve-eligible fleet is
   the ISO-agnostic thermal mask (gas_cc/ct/st, coal, nuclear, oil).

2. **``pjm_reserve_supply_cap=True``** — cap the single reserve class's cleared
   reserve at the fleet's physical 10-minute deliverable ramp
   (``RAMP10_FRAC_BY_GROUP`` × pmax, availability-scaled). Without this the
   single shared-headroom row counts the full ~38 GW of idle fleet headroom as
   reserve supply — far above the ~3.4 GW Primary requirement — so the vertical
   ORDC step never fires and the co-opt is a no-op
   (``docs/multi-iso/pjm-reserve-ordc.md`` honesty gate). The deliverable-ramp
   cap is a physical capability (regenerable for a forecast year, responsive to
   the fleet), never fitted to the LMP residual (CLAUDE.md #11).

Rationale (per the failure signature of pjm-69, which is NOT-YET):
  * C3c scarcity tail = 0 model hours vs 6/18/59 actual — the ORDC step is the
    physically-correct scarcity-pricing mechanism PJM actually runs; it should
    lift the price tail.
  * C1 CC over / CT under (+17 CC / −11 CT TWh in 2024) — forcing reserve-
    eligible mid-merit units (CCs) to hold deliverable headroom backs down their
    energy and shifts it toward the quick-start CT fleet, partly unwinding the
    merit-order inversion.

Everything else (coal sigmoids, passthrough, must-run, drop-pof, sync-srmc, gas
monthly actuals, PJM zonal gas basis, PJM congestion, reference-price interface,
priced interchange, CC derate from top, hydro EIA-930 monthly,
hydro_backfill_year=2024, btm_backfill_year=2024, reliability floor, CT
intermediate split, seam flow/export caps, offer-curve overrides, curve
smoothing) is preserved from pjm-69 verbatim.
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
from scripts.archive.run_pjm69_interchange_caps import (  # noqa: E402
    OFFER_CURVE_OVERRIDES,
)


def main() -> int:
    out_dir = Path("results/calibration/pjm_reserve_coopt")
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
        # --- the only two changes vs pjm-69 ---
        energy_reserve_coopt=True,
        pjm_reserve_supply_cap=True,
        note=(
            "PJM reserve-demand co-opt (unwind CC-over/CT-under + lift scarcity "
            "tail): layers energy+reserve co-optimization onto pjm-69 verbatim. "
            "energy_reserve_coopt=True turns on the co-optimized reserve balance "
            "row (measured PJM_RTO Primary requirement + published two-step ORDC "
            "$850/$300, Manual 11 sec 4.3.3 / FERC EL19-58). "
            "pjm_reserve_supply_cap=True caps cleared reserve at the fleet's "
            "physical 10-min deliverable ramp so the ORDC step can bind instead "
            "of drawing on idle full-fleet headroom (grounded capability, not a "
            "residual fit). Targets: lift C3c scarcity tail (0->6/18/59 actual) "
            "and unwind the CC-over/CT-under merit-order inversion by forcing "
            "reserve-eligible CCs to hold deliverable headroom. All other pjm-69 "
            "settings verbatim."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
