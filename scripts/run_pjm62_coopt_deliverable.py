"""Driver: PJM 62 — energy+reserve co-opt with DELIVERABLE reserve-supply scoping.

The honest, runnable probe from the pjm 62 handoff (step 2). It keeps the pjm 61
consolidate config (the structurally-correct level calibration) verbatim and adds
the energy+reserve co-optimization with the **deliverable reserve-supply scoping**
the PJM branch was previously "wired but un-scoped" for:

* ``energy_reserve_coopt`` — the measured PJM_RTO Primary Reserve requirement
  (~3.4 GW) clears against the published vertical two-step ORDC ($850/$300/+190
  MW) inside the LP, so the reserve clearing price emerges as the balance-row
  dual and would lift the energy LMP (PJM RT = LMP + reserve price).
* ``pjm_reserve_supply_cap`` — cap cleared reserve at the fleet's 10-min
  DELIVERABLE ramp (Σ ramp10[eligible], availability-scaled), the PJM analogue of
  ercot_reserve_supply_cap, instead of ~38 GW of total eligible thermal headroom.
* ``pjm_reserve_online_gated`` — gate reserve to ONLINE (synchronized) capacity
  (R − ρ·ΣP ≤ 0, ρ=1.0 default), so idle capacity backs no reserve.

Together the cap + gate reproduce the bind-gate's tightest defensible reserve
measure ("online + 10-min-deliverable"). Per the 2026-06-28 re-gate in
docs/multi-iso/pjm-reserve-ordc.md, this is EXPECTED to still clear ~$0 across the
broad afternoon band (deliverable headroom ~10 GW median ≫ the ~3.4 GW
requirement on a ~180 GW fleet) — the perfect-foresight LP is not tight when PJM's
real RT was tight. The probe empirically confirms that prerequisite with current
code: the top-tail decompression needs per-gen R[g]≤ramp10[g] co-opt (reserve
competing with energy on the marginal unit) PLUS commitment tightening, on a box
big enough for the heavier per-gen build. Nothing here is fitted to the LMP
residual (claude.md #11): the requirement is measured, the curve is published, the
cap is a physical deliverability definition.

NB (corrects the doc's stale memory claim): the zone-aggregate PJM co-opt DOES fit
the 15 GB calibration box — a single-year memtest peaked ~13.9 GB. Years still
solve sequentially (one year's LP per process at a time), so the 3-year run is
safe; do not parallelize the year loop.
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
from scripts.run_pjm61_consolidate import (  # noqa: E402
    BIT_OVERRIDES,
    OFFER_CURVE_OVERRIDES,
    PRB_OVERRIDES,
)


def main() -> int:
    out_dir = Path("results/calibration/pjm62_coopt_deliverable")
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
        # --- pjm 62: energy+reserve co-opt with deliverable supply scoping ---
        energy_reserve_coopt=True,
        pjm_reserve_supply_cap=True,
        pjm_reserve_online_gated=True,
        pjm_reserve_online_rho=1.0,
        note=(
            "pjm 62 coopt deliverable: pjm 61 consolidate config + "
            "energy_reserve_coopt with deliverable reserve-supply scoping "
            "(pjm_reserve_supply_cap = Σ ramp10[eligible] + pjm_reserve_online_gated "
            "ρ=1.0). Measured PJM Primary req (~3.4 GW) vs published two-step ORDC, "
            "cleared inside the LP. Honest probe (handoff step 2): EXPECTED ~$0 broad "
            "band because the perfect-foresight LP is not tight (deliverable reserve "
            "~10 GW ≫ 3.4 GW req); confirms the top-tail fix needs per-gen "
            "R[g]≤ramp10[g] + commitment tightening, not zone-aggregate scoping. "
            "Memtest: zone-aggregate co-opt fits 15 GB (~13.9 GB peak/yr), correcting "
            "the doc's stale OOM claim. Nothing fitted to the residual (claude.md #11)."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
