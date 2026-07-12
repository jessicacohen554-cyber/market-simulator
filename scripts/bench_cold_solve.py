"""Bench-first HiGHS cold-first-solve experiments (wallclock-baseline-2026-07).

Three bounded experiments on *real captured* ISO-year LPs. BENCH-FIRST: this
script only measures and writes ``results/`` + the handoff doc; it changes NO
model defaults. Each experiment is scored against the adoption rule
(>=10% cold-solve wall improvement AND objective/prices identical) by the
operator reading the printed report.

Experiments
-----------
1. ``exp1`` IPM+crossover for the cold P0 vs the dual-simplex baseline: times
   the first (cold) solve of a year and the P1 warm-start iteration count when
   P1 warm-starts from the crossover basis. Only ``solver``/``run_crossover``
   are touched — never the primal/dual feasibility tolerances.
2. ``exp2`` cross-year ``setBasis`` apply overhead: the current per-element
   ``HighsBasisStatus(int(s))`` list materialization vs a memoized-enum lookup
   (and confirms whether the installed highspy accepts array input at all).
3. ``exp3`` ``MARKET_SIM_HIGHS_THREADS`` in {1, 4, unset}: cold-P0 wall + peak
   RSS, measured one model per isolated subprocess.

Capture seam
------------
The real LP is captured by monkeypatching ``market_sim.pipeline.solve``'s
``solve_dispatch`` under ``MARKET_SIM_WARMSTART=0`` (so both P0 and P1 route
through it), grabbing ``(fleet, demand, build_kwargs, mc_base, mc_bid)`` and
pickling it. The bench then rebuilds ``DispatchModel(fleet, demand, **build_kw)``
directly — identical to the production LP.

Usage
-----
    # capture (heavy; run in background). --coopt engages per-unit reserve co-opt.
    python scripts/bench_cold_solve.py capture --iso ERCOT --year 2023
    python scripts/bench_cold_solve.py capture --iso PJM   --year 2024 --coopt

    python scripts/bench_cold_solve.py exp1 --iso ERCOT --year 2023
    python scripts/bench_cold_solve.py exp3 --iso PJM   --year 2024 --coopt
    python scripts/bench_cold_solve.py exp2 --iso ERCOT --years 2023 2024
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import os
import pickle
import resource
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)
HOURS = 8760


def _cap_path(iso: str, year: int, coopt: bool) -> Path:
    tag = f"{iso}_{year}{'_coopt' if coopt else ''}"
    return RESULTS / f"bench_capture_{tag}.pkl"


def peak_rss_gb() -> float:
    """Process peak resident set (ru_maxrss is monotonic, KiB on Linux)."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024**2)


def vm_hwm_gb() -> float:
    """VmHWM (peak RSS) from /proc/self/status, in GiB."""
    with open("/proc/self/status") as fh:
        for line in fh:
            if line.startswith("VmHWM"):
                return int(line.split()[1]) / (1024**2)
    return float("nan")


def _load_rc():
    spec = importlib.util.spec_from_file_location(
        "run_calibration", ROOT / "scripts" / "run_calibration.py"
    )
    rc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rc)
    return rc


