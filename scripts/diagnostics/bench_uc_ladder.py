"""The MILP-UC wallclock ladder: rungs L1 (one window), L2 (two months), L3 (one year).

GATESPEC section 3 (``docs/records/governance/uc-milp-2026-10/GATESPEC-uc-milp-
testing-protocol-2026-10-03.md``): every rung is a shard (rule 32); this
script only measures and writes JSON + the section 6.1 wall table under
``--out``. It changes NO default and registers nothing.

    python scripts/diagnostics/bench_uc_ladder.py --iso NEISO --year 2023 --rung L1 \\
        --bundle results/calibration/w0_neiso_span --out results/bench/uc/neiso_2023_L1
    python scripts/diagnostics/bench_uc_ladder.py --iso NEISO --year 2023 --rung L2 \\
        --out results/bench/uc/neiso_2023_L2 --arms warm,prefix,threads
    python scripts/diagnostics/bench_uc_ladder.py --iso NEISO --year 2023 --rung L3 \\
        --out results/bench/uc/neiso_2023_L3 --baseline-s 135

L1 and L2 capture the keeper recipe's LP once (``scripts/lib/uc_bench.
capture_year``, one P0 + P1 of the ISO-year; ``--capture`` reuses a saved
capture) and then run the window(s) in-process. L3 drives the production
orchestrator through ``replay_keeper.py --set unit_commitment_milp=true`` and
reads the wall row from the resulting bundle and ``uc_solve_log``. ``--set
KEY=JSON`` forwards a declared ``uc_*`` value (e.g. a PRECOMMIT's longer
look-ahead) to every rung; the defaults are the registry's.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.lib import uc_bench  # noqa: E402


def _parse_sets(specs: list[str]) -> dict:
    out: dict = {}
    for spec in specs or []:
        key, _, raw = spec.partition("=")
        if not key or not raw:
            raise SystemExit(f"--set expects KEY=JSON, got {spec!r}")
        out[key] = json.loads(raw)
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI entry (see the module docstring)."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iso", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--rung", required=True, choices=["L1", "L2", "L3"])
    ap.add_argument(
        "--bundle",
        default=None,
        help="keeper bundle (default: the ISO's designated keeper)",
    )
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--capture", default=None, help="reuse a saved YearCapture pickle (L1/L2)"
    )
    ap.add_argument(
        "--no-solve",
        action="store_true",
        help="L1 only: zero-LP capture; the window LP relaxation stands in for P0",
    )
    ap.add_argument(
        "--arms", default="warm,prefix", help="L2 arms: warm,prefix,threads"
    )
    ap.add_argument("--months", default="1,7", help="L2 months (1-12)")
    ap.add_argument(
        "--baseline-s",
        type=float,
        default=None,
        help="L3 denominator (GATESPEC baseline P0+P1 s)",
    )
    ap.add_argument(
        "--set", dest="overrides", action="append", default=[], metavar="KEY=JSON"
    )
    ap.add_argument(
        "--dump-dir",
        default=None,
        help=(
            "L1 only: on an infeasible window write its model (.mps), carried "
            "state (.npz) and zero-LP diagnosis (.json) here — a harness "
            "argument, never a registry field or an env knob"
        ),
    )
    ap.add_argument(
        "--save-capture",
        action="store_true",
        help=(
            "L1/L2: also save the YearCapture pickle under --out (tens of MB with "
            "a solved capture; off by default so a bench shard's push stays small)"
        ),
    )
    args = ap.parse_args(argv)
    out = Path(args.out)
    if not out.is_absolute():
        out = REPO / out
    out.mkdir(parents=True, exist_ok=True)
    overrides = _parse_sets(args.overrides)
    if args.rung == "L3":
        row = uc_bench.rung_l3(
            args.iso,
            args.year,
            out,
            bundle=args.bundle,
            baseline_s=args.baseline_s,
            overrides=overrides,
        )
        table = uc_bench.wall_table([row])
        (out / "wall_table.md").write_text(table + "\n")
        print(table)
        return 0
    if args.capture:
        cap = uc_bench.YearCapture.load(Path(args.capture))
    else:
        cap = uc_bench.capture_year(
            args.iso,
            args.year,
            out,
            solve=not args.no_solve,
            bundle=Path(args.bundle) if args.bundle else None,
        )
        if args.save_capture:
            cap.save(out / f"capture_{args.iso}_{args.year}.pkl")
    if args.rung == "L1":
        dump_dir = Path(args.dump_dir) if args.dump_dir else None
        res = uc_bench.rung_l1(cap, out, dump_dir=dump_dir, **overrides)
        print(
            json.dumps(
                {k: v for k, v in res.items() if k != "trough_price_milp_vs_p1"},
                indent=1,
                default=str,
            )
        )
        return 0
    months = tuple(int(m) for m in args.months.split(","))
    arms = tuple(a for a in args.arms.split(",") if a)
    res = uc_bench.rung_l2(cap, out, months=months, arms=arms, **overrides)
    for name, arm in res["arms"].items():
        for m in arm["months"]:
            print(
                f"{name:10s} month {m['month']:2d}: {m['windows']} windows, wall {m['wall_s']:.1f}s, "
                f"MILP p50/p95/max {m['milp_s_p50']:.2f}/{m['milp_s_p95']:.2f}/{m['milp_s_max']:.2f}s, "
                f"nodes p50/p95 {m['nodes_p50']:.0f}/{m['nodes_p95']:.0f}, zero-node {m['zero_node_share']:.2f}, "
                f"TL hits {m['time_limit_hits']}, fixed on/off {m['fixed_on']}/{m['fixed_off']}, hash {m['schedule_hash']}"
            )
    print("schedule equal across arms:", res["schedule_equal_across_arms"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
