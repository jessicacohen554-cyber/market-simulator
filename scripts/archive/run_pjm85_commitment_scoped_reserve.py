"""Driver: PJM 85 — commitment-scoped reserve supply (G-20b path B).

The pjm-83 SRMC-reground KEEPER recipe VERBATIM (``run_pjm80_srmc_reground_keeper``
``_solve`` kwargs) + the path-B reserve-supply scoping the pjm-84 verdict demanded
(``results/calibration/pjm84_online_gated_reserve/SUMMARY-g20b.md``):

* ``pjm_reserve_commitment_scoped=True`` (NEW) — the fa_p2-style availability
  mask, P1-native: the P0 base-cost run pattern defines each plant's online
  hours; non-fast-start reserve-eligible units (rule-18 physics gate — plant
  capacity-weighted min-down > 2 h or startup >= $30/MW, the NREL class-table
  thresholds) have availability zeroed in their plant's offline hours before the
  single scored P1 solve, offline gaps shorter than the plant's min-down bridged
  online. This is the exact mechanism ERCOT's AS-aware P2 uses to zero idle
  slow-start capacity out of the reserve-headroom RHS
  (``apply_commitment_with_coal_pin`` + ``ercot_commitment_headroom_overrides``),
  applied at the P0->P1 seam like the CAISO RA bridge because P2 is archived
  (``pipeline.commitment.build_pjm_reserve_p1_prep``).
* ``measured_ramp_capability=True`` (kept from pjm-84 — rule 14, measured over
  estimate) + the keeper's ``pjm_reserve_supply_cap``: with the mask on, the
  deliverable cap is recomputed on the MASKED fleet, so cleared reserve is
  bounded by "Σ ramp10 over ONLINE eligible units" — the pjm-reserve-ordc.md
  bind-gate "online + 10-min-deliverable" measure (~10 GW p50 / ~0.5 GW min vs
  the ~3.3-3.6 GW measured Primary requirement; predicted ~49 bind-h in 2024).

NOT ``pjm_reserve_online_gated`` (path A): the LP-linear ``R <= rho*sum P`` proxy
ties reserve supply to total online OUTPUT (tens of GW) — pjm-84 proved it a
structurally-faithful NON-FIRE (reserve dual $0 in all 26,280 h, min supply/req
3.4x/5.8x/8.7x). Path B supersedes it (one mechanism per phenomenon, rule 19;
the builder hard-errors on a stacked config). The published two-step ORDC
($850/$300/+190 MW) stays as filed — no breakpoint/penalty change (rule 11).

Zone-aggregate co-opt -> memory-light (~14.5 GB peak); the seam releases the P0
model before the cold P1 build so peak RSS stays ~one model. Full span
2023-2025 in one bundle (rule 16), years sequential (rule 12). Registered per
rule 15 whatever the outcome.
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
    "PJM 85 commitment-scoped reserve supply (G-20b path B): pjm-83 keeper "
    "recipe VERBATIM + pjm_reserve_commitment_scoped (fa_p2-style availability "
    "mask at the P0->P1 seam — non-fast-start reserve-eligible units zeroed in "
    "their plant's P0-offline hours, min-down gaps bridged, rule-18 physics "
    "gate; pipeline.commitment.build_pjm_reserve_p1_prep) + "
    "measured_ramp_capability (kept from pjm-84, rule 14). The deliverable "
    "supply cap (keeper's pjm_reserve_supply_cap) is recomputed on the masked "
    "fleet = the pjm-reserve-ordc.md bind-gate 'online + 10-min-deliverable' "
    "measure. NOT pjm_reserve_online_gated: path A proved structurally-"
    "faithful NON-FIRE in pjm-84 (dual $0 x 26,280 h, supply ties to online "
    "OUTPUT not headroom); path B supersedes (rule 19). Published two-step "
    "ORDC as filed (rule 11). Tests whether commitment-scoped online-"
    "deliverable reserve supply crosses the measured Primary requirement in "
    "genuine tail hours (reserve dual > 0) and what it does to C3a/C3c and "
    "the C1 fuel mix vs pjm-83/pjm-84."
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
        pjm_reserve_supply_cap=True,
        # --- G-20b path-B deltas vs pjm-83 keeper ---
        pjm_reserve_commitment_scoped=True,
        measured_ramp_capability=True,
        ct_netload_drag=True,
        ct_drag_overrides=CT_DRAG_OVERRIDES,
        **extra,
    )


def main() -> int:
    out_dir = Path("results/calibration/pjm85_commitment_scoped_reserve")
    run_dir = _solve(out_dir, note=NOTE)
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
