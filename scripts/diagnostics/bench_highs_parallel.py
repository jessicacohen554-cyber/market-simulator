"""Bench: HiGHS ``parallel`` (PAMI parallel simplex) on the cold P0.

The one un-run HiGHS experiment from the wall-clock lane
(``docs/refactor-consolidation-plan-2026-07.md`` §7-H4,
``docs/handoffs/wallclock-baseline-2026-07.md``). It is **not** the thread
experiment: Exp 3 there swept ``MARKET_SIM_HIGHS_THREADS`` (HiGHS's
``threads`` option) and found no scaling. ``threads`` bounds how many threads
HiGHS *may* use; ``parallel`` chooses whether the simplex runs its
**parallel variant at all** (``simplex_strategy`` dual-tasks / dual-multi
"PAMI"). A thread count with no parallel algorithm engaged cannot show
scaling, which is exactly what Exp 3 measured — so the option this script
sweeps is a genuinely different lever, and its verdict is recorded as its own
numbered experiment.

BENCH-FIRST: this script measures and prints. It changes **no** model default.
``src/market_sim/model/lp/model.py`` sets only ``threads`` (from
``MARKET_SIM_HIGHS_THREADS``) and ``presolve=off``; ``parallel`` is left at
HiGHS's ``choose`` and stays that way unless a verdict here says otherwise.
Solver **tolerances are never touched**.

Adoption rule (inherited from the P-4 experiments): adopt a default change only
on **>=10 % cold-P0 wall improvement AND identical objective/prices**
(marginal-tie-only diffs). Otherwise the negative result is recorded in the
baseline doc so it is not re-run.

Input LPs are the archived captures written by
``scripts/diagnostics/bench_cold_solve.py capture`` (frozen history — read, never
edited): ``results/bench_capture_<ISO>_<year>[_coopt].pkl``, holding the real
``(fleet, demand, build_kwargs, mc0, mc1)`` off the production
``pipeline.solve`` seam.

Each setting is timed in its **own subprocess** so peak RSS is clean and no
solver state leaks between runs; the parent then compares objective and price
vectors across settings.

Usage:
    # capture first (heavy; the archived capture driver):
    PYTHONPATH=src:. python scripts/diagnostics/bench_cold_solve.py capture \\
        --iso ERCOT --year 2023

    # then bench (spawns one subprocess per setting, sequentially):
    PYTHONPATH=src:. python scripts/diagnostics/bench_highs_parallel.py \\
        --iso ERCOT --year 2023
    PYTHONPATH=src:. python scripts/diagnostics/bench_highs_parallel.py \\
        --iso MISO --year 2024 --coopt

``--setting <value>`` runs exactly one setting in-process and emits its JSON
result; that is the subprocess entry point the parent uses, not a normal
invocation.
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import resource
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS = ROOT / "results"
# The archived capture driver's naming, mirrored so this script reads the same
# files (scripts/diagnostics/bench_cold_solve.py::_cap_path).
CAPTURE_FMT = "bench_capture_{iso}_{year}{coopt}.pkl"

# HiGHS ``parallel`` values swept. ``choose`` is the production default (the
# model builder never sets the option), so it is the baseline; ``on`` forces the
# parallel simplex variant. ``off`` pins the serial variant, which isolates
# whether ``choose`` was already picking a parallel path.
SETTINGS: tuple[str, ...] = ("choose", "on", "off")


def _capture_path(iso: str, year: int, coopt: bool) -> Path:
    """Return the archived capture path for one ISO-year (see module docstring)."""
    return RESULTS / CAPTURE_FMT.format(
        iso=iso, year=year, coopt="_coopt" if coopt else ""
    )


def _peak_rss_gb() -> float:
    """Process peak resident set in GiB (``ru_maxrss`` is monotonic, KiB on Linux)."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024**2)


def run_one(iso: str, year: int, coopt: bool, setting: str, out: Path) -> dict:
    """Time one ``parallel`` setting on the captured LP; write prices to ``out``.

    Builds the production ``DispatchModel`` from the capture, sets
    ``parallel=<setting>`` on the underlying ``Highs`` handle (nothing else --
    presolve and tolerances stay exactly as the model builder left them), then
    times the **cold P0** (``mc0``) and the **warm P1** (``mc1``, warm-started
    from P0's basis, as production does).

    Args:
        iso: ISO of the capture.
        year: Year of the capture.
        coopt: Whether the capture carries reserve co-optimization rows.
        setting: HiGHS ``parallel`` value (``choose`` / ``on`` / ``off``).
        out: Path the P0 price vector is written to (``.npy``), so the parent
            can diff prices across settings.

    Returns:
        A dict of timings, simplex iteration counts, objectives and peak RSS.
    """
    from market_sim.model.dispatch import DispatchModel

    path = _capture_path(iso, year, coopt)
    if not path.exists():
        raise SystemExit(
            f"no capture at {path} -- run: scripts/diagnostics/bench_cold_solve.py "
            f"capture --iso {iso} --year {year}{' --coopt' if coopt else ''}"
        )
    with open(path, "rb") as fh:
        cap = pickle.load(fh)

    fleet, demand, kw = cap["fleet"], cap["demand"], cap["build_kw"]
    mc0, mc1 = cap["mc0"], cap["mc1"]

    t = time.perf_counter()
    model = DispatchModel(fleet, demand, **kw)
    build_s = time.perf_counter() - t

    # The single option under test. ``choose`` is what production gets today,
    # so it is set explicitly only to make the baseline arm self-documenting --
    # setting it to its own default is a no-op.
    model._h.setOptionValue("parallel", setting)
    resolved = model._h.getOptionValue("parallel")[1]
    simplex_strategy = model._h.getOptionValue("simplex_strategy")[1]
    threads = model._h.getOptionValue("threads")[1]

    t = time.perf_counter()
    r0 = model.solve(mc=mc0)
    p0_s = time.perf_counter() - t
    p0_iters = int(model._h.getInfo().simplex_iteration_count)

    t = time.perf_counter()
    r1 = model.solve(mc=mc1)
    p1_s = time.perf_counter() - t
    p1_iters = int(model._h.getInfo().simplex_iteration_count)

    prices = np.asarray(r0.prices, dtype=float)
    np.save(out, prices)

    return {
        "setting": setting,
        "resolved_parallel": str(resolved),
        "simplex_strategy": int(simplex_strategy),
        "threads_option": int(threads),
        "build_s": round(build_s, 2),
        "p0_cold_s": round(p0_s, 2),
        "p0_simplex_iters": p0_iters,
        "p1_warm_s": round(p1_s, 2),
        "p1_simplex_iters": p1_iters,
        "p0_objective": float(r0.objective_value),
        "p1_objective": float(r1.objective_value),
        "peak_rss_gb": round(_peak_rss_gb(), 2),
    }


