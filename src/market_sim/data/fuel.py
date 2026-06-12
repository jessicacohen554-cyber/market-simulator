"""Fuel price and NOx price resolution.

Resolves per-generator delivered fuel prices ($/MMBtu) and the scenario
NOx price into the forms consumed by marginal-cost assembly
(see :func:`market_sim.data.fleet.assemble_mc`). Carbon-price resolution
lives in :mod:`market_sim.policy.carbon`.

**Gas** generators all pay the same delivered price for a year — the AEO
Henry Hub trajectory (:data:`HENRY_HUB_TRAJECTORIES`) plus the ISO basis
differential (:data:`GAS_BASIS_DIFFERENTIAL`), optionally seasonally
shaped. Per-plant EIA-923 monthly gas costs are **off by default**
(``gas_plant_monthly_fuel_pricing``): merchant CCs in a hub all buy gas in
the same market, and EIA-923 Schedule-5 gas reporting is too sparse (~12%
of ERCOT CC MW) to split same-zone units without introducing a spurious
price asymmetry. For pipeline-constrained ISOs whose marginal gas cost is
set by a blown-out trading hub rather than plant receipts (NEISO /
Algonquin Citygate), the measured hub-month basis overlay
(``gas_hub_basis_overlay``, :func:`apply_hub_basis_overlay`) replaces the
gas price with measured Henry Hub monthly + measured hub basis in covered
months.

**Coal** generators in historical years still pay their own measured
EIA-923 Schedule 5 monthly delivered cost where reported (lignite
mine-mouth vs railed PRB are genuinely different costs), falling back to
the per-year coal supply-class trajectories otherwise. The same resolver
path serves both backcast and forward, so calibration and projection share
one model.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import (
    BIOMASS_PRICE_PER_MMBTU,
    COAL_PRICE_BASE,
    COAL_PRICE_ESCALATION,
    END_YEAR,
    GAS_BASIS_DIFFERENTIAL,
    GAS_MONTHLY_SEASONALITY,
    HENRY_HUB_TRAJECTORIES,
    HOURS_PER_YEAR,
    INFLATION_RATE,
    OIL_PRICE_PER_MMBTU,
    START_YEAR,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.eia923 import (
    EIA923_MONTHLY_COSTS_PATH,
    available_years,
    load_monthly_fuel_costs,
    plant_month_price_grid,
    state_month_price_grid,
)
from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    FleetArrays,
    dual_fuel_plant_groups,
)
from market_sim.data.hydrogen import compute_h2_fuel_cost

logger = logging.getLogger(__name__)

# Fuel-type integer codes (from FUEL_TYPE_MAP) that burn natural gas and
# therefore pay the Henry Hub price. CCUS (``gas_cc_ccs``) burns the same
# natural gas as an unabated gas CC; ``gas_st`` is legacy gas steam.
_GAS_FUEL_IDX: tuple[int, ...] = (
    FUEL_TYPE_MAP["gas_cc"],
    FUEL_TYPE_MAP["gas_ct"],
    FUEL_TYPE_MAP["gas_cc_ccs"],
    FUEL_TYPE_MAP["gas_st"],
)

# Fuel-type integer code for coal-fired units, which pay the coal price.
_COAL_FUEL_IDX: int = FUEL_TYPE_MAP["coal"]

# Fuel-type integer code for oil-fired units (distillate/residual peakers and
# steam), which pay the delivered oil price.
_OIL_FUEL_IDX: int = FUEL_TYPE_MAP["oil"]

# Fuel-type integer code for biomass units, which pay the delivered biomass
# fuel cost.
_BIOMASS_FUEL_IDX: int = FUEL_TYPE_MAP["biomass"]

# Fuel-type integer codes for hydrogen turbines, whose fuel price is the
# derived hydrogen fuel cost (see :mod:`market_sim.data.hydrogen`).
_HYDROGEN_FUEL_IDX: tuple[int, int] = (
    FUEL_TYPE_MAP["hydrogen_ct"],
    FUEL_TYPE_MAP["hydrogen_ccgt"],
)

# Fuel price ($/MMBtu) for non-fuel-burning units (e.g. wind, solar, nuclear,
# hydro, imports), which carry no commodity fuel cost in this model.
_ZERO_FUEL_PRICE: float = 0.0

# Calendar days per month for a non-leap year (sums to 365 -> 8760 hours).
_DAYS_IN_MONTH: tuple[int, ...] = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def resolve_annual_gas_price(config: ScenarioConfig, year: int) -> float:
    """Return the delivered annual gas price ($/MMBtu) for the scenario year.

    The price is the AEO Henry Hub trajectory value for ``year`` and the
    scenario's ``gas_price_path``, plus the ISO's basis differential::

        delivered = HENRY_HUB_TRAJECTORIES[path][year] + basis

    Years beyond the trajectory's last entry are extrapolated using the
    final year-over-year growth rate. This annual (seasonality-free) price
    is the one capacity new-entry LCOE screening should charge gas units,
    so dispatch and capacity evolution see the same gas cost for a year.

    When ``config.gas_price_override`` is set the trajectory lookup is
    bypassed entirely: the override is treated as the measured Henry Hub
    price and the ISO basis differential is added to it, so a calibration
    backcast charges the year's actual delivered gas cost.

    Args:
        config: Scenario configuration supplying ``iso``,
            ``gas_price_path`` and an optional ``gas_price_override``.
        year: Calendar year to resolve.

    Returns:
        The delivered annual gas price in $/MMBtu.
    """
    basis = GAS_BASIS_DIFFERENTIAL.get(config.iso, 0.0)
    if config.gas_price_override is not None:
        return config.gas_price_override + basis

    trajectory = HENRY_HUB_TRAJECTORIES[config.gas_price_path]
    if year in trajectory:
        henry_hub = trajectory[year]
    else:
        # Extrapolate beyond the trajectory using the last growth rate.
        last_year = max(trajectory)
        annual_growth = trajectory[last_year] / trajectory[last_year - 1]
        henry_hub = trajectory[last_year] * annual_growth ** (year - last_year)

    return henry_hub + basis


def _seasonal_factors(hours: int) -> np.ndarray:
    """Return an ``(hours,)`` array of monthly gas seasonality multipliers.

    The 8760-hour year is filled month by month from
    :data:`GAS_MONTHLY_SEASONALITY`; a sub-annual horizon takes the leading
    slice. The 12-iteration loop is over months, not hours.
    """
    full_year = np.empty(HOURS_PER_YEAR)
    hour = 0
    for month in range(1, 13):
        hours_in_month = _DAYS_IN_MONTH[month - 1] * 24
        full_year[hour:hour + hours_in_month] = GAS_MONTHLY_SEASONALITY[month]
        hour += hours_in_month
    if hours <= HOURS_PER_YEAR:
        return full_year[:hours]
    # Multi-year horizons repeat the annual shape.
    reps = -(-hours // HOURS_PER_YEAR)
    return np.tile(full_year, reps)[:hours]


def prb_passthrough_series(
    config: ScenarioConfig, year: int, hours: int
) -> "float | np.ndarray":
    """Return the PRB above-must-run fuel passthrough — flat or gas-keyed.

    When ``config.coal_prb_passthrough_sigmoid`` is False, returns the flat
    ``config.coal_prb_passthrough`` scalar (current behaviour). When True,
    returns an ``(hours,)`` logistic of the monthly delivered gas price
    ($/MMBtu): the passthrough rises from ``coal_prb_passthrough_floor``
    (cheap gas — PRB needs a deep fuel discount to clear against cheap gas CC)
    to ``coal_prb_passthrough_ceil`` (dear gas — little or no discount, and a
    value > 1.0 marks the PRB bid *up* to suppress over-dispatch), centred at
    ``coal_prb_passthrough_gas_mid`` with slope
    ``coal_prb_passthrough_gas_slope`` per $/MMBtu.

    Keying off the monthly gas price tracks the merit-order crossover: PRB is
    infra-marginal under gas CC, so the gap it must close scales with gas.
    """
    if not getattr(config, "coal_prb_passthrough_sigmoid", False):
        return config.coal_prb_passthrough
    return _sigmoid_passthrough(
        _gas_series(config, year, hours),
        config.coal_prb_passthrough_floor,
        config.coal_prb_passthrough_ceil,
        config.coal_prb_passthrough_gas_mid,
        config.coal_prb_passthrough_gas_slope,
    )


def prb_passthrough_series_follower(
    config: ScenarioConfig, year: int, hours: int
) -> np.ndarray:
    """Return the load-follower-tier PRB passthrough series (gas-keyed).

    Used only when ``config.coal_prb_passthrough_tiered`` is set, for PRB
    plants whose per-plant must-run floor is at or below
    ``coal_prb_follower_mustrun_max`` — the low-floor units that cycle as
    load-followers rather than baseload price-takers. Same logistic form as
    the baseload tier but its own ``coal_prb_follower_*`` parameters.
    """
    return _sigmoid_passthrough(
        _gas_series(config, year, hours),
        config.coal_prb_follower_floor,
        config.coal_prb_follower_ceil,
        config.coal_prb_follower_gas_mid,
        config.coal_prb_follower_gas_slope,
    )


def bit_passthrough_series(
    config: ScenarioConfig, year: int, hours: int
) -> "float | np.ndarray":
    """Return the bituminous above-must-run fuel passthrough — flat or gas-keyed.

    The PJM coal-fleet analogue of :func:`prb_passthrough_series`. When
    ``config.coal_bit_passthrough_sigmoid`` is False, returns ``1.0`` (full
    fuel cost — current behaviour). When True, returns an ``(hours,)``
    logistic of the monthly delivered gas price ($/MMBtu) rising from
    ``coal_bit_passthrough_floor`` (cheap gas — bit coal discounts to hold
    its baseload against cheap gas CC) to ``coal_bit_passthrough_ceil``
    (dear gas — full cost, or a markup > 1.0 that suppresses over-run),
    centred at ``coal_bit_passthrough_gas_mid`` with slope
    ``coal_bit_passthrough_gas_slope`` per $/MMBtu.

    Keying off the monthly gas price tracks the merit-order crossover the
    same way the PRB sigmoid does: bit coal's competitiveness against gas CC
    scales with the delivered gas price.
    """
    if not getattr(config, "coal_bit_passthrough_sigmoid", False):
        return 1.0
    return _sigmoid_passthrough(
        _gas_series(config, year, hours),
        config.coal_bit_passthrough_floor,
        config.coal_bit_passthrough_ceil,
        config.coal_bit_passthrough_gas_mid,
        config.coal_bit_passthrough_gas_slope,
    )


def lignite_passthrough_series(
    config: ScenarioConfig, year: int, hours: int
) -> "float | np.ndarray":
    """Return the lignite above-must-run fuel passthrough — flat or gas-keyed.

    The ERCOT mine-mouth-fleet analogue of :func:`bit_passthrough_series`.
    When ``config.coal_lignite_passthrough_sigmoid`` is False, returns ``1.0``
    (full fuel cost — current behaviour). When True, returns an ``(hours,)``
    logistic of the monthly delivered gas price ($/MMBtu) rising from
    ``coal_lignite_passthrough_floor`` (cheap gas — mine-mouth lignite's
    take-or-pay fixed costs are sunk, so it discounts its bid to hold
    baseload against cheap gas CC) to ``coal_lignite_passthrough_ceil``
    (dear gas — full cost; the default ceil of 1.0 never marks lignite up),
    centred at ``coal_lignite_passthrough_gas_mid`` with slope
    ``coal_lignite_passthrough_gas_slope`` per $/MMBtu.

    This discounts the bid, not the cost: the measured ~$1.45/MMBtu
    delivered lignite price still anchors the full-cost end of the curve.
    """
    if not getattr(config, "coal_lignite_passthrough_sigmoid", False):
        return 1.0
    return _sigmoid_passthrough(
        _gas_series(config, year, hours),
        config.coal_lignite_passthrough_floor,
        config.coal_lignite_passthrough_ceil,
        config.coal_lignite_passthrough_gas_mid,
        config.coal_lignite_passthrough_gas_slope,
    )


def sub_passthrough_series(
    config: ScenarioConfig, year: int, hours: int
) -> "float | np.ndarray | None":
    """Return the subbituminous above-must-run passthrough, or ``None``.

    Each coal passthrough sigmoid encodes basin/type/transport-specific
    economics, so "subbituminous"-tagged plants (the derived EIA-923 rank
    CSVs; non-PRB sub-bituminous basins) get their own tunable curve. When
    ``config.coal_sub_passthrough_sigmoid`` is False (default), returns
    ``None`` — the routing layer then keeps the historical behaviour of
    inheriting the PRB family (passthrough, sigmoid and follower tier),
    since plant_taxonomy maps both supplies to COAL_PRB. When True, returns
    the family's own ``(hours,)`` logistic of the monthly delivered gas
    price (``coal_sub_passthrough_*`` params, same form as the PRB/bit/
    lignite sigmoids).
    """
    if not getattr(config, "coal_sub_passthrough_sigmoid", False):
        return None
    return _sigmoid_passthrough(
        _gas_series(config, year, hours),
        config.coal_sub_passthrough_floor,
        config.coal_sub_passthrough_ceil,
        config.coal_sub_passthrough_gas_mid,
        config.coal_sub_passthrough_gas_slope,
    )


def _gas_series(config: ScenarioConfig, year: int, hours: int) -> np.ndarray:
    """Return the ``(hours,)`` delivered gas price ($/MMBtu).

    The same series the merit order prices gas at: when
    ``config.gas_monthly_actuals`` is set (the PJM keeper config), the
    measured EIA-923 ISO-month delivered cost replaces the annual price ×
    generic seasonal shape month-by-month (months with no receipts keep the
    shaped value), so a gas-keyed coal passthrough sigmoid sees the real
    winter spikes the merit order sees. Otherwise the annual price, shaped
    by the seasonality factors when ``config.gas_seasonality`` is on.
    """
    gas = resolve_annual_gas_price(config, year)
    if config.gas_seasonality:
        series = gas * _seasonal_factors(hours)
    else:
        series = np.full(hours, gas, dtype=float)
    if getattr(config, "gas_monthly_actuals", False):
        measured = iso_monthly_gas_prices(config, year)
        if measured is not None:
            hourly_measured = _expand_monthly_to_hourly(
                np.asarray(measured, dtype=float), hours
            )
            series = np.where(
                np.isnan(hourly_measured), series, hourly_measured
            )
    return _hub_overlay_series(series, config, year, hours)


def _sigmoid_passthrough(
    gas_series: np.ndarray, floor: float, ceil: float, mid: float, slope: float
) -> np.ndarray:
    """Logistic passthrough rising from ``floor`` to ``ceil`` in gas price."""
    return floor + (ceil - floor) / (
        1.0 + np.exp(-slope * (gas_series - mid))
    )


_F923_FUEL_GROUP_BY_FUEL: dict[str, str] = {
    "gas_cc": "Natural Gas",
    "gas_ct": "Natural Gas",
    "gas_cc_ccs": "Natural Gas",
    "gas_st": "Natural Gas",
    "coal": "Coal",
    # Oil-fired steam/peakers pay their own EIA-923 delivered distillate /
    # residual cost where reported; plants outside the F923 sample keep the
    # flat OIL_PRICE_PER_MMBTU default (or the nearby-plant fallback).
    "oil": "Petroleum",
}


def _month_index(hours: int) -> np.ndarray:
    """Return an ``(hours,)`` array mapping each hour to a 0-based month."""
    full = np.empty(HOURS_PER_YEAR, dtype=int)
    hour = 0
    for month_idx, days in enumerate(_DAYS_IN_MONTH):
        hours_in_month = days * 24
        full[hour:hour + hours_in_month] = month_idx
        hour += hours_in_month
    if hours <= HOURS_PER_YEAR:
        return full[:hours]
    reps = -(-hours // HOURS_PER_YEAR)
    return np.tile(full, reps)[:hours]


_PLANT_MONTHLY_CACHE: dict[Path, pd.DataFrame] = {}


def _load_monthly_cache(path: Path | None) -> pd.DataFrame | None:
    """Return the F923 monthly cost frame, or ``None`` if the parquet is absent.

    Cached on first call so a multi-year run pays the parquet read cost
    only once. A missing parquet (no historical data shipped) is benign;
    callers fall back to the AEO trajectory in that case.
    """
    resolved = path or EIA923_MONTHLY_COSTS_PATH
    if resolved in _PLANT_MONTHLY_CACHE:
        return _PLANT_MONTHLY_CACHE[resolved]
    if not Path(resolved).exists():
        return None
    frame = load_monthly_fuel_costs(resolved)
    _PLANT_MONTHLY_CACHE[resolved] = frame
    return frame


def _expand_monthly_to_hourly(
    monthly: np.ndarray, hours: int
) -> np.ndarray:
    """Broadcast a length-12 monthly price array onto the hourly horizon."""
    return monthly[_month_index(hours)]


def _iso_monthly_fuel_prices(
    config: ScenarioConfig, year: int, fuel_group: str,
    monthly_costs_path: Path | None = None,
) -> np.ndarray | None:
    """Measured ISO-month delivered price ($/MMBtu) for one F923 fuel group.

    Volume-weights the EIA-923 monthly receipt costs of ``fuel_group``
    across the ISO's plants into one hub-level price per month. Months with
    no reported receipts are returned as ``NaN`` for the caller to fill from
    the per-fuel default; returns ``None`` when the parquet, the year or the
    ISO's plants are absent entirely.
    """
    costs = _load_monthly_cache(monthly_costs_path)
    if costs is None or year not in available_years(costs):
        return None
    from market_sim.data.zone_assignment import build_zone_lookup

    try:
        iso_plants = frozenset(build_zone_lookup(config.iso))
    except Exception:
        return None
    if not iso_plants:
        return None
    sub = costs[
        (costs["year"] == year)
        & (costs["fuel_group"] == fuel_group)
        & costs["plant_id"].isin(iso_plants)
    ]
    if sub.empty:
        return None
    monthly = np.full(12, np.nan)
    spend = sub["price_per_mmbtu"] * sub["quantity"]
    by_month = sub.assign(spend=spend).groupby("month")[["spend", "quantity"]].sum()
    for m, row in by_month.iterrows():
        if row["quantity"] > 0:
            monthly[int(m) - 1] = row["spend"] / row["quantity"]
    return monthly


def iso_monthly_gas_prices(
    config: ScenarioConfig, year: int,
    monthly_costs_path: Path | None = None,
) -> np.ndarray | None:
    """Measured ISO-month delivered gas price ($/MMBtu), or ``None``.

    Volume-weights the EIA-923 monthly Natural Gas receipt costs across the
    ISO's plants into one hub-level price per month — the measured analogue
    of annual Henry Hub + basis × the generic seasonality shape, capturing
    real winter events the fixed shape damps (PJM Jan-2024: $5.07 measured
    vs ~$2.5 shaped). Staying at the ISO level keeps the hub-pricing
    property per-plant gas pricing breaks (same-zone units never split on
    patchy reporting). Months with no reported receipts are returned as
    ``NaN`` for the caller to fill from the trajectory; returns ``None``
    when the parquet, the year or the ISO's plants are absent entirely.
    """
    return _iso_monthly_fuel_prices(config, year, "Natural Gas", monthly_costs_path)


def iso_monthly_oil_prices(
    config: ScenarioConfig, year: int,
    monthly_costs_path: Path | None = None,
) -> np.ndarray | None:
    """Measured ISO-month delivered oil price ($/MMBtu), or ``None``.

    The oil price series for dual-fuel switching parity: the volume-weighted
    EIA-923 Schedule 5 monthly Petroleum (distillate / residual) receipt
    cost across the ISO's plants, one hub-level price per month. For PJM
    states this runs ~$17-23/MMBtu over 2023-2025 (EIA-923 Schedule 5
    receipts; consistent with the EIA "cost of distillate fuel oil delivered
    to the electric power sector" series, ~$20/MMBtu distillate /
    ~$14/MMBtu residual 2023-2024 — see
    :data:`~market_sim.config.constants.OIL_PRICE_PER_MMBTU`). Months with
    no reported receipts are ``NaN``; ``None`` when the parquet, the year or
    the ISO's plants are absent (forward years), in which case callers fall
    back to the flat cited default.
    """
    return _iso_monthly_fuel_prices(config, year, "Petroleum", monthly_costs_path)


# Regional gas-basis upload (doc-07/doc-08 U4 / doc-01 §4): per-ISO monthly
# delivered hub basis ($/MMBtu over Henry Hub) for the named pipeline trading
# points that EIA-923's plant-average delivered cost understates — Transco Z6
# NY / Iroquois for NYISO, Algonquin (AGT) for ISO-NE. The NEISO/Algonquin leg
# is filled (ISO-NE MA gas index, 2023-2025, 35/36 months); other ISOs remain
# header-only until a licensed ICE/Platts or EIA-citygate-proxy fill lands;
# see docs/multi-iso/data-acquisition-report.md §1.
WINTER_GAS_BASIS_PATH: Path = (
    Path(__file__).parents[3] / "inputs" / "raw-data"
    / "gas_basis_by_iso_month.csv"
)

# Measured Henry Hub monthly spot averages (EIA RNGWHHDm via the
# datasets/natural-gas public-domain mirror; see
# docs/multi-iso/data-acquisition-report.md Step 1a). The hub-basis overlay
# adds the measured ISO-month basis back onto this leg.
HENRY_HUB_MONTHLY_PATH: Path = (
    Path(__file__).parents[3] / "inputs" / "raw-data" / "gas-prices"
    / "henry_hub_monthly.csv"
)

_WINTER_BASIS_CACHE: dict[Path, pd.DataFrame | None] = {}
_HH_MONTHLY_CACHE: dict[Path, dict[tuple[int, int], float]] = {}


def _load_winter_basis_frame(path: Path | None) -> pd.DataFrame | None:
    """Return the regional gas-basis frame, or ``None`` when it carries no rows.

    The CSV (``iso,year,month,hub,basis_usd_mmbtu,source``) carries only the
    ISOs whose hub leg has been sourced (currently NEISO/Algonquin), so an
    empty or absent file resolves to ``None`` (callers fall back to measured
    923). Cached per path so a multi-year run reads the file once.
    """
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
    config: ScenarioConfig, year: int, path: Path | None = None,
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


def iso_hub_monthly_gas_prices(
    config: ScenarioConfig, year: int,
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
    basis = load_winter_gas_basis(config, year, path=basis_path)
    if basis is None:
        return None
    henry_hub = _henry_hub_monthly(henry_hub_path)
    monthly = np.full(12, np.nan)
    for m in range(12):
        hh = henry_hub.get((year, m + 1))
        if hh is not None and not np.isnan(basis[m]):
            monthly[m] = hh + float(basis[m])
    if np.isnan(monthly).all():
        return None
    return monthly


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
    forecasts are unchanged. Backcast-only by construction: forward years
    have no basis rows. Mutates ``fuel_prices`` in place; idempotent.

    Args:
        fuel_prices: The ``(n_gen, T)`` delivered fuel-price array, updated
            in place for gas generators in covered months.
        fleet: Vectorized fleet attributes; ``fuel_type_idx`` selects gas.
        config: Scenario configuration supplying ``gas_hub_basis_overlay``,
            ``iso`` and ``hours``.
        year: Calendar year keying the hub-basis lookup.
        basis_path: Optional override for the basis CSV path.
    """
    if not getattr(config, "gas_hub_basis_overlay", False):
        return
    monthly = iso_hub_monthly_gas_prices(config, year, basis_path)
    if monthly is None:
        return
    hourly = _expand_monthly_to_hourly(monthly, fuel_prices.shape[1])
    covered = ~np.isnan(hourly)
    if not covered.any():
        return
    gas_rows = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX))[0]
    if gas_rows.size == 0:
        return
    fuel_prices[np.ix_(gas_rows, np.nonzero(covered)[0])] = hourly[covered]
    logger.info(
        "hub-basis overlay (%s %d): %d gas generators repriced at the "
        "measured hub-month spot in %d/12 months (winter max %.2f $/MMBtu)",
        config.iso, year, gas_rows.size,
        int((~np.isnan(monthly)).sum()), float(np.nanmax(monthly)),
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
    monthly = iso_hub_monthly_gas_prices(config, year)
    if monthly is None:
        return series
    hourly = _expand_monthly_to_hourly(monthly, hours)
    return np.where(np.isnan(hourly), series, hourly)


def resolve_fuel_prices(
    config: ScenarioConfig, fleet: FleetArrays, year: int,
    apply_monthly: bool = True,
) -> np.ndarray:
    """Return the ``(n_gen, T)`` delivered fuel price array for the fleet.

    Pricing model:

      1. **Gas** units pay the AEO Henry Hub trajectory plus the ISO basis
         differential (:func:`resolve_annual_gas_price`), optionally shaped
         by the monthly seasonality factors when ``config.gas_seasonality``
         is set — the *same* price for every gas unit in the ISO that year.
         Per-plant EIA-923 monthly gas costs are applied only when
         ``config.gas_plant_monthly_fuel_pricing`` is set (off by default).
      2. **Coal** units pay :data:`COAL_PRICE_BASE` escalated from
         :data:`START_YEAR` at :data:`COAL_PRICE_ESCALATION` per year, then
         (historical years, ``coal_plant_monthly_pricing`` on) overwritten
         by each plant's own measured EIA-923 monthly delivered cost where
         reported. Months with no reported cost keep the trajectory.

    Hydrogen turbines (``hydrogen_ct``, ``hydrogen_ccgt``) pay the
    derived hydrogen fuel cost from
    :func:`market_sim.data.hydrogen.compute_h2_fuel_cost`. Oil units
    (``oil``) pay the flat delivered distillate/residual price
    (:data:`~market_sim.config.constants.OIL_PRICE_PER_MMBTU`) and biomass
    units (``biomass``) the delivered biomass fuel cost
    (:data:`~market_sim.config.constants.BIOMASS_PRICE_PER_MMBTU`). All other
    generators carry a zero fuel price.

    When ``config.dual_fuel_switching`` is set (and ``apply_monthly`` is
    True), EIA-860 oil/gas switch-capable gas units are finally capped at
    the delivered oil price per hour (:func:`apply_dual_fuel_pricing`), so
    their marginal cost is ``min(gas_mc, oil_mc)``.

    The same code path runs both backcasts and forward projections — the
    F923 lookup simply finds nothing in a forward year and every plant
    falls through to the trajectory-based default.

    Args:
        config: Scenario configuration supplying ``iso``, ``gas_price_path``,
            ``gas_seasonality`` and ``hours``.
        fleet: Vectorized fleet attributes; ``fuel_type_idx`` selects each
            generator's fuel and ``plant_code`` keys the F923 lookup.
        year: Calendar year for which to resolve prices.

    Returns:
        A ``(n_gen, T)`` array of delivered fuel prices ($/MMBtu), where
        ``T`` is ``config.hours``.
    """
    T = config.hours
    delivered_annual = resolve_annual_gas_price(config, year)
    if config.gas_seasonality:
        gas_price_hourly = delivered_annual * _seasonal_factors(T)
    else:
        gas_price_hourly = np.full(T, delivered_annual)
    # Backcast: measured ISO-month delivered gas (EIA-923 volume-weighted)
    # replaces the trajectory + generic seasonal shape month-by-month, so
    # real winter events (PJM Jan-2024 at $5+/MMBtu) reach the merit order.
    # Months with no receipts keep the shaped trajectory value.
    if getattr(config, "gas_monthly_actuals", False):
        measured = iso_monthly_gas_prices(config, year)
        if measured is not None:
            hourly_measured = _expand_monthly_to_hourly(
                np.asarray(measured, dtype=float), T
            )
            gas_price_hourly = np.where(
                np.isnan(hourly_measured), gas_price_hourly, hourly_measured
            )

    coal_price = COAL_PRICE_BASE[config.iso] * (
        1.0 + COAL_PRICE_ESCALATION
    ) ** (year - START_YEAR)

    fuel_type_idx = fleet.fuel_type_idx
    fuel_prices = np.zeros((fleet.n_gen, T), dtype=float)
    fuel_prices[np.isin(fuel_type_idx, _GAS_FUEL_IDX)] = gas_price_hourly
    fuel_prices[fuel_type_idx == _COAL_FUEL_IDX] = coal_price

    # Oil (distillate/residual) and biomass burn at a flat delivered cost: oil
    # sits far above gas (peaker economics), biomass near cheap-coal parity.
    # Neither has a commodity trajectory or F923 plant-monthly override here.
    fuel_prices[fuel_type_idx == _OIL_FUEL_IDX] = OIL_PRICE_PER_MMBTU
    fuel_prices[fuel_type_idx == _BIOMASS_FUEL_IDX] = BIOMASS_PRICE_PER_MMBTU

    # Hydrogen turbines burn green H2 whose cost is derived from renewable
    # LCOE and electrolyzer efficiency rather than a commodity market.
    if np.any(np.isin(fuel_type_idx, _HYDROGEN_FUEL_IDX)):
        h2_price = compute_h2_fuel_cost(year, config, config.iso)
        fuel_prices[np.isin(fuel_type_idx, _HYDROGEN_FUEL_IDX)] = h2_price

    # Callers that set a coal-supply base (lignite/PRB) before the monthly
    # overwrite pass apply_monthly=False and call
    # apply_plant_monthly_fuel_prices themselves afterwards, so the actual
    # EIA-923 monthly cost takes precedence over the supply-class base —
    # then the hub-basis overlay (the measured constrained-hub spot
    # supersedes plant receipts in covered months), and finally the
    # dual-fuel min, which must see the final gas price so oil parity caps
    # the blown-out winter hub price.
    if apply_monthly:
        apply_plant_monthly_fuel_prices(fuel_prices, fleet, config, year)
        apply_hub_basis_overlay(fuel_prices, fleet, config, year)
        apply_dual_fuel_pricing(fuel_prices, fleet, config, year)

    return fuel_prices


def dual_fuel_oil_price_series(
    config: ScenarioConfig, year: int,
    monthly_costs_path: Path | None = None,
) -> np.ndarray:
    """Return the ``(T,)`` delivered oil price ($/MMBtu) for dual-fuel parity.

    The measured ISO-month EIA-923 Petroleum series
    (:func:`iso_monthly_oil_prices`) expanded to hours, with unreported
    months — and years with no F923 data at all (forward years) — filled
    from the flat cited default
    (:data:`~market_sim.config.constants.OIL_PRICE_PER_MMBTU`).
    """
    monthly = iso_monthly_oil_prices(config, year, monthly_costs_path)
    if monthly is None:
        return np.full(config.hours, OIL_PRICE_PER_MMBTU, dtype=float)
    filled = np.where(
        np.isnan(monthly), OIL_PRICE_PER_MMBTU, np.asarray(monthly, dtype=float)
    )
    return _expand_monthly_to_hourly(filled, config.hours)


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
    oil burn hours under-count CO2 slightly).

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
    capable = dual_fuel_plant_groups()
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
            config.iso, year, n_capped, mw_capped,
        )


