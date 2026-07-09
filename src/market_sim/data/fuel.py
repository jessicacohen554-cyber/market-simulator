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
    END_YEAR,
    GAS_BASIS_DIFFERENTIAL,
    GAS_MONTHLY_SEASONALITY,
    HENRY_HUB_TRAJECTORIES,
    HOURS_PER_YEAR,
    INFLATION_RATE,
    LIGNITE_PRICE_2023_25,
    OIL_PRICE_PER_MMBTU,
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

# Fuel price ($/MMBtu) for non-fuel-burning units (e.g. wind, solar, nuclear,
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
    if year in trajectory:
        henry_hub = trajectory[year]
    else:
        # Extrapolate beyond the trajectory using the last growth rate.
        last_year = max(trajectory)
        annual_growth = trajectory[last_year] / trajectory[last_year - 1]
        henry_hub = trajectory[last_year] * annual_growth ** (year - last_year)

    return henry_hub * config.gas_price_factor + basis


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
    if getattr(config, "gas_daily_shape", False):
        # Inject the within-month daily commodity swing onto the correctly-
        # levelled monthly series (mean-preserving, so the annual mix holds).
        series = series * gas_daily_shape_factors(year, hours)
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
# Joaquin Valley between Paths 15 and 26) and LA_BASIN/SDGE/SP15_rest on
# **SoCal Citygate** (SoCalGas/SDG&E). The committed rows are month-balanced
# annual means of the EIA NG Weekly Update archive's weekly Wednesday prints
# (NGI Daily GPI; scripts/fetch_pge_socal_citygate_daily.py +
# derive_caiso_zonal_gas_hub.py), the same free published print the ERCOT
# Waha rows cite. Measured N-S spread (PG&E − SoCal): −0.49 (2023) / +0.54
# (2024) / −0.18 (2025) $/MMBtu — real but year-varying, so it enters as
# data, never as a fitted north-premium knob. Like PJM/MISO/ERCOT this is
# anchored to a gas-capacity-weighted mean of zero in
# :func:`apply_caiso_zonal_gas_basis`, so the calibrated CAISO aggregate gas
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


def gas_daily_shape_factors(
    year: int, hours: int, path: Path | None = None
) -> np.ndarray:
    """Return ``(hours,)`` within-month daily gas-price shape factors.

    Each calendar day's factor is the measured Henry Hub daily spot divided by
    that month's own daily mean, so the factors average to 1.0 within every
    month — multiplying the (correctly-levelled) monthly gas series by them
    adds the real intra-month commodity swing while leaving the monthly mean,
    and hence the annual generation mix, unchanged. The daily spot has only
    trading days; the (typically ~21) quotes are spread evenly across the
    month's calendar days (a weekend inherits the bracketing trading values'
    block), and a month with no quotes resolves to all-ones (no shape). This
    is the same mechanism a forecast would use (a forward monthly level times
    a representative daily shape), so it is not backcast-only.
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
                # days, then repeat each day's factor across its 24 hours.
                day_factor = np.interp(
                    np.linspace(0.0, 1.0, n_days),
                    np.linspace(0.0, 1.0, len(arr)),
                    arr / mean,
                )
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