def _subprocess_result(
    iso: str, year: int, coopt: bool, setting: str, out: Path
) -> dict | None:
    """Run one setting in an isolated subprocess and parse its JSON result."""
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--iso",
        iso,
        "--year",
        str(year),
        "--setting",
        setting,
        "--prices-out",
        str(out),
    ]
    if coopt:
        cmd.append("--coopt")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT / "src"), str(ROOT)])
    print(f"  running parallel={setting} ...", flush=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    for line in proc.stdout.splitlines():
        if line.startswith("RESULT "):
            return json.loads(line[len("RESULT ") :])
    print(f"  !! parallel={setting} produced no result (rc={proc.returncode})")
    print((proc.stderr or proc.stdout)[-2000:])
    return None


def main() -> None:
    """Parse arguments and either run one setting or sweep them all."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iso", required=True, help="ISO of the archived capture.")
    ap.add_argument("--year", type=int, required=True, help="Year of the capture.")
    ap.add_argument(
        "--coopt", action="store_true", help="The capture carries reserve co-opt rows."
    )
    ap.add_argument(
        "--setting",
        default=None,
        choices=SETTINGS,
        help="Subprocess entry point: run exactly this one setting in-process.",
    )
    ap.add_argument(
        "--prices-out",
        default=None,
        help="Where the single-setting run writes its P0 price vector (.npy).",
    )
    args = ap.parse_args()

    if args.setting is not None:
        out = Path(args.prices_out or (RESULTS / f"_px_{args.setting}.npy"))
        res = run_one(args.iso, args.year, args.coopt, args.setting, out)
        print("RESULT " + json.dumps(res), flush=True)
        return

    tag = f"{args.iso} {args.year}{' +coopt' if args.coopt else ''}"
    print("=" * 78)
    print(f"HiGHS `parallel` (PAMI) cold-P0 bench -- {tag}")
    print("=" * 78)

    px_dir = RESULTS / "bench-parallel"
    px_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    prices: dict[str, np.ndarray] = {}
    for setting in SETTINGS:
        out = px_dir / f"px_{args.iso}_{args.year}_{setting}.npy"
        res = _subprocess_result(args.iso, args.year, args.coopt, setting, out)
        if res is None:
            continue
        rows.append(res)
        prices[setting] = np.load(out)

    if not rows:
        raise SystemExit("no setting produced a result")

    print()
    header = (
        f"{'parallel':>9} {'resolved':>9} {'strat':>6} {'build':>8} "
        f"{'P0 cold':>9} {'P0 it':>9} {'P1 warm':>9} {'RSS GB':>7} {'objective':>16}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['setting']:>9} {r['resolved_parallel']:>9} "
            f"{r['simplex_strategy']:>6} {r['build_s']:>7.2f}s "
            f"{r['p0_cold_s']:>8.2f}s {r['p0_simplex_iters']:>9d} "
            f"{r['p1_warm_s']:>8.2f}s {r['peak_rss_gb']:>7.2f} "
            f"{r['p0_objective']:>16.8e}"
        )

    base = next((r for r in rows if r["setting"] == "choose"), rows[0])
    print()
    print(f"baseline = parallel={base['setting']} (production default)")
    for r in rows:
        if r["setting"] == base["setting"]:
            continue
        delta = (base["p0_cold_s"] - r["p0_cold_s"]) / max(base["p0_cold_s"], 1e-9)
        obj_rel = abs(r["p0_objective"] - base["p0_objective"]) / max(
            abs(base["p0_objective"]), 1.0
        )
        px_max = float(np.abs(prices[r["setting"]] - prices[base["setting"]]).max())
        print(
            f"  parallel={r['setting']:>6}: P0 wall {delta:+.1%}  "
            f"obj rel Δ {obj_rel:.2e}  max |Δ price| {px_max:.3e} $/MWh  "
            f"=> {'ADOPT-ELIGIBLE' if delta >= 0.10 and obj_rel == 0.0 else 'no default change'}"
        )
    print()
    print("Adoption rule: >=10% cold-P0 improvement AND identical objective/prices.")


if __name__ == "__main__":
    main()
