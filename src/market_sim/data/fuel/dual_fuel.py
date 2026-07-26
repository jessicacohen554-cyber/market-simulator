"""Dual-fuel (oil/gas switch-capable) pricing: oil parity cap and switch mask.

Split out of ``data/fuel.py`` (W-D3; refactor-consolidation plan §5 item 3) as
pure code motion. ``dual_fuel_plant_groups`` and ``iso_monthly_oil_prices``
are resolved through the package namespace at call time
(:func:`._shared._pkg_ns`) — tests patch the capability lookup on the facade.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import OIL_PRICE_PER_MMBTU
from market_sim.config.paths import OIL_PRICES_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays

from ._shared import (
    _DAYS_IN_MONTH,
    _GAS_FUEL_IDX,
    _expand_monthly_to_hourly,
    _pkg_ns,
    logger,
)
from .trajectories import resolve_annual_oil_price

#: Measured EIA daily New York Harbor ULSD spot ($/gal), fetched by
#: ``scripts/data/fetch_ny_harbor_distillate_daily.py``. Used ONLY for its
#: within-month shape (see :func:`oil_daily_shape_factors`); the delivered
#: level stays the monthly EIA-923 receipt, which alone carries transport,
#: storage and distributor margin that a FOB cargo quote does not.
NY_HARBOR_ULSD_DAILY_PATH: Path = OIL_PRICES_DIR / "ny_harbor_ulsd_daily.csv"

_ULSD_DAILY_DATED_CACHE: dict[Path, dict[int, dict[int, dict[int, float]]]] = {}


def _ny_harbor_ulsd_daily_dated(
    path: Path | None = None,
) -> dict[int, dict[int, dict[int, float]]]:
    """Return ``{year: {month: {day-of-month: $/gal}}}`` NY Harbor ULSD spot.

    The petroleum sibling of
    :func:`~market_sim.data.fuel.hubs._transco_z6_daily_dated`: each EIA
    trading-day quote keyed by its true calendar date, so the daily overlay
    places every print where it actually occurred. Missing file → ``{}``
    (the consumer then resolves to a flat, no-shape series). Cached per path.
    """
    resolved = Path(path) if path else NY_HARBOR_ULSD_DAILY_PATH
    if resolved in _ULSD_DAILY_DATED_CACHE:
        return _ULSD_DAILY_DATED_CACHE[resolved]
    out: dict[int, dict[int, dict[int, float]]] = {}
    if resolved.exists():
        frame = pd.read_csv(resolved, parse_dates=["date"]).sort_values("date")
        for r in frame.itertuples():
            out.setdefault(r.date.year, {}).setdefault(r.date.month, {})[r.date.day] = (
                float(r.ny_harbor_ulsd_usd_gal)
            )
    _ULSD_DAILY_DATED_CACHE[resolved] = out
    return out


def oil_daily_shape_factors(
    year: int, hours: int, path: Path | None = None
) -> np.ndarray:
    """Return ``(hours,)`` within-month daily distillate-price shape factors.

    The petroleum analogue of
    :func:`~market_sim.data.fuel.hubs.gas_daily_shape_factors`, and built by
    the identical construction: each measured NY Harbor ULSD spot quote sits on
    its true trade date, non-trading days (weekends / holidays) carry the last
    trading day's value forward as a staircase (never an interpolation across
    the gap), and each calendar day's factor is that staircase value divided by
    the month's own calendar-day staircase mean. Multiplying the correctly
    levelled monthly oil series by these factors therefore adds the real
    intra-month distillate swing while leaving every monthly mean EXACTLY
    unchanged — mean preservation holds by construction, not by a post-hoc
    renormalization. A month with no quotes resolves to all-ones (no shape).

    Why the delivered level must stay monthly (rule 14 [R-ACCURATE]): the
    EIA-923 receipt is a *delivered* price — it carries transport, storage and
    the distributor's margin — while the EIA spot is a FOB New York Harbor
    cargo quote. Their levels are not interchangeable and the spot must never
    replace the receipt; what the spot uniquely supplies, and the monthly
    receipt structurally cannot, is which days of the month were dear. This is
    also exactly the construction a forecast would use (a forward monthly level
    times a daily shape), so it is rule-13 admissible rather than
    backcast-only.
    """
    factors = np.ones(hours, dtype=float)
    dated = _pkg_ns()._ny_harbor_ulsd_daily_dated(path).get(year)
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
                day_factor = seg / mean
                shaped = np.repeat(day_factor, 24)[: max(0, hours - hour)]
                factors[hour : hour + len(shaped)] = shaped
        hour += month_hours
        day0 += n_days
    return factors


def dual_fuel_oil_price_series(
    config: ScenarioConfig,
    year: int,
    monthly_costs_path: Path | None = None,
) -> np.ndarray:
    """Return the ``(T,)`` delivered oil price ($/MMBtu) for dual-fuel parity.

    The measured ISO-month EIA-923 Petroleum series
    (:func:`iso_monthly_oil_prices`) expanded to hours, with unreported
    months filled from the same fallback :func:`resolve_fuel_prices` uses for
    the (non-dual-fuel) oil fleet: the AEO2025 oil trajectory
    (:func:`resolve_annual_oil_price`) in forecast mode, or the flat cited
    default (:data:`~market_sim.config.constants.OIL_PRICE_PER_MMBTU`) in
    backcast mode / years with no F923 data at all — keeping the dual-fuel
    parity price consistent with a plain oil unit's price in the same year.

    With ``config.dual_fuel_oil_daily_parity`` on, the resulting monthly
    plateau is shaped to DAILY resolution by :func:`oil_daily_shape_factors` —
    mean-preservingly, so every monthly delivered level is untouched and only
    the within-month profile changes. This is a granularity fix, not a level
    change: the gas side of the same min() comparison is already daily (the
    hub-basis overlay), so a monthly-FLAT oil cap pins ~16.5 GW of downstate
    NYISO dual-fuel capacity at one constant price on exactly the cold days
    the daily gas price spikes, truncating the winter peak (120 of 744
    Jan-2025 hours cleared on that flat cap). Default off, byte-identical when
    off. See docs/handoffs/nyiso-overrun-underrun-2026-07.md §2/§6.
    """
    fallback = (
        resolve_annual_oil_price(config, year)
        if config.mode == "forecast"
        else OIL_PRICE_PER_MMBTU
    )
    monthly = _pkg_ns().iso_monthly_oil_prices(config, year, monthly_costs_path)
    if monthly is None:
        hourly = np.full(config.hours, fallback, dtype=float)
    else:
        filled = np.where(np.isnan(monthly), fallback, np.asarray(monthly, dtype=float))
        hourly = _expand_monthly_to_hourly(filled, config.hours)
    if getattr(config, "dual_fuel_oil_daily_parity", False):
        hourly = hourly * _pkg_ns().oil_daily_shape_factors(year, config.hours)
    return hourly


def apply_dual_fuel_pricing(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    monthly_costs_path: Path | None = None,
) -> None:
    """Cap dual-fuel gas units' fuel price at the delivered oil price.

    Doc 03 Pack G: a gas unit flagged oil/gas switch-capable in the EIA-860
    Multifuel schedule (:func:`market_sim.data.fleet.dual_fuel_plant_groups`)
    burns whichever fuel is cheaper each hour, so its marginal cost is
    ``min(gas_mc, oil_mc)`` — implemented as an elementwise
    ``min(gas_price, oil_price)`` on the fuel-price array, which
    :func:`~market_sim.data.fleet.assemble_mc` then multiplies by the unit's
    (gas) heat rate. The switch binds only when the unit's delivered gas
    price spikes past oil parity (winter basis events), so normal-month
    dispatch is unchanged. Objective-only: no LP structural change, and
    emissions stay on the gas characterization (a known simplification —
    oil burn hours under-count CO2 slightly). The *generation* of switched
    hours is re-attributed to oil downstream in the calibration report via
    :func:`dual_fuel_switch_mask` (so modeled oil matches the EIA-930
    ``NG: OIL`` order of magnitude); the price/dispatch here is untouched.

    Gated on ``config.dual_fuel_switching`` (off by default; the calibration
    harness enables it for PJM), so ERCOT and existing forecasts are
    byte-identical. Mutates ``fuel_prices`` in place; idempotent, so callers
    that re-apply it after a later gas-price overwrite are safe.

    Args:
        fuel_prices: The ``(n_gen, T)`` delivered fuel-price array, updated
            in place for dual-fuel-capable gas generators.
        fleet: Vectorized fleet attributes; ``fuel_type_idx`` selects gas
            units and ``plant_code`` / ``plant_group`` key the EIA-860
            dual-fuel capability lookup.
        config: Scenario configuration supplying ``dual_fuel_switching``,
            ``iso`` and ``hours``.
        year: Calendar year keying the measured oil-price lookup.
        monthly_costs_path: Optional override for the F923 parquet path.
    """
    if not getattr(config, "dual_fuel_switching", False):
        return
    groups = fleet.plant_group
    if groups is None:
        return
    capable = _pkg_ns().dual_fuel_plant_groups()
    if not capable:
        return

    oil_hourly = dual_fuel_oil_price_series(config, year, monthly_costs_path)
    is_gas = np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX)
    n_capped = 0
    mw_capped = 0.0
    for g in np.nonzero(is_gas)[0]:
        if (int(fleet.plant_code[g]), str(groups[g])) not in capable:
            continue
        np.minimum(fuel_prices[g], oil_hourly, out=fuel_prices[g])
        n_capped += 1
        mw_capped += float(fleet.pmax[g])
    if n_capped:
        logger.info(
            "dual-fuel switching (%s %d): %d gas tranches (%.0f MW) capped "
            "at the delivered oil price",
            config.iso,
            year,
            n_capped,
            mw_capped,
        )


def dual_fuel_switch_mask(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    monthly_costs_path: Path | None = None,
) -> np.ndarray:
    """Return the ``(n_gen, T)`` bool mask of dual-fuel gas units burning oil.

    A dual-fuel-capable gas unit (:func:`dual_fuel_plant_groups`) runs on its
    backup distillate/residual when its delivered gas price exceeds delivered
    oil parity, so this marks the generator-hours where
    ``gas_price > oil_price`` for the capable units — the counterpart of the
    ``min`` that :func:`apply_dual_fuel_pricing` writes. Call it on the
    pre-``min`` gas-price array (i.e. *before* :func:`apply_dual_fuel_pricing`),
    so ``fuel_prices`` still carries the unburdened (hub-overlaid) gas price.

    Used by the calibration's dispatch re-attribution: a switched unit-hour's
    dispatched MWh is petroleum generation (EIA-930 counts it in ``NG: OIL``),
    not gas, even though the LP carries it on the gas heat-rate. Returns an
    all-``False`` mask when dual-fuel switching is off or no capable unit is in
    the fleet, so non-NEISO/PJM runs see no re-attribution.
    """
    mask = np.zeros(fuel_prices.shape, dtype=bool)
    if not getattr(config, "dual_fuel_switching", False):
        return mask
    groups = fleet.plant_group
    if groups is None:
        return mask
    capable = _pkg_ns().dual_fuel_plant_groups()
    if not capable:
        return mask
    oil_hourly = dual_fuel_oil_price_series(config, year, monthly_costs_path)
    is_gas = np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX)
    for g in np.nonzero(is_gas)[0]:
        if (int(fleet.plant_code[g]), str(groups[g])) not in capable:
            continue
        mask[g] = fuel_prices[g] > oil_hourly
    return mask
