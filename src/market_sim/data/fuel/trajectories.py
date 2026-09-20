"""Annual fuel-price trajectories and the gas-keyed coal passthrough curves.

The per-year resolvers (gas / coal / oil / nuclear / NOx), the monthly gas
seasonality shapes, and the coal supply-chain passthrough sigmoids keyed off
the delivered gas series. Split out of ``data/fuel.py`` (W-D3;
refactor-consolidation plan §5 item 3) as pure code motion; the historically
monkeypatched loader names (``_henry_hub_monthly``,
``iso_monthly_gas_prices``, ``ercot_electric_power_gas_basis``) are resolved
through the package namespace at call time (:func:`._shared._pkg_ns`).
"""

from __future__ import annotations

import numpy as np

from market_sim.config.constants import (
    COAL_PRICE_BASE,
    COAL_PRICE_TRAJECTORIES,
    GAS_BASIS_DIFFERENTIAL,
    GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR,
    GAS_MONTHLY_SEASONALITY,
    HENRY_HUB_TRAJECTORIES,
    HOURS_PER_YEAR,
    NUCLEAR_FUEL_PRICE_HISTORICAL,
    OIL_PRICE_PER_MMBTU,
    OIL_PRICE_TRAJECTORIES,
)
from market_sim.config.scenarios import COAL_SIGMOID_DEFAULTS, ScenarioConfig

from ._shared import _DAYS_IN_MONTH, _expand_monthly_to_hourly, _pkg_ns
from .hubs import _hub_overlay_series


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


def resolve_gas_scenario_path(config: ScenarioConfig, year: int) -> str:
    """Return the ``HENRY_HUB_TRAJECTORIES`` key this scenario-year prices on.

    The one place the crossover fuel seam is decided (rule 19 ``[R-ONE-MECH]``):
    a T1-X/T1-FF crossover's FORWARD years (``>= crossover_forward_year``) price
    gas on ``config.crossover_forward_gas_path`` — the AEO trajectory a pure
    forecast uses — while its in-sample years keep ``config.gas_price_path``
    (the realized hindcast fuel). Every non-crossover run
    (``crossover_forward_year is None``) returns ``config.gas_price_path``
    unchanged, so backcast and plain-forecast callers are byte-identical.

    Split out of :func:`resolve_annual_gas_price` (FFR-2A / audit FR-9) because
    the ISO's own gas price was not the only consumer: the neighbor-seam
    reference price (``runner.py`` → ``apply_interchange_injections`` →
    ``data.neighbor_price``) passed ``config.gas_price_path`` unconditionally,
    so a crossover's forward years priced the import seam off the realized
    path — a ``KeyError`` on ``hindcast_realized`` (keys 2021/2023–2025), or a
    measured level held flat into a forward year, depending on the caller. Both
    callers now resolve the path here.

    Args:
        config: Scenario configuration supplying the two path fields and the
            crossover boundary.
        year: Calendar year to resolve.

    Returns:
        The trajectory key to index ``HENRY_HUB_TRAJECTORIES`` with.
    """
    if config.is_crossover_forward_year(year):
        return config.crossover_forward_gas_path
    return config.gas_price_path


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
    # Per-YEAR MEASURED basis (lane SOCO-55, 2026-09-20;
    # ``gas_basis_differential_measured_by_year``). The scalar above is ONE
    # year's measurement applied to every year, and its own comment registers
    # it as a "forward-year / fallback value only" — but SOCO-54 promoted it
    # onto SOCO's PRIMARY backcast gas-pricing path by turning
    # ``gas_plant_monthly_fuel_pricing`` off, so in a SOCO backcast 2023 was
    # carrying a measured +0.15 $/MMBtu error on every gas unit. When armed,
    # the year's OWN measured basis REPLACES the scalar (rule 19
    # [R-ONE-MECH] — one basis, never a scalar plus an adjustment). A year
    # with no measured row (a forecast year, or any ISO but the ones with a
    # table entry) falls through to the scalar unchanged, so the forward path
    # and every unarmed ISO are inert by construction (rules 13 / 25).
    if getattr(config, "gas_basis_differential_measured_by_year", False):
        _measured = GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR.get(config.iso)
        if _measured is not None and int(year) in _measured:
            basis = _measured[int(year)]
    if config.gas_price_override is not None:
        return config.gas_price_override + basis

    # T1-X crossover forward years (FF-0E, plan §2.2): the realized-fuel
    # "hindcast_realized" path only carries 2021/2023-2025 and would hold the
    # 2025 value flat past 2025 — that is a measured overlay held flat, NOT the
    # forecast fuel methodology. A crossover's forward years (>= the boundary)
    # must price gas on the AEO trajectory (config.crossover_forward_gas_path),
    # the same forward driver a pure forecast uses. In-sample years (< boundary)
    # keep config.gas_price_path (the realized hindcast fuel). No-op for every
    # non-crossover run (crossover_forward_year is None). Since FFR-2A the
    # choice itself lives in resolve_gas_scenario_path, shared with the
    # neighbor-seam reference price (audit FR-9) — one mechanism, one key.
    path = resolve_gas_scenario_path(config, year)
    trajectory = HENRY_HUB_TRAJECTORIES[path]
    # T1-FF back-hold trap (FH-1, hindcast-forward plan §4 row 7): the AEO
    # low/mid/high paths knot from 2023, so a full-forward year below a
    # trajectory's earliest knot would silently take the earliest knot's value
    # (_hold_flat_extrapolate's backward hold — e.g. 2021 priced at the 2023
    # $2.54 against a $3.91 actual, ~35% wrong, with no warning). In a
    # full-forward hindcast that is a hard error: the arm must name a
    # trajectory that actually covers its window (hindcast_realized /
    # hindcast_asknown_*), never inherit a back-held forecast knot.
    if getattr(config, "is_full_forward_hindcast", False) and year < min(trajectory):
        raise ValueError(
            f"T1-FF gas back-hold trap: year {year} is below the earliest "
            f"knot ({min(trajectory)}) of gas trajectory {path!r} — a "
            "full-forward hindcast must price every solve year from a "
            "trajectory that covers it (FH-1, hindcast-forward plan §4 row 7)"
        )
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
        hh = _pkg_ns()._henry_hub_monthly(None)
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


