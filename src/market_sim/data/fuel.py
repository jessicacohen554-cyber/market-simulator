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
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import (
    BIOMASS_PRICE_PER_MMBTU,
    CAISO_CITYGATE_TRANSPORT_ADDER,
    COAL_PRICE_BASE,
    COAL_PRICE_ESCALATION,
    COAL_PRICE_TRAJECTORIES,
    END_YEAR,
    GAS_BASIS_DIFFERENTIAL,
    GAS_MONTHLY_SEASONALITY,
    HENRY_HUB_TRAJECTORIES,
    HOURS_PER_YEAR,
    INFLATION_RATE,
    LIGNITE_PRICE_2023_25,
    NUCLEAR_FUEL_PRICE_HISTORICAL,
    OIL_PRICE_PER_MMBTU,
    OIL_PRICE_TRAJECTORIES,
    PRB_COMMODITY_DECLINE,
    PRB_COMMODITY_FLAT_THROUGH,
    PRB_COMMODITY_SHARE,
    PRB_PRICE_BY_YEAR,
    PRB_RAIL_DIESEL_SHARE,
    PRB_RAIL_NONDIESEL_SHARE,
    START_YEAR,
)
from market_sim.config.paths import GAS_PRICES_DIR, RAW_DATA_DIR
from market_sim.config.scenarios import COAL_SIGMOID_DEFAULTS, ScenarioConfig
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

# Floor for a delivered gas price after a zonal-basis shift: a deep negative
# regional basis (e.g. a cheap upstate index) can never drive the marginal fuel
# cost to zero or below. Well under any real delivered cost, so it only guards
# the degenerate tail.
_GAS_PRICE_FLOOR: float = 0.10

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

# Fuel-type integer code for nuclear units, which pay the derived
# EIA-uranium-marketing $/MMBtu fuel-cycle cost (:func:`resolve_nuclear_fuel_price`).
_NUCLEAR_FUEL_IDX: int = FUEL_TYPE_MAP["nuclear"]

# Fuel price ($/MMBtu) for non-fuel-burning units (e.g. wind, solar,
# hydro, imports), which carry no commodity fuel cost in this model.
_ZERO_FUEL_PRICE: float = 0.0

# Calendar days per month for a non-leap year (sums to 365 -> 8760 hours).
_DAYS_IN_MONTH: tuple[int, ...] = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

# Opt-in clean-data read path. When the ``MARKET_SIM_USE_CLEAN`` environment flag
# is truthy, the delivered fuel-price loaders source their series from the
# curated ``data/clean`` tree via the frozen ``clean_io.read_clean`` seam instead
# of the raw ``data/raw/gas-prices`` CSVs. OFF by default: the raw path stays the
# contract, so existing runs and calibrations are byte-identical unless a caller
# opts in (and the clean path falls back to raw when the clean tree is absent).
_USE_CLEAN_ENV: str = "MARKET_SIM_USE_CLEAN"
_USE_CLEAN_TRUTHY: frozenset[str] = frozenset({"1", "true", "yes", "on"})


def _use_clean_data() -> bool:
    """Whether the opt-in clean-data read path is enabled (default ``False``)."""
    return os.environ.get(_USE_CLEAN_ENV, "").strip().lower() in _USE_CLEAN_TRUTHY


def _hold_flat_extrapolate(trajectory: dict[int, float], year: int) -> float:
    """Return ``trajectory[year]``, holding flat at the nearest known year.

    ``year`` beyond the trajectory's last knot holds the LAST value flat in
    real terms — no compounding tail. This replaces the prior
    last-year-over-year-ratio extrapolation (a silent, unbounded, uncited
    driver — P-1D, CLAUDE.md rule 23): a naive compounding tail invents a
    forever-rising or forever-falling price the source data says nothing
    about, whereas holding the last real, cited value flat only ever asserts
    what the data actually supports.

    ``year`` before the trajectory's first knot, or inside an interior gap
    (e.g. a rule-22 holdout-quarantine year omitted from a hindcast path),
    holds flat at the nearest EARLIER known year (or, if none exists, the
    earliest known year) — never a backward-compounding extrapolation.
    """
    if year in trajectory:
        return trajectory[year]
    last_year = max(trajectory)
    if year > last_year:
        return trajectory[last_year]
    earlier = [y for y in trajectory if y < year]
    if earlier:
        return trajectory[max(earlier)]
    return trajectory[min(trajectory)]


def resolve_annual_gas_price(config: ScenarioConfig, year: int) -> float:
    """Return the delivered annual gas price ($/MMBtu) for the scenario year.

    The price is the AEO Henry Hub trajectory value for ``year`` and the
    scenario's ``gas_price_path``, plus the ISO's basis differential::

        delivered = HENRY_HUB_TRAJECTORIES[path][year] + basis

    Years beyond the trajectory's last entry hold the last real value flat
    (:func:`_hold_flat_extrapolate`) — no compounding tail. This annual
    (seasonality-free) price is the one capacity new-entry LCOE screening
    should charge gas units, so dispatch and capacity evolution see the same
    gas cost for a year.

    When ``config.gas_price_override`` is set the trajectory lookup is
    bypassed entirely: the override is treated as the measured Henry Hub
    price and the ISO basis differential is added to it, so a calibration
    backcast charges the year's actual delivered gas cost.

    ``config.gas_price_factor`` (default 1.0) multiplies the resolved
    trajectory value before the basis differential is added -- the PB-1
    forecast-only gas-price uncertainty lever (docs/handoffs/probability-
    bounds-plan-2026-07.md §2.1/§2.2). It never applies to
    ``gas_price_override``, and ``ScenarioConfig.__post_init__`` asserts it
    stays 1.0 in backcast mode, so it can never become a backcast tuning
    channel (rule 13).

    Args:
        config: Scenario configuration supplying ``iso``,
            ``gas_price_path``, ``gas_price_factor``, and an optional
            ``gas_price_override``.
        year: Calendar year to resolve.

    Returns:
        The delivered annual gas price in $/MMBtu.
    """
    basis = GAS_BASIS_DIFFERENTIAL.get(config.iso, 0.0)
    if config.gas_price_override is not None:
        return config.gas_price_override + basis

    trajectory = HENRY_HUB_TRAJECTORIES[config.gas_price_path]
    henry_hub = _hold_flat_extrapolate(trajectory, year)

    return henry_hub * config.gas_price_factor + basis


def resolve_annual_coal_price(config: ScenarioConfig, year: int) -> float:
    """Return the delivered annual coal price ($/MMBtu) for an ISO/year.

    Anchors on the ISO's own :data:`COAL_PRICE_BASE` level (each ISO's basin
    economics — ERCOT lignite/PRB, PJM Appalachian, MISO PRB+ILB — are
    genuinely different delivered costs a single national series can't
    resolve) and escalates it by the REAL growth ratio of the AEO2025
    national delivered-coal trajectory (:data:`COAL_PRICE_TRAJECTORIES`,
    ``config.coal_price_path``) from ``START_YEAR`` to ``year``, holding flat
    beyond the trajectory's last knot (:func:`_hold_flat_extrapolate`). This
    replaces the flat, uncited :data:`COAL_PRICE_ESCALATION` (1%/yr) forward
    SHAPE with the AEO's modeled coal-supply dynamics, while preserving each
    ISO's own anchor level (P-1D, CLAUDE.md rules 14/23).
    """
    trajectory = COAL_PRICE_TRAJECTORIES[config.coal_price_path]
    anchor_year = min(trajectory)
    anchor_value = _hold_flat_extrapolate(trajectory, anchor_year)
    year_value = _hold_flat_extrapolate(trajectory, year)
    growth_ratio = year_value / anchor_value
    return COAL_PRICE_BASE[config.iso] * growth_ratio


def resolve_annual_oil_price(config: ScenarioConfig, year: int) -> float:
    """Return the delivered annual oil price ($/MMBtu) for a forecast year.

    Forecast years use the AEO2025 distillate+residual blend trajectory
    (:data:`OIL_PRICE_TRAJECTORIES`, ``config.oil_price_path``), holding flat
    beyond its last knot (:func:`_hold_flat_extrapolate`). Backcast callers
    (measured EIA-923 receipts, :func:`dual_fuel_oil_price_series`) and any
    year outside the trajectory's range keep the flat
    :data:`OIL_PRICE_PER_MMBTU` fallback — this function is only consulted
    for the annual forecast default in :func:`resolve_fuel_prices`.
    """
    trajectory = OIL_PRICE_TRAJECTORIES[config.oil_price_path]
    if year < min(trajectory):
        return OIL_PRICE_PER_MMBTU
    return _hold_flat_extrapolate(trajectory, year)


