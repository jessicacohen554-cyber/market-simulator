"""Attribute market-sim dispatch emissions to parent companies.

Joins plant-level dispatch results with the parent-company ownership map
and rolls emissions up to ultimate parents at hourly, monthly and annual
granularity.

The dispatch inputs are plant-level hourly parquets — one per scenario-year
— each carrying ``plant_code``, ``generator_id``, ``hour``, ``dispatch_mw``
and an ``emission_rate`` (tCO2/MWh) column. These are produced by
``scripts/generate_financial_reports.py`` (the ``plant_hourly_{year}``
outputs) from the bin-level dispatch cache.

Usage:
    python scripts/attribute_emissions_to_owners.py \\
        --results-dir reports/SCENARIO_HASH/ \\
        --ownership-map data/ownership/parent_company_fleet_2024.parquet \\
        [--output-dir data/ownership/] [--pattern 'plant_hourly_*.parquet']

Outputs one ``emissions_by_owner_{scenario_hash}_{year}.parquet`` per year.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.ownership import attribute_emissions  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("attribute_emissions_to_owners")


def _year_from_name(path: Path) -> int | None:
    """Extract a four-digit year from a dispatch parquet filename."""
    match = re.search(r"(20\d{2})", path.stem)
    return int(match.group(1)) if match else None


def main() -> None:
    """Attribute each scenario-year's dispatch emissions to parent companies."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-dir",
        type=Path,
        required=True,
        help="Directory of plant-level hourly dispatch parquets.",
    )
    parser.add_argument(
        "--ownership-map",
        type=Path,
        required=True,
        help="parent_company_fleet_{year}.parquet from build_ownership_map.py.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for outputs (defaults to --results-dir).",
    )
    parser.add_argument(
        "--pattern",
        default="plant_hourly_*.parquet",
        help="Glob for the per-year plant-level dispatch parquets.",
    )
    args = parser.parse_args()

    if not args.results_dir.is_dir():
        raise SystemExit(f"results directory not found: {args.results_dir}")
    if not args.ownership_map.exists():
        raise SystemExit(f"ownership map not found: {args.ownership_map}")

    output_dir = args.output_dir or args.results_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    scenario_hash = args.results_dir.resolve().name

    parent_df = pd.read_parquet(args.ownership_map)

    dispatch_files = sorted(args.results_dir.glob(args.pattern))
    if not dispatch_files:
        raise SystemExit(
            f"no dispatch parquets matching {args.pattern!r} in {args.results_dir}"
        )

    for dispatch_path in dispatch_files:
        year = _year_from_name(dispatch_path)
        if year is None:
            logger.warning("skipping %s — no year in filename", dispatch_path.name)
            continue

        attributed = attribute_emissions(dispatch_path, parent_df, year)
        out_path = (
            output_dir / f"emissions_by_owner_{scenario_hash}_{year}.parquet"
        )
        attributed.to_parquet(out_path, index=False)
        logger.info("Wrote %s", out_path)


if __name__ == "__main__":
    main()
