"""Joint FOM x scarcity verification grid for the capacity-economics recalibration.

Implements the probe matrix of the capacity-economics plan §5 (step 3): the 2x3
ERCOT grid ``FOM in {legacy, ATB} x scarcity in {overlay off, ORDC overlay,
endogenous co-opt}`` over the near-term forecast horizon, plus the 2-cell PJM
FOM check (capacity-market revenue side). It is the *verification* leg of the
FOM+scarcity joint protocol — the mechanism that keeps the cost side (FOM) and
the revenue side (scarcity/AS) from being co-tuned against a single retirement
residual (CLAUDE.md rule 1). **Nothing here is a keeper, a backcast run, or a
tuning step**; every cell is a forecast probe whose output feeds
``docs/handoffs/fom-scarcity-joint-protocol-*.md``.

Each cell is a full forward solve (capacity evolution + P1 dispatch, sequential
years, exactly as ``runner.run_scenario_iso`` does it — CLAUDE.md rules 10/12).
Per cell it records, from the cached per-year bundles and the solve log:

  * ``co2_mt`` per year and horizon total (``results.export._summarize_year``);
  * ``avg_price`` per year;
  * ``retired_by_fuel`` GW between the first and last horizon year;
  * ``backstop_mw`` per year (reserve-margin adequacy backstop forced-build,
    parsed from the ``reserve-margin backstop built`` log line) — the acceptance
    gate's "revenue side still broken" tell (plan §5.4);
  * ``screen_revenue`` per fuel — capacity-weighted net-revenue $/kW-yr and the
    going-forward bar $/kW-yr (parsed from the ``screen revenue stack`` log line
    the retirement screen emits) — the revenue-side audit observable.

Runtime: legacy equal-width fleet (``use_campd_bins=False``) so the eight cells
finish in a reasonable wall-clock; the leverage/retirement *ranking* is robust
to fleet granularity (same trade the tornado documents). Rule 12: at most
``--workers`` concurrent solves (default 2), years sequential within each.

Usage::

    python scripts/run_fom_scarcity_grid.py --start-year 2026 --end-year 2031 \
        --workers 2 --out docs/handoffs
"""

from __future__ import annotations

import argparse
import json
import logging
import re
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

THERMAL_FUELS: tuple[str, ...] = (
    "coal",
    "gas_cc",
    "gas_ct",
    "gas_st",
    "oil",
    "nuclear",
)

# ATB-class going-forward FOM defaults under test (plan §1.2). Legacy = today's
# ScenarioConfig defaults (empty override).
_ATB_FOM = {
    "fixed_om_gas_ct": 21.0,  # NREL ATB 2024 Gas CT (F-frame) FOM
    "fixed_om_gas_cc": 30.0,  # NREL ATB 2024 Gas CC FOM (= repo's new-CC value)
    "fixed_om_coal": 45.0,  # NREL ATB 2024 / EIA-S&L existing-coal FOM class
}

# Scarcity axis (ERCOT). "off" = bare LP duals, no AS (today's raw
# ScenarioConfig default). "ordc" = post-solve ORDC energy adder + exogenous AS
# overlay (the intended forecast revenue stack). "coopt" = endogenous
# multi-product AS co-optimization prices scarcity + AS inside the LP.
_SCARCITY: dict[str, dict] = {
    "off": {"scarcity_pricing_enabled": False, "as_revenue_enabled": False},
    "ordc": {
        "scarcity_pricing_enabled": True,
        "scarcity_price_overlay": True,
        "as_revenue_enabled": True,
    },
    "coopt": {
        "energy_reserve_coopt": True,
        "ercot_thermal_as_endogenous": True,
        "ercot_as_forward_requirement": True,
        "scarcity_pricing_enabled": True,
    },
}

_BACKSTOP_RE = re.compile(
    r"year (\d+): reserve-margin backstop built ([\d.]+) MW gas_ct"
)
_SCREEN_RE = re.compile(
    r"screen revenue stack \[(\w+)\]: net_rev=(-?[\d.]+) \$/kW-yr, "
    r"going_forward_bar=([\d.]+) \$/kW-yr, cap=([\d.]+) MW, n=(\d+)"
)


