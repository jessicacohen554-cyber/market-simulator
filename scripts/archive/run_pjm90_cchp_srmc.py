"""Driver: PJM 90 — CC_CHP SRMC re-grounding on top of the pjm-89 steam-gas drag.

pjm-89 (steam-gas overnight drag + CHP HR + outage capture) left one open
residual: CC_CHP grid generation ~+50% over EIA-923 net-to-grid. The measured
diagnosis (agent, 2026-07-08) showed this is NOT a behind-the-meter capacity
problem — the merchant 35% BTM default is already the correct average host share
(net-to-grid / gross = 0.63-0.68) — but an OVER-DISPATCH problem: the CC_CHP grid
tranches run ~48% CF vs the measured net-to-grid ~29% because they bid BELOW
true power-only cost. The keeper's own pjm-79 SRMC re-grounding already fixed
this for every other class ("a sub-SRMC offer is not real", Manual-15
composite-cost floor: ST_GAS/CT_INTERMEDIATE -> 1.0x) but SKIPPED CC_CHP, which
stayed at committed/econ_low/econ_high 0.6624/0.684/0.8208 — the sub-SRMC
outlier. The steam credit belongs to the host (already removed by the BTM
netting), so the GRID-delivered MWh must bid at its power-only cost.

This re-grounds CC_CHP to the composite-cost floor (committed/econ_low/econ_high
0.6624/0.684/0.8208 -> 1.0/1.0/1.05, peak 1.62 unchanged), mirroring the pjm-79
treatment of ST_GAS/CT_INTERMEDIATE. Correct offer physics (rule 1), registered
offer_curve_by_group channel (rule 25) — not a residual-fitted adder. The CC_CHP
must-run steam floor (chp_grid_pmin) is untouched, so the host-steam obligation
still runs; only the ABOVE-floor economic grid delivery is priced at true cost.

Everything else is the pjm-89 recipe VERBATIM (which is pjm-83 re-solved at HEAD
with the four steam-gas corrections). Full span 2023-2025 one bundle (rule 16),
years sequential (rule 1/12). MEMORY: run with MALLOC_ARENA_MAX=2 (one process,
~12.7 GB peak; without it the 2nd year OOMs on a 15 GB host).
"""

from __future__ import annotations

import argparse
import copy
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

# Deep-copy the shared pjm-79 override dict and re-ground ONLY CC_CHP to the
# Manual-15 composite-cost floor (the sub-SRMC outlier the re-grounding missed).
# Deep-copy so the shared module dict other drivers import is never mutated.
_OFFER_OVERRIDES = copy.deepcopy(OFFER_CURVE_OVERRIDES)
_OFFER_OVERRIDES["CC_CHP"] = {
    "committed": 1.0,  # was 0.6624 — no economic tranche below power-only SRMC
    "econ_low": 1.0,  # was 0.684
    "econ_high": 1.05,  # was 0.8208 — slight rising band (cf. CT_INTERMEDIATE 1.08)
    "peak": 1.62,  # unchanged
    "econ_low_share": 0.5,
    "pct_peaking": 8.0,
}

NOTE = (
    "PJM 90 CC_CHP SRMC re-grounding on the pjm-89 steam-gas-drag recipe: CC_CHP "
    "committed/econ_low/econ_high 0.6624/0.684/0.8208 -> 1.0/1.0/1.05 (Manual-15 "
    "composite-cost floor, the pjm-79 sub-SRMC re-grounding CC_CHP had been left "
    "out of). Measured diagnosis: CC_CHP over-DISPATCHES (grid CF ~48% vs "
    "measured net-to-grid ~29%) because it bid below power-only cost, not a BTM "
    "capacity issue (merchant 35% BTM is already the correct host share). The "
    "steam credit is the host's (BTM-removed), so the grid MWh bids at true "
    "power-only cost; the CC_CHP must-run steam floor is untouched. Rule 1 "
    "correct offer physics, registered channel. Otherwise the pjm-89 recipe "
    "verbatim (steam-gas overnight drag + CHP HR + outage capture)."
)


def _solve(years: list[int], out_dir: Path, **extra):
    """Solve PJM for ``years`` with the pjm-89 recipe + CC_CHP SRMC re-grounding."""
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
        **extra,
    )


def main() -> int:
    """CLI: solve ``--years`` into ``--out-dir`` (or ``--report-only``)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--out-dir", type=Path, default=Path("results/calibration/pjm90_cchp_srmc")
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
