"""Declared capacity-emergency event windows — dispatch-time consumers.

Reads the curated ``maxgen-events`` registry (one row per declared
(ISO, level, region) window; ``data/dictionary/schema/maxgen-events.schema.yaml``,
curated by ``scripts.curate_maxgen_events``) for the mechanisms that key on a
DECLARED window at solve time. Today that is the ELMP emergency-tier pricing
channel (``ScenarioConfig.maxgen_emergency_tier_pricing``, the MISO F5
scarcity-depth lane): inside a registry window declared at Maximum Generation
Warning or higher, the energy-balance load-slack cost is repriced from the
ISO's bid cap to the declared tier's emergency offer floor —
``min(voll, tier_floor(level))`` — per the SOM-footnoted tier schedule
(:data:`market_sim.config.reserve_config.MISO_EMERGENCY_TIER1_OFFER_FLOOR` /
``..TIER2..``). Frozen design:
``docs/handoffs/miso-f5-scarcity-depth-design-2026-07.md`` §1.

Clock and scoping conventions are IDENTICAL to the M-2 revealed-derate
deriver (``scripts/derive_campd_maxgen_outages.py``), so the tier windows and
the derate windows are hour-exact aligned by construction: MISO market
operations run on EST (UTC-5) year-round (Tariff Module A; ``Etc/GMT+5``),
window starts floor / ends ceil to the hour (a declared ``23:59`` end-of-day
becomes the next midnight), hour masks go through
:func:`market_sim.data.outages.outage_hour_mask` (half-open, no-leap 8760
model clock), and declared regions crosswalk onto model zones as
``footprint`` -> all zones, ``midwest`` -> all but MISO-South, ``south`` ->
MISO-South.

Backcast/calibration only (legitimacy D-5 ``backcast_only``): a forecast year
carries no declared windows — the registry regenerates from each new
declaration vintage, and the post-9/30/2025 ER25-579 shortage-pricing regime
is the forecast lane's own charter (never half-built here).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from market_sim.config.reserve_config import (
    MISO_EMERGENCY_TIER1_OFFER_FLOOR,
    MISO_EMERGENCY_TIER2_OFFER_FLOOR,
)
from market_sim.data.outages import outage_hour_mask

logger = logging.getLogger(__name__)

# ISO market/registry clock (naive local standard time, the model clock).
# MISO market operations run on EST (UTC-5) year-round — Tariff Module A;
# Etc/GMT+5 is UTC-5. Mirrors derive_campd_maxgen_outages.MODEL_TZ.
MODEL_TZ_BY_ISO: dict[str, str] = {"MISO": "Etc/GMT+5"}

# Declared ladder level -> ELMP emergency-tier offer floor ($/MWh). The
# level vocabulary is the registry schema's closed set (pre-2026 MISO
# ladder). Advisory/Alert rungs carry NO pricing effect: the 2023 SOM
# p.10-11 ladder makes the Alert a price-FORMATION relaxation only ("allows
# 4-hour online resources to set price in ELMP") with no margin change —
# LP-native, since a pure LP has no commitment integralities. Warning and
# Event Step 1 price emergency supply at the Tier-1 floor (Step 1 commits
# emergency-only units / activates emergency ranges — more Tier-1 MW, no new
# pricing tier); Step 2..5 at the Tier-2 floor (Steps 3-5 add non-pricing
# actions; firm load shed itself stays at the ISO cap). Citations on the
# constants in config.reserve_config.
TIER_FLOOR_BY_LEVEL: dict[str, float | None] = {
    "capacity_advisory": None,
    "maxgen_alert": None,
    "maxgen_warning": MISO_EMERGENCY_TIER1_OFFER_FLOOR,
    "maxgen_event_step1": MISO_EMERGENCY_TIER1_OFFER_FLOOR,
    "maxgen_event_step2": MISO_EMERGENCY_TIER2_OFFER_FLOOR,
    "maxgen_event_step3": MISO_EMERGENCY_TIER2_OFFER_FLOOR,
    "maxgen_event_step4": MISO_EMERGENCY_TIER2_OFFER_FLOOR,
    "maxgen_event_step5": MISO_EMERGENCY_TIER2_OFFER_FLOOR,
}

# Model zones inside each declared region scope. MISO-South is LRZ 8-10;
# every other PHYSICAL model zone is the Midwest subregion. Unlike the M-2
# deriver's crosswalk (which only ever sees CAMPD unit zones), the LP's
# zone list also carries the external seam buses (MISO_external /
# MISO_external_South, appended by the interchange topology) — those are
# NOT MISO zones and are excluded from every declared region: load slack at
# an external bus is phantom import supply through the border links, so
# repricing it to a tier floor would fabricate unmeasured emergency imports
# and bypass the measured seam ladders (in a backcast the Tier-1 "call
# external capacity resources" leg is already inside the measured
# interchange). The declared instruments act on MISO's own footprint; the
# tier floor therefore reprices only the physical zones' slack.
_SOUTH_ZONES: frozenset[str] = frozenset({"MISO-South"})
_PHYSICAL_ZONES_BY_ISO: dict[str, frozenset[str]] = {
    "MISO": frozenset(
        {
            "MISO-West",
            "MISO-Plains",
            "MISO-Illinois",
            "MISO-Indiana",
            "MISO-East",
            "MISO-South",
        }
    ),
}


def _zone_in_region(zone: str, region: str, iso: str = "MISO") -> bool:
    """Return whether a PHYSICAL model zone is inside a declared region scope.

    External seam buses (any zone outside the ISO's physical zone set) are
    outside every region by construction — see the module comment above.
    """
    physical = _PHYSICAL_ZONES_BY_ISO.get((iso or "").upper())
    if physical is None:
        raise ValueError(f"physical zone set not registered for ISO {iso!r}")
    if zone not in physical:
        return False
    if region == "footprint":
        return True
    if region == "south":
        return zone in _SOUTH_ZONES
    if region == "midwest":
        return zone not in _SOUTH_ZONES
    raise ValueError(f"unknown declared region {region!r}")


def _import_clean_io():
    """Import the shared ``scripts.lib.clean_io`` reader seam, lazily.

    ``clean_io`` lives under ``scripts/`` (not an installed package), so the
    repo root goes on ``sys.path`` first — the ``data.campd`` pattern.
    """
    import sys

    from market_sim.config import paths

    root = str(paths.REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    from scripts.lib import clean_io  # noqa: E402

    return clean_io


def load_maxgen_registry_model_clock(iso: str) -> pd.DataFrame:
    """Return the ISO's maxgen-events registry on the naive model clock.

    Reads the curated ``maxgen-events`` partition through the frozen
    ``clean_io`` seam, regenerating it from ``data/raw`` when absent
    (``data/clean`` is derived and disposable — the deriver's convention).
    Adds ``start_model`` (hour-floored) and ``end_model_excl`` (hour-ceiled,
    half-open exclusive end: a declared ``23:59`` end-of-day becomes the next
    midnight) naive local-standard-time columns.
    """
    iso = (iso or "").upper()
    tz = MODEL_TZ_BY_ISO.get(iso)
    if tz is None:
        raise ValueError(
            f"maxgen-events model clock not registered for ISO {iso!r} "
            f"(known: {sorted(MODEL_TZ_BY_ISO)})"
        )
    clean_io = _import_clean_io()
    if not clean_io.clean_exists("maxgen-events", iso=iso):
        from scripts.curate_maxgen_events import curate

        curate(isos=[iso])
    ev = clean_io.read_clean("maxgen-events", iso=iso)
    start = ev["start_utc"].dt.tz_convert(tz).dt.tz_localize(None)
    end = ev["end_utc"].dt.tz_convert(tz).dt.tz_localize(None)
    ev = ev.copy()
    ev["start_model"] = start.dt.floor("h")
    ev["end_model_excl"] = end.dt.ceil("h")
    return ev


def emergency_tier_slack_cost(
    iso: str,
    year: int,
    zone_names: list[str],
    voll: float,
    hours: int,
) -> np.ndarray | None:
    """Return the ``(n_zones, T)`` declared-window tier-repriced slack cost.

    Initialized at ``voll`` everywhere; inside each registry window declared
    at Maximum Generation Warning or higher, the declared region's zones take
    ``min(voll, tier_floor(level))`` for the window's model-clock hours
    (:data:`TIER_FLOOR_BY_LEVEL`). ``min`` never RAISES the slack cost, and
    overlapping Warning+ rows on the same zone-hour take the minimum active
    floor (the cheapest active emergency tier is the marginal one — no such
    overlap exists in the current registry; deterministic tie rule).

    Returns ``None`` when no Warning+ row overlaps ``year`` — the caller then
    omits the ``slack_cost`` LP kwarg outright, keeping the flat-``voll``
    cost vector byte-identical (advisory/alert-only years included).
    """
    ev = load_maxgen_registry_model_clock(iso)
    return tier_slack_cost_from_registry(ev, iso, year, zone_names, voll, hours)


def tier_slack_cost_from_registry(
    ev: pd.DataFrame,
    iso: str,
    year: int,
    zone_names: list[str],
    voll: float,
    hours: int,
) -> np.ndarray | None:
    """Pure core of :func:`emergency_tier_slack_cost` on a loaded registry.

    ``ev`` carries the model-clock columns
    (:func:`load_maxgen_registry_model_clock`); separated from the I/O so the
    level/region/window/min semantics are unit-testable on synthetic frames.
    """
    n_zones = len(zone_names)
    cost = np.full((n_zones, int(hours)), float(voll), dtype=float)
    any_window = False
    for r in ev.itertuples(index=False):
        level = str(r.level)
        if level not in TIER_FLOOR_BY_LEVEL:
            raise ValueError(
                f"maxgen-events level {level!r} not in the tier schedule "
                f"(known: {sorted(TIER_FLOOR_BY_LEVEL)})"
            )
        floor = TIER_FLOOR_BY_LEVEL[level]
        if floor is None:
            continue  # advisory/alert: no pricing effect (2023 SOM p.10-11)
        mask = outage_hour_mask(r.start_model, r.end_model_excl, year, hours)
        if not mask.any():
            continue
        z_idx = [
            i
            for i, z in enumerate(zone_names)
            if _zone_in_region(z, str(r.region), iso)
        ]
        if not z_idx:
            continue
        any_window = True
        clamped = min(float(voll), float(floor))
        block = cost[np.ix_(z_idx, np.flatnonzero(mask))]
        cost[np.ix_(z_idx, np.flatnonzero(mask))] = np.minimum(block, clamped)
        logger.info(
            "maxgen tier pricing (%s %d): %s %s %s -> %s, %d hours x %d zones "
            "at $%.0f slack floor",
            iso,
            year,
            level,
            r.region,
            r.start_model,
            r.end_model_excl,
            int(mask.sum()),
            len(z_idx),
            clamped,
        )
    if not any_window:
        return None
    return cost
