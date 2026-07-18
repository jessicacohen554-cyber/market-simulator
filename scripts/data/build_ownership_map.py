"""Build the generator-to-parent-company ownership map from EIA-860.

Loads EIA-860 Schedule 3 (generators) and Schedule 4 (ownership), rolls
every generator-owner row up to its canonical parent company via the
lookup and M&A overlays in :mod:`market_sim.data.ownership_config`, and
writes two parquet outputs to ``data/ownership/``:

* ``parent_company_fleet_{year}.parquet`` — full generator-level mapping.
* ``fleet_summary_{year}.parquet`` — capacity aggregated by parent × fuel
  type × balancing authority.

Usage:
    python scripts/data/build_ownership_map.py --eia860-path PATH --year YEAR \\
        [--as-of-date YYYY-MM-DD] [--output-dir DIR]

Defaults:
    --as-of-date  2026-01-15
    --output-dir  data/ownership
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.ownership import (  # noqa: E402
    build_parent_mapping,
    load_eia860_ownership,
    summarize_fleet_by_parent,
    validate_percent_owned,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("build_ownership_map")

DEFAULT_OUTPUT_DIR = REPO / "data" / "ownership"


def main() -> None:
    """Build and persist the parent-company ownership map and fleet summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--eia860-path",
        type=Path,
        required=True,
        help="EIA-860 annual zip, or a directory of processed parquet sheets.",
    )
    parser.add_argument(
        "--year", type=int, required=True, help="EIA-860 reporting year."
    )
    parser.add_argument(
        "--as-of-date",
        default="2026-01-15",
        help="ISO YYYY-MM-DD snapshot date for the M&A overlay logic.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for the parquet outputs.",
    )
    args = parser.parse_args()

    if not args.eia860_path.exists():
        raise SystemExit(f"EIA-860 path not found: {args.eia860_path}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    ownership = load_eia860_ownership(args.eia860_path, args.year)

    bad = validate_percent_owned(ownership)
    if not bad.empty:
        logger.warning(
            "%d generators have percent_owned not summing to 1.0 "
            "(EIA does not enforce this at survey time)",
            len(bad),
        )

    parent_df = build_parent_mapping(ownership, as_of_date=args.as_of_date)

    unknown = (parent_df["parent_company"] == "Other/Unknown").sum()
    logger.info(
        "Mapped %d generator-owner rows; %d remain Other/Unknown",
        len(parent_df),
        unknown,
    )

    fleet_path = args.output_dir / f"parent_company_fleet_{args.year}.parquet"
    parent_df.to_parquet(fleet_path, index=False)
    logger.info("Wrote generator-level mapping → %s", fleet_path)

    summary = summarize_fleet_by_parent(
        parent_df,
        group_cols=["energy_source_code", "balancing_authority_code"],
    )
    summary_path = args.output_dir / f"fleet_summary_{args.year}.parquet"
    summary.to_parquet(summary_path, index=False)
    logger.info("Wrote fleet summary → %s", summary_path)

    top = summarize_fleet_by_parent(parent_df).head(10)
    for _, row in top.iterrows():
        logger.info(
            "  %-28s %10.0f MW  (%d generators)",
            row["parent_company"],
            row["ownership_mw"],
            int(row["generator_count"]),
        )


if __name__ == "__main__":
    main()
