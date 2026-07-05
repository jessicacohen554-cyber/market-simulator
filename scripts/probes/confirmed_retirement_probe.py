"""Diagnostic probe: does the economic screen retire near-term announced units?

Evidence harness for docs/handoffs/confirmed-retirement-plan-2026-07.md §3 (W0-P2)
and the W2-P2 verification step (§8 item 7 there). Runs a short forecast
(START_YEAR..--end-year) for one ISO with the default ScenarioConfig,
instrumenting capacity-evolution so every confirmed/announced/economic
retirement decision is recorded per year, plus per-unit loss counters and the
survival of the EIA-860 2026-2028 planned-retirement plants. Pure diagnostic —
never registered on the dashboard; touches nothing in src/.

Usage:
    python scripts/probes/confirmed_retirement_probe.py \\
        --iso ERCOT --end-year 2029 --out /tmp/ercot_probe.json
    # with the confirmed-exit injector on (W2-P2 verification):
    python scripts/probes/confirmed_retirement_probe.py \\
        --iso PJM --end-year 2029 --confirmed-exits --out /tmp/pjm_probe.json

2026-07-05 findings (plan §3): zero economic retirements through 2029 in both
ERCOT (reliability floor in permanent ~20 GW deficit rescues every eligible
unit) and PJM (capacity revenue + low FOM bars leave 2 of 1,387 units with any
loss year); binned thermal plants carry retirement_year=None (bins_to_fleet
drops announced dates), so the date-based step is a no-op for them regardless
of the fossil exemption.
"""

from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path

import market_sim.model.capacity as capacity
import market_sim.runner as runner
from market_sim.config.scenarios import ScenarioConfig

RECORDS: dict = {
    "iso": None,
    "years": {},  # year -> {"fleet_in": [...], "known_ret": [...], "econ_ret": [...], "loss_years": {...}}
    "base_fleet": [],
    "error": None,
}
CURRENT_YEAR: list = [None]


def _unit_row(g) -> dict:
    return {
        "unit_id": g.unit_id,
        "plant_code": int(getattr(g, "plant_code", 0) or 0),
        "fuel": g.fuel_type,
        "pmax_mw": round(float(g.pmax_mw), 1),
        "heat_rate": round(float(g.heat_rate), 2),
        "retirement_year": g.retirement_year,
        "zone": g.zone,
    }


_orig_announced = capacity.apply_announced_retirements
_orig_confirmed = capacity.apply_confirmed_exits
_orig_econ = capacity.apply_economic_retirements
_orig_evolve = capacity.evolve_fleet
_orig_base = runner.build_base_fleet


def wrapped_announced(fleet, year, fossil_economic=True, **kw):
    out = _orig_announced(fleet, year, fossil_economic, **kw)
    gone = {g.unit_id for g in fleet} - {g.unit_id for g in out}
    yr = RECORDS["years"].setdefault(year, {})
    yr["announced_ret"] = [_unit_row(g) for g in fleet if g.unit_id in gone]
    # units whose announced date has passed but were exempted (fossil)
    yr["fossil_exempt_due"] = [
        _unit_row(g)
        for g in out
        if g.retirement_year is not None and g.retirement_year <= year
    ]
    return out


def wrapped_confirmed(fleet, year, exits):
    out = _orig_confirmed(fleet, year, exits)
    before = {g.unit_id: g.pmax_mw for g in fleet}
    after = {g.unit_id: g.pmax_mw for g in out}
    yr = RECORDS["years"].setdefault(year, {})
    # Units fully removed and units derated (pmax shrank) by a confirmed exit.
    yr["confirmed_dropped"] = [_unit_row(g) for g in fleet if g.unit_id not in after]
    yr["confirmed_derated"] = [
        {
            "unit_id": uid,
            "pmax_before": round(before[uid], 1),
            "pmax_after": round(after[uid], 1),
        }
        for uid in after
        if uid in before and after[uid] < before[uid] - 1e-6
    ]
    return out


def wrapped_econ(
    fleet,
    fleet_arrays,
    dispatch_result,
    prices,
    config,
    consecutive_loss_years,
    peak_demand,
    **kw,
):
    survivors, loss_years, floor_retention_log = _orig_econ(
        fleet,
        fleet_arrays,
        dispatch_result,
        prices,
        config,
        consecutive_loss_years,
        peak_demand,
        **kw,
    )
    gone = {g.unit_id for g in fleet} - {g.unit_id for g in survivors}
    year = CURRENT_YEAR[0]
    yr = RECORDS["years"].setdefault(year, {})
    yr["econ_ret"] = [_unit_row(g) for g in fleet if g.unit_id in gone]
    yr["loss_years"] = dict(loss_years)
    yr["floor_retentions"] = list(floor_retention_log)
    return survivors, loss_years, floor_retention_log


def wrapped_evolve(fleet, prior_results, year, config, loss_tracker, **kw):
    CURRENT_YEAR[0] = year
    yr = RECORDS["years"].setdefault(year, {})
    yr["fleet_in"] = [_unit_row(g) for g in fleet if g.retirement_year is not None]
    yr["fleet_in_thermal_mw"] = round(
        sum(g.pmax_mw for g in fleet if g.fuel_type in capacity._THERMAL_FOM), 0
    )
    return _orig_evolve(fleet, prior_results, year, config, loss_tracker, **kw)


def wrapped_base(*args, **kwargs):
    fleet = _orig_base(*args, **kwargs)
    RECORDS["base_fleet"] = [_unit_row(g) for g in fleet]
    return fleet


capacity.apply_announced_retirements = wrapped_announced
capacity.apply_confirmed_exits = wrapped_confirmed
capacity.apply_economic_retirements = wrapped_econ
runner.evolve_fleet = wrapped_evolve
runner.build_base_fleet = wrapped_base


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", required=True)
    ap.add_argument("--end-year", type=int, default=2029)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--confirmed-exits",
        action="store_true",
        help="enable the confirmed-exit injector with the seeded registry "
        "(W2-P2 verification: which confirmed units exit on schedule)",
    )
    args = ap.parse_args()

    runner.END_YEAR = args.end_year  # short horizon: diagnostic only
    RECORDS["iso"] = args.iso
    RECORDS["confirmed_exits_enabled"] = bool(args.confirmed_exits)

    import logging

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    config = ScenarioConfig(
        iso=args.iso, mode="forecast", confirmed_exits_enabled=args.confirmed_exits
    )
    try:
        runner.run_scenario_iso(config, args.iso)
    except Exception:
        RECORDS["error"] = traceback.format_exc()
    finally:
        Path(args.out).write_text(json.dumps(RECORDS, indent=1, default=str))
        print(f"wrote {args.out}; error={'yes' if RECORDS['error'] else 'no'}")


if __name__ == "__main__":
    main()