def resolve_nuclear_fuel_price(config: ScenarioConfig, year: int) -> float:
    """Return the delivered nuclear fuel cost ($/MMBtu) for a year.

    ``config.nuclear_fuel_price_override`` (e.g. a sensitivity case), when
    set, is returned as-is. Otherwise the EIA-uranium-marketing-derived
    series (:data:`NUCLEAR_FUEL_PRICE_HISTORICAL`) holds flat beyond its last
    (2024) real-dollar value (:func:`_hold_flat_extrapolate`) — neither EIA
    nor AEO publishes a forward U3O8/SWU trajectory (P-1D, CLAUDE.md rule 23;
    replaces the prior ``$0/MMBtu`` non-fuel-burning default).
    """
    override = getattr(config, "nuclear_fuel_price_override", None)
    if override is not None:
        return float(override)
    return _hold_flat_extrapolate(NUCLEAR_FUEL_PRICE_HISTORICAL, year)


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
        full_year[hour : hour + hours_in_month] = GAS_MONTHLY_SEASONALITY[month]
        hour += hours_in_month
    if hours <= HOURS_PER_YEAR:
        return full_year[:hours]
    # Multi-year horizons repeat the annual shape.
    reps = -(-hours // HOURS_PER_YEAR)
    return np.tile(full_year, reps)[:hours]


def gas_seasonal_shape(config, year: int, hours: int) -> np.ndarray:
    """Return the ``(hours,)`` monthly gas-shape factors the merit order uses.

    Default: the generic climatological :data:`GAS_MONTHLY_SEASONALITY`
    (:func:`_seasonal_factors`). When ``config.gas_hh_monthly_shape`` is set
    and the year has a complete measured Henry Hub monthly series
    (:func:`_henry_hub_monthly`), the MEASURED monthly shape replaces it:
    ``factor_m = HH_m / mean_hours(HH_year)`` — hour-weighted so the shaped
    hourly series' annual mean equals the trusted annual level exactly. The
    LEVEL stays the annual override/trajectory (never the receipt-biased
    EIA-923 sample the Run-77 ERCOT backport rejected); only the month-to-month
    SHAPE is measured — the reconciled variant that postmortem named. A
    measured commodity-price input in the admissible class (delivered fuel
    prices, CLAUDE.md #12): it regenerates for a forward year (futures-curve /
    seasonal-normal shape via the generic fallback) and responds to changed
    conditions (a mild winter's cheap Feb reaches the merit order). Years
    without 12 measured months fall back to the generic shape unchanged.
    """
    if getattr(config, "gas_hh_monthly_shape", False):
        hh = _henry_hub_monthly(None)
        monthly = np.array(
            [hh.get((int(year), m), np.nan) for m in range(1, 13)], dtype=float
        )
        if not np.isnan(monthly).any():
            month_hours = np.array(_DAYS_IN_MONTH, dtype=float) * 24.0
            level = float((monthly * month_hours).sum() / month_hours.sum())
            if level > 0:
                factors = np.repeat(monthly / level, (month_hours).astype(int))
                if hours <= HOURS_PER_YEAR:
                    return factors[:hours]
                reps = -(-hours // HOURS_PER_YEAR)
                return np.tile(factors, reps)[:hours]
    return _seasonal_factors(hours)


# Coal supply tag (coal_supply_class / COAL_PLANT_SUPPLY vocabulary) -> the
# ScenarioConfig field stem of its sigmoid params. "prb_follower" is the
# ERCOT tiered low-must-run tier of the prb curve, not a supply tag.
_COAL_SIGMOID_FIELD_STEM: dict[str, str] = {
    "prb": "prb_passthrough",
    "prb_follower": "prb_follower",
    "subbituminous": "sub_passthrough",
    "bituminous": "bit_passthrough",
    "lignite": "lignite_passthrough",
    "waste": "waste_passthrough",
}

_COAL_SIGMOID_PARAMS = ("floor", "ceil", "gas_mid", "gas_slope")


def coal_sigmoid_params(config: ScenarioConfig, supply: str) -> dict[str, float] | None:
    """Resolve the sigmoid params for one ``(config.iso, supply)`` pair.

    Starts from the region-dependent ``COAL_SIGMOID_DEFAULTS`` entry for the
    config's ISO, then overlays any explicitly-set (non-None) ScenarioConfig
    ``coal_<supply>_passthrough_*`` field — the CLI tuning path. Returns
    None when the resolved set is incomplete (no table entry and not fully
    specified by explicit fields): that ISO/supply has no characterized
    curve and must fall back to the flat passthrough rather than borrow
    another region's economics.
    """
    stem = _COAL_SIGMOID_FIELD_STEM[supply]
    params = dict(COAL_SIGMOID_DEFAULTS.get((config.iso.upper(), supply), {}))
    for p in _COAL_SIGMOID_PARAMS:
        v = getattr(config, f"coal_{stem}_{p}", None)
        if v is not None:
            params[p] = v
    if any(p not in params for p in _COAL_SIGMOID_PARAMS):
        return None
    return params


def coal_passthrough_series(
    config: ScenarioConfig, year: int, hours: int, supply: str
) -> "float | np.ndarray":
    """Return one coal supply chain's above-must-run fuel passthrough.

    Flat fallback when the supply's ``coal_<supply>_passthrough_sigmoid``
    toggle is off, or when no sigmoid is characterized for this
    ``(config.iso, supply)`` (see :func:`coal_sigmoid_params`): the flat
    ``config.coal_prb_passthrough`` scalar for prb, full cost (``1.0``) for
    every other supply.

    When the sigmoid applies, returns an ``(hours,)`` logistic of the
    monthly delivered gas price ($/MMBtu) rising from the supply's ``floor``
    (cheap gas — coal needs a fuel discount to clear against cheap gas CC)
    to its ``ceil`` (dear gas — full cost, or a markup > 1.0 that
    suppresses over-run), centred at ``gas_mid`` with ``gas_slope`` per
    $/MMBtu. Keying off the monthly gas price tracks the merit-order
    crossover: infra-marginal coal's gap to close scales with gas.
    """
    stem = _COAL_SIGMOID_FIELD_STEM[supply]
    flat = config.coal_prb_passthrough if supply == "prb" else 1.0
    if not getattr(config, f"coal_{stem}_sigmoid", False):
        return flat
    params = coal_sigmoid_params(config, supply)
    if params is None:
        return flat
    return _sigmoid_passthrough(
        _gas_series(config, year, hours),
        params["floor"],
        params["ceil"],
        params["gas_mid"],
        params["gas_slope"],
    )


def coal_passthrough_by_supply(
    config: ScenarioConfig, year: int, hours: int
) -> dict[str, "float | np.ndarray"]:
    """Return ``{supply tag: passthrough}`` for every sigmoid-capable supply.

    The routing table :func:`market_sim.data.fleet.campd_tranche_fuel_frac`
    consumes: each coal tranche looks up its own ``coal_supply`` tag, so a
    bituminous plant can never receive the prb curve and vice-versa. Tags
    without an entry (e.g. unclassified "") pass full fuel cost.
    """
    return {
        supply: coal_passthrough_series(config, year, hours, supply)
        for supply in ("prb", "subbituminous", "bituminous", "lignite", "waste")
    }


def prb_follower_passthrough_series(
    config: ScenarioConfig, year: int, hours: int
) -> "float | np.ndarray":
    """Return the load-follower-tier PRB passthrough series (gas-keyed).

    Used only when ``config.coal_prb_passthrough_tiered`` is set, for PRB
    plants whose per-plant must-run floor is at or below
    ``coal_prb_follower_mustrun_max`` — the low-floor units that cycle as
    load-followers rather than baseload price-takers. Same logistic form as
    the baseload tier but its own ``coal_prb_follower_*`` parameters
    (per-ISO key ``"prb_follower"``); falls back to the baseload prb curve
    when no follower curve is characterized.
    """
    params = coal_sigmoid_params(config, "prb_follower")
    if params is None:
        return coal_passthrough_series(config, year, hours, "prb")
    return _sigmoid_passthrough(
        _gas_series(config, year, hours),
        params["floor"],
        params["ceil"],
        params["gas_mid"],
        params["gas_slope"],
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
        series = gas * gas_seasonal_shape(config, year, hours)
    else:
        series = np.full(hours, gas, dtype=float)
    if getattr(config, "gas_monthly_actuals", False):
        measured = iso_monthly_gas_prices(config, year)
        if measured is not None:
            hourly_measured = _expand_monthly_to_hourly(
                np.asarray(measured, dtype=float), hours
            )
            series = np.where(np.isnan(hourly_measured), series, hourly_measured)
    series = _hub_overlay_series(series, config, year, hours)
    # ERCOT zonal gas basis on: the merit order prices gas at the measured
    # EP-anchored level (Henry Hub + electric-power basis), not the flat -0.50
    # scalar (see apply_ercot_zonal_gas_basis). The coal passthrough sigmoid keys
    # off THIS series to set PRB coal's offer, so it must see the same level —
    # otherwise PRB coal keeps the deep cheap-gas discount the -0.50 reference
    # implies while the real gas it competes against is ~$0.4-0.5/MMBtu dearer,
    # and coal over-runs. Add the (flat) level correction; the per-zone spread is
    # left out (ERCOT coal is concentrated in the small-spread North/Northeast).
    if getattr(config, "ercot_zonal_gas_basis", False) and config.iso == "ERCOT":
        ep_basis = ercot_electric_power_gas_basis(year)
        if ep_basis is not None:
            series = series + (ep_basis - GAS_BASIS_DIFFERENTIAL.get("ERCOT", 0.0))
    # The coal sigmoid's gas key deliberately stays at the MONTHLY level and
    # does NOT take the gas_daily_shape within-month swing the gas units bid
    # at (resolve_fuel_prices applies that there). The sigmoid models a coal
    # fuel contract's discount posture — take-or-pay / mine-mouth / rail
    # commitments whose delivered cost, and hence how deep a tranche
    # discounts to hold merit, reprices on a monthly (contract) timescale,
    # not daily spot. Keying it daily made coal offers whipsaw in lockstep
    # with every Henry Hub trough, which (a) erased the coal-vs-gas flip
    # days the daily shape exists to resolve — the merit gap never opened —
    # and (b) showed up directly as the miso-51 C4 2024 coal dispatch-corr
    # FAIL (r=0.856) and C3b 2023/24 monthly-shape FAILs; real coal dispatch
    # is contract/inflexibility-smoothed. One mechanism per timescale: the
    # gas units see the daily price, the coal contract posture sees the
    # month. (miso-52; the daily factors were briefly applied here between
    # the gas_daily_shape intro and this correction.)
    return series


def _sigmoid_passthrough(
    gas_series: np.ndarray, floor: float, ceil: float, mid: float, slope: float
) -> np.ndarray:
    """Logistic passthrough rising from ``floor`` to ``ceil`` in gas price."""
    return floor + (ceil - floor) / (1.0 + np.exp(-slope * (gas_series - mid)))


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
        full[hour : hour + hours_in_month] = month_idx
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


def _expand_monthly_to_hourly(monthly: np.ndarray, hours: int) -> np.ndarray:
    """Broadcast a length-12 monthly price array onto the hourly horizon."""
    return monthly[_month_index(hours)]


def _iso_monthly_fuel_prices(
    config: ScenarioConfig,
    year: int,
    fuel_group: str,
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
    config: ScenarioConfig,
    year: int,
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
    config: ScenarioConfig,
    year: int,
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
WINTER_GAS_BASIS_PATH: Path = RAW_DATA_DIR / "gas_basis_by_iso_month.csv"

# Measured NYISO per-zone annual gas-hub prices (NYISO State of the Market
# reports, Potomac Economics, Figure A-6 annual averages). NYISO prices each
# region off a different pipeline index — the cheap western/Central zones on
# Tenn Z4 200L / Niagara, the Capital/Hudson and Long Island zones on Iroquois
# Z2 / Tenn Z6, and New York City on Transco Z6 (NY) — so the marginal gas unit
# in the east costs persistently more than in the west even when the system
# delivered-cost average (EIA-923 volume-weighted) is the same. That basis,
# at ~7 MMBtu/MWh, is the structural source of the steady upstate-cheap /
# east-dear LMP gradient (Central-East congestion realizes it); a single
# ISO-month series cannot. Consumed by :func:`apply_nyiso_zonal_gas_basis`.
NYISO_ZONAL_GAS_HUB_PATH: Path = RAW_DATA_DIR / "nyiso_zonal_gas_hub.csv"

# The east reference zone whose hub (Iroquois Z2 — the bulk of NYISO gas burns
# in the Capital/Hudson/LI pocket) anchors the offset: zones cheaper than it
# (Upstate on Tenn Z4, NYC on Transco Z6) get a negative basis, leaving the
# already-calibrated east level untouched while opening the west-to-east spread.
NYISO_GAS_HUB_REFERENCE_ZONE: str = "Capital_Hudson"

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
# scripts/fetch_pge_socal_citygate_daily.py + derive_caiso_zonal_gas_hub.py),
# the same free published print the ERCOT Waha rows cite. Measured N-S spread
# (PG&E − SoCal): −0.49 (2023) / +0.54 (2024) / −0.18 (2025) $/MMBtu — real but
# year-varying, so it enters as data, never as a fitted north-premium knob.
# Like PJM/MISO/ERCOT this is anchored to a gas-capacity-weighted mean of zero
# in :func:`apply_caiso_zonal_gas_basis`, so the calibrated CAISO aggregate gas
# level (CA-composite citygate + transport) is preserved and ONLY the measured
# cross-zonal spread opens. Consumed by :func:`apply_caiso_zonal_gas_basis`.
CAISO_ZONAL_GAS_HUB_PATH: Path = RAW_DATA_DIR / "caiso_zonal_gas_hub.csv"

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
# (written by scripts/derive_gas_takeorpay.py). Used by
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
# "New York" row, scraped by scripts/fetch_transco_daily_spot.py). The NYISO
# analogue of HENRY_HUB_DAILY_PATH: used only for its within-month *shape* so the
# daily hub-basis overlay (:func:`iso_hub_daily_gas_prices`) resolves the real
# cold-day spike that a monthly mean smears flat, without moving the monthly hub
# level (the factors normalize to each month's own daily mean). Iroquois Z2 — the
# NYISO reference zone — is not on EIA's free table, so the Iroquois-priced zones
# inherit this Transco daily shape (a real daily Iroquois series is the open ask).
TRANSCO_Z6_NY_DAILY_PATH: Path = GAS_PRICES_DIR / "transco_z6_ny_daily.csv"

# Measured Algonquin Citygate (AGT) *daily* spot, harvested free from the prose of
# every EIA Natural Gas Weekly Update ("...the price went up $9.31 from $4.04/MMBtu
# last Wednesday to $13.35/MMBtu yesterday...") by scripts/fetch_algonquin_daily_spot.py.
# These are real, EIA-published AGT spot prints — two hard-dated Wednesdays per
# weekly page plus winter high/low days, ~123 prints 2023-2025, densest in the cold
# weeks that set the ISO-NE price tail. The NEISO leg of the daily hub-basis overlay
# (:func:`iso_hub_daily_gas_prices`) anchors its within-month AGT basis to these real
# prints and mean-preserves to the measured monthly basis, replacing the retired
# demand-convexity proxy. AGT basis ~= Transco Z6 NY basis (measured slope ~0.95,
# corr ~0.79), so TRANSCO_Z6_NY_DAILY_PATH supplies the within-month shape in the
# sparse (<2 print) covered months; both are EIA Weekly archive series.
ALGONQUIN_DAILY_PATH: Path = GAS_PRICES_DIR / "algonquin_citygate_daily.csv"

# Measured Iroquois Zone 2 *daily* spot prints, harvested from the prose of the
# EIA Natural Gas Weekly Update archive by scripts/fetch_iroquois_daily_spot.py
# (the Iroquois analogue of ALGONQUIN_DAILY_PATH — EIA's compact spot table has
# no Iroquois row, but the narrative quotes the hub in the cold weeks that set
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
# Transco daily series reads (scripts/fetch_caiso_citygate_daily.py), true-date
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

# Measured PG&E Citygate / SoCal Citygate weekly Wednesday prints (EIA NG
# Weekly Update archive, NGI Daily GPI; scripts/fetch_pge_socal_citygate_daily
# .py — the same free published print the CAISO zonal-hub annual rows in
# ``caiso_zonal_gas_hub.csv`` are month-balanced from). The SoCal column is the
# gas leg of the caiso-87 surplus-state trigger
# (:func:`socal_citygate_weekly_hourly` →
# :func:`market_sim.model.transmission.inject_caiso_dsw_surplus_clean`): an
# LDC-citygate proxy for the desert-SW border hubs the remote CCGT buys at
# (documented boundary misalignment, rule 14 — reconciled real data over a
# guess).
PGE_SOCAL_CITYGATE_WEEKLY_PATH: Path = GAS_PRICES_DIR / "pge_socal_citygate_weekly.csv"

# Measured Transco Z6 NY monthly (mean of daily quotes) + the committed Iroquois
# Z2 monthly reconstruction (Transco monthly + the NYISO SOM *annual*
# Iroquois-Transco spread). Consumed by nyiso_reconciled_reference_monthly,
# which re-allocates that measured annual spread across months by the measured
# Algonquin scarcity signal (rule #13 reconciliation; see its docstring).
TRANSCO_IROQUOIS_MONTHLY_PATH: Path = GAS_PRICES_DIR / "transco_z6_iroquois_monthly.csv"

# NYISO downstate (NYC / Long Island) interruptible-gas premium: the measured
# monthly excess of the NY LDC city-gate price over the NY fleet-average
# delivered-to-electric-power gas cost (scripts/fetch_nyiso_downstate_gas_basis.py;
# EIA NG N3050NY3 − N3045NY3, $/MMBtu, floored 0). Consumed by
# :func:`apply_nyiso_downstate_ct_gas_basis`.
NYISO_DOWNSTATE_CT_GAS_BASIS_PATH: Path = (
    GAS_PRICES_DIR / "nyiso_downstate_ct_gas_basis_monthly.csv"
)

_WINTER_BASIS_CACHE: dict[Path, pd.DataFrame | None] = {}
_HH_MONTHLY_CACHE: dict[Path, dict[tuple[int, int], float]] = {}
_HH_DAILY_CACHE: dict[Path, dict[int, dict[int, list[float]]]] = {}
_TRANSCO_DAILY_CACHE: dict[Path, dict[int, dict[int, list[float]]]] = {}
_TRANSCO_DAILY_DATED_CACHE: dict[Path, dict[int, dict[int, dict[int, float]]]] = {}
_ALGONQUIN_DAILY_CACHE: dict[Path, dict[int, dict[int, dict[int, float]]]] = {}
_IROQUOIS_DAILY_CACHE: dict[Path, dict[int, dict[int, dict[int, float]]]] = {}
_CAISO_CITYGATE_DAILY_CACHE: dict[Path, dict[int, dict[int, dict[int, float]]]] = {}

# Clean-data consumption. Curated Parquet for each fuel-price datatype is read
# via the frozen ``clean_io.read_clean`` seam when the opt-in flag is set and the
# clean tree has been populated (``python scripts/curate_fuel_prices.py``). The
# raw CSV path is always the fallback so existing runs are byte-identical unless
# the caller explicitly opts in via the MARKET_SIM_USE_CLEAN env flag.
_FUEL_PRICES_DATATYPE: str = "fuel-prices"
_FUEL_HUB_MONTHLY_DATATYPE: str = "fuel-hub-monthly"
_FUEL_BASIS_DATATYPE: str = "fuel-basis"
_FUEL_ZONAL_HUB_DATATYPE: str = "fuel-zonal-hub"
_FUEL_ERCOT_EP_GAS_DATATYPE: str = "fuel-ercot-ep-gas"
_FUEL_TAKEORPAY_DATATYPE: str = "fuel-takeorpay"

_HENRY_HUB_CLEAN_KEY: tuple[str, str] = ("gas", "henry_hub")

# Clean-backed daily series cache, keyed by (fuel, hub) so a multi-year run reads
# the curated parquet once. Separate from _HH_DAILY_CACHE (raw, keyed by path).
_HH_DAILY_CLEAN_CACHE: dict[tuple[str, str], dict[int, dict[int, list[float]]]] = {}

# Per-datatype clean-path caches (separate from raw caches to avoid type collision).
_WINTER_BASIS_CLEAN_CACHE: dict[str, pd.DataFrame | None] = {}
_HH_MONTHLY_CLEAN_CACHE: dict[tuple[str, str], dict[tuple[int, int], float]] = {}
_ALGONQUIN_DAILY_CLEAN_CACHE: dict[str, dict[int, dict[int, dict[int, float]]]] = {}
_CAISO_CITYGATE_DAILY_CLEAN_CACHE: dict[
    str, dict[int, dict[int, dict[int, float]]]
] = {}
_NYISO_ZONAL_HUB_CLEAN_CACHE: dict[str, pd.DataFrame | None] = {}
_ERCOT_ZONAL_HUB_CLEAN_CACHE: dict[str, pd.DataFrame | None] = {}
_ERCOT_EP_GAS_CLEAN_CACHE: dict[str, pd.DataFrame | None] = {}
_ERCOT_GAS_SPOT_PLANT_CLEAN_CACHE: dict[str, dict[int, float] | None] = {}
_ERCOT_GAS_SPOT_ZONE_CLEAN_CACHE: dict[str, dict[str, float] | None] = {}
_ZONAL_HUB_ISO_CLEAN_CACHE: dict[str, pd.DataFrame | None] = {}


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


def _clean_zonal_hub_frame(iso: str) -> pd.DataFrame | None:
    """Zonal gas-hub frame for ``iso`` from the clean ``fuel-zonal-hub`` tree.

    Returns the same ``pd.DataFrame | None`` contract as the raw CSV loaders.
    """
    from scripts.lib.clean_io import read_clean

    df = read_clean(_FUEL_ZONAL_HUB_DATATYPE, iso=iso, validate=False)
    return df if not df.empty else None


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
    (:data:`ALGONQUIN_DAILY_PATH`, by ``scripts/fetch_algonquin_daily_spot.py``).
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
    (:data:`IROQUOIS_Z2_DAILY_PATH`, by ``scripts/fetch_iroquois_daily_spot.py``).
    Prints are keyed by true calendar day; an absent file yields an empty map so
    every consumer degrades to the existing reconstruction (byte-identical until
    the fetch workflow lands the data). Cached per path.
    """
    resolved = Path(path) if path else IROQUOIS_Z2_DAILY_PATH
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
    scraped by ``scripts/fetch_caiso_citygate_daily.py`` from the same EIA
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

    Each calendar day's factor is the measured Henry Hub daily spot divided by
    that month's own daily mean, then the calendar-day factors are renormalized
    so they average to EXACTLY 1.0 within every month — multiplying the
    (correctly-levelled) monthly gas series by them adds the real intra-month
    commodity swing while leaving the monthly mean, and hence the annual
    generation mix, unchanged. The daily spot has only trading days; the
    (typically ~21) quotes are spread evenly across the month's calendar days
    (a weekend inherits the bracketing trading values' block), and a month with
    no quotes resolves to all-ones (no shape). This is the same mechanism a
    forecast would use (a forward monthly level times a representative daily
    shape), so it is not backcast-only.

    The explicit renormalization is REQUIRED, not cosmetic: bare ``np.interp``
    resampling of the trading-day quotes onto the calendar-day grid does not
    preserve the mean in a convex gas-spike month, so a cold-snap spike
    overshot the month mean by ~2% pre-fix (worst Jan-2024, +$0.10/MMBtu
    delivered — the G-A1 finding, docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md).
    This mirrors the per-hub daily-basis mechanisms below, which already
    renormalize their calendar-day factors to 1.0.
    """
    factors = np.ones(hours, dtype=float)
    by_year = _henry_hub_daily(path).get(year)
    if not by_year:
        return factors
    hour = 0
    for month_idx, n_days in enumerate(_DAYS_IN_MONTH):
        month_hours = n_days * 24
        quotes = by_year.get(month_idx + 1)
        if quotes and hour < hours:
            arr = np.asarray(quotes, dtype=float)
            mean = float(arr.mean())
            if mean > 0:
                # Spread the month's trading-day quotes across its calendar
                # days, then RENORMALIZE so the calendar-day factors average to
                # exactly 1.0 (np.interp resampling does not preserve the mean
                # in a convex spike month — G-A1 fix), then repeat each day's
                # factor across its 24 hours.
                day_factor = np.interp(
                    np.linspace(0.0, 1.0, n_days),
                    np.linspace(0.0, 1.0, len(arr)),
                    arr / mean,
                )
                fbar = float(day_factor.mean())
                if fbar > 0:
                    day_factor = day_factor / fbar
                shaped = np.repeat(day_factor, 24)[: max(0, hours - hour)]
                factors[hour : hour + len(shaped)] = shaped
        hour += month_hours
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
        rec = nyiso_reconciled_reference_monthly(year, basis_path=basis_path)
        if rec is not None:
            return rec[0]
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
    (:func:`_iroquois_z2_daily`, harvested from the EIA NG Weekly narrative by
    ``scripts/fetch_iroquois_daily_spot.py``; ≥2 prints required so a lone quote
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
    """
    monthly = iso_hub_monthly_gas_prices(config, year, basis_path, henry_hub_path)
    if monthly is None:
        return None
    transco_dated = _transco_z6_daily_dated(transco_path).get(year, {})
    iroquois_prints = _iroquois_z2_daily(None).get(year, {})
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


def _flow_date_staircase(
    dated_year: dict[int, dict[int, float]], year: int
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
    """
    stamps = {
        pd.Timestamp(year=year, month=m, day=d) + pd.Timedelta(days=1): v
        for m, days in sorted(dated_year.items())
        for d, v in sorted(days.items())
    }
    if not stamps:
        return None
    idx = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    s = pd.Series(stamps).sort_index()
    s = s.reindex(idx.union(s.index)).sort_index().ffill().bfill().reindex(idx)
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
) -> np.ndarray | None:
    """CAISO daily-resolved citygate gas price ($/MMBtu), ``(hours,)``, or ``None``.

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
    monthly = iso_hub_monthly_gas_prices(config, year, basis_path, henry_hub_path)
    if monthly is None:
        return None
    citygate_dated = _caiso_citygate_daily_dated(citygate_path).get(year, {})
    # caiso-90 (caiso_citygate_flow_date): the prints are a next-day-delivery
    # index, so place them on their FLOW days (trade + 1, weekend packages
    # forward-filled) instead of their trade days. Built once for the year so
    # a month-end print correctly flows into the next covered month; month
    # coverage below is unchanged (a month reprices only where the survey
    # basis row AND its own prints exist).
    flow_series = (
        _flow_date_staircase(citygate_dated, year)
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
        # present); spot_level only changes the LEVEL within them.
        if not np.isnan(hub_m) and hour < T:
            dated = citygate_dated.get(m + 1, {})
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
    (:func:`_algonquin_daily`, ``scripts/fetch_algonquin_daily_spot.py``):

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
    henry_hub = _henry_hub_monthly(henry_hub_path)
    hh_daily = _henry_hub_daily(henry_hub_path).get(year, {})
    all_agt = _algonquin_daily(None)
    agt_prints = all_agt.get(year, {})
    transco_daily = _transco_z6_daily(None).get(year, {})
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
        hourly = _caiso_hub_daily_gas_prices(config, year, basis_path, spot_level=True)
        daily = hourly is not None
    elif getattr(config, "gas_hub_basis_daily", False):
        hourly = iso_hub_daily_gas_prices(config, year, basis_path)
        daily = hourly is not None
    if hourly is None:
        monthly = iso_hub_monthly_gas_prices(config, year, basis_path)
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


_NYISO_ZONAL_HUB_CACHE: dict[Path, pd.DataFrame | None] = {}


def _load_nyiso_zonal_gas_hub(path: Path | None) -> pd.DataFrame | None:
    """Load the NYISO per-zone annual gas-hub table, or ``None`` if absent."""
    if path is None and _use_clean_data():
        from scripts.lib.clean_io import clean_exists

        if clean_exists(_FUEL_ZONAL_HUB_DATATYPE, iso="NYISO"):
            if "_clean" not in _NYISO_ZONAL_HUB_CLEAN_CACHE:
                _NYISO_ZONAL_HUB_CLEAN_CACHE["_clean"] = _clean_zonal_hub_frame("NYISO")
            return _NYISO_ZONAL_HUB_CLEAN_CACHE["_clean"]
    resolved = Path(path) if path else NYISO_ZONAL_GAS_HUB_PATH
    if resolved in _NYISO_ZONAL_HUB_CACHE:
        return _NYISO_ZONAL_HUB_CACHE[resolved]
    frame: pd.DataFrame | None = None
    if resolved.exists():
        loaded = pd.read_csv(resolved)
        if not loaded.empty:
            frame = loaded
    _NYISO_ZONAL_HUB_CACHE[resolved] = frame
    return frame


def nyiso_zonal_gas_offsets(
    year: int, path: Path | None = None
) -> dict[str, float] | None:
    """Return ``{zone: $/MMBtu offset vs the east reference}`` for NYISO, or None.

    The offset is the zone's measured hub price (Tenn Z4 200L upstate, Iroquois
    Z2 in the Capital/Hudson/LI east, Transco Z6 NY in the city) minus the
    reference zone's hub (:data:`NYISO_GAS_HUB_REFERENCE_ZONE`, Iroquois Z2).
    The reference zone resolves to 0.0, so the calibrated east gas level is
    preserved and only the cheaper west/city zones shift down — opening the
    persistent upstate-cheap / east-dear basis the system-average series flattens.
    Returns ``None`` when the table is missing or has no rows for ``year``.
    """
    frame = _load_nyiso_zonal_gas_hub(path)
    if frame is None:
        return None
    sub = frame[frame["year"] == year]
    if sub.empty:
        return None
    hub = {str(r.zone): float(r.hub_usd_mmbtu) for r in sub.itertuples()}
    ref = hub.get(NYISO_GAS_HUB_REFERENCE_ZONE)
    if ref is None:
        return None
    return {z: price - ref for z, price in hub.items()}


def nyiso_reconciled_reference_monthly(
    year: int,
    hub_path: Path | None = None,
    basis_path: Path | None = None,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Reconciled Iroquois Z2 monthly hub price, winter-weighted from measured data.

    The committed reference construction (``transco_z6_iroquois_monthly.csv``)
    distributes the **measured annual** NYISO-SOM Iroquois−Transco spread FLAT
    across months, which mis-states the winter physics: Iroquois Z2 is a
    Connecticut trading point inside the New England pipeline complex, and its
    premium over Transco Z6 NY concentrates in exactly the constrained winter
    months when Algonquin blows out (Dec-2024: flat construction $3.16/MMBtu vs
    the ~$9 complex it physically trades in). No free Iroquois series exists to
    replace it (verified: zero prints in 146 NGWU weekly pages 2023–25; NGI/ICE
    paywalled), so per rule #13 this is the documented **reconciled version of
    the real data** rather than a guess:

      ``iroquois_m = transco_m + annual_spread × 12 × w_m``
      ``w_m = max(agt_basis_m, 0) / Σ max(agt_basis_m, 0)``

    - ``transco_m`` — the measured Transco Z6 NY monthly (mean of daily quotes);
    - ``annual_spread`` — the measured SOM annual Iroquois−Transco spread,
      preserved EXACTLY (scarcity-shaped up to the measured Algonquin-Citygate
      monthly ceiling below; the ceiling-shaved remainder re-enters as a
      year-round base differential water-filled into months with headroom);
    - ``w_m`` — the **measured Algonquin (MA-citygate) monthly basis**, the New
      England pipeline-scarcity signal that physically causes the Iroquois
      premium; unconstrained months (basis ≤ 0) carry zero premium (summer Z2
      trades at Transco backhaul parity).

    No fitted constant, nothing reads a model output or price residual; a
    forecast year regenerates it from the forward basis seasonality and it
    responds to changed conditions (a mild winter ⇒ low AGT basis ⇒ low
    premium). Returns ``(iroquois_m, transco_m)`` as two ``(12,)`` arrays, or
    ``None`` when any input series is incomplete for ``year`` (the caller then
    keeps the flat committed construction, byte-identical).
    """
    resolved = Path(hub_path) if hub_path else TRANSCO_IROQUOIS_MONTHLY_PATH
    if not resolved.exists():
        return None
    frame = pd.read_csv(resolved)
    sub = frame[frame["date"].astype(str).str.startswith(f"{year}-")]
    transco = np.full(12, np.nan)
    iroq = np.full(12, np.nan)
    for r in sub.itertuples():
        m = int(str(r.date)[5:7]) - 1
        if 0 <= m < 12:
            transco[m] = float(r.transco_z6_ny_usd_mmbtu)
            iroq[m] = float(r.iroquois_z2_usd_mmbtu)
    if np.isnan(transco).any() or np.isnan(iroq).any():
        return None
    annual_spread = float((iroq - transco).mean())
    bframe = _load_winter_basis_frame(basis_path)
    if bframe is None:
        return None
    agt_rows = bframe[(bframe["iso"] == "NEISO") & (bframe["year"] == year)]
    agt = np.full(12, np.nan)
    for _, row in agt_rows.iterrows():
        m = int(row["month"]) - 1
        if 0 <= m < 12:
            agt[m] = float(row["basis_usd_mmbtu"])
    if np.isnan(agt).any():
        return None
    w = np.clip(agt, 0.0, None)
    total = float(w.sum())
    if total <= 0.0:
        return None
    spread_m = annual_spread * 12.0 * w / total
    iroq_rec = transco + spread_m
    # Measured-ceiling reconciliation (rule #14): Iroquois Z2 is a Connecticut
    # trading point delivering INTO the New England market area, so its
    # monthly level cannot exceed the Algonquin Citygate — the demand ceiling
    # of the complex it feeds (Z2 gas flows on toward the citygate; a CT
    # buyer never pays more at Z2 than at the citygate it can buy instead).
    # Re-allocating 12x the SOM annual spread onto the few positive-basis
    # months has no per-month magnitude anchor and can breach that ceiling in
    # the most-constrained months (Feb-2023 reconstruction $13.21 vs the
    # measured $8.13 Algonquin month; Jan-2024 $8.60 vs $7.68). Cap each
    # month at the measured Algonquin Citygate monthly (Henry Hub month +
    # the same measured NEISO basis row the weights come from — the series
    # the NEISO keeper itself prices on), floored at Transco so the cap can
    # never invert the hubs. The shaved excess is not left as scarcity
    # premium — it re-enters as a year-round base differential water-filled
    # across the months with ceiling headroom (see below), so the measured
    # SOM ANNUAL spread is preserved exactly while no month out-prices the
    # ceiling.
    hh = _henry_hub_monthly(None)
    hh_m = np.array([hh.get((year, m + 1), np.nan) for m in range(12)])
    if not np.isnan(hh_m).any():
        alg_m = hh_m + agt
        # Floor the ceiling at the committed FLAT construction level
        # (transco + annual spread): the Z2<=citygate ordering is firm in the
        # constrained winter months the re-allocation loads (citygate blowouts
        # far exceed Z2), but inside unconstrained months the two hubs trade
        # within transport noise and the flat level is the better-measured
        # datum — the cap must only shave scarcity-month excess, never push a
        # month below the committed annually-exact construction.
        ceil_m = np.maximum(alg_m, transco + annual_spread)
        capped = np.minimum(iroq_rec, ceil_m)
        # Preserve the measured SOM ANNUAL spread (rule #13 — the annual
        # total is a measured datum, not disposable): the scarcity months
        # could not hold the full AGT-shaped re-allocation under the measured
        # Algonquin ceiling, so the shaved remainder is by construction a
        # year-round (non-scarcity) base differential — Z2 is a premium point
        # over Transco outside blowout months too (Waddington/TransCanada
        # supply pricing), which is why the measured SOM annual exceeds what
        # the scarcity months alone can carry. Water-fill it uniformly across
        # the months with ceiling headroom (the minimal-assumption
        # allocation), never above the ceiling; any residual that the whole
        # ceiling cannot hold is dropped and the annual under-delivers (no
        # 2023-25 year does).
        excess = float((iroq_rec - capped).sum())
        for _ in range(12):
            if excess <= 1e-9:
                break
            room = ceil_m - capped
            open_m = room > 1e-9
            if not open_m.any():
                break
            step = np.minimum(np.full(12, excess / open_m.sum()) * open_m, room)
            capped = capped + step
            excess -= float(step.sum())
        iroq_rec = capped
    return iroq_rec, transco


def nyiso_zonal_gas_ratios_monthly(
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
    basis_path: Path | None = None,
    henry_hub_path: Path | None = None,
) -> dict[str, np.ndarray] | None:
    """Return ``{zone: (12,) monthly ratio}`` vs the reconciled reference hub.

    The month-varying companion of :func:`nyiso_zonal_gas_offsets`, active only
    under ``config.nyiso_iroquois_winter_spread``. With the reference
    (Iroquois Z2) carrying its winter-concentrated premium, the flat annual
    ADDITIVE offsets would (a) wrongly drag the non-Iroquois zones up with the
    winter premium and (b) leave NYC's daily spikes amplified by the reference
    level, so each zone instead prices at the reference hourly series times its
    OWN measured hub-to-reference monthly ratio — preserving the zone's
    measured monthly mean exactly and scaling the within-month daily swing to
    the zone's own level:

    - **NYC** (Transco Z6 NY): ``transco_m / iroquois_m`` — the city resolves
      to its own measured hub monthly exactly.
    - **Iroquois-mapped zones** (Capital_Hudson / Lower_Hudson / Long_Island,
      annual level equal to the reference): ratio 1 — they ARE the reference.
    - **Upstate_West** (Tenn Z4 200L, a Marcellus supply point with no New
      England scarcity premium): its measured SOM annual level riding the
      Henry Hub within-year shape, over the reference —
      ``(annual + hh_m − mean(hh_m)) / iroquois_m`` — so its annual mean stays
      the measured SOM value.

    Every input is a measured series; no fitted constant. Returns ``None``
    when the flag is off or any series is incomplete (caller falls back to the
    annual additive offsets, byte-identical).
    """
    if config.iso != "NYISO" or not getattr(
        config, "nyiso_iroquois_winter_spread", False
    ):
        return None
    rec = nyiso_reconciled_reference_monthly(year, basis_path=basis_path)
    if rec is None:
        return None
    iroq_m, transco_m = rec
    if (iroq_m <= 0).any():
        return None
    frame = _load_nyiso_zonal_gas_hub(path)
    if frame is None:
        return None
    sub = frame[frame["year"] == year]
    if sub.empty:
        return None
    hub = {str(r.zone): float(r.hub_usd_mmbtu) for r in sub.itertuples()}
    ref_ann = hub.get(NYISO_GAS_HUB_REFERENCE_ZONE)
    if ref_ann is None:
        return None
    hh = _henry_hub_monthly(henry_hub_path)
    hh_m = np.array([hh.get((year, m + 1), np.nan) for m in range(12)])
    if np.isnan(hh_m).any():
        return None
    hh_shape = hh_m - float(hh_m.mean())
    ratios: dict[str, np.ndarray] = {}
    for z, price_ann in hub.items():
        if z == "NYC":
            ratios[z] = transco_m / iroq_m
        elif abs(price_ann - ref_ann) < 1e-9:
            ratios[z] = np.ones(12)
        else:
            ratios[z] = np.maximum(price_ann + hh_shape, _GAS_PRICE_FLOOR) / iroq_m
    return ratios


def apply_nyiso_zonal_gas_basis(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
) -> None:
    """Shift each NYISO gas unit's price by its zone's measured hub basis.

    NYISO's regions buy gas off different, persistently-priced pipeline indices
    (:data:`NYISO_ZONAL_GAS_HUB_PATH`): the marginal gas unit in the Capital/
    Hudson east pays Iroquois Z2 / Tenn Z6 while the western and Central zones
    pay the cheaper Tenn Z4 200L / Niagara, so the east marginal gas costs
    ~$1-3/MMBtu more than the west all year. The EIA-923 volume-weighted
    ISO-month series and the thin per-plant F923 receipts (only ~5 NY plants
    report Schedule-5 gas) both wash this gradient out, leaving the model's
    west-to-east LMP spread a knife-edge fuel-merit accident. This adds the
    measured per-zone offset (:func:`nyiso_zonal_gas_offsets`, anchored so the
    east reference zone is unchanged) to every gas unit's delivered price,
    floored at a small positive so a deep negative basis cannot drive fuel
    cost below zero. Runs after the F923 plant-monthly overwrite and before
    :func:`apply_dual_fuel_pricing`, so oil parity still caps any winter spike.

    Gated on ``config.nyiso_zonal_gas_basis`` and ``config.iso == "NYISO"``
    (off by default; the calibration harness enables it for NYISO), so every
    other ISO and all forecasts are byte-identical. Mutates ``fuel_prices`` in
    place; idempotent given the same inputs.
    """
    if not getattr(config, "nyiso_zonal_gas_basis", False):
        return
    if config.iso != "NYISO":
        return
    from market_sim.config.iso_configs import get_iso_config

    zone_names = get_iso_config(config.iso).zone_names
    gas_rows = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX))[0]
    if gas_rows.size == 0:
        return
    # Month-varying ratios under the reconciled winter spread (each zone
    # prices at the reference hourly series times its own measured
    # hub-to-reference monthly ratio; see nyiso_zonal_gas_ratios_monthly).
    monthly_ratios = nyiso_zonal_gas_ratios_monthly(config, year, path)
    if monthly_ratios is not None:
        month_of_hour = _month_index(fuel_prices.shape[1])
        ratio_matrix = np.array(
            [monthly_ratios.get(name, np.ones(12)) for name in zone_names],
            dtype=float,
        )
        gen_ratio = ratio_matrix[fleet.zone_idx[gas_rows]][:, month_of_hour]
        fuel_prices[gas_rows, :] = np.maximum(
            fuel_prices[gas_rows, :] * gen_ratio, _GAS_PRICE_FLOOR
        )
        logger.info(
            "NYISO zonal gas basis (%d, monthly reconciled): %d gas units "
            "scaled by zone-month hub ratio (min %.2f, max %.2f vs %s)",
            year,
            gas_rows.size,
            float(gen_ratio.min()),
            float(gen_ratio.max()),
            NYISO_GAS_HUB_REFERENCE_ZONE,
        )
        return
    offsets = nyiso_zonal_gas_offsets(year, path)
    if offsets is None:
        return
    # Per-generator additive offset from its zone (0.0 for the reference zone
    # and any zone absent from the table — e.g. the priced external node).
    offset_by_zone_idx = np.array(
        [offsets.get(name, 0.0) for name in zone_names], dtype=float
    )
    gen_offset = offset_by_zone_idx[fleet.zone_idx[gas_rows]]
    floored = np.maximum(
        fuel_prices[gas_rows, :] + gen_offset[:, np.newaxis], _GAS_PRICE_FLOOR
    )
    fuel_prices[gas_rows, :] = floored
    logger.info(
        "NYISO zonal gas basis (%d): %d gas units shifted by zone hub offset "
        "(min %.2f, max %.2f $/MMBtu vs %s)",
        year,
        gas_rows.size,
        float(gen_offset.min()),
        float(gen_offset.max()),
        NYISO_GAS_HUB_REFERENCE_ZONE,
    )


_NYISO_DOWNSTATE_CT_BASIS_CACHE: dict[Path, dict[int, np.ndarray]] = {}

# Downstate load pockets served off the NYC / Long Island LDC city gates.
NYISO_DOWNSTATE_CT_ZONES: frozenset[str] = frozenset({"NYC", "Long_Island"})


def nyiso_downstate_ct_gas_premium(
    year: int, path: Path | None = None
) -> np.ndarray | None:
    """Return the ``(12,)`` monthly downstate-peaker interruptible-gas premium.

    The measured monthly excess ($/MMBtu, floored at 0) of the NY LDC city-gate
    price over the Transco Zone 6 NY pipeline hub the model prices downstate gas
    at — the delivered-cost increment a non-firm downstate (NYC / Long Island)
    peaker faces buying interruptible city-gate gas instead of firm pipeline-hub
    gas. Positive year-round; floors to 0 only in months the pipeline hub itself
    spikes above the city gate (arctic events). Read from
    :data:`NYISO_DOWNSTATE_CT_GAS_BASIS_PATH` (built by
    ``scripts/fetch_nyiso_downstate_gas_basis.py`` from EIA NG series N3050NY3
    minus the measured Transco Z6 NY monthly). Returns ``None`` when the table is
    missing or has no rows for ``year`` (e.g. a forward year without the series
    extended).
    """
    resolved = Path(path) if path else NYISO_DOWNSTATE_CT_GAS_BASIS_PATH
    cache = _NYISO_DOWNSTATE_CT_BASIS_CACHE.setdefault(resolved, {})
    if year in cache:
        return cache[year]
    if not resolved.exists():
        cache[year] = None  # type: ignore[assignment]
        return None
    frame = pd.read_csv(resolved)
    sub = frame[frame["year"] == year]
    if sub.empty:
        cache[year] = None  # type: ignore[assignment]
        return None
    monthly = np.zeros(12, dtype=float)
    for r in sub.itertuples():
        m = int(r.month) - 1
        if 0 <= m < 12:
            monthly[m] = float(r.premium_usd_mmbtu)
    cache[year] = monthly
    return monthly


def apply_nyiso_downstate_ct_gas_basis(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
) -> None:
    """Add the interruptible city-gate gas premium to downstate NYISO peakers.

    NYISO's downstate combustion-turbine PEAKERS (NYC zone J + Long Island zone
    K, ``CT_PEAKER`` / ``gas_ct`` — the Bayonne / Equus / Edgewood /
    Glenwood-Landing LM6000 fleet) run only a few hundred hours a year, so they
    cannot justify firm interstate pipeline transportation: they take gas off
    the local LDC (Con Edison / National Grid) **city gate** on interruptible
    service, so their delivered fuel index is the LDC city gate, not the
    interstate pipeline hub the model prices downstate gas at (Transco Z6 NY via
    ``gas_monthly_actuals`` + the hub-basis overlay). Pricing these peakers at
    the pipeline hub, the energy-only LP sees a heat-rate-9-10 LM6000 undercut
    the heat-rate-11-12 downstate steam fleet and runs them near-baseload
    year-round (the CT_PEAKER over-run the de-leaked offer curve exposes, B-NYI-1
    / issue #1344 — dominated by the Long Island gas-island peakers).

    This adds the **measured** monthly premium
    (:func:`nyiso_downstate_ct_gas_premium` — the EIA NY city-gate price minus
    the measured Transco Z6 NY hub, floored at 0) to each downstate
    ``CT_PEAKER`` unit's delivered gas price, lifting it from the pipeline hub to
    its actual LDC-delivered index. The premium is positive year-round (the city
    gate carries interstate-pipeline demand charges + distribution + an
    interruptible premium over the hub every month) and widens in summer when NYC
    gas-for-power cooling demand makes downstate interruptible gas scarce; it
    floors to 0 only when the pipeline hub itself spikes above the city gate
    (arctic events), where the model's base gas already exceeds the delivered
    price. It is a delivered fuel price (CLAUDE.md rule #13's canonical
    admissible input): the city gate and the hub publish monthly and project
    forward, so a forecast year regenerates the premium and it responds to
    changed conditions (a tight winter/summer widens it). Nothing is fitted to a
    price/volume residual (rules #1/#11/#12).

    Runs after :func:`apply_nyiso_zonal_gas_basis` and before
    :func:`apply_dual_fuel_pricing`, so the oil-parity cap still bounds any
    winter spike. Gated on ``config.nyiso_downstate_ct_gas_basis`` and
    ``config.iso == "NYISO"`` (off by default; the calibration harness enables
    it for NYISO), so every other ISO and all forecasts are byte-identical.
    Mutates ``fuel_prices`` in place; idempotent given the same inputs.
    """
    if not getattr(config, "nyiso_downstate_ct_gas_basis", False):
        return
    if config.iso != "NYISO":
        return
    if fleet.plant_group is None:
        return
    premium = nyiso_downstate_ct_gas_premium(year, path)
    if premium is None:
        return
    from market_sim.config.iso_configs import get_iso_config

    zone_names = get_iso_config(config.iso).zone_names
    plant_group = np.asarray(fleet.plant_group)
    # Downstate model-zone indices (NYC / Long Island). Membership is checked by
    # index so units on the priced external node (a zone_idx beyond the model
    # zone list) are ignored, not an out-of-range lookup.
    downstate_idx = np.array(
        [i for i, name in enumerate(zone_names) if name in NYISO_DOWNSTATE_CT_ZONES],
        dtype=int,
    )
    is_gas_ct = np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX)
    ct_rows = np.nonzero(
        is_gas_ct
        & (plant_group == "CT_PEAKER")
        & np.isin(fleet.zone_idx, downstate_idx)
    )[0]
    if ct_rows.size == 0:
        return
    month_of_hour = _month_index(fuel_prices.shape[1])
    premium_hourly = premium[month_of_hour]  # (T,)
    fuel_prices[ct_rows, :] = np.maximum(
        fuel_prices[ct_rows, :] + premium_hourly[np.newaxis, :], _GAS_PRICE_FLOOR
    )
    logger.info(
        "NYISO downstate CT interruptible-gas basis (%d): %d downstate "
        "CT_PEAKER units lifted by the LDC city-gate premium "
        "(monthly min %.2f, max %.2f $/MMBtu; summer-peaked)",
        year,
        ct_rows.size,
        float(premium.min()),
        float(premium.max()),
    )


