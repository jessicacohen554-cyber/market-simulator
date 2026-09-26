"""Command-line entry point and multi-year orchestration for simulations.

A *run* advances one :class:`~market_sim.config.scenarios.ScenarioConfig`
for one ISO across every simulation year, evolving the fleet, solving the
hourly economic dispatch and caching each year's result. A *sweep* expands
a :class:`~market_sim.config.scenarios.SweepDefinition` into many configs
and runs them in parallel.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import logging
import time
from dataclasses import asdict

import numpy as np

from market_sim.config.capacity_market import ClearedCapacityPrice
from market_sim.config.constants import (
    DEFAULT_MARKET_DESIGN,
    MARKET_DESIGN,
    resolve_locality_gross_cone_ratio,
    END_YEAR,
    ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC,
    HISTORIC_OUTAGE_OVERLAY_BY_ISO,
    START_YEAR,
    resolve_capacity_market_clearing,
)
from market_sim.config.entry_config import (
    ENTRY_GROWTH_LIMIT_MULTIPLE,
    ENTRY_THROUGHPUT_WINDOW_YEARS,
)
from market_sim.config.retirement_config import (
    EXIT_THROUGHPUT_LIMIT_MULTIPLE,
    EXIT_THROUGHPUT_WINDOW_YEARS,
)
from market_sim.config.iso_configs import (
    apply_iso_scenario_defaults,
    get_iso_config,
)
from market_sim.config.scenarios import (
    ScenarioConfig,
    SweepDefinition,
    crossover_unbridges_year,
    resolve_demand_growth_rate,
    resolve_policy_bundle,
)
from market_sim.data.datacenter import add_load_layers
from market_sim.data.eia_loader import load_demand
from market_sim.data.input_completeness import check_clean_partitions
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
    load_procured_vre_additions,
    load_retired_within_window,
)
from market_sim.data.build_exit_throughput import max_annual_exit_gw
from market_sim.data.build_throughput import max_annual_build_gw_by_tech
from market_sim.data.offer_curves import (
    apply_cc_committed_offer_margin,
    apply_gas_offer_margin,
    apply_miso_offer_spread_anchored,
    apply_miso_offer_surface,
)
from market_sim.data.announced_retirements import (
    disposition_table as announced_fossil_disposition_table,
    rows_as_records as announced_fossil_rows_as_records,
)
from market_sim.data.confirmed_retirements import (
    ConfirmedExit,
    load_announced_reversal_plants,
    load_confirmed_exits,
)
from market_sim.data.outages import apply_correlated_outage_derate
from market_sim.data.transmission_expansion import (
    TransmissionExpansion,
    apply_transmission_expansion,
    cumulative_deltas,
    load_transmission_expansions,
)
from market_sim.data.fuel import (
    apply_coal_supply_pricing,
    resolve_annual_gas_price,
    resolve_fuel_prices,
    resolve_gas_scenario_path,
)
from market_sim.data.curtailment_share import forecast_wtx_curtail_multipliers
from market_sim.data.renewables import (
    inject_offshore_wind_availability,
    load_renewable_profiles,
)
from market_sim.model.capacity import (
    _FIRM_CLEAN_FUELS,
    CumulativeDeployment,
    _hydro_firm_mw,
    accredited_firm_capacity_mw,
    capacity_reserve_position,
    deliverability_headroom_by_zone,
    locality_capacity_curves_armed,
    locality_capacity_positions,
    locality_prices_by_zone,
    evolve_fleet,
    modelled_hydro_nameplate_mw,
    pipeline_lookahead_units,
    renewable_credits_applied,
    resolve_adequacy_requirement_mw,
)
from market_sim.model.capacity_evolution.adequacy import curve_convention_position
from market_sim.model.ancillary import (
    realized_storage_as_revenue_per_mw_yr,
    realized_thermal_as_revenue_per_mw_yr_by_fuel,
)
from market_sim.model.storage import (
    apply_storage_new_entry,
    build_default_storage,
    load_eia860_pumped_storage,
    load_eia860_storage,
    measured_storage_base_fleet_active,
    storage_accreditation_credit,
    storage_cap_profiles,
    storage_units_to_arrays,
)
from market_sim.config.interchange_config import (
    apply_interchange_topology,
    build_interchange_fleet,
    get_interchange_spec,
)
from market_sim.model.transmission import (
    apply_caiso_local_import_limits,
    apply_interchange_injections,
    build_incidence_matrix,
    apply_miso_measured_sil_envelope,
    build_interface_groups,
    build_caiso_link_loss,
    build_miso_link_loss,
    build_nyiso_link_loss,
    build_pjm_link_loss,
    forward_corridor_interface_groups,
    get_link_bidirectional_array,
    get_link_flow_cost_array,
    get_ttc_array,
    wecc_border_carbon_adder,
)
from market_sim.policy.cap_and_trade import (
    carbon_mc_column,
    per_generator_membership,
)
from market_sim.policy.carbon import resolve_carbon_price
from market_sim.policy.constraints import get_active_policy_constraints
from market_sim.policy.ira import compute_dispatch_credits
from market_sim.policy.eac import apply_eac_to_mc, compute_eac_dispatch_credits
from market_sim.policy.federal_ces import (
    append_federal_ces_region,
    federal_ces_suppresses_state_rps,
)
from market_sim.policy.clean_tiers import (
    build_clean_region_arrays,
    clean_credit_by_fuel,
)
from market_sim.policy.voluntary_demand import append_voluntary_region
from market_sim.policy.rps import (
    build_rps_region_arrays,
    get_rps_acp,
    get_rps_eligible_fuels,
    get_rps_target,
)
from market_sim.results.cache import (
    cache_config_disagreements,
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
    UNSET,
    DispatchSpec,
    PriorYearResults,
    apply_ercot_commitment_posture,
    apply_reserve_coopt,
    build_base_dispatch_kwargs,
    resolve_hydro_cascade,
    resolve_hydro_period_hours,
    build_caiso_ra_p1_prep,
    build_caiso_reserve_p1_prep,
    build_ercot_gas_bridge_p1_preps,
    build_miso_coal_night_floor_p1_prep,
    build_nyiso_gas_bridge_p1_prep,
    build_soco_gas_st_campaign_p1_prep,
    build_spp_gas_bridge_p1_prep,
    build_pjm_reserve_p1_prep,
    reset_pass_timing_log,
    run_commitment_pass,
    run_energy_solve,
)
from market_sim.pipeline.api import (  # noqa: F401 — re-exported facade surface
    run_pair,
    run_scenario,
)
from market_sim.pipeline.timing import (
    log_year_cached_timing,
    log_year_phase_timing,
)
from market_sim.results.outputs import FleetContext
from market_sim.results.scarcity import (
    caiso_scarcity_overlay,
    effective_reliability_deployment_mw,
    ercot_fleet_forced_outage_sigma_mw,
    ercot_lookahead_as_hold_mw,
    ercot_lookahead_committed_reserves,
    ercot_lookahead_expected_ordc_adder,
    reserve_headroom,
    scarcity_prices,
)

logger = logging.getLogger(__name__)

# Capacity-hindcast bridge years (plan §1.1): quarantined years (rule 22) that a
# hindcast window spans but must never solve, read data for, or score. The fleet
# is still evolved across them from the last solved year's drivers so capacity
# outcomes on the far side are reachable, but no dispatch is produced.
HINDCAST_BRIDGE_YEARS = frozenset({2022, 2026})


def is_hindcast_bridge_year(
    year: int,
    *,
    hindcast: bool,
    crossover_forward_year: int | None,
    start_year: int | None,
) -> bool:
    """THE single definition of "evolved across, never solved" (rule 22).

    A bridge year is a quarantined year (:data:`HINDCAST_BRIDGE_YEARS`) inside
    a hindcast window: the fleet evolves across it, but its LP is never solved
    and its measured data never read. The one exception is a genuine T1-X
    crossover forward year (:func:`~market_sim.config.scenarios.
    crossover_unbridges_year`), which is a forecast-mode solve reading no
    measured actuals.

    Both :func:`run_scenario_iso`'s per-year branch and the harness guard
    (``scripts/run_capacity_hindcast._validate_window``) call THIS function, so
    the guard policy-checks exactly the years the runner will actually solve.
    FFR-3Q's breach was two predicates answering one question: the guard
    computed its solve set from the ``--crossover`` CLI flag while the runner
    branched on ``crossover_forward_year``, and a base-2021 T1-FF window fell
    through the gap and solved 2022. Rule 19 ``[R-ONE-MECH]``.
    """
    return (
        hindcast
        and year in HINDCAST_BRIDGE_YEARS
        and not crossover_unbridges_year(
            year,
            crossover_forward_year=crossover_forward_year,
            start_year=start_year,
        )
    )


def hindcast_solve_years(
    start_year: int,
    end_year: int,
    *,
    hindcast: bool = True,
    crossover_forward_year: int | None = None,
) -> list[int]:
    """Return the years a run over ``[start_year, end_year]`` will SOLVE.

    The window minus its bridge years, decided by
    :func:`is_hindcast_bridge_year` — so this is the realized solve set by
    construction, not a second reading of it. The harness guard checks this
    set against the rule-22 policy, and the completion assertion compares it to
    what the evolution ledgers actually recorded.
    """
    return [
        y
        for y in range(start_year, end_year + 1)
        if not is_hindcast_bridge_year(
            y,
            hindcast=hindcast,
            crossover_forward_year=crossover_forward_year,
            start_year=start_year,
        )
    ]


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
    default) -- so BTM and grid CO2 intensity always agree. The class CF is drawn
    from the v2 steam-load history independently of the rate source (empty until
    the v2 artifact carries ``steam_load_klbh_sum``), so the caller falls back to
    the flat ``must_run_cf`` when it is unavailable.

    ``btm_share_by_plant`` is the measured ``chp-btm-share`` artifact
    (:func:`market_sim.data.chp.measured_btm_share_by_plant`), resolved only
    for **forecast** years -- a backcast year keeps its existing
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
                # Same mode-aware (plant, fuel-class) rate the grid tranches
                # book — including the FH-1 hindcast-lane as-of bound and the
                # T1-FF quarantine trim, so BTM and grid CO2 intensity stay on
                # the identical basis in a hindcast/full-forward run.
                rate_map = measured_plant_rates(
                    v2,
                    iso,
                    int(year),
                    str(config.mode),
                    as_of_year=(
                        int(year) if getattr(config, "hindcast", False) else None
                    ),
                    exclude_quarantined=bool(
                        getattr(config, "is_full_forward_hindcast", False)
                    ),
                )
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

    **Backward spans (FH-2, hindcast-forward plan §4 row 6).** ``year <
    config.weather_year`` -- a target year BEFORE the weather base, reachable
    once the forward boundary drops below 2026 -- used to fall out of
    ``range(weather_year, year)`` as an empty loop and silently apply factor
    **1.0**: no de-growth, no error, a 2025 load level presented as 2021's.
    That silence is the defect class FR-7/FR-8 belong to, so it is gone. Two
    explicit behaviours replace it:

    * **T1-FF (full-forward hindcast) hard-errors.** Both shipped arms pin the
      weather base at/below every solve year (Arm R rebinds per solve year, Arm
      K pins the base year), so a backward span there is a posture
      misconfiguration -- and de-growing a *later* year's measured load into an
      "as-of" forecast would import post-base information (rule 13
      [R-MEASURED]). Raised loudly rather than de-grown.
    * **Everywhere else it de-grows correctly**, the exact inverse of the
      forward compounding over the same span (each year's own rate, so the
      two directions compose to identity), and logs that it fired.

    Raises:
        ValueError: On a backward span in a full-forward hindcast.
    """
    if year >= config.weather_year:
        factor = 1.0
        for y in range(config.weather_year, year):
            factor *= 1.0 + _get_growth_rate(config, y)
        return base_demand * factor

    if config.is_full_forward_hindcast:
        raise ValueError(
            f"_scale_demand: target year {year} precedes the weather base "
            f"{config.weather_year} in a full-forward hindcast. Pin the weather "
            "year at/below every solve year (Arm K: the base year; Arm R: the "
            "solve year via crossover_solve_year_weather) -- de-growing a later "
            "measured weather year into an as-of forecast would import "
            "post-base information (hindcast-forward plan §4 row 6, rule 13)."
        )

    factor = 1.0
    for y in range(year, config.weather_year):
        factor *= 1.0 + _get_growth_rate(config, y)
    logger.warning(
        "demand de-growth: target year %d precedes weather base %d -- "
        "dividing the weather-year load by the compounded growth over "
        "[%d, %d) (factor %.4f). Previously this span silently applied 1.0.",
        year,
        config.weather_year,
        year,
        config.weather_year,
        factor,
    )
    return base_demand / factor


