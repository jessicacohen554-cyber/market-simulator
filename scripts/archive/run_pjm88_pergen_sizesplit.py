"""Driver: PJM 88 — size-split pergen pooling tier (pjm-87 diagnosis remedy).

The pjm-87 per-gen opportunity-cost recipe VERBATIM (`run_pjm87_pergen_oppcost`
`_solve` kwargs) + `pjm_reserve_pergen_size_split=True` (**new**): a diagnosis
(fleet-reconstruction probe, no re-solve — the owner-requested investigation
into why pjm-87's magnitude clustered in $0-10 instead of the targeted $10-80
opportunity-cost band) found that none of the 4 measured balance rows
(Primary/Synchronized x RTO/MAD) ever came close to binding — 8-14x supply
margin at the tightest hour of all 3 years. The observed duals came from the
per-POOL joint headroom row instead (energy competing with reserve for one
pool's capacity), and with only 39 uniform (zone, fuel-class) pools the LP can
almost always source PJM's small measured requirement from an idle pool even
when one specific dominant plant is fully energy-loaded — diluting the
opportunity-cost signal.

`pjm_reserve_pergen_size_split` splits each base pool's plants whose capacity
exceeds `PJM_PERGEN_SIZE_SPLIT_MEAN_MULTIPLE` (2.0x) times the pool's own mean
plant capacity into individual reserve columns; smaller plants stay pooled
together exactly as the base tier. Self-normalizing threshold (no absolute MW
cutoff — a granularity/LP-structure choice, not a fitted price parameter,
rule 5). Measured on the real PJM fleet: 95 pools / 190 sync-split R columns
(vs the base 39 pools / 78 columns) — a deliberate middle ground short of the
memory-infeasible full per-plant tier (407 pools / 814 columns, ~10x the base
tier, beyond the documented 2026-07-02 P1 OOM precedent at a smaller column
count). Reserve-block construction alone profiled at ~1.5 GB peak (cheap);
the real risk is the SOLVE's basis-factorization memory, untested at this
scale before this run — the base 39-pool sync tier already solves at ~15.3 GB
(near the box ceiling even with the 6 GB swap net barely touched), and this
tier's reserve block is ~2.3x more rows, so this run carries real OOM risk
(owner-accepted, per the size-split-tier decision).

Published two-step ORDC unchanged; Synchronized rows read from the same cited
curve CSV — no breakpoint/penalty edit (rule 11). No MIP; P1 stays the scored
pass (cold, same as pjm-87 — the sync-cap kwargs override precludes warm
start). Memory: G-40 subset-build pattern; this run itself IS the profiling
step for the size-split tier at real scale (a smaller synthetic/reserve-block-
only profile already ran — see the session's memory probes).

A/B partners: `pjm86_pjm83_head_baseline` (flags off) and `pjm87_pergen_oppcost`
(size-split OFF, sync ON) — isolates the size-split tier's single-mechanism
effect vs pjm-87. Full span 2023-2025 in one bundle (rule 16), years
sequential (rule 12). Registered per rule 15 whatever the outcome.
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
    "PJM 88 size-split pergen pooling tier (pjm-87 diagnosis remedy): "
    "pjm-87 recipe VERBATIM + pjm_reserve_pergen_size_split (NEW: splits "
    "each base (zone, fuel-class) pool's plants above 2.0x the pool's own "
    "mean plant capacity into individual reserve columns -- self-"
    "normalizing threshold, no absolute MW cutoff -- 95 pools / 190 "
    "sync-split R columns vs the base 39/78; a middle ground short of the "
    "memory-infeasible full per-plant tier, 407 pools / 814 columns). "
    "Diagnosis: none of the 4 balance rows ever bind (8-14x margin at the "
    "tightest hour of 3 years); duals come from the per-pool joint headroom "
    "row, diluted by 39 uniform pools letting the LP source PJM's small "
    "requirement from any idle pool. Wanted: sharper opportunity-cost "
    "pricing (more $10-80 hours, fewer $0-10) by concentrating granularity "
    "on individually-dominant plants. Real OOM risk untested at this scale "
    "-- owner-accepted per the size-split-tier decision."
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
        pjm_reserve_pergen=True,
        pjm_reserve_pergen_sync=True,
        # --- size-split delta vs pjm-87 ---
        pjm_reserve_pergen_size_split=True,
        measured_ramp_capability=True,
        ct_netload_drag=True,
        ct_drag_overrides=CT_DRAG_OVERRIDES,
        **extra,
    )


def main() -> int:
    out_dir = Path("results/calibration/pjm88_pergen_sizesplit")
    run_dir = _solve(out_dir, note=NOTE)
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
