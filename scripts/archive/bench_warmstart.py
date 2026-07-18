"""Benchmark: cold (two independent solves) vs warm-start (build once,
re-cost in place) for the calibration P0/P1 dispatch passes.

Captures the *real* ERCOT backcast LP from run_year, then times both paths
and diffs the P1 result so we can see the speedup and any numerical drift.
"""

import importlib.util
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
_REPORT = open(ROOT / "results" / "warmstart_bench.txt", "w", buffering=1)


def say(*a):
    msg = " ".join(str(x) for x in a)
    print(msg, flush=True)
    _REPORT.write(msg + "\n")


spec = importlib.util.spec_from_file_location(
    "run_calibration", ROOT / "scripts" / "run_calibration.py"
)
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)

from market_sim.model.dispatch import DispatchModel  # noqa: E402

YEAR, ISO, HOURS = 2023, "ERCOT", 8760


def iters(model):
    return model._h.getInfo().simplex_iteration_count


# --- 1. Capture the two real solve_dispatch calls from a backcast year ----
captured = []
_real = rc.solve_dispatch


def _spy(fleet, demand, **kwargs):
    captured.append((fleet, demand, dict(kwargs)))
    return _real(fleet, demand, **kwargs)


rc.solve_dispatch = _spy
say(f"Capturing real {ISO} {YEAR} LP ({HOURS}h) ...")
t = time.perf_counter()
gas = rc._henry_hub_actual(rc._load_reference(), YEAR)
rc.run_year(YEAR, ISO, HOURS, gas, {"ttc_wn": None, "ttc_wsc": None, "ttc_pn": None})
rc.solve_dispatch = _real
say(f"  capture run_year wall: {time.perf_counter() - t:.1f}s")

assert len(captured) == 2, f"expected P0+P1, got {len(captured)} solves"
(fleet, demand, kw0), (_, _, kw1) = captured
mc0, mc1 = kw0.pop("mc"), kw1.pop("mc")
build_kw = kw0  # identical to kw1 sans mc
assert set(kw0) == set(kw1)
say(f"  max |mc_bid - mc_base| = {float(np.abs(mc1 - mc0).max()):.3f} $/MWh\n")

# --- 2. COLD path: two independent builds + cold solves -------------------
say("COLD path (current: two independent builds, both cold)")
t = time.perf_counter()
m0 = DispatchModel(fleet, demand, **build_kw)
r0c = m0.solve(mc=mc0)
m1 = DispatchModel(fleet, demand, **build_kw)
p1_cold = m1.solve(mc=mc1)
cold_wall = time.perf_counter() - t
cold_p1_iters = iters(m1)
say(f"  P0 build {r0c.build_time:5.2f}s  solve {r0c.solve_time:5.2f}s")
say(
    f"  P1 build {p1_cold.build_time:5.2f}s  solve {p1_cold.solve_time:5.2f}s"
    f"  ({cold_p1_iters} iters)"
)
say(f"  total wall: {cold_wall:.2f}s\n")
del m0, m1

# --- 3. WARM path: build once, P0 cold, P1 warm-started -------------------
say("WARM path (build once, re-cost P1 in place)")
t = time.perf_counter()
model = DispatchModel(fleet, demand, **build_kw)
r0w = model.solve(mc=mc0)
warm_p0_iters = iters(model)
p1_warm = model.solve(mc=mc1)
warm_p1_iters = iters(model)
warm_wall = time.perf_counter() - t
say(f"  build         {model.build_time:5.2f}s")
say(f"  P0 cold solve {r0w.solve_time:5.2f}s  ({warm_p0_iters} iters)")
say(f"  P1 warm solve {p1_warm.solve_time:5.2f}s  ({warm_p1_iters} iters)")
say(f"  total wall: {warm_wall:.2f}s\n")

# --- 4. Speedup ------------------------------------------------------------
say("=" * 60)
say(
    f"P1 simplex iters:  cold {cold_p1_iters}  ->  warm {warm_p1_iters}  "
    f"({cold_p1_iters / max(warm_p1_iters, 1):.1f}x fewer)"
)
say(
    f"wall time:  cold {cold_wall:.1f}s  ->  warm {warm_wall:.1f}s  "
    f"({cold_wall / warm_wall:.2f}x faster)"
)
say("=" * 60)


# --- 5. Numerical diff: cold-P1 vs warm-P1 --------------------------------
def cmp(name, a, b):
    if a is None and b is None:
        return
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    d = float(np.abs(a - b).max())
    denom = float(np.abs(a).max()) or 1.0
    say(f"  {name:18s} max|Δ| = {d:.3e}   rel = {d / denom:.2e}")


say("\nP1 numerical diff (cold vs warm):")
obj_d = abs(p1_cold.objective_value - p1_warm.objective_value)
say(
    f"  objective          cold {p1_cold.objective_value:.6e}  "
    f"warm {p1_warm.objective_value:.6e}  Δ = {obj_d:.3e} "
    f"(rel {obj_d / abs(p1_cold.objective_value):.2e})"
)
cmp("dispatch (MW)", p1_cold.dispatch, p1_warm.dispatch)
cmp("prices ($/MWh)", p1_cold.prices, p1_warm.prices)
cmp("wind", p1_cold.wind_dispatched, p1_warm.wind_dispatched)
cmp("solar", p1_cold.solar_dispatched, p1_warm.solar_dispatched)
cmp("storage_dis", p1_cold.storage_discharge, p1_warm.storage_discharge)
cmp("slack", p1_cold.slack, p1_warm.slack)

gen_cold = p1_cold.dispatch.sum(axis=1) / 1e6
gen_warm = p1_warm.dispatch.sum(axis=1) / 1e6
say(
    f"\n  per-generator annual TWh  max|Δ| = "
    f"{float(np.abs(gen_cold - gen_warm).max()):.3e} TWh"
)
say(
    f"  total gen  cold {gen_cold.sum():.4f} TWh  warm {gen_warm.sum():.4f} TWh"
    f"  Δ = {abs(gen_cold.sum() - gen_warm.sum()):.3e}"
)
say("\nDONE")
_REPORT.close()