@dataclass
class CellSpec:
    """One grid cell (picklable for a worker process)."""

    cell_id: str
    iso: str
    fom: str  # "legacy" | "atb"
    scarcity: str  # "off" | "ordc" | "coopt" | "na" (PJM)
    overrides: dict
    start_year: int
    end_year: int
    cache_root: str
    log_path: str


@dataclass
class CellResult:
    """Metrics read back from one grid cell."""

    cell_id: str
    iso: str
    fom: str
    scarcity: str
    status: str
    co2_mt_total: float | None = None
    avg_price: float | None = None
    retired_thermal_gw: float | None = None
    retired_by_fuel: dict = field(default_factory=dict)
    backstop_mw_by_year: dict = field(default_factory=dict)
    screen_revenue: dict = field(default_factory=dict)
    per_year: list = field(default_factory=list)
    error: str | None = None


def _parse_log(log_path: str) -> tuple[dict, dict]:
    """Parse backstop MW/year and last-seen per-fuel screen revenue from a log."""
    backstop: dict[str, float] = {}
    screen: dict[str, dict] = {}
    text = Path(log_path).read_text(errors="replace")
    for m in _BACKSTOP_RE.finditer(text):
        backstop[m.group(1)] = float(m.group(2))
    for m in _SCREEN_RE.finditer(text):
        # Last occurrence per fuel wins (final evolution year, the settled fleet).
        screen[m.group(1)] = {
            "net_rev_per_kw_yr": float(m.group(2)),
            "going_forward_bar_per_kw_yr": float(m.group(3)),
            "cap_mw": float(m.group(4)),
            "n_units": int(m.group(5)),
        }
    return backstop, screen


def evaluate_cell(spec_dict: dict) -> dict:
    """Run one forward solve and return its metrics dict (worker process)."""
    spec = CellSpec(**spec_dict)
    from market_sim import runner
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.results import cache
    from market_sim.results.export import _summarize_year

    # Capture INFO logs (backstop + screen-revenue lines) to a per-cell file.
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.FileHandler(spec.log_path, mode="w")
    handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    root.addHandler(handler)

    runner.START_YEAR = spec.start_year
    runner.END_YEAR = spec.end_year
    cache.CACHE_ROOT = Path(spec.cache_root)

    result = CellResult(
        cell_id=spec.cell_id,
        iso=spec.iso,
        fom=spec.fom,
        scarcity=spec.scarcity,
        status="ok",
    )
    try:
        config = ScenarioConfig(iso=spec.iso).with_overrides(**spec.overrides)
        key = runner.run_scenario_iso(config, spec.iso)

        per_year = []
        cap_first: dict[str, float] | None = None
        cap_last: dict[str, float] = {}
        for year in range(spec.start_year, spec.end_year + 1):
            dr = cache.load_result(spec.iso, key, year)
            ctx = cache.load_fleet_context(spec.iso, key, year)
            summary = _summarize_year(dr, ctx)
            cap_gw = summary["capacity_gw"]
            per_year.append(
                {
                    "year": year,
                    "co2_mt": summary["emissions_mt"],
                    "avg_price": summary["avg_price"],
                    "capacity_gw": cap_gw,
                }
            )
            if cap_first is None:
                cap_first = dict(cap_gw)
            cap_last = cap_gw

        result.per_year = per_year
        result.co2_mt_total = float(sum(y["co2_mt"] for y in per_year))
        result.avg_price = float(np.mean([y["avg_price"] for y in per_year]))
        retired = {}
        if cap_first is not None:
            for fuel in THERMAL_FUELS:
                drop = cap_first.get(fuel, 0.0) - cap_last.get(fuel, 0.0)
                if drop > 1e-6:
                    retired[fuel] = round(drop, 4)
        result.retired_by_fuel = retired
        result.retired_thermal_gw = round(float(sum(retired.values())), 4)
    except Exception as exc:  # noqa: BLE001 — a bad cell is data, not a crash
        result.status = "failed"
        result.error = f"{type(exc).__name__}: {exc}"
    finally:
        handler.flush()
        root.removeHandler(handler)
        handler.close()

    try:
        result.backstop_mw_by_year, result.screen_revenue = _parse_log(spec.log_path)
    except Exception:  # noqa: BLE001 — log parse failure never aborts a cell
        pass
    return asdict(result)