def _hindcast_measured_demand(
    config: ScenarioConfig,
    iso: str,
    iso_config,
    year: int,
    import_generators: list,
) -> np.ndarray:
    """Load ``year``'s MEASURED hourly zonal demand -- the hindcast LP's basis.

    THE single construction of a hindcast year's measured load (rule 19
    [R-ONE-MECH]). The LP's ``year_base_demand`` reads it here, and under
    ``capacity_screen_peak_measured_hindcast`` (capx D76) the capacity-screen
    seam peak reads **the same array**, loaded once per year and shared -- so
    the screens and the LP can never be handed two different measured loads for
    one year, which is the whole defect the gate repairs.

    No growth scaling and no additive load layers: this is the realized year's
    metered profile (plan §1.3), and the forecast-only DC / electrification
    layers are never added on top of measured actuals.

    Args:
        config: The run config (supplies the loader's T&D and profile options
            and the hour count).
        iso: ISO code.
        iso_config: The topology-resolved ``ISOConfig`` (zone set and shares).
        year: The realized year to load.
        import_generators: The interchange import fleet. Non-empty means the
            ISO carries an import NODE, so the loader must not fold
            interchange into zonal demand.

    Returns:
        The ``(n_zones, hours)`` measured demand array, truncated to
        ``config.hours``.
    """
    demand = load_demand(
        iso,
        year,
        iso_config,
        td_loss_factor=config.td_loss_factor,
        include_interchange=not import_generators,
        strict_demand_profile=config.strict_demand_profile,
        ercot_tie_zonal_interchange=config.ercot_tie_zonal_interchange,
        nwpp_grid_carried_wind_served=config.nwpp_grid_carried_wind_served,
        nwpp_demand_plant_basis=config.nwpp_demand_plant_basis,
        demand_balance_screen=config.demand_balance_screen,
    )
    if config.hours < demand.shape[1]:
        demand = demand[:, : config.hours]
    return demand


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
    is returned unchanged (the SAME object -- byte-identical behaviour).
    Anti-whipsaw smoothing only; consumed exclusively by the capacity
    screens, never by dispatch or results.
    """
    if alpha >= 1.0 or prev_signal is None:
        return econ_prices
    return alpha * econ_prices + (1.0 - alpha) * prev_signal


def _storage_shave_terms(storage) -> tuple[float, float, float] | None:
    """Aggregate the storage fleet into ``(power_mw, energy_mwh, rte)``.

    The FFR-5D repair (a) inputs for :func:`_storage_peak_shave_net_load`,
    read from the already-carried ``StorageArrays`` fields only (rule 23
    ``[R-FROZEN-DERIVE]`` / rule 24 ``[R-REGISTRY]``: zero new tunables).
    Vintage-ramp 2-D cap profiles take their final-hour value — a unit ramping
    in mid-year is fully online in the ENTERING year the pro-forma prices.
    Round-trip efficiency is the energy-capacity-weighted mean of
    ``eta_chg * eta_dis``. ``None`` when the fleet has no power or no energy.
    """
    power = np.asarray(storage.power_cap, dtype=float)
    energy = np.asarray(storage.energy_cap, dtype=float)
    if power.ndim == 2:
        power = power[:, -1]
    if energy.ndim == 2:
        energy = energy[:, -1]
    p_mw = float(power.sum())
    e_mwh = float(energy.sum())
    if p_mw <= 0.0 or e_mwh <= 0.0:
        return None
    rte = float(
        (
            np.asarray(storage.eta_chg, dtype=float)
            * np.asarray(storage.eta_dis, dtype=float)
            * energy
        ).sum()
        / e_mwh
    )
    return p_mw, e_mwh, max(rte, 1e-6)


def _storage_peak_shave_net_load(
    net_load: np.ndarray,
    power_mw: float,
    energy_mwh: float,
    rte: float,
) -> np.ndarray:
    """Return net load adjusted for the storage fleet (FFR-5D repair (a)).

    The energy/duration-limited equivalent of storage entering the pro-forma
    merit stack: per calendar day the fleet discharges into the day's highest
    net-load hours (water-filling down to a shave level, per-hour cap
    ``power_mw``, daily energy budget ``energy_mwh`` — one cycle per day) and
    recharges ``discharge / rte`` from the day's lowest hours (valley-filling
    up to a fill level with the same power cap). The fill level is bounded
    above by the shave level, so charge and discharge hours are disjoint by
    construction and a day with insufficient cheap headroom replenishes only
    partially. Both levels are found by vectorized per-day bisection — no
    hour loop (rule 2 ``[R-VECTOR]``). Hours beyond the last whole day (none
    at T=8760) pass through unchanged.

    A static stack cannot represent an energy-limited resource as a supply
    block (it would run unlimited hours); shifting the net load the stack
    prices is the standard energy-constrained treatment and mirrors what the
    LP's own storage dispatch does — discharge at the peak, charge in the
    trough. All three parameters come from the carried ``StorageArrays``
    (:func:`_storage_shave_terms`); no new tunables (rules 23/24).
    """
    T = int(net_load.shape[0])
    n_days = T // 24
    if n_days == 0 or power_mw <= 0.0 or energy_mwh <= 0.0:
        return net_load
    days = net_load[: n_days * 24].reshape(n_days, 24)
    p = float(power_mw)
    # Daily discharge budget: the fleet's energy cap, bounded by 24 h at full
    # power (a pure cap-consistency bound, not a parameter).
    e_day = min(float(energy_mwh), 24.0 * p)
    # Discharge: bisect the shave level L per day so that
    # sum_i min(P, max(0, y_i - L)) == E. hi starts at the day max (zero
    # discharge) and lo at (min - P) (every hour at full power), so the
    # bracket always contains the root; 50 halvings put the level error below
    # any physical resolution. Exact equality counts as "over" so the level
    # converges to the TOP of a power-cap-induced equal-spend plateau (the
    # highest level that spends the budget) — ``hi`` then never over-spends,
    # and the charge bracket below stays non-degenerate.
    lo = days.min(axis=1) - p
    hi = days.max(axis=1)
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        spend = np.minimum(p, np.clip(days - mid[:, None], 0.0, None)).sum(axis=1)
        over = spend >= e_day
        lo = np.where(over, mid, lo)
        hi = np.where(over, hi, mid)
    shave_level = hi
    discharge = np.minimum(p, np.clip(days - shave_level[:, None], 0.0, None))
    # Charge: replenish discharge / rte from the day's lowest hours, filling
    # up to level M <= shave level (disjoint hour sets by construction).
    target = discharge.sum(axis=1) / rte
    lo_c = days.min(axis=1)
    hi_c = shave_level.copy()
    for _ in range(50):
        mid = 0.5 * (lo_c + hi_c)
        fill = np.minimum(p, np.clip(mid[:, None] - days, 0.0, None)).sum(axis=1)
        enough = fill >= target
        hi_c = np.where(enough, mid, hi_c)
        lo_c = np.where(enough, lo_c, mid)
    charge = np.minimum(p, np.clip(hi_c[:, None] - days, 0.0, None))
    adjusted = net_load.copy()
    adjusted[: n_days * 24] = (days - discharge + charge).reshape(-1)
    return adjusted


def _lookahead_reprice_signal(
    config: ScenarioConfig,
    next_year: int,
    base_demand: np.ndarray,
    fleet_arrays,
    mc_cost: np.ndarray,
    result,
    n_zones: int,
    demand_next_total: np.ndarray | None = None,
    pipeline_mc: np.ndarray | None = None,
    pipeline_arrays=None,
    pipeline_vre: np.ndarray | None = None,
    vre_capacity_potential: np.ndarray | None = None,
    storage_shave: tuple[float, float, float] | None = None,
    hourly_availability: bool = False,
    scarcity_restoration: dict | None = None,
    diagnostics: dict | None = None,
    extra_stack: "tuple[np.ndarray, np.ndarray] | None" = None,
    extra_vre: np.ndarray | None = None,
) -> np.ndarray:
    """Stack re-price of the entering year's known net load (plan §2.3.2).

    The pro-forma a developer runs against the known fleet, with zero fitted
    parameters: price each hour of next year's net-load duration
    (``demand_{Y+1} - `` this year's VRE output) by ``np.searchsorted`` into
    the current fleet's marginal-cost supply stack (time-mean full variable
    cost, availability-derated capacity), and apply the same ORDC scarcity
    curve the runner's capacity-economics overlay uses where the stack
    thins/exhausts. O(T log G) numpy, no hour loop (rule 2). Feeds ONLY the
    capacity screens via ``prior_results.price_signal`` -- never dispatch,
    results, or the backcast (backcast mode has no capacity evolution).

    ``demand_next_total`` overrides the entering-year total demand ``(T,)``.
    A **capacity hindcast** (plan §1.3) dispatches the *realized* per-year
    demand with no growth scaling (``run_scenario_iso`` line ~872), so the
    "known" entering-year net load must be that same realized next-year load --
    not ``_scale_demand``'s growth-scaled weather year, which is the forecast
    path. The caller passes the realized ``load_demand(iso, next_year, ...)``
    total here; ``None`` (the plain-forecast path) falls back to
    ``_scale_demand`` unchanged.

    **Committed pipeline (FFR-5C ``entry_pipeline_aware_signal``, GATED).**
    Without the gate the stack is the *current* fleet only, so a developer's
    pro-forma cannot see capacity it has already committed and re-decides the
    same opportunity every lag year -- the pipeline-stuffing cobweb, which
    FFR-4A §3.5 located HERE rather than at the annual flow caps that were
    guarding it. Armed, the caller supplies the pipeline rows that are ONLINE
    in ``next_year`` (``cod_year <= next_year``): ``pipeline_arrays`` /
    ``pipeline_mc`` are the thermal rows' ``FleetArrays`` and ``(n, T)``
    marginal cost, built by the SAME builder/assembler the current fleet's
    stack uses, appended to the merit stack; ``pipeline_vre`` is the ``(T,)``
    potential output of pending wind/solar at their own zones' capacity
    factors, added to the net-load VRE term. All three ``None`` -- the default
    and the whole unarmed path -- is byte-identical.

    **Level repairs (FFR-5D ``capacity_screen_unified_lookahead``, GATED).**
    FFR-5A §2a measured three completeness gaps in the as-built object that
    jointly manufacture 122 pro-forma scarcity hours (88 h > $1000, max
    $5000) on a 34.8 %-reserve-margin fleet, so every fuel clears its
    retirement bar 4-13x. Each repair reads existing model state only — zero
    new tunables (rules 23/24) — and each defaults off (byte-identical):

    * ``vre_capacity_potential`` (repair b): the ENTERING fleet's wind/solar
      MW x the model's own hourly CF basis, ``(T,)`` — replaces the
      prior year's REALIZED dispatched VRE output as the net-load VRE term
      (realized output embeds prior-year curtailment and under-counts the
      capacity actually facing the entering year). ``pipeline_vre`` still
      adds on top when the FFR-5C gate is armed.
    * ``storage_shave`` (repair a): ``(power_mw, energy_mwh, rte)`` of the
      entering storage fleet — the stack was thermal-only; the fleet enters
      as a per-day energy-limited peak-shave/valley-fill on net load
      (:func:`_storage_peak_shave_net_load`).
    * ``hourly_availability`` (repair c): derate the stack by the outage
      model's HOURLY availability instead of the annual time-mean.
      Maintenance is scheduled off-peak, so a time-mean derate (~0.79-0.85)
      understates peak-hour capacity exactly where scarcity is priced. The
      per-hour cumulative stack replaces the scalar one; the merit order
      (time-mean mc) is unchanged.

    **Margin-exhaustion walk seams (D11-R ``entry_margin_exhaustion``,
    GATED).** ``extra_stack`` is ``(mc_1d, cap_1d)`` — the walk's accumulated
    thermal tranches, appended to the merit stack at the entrant's variable
    cost and availability-derated capacity (the same append the FFR-5C
    pipeline rows use; a flat capacity row under hourly availability).
    ``extra_vre`` is a ``(T,)`` MW profile added to the net-load VRE term —
    the walk's VRE tranches at their build zone's hourly CF (and must-run
    tranches at their flat screen CF). Both ``None`` — the default and every
    unarmed path — is byte-identical.

    Returns:
        ``(n_zones, T)`` system-wide hourly price signal (every zone sees the
        same stack price, matching the screens' system-level use).
    """
    if demand_next_total is not None:
        demand_next = np.asarray(demand_next_total, dtype=float)  # (T,)
    else:
        demand_next = _scale_demand(base_demand, config, next_year).sum(axis=0)  # (T,)
    if vre_capacity_potential is not None:
        # FFR-5D repair (b): entering-fleet potential, not prior realized.
        vre = np.asarray(vre_capacity_potential, dtype=float)  # (T,)
    else:
        vre = (result.wind_dispatched + result.solar_dispatched).sum(axis=0)  # (T,)
    if pipeline_vre is not None:
        vre = vre + np.asarray(pipeline_vre, dtype=float)
    if extra_vre is not None:
        # D11-R walk tranches (VRE / must-run): CF-shaped output enters the
        # net-load VRE term, the model's own representation of both classes.
        vre = vre + np.asarray(extra_vre, dtype=float)
    net_load = demand_next - vre
    # FFR-8A: the system net load BEFORE the storage shave — the axis the
    # committed-capability share tables were derived on (demand - wind -
    # solar, no storage term; scripts/data/derive_ercot_rtolcap_forward.py).
    net_load_system = net_load
    if storage_shave is not None:
        # FFR-5D repair (a): the storage fleet shifts the net load the stack
        # prices — discharge at the peak, charge in the trough, per day.
        net_load = _storage_peak_shave_net_load(net_load, *storage_shave)
    # Static merit stack: per-generator time-mean full variable cost against
    # availability-derated capacity (outages/derates included).
    mc_gen = np.asarray(mc_cost, dtype=float).mean(axis=1)  # (n_gen,)
    cap_gen = np.asarray(fleet_arrays.pmax, dtype=float) * np.asarray(
        fleet_arrays.availability, dtype=float
    ).mean(axis=1)  # (n_gen,)
    if pipeline_arrays is not None and pipeline_mc is not None:
        # Committed thermal pipeline online in the priced year, on exactly the
        # same time-mean cost / derated-capacity basis as the fleet above.
        mc_gen = np.concatenate(
            [mc_gen, np.asarray(pipeline_mc, dtype=float).mean(axis=1)]
        )
        cap_gen = np.concatenate(
            [
                cap_gen,
                np.asarray(pipeline_arrays.pmax, dtype=float)
                * np.asarray(pipeline_arrays.availability, dtype=float).mean(axis=1),
            ]
        )
    if extra_stack is not None:
        # D11-R walk tranches (thermal): entrant variable cost against
        # availability-derated capacity — the same static-stack basis as the
        # fleet and pipeline rows above.
        _ex_mc, _ex_cap = extra_stack
        mc_gen = np.concatenate([mc_gen, np.asarray(_ex_mc, dtype=float)])
        cap_gen = np.concatenate([cap_gen, np.asarray(_ex_cap, dtype=float)])
    order = np.argsort(mc_gen, kind="stable")
    mc_sorted = mc_gen[order]
    # FFR-8A element E2 (armed only): the pre-RTC design procures the AS plan
    # day-ahead and SCED dispatches around the awards, so responsive AS held
    # on thermal units is not offered to energy — the marginal ENERGY unit
    # sits at net load PLUS the thermal-held AS. Search-target only: the
    # reserve quantities below keep counting AS-held headroom as reserve
    # (RTOLCAP's published definition).
    as_hold = None
    if scarcity_restoration is not None:
        as_hold = ercot_lookahead_as_hold_mw(
            next_year,
            net_load.shape[0],
            load_mw=demand_next,
            wind_mw=scarcity_restoration["wind_potential_mw"],
            solar_mw=scarcity_restoration["solar_potential_mw"],
            storage_as_mw=scarcity_restoration["storage_as_mw"],
        )
    search_load = net_load if as_hold is None else net_load + as_hold
    if hourly_availability:
        # FFR-5D repair (c): per-hour availability-derated cumulative stack.
        # Merit order is unchanged (time-mean mc); only the capacity each
        # tranche offers in hour t is that hour's own derated capacity. The
        # per-hour left-searchsorted index is the count of cumulative-capacity
        # entries strictly below the hour's net load — identical semantics to
        # np.searchsorted(..., side="left") on the scalar path.
        cap_ht = np.asarray(fleet_arrays.pmax, dtype=float)[:, None] * np.asarray(
            fleet_arrays.availability, dtype=float
        )  # (n_gen, T)
        if pipeline_arrays is not None and pipeline_mc is not None:
            cap_ht = np.concatenate(
                [
                    cap_ht,
                    np.asarray(pipeline_arrays.pmax, dtype=float)[:, None]
                    * np.asarray(pipeline_arrays.availability, dtype=float),
                ]
            )
        if extra_stack is not None:
            # Walk tranches carry a flat availability-derated capacity (the
            # tranche's EFORD derate is already inside cap_1d), broadcast
            # over the hours so the row count matches ``order``.
            cap_ht = np.concatenate(
                [
                    cap_ht,
                    np.broadcast_to(
                        np.asarray(extra_stack[1], dtype=float)[:, None],
                        (np.asarray(extra_stack[1]).size, cap_ht.shape[1]),
                    ),
                ]
            )
        cum_cap_ht = np.cumsum(cap_ht[order], axis=0)  # (n_gen, T)
        load_pos = np.clip(search_load, 0.0, None)
        idx = (cum_cap_ht < load_pos[None, :]).sum(axis=0)  # (T,)
        top_of_stack = cum_cap_ht[-1]  # (T,) per-hour available capacity
    else:
        cum_cap = np.cumsum(cap_gen[order])
        idx = np.searchsorted(cum_cap, np.clip(search_load, 0.0, None), side="left")
        top_of_stack = cum_cap[-1]
    prices_h = mc_sorted[np.minimum(idx, mc_sorted.size - 1)]
    # ORDC scarcity tail where the stack exhausts (same curve, same gate as
    # the post-solve capacity-economics adder; reserve-rich hours get ~0).
    adder = None
    r_online = r_full = None
    if config.scarcity_pricing_enabled and config.scarcity_price_overlay:
        reserves = top_of_stack - net_load
        if scarcity_restoration is not None:
            # FFR-8A elements E1 + E4: the published curve on the COMMITTED
            # on-line capability (bounded by the physical headroom), integrated
            # over the fleet's own forced-outage realization distribution —
            # replaces the installed-headroom point evaluation below, one tail
            # per run (rule 19).
            r_online, r_full = ercot_lookahead_committed_reserves(
                config,
                fleet_arrays,
                net_load.shape[0],
                net_load=net_load_system,
                phys_headroom=np.broadcast_to(
                    np.asarray(top_of_stack, dtype=float), net_load.shape
                )
                - net_load,
                storage_as_mw=scarcity_restoration["storage_as_mw"],
            )
            adder = ercot_lookahead_expected_ordc_adder(
                config,
                next_year,
                r_online_mw=r_online,
                r_full_mw=r_full,
                system_lambda=prices_h,
                sigma_r_mw=scarcity_restoration["sigma_r_mw"],
            )
        else:
            adder = scarcity_prices(config, next_year, reserves, prices_h)[
                "scarcity_adder"
            ]
        prices_h = prices_h + adder
    if diagnostics is not None:
        diagnostics.update(
            {
                "entering_year": int(next_year),
                "net_load_system_mw": np.asarray(net_load_system, dtype=float),
                "net_load_mw": np.asarray(net_load, dtype=float),
                "top_of_stack_mw": np.broadcast_to(
                    np.asarray(top_of_stack, dtype=float), net_load.shape
                ).copy(),
                "installed_headroom_mw": np.broadcast_to(
                    np.asarray(top_of_stack, dtype=float), net_load.shape
                )
                - net_load,
                "price_base_usd_mwh": mc_sorted[np.minimum(idx, mc_sorted.size - 1)],
                "adder_usd_mwh": (
                    np.zeros_like(net_load) if adder is None else np.asarray(adder)
                ),
                "mc_sorted_usd_mwh": np.asarray(mc_sorted, dtype=float),
                "cap_sorted_mean_mw": np.asarray(cap_gen, dtype=float)[order],
            }
        )
        if as_hold is not None:
            diagnostics["as_hold_mw"] = np.asarray(as_hold, dtype=float)
        if r_online is not None:
            diagnostics["r_online_mw"] = np.asarray(r_online, dtype=float)
            diagnostics["r_full_mw"] = np.asarray(r_full, dtype=float)
            diagnostics["sigma_r_mw"] = np.asarray(
                scarcity_restoration["sigma_r_mw"], dtype=float
            )
            diagnostics["storage_as_mw"] = float(scarcity_restoration["storage_as_mw"])
    return np.tile(prices_h[None, :], (n_zones, 1))


def _forward_expectation_signal(
    econ_prices: np.ndarray,
    sig_next_flat: np.ndarray,
    sig_curr_flat: np.ndarray,
) -> np.ndarray:
    """Compose the forward-expectation capacity-screen signal (zero-DOF).

    ``signal[z, t] = econ_prices[z, t] + (sig_next[t] - sig_curr[t])`` — the
    run's own prior-year hourly zonal LP dual surface (with the same
    post-solve scarcity overlay the screens' disarm fallback reads) re-leveled
    hour by hour by the lookahead stack instrument's own forward delta: the
    SAME stack / VRE / storage / ORDC-tail basis evaluated at the entering
    year's demand (plus the committed pipeline, when armed) minus the same
    instrument at the current year's dispatched demand. Locational AND
    forward-looking — the developer-pro-forma corner neither measured arm of
    the disarm probe tested (``docs/FINDING-entry-signal-disarm-2026-08.md``
    §6). Exact arithmetic, no coefficient anywhere (rule 21 ``[R-DOF]``);
    returns a NEW array — the duals are never mutated. Gated by
    ``entry_forward_expectation_signal`` at the ``_screen_signal_for`` seam.
    """
    delta = np.asarray(sig_next_flat, dtype=float) - np.asarray(
        sig_curr_flat, dtype=float
    )
    return np.asarray(econ_prices, dtype=float) + delta[None, :]


def _daily_top_bottom_spread(price_h: np.ndarray, k: int = 4) -> float:
    """Mean over whole days of (top-k hour mean - bottom-k hour mean), $/MWh.

    Log-line diagnostic only (the D39 §2 instrument's daily spread
    statistic); hours beyond the last whole day are ignored.
    """
    p = np.asarray(price_h, dtype=float)
    n_days = p.size // 24
    if n_days == 0:
        return 0.0
    days = np.sort(p[: n_days * 24].reshape(n_days, 24), axis=1)
    return float((days[:, -k:].mean(axis=1) - days[:, :k].mean(axis=1)).mean())


def _headroom_rank(headroom_next: np.ndarray, headroom_curr: np.ndarray) -> np.ndarray:
    """Mid-rank empirical CDF of the entering year's headroom on the current year's.

    ``u[t]`` is the fraction of CURRENT-year hours whose headroom lies below
    ``headroom_next[t]``, with ties split at the midpoint (the average of the
    left and right ``searchsorted`` positions) so equal values rank equally
    and the map is monotone. A forward hour tighter than every current hour
    ranks 0.0; looser than every current hour ranks 1.0. Vectorized (rule 2
    ``[R-VECTOR]``): two searchsorted calls, no hour loop.
    """
    h_sorted = np.sort(np.asarray(headroom_curr, dtype=float))
    h_next = np.asarray(headroom_next, dtype=float)
    lo = np.searchsorted(h_sorted, h_next, side="left")
    hi = np.searchsorted(h_sorted, h_next, side="right")
    return (lo + hi) / (2.0 * h_sorted.size)


def _dispersion_expectation_signal(
    econ_prices: np.ndarray,
    headroom_next: np.ndarray,
    headroom_curr: np.ndarray,
) -> np.ndarray:
    """Compose the dispersion-carrying capacity-screen entry signal (zero-DOF).

    capx D43 (``docs/handoffs/FINDING-capx-d39-entry-underbuild-2026-09-02.md``
    §0/§3.1 is the object; the CAISO A/B is the adjudication). The screens'
    price object becomes each zone's OWN realized price-duration curve — the
    prior solve's hourly zonal LP duals, ``econ_prices`` with the same
    post-solve scarcity overlay the screens' disarm fallback reads —
    indexed by the ENTERING year's headroom rank on the CURRENT year's
    headroom distribution::

        u[t]         = _headroom_rank(headroom_next, headroom_curr)[t]
        signal[z, t] = quantile_{1 - u[t]} ( econ_prices[z, :] )

    An hour whose forward headroom (``top_of_stack - net_load``, the
    lookahead instrument's own ``installed_headroom_mw``) sits at the p-th
    percentile of this year's headroom earns this zone's p-th-percentile
    realized price: the merit stack's structural assumption (price is a
    monotone function of net-load position) applied to the REALIZED dual
    distribution instead of the time-mean MC step. The quantile is read by
    linear interpolation on the mid-rank grid ``((i + 0.5) / T)`` of each
    zone's ascending-sorted duals, so at unchanged headroom the map is an
    exact permutation — every zone's price multiset (mean, duration curve,
    hours >= $100, negative hours, zonal spread in distribution) is
    reproduced exactly, and a dual surface that is itself monotone in
    headroom is reproduced hour by hour. Forward hours outside the current
    range clamp to the zone's realized minimum / maximum: the ceiling is the
    dual surface itself, never a pro-forma tail. Exact arithmetic, no
    coefficient anywhere (rule 21 ``[R-DOF]``); returns a NEW ``(n_zones,
    T)`` array — the duals are never mutated. Gated by
    ``entry_dispersion_expectation_signal`` at the ``_screen_signal_for``
    seam. Vectorized: one sort per zone and one interpolation pass (rule 2
    ``[R-VECTOR]``).
    """
    prices = np.asarray(econ_prices, dtype=float)
    n_zones, T = prices.shape
    u = _headroom_rank(headroom_next, headroom_curr)  # (T_next,)
    q = 1.0 - u  # tight headroom -> high quantile
    grid = (np.arange(T) + 0.5) / T
    sorted_duals = np.sort(prices, axis=1)  # ascending per zone
    out = np.empty((n_zones, u.size), dtype=float)
    for z in range(n_zones):  # z = zone (a handful; hours are vectorized)
        out[z] = np.interp(q, grid, sorted_duals[z])
    return out


class _EntryRepriceWalk:
    """Shared repricer state for the margin-exhaustion entry walk (D11-R).

    The live productionization of the L-1b closure
    (``docs/FINDING-entry-signal-l1-2026-08.md`` §2, gated
    ``entry_margin_exhaustion``): one object per priced entering year,
    threaded through ``prior_results.entry_reprice`` into BOTH allocators —
    the thermal/VRE screen (``apply_economic_new_entry``) first, then the
    storage screen (``apply_storage_new_entry``) — so the two walks share one
    accumulated capacity state in their live decision order (rule 19
    ``[R-ONE-MECH]``: one mechanism, one state).

    ``reprice_fn(extra_stack, extra_vre, d_power_mw, d_energy_mwh, rte_added)``
    is a closure over the seam's own :func:`_lookahead_reprice_signal` inputs
    (built in ``_screen_signal_for``), returning ``(flat_signal, adder)`` at
    the given walk additions — so the repricing is the SAME instrument that
    produced the screens' signal, re-invoked, never a model of it. At zero
    additions it reproduces the seam's own call bitwise, which anchors the
    delta construction exactly (the probe's own trick): the walk signal is
    ``consumed + alpha x (S(state) - S(0))`` where ``alpha`` is the screen's
    EWMA blend coefficient (the consumed signal is affine in S_entering
    through both the blend and the forward-expectation composition), and the
    hourly reserve-price legs shift by the raw within-walk adder delta
    (:meth:`reserve_delta`), floored at zero by the caller — a
    within-instrument, within-year difference, zero before any tranche.

    Zero fitted parameters (rule 21 ``[R-DOF]``): every increment enters
    through the model's own seams (thermal at entrant variable cost x
    ``1 - EFORD`` into the merit stack; VRE and must-run as CF-shaped
    net-load reduction; storage through the peak-shave + AS-share terms).
    """

    def __init__(self, reprice_fn, alpha: float):
        self._reprice = reprice_fn
        self._alpha = float(alpha)
        self._mc: list[float] = []
        self._cap: list[float] = []
        self._vre: np.ndarray | None = None
        # (power_mw, energy_mwh, rte) per committed storage tranche.
        self._storage: list[tuple[float, float, float]] = []
        self._s0, self._a0 = self._eval()
        self._sig = self._s0
        self._adder = self._a0

    def _eval(self) -> tuple[np.ndarray, np.ndarray]:
        """Re-invoke the seam's instrument at the current walk state."""
        extra_stack = (
            (np.asarray(self._mc, dtype=float), np.asarray(self._cap, dtype=float))
            if self._mc
            else None
        )
        d_p = sum(mw for mw, _, _ in self._storage)
        d_e = sum(mwh for _, mwh, _ in self._storage)
        rte_added = (
            sum(mwh * rte for _, mwh, rte in self._storage) / d_e if d_e > 0.0 else None
        )
        return self._reprice(extra_stack, self._vre, d_p, d_e, rte_added)

    def add_thermal(self, var_cost: float, mw: float, availability: float) -> None:
        """Commit a thermal tranche: merit-stack row at derated capacity."""
        self._mc.append(float(var_cost))
        self._cap.append(float(mw) * float(availability))
        self._sig, self._adder = self._eval()

    def add_net_load_reduction(self, profile_mw: np.ndarray) -> None:
        """Commit a VRE/must-run tranche: (T,) MW output into the VRE term."""
        profile_mw = np.asarray(profile_mw, dtype=float)
        self._vre = profile_mw if self._vre is None else self._vre + profile_mw
        self._sig, self._adder = self._eval()

    def add_storage(self, mw: float, duration_hr: float, rte: float) -> None:
        """Commit a storage tranche: shave + AS-share terms move with it."""
        self._storage.append((float(mw), float(mw) * float(duration_hr), float(rte)))
        self._sig, self._adder = self._eval()

    def signal(self, consumed: np.ndarray) -> np.ndarray:
        """The consumed screen signal shifted by the walk's own delta."""
        consumed = np.asarray(consumed, dtype=float)
        delta = self._alpha * (self._sig - self._s0)
        if consumed.ndim == 2:
            return consumed + delta[None, : consumed.shape[1]]
        return consumed + delta[: consumed.shape[0]]

    def reserve_delta(self) -> np.ndarray:
        """(T,) within-walk expected-ORDC adder delta (0 before any tranche)."""
        return self._adder - self._a0


def _pipeline_lookahead_terms(
    config: ScenarioConfig,
    fleet_config: ScenarioConfig,
    iso: str,
    entry_pipeline: list[dict] | None,
    through_year: int,
    year: int,
    zone_names: list[str],
    wind_cf: np.ndarray,
    solar_cf: np.ndarray,
    load_shape: np.ndarray,
    carbon_price,
) -> tuple:
    """Value the committed entry pipeline for the look-ahead pro-forma (FFR-5C).

    Turns the ``entry_pipeline`` rows that are ONLINE in ``through_year`` into
    the three terms :func:`_lookahead_reprice_signal` accepts, so the entry
    screen's price signal stops being blind to capacity the model has already
    committed (FFR-4A §3.5 / E-2 -- the anti-cobweb guard's real object).
    Gated by ``entry_pipeline_aware_signal``; the caller only invokes it when
    the gate is armed.

    **Zero new tunables** (rule 24 ``[R-REGISTRY]``). Thermal rows are built by
    :func:`~market_sim.model.capacity.pipeline_lookahead_units` (the same
    ``_make_new_generator`` the step-4.5 commissioning uses) and priced through
    the same ``generators_to_fleet_arrays`` -> ``resolve_fuel_prices`` ->
    ``assemble_mc`` seam as the current fleet's stack, at THIS year's fuel and
    carbon basis so the pro-forma's two halves share one cost basis (rule 19).
    VRE rows carry no Generator -- they enter the model as zonal pools -- so
    they are valued at their own zone's hourly capacity factor, the same array
    that upper-bounds ``W[z,t]``/``S[z,t]`` in the LP. That is a *potential*
    (pre-curtailment) basis, one notch richer than the realized-dispatch VRE
    term it is added to; the pro-forma has no curtailment model to apply and
    inventing a haircut would be a fitted parameter (rules 5 / 24).

    A row whose zone is absent from ``zone_names`` is skipped with a warning
    rather than silently mis-assigned.

    Args:
        config: The run's scenario configuration.
        fleet_config: The (possibly outage-overlay-adjusted) config the year's
            own ``generators_to_fleet_arrays`` call used, so the pipeline units
            are built on identical terms.
        iso: ISO identifier.
        entry_pipeline: The pending-entry queue (read-only here), or ``None``.
        through_year: The year being priced -- rows with a later COD are out.
        year: The dispatch year, i.e. the fuel/carbon basis of the stack.
        zone_names: Model zone order (indexes ``wind_cf``/``solar_cf``).
        wind_cf: ``(n_zones, T)`` wind capacity factors.
        solar_cf: ``(n_zones, T)`` solar capacity factors.
        load_shape: Hourly total demand passed to the fleet-array builder.
        carbon_price: The year's resolved carbon price (scalar or hourly).

    Returns:
        ``(pipeline_arrays, pipeline_mc, pipeline_vre)``; each element is
        ``None`` when the pipeline contributes nothing of that kind.
    """
    units, vre_mw = pipeline_lookahead_units(entry_pipeline, through_year, config, iso)
    pipeline_vre: np.ndarray | None = None
    if vre_mw:
        zone_idx = {name: i for i, name in enumerate(zone_names)}
        acc = np.zeros(int(wind_cf.shape[1]), dtype=float)
        for (zone, tech), mw in sorted(vre_mw.items()):
            cf = wind_cf if tech == "wind" else solar_cf
            z = zone_idx.get(zone)
            if z is None or z >= cf.shape[0]:
                logger.warning(
                    "lookahead pipeline: %s row in zone %r is not a model zone "
                    "-- %0.1f MW excluded from the pro-forma stack",
                    tech,
                    zone,
                    mw,
                )
                continue
            acc = acc + mw * np.asarray(cf[z], dtype=float)
        pipeline_vre = acc
    pipeline_arrays = None
    pipeline_mc = None
    if units:
        pipeline_arrays = generators_to_fleet_arrays(
            units,
            zone_names,
            hours=config.hours,
            iso=iso,
            config=fleet_config,
            load_shape=load_shape,
            year=year,
        )
        pipeline_mc = assemble_mc(
            pipeline_arrays,
            resolve_fuel_prices(config, pipeline_arrays, year),
            carbon_price,
            config.nox_price,
            so2=(pipeline_arrays.so2_rate, config.so2_price),
        )
    return pipeline_arrays, pipeline_mc, pipeline_vre


def _confirmed_exits_active(config: ScenarioConfig) -> bool:
    """Return True when the confirmed-exit channel should load/apply this run.

    Forecast-mode only, regardless of ``confirmed_exits_enabled``'s default --
    a backcast run is a hard no-op even after the 2026-07-05 default flip
    (`docs/handoffs/confirmed-retirement-plan-2026-07.md` §7), since backcast's
    historical exits ride the vintage snapshot instead.
    """
    return config.mode == "forecast" and config.confirmed_exits_enabled


