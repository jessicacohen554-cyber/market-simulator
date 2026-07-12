"""Solve a fixed list of PB-0 scenario-matrix cases, strictly sequentially.

Companion to ``scripts/pb5_member_slice.py``: this is the matrix-case
invocation unit for the same 2-concurrent-invocation batch (CLAUDE.md rule
12) -- one process solves its assigned cases' years sequentially
(``run_scenario_iso``'s year loop), and this process runs alongside (at most)
one other PB-5 invocation (a sampler slice or another matrix slice).

Usage:
    PYTHONPATH=. python scripts/pb5_matrix_slice.py \
        --config configs/scenarios/ercot_base.yaml \
        --matrix configs/scenario_matrix.yaml \
        --cases REF CORNER-HI-EMIT CORNER-LO-EMIT
"""

from __future__ import annotations

import argparse
import logging
import time

from market_sim.config.scenarios import ScenarioConfig, SweepDefinition
from market_sim.matrix import matrix_configs
from market_sim.runner import _run_pair

logger = logging.getLogger("pb5_matrix_slice")


def main() -> None:
    """Parse arguments and solve the requested matrix cases sequentially."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True, help="Base forecast scenario YAML.")
    ap.add_argument(
        "--matrix", required=True, help="Cases-mode sweep YAML (scenario_matrix.yaml)."
    )
    ap.add_argument(
        "--cases", required=True, nargs="+", help="Case names to solve, in order."
    )
    ap.add_argument("--iso", default=None, help="ISO; defaults to the config's own.")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    base = ScenarioConfig.from_yaml(args.config)
    sweep_def = SweepDefinition.from_yaml(args.matrix)
    iso = (args.iso or base.iso).upper()
    configs = matrix_configs(base, sweep_def)

    missing = [c for c in args.cases if c not in configs]
    if missing:
        raise ValueError(f"unknown case(s) {missing}; matrix has {sorted(configs)}")

    logger.info("pb5 matrix slice start: iso=%s cases=%s", iso, args.cases)
    for case in args.cases:
        t0 = time.time()
        key = _run_pair((configs[case], iso))
        logger.info(
            "pb5 matrix case done: case=%s cache_key=%s wall_s=%.1f",
            case,
            key,
            time.time() - t0,
        )
    logger.info("pb5 matrix slice complete: cases=%s", args.cases)


if __name__ == "__main__":
    main()