# --------------------------------------------------------------------------- #
# Capture                                                                      #
# --------------------------------------------------------------------------- #
def capture(iso: str, year: int, coopt: bool) -> dict:
    """Run ``run_year`` once, spying on the pipeline ``solve_dispatch`` to grab
    the real P0/P1 LP, and pickle ``(fleet, demand, build_kw, mc0, mc1)``.

    ``MARKET_SIM_WARMSTART=0`` forces both passes through ``solve_dispatch``.
    ``coopt`` passes ``energy_reserve_coopt=True`` so the LP carries the per-unit
    reserve columns + balance rows (the "big co-opt ISO" structure).
    """
    os.environ["MARKET_SIM_WARMSTART"] = "0"
    import market_sim.pipeline.solve as solve_mod

    rc = _load_rc()
    captured: list = []
    real = solve_mod.solve_dispatch

    def spy(fleet, demand, **kwargs):
        captured.append((fleet, demand, dict(kwargs)))
        return real(fleet, demand, **kwargs)

    solve_mod.solve_dispatch = spy
    # Co-opt flavor is ISO-specific (the flag that adds reserve columns/rows to
    # the LP). PJM uses the generic per-unit energy+reserve co-opt; MISO uses its
    # zonal measured-reserve co-opt (matches the baseline doc's MISO table).
    # ``energy_reserve_coopt`` is the single gate apply_reserve_coopt / the PJM
    # per-unit path both require (kwargs.py:138, commitment.py:512). MISO's
    # _miso_design always builds the market-wide RBDC family from fleet MSSC
    # (no external-data dependency), so this alone gives a real co-opt LP.
    extra = {"energy_reserve_coopt": True} if coopt else {}
    print(
        f"capturing {iso} {year} ({HOURS}h){' +coopt' if coopt else ''} ...", flush=True
    )
    t = time.perf_counter()
    gas = rc._henry_hub_actual(rc._load_reference(), year)
    rc.run_year(
        year,
        iso,
        HOURS,
        gas,
        {"ttc_wn": None, "ttc_wsc": None, "ttc_pn": None},
        **extra,
    )
    solve_mod.solve_dispatch = real
    print(
        f"  capture wall {time.perf_counter() - t:.1f}s, {len(captured)} solves,"
        f" peak RSS {peak_rss_gb():.2f} GB",
        flush=True,
    )
    assert len(captured) >= 2, f"expected >=2 (P0+P1) solves, got {len(captured)}"
    (fleet, demand, kw0), (_, _, kw1) = captured[0], captured[1]
    mc0, mc1 = kw0.pop("mc"), kw1.pop("mc")
    out = dict(
        fleet=fleet,
        demand=demand,
        build_kw=kw0,
        mc0=mc0,
        mc1=mc1,
        iso=iso,
        year=year,
        coopt=coopt,
        n_gen=int(fleet.n_gen),
    )
    path = _cap_path(iso, year, coopt)
    with open(path, "wb") as fh:
        pickle.dump(out, fh)
    print(
        f"  n_gen={fleet.n_gen}  n_zones={demand.shape[0]}  T={demand.shape[1]}"
        f"  |mc1-mc0|max={float(np.abs(mc1 - mc0).max()):.3f}",
        flush=True,
    )
    print(f"  wrote {path.name} ({path.stat().st_size / 1e6:.0f} MB)", flush=True)
    return out


def _load_capture(iso: str, year: int, coopt: bool) -> dict:
    path = _cap_path(iso, year, coopt)
    if not path.exists():
        raise SystemExit(
            f"no capture at {path} — run: capture --iso {iso} "
            f"--year {year}{' --coopt' if coopt else ''}"
        )
    with open(path, "rb") as fh:
        return pickle.load(fh)


def _simplex_iters(model) -> int:
    return model._h.getInfo().simplex_iteration_count


def _ipm_iters(model) -> int:
    try:
        return model._h.getInfo().ipm_iteration_count
    except Exception:
        return -1


def _prices_obj(res):
    return float(res.objective_value), np.asarray(res.prices, dtype=float)


def _diff(a_obj, a_px, b_obj, b_px):
    obj_rel = abs(a_obj - b_obj) / max(abs(a_obj), 1.0)
    px_max = float(np.abs(a_px - b_px).max())
    px_den = float(np.abs(a_px).max()) or 1.0
    return obj_rel, px_max, px_max / px_den


