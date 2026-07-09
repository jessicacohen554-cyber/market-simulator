"""Driver: PJM 94 — all-hours ST_GAS net-load reliability-commitment drag.

Resolves root-cause issue #1483 / gap-register G-21 on top of the pjm-90 keeper
(CC_CHP SRMC re-grounding on the pjm-89 steam-gas overnight-drag recipe). The
pjm-83→90 keeper line deliberately DE-FLOODED ST_GAS — it removed a fake
sub-SRMC offer band (not real physics) and accepted the resulting underrun as a
disclosed, tracked tradeoff (#1483) pending the real forward-native driver. This
driver supplies that driver.

**Diagnosis (CAMPD, 9 pure-play PJM ST_GAS plants, 7.71 GW; scripts/
diag_pjm_stgas_operation.py + derive_pjm_st_gas_netload_drag.py):** the legacy
gas-steam fleet (Marcellus-belt coal-to-gas conversions Brunner Island /
Montour / Martins Creek / Shawville / New Castle + Chalk Point) runs 8.1 / 13.0 /
15.0 TWh (2023/24/25) while the pjm-90 keeper clears only 5.1 / 4.4 / 7.4 — and
CC_REGULAR over-runs by nearly the same amount (2024 ST_GAS −8.0 TWh /
CC_REGULAR +13.5 TWh). The fleet is online 293/299/337 of 365 days with
run-lengths of weeks-to-months, NOT temperature events: only 9–19% of its energy
falls on temperature-flagged days, so the pjm-89 overnight [0,6] temperature/
netload floor (which forces ~0.3 TWh) structurally cannot capture it. The
measured operating rule is an all-hours commitment whose level rises with system
net-load (overnight low-price CF regressed on EIA-930 PJM net-load: Spearman
rho 0.32→0.52, year-stable; flat across overnight/midday/ramp at a given
net-load = around-the-clock, not peaker-shaped).

**Mechanism.** Enable the all-hours ST_GAS net-load drag
(``fleet.apply_gas_st_netload_drag_floor``) — a min-gen FLOOR (offers and prices
untouched; the LP dispatches economically above it) of
``clip(slope·netGW + intercept, 0, cap) × available capacity``, keyed to system
net-load. This is the SAME mechanism the ERCOT and NEISO keepers use — NOT the
fake sub-SRMC band #1483 warned against — and is admissible in backcast AND
forecast (CLAUDE.md #10/#13): both the trigger (net-load, from a load forecast +
VRE build) and the magnitude (physical min-gen) regenerate for a forward year
and respond to changed conditions. Rule 19: turning the drag on drops the pjm-89
overnight h0-6 ST_GAS reliability-floor limbs via
``drop_drag_owned_reliability_specs`` (run_year), so the two do not stack.

**Coefficients (rule 25 — a curve fitted on one ISO's residual is that ISO's; do
NOT reuse ERCOT's 0.00906 / -0.1376 / 0.34):** PJM's OWN hinge, fit by
``scripts/derive_pjm_st_gas_netload_drag.py`` from the measured overnight
(low-price, non-economic) CF vs EIA-930 PJM net-load, 2023-2025 — slope 0.01029,
intercept -0.7263, cap 0.39, zero-crossing 70.6 GW. Zero parameters fitted to a
price or volume residual (rule 11); re-derives only when CAMPD/EIA-930 source
data update (rule 23). The floor lands ST_GAS at ~9.9/11.1/12.4 TWh (vs measured
8.1/13.0/15.0) — a commitment level from the operating rule, not a volume pin.

Everything else is the pjm-90 recipe VERBATIM. Full span 2023-2025 one bundle
(rule 16), years sequential (rule 1/12). MEMORY: run with MALLOC_ARENA_MAX=2
(one process, ~12.7 GB peak; without it the 2nd year OOMs on a 15 GB host).
"""

from __future__ import annotations

import argparse
import copy
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

# pjm-90 CC_CHP SRMC re-grounding (verbatim): deep-copy the shared pjm-79
# override dict and re-ground ONLY CC_CHP to the Manual-15 composite-cost floor.
_OFFER_OVERRIDES = copy.deepcopy(OFFER_CURVE_OVERRIDES)
_OFFER_OVERRIDES["CC_CHP"] = {
    "committed": 1.0,
    "econ_low": 1.0,
    "econ_high": 1.05,
    "peak": 1.62,
    "econ_low_share": 0.5,
    "pct_peaking": 8.0,
}

# PJM's OWN ST_GAS net-load drag hinge (rule 25) — measured overnight CF vs
# EIA-930 PJM net-load, 2023-2025 (scripts/derive_pjm_st_gas_netload_drag.py).
# Overrides the ScenarioConfig ERCOT defaults (0.00906 / -0.1376 / 0.34) for
# this run and is recorded verbatim in run_config.json (rule 24).
GAS_ST_DRAG_OVERRIDES = {
    "gas_st_drag_slope_per_gw": 0.01029,
    "gas_st_drag_intercept": -0.7263,
    "gas_st_drag_cap": 0.39,
}

NOTE = (
    "PJM 94 all-hours ST_GAS net-load reliability-commitment drag on the pjm-90 "
    "recipe (resolves #1483 / G-21). Enables gas_st_netload_drag with PJM's own "
    "hinge clip(0.01029*netGW - 0.7263, 0, 0.39) fit from measured overnight CF "
    "vs EIA-930 PJM net-load (derive_pjm_st_gas_netload_drag.py; rule 25 PJM-own "
    "coeffs, rule 11 zero residual-fit). A min-gen FLOOR (offers/prices "
    "untouched) keyed to net-load — the ERCOT/NEISO keeper mechanism, NOT the "
    "fake sub-SRMC band #1483 warned against; forward-native (#10/#13). Rule 19 "
    "drops the pjm-89 overnight h0-6 ST_GAS reliability limbs (no stacking). "
    "Diagnosis: measured ST_GAS 8.1/13.0/15.0 TWh vs pjm-90 5.1/4.4/7.4, fleet "
    "online 293-337/365 days (weeks-to-months run-lengths, only 9-19% of energy "
    "on temp-flagged days). Otherwise pjm-90 verbatim."
)


def _solve(years: list[int], out_dir: Path, **extra):
    """Solve PJM for ``years`` with the pjm-90 recipe + all-hours ST_GAS drag."""
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
        gas_st_netload_drag=True,
        gas_st_drag_overrides=GAS_ST_DRAG_OVERRIDES,
        **extra,
    )


def main() -> int:
    """CLI: solve ``--years`` into ``--out-dir`` (or ``--report-only``)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("results/calibration/pjm94_stgas_netload_drag"),
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
