"""Derive the fleet-wide fossil CO2 emission-rate artifact (kg CO2 / net MWh).

Assembles one per-MWh CO2 rate for every fossil plant from eGRID (the fleet-wide
base, the only source spanning the small non-CEMS units) overridden by the
CAMPD-measured pooled intensities where they exist. The result is the input to
the calibration page's emissions metric: a class's generation (MWh) times its
net-generation-weighted intensity gives metric tonnes of CO2, model vs actual.

Writes ``data/raw/_processed-legacy/fossil_co2_rates.{parquet,csv}`` (one row per
plant-year), the fast-path artifact :func:`market_sim.data.egrid.fossil_co2_rate_map`
reads in preference to parsing the 21 MB eGRID workbook at render time.

The write is a **year-scoped merge**: only the ``--years`` requested are
re-assembled, and every other year already in the artifact is carried through
value-identical. That is what lets a back-year intake (e.g. the 2018-2021
holdout ladder) land without disturbing the training-year rows a keeper's
emissions metric was scored on. ``--overwrite-all`` restores the older
replace-the-whole-file behaviour for a deliberate full rebuild.

Usage:
    python scripts/data/derive_fossil_co2_rates.py --years 2023 2024
    python scripts/data/derive_fossil_co2_rates.py --years 2023 2024 2025
    python scripts/data/derive_fossil_co2_rates.py --years 2018 2019 2020 2021
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.data import egrid  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("derive_fossil_co2_rates")

# Deterministic on-disk ordering, so a re-run that changes no year's values
# produces the same row order (and the same CSV) as the run before it.
_SORT_KEYS: list[str] = ["year", "plant_id"]


def merge_years(existing: pd.DataFrame, fresh: pd.DataFrame) -> pd.DataFrame:
    """Return ``existing`` with every year present in ``fresh`` replaced by it.

    Years the caller did not re-assemble are carried through unchanged — the
    year-scoped merge that keeps a back-year intake from disturbing the
    training-year rows.

    Args:
        existing: The artifact as read from disk (may be empty).
        fresh: Newly assembled rows for the requested years.

    Returns:
        The merged table, sorted by ``(year, plant_id)``.
    """
    if existing.empty:
        return fresh.sort_values(_SORT_KEYS).reset_index(drop=True)
    kept = existing[~existing["year"].isin(set(fresh["year"].unique()))]
    merged = pd.concat([kept, fresh], ignore_index=True)
    return merged.sort_values(_SORT_KEYS).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024],
        help="Calendar years to assemble (default: 2023 2024).",
    )
    parser.add_argument(
        "--overwrite-all",
        action="store_true",
        help=(
            "Replace the whole artifact with just --years instead of merging "
            "into the years already on disk (default: merge)."
        ),
    )
    args = parser.parse_args()

    rates = egrid.build_fossil_co2_rates(args.years)
    if rates.empty:
        logger.error("no fossil CO2 rates assembled for years %s", args.years)
        return

    out_pq = egrid.FOSSIL_CO2_RATES_PATH
    if not args.overwrite_all and out_pq.exists():
        prior = pd.read_parquet(out_pq)
        carried = sorted(set(prior["year"].unique()) - set(args.years))
        rates = merge_years(prior, rates)
        logger.info("merged into existing artifact; years carried through: %s", carried)
    out_csv = out_pq.with_suffix(".csv")
    out_pq.parent.mkdir(parents=True, exist_ok=True)
    rates.to_parquet(out_pq, index=False)
    rates.to_csv(out_csv, index=False)
    logger.info("wrote %s and %s", out_pq, out_csv)

    for year, g in rates.groupby("year"):
        n_campd = int((g["source"] == "campd").sum())
        n_egrid = int((g["source"] == "egrid").sum())
        logger.info(
            "%d: %d fossil plants (%d CAMPD-measured, %d eGRID); "
            "CO2 rate mean=%.1f median=%.1f kg/MWh-net",
            year,
            len(g),
            n_campd,
            n_egrid,
            g["co2_kg_per_mwh_net"].mean(),
            g["co2_kg_per_mwh_net"].median(),
        )


if __name__ == "__main__":
    main()
