"""Command-line entry point for the LCE portfolio optimizer.

Usage::

    python -m lce_portfolio --load data/sample/sample_load.csv \
        --lmp data/sample/sample_lmp.csv --iso SAMPLE \
        --deltas 1 2 5 7 10 20 --out-dir data/outputs

Reads a load-intake file and an LMP file, runs the premium sweep (Mode A by
default), writes Parquet outputs, and prints a summary. Fully standalone — no
``market_sim`` import.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from lce_portfolio.config import HOURS_PER_YEAR, PortfolioConfig
from lce_portfolio.intake import prepare_load
from lce_portfolio.outputs import summarize, write_outputs
from lce_portfolio.profiles import build_cf_matrix
from lce_portfolio.resources import load_resource_arrays
from lce_portfolio.sweep import run_sweep


def load_lmp(path: str | Path, iso: str) -> np.ndarray:
    """Read a BAU LMP file (columns ``hour``, ``iso``, ``lmp``) for one ISO."""
    path = Path(path)
    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    df = df[df["iso"] == iso].sort_values("hour")
    if len(df) != HOURS_PER_YEAR:
        raise ValueError(f"expected {HOURS_PER_YEAR} LMP rows for {iso}, got {len(df)}")
    return df["lmp"].to_numpy(dtype=float)


def build_config(args: argparse.Namespace) -> PortfolioConfig:
    """Assemble a :class:`PortfolioConfig` from parsed CLI arguments."""
    return PortfolioConfig(
        iso=args.iso,
        mode="matching_target" if args.targets else "premium_cap",
        premium_deltas=tuple(args.deltas),
        matching_targets=tuple(args.targets) if args.targets else (0.8, 0.9, 1.0),
        lcoe_sensitivity=args.sensitivity,
        load_growth_rate=args.load_growth_rate,
        load_growth_years=args.load_growth_years,
    )


def main(argv: list[str] | None = None) -> int:
    """Parse args, run the sweep, write outputs, print the summary."""
    p = argparse.ArgumentParser(description="Scope 2 hourly LCE portfolio optimizer")
    p.add_argument("--load", required=True, help="load-intake CSV/Parquet")
    p.add_argument("--lmp", required=True, help="BAU LMP CSV/Parquet")
    p.add_argument("--iso", required=True)
    p.add_argument(
        "--deltas",
        type=float,
        nargs="+",
        default=[1, 2, 5, 7, 10, 20],
        help="premium caps $/MWh (Mode A)",
    )
    p.add_argument(
        "--targets",
        type=float,
        nargs="+",
        default=None,
        help="matching targets (switches to Mode B)",
    )
    p.add_argument("--sensitivity", choices=["low", "mid", "high"], default="mid")
    p.add_argument("--load-growth-rate", type=float, default=0.0)
    p.add_argument("--load-growth-years", type=int, default=0)
    p.add_argument("--out-dir", default="data/outputs")
    args = p.parse_args(argv)

    config = build_config(args)
    resources = load_resource_arrays(config)
    load = prepare_load(args.load, args.iso, config)
    lmp = load_lmp(args.lmp, args.iso)
    cf = build_cf_matrix(resources, args.iso, config.year)

    sweep = run_sweep(config, resources, load, lmp, cf)
    paths = write_outputs(sweep, args.out_dir)
    print(summarize(sweep))
    print(f"\nwrote: {paths['frontier']}\n       {paths['build_mix']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