# --------------------------------------------------------------------------- #
# Experiment 1: IPM + crossover for the cold P0                               #
# --------------------------------------------------------------------------- #
def exp1(iso: str, year: int, coopt: bool) -> None:
    import highspy

    from market_sim.model.dispatch import DispatchModel

    cap = _load_capture(iso, year, coopt)
    fleet, demand, kw = cap["fleet"], cap["demand"], cap["build_kw"]
    mc0, mc1 = cap["mc0"], cap["mc1"]
    print("=" * 72)
    print(
        f"EXP1  IPM+crossover cold-P0  {iso} {year}"
        f"{' +coopt' if coopt else ''}  n_gen={cap['n_gen']}"
    )
    print("=" * 72)

    # --- Baseline: dual simplex (production default) ----------------------- #
    t = time.perf_counter()
    m = DispatchModel(fleet, demand, **kw)
    b_build = time.perf_counter() - t
    t = time.perf_counter()
    r0 = m.solve(mc=mc0)
    b_p0_wall = time.perf_counter() - t
    b_p0_iters = _simplex_iters(m)
    t = time.perf_counter()
    p1 = m.solve(mc=mc1)
    b_p1_wall = time.perf_counter() - t
    b_p1_iters = _simplex_iters(m)
    b_p0_obj, b_p0_px = _prices_obj(r0)
    b_p1_obj, b_p1_px = _prices_obj(p1)
    print("  baseline (dual simplex):")
    print(
        f"    build {b_build:6.2f}s  P0 cold {b_p0_wall:6.2f}s "
        f"({b_p0_iters} simplex it)  P1 warm {b_p1_wall:6.2f}s "
        f"({b_p1_iters} it)"
    )
    del m, r0, p1
    gc.collect()

    # --- IPM + crossover for the FIRST solve only -------------------------- #
    # Optional wall-clock cap on the IPM solve so a pathological crossover on a
    # degenerate 1.8M-col LP cannot run away (env seconds; 0/unset = unlimited).
    ipm_cap = float(os.environ.get("MARKET_SIM_BENCH_IPM_TIMELIMIT", "0") or 0)
    t = time.perf_counter()
    m = DispatchModel(fleet, demand, **kw)
    i_build = time.perf_counter() - t
    h = m._h
    # Cold P0 via interior point + crossover to a vertex basis. Crossover is
    # required so P1 can warm-start (an interior point has no basis) and so the
    # duals/prices are the same well-defined vertex the simplex reports.
    h.setOptionValue("solver", "ipm")
    h.setOptionValue("run_crossover", "on")
    if ipm_cap > 0:
        h.setOptionValue("time_limit", ipm_cap)
    i_converged = True
    t = time.perf_counter()
    try:
        r0 = m.solve(mc=mc0)
    except RuntimeError as e:  # time-limit / no optimal basis
        i_converged = False
        i_p0_wall = time.perf_counter() - t
        print(
            f"  IPM+crossover: DID NOT CONVERGE within {ipm_cap:.0f}s cap "
            f"(elapsed {i_p0_wall:.1f}s) — {e}"
        )
    if i_converged:
        i_p0_wall = time.perf_counter() - t
        i_p0_ipm_iters = _ipm_iters(m)
        if ipm_cap > 0:
            h.setOptionValue("time_limit", highspy.kHighsInf)
        # Hand the crossover basis to the existing P1 warm-start (changeColsCost).
        h.setOptionValue("solver", "simplex")
        t = time.perf_counter()
        p1 = m.solve(mc=mc1)
        i_p1_wall = time.perf_counter() - t
        i_p1_iters = _simplex_iters(m)
        i_p0_obj, i_p0_px = _prices_obj(r0)
        i_p1_obj, i_p1_px = _prices_obj(p1)
        print("  IPM+crossover:")
        print(
            f"    build {i_build:6.2f}s  P0 cold {i_p0_wall:6.2f}s "
            f"({i_p0_ipm_iters} ipm it + crossover)  P1 warm {i_p1_wall:6.2f}s "
            f"({i_p1_iters} it)"
        )
    del m
    gc.collect()

    # --- Verdict ----------------------------------------------------------- #
    print("-" * 72)
    if not i_converged:
        mult = i_p0_wall / b_p0_wall if b_p0_wall else float("inf")
        print(
            f"  cold-P0 solve wall:  base {b_p0_wall:.2f}s -> ipm "
            f"HIT {ipm_cap:.0f}s CAP (>= {mult:.1f}x, unconverged)"
        )
        print(
            "  ADOPT? NO  (IPM+crossover did not converge within the cap; "
            "dual-simplex baseline is far faster)"
        )
        print("=" * 72, flush=True)
        return
    p0_gain = (b_p0_wall - i_p0_wall) / b_p0_wall * 100.0
    cold_wall_base = b_build + b_p0_wall  # "cold solve" = build + first solve
    cold_wall_ipm = i_build + i_p0_wall
    cold_gain = (cold_wall_base - cold_wall_ipm) / cold_wall_base * 100.0
    p0_obj_rel, p0_px_max, p0_px_rel = _diff(b_p0_obj, b_p0_px, i_p0_obj, i_p0_px)
    p1_obj_rel, p1_px_max, p1_px_rel = _diff(b_p1_obj, b_p1_px, i_p1_obj, i_p1_px)
    print(
        f"  cold-P0 solve wall:  base {b_p0_wall:.2f}s -> ipm {i_p0_wall:.2f}s "
        f"({p0_gain:+.1f}%)"
    )
    print(
        f"  cold  build+P0 wall: base {cold_wall_base:.2f}s -> ipm "
        f"{cold_wall_ipm:.2f}s ({cold_gain:+.1f}%)"
    )
    print(f"  P1 warm iters:  base {b_p1_iters} -> ipm-basis {i_p1_iters}")
    print(
        f"  P0 identity: obj rel {p0_obj_rel:.2e}  max|Δprice| {p0_px_max:.3e} "
        f"(rel {p0_px_rel:.2e})"
    )
    print(
        f"  P1 identity: obj rel {p1_obj_rel:.2e}  max|Δprice| {p1_px_max:.3e} "
        f"(rel {p1_px_rel:.2e})"
    )
    adopt = p0_gain >= 10.0 and p1_obj_rel < 1e-6 and p1_px_max < 1e-3
    print(
        f"  ADOPT? {'YES' if adopt else 'NO'}  "
        f"(rule: cold-P0 wall >=10% AND obj/prices identical)"
    )
    print("=" * 72, flush=True)


