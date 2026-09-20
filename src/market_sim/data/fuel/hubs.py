"""Measured gas trading-hub series: monthly/daily hub prices and overlays.

The Henry Hub / Transco Z6 NY / Algonquin / Iroquois Z2 / CA-composite /
Chicago citygate raw+clean loaders, the trade-date and flow-date staircases,
the within-month daily shape factors, the hub-month reconstruction
(:func:`iso_hub_monthly_gas_prices` / :func:`iso_hub_daily_gas_prices`), and
the hub-basis overlay that reprices gas units at the constrained-hub spot.
Split out of ``data/fuel.py`` (W-D3; refactor-consolidation plan §5 item 3) as
pure code motion; the historically monkeypatched loader names are resolved
through the package namespace at call time (:func:`._shared._pkg_ns`), and the
NYISO reconciled-reference call is routed the same way — which also keeps this
module free of a module-level import of :mod:`.basis.nyiso` (no import cycle).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import CAISO_CITYGATE_TRANSPORT_ADDER
from market_sim.config.paths import GAS_PRICES_DIR, RAW_DATA_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays

from ._shared import (
    _DAYS_IN_MONTH,
    _FUEL_BASIS_DATATYPE,
    _FUEL_HUB_MONTHLY_DATATYPE,
    _FUEL_PRICES_DATATYPE,
    _GAS_FUEL_IDX,
    _HENRY_HUB_CLEAN_KEY,
    _expand_monthly_to_hourly,
    _month_index,
    _pkg_ns,
    _use_clean_data,
    logger,
)


# Regional gas-basis upload (doc-07/doc-08 U4 / doc-01 §4): per-ISO monthly
# delivered hub basis ($/MMBtu over Henry Hub) for the named pipeline trading
# points that EIA-923's plant-average delivered cost understates — Transco Z6
# NY / Iroquois for NYISO, Algonquin (AGT) for ISO-NE. The NEISO/Algonquin leg
# is filled (ISO-NE MA gas index, 2023-2025, 35/36 months); other ISOs remain
# header-only until a licensed ICE/Platts or EIA-citygate-proxy fill lands;
# see docs/multi-iso/data-acquisition-report.md §1.
WINTER_GAS_BASIS_PATH: Path = RAW_DATA_DIR / "gas_basis_by_iso_month.csv"


# Measured Henry Hub monthly spot averages (EIA RNGWHHDm via the
# datasets/natural-gas public-domain mirror; see
# docs/multi-iso/data-acquisition-report.md Step 1a). The hub-basis overlay
# adds the measured ISO-month basis back onto this leg.
HENRY_HUB_MONTHLY_PATH: Path = GAS_PRICES_DIR / "henry_hub_monthly.csv"

# Measured Henry Hub *daily* spot (EIA RNGWHHD, same public-domain mirror as
# the monthly leg). Used only for its within-month *shape*: the gas series
# already carries the correct monthly delivered level (F923 / hub-basis
# overlay), and the daily leg injects the intra-month commodity swing the
# merit order would actually see day to day — cheap shoulder days and
# cold-snap spikes — without moving the monthly mean (the factors are
# normalized to each month's own daily mean, so they average to 1.0).
HENRY_HUB_DAILY_PATH: Path = GAS_PRICES_DIR / "henry_hub_daily.csv"

# Measured Transco Zone 6 NY *daily* spot (EIA Natural Gas Weekly Update archive
# "New York" row, scraped by scripts/data/fetch_transco_daily_spot.py). The NYISO
# analogue of HENRY_HUB_DAILY_PATH: used only for its within-month *shape* so the
# daily hub-basis overlay (:func:`iso_hub_daily_gas_prices`) resolves the real
# cold-day spike that a monthly mean smears flat, without moving the monthly hub
# level (the factors normalize to each month's own daily mean). Iroquois Z2 — the
# NYISO reference zone — is not on EIA's free table, so the Iroquois-priced zones
# inherit this Transco daily shape (a real daily Iroquois series is the open ask).
TRANSCO_Z6_NY_DAILY_PATH: Path = GAS_PRICES_DIR / "transco_z6_ny_daily.csv"

# Measured Algonquin Citygate (AGT) *daily* spot, harvested free from the prose of
# every EIA Natural Gas Weekly Update ("...the price went up $9.31 from $4.04/MMBtu
# last Wednesday to $13.35/MMBtu yesterday...") by scripts/data/fetch_algonquin_daily_spot.py.
# These are real, EIA-published AGT spot prints — two hard-dated Wednesdays per
# weekly page plus winter high/low days, ~123 prints 2023-2025, densest in the cold
# weeks that set the ISO-NE price tail. The NEISO leg of the daily hub-basis overlay
# (:func:`iso_hub_daily_gas_prices`) anchors its within-month AGT basis to these real
# prints and mean-preserves to the measured monthly basis, replacing the retired
# demand-convexity proxy. AGT basis ~= Transco Z6 NY basis (measured slope ~0.95,
# corr ~0.79), so TRANSCO_Z6_NY_DAILY_PATH supplies the within-month shape in the
# sparse (<2 print) covered months; both are EIA Weekly archive series.
ALGONQUIN_DAILY_PATH: Path = GAS_PRICES_DIR / "algonquin_citygate_daily.csv"

# Measured Iroquois Zone 2 *daily* spot prints, to be harvested from the prose of
# the EIA Natural Gas Weekly Update archive by a planned Iroquois daily-spot
# fetcher (not yet landed; analogue of ALGONQUIN_DAILY_PATH — EIA's compact spot
# table has no Iroquois row, but the narrative quotes the hub in the cold weeks
# that set
# the eastern-NY winter price). Iroquois Z2 is the measured hub of the NYISO
# reference zone (Capital_Hudson) and the Lower_Hudson / Long_Island zones; the
# committed monthly reconstruction (Transco Z6 NY monthly + the SOM *annual*
# Iroquois-Transco spread) demonstrably under-reads constrained winter months
# (e.g. Dec-2024 reconstruction $3.16/MMBtu vs the New England complex the Z2
# segment physically trades in at ~$9), so where these real prints exist they
# locally supersede the reconstruction (rule #13: measured over estimate).
IROQUOIS_Z2_DAILY_PATH: Path = GAS_PRICES_DIR / "iroquois_z2_daily.csv"

# Measured California Composite Average citygate (PG&E Citygate / SoCal
# Citygate / SoCal Border blend, NGI Daily GPI) *daily* spot, scraped from the
# same EIA Natural Gas Weekly Update archive compact "Spot Prices" table the
# Transco daily series reads (scripts/data/fetch_caiso_citygate_daily.py), true-date
# keyed like TRANSCO_Z6_NY_DAILY_PATH's dated view (dense trading-day quotes,
# not sparse narrative prints). The CAISO leg of the daily hub-basis overlay
# (:func:`iso_hub_daily_gas_prices`) uses these real prints for the within-month
# *shape* only, mean-preserving on the measured monthly SoCal/PG&E citygate
# basis (``gas_basis_by_iso_month.csv``) — the flat monthly plateau (e.g. the
# Jan-2023 arctic-event month, monthly mean ~HH+$24) replaced by the real
# cold-day spike and its decay (e.g. the measured $24.29/MMBtu 2023-01-12 print
# followed by a collapse to ~$8-11 the last week of the month), instead of
# pricing every January hour at the monthly extreme.
CAISO_CITYGATE_DAILY_PATH: Path = GAS_PRICES_DIR / "caiso_citygate_daily.csv"

# Measured Chicago Citygate daily delivered-gas spot (EIA NG Weekly Update
# compact "Spot Prices" table, the "Chicago" row — NGI Daily GPI; scraped by
# scripts/data/fetch_miso_citygate_daily.py). The MISO analogue of the CAISO/NYISO
# daily hub series: the North/Central marginal winter gas unit prices off Chicago
# Citygate, whose spot blows out far above Henry Hub on the coldest days (Winter
# Storm Heather Friday 2024-01-12 = $25.82/MMBtu). Consumed by the winter
# fuel-security shape overlay (:func:`apply_miso_winter_citygate_daily`) for the
# within-month daily *shape* only, mean-preserving and flow-date-placed (Friday's
# print prices the Sat-Mon-holiday weekend package). MichCon daily is not free
# from EIA (no compact-table row); Chicago is the representative MISO
# North/Central hub (SOURCES_miso_citygate.md).
MISO_CITYGATE_DAILY_PATH: Path = GAS_PRICES_DIR / "miso_citygate_daily.csv"

# Measured PG&E Citygate / SoCal Citygate weekly Wednesday prints (EIA NG
# Weekly Update archive, NGI Daily GPI; scripts/data/fetch_pge_socal_citygate_daily
# .py — the same free published print the CAISO zonal-hub annual rows in
# ``caiso_zonal_gas_hub.csv`` are month-balanced from). The SoCal column is the
# gas leg of the caiso-87 surplus-state trigger
# (:func:`socal_citygate_weekly_hourly` →
# :func:`market_sim.model.transmission.inject_caiso_dsw_surplus_clean`): an
# LDC-citygate proxy for the desert-SW border hubs the remote CCGT buys at
# (documented boundary misalignment, rule 14 — reconciled real data over a
# guess).
PGE_SOCAL_CITYGATE_WEEKLY_PATH: Path = GAS_PRICES_DIR / "pge_socal_citygate_weekly.csv"


_WINTER_BASIS_CACHE: dict[Path, pd.DataFrame | None] = {}
_HH_MONTHLY_CACHE: dict[Path, dict[tuple[int, int], float]] = {}
_HH_DAILY_CACHE: dict[Path, dict[int, dict[int, list[float]]]] = {}
_HH_DAILY_DATED_CACHE: dict[Path, dict[int, dict[int, dict[int, float]]]] = {}
_TRANSCO_DAILY_CACHE: dict[Path, dict[int, dict[int, list[float]]]] = {}
_TRANSCO_DAILY_DATED_CACHE: dict[Path, dict[int, dict[int, dict[int, float]]]] = {}
_ALGONQUIN_DAILY_CACHE: dict[Path, dict[int, dict[int, dict[int, float]]]] = {}
_IROQUOIS_DAILY_CACHE: dict[Path, dict[int, dict[int, dict[int, float]]]] = {}
_CAISO_CITYGATE_DAILY_CACHE: dict[Path, dict[int, dict[int, dict[int, float]]]] = {}
_MISO_CITYGATE_DAILY_CACHE: dict[Path, dict[int, dict[int, dict[int, float]]]] = {}


# Clean-backed daily series cache, keyed by (fuel, hub) so a multi-year run reads
# the curated parquet once. Separate from _HH_DAILY_CACHE (raw, keyed by path).
_HH_DAILY_CLEAN_CACHE: dict[tuple[str, str], dict[int, dict[int, list[float]]]] = {}
_HH_DAILY_DATED_CLEAN_CACHE: dict[
    tuple[str, str], dict[int, dict[int, dict[int, float]]]
] = {}

# Per-datatype clean-path caches (separate from raw caches to avoid type collision).
_WINTER_BASIS_CLEAN_CACHE: dict[str, pd.DataFrame | None] = {}
_HH_MONTHLY_CLEAN_CACHE: dict[tuple[str, str], dict[tuple[int, int], float]] = {}
_ALGONQUIN_DAILY_CLEAN_CACHE: dict[str, dict[int, dict[int, dict[int, float]]]] = {}
_CAISO_CITYGATE_DAILY_CLEAN_CACHE: dict[
    str, dict[int, dict[int, dict[int, float]]]
] = {}


def _clean_fuel_price_daily(fuel: str, hub: str) -> dict[int, dict[int, list[float]]]:
    """Daily delivered price for one ``(fuel, hub)`` from the clean tree.

    Clean-backed mirror of the raw-CSV reshaping in :func:`_henry_hub_daily`:
    reads the curated ``fuel-prices`` dataset through the frozen
    :func:`scripts.lib.clean_io.read_clean` seam (``price_usd_per_mmbtu`` by
    ``fuel`` / ``hub``), selects the requested series and folds its daily price
    into the same ``{year: {month: [daily $/MMBtu, ...]}}`` structure the raw
    path builds. Ordered and grouped on ``interval_start_utc`` (00:00 UTC of each
    price date), so the year/month buckets match the raw ``date`` exactly.
    """
    # Local import: the model→scripts edge is the consumption seam and is only
    # crossed on the opt-in clean path, so module import stays cheap.
    from scripts.lib.clean_io import read_clean

    df = read_clean(
        _FUEL_PRICES_DATATYPE,
        validate=False,
        columns=["interval_start_utc", "fuel", "hub", "price_usd_per_mmbtu"],
    )
    sel = df[(df["fuel"] == fuel) & (df["hub"] == hub)].sort_values(
        "interval_start_utc"
    )
    out: dict[int, dict[int, list[float]]] = {}
    for row in sel.itertuples(index=False):
        ts = row.interval_start_utc
        out.setdefault(ts.year, {}).setdefault(ts.month, []).append(
            float(row.price_usd_per_mmbtu)
        )
    return out


def _clean_fuel_price_daily_dated(
    fuel: str, hub: str
) -> dict[int, dict[int, dict[int, float]]]:
    """Dated daily price for one ``(fuel, hub)`` from the clean tree.

    The **true-date** sibling of :func:`_clean_fuel_price_daily` (the clean-backed
    mirror of :func:`_henry_hub_daily_dated`): the same curated ``fuel-prices``
    rows, but keyed ``{year: {month: {day-of-month: $/MMBtu}}}`` so each
    trading-day quote keeps its actual calendar day instead of collapsing into a
    positional month list.
    """
    from scripts.lib.clean_io import read_clean

    df = read_clean(
        _FUEL_PRICES_DATATYPE,
        validate=False,
        columns=["interval_start_utc", "fuel", "hub", "price_usd_per_mmbtu"],
    )
    sel = df[(df["fuel"] == fuel) & (df["hub"] == hub)].sort_values(
        "interval_start_utc"
    )
    out: dict[int, dict[int, dict[int, float]]] = {}
    for row in sel.itertuples(index=False):
        ts = row.interval_start_utc
        out.setdefault(ts.year, {}).setdefault(ts.month, {})[ts.day] = float(
            row.price_usd_per_mmbtu
        )
    return out


def _clean_hub_monthly(fuel: str, hub: str) -> dict[tuple[int, int], float]:
    """Monthly hub price for one ``(fuel, hub)`` from the clean ``fuel-hub-monthly`` tree.

    Returns the same ``{(year, month): $/MMBtu}`` dict as the raw CSV path.
    """
    from scripts.lib.clean_io import read_clean

    df = read_clean(
        _FUEL_HUB_MONTHLY_DATATYPE,
        validate=False,
        columns=["fuel", "hub", "year", "month", "price_usd_per_mmbtu"],
    )
    sel = df[(df["fuel"] == fuel) & (df["hub"] == hub)]
    return {
        (int(r.year), int(r.month)): float(r.price_usd_per_mmbtu)
        for r in sel.itertuples(index=False)
    }


def _clean_algonquin_daily() -> dict[int, dict[int, dict[int, float]]]:
    """Algonquin daily prices from the clean ``fuel-prices`` tree.

    Returns the same ``{year: {month: {day-of-month: $/MMBtu}}}`` structure as
    the raw CSV path in :func:`_algonquin_daily`.  The ``interval_start_utc``
    day is used as the day-of-month key, matching how the raw path groups the
    date-column day.
    """
    from scripts.lib.clean_io import read_clean

    df = read_clean(
        _FUEL_PRICES_DATATYPE,
        validate=False,
        columns=["interval_start_utc", "fuel", "hub", "price_usd_per_mmbtu"],
    )
    sel = df[(df["fuel"] == "gas") & (df["hub"] == "algonquin")].sort_values(
        "interval_start_utc"
    )
    out: dict[int, dict[int, dict[int, float]]] = {}
    for row in sel.itertuples(index=False):
        ts = row.interval_start_utc
        out.setdefault(ts.year, {}).setdefault(ts.month, {})[ts.day] = float(
            row.price_usd_per_mmbtu
        )
    return out


def _clean_caiso_citygate_daily() -> dict[int, dict[int, dict[int, float]]]:
    """CA Composite citygate daily prices from the clean ``fuel-prices`` tree.

    Returns the same ``{year: {month: {day-of-month: $/MMBtu}}}`` structure as
    the raw CSV path in :func:`_caiso_citygate_daily_dated`.
    """
    from scripts.lib.clean_io import read_clean

    df = read_clean(
        _FUEL_PRICES_DATATYPE,
        validate=False,
        columns=["interval_start_utc", "fuel", "hub", "price_usd_per_mmbtu"],
    )
    sel = df[(df["fuel"] == "gas") & (df["hub"] == "ca_composite")].sort_values(
        "interval_start_utc"
    )
    out: dict[int, dict[int, dict[int, float]]] = {}
    for row in sel.itertuples(index=False):
        ts = row.interval_start_utc
        out.setdefault(ts.year, {}).setdefault(ts.month, {})[ts.day] = float(
            row.price_usd_per_mmbtu
        )
    return out


def _load_winter_basis_frame(path: Path | None) -> pd.DataFrame | None:
    """Return the regional gas-basis frame, or ``None`` when it carries no rows.

    The CSV (``iso,year,month,hub,basis_usd_mmbtu,source``) carries only the
    ISOs whose hub leg has been sourced (currently NEISO/Algonquin), so an
    empty or absent file resolves to ``None`` (callers fall back to measured
    923). Cached per path so a multi-year run reads the file once.
    """
    if path is None and _use_clean_data():
        from scripts.lib.clean_io import clean_exists, read_clean

        if clean_exists(_FUEL_BASIS_DATATYPE):
            if "_clean" not in _WINTER_BASIS_CLEAN_CACHE:
                df = read_clean(_FUEL_BASIS_DATATYPE, validate=False)
                _WINTER_BASIS_CLEAN_CACHE["_clean"] = df if not df.empty else None
            return _WINTER_BASIS_CLEAN_CACHE["_clean"]
    resolved = path or WINTER_GAS_BASIS_PATH
    if resolved in _WINTER_BASIS_CACHE:
        return _WINTER_BASIS_CACHE[resolved]
    frame: pd.DataFrame | None = None
    if Path(resolved).exists():
        loaded = pd.read_csv(resolved)
        if not loaded.empty:
            frame = loaded
    _WINTER_BASIS_CACHE[resolved] = frame
    return frame


def load_winter_gas_basis(
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
) -> np.ndarray | None:
    """Measured monthly delivered gas basis ($/MMBtu over Henry Hub), or ``None``.

    The constrained-hub winter-basis layer (doc-07 design decision 3 /
    doc-08 design decision 1, upload U4): a length-12 array of the ISO's
    named-hub basis (Transco Z6 NY / Iroquois for NYISO, Algonquin Citygate
    for NEISO) by calendar month, which spikes far above the plant-average
    EIA-923 delivered cost in January/February when pipeline capacity is
    scarce — the trigger that drives the dual-fuel gas→oil switch (P13).
    The NEISO leg is filled (ISO-NE MA gas index 2023-2025) and consumed by
    :func:`iso_hub_monthly_gas_prices` / :func:`apply_hub_basis_overlay`;
    for ISOs whose hub leg has not landed (NYISO) this returns ``None`` and
    the gas path falls back to the measured ISO-month 923 series
    (:func:`iso_monthly_gas_prices`), which already carries the winter
    shape volume-weighted across the ISO (Jan-2023 NYISO delivered
    $10.02/MMBtu vs Henry Hub $3.27) if not the full downstate-only blowout.

    Returns ``None`` when the CSV is absent/empty or has no rows for this ISO
    and year; otherwise a ``(12,)`` array with ``NaN`` for unreported months.
    """
    frame = _load_winter_basis_frame(path)
    if frame is None:
        return None
    sub = frame[(frame["iso"] == config.iso) & (frame["year"] == year)]
    if sub.empty:
        return None
    monthly = np.full(12, np.nan)
    for _, row in sub.iterrows():
        m = int(row["month"]) - 1
        if 0 <= m < 12:
            monthly[m] = float(row["basis_usd_mmbtu"])
    return monthly


def _henry_hub_monthly(path: Path | None) -> dict[tuple[int, int], float]:
    """Return ``{(year, month): $/MMBtu}`` measured Henry Hub monthly spot."""
    if path is None and _use_clean_data():
        from scripts.lib.clean_io import clean_exists

        if clean_exists(_FUEL_HUB_MONTHLY_DATATYPE):
            key = ("gas", "henry_hub")
            if key not in _HH_MONTHLY_CLEAN_CACHE:
                _HH_MONTHLY_CLEAN_CACHE[key] = _clean_hub_monthly(*key)
            return _HH_MONTHLY_CLEAN_CACHE[key]
    resolved = Path(path) if path else HENRY_HUB_MONTHLY_PATH
    if resolved in _HH_MONTHLY_CACHE:
        return _HH_MONTHLY_CACHE[resolved]
    out: dict[tuple[int, int], float] = {}
    if resolved.exists():
        frame = pd.read_csv(resolved)
        out = {
            (int(r.year), int(r.month)): float(r.price_usd_mmbtu)
            for r in frame.itertuples()
        }
    _HH_MONTHLY_CACHE[resolved] = out
    return out


def _henry_hub_daily(path: Path | None) -> dict[int, dict[int, list[float]]]:
    """Return ``{year: {month: [daily $/MMBtu, ...]}}`` measured Henry Hub spot.

    Days are grouped by calendar month in date order; trading-day gaps
    (weekends/holidays) simply yield shorter lists. Cached per path.

    When the opt-in clean-data path is enabled (:func:`_use_clean_data`) and no
    explicit ``path`` override is given, the series is sourced from the curated
    ``data/clean/fuel-prices`` parquet — the ``(gas, henry_hub)`` rows, via
    :func:`_clean_fuel_price_daily` — instead of the raw ``henry_hub_daily.csv``.
    The clean and raw paths are byte-for-byte equal (the curator carries the
    price column verbatim); when the clean partition is absent the loader falls
    back to raw, so enabling the flag never breaks a tree that has not been
    regenerated.
    """
    if path is None and _use_clean_data():
        from scripts.lib.clean_io import clean_exists

        if clean_exists(_FUEL_PRICES_DATATYPE):
            key = _HENRY_HUB_CLEAN_KEY
            if key not in _HH_DAILY_CLEAN_CACHE:
                _HH_DAILY_CLEAN_CACHE[key] = _clean_fuel_price_daily(*key)
            return _HH_DAILY_CLEAN_CACHE[key]
    resolved = Path(path) if path else HENRY_HUB_DAILY_PATH
    if resolved in _HH_DAILY_CACHE:
        return _HH_DAILY_CACHE[resolved]
    out: dict[int, dict[int, list[float]]] = {}
    if resolved.exists():
        frame = pd.read_csv(resolved, parse_dates=["date"]).sort_values("date")
        for r in frame.itertuples():
            out.setdefault(r.date.year, {}).setdefault(r.date.month, []).append(
                float(r.price_usd_mmbtu)
            )
    _HH_DAILY_CACHE[resolved] = out
    return out


def _henry_hub_daily_dated(
    path: Path | None,
) -> dict[int, dict[int, dict[int, float]]]:
    """Return ``{year: {month: {day-of-month: $/MMBtu}}}`` measured Henry Hub spot.

    The **true-date** view of the same measured series :func:`_henry_hub_daily`
    reads (the :func:`_transco_z6_daily_dated` construction applied to Henry
    Hub): each trading-day quote keyed by its actual calendar day, so the
    national daily shape (:func:`gas_daily_shape_factors`) can place each print
    where it really occurred and staircase the non-trading gaps, instead of
    spreading the month's quote list evenly across calendar days (which
    mislocated the Winter Storm Heather Friday 2024-01-12 spike onto Jan-13 —
    the miso-72 §3.7 all-ISO correctness finding,
    ``docs/handoffs/miso-winter-fuel-security-design-2026-07.md``). Same
    clean-tree opt-in as the list view; cached per path.
    """
    if path is None and _use_clean_data():
        from scripts.lib.clean_io import clean_exists

        if clean_exists(_FUEL_PRICES_DATATYPE):
            key = _HENRY_HUB_CLEAN_KEY
            if key not in _HH_DAILY_DATED_CLEAN_CACHE:
                _HH_DAILY_DATED_CLEAN_CACHE[key] = _clean_fuel_price_daily_dated(*key)
            return _HH_DAILY_DATED_CLEAN_CACHE[key]
    resolved = Path(path) if path else HENRY_HUB_DAILY_PATH
    if resolved in _HH_DAILY_DATED_CACHE:
        return _HH_DAILY_DATED_CACHE[resolved]
    out: dict[int, dict[int, dict[int, float]]] = {}
    if resolved.exists():
        frame = pd.read_csv(resolved, parse_dates=["date"]).sort_values("date")
        for r in frame.itertuples():
            out.setdefault(r.date.year, {}).setdefault(r.date.month, {})[r.date.day] = (
                float(r.price_usd_mmbtu)
            )
    _HH_DAILY_DATED_CACHE[resolved] = out
    return out


def _transco_z6_daily(path: Path | None) -> dict[int, dict[int, list[float]]]:
    """Return ``{year: {month: [daily $/MMBtu, ...]}}`` measured Transco Z6 NY spot.

    The NYISO analogue of :func:`_henry_hub_daily`, reading the scraped EIA NG
    Weekly archive "New York" (Transco Z6 NY) daily series from
    :data:`TRANSCO_Z6_NY_DAILY_PATH`. Days are grouped by calendar month in date
    order; trading-day gaps (weekends, holiday weeks EIA does not archive) simply
    yield shorter lists, which the mean-preserving shape (normalized to the
    month's own daily mean) handles gracefully. Cached per path.
    """
    if path is None and _use_clean_data():
        from scripts.lib.clean_io import clean_exists

        if clean_exists(_FUEL_PRICES_DATATYPE):
            key = ("gas", "transco_z6")
            if key not in _HH_DAILY_CLEAN_CACHE:
                _HH_DAILY_CLEAN_CACHE[key] = _clean_fuel_price_daily(*key)
            return _HH_DAILY_CLEAN_CACHE[key]
    resolved = Path(path) if path else TRANSCO_Z6_NY_DAILY_PATH
    if resolved in _TRANSCO_DAILY_CACHE:
        return _TRANSCO_DAILY_CACHE[resolved]
    out: dict[int, dict[int, list[float]]] = {}
    if resolved.exists():
        frame = pd.read_csv(resolved, parse_dates=["date"]).sort_values("date")
        for r in frame.itertuples():
            out.setdefault(r.date.year, {}).setdefault(r.date.month, []).append(
                float(r.transco_z6_ny_usd_mmbtu)
            )
    _TRANSCO_DAILY_CACHE[resolved] = out
    return out


def _algonquin_daily(path: Path | None) -> dict[int, dict[int, dict[int, float]]]:
    """Return ``{year: {month: {day-of-month: $/MMBtu}}}`` measured AGT spot prints.

    The ISO-NE analogue of :func:`_transco_z6_daily`, reading the real Algonquin
    Citygate daily prints harvested from the EIA NG Weekly Update narrative
    (:data:`ALGONQUIN_DAILY_PATH`, by ``scripts/data/fetch_algonquin_daily_spot.py``).
    Unlike the Transco series these prints are *sparse and irregular* (two dated
    Wednesdays per weekly page plus winter high/low days), so they are keyed by
    day-of-month — the daily overlay places each real print on its true calendar
    day and interpolates between them, rather than treating the list as a dense
    trading-day sequence. Cached per path.
    """
    if path is None and _use_clean_data():
        from scripts.lib.clean_io import clean_exists

        if clean_exists(_FUEL_PRICES_DATATYPE):
            if "_clean" not in _ALGONQUIN_DAILY_CLEAN_CACHE:
                _ALGONQUIN_DAILY_CLEAN_CACHE["_clean"] = _clean_algonquin_daily()
            return _ALGONQUIN_DAILY_CLEAN_CACHE["_clean"]
    resolved = Path(path) if path else ALGONQUIN_DAILY_PATH
    if resolved in _ALGONQUIN_DAILY_CACHE:
        return _ALGONQUIN_DAILY_CACHE[resolved]
    out: dict[int, dict[int, dict[int, float]]] = {}
    if resolved.exists():
        frame = pd.read_csv(resolved, parse_dates=["date"]).sort_values("date")
        for r in frame.itertuples():
            out.setdefault(r.date.year, {}).setdefault(r.date.month, {})[r.date.day] = (
                float(r.algonquin_citygate_usd_mmbtu)
            )
    _ALGONQUIN_DAILY_CACHE[resolved] = out
    return out


def _transco_z6_daily_dated(
    path: Path | None,
) -> dict[int, dict[int, dict[int, float]]]:
    """Return ``{year: {month: {day-of-month: $/MMBtu}}}`` Transco Z6 NY spot.

    The **true-date** view of the same measured series :func:`_transco_z6_daily`
    reads: each trading-day quote keyed by its actual calendar day, so the daily
    overlay can place each print where it really occurred and interpolate the
    non-trading gaps, instead of spreading the month's quote list evenly across
    calendar days (which shifted the Jan-2024 $23.90 cold-snap print from the
    16th onto the 12th and smeared its peak). Cached per path.
    """
    resolved = Path(path) if path else TRANSCO_Z6_NY_DAILY_PATH
    if resolved in _TRANSCO_DAILY_DATED_CACHE:
        return _TRANSCO_DAILY_DATED_CACHE[resolved]
    out: dict[int, dict[int, dict[int, float]]] = {}
    if resolved.exists():
        frame = pd.read_csv(resolved, parse_dates=["date"]).sort_values("date")
        for r in frame.itertuples():
            out.setdefault(r.date.year, {}).setdefault(r.date.month, {})[r.date.day] = (
                float(r.transco_z6_ny_usd_mmbtu)
            )
    _TRANSCO_DAILY_DATED_CACHE[resolved] = out
    return out


def _iroquois_z2_daily(path: Path | None) -> dict[int, dict[int, dict[int, float]]]:
    """Return ``{year: {month: {day-of-month: $/MMBtu}}}`` measured Iroquois Z2 prints.

    The eastern-NY analogue of :func:`_algonquin_daily`, reading the sparse real
    Iroquois Zone 2 spot prints harvested from the EIA NG Weekly Update narrative
    (:data:`IROQUOIS_Z2_DAILY_PATH`, from a planned, not-yet-landed fetcher).
    Prints are keyed by true calendar day; an absent file yields an empty map so
    every consumer degrades to the existing reconstruction (byte-identical until
    the fetch workflow lands the data). Cached per path.
    """
    resolved = Path(path) if path else _pkg_ns().IROQUOIS_Z2_DAILY_PATH
    if resolved in _IROQUOIS_DAILY_CACHE:
        return _IROQUOIS_DAILY_CACHE[resolved]
    out: dict[int, dict[int, dict[int, float]]] = {}
    if resolved.exists():
        frame = pd.read_csv(resolved, parse_dates=["date"]).sort_values("date")
        if "location" in frame.columns:
            # Only Zone 2 prints price the Iroquois-mapped NYISO zones; the
            # upstream Waddington border point (TransCanada supply, no New
            # England-complex premium) is provenance only.
            frame = frame[frame["location"] == "zone2"]
        for r in frame.itertuples():
            out.setdefault(r.date.year, {}).setdefault(r.date.month, {})[r.date.day] = (
                float(r.iroquois_z2_usd_mmbtu)
            )
    _IROQUOIS_DAILY_CACHE[resolved] = out
    return out


def _caiso_citygate_daily_dated(
    path: Path | None,
) -> dict[int, dict[int, dict[int, float]]]:
    """Return ``{year: {month: {day-of-month: $/MMBtu}}}`` CA Composite spot.

    The CAISO analogue of :func:`_transco_z6_daily_dated`: reads the measured
    California Composite Average citygate daily spot (:data:`CAISO_CITYGATE_DAILY_PATH`,
    scraped by ``scripts/data/fetch_caiso_citygate_daily.py`` from the same EIA
    Natural Gas Weekly Update compact spot table Transco Z6 NY is read from),
    keyed by true calendar day so the daily overlay places each trading-day
    print where it actually occurred and interpolates the non-trading gaps.
    Cached per path.

    When the opt-in clean-data path is enabled (:func:`_use_clean_data`) and no
    explicit ``path`` override is given, the series is sourced from the curated
    ``data/clean/fuel-prices`` parquet (the ``(gas, ca_composite)`` rows) instead
    of the raw CSV; the clean and raw paths are byte-for-byte equal.
    """
    if path is None and _use_clean_data():
        from scripts.lib.clean_io import clean_exists

        if clean_exists(_FUEL_PRICES_DATATYPE):
            if "_clean" not in _CAISO_CITYGATE_DAILY_CLEAN_CACHE:
                _CAISO_CITYGATE_DAILY_CLEAN_CACHE["_clean"] = (
                    _clean_caiso_citygate_daily()
                )
            return _CAISO_CITYGATE_DAILY_CLEAN_CACHE["_clean"]
    resolved = Path(path) if path else CAISO_CITYGATE_DAILY_PATH
    if resolved in _CAISO_CITYGATE_DAILY_CACHE:
        return _CAISO_CITYGATE_DAILY_CACHE[resolved]
    out: dict[int, dict[int, dict[int, float]]] = {}
    if resolved.exists():
        frame = pd.read_csv(resolved, parse_dates=["date"]).sort_values("date")
        for r in frame.itertuples():
            out.setdefault(r.date.year, {}).setdefault(r.date.month, {})[r.date.day] = (
                float(r.ca_composite_usd_mmbtu)
            )
    _CAISO_CITYGATE_DAILY_CACHE[resolved] = out
    return out


def _miso_citygate_daily_dated(
    path: Path | None,
) -> dict[int, dict[int, dict[int, float]]]:
    """Return ``{year: {month: {day-of-month: $/MMBtu}}}`` Chicago Citygate spot.

    The MISO analogue of :func:`_caiso_citygate_daily_dated`: reads the measured
    Chicago Citygate daily delivered-gas spot (:data:`MISO_CITYGATE_DAILY_PATH`,
    scraped by ``scripts/data/fetch_miso_citygate_daily.py`` from the "Chicago" row of
    the same EIA Natural Gas Weekly Update compact spot table), keyed by true
    calendar (trade) day so the winter fuel-security overlay
    (:func:`apply_miso_winter_citygate_daily`) can place each print on its gas
    FLOW day (trade + 1, weekend/holiday packages forward-filled — the caiso-90
    :func:`_flow_date_staircase`) and take the within-month *shape* from the real
    quotes. Cached per path; an absent file yields an empty map (consumer inert).
    """
    resolved = Path(path) if path else MISO_CITYGATE_DAILY_PATH
    if resolved in _MISO_CITYGATE_DAILY_CACHE:
        return _MISO_CITYGATE_DAILY_CACHE[resolved]
    out: dict[int, dict[int, dict[int, float]]] = {}
    if resolved.exists():
        frame = pd.read_csv(resolved, parse_dates=["date"]).sort_values("date")
        for r in frame.itertuples():
            out.setdefault(r.date.year, {}).setdefault(r.date.month, {})[r.date.day] = (
                float(r.chicago_citygate_usd_mmbtu)
            )
    _MISO_CITYGATE_DAILY_CACHE[resolved] = out
    return out


def socal_citygate_weekly_hourly(
    year: int, hours: int, path: Path | None = None
) -> np.ndarray | None:
    """Return ``(hours,)`` SoCal citygate gas from the weekly prints ($/MMBtu).

    Staircase expansion of the measured SoCal Citygate weekly Wednesday prints
    (:data:`PGE_SOCAL_CITYGATE_WEEKLY_PATH`, EIA NG Weekly Update archive):
    each hour carries the most recent weekly print (forward-fill on the
    non-leap model calendar; the year's first hours before the first print
    back-fill from it). The gas leg of the caiso-87 surplus-state trigger —
    a weekly-granularity fuel INPUT to a state classifier, not an hourly
    price, so the staircase is the honest representation of the print's own
    cadence.

    Returns ``None`` when the CSV is absent or carries no SoCal quotes for
    ``year`` (the caller stays byte-identical / inert).
    """
    resolved = Path(path) if path else PGE_SOCAL_CITYGATE_WEEKLY_PATH
    if not resolved.exists():
        return None
    frame = pd.read_csv(resolved, parse_dates=["date"])
    frame = frame[frame["date"].dt.year == year].sort_values("date")
    quotes = frame.dropna(subset=["socal_citygate_usd_mmbtu"])
    if quotes.empty:
        return None
    idx = pd.date_range(f"{year}-01-01", periods=hours + 24, freq="h")
    idx = idx[~((idx.month == 2) & (idx.day == 29))][:hours]
    series = (
        quotes.set_index("date")["socal_citygate_usd_mmbtu"]
        .reindex(idx.union(pd.DatetimeIndex(quotes["date"])))
        .sort_index()
        .ffill()
        .bfill()
        .reindex(idx)
    )
    return series.to_numpy(dtype=float)


def gas_daily_shape_factors(
    year: int, hours: int, path: Path | None = None
) -> np.ndarray:
    """Return ``(hours,)`` within-month daily gas-price shape factors.

    Each measured Henry Hub daily-spot quote is placed on its **true calendar
    (trade) date** and non-trading days (weekends / holidays) carry the last
    trading day's value forward — the :func:`_trade_date_staircase`, the
    :func:`_transco_z6_daily_dated` true-date construction — then each calendar
    day's factor is the staircase value divided by that month's own
    calendar-day staircase mean. Multiplying the (correctly-levelled) monthly
    gas series by these adds the real intra-month commodity swing while
    leaving the monthly mean, and hence the annual generation mix, unchanged.
    A month with no quotes resolves to all-ones (no shape). This is the same
    mechanism a forecast would use (a forward monthly level times a
    representative daily shape), so it is not backcast-only.

    True-date placement is REQUIRED, not cosmetic (the miso-72 §3.7 all-ISO
    correctness fix, ``docs/handoffs/miso-winter-fuel-security-design-2026-07.md``):
    the previous even-spread ``np.interp`` resampling of the month's quote LIST
    onto the calendar grid mislocated any spike bracketed by a trading gap —
    the Winter Storm Heather Friday 2024-01-12 Henry Hub print priced Jan-13 in
    the model — and linearly smeared every peak between quotes. The staircase
    keeps the spike on the day it printed and holds it flat across the
    following non-trading gap, never interpolating across a gap.

    Mean preservation per month HOLDS EXACTLY, by construction rather than by a
    post-hoc renormalization: the divisor is the same staircase's own
    calendar-day mean, so the factors average to exactly 1.0 in every full
    month (this subsumes the earlier G-A1 explicit-renormalization fix,
    docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md, which corrected the
    non-mean-preserving bare-``np.interp`` resampling). What the staircase
    changes about the mean's WEIGHTING is honest and documented: a quote
    bracketing a weekend/holiday gap now enters the month mean once per
    calendar day it covers (a Friday counts ~3×), exactly as the flat-priced
    non-trading days it prices, where the even-spread gave every quote equal
    calendar weight regardless of gap structure.
    """
    factors = np.ones(hours, dtype=float)
    dated = _pkg_ns()._henry_hub_daily_dated(path).get(year)
    if not dated:
        return factors
    daily = _pkg_ns()._trade_date_staircase(dated, year)  # (365,) true-date staircase
    if daily is None:
        return factors
    hour = 0
    day0 = 0  # cumulative day-of-year offset of the month on the non-leap clock
    for month_idx, n_days in enumerate(_DAYS_IN_MONTH):
        month_hours = n_days * 24
        if dated.get(month_idx + 1) and hour < hours:
            seg = daily[day0 : day0 + n_days]
            mean = float(seg.mean())
            if mean > 0:
                # Dividing by the month's own calendar-day staircase mean makes
                # the factors average to exactly 1.0 — mean-preserving with no
                # separate renormalization step — then repeat each day's factor
                # across its 24 hours.
                day_factor = seg / mean
                shaped = np.repeat(day_factor, 24)[: max(0, hours - hour)]
                factors[hour : hour + len(shaped)] = shaped
        hour += month_hours
        day0 += n_days
    return factors


def iso_hub_monthly_gas_prices(
    config: ScenarioConfig,
    year: int,
    basis_path: Path | None = None,
    henry_hub_path: Path | None = None,
) -> np.ndarray | None:
    """Measured hub-month delivered gas price ($/MMBtu), or ``None``.

    Reconstructs the ISO's trading-hub monthly spot price as measured Henry
    Hub monthly spot + the measured hub-month basis from
    :func:`load_winter_gas_basis` (for NEISO: the Algonquin Citygate /
    ISO-NE Massachusetts gas index, whose Dec-Feb basis blows out to
    +$4-13/MMBtu while plant-average EIA-923 receipts stay far lower).
    Months without a basis row — or without a Henry Hub monthly quote —
    are ``NaN`` for the caller to leave on its existing series; returns
    ``None`` when the CSV, the ISO or the year is absent entirely (forward
    years, ISOs with no sourced hub series).
    """
    # NYISO reconciled winter spread (rule #13): the measured annual
    # Iroquois-Transco spread re-allocated across months by the measured
    # Algonquin scarcity signal, replacing the flat committed construction.
    # Falls through (byte-identical) when off or when a series is incomplete.
    if config.iso == "NYISO" and getattr(config, "nyiso_iroquois_winter_spread", False):
        rec = _pkg_ns().nyiso_reconciled_reference_monthly(year, basis_path=basis_path)
        if rec is not None:
            return rec[0]
    basis = load_winter_gas_basis(config, year, path=basis_path)
    if basis is None:
        return None
    henry_hub = _pkg_ns()._henry_hub_monthly(henry_hub_path)
    monthly = np.full(12, np.nan)
    for m in range(12):
        hh = henry_hub.get((year, m + 1))
        if hh is not None and not np.isnan(basis[m]):
            monthly[m] = hh + float(basis[m])
    if np.isnan(monthly).all():
        return None
    return monthly


def _nyiso_hub_daily_gas_prices(
    config: ScenarioConfig,
    year: int,
    basis_path: Path | None = None,
    henry_hub_path: Path | None = None,
    transco_path: Path | None = None,
) -> np.ndarray | None:
    """NYISO daily-resolved reference-hub gas price ($/MMBtu), ``(hours,)``.

    The NYISO leg of :func:`iso_hub_daily_gas_prices`. The monthly reference-zone
    (Iroquois Z2) hub level comes from :func:`iso_hub_monthly_gas_prices`
    (measured Henry Hub month + the Transco/Iroquois basis row); the within-month
    day-to-day swing comes from the **measured Transco Z6 NY daily quotes placed
    on their true calendar days** (:func:`_transco_z6_daily_dated`) — cheap
    shoulder days and the cold-snap spike land where they actually occurred, with
    non-trading gaps linearly interpolated — **mean-preserving** (the daily
    factors renormalize to 1.0 within each month), so the monthly hub level,
    annual gas burn and fuel mix are unchanged. (The prior even-spread placement
    shifted the Jan-2024 $23.90 print from the 16th to the 12th and attenuated
    every peak between trading-day quotes.) The per-zone offsets
    (:func:`apply_nyiso_zonal_gas_basis`) are layered on top by the caller
    exactly as in the monthly path.

    Where the **measured Iroquois Z2 daily prints** exist for a month
    (:func:`_iroquois_z2_daily`, harvested from the EIA NG Weekly narrative by a
    planned, not-yet-landed fetcher; ≥2 prints required so a lone quote
    never re-levels a month), they supersede the reconstruction for the days they
    bracket: prints are placed on their true days and interpolated between, and
    outside the bracketed span the series falls back to the Transco-shaped
    reconstruction. This month is deliberately **not** re-normalized to the
    reconstructed monthly level: the reconstruction (Transco monthly + the SOM
    *annual* Iroquois-Transco spread) demonstrably under-reads constrained winter
    months (Dec-2024 reconstruction $3.16 vs the measured New England complex the
    Z2 segment physically trades in at ~$9), and the measured prints are the
    better data (rule #13) — the monthly mean moves exactly by what the measured
    prints say, no fitted constant.

    Months without a basis row, a Henry Hub quote, or any daily quotes keep the
    flat monthly value (``NaN`` here for the overlay to fall back on), so a
    holiday-week archive gap never biases a month. Returns ``None`` when the
    monthly hub series is unavailable (forward years, no basis rows), so
    :func:`apply_hub_basis_overlay` falls back to the flat monthly overlay.

    Under ``ScenarioConfig.nyiso_hub_gap_month_level`` (default OFF, nyiso-223) a
    calendar day the archive never priced takes the month's OWN observed level
    (factor 1.0) instead of the clamped nearest-print deviation ``np.interp``
    supplies by default. A month whose prints do NOT reach its own edges is the
    normal case, not the exception — the EIA Natural Gas Weekly Update skips the
    late-December holiday weeks, so December carries a 10-13 day trailing gap in
    six of eight archived years — and the clamp therefore fabricates a level for
    precisely the year's coldest days. The gate is still exactly mean-preserving
    (the ``fbar`` renormalisation is applied after it), so it moves WHICH days
    are dear and never how dear the month is; annual gas burn and fuel mix are
    unchanged by construction.
    """
    monthly = _pkg_ns().iso_hub_monthly_gas_prices(
        config, year, basis_path, henry_hub_path
    )
    if monthly is None:
        return None
    transco_dated = _pkg_ns()._transco_z6_daily_dated(transco_path).get(year, {})
    iroquois_prints = _iroquois_z2_daily(None).get(year, {})
    gap_month_level = bool(getattr(config, "nyiso_hub_gap_month_level", False))
    T = config.hours
    out = np.full(T, np.nan, dtype=float)
    hour = 0
    for m in range(12):
        n_days = _DAYS_IN_MONTH[m]
        month_hours = n_days * 24
        hub_m = monthly[m]
        if not np.isnan(hub_m) and hour < T:
            dated = transco_dated.get(m + 1, {})
            if dated:
                days = np.array(sorted(dated), dtype=float)
                vals = np.array([dated[int(d)] for d in days], dtype=float)
                mean = float(vals.mean())
                if mean > 0:
                    # Place each trading-day quote on its true calendar day and
                    # interpolate the gaps (weekends/holiday weeks inherit the
                    # bracketing trading values), then renormalize so the
                    # calendar-day factors average to exactly 1.0 — scaling the
                    # monthly hub level by them stays exactly mean-preserving.
                    day_factor = np.interp(np.arange(n_days), days - 1.0, vals / mean)
                    if gap_month_level:
                        # Rule 14 [R-ACCURATE] repair (nyiso-223). ``np.interp``
                        # CLAMPS outside the observed span, so a calendar day the
                        # archive never priced inherits the NEAREST PRINT'S
                        # DEVIATION from the month — an assertion the measured
                        # series does not make. It is not a rare edge: the EIA
                        # Natural Gas Weekly Update publishes no page over the
                        # late-December holiday weeks, leaving a 10-13 day
                        # TRAILING gap in December in six of the eight archived
                        # years (2018 12 d, 2019 13 d, 2022 10 d, 2023 11 d,
                        # 2024 13 d), plus shorter June/July/November gaps — i.e.
                        # the fabricated days are systematically the coldest and
                        # most volatile of the year. Measured for 2022: the last
                        # print is Dec-21 at $6.29 against a December print-mean
                        # of $7.32, so the whole Winter Storm Elliott window
                        # (Dec 22-31) is asserted 14 % CHEAPER than its own month.
                        # An unpriced day instead takes the month's own observed
                        # level (factor 1.0) — strictly the weaker assertion,
                        # ZERO parameters, still exactly mean-preserving through
                        # the ``fbar`` renormalisation below (so monthly hub
                        # level, annual gas burn and fuel mix are untouched), and
                        # the identical construction in a forecast year, which is
                        # rule 13 [R-MEASURED]'s forward test.
                        grid = np.arange(n_days, dtype=float)
                        unpriced = (grid < days[0] - 1.0) | (grid > days[-1] - 1.0)
                        day_factor[unpriced] = 1.0
                    fbar = float(day_factor.mean())
                    if fbar > 0:
                        day_factor = day_factor / fbar
                    day_hub = hub_m * day_factor
                else:
                    day_hub = np.full(n_days, hub_m)
            else:
                # No daily quotes this month: keep the flat monthly hub level.
                day_hub = np.full(n_days, hub_m)
            # Measured Iroquois Z2 prints (≥2) locally supersede the
            # reconstruction across the day span they bracket (rule #13).
            iq = iroquois_prints.get(m + 1, {})
            if len(iq) >= 2:
                iq_days = np.array(sorted(iq), dtype=float)
                iq_vals = np.array([iq[int(d)] for d in iq_days], dtype=float)
                lo, hi = int(iq_days[0]) - 1, int(iq_days[-1]) - 1
                span = np.arange(lo, hi + 1, dtype=float)
                day_hub = day_hub.copy()
                day_hub[lo : hi + 1] = np.interp(span, iq_days - 1.0, iq_vals)
            shaped = np.repeat(day_hub, 24)[: max(0, T - hour)]
            out[hour : hour + len(shaped)] = shaped
        hour += month_hours
    if np.isnan(out).all():
        return None
    return out


# Minimum trade-day gap (calendar days between consecutive prints) that marks a
# PUBLICATION BLACKOUT rather than a legitimate trading package. Identified from
# the committed ca_composite series' own trade-gap histogram (2018-2026, 1,805
# gaps; scripts/probes/caiso288_blackout_census.py, rule 5 [R-NO-MAGIC]):
#
#     gap 1 d: 1401   gap 2 d:    2   gap 3 d:  312   gap 4 d:   52
#     gap 5 d:    3   gap 8 d:   17   gap 9 d:    1   gap 12 d:   9
#     gap 15 d:   7   gap 19 d:   1
#
# Gaps of 1-4 days ARE the market's trading packages (consecutive weekdays; the
# Friday trade that covers the Sat-Mon weekend package; its holiday-extended
# Sat-Tue form), and the staircase is the correct representation of them: a real
# trade priced those flow days. Gaps of >=8 days are weeks in which EIA published
# no Natural Gas Weekly Update at all (Thanksgiving, and the two weeks spanning
# Christmas/New Year, every year) - NO trade priced those days, so holding the
# last print across them is an extrapolation, not a measurement.
#
# The histogram is EMPTY at 6 and 7, so any threshold in [6, 7] selects exactly
# the same 35 gaps and the value is NOT selectable against any result. 6 is taken
# as the lower edge of that empty region. The three 5-day gaps (2018-08-31,
# 2023-04-06, 2023-06-30 - holiday weeks EIA published with a short table) stay
# on the staircase, which is the conservative side of the split.
_GAS_BLACKOUT_MIN_GAP_DAYS = 6


def _basis_bridge_blackouts(
    flow: "pd.Series",
    hh_daily: "pd.Series",
    min_gap_days: int = _GAS_BLACKOUT_MIN_GAP_DAYS,
) -> "pd.Series":
    """Replace constant-extension across publication blackouts with an
    HH-basis interpolation, leaving every legitimate trading package alone.

    ``flow`` is a date-indexed series of measured citygate prints already placed
    on their flow days (gaps NOT yet filled); ``hh_daily`` is the measured Henry
    Hub daily spot, whose publication calendar has no blackout (it is a
    market-data feed, not a weekly EIA narrative). For each pair of consecutive
    measured prints separated by ``>= min_gap_days`` calendar days, the interior
    days are built as

        ``citygate[d] = hh_staircase[d] + basis_L + w(d) * (basis_R - basis_L)``

    where ``basis_X = citygate[X] - hh_staircase[X]`` at the two bracketing
    MEASURED prints and ``w`` ramps linearly from 0 to 1 across the gap. Shorter
    gaps are untouched, so the caller's own ``ffill`` still staircases them.

    This is the construction the repo already uses for a hub-month level
    (:func:`iso_hub_monthly_gas_prices` = measured HH + measured basis) and for
    the within-month daily shape (:func:`gas_daily_shape_factors`), applied to
    the one place the daily series has no measurement of its own.

    WHY THIS CONSTRUCTION AND NOT CONSTANT-EXTENSION OR A STRAIGHT LINE, decided
    on the GAS DATA and never on a price residual (rule 1 [R-STRUCT]): over a
    synthetic holdout of 33,216 withheld MEASURED citygate days (every fully
    measured window of 8 / 12 / 15 / 19 days in the committed series,
    ``scripts/probes/caiso288_blackout_census.py`` G-FILL), reconstruction error
    against the withheld truth is

        hold-last (current)  MAE 0.716  bias +0.039  RMSE 2.376
        linear interpolation MAE 0.519  bias +0.033  RMSE 1.873
        HH-basis (this)      MAE 0.481  bias +0.017  RMSE 1.787

    and this construction wins on MAE, bias and RMSE at EVERY gap length. On the
    cases that matter - a left anchor in the series' top decile, i.e. a blackout
    that opens on a spike - hold-last carries a systematic **+0.879 $/MMBtu high
    bias** (MAE 2.923) against this construction's +0.170 (MAE 1.681). The
    defect hold-last has is therefore not merely noise: it is a one-sided
    over-statement of gas exactly when the last print is extreme.

    Rule 13 [R-MEASURED]: every input here is measured (both bracketing
    citygate prints, the HH daily series inside the gap) and the identical
    construction regenerates for a forward year from forward curves, so it is
    admissible outside the backcast. Nothing is tuned to any residual.
    """
    if flow.empty or hh_daily.empty:
        return flow
    cal = pd.date_range(flow.index.min(), flow.index.max(), freq="D")
    hs = hh_daily.reindex(hh_daily.index.union(cal)).sort_index().ffill().bfill()
    out = flow.reindex(flow.index.union(cal)).sort_index()
    known = out.dropna()
    for left, right in zip(known.index, known.index[1:]):
        span = (right - left).days
        if span < min_gap_days:
            continue  # a real trading package - the staircase is correct
        inner = pd.date_range(
            left + pd.Timedelta(days=1), right - pd.Timedelta(days=1), freq="D"
        )
        if not len(inner):
            continue
        basis_l = float(known[left]) - float(hs[left])
        basis_r = float(known[right]) - float(hs[right])
        w = np.array([(d - left).days / span for d in inner], dtype=float)
        out.loc[inner] = (
            hs.reindex(inner).to_numpy(dtype=float) + basis_l + w * (basis_r - basis_l)
        )
    return out


def _flow_date_staircase(
    dated_year: dict[int, dict[int, float]],
    year: int,
    bridge_all_years: dict[int, dict[int, dict[int, float]]] | None = None,
    bridge_hh: "pd.Series | None" = None,
) -> np.ndarray | None:
    """365-day flow-date staircase ($/MMBtu) from trade-day citygate prints.

    The daily citygate spot is a next-day-delivery index (NGI Daily GPI via the
    EIA NG Weekly compact table): a print keyed to trade day T prices gas that
    FLOWS on T+1, and Friday's trade covers the whole Sat-through-Monday
    (holiday-extended) weekend package. This helper places each of ``year``'s
    prints on its real-calendar flow day (trade + 1) and forward-fills the
    non-trading gaps — every flow day carries the most recent package that
    priced it — then drops Feb-29 to land on the model's non-leap 365-day
    clock. Days before the year's first flow print back-fill from it (the same
    left-edge constant-extension the trade-dated interpolation applies); a
    Dec-31 print flows into the NEXT year and is dropped (within-year
    construction, the year-start edge is documented as back-filled). Returns
    ``None`` when the year has no prints.

    ``bridge_all_years`` / ``bridge_hh`` (caiso-288,
    ``config.caiso_citygate_blackout_bridge``): when BOTH are given, a gap of
    ``>= _GAS_BLACKOUT_MIN_GAP_DAYS`` calendar days between consecutive measured
    prints is an EIA **publication blackout** rather than a trading package, and
    its interior is built by :func:`_basis_bridge_blackouts` instead of being
    constant-extended. ``bridge_all_years`` is the FULL multi-year dated map
    (not just ``year``'s), because a December blackout's right-hand measured
    anchor is the following January's first print — the one case the within-year
    construction above cannot bracket. Every legitimate 1-4 day package still
    staircases, and the returned array is byte-identical to the unbridged one in
    any year whose gaps are all packages. Off by default; the caller passes
    ``None`` and nothing changes.
    """
    stamps = {
        pd.Timestamp(year=year, month=m, day=d) + pd.Timedelta(days=1): v
        for m, days in sorted(dated_year.items())
        for d, v in sorted(days.items())
    }
    if not stamps:
        return None
    idx = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    if bridge_all_years and bridge_hh is not None and not bridge_hh.empty:
        # Bracket this year's blackouts against the neighbouring years' prints
        # (a Dec blackout's right anchor is the next January's first print),
        # then keep only this year's calendar.
        flow_all = pd.Series(
            {
                pd.Timestamp(year=y, month=m, day=d) + pd.Timedelta(days=1): v
                for y, months in sorted(bridge_all_years.items())
                for m, days in sorted(months.items())
                for d, v in sorted(days.items())
            }
        ).sort_index()
        bridged = _pkg_ns()._basis_bridge_blackouts(flow_all, bridge_hh)
        s = bridged.reindex(idx.union(bridged.index)).sort_index()
    else:
        s = pd.Series(stamps).sort_index().reindex(idx.union(pd.Index(stamps)))
    s = s.sort_index().ffill().bfill().reindex(idx)
    s = s[~((s.index.month == 2) & (s.index.day == 29))]
    return s.to_numpy(dtype=float)


def _trade_date_staircase(
    dated_year: dict[int, dict[int, float]], year: int
) -> np.ndarray | None:
    """365-day true-trade-date staircase ($/MMBtu) from dated daily quotes.

    The trade-date sibling of :func:`_flow_date_staircase`, for a commodity spot
    series whose print IS the price on its own trading day (Henry Hub daily
    spot), not a next-day-delivery index: each quote sits on its true calendar
    (trade) date, and every non-trading day (weekend / holiday) carries the
    LAST trading day's value forward — a staircase, never an interpolation
    across the gap, so a convex single-day spike stays exactly on the day it
    printed instead of leaking into (or being relocated onto) its neighbours.
    Feb-29 is dropped to land on the model's non-leap 365-day clock (a Feb-29
    quote still forward-fills any following non-trading days); days before the
    year's first quote back-fill from it (the same left-edge constant extension
    the flow-date staircase applies). Returns ``None`` when the year has no
    quotes.
    """
    stamps = {
        pd.Timestamp(year=year, month=m, day=d): v
        for m, days in sorted(dated_year.items())
        for d, v in sorted(days.items())
    }
    if not stamps:
        return None
    idx = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    s = pd.Series(stamps).sort_index()
    s = s.reindex(idx).ffill().bfill()
    s = s[~((s.index.month == 2) & (s.index.day == 29))]
    return s.to_numpy(dtype=float)


def _caiso_hub_daily_gas_prices(
    config: ScenarioConfig,
    year: int,
    basis_path: Path | None = None,
    henry_hub_path: Path | None = None,
    citygate_path: Path | None = None,
    *,
    spot_level: bool = False,
    spot_coverage: bool = False,
) -> np.ndarray | None:
    """CAISO daily-resolved citygate gas price ($/MMBtu), ``(hours,)``, or ``None``.

    ``spot_coverage`` (caiso-246, ``config.caiso_citygate_spot_coverage``; only
    meaningful with ``spot_level``): ALSO cover a month that has measured daily
    prints of its own but NO survey basis row — EIA publishes N3050CA3 as
    ``NA`` for 2025-09/10/11 — building its day series exactly as every other
    spot-level month. The survey value is never used where prints exist, so
    this lifts the gate, not the level. Default off keeps the coverage rule
    described below byte-identical.

    The CAISO leg of :func:`iso_hub_daily_gas_prices`, structurally identical to
    the NYISO leg (:func:`_nyiso_hub_daily_gas_prices`): the monthly hub level
    comes from :func:`iso_hub_monthly_gas_prices` (measured Henry Hub month +
    the measured SoCal/PG&E citygate basis row), and the within-month day-to-day
    swing comes from the **measured California Composite Average citygate daily
    spot placed on its true calendar days** (:func:`_caiso_citygate_daily_dated`)
    — dense EIA Weekly compact-table trading-day quotes, not sparse narrative
    prints, exactly like Transco Z6 NY. The daily factors renormalize to 1.0
    within each month before scaling the monthly hub level, so the construction
    is **mean-preserving**: the monthly hub level, annual gas burn and fuel mix
    are unchanged, only the within-month shape moves.

    This resolves the caiso-53 root-cause finding that the monthly-average gas
    overlay is too blunt in spike months: Jan-2023 held a measured $24.29/MMBtu
    citygate print early in the month (2023-01-12) followed by a collapse to
    ~$8-11/MMBtu the last week, but the flat monthly mean (HH + basis $24.34,
    ~$28 total) prices every one of the month's 744 hours at the early-month
    extreme. The daily shape lets the committed-CC repricing (~$213/MWh) cross
    the C3c $200 threshold only on the days gas actually spiked, instead of all
    month.

    Months without a basis row, a Henry Hub quote, or any daily citygate quotes
    keep the flat monthly value (``NaN`` here for the overlay to fall back on).
    Returns ``None`` when the monthly hub series is unavailable (forward years,
    no basis rows), so :func:`apply_hub_basis_overlay` falls back to the flat
    monthly overlay. Backcast-only by construction (2023-2025 basis rows only).

    ``config.caiso_citygate_flow_date`` (caiso-90): when set, the prints are
    placed on their gas FLOW days (trade + 1, weekend/holiday packages
    forward-filled as a staircase — :func:`_flow_date_staircase`) instead of
    their trade days, in both the shape-only and ``spot_level`` branches; the
    month-coverage rules below are unchanged.

    ``spot_level`` (caiso-84, ``caiso_citygate_spot_level``;
    FINDING-caiso-winter-gas-level-2026-07-15): when set, each month's LEVEL is
    anchored to the **calendar-interpolated monthly mean of the measured daily
    citygate series itself** rather than renormalized back to the
    HH+N3050CA3-survey monthly level. The daily prints are placed on their true
    calendar days and interpolated across the gaps exactly as in the default
    path, but the resulting absolute daily $/MMBtu are used directly (not scaled
    to the survey mean), so BOTH the within-month shape and the monthly level
    come from the daily spot the marginal cost-based DEB actually bids at
    (Jan-2023 monthly mean $16.1 vs the survey's $28.08). Months with no daily
    quotes keep the survey monthly level unchanged (the ``else`` branch), so a
    coverage gap never re-levels a month. Coverage is the SAME month-set as the
    default path — a month reprices only where the survey basis row exists — so
    ``spot_level`` is a pure LEVEL swap on the keeper's covered months, never a
    coverage expansion (months the survey leaves uncovered, e.g. CAISO 2025
    Sep-Nov with no basis row, stay on the base EIA-923 series exactly as in the
    keeper). The N3050CA3 survey and the daily spot are both measured EIA
    series; the marginal-offer representation requires the latter (rule 15), and
    the +$0.46 citygate->plant transport is still layered on by the caller
    (:func:`apply_hub_basis_overlay`).
    """
    monthly = _pkg_ns().iso_hub_monthly_gas_prices(
        config, year, basis_path, henry_hub_path
    )
    if monthly is None:
        return None
    citygate_dated = _pkg_ns()._caiso_citygate_daily_dated(citygate_path).get(year, {})
    # caiso-90 (caiso_citygate_flow_date): the prints are a next-day-delivery
    # index, so place them on their FLOW days (trade + 1, weekend packages
    # forward-filled) instead of their trade days. Built once for the year so
    # a month-end print correctly flows into the next covered month; month
    # coverage below is unchanged (a month reprices only where the survey
    # basis row AND its own prints exist).
    # caiso-288 (caiso_citygate_blackout_bridge): EIA publishes no Natural Gas
    # Weekly Update in Thanksgiving week or the two weeks spanning Christmas /
    # New Year, so the daily series carries a 8-19 day hole in Nov and Dec of
    # EVERY year. The staircase's constant-extension fills that hole with the
    # last print before it, which in Dec-2022 is $53.59/MMBtu - the single
    # highest print of the year, held across 10 of December's 31 days while the
    # measured record (SoCal citygate weekly $48.74 -> $20.18; Henry Hub daily
    # -51%) says the western gas crisis was collapsing through exactly those
    # days. Armed, the blackout interiors are rebuilt from the measured HH daily
    # series and the two bracketing measured citygate prints instead
    # (:func:`_basis_bridge_blackouts`, which carries the identification).
    # Rule 14 [R-ACCURATE]: this replaces an extrapolation with a measured
    # reconciliation; rule 19 [R-ONE-MECH]: it REPLACES the constant extension
    # on those days rather than stacking on it, and touches no other day.
    bridge_all = bridge_hh = None
    if getattr(config, "caiso_citygate_blackout_bridge", False):
        bridge_all = _pkg_ns()._caiso_citygate_daily_dated(citygate_path)
        hh_dated = _pkg_ns()._henry_hub_daily_dated(henry_hub_path)
        bridge_hh = pd.Series(
            {
                pd.Timestamp(year=y, month=m, day=d): v
                for y, months in sorted(hh_dated.items())
                for m, days in sorted(months.items())
                for d, v in sorted(days.items())
            }
        ).sort_index()
    flow_series = (
        _flow_date_staircase(citygate_dated, year, bridge_all, bridge_hh)
        if getattr(config, "caiso_citygate_flow_date", False) and citygate_dated
        else None
    )
    T = config.hours
    out = np.full(T, np.nan, dtype=float)
    hour = 0
    day0 = 0  # cumulative day-of-year offset of month m on the non-leap clock
    for m in range(12):
        n_days = _DAYS_IN_MONTH[m]
        month_hours = n_days * 24
        hub_m = monthly[m]
        # Covered on the SAME months as the default path (survey basis row
        # present); spot_level only changes the LEVEL within them — unless
        # spot_coverage (caiso-246) also admits a month on its own daily prints.
        dated = citygate_dated.get(m + 1, {})
        own_prints = bool(spot_level and spot_coverage and dated)
        if (not np.isnan(hub_m) or own_prints) and hour < T:
            if dated and flow_series is not None:
                # Flow-date placement: the month's slice of the year-level
                # staircase. spot_level keeps the absolute $/MMBtu; the
                # shape-only branch keeps its mean-preserving renormalization.
                seg = flow_series[day0 : day0 + n_days]
                if spot_level:
                    day_hub = seg
                else:
                    mean = float(seg.mean())
                    if mean > 0:
                        day_factor = seg / mean
                        fbar = float(day_factor.mean())
                        if fbar > 0:
                            day_factor = day_factor / fbar
                        day_hub = hub_m * day_factor
                    else:
                        day_hub = np.full(n_days, hub_m)
            elif dated:
                days = np.array(sorted(dated), dtype=float)
                vals = np.array([dated[int(d)] for d in days], dtype=float)
                if spot_level:
                    # LEVEL + shape straight from the measured daily spot: place
                    # each quote on its true calendar day and interpolate the
                    # gaps, then use the absolute daily prices directly (NOT
                    # renormalized to the survey monthly level). The month's mean
                    # becomes the calendar-interpolated daily-spot mean.
                    day_hub = np.interp(np.arange(n_days), days - 1.0, vals)
                else:
                    mean = float(vals.mean())
                    if mean > 0:
                        # Place each trading-day quote on its true calendar day
                        # and interpolate the gaps (weekends/holidays inherit the
                        # bracketing trading values), then renormalize so the
                        # calendar-day factors average to exactly 1.0 — scaling
                        # the monthly hub level by them stays mean-preserving.
                        day_factor = np.interp(
                            np.arange(n_days), days - 1.0, vals / mean
                        )
                        fbar = float(day_factor.mean())
                        if fbar > 0:
                            day_factor = day_factor / fbar
                        day_hub = hub_m * day_factor
                    else:
                        day_hub = np.full(n_days, hub_m)
            else:
                # No daily citygate quotes this month: keep the flat monthly hub
                # (the survey level under spot_level, unchanged).
                day_hub = np.full(n_days, hub_m)
            shaped = np.repeat(day_hub, 24)[: max(0, T - hour)]
            out[hour : hour + len(shaped)] = shaped
        hour += month_hours
        day0 += n_days
    if np.isnan(out).all():
        return None
    return out


def iso_hub_daily_gas_prices(
    config: ScenarioConfig,
    year: int,
    basis_path: Path | None = None,
    henry_hub_path: Path | None = None,
) -> np.ndarray | None:
    """Daily-resolved hub-month gas price ($/MMBtu), ``(hours,)``, or ``None``.

    The daily refinement of :func:`iso_hub_monthly_gas_prices` (doc-08 NEISO,
    the daily-AGT leg of upload U4). In each covered month the flat monthly hub
    price (measured Henry Hub month + measured AGT month basis) is replaced by
    a daily series, **mean-preserving at the monthly hub level** so the annual
    gas burn and fuel mix are unchanged:

      ``daily_hub[d] = hh_daily_norm[d] + basis_daily[d]``

    where ``hh_daily_norm`` is the measured Henry Hub daily within-month series
    re-centred to the measured monthly mean, and ``basis_daily`` is the
    **measured Algonquin Citygate daily basis** — anchored to the real AGT spot
    prints EIA publishes in its Weekly Update narrative
    (:func:`_algonquin_daily`, ``scripts/data/fetch_algonquin_daily_spot.py``):

      * In a positive-basis (winter-blowout) month with ≥2 real AGT prints, the
        prints are converted to a same-day basis (``agt_print − hh_daily``) and
        interpolated across the month's days — the real cold-day spike (e.g. the
        $28/MMBtu 2023-02-02 arctic print) lands on its true calendar day.
      * In a positive-basis month with <2 prints, the within-month *shape* is
        taken from the measured **Transco Z6 NY daily basis**, which tracks AGT
        basis ~1:1 (measured slope ≈0.95, corr ≈0.79) since both citygates blow
        out on the same Northeast pipeline-scarcity days.
      * Shoulder/summer months (zero or negative basis, no pipeline scarcity)
        and months with neither prints nor Transco quotes keep the flat basis.

    The daily basis is **mean-preserved** to the measured monthly AGT basis
    (additive shift), so the monthly hub level, annual gas burn and fuel mix are
    unchanged — only the within-month shape is added. Every driver is real,
    free, EIA-sourced gas-market data; there is no demand/oil/LMP-tuned proxy
    (the retired ``AGT_DAILY_BASIS_CONVEXITY`` exponent was fitted to the oil
    burn, violating the measured-input rule). Months without a measured basis row
    or Henry Hub quote stay ``NaN`` for the caller to leave on its existing series.

    This is the daily AGT spot the marginal gas unit would actually bid at on a
    cold day; it is what trips the dual-fuel gas->oil switch and the oil-steam
    fleet (:func:`apply_dual_fuel_pricing`, applied after this overlay) and so
    builds the ISO-NE winter LMP tail. Returns ``None`` when the monthly basis is
    unavailable (so the caller falls back to the flat monthly overlay).

    **NYISO** and **CAISO** use a different daily leg (:func:`_nyiso_hub_daily_gas_prices`,
    :func:`_caiso_hub_daily_gas_prices`): their marginal hub *is* a measured
    daily-spot series (Transco Z6 NY / California Composite Average, both EIA NG
    Weekly compact-table rows), so the within-month shape is taken straight from
    the real daily quotes rather than the AGT narrative-print reconstruction
    below (which is NEISO-specific and must not be reached for other ISOs).
    """
    if config.iso == "NYISO":
        return _nyiso_hub_daily_gas_prices(config, year, basis_path, henry_hub_path)
    if config.iso == "CAISO":
        return _caiso_hub_daily_gas_prices(config, year, basis_path, henry_hub_path)
    basis = load_winter_gas_basis(config, year, path=basis_path)
    if basis is None:
        return None
    henry_hub = _pkg_ns()._henry_hub_monthly(henry_hub_path)
    hh_daily = _pkg_ns()._henry_hub_daily(henry_hub_path).get(year, {})
    all_agt = _pkg_ns()._algonquin_daily(None)
    agt_prints = all_agt.get(year, {})
    transco_daily = _pkg_ns()._transco_z6_daily(None).get(year, {})
    # AGT's own measured daily-price ceiling across the full print record — the
    # physical bound the Transco-shape fallback is capped at (see below).
    agt_price_ceiling = max(
        (p for yr in all_agt.values() for mo in yr.values() for p in mo.values()),
        default=float("inf"),
    )
    T = config.hours
    out = np.full(T, np.nan, dtype=float)
    hour = 0
    for m in range(12):
        n_days = _DAYS_IN_MONTH[m]
        month_hours = n_days * 24
        hh_m = henry_hub.get((year, m + 1))
        b_m = basis[m]
        if hh_m is not None and not np.isnan(b_m) and hour < T:
            # Daily Henry Hub leg, re-centred to the measured monthly mean so
            # the hub leg contributes exactly hh_m to the monthly mean.
            quotes = hh_daily.get(m + 1)
            if quotes:
                arr = np.asarray(quotes, dtype=float)
                day_hh = np.interp(
                    np.linspace(0.0, 1.0, n_days),
                    np.linspace(0.0, 1.0, len(arr)),
                    arr,
                )
                dm = float(day_hh.mean())
                day_hh = day_hh * (hh_m / dm) if dm > 0 else np.full(n_days, hh_m)
            else:
                day_hh = np.full(n_days, hh_m)
            # Daily AGT basis leg, built from real measured gas data and
            # mean-preserved to the measured monthly basis b_m (additive shift),
            # only in positive-basis winter-blowout months; shoulder months stay
            # flat. Priority: real AGT prints (interpolated on their true calendar
            # days) -> measured Transco Z6 NY daily-basis shape -> flat.
            month_prints = agt_prints.get(m + 1, {})
            day_basis = np.full(n_days, b_m)
            if b_m > 0 and len(month_prints) >= 2:
                # Real AGT spot -> same-day basis, interpolated across the month.
                days = np.array(sorted(month_prints), dtype=float)
                pb = np.array([month_prints[int(d)] - day_hh[int(d) - 1] for d in days])
                shape = np.interp(np.arange(n_days), days - 1.0, pb)
                day_basis = shape + (b_m - float(shape.mean()))
            elif b_m > 0 and transco_daily.get(m + 1):
                # Sparse-print month: borrow the measured Transco daily-basis
                # within-month shape (AGT basis ~= Transco basis, slope ~0.95).
                # Cap the borrowed basis at AGT's own measured price ceiling: on
                # the most extreme days NY (Transco) is more pipeline-constrained
                # than Boston (AGT) — e.g. Transco hit $97.9 in the Jan-2025 polar
                # vortex while AGT spot never exceeds ~$30 — so an uncapped shape
                # borrow would over-amplify the AGT peak. Cap before the mean
                # shift so the monthly mean stays exactly b_m. Never below b_m.
                tq = np.asarray(transco_daily[m + 1], dtype=float)
                tx_day = np.interp(
                    np.linspace(0.0, 1.0, n_days),
                    np.linspace(0.0, 1.0, len(tq)),
                    tq,
                )
                tx_basis = tx_day - day_hh
                cap = np.maximum(agt_price_ceiling - day_hh, b_m)
                tx_basis = np.minimum(tx_basis, cap)
                day_basis = tx_basis + (b_m - float(tx_basis.mean()))
            day_hub = day_hh + day_basis  # monthly mean == hh_m + b_m
            shaped = np.repeat(day_hub, 24)[: max(0, T - hour)]
            out[hour : hour + len(shaped)] = shaped
        hour += month_hours
    if np.isnan(out).all():
        return None
    return out


def apply_hub_basis_overlay(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    basis_path: Path | None = None,
) -> None:
    """Reprice gas units at the measured hub-month spot in covered months.

    Doc-08 NEISO design decision 1: in a pipeline-constrained ISO the
    marginal gas unit prices off the constrained trading hub (Algonquin
    Citygate), whose winter spot blows out far above plant-average EIA-923
    receipts — the opportunity cost of gas in hand is the spot price it
    could be resold at, so the dispatch-relevant marginal fuel cost is the
    hub price for *every* gas unit, contracted or not. For each month with
    a measured hub basis row (:func:`iso_hub_monthly_gas_prices`), every
    gas generator's fuel price is **replaced** by the hub-month price,
    superseding both the ISO-month EIA-923 series and the per-plant F923
    overwrite — deliberate for NEISO, where only two plants report
    Schedule-5 gas receipts (partly LNG-priced) and the hub index is the
    far better measurement. Months without a basis row keep whatever the
    earlier passes set. Runs *before* :func:`apply_dual_fuel_pricing`, so
    dual-fuel units still cap the blown-out winter hub price at oil parity.

    Gated on ``config.gas_hub_basis_overlay`` (off by default; the
    calibration harness enables it for NEISO), so ERCOT/PJM/CAISO and all
    forecasts are unchanged. When ``config.gas_hub_basis_daily`` is also set
    the covered-month price is the daily-resolved AGT series
    (:func:`iso_hub_daily_gas_prices`) — the flat monthly plateau replaced by
    the cold-day blowout that trips the dual-fuel switch — falling back to the
    flat monthly hub when the daily series is unavailable. Backcast-only by
    construction: forward years have no basis rows. Mutates ``fuel_prices`` in
    place; idempotent.

    Args:
        fuel_prices: The ``(n_gen, T)`` delivered fuel-price array, updated
            in place for gas generators in covered months.
        fleet: Vectorized fleet attributes; ``fuel_type_idx`` selects gas.
        config: Scenario configuration supplying ``gas_hub_basis_overlay``,
            ``gas_hub_basis_daily``, ``iso`` and ``hours``.
        year: Calendar year keying the hub-basis lookup.
        basis_path: Optional override for the basis CSV path.
    """
    if not getattr(config, "gas_hub_basis_overlay", False):
        return
    hourly: np.ndarray | None = None
    daily = False
    if (
        getattr(config, "caiso_citygate_spot_level", False)
        and config.iso.upper() == "CAISO"
    ):
        # caiso-84: level the overlay on the measured daily citygate SPOT series
        # itself (both level and shape), not the N3050CA3 survey (see
        # _caiso_hub_daily_gas_prices spot_level / caiso_citygate_spot_level).
        hourly = _caiso_hub_daily_gas_prices(
            config,
            year,
            basis_path,
            spot_level=True,
            spot_coverage=bool(getattr(config, "caiso_citygate_spot_coverage", False)),
        )
        daily = hourly is not None
    elif getattr(config, "gas_hub_basis_daily", False):
        hourly = iso_hub_daily_gas_prices(config, year, basis_path)
        daily = hourly is not None
    if hourly is None:
        monthly = _pkg_ns().iso_hub_monthly_gas_prices(config, year, basis_path)
        if monthly is None:
            return
        hourly = _expand_monthly_to_hourly(monthly, fuel_prices.shape[1])
    covered = ~np.isnan(hourly)
    if not covered.any():
        return
    # CAISO: the basis rows are the SoCal / PG&E *citygate* (border) spot; a CA
    # power plant pays the citygate PLUS the LDC intrastate backbone/transmission
    # to its burner tip, so the marginal CC's true delivered (cost-based-bid)
    # fuel cost is citygate + that transport. Reconcile up to the measured CA
    # delivered-to-electric-power census (EIA N3045CA3) with the measured
    # citygate->plant differential (rule #11; see CAISO_CITYGATE_TRANSPORT_ADDER).
    # NEISO (the AGT marginal-unit hub) and every other ISO are unchanged.
    if config.iso.upper() == "CAISO":
        hourly = np.where(covered, hourly + CAISO_CITYGATE_TRANSPORT_ADDER, hourly)
    gas_rows = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX))[0]
    if gas_rows.size == 0:
        return
    fuel_prices[np.ix_(gas_rows, np.nonzero(covered)[0])] = hourly[covered]
    month_of_hour = _month_index(hourly.size)
    covered_months = int(np.unique(month_of_hour[covered]).size)
    logger.info(
        "hub-basis overlay (%s %d, %s): %d gas generators repriced at the "
        "measured hub spot in %d/12 months (winter max %.2f $/MMBtu)",
        config.iso,
        year,
        "daily" if daily else "monthly",
        gas_rows.size,
        covered_months,
        float(np.nanmax(hourly)),
    )


def _hub_overlay_series(
    series: np.ndarray, config: ScenarioConfig, year: int, hours: int
) -> np.ndarray:
    """Return ``series`` with covered months replaced by the hub-month spot.

    The single-series analogue of :func:`apply_hub_basis_overlay`, used by
    :func:`_gas_series` so gas-keyed coal passthrough sigmoids see the same
    delivered gas price the merit order sees. No-op unless
    ``config.gas_hub_basis_overlay`` is set and basis rows exist.
    """
    if not getattr(config, "gas_hub_basis_overlay", False):
        return series
    monthly = _pkg_ns().iso_hub_monthly_gas_prices(config, year)
    if monthly is None:
        return series
    hourly = _expand_monthly_to_hourly(monthly, hours)
    return np.where(np.isnan(hourly), series, hourly)
