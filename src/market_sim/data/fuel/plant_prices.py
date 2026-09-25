"""EIA-923 plant/ISO-month delivered fuel costs (F923 receipt machinery).

The F923 monthly-cost cache, the ISO-month volume-weighted gas/oil series, the
plant-monthly overwrite pass (:func:`apply_plant_monthly_fuel_prices`) with its
ISO-restricted nearby-plant fallback grids (:class:`_NearbyFuelPrices`), and
the measured oil-burn budget. Split out of ``data/fuel.py`` (W-D3;
refactor-consolidation plan §5 item 3) as pure code motion;
``_load_monthly_cache`` is resolved through the package namespace at call time
(:func:`._shared._pkg_ns`) because tests patch it on the facade.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.plant_taxonomy import artifact_class
from market_sim.config.constants import F923_GAS_PRICE_PLAUSIBILITY_BAND
from market_sim.config.paths import GAS_PRICES_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.eia923 import (
    EIA923_MONTHLY_COSTS_PATH,
    available_years,
    load_monthly_fuel_costs,
    plant_month_price_grid,
    state_month_price_grid,
)
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays

from ._shared import _month_index, _pkg_ns, logger
from .basis.ercot import _MCF_TO_MMBTU
from .hubs import gas_daily_shape_factors


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
    costs = _pkg_ns()._load_monthly_cache(monthly_costs_path)
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
    costs = _pkg_ns()._load_monthly_cache(monthly_costs_path)
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


#: EIA delivered-to-electric-power gas price by state, monthly ($/Mcf): series
#: ``N3045<ST>3`` for every state plus ``N3045US3``, the reference the EIA-923
#: own-month plausibility screen reads (SPP-46 R-1 / SPP-49; source note
#: ``data/raw/gas-prices/SOURCES_eia_delivered_gas_electric_power_by_state.md``).
EIA_STATE_ELECTRIC_POWER_GAS_PATH: Path = (
    GAS_PRICES_DIR / "eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv"
)
#: EIA's aggregate series key in that table — the documented fallback for a
#: state-month EIA has not published (many states' 2025 and most pre-2022).
_STATE_EP_GAS_US: str = "US"
#: The F923 fuel group the screen applies to. Coal and petroleum are not
#: screened: P19 names the gas seam, and their delivered costs have no
#: state-level EIA reference of this kind.
_SCREENED_FUEL_GROUP: str = "Natural Gas"

_STATE_EP_GAS_CACHE: dict[Path, dict[tuple[str, int, int], float]] = {}


def load_state_electric_power_gas_prices(
    path: str | Path | None = None,
) -> dict[tuple[str, int, int], float] | None:
    """Return ``{(state, year, month): $/MMBtu}`` from the EIA N3045 table, or ``None``.

    ``N3045<ST>3`` / ``N3045US3`` ($/Mcf) converted at :data:`_MCF_TO_MMBTU`;
    unpublished (``NA``) cells are absent from the mapping. ``None`` when the
    CSV is not on disk — the caller then reports loudly that the screen cannot
    run and passes the frame through, the same absent-input posture the F923
    parquet itself has at this seam. Cached per path for the process.
    """
    resolved = Path(path) if path is not None else EIA_STATE_ELECTRIC_POWER_GAS_PATH
    if resolved in _STATE_EP_GAS_CACHE:
        return _STATE_EP_GAS_CACHE[resolved]
    if not resolved.exists():
        return None
    table = pd.read_csv(resolved, usecols=["state", "year", "month", "price_usd_mcf"])
    price = pd.to_numeric(table["price_usd_mcf"], errors="coerce")
    out = {
        (str(st).strip().upper(), int(y), int(m)): float(v) / _MCF_TO_MMBTU
        for st, y, m, v in zip(table["state"], table["year"], table["month"], price)
        if pd.notna(v)
    }
    _STATE_EP_GAS_CACHE[resolved] = out
    return out


def state_reference_gas_price(
    table: dict[tuple[str, int, int], float], state: str, year: int, month: int
) -> tuple[float, str]:
    """Return ``(reference $/MMBtu, provenance)`` for one state-month.

    Provenance is ``"state"`` (the plant's own state's series), ``"us"`` (the
    state-month is unpublished and the US series stands in) or ``"none"``
    (neither is published: the value is NaN and the month cannot be screened).
    """
    v = table.get((state, year, month))
    if v is not None:
        return v, "state"
    v = table.get((_STATE_EP_GAS_US, year, month))
    if v is not None:
        return v, "us"
    return float("nan"), "none"


def screen_gas_plant_month_prices(
    costs: pd.DataFrame,
    year: int,
    table: dict[tuple[str, int, int], float],
    band: tuple[float, float] = F923_GAS_PRICE_PLAUSIBILITY_BAND,
    plant_ids: "frozenset[int] | set[int] | None" = None,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Replace implausible own-reported Natural Gas plant-months by the state reference.

    The EIA-923 own-month plausibility screen (SPP-46 R-1; owner ruling P19;
    ``ScenarioConfig.f923_gas_price_plausibility_screen``). For every
    ``Natural Gas`` row of ``year`` — restricted to ``plant_ids`` when given,
    which the seam sets to the current fleet's plants so the log counts are
    the ISO's own — the reported ``price_per_mmbtu`` is read against the
    plant's OWN state's EIA delivered-to-electric-power price that month
    (:func:`state_reference_gas_price`; ``state`` from the F923 frame, never
    the fleet row — SPP-46 R-7). A price below ``band[0]`` x reference
    (negative prints included) or above ``band[1]`` x reference is replaced by
    the reference; every in-band print is kept byte-for-byte. A state-month
    with no published state series falls to the US series; a month whose
    reference is ``<= 0`` (a real negative-basis print — NM 2024-08, 2025-10)
    has no defined band and is left as reported.

    Both consumers of the frame at this seam read the SCREENED copy: the
    plant's own months (``plant_month_price_grid``) and the nearby-plant pool
    (:class:`_NearbyFuelPrices`), so a donor's implausible month never seeds a
    recipient's fill either (R-1: "the pool is built from screened months").

    Rule posture: rule 14's misalignment exception — an own-reported month
    outside the band is an AVERAGE cost on a different basis than the marginal
    fuel cost the LP prices (a fixed transport charge over a near-zero
    denominator, or a print that is not the cost of the next MMBtu), reconciled
    to a measured delivered price for the same state and month rather than
    replaced by a guess. Zero free parameters: the band is a declared constant
    (rule 1 (c): never swept), the reference is measured, and the construction
    regenerates for any year the two EIA tables cover.

    Returns a copy of ``costs`` (never mutated) and a count report keyed
    ``in_band`` / ``low`` / ``negative`` / ``high`` / ``ref_us`` /
    ``unscreened_no_ref`` / ``unscreened_nonpos_ref`` / ``plants_flagged``.
    """
    low_mult, high_mult = float(band[0]), float(band[1])
    report = {
        "in_band": 0,
        "low": 0,
        "negative": 0,
        "high": 0,
        "ref_us": 0,
        "unscreened_no_ref": 0,
        "unscreened_nonpos_ref": 0,
        "plants_flagged": 0,
    }
    if "state" not in costs.columns:
        return costs, report
    sel = (costs["year"] == year) & (costs["fuel_group"] == _SCREENED_FUEL_GROUP)
    if plant_ids is not None:
        sel &= costs["plant_id"].isin(plant_ids)
    idx = np.flatnonzero(sel.to_numpy())
    if idx.size == 0:
        return costs, report
    sub = costs.iloc[idx]
    states = sub["state"].astype(str).str.strip().str.upper().to_numpy()
    months = sub["month"].to_numpy(dtype=int)
    prices = sub["price_per_mmbtu"].to_numpy(dtype=float)
    plants = sub["plant_id"].to_numpy()
    new_price = prices.copy()
    flagged_plants: set[int] = set()
    for i in range(idx.size):
        ref, prov = state_reference_gas_price(table, states[i], year, int(months[i]))
        if prov == "none":
            report["unscreened_no_ref"] += 1
            continue
        if prov == "us":
            report["ref_us"] += 1
        if ref <= 0.0:
            report["unscreened_nonpos_ref"] += 1
            continue
        p = prices[i]
        if p < 0.0:
            kind = "negative"
        elif p < low_mult * ref:
            kind = "low"
        elif p > high_mult * ref:
            kind = "high"
        else:
            report["in_band"] += 1
            continue
        report[kind] += 1
        new_price[i] = ref
        flagged_plants.add(int(plants[i]))
    report["plants_flagged"] = len(flagged_plants)
    if not flagged_plants:
        return costs, report
    out = costs.copy()
    col = out.columns.get_loc("price_per_mmbtu")
    out.iloc[idx, col] = new_price
    return out, report


