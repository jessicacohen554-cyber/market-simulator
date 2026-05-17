"""Side-by-side comparison of plant-financial reports across scenarios.

A lighter companion to ``generate_financial_reports.py``: it reads the
per-year report parquets that script produced for two or more scenarios and
emits three comparison CSVs.

Each ``--scenario-dirs`` entry is a report directory holding
``company_annual_{year}.parquet`` and ``plant_annual_{year}.parquet`` files.

Usage:
    python scripts/compare_scenarios.py \\
        --scenario-dirs reports/abc123/ reports/def456/ \\
        --labels "Base Case" "High Carbon" \\
        --output-dir reports/comparison/

Outputs:
    company_comparison.csv    revenue/emissions/generation by company × scenario
    price_comparison.csv      generation-weighted avg price by zone × scenario
    emissions_comparison.csv  total emissions trajectory by scenario
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

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("compare_scenarios")


def _year_from_name(path: Path) -> int | None:
    """Extract a four-digit year from a report parquet filename."""
    match = re.search(r"(20\d{2})", path.stem)
    return int(match.group(1)) if match else None


def _load_yearly(scenario_dir: Path, prefix: str) -> pd.DataFrame:
    """Concatenate every ``{prefix}_{year}.parquet`` in a scenario directory."""
    frames: list[pd.DataFrame] = []
    for path in sorted(scenario_dir.glob(f"{prefix}_*.parquet")):
        year = _year_from_name(path)
        if year is None:
            continue
        block = pd.read_parquet(path)
        if "year" not in block.columns:
            block["year"] = year
        frames.append(block)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    """Build the three cross-scenario comparison CSVs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario-dirs", type=Path, nargs="+", required=True,
        help="Two or more report directories to compare.",
    )
    parser.add_argument(
        "--labels", nargs="+", required=True,
        help="A human-readable label per scenario directory.",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=REPO / "reports" / "comparison",
    )
    args = parser.parse_args()

    if len(args.scenario_dirs) != len(args.labels):
        raise SystemExit("--scenario-dirs and --labels must be the same length")
    if len(args.scenario_dirs) < 2:
        raise SystemExit("need at least two scenarios to compare")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    company_frames: list[pd.DataFrame] = []
    price_frames: list[pd.DataFrame] = []
    emissions_frames: list[pd.DataFrame] = []

    for scenario_dir, label in zip(args.scenario_dirs, args.labels, strict=True):
        if not scenario_dir.is_dir():
            raise SystemExit(f"scenario directory not found: {scenario_dir}")

        company = _load_yearly(scenario_dir, "company_annual")
        plant = _load_yearly(scenario_dir, "plant_annual")

        if not company.empty:
            agg = (
                company.groupby("parent_company", as_index=False)
                .agg(
                    revenue=("owned_revenue", "sum"),
                    emissions_tco2=("owned_co2_emissions_tons", "sum"),
                    generation_mwh=("owned_generation_mwh", "sum"),
                )
            )
            company_frames.append(agg.assign(scenario=label))
            emissions_frames.append(
                company.groupby("year", as_index=False)
                .agg(total_emissions_tco2=("owned_co2_emissions_tons", "sum"))
                .assign(scenario=label)
            )

        if not plant.empty:
            # Generation-weighted average captured price per zone.
            plant = plant.assign(
                _rev=plant["avg_price_captured"].fillna(0.0)
                * plant["generation_mwh"]
            )
            zone_price = (
                plant.groupby("zone", as_index=False)
                .agg(_rev=("_rev", "sum"), gen=("generation_mwh", "sum"))
            )
            zone_price["avg_price_per_mwh"] = (
                zone_price["_rev"] / zone_price["gen"].where(zone_price["gen"] > 0)
            )
            price_frames.append(
                zone_price[["zone", "avg_price_per_mwh"]].assign(scenario=label)
            )

    _write_comparison(
        args.output_dir / "company_comparison.csv",
        company_frames, index=["parent_company"],
        value_cols=["revenue", "emissions_tco2", "generation_mwh"],
    )
    _write_comparison(
        args.output_dir / "price_comparison.csv",
        price_frames, index=["zone"], value_cols=["avg_price_per_mwh"],
    )
    _write_comparison(
        args.output_dir / "emissions_comparison.csv",
        emissions_frames, index=["year"], value_cols=["total_emissions_tco2"],
    )
    logger.info("Wrote comparison CSVs → %s", args.output_dir)


def _write_comparison(
    path: Path,
    frames: list[pd.DataFrame],
    index: list[str],
    value_cols: list[str],
) -> None:
    """Pivot per-scenario frames into one wide comparison CSV.

    For exactly two scenarios a ``delta`` column (second minus first) is
    added for each value column.
    """
    if not frames:
        logger.warning("no data for %s — skipping", path.name)
        return

    combined = pd.concat(frames, ignore_index=True)
    wide = combined.pivot_table(
        index=index, columns="scenario", values=value_cols
    )
    scenarios = list(combined["scenario"].drop_duplicates())
    if len(scenarios) == 2:
        for col in value_cols:
            wide[(col, "delta")] = (
                wide[(col, scenarios[1])] - wide[(col, scenarios[0])]
            )
    wide.columns = ["_".join(str(c) for c in col) for col in wide.columns]
    wide.reset_index().to_csv(path, index=False)
    logger.info("Wrote %s", path)


if __name__ == "__main__":
    main()
