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

Modes (closeout-parasitic-backfill, porting closeout-SOCO-w3's running slope):
``--running-slope`` writes the monthly net-on-gross slope (``measured_running``)
for single-family COAL/CC/ST plants instead of the annual ratio;
``--fleet-scope`` keeps only the ``--iso`` fleets' plants; ``--fill-class-default``
gives every remaining fleet plant its class default (``class_default_fleet``),
the single-fallback proposal.

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

#: plant_group artifact class -> combustion family (running-slope / fill modes)
_FAMILY: dict[str, str] = {
    "COAL": "COAL",
    "CC_REGULAR": "CC",
    "CC_CHP": "CC",
    "ST_GAS": "ST",
    "ST_CHP": "ST",
    "CT_PEAKER": "CT",
    "CT_CHP": "CT",
}
#: families whose monthly gross explains monthly net (steady units); CT is not
#: identified at monthly grain
_RUNNING_FAMILIES: tuple[str, ...] = ("COAL", "CC", "ST")
#: family -> the artifact class whose campd.DEFAULT_PARASITIC_LOAD_PCT it takes
#: (the CHP variants carry the same value)
_FAMILY_DEFAULT_CLASS: dict[str, str] = {
    "COAL": "COAL",
    "CC": "CC_REGULAR",
    "CT": "CT_PEAKER",
    "ST": "ST_GAS",
}

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


def campd_totals(
    states: list[str], years: list[int]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return CAMPD annual plant totals and monthly plant gross over ``states`` x ``years``.

    Reads one state-year extract at a time and reduces it before reading the
    next, then sums across extracts per key. The annual frame equals one
    :func:`campd.annual_plant_totals` call over the concatenated hourly frame
    (every column is a sum, or ``first`` for the name) without holding every
    extract at once. The monthly frame is ``plant_id, year, month, gross_mwh``
    (the running-slope input).
    """
    annual, monthly = [], []
    for state in states:
        for year in years:
            hourly = campd.load_campd_hourly([state], [int(year)])
            if hourly.empty:
                continue
            annual.append(campd.annual_plant_totals(hourly))
            monthly.append(monthly_gross(hourly))
    if not annual:
        return pd.DataFrame(), pd.DataFrame()
    stacked = pd.concat(annual, ignore_index=True)
    sums = ["gross_mwh", "heat_mmbtu", "co2_kg", "nox_kg", "so2_kg", "op_hours"]
    agg = {c: "sum" for c in sums}
    agg["facility_name"] = "first"
    annual_out = stacked.groupby(["plant_id", "year"], as_index=False).agg(agg)
    monthly_out = (
        pd.concat(monthly, ignore_index=True)
        .groupby(["plant_id", "year", "month"], as_index=False)["gross_mwh"]
        .sum()
    )
    return annual_out, monthly_out


def monthly_gross(df: pd.DataFrame) -> pd.DataFrame:
    """Return per ``(plant_id, year, month)`` CAMPD gross MWh from an hourly frame."""
    out = (
        df.assign(month=df["date"].dt.month)
        .groupby(["plant_id", "year", "month"], observed=True)["gross_mw"]
        .sum()
        .rename("gross_mwh")
        .reset_index()
    )
    for k in ("plant_id", "year", "month"):
        out[k] = out[k].astype(int)
    return out


def monthly_gross_net(gross: pd.DataFrame, generation: pd.DataFrame) -> pd.DataFrame:
    """Return monthly CAMPD gross beside EIA-923 combustion net per plant-month.

    ``gross`` is :func:`monthly_gross` output; ``generation`` the EIA-923
    Page-1 frame, filtered to combustion fuels exactly as
    :func:`campd.eia923_combustion_net` does.
    """
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
        net[k] = net[k].astype(int)
    return gross.merge(
        net[["plant_id", "year", "month", "net_mwh"]], on=["plant_id", "year", "month"]
    )


def running_parasitic_factors(
    monthly: pd.DataFrame, families: dict[int, set[str]]
) -> pd.DataFrame:
    """Return pooled RUNNING parasitic factors: the slope of monthly net on monthly gross.

    Annual net / gross charges station service drawn in OFFLINE hours to the
    running output, which for a low-capacity-factor unit is a boundary
    misalignment (rule 14). Over a plant's months with gross > 0,
    ``net = a + b * gross`` separates the two: ``b`` is the running factor,
    ``a`` (negative) the offline draw. Written only for a plant whose fleet
    classes form ONE steady family (COAL, CC or ST) and whose slope lies inside
    the construction's own band (``campd._PARASITIC_MIN``..``_PARASITIC_MAX``)
    with a non-positive intercept (a positive one means the gross misses part
    of the plant); a CT or mixed-family plant is not identified at monthly
    grain and keeps its consumers' class default. Ported from closeout-SOCO-w3
    (``claude/closeout-soco-w3p`` dcc67bc6) so the derive has one version.
    """
    rows = []
    for pid, sub in monthly[monthly["gross_mwh"] > 0].groupby("plant_id"):
        fam = families.get(int(pid), set())
        if len(fam) != 1 or next(iter(fam)) not in _RUNNING_FAMILIES:
            continue
        intercept, slope = campd._ols_intercept_slope(
            sub["gross_mwh"].to_numpy(), sub["net_mwh"].to_numpy()
        )
        # A positive intercept is net the gross cannot explain at zero output
        # (station service cannot be negative): the CAMPD gross misses part of
        # the plant (e.g. an unmetered steam turbine).
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
    cols = [
        "plant_id",
        "year",
        "gross_mwh",
        "net_mwh",
        "parasitic_factor",
        "parasitic_load_pct",
        "source",
        "flag",
    ]
    return pd.DataFrame(rows, columns=cols)


def iso_fleet_family_mw(
    isos: list[str], years: list[int]
) -> dict[int, dict[str, float]]:
    """Return ``{plant_code: {family: pmax_mw}}`` over ``isos``' own EIA-860 fleets.

    Each year loads its own EIA-860 vintage, the population the solve sees; a
    family's MW is its largest summed ``pmax_mw`` in any year. A family is the
    combustion artifact family of the generator's ``plant_group``
    (:data:`_FAMILY`); a non-combustion generator maps to none, but its plant
    is still listed (with an empty dict) so fleet scope keeps it.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.paths import set_eia860_vintage
    from market_sim.config.plant_taxonomy import artifact_class
    from market_sim.data.fleet import load_fleet_from_csv

    out: dict[int, dict[str, float]] = {}
    try:
        for iso in isos:
            for year in years:
                set_eia860_vintage(int(year))
                year_mw: dict[tuple[int, str], float] = {}
                for gen in load_fleet_from_csv(
                    iso, get_iso_config(iso), year=int(year)
                ):
                    code = int(gen.plant_code)
                    if code <= 0:
                        continue
                    out.setdefault(code, {})
                    fam = _FAMILY.get(artifact_class(gen.plant_group))
                    if fam:
                        key = (code, fam)
                        year_mw[key] = year_mw.get(key, 0.0) + float(gen.pmax_mw)
                for (code, fam), mw in year_mw.items():
                    out[code][fam] = max(out[code].get(fam, 0.0), mw)
    finally:
        set_eia860_vintage(None)
    return out


def fleet_class_default_rows(
    parasitic: pd.DataFrame, family_mw: dict[int, dict[str, float]]
) -> pd.DataFrame:
    """Return pooled class-default rows for fleet plants ``parasitic`` has no pooled row for.

    The single-fallback proposal (rule 19): every CEMS fleet plant carries a
    pooled row, so every consumer converts it on the same factor — today the
    HR derives fall back to their artifact class default while the benchmark
    and the tranche derives fall back to 1.0 (gross as net). The class is the
    plant's largest combustion family by fleet MW, valued at
    :data:`campd.DEFAULT_PARASITIC_LOAD_PCT`; source ``class_default_fleet``.
    A plant with no combustion family gets no row.
    """
    have = set(parasitic.loc[parasitic["year"] == 0, "plant_id"].astype(int))
    rows = []
    for code, fams in sorted(family_mw.items()):
        if code in have or not fams:
            continue
        fam = max(sorted(fams), key=lambda f: fams[f])
        pct = campd.DEFAULT_PARASITIC_LOAD_PCT[_FAMILY_DEFAULT_CLASS[fam]]
        rows.append(
            {
                "plant_id": int(code),
                "year": 0,
                "gross_mwh": 0.0,
                "net_mwh": 0.0,
                "parasitic_factor": round(1.0 - pct, 6),
                "parasitic_load_pct": round(pct, 6),
                "source": "class_default_fleet",
                "flag": f"fallback_{fam.lower()}",
            }
        )
    return pd.DataFrame(rows, columns=parasitic.columns)


def merge_parasitic(existing: pd.DataFrame, parasitic: pd.DataFrame) -> pd.DataFrame:
    """Return ``existing`` extended by the measured rows of ``parasitic`` it lacks.

    Every committed ``(plant_id, year)`` row is kept byte-identical; only
    plant-years absent from ``existing`` are added, and only measured ones
    (``measured`` or ``measured_running``).

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
        parasitic["source"].isin(("measured", "measured_running"))
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
    parser.add_argument(
        "--fleet-scope",
        action="store_true",
        help="Keep only plants in --iso's own EIA-860 fleet(s) over --years. A "
        "state extract also carries plants of a neighbouring ISO, so a scoped "
        "back-fill must not write them (rule 25; closeout-SOCO-w3).",
    )
    parser.add_argument(
        "--running-slope",
        action="store_true",
        help="Write the pooled RUNNING factor (slope of monthly EIA-923 net on "
        "monthly CAMPD gross, source measured_running) for single-family "
        "COAL/CC/ST plants instead of the annual ratio (closeout-SOCO-w3; see "
        "running_parasitic_factors).",
    )
    parser.add_argument(
        "--fill-class-default",
        action="store_true",
        help="After the derive (and merge), give every --iso fleet plant still "
        "without a pooled row its largest family's class default (source "
        "class_default_fleet), so every consumer shares one fallback (rule 19; "
        "see fleet_class_default_rows).",
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
    fleet_modes = args.fleet_scope or args.running_slope or args.fill_class_default
    if fleet_modes and not isos:
        parser.error(
            "--fleet-scope / --running-slope / --fill-class-default need --iso"
        )
    if args.check and (args.running_slope or args.fill_class_default):
        parser.error("--check reproduces the annual per-year rows only")

    logger.info("loading CAMPD hourly for states=%s years=%s", states, args.years)
    campd_annual, campd_monthly = campd_totals(states, args.years)
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

    family_mw = iso_fleet_family_mw(isos, args.years) if fleet_modes else {}
    if args.running_slope:
        families = {code: set(fams) for code, fams in family_mw.items()}
        parasitic = running_parasitic_factors(
            monthly_gross_net(
                campd_monthly, generation[generation["year"].isin(args.years)]
            ),
            families,
        )
        logger.info("running slope: %d plants identified", len(parasitic))
    else:
        parasitic = campd.compute_parasitic_factors(
            campd_annual, eia_net, plant_groups=_registry_plant_groups()
        )
    if args.fleet_scope:
        before = parasitic["plant_id"].nunique()
        parasitic = parasitic[parasitic["plant_id"].astype(int).isin(set(family_mw))]
        logger.info(
            "fleet scope: kept %d of %d plants", parasitic["plant_id"].nunique(), before
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
    if args.fill_class_default:
        fill = fleet_class_default_rows(parasitic, family_mw)
        logger.info("fill: %d fleet plants given their class default", len(fill))
        parasitic = (
            pd.concat([parasitic, fill], ignore_index=True)
            .sort_values(["plant_id", "year"], kind="stable")
            .reset_index(drop=True)
        )

    parasitic.to_parquet(pq_path, index=False)
    parasitic.to_csv(csv_path, index=False)
    logger.info("wrote %s and %s", pq_path, csv_path)

    pooled = parasitic[parasitic["year"] == 0]
    measured = pooled[pooled["source"].isin(("measured", "measured_running"))]
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
