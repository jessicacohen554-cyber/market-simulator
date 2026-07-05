"""Foresight A/B experiment for the capacity-screen price signal (W2-P3).

Capacity-economics plan 2026-07 §2.4: four arms — (0) base myopic, (1) EWMA
alpha=0.6, (2) lookahead stack re-price, (3) both — on an ERCOT forecast,
run for the high demand-growth path (the stress case where one-pass myopia is
maximal) plus a mid-growth replicate. Legacy equal-width bins for runtime
(the tornado's documented fidelity trade); sequential years inside each run,
worker processes capped per CLAUDE.md rule 12.

Per-arm metrics over the 2030-2040 window (plan §2.4): fossil dispatch TWh by
class (coal / gas_cc / gas_ct+st), cumulative CO2 Mt, cumulative economic
retirements GW by fuel, cumulative economic entry GW by tech,
reserve-margin-backstop forced MW by year (the myopia tell), floor-retained
MW, and mean / P95 price. The decision rule prints with the report: an arm is
*material* if 2030-2040 cumulative fossil CO2 moves >5% vs arm 0, and
*preferred* if it also reduces backstop forced-build MW.

Forecast probes only — nothing here registers on the backcast dashboard.

Usage::

    python scripts/run_foresight_ab.py --start-year 2026 --end-year 2040 \
        --workers 2 --out docs/handoffs
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

logger = logging.getLogger("foresight_ab")

# The four experiment arms (plan §2.4). Every override is a first-class
# ScenarioConfig field, so each arm's cache_key captures it (rule 24).
ARMS: dict[str, dict] = {
    "base": {},
    "ewma": {"entry_price_signal_alpha": 0.6},
    "lookahead": {"entry_lookahead_reprice": True},
    "both": {"entry_price_signal_alpha": 0.6, "entry_lookahead_reprice": True},
}

GROWTH_PATHS = ("high", "mid")

# Legacy bins for runtime (tornado fidelity trade, documented in the report);
# the adequacy backstop is ON so its forced-build MW — the myopia tell — is
# observable ("recommended on for forecasts", scenarios.py); scarcity pricing
# is ON so the screens run on ERCOT's default capacity-economics footing (the
# post-solve ORDC overlay — plan §5's "today's default" cell; without it the
# perfect-foresight duals carry zero scarcity rent, plan §1.3) and the
# lookahead arm's ORDC tail is live.
BASE_OVERRIDES: dict = {
    "use_campd_bins": False,
    "reserve_margin_build_enabled": True,
    "scarcity_pricing_enabled": True,
}

WINDOW = (2030, 2040)  # metrics window (plan §2.4)

FOSSIL_CLASSES = {
    "coal": ("coal",),
    "gas_cc": ("gas_cc", "gas_cc_ccs"),
    "gas_ct_st": ("gas_ct", "gas_st", "oil"),
}


@dataclass
class ArmSpec:
    """One forward run (picklable for a worker process)."""

    arm: str
    growth: str
    overrides: dict
    start_year: int
    end_year: int
    cache_root: str


@dataclass
class ArmResult:
    """Metrics read back from one forward run."""

    arm: str
    growth: str
    status: str
    per_year: list = field(default_factory=list)
    backstop_mw_by_year: dict = field(default_factory=dict)
    retired_mw_by_fuel: dict = field(default_factory=dict)
    entered_mw_by_tech: dict = field(default_factory=dict)
    floor_retained_mw_by_year: dict = field(default_factory=dict)
    window: dict = field(default_factory=dict)
    error: str | None = None


def evaluate_arm(spec_dict: dict) -> dict:
    """Run one instrumented forward solve (worker process entry point)."""
    spec = ArmSpec(**spec_dict)
    import market_sim.model.capacity as capacity
    from market_sim import runner
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.results import cache
    from market_sim.results.export import _summarize_year

    runner.START_YEAR = spec.start_year
    runner.END_YEAR = spec.end_year
    cache.CACHE_ROOT = Path(spec.cache_root)

    out = ArmResult(arm=spec.arm, growth=spec.growth, status="ok")

    # --- instrumentation (probe-style wrappers; touches nothing in src/) ---
    current_year: list[int | None] = [None]
    backstop: dict[int, float] = {}
    retired: dict[str, float] = {}
    entered: dict[str, float] = {}
    floor_mw: dict[int, float] = {}

    orig_evolve = capacity.evolve_fleet
    orig_backstop = capacity.apply_reserve_margin_build
    orig_econ = capacity.apply_economic_retirements
    orig_entry = capacity.apply_economic_new_entry

    def wrapped_evolve(fleet, prior_results, year, config, loss_tracker, **kw):
        current_year[0] = year
        return orig_evolve(fleet, prior_results, year, config, loss_tracker, **kw)

    def wrapped_backstop(fleet, firm_capacity_mw, peak_demand_mw, year, config, iso):
        new_fleet, built = orig_backstop(
            fleet, firm_capacity_mw, peak_demand_mw, year, config, iso
        )
        backstop[year] = backstop.get(year, 0.0) + float(built)
        return new_fleet, built

    def wrapped_econ(fleet, *args, **kw):
        survivors, losses, floor_log = orig_econ(fleet, *args, **kw)
        gone = {g.unit_id for g in fleet} - {g.unit_id for g in survivors}
        for g in fleet:
            if g.unit_id in gone:
                retired[g.fuel_type] = retired.get(g.fuel_type, 0.0) + g.pmax_mw
        yr = current_year[0] or 0
        floor_mw[yr] = floor_mw.get(yr, 0.0) + sum(r["pmax_mw"] for r in floor_log)
        return survivors, losses, floor_log

    def wrapped_entry(fleet, *args, **kw):
        new_fleet, renewable_additions = orig_entry(fleet, *args, **kw)
        before = {g.unit_id for g in fleet}
        for g in new_fleet:
            if g.unit_id not in before:
                entered[g.fuel_type] = entered.get(g.fuel_type, 0.0) + g.pmax_mw
        for by_fuel in renewable_additions.values():
            for fuel, mw in by_fuel.items():
                entered[fuel] = entered.get(fuel, 0.0) + mw
        return new_fleet, renewable_additions

    capacity.evolve_fleet = wrapped_evolve
    runner.evolve_fleet = wrapped_evolve
    capacity.apply_reserve_margin_build = wrapped_backstop
    capacity.apply_economic_retirements = wrapped_econ
    capacity.apply_economic_new_entry = wrapped_entry

    try:
        config = ScenarioConfig(
            iso="ERCOT",
            demand_growth_path=spec.growth,
            **BASE_OVERRIDES,
            **spec.overrides,
        )
        key = runner.run_scenario_iso(config, "ERCOT")

        for year in range(spec.start_year, spec.end_year + 1):
            result = cache.load_result("ERCOT", key, year)
            context = cache.load_fleet_context("ERCOT", key, year)
            summary = _summarize_year(result, context)
            prices = np.asarray(result.prices, dtype=float)
            out.per_year.append(
                {
                    "year": year,
                    "co2_mt": summary["emissions_mt"],
                    "avg_price": summary["avg_price"],
                    "p95_price": round(float(np.percentile(prices, 95)), 2),
                    "generation_twh": summary["generation_twh"],
                }
            )

        out.backstop_mw_by_year = {int(k): round(v, 1) for k, v in backstop.items()}
        out.retired_mw_by_fuel = {k: round(v, 1) for k, v in retired.items()}
        out.entered_mw_by_tech = {k: round(v, 1) for k, v in entered.items()}
        out.floor_retained_mw_by_year = {
            int(k): round(v, 1) for k, v in floor_mw.items()
        }

        # Metrics window clamped to the run horizon (a smoke run shorter
        # than 2030 still reports over its own years).
        w_lo = max(WINDOW[0], spec.start_year)
        w_hi = min(WINDOW[1], spec.end_year)
        if w_lo > w_hi:
            w_lo, w_hi = spec.start_year, spec.end_year
        window_rows = [r for r in out.per_year if w_lo <= r["year"] <= w_hi]
        fossil_twh = {
            cls: round(
                sum(
                    r["generation_twh"].get(f, 0.0) for r in window_rows for f in fuels
                ),
                2,
            )
            for cls, fuels in FOSSIL_CLASSES.items()
        }
        out.window = {
            "years": [w_lo, w_hi],
            "co2_mt_cum": round(sum(r["co2_mt"] for r in window_rows), 2),
            "fossil_twh_by_class": fossil_twh,
            "mean_price": round(
                float(np.mean([r["avg_price"] for r in window_rows])), 2
            ),
            "mean_p95_price": round(
                float(np.mean([r["p95_price"] for r in window_rows])), 2
            ),
            "backstop_mw_total": round(
                sum(v for k, v in out.backstop_mw_by_year.items() if w_lo <= k <= w_hi),
                1,
            ),
        }
    except Exception as exc:  # noqa: BLE001 - a failed arm is data
        out.status = "failed"
        out.error = f"{type(exc).__name__}: {exc}"
        logger.warning("arm %s/%s failed: %s", spec.arm, spec.growth, out.error)
    finally:
        capacity.evolve_fleet = orig_evolve
        runner.evolve_fleet = orig_evolve
        capacity.apply_reserve_margin_build = orig_backstop
        capacity.apply_economic_retirements = orig_econ
        capacity.apply_economic_new_entry = orig_entry
    return asdict(out)


def decide(results: dict[str, ArmResult], growth: str) -> dict:
    """Apply the plan §2.4 materiality bar / decision rule for one growth path."""
    base = results.get(f"base:{growth}")
    verdicts: dict[str, dict] = {}
    if not base or base.status != "ok":
        return {"error": "base arm failed"}
    base_co2 = base.window["co2_mt_cum"]
    base_backstop = base.window["backstop_mw_total"]
    for arm in ("ewma", "lookahead", "both"):
        r = results.get(f"{arm}:{growth}")
        if not r or r.status != "ok":
            verdicts[arm] = {"status": "failed"}
            continue
        dco2 = r.window["co2_mt_cum"] - base_co2
        pct = 100.0 * dco2 / base_co2 if base_co2 else 0.0
        material = abs(pct) > 5.0
        reduces_backstop = r.window["backstop_mw_total"] < base_backstop
        verdicts[arm] = {
            "co2_mt_cum": r.window["co2_mt_cum"],
            "delta_co2_mt": round(dco2, 2),
            "delta_co2_pct": round(pct, 2),
            "backstop_mw_total": r.window["backstop_mw_total"],
            "material": material,
            "reduces_backstop": reduces_backstop,
            "preferred": material and reduces_backstop,
        }
    verdicts["base"] = {
        "co2_mt_cum": base_co2,
        "backstop_mw_total": base_backstop,
    }
    return verdicts


def render_report(args, results: dict[str, ArmResult], decisions: dict) -> str:
    """Render the committed markdown report."""
    lines: list[str] = []
    a = lines.append
    a(f"# Foresight A/B — ERCOT forecast {args.start_year}-{args.end_year}")
    a("")
    a(
        f"*Generated {date.today().isoformat()} by `scripts/run_foresight_ab.py` "
        "(capacity-economics plan 2026-07 §2.4, W2-P3 stage 3).*"
    )
    a("")
    a(
        "Four arms x two demand-growth paths, legacy equal-width bins "
        "(runtime fidelity trade, as the sensitivity tornado), adequacy "
        "backstop ON so its forced-build MW — the myopia tell — is "
        "observable. Forecast probes only: nothing here is a backcast or a "
        "dashboard run. Metrics window 2030-2040."
    )
    a("")
    a("## Arms")
    a("")
    a("| Arm | Overrides |")
    a("|---|---|")
    for arm, ov in ARMS.items():
        a(f"| {arm} | `{ov or '(myopic base)'}` |")
    a("")
    ran_growths = sorted({k.split(":", 1)[1] for k in results})
    ran_arms = [arm for arm in ARMS if any(k.startswith(f"{arm}:") for k in results)]
    for growth in ran_growths:
        a(f"## Growth path: {growth}")
        a("")
        a(
            "| Arm | cum CO2 (Mt) | dCO2 vs base | coal TWh | gas_cc TWh | "
            "gas_ct+st TWh | retired GW | entered GW | backstop MW | "
            "floor MW (max yr) | mean $ | P95 $ |"
        )
        a("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for arm in ran_arms:
            r = results.get(f"{arm}:{growth}")
            if not r or r.status != "ok":
                a(f"| {arm} | failed: {r.error if r else 'missing'} |")
                continue
            w = r.window
            v = decisions.get(growth, {}).get(arm, {})
            dpct = f"{v['delta_co2_pct']:+.1f}%" if "delta_co2_pct" in v else "—"
            retired_gw = round(sum(r.retired_mw_by_fuel.values()) / 1000.0, 2)
            entered_gw = round(sum(r.entered_mw_by_tech.values()) / 1000.0, 2)
            floor_max = (
                max(r.floor_retained_mw_by_year.values())
                if r.floor_retained_mw_by_year
                else 0.0
            )
            a(
                f"| {arm} | {w['co2_mt_cum']} | {dpct} | "
                f"{w['fossil_twh_by_class']['coal']} | "
                f"{w['fossil_twh_by_class']['gas_cc']} | "
                f"{w['fossil_twh_by_class']['gas_ct_st']} | "
                f"{retired_gw} | {entered_gw} | {w['backstop_mw_total']} | "
                f"{floor_max} | {w['mean_price']} | {w['mean_p95_price']} |"
            )
        a("")
        a(f"### Decision inputs ({growth})")
        a("")
        a("```json")
        a(json.dumps(decisions.get(growth, {}), indent=1))
        a("```")
        a("")
    a("## Decision rule (plan §2.4)")
    a("")
    a(
        "Promote the simplest material arm (>5% cumulative 2030-2040 fossil "
        "CO2 move vs base, preferred if it also reduces backstop MW). "
        "Component 1 of the lookahead arm — known-demand substitution in the "
        "peak-anchored mechanisms — was promoted unconditionally in stage 2 "
        "(a bug-class fix) and is ON in every arm here, including base. If "
        "nothing is material, entry_lookahead_reprice stays default-off as a "
        "designed probe and the negative result is recorded."
    )
    a("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start-year", type=int, default=2026)
    p.add_argument("--end-year", type=int, default=2040)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--growth", nargs="+", default=list(GROWTH_PATHS))
    p.add_argument("--only", nargs="+", default=None, help="Restrict arms.")
    p.add_argument("--out", default="docs/handoffs")
    p.add_argument("--cache-root", default=None)
    args = p.parse_args(argv)

    out_dir = REPO / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_root = args.cache_root or str(out_dir / "_foresight_ab_cache")

    arms = {k: v for k, v in ARMS.items() if not args.only or k in args.only}
    specs = [
        ArmSpec(
            arm=arm,
            growth=growth,
            overrides=dict(ov),
            start_year=args.start_year,
            end_year=args.end_year,
            cache_root=cache_root,
        )
        for growth in args.growth
        for arm, ov in arms.items()
    ]
    logger.info("foresight A/B: %d runs, %d workers", len(specs), args.workers)

    t0 = time.perf_counter()
    results: dict[str, ArmResult] = {}
    with ProcessPoolExecutor(
        max_workers=max(1, args.workers), max_tasks_per_child=1
    ) as pool:
        futures = {
            pool.submit(evaluate_arm, asdict(s)): f"{s.arm}:{s.growth}" for s in specs
        }
        for fut in as_completed(futures):
            rid = futures[fut]
            results[rid] = ArmResult(**fut.result())
            logger.info("%s -> %s", rid, results[rid].status)
    elapsed = time.perf_counter() - t0

    decisions = {g: decide(results, g) for g in args.growth}
    report = render_report(args, results, decisions)
    stem = f"foresight-ab-ercot-{date.today().isoformat()}"
    (out_dir / f"{stem}.md").write_text(report)
    (out_dir / f"{stem}.json").write_text(
        json.dumps(
            {
                "start_year": args.start_year,
                "end_year": args.end_year,
                "base_overrides": BASE_OVERRIDES,
                "arms": ARMS,
                "elapsed_s": round(elapsed, 1),
                "results": {k: asdict(v) for k, v in results.items()},
                "decisions": decisions,
            },
            indent=1,
        )
    )
    print(f"foresight A/B report: {out_dir / (stem + '.md')}")


if __name__ == "__main__":
    main()
