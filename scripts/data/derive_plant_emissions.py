"""Derive per-plant emission rates and start/stop factors from CAMPD CEMS.

For every plant the EPA CAMPD hourly extract covers, this computes the
emissions intensity of net generation — kg CO2, NOx and SO2 per MWh **net**
(gross scaled by the parasitic-load factor) — plus the marginal/no-load
decomposition and per-start incremental emissions. These feed two uses:

* setting plant-specific emission rates in the dispatch LP, so carbon / NOx /
  SO2 prices bite at each plant's measured intensity rather than a fuel-class
  average; and
* tuning cycling-emission penalties from the measured start/stop factors.

It depends on ``parasitic_load_factors.parquet`` (run
``scripts/data/derive_parasitic_load.py`` first). Writes
``data/raw/_processed-legacy/plant_emission_rates.{parquet,csv}`` (one row per
plant-year plus a pooled ``year == 0`` summary) and, unless ``--no-registry``,
adds per-MWh-net rate columns to ``data/raw/reference/master-plant-registry.csv``.

**The write is a year-scoped merge, and the pooled ``year == 0`` block is
protected.** Only the ``--years`` requested are re-derived; every other year
already in the artifact is carried through value-identical, and the pooled rows
— the ONLY rows the model reads (``fleet._plant_emission_rate_map`` and
``egrid._campd_rate_map`` both filter ``year == 0``) — keep whatever pool they
were built from unless ``--repool`` is passed. That is what lets an
out-of-training back-year land (rule 22 data intake) without silently
re-pooling the emission rates every keeper was scored on. ``--repool`` rebuilds
the pooled block from ``--years``; ``--overwrite-all`` restores the older
replace-the-whole-file behaviour.

Usage:
    python scripts/data/derive_plant_emissions.py --iso ERCOT --years 2023 2024 2025
    python scripts/data/derive_plant_emissions.py --states TX --years 2023
    python scripts/data/derive_plant_emissions.py --states TX --years 2022  # back-year, pool untouched
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import PLANT_REGISTRY_CSV, PROCESSED_DIR  # noqa: E402

from market_sim.data import campd  # noqa: E402
from market_sim.data.eia923 import load_monthly_generation  # noqa: E402

# A plant burning between these coal shares blends coal and gas units that
# CAMPD reports as one facility, so no single rate fits its separate dispatch
# bins; its emission-rate override is skipped (bins keep fuel defaults).
_MIXED_COAL_SHARE_LO: float = 0.10
_MIXED_COAL_SHARE_HI: float = 0.90

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("derive_plant_emissions")

# W1 collapsed the old inputs/ tree into data/raw/ — these are the live
# locations the model reads (config/paths.py PROCESSED_DIR, REFERENCE_DIR).
PROCESSED_DIR = PROCESSED_DIR
REGISTRY_PATH = PLANT_REGISTRY_CSV
PARASITIC_PATH = PROCESSED_DIR / "parasitic_load_factors.parquet"

# Per-MWh-net rate columns mirrored into the registry.
_REGISTRY_RATE_COLS: tuple[str, ...] = (
    "co2_kg_per_mwh_net",
    "nox_kg_per_mwh_net",
    "so2_kg_per_mwh_net",
    "startup_co2_kg",
    "startup_nox_kg",
    "startup_so2_kg",
    "starts_per_year",
)


def _load_factors() -> dict[int, float]:
    """Return ``{plant_id: parasitic_factor}`` from the pooled factors file."""
    if not PARASITIC_PATH.exists():
        raise FileNotFoundError(
            f"{PARASITIC_PATH} not found; run scripts/data/derive_parasitic_load.py first"
        )
    return campd.pooled_factor_map(pd.read_parquet(PARASITIC_PATH))


def _update_registry(rates: pd.DataFrame, years: list[int]) -> int:
    """Add pooled per-MWh-net rate columns to the registry. Returns rows set."""
    reg = pd.read_csv(REGISTRY_PATH)
    pooled = rates[rates["year"] == 0].copy()
    n_years = max(len(years), 1)
    pooled["starts_per_year"] = (pooled["starts"] / n_years).round(2)
    by_plant = pooled.set_index(pooled["plant_id"].astype(int))
    plant_ids = reg["plantid"].astype(int)
    for col in _REGISTRY_RATE_COLS:
        src = "starts" if col == "starts_per_year" else col
        if src not in pooled.columns and col != "starts_per_year":
            continue
        reg[col] = plant_ids.map(by_plant[col]).astype(float)
    reg.to_csv(REGISTRY_PATH, index=False)
    return int(plant_ids.isin(by_plant.index).sum())


def merge_years(
    existing: pd.DataFrame, fresh: pd.DataFrame, *, repool: bool
) -> pd.DataFrame:
    """Return ``existing`` with the ``fresh`` years spliced in.

    Per-year rows (``year != 0``) for every year present in ``fresh`` are
    replaced; all other years are carried through untouched. The pooled
    ``year == 0`` block is replaced only when ``repool`` is set — otherwise the
    committed pool survives, because it is the block the dispatch LP reads and
    re-pooling it on a back-year intake would move every solve's CO2 basis.

    Args:
        existing: The artifact as read from disk.
        fresh: Newly derived rows (per-year plus its own pooled block).
        repool: Replace the pooled ``year == 0`` rows with ``fresh``'s.

    Returns:
        The merged table, sorted by ``(plant_id, year)``.
    """
    fresh_years = set(fresh.loc[fresh["year"] != 0, "year"].unique())
    kept = existing[~existing["year"].isin(fresh_years)]
    add = fresh[fresh["year"] != 0]
    if repool:
        kept = kept[kept["year"] != 0]
        add = fresh
    merged = pd.concat([kept, add], ignore_index=True)
    return merged.sort_values(["plant_id", "year"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", default=None)
    parser.add_argument("--states", nargs="+", default=None)
    parser.add_argument("--years", nargs="+", type=int, required=True)
    parser.add_argument("--no-registry", action="store_true")
    parser.add_argument(
        "--repool",
        action="store_true",
        help="Also replace the pooled year==0 block (the rows the LP reads) "
        "with the pool over --years. Default: the committed pool is preserved.",
    )
    parser.add_argument(
        "--overwrite-all",
        action="store_true",
        help="Replace the whole artifact with just --years instead of merging "
        "into the years already on disk (default: merge).",
    )
    args = parser.parse_args()

    states = args.states or list(campd.states_for_iso(args.iso or ""))
    if not states:
        parser.error("supply --states or an --iso with a known state mapping")

    factors = _load_factors()
    logger.info("loaded %d pooled parasitic factors", len(factors))

    df = campd.load_campd_hourly(states, args.years)
    if df.empty:
        logger.error("no CAMPD extracts found for the requested states/years")
        return

    rates = campd.plant_emission_rates(df, factors)

    # Flag coal/gas-blended plants whose single facility rate must not be
    # applied to their separate coal and gas dispatch bins.
    shares = campd.coal_share_by_plant(load_monthly_generation(), args.years)
    rates["coal_share"] = rates["plant_id"].map(shares).round(3)
    rates["mixed"] = (
        rates["coal_share"]
        .between(_MIXED_COAL_SHARE_LO, _MIXED_COAL_SHARE_HI, inclusive="neither")
        .fillna(False)
    )
    n_mixed = rates[rates["year"] == 0]["mixed"].sum()
    if n_mixed:
        logger.info(
            "flagged %d mixed coal/gas plant(s) — rate override will skip them",
            int(n_mixed),
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    pq_path = PROCESSED_DIR / "plant_emission_rates.parquet"
    csv_path = PROCESSED_DIR / "plant_emission_rates.csv"
    # True when the pooled block written below is the one derived from --years
    # (a fresh file, a full overwrite, or an explicit --repool) rather than the
    # committed pool carried through by the merge.
    repooled = args.overwrite_all or args.repool or not pq_path.exists()
    if not args.overwrite_all and pq_path.exists():
        prior = pd.read_parquet(pq_path)
        carried = sorted(set(prior["year"].unique()) - set(args.years))
        rates = merge_years(prior, rates, repool=args.repool)
        logger.info(
            "merged into existing artifact; years carried through: %s "
            "(pooled year==0 %s)",
            carried,
            "REPOOLED over --years" if args.repool else "PRESERVED",
        )
    rates.to_parquet(pq_path, index=False)
    rates.to_csv(csv_path, index=False)
    logger.info("wrote %s and %s", pq_path, csv_path)

    pooled = rates[rates["year"] == 0]
    logger.info(
        "pooled rates over %d plants: CO2 mean=%.1f median=%.1f kg/MWh-net; "
        "NOx mean=%.3f; SO2 mean=%.3f kg/MWh-net",
        len(pooled),
        pooled["co2_kg_per_mwh_net"].mean(),
        pooled["co2_kg_per_mwh_net"].median(),
        pooled["nox_kg_per_mwh_net"].mean(),
        pooled["so2_kg_per_mwh_net"].mean(),
    )

    # The registry mirrors the POOLED block only. A merge that preserved the
    # pool has nothing new to mirror, and rewriting it would divide the old
    # pool's `starts` by this run's year count — so it is skipped, not redone.
    if not args.no_registry and REGISTRY_PATH.exists() and repooled:
        n = _update_registry(rates, args.years)
        logger.info("added emission-rate columns for %d registry plants", n)
    elif not args.no_registry:
        logger.info("registry untouched (pooled block preserved by the merge)")


if __name__ == "__main__":
    main()