def _rps_region_grain_active(config: ScenarioConfig, iso: str) -> bool:
    """Return True when the K-row per-compliance-region RPS grain is built.

    THE single gate on FFR-7B Arm 2 / FFR-6B E-1 (``miso_rps_compliance_regions``).
    All three legs must hold:

    * **MISO only** (rule 25 ``[R-ISO-SCOPE]``) -- the four other RPS ISOs'
      single ISO-wide row is arithmetically exact under free intra-ISO REC
      trade (FFR-6B §2.1), so their LP stays byte-identical.
    * **Forecast mode only.** The gate is enforced HERE, at consumption, not at
      config construction: since owner decision D-26 (sitting Addendum Y.4)
      MISO's ``ISOConfig.default_scenario_overrides`` arms the flag, so a
      backcast-mode MISO config can legitimately carry ``True`` and must still
      resolve the legacy ISO-wide row. Backcast is doubly insulated --
      ``run_calibration_full.py`` never applies ``default_scenario_overrides``
      at all -- but this leg is what makes the flag's presence harmless.
    * **The flag itself**, default-off for every non-MISO caller.

    When False the caller falls through to the scalar ``rps_target`` path; the
    K=1/mask-all special case of the region builder reproduces that row
    byte-identically (``tests/unit/model/test_dispatch.py``
    ``TestRpsComplianceRegionRows``).

    Args:
        config: The scenario configuration being run.
        iso: Resolved ISO identifier, already upper-cased by the caller.

    Returns:
        True when the per-region rows replace the ISO-wide RPS row.
    """
    return (
        iso == "MISO"
        and config.mode == "forecast"
        and getattr(config, "miso_rps_compliance_regions", False)
    )