# --------------------------------------------------------------------------- #
# Experiment 2: cross-year setBasis apply overhead                            #
# --------------------------------------------------------------------------- #
def exp2(iso: str, years: list[int], coopt: bool) -> None:
    import highspy

    from market_sim.model.dispatch import CrossYearBasis, DispatchModel

    print("=" * 72)
    print(f"EXP2  cross-year setBasis apply overhead  {iso} {years}")
    print("=" * 72)

    # Does the installed highspy accept array input for the basis at all?
    b = highspy.HighsBasis()
    accepts_array = True
    try:
        b.col_status = np.array([0, 1, 2], dtype=np.int8)
    except Exception as e:  # noqa: BLE001
        accepts_array = False
        arr_err = f"{type(e).__name__}: {e}"
    print(f"  HighsBasis.col_status accepts np.int8 array? {accepts_array}")
    if not accepts_array:
        print(f"    -> {arr_err.splitlines()[0]}")
        print(
            "    -> array input UNAVAILABLE in this highspy; fallback is the "
            "list-comp path."
        )

    # The apply hot path is a pure function of the column count and is
    # year-invariant (it re-materializes a status list of length total_columns),
    # so no solve is needed: build ONE model and hand it a synthetic prior-year
    # basis whose unit_ids match, forcing the full 1:1 remap — the most
    # expensive apply (every column mapped). Statuses mix LOWER/BASIC/UPPER.
    cap = _load_capture(iso, years[0], coopt)
    m1 = DispatchModel(cap["fleet"], cap["demand"], **cap["build_kw"])
    ncols = int(cap["fleet"].n_gen)
    total_columns = m1.layout.total_columns
    prev = CrossYearBasis(
        col_status=(np.arange(total_columns) % 3).astype(np.int8),
        row_status=(np.arange(m1._n_rows) % 2).astype(np.int8),
        layout=m1.layout,
        unit_ids=list(m1.fleet.unit_ids),
        n_rows=m1._n_rows,
        n_energy_rows=m1._n_energy_rows,
        n_storage_rows=m1._n_storage_rows,
    )
    col_status = (np.arange(total_columns) % 3).astype(np.int8)
    print(f"  total_columns = {total_columns:,}  (n_gen={ncols})")

    def _time(fn, reps=3):
        best = float("inf")
        for _ in range(reps):
            t = time.perf_counter()
            fn()
            best = min(best, time.perf_counter() - t)
        return best

    # (a) current path: construct one enum per element.
    def current():
        return [highspy.HighsBasisStatus(int(s)) for s in col_status]

    # (b) memoized-enum path: reuse the handful of enum objects via a LUT.
    _LUT = [highspy.HighsBasisStatus(i) for i in range(5)]

    def memoized():
        lut = _LUT
        return [lut[s] for s in col_status]

    t_cur = _time(current)
    t_mem = _time(memoized)
    # Byte-identity of the produced statuses (same solve either way).
    identical = all(int(x) == int(y) for x, y in zip(current(), memoized()))
    print(f"  materialize col_status list ({total_columns:,} elems), best of 3:")
    print(f"    (a) current  HighsBasisStatus(int(s)) per elem : {t_cur * 1e3:8.1f} ms")
    print(f"    (b) memoized LUT[s]                            : {t_mem * 1e3:8.1f} ms")
    gain = (t_cur - t_mem) / t_cur * 100.0 if t_cur else 0.0
    print(f"    statuses identical? {identical}   memoized gain {gain:+.1f}%")

    # Full apply overhead (both lists + setBasis) on the real cross-year basis.
    def full_apply():
        m1._n_solves = 0  # allow re-apply for timing
        return m1.apply_cross_year_basis(prev)

    t_full = _time(full_apply, reps=3)
    print(
        f"  full apply_cross_year_basis (both lists + setBasis): {t_full * 1e3:.1f} ms"
    )
    del m1
    gc.collect()
    print(
        "  NOTE: apply overhead is cross-year warm-start SETUP, not solve wall;"
        " it does not enter the >=10% cold-solve-wall adoption test."
    )
    print("=" * 72, flush=True)


