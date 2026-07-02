"""Command-line entry point for the LCE portfolio optimizer.

Usage::

    python -m lce_portfolio --load load.csv --lmp bau_lmp.csv --iso SAMPLE \
        --deltas 1 2 5 7 10 20 --out-dir data/outputs

    # or drive a run entirely from a config file (ADR 0010/0011 load_file /
    # lmp_file fields), batching every ISO in the load file:
    python -m lce_portfolio --config run.json --all-isos --out-dir data/outputs

Reads a load-intake file and an LMP file, runs the premium sweep (Mode A by
default), writes Parquet outputs + run metadata, and prints a summary. Fully
standalone — no ``market_sim`` import. Validation errors (bad schema, missing
hours, unknown ISO) are reported as a single clean message, not a traceback.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.intake import (
    load_intake,
    prepare_emission_rate,
    prepare_lmp,
    prepare_load,
)
from lce_portfolio.outputs import summarize, write_outputs
from lce_portfolio.profiles import build_cf_matrix
from lce_portfolio.resources import load_resource_arrays
from lce_portfolio.sweep import run_sweep


def build_config(args: argparse.Namespace) -> PortfolioConfig:
    """Assemble a base :class:`PortfolioConfig` from a file and/or CLI args.

    ``--config`` provides the base (including its ``load_file``/``lmp_file``,
    ADR 0010/0011); if absent, the sweep-related CLI flags build it. ISO
    selection is always CLI.
    """
    if args.config:
        return PortfolioConfig.from_file(args.config)
    return PortfolioConfig(
        iso=args.iso or "SAMPLE",
        mode="matching_target" if args.targets else "premium_cap",
        premium_deltas=tuple(args.deltas),
        matching_targets=tuple(args.targets) if args.targets else (0.8, 0.9, 1.0),
        lcoe_sensitivity=args.sensitivity,
        load_growth_rate=args.load_growth_rate,
        load_growth_years=args.load_growth_years,
    )


def run_one_iso(
    config: PortfolioConfig,
    load_path: str | Path,
    lmp_path: str | Path,
    out_dir: str | Path,
    emissions_path: str | Path | None = None,
) -> None:
    """Run the full pipeline for a single ISO (``config.iso``) and write outputs.

    ``emissions_path`` is the optional hourly fossil-average CO2-rate file
    (ADR 0013, ``(hour, iso, fossil_avg_co2_rate)``); when absent,
    residual-carbon reporting is off (``residual_co2_tons == 0``), mirroring
    the pre-carbon SAMPLE behavior.
    """
    resources = load_resource_arrays(config)
    load = prepare_load(load_path, config.iso, config)
    lmp = prepare_lmp(lmp_path, config.iso)
    emission_rate = (
        prepare_emission_rate(emissions_path, config.iso) if emissions_path else None
    )
    # profile_shape_year decouples the CF-profile vintage from the modeled
    # `year` (config.py docstring); when set, a missing file is a hard error
    # instead of the default warn-and-synthetic-fallback.
    shape_year = (
        config.profile_shape_year
        if config.profile_shape_year is not None
        else config.year
    )
    cf = build_cf_matrix(
        resources,
        config.iso,
        shape_year,
        required=config.profile_shape_year is not None,
    )

    sweep = run_sweep(config, resources, load, lmp, cf, emission_rate=emission_rate)
    paths = write_outputs(sweep, out_dir, config=config)
    print(summarize(sweep))
    print("wrote: " + "  ".join(str(v) for v in paths.values()) + "\n")


def _isos_in_load(load_path: str | Path) -> list[str]:
    """Distinct ISO names present in the load-intake file."""
    return sorted(load_intake(load_path)["iso"].unique().tolist())


def main(argv: list[str] | None = None) -> int:
    """Parse args, run the sweep for one or all ISOs, write outputs.

    The load/LMP/emissions file paths come from ``--load``/``--lmp``/
    ``--emissions`` if given, else from ``config.load_file``/``config.lmp_file``/
    ``config.emissions_file`` (ADR 0010/0011/0012); a missing load or LMP path
    is a clean CLI error, not a traceback, while a missing emissions path just
    leaves residual-carbon reporting off.
    """
    p = argparse.ArgumentParser(description="Scope 2 hourly LCE portfolio optimizer")
    p.add_argument("--load", default=None, help="load-intake CSV/Parquet")
    p.add_argument("--lmp", default=None, help="BAU LMP CSV/Parquet")
    p.add_argument(
        "--emissions",
        default=None,
        help="hourly fossil-average CO2-rate CSV/Parquet (ADR 0013, optional)",
    )
    p.add_argument("--iso", default=None, help="ISO to run (or use --all-isos)")
    p.add_argument(
        "--all-isos", action="store_true", help="run every ISO in the load file"
    )
    p.add_argument("--config", default=None, help="JSON/YAML config file (base config)")
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

    if not args.all_isos and not (args.iso or args.config):
        p.error("specify --iso, --all-isos, or a --config with an iso")

    try:
        base = build_config(args)
        load_path = args.load or base.load_file
        lmp_path = args.lmp or base.lmp_file
        # Optional (ADR 0013): no emissions file means residual-carbon
        # reporting stays off, so this is never a CLI error.
        emissions_path = args.emissions or base.emissions_file
        if not load_path:
            p.error("specify --load or set load_file in --config")
        if not lmp_path:
            p.error("specify --lmp or set lmp_file in --config")

        isos = _isos_in_load(load_path) if args.all_isos else [args.iso or base.iso]
        for iso in isos:
            run_one_iso(
                base.with_overrides(iso=iso),
                load_path,
                lmp_path,
                args.out_dir,
                emissions_path=emissions_path,
            )
    except (ValueError, KeyError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
