"""Read the curated ``nuclear-license-status`` registry into unit-status objects.

The **read-only consumption stub** for each ISO's nuclear fleet forward-lifetime
registry, curated by the intake pipeline
(``scripts/lib/nuclear_license_status`` → ``data/clean/nuclear-license-status``).

:func:`load_nuclear_license_status` returns one :class:`NuclearUnitStatus` per
operating (or restart-pathway) power reactor unit in an ISO — its current NRC
license expiry and stage, SLR status, any announced uprate, restart pathway, and
confirmed-retirement cross-reference.

**Nothing in the solve path consumes this yet.** FF-G5 shipped the registry as a
grounded DATA input plus a design memo for the forward channel
(``docs/handoffs/ff-g5-nuclear-registry-2026-07.md``); wiring a mechanism that
consumes these objects (folding no-SLR-pathway license expiries into the
confirmed-exit channel, restarts into the planned-additions channel, uprates as a
capacity uprate) is a separately-chartered implementing session. This stub exists
so those tests and that wiring have a stable seam to build against — it mirrors
``market_sim.data.confirmed_retirements.load_confirmed_exits`` deliberately.

The clean tree is derived/gitignored, so a missing partition (an ISO whose
registry has not landed) yields an empty list with a log line rather than an
error. Forecast-forward only by construction: an NRC license is an enforceable
public instrument with a date that regenerates at each intake vintage (rule 13).
"""

from __future__ import annotations

import datetime as _dt  # noqa: F401 -- referenced only in string annotations
import logging

import pandas as pd
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DATATYPE = "nuclear-license-status"


class NuclearUnitStatus(BaseModel):
    """One nuclear unit's forward-lifetime status — the registry row as an object.

    Attributes
    ----------
    plant_id:
        EIA plant code (joins the fleet spine's ``plant_code``).
    unit:
        EIA-860 generator ID within the plant (also the NRC unit number).
    plant_name:
        EIA-860 plant name (human-readable).
    capacity_mw:
        Nameplate MW (spine-validated), or ``None`` when the registry left it
        blank.
    current_license_expiry:
        Current NRC operating-license expiration date (reflects any renewal / SLR
        already granted), or ``None``. The FEDERAL license ceiling — a state
        ceiling (e.g. Diablo Canyon SB 846) lives in the confirmed-retirements
        registry, referenced via ``confirmed_retirement_ref``.
    license_stage:
        ``original`` | ``renewed_60`` | ``slr_granted_80``.
    slr_status:
        ``granted`` | ``under_review`` | ``announced_intent`` | ``none``.
    announced_uprate_mw:
        Announced (not-yet-in-nameplate) uprate MW, or ``None``.
    restart_status:
        ``returned`` | ``in_progress`` | ``planned`` | ``none``/``None`` for a
        normally-operating unit.
    restart_target_year:
        Target return-to-service year for a restart-pathway unit, or ``None``.
    confirmed_retirement_ref:
        ``instrument_id`` of the confirmed-retirements row governing this unit's
        binding exit, when one exists (e.g. ``sb846-diablo-1``); ``None``
        otherwise. The authoritative exit row lives in confirmed-retirements —
        this is a cross-reference only, never a duplicate.
    """

    plant_id: int
    unit: str
    plant_name: str | None = None
    capacity_mw: float | None = None
    current_license_expiry: "_dt.date | None" = None
    license_stage: str | None = None
    slr_status: str | None = None
    announced_uprate_mw: float | None = None
    restart_status: str | None = None
    restart_target_year: int | None = None
    confirmed_retirement_ref: str | None = None


def _clean_str(value: object) -> str | None:
    """Return a stripped string, or ``None`` for blank / NA cells."""
    if value is None or (isinstance(value, float) and value != value) or pd.isna(value):
        return None
    s = str(value).strip()
    return s or None


def load_nuclear_license_status(iso: str) -> list[NuclearUnitStatus]:
    """Return the nuclear fleet forward-lifetime rows for an ISO.

    Reads the clean ``nuclear-license-status`` partition and maps each row to a
    :class:`NuclearUnitStatus`. Returns ``[]`` (with a log line) when the
    partition is absent — the intake for that ISO has not landed — so a future
    caller degrades gracefully. **No solve-path caller exists yet** (FF-G5 is
    data + design only); this is the seam the implementing session will consume.

    Args:
        iso: Model ISO name (e.g. ``"PJM"``, ``"MISO"``). The registry is
            partitioned by this exact label.

    Returns:
        One :class:`NuclearUnitStatus` per unit, sorted by ``(plant_id, unit)``.
    """
    try:
        from scripts.lib.clean_io import read_clean
    except ModuleNotFoundError:
        logger.warning(
            "nuclear-license-status: scripts.lib.clean_io unavailable; no rows "
            "for %s (invoke with PYTHONPATH=. from the repo root).",
            iso,
        )
        return []
    try:
        df = read_clean(DATATYPE, iso=iso.upper())
    except FileNotFoundError:
        logger.info(
            "nuclear-license-status: clean partition for %s absent; returning [] "
            "(run scripts/data/curate_nuclear_license_status.py to regenerate).",
            iso,
        )
        return []

    if df.empty:
        return []

    units: list[NuclearUnitStatus] = []
    for row in df.itertuples(index=False):
        expiry = row.current_license_expiry
        expiry_date = pd.Timestamp(expiry).date() if pd.notna(expiry) else None
        mw = row.capacity_mw
        uprate = row.announced_uprate_mw
        target = row.restart_target_year
        units.append(
            NuclearUnitStatus(
                plant_id=int(row.eia_plant_id),
                unit=str(row.unit).strip(),
                plant_name=_clean_str(row.plant_name),
                capacity_mw=(float(mw) if pd.notna(mw) else None),
                current_license_expiry=expiry_date,
                license_stage=_clean_str(row.license_stage),
                slr_status=_clean_str(row.slr_status),
                announced_uprate_mw=(float(uprate) if pd.notna(uprate) else None),
                restart_status=_clean_str(row.restart_status),
                restart_target_year=(int(target) if pd.notna(target) else None),
                confirmed_retirement_ref=_clean_str(row.confirmed_retirement_ref),
            )
        )
    units.sort(key=lambda u: (u.plant_id, u.unit))
    logger.info("nuclear-license-status: loaded %d unit(s) for %s", len(units), iso)
    return units
