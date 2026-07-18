"""Driver: PJM 89 — steam-gas overnight drag + CHP HR + outage-capture keeper candidate.

The pjm-83 keeper recipe (``run_pjm86_pjm83_head_baseline._solve`` — itself
``run_pjm80_srmc_reground_keeper`` re-solved at HEAD), re-solved on the current
data tree so it absorbs FOUR structural corrections landed on this branch — all
of which live in base config / base data, so the *recipe* (flags + the shared
override dicts imported below) is byte-unchanged and every delta vs pjm-83 is one
of these mechanisms:

1. **ST_GAS extreme-day overnight drag** (headline). Within the
   ``reliability_floor`` engine, PJM ST_GAS carries overnight-windowed [0,6]
   tmax/tmin/netload limbs at its min-must-run level: on an extreme-temperature
   or high-net-load day the boiler is held warm at min-stable overnight to ramp
   for the next peak instead of cycling off. 7 limbs enabled where real;
   forced-energy 3.4-6.1% (rule 20). Replaces the old all-day limbs (rule 14).
2. **CHP steam-credit power-only HR correction** extended to PJM: CC_CHP/CT_CHP
   no longer clear on physically-impossible ~5-6 MMBtu/MWh steam-credited HRs and
   over-deliver +52-67% vs 923.
3. **Outage capture**: FULL_STOP_OVERRIDE_DAYS 14->5 (5-13 d PRB dead stops) +
   orphaned gross-blank ST_CHP steam-host boilers (Grays Ferry).
4. **Coal-bit econ-high** held at the keeper's 1.2664 (the base default bump to
   0.90 is deep-merged over by OFFER_CURVE_OVERRIDES['COAL_BIT']).

Memory note: PJM's per-plant multi-zone energy+reserve co-opt LP peaks ~14-16 GB
per year; on a <=15 GB host, solving all three years in ONE process OOMs on the
2nd year because CPython does not fully return freed heap to the OS between
years. So this driver takes ``--years`` and is meant to be run ONCE PER YEAR in a
fresh process into the SAME ``--out-dir`` (each year persists its own
``dispatch/<year>_P1.parquet`` + ``floors/`` + meta), then scored over the full
bundle with ``--report-only``. Full span 2023-2025 (rule 16), years sequential
(rule 1/12).
"""

from __future__ import annotations

import argparse
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
    "PJM 89 steam-gas overnight drag keeper candidate: pjm-83 recipe re-solved "
    "at HEAD, absorbing four base-config/base-data corrections vs pjm-83 - "
    "(1) ST_GAS extreme-day overnight [0,6] drag in the reliability_floor engine "
    "(tmax/tmin/netload, min-stable, 7 limbs, forced-energy 3.4-6.1%), (2) CHP "
    "steam-credit power-only HR correction extended to PJM, (3) PRB 5-13d "
    "dead-stop + orphaned ST_CHP steam-boiler outage capture, (4) coal-bit "
    "econ-high held at the keeper's 1.2664. Recipe byte-unchanged; every delta "
    "vs pjm-83 is one of these four structural mechanisms."
)


def _solve(years: list[int], out_dir: Path, **extra):
    """Solve PJM for ``years`` with the pjm-83 keeper recipe (imported overrides).

    Mirrors ``run_pjm86_pjm83_head_baseline._solve`` exactly; only the ``years``
    list is parameterized so each year can run in a fresh (memory-clean) process.
    """
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
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 18.0,
            "offer_curve_smoothing_mid": 0.35,
        },
        energy_reserve_coopt=True,
        pjm_reserve_supply_cap=True,
        ct_netload_drag=True,
        ct_drag_overrides=CT_DRAG_OVERRIDES,
        **extra,
    )


def main() -> int:
    """CLI: solve the given ``--years`` into ``--out-dir`` (or ``--report-only``)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("results/calibration/pjm89_steamgas_drag"),
    )
    ap.add_argument(
        "--report-only",
        action="store_true",
        help="Skip solving; just score the existing bundle over all years.",
    )
    args = ap.parse_args()

    if not args.report_only:
        _solve(args.years, args.out_dir, note=NOTE)
    report_run(args.out_dir, band_width=0.10)
    print(f"DONE: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
