"""Measured storage ancillary-service award series (clean ``storage-as-awards``).

Reader over the ``storage-as-awards`` clean datatype — the measured hourly MW
of ancillary services AWARDED to the storage fleet (CAISO: Daily Energy
Storage Report quarterly data; see
``data/raw/storage-as-awards/CAISO/README.md``). This is the measured input
for storage AS power-reservation mechanisms
(:func:`market_sim.model.storage.reserve_caiso_storage_as_power` /
``ScenarioConfig.caiso_storage_as_reservation``): capacity the market has
committed to reserves cannot simultaneously offer energy arbitrage.

Rule-13 admissibility: an AS award is a market-design quantity that
regenerates for a forward year from forward drivers (the AS requirement scales
with load/VRE and the storage fleet's share of it responds to fleet growth and
AS saturation — the endogenous-co-opt path prices exactly that trade-off
forward), and it responds to changed conditions. It is used here only as a
capability *input* (a power reservation the LP dispatches beneath), never as a
dispatch outcome pinned to actuals.

Alignment contract: the clean frames carry true-UTC interval starts; the model
frame is the BA-local (prevailing Pacific) calendar year, one row per physical
hour, Feb 29 dropped (``eia_loader._eia_hourly_frame`` semantics). The mapping
built here is the full UTC hour sequence of the local year minus the Feb-29
hours — exact under both DST transitions.
"""

from __future__ import annotations

import logging
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DATATYPE = "storage-as-awards"

#: Canonical upward AS products — reserve capacity that must be able to raise
#: net injection (discharge headroom). Regulation-down is the downward product.
UPWARD_PRODUCTS: tuple[str, ...] = ("reg_up", "spin", "nonspin")

#: BA-local clock per ISO for the model-frame alignment.
_ISO_TZ: dict[str, str] = {"CAISO": "America/Los_Angeles"}

#: Max missing hours filled by nearest-value before the loader hard-errors
#: (same bounded year-boundary tolerance as data.caiso_as_requirements).
_MAX_BOUNDARY_FILL_HOURS: int = 48


def _model_frame_utc_index(iso: str, year: int, hours: int) -> pd.DatetimeIndex:
    """UTC stamps of the model's local-calendar-year rows (Feb 29 dropped).

    Row k of the model frame is the k-th physical hour of the BA-local
    calendar year; a leap year's 24 Feb-29 hours are dropped to keep the
    fixed 8760 horizon (``eia_loader._eia_hourly_frame`` semantics).
    """
    tz = ZoneInfo(_ISO_TZ[iso])
    start = pd.Timestamp(year=year, month=1, day=1, tz=tz)
    end = pd.Timestamp(year=year + 1, month=1, day=1, tz=tz)
    rng = pd.date_range(start, end, freq="h", inclusive="left").tz_convert("UTC")
    local = rng.tz_convert(tz)
    rng = rng[~((local.month == 2) & (local.day == 29))]
    return rng[:hours]


def load_storage_as_awards(
    iso: str,
    year: int,
    hours: int,
    market: str = "DAM",
    resource_class: str = "battery",
) -> dict[str, np.ndarray]:
    """Load the measured hourly storage AS-award series on the model frame.

    Args:
        iso: ISO code (currently CAISO).
        year: Backcast year (train years 2023-2025 only, CLAUDE.md rule 22).
        hours: LP horizon length T; each series is aligned/trimmed to exactly
            this many model-frame hours.
        market: "DAM" (CAISO IFM — the award that holds through the operating
            day, default) or "RTM" (CAISO RTPD, hourly-averaged).
        resource_class: "battery" (default) or "hybrid".

    Returns:
        ``{product: (hours,) float MW}`` for every product present, on the
        reconciled taxonomy (``reg_up``/``reg_down``/``spin``/``nonspin``).

    Raises:
        FileNotFoundError: the clean partition is absent — the mechanism flag
            hard-errors rather than silently solving without the reservation
            it claims to apply (regenerate with
            ``python scripts/curate_storage_as_awards.py``).
        ValueError: a series has an interior coverage hole, or non-finite /
            negative award MW.
    """
    from scripts.lib.clean_io import read_clean

    df = read_clean(DATATYPE, iso=iso, year=year)
    df = df[(df["market"] == market) & (df["resource_class"] == resource_class)]
    if df.empty:
        raise ValueError(
            f"storage-as-awards {iso} {year}: no rows for market={market!r}, "
            f"resource_class={resource_class!r}."
        )

    frame_idx = _model_frame_utc_index(iso, year, hours)
    out: dict[str, np.ndarray] = {}
    for product, sub in df.groupby("product", sort=False):
        hourly = (
            sub.set_index("interval_start_utc")["award_mw"]
            .sort_index()
            .reindex(frame_idx)
        )
        n_missing = int(hourly.isna().sum())
        if n_missing > _MAX_BOUNDARY_FILL_HOURS:
            raise ValueError(
                f"storage-as-awards {iso} {year} {market}/{resource_class}/"
                f"{product}: {n_missing} model-frame hours uncovered "
                f"(> {_MAX_BOUNDARY_FILL_HOURS} tolerated)."
            )
        if n_missing:
            hourly = hourly.ffill().bfill()
        series = hourly.to_numpy(dtype=float)
        if not np.all(np.isfinite(series)) or np.any(series < 0):
            raise ValueError(
                f"storage-as-awards {iso} {year} {market}/{resource_class}/"
                f"{product}: non-finite or negative award MW."
            )
        out[str(product)] = series
    return out


def upward_award_mw(iso: str, year: int, hours: int, market: str = "DAM") -> np.ndarray:
    """Total battery upward-AS award MW (reg-up + spin + non-spin), (hours,).

    The power the battery fleet holds for upward reserve products and cannot
    simultaneously offer as energy discharge — the quantity
    ``reserve_caiso_storage_as_power`` subtracts from the dispatch power cap.
    """
    awards = load_storage_as_awards(iso, year, hours, market=market)
    total = np.zeros(hours, dtype=float)
    for product in UPWARD_PRODUCTS:
        if product in awards:
            total += awards[product]
    return total


def sustain_energy_mwh(
    iso: str, year: int, hours: int, market: str = "DAM"
) -> np.ndarray:
    """Tariff sustain energy for the battery's spin/non-spin awards, (hours,).

    CAISO AS certification requires contingency-reserve awards to be
    sustainable for 30 minutes from available state of charge
    (:data:`market_sim.config.reserve_config.CAISO_AS_SUSTAIN_DURATION_H`,
    CAISO Tariff §8.4 / App. K; ASSOC initiative; DMM battery special
    reports) — so an awarded battery must hold ``0.5 h × (spin + nonspin)``
    MWh it cannot arbitrage away. Regulation is an AGC product without the
    30-minute contingency sustain and is excluded.
    """
    from market_sim.config.reserve_config import CAISO_AS_SUSTAIN_DURATION_H

    awards = load_storage_as_awards(iso, year, hours, market=market)
    total = np.zeros(hours, dtype=float)
    for product in ("spin", "nonspin"):
        if product in awards:
            total += awards[product]
    return CAISO_AS_SUSTAIN_DURATION_H * total
