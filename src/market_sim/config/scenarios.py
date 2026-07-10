"""Scenario definitions and loading for simulation runs."""

from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path

import yaml

from market_sim.config.paths import (
    CAMPD_BINS_CSV,
    EIA_860_DIR,
    PLANT_REGISTRY_CSV,
    PROCESSED_DIR,
)

# Config fields introduced after the results cache existed. ``cache_key`` omits
# each from its hash while it holds its default value, keeping every historical
# cache key byte-stable; a non-default value still enters the key.
_CACHE_KEY_OPTIONAL_FIELDS = (
    "start_year",
    "end_year",
    "hindcast",
    "hindcast_fuel_variant",
    # G-30 first-wave probes (default-off): dropped from the hash at default so
    # every pre-existing cached run keeps its key; a non-default value enters
    # the key (a distinct scenario).
    "staged_oversupply_thinning",
    "staged_thinning_max_gw_per_year",
    "limited_foresight_dispatch",
)


@dataclass
class ScenarioConfig:
    """Full configuration for a single simulation scenario.

    Fields are organized into tiers (see ``TIER_TAGS``): structural
    settings, scenario levers, expert sensitivities, and calibration knobs.

    All monetary parameters (fuel prices, carbon prices, VOLL, VOM, LCOE)
    are in 2026 real USD anchored to January 1, 2026. See
    constants.REAL_DOLLAR_BASE_YEAR.
    """

    # Tier 0 (structural)
    weather_year: int = 2024
    iso: str = "ERCOT"
    mode: str = "forecast"  # "forecast" | "backcast". Backcast pins the run
    # to a historical year: renewable capacity resolves to that year's
    # EIA-860 actuals, measured hourly profiles replace the EIA-930-derived
    # statistical ones, and planned additions are not injected. This flag —
    # not the presence of gas_price_override — is the mode signal, so a
    # forecast sensitivity that pins the gas price stays a forecast.
    voll: float = 5000.0  # $/MWh, ERCOT default
    hours: int = 8760

    # Simulation horizon. ``None`` defers to constants.START_YEAR / END_YEAR
    # (2026 / 2050) so the default forecast window and every existing cache key
    # are unchanged; a non-default value narrows the run (e.g. a capacity
    # hindcast 2021→2025). These are omitted from ``cache_key`` when ``None``
    # (see ``_CACHE_KEY_OPTIONAL_FIELDS``) so cache keys stay byte-stable at the
    # default horizon.
    start_year: int | None = None
    end_year: int | None = None
    # Capacity-hindcast mode (W2-P5): forecast machinery run backwards from a
    # vintage fleet snapshot to score capacity evolution against actuals. Stays
    # ``mode == "forecast"`` (the hindcast IS the forecast path) but switches on
    # vintage fleet init, realized per-year demand (no growth scaling) and the
    # 2022 bridge in the harness. Never a backcast overlay. Default-off and
    # cache-neutral; see scripts/run_capacity_hindcast.py and
    # docs/handoffs/forecast-validation-program-2026-07.md §1.
    hindcast: bool = False
    hindcast_fuel_variant: str = "realized"  # "realized" | "asknown"

    # Tier 1 (scenario levers)
    gas_price_path: str = "mid"  # "low", "mid", "high" or path to CSV
    gas_price_factor: float = 1.0  # Forecast-only multiplicative shock applied
    # to the resolved gas_price_path trajectory (data.fuel.resolve_annual_gas_
    # price): factor=1.2 scales every year's Henry Hub value 20% up. The PB-1
    # probability-bounds continuous gas-price sampler axis (docs/handoffs/
    # probability-bounds-plan-2026-07.md §2.1/§2.2); neutral 1.0 reproduces
    # today's trajectory exactly. CRITICAL (rule 13): forecast-only —
    # ScenarioConfig.__post_init__ asserts it stays 1.0 in backcast mode, so
    # it can never become a backcast tuning channel.
    carbon_price: float = 0.0  # $/ton CO2
    carbon_price_path: str = (
        "zero"  # "zero", "low", "mid", "high"; used when carbon_price is 0.0
    )
    policy_bundle: str = "current"  # "current" / "tight" / "rollback" — the
    # PB-1 coherent policy-scenario axis (probability-bounds-plan-2026-07.md
    # §1.2), resolved by config.scenarios.resolve_policy_bundle into
    # carbon_price_path, state_carbon_pricing, and the ira_*_last_year fields
    # at config-build time (the RESOLVED fields, not this label, are what
    # land in run_config.json). "current" is neutral: it overrides nothing,
    # so every field keeps its own legislated-default value (OBBBA IRA
    # schedule, carbon_price_path="zero", state_carbon_pricing=True).
    state_carbon_pricing: bool = True  # Charge the ISO's state carbon-program
    # allowance cost (CA cap-and-trade for CAISO; STATE_CARBON_PRICE_BY_ISO)
    # when carbon_price is 0.0 and the year has a measured allowance price.
    # Only CAISO 2023-2025 is registered, so this is default-on for CAISO
    # backcasts and a no-op everywhere else (ERCOT/PJM have no state program;
    # forward years have no entry and fall through to carbon_price_path).
    # See market_sim.policy.carbon.resolve_carbon_price.
    nox_price: float = 0.0  # $/ton NOx
    so2_price: float = 0.0  # $/ton SO2
    # Emissions mass-cap / cap-and-trade LP row (PP-2.1 IPM parity). GATED,
    # default OFF — cap-off reproduces today's dispatch exactly. When on and a
    # power-sector tonnage budget is supplied (mass_cap_tons, or the published
    # RGGI/CARB schedule once landed), the ISO's fossil emissions are bounded by
    # an inequality row whose dual is the endogenous allowance price
    # (DispatchResult.co2_cap_price). This is a power-sector, no-bank SCENARIO
    # price (docs/handoffs/emissions-mass-cap-plan-2026-07.md §2, §8) — NOT the
    # banked multi-sector RGGI/CARB market price, which enters as the measured/
    # projected adder via resolve_carbon_price. See policy/cap_and_trade.py.
    mass_cap_enabled: bool = False
    mass_cap_program: str | None = None  # pollutant/program label for the row
    mass_cap_tons: float | None = None  # explicit annual budget (tons CO2)
    carbon_program_price_path: str | None = None  # named projected forecast path
    demand_growth_rate: float = (
        0.01  # flat override used only when no structured rates exist
    )
    demand_growth_path: str = (
        "mid"  # "low", "mid", "high" — selects from DEMAND_GROWTH_RATES
    )
    demand_growth_percentile: float = 0.5  # Continuous counterpart of
    # demand_growth_path for the PB-1 sampler (probability-bounds-plan-
    # 2026-07.md §2.1): piecewise-linear interpolation across
    # DEMAND_GROWTH_RATES' low/mid/high near+long-era rates (0.0=low,
    # 0.5=mid, 1.0=high), via config.scenarios.resolve_demand_growth_rate.
    # Neutral 0.5 reproduces demand_growth_path's own selection exactly;
    # percentile only overrides path's choice when moved off 0.5.
    # --- Data-center load block (CX-4, gap G-34). Forecast-mode-only; "off" =
    # today, byte-identical. See docs/handoffs/cx4-datacenter-load-design-2026-
    # 07.md and data/datacenter.py. ---
    datacenter_load_path: str = "off"  # "off" | "low" | "mid" | "high" —
    # deterministic scenario-matrix axis (PB-1 §1.1) selecting the per-ISO
    # cumulative-MW trajectory from constants.DATACENTER_ADDITIONS_MW via
    # data.datacenter.resolve_datacenter_mw. "off" leaves demand byte-identical
    # to today (add_datacenter_block is a no-op).
    datacenter_percentile: float = 0.5  # Continuous PB-2 sampler lever
    # (0.0=low, 0.5=mid, 1.0=high), mirroring demand_growth_percentile /
    # tech_cost_percentile. Neutral 0.5 => datacenter_load_path governs; only
    # takes effect when the sampler moves it off 0.5.
    datacenter_load_factor: float = 0.85  # Flat hourly CF of the DC block.
    # Source: LBNL 2024 US Data Center Energy Usage Report (Shehabi et al.,
    # Dec 2024); EPRI 2024 Powering Intelligence load-factor range 0.8-0.95.
    # Frozen physical input (moves only on a source update, never a residual).
    tech_cost_path: str = "mid"  # "low"/"mid"/"high" -> NREL ATB 2024
    # Advanced/Moderate/Conservative technology-cost cases. The PB-1
    # deterministic scenario-matrix T axis (probability-bounds-plan-2026-07.md
    # §1.1): scales NEW_ENTRY_COSTS' capex_per_kw and learning_rate at
    # config-build time via config.scenarios.resolve_new_entry_costs and
    # constants.TECH_COST_MULTIPLIERS. "mid" is neutral (multiplier 1.0 on
    # every tech), so today's NEW_ENTRY_COSTS values are unchanged.
    tech_cost_percentile: float = 0.5  # Continuous counterpart of
    # tech_cost_path for the PB-1 sampler (§2.1): piecewise-linear
    # interpolation across TECH_COST_MULTIPLIERS' low/mid/high (0.0=low,
    # 0.5=mid, 1.0=high). Neutral 0.5 reproduces tech_cost_path's own
    # selection exactly; percentile only overrides path's choice when moved
    # off 0.5.
    renewable_buildout_pace: str = "mid"  # "slow", "mid", "aggressive"
    storage_deployment: str = "mid"
    retirement_aggressiveness: str = "mid"
    hydro_year: str = "normal"  # "dry" | "normal" | "wet" — forecast wet/dry
    # water-year lever on the conventional-hydro monthly-energy budget. The
    # budget MECHANISM (the dispatch LP picks *when* within a month each hydro
    # plant generates) is itself the forward path; this knob sets only the
    # monthly *level*, scaling the normal-water-year climatology
    # (data.hydro.forecast_monthly_hydro) by constants.HYDRO_YEAR_MULTIPLIER so
    # a forecast can run a dry or wet hydrology scenario. "normal" (default) =
    # 1.0, the unscaled climatology. Backcast runs instead pin the budget to the
    # measured EIA-930 NG:WAT realization (--hydro-eia930-monthly) and ignore
    # this lever. Level input only; see docs G9 / methodology-gaps-2026-06.
    hydro_dispatch_envelope: bool = False  # GATED default off (caiso-72
    # STEP-2). Cap the conventional-hydro fleet's hourly dispatch at the
    # measured per-(month x hour-of-day) percentile
    # (constants.HYDRO_ENVELOPE_PERCENTILE) of the ISO's EIA-930 NG:WAT
    # hourly output — the head/flow/scheduling deliverability ceiling the
    # nameplate pmax bound ignores. Without it the budget LP hoards the
    # monthly hydro energy into the top price hours with perfect foresight
    # (CAISO 2024: model evening p95 exceeds measured p95 by 1-2+ GW in 9 of
    # 12 months), displacing the evening gas/CT reality runs. Same measured
    # capability-envelope class as caiso_corridor_flow_limit — the LP still
    # clears below the ceiling; nothing is pinned. Backcast uses the solve
    # year's own measured envelope; a forecast year falls back to the pooled
    # HYDRO_CLIMATOLOGY_YEARS envelope. See
    # results/calibration/FINDING-caiso72-step0-evening-displacement-2026-07-10.md.
    eac_price_nuclear: float = 0.0  # $/MWh, e.g. NY/IL Zero Emission Credit ~$17
    eac_price_wind: float = 0.0  # $/MWh, onshore wind REC
    eac_price_solar: float = 0.0  # $/MWh
    eac_price_gas_cc_ccs: float = 0.0  # $/MWh, CCS-equipped gas CC only (45Q-linked)
    eac_price_storage: float = 0.0  # $/MWh on discharge
    eac_price_offshore_wind: float = (
        0.0  # $/MWh, offshore-specific EAC (may differ from onshore)
    )
    eac_price_geothermal: float = 0.0  # $/MWh, clean firm generation credit
    rps_enabled: bool = True  # whether to enforce RPS as LP constraint
    electrolyzer_type: str = "pem"  # "pem" or "alkaline" — sets H2 fuel cost
    h2_available_year: int = 2035  # was 2032.
    # Source: engineering judgment. §45V credit terminates for construction
    # after Dec 31, 2027 (OBBBA). Without $3/kg credit, green H2 fuel cost
    # ~2x higher. Deployment delayed to mid-2030s when electrolyzer costs
    # and renewable LCOE decline enough to compensate.
    ccs_available_year: int = 2030  # year CCUS enters the candidate pool
    egs_available_year: int = 2030  # year EGS enters the candidate pool
    offshore_wind_available_year: int = 2030
    offshore_wind_eligible_isos: list[str] = field(default_factory=lambda: ["CAISO"])

    # Tier 2 (expert/sensitivity)
    gas_seasonality: bool = True  # Apply monthly Henry Hub seasonality shape
    storage_rte_4hr: float = 0.85
    storage_rte_8hr: float = 0.80
    # Storage new-entry value stack. ``storage_capacity_value`` globally gates
    # the resource-adequacy revenue stream; it is only paid where the ISO's
    # MARKET_DESIGN has a capacity market (e.g. PJM/NYISO/ISO-NE/CAISO), so on
    # energy-only ERCOT it has no effect. Set False to screen on arbitrage
    # alone. ``storage_degradation`` charges a per-MWh cycling-degradation cost
    # against arbitrage margin (penalizes high-cycling short-duration storage).
    storage_capacity_value: bool = True
    storage_degradation: bool = True
    storage_daily_cycling: bool = False  # When True, each storage unit's SOC
    # must return to its start-of-day level every 24h, so it cannot bank cheap
    # energy across days. Bounds the single-LP perfect-foresight advantage to
    # within-day arbitrage (the realistic limit for short-duration storage; a
    # day-ahead operator cannot shift across days either). Off = today's
    # annual-cyclic behaviour. See model-methodology-spec.md (storage).
    nominal_discount_rate: float = 0.08  # Nominal WACC, $/MWh LCOE basis
    retirement_consecutive_years: int = 2  # fallback if no per-fuel override
    forecast_fossil_retirement_economic: bool = True  # In a forecast, fossil
    # (coal/gas/oil) units are NOT retired on their announced EIA-860 planned-
    # retirement date — their phaseout is governed entirely by the economic-
    # retirement screen (capacity.apply_economic_retirements), so the forecast
    # responds to conditions (a fossil unit may close early on losses or run past
    # its announced date if it stays in-merit) rather than to a hardcoded
    # announcement. Non-fossil units (nuclear/hydro/wind/solar/storage) still
    # retire on their announced EIA-860 date (policy/contract/end-of-life exits
    # with no economic-screen analogue). Set False for the legacy behaviour
    # (every scheduled retirement honored regardless of fuel).
    confirmed_exits_enabled: bool = True  # GATED, default-ON (flipped 2026-07-05,
    # owner sign-off — docs/handoffs/confirmed-retirement-plan-2026-07.md §7). When
    # True and mode == "forecast", the confirmed-retirement channel force-retires (or
    # derates, for plant-binned fleets) each unit bound by an enforceable public
    # instrument in the confirmed-retirements registry
    # (data/raw/confirmed-retirements, read via
    # data.confirmed_retirements.load_confirmed_exits) at its instrument date —
    # step 0 of capacity.evolve_fleet and the first-year build_base_fleet, before
    # the announced-date step and the economic screen. Only binding CONFIRMED
    # exits force out; ANNOUNCED-only retirements stay with the economic screen
    # (mirrors load_planned_additions' construction-committed philosophy). The
    # registry is data, not tuning (rule 24): this flag and the clean path are
    # the whole surface. The default was gated off until the registry covered all
    # six ISOs (landed) and its two open primary-document caveats (Rockport 1's
    # civil action number, Diablo Canyon's CPUC decision number) were resolved
    # (both confirmed 2026-07-05 — see data/raw/confirmed-retirements/pjm.csv,
    # caiso.csv). Also activates the non-fossil announced-horizon gate (see
    # forecast_fossil_retirement_economic-adjacent apply_announced_retirements
    # horizon_years wiring in capacity.evolve_fleet). False reproduces the
    # pre-flip, injector-absent behavior exactly (backcast mode is unaffected
    # either way — the channel is forecast-mode only).
    retirement_years_coal: int = 1  # coal retires after 1 unprofitable year
    retirement_years_gas_ct: int = 2  # CTs get 2 years
    retirement_years_gas_cc: int = 3  # modern CCs get 3 years (most flexible/valuable)
    retirement_years_gas_st: int = 2  # legacy gas steam — same grace as a CT
    retirement_years_oil: int = 2  # oil/distillate peakers/steam
    retirement_years_gas_cc_ccs: int = 3  # CCS-equipped CC, like a modern CC
    retirement_years_nuclear: int = 3  # nuclear — long grace (irreversible exit)
    retirement_fom_multiplier_coal: float = 1.3  # coal faces higher effective FOM
    # (regulatory risk, carbon liability, rising insurance). Source: Lazard LCOE 2024.
    retirement_fom_multiplier_gas_ct: float = 1.0
    retirement_fom_multiplier_gas_cc: float = 1.0
    retirement_fom_multiplier_gas_st: float = 1.0
    retirement_fom_multiplier_oil: float = 1.0
    retirement_fom_multiplier_gas_cc_ccs: float = 1.0
    retirement_fom_multiplier_nuclear: float = 1.0
    staged_oversupply_thinning: bool = False  # GATED, default-OFF (G-30
    # first-wave fix). When True, the economic-retirement screen may retire at
    # most ``staged_thinning_max_gw_per_year`` GW **per fuel class per year** —
    # the least-efficient (highest-heat-rate) eligible units go first, the rest
    # carry their loss counter forward and are re-screened next year. This is a
    # RATE cap on exits, not a price floor/adder: it does not change any unit's
    # margin or the retire/keep decision, only how many exits of one fuel class
    # a single simulation year may realize. Structural driver: a fleet does not
    # deactivate 14 GW of one fuel in one calendar year — RTO deactivation-notice
    # periods (ERCOT §3.14 / PJM ~90-day + RMR study), decommissioning lead time,
    # and coal rail/take-or-pay wind-down stage large exits over multiple years.
    # Forward analogue (rule 13): any forecast year's economic exits are throttled
    # by the same physical lead time, and a genuinely over-supplied fleet still
    # exits fully — just spread across years. The point (G-30 first-wave problem):
    # spreading the exits gives a year whose fleet has thinned enough for the LP
    # regime (the in-year ORDC overlay / lookahead pro-forma) to price scarcity
    # and RETAIN the marginal survivor — the retention decision stays the LP's,
    # never this cap's. Mirrors ccs_retrofit_max_gw_per_year's throughput logic.
    staged_thinning_max_gw_per_year: float = 3.0  # GW/yr/fuel-class exit budget
    # when staged_oversupply_thinning is on. 3.0 GW ≈ the largest single-year
    # ERCOT coal-deactivation wave observed historically (two ~1.5 GW plants);
    # it is a lead-time ceiling, never fitted to a retirement residual. Ignored
    # when staged_oversupply_thinning is off (default).
    limited_foresight_dispatch: bool = False  # GATED, default-OFF (G-30 in-year
    # scarcity fix). When True, the in-year dispatch LP is denied perfect annual
    # foresight for flexible resources: storage/hydro cannot bank energy across
    # days to shave the annual net-load peak (bounds storage SOC to a within-day
    # cycle, same machinery as storage_daily_cycling). A real day-ahead/real-time
    # operator has no annual lookahead either, so the perfect-foresight single-LP
    # flattens the net-load duration curve more than the actual market can — which
    # is exactly why the over-supplied-fleet ORDC overlay stays inert (reserves
    # never tighten). With foresight bounded, the peak/net-load-ramp hours the
    # storage fleet can no longer pre-empt let the in-year ORDC overlay price
    # scarcity from the LP regime once the fleet has thinned (pairs with
    # staged_oversupply_thinning). Dispatch-side structural change, zero fitted
    # parameters; volumes still solve on the LP, the overlay reads its duals.
    # (retirement_reserve_margin was DELETED, not zeroed — rule 26. The
    # retirement reliability floor now shares the adequacy backstop's margin:
    # constants.PLANNING_RESERVE_MARGIN_BY_ISO, overridable only through
    # planning_reserve_margin_override below. One requirement, two verbs —
    # capacity-economics plan 2026-07 §3.2.)
    fixed_om_gas_cc: float = 30.0  # $/kW-yr. NREL ATB 2024 Gas-CC FOM.
    fixed_om_gas_ct: float = 21.0  # NREL ATB 2024 Gas-CT (F-frame) FOM.
    # (Flipped from the legacy 12/8 estimates to the externally-identified
    # NREL-ATB-2024 targets — G-32, docs/handoffs/fom-scarcity-defaults-flip-
    # 2026-07-07.md. Rule 11: prefer the accurate measured FOM class over a
    # hand estimate. The flip is inert on the realized ERCOT fleet — the
    # accredited reliability floor / adequacy backstop mask the going-forward
    # bar in the economic-retirement screen (fom-scarcity Stage 2 §2, Stage 5;
    # foresight A/B re-run confirms retirement/entry byte-identical to the
    # legacy-FOM run) — so it is NOT credited with any retirement or emissions
    # effect; it is adopted for input fidelity only.)
    fixed_om_gas_st: float = 35.0  # legacy gas steam (boiler/ST) going-forward fixed
    # cost: high relative to a CC because old steam units are staffing- and
    # maintenance-intensive. Until this field existed, gas_st was absent from the
    # economic-retirement screen entirely (it is not gas_cc/gas_ct/coal), so old
    # steam gas could never retire on economics regardless of revenue. Source:
    # Lazard LCOE / NREL ATB legacy-steam FOM class ($30-40/kW-yr).
    fixed_om_coal: float = 45.0  # NREL ATB 2024 / EIA-S&L existing-coal FOM
    # (flipped from the legacy 40.0 estimate — G-32; see the fixed_om_gas_ct
    # note above for the flip rationale and its inert-on-realized-fleet caveat).
    fixed_om_oil: float = 25.0  # legacy oil/distillate steam & CT — high O&M,
    # rarely run. Source: Lazard LCOE / EIA O&M.
    fixed_om_gas_cc_ccs: float = 25.0  # CC + capture island going-forward fixed
    # cost (host CC O&M + capture O&M). Source: NETL Rev 4 / NREL ATB CCS.
    fixed_om_nuclear: float = 130.0  # existing nuclear avoidable fixed O&M
    # (staffing, security, NRC fees) — large, but high net revenue keeps most
    # reactors solvent; the screen lets a genuinely uneconomic one exit.
    # Source: NEI / EIA nuclear operating-cost surveys, NREL ATB.
    ira_ptc_wind: float = 26.0  # $/MWh
    ira_itc_solar: float = 0.30  # 30%
    ira_itc_storage: float = 0.30
    # IRA credit schedule per OBBBA (One Big Beautiful Bill Act),
    # enacted July 4, 2025.
    # Wind/solar: §45Y/§48E BOC before July 4, 2026 + in-service by Dec 31,
    # 2027. For an annual model, treat 2027 as the last year wind/solar
    # credits are available.
    ira_wind_solar_last_year: int = 2027
    # Other clean (storage, nuclear, geothermal, hydro): §48E graduated
    # phaseout 2029-2033. 100% through 2028, 80% in 2029, 60% in 2030,
    # 40% in 2031, 20% in 2032, 0% after.
    ira_other_clean_last_full_year: int = 2028
    ira_other_clean_phaseout_end: int = 2033
    # §45V hydrogen production credit: construction start by Dec 31, 2027.
    ira_h2_45v_last_year: int = 2027
    # §45Q CCUS credit: extended but phasing out post-2032.
    ira_ccus_45q_last_year: int = 2032
    electrolyzer_efficiency_override: float | None = None  # overrides lookup
    ccs_capture_rate: float = 0.90  # fraction of CO2 captured by CCUS
    co2_transport_storage_cost: float = 15.0  # $/tCO2 for captured CO2
    egs_pmin_fraction: float = 0.20  # EGS turn-down floor (fraction of rated)
    offshore_wind_cf_override: float | None = None  # overrides OFFSHORE_WIND_PARAMS

    # Tier 2 (expert/sensitivity) — CCS retrofit parameters
    ccs_retrofit_hr_penalty: float = (
        0.12  # Fractional heat rate increase from capture parasitic load.
    )
    # Applied as: retrofit_hr = base_hr × (1 + penalty).
    # 0.12 = 12% penalty. Source: NETL Cost & Performance
    # Baseline Rev 4, 2021. Range in literature: 0.10–0.18.
    ccs_retrofit_capex_kw: float = 900.0  # $/kW for post-combustion capture retrofit.
    # Source: NETL 2021, Sargent & Lundy 2022.
    # Lower than greenfield (~$1400/kW) because host plant exists.
    ccs_retrofit_vom_adder: float = (
        8.0  # $/MWh additional VOM for capture O&M, solvent, compression.
    )
    # Source: NETL Cost & Performance Baseline Rev 4.
    ccs_retrofit_capture_rate: float = 0.90  # Fraction of CO2 captured. 0.90 = 90%.
    # Source: NETL design basis for amine scrubbing.
    ccs_retrofit_available_year: int = 2028  # Earliest year retrofits can occur.
    ccs_retrofit_max_gw_per_year: float = 3.0  # GW/yr retrofit throughput cap per ISO.
    # Source: engineering judgment — EPC capacity constraint.
    ccs_retrofit_min_remaining_life: int = (
        15  # Only retrofit units with ≥ N years remaining useful life.
    )
    # Avoids retrofitting units near retirement.

    # Tier 2 (expert/sensitivity) — Fleet aggregation control
    heat_rate_bin_count: int | None = None  # Override default bin count per fuel type.
    # None = use HEAT_RATE_BINS defaults (3 bins).
    # Set to 5, 10, etc. for finer granularity.
    # More bins = more LP variables = slower solve.
    # Recommended: 3 (default) for production runs,
    # 5-10 for CCS/carbon sensitivity analysis.

    # Tier 2 (expert/sensitivity) — CAMPD operational binning
    # When True the thermal fleet is built from the CAMPD-derived bin
    # assignments (one row per plant, aggregated to ~120 operational bins
    # with a 4-tranche Must-Run / Committed / Economic / Peaking capacity
    # structure). When False the legacy equal-width heat-rate binning of
    # aggregate_fleet() is used. See docs/binning-methodology.md.
    use_campd_bins: bool = True
    campd_bins_path: str = str(CAMPD_BINS_CSV)
    plant_registry_path: str = str(PLANT_REGISTRY_CSV)
    # Commercial-operation-date (COD) vintage ramp (market_sim.data.cod_ramp).
    # The backcast fleet snapshot is a recent vintage that includes units built
    # AFTER the solved year; with this on (the default), every generator —
    # thermal, nuclear, oil, and the ERCOT CAMPD bins — is masked month-by-month
    # by its commercial-operation (and retirement) date, so a backcast dispatches
    # only what was actually online: a unit that came online or retired part-way
    # through the year is available only in the months it operated, applied as a
    # single monthly mask inside generators_to_fleet_arrays. The month-precise
    # COD comes from the EIA-860 plant-code map (cod_ramp.load_cod_map); this is
    # the thermal analogue of vintage_capacity_ramp/storage_vintage_ramp. Pure
    # capacity accounting (no fitting), so it is forecast-applicable as well as
    # backcast-correct. Engages in backcast mode (forecast runs pass an explicit
    # calendar year); set False to keep the full present-day snapshot (e.g. to
    # reproduce a pre-COD-ramp run).
    cod_ramp_enabled: bool = True
    eia860_vintage_year: int | None = None  # Year-matched EIA-860 vintage for a
    # backcast. None (default) uses the canonical 2025-Early-Release snapshot in
    # data/raw/eia-860/ filtered to the solved year by the COD ramp. Set
    # to a year with a committed data/raw/eia-860/vintage_<year>/ (2023,
    # 2024) to read the native annual release instead — removing the COD ramp's
    # capacity-weighted-mean COD smear and the absence of units that retired
    # between the solved year and the 2025 snapshot. Measured effect is small
    # (~0.4% of ERCOT installed capacity vs the COD-ramped 2025ER fleet, ~240 MW
    # of retired-2023->25 units), a correctness/provenance refinement rather than
    # a scarcity driver; gated, recalibrate before a keeper. See
    # docs/cod-vintage-ramp.md. Engaged in backcast mode only.
    # Historic (facility-summed) CAMPD outage overlay: hard-zeros coal/CC
    # tranches when a plant's CEMS facility sum drops out. For ERCOT this is the
    # primary outage layer and the unit-level derate only SUPPLEMENTS it
    # (catching single-unit outages the facility sum hides). For an ISO whose
    # unit-level outage file is derived fresh from ALL CAMPD unit data
    # (e.g. PJM via derive_campd_unit_outages.py), the unit-level layer is the
    # COMPLETE outage source and this facility overlay is redundant — stacking
    # both double-counts and over-derates. The per-ISO registry
    # constants.HISTORIC_OUTAGE_OVERLAY_BY_ISO now sets the effective default;
    # the runner resolves it as ``registry.get(iso, this_flag)``, so this flag
    # is the global default and overrides for ISOs absent from that registry.
    historic_outage_overlay: bool = True
    # Optional per-plant tranche-config override CSV (one row per plant with its
    # five tranche shares of nameplate — must-run / committed / econ-low /
    # econ-high / peaking — and the five per-tranche heat-rate multipliers on
    # the plant's base HR). When set, each listed plant's tranche split and band
    # heat rates come straight from the sheet, bypassing offer_curve_by_group
    # and the per-plant committed/peaking dicts; plants absent from the sheet
    # keep the configured defaults. Produced/round-tripped by
    # scripts/export_tranche_config.py and edited via the desktop launcher.
    plant_tranche_config_path: str | None = None
    unknown_zone_default: str = "South_Central"  # zone for bins tagged "Unknown"
    # When True, generators pinned to a single plant take that plant's
    # CAMPD-measured CO2/NOx/SO2 rates per MWh net (plant_emission_rates_path)
    # in place of the fuel-class defaults, so emission prices bite per plant.
    use_plant_emission_rates: bool = True
    plant_emission_rates_path: str = str(PROCESSED_DIR / "plant_emission_rates.parquet")

    # v2 mode-aware CO2-rate source (docs/handoffs/emissions-co2-rate-plan-2026-07.md):
    # when True, CO2 rates come from the per-(iso, plant, unit, year) v2 artifact
    # via the composition mask — a backcast year books its own measured rate, a
    # forecast year the gen-weighted trailing-average estimator base. The 7-year
    # history landed 2026-07-05 (plan §9.5: conditioning gate stays CLOSED,
    # trailing window set to 2 years); default ON as of 2026-07-06 (owner decision
    # G-39 — re-gate incrementally per ISO as each comes up for its next keeper).
    use_plant_emission_rates_v2: bool = True
    plant_emission_rates_v2_path: str = str(
        PROCESSED_DIR / "plant_emission_rates_v2.parquet"
    )

    # Forward emission-control retrofit channel (Tier 2; default OFF).
    # docs/handoffs/emission-control-retrofit-forward-channel-2026-07.md
    # When True AND in forecast mode, an ANNOUNCED EIA-860 environmental-control
    # install (SCR / SNCR / FGD scrubber / DSI) steps the covered unit's forward
    # emission rate down at its committed Inservice Year — the forward step the
    # trailing-window estimator cannot supply ahead of realized history. The
    # install date is a forward driver, not a residual, so the channel is
    # rule-13-admissible (see the handoff). OFF is byte-identical to the base
    # estimator. Backcast years never consult it (measured rates already carry
    # any operating control). Carbon-capture/CO2 is intentionally excluded here —
    # it is owned by the CCS retrofit screen (rule 15).
    control_retrofit_forward: bool = False
    control_retrofit_path: str = str(
        EIA_860_DIR / "eia860_enviro_assoc_emissions_control_equipment.parquet"
    )

    # Tier 3 (calibration) — CAMPD peaking-tranche heat-rate penalties.
    # The top (Peaking) slice of a bin is a separate LP generator whose
    # heat rate is the bin HR scaled by these duct-firing / peaking-increment
    # multipliers, so scarcity output bids above the economic tranche.
    cc_peak_hr_penalty: float = 1.15  # CC duct-firing increment
    ct_peak_hr_penalty: float = 1.10  # CT / gas-steam peaking increment
    # (No coal_*_hr_mult / coal_peak_hr_penalty: ERCOT coal's offer is set by the
    # CAMPD-bin CSV HR_Mult_* columns plus the coal supply / take-or-pay /
    # passthrough-sigmoid stack on base HR — never these Tier-3 knobs, which were
    # wired to no solve path. Removed 2026-07-08 (rule 26); the ercot47
    # coalpeak-dam probe confirmed the CSV coal peaking multiplier is inert.)

    # Tier 3 (calibration) — Two-tranche HR multipliers for the committed
    # vs economic dispatch range. Real units have convex input-output
    # curves: less efficient at part load (the committed tranche) and
    # more efficient in the upper load range (the economic tranche).
    # Each bin's base capacity therefore splits into a Committed tranche
    # (part-load range): HR × multiplier > 1.0, and an Economic tranche
    # (upper load range): HR × multiplier < 1.0. Neither tranche carries
    # a Pmin floor. Source: GE/Siemens OEM IO curves; CEMS input-output
    # curve analysis.
    cc_committed_hr_mult: float = 1.23  # CC part-load penalty ~23%
    cc_econ_hr_mult: float = 0.96  # CC incremental HR ~4% below avg
    ct_committed_hr_mult: float = 1.28  # CT part-load penalty ~28%
    ct_econ_hr_mult: float = 0.97  # CT incremental HR ~3% below avg
    gas_st_committed_hr_mult: float = 1.32  # Gas steam part-load penalty ~32%
    gas_st_econ_hr_mult: float = 0.97  # Gas steam incremental HR
    must_run_cf: float = 0.85  # assumed CF for CHP must-run emissions post-processing
    # EM-5 / plan §5 R6: when True, the calibration bundle adds a reporting-only
    # startup-CO2 column (model_starts x measured campd startup_co2_kg). Measured
    # bound is 0.015-0.018% of annual CO2, <0.2% even at 10x cycling error
    # (docs/handoffs/emissions-co2-rate-plan-2026-07.md §3), so it is never in the
    # dispatch LP and defaults OFF (no dispatch/level change).
    startup_co2_reporting: bool = False

    # Tier 2 (expert/sensitivity) — Unit commitment heuristic (2-pass)
    commitment_enabled: bool = False  # Legacy feature — default off, opt-in
    # for calibration. When True, a price-based commitment filter runs
    # between two LP solves to approximate integer unit commitment. Prefer
    # energy_reserve_coopt for unit commitment pricing going forward; this
    # path stays for backcast/calibration use, not the primary path.
    commitment_irr_hurdle: float = 0.07  # 7% return required on startup cost.
    # A run must generate margin >= startup_per_mw × (1 + irr) to justify
    # the wear and capital risk of a start. Source: operator interviews,
    # 7-10% typical for merchant thermal assets.
    commitment_storage_weight: float = 1.0  # 0 disables. The P2 commitment
    # screen discounts a run's startup-hurdle margin in hours when storage is
    # net-charging, so a cycling unit is not committed purely to serve
    # speculative battery-charging load. Storage net-discharge hours keep
    # full weight — storage and thermal are complements at the peak.
    commitment_storage_in_merit_floor: float = 0.0  # 0 disables. When > 0,
    # an hour whose storage-charge weight falls below this floor is dropped
    # from the in-merit runs the commitment screen detects: a deep
    # battery-charging trough breaks a cycling unit's run, so the shorter
    # pieces face the min-run filter on their own. Stronger than the
    # hurdle-only discount above, which never changes which hours run.
    # 1.0 drops every net-charging hour; 0.85 drops only deep troughs.
    commitment_screen_coal: bool = True  # When False, CAMPD coal is not
    # commitment-screened in P2; instead it is pinned to its P1 dispatch, so
    # coal gains no new generation in P2 (P1 locks it) and the gas
    # re-dispatch happens around fixed coal. Lets a calibration isolate the
    # gas-internal commitment effect without coal absorbing decommitted gas.

    # Tier 1/2 — ORDC scarcity-pricing overlay (post-solve; never an LP
    # input). Replicates ERCOT's published real-time on-line reserve price
    # adder (RTORPA): adder = weighted LOLP x (VOLL - system lambda), LOLP
    # from a normal CDF over reserves minus the minimum contingency level.
    # The overlay owns the price tail and scarcity revenue only — dispatch,
    # volumes and emissions are untouched (the LP stays the emissions
    # engine). See docs/ordc-overlay.md for formula provenance. Generalized
    # to any ISO via scarcity_price_overlay below: capacity-market ISOs
    # default it off because they recover fixed cost through capacity
    # revenue (capacity_revenue_per_mw_yr), not scarcity adders.
    scarcity_pricing_enabled: bool = False  # Master flag. Backcast: emits the
    # lmp + adder series next to the energy-only LMP (which the volume
    # calibration gates stay on). Forecast: retirement / new-entry / CCS
    # screens see prices + adder, so peaker and storage economics include
    # scarcity revenue instead of bare LP duals (which over-retire).
    scarcity_price_overlay: bool = False  # ISO eligibility gate for the
    # post-solve ORDC overlay (replaces the old `iso == "ERCOT"` hard-code).
    # Default off; ERCOT's ISOConfig.default_scenario_overrides sets this
    # True so ERCOT's behavior is unchanged. Other ISOs may opt in once
    # their own ORDC/LOLP parameters (ordc_voll, ordc_mcl_mw, ordc_lolp_*)
    # are calibrated. Still gated by scarcity_pricing_enabled (the master
    # on/off switch) and skipped when energy_reserve_coopt prices scarcity
    # in the LP directly.
    ordc_voll: float = 5000.0  # $/MWh. ORDC VOLL = system-wide offer cap
    # (HCAP), $5,000 since 2022-01-01 (16 TAC 25.509, PUCT Project 52631;
    # was $9,000 pre-Uri — runnable as a scenario).
    ordc_mcl_mw: float = 3000.0  # Minimum contingency level X, MW. LOLP is
    # administratively 1.0 at reserves <= X (adder pins to VOLL - lambda).
    # 3,000 MW since 2022-01-01 (OBDRR038, PUCT Project 52373 blueprint
    # order); 2,000 MW pre-Uri.
    ordc_lolp_sigma_mw: float = 1400.0  # Std dev of the hourly reserve
    # error (MW) in the LOLP normal CDF. ERCOT publishes seasonal /
    # time-of-day-block values (NP6-576-ER); this flat fallback is bounded
    # from the OBDRR048 floor breakpoints (see docs/ordc-overlay.md
    # "Parameter provenance") and is NOT fitted to price residuals. Use
    # ordc_lolp_params_path to supply the published table when available.
    ordc_lolp_mu_mw: float = 0.0  # Mean of the hourly reserve error (MW)
    # before the PUCT-ordered curve shift below. NP6-576-ER publishes the
    # seasonal values; 0 is the neutral fallback.
    ordc_lolp_shift_sigma: float = 0.5  # Rightward LOLP-curve shift in
    # units of sigma — LOLP is evaluated with effective mean mu + shift x
    # sigma. Two 0.25-sigma steps ordered by PUCT Project 48551 (Mar 2019,
    # Mar 2020). 0.0 reproduces the pre-2019 curve.
    ordc_multistep_floor: bool = True  # OBDRR048 multi-step RTORPA floor,
    # effective 2023-11-01: adder >= $20/MWh when reserves <= 6,500 MW,
    # >= $10/MWh when 6,500 < reserves <= 7,000 MW. Date-gated in backcast
    # years; applied unconditionally in forecast years when True.
    ordc_as_plan_mw: float = 0.0  # Ancillary-service plan netting, MW.
    # 0 (default) treats the model's full dispatchable headroom as ORDC
    # reserves, matching ERCOT's published reserve definition: RTOLCAP /
    # RTOFFCAP count AS-held capacity (RRS/ECRS/Non-Spin headroom) as
    # reserves, so netting the AS plan out double-counts scarcity —
    # validated on run92_kiamichi, where netting the published 8,100 MW
    # (2023 average total AS, IMM 2023 State of the Market Report)
    # produces ~10x the actual count of cap-pinned hours. Set to the
    # published AS plan to model reserves as energy-market-available
    # headroom only (rejected; see docs/ordc-overlay.md). Full AS
    # co-optimization is out of scope.
    ordc_lolp_params_path: str | None = None  # Optional CSV of seasonal /
    # TOD-block LOLP parameters (columns: season, tod_block, mu_mw,
    # sigma_mw — ERCOT NP6-576-ER layout). When set, overrides the flat
    # ordc_lolp_mu_mw / ordc_lolp_sigma_mw fallbacks per hour.
    # NOTE — ordc_reliability_deployment_mw was DELETED 2026-07-04 (CLAUDE.md
    # rule 26: deleted means deleted; audit L10). It was the fitted RTORDPA
    # analogue — a flat, NON-physical reserve offset calibrated to the 2023
    # stress year's LMP residual (~2,500 MW), superseded by the formulaic
    # reserve accounting in results.scarcity (online/offline reserve split +
    # measured AS-plan netting). It had been deprecated-at-0 and was re-swept
    # AFTER deprecation (calibration-log:185) — a zeroed knob that still
    # parses is a re-armable answer key, so the field is gone: setting it now
    # raises. The forward RTC+B scenario knob rtcb_reliability_deployment_mw
    # (below) is unrelated and remains.
    as_revenue_enabled: bool = False  # Credit ERCOT ancillary-service market
    # revenue (Reg/RRS/ECRS/Non-Spin) in the capacity economics — the
    # retirement, new-entry and storage-entry screens. Default off (energy +
    # scarcity only, byte-identical baseline); recommended on for ERCOT
    # forecasts. ERCOT-only: capacity-market ISOs already recover fixed cost
    # through capacity_revenue_per_mw_yr. Without it, storage is undervalued
    # ~6x (AS was ~85% of 2023 ERCOT battery revenue) and tail thermal under-
    # earns. The per-tech rates and saturation live in constants.ERCOT_AS_*;
    # the revenue saturates steeply as the AS-eligible (mostly storage) fleet
    # grows (Modo: battery AS revenue fell ~90% 2023->2025). See
    # docs/ordc-overlay.md (AS revenue).
    as_revenue_multiplier: float = 1.0  # Scenario scale on the calibrated AS
    # revenue rates (forward AS-price view: tighter/looser AS markets).

    # --- W2-P3 Stage 2 — capacity-screen reserve (scarcity/AS) valuation -----
    # Revenue-side fix (capacity-economics plan 2026-07 §5 step 2): the
    # retirement and thermal new-entry screens value each reserve-eligible
    # unit's hour-by-hour BEST use — energy margin (price − mc) or the
    # reserve price, never both on the same MW (the co-optimization arbitrage
    # condition) — against the reserve-price signal the model already
    # produces: the reserve co-opt's own duals under
    # ercot_thermal_as_endogenous (superseding that flag's annual per-fuel
    # rate), else the post-solve ORDC scarcity adder. Market-design grounding
    # for the ORDC leg: ERCOT pays real-time on-line/off-line reserves the
    # same ORDC price the energy adder carries (RTORPA / RTOFFPA, Nodal
    # Protocols §6.5.7.5), so available headroom in a scarcity-priced hour is
    # income the screens were structurally blind to. Zero fitted parameters —
    # the signal is the published-ORDC/co-opt price the model already
    # computes; the Potomac SOM CT/CC net-revenue tables are the external
    # validity check, never a target (rule 1). Off = ablation: screens fall
    # back to the legacy annual AS credits (endogenous per-fuel rate or the
    # calibrated exogenous flat rate). Forecast-only surface — capacity
    # evolution never runs in backcast, so keepers are byte-identical.
    screen_reserve_value_enabled: bool = True

    ercot_market_design: str = "auto"  # ERCOT scarcity-pricing regime:
    # "ordc"  — the 2014-Dec2025 ORDC + RTORDPA reliability-deployment design
    #           (RTORPA from the ORDC curve PLUS the discretionary ECRS/RUC
    #           reserve withholding the reliability-deployment offset stands in
    #           for — the design that produced the 2023 prices).
    # "rtcb"  — the RTC+B design (live 2025-12-05): AS demand curves co-optimized
    #           in SCED. Still ORDC-shaped/VOLL-anchored, so the overlay is the
    #           right first-order representation, but the 2023 reserve-withholding
    #           conservatism was reformed, so the reliability-deployment offset
    #           does NOT carry forward unless rtcb_reliability_deployment_mw is set.
    # "auto"  — year-gated: ORDC for years <= 2025, RTC+B for >= 2026.
    # This is what separates the (erroneous) 2023 backcast design from the
    # forward design: the ORDC regime carries no reliability-deployment offset
    # (the fitted ordc_reliability_deployment_mw knob was deleted 2026-07-04);
    # the RTC+B regime uses rtcb_reliability_deployment_mw (default 0).
    rtcb_reliability_deployment_mw: float = 0.0  # Reliability-deployment offset
    # under the RTC+B regime (forecast). Default 0 — RTC+B reformed the ECRS
    # conservatism, so forward scarcity prices to fundamentals. Set > 0 to model
    # a scenario where 2023-style reserve conservatism recurs under RTC+B.

    # Tier 1/2 — NYISO RCPF (Reserve Constraint Penalty Factor) scarcity
    # overlay (post-solve; never an LP input). NYISO's analogue of the ERCOT
    # ORDC adder: a stepped reserve demand curve whose shadow price flows
    # into the LBMP via energy/reserve co-optimization. The nested products
    # (10-min spin ⊂ 10-min total ⊂ 30-min total) stack in a deepening
    # shortage, reaching the high-hundreds/low-thousands tail the energy-only
    # LP cannot produce. Owns the price tail only — zero whenever reserves
    # clear the requirement (the vast majority of hours), so the body of the
    # distribution is untouched. NYISO-only: other capacity-market ISOs
    # recover fixed cost through capacity revenue. See
    # results.rcpf / docs/nyiso-rcpf-overlay.md.
    nyiso_rcpf_enabled: bool = False  # Master flag for the NYISO RCPF overlay.
    nyiso_rcpf_products: tuple | None = None  # Optional override of the
    # reserve demand-curve table (constants.NYISO_RCPF_PRODUCTS): a tuple of
    # (name, requirement_mw, critical_mw, max_penalty_$/MWh) products. None
    # uses the published NYISO defaults. A scenario can widen/tighten the
    # curves (e.g. a future capacity-shortage view) without a code edit.
    nyiso_rcpf_locational: dict | None = None  # Optional override of the
    # locational reserve regions (constants.NYISO_RCPF_LOCATIONAL): a dict of
    # region -> {"zones": (model-zone names), "products": ((name, req_mw,
    # crit_mw, max_$/MWh), ...)}. None uses the published NYISO defaults
    # (East / SENY / NYC). The overlay stacks each region's demand-curve price
    # onto every model zone the region contains, on top of the system-wide
    # NYCA tier (nyiso_rcpf_products); see results.rcpf.locational_zone_adders.
    nyiso_dynamic_reserve_requirements: bool = False  # GATED, default-OFF
    # condition-varying NYISO reserve requirements (issue #1344). When on (NYISO
    # + energy_reserve_coopt), each in-LP reserve family's static published
    # requirement (reserve_config.NYISO_RCPF_PRODUCTS / NYISO_RCPF_LOCATIONAL)
    # is replaced by the MEASURED as-enforced hourly locational requirement
    # series for that (region, product) — the requirement NYISO actually
    # scheduled into RTD/RTC, which RISES with conditions (thunderstorm alerts,
    # gas contingencies, largest-source changes). The empirical basis: with the
    # static requirements the downstate families never bind (NYC holds 2-3x the
    # published MW in the exact hours reality prices >$300), and both the
    # online-proxy and commitment-gated formulations were refuted AT the static
    # requirement (docs/handoffs/nyiso-downstate-reserve-incidence-2026-06.md
    # paths A/B). A measured requirement is a market-design INPUT (rule #13
    # admissible: regenerates forward as published-static-base + condition
    # rules applied to forward weather/contingency states, responds to changed
    # conditions); the measured reserve PRICES stay validation-only and are
    # never read. Data seam: data/raw/NYISO-AS/requirements/ (the Ask-B intake,
    # docs/handoffs/nyiso-data-asks-2026-07.md) via
    # data.nyiso_reserve_requirements.load_nyiso_reserve_requirements — the
    # flag HARD-ERRORS when the series is absent (no silent static fallback, so
    # a run_config claiming dynamic requirements cannot quietly solve without
    # them). Families without a measured series (e.g. the synchronised-reserve
    # scaffold families) keep their static values. ORDC shortfall steps stay
    # anchored to the published static (req, crit, penalty) shape and TRANSLATE
    # with the hourly requirement (documented approximation — the published
    # RCPF is itself a stepped curve). Promotion gate: leave-one-year-out
    # scoring within 2023-2025 (CLAUDE.md rule 22). Default off
    # (byte-identical); NYISO-only. Mutually exclusive with nyiso_rcpf_enabled
    # under energy_reserve_coopt (rule 19 — see reserve_config._nyiso_design).

    # NEISO (ISO-NE) RCPF scarcity overlay — the ISO-NE analogue of the NYISO
    # lever above (post-solve; never an LP input). ISO-NE prices real-time
    # scarcity through Reserve Constraint Penalty Factors on its nested
    # operating-reserve products (TMSR ⊂ total 10-min ⊂ total 30-min); the
    # penalties stack into the LMP in a deepening shortage. ISO-NE recovers
    # fixed cost through the Forward Capacity Market, so the overlay owns the
    # price tail only and is $0 in calm hours — a forward/scarcity lever, not a
    # backcast adjustment. See constants.NEISO_RCPF_PRODUCTS / results.rcpf.
    neiso_rcpf_enabled: bool = False  # Master flag for the NEISO RCPF overlay.
    neiso_rcpf_products: tuple | None = None  # Optional override of the ISO-NE
    # reserve demand-curve table (constants.NEISO_RCPF_PRODUCTS): a tuple of
    # (name, requirement_mw, critical_mw, max_penalty_$/MWh) products. None uses
    # the sourced ISO-NE defaults. A forward scenario can widen/tighten the
    # curves (e.g. a tighter reserve margin) without a code edit.
    neiso_dynamic_reserve_requirements: bool = False  # GATED, default-OFF
    # condition-varying ISO-NE reserve requirements — the exact NEISO analogue
    # of nyiso_dynamic_reserve_requirements above (issue #1344; NEISO winter
    # scarcity charter Limb A). When on (NEISO + energy_reserve_coopt), each
    # in-LP reserve family's static published requirement
    # (reserve_config.NEISO_RCPF_PRODUCTS: 1,800/1,200/600 MW) is replaced by
    # the MEASURED as-enforced hourly requirement series for that (location,
    # product) — ISO Express "Hourly Reserve Requirements" (ancillary-hourly-
    # rr), the requirement ISO-NE actually enforced in real time, which RISES
    # with conditions (largest first/second contingency, cold-weather and
    # gas-contingency events). The empirical basis: at the static requirements
    # the co-opt is provably DORMANT on 2023-2025 (reserve dual $0.00 in all
    # 26,280 hours — the neiso-56 keeper) while the measured system 30-min
    # requirement EXCEEDS the static 1,800 MW in every one of those hours
    # (mean ~2,300 MW, peaking 3,167 MW in the Jan-2025 cold snap that carries
    # the C3c >$300 DA tail). A measured requirement is a market-design INPUT
    # (rule #13 admissible: regenerates forward as published-static-base +
    # condition rules applied to forward weather/contingency states, responds
    # to changed conditions); the measured reserve PRICES stay validation-only
    # and are never read. Data seam: data/raw/NEISO-AS/requirements/ ->
    # data/clean/reserve-requirements/NEISO/<year> via
    # data.neiso_reserve_requirements.load_neiso_reserve_requirements — the
    # flag HARD-ERRORS when the series is absent (no silent static fallback,
    # so a run_config claiming dynamic requirements cannot quietly solve
    # without them). Locations without an in-LP family (the SWCT/CT/NEMABSTN
    # local reserve zones) are not mapped; a family without a measured series
    # keeps its static value. ORDC shortfall steps stay anchored to the
    # published static (req, crit, penalty) shape and TRANSLATE with the
    # hourly requirement (documented approximation — the published RCPF is
    # itself a stepped curve). Promotion gate: leave-one-year-out scoring
    # within 2023-2025 (CLAUDE.md rule 22). Default off (byte-identical);
    # NEISO-only. Mutually exclusive with neiso_rcpf_enabled under
    # energy_reserve_coopt (rule 19 — see reserve_config._neiso_design).

    reserve_margin_build_enabled: bool | None = None  # Adequacy backstop: after
    # the economic new-entry screen, force-build firm (gas_ct) capacity if the
    # system's accredited firm capacity is below peak * (1 + planning reserve
    # margin). This is the ReEDS/NEMS/CDR structural adequacy mechanism — it
    # keeps the lights on when under-priced energy/scarcity revenue would
    # otherwise under-build, independent of getting prices exactly right. The
    # economic screen still decides the profitable build; this only fills the
    # residual adequacy gap. Tests the entering year's known peak (plan §2.3
    # component 1; prior-year peak only when a caller does not supply the known
    # one).
    #   TRI-STATE market-design resolution (G-41, PJM hindcast I7 decision
    # 2026-07-06, owner-approved market-design-dependent variant): None (default)
    # resolves per market design in capacity.resolve_reserve_margin_build_enabled
    # — ON for ISOs whose design procures capacity to an adequacy requirement
    # (MARKET_DESIGN[iso].capacity_market: PJM/MISO/NYISO/NEISO/CAISO — the LP
    # analogue of RPM's absolute-IRM procurement), OFF for energy-only ERCOT
    # (no absolute floor — an under-remunerated unit exits and ORDC prices the
    # scarcity) and ISOs absent from MARKET_DESIGN (conservative). Set True/False
    # explicitly to force it either way (rule 21 — the knob lands in
    # run_config.json). Energy-only ERCOT stays byte-identical (resolves off);
    # a scenario that pins False reproduces the pre-G-41 off behaviour exactly.
    market_design_retirement_floor: bool = False  # GATED, default-OFF
    # market-design fidelity gate on the RETIREMENT reliability floor
    # (fom-scarcity stage 5 / the capacity-economics successor mechanism,
    # docs/handoffs/fom-scarcity-joint-protocol-2026-07-06-stage5-energy-only-floor.md
    # §1). When on, the floor (_apply_reliability_floor — "un-retire eligible
    # units until the PRM requirement clears") applies ONLY in ISOs whose
    # market design actually procures capacity to an adequacy requirement
    # (MARKET_DESIGN[iso].capacity_market: PJM/MISO/NYISO/NEISO/CAISO). An ISO
    # explicitly registered energy-only (ERCOT) skips the floor entirely: the
    # real ERCOT has no reliability floor — an under-remunerated unit exits
    # (~0.5-2 GW/yr observed), reserves tighten, and the ORDC prices the
    # resulting scarcity, which is the revenue that retains the marginal
    # survivor. RMR is transmission-security-scoped and rare (Nodal Protocols
    # §3.14.1), never a system-wide adequacy channel, so zero-cost fleet-wide
    # retention is not a real ERCOT mechanism (rule 1). ISOs absent from
    # MARKET_DESIGN keep the floor (conservative fallback). The default-off
    # reserve_margin_build_enabled backstop is untouched and remains the
    # modeling-safety valve. Default off = byte-identical everywhere;
    # capacity-market ISOs byte-identical even when on.
    capacity_deliverability_limits: bool = False  # GATED, default-OFF locational
    # resource-adequacy mechanism. When on, the model reads each ISO's published
    # capacity-deliverability parameters (PJM CETO/CETL, MISO LRR/CIL, NYISO
    # LCR/TSL, ISO-NE LSR, CAISO LCR/MIC) from the capacity-deliverability clean
    # datatype, crosswalks the areas onto model zones (config.
    # capacity_area_crosswalk), and (a) replaces the system-wide
    # EXTERNAL_SIMULTANEOUS_LIMITS scalar with the per-area seam import_limit
    # where available (CAISO MIC → WECC_import), and (b) gates the capacity-value
    # / economic new-entry / retirement screens by per-zone requirement vs
    # deliverable accredited capacity: the marginal capacity payment collapses in
    # a zone whose deliverable firm capacity already clears its locational
    # requirement (RA saturated), mirroring how a binding LCR prices locational
    # capacity. This is a structural mechanism (repo rule #1), NOT a backcast-fit
    # lever. Part (a) IS enabled in the caiso-51 CAISO keeper backcast
    # (--capacity-deliverability-limits), where the published MIC seam limit
    # supersedes the fitted 7,500 MW WECC cap (audit item C-5;
    # docs/caiso-c5-wecc-cap-closeout-2026-07-03.md); Part (b), the capacity-
    # payment collapse, remains unvalidated in any keeper. Default off
    # (byte-identical); no-ops when the clean partition is absent (ERCOT, or
    # intake not landed).
    ramp_limits: bool = False  # GATED, default-OFF plant-group hourly ramp
    # envelopes in the dispatch LP (model/dispatch._build_ramp_rows). One
    # two-sided row per ramp-constrained plant group per hour transition,
    # bounding the group's hourly dispatch delta by its CAMPD-measured max
    # observed 1-h up/down gross-load move (data.fleet.build_ramp_groups /
    # scripts/derive_campd_ramp_envelopes.py; design
    # docs/ramp-locational-design-2026-07.md §1). A measured physical-
    # capability input with zero fitted degrees of freedom (rule #13): the
    # envelope regenerates from the CAMPD pipeline for any vintage, responds
    # to fleet change, and never reads a residual. Forces the LP to either
    # pre-position slow CC before the evening ramp or clear fast resources
    # (CT/storage/imports) at the ramp margin, so the marginal unit in ramp-
    # bound hours becomes the fast resource and CT clears on merit. Default
    # off (byte-identical); no-op when the ISO has no envelope artifact.
    # A/B result (FINDING-ramp-lcr-caiso-2026-07): structurally sound but
    # near-inert on CAISO evening CT (+2 MW) — kept gated, not in any keeper.
    local_capacity_constraints: bool = False  # GATED, default-OFF local-
    # capacity (LCR-area) minimum-generation rows in the dispatch LP
    # (model/dispatch._build_local_capacity_rows, inputs from
    # data.local_capacity.build_local_capacity_specs). One >= row per covered
    # LCR area per hour: in-area thermal dispatch (+ the in-area share of
    # zone storage) must cover max(0, share*zone_load - import_cap), all
    # parameters from the ISO's published LCR study tables (CAISO LCT report;
    # capacity-deliverability intake) — the exact LP relaxation of a load-
    # pocket zone split, binding only when local load exceeds the study
    # import capability (design docs/ramp-locational-design-2026-07.md §3).
    # The row dual is out-of-market (uplift-like) commitment support and does
    # not enter the zonal energy-balance dual, so hub LMP benchmarks are
    # untouched. Default off (byte-identical); no-op when the ISO has no
    # covered areas / membership crosswalk. A/B result
    # (FINDING-ramp-lcr-caiso-2026-07): +39 MW evening CT with 0.5-1.5%
    # forced share (D-2 PASS) — kept gated pending keeper promotion.
    planning_reserve_margin: float = 0.1375  # Fallback/override planning
    # reserve margin for the adequacy backstop. The per-ISO registry
    # constants.PLANNING_RESERVE_MARGIN_BY_ISO now LEADS: the backstop resolves
    # PLANNING_RESERVE_MARGIN_BY_ISO.get(iso, this scalar), so this value only
    # applies as an explicit override or when an ISO is absent from the
    # registry. 13.75% is ERCOT's economically-optimal reserve margin
    # (Brattle/Astrape 2022 study for the PUCT); a capacity-market ISO uses its
    # own installed-reserve-margin target from the registry.
    planning_reserve_margin_override: float | None = None  # Sensitivity lever:
    # when set, replaces the per-ISO PLANNING_RESERVE_MARGIN_BY_ISO registry
    # value in BOTH consumers of the planning reserve margin — the retirement
    # reliability floor and the reserve-margin build backstop (one requirement,
    # two verbs; capacity-economics plan 2026-07 §3.2). None (default) resolves
    # the ISO's published PRM from constants.py (Brattle/Astrape ERCOT 2022,
    # CPUC RA 15%, PJM IRM, MISO PRMR, NYSRC IRM, ISO-NE ICR-derived — see the
    # registry's per-ISO citations). Registered tornado channel for the
    # reserve-margin band (rule 24); never fitted to a residual.
    entry_price_signal_alpha: float = 1.0  # EWMA blend of the price signal the
    # capacity screens (retirement / new entry / storage entry) consume:
    # signal_Y = alpha x econ_prices_{Y-1} + (1 - alpha) x signal_{Y-1}.
    # 1.0 (default) = byte-identical to raw prior-year prices; < 1.0 smooths
    # single-draw whipsaw (one weather/outage-shaped year triggering a
    # retirement or entry wave the next year reverses). Anti-whipsaw, NOT
    # anti-lag — it looks backward and mildly worsens lag under monotone
    # growth. A/B control arm per capacity-economics plan 2026-07 §2.2/§2.4;
    # probe value 0.6. Screens-only: never touches dispatch, results, or the
    # backcast (backcast mode has no capacity evolution).
    entry_lookahead_reprice: bool = False  # GATED, default-OFF growth-scaled
    # lookahead (plan §2.3.2): re-price the prior year's marginal-cost supply
    # stack against the ENTERING year's known net-load duration
    # (demand_Y - prior-year VRE output), with the same ORDC scarcity curve
    # the runner's capacity-economics overlay uses where the stack exhausts.
    # The pro-forma a real developer runs — projected load against the known
    # fleet — with ZERO fitted parameters (every input is an existing model
    # quantity; rule 13 admissible: regenerates from forward drivers in any
    # year). Feeds ONLY the capacity screens (retirement / new entry /
    # storage), never dispatch, results, or the backcast.
    interchange_shaping: bool = False  # Priced-interchange node: shape the
    # import-tranche availability and export-sink floor by the measured EIA-930
    # month x hour-of-day net-interchange envelope (transmission.
    # inject_interchange_shape), so the node imports overnight and EXPORTS the
    # midday solar glut instead of clearing a flat all-hours import. Default off
    # (byte-identical); only fires when priced_interchange is on and a measured
    # envelope exists. Targets CAISO's over-priced midday floor (the flat node
    # floors price at the cheapest active import tranche all day).
    interchange_shaping_export_only: bool = False  # Like interchange_shaping but
    # skips the import-availability cap, shaping ONLY the export side. The both-
    # sided shape caps gross import availability to the net-import envelope
    # (net << gross), starving baseload imports and substituting gas; export-only
    # keeps just the midday-export cap (surplus beyond the measured export
    # curtails and prices negative) without the import regression. Implies
    # interchange_shaping; default off (byte-identical).
    interchange_shape_import_pct: float = 90.0  # Percentile of the measured
    # EIA-930 (month x hour-of-day) net-interchange distribution
    # (eia_loader.measured_interchange_envelope) that sets the import-tranche
    # availability cap under interchange_shaping. Promoted from what was an
    # os.environ.get("INTERCHANGE_SHAPE_IMPORT_PCT", ...) read in
    # transmission.inject_interchange_shape (an off-registry tuning channel,
    # CLAUDE.md rule 24) so the value is visible in run_config.json instead of
    # a silent shell override. 90.0 reproduces the function's own prior
    # behavior: the env var, when unset (every run to date), fell back to the
    # caller's `percentile` argument, and every call site left that argument
    # at the function signature's default of 90.0 — no run ever exercised a
    # non-default value via the env channel. Under the bidirectional intertie
    # (gross == net), the net-import envelope IS the deliverable import, so
    # the import cap can ride a higher percentile (fatter overnight tail)
    # without re-admitting the midday imports the (near-zero) midday envelope
    # already excludes — see the "bidir sweep" note in
    # inject_interchange_shape's docstring. Only bites when interchange_shaping
    # is on (default off, byte-identical).
    interchange_shape_export_pct: float = 90.0  # Percentile of the measured
    # EIA-930 net-interchange distribution that sets the export-sink floor
    # under interchange_shaping. Same promotion/rationale as
    # interchange_shape_import_pct above (was
    # os.environ.get("INTERCHANGE_SHAPE_EXPORT_PCT", ...)); 90.0 reproduces
    # the prior env-unset default. Only bites when interchange_shaping is on
    # (default off, byte-identical).
    reference_price_interface: bool = False  # Priced-interchange node: serve the
    # seam through the forecast-grade reference-price interface instead of the
    # fitted IMPORT_TRANCHES/EXPORT_TRANCHES. Each neighbor's hourly price is
    # built from forward drivers — (henry_hub + gas_basis) x marginal_heat_rate x
    # neighbor_load_shape — and the seam clears on the spread vs the ISO's own LMP
    # with a small hurdle, bounded by the interface limit (config.constants.
    # INTERFACE_NEIGHBORS; transmission.build_reference_price_node +
    # inject_reference_price_mc). Nothing is tuned to the net-MWh target, so the
    # backcast net export is a genuine validation. Requires priced_interchange;
    # gated to ISOs present in INTERFACE_NEIGHBORS (PJM today), byte-identical
    # otherwise. Default off. See docs/reference-price-interface.md.
    neighbor_hr_forward_skill: str | None = None  # FORWARD-SKILL validation
    # mode for the reference-price interface's neighbor heat rate
    # (data.neighbor_price.neighbor_heat_rate / _FORWARD_SKILL_MODES):
    # "elastic" skips each neighbor's measured per-year hr_by_year anchor and
    # uses the gas-elastic implied HR instead; "flat" also skips the elastic
    # coefficients and uses the flat marginal_heat_rate. Forces a backcast year
    # to price off the SAME forward formula a forecast year would use, so it
    # can be scored against the held-out actuals as a forward-skill check.
    # Threaded through transmission.apply_interchange_injections ->
    # inject_reference_price_mc -> neighbor_price.{interface_reference_prices,
    # seam_tranche_prices} -> neighbor_heat_rate. Reads only each neighbor's OWN
    # gas/LMP fit, never the ISO's interchange (rule #11). Promoted from a
    # plain keyword argument to a ScenarioConfig field so the setting is
    # recorded in run_config.json instead of a silent call-site default
    # (CLAUDE.md rule 23 — this was formerly the FORWARD_SKILL_ENV /
    # MARKET_SIM_NEIGHBOR_HR_FORWARD_SKILL environment-variable channel,
    # already removed). Default None (off) is byte-identical to every keeper
    # and forecast run; only a validation script sets it.
    reliability_floor: bool = False  # ISO-agnostic temperature/net-load
    # reliability-commitment floor: look up the ISO in
    # RELIABILITY_FLOOR_REGISTRY (iso_configs.py) and apply ALL enabled
    # (zone, class, driver) limb specs via the single generic engine
    # (transmission.inject_reliability_floor). One flag arms every limb; the
    # registry is the single source of truth (seeded from the derived
    # reliability_floor_coeffs_<ISO>.csv). New ISOs/limbs need ONLY this flag +
    # a registry row + a weather file; no new code. Default off (byte-identical;
    # the registry is empty until Phase 2 fills the coefficient CSVs).
    reliability_floor_overrides: dict[str, dict] = field(default_factory=dict)
    # Per-limb run-config overrides for the generic floor, keyed
    # "<ZONE>:<CLASS>:<driver>" -> {"enabled"?: bool, "floor_pct"?: float,
    # "threshold"?: float}. Applied to the registry specs at run time via
    # iso_configs.apply_reliability_floor_overrides before the engine runs, so a
    # single limb can be toggled or re-tuned (e.g. --floor-disable ZONE:CLASS)
    # without editing the registry. Empty = registry defaults verbatim.
    class_commitment_overrides: dict[str, dict] = field(default_factory=dict)
    # Per-class commitment overrides for THIS run's ISO, keyed by plant_group
    # class (e.g. "ST_GAS") -> {"min_run_hours"?: int, "min_down_hours"?: int}.
    # Threaded through model.commitment._commitment_params so a longer steam-gas
    # min-run (a boiler held across a multi-day temperature event) can be enabled
    # per ISO×class without editing config.constants.ST_GAS_COMMITMENT_PARAMS.
    # Empty = the constant-table defaults. Default off (byte-identical).
    caiso_gas_commitment_floor: bool = False  # CAISO Resource-Adequacy
    # must-offer minimum-commitment floor: hold the gas fleet (gas_cc/gas_ct/
    # gas_st) online over the midday solar-glut window at the measured EIA-930
    # NG: NG profile (caiso_gas_floor_frac-scaled), via the hour-varying
    # FleetArrays.min_gen lower bound (transmission.
    # inject_caiso_gas_commitment_floor). RA gas can't economically cycle off
    # for the evening ramp, so it over-generates midday and CAISO exports/
    # curtails the surplus at ~$0; the economic dispatch instead decommits gas
    # and imports, staying balanced (so its midday marginal is a >=$28 import/
    # gas — the over-priced floor). The floor makes the model LONG so its
    # surplus prices at ~$0. Default off (byte-identical); CAISO-only, no-op
    # without a measured NG: NG profile. Pair with --interchange-shaping
    # (export side) + the $0 export/curtailment sink.
    caiso_gas_floor_frac: float = 1.0  # Fraction of the measured EIA-930 NG: NG
    # (month x hour-of-day median) the midday gas floor targets. 1.0 = the full
    # measured profile; lower keeps modeled gas TWh nearer EIA-923 (forcing
    # commitment can inflate gas — the surplus must export/curtail, not pad the
    # mix). Only used when caiso_gas_commitment_floor is on.
    caiso_ra_mustoffer: bool = False  # CAISO Resource-Adequacy must-offer
    # COMMITMENT (Step-1 replacement for the measured-outcome gas floor above).
    # A real RA must-offer obligation is a *commitment* — the unit is online at
    # minimum stable load and FREE to dispatch down to it — NOT an energy floor
    # pinned to measured generation. Applied P1-NATIVE (P2 is archived — CLAUDE.md
    # "Dispatch & Commitment": P0/P1 are the only production passes and every run
    # is scored on P1): the bridge is written as a min_gen floor BEFORE the single
    # P1 clearing solve (pipeline.commitment.caiso_ra_p1_floor_fleet /
    # build_caiso_ra_p1_prep, injected at the P0->P1 seam), detected from the
    # base-cost P0 run pattern via model.commitment.caiso_ra_mustoffer_min_gen. It
    # holds each gas CC/CT unit that P0 runs BEFORE and AFTER a midday idle gap
    # SHORTER than its physical minimum-down time at caiso_ra_min_load_frac x
    # available capacity across that gap: it cannot economically cycle off and
    # restart for the evening ramp, so its RA commitment keeps it online at
    # min-load instead of cold midday. Detected from the model's OWN P0 run
    # pattern + the physical min-down time (CC_COMMITMENT_PARAMS), both
    # forward-derivable and condition-responsive — no measured-outcome pin
    # (CLAUDE.md #1/#11). The P1 LP dispatches economically above the floor, so it
    # only binds when oversupply would otherwise drive the committed unit cold;
    # the midday ~$0 price comes from real oversupply (solar/imports), not the
    # floor. Default off (byte-identical); CAISO-only via _calibration_config.
    # (This no longer triggers a P2 pass; the former P2 RA branch in
    # pipeline.commitment is retained for the legacy --enable-legacy-p2 path.)
    caiso_ra_min_load_frac: float = 0.40  # Minimum stable load of a committed
    # gas unit as a fraction of available capacity, for the RA must-offer bridge
    # commitment above. ~0.40 is the typical combined-cycle / frame simple-cycle
    # minimum generation (one combustion train at minimum; NREL "Power Plant
    # Cycling Costs" 2012; CAISO Master File PMin/PMax). A physical turn-down
    # limit, not a price/volume fit. Only used when caiso_ra_mustoffer is on.
    caiso_ra_startup_bridge: bool = False  # CAISO RA must-offer STARTUP-COST-AWARE
    # extension (caiso-44). The plain RA bridge (caiso_ra_mustoffer above) floors a
    # CC/CT only across a midday idle gap SHORTER than its physical min-down time.
    # This extends it to ALSO floor a gap LONGER than min-down when cycling off is
    # uneconomic, per the standard unit-commitment restart inequality:
    #   startup_per_mw > (MC - LMP_gap) x caiso_ra_min_load_frac x gap_hours
    # RHS = the NET cost of holding at min-load through the gap: the min-load energy
    # displaces the marginal import/gas at the gap-hour LMP, so it costs (MC - LMP),
    # not full MC. When gas is near-marginal (MC ~ LMP) the RHS collapses toward
    # zero and even a small startup cost holds the unit online — why real CAISO
    # keeps ~6.8 GW gas committed through the deep spring belly a pure LP over-cycles
    # (it pays no startup on a continuous ramp). MC is the unit's own marginal cost
    # and LMP_gap the model's OWN base-cost (P0) dual the P1-native bridge prices
    # the gap at — both forward-derivable, NO measured-generation pin (CLAUDE.md
    # #1/#11), so unlike the removed NG:NG floor this is keeper-eligible. Default
    # off (byte-identical); requires caiso_ra_mustoffer; CAISO-only. Toggle with
    # --caiso-ra-startup-bridge.
    caiso_ra_bridge_decommit: bool = False  # Solar-proportional / seasonal
    # DECOMMITMENT control on the startup bridge above (caiso-48). The plain
    # startup bridge over-commits in high-solar years: the P1 LMP it prices the
    # gap at is biased HIGH midday (P1, with no floors, is never long), so
    # MC − LMP ≈ 0 and every gap bridges, in every season, at any length —
    # caiso-45 tripped the EIA-923 gas guardrail (+34.4% in 2025). Two pieces of
    # real unit-commitment physics bound it (model.commitment
    # ._apply_economic_bridges): (1) DAY-AHEAD HORIZON — the DAM (CAISO IFM/RUC)
    # commits one 24-hour operating day, so only a gap ≤ DA_COMMITMENT_HORIZON_
    # HOURS can be an intra-day min-load hold; longer idles are next-day
    # decommit/re-offer decisions (the seasonal decommitment). (2) OVER-
    # GENERATION REPRICING + RUC-ORDER DECOMMIT — held min-load energy is worth
    # the gap LMP only while it displaces dispatchable supply (P1 import
    # dispatch backs down, export-sink headroom absorbs); once the candidate
    # floors exceed that hourly absorption the marginal displaced MWh is a
    # curtailable renewable at the negative keep-running offer, so surplus gap
    # hours reprice to -renewable_keep_running_value and uneconomic bridges
    # decommit cheapest-startup-first (the RUC de-commitment order), each
    # removal shrinking the surplus (monotone, no iteration). Deeper solar →
    # less absorption → more decommitment: the solar-proportional ramp. All
    # inputs are the model's own P1 solution + physical constants — nothing fits
    # a gas/price residual (CLAUDE.md #1/#11), keeper-eligible. Default off
    # (byte-identical caiso-45 bridge); requires caiso_ra_startup_bridge;
    # CAISO-only. Toggle with --caiso-ra-bridge-decommit.
    caiso_ra_mustoffer_quantity_gate: bool = False  # CAISO RA must-offer
    # QUANTITY gate (gap G-61 path (a), D-8 closure §7). Real CAISO attaches
    # the must-offer obligation only to RA-CONTRACTED (shown) capacity; the
    # ungated P1-native bridge floors the WHOLE merchant gas CC fleet through
    # the solar belly (no RA-quantity gate), over-committing CC and
    # pre-positioning it to out-compete fast-start CT at the evening ramp.
    # With this gate on, the bridged fleet is capped at the PUBLISHED
    # gas-fired must-offer RA capacity for the compliance year
    # (constants.CAISO_RA_MUSTOFFER_GAS_MW — DMM Annual Report "Must-Offer:
    # Gas-fired generators", the bid-insertion category): bridged plants are
    # dropped cheapest-startup-first (the RUC de-commitment order already
    # used by _apply_economic_bridges — cheapest to bring back tomorrow
    # cycles off first) until the kept plants' summed pmax fits the published
    # quantity. A measured market-design quantity, forward-regenerating
    # (refreshes on each DMM annual publication), never fitted to a residual
    # (rules 13/23). MEASURED NO-OP AT HEAD (2026-07-07, G-61a): the bridged
    # CC fleet totals 13.7-13.8 GW true pmax in 2023-25, inside the published
    # 19,130/15,566/15,566 MW in every year — the model bridges LESS capacity
    # than reality obligates, so G-61's over-commitment is not a quantity-
    # scope error (the conflation of must-OFFER with must-stay-online is —
    # path (b)). Kept as the forward scope guard: it binds when the published
    # series drops below fleet scale. Default off (byte-identical); requires
    # caiso_ra_mustoffer; CAISO-only. GATED CHANGE (alters dispatch volumes).
    caiso_ra_bridge_startup_aware: bool = False  # CAISO RA bridge STARTUP-AWARE
    # run detection (gap G-61 path (b), D-8 closure §7). The P1-native bridge
    # detects committed runs from the raw base-cost P0 dispatch; P0 pays no
    # startup cost on a continuous ramp, so it over-cycles CC — phantom
    # micro-runs a real unit commitment would never start chop the solar
    # belly into sub-min-down gaps, every one of which the physical bridge
    # floors unconditionally. With this on, a detected run anchors a bridge
    # only when it is COMMITMENT-REAL under the unit's own start economics:
    # the run's P0 energy margin per MW of capacity,
    #   Σ_t∈run (LMP_P0[zone,t] − MC[g,t]) × dispatch[g,t] / pmax[g],
    # must cover the unit's published per-MW startup cost (the same
    # NREL/CAMPD-bin startup the economic bridge prices, _ra_bridge_unit_
    # params) — the standard UC start test: one startup amortized over the
    # run's whole margin. Runs failing it are removed BEFORE gap detection,
    # so phantom fragments stop manufacturing short gaps and a bridge only
    # ever spans two genuinely-committed runs. Inputs are the model's own P0
    # solution + published class startup costs — zero fitted parameters,
    # forward-derivable (rules 13/17); the run threshold and min-down physics
    # are unchanged. Default off (byte-identical); requires
    # caiso_ra_mustoffer; CAISO-only. GATED CHANGE (alters dispatch volumes).
    caiso_ra_bridge_curtailment_release: bool = False  # CAISO RA bridge
    # CURTAILED-VRE RELEASE (gap G-61 path (c), D-8 closure §7). A bridge gap
    # is NOT floored when the model's own P0 solution shows genuine
    # curtailed-VRE volume inside it — wind+solar dispatched below their
    # available potential (Σ cf × cap − Σ dispatched >
    # constants.CAISO_CURTAIL_RELEASE_EPS_MW, a float-noise guard) — because
    # holding thermal min-load through real renewable curtailment displaces
    # curtailable energy, and real CAISO decommits RA units in oversupply
    # (RUC de-commitment / exceptional dispatch) rather than curtail more
    # VRE. This is the VOLUME form of the §7 price-based release (built,
    # correct in isolation, reverted as inert — the midday LMP never reaches
    # the curtailment floor here): volume fires whenever curtailment
    # physically occurs, price only when the LP is long enough to hit the
    # renewable offer floor. Ex-ante honesty note (FINDING-caiso-seam-diurnal
    # -2026-07-07): at HEAD the model reaches the curtailment margin only
    # 0-28 h/yr (the seam under-imports midday), so this release is expected
    # near-inert until the seam-shape fix lands — build it because it is real
    # market design (rule 1), record what it does. Zero fitted parameters;
    # inputs are the model's own P0 solution + the LP's own renewable bounds.
    # Threaded on the backcast path (run_calibration.py); the forecast
    # orchestrator does not yet pass the potential series, where the flag is
    # inert by construction. Default off (byte-identical); requires
    # caiso_ra_mustoffer; CAISO-only. GATED CHANGE (alters dispatch volumes).
    neiso_gas_coldsnap_derate: bool = False  # NEISO winter gas-fired availability
    # derate (temperature-dependent forced outage, TDFOR). On deep-winter cold
    # snaps the gas-electric constraint physically curtails NON-dual-fuel gas
    # generators (the pipeline diverts to heating; units without firm transport or
    # oil backup cannot get fuel), so a share of the gas fleet is UNAVAILABLE — not
    # merely expensive. An energy-only LP keeps them available-but-dear (price caps
    # at the dual-fuel oil parity ~$258), so it never goes reserve-short and never
    # produces the winter scarcity tail. This derates non-dual-fuel gas-fired
    # availability over the cold-snap window (NEISO_COLDSNAP_FLOOR_HOURS) by
    # clip(slope*(t0 - TMIN), 0, cap) keyed to the NEISO load-weighted daily MIN
    # temperature (transmission.inject_neiso_gas_coldsnap_derate). Dual-fuel units
    # are EXCLUDED — they switch to oil (apply_dual_fuel_pricing), not vanish.
    # Pairs with energy_reserve_coopt: the derate creates the reserve shortage the
    # NEISO RCPF co-opt then prices into the LMP (the >$300 cold-hour tail), which
    # also widens the peak/trough spread so storage cycles. Forward-reproducible
    # (a forecast year's pinned TMIN) and condition-responsive (colder winter ->
    # more derate); the magnitude traces to NERC cold-weather forced-outage data,
    # NOT a fit to the price tail. Default off (byte-identical); NEISO-only.
    neiso_gas_derate_t0_c: float = -7.0  # Cold-limb zero-crossing (~20 degF): above
    # this daily MIN temperature gas forced-outage stays at its base equipment rate
    # (no incremental fuel-constraint derate). NERC cold-weather analyses place the
    # onset of sharply-rising generator forced outages near 20 degF.
    neiso_gas_derate_slope_per_c: float = 0.018  # Incremental gas forced-out
    # fraction gained per deg C of TMIN below t0. Sets ~0.20 (the cap) at ~ -18 degC
    # (0 degF): slope = cap / (t0 - T_extreme) = 0.20 / (-7 - -18) ~= 0.018.
    neiso_gas_derate_cap: float = 0.20  # Max incremental gas-fired forced-out
    # fraction at extreme cold. Anchored to the NERC/FERC Winter Storm Elliott
    # analysis: gas fuel-supply issues drove ~20% of unplanned generator
    # outages/derates and gas was the largest forced-out category (Eastern
    # Interconnection 13% of all capacity forced out at the peak) — a published
    # physical magnitude, not tuned to land a target number of >$300 hours.
    neiso_oil_burn_budget: bool = False  # NEISO oil-burn inventory budget.
    # ISO-NE's dual-fuel and oil-primary peaker fleet rations a LIMITED
    # on-site distillate stock over multi-day cold snaps. The energy-only LP
    # caps every top hour at the flat dual-fuel oil-parity (~$258/MWh) and
    # produces 0 hours > $300, because oil commodity price does NOT spike
    # like pipeline-gas basis. The real scarcity is a QUANTITY (inventory)
    # limit, not a price: when the monthly oil-burn budget binds in a cold
    # snap, the marginal oil MWh is priced at SRMC + shadow price, lifting
    # the cleared LMP above oil parity and producing >$300 hours
    # endogenously. Structurally identical to the hydro monthly energy
    # budget (dispatch.py:_build_hydro_rows). Budget derived from measured
    # EIA-923 Schedule 5 monthly Petroleum receipts (MMBtu, converted to
    # MWh via fleet heat rates) — a reproducible physical deliverability
    # input (CLAUDE.md #10: could be produced for a forward year from a
    # seasonal oil-deliverability assumption). NEISO-only, backcast-only,
    # default off (byte-identical). See data/fuel.py:load_oil_burn_budget.
    #
    # SUPERSEDED for NEISO by neiso_winter_fuel_inventory below: load_oil_burn_
    # budget derives the budget from EIA-923 petroleum RECEIPTS (a measured
    # deliveries-to-tank OUTCOME, 1-2 plants reporting) — inadmissible as a
    # budget driver under CLAUDE.md #13 (no forward analogue; the dispatch
    # validated is not the dispatch forecast). Kept only for reference; not a
    # keeper path.
    neiso_winter_fuel_inventory: bool = False  # NEISO winter (Nov-Mar) oil-burn
    # inventory budget, Component A of the fuel-inventory / seasonal-reliability
    # build (docs/multi-iso/neiso-winter-fuel-inventory-plan-2026-07.md). Same
    # LP mechanism as neiso_oil_burn_budget (dispatch.py:_build_oil_budget_rows,
    # structurally identical to the hydro monthly-energy budget) but the budget
    # is DERIVED from forward-regenerable capacity/logistics quantities — tank
    # start-fill + re-supply delivery rate + boiler firing rate — from the
    # winter-fuel-inventory clean datatype (ISO-NE OFSA / Winter Reliability
    # Program studies + EIA-860), NOT from measured burn/receipts. Rule-#13
    # admissible: could be produced for a forward year and responds to changed
    # weather/fleet. Scope is the oil-capable fleet — oil-primary units PLUS the
    # dual-fuel gas units' oil limb (the coverage hole that killed the F923
    # neiso-40 probe), the latter budgeted only over their exogenous oil-switch
    # hours so gas generation is never capped. One pooled fleet row per winter
    # month; the binding dual is the endogenous winter scarcity rent, lifting
    # the persisted P1 LMP above the flat dual-fuel oil-parity cap (~$258).
    # NEISO-only, backcast-only, default off (byte-identical). See
    # data/winter_fuel_inventory.py:build_winter_fuel_budget.
    neiso_winter_fuel_start_fill_bbl: float | None = None  # Start-of-winter
    # fleet oil inventory (barrels) sizing the neiso_winter_fuel_inventory
    # budget. None -> the reader's default (WRP 2014/15 low target, 2.8M bbl).
    # The Winter Reliability Program (FERC ER14-2407) published a 2.8M (low) /
    # 3.8M (high) bbl fleet oil-inventory target; the sensitivity pair solves
    # both. A program-design logistics target (admissible, CLAUDE.md #13), NOT
    # tuned to the price/volume residual.
    neiso_winter_fuel_mustrun: bool = False  # NEISO winter fuel-security
    # must-run, Component B of the fuel-inventory / seasonal-reliability build
    # (docs/multi-iso/neiso-winter-fuel-inventory-plan-2026-07.md). The seasonal-
    # reliability commitment coupled to the Component-A inventory budget above:
    # ISO-NE postures its fuel-secure steam fleet (COAL_BIT + the oil-capable
    # ST_GAS units) through winter for energy security beyond pure energy
    # economics (Winter Reliability Program FERC ER14-2407 -> Inventoried Energy
    # Program ER19-1428 -> OFSA operational posture). The energy-only LP commits
    # these units only in the few hours gas/oil is dear, so their winter energy
    # under-runs AND their oil draw never reaches the seasonal budget (leaving
    # Component A inert). This floors the fuel-secure classes at minimum-stable on
    # winter (Nov-Mar) cold days (zone daily TMIN < neiso_winter_fuelsec_tmin_c),
    # at which point the dual-fuel oil limb burns on the acute snaps and the
    # Component-A budget can bind -> endogenous winter scarcity rent (C3c) and
    # wider storage spread (C5b) as a consequence, not a tuned adder. REPLACES the
    # disabled COAL/ST_GAS tmin cold-limb reliability floors (rule 19; those were
    # disabled for thin cold-day sample, n=7-8). floor_pct = commit_frac x
    # min_stable_pct, never a measured-CF ceiling and never tuned to the residual
    # (rules 1/24). Tags MECH_WINTER_FUELSEC for D-2 attribution; a merchant
    # reliability commitment subject to the forced-share gate, ablated in the
    # zero-forcing twin. NEISO-only, backcast-only, default off (byte-identical).
    # See data/winter_fuel_inventory.py:apply_winter_fuelsec_mustrun.
    neiso_winter_fuelsec_min_stable_pct: float = 0.40  # Physical minimum-stable
    # fraction of a committed fuel-secure steam boiler (COAL_BIT/ST_GAS) — the
    # depth the winter must-run holds them at. 0.40 is the standard subcritical
    # steam-boiler turndown (Merrimack-class coal min-load ~40% of nameplate); a
    # physical engineering constant, NOT fit to the winter-energy residual.
    neiso_winter_fuelsec_commit_frac: float = 1.0  # Fraction of each fuel-secure
    # class under the winter program posture. 1.0 = the NEISO fuel-secure steam
    # fleet IS the program fleet (the coal + oil-capable steam units the WRP/IEP
    # target). A program-scope quantity; if a future EIA-860/FCM roster crosswalk
    # narrows the committed set (winter-fuel data-audit §3), this is the knob —
    # never the price/volume residual.
    neiso_winter_fuelsec_tmin_c: float = -7.0  # Cold-day gate on zone daily TMIN
    # for the winter must-run (~20 F). The NERC cold-weather forced-outage onset
    # (shared with neiso_gas_derate_t0_c): the temperature at which winter fuel-
    # security stress begins and ISO-NE postures the fuel-secure fleet. A
    # published physical threshold, NOT swept to land a target tail-hour or
    # winter-energy count (rule 24).
    nyiso_local_selfsupply: bool = False  # NYISO Long Island (zone K) local
    # self-supply floor: zone K is cable-islanded (NYC->LI 1,650 MW + ~1.2 GW
    # external ties) and carries NYISO locational-minimum-installed-capacity
    # (LMIC) / local-reliability rules that keep its own older, costlier
    # gas-steam + peaker fleet running rather than importing the full cable
    # rating of cheap NYC gas. The economic LP, lacking that rule, floods cheap
    # NYC power across the 1,650 MW link and under-runs the LI fleet (model 3.7
    # vs EIA-923 8.52 TWh, 2023; docs/nyiso-dispatch-validation-2026-06). This
    # forces in-zone dispatchable thermal generation >= NYISO_LOCAL_SELFSUPPLY_
    # FRAC[zone] x zonal load each hour, via the hour-varying FleetArrays.min_gen
    # lower bound (transmission.inject_nyiso_local_selfsupply), distributed over
    # the zone's thermal tranches cheapest-first and capped at availability (so
    # it can never manufacture unmet load). FORWARD-REPRODUCIBLE (scales with
    # load, responds to conditions) and grounded in NYISO market design — NOT a
    # pin to measured LI generation (CLAUDE.md rule #12). Default off
    # (byte-identical); NYISO-only.
    nyiso_li_lcr_tsl: bool = False  # NYISO Long Island Zone-K LCR/TSL mechanism
    # (issue #1345): REPLACES the Long_Island entry of the 0.45 self-supply
    # energy-fraction floor (a residual-identified scalar, DOF ledger S5) with
    # the published transmission-security construction. In the peak window
    # (transmission.NYISO_SELFSUPPLY_FLOOR_HOURS, HB14-21 — the design-cooling
    # condition the LCR locality requirements are defined at), the NYC->
    # Long_Island link's import limit is capped at the PUBLISHED Zone-K
    # locality import limit (data/raw/capacity-deliverability/nyiso/nyiso.csv,
    # "Long Island" import_limit: 325/275/275 MW for 2023/24-2025/26, NYISO
    # Locality Bulk-Power Transmission Capability reports), so LI in-window
    # supply beyond the external ties + the security-limited AC import clears
    # from the in-zone fleet ECONOMICALLY (LP merit order) instead of through a
    # forced min_gen floor — the floor-forced CT/ST energy the D-2 budget
    # (rule 20) charges to nyiso_local_selfsupply goes to zero for LI by
    # construction. RULE-14 BOUNDARY NOTE: the published import limit is the
    # LCR/ICAP peak-condition transmission-security boundary (N-1-1 planning
    # basis, UDR-backed external cables counted separately), NOT a real-time
    # scheduling limit; applying it outside the design-condition window would
    # force ~16 TWh/yr of LI energy vs the ~8.5 TWh physically real, so it is
    # applied ONLY in the same HB14-21 window the (narrowed, PR #1442) floor
    # already used — the window where the constraint's own driver (design
    # cooling peak) is active. The external-tie links into LI (priced import
    # node, ~1.2 GW UDR cables) stay at their physical ratings. The cap is
    # symmetric on the AC link in-window (LI->NYC export also limited to the
    # TSL there); measured LI peak-window exports are ~0, documented
    # misalignment accepted rather than new plumbing. Forward-reproducible:
    # the LCR/TSL tables publish every capability year and respond to new cables /
    # requirement changes. When on, transmission.inject_nyiso_local_selfsupply
    # skips Long_Island (one mechanism per phenomenon, rule 19); the 0.45
    # scalar remains only for the default-off legacy path. Default off
    # (byte-identical); NYISO-only.
    nyiso_firm_imports: bool = False  # NYISO firm (must-flow) import baseload:
    # Hydro-Québec (Châteauguay/Cedars) and Ontario (IESO) sell NY firm,
    # long-term scheduled hydro/nuclear baseload that flows regardless of NY's
    # hourly price — not price-responsive economy energy. The priced node prices
    # them as economic tranches (clear only when NYISO price > tranche cost),
    # backing them off in cheap-overnight hours / low-price years even though the
    # real schedule keeps flowing. This sets a must-flow floor (NYISO_FIRM_
    # IMPORT_FLOOR_FRAC x tranche capacity) on those rows via FleetArrays.min_gen
    # (transmission.inject_nyiso_firm_imports). The floor stays below the
    # measured lightest-import hour (NY imported >=922 MW in 98% of 2023 hours)
    # so it never forces a phantom over-import. FORWARD-REPRODUCIBLE (a firm
    # schedule reproduces for any year); Tier 3. Default off; NYISO-only.
    nyiso_import_reconciliation: bool = False  # NYISO priced import-node
    # boundary-flow calibration: pin the priced node's MONTHLY net interchange to
    # the measured EIA-930 schedule (eia_loader.nyiso_net_interchange) via a
    # per-month band constraint in the LP (transmission.
    # build_import_node_reconciliation -> dispatch._build_import_node_rows). The
    # economic priced node clears a near-flat ~18.5-21.6 TWh because its tranche
    # offers are near-static and do NOT track the metered schedule's year-over-
    # year decline (23.45 -> 20.35 -> 19.09 TWh), so it under-imports in 2023 and
    # over-imports in 2024/25 vs the metered schedule. This is the standard
    # production-cost boundary-flow calibration (Aurora/PLEXOS/GridView/PROMOD
    # historical validation pin the tie-line net flow against an unmodeled
    # neighbor; ReEDS fixes net trade with non-modeled regions). Unlike the prior
    # rejected "import scaling" (which degraded an already-exact served-wedge
    # match), the current priced node DEVIATES +-1-5 TWh/yr, so moving it toward
    # the measurement REPLACES an economic estimate with the authoritative
    # measurement (CLAUDE.md rule #11) — the opposite of overfitting. The target
    # is the measured schedule itself, NOT a residual-minimizing volume (rule
    # #12); the band (NYISO_IMPORT_RECON_BAND_FRAC) only leaves the priced
    # tranches room to set the marginal price WITHIN each month's envelope. Keeps
    # imports price-responsive within the band; the priced node stays the forward
    # mechanism (in a forecast the constraint is sourced from the neighbor's
    # forecast net position or relaxed). Requires --priced-interchange. Default
    # off (byte-identical); NYISO-only.
    nyiso_import_hub_prices: bool = False  # NYISO priced import-node tranches
    # repriced at the MEASURED hourly neighbor system LMP: PJM_west takes the
    # PJM hourly Day-Ahead hub mean, ISONE_tie the ISO-NE hourly DA hub mean
    # (data/raw/_validation-source/actual_lmp_hourly_{PJM,NEISO}.parquet via
    # neighbor_price.neighbor_lmp_hourly, rt fallback), the residual
    # import_scarcity block the hourly MAX of the two (the deep non-firm MW
    # beyond the direct-tie blocks cannot be cheaper than every real adjacent
    # market), each + the inter-control-area wheeling hurdle; the export_surplus
    # sink is repriced at the same max − hurdle (sell to the best-paying
    # neighbor), making the seam arbitrage-free. Replaces the static per-year
    # IMPORT_TRANCHES_BY_YEAR ladder, which the neighbor_price module documents
    # as "a backcast fit — re-fitted per year, blind to neighbor fundamentals":
    # the flat $13.5-79.7 (2024) ladder caps NYISO's winter/heat-wave price
    # exactly when the real seam repriced with the neighbors (Dec-2024 NEISO
    # $84.5/mo mean vs the $44.9 ISONE_tie constant; Jun-2025 heat-wave DA
    # spikes). The NYISO analogue of miso_pjm_lmp_import_pricing (measured PJM
    # border DA LMP) and caiso_import_hub_prices (measured WECC intertie LMP) —
    # a measured neighbor price-formation input (rule #12), blind to NYISO's own
    # flow (rule #11); in a forecast year the same tranches price off the
    # modeled neighbor / reference-price formula, so the mechanism regenerates
    # from forward drivers. HQ_hydro / IESO_Ontario keep their firm-contract
    # ladder values (no organized-market LMP series; HQ is firm-floored). The
    # monthly EIA-930 reconciliation band, HQ firm floor and SIL cap are
    # unchanged. Requires --priced-interchange. Default off (byte-identical);
    # NYISO-only; no-op without the measured parquets.
    nyiso_iroquois_winter_spread: bool = False  # NYISO eastern (Iroquois Z2)
    # winter gas premium, reconciled from measured data (rule #13). The
    # committed reference construction distributes the MEASURED annual
    # NYISO-SOM Iroquois-Transco spread FLAT across months, under-reading the
    # constrained winter months (Dec-2024 $3.16/MMBtu modeled vs the ~$9 New
    # England complex the Z2 segment - a Connecticut trading point - trades
    # in). No free Iroquois series exists (verified: zero prints in 146 NGWU
    # weekly pages 2023-25; NGI/ICE paywalled), so the measured ANNUAL spread
    # is re-allocated across months in proportion to the measured Algonquin
    # (MA-citygate) monthly basis - the New England pipeline-scarcity signal
    # that physically causes the Iroquois premium - then CAPPED month-by-month
    # at the measured Algonquin Citygate monthly level (rule #14: Z2 delivers
    # INTO the New England market area, so it cannot out-price the citygate
    # ceiling of the complex; the cap floors at the committed flat
    # construction so it only shaves scarcity-month excess). The shaved
    # excess re-enters as a year-round base differential water-filled into
    # months with ceiling headroom, preserving the measured SOM ANNUAL spread
    # exactly - the reconciliation of three measured series (SOM annual +
    # AGT scarcity shape + Algonquin ceiling), no fitted constant. Zonal companions switch from flat annual offsets to
    # monthly hub ratios so NYC resolves to its own measured Transco Z6 NY
    # monthly and Upstate to its measured SOM annual level riding the Henry
    # Hub shape (fuel.nyiso_reconciled_reference_monthly /
    # nyiso_zonal_gas_ratios_monthly). No fitted constant, nothing reads a
    # model output; forward years regenerate it from the forward basis
    # seasonality. Requires nyiso_zonal_gas_basis + gas_hub_basis_overlay.
    # Default off (byte-identical); NYISO-only.
    nyiso_synchronised_reserve: bool = False  # NYISO online-gated SPINNING
    # reserve (path A of the downstate-reserve frontier, docs/handoffs/
    # nyiso-downstate-reserve-incidence-2026-06.md). Adds a NYC locational
    # 10-minute SPINNING reserve family on an ONLINE-GATED reserve class whose
    # headroom counts only online generation (R[spin,z] <= rho * sum online
    # quick-start P), not idle capacity — so an offline peaker no longer counts
    # its full pmax as deliverable spin. This is the root-cause fix for the NYC
    # peaker under-run + missing >$300 tail: the idle-allowed headroom let phantom
    # (offline) reserve satisfy every family, so the RCPF never priced. Holding
    # online spin forces NYC peakers to commit (CT_PEAKER energy up) and binds the
    # family so the RCPF tail fires endogenously (C3c/C3a up). Requirement = 1/2
    # of the NYC 10-min total (the published NYISO spinning = 1/2-of-total ratio),
    # NOT fitted to the residual. With the P2 commitment screen ON (--commitment)
    # this becomes PATH B: the spinning family rides the ordinary class-1
    # headroom and commitment (apply_commitment_with_coal_pin zeroing decommitted
    # availability + reserve_adequacy_commit) is the online gate, so the class-1
    # NYC headroom equals Sum_online(pmax - P) — the physically-correct
    # synchronised headroom the online-gated proxy could not express. With
    # commitment OFF it stays PATH A (the online-gated proxy above). Default off
    # (byte-identical); NYISO-only; requires --energy-reserve-coopt.
    nyiso_spin_headroom_frac: float = 1.0  # Path-B committed-capacity target
    # multiplier for the reserve-adequacy commit: force-commit NYC quick-start
    # until committed capacity (Sum pmax x availability) covers
    # nyiso_spin_requirement_mw x this factor. 1.0 = commit exactly to the
    # MEASURED spinning requirement (the grounded default — the family then binds
    # whenever the committed downstate fleet is dispatched up); a value > 1 commits
    # more headroom so the tail fires only deeper into scarcity. A coverage
    # multiple on the measured requirement, NOT a price-residual fit (rule #12).
    nyiso_forward_net_import_twh: dict[int, float] | None = None  # FORECAST band
    # source for the NYISO import reconciliation. In a forecast (mode="forecast")
    # there is no measured EIA-930 net interchange to band to, so the band target
    # is the NEIGHBOR'S FORECAST NET POSITION supplied here: an annual NYISO net
    # IMPORT (TWh, positive = net import) per forecast year, e.g. derived from the
    # PJM / Hydro-Québec / Ontario / ISO-NE forward export outlooks (NYISO Gold
    # Book imports, neighbor capacity-expansion / interface schedules). The annual
    # forecast is shaped to monthly targets by the forecast load distribution
    # (imports track load, so the band RESPONDS to changed conditions — the
    # forward-reproducibility test, CLAUDE.md rule #12), and the priced tranches
    # still set the marginal price WITHIN each month's envelope (band half-width
    # NYISO_IMPORT_RECON_BAND_FRAC). When this is None (the default) the forecast
    # band RELAXES to the bare priced-seam economics (no constraint) — the seam
    # clears endogenously rather than being pinned to any measured monthly total.
    # In a backcast (mode="backcast") this is ignored and the band targets the
    # measured EIA-930 schedule (the realization). NYISO-only.
    miso_firm_imports: bool = False  # Manitoba Hydro firm-hydro import block:
    # Manitoba Hydro sells ~10-15 TWh/yr of FIRM contracted hydro into MISO-West
    # over the Manitoba<->US HVDC / 500 kV ties — MISO's single largest import
    # source and the structural reason MISO is a net IMPORTER (EIA-930 net
    # interchange -37.9/-23.1/-19.0 TWh, 2023-25). This import sits OUTSIDE the
    # gas-margin reference-price seam (INTERFACE_NEIGHBORS["MISO"], PJM/SPP/SERC):
    # firm hydro has no gas x heat-rate price analogue, so it is a SEPARATE block
    # priced as firm hydro (a low, near-constant energy offer reflecting the
    # contract, MISO_MANITOBA_FIRM_IMPORT_OFFER), landing directly in MISO-West
    # (the model zone the ties physically enter) and counted as net interchange
    # via its fuel_type="import". The block (transmission.build_miso_firm_imports)
    # is floored as must-flow firm baseload (transmission.inject_miso_firm_imports,
    # MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC x capacity) so it flows every hour
    # regardless of MISO's hourly price. Volume is sourced from the Manitoba Hydro
    # export-contract band, NOT fitted to the net-interchange residual (rule #12:
    # a firm contract reproduces for any forward year and responds to a changed
    # contract). Requires --priced-interchange (served by the priced node). MISO-
    # only; default off here but default-ON for the MISO backcast via
    # interchange_config.resolve_miso_firm_imports (the firm Manitoba import is the correct
    # structure for MISO, not a probe). ERCOT byte-identical.
    miso_seam_flow_limit: bool = False  # MISO reference-price seam: cap each
    # seam's (PJM/SPP/South) import-band availability at the MEASURED EIA-930
    # BA-to-BA net-import deliverability envelope (per (month × hour-of-day) p90
    # of the directed flow over the seam's DIBAs; interchange_config.MISO_SEAM_DIBA,
    # data.eia_loader.measured_seam_import_envelope, transmission.inject_miso_
    # seam_flow_limit). Fixes the structural over-import: the priced seam imports
    # at the interface limit on ALL THREE borders whenever MISO's LMP exceeds the
    # neighbor's (-72/-50/-7 TWh net vs measured -38/-23/-19), but in reality only
    # the eastern PJM seam is a large net-import path — MISO nets ~0 over SPP and
    # net-EXPORTS over the southern TVA-dominated seam. The one-sided import cap
    # bounds each seam to its deliverable transfer (SPP/South clip toward ~0
    # import) while the export bands keep their priced economics; a high
    # percentile keeps headroom so the modeled price still sets the typical hour.
    # An ATC/transfer-capability proxy from the directed-flow series — reproducible
    # for a forward year and flow-responsive — NOT fitted to the net-MWh residual
    # (rules #1/#12). Requires --reference-price-interface; MISO-only (no seam-DIBA
    # map → no-op, byte-identical for other ISOs). Default off; opt-in per run.
    miso_seam_flow_percentile: float | None = None  # Override the per-seam import
    # deliverability percentile used by miso_seam_flow_limit. None keeps the
    # constants.MISO_SEAM_FLOW_PERCENTILE default (90). Raising it (e.g. 95) lifts
    # the deliverability envelope toward the measured upper-tail transfer, letting
    # the priced seam clear MORE import in tight hours — the round-2 import-lift
    # knob for the 2024/2025 structural under-import (model 8.3 vs measured 23.1
    # TWh in 2024; 2025 net-EXPORT vs measured net-IMPORT). Still a deliverability
    # ceiling from the measured directed-flow duration curve, NOT a flow pinned to
    # the net-MWh residual (rules #1/#12). A higher percentile only RELAXES the
    # cap; the priced seam economics still clear the merit order below it. Used
    # only when miso_seam_flow_limit is set; MISO-only; default keeps p90
    # (byte-identical).
    miso_pjm_border_anchor: bool = False  # MISO eastern PJM seam: re-anchor the
    # PJM neighbor price from PJM's SYSTEM-average realized LMP to its MISO-facing
    # WESTERN border hubs (ComEd / AEP-Ohio / ATSI; interchange_config.MISO_PJM_
    # BORDER_HR_BY_YEAR, applied in transmission.inject_reference_price_mc). The import
    # mirror of the pjm58 NYISO-WEST re-anchor: the MISO eastern (PJM) seam clears
    # against western PJM, which prices below the eastern-load-weighted system
    # average, so the system anchor over-prices the import and MISO under-imports
    # over its largest seam (2024 -15 vs measured -23, 2025 -3 vs -19 TWh). The
    # per-year border HR is system_HR x (mean MISO-facing border-hub LMP / system
    # LMP); the discount deepens in tight years (ratio 0.981/0.956/0.936) so 2023
    # (already matched) barely moves while 2024/2025 clear more import up to the
    # measured deliverability cap. A measured neighbor price-formation input
    # (rule #12), blind to MISO's flow (rule #11; reads only PJM zonal LMP).
    # Requires --reference-price-interface; MISO-only. Default off; opt-in.
    miso_seam_export_limit: bool = False  # MISO reference-price seam: the EXPORT
    # mirror of miso_seam_flow_limit. Cap each seam's (PJM/SPP/South) net EXPORT
    # at the MEASURED EIA-930 BA-to-BA net-export deliverability envelope (per
    # (month × hour-of-day) p90 of the directed flow over the seam's DIBAs;
    # data.eia_loader.measured_seam_import_envelope(direction="export"),
    # transmission.inject_miso_seam_flow_limit(direction="export")). Fixes the
    # structural over-EXPORT: the priced seam exports cheap MISO coal back over
    # every border whenever a neighbor's price exceeds MISO's, but in reality MISO
    # reliably net-IMPORTS over the eastern PJM seam — it cannot net-export there.
    # Raising the negative-output export bands' lower bound (min_gen) toward 0
    # clips the PJM seam's export to ~0 while SPP/South keep their measured ~GW of
    # export headroom; the export bands keep their priced economics below the cap.
    # An ATC/transfer-capability proxy from the directed-flow series — reproducible
    # for a forward year and flow-responsive — NOT fitted to the net-MWh residual
    # (rules #1/#12). Shares the miso_seam_flow_percentile knob with the import cap
    # (one p90 envelope, both directions). Requires --reference-price-interface;
    # MISO-only (no seam-DIBA map → no-op, byte-identical). Default off; opt-in.
    miso_firm_import_floor: bool = False  # Firm (must-flow) import floor on the
    # reference-price seam — the import-direction mirror of the PJM firm-export
    # floor and the Manitoba/HQ firm-import blocks. MISO net-imports from the PJM
    # seam (PJM + IESO/Ontario) in ~99-100% of hours at a stable multi-GW base
    # (cheap Ontario nuclear/hydro surplus + firm PJM-east scheduled transfers)
    # that flows regardless of the hourly spread. The gas x heat-rate economic
    # seam prices the PJM border ABOVE MISO's cheap coal and so wrongly
    # net-EXPORTS over it (the 2024 -8.3 vs -23.1 net-import miss, the 2025 +18 vs
    # -19 sign flip, and the 2025 +20 TWh energy-balance overshoot). This forces
    # the cheapest import tranches on at the measured firm base
    # (NeighborInterface.firm_import_floor_by_year, the p10 of the seam's net
    # import; transmission.inject_reference_price_firm_import) so the inframarginal
    # must-flow import displaces the over-running domestic coal/CC, the economic
    # tranches clearing on top. p10 (imported in >=90% of hours), NOT the realized
    # net interchange (rule #11); a measured market-operations input whose forward
    # analogue is the firm scheduled transfer (rule #12). Requires
    # --reference-price-interface; MISO-only (only the PJM seam carries a floor).
    # Default off (byte-identical); opt-in per run.
    miso_cc_coal_rebalance: bool = False  # MISO CC_REGULAR / COAL_BIT offer-curve
    # rebalance: raise the MISO combined-cycle committed/econ-high bands and the
    # bituminous-coal econ-high band so the MARGINAL CC / coal-bit MWh sits ABOVE
    # the priced-import hurdle (and above the under-running CT_PEAKER / ST_GAS),
    # rather than being the cheapest fill. Structural correction for the round-2
    # conservation-of-energy miss: with imports too low, cheap domestic CC_REGULAR
    # and COAL_BIT over-run (2025 coal 232 vs EIA-923 201 TWh) and price out the
    # CT peakers and gas steam. The marginal block of a baseload CC/coal unit is
    # NOT the cheapest available supply when priced imports are on the bar, so its
    # top tranche must clear above the import hurdle — an offer-SHAPE correction,
    # not a residual-tuned adder. Applied as a deep-merge offer-curve override
    # gated to iso=="MISO" (other ISOs / forecasts byte-identical). Default off;
    # opt-in per run, validated by the import↑ / CC↓ / coal↓ / CT↑ / ST↑ response.
    miso_pjm_lmp_import_pricing: bool = False  # MISO PJM seam: price each PJM
    # import/export tranche at the MEASURED hourly PJM Day-Ahead LMP at the
    # MISO-facing western border hubs (equal-weight mean of CHICAGO GEN / AEP
    # GEN / ATSI GEN — the same border decomposition as MISO_PJM_BORDER_HR_BY_
    # YEAR) + hurdle, replacing the synthetic gas × heat-rate × load-shape
    # ladder. The gas × HR ladder is too FLAT: its off-peak price never dips
    # below MISO's own cheap coal, so the model wrongly under-imports in 2024/
    # 2025 (import 17/5.8 vs actual 23/19 TWh). The real PJM border LMP dips
    # well below the flat gas × HR average in PJM's off-peak hours (p10 $15-22,
    # 29-49% of hours below $25 vs the flat $30+ ladder), pulling import into
    # those cheap hours. DISPLACES the miso_pjm_border_anchor gas × HR HR for
    # the PJM seam (the two are alternatives; don't stack). SPP/South seams
    # keep their gas × HR pricing. Requires --reference-price-interface;
    # MISO-only; no-op without the measured parquet (byte-identical).
    # Measured neighbor price-formation input (rule #12), blind to MISO's own
    # flow (rule #11 — reads only PJM hub LMP). Default off; opt-in.
    miso_seam_measured_ladder: bool = False  # MISO reference-price seams: price
    # every seam band (PJM/SPP/South, import + export) at the MEASURED per-year
    # Q-Q band ladder (interchange_config.MISO_SEAM_LADDER_BY_YEAR, derived by
    # scripts/derive_miso_seam_ladders.py: EIA-930 per-seam flow duration curves
    # coupled quantile-by-quantile with the measured MISO DA hub LMP — the NEISO
    # audit-C-6 measured-ladder pattern), replacing the gas x HR x load-shape
    # band prices + hurdle for backcast years. Fixes the 2025 import starvation
    # (G-23 residual): the measured PJM+IESO seam is a firm/scheduled base that
    # flows in ~98-100% of hours UNCORRELATED with the hourly spread (r=+0.06;
    # 2025 RT spread $0.00 while 28 TWh flowed; 46-56% of import MWh inside the
    # $2 hurdle band), which a spot-spread-arbitrage seam structurally deletes
    # in a zero-spread year (miso-45: 3.4 TWh gross imports vs 19.0 actual net).
    # The ladder is the seam's revealed supply curve: the LP still clears each
    # band economically on ITS OWN hourly price (nothing forced — contrast the
    # rejected miso_firm_import_floor pin); the measured (month x hod) seam
    # envelopes and band capacities are unchanged. Measured-behaviour
    # identification, frozen formula, zero fitted parameters (rule 23); forward
    # years keep the gas-elastic reference-price formula (two-track, like
    # hr_by_year; pooled ladder = the forward story, see the registry comment).
    # DISPLACES miso_pjm_border_anchor / miso_pjm_lmp_import_pricing on the
    # rows it prices (alternatives, never stacked; this overwrite runs last).
    # Requires --reference-price-interface; MISO-only; no-op for years outside
    # the registry (byte-identical). Default off; opt-in per run.
    caiso_import_hub_prices: bool = False  # Price the CAISO priced-import node's
    # tranches at the MEASURED hourly WECC neighbor-hub LMP each proxies, instead
    # of the static fitted ladder in IMPORT_TRANCHES["CAISO"]. The PNW blocks
    # (PNW_hydro_base/PNW_midC) take the Mid-Columbia / Malin (COI/PDCI) intertie
    # price; the desert-SW blocks (DSW_solar_PV/DSW_CCGT/DSW_CT) take the Palo
    # Verde / Mead (Path 46) price. Diagnosis (DIAGNOSIS-caiso-import-ladder
    # -2026-06-19): the static ladder — re-fit in bundle mode against the model's
    # OWN solved price — prices imports too high and aseasonally, so the
    # import-set cheaper hours run high and the node never goes long enough to
    # price the negative midday tail (model 14 hrs <=$0 vs actual 868). The
    # measured intertie LMP is the real delivered cost of the imported energy:
    # seasonal (spring PNW-runoff crash), negative in the desert-SW solar glut,
    # reproducible for a forward year, and responsive — not a number tuned to the
    # residual. This is lever (A): it fixes the import-set hours + the negative
    # tail; it does NOT fix the gas-cost-bound median (the larger half of the body
    # overprice — doc lever B). Pair with --interchange-shaping so cheap imports
    # stay at the real deliverable volume (else over-import). Carried via a
    # post-assembly mc overwrite (transmission.inject_caiso_import_hub_prices +
    # data.eia_loader.measured_import_hub_prices). Default off (byte-identical);
    # CAISO-only; no-op without the measured intertie parquet (data/raw/
    # _validation-source/wecc_intertie_lmp_hourly_CAISO.parquet), fetched from
    # CAISO OASIS by the fetch-caiso-oasis workflow (open-egress runner).
    caiso_import_gas_coupling: bool = False  # Shift the gas-set CAISO import
    # tranches (DSW_CCGT, DSW_CT) by the measured commodity-gas delta
    # (iso_hub_monthly_gas_prices - iso_monthly_gas_prices) x heat rate, so the
    # desert-SW gas imports track the same commodity spot the hub-basis overlay
    # applies to in-state gas. Forecast-consistent, no-OASIS replacement for the
    # desert-SW leg of lever A (PLAN-caiso-gas-coupled-imports-2026-06-20): when
    # --gas-hub-basis-overlay cheapens in-state gas, uncoupled fitted import
    # blocks get undercut and gas TWh over-runs (+12%, RESULTS-caiso-leverB-
    # citygate); coupling moves both legs together so imports hold their share
    # and gas stays disciplined while the body still drops. The shift is ~0 at
    # the baseline gas level (preserves validated import volume); no new fitted
    # constant. Carried via a post-assembly mc shift
    # (transmission.inject_caiso_import_gas_coupling). Default off
    # (byte-identical); CAISO-only; pairs with --gas-hub-basis-overlay; no-op for
    # forecast years (no measured gas basis). Does NOT address the negative
    # midday tail — that is caiso_import_solar_shape below.
    caiso_import_solar_shape: bool = False  # Restore the CAISO negative midday
    # tail. The desert-SW solar import block (DSW_solar_PV / Palo Verde hub) is
    # the marginal CAISO import midday, but its level is priced flat (gas-coupled
    # ~$48), so the model floors at ~$0 midday (14 hrs <=$0 vs actual ~868, 2024).
    # This collapses that block's per-hour offer toward -renewable_keep_running_
    # value as CAISO net load (load less utility solar/wind) drops into its annual
    # belly, so the marginal desert-SW solar import bids negative in the spring
    # solar glut and sets a sub-$0 LMP. Net-load-gated (fires spring-midday, not
    # summer-midday); depth is the existing REC/PTC keep-running constant (no new
    # fitted price level). Carried via a post-assembly mc shift
    # (transmission.inject_caiso_import_solar_shape); applies on top of the gas
    # coupling. Default off (byte-identical); CAISO-only.
    caiso_solar_shape_nl_hi_pct: float = 30.0  # Net-load percentile (of the
    # dispatch year's own net-load series) above which the solar-shape offer
    # collapse (above) does not fire at all, and below which it ramps in. Net
    # load is CAISO's own duck-curve diagnostic: load minus utility-scale wind/
    # solar, at its annual minimum in the spring midday "belly" when solar
    # output is largest relative to (still-low, pre-summer) load. CAISO's
    # published duck-curve analyses (e.g. the original 2013 "duck chart") and
    # its own net-load duration curve show the belly spanning roughly the
    # bottom quartile-to-third of hours in a year — the choice of a percentile
    # BAND (not a fixed MW level) is what makes the gate forward-reproducible:
    # it re-centers on whatever net-load distribution the dispatched year (or a
    # future forecast year with more solar) actually produces, rather than
    # freezing today's belly depth in MW. 30% marks the outer edge of that
    # band, where the ramp begins tapering back to the flat gas-coupled offer.
    # Derived quantitatively from the EIA-930 CISO net-load distribution by
    # scripts/derive_caiso_solar_shape_band.py (frozen, rule 23 — re-run only
    # on a new 930 vintage): the "pure belly" edge — the largest percentile P
    # such that >=99% of hours with net load <= p(P) are solar-driven
    # inversion hours (net load below the local day's overnight 00-05h
    # minimum, the duck's defining signature) — comes out 33.0/30.0/34.5 for
    # 2023/2024/2025, confirming 30 as the stable conservative edge.
    # (Historically this pair was checked post-hoc against realized negative-
    # price hours as a sanity diagnostic — see
    # transmission.inject_caiso_import_solar_shape's docstring — but that
    # check is not the anchor: the band is set from the net-load shape itself.)
    caiso_solar_shape_nl_lo_pct: float = 10.0  # Net-load percentile at/below
    # which the collapse is total (s=1, offer floors at
    # -renewable_keep_running_value): the deepest ~tenth of net-load hours,
    # the trough of the duck-curve belly where the regional WECC solar/hydro
    # glut is most acute. Same net-load-percentile grounding as the HI
    # threshold above; per scripts/derive_caiso_solar_shape_band.py the
    # canonical deep-belly population (spring Mar-May midday 11-16h local,
    # the belly of CAISO's published duck chart) has its median annual
    # net-load rank at 10.0/5.6/6.0 (2023/2024/2025, p75 <= 16.6) — the deep
    # belly saturates the bottom decile, confirming 10.
    caiso_bidir_intertie: bool = False  # Model CAISO's WECC tie as a SINGLE
    # signed flow instead of two independent one-way mechanisms. The legacy node
    # carries priced import tranches AND separate export sinks on the same
    # external bubble, so the LP can simultaneously import the cheap midday hub
    # and stay long on its own solar (2024 diurnal interchange corr −0.65,
    # anti-correlated with the measured tie). This collapses both legs onto one
    # net direction over a shared directional cap (import ≤ ~8.3 GW, export ≤
    # ~3.5 GW), pricing import at hub + per-tranche border carbon and export at
    # the hub. Because every import leg (hub + carbon) is priced at/above the
    # export leg (hub) at every hour, the legs are arbitrage-free by construction
    # — the LP never imports and exports in the same hour, so the tie reverses to
    # export in the midday solar glut and the diurnal sign tracks the measured
    # interchange (no MIP, pure LP). Supersedes --caiso-import-hub-prices /
    # --caiso-import-gas-coupling / --caiso-import-solar-shape (the legacy
    # two-mechanism injectors) when on. Carried by
    # transmission.build_caiso_bidir_intertie +
    # transmission.inject_caiso_bidir_intertie_prices. Default off
    # (byte-identical); CAISO-only; no-op without the measured intertie parquet
    # (2023 falls back to the static ladder, like --caiso-import-hub-prices).
    caiso_per_hub_intertie: bool = False  # Model CAISO's WECC tie as TWO signed
    # corridors — COI/Path-66 at the Malin hub into NP15 (north) and Path-46/WOR
    # at the Palo Verde hub into SP15 (south) — each a single signed flow priced
    # at its OWN measured intertie hub. The unification of --caiso-bidir-intertie
    # (single signed flow → per-hub netting, fixes the inverted diurnal sign) and
    # --caiso-import-hub-prices (per-hub basis, Malin != Palo Verde): the bidir
    # node had to average the two hubs into one price (discarding the basis), and
    # the hub-price node kept the basis but pooled both legs onto one bubble (so
    # the cheap Palo Verde midday block filled the whole 8.3 GW budget and never
    # netted → over-import + inverted diurnal). Two per-hub signed legs recover
    # both: each corridor carries one net direction per hour over its own real
    # link, so the Palo Verde leg reverses to EXPORT in the midday solar glut
    # instead of over-importing. The 8.3 GW simultaneous-import cap stays as the
    # WECC_import_simultaneous interface limit, re-homed to the two corridor
    # links. Supersedes --caiso-import-hub-prices / --caiso-bidir-intertie /
    # --caiso-import-solar-shape (the measured per-hub Palo Verde price already
    # prints the negative midday tail solar-shape proxied; --caiso-import-gas-
    # coupling still applies to the desert-SW gas legs). Carried by
    # transmission.split_caiso_import_node_per_hub +
    # transmission.build_caiso_per_hub_intertie +
    # transmission.inject_caiso_per_hub_intertie_prices. Default off
    # (byte-identical); CAISO-only; 2023 falls back to the static ladder.
    caiso_perhub_firm_base: bool = False  # Keep the firm/contracted import
    # tranches (transmission.CAISO_FIRM_IMPORT_TRANCHES: PNW_hydro_base = BPA
    # firm hydro over COI, DSW_solar_PV = desert-SW solar PPAs over Path-46) at
    # their static contract-cost estimates while caiso_per_hub_intertie prices
    # the spot-traded tranches (Mid-C economy, DSW thermal, scarcity) and both
    # export legs at the measured hourly hub. The real market schedules the
    # specified/contracted majority of CAISO's imports at contract cost — they
    # are INFRAMARGINAL, so CAISO clears domestic while the tie still flows
    # (2023/24 summers: CAISO $50-54 with Palo Verde spot at $69-74 and 3-4 GW
    # importing). Pricing every tranche at spot transplants the hub spike into
    # CAISO whenever the tie is marginal. Requires caiso_per_hub_intertie.
    # Default off (byte-identical).
    caiso_corridor_flow_limit: bool = False  # Cap each CAISO per-hub corridor's
    # import-direction flow at the MEASURED diurnal deliverability envelope (an
    # ATC proxy): the per-(month × hour-of-day) p95 net import on COI/Path-66 and
    # Path-46/WOR from EIA-930 BA-to-BA interchange. The neighbors are themselves
    # long on solar midday, so the transfer they can schedule into a long CAISO
    # collapses ~6→~3.6 GW (DSW) and ~2.3→~0.8 GW (PNW) midday — but the per-hub
    # injector prices the whole neighbor stack at the cheap midday hub LMP, so
    # without this ceiling the LP pulls the neighbors' idle thermal tranches up to
    # the 8.3 GW simultaneous cap (the spurious ~5 GW midday over-import behind
    # the inverted-diurnal residual). Applied as a one-sided hourly upper bound on
    # the corridor link's import flow (export keeps the physical TTC), so the LP
    # still clears its merit order below the ceiling — a capability limit, not a
    # flow pinned to the residual (rule #12). Requires caiso_per_hub_intertie (the
    # split that creates the corridor links). Carried by eia_loader
    # .measured_corridor_flow_envelope + transmission.build_caiso_corridor_flow_
    # groups. Default off (byte-identical); CAISO-only.
    caiso_firm_import_shape: bool = False  # Shape the firm/contracted CAISO
    # import blocks' hourly availability by the MEASURED revealed import-base
    # profile instead of a flat 8760 block (caiso-73; FINDING-caiso72 live
    # lead #1). The flat firm base makes the same MW available every hour,
    # while measured CISO corridor net imports run 5.3-6.3 GW overnight,
    # 0.2-1.3 GW midday and ramp back to 5.4-6.2 GW in the evening — the model
    # under-imports the deep evening 1.4-2.2 GW and over-imports midday
    # (+2.3 GW at h14). Level anchor per corridor = the YEAR's DMM RA-import
    # capacity × MIC corridor split (interchange_config.IMPORT_TRANCHES_BY_
    # YEAR — the documented published sizing), so annual firm energy
    # capability is conserved; shape = the unit-mean per-(month × hod) median
    # of measured total CISO corridor net imports (eia_loader.measured_firm_
    # import_shape, model-clock mapped), same-year in a backcast and pooled
    # multi-year climatology in a forecast year (DMM RA import contracting is
    # a persistent structure). An hour-varying pmax CAPABILITY the LP still
    # clears below — never a price adder, never a flow pinned to the residual
    # (rules #13/#14). Carried by transmission.inject_caiso_firm_import_shape
    # via the shared apply_interchange_injections seam (both orchestrators).
    # Requires caiso_per_hub_intertie + caiso_perhub_firm_base. Default off
    # (byte-identical); CAISO-only.
    caiso_intertie_reference_price: bool = False  # Price each CAISO per-hub WECC
    # corridor from the FORWARD reference-price formula instead of the measured
    # OASIS hub LMP: per-hub price = (henry_hub[year] + gas_basis) × neighbor
    # marginal heat rate × load-shape, the SAME forecast-native construction
    # PJM/MISO use (reference_price_interface), specialized to the two ties — COI/
    # Path-66 proxies the Pacific-NW at Malin (gross-load shape), Path-46/WOR the
    # desert-SW at Palo Verde (net-load shape, so its midday price dips with the
    # solar glut). The level rides the forward Henry Hub trajectory and the shape
    # rides the neighbor's hourly tightness, so the seam reprices forward as
    # gas/solar move and stays live in a forecast year — where the measured hub
    # series is absent and caiso_per_hub_intertie goes inert. The measured hub LMP
    # stays the BACKCAST realization the formula is validated against (scripts/
    # compare_caiso_intertie_formula_vs_measured.py); nothing is pinned to it
    # (CLAUDE.md #10/#12). Supersedes the measured per-hub injector when on.
    # Requires caiso_per_hub_intertie (the per-hub legs it reprices). Carried by
    # transmission.inject_caiso_per_hub_reference_prices +
    # data.neighbor_price.caiso_hub_reference_price. Default off (byte-identical);
    # CAISO-only.
    caiso_corridor_atc_forward: bool = False  # Cap each CAISO per-hub corridor's
    # import-direction flow at a FORWARD ATC deliverability ceiling instead of the
    # measured p95 envelope: ATC(t) = corridor TTC × posted-ATC base fraction ×
    # clip(1 − k × solar_frac(t), floor, 1), where solar_frac is CISO solar /
    # demand (a forward driver that responds to a changed solar build). The solar
    # derate reproduces the structural midday deliverability collapse (the WECC
    # neighbors are themselves long on solar midday) off a capability limit, never
    # the measured corridor flow (CLAUDE.md #12). One-sided on the import
    # direction (export keeps the physical TTC); the LP still clears its merit
    # order below the ceiling. Supersedes the measured corridor cap
    # (caiso_corridor_flow_limit) when on. Requires caiso_per_hub_intertie. Carried
    # by transmission.forward_corridor_atc_envelope +
    # transmission.build_caiso_corridor_flow_groups +
    # eia_loader.caiso_solar_fraction. Default off (byte-identical); CAISO-only.
    caiso_reference_price_seam: bool = False  # Price BOTH legs of CAISO's two WECC
    # corridors with the forward-native reference-price seam (the PJM/MISO
    # INTERFACE_NEIGHBORS construction, INTERFACE_NEIGHBORS["CAISO"]): per corridor,
    # import + export flow tranches priced from (HH + gas_basis) × heat_rate ×
    # load-shape ± hurdle, with the CARB border carbon added to the import leg.
    # Replaces the measured per-hub OASIS ladder (caiso_per_hub_intertie): the
    # export leg clears at hub − hurdle (the price a WECC neighbor pays for CAISO's
    # midday solar surplus, fixing "model never exports") and the seam stays live
    # in every year (no OASIS gap, e.g. 2023). When on, the per-hub split + the
    # corridor ATC envelope (caiso_corridor_flow_limit) still apply — the
    # reference price sets the PRICE, the ATC envelope the FLOW LIMIT. Mutually
    # exclusive with caiso_per_hub_intertie (the runner skips the OASIS path when
    # this is on). Carried by transmission.build_reference_price_node (per-corridor
    # placement) + transmission.inject_reference_price_mc (carbon_price) +
    # neighbor_price load-shape (net/gross via CISO proxy). Default off
    # (byte-identical); CAISO-only.
    as_reserve_withholding: bool = False  # ERCOT backcast probe: remove the
    # hourly cleared DAM upward-AS MW (RegUp/RRS/ECRS/Non-Spin, built by
    # scripts/build_ercot_as_withholding.py from the NP3-911 reports) from
    # thermal headroom before the energy supply curve clears, so capacity sold
    # as AS cannot also offer energy. Default off (byte-identical baseline);
    # ERCOT-only. This is an UPPER BOUND — it books all AS to thermal, with no
    # storage/load split (the per-resource DAM Gen Resource Data needed for a
    # true split is unavailable across the backcast window), so it over-
    # withholds where batteries/load carry AS (most in the later years). Used
    # to gate whether a rigorous thermal-share build is worth the data pull.
    energy_reserve_coopt: bool = False  # Co-optimize energy and operating
    # reserve inside the LP (PJM and ERCOT). Adds a zonal reserve variable
    # sharing each eligible unit's headroom with energy (P + R <= pmax*avail), a
    # reserve-balance constraint at the requirement, and a published reserve
    # demand curve as priced shortfall steps so the reserve clearing price
    # emerges as the constraint dual and lifts the energy LMP endogenously.
    # Replaces the post-solve overlay when on (no double-count).
    #   * PJM — Primary Reserve at the structural 1.5 x most-severe single
    #     contingency (scarcity.pjm_primary_reserve_requirement) priced by the
    #     two-step ORDC curve (data/raw/_validation-source/pjm_ordc_curve.csv).
    #   * ERCOT — the VOLL-anchored ORDC reserve demand curve discretized into
    #     shortfall steps (scarcity.ercot_ordc_demand_steps): reserve-eligible
    #     thermal units part-load so the LP carries real spinning reserve instead
    #     of counting cold/idle slow-start capacity as responsive (the perfect-
    #     commitment headroom overstatement the post-solve overlay's online/
    #     offline split and the fitted RTORDPA offset both worked around). This is
    #     the RTC+B design (live 2025-12-05) and supersedes scarcity_pricing_
    #     enabled when on (the runner/calibration path skips the adder).
    # Structural, forecast-applicable (requirement + price both move with the
    # fleet); measured reserve series are backcast honesty gates only. GATED
    # CHANGE — it alters dispatch volumes (units part-load for reserve), so it is
    # NOT byte-identical and the volume calibration must be re-run before a
    # keeper. Default off. See docs/ordc-overlay.md (energy+reserve co-opt).
    miso_zonal_reserves: bool = False  # MISO co-opt: add LOCATIONAL (zonal)
    # operating-reserve families on top of the market-wide RBDC family, per the
    # NYISO nested-family template. MISO establishes Reserve Zones from the
    # IROL/RDT/SOL constraint set and enforces a minimum Zonal Operating
    # Reserve Requirement per zone (BPM-002 §3.3/§3.3.2); the zonal requirement
    # anchor is the pre-determined largest zonal contingency event (Chen et al.,
    # IEEE TPWRS, MISO STR design), i.e. the within-zone MSSC — fleet-derived
    # and forward-responsive, the zonal analogue of the market-wide MSSC basis.
    # Shortfalls price at the PUBLISHED Zonal Operating Reserve Demand Curve
    # (BPM-002 §5.2.1.2 / Tariff Schedule 28-A): $200/MWh for the last 20% of
    # the requirement, $1,100/MWh (energy offer cap $1,000 + contingency-
    # reserve offer cap $100) from 10-80%, and VOLL minus the zonal regulating
    # price below 10% (MISO_ZONAL_ORDC_STEPS, reserve_config.py). Default zone
    # set: MISO-South only (reserves deliverable across the RDT are limited —
    # scope doc §6); override via miso_zonal_reserve_zones. Zero parameters
    # fitted to the price residual. Requires energy_reserve_coopt. GATED
    # CHANGE — alters dispatch volumes; default off per the multi-ISO protocol.
    miso_zonal_reserve_zones: tuple | None = None  # Optional override of the
    # zonal reserve family zone set (model zone names). None -> the default
    # (MISO-South,) per scope §6; e.g. ("MISO-South", "MISO-East") adds the
    # Michigan-pocket family.
    miso_reserve_pergen: bool = False  # MISO: PER-ASSET reserve co-optimization
    # (dispatch._build_reserve_rows_pergen), the MISO analogue of
    # pjm_reserve_pergen — one R[r,t] column per (zone, fuel-class) pool of
    # reserve-eligible units with nonzero 10-min ramp, joint Σ P + R ≤
    # Σ pmax·availability per pool-hour, and R[r] ≤ Σ FleetArrays.ramp10
    # (RAMP10_FRAC_BY_GROUP × pmax, NREL/TP-5500-55588 App. H class ramp
    # rates) as a variable bound. Reserve then competes with energy on the
    # same marginal pool AND cleared reserve is capped at what the fleet can
    # physically deliver inside MISO's 10-minute contingency-reserve window
    # (BPM-002 §2.2: Spin + Supplemental must convert to energy in 10 min;
    # quick-start CT/oil count at full capacity, coal/CC/gas-ST at their
    # class ramp) — the deliverability structure that lets the market-wide
    # RBDC and the zonal §5.2.1.2 curve families genuinely run short instead
    # of always re-dispatching around the requirement (the miso-38 gate-4
    # perfect-foresight-headroom diagnosis). Class-level pooling everywhere
    # is the documented 15 GB memory tier (per-plant/per-tranche R columns
    # are memory-infeasible at MISO plant scale, miso-reserve-coopt.md);
    # same ramp physics at every tier, never a breakpoint/penalty change.
    # Zero parameters fitted to the price residual. Requires
    # energy_reserve_coopt + MISO; default off; GATED CHANGE (alters
    # dispatch volumes).
    miso_commitment_posture: bool = False  # MISO: pooled linear commitment-
    # posture lever (docs/multi-iso/miso-scarcity-posture-design-2026-07.md §A,
    # the G-25/DP-1 workstream). Per (zone × fuel-class) pergen pool p, adds a
    # continuous online-capacity variable U[p,t] ∈ [0, Σ pmax·availability]
    # with (i) joint headroom re-anchored to online capacity
    # (Σ P + R ≤ U instead of ≤ Σ cap), (ii) a CEMS-measured min-load coupling
    # Σ P ≥ mlf_p·U (mlf = the thermal_tranches committed_pct min-stable-when-
    # online percentile, capacity-weighted per pool; MIN_STABLE_PCT_PHYSICAL
    # WWSIS-2 class gap-fill for uncovered plants), (iii) a startup charge on
    # ΔU⁺ (SU ≥ U[t] − U[t−1], cyclic; $/MW from the NREL/SR-5500-55433 class
    # tables COMMITMENT_PARAMS_BY_FUEL / BIN_STARTUP_COST_PER_MW — re-timing
    # energy now pays a real start instead of the P1 zero-commitment-cost
    # relief the miso-39 gate-4 diagnosis measured at $4-23/MWh), and (iv) the
    # pergen reserve cap online-gated R ≤ ρ_p(t)·U (offline capacity
    # contributes no 10-minute ramp), so the published RBDC / zonal curve
    # families can genuinely run short. Eligibility gates on POOL PHYSICS,
    # never class tuples (rule 18): pools whose capacity-weighted class params
    # are fast-start (min-down ≤ 2 h AND startup < $30/MW — CT/oil) are
    # exempt (no U column; their offline capacity legitimately provides MISO
    # offline supplemental). NOT a floor: forces no energy (the min-load term
    # binds only capacity the LP itself keeps online — rule 17 window
    # deliberately none), carries no min_gen/D-2 mechanism id, and every
    # input is measured (CEMS mlf), published (NREL startup tables) or
    # physics (ramp10) — zero fitted parameters. Honesty gate: modeled online
    # headroom / cleared reserve vs the measured MISO ASM series
    # (data/raw/MISO-AS), NEVER the price-tail residual (rules 1/13). Min-run
    # /min-down rolling-window smoothing on U is deliberately deferred (the
    # startup charge carries the cycling economics; window rows are a
    # documented memory-gated follow-up, G-40). Requires energy_reserve_coopt
    # + miso_reserve_pergen; default off; GATED CHANGE (alters dispatch
    # volumes).
    caiso_scarcity_pricing: bool = False  # CAISO: enable the post-solve
    # power-balance scarcity price overlay (results.scarcity.caiso_scarcity_
    # overlay). Adds a probabilistic LOLP × (VOLL - λ) adder to the scored
    # energy prices using CAISO tariff-backed parameters (VOLL $2,000 per
    # Tariff §39.6.1; MCL 1,400 MW / Diablo Canyon MSSC; σ 2,500 MW / FRP
    # net-load uncertainty). Fires during evening net-load ramps and tight
    # conditions where the LP's perfect foresight clears without scarcity
    # rent the real market produces via penalty prices (Tariff §27.4.3.2,
    # BPM MO §6.6.4). Zero fitted parameters; forward-derivable (σ scales
    # with RE penetration, MCL tracks the largest contingency). Mutually
    # exclusive with caiso_reserve_coopt under energy_reserve_coopt
    # (rule 19 — one mechanism per phenomenon). CAISO-only; default off.
    caiso_lcr_commitment_credit: bool = False  # CAISO: credit the LCR
    # constraint dual (local-commitment value, $/MWh) in the P2 commitment
    # margin, analogous to the AS-revenue credit (as_value). CAISO pays
    # locally-committed units via BCR/CPM (Tariff §40.6); units in LCR areas
    # whose local-capacity row binds earn the uplift dual as additional
    # commitment revenue the hurdle would otherwise ignore, preventing P2
    # from decommitting runs that P1 correctly clears for local reliability.
    # Requires local_capacity_constraints=True. Default off; GATED CHANGE.
    caiso_reserve_coopt: bool = False  # CAISO: enable the per-generator
    # energy+reserve co-optimization (reserve_config._caiso_design, L-10). CAISO
    # is the only registered ISO whose reserve design was previously a hard
    # short-circuit in pipeline.kwargs.apply_reserve_coopt (issue #1492); this
    # flag lifts that short-circuit. When on (and energy_reserve_coopt on) CAISO
    # builds the PER-GENERATOR contingency-reserve co-opt: one R[r,t] column per
    # (zone, fuel-class) pool of reserve-eligible thermal units with nonzero
    # 10-min ramp, joint Σ P + R ≤ Σ pmax·availability per pool-hour, and
    # R[r] ≤ Σ FleetArrays.ramp10 as a variable bound (the MISO miso_reserve_
    # pergen structure). The requirement is BAL-002-WECC-3 Contingency Reserve
    # (max(most-severe single contingency via largest_single_contingency_mw,
    # CAISO_CONTINGENCY_FRAC × load), split half spinning / half non-spinning per
    # WECC-3 + DMM practice) and shortfalls price at the PUBLISHED CAISO tariff
    # §27.1.2.3.5 scarcity reserve demand curves (spinning 10% of the $1,000 soft
    # energy bid cap flat; non-spinning 50/60/70% at the 70/210 MW shortage
    # tiers) — the two products co-drawn on the shared pergen pool so their
    # shortfall duals sum into the energy LMP (§27.1.2.4 co-optimization). The
    # pergen ramp bound is what makes the requirement bite: a zone-aggregate
    # ungated family clears inertly from ~10 GW of idle evening CC headroom at
    # zero opportunity cost (the MISO lesson, issue #1492). Zero parameters
    # fitted to the price residual (tariff/NERC values only, rules 5/23).
    # DOCUMENTED GAPS (issue #1492, next increments — all would ADD reserve
    # supply, so this build over-states scarcity ex-ante, rule 1): storage
    # (dominant CAISO AS provider, not backed by the pergen builder), hydro
    # (RAMP10_FRAC has no hydro entry → ramp10 = 0), and Regulation Up/Down (no
    # forward-derivable requirement series). Requires energy_reserve_coopt +
    # CAISO; default off; GATED CHANGE (alters dispatch volumes). See
    # docs/multi-iso/caiso-reserve-coopt.md.
    caiso_commitment_posture: bool = False  # CAISO: the SAME pooled linear
    # commitment-posture lever as miso_commitment_posture (design note §A) on
    # the CAISO per-generator spin/non-spin co-opt pools — U[p,t] online
    # capacity with joint headroom re-anchored (Σ P + R ≤ U), CEMS-measured
    # min-load coupling Σ P ≥ mlf·U, NREL-table startup charge on ΔU⁺
    # (cyclic), and the online ramp gate R ≤ ρ(t)·U (offline capacity
    # contributes no 10-minute ramp). Fast-start pools exempt by POOL PHYSICS
    # (capacity-weighted min-down ≤ 2 h AND startup < $30/MW — rule 18, never
    # class tuples). CAISO rationale (caiso-70 FINDING, 2026-07-10): the
    # ungated pergen pool clears reserve from idle capacity at zero
    # opportunity cost, so no RTPD/RUC-like award→energy channel exists — the
    # posture U makes holding spin/non-spin cost a real start + min-load ride,
    # the forward-real mechanism by which CAISO's evening reserve procurement
    # commits gas (the measured evening CC deficit, +1.9/+1.2/+0.3 GW
    # 2023/24/25, docs/handoffs/caiso-belly-commitment-probe-2026-07.md). NOT
    # a floor: forces no exogenous energy (the min-load term binds only
    # capacity the LP itself brings online), carries no min_gen/D-2 mechanism
    # id, and every input is measured (CEMS mlf), published (NREL startup
    # tables, BAL-002-WECC-3 requirement, tariff §27.1.2.3.5 curves) or
    # physics (ramp10) — zero fitted parameters (rules 5/13/23). Read only by
    # reserve_config._caiso_design, so it requires energy_reserve_coopt +
    # caiso_reserve_coopt + CAISO; default off; GATED CHANGE (alters dispatch
    # volumes).
    caiso_locational_as_families: bool = False  # CAISO: add zone-masked
    # spin/non-spin reserve families whose hourly requirement is the MEASURED
    # CAISO OASIS AS_REQ regional MINIMUM south / north of Path 26 (AS_SP26 →
    # LA_BASIN/SDGE/SP15_rest, AS_NP26 → NP15/ZP26; data/raw/CAISO-AS,
    # data.caiso_as_requirements). The must-procure-within-region floor is a
    # locational, rule-13-admissible market-design input (regenerates forward
    # from the published BPM regional-requirement rules; zero fitted
    # parameters). Read only by reserve_config._caiso_design → requires
    # energy_reserve_coopt + caiso_reserve_coopt + CAISO; default off; GATED.
    # EX-ANTE INERT on the current 6-zone split topology (rule 1 / the caiso-70
    # arc): the SP26 minimum (~318 MW evening) is ~15× smaller than SoCal's own
    # un-postured in-region reserve supply (~4.8 GW), so it forces no SoCal gas
    # online — see results/calibration/FINDING-caiso71-locational-as-inert-
    # 2026-07-10.md. Shipped as correct structure (a real, forward-regenerable
    # locational requirement) that a materially larger local constraint (finer
    # LA-Basin pockets, RMR / local-capacity) could later populate; NOT in any
    # keeper.
    ercot_load_resource_reserve: bool = False  # ERCOT co-opt: credit the
    # measured Load-Resource responsive reserve (RRS-UFR, the under-frequency-
    # relay RRS that by protocol only Load Resources provide; ~0.8-0.9 GW) into
    # the reserve balance by lowering its RHS, so the co-opt LP stops pricing a
    # scarcity adder in non-scarce hours from omitting load-side reserve supply
    # (it already counts thermal headroom + storage). Built by
    # scripts/build_ercot_as_withholding.py (rrsufr_mw) for 2024/2025 and
    # scripts/build_ercot_as_2023.py for 2023. GATED — alters dispatch volumes,
    # re-run the volume calibration. Default off; ERCOT co-opt only.
    ercot_load_resource_reserve_from_year: int = 2023  # First weather year the
    # load-resource RRS-UFR credit applies to. Default 2023 = credit every
    # backcast year (the measured load reserve is real reserve supply the co-opt
    # LP omits, physically correct in every year). The knob exists as an optional
    # exclusion lever, NOT a default-off scope — UNLIKE the storage-AS credit,
    # because the two measured 2023 inputs interact: storage_as_commitment caps
    # battery dispatch by the MEASURED 2023 storage-AS (~1.25 GW, vs the old
    # 0.83 GW estimate) for ALL years, which over-tightens 2023 (uncredited
    # 49.8->58.4, tail over actual at 210/130 vs 181/104, run138). The measured
    # ~884 MW load credit corrects it — best 2023 monthly MAE 16.0->12.1, avg
    # 58.4->43.1 (run139). So with BOTH measured 2023 inputs + the run133/134
    # derate fix, crediting 2023 load is the "measured reserves + correct
    # derates" combination; leaving it off over-tightens. Settable via
    # --ercot-load-resource-reserve-from-year (raise it to exclude early years).
    ercot_storage_as_reserve: bool = False  # ERCOT co-opt: credit the measured
    # battery-provided AS (RegUp/RRS/ECRS, the storage column of the per-resource-
    # type 60-Day DAM AS awards; ~0.8 GW 2023 → ~2.8 GW 2025) back into the co-opt
    # reserve balance. storage_as_commitment subtracts this same MW from the
    # storage power cap, and the reserve block derives reserve room from that
    # reduced cap — so the committed battery AS is dropped from energy (correct)
    # AND from reserve supply (incorrect: it is held responsive reserve, in
    # ERCOT's RTOLCAP/RTOFFCAP). This credits it back, like the load-resource
    # credit, so the LP stops pricing a scarcity adder in non-scarce hours.
    # GUARDED on storage_as_commitment (off → the full cap is already reserve, no
    # credit). Self-targeting: negligible in 2023, largest in 2025 where the
    # residual co-opt overshoot lives. GATED — re-run the volume calibration.
    # Default off; ERCOT co-opt only.
    ercot_storage_as_reserve_from_year: int = 2025  # First weather year the
    # storage-AS reserve credit applies to. A modeling scope (not a measured
    # fact): the credit is physically correct every year, but 2023 and 2024 each
    # carry genuine scarcity the ORDC-only model can only reach THROUGH the
    # reserve over-fire, so crediting the battery AS removes the mechanism and
    # the model under-produces their real tails. 2023 is the documented
    # out-of-market year (tail = 47% of total $; ERCOT RTORDPA / ECRS
    # conservatism an ORDC model can't reproduce). 2024 has real tight-day
    # scarcity (53 h >$200, 8 h >$1000); a single-year probe crediting 2024
    # cooled avg 29.0->21.2 (actual 26.8), WORSENED MAE 10.5->12.7, and
    # collapsed the tail 49->7 h >$200 — confirmed empirically, not assumed from
    # "lower storage penetration". 2025 is the lone year whose residual is purely
    # the reserve-accounting over-fire (tail = 4% of $, reserves genuinely fat),
    # so the credit is gated to 2025+ (forecast years inherit it under the
    # reformed RTC+B fleet regime). NB: the reliability-deployment overlay does
    # NOT re-warm credited backcast years — it is an energy/congestion min-gen
    # floor (near-no-op on system LMP), not an ORDC scarcity-price mechanism.
    # Settable from the CLI via --ercot-storage-as-reserve-from-year (set to 2023
    # to probe a global credit). Going global is BLOCKED on a scarcity-price model:
    # the in-LP ORDC curve is hour-invariant so a re-derived LOLP can't self-target
    # 2024's tail, and 2023's tail is out-of-market (administrative, un-modelable by
    # any LOLP curve). See docs/ercot-run131-lmp-decomposition-2026-06.md
    # ("Global storage-AS credit — investigated, BLOCKED").
    ercot_ecrs_requirement: bool = False  # ERCOT co-opt: ADD the measured ECRS
    # procurement (~2 GW from 2023-06-10, ASPLANNP433 ECRS rows) to the reserve-
    # balance RHS. The co-opt models a single contingency-reserve product (ORDC
    # from ordc_mcl_mw + LOLP) and never grew when ECRS launched mid-2023, so it
    # holds too little reserve and under-prices the broad "tight-but-not-scarce"
    # mid-range across 2023-H2 and 2024/25 (the bimodal monthly-shape error: rare
    # VOLL spikes over, the moderate months under). This is the demand-side mirror
    # of the load/storage *supply* credits — it raises the absolute reserve level
    # the ORDC steps price at, lifting the marginal step in moderate-headroom
    # hours. Exogenous ERCOT-published quantity, NOT fitted to price; the real
    # June-2023 onset is carried by the data (2023-H1 has no ECRS rows → 0 MW), so
    # no start date is hard-coded. Default off; ERCOT co-opt only. GATED — watch
    # the tail (it tightens every active hour) and re-gate all years.
    ercot_ecrs_requirement_from_year: int = 2023  # First weather year the ECRS
    # requirement applies to (default 2023 = the launch year; the data zeroes the
    # pre-June-2023 hours itself).
    ercot_multiproduct_as_coopt: bool = False  # ERCOT: replace the single lumped
    # contingency-reserve co-opt product with the MULTI-PRODUCT AS stack — a
    # co-optimization demand curve per AS product (RegUp/RRS/ECRS/NonSpin,
    # ERCOT_AS_PRODUCTS), each additive and cascading (higher-quality substitutes
    # down). The binding product's reserve dual is the MCPC the measured DAM-AS
    # overlay reads, formed endogenously from the LP. Requires energy_reserve_coopt
    # (the multi-product builder is the ERCOT co-opt's multi-product mode) and is
    # paired with commitment_enabled for the phantom-headroom fix. Default off;
    # the forward analogue of ercot_dam_as_overlay (Finding 1 / G1). GATED.
    ercot_ecrs_conservative_deployment: bool = False  # ERCOT multi-product co-opt:
    # represent the PUBLISHED pre-reform ECRS deployment design as the ECRS demand
    # curve, year/date-keyed like the OBDRR048 floor. From ECRS go-live
    # (2023-06-10, market notice M-D050523-01; onset carried by the ASPLANNP433
    # data) through 2024-07-31, ERCOT had NO price-based ECRS release to SCED:
    # awarded ECRS was carved out of the SCED-dispatchable range (HASL) and
    # released only by manual/automatic reliability deployment (frequency
    # < 59.91 Hz, or 10-minute projected net-load insufficiency — ERCOT Ancillary
    # Services Study white paper, Sept 2024), which the IMM found "led to
    # artificial shortage pricing … doubled average energy prices between June and
    # December 2023" (>$12B; 2023 State of the Market Report §II.G,
    # recommendation 2023-3). Economically that is a reserve demand step AT THE
    # SYSTEM-WIDE OFFER CAP for the full requirement (withheld at any price below
    # the cap), so the ECRS family's shortfall steps become a single ordc_voll
    # step and the withheld supply raises the ENERGY dual endogenously in tight
    # hours. From 2024-08-01 (ERCOT operating-procedure change after the PUCT
    # rejected NPRR1224's $750 offer floor on 2024-07-25: release on a sustained
    # 40 MW/10-min power-balance violation, dispatched at the resources' own
    # offers — no administrative floor) the ECRS family reverts to the standing
    # VOLL-anchored ramp (the model's releasable-reserve representation). All
    # dates/values are published market design (docs/parameter-citations.md), no
    # parameter is fitted to a price residual. Default off; ERCOT multi-product
    # co-opt only. GATED.
    ercot_ordc_total_reserve: bool = False  # ERCOT multi-product co-opt: ALSO
    # enforce the lumped ORDC TOTAL-reserve demand curve (the published RTORPA
    # mechanism of the 2014-2025 ORDC regime, NPRR568 / PUCT project 37897 +
    # OBDRR048 floors) alongside the per-product AS families. Pre-RTC+B, ERCOT's
    # real-time scarcity price was set by the Operating Reserve Demand Curve on
    # TOTAL online reserves — RTSPP = SCED energy price + RTORPA(total reserves)
    # — while the DAM AS products (RegUp/RRS/ECRS/NonSpin) withheld their awarded
    # capacity from the SCED-dispatchable range (HASL). The faithful pre-RTC+B
    # stack is therefore BOTH: product-level withholding (the per-product
    # families, incl. the ECRS conservative-deployment step) AND the lumped
    # LOLP×VOLL total-reserve curve pricing the aggregate reserve level. This
    # flag appends one extra reserve-balance family (scarcity.
    # ercot_ordc_demand_steps — the same curve the single-product co-opt uses)
    # that draws on the SUM of every product's cleared reserve (reserve_class
    # -1 = all classes in dispatch._build_reserve_rows): an RRS/ECRS MW counts
    # toward the total exactly as RTOLCAP counts it, no capacity is
    # double-procured (the shared-headroom rows still bound P + ΣR ≤ cap), and
    # reserve held beyond the AS plans up to the ORDC span is valued at the
    # curve — the measured ~2× RTOLCAP-vs-AS-plan coverage the products alone
    # cannot express. Without it the multi-product swap silently DROPS the
    # published total-reserve mechanism and the deep scarcity tail collapses
    # (ercot27 probe: Aug-2023 −$88.7 vs keeper −$46, >$1000 hours 28 vs 61).
    # Published market design, zero fitted parameters. Default off; requires
    # energy_reserve_coopt + ercot_multiproduct_as_coopt. GATED.
    ercot_storage_as_product_credit: bool = False  # ERCOT multi-product co-opt,
    # measured storage path only: net the measured hourly battery AS award
    # (RegUp/RRS/ECRS cleared by batteries, the 60-Day DAM per-resource-type
    # series — the same measured input storage_as_commitment reserves out of
    # the storage power cap) pro-rata OFF the fast products' requirements.
    # Without it the products pull the batteries' awarded ~1.2-2.8 GW from
    # thermal headroom instead — capacity the real market never withheld from
    # SCED (the batteries carried it). The multi-product analogue of the
    # single-product ercot_storage_as_reserve requirement netting; same
    # from-year gate (ercot_storage_as_reserve_from_year), same measured
    # procurement quantity (never a price), penalty curves untouched. No-op
    # under the endogenous split (the battery is inside the co-opt there).
    # Default off; ERCOT multi-product co-opt only. GATED.
    ercot_as_critical_frac: float = 0.0  # Reserve level (as a fraction of each AS
    # product's peak requirement) at/below which its VOLL-anchored demand curve
    # hits the full AS offer cap. 0 (default) ramps the curve linearly from $0 at
    # the requirement to ordc_voll at zero reserve — the documented stand-in for
    # the published stepped ASDC. The allowed "tune the level on the right
    # structure" knob (CLAUDE.md #1), not a per-product price fit.
    ercot_as_n_ramp: int = 12  # Number of equal-width steps discretizing each AS
    # product's VOLL-anchored demand curve (more steps = smoother price-vs-reserve).
    ercot_as_aware_commitment: bool = False  # ERCOT: run a P2 commitment screen
    # that values a unit's AS revenue (reserve clearing price x reserve-eligible
    # headroom), not energy margin alone, when deciding which units stay online.
    # The energy-only screen decommits CC/CT that ERCOT actually keeps online FOR
    # AS, starving the reserve pool (the rejected energy-only P2 over-fire). Adding
    # the P1 reserve dual x headroom to the commitment hurdle keeps the units that
    # clear AS in a tight month committed, so the P2 shared-headroom RHS reflects
    # REALISTIC online headroom (idle slow-start capacity that earns neither energy
    # nor AS is decommitted out of it). That lets the multi-product co-opt form the
    # broad-month elevation endogenously instead of only the acute days (the
    # phantom-headroom gap, Finding 1 / G1). The AS value uses the model's OWN P1
    # balance-row dual (reserve_price_by_family), never the measured MCPC — no fit.
    # Requires energy_reserve_coopt + ercot_multiproduct_as_coopt; triggers a P2
    # pass even when commitment_enabled is off. Default off; ERCOT-only; GATED.
    ercot_as_adequacy_frac: float = 1.0  # AS-aware commitment: the coverage
    # multiple for the AS-adequacy floor (model.commitment.as_adequacy_commit).
    # After the AS-aware screen decommits the cold idle slow-start capacity, this
    # re-commits cheapest eligible units until committed online headroom covers
    # ercot_as_adequacy_frac x the MEASURED total AS requirement (ASPLANNP433), so
    # the co-opt cannot price a false VOLL-scale shortage the real market procured
    # around. 1.0 = cover the procured AS exactly (the grounded default); a coverage
    # multiple on the measured requirement, NOT a price-residual fit (CLAUDE.md #12).
    ercot_reserve_supply_cap: bool = False  # ERCOT: cap the multi-product co-opt's
    # cleared reserve to the MEASURED online responsive capability (RTOLCAP /
    # RTOFFCAP) instead of letting it draw on full-fleet headroom. The co-opt's
    # shared-headroom RHS counts every reserve-eligible thermal unit's full
    # capacity as reserve supply — including cold slow-start units a
    # perfect-foresight LP leaves idle but still counts as "available" — so
    # modeled reserve never tightens into the ~8-12 GW band where ERCOT's ORDC
    # adder actually fires (the phantom-headroom gap, Finding 1 / G1). This lever
    # re-scopes the reserve SUPPLY DEFINITION: it adds, per shared-headroom tier,
    # a system-wide row capping cleared reserve at the measured RTOLCAP (fast/
    # spinning tier) and RTOLCAP+RTOFFCAP (all tier incl. quick-start offline), so
    # modeled online reserve TRACKS the measured series. An exogenous physical/
    # market-rule distinction (online responsive vs full installed headroom), NOT
    # a price fit — the cap is the ERCOT-published reserve capability, never the
    # LMP or MCPC. Shapes the supply, not the commitment, so it sidesteps the
    # energy-vs-headroom redispatch problem of the AS-aware commitment screen.
    # Requires energy_reserve_coopt + ercot_multiproduct_as_coopt. Pair with the
    # published-ORDC curve (ordc_lolp_params_path / KEEPER_ORDC_TABLE), which
    # prices the P90-P99 band the supply re-scope finally reaches. Default off;
    # ERCOT-only; GATED.
    ercot_reserve_supply_cap_from_year: int = 2023  # First weather year the
    # RTOLCAP reserve-supply cap applies. A modeling default (the measured series
    # exists 2023+); the cap is physically correct in every ORDC-regime year. The
    # 2025 RTC+B go-live tail (post 2025-12-05) has no measured RTOLCAP and is
    # left uncapped (the cap series fills those hours with no constraint).
    ercot_reserve_supply_forward: bool = False  # ERCOT: source the RTOLCAP /
    # RTOFFCAP reserve-supply cap from the FORWARD FORMULA
    # (scarcity.ercot_rtolcap_forward_supply_cap_mw) instead of the measured
    # ercot_<year>_ordc_reserves_hourly.parquet — the WS-A forward analogue of the
    # last measured AS-path lever (docs/handoffs/ercot-rtolcap-forward-2026-07.md).
    # The cap is rebuilt from the model's own forecast net-load, the derived per-
    # class on-line headroom-realization shares (ERCOT_RTOLCAP_FWD_ONLINE_SHARE)
    # and the fleet's evolving reserve-eligible capacity, so it REGENERATES for a
    # forecast year and responds to changed conditions (rule #10). The seam is
    # mode-aware exactly like ercot_load_resource_reserve_credit_mw (G4):
    # **backcast with this flag OFF** returns the measured parquet byte-identical
    # (the validation target); **forecast OR this flag ON** returns the formula.
    # Setting it True in backcast is the run-163-style one-delta probe that proves
    # the formula carries the measured cap's role. Default off; ERCOT-only; GATED.
    # The formula never reads the LP's commitment/output state (anti-F3/F4) and
    # never a price (honesty gate: RTOLCAP MW quantity only).
    ercot_online_capacity_envelope: bool = False  # ERCOT: cap the multi-product
    # co-opt's shared-headroom ENERGY+RESERVE at the committed on-line CAPACITY
    # envelope — the G-22 commitment-thinness structure (docs/FINDING-ercot-
    # priceshape-2026-07.md §3 / structural conclusion #2). ercot_reserve_supply_cap
    # caps only the cleared RESERVE (Σ R ≤ RTOLCAP); the ENERGY side of the shared
    # headroom still draws on full-fleet capacity, so in the missed 2023 tail hours
    # the model retains ~3.2 GW of spare sub-$200 energy capacity BEYOND the
    # measured on-line capability (RTOLCAP) — the P1 perfect-commitment assumption
    # (every available MW serves energy instantly) plus the sub-2-day forced-outage
    # tail. That phantom spare keeps the energy dual at ~$45 where SCED cleared
    # $600+. This lever adds, per shared-headroom tier, a system-wide row
    # `Σ_{elig thermal} P + Σ_prod R ≤ online_cap_env(t)` where online_cap_env is
    # the CAMPD-measured committed on-line HSL (scarcity.
    # ercot_online_capacity_envelope_mw), so the model cannot dispatch OR reserve
    # more thermal than the real system had on-line. Unlike the flat reserve cap
    # the ENERGY term makes it CONDITION-RESPONSIVE: inert in slack hours (spare
    # capacity abundant), binding only in the high-energy tight hours where the
    # tail miss lives, tightening reserve into the ORDC band with NO offer-height
    # change (the price rises via the co-opt reserve-shortage channel, not via a
    # tuned offer — rule #1). The envelope is anchored to the measured RTOLCAP
    # series (online_cap_env − dispatch reproduces RTOLCAP level/band/coverage; the
    # anti-F1 identification gate, scripts/validate_ercot_online_capacity.py), never
    # to the price residual (rules #13/#14/#23). Requires energy_reserve_coopt +
    # ercot_multiproduct_as_coopt. Mode-aware net-load driver like
    # ercot_reserve_supply_forward (backcast reads its own forecast net-load, not
    # the LP's output). Default off; ERCOT-only; GATED.
    ercot_online_capacity_envelope_extreme: bool = False  # ERCOT: the
    # EXTREME-PEAK-RESOLVED variant of the on-line-capacity envelope — the filed
    # G-22 forward path after the ercot41 rejection (docs/handoffs/ercot-online-
    # capacity-envelope-2026-07.md §5). The base envelope reproduced measured
    # RTOLCAP in the binding regime (±2%) but its pooled decile-9 share median
    # under-stated the committable capacity in the top-2% net-load hours, so the
    # in-LP room collapsed (4.4/6.7 GW vs measured 8.0/11.1 in 2023/24) and the
    # ORDC over-fired (C3a PASS→FAIL, C3b 0.32→13.2). This variant keeps the
    # identical LP row (Σ elig thermal P + Σ prod R ≤ online_cap_env) and
    # replaces the envelope's driver resolution: (1) the share table is resolved
    # at 2-percentile grain inside the top decile (14 net-load bins,
    # scarcity.ercot_online_cap_extreme_bin — the measured CAMPD commitment
    # saturation the decile median collapsed), and (2) the scalar deliverability
    # becomes a per-bin profile fit to the measured thermal on-line HSL identity
    # (CAMPD gross + RTOLCAP − storage AS − LR credit), so the envelope
    # reproduces the measured on-line capability IN THE EXTREME TAIL, not just
    # the binding-regime mean (ERCOT_ONLINE_CAP_SHARE_EXTREME /
    # ERCOT_ONLINE_CAP_DELIV_PROFILE_EXTREME, derived by
    # scripts/derive_ercot_rtolcap_forward.py --emit online-cap-extreme-constant).
    # Every input is a measured MW quantity (rules #13/#14/#23, never a price);
    # identification gated by scripts/validate_ercot_online_capacity.py
    # --extreme (binding AND extreme-tail reproduction). Implies the envelope
    # machinery — do not set together with ercot_online_capacity_envelope (the
    # base flag keeps its frozen decile tables for ercot41 replay fidelity).
    # Default off; ERCOT-only; GATED.
    pjm_reserve_supply_cap: bool = False  # PJM analogue of ercot_reserve_supply_cap:
    # cap the energy+reserve co-opt's cleared reserve at the fleet's 10-min
    # DELIVERABLE ramp (FleetArrays.ramp10 = RAMP10_FRAC_BY_GROUP × pmax,
    # availability-scaled) instead of total eligible thermal headroom. The bare
    # PJM co-opt draws reserve on ~38 GW of full-fleet headroom vs the ~3.4 GW
    # Primary requirement, so the published vertical ORDC step never fires; this
    # re-scopes reserve SUPPLY to the deliverable slice (scarcity.
    # pjm_reserve_deliverable_supply_cap_mw). A physical deliverability definition
    # (ramp × cap), never fitted to the LMP residual. Requires energy_reserve_coopt
    # + PJM; default off; GATED.
    pjm_reserve_online_gated: bool = False  # PJM: gate co-opt reserve to ONLINE
    # (synchronized) capacity — the shared-headroom row becomes
    # R[z] − ρ·Σ_g P[g] ≤ 0, so an idle (P=0) unit backs no reserve and an online
    # unit backs ρ × its output. Pairs with pjm_reserve_supply_cap to reproduce
    # PJM's "online + 10-min-deliverable" reserve measure (the tightest defensible
    # supply definition, docs/multi-iso/pjm-reserve-ordc.md bind-gate). Requires
    # energy_reserve_coopt + PJM; default off; GATED.
    pjm_reserve_online_rho: float = 1.0  # online-headroom multiplier for the gated
    # PJM reserve class (~ fleet (pmax−pmin)/pmin near min load). Default 1.0 (the
    # dispatch._build_reserve_rows documented default); not fitted to a residual.
    pjm_reserve_commitment_scoped: bool = False  # PJM path B (G-20b): scope the
    # P1 reserve co-opt's supply to the COMMITMENT-DERIVED online fleet. An
    # fa_p2-style availability mask (the ERCOT AS-aware P2 mechanism that zeroes
    # idle slow-start capacity out of the reserve-headroom RHS, made P1-native
    # like the CAISO RA bridge): the P0 base-cost run pattern defines each
    # PLANT's online hours; non-fast-start reserve-eligible units (unit physics
    # gate, rule 18 — capacity-weighted plant min-down > 2 h or startup ≥
    # $30/MW, the same NREL/class-table thresholds as _posture_pool_params)
    # have availability zeroed in their plant's offline hours before the single
    # scored P1 solve, and the pjm_reserve_supply_cap deliverable ramp cap is
    # recomputed on the masked fleet (Σ ramp10 over ONLINE eligible units — the
    # pjm-reserve-ordc.md bind-gate "online + 10-min-deliverable" measure).
    # Offline gaps shorter than the plant's min-down are bridged online (a unit
    # physically cannot cycle off-and-back inside its min-down window).
    # Fast-start units are NEVER masked: an offline 10-min CT/oil peaker still
    # provides non-synchronized Primary reserve per Manual 11 sec 4.2.
    # Commitment state derived from the model's own P0 solve — forward-
    # regenerating, condition-responsive, no measured series and no fitted
    # parameter (rules 11/13). Published two-step ORDC stays as filed.
    # Mutually exclusive with pjm_reserve_online_gated (path A, the LP-linear
    # proxy this supersedes) and pjm_reserve_pergen (different supply layout).
    # Requires energy_reserve_coopt + PJM; default off; GATED
    # (pipeline.commitment.build_pjm_reserve_p1_prep).
    pjm_reserve_pergen: bool = False  # PJM: PER-GENERATOR reserve co-optimization
    # (dispatch._build_reserve_rows_pergen) — one R[r,t] column per (zone,
    # fuel-class) pool of reserve-eligible tranches with nonzero 10-min ramp,
    # joint Σ P + R ≤ Σ pmax·availability per pool-hour, R[r] ≤
    # Σ FleetArrays.ramp10 × availability (hourly; RAMP10_FRAC_BY_GROUP ×
    # pmax, NREL/TP-5500-55588 class ramp rates, measured-reconciled under
    # measured_ramp_capability) as a variable bound, and TWO measured balance
    # families per Manual 11 sec 4.2: the RTO Reserve Zone (measured
    # pr_req_mw) and the nested Mid-Atlantic/Dominion Reserve Subzone
    # (measured mad_pr_req_mw), each priced by the published two-step ORDC
    # ($850/$300/+190 MW, pjm_ordc_curve.csv). Reserve competes with energy
    # AT THE MARGINAL POOL, so the balance dual carries the sub-shortage
    # opportunity cost into the LMP endogenously — no overlay, no haircut, no
    # fitted params (docs/multi-iso/pjm-reserve-ordc.md Phase 2). Class-level
    # pooling everywhere is the documented 15 GB memory tier the miso-39
    # keeper proved feasible: the finer plant-in-MAD tier (257 R columns,
    # 2.25M joint rows) solved P0 at ~15.1 GB but OOM'd in the P1 warm-start
    # (2026-07-02 memtest) — a documented memory scope-down, never a
    # breakpoint/penalty change. Supersedes (mutually exclusive with)
    # pjm_reserve_supply_cap / pjm_reserve_online_gated, whose zone-aggregate
    # scoping the per-pool ramp10 bound replaces. Requires
    # energy_reserve_coopt + PJM; default off; GATED. Profile memory before
    # multi-year runs (CLAUDE.md #45).
    pjm_reserve_pergen_sync: bool = False  # PJM: per-gen OPPORTUNITY-COST reserve
    # co-optimization — the G-20b successor build (pjm-84/pjm-85 verdict:
    # reserve-supply scoping cannot price the $75-200 afternoon band; the band
    # is the SUB-SHORTAGE opportunity cost, needing reserve to compete with
    # energy on the same marginal unit AND an honest product split). On top of
    # pjm_reserve_pergen's (zone, fuel-class) pools this adds, per Manual 11
    # sec 4.2/4.3.3:
    # (i) the SYNCHRONIZED reserve sub-product as its own measured balance
    #     families (RTO sr_req_mw + nested MAD mad_sr_req_mw, PJM Data Miner
    #     reserve_market_results service=SR — the same rule-13 reliability-
    #     quantity basis as the Primary series) priced by the published
    #     Synchronized two-step ORDC rows (pjm_ordc_curve.csv, as filed —
    #     never forcing the Primary row to bind against a synchronized-only
    #     supply, the pjm-85 structural warning;
    # (ii) a per-pool product split of the R columns: a SYNC column servable
    #     only by ONLINE capacity's 10-min ramp, and a NON-SYNC column
    #     servable by OFFLINE fast-start ramp (Manual 11 sec 4.2: offline
    #     10-min CT/oil provides non-synchronized Primary, rule-18 physics
    #     gate) — both share the pool's joint P+R headroom row, so a reserve
    #     award of either product consumes the same iron; and
    # (iii) online scoping of the SYNC caps at the P0->P1 seam from the
    #     model's own P0 run pattern (the pjm-85 pjm_commitment_scoped plant-
    #     online derivation, min-down gap-bridged, applied to the RESERVE
    #     bounds only — energy availability is NOT masked, so P1's energy
    #     redispatch around the held reserve is exactly what prices the
    #     opportunity cost). P0 solves all-online (sync=full deliverable
    #     ramp, nonsync=0); P1 cold-solves on the masked caps
    #     (pipeline.commitment.build_pjm_reserve_p1_prep).
    # Measured requirement + published curve + physics ramp/commitment gates;
    # zero parameters fitted to the price residual (rules 1/11/13). Requires
    # energy_reserve_coopt + pjm_reserve_pergen + PJM; mutually exclusive with
    # pjm_reserve_commitment_scoped / pjm_reserve_online_gated /
    # pjm_commitment_posture (one mechanism per phenomenon, rule 19). Default
    # off; GATED CHANGE (alters dispatch volumes). Profile memory first
    # (CLAUDE.md #12/#45 — the R-column count doubles vs pjm_reserve_pergen).
    pjm_reserve_pergen_size_split: bool = False  # PJM: SIZE-SPLIT the pergen
    # pooling tier (reserve_config.pjm_pergen_structure's
    # size_split_mean_multiple, PJM_PERGEN_SIZE_SPLIT_MEAN_MULTIPLE=2.0x) —
    # the pjm-87 diagnosis (fleet-reconstruction probe, no re-solve): none of
    # the 4 balance rows (Primary/Synchronized x RTO/MAD) ever came close to
    # binding (8-14x supply margin at the tightest hour of 3 years); the
    # observed opportunity-cost duals came from the per-POOL joint headroom
    # row instead, and with 39 uniform (zone, fuel-class) pools the LP can
    # almost always source PJM's small measured requirement from SOME idle
    # pool even when one specific dominant plant is fully energy-loaded —
    # diluting the signal. This splits each base pool's plants whose capacity
    # exceeds the multiple x the pool's own mean plant capacity into
    # INDIVIDUAL pools (self-normalizing threshold, no absolute MW cutoff —
    # a granularity/LP-structure choice, not a fitted price parameter, rule
    # 5); smaller plants stay pooled together exactly as the base tier. A
    # deliberate middle ground between the base 39-pool tier and the memory-
    # infeasible full per-plant tier (407 pools / 814 sync-split R columns,
    # ~10x the base tier — beyond the documented 2026-07-02 P1 OOM precedent
    # at a smaller column count). Requires energy_reserve_coopt +
    # pjm_reserve_pergen; composes with pjm_reserve_pergen_sync (both use the
    # same pjm_pergen_structure call, so the sync/non-sync product split
    # rides the size-split pools unchanged). Default off; GATED CHANGE
    # (alters dispatch volumes AND the LP column/row count — profile memory
    # first, CLAUDE.md #12/#45).
    pjm_commitment_posture: bool = False  # PJM: the SAME pooled linear
    # commitment-posture lever as miso_commitment_posture (design note
    # docs/multi-iso/miso-scarcity-posture-design-2026-07.md §A; PJM port
    # docs/handoffs/pjm-commitment-posture-port-2026-07.md), ported not
    # forked — shared _posture_pool_params / dispatch U-SU columns. Per
    # non-fast-start (zone × fuel-class) pergen pool p, adds a continuous
    # online-capacity variable U[p,t] with (i) the joint headroom re-anchored
    # to online capacity (Σ P + R ≤ U), (ii) a CEMS-measured min-load coupling
    # Σ P ≥ mlf_p·U (committed_pct min-stable, WWSIS-2 gap-fill), (iii) a
    # startup charge on ΔU⁺ ($/MW from the NREL class tables), and (iv) the
    # pergen reserve cap online-gated R ≤ ramp10_p·U — so PJM's published
    # Manual-11 Primary/MAD ORDC families can run short in thin hours instead
    # of drawing on ~14 GW of free perfect-foresight online headroom (the
    # pjm-81 blocker: model online reserve never thins toward PJM's real
    # ~3 GW). Eligibility gates on POOL PHYSICS, never class tuples (rule 18):
    # fast-start pools (min-down ≤ 2 h AND startup < $30/MW — CT peakers/oil)
    # get no U column. NOT a floor: forces no energy, carries no D-2 id, every
    # input measured/published/physics — zero fitted parameters. Honesty gate:
    # modeled online headroom / cleared reserve vs the measured PJM reserve-
    # market series (data/raw/PJM-AS reserve_market_results), NEVER the price-
    # tail residual (rules 1/13; scripts/report_pjm_posture_gate.py). Requires
    # energy_reserve_coopt + pjm_reserve_pergen; default off; GATED CHANGE
    # (alters dispatch volumes). Profile memory before multi-year runs.
    measured_ramp_capability: bool = False  # Reconcile FleetArrays.ramp10's
    # class 10-minute fractions (RAMP10_FRAC_BY_GROUP/_BY_FUEL, the NREL/EIA
    # class-rate ESTIMATE) against the MEASURED per-plant ramp-capability
    # datatype (data/clean/ramp-capability, scripts/curate_ramp_capability.py):
    # EIA-860 Schedule 3.1 "Time from Cold Shutdown to Full Load" = "10M"
    # fast-start thermal capacity as a FLOOR, and the CAMPD CEMS maximum
    # observed 1-hour plant gross-load up-ramp (pooled 2023-2025, holdouts
    # excluded) as a CEILING on the class rate — the sustained-delivery bound
    # a 10-minute reserve award must honour (PJM Manual 11 primary reserve
    # ~30 min; MISO BPM-002 contingency reserve). Formula and citations:
    # market_sim.data.ramp_capability.measured_ramp10_frac. Plants without
    # coverage keep the class estimate (rule 14 fallback). Feeds the per-asset
    # reserve co-optimizations (pjm_reserve_pergen / miso_reserve_pergen);
    # inert unless a consumer reads ramp10. Measured physical capability,
    # forward-regenerating, never fitted to a residual (rules 13/24).
    # Default off; GATED (alters the co-opt deliverable-reserve bound).
    ercot_as_forward_requirement: bool = False  # ERCOT: set each multi-product AS
    # requirement (RegUp/RRS/ECRS/NonSpin) from a FORWARD formula of forecast
    # drivers — req_product(t) = f(net-load, ramp, VRE-share, net-load
    # forecast-error quantile, largest-contingency / load-ratio share) per ERCOT's
    # published AS Methodology — instead of reading the measured AS Plan
    # (ASPLANNP433). The forward analogue of the measured requirement (G3); the
    # measured series stays the backcast realization the formula is validated
    # against (modeled-vs-measured requirement MW, NOT a price fit). Default off →
    # the co-opt falls back to the measured ASPLANNP433 (the keeper/backcast
    # behaviour is unchanged). When on, the requirement responds to forward
    # conditions: more VRE → larger ramp/forecast-error → larger requirement.
    # Requires energy_reserve_coopt + ercot_multiproduct_as_coopt. The coefficients
    # are in constants.py (ERCOT_AS_*), calibrated to the published requirement MW,
    # never to a price. ERCOT-only; GATED. See
    # docs/ercot-as-forward-requirement-2026-06.md.
    as_reserve_formula: bool = False  # CAISO backcast: withhold a formula-based
    # upward operating-reserve requirement R(t) = max(MSSC, 0.067*load) +
    # 0.01*load (WECC MORC contingency + 1% regulation-up; see
    # fleet.caiso_operating_reserve_mw) from the gas top-of-merit headroom before
    # the energy curve clears, so capacity held as reserve cannot also offer
    # energy and the tight-hour / evening-tail price lifts. Default off
    # (byte-identical baseline); CAISO-only. A published-standard, no-fitted-
    # constants scaffold until OASIS cleared-AS data (AS_REQ/AS_RESULTS) can be
    # pulled to replace the formula with measured MW (outbound network is blocked
    # in the remote env). Lifts the evening tail only — it does NOT touch the
    # separately-handled midday floor.
    storage_as_commitment: bool = False  # ERCOT backcast: reserve the measured
    # hourly storage upward-AS MW (RegUp/RRS/ECRS cleared by batteries, from the
    # per-resource-type series) from the storage dispatch power cap, so capacity
    # committed to AS cannot also arbitrage energy. Default off (byte-identical);
    # ERCOT-only. Unlike thermal AS (tiny), storage carries ~2-3 GW of AS — a
    # large share of the battery fleet — and the energy-only LP otherwise dumps
    # the full fleet into the few highest-price hours. Reserves power, not SOC.
    ercot_storage_as_endogenous: bool = False  # ERCOT forward (G5): make the
    # battery CHOOSE energy vs upward-AS endogenously inside the multi-product
    # co-opt, REPLACING the measured-award reservation (storage_as_commitment +
    # ercot_storage_as_reserve). When on, the FULL battery power cap is handed to
    # the co-opt (no measured subtraction), so a unit's upward-reserve room
    # (cap − discharge + charge) competes with arbitrage on the same power cap in
    # the shared-headroom rows and is priced by the per-product AS demand curves
    # (reserve_price_by_family): the battery holds AS only when a product's
    # reserve dual exceeds its energy-arbitrage opportunity cost — the real bid.
    # The cleared storage AS is part of the capped reserve R, so it counts toward
    # the measured RTOLCAP online-responsive supply (which already includes online
    # batteries: RTOLCAP grows 13.5→16.7→19.1 GW in lockstep with the battery
    # fleet 2023→25), consistent with ercot_reserve_supply_cap. FORWARD RESPONSE:
    # as the fleet grows and AS saturates, the AS price falls and batteries tilt
    # back to energy — no measured award needed. The measured 60-Day DAM awards
    # stay ONLY as the backcast realization to validate the chosen split against,
    # never to pin it (CLAUDE.md #12). Default off (byte-identical); ERCOT
    # multi-product co-opt only. Mutually exclusive with storage_as_commitment
    # (the measured path); endogenous takes precedence and forces the measured
    # path off when both are set.
    # ENTRY RECONCILIATION (rule 19): when on, the storage new-entry screen
    # (model.storage.apply_storage_new_entry) credits the AS value DERIVED from
    # this solve's own reserve duals (ancillary.realized_storage_as_revenue_per_mw_yr)
    # and the exogenous as_revenue_per_mw_yr("storage") is suppressed — exactly
    # one mechanism prices storage AS. Requires energy_reserve_coopt (validated);
    # in forecast with ercot_multiproduct_as_coopt it also requires
    # ercot_as_forward_requirement (else the AS requirement is the zero
    # measured-plan fallback). See docs/storage-as-withholding-attribution-2026-07.md.
    ercot_thermal_as_endogenous: bool = False  # ERCOT forward: the thermal
    # analogue of ercot_storage_as_endogenous (rule 19). Under the reserve co-opt,
    # thermal AS is priced endogenously (reserve duals + the scarcity-lifted energy
    # margin the capacity screens already read off `prices`), so adding the
    # exogenous flat as_revenue_per_mw_yr in the retirement/new-entry screens
    # double-counts. When on, those screens instead credit the per-fuel AS value
    # DERIVED from this year's co-opt reserve duals
    # (ancillary.realized_thermal_as_revenue_per_mw_yr_by_fuel, built on
    # scarcity.ercot_as_aware_unit_value) and the exogenous rate is suppressed for
    # thermal — exactly one mechanism prices thermal AS. FORWARD RESPONSE: the
    # derived rate falls as the AS-eligible fleet grows and the reserve price
    # collapses; no measured award in the path (rule 13). Forecast-only (capacity
    # evolution never runs in backcast) and default off, so keepers are
    # byte-identical. Requires energy_reserve_coopt (validated); in forecast with
    # ercot_multiproduct_as_coopt it also requires ercot_as_forward_requirement
    # (else the AS requirement is the zero measured-plan fallback), same footguns
    # as the storage flag. See docs/storage-as-withholding-attribution-2026-07.md.
    ercot_storage_as_duration_gate: bool = False  # ERCOT (G5 follow-up): add the
    # published per-product AS SOC-duration requirements to the endogenous storage
    # split so a short-duration battery cannot sell long-duration AS on its full
    # power. When on (requires ercot_storage_as_endogenous), storage's upward AS
    # becomes an explicit per-zone reserve variable RS[c,z] (dispatch, appended
    # after the ORDC block) bounded by an LP-linear duration gate
    # Σ_c dur_c·RS[c,z] ≤ Σ_{s∈z} SOC[s] (durations = ERCOT_AS_PRODUCT_DURATION_H:
    # RegUp/RRS 1 h, ECRS 2 h, Non-Spin 4 h — ERCOT Nodal Protocols §3.17.3 ESR
    # SOC rule), alongside the existing power-cap competition. Fixes the endogenous
    # split's 2.1–2.4× over-hold vs the measured 60-Day DAM award (ercot32 root
    # cause 1). Cleared storage AS still counts under RTOLCAP (the supply cap) and
    # in the reserve balance. Default off (byte-identical); ERCOT multi-product
    # co-opt only. See docs/handoffs/ercot-storage-as-duration-gate-2026-07.md.
    negative_renewable_offers: bool = False  # Let curtailable wind/solar set a
    # sub-$0 marginal price in oversupply, reproducing CAISO's negative midday
    # LMPs (2024 RT da_pct: p5 -$10, p1 -$24, min -$41). California renewables
    # bid BELOW $0 to keep producing for their RPS/REC and federal-PTC value, so
    # in the spring-midday solar glut the marginal (curtailed) unit clears
    # negative. The model's wind/solar are availability-capped LP slices that
    # otherwise carry a $0 (solar) or -PTC (wind) offer and are never marginal,
    # so the model floors at $0 at best. When on, the wind/solar dispatch offer
    # is floored at the negative keep-running value below (so curtailing them is
    # the costly action and the LMP follows them negative). Default off
    # (byte-identical baseline); pushes the floor below the existing $0
    # export/curtailment sink. Only bites once the model is LONG midday (the RA
    # must-offer commitment floor workstream); develop/test in a forced-long
    # harness. ISO-agnostic mechanism, but targeted at CAISO.
    renewable_keep_running_value: float = 20.0  # $/MWh, the curtailable
    # renewable "keep-running" value used as the negative-offer floor when
    # negative_renewable_offers is on: a renewable on a PPA/REC will pay up to
    # this much to avoid being curtailed, so it bids -keep_running_value. One
    # defensible constant (not a per-hour shape). $20/MWh sits in the middle of
    # the cited range: CA RPS Bucket-1 (PCC1) REC prices have historically
    # cleared ~$10-25/MWh, and the federal §45 wind PTC is ~$28/MWh (2024,
    # inflation-adjusted). For wind the floor is the MORE-negative of this and
    # the PTC already on wind_mc (so the PTC, when active, dominates and there
    # is no double-count); for solar — which earns the ITC, not the PTC, so its
    # dispatch offer is $0 — this REC value is what carries it negative.

    caiso_solar_deliverability: bool = False  # CAISO Lever-D structural solar
    # local-deliverability derate. The reduced 3-zone CAISO topology collapses
    # the sub-area / distribution network where ~70% of CAISO solar curtailment
    # actually occurs (CAISO production-&-curtailment workbooks; docs/caiso-lever-
    # audit-2026-06.md, Lever D), so handed the uncurtailed HSL potential the LP
    # dispatches ~the full potential and re-curtails ~0. This caps the per-zone
    # solar dispatch upper bound at solar_pot × clip(1 − k × solar_frac(t), floor,
    # 1) — the solar-generation analogue of the accepted WECC corridor ATC derate
    # (transmission.forward_corridor_atc_envelope): as midday solar penetration
    # rises, the local network can evacuate a smaller share of the concentrated
    # solar and the surplus curtails. solar_frac(t) (eia_loader.caiso_solar_
    # fraction, CISO solar / demand) is a FORWARD driver that responds to a
    # changed solar build and load, never the measured curtailment outcome, so
    # the curtailed VOLUME emerges per-year from that year's own penetration and
    # potential (CLAUDE.md #1/#11). The LP still dispatches economically up to the
    # ceiling and curtails further below it under system oversupply. CAISO-only;
    # built by transmission.caiso_solar_deliverability_derate. Default off
    # (byte-identical); --no-caiso-solar-deliverability forces it off.
    caiso_solar_deliverability_k: float = 0.15  # local-deliverability sensitivity
    # to solar penetration. Derived as the reference-year midday curtailment rate
    # ÷ midday solar penetration: CAISO 2023/2024 midday curt/HSL = 0.073 ÷
    # solar_frac 0.441/0.499 → k ≈ 0.166 / 0.146, stable across both reference
    # years (so a structural sensitivity, not a per-year fit). 0.15 = the mid.
    # The target year's curtailed MW = solar_pot × k × solar_frac emerges from
    # that year's own forward penetration — never the target year's actuals.
    caiso_solar_deliverability_floor: float = 0.50  # floor on the derate so even
    # at extreme penetration (solar_frac → 1) the local network still evacuates
    # ≥ 50% of potential — a guard against an unphysical deep cut, not a fit knob.
    caiso_solar_endogenous_spill: bool = False  # CAISO midday price fix: give the
    # LP the FULL (underated) solar potential as the upper bound and let the LP
    # endogenously curtail solar via reduced dispatch in oversupply hours. When on,
    # the pre-LP solar CF ceiling derate (caiso_solar_deliverability) is SKIPPED —
    # the LP sees the full HSL potential, dispatches solar up to what the system
    # can absorb, and any excess potential is simply not dispatched (solar becomes
    # the marginal resource, setting the energy-balance dual to solar_mc ≈ $0 or
    # negative via the keep-running-value offer). This replaces the CF-ceiling
    # haircut that silently removed solar from the merit order and kept gas
    # marginal every midday hour. CAISO-only; overrides caiso_solar_deliverability
    # when True. The curtailment VOLUME emerges endogenously from LP economics
    # (CLAUDE.md #1: right mechanism, not fitted level).
    caiso_solar_cap_at_delivered: bool = False  # INTERIM STOPGAP (Lever-D P6),
    # DEFAULT-OFF DIAGNOSTIC ONLY. Caps the backcast solar dispatch upper bound at
    # the measured EIA-930 delivered solar profile (the "delivered-not-potential"
    # item), so the model cannot over-run delivered. This PINS solar to the
    # measured outcome — it has NO forward analogue and must NEVER be enabled in a
    # keeper or quoted as forecast skill (CLAUDE.md #11). It exists only as an A/B
    # reference for the structural caiso_solar_deliverability derate above; enable
    # with --caiso-solar-cap-at-delivered for a diagnostic probe.

    # Tier 3 (calibration)
    renewable_cf_adjustment: float = 1.0
    basis_differential_factor: float = 1.0
    wefor_multiplier: float = 1.0  # Global scale on every thermal class's
    # forced-outage rate (WEFOR) before the seasonal summer/shoulder/winter
    # split, so the seasonal *shape* is preserved while the outage magnitude
    # is lightened (or raised). < 1.0 raises availability everywhere — most
    # in the shoulder months, where WEFOR is heaviest after the summer-peak
    # redistribution. Does not touch the planned-outage (POF) or
    # weather/performance derate terms.
    maintenance_monthly_shape: bool = True  # FORECAST-mode planned-maintenance
    # shaping. When True (default) and mode == "forecast", the flat shoulder-POF
    # heuristic (POF smeared evenly across _CC_SHOULDER_MONTHS) is replaced by
    # the historically-derived MAINTENANCE_MONTHLY_SHAPE (per-group 12-month
    # weights learned from CAMPD/GADS outage timing). The group's annual POF
    # budget is conserved exactly (the shape has a month-weighted mean of 1) —
    # only its seasonal distribution is sharpened (peaks Apr/Oct-Nov, ~0 at the
    # Jul/Aug summer peak). False restores the legacy flat shoulder block.
    # Backcast runs are unaffected either way (POF there comes from the historic
    # overlay / coal_drop_pof path). Spec section 1.7 roadmap item.
    wefor_residual: float | None = None  # Historic-backcast WEFOR floor for
    # the overlay-covered thermal classes (coal + CC_REGULAR/CC_CHP/ST_GAS/
    # ST_CHP). The CAMPD historic overlay + unit-level derate already carry
    # every >= 5-day outage for those classes, so the full statistical WEFOR
    # (5% CC, 21% ST_GAS, 12% coal base + age escalation) double-counts them.
    # When set (and outage_source == "historic"), each covered unit's WEFOR
    # is capped at this short-outage residual — the < 5-day events below the
    # overlay's detector floor, ~1-2%. None (default) keeps the full
    # statistical WEFOR everywhere (forecast runs, ERCOT, and any backcast
    # that has not been re-balanced on the corrected availability). CTs have
    # no overlay coverage and are never affected.
    td_loss_factor: float = 0.0  # Gross-up of EIA-930 demand, as a fraction.
    # EIA-930 "Demand" is generation-side: Demand + Total Interchange = Net
    # Generation (verified to <0.01 TWh for ERCOT 2023/2024), so the demand
    # target already equals net generation and needs no gross-up to match the
    # fleet's actual output. The former 0.058 came from eGRID net generation
    # (472.9 TWh) / EIA-930 demand (446.8 TWh) − 1, but eGRID's total includes
    # ~28 TWh of behind-the-meter CHP self-supply that EIA-930 grid demand
    # excludes — so that ratio was mostly mislabeled BTM CHP, not T&D losses,
    # and inflated grid generation by the BTM amount. Applied as:
    # demand = raw_demand × (1 + factor).
    # NYISO stays 0.0 too, now Gold-Book-confirmed (2026-06): NYISO Gold Book
    # Table I-2 actual NYCA Annual Energy (Note 1: "include transmission &
    # distribution losses") = 147,050 GWh (2023) = the EIA-930 NYIS demand the
    # model serves, so that demand is ALREADY the loss-inclusive net-energy-for-
    # load — a gross-up would double-count. See
    # docs/nyiso-td-loss-resolution-2026-06.md.
    strict_demand_profile: bool = False  # When True, threaded through to
    # data.eia_loader.load_demand/load_demand_meta: raise
    # DemandProfileNotRepairedError instead of silently falling back to the
    # corrupted legacy eia_demand_profiles/eia_demand_meta series when the
    # repaired demand-profile clean partition is missing for an (iso, year)
    # the repair covers. Defaults to False (warn-and-fall-back, byte-identical
    # to the pre-existing behavior).
    vintage_capacity_ramp: bool = True  # When True, renewable capacity for a
    # calibration year ramps month-by-month from each plant's commercial
    # operation date (EIA-860 Operating Month/Year). When False, flat
    # year-end capacity is used (pre-calibration behavior).
    storage_vintage_ramp: bool = False  # When True, the EIA-860 backcast
    # battery fleet's dispatch power/energy caps ramp month-by-month from
    # each unit's COD (EIA-860 Operating Month/Year) — the storage analogue
    # of vintage_capacity_ramp. First-order for CAISO, which commissioned
    # 3.0 GW during 2023 and 3.6 GW during 2024 (EIA-860 energy-storage
    # schedule), so a flat year-end fleet overstates the spring/summer
    # battery capability by 1.5-2 GW. Off by default: the ERCOT/PJM
    # backcasts were calibrated against flat year-end fleets and stay
    # unchanged until recalibrated (CAISO prompt pack E2).
    # Tier 3 (calibration) — Coal take-or-pay supply-curve tranches
    # Each coal bin is split into three tranches modeling its take-or-pay
    # fuel contract: a fraction of capacity at a fraction of fuel passthrough.
    # Tranche 1 (contracted volume) bids at VOM only — its fuel is sunk;
    # higher tranches bid progressively more of full fuel cost. The fractions
    # need not sum to 1.0 but normally do. The take-or-pay STRUCTURE is a real
    # coal-contract mechanism (rule #1); the specific step sizes below were
    # calibrated to EIA-930 2023-2024 hourly ERCOT coal dispatch and eGRID
    # 2023/2024 actuals — R6 DOCUMENT-AND-KEEP (owner-sanctioned offer-curve
    # scope; docs/handoffs/scalar-remediation-plan-2026-07.md C-8), tracked
    # residual-identified in the DOF ledger (open: re-ground the step sizes on
    # EIA-923 fuel-cost-dispersion/contract-share data instead of the
    # backcast fit; issue #1336).
    coal_tranche_1_frac: float = 0.30  # Take-or-pay capacity fraction
    coal_tranche_1_fuel_passthrough: float = 0.00  # VOM only — fuel sunk
    coal_tranche_2_frac: float = 0.25  # Partially contracted
    coal_tranche_2_fuel_passthrough: float = 0.35
    coal_tranche_3_frac: float = 0.45  # Economic dispatch
    coal_tranche_3_fuel_passthrough: float = 1.00  # Full fuel cost

    # Tier 3 (calibration) — CAMPD coal pricing. Plant-specific coal
    # delivered fuel cost is a per-year trajectory built in fuel.py
    # (COAL_PRICE_LIGNITE_BY_YEAR / COAL_PRICE_PRB_BY_YEAR). PRB plants
    # have rail/coal take-or-pay contracts; that sunk-cost share now flows
    # through the per-bin _mustrun tranche (which bids at VOM only), so
    # the default delivered-cost passthrough on the remaining tranches is
    # 1.0. Override below 1.0 only to study a flat PRB delivered-cost
    # discount on top of the must-run staircase.
    coal_prb_contract_passthrough: float = 1.00

    # Tier 3 (calibration) — CAMPD coal committed-tranche price-taking.
    # A PRB coal unit that is online price-takes across all the capacity it
    # is running, not just its committed slice: it bids to clear rather than
    # on full marginal cost. This passes only ``coal_prb_passthrough`` of the
    # fuel cost into the bid (VOM + carbon + NOx are always charged) for every
    # PRB tranche above must-run (committed, economic, peaking), so baseloaded
    # PRB clears the merit order instead of being priced out by cheap gas.
    # Mine-mouth lignite is left at full cost. 1.0 = full fuel cost (off).
    coal_prb_passthrough: float = 1.00

    # Tier 3 (calibration) — gas-keyed coal passthrough sigmoids, ONE
    # INDEPENDENTLY TUNABLE LOGISTIC PER COAL SUPPLY CHAIN. Each supply
    # class ("prb" rail take-or-pay, "subbituminous" derived-rank,
    # "bituminous" Appalachian/Illinois-Basin, "lignite" mine-mouth) has its
    # own economics — basin, rank, mine-mouth vs rail, contract structure —
    # so each gets its own sigmoid, and the sigmoids are REGION-DEPENDENT:
    # the floor/ceil/gas_mid/gas_slope fields below default to None, which
    # resolves from COAL_SIGMOID_DEFAULTS[(iso, supply)] (the per-ISO tuned
    # curves). Setting a field explicitly (CLI tuning flags) overrides the
    # table; an ISO/supply with neither a table entry nor explicit fields
    # gets NO sigmoid (the flat fallback), so a curve tuned in one ISO can
    # never silently apply to another ISO's coal fleet. See
    # fuel.coal_passthrough_series.
    #
    # When a sigmoid is on, every above-must-run tranche of that supply
    # passes a logistic of the monthly delivered gas price instead of its
    # flat passthrough: a fuel discount when gas is cheap (coal holds its
    # baseload against cheap gas CC) and a markup > 1.0 when gas is dear (so
    # it doesn't over-run). Keyed off the measured EIA-923 ISO-month gas
    # series when gas_monthly_actuals is on, else the shaped trajectory.
    coal_prb_passthrough_sigmoid: bool = False
    coal_prb_passthrough_floor: float | None = None
    coal_prb_passthrough_ceil: float | None = None
    coal_prb_passthrough_gas_mid: float | None = None
    coal_prb_passthrough_gas_slope: float | None = None

    # Tier 3 (calibration) — tiered PRB passthrough (ERCOT). When True, PRB
    # plants whose per-plant must-run floor is <= coal_prb_follower_mustrun_max
    # use a SEPARATE follower-tier sigmoid (coal_prb_follower_*, the
    # "prb_follower" supply key in COAL_SIGMOID_DEFAULTS); the rest use the
    # baseload sigmoid above. The low-floor units are load-followers (they
    # cycle), not baseload price-takers, so they can want a different curve.
    # Requires coal_prb_passthrough_sigmoid and coal_mustrun_per_plant.
    coal_prb_passthrough_tiered: bool = False
    coal_prb_follower_mustrun_max: float = 25.0  # MR% <= this -> follower tier
    coal_prb_follower_floor: float | None = None
    coal_prb_follower_ceil: float | None = None
    coal_prb_follower_gas_mid: float | None = None
    coal_prb_follower_gas_slope: float | None = None

    # Subbituminous: the derived EIA-923 rank tag. Historically aliased onto
    # the PRB sigmoid (plant_taxonomy routes both to COAL_PRB), but a
    # sub-bituminous plant outside ERCOT does not share ERCOT PRB's rail
    # contract economics — each ISO's subbit fleet gets its own curve
    # (e.g. PJM's two PRB-by-rail plants delivered into PJM conditions).
    coal_sub_passthrough_sigmoid: bool = False
    coal_sub_passthrough_floor: float | None = None
    coal_sub_passthrough_ceil: float | None = None
    coal_sub_passthrough_gas_mid: float | None = None
    coal_sub_passthrough_gas_slope: float | None = None

    # Bituminous (the PJM coal fleet's dominant rank).
    coal_bit_passthrough_sigmoid: bool = False
    coal_bit_passthrough_floor: float | None = None
    coal_bit_passthrough_ceil: float | None = None
    coal_bit_passthrough_gas_mid: float | None = None
    coal_bit_passthrough_gas_slope: float | None = None

    # Bituminous spot-coal marginal treatment (PJM): unlike PRB/lignite
    # mine-mouth take-or-pay, PJM bituminous buys coal on spot/market terms, so
    # it is the marginal, price-responsive swing fuel — it should bid near full
    # delivered cost and back down when gas is cheap, not run as discounted
    # baseload. When set, a bituminous-ranked coal plant's per-plant CAMPD
    # must-run floor is zeroed in bins_to_fleet, so all of its capacity enters
    # the rising offer-curve tranches (committed/econ/peak) with Pmin=0 and bids
    # full delivered cost (pair with coal_bit_passthrough_floor=1.0). PRB,
    # lignite and waste coal keep their take-or-pay must-run floors. This is the
    # contract-physics structure, not a coal-MWh residual tune (CLAUDE.md
    # #1/#11): a faithful model holds bit up only when it is economic, so any
    # under-run it then shows is a price-formation signal, not a coal fault.
    coal_bit_dispatchable: bool = False

    # Take-or-pay from data (all coal ranks): replace the hardcoded "must-run
    # tranche is 100% sunk" assumption with the MEASURED contracted share of
    # each plant's EIA-923 Schedule-5 fuel receipts (Purchase Type C/NC/T vs
    # spot S). When set, a coal must-run tranche passes 1 - contract_share of
    # its fuel into the bid (only the contracted tonnage is sunk; the spot
    # remainder bids full delivered cost), per
    # scripts/derive_coal_takeorpay.py → fleet.coal_takeorpay_share. This is
    # the physically-honest, forward-reproducible version of the calibrated
    # gas-keyed passthrough discount (CLAUDE.md #11): a plant with no
    # classifiable Purchase Type keeps the default 100%-sunk treatment. Default
    # off (the keeper's behaviour is unchanged) until the per-ISO
    # coal_takeorpay_<ISO>.csv artifact is derived and the run re-solved.
    coal_takeorpay_from_data: bool = False

    # Online-Pmin coal must-run floor (rebuild step 2): size the coal must-run
    # (cheap, fuel-sunk) tranche from the measured *online* minimum stable load
    # — the net MW the unit holds 95% of its online time, as a fraction of
    # nameplate (thermal_tranches_<ISO>.csv ``mustrun_online_pct``) — instead of
    # the all-hours available-CF P5 (``mustrun_pct``), which reads ~2x high for
    # an always-online unit (its all-hours P5 sits in its normal operating band
    # and the outage-derate denominator inflates the available-CF). In the
    # energy-only LP the coal ``_mustrun`` tranche has Pmin=0, so it is not a
    # forced floor but the SIZE of the cheap (sunk-fuel) bid band; shrinking it
    # to the true online Pmin moves coal capacity into the full-delivered-cost
    # rising tranches, so coal price-follows (backs down in cheap hours) instead
    # of baseloading the whole fleet under gas. Pairs with
    # coal_takeorpay_from_data (step 1: the cheap band's sunk fuel share). A
    # forward-reproducible CEMS quantity (CLAUDE.md #11). Default off (keeper
    # unchanged) until the artifact carries the column and the run is re-solved;
    # plants whose artifact predates the column keep ``mustrun_pct``. See
    # docs/multi-iso/pjm-coal-operations-firstprinciples-2026-06.md (Thread D).
    coal_mustrun_online_pmin: bool = False

    # Intermediate-duty CT split (MISO calibration). EIA-860 confirms MISO's
    # high-CF CT_PEAKER units are genuine simple-cycle GT/IC (not mislabeled
    # combined cycle), so the classification is correct — but ~half the fleet
    # runs intermediate / near-baseload (measured CAMPD median CF >=
    # ``ct_intermediate_cf_threshold``) rather than as true peakers. The single
    # steep CT_PEAKER offer curve (a committed-band start-cost hurdle) prices
    # their always-on energy above the CC fleet, so they never clear and
    # CC_REGULAR over-runs (the CT_PEAKER under / CC over C1 miss). When set,
    # that cohort (fleet.ct_intermediate_plants) is routed to the flatter
    # ``CT_INTERMEDIATE`` offer curve so its energy clears. The median-CF cohort
    # is a forward-reproducible duty-role signal assigning an offer *shape* (not
    # a pin to measured output), admissible on the same basis as
    # ST_GAS_PEAKER_PLANTS. Default off (keeper unchanged) until re-solved.
    ct_intermediate_split: bool = False
    ct_intermediate_cf_threshold: float = 50.0

    # ST_GAS analogue of ct_intermediate_split. MISO's legacy gas-steam fleet
    # (Harding Street, Ames, Nine Mile Point, Lewis Creek, Sabine, ...) runs
    # intermediate/near-baseload (measured CAMPD median CF >=
    # ``st_gas_intermediate_cf_threshold``), not as peakers, but inherits the
    # ERCOT-fitted steep ST_GAS offer curve (steep econ_high + 15% peaking band)
    # that prices most of each unit above merit, so the model under-runs them
    # (the Moselle / Lewis Creek under-run). When set, that cohort
    # (fleet.st_gas_intermediate_plants) is routed to the flatter
    # ``ST_GAS_INTERMEDIATE`` offer curve so its sustained energy clears. The
    # median-CF cohort assigns an offer *shape* (not a pin to measured output),
    # admissible on the same basis as ct_intermediate_split / ST_GAS_PEAKER_PLANTS.
    # Default off (prior keeper unchanged) until re-solved.
    st_gas_intermediate_split: bool = False
    st_gas_intermediate_cf_threshold: float = 50.0

    # CC_REGULAR analogue of ct_intermediate_split / st_gas_intermediate_split.
    # MISO's entire combined-cycle fleet runs intermediate/baseload (measured
    # CAMPD median CF 50-150 %, mean ~90 %), but inherits the CC_REGULAR offer
    # curve fit to ERCOT's duct-fire-heavy 2x1 peaker CCs (Colorado Bend II /
    # Wolf Hollow II): a rising start-cost-amortized econ ramp (econ_high 1.27)
    # that over-prices the upper operating range of an already-committed baseload
    # CC, whose incremental energy is near its flat full-load heat rate
    # (~0.93x average), so the upper econ tranches sit above the clearing price
    # and the model under-runs the CC fleet (the MISO 2023/2024 gas-CC under-run,
    # -24 to -28 TWh vs EIA-923). When set, that cohort
    # (fleet.cc_intermediate_plants) is routed to the flatter ``CC_INTERMEDIATE``
    # offer curve, which flattens the econ ramp to the measured near-baseload
    # incremental cost while KEEPING the physically-real duct-burner peak band
    # (only the operating-range ramp is corrected, never the ~2.25x duct-fire
    # peak). The median-CF cohort assigns an offer *shape* (not a pin to measured
    # output), admissible on the same basis as ct_intermediate_split /
    # st_gas_intermediate_split. Default off (prior keeper unchanged) until
    # re-solved.
    cc_intermediate_split: bool = False
    cc_intermediate_cf_threshold: float = 50.0

    # ISO-gated gas-steam startup amortization. The ST_GAS startup cost +
    # min-run/min-down (constants.ST_GAS_COMMITMENT_PARAMS) are only fed into the
    # P1 monthly bid markup when this is set, so a stop-start costs more than
    # idling and the intermediate steam fleet drags rather than cycling like a
    # peaker. Default off → ERCOT and every prior keeper stay byte-identical.
    gas_st_startup_cost: bool = False

    # Fast-start tranche pricing (ISO-NE Order 825 analogue): when set, the
    # FAST-START-capable tranches of the gas CAMPD bins carry the bin's NREL
    # startup cost (fleet.BIN_STARTUP_COST_PER_MW, NREL/SR-5500-55433) exactly
    # as the committed tranche already does, so compute_monthly_markup
    # amortizes each tranche's own P0 run lengths into its P1 bid. Scope
    # follows ISO-NE fast-start pricing eligibility (start + notification
    # <= ~30 min): CT_PEAKER/CT_CHP econ+peak tranches (a peaker's upper
    # blocks are additional quick-start units) and the CC_REGULAR/CC_CHP
    # duct-burner/quick-response PEAK band only. A big CC's econ blocks are
    # deliberately excluded — block-loading a committed CC is not a fast
    # start, and its start costs settle as NCPC uplift, not in the LMP. The
    # resulting offer component is fuel-price-INVARIANT ($/MWh from
    # $/MW-start over run hours), which the heat-rate-multiplier
    # parameterization cannot express: a mult-only curve over-prices high-gas
    # winter months and under-prices cheap-gas summer evening peaks
    # simultaneously (the NEISO 2024 C3b Jan/Feb +$9-10 vs Jul/Aug -$10-11
    # signature). Dynamics-correct: a peak block run 4 evening hours bids
    # +startup/4 per MWh; a block marginal around the clock in a cold month
    # bids +startup/run≈0. No new constants — reuses the cited NREL startup
    # table and the existing P0 run-length machinery. Default off → every
    # prior keeper stays byte-identical.
    tranche_startup_amortization: bool = False

    # Fast-start amortization v3 — MEASURED run-length basis (requires
    # ``tranche_startup_amortization``). v2 amortizes each fast-start tranche's
    # NREL start cost over the tranche's own P0 run lengths, which is circular
    # when the offer level itself is wrong: offers too cheap -> P0 runs the CTs
    # in long blocks -> per-MWh amortized start cost ~0 -> the lever
    # self-disables (the nyiso-44 probe finding: CT_PEAKER moved only
    # 4.90 -> 4.75 TWh vs 2.13 actual). When set, the simple-cycle CT tranches
    # (CT_PEAKER / CT_CHP) instead amortize over the unit's CAMPD-MEASURED
    # median start-to-stop run length (scripts/derive_campd_ct_run_lengths.py:
    # consecutive grossLoad-online hours from the unit-level CAMPD extracts,
    # pooled 2023-2025, ISO-class median fallback for plants without CEMS).
    # Basis choice (documented per the derivation): the measured median is the
    # EX-ANTE expected-run horizon real GT offers amortize start recovery over
    # (the NYISO/ISO-NE fast-start pricing convention); the endogenous P0 run
    # length may only SHORTEN the horizon (a unit the model itself starts for
    # 2 h genuinely pays its start over 2 h), never lengthen it beyond the
    # measured basis — markup = startup / max(1, min(P0_month_avg_run,
    # measured_median)), a month with no P0 runs uses the measured median
    # outright. This removes the self-disabling circularity while keeping the
    # month-resolved dynamics. CC peak (duct-burner) bands keep the v2 P0
    # basis — a duct burner's "run" is not a CEMS start-to-stop block, so the
    # measured statistic does not describe it. The measured run length is a
    # rule-#12-admissible measured market-behaviour parameter (same class as
    # the CAMPD committed shares / min-stable loads): it regenerates from the
    # CAMPD pipeline for any new vintage and re-derives only when its source
    # data updates (rule #23), never from a residual. Default off -> every
    # prior keeper stays byte-identical.
    tranche_startup_measured_runs: bool = False

    # NYSDEC 6 NYCRR Subpart 227-3 "peaker rule" availability overlay
    # (NYISO). The regulation caps ozone-season (May 1 - Sep 30) NOx from
    # simple-cycle turbines in two phases (2023-05-01 / 2025-05-01); units
    # whose compliance plan is ozone-season shutdown or reliability-only
    # operation are unavailable to the energy market inside the window. When
    # set, the curated unit-level compliance schedule
    # (data/raw/reference/nysdec-227-3-peaker-compliance.csv — NYISO Gold Book
    # Tables IV-3..IV-6, 2023-2025 vintages, per-unit citations in the CSV)
    # zeroes/derates each restricted unit's availability inside its effective
    # ozone windows. AVAILABILITY ONLY, never an offer or price change — the
    # same rule-#12 admissibility class as the CAMPD unit-outage windows: an
    # exogenous regulatory availability event with a forward story (the
    # schedule extends through the 2030 NYPA phase-out) that regenerates from
    # the regulation, not from observed CF. Units the NYISO STAR process
    # designated to remain in operation past the compliance date (Gowanus 2&3
    # / Narrows 1&2 barges, to May 2027) are carried in the CSV but NOT
    # restricted — the designation is part of the same regulatory record.
    # Default off.
    nysdec_peaker_rule_availability: bool = False

    # ISO-gated gas-steam forced-outage base override. The global ST_GAS WEFOR
    # base (constants.THERMAL_AVAILABILITY["ST_GAS"] = 0.21) is fitted to ERCOT's
    # once-through 1950s-60s steamers and is >2x every other thermal class — an
    # implicit availability crush that holds MISO's intermediate steam off
    # (compounding the Moselle / Lewis Creek under-run on top of the EIA-860
    # net-summer rating already applied). When set, the ST_GAS/ST_CHP WEFOR base
    # is replaced with this realistic NERC-GADS gas-steam EFOR (the age
    # escalation and derate are kept). None leaves the global value (ERCOT/other
    # ISOs byte-identical).
    gas_st_wefor_base_override: float | None = None

    # SRMC-priced synchronization tranche (rebuild step 3a). Completes the
    # three-layer coal structure of Thread D. With this on (it requires
    # ``coal_mustrun_online_pmin`` so the synchronization band is sized to the
    # measured online-net-MW Pmin, and pairs with ``coal_takeorpay_from_data``
    # for the per-plant contract share), the coal min-load band is split into
    # two *forced-on* layers and held synchronized via FleetArrays.min_gen:
    #   1. ``_mustrun`` — the contracted (take-or-pay, sunk) share of the
    #      online Pmin (= online_Pmin x contract_share), bidding fuel-free
    #      (VOM + carbon + NOx). The genuinely must-burn floor.
    #   2. ``_sync`` — the spot (avoidable-fuel) remainder of the online Pmin
    #      (= online_Pmin x (1 - contract_share)), bidding its REAL SRMC (full
    #      delivered fuel + VOM + reagents; no take-or-pay discount).
    # Both are forced on (synchronized) so coal HOLDS volume at min-load instead
    # of price-following all the way down (the step-2 residual: 2024 coal under),
    # while the full-delivered-cost dispatchable tranches above still back down
    # in cheap hours so coal price-follows above Pmin (CEMS low/hi ~0.63). The
    # forced band bids at SRMC rather than fuel-free, so it does not re-suppress
    # the LMP coal sets when marginal. Forward-reproducible (online Pmin +
    # measured EIA-923 Sch-5 contract share; CLAUDE.md #11). Default off (keeper
    # unchanged). See docs/multi-iso/pjm-coal-operations-firstprinciples-2026-06.md
    # (Thread D, layer 2) and docs/multi-iso/pjm-reserve-ordc.md.
    coal_sync_srmc_tranche: bool = False

    # Marginal-coal measured-SRMC offer bound. The gas-keyed passthrough
    # sigmoids exist to model take-or-pay / stay-online BID discounting of
    # *contracted* coal, but they currently discount every above-must-run
    # tranche — including the marginal (econ*/peak) tranches whose fuel is
    # bought at market and has no sunk-contract story. With this on, the
    # fuel passthrough of a coal tranche above ``_committed`` is clamped to
    # >= 1.0, so the marginal coal offer never drops below the plant's own
    # measured incremental delivered SRMC (F923 delivered $/MMBtu x tranche
    # heat rate + VOM; the committed/must-run bands keep their contracted
    # discount). Removes a fitted degree of freedom from the offer path
    # rather than adding one — the sigmoid keeps only the tranches whose
    # discount has a physical (contract) driver. Forward-reproducible: the
    # bound is "offer >= full delivered fuel cost", which regenerates from
    # the forward fuel-price trajectory. Evidence: MISO model LMP sat $4-5
    # below the coal fleet's cheapest *measured* tranche while coal was
    # marginal ~94% of hours (results/calibration/FINDING-miso-burndown-
    # 2026-07.md Evidence 2). Default off (all existing keepers unchanged).
    coal_econ_srmc_bound: bool = False

    # Lignite (mine-mouth): take-or-pay fixed costs are sunk, so in
    # cheap-gas months lignite discounts its BID (not its cost) to hold
    # baseload against cheap gas CC instead of being priced out.
    coal_lignite_passthrough_sigmoid: bool = False
    coal_lignite_passthrough_floor: float | None = None
    coal_lignite_passthrough_ceil: float | None = None
    coal_lignite_passthrough_gas_mid: float | None = None
    coal_lignite_passthrough_gas_slope: float | None = None

    # Waste coal (culm/gob/mine-refuse, the PJM COAL_WC class): the fuel is
    # a near-free reclamation byproduct, so there is no cheap-gas discount
    # to give (floor ~1.0) — the curve exists to mark the bid UP when gas
    # is dear, suppressing the over-run a cheap-fuel fleet shows in
    # high-gas years.
    coal_waste_passthrough_sigmoid: bool = False
    coal_waste_passthrough_floor: float | None = None
    coal_waste_passthrough_ceil: float | None = None
    coal_waste_passthrough_gas_mid: float | None = None
    coal_waste_passthrough_gas_slope: float | None = None

    # Tier 3 (calibration) — CAMPD coal must-run overrides. When set, replace
    # the per-plant CSV must-run percentage for coal of the given supply with
    # this value; the committed/economic/peaking grid tranches rescale to fill
    # the remaining capacity. A gas-price-independent floor, swept to find the
    # coal level that holds across calibration years. None = use the CSV value.
    coal_lignite_mustrun_override: float | None = None
    coal_prb_mustrun_override: float | None = None

    # When True, coal must-run % comes from the per-plant CAMPD-derived table
    # (fleet.COAL_MUSTRUN_BY_PLANT) instead of the uniform lignite/PRB
    # overrides above — each coal plant gets its own observed minimum-load
    # floor. Plants absent from the table fall back to the uniform override or
    # the CSV value. The historic outage overlay still applies on top.
    coal_mustrun_per_plant: bool = False

    # When True, each within-window retiree plant (fleet.load_retired_within_
    # window) is capped to its measured monthly CAMPD CEMS envelope
    # (outages.retiree_availability_caps): a winding-down retiree the cost-based
    # LP would hold at its coal must-run floor as baseload is limited to the
    # peak output it actually demonstrated each month (zero after it stops),
    # honestly reflecting the out-of-market retirement economics the merit order
    # cannot see. Scoped to the within-window retirees (the bulk fleet keeps its
    # cost-based dispatch); backcast-only (historic outage source). Off by
    # default; enabled per ISO once its retiree-keeper effect is scored.
    retiree_cems_cap: bool = False

    # When True, simple-cycle peakers (CT_PEAKER) carry a per-plant monthly
    # reliability must-run floor equal to their observed EIA-923 net generation
    # (fleet.ct_mustrun_floor_mwh_by_plant), injected as a minimum-generation
    # bound. The energy-only LP prices CTs out almost entirely (~0% CF) where
    # the actuals show ~4% — peakers run for local reliability / reserves, not
    # economics — so the observed energy is forced on. Because the floor IS
    # observed generation (it already nets out every real outage), the
    # statistical WEFOR and planned-outage (maintenance) derates do NOT apply to
    # these units; layering them on would double-count and clip the floor.
    # Backcast-only; forecast years (no 923) get no floor. Off by default.
    ct_mustrun_per_plant: bool = False
    # Fraction of the observed monthly CT_PEAKER net generation to force as the
    # reliability floor (1.0 = the full observed energy). Lower it to leave the
    # peaker some economic headroom above the must-run base.
    ct_mustrun_floor_frac: float = 1.0

    # CT_PEAKER AS/RUC-deployment energy overlay (backcast only). Distinct from
    # the reliability must-run floor above: instead of forcing the full observed
    # net generation, it floors each CEMS-covered peaker to its *measured* output
    # ONLY in the out-of-merit hours where the RT price was below the unit's
    # marginal cost (the IMM-documented ancillary-service / reliability-unit-
    # commitment deployment + reserve-adequacy wedge the energy-only merit order
    # cannot dispatch — ~1.4-2.3 TWh/yr, scripts/derive_ct_deployment.py +
    # outages.ct_deployment_floor_for_year). The in-merit hours stay economic, so
    # CT is not floored to its full CEMS output. A sparse per-hour min-gen bound
    # (no MIP — prices stay LP duals); the units keep the statistical
    # availability model (the floor is well below pmax in its hours and merely
    # availability-capped). Off by default; forecast years (no artifact) no-op.
    ct_deployment_overlay: bool = False
    # Fraction of the measured deployment energy to force (1.0 = the full
    # measured out-of-merit wedge). Lower it to dial the recovered energy back
    # if a year would overshoot its CT class bar.
    ct_deployment_floor_frac: float = 1.0

    # Spatial reliability-deployment overlay (backcast only). The generalization
    # of the CT deployment overlay above to the load-pocket thermal fleet
    # (CC_REGULAR, COAL, ST_GAS, CC_CHP) in the under-running zones
    # (South_Central, West, Northeast). The 7-zone reduced network cannot form
    # the intra-zonal congestion pockets that pin local ERCOT prices above the
    # system hub, so the single-system-price LP over-generates North and
    # under-generates those pockets. This overlay floors each CEMS-covered
    # pocket plant to its *measured* net output ONLY in the hours where it was
    # economic at its LOCAL load-zone price yet out of merit at the system hub
    # (the congestion subset — ~2.7/3.6/5.2 TWh, scripts/derive_reliability_
    # deployment.py + outages.reliability_deployment_floor_for_year). A sparse
    # per-hour min-gen bound (no MIP — prices stay LP duals); the units keep the
    # statistical WEFOR/POF model (the floor is sparse and below pmax). Off by
    # default; forecast years / other ISOs (no artifact) no-op.
    reliability_deployment_overlay: bool = False
    # Fraction of the measured reliability-deployment energy to force (1.0 = the
    # full measured congestion wedge). Lower it if a year would overshoot a
    # pocket class bar.
    reliability_deployment_floor_frac: float = 1.0

    # When True, drop the statistical planned-outage (POF) derate on coal —
    # planned maintenance is now captured by the historic outage overlay, so
    # the POF would double-count. Keep WEFOR (forced outages) in the non-summer
    # months and the weather/performance derate all year; no POF and no
    # summer->shoulder WEFOR redistribution. Coal only; other thermal classes
    # keep the full POF/WEFOR seasonal model.
    coal_drop_pof: bool = False

    # Tier 3 (calibration) — CHP startup costs covered by the steam host.
    # When True, CHP classes (CC_CHP / CT_CHP / ST_CHP) are exempt from the
    # P1 monthly startup-amortization markup: a steam-host-obligated cogen
    # never pays a cold start on its own account (the host's steam demand
    # keeps the unit hot, or the start is incurred for steam regardless of
    # the energy market), so its energy bid carries no startup component.
    # Off (default) keeps the legacy behaviour where CHP CAMPD bins pay
    # their bin startup cost like merchant units.
    chp_startup_covered: bool = False

    # Warm-boiler coal committed band: a CAMPD coal bin with a per-plant
    # must-run floor never goes fully dark (the mustrun tranche holds the
    # boiler online), so its committed tranche's dispatch is a ramp on a
    # hot unit, not a cold start — exempt it from the P1 startup
    # amortization (the $100/MW coal start otherwise prices the committed
    # band above the econ ramp, inverting the offer-curve band order).
    # Off (default) keeps the legacy markup on every committed tranche.
    coal_warm_committed: bool = False

    # Render the per-plant committed band as an n-slice rising ramp (spanning
    # the committed HR multiplier +/- this fraction) instead of one flat
    # block, so a CAMPD bin clears its committed capacity progressively with
    # price rather than snapping 0 -> full committed share in one hour (the
    # under-populated mid-capacity-factor-band artifact of the commitment-free
    # LP). 0.0 (default) keeps the flat block. The mean committed bid is
    # unchanged, so class volume is ~preserved; only the dispatch level
    # distribution smooths. Slice count = offer_curve_smoothing_n.
    committed_ramp_spread: float = 0.0

    # Restrict the WEFOR residual cap (wefor_residual) to a chosen set of
    # plant groups. None (default) keeps the legacy scope — every
    # CAMPD-covered class (coal + CC/ST and their CHP). Set e.g.
    # {"ST_GAS", "ST_CHP"} to relieve only the class with a measured
    # availability deficit, leaving CC and coal on the full statistical
    # forced-outage model (the per-class evidence: ST_GAS 2024 was
    # availability-capped; CC was already over; coal relief just lets gas
    # displace it).
    wefor_residual_groups: frozenset[str] | None = None

    # Legacy gas-steam (ST_GAS) summer reliability treatment. When
    # gas_st_summer_mustrun > 0, the base (non-peak) ST_GAS tranches carry a
    # hard minimum-generation floor of that fraction of capacity in May-Sep
    # (units "dragged" online at min load for reliability). When
    # gas_st_startup_spread is True, ST_GAS amortizes its startup cost over the
    # whole May-Sep season (one seasonal start) rather than per calendar month,
    # so its summer bid markup is near zero.
    gas_st_startup_spread: bool = False
    # Off-summer (Oct-Apr) ST_GAS reliability min-gen floor, as a fraction of
    # capacity, applied to the same reliability (non-peaker) ST_GAS units as
    # gas_st_summer_mustrun. Peaker-class ST_GAS (fleet.ST_GAS_PEAKER_PLANTS)
    # get neither floor and run purely economically.
    gas_st_netload_drag: bool = False
    gas_st_drag_slope_per_gw: float = 0.00906  # overnight CF per GW net-load
    gas_st_drag_intercept: float = -0.1376  # floor zero-crossing ~15.2 GW
    gas_st_drag_cap: float = 0.34  # max observed overnight floor fraction (~50 GW)

    # CT_PEAKER net-load reliability drag (the simple-cycle analog of the ST_GAS
    # drag). ERCOT commits fast-start peakers for summer-peak + evening
    # net-load-ramp local reliability (RUC/RMR), which the hourly energy-only LP
    # — seeing their top-of-merit offer — never makes, so the backcast
    # under-runs CT_PEAKER and the freed energy spills onto cheaper CC. When
    # ct_netload_drag is True, each non-_peak CT_PEAKER tranche carries a
    # min-gen floor of clip(slope*netload_GW + intercept, 0, cap) x capacity,
    # but ONLY in the afternoon-evening ramp window [ramp_start, ramp_end) where
    # peakers actually serve reliability — CT overnight CF is ~0 even at high
    # net-load (the solar-collapse ramp is the signal, unlike the all-hours
    # ST_GAS boiler), so an ungated all-hours floor would over-floor. Defaults
    # are the CAMPD CT_PEAKER evening (15-22h) capacity factor regressed on
    # contemporaneous net-load, 2023-2025 (docs/ercot-ct-netload-drag-2026-06.md);
    # like the ST_GAS curve the trigger (net-load) and magnitude (physical
    # min-gen) are forward-derivable and condition-responsive, so it is the
    # forward-native replacement for the ct_mustrun_per_plant actuals pin
    # (CLAUDE.md #10/#11), admissible in both backcast and forecast.
    ct_netload_drag: bool = False
    ct_drag_slope_per_gw: float = 0.00703  # evening CF per GW net-load
    ct_drag_intercept: float = -0.1427  # floor zero-crossing ~20.3 GW
    ct_drag_cap: float = 0.47  # 95th-pct evening CF (hottest ramp hours)
    ct_drag_ramp_start: int = 15  # ramp window start hour (inclusive, local std)
    ct_drag_ramp_end: int = 22  # ramp window end hour (exclusive, local std)

    # ERCOT G-22 condition-responsive CT/peaker offer surface (default off,
    # ERCOT-gated). In the missed tail hours the model offers online CT/peaker
    # economic+peak tranches at flat heat_rate x gas (~$50-150/MWh) — "phantom
    # sub-$200 spare" that caps the energy dual — while the real fleet's peakers
    # self-withhold to the ERCOT cap band (~$1,500/MWh). This raises the CT/peaker
    # econ+peak tranche offer to the MEASURED self-withholding level (60-Day DAM
    # disclosure, data/raw/_validation-source/ercot_ct_offer_surface.json) only
    # above a measured net-load-percentile hinge (where even the peaker fleet's
    # lower quartile has crossed to cap-band); slack hours are byte-identical
    # (LP applies max(mc, level), low regime = 0). Forward-native (net-load
    # regenerates from a load+VRE forecast), rule-13-admissible; parameters
    # frozen against residuals (rule 20). See
    # docs/handoffs/ercot-g22-offer-surface-2026-07.md and
    # data.fleet.apply_ercot_ct_offer_surface.
    ercot_ct_offer_surface: bool = False

    # ERCOT G-22 §8 / ercot37-filed HETEROGENEITY-PRESERVING condition-responsive
    # offer surface (default off, ERCOT-gated). The successor to the rejected flat
    # ``ercot_ct_offer_surface`` (which collapsed the fleet's offer heterogeneity by
    # posting one p50 level on every CT econ/peak row → overshoot, calibration-log
    # 2026-07-06) and the rejected static ``peak_ladder`` wall (which perturbed the
    # P0→P1 startup-amortization coupling in ALL hours → CT↔ST volume swap,
    # docs/FINDING-ercot-priceshape-2026-07.md §6). This mechanism posts the MEASURED
    # peak-band offer DISTRIBUTION (the 60-Day DAM disclosure top-of-curve quantile
    # ladder, per class) but CONDITION-BINNED by net-load percentile, applied to the
    # gas peak-band rungs (CC/CT/ST) in the P1 clearing solve ONLY and ONLY in the
    # anticipated-tight hours — so (a) P0 run lengths (and the CT↔ST coupling) are
    # byte-identical to the keeper, (b) loose hours are byte-identical (the wall is
    # clamped never to lower an offer below the keeper's resolved peak height), and
    # (c) within a tight hour the lower rungs stay competitive while only the upper
    # rungs reach the cap band — the heterogeneity the flat surface destroyed. Both
    # the trigger (net-load percentile, forward-native from a load+VRE forecast) and
    # the level (measured QSE offer quantiles) are rule-13-admissible; parameters are
    # derived from source data only (rule 21) and frozen against residuals (rule 20).
    # The measured surface SUPERSEDES the static p50 peak on these classes where it
    # applies (rule 19: one mechanism per phenomenon — it does not stack on top).
    # See scripts/derive_dam_offer_hrmults.py --condition-binned and
    # data.fleet.apply_ercot_offer_surface_conditional.
    ercot_offer_surface_conditional: bool = False
    # Path to the measured condition-binned ladder JSON (default: the frozen
    # data/raw/_validation-source/offer_curve_dam_hrmults_condbinned.json). None →
    # the mechanism is a no-op even when the flag is on.
    ercot_offer_surface_binned_path: str | None = None
    # Net-load percentile bin EDGES separating the loose / mid / tight regimes the
    # measured ladder is derived and applied over. The n edges define n+1 bins on the
    # year's own net-load distribution (percentile-ranked, so a forecast year's bins
    # regenerate); bin 0 is the loosest. MUST match the edges the derive used (the
    # JSON records them and the mechanism asserts agreement). Default: three edges →
    # four bins, resolving the top decile where the wall lives.
    ercot_offer_surface_netload_pcts: tuple[float, ...] = (0.80, 0.90, 0.97)
    # Minimum net-load bin index (0 = loosest) at which the peak-rung wall engages.
    # Below it the surface is inert (byte-identical), protecting mild hours from any
    # residual peak-band repricing. 0 applies the full measured distribution in every
    # bin (the merit order still self-gates: mild hours reach only the lower rungs).
    ercot_offer_surface_min_bin: int = 0
    # Safety cap on the repriced peak offer as a fraction of VOLL, so a measured wall
    # rung can never tie or exceed the value of lost load (which would let the LP shed
    # load instead of clearing the peak band). 0.95 × 5000 = $4750, above the measured
    # p90 wall (~$2,700) and below VOLL.
    ercot_offer_surface_price_cap_frac: float = 0.95

    # ERCOT unit-level (window-grain) nuclear refuel availability (default off,
    # ERCOT backcast-gated). Replaces the NUCLEAR_MONTHLY_CF_BY_YEAR fleet-month
    # smear for the four ERCOT reactors with the measured per-reactor DAILY
    # availability from the 60-Day DAM disclosure Gen_Resource NUC status
    # (data/raw/ercot-nuclear-availability.csv,
    # scripts/derive_ercot_nuclear_availability.py), monthly energy reconciled
    # to the same EIA-923 anchor the smear used. The smear carries the right
    # monthly ENERGY but mis-times refuel windows within the month by up to
    # ±1.4 GW (2024 type case: STP-2 out 3/23–5/19 spans the Apr-16/Apr-28/
    # May-8 scarcity events, Comanche Peak 1 out 5/11–5/16 overlaps the May
    # DA-shoulder days, and all four units were BACK for the May-24..27 record
    # heat the smear kept derated — docs/DIAGNOSIS-ercot-may2024-outage-
    # forensics-2026-07.md §2.1). A refuel window is a physical availability
    # event (rule-14 admissible, the nuclear analogue of the CAMPD fossil
    # outage windows; forward years regenerate via NUCLEAR_MONTHLY_CF /
    # refuel-block scheduling). Dates the disclosure does not cover (Oct 2023
    # hole, Nov-Dec 2025 until the 2026 publications land) keep the monthly
    # smear. See data.outages.ercot_nuclear_unit_availability_series and the
    # application in data.fleet.generators_to_fleet_arrays.
    ercot_nuclear_unit_availability: bool = False

    # NEISO condition-responsive fast-start offer surface — the ISO-NE analogue
    # of ercot_offer_surface_conditional above (winter scarcity charter Limb B;
    # the G-22 §8 heterogeneity-preserving design, default off, NEISO-gated).
    # Posts the MEASURED fast-start offer DISTRIBUTION from ISO-NE's public DA
    # Energy Market historical offer data (masked assets; the fast-start
    # population selected by physics, Claim30 >= 0.9 x EcoMax), condition-binned
    # by within-year net-load percentile, onto the CT_PEAKER peak-band rungs in
    # the P1 clearing solve ONLY and ONLY in anticipated-tight hours — P0 run
    # lengths and loose hours stay byte-identical (the ladder is clamped never
    # to lower an offer below the resolved peak height); within a tight hour
    # the lower rungs stay competitive while the upper rungs reach the measured
    # wall. Trigger (net-load percentile, forward-native) and level (measured
    # offer quantiles over the model's own Algonquin daily gas series) are
    # rule-13 admissible; parameters are derived from source data only
    # (scripts/derive_neiso_offer_surface.py, rule 21) and frozen against
    # residuals (rule 20). NEISO-only (rule 25: the surface carries no generic
    # fallback and never crosses ISO boundaries).
    neiso_offer_surface_conditional: bool = False
    # Path to the measured NEISO condition-binned ladder JSON (default: the
    # frozen data/raw/_validation-source/neiso_offer_surface_condbinned.json).
    # None → the mechanism is a no-op even when the flag is on.
    neiso_offer_surface_binned_path: str | None = None
    # Net-load percentile bin EDGES (same contract as the ERCOT field above;
    # the JSON records its edges and the mechanism asserts agreement).
    neiso_offer_surface_netload_pcts: tuple[float, ...] = (0.80, 0.90, 0.97)
    # Minimum net-load bin index at which the wall engages (0 = every bin; the
    # merit order still self-gates in mild hours).
    neiso_offer_surface_min_bin: int = 0
    # Safety cap on the repriced offer as a fraction of VOLL (the measured
    # offers already carry ISO-NE's $1,000/MWh energy offer cap; this guard
    # only keeps a repriced rung strictly below the load-shed slack).
    neiso_offer_surface_price_cap_frac: float = 0.95

    # Combined-cycle tranche heat-rate OVERRIDES (relative to the plant's base
    # HR). When set, every CC bin's committed / economic / peaking tranche heat
    # rate is base_HR x {cc_committed_hr_override, cc_econ_hr_override,
    # cc_peak_hr_override}, giving a rising part-load supply curve (committed at
    # full efficiency, economic a modest penalty, peaking expensive) instead of
    # the per-plant CSV HR_Mult columns. None leaves the CSV multipliers in
    # place. (Distinct from the cc_committed_hr_mult / cc_econ_hr_mult oracles
    # above, which document the CSV's expected multipliers but are not applied.)
    cc_committed_hr_override: float | None = None
    cc_econ_hr_override: float | None = None
    cc_peak_hr_override: float | None = None

    # When True, each CC_REGULAR bin's committed-tranche % (minimum stable load
    # once started) is replaced by the per-plant CAMPD-observed value
    # (fleet.CC_REGULAR_COMMITTED_PCT_BY_PLANT) instead of the coarse assumed
    # CSV Pct_Committed; the economic tranche absorbs the difference. Plants
    # without CAMPD coverage keep the CSV value. Off by default (CSV split).
    cc_committed_per_plant: bool = False

    # When True (ERCOT backcast), each CC_REGULAR plant's LP capacity is raised
    # to its demonstrated CAMPD peak where that exceeds the curated bin
    # nameplate — the cold-weather (winter) over-rating an F-class CC delivers
    # that the standard nameplate omits. Raise-only: a plant that never
    # dispatched to its rating keeps it. Without this, plants like Freestone
    # (nameplate 1036 MW, observed peak 1119 MW) cannot reach the output the
    # real plant did and log zero hours in their top CF band. Reconciliation
    # table from scripts/derive_cc_capacity_reconcile.py. Off by default.
    cc_capacity_reconcile: bool = False
    cc_capacity_reconcile_path: str = str(
        PROCESSED_DIR / "cc_capacity_reconcile_ERCOT.csv"
    )

    # When True, CC_REGULAR / CC_CHP plants use the per-plant CAMPD-derived
    # duct-firing/scarcity share from fleet.thermal_tranche_peaking (the share
    # of the plant's demonstrated sustained maximum cleared in <5% of its
    # online hours) instead of the offer curve's class-wide ``pct_peaking`` —
    # moving where the expensive duct-burner peak band starts on the CF axis.
    # The economic tranche absorbs the difference. Plants absent from the
    # ISO's thermal-tranche artifact keep the offer-curve value. Off by
    # default. (The prior ERCOT hand-set CC_REGULAR_PEAKING_PCT_BY_PLANT
    # four-plant override this flag also drove was deleted 2026-07 — rule 26,
    # G-26/C-12: dead in every current keeper, structurally superseded here
    # and by ``cc_duct_peaking`` below.)
    cc_peaking_per_plant: bool = False

    # When True, every CC_REGULAR / CC_CHP plant's peaking-tranche % comes
    # from the EIA-860 duct-burner flag (fleet.cc_duct_peaking_pct):
    # duct-fired plants get their nameplate-vs-net-summer capability gap as
    # the peak band, non-duct CC plants get 0 — no phantom scarcity band on
    # plants with no duct firing. Supersedes the offer curve's class-wide
    # ``pct_peaking`` (the band heat-rate multipliers still apply on top);
    # plants absent from the EIA-860 sheet keep the class value. Off by
    # default.
    cc_duct_peaking: bool = False

    # Physical cap (percentage points of capacity) on the per-plant
    # ``cc_duct_peaking`` band. The raw EIA-860 nameplate-vs-net-summer gap
    # conflates the ambient SUMMER CAPACITY DERATE with the genuine duct-firing
    # increment, so for plants with a large gap it sizes an oversized expensive
    # peak band that drops the price wall far below the real duct-firing point
    # (e.g. Guernsey 13% gap -> wall at ~76% of nameplate). Capping the band at
    # the F-class supplementary-firing engineering maximum (~8% of capacity)
    # keeps the per-plant duct FLAG structure (non-duct CCs still get 0) while
    # positioning the wall at the physical ~92% duct-firing point. None leaves
    # the raw gap uncapped (prior behaviour). A physical bound, not a fit.
    cc_duct_peaking_cap_pct: float | None = None

    # When True, combined-cycle (CC_REGULAR / CC_CHP) plants in the per-plant
    # fleet carry their full EIA-860 NAMEPLATE capacity in the LP and are derated
    # to the measured NET SUMMER rating in the summer months only — the correct
    # seasonal shape (full cold-weather capability in winter, ambient-derated in
    # summer). This replaces the prior behaviour of pinning the LP capacity at
    # net-summer year-round (which under-modelled winter output AND, with the
    # flat 10% ``_SUMMER_CLASS_DERATE`` applied on top, derated summer twice) and
    # the flat class derate with the per-plant MEASURED summer derate
    # (net_summer / nameplate, fleet.cc_summer_capacity). In a historic backcast
    # the statistical forced-outage rate (WEFOR), planned-outage factor (POF) and
    # age-based performance derate are also dropped for CC — the CAMPD outage
    # overlay already supplies every real outage window, so the statistical model
    # double-counts. The duct-firing peak band then sits at the top of nameplate
    # (its physical location) instead of inside a net-summer-capped range.
    # Coal/CT/ST and ERCOT (CAMPD-bin nameplate capacity) are unaffected. Off by
    # default.
    cc_nameplate_summer_derate: bool = False

    # COAL net-summer capacity derate (coal_nameplate_summer_derate, off by
    # default). The exact coal analogue of cc_nameplate_summer_derate above: a
    # coal steam unit carries its EIA-860 NAMEPLATE capacity in the LP (the
    # CAMPD-bin / EIA-860 pmax) but is physically incapable of that output in the
    # summer — condenser back-pressure and cooling-water-temperature limits pull
    # an old steam unit's sustainable rating down to its published NET-SUMMER
    # capacity. This applies the per-plant MEASURED summer availability multiplier
    # ``net_summer / nameplate`` (fleet.coal_summer_derate_ratio, EIA-860 Operable
    # "Conventional Steam Coal" / "Coal IGCC" units) on the summer months only —
    # the same seasonal shape and same published EIA-860 source CC/CT already use,
    # which coal alone was omitted from ("COAL / ST_GAS carry no existing summer
    # derate" — the availability loop below). Rule-15 measured-replaces-estimate
    # and rule-11 physical: the net-summer rating regenerates for any forward year
    # and responds to changed conditions (a re-rated unit gets a new EIA-860
    # summer number), so it is admissible in BOTH backcast and forecast, never a
    # residual-fitted haircut. It is NOT the rejected ``temp_dependent_derate``
    # (an INCREMENTAL literature-slope cut BELOW net-summer, refuted for the ERCOT
    # gas fleet 2026-07-09): this only brings coal DOWN to its published
    # net-summer rating, which the per-plant CEMS summer maxima confirm the fleet
    # tops out at (Oak Grove 0.937 vs ns 0.952, Major Oak 0.877 vs 0.873, Spruce
    # 0.893 vs 0.904 — see docs/handoffs/ercot-coal-nameplate-summer-derate-2026-07.md).
    # A plant whose summer rating meets/exceeds nameplate (Martin Lake 1.03,
    # Coleto 1.05) clamps to 1.0 (no derate). Only reduces capacity, only in
    # summer; can never loosen the fleet. ERCOT-scoped in practice (rule 24), but
    # the EIA-860 lookup is ISO-agnostic. Off by default.
    coal_nameplate_summer_derate: bool = False

    # Gas-turbine AMBIENT-TEMPERATURE capacity derate (gt_ambient_derate, off by
    # default). The EIA-860 net-summer rating (applied above/flat _SUMMER_CLASS_
    # DERATE) is a season-average summer capability; a gas turbine keeps losing
    # output as ambient rises ABOVE that rating point, so the hottest design-peak
    # afternoon — exactly the hours scarcity should occur — is materially below
    # the net-summer rating. This layers an INCREMENTAL, purely-additive derate
    # on CC_REGULAR/CT_PEAKER (and their CHP variants) for hours whose measured
    # zone tmax exceeds ``gt_ambient_derate_ref_c``:
    #     extra(t) = slope_class x max(0, tmax_zone(t) - ref_c);  avail *= 1-extra
    # ``ref_c`` is the net-summer capability-test reference (~35 C / 95 F, the
    # standard summer GT rating point — so the increment does NOT double-count the
    # net-summer derate, it only deepens it on hotter-than-rating hours). The
    # per-C slopes are physical GT ambient-derate rates (combined-cycle less
    # sensitive than simple-cycle, the steam bottoming cycle partially
    # compensating): CC ~0.4 %/C, CT ~0.6 %/C (NREL/GE frame-GT performance
    # curves, docs/parameter-citations.md). Both the physical slope and the
    # measured hourly temperature regenerate for a forward year and respond to
    # changed conditions, so this is a rule-11-admissible physical input in BOTH
    # backcast and forecast — not a residual-fitted haircut. Only reduces
    # capacity, only on hot hours; can never loosen the fleet.
    gt_ambient_derate: bool = False
    gt_ambient_derate_ref_c: float = 35.0  # net-summer rating reference temp (C)
    gt_ambient_derate_slope_cc: float = 0.004  # CC fractional loss per C above ref
    gt_ambient_derate_slope_ct: float = 0.006  # CT fractional loss per C above ref

    # TEMPERATURE-DEPENDENT capacity derate (temp_dependent_derate, off by
    # default) -- a physically-derived ALTERNATIVE to the flat EIA-860 net-summer
    # / _SUMMER_CLASS_DERATE treatment, not an increment on top of it (contrast
    # gt_ambient_derate above). When on it REPLACES the flat summer derate (and
    # the per-plant measured CC ratio) with a per-class curve in measured hourly
    # zone dry-bulb temperature and supersedes gt_ambient_derate for the affected
    # classes. Two physical mechanisms:
    #   * gas turbines (CC/CT) -- air-density / mass-flow limited: usable output
    #     falls ~linearly as ambient dry-bulb rises above the 15 C (59 F) ISO
    #     rating point. CT (simple cycle) is steepest; CC is shallower because the
    #     steam bottoming cycle recovers part of the lost GT exhaust heat.
    #   * steam plants (ST_GAS / COAL) -- condenser back-pressure limited: a
    #     smaller loss with a warmer onset; dry-bulb TMAX is a proxy for the true
    #     wet-bulb / cooling-water driver (documented approximation).
    # Curve:  raw(t) = 1 - slope_class * max(0, tmax_zone(t) - ref_class).
    # For classes that already carry a net-summer derate (CC/CT, or the per-plant
    # measured CC ratio under cc_nameplate_summer_derate) the curve is rescaled so
    # its SUMMER-hours (Jun-Sep) mean reproduces that same net-summer capability:
    # capacity-NEUTRAL on the seasonal average, only RESHAPING it by temperature
    # so heatwave hours sit below net-summer (where scarcity should occur) and
    # cooler hours toward full rating -- it does NOT tune the level (rules 1, 9).
    # COAL / ST_GAS carry no existing summer derate, so they take the raw curve
    # directly: a pure, additive hot-hour condenser derate. Availability is never
    # driven above 1.0, so capacity never exceeds the net-summer pmax basis.
    # Physics slope x measured hourly temperature -> forward-reproducible in BOTH
    # backcast and forecast (rule 11); never fitted to a price/volume residual.
    # Slopes are fractional loss per degree C. Sources (docs/parameter-citations):
    #   CT 0.0126/C  = 0.70 %/F, mid of the 0.5-0.9 %/F industry frame-GT range
    #                  (arXiv:2311.07001 uses 0.0083/C; CPUC R.21-10-002 ~1 %/C).
    #   CC 0.0076/C  = 0.42 %/F net, from ~22.6 % net loss over 41->95 F
    #                  (arXiv:2311.07001 net-CC ~0.75 %/C).
    #   ST_GAS 0.0054/C = 0.30 %/F (CPUC R.21-10-002: steam slope > GT slope, but
    #                  plant-level condenser derate is modest).
    #   COAL 0.0040/C = 0.22 %/F, onset 25 C / 77 F (arXiv:2311.07001 reports a
    #                  modest steam-coal summer deration, condenser-onset limited).
    temp_dependent_derate: bool = False
    temp_derate_ref_c: float = 15.0  # ISO 59 F rating point (GT + gas-steam)
    temp_derate_ref_c_coal: float = 25.0  # coal condenser-derate onset (~77 F)
    temp_derate_slope_cc: float = 0.0076  # CC fractional loss per C above ref
    temp_derate_slope_ct: float = 0.0126  # CT fractional loss per C above ref
    temp_derate_slope_st_gas: float = 0.0054  # gas-steam fractional loss per C
    temp_derate_slope_coal: float = 0.0040  # coal fractional loss per C above ref

    # Reliability gas-steam (ST_GAS) tranche heat-rate OVERRIDES (relative to
    # the plant's base HR). When set, each reliability ST_GAS bin's committed /
    # economic / peaking heat rate is base_HR x {gas_st_committed_hr_override,
    # gas_st_econ_hr_override, gas_st_peak_hr_override}. The cheap committed
    # tranche (e.g. 0.5x) replaces the old flat must-run floor: a low committed
    # bid commits the unit economically instead of forcing it on. Peaker-class
    # ST_GAS (fleet.ST_GAS_PEAKER_PLANTS) keep their CSV HR_Mult columns and run
    # purely economically. None leaves the CSV multipliers in place.
    gas_st_committed_hr_override: float | None = None
    gas_st_econ_hr_override: float | None = None
    gas_st_peak_hr_override: float | None = None

    # CT_CHP tranche heat-rate overrides (relative to base HR), applied to the
    # grid-facing tranches above the must-run BTM + steam-following floor. None
    # leaves the CSV HR_Mult columns in place.
    ct_committed_hr_override: float | None = None
    ct_econ_hr_override: float | None = None
    ct_peak_hr_override: float | None = None

    # Economic-tranche split. Maps a CAMPD bin's Plant_Group to a 3-element
    # list ``[split_frac, lo_hr_mult, hi_hr_mult]``: the single economic tranche
    # is replaced by two stepped tranches — a lower step holding ``split_frac``
    # of the economic capacity at ``base_HR x lo_hr_mult`` (the plant's weighted
    # heat rate ``hr_weighted`` x the multiplier), and an upper step holding the
    # remainder at ``base_HR x hi_hr_mult`` — giving a rising heat rate across
    # the economic block (lo_hr_mult < hi_hr_mult). The mechanism is generic and
    # available for EVERY group (CC_REGULAR, CC_CHP, ST_GAS, CT_CHP, CT_PEAKER,
    # COAL, ST_CHP); only groups present in the map are split, and ST_GAS peaker
    # plants (fleet.ST_GAS_PEAKER_PLANTS) are excluded (they dispatch on CSV heat
    # rates). When a group is split, its two steps' heat rates come from
    # lo/hi_hr_mult and SUPERSEDE that group's single cc_/gas_st_/ct_econ_hr_
    # override for the economic tranche.
    #
    # The split location and multipliers are NOT defaulted — they are supplied by
    # the operator from their own research. Empty map (the default) leaves every
    # group with a single economic tranche (current behavior). Example (values
    # illustrative, not endorsed):
    #     econ_split_by_group={"ST_GAS": [0.5, 0.9, 1.3],
    #                          "CC_REGULAR": [0.5, 1.05, 1.30]}
    econ_split_by_group: dict[str, list[float]] = field(default_factory=dict)

    # Unified thermal offer-curve parameterization (supersedes the legacy
    # cc_/gas_st_/ct_*_hr_override triples + econ_split_by_group for any group
    # present here). Maps a Plant_Group to its band price multipliers on the
    # heat-rate term — band MC = VOM + (AHR x fuel_price) x multiplier, with VOM
    # held CONSTANT across bands (no peak VOM markup). Inner keys:
    #   committed      — committed-band HR multiplier
    #   econ_low       — economic ramp START HR multiplier (CF-low end)
    #   econ_high      — economic ramp END HR multiplier (CF-high end). The
    #                    n-slice ramp spans econ_low -> econ_high; these two
    #                    endpoints set its slope.
    #   econ_low_share — fraction of the economic block in the lower step
    #                    (only used when smoothing is off; two flat econ steps)
    #   peak           — OPTIONAL peaking-band HR multiplier. The peak is a
    #                    SEPARATE flat tranche that jumps up above the ramp. When
    #                    omitted for CC_REGULAR / CC_CHP it defaults to the
    #                    per-plant duct-burner multiplier by turbine class
    #                    (fleet.cc_duct_burner_peak_mult); set it to override
    #                    with a single flat value. Required for non-CC groups.
    #   pct_committed  — OPTIONAL committed capacity %; when present it overrides
    #                    the CSV Pct_Committed (per-plant CC grounding still wins)
    #   pct_peaking    — OPTIONAL peaking capacity %; when present it overrides
    #                    the CSV Pct_Peaking before the residual split
    #                    (residual = 100 - must_run - committed - peaking, then
    #                    econ_low/econ_high = residual x econ_low_share/(1-share))
    # ST_GAS peaker plants (fleet.ST_GAS_PEAKER_PLANTS) are excluded (CSV heat
    # rates). Empty (the default) leaves the legacy override / CSV path intact.
    offer_curve_by_group: dict[str, dict[str, float]] = field(default_factory=dict)

    # N-slice smoothing of the economic offer curve. When
    # offer_curve_smoothing_n > 0, each plant's flat econ blocks (econ-low /
    # econ-high) are replaced by N equal-capacity sub-tranches whose heat-rate
    # multiplier rises from the econ-low multiplier to the econ-high multiplier
    # along
    # ``mult(t) = lo + (pk - lo) * t**exp``, ``t = (k + 0.5)/N``. exp = 1.0 is a
    # straight (linear) ramp, matching the gently-rising incremental heat rate
    # of a thermal unit; exp > 1 is convex (cheap-bottom). Finer steps let a
    # unit fill gradually as price crosses its rising MC instead of snapping
    # between two wide flat blocks, so dispatch spreads across the CF range the
    # way CAMPD shows rather than parking at a few band edges. Only engages on
    # the offer-curve / econ-split path (real calibration runs); set to 0 to
    # recover the flat two-block econ curve.
    offer_curve_smoothing_n: int = 6
    offer_curve_smoothing_exp: float = 1.0
    # Optional midpoint anchor for the econ ramp shape: the fraction of the
    # lo->pk heat-rate rise reached at the capacity midpoint (t = 0.5),
    # rendered as a two-segment piecewise-linear ramp f(0)=0, f(0.5)=mid,
    # f(1)=1. None (default) keeps the t**exp power shape. mid < 0.5 keeps
    # the middle slices cheap and concentrates the rise in the top of the
    # curve — e.g. 0.25 prices slice 4 of 6 like a linear ramp's slice 2 —
    # which the single exp exponent cannot do without also distorting the
    # bottom. Overrides offer_curve_smoothing_exp when set.
    offer_curve_smoothing_mid: float | None = None

    # Outage capacity comes off the TOP of a CC_REGULAR plant's offer stack
    # instead of pro-rata across its tranches. The default (False) scales
    # every tranche by the same hourly availability factor, which drags the
    # cheap committed block down with the plant — a 2x1 CC with one train out
    # (availability ~0.67) sees its committed floor fall from ~37% to ~25% of
    # nameplate and the LP parks there, while the real plant runs its
    # remaining train near full load (CAMPD dwells at 36-43% CF). When True,
    # each CC_REGULAR plant's hourly available MW (unchanged in total) fills
    # its tranches bottom-up in heat-rate order — committed first, econ
    # slices, duct-fire peak last — so a partial outage truncates the
    # expensive end of the curve and the committed floor keeps its level,
    # exactly as a real plant sheds its least-efficient increments first.
    cc_outage_derate_from_top: bool = False

    # CHP cogeneration treatment. When chp_steam_following is True, each
    # CC_CHP / CT_CHP / ST_CHP bin is modeled as a steam host's cogen rather
    # than a merchant unit:
    #   * the behind-the-meter host self-supply removed from the grid LP (and
    #     added back in the report) is fleet.chp_btm_pct() — a per-plant share
    #     keyed to the EIA-923 sector (merchant / industrial / commercial),
    #     not the flat chp_btm_floor_pct or the CSV Pct_Must_Run;
    #   * a grid-delivered steam-following floor (fleet.CHP_PMIN_CF_BY_PLANT
    #     minus the BTM share) is forced on flat via FleetArrays.min_gen — the
    #     steady export base that always reaches the grid.
    # Off by default (merchant behavior); the calibration backcast turns it on.
    chp_steam_following: bool = False
    chp_btm_floor_pct: float = 40.0

    # Measured steam-following export floor (backcast/calibration overlay,
    # composes with chp_steam_following). When True in backcast mode, each
    # CHP bin's total must-run CF (the ``pmin_cf`` feeding the grid floor
    # ``pmin_cf x (1 - btm_share)``) is the plant's measured EIA-923 class
    # CF for the solved year (data.chp.chp_class_netgen_mwh / nameplate-hours)
    # instead of the pooled CAMPD p2 minimum. A topping-cycle cogen's power
    # train follows its host's steam demand, not the LMP — its grid export
    # rides at the host-driven operating level (ERCOT CC_CHP fleet: ~50-70%
    # annual CF) all year, while the p2 percentile only captures the
    # never-below minimum (~20-35%), leaving the LP to idle the steam-following
    # base whenever the cogen's offer sits above the margin. Rule #13
    # admissibility: host steam demand is a physical input exogenous to the
    # power market; the same floor regenerates for a forward year from
    # sector-level host demand x the EIA-860 CHP designation, and it responds
    # to changed host conditions (a shrinking host shrinks the floor). The LP
    # keeps upward freedom (scarcity dispatch above the floor) and outage
    # windows still relax it (min_gen is clipped to pmax x availability).
    # Plants absent from the year's EIA-923 vintage keep the p2/artifact floor.
    # Off by default — forecast mode always uses the persistent
    # chp_pmin_cf floors.
    chp_export_floor_measured: bool = False

    # Measured ERCOT GTC transfer limits (backcast/calibration overlay). When
    # True in backcast mode, the export-direction capability of the transfer
    # links that carry ERCOT's published Generic Transmission Constraints
    # (PNHNDL -> Panhandle->North, WESTEX -> the two West export links,
    # NE_LOB -> Northeast->North; constants.ERCOT_GTC_LINK_MAP) follows the
    # measured hourly GTC limit series curated from the NP6-86 "SCED Shadow
    # Prices and Binding Transmission Constraints" archive (gtc-limits clean
    # datatype) instead of the single static ttc_mw. Hours where a constraint
    # was in SCED's active set take the time-average of its per-interval
    # measured limits; other hours ride the constraint's measured year
    # envelope. The import direction keeps the static thermal capability
    # (a GTC is an export stability limit, not an import rating). Renewable
    # curtailment then emerges endogenously wherever the measured limits
    # bottle the West/Panhandle pockets — never from a quota or haircut.
    # Rule #14 admissibility: a GTC limit is a published physical/market
    # input (a voltage/WSCR stability transfer limit) that regenerates for
    # any year ERCOT publishes and responds to changed grid conditions; the
    # reported HSL curtailment totals remain the VALIDATION target and are
    # never read by this overlay. Applied per year only when BOTH the year's
    # gtc-limits clean partition AND its measured HSL renewable-potential
    # data exist (without real potential, delivered-as-CF renewables would be
    # double-curtailed below actuals). Off by default; forecast mode always
    # uses the static (or scenario-built) link ratings.
    ercot_gtc_limits_measured: bool = False

    # Measured PJM internal interface transfer limits (backcast/calibration
    # overlay — the PJM analogue of ercot_gtc_limits_measured). When True in
    # backcast mode for PJM, the forward (west->east congestion) direction of
    # the internal links whose static ttc_mw was seeded from the PJM Data
    # Miner 2 transfer-limit postings (constants.PJM_INTERFACE_LINK_MAP:
    # 50045005 -> ComEd->AEP, AEP/DOM -> AEP->Dominion, AP-South ->
    # West_APS->SWMAAC, Bedington-BlackOak -> West_APS->Central_PA, and the
    # Average Western/Central/Eastern envelopes on the links they seeded)
    # follows the measured HOURLY published limit series
    # (transfer-interface-limits clean datatype) instead of the single static
    # ttc_mw. Where an interface publishes both pre- and post-contingency
    # limits, the operative hourly cap is their elementwise min (both are
    # simultaneously-enforced security limits). The reverse direction keeps
    # the static capability (the published limits are directional
    # security limits on the west->east cut, not reverse ratings).
    # Supersedes constants.PJM_MEASURED_INTERNAL_TTC's static medians on the
    # mapped links when both are enabled — same measured feed at hourly
    # rather than pooled-median aggregation (rule 19: one mechanism per
    # phenomenon), while pjm_congestion still sets the static fill/reverse
    # value those links carry.
    # Rule #13/#14 admissibility: an interface transfer limit is PJM's
    # published operating-security transfer capability — it regenerates
    # every year from the same Data Miner 2 feed and responds to changed
    # grid conditions (outages, re-ratings, upgrades); nothing here reads
    # model outputs or the scoring targets. Two-track by construction
    # (the hr_by_year pattern): backcast years read the measured hourly
    # series; FORECAST years keep the static seeds — the static ttc_mw
    # values (2024 means of this same feed) ARE the forward story, since a
    # forecast has no realized outage/re-rating sequence to read.
    # Off by default.
    pjm_measured_interface_limits: bool = False

    # ERCOT West Texas Export corridor VRE curtailment-share driver
    # (backcast/calibration overlay; docs/handoffs/ercot-vre-curtailment-topology-
    # scope-2026-07.md, WP-B). When True in backcast mode for ERCOT, the West and
    # Panhandle zones' wind (and solar) CF upper bound is multiplied by
    #   1 - depth * congestion_share(net_load_decile, hour_of_day, season),
    # the reduced-form stand-in for the sub-zonal Permian/CREZ nodal congestion
    # the 8-zone reduction cannot resolve -- dozens of internal 138/345 kV lines
    # that chronically curtail West wind even when the aggregate West->North
    # interface has headroom (the C2 / [3e] under-curtailment gap; step-2 handoff).
    # congestion_share is the SHAPE: the measured NP6-86 SCED West-corridor binding
    # frequency (data.curtailment_share reads the derived reference table
    # data/raw/reference/ercot_wtx_curtailment_share.csv), geo-attributed via
    # ERCOT's authoritative Settlement-Point/electrical-bus load-zone mapping
    # (NP4-160) and reproducing the measured binding-frequency distribution
    # leave-one-year-out (rule #23). It is a function of the model's OWN net-load,
    # so it regenerates for a forecast year (more West VRE -> deeper net-load
    # troughs -> higher congestion share). depth is the LEVEL: a single per-tech
    # coefficient centred on the measured curtailment MW quantity like the
    # RTOLCAP-forward ``deliv`` coefficient (never a price residual), a LOYO-stable
    # structural constant (~0.10 wind across 2023-2025); depth=0.0 is the
    # zero-forcing ablation (driver inert). Applied per year only when the derived
    # reference table and the year's measured HSL potential both exist. Off by
    # default. See scripts/derive_ercot_wtx_curtailment_share.py.
    ercot_wtx_curtailment_driver: bool = False
    ercot_wtx_curtail_depth_wind: float = 0.1004
    ercot_wtx_curtail_depth_solar: float = 0.1637

    # When True (default), coal generators are repriced to the flat annual
    # lignite/PRB delivered-cost trajectory (apply_coal_supply_pricing),
    # overwriting any EIA-923 monthly per-plant cost. Set False to keep the
    # actual EIA-923 monthly delivered cost for matched coal plants (the rest
    # fall back to the generic COAL_PRICE_BASE annual).
    coal_supply_repricing: bool = True

    # When True (default), coal generators that report EIA-923 monthly fuel
    # receipts (currently Fayette, San Miguel, J K Spruce) have their delivered
    # cost overwritten by that measured plant-specific monthly price. Set False
    # to keep all coal on the flat annual lignite/PRB trajectory (the "average"
    # baseline), reverting those few plants to the supply-type average. Coal
    # supply classes (lignite mine-mouth vs railed PRB) are physically distinct
    # costs, so per-plant coal pricing stays on by default.
    coal_plant_monthly_pricing: bool = True

    # Per-plant monthly gas pricing. OFF by default: every gas generator pays
    # the same Henry Hub trajectory + ISO basis (optionally seasonally shaped),
    # so units in the same zone are not split by patchy EIA-923 Schedule-5
    # reporting. EIA-923 gas-cost coverage in ERCOT is thin (~12% of CC MW),
    # and because merchant CCs in a hub all buy gas in the same market, giving
    # the few reporting plants their own (often higher, winter-spiking) cost
    # while suppressed peers pay the smoothed trajectory creates a spurious
    # intra-zone price asymmetry (e.g. it penalised Jack County against its
    # North-zone neighbours). Set True to restore per-plant gas costs where
    # EIA-923 reports them. Does not affect coal (see above) or oil.
    gas_plant_monthly_fuel_pricing: bool = False

    # Tier 3 (calibration) — "nearby plant" fuel-cost fallback. When True, a
    # coal/oil generator with no EIA-923 delivered cost of its own for a
    # month is priced at the quantity-weighted average of the *other* plants
    # that did report — its own state first (when at least
    # ``nearby_fuel_price_min_state_plants`` plants reported there), else its
    # model zone — before dropping to the coal / oil trajectory. (Gas no longer
    # uses per-plant monthly costs by default — see
    # ``gas_plant_monthly_fuel_pricing`` — so this fallback only shapes gas when
    # that flag is explicitly turned back on.) Off by default. See
    # market_sim.data.fuel.apply_plant_monthly_fuel_prices.
    nearby_fuel_price_fallback: bool = False
    nearby_fuel_price_min_state_plants: int = 2  # state-mean sample floor;
    #   below it the broader model-zone mean is used instead.

    # Tier 3 (calibration) — keep the non-ERCOT fleet at full per-plant
    # granularity (no efficiency-bin aggregation) so each generator retains
    # its EIA plant code, plant group and state. Required for the per-plant
    # EIA-923 fuel cost and the historic CAMPD outage overlay to bind to real
    # plants; without it the fleet collapses to ~100 representative bins with
    # no plant identity. Off by default (forward runs keep the aggregated,
    # faster fleet); the calibration harness turns it on for non-ERCOT ISOs.
    # ERCOT is unaffected — it builds its fleet from CAMPD bins, not this path.
    plant_level_fleet: bool = False

    # Tier 3 (calibration) — give the non-ERCOT per-plant gas fleet a stepped
    # offer curve (committed/economic/peaking heat-rate bands) instead of a
    # single flat block, via split_gas_tranches. Off by default so the present
    # calibration is unchanged; enabling it shifts the gas merit order (part-
    # load units bid up, efficient units down) and wants a tuning pass on the
    # _GAS_TRANCHE_SHARES. ERCOT's offer curve comes from its CAMPD bins.
    gas_offer_curve: bool = False

    # Tier 3 — pumped-storage dispatch adder ($/MWh discharged), the
    # reduced-form opportunity cost of PS reserve/regulation duty the
    # energy-only LP does not see. ``None`` (default) resolves per ISO from
    # constants.PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO, which is empty for every
    # ISO — PS arbitrages on its physical RTE like every other storage
    # resource (see that constant for the per-ISO retirement history). A
    # number here overrides the per-ISO default for every ISO in the scenario
    # (scenario lever, not a calibration fit).
    pumped_storage_dispatch_adder: float | None = None

    # Tier 3 — grid-battery throughput/cycling cost ($/MWh discharged), the
    # battery analogue of pumped_storage_dispatch_adder. Two real costs the
    # energy-only LP otherwise ignores: cycling degradation (cell-replacement
    # capex amortized per MWh discharged — ~$15-25/MWh for li-ion at current
    # pack prices, NREL "Utility-Scale Battery Storage" ATB 2024 cycle-life
    # basis; the original cycle-aging literature put it at $25-50/MWh — Xu,
    # Zhao, Zheng, Litvinov & Kirschen 2018, "Factoring the Cycle Aging Cost
    # of Batteries Participating in Electricity Markets", IEEE Trans. Power
    # Systems 33(2)) and the ancillary-service opportunity cost of
    # arbitraging instead of holding reserve (the dominant ERCOT BESS
    # revenue stream through 2024, ERCOT ESR reports). With no adder the LP
    # cycles the fleet every day the spread clears RTE losses (~1.2-1.3
    # cycles/day) where the observed ERCOT fleet ran ~0.7-0.8 (EIA-930 BAT
    # discharge vs EIA-860 fleet energy).
    # Default 0.0 = prior behaviour; calibration backcasts set it (see
    # docs/calibration-best-so-far.md).
    battery_dispatch_adder: float = 0.0

    # Tier 3 (calibration) — price gas at the ISO's measured EIA-923 monthly
    # volume-weighted delivered cost instead of annual Henry Hub + basis ×
    # the generic seasonality shape. One hub-level price per month (per-plant
    # gas stays off — same-zone units never split on patchy reporting), so
    # real winter events the fixed shape damps (PJM Jan-2024: $5.07 measured
    # vs ~$2.5 shaped) reach the merit order. Off by default so the present
    # ERCOT calibration is unchanged; backcast-only by construction (forward
    # years have no F923 rows and keep the trajectory).
    gas_monthly_actuals: bool = False

    # Tier 3 (calibration) — replace the generic climatological monthly gas
    # SHAPE (GAS_MONTHLY_SEASONALITY) with the MEASURED Henry Hub monthly
    # shape for the year, hour-weight-normalized so the annual mean stays
    # exactly the trusted annual level (fuel.gas_seasonal_shape). The
    # reconciled variant the Run-77 postmortem named: the raw EIA-923
    # receipt LEVEL swap was rejected for ERCOT (the ~20%-coverage reporter
    # sample runs ~+$1/MMBtu above the merchant hub), but the measured
    # month-to-month shape is real — the generic shape holds Feb/Mar-2024
    # ~$0.7/MMBtu too dear (post-Heather gas collapsed to $1.49-1.72 vs the
    # shaped $2.23-2.41) and Jan-2024 $0.66 too cheap. Measured commodity
    # price input (delivered fuel prices, rule #12): forward years have no
    # HH rows and keep the generic shape (the futures-shape analogue), and
    # the shape responds to conditions. Off by default (byte-identical).
    gas_hh_monthly_shape: bool = False

    # Inject the measured Henry Hub *daily* within-month shape onto the gas
    # series (fuel.gas_daily_shape_factors): the monthly delivered level is
    # unchanged (factors normalize to 1.0 per month), but the merit order sees
    # the real day-to-day commodity swing — cheap shoulder days and cold-snap
    # spikes — instead of one flat price per month. Physics input correctness,
    # applied before any offer-curve tuning; works in forecast too (a forward
    # monthly level times a representative daily shape).
    gas_daily_shape: bool = False

    # Tier 3 (calibration) — measured hub-month gas basis overlay (doc-08
    # NEISO P7). In months with a measured hub basis row in
    # data/raw/gas_basis_by_iso_month.csv (NEISO: Algonquin Citygate
    # via the ISO-NE MA gas index, 2023-2025), every gas unit's fuel price
    # is REPLACED by measured Henry Hub monthly + the measured hub basis —
    # the constrained-hub spot is the marginal gas unit's opportunity cost,
    # far above plant-average EIA-923 receipts in Dec-Feb blowouts (Jan-25
    # AGT basis +$12.79/MMBtu) and the better measurement where Schedule-5
    # gas reporting is near-empty (two NEISO reporters). Supersedes the
    # ISO-month and per-plant F923 gas passes in covered months; runs before
    # the dual-fuel min so oil parity still caps the winter spike. Off by
    # default so ERCOT/PJM/CAISO and all forecasts are unchanged; the
    # calibration harness enables it for NEISO. Backcast-only by
    # construction (no basis rows in forward years). See
    # market_sim.data.fuel.apply_hub_basis_overlay.
    gas_hub_basis_overlay: bool = False

    # Tier 3 (calibration) — NYISO per-zone gas-hub basis. NYISO's regions price
    # gas off different pipeline indices (cheap Tenn Z4 200L / Niagara upstate,
    # dearer Iroquois Z2 / Tenn Z6 in the Capital/Hudson east, Transco Z6 NY in
    # the city), so the east marginal gas costs persistently more than the west
    # all year — the structural source of the upstate-cheap / east-dear LMP
    # gradient that a single ISO-month series flattens. When set, every NYISO
    # gas unit is shifted by its zone's measured hub offset vs the east
    # reference (Iroquois Z2), so the calibrated east level is unchanged and the
    # cheaper west/city zones drop. Off by default so other ISOs and all
    # forecasts are byte-identical; the calibration harness enables it for
    # NYISO. Backcast-only (no hub rows in forward years). See
    # market_sim.data.fuel.apply_nyiso_zonal_gas_basis.
    nyiso_zonal_gas_basis: bool = False

    # ---- NYISO downstate-peaker structural pricing (2026-07, issue #1344 /
    # ---- B-NYI-1 de-leak follow-up). New fields added as one contiguous block.
    #
    # Tier 3 (calibration) — NYISO downstate interruptible city-gate gas premium
    # for CT peakers. NYISO's downstate combustion-turbine peakers (NYC zone J +
    # Long Island zone K, the CT_PEAKER LM6000 fleet) run only a few hundred
    # hours a year, so they hold no firm interstate pipeline capacity and take
    # gas off the local LDC (Con Edison / National Grid / KeySpan) city gate on
    # interruptible service. Their delivered fuel index is the LDC city gate, not
    # the interstate pipeline hub the model prices downstate gas at (Transco Z6
    # NY via gas_monthly_actuals + the hub-basis overlay). Pricing the peakers at
    # the pipeline hub lets an HR~9-10 LM6000 undercut the HR~11-12 downstate
    # steam fleet and run near-baseload year-round (dominated by the Long Island
    # gas-island peakers) — the CT_PEAKER over-run the B-NYI-1 offer de-leak
    # exposes. When set, each downstate CT_PEAKER unit's delivered gas is lifted
    # from the pipeline hub to its LDC-delivered index by the MEASURED monthly
    # premium (EIA NG NY city-gate N3050NY3 minus the measured Transco Z6 NY hub,
    # floored 0; positive year-round, widening in summer; a delivered fuel price,
    # rule #13's canonical admissible input — regenerates for a forward year and
    # responds to changed conditions). Off by default so other ISOs and all
    # forecasts are byte-identical; the calibration harness enables it for NYISO.
    # Backcast+forecast reproducible. See
    # market_sim.data.fuel.apply_nyiso_downstate_ct_gas_basis.
    nyiso_downstate_ct_gas_basis: bool = False

    # Tier 3 (calibration) — DAILY re-grounding of the same downstate CT-peaker
    # delivered-gas index. Supersedes nyiso_downstate_ct_gas_basis (the
    # monthly-premium adder) for the same class: instead of lifting the
    # pipeline-hub MONTHLY base by the monthly LDC premium, each downstate
    # CT_PEAKER unit's delivered gas is SET directly to the curated DAILY
    # delivered-gas index = measured Transco Z6 NY pipeline-hub daily spot +
    # measured monthly LDC city-gate premium (the nyiso-downstate-gas curated
    # datatype; free-data memo §1.4). The daily Transco spot captures the
    # cold-snap blowouts (Jan-2024 $23.90) on the exact days the interruptible
    # peakers actually run, which the monthly mean smears away — a strictly more
    # measured, forward-native re-grounding (rules #11/#13), never a fitted band.
    # The dual-fuel oil-parity min still caps any winter spike (runs after).
    # Off by default; set nyiso_downstate_ct_gas_basis=False when this is on
    # (one mechanism per phenomenon, rule 19). See
    # market_sim.data.fuel.apply_nyiso_downstate_ct_gas_daily.
    nyiso_downstate_ct_gas_daily: bool = False

    # Tier 3 (calibration) — PJM per-zone gas basis. PJM is priced off a single
    # ISO-wide delivered-gas series, so every gas-CC carries the same marginal
    # cost, all 8 zones clear at one LMP (0.000 zonal spread in every hour), no
    # zone wants cheaper power from a neighbour, and the internal TTCs
    # (ComEd→AEP, AEP→Dominion, Central_PA→EMAAC, SWMAAC→EMAAC, …) never bind —
    # PJM collapses to one copper-plate. That flattens the real west-cheap /
    # east-dear gas gradient: the eastern load pockets (EMAAC/SWMAAC/Dominion,
    # ~38% of load) burn dear Transco Z6 / TETCO M3 gas but are priced at the
    # cheap ISO average, so eastern CC_REGULAR over-runs and pins the price low,
    # undercutting the western bituminous coal belt (AEP_Ohio + West_APS carry 94%
    # of PJM bit) and pushing PJM to clear below its neighbours (over-export).
    # When set, each PJM gas unit is shifted by its zone's measured basis vs Henry
    # Hub (data/raw/pjm_zonal_gas_hub.csv — the EIA delivered-to-electric-power
    # price by the zone's primary state, a forward-reproducible measured series),
    # re-centred to a gas-capacity-weighted mean of zero so the calibrated
    # fleet-aggregate gas level is preserved and ONLY the cross-zonal split moves
    # (the western coal belt gets cheaper, the eastern pockets dearer). Mirrors
    # the ERCOT capacity-weighted-zero anchor (not the NYISO single-reference
    # anchor), with no level correction since PJM's level is already calibrated by
    # the ISO-month actuals. Off by default so other ISOs and all forecasts are
    # byte-identical; the calibration harness enables it for PJM. Backcast-only
    # (no hub rows in forward years). See
    # market_sim.data.fuel.apply_pjm_zonal_gas_basis.
    pjm_zonal_gas_basis: bool = False

    # MISO per-zone delivered-gas basis spread. MISO's three zones sit on different
    # pipeline hubs (North on MidCon / Northern Natural, Central on Chicago
    # Citygate, South on Gulf Coast LA), so flattening to one ISO-wide gas price
    # mis-prices the north/south gradient. This adds each zone's measured
    # EIA-delivered basis vs Henry Hub as a mean-zero capacity-weighted spread,
    # identical to the PJM mechanism. Off by default; the calibration harness
    # enables it for MISO. See market_sim.data.fuel.apply_miso_zonal_gas_basis.
    miso_zonal_gas_basis: bool = False

    # CAISO per-zone citygate-hub gas basis spread. CAISO's zones buy from two
    # separately traded LDC citygate hubs — NP15/ZP26 on PG&E Citygate, SP15 on
    # SoCal Citygate — but the model prices every zone off the single blended
    # CA-composite series, so the gas fleets are equally cheap and the LP
    # develops no systematic north-south dispatch gradient (its NP15/ZP26 clear
    # byte-identical prices and its N-S LMP basis carries the wrong sign vs the
    # measured hub LMPs). This adds each zone's measured hub basis vs Henry Hub
    # (data/raw/caiso_zonal_gas_hub.csv — month-balanced annual means of the
    # EIA NG Weekly archive's weekly Wednesday prints, NGI Daily GPI; the same
    # published print the ERCOT Waha rows cite) as a mean-zero capacity-weighted
    # spread, identical to the PJM/MISO mechanism, preserving the calibrated
    # composite+transport aggregate level. Measured N-S spread (PG&E − SoCal):
    # −0.49 / +0.54 / −0.18 $/MMBtu (2023/24/25) — year-varying measured data,
    # not a fitted north-premium knob. Off by default so every existing CAISO
    # keeper replay is byte-identical. Backcast-only (no hub rows in forward
    # years). See market_sim.data.fuel.apply_caiso_zonal_gas_basis.
    caiso_zonal_gas_basis: bool = False

    # CAISO asymmetric measured Path 15 / Path 26 directional ratings. The
    # internal N-S links carry symmetric TTCs (5,400 / 4,000 MW) although each
    # is only ONE direction's WECC-accepted rating: Path 15 (Midway–Los Banos)
    # is 3,265 MW N→S / 5,400 MW S→N and Path 26 (Midway–Vincent) is 4,000 MW
    # N→S / 3,000 MW S→N (WECC Path Rating Catalog, 2024 public version). The
    # loose directions let the LP equalize the zones (Path 15 never binds;
    # NP15==ZP26 byte-identical all years) and ship the south's midday solar
    # surplus north past the real 3,000 MW Path-26 S→N limit, suppressing the
    # measured NP15-over-SP15 LMP premium. When on, two InterfaceLimit rows cap
    # each path's directional flow at the published rating (the per-link TTC
    # keeps the looser direction). Measured data over estimate (rule 14); off
    # by default so every existing CAISO keeper replay is byte-identical. See
    # market_sim.model.transmission.apply_caiso_asymmetric_path_limits.
    caiso_asymmetric_path_ratings: bool = False

    # CAISO per-year SP15-pocket import caps. The SP15-split foundation
    # (2026-07-09) baked the two internal import-limited links
    # (SP15_rest->LA_BASIN, SP15_rest->SDGE) at the STATIC 2023 (tightest-year)
    # LCT import_cap = peak_load - requirement (LA_BASIN 12,008 MW, SDGE 1,436
    # MW), documenting per-year as the deferred end state (docs/handoffs/
    # caiso-sp15-split-implementation-scope-2026-07-09.md, "Import-cap values").
    # When on, each solve year's link TTC is swapped to that year's measured
    # LCT row (LA_BASIN 12,008/15,224/15,174, SDGE 1,436/2,074/2,071 MW for
    # 2023/24/25 -- data/raw/capacity-deliverability/caiso/caiso.csv via
    # data.local_capacity.load_lcr_parameters), same peak_load - requirement
    # convention, frozen per rule 24 (never the reserve-margin gross-up, never
    # tuned to a residual). A no-op for any year without a published LCT row
    # (the link keeps its static 2023 default). Off by default so every
    # existing CAISO keeper replay is byte-identical. See
    # market_sim.model.transmission.apply_caiso_local_import_limits.
    caiso_per_year_import_caps: bool = False

    # PJM transmission-congestion lever (break the copper-plate). PJM clears as a
    # perfect single price (0.000 zonal LMP spread in all 8760 hours of all
    # backcast years) because the priced external star node (PJM_external) wires
    # ~30 GW of uncongested transfer to 5 border zones — the dear-east load
    # pockets import directly from one price hub and never pull power through the
    # internal west→east lines — and the internal interface TTCs are loose Tier-3
    # estimates that never bind. When set (PJM only, requires the priced-
    # interchange external node), each PJM_external→border link's signed flow is
    # capped per hour at the measured per-border net-interchange envelope
    # (constants.PJM_EXTERNAL_FLOW_PERCENTILE,
    # eia_loader.pjm_zonal_interchange_envelope) and the internal interfaces with a
    # confident measured mapping are tightened to their measured transfer-limit
    # postings (constants.PJM_MEASURED_INTERNAL_TTC). The hub can no longer flood
    # the east with cheap imports, so the interior zones source western power
    # across the now-binding internal cuts: eastern LMP separates up, western coal
    # runs to serve the east, and the over-export shrinks toward the measured
    # schedule. Measured PJM transfer/interchange data, forward-reproducible, no
    # residual tuning (rules #11/#12). Off by default (every other ISO and all
    # forecasts byte-identical); the calibration harness enables it for PJM. See
    # market_sim.model.transmission.build_pjm_external_flow_groups.
    pjm_congestion: bool = False

    pjm_seam_flow_limit: bool = False  # PJM reference-price seam: the PJM
    # analogue of miso_seam_flow_limit. Cap each of PJM's 5 reference-price
    # seams' (MISO/NYISO/Carolinas/TVA/LGEE) import-band availability at the
    # MEASURED per-neighbor deliverability envelope from the PJM tie-line file
    # (border zones summed to neighbor level, per (month × hour-of-day) p90 of
    # the directed flow; transmission.inject_pjm_seam_flow_limit). Fixes the
    # structural over-import: the priced seam imports at the interface limit on
    # every border whenever PJM's LMP exceeds the neighbor's, but in reality
    # each seam has a bounded deliverable transfer. An ATC/transfer-capability
    # proxy from the directed-flow series — reproducible for a forward year and
    # flow-responsive — NOT fitted to the net-MWh residual (rules #1/#12).
    # Requires --reference-price-interface; PJM-only (no seam map → no-op,
    # byte-identical for other ISOs). Default off; opt-in per run.
    pjm_seam_flow_percentile: float | None = None  # Override the per-seam
    # deliverability percentile used by pjm_seam_flow_limit. None keeps the
    # constants.PJM_SEAM_FLOW_PERCENTILE default (90). Raising it (e.g. 95)
    # lifts the deliverability envelope toward the measured upper-tail transfer,
    # letting the priced seam clear more in tight hours. Still a deliverability
    # ceiling from the measured directed-flow duration curve, NOT a flow pinned
    # to the net-MWh residual (rules #1/#12). Used only when pjm_seam_flow_limit
    # is set; PJM-only; default keeps p90 (byte-identical).
    pjm_seam_export_limit: bool = False  # PJM reference-price seam: the EXPORT
    # mirror of pjm_seam_flow_limit. Cap each seam's net EXPORT at the MEASURED
    # per-neighbor export deliverability envelope (raising the negative-output
    # export bands' lower bound / min_gen toward 0;
    # transmission.inject_pjm_seam_flow_limit(direction="export")). Fixes the
    # structural over-EXPORT: the reference-price interface exports at full TTC
    # on all 5 seams simultaneously whenever a neighbor's price exceeds PJM's,
    # producing ~38 TWh net export regardless of actuals, but each seam has a
    # bounded deliverable export path. An ATC/transfer-capability proxy from the
    # directed-flow series — reproducible for a forward year and flow-responsive
    # — NOT fitted to the net-MWh residual (rules #1/#12). Shares the
    # pjm_seam_flow_percentile knob with the import cap (one p90 envelope, both
    # directions). Requires --reference-price-interface; PJM-only (no seam map →
    # no-op, byte-identical). Default off; opt-in.
    pjm_seam_measured_ladder: bool = False  # PJM reference-price seams: price
    # every seam band (MISO/NYISO/Carolinas/TVA/LGEE, import + export) at the
    # MEASURED per-year Q-Q band ladder
    # (interchange_config.PJM_SEAM_LADDER_BY_YEAR, derived by
    # scripts/derive_pjm_seam_ladders.py: PJM settlement-grade tie-line flow
    # duration curves coupled quantile-by-quantile with the measured PJM DA
    # system LMP — the MISO miso_seam_measured_ladder / NEISO audit-C-6
    # pattern), replacing the gas x HR x load-shape band prices + hurdle for
    # backcast years. Fixes the 2023 interchange duration miss (pjm-95 C1
    # root-cause lead): the measured PJM interchange is direction-STRUCTURAL —
    # export to MISO/NYISO in ~97-100% of ALL hours, import from
    # Carolinas/TVA/LGEE in 77-97% — firm PTP schedules revealed only
    # statistically, which the spot-spread seam inverts (model imports in 46%
    # of 2023 hours vs measured ~2%, diurnal corr -0.50; the phantom imports
    # displace CC_REGULAR dispatch). The ladder is the seam's revealed supply
    # curve: the LP still clears each band economically on ITS OWN hourly
    # price (nothing forced); band capacities and the measured per-border
    # (month x hod) envelopes (pjm_seam_flow_limit/pjm_seam_export_limit) are
    # unchanged. Measured-behaviour identification, frozen formula, zero
    # fitted parameters (rule 23); forward years keep the gas-elastic
    # reference-price formula (two-track, like hr_by_year; pooled ladder = the
    # forward story, see the registry comment). DISPLACES the firm
    # scheduled-export floor (inject_reference_price_firm_export) on the years
    # it covers — the floor pins the same deep-duration firm base the ladder
    # prices (alternatives, never stacked; rule 19). Requires
    # --reference-price-interface; PJM-only; no-op for years outside the
    # registry (byte-identical). Default off; opt-in per run.

    # Tier 3 (calibration) — ERCOT per-zone gas-hub basis. ERCOT's model zones
    # buy gas off structurally different regional hubs: West/Panhandle on Waha
    # (Permian, a deep takeaway-constrained discount — annual avg ~$0/MMBtu and
    # negative 42% of days in 2024), North/Northeast on the North/East-Texas
    # complex (~Henry Hub), Houston on the Houston Ship Channel (~HH), and
    # South_Central/South on the South-Texas hubs (a modest HH premium). The
    # single ERCOT scalar basis (GAS_BASIS_DIFFERENTIAL, the Waha discount
    # applied fleet-wide) flattens this gradient, so the merit order prices
    # DFW/North CCs (Midlothian, Wolf Hollow I, Wise) on the same cheap gas as
    # Permian CCs (Odessa-Ector, Quail Run) — over-running North/NE CCs and
    # under-running West/Permian and South CCs (a spatial reallocation, not a
    # level miss). When set, each ERCOT gas unit is shifted by its zone's
    # measured basis vs Henry Hub (data/raw/ercot_zonal_gas_hub.csv), re-centred
    # to a gas-capacity-weighted mean of zero so the calibrated fleet-aggregate
    # gas level (and the within-gas ST_GAS/CT/CC ledger) is preserved and only
    # the cross-zonal split moves; the level is anchored on the measured TX
    # delivered-to-electric-power gas price (EIA N3045TX3) rather than the flat
    # -0.50 Waha scalar, and the EIA-923 receipts supply only the (mean-zero)
    # zonal spread (so their regulated-utility level bias is dropped). NOT the TX
    # city-gate price (N3050TX3), which carries the LDC distribution margin
    # (~+$1.3/MMBtu) generators do not pay. DEFAULT-OFF DIAGNOSTIC — not a keeper lever:
    # the basis is measured and correct, but a 7-zone LP cannot model the
    # intra-Permian (<200 kV) transmission that, in reality, traps the cheap
    # Waha generation. Enabling it shrinks the North CC over-run (2024 +13.2 ->
    # +3.7 TWh) and fixes the West CC under-run, but RELOCATES the same
    # unmodelable nodal residual onto West/Permian CT peakers, which run
    # baseload on ~$0 Waha gas (2024 West CT +9.9 TWh) with no LMP gain — a CC
    # -> CT swap within the gas family, not a fit. So it is kept off in the
    # keeper (see docs/ercot-zonal-gas-basis-ct-relocation-2026-06.md). Off by
    # default so other ISOs and all forecasts are byte-identical. Backcast-only
    # (no hub rows in forward years). See
    # market_sim.data.fuel.apply_ercot_zonal_gas_basis.
    ercot_zonal_gas_basis: bool = False

    # Tier 3 (calibration) — delivered-gas floor on the ERCOT zonal basis above.
    # The West/Panhandle basis in data/raw/ercot_zonal_gas_hub.csv is a Waha *hub*
    # (pooling-point) basis (2024 -2.19): the takeaway-constrained price at which
    # Permian producers offload associated gas they cannot move, which goes
    # negative ~42% of days. A power plant does NOT buy at the wellhead/hub — it
    # buys *delivered* gas at the burner tip, paying intrastate pipeline
    # transport, fuel retention and a minimum commodity charge on top, so its
    # delivered cost has a structural positive floor regardless of how negative
    # the hub goes. Feeding the raw hub basis to the merit order prices the
    # West/Permian gas units (Morgan Creek, Laredo, Permian Basin, Ector County)
    # at ~$0/MMBtu, so they offer ~$0-5/MWh and run BASELOAD when in reality they
    # are peakers (CEMS CF <3% for Morgan Creek/Laredo) — the CT_PEAKER over-run.
    # The measured TX delivered-to-electric-power series (EIA N3045TX3, $2.11/MMBtu
    # in 2024 — the gen-weighted statewide level, which already includes the West
    # plants) is direct evidence that no TX power plant paid near $0 delivered.
    # When set, each gas unit's per-zone delivered discount (the mean-zero zonal
    # spread) is floored at this value — the cited measured Waha *delivered* basis
    # (constants.GAS_BASIS_DIFFERENTIAL["ERCOT"] = -0.50, "Waha discount; EIA NG
    # Weekly") — so the delivered price never falls below Henry Hub + measured EP
    # basis - 0.50. This is a transport-grounded physical floor, not a residual
    # fit: it is the same cited delivered Waha discount already used fleet-wide,
    # it regenerates for any forward year and tracks Henry Hub (admissibility test
    # #12), and it leaves every zone already above the floor (North, Houston, etc.)
    # untouched — only the unphysical deep-negative West tail is truncated. No-op
    # unless ercot_zonal_gas_basis is also on and iso == ERCOT. See
    # market_sim.data.fuel.apply_ercot_zonal_gas_basis.
    ercot_gas_delivered_floor_basis: float | None = None

    # Tier 3 (calibration) — MEASURED re-grounding of the West/Waha floor depth
    # above. The flat ercot_gas_delivered_floor_basis (-0.50) is a single cited
    # scalar; this replaces it with a *measured* haircut. Only the SPOT-purchased
    # fraction of a zone's gas sees the Waha hub collapse — the firm-contracted
    # fraction is priced off a term index and is insulated. When set, each zone's
    # hub basis is scaled by its EIA-923 Schedule-5 measured gas spot share
    # (scripts/derive_gas_takeorpay.py -> data/raw/_processed-legacy/
    # gas_takeorpay_ERCOT.csv, aggregated to zones by
    # market_sim.data.fuel.ercot_gas_spot_share_by_zone), so the West delivered
    # discount becomes spot_share x hub_basis — a measured fraction, not a chosen
    # constant (CLAUDE.md #11/#12). Composes with the scalar floor (haircut shrinks
    # the discount, floor caps any residual deep tail). No-op unless
    # ercot_zonal_gas_basis is also on, iso == ERCOT, and the receipt-derived share
    # is on disk (else the scalar floor alone applies). See
    # market_sim.data.fuel.apply_ercot_zonal_gas_basis.
    ercot_gas_contract_haircut: bool = False

    # Tier 3 (calibration) — MEASURED per-unit fuel correction. A handful of
    # CAMPD-binned combustion-turbine peakers are EIA-860 *Petroleum-Liquids*
    # (distillate/DFO) units that the bin sheet routes through the gas CT_PEAKER
    # class, so the LP prices them on cheap Waha gas and runs them baseload —
    # most visibly Morgan Creek (3492), an EIA-860 DFO GT the model floats at
    # ~92% CF against its real 1.6%. When set, every gas-CT bin whose EIA-860
    # technology is "Petroleum Liquids" is repriced on distillate
    # (OIL_PRICE_PER_MMBTU) instead of gas — the same oil-primary treatment the
    # legacy fleet already gives these units (see fleet.dual_fuel_plant_groups,
    # which excludes oil-primary switchers because "they are already modeled as
    # oil units"). This is a structural data-correctness fix keyed on the
    # measured EIA-860 energy source, NOT a residual adder: it regenerates for
    # any forward year from the same EIA-860 field and tracks the oil-price
    # trajectory (admissibility test #11/#12). The plant_group (CT_PEAKER) is
    # untouched, so reserve/must-run/offer-curve logic is unchanged — only the
    # fuel the unit burns changes. See market_sim.data.fleet.bins_to_fleet and
    # oil_primary_bin_plants.
    oil_primary_bin_fuel: bool = False

    # Tier 3 (calibration) — STRUCTURAL net-load-indexed West/Panhandle Waha gas
    # basis (the structurally-grounded replacement for the flat
    # ercot_gas_delivered_floor_basis scalar). The Waha hub is NOT a constant
    # annual discount: it collapses deeply negative precisely when regional
    # gas+power demand is LOW (shoulder/overnight oversupply, constrained Permian
    # takeaway) and firms up toward its normal delivered level when demand is
    # HIGH — i.e. the basis is anti-correlated with system net-load
    # (load - wind - solar), exactly the weather/demand driver the ST_GAS
    # reliability drag keys off (fleet.apply_gas_st_netload_drag_floor). A single
    # scalar (annual mean, or a chosen floor) flattens this: it prices a West
    # *peaker* — which burns only in high-net-load scarcity hours, when Waha is
    # firm — on the same ~$0 annual-mean gas as a West *baseload CC*, which burns
    # across all hours including the cheap collapse. That collapses the heat-rate
    # spread and floats the inefficient peakers at baseload (the CT_PEAKER
    # over-run). When set, the West/Panhandle gas units get a per-hour,
    # net-load-indexed gas price added on top of the annual zonal basis
    # (ercot_zonal_gas_basis), MEAN-ZERO over the year so the measured annual Waha
    # basis (data/raw/ercot_zonal_gas_hub.csv) is preserved exactly — it only
    # redistributes cost across hours: dearest at the highest-net-load hours
    # (toward ercot_west_gas_firm_basis), cheapest at the lowest. A peaker running
    # the top net-load hours then pays firm Waha and idles except in genuine
    # scarcity (real summer peaking preserved); a CC running all hours pays the
    # blended annual mean and stays baseload. This is a structural mechanism, not
    # a residual fit: it is a function of net-load (a load forecast + a VRE build,
    # so it regenerates for any forward year and responds to changed conditions —
    # more VRE lowers net-load and shifts the curve, admissibility #10/#12),
    # anchored on the *measured* annual Waha basis and the cited firm Waha
    # delivered level. No-op unless ercot_zonal_gas_basis is also on and
    # iso == ERCOT. See market_sim.data.fuel.apply_ercot_west_netload_gas_shape.
    ercot_west_netload_gas_shape: bool = False

    # The high-net-load asymptote of the net-load-indexed West basis above: the
    # Waha *delivered* basis vs Henry Hub during FIRM (high-demand) conditions,
    # the level a West plant pays in the scarcity hours its peakers actually run.
    # The one physical anchor of the shape (its amplitude is pinned so the
    # highest-net-load hour reaches Henry Hub + this basis); the rest of the curve
    # is fixed by preserving the measured annual mean. Defaults to the cited
    # normal Waha delivered discount (GAS_BASIS_DIFFERENTIAL["ERCOT"] = -0.50, EIA
    # NG Weekly) when the shape is on. Not tuned to a CT residual — it is the
    # firm-demand Waha level, accepted as-is. ERCOT only.
    ercot_west_gas_firm_basis: float | None = None

    # Optional override of the measured Waha negative-price-day frequency that
    # splits the net-load distribution into the COLLAPSED (lowest-net-load) and
    # FIRM (highest-net-load) regimes of the two-regime step above. When None (the
    # default), the collapse frequency comes from the endogenous oversupply model
    # (ercot_west_gas_endogenous_collapse) when that is on, else the per-year
    # measured value from the neg_day_freq column of data/raw/ercot_zonal_gas_hub.csv
    # (2024 EIA-authoritative at 0.42; 2023/2025 NGI counts), falling back to the
    # 2024 record (0.42) for years with no row. This is the measured *collapse
    # frequency*, not a tuning knob — set it only for diagnostic probes, never to
    # chase the CT_PEAKER residual. ERCOT only.
    ercot_west_gas_collapse_freq: float | None = None

    # Make the two-regime split frequency ENDOGENOUS (the forward analogue of the
    # measured neg_day_freq above — closing the last measured input of the West
    # net-load gas shape, gap G6). When on, collapse_freq is computed from forecast
    # West/Panhandle oversupply: the fraction of hours West+Panhandle wind+solar
    # generation exceeds local West load plus the region's export TTC
    # (WESTEX+PNHNDL) — i.e. how often the Permian basin is over-supplied and the
    # Waha hub crashes. Every input is a forecast quantity the model already builds
    # (the VRE capacity×CF, the load forecast, the transmission topology), so it
    # regenerates for any forward year and RESPONDS to changed conditions: more
    # West VRE -> more oversupply hours -> higher collapse frequency
    # (admissibility #10/#12). The measured neg_day_freq stays as the backcast
    # realization to validate against (logged alongside, never re-pinned). When
    # off, the legacy measured-read behaviour. The ercot_west_gas_collapse_freq
    # override still wins for diagnostic probes. ERCOT only; no-op unless
    # ercot_west_netload_gas_shape is also on.
    # See market_sim.data.fuel.ercot_west_oversupply_collapse_freq.
    ercot_west_gas_endogenous_collapse: bool = False

    # Burner-tip delivered floor ($/MMBtu) for the COLLAPSE regime of the
    # two-regime step. The Waha *hub* goes to ~$0 (and negative) on over-supply
    # days, but a plant's *delivered* gas never does: intrastate transport +
    # as-burned handling set a positive floor well above the hub. Flooring the deep
    # regime at the generic ~$0.10 gas floor (a hub-like number) creates a
    # cheap-hour magnet that pulls low-HR West CTs into the lowest-demand hours
    # (dispatch anti-correlated with load); the delivered burner tip must floor at
    # the transport-bound minimum instead. None keeps the generic floor (legacy).
    # A physical transport-bound input, not a CT residual fit. ERCOT only.
    ercot_west_gas_delivered_floor: float | None = None

    # Tier 3 (calibration) — daily resolution for the hub-basis overlay above
    # (doc-08 NEISO, the daily-AGT refinement of upload U4). When set (and
    # gas_hub_basis_overlay is on), the covered-month gas price is no longer a
    # flat monthly plateau (measured Henry Hub month + measured AGT month
    # basis) but a *daily* series: the measured Henry Hub daily within-month
    # shape plus the measured AGT daily basis, anchored to the real Algonquin
    # Citygate daily spot prints EIA publishes in its Weekly Update narrative
    # (data/raw/gas-prices/algonquin_citygate_daily.csv) and interpolated on
    # their true calendar days (sparse-print months borrow the measured Transco
    # Z6 NY daily-basis shape), mean-preserving per month so the monthly level —
    # and the annual gas burn / fuel mix — is unchanged. This is what trips the
    # dual-fuel gas->oil switch and the oil-steam fleet on the coldest days
    # (the monthly average never reaches distillate parity) and produces the
    # ISO-NE winter LMP tail. Built entirely from real, free, EIA-sourced
    # gas-market data — it replaced the retired demand-convexity proxy
    # (AGT_DAILY_BASIS_CONVEXITY, which was fitted to the oil burn). Falls back
    # to the flat monthly overlay when no daily basis can be built. Off by
    # default; the calibration harness enables it for NEISO. See
    # market_sim.data.fuel.iso_hub_daily_gas_prices and
    # docs/multi-iso/neiso-data-audit.md.
    gas_hub_basis_daily: bool = False

    # Tier 3 (calibration) — re-attribute dual-fuel switched generation to oil
    # (doc-08 NEISO §2d). The dual-fuel switch (dual_fuel_switching) is
    # objective-only: a unit that switches to oil prices at min(gas, oil) but
    # the LP dispatches it on the gas heat-rate and its MWh would otherwise be
    # reported as gas. When set, the calibration relabels the switched
    # generator-hours (fuel.dual_fuel_switch_mask) as oil in the persisted
    # dispatch so modeled oil matches the EIA-930 NG:OIL column — an
    # LMP-neutral re-attribution (no LP/price change). Default-on for NEISO
    # only (its AGT hub overlay is what pushes winter gas past oil parity);
    # OFF for PJM/NYISO so their keepers stay byte-identical until their oil
    # re-attribution is separately validated (their dual-fuel units do switch
    # on their own winter gas, so enabling it would move their gas/oil split).
    # NYISO validated NEGATIVE (2026-07-04): the NYIS EIA-930 feed does NOT
    # move dual-fuel switch-hours out of ``NG: NG`` (Jan-2025 parity switching
    # would relabel 0.80 TWh while the measured NYIS ``NG: OIL`` carried
    # 0.031 TWh; conversely 2023 shows 2.17 TWh OIL against a 0.42 TWh
    # EIA-923 oil class — a static plant-primary attribution parity hours
    # cannot reproduce), so relabelling scores a basis mismatch against the
    # C2 gas family, not a dispatch error. Keep OFF for NYISO.
    dual_fuel_oil_reattribution: bool = False

    # Tier 3 (calibration) — dual-fuel switching (doc 03 Pack G). Gas units
    # flagged oil/gas switch-capable in EIA-860 ("Switch Between Oil and
    # Natural Gas?" on the Multifuel schedule) price their fuel at
    # min(gas, oil) per hour, so when the delivered gas price spikes past
    # oil parity the unit bids on its backup distillate/residual cost instead
    # of being priced out — the winter fuel-switching behaviour central to
    # PJM/NYISO/ISO-NE cold snaps. Objective-only (an assemble_mc fuel-price
    # extension, no LP structural change); emissions/heat rate stay on the
    # gas characterization. Off by default so ERCOT (no dual-fuel fleet
    # behaviour) and existing forecasts are unchanged; the calibration
    # harness turns it on for the winter-switching cluster — PJM and the NE/NY
    # ISOs (NYISO downstate Ravenswood/Astoria/Bowline/Roseton/Northport CT/ST
    # units carry ~17 GW of EIA-860-flagged oil backup; NEISO's Algonquin-spot
    # marginal gas). See docs/multi-iso/nyiso-data-audit.md (P13).
    dual_fuel_switching: bool = False

    # Tier 3 (calibration) — thermal availability source. "statistical"
    # (default) builds coal/CC availability from the seasonal WEFOR/POF model;
    # "historic" additionally overlays actual ERCOT outages (coal/CC plants,
    # > 10-day spans) for the weather year as a hard zero, pinning units that
    # were physically out for sustained maintenance. Backcasts set "historic"
    # to cut calibration noise; forecasts keep "statistical". See
    # market_sim.data.outages and generators_to_fleet_arrays.
    outage_source: str = "statistical"

    gas_price_override: float | None = None  # When set, pins the annual
    # Henry Hub price ($/MMBtu) to a measured value instead of the AEO
    # trajectory — used to backcast a calibration year against EIA actuals.
    # NOTE: this no longer signals backcast mode; set ``mode="backcast"``
    # explicitly. A forecast may pin gas as a sensitivity without flipping
    # the renewables loader into historical-actuals mode.

    def __post_init__(self) -> None:
        if self.mode not in ("forecast", "backcast"):
            raise ValueError(
                f"ScenarioConfig.mode must be 'forecast' or 'backcast', "
                f"got {self.mode!r}"
            )
        from market_sim.config.constants import HYDRO_YEAR_MULTIPLIER

        if self.hydro_year not in HYDRO_YEAR_MULTIPLIER:
            raise ValueError(
                f"ScenarioConfig.hydro_year must be one of "
                f"{sorted(HYDRO_YEAR_MULTIPLIER)}, got {self.hydro_year!r}"
            )

        if self.neighbor_hr_forward_skill not in (None, "elastic", "flat"):
            raise ValueError(
                "ScenarioConfig.neighbor_hr_forward_skill must be None, "
                f"'elastic', or 'flat', got {self.neighbor_hr_forward_skill!r}"
            )

        # gas_price_factor is a forecast-only uncertainty lever (PB-1 §2.1);
        # rule 13 forbids it ever becoming a backcast tuning channel that
        # scales the measured/AEO gas trajectory to chase a residual.
        if self.mode == "backcast" and self.gas_price_factor != 1.0:
            raise ValueError(
                "gas_price_factor is a forecast-only uncertainty lever and "
                "must be 1.0 in backcast mode (rule 13); got "
                f"{self.gas_price_factor!r}"
            )

        # Data-center load block (CX-4): forecast-mode-only scenario axis. A
        # non-"off" path in backcast mode is a hard error (rule 22 / memo §6):
        # a backcast pins measured load, so the DC block must never enter a
        # scored backcast. Also validates the path label.
        if self.datacenter_load_path not in ("off", "low", "mid", "high"):
            raise ValueError(
                "ScenarioConfig.datacenter_load_path must be one of "
                "('off', 'low', 'mid', 'high'), got "
                f"{self.datacenter_load_path!r}"
            )
        if self.mode == "backcast" and self.datacenter_load_path != "off":
            raise ValueError(
                "datacenter_load_path is a forecast-only scenario axis and must "
                "be 'off' in backcast mode (rule 22 holdout discipline): a "
                "backcast pins measured load, so the data-center block must "
                "never enter a scored backcast; got "
                f"{self.datacenter_load_path!r}."
            )

        # The two on-line-capacity envelope variants resolve the SAME LP row
        # from different derived tables (base decile vs extreme-peak-resolved);
        # setting both would be ambiguous about which table governs, so it is a
        # hard error rather than a silent precedence rule (rule 19: one
        # mechanism per phenomenon).
        if self.ercot_online_capacity_envelope and (
            self.ercot_online_capacity_envelope_extreme
        ):
            raise ValueError(
                "ercot_online_capacity_envelope and "
                "ercot_online_capacity_envelope_extreme are mutually exclusive "
                "variants of the same envelope row — set exactly one."
            )

        # Endogenous storage energy-vs-AS competition is priced *inside* the
        # reserve co-optimization: without it the flag would silently no-op
        # (and, worse, still suppress the exogenous storage AS credit in the
        # entry screen — rule 19 — leaving storage with zero AS value). Require
        # the co-opt so the mechanism it names is actually present.
        if self.ercot_storage_as_endogenous and not self.energy_reserve_coopt:
            raise ValueError(
                "ercot_storage_as_endogenous requires energy_reserve_coopt: the "
                "endogenous storage energy-vs-AS split is priced by the reserve "
                "co-optimization, which is off. Enable energy_reserve_coopt "
                "(ERCOT multi-product) or clear ercot_storage_as_endogenous."
            )
        # CAISO's reserve co-optimization (reserve_config._caiso_design, issue
        # #1492) is priced inside the shared reserve co-opt; without it the flag
        # would silently no-op (apply_reserve_coopt gates on energy_reserve_coopt
        # first). Require both so the mechanism the flag names is actually built.
        if (
            getattr(self, "caiso_scarcity_pricing", False)
            and self.energy_reserve_coopt
            and self.caiso_reserve_coopt
        ):
            raise ValueError(
                "caiso_scarcity_pricing and caiso_reserve_coopt are mutually "
                "exclusive (rule 19 — one mechanism per phenomenon): the "
                "post-solve overlay and the in-LP co-opt both price CAISO "
                "reserve scarcity. Enable one or the other, not both."
            )
        if self.caiso_reserve_coopt and not self.energy_reserve_coopt:
            raise ValueError(
                "caiso_reserve_coopt requires energy_reserve_coopt: the CAISO "
                "energy+reserve co-optimization is priced by the reserve co-opt, "
                "which is off. Enable energy_reserve_coopt or clear "
                "caiso_reserve_coopt."
            )
        # The duration gate bounds the ENDOGENOUS storage split by SOC; it is
        # meaningless (and silently no-ops) without the endogenous split, and
        # must NEVER combine with the measured award reservation (docking the cap
        # AND netting the requirement, then gating, would triple-treat storage).
        if self.ercot_storage_as_duration_gate and not self.ercot_storage_as_endogenous:
            raise ValueError(
                "ercot_storage_as_duration_gate requires ercot_storage_as_endogenous: "
                "the duration gate bounds the endogenous storage AS split by state "
                "of charge; enable the endogenous split or clear the duration gate."
            )
        # Forecast multi-product AS requirement must regenerate from forward
        # drivers: the measured-plan fallback (ASPLANNP433) returns an all-zero
        # requirement for any year with no file, so a forecast co-opt without
        # ercot_as_forward_requirement would demand zero AS and withhold
        # nothing. (The single-product ORDC path is LOLP×VOLL, forward-safe, so
        # this is scoped to the multi-product AS co-opt.)
        if (
            self.mode == "forecast"
            and self.ercot_storage_as_endogenous
            and self.ercot_multiproduct_as_coopt
            and not self.ercot_as_forward_requirement
        ):
            raise ValueError(
                "forecast ercot_storage_as_endogenous with "
                "ercot_multiproduct_as_coopt requires ercot_as_forward_requirement "
                "so the AS requirement regenerates from forward load/VRE drivers; "
                "the measured-plan fallback is zero for forecast years."
            )

        # Thermal AS reconciliation mirrors the storage one: the derived per-fuel
        # credit is read off the co-opt's reserve duals, so the co-opt must be on
        # (otherwise the flag would silently suppress the exogenous thermal credit
        # and leave thermal with zero AS value — rule 19).
        if self.ercot_thermal_as_endogenous and not self.energy_reserve_coopt:
            raise ValueError(
                "ercot_thermal_as_endogenous requires energy_reserve_coopt: the "
                "endogenous thermal AS credit is derived from the reserve "
                "co-optimization's duals, which is off. Enable energy_reserve_coopt "
                "(ERCOT multi-product) or clear ercot_thermal_as_endogenous."
            )
        if (
            self.mode == "forecast"
            and self.ercot_thermal_as_endogenous
            and self.ercot_multiproduct_as_coopt
            and not self.ercot_as_forward_requirement
        ):
            raise ValueError(
                "forecast ercot_thermal_as_endogenous with "
                "ercot_multiproduct_as_coopt requires ercot_as_forward_requirement "
                "so the AS requirement regenerates from forward load/VRE drivers; "
                "the measured-plan fallback is zero for forecast years."
            )

    @property
    def real_discount_rate(self) -> float:
        """Real discount rate via Fisher equation: (1+nominal)/(1+inflation) - 1."""
        from market_sim.config.constants import INFLATION_RATE

        return (1.0 + self.nominal_discount_rate) / (1.0 + INFLATION_RATE) - 1.0

    def cache_key(self) -> str:
        """Return a deterministic 16-char hash of the full config.

        Hashes the stored ``nominal_discount_rate`` field (``asdict`` covers
        it). ``real_discount_rate`` is a derived property, deterministic given
        ``INFLATION_RATE``, so it is not part of the hash.
        """
        payload_dict = asdict(self)
        # Fields added after the on-disk cache existed are dropped from the
        # hash when they hold their default value, so every pre-existing cached
        # run keeps its key. A non-default value DOES enter the key (a hindcast
        # or a narrowed horizon is a distinct scenario).
        defaults = ScenarioConfig()
        for name in _CACHE_KEY_OPTIONAL_FIELDS:
            if payload_dict.get(name) == getattr(defaults, name):
                payload_dict.pop(name, None)
        payload = json.dumps(payload_dict, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def with_overrides(self, **kwargs) -> "ScenarioConfig":
        """Return a copy of this config with the given fields replaced."""
        return replace(self, **kwargs)

    def _non_default_values(self) -> dict:
        """Return a dict of fields whose values differ from the defaults."""
        defaults = ScenarioConfig()
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if getattr(self, f.name) != getattr(defaults, f.name)
        }

    def to_yaml(self, path) -> None:
        """Write only non-default fields to a YAML file at ``path``."""
        Path(path).write_text(
            yaml.safe_dump(self._non_default_values(), sort_keys=True)
        )

    def to_yaml_full(self, path) -> None:
        """Write every field to a YAML file at ``path`` for reproducibility."""
        Path(path).write_text(yaml.safe_dump(asdict(self), sort_keys=True))

    @classmethod
    def from_yaml(cls, path) -> "ScenarioConfig":
        """Load a config from YAML, merging stored overrides onto defaults."""
        data = yaml.safe_load(Path(path).read_text()) or {}
        return cls(**data)

    @classmethod
    def as_zero_forcing_ablation(cls, cfg: "ScenarioConfig") -> "ScenarioConfig":
        """Return a copy of ``cfg`` with every MERCHANT floor/bridge neutralized.

        The zero-forcing ablation twin (audit §7 D-3 / CLAUDE.md rule 20): a
        reference solve with all merchant reliability/commitment floors, drags,
        bridges and availability haircuts OFF, KEEPING only the structural
        must-run set (nuclear must-run, CHP steam-following, coal take-or-pay).
        The keeper-vs-twin per-class delta quantifies what each floor buys — a
        delta explainable only as "the floor buys the residual" is an open
        root-cause item, not a calibrated parameter.

        The off-list is DERIVED from the D-2 mechanism registry
        (:func:`market_sim.data.floor_mechanisms.zero_forcing_field_overrides`),
        not hand-maintained here, so a newly added merchant floor mechanism is
        ablated by default. Only the fields that registry names are changed;
        every other knob (offer curves, fuel, fleet, interchange) is carried
        through unchanged so the twin isolates the floors. Applying this AFTER
        all per-ISO defaults and ``with_overrides`` forces the floors off
        regardless of how they were set — the CAISO ``ct_netload_drag`` /
        ``caiso_ra_mustoffer`` defaults are config-level, so only a config
        transform (not a False kwarg) can neutralize them.
        """
        from market_sim.data.floor_mechanisms import zero_forcing_field_overrides

        field_names = {f.name for f in fields(cls)}
        overrides = {
            k: v for k, v in zero_forcing_field_overrides().items() if k in field_names
        }
        return replace(cfg, **overrides)


# --- PB-1 uncertainty-lever resolvers -------------------------------------
# Pure, config-build-time resolvers for the probability-bounds levers
# (docs/handoffs/probability-bounds-plan-2026-07.md). Each pairs a discrete
# "_path" field (the §1 deterministic scenario-matrix axis) with a
# continuous "_percentile" field (the §2 multivariate sampler axis, 0.0=low,
# 0.5=mid, 1.0=high). At every field's neutral default the resolved value is
# byte-identical to today's behavior; a percentile only takes effect when
# moved off its neutral 0.5 midpoint, so the two axes never fight silently.

_PERCENTILE_BY_PATH_LABEL: dict[str, float] = {"low": 0.0, "mid": 0.5, "high": 1.0}
_NEUTRAL_PERCENTILE: float = 0.5


def _interpolate_low_mid_high(
    percentile: float, low: float, mid: float, high: float
) -> float:
    """Piecewise-linear interpolation across (0.0, 0.5, 1.0) -> (low, mid, high).

    Shared by every PB-1 "_percentile" lever (:func:`resolve_new_entry_costs`,
    :func:`resolve_demand_growth_rate`): 0.0 returns ``low``, 0.5 returns
    ``mid`` exactly, 1.0 returns ``high``, and values in between interpolate
    linearly on each half. Clamped to [0.0, 1.0] so an out-of-range draw
    cannot silently extrapolate past the cited low/high levels.
    """
    p = min(1.0, max(0.0, percentile))
    if p <= _NEUTRAL_PERCENTILE:
        frac = p / _NEUTRAL_PERCENTILE
        return low + (mid - low) * frac
    frac = (p - _NEUTRAL_PERCENTILE) / (1.0 - _NEUTRAL_PERCENTILE)
    return mid + (high - mid) * frac


def _effective_percentile(path_label: str, percentile: float) -> float:
    """Resolve the effective 0-1 percentile for a path/percentile field pair.

    The continuous ``percentile`` field wins whenever it has been moved off
    its neutral 0.5 midpoint (the sampler's job, PB-1 §2); otherwise the
    discrete ``path_label`` field's own selection is used (the scenario
    matrix's job, PB-1 §1). Both at their defaults resolve to 0.5 either way,
    so this is a no-op unless a caller actually sets one of the two levers.
    """
    if percentile != _NEUTRAL_PERCENTILE:
        return percentile
    return _PERCENTILE_BY_PATH_LABEL[path_label]


def resolve_new_entry_costs(config: "ScenarioConfig") -> dict[str, dict[str, float]]:
    """Return :data:`constants.NEW_ENTRY_COSTS` scaled by the tech-cost lever.

    Interpolates each technology's ``capex_per_kw`` and ``learning_rate``
    across :data:`constants.TECH_COST_MULTIPLIERS`' low/mid/high cases (NREL
    ATB 2024 Advanced/Moderate/Conservative) using the effective percentile
    from ``config.tech_cost_path``/``config.tech_cost_percentile`` (PB-1
    §1.1/§2.1). ``base_cf`` and ``lifetime_yr`` are untouched -- the tech-cost
    lever is a cost lever, not a performance one. At the neutral default
    ("mid"/0.5, multiplier 1.0 on every tech) this returns values identical to
    :data:`constants.NEW_ENTRY_COSTS`.

    Args:
        config: Scenario config supplying ``tech_cost_path`` and
            ``tech_cost_percentile``.

    Returns:
        A new ``{tech: {param: value}}`` dict, the same shape as
        :data:`constants.NEW_ENTRY_COSTS`.
    """
    from market_sim.config.constants import NEW_ENTRY_COSTS, TECH_COST_MULTIPLIERS

    percentile = _effective_percentile(
        config.tech_cost_path, config.tech_cost_percentile
    )
    resolved: dict[str, dict[str, float]] = {}
    for tech, costs in NEW_ENTRY_COSTS.items():
        scaled = dict(costs)
        multipliers = TECH_COST_MULTIPLIERS.get(tech)
        if multipliers is not None:
            for param in ("capex_per_kw", "learning_rate"):
                mult = _interpolate_low_mid_high(
                    percentile,
                    multipliers["low"][param],
                    multipliers["mid"][param],
                    multipliers["high"][param],
                )
                scaled[param] = costs[param] * mult
        resolved[tech] = scaled
    return resolved


def resolve_demand_growth_rate(config: "ScenarioConfig", year: int) -> float:
    """Return the demand growth rate for ``year`` under the PB-1 load lever.

    Selects the near/long era from ``constants.DEMAND_GROWTH_TRANSITION_YEAR``,
    then interpolates :data:`constants.DEMAND_GROWTH_RATES`' low/mid/high era
    rates at the effective percentile from ``config.demand_growth_path``/
    ``config.demand_growth_percentile`` (PB-1 §1.1/§2.1; both eras move
    together). Falls back to ``config.demand_growth_rate`` exactly as the
    legacy path-only lookup did, when the config's ISO or
    ``demand_growth_path`` has no entry in the table (e.g. MISO).

    Args:
        config: Scenario config supplying the ISO and both growth levers.
        year: Simulation year.

    Returns:
        The annual demand growth rate (fraction, e.g. 0.03 = 3%/yr).
    """
    from market_sim.config.constants import (
        DEMAND_GROWTH_RATES,
        DEMAND_GROWTH_TRANSITION_YEAR,
    )

    iso_rates = DEMAND_GROWTH_RATES.get(config.iso, {})
    path_rates = iso_rates.get(config.demand_growth_path)
    if not isinstance(path_rates, dict):
        return config.demand_growth_rate

    era = "near" if year <= DEMAND_GROWTH_TRANSITION_YEAR else "long"
    low = iso_rates.get("low", {}).get(era)
    mid = iso_rates.get("mid", {}).get(era)
    high = iso_rates.get("high", {}).get(era)
    if low is None or mid is None or high is None:
        return path_rates[era]

    percentile = _effective_percentile(
        config.demand_growth_path, config.demand_growth_percentile
    )
    return _interpolate_low_mid_high(percentile, low, mid, high)


# Underlying-field overrides per named policy bundle (PB-1 §1.2). "current"
# is empty -- every field keeps its own legislated-default value. IRA year
# offsets apply to every ira_*_last_year field uniformly.
_IRA_LAST_YEAR_FIELDS: tuple[str, ...] = (
    "ira_wind_solar_last_year",
    "ira_other_clean_last_full_year",
    "ira_other_clean_phaseout_end",
    "ira_h2_45v_last_year",
    "ira_ccus_45q_last_year",
)

_POLICY_BUNDLES: dict[str, dict] = {
    "current": {},
    "tight": {
        # RFF mid carbon path; IRA horizons extended +5yr (plan §1.2).
        "carbon_price_path": "mid",
        "ira_year_offset": 5,
    },
    "rollback": {
        # No federal carbon price (same as current); state programs frozen
        # off rather than left escalating -- the nearest existing-field
        # expression of "no further state-program pricing," since a genuine
        # flat-forward-freeze trajectory mechanism doesn't exist yet (a
        # disclosed simplification, PB-1 §1.2). IRA sunset pulled -2yr.
        "carbon_price_path": "zero",
        "state_carbon_pricing": False,
        "ira_year_offset": -2,
    },
}


def resolve_policy_bundle(config: "ScenarioConfig") -> "ScenarioConfig":
    """Resolve ``config.policy_bundle`` to its underlying fields (PB-1 §1.2).

    Returns a copy of ``config`` with ``carbon_price_path``,
    ``state_carbon_pricing``, and every ``ira_*_last_year`` field replaced
    per the named bundle -- a resolver, not hidden state, so the RESOLVED
    fields (not the ``policy_bundle`` label) are what a caller should record
    to ``run_config.json``. "current" overrides nothing and returns ``config``
    unchanged.

    Args:
        config: Scenario config supplying ``policy_bundle`` and the fields it
            resolves.

    Returns:
        ``config`` with the bundle's field overrides applied (or ``config``
        itself, unchanged, for "current").

    Raises:
        ValueError: If ``config.policy_bundle`` is not a registered bundle.
    """
    if config.policy_bundle not in _POLICY_BUNDLES:
        raise ValueError(
            f"ScenarioConfig.policy_bundle must be one of "
            f"{sorted(_POLICY_BUNDLES)}, got {config.policy_bundle!r}"
        )
    spec = _POLICY_BUNDLES[config.policy_bundle]
    overrides = {k: v for k, v in spec.items() if k != "ira_year_offset"}
    offset = spec.get("ira_year_offset", 0)
    if offset:
        for field_name in _IRA_LAST_YEAR_FIELDS:
            overrides[field_name] = getattr(config, field_name) + offset
    if not overrides:
        return config
    return replace(config, **overrides)


# Per-(ISO, coal supply) gas-keyed passthrough sigmoid defaults — the tuned
# curves behind the coal_*_passthrough_sigmoid toggles. Each entry reflects
# one specific coal supply chain in one market: the basin, rank, mine-mouth
# vs rail delivery and contract structure all shift where the coal-vs-gas-CC
# merit-order crossover sits, so a curve tuned in one ISO must never leak
# into another. ScenarioConfig fields left at None resolve from here
# (fuel.coal_sigmoid_params); explicit fields (CLI tuning flags) override
# entry-by-entry. An (iso, supply) pair absent here — and not fully
# specified by explicit fields — gets no sigmoid: the flat passthrough.
#
# Supply keys match coal_supply_class tags ("prb" / "subbituminous" /
# "bituminous" / "lignite" / "waste"), plus "prb_follower" for the ERCOT
# tiered low-must-run load-follower tier of the prb curve.
#
# G-26/C-1 disposition (docs/handoffs/scalar-remediation-plan-2026-07.md):
# R6 DOCUMENT-AND-KEEP — the gas-keyed passthrough MECHANISM is owner-
# sanctioned rule-#1 offer-curve scope (a real take-or-pay/mine-mouth coal
# contract makes fuel cost mostly fixed, so a plant's bid should track its
# OWN sunk cost, not chase the marginal gas-CC price up or down), but the
# specific per-(ISO,supply) floor/ceil/gas_mid/gas_slope numbers below were
# tuned run-by-run against each ISO's backcast (documented inline per entry)
# and are only weakly identified (D-8: each asymptote is pinned by a single
# gas regime — floor by the cheapest observed year, ceil by the dearest —
# docs/out-of-sample-results-2026-07.md §2C). Two distinct physical stories
# are in play, and neither is a numbers change here (documentation of
# plausibility only): (1) COST-TRACKING basins whose delivered fuel cost does
# NOT follow the gas index (mine-mouth/rail PRB and mine-mouth lignite in
# MISO) must carry ceil <= 1.0 — the sigmoid may only ever DISCOUNT the bid
# toward sunk cost, never mark it up past full cost, since there is no gas-
# indexed contract escalator to justify a markup (the MISO PRB/bituminous
# entries below were fixed to ceil <= 1.0 for exactly this reason after run
# 30); (2) OPPORTUNITY-COST bidding basins (ERCOT's PRB-by-rail entries,
# ceil > 1.0) price toward the gas-CC breakeven to capture margin while
# staying in merit, a genuine strategic-bidding story distinct from (1) — but
# the two stories being applied inconsistently by ISO, with no single
# documented rule for which basin gets which, is itself part of the D-8 weak-
# identification finding. Full re-derivation from cited coal-contract-
# structure data (EIA-923 Schedule-5 fuel-cost dispersion / take-or-pay
# share) is tracked, not done here; open:
# https://github.com/jessicacohen554-cyber/market-simulator/issues/1347.
COAL_SIGMOID_DEFAULTS: dict[tuple[str, str], dict[str, float]] = {
    # ERCOT PRB-by-rail (curated COAL_PLANT_SUPPLY tags): per-month
    # PRB-vs-gas-CC breakeven across 2023-2025 (run-70s tuning series).
    ("ERCOT", "prb"): {"floor": 0.78, "ceil": 1.50, "gas_mid": 2.85, "gas_slope": 2.5},
    ("ERCOT", "prb_follower"): {
        "floor": 0.68,
        "ceil": 1.35,
        "gas_mid": 2.85,
        "gas_slope": 2.5,
    },
    # Safety net for any future ERCOT coal plant that misses the curated map
    # and lands on the derived "subbituminous" rank tag: mirror the prb
    # baseload curve (PRB IS sub-bituminous; same basin economics in ERCOT).
    ("ERCOT", "subbituminous"): {
        "floor": 0.78,
        "ceil": 1.50,
        "gas_mid": 2.85,
        "gas_slope": 2.5,
    },
    # ERCOT mine-mouth lignite, derived from the run-80 flat-reprice
    # anchors: a $1.15/MMBtu flat probe ≈ passthrough 0.79 fixed 2023, a
    # $1.05 ≈ 0.72 fixed 2024, and 2025 wants ~full cost — a sigmoid on the
    # PRB midpoint/slope with floor 0.70 and ceil 1.00 (no dear-gas markup)
    # lands all three. The delivered-price constant stays grounded at the
    # measured ~$1.45/MMBtu; this discounts the BID, not the cost.
    ("ERCOT", "lignite"): {
        "floor": 0.70,
        "ceil": 1.00,
        "gas_mid": 2.85,
        "gas_slope": 2.5,
    },
    # PJM bituminous (Appalachian/Illinois Basin): brackets the per-month
    # bit-vs-gas-CC breakeven across PJM 2023-2025 (~0.5 at $2.2/MMBtu gas
    # to ~1.7 at $6.9) conservatively — a moderate pull toward breakeven,
    # not full price-taking. Ceiling 1.25 -> 1.32 (PJM run 16): trims the
    # dear-gas-2025 BIT over-run (+6.3 -> +3.3 TWh) while the cheap-gas
    # 2024 passthrough moves <0.01, leaving 2024 BIT at-actual. Floor
    # 0.82 -> 0.80 (run 19): the export-sink reprice deepened the cheap-
    # hour price trough and bled 2023/24 BIT (-4.8 TWh in 2024); a 2%
    # deeper cheap-gas discount restores bit's near-tied committed/econ
    # blocks against gas CC on the plateau.
    # Floor 0.80 -> 0.76 (2026-06-17, on the pjm_27_aswh reserve-withholding
    # baseline): a 4% deeper cheap-gas discount (bituminous bidding toward its
    # take-or-pay/avoidable cost to hold merit under cheap gas) pulls coal
    # toward EIA-930 in every year — 2024 (cheapest gas, $2.19) -8.1% -> -5.8%,
    # 2023 -4.7% -> -2.7%, 2025 (dear gas, near gas_mid) -1.7% -> -1.0%; gas
    # 2024 +4.6% -> +3.9%. Gas-keyed, so it self-targets the cheap-gas years
    # and leaves the dear-gas ceiling untouched. (scripts/probes/_pjm_bit_floor_probe.)
    # MISO coal sigmoids — RE-DERIVED 2026-07-09 from measured coal-commodity
    # price by `scripts/derive_coal_sigmoid.py`, retiring the ERCOT byte-copies
    # (the old MISO entries reused ERCOT's gas_mid 2.85 / gas_slope 2.5 with
    # hand-tuned floor/ceil — the rule-24 wart flagged as #1347 / gap G-26).
    # Rule-23 trigger: the #1803 intake added the EIA Annual Coal Report region
    # f.o.b.-mine price + BLS PPI coal-mining series that a real re-derivation
    # needs (data/raw/coal-prices/; docs/handoffs/coal-price-data-intake-2026-07.md,
    # coal-sigmoid-rederive-2026-07.md). NOT re-tuned to any MISO residual — the
    # honesty gate. Each parameter is grounded (derive-script docstring):
    #   gas_mid  = coal-vs-gas-CC merit crossover = deliv$/MMBtu × HR_coal / HR_cc,
    #              with deliv from the region f.o.b. lifted by delivery-mode
    #              commodity share (PRB /0.42 long-haul rail → ~$2.01, ILB/App
    #              bituminous /0.85 short rail → ~$2.57). PRB crosses at $3.19,
    #              cheaper-than-gas ILB/App bituminous only at $4.12 — the
    #              region-specific crossover the 2.85 byte-copy got wrong.
    #   ceil     = 1.0 — cost-tracking basins never bid above full delivered cost
    #              (retires the residual-tuned 0.92-0.98 markdown).
    #   floor    = gas_min / gas_mid (gas_min = MISO 2024 delivered-gas trough
    #              $2.19), the deepest cheap-gas discount to hold merit parity.
    #   gas_slope= 1 / cross-region delivered-cost dispersion (bituminous spans
    #              IL/IN/KY/ENC → wide spread → gentle 1.09); single-region PRB
    #              resolves no spread → baseline 2.5 (annual data can't resolve
    #              its sharpness — rule-23 granularity caveat).
    # Provenance artifact: data/raw/_processed-legacy/coal_sigmoid_params.csv.
    ("MISO", "bituminous"): {
        "floor": 0.532,
        "ceil": 1.0,
        "gas_mid": 4.115,
        "gas_slope": 1.092,
    },
    ("MISO", "prb"): {
        "floor": 0.687,
        "ceil": 1.0,
        "gas_mid": 3.187,
        "gas_slope": 2.5,
    },
    ("MISO", "prb_follower"): {
        "floor": 0.598,
        "ceil": 1.0,
        "gas_mid": 3.187,
        "gas_slope": 2.5,
    },
    ("PJM", "bituminous"): {
        "floor": 0.76,
        "ceil": 1.32,
        "gas_mid": 3.40,
        "gas_slope": 2.5,
    },
    # PJM subbituminous (the two ComEd PRB-by-rail plants 876/879 delivered into
    # PJM): these are mid-merit PRB CYCLERS, not baseload. Their bare delivered
    # SRMC (~$2.0/MMBtu PRB x ~10.5 HR ~ $21/MWh) sits below gas CC, so with the
    # old loose curve (floor 1.00 / ceil 1.25, ~no cheap-gas markup) the model
    # baseloaded them and over-ran +45% even in the CHEAPEST-gas year (2024:
    # model 6.41 vs EIA-923 4.41 TWh). The over-run is large at low gas, so the
    # curve needs a real markup at the FLOOR (not just a dear-gas ceiling): a
    # cycler's effective offer sits well above bare fuel SRMC (start/min-run +
    # the fact they are not true baseload). Still gas-keyed (more markup when gas
    # is dear) so it does not over-suppress in cheap hours. PJM-specific (NOT the
    # ERCOT prb/subbit curve, whose floor/ceil suppressed these plants below
    # actuals — run 14).
    # Calibrated on the 2024 solve: at a ~1.06 mean markup (old loose curve) the
    # dispatchable bands cleared 4.24 TWh (+45% over); at ~1.54 they crushed to
    # 1.07 TWh (-26% under). The response is ~linear (~-6.6 TWh per unit mean
    # markup over the 8760 dispatch), so a 2024 mean markup ~1.35 lands the
    # dispatchable bands at ~2.2 TWh on top of the step-3a forced floor (~2.17
    # TWh) ~ the 4.41 TWh actual. floor 1.22 / ceil 1.65 / gas_mid 3.5 / slope
    # 1.4 gave mean markups ~1.35 (2024) / 1.40 (2023) / 1.47 (2025) — but slope
    # 1.4 was too gentle for the dear-gas tail: 2025 ($3.95) under-marked and the
    # dispatchable PRB bands over-ran +36% (round-2). Steepened to floor 1.22 /
    # ceil 2.10 / gas_mid 3.70 / slope 3.0: holds the cheap-gas floor (annual-mean
    # markups ~1.29 at 2024 $2.86, ~1.41 at 2023 $3.26) while marking the dear-gas
    # year up hard (~1.82 at 2025 $3.95) so the dispatchable bands back out of the
    # over-run. Gas-keyed, so it self-targets 2025 and leaves the cheap-gas floor
    # put. PJM subbit = 2 plants (876 Kincaid, 879 Powerton); the delivered PRB
    # price ($2.0/MMBtu, ~defensible for ComEd) is unchanged — this marks the BID,
    # not the cost.
    ("PJM", "subbituminous"): {
        "floor": 1.22,
        "ceil": 2.10,
        "gas_mid": 3.70,
        "gas_slope": 3.0,
    },
    # PJM waste coal (culm/gob, the COAL_WC class): near-free reclamation
    # fuel, so no cheap-gas discount (floor 1.0) — only a dear-gas markup.
    # Placement from the run-16/17/18 monthly EIA-923 decomposition: the
    # over-runs live in $5+ gas months (Jan-2025 +0.48 TWh at $6.86 needs
    # a ~2x ceiling before the markup outprices waste at all), while the
    # at-actual 2023 months sit at $3.4-5.0 — runs 17/18 bit 2023's
    # Jan/Feb ($4.85-4.98) and pushed 2023 COAL_WC out of the 1 TWh cap,
    # so the curve rises even later and steeper (mid 5.15, slope 3):
    # ~1.3-1.4 at 2023's winter prices, ~1.4 at Feb/Dec-2025's $5.0-5.1,
    # ~2.1 at Jan-2025's $6.86. Midpoint split: 5.30 would release too
    # much of Feb/Dec-2025 once the run-19 econ-ramp midpoint (curve-mid
    # 0.35) lifts WC mid-band dispatch in both years.
    ("PJM", "waste"): {"floor": 1.00, "ceil": 2.10, "gas_mid": 5.15, "gas_slope": 3.0},
}


TIER_TAGS: dict[str, int] = {
    "weather_year": 0,
    "mode": 0,
    "iso": 0,
    "voll": 0,
    "hours": 0,
    "gas_price_path": 1,
    "gas_price_factor": 1,
    "carbon_price": 1,
    "carbon_price_path": 1,
    "policy_bundle": 1,
    "state_carbon_pricing": 1,
    "nox_price": 1,
    "so2_price": 1,
    "mass_cap_enabled": 1,
    "mass_cap_program": 1,
    "mass_cap_tons": 1,
    "carbon_program_price_path": 1,
    "demand_growth_rate": 1,
    "demand_growth_path": 1,
    "demand_growth_percentile": 1,
    "datacenter_load_path": 2,
    "datacenter_percentile": 2,
    "datacenter_load_factor": 2,
    "tech_cost_path": 1,
    "tech_cost_percentile": 1,
    "renewable_buildout_pace": 1,
    "storage_deployment": 1,
    "retirement_aggressiveness": 1,
    "hydro_year": 1,
    "eac_price_nuclear": 1,
    "eac_price_wind": 1,
    "eac_price_solar": 1,
    "eac_price_gas_cc_ccs": 1,
    "eac_price_storage": 1,
    "eac_price_offshore_wind": 1,
    "eac_price_geothermal": 1,
    "rps_enabled": 1,
    "electrolyzer_type": 1,
    "h2_available_year": 1,
    "ccs_available_year": 1,
    "egs_available_year": 1,
    "offshore_wind_available_year": 1,
    "offshore_wind_eligible_isos": 1,
    "gas_seasonality": 2,
    "storage_rte_4hr": 2,
    "storage_rte_8hr": 2,
    "storage_capacity_value": 2,
    "storage_degradation": 2,
    "nominal_discount_rate": 2,
    "retirement_consecutive_years": 2,
    "forecast_fossil_retirement_economic": 1,
    "retirement_years_coal": 2,
    "retirement_years_gas_ct": 2,
    "retirement_years_gas_cc": 2,
    "retirement_years_gas_st": 2,
    "retirement_years_oil": 2,
    "retirement_years_gas_cc_ccs": 2,
    "retirement_years_nuclear": 2,
    "retirement_fom_multiplier_coal": 2,
    "retirement_fom_multiplier_gas_ct": 2,
    "retirement_fom_multiplier_gas_cc": 2,
    "retirement_fom_multiplier_gas_st": 2,
    "retirement_fom_multiplier_oil": 2,
    "retirement_fom_multiplier_gas_cc_ccs": 2,
    "retirement_fom_multiplier_nuclear": 2,
    "fixed_om_gas_cc": 2,
    "fixed_om_gas_ct": 2,
    "fixed_om_gas_st": 2,
    "fixed_om_coal": 2,
    "fixed_om_oil": 2,
    "fixed_om_gas_cc_ccs": 2,
    "fixed_om_nuclear": 2,
    "ira_ptc_wind": 2,
    "ira_itc_solar": 2,
    "ira_itc_storage": 2,
    "ira_wind_solar_last_year": 2,
    "ira_other_clean_last_full_year": 2,
    "ira_other_clean_phaseout_end": 2,
    "ira_h2_45v_last_year": 2,
    "ira_ccus_45q_last_year": 2,
    "electrolyzer_efficiency_override": 2,
    "ccs_capture_rate": 2,
    "co2_transport_storage_cost": 2,
    "egs_pmin_fraction": 2,
    "offshore_wind_cf_override": 2,
    "ccs_retrofit_hr_penalty": 2,
    "ccs_retrofit_capex_kw": 2,
    "ccs_retrofit_vom_adder": 2,
    "ccs_retrofit_capture_rate": 2,
    "ccs_retrofit_available_year": 2,
    "ccs_retrofit_max_gw_per_year": 2,
    "ccs_retrofit_min_remaining_life": 2,
    "heat_rate_bin_count": 2,
    "use_campd_bins": 2,
    "campd_bins_path": 2,
    "plant_registry_path": 2,
    "use_plant_emission_rates": 2,
    "plant_emission_rates_path": 2,
    "use_plant_emission_rates_v2": 2,
    "plant_emission_rates_v2_path": 2,
    "control_retrofit_forward": 2,
    "control_retrofit_path": 2,
    "unknown_zone_default": 2,
    "commitment_enabled": 2,
    "commitment_irr_hurdle": 2,
    "commitment_storage_weight": 2,
    "commitment_storage_in_merit_floor": 2,
    "commitment_screen_coal": 2,
    "scarcity_pricing_enabled": 1,
    "scarcity_price_overlay": 2,
    "ordc_voll": 1,
    "ordc_mcl_mw": 1,
    "ordc_lolp_sigma_mw": 2,
    "ordc_lolp_mu_mw": 2,
    "ordc_lolp_shift_sigma": 2,
    "ordc_multistep_floor": 2,
    "ordc_as_plan_mw": 2,
    "ordc_lolp_params_path": 2,
    "as_revenue_enabled": 1,
    "interchange_shaping": 1,
    "interchange_shaping_export_only": 1,
    "interchange_shape_import_pct": 3,
    "interchange_shape_export_pct": 3,
    "reference_price_interface": 1,
    "caiso_intertie_reference_price": 1,
    "caiso_corridor_atc_forward": 1,
    "caiso_reference_price_seam": 1,
    "caiso_scarcity_pricing": 1,
    "caiso_lcr_commitment_credit": 1,
    "caiso_gas_commitment_floor": 1,
    "caiso_gas_floor_frac": 3,
    "caiso_ra_mustoffer": 1,
    "caiso_ra_min_load_frac": 2,
    "caiso_ra_startup_bridge": 1,
    "caiso_ra_bridge_decommit": 1,
    "caiso_ra_mustoffer_quantity_gate": 1,
    "caiso_ra_bridge_startup_aware": 1,
    "caiso_ra_bridge_curtailment_release": 1,
    "reliability_floor": 1,
    "caiso_solar_deliverability": 1,
    "caiso_solar_deliverability_k": 3,
    "caiso_solar_deliverability_floor": 3,
    "caiso_solar_endogenous_spill": 1,
    "caiso_solar_cap_at_delivered": 1,
    "neiso_gas_coldsnap_derate": 1,
    "neiso_gas_derate_t0_c": 1,
    "neiso_gas_derate_slope_per_c": 3,
    "neiso_gas_derate_cap": 2,
    "neiso_oil_burn_budget": 1,
    "neiso_winter_fuel_inventory": 1,
    "neiso_winter_fuel_start_fill_bbl": 1,
    "nyiso_local_selfsupply": 1,
    "nyiso_firm_imports": 1,
    "nyiso_import_reconciliation": 1,
    "nyiso_import_hub_prices": 1,
    "nyiso_iroquois_winter_spread": 1,
    "nyiso_synchronised_reserve": 1,
    "nyiso_forward_net_import_twh": 2,
    "nyiso_spin_headroom_frac": 2,
    "miso_firm_imports": 1,
    "miso_seam_flow_limit": 1,
    "miso_seam_flow_percentile": 3,
    "miso_seam_export_limit": 1,
    "pjm_seam_flow_limit": 1,
    "pjm_seam_flow_percentile": 3,
    "pjm_seam_export_limit": 1,
    "pjm_seam_measured_ladder": 1,
    "miso_pjm_border_anchor": 1,
    "miso_cc_coal_rebalance": 1,
    "miso_firm_import_floor": 1,
    "miso_pjm_lmp_import_pricing": 1,
    "miso_seam_measured_ladder": 1,
    "ct_intermediate_split": 1,
    "ct_intermediate_cf_threshold": 3,
    "st_gas_intermediate_split": 1,
    "st_gas_intermediate_cf_threshold": 3,
    "cc_intermediate_split": 1,
    "cc_intermediate_cf_threshold": 3,
    "gas_st_startup_cost": 3,
    "tranche_startup_amortization": 1,
    "tranche_startup_measured_runs": 1,
    "nysdec_peaker_rule_availability": 1,
    "gas_st_wefor_base_override": 3,
    "as_reserve_withholding": 1,
    "as_reserve_formula": 1,
    "energy_reserve_coopt": 1,
    "miso_zonal_reserves": 1,
    "miso_zonal_reserve_zones": 1,
    "miso_reserve_pergen": 1,
    "miso_commitment_posture": 1,
    "caiso_commitment_posture": 1,
    "ercot_load_resource_reserve": 1,
    "ercot_load_resource_reserve_from_year": 1,
    "ercot_storage_as_reserve": 1,
    "ercot_storage_as_reserve_from_year": 1,
    "ercot_ecrs_requirement": 1,
    "ercot_ecrs_requirement_from_year": 1,
    "ercot_multiproduct_as_coopt": 1,
    "ercot_ecrs_conservative_deployment": 1,
    "ercot_ordc_total_reserve": 1,
    "ercot_storage_as_product_credit": 1,
    "ercot_as_critical_frac": 1,
    "ercot_as_n_ramp": 1,
    "ercot_as_aware_commitment": 1,
    "ercot_as_adequacy_frac": 2,
    "ercot_reserve_supply_cap": 1,
    "ercot_reserve_supply_cap_from_year": 1,
    "ercot_reserve_supply_forward": 1,
    "ercot_online_capacity_envelope": 1,
    "ercot_online_capacity_envelope_extreme": 1,
    "pjm_reserve_supply_cap": 1,
    "pjm_reserve_online_gated": 1,
    "pjm_reserve_online_rho": 1,
    "pjm_reserve_commitment_scoped": 1,
    "pjm_reserve_pergen": 1,
    "pjm_reserve_pergen_sync": 1,
    "pjm_reserve_pergen_size_split": 1,
    "pjm_commitment_posture": 1,
    "measured_ramp_capability": 1,
    "ercot_as_forward_requirement": 1,
    "storage_as_commitment": 1,
    "ercot_storage_as_endogenous": 1,
    "ercot_thermal_as_endogenous": 1,
    "ercot_storage_as_duration_gate": 1,
    "negative_renewable_offers": 1,
    "renewable_keep_running_value": 2,
    "as_revenue_multiplier": 2,
    "ercot_market_design": 1,
    "rtcb_reliability_deployment_mw": 2,
    "nyiso_rcpf_enabled": 1,
    "nyiso_rcpf_products": 2,
    "nyiso_rcpf_locational": 2,
    "nyiso_dynamic_reserve_requirements": 1,
    "nyiso_li_lcr_tsl": 1,
    "neiso_rcpf_enabled": 1,
    "neiso_rcpf_products": 2,
    "reserve_margin_build_enabled": 1,
    "market_design_retirement_floor": 1,
    "planning_reserve_margin": 2,
    "planning_reserve_margin_override": 2,
    "entry_price_signal_alpha": 2,
    "entry_lookahead_reprice": 1,
    "cc_peak_hr_penalty": 3,
    "ct_peak_hr_penalty": 3,
    "cc_committed_hr_mult": 3,
    "cc_econ_hr_mult": 3,
    "ct_committed_hr_mult": 3,
    "ct_econ_hr_mult": 3,
    "gas_st_committed_hr_mult": 3,
    "gas_st_econ_hr_mult": 3,
    "must_run_cf": 3,
    "startup_co2_reporting": 3,
    "renewable_cf_adjustment": 3,
    "basis_differential_factor": 3,
    "wefor_multiplier": 3,
    "wefor_residual": 3,
    "maintenance_monthly_shape": 3,
    "td_loss_factor": 3,
    "vintage_capacity_ramp": 3,
    "storage_vintage_ramp": 3,
    "cod_ramp_enabled": 3,
    "coal_tranche_1_frac": 3,
    "coal_tranche_1_fuel_passthrough": 3,
    "coal_tranche_2_frac": 3,
    "coal_tranche_2_fuel_passthrough": 3,
    "coal_tranche_3_frac": 3,
    "coal_tranche_3_fuel_passthrough": 3,
    "coal_prb_contract_passthrough": 3,
    "coal_prb_passthrough": 3,
    "coal_prb_passthrough_sigmoid": 3,
    "coal_prb_passthrough_floor": 3,
    "coal_prb_passthrough_ceil": 3,
    "coal_prb_passthrough_gas_mid": 3,
    "coal_prb_passthrough_gas_slope": 3,
    "coal_prb_passthrough_tiered": 3,
    "coal_prb_follower_mustrun_max": 3,
    "coal_prb_follower_floor": 3,
    "coal_prb_follower_ceil": 3,
    "coal_prb_follower_gas_mid": 3,
    "coal_prb_follower_gas_slope": 3,
    "coal_bit_passthrough_sigmoid": 3,
    "coal_bit_passthrough_floor": 3,
    "coal_bit_passthrough_ceil": 3,
    "coal_bit_passthrough_gas_mid": 3,
    "coal_bit_passthrough_gas_slope": 3,
    "coal_econ_srmc_bound": 3,
    "coal_lignite_passthrough_sigmoid": 3,
    "coal_lignite_passthrough_floor": 3,
    "coal_lignite_passthrough_ceil": 3,
    "coal_lignite_passthrough_gas_mid": 3,
    "coal_lignite_passthrough_gas_slope": 3,
    "coal_sub_passthrough_sigmoid": 3,
    "coal_sub_passthrough_floor": 3,
    "coal_sub_passthrough_ceil": 3,
    "coal_sub_passthrough_gas_mid": 3,
    "coal_sub_passthrough_gas_slope": 3,
    "coal_waste_passthrough_sigmoid": 3,
    "coal_waste_passthrough_floor": 3,
    "coal_waste_passthrough_ceil": 3,
    "coal_waste_passthrough_gas_mid": 3,
    "coal_waste_passthrough_gas_slope": 3,
    "coal_lignite_mustrun_override": 3,
    "coal_prb_mustrun_override": 3,
    "coal_mustrun_per_plant": 3,
    "ct_mustrun_per_plant": 3,
    "ct_mustrun_floor_frac": 3,
    "ct_deployment_overlay": 3,
    "ct_deployment_floor_frac": 3,
    "reliability_deployment_overlay": 3,
    "reliability_deployment_floor_frac": 3,
    "coal_drop_pof": 3,
    "gas_st_startup_spread": 3,
    "gas_st_netload_drag": 3,
    "gas_st_drag_slope_per_gw": 3,
    "gas_st_drag_intercept": 3,
    "gas_st_drag_cap": 3,
    "ct_netload_drag": 3,
    "ramp_limits": 3,
    "local_capacity_constraints": 3,
    "ct_drag_slope_per_gw": 3,
    "ct_drag_intercept": 3,
    "ct_drag_cap": 3,
    "ct_drag_ramp_start": 3,
    "ct_drag_ramp_end": 3,
    "cc_committed_hr_override": 3,
    "cc_econ_hr_override": 3,
    "cc_peak_hr_override": 3,
    "gas_st_committed_hr_override": 3,
    "gas_st_econ_hr_override": 3,
    "gas_st_peak_hr_override": 3,
    "ct_committed_hr_override": 3,
    "ct_econ_hr_override": 3,
    "ct_peak_hr_override": 3,
    "chp_steam_following": 3,
    "chp_btm_floor_pct": 3,
    "chp_export_floor_measured": 3,
    "ercot_gtc_limits_measured": 3,
    "pjm_measured_interface_limits": 3,
    "ercot_wtx_curtailment_driver": 3,
    "ercot_wtx_curtail_depth_wind": 3,
    "ercot_wtx_curtail_depth_solar": 3,
    "coal_supply_repricing": 3,
    "coal_plant_monthly_pricing": 3,
    "nearby_fuel_price_fallback": 3,
    "nearby_fuel_price_min_state_plants": 3,
    "plant_level_fleet": 3,
    "gas_offer_curve": 3,
    "pumped_storage_dispatch_adder": 3,
    "battery_dispatch_adder": 3,
    "gas_monthly_actuals": 3,
    "gas_hh_monthly_shape": 3,
    "gas_hub_basis_overlay": 3,
    "nyiso_zonal_gas_basis": 3,
    "nyiso_downstate_ct_gas_basis": 3,
    "nyiso_downstate_ct_gas_daily": 3,
    "pjm_zonal_gas_basis": 3,
    "miso_zonal_gas_basis": 3,
    "pjm_congestion": 3,
    "ercot_zonal_gas_basis": 3,
    "ercot_gas_delivered_floor_basis": 3,
    "ercot_gas_contract_haircut": 3,
    "oil_primary_bin_fuel": 3,
    "ercot_west_netload_gas_shape": 3,
    "ercot_west_gas_firm_basis": 3,
    "ercot_west_gas_collapse_freq": 3,
    "ercot_west_gas_endogenous_collapse": 3,
    "ercot_west_gas_delivered_floor": 3,
    "gas_hub_basis_daily": 3,
    "dual_fuel_switching": 3,
    "dual_fuel_oil_reattribution": 3,
    "outage_source": 3,
    "gas_price_override": 3,
}


@dataclass
class SweepDefinition:
    """A parameter sweep, or a named-case matrix, expanding into ``ScenarioConfig``\\ s.

    Two mutually-exclusive expansion modes, gated on which mapping is
    non-empty:

    - ``sweep``: the original cartesian mode — a ``{field: [values]}`` mapping
      expands to every combination (``len(values_1) x len(values_2) x ...``
      configs).
    - ``cases``: the PB-1 named-case mode (probability-bounds-plan-2026-07.md
      §1.3) — a ``{case_name: {field: value}}`` mapping expands to exactly one
      config per named case, e.g. the 13-case AEO/IPM-style scenario matrix in
      ``configs/scenario_matrix.yaml``. Unlike ``sweep``, case identity
      (the name) is preserved via :meth:`case_configs` so downstream output
      (the scenario-matrix trajectory table) can label each member.

    Both modes expand *onto* an optional ``base_config`` (every existing
    field of the base is carried through unchanged except the named
    overrides), defaulting to ``ScenarioConfig()`` when none is given —
    reusing this one engine for both the sweep CLI (no base) and the matrix
    CLI (explicit ``--config`` base), per PP-1.1's instruction not to write a
    second sweep engine.
    """

    sweep: dict[str, list] = field(default_factory=dict)
    cases: dict[str, dict] = field(default_factory=dict)
    mode: str = "factorial"

    def __post_init__(self) -> None:
        """Reject a definition that sets both expansion modes at once."""
        if self.sweep and self.cases:
            raise ValueError(
                "SweepDefinition.sweep and SweepDefinition.cases are "
                "mutually exclusive -- a sweep/matrix file must use one "
                "expansion mode, not both"
            )

    def generate(
        self, base_config: ScenarioConfig | None = None
    ) -> list[ScenarioConfig]:
        """Expand into a list of configs (cartesian ``sweep``, or ``cases`` in order).

        Args:
            base_config: Config every expanded member overrides onto.
                Defaults to ``ScenarioConfig()``.
        """
        base = base_config if base_config is not None else ScenarioConfig()
        if self.cases:
            return list(self.case_configs(base).values())
        if not self.sweep:
            return [base]
        names = list(self.sweep.keys())
        value_lists = [self.sweep[name] for name in names]
        configs = []
        for combo in itertools.product(*value_lists):
            overrides = dict(zip(names, combo))
            configs.append(base.with_overrides(**overrides))
        return configs

    def case_configs(
        self, base_config: ScenarioConfig | None = None
    ) -> dict[str, ScenarioConfig]:
        """Expand ``cases`` into ``{case_name: config}``, preserving YAML order.

        Args:
            base_config: Config every named case overrides onto. Defaults to
                ``ScenarioConfig()``.

        Raises:
            ValueError: If ``cases`` is empty (this definition is a ``sweep``,
                not a named-case matrix).
        """
        if not self.cases:
            raise ValueError(
                "case_configs requires a non-empty 'cases' mapping; this "
                "SweepDefinition has none (it may be a cartesian 'sweep')"
            )
        base = base_config if base_config is not None else ScenarioConfig()
        return {
            name: base.with_overrides(**overrides)
            for name, overrides in self.cases.items()
        }

    @classmethod
    def from_yaml(cls, path) -> "SweepDefinition":
        """Load a sweep or named-case matrix definition from a YAML file."""
        data = yaml.safe_load(Path(path).read_text()) or {}
        return cls(
            sweep=data.get("sweep", {}),
            cases=data.get("cases", {}),
            mode=data.get("mode", "factorial"),
        )
