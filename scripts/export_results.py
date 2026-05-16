"""Export every completed cached scenario to the frontend data directory.

Scans the results cache for scenarios whose every simulation year is
present, exports each to a compact annual-summary JSON via
:func:`market_sim.results.export.export_scenario_json`, and writes a
``scenarios.json`` index listing the exported scenarios with their metadata.

Run: ``python scripts/export_results.py``
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import END_YEAR, START_YEAR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.results import cache  # noqa: E402
from market_sim.results.export import export_scenario_json  # noqa: E402

logger = logging.getLogger(__name__)

DEFAULT_RESULTS_ROOT = REPO / "results"
DEFAULT_OUTPUT_DIR = REPO / "frontend" / "data" / "results"
DEFAULT_INDEX_PATH = REPO / "frontend" / "data" / "scenarios.json"


def find_completed_scenarios(results_root: Path) -> list[tuple[str, str]]:
    """Return ``(iso, cache_key)`` pairs whose every simulation year is cached.

    A scenario directory is complete when it holds a ``config.yaml`` and one
    ``year_{year}.parquet`` for every year from :data:`START_YEAR` to
    :data:`END_YEAR`.

    Args:
        results_root: The cache root directory, holding one subdirectory
            per ISO.

    Returns:
        Sorted ``(iso, cache_key)`` pairs for every completed scenario.
    """
    pairs: list[tuple[str, str]] = []
    if not results_root.is_dir():
        return pairs

    years = range(START_YEAR, END_YEAR + 1)
    for iso_dir in sorted(p for p in results_root.iterdir() if p.is_dir()):
        for scenario_dir in sorted(
            p for p in iso_dir.iterdir() if p.is_dir()
        ):
            if not (scenario_dir / "config.yaml").exists():
                continue
            complete = all(
                (scenario_dir / f"year_{year}.parquet").exists()
                for year in years
            )
            if complete:
                pairs.append((iso_dir.name, scenario_dir.name))
            else:
                logger.warning(
                    "skipping incomplete scenario %s/%s",
                    iso_dir.name, scenario_dir.name,
                )
    return pairs


def export_all(
    results_root: Path, output_dir: Path, index_path: Path
) -> list[dict]:
    """Export every completed scenario and write the ``scenarios.json`` index.

    Args:
        results_root: The cache root directory to scan.
        output_dir: Directory to write per-scenario JSON files into.
        index_path: Path of the ``scenarios.json`` index to write.

    Returns:
        The list of per-scenario metadata dicts written to the index.
    """
    scenarios: list[dict] = []
    for iso, cache_key in find_completed_scenarios(results_root):
        prior_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = results_root
        try:
            json_path = export_scenario_json(cache_key, iso, output_dir)
            config = ScenarioConfig.from_yaml(
                cache.get_config_path(iso, cache_key, START_YEAR)
            )
        finally:
            cache.CACHE_ROOT = prior_root

        scenarios.append(
            {
                "cache_key": cache_key,
                "iso": iso,
                "file": json_path.name,
                "year_start": START_YEAR,
                "year_end": END_YEAR,
                "config": asdict(config),
            }
        )
        logger.info("exported %s/%s -> %s", iso, cache_key, json_path.name)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps({"scenarios": scenarios}, indent=2))
    logger.info("wrote %s (%d scenario(s))", index_path, len(scenarios))
    return scenarios


def _build_parser() -> argparse.ArgumentParser:
    """Return the ``export_results`` argument parser."""
    parser = argparse.ArgumentParser(
        prog="export_results",
        description="Export completed cached scenarios to frontend JSON.",
    )
    parser.add_argument(
        "--results-root", type=Path, default=DEFAULT_RESULTS_ROOT,
        help="Cache root directory to scan (default: results/).",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
        help="Directory for per-scenario JSON (default: frontend/data/results/).",
    )
    parser.add_argument(
        "--index", type=Path, default=DEFAULT_INDEX_PATH,
        help="Path of the scenarios.json index (default: frontend/data/scenarios.json).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point: export every completed scenario found in the cache."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = _build_parser().parse_args(argv)
    scenarios = export_all(args.results_root, args.output_dir, args.index)
    if not scenarios:
        logger.warning("no completed scenarios found under %s", args.results_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
