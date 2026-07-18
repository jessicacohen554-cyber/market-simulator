"""Commercial-operation-date (COD) vintage ramp — the single COD source.

A backcast solves a single historical year, but the dispatch fleet snapshot
(the curated ERCOT CAMPD bins / the EIA-860 generator parquet) is a *recent*
vintage that includes units commissioned **after** the year being solved. Left
unfiltered, a 2023 backcast dispatches GWs of capacity that were not yet built —
inflating reserve headroom and suppressing the scarcity prices the LP can set.

Renewables and storage already respect their commercial-operation dates
(:func:`market_sim.data.renewables` ramps wind/solar by ``Operating Month`` /
``Operating Year``; storage enters by vintage). This module extends the **same
month-precise rule to every thermal/nuclear/oil generator** so the default
backcast fleet reflects only what was actually online in the solved year.

The mechanism is a single :func:`monthly_online_mask` applied inside
:func:`market_sim.data.fleet.generators_to_fleet_arrays` (gated on
``config.cod_ramp_enabled``, default on for backcasts). Each dispatched
generator's commercial-operation / retirement date drives a 12-month online
mask: a unit that came online (or retired) part-way through the solved year is
available **only in the months it actually operated**, with ``min_gen`` (the
hard must-run floor) zeroed in the offline months so the LP lower bound cannot
force a not-yet-built / retired unit to run.

The COD date is sourced from EIA-860, the authoritative commissioning record —
``eia860_generator_operable.parquet`` carries a month-precise ``Operating
Month`` / ``Operating Year`` (and ``Planned Retirement Month`` / ``Year``) for
~every operable generator. :func:`load_cod_map` reduces it to a per-plant
``{plant_code: (online_year, online_month, retirement_year, retirement_month)}``
map (the plant's earliest unit defines its online date; a retirement applies
only when the *whole* plant retires). The ERCOT CAMPD bins carry no build date
of their own, so this plant-code map is what gives them month precision; raw
EIA-860 :class:`Generator` objects fall back to their own ``online_year`` /
``online_month`` when their plant is absent from the map.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

import numpy as np
import pandas as pd

from market_sim.config.paths import PLANT_REGISTRY_CSV

logger = logging.getLogger(__name__)

_REGISTRY = PLANT_REGISTRY_CSV

# Opt-in clean-data read path (mirrors market_sim.data.fuel / outages /
# zone_assignment). When MARKET_SIM_USE_CLEAN is truthy, the registry-only
# year_built back-fill reads the curated reference/plant-registry table
# instead of the raw master-plant-registry.csv. OFF by default; falls back to
# raw when the clean partition is absent.
_USE_CLEAN_ENV = "MARKET_SIM_USE_CLEAN"
_USE_CLEAN_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _use_clean() -> bool:
    """Whether the opt-in clean-data read path is enabled (default ``False``)."""
    return os.environ.get(_USE_CLEAN_ENV, "").strip().lower() in _USE_CLEAN_TRUTHY


def _registry_year_built() -> pd.DataFrame:
    """Return the plant registry's ``(plant_id, year_built)`` rows, no nulls.

    Reads the curated ``reference/plant-registry`` clean table when
    :func:`_use_clean` is set and the partition exists (written by
    ``scripts/data/curate_reference.py``); otherwise reads ``_REGISTRY`` (the raw
    ``master-plant-registry.csv``) directly. Returns an empty frame when
    neither source is available.
    """
    if _use_clean():
        from scripts.lib.clean_io import clean_exists, read_clean

        if clean_exists("reference", market="plant-registry"):
            df = read_clean(
                "reference", market="plant-registry", columns=["plant_id", "year_built"]
            )
            return df.dropna(subset=["plant_id", "year_built"])
    if not _REGISTRY.exists():
        return pd.DataFrame(columns=["plant_id", "year_built"])
    reg = pd.read_csv(_REGISTRY, usecols=["plantid", "year_built"])
    reg = reg.rename(columns={"plantid": "plant_id"})
    return reg.dropna(subset=["plant_id", "year_built"])


# The month-precise generator-level EIA-860 operable schedule (Operating Month /
# Year, Planned Retirement Month / Year per generator) is read from the active
# vintage directory (paths.active_eia860_dir) inside _load_cod_map, so a
# year-matched vintage switch is honored and the cache keys on the directory.
#
# Alongside the operable schedule, the same directory's within-window retiree
# parquet (eia860_generator_retired_within_window.parquet, built by
# ``scripts/data/process_eia860.py --retired-window-from`` from the final EIA-860
# vintages' "Retired and Canceled" sheets) is unioned into the COD map so the
# ramp can age out whole plants that retired mid-window and so are absent from
# the default recent operable vintage (e.g. Mystic, plant 1588, retired
# mid-2024). It carries the actual retirement in ``planned_retirement_*``. The
# fleet loader injects the matching generators (the snapshot can only drop a
# unit it contains). A year-matched native vintage carries those exits in its
# own operable file and ships no retiree parquet, so the union is a no-op there
# (no double-count).
_RETIRED_WINDOW_NAME = "eia860_generator_retired_within_window.parquet"

# Month assumed for a unit whose COD *year* is known but whose month is not
# (e.g. a plant carried only by the master registry's year-only ``year_built``,
# absent from the month-precise EIA-860 operable schedule). A mid-year default
# keeps a same-year unit online for roughly half the year — the neutral
# assumption, matching the half-year prorate the year-only ramp used to apply.
COD_FALLBACK_MONTH = 7

# A ``Generator.online_year`` at or below this sentinel means "vintage unknown"
# (the model default is 2000 for fleets that never set a real commissioning
# year), so it must not drop a genuinely pre-existing unit.
_ONLINE_YEAR_SENTINEL = 2000

# One per-plant COD record: month-precise online and (optional) retirement date.
CodEntry = tuple[int, int, int | None, int | None]


def _cod_work_frame(path, columns: dict[str, str]) -> "pd.DataFrame | None":
    """Read an EIA-860 generator parquet into the COD reducer's column frame.

    ``columns`` maps the reducer's short names (``pc``/``oy``/``om``/``cap``/
    ``ry``/``rm``) to the source parquet's actual column names, so the operable
    sheet (raw EIA-860 headers) and the within-window retiree parquet (canonical
    schema) feed the same per-plant reduction. Returns ``None`` when the file is
    absent.
    """
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    frame = pd.DataFrame(
        {
            short: pd.to_numeric(df.get(src), errors="coerce")
            for short, src in columns.items()
        }
    )
    return frame.dropna(subset=["pc", "oy"])


def load_cod_map() -> dict[int, CodEntry]:
    """Public entry point: build the COD map for the active EIA-860 vintage.

    Resolves the directory through :func:`paths.active_eia860_dir` (so a
    ``ScenarioConfig.eia860_vintage_year`` switch is honored) and defers to the
    directory-keyed cache below.

    When the clean seam is on (``MARKET_SIM_USE_CLEAN``), the COD map is built
    from the curated clean ``fleet`` registry instead (:func:`_load_cod_map_clean`),
    routing the active vintage directory to its clean partition year so the same
    ``eia860_vintage_year`` switch is honored end to end.
    """
    from market_sim.config.paths import active_eia860_dir

    # Lazy import to dodge the fleet <-> cod_ramp module-load cycle (fleet imports
    # cod_ramp at module top); both are fully imported by the time this is called.
    from market_sim.data.fleet import _clean_fleet_year, _use_clean

    if _use_clean():
        return _load_cod_map_clean(_clean_fleet_year(active_eia860_dir()))
    return _load_cod_map(active_eia860_dir())


@lru_cache(maxsize=4)
def _load_cod_map_clean(partition_year: int) -> dict[int, CodEntry]:
    """Build the COD map from the curated clean ``fleet`` registry.

    The clean counterpart of :func:`_load_cod_map`. The frozen clean ``fleet``
    schema carries ``plant_id``, ``nameplate_capacity_mw`` and ``operating_year``
    but NOT the month-precise ``Operating Month`` / ``Planned Retirement
    Month``/``Year`` columns the raw reducer uses, so this is necessarily a
    **year-precise** COD map: each plant's online year is the capacity-weighted
    mean of its units' ``operating_year`` (rounded), its online month defaults to
    :data:`COD_FALLBACK_MONTH`, and it carries **no** planned retirement.
    Recovering month precision and plant retirements through the clean seam would
    require a fleet-schema contract change — raise one rather than editing the
    frozen YAML. The master-registry ``year_built`` back-fill is applied exactly
    as on the raw path (the registry is a raw reference file, not part of the
    clean contract).

    Raises ``FileNotFoundError`` (with a regenerate hint) when the clean fleet
    partition is absent — regenerate it with
    ``python scripts/regenerate_clean.py fleet``.
    """
    from scripts.lib import clean_io

    cod: dict[int, CodEntry] = {}

    df = clean_io.read_clean(
        "fleet",
        year=partition_year,
        columns=["plant_id", "nameplate_capacity_mw", "operating_year"],
    )
    work = pd.DataFrame(
        {
            "pc": pd.to_numeric(df.get("plant_id"), errors="coerce"),
            "cap": pd.to_numeric(df.get("nameplate_capacity_mw"), errors="coerce"),
            "oy": pd.to_numeric(df.get("operating_year"), errors="coerce"),
        }
    ).dropna(subset=["pc", "oy"])

    if not work.empty:
        # Positive nameplate weights the COD; equal-weight a plant that reports
        # no capacity so it still gets a representative year.
        work["w"] = work["cap"].where(work["cap"] > 0.0, 0.0)
        for code, grp in work.groupby("pc"):
            code = int(code)
            weights = grp["w"].to_numpy()
            if weights.sum() <= 0.0:
                weights = np.ones(len(grp))
            online_year = int(
                round(float(np.average(grp["oy"].to_numpy(), weights=weights)))
            )
            # Month unknown in the clean schema -> mid-year default; no retirement.
            cod[code] = (online_year, COD_FALLBACK_MONTH, None, None)

    # Registry-only back-fill (year-only -> mid-year default), never overriding
    # a clean-fleet record — mirrors the raw reducer.
    reg = _registry_year_built()
    for code, year in zip(reg["plant_id"], reg["year_built"]):
        code = int(code)
        if code not in cod:
            cod[code] = (int(year), COD_FALLBACK_MONTH, None, None)

    return cod


@lru_cache(maxsize=4)
def _load_cod_map(eia860_dir) -> dict[int, CodEntry]:
    """Build the ``{plant_code: (online_year, online_month, ret_year, ret_month)}`` map.

    Reduced from the month-precise EIA-860 operable generator schedule:

    * the plant's online date is the **capacity-weighted** mean of its units'
      ``(Operating Year, Operating Month)`` — a representative COD that tracks
      where the bulk of the plant's nameplate actually came online, so a plant
      whose capacity is dominated by a recent build ramps in the solved year
      while one with a small recent addition to an old base does not. (A scalar
      per-plant COD necessarily approximates a genuinely mixed-vintage plant; the
      capacity weighting is the closest single date to the true per-unit
      online-capacity fraction — see docs/cod-vintage-ramp.md.)
    * a **retirement** date is recorded only when *every* unit of the plant
      carries a planned retirement (the whole plant goes away); the latest such
      date is used, so capacity is kept until the last unit retires. A partial
      retirement leaves the plant online (``None``).

    Plants present only in the curated master registry (``year_built``) — not in
    the EIA-860 operable schedule — are back-filled at :data:`COD_FALLBACK_MONTH`
    so an ERCOT plant the registry knows but EIA-860 omits still ramps by year.
    The result is cached (the underlying files are static within a process).
    """
    cod: dict[int, CodEntry] = {}

    # The operable schedule (raw EIA-860 headers) plus the active directory's
    # within-window retiree parquet (canonical schema) feed the same per-plant
    # reduction. The retiree file is absent from a year-matched native vintage
    # dir (which carries its exits in the operable file already), so the union
    # is a no-op there.
    frames = [
        _cod_work_frame(
            eia860_dir / "eia860_generator_operable.parquet",
            {
                "pc": "Plant Code",
                "oy": "Operating Year",
                "om": "Operating Month",
                "cap": "Nameplate Capacity (MW)",
                "ry": "Planned Retirement Year",
                "rm": "Planned Retirement Month",
            },
        ),
        _cod_work_frame(
            eia860_dir / _RETIRED_WINDOW_NAME,
            {
                "pc": "plant_id",
                "oy": "operating_year",
                "om": "operating_month",
                "cap": "nameplate_capacity_mw",
                "ry": "planned_retirement_year",
                "rm": "planned_retirement_month",
            },
        ),
    ]
    frames = [f for f in frames if f is not None]
    work = pd.concat(frames, ignore_index=True) if frames else None

    if work is not None and not work.empty:
        work["om"] = work["om"].fillna(COD_FALLBACK_MONTH).clip(1, 12)
        # Positive nameplate weights the COD; fall back to equal weight when a
        # plant reports no capacity so it still gets a representative date.
        work["w"] = work["cap"].where(work["cap"] > 0.0, 0.0)
        for code, grp in work.groupby("pc"):
            code = int(code)
            weights = grp["w"].to_numpy()
            if weights.sum() <= 0.0:
                weights = np.ones(len(grp))
            # Continuous COD (year + (month-1)/12), capacity-weighted, then split
            # back into an integer (year, month).
            cont = grp["oy"].to_numpy() + (grp["om"].to_numpy() - 1.0) / 12.0
            mean = float(np.average(cont, weights=weights))
            online_year = int(np.floor(mean))
            online_month = int(round((mean - online_year) * 12.0)) + 1
            online_month = min(max(online_month, 1), 12)
            # Retire the plant only when every unit has a planned retirement.
            ret_year = ret_month = None
            ret = grp.dropna(subset=["ry"])
            if len(ret) == len(grp) and len(ret) > 0:
                last = ret.sort_values(["ry", "rm"]).iloc[-1]
                ret_year = int(last["ry"])
                ret_month = int(last["rm"]) if pd.notna(last["rm"]) else 12
            cod[code] = (online_year, online_month, ret_year, ret_month)

    # Registry-only back-fill (year-only -> mid-year default), never overriding
    # the month-precise EIA-860 record.
    reg = _registry_year_built()
    for code, year in zip(reg["plant_id"], reg["year_built"]):
        code = int(code)
        if code not in cod:
            cod[code] = (int(year), COD_FALLBACK_MONTH, None, None)

    return cod


def monthly_online_mask(
    online_year: int | None,
    online_month: int,
    retirement_year: int | None,
    retirement_month: int | None,
    run_year: int,
) -> np.ndarray:
    """Return the ``(12,)`` boolean online mask for one unit in ``run_year``.

    Element ``m`` (0-based month) is ``True`` when the unit is commissioned and
    not yet retired in calendar month ``m + 1``:

    * ``online_year > run_year`` → not yet built (all ``False``);
    * ``online_year == run_year`` → online from ``online_month`` on;
    * ``retirement_year < run_year`` → already gone (all ``False``);
    * ``retirement_year == run_year`` → online through ``retirement_month``.

    ``online_year`` of ``None`` (vintage unknown) keeps the unit fully online.
    """
    months = np.arange(1, 13)
    on = np.ones(12, dtype=bool)
    if online_year is not None:
        if online_year > run_year:
            on[:] = False
        elif online_year == run_year:
            on &= months >= online_month
    if retirement_year is not None:
        if retirement_year < run_year:
            on[:] = False
        elif retirement_year == run_year:
            on &= months <= (retirement_month if retirement_month is not None else 12)
    return on


def class_cod_coverage(
    class_labels: "list[str]",
    online_years: "list[int | None]",
) -> dict[str, tuple[int, int]]:
    """Tabulate per-class COD-date coverage for a fleet.

    ``class_labels[i]`` is generator ``i``'s resource class (its ``plant_group``,
    or fuel type when the group is blank) and ``online_years[i]`` is the
    ``online_year`` :func:`effective_cod` resolved for it (``None`` = vintage
    unknown → the unit is held fully online with no ramp). Returns
    ``{class_label: (n_units, n_with_cod)}``.

    The audit guardrail: a resource class whose units all resolve to a known
    EIA-860 COD is month-precision ramped; a class with ``n_with_cod == 0`` is
    silently skipping the vintage ramp (a future fleet vintage that drops a
    class's build dates, or a new fuel that never reaches the COD map, shows up
    here as 0-of-N covered). See :func:`log_class_cod_coverage`.
    """
    cov: dict[str, list[int]] = {}
    for label, oy in zip(class_labels, online_years):
        rec = cov.setdefault(str(label or "unknown"), [0, 0])
        rec[0] += 1
        if oy is not None:
            rec[1] += 1
    return {k: (v[0], v[1]) for k, v in cov.items()}


def log_class_cod_coverage(
    coverage: dict[str, tuple[int, int]], iso: str, run_year: int
) -> list[str]:
    """Log per-class COD coverage and WARN on any class with no COD dates.

    Emits one DEBUG line per class and a single WARNING naming every class that
    resolved **zero** EIA-860 COD dates across all its units — the signal that a
    resource class is silently bypassing the month-precise vintage ramp. Returns
    the list of fully-uncovered class labels (empty when every class is covered),
    so callers/tests can assert on it.
    """
    uncovered: list[str] = []
    for label in sorted(coverage):
        n, n_cod = coverage[label]
        logger.debug(
            "COD coverage (%s %s): %s %d/%d units have an EIA-860 COD",
            iso,
            run_year,
            label,
            n_cod,
            n,
        )
        if n > 0 and n_cod == 0:
            uncovered.append(label)
    if uncovered:
        logger.warning(
            "COD ramp (%s %s): %d resource class(es) have NO EIA-860 COD date "
            "and skip the vintage ramp entirely: %s — a fleet vintage may have "
            "dropped this class's build dates (check load_cod_map / "
            "_map_fuel_type coverage)",
            iso,
            run_year,
            len(uncovered),
            ", ".join(uncovered),
        )
    return uncovered


def effective_cod(
    plant_code: int,
    online_year: int,
    online_month: int,
    retirement_year: int | None,
    retirement_month: int | None,
    cod_map: dict[int, CodEntry],
) -> CodEntry:
    """Resolve a generator's COD, preferring the EIA-860 plant-code map.

    A generator pinned to a physical plant (``plant_code > 0``) present in
    ``cod_map`` takes the month-precise EIA-860 record — this is what gives the
    ERCOT CAMPD bins (which carry no build date) their COD. Otherwise the
    generator's own ``online_year`` / ``online_month`` apply, with the model's
    ``2000`` sentinel treated as "vintage unknown" so a real pre-existing unit
    is never dropped.

    The plant map supplies the **online** date, but its retirement is a
    plant-level reduction: ``_load_cod_map`` collapses a plant's heterogeneous
    unit retirements to the **latest** one, which keeps a winding-down plant
    fully online past the months its earlier units actually left (e.g. Homer
    City, plant 3122 — its three coal units retired 2023-07 / 2023-08 / 2024-04,
    yet the collapse held all 2012 MW online through 2024-04, ~2 GW of phantom
    H2-2023 capacity the cost-based LP then dispatched as baseload). So when the
    generator carries its **own** per-unit retirement, prefer it over the
    plant-collapsed date — each within-window retiree unit ages out on its true
    EIA-860 retirement month. The ERCOT CAMPD bins carry no retirement, so they
    keep the plant-map record unchanged.
    """
    entry = cod_map.get(int(plant_code)) if plant_code else None
    if entry is not None:
        if retirement_year is not None:
            entry_oy, entry_om, _, _ = entry
            return (entry_oy, entry_om, retirement_year, retirement_month)
        return entry
    oy = online_year if online_year > _ONLINE_YEAR_SENTINEL else None
    return (oy, online_month, retirement_year, retirement_month)
