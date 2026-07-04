"""Derive per-plant parasitic-load factors from CAMPD gross vs EIA-923 net.

A plant's parasitic-load factor is annual net generation (EIA-923 Page 1,
combustion units) divided by annual gross generation (EPA CAMPD CEMS). It is
the fraction of gross output that reaches the grid after station service, and
is used to scale CAMPD's measured gross down to net for the hourly dispatch
correlation and to set per-MWh-net emission rates.

This script is ISO-agnostic: pass ``--states`` and ``--years`` directly, or
``--iso`` to use the :data:`market_sim.data.campd.ISO_STATES` lookup. It
writes ``data/raw/_processed-legacy/parasitic_load_factors.{parquet,csv}`` (one row per
plant-year plus a pooled ``year == 0`` summary per plant) and, unless
``--no-registry``, back-fills the ``parasitic_load_pct`` column of
``data/raw/reference/master-plant-registry.csv``.

Usage:
    python scripts/derive_parasitic_load.py --iso ERCOT --years 2023 2024 2025
    python scripts/derive_parasitic_load.py --states TX --years 2023
    python scripts/derive_parasitic_load.py --states PA NJ MD --years 2023 2024
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.data import campd  # noqa: E402
from market_sim.data.eia923 import load_monthly_generation  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("derive_parasitic_load")

# W1 collapsed the old inputs/ tree into data/raw/ — these are the live
# locations the model reads (config/paths.py PROCESSED_DIR, REFERENCE_DIR).
PROCESSED_DIR = REPO / "data" / "raw" / "_processed-legacy"
REGISTRY_PATH = REPO / "data" / "raw" / "reference" / "master-plant-registry.csv"


def _registry_plant_groups() -> dict[int, str]:
    """Return ``{plantid: plant_group}`` from the registry for fallbacks."""
    if not REGISTRY_PATH.exists():
        return {}
    reg = pd.read_csv(REGISTRY_PATH)
    return dict(zip(reg["plantid"].astype(int), reg["plant_group"].astype(str)))


def _update_registry(parasitic: pd.DataFrame) -> int:
    """Back-fill ``parasitic_load_pct`` in the registry from pooled factors.

    Returns the number of registry rows updated.
    """
    reg = pd.read_csv(REGISTRY_PATH)
    pooled = parasitic[parasitic["year"] == 0]
    pct_by_plant = dict(
        zip(pooled["plant_id"].astype(int), pooled["parasitic_load_pct"].astype(float))
    )
    mask = reg["plantid"].astype(int).isin(pct_by_plant)
    reg.loc[mask, "parasitic_load_pct"] = (
        reg.loc[mask, "plantid"].astype(int).map(pct_by_plant)
    )
    reg.to_csv(REGISTRY_PATH, index=False)
    return int(mask.sum())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", default=None, help="ISO whose states to load.")
    parser.add_argument("--states", nargs="+", default=None, help="CAMPD state codes.")
    parser.add_argument("--years", nargs="+", type=int, required=True)
    parser.add_argument(
        "--no-registry",
        action="store_true",
        help="Skip back-filling parasitic_load_pct in the registry.",
    )
    args = parser.parse_args()

    states = args.states or list(campd.states_for_iso(args.iso or ""))
    if not states:
        parser.error("supply --states or an --iso with a known state mapping")

    logger.info("loading CAMPD hourly for states=%s years=%s", states, args.years)
    df = campd.load_campd_hourly(states, args.years)
    if df.empty:
        logger.error("no CAMPD extracts found for the requested states/years")
        return
    campd_annual = campd.annual_plant_totals(df)
    logger.info(
        "CAMPD: %d plant-years across %d plants",
        len(campd_annual),
        campd_annual["plant_id"].nunique(),
    )

    generation = load_monthly_generation()
    eia_net = campd.eia923_combustion_net(
        generation[generation["year"].isin(args.years)]
    )

    parasitic = campd.compute_parasitic_factors(
        campd_annual, eia_net, plant_groups=_registry_plant_groups()
    )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    pq_path = PROCESSED_DIR / "parasitic_load_factors.parquet"
    csv_path = PROCESSED_DIR / "parasitic_load_factors.csv"
    parasitic.to_parquet(pq_path, index=False)
    parasitic.to_csv(csv_path, index=False)
    logger.info("wrote %s and %s", pq_path, csv_path)

    pooled = parasitic[parasitic["year"] == 0]
    measured = pooled[pooled["source"] == "measured"]
    logger.info(
        "pooled factors: %d plants (%d measured, %d class-default); "
        "measured net/gross mean=%.4f median=%.4f",
        len(pooled),
        len(measured),
        len(pooled) - len(measured),
        measured["parasitic_factor"].mean() if len(measured) else float("nan"),
        measured["parasitic_factor"].median() if len(measured) else float("nan"),
    )

    if not args.no_registry and REGISTRY_PATH.exists():
        n = _update_registry(parasitic)
        logger.info("updated parasitic_load_pct for %d registry plants", n)


if __name__ == "__main__":
    main()