def _zone_delivered_hourly(
    by_md: dict[int, dict[int, float]], hours: int
) -> np.ndarray:
    """Expand one zone's ``{month:{day:val}}`` onto the model's 8760 calendar.

    Each calendar day's value is repeated across its 24 hours, mirroring the
    mean-preserving daily overlay's calendar walk
    (:func:`nyiso_reconciled_reference_monthly`); a leap-year Feb-29 row is never
    referenced. Returns a ``(hours,)`` array (may hold NaN only where a whole
    month is missing, which the caller resolves).
    """
    out = np.full(hours, np.nan, dtype=float)
    hour = 0
    for m in range(12):  # m = 0-based month
        n_days = _DAYS_IN_MONTH[m]
        dated = by_md.get(m + 1, {})
        if dated and hour < hours:
            day_vals = np.array(
                [dated.get(d, np.nan) for d in range(1, n_days + 1)], dtype=float
            )
            # A single non-trading gap should never leave a NaN hole; the daily
            # series is already gap-filled at curation, but guard defensively.
            if np.isnan(day_vals).any():
                day_vals = pd.Series(day_vals).ffill().bfill().to_numpy()
            shaped = np.repeat(day_vals, 24)[: max(0, hours - hour)]
            out[hour : hour + len(shaped)] = shaped
        hour += n_days * 24
    return out


