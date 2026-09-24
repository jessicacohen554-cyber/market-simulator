"""Per-year backcast fleets and the year-stacked measured-heat-rate layout (F1 D4).

Shared by the five measured-heat-rate derives
(``scripts/data/derive_campd_{ct,coal,gas_st,cc}_heat_rates.py`` and
``scripts/data/derive_chp_power_only_heat_rates.py``), which before F1 pooled
CAMPD 2023-2025 against the CANONICAL snapshot fleet only — so a plant that
retired before 2023 was never in the target set and never got a measured rate
(docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md §1 D4).

Two things live here:

* :func:`backcast_fleets` — the ISO's fleet for each backcast year exactly as
  the post-F1 backcast default builds it: the year-matched ``vintage_<Y>/``
  table where one is committed (the canonical snapshot otherwise) plus the
  within-window retiree channel, restricted to units online in ``Y``. Its union
  (:func:`union_fleet`) is the derive's target population, so every plant the
  backcast can dispatch in ANY year 2019-2025 is eligible for a measured rate.
* The artifact layout. Every measured artifact carries a ``year`` column:
  ``year == 0`` is the plant's POOLED rate over the whole window, ``year == Y``
  its rate from year ``Y``'s hours alone. The per-year row exists only where the
  derive's OWN trust gate (its unchanged minimum-qualifying-hours constant)
  clears on that year's hours by themselves — so the minimum-hours rule for a
  year rate is not a new threshold, it is the one each derive already uses to
  decide whether a pooled rate is trustworthy, applied to the year's hours. The
  loader (``market_sim.data.fleet.campd_bins._measured_heat_rates``) takes the
  solve year's own ``ok`` row where one exists, else the pooled ``ok`` row.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import EIA_860_DIR, set_eia860_vintage
from market_sim.data.fleet import load_fleet_from_csv
from market_sim.data.fleet.eia860 import load_retired_within_window

#: The program's backcast span (rule 22 as amended: 2019-2025 for every ISO).
#: The derives pool and slice over exactly these CAMPD vintages by default.
BACKCAST_YEARS: tuple[int, ...] = tuple(range(2019, 2026))

#: The ``year`` value of a POOLED row (the same convention as
#: ``plant_emission_rates.parquet``'s ``year == 0`` pooled rows).
POOLED_YEAR: int = 0


def _online_in(gen, year: int) -> bool:
    """True when ``gen`` operated for any part of calendar ``year``."""
    if int(getattr(gen, "online_year", 0) or 0) > year:
        return False
    ret = getattr(gen, "retirement_year", None)
    return ret is None or int(ret) >= year


def backcast_fleets(
    iso: str, years: Iterable[int] = BACKCAST_YEARS, **flags
) -> dict[int, list]:
    """Return ``{year: fleet}`` as the post-F1 backcast default loads each year.

    Args:
        iso: ISO identifier.
        years: Backcast years to load.
        **flags: ``load_fleet_from_csv`` keyword flags (the derives' PROVENANCE
            recipe; they move only the reported incumbent rate).

    Returns:
        One generator list per year, units online in that year only.
    """
    iso = iso.upper()
    cfg = get_iso_config(iso)
    out: dict[int, list] = {}
    for year in years:
        vintage = year if (EIA_860_DIR / f"vintage_{year}").is_dir() else None
        set_eia860_vintage(vintage)
        try:
            gens = load_fleet_from_csv(iso, cfg, year=year, **flags)
            gens = gens + load_retired_within_window(iso, cfg, year=year)
        finally:
            set_eia860_vintage(None)
        out[int(year)] = [g for g in gens if _online_in(g, int(year))]
    return out


def union_fleet(fleets: dict[int, list]) -> list:
    """Return one generator per ``unit_id`` across years, the LATEST year's record."""
    latest: dict[str, object] = {}
    for year in sorted(fleets):
        for gen in fleets[year]:
            latest[str(gen.unit_id)] = gen
    return list(latest.values())


def stack_year_tables(
    pooled: pd.DataFrame,
    per_year: dict[int, pd.DataFrame],
) -> pd.DataFrame:
    """Stack a pooled plant table and its per-year tables into one artifact.

    Pooled rows carry ``year == 0`` and come first; each year's rows follow in
    year order. Column order is the pooled table's, with ``year`` inserted
    after ``plant_code``.
    """
    frames = [pooled.assign(year=POOLED_YEAR)]
    for year in sorted(per_year):
        table = per_year[year]
        if table is not None and not table.empty:
            frames.append(table.assign(year=int(year)))
    out = pd.concat(frames, ignore_index=True)
    cols = [c for c in pooled.columns if c != "year"]
    cols.insert(cols.index("plant_code") + 1 if "plant_code" in cols else 0, "year")
    extra = [c for c in out.columns if c not in cols]
    return out[cols + extra]


def per_year_tables(
    years: Iterable[int], build: Callable[[int], pd.DataFrame | None]
) -> dict[int, pd.DataFrame]:
    """Run ``build(year)`` for each year, dropping years with no qualifying unit.

    ``build`` is the derive's own pooled construction restricted to one year's
    hours; a derive that finds no qualifying hours raises ``SystemExit`` (its
    pooled contract), which here means only "no per-year row for that year".
    """
    out: dict[int, pd.DataFrame] = {}
    for year in years:
        try:
            table = build(int(year))
        except SystemExit:
            continue
        if table is not None and not table.empty:
            out[int(year)] = table
    return out


def class_capacity(fleet: list, klass: str) -> dict[int, float]:
    """Return ``{plant_code: MW}`` over a fleet's generators of one class."""
    caps: dict[int, float] = {}
    for gen in fleet:
        if gen.plant_group != klass:
            continue
        code = int(gen.plant_code or 0)
        if code:
            caps[code] = caps.get(code, 0.0) + float(gen.pmax_mw)
    return caps


def class_heat_rates(fleet: list, klass: str) -> dict[int, float]:
    """Return the capacity-weighted assigned heat rate per plant for one class."""
    num: dict[int, float] = {}
    den: dict[int, float] = {}
    for gen in fleet:
        if gen.plant_group != klass:
            continue
        code = int(gen.plant_code or 0)
        if not code:
            continue
        num[code] = num.get(code, 0.0) + float(gen.pmax_mw) * float(gen.heat_rate)
        den[code] = den.get(code, 0.0) + float(gen.pmax_mw)
    return {c: num[c] / den[c] for c in num if den[c] > 0}