def _electric_power_level_series(
    series: np.ndarray, config: ScenarioConfig, year: int, hours: int
) -> np.ndarray:
    """REPLACE the monthly gas LEVEL with the measured N3045 state blend.

    Gated on ``config.gas_electric_power_monthly_level``. The measured level
    (:func:`market_sim.data.fuel.electric_power.iso_electric_power_monthly_level`)
    supersedes whatever set the level before it — the annual trajectory
    x generic shape, or the EIA-923 ISO-month receipts under
    ``gas_monthly_actuals`` — rather than stacking on it (rule 19
    ``[R-ONE-MECH]``), and is itself superseded in covered months by the
    measured constrained-hub index applied immediately after
    (:func:`._hub_overlay_series`), which is the marginal unit's own
    opportunity cost where one is published. An inadmissible year returns
    ``None`` and the incoming series passes through untouched, so every
    forecast run and every year the mechanism cannot price is byte-identical.
    """
    if not getattr(config, "gas_electric_power_monthly_level", False):
        return series
    level = _pkg_ns().iso_electric_power_monthly_level(config.iso, year)
    if level is None:
        return series
    return _expand_monthly_to_hourly(np.asarray(level, dtype=float), hours)


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
        measured = _pkg_ns().iso_monthly_gas_prices(config, year)
        if measured is not None:
            hourly_measured = _expand_monthly_to_hourly(
                np.asarray(measured, dtype=float), hours
            )
            series = np.where(np.isnan(hourly_measured), series, hourly_measured)
    series = _electric_power_level_series(series, config, year, hours)
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
        ep_basis = _pkg_ns().ercot_electric_power_gas_basis(year)
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


def resolve_nox_price(config: ScenarioConfig) -> float:
    """Return the NOx price ($/ton NOx) for the given scenario.

    Args:
        config: Scenario configuration supplying ``nox_price``.

    Returns:
        The NOx price in $/ton NOx.
    """
    return config.nox_price