def _downstate_delivered_gas_hourly_by_zone(
    iso: str, year: int, hours: int
) -> dict[str, np.ndarray] | None:
    """Return ``{zone: (hours,) delivered-gas index}`` per downstate zone, or ``None``.

    Expands the curated per-zone ``nyiso-downstate-gas`` daily index
    (:func:`market_sim.data.nyiso_downstate_gas.delivered_gas_by_zone_month_day` —
    measured Transco Z6 NY daily spot + monthly LDC non-firm transport rate, per
    zone) onto the model's fixed 365-day (28-day-February) calendar. ``None`` when
    the datatype has no rows for the year (a forward year without the series
    extended), so the caller falls back to the monthly-premium path.
    """
    from market_sim.data.nyiso_downstate_gas import delivered_gas_by_zone_month_day

    by_zone = delivered_gas_by_zone_month_day(iso, year)
    if not by_zone:
        return None
    out: dict[str, np.ndarray] = {}
    for zone, by_md in by_zone.items():
        arr = _zone_delivered_hourly(by_md, hours)
        if np.isnan(arr).all():
            continue
        # Any residual NaN (a month with no rows) falls back to surrounding
        # measured days so the CT gas is always defined where the class dispatches.
        if np.isnan(arr).any():
            arr = pd.Series(arr).ffill().bfill().to_numpy()
        out[zone] = arr
    return out or None


