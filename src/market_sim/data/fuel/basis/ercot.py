"""ERCOT zonal gas basis: Waha/regional hub spreads, the measured TX
electric-power level anchor, the EIA-923 contract/spot haircut, and the West
net-load two-regime gas shape.

Split out of ``data/fuel.py`` (W-D3; refactor-consolidation plan §5 item 3) as
pure code motion. Rule 25: every value here is ERCOT's own (measured EIA
series, the ERCOT hub CSV, cited Waha delivered floors) — nothing merges into
a generic default. ``_henry_hub_monthly`` and ``ercot_gas_spot_share_by_plant``
are resolved through the package namespace at call time
(:func:`.._shared._pkg_ns`): tests patch the former and attribute-write the
latter on the facade.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays

from .._shared import (
    _FUEL_ERCOT_EP_GAS_DATATYPE,
    _FUEL_TAKEORPAY_DATATYPE,
    _FUEL_ZONAL_HUB_DATATYPE,
    _GAS_FUEL_IDX,
    _GAS_PRICE_FLOOR,
    _clean_zonal_hub_frame,
    _pkg_ns,
    _use_clean_data,
    logger,
)


# ERCOT per-zone delivered-gas basis vs Henry Hub ($/MMBtu) by year. West /
# Panhandle price off Waha (the takeaway-constrained Permian discount),
# North / Northeast off the North/East-Texas complex (~Henry Hub, measured from
# EIA-923 Schedule-5 receipts), Houston off the Houston Ship Channel (~HH), and
# South_Central / South off the South-Texas hubs (a modest HH premium, also
# EIA-923-measured). Unlike the NYISO table this is anchored to a
# gas-capacity-weighted mean of zero (not a single reference zone), so the
# calibrated ERCOT fleet-aggregate gas level is preserved and only the
# cross-zonal split moves. Consumed by :func:`apply_ercot_zonal_gas_basis`.
ERCOT_ZONAL_GAS_HUB_PATH: Path = RAW_DATA_DIR / "ercot_zonal_gas_hub.csv"


# Measured EIA price of natural gas delivered to TX electric-power consumers
# (series N3045TX3, $/Mcf monthly). This is the gen-weighted ERCOT-wide delivered
# gas level — the *power-plant* delivered cost, NOT the TX city-gate price
# (N3050TX3), which carries the LDC distribution margin (~+$1.3/MMBtu over Henry
# Hub) that generators do not pay. Used by :func:`ercot_electric_power_gas_basis`
# to anchor the zonal-basis level on measured data instead of the flat -0.50
# scalar; the EIA-923 per-zone receipts then supply only the (mean-zero) spread.
ERCOT_ELECTRIC_POWER_GAS_PATH: Path = (
    RAW_DATA_DIR / "ercot_electric_power_gas_price.csv"
)

# Per-plant natural-gas contract/spot share from EIA-923 Schedule-5 Purchase Type
# (written by scripts/data/derive_gas_takeorpay.py). Used by
# :func:`ercot_gas_spot_share_by_zone` to re-ground the West/Waha delivered-gas
# floor depth on a MEASURED spot fraction (the firm-contracted gas is insulated
# from the Waha hub collapse) instead of the cited -0.50 scalar floor.
ERCOT_GAS_TAKEORPAY_PATH: Path = (
    RAW_DATA_DIR / "_processed-legacy" / "gas_takeorpay_ERCOT.csv"
)
# Authoritative ERCOT thermal plant -> model-zone map (the hard-coded ERCOT_Zone
# column on the CAMPD bin sheet), used to aggregate the per-plant gas spot share
# to model zones.
ERCOT_BIN_ASSIGNMENTS_PATH: Path = (
    RAW_DATA_DIR / "reference" / "custom-bin-assignments.csv"
)


# EIA natural-gas heat content: 1 Mcf ~= 1.036 MMBtu (2023 avg, ~1,036 Btu/cf).
# Converts the $/Mcf delivered series to the $/MMBtu the merit order prices in.
_MCF_TO_MMBTU: float = 1.036


_ERCOT_ZONAL_HUB_CLEAN_CACHE: dict[str, pd.DataFrame | None] = {}
_ERCOT_EP_GAS_CLEAN_CACHE: dict[str, pd.DataFrame | None] = {}
_ERCOT_GAS_SPOT_PLANT_CLEAN_CACHE: dict[str, dict[int, float] | None] = {}
_ERCOT_GAS_SPOT_ZONE_CLEAN_CACHE: dict[str, dict[str, float] | None] = {}


def _clean_ercot_ep_gas_frame() -> pd.DataFrame | None:
    """TX electric-power gas price frame from the clean ``fuel-ercot-ep-gas`` tree."""
    from scripts.lib.clean_io import read_clean

    df = read_clean(_FUEL_ERCOT_EP_GAS_DATATYPE, validate=False)
    return df if not df.empty else None


def _clean_takeorpay_plant_dict() -> dict[int, float] | None:
    """Per-plant gas spot share from the clean ``fuel-takeorpay`` tree.

    Returns the same ``{plant_code: spot_share}`` dict as the raw CSV path.
    """
    from scripts.lib.clean_io import read_clean

    df = read_clean(
        _FUEL_TAKEORPAY_DATATYPE,
        validate=False,
        columns=["plant_code", "spot_share"],
    )
    if df.empty:
        return None
    result = {int(pc): float(s) for pc, s in zip(df["plant_code"], df["spot_share"])}
    return result or None


_ERCOT_ZONAL_HUB_CACHE: dict[Path, pd.DataFrame | None] = {}


def _load_ercot_zonal_gas_hub(path: Path | None) -> pd.DataFrame | None:
    """Load the ERCOT per-zone annual gas-basis table, or ``None`` if absent."""
    if path is None and _use_clean_data():
        from scripts.lib.clean_io import clean_exists

        if clean_exists(_FUEL_ZONAL_HUB_DATATYPE, iso="ERCOT"):
            if "_clean" not in _ERCOT_ZONAL_HUB_CLEAN_CACHE:
                _ERCOT_ZONAL_HUB_CLEAN_CACHE["_clean"] = _clean_zonal_hub_frame("ERCOT")
            return _ERCOT_ZONAL_HUB_CLEAN_CACHE["_clean"]
    resolved = Path(path) if path else ERCOT_ZONAL_GAS_HUB_PATH
    if resolved in _ERCOT_ZONAL_HUB_CACHE:
        return _ERCOT_ZONAL_HUB_CACHE[resolved]
    frame: pd.DataFrame | None = None
    if resolved.exists():
        loaded = pd.read_csv(resolved)
        if not loaded.empty:
            frame = loaded
    _ERCOT_ZONAL_HUB_CACHE[resolved] = frame
    return frame


def ercot_zonal_gas_basis_by_zone(
    year: int, path: Path | None = None
) -> dict[str, float] | None:
    """Return ``{zone: basis vs Henry Hub ($/MMBtu)}`` for ERCOT, or None.

    The raw measured per-zone basis (West/Panhandle on Waha, North/Northeast on
    the North/East-Texas complex, Houston on the Houston Ship Channel,
    South_Central/South on the South-Texas hubs;
    :data:`ERCOT_ZONAL_GAS_HUB_PATH`). The mean-zero re-centring that preserves
    the calibrated fleet-aggregate level is done in
    :func:`apply_ercot_zonal_gas_basis`, which weights by each zone's gas
    capacity. Returns ``None`` when the table is missing or has no rows for
    ``year`` (e.g. a forward year).
    """
    frame = _load_ercot_zonal_gas_hub(path)
    if frame is None:
        return None
    sub = frame[frame["year"] == year]
    if sub.empty:
        return None
    return {str(r.zone): float(r.basis_vs_hh_usd_mmbtu) for r in sub.itertuples()}


def ercot_waha_collapse_freq(year: int, path: Path | None = None) -> float | None:
    """Return the measured Waha negative-price-day frequency for ``year``, or None.

    The fraction of the year the Waha *hub* spot price was negative (the deep
    take-away-constrained collapse), read from the ``neg_day_freq`` column of
    :data:`ERCOT_ZONAL_GAS_HUB_PATH` (West row). This is the measured collapse
    frequency that splits the net-load distribution into a *collapsed* (lowest
    net-load) regime and a *firm* (highest net-load) regime in
    :func:`apply_ercot_west_netload_gas_shape`. 2024 is EIA-authoritative (42% of
    trading days, Today-in-Energy id=64445); 2023/2025 are NGI/Reuters annual
    negative-day counts (see ``neg_day_freq_source``). Returns ``None`` when the
    table, the West row, or the column is missing (e.g. a forward year), so the
    caller can fall back to its default.
    """
    frame = _load_ercot_zonal_gas_hub(path)
    if frame is None or "neg_day_freq" not in frame.columns:
        return None
    sub = frame[(frame["year"] == year) & (frame["zone"] == "West")]
    if sub.empty:
        return None
    val = sub["neg_day_freq"].iloc[0]
    if pd.isna(val):
        return None
    return float(val)


_ERCOT_EP_GAS_CACHE: dict[Path, pd.DataFrame | None] = {}


def _load_ercot_electric_power_gas(path: Path | None) -> pd.DataFrame | None:
    """Load the measured TX delivered-to-electric-power gas table, or None."""
    if path is None and _use_clean_data():
        from scripts.lib.clean_io import clean_exists

        if clean_exists(_FUEL_ERCOT_EP_GAS_DATATYPE):
            if "_clean" not in _ERCOT_EP_GAS_CLEAN_CACHE:
                _ERCOT_EP_GAS_CLEAN_CACHE["_clean"] = _clean_ercot_ep_gas_frame()
            return _ERCOT_EP_GAS_CLEAN_CACHE["_clean"]
    resolved = Path(path) if path else ERCOT_ELECTRIC_POWER_GAS_PATH
    if resolved in _ERCOT_EP_GAS_CACHE:
        return _ERCOT_EP_GAS_CACHE[resolved]
    frame: pd.DataFrame | None = None
    if resolved.exists():
        loaded = pd.read_csv(resolved)
        if not loaded.empty:
            frame = loaded
    _ERCOT_EP_GAS_CACHE[resolved] = frame
    return frame


def ercot_electric_power_gas_basis(
    year: int, path: Path | None = None, henry_hub_path: Path | None = None
) -> float | None:
    """Return the measured TX delivered-to-electric-power gas basis vs Henry Hub.

    The annual mean of the EIA price of gas delivered to TX electric-power
    consumers (series N3045TX3, :data:`ERCOT_ELECTRIC_POWER_GAS_PATH`, converted
    $/Mcf -> $/MMBtu) minus the annual-mean measured Henry Hub
    (:func:`_henry_hub_monthly`). This is the gen-weighted ERCOT-wide *power-plant*
    delivered gas level, used by :func:`apply_ercot_zonal_gas_basis` to anchor the
    zonal basis on measured data instead of the flat ``-0.50`` scalar. Returns
    ``None`` when either series is missing for ``year`` (e.g. a forward year), so
    the caller falls back to the scalar-anchored mean-zero behaviour.
    """
    frame = _load_ercot_electric_power_gas(path)
    if frame is None:
        return None
    sub = frame[frame["year"] == year]
    if sub.empty:
        return None
    ep_mmbtu = float((sub["price_usd_mcf"] / _MCF_TO_MMBTU).mean())
    hh = _pkg_ns()._henry_hub_monthly(henry_hub_path)
    hh_months = [hh[(year, m)] for m in range(1, 13) if (year, m) in hh]
    if not hh_months:
        return None
    return ep_mmbtu - float(np.mean(hh_months))


_ERCOT_GAS_SPOT_CACHE: dict[tuple[Path, Path], dict[str, float] | None] = {}
_ERCOT_GAS_SPOT_PLANT_CACHE: dict[Path, dict[int, float] | None] = {}


def ercot_gas_spot_share_by_plant(
    takeorpay_path: Path | None = None,
) -> dict[int, float] | None:
    """Return ``{plant_code: gas spot share}`` for ERCOT, or ``None`` if absent.

    The per-plant counterpart to :func:`ercot_gas_spot_share_by_zone`: it returns
    each reporting gas plant's own EIA-923 Schedule-5 spot share, untouched by any
    zonal aggregation. The haircut applies a unit's *own* measured share, so a
    plant that buys 100% spot keeps the full Waha hub discount (share 1.0) while a
    100%-contract plant loses it entirely (share 0.0) — unlike the zone average,
    which would smear one number across both. Plants that file no classifiable gas
    receipt are simply absent here, so the caller defaults them to ``1.0`` (full
    spot exposure, the conservative no-haircut default that matches the deriver's
    "no classifiable Purchase Type -> treated as fully spot"). Returns ``None``
    when the receipt table is missing (f923 not extracted, or a forward year).
    """
    if takeorpay_path is None and _use_clean_data():
        from scripts.lib.clean_io import clean_exists

        if clean_exists(_FUEL_TAKEORPAY_DATATYPE):
            if "_clean" not in _ERCOT_GAS_SPOT_PLANT_CLEAN_CACHE:
                _ERCOT_GAS_SPOT_PLANT_CLEAN_CACHE["_clean"] = (
                    _clean_takeorpay_plant_dict()
                )
            return _ERCOT_GAS_SPOT_PLANT_CLEAN_CACHE["_clean"]
    tp = Path(takeorpay_path) if takeorpay_path else ERCOT_GAS_TAKEORPAY_PATH
    if tp in _ERCOT_GAS_SPOT_PLANT_CACHE:
        return _ERCOT_GAS_SPOT_PLANT_CACHE[tp]
    result: dict[int, float] | None = None
    if tp.exists():
        top = pd.read_csv(tp)
        if not top.empty:
            result = {
                int(pc): float(s) for pc, s in zip(top["plant_code"], top["spot_share"])
            } or None
    _ERCOT_GAS_SPOT_PLANT_CACHE[tp] = result
    return result


def ercot_gas_spot_share_by_zone(
    takeorpay_path: Path | None = None,
    bin_path: Path | None = None,
) -> dict[str, float] | None:
    """Return ``{model_zone: gas spot share}`` for ERCOT, or ``None`` if absent.

    Aggregates the per-plant EIA-923 gas spot share
    (:data:`ERCOT_GAS_TAKEORPAY_PATH`, written by ``scripts/data/derive_gas_takeorpay``)
    to model zones using the CAMPD bin sheet's hard-coded ``ERCOT_Zone`` column
    (:data:`ERCOT_BIN_ASSIGNMENTS_PATH`), MMBtu-weighted across each zone's
    reporting gas plants. Zones with no reporting plant are omitted, so the caller
    leaves their hub basis unchanged (the conservative default — no haircut). The
    spot share is the avoidable fraction that sees the Waha hub collapse; the
    complement is firm-contracted and insulated. Returns ``None`` when the receipt
    table is missing (e.g. f923 not extracted, or a forward year) so the caller
    falls back to the scalar floor / unhaircut behaviour.
    """
    if takeorpay_path is None and _use_clean_data():
        from scripts.lib.clean_io import clean_exists

        if clean_exists(_FUEL_TAKEORPAY_DATATYPE):
            from scripts.lib.clean_io import read_clean

            bp_path = Path(bin_path) if bin_path else ERCOT_BIN_ASSIGNMENTS_PATH
            cache_key = f"_clean_{bp_path}"
            if cache_key not in _ERCOT_GAS_SPOT_ZONE_CLEAN_CACHE:
                top = read_clean(_FUEL_TAKEORPAY_DATATYPE, validate=False)
                result_clean: dict[str, float] | None = None
                if not top.empty and bp_path.exists():
                    zmap = pd.read_csv(bp_path)[
                        ["Plant_Code", "ERCOT_Zone"]
                    ].drop_duplicates("Plant_Code")
                    merged = top.merge(
                        zmap, left_on="plant_code", right_on="Plant_Code", how="inner"
                    )
                    if not merged.empty:
                        w = merged["total_mmbtu"].clip(lower=0.0)
                        merged = merged.assign(_w=w, _sw=merged["spot_share"] * w)
                        agg = merged.groupby("ERCOT_Zone")[["_w", "_sw"]].sum()
                        agg = agg[agg["_w"] > 0]
                        result_clean = {
                            str(z): float(r._sw / r._w) for z, r in agg.iterrows()
                        } or None
                _ERCOT_GAS_SPOT_ZONE_CLEAN_CACHE[cache_key] = result_clean
            return _ERCOT_GAS_SPOT_ZONE_CLEAN_CACHE[cache_key]
    tp = Path(takeorpay_path) if takeorpay_path else ERCOT_GAS_TAKEORPAY_PATH
    bp = Path(bin_path) if bin_path else ERCOT_BIN_ASSIGNMENTS_PATH
    key = (tp, bp)
    if key in _ERCOT_GAS_SPOT_CACHE:
        return _ERCOT_GAS_SPOT_CACHE[key]
    result: dict[str, float] | None = None
    if tp.exists() and bp.exists():
        top = pd.read_csv(tp)
        zmap = pd.read_csv(bp)[["Plant_Code", "ERCOT_Zone"]].drop_duplicates(
            "Plant_Code"
        )
        if not top.empty:
            merged = top.merge(
                zmap, left_on="plant_code", right_on="Plant_Code", how="inner"
            )
            if not merged.empty:
                # MMBtu-weighted spot share per zone.
                w = merged["total_mmbtu"].clip(lower=0.0)
                merged = merged.assign(_w=w, _sw=merged["spot_share"] * w)
                agg = merged.groupby("ERCOT_Zone")[["_w", "_sw"]].sum()
                agg = agg[agg["_w"] > 0]
                result = {
                    str(z): float(r._sw / r._w) for z, r in agg.iterrows()
                } or None
    _ERCOT_GAS_SPOT_CACHE[key] = result
    return result


def apply_ercot_zonal_gas_basis(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
) -> None:
    """Shift each ERCOT gas unit's price by its zone's measured hub basis.

    ERCOT's model zones buy gas off structurally different regional hubs (Waha
    in the West/Panhandle, the North/East-Texas complex in North/Northeast, the
    Houston Ship Channel in Houston, the South-Texas hubs in
    South_Central/South). The single ERCOT scalar basis
    (:data:`~market_sim.config.constants.GAS_BASIS_DIFFERENTIAL`, the Waha
    discount applied fleet-wide) flattens this gradient, so the merit order
    prices DFW/North CCs on the same cheap gas as Permian CCs — over-running
    North/Northeast CCs and under-running West/Permian and South CCs.

    This shifts each gas unit by two measured pieces:

    1. a **level** correction from the flat ``-0.50`` scalar to the measured TX
       delivered-to-electric-power gas basis (:func:`ercot_electric_power_gas_basis`,
       EIA series N3045TX3 — the gen-weighted ERCOT-wide power-plant delivered
       cost; the ``-0.50`` Waha scalar runs ~$0.4-0.5/MMBtu too cheap in 2023/24),
       applied uniformly so it is a pure re-level, and
    2. a **mean-zero zonal spread** = each zone's EIA-923 basis
       (:func:`ercot_zonal_gas_basis_by_zone`) minus its gas-capacity-weighted
       mean, so the spread moves *only* the cross-zonal split and the EIA-923
       regulated-utility level bias (its receipts price ~$0.2/MMBtu above the
       measured electric-power average) is dropped — only its relative shape is kept.

    Net: every gas unit ends near ``Henry Hub + electric_power_basis +
    zone_spread``. When the electric-power series is unavailable (forward years)
    the level term is 0 and this degrades to the prior scalar-anchored mean-zero
    behaviour. The shift is floored at a small positive so a deep negative Waha
    basis cannot drive the delivered price below zero.

    When ``config.ercot_gas_delivered_floor_basis`` is set, the per-zone spread is
    additionally floored at that value (the cited measured Waha *delivered* basis,
    ``-0.50``) before the level correction: the raw West/Panhandle basis is a Waha
    *hub* basis (the takeaway-constrained wellhead price, negative ~42% of days),
    but a power plant pays *delivered* gas at the burner tip — intrastate transport
    + fuel retention + minimum commodity on top — so its delivered discount has a
    transport-grounded floor. Without it the West/Permian gas units offer ~$0/MWh
    and run baseload (the CT_PEAKER over-run); the measured TX
    delivered-to-electric-power level confirms no TX plant paid near $0 delivered.
    Runs after the F923
    plant-monthly overwrite and before :func:`apply_dual_fuel_pricing`, so oil
    parity still caps any winter spike.

    Gated on ``config.ercot_zonal_gas_basis`` and ``config.iso == "ERCOT"``
    (a default-off diagnostic; see the field docstring on ScenarioConfig), so
    every other ISO and all forecasts are byte-identical. Mutates ``fuel_prices``
    in place; idempotent given the same inputs.
    """
    if not getattr(config, "ercot_zonal_gas_basis", False):
        return
    if config.iso != "ERCOT":
        return
    basis = ercot_zonal_gas_basis_by_zone(year, path)
    if basis is None:
        return
    from market_sim.config.iso_configs import get_iso_config

    zone_names = get_iso_config(config.iso).zone_names
    gas_rows = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX))[0]
    if gas_rows.size == 0:
        return
    # Mean-zero zonal SPREAD: each zone's EIA-923 basis minus the gas-capacity-
    # weighted mean, so only the cross-zonal shape survives (the EIA-923
    # regulated-utility level bias is dropped). Zones absent from the table -> 0.
    basis_by_zone_idx = np.array(
        [basis.get(name, 0.0) for name in zone_names], dtype=float
    )
    # MEASURED CONTRACT HAIRCUT (re-grounds the floor depth, CLAUDE.md #11/#12):
    # only the SPOT-purchased fraction of a unit's gas sees the Waha hub collapse;
    # the firm-contracted fraction is priced off a term index and is insulated.
    # So scale each gas unit's hub basis by ITS OWN EIA-923-measured plant spot
    # share (the firm complement is priced at the fleet/firm level = 0 zonal
    # discount). Per-PLANT, not the zone average: a 100%-spot unit keeps the full
    # Waha discount (e.g. Permian Basin, Laredo) while a 100%-contract unit in the
    # same zone loses it entirely (Ector County) — the zone mean would smear one
    # number across both and mis-price each. This makes the West delivered discount
    # a *measured* haircut of the hub basis rather than the cited -0.50 scalar floor
    # below. No-op unless the haircut is enabled AND the receipt-derived share is on
    # disk (else the scalar floor alone applies). Non-reporting units default to 1.0
    # (full spot exposure, the conservative no-haircut default). Composes with the
    # floor: the haircut shrinks the discount, the floor caps any residual deep tail.
    gen_basis = basis_by_zone_idx[fleet.zone_idx[gas_rows]]
    if getattr(config, "ercot_gas_contract_haircut", False):
        plant_spot = _pkg_ns().ercot_gas_spot_share_by_plant()
        if plant_spot is not None:
            unit_haircut = np.array(
                [plant_spot.get(int(pc), 1.0) for pc in fleet.plant_code[gas_rows]],
                dtype=float,
            )
            gen_basis = gen_basis * unit_haircut
            n_hc = int(np.sum(unit_haircut < 1.0))
            logger.info(
                "ERCOT gas contract haircut (%d): per-PLANT spot share, %d/%d gas "
                "units haircut (mean share %.2f over reporting plants); zone agg %s",
                year,
                n_hc,
                gas_rows.size,
                (float(np.mean(list(plant_spot.values()))) if plant_spot else 1.0),
                {
                    n: round(s, 2)
                    for n, s in (ercot_gas_spot_share_by_zone() or {}).items()
                    if n in zone_names
                },
            )
    weights = fleet.pmax[gas_rows]
    total_w = float(weights.sum())
    weighted_mean = float((gen_basis * weights).sum() / total_w) if total_w else 0.0
    zone_spread = gen_basis - weighted_mean
    # DELIVERED-GAS FLOOR: the raw West/Panhandle basis is a Waha *hub*
    # (pooling-point) basis — the takeaway-constrained price producers offload
    # associated gas at, negative ~42% of days in 2024. A power plant buys
    # *delivered* gas at the burner tip (intrastate transport + fuel retention +
    # minimum commodity on top), so its delivered discount cannot exceed the cited
    # measured Waha *delivered* basis. Flooring the per-zone spread at that value
    # (GAS_BASIS_DIFFERENTIAL["ERCOT"] = -0.50) keeps the West/Permian gas units
    # (Morgan Creek, Laredo, Permian Basin, Ector County) from offering ~$0/MWh and
    # running baseload (the CT_PEAKER over-run); the measured TX
    # delivered-to-electric-power level ($2.11/MMBtu in 2024) confirms no TX plant
    # paid near $0 delivered. Forward-defensible (regenerates per year, tracks HH);
    # zones already above the floor (North, Houston, ...) are untouched, so only
    # the unphysical deep-negative West tail is truncated. Off unless the basis is
    # explicitly set on the config.
    floor_basis = getattr(config, "ercot_gas_delivered_floor_basis", None)
    if floor_basis is not None:
        zone_spread = np.maximum(zone_spread, float(floor_basis))
    # LEVEL correction: replace the flat -0.50 scalar already in the price with the
    # measured TX electric-power delivered basis. 0.0 if the series is unavailable
    # (forward years) -> pure mean-zero spread, the prior behaviour.
    ep_basis = ercot_electric_power_gas_basis(year)
    scalar = GAS_BASIS_DIFFERENTIAL.get("ERCOT", 0.0)
    level_corr = (ep_basis - scalar) if ep_basis is not None else 0.0
    gen_offset = level_corr + zone_spread
    floored = np.maximum(
        fuel_prices[gas_rows, :] + gen_offset[:, np.newaxis], _GAS_PRICE_FLOOR
    )
    fuel_prices[gas_rows, :] = floored
    logger.info(
        "ERCOT zonal gas basis (%d): %d gas units; level %+.2f -> measured EP "
        "%+.2f (corr %+.2f), zonal spread %.2f..%.2f $/MMBtu%s",
        year,
        gas_rows.size,
        scalar,
        (ep_basis if ep_basis is not None else scalar),
        level_corr,
        float(zone_spread.min()),
        float(zone_spread.max()),
        (
            f" (delivered floor {float(floor_basis):+.2f})"
            if floor_basis is not None
            else ""
        ),
    )


# Fallback Waha negative-price-day frequency when the measured per-year value
# (data/raw/ercot_zonal_gas_hub.csv neg_day_freq, e.g. a forward year) is absent.
# The fraction of hours assigned to the COLLAPSED (deep-negative) regime in the
# two-regime net-load step; the complement is the FIRM regime. 0.42 is the 2024
# record (EIA: Waha < $0 on 42% of trading days) — a conservative central value.
_WEST_GAS_COLLAPSE_FREQ_DEFAULT: float = 0.42
# Model zones priced off the Waha hub (the anti-correlated, takeaway-constrained
# Permian basin). Panhandle carries ~0 modeled load but is included for parity.
_ERCOT_WAHA_ZONES: tuple[str, ...] = ("West", "Panhandle")


def ercot_west_oversupply_collapse_freq(
    west_vre_mw: np.ndarray,
    west_local_load_mw: np.ndarray,
    export_limit_mw: float,
) -> float | None:
    """Endogenous Waha collapse frequency from forecast West/Panhandle oversupply.

    The forward analogue of the measured Waha negative-price-day frequency
    (:func:`ercot_waha_collapse_freq`) — the *forecast* driver that closes the
    last measured input of the West net-load gas shape (gap G6). The Waha hub
    collapses deeply negative when the Permian/West basin is **over-supplied**:
    when local West+Panhandle wind+solar generation exceeds what the region can
    burn/serve locally **plus** what it can ship out across its constrained
    takeaway (the WESTEX + PNHNDL export TTC), the surplus has nowhere to go and
    crashes the local (Waha-correlated) price. This returns the fraction of hours
    that happens:

        ``freq = mean( west_vre > west_local_load + export_limit )``

    Every input is a forecast quantity the model already builds — the West/
    Panhandle VRE **capacity × CF** (a build plus a weather-year CF shape), the
    West local **load** (a load forecast), and the **export TTC** (the
    transmission topology) — so the frequency regenerates for any forward year and
    **responds to changed conditions**: more West VRE raises ``west_vre``, pushing
    more hours over the headroom line -> higher collapse frequency; more local
    load or more takeaway lowers it (admissibility tests #10/#12). It is therefore
    a structural mechanism, not a fitted number — and the measured ``neg_day_freq``
    stays as the backcast realization this is validated against, never re-pinned.

    Returns ``None`` for a degenerate (empty / mismatched-length) series so the
    caller falls back to the measured value or the default.
    """
    vre = np.asarray(west_vre_mw, dtype=float)
    load = np.asarray(west_local_load_mw, dtype=float)
    if vre.size == 0 or load.size != vre.size:
        return None
    # Headroom = what the basin can absorb locally + export across its takeaway.
    # Oversupply hours are those whose local VRE exceeds it (the surplus that
    # crashes Waha). No Python loop over hours — pure vectorised comparison.
    headroom = load + float(export_limit_mw)
    return float((vre > headroom).mean())


def apply_ercot_west_netload_gas_shape(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    net_load_mw: np.ndarray,
    henry_hub_path: Path | None = None,
    west_oversupply_freq: float | None = None,
) -> None:
    """Make the West/Panhandle Waha gas basis a two-regime function of net-load.

    The structural replacement for the flat
    :attr:`~market_sim.config.scenarios.ScenarioConfig.ercot_gas_delivered_floor_basis`
    scalar. The Waha hub is not a constant annual discount: it collapses deeply
    negative precisely when regional gas+power demand is **low** (shoulder /
    overnight oversupply against constrained Permian takeaway) and firms up toward
    its normal delivered level when demand is **high** — i.e. the basis is
    anti-correlated with system net-load (``load - wind - solar``), the same
    weather/demand driver the ST_GAS reliability drag keys off
    (:func:`market_sim.data.fleet.apply_gas_st_netload_drag_floor`).

    A single annual scalar prices a West **peaker** — which burns only in the
    high-net-load scarcity hours, when Waha is firm — on the same ~$0 annual-mean
    gas as a West baseload **CC**, which burns across all hours including the
    cheap collapse. That collapses the heat-rate spread and floats the inefficient
    peakers at baseload (the CT_PEAKER over-run). Indexing the basis to net-load
    instead lets the peaker/CC split fall out of *when each unit runs* rather than
    a chosen per-unit number.

    **Two-regime step keyed on the collapse frequency.** The Waha basis is
    bimodal — deeply negative on the days the hub is over-supplied, firm on the
    rest — so a single number for the whole distribution is wrong in both tails.
    The split point is the Waha negative-price-day frequency ``collapse_freq``.
    When ``config.ercot_west_gas_endogenous_collapse`` is on it is the
    **endogenous** forecast oversupply frequency passed in as
    ``west_oversupply_freq`` (:func:`ercot_west_oversupply_collapse_freq`: how
    often forecast West/Panhandle VRE exceeds local load + export TTC) — the
    forward driver that closes the last measured input (gap G6). Otherwise it is
    the **measured** value (``data/raw/ercot_zonal_gas_hub.csv`` ``neg_day_freq``;
    2024 is EIA-authoritative at 42% of trading days, id=64445), which also stays
    logged as the backcast realization to validate the endogenous value against.
    The ``config.ercot_west_gas_collapse_freq`` override still wins for diagnostic
    probes. The lowest ``collapse_freq`` fraction of net-load hours are assigned a deep collapsed
    basis; the top ``1 - collapse_freq`` are assigned the firm Waha **delivered**
    level ``Henry Hub + ercot_west_gas_firm_basis`` — the level a West plant pays
    in the high-demand hours its peakers actually run. The deep value is **not**
    chosen: it is solved from the annual-mean constraint

        ``collapse_freq · deep + (1 - collapse_freq) · firm = annual_measured``

    so the measured annual Waha basis already set by
    :func:`apply_ercot_zonal_gas_basis` is preserved — only redistributed across
    hours — then floored at the physical delivered minimum (:data:`_GAS_PRICE_FLOOR`;
    delivered gas is never negative, so the realised annual mean rises slightly
    above the deep-negative hub mean, which is correct: the hub goes negative, the
    burner tip does not). Because peakers run only in the top-demand hours they sit
    firmly in the firm regime and pay firm Waha; a baseload CC running across all
    hours pays the blend.

    Structural, not a residual fit: every input is measured or cited — the split is
    the measured negative-day frequency, the firm level is the cited firm Waha
    delivered basis, and the deep level is forced by mean-preservation, none tuned
    to the CT_PEAKER volume residual. It is a function of net-load (a load forecast
    plus a VRE build, so it regenerates for any forward year and responds to
    changed conditions — more VRE lowers net-load and shifts which hours collapse,
    admissibility tests #10/#12).

    Gated on ``config.ercot_west_netload_gas_shape``, ``config.ercot_zonal_gas_basis``
    (it shapes the basis that function applies) and ``config.iso == "ERCOT"``.
    Mutates ``fuel_prices`` in place; idempotent given the same inputs.
    """
    if not getattr(config, "ercot_west_netload_gas_shape", False):
        return
    if not getattr(config, "ercot_zonal_gas_basis", False):
        return
    if config.iso != "ERCOT":
        return
    from market_sim.config.iso_configs import get_iso_config

    zone_names = get_iso_config(config.iso).zone_names
    waha_zone_idx = [
        i for i, name in enumerate(zone_names) if name in _ERCOT_WAHA_ZONES
    ]
    if not waha_zone_idx:
        return
    gas_rows = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX))[0]
    west_rows = gas_rows[np.isin(fleet.zone_idx[gas_rows], waha_zone_idx)]
    if west_rows.size == 0:
        return

    hours = fuel_prices.shape[1]
    nl = np.asarray(net_load_mw, dtype=float)[:hours]
    if nl.size != hours:
        return

    # Collapse frequency: the fraction of hours in the deep (low-net-load) regime.
    # Precedence: config override (env ERCOT_WEST_GAS_COLLAPSE_FREQ, diagnostic) >
    # the ENDOGENOUS forecast oversupply frequency (when
    # ercot_west_gas_endogenous_collapse is on; the forward driver, gap G6) >
    # measured per-year neg_day_freq > the 2024 record default. The measured value
    # is always read so it can be logged as the backcast realization to validate
    # the endogenous frequency against. Clamped into (0, 1) exclusive so both
    # regimes are non-empty.
    measured_freq = ercot_waha_collapse_freq(year)
    collapse_freq = getattr(config, "ercot_west_gas_collapse_freq", None)
    freq_source = "config-override"
    endogenous = getattr(config, "ercot_west_gas_endogenous_collapse", False)
    if collapse_freq is None and endogenous and west_oversupply_freq is not None:
        collapse_freq = west_oversupply_freq
        freq_source = "endogenous-oversupply"
    if collapse_freq is None:
        collapse_freq = measured_freq
        freq_source = "measured-neg-day"
    if collapse_freq is None:
        collapse_freq = _WEST_GAS_COLLAPSE_FREQ_DEFAULT
        freq_source = "default"
    collapse_freq = float(min(max(float(collapse_freq), 0.01), 0.99))

    # Firm (high-demand) Waha delivered level the top-demand hours should reach.
    firm_basis = getattr(config, "ercot_west_gas_firm_basis", None)
    if firm_basis is None:
        firm_basis = GAS_BASIS_DIFFERENTIAL.get("ERCOT", -0.50)
    firm_basis = float(firm_basis)
    hh = _pkg_ns()._henry_hub_monthly(henry_hub_path)
    hh_year = [hh[(year, m)] for m in range(1, 13) if (year, m) in hh]
    if not hh_year:
        return
    hh_mean = float(np.mean(hh_year))

    # Burner-tip delivered floor for the COLLAPSE regime. The hub goes to ~$0 (and
    # negative) on over-supply days, but a power plant's *delivered* gas never does:
    # intrastate transport + as-burned handling set a positive floor well above the
    # hub. Flooring the deep regime at the generic _GAS_PRICE_FLOOR (~$0.10, a
    # hub-like number) creates a perverse "cheap-hour magnet" that pulls low-HR West
    # CTs into the lowest-demand hours (dispatch anti-correlated with load) — the
    # delivered burner tip must floor at the transport-bound minimum instead. Config
    # ercot_west_gas_delivered_floor (env ERCOT_WEST_GAS_DELIVERED_FLOOR); None keeps
    # the generic floor (legacy behaviour).
    deliv_floor = getattr(config, "ercot_west_gas_delivered_floor", None)
    deliv_floor = float(deliv_floor) if deliv_floor is not None else _GAS_PRICE_FLOOR
    firm_price = max(hh_mean + firm_basis, deliv_floor)

    # Split the net-load distribution: the lowest collapse_freq fraction of hours
    # COLLAPSE, the top (1 - collapse_freq) are FIRM. nl_split is the collapse_freq
    # quantile of net-load.
    nl_split = float(np.quantile(nl, collapse_freq))
    collapse_mask = nl <= nl_split  # (T,)
    cfrac = float(collapse_mask.mean())  # realised collapse fraction (ties)
    ffrac = 1.0 - cfrac
    if cfrac <= 0.0 or ffrac <= 0.0:
        return  # degenerate net-load distribution; leave the flat basis in place

    # Deep collapsed price per unit, forced by the annual-mean constraint
    # cfrac*deep + ffrac*firm = p_mean, then floored at the delivered burner-tip
    # minimum (the burner tip never reaches the hub's negative collapse — the floor
    # lift is the realised premium of delivered over hub).
    p_mean = fuel_prices[west_rows, :].mean(axis=1)  # (n_west,)
    deep_price = (p_mean - ffrac * firm_price) / cfrac  # (n_west,)
    deep_price = np.maximum(deep_price, deliv_floor)
    shaped = np.where(
        collapse_mask[np.newaxis, :], deep_price[:, np.newaxis], firm_price
    )
    fuel_prices[west_rows, :] = shaped
    realised_mean = fuel_prices[west_rows, :].mean()
    logger.info(
        "ERCOT West net-load gas step (%d): %d West/Panhandle gas units; "
        "collapse_freq %.3f (%s; endogenous-oversupply %s vs measured neg-day %s); "
        "split nl %.0f MW; firm basis %+.2f -> firm $%.2f, "
        "deep $%.2f..$%.2f (deliv floor $%.2f); annual gas $%.2f -> $%.2f "
        "(floor-lifted from the negative hub tail)",
        year,
        west_rows.size,
        cfrac,
        freq_source,
        (f"{west_oversupply_freq:.3f}" if west_oversupply_freq is not None else "n/a"),
        (f"{measured_freq:.3f}" if measured_freq is not None else "n/a"),
        nl_split,
        firm_basis,
        firm_price,
        float(deep_price.min()),
        float(deep_price.max()),
        deliv_floor,
        float(p_mean.mean()),
        float(realised_mean),
    )
