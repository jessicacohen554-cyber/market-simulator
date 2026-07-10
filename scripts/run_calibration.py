"""Run the dispatch model for calibration years and print comparison tables.

Backcasts the hourly economic dispatch against historical years (2021-2024)
for which EIA actuals exist, then prints headline diagnostics — generation by
fuel, CO2, zonal prices, negative-price hours and renewable curtailment — so
the modeled year can be eyeballed against the eGRID benchmark.

Each calibration year is run as a single-year dispatch (no capacity
evolution): the EIA-860 fleet is dispatched against that year's EIA-930
demand and renewable profiles, with the renewable capacity and gas price
pinned to the year's measured values.

Usage:
    python scripts/run_calibration.py --year 2023
    python scripts/run_calibration.py --year 2021 2022 2023 2024
    python scripts/run_calibration.py --year 2023 --hours 168
    python scripts/run_calibration.py --year 2023 --ttc-wn 9000 --ttc-wsc 3000

Options:
    --year         One or more calibration years to run.
    --iso          ISO to calibrate (default ERCOT).
    --hours        Dispatch horizon in hours (default 8760); use a small
                   value such as 168 for a quick smoke test.
    --ttc-wn       Override the West<->North transfer capability (MW).
    --ttc-wsc      Override the West<->South_Central transfer capability (MW).
    --ttc-pn       Override the Panhandle<->North transfer capability (MW).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    HOURS_PER_YEAR,
    NYISO_INTERFACE_TTC_BY_MONTH,
    NYISO_INTERFACE_TTC_BY_YEAR,
    resolve_reference_price_interface,
)
from market_sim.config.interchange_config import (  # noqa: E402
    INTERFACE_NEIGHBORS,
    PRICED_INTERCHANGE_DEFAULT_ISOS,
    apply_interchange_topology,
    build_interchange_fleet,
    get_interchange_spec,
    resolve_priced_interchange,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import CALIBRATION_DIR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.eia_loader import (  # noqa: E402
    load_demand,
    load_ercot_fossil_gen,
)
from market_sim.data.fleet import (  # noqa: E402
    _hour_to_month_index,
    apply_coal_tranches,
    apply_ercot_ct_offer_surface,
    apply_neiso_coldsnap_derate,
    apply_netload_drag_floors,
    assemble_mc,
    build_base_fleet,
    build_dispatch_fleet,
    build_ercot_offer_surface_conditional_markup,
    fleet_to_bins,
    generators_to_fleet_arrays,
    load_campd_bins,
    load_fleet_from_csv,
    load_retired_within_window,
    thermal_tranche_overrides,
)
from market_sim.data.fuel import (  # noqa: E402
    apply_caiso_zonal_gas_basis,
    apply_coal_supply_pricing,
    apply_dual_fuel_pricing,
    apply_ercot_west_netload_gas_shape,
    apply_ercot_zonal_gas_basis,
    apply_hub_basis_overlay,
    apply_miso_zonal_gas_basis,
    apply_nyiso_downstate_ct_gas_basis,
    apply_nyiso_downstate_ct_gas_daily,
    apply_nyiso_zonal_gas_basis,
    apply_pjm_zonal_gas_basis,
    apply_plant_monthly_fuel_prices,
    dual_fuel_switch_mask,
    ercot_west_oversupply_collapse_freq,
    resolve_fuel_prices,
)
from market_sim.data.renewables import (  # noqa: E402
    hsl_potential_mw,
    inject_offshore_wind_availability,
    load_hsl_hourly,
    load_renewable_profiles,
)
from market_sim.pipeline import (  # noqa: E402
    DispatchSpec,
    apply_reserve_coopt,
    backcast_config,
    build_base_dispatch_kwargs,
    build_caiso_ra_p1_prep,
    build_pjm_reserve_p1_prep,
    run_commitment_pass,
    run_energy_solve,
)
from market_sim.pipeline.backcast_config import (  # noqa: E402
    _GENERIC_NEUTRAL_GAS_CLASSES,  # noqa: F401 -- re-exported for test_offer_curve_deleakage
    _MISO_CC_COAL_REBALANCE,
    _deep_merge_offer_curve,
    _neutralize_generic_gas_bands,  # noqa: F401 -- re-exported for test_offer_curve_deleakage
)
from market_sim.model.storage import (  # noqa: E402
    load_eia860_storage,
    reserve_storage_as_power,
    storage_cap_profiles,
    storage_units_to_arrays,
)
from market_sim.model.transmission import (  # noqa: E402
    apply_interchange_injections,
    build_incidence_matrix,
    build_interface_groups,
    get_link_bidirectional_array,
    get_ttc_array,
    wecc_border_carbon_adder,
)
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from market_sim.policy.constraints import (  # noqa: E402
    build_mass_cap_dispatch_kwargs,
)
from market_sim.policy.eac import (  # noqa: E402
    apply_eac_to_mc,
    apply_negative_renewable_offer_floor,
    compute_eac_dispatch_credits,
)
from market_sim.policy.ira import compute_dispatch_credits  # noqa: E402
from market_sim.results.calibration import (  # noqa: E402
    check_hourly_dispatch_correlation,
)
from market_sim.results.emissions import compute_emissions  # noqa: E402
from market_sim.results.outputs import FleetContext  # noqa: E402

# Model fuel types that make up the EIA-930 "natural gas" telemetry series:
# combined cycle, combustion turbine and gas steam are reported as one fuel.
_GAS_FUEL_TYPES: frozenset[str] = frozenset({"gas_cc", "gas_ct", "gas_st"})

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("run_calibration")

# Calibration reference written by scripts/build_calibration_reference.py.
REFERENCE_PATH: Path = CALIBRATION_DIR / "calibration_reference.json"

# Fallback measured Henry Hub annual-average spot price ($/MMBtu), used when
# the calibration reference JSON has not yet been generated.
# Source: EIA Henry Hub Natural Gas Spot Price, annual averages.
_HENRY_HUB_FALLBACK: dict[int, float] = {
    2021: 3.72,
    2022: 6.45,
    2023: 2.54,
    2024: 2.19,
    2025: 3.52,
}

_MWH_PER_TWH: float = 1.0e6
_TONNES_PER_MT: float = 1.0e6

# Zone-pair identifying each transfer link whose TTC the CLI can override.
# Both legs of the West Texas Export interface and the Panhandle GTC are
# exposed for tuning — these are ERCOT's primary wind-export constraints.
_TTC_LINK_ZONES: dict[str, frozenset[str]] = {
    "ttc_wn": frozenset({"West", "North"}),
    "ttc_wsc": frozenset({"West", "South_Central"}),
    "ttc_pn": frozenset({"Panhandle", "North"}),
}


def _load_reference() -> dict:
    """Return the calibration reference dict, or an empty dict if unbuilt."""
    if not REFERENCE_PATH.exists():
        logger.warning(
            "calibration reference %s not found — run "
            "build_calibration_reference.py first; using fallback gas prices",
            REFERENCE_PATH.relative_to(REPO),
        )
        return {}
    return json.loads(REFERENCE_PATH.read_text())


def _henry_hub_actual(reference: dict, year: int) -> float:
    """Return the measured Henry Hub price for ``year`` from the reference."""
    table = reference.get("henry_hub_actual", {})
    if str(year) in table:
        return float(table[str(year)])
    return _HENRY_HUB_FALLBACK[year]


# Backward-compatible alias (orchestrator-unification Stage 7 moved the
# function to market_sim.pipeline.backcast_config): probe/derive scripts and
# tests importing ``_calibration_config`` from this module, or calling it via
# ``rc._calibration_config``, keep working unchanged.
_calibration_config = backcast_config


def _apply_ttc_overrides(
    iso_config, ttc: np.ndarray, overrides: dict[str, float | None]
) -> np.ndarray:
    """Return ``ttc`` with the requested link capabilities overridden.

    Args:
        iso_config: The ISO topology, used to map links to zone pairs.
        ttc: The base ``(n_links,)`` transfer-capability array.
        overrides: ``{"ttc_wn": MW | None, "ttc_wsc": MW | None,
            "ttc_pn": MW | None}``.

    Returns:
        A copy of ``ttc`` with each non-``None`` override applied.
    """
    ttc = ttc.copy()
    for key, value in overrides.items():
        if value is None:
            continue
        target = _TTC_LINK_ZONES[key]
        for i, link in enumerate(iso_config.links):
            if frozenset({link.from_zone, link.to_zone}) == target:
                logger.info(
                    "override %s link TTC: %.0f -> %.0f MW",
                    "-".join(sorted(target)),
                    ttc[i],
                    value,
                )
                ttc[i] = value
    return ttc


def _apply_iso_year_ttc(iso_config, iso: str, year: int):
    """Return ``iso_config`` with year-varying interface TTCs applied.

    Some interfaces change capacity across the backcast years as transmission
    is built (e.g. NYISO's Central-East jumps with the NY Transco AC
    Transmission project, in service December 2023). The static topology in
    ``iso_configs`` carries one value; this rewrites the matching links to the
    year-accurate limit (``constants.NYISO_INTERFACE_TTC_BY_YEAR``) so 2023
    runs on the pre-upgrade limit and 2024+ on the upgraded one. A no-op for
    ISOs/years with no entry.
    """
    if iso != "NYISO":
        return iso_config
    overrides = NYISO_INTERFACE_TTC_BY_YEAR.get(year)
    if not overrides:
        return iso_config
    links = []
    for link in iso_config.links:
        new_ttc = overrides.get((link.from_zone, link.to_zone))
        if new_ttc is not None and new_ttc != link.ttc_mw:
            logger.info(
                "NYISO %d interface TTC: %s->%s %.0f -> %.0f MW "
                "(AC Transmission year-varying limit)",
                year,
                link.from_zone,
                link.to_zone,
                link.ttc_mw,
                new_ttc,
            )
            links.append(link.model_copy(update={"ttc_mw": new_ttc}))
        else:
            links.append(link)
    return iso_config.model_copy(update={"links": links})


def _apply_iso_monthly_ttc(ttc, iso_config, iso: str, year: int, hours: int):
    """Expand the scalar TTC array to a per-hour ``(hours, n_links)`` matrix
    when the ISO has a measured monthly interface envelope for ``year``.

    NYISO's Central-East day-ahead TTC is not flat across a year: it steps up
    when the AC Transmission upgrade energizes (Dec 2023) and derates each
    late-summer/shoulder. ``constants.NYISO_INTERFACE_TTC_BY_MONTH`` carries the
    measured 12-month mean per interface; this maps each hour of the backcast
    year to its calendar month (leap-safe) and rewrites the matching link's
    limit hour by hour, so the dispatch binds on the seasonal envelope rather
    than one annual value. Returns ``ttc`` unchanged (1-D) for ISOs/years with
    no monthly table — byte-identical to the prior scalar path.
    """
    if iso != "NYISO":
        return ttc
    monthly = NYISO_INTERFACE_TTC_BY_MONTH.get(year)
    if not monthly:
        return ttc
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days_per_month = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_of_hour = np.repeat(np.arange(1, 13), [d * 24 for d in days_per_month])[
        :hours
    ]
    ttc_t = np.broadcast_to(ttc, (hours, len(ttc))).copy()
    for i, link in enumerate(iso_config.links):
        profile = monthly.get((link.from_zone, link.to_zone))
        if profile is None:
            continue
        prof = np.asarray(profile, dtype=float)
        ttc_t[:, i] = prof[month_of_hour - 1]
        logger.info(
            "NYISO %d %s->%s monthly TTC envelope: %.0f-%.0f MW "
            "(measured Central-East DAM postings)",
            year,
            link.from_zone,
            link.to_zone,
            prof.min(),
            prof.max(),
        )
    return ttc_t


def _apply_caiso_solar_deliverability(
    solar_cf: np.ndarray, iso: str, year: int, config
) -> np.ndarray:
    """Re-curtail the CAISO solar potential for the local congestion the reduced
    topology can't see (Lever D).

    Two CAISO-only paths, both operating on the per-zone solar CF upper bound the
    LP dispatches against:

    * **Structural** (``config.caiso_solar_deliverability``, the keeper path): a
      local-deliverability derate ``clip(1 − k × solar_frac(t), floor, 1)`` from
      :func:`market_sim.model.transmission.caiso_solar_deliverability_derate`,
      driven by the FORWARD solar-penetration signal. The curtailed VOLUME emerges
      per-year from that year's own penetration/build — never a pin to actuals.

    * **Interim stopgap** (``config.caiso_solar_cap_at_delivered``, a default-off
      DIAGNOSTIC): caps each hour's solar at the measured EIA-930 delivered share
      of the HSL potential. This PINS solar to the measured outcome (no forward
      analogue) and must never feed a keeper — it exists only as an A/B reference
      for the structural derate (CLAUDE.md #11).

    Returns ``solar_cf`` unchanged (byte-identical) for non-CAISO ISOs, when
    neither flag is set, or when the forward signal / HSL data is unavailable.
    """
    if iso.upper() != "CAISO":
        return solar_cf
    hours = solar_cf.shape[1]

    if getattr(config, "caiso_solar_cap_at_delivered", False):
        # DIAGNOSTIC: delivered/potential ratio from the HSL parquet (delivered
        # gen ÷ uncurtailed potential), applied as a per-hour ceiling on the CF.
        from market_sim.data.renewables import load_hsl_hourly

        hsl = load_hsl_hourly("CAISO", year)
        if hsl is not None:
            pot = hsl["solar_hsl_mw"].to_numpy(dtype=float)[:hours]
            gen = hsl["solar_gen_mw"].to_numpy(dtype=float)[:hours]
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = np.where(pot > 0.0, np.clip(gen / pot, 0.0, 1.0), 1.0)
            logger.info(
                "CAISO %d: solar cap-at-delivered DIAGNOSTIC (default-off pin, "
                "not forecast skill) — solar potential haircut to measured "
                "delivered, mean ratio %.3f midday",
                year,
                float(
                    np.mean(
                        ratio[
                            (np.arange(hours) % 24 >= 9) & (np.arange(hours) % 24 <= 15)
                        ]
                    )
                ),
            )
            return solar_cf * ratio[None, :]
        logger.warning(
            "CAISO %d: --caiso-solar-cap-at-delivered requested but no HSL "
            "parquet — solar left uncapped (no-op)",
            year,
        )
        return solar_cf

    if getattr(config, "caiso_solar_endogenous_spill", False):
        logger.info(
            "CAISO %d: endogenous solar spill — full solar potential passed "
            "to LP (no pre-LP CF derate); solar sets the midday dual when "
            "curtailed",
            year,
        )
        return solar_cf

    if getattr(config, "caiso_solar_deliverability", False):
        from market_sim.model.transmission import caiso_solar_deliverability_derate

        derate = caiso_solar_deliverability_derate(
            year,
            hours,
            float(getattr(config, "caiso_solar_deliverability_k", 0.15)),
            float(getattr(config, "caiso_solar_deliverability_floor", 0.50)),
        )
        if derate is not None:
            hod = np.arange(hours) % 24
            mid = (hod >= 9) & (hod <= 15)
            logger.info(
                "CAISO %d: local solar deliverability derate (Lever D) — "
                "solar potential capped at clip(1 − %.3f × solar_frac, %.2f, 1); "
                "midday mean derate %.3f (≈ %.1f%% midday curtailment headroom)",
                year,
                float(getattr(config, "caiso_solar_deliverability_k", 0.15)),
                float(getattr(config, "caiso_solar_deliverability_floor", 0.50)),
                float(np.mean(derate[mid])),
                100.0 * (1.0 - float(np.mean(derate[mid]))),
            )
            return solar_cf * derate[None, :]
        logger.warning(
            "CAISO %d: caiso_solar_deliverability on but no forward solar "
            "penetration signal — solar left uncapped (no-op)",
            year,
        )
    return solar_cf


def run_year(
    year: int,
    iso: str,
    hours: int,
    gas_price: float,
    ttc_overrides: dict[str, float | None],
    coal_passthrough: float | None = None,
    commitment_enabled: bool = False,
    commitment_screen_coal: bool = True,
    coal_lignite_mustrun: float | None = None,
    coal_prb_mustrun: float | None = None,
    coal_prb_passthrough: float = 1.0,
    outage_source: str = "historic",
    coal_prb_passthrough_sigmoid: bool = False,
    coal_mustrun_per_plant: bool = False,
    retiree_cems_cap: bool = False,
    ct_mustrun_per_plant: bool = False,
    ct_mustrun_floor_frac: float = 1.0,
    coal_drop_pof: bool = False,
    coal_prb_passthrough_tiered: bool = False,
    prb_overrides: dict | None = None,
    coal_bit_sigmoid: bool = False,
    bit_overrides: dict | None = None,
    coal_econ_srmc_bound: bool = False,
    coal_takeorpay_from_data: bool = False,
    coal_mustrun_online_pmin: bool = False,
    coal_sync_srmc_tranche: bool = False,
    ct_intermediate_split: bool = False,
    ct_intermediate_cf_threshold: float | None = None,
    cc_intermediate_split: bool = False,
    cc_intermediate_cf_threshold: float | None = None,
    tranche_startup_amortization: bool = False,
    tranche_startup_measured_runs: bool = False,
    nysdec_peaker_rule_availability: bool = False,
    oil_primary_bin_fuel: bool = False,
    plant_tranche_config: str | None = None,
    storage_daily_cycling: bool = False,
    storage_vintage_ramp: bool = False,
    battery_dispatch_adder: float = 0.0,
    gas_offer_curve: bool = False,
    gas_monthly_actuals: bool = False,
    pjm_zonal_gas_basis: bool = False,
    miso_zonal_gas_basis: bool = False,
    pjm_congestion: bool = False,
    offer_curve_overrides: dict[str, dict[str, float]] | None = None,
    offer_curve_deltas: dict[str, dict[str, float]] | None = None,
    curve_smoothing: dict[str, float | int | None] | None = None,
    cc_derate_from_top: bool = False,
    cc_nameplate_summer_derate: bool = False,
    coal_nameplate_summer_derate: bool = False,
    gt_ambient_derate: bool = False,
    gt_ambient_derate_ref_c: float | None = None,
    gt_ambient_derate_slope_cc: float | None = None,
    gt_ambient_derate_slope_ct: float | None = None,
    temp_dependent_derate: bool = False,
    ercot_offer_surface_conditional: bool = False,
    neiso_offer_surface_conditional: bool = False,
    must_run_mw: "np.ndarray | None" = None,
    inject_biomass_mustrun: bool = False,
    priced_interchange: bool = False,
    hydro_backfill_year: int | None = None,
    as_reserve_withholding: bool = False,
    as_reserve_formula: bool = False,
    energy_reserve_coopt: bool = False,
    miso_zonal_reserves: bool = False,
    miso_reserve_pergen: bool = False,
    miso_commitment_posture: bool = False,
    ercot_multiproduct_as_coopt: bool = False,
    ercot_ecrs_conservative_deployment: bool = False,
    ercot_ordc_total_reserve: bool = False,
    ercot_as_aware_commitment: bool = False,
    ercot_reserve_supply_cap: bool = False,
    ercot_reserve_supply_cap_from_year: int = 2023,
    ercot_reserve_supply_forward: bool = False,
    pjm_reserve_supply_cap: bool = False,
    pjm_reserve_online_gated: bool = False,
    pjm_reserve_online_rho: float = 1.0,
    pjm_reserve_commitment_scoped: bool = False,
    pjm_reserve_pergen: bool = False,
    pjm_reserve_pergen_sync: bool = False,
    pjm_reserve_pergen_size_split: bool = False,
    pjm_commitment_posture: bool = False,
    measured_ramp_capability: bool = False,
    ercot_as_forward_requirement: bool = False,
    ercot_load_resource_reserve: bool = False,
    ercot_load_resource_reserve_from_year: int = 2023,
    ercot_storage_as_reserve: bool = False,
    ercot_storage_as_reserve_from_year: int = 2025,
    ercot_ecrs_requirement: bool = False,
    ercot_ecrs_requirement_from_year: int = 2023,
    ordc_lolp_params_path: str | None = None,
    ercot_storage_as_product_credit: bool = False,
    gas_hh_monthly_shape: bool = False,
    storage_as_commitment: bool = False,
    ercot_storage_as_endogenous: bool = False,
    ercot_storage_as_duration_gate: bool = False,
    hydro_eia930_monthly: bool = False,
    hydro_forecast_budget: bool = False,
    hydro_year: str = "normal",
    interchange_shaping: bool = False,
    interchange_shaping_export_only: bool = False,
    reference_price_interface: bool = False,
    negative_renewable_offers: bool | None = None,
    caiso_gas_commitment_floor: bool | None = None,
    caiso_gas_floor_frac: float | None = None,
    caiso_ra_mustoffer: bool | None = None,
    caiso_ra_min_load_frac: float | None = None,
    caiso_ra_startup_bridge: bool | None = None,
    caiso_ra_bridge_decommit: bool | None = None,
    reliability_floor: bool | None = None,
    reliability_floor_overrides: dict | None = None,
    scarcity_price_overlay: bool | None = None,
    caiso_scarcity_pricing: bool | None = None,
    caiso_lcr_commitment_credit: bool | None = None,
    caiso_solar_deliverability: bool | None = None,
    caiso_solar_deliverability_k: float | None = None,
    caiso_solar_endogenous_spill: bool | None = None,
    caiso_solar_cap_at_delivered: bool | None = None,
    neiso_gas_coldsnap_derate: bool | None = None,
    neiso_oil_burn_budget: bool | None = None,
    neiso_winter_fuel_inventory: bool | None = None,
    neiso_winter_fuel_start_fill_bbl: float | None = None,
    neiso_winter_fuel_mustrun: bool | None = None,
    caiso_import_hub_prices: bool | None = None,
    caiso_import_gas_coupling: bool | None = None,
    caiso_import_solar_shape: bool | None = None,
    caiso_bidir_intertie: bool | None = None,
    caiso_per_hub_intertie: bool | None = None,
    caiso_perhub_firm_base: bool | None = None,
    caiso_corridor_flow_limit: bool | None = None,
    caiso_intertie_reference_price: bool | None = None,
    caiso_corridor_atc_forward: bool | None = None,
    caiso_reference_price_seam: bool | None = None,
    capacity_deliverability_limits: bool | None = None,
    ramp_limits: bool | None = None,
    local_capacity_constraints: bool | None = None,
    nyiso_local_selfsupply: bool | None = None,
    nyiso_firm_imports: bool | None = None,
    nyiso_import_reconciliation: bool | None = None,
    nyiso_import_hub_prices: bool | None = None,
    nyiso_iroquois_winter_spread: bool | None = None,
    nyiso_synchronised_reserve: bool | None = None,
    nyiso_spin_headroom_frac: float | None = None,
    nyiso_dynamic_reserve_requirements: bool | None = None,
    neiso_dynamic_reserve_requirements: bool | None = None,
    miso_firm_imports: bool | None = None,
    miso_seam_flow_limit: bool = False,
    miso_seam_flow_percentile: float | None = None,
    miso_seam_export_limit: bool = False,
    miso_pjm_border_anchor: bool = False,
    miso_cc_coal_rebalance: bool = False,
    miso_firm_import_floor: bool = False,
    miso_pjm_lmp_import_pricing: bool = False,
    miso_seam_measured_ladder: bool = False,
    pjm_seam_flow_limit: bool = False,
    pjm_seam_flow_percentile: float | None = None,
    pjm_seam_export_limit: bool = False,
    pjm_seam_measured_ladder: bool = False,
    gas_hub_basis_overlay: bool | None = None,
    gas_st_netload_drag: bool = False,
    gas_st_drag_overrides: dict[str, float] | None = None,
    st_gas_intermediate: bool = False,
    st_gas_intermediate_cf_threshold: float | None = None,
    ct_netload_drag: bool | None = None,
    ct_drag_overrides: dict[str, float] | None = None,
    chp_export_floor_measured: bool = False,
    ercot_gtc_limits_measured: bool = False,
    ercot_wtx_curtailment_driver: bool | None = None,
    ercot_wtx_curtail_depth_wind: float | None = None,
    ercot_wtx_curtail_depth_solar: float | None = None,
    mass_cap_enabled: bool = False,
    mass_cap_tons: float | None = None,
    mass_cap_program: str | None = None,
    zero_forcing_ablation: bool = False,
    fleet_only: bool = False,
    xyear_cache: "list | None" = None,
) -> "tuple[object, FleetContext, object | None, dict] | dict":
    """Solve the single-year calibration dispatch for one ISO-year.

    Builds the calibration configuration, loads the EIA-860 generator and
    storage fleets and the year's EIA-930 demand and renewable profiles,
    assembles the marginal-cost array (fuel cost, cycling adders, EAC and
    IRA dispatch credits) and solves the hourly economic dispatch. No
    capacity evolution is performed — the fleet is dispatched as observed.

    Args:
        year: Calibration year.
        iso: ISO identifier.
        hours: Dispatch horizon in hours.
        gas_price: Measured Henry Hub annual price ($/MMBtu).
        ttc_overrides: Optional per-link TTC overrides for a sweep.
        coal_passthrough: Optional PRB coal contract-passthrough override.
        commitment_enabled: When True, run the P2 unit-commitment pass after
            P1 and return the P1 result for comparison.
        commitment_screen_coal: When False, coal is exempt from the P2 screen.
        zero_forcing_ablation: When True, neutralize every merchant floor/
            bridge (keeping only nuclear must-run, CHP steam-following and coal
            take-or-pay) via ``ScenarioConfig.as_zero_forcing_ablation`` after
            all config resolution — the D-3 ablation twin (audit §7 /
            CLAUDE.md rule 20).
        fleet_only: When True, stop after the fleet/storage arrays are built
            and return a state dict instead of solving any LP. Lets a
            post-processor (e.g. the ORDC scarcity overlay,
            ``scripts/derive_ordc_overlay.py``) reconstruct the exact hourly
            availability a persisted bundle solved against — same config,
            same outage overlay, same derates — without re-solving.
        priced_interchange: When True, interchange is served by the priced
            import/export node (import tranches + export sinks in the ISO's
            external zone, the forward-scenario mechanism) instead of the
            measured schedule added to demand. Lets a backcast validate the
            node's calibration against the EIA-930 net-interchange duration
            curve.
        mass_cap_enabled: When True, thread the unified carbon resolver's
            power-sector mass-cap ROW into this calibration year (G-29,
            docs/handoffs/emissions-mass-cap-plan-2026-07.md) instead of the
            default adder path. Default False leaves the calibration harness
            byte-identical (the row was previously unreachable here at all).
            A diagnostic/validation lever only — never a keeper default.
        mass_cap_tons: Optional explicit annual budget (metric tons CO2)
            overriding the ISO program's published schedule; see
            ``policy.cap_and_trade._power_sector_cap``.
        mass_cap_program: Optional cap label override (see
            ``policy.cap_and_trade._power_sector_cap``).

    Returns:
        A tuple ``(result, context, result_p1, p2_state)``. ``result`` is the
        final dispatch (P2 when commitment is enabled, otherwise P1);
        ``result_p1`` is the pre-commitment P1 result when commitment ran,
        else ``None``; ``p2_state`` is the cached P1 input bundle that
        :func:`_commitment_pass` (the P2 post-process) consumes.
    """
    config = backcast_config(
        year,
        iso,
        hours,
        gas_price,
        coal_passthrough,
        commitment_enabled,
        commitment_screen_coal,
        coal_lignite_mustrun,
        coal_prb_mustrun,
        coal_prb_passthrough,
        outage_source,
        coal_prb_passthrough_sigmoid,
        coal_mustrun_per_plant,
        retiree_cems_cap,
        ct_mustrun_per_plant,
        ct_mustrun_floor_frac,
        coal_drop_pof,
        coal_prb_passthrough_tiered,
        offer_curve_overrides=offer_curve_overrides,
        offer_curve_deltas=offer_curve_deltas,
        ercot_offer_surface_conditional=ercot_offer_surface_conditional,
        neiso_offer_surface_conditional=neiso_offer_surface_conditional,
    )
    if gas_st_netload_drag:
        config = config.with_overrides(
            gas_st_netload_drag=True, **(gas_st_drag_overrides or {})
        )
    # Tri-state: None keeps the backcast_config per-ISO default (CAISO
    # keeper default-ON), True/False force the drag on/off — so an A/B arm
    # can run CAISO with the drag scrubbed (--no-ct-netload-drag) without
    # touching the keeper default.
    if ct_netload_drag is not None:
        config = config.with_overrides(ct_netload_drag=bool(ct_netload_drag))
        if ct_netload_drag and ct_drag_overrides:
            config = config.with_overrides(**ct_drag_overrides)
    if chp_export_floor_measured:
        # Measured steam-following export floor (backcast overlay): CHP bins'
        # grid floor rides at the year's measured EIA-923 class CF x the
        # sector grid-delivery share instead of the pooled CAMPD p2 minimum.
        config = config.with_overrides(chp_export_floor_measured=True)
    if ercot_gtc_limits_measured:
        # Measured ERCOT GTC transfer limits (backcast overlay): the GTC-
        # carrying links' export capability follows the hourly NP6-86 series
        # (gtc-limits clean datatype) instead of the static ttc_mw.
        config = config.with_overrides(ercot_gtc_limits_measured=True)
    # ERCOT West Texas Export corridor VRE curtailment-share driver (WP-B):
    # the West/Panhandle wind & solar CF ceiling follows the derived
    # net-load-indexed congestion share (data.curtailment_share) so the
    # sub-zonal Permian/CREZ nodal congestion the 8-zone reduction cannot
    # resolve is represented. depth=0 -> inert (zero-forcing ablation twin).
    # Tri-state (ct_netload_drag pattern): None keeps the backcast_config
    # per-ISO default (ERCOT keeper default-ON, owner GO 2026-07-07);
    # True/False force it on/off so an A/B arm can scrub the driver without
    # touching the keeper default.
    _wtx_overrides: dict = {}
    if ercot_wtx_curtailment_driver is not None:
        _wtx_overrides["ercot_wtx_curtailment_driver"] = bool(
            ercot_wtx_curtailment_driver
        )
    if ercot_wtx_curtail_depth_wind is not None:
        _wtx_overrides["ercot_wtx_curtail_depth_wind"] = float(
            ercot_wtx_curtail_depth_wind
        )
    if ercot_wtx_curtail_depth_solar is not None:
        _wtx_overrides["ercot_wtx_curtail_depth_solar"] = float(
            ercot_wtx_curtail_depth_solar
        )
    if _wtx_overrides:
        config = config.with_overrides(**_wtx_overrides)
    if mass_cap_enabled:
        # G-29 wiring: the calibration harness previously had no path to
        # mass_cap_enabled at all, so the mass-cap row (policy.cap_and_trade
        # .resolve_carbon_program's ROW path) was inert here even though
        # runner.py's forecast path has threaded it since the mass-cap plan
        # landed. Diagnostic-only lever (e.g. the RGGI dual-vs-auction-price
        # probe); never a keeper default.
        config = config.with_overrides(
            mass_cap_enabled=True,
            mass_cap_tons=mass_cap_tons,
            mass_cap_program=mass_cap_program,
        )
    if interchange_shaping:
        config = config.with_overrides(interchange_shaping=True)
    if interchange_shaping_export_only:
        config = config.with_overrides(
            interchange_shaping=True, interchange_shaping_export_only=True
        )
    if reference_price_interface:
        config = config.with_overrides(reference_price_interface=True)
    if coal_takeorpay_from_data:
        # Coal must-run sunk fraction = measured EIA-923 Schedule-5 take-or-pay
        # share per plant (campd_tranche_fuel_frac), not the hardcoded 100%.
        config = config.with_overrides(coal_takeorpay_from_data=True)
    if coal_mustrun_online_pmin:
        # Coal must-run band sized to the measured online-net-MW synchronization
        # Pmin (thermal_tranches mustrun_online_pct), not the all-hours
        # available-CF floor (rebuild step 2).
        config = config.with_overrides(coal_mustrun_online_pmin=True)
    if coal_sync_srmc_tranche:
        # SRMC-priced synchronization tranche (rebuild step 3a): the coal
        # online-Pmin band is split by the measured contract share into a
        # fuel-free _mustrun floor and a full-SRMC _sync band, both forced on so
        # coal holds synchronized at min-load while dispatchable tranches above
        # price-follow.
        config = config.with_overrides(coal_sync_srmc_tranche=True)
    if ct_intermediate_split:
        # Route the measured intermediate-duty CT cohort
        # (fleet.ct_intermediate_plants) to the flatter CT_INTERMEDIATE offer
        # curve so their always-on energy clears instead of carrying the steep
        # true-peaker start-cost hurdle (the CT_PEAKER-under / CC-over miss).
        config = config.with_overrides(ct_intermediate_split=True)
    if ct_intermediate_cf_threshold is not None:
        config = config.with_overrides(
            ct_intermediate_cf_threshold=float(ct_intermediate_cf_threshold)
        )
    if cc_intermediate_split:
        # Route the measured baseload-duty CC cohort (fleet.cc_intermediate_plants)
        # to the flatter CC_INTERMEDIATE offer curve so the upper operating-range
        # tranches of MISO's near-baseload CC fleet clear instead of carrying the
        # ERCOT-peaker-fit rising econ ramp (the 2023/2024 gas-CC under-run). Only
        # the operating-range ramp is corrected; the duct-burner peak is unchanged.
        config = config.with_overrides(cc_intermediate_split=True)
    if cc_intermediate_cf_threshold is not None:
        config = config.with_overrides(
            cc_intermediate_cf_threshold=float(cc_intermediate_cf_threshold)
        )
    if tranche_startup_amortization:
        # Fast-start tranche pricing (ISO-NE Order 825 analogue): the gas
        # bins' econ/peak tranches carry the same NREL start cost as the
        # committed anchor, so the P1 markup amortizes each tranche's own P0
        # run lengths into its bid — the fuel-price-invariant commitment-cost
        # component of the real offer stack the HR-multiplier curve cannot
        # express (winter over- / summer-evening under-pricing signature).
        config = config.with_overrides(tranche_startup_amortization=True)
    if tranche_startup_measured_runs:
        # v3 measured-run-length basis: the simple-cycle CT tranches amortize
        # over the CAMPD-measured median start-to-stop run length
        # (derive_campd_ct_run_lengths.py artifact) as the horizon ceiling —
        # P0 runs may only shorten it — removing the v2 circularity where
        # too-cheap offers → long P0 blocks → ≈0 markup (nyiso-44 finding).
        config = config.with_overrides(tranche_startup_measured_runs=True)
    if nysdec_peaker_rule_availability:
        # NYSDEC 6 NYCRR 227-3 peaker-rule availability overlay: curated
        # unit-level ozone-season compliance windows (Gold Book IV-3..IV-6),
        # availability only, never an offer/price change (rule #12 class of
        # the CAMPD outage windows).
        config = config.with_overrides(nysdec_peaker_rule_availability=True)
    if oil_primary_bin_fuel:
        # Measured EIA-860 oil-primary fuel correction (plant-registry screen
        # unioned with the generator-level Energy-Source-1 majority screen);
        # CLI-explicit counterpart of the legacy ERCOT_OIL_PRIMARY env gate.
        config = config.with_overrides(oil_primary_bin_fuel=True)
    if st_gas_intermediate:
        # MISO intermediate gas-steam structure (one consolidated lever, default
        # OFF → prior keepers / other ISOs byte-identical). The legacy gas-steam
        # fleet (Harding Street, Ames, Nine Mile Pt, Lewis Creek, Sabine, ...)
        # runs intermediate-duty, not as peakers, but inherits ERCOT-fitted steam
        # parameters that under-run it (Moselle / Lewis Creek) and let it cycle
        # with peaker agility. Three coupled corrections, each well-grounded:
        #  1. route the measured median-CF cohort (fleet.st_gas_intermediate_plants)
        #     to the flatter ST_GAS_INTERMEDIATE offer curve so its sustained
        #     energy clears;
        #  2. the ST_GAS startup cost + min-run feed the P1 bid markup so a
        #     stop-start costs more than idling (steam drags, not cycles);
        #  3. replace the ERCOT-fitted ST_GAS WEFOR base (0.21, >2x every other
        #     thermal class) with a realistic NERC-GADS gas-steam EFOR, lifting
        #     the implicit availability crush off MISO's net-summer-rated steam.
        # NOTE: the net-load reliability-drag floor (the Little Gypsy / River
        # load-pocket weather-dependent must-run) is deliberately NOT enabled
        # here. Its ScenarioConfig coefficients are ERCOT-derived and SATURATE at
        # the 0.34 cap across all of MISO's larger net-load range (60-110 GW),
        # degenerating into a flat 34% must-run rather than the weather-responsive
        # curve intended — borrowed coefficients, not a MISO mechanism. It needs
        # a MISO-specific regression (MISO overnight ST_GAS CAMPD CF vs MISO
        # net-load), mirroring the ERCOT/NYISO/CAISO per-ISO floor derivations,
        # before it can be a keeper lever. Tracked as the immediate follow-up;
        # enable per-run via --gas-st-netload-drag once MISO coefficients exist.
        config = config.with_overrides(
            st_gas_intermediate_split=True,
            gas_st_startup_cost=True,
            gas_st_wefor_base_override=0.10,
        )
    if st_gas_intermediate_cf_threshold is not None:
        config = config.with_overrides(
            st_gas_intermediate_cf_threshold=float(st_gas_intermediate_cf_threshold)
        )
    # Tri-state overrides: None = keep the per-ISO base default from
    # backcast_config (CAISO defaults the RA floor + negative offers ON, the
    # validated keeper); an explicit True/False from the CLI overrides it (so a
    # no-floor baseline probe is --no-caiso-gas-commitment-floor).
    if negative_renewable_offers is not None:
        config = config.with_overrides(
            negative_renewable_offers=negative_renewable_offers
        )
    if caiso_gas_commitment_floor is not None:
        config = config.with_overrides(
            caiso_gas_commitment_floor=caiso_gas_commitment_floor
        )
    if caiso_gas_floor_frac is not None:
        config = config.with_overrides(caiso_gas_floor_frac=caiso_gas_floor_frac)
    if caiso_ra_mustoffer is not None:
        config = config.with_overrides(caiso_ra_mustoffer=caiso_ra_mustoffer)
    if caiso_ra_min_load_frac is not None:
        config = config.with_overrides(caiso_ra_min_load_frac=caiso_ra_min_load_frac)
    if caiso_ra_startup_bridge is not None:
        config = config.with_overrides(caiso_ra_startup_bridge=caiso_ra_startup_bridge)
    if caiso_ra_bridge_decommit is not None:
        config = config.with_overrides(
            caiso_ra_bridge_decommit=caiso_ra_bridge_decommit
        )
    if reliability_floor is not None:
        config = config.with_overrides(reliability_floor=reliability_floor)
    if reliability_floor_overrides is not None:
        config = config.with_overrides(
            reliability_floor_overrides=reliability_floor_overrides
        )
    if scarcity_price_overlay is not None:
        config = config.with_overrides(
            scarcity_pricing_enabled=scarcity_price_overlay,
            scarcity_price_overlay=scarcity_price_overlay,
        )
    if caiso_scarcity_pricing is not None:
        config = config.with_overrides(
            scarcity_pricing_enabled=True,
            caiso_scarcity_pricing=caiso_scarcity_pricing,
        )
    if caiso_lcr_commitment_credit is not None:
        config = config.with_overrides(
            caiso_lcr_commitment_credit=caiso_lcr_commitment_credit,
        )
    if caiso_solar_deliverability is not None:
        config = config.with_overrides(
            caiso_solar_deliverability=caiso_solar_deliverability
        )
    if caiso_solar_deliverability_k is not None:
        config = config.with_overrides(
            caiso_solar_deliverability_k=caiso_solar_deliverability_k
        )
    if caiso_solar_endogenous_spill is not None:
        config = config.with_overrides(
            caiso_solar_endogenous_spill=caiso_solar_endogenous_spill
        )
    if caiso_solar_cap_at_delivered is not None:
        config = config.with_overrides(
            caiso_solar_cap_at_delivered=caiso_solar_cap_at_delivered
        )
    if neiso_gas_coldsnap_derate is not None:
        config = config.with_overrides(
            neiso_gas_coldsnap_derate=neiso_gas_coldsnap_derate
        )
    if neiso_oil_burn_budget is not None:
        config = config.with_overrides(neiso_oil_burn_budget=neiso_oil_burn_budget)
    if neiso_winter_fuel_inventory is not None:
        config = config.with_overrides(
            neiso_winter_fuel_inventory=neiso_winter_fuel_inventory
        )
    if neiso_winter_fuel_start_fill_bbl is not None:
        config = config.with_overrides(
            neiso_winter_fuel_start_fill_bbl=neiso_winter_fuel_start_fill_bbl
        )
    if neiso_winter_fuel_mustrun is not None:
        config = config.with_overrides(
            neiso_winter_fuel_mustrun=neiso_winter_fuel_mustrun
        )
    if caiso_import_hub_prices is not None:
        config = config.with_overrides(caiso_import_hub_prices=caiso_import_hub_prices)
    if caiso_import_gas_coupling is not None:
        config = config.with_overrides(
            caiso_import_gas_coupling=caiso_import_gas_coupling
        )
    if caiso_import_solar_shape is not None:
        config = config.with_overrides(
            caiso_import_solar_shape=caiso_import_solar_shape
        )
    if caiso_bidir_intertie is not None:
        config = config.with_overrides(caiso_bidir_intertie=caiso_bidir_intertie)
    if caiso_per_hub_intertie is not None:
        config = config.with_overrides(caiso_per_hub_intertie=caiso_per_hub_intertie)
    if caiso_perhub_firm_base is not None:
        config = config.with_overrides(caiso_perhub_firm_base=caiso_perhub_firm_base)
    if caiso_corridor_flow_limit is not None:
        config = config.with_overrides(
            caiso_corridor_flow_limit=caiso_corridor_flow_limit
        )
    if caiso_intertie_reference_price is not None:
        config = config.with_overrides(
            caiso_intertie_reference_price=caiso_intertie_reference_price
        )
    if caiso_corridor_atc_forward is not None:
        config = config.with_overrides(
            caiso_corridor_atc_forward=caiso_corridor_atc_forward
        )
    if caiso_reference_price_seam is not None:
        config = config.with_overrides(
            caiso_reference_price_seam=caiso_reference_price_seam
        )
    if capacity_deliverability_limits is not None:
        config = config.with_overrides(
            capacity_deliverability_limits=capacity_deliverability_limits
        )
    if ramp_limits is not None:
        config = config.with_overrides(ramp_limits=ramp_limits)
    if local_capacity_constraints is not None:
        config = config.with_overrides(
            local_capacity_constraints=local_capacity_constraints
        )
    if nyiso_local_selfsupply is not None:
        config = config.with_overrides(nyiso_local_selfsupply=nyiso_local_selfsupply)
    if nyiso_firm_imports is not None:
        config = config.with_overrides(nyiso_firm_imports=nyiso_firm_imports)
    if nyiso_import_reconciliation is not None:
        config = config.with_overrides(
            nyiso_import_reconciliation=nyiso_import_reconciliation
        )
    if nyiso_import_hub_prices is not None:
        config = config.with_overrides(nyiso_import_hub_prices=nyiso_import_hub_prices)
    if nyiso_iroquois_winter_spread is not None:
        config = config.with_overrides(
            nyiso_iroquois_winter_spread=nyiso_iroquois_winter_spread
        )
    if nyiso_synchronised_reserve is not None:
        config = config.with_overrides(
            nyiso_synchronised_reserve=nyiso_synchronised_reserve
        )
    if nyiso_spin_headroom_frac is not None:
        config = config.with_overrides(
            nyiso_spin_headroom_frac=nyiso_spin_headroom_frac
        )
    if nyiso_dynamic_reserve_requirements is not None:
        config = config.with_overrides(
            nyiso_dynamic_reserve_requirements=nyiso_dynamic_reserve_requirements
        )
    if neiso_dynamic_reserve_requirements is not None:
        config = config.with_overrides(
            neiso_dynamic_reserve_requirements=neiso_dynamic_reserve_requirements
        )
    if miso_firm_imports is not None:
        config = config.with_overrides(miso_firm_imports=miso_firm_imports)
    if miso_seam_flow_limit:
        config = config.with_overrides(miso_seam_flow_limit=True)
    if miso_seam_flow_percentile is not None:
        # Round-2 import-lift: raise the seam deliverability percentile (p90 ->
        # e.g. p95) so the priced seam clears more import in tight hours. Only
        # bites with --miso-seam-flow-limit; still a measured-duration ceiling.
        config = config.with_overrides(
            miso_seam_flow_percentile=float(miso_seam_flow_percentile)
        )
    if miso_seam_export_limit:
        config = config.with_overrides(miso_seam_export_limit=True)
    if pjm_seam_flow_limit:
        config = config.with_overrides(pjm_seam_flow_limit=True)
    if pjm_seam_flow_percentile is not None:
        config = config.with_overrides(
            pjm_seam_flow_percentile=float(pjm_seam_flow_percentile)
        )
    if pjm_seam_export_limit:
        config = config.with_overrides(pjm_seam_export_limit=True)
    if pjm_seam_measured_ladder:
        config = config.with_overrides(pjm_seam_measured_ladder=True)
    if miso_pjm_border_anchor:
        config = config.with_overrides(miso_pjm_border_anchor=True)
    if miso_cc_coal_rebalance and iso.upper() == "MISO":
        # Raise the MISO CC_REGULAR / COAL_BIT offer curve so the marginal CC /
        # coal-bit MWh sits above the priced-import hurdle (and the under-running
        # CT_PEAKER / ST_GAS), correcting the cheap-domestic-fill-eats-imports
        # miss. ISO-gated (other ISOs / forecasts byte-identical); applied as a
        # deep-merge offer-curve override on top of the calibrated MISO curve.
        rebalanced = _deep_merge_offer_curve(
            config.offer_curve_by_group, _MISO_CC_COAL_REBALANCE
        )
        config = config.with_overrides(
            offer_curve_by_group=rebalanced, miso_cc_coal_rebalance=True
        )
    if miso_firm_import_floor:
        # Firm (must-flow) import floor on the reference-price seam — forces the
        # measured near-firm PJM/IESO net-import base so the seam stops wrongly
        # net-exporting (fixes the import shortfall + 2025 energy-balance overshoot
        # by displacing the over-running domestic coal/CC). Requires the priced
        # interface; MISO-only (only the PJM seam carries a floor).
        config = config.with_overrides(miso_firm_import_floor=True)
    if miso_pjm_lmp_import_pricing:
        config = config.with_overrides(miso_pjm_lmp_import_pricing=True)
    if miso_seam_measured_ladder:
        config = config.with_overrides(miso_seam_measured_ladder=True)
    if gas_hub_basis_overlay is not None:
        config = config.with_overrides(gas_hub_basis_overlay=gas_hub_basis_overlay)
    # Per-run PRB passthrough sigmoid floor/ceiling tune (run_calibration_full
    # --prb-* flags); None entries leave the ScenarioConfig default in place.
    if prb_overrides:
        config = config.with_overrides(
            **{k: v for k, v in prb_overrides.items() if v is not None}
        )
    # Gas-keyed coal passthrough sigmoids per supply chain. The bit family
    # has its own flag/overrides; the sub/lignite enables and all their
    # tuning params ride the generic prb_overrides ScenarioConfig override
    # channel (run_calibration_full --coal-{sub,lignite}-sigmoid and the
    # --{sub,lignite}-* flags). Params left at None resolve from the
    # per-ISO COAL_SIGMOID_DEFAULTS table (fuel.coal_sigmoid_params).
    if coal_bit_sigmoid:
        config = config.with_overrides(coal_bit_passthrough_sigmoid=True)
    if bit_overrides:
        config = config.with_overrides(
            **{k: v for k, v in bit_overrides.items() if v is not None}
        )
    # Marginal-coal measured-SRMC offer bound (run_calibration_full
    # --coal-econ-srmc-bound): clamp the econ*/peak coal tranches' fuel
    # passthrough to >= 1.0 so the marginal coal offer never sits below the
    # plant's measured F923 incremental delivered SRMC; the committed/
    # must-run bands keep the contracted take-or-pay discount
    # (fleet.campd_tranche_fuel_frac; ScenarioConfig.coal_econ_srmc_bound).
    if coal_econ_srmc_bound:
        config = config.with_overrides(coal_econ_srmc_bound=True)
    # Per-plant tranche-config override sheet (run_calibration_full
    # --plant-tranche-config): each listed plant's tranche shares + band HR
    # multipliers come straight from the CSV, bypassing the offer curve.
    if plant_tranche_config:
        config = config.with_overrides(plant_tranche_config_path=plant_tranche_config)
    # Daily SOC-cycling cap (run_calibration_full --storage-daily-cycling):
    # bounds storage perfect foresight to within-day arbitrage.
    if storage_daily_cycling:
        config = config.with_overrides(storage_daily_cycling=True)
    if storage_vintage_ramp:
        config = config.with_overrides(storage_vintage_ramp=True)
    # AS reserve withholding (run_calibration_full --as-reserve-withholding):
    # remove the measured cleared reserve MW from the gas/flexible-thermal
    # headroom before the energy supply curve clears (ERCOT up-AS / PJM Primary
    # Reserve requirement; fleet.generators_to_fleet_arrays).
    if as_reserve_withholding:
        config = config.with_overrides(as_reserve_withholding=True)
    # CAISO formula-based operating-reserve withholding (run_calibration_full
    # --as-reserve-formula): withhold R(t) = max(MSSC, 0.067*load) + 0.01*load
    # (WECC MORC + 1% regulation-up) from gas top-of-merit headroom; CAISO-only,
    # the default-off scaffold until OASIS cleared-AS data can be pulled
    # (fleet.caiso_operating_reserve_mw / generators_to_fleet_arrays).
    if as_reserve_formula:
        config = config.with_overrides(as_reserve_formula=True)
    # Energy+reserve co-optimization (run_calibration_full
    # --energy-reserve-coopt): co-optimize energy and Primary Reserve inside the
    # LP (structural 1.5 x MSSC requirement + published ORDC demand curve);
    # PJM-gated in _run_dispatch. Replaces the post-solve ORDC overlay.
    if energy_reserve_coopt:
        config = config.with_overrides(energy_reserve_coopt=True)
    # MISO locational (zonal) reserve families on top of the market-wide RBDC
    # (run_calibration_full --miso-zonal-reserves): BPM-002 §3.3.2 zonal
    # minimum requirements priced at the published §5.2.1.2 zonal curve.
    if miso_zonal_reserves:
        config = config.with_overrides(miso_zonal_reserves=True)
    # MISO per-asset (zone x fuel-class pooled) 10-min-ramp-bounded reserve
    # columns (run_calibration_full --miso-reserve-pergen): reserve competes
    # with energy on the marginal pool and cleared reserve is capped at the
    # deliverable 10-minute ramp, so the RBDC / zonal ORDC families can run
    # short (reserve_config._miso_design pergen branch).
    if miso_reserve_pergen:
        config = config.with_overrides(miso_reserve_pergen=True)
    # Pooled linear commitment-posture lever on the pergen pools (design note
    # docs/multi-iso/miso-scarcity-posture-design-2026-07.md §A).
    if miso_commitment_posture:
        config = config.with_overrides(miso_commitment_posture=True)
    if ercot_multiproduct_as_coopt:
        config = config.with_overrides(ercot_multiproduct_as_coopt=True)
    # Published pre-reform ECRS deployment design (no price-based release
    # through 2024-07-31 -> at-cap demand step; standing ramp after): see
    # reserve_config.ERCOT_ECRS_RELEASE_REFORM_* citations.
    if ercot_ecrs_conservative_deployment:
        config = config.with_overrides(ercot_ecrs_conservative_deployment=True)
    # Lumped ORDC total-reserve family (RTORPA) layered on the product stack:
    # see ScenarioConfig.ercot_ordc_total_reserve / reserve_config.
    if ercot_ordc_total_reserve:
        config = config.with_overrides(ercot_ordc_total_reserve=True)
    # Measured battery AS award netted off the fast products' requirements
    # (multi-product measured-storage path): reserve_config.
    if ercot_storage_as_product_credit:
        config = config.with_overrides(ercot_storage_as_product_credit=True)
    # Measured HH monthly gas shape (level-preserving): fuel.gas_seasonal_shape.
    if gas_hh_monthly_shape:
        config = config.with_overrides(gas_hh_monthly_shape=True)
    if ercot_as_aware_commitment:
        config = config.with_overrides(ercot_as_aware_commitment=True)
    if ercot_reserve_supply_cap:
        config = config.with_overrides(
            ercot_reserve_supply_cap=True,
            ercot_reserve_supply_cap_from_year=ercot_reserve_supply_cap_from_year,
        )
    if ercot_reserve_supply_forward:
        config = config.with_overrides(ercot_reserve_supply_forward=True)
    if pjm_reserve_supply_cap:
        config = config.with_overrides(pjm_reserve_supply_cap=True)
    if pjm_reserve_online_gated:
        config = config.with_overrides(
            pjm_reserve_online_gated=True,
            pjm_reserve_online_rho=pjm_reserve_online_rho,
        )
    if pjm_reserve_commitment_scoped:
        # PJM path B (G-20b): commitment-scoped reserve supply — fa_p2-style
        # availability mask from the P0 run pattern at the P0->P1 seam +
        # deliverable supply cap recomputed on the masked fleet
        # (pipeline.commitment.build_pjm_reserve_p1_prep). GATED default off.
        config = config.with_overrides(pjm_reserve_commitment_scoped=True)
    if pjm_reserve_pergen:
        config = config.with_overrides(pjm_reserve_pergen=True)
    if pjm_reserve_pergen_sync:
        # PJM per-gen OPPORTUNITY-COST co-opt (G-20b successor): Synchronized
        # sub-product families + per-pool sync/non-sync column split, sync
        # caps online-scoped at the P0->P1 seam
        # (pipeline.commitment.build_pjm_reserve_p1_prep). Requires
        # pjm_reserve_pergen. GATED default off.
        config = config.with_overrides(pjm_reserve_pergen_sync=True)
    if pjm_reserve_pergen_size_split:
        # PJM pergen SIZE-SPLIT pooling tier (pjm-87 diagnosis remedy):
        # splits each (zone, fuel-class) pool's large plants into individual
        # columns, self-normalizing threshold (reserve_config.
        # PJM_PERGEN_SIZE_SPLIT_MEAN_MULTIPLE). Requires pjm_reserve_pergen.
        # GATED default off.
        config = config.with_overrides(pjm_reserve_pergen_size_split=True)
    if pjm_commitment_posture:
        # PJM commitment-posture lever (design note §A ported; requires the
        # pergen reserve co-opt). U/SU columns on non-fast-start pools; zero
        # fitted parameters. GATED default off.
        config = config.with_overrides(pjm_commitment_posture=True)
    if measured_ramp_capability:
        # Measured EIA-860/CAMPD ramp-capability reconciliation of the class
        # ramp10 fractions (data/ramp_capability.py; rule 14 measured-over-
        # estimate). Consumed at fleet build; GATED default off.
        config = config.with_overrides(measured_ramp_capability=True)
    if ercot_as_forward_requirement:
        config = config.with_overrides(ercot_as_forward_requirement=True)
    # ERCOT load-resource reserve credit (run_calibration_full
    # --ercot-load-resource-reserve): credit measured RRS-UFR (load-side
    # responsive reserve) into the co-opt reserve balance. GATED — alters
    # dispatch volumes. ERCOT co-opt only; a no-op otherwise.
    if ercot_load_resource_reserve:
        config = config.with_overrides(
            ercot_load_resource_reserve=True,
            ercot_load_resource_reserve_from_year=int(
                ercot_load_resource_reserve_from_year
            ),
        )
    # ERCOT storage-AS reserve credit (run_calibration_full
    # --ercot-storage-as-reserve): credit the measured battery-provided AS back
    # into the co-opt reserve balance — storage_as_commitment removes it from the
    # reserve cap, so the committed battery AS would otherwise be dropped from
    # reserve supply. GATED; ERCOT co-opt + storage_as_commitment only.
    if ercot_storage_as_reserve:
        config = config.with_overrides(
            ercot_storage_as_reserve=True,
            ercot_storage_as_reserve_from_year=int(ercot_storage_as_reserve_from_year),
        )
    if ercot_ecrs_requirement:
        config = config.with_overrides(
            ercot_ecrs_requirement=True,
            ercot_ecrs_requirement_from_year=int(ercot_ecrs_requirement_from_year),
        )
    # Published ORDC LOLP table (run_calibration_full --ordc-lolp-params-path):
    # replace the neutral flat fallback (mu=0) with ERCOT's published NP6-576-ER
    # seasonal/TOD mu/sigma so the co-opt reserve demand curve sits at the real
    # reserve level the adder begins to bite. Grounded input, not a price fit.
    if ordc_lolp_params_path:
        config = config.with_overrides(ordc_lolp_params_path=str(ordc_lolp_params_path))
    # Storage AS commitment (run_calibration_full --storage-as-commitment):
    # ERCOT-only reservation of measured storage up-AS MW from the battery
    # dispatch power cap (applied after storage_cap_profiles below).
    if storage_as_commitment:
        config = config.with_overrides(storage_as_commitment=True)
    # Endogenous storage energy-vs-AS co-opt (run_calibration_full
    # --ercot-storage-as-endogenous, G5): the battery CHOOSES energy vs upward-AS
    # inside the multi-product co-opt, replacing the measured-award reservation.
    # Full battery cap to the co-opt (no measured subtraction below), the measured
    # reserve credit guarded off (scarcity.ercot_*_coopt_inputs), and the cleared
    # storage AS counts toward the measured RTOLCAP supply cap. Takes precedence
    # over storage_as_commitment when both are set.
    if ercot_storage_as_endogenous:
        config = config.with_overrides(ercot_storage_as_endogenous=True)
    if ercot_storage_as_duration_gate:
        config = config.with_overrides(ercot_storage_as_duration_gate=True)
    # Battery throughput/cycling cost (run_calibration_full --battery-adder):
    # per-MWh-discharged adder that tames LP over-cycling of the BESS fleet.
    # CAISO defaults to $5/MWh when no explicit adder is passed: the 10+ GW
    # fleet with perfect-foresight LP over-cycles without a throughput cost
    # proxy for degradation + ancillary-service opportunity cost.
    _batt_adder = battery_dispatch_adder
    if not _batt_adder and iso.upper() == "CAISO":
        _batt_adder = 5.0
    if _batt_adder:
        config = config.with_overrides(battery_dispatch_adder=_batt_adder)
    if gas_offer_curve:
        config = config.with_overrides(gas_offer_curve=True)
    # Measured ISO-month delivered gas (EIA-923) instead of annual + shape.
    if gas_monthly_actuals:
        config = config.with_overrides(gas_monthly_actuals=True)
    # PJM per-zone gas basis (opens the west-cheap / east-dear spread so PJM
    # stops clearing as a single copper-plate). No-op for non-PJM ISOs — the
    # apply gates on iso == "PJM" — so setting it here is safe regardless.
    if pjm_zonal_gas_basis:
        config = config.with_overrides(pjm_zonal_gas_basis=True)
    # MISO per-zone gas basis (opens the north/south gas gradient). No-op for
    # non-MISO ISOs — the apply gates on iso == "MISO".
    if miso_zonal_gas_basis:
        config = config.with_overrides(miso_zonal_gas_basis=True)
    # PJM transmission-congestion lever (break the copper-plate): cap the priced
    # external star node to the measured per-border interchange envelope + tighten
    # the internal interfaces to their measured transfer limits. Wired below at
    # the interface-group / TTC build; no-op for non-PJM ISOs.
    if pjm_congestion:
        config = config.with_overrides(pjm_congestion=True)
    # Econ-ramp rendering sweep (run_calibration_full --curve-n / --curve-exp):
    # offer_curve_smoothing_n / offer_curve_smoothing_exp; None entries keep
    # the ScenarioConfig defaults.
    if curve_smoothing:
        config = config.with_overrides(
            **{k: v for k, v in curve_smoothing.items() if v is not None}
        )
    # Top-of-stack outage allocation for CC_REGULAR (run_calibration_full
    # --cc-derate-from-top): partial outages truncate the expensive end of
    # the offer curve instead of scaling every tranche pro-rata. CAISO
    # defaults ON: per-plant peaking bands are narrow (0-4%), so pro-rata
    # derates crush the committed floor and prevent 0% CF hours.
    if cc_derate_from_top or iso.upper() == "CAISO":
        config = config.with_overrides(cc_outage_derate_from_top=True)
    if cc_nameplate_summer_derate:
        config = config.with_overrides(cc_nameplate_summer_derate=True)
    if coal_nameplate_summer_derate:
        config = config.with_overrides(coal_nameplate_summer_derate=True)
    if gt_ambient_derate:
        # Physics-grounded GT ambient-temperature derate on the hottest hours
        # (fleet.generators_to_fleet_arrays). Slopes/reference default to the
        # ScenarioConfig physical values unless the caller overrides them.
        _amb = {"gt_ambient_derate": True}
        if gt_ambient_derate_ref_c is not None:
            _amb["gt_ambient_derate_ref_c"] = float(gt_ambient_derate_ref_c)
        if gt_ambient_derate_slope_cc is not None:
            _amb["gt_ambient_derate_slope_cc"] = float(gt_ambient_derate_slope_cc)
        if gt_ambient_derate_slope_ct is not None:
            _amb["gt_ambient_derate_slope_ct"] = float(gt_ambient_derate_slope_ct)
        config = config.with_overrides(**_amb)
    if temp_dependent_derate:
        # Temperature-dependent capacity derate: replaces the flat EIA-860
        # net-summer derate with a per-class physical curve in measured hourly
        # zone dry-bulb temperature (fleet.generators_to_fleet_arrays). Slopes/
        # reference temps default to the ScenarioConfig physical values.
        config = config.with_overrides(temp_dependent_derate=True)
    if zero_forcing_ablation:
        # D-3 zero-forcing ablation twin (audit §7 / CLAUDE.md rule 20): drop
        # every MERCHANT floor/bridge, keeping only the structural must-run set
        # (nuclear / CHP-steam / coal take-or-pay). Applied AFTER every per-ISO
        # default and with_overrides so the floors go off regardless of how they
        # were set — the CAISO ct_netload_drag / caiso_ra_mustoffer defaults are
        # config-level (not kwargs), so only a config transform can neutralize
        # them. The off-list is derived from the D-2 mechanism registry, so a
        # new floor is ablated by default (see ScenarioConfig.as_zero_forcing_
        # ablation / data.floor_mechanisms.zero_forcing_field_overrides).
        config = ScenarioConfig.as_zero_forcing_ablation(config)
    # Point the EIA-860 loaders at a year-matched vintage when the scenario asks
    # for one (backcast knob; None resets to the canonical 2025ER snapshot the
    # COD ramp filters to the solved year). Must precede every fleet / storage /
    # renewable / COD-map load below so they all read the same vintage.
    from market_sim.config.paths import set_eia860_vintage

    set_eia860_vintage(
        config.eia860_vintage_year if config.mode == "backcast" else None
    )
    iso_config = get_iso_config(iso)
    # Year-varying interface limits (e.g. NYISO Central-East jumps with the AC
    # Transmission project in service Dec 2023) — applied before the import
    # node joins so the corrected links flow through the whole solve.
    iso_config = _apply_iso_year_ttc(iso_config, iso, year)
    # Priced import/export node (orchestrator-unification Stage 5): the
    # builder choice — reference-price seam vs CAISO per-hub / bidirectional
    # intertie vs the static year-grounded tranche ladder, plus the Manitoba
    # firm-import block — is resolved by the SHARED
    # config/interchange_config.get_interchange_spec (the same spec the
    # forecast runner consumes), and the generators come from the shared
    # build_interchange_fleet, which delegates to the canonical
    # transmission.py builders. The external zone joins the topology and its
    # import tranches + export sinks join the fleet below; the measured
    # interchange schedule then stays out of demand (no double count).
    import_generators: list = []
    # Default the CAISO corridor intertie flag so the later corridor-limit
    # and forward-ATC checks are bound on every path; it is only set inside
    # the priced-interchange block below (CAISO-only), so a non-priced or
    # non-CAISO run keeps it False.
    caiso_corridors = False
    if priced_interchange:
        # CARB levies its cap-and-trade allowance on unspecified WECC imports
        # (border carbon adjustment, EF 0.428 t/MWh x allowance), so every
        # CAISO import tranche carries it in its delivered cost — the same
        # adder the production runner applies (model.runner). It is NOT on the
        # export sinks (exports owe no CA compliance cost). Resolved at the
        # backcast year's carbon price (each calibration solve is single-year).
        border_carbon = (
            wecc_border_carbon_adder(resolve_carbon_price(config, year))
            if iso == "CAISO"
            else 0.0
        )
        interchange_spec = get_interchange_spec(config, iso, year=year)
        caiso_corridors = interchange_spec.use_corridors
        import_generators = build_interchange_fleet(interchange_spec, border_carbon)
        # Shared topology sequence (same order as always): external node
        # extension, the capacity-deliverability Part-A seam import cap
        # (backcast mirror of the runner hook — the published per-area MIC
        # replaces the calibrated simultaneous-import scalar, resolved for
        # THIS backcast year's delivery year; no-op off the default-off flag
        # or when the clean data is absent), then the CAISO per-hub corridor
        # split re-homing the import links + simultaneous cap onto the
        # corridor zones the per-hub / reference-seam builder used.
        iso_config = apply_interchange_topology(
            iso_config,
            interchange_spec,
            config,
            year=year,
            extend_node=True,
        )
    zone_names = iso_config.zone_names

    demand = load_demand(
        iso,
        year,
        iso_config,
        td_loss_factor=config.td_loss_factor,
        include_interchange=not priced_interchange,
    )
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        iso, year, iso_config, config
    )
    if config.hours < demand.shape[1]:
        demand = demand[:, : config.hours]
        wind_cf = wind_cf[:, : config.hours]
        solar_cf = solar_cf[:, : config.hours]

    # CAISO Lever-D: re-curtail the uncurtailed HSL solar potential the dispatch
    # is handed. The reduced 3-zone topology cannot see the sub-area / local
    # congestion that drives ~70% of CAISO solar curtailment, so the LP runs the
    # full potential and curtails ~0 (docs/caiso-lever-audit-2026-06.md, Lever D).
    solar_cf = _apply_caiso_solar_deliverability(solar_cf, iso, year, config)

    # Must-run "other" resources (biomass, process gas, ...) serve load
    # exogenously — they run for industrial/process reasons, not LP economics —
    # so net them out of demand before the dispatch so they displace marginal
    # gas instead of being double-counted on top of a fully-served balance.
    if must_run_mw is not None:
        mr = np.asarray(must_run_mw, dtype=float)
        if mr.shape[1] > config.hours:
            mr = mr[:, : config.hours]
        demand = np.maximum(demand - mr, 0.0)

    incidence = build_incidence_matrix(iso_config.links, zone_names)
    ttc = _apply_ttc_overrides(
        iso_config, get_ttc_array(iso_config.links), ttc_overrides
    )
    # PJM congestion lever (Lever B): tighten the internal interfaces with a
    # confident measured mapping to their measured PJM transfer-limit postings
    # (constants.PJM_MEASURED_INTERNAL_TTC). Applied to the scalar TTC array before
    # the monthly expansion; no-op off the flag or for non-PJM ISOs.
    if getattr(config, "pjm_congestion", False) and iso == "PJM":
        from market_sim.config.constants import PJM_MEASURED_INTERNAL_TTC

        ttc = ttc.copy()
        for i, link in enumerate(iso_config.links):
            measured = PJM_MEASURED_INTERNAL_TTC.get((link.from_zone, link.to_zone))
            if measured is not None and measured != ttc[i]:
                logger.info(
                    "PJM congestion: internal TTC %s->%s %.0f -> %.0f MW "
                    "(measured transfer-limit posting)",
                    link.from_zone,
                    link.to_zone,
                    ttc[i],
                    measured,
                )
                ttc[i] = measured
    # Seasonal interface envelope: expand the scalar TTC to a per-hour matrix
    # where a measured monthly limit exists (NYISO Central-East). No-op (1-D)
    # for ISOs/years without one.
    ttc = _apply_iso_monthly_ttc(ttc, iso_config, iso, year, demand.shape[1])
    # NYISO Zone-K LCR/TSL mechanism (issue #1345, config.nyiso_li_lcr_tsl):
    # cap the NYC->Long_Island link at the published locality import limit in
    # the HB14-21 design-condition window, replacing the Long_Island 0.45
    # self-supply energy floor (excluded below — rule 19, one mechanism per
    # phenomenon). LI reliability energy then clears economically behind a
    # published limit instead of through a forced min_gen floor.
    if getattr(config, "nyiso_li_lcr_tsl", False):
        from market_sim.model.transmission import apply_nyiso_li_tsl_import_cap

        ttc = apply_nyiso_li_tsl_import_cap(ttc, iso_config, iso, year, demand.shape[1])
        logger.info(
            "%s %d: Zone-K LCR/TSL import cap on NYC->Long_Island (HB14-21, "
            "published locality import limit; replaces the LI self-supply "
            "energy floor)",
            iso,
            year,
        )
    # Measured ERCOT GTC export limits (backcast overlay, ScenarioConfig.
    # ercot_gtc_limits_measured): the GTC-carrying links' export direction
    # follows the hourly NP6-86 measured limit series so West/Panhandle
    # curtailment emerges endogenously from the binding published limits.
    # Applied only when the year ALSO has measured HSL renewable potential —
    # without it the renewable upper bound is the delivered actuals
    # (EIA-930-as-CF) and any binding export cap would double-curtail wind
    # below what really flowed. The import direction keeps the static rating
    # (a GTC is an export stability limit).
    ttc_import = None
    if getattr(config, "ercot_gtc_limits_measured", False) and iso == "ERCOT":
        from market_sim.data.gtc import ercot_gtc_ttc_hourly

        if load_hsl_hourly(iso, year) is None:
            logger.warning(
                "ercot_gtc_limits_measured: %d has no measured HSL potential "
                "(renewables ride delivered-as-CF) — measured GTC limits "
                "skipped for this year to avoid double-curtailment",
                year,
            )
        else:
            gtc_out = ercot_gtc_ttc_hourly(
                np.asarray(ttc, dtype=float), iso_config, year, demand.shape[1]
            )
            if gtc_out is None:
                logger.warning(
                    "ercot_gtc_limits_measured: no gtc-limits clean partition "
                    "for %d — static TTC kept (supply the NP6-86 archives and "
                    "run scripts/curate_gtc_limits.py)",
                    year,
                )
            else:
                ttc, ttc_import = gtc_out

    # ERCOT West Texas Export corridor VRE curtailment-share driver (WP-B): a
    # per-(zone, hour) ceiling on West/Panhandle wind & solar reproducing the
    # sub-zonal Permian/CREZ nodal congestion the 8-zone reduction cannot resolve.
    # Reads the derived congestion-share table and the model's OWN net-load, so it
    # regenerates forward. Applied only when the year carries measured HSL
    # potential (the uncurtailed CF ceiling) — otherwise the delivered-as-CF
    # renewables already embed curtailment and the ceiling would double-count.
    wind_curtail_share = None
    solar_curtail_share = None
    if getattr(config, "ercot_wtx_curtailment_driver", False) and iso == "ERCOT":
        if load_hsl_hourly(iso, year) is None:
            logger.warning(
                "ercot_wtx_curtailment_driver: %d has no measured HSL potential "
                "(renewables ride delivered-as-CF) — curtailment ceiling skipped "
                "to avoid double-curtailment",
                year,
            )
        else:
            from market_sim.config import paths as _paths
            from market_sim.data.curtailment_share import wtx_curtail_multipliers

            # System net-load on the potential convention (fleet net-load drag):
            # demand minus uncurtailed wind & solar potential, summed over zones.
            net_load = (
                demand.sum(axis=0)
                - (np.asarray(wind_cap)[:, None] * wind_cf).sum(axis=0)
                - (np.asarray(solar_cap)[:, None] * solar_cf).sum(axis=0)
            )
            mult = wtx_curtail_multipliers(
                net_load,
                list(zone_names),
                depth_wind=float(getattr(config, "ercot_wtx_curtail_depth_wind", 0.0)),
                depth_solar=float(
                    getattr(config, "ercot_wtx_curtail_depth_solar", 0.0)
                ),
                reference_dir=_paths.RAW_DIR / "reference",
            )
            if mult is None:
                logger.warning(
                    "ercot_wtx_curtailment_driver: no derived share table for %d "
                    "— ceiling skipped (run "
                    "scripts/derive_ercot_wtx_curtailment_share.py)",
                    year,
                )
            else:
                wind_curtail_share, solar_curtail_share = mult
                logger.info(
                    "ercot_wtx_curtailment_driver: %d West/Panhandle VRE ceiling "
                    "active (depth wind=%.4f solar=%.4f)",
                    year,
                    float(getattr(config, "ercot_wtx_curtail_depth_wind", 0.0)),
                    float(getattr(config, "ercot_wtx_curtail_depth_solar", 0.0)),
                )
    # Aggregate interface limits (CAISO's simultaneous WECC import cap): resolve
    # the configured link groups to flow-column indices for the LP. Empty (no
    # extra rows) for ISOs without an interface_limits entry.
    interface_groups = build_interface_groups(
        iso_config.links, iso_config.interface_limits
    )
    # MISO per-zone seasonal CIL/CEL deliverability groups: replace the static
    # summer ``MISO_CIL_*`` fallbacks baked into _miso_config with per-season
    # hourly caps from the LOLE Study Report data (scope decision D7 — the
    # NYISO monthly-TTC pattern, fed from data/capacity_deliverability instead
    # of a constants table). Always on for MISO: the measured seasonal limits
    # ARE the internal congestion structure (rule #10-admissible — they
    # regenerate every planning year from forward drivers). Falls back to the
    # static summer caps when the clean partition is absent (never silent-zero).
    if iso == "MISO":
        from market_sim.model.transmission import build_miso_deliverability_groups

        seasonal_groups = build_miso_deliverability_groups(
            iso_config.links, year, demand.shape[1]
        )
        if seasonal_groups:
            static_limits = [
                lim
                for lim in iso_config.interface_limits
                if not lim.name.startswith("MISO_CIL_")
            ]
            interface_groups = (
                build_interface_groups(iso_config.links, static_limits)
                + seasonal_groups
            )
            logger.info(
                "MISO %d: seasonal CIL/CEL interface caps on %d zone group(s) "
                "(per-season hourly vectors from the LOLE deliverability data; "
                "static summer fallbacks replaced)",
                year,
                len(seasonal_groups),
            )
        else:
            logger.warning(
                "MISO %d: capacity-deliverability clean partition absent — "
                "falling back to static PY2025-26 summer CIL/CEL caps; run "
                "scripts/curate_capacity_deliverability.py",
                year,
            )
    # [measured: EIA-930 per-corridor (month × hour-of-day) p95 net-flow
    #  envelope → corridor import/export caps | forecast substitute:
    #  caiso_corridor_atc_forward — the shared
    #  transmission.forward_corridor_interface_groups capability envelope,
    #  which the forecast runner also wires (Stage 5); the measured branch
    #  below is a backcast overlay, plan §3.1]
    # Measured WECC corridor deliverability envelope (CAISO per-hub only): cap
    # each corridor link's import-direction flow at the per-(month × hour-of-day)
    # p95 measured net import (an ATC proxy that tightens midday), so the LP can
    # no longer pull the neighbors' idle thermal tranches over the cheap-priced
    # hub up to the 8.3 GW simultaneous cap. One-sided hourly upper bounds, added
    # to the interface groups; export keeps the physical TTC. No-op off the flag
    # or when the year has no measured interchange (byte-identical).
    forward_atc = caiso_corridors and getattr(
        config, "caiso_corridor_atc_forward", False
    )
    if forward_atc or (
        caiso_corridors and getattr(config, "caiso_corridor_flow_limit", False)
    ):
        from market_sim.model.transmission import build_caiso_corridor_flow_groups

        corridor_export_env = (
            None  # measured branch fills it; forward ATC leaves it off
        )
        if forward_atc:
            # FORWARD ATC: corridor TTC × posted-ATC base fraction × forward solar
            # derate (CISO solar / demand), a capability limit — not the measured
            # p95 flow (CLAUDE.md #12). Supersedes the measured envelope when on.
            from market_sim.model.transmission import forward_corridor_atc_envelope

            corridor_env = forward_corridor_atc_envelope(
                iso_config, iso, year, demand.shape[1]
            )
            cap_label = "FORWARD ATC (TTC × ATC-frac × solar derate)"
        else:
            from market_sim.data.eia_loader import measured_corridor_flow_envelope

            corridor_env = measured_corridor_flow_envelope(iso, year, demand.shape[1])
            # Symmetric measured export-deliverability ceiling: caps each
            # corridor's export (negative) flow at its p95 net export, which
            # collapses to ~0 in the evening ramp where the corridor reliably
            # net-imports — forbidding the LP's unphysical evening wheel-out of
            # cheap CA gas that over-dispatched CC_REGULAR and inflated the
            # evening LMP. A capability envelope the LP clears below, not the
            # hourly residual (rule #12).
            corridor_export_env = measured_corridor_flow_envelope(
                iso, year, demand.shape[1], direction="export"
            )
            from market_sim.config.interchange_config import (
                CAISO_CORRIDOR_FLOW_PERCENTILE,
            )

            cap_label = f"measured p{CAISO_CORRIDOR_FLOW_PERCENTILE:g} ATC proxy"
        if corridor_env:
            corridor_groups = build_caiso_corridor_flow_groups(
                iso_config.links,
                corridor_env,
                export_envelope=None if forward_atc else corridor_export_env,
            )
            interface_groups = interface_groups + corridor_groups
            exp_note = ""
            if corridor_export_env:
                exp_note = (
                    "; export-direction cap on (evening net-export ~0 → no wheel-out): "
                    f"median export DSW {float(np.median(corridor_export_env.get('WECC_DSW', [np.nan]))) / 1000.0:.1f} GW "
                    f"/ PNW {float(np.median(corridor_export_env.get('WECC_PNW', [np.nan]))) / 1000.0:.1f} GW"
                )
            logger.info(
                "%s %d: WECC corridor deliverability cap on %d link(s) — %s; "
                "median import DSW %.1f GW / PNW %.1f GW; midday tighter%s",
                iso,
                year,
                len(corridor_groups),
                cap_label,
                float(np.median(corridor_env.get("WECC_DSW", [np.nan]))) / 1000.0,
                float(np.median(corridor_env.get("WECC_PNW", [np.nan]))) / 1000.0,
                exp_note,
            )

    # PJM congestion lever (Lever A): cap each PJM_external→border link's signed
    # flow per hour at the measured per-border net-interchange envelope, so the
    # priced external star node can no longer wheel ~30 GW uncongested into the 5
    # border zones (the copper-plate bypass). Mirrors the CAISO corridor cap
    # (asymmetric per-hour interface groups); no-op off the flag, for non-PJM, or
    # when the measured tie file is absent (byte-identical).
    if getattr(config, "pjm_congestion", False) and iso == "PJM" and priced_interchange:
        from market_sim.config.constants import PJM_EXTERNAL_FLOW_PERCENTILE
        from market_sim.config.interchange_config import IMPORT_ZONE
        from market_sim.data.eia_loader import pjm_zonal_interchange_envelope
        from market_sim.model.transmission import build_pjm_external_flow_groups

        env = pjm_zonal_interchange_envelope(
            year, zone_names, demand.shape[1], PJM_EXTERNAL_FLOW_PERCENTILE
        )
        if env is not None:
            import_cap, export_cap = env
            ext_groups = build_pjm_external_flow_groups(
                iso_config.links, import_cap, export_cap, zone_names
            )
            interface_groups = interface_groups + ext_groups
            # Per-border median caps (GW) for the log: dominant direction generous,
            # minor direction ~0 (EMAAC import / Dominion export / interior zones).
            border_rows = {
                ln.to_zone
                for ln in iso_config.links
                if ln.from_zone == IMPORT_ZONE.get("PJM")
            }
            zone_idx = {z: i for i, z in enumerate(zone_names)}
            cap_note = "; ".join(
                f"{z.replace('PJM_', '')} imp {np.median(import_cap[zone_idx[z]]) / 1000.0:.1f}"
                f"/exp {np.median(export_cap[zone_idx[z]]) / 1000.0:.1f} GW"
                for z in sorted(border_rows)
                if z in zone_idx
            )
            logger.info(
                "PJM %d: external-node deliverability cap (p%g) on %d link(s) — %s",
                year,
                PJM_EXTERNAL_FLOW_PERCENTILE,
                len(ext_groups),
                cap_note,
            )

    # Commercial-operation-date (COD) vintage ramp: in a backcast the fleet
    # snapshot is a recent vintage that includes units built after the solved
    # year. The ramp is now applied uniformly inside generators_to_fleet_arrays
    # (config.cod_ramp_enabled, default on) via the month-precise EIA-860
    # plant-code map — covering the ERCOT CAMPD bins and every raw EIA-860 unit
    # alike — so the per-fleet-path scaling that used to live here is gone. See
    # data.cod_ramp.

    # Whole-plant exits that retired mid-window (e.g. Mystic) are absent from
    # the single recent operable snapshot, so the COD ramp has nothing to age
    # out. Inject them into the backcast fleet base — the ramp
    # (generators_to_fleet_arrays) then dispatches each through its real
    # retirement month and zeros it after. Mirror of forecast's planned
    # additions; backcast-mode only (run_calibration is always backcast). The
    # year selects the active EIA-860 vintage; a year-matched native vintage
    # carries these exits in its own operable file and ships no retiree parquet,
    # so this returns nothing there (no double-count).
    retired_units = (
        load_retired_within_window(iso, iso_config, year=year)
        if config.mode == "backcast"
        else []
    )

    # Resolve the per-plant bin frame, then build the base fleet and the
    # LP-ready dispatch fleet through the SHARED builders
    # (fleet.build_base_fleet / fleet.build_dispatch_fleet) — the same
    # bodies the forecast runner calls (orchestrator-unification Stage 6).
    # Backcast-specific inputs enter as explicit parameters: the year-matched
    # EIA-860 vintage, the curated ERCOT bin sheet at this solve year's
    # vintage, the measured hydro monthly budgets, the biomass-injection
    # drop, the historical import placement (after hydro), and the
    # emission-override seam (off — backcast per-plant rates enter via the
    # bin artifacts and the v2 hook inside bins_to_fleet, G-39 §9.6).
    campd_bins = (
        load_campd_bins(
            config.campd_bins_path,
            year=year,
            capacity_reconcile_path=(
                config.cc_capacity_reconcile_path
                if config.cc_capacity_reconcile
                else None
            ),
        )
        if config.use_campd_bins and iso == "ERCOT"
        else None
    )
    if (
        campd_bins is None
        and getattr(config, "plant_level_fleet", False)
        and thermal_tranche_overrides(iso)
    ):
        # Per-plant thermal fleet with ERCOT's smoothed rising offer curve:
        # synthesize the per-plant bins frame (committed / coal must-run from
        # the CAMPD thermal-tranche artifact). An empty synthesis (no
        # artifact coverage) leaves campd_bins None and falls through to the
        # legacy aggregate path inside build_base_fleet (n_bins=0 keeps the
        # per-plant identity).
        synth = fleet_to_bins(
            load_fleet_from_csv(iso, iso_config, year=year) + retired_units,
            iso,
            config,
        )
        if not synth.empty:
            campd_bins = synth
    fleet_base = build_base_fleet(
        campd_bins,
        iso,
        iso_config,
        zone_names,
        config,
        retired_units,
        [],  # planned additions are forecast-only; the vintage carries built units
        year,
        None,  # confirmed exits ride the year-matched vintage in a backcast
        vintage_year=year,
        # Gas/coal are dispatched via the CAMPD bins; biomass is injected as
        # a must-run resource (run_calibration_full). Oil is kept as its own
        # raw LP unit so it dispatches as the scarcity peaker it is — the
        # backcast's historical divergence from the runner's oil-excluding
        # default set (see build_base_fleet's nonthermal_exclude note).
        nonthermal_exclude=(
            frozenset({"gas_cc", "gas_ct", "coal", "biomass"})
            if iso == "ERCOT"
            else None
        ),
        legacy_n_bins=(
            0
            if getattr(config, "plant_level_fleet", False)
            else config.heat_rate_bin_count
        ),
    )
    fleet, fuel_fracs, hydro_gen_idx, hydro_monthly_energy = build_dispatch_fleet(
        fleet_base,
        campd_bins,
        import_generators,
        iso,
        year,
        zone_names,
        config,
        hydro_backfill_year=hydro_backfill_year,
        hydro_eia930_monthly=hydro_eia930_monthly,
        hydro_forecast_budget=hydro_forecast_budget,
        hydro_year=hydro_year,
        drop_biomass_units=inject_biomass_mustrun,
        imports_after_hydro=True,
        apply_emission_overrides=False,
    )
    # CT_PEAKER reliability must-run floor: pass the peakers' CAMPD/CEMS hourly
    # on/off shape so the floor starts/stops with the real unit (zero in every
    # hour the plant did not report load), instead of being smeared flat. The
    # parasitic factor only scales magnitude, which the per-month shape
    # normalization removes, so a bare gross series is enough.
    ct_campd_shape = None
    if getattr(config, "ct_mustrun_per_plant", False):
        from market_sim.data import campd as _campd

        _states = _campd.states_for_iso(iso)
        if _states:
            _cdf = _campd.load_campd_hourly(_states, [config.weather_year])
            if not _cdf.empty:
                ct_campd_shape = _campd.plant_hourly_net(
                    _cdf, {}, config.weather_year, hours=config.hours
                )
    fleet_arrays = generators_to_fleet_arrays(
        fleet,
        zone_names,
        hours=config.hours,
        iso=iso,
        config=config,
        load_shape=demand.sum(axis=0),
        ct_campd_shape=ct_campd_shape,
        year=config.weather_year,
    )
    inject_offshore_wind_availability(fleet_arrays, wind_cf, config, iso)
    # Net-load-indexed ST_GAS + CT_PEAKER reliability-drag min-gen floors —
    # the single shared gate-and-log wrapper both orchestrators call
    # (fleet.apply_netload_drag_floors, orchestrator-unification Stage 6).
    # Gates internally on gas_st_netload_drag / ct_netload_drag; net-load uses
    # the same LP-served convention as the other net-load consumers below.
    apply_netload_drag_floors(
        fleet_arrays,
        fleet,
        demand,
        wind_cf,
        wind_cap,
        solar_cf,
        solar_cap,
        config,
        iso,
        year,
    )
    # ══════════════════════════════════════════════════════════════════════
    # BACKCAST MEASURED INTERCHANGE OVERLAYS — availability / seam limits.
    # Every block below feeds a MEASURED series into the priced node's bounds
    # (CLAUDE.md rule 12: reproducible capability envelopes, never an outcome
    # pin) and is backcast-only by design (plan §3.1). None is reachable from
    # the forecast path: the forecast substitutes are noted per overlay.
    # The forward-native interchange injections live in the SHARED
    # transmission.apply_interchange_injections, called below after the mc
    # assembly (both orchestrators run it).
    # ══════════════════════════════════════════════════════════════════════
    # [measured: EIA-930 CISO diurnal interchange envelope → import/export
    #  availability shape | forecast substitute: none — the reference-price /
    #  per-hub seams price the diurnal signal instead of bounding it]
    # Shape the priced import/export node by the measured EIA-930 diurnal
    # interchange envelope (import overnight, export the midday solar glut) so
    # the node stops clearing a flat all-hours import that floors the midday
    # price. Only fires with priced interchange + the opt-in flag + a measured
    # envelope; otherwise the static node is unchanged.
    if priced_interchange and getattr(config, "interchange_shaping", False):
        from market_sim.model.transmission import inject_interchange_shape

        export_only = getattr(config, "interchange_shaping_export_only", False)
        # Per-direction envelope percentile is a ScenarioConfig field (rule
        # 24 — was an os.environ INTERCHANGE_SHAPE_IMPORT_PCT/EXPORT_PCT read
        # inside inject_interchange_shape), so the value that ran is recorded
        # in run_config.json. Both default to 90.0, reproducing the env-unset
        # behavior of every run to date.
        import_pct = getattr(config, "interchange_shape_import_pct", 90.0)
        export_pct = getattr(config, "interchange_shape_export_pct", 90.0)
        if inject_interchange_shape(
            fleet_arrays,
            iso,
            year,
            export_only=export_only,
            import_percentile=import_pct,
            export_percentile=export_pct,
        ):
            logger.info(
                "%s %d: priced node shaped by measured EIA-930 interchange "
                "envelope (%s, import p%g / export p%g)",
                iso,
                year,
                "export midday only — imports uncapped"
                if export_only
                else "import overnight / export midday",
                import_pct,
                export_pct,
            )
    # [measured: EIA-930 MISO BA-to-BA net-import envelope → seam import cap |
    #  forecast substitute: the seam's interface_limit_mw + reference prices]
    # MISO reference-price seam deliverability cap: bound each seam's
    # (PJM/SPP/South) import-band availability at the measured EIA-930 BA-to-BA
    # net-import envelope, so the model stops over-importing on the SPP/southern
    # borders MISO actually nets ~0 / net-EXPORTS over. One-sided import ceiling;
    # export bands keep their priced economics. No-op off the flag, for non-MISO,
    # or when the year has no measured interchange (byte-identical).
    if getattr(config, "reference_price_interface", False) and getattr(
        config, "miso_seam_flow_limit", False
    ):
        from market_sim.model.transmission import inject_miso_seam_flow_limit

        # Optional round-2 import-lift: raise the deliverability percentile so the
        # priced seam clears more import in tight hours (None keeps the p90
        # default). Still a measured-duration-curve ceiling, not a residual pin.
        _seam_pct = getattr(config, "miso_seam_flow_percentile", None)
        if inject_miso_seam_flow_limit(fleet_arrays, iso, year, percentile=_seam_pct):
            from market_sim.config.constants import MISO_SEAM_FLOW_PERCENTILE

            logger.info(
                "%s %d: reference-price seam import capped at measured EIA-930 "
                "BA-to-BA deliverability envelope (p%g; SPP/South clip toward "
                "~0 import, PJM keeps its measured eastern transfer)",
                iso,
                year,
                MISO_SEAM_FLOW_PERCENTILE if _seam_pct is None else _seam_pct,
            )
    # Export mirror: cap each seam's net EXPORT at the measured net-export
    # envelope by raising the export bands' lower bound toward 0. Clips the PJM
    # seam (which MISO net-imports over) to ~0 export, removing the spurious
    # export of cheap MISO coal back east; SPP/South keep their measured export
    # headroom. Shares the import cap's percentile (one envelope, both
    # directions). No-op off the flag, for non-MISO, or with no measured year.
    if getattr(config, "reference_price_interface", False) and getattr(
        config, "miso_seam_export_limit", False
    ):
        from market_sim.model.transmission import inject_miso_seam_flow_limit

        _seam_pct = getattr(config, "miso_seam_flow_percentile", None)
        if inject_miso_seam_flow_limit(
            fleet_arrays, iso, year, percentile=_seam_pct, direction="export"
        ):
            from market_sim.config.constants import MISO_SEAM_FLOW_PERCENTILE

            logger.info(
                "%s %d: reference-price seam export capped at measured EIA-930 "
                "BA-to-BA net-export envelope (p%g; PJM seam clips export toward "
                "~0, SPP/South keep their measured export headroom)",
                iso,
                year,
                MISO_SEAM_FLOW_PERCENTILE if _seam_pct is None else _seam_pct,
            )
    # [measured: PJM tie-line per-neighbor flow envelope → seam import cap |
    #  forecast substitute: the seam's interface_limit_mw + reference prices]
    # PJM seam import cap: cap each of PJM's 5 reference-price seams' import
    # bands at the measured per-neighbor deliverability envelope (PJM tie-line
    # file, aggregated from border zones to neighbor level). Fixes the ~38 TWh
    # over-export by capping the LP's simultaneous full-TTC export on all 5
    # seams. No-op off the flag, for non-PJM, or with no measured tie file.
    if getattr(config, "reference_price_interface", False) and getattr(
        config, "pjm_seam_flow_limit", False
    ):
        from market_sim.model.transmission import inject_pjm_seam_flow_limit

        _pjm_pct = getattr(config, "pjm_seam_flow_percentile", None)
        if inject_pjm_seam_flow_limit(
            fleet_arrays, iso, year, zone_names, hours, percentile=_pjm_pct
        ):
            from market_sim.config.constants import PJM_SEAM_FLOW_PERCENTILE

            logger.info(
                "%s %d: reference-price seam import capped at measured PJM "
                "tie-line deliverability envelope (p%g); each neighbor's "
                "import bands derated to border-zone summed envelope",
                iso,
                year,
                PJM_SEAM_FLOW_PERCENTILE if _pjm_pct is None else _pjm_pct,
            )
    # PJM seam export cap: symmetric mirror — cap each seam's net export at
    # the measured per-neighbor export envelope.
    if getattr(config, "reference_price_interface", False) and getattr(
        config, "pjm_seam_export_limit", False
    ):
        from market_sim.model.transmission import inject_pjm_seam_flow_limit

        _pjm_pct = getattr(config, "pjm_seam_flow_percentile", None)
        if inject_pjm_seam_flow_limit(
            fleet_arrays,
            iso,
            year,
            zone_names,
            hours,
            percentile=_pjm_pct,
            direction="export",
        ):
            from market_sim.config.constants import PJM_SEAM_FLOW_PERCENTILE

            logger.info(
                "%s %d: reference-price seam export capped at measured PJM "
                "tie-line net-export envelope (p%g); each neighbor's export "
                "bands floored to border-zone summed envelope",
                iso,
                year,
                PJM_SEAM_FLOW_PERCENTILE if _pjm_pct is None else _pjm_pct,
            )
    # ── end of the backcast measured interchange overlays (availability) ──
    # (the measured PRICE overlays live in _backcast_measured_interchange_
    # prices below, threaded into the shared injection sequence; the measured
    # NYISO reconciliation band and CAISO corridor envelopes are built at
    # their structural call sites further down, labelled the same way.)
    # CAISO RA must-offer floor: hold the gas fleet online midday at the
    # measured EIA-930 NG: NG profile (frac-scaled) so the model goes LONG and
    # its surplus exports/curtails at ~$0 (mirrors inject_interchange_shape).
    if getattr(config, "caiso_gas_commitment_floor", False):
        from market_sim.model.transmission import (
            inject_caiso_gas_commitment_floor,
        )

        frac = float(getattr(config, "caiso_gas_floor_frac", 1.0))
        if inject_caiso_gas_commitment_floor(fleet_arrays, iso, year, frac):
            logger.info(
                "%s %d: RA must-offer floor — gas fleet held online midday at "
                "%.2f x measured EIA-930 NG: NG (long-midday floor)",
                iso,
                year,
                frac,
            )

    # ── Generic registry-driven reliability floor ──────────────────────────
    # One flag, one engine, one registry: every enabled (zone, class, driver)
    # limb in RELIABILITY_FLOOR_REGISTRY[iso] (seeded from the derived
    # reliability_floor_coeffs_<ISO>.csv) is applied by the single ISO-agnostic
    # engine. Per-run overrides (config.reliability_floor_overrides) can toggle
    # or re-tune individual limbs without editing the registry.
    if getattr(config, "reliability_floor", False):
        from market_sim.config.iso_configs import (
            RELIABILITY_FLOOR_REGISTRY,
            apply_reliability_floor_overrides,
            drop_drag_owned_reliability_specs,
        )
        from market_sim.model.transmission import inject_reliability_floor

        _floor_specs = apply_reliability_floor_overrides(
            RELIABILITY_FLOOR_REGISTRY.get(iso, []),
            getattr(config, "reliability_floor_overrides", None),
        )
        # Rule 19: when a net-load drag owns a class's commitment (CT_PEAKER via
        # ct_netload_drag), drop that class's reliability-floor limbs so the two
        # do not stack into an all-day floor binding overnight (the D-4
        # off-window failure; docs/FINDING-pjm-burndown-2026-07.md). No-op when
        # no drag is active, so non-drag ISOs/runs are byte-identical.
        _n_before = len(_floor_specs)
        _floor_specs = drop_drag_owned_reliability_specs(_floor_specs, config)
        if len(_floor_specs) < _n_before:
            logger.info(
                "%s %d: reliability floor — dropped %d drag-owned limb(s) "
                "(CLAUDE.md rule 19: net-load drag owns the class commitment)",
                iso,
                year,
                _n_before - len(_floor_specs),
            )
        if _floor_specs and inject_reliability_floor(
            fleet_arrays,
            iso,
            year,
            _floor_specs,
            zone_names,
            demand=demand,
            wind_cf=wind_cf,
            wind_cap=wind_cap,
            solar_cf=solar_cf,
            solar_cap=solar_cap,
        ):
            logger.info(
                "%s %d: reliability floor — %d enabled limb spec(s) applied "
                "from RELIABILITY_FLOOR_REGISTRY",
                iso,
                year,
                sum(1 for s in _floor_specs if getattr(s, "enabled", True)),
            )

    # NEISO winter fuel-security must-run (Component B): posture the fuel-secure
    # steam fleet (COAL_BIT + oil-capable ST_GAS) at minimum-stable on winter
    # cold days under the ISO-NE winter-reliability program posture (WRP/IEP/OFSA)
    # — the seasonal-reliability commitment coupled to the Component-A oil-burn
    # inventory budget above. Runs AFTER the reliability-floor engine so it
    # composes cheapest-first via `maximum` and its raised unit-hours carry the
    # MECH_WINTER_FUELSEC D-2 tag. Replaces the disabled COAL/ST_GAS tmin cold
    # limbs (rule 19). NEISO-only; default off (byte-identical).
    if getattr(config, "neiso_winter_fuel_mustrun", False):
        from market_sim.data.winter_fuel_inventory import (
            _WINTER_FUELSEC_CLASSES,
            apply_winter_fuelsec_mustrun,
        )

        # Rule 19/24 reconcile: the NEISO ST_GAS net-load reliability limb
        # (reliability_floor_coeffs_NEISO.csv, 2026-07-06) owns the legacy-steam
        # commitment on tight-system days — hot AND cold, a superset of Component
        # B's cold-day window for that class. When both mechanisms are armed in a
        # run, Component B keeps only its coal scope so two floors never stack on
        # one phenomenon (the tmin limbs it replaced stay disabled either way).
        from market_sim.config.iso_configs import (
            RELIABILITY_FLOOR_REGISTRY as _rf_registry,
        )

        _wf_classes = _WINTER_FUELSEC_CLASSES
        if getattr(config, "reliability_floor", False) and any(
            s.enabled and s.plant_class == "ST_GAS" and s.driver == "netload"
            for s in _rf_registry.get(iso, [])
        ):
            _wf_classes = tuple(c for c in _wf_classes if c != "ST_GAS")

        if apply_winter_fuelsec_mustrun(
            fleet_arrays,
            iso,
            config.weather_year,
            zone_names,
            plant_classes=_wf_classes,
            min_stable_pct=float(
                getattr(config, "neiso_winter_fuelsec_min_stable_pct", 0.40)
            ),
            commit_frac=float(getattr(config, "neiso_winter_fuelsec_commit_frac", 1.0)),
            tmin_threshold_c=float(
                getattr(config, "neiso_winter_fuelsec_tmin_c", -7.0)
            ),
            hours=config.hours,
        ):
            logger.info(
                "%s %d: winter fuel-security must-run (Component B) applied — "
                "COAL_BIT/ST_GAS floored at %.2f x min-stable on Nov-Mar cold "
                "days (TMIN < %.1f C, NERC cold-onset; WRP/IEP/OFSA posture)",
                iso,
                year,
                float(getattr(config, "neiso_winter_fuelsec_commit_frac", 1.0)),
                float(getattr(config, "neiso_winter_fuelsec_tmin_c", -7.0)),
            )

    # NEISO winter gas-availability cold-snap derate — the shared
    # gate-and-log wrapper both orchestrators call
    # (fleet.apply_neiso_coldsnap_derate, orchestrator-unification Stage 6;
    # closes the §2.2 accidental-drift row). Gates internally on
    # neiso_gas_coldsnap_derate; must run before the reserve-co-opt inputs
    # are built so the shared-headroom RHS sees the derated availability.
    apply_neiso_coldsnap_derate(fleet_arrays, config, iso, year)

    # NYISO firm import baseload (HQ/Ontario must-flow) and the Manitoba
    # firm-hydro floor now run inside the SHARED
    # transmission.apply_interchange_injections below — contract-structure
    # floors, forward-native, reachable from both orchestrators (Stage 5).

    # [measured: EIA-930 NYISO monthly net-interchange schedule → monthly LP
    #  band | forecast substitute: config.nyiso_forward_net_import_twh —
    #  build_import_node_reconciliation is mode-aware, the runner passes
    #  mode="forecast"]
    # NYISO priced-node boundary-flow reconciliation: pin the priced node's
    # MONTHLY net interchange to the measured EIA-930 schedule via a per-month
    # band constraint in the LP (transmission.build_import_node_reconciliation ->
    # dispatch._build_import_node_rows). The near-static economic tranche ladder
    # clears a near-flat ~18.5-21.6 TWh that does not track the metered
    # schedule's 23.45 -> 20.35 -> 19.09 TWh decline; the band replaces that
    # economic estimate with the authoritative measurement (CLAUDE.md rule #11),
    # priced tranches still setting the marginal price within each month's
    # envelope. Only fires with priced interchange + the flag + a priced node.
    import_node_recon = None
    if priced_interchange and getattr(config, "nyiso_import_reconciliation", False):
        from market_sim.model.transmission import build_import_node_reconciliation

        # Mode-aware band target: backcast -> measured EIA-930 schedule
        # (calibration always sets mode="backcast", so this is byte-identical to
        # the prior behaviour); forecast -> the neighbor's forecast net position
        # (config.nyiso_forward_net_import_twh), shaped to monthly by the
        # forecast load, else relaxed to the bare priced-seam economics.
        import_node_recon = build_import_node_reconciliation(
            fleet_arrays,
            iso,
            year,
            mode=getattr(config, "mode", "backcast"),
            forward_net_import_twh=getattr(
                config, "nyiso_forward_net_import_twh", None
            ),
            system_demand=demand,
        )
        if import_node_recon is not None:
            node_idx, recon_lo, recon_hi = import_node_recon
            _recon_target = (
                "the neighbor's forecast net position"
                if getattr(config, "mode", "backcast") == "forecast"
                else "measured EIA-930 net interchange"
            )
            logger.info(
                "%s %d: priced import node reconciled to %s — %d node rows, "
                "annual band [%.2f, %.2f] TWh",
                iso,
                year,
                _recon_target,
                int(node_idx.size),
                recon_lo.sum() / 1e6,
                recon_hi.sum() / 1e6,
            )

    # NYISO Long Island local self-supply floor: force the cable-islanded LI
    # pocket to meet a forward fraction of its own load with in-zone thermal
    # generation rather than importing cheap NYC gas (transmission.
    # inject_nyiso_local_selfsupply). NYISO-only; scales with load.
    if getattr(config, "nyiso_local_selfsupply", False):
        from market_sim.model.transmission import inject_nyiso_local_selfsupply

        # Zone-K LCR/TSL mechanism active (issue #1345): the published-limit
        # import cap owns Long_Island this run; skipping its floor entry here
        # keeps the two mechanisms from stacking (rule 19).
        _selfsupply_exclude = (
            frozenset({"Long_Island"})
            if getattr(config, "nyiso_li_lcr_tsl", False)
            else frozenset()
        )
        if inject_nyiso_local_selfsupply(
            fleet_arrays, iso, demand, zone_names, exclude_zones=_selfsupply_exclude
        ):
            logger.info(
                "%s %d: local self-supply floor applied to downstate pocket(s) "
                "(LMIC / cable-islanded local reliability)",
                iso,
                year,
            )

    # Fuel prices: gas/coal base, then the lignite/PRB supply base for coal
    # (our costs), then the actual EIA-923 monthly per-plant delivered cost
    # on top — so measured monthly cost takes precedence and the supply
    # trajectory is only the base/fallback for plant-months without data.
    fuel_prices = resolve_fuel_prices(config, fleet_arrays, year, apply_monthly=False)
    if config.coal_supply_repricing:
        apply_coal_supply_pricing(fuel_prices, fleet, config, year)
    apply_plant_monthly_fuel_prices(fuel_prices, fleet_arrays, config, year)
    # Hub-basis overlay (NEISO only): replace the gas price with the measured
    # Algonquin Citygate hub spot in covered months — daily-resolved when
    # gas_hub_basis_daily is on. Because run_year resolves fuel prices with
    # apply_monthly=False (so the coal-supply base lands before the per-plant
    # EIA-923 overwrite), the overlay that resolve_fuel_prices runs in its
    # apply_monthly=True branch must be re-applied here, mirroring that branch's
    # order: plant-monthly, then hub overlay, then the dual-fuel min. No-op
    # unless gas_hub_basis_overlay is set (and basis rows exist), so non-NEISO
    # runs are unchanged.
    apply_hub_basis_overlay(fuel_prices, fleet_arrays, config, year)
    # NYISO per-zone gas-hub basis: shift each gas unit to its region's pipeline
    # index so the east marginal gas stays dearer than the west (the structural
    # source of the upstate-cheap / east-dear spread). Mirrors the
    # resolve_fuel_prices apply_monthly=True order: after the plant-monthly /
    # hub overlay, before the dual-fuel min so oil parity still caps any winter
    # spike. No-op unless nyiso_zonal_gas_basis is set (NYISO only).
    apply_nyiso_zonal_gas_basis(fuel_prices, fleet_arrays, config, year)
    # NYISO downstate CT-peaker interruptible city-gate gas premium: lift each
    # NYC / Long Island CT_PEAKER unit's delivered gas by the measured monthly
    # LDC city-gate premium (summer-peaked interruptible-gas scarcity these
    # non-firm peakers face) so an efficient LM6000 no longer undercuts the
    # dearer downstate steam fleet on flat hub gas (issue #1344 / B-NYI-1). Same
    # order as the other basis overlays: after the zonal basis, before the
    # dual-fuel oil-parity min. No-op unless nyiso_downstate_ct_gas_basis is set
    # (NYISO only). See fuel.apply_nyiso_downstate_ct_gas_basis.
    apply_nyiso_downstate_ct_gas_basis(fuel_prices, fleet_arrays, config, year)
    # NYISO downstate CT-peaker DAILY delivered-gas re-grounding: SET each NYC /
    # Long Island CT_PEAKER unit's gas to the curated measured daily delivered
    # index (Transco Z6 NY daily spot + monthly LDC premium), so the cold-snap
    # blowouts on the exact days the interruptible peakers run lift their offer —
    # the daily-resolution successor to the monthly premium above (rules
    # #11/#13). Same order: after the monthly basis, before the dual-fuel
    # oil-parity min. No-op unless nyiso_downstate_ct_gas_daily is set (NYISO
    # only). See fuel.apply_nyiso_downstate_ct_gas_daily.
    apply_nyiso_downstate_ct_gas_daily(fuel_prices, fleet_arrays, config, year)
    # ERCOT per-zone gas-hub basis: shift each gas unit to its zone's measured
    # regional hub (Waha-cheap West/Permian, dearer North/East-Texas and South)
    # so the merit order stops over-running DFW/North CCs on flat Waha-discounted
    # gas. Mean-zero anchored so the aggregate gas level is preserved. Same order
    # as the resolve_fuel_prices apply_monthly=True branch: after the
    # plant-monthly / hub overlay, before the dual-fuel min. No-op unless
    # ercot_zonal_gas_basis is set (ERCOT only).
    apply_ercot_zonal_gas_basis(fuel_prices, fleet_arrays, config, year)
    # PJM per-zone gas basis: shift each gas unit to its zone's measured regional
    # delivered-to-electric-power basis (west coal belt cheap, eastern
    # EMAAC/SWMAAC/Dominion dear) so PJM stops clearing as a single copper-plate —
    # the internal TTCs bind, eastern LMP separates up, eastern CCs back off and
    # western coal serves the east. Capacity-weighted mean-zero so the aggregate
    # gas level is preserved. Same order as the resolve_fuel_prices
    # apply_monthly=True branch: after the plant-monthly / hub overlay, before the
    # dual-fuel min. No-op unless pjm_zonal_gas_basis is set (PJM only).
    apply_pjm_zonal_gas_basis(fuel_prices, fleet_arrays, config, year)
    # MISO per-zone gas basis (north/south gas gradient). Same mean-zero core as
    # PJM. No-op unless miso_zonal_gas_basis is set (MISO only).
    apply_miso_zonal_gas_basis(fuel_prices, fleet_arrays, config, year)
    # CAISO per-zone citygate basis (NP15/ZP26 on PG&E Citygate, SP15 on SoCal
    # Citygate — measured weekly prints, mean-zero). No-op unless
    # caiso_zonal_gas_basis is set (CAISO only).
    apply_caiso_zonal_gas_basis(fuel_prices, fleet_arrays, config, year)
    # Net-load-indexed West/Panhandle Waha shape: redistribute the West gas basis
    # across hours (firm at high net-load, collapsed at low) so peakers — which
    # burn only in scarcity hours — see firm Waha and idle, while the West CCs on
    # all-hours blended gas stay baseload. Mean-zero so the annual basis above is
    # preserved; structural replacement for the flat delivered-floor scalar. No-op
    # unless ercot_west_netload_gas_shape (+ ercot_zonal_gas_basis) is set, ERCOT.
    if getattr(config, "ercot_west_netload_gas_shape", False):
        west_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        # Endogenous Waha collapse frequency (gap G6): how often forecast West/
        # Panhandle VRE over-supplies the local basin (local load + export TTC).
        # Built from the per-zone VRE capacity×CF, the West load, and the
        # WESTEX+PNHNDL export limit the model already carries — the forward
        # driver that replaces the measured neg_day_freq when
        # ercot_west_gas_endogenous_collapse is on. Always computed so it can be
        # logged against the measured value; the function uses it only when the
        # flag is set.
        waha_zone_idx = [
            i for i, name in enumerate(zone_names) if name in ("West", "Panhandle")
        ]
        west_oversupply_freq = None
        if waha_zone_idx:
            widx = np.array(waha_zone_idx)
            west_vre = (solar_cap[widx, None] * solar_cf[widx]).sum(axis=0) + (
                wind_cap[widx, None] * wind_cf[widx]
            ).sum(axis=0)
            west_local_load = demand[widx].sum(axis=0)
            # Export takeaway: total TTC on links leaving the Waha zones (WESTEX
            # West->North/South_Central + PNHNDL Panhandle->North); the constrained
            # path the surplus must squeeze through before it crashes the hub.
            export_limit = sum(
                link.ttc_mw
                for link in iso_config.links
                if link.from_zone in ("West", "Panhandle")
                and link.to_zone not in ("West", "Panhandle")
            )
            west_oversupply_freq = ercot_west_oversupply_collapse_freq(
                west_vre, west_local_load, export_limit
            )
        apply_ercot_west_netload_gas_shape(
            fuel_prices,
            fleet_arrays,
            config,
            year,
            west_net_load,
            west_oversupply_freq=west_oversupply_freq,
        )
    # Capture which dual-fuel generator-hours will switch to oil (gas price >
    # oil parity) BEFORE the min-cap below overwrites the gas price, so the
    # dispatch re-attribution can count their MWh as petroleum, not gas (the
    # switch itself is objective-only; this is a reporting re-attribution).
    # Gated on dual_fuel_oil_reattribution (NEISO-only) so PJM/NYISO — whose
    # dual-fuel units also switch on their own winter gas — stay byte-identical.
    # Also computed for the winter fuel-inventory budget (Component A), which
    # gates each dual-fuel unit's oil-burn budget to exactly these oil hours so
    # the seasonal stock constraint never caps its gas generation.
    dual_fuel_oil_mask = (
        dual_fuel_switch_mask(fuel_prices, fleet_arrays, config, year)
        if (
            getattr(config, "dual_fuel_oil_reattribution", False)
            or getattr(config, "neiso_winter_fuel_inventory", False)
        )
        else None
    )
    # Dual-fuel switching last, so the oil-parity min sees the final delivered
    # gas price — the AGT-hub winter spot, so the gas->oil switch trips on cold
    # days (NEISO) — not the per-plant monthly cost alone (PJM).
    apply_dual_fuel_pricing(fuel_prices, fleet_arrays, config, year)
    carbon_price = resolve_carbon_price(config, year)
    wind_mc, solar_mc = compute_dispatch_credits(config, year)
    # Base marginal cost: fuel + VOM + carbon + NOx, then exogenous EACs,
    # then the coal take-or-pay tranche discount. No startup-cost markup.
    mc_base = assemble_mc(fleet_arrays, fuel_prices, carbon_price, config.nox_price)
    apply_eac_to_mc(mc_base, fleet_arrays, config)
    apply_coal_tranches(mc_base, fleet, fleet_arrays, fuel_fracs, fuel_prices)
    # ERCOT G-22 condition-responsive CT/peaker offer surface (default off,
    # ERCOT-gated): raise the CT/peaker econ+peak tranche bid to the MEASURED
    # self-withholding level (60-Day DAM disclosure) in the top-net-load hours
    # where the real fleet's peakers price to the cap band, removing the
    # "phantom sub-$200 spare" that caps the energy dual in the missed tail.
    # Net-load uses the same LP-served convention as the drag floors above.
    if getattr(config, "ercot_ct_offer_surface", False) and iso == "ERCOT":
        _ct_surface_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        apply_ercot_ct_offer_surface(mc_base, fleet, _ct_surface_net_load, config)
    # ERCOT G-22 §8 heterogeneity-preserving condition-responsive offer surface
    # (default off, ERCOT-gated): the P1-ONLY additive markup that reprices the gas
    # peak-band scarcity wall in anticipated-tight hours. Built here (net-load + the
    # per-gen fuel price are ready) and threaded into run_energy_solve so it lands on
    # the P1 clearing objective only — P0 run lengths (and the CT<->ST startup
    # coupling) stay byte-identical to the keeper (fleet.
    # build_ercot_offer_surface_conditional_markup). None when the flag is off.
    offer_surface_mc_bid_adjust = None
    if getattr(config, "ercot_offer_surface_conditional", False) and iso == "ERCOT":
        _surface_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        offer_surface_mc_bid_adjust = build_ercot_offer_surface_conditional_markup(
            fleet_arrays, fleet, fuel_prices, _surface_net_load, config
        )
    # NEISO fast-start offer surface (charter Limb B): the identical P1-only
    # seam, NEISO-gated (fleet.build_neiso_offer_surface_conditional_markup).
    if getattr(config, "neiso_offer_surface_conditional", False) and iso == "NEISO":
        _surface_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        offer_surface_mc_bid_adjust = build_neiso_offer_surface_conditional_markup(
            fleet_arrays, fleet, fuel_prices, _surface_net_load, config
        )
    # ── Interchange price/limit injections (orchestrator-unification Stage 5)
    # The forward-native sequence — reference-price seams (generic + CAISO
    # dedicated), firm import/export floors, and the CAISO offer couplings —
    # is the SHARED transmission.apply_interchange_injections, the exact call
    # the forecast runner makes; every step is gated by its existing
    # ScenarioConfig field. The BACKCAST-ONLY measured-price overlays are
    # consolidated below and threaded into the shared sequence at its
    # documented seam point (after the forward base prices, before the
    # couplings — the order the inline code always had). Each overlay names
    # its measured source and forecast substitute (plan §3.1); none is
    # reachable from the forecast path, which passes measured_overlay=None.
    caiso_ref_seam = (
        getattr(config, "caiso_reference_price_seam", False) and iso == "CAISO"
    )
    per_hub_intertie = (
        (not caiso_ref_seam)
        and getattr(config, "caiso_per_hub_intertie", False)
        and iso == "CAISO"
    )
    bidir_intertie = getattr(config, "caiso_bidir_intertie", False) and iso == "CAISO"
    legacy_intertie = not per_hub_intertie and not bidir_intertie

    def _backcast_measured_interchange_prices(fleet_arrays, mc_base) -> None:
        """Backcast measured-price interchange overlays (BOD, plan §3.1).

        Measured hub/border LMP overwrites on the priced node's mc rows —
        each a real delivered price fed as an input (rule 12-admissible), but
        with no forward analogue series, so the forecast substitutes the
        reference-price formula per seam. Runs inside the shared injection
        sequence after the forward base prices and before the couplings.
        """
        # [measured: PJM DA LMP at the MISO-facing western border hubs |
        #  forecast substitute: gas × HR reference price, optionally re-
        #  anchored via miso_pjm_border_anchor]. Overwrites ONLY the PJM seam
        # rows the generic inject_reference_price_mc just priced; SPP/South
        # keep their gas × HR pricing. Measured LMP takes precedence over the
        # border anchor when both are on. No-op without the measured parquet.
        if (
            getattr(config, "reference_price_interface", False)
            and iso in INTERFACE_NEIGHBORS
            and iso != "CAISO"
            and getattr(config, "miso_pjm_lmp_import_pricing", False)
        ):
            from market_sim.model.transmission import (
                inject_miso_pjm_lmp_import_prices,
            )

            if inject_miso_pjm_lmp_import_prices(fleet_arrays, mc_base, iso, year):
                logger.info(
                    "%s %d: PJM seam repriced to MEASURED hourly PJM "
                    "border-hub DA LMP (CHICAGO GEN / AEP GEN / ATSI GEN "
                    "mean + $%.0f hurdle)",
                    iso,
                    year,
                    next(
                        (
                            n.hurdle
                            for n in INTERFACE_NEIGHBORS.get(iso, [])
                            if n.name == "PJM"
                        ),
                        2.0,
                    ),
                )
        # [measured: per-seam Q-Q band ladders — EIA-930 seam flow duration
        #  curves coupled with the measured MISO DA hub LMP
        #  (interchange_config.MISO_SEAM_LADDER_BY_YEAR, scripts/
        #  derive_miso_seam_ladders.py) | forecast substitute: the gas-elastic
        #  reference-price formula (hr_by_year two-track; pooled ladder = the
        #  forward story)]. Overwrites EVERY seam band (PJM/SPP/South, both
        # directions) with its measured revealed-supply-curve price, so the
        # firm/scheduled PJM+IESO base the spot-spread pricing deletes (G-23
        # 2025 import starvation) clears economically. Runs LAST among the
        # seam price overwrites — displaces the border-anchor / PJM-LMP
        # prices on the rows it covers (alternatives, never stacked).
        if (
            getattr(config, "reference_price_interface", False)
            and iso in INTERFACE_NEIGHBORS
            and iso != "CAISO"
            and getattr(config, "miso_seam_measured_ladder", False)
        ):
            from market_sim.model.transmission import (
                inject_miso_seam_ladder_prices,
            )

            if inject_miso_seam_ladder_prices(fleet_arrays, mc_base, iso, year):
                logger.info(
                    "%s %d: seam bands repriced to the MEASURED per-seam Q-Q "
                    "ladders (EIA-930 flow durations x MISO DA hub quantiles; "
                    "PJM/SPP/South, import + export; no added hurdle)",
                    iso,
                    year,
                )
        # [measured: per-seam Q-Q band ladders — PJM settlement-grade tie-line
        #  flow duration curves coupled with the measured PJM DA system LMP
        #  (interchange_config.PJM_SEAM_LADDER_BY_YEAR, scripts/
        #  derive_pjm_seam_ladders.py) | forecast substitute: the gas-elastic
        #  reference-price formula (hr_by_year two-track; pooled ladder = the
        #  forward story)]. Overwrites EVERY seam band (MISO/NYISO/Carolinas/
        # TVA/LGEE, both directions) with its measured revealed-supply-curve
        # price, so the direction-structural record (near-always export to
        # MISO/NYISO, near-always import from the south) the spot-spread
        # pricing inverts (pjm-95 2023: imports 46% of hours vs measured ~2%,
        # displacing CC_REGULAR) clears economically. The firm scheduled-
        # export floor is displaced on ladder years inside
        # apply_interchange_injections (alternatives, never stacked; rule 19).
        if (
            getattr(config, "reference_price_interface", False)
            and iso in INTERFACE_NEIGHBORS
            and iso != "CAISO"
            and getattr(config, "pjm_seam_measured_ladder", False)
        ):
            from market_sim.model.transmission import (
                inject_pjm_seam_ladder_prices,
            )

            if inject_pjm_seam_ladder_prices(fleet_arrays, mc_base, iso, year):
                logger.info(
                    "%s %d: seam bands repriced to the MEASURED per-seam Q-Q "
                    "ladders (tie-line flow durations x PJM DA system "
                    "quantiles; MISO/NYISO/Carolinas/TVA/LGEE, import + "
                    "export; no added hurdle; firm-export floor displaced)",
                    iso,
                    year,
                )
        # [measured: WECC intertie hub LMP (Malin / Palo Verde, OASIS) per
        #  corridor | forecast substitute: caiso_intertie_reference_price —
        #  the forward (HH+basis)×HR×load-shape per-hub seam, which the
        #  shared sequence prices INSTEAD of this overlay when set]. The
        # caiso-51 keeper's headline seam: each per-hub corridor priced at
        # its OWN measured hub, firm/contracted tranches held at contract
        # cost under caiso_perhub_firm_base.
        if per_hub_intertie and not getattr(
            config, "caiso_intertie_reference_price", False
        ):
            from market_sim.model.transmission import (
                inject_caiso_per_hub_intertie_prices,
            )

            if inject_caiso_per_hub_intertie_prices(
                fleet_arrays,
                mc_base,
                iso,
                year,
                carbon_price,
                firm_base=getattr(config, "caiso_perhub_firm_base", False),
            ):
                logger.info(
                    "%s %d: per-hub WECC intertie — two signed corridors (Malin/COI "
                    "→ NP15, Palo Verde/Path-46 → SP15), each priced at its OWN "
                    "measured hub (per-hub basis + per-hub netting, arbitrage-free, "
                    "one direction per hour per corridor)%s",
                    iso,
                    year,
                    (
                        " — firm/contracted tranches held at contract cost "
                        "(caiso_perhub_firm_base)"
                        if getattr(config, "caiso_perhub_firm_base", False)
                        else ""
                    ),
                )
        # [measured: WECC intertie hub LMP (MCE, per-hub series averaged to
        #  one) | forecast substitute: none wired — the bidir STRUCTURE is
        #  forward-reachable via the spec; its legs keep the static ladder
        #  prices in a forecast]. Single signed tie, both legs at the hub.
        if not per_hub_intertie and bidir_intertie:
            from market_sim.model.transmission import (
                inject_caiso_bidir_intertie_prices,
            )

            if inject_caiso_bidir_intertie_prices(
                fleet_arrays, mc_base, iso, year, carbon_price
            ):
                logger.info(
                    "%s %d: bidirectional WECC intertie — single signed flow on a "
                    "shared cap, both legs priced at the measured hub (import + "
                    "border carbon / export, arbitrage-free, one direction per hour)",
                    iso,
                    year,
                )
        # [measured: WECC intertie hub LMPs (Mid-C / Palo Verde) on the pooled
        #  legacy node, import + export sides | forecast substitute: the
        #  static ladder / the per-hub or reference seams]. Superseded by the
        # per-hub and bidir nodes; gated to the legacy pooled topology only.
        if legacy_intertie and getattr(config, "caiso_import_hub_prices", False):
            from market_sim.model.transmission import (
                inject_caiso_export_hub_prices,
                inject_caiso_import_hub_prices,
            )

            if inject_caiso_import_hub_prices(
                fleet_arrays, mc_base, iso, year, carbon_price
            ):
                logger.info(
                    "%s %d: import tranches repriced to measured WECC intertie "
                    "hub LMPs (Mid-C / Palo Verde) — static ladder bypassed",
                    iso,
                    year,
                )
            # Symmetric export side of the same bidirectional intertie, so the
            # tie can reverse to the measured +3.5 GW export.
            if inject_caiso_export_hub_prices(fleet_arrays, mc_base, iso, year):
                logger.info(
                    "%s %d: neighbor-export sink repriced to the measured WECC "
                    "intertie hub LMP — intertie can reverse to export",
                    iso,
                    year,
                )
        # [measured: PJM / ISO-NE Day-Ahead system LMP (hourly) | forecast
        #  substitute: the year-grounded static ladder / a future NYISO
        #  reference seam]. NYISO analogue of the CAISO/MISO measured-hub
        # pricing; the monthly EIA-930 reconciliation band, HQ firm floor and
        # SIL cap are unchanged.
        if (
            iso == "NYISO"
            and priced_interchange
            and getattr(config, "nyiso_import_hub_prices", False)
        ):
            from market_sim.model.transmission import inject_nyiso_import_hub_prices

            if inject_nyiso_import_hub_prices(fleet_arrays, mc_base, iso, year):
                logger.info(
                    "%s %d: import tranches repriced to measured neighbor hourly "
                    "DA LMPs (PJM_west→PJM, ISONE_tie→NEISO, scarcity→hourly max, "
                    "export sink→hourly min) — static ladder bypassed",
                    iso,
                    year,
                )

    # Net load for the solar-shape coupling: the LP-served load (net of
    # must-run) less utility solar/wind generation — same convention as the
    # drag floors and the forecast runner.
    _interchange_net_load = None
    if getattr(config, "caiso_import_solar_shape", False):
        _interchange_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
    apply_interchange_injections(
        fleet_arrays,
        mc_base,
        config,
        iso,
        year,
        carbon_price=carbon_price,
        gas_scenario=config.gas_price_path,
        net_load=_interchange_net_load,
        measured_overlay=_backcast_measured_interchange_prices,
    )

    wind_eac, solar_eac, storage_eac = compute_eac_dispatch_credits(config)
    wind_mc -= wind_eac
    solar_mc -= solar_eac
    # Floor the curtailable wind/solar offers at the negative keep-running
    # (REC/PTC) value so curtailed renewables can set a sub-$0 marginal price
    # in oversupply (CAISO negative midday LMPs). No-op unless
    # config.negative_renewable_offers is on; the floor is the more-negative of
    # the existing offer and -renewable_keep_running_value (so wind's PTC is not
    # double-counted). See market_sim.policy.eac.
    wind_mc, solar_mc = apply_negative_renewable_offer_floor(wind_mc, solar_mc, config)

    storage_units = load_eia860_storage(iso, year, config)
    storage = storage_units_to_arrays(storage_units, zone_names)
    # Static (n_storage,) caps, or hour-varying (n_storage, T) when the
    # intra-year COD ramp is on (config.storage_vintage_ramp) and capacity
    # was commissioned mid-year — mid-year GWs stay offline before COD.
    storage_power_cap, storage_energy_cap = storage_cap_profiles(
        storage_units, storage, config.hours
    )
    # Reserve the measured storage up-AS MW from the dispatch power cap so AS-
    # committed battery capacity cannot also arbitrage energy (ERCOT only).
    # SKIPPED under ercot_storage_as_endogenous (G5): the endogenous co-opt hands
    # the FULL battery cap to the LP and lets it choose energy vs AS, so the
    # measured-award subtraction must not apply (it would pre-commit the split).
    if (
        getattr(config, "storage_as_commitment", False)
        and not getattr(config, "ercot_storage_as_endogenous", False)
        and iso == "ERCOT"
    ):
        storage_power_cap = reserve_storage_as_power(
            storage_power_cap, config.weather_year, config.hours
        )

    if fleet_only:
        # Availability-reconstruction exit (no LP): everything a post-solve
        # consumer needs to recompute pmax x availability per unit-hour,
        # the renewable potential (cf x cap) and the storage power caps,
        # aligned with the persisted bundle.
        return {
            "config": config,
            "fleet": fleet,
            "fleet_arrays": fleet_arrays,
            "storage_units": storage_units,
            "storage": storage,
            "storage_power_cap": storage_power_cap,
            "wind_cf": wind_cf,
            "wind_cap": wind_cap,
            "solar_cf": solar_cf,
            "solar_cap": solar_cap,
            "demand": demand,
        }

    # Oil-burn inventory budget (NEISO-gated). When the budget binds in a
    # cold-snap month, its dual is the scarcity rent that lifts the persisted P1
    # LMP above the flat dual-fuel oil-parity cap (~$258).
    #
    # Two derivations of the same LP mechanism (dispatch._build_oil_budget_rows):
    #   - neiso_winter_fuel_inventory (Component A, keeper path): forward-
    #     derivable capacity/logistics budget (tank fill + re-supply) over the
    #     oil-primary + dual-fuel oil-limb fleet, the limb gated to its exogenous
    #     oil-switch hours (dual_fuel_oil_mask) so gas generation is never
    #     capped. One pooled fleet row per winter month, MMBtu-weighted.
    #   - neiso_oil_burn_budget (superseded): EIA-923 petroleum RECEIPTS, a
    #     measured deliveries-to-tank OUTCOME inadmissible under CLAUDE.md #13.
    #     Kept only as a reference path; never a keeper.
    oil_monthly_budget = None
    oil_budget_gen_idx = None
    oil_budget_month_index = None
    oil_budget_gen_hour_coeff = None
    oil_budget_group_index = None
    if getattr(config, "neiso_winter_fuel_inventory", False):
        from market_sim.data.winter_fuel_inventory import build_winter_fuel_budget

        _wf = build_winter_fuel_budget(
            iso,
            fleet_arrays,
            dual_fuel_oil_mask,
            start_fill_bbl=getattr(config, "neiso_winter_fuel_start_fill_bbl", None),
            hours=config.hours,
        )
        if _wf is not None:
            (
                oil_budget_gen_idx,
                oil_monthly_budget,
                oil_budget_month_index,
                oil_budget_gen_hour_coeff,
                oil_budget_group_index,
            ) = _wf
            _fin = np.isfinite(oil_monthly_budget)
            logger.info(
                "winter fuel-inventory budget (%s %d): %d oil-capable gens, "
                "start_fill=%s bbl, %d winter month(s) constrained, "
                "monthly cap %.2f M MMBtu (~%.2f TWh @HR10.8)",
                iso,
                year,
                oil_budget_gen_idx.size,
                (
                    f"{getattr(config, 'neiso_winter_fuel_start_fill_bbl', None):.0f}"
                    if getattr(config, "neiso_winter_fuel_start_fill_bbl", None)
                    else "2.8M(default)"
                ),
                int(_fin.sum()),
                float(oil_monthly_budget[_fin].max()) / 1e6 if _fin.any() else 0.0,
                float(oil_monthly_budget[_fin].max()) / 10.8 / 1e6
                if _fin.any()
                else 0.0,
            )
    elif getattr(config, "neiso_oil_burn_budget", False):
        from market_sim.data.fuel import load_oil_burn_budget

        _oil_result = load_oil_burn_budget(
            iso,
            year,
            fleet_arrays,
        )
        if _oil_result is not None:
            oil_budget_gen_idx, oil_monthly_budget = _oil_result

    # Base dispatch kwargs + priced import-node band: the shared pipeline
    # assembly (orchestrator-unification Stage 2) — the same key set the
    # inline dict carried, byte-identical values. The backcast-only keys
    # (ttc_import, oil_*) are passed explicitly so they stay present (possibly
    # None-valued) exactly as before; the forecast assembly leaves them UNSET.
    dispatch_spec = DispatchSpec(
        wind_cf=wind_cf,
        wind_cap=wind_cap,
        solar_cf=solar_cf,
        solar_cap=solar_cap,
        # Load-shed penalty = the ISO's own energy bid cap (ISOConfig.voll),
        # not the ERCOT-flavored ScenarioConfig default ($5,000). NYISO/CAISO/
        # MISO/PJM cap verifiable energy offers at $2,000 (FERC Order 831);
        # ERCOT at $5,000. Using the per-ISO cap makes scarcity hours price at
        # the ceiling the market actually clears against.
        voll=iso_config.voll,
        incidence=incidence,
        ttc=ttc,
        # Import-direction bound when the measured ERCOT GTC overlay made the
        # export caps hourly/asymmetric; None keeps the symmetric -ttc.
        ttc_import=ttc_import,
        # ERCOT West Texas Export corridor VRE curtailment ceilings (WP-B);
        # None off-corridor / driver-off leaves the uncurtailed CF bound.
        wind_curtail_share=wind_curtail_share,
        solar_curtail_share=solar_curtail_share,
        storage_power_cap=storage_power_cap,
        storage_energy_cap=storage_energy_cap,
        storage_zone_idx=storage.zone_idx,
        eta_chg=storage.eta_chg,
        eta_dis=storage.eta_dis,
        wind_mc=wind_mc,
        solar_mc=solar_mc,
        storage_discharge_eac=storage_eac,
        storage_discharge_cost=storage.vom,
        rps_target=None,
        storage_daily_cycle_hours=24 if config.storage_daily_cycling else None,
        interface_groups=interface_groups or None,
        # One-way links (MISO's RDT 3,000/2,500 MW directional pair) floor
        # their flow at 0 instead of -ttc. Every other ISO's links are
        # bidirectional (all-True array -> byte-identical bounds). This was
        # built in dispatch but never wired here, so the RDT asymmetry was
        # silently symmetric (+/-ttc per leg) before the six-zone refinement.
        link_bidirectional=get_link_bidirectional_array(iso_config.links),
        hydro_monthly_energy=hydro_monthly_energy,
        hydro_gen_idx=hydro_gen_idx,
        oil_monthly_budget=oil_monthly_budget,
        oil_gen_idx=oil_budget_gen_idx,
        oil_month_index=oil_budget_month_index,
        oil_gen_hour_coeff=oil_budget_gen_hour_coeff,
        oil_group_index=oil_budget_group_index,
        T=config.hours,
    )
    dispatch_kwargs = build_base_dispatch_kwargs(
        dispatch_spec, import_node_recon=import_node_recon
    )
    # Emissions mass-cap rows (policy constraint path, gated; G-29). Mirrors
    # runner.py's forecast-path `mass_caps` block so the backcast calibration
    # harness shares the identical seam — before this wire-through,
    # mass_cap_enabled was never reachable here at all (`get_active_policy_
    # constraints` had no caller in either run_calibration.py or
    # run_calibration_full.py). Default off -> {} -> no dispatch_kwargs
    # change, identical LP. See docs/handoffs/emissions-mass-cap-plan-2026-07.md.
    dispatch_kwargs.update(
        build_mass_cap_dispatch_kwargs(config, year, zone_names, fleet_arrays)
    )

    # Plant-group hourly ramp envelopes (config.ramp_limits, GATED default
    # off): CAMPD-measured trajectory bounds per plant group per hour
    # transition (model/dispatch._build_ramp_rows; design
    # docs/ramp-locational-design-2026-07.md §1). Mirrored in runner.py so
    # the forecast path shares the mechanism (forecast parity, design §4).
    # No-op (identical LP) when off or when the ISO has no envelope artifact.
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
    # (config.local_capacity_constraints, GATED default off): published-study
    # load-pocket relaxation (design §3), RHS from the LCR report parameters
    # scaled by this year's zonal load shape. Mirrored in runner.py (forecast
    # parity). No-op when off or the ISO has no covered areas / crosswalk.
    if getattr(config, "local_capacity_constraints", False):
        from market_sim.data.local_capacity import build_local_capacity_specs

        lcr_specs, _lcr_meta = build_local_capacity_specs(
            iso,
            year,
            fleet_arrays.plant_code,
            fleet_arrays.pmax,
            fleet_arrays.availability,
            zone_names,
            demand,
            storage.zone_idx,
            storage_power_cap,
        )
        if lcr_specs:
            dispatch_kwargs.update(local_capacity_specs=lcr_specs)

    # Hydro hourly deliverability envelope (config.hydro_dispatch_envelope,
    # GATED default off): fleet-wide hourly ceiling at the measured
    # per-(month x hod) percentile of EIA-930 NG:WAT — bounds the budget LP's
    # perfect-foresight hoarding of the monthly hydro energy into the top
    # price hours (caiso-72 STEP-2; FINDING-caiso72-step0). Mirrored in
    # runner.py (forecast parity — a forecast year falls back to the pooled
    # climatology envelope inside the loader). No-op (identical LP) when off,
    # no hydro fleet, or no measured series.
    if (
        getattr(config, "hydro_dispatch_envelope", False)
        and hydro_gen_idx is not None
        and len(hydro_gen_idx)
    ):
        from market_sim.data.eia_loader import measured_hydro_hourly_envelope

        env = measured_hydro_hourly_envelope(iso, year, config.hours)
        if env is not None:
            # Feasibility guard: never cap below the fleet's own hourly lower
            # bounds (min_gen floors / pmin).
            h_idx = np.asarray(hydro_gen_idx, dtype=int)
            if getattr(fleet_arrays, "min_gen", None) is not None:
                lo = fleet_arrays.min_gen[h_idx, : config.hours].sum(axis=0)
            else:
                lo = np.full(config.hours, fleet_arrays.pmin[h_idx].sum())
            env = np.maximum(env, lo)
            # CISO's NG:WAT includes pumped-storage net output (no separate
            # PS series), so the capped model quantity includes PS net
            # discharge — like-for-like with the measured envelope.
            ps_idx = np.flatnonzero(
                np.char.startswith(np.asarray(storage.tech_names, dtype=str), "pumped")
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

    # Energy+reserve co-optimization: the shared pipeline wrapper
    # (orchestrator-unification Stage 2) — the per-ISO reserve designs live in
    # config/reserve_config.py (get_reserve_design), already shared with the
    # forecast runner; the wrapper owns the gate (energy_reserve_coopt, CAISO
    # excluded), the forward-driver threading, the merge, and the logging.
    # Collapses the former per-ISO elif ladder, byte-identically:
    #   * the hand-built PJM zone-aggregate block == reserve_config._pjm_design
    #     (measured Primary requirement + published ORDC — only the last ORDC
    #     step width depends on the requirement scalar and the design sets it
    #     to max(req), the same value — + deliverable supply cap + online gate);
    #   * the post-design ERCOT RTOLCAP supply-cap overwrite is folded into the
    #     designs themselves (audit gap A5): in backcast mode the design's
    #     internal ercot_rtolcap_supply_cap_mw call returns the same measured
    #     parquet series the overwrite applied.
    # sim_year=year is value-identical here: the backcast pins weather_year to
    # the solve year and every sim_year consumer falls back to weather_year.
    apply_reserve_coopt(
        dispatch_kwargs,
        config,
        fleet_arrays,
        config.hours,
        zone_names,
        system_load=demand.sum(axis=0),
        wind_gen=(wind_cap[:, None] * wind_cf).sum(axis=0),
        solar_gen=(solar_cap[:, None] * solar_cf).sum(axis=0),
        sim_year=year,
    )

    # P0 → monthly startup markup → P1 via the shared pipeline solve core
    # (orchestrator-unification Stage 3): the intra-year warm start, the
    # cross-year warm-start seam (xyear_cache threaded from the multi-year
    # loop, basis exported even when the XYEAR flag is off so a downstream A/B
    # does not depend on call ordering), and the startup-markup config gates
    # all moved to pipeline.solve.run_energy_solve statement-for-statement.
    # P1-native CAISO RA must-offer bridge: the hook floors the merchant gas
    # CC/CT fleet from the P0 run pattern before the P1 clearing solve, so the
    # RA structure rides the scored P1 pass (P2 is archived — CLAUDE.md: P0/P1
    # only). None for every non-CAISO / non-RA run (byte-identical).
    ra_p1_prep = build_caiso_ra_p1_prep(
        config,
        iso,
        fleet,
        fleet_arrays,
        mc_base,
        renewable_potential_mw=(
            (wind_cap[:, None] * wind_cf) + (solar_cap[:, None] * solar_cf)
        ).sum(axis=0),
    )
    # P1-native PJM commitment-scoped reserve supply (path B, G-20b): the fleet
    # hook zeroes non-fast-start reserve-eligible units' availability in their
    # plant's P0-offline hours (the fa_p2-style mask), the kwargs hook
    # recomputes the deliverable reserve-supply cap on the masked fleet. (None,
    # None) for every non-PJM / gate-off run (byte-identical). ISO-exclusive
    # with the CAISO hook, so at most one fleet prep is ever non-None.
    pjm_fleet_prep, pjm_kwargs_prep = build_pjm_reserve_p1_prep(
        config, iso, fleet_arrays
    )
    energy_solve = run_energy_solve(
        fleet,
        fleet_arrays,
        demand,
        mc_base,
        dispatch_kwargs,
        config,
        xyear_cache=xyear_cache,
        p1_fleet_prep=ra_p1_prep or pjm_fleet_prep,
        p1_kwargs_prep=pjm_kwargs_prep,
        mc_bid_adjust=offer_surface_mc_bid_adjust,
    )
    result = energy_solve.p1
    mc_bid = energy_solve.mc_bid
    # The fleet P1 actually solved on — the RA-floored fleet when the bridge
    # fired, else the input fleet unchanged. Persist ITS min_gen as the P1 pass's
    # floors and expose it downstream (D-2 forced-energy attribution).
    fleet_arrays = energy_solve.p1_fleet_arrays

    context = FleetContext.from_arrays(
        fleet_arrays,
        iso_config,
        wind_cf,
        wind_cap,
        solar_cf,
        solar_cap,
        storage.energy_cap,
    )
    # Everything the P2 commitment pass needs, kept so P2 can be re-run as a
    # post-process (see _commitment_pass / run_p2) without re-solving P0/P1.
    p2_state = {
        "year": year,
        "iso": iso,
        "fleet": fleet,
        "fleet_arrays": fleet_arrays,
        "mc_base": mc_base,
        "mc_bid": mc_bid,
        "p1_result": result,
        "demand": demand,
        "dispatch_kwargs": dispatch_kwargs,
        "config": config,
        "context": context,
        "storage_units": storage_units,
        "dual_fuel_oil_mask": dual_fuel_oil_mask,
        # Zone-name list for the shared P2 core's NYISO path B (Stage 4);
        # older pickled p2_states predate the key (the core requires it only
        # when that branch fires).
        "zone_names": zone_names,
        # Link list in flow-column order (the possibly import-node-extended /
        # per-hub-split topology actually solved), so the bundle can persist
        # per-link flows for interface-binding diagnostics (the MISO zonal
        # gates report binding-hour counts per CIL/CEL group and the RDT).
        "links": iso_config.links,
    }

    # P2 (ARCHIVED — last resort, CLAUDE.md "Dispatch & Commitment"): the
    # optional third LP solve. P0/P1 are the only production passes and every run
    # is scored on P1; P2 runs only when a legacy diagnostic gate is explicitly
    # set. The CAISO RA must-offer bridge NO LONGER triggers P2 — it is applied
    # P1-native above (build_caiso_ra_p1_prep). ERCOT AS-aware commitment stays a
    # P2 trigger, reachable only behind the CLI's --enable-legacy-p2 unlock; it
    # values a unit's own P1 reserve dual in the screen and needs the
    # multi-product co-opt to supply the per-product reserve duals.
    as_aware = (
        getattr(config, "ercot_as_aware_commitment", False)
        and iso == "ERCOT"
        and getattr(config, "energy_reserve_coopt", False)
    )
    result_p1 = None
    if config.commitment_enabled or as_aware:
        result_p1 = result
        result = _commitment_pass(p2_state)

    return result, context, result_p1, p2_state


# Stage 4 (orchestrator unification): the P2 commitment body moved to the
# shared core (``market_sim.pipeline.commitment.run_commitment_pass``) — one
# commitment pass for both orchestrators. The old name is kept as the seam
# ``run_calibration_full`` imports (bundle writer + the ``run_p2`` pickled-state
# re-run path); it accepts the same ``(state, config=None)`` signature and
# stashes ``state["fleet_arrays_p2"]`` exactly as before.
_commitment_pass = run_commitment_pass


def _generation_twh(result, context: FleetContext) -> dict[str, float]:
    """Return modeled annual generation by fuel (TWh)."""
    gen_per_unit = result.dispatch.sum(axis=1)
    twh: dict[str, float] = {}
    for g, fuel in enumerate(context.fuel_types):
        twh[fuel] = twh.get(fuel, 0.0) + float(gen_per_unit[g]) / _MWH_PER_TWH
    twh["wind"] = (
        twh.get("wind", 0.0) + float(result.wind_dispatched.sum()) / _MWH_PER_TWH
    )
    twh["solar"] = (
        twh.get("solar", 0.0) + float(result.solar_dispatched.sum()) / _MWH_PER_TWH
    )
    return twh


def _print_table(title: str, rows: list[tuple]) -> None:
    """Print a titled, column-aligned text table."""
    print(f"\n  {title}")
    widths = [max(len(str(r[c])) for r in rows) for c in range(len(rows[0]))]
    for row in rows:
        cells = [str(row[c]).rjust(widths[c]) for c in range(len(row))]
        print("    " + "  ".join(cells))


def _report_year(
    year: int, iso: str, result, context: FleetContext, reference: dict, label: str = ""
) -> None:
    """Print the calibration diagnostics for one solved ISO-year."""
    tag = f"  [{label}]" if label else ""
    print(f"\n{'=' * 64}")
    print(f"  Calibration: {iso} {year}   (status: {result.status}){tag}")
    print(f"{'=' * 64}")

    model_twh = _generation_twh(result, context)
    # The benchmark is EIA-923 by-fuel net generation for the run year --
    # unlike the eGRID plant snapshot, its totals sum to the balancing
    # authority's actual net generation. Compared only for a full 8760-hour
    # run; a sub-annual horizon (--hours) is a smoke test, not a backcast.
    full_year = result.dispatch.shape[1] >= HOURS_PER_YEAR
    year_ref = reference.get("isos", {}).get(iso, {}).get(str(year), {})
    bench_twh = year_ref.get("generation_twh", {}) if full_year else {}
    if not full_year:
        print(
            f"\n  NOTE: {result.dispatch.shape[1]}-hour run -- EIA-923 "
            "benchmark comparison suppressed (full 8760h required)."
        )
    # The EIA-923 monthly file for the current year is preliminary until
    # the annual revision (typically Sep of the following year): it
    # under-reports renewable generation by ~30 TWh because small / new
    # wind and solar plants are slow to submit Form 923. Flag that here
    # so the "+13.6% total" gap is read as a benchmark gap, not a model
    # error. The EIA-930 hourly extract is the more complete reference
    # for the current year (see the calibration_reference.json
    # ``eia930_total_twh`` block).
    if full_year and iso == "ERCOT" and year >= 2025:
        print(
            "\n  NOTE: ERCOT 2025 EIA-923 monthly file is preliminary "
            "(released Feb 2026). It under-reports renewable generation "
            "by ~30 TWh vs EIA-930 hourly metered output; expect "
            "+10-15% model-vs-EIA-923 gaps until the annual revision."
        )

    fuels = sorted(set(model_twh) | set(bench_twh))
    gen_rows: list[tuple] = [("fuel", "model TWh", "EIA-923 TWh", "diff %")]
    for fuel in fuels:
        m = model_twh.get(fuel, 0.0)
        b = bench_twh.get(fuel)
        if b is None:
            gen_rows.append((fuel, f"{m:.2f}", "—", "—"))
        else:
            diff = 100.0 * (m - b) / b if b else float("inf")
            gen_rows.append((fuel, f"{m:.2f}", f"{b:.2f}", f"{diff:+.1f}"))
    total_m = sum(model_twh.values())
    total_b = sum(bench_twh.values()) if bench_twh else None
    gen_rows.append(
        (
            "TOTAL",
            f"{total_m:.2f}",
            f"{total_b:.2f}" if total_b else "—",
            f"{100.0 * (total_m - total_b) / total_b:+.1f}" if total_b else "—",
        )
    )
    _print_table("Generation by fuel", gen_rows)

    emissions_t = float(
        compute_emissions(result.dispatch, np.asarray(context.emission_rate)).sum()
    )
    model_co2 = emissions_t / _TONNES_PER_MT
    # The EIA-923 Page 1 benchmark carries no CO2; report modeled CO2 alone.
    print(f"\n  CO2 emissions\n    model {model_co2:.2f} Mt")

    price_rows: list[tuple] = [("zone", "avg $/MWh", "neg-price hrs")]
    iso_config = get_iso_config(iso)
    for z, zone in enumerate(iso_config.zone_names):
        zone_price = result.prices[z]
        price_rows.append(
            (
                zone,
                f"{zone_price.mean():.2f}",
                str(int((zone_price < 0.0).sum())),
            )
        )
    system_price = result.prices.mean(axis=0)
    price_rows.append(
        (
            "SYSTEM",
            f"{system_price.mean():.2f}",
            str(int((system_price < 0.0).sum())),
        )
    )
    _print_table("Zonal prices", price_rows)

    _report_curtailment(year, iso, result, context, full_year)

    _report_hourly_correlation(year, iso, result, context, full_year)


def _report_curtailment(
    year: int, iso: str, result, context: FleetContext, full_year: bool
) -> None:
    """Print the headline modeled-vs-reported renewable curtailment metric.

    Modeled curtailment is the dispatch's unused wind/solar potential. For
    ISO-years with a built HSL-style parquet (scripts/build_ercot_hsl.py /
    build_caiso_hsl.py) the reported curtailment — the telemetered
    ``hsl - gen`` — is printed beside it, with the monthly shape (the CAISO
    P6 / ERCOT E3 headline metric): a transmission-constrained dispatch fed
    uncurtailed potential should reproduce both the level and the
    seasonality of real curtailment. The reported comparison is suppressed
    on a sub-annual smoke run, and the table falls back to model-only
    columns when no HSL data covers the year.
    """
    hsl = load_hsl_hourly(iso, year)
    compare = hsl is not None and full_year

    caps = {"wind": context.wind_cap_mw, "solar": context.solar_cap_mw}
    potential = {
        "wind": context.wind_potential_mwh,
        "solar": context.solar_potential_mwh,
    }
    dispatched = {
        "wind": np.asarray(result.wind_dispatched, dtype=float).sum(axis=0),
        "solar": np.asarray(result.solar_dispatched, dtype=float).sum(axis=0),
    }

    rows: list[tuple] = [
        (
            "resource",
            "installed GW",
            "potential TWh",
            "model TWh",
            "model %",
            "reported TWh",
            "reported %",
        )
    ]
    for fuel in ("wind", "solar"):
        pot_mwh = potential[fuel]
        curt_mwh = max(pot_mwh - float(dispatched[fuel].sum()), 0.0)
        reported_twh = reported_pct = "—"
        if compare:
            rep_curt = float(
                (hsl[f"{fuel}_hsl_mw"] - hsl[f"{fuel}_gen_mw"]).clip(lower=0.0).sum()
            )
            rep_pot = float(hsl[f"{fuel}_hsl_mw"].sum())
            reported_twh = f"{rep_curt / _MWH_PER_TWH:.2f}"
            reported_pct = f"{100.0 * rep_curt / rep_pot:.1f}" if rep_pot > 0 else "—"
        rows.append(
            (
                fuel,
                f"{caps[fuel] / 1e3:.2f}",
                f"{pot_mwh / _MWH_PER_TWH:.2f}",
                f"{curt_mwh / _MWH_PER_TWH:.2f}",
                f"{100.0 * curt_mwh / pot_mwh:.1f}" if pot_mwh > 0 else "—",
                reported_twh,
                reported_pct,
            )
        )
    _print_table("Renewable curtailment — modeled vs reported", rows)
    if hsl is None:
        print(
            f"    (no reported HSL data for {iso} {year}; build with "
            "scripts/build_ercot_hsl.py / build_caiso_hsl.py — ERCOT 2024+ "
            "needs the NP6 report uploads)"
        )
        return
    if not compare:
        print("    (reported comparison suppressed -- full 8760h run required)")
        return

    # Monthly shape: model re-curtailment vs reported, GWh per month. The
    # model's hourly potential is the same rescaled HSL series the dispatch
    # consumed (renewables.hsl_potential_mw), so the comparison isolates
    # *when* the model curtails, not profile-construction differences.
    month_idx = _hour_to_month_index(HOURS_PER_YEAR)
    monthly: dict[str, np.ndarray] = {}
    for fuel in ("wind", "solar"):
        pot_mw = hsl_potential_mw(iso, year, fuel)
        model_curt = np.clip(pot_mw - dispatched[fuel][:HOURS_PER_YEAR], 0.0, None)
        rep_curt = (
            (hsl[f"{fuel}_hsl_mw"] - hsl[f"{fuel}_gen_mw"])
            .clip(lower=0.0)
            .to_numpy(dtype=float)
        )
        monthly[f"{fuel}_model"] = (
            np.bincount(month_idx, weights=model_curt, minlength=12) / 1e3
        )
        monthly[f"{fuel}_reported"] = (
            np.bincount(month_idx, weights=rep_curt, minlength=12) / 1e3
        )
    monthly_rows: list[tuple] = [
        ("month", "wind model", "wind rptd", "solar model", "solar rptd"),
    ]
    for m in range(12):
        monthly_rows.append(
            (
                str(m + 1),
                f"{monthly['wind_model'][m]:.0f}",
                f"{monthly['wind_reported'][m]:.0f}",
                f"{monthly['solar_model'][m]:.0f}",
                f"{monthly['solar_reported'][m]:.0f}",
            )
        )
    _print_table("Monthly curtailment (GWh)", monthly_rows)


def _report_hourly_correlation(
    year: int, iso: str, result, context: FleetContext, full_year: bool
) -> None:
    """Print the modeled-vs-EIA-930 hourly dispatch correlation for coal/gas.

    Compares the shape of the hourly dispatch — not just annual totals — so
    a model that hits the right yearly TWh by running flat when the real
    fleet cycled is still visible. ERCOT only, and only for a full 8760-hour
    run (the EIA-930 fossil series is a whole-year extract).
    """
    if iso != "ERCOT" or not full_year:
        return
    eia_hourly = load_ercot_fossil_gen(year)
    if eia_hourly is None:
        print(
            "\n  Hourly dispatch correlation\n    (no EIA-930 fossil "
            f"series for {year})"
        )
        return

    coal = np.zeros(result.dispatch.shape[1])
    gas = np.zeros(result.dispatch.shape[1])
    for g, fuel in enumerate(context.fuel_types):
        if fuel == "coal":
            coal += result.dispatch[g]
        elif fuel in _GAS_FUEL_TYPES:
            gas += result.dispatch[g]

    stats = check_hourly_dispatch_correlation({"coal": coal, "gas": gas}, eia_hourly)
    rows: list[tuple] = [("fuel", "pearson r", "nrmse", "model TWh", "EIA TWh")]
    for fuel in ("coal", "gas"):
        s = stats[fuel]
        rows.append(
            (
                fuel,
                f"{s['pearson_r']:.3f}",
                f"{s['nrmse']:.3f}",
                f"{s['model_twh']:.2f}",
                f"{s['eia_twh']:.2f}",
            )
        )
    _print_table("Hourly dispatch correlation (vs EIA-930)", rows)


def _build_parser() -> argparse.ArgumentParser:
    """Return the run_calibration argument parser."""
    parser = argparse.ArgumentParser(
        prog="run_calibration",
        description="Run dispatch for calibration years and compare to EIA.",
    )
    parser.add_argument(
        "--year",
        type=int,
        nargs="+",
        required=True,
        help="One or more calibration years (2021-2024).",
    )
    parser.add_argument(
        "--iso",
        default="ERCOT",
        help="ISO to calibrate (default ERCOT).",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=8760,
        help="Dispatch horizon in hours (default 8760; 168 for a quick test).",
    )
    parser.add_argument(
        "--ttc-wn",
        type=float,
        default=None,
        help="Override the West<->North transfer capability (MW).",
    )
    parser.add_argument(
        "--ttc-wsc",
        type=float,
        default=None,
        help="Override the West<->South_Central transfer capability (MW).",
    )
    parser.add_argument(
        "--ttc-pn",
        type=float,
        default=None,
        help="Override the Panhandle<->North transfer capability (MW).",
    )
    parser.add_argument(
        "--coal-passthrough",
        type=float,
        default=None,
        help="Override coal_prb_contract_passthrough (PRB take-or-pay "
        "fuel-cost fraction); 1.0 disables the discount.",
    )
    parser.add_argument(
        "--enable-legacy-p2",
        action="store_true",
        help="Unlock the ARCHIVED P2 commitment pass (last resort). P0/P1 are the "
        "only production passes and every run is scored on P1. --commitment / "
        "--no-coal-p2 are hidden and inert unless this is passed.",
    )
    parser.add_argument(
        "--commitment",
        action="store_true",
        # ARCHIVED P2 trigger — hidden from --help, gated behind --enable-legacy-p2.
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--no-coal-p2",
        action="store_true",
        # ARCHIVED P2 knob — hidden; only meaningful under --enable-legacy-p2.
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--priced-interchange",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Serve interchange through the priced import/export node "
        "(import tranches + export sinks in the ISO's external zone) "
        "instead of the measured schedule added to demand. Default per "
        f"ISO: on for {', '.join(sorted(PRICED_INTERCHANGE_DEFAULT_ISOS))} "
        "(no measured-schedule mode), off elsewhere; pass "
        "--no-priced-interchange to force the measured schedule.",
    )
    parser.add_argument(
        "--reference-price-interface",
        action="store_true",
        help="Serve the priced-interchange seam through the forecast-grade "
        "reference-price interface (per-neighbor gas x heat-rate x "
        "load-shape, cleared on the spread vs the ISO LMP with a hurdle) "
        "instead of the fitted IMPORT_TRANCHES/EXPORT_TRANCHES. Implies "
        "--priced-interchange; gated to ISOs in INTERFACE_NEIGHBORS (PJM). "
        "See docs/reference-price-interface.md.",
    )
    parser.add_argument(
        "--negative-renewable-offers",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Floor the curtailable wind/solar dispatch offer at the negative "
        "keep-running (REC/PTC) value so curtailed renewables set a "
        "sub-$0 marginal price in oversupply (CAISO negative midday "
        "LMPs). Default (unset) keeps the per-ISO base config value (ON "
        "for CAISO); --no-negative-renewable-offers forces it off.",
    )
    parser.add_argument(
        "--mass-cap-enabled",
        action="store_true",
        help="Thread the unified carbon resolver's power-sector mass-cap "
        "ROW (policy.cap_and_trade.resolve_carbon_program) into this "
        "calibration year instead of the default measured-price adder "
        "(G-29, docs/handoffs/emissions-mass-cap-plan-2026-07.md). "
        "Diagnostic-only (e.g. the RGGI dual-vs-auction-price validation "
        "probe); never a keeper default. No effect on ISOs with no "
        "cap-and-trade program (ERCOT/MISO) or no published budget for "
        "the requested year.",
    )
    parser.add_argument(
        "--mass-cap-tons",
        type=float,
        default=None,
        help="Explicit annual mass-cap budget (metric tons CO2), overriding "
        "the ISO program's published schedule. Only meaningful with "
        "--mass-cap-enabled.",
    )
    parser.add_argument(
        "--mass-cap-program",
        default=None,
        help="Label override for the mass-cap row's reported allowance "
        "price. Only meaningful with --mass-cap-enabled.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point: run each requested calibration year and print diagnostics.

    Args:
        argv: Argument vector to parse. Defaults to ``sys.argv[1:]``.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    # P2 is ARCHIVED (P0/P1 only; scored on P1). Reaching for it without the
    # explicit unlock is a hard error so it is never a silent calibration option.
    if (args.commitment or args.no_coal_p2) and not args.enable_legacy_p2:
        parser.error(
            "the P2 commitment pass is ARCHIVED (P0/P1 only; runs are scored on "
            "P1). --commitment / --no-coal-p2 require --enable-legacy-p2 to run "
            'P2 as a last resort. See CLAUDE.md "Dispatch & Commitment".'
        )
    iso = args.iso.upper()
    # The reference-price interface is on when the CLI flag is set OR the ISO is
    # in the per-ISO default-on set (MISO); see resolve_reference_price_interface.
    reference_price_interface = resolve_reference_price_interface(
        args.reference_price_interface, iso
    )
    priced_interchange = resolve_priced_interchange(args.priced_interchange, iso)
    # The reference-price interface serves the seam through the priced node, so
    # it implies priced interchange (unless explicitly turned off on the CLI).
    if reference_price_interface and args.priced_interchange is not False:
        priced_interchange = True
    reference = _load_reference()
    ttc_overrides = {
        "ttc_wn": args.ttc_wn,
        "ttc_wsc": args.ttc_wsc,
        "ttc_pn": args.ttc_pn,
    }

    # Single-element holder carrying the prior year's optimal basis across
    # run_year calls for cross-year warm-start (MARKET_SIM_WARMSTART_XYEAR=1).
    # Years are run in the order requested, so listing them chronologically lets
    # each P0 warm-start from the adjacent year's basis.
    xyear_cache: list = []
    for year in args.year:
        gas_price = _henry_hub_actual(reference, year)
        logger.info(
            "running %s %d (hours=%d, Henry Hub=$%.2f/MMBtu)",
            iso,
            year,
            args.hours,
            gas_price,
        )
        result, context, result_p1, _ = run_year(
            year,
            iso,
            args.hours,
            gas_price,
            ttc_overrides,
            args.coal_passthrough,
            commitment_enabled=args.commitment,
            commitment_screen_coal=not args.no_coal_p2,
            priced_interchange=priced_interchange,
            reference_price_interface=reference_price_interface,
            negative_renewable_offers=args.negative_renewable_offers,
            mass_cap_enabled=args.mass_cap_enabled,
            mass_cap_tons=args.mass_cap_tons,
            mass_cap_program=args.mass_cap_program,
            xyear_cache=xyear_cache,
        )
        if result_p1 is not None:
            _report_year(year, iso, result_p1, context, reference, label="P1")
            _report_year(year, iso, result, context, reference, label="P2")
        else:
            _report_year(year, iso, result, context, reference)


if __name__ == "__main__":
    main()
