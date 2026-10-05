"""Derive per-plant parasitic-load factors from CAMPD gross vs EIA-923 net.

A plant's parasitic-load factor is annual net generation (EIA-923 Page 1,
combustion units) divided by annual gross generation (EPA CAMPD CEMS). It is
the fraction of gross output that reaches the grid after station service, and
is used to scale CAMPD's measured gross down to net for the hourly dispatch
correlation and to set per-MWh-net emission rates.

This script is ISO-agnostic: pass ``--states`` and ``--years`` directly, or
``--iso`` (one or more ISOs, or ``ALL`` for every ISO in
:data:`market_sim.data.campd.ISO_STATES`) to use that lookup. CAMPD is read one
state-year at a time and reduced to annual plant totals before the next is
read, so an all-ISO pass never holds more than one extract in memory. It
writes ``data/raw/_processed-legacy/parasitic_load_factors.{parquet,csv}`` (one row per
plant-year plus a pooled ``year == 0`` summary per plant) and, unless
``--no-registry``, back-fills the ``parasitic_load_pct`` column of
``data/raw/reference/master-plant-registry.csv``.

Usage:
    python scripts/data/derive_parasitic_load.py --iso ERCOT --years 2023 2024 2025
    python scripts/data/derive_parasitic_load.py --states TX --years 2023
    python scripts/data/derive_parasitic_load.py --states PA NJ MD --years 2023 2024
    python scripts/data/derive_parasitic_load.py --iso ALL --years 2019 2020 2021 \
        2022 2023 2024 2025 --check            # reproduce committed rows, write nothing
    python scripts/data/derive_parasitic_load.py --iso ALL --years 2019 2020 2021 \
        2022 2023 2024 2025 --merge --no-registry   # back-fill every uncovered plant

``--check`` recomputes every requested plant-year and compares it with the
committed file (no write): it is the reproduction gate a back-fill runs first,
so a merge only ever extends a construction shown to reproduce what the file
already owns.
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

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("derive_parasitic_load")

# W1 collapsed the old inputs/ tree into data/raw/ — these are the live
# locations the model reads (config/paths.py PROCESSED_DIR, REFERENCE_DIR).
PROCESSED_DIR = PROCESSED_DIR
REGISTRY_PATH = PLANT_REGISTRY_CSV


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


def campd_annual_totals(states: list[str], years: list[int]) -> pd.DataFrame:
    """Return :func:`campd.annual_plant_totals` over ``states`` x ``years``.

    Reads one state-year extract at a time and reduces it to plant-year totals
    before reading the next, then sums across extracts per ``(plant_id,
    year)``. Every column of :func:`campd.annual_plant_totals` is a sum (or
    ``first`` for the name), so this equals one call over the concatenated
    frame, without holding every hourly extract at once.
    """
    frames = []
    for state in states:
        for year in years:
            hourly = campd.load_campd_hourly([state], [int(year)])
            if not hourly.empty:
                frames.append(campd.annual_plant_totals(hourly))
    if not frames:
        return pd.DataFrame()
    stacked = pd.concat(frames, ignore_index=True)
    sums = ["gross_mwh", "heat_mmbtu", "co2_kg", "nox_kg", "so2_kg", "op_hours"]
    agg = {c: "sum" for c in sums}
    agg["facility_name"] = "first"
    return stacked.groupby(["plant_id", "year"], as_index=False).agg(agg)


def merge_parasitic(existing: pd.DataFrame, parasitic: pd.DataFrame) -> pd.DataFrame:
    """Return ``existing`` extended by the measured rows of ``parasitic`` it lacks.

    Every committed ``(plant_id, year)`` row is kept byte-identical; only
    plant-years absent from ``existing`` are added, and only ``measured`` ones.

    * A freshly pooled ``year == 0`` row is added only for a plant ``existing``
      carries no pooled row for: writing one over a committed pooled row would
      move an already-committed default on the strength of a different year
      set (rule 23). Keyed on the pooled row itself, not on "any row": a plant
      the file carries only per-year rows for (the 2022 back-fill left 106 such)
      has no default to move, and the pooled row is the only one consumers read.
    * A ``class_default`` row is never added. Its class comes from the plant
      registry, which carries a ``plant_group`` for almost no plant outside
      ERCOT, so the "default" written is the generic
      ``campd._DEFAULT_PARASITIC_LOAD_PCT`` (0.97) whatever the class. Left
      absent, every consumer applies its own class fallback instead (the HR
      derives their artifact class default; the benchmark 1.0), exactly as
      before the back-fill: a back-fill adds measurement, never an estimate.
    """
    have = set(map(tuple, existing[["plant_id", "year"]].to_numpy()))
    have_pooled = set(existing.loc[existing["year"] == 0, "plant_id"].to_numpy())
    cand = parasitic[
        (parasitic["source"] == "measured")
        & ((parasitic["year"] != 0) | (~parasitic["plant_id"].isin(have_pooled)))
    ]
    keys = map(tuple, cand[["plant_id", "year"]].to_numpy())
    fresh = cand[[k not in have for k in keys]]
    logger.info(
        "merge: kept %d committed rows, added %d measured plant-years "
        "(%d pooled), file now %d",
        len(existing),
        len(fresh),
        int((fresh["year"] == 0).sum()),
        len(existing) + len(fresh),
    )
    return (
        pd.concat([existing, fresh], ignore_index=True)
        .sort_values(["plant_id", "year"], kind="stable")
        .reset_index(drop=True)
    )


def reproduce_check(
    existing: pd.DataFrame, parasitic: pd.DataFrame, tol: float
) -> pd.DataFrame:
    """Compare recomputed per-year rows with the committed ones.

    Joins on ``(plant_id, year)`` for every per-year row (``year != 0``) the
    two frames share, and returns one row per shared plant-year with both
    factors and sources, ``abs_diff`` and ``within_tol`` (``abs_diff <= tol``
    and the same ``source``). Pooled rows are excluded: each was pooled over
    the year set of the run that first wrote it, which differs between ISOs.
    """
    cols = ["plant_id", "year", "parasitic_factor", "source", "gross_mwh", "net_mwh"]
    joined = existing.loc[existing["year"] != 0, cols].merge(
        parasitic.loc[parasitic["year"] != 0, cols],
        on=["plant_id", "year"],
        suffixes=("_committed", "_recomputed"),
    )
    joined["abs_diff"] = (
        joined["parasitic_factor_committed"] - joined["parasitic_factor_recomputed"]
    ).abs()
    joined["within_tol"] = (joined["abs_diff"] <= tol) & (
        joined["source_committed"] == joined["source_recomputed"]
    )
    return joined


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iso",
        nargs="+",
        default=None,
        help="ISO(s) whose states to load; ALL for every ISO in campd.ISO_STATES.",
    )
    parser.add_argument("--states", nargs="+", default=None, help="CAMPD state codes.")
    parser.add_argument("--years", nargs="+", type=int, required=True)
    parser.add_argument(
        "--no-registry",
        action="store_true",
        help="Skip back-filling parasitic_load_pct in the registry.",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Back-fill the existing output instead of replacing it: every "
        "committed (plant_id, year) row is kept and only plant-years the file "
        "lacks are added. Required for a scoped back-fill — this output is "
        "shared across ISOs, so a plain write would delete the rest.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Recompute and compare with the committed file; write nothing. "
        "Exits non-zero when a shared plant-year differs by more than --tol.",
    )
    parser.add_argument("--tol", type=float, default=0.005)
    parser.add_argument(
        "--check-out", default=None, help="Optional CSV of the --check comparison."
    )
    args = parser.parse_args()

    isos = args.iso or []
    if [i.upper() for i in isos] == ["ALL"]:
        isos = list(campd.ISO_STATES)
    states = args.states or sorted(
        {st for iso in isos for st in campd.states_for_iso(iso)}
    )
    if not states:
        parser.error("supply --states or an --iso with a known state mapping")

    logger.info("loading CAMPD hourly for states=%s years=%s", states, args.years)
    campd_annual = campd_annual_totals(states, args.years)
    if campd_annual.empty:
        logger.error("no CAMPD extracts found for the requested states/years")
        return
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

    if args.check:
        cmp = reproduce_check(pd.read_parquet(pq_path), parasitic, args.tol)
        if args.check_out:
            cmp.to_csv(args.check_out, index=False)
        bad = cmp[~cmp["within_tol"]]
        logger.info(
            "check: %d shared plant-years, %d within %.3f (same source), "
            "max |diff| %.6f",
            len(cmp),
            len(cmp) - len(bad),
            args.tol,
            cmp["abs_diff"].max() if len(cmp) else 0.0,
        )
        sys.exit(1 if len(bad) else 0)

    if args.merge and pq_path.exists():
        # This file is SHARED across every ISO and every year, and the plain
        # write replaces it wholesale with just the requested states/years —
        # so a scoped back-fill without --merge would silently delete every
        # other ISO's rows (rule 25).
        parasitic = merge_parasitic(pd.read_parquet(pq_path), parasitic)

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