def apply_nyiso_downstate_ct_gas_daily(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
) -> None:
    """Re-ground downstate NYISO CT-peaker gas on the measured DAILY delivered index.

    The daily-resolution successor to :func:`apply_nyiso_downstate_ct_gas_basis`
    (the monthly-premium adder) for the same NYC / Long Island ``CT_PEAKER``
    LM6000 fleet (Bayonne / Equus / Edgewood / Glenwood-Landing). Rather than
    lift the pipeline-hub *monthly* base by a statewide monthly premium, this
    **sets** each downstate CT_PEAKER unit's delivered gas directly to the curated
    per-zone ``nyiso-downstate-gas`` daily index — the measured Transco Zone 6 NY
    pipeline-hub **daily** spot (the peaker's own commodity) plus the measured
    **monthly** LDC **non-firm transportation** delivery rate for that unit's zone
    (KEDNY SC-22 for NYC, KEDLI SC-19 for Long Island;
    :func:`_downstate_delivered_gas_hourly_by_zone`).

    Why this is the correct grounding (rules #11/#12/#13): these interruptible
    peakers run only a few hundred hours a year, concentrated on the coldest days
    when the downstate pipeline hub blows out (Transco Z6 NY hit $23.90/MMBtu in
    Jan-2024). The monthly mean smears that spike across the whole month, pricing
    the peaker's scarce-day gas far too cheap on exactly the hours it clears —
    letting an HR~9-10 LM6000 undercut the dearer downstate steam fleet. Pricing
    the daily hub spot lifts the peaker offer on the scarce days it runs. And
    because they are transportation customers (buy their own commodity, pay the
    LDC a non-firm transport charge), the adder over the hub is the measured LDC
    non-firm transportation delivery rate — not the statewide firm citygate the v1
    construction used — and it is per-zone because the LI gas island (KEDLI) and
    the NYC system (KEDNY) carry materially different delivery costs. Each input
    is a measured, forward-native market/tariff series (the daily Transco spot and
    the monthly LDC transport rate both publish forward and step at rate cases /
    respond to changed conditions), so a forecast year regenerates it; nothing is
    fitted to a price or volume residual (rules #1/#11/#12/#13).

    Runs immediately after :func:`apply_nyiso_downstate_ct_gas_basis` in the
    fuel-price pipeline and before :func:`apply_dual_fuel_pricing`, so the
    oil-parity cap still bounds any winter spike. Gated on
    ``config.nyiso_downstate_ct_gas_daily`` and ``config.iso == "NYISO"`` (off by
    default; the calibration harness enables it for NYISO). It supersedes the
    monthly adder for this class — set ``nyiso_downstate_ct_gas_basis=False`` when
    this is on (one mechanism per phenomenon, rule 19); if both were set, the
    daily SET here overwrites the monthly ADD, so the level is still the daily
    delivered index. Mutates ``fuel_prices`` in place; idempotent given the same
    inputs; every other ISO and all forecasts without the series are byte-identical.
    """
    if not getattr(config, "nyiso_downstate_ct_gas_daily", False):
        return
    if config.iso != "NYISO":
        return
    if fleet.plant_group is None:
        return
    by_zone = _downstate_delivered_gas_hourly_by_zone(
        config.iso, year, fuel_prices.shape[1]
    )
    if not by_zone:
        return
    from market_sim.config.iso_configs import get_iso_config

    zone_names = get_iso_config(config.iso).zone_names
    plant_group = np.asarray(fleet.plant_group)
    is_gas_ct = np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX)
    total_rows = 0
    lo = hi = None
    # Each downstate zone's CT_PEAKER units take that zone's own LDC-delivered
    # index (membership by zone index so a priced external node is ignored).
    for zone, delivered in by_zone.items():
        if zone not in NYISO_DOWNSTATE_CT_ZONES or zone not in zone_names:
            continue
        z_idx = zone_names.index(zone)
        ct_rows = np.nonzero(
            is_gas_ct & (plant_group == "CT_PEAKER") & (fleet.zone_idx == z_idx)
        )[0]
        if ct_rows.size == 0:
            continue
        fuel_prices[ct_rows, :] = np.maximum(delivered[np.newaxis, :], _GAS_PRICE_FLOOR)
        total_rows += int(ct_rows.size)
        zmin, zmax = float(delivered.min()), float(delivered.max())
        lo = zmin if lo is None else min(lo, zmin)
        hi = zmax if hi is None else max(hi, zmax)
    if total_rows == 0:
        return
    logger.info(
        "NYISO downstate CT per-zone daily delivered-gas re-grounding (%d): %d "
        "downstate CT_PEAKER units SET to their zone's measured daily delivered "
        "index (Transco Z6 NY daily + LDC non-firm transport rate; "
        "range %.2f-%.2f $/MMBtu across zones %s)",
        year,
        total_rows,
        float(lo),
        float(hi),
        list(by_zone),
    )


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
    hh = _henry_hub_monthly(henry_hub_path)
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
    (:data:`ERCOT_GAS_TAKEORPAY_PATH`, written by ``scripts/derive_gas_takeorpay``)
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
        plant_spot = ercot_gas_spot_share_by_plant()
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


