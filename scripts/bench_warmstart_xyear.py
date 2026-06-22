"""Benchmark: cold vs CROSS-YEAR warm-start for the calibration P0 solve.

Intra-year warm-start (build once, re-cost P1 from P0's basis) already makes the
P1 second solve cheap, so the one cold solve left in each year is P0. This times
the alternative where each year's P0 warm-starts from the *previous year's*
optimal basis, remapped onto the new fleet (DispatchModel.apply_cross_year_basis,
option (c): map the basis, do not grow the LP).

It captures the real ERCOT backcast LP for three consecutive years once (pickled
to results/), then runs two paths over those years:

  COLD   : each year builds a fresh DispatchModel, solves P0 cold + P1 warm.
  XWARM  : each year builds a fresh DispatchModel, applies the prior year's
           basis to P0, then solves P0 + P1. The basis is carried year to year.

and reports per-year and total wall clock, the P0 simplex-iteration reduction,
peak RSS, the union ("superset", option (a)) fleet size for the memory tradeoff,
and the per-plant annual-MWh / zonal-price drift between the two P1 solutions.

Usage:
    MARKET_SIM_WARMSTART=0 python scripts/bench_warmstart_xyear.py
    (the env var only affects the capture run; the bench builds models directly)
"""

import importlib.util
import os
import pickle
import resource
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)
CACHE = RESULTS / "warmstart_xyear_capture.pkl"
_REPORT = open(RESULTS / "warmstart_xyear_bench.txt", "w", buffering=1)

YEARS = [2023, 2024, 2025]
ISO, HOURS = "ERCOT", 8760


def say(*a):
    msg = " ".join(str(x) for x in a)
    print(msg, flush=True)
    _REPORT.write(msg + "\n")


def _load_rc():
    spec = importlib.util.spec_from_file_location(
        "run_calibration", ROOT / "scripts" / "run_calibration.py"
    )
    rc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rc)
    return rc


def capture():
    """Run run_year per year, spying on solve_dispatch to grab the real LP.

    Requires MARKET_SIM_WARMSTART=0 so both P0 and P1 go through solve_dispatch.
    Pickles {year: (fleet, demand, build_kw, mc0, mc1)} so the bench is repeatable.
    """
    rc = _load_rc()
    out = {}
    real = rc.solve_dispatch
    for year in YEARS:
        captured = []

        def spy(fleet, demand, **kwargs):
            captured.append((fleet, demand, dict(kwargs)))
            return real(fleet, demand, **kwargs)

        rc.solve_dispatch = spy
        say(f"capturing {ISO} {year} ({HOURS}h) ...")
        t = time.perf_counter()
        gas = rc._henry_hub_actual(rc._load_reference(), year)
        rc.run_year(
            year, ISO, HOURS, gas, {"ttc_wn": None, "ttc_wsc": None, "ttc_pn": None}
        )
        rc.solve_dispatch = real
        say(f"  capture wall {time.perf_counter() - t:.1f}s, {len(captured)} solves")
        assert len(captured) == 2, f"expected P0+P1, got {len(captured)}"
        (fleet, demand, kw0), (_, _, kw1) = captured
        mc0, mc1 = kw0.pop("mc"), kw1.pop("mc")
        assert set(kw0) == set(kw1)
        out[year] = (fleet, demand, kw0, mc0, mc1)
    with open(CACHE, "wb") as fh:
        pickle.dump(out, fh)
    return out


def peak_rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024**2)


def iters(model):
    return model._h.getInfo().simplex_iteration_count