def _clean_region_arrays_for_year(
    config: ScenarioConfig,
    iso: str,
    year: int,
    zone_names: list[str],
    fleet_arrays,
    zone_demand=None,
):
    """Return the clean-tier row family this ISO-year solves with, or ``None``.

    THE single resolver of the family's region list (SCN-WS2a), used by the
    solve-side arming AND by the ``prior_results`` dual mapping — including
    the cached-year path, which never assembles the solve-side arrays — so
    the restored ``clean_region_duals`` always map onto the identical region
    list the solve was built from. Three legs, in region order:

    * **State clean rows** (FFR-7B Arm 3, MISO only): built iff the state RPS
      rows are (``rps_enabled`` and not the pure-federal counterfactual), the
      K-row grain is active (:func:`_rps_region_grain_active`) and
      ``miso_clean_tier_rows`` is armed — exactly the pre-SCN-WS2a gate, so
      every MISO keeper's family is unchanged (the tuple-form regions).
    * **The federal CES target row** (SCN-WS2a), appended last through
      ``policy.federal_ces.append_federal_ces_region`` when
      ``federal_ces_target_by_year`` is set; it stands alone in every other
      ISO. It is NOT suppressed by ``federal_ces_replaces_state_rps`` (that
      flag removes the STATE rows — the pure-federal posture is exactly the
      federal row standing alone).
    * **The voluntary clean-demand row** (SCN-WS3b, the family's second
      consumer), appended LAST through
      ``policy.voluntary_demand.append_voluntary_region`` when
      ``voluntary_clean_demand_path`` is not ``"off"`` in a forward run: one
      all-zone region whose RHS is the resolved volume ``V(ISO, y)`` — a
      share of THIS year's ``zone_demand`` (after the load layers), which
      is why the demand is an argument here — escaping at the buyer's WTP
      ceiling. Not suppressed by ``federal_ces_replaces_state_rps`` either
      (a voluntary buyer is not a state row). Returned unchanged when off.

    Args:
        config: The scenario configuration being run.
        iso: Resolved ISO identifier, already upper-cased by the caller.
        year: Simulation year.
        zone_names: Model zone names in LP zone-index order.
        fleet_arrays: The fleet the LP solves on (the federal row's
            per-generator credit vector is aligned to it).
        zone_demand: The ``(n_zones, T)`` demand the LP is handed this year
            (the voluntary row's volume is a share of it). ``None`` is legal
            only while the voluntary row is off — the pre-SCN-WS3b call
            shape, byte-identical.

    Returns:
        The composed ``CleanRegionArrays`` or ``None`` (no clean row at all).
    """
    state_arrays = None
    if (
        config.rps_enabled
        and not federal_ces_suppresses_state_rps(config)
        and _rps_region_grain_active(config, iso)
        and getattr(config, "miso_clean_tier_rows", False)
    ):
        state_arrays = build_clean_region_arrays(iso, year, zone_names)
    arrays = append_federal_ces_region(
        config, year, zone_names, fleet_arrays, state_arrays
    )
    return append_voluntary_region(config, iso, year, zone_names, arrays, zone_demand)


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
    # defaults (2026/2050) when set -- a capacity hindcast runs 2021→2025. The
    # defaults keep every existing forecast and cache key unchanged.
    start_year = config.start_year if config.start_year is not None else START_YEAR
    end_year = config.end_year if config.end_year is not None else END_YEAR

    # Resolve the PB-1 policy_bundle lever to its underlying fields (rule 24:
    # config-build time, no hidden state) before cache_key/run_config capture
    # the config -- a no-op for the neutral "current" default.
    config = resolve_policy_bundle(config)

    # Arm/disarm the CAISO FSNO sub-zonal partition for this run BEFORE the
    # first get_iso_config / zone-lookup call, so the LP and every bare
    # get_iso_config() consumer see the same topology (caiso-224; the
    # run_calibration.run_year seam is this line's backcast twin —
    # config.topology_variant module docstring has the full rationale).
    from market_sim.config.topology_variant import set_caiso_fsno_partition

    set_caiso_fsno_partition(
        iso == "CAISO" and getattr(config, "caiso_fsno_subzonal_topology", False)
    )
    # PJM-NEXT fleet_zone_vintage_coords: armed per solve, like the partition
    # above, before the first fleet load reads the zone lookup.
    from market_sim.data.zone_assignment import set_fleet_zone_vintage_coords

    set_fleet_zone_vintage_coords(getattr(config, "fleet_zone_vintage_coords", False))

    iso_config = get_iso_config(iso)
    # Apply ISO-level scenario defaults (e.g. CAISO negative_renewable_offers)
    # for fields the caller has not explicitly set. The rule lives in ONE place
    # (config.iso_configs.apply_iso_scenario_defaults, rule 19) so a run record
    # built OUTSIDE this function can resolve the same posture instead of
    # reporting the caller's unresolved config — the FFR-2E defect class.
    config = apply_iso_scenario_defaults(config, iso)

    # caiso-190: the input-completeness guard on the FORECAST solve path.
    # caiso-157 built it, caiso-188 wired the backcast lane and filed this half
    # as still owed (FINDING-caiso188-import-tranche-dof-2026-08-09.md §6a) —
    # the same silent-degradation surface exists here and had no guard call at
    # all. Runs on the RESOLVED config (after apply_iso_scenario_defaults, so
    # an ISO default that arms a mechanism is checked too) and before any LP
    # input is built.
    #
    # strict=False is the deliberate asymmetry between the lanes: a mechanism
    # with NO declared fallback (hydro_ror_split) still fails fast here, but a
    # DECLARED fallback (capacity_deliverability_limits -> the baked
    # simultaneous-import scalar) warns loudly and records the outcome it
    # produced rather than killing the run. No keeper is promoted from the
    # forecast lane, and the resolved value is now recoverable from
    # run_config.json's resolved_inputs block either way. The calibration lane
    # keeps strict=True, where even a declared fallback is fatal.
    check_clean_partitions(config, iso, strict=False)

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
    # the CAISO per-hub corridor split -- one sequence, both orchestrators.
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
    from market_sim.config.paths import (
        resolve_backcast_eia860_vintage,
        set_eia860_standby_admission,
        set_eia860_vintage,
    )

    # Standby (SB) generator admission for the same loaders (NWPP-NEXT-5,
    # ScenarioConfig.admit_standby_units; {"OP"} while off). Set on every run.
    set_eia860_standby_admission(config.admit_standby_units)

    # A capacity hindcast (plan §1.3) is forecast-mode but initialises from a
    # vintage snapshot (the 2020 Final release) so the modelled start-year fleet
    # matches what actually existed -- the vintage is honoured under
    # config.hindcast too. A plain forecast resets to the canonical snapshot.
    #
    # In BACKCAST mode the weather year IS the solved year, so it is the year
    # eia860_vintage_tracks_solve_year resolves against (pjm-167). The hindcast
    # leg keeps the explicit pin alone -- resolve_backcast_eia860_vintage gives
    # an explicit eia860_vintage_year precedence, and the tracking gate is
    # passed only on the backcast leg, so a hindcast is untouched either way.
    set_eia860_vintage(
        resolve_backcast_eia860_vintage(
            config.eia860_vintage_year,
            int(config.weather_year) if config.mode == "backcast" else None,
            config.mode == "backcast"
            and getattr(config, "eia860_vintage_tracks_solve_year", False),
        )
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
        ercot_tie_zonal_interchange=config.ercot_tie_zonal_interchange,
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
    # miso-255 miso_import_sil_measured_envelope (MISO-only, GATED default off):
    # REPLACE the 8,700 MW bidirectional MISO_simultaneous_import scalar -- the
    # published Capacity Import Limit, a PRA/LOLE accreditation construct being
    # used as the hourly energy bound in both directions -- with MISO's own
    # measured coincident boundary transfer envelope per direction. Rule 14
    # [R-ACCURATE]; replaces, never stacks (rule 19). No-op off the flag, for a
    # non-MISO ISO, or when the envelope does not resolve (a forecast year), so
    # every other run is byte-identical.
    if getattr(config, "miso_import_sil_measured_envelope", False):
        interface_groups, _sil_info = apply_miso_measured_sil_envelope(
            interface_groups,
            iso_config.interface_limits,
            config.weather_year,
            base_demand.shape[1],
            percentile=getattr(config, "miso_seam_flow_percentile", None),
            hour_ending_key=getattr(
                config, "miso_seam_envelope_hour_ending_key", False
            ),
        )
        if _sil_info is not None:
            logger.info(
                "%s: aggregate simultaneous-transfer limit REPLACED by the "
                "measured coincident boundary envelope -- declared scalar "
                "%.0f MW -> import mean %.0f / max %.0f MW, export mean %.0f / "
                "max %.0f MW; import below the scalar in %d h, export in %d h",
                iso,
                _sil_info["declared_scalar_mw"],
                _sil_info["import_env_mean_mw"],
                _sil_info["import_env_max_mw"],
                _sil_info["export_env_mean_mw"],
                _sil_info["export_env_max_mw"],
                _sil_info["hours_import_below_scalar"],
                _sil_info["hours_export_below_scalar"],
            )
        else:
            logger.info(
                "%s: miso_import_sil_measured_envelope armed but no envelope "
                "resolved for %d -- aggregate limit keeps its declared scalar",
                iso,
                config.weather_year,
            )
    # FORWARD ATC corridor deliverability cap (CAISO per-hub corridors,
    # ``caiso_corridor_atc_forward``, default off): corridor TTC × posted-ATC
    # base fraction × forward solar derate -- a capability limit that
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
                "%s: WECC corridor deliverability cap on %d link(s) -- "
                "FORWARD ATC (TTC × ATC-frac × solar derate)",
                iso,
                len(_corridor_groups),
            )

    # Forward transmission-expansion channel (FF-G1, GATED
    # transmission_expansion_enabled, default off): committed-instrument
    # registry rows loaded once here, applied per solve year at the year_ttc
    # seam below. Forecast-forward only — __post_init__ coerces the flag off
    # in backcast/hindcast, and the mode gate here is belt-and-braces.
    # required=True is the fail-loud condition (W2-E / G12 convention): with
    # the flag on, a never-curated checkout raises with the regeneration
    # command instead of silently running the frozen-topology forecast.
    _txexp_expansions: list[TransmissionExpansion] = []
    if (
        config.mode == "forecast"
        and not config.hindcast
        and getattr(config, "transmission_expansion_enabled", False)
    ):
        _txexp_expansions = load_transmission_expansions(iso, required=True)
    # Base (pre-corridor) interface-group count: a per-year expansion rebuild
    # regenerates exactly the declared-limit groups and re-appends any
    # corridor extension groups verbatim (one group per InterfaceLimit, so the
    # declared count is len(iso_config.interface_limits)).
    _txexp_base_group_count = len(iso_config.interface_limits)

    fleet = None
    loss_tracker: dict[str, int] = {}
    prior_results = None
    # EWMA state for the capacity screens' price signal (plan §2.2): the
    # previous year's blended signal. None until the first solved year.
    price_signal_prev: np.ndarray | None = None
    # FFR-5D capacity_screen_unified_lookahead (GATED, default OFF): the
    # per-entering-year lookahead signals the last SOLVED year priced —
    # {entering_year: (n_zones, T)}. Rebuilt at every solved year's seam;
    # consumed at the top of each loop iteration, where the entering year's
    # own signal is swapped into prior_results.price_signal before any
    # screen runs. Empty unarmed (byte-identical).
    unified_signals: dict[int, np.ndarray] = {}
    # D11-R / D12 per-entering-year state, bound here for the SAME reason
    # ``unified_signals`` is: the year loop READS both near its top (the
    # entering-year rebinds) and only re-binds them further down, at the
    # solved-year seam. Both reads are gated on ``prior_results is not None``,
    # so no live path reaches them before the first seam — but the names were
    # nonetheless unbound in this scope on entry, which ruff reports as F821
    # and which is one early ``continue`` away from a real UnboundLocalError.
    # Byte-identical: each is re-assigned to a fresh ``{}`` at the seam on
    # every iteration, so these bindings are only ever read before the first
    # seam, where the gates are False.
    entry_walks: dict[int, _EntryRepriceWalk] = {}
    entry_reserve_adders: dict[int, np.ndarray] = {}

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
    # ramp ages each out by its real retirement month. Backcast-mode only -- a
    # forecast must not carry an already-retired unit. Loaded before the bins
    # are synthesized so the retirees are binned with the rest of the fleet.
    retired_within_window: list[Generator] = []
    if config.mode == "backcast":
        # miso-188 vintage-status oracle (retiree_vintage_status_scope,
        # default off): in a backcast the weather-year pin IS the solve
        # year, so it keys the oracle. The year kwarg is threaded only when
        # the scope is armed so the off path stays byte-identical (the
        # CHP-flag join reads the year too).
        _rvs = getattr(config, "retiree_vintage_status_scope", False)
        # miso-190 partial-plant exit carry: forecast-parity threading of the
        # same gated membership widening (leg 1 only — the mothball re-carry
        # is deliberately not wired here, per the Cottonwood owner default).
        _ppx = getattr(config, "partial_plant_exit_carry", False)
        # SPP-48 mid-vintage-year exit carry: the plants a year-matched native
        # vintage drops from BOTH its sheets because they retired during that
        # very year. Needs the solved year (it selects on it), so it joins the
        # same year-threading predicate; default-off and byte-inert while off.
        _mvx = getattr(config, "mid_vintage_exit_carry", False)
        # F1 D4: the measured heat-rate swaps reach the retiree channel too,
        # at the solved year's own rate (default off outside a backcast).
        _mhr = {
            name: getattr(config, name, False)
            for name in (
                "measured_ct_heat_rates",
                "measured_coal_heat_rates",
                "measured_st_heat_rates",
                "measured_cc_heat_rates",
                "measured_chp_heat_rates",
            )
        }
        retired_within_window = load_retired_within_window(
            iso,
            iso_config,
            year=(
                int(config.weather_year)
                if (_rvs or _ppx or _mvx or any(_mhr.values()))
                else None
            ),
            vintage_status_scope=_rvs,
            partial_plant_exit_carry=_ppx,
            mid_vintage_exit_carry=_mvx,
            **_mhr,
        )

    campd_bins = load_or_synthesize_bins(config, iso, iso_config, retired_within_window)

    # Storage is managed across years like the generation fleet: the base
    # year starts from the deployment-pace fleet, later years grow via the
    # economic new-entry screen.
    #
    # A BACKCAST resolves the base fleet AS OF ITS SOLVE YEAR from EIA-860
    # instead (FFR-4D, rule 14 [R-ACCURATE]). ``STORAGE_BASE_FLEET_MW`` is a
    # FORECAST object -- its own docstring calls it "the base year (2026)" and
    # its low/mid/high are the ``storage_deployment`` scenario ladder -- so
    # feeding it to a 2023 solve is a vintage/as-of misalignment, not a
    # scenario choice. ``load_eia860_storage`` was written for exactly this
    # ("grounds a calibration backcast in the historical storage fleet rather
    # than the forward-looking STORAGE_BASE_FLEET_MW scenario constant") and
    # was ORPHANED -- no runner path called it, so ``storage_vintage_ramp`` was
    # a dead flag for batteries even where a keeper armed it (the caiso-98
    # dead-flag lesson). It matters most where the fleet moved fastest: CAISO's
    # measured battery fleet is 7,492 / 11,131 / 15,448 MW at year-end
    # 2023 / 2024 / 2025 against the flat 8,000 MW the scalar supplied.
    # Rule 25 [R-ISO-SCOPE]: the backcast leg is scoped to the ISOs in
    # ``STORAGE_MEASURED_BASE_FLEET_ISOS`` so the other five keepers stay
    # byte-identical; the loader already appends pumped storage itself.
    #
    # A capacity HINDCAST (mode="forecast" + hindcast=True) has the same
    # vintage/as-of misalignment one notch worse: it fell through to the
    # forward scalar even though set_eia860_vintage above already pointed
    # every EIA-860 loader at the run's vintage_<year>/ snapshot — the
    # FFR-3V renewable-pool leak's storage sibling (FFR-9A). ERCOT's
    # vintage-2020 measured storage fleet is 223 MW against the 17,000 MW
    # scalar, a base the endogenous entry screen then ADDS to (~30 GW by the
    # 2024 solve vs ~10 GW actual — FFR-8B §2.3/§3, the dominant remaining
    # input error on the forward price object). A hindcast therefore seeds
    # from the vintage EIA-860 measured fleet in EVERY ISO — the vintage
    # sheet is precisely what a run at that cutoff may know (rule 13
    # [R-MEASURED]) and measured beats the scalar (rule 14 [R-ACCURATE]);
    # no keeper is affected, so the backcast leg's per-ISO enrollment does
    # not apply. Both legs and their scoping rationale live in
    # ``measured_storage_base_fleet_active``; called at start_year, the
    # vintage sheet's units are all pre-start_year CODs, so the seed carries
    # no intra-year ramp profile (the FFR-3V third-leg hazard).
    measured_storage = measured_storage_base_fleet_active(config, iso)
    if measured_storage:
        storage_units = load_eia860_storage(iso, start_year, config)
        logger.info(
            "%s %d: %d measured EIA-860 storage units (%.0f MW incl. pumped storage)",
            iso,
            start_year,
            len(storage_units),
            sum(u.power_cap_mw for u in storage_units),
        )
    else:
        storage_units = build_default_storage(iso_config, config)

        # Pumped storage is existing installed capacity (EIA-860 prime mover
        # ``PS``, ~20 GW nationally) with no new build, so the parameterized
        # battery builder never includes it. Prepend the EIA-860 PS fleet to the
        # storage list once, before the new-entry screen -- PS is fixed existing
        # capacity and does not participate in the endogenous battery-growth
        # screen (it persists across years because ``apply_storage_new_entry``
        # preserves existing units). Per CLAUDE.md rule #12, EIA-860 installed
        # capacity is a physical asset registry, admissible as a forward input
        # in any year.
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

    # FFR-5E near-term VRE procurement channel (owner decision D-18(a)): the
    # WIND/SOLAR limb of the same known-additions channel above, which skips
    # them because _map_fuel_type returns None for wind and solar. GATED
    # (vre_procurement_additions_enabled, default OFF) and forecast-mode only
    # — a backcast's historical VRE rides the vintage snapshot. Loaded once;
    # rows commission in evolve_fleet step 4 at their EIA-860 effective year.
    procured_vre_additions: list[dict] = []
    if config.mode == "forecast" and getattr(
        config, "vre_procurement_additions_enabled", False
    ):
        procured_vre_additions = load_procured_vre_additions(iso, iso_config)

    # RC-1B hindcast information gate (RC-0B D4): in hindcast mode
    # (config.hindcast, e.g. scripts/run_capacity_hindcast.py), a confirmed
    # exit or an announced-reversal suppression may only apply if it was
    # already knowable as of the vintage cutoff (Dec 31 of the EIA-860 vintage
    # year the hindcast is seeded from) -- never the model's own solve/report
    # date. Outside hindcast mode (the production forecast path) this is
    # None, applying no cutoff (byte-identical to the pre-RC-1B behavior).
    confirmed_registry_as_of: "_dt.date | None" = None
    if getattr(config, "hindcast", False) and config.eia860_vintage_year is not None:
        confirmed_registry_as_of = _dt.date(config.eia860_vintage_year, 12, 31)

    # Confirmed (binding-instrument) exits: the exogenous forecast retirement
    # channel, GATED on confirmed_exits_enabled (default on, flipped 2026-07-05)
    # and forecast-mode only (a backcast's historical exits ride the vintage
    # snapshot, and config.mode == "forecast" here is a hard gate independent of
    # the flag's default, so a backcast run is unaffected by the flip). Loaded
    # once; applied at step 0 of evolve_fleet and the first-year base fleet.
    confirmed_exits: list[ConfirmedExit] = []
    if _confirmed_exits_active(config):
        # required=True (W2-E / G12): this branch IS the fail-loud condition
        # (confirmed_exits_enabled on, forecast mode), so a missing or
        # unimportable registry raises with the regeneration command instead
        # of the warn-only no-op that silently handed ERCOT 477 MW of
        # phantom 2026 fleet (W1-B B3/B4).
        confirmed_exits = load_confirmed_exits(
            iso, as_of=confirmed_registry_as_of, required=True
        )
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
    # (every registry row superseded -- e.g. Byron/Dresden's 2021 dates
    # reversed by IL CEJA) keep running; their stale EIA-860 dates are
    # ignored by evolve_fleet step 1. Deliberately NOT gated on
    # confirmed_exits_enabled: honoring a documented reversal is an
    # announced-channel data correction, not an exogenous exit injection.
    announced_reversal_plants: frozenset[int] = frozenset()
    if config.mode == "forecast":
        # Hindcast announced-exit verification (owner directive 2026-08-22;
        # field docstring in scenarios.py): when armed, the REVERSAL loader
        # bypasses the RC-1B vintage information gate (as_of=None) so an
        # announced date the realized record shows was cancelled by a later
        # counter-instrument (Byron/Dresden's 2021 dates, reversed by IL CEJA
        # 2021-09-15 — after the 2020-vintage cutoff) is countered instead of
        # false-retiring a running plant. Verification-only: the confirmed-
        # EXIT channel above keeps its information gate untouched, so this
        # can suppress a never-executed exit but never inject one.
        reversal_as_of = confirmed_registry_as_of
        if getattr(config, "hindcast", False) and getattr(
            config, "hindcast_verified_announced_exits", False
        ):
            reversal_as_of = None
        # Fail-loud shares the confirmed channel's condition (same clean
        # partition, W2-E / G12): when confirmed_exits_enabled is off the
        # reversal channel keeps its warn-only degradation, preserving its
        # deliberate independence from the gate.
        announced_reversal_plants = load_announced_reversal_plants(
            iso,
            as_of=reversal_as_of,
            required=_confirmed_exits_active(config),
        )

    # capx D42 (2026-09-02): the FOSSIL owner-filed EIA-860 Schedule-3 dates,
    # GATED fossil_announced_exits_enabled — DEFAULT ON since 2026-09-03 (owner
    # ruling Q30 / capx D44); an explicit False loads nothing and restores the
    # pre-Q30 posture byte-identically — and forecast-mode only, like every
    # exogenous exit channel (which is why a BACKCAST is untouched by the flip). Read from the ACTIVE vintage snapshot — the
    # rule-13 vintage gate: a date is admissible only because it was on file
    # at the run's information cutoff. Under the verified posture
    # (hindcast_verified_announced_exits) the set is checked per unit against
    # the later in-repo vintages (a filed deferral / withdrawal is honored;
    # nothing injected or advanced) and reversal-registry plants are dropped.
    # The full audited disposition table is persisted on the first ledger
    # year so a finding reports the ex-ante and verified sets side by side.
    announced_fossil_exits: list = []
    announced_fossil_schedule: list[dict] = []
    if config.mode == "forecast" and getattr(
        config, "fossil_announced_exits_enabled", False
    ):
        _afx_table = announced_fossil_disposition_table(
            iso,
            verify=bool(
                getattr(config, "hindcast", False)
                and getattr(config, "hindcast_verified_announced_exits", False)
            ),
            reversed_plant_codes=announced_reversal_plants,
        )
        announced_fossil_exits = [
            r for r in _afx_table if r.disposition not in ("cancelled", "reversed")
        ]
        announced_fossil_schedule = announced_fossil_rows_as_records(_afx_table)
        logger.info(
            "capx D42 fossil announced dates armed: %d live row(s), %.0f MW, %s",
            len(announced_fossil_exits),
            sum(r.mw or 0.0 for r in announced_fossil_exits),
            (
                f"{min(r.exit_year for r in announced_fossil_exits)}-"
                f"{max(r.exit_year for r in announced_fossil_exits)}"
                if announced_fossil_exits
                else "n/a"
            ),
        )

    # FF-2A entry-stack state (both gates default-off ⇒ both None/absent,
    # byte-identical). The growth ladder (entry_rate_limits) tracks each
    # tech's PRIOR MAXIMUM annual build: seeded from the measured EIA-860
    # record at the run's vintage (trailing ENTRY_THROUGHPUT_WINDOW_YEARS
    # window — data.build_throughput.max_annual_build_gw_by_tech reads the active
    # vintage directory, so a 2020-vintage hindcast sees only what was
    # knowable at the cutoff) and raised as the model's own decisions land.
    # The pending-entry pipeline (entry_commissioning_lag) carries decided-
    # but-not-yet-commissioned builds across years (mutated in place by
    # evolve_fleet, the same seam pattern as the evolution-ledger events).
    entry_prior_max_gw: dict[str, float] | None = None
    if getattr(config, "entry_rate_limits", False):
        # Anchor on the RESOLVED horizon start (line ~505), not the raw
        # config field: ``ScenarioConfig.start_year`` defaults to None, so
        # ``config.start_year - 1`` raised TypeError for every config that did
        # not set an explicit horizon. That path was unreachable while
        # entry_rate_limits was default-off and became live when owner decision
        # D-2 armed it (2026-08-02) — a latent defect the arming exposed, not a
        # behaviour change. Configs that DO set start_year are unaffected: the
        # local is identical to config.start_year whenever the field is set.
        _seed_through = config.eia860_vintage_year or (start_year - 1)
        entry_prior_max_gw = max_annual_build_gw_by_tech(
            iso, _seed_through, ENTRY_THROUGHPUT_WINDOW_YEARS
        )
        logger.info(
            "entry growth-ladder seed (%s, through %d, %d-yr window): %s",
            iso,
            _seed_through,
            ENTRY_THROUGHPUT_WINDOW_YEARS,
            {t: round(v, 3) for t, v in sorted(entry_prior_max_gw.items())},
        )
    entry_pipeline: list[dict] | None = (
        [] if getattr(config, "entry_commissioning_lag", False) else None
    )

    # FFR-3F exit-throughput cap (exit_rate_limits, GATED default-off ⇒ None,
    # byte-identical). The EXIT half of the same queue the growth ladder above
    # bounds on the entry side, and seeded the same way: the measured EIA-860
    # record at the run's vintage (data.build_exit_throughput.max_annual_exit_gw
    # reads the active vintage directory, so a 2023-vintage hindcast sees only
    # deactivations knowable at the cutoff) × EXIT_THROUGHPUT_LIMIT_MULTIPLE.
    # Unlike the entry ladder this seed does NOT rise endogenously: the model's
    # own exits are not evidence about how fast an RTO can process
    # deactivations, so admitting them would let the cap bootstrap itself
    # (rule 13 — the seed must stay a measured external input, never a model
    # outcome fed back). An ISO with no measured deactivation in the window
    # carries NO cap (rule 25 neutral fallback), logged.
    exit_rate_cap_mw: float | None = None
    if getattr(config, "exit_rate_limits", False):
        _exit_seed_through = config.eia860_vintage_year or (start_year - 1)
        _exit_prior_max_gw = max_annual_exit_gw(
            iso, _exit_seed_through, EXIT_THROUGHPUT_WINDOW_YEARS
        )
        if _exit_prior_max_gw is None:
            logger.warning(
                "exit throughput cap (%s): seed UNRESOLVED for the %d-yr "
                "window through %d (no measured thermal deactivation, or the "
                "EIA-860 retired sheet is absent — see the reader's own log "
                "line for which) — NO cap applied (rule 25 neutral fallback). "
                "The arm is INERT this run; do not read it as a tested cap.",
                iso,
                EXIT_THROUGHPUT_WINDOW_YEARS,
                _exit_seed_through,
            )
        else:
            exit_rate_cap_mw = (
                EXIT_THROUGHPUT_LIMIT_MULTIPLE * _exit_prior_max_gw * 1000.0
            )
            logger.info(
                "exit throughput cap (%s, through %d, %d-yr window): measured "
                "max single-year deactivation %.3f GW × %.1f = %.0f MW/yr",
                iso,
                _exit_seed_through,
                EXIT_THROUGHPUT_WINDOW_YEARS,
                _exit_prior_max_gw,
                EXIT_THROUGHPUT_LIMIT_MULTIPLE,
                exit_rate_cap_mw,
            )

    # Global cumulative deployment drives the Wright's-Law learning curves.
    # It starts from the reference-year installed base and advances one year
    # of worldwide deployment (plus this ISO's local builds) every year.
    cumulative = CumulativeDeployment.initial()

    # Cross-year LP warm-start holder for the forecast horizon (plan §7 H-3,
    # owner decision D-9). Each solved year hands its optimal basis to the next
    # year's P0 through this single-element list. ``None`` — the default, and
    # every run that does not arm ``forecast_xyear_warmstart`` — keeps the
    # forecast cold-only and byte-identical: the shared solve core neither
    # applies nor exports a basis when the holder is None.
    #
    # The flag is threaded to ``run_energy_solve`` as BOTH the holder and the
    # explicit ``xyear_warmstart`` gate, so the forecast never reads
    # ``MARKET_SIM_WARMSTART_XYEAR`` (rule 24 [R-REGISTRY]: the calibration
    # CLIs default that env var ON, and it must not silently reach the forecast
    # trajectory). Safe only because wave 4C made the economic retirement screen
    # basis-independent — see docs/cross-year-warmstart.md.
    forecast_xyear_cache: list | None = [] if config.forecast_xyear_warmstart else None

    # Last year whose LP actually solved. In a capacity hindcast the 2022
    # bridge (plan §1.1) is evolved but never solved, so the year after it
    # keeps consuming the last solved year's prior_results and drivers.
    # T1-FF Arm R given-weather posture (FH-1, hindcast-forward plan §2.1):
    # ``wx_config`` is the weather-transient view of the run config used ONLY
    # at the demand-scaling call sites below. Under
    # ``crossover_solve_year_weather`` each solved forward year rebinds the
    # weather base (``base_demand``, ``wind_cf``/``solar_cf``) to its own year
    # and points ``wx_config.weather_year`` at it, so ``_scale_demand`` spans
    # zero years — the same transient-``replace`` pattern as ``fleet_config``
    # below: the run's recorded config and cache key are never mutated. At the
    # default (posture off) ``wx_config`` IS ``config`` and every path is
    # byte-identical.
    wx_config = config
    loaded_weather_year = config.weather_year
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
        # T1-X crossover (FF-0E, plan §2.2): a GENUINE crossover SOLVES its
        # forward years (>= 2026) as forecast-mode years, so 2026 — a plain-
        # hindcast quarantine bridge year — is un-bridged there. Rule-22-legal:
        # a forecast solve of 2026+ consumes no measured H1-2026 actuals (the
        # measured overlays are all skipped for crossover forward years).
        #
        # The un-bridging is SCOPED to that case (FFR-3U), not applied to any
        # year at/above ``crossover_forward_year``: a T1-FF full-forward
        # hindcast points the boundary at its OWN base year, so the un-scoped
        # test made every year of a base-2021 window a "forward year" and
        # solved 2022 — a validation-tier holdout — with its measured data
        # read (FFR-3Q §2.2, owner Addendum L). One definition, shared with the
        # harness guard: ``is_hindcast_bridge_year``.
        is_bridge = is_hindcast_bridge_year(
            year,
            hindcast=config.hindcast,
            crossover_forward_year=config.crossover_forward_year,
            start_year=start_year,
        )
        driver_year = last_solved_year if is_bridge else year

        # FFR-5D capacity_screen_unified_lookahead (GATED, default OFF): swap
        # THIS entering year's own lookahead signal into prior_results before
        # any screen consumes it — evolve_fleet (retirement pipeline, CCS,
        # new entry) and the storage screen both read
        # prior_results.price_signal — so every screen for this entering year
        # sees ONE price object (rule 19), bridged and bridge-adjacent
        # entering years included. For a normal entering year this re-assigns
        # the identical array the seam already stored (a no-op); after a
        # bridge it replaces a signal priced for the bridge year with the one
        # priced for THIS year. Unarmed the dict is empty (byte-identical).
        if (
            getattr(config, "capacity_screen_unified_lookahead", False)
            and prior_results is not None
        ):
            _uni_sig = unified_signals.get(year)
            if _uni_sig is not None:
                prior_results.price_signal = _uni_sig
        # D11-R: rebind THIS entering year's own margin-exhaustion walk (the
        # same per-entering-year pattern as the unified-signal swap above —
        # after a bridge the walk stored for next_year is the wrong entering
        # year's instrument). Unarmed the dict is empty (byte-identical).
        if (
            getattr(config, "entry_margin_exhaustion", False)
            and prior_results is not None
        ):
            prior_results.entry_reprice = entry_walks.get(year)
        # D12: rebind THIS entering year's own forward reserve leg (same
        # per-entering-year pattern — after a bridge the adder stored for
        # next_year prices the wrong entering year's scarcity). Unarmed the
        # dict is empty (byte-identical).
        if (
            getattr(config, "entry_forward_reserve_leg", False)
            and prior_results is not None
        ):
            prior_results.entry_reserve_price_signal = entry_reserve_adders.get(year)

        # T1-FF Arm R given-weather rebind (FH-1, hindcast-forward plan §2.1):
        # a solved forward year re-seeds the weather base from ITSELF — the
        # solve year's demand profile and renewable CF — so the forward stack
        # (growth-scaled demand, CF × evolving capacity) runs on that year's
        # own weather with a zero-year growth span. The evolving capacity
        # state (wind_cap / solar_cap) is untouched: only the resource shapes
        # rebind. A bridge year never rebinds (its data is never read, rule
        # 22); it keeps the last solved year's base, grown forward by
        # ``wx_config``. Field validation guarantees this posture only exists
        # on a full-forward hindcast, so every other run skips this block.
        if (
            config.crossover_solve_year_weather
            and not is_bridge
            and year != loaded_weather_year
        ):
            base_demand = load_demand(
                iso,
                year,
                iso_config,
                td_loss_factor=config.td_loss_factor,
                include_interchange=not import_generators,
                strict_demand_profile=config.strict_demand_profile,
                ercot_tie_zonal_interchange=config.ercot_tie_zonal_interchange,
            )
            _wx_wind_cf, _, _wx_solar_cf, _ = load_renewable_profiles(
                iso, year, iso_config, config
            )
            if config.hours < base_demand.shape[1]:
                base_demand = base_demand[:, : config.hours]
                _wx_wind_cf = _wx_wind_cf[:, : config.hours]
                _wx_solar_cf = _wx_solar_cf[:, : config.hours]
            wind_cf, solar_cf = _wx_wind_cf, _wx_solar_cf
            wx_config = config.with_overrides(weather_year=year)
            loaded_weather_year = year
            logger.info(
                "year %d: T1-FF Arm R given-weather rebind -- demand profile "
                "and renewable CF re-seeded from weather year %d",
                year,
                year,
            )

        # The entering year's demand is deterministically known before the
        # fleet evolves (_scale_demand is pure config arithmetic), so the
        # capacity screens' peak-anchored mechanisms -- the retirement
        # reliability floor and the reserve-margin backstop -- test the
        # current year's known peak instead of lagging it by a full year
        # (capacity-economics plan 2026-07 §2.3 component 1: an off-by-one
        # deletion, not foresight). The price-driven screens still see only
        # prior-year outcomes (one-pass, rule 10).
        #
        # The additive load layers — the data-center flat block (G-34) plus the
        # FF-G4 electrification end-use layers (heat_pump/ev) — are folded in
        # immediately after _scale_demand and before peak is taken, so every
        # peak-anchored capacity screen (retirement floor, reserve-margin
        # backstop) sees the reshaped load for free. When on, add_load_layers
        # RELOCATES each layer's energy (jointly energy-invariant: the total
        # growth rate is DC- and electrification-inclusive, FF-1C/FF-G4) onto
        # the layer's own shape rather than double-counting it. Forecast-mode-
        # only; with every layer off/unsourced => same array object,
        # byte-identical.
        #
        # capx D76 (GATED ``capacity_screen_peak_measured_hindcast``, default
        # OFF). The growth path above is the RIGHT construction for a forecast
        # year and the WRONG one for a hindcast year: with ``weather_year``
        # 2024 (2025 on a crossover) and no per-solve-year weather rebind,
        # ``_scale_demand`` DE-GROWS the weather year's measured load back
        # across the span, so every non-weather hindcast year hands the screens
        # a synthesized peak while the LP below dispatches the measured one
        # (FINDING-capx-d76-2026-09-06.md §2: −23.3 % to +15.4 % across the six
        # ISOs). Armed, the seam peak is the year's OWN measured peak, from the
        # same ``_hindcast_measured_demand`` array the LP takes below -- it
        # REPLACES the de-grown peak, it does not stack on it (rule 19
        # [R-ONE-MECH]), and one load is performed per year exactly as before.
        # The predicate is the LP's own, so a FORECAST year -- which has no
        # measured load and for which growth IS the methodology (rule 13
        # [R-MEASURED]) -- and a crossover FORWARD year both keep the growth
        # path, and every unarmed run is byte-identical.
        screen_measured_demand: np.ndarray | None = None
        if (
            config.capacity_screen_peak_measured_hindcast
            and config.hindcast
            and not config.is_crossover_forward_year(year)
        ):
            screen_measured_demand = _hindcast_measured_demand(
                config, iso, iso_config, year, import_generators
            )
            year_demand = screen_measured_demand
        else:
            year_demand = _scale_demand(base_demand, wx_config, year)
            year_demand = add_load_layers(year_demand, config, iso, year, zone_names)
        peak_demand = float(year_demand.sum(axis=0).max())

        # CR-1 sloped capacity demand-curve reserve position (default-off gate).
        # Accredited firm capacity ÷ the shared adequacy requirement on the
        # ENTERING fleet, computed ONCE per year and threaded verbatim into all
        # three capacity screens -- retirement + thermal entry (via evolve_fleet)
        # and storage entry (below) -- so every screen prices adequacy off one
        # requirement and one basis (rule 19). None (gate off, base year with no
        # fleet, or no prior pools) keeps the fixed net-CONE price and is
        # byte-identical to the pre-CR-1 path. The gate resolves PER ISO
        # (RC-1B/RC-1A: capacity_market_clearing_by_iso row when present, else
        # the scalar) so a probe arm — e.g. run_capacity_hindcast.py
        # --capacity-market-clearing, which sets ONLY the by-ISO row — actually
        # computes the position; the scalar-only check here made that arm a
        # silent no-op.
        curve_reserve_position: float | None = None
        if (
            resolve_capacity_market_clearing(config, iso)
            and fleet is not None
            and prior_results is not None
        ):
            curve_reserve_position = capacity_reserve_position(
                fleet,
                float(prior_results.get("wind_cap_mw", 0.0) or 0.0),
                float(prior_results.get("solar_cap_mw", 0.0) or 0.0),
                float(prior_results.get("storage_firm_mw", 0.0) or 0.0),
                config,
                iso,
                peak_demand,
                year,
            )

        # capx D59 (locality_capacity_curves, GATED default-OFF): the NYISO
        # LOCALITY positions and prices, computed ONCE per year on the SAME
        # entering fleet as the NYCA position above (rule 19 — the two
        # positions the §5.15.2 settlement compares are contemporaneous) and
        # threaded verbatim into the retirement, thermal-entry and storage
        # screens. Empty (gate off / not NYISO / base year) ⇒ every screen
        # receives None and is byte-identical. The ICAP census uses the LP's
        # own zonal renewable nameplate and the storage fleet by zone, never a
        # load-share split (DESIGN §2.2).
        locality_positions: dict = {}
        locality_prices: dict[str, float] = {}
        locality_cost_ratio: dict[str, float] = {}
        if (
            locality_capacity_curves_armed(config, iso)
            and fleet is not None
            and prior_results is not None
        ):
            _storage_by_zone: dict[str, float] = {}
            for _su in storage_units:
                _storage_by_zone[_su.zone] = _storage_by_zone.get(
                    _su.zone, 0.0
                ) + float(_su.power_cap_mw)
            locality_positions = locality_capacity_positions(
                iso,
                year,
                fleet,
                config,
                wind_pool_by_zone={
                    z: float(wind_cap[i]) for i, z in enumerate(zone_names)
                },
                solar_pool_by_zone={
                    z: float(solar_cap[i]) for i, z in enumerate(zone_names)
                },
                storage_power_by_zone=_storage_by_zone,
                locality_peak_by_zone={
                    z.name: float(peak_demand) * float(z.load_share)
                    for z in iso_config.zones
                },
            )
            locality_prices = locality_prices_by_zone(locality_positions)
            for _loc, _pos in locality_positions.items():
                _ratio = resolve_locality_gross_cone_ratio(iso, _loc, year)
                if _ratio is not None:
                    for _z in _pos.zones or ():
                        locality_cost_ratio[_z] = float(_ratio)

        # capx D52 observability (additive ledger fields, decision-neutral and
        # cache-key-neutral — nothing reads them back): the capacity-screen
        # SEAM peak this block's position and evolve_fleet's floor/backstop
        # consume, the requirement resolved on it, the ENTERING accredited
        # firm the screens price (the same ledger + pools the position uses),
        # and their ratio on the ISO's curve convention — written whether or
        # not the clearing gate is on. The ledger's ``peak_demand_mw`` /
        # ``adequacy_requirement_mw`` below are re-derived from the LP's own
        # (in a hindcast: measured) load, so in every hindcast year that is not
        # the weather year they are NOT the values the screens saw; D45-R had
        # to back the screens' position out of the curve-ON ledger against a
        # class-EFORd reconstruction (PREDECL-capx-d52-2026-09-04.md §1).
        screen_peak_demand: float = peak_demand
        screen_requirement_mw: float | None = None
        screen_entering_firm_mw: float | None = None
        screen_reserve_position: float | None = None
        if fleet is not None and prior_results is not None and peak_demand > 0.0:
            screen_requirement_mw = resolve_adequacy_requirement_mw(
                config, iso, peak_demand, year
            )
            screen_entering_firm_mw = accredited_firm_capacity_mw(
                fleet,
                float(prior_results.get("wind_cap_mw", 0.0) or 0.0),
                float(prior_results.get("solar_cap_mw", 0.0) or 0.0),
                float(prior_results.get("storage_firm_mw", 0.0) or 0.0),
                iso=iso,
                peak_demand_mw=peak_demand,
                elcc_curves_enabled=config.renewable_elcc_curves,
                year=year,
                nqc_curves_enabled=config.caiso_nqc_accreditation,
                config=config,
                accreditation_year=year,
            )
            if screen_requirement_mw > 0.0:
                screen_reserve_position = curve_convention_position(
                    config, iso, screen_entering_firm_mw / screen_requirement_mw
                )
        # capx D59 ledger block (additive, decision-neutral, cache-key-neutral):
        # per representable locality the ICAP census terms, requirement,
        # position, locality curve price, the NYCA seam price and the §5.15.2
        # settled price — written whenever the gate is armed; [] otherwise.
        _nyca_price_kw_yr = (
            MARKET_DESIGN.get(iso, DEFAULT_MARKET_DESIGN).capacity_price_per_firm_mw_yr(
                config, curve_reserve_position, iso=iso, year=year
            )
            / 1000.0
            if locality_positions
            else None
        )
        locality_ledger_rows = []
        for _loc, _pos in locality_positions.items():
            _row = _pos.as_ledger_row()
            _row["nyca_price_per_kw_yr"] = round(float(_nyca_price_kw_yr), 4)
            _row["settled_price_per_kw_yr"] = round(
                max(
                    float(_nyca_price_kw_yr),
                    (
                        _row["price_per_kw_yr"]
                        if _row["price_per_kw_yr"] is not None
                        else 0.0
                    ),
                ),
                4,
            )
            _row["gross_cone_ratio"] = resolve_locality_gross_cone_ratio(
                iso, _loc, year
            )
            _row["below_requirement"] = bool(_pos.position < 1.0)
            locality_ledger_rows.append(_row)
        screen_ledger_fields = dict(
            locality_capacity=locality_ledger_rows,
            screen_peak_demand_mw=round(float(screen_peak_demand), 3),
            screen_adequacy_requirement_mw=(
                round(float(screen_requirement_mw), 3)
                if screen_requirement_mw is not None
                else None
            ),
            screen_entering_firm_mw=(
                round(float(screen_entering_firm_mw), 3)
                if screen_entering_firm_mw is not None
                else None
            ),
            screen_reserve_position=(
                round(float(screen_reserve_position), 6)
                if screen_reserve_position is not None
                else None
            ),
        )

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
                announced_fossil_exits=announced_fossil_exits,
            )
            # First year has no evolution: the ledger records the base fleet
            # snapshot only (fleet_by_fuel before == after, no events).
            base_totals = fleet_totals_by_fuel(fleet)
            evo_events["fleet_by_fuel_before"] = base_totals
            evo_events["fleet_by_fuel_after"] = base_totals
            if announced_fossil_schedule:
                # capx D42 audit record (first ledger year only): every dated
                # row with its disposition, incl. the cancelled/reversed rows
                # the channel never applies.
                evo_events["announced_fossil_schedule"] = announced_fossil_schedule
        else:
            # The RPS shadow price from the prior year's dispatch raises the
            # expected revenue of clean technologies in the new-entry screen.
            # Scalar (legacy row) or per-zone vector (K-row grain, FFR-7B
            # Arm 2 — an ndarray has no truth value, so test ndim, not
            # truthiness).
            prior_rps_shadow = 0.0
            prior_clean_by_fuel = None
            if prior_results is not None:
                _prior_rs = prior_results.get("rps_shadow_price")
                if _prior_rs is not None and (np.ndim(_prior_rs) > 0 or _prior_rs):
                    prior_rps_shadow = _prior_rs
                # Clean-tier per-(fuel, zone) credits (FFR-7B Arm 3) — None
                # off the family, byte-identical.
                prior_clean_by_fuel = prior_results.get("clean_attribute_price_by_fuel")
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
                clean_attribute_price_by_fuel=prior_clean_by_fuel,
                cumulative=cumulative,
                gas_price_per_mmbtu=gas_price_year,
                carbon_price=carbon_price_year,
                events=evo_events,
                confirmed_exits=confirmed_exits,
                peak_demand_next=peak_demand,
                announced_reversal_plants=announced_reversal_plants,
                announced_fossil_exits=announced_fossil_exits,
                reserve_position=curve_reserve_position,
                entry_rate_caps_mw=(
                    {
                        t: ENTRY_GROWTH_LIMIT_MULTIPLE * gw * 1000.0
                        for t, gw in entry_prior_max_gw.items()
                    }
                    if entry_prior_max_gw is not None
                    else None
                ),
                entry_pipeline=entry_pipeline,
                exit_rate_cap_mw=exit_rate_cap_mw,
                locality_prices_by_zone=(locality_prices or None),
                locality_cost_ratio_by_zone=(locality_cost_ratio or None),
            )
            # Growth-ladder update (entry_rate_limits): this year's decision-
            # grain builds raise the prior max, so a tech building at its
            # ladder cap doubles its deliverable throughput next year — the
            # ReEDS relative-growth dynamic on the measured seed.
            if entry_prior_max_gw is not None:
                for t, mw in (evo_events.get("entry_decided_mw_by_tech") or {}).items():
                    # Only techs with a measured seed carry a ladder; an
                    # unseeded tech stays uncapped (rule 25 neutral fallback)
                    # rather than acquiring a cap from its own first build.
                    if t in entry_prior_max_gw and mw / 1000.0 > entry_prior_max_gw[t]:
                        entry_prior_max_gw[t] = mw / 1000.0
            # Persist the reliability floor's attribution log next to the
            # per-year results parquet (rule 20 analogue: floor-retained MW
            # must be measurable per run, not argued). Written every evolved
            # year -- an empty list is the affirmative "floor did not bind".
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
            # capx D57 (DESIGN-capx-d54 §3.5 / §4.4): when the supply-clearing
            # gate is on, evolve_fleet's retirement screen cleared the
            # sell-offer stack this year and wrote the ledger block; storage
            # entry is a PRICE TAKER at that clearing price through the same
            # ``reserve_position`` slot (a pre-priced object — one seam, rule
            # 19). Absent (gate off, or no screen ran) ⇒ the census position,
            # byte-identically.
            storage_reserve_position: object = curve_reserve_position
            _cc = evo_events.get("capacity_clearing")
            if _cc:
                storage_reserve_position = ClearedCapacityPrice(
                    price_per_firm_mw_yr=float(_cc["price_per_firm_mw_yr"]),
                    cleared_position=float(_cc["cleared_position"]),
                    census_position=float(_cc["census_position"]),
                )
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
                reserve_position=storage_reserve_position,
                locality_prices_by_zone=(locality_prices or None),
                # D11-R: the SAME walk state the thermal screen just walked
                # (evolve_fleet step 5), so this year's thermal tranches are
                # already in the storage walk's starting signal. None
                # unarmed (byte-identical).
                entry_reprice=prior_results.get("entry_reprice"),
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
                    "%s %d: storage vintage ramp applied -- %d units with mid-year COD",
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
        #
        # capx D83: "no dispatch fields" is a statement about the LP, NEVER
        # about the fleet. ``evolve_fleet`` has already run above, so every
        # FLEET-STATE / accreditation-trail quantity a solved year records
        # exists here too -- ``wind_cap`` / ``solar_cap`` were grown IN PLACE by
        # this year's own renewable additions a few lines up, ``storage_units``
        # is post-entry, ``fleet`` is post-evolution, and
        # ``curve_reserve_position`` was computed on the seam peak. Writing this
        # dict by hand instead of sharing the solved writer's field list
        # silently dropped EIGHT of them, which made a bridge year the one year
        # whose capacity screen was not reproducible from its own record: the
        # screens consumed those pools (they are inside
        # ``screen_entering_firm_mw`` below) and the ledger did not say so, so
        # D75-R had to reconstruct them by hand -- twice (D75 §6 item 3,
        # re-raised as FINDING-capx-d75r §6 item 1). They are restored below
        # with the IDENTICAL expressions the solved writer uses, and the two key
        # sets are held equal by
        # ``tests/unit/results/test_bridge_ledger_field_parity.py`` so neither
        # writer can gain or lose a field without the other.
        #
        # ``peak_demand_mw`` / ``adequacy_requirement_mw`` / ``reserve_margin``
        # / ``rps_dual`` stay None, and that is FAITHFUL rather than a second
        # gap: ``peak_demand`` is RE-DERIVED from the LP's own load below this
        # branch, so a bridge year has no LP peak; the requirement and the
        # margin are defined on that peak, and the dual is an LP dual. The SEAM
        # peak the screens actually consumed, and the requirement resolved on
        # it, are already recorded by ``screen_ledger_fields`` (capx D52) --
        # which is also why the credits below are resolved at ``peak_demand``,
        # the seam peak: that is the basis the year's screens really applied.
        if is_bridge:
            _ledger = dict(evo_events)
            _bridge_wind_pool_mw = float(np.sum(wind_cap))
            _bridge_solar_pool_mw = float(np.sum(solar_cap))
            _ledger.update(
                iso=iso,
                year=year,
                mode=config.mode,
                hindcast=True,
                bridge=True,
                peak_demand_mw=None,
                reserve_margin=None,
                rps_dual=None,
                adequacy_requirement_mw=None,
                # The model's dispatched conventional-hydro NAMEPLATE and the
                # same resources at the ISO's published accreditation -- the
                # documented companion pair (FFR-3B). Neither is LP-derived,
                # and neither costs a new read: ``_hydro_firm_mw`` calls
                # ``modelled_hydro_nameplate_mw`` itself, which is cached per
                # ``(iso, year)`` and was already invoked for this year by the
                # screens' own ``accredited_firm_capacity_mw`` call above.
                firm_clean_mw=round(
                    float(
                        modelled_hydro_nameplate_mw(iso, year)
                        + sum(
                            g.pmax_mw for g in fleet if g.fuel_type in _FIRM_CLEAN_FUELS
                        )
                    ),
                    3,
                ),
                firm_clean_accredited_mw=round(
                    float(_hydro_firm_mw(fleet, iso, year)), 3
                ),
                capacity_reserve_position=(
                    round(float(curve_reserve_position), 6)
                    if curve_reserve_position is not None
                    else None
                ),
                # capx D52: the seam quantities the bridge year's screens
                # consumed (the bridge evolves against the seam peak even
                # though it never solves).
                **screen_ledger_fields,
                # Accreditation trail (CR-3.1), same fields and same resolvers
                # as the solved writer: pool nameplates, the credit each VRE
                # class actually earned on this year's basis, and the storage
                # fleet's power / pre-dilution accredited MW.
                wind_cap_mw=round(_bridge_wind_pool_mw, 3),
                solar_cap_mw=round(_bridge_solar_pool_mw, 3),
                renewable_credit_applied={
                    fuel: round(credit, 6)
                    for fuel, credit in renewable_credits_applied(
                        fleet,
                        _bridge_wind_pool_mw,
                        _bridge_solar_pool_mw,
                        iso,
                        peak_demand_mw=peak_demand,
                        elcc_curves_enabled=config.renewable_elcc_curves,
                        nqc_curves_enabled=config.caiso_nqc_accreditation,
                        config=config,
                        accreditation_year=year,
                    ).items()
                },
                storage_power_mw=round(
                    float(sum(u.power_cap_mw for u in storage_units)), 3
                ),
                # The SAME expression the solved writer's ``prior_results``
                # carries (one storage-accreditation resolver, rule 19); the
                # bridge cannot read it off ``prior_results``, which is still
                # pointed at the last SOLVED year by design.
                storage_firm_mw=round(
                    float(
                        sum(
                            u.power_cap_mw
                            * storage_accreditation_credit(
                                u.energy_cap_mwh / u.power_cap_mw
                                if u.power_cap_mw > 0
                                else 0.0,
                                iso,
                                config,
                                u.tech_name,
                            )
                            for u in storage_units
                        )
                    ),
                    3,
                ),
                storage_additions=_storage_additions_since(
                    storage_units, prior_storage_ids, zone_names
                ),
                solve_counts={"P0": 0, "P1": 0, "P2": 0},
            )
            _lp = ledger_path(get_cache_path(iso, cache_key, year))
            write_ledger(_lp, _ledger)
            logger.info(
                "year %d: capacity-hindcast BRIDGE -- evolved, not solved (ledger %s)",
                year,
                _lp.name,
            )
            continue

        # Capacity hindcast (plan §1.3): dispatch the realized year's demand
        # profile with NO growth scaling, so capacity logic is isolated from
        # demand-forecast error. A plain forecast keeps the once-loaded
        # weather-year base grown by _scale_demand below.
        # T1-X crossover forward years (FF-0E, plan §2.2) take the forecast
        # branch instead: growth-scaled demand from the weather-year base (the
        # harness pins weather_year to the last realized year), never the
        # measured per-year load loader.
        if config.hindcast and not config.is_crossover_forward_year(year):
            # capx D76: when the gate is armed the seam above already loaded
            # THIS array under the identical predicate, so reuse it -- an armed
            # hindcast year performs exactly ONE measured load, as it always
            # has, and the screens and the LP are guaranteed the same object
            # rather than two equal-by-inspection reads (rule 19).
            year_base_demand = (
                screen_measured_demand
                if screen_measured_demand is not None
                else _hindcast_measured_demand(
                    config, iso, iso_config, year, import_generators
                )
            )
        else:
            year_base_demand = base_demand

        # Assemble this year's LP-ready dispatch fleet from the persistent
        # ``fleet``: coal take-or-pay pricing via CAMPD per-plant fuel
        # fractions when ``campd_bins`` is active (the non-CAMPD fallback
        # passes coal through unsplit, optionally gas-tranched) -- plus
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
            else config.with_overrides(historic_outage_overlay=outage_overlay)
        )
        # NET-load window series for the commitment floors
        # (config.commitment_floor_window_netload, SPP-66, owner ruling "Shared
        # gate" 2026-09-20). Built ONLY when the gate is armed, so an unarmed
        # run performs exactly the array work it did before and every committed
        # bundle in every ISO is byte-identical; unarmed, the floor composer
        # receives None and keeps its system-load window.
        #
        # Same construction as the six existing net-load sites in this file --
        # demand less AVAILABLE wind/solar -- so no new scalar is introduced
        # (rules 21 [R-DOF] / 24 [R-REGISTRY]). It is the MODEL's own
        # capacity x CF, never measured VRE output, so it regenerates for a
        # forecast year off the evolved fleet (rule 13 [R-MEASURED]).
        # ``solar_cf``, not ``year_solar_cf``: the latter is first assigned well
        # below this point, and three of the six existing sites likewise read
        # the un-derated series.
        _floor_netload_shape = None
        if getattr(config, "commitment_floor_window_netload", False):
            _floor_netload_shape = (
                year_base_demand.sum(axis=0)
                - (np.asarray(wind_cap, dtype=float)[:, None] * wind_cf).sum(axis=0)
                - (np.asarray(solar_cap, dtype=float)[:, None] * solar_cf).sum(axis=0)
            )
        fleet_arrays = generators_to_fleet_arrays(
            dispatch_fleet,
            zone_names,
            hours=config.hours,
            iso=iso,
            config=fleet_config,
            load_shape=year_base_demand.sum(axis=0),
            netload_shape=_floor_netload_shape,
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
        if config.hindcast and not config.is_crossover_forward_year(year):
            # Measured/pinned historical load governs the hindcast LP; the
            # forecast-only load layers are never added on top of measured
            # actuals (and datacenter_load_path/electrification_path are "off"
            # in any hindcast anyway). A crossover forward year (>= boundary)
            # falls to the forecast branch below — growth-scaled demand, no
            # measured overlay (FF-0E §2.2).
            year_demand = year_base_demand
        else:
            # Same joint layer relocation as the capacity-screen seam above
            # (G-34 + FF-G4), applied on the forecast branch so the LP and
            # results path see the identical demand the screens saw. All
            # layers off/unsourced => same array, byte-identical.
            year_demand = _scale_demand(base_demand, wx_config, year)
            year_demand = add_load_layers(year_demand, config, iso, year, zone_names)
        peak_demand = float(year_demand.sum(axis=0).max())

        # Net-load-indexed ST_GAS + CT_PEAKER reliability-drag min-gen floors --
        # the single shared gate-and-log wrapper both orchestrators call
        # (fleet.apply_netload_drag_floors, orchestrator-unification Stage 6).
        # Gates internally on gas_st_netload_drag / ct_netload_drag (default
        # off -- byte-identical when unset); net-load uses the LP-served
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
        # NEISO winter gas-availability cold-snap derate -- the shared
        # gate-and-log wrapper (fleet.apply_neiso_coldsnap_derate,
        # orchestrator-unification Stage 6: previously wired only in the
        # backcast orchestrator, the plan's §2.2 accidental-drift row).
        # Gated on neiso_gas_coldsnap_derate (default off -- byte-identical);
        # must run before the reserve-co-opt inputs are assembled so the
        # shared-headroom RHS sees the derated availability.
        apply_neiso_coldsnap_derate(fleet_arrays, config, iso, year)
        # Correlated cold-event forced-outage derate (FF-1B; gate-and-log
        # wrapper data/outages.apply_correlated_outage_derate). Gated on
        # correlated_forced_outage (default off -- byte-identical) and
        # forecast/hindcast mode only (backcast carries the measured CAMPD
        # outage overlays instead -- charter D.5). Must run here, before the
        # LP bounds and the post-solve ORDC reserve read availability, so a
        # deep-cold event thins both the dispatchable stack and the ORDC
        # point reserve (charter D.6: the mean-availability channel).
        apply_correlated_outage_derate(fleet_arrays, config, iso, year)

        # NYISO Long Island local self-supply floor (orchestrator-unification
        # Stage 6, the plan's §2.2 accidental-drift row): force the cable-
        # islanded LI pocket to meet a fraction of its own load with in-zone
        # thermal generation rather than importing cheap NYC gas
        # (interchange.nyiso.inject_nyiso_local_selfsupply). NYISO-only; gated
        # on nyiso_local_selfsupply (default off -- byte-identical when unset).
        #
        # WHY IT IS HERE AND NOT BACKCAST-ONLY: the LMIC / local-reliability
        # rule this proxies is NYISO MARKET DESIGN, not a measured overlay --
        # it scales with load and responds to changed conditions, so it is
        # forward-reproducible (rule 13 [R-MEASURED]) and its D-5 registry row
        # is mode="both", declared=False ("LMIC market-design rule --
        # mode-independent by intent"). It was wired only in the backcast
        # orchestrator, so D-5 read it as an undeclared backcast-only
        # difference and FAILed on every NYISO keeper through nyiso-100.
        # Placed after the availability derates above so the floor's
        # "never demand more than the in-zone fleet can supply" clamp sees
        # final availability -- the same order the backcast orchestrator uses.
        if getattr(config, "nyiso_local_selfsupply", False):
            from market_sim.model.transmission import inject_nyiso_local_selfsupply

            # Zone-K LCR/TSL mechanism active (issue #1345): the published-limit
            # import cap owns Long_Island this run; skipping its floor entry
            # here keeps the two mechanisms from stacking (rule 19
            # [R-ONE-MECH]). Mirrors the backcast orchestrator exactly.
            _selfsupply_exclude = (
                frozenset({"Long_Island"})
                if getattr(config, "nyiso_li_lcr_tsl", False)
                else frozenset()
            )
            if inject_nyiso_local_selfsupply(
                fleet_arrays,
                iso,
                year_demand,
                zone_names,
                exclude_zones=_selfsupply_exclude,
            ):
                logger.info(
                    "%s %d: local self-supply floor applied to downstate "
                    "pocket(s) (LMIC / cable-islanded local reliability)",
                    iso,
                    year,
                )

        fuel_prices = resolve_fuel_prices(config, fleet_arrays, year)
        # Reprice CAMPD coal bins by plant fuel supply (mine-mouth
        # lignite vs PRB by rail); no-op for the legacy fleet.
        apply_coal_supply_pricing(fuel_prices, dispatch_fleet, config, year)
        carbon_price = resolve_carbon_price(config, year)
        # Partial-footprint carbon program (pjm-146 seam, SCN-WS1a G-C3): the
        # same gate and arithmetic as scripts/run_calibration.py's assemble_mc
        # call -- when the ISO's program maps membership per zone (today only
        # PJM's RGGI footprint) and the resolved adder is nonzero, the scalar
        # becomes the per-generator membership-weighted column
        # emission_rate[g] x m[g] x p_allowance. Whole-ISO programs and
        # program-less ISOs get the scalar back as the SAME object, so their
        # solves stay byte-identical (policy.cap_and_trade.carbon_mc_column).
        carbon_mc = carbon_mc_column(
            config, iso, year, carbon_price, fleet_arrays, zone_names
        )
        if carbon_mc is not carbon_price:
            logger.info(
                "%s %d: partial-footprint carbon adder -- %d/%d generators "
                "carry a nonzero membership-weighted allowance price",
                iso,
                year,
                int((np.asarray(carbon_mc) > 0).sum()),
                len(carbon_mc),
            )
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
            carbon_mc,
            config.nox_price,
            so2=(fleet_arrays.so2_rate, config.so2_price),
        )

        # The cache key names a config largely by OMISSION -- every registered
        # optional field sitting at its default is dropped from the hash -- so a
        # bundle on disk at this key is not proof that it was solved under this
        # config. capx D24 demonstrated two committed pairs at one key with
        # materially different postures (FINDING-capx-d24-cache-key-defect-
        # 2026-09-01.md §4). Option (c') of that finding, owner ruling Q20: the
        # stored config.yaml has to agree before the bundle is served. A
        # disagreement is a logged MISS naming the fields and a re-solve, never
        # an exception -- a run must not die because a stale bundle exists.
        _year_cached = is_cached(iso, cache_key, year)
        _cache_conflicts = (
            cache_config_disagreements(iso, cache_key, year, config)
            if _year_cached
            else []
        )
        if _cache_conflicts:
            logger.warning(
                "%s %d: REFUSING the cached bundle at key %s -- its stored "
                "config.yaml disagrees with this run's config on %d field(s): "
                "%s%s. Re-solving (capx D24 option (c'), owner ruling Q20).",
                iso,
                year,
                cache_key,
                len(_cache_conflicts),
                ", ".join(_cache_conflicts[:12]),
                " ..." if len(_cache_conflicts) > 12 else "",
            )
        if _year_cached and not _cache_conflicts:
            result = load_result(iso, cache_key, year)
            _t_cached = time.perf_counter()
            _total = _t_cached - year_start
            log_year_cached_timing(logger, year, total=_total)
        else:
            wind_mc, solar_mc = compute_dispatch_credits(config, year)
            if getattr(config, "wind_ptc_vintage_offers", False):
                # ERCOT-65 PTC vintage scoping -- D-5 forecast parity with the
                # backcast orchestrator's wind_mc seam: the flat -ira_ptc_wind
                # offer becomes the per-zone-month measured EIA-860 vintage
                # blend (policy.ira.wind_ptc_vintage_dispatch_offer; full
                # adjudication at the ScenarioConfig field). Falls back to
                # the flat offer when the share data is unavailable.
                from market_sim.policy.ira import wind_ptc_vintage_dispatch_offer

                _vintage_wind_mc = wind_ptc_vintage_dispatch_offer(
                    iso, year, zone_names, config, wind_cf.shape[1]
                )
                if _vintage_wind_mc is not None:
                    wind_mc = _vintage_wind_mc
            # Base marginal cost: the full variable cost above, then
            # exogenous EACs, then the coal take-or-pay tranche discount.
            # This is the generators' bid basis -- no startup-cost markup.
            mc_base = mc_cost.copy()
            # Exogenous EACs shift the cost vector: per-generator EACs
            # lower per-generator MC, wind/solar EACs lower their dispatch
            # adders, and the storage EAC credits discharge. The EAC is real
            # bidding behavior; it does not stack with the RPS shadow price
            # in capacity economics (each MWh sells one attribute, once).
            # Year-aware since W2-A: under federal_ces_enabled the per-unit
            # subtraction is max(legacy eac_price_*, premium × credit
            # fraction) for THIS year (policy/federal_ces.py) — applied here
            # once, pre-P0, and carried through P1 (one delivery channel;
            # no LP rows added).
            apply_eac_to_mc(mc_base, fleet_arrays, config, year)
            # Coal tranche 1 bids at VOM only (its fuel is sunk under the
            # take-or-pay contract); higher tranches pass through more fuel.
            # Under coal_offer_net_revenue_margin the CAMPD _mustrun band is
            # instead repriced to the measured net-margin form (ERCOT-137).
            apply_coal_tranches(
                mc_base,
                dispatch_fleet,
                fleet_arrays,
                fuel_fracs,
                fuel_prices,
                config,
                year=year,
            )
            # Gas-offer net-revenue margin (gas_offer_net_revenue_margin,
            # default off — forecast parity with the backcast orchestrator's
            # seam): gas tranche markups become fixed $/MWh margins at the
            # ISO's identification anchor; the physical burn keeps tracking
            # the forward gas path. Applies to the BID basis only, never to
            # mc_cost (the retirement screen's full variable cost above —
            # margins are offer components, not costs).
            apply_gas_offer_margin(mc_base, dispatch_fleet, fuel_prices, config)
            # MISO measured offer surface (miso_offer_surface_measured, default
            # off, MISO-gated — miso-151): forecast parity with the backcast
            # seam. SUBSUMES the margin the call above sets on MISO's above-base
            # gas tranches (rule 19 [R-ONE-MECH]) — never stacks. Its three
            # conditioning drivers (own-curve position, net-load percentile,
            # delivered gas) all exist forward, which is what makes the surface
            # rule-13 admissible rather than a backcast overlay.
            if getattr(config, "miso_offer_surface_measured", False) and iso == "MISO":
                from market_sim.data.fuel.trajectories import _gas_series

                _miso_surface_net_load = (
                    year_demand.sum(axis=0)
                    - (solar_cap[:, None] * solar_cf).sum(axis=0)
                    - (wind_cap[:, None] * wind_cf).sum(axis=0)
                )
                apply_miso_offer_surface(
                    mc_base,
                    dispatch_fleet,
                    _miso_surface_net_load,
                    _gas_series(config, year, mc_base.shape[1]),
                    config,
                )
            # miso-180 anchored SPREAD-ONLY dispersion graft
            # (miso_offer_spread_anchored, default off, MISO-gated): forecast
            # parity with the backcast seam — the above-anchor econ/peak
            # tranches are floored at the stack's own monthly anchor level
            # plus the measured eligible-book rise (shape, never level). The
            # measured G_ref seam hard-errors on a year with no measured gas
            # rows rather than silently substituting a forward curve; wiring
            # the forward trajectory through it is a deliberate future change.
            apply_miso_offer_spread_anchored(
                mc_base, dispatch_fleet, fleet_arrays, config, year
            )
            # CC committed-block measured offer level (cc_committed_offer_margin,
            # default off — ERCOT-139): the CC_REGULAR `_committed` tranche is
            # repriced from its band multiplier to the measured RT SCED curve
            # bottom as a fuel-invariant margin at the SHARED gas anchor. Bid
            # basis only, never mc_cost (the retirement screen's full variable
            # cost — a measured offer level is an offer component, not a cost).
            apply_cc_committed_offer_margin(
                mc_base, dispatch_fleet, fleet_arrays, config
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
            # backcast runs -- reference-price seams, firm import/export
            # floors, and the CAISO offer couplings -- every one gated by its
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
                # Audit FR-9 (fixed FFR-2A): the seam prices off the SAME
                # trajectory the ISO's own gas does. A T1-X/T1-FF crossover's
                # forward years resolve to crossover_forward_gas_path; every
                # other run resolves to config.gas_price_path, unchanged.
                # Before this the seam took gas_price_path unconditionally, so
                # a crossover forward year priced its imports off the realized
                # hindcast path (KeyError on "hindcast_realized", whose keys
                # stop at 2025) — a measured input reaching a forward year,
                # rule 13 [R-MEASURED].
                gas_scenario=resolve_gas_scenario_path(config, year),
                net_load=_interchange_net_load,
            )
            wind_eac, solar_eac, storage_eac = compute_eac_dispatch_credits(
                config, year
            )
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
                        "forecast net position -- %d node rows, annual band "
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
            # Statute-defined eligible-fuel set for the RPS row (FFR-7B Arm 1):
            # names beyond wind/solar add the matching thermal-block generator
            # columns (e.g. NYISO existing hydro, CAISO geothermal/biomass).
            rps_eligible_fuels = None
            # Pure-federal counterfactual (W2-A plan §5.3): with the federal
            # CES enabled AND federal_ces_replaces_state_rps, the state RPS
            # row is not built (rps_target stays None), so no RPS dual exists
            # and the premium is the only attribute mechanism. Moot for ERCOT
            # (all-zero STATE_RPS_FLOORS entry — no row either way); PJM DOES
            # carry a row (0.185→0.33 since the FF-1E-policy refresh), so the
            # suppression is live there (stale-comment fix, FFR-6B §5.4).
            # Per-state compliance-region grain (FFR-7B Arm 2 / FFR-6B E-1),
            # GATED miso_rps_compliance_regions — the FIELD default is OFF, but
            # MISO's ISOConfig.default_scenario_overrides ARMS it for the
            # forecast lane (owner decision D-26, sitting Addendum Y.4,
            # 2026-08-06; measured basis FFR-7B-2 §3.1). The three-leg gate is
            # _rps_region_grain_active — MISO-only (rule 25 [R-ISO-SCOPE]: the
            # four other RPS ISOs' single ISO-wide row is arithmetically exact
            # under free intra-ISO REC trade, FFR-6B §2.1, and stays
            # byte-identical) AND forecast-mode, so a backcast-mode MISO config
            # carrying the armed override still lands on the legacy row below.
            # When armed, the K per-region rows REPLACE the ISO-wide row
            # (rps_target stays None — one row family per phenomenon,
            # rule 19). The CES suppression above applies to the region rows
            # exactly as to the ISO-wide row: under a pure-federal
            # counterfactual no state row of either grain is built.
            # Clean-tier family (FFR-7B Arm 3): rides the Arm-2 machinery —
            # arming it without the compliance-region grain is a wiring
            # error, refused loudly. ARMED FOR THE MISO FORECAST LANE by
            # owner decision D-29 (sitting Addendum AK.8, 2026-08-11) through
            # MISO's ISOConfig.default_scenario_overrides, exactly as D-26
            # armed Arm 2 above — so a MISO forecast leg that passes no flag
            # builds BOTH families. Both former blockers are closed: the
            # §45U-vs-clean-dual composition by D-28 option A (and measured
            # moot — §45U dies after 2032 while MI cannot bind before 2035),
            # and the generator-column zone-mask defect by ARM3-FIX. The
            # forecast-mode leg of the gate is what keeps the armed override
            # off the backcast lane (see _rps_region_grain_active).
            rps_region_arrays = None
            clean_region_arrays = None
            if getattr(config, "miso_clean_tier_rows", False) and not getattr(
                config, "miso_rps_compliance_regions", False
            ):
                raise ValueError(
                    "miso_clean_tier_rows requires miso_rps_compliance_regions "
                    "— the clean-tier family rides the Arm-2 K-row machinery "
                    "(FFR-6B §6.2: the dependency is strict and one-directional)"
                )
            if config.rps_enabled and not federal_ces_suppresses_state_rps(config):
                # The CES suppression above covers the state CLEAN rows too
                # (FFR-6B §6.4): under a pure-federal counterfactual neither
                # family is built, or the counterfactual stops being pure.
                if _rps_region_grain_active(config, iso):
                    rps_region_arrays = build_rps_region_arrays(iso, year, zone_names)
                if rps_region_arrays is None:
                    rps_target = get_rps_target(iso, year)
                    rps_acp_price = get_rps_acp(iso)
                    rps_eligible_fuels = get_rps_eligible_fuels(iso)
            # Clean-tier family — MISO's state rows (Arm 3, gated exactly as
            # before) plus the federal CES TARGET row (SCN-WS2a: one region
            # spanning every load zone, credited by unit_credit_fractions,
            # escaping at the ACP; its dual is the endogenous federal EAC
            # price) plus the voluntary clean-demand row (SCN-WS3b: one
            # all-zone region whose RHS is a share of THIS year's demand,
            # escaping at the buyer's WTP ceiling — hence year_demand is
            # passed; off = byte-identical). ONE resolver, shared with the
            # prior_results mapping below, so a cached year maps its duals
            # onto the identical region list. None wherever none exists
            # (byte-identical).
            clean_region_arrays = _clean_region_arrays_for_year(
                config, iso, year, zone_names, fleet_arrays, zone_demand=year_demand
            )
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
                        "CAISO %d: solar deliverability derate (Lever D) -- "
                        "midday mean %.3f (≈ %.1f%% curtailment headroom)",
                        year,
                        float(np.mean(_sol_derate[mid])),
                        100.0 * (1.0 - float(np.mean(_sol_derate[mid]))),
                    )
            elif iso == "CAISO" and _endogenous_spill:
                logger.info(
                    "CAISO %d: endogenous solar spill -- full solar potential "
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
            # load_renewable_profiles under the same gate -- no
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
            # SPP wind curtailment ceiling (SPP-58), forecast leg: the same
            # per-(zone, hour) ceiling the backcast orchestrator applies
            # (scripts/run_calibration.py), computed from the FORECAST state so
            # the decile mapping regenerates as SPP wind builds out — which is
            # what makes the mechanism forward-native under rule 13
            # [R-MEASURED] rather than a backcast-only overlay. The matching
            # flat gross-up of the delivered basis happens in
            # load_renewable_profiles under the same gate (which also disarms
            # the oversupply allocation there, rule 19), so no double-count.
            # UNSET off the flag => byte-identical LP.
            if iso == "SPP" and getattr(config, "spp_curtailment_ceiling", False):
                from market_sim.config import paths as _spp_paths
                from market_sim.data.curtailment_share import spp_curtail_multipliers

                _spp_net_load = (
                    np.asarray(year_demand, dtype=float).sum(axis=0)
                    - (np.asarray(wind_cap, dtype=float)[:, None] * wind_cf).sum(axis=0)
                    - (np.asarray(solar_cap, dtype=float)[:, None] * year_solar_cf).sum(
                        axis=0
                    )
                )
                _spp_mult = spp_curtail_multipliers(
                    _spp_net_load,
                    list(zone_names),
                    depth_wind=float(getattr(config, "spp_curtail_depth_wind", 0.0)),
                    reference_dir=_spp_paths.RAW_DIR / "reference",
                )
                if _spp_mult is not None:
                    _wtx_mult = _spp_mult
            _wtx_spec_kwargs = (
                {
                    "wind_curtail_share": _wtx_mult[0],
                    "solar_curtail_share": _wtx_mult[1],
                }
                if _wtx_mult is not None
                else {}
            )
            # CAISO per-year SP15-pocket import caps (config.caiso_per_year_import_caps,
            # default off -- byte-identical no-op): swap links 4/5's TTC (baked
            # in at the static 2023 tightest-year value) to this solve year's
            # measured LCT import_cap before the LP reads it. Only the TTC
            # array needs recomputing per year; incidence and
            # link_bidirectional are topology-only and unaffected.
            year_ttc = ttc
            _year_iso_config = iso_config
            if iso == "CAISO" and getattr(config, "caiso_per_year_import_caps", False):
                _caiso_year_iso_config = apply_caiso_local_import_limits(
                    iso_config, iso, year
                )
                if _caiso_year_iso_config is not iso_config:
                    _year_iso_config = _caiso_year_iso_config
                    year_ttc = get_ttc_array(_caiso_year_iso_config.links)
            # Forward transmission-expansion channel (FF-G1): add the
            # cumulative in-service committed deltas to this solve year's link
            # TTCs / interface caps. apply_transmission_expansion returns the
            # SAME object when nothing applies (pre-COD years, zero-row
            # registry, flag off => _txexp_expansions empty and this block is
            # skipped), so the default path is byte-identical. Only the TTC
            # array — and, when an interface cap moved, the declared-limit
            # groups (corridor extension groups re-appended verbatim) — are
            # recomputed per year; incidence and link_bidirectional are
            # topology-order-only and unaffected.
            year_interface_groups = interface_groups
            if _txexp_expansions:
                _txexp_year_config = apply_transmission_expansion(
                    _year_iso_config, iso, year, _txexp_expansions
                )
                if _txexp_year_config is not _year_iso_config:
                    year_ttc = get_ttc_array(_txexp_year_config.links)
                    if (
                        _txexp_year_config.interface_limits
                        is not _year_iso_config.interface_limits
                    ):
                        year_interface_groups = (
                            build_interface_groups(
                                _txexp_year_config.links,
                                _txexp_year_config.interface_limits,
                            )
                            + interface_groups[_txexp_base_group_count:]
                        )
                    _txexp_links, _txexp_ifaces = cumulative_deltas(
                        _txexp_expansions, year
                    )
                    logger.info(
                        "%s %d: transmission-expansion deltas applied "
                        "(links %s; interfaces %s)",
                        iso,
                        year,
                        {f"{a}->{b}": round(v, 1) for (a, b), v in _txexp_links.items()}
                        or "none",
                        {
                            k: (round(f, 1), round(r, 1))
                            for k, (f, r) in _txexp_ifaces.items()
                        }
                        or "none",
                    )
            # NYISO locality LCR/TSL import caps (orchestrator-unification
            # Stage 6, same accidental-drift row as the self-supply floor
            # above): cap the NYC->Long_Island (Zone-K) and Lower_Hudson->NYC
            # (Zone-J) links at their PUBLISHED locality import limits in the
            # HB14-21 design-condition window. Both gated (default off --
            # byte-identical when unset) and NYISO-only; both are published
            # transmission limits that republish every capability year, so
            # they are forward-reproducible market design, not overlays.
            #
            # These travel WITH the self-supply floor and must never be split
            # from it: nyiso_li_lcr_tsl is precisely what excludes Long_Island
            # from that floor (rule 19 [R-ONE-MECH]). Wiring the floor into
            # this orchestrator without these caps would leave a forecast run
            # carrying the keeper's config with NEITHER mechanism on the
            # downstate pocket -- D-5 green with the real gap still open.
            if iso == "NYISO" and getattr(config, "nyiso_li_lcr_tsl", False):
                from market_sim.model.transmission import (
                    apply_nyiso_li_tsl_import_cap,
                )

                _li_n11 = bool(getattr(config, "nyiso_li_tsl_n11_security", False))
                year_ttc = apply_nyiso_li_tsl_import_cap(
                    year_ttc,
                    _year_iso_config,
                    iso,
                    year,
                    year_demand.shape[1],
                    n11_security_basis=_li_n11,
                )
                logger.info(
                    "%s %d: Zone-K LCR/TSL import cap on NYC->Long_Island "
                    "(HB14-21, published %s; replaces the "
                    "LI self-supply energy floor)",
                    iso,
                    year,
                    "N-1-1 transmission security limit"
                    if _li_n11
                    else "locality import limit",
                )
            if iso == "NYISO" and getattr(config, "nyiso_nyc_lcr_tsl", False):
                from market_sim.model.transmission import (
                    apply_nyiso_nyc_tsl_import_cap,
                )

                year_ttc = apply_nyiso_nyc_tsl_import_cap(
                    year_ttc, _year_iso_config, iso, year, year_demand.shape[1]
                )
                logger.info(
                    "%s %d: Zone-J LCR/TSL import cap on Lower_Hudson->NYC "
                    "(HB14-21, published NYC locality import limit; replaces "
                    "the 3,900 MW Dunwoodie-South energy-TTC estimate)",
                    iso,
                    year,
                )
            # Base dispatch kwargs + priced import-node band: the shared
            # pipeline assembly (orchestrator-unification Stage 2) -- the same
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
                interface_groups=year_interface_groups or None,
                # One-way links (MISO's RDT directional pair) floor their flow
                # at 0; all-True for every other ISO (byte-identical bounds).
                link_bidirectional=get_link_bidirectional_array(iso_config.links),
                # Priced RDT TCDC tiers (miso_rdt_tcdc): $/MWh on the tiered
                # one-way links; None (all links free) is byte-identical.
                link_flow_cost=get_link_flow_cost_array(iso_config.links),
                # Marginal loss fractions on the one-way Midwest loss pairs
                # (miso_zonal_loss_surface): forecast years resolve to the
                # pooled multi-year surface rows. UNSET off the flag, so the
                # forecast kwargs key set is unchanged (byte-identical).
                link_loss=(
                    build_miso_link_loss(
                        iso_config.links, iso, year, int(base_demand.shape[1])
                    )
                    if getattr(config, "miso_zonal_loss_surface", False)
                    else (
                        build_pjm_link_loss(
                            iso_config.links, iso, year, int(base_demand.shape[1])
                        )
                        if getattr(config, "pjm_zonal_loss_surface", False)
                        else (
                            build_caiso_link_loss(
                                iso_config.links, iso, year, int(base_demand.shape[1])
                            )
                            if getattr(config, "caiso_zonal_loss_surface", False)
                            else (
                                build_nyiso_link_loss(
                                    iso_config.links,
                                    iso,
                                    year,
                                    int(base_demand.shape[1]),
                                )
                                if getattr(config, "nyiso_zonal_loss_surface", False)
                                else UNSET
                            )
                        )
                    )
                ),
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
                # Omitted (UNSET) when no eligible set accompanies an active
                # row, so the dispatch-kwargs key set is unchanged wherever the
                # row is off or default (byte-identity; FFR-7B Arm 1).
                rps_eligible_fuels=(
                    rps_eligible_fuels if rps_eligible_fuels is not None else UNSET
                ),
                # K-row compliance-region grain (FFR-7B Arm 2): omitted
                # (UNSET) off the gate, so the dispatch-kwargs key set — and
                # with it every unarmed LP — is unchanged (byte-identity).
                rps_region_zone_mask=(
                    rps_region_arrays.eligible_zone_mask
                    if rps_region_arrays is not None
                    else UNSET
                ),
                rps_region_obligation_frac=(
                    rps_region_arrays.obligation_frac
                    if rps_region_arrays is not None
                    else UNSET
                ),
                rps_region_acp_price=(
                    rps_region_arrays.acp_price
                    if rps_region_arrays is not None
                    else UNSET
                ),
                # Clean-tier family (FFR-7B Arm 3): omitted (UNSET) off the
                # gate — byte-identity, same discipline as the RPS family.
                clean_region_zone_mask=(
                    clean_region_arrays.eligible_zone_mask
                    if clean_region_arrays is not None
                    else UNSET
                ),
                clean_region_obligation_frac=(
                    clean_region_arrays.obligation_frac
                    if clean_region_arrays is not None
                    else UNSET
                ),
                clean_region_acp_price=(
                    clean_region_arrays.acp_price
                    if clean_region_arrays is not None
                    else UNSET
                ),
                clean_region_fuels=(
                    clean_region_arrays.qualifying_fuels
                    if clean_region_arrays is not None
                    else UNSET
                ),
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
                # Per-plant budget period from the project's own governing
                # instrument (nyiso-220). UNSET unless the mechanism is armed
                # AND this ISO has registry entries, so every other run's
                # dispatch-kwargs key set is unchanged.
                hydro_period_hours=resolve_hydro_period_hours(
                    iso, dispatch_fleet, hydro_gen_idx, config
                ),
                # Hydraulic-cascade coupling (NWPP-36, owner ruling N3). UNSET
                # unless armed AND this ISO-year has a measured cascade
                # artifact resolving onto the fleet, so every other run's
                # dispatch-kwargs key set is unchanged. Same shared resolver as
                # scripts/run_calibration.py.
                hydro_cascade=resolve_hydro_cascade(
                    iso,
                    year,
                    dispatch_fleet,
                    hydro_gen_idx,
                    config,
                    hydro_monthly_energy=hydro_monthly_energy,
                ),
                T=config.hours,
            )
            dispatch_kwargs = build_base_dispatch_kwargs(
                dispatch_spec, import_node_recon=import_node_recon
            )
            # Overgeneration-dump guard domain (dump_cost_full_offer_domain,
            # GATED default off — caiso-139). Mirrors the run_calibration.py
            # hook so the forecast and backcast paths share the mechanism: the
            # guard is an LP soundness invariant (no row may profit by
            # generating purely to dump), so it regenerates from whatever offer
            # set a forecast year assembles. Flag off → key unset → identical LP.
            if getattr(config, "dump_cost_full_offer_domain", False):
                dispatch_kwargs.update(dump_cost_full_offer_domain=True)
            # Emissions mass-cap rows (policy constraint path, gated). When
            # mass_cap_enabled and a power-sector CO2 budget is configured for
            # the ISO's program/year, bound in-region fossil emissions; each
            # cap's per-generator coefficient is m[g]·emission_rate, where
            # m[g] is per-unit-exact for any generator with a real plant_code
            # (tested against its own plant's state) and the zone-level
            # m_zone[zone_idx] fallback otherwise (per_generator_membership,
            # plan §5). Default off → no specs → identical LP. The row dual is
            # surfaced as DispatchResult.co2_cap_price (a power-sector,
            # no-bank scenario allowance price -- plan §2/§8, not the
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
            if config.ramp_limits:
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
            # EIA-930 NG:WAT -- bounds the budget LP's perfect-foresight
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
                    # includes PS net discharge -- like-for-like with the
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
            # ERCOT standalone energy-only commitment-posture (reserve-decoupled;
            # docs/handoffs/ercot-commitment-thinness-2026-07.md). No-op /
            # byte-identical for every non-ERCOT run and default-off ERCOT.
            apply_ercot_commitment_posture(dispatch_kwargs, config, fleet_arrays)
            # P0 → monthly startup markup → P1 via the shared pipeline solve
            # core (orchestrator-unification Stage 3) -- intra-year warm start
            # included, statement-for-statement the former inline sequence.
            # Cross-year warm-start on the forecast path is gated ENTIRELY by
            # config.forecast_xyear_warmstart (plan §7 H-3, owner decision D-9):
            # forecast_xyear_cache is None unless the flag is armed, and a None
            # holder means the shared solve core neither applies nor exports a
            # basis -- so the default forecast stays cold-only and byte-identical
            # to the pre-D-9 tree. The same flag is passed as the explicit
            # xyear_warmstart gate so the calibration CLIs' default-ON
            # MARKET_SIM_WARMSTART_XYEAR can never reach the forecast trajectory
            # (rule 24 [R-REGISTRY]). tests/test_xyear_warmstart_default.py
            # statically asserts that pairing.
            # The historical blocker -- the marginal-tie reshuffle being read by
            # capacity.evolve_fleet's per-unit retirement screen, which could tip
            # a retire/keep decision and change the next year's fleet -- was
            # closed by wave 4C: the screen prices the attainable pro-forma
            # margin and credits attribute revenue on attainable in-merit
            # generation, so it depends on prices/mc/capacity only
            # (tests/test_forecast_warmstart_tie_invariance.py,
            # docs/cross-year-warmstart.md).
            # P1-native CAISO RA must-offer bridge (P2 archived -- CLAUDE.md:
            # P0/P1 only): floor the merchant gas CC/CT fleet from the P0 run
            # pattern before P1, so the scored P1 carries the RA structure. None
            # for every non-CAISO / non-RA run (byte-identical).
            ra_p1_prep = build_caiso_ra_p1_prep(
                config, iso, dispatch_fleet, fleet_arrays, mc_base
            )
            # P1-native ERCOT gas commitment bridge (ERCOT-63): committed-state
            # floor on merchant gas-CC from the P0 run pattern -- forward-native
            # by construction, so the forecast path carries it identically.
            # (None, None) for every non-ERCOT / gate-off run (byte-identical).
            # ERCOT-64 floor-scoped committed-LSL markdown: the measured LSL
            # bid on exactly the bridge's floored plant-hours -- the bid hook
            # shares the bridge's ONE floor computation (D-5 forecast parity
            # with the backcast orchestrator's wiring).
            _floorscoped_fn = None
            if (
                getattr(config, "ercot_offer_surface_lowcurve_floorscoped", False)
                and iso == "ERCOT"
            ):
                from market_sim.data.fleet import (
                    build_ercot_offer_surface_lowcurve_floorscoped_markdown,
                )

                _floorscoped_net_load = (
                    year_demand.sum(axis=0)
                    - (solar_cap[:, None] * year_solar_cf).sum(axis=0)
                    - (wind_cap[:, None] * wind_cf).sum(axis=0)
                )

                def _floorscoped_fn(
                    floor_mask,
                    _fa=fleet_arrays,
                    _fleet=dispatch_fleet,
                    _fp=fuel_prices,
                    _nl=_floorscoped_net_load,
                ):
                    return build_ercot_offer_surface_lowcurve_floorscoped_markdown(
                        _fa, _fleet, _fp, _nl, config, floor_mask
                    )

            ercot_bridge_prep, ercot_bridge_bid_prep = build_ercot_gas_bridge_p1_preps(
                config,
                iso,
                dispatch_fleet,
                fleet_arrays,
                mc_base,
                floorscoped_markdown_fn=_floorscoped_fn,
            )
            # P1-native NYISO gas commitment bridge (nyiso-87): committed-state
            # floor on the merchant slow-start gas fleet (CC_REGULAR + ST_GAS)
            # from the P0 run pattern -- minimum run duration, minimum down
            # time and the startup-restart inequality, all forward-native, so
            # the forecast path carries it identically (D-5 parity). None for
            # every non-NYISO / gate-off run (byte-identical).
            nyiso_bridge_prep = build_nyiso_gas_bridge_p1_prep(
                config, iso, dispatch_fleet, fleet_arrays, mc_base
            )
            # P1-native SPP gas commitment bridge (SPP-44): the SPP leg of the
            # same family on SPP's merchant slow-start gas fleet at its
            # measured plant-basis minimum stable load; forward-native, so
            # the forecast path carries it identically (D-5 parity). None for
            # every non-SPP / gate-off run (byte-identical).
            spp_bridge_prep = build_spp_gas_bridge_p1_prep(
                config, iso, dispatch_fleet, fleet_arrays, mc_base
            )
            # P1-native SOCO gas-steam CAMPAIGN commitment floor (SOCO-53d):
            # the SOCO leg of the same family, and the only one whose object is
            # a multi-WEEK campaign rather than an overnight or midday gap.
            # Measured minimum-run extension + online-hours LSL state floor on
            # SOCO's campaign-duty gas boilers, at their own measured
            # plant-basis minimum stable load; the restart legs are NOT armed
            # (SOCO's boilers do not two-shift). Forward-native, so the forecast
            # path carries it identically (D-5 parity). None for every non-SOCO
            # / gate-off run (byte-identical).
            soco_campaign_prep = build_soco_gas_st_campaign_p1_prep(
                config, iso, dispatch_fleet, fleet_arrays
            )
            # P1-native MISO regulated-coal night floor (miso-113):
            # committed-state floor on the regulated PRB/subbituminous fleet
            # at each plant's OWN measured within-run night level, net of its
            # _mustrun band (rule 19 [R-ONE-MECH]), over the P0-detected
            # committed run. Forward-native (the run pattern is the model's
            # own P0), so the forecast path carries it identically (D-5
            # parity). None for every non-MISO / gate-off run
            # (byte-identical).
            miso_night_floor_prep = build_miso_coal_night_floor_p1_prep(
                config, iso, dispatch_fleet, fleet_arrays
            )
            # P1-native PJM commitment-scoped reserve supply (path B, G-20b):
            # fa_p2-style availability mask from the P0 run pattern + the
            # deliverable supply cap recomputed on the masked fleet. (None,
            # None) for every non-PJM / gate-off run (byte-identical);
            # ISO-exclusive with the CAISO hook. Forward-regenerating by
            # construction -- the commitment state is the model's own P0 solve.
            pjm_fleet_prep, pjm_kwargs_prep = build_pjm_reserve_p1_prep(
                config, iso, fleet_arrays
            )
            # P1-native CAISO online-scoped reserve split
            # (caiso_reserve_online_scoped): the kwargs hook recomputes the
            # (2*n_r, T) spin/non-spin product-split ramp caps from the P0
            # run pattern -- SPIN scoped to online iron, NONSPIN to offline
            # fast-start. None for every non-CAISO / gate-off run
            # (byte-identical); ISO-exclusive with the PJM kwargs hook.
            caiso_reserve_kwargs_prep = build_caiso_reserve_p1_prep(
                config, iso, fleet_arrays
            )
            _t_pre_solve = time.perf_counter()
            # Keep the shared per-pass timing log to this year (the forecast
            # path is one energy solve per year) — PERF-B session 2.
            reset_pass_timing_log()
            energy_solve = run_energy_solve(
                dispatch_fleet,
                fleet_arrays,
                year_demand,
                mc_base,
                dispatch_kwargs,
                config,
                xyear_cache=forecast_xyear_cache,
                xyear_warmstart=config.forecast_xyear_warmstart,
                p1_fleet_prep=(
                    ra_p1_prep
                    or ercot_bridge_prep
                    or nyiso_bridge_prep
                    or spp_bridge_prep
                    or soco_campaign_prep
                    or miso_night_floor_prep
                    or pjm_fleet_prep
                ),
                p1_kwargs_prep=pjm_kwargs_prep or caiso_reserve_kwargs_prep,
                p1_bid_adjust_prep=ercot_bridge_bid_prep,
            )
            _t_post_solve = time.perf_counter()
            p1_result = energy_solve.p1
            mc_bid = energy_solve.mc_bid
            # The fleet P1 solved on -- RA-floored when the bridge fired, else the
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
            # K-row compliance-region diagnostics (FFR-7B Arm 2): each
            # region's dual IS that compliance market's REC price — logged
            # per year so an armed measurement can quote the per-region
            # duals without replaying the solve.
            if rps_region_arrays is not None and result.rps_region_duals is not None:
                logger.info(
                    "%s %d: RPS compliance-region duals ($/MWh): %s",
                    iso,
                    year,
                    {
                        label: round(float(d), 4)
                        for label, d in zip(
                            rps_region_arrays.labels, result.rps_region_duals
                        )
                    },
                )
            if (
                clean_region_arrays is not None
                and result.clean_region_duals is not None
            ):
                logger.info(
                    "%s %d: clean-tier region duals ($/MWh): %s",
                    iso,
                    year,
                    {
                        label: round(float(d), 4)
                        for label, d in zip(
                            clean_region_arrays.labels, result.clean_region_duals
                        )
                    },
                )

            # === LEGACY: P2 Commitment Screen (ARCHIVED -- last resort) ===
            # P2 (opt-in, CLAUDE.md "Dispatch & Commitment"): screen CC/CT
            # commitment on P1 clearing prices against base MC, pin coal to its P1
            # dispatch, and re-solve. P0/P1 are the only production passes and
            # every run is scored on P1; this branch runs only when a legacy
            # diagnostic gate is explicitly set (CLI --enable-legacy-p2). The
            # CAISO RA must-offer bridge NO LONGER triggers P2 -- it is applied
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
                # economic commitment screen + coal pin -- the same body the
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
            # results_write sub-instrumentation (refactor plan §7-H4): on the
            # forecast path the window is the archived P2 screen (inert by
            # default) plus save_result's parquet + config write. The two
            # segments are disjoint and exhaustive, so they sum to
            # results_write exactly.
            _t_pre_save = time.perf_counter()
            save_result(result, config, iso, year, context=context, demand=year_demand)
            _t_end = time.perf_counter()
            # The three subtrahends are the pass's OWN totals (PERF-B session 3,
            # charter C-2): ``build_s`` is EVERY matrix build run_energy_solve
            # performed — ``p1.build_time`` names one model and left the P0
            # model's build inside ``markup`` whenever P1 cold-rebuilt on a
            # floored fleet. The forecast path is one energy solve per year,
            # so the result's fields are the whole accounting here.
            _solve_p0 = energy_solve.solve_p0_s
            _solve_p1 = energy_solve.solve_p1_s
            _build = energy_solve.build_s
            _energy_s = _t_post_solve - _t_pre_solve
            _markup_s = max(0.0, _energy_s - _build - _solve_p0 - _solve_p1)
            _results_write = _t_end - _t_post_solve
            _total = _t_end - year_start
            _data_prep = _total - _solve_p0 - _markup_s - _solve_p1 - _results_write
            # markup sub-instrumentation (PERF-B session 2): ``markup`` is the
            # residual above, not a measured phase, so its components come from
            # inside run_energy_solve and ``other`` books this frame's
            # call/return edges around it — see pipeline/timing.py.
            _markup_parts = dict(energy_solve.markup_parts)
            if _markup_parts:
                _markup_parts["other"] = _markup_s - sum(_markup_parts.values())
            log_year_phase_timing(
                logger,
                year,
                data_prep=_data_prep,
                solve_p0=_solve_p0,
                markup=_markup_s,
                solve_p1=_solve_p1,
                results_write=_results_write,
                total=_total,
                markup_parts=_markup_parts,
                results_write_parts={
                    "legacy_p2": _t_pre_save - _t_post_solve,
                    "parquet": _t_end - _t_pre_save,
                },
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
        # see -- economic retirement, new entry and CCS retrofit screens
        # (capacity.evolve_fleet) -- so peakers and storage earn scarcity
        # revenue instead of bare LP duals. Raw duals structurally carry no
        # scarcity rent in a perfect-foresight LP with zero unserved energy,
        # which over-retires dispatchables and under-builds. Dispatch,
        # volumes, emissions and persisted results are untouched.
        # scarcity_price_overlay defaults True for ERCOT (energy-only; see
        # ISOConfig.default_scenario_overrides) and False elsewhere --
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
            # capacity backs the ORDC curve -- a cold slow-start unit the
            # perfect-foresight LP left idle is NOT real-time reserve. This is
            # the market-design-grounded replacement for the fitted flat RTORDPA
            # offset (the offset stays addable, default 0, as an explicit probe;
            # NOT netting the AS plan -- ERCOT's RTOLCAP already counts online
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
                "year %d: ORDC scarcity adder for capacity economics -- "
                "mean $%.2f/MWh, >$10 in %d h, max $%.0f",
                year,
                float(adder.mean()),
                int((adder > 10).sum()),
                float(adder.max()),
            )

        # CAISO post-solve scarcity overlay (Tariff §27.4.3.2 / §39.6.1):
        # the probabilistic reserve-scarcity adder is added to SCORED prices
        # (result.prices) because CAISO has no other scarcity mechanism -- the
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
            # caiso-85: the unloaded, must-offer import capability the LP holds
            # below VOLL — the corridor-bounded intertie supply that must exhaust
            # before CAISO's power-balance penalty prices fire (RA imports are
            # must-offer, CPUC D.20-06-028). Post-solve only; None off (byte-id).
            import_headroom_caiso = None
            if getattr(config, "caiso_scarcity_import_headroom", False):
                from market_sim.data.eia_loader import measured_corridor_flow_envelope
                from market_sim.data.fleet import FUEL_TYPE_MAP

                imp = fleet_arrays.fuel_type_idx == FUEL_TYPE_MAP["import"]
                if imp.any():
                    avail_cap = (
                        fleet_arrays.pmax[imp][:, None] * fleet_arrays.availability[imp]
                    )
                    imp_disp_by_row = result.dispatch[imp]
                    imp_disp = imp_disp_by_row.sum(axis=0)
                    # Tranche-level unloaded capability (pmax·availability - dispatch).
                    tranche_hr = np.maximum(avail_cap - imp_disp_by_row, 0.0).sum(
                        axis=0
                    )
                    # Bound by the measured WECC corridor import cap the LP itself
                    # dispatched under: unloaded import that could NOT be delivered
                    # through the corridor is not reserve.
                    env = measured_corridor_flow_envelope(
                        iso, year, imp_disp.shape[0], direction="import"
                    )
                    if env:
                        corridor_cap = np.sum(list(env.values()), axis=0)
                        corridor_hr = np.maximum(corridor_cap - imp_disp, 0.0)
                        import_headroom_caiso = np.minimum(tranche_hr, corridor_hr)
                    else:
                        import_headroom_caiso = tranche_hr
            caiso_adder = caiso_scarcity_overlay(
                fleet_arrays,
                result.dispatch,
                storage.power_cap,
                result.storage_charge,
                result.storage_discharge,
                renewable_headroom=ren_headroom_caiso,
                system_lambda=lam_caiso,
                import_headroom=import_headroom_caiso,
            )
            result.prices = result.prices + caiso_adder[None, :]
            econ_prices = result.prices
            overlay_adder = caiso_adder
            logger.info(
                "year %d: CAISO scarcity overlay -- "
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
        # array object -- byte-identical). Screens-only: dispatch, results
        # and persisted prices never see it.
        price_signal = econ_prices
        # The entering year the lookahead re-prices for. A capacity hindcast
        # (rule 22) may NEVER read a quarantined bridge year's data, so the
        # look-ahead is suppressed whenever the next year is a bridge year
        # (2022, 2026) or falls outside this run's own window -- the last
        # solved hindcast year (2025) has no admissible next year to screen
        # for. A plain forecast is bounded only by the module horizon.
        #
        # FFR-5D capacity_screen_unified_lookahead (GATED, default OFF, owner
        # decision D-19(a)): armed, the bridge suppression is replaced BY
        # CONSTRUCTION rather than by exception — a bridged entering year is
        # still priced, but on the growth-scaled demand fallback the
        # full-forward leg already uses for forward years, so the rule-22
        # no-read contract is unchanged while the screens' price OBJECT stops
        # flipping at the bridge (the FFR-5A basis asymmetry). The signals
        # are stored per entering year in ``unified_signals``; the top of the
        # year loop swaps the matching one into prior_results.price_signal.
        next_year = year + 1
        unified_screens = getattr(config, "capacity_screen_unified_lookahead", False)
        # FFR-8A scarcity restoration (GATED default OFF; __post_init__
        # guarantees it only arms with the unified lookahead, ERCOT-only).
        # The fleet's forced-outage sigma is a function of THIS year's solved
        # fleet, shared by every entering-year signal priced off it.
        scarcity_screens = getattr(
            config, "capacity_screen_scarcity_restoration", False
        )
        scarcity_sigma_r = (
            ercot_fleet_forced_outage_sigma_mw(
                dispatch_fleet, config, year, config.hours
            )
            if scarcity_screens
            else None
        )
        if config.hindcast:
            lookahead_next_ok = next_year <= end_year and (
                unified_screens or next_year not in HINDCAST_BRIDGE_YEARS
            )
        else:
            lookahead_next_ok = year < END_YEAR
        unified_signals = {}
        # D11-R margin-exhaustion walk state, one per priced entering year
        # (mirrors unified_signals): built by _screen_signal_for when
        # entry_margin_exhaustion is armed, bound into prior_results so the
        # entry screens can walk the SAME instrument that priced their
        # signal. Empty unarmed (byte-identical).
        entry_walks: dict[int, _EntryRepriceWalk] = {}
        # D12 forward reserve leg, one (T,) expected-ORDC adder per priced
        # entering year (mirrors entry_walks): captured by _screen_signal_for
        # when entry_forward_reserve_leg is armed, bound into prior_results so
        # the ENTRY screens read the entering year's own scarcity expectation
        # as their hourly reserve legs. Empty unarmed (byte-identical).
        entry_reserve_adders: dict[int, np.ndarray] = {}
        # ENTRY-SIGNAL forward-expectation state: the S_current evaluation
        # depends only on THIS solved year (its dispatched demand, its stack
        # basis), never on the entering year, so one evaluation serves every
        # ``_screen_signal_for`` call this year makes (next_year and the
        # bridge-adjacent year alike).
        _fwd_curr_state: dict = {}
        # C-1 JOINT POSTURE (owner ruling R-B, docs/PRECOMMIT-c1-joint-wind-
        # 2026-08-31.md §1.3): the seam is AVAILABLE whenever either the
        # reprice (which consumes its LEVEL) or the margin-exhaustion walk
        # (which consumes only its within-year DELTA,
        # _EntryRepriceWalk.signal = consumed + alpha x (S(state) - S(0))) is
        # armed. Widening availability is NOT arming: with the reprice
        # disarmed the seam runs for its WALK and its diagnostic dump only —
        # every consumption below stays gated on entry_lookahead_reprice, so
        # the screens keep the raw prior-year zonal duals (price_signal =
        # econ_prices, set above) that the disarm posture is defined by.
        # Byte-identical in every previously-reachable posture: armed-reprice
        # is unchanged, and with BOTH off the gate is False exactly as before.
        _reprice_level = config.entry_lookahead_reprice
        if (
            (_reprice_level or config.entry_margin_exhaustion)
            and config.mode == "forecast"
            and lookahead_next_ok
        ):

            def _screen_signal_for(entering_year: int) -> np.ndarray:
                """Price the capacity-screen lookahead for one entering year.

                The per-entering-year body of the seam: realized-demand
                override resolution (hindcast, non-bridge, non-crossover
                years only — rule 22), the FFR-5C pipeline terms, and the
                FFR-5D level repairs, all against THIS solved year's stack
                basis. Unarmed it is called exactly once with ``next_year``
                and reproduces the shipped path byte-identically.
                """
                # Hindcast: the KNOWN entering-year load is the realized
                # demand the LP will actually dispatch (line ~872), not a
                # growth-scaled weather year. Forecast: None → _scale_demand
                # fallback. A crossover FORWARD entering year must NOT read
                # the measured per-year loader (the same seam that skips it
                # for the LP demand above, FF-0E §2.2 / FH-1), and neither
                # may a BRIDGED entering year (rule 22 — only reachable
                # armed): both fall to the growth-scaled ``wx_config``
                # fallback like a plain forecast.
                demand_next_total = None
                if (
                    config.hindcast
                    and not config.is_crossover_forward_year(entering_year)
                    and not is_hindcast_bridge_year(
                        entering_year,
                        hindcast=config.hindcast,
                        crossover_forward_year=config.crossover_forward_year,
                        start_year=start_year,
                    )
                ):
                    _dn = load_demand(
                        iso,
                        entering_year,
                        iso_config,
                        td_loss_factor=config.td_loss_factor,
                        include_interchange=not import_generators,
                        strict_demand_profile=config.strict_demand_profile,
                        ercot_tie_zonal_interchange=config.ercot_tie_zonal_interchange,
                    )
                    if config.hours < _dn.shape[1]:
                        _dn = _dn[:, : config.hours]
                    demand_next_total = _dn.sum(axis=0)
                # FFR-5C entry_pipeline_aware_signal (GATED, default OFF ⇒
                # all three terms stay None and this is byte-identical): let
                # the pro-forma see the capacity the model has already
                # committed. The netting this replaces was guarding the same
                # phenomenon at the wrong object -- the annual flow caps
                # (rule 19 [R-ONE-MECH];
                # docs/handoffs/ffr-4a-entry-ladder-2026-08-04.md §3.5).
                _pipe_arrays = _pipe_mc = _pipe_vre = None
                if getattr(config, "entry_pipeline_aware_signal", False):
                    _pipe_arrays, _pipe_mc, _pipe_vre = _pipeline_lookahead_terms(
                        config,
                        fleet_config,
                        iso,
                        entry_pipeline,
                        entering_year,
                        year,
                        zone_names,
                        wind_cf,
                        solar_cf,
                        year_base_demand.sum(axis=0),
                        carbon_price,
                    )
                # FFR-5D level repairs (armed only; each None/False unarmed ⇒
                # byte-identical): entering-fleet VRE potential (repair b),
                # the entering storage fleet as a per-day peak shave (repair
                # a), hourly availability derating (repair c). All read
                # end-of-this-year model state — the same "last solved
                # state" basis every screen already runs on.
                _uni_vre = _uni_storage = None
                if unified_screens:
                    _uni_vre = (
                        wind_cf * np.asarray(wind_cap, dtype=float)[:, None]
                        + solar_cf * np.asarray(solar_cap, dtype=float)[:, None]
                    ).sum(axis=0)
                    _uni_storage = _storage_shave_terms(storage)
                # FFR-8A capacity_screen_scarcity_restoration (GATED, default
                # OFF ⇒ the bundle stays None and the unified path is
                # byte-identical). Armed: the storage fleet splits between its
                # AS-award share (held reserve, counted in the tail's R) and
                # its merchant share (the peak shave) — one measured constant,
                # two disjoint uses; the entering year's separate wind/solar
                # potentials feed the forward AS-requirement drivers; the
                # fleet's forced-outage sigma feeds the tail's expectation.
                # D11-R walk closure input: the PRE-split full storage terms,
                # so the walk can recompute the seam's own shave/AS split
                # with its accumulated storage tranches folded in.
                _uni_storage_full = _uni_storage
                _scar_bundle = None
                if scarcity_screens and _uni_storage is not None:
                    _p_mw, _e_mwh, _rte = _uni_storage
                    _as_frac = float(ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC)
                    _scar_storage_as = _as_frac * _p_mw
                    _uni_storage = (
                        (1.0 - _as_frac) * _p_mw,
                        (1.0 - _as_frac) * _e_mwh,
                        _rte,
                    )
                elif scarcity_screens:
                    _scar_storage_as = 0.0
                if scarcity_screens:
                    _scar_bundle = {
                        "wind_potential_mw": (
                            wind_cf * np.asarray(wind_cap, dtype=float)[:, None]
                        ).sum(axis=0),
                        "solar_potential_mw": (
                            solar_cf * np.asarray(solar_cap, dtype=float)[:, None]
                        ).sum(axis=0),
                        "sigma_r_mw": scarcity_sigma_r,
                        "storage_as_mw": _scar_storage_as,
                    }
                # L-5 (FINDING-entry-screen-t1h-2026-08 defect D-7): the
                # screen-signal dump is DIAGNOSTIC output, so it also arms on
                # the diagnostics gate — ``entry_screen_diagnostics``, the
                # RC-0C flag that already gates the per-candidate screen
                # ledger — not only on the behavioural
                # ``capacity_screen_unified_lookahead`` flag. Without this, an
                # ISO running the shipped (non-unified) lookahead cannot be
                # diagnosed offline at all. Output-only either way: the dict
                # is write-only inside ``_lookahead_reprice_signal`` (tested)
                # and this block only reads existing state and writes the npz,
                # so arming it changes no dispatch or entry outcome. At the
                # flag's default this expression is byte-identical to the old
                # ``{} if unified_screens else None``.
                # D12 forward reserve leg: the leg is the instrument's own
                # adder, read from the diagnostics dict, so arming the flag
                # forces the dict on. The npz write below keeps its ORIGINAL
                # gate (_dump_diag) — arming the leg alone captures the adder
                # without emitting dump files.
                _dump_diag = unified_screens or getattr(
                    config, "entry_screen_diagnostics", False
                )
                # capx D43 dispersion construction: its two headroom terms
                # are the instrument's own installed_headroom_mw diagnostics,
                # so arming the flag forces the dict on the same way (the
                # npz write keeps its ORIGINAL gate below).
                _dispersion_sig = getattr(
                    config, "entry_dispersion_expectation_signal", False
                )
                _diag: dict | None = (
                    {}
                    if (
                        _dump_diag
                        or getattr(config, "entry_forward_reserve_leg", False)
                        or _dispersion_sig
                    )
                    else None
                )
                sig = _lookahead_reprice_signal(
                    wx_config,
                    entering_year,
                    base_demand,
                    fleet_arrays,
                    mc_cost,
                    result,
                    len(zone_names),
                    demand_next_total=demand_next_total,
                    pipeline_mc=_pipe_mc,
                    pipeline_arrays=_pipe_arrays,
                    pipeline_vre=_pipe_vre,
                    vre_capacity_potential=_uni_vre,
                    storage_shave=_uni_storage,
                    hourly_availability=unified_screens,
                    scarcity_restoration=_scar_bundle,
                    diagnostics=_diag,
                )
                # ENTRY-SIGNAL forward-expectation composition (GATED
                # default-OFF, entry_forward_expectation_signal;
                # docs/FINDING-entry-signal-disarm-2026-08.md §6). The
                # screens' price object becomes the run's own prior-year
                # hourly ZONAL LP dual surface (econ_prices — locational,
                # real intraday shape, realized scarcity) re-leveled hour by
                # hour against the ENTERING year's stack. The re-level is
                # the same lookahead instrument evaluated twice: S_entering
                # is ``sig`` above, exactly as shipped; S_current prices
                # THIS year's own dispatched demand on the same stack /
                # VRE / storage / tail basis with NO pipeline terms — the
                # committed pipeline is part of what CHANGES between the
                # two years, so it belongs to the delta, not the baseline.
                # Exact arithmetic, zero fitted parameters (rule 21
                # [R-DOF]); replaces the zone-flat object rather than
                # stacking a correction on it (rule 19 [R-ONE-MECH]).
                if getattr(config, "entry_forward_expectation_signal", False):
                    if "sig" not in _fwd_curr_state:
                        _diag_curr: dict | None = {} if _diag is not None else None
                        _fwd_curr_state["sig"] = _lookahead_reprice_signal(
                            wx_config,
                            year,
                            base_demand,
                            fleet_arrays,
                            mc_cost,
                            result,
                            len(zone_names),
                            demand_next_total=year_demand.sum(axis=0),
                            vre_capacity_potential=_uni_vre,
                            storage_shave=_uni_storage,
                            hourly_availability=unified_screens,
                            scarcity_restoration=_scar_bundle,
                            diagnostics=_diag_curr,
                        )
                        _fwd_curr_state["diag"] = _diag_curr
                    _sig_curr_flat = _fwd_curr_state["sig"][0]
                    _fwd_delta = sig[0] - _sig_curr_flat
                    sig = _forward_expectation_signal(
                        econ_prices, sig[0], _sig_curr_flat
                    )
                    if _diag is not None:
                        # L-5 relocation carried deliberately (disarm §3.3):
                        # the dump keeps the S_entering internals above AND
                        # records the S_current internals, the forward delta
                        # and the composed zonal signal, so the object the
                        # screens actually consumed stays offline-diagnosable
                        # without a solve.
                        _diag["fwd_delta_usd_mwh"] = np.asarray(_fwd_delta, dtype=float)
                        _diag["signal_zonal_usd_mwh"] = np.asarray(sig, dtype=float)
                        _dc = _fwd_curr_state.get("diag") or {}
                        for _k in (
                            "price_base_usd_mwh",
                            "adder_usd_mwh",
                            "net_load_mw",
                        ):
                            if _k in _dc:
                                _diag[f"fwd_curr_{_k}"] = _dc[_k]
                    _zspread = float((sig.max(axis=0) - sig.min(axis=0)).mean())
                    logger.info(
                        "year %d: forward-expectation signal for %d -- "
                        "duals re-leveled by stack delta mean $%+.2f/MWh "
                        "(p05 %+.2f / p95 %+.2f); mean hourly cross-zone "
                        "spread $%.2f/MWh (the zone-flat object's is 0.0 "
                        "by construction)",
                        year,
                        entering_year,
                        float(_fwd_delta.mean()),
                        float(np.percentile(_fwd_delta, 5)),
                        float(np.percentile(_fwd_delta, 95)),
                        _zspread,
                    )
                # capx D43 DISPERSION-CARRYING expectation (GATED default-OFF,
                # entry_dispersion_expectation_signal; the D39 object:
                # docs/handoffs/FINDING-capx-d39-entry-underbuild-2026-09-02.md
                # §0/§3.1/§7). The screens' price object becomes each zone's
                # OWN realized price-duration curve (econ_prices — the
                # prior-year zonal duals with the run's own scarcity
                # overlay) indexed by the ENTERING year's headroom rank on
                # the CURRENT year's headroom distribution. Both headroom
                # terms are the lookahead instrument's own installed_headroom
                # diagnostics: S_entering is the ``sig`` evaluation above
                # (entering demand, pipeline / unified repairs as armed) and
                # S_current is the shared _fwd_curr_state evaluation at THIS
                # year's own dispatched demand with no pipeline terms — the
                # same pair the forward-expectation composition uses, so
                # load growth, VRE potential, the committed pipeline and the
                # storage shave move the RANK. Zero fitted parameters (rule
                # 21 [R-DOF]); REPLACES the zone-flat object (rule 19
                # [R-ONE-MECH]; __post_init__ refuses it alongside the
                # hour-aligned composition or the exhaustion walk).
                if _dispersion_sig:
                    if "sig" not in _fwd_curr_state:
                        _diag_curr_d: dict = {}
                        _fwd_curr_state["sig"] = _lookahead_reprice_signal(
                            wx_config,
                            year,
                            base_demand,
                            fleet_arrays,
                            mc_cost,
                            result,
                            len(zone_names),
                            demand_next_total=year_demand.sum(axis=0),
                            vre_capacity_potential=_uni_vre,
                            storage_shave=_uni_storage,
                            hourly_availability=unified_screens,
                            scarcity_restoration=_scar_bundle,
                            diagnostics=_diag_curr_d,
                        )
                        _fwd_curr_state["diag"] = _diag_curr_d
                    _h_next = np.asarray(_diag["installed_headroom_mw"], dtype=float)
                    _h_curr = np.asarray(
                        _fwd_curr_state["diag"]["installed_headroom_mw"], dtype=float
                    )
                    sig = _dispersion_expectation_signal(econ_prices, _h_next, _h_curr)
                    _u_rank = _headroom_rank(_h_next, _h_curr)
                    # L-5 dump relocation (the composition's precedent): the
                    # dump keeps the S_entering internals above AND records
                    # the S_current internals, the headroom rank and the
                    # composed zonal signal, so the object the screens
                    # consumed stays offline-diagnosable without a solve.
                    _diag["headroom_rank_next"] = np.asarray(_u_rank, dtype=float)
                    _diag["signal_zonal_usd_mwh"] = np.asarray(sig, dtype=float)
                    _dc = _fwd_curr_state.get("diag") or {}
                    for _k in (
                        "price_base_usd_mwh",
                        "adder_usd_mwh",
                        "net_load_mw",
                        "installed_headroom_mw",
                    ):
                        if _k in _dc:
                            _diag[f"fwd_curr_{_k}"] = _dc[_k]
                    logger.info(
                        "year %d: dispersion-carrying signal for %d -- realized "
                        "zonal duration curves indexed by entering headroom rank: "
                        "mean $%.2f/MWh (duals $%.2f, stack $%.2f); h >= $100: "
                        "%d (duals %d, stack %d); daily top4-bot4 spread $%.2f "
                        "(duals %.2f, stack %.2f); mean cross-zone spread $%.2f; "
                        "rank shift mean %+.3f",
                        year,
                        entering_year,
                        float(sig.mean()),
                        float(econ_prices.mean()),
                        float(_diag["price_base_usd_mwh"].mean()),
                        int((sig.mean(axis=0) >= 100.0).sum()),
                        int((econ_prices.mean(axis=0) >= 100.0).sum()),
                        int((_diag["price_base_usd_mwh"] >= 100.0).sum()),
                        _daily_top_bottom_spread(sig.mean(axis=0)),
                        _daily_top_bottom_spread(econ_prices.mean(axis=0)),
                        _daily_top_bottom_spread(_diag["price_base_usd_mwh"]),
                        float((sig.max(axis=0) - sig.min(axis=0)).mean()),
                        float(_u_rank.mean() - 0.5),
                    )
                # D12 forward reserve leg (GATED entry_forward_reserve_leg,
                # default OFF ⇒ dict empty, byte-identical): capture the
                # entering year's own expected-ORDC adder — the SAME
                # instrument invocation's scarcity object the energy leg just
                # priced — as this entering year's entry-screen reserve leg.
                if getattr(config, "entry_forward_reserve_leg", False) and _diag:
                    entry_reserve_adders[entering_year] = np.asarray(
                        _diag["adder_usd_mwh"], dtype=float
                    )
                if _diag and _dump_diag:
                    # FFR-8A diagnostic dump: the lookahead stack internals,
                    # next to the year's evolution ledger. Output-only — no
                    # config field, no cache-key term, no solve-path change
                    # (the control arm's reproduction gate proves it). The
                    # fleet/storage/VRE context makes the dump self-contained
                    # for the offline ablation probe (A1-A5) and the
                    # actual-fleet re-price, so the diagnosis never replays a
                    # solve.
                    _pg = getattr(fleet_arrays, "plant_group", None)
                    if _pg is not None:
                        _pg = np.asarray(_pg, dtype=object)
                        _cls_names = sorted({str(g) for g in _pg if str(g)})
                        _diag["class_names"] = np.array(_cls_names)
                        _diag["class_pmax_mw"] = np.array(
                            [
                                float(
                                    np.asarray(fleet_arrays.pmax, dtype=float)[
                                        _pg == c
                                    ].sum()
                                )
                                for c in _cls_names
                            ]
                        )
                    _diag.setdefault(
                        "sigma_r_mw",
                        ercot_fleet_forced_outage_sigma_mw(
                            dispatch_fleet, config, year, config.hours
                        ),
                    )
                    _shave_full = _storage_shave_terms(storage)
                    if _shave_full is not None:
                        _diag["storage_power_mw"] = float(_shave_full[0])
                        _diag["storage_energy_mwh"] = float(_shave_full[1])
                        _diag["storage_rte"] = float(_shave_full[2])
                    _diag["wind_potential_mw"] = (
                        wind_cf * np.asarray(wind_cap, dtype=float)[:, None]
                    ).sum(axis=0)
                    _diag["solar_potential_mw"] = (
                        solar_cf * np.asarray(solar_cap, dtype=float)[:, None]
                    ).sum(axis=0)
                    # capx D43 (L-5 dump extension, output-only): the run's
                    # OWN prior-year zonal dual surface the disarm fallback
                    # and both replacement constructions read. With it the
                    # dump is self-contained for the expected-vs-realized
                    # instrument (D39 §2): the NEXT solved year's dump
                    # carries that year's realized duals, so a run's own
                    # screen expectation can be scored against its own
                    # realized surface offline — no keeper stand-in, no
                    # replay. No config field, no cache-key term, no
                    # solve-path change.
                    _diag["econ_prices_usd_mwh"] = np.asarray(econ_prices, dtype=float)
                    _diag_path = get_cache_path(iso, cache_key, year).parent / (
                        f"screen_signal_diag_{year}_for_{entering_year}.npz"
                    )
                    _diag_path.parent.mkdir(parents=True, exist_ok=True)
                    np.savez_compressed(_diag_path, **_diag)
                # Unarmed: system row (every zone identical). Under the
                # forward-expectation composition the surface is zonal, so
                # the scarcity-hour log counts read the cross-zone mean.
                _sig_h = (
                    sig.mean(axis=0)
                    if (
                        getattr(config, "entry_forward_expectation_signal", False)
                        or _dispersion_sig
                    )
                    else sig[0]
                )
                logger.info(
                    "year %d: lookahead stack re-price for %d capacity "
                    "screens -- mean $%.2f/MWh (raw duals+overlay mean "
                    "$%.2f); pro-forma scarcity >$200 in %d h, >$1000 in "
                    "%d h, max $%.0f; committed pipeline priced in: "
                    "%d thermal unit(s), %.0f MWh VRE; unified repairs %s",
                    year,
                    entering_year,
                    float(sig.mean()),
                    float(econ_prices.mean()),
                    int((_sig_h > 200).sum()),
                    int((_sig_h > 1000).sum()),
                    float(_sig_h.max()),
                    0 if _pipe_arrays is None else int(_pipe_arrays.pmax.size),
                    0.0 if _pipe_vre is None else float(_pipe_vre.sum()),
                    "on" if unified_screens else "off",
                )
                # D11-R margin-exhaustion walk (GATED entry_margin_exhaustion,
                # default OFF ⇒ byte-identical): hand the entry screens a
                # repricer over THIS seam's own instrument at THIS entering
                # year's inputs. The closure re-invokes
                # _lookahead_reprice_signal with the walk's additions entering
                # through the model's own seams; at zero additions it
                # reproduces the ``sig`` call above bitwise, anchoring the
                # walk's delta construction exactly.
                if getattr(config, "entry_margin_exhaustion", False):

                    def _walk_reprice(
                        extra_stack,
                        extra_vre_walk,
                        d_power_mw,
                        d_energy_mwh,
                        rte_added,
                        _dnt=demand_next_total,
                        _pa=_pipe_arrays,
                        _pm=_pipe_mc,
                        _pv=_pipe_vre,
                        _uv=_uni_vre,
                        _usf=_uni_storage_full,
                        _sb=_scar_bundle,
                        _ey=entering_year,
                    ):
                        """(flat_signal, adder) at the given walk additions."""
                        shave = None
                        if unified_screens:
                            p0, e0, rte0 = _usf if _usf is not None else (0.0, 0.0, 0.0)
                            p1, e1 = p0 + d_power_mw, e0 + d_energy_mwh
                            if p1 > 0.0 and e1 > 0.0:
                                # Energy-weighted RTE of base fleet + walk
                                # tranches — the same aggregation
                                # _storage_shave_terms uses. At zero walk
                                # storage keep rte0 verbatim (no ulp drift
                                # against the seam's own call).
                                if d_energy_mwh == 0.0:
                                    rte1 = max(rte0, 1e-6)
                                else:
                                    rte1 = max(
                                        (rte0 * e0 + (rte_added or 0.0) * d_energy_mwh)
                                        / e1,
                                        1e-6,
                                    )
                                if _sb is not None:
                                    _f = float(ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC)
                                    shave = ((1.0 - _f) * p1, (1.0 - _f) * e1, rte1)
                                else:
                                    shave = (p1, e1, rte1)
                        scar = _sb
                        if _sb is not None and d_power_mw > 0.0:
                            _f = float(ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC)
                            scar = dict(_sb)
                            scar["storage_as_mw"] = (
                                float(_sb["storage_as_mw"]) + _f * d_power_mw
                            )
                        _d: dict = {}
                        s = _lookahead_reprice_signal(
                            wx_config,
                            _ey,
                            base_demand,
                            fleet_arrays,
                            mc_cost,
                            result,
                            len(zone_names),
                            demand_next_total=_dnt,
                            pipeline_mc=_pm,
                            pipeline_arrays=_pa,
                            pipeline_vre=_pv,
                            vre_capacity_potential=_uv,
                            storage_shave=shave,
                            hourly_availability=unified_screens,
                            scarcity_restoration=scar,
                            diagnostics=_d,
                            extra_stack=extra_stack,
                            extra_vre=extra_vre_walk,
                        )
                        return s[0], np.asarray(_d["adder_usd_mwh"], dtype=float)

                    entry_walks[entering_year] = _EntryRepriceWalk(
                        _walk_reprice, float(config.entry_price_signal_alpha)
                    )
                return sig

            # The seam always RUNS for next_year (that call is what builds the
            # walk); whether its level is CONSUMED is the reprice's question.
            _sig_next = _screen_signal_for(next_year)
            if _reprice_level:
                price_signal = _sig_next
            if unified_screens:
                # Every entering year this solved year's prior_results will
                # screen gets its OWN signal: next_year always; the
                # bridge-adjacent year after a bridged next_year too (the
                # bridge iteration never solves, so prior_results stays
                # pointed here and the post-bridge screens would otherwise
                # consume a signal priced for the wrong year). Blends use the
                # pre-update EWMA state; pass-through at alpha=1.0.
                _prev_ewma = price_signal_prev
                _alpha = float(config.entry_price_signal_alpha)
                if _reprice_level:
                    unified_signals[next_year] = _blend_price_signal(
                        _sig_next, _prev_ewma, _alpha
                    )
                _after_bridge = next_year + 1
                if (
                    is_hindcast_bridge_year(
                        next_year,
                        hindcast=config.hindcast,
                        crossover_forward_year=config.crossover_forward_year,
                        start_year=start_year,
                    )
                    and _after_bridge <= end_year
                    and not is_hindcast_bridge_year(
                        _after_bridge,
                        hindcast=config.hindcast,
                        crossover_forward_year=config.crossover_forward_year,
                        start_year=start_year,
                    )
                ):
                    # Same split: the call is what builds the bridge-adjacent
                    # entering year's walk, so it is unconditional; only its
                    # level's consumption is the reprice's question. Without
                    # this the joint posture would lose exactly one entering
                    # year's walk and go silently bang-bang there.
                    _sig_after = _screen_signal_for(_after_bridge)
                    if _reprice_level:
                        unified_signals[_after_bridge] = _blend_price_signal(
                            _sig_after, _prev_ewma, _alpha
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
        #  * co-opt duals -- under ercot_thermal_as_endogenous the per-hour
        #    binding reserve price from the solve's own reserve_price_by_family
        #    (all-products tier for synchronized units; the non-fast/Non-Spin
        #    tier for offline-capable quick-starts, mirroring the co-opt's
        #    headroom cascade). Supersedes that flag's annual per-fuel rate.
        #  * else the post-solve ORDC scarcity adder -- ERCOT pays real-time
        #    on-line/off-line reserves the same ORDC price the energy adder
        #    carries (RTORPA/RTOFFPA, Nodal Protocols §6.5.7.5), so the
        #    published-curve adder is the reserve price both tiers see.
        # None when the flag is off or neither mechanism ran -- the screens
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
            # D11-R margin-exhaustion walk for the entering year the stored
            # price_signal prices (rebound per entering year at the top of
            # the next iteration, mirroring the unified-signal swap). None
            # unarmed — the allocators then keep their bang-bang paths.
            entry_reprice=entry_walks.get(next_year),
            # D12 forward reserve leg for the same entering year (rebound per
            # entering year alongside entry_reprice). None unarmed — the
            # entry screens then keep the shipped realized legs.
            entry_reserve_price_signal=entry_reserve_adders.get(next_year),
            peak_demand=peak_demand,
            planned_additions=planned_additions,
            procured_vre_additions=procured_vre_additions,
            mc_cost=mc_cost,
            # Scalar (legacy row) or per-zone vector (K-row grain, FFR-7B
            # Arm 2) — an ndarray has no truth value, so gate on ndim.
            rps_shadow_price=(
                result.rps_shadow_price
                if result.rps_shadow_price is not None
                and np.ndim(result.rps_shadow_price) > 0
                else (result.rps_shadow_price or 0.0)
            ),
            # Clean-tier per-(fuel, zone) credits (FFR-7B Arm 3 state rows +
            # the SCN-WS2a federal CES target row): the region spec is
            # recomputed through the ONE resolver the solve side uses
            # (cheap, pure) so the cached-year path — which never assembles
            # the solve-side arrays — maps its restored duals identically.
            # The federal row's dual lands on every eligible fuel at
            # dual × credit fraction, entering the screens' existing max();
            # the voluntary row's (SCN-WS3b) lands on its eligible set at
            # dual × 1.0 the same way — the same year_demand sizes its RHS
            # here as on the solve side, so the region lists are identical.
            clean_attribute_price_by_fuel=(
                clean_credit_by_fuel(
                    _clean_region_arrays_for_year(
                        config,
                        iso,
                        year,
                        zone_names,
                        fleet_arrays,
                        zone_demand=year_demand,
                    ),
                    result.clean_region_duals,
                )
                if result.clean_region_duals is not None
                else None
            ),
            retrofit_log=retrofit_log,
            # AS-eligible (storage) fleet power for the AS-revenue saturation
            # in next year's capacity screens (capacity.evolve_fleet).
            storage_power_mw=float(sum(storage.power_cap))
            if storage.power_cap.ndim == 1
            else float(storage.power_cap.sum(axis=0).max()),
            # Storage AS revenue DERIVED from this year's co-opt reserve duals
            # (the endogenous analogue of the exogenous as_revenue rate) -- fed
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
            # -- fed to next year's retirement/new-entry screens so exactly one
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
            # Reserve-price signal (plan §5 step 2) -- the hourly reserve value
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
            # One storage-accreditation resolver (rule 19): the ISO's published
            # whole-class ratio where it has one and its gate is armed, else the
            # by-duration ELCC table. Unarmed this is byte-identical to the
            # pre-FFR-4E `_elcc_for_duration` call it replaces.
            storage_firm_mw=float(
                sum(
                    u.power_cap_mw
                    * storage_accreditation_credit(
                        u.energy_cap_mwh / u.power_cap_mw
                        if u.power_cap_mw > 0
                        else 0.0,
                        iso,
                        config,
                        u.tech_name,
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
            peak_demand_mw=peak_demand,
            elcc_curves_enabled=config.renewable_elcc_curves,
            nqc_curves_enabled=config.caiso_nqc_accreditation,
            config=config,
            accreditation_year=year,
        )
        # CR-3.1 observability: the credit each VRE class actually earned on
        # this year's own penetration (same resolver/basis as firm_mw above),
        # plus the storage fleet's power and pre-dilution accredited MW -- the
        # per-year accreditation trail the capacity-hindcast before/after
        # diagnostic and the T1.9 storage-saturation ladder read.
        credits_applied = renewable_credits_applied(
            fleet,
            float(np.sum(wind_cap)),
            float(np.sum(solar_cap)),
            iso,
            peak_demand_mw=peak_demand,
            elcc_curves_enabled=config.renewable_elcc_curves,
            nqc_curves_enabled=config.caiso_nqc_accreditation,
            # Same pair `firm_mw` above threads (capx D48 + D75-R): this row
            # records the credit the ledger APPLIED, so it must resolve through
            # the identical ladder or the trail would misreport it (rule 19).
            config=config,
            accreditation_year=year,
        )
        ledger = dict(evo_events)
        ledger.update(
            iso=iso,
            year=year,
            mode=config.mode,
            hindcast=bool(config.hindcast),
            bridge=False,
            peak_demand_mw=round(peak_demand, 3),
            # FFR-1C finding F-5, closed here (FFR-3B): this field summed
            # ``_FIRM_CLEAN_FUELS`` ("hydro",) over the PERSISTENT fleet, which
            # structurally never contains hydro — the runner carries hydro only
            # in the transient dispatch fleet — so every ledger ever written
            # reported firm_clean_mw = 0.0 for every ISO and year. That is a
            # DISPLAY seam, not a decision one: nothing reads this field to
            # decide anything (the adequacy screens read
            # ``accredited_firm_capacity_mw``, which FFR-1C already corrected),
            # so the fix is dispatch-inert by construction.
            #
            # It now reports the nameplate the model ACTUALLY dispatches —
            # ``modelled_hydro_nameplate_mw``, the exact population
            # ``build_hydro_fleet`` puts in the LP, resolved for the solve year
            # — keeping the field's own nameplate units. Any hydro that DID
            # reach the persistent fleet is added, mirroring
            # ``_hydro_firm_mw``'s no-double-count discipline in reverse: there
            # the pool is netted against the fleet, here the two are summed, so
            # the total is the same population either way.
            firm_clean_mw=round(
                float(
                    modelled_hydro_nameplate_mw(iso, year)
                    + sum(g.pmax_mw for g in fleet if g.fuel_type in _FIRM_CLEAN_FUELS)
                ),
                3,
            ),
            # Companion: the same resources at the ISO's PUBLISHED accreditation
            # factor — the MW that actually enter ``accredited_firm_capacity_mw``.
            # Reported alongside rather than replacing the nameplate basis,
            # because silently changing a field's units is how the next reader
            # gets misled a second time. Additive: readers of older ledgers must
            # treat an absent key as backward-compatible, not malformed.
            firm_clean_accredited_mw=round(float(_hydro_firm_mw(fleet, iso, year)), 3),
            reserve_margin=round(firm_mw / peak_demand - 1.0, 6)
            if peak_demand > 0
            else None,
            # capx D45 (2026-09-03) observability, ADDITIVE and output-only (no
            # decision reads it back; not a cache-key term): the CR-1 reserve
            # position the three capacity screens actually consumed this year
            # (ENTERING fleet ÷ this year's requirement — ``None`` when the
            # clearing gate is off for this ISO or in the base year) and the
            # adequacy requirement the position, the reliability floor and the
            # backstop share, so a per-year position table reads off the
            # committed ledger instead of being reconstructed from the
            # post-evolution ``reserve_margin`` identity (the D28/D37 route).
            capacity_reserve_position=(
                round(float(curve_reserve_position), 6)
                if curve_reserve_position is not None
                else None
            ),
            adequacy_requirement_mw=(
                round(
                    float(
                        resolve_adequacy_requirement_mw(config, iso, peak_demand, year)
                    ),
                    3,
                )
                if peak_demand > 0
                else None
            ),
            # capx D52: the SEAM peak / requirement / entering firm / position
            # the screens actually consumed this year (see the observability
            # block at the top of the loop) — distinct from the two LP-peak
            # fields above in every hindcast year that is not the weather year.
            **screen_ledger_fields,
            # Accreditation trail (CR-3.1): pool nameplates, resolved VRE
            # credits, and the storage fleet's power / pre-dilution firm MW
            # (dilution applies at the evolve consumer, capacity.py -- see
            # _storage_portfolio_elcc_dilution).
            wind_cap_mw=round(float(np.sum(wind_cap)), 3),
            solar_cap_mw=round(float(np.sum(solar_cap)), 3),
            renewable_credit_applied={
                fuel: round(credit, 6) for fuel, credit in credits_applied.items()
            },
            storage_power_mw=round(
                float(sum(u.power_cap_mw for u in storage_units)), 3
            ),
            storage_firm_mw=round(float(prior_results["storage_firm_mw"]), 3),
            # Scalar dual verbatim (legacy row); under the K-row grain the
            # ledger scalar is the MAX region dual (the binding compliance
            # market's REC price) — the full per-region vector is logged at
            # solve time and carried on DispatchResult.rps_region_duals.
            rps_dual=round(
                float(
                    np.max(result.rps_shadow_price)
                    if result.rps_shadow_price is not None
                    and np.ndim(result.rps_shadow_price) > 0
                    else (result.rps_shadow_price or 0.0)
                ),
                6,
            ),
            storage_additions=_storage_additions_since(
                storage_units, prior_storage_ids, zone_names
            ),
            solve_counts={"P0": 1, "P1": 1, "P2": 1 if p2_enabled else 0},
        )
        write_ledger(ledger_path(get_cache_path(iso, cache_key, year)), ledger)
        last_solved_year = year

    logger.info("run_scenario_iso done: iso=%s cache_key=%s", iso, cache_key)
    return cache_key


def run_sweep(sweep_def: SweepDefinition, workers: int | None = None) -> list[str]:
    """Expand a sweep into configs and run every ``(config, iso)`` pair.

    Delegates the fan-out to :func:`market_sim.pipeline.members.run_pairs`, the
    single shared home for the member pool (the same helper the ensembles and
    the scenario matrix reach). That is also the rule-12 fix: this function's
    former private copy defaulted to an **uncapped** ``cpu_count - 1`` workers,
    and a forecast member on a per-plant ISO is several GB, so more than ~2
    concurrent members OOMs. The default is now ``min(2, cpu_count - 1)``.

    Args:
        sweep_def: The sweep definition to expand.
        workers: Number of worker processes. Defaults to ``min(2, cpu_count -
            1)`` (CLAUDE.md rule 12); an explicit value is honoured as given.
            With a single worker the pairs run in-process (no subprocess
            overhead).

    Returns:
        The list of cache keys, one per ``(config, iso)`` pair, in expansion
        order.
    """
    # Lazy import, mirroring matrix.run_matrix: ``members`` module-imports the
    # pipeline api facade, whose ``runner`` import is itself lazy, so nothing
    # here can close a module-level import cycle.
    from market_sim.pipeline.members import run_pairs

    configs = sweep_def.generate()
    pairs = [(config, config.iso) for config in configs]

    logger.info("run_sweep start: %d (config, iso) pair(s)", len(pairs))

    return run_pairs(pairs, workers=workers)


def _add_authorization_flag(subparser: argparse.ArgumentParser) -> None:
    """Attach the shared §2.1b ``--full-solve-authorized`` flag to a subcommand.

    Every ``market-sim`` subcommand can schedule a forecast horizon (the
    scenario YAML carries it, and a YAML with no year fields inherits the
    2026-2050 module default), so every one of them carries the cap and its
    authorization flag. See :mod:`market_sim.config.schedulable`.

    Args:
        subparser: The subcommand parser to extend.
    """
    from market_sim.config.schedulable import add_authorization_flag

    add_authorization_flag(
        subparser,
        "Without it this CLI REFUSES a config whose forecast horizon is wider "
        "than the cap (audit FR-25).",
    )


def _assert_cli_schedulable(
    config: ScenarioConfig, args: argparse.Namespace, entry_point: str
) -> None:
    """Refuse an over-cap forecast horizon before any solve begins.

    The §2.1b cap (plan §7.9) was enforced only in ``run_full_horizon.py`` and
    ``run_ces_leg.py``; a ``market-sim run/sweep/ensemble/matrix`` invocation
    over a default 2026-2050 YAML scheduled 25 solve-years with no refusal
    anywhere (forecast-readiness audit FR-25). Backcast configs are untouched —
    their windows are rule-22's holdout gate, not §2.1b's.

    Args:
        config: The scenario about to be solved.
        args: Parsed CLI arguments (supplies ``full_solve_authorized``).
        entry_point: Label naming the subcommand in the refusal message.

    Raises:
        SystemExit: When the window exceeds the cap and is unauthorized.
    """
    from market_sim.config.schedulable import assert_config_schedulable

    assert_config_schedulable(
        config, getattr(args, "full_solve_authorized", False), entry_point
    )


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
    _add_authorization_flag(run_parser)

    sweep_parser = subparsers.add_parser("sweep", help="Run a parameter sweep.")
    sweep_parser.add_argument(
        "--sweep", required=True, help="Path to a sweep YAML file."
    )
    sweep_parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Worker processes; defaults to min(2, cpu_count - 1) (rule 12).",
    )
    _add_authorization_flag(sweep_parser)

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
    _add_authorization_flag(ensemble_parser)

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
    _add_authorization_flag(matrix_parser)

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
        _assert_cli_schedulable(config, args, "market-sim run")
        run_scenario_iso(config, iso)
    elif args.command == "sweep":
        sweep_def = SweepDefinition.from_yaml(args.sweep)
        # A sweep member may override start_year/end_year, so check every
        # expanded config, not just the (default) base.
        for member in sweep_def.generate():
            _assert_cli_schedulable(member, args, "market-sim sweep")
        run_sweep(sweep_def, args.workers)
    elif args.command == "ensemble":
        config = ScenarioConfig.from_yaml(args.config)
        iso = args.iso or config.iso
        # An ensemble solves the window once PER MEMBER, so an over-cap window
        # is over-cap many times over; the cap is checked on the window (the
        # §2.1b unit) and the member count is reported by the drivers.
        _assert_cli_schedulable(config, args, "market-sim ensemble")
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

        # The matrix CLI takes no year arguments at all — the horizon rides the
        # base YAML (and its cases may override it), which is exactly why an
        # unguarded `market-sim matrix` was the audit's headline FR-25 hole.
        base_config = ScenarioConfig.from_yaml(args.config)
        _assert_cli_schedulable(base_config, args, "market-sim matrix")
        for case in SweepDefinition.from_yaml(args.matrix).generate(base_config):
            _assert_cli_schedulable(case, args, "market-sim matrix")
        run_matrix_cli(args.config, args.matrix, args.iso, args.workers, args.out_dir)


if __name__ == "__main__":
    main()