def build_cells(
    start_year: int, end_year: int, cache_root: str, log_dir: str
) -> list[CellSpec]:
    """Build the 6 ERCOT + 2 PJM grid cells."""
    base = {"use_campd_bins": False, "reserve_margin_build_enabled": True}
    cells: list[CellSpec] = []

    def add(iso: str, fom: str, scarcity: str, extra: dict) -> None:
        cid = f"{iso.lower()}_{fom}_{scarcity}"
        ov = dict(base)
        if fom == "atb":
            ov.update(_ATB_FOM)
        ov.update(extra)
        cells.append(
            CellSpec(
                cell_id=cid,
                iso=iso,
                fom=fom,
                scarcity=scarcity,
                overrides=ov,
                start_year=start_year,
                end_year=end_year,
                cache_root=str(Path(cache_root) / cid),
                log_path=str(Path(log_dir) / f"{cid}.log"),
            )
        )

    for fom in ("legacy", "atb"):
        for scar, extra in _SCARCITY.items():
            add("ERCOT", fom, scar, extra)
    # PJM FOM axis only (capacity-market revenue side); default scarcity.
    for fom in ("legacy", "atb"):
        add("PJM", fom, "na", {})
    return cells


def run_grid(cells: list[CellSpec], workers: int) -> dict[str, CellResult]:
    """Execute every cell (fresh process each, memory freed on exit)."""
    results: dict[str, CellResult] = {}
    workers = max(1, int(workers))
    with ProcessPoolExecutor(max_workers=workers, max_tasks_per_child=1) as pool:
        futures = {pool.submit(evaluate_cell, asdict(c)): c.cell_id for c in cells}
        done = 0
        total = len(futures)
        for fut in as_completed(futures):
            cid = futures[fut]
            results[cid] = CellResult(**fut.result())
            done += 1
            logger.info("[%d/%d] %s -> %s", done, total, cid, results[cid].status)
    return results


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start-year", type=int, default=2026)
    p.add_argument("--end-year", type=int, default=2031)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--out", default="docs/handoffs")
    p.add_argument("--cache-root", default=None)
    return p


def main(argv: list[str] | None = None) -> None:
    """CLI entry point: run the grid and write the JSON result blob."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = _build_parser().parse_args(argv)
    out_dir = REPO / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_date = date.today().isoformat()
    cache_root = args.cache_root or str(out_dir / "_fom_scarcity_grid_cache")
    log_dir = str(out_dir / "_fom_scarcity_grid_logs")
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    cells = build_cells(args.start_year, args.end_year, cache_root, log_dir)
    logger.info(
        "grid %d-%d: %d cells, %d workers",
        args.start_year,
        args.end_year,
        len(cells),
        args.workers,
    )
    t0 = time.perf_counter()
    results = run_grid(cells, args.workers)
    elapsed = time.perf_counter() - t0
    logger.info("all cells finished in %.1fs", elapsed)

    json_path = out_dir / f"fom-scarcity-grid-{run_date}.json"
    json_path.write_text(
        json.dumps(
            {
                "start_year": args.start_year,
                "end_year": args.end_year,
                "elapsed_s": round(elapsed, 1),
                "atb_fom": _ATB_FOM,
                "scarcity_axis": _SCARCITY,
                "results": {k: asdict(v) for k, v in results.items()},
            },
            indent=2,
        )
    )
    logger.info("wrote %s", json_path)
    print(f"grid result: {json_path}")


if __name__ == "__main__":
    main()
