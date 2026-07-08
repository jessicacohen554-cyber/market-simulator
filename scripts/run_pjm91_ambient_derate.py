"""Driver: PJM 91 — GT ambient-temperature capacity derate on the pjm-90 recipe.

Owner hypothesis (2026-07-08): the model overstates summer-peak AVAILABLE
capacity, so the LP never climbs the supply curve into scarcity (C3c: 2025
model 0h >$200 vs DA actual 51h) and CCGTs over-run (C1: CC_REGULAR +13 TWh).

Diagnostic finding (scripts/probes/_pjm_summer_capacity_diag.py): in the top
summer net-load hours the model carries 8-11 GW of thermal headroom over
net-load at the absolute peak (reserve margin 8.7-30%), while the measured PJM
Primary reserve requirement is only ~2 GW — so the energy+reserve co-opt's ORDC
step is nowhere near binding. Two capacity leaks were investigated:

  * Issue B (missing retirements/mothballs): RULED OUT. The within-window
    retiree intake (7.3 GW fossil through 2024) + COD ramp already remove real
    retirements; the 2024 EIA-923 zero-gen fossils are small old oil/gas
    peakers (legitimate economic-idle deep-peak reserve — the scarcity tranche,
    NOT phantom, rule 11); the 2025 zero-gen list is a partial-923-release
    artifact.
  * Issue A (ambient derate): the EIA-860 net-summer rating (already applied to
    CC/CT in summer) IS the summer-peak-condition rating, so the physically-
    correct INCREMENTAL derate for hours hotter than that rating point is small
    (~0.3 GW at peak). This driver adds that structurally-correct increment
    (config.gt_ambient_derate) — a physics slope x measured hourly zone tmax,
    forward-reproducible (rule 11) — but does NOT crank it to force the tail
    (that would pin to the residual, rule 11). It is a correct-structure
    improvement (rule 1), not a scarcity manufacturing device.

Everything else is the pjm-90 recipe VERBATIM. Full span 2023-2025 one bundle
(rule 16), years sequential (rule 1/12). MEMORY: MALLOC_ARENA_MAX=2.
"""

from __future__ import annotations

import argparse
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
from scripts.run_pjm90_cchp_srmc import _OFFER_OVERRIDES  # noqa: E402

NOTE = (
    "PJM 91 GT ambient-temperature capacity derate on the pjm-90 recipe: adds "
    "config.gt_ambient_derate (CC 0.4 %/C, CT 0.6 %/C above a 35 C net-summer "
    "reference, applied to measured hourly zone tmax) — the physically-correct "
    "incremental hot-hour derate the EIA-860 net-summer rating does not capture. "
    "Rule-11 physical input (physics slope x measured temperature), forward-"
    "reproducible; NOT tuned to the price residual. Diagnostic showed the summer "
    "capacity is NOT materially overstated vs the measured net-summer rating "
    "(incremental derate ~0.3 GW at peak) and no phantom retirements — so this "
    "is a correct-structure improvement, not a scarcity-manufacturing lever. "
    "Otherwise the pjm-90 recipe verbatim."
)


def _solve(years: list[int], out_dir: Path, **extra):
    """Solve PJM for ``years`` with the pjm-90 recipe + GT ambient derate."""
    reference = _load_reference()
    return solve_and_persist(
        years,
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
        offer_curve_overrides=_OFFER_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 18.0,
            "offer_curve_smoothing_mid": 0.35,
        },
        energy_reserve_coopt=True,
        pjm_reserve_supply_cap=True,
        ct_netload_drag=True,
        ct_drag_overrides=CT_DRAG_OVERRIDES,
        gt_ambient_derate=True,
        **extra,
    )


def main() -> int:
    """CLI: solve ``--years`` into ``--out-dir`` (or ``--report-only``)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--out-dir", type=Path, default=Path("results/calibration/pjm91_ambient_derate")
    )
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    if not args.report_only:
        _solve(args.years, args.out_dir, note=NOTE)
    report_run(args.out_dir, band_width=0.10)
    print(f"DONE: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
