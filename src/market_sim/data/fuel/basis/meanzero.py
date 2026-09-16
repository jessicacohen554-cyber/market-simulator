"""Shared capacity-weighted mean-zero zonal gas-basis core (PJM/MISO/CAISO).

The generic per-zone hub-table loader and the mean-zero applier those three
ISOs delegate to, plus their hub-table path constants. Rule 25: the shared
core carries NO tuned values — every fitted/measured per-ISO number lives in
the ISO's own CSV (``{pjm,miso,caiso}_zonal_gas_hub.csv``) and is applied only
under that ISO's own config gate. Split out of ``data/fuel.py`` (W-D3) as pure
code motion.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays

from .._shared import (
    _FUEL_ZONAL_HUB_DATATYPE,
    _GAS_FUEL_IDX,
    _GAS_PRICE_FLOOR,
    _clean_zonal_hub_frame,
    _use_clean_data,
    logger,
)


# PJM per-zone delivered-gas basis vs Henry Hub ($/MMBtu) by year. PJM clears as
# a single copper-plate because every gas unit is priced off one ISO-wide
# delivered series, so no zone ever wants cheap power from another and the
# internal TTCs never bind. In reality the western coal belt (ComEd on Chicago
# Citygate, AEP_Ohio / ATSI on Appalachian/Dominion-South, West_APS on
# Appalachian, Central_PA on Marcellus/TETCO-M3) buys gas ~$0.3-0.6/MMBtu BELOW
# Henry Hub, while the eastern/southeastern load pockets (Dominion on Transco
# Z6/TETCO M3, SWMAAC on Transco Z6, EMAAC on Transco Z6 non-NY) pay a persistent
# premium. The per-zone basis is the EIA "natural gas delivered to electric power
# consumers" price by the zone's primary state (series N3045<ST>3M, $/Mcf monthly
# -> $/MMBtu annual mean) minus the annual-mean Henry Hub — a measured,
# forward-reproducible power-plant delivered cost that regenerates every year and
# tracks changing regional supply. Like the ERCOT table (and unlike NYISO) this
# is anchored to a gas-capacity-weighted mean of zero in
# :func:`apply_pjm_zonal_gas_basis`, so the calibrated PJM fleet-aggregate gas
# level is preserved and ONLY the cross-zonal spread opens. Consumed by
# :func:`apply_pjm_zonal_gas_basis`.
PJM_ZONAL_GAS_HUB_PATH: Path = RAW_DATA_DIR / "pjm_zonal_gas_hub.csv"


# MISO per-zone delivered-gas basis vs Henry Hub ($/MMBtu) by year. MISO's six
# zones sit on three pipeline-hub regions: MISO-West/MISO-Plains on MidCon /
# Northern Natural (IA proxy, EIA N3045IA3), MISO-Illinois/MISO-Indiana/
# MISO-East on Chicago Citygate (IL, N3045IL3 — per-state IN/MichCon series
# are a pending refinement, see the CSV source notes), MISO-South on the
# Gulf Coast (LA, N3045LA3). Like PJM (and unlike NYISO) this
# is anchored to a gas-capacity-weighted mean of zero in
# :func:`apply_miso_zonal_gas_basis`, so the calibrated MISO fleet-aggregate gas
# level is preserved and ONLY the cross-zonal spread opens. Consumed by
# :func:`apply_miso_zonal_gas_basis`.
MISO_ZONAL_GAS_HUB_PATH: Path = RAW_DATA_DIR / "miso_zonal_gas_hub.csv"


# CAISO per-zone gas-hub basis vs Henry Hub ($/MMBtu) by year. CAISO's zones
# buy from two LDC systems with separately traded citygate hubs: NP15/ZP26 on
# **PG&E Citygate** (the PG&E backbone serves both the Bay Area and the San
# Joaquin Valley between Paths 15 and 26) and SP15 on **SoCal Citygate**
# (SoCalGas/SDG&E). The committed rows are month-balanced annual means of the
# EIA NG Weekly Update archive's weekly Wednesday prints (NGI Daily GPI;
# scripts/data/fetch_pge_socal_citygate_daily.py + derive_caiso_zonal_gas_hub.py),
# the same free published print the ERCOT Waha rows cite. Measured N-S spread
# (PG&E − SoCal): −0.49 (2023) / +0.54 (2024) / −0.18 (2025) $/MMBtu — real but
# year-varying, so it enters as data, never as a fitted north-premium knob.
# Like PJM/MISO/ERCOT this is anchored to a gas-capacity-weighted mean of zero
# in :func:`apply_caiso_zonal_gas_basis`, so the calibrated CAISO aggregate gas
# level (CA-composite citygate + transport) is preserved and ONLY the measured
# cross-zonal spread opens. Consumed by :func:`apply_caiso_zonal_gas_basis`.
CAISO_ZONAL_GAS_HUB_PATH: Path = RAW_DATA_DIR / "caiso_zonal_gas_hub.csv"


# SPP per-zone delivered-gas basis vs Henry Hub ($/MMBtu) by year. SPP's two
# zones straddle the Mid-Continent gas complex: SPP-North on NGPL
# Mid-Continent / Panhandle Eastern (KS proxy, EIA N3045KS3 — the plurality
# 30.1% of the zone's gas fleet, the only North state EIA publishes) and
# SPP-South on ANR Oklahoma / Panhandle Eastern (OK proxy, N3045OK3 — an
# outright 59.0% majority of that zone's gas fleet). Built by lane SPP-32 the
# same way every sibling table here is: the EIA delivered-to-electric-power
# state series minus the Henry Hub monthly mean, averaged over the year's 12
# monthly prints.
#
# Two properties a consumer must know, both recorded in full in
# ``data/raw/spp_zonal_gas_hub.SOURCES.md``:
#   * The committed span is **2022-2024**, not 2023-2025. N3045OK3 is an
#     intermittent series that EIA does not print for 2025, and the table stops
#     at the intersection of the two zones' published years ON PURPOSE — a
#     North-only 2025 row would let SPP-South default to a 0.0 basis and
#     manufacture a ~$0.7/MMBtu spread out of a publication gap. With no 2025
#     row the lookup returns ``None`` and an applier no-ops visibly instead.
#   * The 2025 hole is NOT filled by blending TX/NM into SPP-South: measured,
#     TX+NM sits $0.43 (2023) and $1.10 (2024) /MMBtu away from OK, so
#     renormalising would swing the South basis $1.34/MMBtu between 2024 and
#     2025 on publication availability alone (rule 14 ``[R-ACCURATE]``).
#
# NO APPLIER IS ARMED FOR SPP. This is a registered path and a measured table,
# not a mechanism: lane SPP-32 adds no ``ScenarioConfig`` field (plan §7 gate
# G8), so nothing reads this yet and no keeper's cache key moves. Arming it is
# SPP-40's / SPP-52's call, and it needs the 2025 question answered first.
SPP_ZONAL_GAS_HUB_PATH: Path = RAW_DATA_DIR / "spp_zonal_gas_hub.csv"


# SOCO per-zone delivered-gas basis vs Henry Hub ($/MMBtu) by year, 2023-2025.
# Built by lane SOCO-32 from the COMMITTED per-plant EIA-923 Schedule 2 series
# (``scripts/data/derive_soco_zonal_gas_hub.py``, the NWPP-33 construction),
# quantity-weighted across each zone's own plants within a month and
# month-balanced over the year — not from a state proxy, and for two measured
# reasons that are in ``data/raw/soco_zonal_gas_hub.SOURCES.md`` in full:
#
#   * card S3's zone map puts the six SERC FLORIDA-panhandle plants in
#     ``SOCO_AL``, and the two of them that burn gas are 20-25 % of that zone's
#     burn at a ~$1.10/MMBtu premium over the Alabama plants — a delivered
#     market an Alabama state series cannot see at all (rule 14
#     ``[R-ACCURATE]``'s "defined on a different boundary than our zones");
#   * EIA publishes the state series for neither GA nor MS after 2024-12, so a
#     state-series table would end mid-backcast and either leave 2025 basis-less
#     or let two zones default to 0.0 and fabricate a spread out of a
#     publication gap (the trap SPP-32 refused above).
#
# Where the zone boundary IS the state line the two routes agree to
# <= 0.044 $/MMBtu (GA, MS), which is the evidence the route is sound.
#
# There is no traded Southeast index to use instead: SOCO-12 swept both free EIA
# routes and returned a documented NO (no Southeast row in the Weekly Update
# spot table, no Southeast region on the daily map), so the table's ``hub``
# column names the transport system (Southern Natural Gas / Transco Zone 4) and
# the VALUE is the measured delivered price, never a quote.
#
# NO APPLIER IS ARMED FOR SOCO. This is a registered path and a measured table,
# not a mechanism: lane SOCO-32 adds no ``ScenarioConfig`` field (plan §7 gate
# G8), so nothing reads this yet and no keeper's cache key moves. Arming it is
# SOCO-40's or a later lever's call. Note for whoever does: SOCO's zones are
# whole states, so unlike every sibling table this one is NOT a proxy — and its
# measured mean-zero spread is 0.789 / 0.467 / 0.537 $/MMBtu.
SOCO_ZONAL_GAS_HUB_PATH: Path = RAW_DATA_DIR / "soco_zonal_gas_hub.csv"


_ZONAL_HUB_ISO_CLEAN_CACHE: dict[str, pd.DataFrame | None] = {}


_ZONAL_HUB_CACHE: dict[Path, pd.DataFrame | None] = {}


def _load_zonal_gas_hub(path: Path) -> pd.DataFrame | None:
    """Load a per-zone annual gas-basis table, or ``None`` if absent."""
    if _use_clean_data():
        from scripts.lib.clean_io import clean_exists

        iso_key: str | None = None
        if path == PJM_ZONAL_GAS_HUB_PATH:
            iso_key = "PJM"
        elif path == MISO_ZONAL_GAS_HUB_PATH:
            iso_key = "MISO"
        if iso_key is not None and clean_exists(_FUEL_ZONAL_HUB_DATATYPE, iso=iso_key):
            if iso_key not in _ZONAL_HUB_ISO_CLEAN_CACHE:
                _ZONAL_HUB_ISO_CLEAN_CACHE[iso_key] = _clean_zonal_hub_frame(iso_key)
            return _ZONAL_HUB_ISO_CLEAN_CACHE[iso_key]
    if path in _ZONAL_HUB_CACHE:
        return _ZONAL_HUB_CACHE[path]
    frame: pd.DataFrame | None = None
    if path.exists():
        loaded = pd.read_csv(path)
        if not loaded.empty:
            frame = loaded
    _ZONAL_HUB_CACHE[path] = frame
    return frame


def _zonal_gas_basis_by_zone(path: Path, year: int) -> dict[str, float] | None:
    """Return ``{zone: basis vs Henry Hub ($/MMBtu)}`` from a hub CSV, or None."""
    frame = _load_zonal_gas_hub(path)
    if frame is None:
        return None
    sub = frame[frame["year"] == year]
    if sub.empty:
        return None
    return {str(r.zone): float(r.basis_vs_hh_usd_mmbtu) for r in sub.itertuples()}


def _apply_meanzero_zonal_gas_basis(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    *,
    iso: str,
    config_field: str,
    hub_path: Path,
    path_override: Path | None = None,
    skip_cells: np.ndarray | None = None,
) -> None:
    """Shared core for mean-zero capacity-weighted zonal gas basis (PJM / MISO).

    Adds each zone's measured basis spread (EIA delivered-to-electric-power minus
    Henry Hub) to every gas unit's delivered price, after subtracting the
    gas-capacity-weighted mean so the calibrated fleet-aggregate level is
    preserved and only the cross-zonal shape moves. Floored at
    :data:`_GAS_PRICE_FLOOR` so a deep negative basis cannot drive fuel cost
    below zero. Gated on ``config.<config_field>`` and ``config.iso == iso``.

    ``skip_cells`` (miso-213, rule 19 ``[R-ONE-MECH]``): an optional
    ``(n_gen, T)`` boolean mask of cells whose delivered price was SET by the
    EIA-923 print path (:func:`~..plant_prices.apply_plant_monthly_fuel_prices`
    returns it). A print already embeds the regional delivered premium the
    N3045 state series measures, so on those cells the spread is NOT added
    and the cell is left byte-untouched (no floor either). The
    capacity-weighted mean is still computed over ALL gas rows, so the zonal
    spread VALUES are unchanged by the mask — only the set of recipient cells
    changes. ``None`` (every caller today except the MISO applier under
    ``miso_zonal_gas_basis_skip_923_priced``) is the historical behaviour.
    """
    if not getattr(config, config_field, False):
        return
    if config.iso != iso:
        return
    path = path_override if path_override else hub_path
    basis = _zonal_gas_basis_by_zone(path, year)
    if basis is None:
        return
    # CAISO FSNO sub-zonal partition (caiso-224): FSNO is carved from NP15
    # inside PG&E citygate territory, so it inherits NP15's measured basis —
    # the precommit §3 parent-inheritance rule. Without this alias the
    # zone_names loop below would silently hand FSNO gas a 0.0 basis (~$4/
    # MMBtu below citygate). Inert when FSNO is not in the topology.
    if iso == "CAISO" and "FSNO" not in basis:
        basis["FSNO"] = basis.get("NP15", 0.0)
    from market_sim.config.iso_configs import get_iso_config

    zone_names = get_iso_config(config.iso).zone_names
    gas_rows = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX))[0]
    if gas_rows.size == 0:
        return
    basis_by_zone_idx = np.array(
        [basis.get(name, 0.0) for name in zone_names], dtype=float
    )
    gen_basis = basis_by_zone_idx[fleet.zone_idx[gas_rows]]
    weights = fleet.pmax[gas_rows]
    total_w = float(weights.sum())
    weighted_mean = float((gen_basis * weights).sum() / total_w) if total_w else 0.0
    zone_spread = gen_basis - weighted_mean
    floored = np.maximum(
        fuel_prices[gas_rows, :] + zone_spread[:, np.newaxis], _GAS_PRICE_FLOOR
    )
    skipped_share = 0.0
    if skip_cells is not None:
        keep = np.asarray(skip_cells, dtype=bool)[gas_rows, :]
        skipped_share = float(keep.mean()) if keep.size else 0.0
        floored = np.where(keep, fuel_prices[gas_rows, :], floored)
    fuel_prices[gas_rows, :] = floored
    logger.info(
        "%s zonal gas basis (%d): %d gas units; cap-weighted mean %+.2f removed, "
        "zonal spread %.2f..%.2f $/MMBtu; %.1f%% of gas cells skipped as "
        "print-derived",
        iso,
        year,
        gas_rows.size,
        weighted_mean,
        float(zone_spread.min()),
        float(zone_spread.max()),
        100.0 * skipped_share,
    )
