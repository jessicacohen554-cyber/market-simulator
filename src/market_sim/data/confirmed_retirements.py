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
**Exception (W2-E / G12):** when the caller passes ``required=True`` — the
runner does so whenever ``confirmed_exits_enabled`` is on in forecast mode — a
missing or unimportable registry RAISES instead of silently degrading: the
W1-B smoke showed the warn-only no-op handing ERCOT 477 MW of phantom 2026
fleet (V H Braunig backlog) on a fresh checkout. Remediation:
``PYTHONPATH=. python scripts/curate_confirmed_retirements.py``.
Forecast-forward only: a backcast's historical exits are already carried by the
EIA-860 vintage snapshot + within-window retiree build (plan §5.4).
"""

from __future__ import annotations

import datetime as _dt  # noqa: F401 -- referenced only in string annotations
import logging

import pandas as pd
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DATATYPE = "confirmed-retirements"

# W2-E / G12 fail-loud remediation, quoted verbatim in every required-mode
# raise below. data/clean is derived and gitignored, so a fresh checkout has
# no registry until it is regenerated; and cache_key hashes config only,
# never data-file state, so caches solved before the regeneration must go.
_REMEDIATION = (
    "run `PYTHONPATH=. python scripts/curate_confirmed_retirements.py` from "
    "the repo root to regenerate data/clean/confirmed-retirements, then "
    "delete any results/<ISO>/<key>/ caches solved before it existed "
    "(cache_key hashes config only, never data-file state)"
)


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


def load_confirmed_exits(
    iso: str, as_of: "_dt.date | None" = None, required: bool = False
) -> list[ConfirmedExit]:
    """Return the confirmed (binding-instrument) exits for an ISO.

    Reads the clean ``confirmed-retirements`` partition, drops ``superseded``
    rows, and collapses to the **earliest** non-superseded instrument per
    ``(plant_id, generator_id)`` unit. Returns ``[]`` (with a log line) when the
    partition is absent — the intake for that ISO has not landed — so the caller
    degrades to the economic-retirement screen with no confirmed channel.

    Args:
        iso: Model ISO name (e.g. ``"PJM"``, ``"ERCOT"``). The registry is
            partitioned by this exact label (NEISO is stored as ``"NEISO"``).
        as_of: RC-1B hindcast information gate. When given, only instruments
            with ``instrument_date <= as_of`` are knowable — a row dated after
            ``as_of`` (e.g. ERCOT's Braunig 1/2 NSO, instrument_date
            2024-03-13) is dropped entirely, so an as-of-2020 hindcast cannot
            leak a post-2020 confirmed exit into its 2021-2025 forecast.
            ``None`` (default, the forecast-mode path) applies no cutoff —
            byte-identical to the pre-RC-1B behavior. A row with a null
            ``instrument_date`` is treated as unknown-dated and is DROPPED
            when ``as_of`` is given (never assumed knowable) rather than
            silently kept.
        required: W2-E / G12 fail-loud switch. When True — the runner passes
            it whenever ``confirmed_exits_enabled`` is on in forecast mode —
            a missing clean partition or an unimportable
            ``scripts.lib.clean_io`` seam raises :class:`RuntimeError` with
            the regeneration command instead of degrading to a warn-only
            empty list (the W1-B B3/B4 silent-477-MW failure). Default False
            preserves the degrade-to-economic-screen behavior for optional
            callers.

    Returns:
        One :class:`ConfirmedExit` per unit, sorted by ``(exit_year, plant_id,
        generator_id)``.
    """
    try:
        from scripts.lib.clean_io import read_clean
    except ModuleNotFoundError as exc:
        if required:
            raise RuntimeError(
                f"confirmed-retirements: scripts.lib.clean_io is unimportable "
                f"(repo root not on sys.path? — invoke with PYTHONPATH=. from "
                f"the repo root) while confirmed_exits_enabled is on in "
                f"forecast mode. Refusing to run with a silently degraded "
                f"confirmed-exit channel for {iso} (W1-B B4: ERCOT gains "
                f"477 MW of phantom fleet); {_REMEDIATION}."
            ) from exc
        logger.warning(
            "confirmed-retirements: HINDCAST INFORMATION-GATE WARNING — "
            "scripts.lib.clean_io unavailable; no confirmed exits for %s. "
            "If this ISO's registry should be present, this run is silently "
            "missing its confirmed-exit channel entirely (RC-1B D4).",
            iso,
        )
        return []
    try:
        df = read_clean(DATATYPE, iso=iso.upper())
    except FileNotFoundError as exc:
        if required:
            raise RuntimeError(
                f"confirmed-retirements: clean partition for {iso} is absent "
                f"while confirmed_exits_enabled is on in forecast mode. "
                f"data/clean is derived and gitignored, so a fresh checkout "
                f"has no registry; refusing to silently degrade to the "
                f"economic screen (W1-B B3: ERCOT's 2026 fleet gains 477 MW "
                f"— V H Braunig backlog); {_REMEDIATION}."
            ) from exc
        logger.warning(
            "confirmed-retirements: HINDCAST INFORMATION-GATE WARNING — clean "
            "partition for %s absent; run scripts/curate_confirmed_retirements.py "
            "(and scripts/regenerate_clean.py) before trusting any hindcast A/B "
            "leg that expects this ISO's confirmed-exit/reversal channel — a "
            "missing partition silently degrades to the economic screen and "
            "must never be mistaken for information discipline (RC-1B D4). "
            "No confirmed exits for %s this call.",
            iso,
            iso,
        )
        return []

    if df.empty:
        return []
    live = df[~df["superseded"].astype(bool)].copy()
    if live.empty:
        return []
    if as_of is not None:
        instrument_date = pd.to_datetime(live["instrument_date"], errors="coerce")
        cutoff = pd.Timestamp(as_of)
        live = live[instrument_date.notna() & (instrument_date <= cutoff)]
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


def load_announced_reversal_plants(
    iso: str, as_of: "_dt.date | None" = None, required: bool = False
) -> frozenset[int]:
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
    is absent.

    Args:
        iso: Model ISO name.
        as_of: RC-1B hindcast information gate. A reversal is only knowable
            once its OWN counter-instrument existed — gated on
            ``superseding_instrument_date`` (distinct from ``instrument_date``,
            the original — now-cancelled — instrument's date), not the
            original instrument's date. A plant whose ``superseding_
            instrument_date`` is null or postdates ``as_of`` is excluded from
            the returned set (its reversal was not yet knowable, so the
            original announced date should still fire) — the worked case:
            Byron/Dresden's original instrument_date is 2020-08-27 but the
            CEJA reversal's superseding_instrument_date is 2021-09-15, so an
            as-of-2020 hindcast (``as_of=date(2020, 12, 31)``) must NOT
            suppress their announced exit. ``None`` (default) applies no
            cutoff — byte-identical to the pre-RC-1B behavior (every fully-
            superseded plant is suppressed regardless of when its reversal
            became known).
        required: W2-E / G12 fail-loud switch (same clean partition as
            :func:`load_confirmed_exits`). The runner passes it whenever
            ``confirmed_exits_enabled`` is on in forecast mode; a missing or
            unimportable registry then raises :class:`RuntimeError` instead
            of silently skipping reversal suppression. Default False keeps
            the warn-only degradation — the reversal channel is a data
            correction, deliberately usable without the confirmed channel.
    """
    try:
        from scripts.lib.clean_io import read_clean
    except ModuleNotFoundError as exc:
        if required:
            raise RuntimeError(
                f"confirmed-retirements: scripts.lib.clean_io is unimportable "
                f"(repo root not on sys.path? — invoke with PYTHONPATH=. from "
                f"the repo root) while confirmed_exits_enabled is on in "
                f"forecast mode; refusing to silently skip announced-reversal "
                f"suppression for {iso} (W1-B B4); {_REMEDIATION}."
            ) from exc
        logger.warning(
            "confirmed-retirements: HINDCAST INFORMATION-GATE WARNING — "
            "scripts.lib.clean_io unavailable; no reversal suppression for %s.",
            iso,
        )
        return frozenset()
    try:
        df = read_clean(DATATYPE, iso=iso.upper())
    except FileNotFoundError as exc:
        if required:
            raise RuntimeError(
                f"confirmed-retirements: clean partition for {iso} is absent "
                f"while confirmed_exits_enabled is on in forecast mode; "
                f"refusing to silently skip announced-reversal suppression "
                f"(W1-B B3); {_REMEDIATION}."
            ) from exc
        logger.warning(
            "confirmed-retirements: HINDCAST INFORMATION-GATE WARNING — clean "
            "partition for %s absent; no reversal suppression applied. A "
            "missing partition must never be mistaken for information "
            "discipline (RC-1B D4) — run scripts/curate_confirmed_retirements.py "
            "+ scripts/regenerate_clean.py first.",
            iso,
        )
        return frozenset()
    if df.empty:
        return frozenset()
    superseded = df["superseded"].astype(bool)
    all_superseded = superseded.groupby(df["plant_id"]).all()
    plants = frozenset(int(p) for p, flag in all_superseded.items() if flag)
    if as_of is not None and plants:
        cutoff = pd.Timestamp(as_of)
        superseding_date = pd.to_datetime(
            df["superseding_instrument_date"], errors="coerce"
        )
        # A plant's reversal is knowable-as-of `as_of` only if EVERY one of its
        # superseded rows already carries a superseding_instrument_date <=
        # cutoff (a plant with any row whose reversal postdates the cutoff, or
        # is undated, was not yet known to be reversed).
        known_by_cutoff = superseding_date.notna() & (superseding_date <= cutoff)
        known_by_cutoff = known_by_cutoff.groupby(df["plant_id"]).all()
        plants = frozenset(p for p in plants if known_by_cutoff.get(p, False))
    if plants:
        logger.info(
            "confirmed-retirements: %d plant(s) with fully-superseded "
            "(reversed) retirements for %s: %s",
            len(plants),
            iso,
            sorted(plants),
        )
    return plants