def run():
    from market_sim.model.dispatch import DispatchModel

    if CACHE.exists():
        say(f"loading captured LPs from {CACHE.name}")
        with open(CACHE, "rb") as fh:
            data = pickle.load(fh)
    else:
        data = capture()

    # LP dimensions + the union ("superset", option (a)) fleet, for the memory
    # tradeoff: option (a) would carry one matrix sized to every unit that ever
    # runs; option (c) (shipped) keeps each year's own, smaller matrix.
    say("\n" + "=" * 68)
    say("LP size per year and the option-(a) superset cost")
    say("=" * 68)
    union_units = set()
    n_gen_by_year = {}
    for year in YEARS:
        fleet, demand, kw, mc0, _ = data[year]
        union_units |= set(fleet.unit_ids)
        n_gen_by_year[year] = fleet.n_gen
        say(
            f"  {year}: n_gen={fleet.n_gen:5d}  n_zones={demand.shape[0]}  "
            f"T={demand.shape[1]}"
        )
    say(
        f"  union of units over {YEARS}: {len(union_units)}  "
        f"(max single-year {max(n_gen_by_year.values())}; "
        f"superset is +{len(union_units) - max(n_gen_by_year.values())} cols/hour, "
        f"~{100 * len(union_units) / max(n_gen_by_year.values()) - 100:.1f}% wider "
        "thermal block every hour)"
    )

    results = {}  # (path, year) -> dict
    for path in ("COLD", "XWARM"):
        say("\n" + "=" * 68)
        say(f"{path} path")
        say("=" * 68)
        prev_basis = None
        for year in YEARS:
            fleet, demand, kw, mc0, mc1 = data[year]
            t = time.perf_counter()
            model = DispatchModel(fleet, demand, **kw)
            build_t = time.perf_counter() - t
            applied = False
            if path == "XWARM" and prev_basis is not None:
                applied = model.apply_cross_year_basis(prev_basis)
            t = time.perf_counter()
            model.solve(mc=mc0)
            p0_solve = time.perf_counter() - t
            p0_iters = iters(model)
            t = time.perf_counter()
            r1 = model.solve(mc=mc1)
            p1_solve = time.perf_counter() - t
            p1_iters = iters(model)
            prev_basis = model.export_cross_year_basis()
            wall = build_t + p0_solve + p1_solve
            results[(path, year)] = dict(
                build=build_t,
                p0=p0_solve,
                p0_iters=p0_iters,
                p1=p1_solve,
                p1_iters=p1_iters,
                wall=wall,
                applied=applied,
                fleet=fleet,
                r1=r1,
            )
            say(
                f"  {year}: build {build_t:6.2f}s  P0 {p0_solve:6.2f}s "
                f"({p0_iters:6d} it{' warm' if applied else ' cold'})  "
                f"P1 {p1_solve:6.2f}s ({p1_iters:5d} it)  wall {wall:6.2f}s"
            )
            del model
        say(f"  peak RSS so far: {peak_rss_gb():.2f} GB")

    # --- Speedup table -----------------------------------------------------
    say("\n" + "=" * 68)
    say("SPEEDUP  (cross-year warm vs cold; P0 is the solve that changes)")
    say("=" * 68)
    say(
        f"  {'year':>6} {'P0 cold':>9} {'P0 warm':>9} {'iters c':>9} "
        f"{'iters w':>9} {'P0 x':>6} {'wall c':>8} {'wall w':>8} {'wall x':>7}"
    )
    tot_p0c = tot_p0w = tot_wc = tot_ww = 0.0
    for year in YEARS:
        c, w = results[("COLD", year)], results[("XWARM", year)]
        tot_p0c += c["p0"]
        tot_p0w += w["p0"]
        tot_wc += c["wall"]
        tot_ww += w["wall"]
        say(
            f"  {year:>6} {c['p0']:9.2f} {w['p0']:9.2f} {c['p0_iters']:9d} "
            f"{w['p0_iters']:9d} {c['p0'] / max(w['p0'], 1e-9):6.2f} "
            f"{c['wall']:8.2f} {w['wall']:8.2f} {c['wall'] / max(w['wall'], 1e-9):7.2f}"
        )
    say(
        f"  {'TOTAL':>6} {tot_p0c:9.2f} {tot_p0w:9.2f} {'':9} {'':9} "
        f"{tot_p0c / max(tot_p0w, 1e-9):6.2f} {tot_wc:8.2f} {tot_ww:8.2f} "
        f"{tot_wc / max(tot_ww, 1e-9):7.2f}"
    )
    say(f"\n  peak RSS: {peak_rss_gb():.2f} GB")

    # --- Neutrality: per-plant annual MWh + zonal price drift (P1) ----------
    say("\n" + "=" * 68)
    say("NEUTRALITY  (P1 cold vs P1 cross-year-warm)")
    say("=" * 68)
    for year in YEARS:
        c, w = results[("COLD", year)], results[("XWARM", year)]
        rc_, rw_ = c["r1"], w["r1"]
        fleet = c["fleet"]
        # Per-plant annual MWh.
        codes = np.asarray(fleet.plant_code)
        gen_c = rc_.dispatch.sum(axis=1)
        gen_w = rw_.dispatch.sum(axis=1)
        uniq = np.unique(codes)
        plant_c = np.array([gen_c[codes == p].sum() for p in uniq])
        plant_w = np.array([gen_w[codes == p].sum() for p in uniq])
        dmwh = np.abs(plant_c - plant_w)
        dprice = np.abs(rc_.prices - rw_.prices)
        obj_rel = abs(rc_.objective_value - rw_.objective_value) / abs(
            rc_.objective_value
        )
        say(
            f"  {year}: obj rel Δ {obj_rel:.2e}  "
            f"max per-plant |Δ annual MWh| {dmwh.max():.3e}  "
            f"max |Δ zonal price| {dprice.max():.3e} $/MWh  "
            f"total gen Δ {abs(plant_c.sum() - plant_w.sum()):.3e} MWh"
        )
    say("\nDONE")
    _REPORT.close()


if __name__ == "__main__":
    if os.environ.get("CAPTURE_ONLY") == "1":
        capture()
    else:
        run()