def apply_plant_monthly_fuel_prices(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    monthly_costs_path: str | Path | None = None,
    state_gas_reference_path: str | Path | None = None,
) -> np.ndarray:
    """Overwrite per-generator fuel prices with F923 monthly plant costs.

    Returns the ``(n_gen, T)`` boolean mask of the cells this overlay WROTE
    (a plant's own reported month or a nearby-pool fill) — all-False when
    the overlay is a no-op (forecast mode, no table, year outside the
    window). The mask is the print-derived-cell record consumed by
    ``miso_zonal_gas_basis_skip_923_priced`` (miso-213): a cell the print
    path priced already embeds the regional delivered premium the zonal
    basis would add on top (rule 19 ``[R-ONE-MECH]``), so the MISO applier
    can leave those cells alone. Every other caller may ignore the return.

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
    class-blind fuel-group pools — see :class:`_NearbyFuelPrices`. Under
    ``config.nearby_fuel_price_zone_donor_guard`` (caiso-243) the zone tier
    carries the same distinct-reporter floor as the state tier, so a
    zone-month served by a single reporting plant is not trusted (a pool of
    one returned that plant's price verbatim — the 55077 96.161 $/MMBtu
    defect). The state tier is reachable only when the fleet carries
    ``state`` — the plant-level CAMPD-bin fleet does so under
    ``config.fleet_state_from_eia860`` (defect D1 of the same finding).

    **Plausibility screen (SPP-49, owner ruling P19, default ON).** Under
    ``config.f923_gas_price_plausibility_screen`` every own-reported Natural
    Gas plant-month the seam would consume is first read against the plant's
    own state's EIA delivered-to-electric-power price (``N3045<ST>3``,
    :data:`EIA_STATE_ELECTRIC_POWER_GAS_PATH`); a month outside
    :data:`~market_sim.config.constants.F923_GAS_PRICE_PLAUSIBILITY_BAND` x
    that reference falls back to the reference, and the nearby-plant pool is
    built from the screened months — see :func:`screen_gas_plant_month_prices`.
    Reachable only where this overlay prices gas at all (the gate is coerced
    off elsewhere so those configs keep their cache keys). A missing reference
    table is logged as a WARNING and the frame passes through unscreened.

    **Backcast-only (mode gate).** Measured F923 delivered costs are a
    historic overlay (CLAUDE.md rule 22, methodology spec §1.7), so this
    function is a no-op unless ``config.mode == "backcast"`` — year
    availability alone is NOT the forecast gate: the parquet may carry
    measured rows for a forecast year (the H1-2026 intake does) and a
    forecast run must still ignore them (G11 / W2-E; the W1-B smoke found
    forecast-mode 2026 pricing ERCOT 12 / PJM 51 generators from measured
    actuals). Documented exception: the capacity hindcast
    (``config.hindcast``) runs forecast-mode machinery over historical
    years and is *designed* to consume realized historical inputs
    (``hindcast_fuel_variant``, scenarios.py), so it keeps the overlay —
    see the gate comment below.

    A missing parquet or a year outside the F923 window is likewise a
    no-op: every generator keeps the per-fuel default. The same is true
    for plants outside the F923 sample when the fallback is off, per the
    project's "forward = plant-class/zone average" requirement.

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
        state_gas_reference_path: Optional override for the EIA N3045 state
            reference CSV the plausibility screen reads.
    """
    # G11 / W2-E mode gate (rule 22, spec §1.7): measured plant-monthly
    # delivered costs are a backcast-only overlay. The year-availability
    # check below stopped being a forecast gate the moment measured H1-2026
    # receipts were intaken (the parquet now carries the forecast start
    # year). Carve-out: the capacity hindcast (config.hindcast) is
    # forecast-mode by construction and DESIGNED to consume realized
    # historical inputs; its harness bounds the window to <= 2025
    # (scripts/run_capacity_hindcast.py), so no quarantined H1-2026 row can
    # reach it. Both hindcast fuel variants keep the overlay: the
    # realized/asknown pair isolates the GAS trajectory error and shares
    # the delivered-coal channel, so gating one variant would conflate the
    # comparison (owner-approved Option 1, 2026-07-17).
    written = np.zeros((fleet.n_gen, config.hours), dtype=bool)
    if config.mode != "backcast" and not getattr(config, "hindcast", False):
        return written
    # T1-X crossover forward years (FF-0E, plan §2.2): the F923 plant-monthly
    # delivered-cost overlay is a MEASURED backcast/hindcast overlay. A
    # crossover's forward years (>= the boundary) run on forward drivers only —
    # they must NOT read measured F923 receipts (which now carry rows into the
    # forecast start year), so the overlay is skipped and those years fall back
    # to the AEO trajectory coal/gas price. No-op for a plain hindcast or
    # backcast (crossover_forward_year is None → is_crossover_forward_year False).
    if config.is_crossover_forward_year(year):
        return written
    costs = _pkg_ns()._load_monthly_cache(
        Path(monthly_costs_path) if monthly_costs_path else None
    )
    if costs is None or year not in available_years(costs):
        return written

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
    # SPP-49 plausibility screen (owner ruling P19): screen the year's own-
    # reported Natural Gas months against the plant's own state's EIA
    # reference BEFORE either consumer reads the frame, so the plant's own
    # month and the pool it donates to see the same screened value. Only
    # meaningful where gas is priced from F923 at all (the config coerces the
    # gate off otherwise); coal / oil rows are untouched.
    gas_from_f923 = bool(getattr(config, "gas_plant_monthly_fuel_pricing", False))
    if gas_from_f923 and bool(
        getattr(config, "f923_gas_price_plausibility_screen", False)
    ):
        reference = load_state_electric_power_gas_prices(state_gas_reference_path)
        if reference is None:
            logger.warning(
                "F923 gas-price plausibility screen for %d SKIPPED: the EIA "
                "state reference table is absent (%s) — own-reported plant "
                "months are consumed unscreened",
                year,
                state_gas_reference_path or EIA_STATE_ELECTRIC_POWER_GAS_PATH,
            )
        else:
            iso_gas_plants = frozenset(
                int(p)
                for p, f in zip(fleet.plant_code, fleet.fuel_type_idx)
                if int(p) > 0
                and _F923_FUEL_GROUP_BY_FUEL.get(_fuel_name(f)) == _SCREENED_FUEL_GROUP
            )
            costs, screen_report = screen_gas_plant_month_prices(
                costs, year, reference, plant_ids=iso_gas_plants
            )
            logger.info(
                "F923 gas-price plausibility screen for %d (%s, band [%s, %s] x "
                "state N3045 reference): %d plant-months in band, %d low, %d "
                "negative, %d high -> reference (%d plants); %d months on the "
                "US fallback reference, %d unscreened (no reference), %d "
                "unscreened (reference <= 0)",
                year,
                config.iso,
                F923_GAS_PRICE_PLAUSIBILITY_BAND[0],
                F923_GAS_PRICE_PLAUSIBILITY_BAND[1],
                screen_report["in_band"],
                screen_report["low"],
                screen_report["negative"],
                screen_report["high"],
                screen_report["plants_flagged"],
                screen_report["ref_us"],
                screen_report["unscreened_no_ref"],
                screen_report["unscreened_nonpos_ref"],
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
                    written[g, mask] = True
            n_overwrites += 1

        # 2) Nearby-plant fallback fills the still-unreported months.
        if nearby is not None and not reported.all():
            st = str(states[g]) if states is not None else ""
            # Donor class FAMILY: coal pools across its subclasses as ONE class,
            # exactly as the bare COAL group pooled before COAL-SUB (2026-09-25).
            klass = (
                artifact_class(fleet.plant_group[g])
                if fleet.plant_group is not None
                else None
            )
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
                    written[g, mask] = True
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
    return written


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
        # caiso-243 repair form (a): the zone tier's distinct-reporter floor.
        # The SAME registered floor as the state tier (no new constant); 0
        # (the default-off path) keeps the historical unguarded zone mean.
        self._min_zone = (
            self._min_state
            if bool(getattr(config, "nearby_fuel_price_zone_donor_guard", False))
            else 0
        )
        # Per (fuel_group, class-or-None): zone reporter-count grids, the
        # zone-tier companion of ``state_count`` (caiso-243).
        self._zone_count: dict[tuple[str, str | None], dict[int, np.ndarray]] = {}
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
                # Class family (a coal subclass pools as the coal family, the
                # recipient-side key above; COAL-SUB).
                klass = artifact_class(fleet.plant_group[g])
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
        zone_count: dict[int, np.ndarray] = {}
        if not sub.empty:
            z = sub.assign(
                zone=sub["plant_id"].map(self._plant_to_zone),
                weighted=sub["price_per_mmbtu"] * sub["quantity"],
            ).dropna(subset=["zone"])
            for zone, grp in z.groupby("zone", sort=False):
                wsum = np.zeros(12, dtype=float)
                qsum = np.zeros(12, dtype=float)
                # Distinct reporting plants per zone-month (caiso-243): the
                # zone-tier analogue of ``state_month_price_grid``'s count.
                reporters: list[set[int]] = [set() for _ in range(12)]
                for _, row in grp.iterrows():
                    m = int(row["month"]) - 1
                    if 0 <= m < 12:
                        wsum[m] += float(row["weighted"])
                        qsum[m] += float(row["quantity"])
                        reporters[m].add(int(row["plant_id"]))
                with np.errstate(invalid="ignore", divide="ignore"):
                    zone_price[int(zone)] = np.where(qsum > 0.0, wsum / qsum, np.nan)
                zone_count[int(zone)] = np.array(
                    [float(len(r)) for r in reporters], dtype=float
                )
        result = (state_price, state_count, zone_price)
        self._cache[(fuel_group, klass)] = result
        self._zone_count[(fuel_group, klass)] = zone_count
        return result

    def _zone_ok(self, fuel_group: str, klass: str | None, zone_idx: int) -> np.ndarray:
        """Length-12 mask: zone-months clearing the zone-tier reporter floor.

        All-True on the default-off path (``_min_zone == 0``), so the
        historical unguarded zone mean is byte-identical (caiso-243).
        """
        if self._min_zone <= 0:
            return np.ones(12, dtype=bool)
        counts = self._zone_count.get((fuel_group, klass), {}).get(int(zone_idx))
        if counts is None:
            return np.zeros(12, dtype=bool)
        return counts >= self._min_zone

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
        fuel-group state → fuel-group zone. Under the zone donor guard a
        zone-month below the reporter floor is skipped like a thin state-month.
        """
        tiers = []
        if self.class_aware and klass:
            tiers.append((str(klass), self._grids(fuel_group, str(klass))))
        tiers.append((None, self._grids(fuel_group)))
        out = np.full(12, np.nan, dtype=float)
        for tier_klass, (state_price, state_count, zone_price) in tiers:
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
                need = (
                    np.isnan(out)
                    & ~np.isnan(zp)
                    & self._zone_ok(fuel_group, tier_klass, int(zone_idx))
                )
                out[need] = zp[need]
        return out


def _fuel_name(fuel_idx: int) -> str:
    """Return the fuel-type name for a fuel-type index, or ``""``."""
    from market_sim.data.fleet import FUEL_TYPE_NAMES

    idx = int(fuel_idx)
    if 0 <= idx < len(FUEL_TYPE_NAMES):
        return FUEL_TYPE_NAMES[idx]
    return ""