def apply_plant_monthly_fuel_prices(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    monthly_costs_path: str | Path | None = None,
) -> None:
    """Overwrite per-generator fuel prices with F923 monthly plant costs.

    For each eligible coal / oil generator whose ``plant_code`` matches a
    plant-month in the EIA-923 monthly cost table for ``year``, the
    generator's hourly fuel price is set to the plant's measured
    monthly delivered cost (broadcast to hours by the calendar month
    map). Months with no reported price preserve the per-fuel default
    already in ``fuel_prices``, so a coal plant whose January cost is
    suppressed keeps the COAL_PRICE_BASE trajectory for January and the
    F923 measured cost for the other 11 months.

    **Gas is excluded by default.** Gas generators are skipped unless
    ``config.gas_plant_monthly_fuel_pricing`` is set, so every gas unit
    keeps the uniform Henry Hub + basis price from :func:`resolve_fuel_prices`
    and same-zone units are not split by patchy EIA-923 reporting. Coal can
    likewise be held on the flat lignite/PRB average via
    ``config.coal_plant_monthly_pricing = False``.

    **Nearby-plant fallback.** When ``config.nearby_fuel_price_fallback``
    is set, a month with no reported cost for the plant is filled — before
    the per-fuel trajectory default — from the quantity-weighted average of
    the *other* generators that did report: the plant's own state first
    (when at least ``config.nearby_fuel_price_min_state_plants`` plants
    reported in that state-month), otherwise the plant's model zone. The
    averages are restricted to the current ISO's fleet, so a PJM backcast
    never inherits an ERCOT or MISO delivered cost. This is off by default,
    so ERCOT — whose plants overwhelmingly report — is unchanged.

    A missing parquet (forward years or untracked ISO) is a no-op: every
    generator keeps the per-fuel default. The same is true for plants
    outside the F923 sample when the fallback is off, per the project's
    "forward = plant-class/zone average" requirement.

    Mutates ``fuel_prices`` in place.

    Args:
        fuel_prices: The ``(n_gen, T)`` per-fuel default fuel-price array,
            updated in place with plant-specific monthly prices.
        fleet: Vectorized fleet attributes carrying ``plant_code``,
            ``fuel_type_idx`` and (for the fallback) ``state`` / ``zone_idx``.
        config: Scenario configuration supplying ``hours``,
            ``coal_plant_monthly_pricing`` and the nearby-fallback knobs.
        year: Calendar year keying the F923 monthly lookup.
        monthly_costs_path: Optional override for the F923 parquet path.
    """
    costs = _load_monthly_cache(
        Path(monthly_costs_path) if monthly_costs_path else None
    )
    if costs is None or year not in available_years(costs):
        return

    T = config.hours
    month_idx = _month_index(T)
    use_nearby = bool(getattr(config, "nearby_fuel_price_fallback", False))
    nearby = _NearbyFuelPrices(costs, year, fleet, config) if use_nearby else None
    states = fleet.state

    grids: dict[str, dict[int, np.ndarray]] = {}
    n_overwrites = 0
    n_nearby = 0
    for g in range(fleet.n_gen):
        fuel_name = _fuel_name(fleet.fuel_type_idx[g])
        fuel_group = _F923_FUEL_GROUP_BY_FUEL.get(fuel_name)
        if fuel_group is None:
            continue
        # Coal monthly pricing can be switched off (config) to hold all coal
        # on the flat annual lignite/PRB average.
        if fuel_name == "coal" and not getattr(
            config, "coal_plant_monthly_pricing", True
        ):
            continue
        # Gas per-plant monthly pricing is OFF by default: every gas unit pays
        # the uniform Henry Hub + basis price set upstream, so patchy EIA-923
        # reporting does not split units in the same zone. Set
        # ``gas_plant_monthly_fuel_pricing`` to restore per-plant gas costs.
        if fuel_group == "Natural Gas" and not getattr(
            config, "gas_plant_monthly_fuel_pricing", False
        ):
            continue
        grid = grids.get(fuel_group)
        if grid is None:
            grid = plant_month_price_grid(costs, year, fuel_group)
            grids[fuel_group] = grid

        plant_code = int(fleet.plant_code[g])
        own = grid.get(plant_code) if plant_code > 0 else None
        reported = ~np.isnan(own) if own is not None else np.zeros(12, dtype=bool)

        # 1) The plant's own measured months win outright.
        if own is not None and reported.any():
            for m in np.nonzero(reported)[0]:
                mask = month_idx == m
                if mask.any():
                    fuel_prices[g, mask] = own[m]
            n_overwrites += 1

        # 2) Nearby-plant fallback fills the still-unreported months.
        if nearby is not None and not reported.all():
            st = str(states[g]) if states is not None else ""
            fill = nearby.month_prices(fuel_group, st, int(fleet.zone_idx[g]))
            applied = False
            for m in np.nonzero(~reported)[0]:
                v = fill[m]
                if np.isnan(v):
                    continue
                mask = month_idx == m
                if mask.any():
                    fuel_prices[g, mask] = v
                    applied = True
            if applied:
                n_nearby += 1

    if n_overwrites or n_nearby:
        logger.info(
            "F923 fuel costs for %d: %d generators priced from their own "
            "plant, %d gap-filled from nearby (state/zone) plants",
            year, n_overwrites, n_nearby,
        )


