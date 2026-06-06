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
from dataclasses import fields
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.eia_loader import (  # noqa: E402
    load_demand,
    load_ercot_fossil_gen,
)
from market_sim.data.fleet import (  # noqa: E402
    _AGGREGATABLE_FUELS,
    COAL_MUSTRUN_BY_PLANT,
    aggregate_fleet,
    apply_coal_tranches,
    assemble_mc,
    bins_to_fleet,
    campd_tranche_fuel_frac,
    fleet_to_bins,
    generators_to_fleet_arrays,
    load_campd_bins,
    load_fleet_from_csv,
    split_coal_tranches,
    split_gas_tranches,
    thermal_tranche_overrides,
)
from market_sim.data.fuel import (  # noqa: E402
    apply_coal_supply_pricing,
    apply_plant_monthly_fuel_prices,
    prb_passthrough_series,
    prb_passthrough_series_follower,
    resolve_fuel_prices,
)
from market_sim.data.renewables import (  # noqa: E402
    inject_offshore_wind_availability,
    load_renewable_profiles,
)
from market_sim.model.commitment import (  # noqa: E402
    apply_commitment_with_coal_pin,
    compute_commitment,
    compute_monthly_markup,
)
from market_sim.model.dispatch import solve_dispatch  # noqa: E402
from market_sim.model.storage import (  # noqa: E402
    load_eia860_storage,
    storage_units_to_arrays,
)
from market_sim.model.transmission import (  # noqa: E402
    build_incidence_matrix,
    get_ttc_array,
)
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from market_sim.policy.eac import (  # noqa: E402
    apply_eac_to_mc,
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
REFERENCE_PATH: Path = REPO / "inputs" / "calibration" / "calibration_reference.json"

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


def _deep_merge_offer_curve(
    base: dict[str, dict[str, float]],
    overrides: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    """Deep-merge ``overrides`` onto the default ``offer_curve_by_group``.

    Each top-level key is a fleet class (CC_REGULAR, CT_PEAKER, ...); the
    nested dict holds the band multipliers (committed, econ_low, econ_high,
    peak, econ_low_share, pct_peaking). Only the bands named in ``overrides``
    are replaced; every unspecified band keeps its calibrated default, so a
    caller can tune one knob on one class without restating the whole curve.
    Unknown classes/bands are passed through unchanged (the dispatch code
    ignores keys it does not consume) so a typo fails loudly downstream
    rather than being silently dropped here.
    """
    merged = {cls: dict(bands) for cls, bands in base.items()}
    for cls, bands in overrides.items():
        if not isinstance(bands, dict):
            raise ValueError(
                f"offer-curve override for {cls!r} must be an object of "
                f"band->multiplier, got {type(bands).__name__}")
        merged.setdefault(cls, {}).update(bands)
    return merged


def _apply_offer_curve_deltas(
    base: dict[str, dict[str, float]],
    deltas: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    """Return ``base`` with each ``deltas`` value ADDED to the current band.

    Unlike :func:`_deep_merge_offer_curve` (absolute replacement), this nudges
    a band relative to whatever it already is: ``{"CT_PEAKER":{"committed":0.05}}``
    turns a 1.40 committed multiplier into 1.45, and ``-0.05`` into 1.35 — so a
    re-tune does not have to restate the absolute value. The class/band must
    already exist in ``base`` (you can only nudge a band the offer curve
    actually has); an unknown one raises with the valid options listed.
    """
    merged = {cls: dict(bands) for cls, bands in base.items()}
    for cls, bands in deltas.items():
        if cls not in merged:
            raise ValueError(
                f"offer-curve delta for unknown class {cls!r}; valid classes: "
                f"{', '.join(sorted(merged))}")
        if not isinstance(bands, dict):
            raise ValueError(
                f"offer-curve delta for {cls!r} must be an object of "
                f"band->delta, got {type(bands).__name__}")
        for band, delta in bands.items():
            if band not in merged[cls]:
                raise ValueError(
                    f"offer-curve delta for unknown band {cls}.{band!r}; "
                    f"{cls} bands: {', '.join(sorted(merged[cls]))}")
            merged[cls][band] = merged[cls][band] + delta
    return merged



def _calibration_config(
    year: int, iso: str, hours: int, gas_price: float,
    coal_passthrough: float | None = None,
    commitment_enabled: bool = False,
    commitment_screen_coal: bool = True,
    coal_lignite_mustrun: float | None = None,
    coal_prb_mustrun: float | None = None,
    coal_prb_passthrough: float = 1.0,
    outage_source: str = "historic",
    coal_prb_passthrough_sigmoid: bool = False,
    coal_mustrun_per_plant: bool = False,
    coal_drop_pof: bool = False,
    coal_prb_passthrough_tiered: bool = False,
    offer_curve_overrides: dict[str, dict[str, float]] | None = None,
    offer_curve_deltas: dict[str, dict[str, float]] | None = None,
):
    """Build the ScenarioConfig for one calibration year.

    The calibration configuration fixes the structural and policy levers to
    their backcast values: the weather year is the calibration year, the
    EIA-860 vintage capacity ramp is on, the EIA-930 generation-side demand
    is used without a T&D gross-up, gas seasonality is on, and the carbon
    price and RPS constraint are off.

    The measured Henry Hub price is applied through ``gas_price_override``
    when that field exists on :class:`ScenarioConfig`; otherwise the run
    falls back to the configured ``gas_price_path`` trajectory.

    Args:
        year: Calibration year.
        iso: ISO identifier.
        hours: Dispatch horizon in hours.
        gas_price: Measured Henry Hub annual price ($/MMBtu).

    Returns:
        The calibration :class:`ScenarioConfig`.
    """
    config = ScenarioConfig(
        weather_year=year,
        iso=iso,
        hours=hours,
        vintage_capacity_ramp=True,
        td_loss_factor=0.0,  # EIA-930 demand is generation-side
        #   (Demand + Interchange = Net Generation); no gross-up so the grid
        #   demand target equals actual grid net generation and BTM CHP
        #   self-supply stays off-grid. See ScenarioConfig.td_loss_factor.
        gas_seasonality=True,
        carbon_price=0.0,
        rps_enabled=False,
        commitment_enabled=commitment_enabled,  # P1-only by default: the
        #   3-tranche, no-Pmin bin structure dispatches correctly without the
        #   P2 screen. Opt in with --commitment to add the unit-commitment pass.
        commitment_screen_coal=commitment_screen_coal,
        wefor_multiplier=0.7,  # lighten thermal forced-outage rates ~30%
        #   (shape preserved) so coal can hold its shoulder-month output
        #   rather than being availability-capped in spring/autumn.
        coal_prb_passthrough=coal_prb_passthrough,  # default 1.0 = OFF (it is
        #   gas-price fragile; coal level set by the must-run floor). Set via
        #   --coal-prb-passthrough to re-test the price-taking discount.
        coal_lignite_mustrun_override=coal_lignite_mustrun,
        coal_prb_mustrun_override=coal_prb_mustrun,
        outage_source=outage_source,  # backcast pins actual coal/CC outages;
        #   "statistical" reverts to the WEFOR/POF availability model.
        nearby_fuel_price_fallback=(iso.upper() != "ERCOT"),  # merchant-heavy
        #   ISOs (PJM) have many plants that file no EIA-923 delivered cost;
        #   fill those months from state/zone neighbours before the Henry Hub
        #   curve. Off for ERCOT, whose plants overwhelmingly report.
        plant_level_fleet=(iso.upper() != "ERCOT"),  # non-ERCOT ISOs run the
        #   per-plant EIA-860 fleet (no efficiency-bin aggregation) so the
        #   per-plant fuel cost and CAMPD outage overlay bind to real plants.
        #   ERCOT builds its fleet from CAMPD bins, so this path is unused.
        coal_plant_monthly_pricing=True,  # plant-specific EIA-923 monthly coal
        #   cost where reported (Fayette/San Miguel/J K Spruce); the rest fall
        #   back to the flat lignite/PRB average.
        coal_prb_passthrough_sigmoid=coal_prb_passthrough_sigmoid,  # gas-keyed
        #   PRB passthrough when set; else the flat coal_prb_passthrough.
        coal_mustrun_per_plant=coal_mustrun_per_plant,  # per-plant CAMPD coal
        #   must-run floors when set; else the uniform lignite/PRB overrides.
        coal_drop_pof=coal_drop_pof,  # drop statistical POF on coal (planned
        #   maintenance now comes from the historic outage overlay).
        coal_prb_passthrough_tiered=coal_prb_passthrough_tiered,  # separate
        #   follower-tier PRB sigmoid for low-must-run load-followers.
        gas_st_startup_spread=True,  # amortize ST_GAS startup over the whole
        #   May-Sep season (one seasonal start), not per calendar month.
        # CC and ST_GAS supply curves now come from the unified offer curve
        # below (offer_curve_by_group), so their legacy override triples are
        # left unset. CT_CHP keeps its legacy override (not in the offer curve).
        cc_committed_per_plant=True,   # ground each CC_REGULAR committed % in
        #   CAMPD-observed minimum stable load (fleet.CC_REGULAR_COMMITTED_PCT_
        #   BY_PLANT) instead of the coarse assumed CSV Pct_Committed.
        cc_peaking_per_plant=True,     # the four F-class(late) 2x1 CCs (CBII,
        #   WH2, Rayburn, Temple) move the duct-burner peak band start to 85%
        #   (pct_peaking 15) so the expensive band bites earlier and they back
        #   down out of the 80-90% CF range (fleet.CC_REGULAR_PEAKING_PCT_BY_PLANT).
        ct_committed_hr_override=1.1,  # CT_CHP supply curve above its must-run
        ct_econ_hr_override=1.2,        # BTM + steam-following floor; raised in
        ct_peak_hr_override=1.4,        # run9 (CT_CHP was running too much).
        # Unified thermal offer curve (operator-supplied band multipliers on
        # AHR x fuel_price; VOM constant across bands). Economic block split
        # into two steps (econ_low / econ_high) by econ_low_share. CC peaking
        # uses the per-plant duct-burner multiplier (turbine class), so no
        # "peak" key. Gas Steam committed kept at the current 0.65x reliability
        # value (per operator); CC and Coal keep their CSV peaking %, while
        # Gas CT -> 7% and Gas Steam -> 15%.
        offer_curve_by_group={
            # CC offer curve fit to Colorado Bend II / Wolf Hollow II observed
            # CAMPD heat-rate curves: marginal HR ~0.95x avg and flat across
            # the operating range, negligible duct-firing. committed/econ are a
            # flat cheap band; peak stays the duct-burner class multiplier;
            # pct_peaking 8% = observed duct-fire headroom. committed % per-plant
            # grounded (cc_committed_per_plant).
            "CC_REGULAR": {"committed": 0.92, "econ_low": 1.06,
                           "econ_high": 1.27, "econ_low_share": 0.50,
                           "pct_peaking": 8.0},
            "CC_CHP": {"committed": 0.92,
                       "econ_low": 1.01 if iso == "PJM" else 0.96,
                       "econ_high": 1.22 if iso == "PJM" else 1.12,
                       "econ_low_share": 0.50,
                       "pct_peaking": 8.0},
            # CT/ST committed band raised as a P1 startup-cost proxy: the
            # part-load committed slice only clears when price is high, so
            # peakers stop parking at ~20% CF for hundreds of hours. CT hurdle
            # is committed 1.55 (peak HR mult 13.15); ST hurdle committed 0.81
            # with a slightly lower econ-high / peak top. The CT committed
            # hurdle / econ-low / peak are an ERCOT calibration tune; PJM keeps
            # its own validated CT curve (committed 1.10, econ_low 1.32,
            # peak 13.0).
            "CT_PEAKER": {"committed": 1.10 if iso == "PJM" else 1.55,
                          "econ_low": 1.32 if iso == "PJM" else 1.27,
                          "econ_high": 1.98,
                          "peak": 13.0 if iso == "PJM" else 13.15,
                          "econ_low_share": 0.526, "pct_peaking": 7.0},
            "ST_GAS": {"committed": 0.81, "econ_low": 1.05,
                       "econ_high": 1.40, "peak": 4.20,
                       "econ_low_share": 0.500, "pct_peaking": 15.0},
            # Coal split by supply: lignite (mine-mouth) raised +0.05 across the
            # board; PRB uses a pure offer curve (sigmoid off) -- higher commit,
            # lower econ-low start, slightly higher econ-high.
            "COAL_LIGNITE": {"committed": 0.95, "econ_low": 1.14,
                             "econ_high": 1.15, "peak": 1.55,
                             "econ_low_share": 0.556},
            "COAL_PRB": {"committed": 0.95, "econ_low": 0.77,
                         "econ_high": 1.19, "peak": 1.48,
                         "econ_low_share": 0.556},
            # Generic bituminous coal (ISOs whose coal isn't ERCOT lignite/PRB,
            # e.g. PURPA-era PJM units): all 10 ERCOT coal plants are supply-
            # classified so this never fires for ERCOT. A flat baseload curve —
            # cheap committed band (0.90) and econ near base HR — keeps coal in
            # merit as baseload instead of the generic 1.15x default backing it
            # out under cheap gas (which left PJM coal ~12 TWh light).
            "COAL": {"committed": 0.90, "econ_low": 0.95,
                     "econ_high": 1.10, "peak": 1.45,
                     "econ_low_share": 0.55},
        },
        chp_steam_following=True,  # model CC/CT/ST_CHP as steam-host cogens:
        #   a per-plant sector-keyed BTM pull-out (fleet.chp_btm_pct) plus a
        #   grid-delivered steam-following min-gen (CHP_PMIN_CF_BY_PLANT - BTM).
        chp_btm_floor_pct=40.0,  # flat fallback only (sector BTM supersedes it).
        # ERCOT's unit-level derate only supplements the facility overlay, so it
        # keeps both. Other ISOs (PJM) derive their unit-level file from ALL
        # CAMPD unit data — the complete outage source — so they drop the
        # redundant facility overlay to avoid double-counting (which crushed
        # coal availability and spiked prices).
        historic_outage_overlay=(iso == "ERCOT"),
    )
    if any(f.name == "gas_price_override" for f in fields(ScenarioConfig)):
        config = config.with_overrides(gas_price_override=gas_price)
    else:
        logger.warning(
            "ScenarioConfig has no gas_price_override field; "
            "year %d falls back to the '%s' gas-price trajectory",
            year, config.gas_price_path,
        )
    if coal_passthrough is not None:
        config = config.with_overrides(
            coal_prb_contract_passthrough=coal_passthrough
        )
    # Operator-supplied per-class/per-band heat-rate multiplier overrides
    # (run_calibration_full --offer-curve-json) deep-merged onto the calibrated
    # defaults above. Only the named bands change; the merged curve is recorded
    # verbatim in the bundle's run_config.json (scenario_config.offer_curve_by_group).
    if offer_curve_overrides:
        config = config.with_overrides(
            offer_curve_by_group=_deep_merge_offer_curve(
                config.offer_curve_by_group, offer_curve_overrides
            )
        )
    # Relative nudges (run_calibration_full --offer-curve-delta-json): added on
    # top of the (possibly absolute-overridden) curve, so the operator can tweak
    # by +/-0.05 without restating the prior value. The resolved absolute curve
    # is still recorded in run_config.json.
    if offer_curve_deltas:
        config = config.with_overrides(
            offer_curve_by_group=_apply_offer_curve_deltas(
                config.offer_curve_by_group, offer_curve_deltas
            )
        )
    return config


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
                    "-".join(sorted(target)), ttc[i], value,
                )
                ttc[i] = value
    return ttc


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
    coal_drop_pof: bool = False,
    coal_prb_passthrough_tiered: bool = False,
    prb_overrides: dict | None = None,
    plant_tranche_config: str | None = None,
    storage_daily_cycling: bool = False,
    gas_offer_curve: bool = False,
    offer_curve_overrides: dict[str, dict[str, float]] | None = None,
    offer_curve_deltas: dict[str, dict[str, float]] | None = None,
) -> tuple[object, FleetContext, object | None]:
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

    Returns:
        A tuple ``(result, context, result_p1, p2_state)``. ``result`` is the
        final dispatch (P2 when commitment is enabled, otherwise P1);
        ``result_p1`` is the pre-commitment P1 result when commitment ran,
        else ``None``; ``p2_state`` is the cached P1 input bundle that
        :func:`_commitment_pass` (the P2 post-process) consumes.
    """
    config = _calibration_config(
        year, iso, hours, gas_price, coal_passthrough,
        commitment_enabled, commitment_screen_coal,
        coal_lignite_mustrun, coal_prb_mustrun,
        coal_prb_passthrough, outage_source,
        coal_prb_passthrough_sigmoid, coal_mustrun_per_plant,
        coal_drop_pof, coal_prb_passthrough_tiered,
        offer_curve_overrides=offer_curve_overrides,
        offer_curve_deltas=offer_curve_deltas,
    )
    # Per-run PRB passthrough sigmoid floor/ceiling tune (run_calibration_full
    # --prb-* flags); None entries leave the ScenarioConfig default in place.
    if prb_overrides:
        config = config.with_overrides(
            **{k: v for k, v in prb_overrides.items() if v is not None})
    # Per-plant tranche-config override sheet (run_calibration_full
    # --plant-tranche-config): each listed plant's tranche shares + band HR
    # multipliers come straight from the CSV, bypassing the offer curve.
    if plant_tranche_config:
        config = config.with_overrides(
            plant_tranche_config_path=plant_tranche_config)
    # Daily SOC-cycling cap (run_calibration_full --storage-daily-cycling):
    # bounds storage perfect foresight to within-day arbitrage.
    if storage_daily_cycling:
        config = config.with_overrides(storage_daily_cycling=True)
    if gas_offer_curve:
        config = config.with_overrides(gas_offer_curve=True)
    iso_config = get_iso_config(iso)
    zone_names = iso_config.zone_names

    demand = load_demand(
        iso, year, iso_config, td_loss_factor=config.td_loss_factor
    )
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        iso, year, iso_config, config
    )
    if config.hours < demand.shape[1]:
        demand = demand[:, :config.hours]
        wind_cf = wind_cf[:, :config.hours]
        solar_cf = solar_cf[:, :config.hours]

    incidence = build_incidence_matrix(iso_config.links, zone_names)
    ttc = _apply_ttc_overrides(
        iso_config, get_ttc_array(iso_config.links), ttc_overrides
    )

    # Build the dispatch fleet the same way the runner does: CAMPD
    # operational bins for ERCOT (three stepped tranches per bin, nuclear
    # and other non-aggregatable units from EIA-860), the legacy
    # equal-width heat-rate binning otherwise.
    campd_bins = (
        load_campd_bins(config.campd_bins_path)
        if config.use_campd_bins and iso == "ERCOT"
        else None
    )
    if campd_bins is not None:
        campd_fleet, _ = bins_to_fleet(campd_bins, zone_names, config)
        non_thermal = [
            g for g in load_fleet_from_csv(iso, iso_config)
            if g.fuel_type not in _AGGREGATABLE_FUELS
        ]
        fleet = non_thermal + campd_fleet
        # Must-run tranches bid at VOM + carbon + NOx only — fuel sunk
        # under take-or-pay coal contracts, CHP host steam obligations or
        # ERCOT RUC. PRB coal tranches above must-run price-take: they pass
        # only coal_prb_passthrough of their fuel cost into the bid so
        # baseloaded PRB clears the merit order instead of being priced out
        # by cheap gas. apply_coal_tranches applies both discounts.
        # PRB above-must-run passthrough: flat scalar, or an (T,) gas-keyed
        # sigmoid when config.coal_prb_passthrough_sigmoid is set. When tiered,
        # low-floor load-follower PRB plants get the follower-tier sigmoid.
        prb_pt = prb_passthrough_series(config, year, config.hours)
        if (config.coal_prb_passthrough_sigmoid
                and config.coal_prb_passthrough_tiered):
            foll_pt = prb_passthrough_series_follower(
                config, year, config.hours
            )
            thr = config.coal_prb_follower_mustrun_max

            def _pt_for(g):
                if (g.fuel_type == "coal"
                        and getattr(g, "coal_supply", "") == "prb"
                        and COAL_MUSTRUN_BY_PLANT.get(
                            g.plant_code, 100.0) <= thr):
                    return foll_pt
                return prb_pt
            fuel_fracs = [campd_tranche_fuel_frac(g, _pt_for(g)) for g in fleet]
        else:
            fuel_fracs = [campd_tranche_fuel_frac(g, prb_pt) for g in fleet]
    else:
        # Per-plant calibration fleet (plant_level_fleet) keeps each EIA-860
        # unit as its own LP column so plant_code / plant_group / state carry
        # into dispatch — required for per-plant EIA-923 fuel costs and the
        # CAMPD outage overlay to bind. Otherwise use the legacy efficiency-
        # bin aggregation (faster, but identity-free).
        #
        # When the ISO has a CAMPD-derived thermal-tranche artifact
        # (thermal_tranches_<ISO>.csv), give its per-plant thermal fleet the
        # SAME smoothed rising offer curve ERCOT gets: build a synthetic
        # per-plant bins frame (committed / coal must-run from the artifact)
        # and route it through bins_to_fleet, with every non-binned generator
        # (nuclear, oil, biomass, hydro, ...) kept as its own raw LP unit. The
        # binned-keys exclusion guarantees no double-count and no dropped unit.
        if (getattr(config, "plant_level_fleet", False)
                and thermal_tranche_overrides(iso)):
            all_gens = load_fleet_from_csv(iso, iso_config)
            synth = fleet_to_bins(all_gens, iso, config)
            if not synth.empty:
                binned = set(zip(
                    synth["Plant_Code"].astype(int), synth["Plant_Group"]
                ))
                thermal_fleet, _ = bins_to_fleet(synth, zone_names, config)
                non_binned = [
                    g for g in all_gens
                    if (int(g.plant_code), g.plant_group) not in binned
                ]
                fleet = non_binned + thermal_fleet
                prb_pt = prb_passthrough_series(config, year, config.hours)
                fuel_fracs = [
                    campd_tranche_fuel_frac(g, prb_pt) for g in fleet
                ]
            else:
                fleet, fuel_fracs = split_coal_tranches(
                    aggregate_fleet(all_gens, n_bins=0), config
                )
        else:
            n_bins = 0 if getattr(config, "plant_level_fleet", False) \
                else config.heat_rate_bin_count
            fleet_base = aggregate_fleet(
                load_fleet_from_csv(iso, iso_config), n_bins=n_bins,
            )
            fleet, fuel_fracs = split_coal_tranches(fleet_base, config)
            # Optional stepped gas offer curve (committed/economic/peaking
            # heat-rate bands) for the per-plant fleet; off by default.
            if getattr(config, "gas_offer_curve", False):
                fleet, fuel_fracs = split_gas_tranches(fleet, fuel_fracs, config)
    fleet_arrays = generators_to_fleet_arrays(
        fleet, zone_names, hours=config.hours, iso=iso, config=config
    )
    inject_offshore_wind_availability(fleet_arrays, wind_cf, config, iso)

    # Fuel prices: gas/coal base, then the lignite/PRB supply base for coal
    # (our costs), then the actual EIA-923 monthly per-plant delivered cost
    # on top — so measured monthly cost takes precedence and the supply
    # trajectory is only the base/fallback for plant-months without data.
    fuel_prices = resolve_fuel_prices(
        config, fleet_arrays, year, apply_monthly=False
    )
    if config.coal_supply_repricing:
        apply_coal_supply_pricing(fuel_prices, fleet, config, year)
    apply_plant_monthly_fuel_prices(fuel_prices, fleet_arrays, config, year)
    carbon_price = resolve_carbon_price(config, year)
    wind_mc, solar_mc = compute_dispatch_credits(config, year)
    # Base marginal cost: fuel + VOM + carbon + NOx, then exogenous EACs,
    # then the coal take-or-pay tranche discount. No startup-cost markup.
    mc_base = assemble_mc(
        fleet_arrays, fuel_prices, carbon_price, config.nox_price
    )
    apply_eac_to_mc(mc_base, fleet_arrays, config)
    apply_coal_tranches(mc_base, fleet, fleet_arrays, fuel_fracs, fuel_prices)
    wind_eac, solar_eac, storage_eac = compute_eac_dispatch_credits(config)
    wind_mc -= wind_eac
    solar_mc -= solar_eac

    storage = storage_units_to_arrays(
        load_eia860_storage(iso, year, config), zone_names
    )

    dispatch_kwargs = dict(
        wind_cf=wind_cf,
        wind_cap=wind_cap,
        solar_cf=solar_cf,
        solar_cap=solar_cap,
        voll=config.voll,
        incidence=incidence,
        ttc=ttc,
        storage_power_cap=storage.power_cap,
        storage_energy_cap=storage.energy_cap,
        storage_zone_idx=storage.zone_idx,
        eta_chg=storage.eta_chg,
        eta_dis=storage.eta_dis,
        wind_mc=wind_mc,
        solar_mc=solar_mc,
        storage_discharge_eac=storage_eac,
        rps_target=None,
        storage_daily_cycle_hours=24 if config.storage_daily_cycling else None,
        T=config.hours,
    )
    # P0: solve with base MC to extract per-month run lengths.
    r0 = solve_dispatch(fleet_arrays, demand, mc=mc_base, **dispatch_kwargs)
    # P1: solve with bid MC = base MC + monthly startup amortization.
    markup = compute_monthly_markup(
        fleet, fleet_arrays, r0.dispatch, config.hours,
        gas_st_season_spread=config.gas_st_startup_spread,
    )
    mc_bid = mc_base + markup
    result = solve_dispatch(fleet_arrays, demand, mc=mc_bid, **dispatch_kwargs)

    context = FleetContext.from_arrays(
        fleet_arrays, iso_config, wind_cf, wind_cap, solar_cf, solar_cap,
        storage.energy_cap,
    )
    # Everything the P2 commitment pass needs, kept so P2 can be re-run as a
    # post-process (see _commitment_pass / run_p2) without re-solving P0/P1.
    p2_state = {
        "year": year, "iso": iso, "fleet": fleet,
        "fleet_arrays": fleet_arrays, "mc_base": mc_base, "mc_bid": mc_bid,
        "p1_result": result, "demand": demand,
        "dispatch_kwargs": dispatch_kwargs, "config": config,
        "context": context,
    }

    # P2 (optional): screen CC/CT commitment on P1 prices vs base MC, pin
    # coal to its P1 dispatch, and re-solve (a single LP solve).
    result_p1 = None
    if config.commitment_enabled:
        result_p1 = result
        result = _commitment_pass(p2_state)

    return result, context, result_p1, p2_state


def _commitment_pass(state: dict, config=None):
    """Run the P2 commitment pass from a P1 ``state`` dict; return the result.

    Re-uses the cached P1 marginal cost, demand and dispatch inputs, so only
    the single P2 LP solve runs — no P0/P1 re-solve. ``config`` overrides the
    state's config (to iterate commitment params); defaults to the state's.
    This is the seam the P2 post-processing layer uses.
    """
    cfg = config if config is not None else state["config"]
    fleet = state["fleet"]
    fa = state["fleet_arrays"]
    p1 = state["p1_result"]
    dk = state["dispatch_kwargs"]
    committed = compute_commitment(
        p1.prices, state["mc_base"], fleet, fa, cfg,
        storage_charge=p1.storage_charge,
        storage_discharge=p1.storage_discharge,
        storage_zone_idx=dk["storage_zone_idx"], demand=state["demand"],
    )
    fa_p2 = apply_commitment_with_coal_pin(
        fa, committed, p1.dispatch, fleet,
        screen_coal=cfg.commitment_screen_coal,
    )
    return solve_dispatch(fa_p2, state["demand"], mc=state["mc_bid"], **dk)


def _generation_twh(result, context: FleetContext) -> dict[str, float]:
    """Return modeled annual generation by fuel (TWh)."""
    gen_per_unit = result.dispatch.sum(axis=1)
    twh: dict[str, float] = {}
    for g, fuel in enumerate(context.fuel_types):
        twh[fuel] = twh.get(fuel, 0.0) + float(gen_per_unit[g]) / _MWH_PER_TWH
    twh["wind"] = twh.get("wind", 0.0) + float(
        result.wind_dispatched.sum()
    ) / _MWH_PER_TWH
    twh["solar"] = twh.get("solar", 0.0) + float(
        result.solar_dispatched.sum()
    ) / _MWH_PER_TWH
    return twh


def _curtailment_pct(potential: float, dispatched: float) -> float:
    """Return curtailed energy as a percentage of available potential."""
    if potential <= 0.0:
        return 0.0
    return 100.0 * max(potential - dispatched, 0.0) / potential


def _print_table(title: str, rows: list[tuple]) -> None:
    """Print a titled, column-aligned text table."""
    print(f"\n  {title}")
    widths = [max(len(str(r[c])) for r in rows) for c in range(len(rows[0]))]
    for row in rows:
        cells = [str(row[c]).rjust(widths[c]) for c in range(len(row))]
        print("    " + "  ".join(cells))


def _report_year(year: int, iso: str, result, context: FleetContext,
                  reference: dict, label: str = "") -> None:
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
    year_ref = (
        reference.get("isos", {}).get(iso, {}).get(str(year), {})
    )
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
    gen_rows.append((
        "TOTAL", f"{total_m:.2f}",
        f"{total_b:.2f}" if total_b else "—",
        f"{100.0 * (total_m - total_b) / total_b:+.1f}" if total_b else "—",
    ))
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
        price_rows.append((
            zone,
            f"{zone_price.mean():.2f}",
            str(int((zone_price < 0.0).sum())),
        ))
    system_price = result.prices.mean(axis=0)
    price_rows.append((
        "SYSTEM",
        f"{system_price.mean():.2f}",
        str(int((system_price < 0.0).sum())),
    ))
    _print_table("Zonal prices", price_rows)

    wind_curt = _curtailment_pct(
        context.wind_potential_mwh, float(result.wind_dispatched.sum())
    )
    solar_curt = _curtailment_pct(
        context.solar_potential_mwh, float(result.solar_dispatched.sum())
    )
    _print_table("Renewable curtailment", [
        ("resource", "installed GW", "curtailed %"),
        ("wind", f"{context.wind_cap_mw / 1e3:.2f}", f"{wind_curt:.1f}"),
        ("solar", f"{context.solar_cap_mw / 1e3:.2f}", f"{solar_curt:.1f}"),
    ])

    _report_hourly_correlation(year, iso, result, context, full_year)


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
        print("\n  Hourly dispatch correlation\n    (no EIA-930 fossil "
              f"series for {year})")
        return

    coal = np.zeros(result.dispatch.shape[1])
    gas = np.zeros(result.dispatch.shape[1])
    for g, fuel in enumerate(context.fuel_types):
        if fuel == "coal":
            coal += result.dispatch[g]
        elif fuel in _GAS_FUEL_TYPES:
            gas += result.dispatch[g]

    stats = check_hourly_dispatch_correlation(
        {"coal": coal, "gas": gas}, eia_hourly
    )
    rows: list[tuple] = [
        ("fuel", "pearson r", "nrmse", "model TWh", "EIA TWh")
    ]
    for fuel in ("coal", "gas"):
        s = stats[fuel]
        rows.append((
            fuel, f"{s['pearson_r']:.3f}", f"{s['nrmse']:.3f}",
            f"{s['model_twh']:.2f}", f"{s['eia_twh']:.2f}",
        ))
    _print_table("Hourly dispatch correlation (vs EIA-930)", rows)


def _build_parser() -> argparse.ArgumentParser:
    """Return the run_calibration argument parser."""
    parser = argparse.ArgumentParser(
        prog="run_calibration",
        description="Run dispatch for calibration years and compare to EIA.",
    )
    parser.add_argument(
        "--year", type=int, nargs="+", required=True,
        help="One or more calibration years (2021-2024).",
    )
    parser.add_argument(
        "--iso", default="ERCOT", help="ISO to calibrate (default ERCOT).",
    )
    parser.add_argument(
        "--hours", type=int, default=8760,
        help="Dispatch horizon in hours (default 8760; 168 for a quick test).",
    )
    parser.add_argument(
        "--ttc-wn", type=float, default=None,
        help="Override the West<->North transfer capability (MW).",
    )
    parser.add_argument(
        "--ttc-wsc", type=float, default=None,
        help="Override the West<->South_Central transfer capability (MW).",
    )
    parser.add_argument(
        "--ttc-pn", type=float, default=None,
        help="Override the Panhandle<->North transfer capability (MW).",
    )
    parser.add_argument(
        "--coal-passthrough", type=float, default=None,
        help="Override coal_prb_contract_passthrough (PRB take-or-pay "
             "fuel-cost fraction); 1.0 disables the discount.",
    )
    parser.add_argument(
        "--commitment", action="store_true",
        help="Run the P2 unit-commitment pass after P1; both are reported.",
    )
    parser.add_argument(
        "--no-coal-p2", action="store_true",
        help="Pin coal to its P1 dispatch in P2 instead of screening it: "
             "coal gains no new generation in P2 (P1 locks it). Only "
             "meaningful with --commitment.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point: run each requested calibration year and print diagnostics.

    Args:
        argv: Argument vector to parse. Defaults to ``sys.argv[1:]``.
    """
    args = _build_parser().parse_args(argv)
    iso = args.iso.upper()
    reference = _load_reference()
    ttc_overrides = {
        "ttc_wn": args.ttc_wn,
        "ttc_wsc": args.ttc_wsc,
        "ttc_pn": args.ttc_pn,
    }

    for year in args.year:
        gas_price = _henry_hub_actual(reference, year)
        logger.info(
            "running %s %d (hours=%d, Henry Hub=$%.2f/MMBtu)",
            iso, year, args.hours, gas_price,
        )
        result, context, result_p1, _ = run_year(
            year, iso, args.hours, gas_price, ttc_overrides,
            args.coal_passthrough,
            commitment_enabled=args.commitment,
            commitment_screen_coal=not args.no_coal_p2,
        )
        if result_p1 is not None:
            _report_year(year, iso, result_p1, context, reference, label="P1")
            _report_year(year, iso, result, context, reference, label="P2")
        else:
            _report_year(year, iso, result, context, reference)


if __name__ == "__main__":
    main()