def pjm_zonal_gas_basis_by_zone(
    year: int, path: Path | None = None
) -> dict[str, float] | None:
    """Return ``{zone: basis vs Henry Hub ($/MMBtu)}`` for PJM, or None.

    The raw measured per-zone basis (each PJM zone's primary-state EIA
    delivered-to-electric-power gas price minus Henry Hub;
    :data:`PJM_ZONAL_GAS_HUB_PATH`). The mean-zero re-centring that preserves the
    calibrated fleet-aggregate level is done in :func:`apply_pjm_zonal_gas_basis`,
    which weights by each zone's gas capacity. Returns ``None`` when the table is
    missing or has no rows for ``year`` (e.g. a forward year).
    """
    return _zonal_gas_basis_by_zone(
        Path(path) if path else PJM_ZONAL_GAS_HUB_PATH, year
    )


def miso_zonal_gas_basis_by_zone(
    year: int, path: Path | None = None
) -> dict[str, float] | None:
    """Return ``{zone: basis vs Henry Hub ($/MMBtu)}`` for MISO, or None.

    Same format and semantics as :func:`pjm_zonal_gas_basis_by_zone` but reads
    :data:`MISO_ZONAL_GAS_HUB_PATH`.
    """
    return _zonal_gas_basis_by_zone(
        Path(path) if path else MISO_ZONAL_GAS_HUB_PATH, year
    )


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
) -> None:
    """Shared core for mean-zero capacity-weighted zonal gas basis (PJM / MISO).

    Adds each zone's measured basis spread (EIA delivered-to-electric-power minus
    Henry Hub) to every gas unit's delivered price, after subtracting the
    gas-capacity-weighted mean so the calibrated fleet-aggregate level is
    preserved and only the cross-zonal shape moves. Floored at
    :data:`_GAS_PRICE_FLOOR` so a deep negative basis cannot drive fuel cost
    below zero. Gated on ``config.<config_field>`` and ``config.iso == iso``.
    """
    if not getattr(config, config_field, False):
        return
    if config.iso != iso:
        return
    path = path_override if path_override else hub_path
    basis = _zonal_gas_basis_by_zone(path, year)
    if basis is None:
        return
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
    fuel_prices[gas_rows, :] = floored
    logger.info(
        "%s zonal gas basis (%d): %d gas units; cap-weighted mean %+.2f removed, "
        "zonal spread %.2f..%.2f $/MMBtu",
        iso,
        year,
        gas_rows.size,
        weighted_mean,
        float(zone_spread.min()),
        float(zone_spread.max()),
    )


def apply_pjm_zonal_gas_basis(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
) -> None:
    """Shift each PJM gas unit's price by its zone's measured regional gas basis.

    Delegates to :func:`_apply_meanzero_zonal_gas_basis` — the shared
    capacity-weighted mean-zero core that PJM and MISO both use. See that
    function's docstring for the mechanics.

    Gated on ``config.pjm_zonal_gas_basis`` and ``config.iso == "PJM"`` (a
    default-off diagnostic; see the field docstring on ScenarioConfig), so every
    other ISO and all forecasts are byte-identical. Mutates ``fuel_prices`` in
    place; idempotent given the same inputs.
    """
    _apply_meanzero_zonal_gas_basis(
        fuel_prices,
        fleet,
        config,
        year,
        iso="PJM",
        config_field="pjm_zonal_gas_basis",
        hub_path=PJM_ZONAL_GAS_HUB_PATH,
        path_override=Path(path) if path else None,
    )


def apply_miso_zonal_gas_basis(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
) -> None:
    """Shift each MISO gas unit's price by its zone's measured regional gas basis.

    Delegates to :func:`_apply_meanzero_zonal_gas_basis` — the same
    capacity-weighted mean-zero core used by PJM. MISO-West/MISO-Plains sit
    on MidCon / Northern Natural (IA), the eastern Midwest zones (Illinois/
    Indiana/East) on Chicago Citygate (IL),
    and MISO-South on Gulf Coast (LA); the spread opens while the
    fleet-aggregate gas level is preserved.

    Gated on ``config.miso_zonal_gas_basis`` and ``config.iso == "MISO"``.
    Default-off; the calibration harness enables it for MISO.
    """
    _apply_meanzero_zonal_gas_basis(
        fuel_prices,
        fleet,
        config,
        year,
        iso="MISO",
        config_field="miso_zonal_gas_basis",
        hub_path=MISO_ZONAL_GAS_HUB_PATH,
        path_override=Path(path) if path else None,
    )


def caiso_zonal_gas_basis_by_zone(
    year: int, path: Path | None = None
) -> dict[str, float] | None:
    """Return ``{zone: basis vs Henry Hub ($/MMBtu)}`` for CAISO, or None.

    Same format and semantics as :func:`pjm_zonal_gas_basis_by_zone` but reads
    :data:`CAISO_ZONAL_GAS_HUB_PATH` (NP15/ZP26 on PG&E Citygate, LA_BASIN/
    SDGE/SP15_rest on SoCal Citygate — measured weekly EIA NG Weekly prints,
    month-balanced).
    """
    return _zonal_gas_basis_by_zone(
        Path(path) if path else CAISO_ZONAL_GAS_HUB_PATH, year
    )