class _NearbyFuelPrices:
    """ISO-restricted state/zone "nearby plant" fuel-cost fallback grids.

    Lazily builds, per EIA-923 ``fuel_group``, the quantity-weighted monthly
    delivered cost of the current ISO's reporting plants aggregated two ways:
    by USPS state (with a reporter count) and by model zone index. A plant
    missing its own cost in a month is filled from its state mean when the
    state cleared the sample floor, otherwise from its zone mean. Both are
    drawn only from the ISO's own fleet, so no cross-ISO price leaks in.
    """

    def __init__(
        self,
        costs: pd.DataFrame,
        year: int,
        fleet: FleetArrays,
        config: ScenarioConfig,
    ) -> None:
        self._year = year
        self._min_state = int(
            getattr(config, "nearby_fuel_price_min_state_plants", 2)
        )
        iso_plants = {int(p) for p in fleet.plant_code if int(p) > 0}
        self._plant_to_zone = {
            int(p): int(z)
            for p, z in zip(fleet.plant_code, fleet.zone_idx)
            if int(p) > 0
        }
        self._iso_costs = costs[
            (costs["year"] == year) & (costs["plant_id"].isin(iso_plants))
        ]
        # Per fuel group: (state_price, state_count, zone_price) grids.
        self._cache: dict[str, tuple[dict, dict, dict]] = {}

    def _grids(self, fuel_group: str) -> tuple[dict, dict, dict]:
        cached = self._cache.get(fuel_group)
        if cached is not None:
            return cached
        sub = self._iso_costs[self._iso_costs["fuel_group"] == fuel_group]
        state_price, state_count = state_month_price_grid(
            sub, self._year, fuel_group
        )
        zone_price: dict[int, np.ndarray] = {}
        if not sub.empty:
            z = sub.assign(
                zone=sub["plant_id"].map(self._plant_to_zone),
                weighted=sub["price_per_mmbtu"] * sub["quantity"],
            ).dropna(subset=["zone"])
            for zone, grp in z.groupby("zone", sort=False):
                wsum = np.zeros(12, dtype=float)
                qsum = np.zeros(12, dtype=float)
                for _, row in grp.iterrows():
                    m = int(row["month"]) - 1
                    if 0 <= m < 12:
                        wsum[m] += float(row["weighted"])
                        qsum[m] += float(row["quantity"])
                with np.errstate(invalid="ignore", divide="ignore"):
                    zone_price[int(zone)] = np.where(
                        qsum > 0.0, wsum / qsum, np.nan
                    )
        result = (state_price, state_count, zone_price)
        self._cache[fuel_group] = result
        return result

    def month_prices(
        self, fuel_group: str, state: str, zone_idx: int
    ) -> np.ndarray:
        """Return a length-12 fill price array (NaN where no nearby data)."""
        state_price, state_count, zone_price = self._grids(fuel_group)
        out = np.full(12, np.nan, dtype=float)
        sp = state_price.get(state)
        if sp is not None:
            sc = state_count.get(state)
            ok = (sc >= self._min_state) & ~np.isnan(sp) if sc is not None \
                else ~np.isnan(sp)
            out[ok] = sp[ok]
        zp = zone_price.get(int(zone_idx))
        if zp is not None:
            need = np.isnan(out) & ~np.isnan(zp)
            out[need] = zp[need]
        return out


