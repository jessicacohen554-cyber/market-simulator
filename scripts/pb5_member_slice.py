"""Solve one slice of a PB-5 sampler ensemble's members, strictly sequentially.

The production probability-band batch (PB-5,
``docs/handoffs/probability-bounds-plan-2026-07.md`` §5) runs ensemble members
as SEPARATE sequential invocations, at most two concurrent (CLAUDE.md rule 12;
gap-register G-35's operational note: the concurrent ``ProcessPoolExecutor``
member path in ``ensemble.py`` is not the production route). This driver is
that invocation unit: it samples the full deterministic draw set from the
committed sampler spec (same seed => bit-identical draws in every invocation,
``market_sim.uncertainty.sample_draws``), then solves only the draws whose
index satisfies ``index % stride == offset`` — years within each member always
sequential (``run_scenario_iso``'s year loop).

Two invocations with ``--stride 2 --offset 0`` / ``--offset 1`` therefore
partition the member set with zero overlap and never exceed two concurrent
solves. Every member caches under its own config hash, so the final assembly
pass (``market-sim ensemble --sampler ... --workers 1 --out-dir ...``) reuses
each member solved here without re-solving anything.

Usage:
    PYTHONPATH=. python scripts/pb5_member_slice.py \
        --config configs/scenarios/ercot_base.yaml \
        --sampler configs/uncertainty_ercot.yaml \
        --draws 16 --stride 2 --offset 0
"""

from __future__ import annotations

import argparse
import logging
import time
from dataclasses import replace

from market_sim.config.scenarios import ScenarioConfig
from market_sim.pipeline.api import run_pair
from market_sim.uncertainty import UncertaintySpec, draw_to_config, sample_draws

logger = logging.getLogger("pb5_member_slice")


def main() -> None:
    """Parse the slice arguments and solve the slice's members sequentially."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True, help="Base forecast scenario YAML.")
    ap.add_argument("--sampler", required=True, help="Uncertainty-sampler YAML spec.")
    ap.add_argument(
        "--draws", type=int, default=None, help="Override the spec's draw count n."
    )
    ap.add_argument(
        "--seed", type=int, default=None, help="Override the spec's sampler seed."
    )
    ap.add_argument(
        "--stride", type=int, default=1, help="Slice stride (number of invocations)."
    )
    ap.add_argument(
        "--offset", type=int, default=0, help="Slice offset (this invocation's lane)."
    )
    ap.add_argument("--iso", default=None, help="ISO; defaults to the config's own.")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    base = ScenarioConfig.from_yaml(args.config)
    spec = UncertaintySpec.from_yaml(args.sampler)
    overrides = {}
    if args.draws is not None:
        overrides["n"] = args.draws
    if args.seed is not None:
        overrides["seed"] = args.seed
    if overrides:
        spec = replace(spec, **overrides)

    iso = (args.iso or base.iso).upper()
    drawset = sample_draws(spec)
    slice_draws = drawset.draws[args.offset :: args.stride]
    logger.info(
        "pb5 slice start: iso=%s n=%d seed=%d spec_hash=%s stride=%d offset=%d "
        "-> %d members in this invocation",
        iso,
        spec.n,
        spec.seed,
        drawset.meta.spec_hash,
        args.stride,
        args.offset,
        len(slice_draws),
    )

    for draw in slice_draws:
        config = draw_to_config(base, draw)
        t0 = time.time()
        key = run_pair((config, iso))
        logger.info(
            "pb5 member done: draw_id=%s cache_key=%s wall_s=%.1f "
            "gas_factor=%.4f load_pct=%.4f tech_pct=%.4f weather=%d hydro=%s "
            "policy=%s",
            draw.draw_id,
            key,
            time.time() - t0,
            draw.gas_price_factor,
            draw.demand_growth_percentile,
            draw.tech_cost_percentile,
            draw.weather_year,
            draw.hydro_year,
            draw.policy_bundle,
        )

    logger.info("pb5 slice complete: offset=%d stride=%d", args.offset, args.stride)


if __name__ == "__main__":
    main()