def apply_caiso_zonal_gas_basis(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
) -> None:
    """Shift each CAISO gas unit's price by its zone's measured citygate basis.

    Delegates to :func:`_apply_meanzero_zonal_gas_basis` — the shared
    capacity-weighted mean-zero core PJM/MISO use. NP15/ZP26 price off PG&E
    Citygate and LA_BASIN/SDGE/SP15_rest off SoCal Citygate (measured weekly
    prints, :data:`CAISO_ZONAL_GAS_HUB_PATH`), so the two halves of CAISO stop
    sharing one blended CA-composite gas price and the measured north-south
    marginal-cost gradient reaches the merit order; the fleet-aggregate gas
    level (the calibrated composite + transport) is preserved by the
    mean-zero anchor.

    Gated on ``config.caiso_zonal_gas_basis`` and ``config.iso == "CAISO"``
    (default-off; see the field docstring on ScenarioConfig), so every other
    ISO and every existing CAISO keeper replay is byte-identical. Mutates
    ``fuel_prices`` in place; idempotent given the same inputs.
    """
    _apply_meanzero_zonal_gas_basis(
        fuel_prices,
        fleet,
        config,
        year,
        iso="CAISO",
        config_field="caiso_zonal_gas_basis",
        hub_path=CAISO_ZONAL_GAS_HUB_PATH,
        path_override=Path(path) if path else None,
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
    hh = _henry_hub_monthly(henry_hub_path)
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
    config: ScenarioConfig,
    fleet: FleetArrays,
    year: int,
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
      2. **Coal** units pay :data:`COAL_PRICE_BASE` escalated to ``year``:
         in forecast mode via the AEO2025 real-growth ratio
         (:func:`resolve_annual_coal_price`); in backcast mode via the flat
         :data:`COAL_PRICE_ESCALATION` rate (unchanged), then (historical
         years, ``coal_plant_monthly_pricing`` on) overwritten by each
         plant's own measured EIA-923 monthly delivered cost where reported.
         Months with no reported cost keep the trajectory.

    Hydrogen turbines (``hydrogen_ct``, ``hydrogen_ccgt``) pay the
    derived hydrogen fuel cost from
    :func:`market_sim.data.hydrogen.compute_h2_fuel_cost`. Oil units
    (``oil``) pay the AEO2025 oil-price trajectory in forecast mode
    (:func:`resolve_annual_oil_price`) or the flat delivered price
    (:data:`~market_sim.config.constants.OIL_PRICE_PER_MMBTU`) in backcast
    mode. Biomass units (``biomass``) pay the delivered biomass fuel cost
    (:data:`~market_sim.config.constants.BIOMASS_PRICE_PER_MMBTU`). Nuclear
    units (``nuclear``) pay the EIA-uranium-marketing-derived fuel-cycle cost
    (:func:`resolve_nuclear_fuel_price`) in both modes. All other generators
    (wind, solar, hydro, imports) carry a zero fuel price.

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
        gas_price_hourly = delivered_annual * gas_seasonal_shape(config, year, T)
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

    # Daily Henry Hub within-month shape: the monthly level above is correct
    # (trajectory / measured ISO-month), and this multiplies in the real
    # day-to-day commodity swing the marginal gas unit's bid would track,
    # mean-preserving per month so the annual gas burn is unchanged. This is
    # the gas price the gas units actually bid at, so it is shaped here (the
    # coal-sigmoid reference in _gas_series is shaped identically).
    if getattr(config, "gas_daily_shape", False):
        gas_price_hourly = gas_price_hourly * gas_daily_shape_factors(year, T)

    if config.mode == "forecast":
        # Forecast years track the AEO2025 national coal-price REAL GROWTH
        # applied to the ISO's own delivered-cost anchor (resolve_annual_coal_price)
        # rather than the flat, uncited COAL_PRICE_ESCALATION rate.
        coal_price = resolve_annual_coal_price(config, year)
    else:
        # Backcast: unchanged flat-escalation fallback (superseded within the
        # backcast window by the EIA-923 monthly overwrite pass below for any
        # plant/month with reported delivered cost).
        coal_price = COAL_PRICE_BASE[config.iso] * (1.0 + COAL_PRICE_ESCALATION) ** (
            year - START_YEAR
        )

    fuel_type_idx = fleet.fuel_type_idx
    fuel_prices = np.zeros((fleet.n_gen, T), dtype=float)
    fuel_prices[np.isin(fuel_type_idx, _GAS_FUEL_IDX)] = gas_price_hourly
    fuel_prices[fuel_type_idx == _COAL_FUEL_IDX] = coal_price

    # Oil (distillate/residual) and biomass burn at a flat delivered cost in
    # backcast (oil sits far above gas — peaker economics — and any measured
    # EIA-923 receipts take precedence via the dual-fuel pass below); forecast
    # years use the AEO2025 delivered-oil trajectory. Biomass has no commodity
    # trajectory or F923 plant-monthly override at all.
    oil_price = (
        resolve_annual_oil_price(config, year)
        if config.mode == "forecast"
        else OIL_PRICE_PER_MMBTU
    )
    fuel_prices[fuel_type_idx == _OIL_FUEL_IDX] = oil_price
    fuel_prices[fuel_type_idx == _BIOMASS_FUEL_IDX] = BIOMASS_PRICE_PER_MMBTU

    # Nuclear burns a real, priced fuel (EIA-uranium-marketing-derived
    # fuel-cycle cost) in both backcast and forecast — not the non-fuel-burning
    # $0 default (D2 fix).
    fuel_prices[fuel_type_idx == _NUCLEAR_FUEL_IDX] = resolve_nuclear_fuel_price(
        config, year
    )

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
        # NYISO: shift each gas unit to its zone's measured pipeline-hub level
        # so the east marginal gas stays dearer than the west (the structural
        # source of the upstate-cheap / east-dear LMP spread). Before dual-fuel
        # so oil parity still caps any winter blowout.
        apply_nyiso_zonal_gas_basis(fuel_prices, fleet, config, year)
        # ERCOT: shift each gas unit to its zone's measured regional hub basis
        # (Waha-cheap West/Permian, dearer North/East-Texas and South) so the
        # merit order stops over-running DFW/North CCs on flat Waha-discounted
        # gas. Mean-zero anchored, so the aggregate gas level is unchanged.
        # Before dual-fuel so oil parity still caps any winter blowout.
        apply_ercot_zonal_gas_basis(fuel_prices, fleet, config, year)
        # PJM: shift each gas unit to its zone's measured regional gas basis
        # (west coal belt cheap, eastern EMAAC/SWMAAC/Dominion dear) so PJM stops
        # clearing as a single copper-plate and the internal TTCs bind.
        # Capacity-weighted mean-zero, so the aggregate gas level is unchanged.
        # Before dual-fuel so oil parity still caps any winter blowout.
        apply_pjm_zonal_gas_basis(fuel_prices, fleet, config, year)
        # MISO: shift each gas unit to its zone's measured regional gas basis
        # (North on MidCon/Northern Natural, Central on Chicago Citygate, South
        # on Gulf Coast). Same mean-zero core as PJM. Before dual-fuel so oil
        # parity still caps any winter blowout.
        apply_miso_zonal_gas_basis(fuel_prices, fleet, config, year)
        # CAISO: shift each gas unit to its zone's measured citygate basis
        # (NP15/ZP26 on PG&E Citygate, SP15 on SoCal Citygate) so the two
        # halves of CAISO stop sharing one blended composite gas price. Same
        # mean-zero core as PJM/MISO. Before dual-fuel so oil parity still
        # caps any winter blowout.
        apply_caiso_zonal_gas_basis(fuel_prices, fleet, config, year)
        apply_dual_fuel_pricing(fuel_prices, fleet, config, year)

    return fuel_prices


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
    """
    fallback = (
        resolve_annual_oil_price(config, year)
        if config.mode == "forecast"
        else OIL_PRICE_PER_MMBTU
    )
    monthly = iso_monthly_oil_prices(config, year, monthly_costs_path)
    if monthly is None:
        return np.full(config.hours, fallback, dtype=float)
    filled = np.where(np.isnan(monthly), fallback, np.asarray(monthly, dtype=float))
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
    capable = dual_fuel_plant_groups()
    if not capable:
        return mask
    oil_hourly = dual_fuel_oil_price_series(config, year, monthly_costs_path)
    is_gas = np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX)
    for g in np.nonzero(is_gas)[0]:
        if (int(fleet.plant_code[g]), str(groups[g])) not in capable:
            continue
        mask[g] = fuel_prices[g] > oil_hourly
    return mask


def load_oil_burn_budget(
    iso: str,
    year: int,
    fleet: "FleetArrays",
    monthly_costs_path: Path | None = None,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Return ``(oil_gen_idx, monthly_budget_mwh)`` for the oil inventory constraint.

    Derives a monthly oil-burn cap (MWh) from measured EIA-923 Schedule 5
    Petroleum receipts — the ISO's total monthly petroleum heat-input
    (MMBtu), allocated pro-rata by nameplate to each oil-primary generator
    in the fleet, then converted to MWh via that generator's heat rate.
    The result is a per-generator monthly budget exactly like the hydro
    family (one LP row per generator × month).

    Scope is **oil-primary generators only** (``fuel_type_idx ==
    FUEL_TYPE_MAP["oil"]``). Dual-fuel gas units are excluded: their oil
    consumption is not captured in F923 petroleum receipts (they report as
    gas plants), so constraining them with this budget would produce a
    budget far below actual consumption and make the LP infeasible.

    When no EIA-923 petroleum data exists for the ISO-year, returns
    ``None`` (the caller skips the constraint, identical LP).

    Source: EIA-923 Schedule 5 monthly Petroleum receipts (quantity in
    MMBtu) — measured oil DELIVERIES, the physical stock of distillate
    available to burn. This is a reproducible deliverability input whose
    forward analogue is a seasonal oil-storage/contract assumption
    (CLAUDE.md #10). NOT sized to land a target number of >$300 hours.

    Args:
        iso: ISO identifier.
        year: Calendar year.
        fleet: Vectorized fleet arrays carrying ``fuel_type_idx``,
            ``plant_code``, ``plant_group``, ``pmax``, ``heat_rate``.
        monthly_costs_path: Optional override for the F923 parquet path.

    Returns:
        ``(oil_gen_idx, monthly_budget_mwh)`` with ``oil_gen_idx`` shape
        ``(n_oil,)`` (thermal-block column indices) and
        ``monthly_budget_mwh`` shape ``(n_oil, 12)`` in MWh; or ``None``
        when no measured data exists.
    """
    costs = _load_monthly_cache(monthly_costs_path)
    if costs is None or year not in available_years(costs):
        return None
    from market_sim.data.zone_assignment import build_zone_lookup

    try:
        iso_plants = frozenset(build_zone_lookup(iso.upper()))
    except Exception:
        return None
    if not iso_plants:
        return None

    # Total ISO petroleum receipts by month (MMBtu).
    sub = costs[
        (costs["year"] == year)
        & (costs["fuel_group"] == "Petroleum")
        & costs["plant_id"].isin(iso_plants)
    ]
    if sub.empty:
        return None
    iso_monthly_mmbtu = np.zeros(12, dtype=float)
    for m, qty in sub.groupby("month")["quantity"].sum().items():
        iso_monthly_mmbtu[int(m) - 1] = float(qty)
    if iso_monthly_mmbtu.sum() <= 0:
        return None

    # Identify oil-primary generators only (fuel_type_idx == oil).
    oil_idx = FUEL_TYPE_MAP["oil"]
    oil_gen_idx = np.flatnonzero(np.asarray(fleet.fuel_type_idx) == oil_idx)
    if oil_gen_idx.size == 0:
        return None

    # Allocate the ISO-level monthly MMBtu budget pro-rata by nameplate MW.
    pmax = np.asarray(fleet.pmax, dtype=float)
    total_oil_mw = pmax[oil_gen_idx].sum()
    if total_oil_mw <= 0:
        return None
    shares = pmax[oil_gen_idx] / total_oil_mw  # (n_oil,)

    # Convert each generator's MMBtu allocation to MWh: MWh = MMBtu / HR.
    hr = np.asarray(fleet.heat_rate, dtype=float)[oil_gen_idx]
    hr = np.where(hr > 0, hr, 10.0)  # fallback HR for safety
    monthly_budget_mwh = np.outer(shares, iso_monthly_mmbtu) / hr[:, None]

    # Check how many reporting plants actually contributed to these receipts.
    n_reporting = sub["plant_id"].nunique()
    finite_months = int((iso_monthly_mmbtu > 0).sum())
    finite_mwh = monthly_budget_mwh[:, iso_monthly_mmbtu > 0].sum()

    # Skip when petroleum receipt coverage is too sparse to be a meaningful
    # fleet-wide constraint: fewer than half the months have any deliveries,
    # or the budget derives from fewer reporting plants than the constrained
    # fleet. F923 receipts measure deliveries to tank, not inventory; gaps
    # mean the tank wasn't refilled, not that no oil was available.
    if finite_months < 6 or n_reporting < max(2, oil_gen_idx.size // 20):
        logger.info(
            "oil burn budget (%s %d): SKIPPED — F923 petroleum receipts "
            "too sparse (%d reporting plant(s), %d/12 months with "
            "deliveries, %.1f GWh) to constrain %d generators (%.0f MW)",
            iso,
            year,
            n_reporting,
            finite_months,
            finite_mwh / 1e3,
            oil_gen_idx.size,
            total_oil_mw,
        )
        return None

    # Months with zero receipts are unconstrained (inf) — zero deliveries
    # does not mean zero available fuel; plants burn from tank inventory.
    monthly_budget_mwh[:, iso_monthly_mmbtu <= 0] = np.inf

    n_oil = oil_gen_idx.size
    logger.info(
        "oil burn budget (%s %d): %d oil-capable generators "
        "(%.0f MW, %.1f GWh annual budget from EIA-923 petroleum receipts, "
        "%d/12 months constrained, %d reporting plant(s))",
        iso,
        year,
        n_oil,
        total_oil_mw,
        finite_mwh / 1e3,
        finite_months,
        n_reporting,
    )
    return oil_gen_idx, monthly_budget_mwh


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
    so ERCOT — whose plants overwhelmingly report — is unchanged. Under
    ``config.class_aware_fuel_price_fallback`` the fallback consults a
    same-class donor tier (the recipient's ``plant_group``) before the
    class-blind fuel-group pools — see :class:`_NearbyFuelPrices`.

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
    # Daily Henry Hub within-month swing for GAS plant-months: the flat F923
    # monthly overwrite below would erase the daily commodity shape
    # resolve_fuel_prices already applied under ``gas_daily_shape``, leaving
    # the merit order blind to the intra-month gas troughs/spikes the marginal
    # gas unit's bid actually tracks (the miso-50 root cause: coal-vs-gas
    # flip days are unresolvable on a flat plant-month). Re-carry the
    # mean-preserving factors onto every overwritten gas plant-month so the
    # plant's measured monthly level is kept exactly and only the within-month
    # shape rides on top. Coal/oil monthly costs stay flat (delivered coal has
    # no daily commodity market at the plant burner tip).
    gas_daily = (
        gas_daily_shape_factors(year, T)
        if getattr(config, "gas_daily_shape", False)
        else None
    )
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
                    if gas_daily is not None and fuel_group == "Natural Gas":
                        fuel_prices[g, mask] = own[m] * gas_daily[mask]
                    else:
                        fuel_prices[g, mask] = own[m]
            n_overwrites += 1

        # 2) Nearby-plant fallback fills the still-unreported months.
        if nearby is not None and not reported.all():
            st = str(states[g]) if states is not None else ""
            klass = str(fleet.plant_group[g]) if fleet.plant_group is not None else None
            fill = nearby.month_prices(fuel_group, st, int(fleet.zone_idx[g]), klass)
            applied = False
            for m in np.nonzero(~reported)[0]:
                v = fill[m]
                if np.isnan(v):
                    continue
                mask = month_idx == m
                if mask.any():
                    if gas_daily is not None and fuel_group == "Natural Gas":
                        fuel_prices[g, mask] = v * gas_daily[mask]
                    else:
                        fuel_prices[g, mask] = v
                    applied = True
            if applied:
                n_nearby += 1

    if n_overwrites or n_nearby:
        logger.info(
            "F923 fuel costs for %d: %d generators priced from their own "
            "plant, %d gap-filled from nearby (state/zone) plants",
            year,
            n_overwrites,
            n_nearby,
        )


class _NearbyFuelPrices:
    """ISO-restricted state/zone "nearby plant" fuel-cost fallback grids.

    Lazily builds, per EIA-923 ``fuel_group``, the quantity-weighted monthly
    delivered cost of the current ISO's reporting plants aggregated two ways:
    by USPS state (with a reporter count) and by model zone index. A plant
    missing its own cost in a month is filled from its state mean when the
    state cleared the sample floor, otherwise from its zone mean. Both are
    drawn only from the ISO's own fleet, so no cross-ISO price leaks in.

    Under ``config.class_aware_fuel_price_fallback`` (and a fleet carrying
    ``plant_group``), a same-class donor tier is consulted first: the
    state/zone grids restricted to reporting plants whose capacity-dominant
    model class (within the fuel group) matches the recipient generator's
    class. The class-blind fuel-group-wide grids remain the fallback, so a
    class with no reporting peers fills exactly as before. Rationale: the
    fuel-group pool is quantity-weighted, so for gas it is CC-burn-dominated
    and prices a non-filing CT ~$1.6/MMBtu below its measured class cost
    (docs/DIAGNOSIS-miso-july2025-lmp-2026-07.md §6).
    """

    def __init__(
        self,
        costs: pd.DataFrame,
        year: int,
        fleet: FleetArrays,
        config: ScenarioConfig,
    ) -> None:
        self._year = year
        self._min_state = int(getattr(config, "nearby_fuel_price_min_state_plants", 2))
        iso_plants = {int(p) for p in fleet.plant_code if int(p) > 0}
        self._plant_to_zone = {
            int(p): int(z)
            for p, z in zip(fleet.plant_code, fleet.zone_idx)
            if int(p) > 0
        }
        self._iso_costs = costs[
            (costs["year"] == year) & (costs["plant_id"].isin(iso_plants))
        ]
        # Per (fuel_group, class-or-None): (state_price, state_count,
        # zone_price) grids. The ``None`` key is the class-blind pool.
        self._cache: dict[tuple[str, str | None], tuple[dict, dict, dict]] = {}
        self.class_aware = (
            bool(getattr(config, "class_aware_fuel_price_fallback", False))
            and fleet.plant_group is not None
        )
        # Donor plants are classified by their capacity-dominant model class
        # within each fuel group (F923 files at plant level, so a mixed CC+CT
        # plant's gas receipts go to whichever class holds most of its MW).
        self._plant_class: dict[str, dict[int, str]] = {}
        if self.class_aware:
            cap: dict[str, dict[int, dict[str, float]]] = {}
            for g in range(fleet.n_gen):
                p = int(fleet.plant_code[g])
                if p <= 0:
                    continue
                fg = _F923_FUEL_GROUP_BY_FUEL.get(_fuel_name(fleet.fuel_type_idx[g]))
                if fg is None:
                    continue
                klass = str(fleet.plant_group[g])
                by = cap.setdefault(fg, {}).setdefault(p, {})
                by[klass] = by.get(klass, 0.0) + float(fleet.pmax[g])
            self._plant_class = {
                fg: {p: max(by, key=by.get) for p, by in plants.items()}
                for fg, plants in cap.items()
            }

    def _grids(
        self, fuel_group: str, klass: str | None = None
    ) -> tuple[dict, dict, dict]:
        cached = self._cache.get((fuel_group, klass))
        if cached is not None:
            return cached
        sub = self._iso_costs[self._iso_costs["fuel_group"] == fuel_group]
        if klass is not None:
            donor_class = self._plant_class.get(fuel_group, {})
            sub = sub[sub["plant_id"].map(lambda p: donor_class.get(int(p))) == klass]
        state_price, state_count = state_month_price_grid(sub, self._year, fuel_group)
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
                    zone_price[int(zone)] = np.where(qsum > 0.0, wsum / qsum, np.nan)
        result = (state_price, state_count, zone_price)
        self._cache[(fuel_group, klass)] = result
        return result

    def month_prices(
        self,
        fuel_group: str,
        state: str,
        zone_idx: int,
        klass: str | None = None,
    ) -> np.ndarray:
        """Return a length-12 fill price array (NaN where no nearby data).

        Each tier fills only the months still NaN after the tiers before it:
        same-class state → same-class zone (class-aware mode only), then
        fuel-group state → fuel-group zone.
        """
        tiers = []
        if self.class_aware and klass:
            tiers.append(self._grids(fuel_group, str(klass)))
        tiers.append(self._grids(fuel_group))
        out = np.full(12, np.nan, dtype=float)
        for state_price, state_count, zone_price in tiers:
            sp = state_price.get(state)
            if sp is not None:
                sc = state_count.get(state)
                ok = (
                    (sc >= self._min_state) & ~np.isnan(sp)
                    if sc is not None
                    else ~np.isnan(sp)
                )
                fill = np.isnan(out) & ok
                out[fill] = sp[fill]
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
# Mine-mouth lignite / PRB-by-rail base levels and trajectory shares now live
# in constants.py (LIGNITE_PRICE_2023_25, PRB_PRICE_BY_YEAR, PRB_*_SHARE,
# PRB_COMMODITY_DECLINE, PRB_COMMODITY_FLAT_THROUGH) — measured delivered-fuel-
# cost inputs (CLAUDE.md rule #13), not a fitted/residual value.


def _build_coal_price_trajectories() -> tuple[dict[int, float], dict[int, float]]:
    """Return ``(lignite, prb)`` delivered-cost dicts spanning 2023-END_YEAR."""
    lignite: dict[int, float] = {}
    prb: dict[int, float] = {}
    for y in (2023, 2024, 2025):
        lignite[y] = LIGNITE_PRICE_2023_25
        prb[y] = PRB_PRICE_BY_YEAR[y]

    avg_prb = sum(PRB_PRICE_BY_YEAR.values()) / 3.0
    commodity_base = PRB_COMMODITY_SHARE * avg_prb
    rail_diesel = PRB_RAIL_DIESEL_SHARE * avg_prb  # held flat forward
    rail_nondiesel_base = PRB_RAIL_NONDIESEL_SHARE * avg_prb
    for y in range(2026, END_YEAR + 1):
        lignite[y] = LIGNITE_PRICE_2023_25 * (1.0 + INFLATION_RATE) ** (y - 2025)
        if y <= PRB_COMMODITY_FLAT_THROUGH:
            commodity = commodity_base
        else:
            commodity = commodity_base * (1.0 - PRB_COMMODITY_DECLINE) ** (
                y - PRB_COMMODITY_FLAT_THROUGH
            )
        rail_nondiesel = rail_nondiesel_base * (1.0 + INFLATION_RATE) ** (y - 2026)
        prb[y] = commodity + rail_diesel + rail_nondiesel
    return lignite, prb


COAL_PRICE_LIGNITE_BY_YEAR, COAL_PRICE_PRB_BY_YEAR = _build_coal_price_trajectories()


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
    from market_sim.data.coal import COAL_PLANT_SUPPLY

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
            monthly[int(month) - 1] = float(
                np.average(mrows["price_per_mmbtu"], weights=mrows["quantity"])
            )
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