def _fuel_name(fuel_idx: int) -> str:
    """Return the fuel-type name for a fuel-type index, or ``""``."""
    from market_sim.data.fleet import FUEL_TYPE_NAMES
    idx = int(fuel_idx)
    if 0 <= idx < len(FUEL_TYPE_NAMES):
        return FUEL_TYPE_NAMES[idx]
    return ""


# --- CAMPD coal delivered fuel cost ($/MMBtu), by year and supply type ------
# Mine-mouth lignite: $1.45 flat across 2023-2025, then escalates at general
# inflation through the modeling window. PRB-by-rail: measured delivered cost
# for 2023-2025; from 2026 a forward curve decomposes the 2023-2025 average
# into commodity (42%), diesel-driven rail freight (12%) and non-diesel rail
# freight (46%). The commodity component holds flat through 2030 then declines
# 1.5%/yr as coal demand falls; non-diesel rail escalates at inflation; the
# diesel-rail component is held at its 2025 level (the model carries no
# forward diesel price curve). Source: operator/EIA cost data, user calibration.
_LIGNITE_PRICE_2023_25: float = 1.45
_PRB_PRICE_CALIBRATION: dict[int, float] = {2023: 2.15, 2024: 2.00, 2025: 2.00}
_PRB_COMMODITY_SHARE: float = 0.42
_PRB_RAIL_DIESEL_SHARE: float = 0.12
_PRB_RAIL_NONDIESEL_SHARE: float = 0.46
_PRB_COMMODITY_DECLINE: float = 0.015      # annual, from 2031 as demand falls
_PRB_COMMODITY_FLAT_THROUGH: int = 2030


