"""Driver: PJM 82 — commitment-posture lever A/B probe (L-13 port).

The pjm-81 per-gen reserve co-optimization recipe VERBATIM plus exactly one
delta: ``pjm_commitment_posture`` (design note
``docs/multi-iso/miso-scarcity-posture-design-2026-07.md`` §A, ported to PJM;
``docs/handoffs/pjm-commitment-posture-port-2026-07.md``). Per non-fast-start
(zone, fuel-class) pergen pool, an online-capacity variable U with joint
P + R <= U, CEMS-measured min-load coupling P >= mlf*U, an NREL-class startup
charge on dU+, and the pergen reserve cap online-gated R <= ramp10*U — so PJM's
published Manual-11 Primary/MAD ORDC families can run short in thin hours
instead of drawing on ~14 GW of free perfect-foresight online headroom (the
pjm-81 blocker). Zero fitted parameters.

This is the single-mechanism B arm; A is pjm-81 (posture off — the verified
default-off no-op is the ablation twin, rule 21). Honesty-gated on the measured
PJM reserve-market series BEFORE the tail (rules 1/13;
scripts/report_pjm_posture_gate.py). Registered per rule 15; full span
2023-2025, single invocation, sequential years (rule 16).

Memory: run with MALLOC_ARENA_MAX=1 MARKET_SIM_HIGHS_THREADS=1 and a swapfile
(the pjm-78/79/81 convention on the 15 GB box). The posture adds 2*q online/
startup columns and the posture families over pjm-81's ~39 R columns.
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
    out_dir = Path("results/calibration/pjm82_commitment_posture")
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
        pjm_reserve_pergen=True,
        measured_ramp_capability=True,
        pjm_commitment_posture=True,
        ct_netload_drag=True,
        ct_drag_overrides=CT_DRAG_OVERRIDES,
        note=(
            "PJM 82 commitment-posture A/B probe (L-13 port): pjm-81 per-gen "
            "reserve co-opt recipe + pjm_commitment_posture (MISO §A lever "
            "ported, shared code — non-fast-start pool U/SU columns, "
            "CEMS-measured mlf min-load coupling, NREL-class startup charge, "
            "online-gated reserve cap R<=ramp10*U). Single-mechanism B arm vs "
            "pjm-81 (A, posture off). Zero fitted parameters; honesty-gated on "
            "the measured PJM reserve-market series (report_pjm_posture_gate.py)."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
