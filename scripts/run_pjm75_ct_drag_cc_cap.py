"""Driver: PJM 75 — CT net-load deployment drag + CC demonstrated-peak cap.

Targets the pjm-74 C1 residual with the two remaining measured, forward-native
levers at the 2024 CC-over / CT-under gap (2024 CC_REGULAR +16.57 TWh / +1.7pp,
CT_PEAKER -8.76 TWh / -1.1pp). The P2 commitment screen is off the table (user
decision) and the offer-multiplier axis is exhausted: run-74 proved offer moves
shift all three years uniformly (CC -4.4 TWh in each) and cannot close a
2024-concentrated gap. Both new levers are measured quantities that regenerate
for a forward year and respond to changed conditions (CLAUDE.md #12/#13) — no
residual fitting, no actuals pinning.

1. **CT_PEAKER net-load deployment drag** (``ct_netload_drag``) — the
   forward-native mechanism already validated as the ERCOT keeper
   (2026-07-01-24-ct-drag-v1, docs/ercot-ct-netload-drag-2026-06.md) and the
   CAISO keeper default: a per-hour min-gen floor
   ``clip(slope*netload_GW + intercept, 0, cap)`` on the non-``_peak``
   CT_PEAKER tranches, gated to the afternoon-evening ramp h[15,22), over
   which the LP dispatches economically. It represents the AS/RUC deployment
   energy the merit order can't see — exactly the diagnosed PJM CT gap (the
   real fleet runs deployment energy the model's top-of-merit CT offer never
   clears). PJM coefficients derived the same way ERCOT's/CAISO's were
   (scripts/derive_pjm_ct_netload_drag.py): measured CAMPD pure-play
   CT_PEAKER ramp-window capacity factor regressed on EIA-930 PJM net-load
   (UTC-5 aligned), 2023-2025, Spearman rho 0.50/0.51/0.60 and year-stable.
   PJM's CF-vs-net-load curve is two-regime (flat economic-peaking base below
   ~90 GW, linear reliability-deployment rise above), so the fit is the
   clipped line itself (hinge SSE over the binned medians, 0.133 vs 0.176 for
   the ERCOT-recipe unclipped line): slope 0.01108/GW, intercept -0.9987,
   cap 0.46, zero-crossing 90.1 GW. Floor energy 4.70/6.29/7.16 TWh
   (2023/24/25) — NOT year-uniform (rises with the tighter 2024/2025
   net-load), the property the offer axis lacked; floored-total overshoots
   measured by only +4/+7/+5% (ERCOT keeper: +6-8%).

2. **CC demonstrated-peak cap** (``cc_capacity_reconcile`` with the new
   mode="cap" rows, pjm-cc-overgen-recommendation Rank 4, targets Miss #2 —
   the 95-100% CF pile): a CC_REGULAR plant's LP capacity is bounded at
   min(model nameplate, CAMPD demonstrated sustained max = p99.9 of net MW
   pooled 2023-2025), applied only where nameplate exceeds the demonstrated
   peak by >1.1x (scripts/derive_cc_capacity_reconcile.py --iso PJM --mode
   cap). 17 plants capped, -2,686 MW of phantom top-band capacity; EIA-860
   winter ratings independently corroborate most caps (Key 774 vs winter 778,
   Camden 139 vs 145, Ontelaunee 590 vs 591). Three candidates (Hunterstown,
   Ironwood, Allegheny 3-4-5) are excluded by a cross-source feasibility
   guard — their EIA-923 annual net generation is infeasible at the CAMPD
   peak (implied CF up to 1.27), so their CEMS series understate the plant
   (CLAUDE.md #13 misalignment exception). Binds hardest in high-CF hours,
   so it is NOT year-uniform either. Measured capability/availability, not
   generation pinning: the cap regenerates from rolling CEMS history and a
   changed forward fleet would re-derive it.

Deliberately NOT included:
- ``cc_peaking_per_plant``: PJM already defaults ``cc_duct_peaking=True``
  (measured per-plant EIA-860 duct-burner shares supersede the class-wide
  8.0% estimate for every mapped plant, cap 18 via curve_smoothing), and the
  duct map takes precedence over the thermal-tranche artifact in
  bins_to_fleet — enabling it would touch only unmapped plants, a murky
  interaction for no measured gain.
- ``ct_deployment_overlay``: pins measured CEMS out-of-merit deployment
  energy (backcast-only, no forward analogue) — inadmissible for a keeper
  where the net-load drag provides the forward-native equivalent.
- Scarcity adders / ORDC overlays / tail work: C3c stays blocked on the
  per-gen reserve thread (docs/multi-iso/pjm-reserve-ordc.md).

Everything else pjm-74 verbatim: CC_REGULAR econ_low 1.00 + CT_PEAKER
econ_high 1.27 (Manual-15-grounded, imported), coal_bit floor 0.65 sigmoid,
reserve co-opt ON, historic outages, zonal gas basis, congestion, priced
interchange, seam caps, hydro/BTM backfill 2024, commitment=False.

Predicted signs (stated BEFORE solving; keep structurally-correct mechanisms
even where a residual worsens):
- CT_PEAKER UP all years, most in 2024/2025 (floor energy 4.7/6.3/7.2 TWh,
  partially overlapping hours the LP already dispatches) — targets the 2024
  -8.76 TWh under-run.
- CC_REGULAR DOWN all years: the cap removes phantom high-CF capacity and
  the CT floor displaces marginal CC in ramp hours — targets the 2024 +16.57
  over-run. 2023 CC (-6.71 under) will get MORE negative — accepted: the cap
  is measured capability, and the 2023 under-run's root cause is elsewhere
  (per rule #1/#11, do not reject a real mechanism on a residual).
- Coal UP slightly (freed mid-merit energy; 2024 had headroom).
- Prices: hours where the floor binds reprice DOWN slightly (floored MW is
  out-of-merit supply), so C3a (already -8.7%/-14.1% under) may worsen
  slightly — accepted for the same reason; C3c unchanged (tail out of scope).
- C2 2025 gas share DOWN toward benchmark (CC down more than CT up).
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
    PRB_OVERRIDES,
)
from scripts.run_pjm74_cc_ct_rebalance import (  # noqa: E402
    BIT_OVERRIDES,
    OFFER_CURVE_OVERRIDES,
)

# PJM CT_PEAKER net-load deployment-drag curve, regressed from measured CAMPD
# pure-play CT CF on EIA-930 PJM net-load, ramp window h[15,22) local standard,
# 2023-2025 pooled (scripts/derive_pjm_ct_netload_drag.py — do NOT reuse the
# ERCOT 0.00703/-0.1427/0.47 or CAISO 0.00901/-0.1124/0.36 coefficients).
CT_DRAG_OVERRIDES = {
    "ct_drag_slope_per_gw": 0.01108,  # CF per GW net-load, hinge fit
    "ct_drag_intercept": -0.9987,  # zero-crossing ~90.1 GW
    "ct_drag_cap": 0.46,  # 95th-pct ramp-window CF
    "ct_drag_ramp_start": 15,  # ramp window [15, 22) local standard,
    "ct_drag_ramp_end": 22,  # same window as the ERCOT/CAISO keepers
}

# Generic ScenarioConfig override channel (prb_overrides): the pjm-61 PRB
# sigmoid params plus the CC demonstrated-peak cap artifact
# (scripts/derive_cc_capacity_reconcile.py --iso PJM --mode cap; mode="cap"
# rows apply min() in fleet._reconcile_cc_capacity via fleet_to_bins).
CONFIG_OVERRIDES = {
    **PRB_OVERRIDES,
    "cc_capacity_reconcile": True,
    "cc_capacity_reconcile_path": str(
        _REPO / "data/raw/_processed-legacy/cc_capacity_reconcile_PJM.csv"
    ),
}


def main() -> int:
    out_dir = Path("results/calibration/pjm75_ct_drag_cc_cap")
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
            "PJM 75 CT net-load deployment drag + CC demonstrated-peak cap. "
            "CT_PEAKER min-gen floor clip(0.01108*netGW - 0.9987, 0, 0.46) in "
            "ramp h[15,22) — measured CAMPD CT CF vs EIA-930 net-load "
            "(derive_pjm_ct_netload_drag.py), the ERCOT/CAISO keeper "
            "mechanism with PJM-fit hinge coefficients; forward-native "
            "replacement for the diagnosed AS/RUC deployment energy. CC "
            "capacity capped at CAMPD demonstrated sustained max (p99.9, "
            "2023-25) for 17 plants whose nameplate exceeds it >1.1x "
            "(-2686 MW phantom top-band; derive_cc_capacity_reconcile.py "
            "--iso PJM --mode cap, EIA-923 feasibility-guarded). All else "
            "pjm-74 verbatim (M15 offer moves, coal_bit floor 0.65, reserve "
            "co-opt ON, commitment=False)."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