def _build_coal_price_trajectories() -> tuple[dict[int, float], dict[int, float]]:
    """Return ``(lignite, prb)`` delivered-cost dicts spanning 2023-END_YEAR."""
    lignite: dict[int, float] = {}
    prb: dict[int, float] = {}
    for y in (2023, 2024, 2025):
        lignite[y] = _LIGNITE_PRICE_2023_25
        prb[y] = _PRB_PRICE_CALIBRATION[y]

    avg_prb = sum(_PRB_PRICE_CALIBRATION.values()) / 3.0
    commodity_base = _PRB_COMMODITY_SHARE * avg_prb
    rail_diesel = _PRB_RAIL_DIESEL_SHARE * avg_prb        # held flat forward
    rail_nondiesel_base = _PRB_RAIL_NONDIESEL_SHARE * avg_prb
    for y in range(2026, END_YEAR + 1):
        lignite[y] = (
            _LIGNITE_PRICE_2023_25 * (1.0 + INFLATION_RATE) ** (y - 2025)
        )
        if y <= _PRB_COMMODITY_FLAT_THROUGH:
            commodity = commodity_base
        else:
            commodity = commodity_base * (1.0 - _PRB_COMMODITY_DECLINE) ** (
                y - _PRB_COMMODITY_FLAT_THROUGH
            )
        rail_nondiesel = (
            rail_nondiesel_base * (1.0 + INFLATION_RATE) ** (y - 2026)
        )
        prb[y] = commodity + rail_diesel + rail_nondiesel
    return lignite, prb


