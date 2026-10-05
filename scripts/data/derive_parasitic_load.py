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
    python scripts/data/derive_parasitic_load.py --iso ERCOT --years 2023 2024 2025
    python scripts/data/derive_parasitic_load.py --states TX --years 2023
    python scripts/data/derive_parasitic_load.py --states PA NJ MD --years 2023 2024
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

#: plant_group artifact class -> combustion family (running-slope mode)
_FAMILY: dict[str, str] = {
    "COAL": "COAL",
    "CC_REGULAR": "CC",
    "CC_CHP": "CC",
    "ST_GAS": "ST",
    "ST_CHP": "ST",
    "CT_PEAKER": "CT",
    "CT_CHP": "CT",
}
#: families whose monthly gross explains monthly net (steady units); CT is not identified at monthly grain
_RUNNING_FAMILIES: tuple[str, ...] = ("COAL", "CC", "ST")

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


def iso_fleet_plant_families(iso: str, years: list[int]) -> dict[int, set[str]]:
    """Return ``{plant_code: {family, ...}}`` for ``iso``'s own EIA-860 fleet over ``years``.

    Each year loads its own EIA-860 vintage, the population the solve sees. A family is the
    combustion artifact family of the generator's ``plant_group`` (:data:`_FAMILY`); a
    non-combustion generator (solar, storage, hydro, nuclear) maps to no family.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.paths import set_eia860_vintage
    from market_sim.config.plant_taxonomy import artifact_class
    from market_sim.data.fleet import load_fleet_from_csv

    out: dict[int, set[str]] = {}
    for year in years:
        set_eia860_vintage(int(year))
        for gen in load_fleet_from_csv(iso, get_iso_config(iso), year=int(year)):
            code = int(gen.plant_code)
            if code <= 0:
                continue
            fam = _FAMILY.get(artifact_class(gen.plant_group))
            out.setdefault(code, set())
            if fam:
                out[code].add(fam)
    return out


def monthly_gross_net(df: pd.DataFrame, generation: pd.DataFrame) -> pd.DataFrame:
    """Return per ``(plant_id, year, month)`` CAMPD gross MWh beside EIA-923 combustion net MWh."""
    gross = (
        df.assign(month=df["date"].dt.month)
        .groupby(["plant_id", "year", "month"], observed=True)["gross_mw"]
        .sum()
        .rename("gross_mwh")
        .reset_index()
    )
    fuels = generation["fuel_type"].astype(str).str.upper()
    comb = generation[~fuels.isin(campd._NON_COMBUSTION_FUELS)]
    cols = list(campd._EIA923_MONTH_COLUMNS)
    net = (
        comb.groupby(["plant_id", "year"], observed=True)[cols]
        .sum()
        .reset_index()
        .melt(id_vars=["plant_id", "year"], var_name="col", value_name="net_mwh")
    )
    net["month"] = net["col"].map({c: i + 1 for i, c in enumerate(cols)})
    for k in ("plant_id", "year"):
        gross[k] = gross[k].astype(int)
        net[k] = net[k].astype(int)
    return gross.merge(
        net[["plant_id", "year", "month", "net_mwh"]], on=["plant_id", "year", "month"]
    )


def running_parasitic_factors(
    monthly: pd.DataFrame, families: dict[int, set[str]]
) -> pd.DataFrame:
    """Return pooled RUNNING parasitic factors: the slope of monthly net on monthly gross.

    Annual net / gross charges station service drawn in OFFLINE hours to the running output, which for
    a low-capacity-factor unit is a boundary misalignment (rule 14). Over a plant's months with gross > 0,
    ``net = a + b * gross`` separates the two: ``b`` is the running factor, ``a`` (negative) the offline
    draw. Written only for a plant whose fleet classes form ONE steady family (COAL, CC or ST) and whose
    slope lies inside the construction's own band (``campd._PARASITIC_MIN``..``_PARASITIC_MAX``) with a
    non-positive intercept (a positive one means the gross misses part of the plant); a CT
    or mixed-family plant is not identified at monthly grain and keeps its consumers' class default.
    """
    rows = []
    for pid, sub in monthly[monthly["gross_mwh"] > 0].groupby("plant_id"):
        fam = families.get(int(pid), set())
        if len(fam) != 1 or next(iter(fam)) not in _RUNNING_FAMILIES:
            continue
        intercept, slope = campd._ols_intercept_slope(
            sub["gross_mwh"].to_numpy(), sub["net_mwh"].to_numpy()
        )
        # A positive intercept is net the gross cannot explain at zero output (station service cannot
        # be negative): the CAMPD gross misses part of the plant (e.g. an unmetered steam turbine).
        if intercept > 0.0 or not (
            campd._PARASITIC_MIN <= slope <= campd._PARASITIC_MAX
        ):
            continue
        rows.append(
            {
                "plant_id": int(pid),
                "year": 0,
                "gross_mwh": round(float(sub["gross_mwh"].sum()), 3),
                "net_mwh": round(float(sub["net_mwh"].sum()), 3),
                "parasitic_factor": round(float(slope), 6),
                "parasitic_load_pct": round(float(1.0 - slope), 6),
                "source": "measured_running",
                "flag": "ok",
            }
        )
    return pd.DataFrame(rows)


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
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Back-fill the existing output instead of replacing it: every "
        "committed (plant_id, year) row is kept and only plant-years the file "
        "lacks are added. Required for a scoped back-fill — this output is "
        "shared across ISOs, so a plain write would delete the rest.",
    )
    parser.add_argument(
        "--fleet-scope",
        action="store_true",
        help="Keep only plants in --iso's own EIA-860 fleet over --years. A "
        "state extract also carries plants of a neighbouring ISO (MS/FL plants "
        "of MISO in SOCO's states), so a scoped back-fill must not write them "
        "(rule 25 [R-ISO-SCOPE]; closeout-SOCO-w3).",
    )
    parser.add_argument(
        "--measured-only",
        action="store_true",
        help="Write only rows whose factor was measured (source == measured). "
        "A class_default row carries a generic default that would replace the "
        "consumer's own class default with another estimate, not a measurement "
        "(rule 14); a plant without a measured row keeps its consumers' class "
        "defaults (closeout-SOCO-w3).",
    )
    parser.add_argument(
        "--running-slope",
        action="store_true",
        help="Write the pooled RUNNING factor (slope of monthly EIA-923 net on monthly CAMPD gross, "
        "source measured_running) for single-family COAL/CC/ST plants instead of the annual "
        "ratio (closeout-SOCO-w3; see running_parasitic_factors).",
    )
    args = parser.parse_args()
    if (args.fleet_scope or args.running_slope) and not args.iso:
        parser.error("--fleet-scope / --running-slope need --iso")

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

    families = (
        iso_fleet_plant_families(args.iso, args.years)
        if args.fleet_scope or args.running_slope
        else {}
    )
    if args.running_slope:
        parasitic = running_parasitic_factors(
            monthly_gross_net(df, generation[generation["year"].isin(args.years)]),
            families,
        )
        logger.info("running slope %s: %d plants identified", args.iso, len(parasitic))
    else:
        parasitic = campd.compute_parasitic_factors(
            campd_annual, eia_net, plant_groups=_registry_plant_groups()
        )
    if args.fleet_scope:
        before = parasitic["plant_id"].nunique()
        parasitic = parasitic[parasitic["plant_id"].astype(int).isin(set(families))]
        logger.info(
            "fleet scope %s: kept %d of %d plants",
            args.iso,
            parasitic["plant_id"].nunique(),
            before,
        )
    if args.measured_only:
        parasitic = parasitic[
            parasitic["source"].isin(("measured", "measured_running"))
        ]

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    pq_path = PROCESSED_DIR / "parasitic_load_factors.parquet"
    csv_path = PROCESSED_DIR / "parasitic_load_factors.csv"

    if args.merge and pq_path.exists():
        # This file is SHARED across every ISO and every year, and the plain
        # write replaces it wholesale with just the requested states/years —
        # so a scoped back-fill without --merge would silently delete every
        # other ISO's rows. Merge keeps every committed (plant_id, year) row
        # byte-identical and adds only plant-years the file does not carry.
        #
        # The pooled `year == 0` row is the per-plant fallback averaged over
        # whatever years were passed. It is kept ONLY for plants the file does
        # not already carry one for: writing it for an existing plant would
        # move an already-committed default on the strength of a narrower year
        # set, while a plant new to the file has no default to move and needs
        # one. Adding coverage must not move values the file already owns
        # (rule 22 consistency clause).
        existing = pd.read_parquet(pq_path)
        have = set(map(tuple, existing[["plant_id", "year"]].to_numpy()))
        have_plants = set(existing["plant_id"].to_numpy())
        cand = parasitic[
            (parasitic["year"] != 0) | (~parasitic["plant_id"].isin(have_plants))
        ]
        keys = map(tuple, cand[["plant_id", "year"]].to_numpy())
        fresh = cand[[k not in have for k in keys]]
        parasitic = (
            pd.concat([existing, fresh], ignore_index=True)
            .sort_values(["plant_id", "year"], kind="stable")
            .reset_index(drop=True)
        )
        logger.info(
            "merge: kept %d committed rows, added %d new plant-years, file now %d",
            len(existing),
            len(fresh),
            len(parasitic),
        )

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
