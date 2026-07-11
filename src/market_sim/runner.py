"""Command-line entry point and multi-year orchestration for simulations.

A *run* advances one :class:`~market_sim.config.scenarios.ScenarioConfig`
for one ISO across every simulation year, evolving the fleet, solving the
hourly economic dispatch and caching each year's result. A *sweep* expands
a :class:`~market_sim.config.scenarios.SweepDefinition` into many configs
and runs them in parallel.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from multiprocessing import cpu_count

import numpy as np

from market_sim.config.constants import (
    END_YEAR,
    HISTORIC_OUTAGE_OVERLAY_BY_ISO,
    START_YEAR,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import (
    ScenarioConfig,
    SweepDefinition,
    resolve_demand_growth_rate,
    resolve_policy_bundle,
)
from market_sim.data.datacenter import add_datacenter_block
from market_sim.data.eia_loader import load_demand
from market_sim.data.fleet import (
    Generator,
    apply_coal_tranches,
    apply_ercot_ct_offer_surface,
    apply_neiso_coldsnap_derate,
    apply_netload_drag_floors,
    assemble_mc,
    build_base_fleet,
    build_dispatch_fleet,
    generators_to_fleet_arrays,
    load_or_synthesize_bins,
    load_planned_additions,
    load_retired_within_window,
)
from market_sim.data.confirmed_retirements import (
    ConfirmedExit,
    load_announced_reversal_plants,
    load_confirmed_exits,
)
from market_sim.data.fuel import (
    apply_coal_supply_pricing,
    resolve_annual_gas_price,
    resolve_fuel_prices,
)
from market_sim.data.curtailment_share import forecast_wtx_curtail_multipliers
from market_sim.data.renewables import (
    inject_offshore_wind_availability,
    load_renewable_profiles,
)
from market_sim.model.capacity import (
    _FIRM_CLEAN_FUELS,
    CumulativeDeployment,
    accredited_firm_capacity_mw,
    deliverability_headroom_by_zone,
    evolve_fleet,
)
from market_sim.model.ancillary import (
    realized_storage_as_revenue_per_mw_yr,
    realized_thermal_as_revenue_per_mw_yr_by_fuel,
)
from market_sim.model.storage import (
    _elcc_for_duration,
    apply_storage_new_entry,
    build_default_storage,
    load_eia860_pumped_storage,
    storage_cap_profiles,
    storage_units_to_arrays,
)
from market_sim.config.interchange_config import (
    apply_interchange_topology,
    build_interchange_fleet,
    get_interchange_spec,
)
from market_sim.model.transmission import (
    apply_interchange_injections,
    build_incidence_matrix,
    build_interface_groups,
    forward_corridor_interface_groups,
    get_link_bidirectional_array,
    get_link_flow_cost_array,
    get_ttc_array,
    wecc_border_carbon_adder,
)
from market_sim.policy.cap_and_trade import per_generator_membership
from market_sim.policy.carbon import resolve_carbon_price
from market_sim.policy.constraints import get_active_policy_constraints
from market_sim.policy.ira import compute_dispatch_credits
from market_sim.policy.eac import apply_eac_to_mc, compute_eac_dispatch_credits
from market_sim.policy.rps import get_rps_acp, get_rps_target
from market_sim.results.cache import (
    get_cache_path,
    is_cached,
    load_result,
    save_result,
)
from market_sim.results.emissions import compute_must_run_emissions, measured_class_cf
from market_sim.results.evolution_ledger import (
    fleet_totals_by_fuel,
    ledger_path,
    new_events,
    write_ledger,
)
from market_sim.config.reserve_config import ERCOT_AS_PRODUCTS
from market_sim.pipeline import (
    DispatchSpec,
    PriorYearResults,
    apply_reserve_coopt,
    build_base_dispatch_kwargs,
    build_caiso_ra_p1_prep,
    build_pjm_reserve_p1_prep,
    run_commitment_pass,
    run_energy_solve,
)
from market_sim.results.outputs import FleetContext
from market_sim.results.scarcity import (
    caiso_scarcity_overlay,
    effective_reliability_deployment_mw,
    reserve_headroom,
    scarcity_prices,
)

logger = logging.getLogger(__name__)

# Capacity-hindcast bridge years (plan §1.1): quarantined years (rule 22) that a
# hindcast window spans but must never solve, read data for, or score. The fleet
# is still evolved across them from the last solved year's drivers so capacity
# outcomes on the far side are reachable, but no dispatch is produced.
HINDCAST_BRIDGE_YEARS = frozenset({2022, 2026})


def _chp_measured_co2_inputs(
    config: ScenarioConfig, iso: str, year: int
) -> tuple[dict[int, float], dict[str, float], dict[int, float]]:
    """Return ``(measured_rate_by_plant, class_cf_by_group, btm_share_by_plant)``.

    Resolves the EM-7 (plan §5 R5) consistency inputs so the behind-the-meter
    must-run reconstruction books CO2 at the **same measured rate its grid
    tranches use**, sizes the forecast fallback with a measured CHP class
    capacity factor instead of the flat 0.85, and sizes the forecast host
    pull-out from a measured per-plant BTM share instead of the sector-keyed
    default. The rate source mirrors the grid's
    (``fleet.apply_plant_emission_rates*``): the mode-aware v2 artifact when
    ``use_plant_emission_rates_v2`` is on, else the legacy pooled artifact when
    ``use_plant_emission_rates`` is on, else empty (caller keeps the fuel-class
    default) — so BTM and grid CO2 intensity always agree. The class CF is drawn
    from the v2 steam-load history independently of the rate source (empty until
    the v2 artifact carries ``steam_load_klbh_sum``), so the caller falls back to
    the flat ``must_run_cf`` when it is unavailable.

    ``btm_share_by_plant`` is the measured ``chp-btm-share`` artifact
    (:func:`market_sim.data.chp.measured_btm_share_by_plant`), resolved only
    for **forecast** years — a backcast year keeps its existing
    ``run_calibration_full.py::_btm_frame`` sizing (sector-keyed
    :func:`market_sim.data.chp.chp_btm_pct`), unchanged by this function.
    Empty when the mode is backcast, no clean partition exists for the ISO, or
    the artifact covers no plant, so the caller falls back to the bin's own
    ``pct_mr`` share for every plant.
    """
    from pathlib import Path

    import pandas as pd

    from market_sim.data.chp import measured_btm_share_by_plant
    from market_sim.data.emission_rates import fuel_class, measured_plant_rates

    by_plant: dict[int, float] = {}
    class_cf: dict[str, float] = {}
    btm_share: dict[int, float] = {}

    if str(getattr(config, "mode", "forecast")) == "forecast":
        btm_share = measured_btm_share_by_plant(iso)

    if getattr(config, "use_plant_emission_rates_v2", False):
        path = Path(config.plant_emission_rates_v2_path)
        if path.exists():
            v2 = pd.read_parquet(path)
            v2 = v2[v2["iso"].astype(str) == str(iso)]
            if not v2.empty:
                # Same mode-aware (plant, fuel-class) rate the grid tranches book.
                rate_map = measured_plant_rates(v2, iso, int(year), str(config.mode))
                by_plant = {int(pid): rate for (pid, _fc), rate in rate_map.items()}
                # A plant whose CEMS units span classes: the must-run tranche is
                # gas, so prefer the gas-class rate when present.
                for (pid, fc), rate in rate_map.items():
                    if fc == fuel_class("gas"):
                        by_plant[int(pid)] = rate
                class_cf = measured_class_cf(v2)
    elif getattr(config, "use_plant_emission_rates", False):
        from market_sim.data.fleet import _plant_emission_rate_map

        path = Path(config.plant_emission_rates_path)
        if path.exists():
            # Legacy pooled artifact books the same (co2, nox, so2) tonnes/MWh the
            # grid tranches use; mixed plants are excluded from it (Parish), so
            # they fall through to the fuel-class default on both sides.
            by_plant = {
                int(pid): co2
                for pid, (co2, _nox, _so2) in _plant_emission_rate_map(
                    str(path)
                ).items()
            }
        # Class CF still comes from v2 history when the artifact carries it.
        v2_path = Path(config.plant_emission_rates_v2_path)
        if v2_path.exists():
            v2 = pd.read_parquet(v2_path)
            v2 = v2[v2["iso"].astype(str) == str(iso)]
            if not v2.empty:
                class_cf = measured_class_cf(v2)

    return by_plant, class_cf, btm_share


def _get_growth_rate(config: ScenarioConfig, year: int) -> float:
    """Return the demand growth rate for a given year.

    Delegates to :func:`market_sim.config.scenarios.resolve_demand_growth_rate`,
    which also honors the PB-1 ``demand_growth_percentile`` sampler lever;
    at its neutral 0.5 default this is identical to the plain
    ``demand_growth_path`` lookup this function used to do directly.
    """
    return resolve_demand_growth_rate(config, year)


def _scale_demand(
    base_demand: np.ndarray, config: ScenarioConfig, year: int
) -> np.ndarray:
    """Scale weather-year demand to the target year using compound growth.

    ``base_demand`` is the *weather year's* actual hourly load, so growth
    compounds from ``config.weather_year`` -- not from the first simulated
    year. Compounding from START_YEAR silently dropped the growth between
    the weather year and the simulation start (e.g. 2024 actuals presented
    as 2026 demand), an error that then propagated through every forecast
    year. A backcast (``year == weather_year``) still gets a factor of 1.
    """
    factor = 1.0
    for y in range(config.weather_year, year):
        factor *= 1.0 + _get_growth_rate(config, y)
    return base_demand * factor


def _storage_additions_since(
    storage_units, prior_ids: set[str], zone_names: list[str]
) -> list[dict]:
    """Return the evolution-ledger records for storage units built this year.

    Args:
        storage_units: The storage fleet after this year's new-entry screen.
        prior_ids: ``unit_id`` set present before the screen ran.
        zone_names: Unused; retained for signature symmetry with the arrays
            builder (a unit already carries its zone name).

    Returns:
        One ``{"unit_id","tech","mw","zone","duration_h"}`` dict per new unit.
    """
    out: list[dict] = []
    for u in storage_units:
        if u.unit_id in prior_ids:
            continue
        duration = (
            float(u.energy_cap_mwh / u.power_cap_mw) if u.power_cap_mw > 0 else 0.0
        )
        out.append(
            {
                "unit_id": u.unit_id,
                "tech": getattr(u, "tech_name", "storage"),
                "mw": float(u.power_cap_mw),
                "zone": getattr(u, "zone", ""),
                "duration_h": round(duration, 3),
            }
        )
    return out


def _blend_price_signal(
    econ_prices: np.ndarray,
    prev_signal: np.ndarray | None,
    alpha: float,
) -> np.ndarray:
    """Return the EWMA-blended capacity-screen price signal (plan §2.2).

    ``signal_Y = alpha * econ_prices_{Y-1} + (1 - alpha) * signal_{Y-1}``.
    At ``alpha == 1.0`` (the default) or with no prior signal the input array
    is returned unchanged (the SAME object — byte-identical behaviour).
    Anti-whipsaw smoothing only; consumed exclusively by the capacity
    screens, never by dispatch or results.
    """
    if alpha >= 1.0 or prev_signal is None:
        return econ_prices
    return alpha * econ_prices + (1.0 - alpha) * prev_signal


def _lookahead_reprice_signal(
    config: ScenarioConfig,
    next_year: int,
    base_demand: np.ndarray,
    fleet_arrays,
    mc_cost: np.ndarray,
    result,
    n_zones: int,
    demand_next_total: np.ndarray | None = None,
) -> np.ndarray:
    """Stack re-price of the entering year's known net load (plan §2.3.2).

    The pro-forma a developer runs against the known fleet, with zero fitted
    parameters: price each hour of next year's net-load duration
    (``demand_{Y+1} - `` this year's VRE output) by ``np.searchsorted`` into
    the current fleet's marginal-cost supply stack (time-mean full variable
    cost, availability-derated capacity), and apply the same ORDC scarcity
    curve the runner's capacity-economics overlay uses where the stack
    thins/exhausts. O(T log G) numpy, no hour loop (rule 2). Feeds ONLY the
    capacity screens via ``prior_results.price_signal`` — never dispatch,
    results, or the backcast (backcast mode has no capacity evolution).

    ``demand_next_total`` overrides the entering-year total demand ``(T,)``.
    A **capacity hindcast** (plan §1.3) dispatches the *realized* per-year
    demand with no growth scaling (``run_scenario_iso`` line ~872), so the
    "known" entering-year net load must be that same realized next-year load —
    not ``_scale_demand``'s growth-scaled weather year, which is the forecast
    path. The caller passes the realized ``load_demand(iso, next_year, ...)``
    total here; ``None`` (the plain-forecast path) falls back to
    ``_scale_demand`` unchanged.

    Returns:
        ``(n_zones, T)`` system-wide hourly price signal (every zone sees the
        same stack price, matching the screens' system-level use).
    """
    if demand_next_total is not None:
        demand_next = np.asarray(demand_next_total, dtype=float)  # (T,)
    else:
        demand_next = _scale_demand(base_demand, config, next_year).sum(axis=0)  # (T,)
    vre = (result.wind_dispatched + result.solar_dispatched).sum(axis=0)  # (T,)
    net_load = demand_next - vre
    # Static merit stack: per-generator time-mean full variable cost against
    # availability-derated capacity (outages/derates included).
    mc_gen = np.asarray(mc_cost, dtype=float).mean(axis=1)  # (n_gen,)
    cap_gen = np.asarray(fleet_arrays.pmax, dtype=float) * np.asarray(
        fleet_arrays.availability, dtype=float
    ).mean(axis=1)  # (n_gen,)
    order = np.argsort(mc_gen, kind="stable")
    mc_sorted = mc_gen[order]
    cum_cap = np.cumsum(cap_gen[order])
    idx = np.searchsorted(cum_cap, np.clip(net_load, 0.0, None), side="left")
    prices_h = mc_sorted[np.minimum(idx, mc_sorted.size - 1)]
    # ORDC scarcity tail where the stack exhausts (same curve, same gate as
    # the post-solve capacity-economics adder; reserve-rich hours get ~0).
    if config.scarcity_pricing_enabled and config.scarcity_price_overlay:
        reserves = cum_cap[-1] - net_load
        adder = scarcity_prices(config, next_year, reserves, prices_h)["scarcity_adder"]
        prices_h = prices_h + adder
    return np.tile(prices_h[None, :], (n_zones, 1))


def _confirmed_exits_active(config: ScenarioConfig) -> bool:
    """Return True when the confirmed-exit channel should load/apply this run.

    Forecast-mode only, regardless of ``confirmed_exits_enabled``'s default —
    a backcast run is a hard no-op even after the 2026-07-05 default flip
    (`docs/handoffs/confirmed-retirement-plan-2026-07.md` §7), since backcast's
    historical exits ride the vintage snapshot instead.
    """
    return config.mode == "forecast" and config.confirmed_exits_enabled


def run_scenario_iso(config: ScenarioConfig, iso: str) -> str:
    """Run every simulation year for one scenario and one ISO, sequentially.

    For each year from :data:`START_YEAR` to :data:`END_YEAR` the fleet is
    evolved from the prior year (or built fresh in the first year), the
    hourly economic dispatch is solved, and the result is cached. A year
    whose result is already cached is loaded and skipped, so re-running a
    scenario does no redundant solving.

    Args:
        config: The scenario configuration to run.
        iso: ISO identifier, e.g. ``"ERCOT"`` or ``"CAISO"``. When it
            differs from ``config.iso`` the config's ISO is overridden so
            every downstream lookup stays consistent.

    Returns:
        The scenario's deterministic ``cache_key``.
    """
    iso = iso.upper()
    if config.iso != iso:
        config = config.with_overrides(iso=iso)

    # Simulation horizon: config.start_year/end_year override the module
    # defaults (2026/2050) when set — a capacity hindcast runs 2021→2025. The
    # defaults keep every existing forecast and cache key unchanged.
    start_year = config.start_year if config.start_year is not None else START_YEAR
    end_year = config.end_year if config.end_year is not None else END_YEAR

    # Resolve the PB-1 policy_bundle lever to its underlying fields (rule 24:
    # config-build time, no hidden state) before cache_key/run_config capture
    # the config -- a no-op for the neutral "current" default.
    config = resolve_policy_bundle(config)

    iso_config = get_iso_config(iso)
    # Apply ISO-level scenario defaults (e.g. CAISO negative_renewable_offers)
    # for fields the caller has not explicitly set.
    if iso_config.default_scenario_overrides:
        defaults = ScenarioConfig()
        overrides_to_apply = {
            k: v
            for k, v in iso_config.default_scenario_overrides.items()
            if getattr(config, k) == getattr(defaults, k)
        }
        if overrides_to_apply:
            config = config.with_overrides(**overrides_to_apply)

    cache_key = config.cache_key()

    logger.info(
        "run_scenario_iso start: iso=%s cache_key=%s config=%s",
        iso,
        cache_key,
        asdict(config),
    )
    if config.commitment_enabled:
        logger.warning(
            "P2 commitment is a legacy feature; prefer energy_reserve_coopt "
            "for unit commitment pricing."
        )
    # Interconnected ISOs with a configured import node (CAISO's WECC node,
    # PJM's external node) model their neighbors as priced import tranches
    # plus export sinks: pseudo-generators that ride along with the dispatch
    # fleet but never evolve. PJM's external zone is appended to the topology
    # here; CAISO's is baked in. CAISO import tranches carry the CA
    border_carbon = (
        wecc_border_carbon_adder(resolve_carbon_price(config, start_year))
        if iso == "CAISO"
        else 0.0
    )
    interchange_spec = get_interchange_spec(config, iso)
    import_generators = build_interchange_fleet(interchange_spec, border_carbon)
    # Shared interchange topology (orchestrator-unification Stage 5): external
    # node extension, the capacity-deliverability Part-A seam import cap, and
    # the CAISO per-hub corridor split — one sequence, both orchestrators.
    iso_config = apply_interchange_topology(
        iso_config,
        interchange_spec,
        config,
        year=start_year,
        extend_node=bool(import_generators),
    )
    zone_names = iso_config.zone_names

    # Weather-year inputs are fixed across the run; load them once. The CF
    # profiles (wind_cf, solar_cf) are resource-driven and stay fixed, but
    # wind_cap and solar_cap are mutable: capacity evolution grows them each
    # year as new renewables are built.
    # When the priced node is active it serves the interchange, so the
    # measured schedule stays out of demand (it would double-count the
    # export); forward years have no measured schedule anyway.
    # Year-matched EIA-860 vintage (backcast scenario knob): point the fleet /
    # storage / renewable / COD-map loaders at data/raw/eia-860/
    # vintage_<year>/ when requested, else the canonical 2025ER snapshot. The
    # weather-year inputs are fixed across the run, so the vintage is set once
    # here, before any load. None (forecast, or no committed vintage dir) resets
    # to the canonical snapshot. See config.paths.set_eia860_vintage.
    from market_sim.config.paths import set_eia860_vintage

    # A capacity hindcast (plan §1.3) is forecast-mode but initialises from a
    # vintage snapshot (the 2020 Final release) so the modelled start-year fleet
    # matches what actually existed — the vintage is honoured under
    # config.hindcast too. A plain forecast resets to the canonical snapshot.
    set_eia860_vintage(
        config.eia860_vintage_year
        if (config.mode == "backcast" or config.hindcast)
        else None
    )
    base_demand = load_demand(
        iso,
        config.weather_year,
        iso_config,
        td_loss_factor=config.td_loss_factor,
        include_interchange=not import_generators,
        strict_demand_profile=config.strict_demand_profile,
    )
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        iso, config.weather_year, iso_config, config
    )
    # Trim profiles to config.hours when running a sub-annual horizon.
    if config.hours < base_demand.shape[1]:
        base_demand = base_demand[:, : config.hours]
        wind_cf = wind_cf[:, : config.hours]
        solar_cf = solar_cf[:, : config.hours]
    incidence = build_incidence_matrix(iso_config.links, zone_names)
    ttc = get_ttc_array(iso_config.links)
    # Aggregate interface limits (CAISO simultaneous WECC import cap): resolved
    # once to flow-column groups; empty for ISOs without an interface_limits
    # entry, so the LP is identical there.
    interface_groups = build_interface_groups(
        iso_config.links, iso_config.interface_limits
    )
    # FORWARD ATC corridor deliverability cap (CAISO per-hub corridors,
    # ``caiso_corridor_atc_forward``, default off): corridor TTC × posted-ATC
    # base fraction × forward solar derate — a capability limit that
    # regenerates from forward drivers, shared with the backcast orchestrator
    # (the measured-p95 variant is a backcast-only overlay there). No-op off
    # the flag or when no corridor resolves.
    if interchange_spec.use_corridors and getattr(
        config, "caiso_corridor_atc_forward", False
    ):
        _corridor_groups = forward_corridor_interface_groups(
            iso_config, iso, config.weather_year, base_demand.shape[1]
        )
        if _corridor_groups:
            interface_groups = interface_groups + _corridor_groups
            logger.info(
                "%s: WECC corridor deliverability cap on %d link(s) — "
                "FORWARD ATC (TTC × ATC-frac × solar derate)",
                iso,
                len(_corridor_groups),
            )

    fleet = None
    loss_tracker: dict[str, int] = {}
    prior_results = None
    # EWMA state for the capacity screens' price signal (plan §2.2): the
    # previous year's blended signal. None until the first solved year.
    price_signal_prev: np.ndarray | None = None

    # Load the CAMPD operational bins once when enabled. The same bin frame
    # builds the dispatch fleet and drives the CHP must-run post-processing.
    # The per-plant binning path is taken by any ISO with a bin artifact
    # (CAMPD_BINNING_ISOS); ISOs without one always fall back
    # to the legacy aggregate_fleet path regardless of ``use_campd_bins``.
    #
    # ERCOT reads its curated per-plant bin sheet
    # (``config.campd_bins_path``); its base fleet is built once from the start
    # year so its bins take the EIA-923 dominant class for that year (a curated
    # bin can't drift), then carry forward through the projection. The other
    # CAMPD ISOs have no curated sheet, so the SAME per-plant bins frame is
    # synthesized from the EIA-860 fleet plus the ISO's CAMPD-derived
    # ``thermal_tranches_<ISO>.csv`` (committed / coal must-run / CC peaking)
    # via ``fleet_to_bins`` -- giving them ERCOT's smoothed rising offer curve
    # and per-plant tranches. An ISO whose synthesis yields no thermal bins
    # (no artifact) falls through to the legacy path. Both branches --
    # and the post-load fallback when the artifact is missing -- live in
    # ``load_or_synthesize_bins``.
    # Within-window plant exits (the backcast mirror of planned additions):
    # whole plants that retired mid-window are absent from the single recent
    # operable snapshot, so they are injected into the base fleet and the COD
    # ramp ages each out by its real retirement month. Backcast-mode only — a
    # forecast must not carry an already-retired unit. Loaded before the bins
    # are synthesized so the retirees are binned with the rest of the fleet.
    retired_within_window: list[Generator] = []
    if config.mode == "backcast":
        retired_within_window = load_retired_within_window(iso, iso_config)

    campd_bins = load_or_synthesize_bins(config, iso, iso_config, retired_within_window)

    # Storage is managed across years like the generation fleet: the base
    # year starts from the deployment-pace fleet, later years grow via the
    # economic new-entry screen.
    storage_units = build_default_storage(iso_config, config)

    # Pumped storage is existing installed capacity (EIA-860 prime mover ``PS``,
    # ~20 GW nationally) with no new build, so the parameterized battery builder
    # never includes it. Prepend the EIA-860 PS fleet to the storage list once,
    # before the new-entry screen -- PS is fixed existing capacity and does not
    # participate in the endogenous battery-growth screen (it persists across
    # years because ``apply_storage_new_entry`` preserves existing units). Per
    # CLAUDE.md rule #12, EIA-860 installed capacity is a physical asset
    # registry, admissible as a forward input in any year.
    ps_units = load_eia860_pumped_storage(iso, start_year, config=config)
    if ps_units:
        storage_units = ps_units + storage_units
        logger.info(
            "%s %d: %d pumped-storage units (%.0f MW) from EIA-860",
            iso,
            start_year,
            len(ps_units),
            sum(u.power_cap_mw for u in ps_units),
        )

    # Known additions (methodology spec §5.4): EIA-860 planned /
    # under-construction thermal units, deterministic through the data
    # horizon. Loaded once; units come online in their EIA-860 effective
    # year via evolve_fleet step 3 (or the first-year fleet below for units
    # already due). Forecast-mode only: a backcast solves a historical year
    # whose fleet snapshot already reflects what was actually built.
    planned_additions: list[Generator] = []
    if config.mode == "forecast":
        planned_additions = load_planned_additions(iso, iso_config)
        if planned_additions:
            logger.info(
                "loaded %d planned EIA-860 additions (%.0f MW, %d-%d)",
                len(planned_additions),
                sum(g.pmax_mw for g in planned_additions),
                min(g.online_year for g in planned_additions),
                max(g.online_year for g in planned_additions),
            )

    # Confirmed (binding-instrument) exits: the exogenous forecast retirement
    # channel, GATED on confirmed_exits_enabled (default on, flipped 2026-07-05)
    # and forecast-mode only (a backcast's historical exits ride the vintage
    # snapshot, and config.mode == "forecast" here is a hard gate independent of
    # the flag's default, so a backcast run is unaffected by the flip). Loaded
    # once; applied at step 0 of evolve_fleet and the first-year base fleet.
    confirmed_exits: list[ConfirmedExit] = []
    if _confirmed_exits_active(config):
        confirmed_exits = load_confirmed_exits(iso)
        if confirmed_exits:
            logger.info(
                "loaded %d confirmed exits (%.0f MW, %d-%d)",
                len(confirmed_exits),
                sum(e.mw or 0.0 for e in confirmed_exits),
                min(e.exit_year for e in confirmed_exits),
                max(e.exit_year for e in confirmed_exits),
            )

    # Retirement-reversal supersession (announced channel): plants whose
    # announced exit was reversed outright by a public counter-instrument
    # (every registry row superseded — e.g. Byron/Dresden's 2021 dates
    # reversed by IL CEJA) keep running; their stale EIA-860 dates are
    # ignored by evolve_fleet step 1. Deliberately NOT gated on
    # confirmed_exits_enabled: honoring a documented reversal is an
    # announced-channel data correction, not an exogenous exit injection.
    announced_reversal_plants: frozenset[int] = frozenset()
    if config.mode == "forecast":
        announced_reversal_plants = load_announced_reversal_plants(iso)

    # Global cumulative deployment drives the Wright's-Law learning curves.
    # It starts from the reference-year installed base and advances one year
    # of worldwide deployment (plus this ISO's local builds) every year.
    cumulative = CumulativeDeployment.initial()

    # Last year whose LP actually solved. In a capacity hindcast the 2022
    # bridge (plan §1.1) is evolved but never solved, so the year after it
    # keeps consuming the last solved year's prior_results and drivers.
    last_solved_year = start_year
    for year in range(start_year, end_year + 1):
        year_start = time.perf_counter()
        renewable_additions: dict[str, dict[str, float]] = {}
        retrofit_log: list[dict] = []
        # Per-year capacity events for the evolution ledger (plan §2.1).
        evo_events = new_events()

        # Capacity hindcast (rule 22): the bridge year is evolved but its LP is
        # never solved, its data never read, and prior_results is left pointing
        # at the last solved year. Its capacity drivers (gas/carbon) come from
        # that last solved year, never from the quarantined bridge year.
        is_bridge = config.hindcast and year in HINDCAST_BRIDGE_YEARS
        driver_year = last_solved_year if is_bridge else year

        # The entering year's demand is deterministically known before the
        # fleet evolves (_scale_demand is pure config arithmetic), so the
        # capacity screens' peak-anchored mechanisms — the retirement
        # reliability floor and the reserve-margin backstop — test the
        # current year's known peak instead of lagging it by a full year
        # (capacity-economics plan 2026-07 §2.3 component 1: an off-by-one
        # deletion, not foresight). The price-driven screens still see only
        # prior-year outcomes (one-pass, rule 10).
        #
        # The data-center flat load block (G-34) is added immediately after
        # _scale_demand and before peak is taken, so every peak-anchored
        # capacity screen (retirement floor, reserve-margin backstop) sees the
        # DC load for free. Forecast-mode-only and default-off
        # (datacenter_load_path == "off") => same array object, byte-identical.
        year_demand = _scale_demand(base_demand, config, year)
        year_demand = add_datacenter_block(year_demand, config, iso, year, zone_names)
        peak_demand = float(year_demand.sum(axis=0).max())

        if fleet is None:
            # First year: build the base fleet. With CAMPD binning the fleet
            # comes from the operational bin assignments (base + peak
            # generators per bin); otherwise the EIA-860 fleet is collapsed
            # into equal-width efficiency-bin representatives. Either way the
            # collapse happens before the LP -- the dominant solve-time win.
            fleet = build_base_fleet(
                campd_bins,
                iso,
                iso_config,
                zone_names,
                config,
                retired_within_window,
                planned_additions,
                year,
                confirmed_exits=confirmed_exits,
            )
            # First year has no evolution: the ledger records the base fleet
            # snapshot only (fleet_by_fuel before == after, no events).
            base_totals = fleet_totals_by_fuel(fleet)
            evo_events["fleet_by_fuel_before"] = base_totals
            evo_events["fleet_by_fuel_after"] = base_totals
        else:
            # The RPS shadow price from the prior year's dispatch raises the
            # expected revenue of clean technologies in the new-entry screen.
            prior_rps_shadow = 0.0
            if prior_results is not None and prior_results.get("rps_shadow_price"):
                prior_rps_shadow = prior_results["rps_shadow_price"]
            # Gas price and carbon price for the year feed the new-entry
            # screen so gas CC is charged its expected variable fuel cost.
            # The annual (seasonality-free) delivered gas price keeps
            # capacity evolution aligned with hourly dispatch fuel costs.
            gas_price_year = resolve_annual_gas_price(config, driver_year)
            carbon_price_year = resolve_carbon_price(config, driver_year)
            (
                fleet,
                loss_tracker,
                renewable_additions,
                retrofit_log,
                floor_retention_log,
            ) = evolve_fleet(
                fleet,
                prior_results,
                year,
                config,
                loss_tracker,
                rps_shadow_price=prior_rps_shadow,
                cumulative=cumulative,
                gas_price_per_mmbtu=gas_price_year,
                carbon_price=carbon_price_year,
                eac_price_ccs=config.eac_price_gas_cc_ccs,
                events=evo_events,
                confirmed_exits=confirmed_exits,
                peak_demand_next=peak_demand,
                announced_reversal_plants=announced_reversal_plants,
            )
            # Persist the reliability floor's attribution log next to the
            # per-year results parquet (rule 20 analogue: floor-retained MW
            # must be measurable per run, not argued). Written every evolved
            # year — an empty list is the affirmative "floor did not bind".
            floor_log_path = (
                get_cache_path(iso, cache_key, year).parent
                / f"year_{year}_floor_retentions.json"
            )
            floor_log_path.parent.mkdir(parents=True, exist_ok=True)
            floor_log_path.write_text(json.dumps(floor_retention_log, indent=1))
            if retrofit_log:
                avg_savings = sum(
                    r["annual_net_savings_per_mw"] for r in retrofit_log
                ) / len(retrofit_log)
                logger.info(
                    "Year %d: %d CCS retrofits, %.0f $/MW-yr avg savings",
                    year,
                    len(retrofit_log),
                    avg_savings,
                )
            # New wind/solar grow the zonal capacity pools that bound the
            # W[z,t] and S[z,t] dispatch variables -- they are not added as
            # flat-availability thermal generators.
            for zone_name, additions in renewable_additions.items():
                z_idx = zone_names.index(zone_name)
                wind_cap[z_idx] += additions.get("wind", 0.0)
                solar_cap[z_idx] += additions.get("solar", 0.0)

        # Storage grows endogenously: year 2026 uses the base fleet, and
        # 2027+ screens arbitrage revenue against cost on prior-year prices.
        prior_storage_ids = {u.unit_id for u in storage_units}
        if prior_results is not None:
            # Locational deliverability headroom for the storage capacity-value
            # gate (no-op unless capacity_deliverability_limits is on). Uses the
            # current thermal fleet plus the zonal renewable pools; existing
            # storage firm is left out so the screen sizes the *marginal* build
            # against the non-storage deliverable capacity.
            storage_headroom: dict[str, float] = {}
            if config.capacity_deliverability_limits:
                wind_by_zone = {z: float(wind_cap[i]) for i, z in enumerate(zone_names)}
                solar_by_zone = {
                    z: float(solar_cap[i]) for i, z in enumerate(zone_names)
                }
                storage_headroom = deliverability_headroom_by_zone(
                    iso,
                    year,
                    fleet,
                    config,
                    wind_pool_by_zone=wind_by_zone,
                    solar_pool_by_zone=solar_by_zone,
                )
            # The storage screen consumes the capacity-screen price signal
            # (EWMA / lookahead, plan §2.2-§2.3) when present; identical to
            # raw prices at the defaults. Bare-dict callers without the key
            # fall back to prices.
            storage_screen_prices = prior_results.get("price_signal")
            if storage_screen_prices is None:
                storage_screen_prices = prior_results["prices"]
            storage_units = apply_storage_new_entry(
                storage_units,
                storage_screen_prices,
                year,
                config,
                iso,
                cumulative=cumulative,
                deliverability_headroom=storage_headroom,
                endogenous_as_revenue_per_mw_yr=prior_results.get(
                    "storage_as_revenue_per_mw_yr"
                ),
            )
        storage = storage_units_to_arrays(storage_units, zone_names)

        if getattr(config, "storage_vintage_ramp", False):
            power_cap_2d, energy_cap_2d = storage_cap_profiles(
                storage_units, storage, config.hours
            )
            if power_cap_2d is not storage.power_cap:
                storage.power_cap = power_cap_2d
                storage.energy_cap = energy_cap_2d
                logger.info(
                    "%s %d: storage vintage ramp applied — %d units with mid-year COD",
                    iso,
                    year,
                    int((power_cap_2d != power_cap_2d[:, :1]).any(axis=1).sum()),
                )

        # Advance global cumulative deployment by one year, folding in this
        # ISO's local builds (GW) so the learning curves see them next year.
        local_builds: dict[str, float] = {}
        for zone_adds in renewable_additions.values():
            for fuel, mw in zone_adds.items():
                local_builds[fuel] = local_builds.get(fuel, 0.0) + mw / 1000.0
        for g in fleet:
            if g.online_year == year and g.fuel_type in (
                "gas_cc",
                "nuclear",
                "gas_cc_ccs",
            ):
                local_builds[g.fuel_type] = (
                    local_builds.get(g.fuel_type, 0.0) + g.pmax_mw / 1000.0
                )
        # Attribute new storage builds to each tech's own learning curve
        # (li-ion durations share the "li_ion" curve; iron-air / flow / CAES
        # each have their own) so non-li-ion durations actually learn.
        for u in storage_units:
            if u.unit_id in prior_storage_ids:
                continue
            ref_key = "li_ion" if "li_ion" in u.tech_name else u.tech_name
            local_builds[ref_key] = (
                local_builds.get(ref_key, 0.0) + u.power_cap_mw / 1000.0
            )
        cumulative.advance_year(local_builds)

        # Capacity-hindcast bridge (rule 22): the fleet has been evolved across
        # the quarantined year, but the LP is never solved, no year-specific
        # data is read, and prior_results / last_solved_year are left pointing
        # at the last solved year. Persist the evolution-only ledger (no
        # dispatch fields) and move on to the next year.
        if is_bridge:
            _ledger = dict(evo_events)
            _ledger.update(
                iso=iso,
                year=year,
                mode=config.mode,
                hindcast=True,
                bridge=True,
                peak_demand_mw=None,
                firm_clean_mw=None,
                reserve_margin=None,
                rps_dual=None,
                storage_additions=_storage_additions_since(
                    storage_units, prior_storage_ids, zone_names
                ),
                solve_counts={"P0": 0, "P1": 0, "P2": 0},
            )
            _lp = ledger_path(get_cache_path(iso, cache_key, year))
            write_ledger(_lp, _ledger)
            logger.info(
                "year %d: capacity-hindcast BRIDGE — evolved, not solved (ledger %s)",
                year,
                _lp.name,
            )
            continue

        # Capacity hindcast (plan §1.3): dispatch the realized year's demand
        # profile with NO growth scaling, so capacity logic is isolated from
        # demand-forecast error. A plain forecast keeps the once-loaded
        # weather-year base grown by _scale_demand below.
        if config.hindcast:
            year_base_demand = load_demand(
                iso,
                year,
                iso_config,
                td_loss_factor=config.td_loss_factor,
                include_interchange=not import_generators,
                strict_demand_profile=config.strict_demand_profile,
            )
            if config.hours < year_base_demand.shape[1]:
                year_base_demand = year_base_demand[:, : config.hours]
        else:
            year_base_demand = base_demand

        # Assemble this year's LP-ready dispatch fleet from the persistent
        # ``fleet``: coal (and optionally gas) take-or-pay tranching --
        # CAMPD per-plant fuel fractions when ``campd_bins`` is active, else
        # the legacy split_coal_tranches/split_gas_tranches -- plus
        # energy-limited hydro and the CAMPD plant-specific emission-rate
        # overrides. dispatch_fleet is transient; the persistent ``fleet``
        # (un-split, no hydro) carries to next year.
        dispatch_fleet, fuel_fracs, hydro_gen_idx, hydro_monthly_energy = (
            build_dispatch_fleet(
                fleet, campd_bins, import_generators, iso, year, zone_names, config
            )
        )
        # Resolve the historic (facility-summed) outage overlay per ISO. The
        # facility overlay is the primary layer only for facility-summed ISOs
        # (ERCOT); ISOs whose unit-level file is the complete CAMPD-derived
        # source (e.g. PJM) disable it so the two layers don't double-count.
        # An explicit config flag still applies for ISOs absent from the
        # registry. The resolved value is threaded into the fleet-array build
        # (the sole consumer) without mutating the run's recorded config, so
        # ERCOT's default (overlay True) passes the original config unchanged.
        outage_overlay = HISTORIC_OUTAGE_OVERLAY_BY_ISO.get(
            iso, config.historic_outage_overlay
        )
        fleet_config = (
            config
            if outage_overlay == config.historic_outage_overlay
            else replace(config, historic_outage_overlay=outage_overlay)
        )
        fleet_arrays = generators_to_fleet_arrays(
            dispatch_fleet,
            zone_names,
            hours=config.hours,
            iso=iso,
            config=fleet_config,
            load_shape=year_base_demand.sum(axis=0),
            year=year,
        )
        # Replace flat offshore-wind availability with a derived hourly
        # profile; must run after fleet-array build and before dispatch.
        inject_offshore_wind_availability(fleet_arrays, wind_cf, config, iso)

        # The capacity screens already consumed the entering year's known peak
        # (computed at the top of the loop, before fleet evolution). Recompute
        # year_demand / peak_demand here on the hindcast-aware basis for the LP
        # and results path: in hindcast mode the measured/pinned load
        # (year_base_demand) governs the solve, not the forecast scalar.
        if config.hindcast:
            # Measured/pinned historical load governs the hindcast LP; the
            # forecast-only DC block is never added on top of measured actuals
            # (and datacenter_load_path is "off" in any hindcast anyway).
            year_demand = year_base_demand
        else:
            # Same DC block as the capacity-screen seam above (G-34), applied on
            # the forecast branch so the LP and results path see the identical
            # demand the screens saw. Default-off => same array, byte-identical.
            year_demand = _scale_demand(base_demand, config, year)
            year_demand = add_datacenter_block(
                year_demand, config, iso, year, zone_names
            )
        peak_demand = float(year_demand.sum(axis=0).max())

        # Net-load-indexed ST_GAS + CT_PEAKER reliability-drag min-gen floors —
        # the single shared gate-and-log wrapper both orchestrators call
        # (fleet.apply_netload_drag_floors, orchestrator-unification Stage 6).
        # Gates internally on gas_st_netload_drag / ct_netload_drag (default
        # off — byte-identical when unset); net-load uses the LP-served
        # convention shared with the backcast path.
        apply_netload_drag_floors(
            fleet_arrays,
            dispatch_fleet,
            year_demand,
            wind_cf,
            wind_cap,
            solar_cf,
            solar_cap,
            config,
            iso,
            year,
        )
        # NEISO winter gas-availability cold-snap derate — the shared
        # gate-and-log wrapper (fleet.apply_neiso_coldsnap_derate,
        # orchestrator-unification Stage 6: previously wired only in the
        # backcast orchestrator, the plan's §2.2 accidental-drift row).
        # Gated on neiso_gas_coldsnap_derate (default off — byte-identical);
        # must run before the reserve-co-opt inputs are assembled so the
        # shared-headroom RHS sees the derated availability.
        apply_neiso_coldsnap_derate(fleet_arrays, config, iso, year)

        fuel_prices = resolve_fuel_prices(config, fleet_arrays, year)
        # Reprice CAMPD coal bins by plant fuel supply (mine-mouth
        # lignite vs PRB by rail); no-op for the legacy fleet.
        apply_coal_supply_pricing(fuel_prices, dispatch_fleet, config, year)
        carbon_price = resolve_carbon_price(config, year)
        # Full variable cost: fuel + VOM + carbon + NOx + SO2 -- computed
        # even on cached years because next year's economic retirement
        # screen nets it against price (inframarginal margin, not gross
        # revenue). Deliberately excludes the EAC discount (attribute
        # revenue is credited separately in the screen -- using both would
        # double-count) and the take-or-pay tranche discount (sunk fuel is
        # avoidable on a retirement horizon, where contracts lapse).
        mc_cost = assemble_mc(
            fleet_arrays,
            fuel_prices,
            carbon_price,
            config.nox_price,
            so2=(fleet_arrays.so2_rate, config.so2_price),
        )

        if is_cached(iso, cache_key, year):
            result = load_result(iso, cache_key, year)
            logger.info(
                "year %d: cached, skipped (%.3fs)",
                year,
                time.perf_counter() - year_start,
            )
        else:
            wind_mc, solar_mc = compute_dispatch_credits(config, year)
            # Base marginal cost: the full variable cost above, then
            # exogenous EACs, then the coal take-or-pay tranche discount.
            # This is the generators' bid basis — no startup-cost markup.
            mc_base = mc_cost.copy()
            # Exogenous EACs shift the cost vector: per-generator EACs
            # lower per-generator MC, wind/solar EACs lower their dispatch
            # adders, and the storage EAC credits discharge. The EAC is real
            # bidding behavior; it does not stack with the RPS shadow price
            # in capacity economics (each MWh sells one attribute, once).
            apply_eac_to_mc(mc_base, fleet_arrays, config)
            # Coal tranche 1 bids at VOM only (its fuel is sunk under the
            # take-or-pay contract); higher tranches pass through more fuel.
            apply_coal_tranches(
                mc_base, dispatch_fleet, fleet_arrays, fuel_fracs, fuel_prices
            )
            # ERCOT G-22 condition-responsive CT/peaker offer surface: raise the
            # CT/peaker econ+peak tranche bid to the MEASURED self-withholding
            # level (60-Day DAM disclosure) in the top-net-load hours where the
            # real fleet's peakers price to the cap band, removing the "phantom
            # sub-$200 spare" that caps the energy dual. Default off, ERCOT-gated;
            # byte-identical below the measured net-load hinge (max(mc, 0) = mc).
            if getattr(config, "ercot_ct_offer_surface", False) and iso == "ERCOT":
                _ct_surface_net_load = (
                    year_demand.sum(axis=0)
                    - (solar_cap[:, None] * solar_cf).sum(axis=0)
                    - (wind_cap[:, None] * wind_cf).sum(axis=0)
                )
                apply_ercot_ct_offer_surface(
                    mc_base, dispatch_fleet, _ct_surface_net_load, config
                )
            # Shared forward-native interchange injections (orchestrator-
            # unification Stage 5): the SAME post-assembly sequence the
            # backcast runs — reference-price seams, firm import/export
            # floors, and the CAISO offer couplings — every one gated by its
            # existing ScenarioConfig field, all default off in forecast
            # configs. The backcast additionally passes its measured-price
            # overlay block; the forecast never does.
            _interchange_net_load = None
            if iso == "CAISO" and getattr(config, "caiso_import_solar_shape", False):
                # LP-served net load (same convention as the drag floors and
                # the backcast orchestrator's solar-shape input).
                _interchange_net_load = (
                    year_demand.sum(axis=0)
                    - (solar_cap[:, None] * solar_cf).sum(axis=0)
                    - (wind_cap[:, None] * wind_cf).sum(axis=0)
                )
            apply_interchange_injections(
                fleet_arrays,
                mc_base,
                config,
                iso,
                year,
                carbon_price=resolve_carbon_price(config, year),
                gas_scenario=config.gas_price_path,
                net_load=_interchange_net_load,
            )
            wind_eac, solar_eac, storage_eac = compute_eac_dispatch_credits(config)
            wind_mc -= wind_eac
            solar_mc -= solar_eac
            if getattr(config, "negative_renewable_offers", False):
                from market_sim.policy.eac import apply_negative_renewable_offer_floor

                wind_mc, solar_mc = apply_negative_renewable_offer_floor(
                    wind_mc, solar_mc, config
                )
            import_node_recon = None
            if (
                interchange_spec.monthly_reconciliation is not None
                and import_generators
            ):
                from market_sim.model.transmission import (
                    build_import_node_reconciliation,
                )

                import_node_recon = build_import_node_reconciliation(
                    fleet_arrays,
                    iso,
                    year,
                    mode="forecast",
                    forward_net_import_twh=getattr(
                        config, "nyiso_forward_net_import_twh", None
                    ),
                    system_demand=year_demand,
                )
                if import_node_recon is not None:
                    node_idx, recon_lo, recon_hi = import_node_recon
                    logger.info(
                        "%s %d: priced import node reconciled to the neighbor's "
                        "forecast net position — %d node rows, annual band "
                        "[%.2f, %.2f] TWh",
                        iso,
                        year,
                        int(node_idx.size),
                        recon_lo.sum() / 1e6,
                        recon_hi.sum() / 1e6,
                    )
            # The RPS is enforced as an LP constraint when enabled; its dual
            # is the RPS shadow price returned in the dispatch result.
            rps_target = None
            # The RPS ACP ceiling ($/MWh) accompanies an active target: it
            # prices the ACP escape column so the RPS row stays feasible when
            # in-region wind+solar cannot reach the target and its dual (REC
            # price) is capped at the ACP (policy/rps.get_rps_acp; rule 13).
            rps_acp_price = None
            if config.rps_enabled:
                rps_target = get_rps_target(iso, year)
                rps_acp_price = get_rps_acp(iso)
            # CAISO solar deliverability derate (Lever D): reduce the solar CF
            # ceiling by the forward solar-penetration signal so the LP sees
            # the local-network congestion the reduced 3-zone topology misses.
            # When caiso_solar_endogenous_spill is on, the CF derate is SKIPPED:
            # the LP gets the full solar potential and curtails endogenously
            # (solar becomes marginal in oversupply, crashing the dual to
            # solar_mc instead of pinning at gas MC).
            year_solar_cf = solar_cf
            _endogenous_spill = getattr(config, "caiso_solar_endogenous_spill", False)
            if (
                iso == "CAISO"
                and getattr(config, "caiso_solar_deliverability", False)
                and not _endogenous_spill
            ):
                from market_sim.model.transmission import (
                    caiso_solar_deliverability_derate,
                )

                _sol_derate = caiso_solar_deliverability_derate(
                    config.weather_year,
                    solar_cf.shape[1],
                    float(getattr(config, "caiso_solar_deliverability_k", 0.15)),
                    float(getattr(config, "caiso_solar_deliverability_floor", 0.50)),
                )
                if _sol_derate is not None:
                    year_solar_cf = solar_cf * _sol_derate[None, :]
                    hod = np.arange(len(_sol_derate)) % 24
                    mid = (hod >= 9) & (hod <= 15)
                    logger.info(
                        "CAISO %d: solar deliverability derate (Lever D) — "
                        "midday mean %.3f (≈ %.1f%% curtailment headroom)",
                        year,
                        float(np.mean(_sol_derate[mid])),
                        100.0 * (1.0 - float(np.mean(_sol_derate[mid]))),
                    )
            elif iso == "CAISO" and _endogenous_spill:
                logger.info(
                    "CAISO %d: endogenous solar spill — full solar potential "
                    "passed to LP (no pre-LP CF derate); solar sets the midday "
                    "dual when curtailed",
                    year,
                )
            # ERCOT West Texas Export corridor VRE curtailment-share driver
            # (WP-B), forecast leg: the same per-(zone, hour) ceiling the
            # backcast orchestrator applies, computed from the FORECAST state
            # (this year's scaled demand minus the evolved fleet's uncurtailed
            # wind/solar potential) so curtailment emerges endogenously and
            # the decile mapping regenerates as West VRE builds out. The
            # matching gross-up of the delivered-basis profile happens in
            # load_renewable_profiles under the same gate — no
            # double-curtailment. UNSET off the flag (byte-identical LP).
            _wtx_mult = forecast_wtx_curtail_multipliers(
                config,
                iso,
                year,
                year_demand,
                wind_cf,
                wind_cap,
                year_solar_cf,
                solar_cap,
                zone_names,
            )
            _wtx_spec_kwargs = (
                {
                    "wind_curtail_share": _wtx_mult[0],
                    "solar_curtail_share": _wtx_mult[1],
                }
                if _wtx_mult is not None
                else {}
            )
            # CAISO per-year SP15-pocket import caps (config.caiso_per_year_import_caps,
            # default off — byte-identical no-op): swap links 4/5's TTC (baked
            # in at the static 2023 tightest-year value) to this solve year's
            # measured LCT import_cap before the LP reads it. Only the TTC
            # array needs recomputing per year; incidence and
            # link_bidirectional are topology-only and unaffected.
            year_ttc = ttc
            if iso == "CAISO" and getattr(config, "caiso_per_year_import_caps", False):
                _caiso_year_iso_config = apply_caiso_local_import_limits(
                    iso_config, iso, year
                )
                if _caiso_year_iso_config is not iso_config:
                    year_ttc = get_ttc_array(_caiso_year_iso_config.links)
            # Base dispatch kwargs + priced import-node band: the shared
            # pipeline assembly (orchestrator-unification Stage 2) — the same
            # key set the inline dict carried, byte-identical values.
            dispatch_spec = DispatchSpec(
                wind_cf=wind_cf,
                wind_cap=wind_cap,
                solar_cf=year_solar_cf,
                solar_cap=solar_cap,
                **_wtx_spec_kwargs,
                # Load-shed penalty = the ISO's own energy bid cap, not the
                # ERCOT-flavored ScenarioConfig default ($5,000). Each ISOConfig
                # carries its real cap (NYISO/CAISO/MISO/PJM $2,000 per FERC
                # Order 831; ERCOT $5,000), so scarcity hours price at the cap
                # the market actually clears against instead of a uniform $5k.
                voll=iso_config.voll,
                incidence=incidence,
                ttc=year_ttc,
                interface_groups=interface_groups or None,
                # One-way links (MISO's RDT directional pair) floor their flow
                # at 0; all-True for every other ISO (byte-identical bounds).
                link_bidirectional=get_link_bidirectional_array(iso_config.links),
                # Priced RDT TCDC tiers (miso_rdt_tcdc): $/MWh on the tiered
                # one-way links; None (all links free) is byte-identical.
                link_flow_cost=get_link_flow_cost_array(iso_config.links),
                storage_power_cap=storage.power_cap,
                storage_energy_cap=storage.energy_cap,
                storage_zone_idx=storage.zone_idx,
                eta_chg=storage.eta_chg,
                eta_dis=storage.eta_dis,
                wind_mc=wind_mc,
                solar_mc=solar_mc,
                storage_discharge_eac=storage_eac,
                storage_discharge_cost=storage.vom,
                rps_target=rps_target,
                rps_acp_price=rps_acp_price,
                # Bound storage foresight to within-day arbitrage when the
                # config asks for it (methodology spec §1.3); previously
                # only the backcast script honored this flag.
                # ``limited_foresight_dispatch`` (G-30 in-year scarcity fix)
                # forces the same within-day bound: a real DAM/RT operator has
                # no annual lookahead, so denying the single-LP its perfect-
                # foresight cross-day peak-shaving lets peak/net-load-ramp hours
                # tighten and the ORDC overlay price scarcity from the LP regime
                # once the fleet has thinned (pairs with staged thinning).
                storage_daily_cycle_hours=(
                    24
                    if (
                        config.storage_daily_cycling
                        or config.limited_foresight_dispatch
                    )
                    else None
                ),
                # Conventional-hydro monthly energy budget: constrains each
                # hydro plant's monthly generation to its (climatology) budget
                # while letting the LP choose when within the month to generate.
                # Both None (the default) when the ISO has no hydro plants.
                hydro_gen_idx=hydro_gen_idx,
                hydro_monthly_energy=hydro_monthly_energy,
                T=config.hours,
            )
            dispatch_kwargs = build_base_dispatch_kwargs(
                dispatch_spec, import_node_recon=import_node_recon
            )
            # Emissions mass-cap rows (policy constraint path, gated). When
            # mass_cap_enabled and a power-sector CO2 budget is configured for
            # the ISO's program/year, bound in-region fossil emissions; each
            # cap's per-generator coefficient is m[g]·emission_rate, where
            # m[g] is per-unit-exact for any generator with a real plant_code
            # (tested against its own plant's state) and the zone-level
            # m_zone[zone_idx] fallback otherwise (per_generator_membership,
            # plan §5). Default off → no specs → identical LP. The row dual is
            # surfaced as DispatchResult.co2_cap_price (a power-sector,
            # no-bank scenario allowance price — plan §2/§8, not the
            # RGGI/CARB market price).
            mass_caps = get_active_policy_constraints(
                config, year, zone_names=zone_names
            )
            if mass_caps:
                cap_coeffs = np.vstack(
                    [
                        per_generator_membership(
                            config.iso, year, spec.membership, fleet_arrays
                        )
                        * fleet_arrays.emission_rate
                        for spec in mass_caps
                    ]
                )
                dispatch_kwargs.update(
                    mass_cap_coeffs=cap_coeffs,
                    mass_cap_rhs=np.array(
                        [spec.cap_tons for spec in mass_caps], dtype=float
                    ),
                    mass_cap_labels=[spec.label for spec in mass_caps],
                )
            # Plant-group hourly ramp envelopes (config.ramp_limits, GATED
            # default off): CAMPD-measured trajectory bounds per plant group
            # per hour transition. Mirrors the run_calibration.py hook so the
            # forecast and backcast paths share the mechanism (forecast
            # parity, design doc §4). No-op (identical LP) when off or when
            # the ISO has no committed envelope artifact.
            if getattr(config, "ramp_limits", False):
                from market_sim.data.fleet import build_ramp_groups

                ramp_groups = build_ramp_groups(fleet_arrays, iso)
                if ramp_groups is not None:
                    r_gen_idx, r_group_col, r_up, r_dn = ramp_groups
                    dispatch_kwargs.update(
                        ramp_gen_idx=r_gen_idx,
                        ramp_group_col=r_group_col,
                        ramp_up_mw=r_up,
                        ramp_dn_mw=r_dn,
                    )
                    logger.info(
                        "%s %d: ramp envelopes on %d plant groups (%d member tranches)",
                        iso,
                        year,
                        r_up.size,
                        r_gen_idx.size,
                    )
            # Local-capacity (LCR-area) minimum-generation rows
            # (config.local_capacity_constraints, GATED default off): the
            # published-study load-pocket relaxation (design doc §3). Same
            # forecast-parity mirror of the run_calibration.py hook; the RHS
            # scales with this year's zonal load shape, so the mechanism
            # regenerates forward natively. No-op when off or when the ISO
            # has no covered areas / membership crosswalk.
            if getattr(config, "local_capacity_constraints", False):
                from market_sim.data.local_capacity import (
                    build_local_capacity_specs,
                )

                lcr_specs, _lcr_meta = build_local_capacity_specs(
                    iso,
                    year,
                    fleet_arrays.plant_code,
                    fleet_arrays.pmax,
                    fleet_arrays.availability,
                    zone_names,
                    year_demand,
                    storage.zone_idx,
                    storage.power_cap,
                )
                if lcr_specs:
                    dispatch_kwargs.update(local_capacity_specs=lcr_specs)
            # Hydro hourly deliverability envelope
            # (config.hydro_dispatch_envelope, GATED default off): fleet-wide
            # hourly ceiling at the measured per-(month x hod) percentile of
            # EIA-930 NG:WAT — bounds the budget LP's perfect-foresight
            # hoarding (caiso-72 STEP-2). Mirrored in run_calibration.py
            # (backcast parity). No-op when off, no hydro fleet, or no
            # measured/climatology series.
            if (
                getattr(config, "hydro_dispatch_envelope", False)
                and hydro_gen_idx is not None
                and len(hydro_gen_idx)
            ):
                from market_sim.data.eia_loader import (
                    measured_hydro_hourly_envelope,
                )

                env = measured_hydro_hourly_envelope(iso, year, config.hours)
                if env is not None:
                    # Feasibility guard: never cap below the fleet's own
                    # hourly lower bounds (min_gen floors / pmin).
                    h_idx = np.asarray(hydro_gen_idx, dtype=int)
                    if getattr(fleet_arrays, "min_gen", None) is not None:
                        lo = fleet_arrays.min_gen[h_idx, : config.hours].sum(axis=0)
                    else:
                        lo = np.full(config.hours, fleet_arrays.pmin[h_idx].sum())
                    env = np.maximum(env, lo)
                    # CISO's NG:WAT includes pumped-storage net output (no
                    # separate PS series), so the capped model quantity
                    # includes PS net discharge — like-for-like with the
                    # measured envelope.
                    ps_idx = np.flatnonzero(
                        np.char.startswith(
                            np.asarray(storage.tech_names, dtype=str),
                            "pumped",
                        )
                    )
                    dispatch_kwargs.update(
                        hydro_envelope_gen_idx=h_idx,
                        hydro_envelope_mw=env,
                        hydro_envelope_storage_idx=(ps_idx if ps_idx.size else None),
                    )
                    logger.info(
                        "%s %d: hydro deliverability envelope on %d units "
                        "(evening p95 %.0f MW)",
                        iso,
                        year,
                        h_idx.size,
                        float(np.quantile(env, 0.95)),
                    )
            # Energy + operating-reserve co-optimization (multi-ISO, gated):
            # the ISO's reserve demand curve enters the LP as reserve balance
            # rows so the reserve clearing price lifts the energy LMP
            # endogenously. Config-driven (reserve_config.py); the gate, driver
            # threading, merge, and logging live in the shared pipeline wrapper
            # (orchestrator-unification Stage 2).
            apply_reserve_coopt(
                dispatch_kwargs,
                config,
                fleet_arrays,
                config.hours,
                zone_names,
                system_load=year_demand.sum(axis=0),
                wind_gen=(wind_cap[:, None] * wind_cf).sum(axis=0),
                solar_gen=(solar_cap[:, None] * year_solar_cf).sum(axis=0),
                sim_year=year,
            )
            # P0 → monthly startup markup → P1 via the shared pipeline solve
            # core (orchestrator-unification Stage 3) — intra-year warm start
            # included, statement-for-statement the former inline sequence.
            # Cross-year warm-start stays OFF on the forecast path
            # (xyear_cache=None): its marginal-tie reshuffle is read by
            # capacity.evolve_fleet's per-unit retirement screen and can tip a
            # retire/keep decision, changing the next year's fleet (plan §8,
            # docs/cross-year-warmstart.md). Wiring it forecast-side is
            # blocked on a basis-independent capacity screen (warm-start
            # backlog #4) — do not thread a cache here before that lands.
            # P1-native CAISO RA must-offer bridge (P2 archived — CLAUDE.md:
            # P0/P1 only): floor the merchant gas CC/CT fleet from the P0 run
            # pattern before P1, so the scored P1 carries the RA structure. None
            # for every non-CAISO / non-RA run (byte-identical).
            ra_p1_prep = build_caiso_ra_p1_prep(
                config, iso, dispatch_fleet, fleet_arrays, mc_base
            )
            # P1-native PJM commitment-scoped reserve supply (path B, G-20b):
            # fa_p2-style availability mask from the P0 run pattern + the
            # deliverable supply cap recomputed on the masked fleet. (None,
            # None) for every non-PJM / gate-off run (byte-identical);
            # ISO-exclusive with the CAISO hook. Forward-regenerating by
            # construction — the commitment state is the model's own P0 solve.
            pjm_fleet_prep, pjm_kwargs_prep = build_pjm_reserve_p1_prep(
                config, iso, fleet_arrays
            )
            energy_solve = run_energy_solve(
                dispatch_fleet,
                fleet_arrays,
                year_demand,
                mc_base,
                dispatch_kwargs,
                config,
                xyear_cache=None,
                p1_fleet_prep=ra_p1_prep or pjm_fleet_prep,
                p1_kwargs_prep=pjm_kwargs_prep,
            )
            p1_result = energy_solve.p1
            mc_bid = energy_solve.mc_bid
            # The fleet P1 solved on — RA-floored when the bridge fired, else the
            # input fleet. Downstream save/floor-persistence sees the floors.
            fleet_arrays = energy_solve.p1_fleet_arrays
            context = FleetContext.from_arrays(
                fleet_arrays,
                iso_config,
                wind_cf,
                wind_cap,
                year_solar_cf,
                solar_cap,
                storage.energy_cap,
            )
            result = p1_result

            # === LEGACY: P2 Commitment Screen (ARCHIVED — last resort) ===
            # P2 (opt-in, CLAUDE.md "Dispatch & Commitment"): screen CC/CT
            # commitment on P1 clearing prices against base MC, pin coal to its P1
            # dispatch, and re-solve. P0/P1 are the only production passes and
            # every run is scored on P1; this branch runs only when a legacy
            # diagnostic gate is explicitly set (CLI --enable-legacy-p2). The
            # CAISO RA must-offer bridge NO LONGER triggers P2 — it is applied
            # P1-native above (build_caiso_ra_p1_prep). AS-aware commitment
            # (ERCOT, gated): value a unit's AS revenue when screening commitment
            # so the units a tight month keeps online FOR AS stay committed and
            # the P2 co-opt headroom reflects realistic online capacity (the
            # phantom-headroom fix, Finding 1 / G1); ERCOT + multi-product co-opt
            # only.
            as_aware = (
                getattr(config, "ercot_as_aware_commitment", False)
                and iso == "ERCOT"
                and getattr(config, "energy_reserve_coopt", False)
            )
            if config.commitment_enabled or as_aware:
                save_result(
                    p1_result,
                    config,
                    iso,
                    year,
                    context=context,
                    pass_label="p1",
                )
                # Shared P2 core (pipeline.commitment, orchestrator-unification
                # Stage 4): CAISO RA must-offer bridge / NYISO path B / ERCOT
                # AS-aware screen + AS-adequacy floor + WS1 headroom overrides /
                # economic commitment screen + coal pin — the same body the
                # backcast orchestrator runs, statement-for-statement.
                result = run_commitment_pass(
                    {
                        "year": year,
                        "iso": iso,
                        "fleet": dispatch_fleet,
                        "fleet_arrays": fleet_arrays,
                        "mc_base": mc_base,
                        "mc_bid": mc_bid,
                        "p1_result": p1_result,
                        "demand": year_demand,
                        "dispatch_kwargs": dispatch_kwargs,
                        "config": config,
                        "zone_names": zone_names,
                    }
                )
            # === END LEGACY: P2 Commitment Screen ===
            save_result(result, config, iso, year, context=context, demand=year_demand)
            logger.info(
                "year %d: solved and cached (%.3fs)",
                year,
                time.perf_counter() - year_start,
            )

        # CHP must-run post-processing: non-coal must-run capacity is
        # removed from the LP (the CHP units serve host industrial steam,
        # not the grid), so add its generation and emissions back here
        # for asset-level emissions trajectories.
        if campd_bins is not None:
            # EM-7 (plan §5 R5): book BTM CO2 at the plant's measured v2 rate
            # (matching its grid tranches) and size the fallback with a measured
            # CHP class CF instead of the flat must_run_cf.
            mr_rates, mr_class_cf, mr_btm_share = _chp_measured_co2_inputs(
                config, iso, year
            )
            mr = compute_must_run_emissions(
                campd_bins,
                year,
                config.must_run_cf,
                btm_share_by_plant=mr_btm_share,
                measured_rate_by_plant=mr_rates,
                class_cf_by_group=mr_class_cf,
            )
            if not mr.empty:
                logger.info(
                    "year %d: CHP must-run post-processing -- %d bins, "
                    "%.0f GWh, %.0f kt CO2 (asset-level, outside the LP)",
                    year,
                    len(mr),
                    mr["mr_gen_mwh"].sum() / 1000.0,
                    mr["mr_co2_tons"].sum() / 1000.0,
                )

        # ORDC scarcity overlay (post-solve; ERCOT's energy-only design,
        # generalized to any ISO via scarcity_price_overlay): the published
        # reserve-scarcity adder is computed from this year's solved
        # headroom and added to the prices next year's capacity economics
        # see — economic retirement, new entry and CCS retrofit screens
        # (capacity.evolve_fleet) — so peakers and storage earn scarcity
        # revenue instead of bare LP duals. Raw duals structurally carry no
        # scarcity rent in a perfect-foresight LP with zero unserved energy,
        # which over-retires dispatchables and under-builds. Dispatch,
        # volumes, emissions and persisted results are untouched.
        # scarcity_price_overlay defaults True for ERCOT (energy-only; see
        # ISOConfig.default_scenario_overrides) and False elsewhere —
        # capacity-market ISOs recover fixed cost through capacity-market
        # revenue (capacity_revenue_per_mw_yr) instead, no adder there.
        # When co-optimization is on the energy LMP (result.prices) already
        # carries the scarcity lift via the reserve clearing price, so the
        # post-solve adder is skipped to avoid double-counting.
        econ_prices = result.prices
        overlay_adder = None  # captured for the screens' reserve-price signal
        if (
            config.scarcity_pricing_enabled
            and config.scarcity_price_overlay
            and not getattr(config, "energy_reserve_coopt", False)
        ):
            ren_headroom = (
                wind_cf * np.asarray(wind_cap)[:, None]
                + solar_cf * np.asarray(solar_cap)[:, None]
                - result.wind_dispatched
                - result.solar_dispatched
            ).sum(axis=0)
            # Online/offline reserve split (results.scarcity): only responsive
            # capacity backs the ORDC curve — a cold slow-start unit the
            # perfect-foresight LP left idle is NOT real-time reserve. This is
            # the market-design-grounded replacement for the fitted flat RTORDPA
            # offset (the offset stays addable, default 0, as an explicit probe;
            # NOT netting the AS plan — ERCOT's RTOLCAP already counts online
            # AS-held capacity as reserve, so subtracting it double-counts).
            r_online, r_offline = reserve_headroom(
                fleet_arrays,
                result.dispatch,
                storage.power_cap,
                result.storage_charge,
                result.storage_discharge,
                effective_reliability_deployment_mw(year, config),
                renewable_headroom=ren_headroom,
            )
            d_tot = year_demand.sum(axis=0)
            lam = np.where(
                d_tot > 0,
                (result.prices * year_demand).sum(axis=0)
                / np.where(d_tot > 0, d_tot, 1.0),
                result.prices.mean(axis=0),
            )
            adder = scarcity_prices(
                config, year, r_online + r_offline, lam, reserves_online_mw=r_online
            )["scarcity_adder"]
            econ_prices = result.prices + adder[None, :]
            overlay_adder = adder
            logger.info(
                "year %d: ORDC scarcity adder for capacity economics — "
                "mean $%.2f/MWh, >$10 in %d h, max $%.0f",
                year,
                float(adder.mean()),
                int((adder > 10).sum()),
                float(adder.max()),
            )

        # CAISO post-solve scarcity overlay (Tariff §27.4.3.2 / §39.6.1):
        # the probabilistic reserve-scarcity adder is added to SCORED prices
        # (result.prices) because CAISO has no other scarcity mechanism — the
        # reserve co-opt (caiso-59) is inert (12.9 GW headroom >> 2.2 GW
        # requirement), and no measured overlay series exists. The LOLP-based
        # adder uses CAISO's higher net-load uncertainty (σ = 2,500 MW from
        # FRP design, vs ERCOT's 1,400 MW demand-only) so it fires during
        # evening solar decline and import-tight hours where the real market
        # produces penalty-price scarcity the LP cannot. Dispatch, volumes
        # and emissions are untouched. CAISO-only; mutually exclusive with
        # the in-LP co-opt (rule 19).
        if (
            iso == "CAISO"
            and config.scarcity_pricing_enabled
            and getattr(config, "caiso_scarcity_pricing", False)
            and not getattr(config, "energy_reserve_coopt", False)
        ):
            ren_headroom_caiso = (
                wind_cf * np.asarray(wind_cap)[:, None]
                + solar_cf * np.asarray(solar_cap)[:, None]
                - result.wind_dispatched
                - result.solar_dispatched
            ).sum(axis=0)
            d_tot_caiso = year_demand.sum(axis=0)
            lam_caiso = np.where(
                d_tot_caiso > 0,
                (result.prices * year_demand).sum(axis=0)
                / np.where(d_tot_caiso > 0, d_tot_caiso, 1.0),
                result.prices.mean(axis=0),
            )
            caiso_adder = caiso_scarcity_overlay(
                fleet_arrays,
                result.dispatch,
                storage.power_cap,
                result.storage_charge,
                result.storage_discharge,
                renewable_headroom=ren_headroom_caiso,
                system_lambda=lam_caiso,
            )
            result.prices = result.prices + caiso_adder[None, :]
            econ_prices = result.prices
            overlay_adder = caiso_adder
            logger.info(
                "year %d: CAISO scarcity overlay — "
                "mean $%.2f/MWh, >$10 in %d h, >$50 in %d h, max $%.0f",
                year,
                float(caiso_adder.mean()),
                int((caiso_adder > 10).sum()),
                int((caiso_adder > 50).sum()),
                float(caiso_adder.max()),
            )

        # Capacity-screen price signal (plan §2.2-§2.3): optionally re-price
        # the entering year's known net load against this year's supply
        # stack, then EWMA-blend across years. At the defaults (alpha=1.0,
        # lookahead off) this passes econ_prices through unchanged (the same
        # array object — byte-identical). Screens-only: dispatch, results
        # and persisted prices never see it.
        price_signal = econ_prices
        # The entering year the lookahead re-prices for. A capacity hindcast
        # (rule 22) may NEVER read a quarantined bridge year's data, so the
        # look-ahead is suppressed whenever the next year is a bridge year
        # (2022, 2026) or falls outside this run's own window — the last
        # solved hindcast year (2025) has no admissible next year to screen
        # for. A plain forecast is bounded only by the module horizon.
        next_year = year + 1
        if config.hindcast:
            lookahead_next_ok = (
                next_year <= end_year and next_year not in HINDCAST_BRIDGE_YEARS
            )
        else:
            lookahead_next_ok = year < END_YEAR
        if (
            config.entry_lookahead_reprice
            and config.mode == "forecast"
            and lookahead_next_ok
        ):
            # Hindcast: the KNOWN entering-year load is the realized next-year
            # demand the LP will actually dispatch (line ~872), not a growth-
            # scaled weather year. Forecast: None → _scale_demand fallback.
            demand_next_total = None
            if config.hindcast:
                _dn = load_demand(
                    iso,
                    next_year,
                    iso_config,
                    td_loss_factor=config.td_loss_factor,
                    include_interchange=not import_generators,
                    strict_demand_profile=config.strict_demand_profile,
                )
                if config.hours < _dn.shape[1]:
                    _dn = _dn[:, : config.hours]
                demand_next_total = _dn.sum(axis=0)
            price_signal = _lookahead_reprice_signal(
                config,
                next_year,
                base_demand,
                fleet_arrays,
                mc_cost,
                result,
                len(zone_names),
                demand_next_total=demand_next_total,
            )
            _ps_h = price_signal[0]  # system row; every zone identical
            logger.info(
                "year %d: lookahead stack re-price for %d capacity screens — "
                "mean $%.2f/MWh (raw duals+overlay mean $%.2f); "
                "pro-forma scarcity >$200 in %d h, >$1000 in %d h, max $%.0f",
                year,
                next_year,
                float(price_signal.mean()),
                float(econ_prices.mean()),
                int((_ps_h > 200).sum()),
                int((_ps_h > 1000).sum()),
                float(_ps_h.max()),
            )
        price_signal = _blend_price_signal(
            price_signal, price_signal_prev, float(config.entry_price_signal_alpha)
        )
        price_signal_prev = price_signal

        # Reserve-price signal for next year's capacity screens (capacity-
        # economics plan §5 step 2, screen_reserve_value_enabled): the hourly
        # $/MWh a reserve-eligible unit earns holding reserve instead of
        # selling energy, so the retirement/new-entry screens can value each
        # unit's per-hour best use max(energy margin, reserve price). Exactly
        # one mechanism produces it (rule 19):
        #  * co-opt duals — under ercot_thermal_as_endogenous the per-hour
        #    binding reserve price from the solve's own reserve_price_by_family
        #    (all-products tier for synchronized units; the non-fast/Non-Spin
        #    tier for offline-capable quick-starts, mirroring the co-opt's
        #    headroom cascade). Supersedes that flag's annual per-fuel rate.
        #  * else the post-solve ORDC scarcity adder — ERCOT pays real-time
        #    on-line/off-line reserves the same ORDC price the energy adder
        #    carries (RTORPA/RTOFFPA, Nodal Protocols §6.5.7.5), so the
        #    published-curve adder is the reserve price both tiers see.
        # None when the flag is off or neither mechanism ran — the screens
        # then keep the legacy annual AS credits.
        reserve_price_signal = None
        reserve_price_signal_slow = None
        if getattr(config, "screen_reserve_value_enabled", True):
            rp_fam = getattr(result, "reserve_price_by_family", None)
            if (
                rp_fam is not None
                and iso == "ERCOT"
                and getattr(config, "ercot_thermal_as_endogenous", False)
            ):
                rp = np.asarray(rp_fam, dtype=float)
                if rp.ndim == 2 and rp.shape[1] > 0:
                    if getattr(config, "ercot_multiproduct_as_coopt", False):
                        products = list(ERCOT_AS_PRODUCTS)
                        slow_cols = [
                            p
                            for p in range(min(rp.shape[1], len(products)))
                            if products[p][2] != "fast"
                        ]
                    else:
                        # Single-product co-opt: the lumped contingency
                        # reserve is suppliable by quick-starts too.
                        slow_cols = list(range(rp.shape[1]))
                    reserve_price_signal = rp.max(axis=1)
                    reserve_price_signal_slow = (
                        rp[:, slow_cols].max(axis=1)
                        if slow_cols
                        else np.zeros(rp.shape[0], dtype=float)
                    )
            elif overlay_adder is not None:
                reserve_price_signal = overlay_adder
                reserve_price_signal_slow = overlay_adder

        # Typed cross-year state (pipeline.PriorYearResults, AR-2). The .get /
        # __getitem__ shims keep every dict-style reader (this loop's next
        # iteration, capacity.evolve_fleet, apply_storage_new_entry) working
        # unchanged; values are identical to the former dict, key-for-key.
        prior_results = PriorYearResults(
            fleet_arrays=fleet_arrays,
            dispatch_result=result,
            prices=econ_prices,
            price_signal=price_signal,
            peak_demand=peak_demand,
            planned_additions=planned_additions,
            mc_cost=mc_cost,
            rps_shadow_price=result.rps_shadow_price or 0.0,
            retrofit_log=retrofit_log,
            # AS-eligible (storage) fleet power for the AS-revenue saturation
            # in next year's capacity screens (capacity.evolve_fleet).
            storage_power_mw=float(sum(storage.power_cap))
            if storage.power_cap.ndim == 1
            else float(storage.power_cap.sum(axis=0).max()),
            # Storage AS revenue DERIVED from this year's co-opt reserve duals
            # (the endogenous analogue of the exogenous as_revenue rate) — fed
            # to next year's storage entry screen so exactly one mechanism
            # prices storage AS under ercot_storage_as_endogenous (rule 19).
            # 0.0 when the co-opt did not price reserve this year.
            storage_as_revenue_per_mw_yr=realized_storage_as_revenue_per_mw_yr(
                result.reserve_price_by_family,
                result.reserve_dispatch,
                result.storage_charge,
                result.storage_discharge,
                storage.power_cap,
                storage.zone_idx,
                len(zone_names),
            )
            if getattr(config, "ercot_storage_as_endogenous", False)
            else 0.0,
            # Per-fuel thermal AS revenue DERIVED from this year's co-opt reserve
            # duals (the endogenous analogue of the exogenous flat as_revenue rate)
            # — fed to next year's retirement/new-entry screens so exactly one
            # mechanism prices thermal AS under ercot_thermal_as_endogenous
            # (rule 19). Empty dict when the co-opt did not price reserve this year.
            thermal_as_revenue_per_mw_yr=(
                realized_thermal_as_revenue_per_mw_yr_by_fuel(
                    fleet_arrays,
                    result.dispatch,
                    result.reserve_price_by_family,
                    config.hours,
                )
                if (
                    getattr(config, "ercot_thermal_as_endogenous", False)
                    and iso == "ERCOT"
                )
                else None
            ),
            # Reserve-price signal (plan §5 step 2) — the hourly reserve value
            # next year's retirement/new-entry screens max against the energy
            # margin (synchronized tier / offline quick-start tier).
            reserve_price_signal=reserve_price_signal,
            reserve_price_signal_slow=reserve_price_signal_slow,
            # Zonal hourly CF profiles + zone ordering so the VRE new-entry
            # screen values its build zone's capture shape against that
            # zone's prices (plan §6 CX-6c) instead of a flat mean.
            zone_names=list(zone_names),
            wind_cf=wind_cf,
            solar_cf=solar_cf,
            # Renewable-pool and accredited-storage-firm capacity for next
            # year's reserve-margin adequacy backstop.
            wind_cap_mw=float(np.sum(wind_cap)),
            solar_cap_mw=float(np.sum(solar_cap)),
            storage_firm_mw=float(
                sum(
                    u.power_cap_mw
                    * _elcc_for_duration(
                        u.energy_cap_mwh / u.power_cap_mw if u.power_cap_mw > 0 else 0.0
                    )
                    for u in storage_units
                )
            ),
        )

        # Evolution ledger (plan §2.1): persist this solved year's capacity
        # events + summary beside its dispatch parquet. P0+P1 always solve once;
        # P2 (archived) runs only when a legacy diagnostic screen is enabled. The
        # CAISO RA must-offer bridge is P1-native and adds no P2 solve.
        p2_enabled = config.commitment_enabled or (
            getattr(config, "ercot_as_aware_commitment", False)
            and iso == "ERCOT"
            and getattr(config, "energy_reserve_coopt", False)
        )
        firm_mw = accredited_firm_capacity_mw(
            fleet,
            float(np.sum(wind_cap)),
            float(np.sum(solar_cap)),
            prior_results["storage_firm_mw"],
            iso=iso,
        )
        ledger = dict(evo_events)
        ledger.update(
            iso=iso,
            year=year,
            mode=config.mode,
            hindcast=bool(config.hindcast),
            bridge=False,
            peak_demand_mw=round(peak_demand, 3),
            firm_clean_mw=round(
                float(
                    sum(g.pmax_mw for g in fleet if g.fuel_type in _FIRM_CLEAN_FUELS)
                ),
                3,
            ),
            reserve_margin=round(firm_mw / peak_demand - 1.0, 6)
            if peak_demand > 0
            else None,
            rps_dual=round(float(result.rps_shadow_price or 0.0), 6),
            storage_additions=_storage_additions_since(
                storage_units, prior_storage_ids, zone_names
            ),
            solve_counts={"P0": 1, "P1": 1, "P2": 1 if p2_enabled else 0},
        )
        write_ledger(ledger_path(get_cache_path(iso, cache_key, year)), ledger)
        last_solved_year = year

    logger.info("run_scenario_iso done: iso=%s cache_key=%s", iso, cache_key)
    return cache_key


def _run_pair(pair: tuple[ScenarioConfig, str]) -> str:
    """Run one ``(config, iso)`` pair; the worker entry point for sweeps."""
    config, iso = pair
    return run_scenario_iso(config, iso)


def run_sweep(sweep_def: SweepDefinition, workers: int | None = None) -> list[str]:
    """Expand a sweep into configs and run every ``(config, iso)`` pair.

    Args:
        sweep_def: The sweep definition to expand.
        workers: Number of worker processes. Defaults to ``cpu_count - 1``.
            With a single worker the pairs run in-process (no subprocess
            overhead).

    Returns:
        The list of cache keys, one per ``(config, iso)`` pair.
    """
    configs = sweep_def.generate()
    pairs = [(config, config.iso) for config in configs]

    if workers is None:
        workers = max(1, cpu_count() - 1)

    logger.info(
        "run_sweep start: %d (config, iso) pairs across %d worker(s)",
        len(pairs),
        workers,
    )

    if workers == 1:
        return [_run_pair(pair) for pair in pairs]

    with ProcessPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(_run_pair, pairs))


def _build_parser() -> argparse.ArgumentParser:
    """Return the ``market-sim`` argument parser with its subcommands."""
    parser = argparse.ArgumentParser(
        prog="market-sim",
        description="Electricity market dispatch and policy simulator.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a single scenario.")
    run_parser.add_argument(
        "--config", required=True, help="Path to a scenario YAML file."
    )
    run_parser.add_argument(
        "--iso",
        default=None,
        help="ISO to run; defaults to the config's own ISO.",
    )

    sweep_parser = subparsers.add_parser("sweep", help="Run a parameter sweep.")
    sweep_parser.add_argument(
        "--sweep", required=True, help="Path to a sweep YAML file."
    )
    sweep_parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Worker processes; defaults to cpu_count - 1.",
    )

    ensemble_parser = subparsers.add_parser(
        "ensemble",
        help="Run a forecast over multiple weather years and report the distribution.",
    )
    ensemble_parser.add_argument(
        "--config", required=True, help="Path to a forecast scenario YAML file."
    )
    ensemble_parser.add_argument(
        "--iso",
        default=None,
        help="ISO to run; defaults to the config's own ISO.",
    )
    ensemble_parser.add_argument(
        "--weather-years",
        type=int,
        nargs="+",
        default=None,
        help="Weather years to draw over (weather-only path); defaults to "
        "the ISO's verified pool (weather_year_pool). Ignored when --sampler "
        "is given.",
    )
    ensemble_parser.add_argument(
        "--sampler",
        default=None,
        help="Path to an uncertainty-sampler YAML spec (PB-2). When given, the "
        "member axis is the multivariate draw, not the weather year.",
    )
    ensemble_parser.add_argument(
        "--draws",
        type=int,
        default=None,
        help="Number of sampler draws; overrides the spec's n. Requires --sampler.",
    )
    ensemble_parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Sampler RNG seed; overrides the spec's seed. Requires --sampler.",
    )
    ensemble_parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Worker processes; defaults to min(2, cpu_count - 1) (rule 12).",
    )
    ensemble_parser.add_argument(
        "--out-dir",
        default=None,
        help="Directory for the sampler output surface (draws/metrics/bands "
        "parquet + ensemble_meta.json). Requires --sampler.",
    )
    ensemble_parser.add_argument(
        "--out",
        default=None,
        help="Path to write the weather-year ensemble distribution JSON; "
        "skipped if omitted. Weather-only path.",
    )
    ensemble_parser.add_argument(
        "--structural-prior",
        action="store_true",
        help="Fold the D-7 structural-error prior into the emissions band "
        "(PB-3), producing the published dispatch-conditional band alongside "
        "the parametric one. Requires --sampler and --out-dir.",
    )

    matrix_parser = subparsers.add_parser(
        "matrix",
        help=(
            "Run a named-case AEO/IPM-style scenario matrix (deterministic "
            "range, not a probability band)."
        ),
    )
    matrix_parser.add_argument(
        "--config", required=True, help="Path to the base forecast scenario YAML."
    )
    matrix_parser.add_argument(
        "--matrix",
        required=True,
        help="Path to a cases-mode sweep YAML, e.g. configs/scenario_matrix.yaml.",
    )
    matrix_parser.add_argument(
        "--iso",
        default=None,
        help="ISO to run; defaults to the base config's own ISO.",
    )
    matrix_parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Concurrent cases; hard-capped at 2 (CLAUDE.md rule 12/16).",
    )
    matrix_parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory; defaults to results/ensemble/<matrix_id>/.",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``market-sim`` console script.

    Args:
        argv: Argument vector to parse. Defaults to ``sys.argv[1:]``.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = _build_parser().parse_args(argv)

    if args.command == "run":
        config = ScenarioConfig.from_yaml(args.config)
        iso = args.iso or config.iso
        run_scenario_iso(config, iso)
    elif args.command == "sweep":
        run_sweep(SweepDefinition.from_yaml(args.sweep), args.workers)
    elif args.command == "ensemble":
        config = ScenarioConfig.from_yaml(args.config)
        iso = args.iso or config.iso
        if args.sampler:
            from dataclasses import replace

            from market_sim.ensemble import run_sampler_ensemble
            from market_sim.uncertainty import UncertaintySpec

            spec = UncertaintySpec.from_yaml(args.sampler)
            overrides = {}
            if args.draws is not None:
                overrides["n"] = args.draws
            if args.seed is not None:
                overrides["seed"] = args.seed
            if overrides:
                spec = replace(spec, **overrides)
            prior = None
            if args.structural_prior:
                from market_sim.structural_prior import default_prior

                prior = default_prior()
            run_sampler_ensemble(
                config, spec, iso, args.workers, args.out_dir, prior=prior
            )
        else:
            from market_sim.ensemble import export_ensemble_json, run_weather_ensemble

            members = run_weather_ensemble(
                config, iso, args.weather_years, args.workers
            )
            if args.out:
                export_ensemble_json(members, iso, args.out)
    elif args.command == "matrix":
        from market_sim.matrix import run_matrix_cli

        run_matrix_cli(args.config, args.matrix, args.iso, args.workers, args.out_dir)


if __name__ == "__main__":
    main()
