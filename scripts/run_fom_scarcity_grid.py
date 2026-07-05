"""Joint FOM x scarcity verification grid (capacity-economics plan §5 step 3).

Six ERCOT forecast probes (2026-2031, mid growth): FOM in {legacy, ATB} x
scarcity in {overlay off, ORDC overlay (today's default), endogenous
multi-product AS co-opt}, plus the 2-cell PJM FOM-axis check (capacity-market
revenue side). Per cell it records: retired thermal GW by fuel, backstop
forced-build MW by year, the CO2 path, and — the §5 identification quantity —
the retirement screen's per-class collected revenue stack for gas_ct / gas_cc
in $/kW-yr (energy margin on the screen's price signal + AS credit + capacity
payment), instrumented probe-style around apply_economic_retirements.

This grid is VERIFICATION, never calibration (plan §5 threat model): the FOM
side is identified by NREL ATB / EIA-S&L published values, the revenue side
by the published ORDC methodology and the Potomac SOM net-revenue benchmark
(scripts/probes/fom_scarcity_revenue_audit.py). Nothing here tunes either
side against retirement pace. Forecast probes only — no dashboard runs.

Acceptance gates for flipping the FOM defaults (plan §5.4): in the
ATB x ORDC-default cell, 2026-2028 thermal retirement pace within the
observed ERCOT range (~0.5-2 GW/yr) and backstop force-builds ~0 in the
first three years.

Usage::

    python scripts/run_fom_scarcity_grid.py --workers 1 --out docs/handoffs
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

logger = logging.getLogger("fom_scarcity_grid")

# FOM axis: legacy defaults vs the plan §1.2 ATB/EIA-S&L proposal.
FOM_AXIS: dict[str, dict] = {
    "legacy": {},
    "atb": {"fixed_om_gas_ct": 21.0, "fixed_om_gas_cc": 30.0, "fixed_om_coal": 45.0},
}

# Scarcity axis (ERCOT): overlay off / post-solve ORDC overlay (today's
# default capacity-economics footing) / endogenous multi-product AS co-opt
# (the designated forward mechanism, forecast-gap G1/P1).
SCARCITY_AXIS: dict[str, dict] = {
    "off": {"scarcity_pricing_enabled": False},
    "ordc": {"scarcity_pricing_enabled": True},
    "coopt": {
        "scarcity_pricing_enabled": True,
        "energy_reserve_coopt": True,
        "ercot_multiproduct_as_coopt": True,
        "ercot_thermal_as_endogenous": True,
        "ercot_storage_as_endogenous": True,
        "ercot_as_forward_requirement": True,
    },
}

BASE_OVERRIDES: dict = {
    "use_campd_bins": False,
    "reserve_margin_build_enabled": True,
    "demand_growth_path": "mid",
}

SCREEN_CLASSES = ("gas_ct", "gas_cc")


@dataclass
class CellSpec:
    """One grid cell (picklable for a worker process)."""

    cell: str
    iso: str
    overrides: dict
    start_year: int
    end_year: int
    cache_root: str


@dataclass
class CellResult:
    """Metrics read back from one grid cell."""

    cell: str
    iso: str
    status: str
    per_year: list = field(default_factory=list)
    screen_revenue_kw_yr: dict = field(default_factory=dict)
    retired_mw_by_fuel: dict = field(default_factory=dict)
    retired_mw_by_year: dict = field(default_factory=dict)
    backstop_mw_by_year: dict = field(default_factory=dict)
    floor_retained_mw_by_year: dict = field(default_factory=dict)
    error: str | None = None


def evaluate_cell(spec_dict: dict) -> dict:
    """Run one instrumented grid cell (worker process entry point)."""
    spec = CellSpec(**spec_dict)
    import market_sim.model.capacity as capacity
    from market_sim import runner
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.model.ancillary import as_revenue_per_mw_yr
    from market_sim.results import cache
    from market_sim.results.export import _summarize_year

    runner.START_YEAR = spec.start_year
    runner.END_YEAR = spec.end_year
    cache.CACHE_ROOT = Path(spec.cache_root)

    out = CellResult(cell=spec.cell, iso=spec.iso, status="ok")

    current_year: list[int | None] = [None]
    backstop: dict[int, float] = {}
    retired: dict[str, float] = {}
    retired_by_year: dict[int, float] = {}
    floor_mw: dict[int, float] = {}
    screen_rev: dict[int, dict] = {}

    orig_evolve = capacity.evolve_fleet
    orig_backstop = capacity.apply_reserve_margin_build
    orig_econ = capacity.apply_economic_retirements

    def wrapped_evolve(fleet, prior_results, year, config, loss_tracker, **kw):
        current_year[0] = year
        return orig_evolve(fleet, prior_results, year, config, loss_tracker, **kw)

    def wrapped_backstop(fleet, firm_capacity_mw, peak_demand_mw, year, config, iso):
        new_fleet, built = orig_backstop(
            fleet, firm_capacity_mw, peak_demand_mw, year, config, iso
        )
        backstop[year] = backstop.get(year, 0.0) + float(built)
        return new_fleet, built

    def wrapped_econ(
        fleet, fleet_arrays, dispatch_result, prices, config, losses, peak, **kw
    ):
        # §5 identification quantity: the per-class revenue stack the screen
        # actually collects, mirroring apply_economic_retirements' own
        # arithmetic (energy margin on the screen's signal + AS credit +
        # capacity payment; attribute revenue is zero for fossil).
        yr = current_year[0] or 0
        mc = kw.get("mc")
        storage_power_mw = kw.get("storage_power_mw", 0.0)
        thermal_as = kw.get("thermal_as_revenue_per_mw_yr")
        headroom = kw.get("deliverability_headroom")
        prices_arr = np.asarray(prices, dtype=float)
        dispatch = np.asarray(dispatch_result.dispatch, dtype=float)
        idx_of = {uid: i for i, uid in enumerate(fleet_arrays.unit_ids)}
        acc: dict[str, dict] = {
            c: {"energy": 0.0, "as": 0.0, "capacity": 0.0, "mw": 0.0}
            for c in SCREEN_CLASSES
        }
        for g in fleet:
            if g.fuel_type not in SCREEN_CLASSES:
                continue
            rows = capacity._dispatch_rows(g, idx_of)
            if not rows:
                continue
            zone = int(fleet_arrays.zone_idx[rows[0]])
            if mc is None:
                energy = float(sum(np.dot(prices_arr[zone], dispatch[i]) for i in rows))
            else:
                mc_arr = np.asarray(mc, dtype=float)
                energy = float(
                    sum(np.dot(prices_arr[zone] - mc_arr[i], dispatch[i]) for i in rows)
                )
            if thermal_as is not None:
                as_rev = g.pmax_mw * thermal_as.get(g.fuel_type, 0.0)
            else:
                as_rev = g.pmax_mw * as_revenue_per_mw_yr(
                    g.fuel_type, storage_power_mw, config
                )
            cap_rev = 0.0
            if not capacity._zone_is_long(headroom, g.zone):
                cap_rev = g.pmax_mw * capacity.capacity_revenue_per_mw_yr(
                    config.iso, g.eford
                )
            a = acc[g.fuel_type]
            a["energy"] += energy
            a["as"] += as_rev
            a["capacity"] += cap_rev
            a["mw"] += g.pmax_mw
        screen_rev[yr] = {
            c: {
                "energy_kw_yr": round(v["energy"] / (v["mw"] * 1000.0), 2),
                "as_kw_yr": round(v["as"] / (v["mw"] * 1000.0), 2),
                "capacity_kw_yr": round(v["capacity"] / (v["mw"] * 1000.0), 2),
                "total_kw_yr": round(
                    (v["energy"] + v["as"] + v["capacity"]) / (v["mw"] * 1000.0), 2
                ),
                "class_mw": round(v["mw"], 1),
            }
            for c, v in acc.items()
            if v["mw"] > 0.0
        }

        survivors, losses_out, floor_log = orig_econ(
            fleet, fleet_arrays, dispatch_result, prices, config, losses, peak, **kw
        )
        gone = {g.unit_id for g in fleet} - {g.unit_id for g in survivors}
        for g in fleet:
            if g.unit_id in gone:
                retired[g.fuel_type] = retired.get(g.fuel_type, 0.0) + g.pmax_mw
                retired_by_year[yr] = retired_by_year.get(yr, 0.0) + g.pmax_mw
        floor_mw[yr] = floor_mw.get(yr, 0.0) + sum(r["pmax_mw"] for r in floor_log)
        return survivors, losses_out, floor_log

    capacity.evolve_fleet = wrapped_evolve
    runner.evolve_fleet = wrapped_evolve
    capacity.apply_reserve_margin_build = wrapped_backstop
    capacity.apply_economic_retirements = wrapped_econ

    try:
        config = ScenarioConfig(iso=spec.iso, **{**BASE_OVERRIDES, **spec.overrides})
        key = runner.run_scenario_iso(config, spec.iso)
        for year in range(spec.start_year, spec.end_year + 1):
            result = cache.load_result(spec.iso, key, year)
            context = cache.load_fleet_context(spec.iso, key, year)
            summary = _summarize_year(result, context)
            out.per_year.append(
                {
                    "year": year,
                    "co2_mt": summary["emissions_mt"],
                    "avg_price": summary["avg_price"],
                }
            )
        out.screen_revenue_kw_yr = {int(k): v for k, v in screen_rev.items()}
        out.retired_mw_by_fuel = {k: round(v, 1) for k, v in retired.items()}
        out.retired_mw_by_year = {
            int(k): round(v, 1) for k, v in retired_by_year.items()
        }
        out.backstop_mw_by_year = {int(k): round(v, 1) for k, v in backstop.items()}
        out.floor_retained_mw_by_year = {
            int(k): round(v, 1) for k, v in floor_mw.items()
        }
    except Exception as exc:  # noqa: BLE001 - a failed cell is data
        out.status = "failed"
        out.error = f"{type(exc).__name__}: {exc}"
        logger.warning("cell %s failed: %s", spec.cell, out.error)
    finally:
        capacity.evolve_fleet = orig_evolve
        runner.evolve_fleet = orig_evolve
        capacity.apply_reserve_margin_build = orig_backstop
        capacity.apply_economic_retirements = orig_econ
    return asdict(out)


def gate_check(results: dict[str, CellResult], start_year: int) -> dict:
    """Plan §5.4 acceptance gates on the ATB x ORDC-default cell."""
    cell = results.get("ercot:atb:ordc")
    if not cell or cell.status != "ok":
        return {"pass": False, "reason": "atb:ordc cell missing/failed"}
    # Capacity evolution (screen + backstop) first runs entering the second
    # simulated year, so "the first three years" reads the evolution years
    # start+1..start+3.
    first3 = range(start_year + 1, start_year + 4)
    pace = [cell.retired_mw_by_year.get(y, 0.0) / 1000.0 for y in first3]
    backstop3 = sum(cell.backstop_mw_by_year.get(y, 0.0) for y in first3)
    # Observed ERCOT thermal retirement pace ~0.5-2 GW/yr (plan §5.4);
    # gate on the mean over the first three evolution years, with a small
    # tolerance band around the observed range.
    mean_pace = float(np.mean(pace)) if pace else 0.0
    pace_ok = 0.3 <= mean_pace <= 2.5
    backstop_ok = backstop3 <= 1.0
    return {
        "retirement_pace_gw_by_year": [round(p, 2) for p in pace],
        "retirement_pace_gw_mean": round(mean_pace, 2),
        "pace_within_observed_band": pace_ok,
        "backstop_mw_first3": round(backstop3, 1),
        "backstop_near_zero": backstop_ok,
        "pass": bool(pace_ok and backstop_ok),
    }


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start-year", type=int, default=2026)
    p.add_argument("--end-year", type=int, default=2031)
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--skip-pjm", action="store_true")
    p.add_argument("--only", nargs="+", default=None, help="Restrict cell ids.")
    p.add_argument("--out", default="docs/handoffs")
    p.add_argument("--cache-root", default=None)
    args = p.parse_args(argv)

    out_dir = REPO / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_root = args.cache_root or str(out_dir / "_fom_grid_cache")

    specs: list[CellSpec] = []
    for fom_key, fom_ov in FOM_AXIS.items():
        for sc_key, sc_ov in SCARCITY_AXIS.items():
            specs.append(
                CellSpec(
                    cell=f"ercot:{fom_key}:{sc_key}",
                    iso="ERCOT",
                    overrides={**fom_ov, **sc_ov},
                    start_year=args.start_year,
                    end_year=args.end_year,
                    cache_root=cache_root,
                )
            )
    if not args.skip_pjm:
        for fom_key, fom_ov in FOM_AXIS.items():
            specs.append(
                CellSpec(
                    cell=f"pjm:{fom_key}",
                    iso="PJM",
                    overrides=dict(fom_ov),
                    start_year=args.start_year,
                    end_year=args.end_year,
                    cache_root=cache_root,
                )
            )
    if args.only:
        keep = set(args.only)
        specs = [s for s in specs if s.cell in keep]

    logger.info("grid: %d cells, %d workers", len(specs), args.workers)
    t0 = time.perf_counter()
    results: dict[str, CellResult] = {}
    with ProcessPoolExecutor(
        max_workers=max(1, args.workers), max_tasks_per_child=1
    ) as pool:
        futures = {pool.submit(evaluate_cell, asdict(s)): s.cell for s in specs}
        for fut in as_completed(futures):
            cid = futures[fut]
            results[cid] = CellResult(**fut.result())
            logger.info("%s -> %s", cid, results[cid].status)
    elapsed = time.perf_counter() - t0

    gates = gate_check(results, args.start_year)
    stem = f"fom-scarcity-grid-{date.today().isoformat()}"
    (out_dir / f"{stem}.json").write_text(
        json.dumps(
            {
                "start_year": args.start_year,
                "end_year": args.end_year,
                "base_overrides": BASE_OVERRIDES,
                "fom_axis": FOM_AXIS,
                "scarcity_axis": SCARCITY_AXIS,
                "elapsed_s": round(elapsed, 1),
                "results": {k: asdict(v) for k, v in results.items()},
                "acceptance_gates": gates,
            },
            indent=1,
        )
    )
    print(json.dumps(gates, indent=1))
    print(f"grid results: {out_dir / (stem + '.json')}")


if __name__ == "__main__":
    main()
