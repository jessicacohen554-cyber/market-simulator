#!/usr/bin/env python
"""D-9 forecast warm-start A/B — full-horizon warm arm vs cold arm (one ISO).

Owner decision D-9 (``docs/refactor-consolidation-plan-2026-07.md`` §9, wall-clock
lever §7 H-3) flips the forecast-path cross-year LP warm start ON *only* on
evidence that the capacity trajectory is unchanged. This probe is that evidence.

Each arm is ONE invocation solving its years sequentially (rule 12); the caller
launches the two arms as the two permitted concurrent invocations, each with its
own ``--out-dir``. The arms are isolated twice over: ``solve_and_summarize``
redirects ``CACHE_ROOT`` to the arm's out-dir, and arming
``forecast_xyear_warmstart`` changes the ``cache_key``, so neither arm can read
the other's cached years.

Determinism pin: run both arms with ``MARKET_SIM_HIGHS_THREADS=1``. HiGHS's
multi-threaded dual simplex breaks marginal ties nondeterministically, so at the
default thread setting even a cold-vs-cold control drifts and the trajectory
comparison would measure the solver, not the warm start
(``docs/cross-year-warmstart.md``). The single-thread penalty on ERCOT cold P0 is
~5 % (``docs/handoffs/wallclock-baseline-2026-07.md`` Exp 3), so the wall-clock
comparison is unaffected — both arms pay it.

The config is ``run_full_horizon.reference_config`` — every ScenarioConfig field
at its default except mode/iso/horizon — plus the one arm bit. This probe
deliberately does not go through ``run_full_horizon.main``: that entry point's
``assert_schedulable`` gate is the FORECAST program's §2.1b scheduling
discipline for registered forecast-family runs, and this is a wall-clock probe
that registers nothing. The horizon it solves is whatever the owner's A/B ask
specifies.

Usage::

    # one arm (launch the two arms concurrently, each in its own invocation):
    MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
        python scripts/probes/_d9_forecast_warmstart_ab.py --arm warm \
        --iso ERCOT --out-dir results/d9-ab/warm

    # then the verdict:
    python scripts/probes/_d9_forecast_warmstart_ab.py --compare \
        --cold results/d9-ab/cold/full_horizon_summary.json \
        --warm results/d9-ab/warm/full_horizon_summary.json \
        --out results/d9-ab/verdict.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.run_full_horizon import (  # noqa: E402
    reference_config,
    solve_and_summarize,
)

# Capacity-trajectory keys the guardrail is scored on. These are the year-over-
# year fleet state and the capacity EVENTS that produce it — exactly what warm
# start must not move. Prices/emissions are reported separately: a price
# difference with an identical fleet is within-year marginal-tie noise, but a
# fleet difference is a surviving basis-dependent reader.
_CAPACITY_KEYS = (
    "total_cap_mw",
    "thermal_mw",
    "firm_clean_mw",
    "vre_mw",
    "storage_mw",
    "builds_thermal_mw",
    "builds_renew_mw",
    "builds_storage_mw",
    "retire_mw",
)
_OUTCOME_KEYS = (
    "lw_price",
    "max_hourly_price",
    "co2_mt",
    "reserve_margin",
    "peak_demand_mw",
)


def run_arm(
    arm: str,
    iso: str,
    start_year: int,
    end_year: int,
    out_dir: Path,
    hours: int = 8760,
    golden_posture: bool = False,
) -> dict:
    """Solve one arm's horizon and return its summary dict.

    ``hours`` < 8760 is a REDUCED-horizon pre-screen only (it reproduces the
    168 h ERCOT 2026-2032 measurement in ``docs/cross-year-warmstart.md`` that
    originally refuted the forecast wiring, so the same experiment can be
    re-run cheaply against the post-4C screen). The D-9 verdict itself is taken
    on the full 8760 h horizon — rule 8 [R-8760].

    ``golden_posture`` layers the §2.1a decision (a) per-ISO capacity-market
    clearing onto the reference config. The ERCOT D-9 A/B did not need it —
    energy-only ERCOT has no capacity market, so the flag is inert there. For
    the five capacity-market ISOs it is the whole point of the multi-ISO
    extension: the CR-1 sloped demand curve prices capacity off the accredited
    reserve position, which reaches all three capacity screens, and that path
    is exactly what the ERCOT guardrail never exercised. Both arms carry the
    same posture, so the A/B still isolates the warm start.
    """
    warm = arm == "warm"
    overrides = {"forecast_xyear_warmstart": warm}
    if hours != 8760:
        overrides["hours"] = hours
    config = reference_config(
        iso, start_year, end_year, cmc=False, golden_posture=golden_posture
    ).with_overrides(**overrides)
    assert config.forecast_xyear_warmstart is warm
    print(
        f"[d9-ab] arm={arm} iso={iso} {start_year}-{end_year} "
        f"forecast_xyear_warmstart={warm} golden_posture={golden_posture} "
        f"cache_key={config.cache_key()}"
    )
    return solve_and_summarize(
        config,
        iso,
        out_dir,
        redirect_cache=True,
        extra_summary={
            "d9_arm": arm,
            "forecast_xyear_warmstart": warm,
            "golden_posture": golden_posture,
        },
    )


def _by_year(summary: dict) -> dict[int, dict]:
    return {int(r["year"]): r for r in summary.get("trajectory", [])}


def compare(cold: dict, warm: dict) -> dict:
    """Diff the two arms' capacity trajectories year by year.

    Returns a verdict dict. ``capacity_identical`` is the D-9 guardrail: it is
    True only when every year present in both arms carries byte-equal values for
    every key in :data:`_CAPACITY_KEYS` AND an identical per-fuel capacity map.
    """
    c, w = _by_year(cold), _by_year(warm)
    years = sorted(set(c) & set(w))
    rows: list[dict] = []
    capacity_identical = True
    for year in years:
        cr, wr = c[year], w[year]
        deltas = {}
        for key in _CAPACITY_KEYS:
            cv, wv = cr.get(key), wr.get(key)
            if cv != wv:
                deltas[key] = {
                    "cold": cv,
                    "warm": wv,
                    "delta": (
                        (wv - cv)
                        if isinstance(cv, (int, float)) and isinstance(wv, (int, float))
                        else None
                    ),
                }
        fuel_deltas = {}
        cf = cr.get("capacity_by_fuel_mw") or {}
        wf = wr.get("capacity_by_fuel_mw") or {}
        for fuel in sorted(set(cf) | set(wf)):
            cv, wv = cf.get(fuel), wf.get(fuel)
            if cv != wv:
                fuel_deltas[fuel] = {"cold": cv, "warm": wv}
        outcome_deltas = {
            key: {"cold": cr.get(key), "warm": wr.get(key)}
            for key in _OUTCOME_KEYS
            if cr.get(key) != wr.get(key)
        }
        if deltas or fuel_deltas:
            capacity_identical = False
        rows.append(
            {
                "year": year,
                "capacity_deltas": deltas,
                "capacity_by_fuel_deltas": fuel_deltas,
                "outcome_deltas": outcome_deltas,
            }
        )
    return {
        "years_compared": years,
        "cold_years_solved": cold.get("solved_years"),
        "warm_years_solved": warm.get("solved_years"),
        "cold_total_wall_s": cold.get("total_wall_s"),
        "warm_total_wall_s": warm.get("total_wall_s"),
        "speedup": (
            round(cold["total_wall_s"] / warm["total_wall_s"], 3)
            if cold.get("total_wall_s") and warm.get("total_wall_s")
            else None
        ),
        "cold_peak_rss_mb": cold.get("global_peak_rss_mb"),
        "warm_peak_rss_mb": warm.get("global_peak_rss_mb"),
        "cold_per_year_perf": cold.get("per_year_perf"),
        "warm_per_year_perf": warm.get("per_year_perf"),
        "capacity_identical": capacity_identical,
        "verdict": "FLIP-CLEAR" if capacity_identical else "NO-FLIP",
        "per_year": rows,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=("warm", "cold"))
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument("--start-year", type=int, default=2026)
    ap.add_argument("--end-year", type=int, default=2050)
    ap.add_argument("--out-dir", type=Path)
    ap.add_argument(
        "--hours",
        type=int,
        default=8760,
        help="Reduced-horizon PRE-SCREEN only; the D-9 verdict runs at 8760.",
    )
    ap.add_argument(
        "--golden-posture",
        action="store_true",
        help=(
            "Layer the §2.1a per-ISO capacity-market clearing onto the arm "
            "(inert for energy-only ERCOT; the exercised path for the five "
            "capacity-market ISOs)."
        ),
    )
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--cold", type=Path, help="cold arm full_horizon_summary.json")
    ap.add_argument("--warm", type=Path, help="warm arm full_horizon_summary.json")
    ap.add_argument("--out", type=Path, help="verdict json path")
    args = ap.parse_args(argv)

    if args.compare:
        if not (args.cold and args.warm):
            ap.error("--compare needs --cold and --warm")
        verdict = compare(
            json.loads(args.cold.read_text()), json.loads(args.warm.read_text())
        )
        text = json.dumps(verdict, indent=2)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text + "\n")
        print(text)
        moved = [r["year"] for r in verdict["per_year"] if r["capacity_deltas"]]
        print(
            f"\n===== D-9 guardrail: {verdict['verdict']} =====\n"
            f"  capacity trajectory identical: {verdict['capacity_identical']}\n"
            f"  years with a capacity delta: {moved or 'none'}\n"
            f"  wall: cold {verdict['cold_total_wall_s']}s vs warm "
            f"{verdict['warm_total_wall_s']}s (speedup {verdict['speedup']})"
        )
        return 0 if verdict["capacity_identical"] else 2

    if not (args.arm and args.out_dir):
        ap.error("an arm run needs --arm and --out-dir")
    summary = run_arm(
        args.arm,
        args.iso.upper(),
        args.start_year,
        args.end_year,
        args.out_dir,
        hours=args.hours,
        golden_posture=args.golden_posture,
    )
    return 1 if summary.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
