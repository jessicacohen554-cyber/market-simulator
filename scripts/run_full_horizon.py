#!/usr/bin/env python
"""Full-horizon forecast runner + feasibility instrumentation (P-3A, plan §2 G1).

Runs one ISO's *reference* forecast across the full 2026-2050 horizon (the
horizon that, per the forecast-driver audit plan §2 testing-audit G1, has never
been solved end-to-end), captures per-year wall time and peak RSS, then scores
the I1-I14 forecast invariants over the completed run. It writes a single
``full_horizon_summary.json`` beside the cached run so the six per-ISO
invocations can be collated into one findings report.

This is a *forecast probe*: ``mode="forecast"``, every ScenarioConfig field at
its default (so ``use_campd_bins=True`` gives each ISO its own per-plant CAMPD
bins where an artifact exists — the ISO default), plus the two P-3A pins:

  * ``capacity_market_clearing=False`` — the P-2A recommendation (the flip is
    unvalidated; NOT an A/B this pass).
  * ``start_year``/``end_year`` = the requested window (default 2026-2050).

Nothing here tunes anything or changes a threshold (findings only, rules
1/11/14). It solves years sequentially inside one invocation (rule 12); the
caller runs at most two ISO invocations concurrently, each with its own
``--out-dir``.

Memory: per-plant multi-zone forecast years are RAM-heavy and OOM without a
glibc arena cap (precedent: the NEISO/PJM/MISO per-plant probes). Launch with
``MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1`` when running
two concurrently on a small box.

Usage::

    MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
        python scripts/run_full_horizon.py --iso ERCOT \
        --out-dir results/full-horizon/ercot 2>&1 | tee results/full-horizon/ercot.log
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import traceback
from pathlib import Path

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.results import cache as cachemod  # noqa: E402
from scripts import check_forecast_invariants as C  # noqa: E402


# --------------------------------------------------------------------------- #
# RSS sampling + per-year timing
# --------------------------------------------------------------------------- #
def _read_rss_mb() -> float:
    """Current process resident set size in MB, from /proc/self/status."""
    try:
        with open("/proc/self/status", "r") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0  # kB -> MB
    except OSError:
        pass
    return 0.0


class Sampler:
    """Background RSS sampler: records (monotonic_time, rss_mb) every interval."""

    def __init__(self, interval: float = 0.5):
        self.interval = interval
        self.samples: list[tuple[float, float]] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def _loop(self) -> None:
        while not self._stop.is_set():
            self.samples.append((time.monotonic(), _read_rss_mb()))
            self._stop.wait(self.interval)

    def start(self) -> None:
        self.samples.append((time.monotonic(), _read_rss_mb()))
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)
        self.samples.append((time.monotonic(), _read_rss_mb()))

    def peak_between(self, t0: float, t1: float) -> float:
        vals = [rss for (t, rss) in self.samples if t0 < t <= t1]
        return max(vals) if vals else 0.0

    @property
    def global_peak(self) -> float:
        return max((rss for (_, rss) in self.samples), default=0.0)


# --------------------------------------------------------------------------- #
# Reference forecast config
# --------------------------------------------------------------------------- #
# §2.1b window cap (the owner's "10-hour rule", 2026-07-19). A forecast/hindcast
# invocation launched under the Forecast Finalization Program may span at most
# this many solve-years unless --full-solve-authorized is passed (the FF-3E
# schedulability guard, mirroring run_calibration_full.py's rule-22 gate).
MAX_UNAUTHORIZED_SOLVE_YEARS = 5


def assert_schedulable(
    start_year: int, end_year: int, full_solve_authorized: bool
) -> int:
    """Enforce the §2.1b window cap; return the solve-year count.

    A forecast run solves every year in the closed window, so the solve-year
    count is ``end - start + 1``. A window wider than
    :data:`MAX_UNAUTHORIZED_SOLVE_YEARS` is REFUSED (``SystemExit``) unless the
    owner authorized the full-horizon campaign for this ISO
    (``full_solve_authorized``) — the FF-3E schedulability guard mirroring
    ``run_calibration_full.py``'s rule-22 ``--holdout-authorized`` gate (plan
    §2.1b / §2.4-0 / §7.9). Extracted as a pure function so the guard is
    unit-testable without a solve.

    Args:
        start_year: First solve year.
        end_year: Last solve year (inclusive).
        full_solve_authorized: Whether the owner authorized a > 5-year window.

    Returns:
        The number of solve-years in the window.

    Raises:
        SystemExit: When the window exceeds the cap and is unauthorized.
    """
    n_solve_years = end_year - start_year + 1
    if n_solve_years > MAX_UNAUTHORIZED_SOLVE_YEARS and not full_solve_authorized:
        raise SystemExit(
            f"REFUSING full-horizon solve: {start_year}-{end_year} is "
            f"{n_solve_years} solve-years, over the §2.1b cap of "
            f"{MAX_UNAUTHORIZED_SOLVE_YEARS}. The schedulable instruments are T0, "
            f"T1-F (2026-2030), T1-X (2023-2027), T1-H (2021-2025) — all ≤5 yr. "
            f"T2/T3/golden/W4-campaign windows are DEFERRED until the owner opens "
            f"the gate for this ISO (plan §2.1b: backcast keeper + calibration-"
            f"complete marker, green T1 POC gates, crossover gap + FF-3E readiness "
            f"+ projected cost, and explicit per-campaign owner authorization). "
            f"Pass --full-solve-authorized ONLY when that authorization exists."
        )
    return n_solve_years


def reference_config(
    iso: str, start_year: int, end_year: int, cmc: bool, golden_posture: bool = False
) -> ScenarioConfig:
    """The P-3A reference forecast: all defaults, forecast mode, P-2A pins.

    Every field except mode/iso/horizon/capacity_market_clearing is left at the
    ScenarioConfig default, so ``use_campd_bins=True`` yields each ISO's own
    per-plant CAMPD bins where an artifact exists (the ISO default). The FF-1F /
    FF-2A default flips (``datacenter_load_path="mid"``,
    ``correlated_forced_outage=True``, ``entry_lookahead_reprice=True``) are the
    ScenarioConfig defaults and therefore already active here (plan §2.1a c/d/e).

    ``golden_posture`` (FF-3E) layers on the ONE §2.1a decision the defaults do
    NOT carry: decision (a), per-ISO capacity-market clearing ON for every ISO
    with a real capacity market (PJM/MISO/NYISO/NEISO/CAISO; energy-only ERCOT
    stays OFF). Executed here through ``capacity_market_clearing_by_iso`` (the
    FF-2C per-ISO seam), so a golden solve launched through this runner takes the
    frozen §2.1a posture instead of the pre-flip probe posture. Default False =
    byte-identical to the P-3A probe (the field stays ``None``); the constant is
    imported lazily from the FF-3E battery, the single authoritative encoding of
    the §2.1a decision, so this module's import time is unchanged.
    """
    cmc_by_iso = None
    if golden_posture:
        from scripts.ff_readiness_battery import GOLDEN_CMC_BY_ISO

        cmc_by_iso = dict(GOLDEN_CMC_BY_ISO)
    return ScenarioConfig(
        iso=iso.upper(),
        mode="forecast",
        start_year=start_year,
        end_year=end_year,
        capacity_market_clearing=cmc,
        capacity_market_clearing_by_iso=cmc_by_iso,
    )


# --------------------------------------------------------------------------- #
# Trajectory extraction (findings only — reconstructs, never tunes)
# --------------------------------------------------------------------------- #
SCARCITY_THRESHOLDS = (100.0, 500.0, 1000.0, 2000.0)


def _co2_tons(yd: "C.YearData") -> float | None:
    """Annual CO2 tons; reconstruct from context rate when the array is absent.

    The forecast path's DispatchResult carries no populated ``emissions`` array
    (a downstream/backcast step), so mirror golden_forecast_bands: dispatch ×
    the fleet context's per-generator emission rate (tCO2/MWh).
    """
    direct = C._annual_co2_tons(yd)
    if direct is not None:
        return direct
    if (
        yd.context is not None
        and getattr(yd.context, "emission_rate", None) is not None
    ):
        rate = np.asarray(yd.context.emission_rate, dtype=float)
        gen_mwh = np.asarray(yd.result.dispatch, dtype=float).sum(axis=1)
        if rate.shape == gen_mwh.shape:
            return float((gen_mwh * rate).sum())
    return None


def _system_hourly_price(yd: "C.YearData") -> np.ndarray:
    """Load-weighted system price per hour (falls back to zone mean)."""
    p = np.asarray(yd.result.prices, dtype=float)  # (n_zones, T)
    if yd.demand is not None:
        d = np.asarray(yd.demand, dtype=float)  # (n_zones, T)
        den = d.sum(axis=0)
        den = np.where(den > 0, den, 1.0)
        return (p * d).sum(axis=0) / den
    return p.mean(axis=0)


def _capacity_by_fuel(yd: "C.YearData") -> dict[str, float]:
    ctx = yd.context
    out: dict[str, float] = {}
    if ctx is None:
        return out
    for fuel, mw in zip(ctx.fuel_types, ctx.pmax_mw):
        out[fuel] = out.get(fuel, 0.0) + float(mw)
    out["wind"] = out.get("wind", 0.0) + float(getattr(ctx, "wind_cap_mw", 0.0))
    out["solar"] = out.get("solar", 0.0) + float(getattr(ctx, "solar_cap_mw", 0.0))
    return out


def extract_trajectory(run: "C.Run") -> list[dict]:
    """Per-year headline trajectory metrics for the findings tables."""
    rows: list[dict] = []
    for year in run.solved_years:
        yd = run.years[year]
        led = run.ledgers.get(year, {})
        price_h = _system_hourly_price(yd)
        scar = {
            f"hours_ge_{int(th)}": int((price_h >= th).sum())
            for th in SCARCITY_THRESHOLDS
        }
        co2 = _co2_tons(yd)
        cap = _capacity_by_fuel(yd)
        thermal = sum(mw for f, mw in cap.items() if f in C.THERMAL_FUELS)
        firm_clean = sum(mw for f, mw in cap.items() if f in C.FIRM_CLEAN_FUELS)
        vre = cap.get("wind", 0.0) + cap.get("solar", 0.0)

        def _sum_ledger(key: str, mwkey: str = "mw") -> float:
            return float(sum(float(r.get(mwkey, 0.0)) for r in led.get(key, [])))

        rows.append(
            {
                "year": year,
                "lw_price": round(C._load_weighted_price(yd), 3),
                "max_hourly_price": round(float(price_h.max()), 1),
                "neg_price_hour_frac": round(
                    float((np.asarray(yd.result.prices) < 0).mean()), 5
                ),
                **scar,
                "co2_mt": round(co2 / 1e6, 4) if co2 is not None else None,
                "peak_demand_mw": led.get("peak_demand_mw"),
                "reserve_margin": led.get("reserve_margin"),
                "rps_dual": led.get("rps_dual"),
                "thermal_mw": round(thermal, 1),
                "firm_clean_mw": round(firm_clean, 1),
                "vre_mw": round(vre, 1),
                "total_cap_mw": round(sum(cap.values()), 1),
                "storage_mw": round(cap.get("storage", 0.0), 1),
                "builds_thermal_mw": _sum_ledger("thermal_additions"),
                "builds_renew_mw": _sum_ledger("renewable_additions"),
                "builds_storage_mw": _sum_ledger("storage_additions"),
                "retire_mw": _sum_ledger("retirements"),
                "capacity_by_fuel_mw": {k: round(v, 1) for k, v in sorted(cap.items())},
            }
        )
    return rows


# --------------------------------------------------------------------------- #
# Instrumented solve engine (shared: reference forecast + CES campaign leg)
# --------------------------------------------------------------------------- #
def solve_and_summarize(
    config: ScenarioConfig,
    iso: str,
    out_dir: Path,
    *,
    sample_interval: float = 0.5,
    redirect_cache: bool = True,
    extra_summary: dict | None = None,
) -> dict:
    """Solve one forecast config with instrumentation, write its summary, return it.

    The shared engine behind :func:`main` (the P-3A reference forecast) and
    ``scripts/run_ces_leg.py`` (one premium-ladder leg — FF-3F): it solves
    ``config`` for ``iso`` with per-year wall/RSS sampling, scores the I1-I14
    forecast invariants and the headline trajectory over the cached years,
    writes ``<out_dir>/full_horizon_summary.json`` (the sidecar
    ``register_forecast_baseline.py`` consumes), prints the console report, and
    returns the summary dict.

    Args:
        config: A forecast ``ScenarioConfig`` (caller sets the window + posture;
            the §2.1b window cap is the caller's ``assert_schedulable`` gate).
        iso: ISO identifier.
        out_dir: Directory the ``full_horizon_summary.json`` is written to.
        sample_interval: RSS sampling period in seconds.
        redirect_cache: When True (default — ``run_full_horizon``'s behavior)
            the cache root is pointed at ``out_dir`` so an isolated reference
            solve lands under its own directory. A CES campaign leg passes
            False so its solve lands in the DEFAULT ``results/`` cache — where
            ``report_ces_campaign.py`` and the matrix bundle assemble every leg
            by ``cache_key`` (a redirected leg would be invisible to the report).
            The cache root is restored afterward either way.
        extra_summary: Optional dict merged into the summary verbatim (a leg
            records its ``case`` / ``premium_usd_per_mwh`` / ``crediting`` /
            ``campaign`` there for the CES sidecar).

    Returns:
        The summary dict (also written to disk). ``summary["error"]`` is the
        stringified solve exception or ``None``.
    """
    iso = iso.upper()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # runner binds ``save_result`` by name at import; patch it there to record
    # per-year completion timestamps.
    from market_sim import runner as runnermod

    year_marks: list[tuple[int, float]] = []
    _orig_save = runnermod.save_result
    _orig_cache_root = cachemod.CACHE_ROOT

    def _timed_save(result, config_, iso_, year, **kwargs):
        path = _orig_save(result, config_, iso_, year, **kwargs)
        # record only the final-pass save (pass_label=None) as the boundary
        if kwargs.get("pass_label") is None:
            year_marks.append((int(year), time.monotonic()))
        return path

    sampler = Sampler(interval=sample_interval)
    error = None
    cache_key = None
    if redirect_cache:
        # Point the cache root at this run's out-dir (isolated reference solve).
        cachemod.CACHE_ROOT = out_dir
    runnermod.save_result = _timed_save
    sampler.start()
    run_start = time.monotonic()
    try:
        cache_key = runnermod.run_scenario_iso(config, iso)
    except Exception as exc:  # noqa: BLE001 — capture, report, keep partials
        error = f"{type(exc).__name__}: {exc}"
        traceback.print_exc()
    finally:
        run_end = time.monotonic()
        sampler.stop()
        runnermod.save_result = _orig_save

    total_wall = run_end - run_start

    # Per-year wall + peak RSS from the recorded boundaries.
    per_year_perf: list[dict] = []
    prev_t = run_start
    for year, t in sorted(year_marks, key=lambda kv: kv[1]):
        per_year_perf.append(
            {
                "year": year,
                "wall_s": round(t - prev_t, 1),
                "peak_rss_mb": round(sampler.peak_between(prev_t, t), 1),
            }
        )
        prev_t = t

    # Locate the run dir (via the live cache root, so this resolves whether or
    # not the cache was redirected) and score invariants + trajectory.
    run_dir = (
        cachemod.get_cache_path(iso, cache_key, config.start_year).parent
        if cache_key
        else None
    )
    invariants: list[dict] = []
    trajectory: list[dict] = []
    solved_years: list[int] = []
    if run_dir and run_dir.exists():
        try:
            results = C.run_single(run_dir)
            invariants = [
                {"id": r.ident, "name": r.name, "status": r.status, "detail": r.detail}
                for r in results
            ]
        except Exception as exc:  # noqa: BLE001
            invariants = [
                {
                    "id": "LOAD",
                    "name": "invariant load",
                    "status": "FAIL",
                    "detail": f"{type(exc).__name__}: {exc}",
                }
            ]
        try:
            run = C.load_run(run_dir)
            solved_years = run.solved_years
            trajectory = extract_trajectory(run)
        except Exception:  # noqa: BLE001
            traceback.print_exc()

    # Restore the cache root now that every cache read is done (matters when the
    # engine is called more than once in a process, e.g. a leg then an assembly).
    cachemod.CACHE_ROOT = _orig_cache_root

    start_year, end_year = config.start_year, config.end_year
    summary = {
        "iso": iso,
        "start_year": start_year,
        "end_year": end_year,
        "capacity_market_clearing": bool(config.capacity_market_clearing),
        "cache_key": cache_key,
        "run_dir": str(run_dir) if run_dir else None,
        "error": error,
        "total_wall_s": round(total_wall, 1),
        "global_peak_rss_mb": round(sampler.global_peak, 1),
        "n_solved_years": len(solved_years),
        "solved_years": solved_years,
        "per_year_perf": per_year_perf,
        "invariants": invariants,
        "trajectory": trajectory,
    }
    if extra_summary:
        summary.update(extra_summary)
    summary_path = out_dir / "full_horizon_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")

    # Console report.
    print(f"\n===== {iso} {start_year}-{end_year} summary =====")
    print(
        f"  years solved: {len(solved_years)} / {end_year - start_year + 1}"
        f"  ({solved_years[:1]}..{solved_years[-1:]})"
    )
    print(
        f"  total wall: {total_wall / 60:.1f} min   global peak RSS: {sampler.global_peak / 1024:.2f} GB"
    )
    if error:
        print(f"  ERROR: {error}")
    if per_year_perf:
        med = sorted(p["wall_s"] for p in per_year_perf)[len(per_year_perf) // 2]
        maxrss = max(p["peak_rss_mb"] for p in per_year_perf)
        print(
            f"  median year wall: {med:.1f}s   max per-year peak RSS: {maxrss / 1024:.2f} GB"
        )
    n_fail = sum(1 for i in invariants if i["status"] == "FAIL")
    n_warn = sum(1 for i in invariants if i["status"] == "WARN")
    print(f"  invariants: {n_fail} FAIL, {n_warn} WARN")
    for i in invariants:
        if i["status"] in ("FAIL", "WARN"):
            print(
                f"    [{i['status']}] {i['id']:<4} {i['name']:<26} {i['detail'][:120]}"
            )
    print(f"  wrote {summary_path}")
    return summary


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--start-year", type=int, default=2026)
    ap.add_argument("--end-year", type=int, default=2050)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument(
        "--capacity-market-clearing",
        action="store_true",
        help="Flip the CR-1 sloped-curve gate on (default OFF = P-2A recommendation).",
    )
    ap.add_argument(
        "--sample-interval", type=float, default=0.5, help="RSS sampling seconds."
    )
    ap.add_argument(
        "--golden-posture",
        action="store_true",
        help=(
            "Layer the §2.1a decision-(a) per-ISO capacity-market clearing onto "
            "the config (PJM/MISO/NYISO/NEISO/CAISO curve-ON, ERCOT energy-only "
            "OFF). Off by default = the P-3A probe posture. Use for a golden solve."
        ),
    )
    ap.add_argument(
        "--full-solve-authorized",
        action="store_true",
        help=(
            "Lift the §2.1b window cap (the '10-hour rule'). Without it this "
            "runner REFUSES a window wider than 5 solve-years — the schedulable "
            "instruments are T0/T1-F/T1-X/T1-H (≤5 yr). Mirrors the rule-22 "
            "--holdout-authorized gate: a full-horizon (T2/T3/golden) solve is "
            "unschedulable until the owner authorizes it per ISO (plan §2.1b)."
        ),
    )
    args = ap.parse_args(argv)

    # §2.1b full-solve authorization gate (the FF-3E schedulability guard). No
    # forecast/hindcast invocation under this program may span > 5 solve-years
    # unless the owner has authorized the full-horizon campaign for this ISO
    # (plan §2.1b/§2.4-0, §7.9). Discipline-level enforcement, mirroring
    # run_calibration_full.py's rule-22 --holdout gate.
    assert_schedulable(args.start_year, args.end_year, args.full_solve_authorized)

    iso = args.iso.upper()
    config = reference_config(
        iso,
        args.start_year,
        args.end_year,
        args.capacity_market_clearing,
        golden_posture=args.golden_posture,
    )
    summary = solve_and_summarize(
        config,
        iso,
        args.out_dir,
        sample_interval=args.sample_interval,
        redirect_cache=True,
    )
    return 1 if summary.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
