"""Capture a dispatch baseline for one ISO by running the full scenario.

Runs ``run_scenario_iso`` for the given ISO in backcast mode and copies the
output Parquet files to the specified directory. Can be run in parallel for
multiple ISOs since each writes to its own ``--out-dir``.

Usage:
    python scripts/capture_baseline.py --iso ERCOT --out-dir baselines/ercot
    python scripts/capture_baseline.py --iso CAISO --out-dir baselines/caiso --year 2023 2024 2025

Parallel capture (one shell per ISO):
    python scripts/capture_baseline.py --iso PJM --out-dir baselines/pjm &
    python scripts/capture_baseline.py --iso CAISO --out-dir baselines/caiso &
    wait
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.pipeline.api import run_scenario  # noqa: E402
from market_sim.results.cache import CACHE_ROOT  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("capture_baseline")


def capture(iso: str, out_dir: Path, years: list[int] | None = None) -> None:
    """Run the backcast scenario and copy result Parquet files to out_dir."""
    config = ScenarioConfig(
        iso=iso,
        mode="backcast",
        weather_year=years[0] if years else 2024,
    )

    logger.info(
        "Running backcast for %s (config.cache_key=%s)", iso, config.cache_key()
    )
    cache_key = run_scenario(config, iso)

    out_dir.mkdir(parents=True, exist_ok=True)

    cache_dir = CACHE_ROOT / iso / cache_key
    parquet_files = sorted(cache_dir.glob("year_*.parquet"))

    if not parquet_files:
        logger.warning("No year_*.parquet files found in %s", cache_dir)
        return

    if years:
        parquet_files = [
            f for f in parquet_files if any(f"year_{y}" in f.stem for y in years)
        ]

    for src in parquet_files:
        dst = out_dir / src.name
        shutil.copy2(src, dst)
        logger.info("Copied %s -> %s", src, dst)

    logger.info("Baseline captured: %d files in %s", len(parquet_files), out_dir)


def main() -> int:
    """Entry point for the baseline capture script."""
    parser = argparse.ArgumentParser(
        description="Capture a dispatch baseline for one ISO."
    )
    parser.add_argument(
        "--iso",
        required=True,
        help="ISO to run (ERCOT, CAISO, PJM, MISO, NYISO, NEISO)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Directory to write baseline Parquet files to",
    )
    parser.add_argument(
        "--year",
        type=int,
        nargs="+",
        default=None,
        help="Backcast year(s) to capture (default: weather_year only)",
    )
    args = parser.parse_args()

    try:
        capture(args.iso.upper(), args.out_dir, args.year)
    except Exception:
        logger.exception("Baseline capture failed for %s", args.iso)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
