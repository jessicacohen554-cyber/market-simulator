"""Read the curated ``confirmed-retirements`` registry into confirmed exits.

The model's *consumption seam* for each ISO's binding-instrument retirement
registry, curated by the intake pipeline
(``scripts/lib/confirmed_retirements`` → ``data/clean/confirmed-retirements``).

:func:`load_confirmed_exits` returns one :class:`ConfirmedExit` per unit — the
**earliest non-superseded** instrument for that unit — as a plain pydantic
object carrying just what the mechanism needs (identity, exit date, MW).
:func:`model.capacity.apply_confirmed_exits` consumes them as **step 0** of the
forecast capacity evolution, force-retiring / derating each unit at its
instrument date regardless of economics (a consent decree does not care about
the reserve margin). Superseded rows (a counter-instrument — RMR, DOE 202(c),
statute amendment — suspends the exit) are dropped here, so the unit reverts to
the economic-retirement screen exactly as the audit trail intends.

The clean tree is derived/gitignored, so a missing partition (an ISO whose
registry has not landed, or ERCOT before its rows are seeded) yields an empty
list with a log line rather than an error — callers gate on
``ScenarioConfig.confirmed_exits_enabled`` and degrade to the economic screen.
Forecast-forward only: a backcast's historical exits are already carried by the
EIA-860 vintage snapshot + within-window retiree build (plan §5.4).
"""

from __future__ import annotations

import logging

import pandas as pd
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DATATYPE = "confirmed-retirements"


class ConfirmedExit(BaseModel):
    """One unit's binding, confirmed retirement — the injector's input.

    Attributes
    ----------
    plant_id:
        EIA plant code (joins the fleet spine's ``plant_code``).
    generator_id:
        EIA-860 generator ID within the plant (matches a unit-grain
        ``Generator.unit_id`` suffix; plant-binned fleets match on
        ``plant_id`` alone and derate).
    exit_year / exit_month:
        Calendar year (and optional month) the instrument requires the unit
        offline.
    mw:
        Nameplate MW of the exiting unit (from the registry's spine-validated
        ``capacity_mw``), used to derate a plant-binned generator; ``None`` when
        the registry left it blank.
    """

    plant_id: int
    generator_id: str
    exit_year: int
    exit_month: int | None = None
    mw: float | None = None


def load_confirmed_exits(iso: str) -> list[ConfirmedExit]:
    """Return the confirmed (binding-instrument) exits for an ISO.

    Reads the clean ``confirmed-retirements`` partition, drops ``superseded``
    rows, and collapses to the **earliest** non-superseded instrument per
    ``(plant_id, generator_id)`` unit. Returns ``[]`` (with a log line) when the
    partition is absent — the intake for that ISO has not landed — so the caller
    degrades to the economic-retirement screen with no confirmed channel.

    Args:
        iso: Model ISO name (e.g. ``"PJM"``, ``"ERCOT"``). The registry is
            partitioned by this exact label (NEISO is stored as ``"NEISO"``).

    Returns:
        One :class:`ConfirmedExit` per unit, sorted by ``(exit_year, plant_id,
        generator_id)``.
    """
    try:
        from scripts.lib.clean_io import read_clean
    except ModuleNotFoundError:
        logger.warning(
            "confirmed-retirements: scripts.lib.clean_io unavailable; "
            "no confirmed exits for %s",
            iso,
        )
        return []
    try:
        df = read_clean(DATATYPE, iso=iso.upper())
    except FileNotFoundError:
        logger.info(
            "confirmed-retirements: clean partition for %s absent; run "
            "scripts/curate_confirmed_retirements.py. No confirmed exits.",
            iso,
        )
        return []

    if df.empty:
        return []
    live = df[~df["superseded"].astype(bool)].copy()
    if live.empty:
        return []

    # Earliest non-superseded instrument per unit (a unit may carry an old
    # superseded row plus a live one; the live earliest exit is the ceiling).
    live["exit_year"] = pd.to_numeric(live["exit_year"], errors="coerce")
    live = live.dropna(subset=["exit_year"])
    live = live.sort_values("exit_year").drop_duplicates(
        subset=["plant_id", "generator_id"], keep="first"
    )

    exits: list[ConfirmedExit] = []
    for row in live.itertuples(index=False):
        exit_month = row.exit_month
        mw = row.capacity_mw
        exits.append(
            ConfirmedExit(
                plant_id=int(row.plant_id),
                generator_id=str(row.generator_id).strip(),
                exit_year=int(row.exit_year),
                exit_month=(int(exit_month) if pd.notna(exit_month) else None),
                mw=(float(mw) if pd.notna(mw) else None),
            )
        )
    exits.sort(key=lambda e: (e.exit_year, e.plant_id, e.generator_id))
    logger.info(
        "confirmed-retirements: loaded %d confirmed exit(s) for %s", len(exits), iso
    )
    return exits


def load_announced_reversal_plants(iso: str) -> frozenset[int]:
    """Return plant codes whose announced retirement was REVERSED outright.

    The retirement-reversal supersession channel (confirmed-retirement plan
    §2.2 counter-instruments; capacity-economics Stage 2): a plant whose every
    registry row is ``superseded`` — a counter-instrument (statute, RMR, DOE
    202(c), withdrawal) cancelled the exit and nothing re-confirmed it — must
    not have its stale EIA-860 announced date executed by
    :func:`market_sim.model.capacity.apply_announced_retirements`. The worked
    case is Byron/Dresden: the 2020-vintage EIA-860 carries their 2021 planned
    dates (Exelon's PJM deactivation requests), reversed by Illinois CEJA
    (P.A. 102-0662, 2021-09-15), so the non-fossil announced channel
    false-retires ~4.1 GW of nuclear in any run seeded from that vintage.

    A plant with **any live (non-superseded) row is excluded**: its exit was
    replaced by a different confirmed instrument (e.g. Diablo Canyon's SB 846
    schedule superseding the 2016 settlement), so its announced date still
    stands and the confirmed channel governs.

    Data-driven and independent of ``confirmed_exits_enabled`` — honoring a
    documented reversal is an announced-channel data correction, not an
    exogenous exit injection. Returns ``frozenset()`` when the clean partition
    is absent. Limitation (documented, not gated): reversal rows carry no
    superseding-instrument date column, so the suppression is not date-gated
    within a hindcast window — every seeded reversal predates the earliest
    evolution step that could consume it (CEJA 2021-09 vs the 2022 bridge).
    """
    try:
        from scripts.lib.clean_io import read_clean
    except ModuleNotFoundError:
        return frozenset()
    try:
        df = read_clean(DATATYPE, iso=iso.upper())
    except FileNotFoundError:
        return frozenset()
    if df.empty:
        return frozenset()
    superseded = df["superseded"].astype(bool)
    all_superseded = superseded.groupby(df["plant_id"]).all()
    plants = frozenset(int(p) for p, flag in all_superseded.items() if flag)
    if plants:
        logger.info(
            "confirmed-retirements: %d plant(s) with fully-superseded "
            "(reversed) retirements for %s: %s",
            len(plants),
            iso,
            sorted(plants),
        )
    return plants