COAL_PRICE_LIGNITE_BY_YEAR, COAL_PRICE_PRB_BY_YEAR = (
    _build_coal_price_trajectories()
)


@lru_cache(maxsize=1)
def _prb_monthly_actuals() -> dict[int, np.ndarray]:
    """Return ``{year: (12,) $/MMBtu}`` measured PRB delivered cost by month.

    Quantity-weighted across the EIA-923 coal-cost reporters whose plant is
    tagged PRB-by-rail in :data:`market_sim.data.fleet.COAL_PLANT_SUPPLY`
    (ERCOT: Fayette and J K Spruce — the merchant fleet's receipts are
    confidential). The series proxies the delivered PRB cost for the
    *non-reporting* PRB plants in :func:`apply_coal_supply_pricing`; the
    reporters themselves are overwritten with their own plant-months by
    :func:`apply_plant_monthly_fuel_prices` afterwards. Months without a
    report carry the year's mean of the reported months. Lignite has no
    usable monthly proxy (the only reporter, San Miguel, burns its own
    high-cost mine) and stays on the flat annual trajectory. Returns an
    empty dict when the F923 parquet is absent.
    """
    costs = _load_monthly_cache(None)
    if costs is None:
        return {}
    from market_sim.data.fleet import COAL_PLANT_SUPPLY
    prb_plants = {p for p, s in COAL_PLANT_SUPPLY.items() if s == "prb"}
    sub = costs[
        costs["plant_id"].isin(prb_plants)
        & (costs["fuel_group"] == "Coal")
        & costs["price_per_mmbtu"].notna()
        & (costs["quantity"] > 0)
    ]
    out: dict[int, np.ndarray] = {}
    for year, rows in sub.groupby("year"):
        monthly = np.full(12, np.nan)
        for month, mrows in rows.groupby("month"):
            monthly[int(month) - 1] = float(np.average(
                mrows["price_per_mmbtu"], weights=mrows["quantity"]
            ))
        if np.isnan(monthly).all():
            continue
        monthly[np.isnan(monthly)] = np.nanmean(monthly)
        out[int(year)] = monthly
    return out


