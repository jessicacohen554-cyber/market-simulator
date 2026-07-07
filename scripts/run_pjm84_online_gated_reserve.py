"""Driver: PJM 84 — online-gated deliverable reserve co-opt (G-20b).

The pjm-83 SRMC-reground KEEPER recipe VERBATIM (``run_pjm80_srmc_reground_keeper``
``_solve`` kwargs) with exactly two Phase-2 deltas that thin the co-opt's reserve
SUPPLY toward PJM's real synchronized-reserve product, so the published vertical
two-step ORDC requirement can bind:

* ``pjm_reserve_online_gated=True`` — the zone-aggregate reserve row becomes
  ``R[z] − ρ·Σ_g P[g] ≤ 0`` (dispatch._build_reserve_rows, online-gated path):
  an idle (P≈0) unit backs NO reserve and an online unit backs ρ×its output, so
  the ~14 GW of "synchronized-and-idle" perfect-foresight headroom (the pjm-81
  blocker) stops supplying spinning reserve for free. This is the genuine
  "reserve ∝ online output" mechanism the G-20b brief describes (path A: an
  LP-linear proxy for commitment-gated spinning reserve; the exact gate needs an
  online binary — path B / the P2 fa_p2 availability screen — noted in the code).
* ``measured_ramp_capability=True`` — FleetArrays.ramp10's NREL class fractions
  are reconciled against the measured ramp-capability datatype (EIA-860 "10M"
  fast-start floor + CAMPD CEMS 1-h envelope ceiling, data/clean/ramp-capability),
  so the deliverable supply cap (pjm_reserve_supply_cap, already in the keeper)
  uses the measured 10-min-reachable MW, not the class estimate (rule 14).

WHY NOT ``pjm_reserve_pergen`` (the third brief flag): in reserve_config.py the
pergen branch RETURNS before the online-gate logic — pergen is mutually exclusive
with online_gated (its joint ``Σ P + R ≤ Σ cap`` headroom lets idle in-pool
capacity back reserve, which is exactly why the pjm-81 pergen probe fired only
1 h/3 yr). The online-gate ``R ≤ ρ·Σ P`` is the lever that actually removes the
phantom idle headroom, and the pjm-reserve-ordc bind-gate probe predicts the
online+deliverable measure crosses the ~3.4 GW requirement ~49 h/2024 (vs
pergen's 1 h). So online_gated + supply_cap + measured_ramp is the buildable
realization of the brief's "online-scaled AND 10-min-deliverable" reserve; pergen
is documented separately (pjm-81) and NOT stacked here.

Zone-aggregate → memory-light (pjm-62 zone-aggregate co-opt peaked ~14.5 GB), so
no per-gen swapfile is needed. Full span 2023-2025 in one bundle (rule 16), years
sequential (rule 12). Registered per rule 15.
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
from scripts.run_pjm74_cc_ct_rebalance import BIT_OVERRIDES  # noqa: E402
from scripts.run_pjm75_ct_drag_cc_cap import (  # noqa: E402
    CONFIG_OVERRIDES,
    CT_DRAG_OVERRIDES,
)
from scripts.run_pjm79_srmc_reground import OFFER_CURVE_OVERRIDES  # noqa: E402

NOTE = (
    "PJM 84 online-gated deliverable reserve co-opt (G-20b): pjm-83 keeper "
    "recipe VERBATIM + pjm_reserve_online_gated (zone-aggregate R <= rho*sum P, "
    "idle capacity backs no spinning reserve — the genuine 'reserve prop. to "
    "online output' online-gate, dispatch._build_reserve_rows) + "
    "measured_ramp_capability (EIA-860 10M fast-start + CAMPD CEMS envelope "
    "reconciliation of FleetArrays.ramp10, feeding the keeper's "
    "pjm_reserve_supply_cap deliverable cap). NOT pergen: pergen supersedes "
    "online_gated in reserve_config and its joint headroom lets idle in-pool "
    "capacity back reserve (pjm-81 = 1 h/3 yr). Tests whether online-gating "
    "thins effective spinning supply enough for the published two-step ORDC "
    "requirement to bind (reserve dual > 0) in genuinely short hours. Path-A "
    "LP-linear proxy; path B (online binary / P2 availability) is the exact "
    "gate. Dispatch/fuel-mix compared vs pjm-83 to confirm no fitted fire "
    "(rule 1/11)."
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
        # --- G-20b Phase-2 deltas vs pjm-83 keeper ---
        pjm_reserve_online_gated=True,
        measured_ramp_capability=True,
        ct_netload_drag=True,
        ct_drag_overrides=CT_DRAG_OVERRIDES,
        **extra,
    )


def main() -> int:
    out_dir = Path("results/calibration/pjm84_online_gated_reserve")
    run_dir = _solve(out_dir, note=NOTE)
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
