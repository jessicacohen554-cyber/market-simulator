"""Driver: PJM 76 — per-generator reserve co-optimization (R[g] ≤ ramp10[g]).

The Phase-2 build of docs/multi-iso/pjm-reserve-ordc.md, targeting the
residuals the pjm-75 attestation diagnosed as one root cause — the missing
per-gen reserve competition (2024 CC_REGULAR +8.85 TWh over, C3a 2024 −8.1% /
2025 −13.4% price under, C3c 0 tail hours vs 6/18/59): reserve must compete
with energy ON THE SAME MARGINAL UNIT for the balance dual to carry a
sub-shortage opportunity cost into the LMP. The zone-aggregate co-opt in the
keeper (energy_reserve_coopt + pjm_reserve_supply_cap) honestly clears
reserve_price=$0 in all 8,760 h of every year — pooled deliverable headroom
(Σ ramp10 ≈ 50 GW) sits ~15× above the ~3.4 GW measured Primary requirement,
so the published vertical ORDC step never fires (pjm-62 empirical re-gate).

New lever (``pjm_reserve_pergen``, dispatch._build_reserve_rows_pergen) —
pure structure, zero fitted parameters (CLAUDE.md #12 admissible):

* One reserve column R[r,t] per reserve-providing ASSET, memory-tiered to
  the binding geography (2026-07-02 memtests: per-tranche 2,624 R columns
  OOM'd the 15 GB box at ~15.9 GB; plant-level everywhere, 448 columns, at
  ~15.1 — the HiGHS solve workspace scales with the joint-row count):
  INSIDE the MAD subzone one column per (plant, fuel-class, zone) — tranches
  dispatch bang-bang so headroom/ramp are plant properties (the
  pjm_online_reserve doctrine); OUTSIDE MAD one column per (zone, fuel-
  class) — coarser pooling on the side where no locational requirement
  binds, still competing with that zone-class's energy at its margin.
  R[r] ≤ Σ FleetArrays.ramp10 = RAMP10_FRAC_BY_GROUP × pmax (NREL/
  TP-5500-55588 App. H class ramp rates: coal 0.15, CC 0.40, CT/oil 1.00,
  gas-ST 0.20 — regenerates for a forecast fleet). Same ramp physics at
  every tier; never a breakpoint/penalty change.
* Joint headroom Σ_members P[g,t] + R[r,t] ≤ Σ pmax·availability per
  asset-hour: a MW held as reserve cannot clear as energy, so a loaded
  marginal plant's forgone margin IS the reserve price (the $75–200
  opportunity-cost band mechanism).
* TWO nested measured balance families (Manual 11 sec 4.2): the RTO Reserve
  Zone (measured pr_req_mw, mean 3.09/3.42/3.35 GW 2023/24/25) and the
  Mid-Atlantic/Dominion Reserve Subzone (measured mad_pr_req_mw, mean
  2.55/2.56/2.60 GW; model zones Central_PA/Dominion/EMAAC/SWMAAC — EKPC
  misalignment documented in reserve_config.PJM_MAD_ZONES). Both requirements
  are measured *reliability* quantities from PJM Data Miner reserve-market
  results (scripts/build_pjm_as_withholding.py), with the published two-step
  ORDC ($850/$300/+190 MW, Manual 11 sec 4.3.3) pricing shortfalls. Forward
  analogue exists (1.5×MSSC Manual-11 rule), so the measured RHS passes the
  rule-#12 admissibility test.
* Supersedes the zone-aggregate supply cap (pjm_reserve_supply_cap stays in
  the recipe; reserve_config._pjm_design's pergen branch never computes it).

NOT included (scope guard): no scarcity adders / post-solve ORDC overlays, no
breakpoint lowering or penalty inflation (the curve is the published CSV
verbatim), no ct_mustrun_per_plant / ct_deployment_overlay, no offer-
multiplier retouch, commitment=False unchanged. The Phase-1 commitment
posture (the second diagnosed root-cause leg) remains off the table per the
standing user decision, so the opportunity-cost band is expected only where
the LP is ALREADY tight on deliverable marginal headroom.

Everything else pjm-75 verbatim: CT net-load deployment drag (PJM hinge
clip(0.01108·netGW − 0.9987, 0, 0.46), h[15,22)), CC demonstrated-peak cap
(17 plants −2,686 MW, mode=cap), pjm-61 PRB_OVERRIDES + pjm-74
OFFER_CURVE_OVERRIDES + coal_bit floor 0.65, historic outages, zonal gas
basis, congestion, priced interchange, seam caps, hydro/BTM backfill 2024.

Predicted signs (stated BEFORE solving; structurally-correct mechanisms stay
even where a residual worsens, CLAUDE.md #1/#11):

- reserve_price: nonzero in a MINORITY of hours only — tight ramp-window
  hours where deliverable marginal headroom thins (the bind-gate probe found
  ~16–49 h/yr under the online+deliverable measure) plus MAD-local binds the
  RTO aggregate never saw; $0 elsewhere (idle quick-start CT ramp legitimately
  backs Primary at no opportunity cost). An honest mostly-$0 outcome with a
  priced tail is the expected result, NOT a failure.
- C3c tail hours: UP from 0 toward the benchmark 6/18/59 — the reserve dual
  adds into the LMP exactly in the hours PJM's tail lives.
- C3a avg LMP: UP slightly (2024 −8.1% / 2025 −13.4% under-runs shrink) —
  bounded by the few binding hours.
- C1 2024 CC_REGULAR (+8.85 over): DOWN slightly — holding R on loaded
  marginal CCs backs their energy down in binding hours; CT_PEAKER: UP
  slightly (displacement + shortfall-priced hours dispatch peakers).
- C1 2023 CC (−14.54 under): roughly unchanged (the reserve bind is rare in
  the soft 2023 year); the 2023 root cause is a separate thread.
- C2 2025 gas/coal shares: second-order (≤ a few tenths of a pp).

Memory: the 2024 single-year probe (scripts/probes/_pjm76_pergen_memtest.py)
gates the 3-year run per CLAUDE.md #45 — record its peak RSS in the session
log before launching this driver. Years run SEQUENTIALLY in one invocation.
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
    out_dir = Path("results/calibration/pjm76_pergen_reserve")
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
        pjm_reserve_pergen=True,
        ct_netload_drag=True,
        ct_drag_overrides=CT_DRAG_OVERRIDES,
        note=(
            "PJM 76 per-gen reserve co-opt: R[j,t] per reserve-eligible unit "
            "(ramp10>0), R <= FleetArrays.ramp10 (NREL class ramp rates), "
            "joint P+R <= pmax*avail per unit-hour, nested measured RTO "
            "(pr_req_mw) + Mid-Atlantic/Dominion (mad_pr_req_mw) Primary "
            "balance families priced by the published $850/$300/+190 ORDC "
            "(Manual 11 sec 4.2/4.3.3) — reserve competes with energy on the "
            "same marginal unit, so the balance dual carries the sub-shortage "
            "opportunity cost into the LMP endogenously. Zero fitted params; "
            "supersedes the zone-aggregate supply cap. All else pjm-75 "
            "verbatim (CT net-load drag, CC demonstrated-peak cap, M15 offer "
            "moves, coal_bit floor 0.65, commitment=False)."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
