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
from functools import lru_cache

import numpy as np
import pandas as pd

from market_sim.config.paths import EIA_860_DIR, INPUTS_DIR

logger = logging.getLogger(__name__)

_REGISTRY = INPUTS_DIR / "master-plant-registry.csv"
# Month-precise generator-level EIA-860 operable schedule (Operating Month /
# Year, Planned Retirement Month / Year per generator). Preferred over the
# year-only processed thermal parquet because it carries the commissioning
# *month* the renewable/storage ramps already use.
_EIA860_OPERABLE = EIA_860_DIR / "eia860_generator_operable.parquet"

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


@lru_cache(maxsize=1)
def load_cod_map() -> dict[int, CodEntry]:
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

    if _EIA860_OPERABLE.exists():
        df = pd.read_parquet(_EIA860_OPERABLE)
        pc = pd.to_numeric(df.get("Plant Code"), errors="coerce")
        oy = pd.to_numeric(df.get("Operating Year"), errors="coerce")
        om = pd.to_numeric(df.get("Operating Month"), errors="coerce")
        cap = pd.to_numeric(df.get("Nameplate Capacity (MW)"), errors="coerce")
        ry = pd.to_numeric(df.get("Planned Retirement Year"), errors="coerce")
        rm = pd.to_numeric(df.get("Planned Retirement Month"), errors="coerce")
        work = pd.DataFrame(
            {"pc": pc, "oy": oy, "om": om, "cap": cap, "ry": ry, "rm": rm}
        ).dropna(subset=["pc", "oy"])
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
                ret_month = (
                    int(last["rm"]) if pd.notna(last["rm"]) else 12
                )
            cod[code] = (online_year, online_month, ret_year, ret_month)

    # Registry-only back-fill (year-only -> mid-year default), never overriding
    # the month-precise EIA-860 record.
    if _REGISTRY.exists():
        reg = pd.read_csv(_REGISTRY, usecols=["plantid", "year_built"])
        reg = reg.dropna(subset=["plantid", "year_built"])
        for code, year in zip(reg["plantid"], reg["year_built"]):
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
    """
    entry = cod_map.get(int(plant_code)) if plant_code else None
    if entry is not None:
        return entry
    oy = online_year if online_year > _ONLINE_YEAR_SENTINEL else None
    return (oy, online_month, retirement_year, retirement_month)