# --------------------------------------------------------------------------- #
# Experiment 3: threads sweep (isolated subprocess per setting for peak RSS)  #
# --------------------------------------------------------------------------- #
def _solve_once(iso: str, year: int, coopt: bool) -> None:
    """Child mode: build one model, cold-solve P0, print wall + peak RSS.

    ``MARKET_SIM_HIGHS_THREADS`` (or its absence) is read by DispatchModel from
    the environment, so the parent sets it before spawning this child.
    """
    from market_sim.model.dispatch import DispatchModel

    cap = _load_capture(iso, year, coopt)
    thr = os.environ.get("MARKET_SIM_HIGHS_THREADS", "unset")
    t = time.perf_counter()
    m = DispatchModel(cap["fleet"], cap["demand"], **cap["build_kw"])
    build = time.perf_counter() - t
    t = time.perf_counter()
    r0 = m.solve(mc=cap["mc0"])
    p0 = time.perf_counter() - t
    obj = float(r0.objective_value)
    print(
        f"THREADS={thr}\tbuild={build:.2f}\tp0={p0:.2f}\t"
        f"peak_rss_gb={vm_hwm_gb():.3f}\tobj={obj:.8e}",
        flush=True,
    )


def exp3(iso: str, year: int, coopt: bool) -> None:
    import subprocess

    print("=" * 72)
    print(f"EXP3  threads {{1,4,unset}}  {iso} {year}{' +coopt' if coopt else ''}")
    print("=" * 72)
    rows = []
    for thr in ["unset", "1", "4"]:
        env = dict(os.environ)
        env.pop("MARKET_SIM_HIGHS_THREADS", None)
        if thr != "unset":
            env["MARKET_SIM_HIGHS_THREADS"] = thr
        cmd = [
            sys.executable,
            str(Path(__file__)),
            "_solve_once",
            "--iso",
            iso,
            "--year",
            str(year),
        ]
        if coopt:
            cmd.append("--coopt")
        out = subprocess.run(cmd, env=env, capture_output=True, text=True)
        line = [ln for ln in out.stdout.splitlines() if ln.startswith("THREADS=")]
        if not line:
            print(f"  threads={thr}: FAILED\n{out.stdout[-500:]}\n{out.stderr[-800:]}")
            continue
        rec = dict(kv.split("=", 1) for kv in line[0].split("\t"))
        rows.append(rec)
        print(
            f"  threads={rec['THREADS']:>5}  build={float(rec['build']):6.2f}s  "
            f"P0={float(rec['p0']):6.2f}s  peak_rss={float(rec['peak_rss_gb']):.2f}GB"
            f"  obj={rec['obj']}"
        )
    # Objective identity across thread settings.
    if len(rows) >= 2:
        objs = {r["THREADS"]: float(r["obj"]) for r in rows}
        base = objs.get("1", next(iter(objs.values())))
        maxrel = max(abs(o - base) / max(abs(base), 1.0) for o in objs.values())
        print("-" * 72)
        print(f"  objective identity across thread settings: max rel Δ {maxrel:.2e}")
        print(
            "  DELIVERABLE: per-ISO recommendation in docs (NOT a default change);"
            " single-thread stays the golden/repro pin."
        )
    print("=" * 72, flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("capture", "exp1", "exp3", "_solve_once"):
        p = sub.add_parser(name)
        p.add_argument("--iso", required=True)
        p.add_argument("--year", type=int, required=True)
        p.add_argument("--coopt", action="store_true")
    p2 = sub.add_parser("exp2")
    p2.add_argument("--iso", required=True)
    p2.add_argument("--years", type=int, nargs=2, required=True)
    p2.add_argument("--coopt", action="store_true")
    args = ap.parse_args()

    if args.cmd == "capture":
        capture(args.iso, args.year, args.coopt)
    elif args.cmd == "exp1":
        exp1(args.iso, args.year, args.coopt)
    elif args.cmd == "exp2":
        exp2(args.iso, args.years, args.coopt)
    elif args.cmd == "exp3":
        exp3(args.iso, args.year, args.coopt)
    elif args.cmd == "_solve_once":
        _solve_once(args.iso, args.year, args.coopt)


if __name__ == "__main__":
    main()