def apply_coal_supply_pricing(
    fuel_prices: np.ndarray,
    generators: list,
    config: ScenarioConfig,
    year: int,
) -> None:
    """Reprice CAMPD coal generators by their plant fuel-supply type.

    Mine-mouth lignite and PRB-by-rail generators bid at their per-year
    delivered fuel cost — :data:`COAL_PRICE_LIGNITE_BY_YEAR` and
    :data:`COAL_PRICE_PRB_BY_YEAR`. The PRB delivered cost is scaled by
    ``coal_prb_contract_passthrough``: take-or-pay rail/coal contracts
    leave much of the delivered tonnage sunk, so the marginal dispatch bid
    sits below delivered cost. Coal generators with no ``coal_supply`` tag
    (the legacy fleet, or an unmapped plant), or a run year outside the
    coal price trajectory, keep the generic price already in
    ``fuel_prices``.

    Mutates ``fuel_prices`` in place.

    Args:
        fuel_prices: The ``(n_gen, T)`` delivered fuel-price array to update,
            aligned row-for-row with ``generators``.
        generators: The dispatch fleet.
        config: Scenario configuration supplying ``coal_prb_contract_passthrough``.
        year: Calendar year, selecting the coal price trajectory entry.
    """
    lignite = COAL_PRICE_LIGNITE_BY_YEAR.get(year)
    prb_delivered = COAL_PRICE_PRB_BY_YEAR.get(year)
    if lignite is None or prb_delivered is None:
        return  # year outside the coal trajectory — keep the generic price

    # PRB base: the measured monthly reporter series for historical years
    # (see _prb_monthly_actuals), expanded hour-by-hour; the flat annual
    # trajectory where no reports exist (forward years). Reporting plants
    # are overwritten with their own months downstream.
    monthly = _prb_monthly_actuals().get(year)
    if monthly is not None:
        prb_price = monthly[_month_index(fuel_prices.shape[1])]
    else:
        prb_price = prb_delivered

    price_by_supply = {
        "lignite": lignite,
        "prb": prb_price * config.coal_prb_contract_passthrough,
    }
    for g_idx, gen in enumerate(generators):
        price = price_by_supply.get(getattr(gen, "coal_supply", ""))
        if price is not None:
            fuel_prices[g_idx, :] = price


def resolve_nox_price(config: ScenarioConfig) -> float:
    """Return the NOx price ($/ton NOx) for the given scenario.

    Args:
        config: Scenario configuration supplying ``nox_price``.

    Returns:
        The NOx price in $/ton NOx.
    """
    return config.nox_price
