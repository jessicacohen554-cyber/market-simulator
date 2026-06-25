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
    PLANT_REGISTRY_CSV,
    PROCESSED_DIR,
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

    # Tier 1 (scenario levers)
    gas_price_path: str = "mid"  # "low", "mid", "high" or path to CSV
    carbon_price: float = 0.0  # $/ton CO2
    carbon_price_path: str = (
        "zero"  # "zero", "low", "mid", "high"; used when carbon_price is 0.0
    )
    state_carbon_pricing: bool = True  # Charge the ISO's state carbon-program
    # allowance cost (CA cap-and-trade for CAISO; STATE_CARBON_PRICE_BY_ISO)
    # when carbon_price is 0.0 and the year has a measured allowance price.
    # Only CAISO 2023-2025 is registered, so this is default-on for CAISO
    # backcasts and a no-op everywhere else (ERCOT/PJM have no state program;
    # forward years have no entry and fall through to carbon_price_path).
    # See market_sim.policy.carbon.resolve_carbon_price.
    nox_price: float = 0.0  # $/ton NOx
    so2_price: float = 0.0  # $/ton SO2
    demand_growth_rate: float = (
        0.01  # flat override used only when no structured rates exist
    )
    demand_growth_path: str = (
        "mid"  # "low", "mid", "high" — selects from DEMAND_GROWTH_RATES
    )
    renewable_buildout_pace: str = "mid"  # "slow", "mid", "aggressive"
    storage_deployment: str = "mid"
    retirement_aggressiveness: str = "mid"
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
    retirement_reserve_margin: float = 0.15  # 15% reserve margin over peak net demand
    # Don't retire thermal below (peak_demand - firm_clean) * (1 + reserve_margin)
    fixed_om_gas_cc: float = 12.0  # $/kW-yr
    fixed_om_gas_ct: float = 8.0
    fixed_om_gas_st: float = 35.0  # legacy gas steam (boiler/ST) going-forward fixed
    # cost: high relative to a CC because old steam units are staffing- and
    # maintenance-intensive. Until this field existed, gas_st was absent from the
    # economic-retirement screen entirely (it is not gas_cc/gas_ct/coal), so old
    # steam gas could never retire on economics regardless of revenue. Source:
    # Lazard LCOE / NREL ATB legacy-steam FOM class ($30-40/kW-yr).
    fixed_om_coal: float = 40.0
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

    # Tier 3 (calibration) — CAMPD peaking-tranche heat-rate penalties.
    # The top (Peaking) slice of a bin is a separate LP generator whose
    # heat rate is the bin HR scaled by these duct-firing / peaking-increment
    # multipliers, so scarcity output bids above the economic tranche.
    cc_peak_hr_penalty: float = 1.15  # CC duct-firing increment
    ct_peak_hr_penalty: float = 1.10  # CT / gas-steam peaking increment
    coal_peak_hr_penalty: float = 1.08  # Coal peaking increment

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
    coal_committed_hr_mult: float = 1.22  # Coal part-load penalty ~22%
    coal_econ_hr_mult: float = 0.97  # Coal incremental HR
    must_run_cf: float = 0.85  # assumed CF for CHP must-run emissions post-processing

    # Tier 2 (expert/sensitivity) — Unit commitment heuristic (2-pass)
    commitment_enabled: bool = False  # default off — opt-in for calibration.
    # When True, a price-based commitment
    # filter runs between two LP solves to
    # approximate integer unit commitment.
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

    # Tier 1/2 — ERCOT ORDC scarcity-pricing overlay (post-solve; never an LP
    # input). Replicates ERCOT's published real-time on-line reserve price
    # adder (RTORPA): adder = weighted LOLP x (VOLL - system lambda), LOLP
    # from a normal CDF over reserves minus the minimum contingency level.
    # The overlay owns the price tail and scarcity revenue only — dispatch,
    # volumes and emissions are untouched (the LP stays the emissions
    # engine). See docs/ordc-overlay.md for formula provenance. ERCOT-only:
    # capacity-market ISOs recover fixed cost through capacity revenue
    # (capacity_revenue_per_mw_yr), not scarcity adders.
    scarcity_pricing_enabled: bool = False  # Master flag. Backcast: emits the
    # lmp + adder series next to the energy-only LMP (which the volume
    # calibration gates stay on). Forecast: retirement / new-entry / CCS
    # screens see prices + adder, so peaker and storage economics include
    # scarcity revenue instead of bare LP duals (which over-retire).
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
    ordc_reliability_deployment_mw: float = 0.0  # DEPRECATED reliability-
    # deployment / reserve-tightness offset (MW), subtracted from reserves
    # before the ORDC curve. This was the fitted RTORDPA analogue — a flat,
    # NON-physical offset calibrated to the 2023 stress year's LMP residual
    # (~2,500 MW). It is **superseded** by the formulaic reserve accounting in
    # results.scarcity: (1) the online/offline reserve split (cold slow-start
    # capacity no longer counts as responsive reserve — the real cause of the
    # perfect-commitment headroom overstatement this offset papered over), and
    # (2) AS-plan netting from the measured cleared-DAM up-AS series (or the
    # ercot_operating_reserve_mw formula in forecast / 2023). Both are
    # market-design-grounded and renewable-responsive, so the keeper needs no
    # fitted offset. Per claude.md (no pinning the backcast to actuals) this is
    # kept only as a default-0, explicitly-labelled diagnostic probe — never a
    # keeper — and is still added on top of the AS netting when set, so a
    # scenario can model extra discretionary conservatism. The runner no longer
    # depends on it for the baseline. See docs/backcast-measured-data-audit-
    # 2026-06.md and docs/ordc-overlay.md.
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
    # forward design: ordc_reliability_deployment_mw applies only in the ORDC
    # regime; the RTC+B regime uses rtcb_reliability_deployment_mw (default 0).
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

    reserve_margin_build_enabled: bool = False  # Adequacy backstop: after the
    # economic new-entry screen, force-build firm (gas_ct) capacity if the
    # system's accredited firm capacity is below peak * (1 + planning reserve
    # margin). This is the ReEDS/NEMS/CDR structural adequacy mechanism — it
    # keeps the lights on when under-priced energy/scarcity revenue would
    # otherwise under-build, independent of getting prices exactly right. The
    # economic screen still decides the profitable build; this only fills the
    # residual adequacy gap. Default off (byte-identical); recommended on for
    # forecasts. Uses the prior year's peak (build-ahead-of-need).
    planning_reserve_margin: float = 0.1375  # Fallback/override planning
    # reserve margin for the adequacy backstop. The per-ISO registry
    # constants.PLANNING_RESERVE_MARGIN_BY_ISO now LEADS: the backstop resolves
    # PLANNING_RESERVE_MARGIN_BY_ISO.get(iso, this scalar), so this value only
    # applies as an explicit override or when an ISO is absent from the
    # registry. 13.75% is ERCOT's economically-optimal reserve margin
    # (Brattle/Astrape 2022 study for the PUCT); a capacity-market ISO uses its
    # own installed-reserve-margin target from the registry.
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
    # NOT fitted to the residual. LP-linear online-headroom PROXY for true
    # commitment-gated spin (the exact gate is path B / model.commitment). Default
    # off (byte-identical); NYISO-only; requires --energy-reserve-coopt.
    miso_firm_imports: bool = False  # Manitoba Hydro firm-hydro import block:
    # Manitoba Hydro sells ~10-15 TWh/yr of FIRM contracted hydro into MISO-North
    # over the Manitoba<->US HVDC / 500 kV ties — MISO's single largest import
    # source and the structural reason MISO is a net IMPORTER (EIA-930 net
    # interchange -37.9/-23.1/-19.0 TWh, 2023-25). This import sits OUTSIDE the
    # gas-margin reference-price seam (INTERFACE_NEIGHBORS["MISO"], PJM/SPP/SERC):
    # firm hydro has no gas x heat-rate price analogue, so it is a SEPARATE block
    # priced as firm hydro (a low, near-constant energy offer reflecting the
    # contract, MISO_MANITOBA_FIRM_IMPORT_OFFER), landing directly in MISO-North
    # (the model zone the ties physically enter) and counted as net interchange
    # via its fuel_type="import". The block (transmission.build_miso_firm_imports)
    # is floored as must-flow firm baseload (transmission.inject_miso_firm_imports,
    # MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC x capacity) so it flows every hour
    # regardless of MISO's hourly price. Volume is sourced from the Manitoba Hydro
    # export-contract band, NOT fitted to the net-interchange residual (rule #12:
    # a firm contract reproduces for any forward year and responds to a changed
    # contract). Requires --priced-interchange (served by the priced node). MISO-
    # only; default off here but default-ON for the MISO backcast via
    # constants.resolve_miso_firm_imports (the firm Manitoba import is the correct
    # structure for MISO, not a probe). ERCOT byte-identical.
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
    # need not sum to 1.0 but normally do. Source: calibrated to EIA-930
    # 2023-2024 hourly ERCOT coal dispatch and eGRID 2023/2024 actuals.
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
    gas_st_summer_mustrun: float = 0.0
    gas_st_startup_spread: bool = False
    # Off-summer (Oct-Apr) ST_GAS reliability min-gen floor, as a fraction of
    # capacity, applied to the same reliability (non-peaker) ST_GAS units as
    # gas_st_summer_mustrun. Peaker-class ST_GAS (fleet.ST_GAS_PEAKER_PLANTS)
    # get neither floor and run purely economically.
    gas_st_offsummer_mustrun: float = 0.0

    # Net-load-indexed ST_GAS reliability-drag floor — the endogenous,
    # weather-driven replacement for the blunt seasonal gas_st_summer_mustrun
    # calendar fraction. ERCOT holds legacy gas-steam committed at minimum load
    # for local/system reliability (RUC); the held fraction is not a fixed
    # season but rises with system net-load (load - wind - solar), the
    # operational proxy for reserve tightness RUC keys off. When
    # gas_st_netload_drag is True, each non-peaker ST_GAS unit carries a per-hour
    # min-gen floor of clip(slope*netload_GW + intercept, 0, cap) x capacity,
    # over which the LP dispatches economically. The defaults are the CAMPD
    # overnight (low-price) ST_GAS capacity factor regressed on contemporaneous
    # system net-load, 2023-2025 (docs/ercot-st-gas-netload-drag-2026-06.md);
    # the relationship is year-stable, so a single curve regenerates for a
    # forward year (which has a load forecast and wind/solar build -> net-load)
    # and responds to changed conditions (more VRE -> lower net-load -> less
    # drag). That forward-derivability + condition-response makes it a
    # legitimate input in both backcast and forecast (CLAUDE.md #10), unlike a
    # fixed seasonal fraction or an offer markdown tuned to the ST_GAS residual.
    gas_st_netload_drag: bool = False
    gas_st_drag_slope_per_gw: float = 0.00906  # overnight CF per GW net-load
    gas_st_drag_intercept: float = -0.1376  # floor zero-crossing ~15.2 GW
    gas_st_drag_cap: float = 0.34  # max observed overnight floor fraction (~50 GW)

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

    # When True, the CC_REGULAR plants in fleet.CC_REGULAR_PEAKING_PCT_BY_PLANT
    # use that per-plant peaking-tranche % instead of the offer curve's
    # ``pct_peaking`` — moving where the expensive duct-burner peak band starts
    # on the CF axis (e.g. 15% => peaking starts at 85% of nameplate). The
    # economic tranche absorbs the difference. Other CC_REGULAR plants keep the
    # offer-curve value. Off by default.
    cc_peaking_per_plant: bool = False

    # When True, every CC_REGULAR / CC_CHP plant's peaking-tranche % comes
    # from the EIA-860 duct-burner flag (fleet.cc_duct_peaking_pct):
    # duct-fired plants get their nameplate-vs-net-summer capability gap as
    # the peak band, non-duct CC plants get 0 — no phantom scarcity band on
    # plants with no duct firing. Supersedes the offer curve's class-wide
    # ``pct_peaking`` (the band heat-rate multipliers still apply on top);
    # plants absent from the EIA-860 sheet keep the class value, and the
    # ERCOT hand-set CC_REGULAR_PEAKING_PCT_BY_PLANT map stays the final
    # word for its plants. Off by default.
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

    # Tier 3 — pumped-storage dispatch adder ($/MWh discharged). PSH pure O&M
    # is < $1/MWh, but the fleet (e.g. Bath County) reserves much of its duty
    # for regulation/reserves and follows pumping schedules the energy-only LP
    # does not see; with no adder the LP arbitrages PS every day the spread
    # clears RTE losses and generates ~2-3x the observed PS energy, shaving
    # exactly the peaks the CT fleet actually served. This is the reduced-form
    # opportunity cost of that reserve duty. ``None`` (default) resolves per
    # ISO from constants.PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO — PJM $10,
    # calibrated so PJM PS lands near its observed ~3.5-4 TWh/yr (EIA-923 PS
    # gross generation); ISOs without a calibrated entry (e.g. CAISO) get
    # 0.0 until their own calibration says otherwise. A number overrides the
    # per-ISO default for every ISO in the scenario.
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
    # default), the per-year measured value is read from the neg_day_freq column of
    # data/raw/ercot_zonal_gas_hub.csv (2024 EIA-authoritative at 0.42; 2023/2025
    # NGI counts), falling back to the 2024 record (0.42) for years with no row.
    # This is the measured *collapse frequency*, not a tuning knob — set it only
    # for diagnostic probes, never to chase the CT_PEAKER residual. ERCOT only.
    ercot_west_gas_collapse_freq: float | None = None

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
        payload = json.dumps(asdict(self), sort_keys=True)
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
    "carbon_price": 1,
    "carbon_price_path": 1,
    "state_carbon_pricing": 1,
    "nox_price": 1,
    "so2_price": 1,
    "demand_growth_rate": 1,
    "demand_growth_path": 1,
    "renewable_buildout_pace": 1,
    "storage_deployment": 1,
    "retirement_aggressiveness": 1,
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
    "retirement_reserve_margin": 2,
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
    "unknown_zone_default": 2,
    "commitment_enabled": 2,
    "commitment_irr_hurdle": 2,
    "commitment_storage_weight": 2,
    "commitment_storage_in_merit_floor": 2,
    "commitment_screen_coal": 2,
    "scarcity_pricing_enabled": 1,
    "ordc_voll": 1,
    "ordc_mcl_mw": 1,
    "ordc_lolp_sigma_mw": 2,
    "ordc_lolp_mu_mw": 2,
    "ordc_lolp_shift_sigma": 2,
    "ordc_multistep_floor": 2,
    "ordc_as_plan_mw": 2,
    "ordc_lolp_params_path": 2,
    "ordc_reliability_deployment_mw": 2,
    "as_revenue_enabled": 1,
    "interchange_shaping": 1,
    "interchange_shaping_export_only": 1,
    "reference_price_interface": 1,
    "caiso_gas_commitment_floor": 1,
    "caiso_gas_floor_frac": 3,
    "nyiso_local_selfsupply": 1,
    "nyiso_firm_imports": 1,
    "nyiso_import_reconciliation": 1,
    "nyiso_synchronised_reserve": 1,
    "miso_firm_imports": 1,
    "as_reserve_withholding": 1,
    "as_reserve_formula": 1,
    "energy_reserve_coopt": 1,
    "ercot_load_resource_reserve": 1,
    "ercot_load_resource_reserve_from_year": 1,
    "ercot_storage_as_reserve": 1,
    "ercot_storage_as_reserve_from_year": 1,
    "ercot_ecrs_requirement": 1,
    "ercot_ecrs_requirement_from_year": 1,
    "storage_as_commitment": 1,
    "negative_renewable_offers": 1,
    "renewable_keep_running_value": 2,
    "as_revenue_multiplier": 2,
    "ercot_market_design": 1,
    "rtcb_reliability_deployment_mw": 2,
    "nyiso_rcpf_enabled": 1,
    "nyiso_rcpf_products": 2,
    "nyiso_rcpf_locational": 2,
    "neiso_rcpf_enabled": 1,
    "neiso_rcpf_products": 2,
    "reserve_margin_build_enabled": 1,
    "planning_reserve_margin": 2,
    "cc_peak_hr_penalty": 3,
    "ct_peak_hr_penalty": 3,
    "coal_peak_hr_penalty": 3,
    "cc_committed_hr_mult": 3,
    "cc_econ_hr_mult": 3,
    "ct_committed_hr_mult": 3,
    "ct_econ_hr_mult": 3,
    "gas_st_committed_hr_mult": 3,
    "gas_st_econ_hr_mult": 3,
    "coal_committed_hr_mult": 3,
    "coal_econ_hr_mult": 3,
    "must_run_cf": 3,
    "renewable_cf_adjustment": 3,
    "basis_differential_factor": 3,
    "wefor_multiplier": 3,
    "wefor_residual": 3,
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
    "gas_st_summer_mustrun": 3,
    "gas_st_startup_spread": 3,
    "gas_st_offsummer_mustrun": 3,
    "gas_st_netload_drag": 3,
    "gas_st_drag_slope_per_gw": 3,
    "gas_st_drag_intercept": 3,
    "gas_st_drag_cap": 3,
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
    "coal_supply_repricing": 3,
    "coal_plant_monthly_pricing": 3,
    "nearby_fuel_price_fallback": 3,
    "nearby_fuel_price_min_state_plants": 3,
    "plant_level_fleet": 3,
    "gas_offer_curve": 3,
    "pumped_storage_dispatch_adder": 3,
    "battery_dispatch_adder": 3,
    "gas_monthly_actuals": 3,
    "gas_hub_basis_overlay": 3,
    "nyiso_zonal_gas_basis": 3,
    "ercot_zonal_gas_basis": 3,
    "ercot_gas_delivered_floor_basis": 3,
    "ercot_gas_contract_haircut": 3,
    "oil_primary_bin_fuel": 3,
    "ercot_west_netload_gas_shape": 3,
    "ercot_west_gas_firm_basis": 3,
    "ercot_west_gas_collapse_freq": 3,
    "ercot_west_gas_delivered_floor": 3,
    "gas_hub_basis_daily": 3,
    "dual_fuel_switching": 3,
    "dual_fuel_oil_reattribution": 3,
    "outage_source": 3,
    "gas_price_override": 3,
}


@dataclass
class SweepDefinition:
    """A parameter sweep that expands into multiple ``ScenarioConfig`` objects."""

    sweep: dict[str, list] = field(default_factory=dict)
    mode: str = "factorial"

    def generate(self) -> list[ScenarioConfig]:
        """Expand the sweep into a list of configs (cartesian product)."""
        if not self.sweep:
            return [ScenarioConfig()]
        names = list(self.sweep.keys())
        value_lists = [self.sweep[name] for name in names]
        configs = []
        for combo in itertools.product(*value_lists):
            overrides = dict(zip(names, combo))
            configs.append(ScenarioConfig().with_overrides(**overrides))
        return configs

    @classmethod
    def from_yaml(cls, path) -> "SweepDefinition":
        """Load a sweep definition from a YAML file at ``path``."""
        data = yaml.safe_load(Path(path).read_text()) or {}
        return cls(
            sweep=data.get("sweep", {}),
            mode=data.get("mode", "factorial"),
        )
