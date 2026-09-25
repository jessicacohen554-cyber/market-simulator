"""Physical and economic constants with citation comments."""

# --- Facade re-exports (constants split, refactor plan §5 — 2026-07-20) ------
# Three blocks moved to sibling modules; every moved name (public and private)
# stays importable from this module so the 130+ existing importers are
# unaffected. Unused-import lint is ignored for this file (pyproject
# per-file-ignores F401) — these ARE the exports. Values and citation
# comments live at the new homes:
#   config/fuel_trajectories.py — fuel prices, availability shapes, carbon paths
#   config/capacity_market.py — cap-and-trade, capacity market, adequacy, storage
#   config/ercot_envelopes.py — ERCOT reserve-supply / on-line-capacity envelopes
from market_sim.config.capacity_market import (
    ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
    ADEQUACY_EXTERNAL_TIE_FIRM_MW,
    ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO,
    ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO,
    AS_REVENUE_PER_KW_YR_BY_ISO,
    AS_SATURATION_REF_GW_BY_ISO,
    CAISO_RA_MPB_ANCHOR_PER_KW_YR,
    CAMPD_BINNING_ISOS,
    CAPACITY_CURVE_ELIGIBLE_BY_ISO,
    CAP_AND_TRADE_PROGRAMS,
    CARBON_PROGRAM_PRICE_PATH_ESCALATION_MULTIPLIER,
    CARB_ALLOWANCE_BUDGET,
    CARB_FLOOR_ESCALATION,
    CARB_FLOOR_PRICE,
    CapAndTradeProgram,
    CapacityDemandCurvePoint,
    ClearedCapacityPrice,
    DEFAULT_MARKET_DESIGN,
    ERCOT_AS_REVENUE_PER_KW_YR,
    ERCOT_AS_SATURATION_EXPONENT,
    ERCOT_AS_SATURATION_REF_GW,
    DEMAND_RESPONSE_SUPPLY_HOLD_LAST_RATIO_BY_ISO,
    DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO,
    FORECAST_POOL_REQUIREMENT_BY_ISO,
    FORECAST_POOL_REQUIREMENT_PRE_REFORM_BY_ISO,
    NET_ICR_HOLD_LAST_RATIO_BY_ISO,
    NET_ICR_REQUIREMENT_MW_BY_ISO,
    RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO,
    NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO,
    NYCA_ICAP_UCAP_TRANSLATION_BY_ISO,
    NYCA_IRM_ADOPTED_BY_ISO,
    LOCALITY_CAPACITY_AREAS_BY_ISO,
    LOCALITY_GROSS_CONE_BY_ISO,
    LOCALITY_MARKET_DESIGN_VINTAGES,
    NYISO_LOCALITY_UDR_ICAP_MW,
    locality_curve_price_per_firm_mw_yr,
    resolve_locality_curve_vintage,
    resolve_locality_gross_cone_ratio,
    HISTORIC_OUTAGE_OVERLAY_BY_ISO,
    HYDRO_ACCREDITATION_CREDIT_BY_ISO,
    MARKET_DESIGN,
    MARKET_DESIGN_VINTAGES,
    MISOSeasonRBDC,
    MISO_CLEAN_TIER_REGIONS,
    MISO_RPS_COMPLIANCE_REGIONS,
    MISO_RPS_MIDWEST_FOOTPRINT_ZONES,
    MISO_SEASONAL_RBDC,
    MarketDesign,
    MarketDesignVintage,
    NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO,
    NONFOSSIL_ANNOUNCED_HORIZON_YEARS,
    PJM_RGGI_ZONE_SHARE,
    PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE,
    PLANNING_RESERVE_MARGIN_BY_ISO,
    PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO,
    QUEUE_CAP_GW,
    QUEUE_CAP_PER_TECH_GW,
    RENEWABLE_CAPACITY_CREDIT,
    RENEWABLE_CAPACITY_CREDIT_BY_ISO,
    RENEWABLE_ELCC_CURVES_BY_ISO,
    RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO,
    RENEWABLE_NQC_CURVES_BY_ISO,
    RGGI_MEMBER_STATES_BY_YEAR,
    RGGI_RESERVE_ESCALATION,
    RGGI_STATE_CO2_BUDGET,
    RPS_ELIGIBLE_FUELS_BY_ISO,
    RenewableElccCurve,
    SHORT_TON_TO_METRIC_TONNE,
    STATE_RPS_ACP,
    STATE_RPS_FLOORS,
    STORAGE_ANNUAL_BUILD_CAP_MW,
    STORAGE_BASE_FLEET_MW,
    STORAGE_DEGRADATION_REPLACEMENT_FRACTION,
    STORAGE_DEPLOYMENT_CEILING_MW,
    STORAGE_ELCC_BY_DURATION,
    STORAGE_ELCC_BY_DURATION_BY_ISO,
    STORAGE_ELCC_DILUTION_CEILING_RATIO_BY_ISO,
    STORAGE_ELCC_DILUTION_REFERENCE_MW_BY_ISO,
    STORAGE_ELCC_SATURATION_EXPONENT,
    STORAGE_MEASURED_BASE_FLEET_ISOS,
    STORAGE_TECHS,
    STORAGE_TECH_AVAILABLE_YEAR,
    STORAGE_TECH_BUILD_SHARE_CAP,
    STORAGE_TECH_POWER_SHARE,
    STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO,
    SeasonalRBDC,
    THERMAL_ACCREDITATION_BASIS_BY_ISO,
    THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO,
    THERMAL_ELCC_CLASS_RATING_BY_ISO,
    THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO,
    _MISO_DAILY_NET_CONE_PER_MW_DAY,
    _MISO_NC_NET_CONE_PER_MW_YR,
    _MISO_RBDC_CURVE,
    _MISO_SEASON_DAYS,
    _MISO_SEASON_POINTS,
    _MISO_RBDC_FALL_POINTS,
    _MISO_RBDC_SPRING_POINTS,
    _MISO_RBDC_SUMMER_POINTS,
    _MISO_RBDC_WINTER_POINTS,
    _MISO_VERTICAL_CURVE,
    _MISO_VERTICAL_STEP,
    _miso_annual_reduction,
    _NEISO_FCA11_CURVE,
    _NEISO_FCA13_CURVE,
    _NEISO_FCA_CAP_X,
    _NEISO_FCA_CURVE,
    _NEISO_MRI_CLEARING_POINTS,
    _NEISO_MRI_ZERO_X,
    _NYISO_ICAP_CURVE,
    _NYISO_LOCALITY_CURVE_LENGTH,
    _NYISO_NYCA_CURVE_LENGTH,
    _PJM_VRR_CURVE,
    _PJM_VRR_CURVE_2027_2028,
    _PJM_VRR_CURVE_2028_2029,
    _NO_DEFAULT_CAP_REFUSED_LOGGED,
    _SUPPLY_CLEARING_REFUSED_LOGGED,
    _neiso_fca_vintage_curve,
    _nyiso_icap_vintage_curve,
    evaluate_demand_curve,
    evaluate_renewable_elcc_curve,
    forward_net_cone_anchor,
    resolve_caiso_ra_mpb_anchor,
    resolve_capacity_adequacy_requirement_published,
    resolve_capacity_curve_eligible,
    resolve_capacity_going_forward_bar_published,
    resolve_capacity_market_clearing,
    resolve_capacity_market_supply_clearing,
    resolve_capacity_no_default_cap_convention,
    resolve_demand_curve_vintage,
    seasonal_rbdc_price_per_firm_mw_yr,
)
from market_sim.config.ercot_envelopes import (
    ERCOT_ONLINE_CAP_DELIV_COEF,
    ERCOT_ONLINE_CAP_DELIV_PROFILE_EXTREME,
    ERCOT_ONLINE_CAP_DELIV_PROFILE_MEASURED,
    ERCOT_ONLINE_CAP_MEASURED_AVAIL_CLASSES,
    ERCOT_ONLINE_CAP_SHARE,
    ERCOT_ONLINE_CAP_SHARE_EXTREME,
    ERCOT_ONLINE_CAP_SHARE_MEASURED,
    ERCOT_RTOLCAP_FWD_DELIV_COEF,
    ERCOT_RTOLCAP_FWD_N_DECILE,
    ERCOT_RTOLCAP_FWD_N_SEASON,
    ERCOT_RTOLCAP_FWD_OFFLINE_CLASSES,
    ERCOT_RTOLCAP_FWD_OFFLINE_DELIV_COEF,
    ERCOT_RTOLCAP_FWD_OFFLINE_SHARE,
    ERCOT_RTOLCAP_FWD_ONLINE_CLASSES,
    ERCOT_RTOLCAP_FWD_ONLINE_SHARE,
    ERCOT_RTOLCAP_FWD_SEASON_BY_MONTH,
    ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC,
)
from market_sim.config.fuel_trajectories import (
    BIOMASS_PRICE_PER_MMBTU,
    CAISO_CITYGATE_TRANSPORT_ADDER,
    CARBON_PRICE_PATHS,
    CARB_UNSPECIFIED_IMPORT_EF,
    COAL_DELIVERY_COMMODITY_SHARE,
    COAL_HEAT_CONTENT_MMBTU_PER_TON,
    COAL_MAX_CF_BY_PLANT,
    COAL_PRICE_BASE,
    COAL_PRICE_ESCALATION,
    COAL_PRICE_TRAJECTORIES,
    COAL_SIGMOID_BACKCAST_GAS_MIN_MMBTU,
    COAL_SIGMOID_BASELINE_SLOPE,
    COAL_SIGMOID_FLOOR_MIN,
    COAL_SIGMOID_FOLLOWER_DISCOUNT,
    COAL_SIGMOID_REP_HR_COAL,
    COAL_SIGMOID_REP_HR_GAS_CC,
    COAL_SIGMOID_SLOPE_MAX,
    COAL_SIGMOID_SLOPE_MIN,
    GAS_BASIS_DIFFERENTIAL,
    GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR,
    GAS_MONTHLY_SEASONALITY,
    HENRY_HUB_TRAJECTORIES,
    LIGNITE_PRICE_2023_25,
    MAINTENANCE_MONTHLY_SHAPE,
    NUCLEAR_FUEL_PRICE_HISTORICAL,
    OIL_PRICE_PER_MMBTU,
    OIL_PRICE_TRAJECTORIES,
    PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE,
    PRB_COMMODITY_DECLINE,
    PRB_COMMODITY_FLAT_THROUGH,
    PRB_COMMODITY_SHARE,
    PRB_PRICE_BY_YEAR,
    PRB_RAIL_DIESEL_SHARE,
    PRB_RAIL_NONDIESEL_SHARE,
    STATE_CARBON_PRICE_BY_ISO,
    SUMMER_CLASS_DERATE,
    SUMMER_WEFOR_SHARE,
    THERMAL_AVAILABILITY,
)


# Heat rate efficiency bins (MMBtu/MWh) by fuel class and technology vintage.
# Lower heat rate means higher thermal efficiency.
# Source: EIA Table 8 (Average Tested Heat Rates by Prime Mover and Fuel Type).
HEAT_RATE_BINS: dict[str, dict[str, float]] = {
    "gas_cc": {
        "h_class": 6.3,  # EIA Table 8 — newest H-class combined-cycle units
        "f_class": 6.7,  # EIA Table 8 — F-class combined-cycle units
        "older": 7.5,  # EIA Table 8 — legacy combined-cycle units
    },
    "gas_ct": {
        "aero": 9.0,  # EIA Table 8 — aeroderivative combustion turbines
        "frame": 10.5,  # EIA Table 8 — heavy-frame combustion turbines
        "older": 11.5,  # EIA Table 8 — legacy combustion turbines
    },
    # Legacy natural-gas steam boilers (fuel gas_st, D-25 taxonomy fix). One
    # "default" bin like oil/biomass: the vintage classifier carries no
    # sub-bins for them (fleet._efficiency_bin). Fallback only — nearly every
    # gas_st row carries a unit-level eGRID heat rate.
    "gas_st": {
        "default": 10.3,  # EIA Table 8.2 — natural-gas steam generators (~10,300 Btu/kWh)
    },
    "coal": {
        "supercritical": 8.8,  # EIA Table 8 — supercritical steam units
        "subcritical": 10.0,  # EIA Table 8 — subcritical steam units
        "older": 10.8,  # EIA Table 8 — legacy subcritical steam units
    },
    # Oil and biomass classify into a single "default" bin (the EIA-source
    # classifier carries no vintage sub-bins for them, see fleet._efficiency_bin).
    "oil": {
        "default": 13.5,  # EIA Table 8 — petroleum-fired GT/steam (oil peaker)
    },
    "biomass": {
        "default": 13.5,  # EIA Table 8 — wood/biomass steam (low-efficiency)
    },
}

# eGRID plant-heat-rate boundary reconciliation (see
# docs/handoffs/miso-88-egrid-hr-boundary-plan-2026-07.md).
#
# eGRID keys its plant sheet on ORISPL, but CEMS reports co-located plants that
# share a stack/facility under ONE facilityId. Where that happens the plant row's
# heat input (PLHTIAN) covers the whole CEMS facility while its net generation
# (PLNGENAN) covers only the one EIA plant, so PLHTRT is a ratio of two different
# boundaries and the co-located sibling's fuel is double-counted. Riverside
# Energy Center (55641) / West Riverside (64020) is the live instance: PLHTRT
# 14,963.7 Btu/kWh against a boundary-consistent 6,880.
#
# Site identity: co-located plants share a fence line. 1.0 km comfortably spans
# a multi-block generating station (Riverside/West Riverside are 454 m apart)
# while never reaching an unrelated station.
EGRID_COLOCATION_RADIUS_KM: float = 1.0
# CEMS unit commissioning date vs the EIA-860 generator in-service year differ by
# up to a year for the same machine (CEMS certifies at first fire, EIA-860 records
# commercial operation): eGRID UNT23 dates West Riverside's turbines 2019, EIA-860
# dates the generators 2020. A one-year window matches a unit to its own plant's
# vintages without reaching an adjacent build.
EGRID_UNIT_VINTAGE_TOL_YEARS: int = 1
# Physical ceiling for a combined-cycle plant heat rate. A combined cycle raises
# steam from its own topping turbine's exhaust, so it cannot be LESS efficient
# than a bare simple-cycle GT of the same era — HEAT_RATE_BINS["gas_ct"]["older"]
# (EIA Table 8 legacy combustion turbine). A gas_cc plant rate above this is
# arithmetic on mismatched boundaries, not measured inefficiency. Scoped to
# gas_cc: this is the one class where the bound is airtight (a CT has no
# less-efficient sibling technology to bound it against).
EGRID_CC_HR_PHYSICAL_CEILING: float = HEAT_RATE_BINS["gas_ct"]["older"]
# Physical FLOOR for a simple-cycle-only plant heat rate — the mirror of the
# ceiling above on the other side of the physics (SPP-46 R-2; owner ruling P19,
# 2026-09-08, repo-wide; PRECOMMIT-spp-49-2026-09-08.md §1.1 / §2.2). A plant
# whose every operating EIA-860 row is a simple-cycle prime mover (GT or IC — no
# steam cycle anywhere on site, so no heat recovery) cannot convert fuel to net
# electricity at better than the best bare turbine, HEAT_RATE_BINS["gas_ct"]["aero"]
# (EIA Table 8 aeroderivative). A plant-grain eGRID PLHTRT below it is arithmetic
# on mismatched boundaries (Pioneer 57881: 3.43 MMBtu/MWh with EIA-923 net
# generation ~3x its CEMS gross load), not measured efficiency; the fleet loader
# clamps such a plant's rows to this floor (data/fleet/eia860.py::
# _apply_simple_cycle_hr_floor). An alias of an existing cited constant, no new
# number. Scoped to simple-cycle-only plants: a mixed plant's blend rate is the
# egrid_family_heat_rates object, never this.
EGRID_CT_HR_PHYSICAL_FLOOR: float = HEAT_RATE_BINS["gas_ct"]["aero"]

# ercot-261. Maximum |disagreement| in $/MMBtu between the two independent
# measurements of the Texas delivered-to-electric-power gas price -- the EIA
# N3045TX3 state survey (ERCOT_ELECTRIC_POWER_GAS_PATH) and the EIA-923
# Schedule-5 quantity-weighted plant receipts (ERCOT_GAS_CORROBORATOR_PATH) --
# for that month's survey print to be admissible as an HOURLY delivered-gas
# level under ScenarioConfig.ercot_ep_gas_basis_corroborated.
#
# IDENTIFICATION (rule 21 [R-DOF], and it is the only free parameter that gate
# adds): the observed disagreement distribution of the two series over all 84
# months 2019-01..2025-12. They agree within $0.85/MMBtu in 82 of those months;
# the only two outliers are 2021-02 ($13.77) and 2021-12 ($3.47), with NO month
# in between -- a factor-4.1 empty gap. 1.00 sits inside that gap, above the
# corroborating mass and 3.5x below the nearest outlier. Set ex ante from the
# data's own gap structure and NEVER swept against a criterion (rule 1
# [R-STRUCT]); it selects which MEASURED month is admissible and the measurement
# it admits carries zero DOF.
# (docs/PRECOMMIT-ercot261-gas-level-retirements-2026-09-09.md SS1c, SS6.)
ERCOT_GAS_CORROBORATION_TOL_USD_MMBTU: float = 1.00

# EIA-923 own-month gas-price plausibility band (SPP-46 R-1; owner ruling P19,
# 2026-09-08, repo-wide; ScenarioConfig.f923_gas_price_plausibility_screen,
# data/fuel/plant_prices.py::screen_gas_plant_month_prices). A plant's OWN
# reported EIA-923 Schedule-5 delivered gas cost for a month is kept only while
# it sits within [low, high] x the plant's own state's EIA delivered-to-electric-
# power price that month (series N3045<ST>3, $/Mcf -> $/MMBtu); outside the band
# it falls back to that reference. Below the band are negative and near-zero
# prints (Elk Station 58835 $0.16-0.41 every month of 2024; Mustang Station CC
# negative in seven months) that are not the marginal cost of the next MMBtu;
# above it are low-burn months whose AVERAGE cost carries a fixed transport /
# reservation charge over a near-zero denominator (Riverside 4940 Apr-2023
# $71.66 on 2,750 MMBtu) — an average cost on a different basis than the marginal
# fuel cost the LP prices (rule 14's misalignment exception). DECLARED, never
# swept: the band was fixed in PRECOMMIT-spp-46-2026-09-07.md §3(E) before any
# number existed and re-declared in PRECOMMIT-spp-49 §2.1; rule 1 (c) forbids
# selecting it on any gate. A structural plausibility threshold, not a tunable.
F923_GAS_PRICE_PLAUSIBILITY_BAND: tuple[float, float] = (0.5, 2.0)

# Commitment parameters by thermal class.
# Each entry: (heat_rate_cutoff, {startup_per_mw, min_run_hours, min_down_hours})
# Source: NREL/SR-5500-55433 (Kumar et al. 2012), OEM specs.
# The commitment heuristic uses these to screen whether a run of positive-margin
# hours justifies a physical startup.

CC_COMMITMENT_PARAMS: list[tuple[float, dict[str, float]]] = [
    (
        6.5,
        {"startup_per_mw": 63.8, "min_run_hours": 10, "min_down_hours": 8},
    ),  # h-class
    (7.5, {"startup_per_mw": 48.6, "min_run_hours": 8, "min_down_hours": 6}),  # f-class
    (99.0, {"startup_per_mw": 24.1, "min_run_hours": 5, "min_down_hours": 4}),  # older
]

CT_COMMITMENT_PARAMS: list[tuple[float, dict[str, float]]] = [
    (10.0, {"startup_per_mw": 12.3, "min_run_hours": 1, "min_down_hours": 1}),  # aero
    (11.0, {"startup_per_mw": 24.5, "min_run_hours": 1, "min_down_hours": 1}),  # frame
    (99.0, {"startup_per_mw": 19.0, "min_run_hours": 1, "min_down_hours": 1}),  # older
]
# Gas steam (legacy oil/gas boilers): high thermal inertia — slow to start, a
# real fuel/wear cost per start, and a long minimum run because a stop-start
# cycle is more expensive than idling at minimum load. The startup cost is far
# larger than a combustion turbine's and the min-run/min-down windows much
# longer, so these intermediate-duty units DRAG (hold online at part load)
# rather than cycle like peakers. ISO-gated on ScenarioConfig.gas_st_startup_cost
# (default OFF → ERCOT byte-identical); enabled for MISO's intermediate steam.
# Source: NREL/SR-5500-55433 (Kumar et al. 2012) gas-steam class, OEM specs.
ST_GAS_COMMITMENT_PARAMS: list[tuple[float, dict[str, float]]] = [
    (
        10.0,
        # efficient steam: min-run raised 12 -> 24h so a boiler committed for a
        # heat-wave / cold-snap stays online across the multi-day event rather
        # than two-shifting (NREL/SR-5500-55433 gas-steam cycling cost; a
        # stop-start is dearer than idling at minimum load over a sustained event).
        {"startup_per_mw": 55.0, "min_run_hours": 24, "min_down_hours": 8},
    ),  # efficient steam
    (
        99.0,
        # older subcritical: min-run raised 24 -> 48h (higher thermal inertia,
        # larger per-start wear cost — these legacy boilers drag online across a
        # whole multi-day temperature event rather than cycle).
        {"startup_per_mw": 75.0, "min_run_hours": 48, "min_down_hours": 12},
    ),  # older subcritical
]
ST_GAS_STARTUP_PARAMS: list[tuple[float, float]] = [
    (10.0, 55.0),  # efficient steam
    (99.0, 75.0),  # older subcritical
]

# Day-ahead unit-commitment horizon (hours). CAISO's day-ahead market (IFM +
# residual unit commitment) commits ONE 24-hour operating day at a time (CAISO
# Fifth Replacement FERC Electric Tariff §31.3; BPM for Market Operations,
# day-ahead timeline) — the same one-operating-day horizon every US ISO's DAM
# uses. A committed unit is therefore only ever HELD online at min-load across
# an idle gap that fits inside one DA commitment cycle; a longer gap is a
# next-day decommit/re-offer decision, not an intra-day hold, and the unit
# shuts down. Bounds the startup-cost-aware RA bridge when
# ScenarioConfig.caiso_ra_bridge_decommit is on.
DA_COMMITMENT_HORIZON_HOURS: int = 24

# Measured run-length ceiling that scopes the NYISO ONLINE-HOURS LSL state
# floor (ScenarioConfig.nyiso_gas_bridge_state_floor_min_run) to the
# near-baseload duty cohort: a CC plant carries the state floor only when its
# OWN measured plant-basis run-length p25
# (data/raw/_processed-legacy/campd_perplant_min_run_NYISO.csv, nyiso-146
# phase 0) is at or above this many hours. A POPULATION-GAP SEPARATOR, not a
# tuned value (rules 5/21): NYISO's live CC fleet measures p25s of
# {7, 8, 10, 12, 14, 15, 19.75} h (the cyclers/intermediates) then a 6.6x gap
# to {130 Poletti, 134.75 Bethlehem, 645.75 Caithness} (the near-baseload
# cohort the nyiso-146b unscoped arm repaired) — any threshold inside
# (19.75, 130) selects the identical membership; 100 is the round midpoint.
# The unscoped arm measured WHY the scope is needed: the state floor glued
# the intermediates too (Athens 2025: 9 model starts vs 63 metered; one new
# D-4 conviction at Saranac), exactly the plants below the gap.
NYISO_STATE_FLOOR_MIN_RUN_HOURS: float = 100.0

# Fast-start exclusion for the ECONOMIC (startup-cost) leg of the RA
# must-offer bridge. Holding a unit at min-load across a gap LONGER than its
# min-down is only ever the economic choice when the restart it avoids is
# genuinely slow and expensive — combined-cycle physics (min-down 4-8 h,
# $24-64/MW starts, CC_COMMITMENT_PARAMS above). A fast-start simple-cycle CT
# (min-down 1 h, $12-25/MW starts, CT_COMMITMENT_PARAMS) restarts within the
# hour, so the real market cycles it off overnight; economically bridging one
# forces exactly the units that DO cycle off (model-legitimacy audit §1.2c,
# rule 17: eligibility by unit physics, never a class-name tuple). The
# threshold sits at the CC table's own floor (the "older" CC class, 4 h) —
# every CC row qualifies, every CT row (1 h) is excluded. The PHYSICAL
# gap < min-down bridge is not gated by this: it is a restart bar, and for a
# 1 h min-down unit it can never fire anyway.
RA_BRIDGE_ECON_MIN_DOWN_HOURS: float = 4.0

# SPP gas commitment bridge (ScenarioConfig.spp_gas_commitment_bridge, lane
# SPP-44, PRECOMMIT-spp-44-2026-09-07 §2): the two MEASURED per-class
# statistics the bridge's floor reads, keyed by LP fuel type. Both come from
# the CAMPD 2023-2025 loading-when-on derive on the PLANT basis
# (scripts/data/derive_campd_gas_commitment_params.py --iso SPP --plant-basis
# -> data/raw/_processed-legacy/campd_gas_commitment_params_plant_SPP.csv):
# the facility's units are summed to ONE series before any statistic is
# taken, so the fraction is the plant's minimum stable CONFIGURATION over its
# full capability — the basis a floor multiplied by PLANT pmax requires
# (FINDING-caiso135 §A / §R adjudication; the shared detector floors
# min_load_frac x plant pmax, clipped to the base tranche). Per-unit values
# (CC 0.440 / ST 0.266) are reported in the same derive and NOT used.
#
#   min_load_frac  = HSL-weighted p50 of plant lsl_frac (LSL = p5 of
#                    online-hour load, HSL = p99.5 of pooled load):
#                    CC_REGULAR 0.209 (p25 0.141 / p75 0.320, 19 plants,
#                    10,403 MW); ST_GAS 0.090 (0.076 / 0.139, 26 plants,
#                    11,373 MW) — SPP's gas steam is legacy multi-unit
#                    stations running one boiler at a time.
#   min_run_hours  = capacity-weighted p25 of the plant-basis run-length
#                    distribution (an observed run bounds a minimum-run
#                    CONSTRAINT from above, so the low order statistic is the
#                    identification — the derive's own docstring, the nyiso-90
#                    precedent): CC_REGULAR 15 h (5,290 runs), ST_GAS 5 h
#                    (2,931 runs).
#
# Rules 5/13/21/23: measured unit-conduct properties that regenerate for any
# vintage and re-derive ONLY when the CAMPD extracts update — never from a
# residual. Rule 25: SPP's own market's data; NYISO's 0.523 / 0.239 and
# 21 / 13 h are not inherited. Read only when the SPP bridge gate is on.
SPP_GAS_BRIDGE_MIN_LOAD_FRAC: dict[str, float] = {"gas_cc": 0.209, "gas_st": 0.090}
SPP_GAS_BRIDGE_MIN_RUN_HOURS: dict[str, float] = {"gas_cc": 15.0, "gas_st": 5.0}

# Fast-start eligibility threshold (h) for the ERCOT offline fast-start pool
# offer leg (ScenarioConfig.ercot_faststart_pool_offer): a unit is
# SCED-startable intra-hour — the OFFQS/OFFNS telemetry family the pool
# ladder is measured on — iff its min-down fits inside the operating hour's
# dispatch horizon. CT physics (CT_COMMITMENT_PARAMS: 1 h min-down) clears
# the gate; every CC (4-8 h) and gas-steam (8-12 h) row fails it. Rule 17's
# own fast-start line (min-down <= 2 h); eligibility by unit physics, never
# a class-name tuple (rule 12 / charter §9.2,
# docs/handoffs/ercot-residual-midband-formation-lane-2026-07.md).
FASTSTART_POOL_MIN_DOWN_HOURS: float = 2.0

# SLOW-START eligibility band (h) for the ERCOT offline-increment re-pricing
# tier (ScenarioConfig.ercot_offline_commit_offer, ERCOT-176). The tier prices
# the capability whose next MW requires a START that cannot happen inside the
# operating hour — the complement of the fast-start pool above — at that
# class's own measured start-inclusive SCED2 ladder.
#
# Eligibility is UNIT PHYSICS, never a class-name tuple (rule 18
# [R-PHYSICS]). Both bounds are read off the committed commitment tables
# above, not fitted:
#   * min-down band [4, 8] h = CC_COMMITMENT_PARAMS' own floor and ceiling
#     (older 4 h, f-class 6 h, h-class 8 h). The floor coincides with
#     RA_BRIDGE_ECON_MIN_DOWN_HOURS above, already documented as the line
#     where "every CC row qualifies, every CT row (1 h) is excluded".
#   * min-run <= 12 h is the WITHIN-DAY start-and-run line: a unit whose
#     minimum run is 24-48 h is not making a within-day start decision at
#     all — its commitment is a multi-day choice. It sits above every CC
#     class (min-run 5/8/10 h) and below ST_GAS_COMMITMENT_PARAMS (24/48 h)
#     and coal, so the band admits the CC classes and excludes gas steam and
#     coal by physics.
#
# The min-run bound is load-bearing for rule 19 [R-ONE-MECH], not decoration:
# ST_GAS min-down (8 h) is inside the min-down band, and the gas-steam offer
# lane is REJECTED (`R`) from ERCOT-91 on the ERCOT-89 zero-spurious/C3a
# guards. Without the min-run bound this tier would silently re-test that
# closed cell.
# Source: NREL/SR-5500-55433 (Kumar et al. 2012) via the *_COMMITMENT_PARAMS
# tables above; docs/PRECOMMIT-ercot176-offline-increment-2026-08-07.md §1.
OFFLINE_COMMIT_MIN_DOWN_HOURS_MIN: float = 4.0
OFFLINE_COMMIT_MIN_DOWN_HOURS_MAX: float = 8.0
OFFLINE_COMMIT_MIN_RUN_HOURS_MAX: float = 12.0

# CAISO gas-fired MUST-OFFER Resource-Adequacy capacity (MW), by compliance
# year — the PUBLISHED quantity the RA must-offer bridge is gated to when
# ScenarioConfig.caiso_ra_mustoffer_quantity_gate is on (gap G-61 path (a)).
# Real CAISO attaches the must-offer obligation only to RA-CONTRACTED (shown)
# capacity; the ungated bridge floors the WHOLE merchant gas CC fleet, which
# over-commits CC through the solar belly (D-8 closure §7). Source: CAISO
# Department of Market Monitoring, Annual Report on Market Issues and
# Performance — "Average system resource adequacy capacity, availability, and
# performance by fuel type (RMO+ hours)": the "Must-Offer: Gas-fired
# generators" row (the category the California ISO inserts bids for — the
# literal 24x7 must-offer fleet; the separate "use-limited gas" category is
# NOT bid-inserted and is excluded here). 2023: 19,130 MW (2023 Annual
# Report, Jul 2024, Table 8.4); 2024: 15,566 MW (2024 Annual Report,
# Aug 2025, RA chapter table). 2025 carries the LATEST PUBLISHED vintage
# (the 2024 value) — the DMM 2025 Annual Report is unpublished as of
# 2026-07; refresh on its publication (a source-data change, rule 23 —
# never a residual). Values are NQC-basis annual RMO+-hour averages; the
# gate consumes them against model plant pmax (pmax ≥ NQC, so the gate is
# conservative in the strict direction — disclosed, not fitted).
CAISO_RA_MUSTOFFER_GAS_MW: dict[int, float] = {
    2023: 19130.0,
    2024: 15566.0,
    2025: 15566.0,  # latest published vintage (DMM 2024 Annual Report)
}

# Float-noise guard on the RA bridge's curtailed-VRE release (gap G-61 path
# (c), ScenarioConfig.caiso_ra_bridge_curtailment_release): a P0 hour counts
# as genuinely curtailing renewables only when wind+solar dispatch sits more
# than this many MW below the available potential. Purely numerical (LP
# round-off on Σ cf × cap sums spans ~1e-6..1e-2 MW); NOT a behavioural
# threshold — any physically-real curtailment event is orders of magnitude
# above it.
CAISO_CURTAIL_RELEASE_EPS_MW: float = 1.0

# Coal is not commitment-screened: EIA-930 confirms ERCOT coal runs all 8,760
# hours, cycling output level rather than starting and stopping.

# Physical minimum-stable level (Pmin/Pmax) of a *committed* thermal unit, by
# plant class. This is the turbine floor a unit holds once it is physically
# turned on — distinct from the offer-curve must-run tranche share (Pct_Must_Run),
# which is 0 for merchant units that carry no market must-offer obligation. The
# temperature-gated reliability floor reliability-commits these merchant units on
# an extreme day (RUC / cold-weather CT mobilization) and then enforces P ≥ Pmin,
# so its magnitude is sourced from THIS table, not from Pct_Must_Run.
# Source: NREL WWSIS-2 / TEPPC (NREL/TP-5500-55588) Table 7 — Western
# Interconnection per-type min-stable averages. PHYSICAL and forward-reproducible
# (regenerates for a forward year from engineering specs); NOT tuned to the
# backcast residual (CLAUDE.md #9/#11). Do not nudge these to improve MAE.
MIN_STABLE_PCT_PHYSICAL: dict[str, float] = {
    "ST_GAS": 0.12,  # gas steam — WWSIS-2 12% (older subcritical sits high end)
    "ST_CHP": 0.12,  # gas-steam cogeneration — same steam physics
    "CT_PEAKER": 0.38,  # simple-cycle CT — WWSIS-2 38% (older frame up to 50–60%)
    "CT_CHP": 0.38,  # simple-cycle CT cogeneration — same CT physics
    "CC_REGULAR": 0.52,  # combined cycle — WWSIS-2 52% (least-flexible fossil)
    "CC_CHP": 0.52,  # combined-cycle cogeneration — same CC physics
    # Subcritical/supercritical coal steam — WWSIS-2 40%; every coal subclass
    # (COAL-SUB, 2026-09-25: the bare ``COAL`` class is deleted).
    "COAL_LIGNITE": 0.40,
    "COAL_PRB": 0.40,
    "COAL_BIT": 0.40,
    "COAL_WC": 0.40,
    "oil": 0.12,  # oil / oil-steam — steam physics (taxonomy lumps oil into one)
}

# Sector-based behind-the-meter (BTM) share of nameplate pulled out of the grid
# LP as CHP host self-supply (fleet.CHP_SECTOR_CLASS_BY_PLANT assigns each
# plant to "industrial"/"commercial"/"merchant" from its EIA-923 Schedule-8
# sector classification).
#
# "industrial"/"commercial": re-derived from EIA-923 Schedule-8 CHP fuel
# allocation (independent of this model's own dispatch/backcast) — EIA's
# published CHP-sector analysis reports industrial-sector CHP plants
# allocating ~70% of fuel consumption to useful thermal output and
# commercial-sector plants ~65% (EIA Today in Energy, "Combined heat and
# power technology fills an important energy niche",
# https://www.eia.gov/todayinenergy/detail.php?id=8250, itself sourced from
# Schedule-8 CHP fuel-consumption/thermal-output reporting). A plant whose
# design dedicates most of its fuel to the host's thermal load is host-
# dominated in its electric output too, so the fuel-allocation share stands in
# for the BTM electric share. Replaces the prior values (60/60), which were
# hand-trimmed to 50/50 to close a Run-61..65 backcast residual (CLAUDE.md
# rule #22 — a derive input must not move because a residual moved).
#
# "merchant": no independent EIA sector-level split exists for merchant/IPP
# (NAICS-22) CHP hosts at this granularity — retained at its prior fitted
# value. Residual-identified, forecast-risk (open item for the DOF ledger,
# S5; G-26/issue #1335): replace when an independent merchant-CHP host-load
# source is found. R6 DOCUMENT-AND-KEEP disposition per
# docs/handoffs/scalar-remediation-plan-2026-07.md C-4 — deletion is not an
# improvement (0% would be an equally unsourced assumption) and the
# candidate fix (extending the EIA-923 intake to Schedule 8, filtered to the
# ~15-40 merchant-tagged plant codes, mirroring the industrial/commercial
# derivation above) is a data-intake project, not a hygiene edit; full
# survey of candidate sources and the recommended path in
# docs/handoffs/merchant-chp-host-load-memo-2026-07.md.
CHP_BTM_PCT_BY_SECTOR: dict[str, float] = {
    "merchant": 35.0,  # residual-identified, forecast-risk — no independent source yet
    "industrial": 70.0,  # EIA-923 Schedule-8: ~70% of CHP fuel to useful thermal output
    "commercial": 65.0,  # EIA-923 Schedule-8: ~65% of CHP fuel to useful thermal output
}
CHP_ST_BTM_PCT: float = 90.0  # ST_CHP group (tiny chemical host-steam): near-full BTM

# CC/CT startup costs ($/MW per start) keyed by ascending heat-rate cutoff.
# Used to amortize startup cost into the monthly bid markup: a generator bids
# above marginal cost to recover startup_cost / expected_run_length.
# Source: NREL/SR-5500-55433 (Kumar et al. 2012).
CC_STARTUP_PARAMS: list[tuple[float, float]] = [
    (6.5, 63.8),  # h-class
    (7.5, 48.6),  # f-class
    (99.0, 24.1),  # older
]
CT_STARTUP_PARAMS: list[tuple[float, float]] = [
    (10.0, 12.3),  # aero
    (11.0, 24.5),  # frame
    (99.0, 19.0),  # older
]

# DELETED 2026-07 (rule 26, G-26/C-12/issue #1335-adjacent audit sweep): a
# per-plant ERCOT CC_REGULAR peaking-tranche % (top slice of nameplate priced
# at the duct-burner peak multiplier) applied to exactly the four F-class(late)
# 2x1 CCs the model over-ran in the 80-90% CF range — not a published or
# physically-measured turbine limit, i.e. an answer-key scalar with no
# independent source. Confirmed dead at HEAD before deletion: the current
# ERCOT keeper (2026-07-06-ercot34-stage4-overlay-off) explicitly carries
# `cc_peaking_per_plant=False` (superseded by the measured EIA-860
# duct-burner mechanism, `cc_duct_peaking`/`fleet.cc_duct_peaking_pct`), and
# every non-ERCOT keeper's `cc_peaking_per_plant=True` drives only the
# CAMPD-measured `fleet.thermal_tranche_peaking` path — this dict's four
# ERCOT-specific plant codes never matched any other ISO's fleet. No keeper
# changes behavior from this deletion. Follow-up correction (same sweep): the
# ERCOT DEFAULT builder (pipeline/backcast_config.py) previously left
# `cc_duct_peaking` PJM-only and `cc_peaking_per_plant` unconditionally True
# for every ISO — deleting this dict without also fixing that default would
# have left ERCOT with NO per-plant peaking mechanism at all (silently
# regressing to the flat class-wide `pct_peaking`) unless a run happened to
# pass the existing `--cc-duct-peaking` CLI flag by hand, while simultaneously
# breaking every non-ERCOT ISO's default (`cc_peaking_per_plant` drives their
# real, already-keeper-validated CAMPD mechanism). Fixed: ERCOT's default is
# now `cc_duct_peaking=True` + `cc_peaking_per_plant=False`, matching every
# current ERCOT keeper exactly and generalizing the EIA-860 duct-burner
# mechanism to every ERCOT CC plant (not four named ones); CAISO/PJM/NYISO/
# NEISO/MISO defaults are restored to `cc_peaking_per_plant=True` unchanged.
# Extending `cc_duct_peaking` to those five ISOs by default is a distinct,
# real follow-up (EIA-860 would supersede their measured CAMPD mechanism for
# every EIA-860-covered plant) that needs its own per-ISO calibration probe +
# leave-one-year-out validation (rule 22) before promotion — not a silent
# default flip.

# DELETED 2026-07 (rule 26, G-26/C-8/issue #1336): COAL_TRANCHES was a
# documentation-only mirror of the coal take-or-pay supply-curve tranches —
# never imported or read anywhere (confirmed by grep: zero references outside
# an offer_curves.py docstring). A dead duplicate of a tunable is exactly the
# "re-armable answer key" rule 26 warns about (editing this list would
# silently do nothing), so it was removed rather than kept in sync by hand.
# The ScenarioConfig.coal_tranche_{1,2,3}_{frac,fuel_passthrough} fields it
# mirrored were themselves DELETED 2026-08-12 (ercot-188 G#3 owner ruling)
# along with their sole consumer offer_curves.split_coal_tranches — dead in
# build_dispatch_fleet's else limb for every registered bundle (proof:
# results/calibration/ercot188_g3_unreachability_proof.json).

# Legacy per-class heat-rate-override band defaults (econ/peak multipliers on the
# plant's base heat rate) for the CC / gas-steam / CT_CHP supply-curve override
# triples (``{cc,gas_st,ct}_*_hr_override`` in :class:`ScenarioConfig`). These
# fire ONLY when the corresponding ``*_committed_hr_override`` is explicitly set
# AND no ``offer_curve_by_group`` entry covers the group — i.e. the legacy
# non-``offer_curve`` path used by the original ERCOT calibration before the
# per-group offer curves existed. They are NOT ISO-generic fallbacks: no
# non-ERCOT keeper reaches them (every ISO carries a per-group offer curve), and
# rule #24 forbids their use as a cross-ISO fallback. Named here (rather than
# buried as ``getattr(config, ..., <literal>)`` defaults in ``data/fleet.py`` /
# ``data/offer_curves.py``) per audit rule #23 (no fallback literals in the offer
# path). Source: ERCOT DAM offer-shape grounding, docs/ercot-dam-offer-hrmults-
# 2026-06.md (part-load/duct-firing heat-rate spreads); ERCOT-lineage only.
CC_ECON_HR_OVERRIDE_DEFAULT: float = 1.2  # CC economic band ≈ 1.2× base HR
CC_PEAK_HR_OVERRIDE_DEFAULT: float = 1.8  # CC duct-firing peak ≈ 1.8× base HR
GAS_ST_ECON_HR_OVERRIDE_DEFAULT: float = 1.0  # gas-steam econ ≈ flat full-load HR
GAS_ST_PEAK_HR_OVERRIDE_DEFAULT: float = 1.5  # gas-steam peak ≈ 1.5× base HR
# (CT_ECON_HR_OVERRIDE_DEFAULT / CT_PEAK_HR_OVERRIDE_DEFAULT deleted 2026-08-03
# with the ct_*_hr_override triple they backed — rule 26 [R-DELETE], nyiso-114;
# see the ScenarioConfig note at the deleted fields. The CC and gas-steam
# defaults above are untouched: their triples are still reachable.)

# Gas offer-curve tranche SHARES (committed / economic / peaking) of nameplate
# by group, for the generic (non-CAMPD) offer curve
# (:func:`market_sim.data.offer_curves.split_gas_tranches`). These are
# STRUCTURAL capacity splits — how a unit's nameplate divides into offer
# bands — not tuned heat-rate multipliers, so they are ISO-neutral and stay
# generic (rule #24: no hardcoded per-plant/per-group dicts in ``data/``
# modules — moved here from a module-level literal in ``offer_curves.py``
# during the 2026-07 scalar-remediation sweep, B-GOV-1; value unchanged, C-11
# closure verification). CTs are peakers with no part-load committed band;
# CC/ST split a part-load committed band off the efficient economic band,
# plus a small duct-fired peaking top slice. The per-band heat-rate
# MULTIPLIERS applied to these shares come from the ``*_hr_mult`` /
# ``*_peak_hr_penalty`` ScenarioConfig fields (ERCOT-lineage defaults); D-9
# (scripts/legitimacy_diagnostics.py) forbids a non-ERCOT ISO from reaching
# this path without carrying its own ``offer_curve_by_group`` bands, so no
# cross-ISO leakage of those multipliers occurs.
GAS_TRANCHE_SHARES_BY_GROUP: dict[str, tuple[float, float, float]] = {
    "CC_REGULAR": (0.30, 0.60, 0.10),
    "CC_CHP": (0.30, 0.60, 0.10),
    "ST_GAS": (0.40, 0.50, 0.10),
    "ST_CHP": (0.40, 0.50, 0.10),
    "CT_PEAKER": (0.0, 0.88, 0.12),
    "CT_CHP": (0.0, 0.88, 0.12),
}

# Gas-offer net-revenue margin ANCHOR ($/MMBtu) by ISO — the delivered-gas
# identification point of the ``gas_offer_net_revenue_margin`` mechanism
# (:func:`market_sim.data.offer_curves.apply_gas_offer_margin`). Each value is
# the mean of the model's own merit-order delivered-gas series
# (``data.fuel.trajectories._gas_series`` — measured EIA Henry Hub monthly ×
# the ISO's measured hub basis, the exact series the registered
# ``offer_curve_by_group`` band multipliers were calibrated against) over the
# training window 2023–2025. At ``fuel == anchor`` the reformed offer reduces
# EXACTLY to the registered band multiplier, so the anchor is an
# identification constant, not a tunable: it re-derives ONLY when the gas
# source workbooks change (rule 23), via
# ``scripts/data/derive_gas_offer_margin_anchor.py``.
# Each value is the derive script's output 2026-07-23 (each ISO's keeper gas
# overlay; TRAIN_WINDOW_HH Henry Hub 2.54 / 2.19 / 3.52), design doc
# docs/handoffs/gas-offer-net-revenue-margin-design-2026-07.md:
#   ERCOT: 2.2494 = mean(2.0394, 1.6895, 3.0192) — annual-HH + seasonality
#     delivered series (ercot99: no monthly actuals / hub overlay; Waha-ish
#     discount to HH).
#   PJM:   3.3483 = mean(3.2551, 2.8556, 3.9341) — monthly-actuals delivered
#     (keeper --gas-monthly-actuals; +GAS_BASIS_DIFFERENTIAL PJM).
#   CAISO: 4.7964 = mean(6.9524, 3.3721, 4.0646) — SoCal/PG&E Citygate
#     hub-basis overlay (the 2023 western-gas-crisis year lifts the mean).
#   MISO:  3.0492 = mean(2.8392, 2.4893, 3.8190) — annual Henry Hub + the flat
#     GAS_BASIS_DIFFERENTIAL["MISO"] = 0.30 Chicago-Citygate footprint blend,
#     with mean-preserving seasonality + daily shape.
#     *(DESCRIPTION CORRECTED 2026-09-05 by miso-215, MEASURED, VALUE UNTOUCHED:
#     this read "per-plant EIA-923 monthly level + mean-preserving daily shape".
#     GAS_SERIES_FLAGS["MISO"] is {gas_seasonality, gas_daily_shape,
#     miso_zonal_gas_basis} and `_gas_series` is ISO-level, so it cannot carry a
#     per-plant 923 level; reproducing it gives series − HH = +0.2992 / +0.2993 /
#     +0.2990 in 2023/2024/2025 — the flat 0.30 basis constant, in every year.
#     The per-plant EIA-923 print (gas_plant_monthly_fuel_pricing) applies on the
#     (n_gen, T) array AFTER this series and is invisible to the derive, so the
#     ANCHOR and the FLEET's delivered price are identified on different bases:
#     `results/calibration/_miso215_intermediate_phys.json` M3a, and
#     `FINDING-miso215-intermediate-phys-coverage-2026-09-05.md` §4. Whether the
#     identification point should stay the ISO series is an OWNER question this
#     lane routed; nothing here changes the value or any solve.)*
#   NYISO: 3.9046 = mean(3.3566, 2.7969, 5.5602) — monthly actuals + zonal
#     pipeline-hub basis + Transco Z6 daily overlay.
#   NEISO: 4.0763 = mean(2.9365, 3.0304, 6.2621) — Algonquin (AGT) hub-basis
#     delivered series.
# ISOs absent from this registry hard-fail when the flag is armed (never a
# silent fallback — rule 25); tuned per-ISO anchors never cross ISO
# boundaries (rule 24).
GAS_OFFER_MARGIN_ANCHOR_BY_ISO: dict[str, float] = {
    "ERCOT": 2.2494,
    "PJM": 3.3483,
    "CAISO": 4.7964,
    "MISO": 3.0492,
    "NYISO": 3.9046,
    "NEISO": 4.0763,
    # SPP is DELIBERATELY ABSENT at registration (2026-09-06, lane SPP-20):
    # every value above is the output of scripts/data/derive_gas_offer_margin_
    # anchor.py run on that ISO's OWN keeper gas series (rule 23 — a frozen
    # derive, never hand-entered), and SPP has no gas-series recipe or keeper
    # yet. The flag this anchors is default-off, so the registered hard-fail
    # ("ISOs absent from this registry hard-fail when the flag is armed") is
    # exactly the right behaviour until SPP-40 derives it on the first keeper.
}

# MEASURED min-load block-average burn ratio of the ST_GAS plants that
# ``offer_curves._offer_curve_for_group`` EXCLUDES from ``offer_curve_by_group``
# — its ``ST_GAS_PEAKER_PLANTS`` bypass — by ISO. Consumed ONLY under
# ``ScenarioConfig.caiso_st_gas_committed_measured`` (gated, default off).
#
# WHY THE REGISTRY EXISTS (caiso-239, rule 24 [R-REGISTRY] / rule 14
# [R-ACCURATE]). A bypassed ST_GAS bin never reaches
# ``committed_hr = base_hr x offer["committed"]`` in ``fleet.assembly``, so its
# committed band falls through to the ERCOT-lineage class default
# ``fleet.campd_bins._DEFAULT_HR_MULT_BY_GROUP["ST_GAS"]["mc"] = 1.15`` — an
# UNCITED literal in a data/ module, absent from ``run_config.json`` and from
# the DOF ledger's ``offer_curve_by_group`` count. For CAISO that literal
# prices the whole 2,858.8 MW once-through-cooling steam fleet (plants 315 AES
# Alamitos, 335 AES Huntington Beach, 350 Ormond Beach — the three plants
# ``ST_GAS_PEAKER_PLANTS`` names) while CAISO's own measurement of THOSE EXACT
# UNITS sits unused. This registry is the measured replacement.
#
# CAISO 1.683 = ``avg_committed_p50`` for class ST_GAS in
# ``data/raw/reference/caiso_campd_marginal_hr_summary.csv`` (base HR 11.847,
# n_units 10). Those ten units are exactly plants 315/335/350 —
# ``data/raw/_processed-legacy/campd_gas_commitment_params_CAISO_units.csv``
# lists Alamitos 3/4/5/CT1/CT2, Huntington Beach 2/CT1/CT2 and Ormond Beach 1/2
# and no others — so the statistic's population and the band's population
# COINCIDE, which is what makes this a rule-14 measured-for-estimate
# substitution rather than a transplant. It is the SAME key already resolved
# onto this class as ``phys_committed`` in
# ``pipeline.backcast_config._CAISO_OFFER_CURVE``, so arming it adds no new
# measurement and no free parameter (rule 21 [R-DOF]).
#
# DISPERSION, DISCLOSED (caiso-239 §1 F-5): ST_GAS is the only CAISO class whose
# ``avg_committed`` spread is wide — p25 0.682 / p50 1.683 / p75 3.275, ratio
# 4.80, against 1.12-1.27 for every other gas class. The spread is real physical
# bimodality (six steam units at LSL 7.6-10.0 % of HSL pooled with four
# colocated CTs at 22.0-28.2 %), and the tranche this value prices is sized
# 6.3-9.3 % of nameplate — the STEAM min-load block, whose own statistic sits
# near p75. The class p50 is therefore the CONSERVATIVE choice for this tranche,
# not a midpoint of convenience.
#
# Re-derives ONLY when the CAMPD source updates (rule 23 [R-FROZEN-DERIVE]).
# No other ISO has a measured counterpart yet; an ISO absent from this registry
# cannot arm the mechanism (rule 25 [R-ISO-SCOPE] — the gate hard-errors rather
# than silently falling back to the class default).
ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO: dict[str, float] = {
    "CAISO": 1.683,
}

# MEASURED PEAK-band offer multiplier of the same bypassed ST_GAS plants, by
# ISO. Consumed ONLY under ``ScenarioConfig.caiso_st_gas_peak_measured``
# (gated, default off). The ``mc`` sibling of the registry directly above; the
# two are DISJOINT BY BAND (rule 19 [R-ONE-MECH]) — that one moves the committed
# band and nothing else, this one the peak band and nothing else.
#
# WHY THIS REGISTRY EXISTS (caiso-240, rule 24 [R-REGISTRY] / rule 14
# [R-ACCURATE]). The caiso-240 census measured the full footprint of all 28
# ``fleet.campd_bins._DEFAULT_HR_MULT_BY_GROUP`` literals on all six designated
# keepers, and found that after caiso-239 exactly TWO cells remain live on the
# CAISO keeper — ``ST_GAS["econ"] = 1.00`` and ``ST_GAS["peak"] = 1.10`` — both
# on the same 2,858.8 MW once-through-cooling steam fleet (plants 315 / 335 /
# 350) reached through the same ``ST_GAS_PEAKER_PLANTS`` offer-curve bypass.
# ``peak`` is the one of the two that has a measured counterpart AT THE MODEL'S
# OWN GRAIN: the bypassed plant's peak band is a single flat multiplier, and the
# measurement is a single number.
#
# CAISO 1.166 = ``CT_PEAKER.bands.peak`` in the committed
# ``data/raw/_validation-source/caiso_offer_curve_measured.json`` (CAISO OASIS
# Public Bid Data, PUB_DAM_GRP masked DAM bids, trade years 2023-2025). It is
# the SAME value the CAISO ``ST_GAS`` class band already carries on the keeper,
# armed there by ``caiso_offer_surface_measured_ungrounded`` at caiso-231 — and
# ``derive_caiso_offer_surface.py`` discloses why that class assignment is
# sound: *"the three OTC/RMR steamers (ST_GAS ...) and priced CT_CHP curves land
# in the CT bucket"*. So the measurement's population CONTAINS exactly the
# plants this registry prices, while the class band it was written onto reaches
# none of them.
#
# POPULATION MATCH IS CONTAINMENT, NOT COINCIDENCE — DISCLOSED AGAINST INTEREST.
# Unlike caiso-239's ``avg_committed_p50`` (whose ten CAMPD units ARE plants
# 315/335/350 and no others), the CT bucket is the pooled
# CT_PEAKER + CT_CHP + ST_GAS conduct and the OASIS ids are masked, so the
# steamers cannot be isolated inside it. This is the SAME basis on which
# caiso-231 re-grounded the ST_GAS class band and promoted the result, applied
# now to the plants the class band was measured on and never reaches.
#
# BID CONDUCT, NOT PHYSICS — hence the rule-13 treatment DIFFERS from
# caiso-239's. That mechanism arms a measured PHYSICAL heat-rate ratio (a
# boiler's part-load burn, year-independent) and is deliberately NOT a
# backcast-only overlay. This one arms measured BID conduct from a specific
# year's OASIS record, exactly like its ``caiso_offer_surface_measured*``
# siblings, so it IS registered in ``_BACKCAST_ONLY_OVERLAY_FIELDS``.
#
# Re-derives ONLY when the OASIS source updates (rule 23 [R-FROZEN-DERIVE]).
# An ISO absent from this registry cannot arm the mechanism (rule 25
# [R-ISO-SCOPE] — the gate hard-errors rather than silently falling back to the
# class default).
ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO: dict[str, float] = {
    "CAISO": 1.166,
}

# ZONE-resolved delivered-gas anchor ($/MMBtu) — the same identification point
# as ``GAS_OFFER_MARGIN_ANCHOR_BY_ISO`` above, evaluated at the grain the
# mechanism's own definition requires, for the ISOs whose keeper applies a
# PER-ZONE delivered-gas basis (nyiso-109).
#
# ``apply_gas_offer_margin``'s identity is *at ``fuel == anchor`` the reformed
# offer reduces EXACTLY to the registered band multiplier* — a statement about a
# unit's OWN delivered fuel. The ISO anchor above is derived from
# ``data.fuel.trajectories._gas_series``, which is ISO-level: it carries the hub
# overlay but NOT the per-zone basis, which the solve applies afterwards on the
# ``(n_gen, T)`` array. On an ISO with no zonal basis the two are the same
# series and the ISO anchor is correctly identified everywhere. On NYISO they
# are not: ``apply_nyiso_zonal_gas_basis`` is anchored so the REFERENCE zone
# (Capital_Hudson, Iroquois Z2) is unchanged and every other zone shifts DOWN to
# its own measured pipeline hub, so a unit in NYC (Transco Z6 NY) or
# Upstate_West (Tenn Z4 200L) pays persistently less than the ISO series — and
# ``markup_hr × (anchor − fuel)`` then adds a margin uplift its band multiplier
# was never calibrated to carry (the further below the anchor, the larger the
# uplift). Resolving the anchor per zone restores the mechanism's own identity
# in every zone; the reference zone's value is the ISO anchor unchanged.
#
# Values are the derive script's output
# (``scripts/data/derive_gas_offer_margin_anchor.py --iso <ISO> --by-zone``),
# which applies the RUNTIME zonal-basis transform to the same delivered series
# over the same 2023-2025 training window, so these are by construction the
# levels the solve prices those zones' gas units at.
#
# NYISO (nyiso-109, derived 2026-08-01) — reference-zone convention
# (``apply_nyiso_zonal_gas_basis`` holds Capital_Hudson / Iroquois Z2 at 0 and
# shifts every other zone DOWN), so the ISO anchor is the reference level and
# the pre-fix defect was one-sided over-marking:
#   Capital_Hudson / Lower_Hudson / Long_Island  3.9046 = mean(3.3566, 2.7969,
#     5.5602) — the reference hub, identical to the ISO anchor.
#   NYC          2.7612 = mean(2.0166, 2.0869, 4.1802) — Transco Z6 NY.
#   Upstate_West 2.0346 = mean(1.8966, 1.7269, 2.4802) — Tenn Z4 200L.
#
# PJM (pjm-144, derived 2026-08-02) — capacity-weighted MEAN-ZERO convention
# (``apply_pjm_zonal_gas_basis`` -> the ``basis.meanzero`` core subtracts the
# GAS-CAPACITY-weighted fleet mean of the per-zone basis, so the ISO anchor is
# the fleet centroid and the pre-fix defect was TWO-SIDED: premium eastern
# zones under-marked, discount western zones over-marked). Because the runtime
# transform depends on the fleet's per-zone gas capacity, the derive carries
# the keeper's own per-year fleet weights:
# ``--weights-bundle results/calibration/pjm143_hy_level_B`` (rebuilt no-LP via
# scripts.lib.bundle_fleet.reconstruct_bundle_fleet; per-year capacity-weighted
# means removed: -0.105 / +0.169 / +0.239 $/MMBtu). Basis source is the
# committed per-zone EIA delivered-to-electric-power table
# data/raw/pjm_zonal_gas_hub.csv:
#   PJM_SWMAAC     4.4328 = mean(3.7841, 3.6357, 5.8786) — Transco Z6 (MD).
#   PJM_Dominion   3.8798 = mean(4.1211, 3.3207, 4.1976) — Transco Z6/TETCO M3 (VA).
#   PJM_EMAAC      3.4898 = mean(3.0401, 2.8117, 4.6176) — Transco Z6 non-NY (NJ).
#   PJM_ComEd      3.2575 = mean(3.2521, 2.8067, 3.7136) — Chicago Citygate (IL).
#   PJM_AEP_Ohio   3.1201 = mean(3.1141, 2.7427, 3.5036) — Appalachian (OH).
#   PJM_ATSI       3.1201 = mean(3.1141, 2.7427, 3.5036) — Appalachian (OH).
#   PJM_Central_PA 2.9708 = mean(2.9281, 2.5497, 3.4346) — TETCO M3 (PA).
#   PJM_West_APS   2.9495 = mean(2.7871, 2.5917, 3.4696) — Appalachian (WV).
#
# ERCOT (ercot-150, derived 2026-08-02) — capacity-weighted mean-zero spread
# PLUS flat measured LEVEL convention (``apply_ercot_zonal_gas_basis``, ERCOT's
# own basis module): each zone's EIA-923 basis minus the gas-capacity-weighted
# fleet mean, plus the measured TX delivered-to-electric-power level correction
# (EIA N3045TX3 minus the −0.50 scalar baked into the ISO anchor: +0.500 /
# +0.417 / +0.045 in 2023/24/25) — so the ISO anchor is BELOW the fleet
# centroid and six zones sit above it while Waha-priced West sits below. The
# anchors are read from the keeper reconstruction's own resolved fuel_prices
# (``derive_gas_offer_margin_anchor.SOLVE_FUEL_ARRAY_ISOS``; weights bundle
# ``results/calibration/ercot149_gas_event_cap_arm`` rebuilt no-LP via
# scripts.lib.bundle_fleet.reconstruct_bundle_fleet), the exact array
# ``apply_gas_offer_margin`` prices against, so the West value includes the
# keeper's ``ercot_west_netload_gas_shape`` burner-tip floor lift (post-basis
# 1.62/0.21/0.65 → realized 1.99/1.15/2.74 — the two-regime step confines the
# Waha collapse to the measured 3/42/11 % of hours and prices the rest at firm
# Waha, restoring most of the West annual level). Basis source
# data/raw/ercot_zonal_gas_hub.csv; EP series
# data/raw/ercot_electric_power_gas_price.csv; per-year capw means removed
# +0.18 / +0.04 / +0.02 $/MMBtu (full record with the West decomposition in
# results/calibration/_ercot150_zonal_anchor_derivation.json):
#   South         3.2778 = mean(3.5721, 2.6518, 3.6094) — South TX/Agua Dulce.
#   South_Central 2.7578 = mean(2.9021, 2.4718, 2.8994) — South TX hubs.
#   North         2.7178 = mean(2.4721, 2.2318, 3.4494) — North/East-TX complex.
#   Northeast     2.7178 = mean(2.4721, 2.2318, 3.4494) — proxy→North (E-TX).
#   Houston       2.3111 = mean(2.1921, 1.8718, 2.8694) — Houston Ship Channel.
#   West          1.9586 = mean(1.9866, 1.1497, 2.7396) — Waha, net-load-shaped.
#   (Panhandle carries no gas capacity in any training year and is omitted —
#   zones absent from the map keep the window anchor, a no-op on an empty
#   zone.)
#
# MISO (miso-119, derived 2026-08-03) — capacity-weighted MEAN-ZERO convention
# (``apply_miso_zonal_gas_basis`` -> the same ``basis.meanzero`` core as PJM,
# no level term), so the ISO anchor is the fleet centroid and the pre-fix
# defect is TWO-SIDED: the Gulf-premium South (persistent +0.30/+0.39/+0.34
# raw basis) under-marked, the Chicago-basis eastern-Midwest zones and the
# MidCon West/Plains over-marked. Derived on the keeper's own per-year fleet
# weights: ``--weights-bundle results/calibration/miso117_ctheatrate_B``
# (rebuilt no-LP via scripts.lib.bundle_fleet.reconstruct_bundle_fleet;
# per-year capacity-weighted means removed +0.154 / +0.272 / +0.061 $/MMBtu).
# MISO is deliberately NOT in ``SOLVE_FUEL_ARRAY_ISOS``: its per-plant gas
# pricing (``gas_plant_monthly_fuel_pricing``) lives in the margin's own
# hour-by-hour ``fuel`` tracking, and the zonal anchor corrects exactly the
# zone-spread term the zonal basis adds (miso-119 prereg §2). Basis source is
# the committed per-zone EIA delivered-to-electric-power table
# data/raw/miso_zonal_gas_hub.csv:
#   MISO-South    3.2291 = mean(2.9807, 2.6052, 4.1013) — Gulf Coast (LA).
#   MISO-West     2.9641 = mean(3.1447, 2.5742, 3.1733) — MidCon/N. Natural (IA).
#   MISO-Plains   2.9641 = mean(3.1447, 2.5742, 3.1733) — MidCon/N. Natural (IA).
#   MISO-Illinois 2.8971 = mean(2.5777, 2.3372, 3.7763) — Chicago Citygate (IL).
#   MISO-Indiana  2.8971 = mean(2.5777, 2.3372, 3.7763) — Chicago Citygate (IL).
#   MISO-East     2.8971 = mean(2.5777, 2.3372, 3.7763) — Chicago Citygate (IL).
#
# An identification constant, not a tunable: rule 23 [R-FROZEN-DERIVE], it
# re-derives ONLY when the gas source data, the per-zone hub table, the EP
# series, or (for a capacity-weighted ISO) the keeper fleet recipe the weights
# are read from changes, never because a price residual moved. ISOs absent
# from the registry hard-fail when the zonal gate is armed (never a silent
# fallback — rule 24), and a zone table is that ISO's own measured basis and
# never crosses a boundary (rule 25).
GAS_OFFER_MARGIN_ANCHOR_BY_ZONE: dict[str, dict[str, float]] = {
    "NYISO": {
        "Upstate_West": 2.0346,
        "Capital_Hudson": 3.9046,
        "Lower_Hudson": 3.9046,
        "NYC": 2.7612,
        "Long_Island": 3.9046,
    },
    "PJM": {
        "PJM_ComEd": 3.2575,
        "PJM_AEP_Ohio": 3.1201,
        "PJM_ATSI": 3.1201,
        "PJM_West_APS": 2.9495,
        "PJM_Central_PA": 2.9708,
        "PJM_Dominion": 3.8798,
        "PJM_EMAAC": 3.4898,
        "PJM_SWMAAC": 4.4328,
    },
    "ERCOT": {
        "West": 1.9586,
        "North": 2.7178,
        "Northeast": 2.7178,
        "Houston": 2.3111,
        "South_Central": 2.7578,
        "South": 3.2778,
    },
    "MISO": {
        "MISO-West": 2.9641,
        "MISO-Plains": 2.9641,
        "MISO-Illinois": 2.8971,
        "MISO-Indiana": 2.8971,
        "MISO-East": 2.8971,
        "MISO-South": 3.2291,
    },
}

# Delivered-COAL anchor ($/MMBtu) — the identification point of the
# ``coal_offer_net_revenue_margin`` mechanism (ERCOT-137, the gas form's coal
# analogue; :func:`market_sim.data.fleet.legacy_bins.apply_coal_tranches`).
# Each value is the training-window (2023–2025) capacity-weighted mean of the
# model's own delivered coal price at the LP seam — per-plant EIA-923 receipts
# where published (Fayette / J K Spruce / San Miguel, the only ERCOT
# reporters; ercot135 §3), the measured coal supply trajectories elsewhere —
# read from the COMMITTED seam capture
# ``results/calibration/ercot135_coal_merit_order.json`` (A_model_offer
# per_plant ``fuel_price_mmbtu`` × ``pmax_mw``; year means
# 1.8169 / 1.7556 / 1.6436). An identification constant, not a tunable: it
# re-derives ONLY when the underlying coal price sources change (rule 23),
# via ``scripts/data/derive_coal_offer_margin_anchor.py``. ISOs absent from
# the registry hard-fail when the flag is armed (rule 24 — never a silent
# fallback); the ERCOT value is identified on ERCOT SCED conduct and never
# crosses ISO boundaries (rule 25).
COAL_OFFER_MARGIN_ANCHOR_BY_ISO: dict[str, float] = {
    "ERCOT": 1.7387,
}

# Measured coal min-load offer LEVEL ($/MWh) — the other half of the
# ``coal_offer_net_revenue_margin`` identification: the real fleet's RT
# supply-curve bottom, 60-Day SCED ``Submitted TPO-Price1`` capacity-weighted
# p50 at 98.8–100 % coverage, pooled res-hours-weighted across the four
# 2024–2025 disclosure subsets (16.86 / 16.37 / 15.00 / 15.00 →
# 15.8807; committed artifact
# ``results/calibration/ercot136_coal_headroom_conduct.json``
# B1_curve_bottom, the ERCOT-136 §3 decisive measurement). The min-load
# block's own declared price corroborates it independently (Min Gen Cost p25
# $18.00, 28–31 % coverage — corroboration only, never the anchor). At
# ``fuel == anchor`` the resolved ``_mustrun`` bid equals this level exactly.
# 2023 application is a declared extrapolation, gated LOYO per-year in the
# ERCOT-137 precommit. Its ORIGINAL premise ("no 2023 SCED disclosure exists")
# was dissolved by the ercot-157 delivery-2023 corpus re-upload and TESTED at
# ercot-169 (matrix §5.1 item 13, Phase 0, no LP; decision rule pre-registered
# in docs/PRECOMMIT-ercot169-margin-fuel-invariance-2026-08-05.md; full record
# results/calibration/ercot169_margin_fuel_invariance.json +
# FINDING-ercot169-margin-fuel-invariance-2026-08-05.md). **The test could not
# be completed: NOT-IDENTIFIABLE-2023.** The instrument's own licensing test
# (ERCOT-138 §3.4 curve coverage) fails on the delivery-2023 COAL rows —
# curve_share 0.9702 (full-day 0.9794) against the 0.9876 floor this constant
# was licensed on — because Martin Lake units 1-3 (~2.3 GW) submit NO
# incremental curve in 20-24 % of their online intervals, concentrated
# March-June 2023 (monthly curve_share 0.907-0.937 there vs 0.995-1.000 in
# Jan and Jul-Nov). A biased instrument cannot certify OR refute, so the
# verdict is withheld in both directions and the extrapolation note STANDS.
# Reported UNLICENSED at ercot-169, not as a verdict: the 2023 measured bottom
# was 18.380 $/MWh, i.e. level_2023 = 17.5211 after removing this form's own
# fuel response, +1.6404 = 1.76× the ±0.9300 band.
#
# **RESOLVED AT ercot-171 (2026-08-05) — the extrapolation note is RETIRED BY
# VERIFICATION, and the ercot-169 UNLICENSED reading above is SUPERSEDED: it was
# the coverage defect, not the level.** On the owner's in-session adjudication of
# the ERCOT-169 §6 open decision (option 2, "charter a licensed sub-population
# instrument"), the coverage shortfall was removed by a RULE applied identically
# to every year — drop the COAL resources whose OWN curve_share falls below the
# SAME 0.9876 floor (never lowered) — and the resulting instrument was gated on
# its NEUTRALITY: the identical rule applied to the four 2024/25 identification
# subsets must still reproduce this constant within its own band, because a
# coverage restriction is admissible only if it fixes coverage and not level.
# Both gates PASS. G-LIC: delivery-2023 curve_share 0.97022 → **0.99969** (the
# rule drops CALAVERS_JKS2, MLSES_UNIT1/2/3, WAP_WAP_G8). G-NEUT: the restricted
# 2024/25 pooled level is 15.4549 vs this constant's 15.8807, **−0.4258 = 0.46×
# the band** — level-neutral. The restricted delivery-2023 reading is then
# measured bottom 16.87 → **level_2023 = 16.0111**, i.e. **+0.1304 above this
# constant = 0.14× the ±0.9300 band — CONFIRMED** (full-day T2 16.0811, also
# inside). So this constant IS the measured 2023 level; its 2023 application is
# no longer an extrapolation but a verification. No solve, no new mechanism, no
# new DOF, keeper unchanged. **Caveat carried, not buried:** the alternative
# month-scoped restriction (S2, pre-declared REPORTED-NOT-GATING before
# measuring, because season selection biases a coal statistic the ercot-168
# repricing showed is seasonally structured) licenses at 0.99818 but reads
# level_2023 17.8411, +1.9604 = 2.11× band — OUTSIDE. S2 keeps Jan + Jul-Nov and
# so selects the scarcity season, which lifts a curve-BOTTOM statistic in exactly
# the direction observed; the pre-registered gate is S1 and S1 passes, but the
# two routes disagree and that should be read alongside the verdict, not behind
# it. Record: docs/PRECOMMIT-ercot171-coal-licensed-subpopulation-2026-08-05.md,
# results/calibration/ercot171_coal_licensed_subpop.json +
# FINDING-ercot171-coal-licensed-subpopulation-2026-08-05.md.
# Re-derives only with its source disclosure (rule 23), via the same derive
# script (``--year`` runs the ercot-169 test); per-ISO, never transferred
# (rule 25).
COAL_OFFER_MARGIN_LEVEL_BY_ISO: dict[str, float] = {
    "ERCOT": 15.8807,
}

# Measured CC committed-block offer LEVEL ($/MWh) — the identification constant
# of the ``cc_committed_offer_margin`` mechanism (ERCOT-139, the gas-CC analogue
# of the coal min-load net-revenue margin above;
# :func:`market_sim.data.offer_curves.apply_cc_committed_offer_margin`). The
# real CC fleet's RT supply-curve bottom expressed at the delivered-gas anchor:
# 60-Day SCED ``Submitted TPO-Price1`` capacity-weighted p50, pooled
# res-hours-weighted across the four 2024–2025 disclosure subsets (committed
# artifact ``results/calibration/ercot136_coal_headroom_conduct.json``
# B1_curve_bottom, CC rows — the same measurement, instrument, construction and
# loader that supplied coal's level, read off its COAL twin). Curve coverage on
# those rows is 95.1–98.0 % of RT-dispatchable headroom, so CC passes the same
# RT-instrument licensing test coal passed (ERCOT-138 §3.4).
#
# The raw subset bottoms are NOT year-invariant (2024 $10.07 / 2025 $18.07 —
# delivered gas moved 2.213 → 3.232 $/MMBtu); the margin form's claim is that
# the residual ABOVE fuel is, so the level is identified by removing the
# corpus's own measured fuel response (HR_implied 7.8521 $/MMBtu, from the
# disclosure itself — no model heat rate, no fitted slope):
#   level_i = bottom_i − HR_implied × (fuel_i − anchor)
#   10.1158 / 10.6358 / 9.6746 / 11.0146 → 10.354 res-hours-weighted.
# Identification quality: cross-subset dispersion ±42.98 % raw → ±6.47 %
# anchored, and the INDEPENDENT ``Min Gen Cost`` p50 instrument at 70–82 %
# coverage lands 10.6662 (3.02 % away). Coal's corroborating instrument sat at
# 28–31 % coverage, so this level is the better-attested of the two.
#
# The ANCHOR is NOT a second constant: the mechanism reuses
# ``GAS_OFFER_MARGIN_ANCHOR_BY_ISO`` (ERCOT 2.2494) so the whole gas offer
# surface keeps ONE identification point that cannot drift against itself
# (rule 19 [R-ONE-MECH] bookkeeping). At ``fuel == anchor`` the resolved
# ``_committed`` bid equals this level exactly.
#
# **The 2023 declared extrapolation is RETIRED BY VERIFICATION (ercot-169,
# 2026-08-05 — matrix §5.1 item 13, Phase 0, no LP, keeper UNCHANGED).** Its
# premise ("no 2023 SCED disclosure exists") was dissolved by the ercot-157
# delivery-2023 corpus re-upload, and because this is a MARGIN form the corpus
# tested the fuel-invariance claim itself rather than merely re-deriving. On
# the delivery-2023 corpus (2.34 M rows, 365 days), reconstructing THIS
# identification's own instrument (ERCOT-136 §B1 HSL-cap-weighted p50 curve
# bottom, same row filters, same cap-weighting, CPT→CST at derivation) on the
# window three of the four identification subsets sample (h11–22 CST):
#   measured bottom 13.390 − 7.8521 × (2.6012 − 2.2494) = **level₂₀₂₃ 10.6276**
# against the armed 10.354 — **+0.2736, inside the ±6.47 % (±$0.6699) band this
# constant is identified to**, i.e. 0.41 of the band. The full-day read agrees
# (10.7076, +0.3536) and the raw-CPT clock sensitivity is ±$0.01. The
# delivered-gas basis is the identification's OWN (ERCOT-138 §J ``fuel_capwtd``),
# re-established by a no-LP keeper reconstruction that reproduces its committed
# 2024/2025 values to 2.2129/3.2324 vs 2.213/3.232. **Caveat carried, not
# buried:** the licensing margin is negligible — 2023 CC curve coverage is
# 0.95084 against the 0.95054 floor (+0.0003), and the full-day window's 0.95051
# sits 0.00003 BELOW it, so this limb passes its coverage licence essentially at
# the boundary. The confirmation is real under the pre-registered rule and is
# the tightest of the three limbs on value; it is not a wide-margin result.
# Record: docs/PRECOMMIT-ercot169-margin-fuel-invariance-2026-08-05.md,
# results/calibration/ercot169_margin_fuel_invariance.json,
# results/calibration/FINDING-ercot169-margin-fuel-invariance-2026-08-05.md.
# Re-derives only with its source disclosure (rule 23), via
# ``scripts/data/derive_cc_committed_offer_margin.py`` (``--year`` runs the
# ercot-169 test). ISOs absent from the registry hard-fail when the flag is
# armed (rule 24 — never a silent fallback); ERCOT-identified from ERCOT
# conduct and never transferred (rule 25).
CC_COMMITTED_OFFER_LEVEL_BY_ISO: dict[str, float] = {
    "ERCOT": 10.354,
}

# Measured coal `_peak`-tranche offer LEVEL ($/MWh) and GAS slope (MMBtu/MWh)
# — the identification constants of the ``coal_peak_offer_margin`` mechanism
# (ERCOT-140, the coal offer-curve UPPER-TAIL successor ERCOT-123 §7.2
# chartered; ``docs/PRECOMMIT-ercot140-coal-peak-offer-2026-07-30.md``;
# applied in :func:`market_sim.data.fleet.legacy_bins.apply_coal_tranches`).
# The real coal fleet's top-decile boundary price: 60-Day SCED ``Submitted
# TPO-Price1`` capacity-weighted p90 of above-min-load capability, from the
# committed ERCOT-138 artifact
# ``results/calibration/ercot138_coal_gas_ranking.json`` (``E_bid_detail``
# COAL p90 rows: 34.82 / 34.82 / 43.00 / 48.01 across the four 2024–2025
# disclosure subsets, vs the model's 24.61–32.52 — the §5.6 finding).
#
# The slope basis is GAS, not coal: the measured top ROSE 34.82 → 45.43
# (res-hours-pooled) while delivered coal FELL 1.748 → 1.630 $/MMBtu (a
# coal-fuel form has slope −89.9 — wrong sign, refuted), and delivered gas
# rose 2.213 → 3.232, giving GAS_HR = 10.4100 MMBtu/MWh — within ~5 % of the
# fleet's own measured cap-weighted offer heat rate (10.905, ERCOT-138 §J):
# gas-parity opportunity pricing of the marginal coal MW.
#   level_i = p90_i − GAS_HR × (gas_i − anchor)
#   35.1989 / 35.1989 / 32.7711 / 37.7811 → 35.1989 res-hours-weighted.
# Identification quality: cross-subset dispersion ±18.74 % raw → ±7.12 %
# anchored. The ANCHOR is NOT a new constant: the mechanism reuses
# ``GAS_OFFER_MARGIN_ANCHOR_BY_ISO`` (ERCOT 2.2494 — rule 19, one gas
# identification point for the whole offer surface). At ``gas == anchor`` the
# resolved ``_peak`` bid equals this level exactly.
#
# 2023 application is a declared extrapolation, gated per-year in the ERCOT-140
# precommit §4.1; the ERCOT-138 §H same-plants 2025 flip is that precommit's
# declared identification risk (§2.2). Its ORIGINAL premise ("no 2023 SCED
# disclosure exists") was dissolved by the ercot-157 delivery-2023 corpus and
# TESTED at ercot-169 (matrix §5.1 item 13, Phase 0, no LP; pre-registered rule
# in docs/PRECOMMIT-ercot169-margin-fuel-invariance-2026-08-05.md).
# **The test could not be completed: NOT-IDENTIFIABLE-2023** — this limb shares
# the COAL class's licensing failure (curve_share 0.9702 vs the 0.9876 floor;
# the Martin Lake March-June no-curve block — see COAL_OFFER_MARGIN_LEVEL_BY_ISO
# above), so the verdict is withheld in both directions and the extrapolation
# note STANDS. Reported UNLICENSED for the record, not as a verdict, because the
# magnitude is the largest finding of that session: the delivery-2023 measured
# above-min-load p90 is **75.00 $/MWh** (flat at $75 in 9 of 12 months; the two
# most common submitted TOP steps in 2023 are $78.00 and $75.01, so it is
# widespread conduct and not one plant), i.e. level₂₀₂₃ = 71.3378 after removing
# the gas response (10.4100 × (2.6012 − 2.2494) = +3.6622) — **+36.14 above this
# constant, 14.4× the ±7.12 % (±$2.5062) band.** No coverage shortfall of
# 1.7 pp can produce a 2× level shift, and it corroborates at fleet scale the
# ercot-168 finding that 2023 coal offer conduct differs structurally from
# 2024/25 (Oak Grove's measured overnight top $60.26/$61.46). It is carried to
# the owner as an OPEN question on this constant's 2023 application — never a
# refutation, never a licence to arm (rule 13).
#
# **ercot-171 (2026-08-05) — the licensed-sub-population route CANNOT reach this
# limb, and the extrapolation note STANDS.** On the owner's in-session
# adjudication of the ERCOT-169 §6 open decision (option 2), the coverage
# shortfall was removed by a rule applied identically to every year (drop the
# COAL resources whose OWN curve_share falls below the same 0.9876 floor) and the
# instrument was gated on NEUTRALITY: the identical rule applied to the four
# 2024/25 identification subsets must still reproduce this constant within its
# own band. **G-LIC passes (2023 curve_share 0.97022 → 0.99969) but G-NEUT FAILS
# decisively** — the restricted 2024/25 pooled level is **54.3658** against this
# constant's 35.1989, **+19.17 = 7.6× the ±2.5062 band**, and the re-derived gas
# slope moves 10.4049 → 8.9503. The reason is structural and is the whole point
# of the gate: this limb's statistic is a **p90 of the top of the curve**, and
# dropping 18–28 % of the subsets' cap-weight moves a top-decile boundary
# violently, where the same rule is level-neutral on limb A's **median of the
# curve bottom** (−0.4258 = 0.46× band). The restriction is therefore a
# level-SELECTING filter here, not a coverage fix, so the 2023 reading under it is
# not comparable to this constant and **NOT-IDENTIFIABLE-2023 is CONFIRMED**.
# ERCOT-169 §6 option 1 holds by default: this note stands, **no candidate arm is
# named, and none may be built on this record** (rule 13). A different instrument
# — one that does not select on the tail — would need its own charter.
# Record: docs/PRECOMMIT-ercot171-coal-licensed-subpopulation-2026-08-05.md,
# results/calibration/ercot171_coal_licensed_subpop.json +
# FINDING-ercot171-coal-licensed-subpopulation-2026-08-05.md.
# Re-derives only with its source
# disclosure (rule 23), via ``scripts/data/derive_coal_peak_offer_margin.py``
# (``--year`` runs the ercot-169 test). ISOs absent from the registries
# hard-fail when the flag is armed (rule 24 — never a silent fallback);
# ERCOT-identified from ERCOT conduct and never transferred (rule 25).
COAL_PEAK_OFFER_LEVEL_BY_ISO: dict[str, float] = {
    "ERCOT": 35.1989,
}
COAL_PEAK_OFFER_GAS_HR_BY_ISO: dict[str, float] = {
    "ERCOT": 10.4100,
}

# PER-YEAR measured coal `_peak`-tranche offer LEVEL ($/MWh) — the year-keyed
# refinement of ``COAL_PEAK_OFFER_LEVEL_BY_ISO`` above (ercot-192, matrix §5.1
# item 13; owner signature **B1** on
# ``docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md`` card B,
# 2026-08-11: *"re-adjudicate under a fresh precommit before any arm"*).
# Consumed under ``coal_peak_offer_yearly_level`` (requires
# ``coal_peak_offer_margin``): for a solve year PRESENT here the `_peak` bid is
# ``level_year + GAS_HR × (gas_cc(t) − anchor)``; a solve year ABSENT (2024,
# 2025) falls through to the static constant **bit-identically**. The SLOPE and
# the SHARED anchor are untouched — one year cannot identify a slope, and the
# anchor is the whole gas offer surface's single identification point (rule 19
# [R-ONE-MECH]). Same shape as the ercot-168 per-year precedent
# (``COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO``), which likewise refines a level
# and leaves tranche ownership alone.
#
# **Why 2023 is keyed, and how the value was identified.** ERCOT-140 declared
# *"2023 application is a declared extrapolation (no 2023 SCED disclosure
# exists)"*; the ercot-157 delivery-2023 NP3-965 corpus re-upload dissolved that
# premise. The constant's OWN instrument (ERCOT-138 incremental-MW-weighted p90
# of above-min-load submitted steps, same row filters, same cap-weighting,
# CPT→CST at derivation) reads **p90 = 75.00 $/MWh** on the delivery-2023 COAL
# rows — flat at $75 in 9 of 12 months, and the corpus's two most common
# submitted TOP steps are $78.00 (21,677 intervals) and $75.01 (17,869), with
# the 2024/25 level $34.82 only a distant tenth. Removing this form's own gas
# response gives
#   level₂₀₂₃ = 75.00 − 10.4100 × (2.6012 − 2.2494) = 75.00 − 3.6622 = 71.3378
# i.e. **+36.1389 above the armed 35.1989 = 14.42× its ±7.12 % (±$2.5062)
# band** — the armed constant is roughly HALF the measured 2023 top. The point
# estimate is window-invariant (matched h11–22 CST and full-day both 71.3378).
#
# **The coverage objection is CLOSED BY BOUND, not by repair.** ercot-169 could
# not license this read (COAL ``curve_share`` 0.9702 vs the 0.9876 floor — the
# Martin Lake units 1–3 March–June no-curve block) and ercot-171 showed the
# licensed-sub-population route cannot reach this limb (dropping 26.1 % of
# HSL-cap moves a p90 of the curve TOP by +19.17 = 7.6× band; G-NEUT FAILED,
# NOT-IDENTIFIABLE-2023 CONFIRMED), closing with *"an instrument that does not
# select on the tail would need its own charter."* B1 chartered it, and it takes
# the route that needs no repair at all: the missing rows contribute ZERO weight
# to a weighted quantile, so give that weight the most extreme admissible price
# in each direction and recompute the SAME statistic —
#   append M at the bottom ⇒ q_low  = α + (α−1)·M/O
#   append M at the top    ⇒ q_high = α·(1 + M/O)
# The true α-quantile then lies in ``[Q(q_low), Q(q_high)]`` under **ANY
# imputation of the missing rows whatsoever**. Measured, with M the no-curve
# rows' full incremental range (the statistic's own denominator, hence maximal):
# the delivery-2023 interval is **[71.3378, 81.3678]** (matched window),
# **[71.3378, 71.3578]** (full day) and **[71.3378, 96.3378]** (raw-CPT clock) —
# the LOWER edge is 71.3378 in every window, so the 2023 level is **at least
# 14.42 band-widths above the armed constant no matter what the missing rows
# would have said**. Card B's *"a 1.7 pp coverage shortfall cannot produce a 2×
# level shift"* is thereby measured rather than asserted. Nothing is dropped,
# nothing imputed, no licensing quantity swapped, and the 0.9876 floor is NOT
# lowered. Two alternative repairs were REFUSED in the precommit BEFORE any
# level was read, on the Phase-0a structure measurement: own-conduct imputation
# (98.8 % of the missing headroom is ERCOT-123 bucket (b) price-taking at 98 %
# loading, so imputing a curve would invent an offer that was never submitted —
# rule 13 [R-MEASURED]) and re-expressing the licence on the exposure-matched
# ``a_offered`` (measured 0.94775 on 2023, i.e. WORSE than ``curve_share``; and
# a licensing quantity may never be chosen after seeing which one passes).
#
# **Neutrality gate (the ercot-171 lesson, applied to this instrument).** The
# identical bound construction on the four committed 2024/25 identification
# subsets: footing −0.0024 (limb A) / +2.6e-5 (this limb) against the armed
# values, and the LOWER edge — the edge that carries the 2023 verdict direction
# — displaces the pooled level by **0.065× / 0.000× band**. Reported, not buried:
# the OPPOSITE edge displaces by 2.635× band on those same licensed subsets,
# because a p90 of a steep curve top admits a large upward excursion from even
# 0.3–0.7 % missing weight. That is the bound being honest; it is the lower edge
# that this identification rests on.
#
# ZERO FITTED SCALARS (rule 23 [R-DOF]): the value is the constant's own
# statistic on the constant's own window with the constant's own fuel response
# removed — no residual is consulted anywhere in its derivation. Re-derives only
# with its source disclosure (rule 23), via
# ``scripts/data/derive_coal_peak_offer_margin.py`` and
# ``scripts/probes/ercot192_coal_limbs_bound_phase0.py``; ISOs absent from the
# registry fall through to the static constant, and an ARMED ISO with no year
# table is a hard error (rule 24 — never a silent fallback); ERCOT-identified
# from ERCOT conduct and never transferred (rule 25 [R-ISO-SCOPE]).
# Record: docs/PRECOMMIT-ercot192-coal-limbs-2023-reapplication-2026-08-12.md,
# results/calibration/ercot192_coal_limbs_bound.json,
# results/calibration/ercot192_coal_peak_structure.json,
# results/calibration/FINDING-ercot192-coal-limbs-2023-2026-08-12.md.
COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO: dict[str, dict[int, float]] = {
    "ERCOT": {2023: 71.3378},
}

# PER-PLANT measured coal offer supply curves — the identification artifact of
# the ``coal_perplant_offer_level`` mechanism (ERCOT-144, the DOF-retirement
# lane ERCOT-143 §2 chartered; applied in
# :func:`market_sim.data.fleet.legacy_bins.apply_coal_tranches`).
#
# Measured PER RESOURCE, every ERCOT coal plant submits a near-flat 60-Day
# SCED ``Submitted TPO`` curve at a plant-specific level — the fleet's smooth
# supply curve is CROSS-PLANT LEVEL DISPERSION, not within-plant slope
# (``docs/DIAGNOSIS-ercot143-lignite-offer-slope-2026-07-30.md`` §2). Each
# entry is the plant's MERGED price-sorted step supply curve of its resources'
# **modal** submitted TPO curves, pooled over the four on-disk 2024–2025
# disclosure subsets, as ``(cumulative_MW, price)`` breakpoints — verbatim
# disclosure conduct, zero fitted parameters
# (``scripts/data/derive_coal_perplant_offer.py``; provenance artifact
# ``data/raw/_processed-legacy/coal_perplant_offer_curves_ERCOT.json``).
# Jointly-owned plants (Fayette J01/J02, Sandy Creek J01–J04) merge genuinely
# different per-owner curves — Fayette's top ~36 % really is offered at
# $100–150 — so the merged curve is the plant's actual aggregate offer.
#
# Modal-curve time-stability is the identification license (Oak Grove's curve
# repeats identically x1436 across subsets AND years); the corpus FORBIDS any
# hourly/seasonal/diurnal identification (h0–h8 is 8.44 % of it — ERCOT-143
# §3), so the mechanism reads a LEVEL at the tranche (capacity) grain only.
# The 2023 application is a DECLARED EXTRAPOLATION (no 2023 SCED disclosure
# exists), exactly as ERCOT-137/139/140 declared theirs, gated LOYO per year.
# The curves are fuel-invariant BY MEASUREMENT: the mid-band levels did not
# co-move with delivered gas (+46 % 2024→2025) or coal within the corpus —
# the surface keeps its fuel response at the bottom (`_mustrun`, ERCOT-137
# coal-anchored) and top (`_peak`, ERCOT-140 gas-anchored) only.
#
# Points at/below ``COAL_PERPLANT_SELF_SCHED_FLOOR`` (San Miguel's 220 MW
# block at −$249) are KEPT verbatim but EXCLUDED from level statistics by the
# consumer: an offer at the ~−$250 floor is a price-taker self-schedule /
# commitment signal, not a marginal cost, and porting it into an LP energy
# bid would pin the block always-on (the ERCOT-144 handoff's pre-registered
# risk). Rule-23 frozen (re-derive only on new disclosure data); ISOs absent
# from the registry hard-fail when the flag is armed (rule 24); ERCOT-
# identified from ERCOT conduct and never transferred (rule 25).
COAL_PERPLANT_SELF_SCHED_FLOOR: float = -200.0
COAL_PERPLANT_OFFER_CURVE_BY_ISO: dict[
    str, dict[int, tuple[tuple[float, float], ...]]
] = {
    "ERCOT": {
        298: (
            (518, 15),
            (720, 16),
            (721, 18.63),
            (722, 18.65),
            (817, 18.73),
            (963, 19.02),
            (1025, 19.18),
            (1133, 19.47),
            (1197, 19.75),
            (1198, 22.71),
            (1425, 22.74),
            (1483, 22.76),
            (1537, 22.79),
            (1586, 22.82),
            (1633, 22.85),
            (1668, 22.87),
        ),  # Limestone
        3470: (
            (159, 9),
            (227, 10),
            (386, 13),
            (453, 14),
            (611, 16.9),
            (612, 17.64),
            (732, 17.74),
            (898, 18.36),
            (980, 18.59),
            (1032, 19.08),
            (1099, 19.43),
            (1145, 19.8),
            (1301, 20.01),
            (1358, 20.28),
            (1401, 20.52),
            (1519, 20.59),
            (1520, 21),
            (1572, 21.12),
            (1653, 21.18),
            (1692, 21.25),
            (1835, 21.46),
            (1900, 21.76),
            (1948, 21.91),
            (2033, 21.97),
            (2090, 22.35),
            (2133, 22.37),
            (2176, 22.81),
            (2216, 22.83),
            (2266, 22.93),
            (2302, 23.28),
            (2348, 23.52),
            (2381, 23.66),
            (2418, 23.84),
            (2461, 24.1),
            (2512, 24.76),
        ),  # W A Parish
        6146: (
            (194, 20.91),
            (303, 20.92),
            (408, 20.93),
            (510, 20.94),
            (613, 20.95),
            (718, 20.96),
            (835, 20.97),
            (1181, 22.2),
            (1404, 22.21),
            (1619, 22.22),
            (1828, 22.23),
            (2037, 22.24),
            (2251, 22.25),
            (2485, 22.26),
        ),  # Martin Lake
        6178: (
            (220, 17.32),
            (299, 17.33),
            (371, 17.34),
            (442, 17.91),
            (512, 18.49),
            (585, 19.04),
            (655, 19.69),
        ),  # Coleto Creek
        6179: (
            (180, 13.83),
            (258, 14.07),
            (283, 14.2),
            (304, 14.27),
            (325, 14.48),
            (403, 14.55),
            (428, 14.57),
            (449, 14.68),
            (471, 14.84),
            (492, 14.88),
            (517, 14.94),
            (538, 15.09),
            (560, 15.12),
            (581, 15.29),
            (606, 15.3),
            (628, 15.41),
            (649, 15.49),
            (674, 15.67),
            (696, 15.69),
            (717, 15.7),
            (739, 15.98),
            (764, 16.04),
            (819, 16.13),
            (841, 16.26),
            (866, 16.41),
            (888, 16.55),
            (913, 16.78),
            (935, 16.83),
            (982, 17.39),
            (1042, 17.52),
            (1120, 98.86),
            (1198, 100.42),
            (1225, 100.85),
            (1250, 102.69),
            (1277, 102.94),
            (1302, 104.53),
            (1327, 105.28),
            (1352, 106.38),
            (1377, 107.61),
            (1402, 108.22),
            (1427, 109.95),
            (1452, 110.07),
            (1457.9, 110.5),
            (1482.9, 112.28),
            (1507.9, 114.61),
            (1516.8, 115.45),
            (1517, 150),
            (1634, 150.1),
        ),  # Fayette
        6180: (
            (317, 8.37),
            (408, 8.42),
            (493, 8.58),
            (575, 8.77),
            (658, 8.96),
            (743, 9.14),
            (1060, 9.32),
            (1151, 9.33),
            (1288, 9.35),
            (1373, 9.36),
            (1455, 9.43),
            (1538, 9.5),
            (1623, 9.57),
            (1760, 9.64),
        ),  # Oak Grove
        6183: ((220, -249), (221, 42), (396, 43)),  # San Miguel
        7030: ((160, 14.73), (310, 14.74)),  # Major Oak
        7097: (
            (290, 15.72),
            (300, 15.83),
            (425, 16.37),
            (435, 16.46),
            (515, 16.61),
            (555, 16.81),
            (595, 16.99),
            (625, 17.08),
            (645, 17.16),
            (665, 17.34),
            (735, 17.69),
            (765, 17.95),
            (895, 18.41),
            (915, 18.56),
            (985, 18.57),
            (1015, 18.83),
            (1205, 19.82),
            (1365, 20.24),
        ),  # JK Spruce
        56611: (
            (41, 21.53),
            (47, 21.68),
            (53, 21.83),
            (59, 21.98),
            (65, 22.13),
            (71, 22.28),
            (77, 22.43),
            (83, 22.58),
            (89, 22.73),
            (106, 23.1),
            (196, 27.55),
            (196.1, 27.56),
            (408.3, 29.36),
            (535.9, 31.14),
            (669.9, 32.92),
            (791.9, 34.82),
            (935, 65),
        ),  # Sandy Creek
    },
}

# PER-YEAR windowed per-plant coal offer curves (ercot-168, matrix §5.1 item
# 12 — the rule-23 re-derivation of the registry above from the delivery-2023
# NP3-965 corpus, whose ercot-157 landing dissolved the "no 2023 SCED exists"
# extrapolation premise recorded in the ercot-144 DOF ledger). Consumed under
# ``coal_perplant_offer_yearly`` (requires ``coal_perplant_offer_level``):
# for a solve year PRESENT here, committed/econ tranches of listed plants are
# priced per (months × hours) window on the window's own merged measured
# curve — the SAME window mapping as the static registry, evaluated per cell;
# `_mustrun`/`_peak` keep their ERCOT-137/ERCOT-140 owners, and a solve year
# ABSENT here (2024, 2025) falls through to the static registry unchanged.
#
# Construction (zero fitted scalars; derive
# ``scripts/data/derive_coal_perplant_offer.py --year 2023``; provenance
# ``data/raw/_processed-legacy/coal_perplant_offer_curves_2023_ERCOT.json``):
# the effective curve of (resource, month, hour) is the hour's modal
# price-tuple curve iff that key repeats on a strict majority (>0.5) of the
# month's live days at that hour, else the month's pooled modal curve — the
# ercot-144 modal/time-stability license applied at the corpus's own hourly
# submission grain (full-year 24 h coverage; the ERCOT-143 §3 "no diurnal
# identification" refusal was coverage-scoped to the 2024/25 probe-day
# corpus). Hours are FIXED CST (converted from the disclosure's prevailing
# clock at derivation — the ercot-166 DST-defect class, closed at source).
# Headline content: Oak Grove's Aug–Oct overnight (h23–h8) repricing to a
# $60.26/$61.46 top at its LSL step — the measured executor of the 2023
# coal-fleet two-shift (FINDING-ercot166 §4) — plus month-grain level moves
# (Martin Lake +$1.9 from Aug, San Miguel May step, Major Oak Jun/Dec steps)
# the 2024/25 extrapolation could not see. Fuel decomposition (precommit
# §1f): no measured fuel series moves at any offer step — conduct, not
# commodity; no commodity backing is claimed (owner adjudication 2026-08-05).
# Rule-23 frozen; rule-25 ERCOT-only; window entries are (months, hours,
# curve) with exhaustive non-overlapping (month × hour) coverage, validated
# at resolution time.
# Machine-emitted block (derive_coal_perplant_offer.py --year): one window per
# line, trailing commas load-bearing for 1-tuples; keep the emitter's bytes so
# a re-derive diffs cleanly against the provenance JSON.
# fmt: off
COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO: dict[
    str,
    dict[
        int,
        dict[
            int,
            tuple[
                tuple[
                    tuple[int, ...], tuple[int, ...], tuple[tuple[float, float], ...]
                ],
                ...,
            ],
        ],
    ],
] = {
    "ERCOT": {
        2023: {
            298: (  # Limestone
                ((1,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((260, 12.22), (360, 12.24), (618, 17.47), (720, 17.5), (721, 22.34), (722, 22.36), (817, 22.46), (963, 22.81), (1025, 23), (1133, 23.35), (1197, 23.69), (1198, 24.47), (1425, 24.49), (1483, 24.5), (1537, 24.52), (1586, 24.53), (1633, 24.55), (1667, 24.57),)),
                ((2,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((260, 12.22), (360, 12.24), (618, 17.38), (720, 17.41), (721, 21.79), (722, 21.82), (817, 21.91), (963, 22.25), (1025, 22.44), (1133, 22.78), (1197, 23.12), (1198, 23.92), (1425, 23.95), (1483, 23.97), (1537, 24), (1586, 24.03), (1633, 24.06), (1667, 24.08),)),
                ((3,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((260, 19.53), (360, 19.58), (361, 23.63), (588, 23.68), (646, 23.72), (700, 23.77), (758, 23.82), (793, 78),)),
                ((4,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((258, 18.03), (360, 18.05), (620, 19.83), (720, 19.88), (721, 21.57), (722, 21.6), (817, 21.69), (963, 22.02), (1198, 22.21), (1199, 23.77), (1426, 23.82), (1484, 23.87), (1538, 23.93), (1613, 23.98), (1650, 78),)),
                ((5,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((258, 17.67), (360, 17.7), (620, 19.03), (720, 19.08), (721, 21.26), (722, 21.28), (817, 21.38), (963, 21.7), (1025, 21.89), (1133, 22.22), (1197, 22.55), (1198, 23.44), (1425, 23.5), (1483, 23.55), (1537, 23.61), (1586, 23.66), (1633, 23.72), (1667, 23.77),)),
                ((6,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((258, 17.04), (360, 17.06), (620, 19.19), (720, 19.26), (721, 21.09), (722, 21.11), (817, 21.21), (963, 21.53), (1025, 21.72), (1133, 22.04), (1197, 22.37), (1198, 23.34), (1425, 23.42), (1483, 23.49), (1537, 23.57), (1586, 23.64), (1633, 23.72), (1667, 23.79),)),
                ((7,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((258, 16.59), (360, 16.62), (620, 18.79), (720, 18.89), (721, 21.06), (722, 21.09), (817, 21.18), (963, 21.5), (1025, 21.69), (1133, 22.01), (1197, 22.34), (1198, 23.41), (1425, 23.51), (1483, 23.61), (1537, 23.71), (1586, 23.81), (1633, 23.91), (1667, 24.01),)),
                ((8,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((258, 16.7), (360, 16.72), (620, 18.9), (720, 19.01), (721, 20.95), (722, 20.97), (817, 21.06), (963, 21.39), (1025, 21.57), (1133, 21.89), (1197, 22.22), (1198, 23.32), (1425, 23.43), (1483, 23.53), (1537, 23.65), (1586, 23.75), (1633, 23.86), (1667, 23.97),)),
                ((9,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((258, 16.53), (360, 16.56), (620, 18.69), (720, 18.77), (721, 20.97), (722, 21), (817, 21.09), (963, 21.41), (1025, 21.6), (1133, 21.92), (1197, 22.25), (1198, 23.25), (1425, 23.33), (1483, 23.42), (1537, 23.5), (1586, 23.58), (1633, 23.67), (1667, 23.75),)),
                ((10,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((258, 17.71), (360, 17.73), (620, 19.65), (720, 19.69), (721, 21.21), (722, 21.23), (817, 21.32), (963, 21.65), (1025, 21.84), (1133, 22.16), (1197, 22.49), (1198, 23.35), (1425, 23.4), (1483, 23.45), (1537, 23.5), (1586, 23.54), (1633, 23.59), (1667, 23.64),)),
                ((11,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((258, 17.16), (360, 17.19), (620, 19.23), (720, 19.25), (721, 21.5), (722, 21.52), (817, 21.62), (963, 21.95), (1025, 22.14), (1133, 22.47), (1197, 22.8), (1198, 23.55), (1425, 23.57), (1483, 23.59), (1537, 23.6), (1570, 23.62), (1580, 78),)),
                ((12,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((258, 18.21), (360, 18.23), (620, 20.27), (720, 20.29), (721, 21.44), (722, 21.46), (817, 21.56), (963, 21.89), (1025, 22.08), (1133, 22.41), (1197, 22.74), (1198, 23.49), (1425, 23.51), (1483, 23.53), (1537, 23.55), (1586, 23.57), (1633, 23.59), (1667, 23.61),)),
            ),
            3470: (  # W A Parish
                ((1,), (0, 1, 2, 3, 4,), ((159, 9.65), (226, 10.19), (384, 21.68), (540, 22.31), (660, 22.58), (661, 22.71), (779, 22.96), (922, 23.26), (1004, 23.48), (1085, 23.61), (1133, 23.81), (1198, 24.26), (1241, 24.36), (1308, 24.38), (1348, 24.9), (1405, 24.91), (1462, 25.27), (1498, 25.45), (1548, 25.56), (1585, 26.09), (1637, 26.17), (1683, 26.21), (1726, 26.87), (1773, 27.07), (1824, 27.61), (1867, 27.97), (1900, 28.87),)),
                ((1,), (5, 6,), ((159, 9.65), (226, 10.19), (384, 21.68), (540, 22.31), (610, 22.58), (611, 22.71), (729, 22.96), (872, 23.26), (942, 23.48), (1023, 23.61), (1071, 23.81), (1136, 24.26), (1179, 24.36), (1249, 24.38), (1289, 24.9), (1346, 24.91), (1416, 25.27), (1452, 25.45), (1502, 25.56), (1539, 26.09), (1609, 26.17), (1655, 26.21), (1698, 26.87), (1701, 27.07), (1752, 27.61), (1798, 78),)),
                ((1,), (7, 8, 9, 10, 11, 12, 13, 14, 15,), ((159, 9.65), (226, 10.19), (384, 21.68), (540, 22.31), (660, 22.58), (661, 22.71), (779, 22.96), (922, 23.26), (1004, 23.48), (1085, 23.61), (1133, 23.81), (1198, 24.26), (1241, 24.36), (1308, 24.38), (1348, 24.9), (1405, 24.91), (1462, 25.27), (1498, 25.45), (1548, 25.56), (1585, 26.09), (1637, 26.17), (1683, 26.21), (1726, 26.87), (1773, 27.07), (1824, 27.61), (1867, 27.97), (1900, 28.87),)),
                ((1,), (16,), ((159, 9.65), (226, 10.19), (384, 21.68), (540, 22.31), (610, 22.58), (611, 22.71), (729, 22.96), (872, 23.26), (942, 23.48), (1023, 23.61), (1071, 23.81), (1136, 24.26), (1179, 24.36), (1249, 24.38), (1289, 24.9), (1346, 24.91), (1416, 25.27), (1452, 25.45), (1502, 25.56), (1539, 26.09), (1609, 26.17), (1655, 26.21), (1698, 26.87), (1701, 27.07), (1752, 27.61), (1798, 78),)),
                ((1,), (17, 18, 19, 20, 21, 22, 23,), ((159, 9.65), (226, 10.19), (384, 21.68), (540, 22.31), (660, 22.58), (661, 22.71), (779, 22.96), (922, 23.26), (1004, 23.48), (1085, 23.61), (1133, 23.81), (1198, 24.26), (1241, 24.36), (1308, 24.38), (1348, 24.9), (1405, 24.91), (1462, 25.27), (1498, 25.45), (1548, 25.56), (1585, 26.09), (1637, 26.17), (1683, 26.21), (1726, 26.87), (1773, 27.07), (1824, 27.61), (1867, 27.97), (1900, 28.87),)),
                ((2,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((159, 12.67), (226, 13.21), (384, 21.1), (540, 21.71), (660, 21.98), (661, 22.09), (779, 22.35), (922, 22.63), (1004, 22.86), (1085, 22.98), (1133, 23.17), (1198, 23.62), (1241, 23.71), (1308, 23.73), (1405, 24.25), (1462, 24.6), (1498, 24.79), (1548, 24.89), (1585, 25.42), (1637, 25.48), (1683, 25.52), (1726, 26.15), (1773, 26.35), (1824, 26.87), (1867, 27.23), (1900, 28.11),)),
                ((3,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((159, 15), (226, 15.1), (384, 20.46), (540, 21.08), (660, 21.39), (779, 21.76), (922, 22.29), (1004, 22.31), (1085, 22.44), (1133, 22.82), (1198, 23.12), (1265, 23.23), (1308, 23.35), (1365, 23.8), (1405, 23.88), (1462, 24.15), (1498, 24.4), (1548, 24.48), (1585, 25.02), (1637, 25.07), (1683, 25.16), (1726, 25.84), (1773, 25.99), (1824, 26.62), (1867, 26.91), (1900, 27.84),)),
                ((4,), (0, 1, 2, 3, 4,), ((159, 15), (226, 15.1), (384, 20.3), (540, 20.93), (660, 21.27), (778, 21.66), (779, 21.94), (861, 22.25), (942, 22.39), (1085, 22.45), (1133, 22.97), (1198, 23.12), (1265, 23.23), (1308, 23.49), (1365, 23.85), (1405, 24.01), (1462, 24.2), (1498, 24.53), (1548, 24.58), (1585, 25.14), (1637, 25.18), (1683, 25.31), (1726, 26.04), (1773, 26.16), (1824, 26.87), (1867, 27.13), (1900, 28.11),)),
                ((4,), (5,), ((159, 15), (226, 15.1), (384, 20.3), (540, 20.93), (614, 21.27), (732, 21.66), (733, 21.94), (807, 22.25), (888, 22.39), (1031, 22.45), (1079, 22.97), (1144, 23.12), (1218, 23.23), (1261, 23.49), (1318, 23.85), (1358, 24.01), (1432, 24.2), (1468, 24.53), (1518, 24.58), (1555, 25.14), (1629, 25.18), (1675, 25.31), (1718, 26.04), (1723, 26.16), (1774, 26.87), (1851, 78),)),
                ((4,), (6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((159, 15), (226, 15.1), (384, 20.3), (540, 20.93), (660, 21.27), (778, 21.66), (779, 21.94), (861, 22.25), (942, 22.39), (1085, 22.45), (1133, 22.97), (1198, 23.12), (1265, 23.23), (1308, 23.49), (1365, 23.85), (1405, 24.01), (1462, 24.2), (1498, 24.53), (1548, 24.58), (1585, 25.14), (1637, 25.18), (1683, 25.31), (1726, 26.04), (1773, 26.16), (1824, 26.87), (1867, 27.13), (1900, 28.11),)),
                ((5,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((159, 15), (226, 15.1), (384, 19.7), (540, 20.36), (660, 20.72), (778, 21.13), (860, 21.74), (861, 21.79), (942, 21.9), (1085, 22.27), (1150, 22.67), (1198, 22.76), (1265, 22.77), (1308, 23.25), (1365, 23.45), (1405, 23.74), (1462, 23.79), (1512, 24.22), (1548, 24.23), (1600, 24.81), (1637, 24.82), (1683, 24.99), (1726, 25.76), (1773, 25.83), (1824, 26.62), (1867, 26.86), (1900, 27.88),)),
                ((6,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((159, 15), (226, 15.1), (384, 19.48), (540, 20.14), (660, 20.5), (778, 20.92), (860, 21.53), (941, 21.69), (942, 21.8), (1085, 22.28), (1150, 22.47), (1217, 22.56), (1265, 22.75), (1308, 23.22), (1365, 23.24), (1422, 23.58), (1462, 23.7), (1512, 24.02), (1548, 24.17), (1600, 24.61), (1637, 24.75), (1683, 24.8), (1726, 25.57), (1773, 25.63), (1824, 26.44), (1867, 26.66), (1900, 27.68),)),
                ((7,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((159, 15), (226, 15.1), (384, 19.11), (542, 19.38), (645, 19.96), (801, 20.05), (921, 20.43), (994, 20.81), (1112, 20.84), (1194, 21.46), (1275, 21.63), (1335, 21.66), (1336, 21.79), (1479, 22.26), (1544, 22.42), (1663, 22.51), (1711, 22.73), (1811, 23.21), (1857, 23.36), (1914, 23.54), (1954, 23.68), (2004, 24), (2040, 24.15), (2083, 24.21), (2135, 24.59), (2172, 24.73), (2218, 24.79), (2257, 25.06), (2300, 25.58), (2347, 25.63), (2385, 25.9), (2436, 26.47), (2479, 26.67), (2512, 27.71),)),
                ((8,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((159, 4.68), (226, 5.15), (384, 19.26), (709, 19.84), (865, 19.93), (985, 20.3), (1020, 20.69), (1138, 20.71), (1220, 21.33), (1301, 21.5), (1371, 21.53), (1372, 21.66), (1515, 22.13), (1580, 22.28), (1647, 22.37), (1682, 22.38), (1730, 22.6), (1830, 23.07), (1865, 23.23), (1922, 23.4), (1962, 23.54), (2012, 23.85), (2048, 24.01), (2118, 24.08), (2170, 24.43), (2207, 24.58), (2253, 24.64), (2296, 25.42), (2343, 25.47), (2385, 25.77), (2436, 26.3), (2479, 26.5), (2512, 27.54),)),
                ((9,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((159, -22.78), (227, -21.99), (386, 4.68), (453, 5.15), (611, 19.38), (767, 20.03), (887, 20.39), (888, 20.4), (1006, 20.8), (1172, 21.24), (1254, 21.41), (1255, 21.45), (1336, 21.57), (1479, 21.93), (1531, 22.08), (1596, 22.33), (1644, 22.41), (1711, 22.42), (1754, 22.9), (1800, 22.92), (1857, 23.1), (1897, 23.38), (1954, 23.43), (1997, 23.76), (2083, 23.86), (2172, 24.45), (2211, 24.6), (2257, 24.63), (2300, 25.4), (2338, 25.44), (2385, 25.46), (2436, 26.25), (2479, 26.47), (2512, 27.49),)),
                ((10,), (0, 1, 2, 3, 4, 5, 6, 7,), ((159, -22.78), (227, -21.99), (386, 4.68), (453, 5.15), (611, 19.81), (767, 20.45), (768, 20.67), (888, 20.8), (1006, 21.19), (1172, 21.52), (1173, 21.58), (1255, 21.79), (1336, 21.94), (1479, 22.09), (1531, 22.36), (1579, 22.6), (1644, 22.69), (1711, 22.78), (1754, 23.11), (1800, 23.21), (1857, 23.43), (1897, 23.61), (1954, 23.77), (1997, 24.06), (2033, 24.12), (2083, 24.17), (2120, 24.72), (2172, 24.77), (2211, 24.91), (2257, 24.92), (2300, 25.66), (2338, 25.75), (2385, 25.76), (2436, 26.52), (2479, 26.75), (2512, 27.74),)),
                ((10,), (8,), ((159, -22.78), (227, -21.99), (386, 4.68), (453, 5.15), (611, 19.81), (767, 20.45), (768, 20.67), (839, 20.8), (957, 21.19), (1123, 21.52), (1124, 21.58), (1195, 21.79), (1276, 21.94), (1419, 22.09), (1471, 22.36), (1519, 22.6), (1584, 22.69), (1655, 22.78), (1698, 23.11), (1744, 23.21), (1801, 23.43), (1826, 23.61), (1897, 23.77), (1940, 24.06), (1990, 24.17), (2061, 24.77), (2100, 24.91), (2146, 24.92), (2189, 25.66), (2227, 25.75), (2232, 25.76), (2283, 26.52), (2458, 78),)),
                ((10,), (9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((159, -22.78), (227, -21.99), (386, 4.68), (453, 5.15), (611, 19.81), (767, 20.45), (768, 20.67), (888, 20.8), (1006, 21.19), (1172, 21.52), (1173, 21.58), (1255, 21.79), (1336, 21.94), (1479, 22.09), (1531, 22.36), (1579, 22.6), (1644, 22.69), (1711, 22.78), (1754, 23.11), (1800, 23.21), (1857, 23.43), (1897, 23.61), (1954, 23.77), (1997, 24.06), (2033, 24.12), (2083, 24.17), (2120, 24.72), (2172, 24.77), (2211, 24.91), (2257, 24.92), (2300, 25.66), (2338, 25.75), (2385, 25.76), (2436, 26.52), (2479, 26.75), (2512, 27.74),)),
                ((11,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((159, -22.78), (227, -21.99), (386, 4.68), (453, 5.15), (611, 20.32), (767, 20.95), (768, 20.98), (888, 21.28), (1006, 21.67), (1007, 21.8), (1173, 21.84), (1255, 22.24), (1398, 22.33), (1479, 22.38), (1531, 22.69), (1579, 22.86), (1644, 23.1), (1711, 23.21), (1754, 23.39), (1800, 23.55), (1857, 23.81), (1897, 23.93), (1954, 24.17), (1997, 24.4), (2033, 24.46), (2083, 24.53), (2120, 25.08), (2172, 25.13), (2218, 25.25), (2257, 25.26), (2300, 25.96), (2347, 26.09), (2385, 26.11), (2436, 26.79), (2479, 27.05), (2512, 28.01),)),
                ((12,), (0, 1, 2,), ((159, -22.78), (227, -21.99), (386, 7), (453, 8), (611, 20.67), (612, 20.97), (768, 21.28), (888, 21.56), (889, 21.74), (1055, 21.81), (1173, 21.92), (1316, 22.27), (1398, 22.43), (1479, 22.56), (1531, 22.66), (1579, 22.8), (1644, 23.2), (1711, 23.31), (1754, 23.33), (1800, 23.5), (1857, 23.84), (1897, 23.85), (1954, 24.19), (1997, 24.34), (2033, 24.38), (2083, 24.48), (2120, 25.01), (2172, 25.07), (2218, 25.12), (2257, 25.18), (2300, 25.76), (2347, 25.95), (2385, 26.03), (2436, 26.49), (2479, 26.83), (2512, 27.7),)),
                ((12,), (3, 4, 5, 6, 7, 8,), ((159, -22.78), (227, -21.99), (386, 7), (453, 8), (611, 20.67), (612, 20.97), (768, 21.28), (888, 21.56), (889, 21.74), (1055, 21.81), (1173, 21.92), (1316, 22.27), (1398, 22.43), (1479, 22.56), (1531, 22.66), (1579, 22.8), (1644, 23.2), (1711, 23.31), (1754, 23.33), (1800, 23.5), (1857, 23.84), (1897, 23.85), (1954, 24.19), (1997, 24.34), (2033, 24.38), (2083, 24.48), (2120, 25.01), (2172, 25.07), (2218, 25.12), (2257, 25.18), (2300, 25.76), (2395, 25.95), (2433, 26.03), (2484, 26.49), (2508, 78),)),
                ((12,), (9, 10, 11,), ((159, -22.78), (227, -21.99), (386, 7), (453, 8), (611, 20.67), (612, 20.97), (768, 21.28), (888, 21.56), (889, 21.74), (1055, 21.81), (1173, 21.92), (1316, 22.27), (1398, 22.43), (1479, 22.56), (1531, 22.66), (1579, 22.8), (1644, 23.2), (1711, 23.31), (1754, 23.33), (1800, 23.5), (1857, 23.84), (1897, 23.85), (1954, 24.19), (1997, 24.34), (2033, 24.38), (2083, 24.48), (2120, 25.01), (2172, 25.07), (2228, 25.12), (2267, 25.18), (2362, 25.95), (2400, 26.03), (2498, 78),)),
                ((12,), (12,), ((159, -22.78), (227, -21.99), (386, 7), (453, 8), (611, 20.67), (612, 20.97), (768, 21.28), (888, 21.56), (889, 21.74), (1055, 21.81), (1173, 21.92), (1316, 22.27), (1398, 22.43), (1479, 22.56), (1531, 22.66), (1579, 22.8), (1644, 23.2), (1711, 23.31), (1754, 23.33), (1800, 23.5), (1857, 23.84), (1897, 23.85), (1954, 24.19), (1997, 24.34), (2033, 24.38), (2083, 24.48), (2120, 25.01), (2172, 25.07), (2218, 25.12), (2257, 25.18), (2300, 25.76), (2395, 25.95), (2433, 26.03), (2484, 26.49), (2508, 78),)),
                ((12,), (13, 14, 15, 16,), ((159, -22.78), (227, -21.99), (386, 7), (453, 8), (611, 20.67), (612, 20.97), (768, 21.28), (888, 21.56), (889, 21.74), (1055, 21.81), (1173, 21.92), (1316, 22.27), (1398, 22.43), (1479, 22.56), (1531, 22.66), (1579, 22.8), (1644, 23.2), (1711, 23.31), (1754, 23.33), (1800, 23.5), (1857, 23.84), (1897, 23.85), (1954, 24.19), (1997, 24.34), (2033, 24.38), (2083, 24.48), (2120, 25.01), (2172, 25.07), (2228, 25.12), (2267, 25.18), (2362, 25.95), (2400, 26.03), (2498, 78),)),
                ((12,), (17,), ((159, -22.78), (227, -21.99), (386, 7), (453, 8), (611, 20.67), (612, 20.97), (768, 21.28), (888, 21.56), (889, 21.74), (1055, 21.81), (1173, 21.92), (1316, 22.27), (1398, 22.43), (1479, 22.56), (1531, 22.66), (1579, 22.8), (1644, 23.2), (1711, 23.31), (1754, 23.33), (1800, 23.5), (1857, 23.84), (1897, 23.85), (1954, 24.19), (1997, 24.34), (2033, 24.38), (2083, 24.48), (2120, 25.01), (2172, 25.07), (2218, 25.12), (2257, 25.18), (2300, 25.76), (2395, 25.95), (2433, 26.03), (2484, 26.49), (2508, 78),)),
                ((12,), (18,), ((159, -22.78), (227, -21.99), (386, 7), (453, 8), (611, 20.67), (612, 20.97), (768, 21.28), (888, 21.56), (889, 21.74), (1055, 21.81), (1173, 21.92), (1316, 22.27), (1398, 22.43), (1479, 22.56), (1531, 22.66), (1579, 22.8), (1644, 23.2), (1711, 23.31), (1754, 23.33), (1800, 23.5), (1857, 23.84), (1897, 23.85), (1954, 24.19), (1997, 24.34), (2033, 24.38), (2083, 24.48), (2120, 25.01), (2172, 25.07), (2218, 25.12), (2257, 25.18), (2300, 25.76), (2347, 25.95), (2385, 26.03), (2436, 26.49), (2479, 26.83), (2512, 27.7),)),
                ((12,), (19, 20, 21, 22,), ((159, -22.78), (227, -21.99), (386, 7), (453, 8), (611, 20.67), (612, 20.97), (768, 21.28), (888, 21.56), (889, 21.74), (1055, 21.81), (1173, 21.92), (1316, 22.27), (1398, 22.43), (1479, 22.56), (1531, 22.66), (1579, 22.8), (1644, 23.2), (1711, 23.31), (1754, 23.33), (1800, 23.5), (1857, 23.84), (1897, 23.85), (1954, 24.19), (1997, 24.34), (2033, 24.38), (2083, 24.48), (2120, 25.01), (2172, 25.07), (2218, 25.12), (2257, 25.18), (2300, 25.76), (2395, 25.95), (2433, 26.03), (2484, 26.49), (2508, 78),)),
                ((12,), (23,), ((159, -22.78), (227, -21.99), (386, 7), (453, 8), (611, 20.67), (612, 20.97), (768, 21.28), (888, 21.56), (889, 21.74), (1055, 21.81), (1173, 21.92), (1316, 22.27), (1398, 22.43), (1479, 22.56), (1531, 22.66), (1579, 22.8), (1644, 23.2), (1711, 23.31), (1754, 23.33), (1800, 23.5), (1857, 23.84), (1897, 23.85), (1954, 24.19), (1997, 24.34), (2033, 24.38), (2083, 24.48), (2120, 25.01), (2172, 25.07), (2218, 25.12), (2257, 25.18), (2300, 25.76), (2347, 25.95), (2385, 26.03), (2436, 26.49), (2479, 26.83), (2512, 27.7),)),
            ),
            6146: (  # Martin Lake
                ((1,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((194, 26.05), (343, 26.06), (767, 26.07), (965, 27.16), (1112, 27.17), (1536, 27.18), (1736, 28.28), (1884, 28.29), (2310, 28.3), (2317, 29.83), (2360, 30.09), (2363, 30.11), (2378, 30.12), (2384, 30.31), (2421, 30.58), (2424, 30.61), (2434, 30.62), (2440, 31.42), (2477, 31.58), (2480, 31.6), (2485, 31.61),)),
                ((2,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((194, 20.89), (343, 20.9), (767, 20.91), (965, 21.4), (1112, 21.41), (1536, 21.42), (1736, 22.36), (1884, 22.37), (2310, 22.38), (2316, 24.71), (2323, 24.73), (2403, 24.94), (2409, 24.96), (2434, 24.97), (2440, 25.65), (2477, 25.78), (2480, 25.8), (2485, 25.81),)),
                ((3, 4, 5,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((194, 18.56), (303, 18.8), (408, 18.93), (510, 19.01), (708, 19.05), (811, 19.06), (916, 19.1), (1033, 19.13), (1141, 19.19), (1244, 19.34), (1345, 19.43), (1446, 19.5), (1549, 19.55), (1660, 19.58), (1860, 19.97), (1968, 20.16), (2073, 20.28), (2174, 20.35), (2275, 20.39), (2379, 20.43), (2485, 20.46),)),
                ((6, 7,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((194, 18.56), (303, 18.8), (408, 18.93), (510, 19.01), (708, 19.02), (811, 19.06), (916, 19.1), (1141, 19.13), (1244, 19.3), (1345, 19.39), (1446, 19.46), (1549, 19.51), (1660, 19.55), (1860, 19.89), (1968, 20.07), (2073, 20.19), (2174, 20.26), (2275, 20.31), (2379, 20.35), (2485, 20.38),)),
                ((8, 9,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((194, 20.89), (303, 20.9), (408, 20.91), (510, 20.92), (613, 20.93), (718, 20.94), (835, 20.95), (1033, 21.35), (1141, 21.36), (1244, 21.37), (1345, 21.38), (1446, 21.39), (1549, 21.4), (1660, 21.41), (1860, 22.23), (1968, 22.24), (2073, 22.25), (2174, 22.26), (2275, 22.27), (2379, 22.28), (2485, 22.29),)),
                ((10, 11,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((194, 20.89), (303, 20.9), (408, 20.91), (510, 20.92), (613, 20.93), (718, 20.94), (835, 20.95), (1033, 21.38), (1141, 21.39), (1244, 21.4), (1345, 21.41), (1446, 21.42), (1549, 21.43), (1660, 21.44), (1860, 22.29), (1968, 22.3), (2073, 22.31), (2174, 22.32), (2275, 22.33), (2379, 22.34), (2485, 22.35),)),
                ((12,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((194, 20.89), (303, 20.9), (408, 20.91), (510, 20.92), (613, 20.93), (718, 20.94), (835, 20.95), (1033, 21.4), (1141, 21.41), (1244, 21.42), (1345, 21.43), (1446, 21.44), (1549, 21.45), (1660, 21.46), (1860, 22.36), (1968, 22.37), (2073, 22.38), (2174, 22.39), (2275, 22.4), (2379, 22.41), (2485, 22.42),)),
            ),
            6178: (  # Coleto Creek
                ((1,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((220, 22.99), (299, 23), (371, 23.01), (442, 23.86), (512, 24.72), (585, 25.54), (655, 26.5),)),
                ((2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((220, 18.73), (299, 18.74), (371, 18.75), (442, 19.36), (512, 19.99), (585, 20.59), (655, 21.29),)),
            ),
            6179: (  # Fayette
                ((1,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((180, 15.96), (258, 16.2), (336, 16.33), (361, 16.4), (383, 16.51), (404, 16.58), (447, 16.83), (472, 16.84), (493, 17.07), (515, 17.15), (540, 17.29), (561, 17.32), (583, 17.47), (604, 17.57), (629, 17.73), (651, 17.79), (672, 17.81), (693, 18.06), (715, 18.11), (740, 18.17), (761, 18.3), (783, 18.43), (808, 18.62), (830, 18.74), (885, 18.87), (910, 19.06), (957, 19.37), (982, 19.5), (1042, 20.38), (1120, 99.61), (1198, 101.28), (1225, 101.62), (1250, 103.48), (1277, 103.82), (1302, 105.33), (1327, 106.17), (1352, 107.19), (1377, 108.53), (1402, 109.05), (1427, 110.88), (1452, 110.91), (1477, 112.77), (1502, 113.24), (1527, 114.63), (1552, 115.59), (1569, 115.89), (1594, 117.94), (1619, 120.3), (1637, 121.99),)),
                ((2,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((180, 15.85), (258, 16.13), (336, 16.26), (361, 16.29), (383, 16.44), (405, 16.52), (430, 16.73), (452, 16.76), (474, 16.78), (496, 17.03), (518, 17.08), (543, 17.17), (565, 17.29), (587, 17.39), (609, 17.55), (634, 17.61), (656, 17.71), (678, 17.8), (700, 18.03), (725, 18.05), (747, 18.06), (769, 18.32), (791, 18.35), (816, 18.49), (838, 18.66), (885, 18.82), (910, 18.93), (957, 19.28), (982, 19.37), (1042, 20.23), (1120, 99.19), (1198, 100.85), (1225, 101.19), (1250, 103.04), (1277, 103.38), (1302, 104.89), (1327, 105.73), (1352, 106.74), (1377, 108.07), (1402, 108.59), (1427, 110.41), (1452, 110.44), (1477, 112.29), (1502, 112.76), (1527, 114.14), (1552, 115.1), (1569, 115.4), (1594, 117.45), (1619, 119.79), (1637, 121.48),)),
                ((3,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((180, 15.85), (258, 16.12), (336, 16.25), (361, 16.29), (383, 16.43), (405, 16.51), (430, 16.73), (452, 16.75), (474, 16.77), (496, 17.02), (518, 17.07), (543, 17.17), (565, 17.28), (587, 17.39), (609, 17.54), (634, 17.61), (656, 17.7), (678, 17.8), (700, 18.02), (747, 18.05), (769, 18.31), (791, 18.34), (816, 18.49), (838, 18.65), (885, 18.81), (910, 18.93), (957, 19.27), (982, 19.37), (1042, 20.23), (1120, 99.11), (1198, 100.76), (1225, 101.1), (1250, 102.95), (1277, 103.29), (1302, 104.8), (1327, 105.64), (1352, 106.65), (1377, 107.98), (1402, 108.5), (1427, 110.32), (1452, 110.35), (1477, 112.2), (1502, 112.66), (1527, 114.05), (1552, 115.01), (1570, 115.38), (1595, 117.35), (1620, 119.69), (1638, 121.37),)),
                ((4,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((180, 15.66), (258, 15.88), (336, 16.01), (361, 16.09), (383, 16.19), (405, 16.26), (427, 16.5), (449, 16.52), (474, 16.53), (496, 16.77), (518, 16.81), (543, 16.96), (565, 17.02), (587, 17.12), (609, 17.27), (634, 17.4), (656, 17.43), (678, 17.53), (700, 17.75), (722, 17.78), (747, 17.83), (769, 18.03), (791, 18.06), (816, 18.27), (838, 18.37), (885, 18.52), (910, 18.7), (957, 18.98), (982, 19.14), (1042, 19.99), (1120, 98.94), (1198, 100.59), (1225, 100.93), (1250, 102.78), (1277, 103.12), (1302, 104.62), (1327, 105.46), (1352, 106.47), (1377, 107.8), (1402, 108.32), (1427, 110.13), (1452, 110.16), (1477, 112.01), (1502, 112.47), (1527, 113.85), (1552, 114.81), (1570, 115.18), (1595, 117.15), (1620, 119.49), (1638, 121.17),)),
                ((5,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((180, 16.4), (258, 16.62), (282, 16.82), (382, 16.93), (404, 17.19), (428, 17.23), (450, 17.24), (472, 17.44), (494, 17.55), (518, 17.65), (540, 17.69), (562, 17.86), (584, 17.94), (608, 18.06), (630, 18.18), (652, 18.2), (674, 18.45), (698, 18.48), (720, 18.49), (742, 18.7), (764, 18.8), (788, 18.89), (810, 18.95), (832, 19.11), (856, 19.31), (903, 19.44), (974, 19.72), (1042, 20.64), (1120, 98.94), (1198, 100.59), (1225, 100.93), (1250, 102.78), (1277, 103.12), (1302, 104.62), (1327, 105.46), (1352, 106.47), (1377, 107.8), (1402, 108.32), (1427, 110.13), (1452, 110.16), (1477, 112.01), (1502, 112.47), (1527, 113.85), (1552, 114.81), (1570, 115.18), (1595, 117.15), (1620, 119.49), (1638, 121.17),)),
                ((6,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((180, 16.26), (258, 16.46), (282, 16.67), (303, 16.76), (381, 16.78), (402, 17.02), (423, 17.05), (447, 17.08), (468, 17.25), (489, 17.35), (534, 17.49), (555, 17.64), (576, 17.73), (600, 17.91), (621, 17.93), (642, 17.97), (663, 18.21), (684, 18.23), (708, 18.32), (729, 18.44), (750, 18.52), (771, 18.68), (795, 18.73), (816, 18.82), (840, 19.14), (895, 19.23), (950, 19.52), (974, 19.55), (1042, 20.46), (1428, 75), (1638, 75.01),)),
                ((7,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((180, 16.22), (258, 16.4), (282, 16.63), (303, 16.7), (381, 16.72), (402, 16.95), (423, 16.99), (447, 17.04), (468, 17.19), (489, 17.28), (510, 17.43), (534, 17.45), (555, 17.57), (576, 17.66), (600, 17.86), (621, 17.87), (642, 17.9), (663, 18.14), (684, 18.16), (708, 18.27), (729, 18.38), (750, 18.45), (771, 18.61), (795, 18.68), (816, 18.75), (840, 19.09), (895, 19.16), (950, 19.36), (974, 19.5), (1042, 20.41), (1484, 75), (1634, 75.01),)),
                ((8,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((180, 15.91), (258, 16.09), (282, 16.32), (360, 16.33), (381, 16.39), (402, 16.57), (423, 16.68), (447, 16.74), (468, 16.8), (489, 16.98), (510, 17.04), (534, 17.15), (555, 17.27), (576, 17.28), (597, 17.52), (642, 17.56), (663, 17.76), (684, 17.86), (708, 17.97), (729, 17.99), (750, 18.15), (771, 18.23), (795, 18.39), (816, 18.45), (871, 18.78), (895, 18.8), (950, 19.06), (974, 19.21), (1042, 20.05), (1235, 75), (1340, 75.01), (1418, 99.19), (1445, 101.19), (1470, 103.04), (1495, 104.89), (1520, 106.74), (1545, 108.59), (1570, 110.44), (1595, 112.29), (1620, 114.14), (1634, 115.18),)),
                ((9,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((180, 16.29), (258, 16.46), (336, 16.7), (360, 16.71), (381, 16.77), (402, 16.95), (423, 17.07), (447, 17.13), (468, 17.19), (489, 17.37), (510, 17.43), (534, 17.55), (555, 17.67), (576, 17.68), (597, 17.92), (618, 17.97), (642, 17.98), (663, 18.17), (684, 18.27), (708, 18.4), (729, 18.41), (750, 18.58), (771, 18.66), (795, 18.82), (816, 18.88), (871, 19.19), (895, 19.25), (950, 19.51), (974, 19.67), (1042, 20.54), (1428, 75), (1638, 75.01),)),
                ((10,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((78, 16.15), (156, 16.29), (177, 16.45), (198, 16.54), (219, 16.76), (240, 16.78), (261, 17.03), (282, 17.06), (303, 17.27), (324, 17.36), (345, 17.52), (366, 17.67), (387, 17.76), (408, 17.97), (429, 18.01), (450, 18.25), (471, 18.27), (492, 18.58), (547, 18.79), (602, 19.21), (680, 98.86), (758, 100.51), (785, 100.85), (810, 102.69), (837, 103.03), (862, 104.54), (887, 105.37), (912, 106.38), (925.9, 107.41), (950.9, 107.7), (975.9, 110.04), (980.8, 110.51), (981, 150), (1184, 150.01),)),
                ((11,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((78, 16.13), (156, 16.26), (177, 16.43), (198, 16.51), (219, 16.73), (240, 16.75), (261, 17), (282, 17.03), (303, 17.24), (324, 17.34), (345, 17.49), (366, 17.64), (387, 17.73), (408, 17.94), (429, 17.98), (450, 18.22), (471, 18.25), (492, 18.55), (547, 18.76), (602, 19.18), (680, 98.86), (758, 100.51), (785, 100.85), (810, 102.69), (837, 103.03), (862, 104.54), (887, 105.37), (912, 106.38), (937, 107.7), (962, 108.22), (987, 110.04), (1012, 110.07), (1037, 111.91), (1062, 112.38), (1087, 113.76), (1112, 114.71), (1126, 114.79), (1137.4, 115.79), (1137.5, 150), (1190, 150.01),)),
                ((12,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((180, 15.67), (258, 15.84), (336, 15.98), (360, 16.09), (382, 16.15), (403, 16.22), (446, 16.46), (470, 16.51), (491, 16.7), (513, 16.77), (537, 16.93), (558, 16.94), (580, 17.09), (601, 17.18), (625, 17.34), (647, 17.4), (668, 17.42), (689, 17.66), (711, 17.71), (735, 17.76), (756, 17.9), (778, 18.02), (802, 18.18), (824, 18.33), (879, 18.45), (903, 18.6), (950, 18.98), (974, 19.02), (1042, 19.87), (1120, 98.86), (1198, 100.51), (1225, 100.85), (1250, 102.69), (1277, 103.03), (1302, 104.54), (1327, 105.37), (1352, 106.38), (1362.9, 107.19), (1387.9, 107.7), (1412.9, 110.04), (1427.8, 111.44), (1428, 150), (1638, 150.01),)),
            ),
            6180: (  # Oak Grove
                ((1,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((826, 3.66), (839, 3.68), (842, 3.69), (845, 3.7), (849, 3.71), (852, 3.72), (880, 3.73), (1706, 3.93), (1719, 3.95), (1722, 3.96), (1725, 3.97), (1729, 3.98), (1732, 3.99), (1760, 4),)),
                ((2, 3, 4, 5, 11, 12,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((826, 4.11), (839, 4.12), (842, 4.13), (845, 4.14), (849, 4.15), (852, 4.16), (880, 4.17), (1706, 4.42), (1719, 4.44), (1722, 4.45), (1725, 4.46), (1729, 4.47), (1732, 4.48), (1760, 4.49),)),
                ((6, 7,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((826, 4.13), (839, 4.14), (842, 4.15), (845, 4.16), (849, 4.17), (852, 4.18), (880, 4.19), (1706, 4.42), (1719, 4.44), (1722, 4.45), (1725, 4.46), (1729, 4.47), (1732, 4.48), (1760, 4.49),)),
                ((8,), (0, 1, 2, 3, 4, 5, 6,), ((1760, 60.26),)),
                ((8,), (7, 8,), ((826, 4.42), (839, 4.44), (842, 4.45), (845, 4.46), (849, 4.47), (852, 4.48), (880, 4.49), (1760, 60.26),)),
                ((8,), (9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,), ((826, 4.13), (839, 4.14), (842, 4.15), (845, 4.16), (849, 4.17), (852, 4.18), (880, 4.19), (1706, 4.42), (1719, 4.44), (1722, 4.45), (1725, 4.46), (1729, 4.47), (1732, 4.48), (1760, 4.49),)),
                ((8,), (23,), ((1760, 60.26),)),
                ((9,), (0, 1, 2, 3, 4, 5, 6, 7, 8,), ((1760, 60.26),)),
                ((9,), (9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,), ((826, 4.13), (839, 4.14), (842, 4.15), (845, 4.16), (849, 4.17), (852, 4.18), (880, 4.19), (1706, 4.42), (1719, 4.44), (1722, 4.45), (1725, 4.46), (1729, 4.47), (1732, 4.48), (1760, 4.49),)),
                ((9,), (23,), ((1760, 60.26),)),
                ((10,), (0, 1, 2, 3, 4, 5, 6, 7, 8,), ((1760, 61.46),)),
                ((10,), (9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,), ((826, 4.11), (839, 4.12), (842, 4.13), (845, 4.14), (849, 4.15), (852, 4.16), (880, 4.17), (1706, 4.42), (1719, 4.44), (1722, 4.45), (1725, 4.46), (1729, 4.47), (1732, 4.48), (1760, 4.49),)),
                ((10,), (23,), ((1760, 61.46),)),
            ),
            6183: (  # San Miguel
                ((1, 2,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((320, -249), (321, 19), (396, 20),)),
                ((3,), (0, 1, 2, 3, 4, 5, 6, 7, 8,), ((320, -249), (321, 19), (396, 20),)),
                ((3,), (9, 10, 11, 12,), ((220, -249), (221, 0), (396, 1),)),
                ((3,), (13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((320, -249), (321, 19), (396, 20),)),
                ((4, 6, 7, 9, 10, 11, 12,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((220, -249), (221, 42), (396, 43),)),
                ((5,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((220, -249), (221, 40), (396, 41),)),
                ((8,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((220, -249), (221, 42), (300, 43), (305, 50), (396, 51),)),
            ),
            7030: (  # Major Oak
                ((1, 2, 3, 4, 5,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((160, 10), (310, 10.01),)),
                ((6, 7, 8, 9,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((160, 13), (310, 13.01),)),
                ((10,), (0, 1, 2, 3, 4,), ((160, 10), (310, 10.01),)),
                ((10,), (5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,), ((160, 13), (310, 13.01),)),
                ((10,), (23,), ((160, 10), (310, 10.01),)),
                ((11,), (0, 1, 2, 3, 4, 5,), ((160, 10), (310, 10.01),)),
                ((11,), (6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((160, 13), (310, 13.01),)),
                ((12,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((160, 10), (170, 24.53), (181, 25.01), (191, 25.27), (202, 25.45), (213, 25.48), (224, 25.63), (234, 25.8), (244, 25.91), (255, 25.98), (266, 26.16), (277, 26.35), (288, 26.38), (299, 26.85), (310, 27.33),)),
            ),
            7097: (  # JK Spruce
                ((1,), (0, 1, 2, 3, 4,), ((290, 33.53), (300, 34), (380, 35), (420, 36), (440, 37), (460, 38), (590, 39), (610, 40), (800, 41), (925, 63.26), (1249, 64), (1250, 75), (1300, 75.01), (1360, 75.02),)),
                ((1,), (5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,), ((125, 33.26), (135, 33.36), (425, 33.53), (435, 34), (515, 35), (555, 36), (575, 37), (595, 38), (725, 39), (745, 40), (935, 41), (1250, 75), (1300, 75.01), (1360, 75.02),)),
                ((1,), (22, 23,), ((290, 33.53), (300, 34), (380, 35), (420, 36), (440, 37), (460, 38), (590, 39), (610, 40), (800, 41), (925, 63.26), (1249, 64), (1250, 75), (1300, 75.01), (1360, 75.02),)),
                ((2,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((415, 33.26), (425, 33.36), (739, 34.9), (1055, 75), (1225, 75.01), (1345, 75.02),)),
                ((3,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((290, 16.74), (300, 16.85), (380, 17.69), (420, 18.09), (440, 18.29), (460, 18.48), (590, 19.62), (610, 19.78), (800, 21.12), (925, 26.6), (1219, 29.4), (1220, 75), (1320, 75.01), (1360, 75.02),)),
                ((4, 12,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((290, 16.59), (300, 16.7), (425, 17.28), (435, 17.37), (515, 17.53), (555, 17.74), (595, 17.92), (625, 18.02), (645, 18.11), (665, 18.3), (735, 18.67), (765, 18.95), (895, 19.43), (915, 19.59), (985, 19.6), (1015, 19.88), (1205, 20.92), (1365, 21.37),)),
                ((5,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((290, 16.35), (300, 16.46), (425, 17.03), (505, 17.28), (545, 17.67), (565, 17.86), (585, 18.04), (715, 19.15), (735, 19.31), (989, 19.36), (1179, 20.62), (1180, 75), (1275, 75.01), (1360, 75.02),)),
                ((6,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((290, 16.2), (300, 16.3), (425, 16.87), (505, 17.11), (545, 17.5), (565, 17.68), (585, 17.87), (715, 18.97), (735, 19.12), (989, 19.17), (1179, 20.42), (1180, 75), (1280, 75.01), (1360, 75.02),)),
                ((7,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((290, 15.96), (300, 16.06), (425, 16.62), (505, 16.86), (545, 17.24), (565, 17.42), (585, 17.6), (715, 18.69), (735, 18.84), (989, 18.89), (1179, 20.12), (1180, 75), (1270, 75.01), (1310, 75.02), (1360, 75.03),)),
                ((8,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((290, 15.8), (300, 15.91), (425, 16.45), (435, 16.54), (515, 16.7), (555, 16.9), (595, 17.07), (625, 17.16), (645, 17.25), (665, 17.43), (735, 17.78), (765, 18.05), (895, 18.5), (915, 18.65), (985, 18.66), (1015, 18.93), (1205, 19.92), (1365, 20.34),)),
                ((9,), (0, 1, 2, 3,), ((125, 16.62), (309, 18.26), (599, 50.01), (609, 50.02), (689, 50.03), (729, 50.04), (749, 50.05), (769, 50.06), (899, 50.07), (919, 50.08), (1109, 50.09), (1110, 85), (1210, 85.01), (1260, 85.02), (1360, 85.03),)),
                ((9,), (4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,), ((290, 15.96), (300, 16.06), (425, 16.62), (505, 16.86), (545, 17.24), (565, 17.42), (585, 17.6), (769, 18.26), (899, 18.69), (919, 18.84), (1109, 20.12), (1110, 85), (1210, 85.01), (1260, 85.02), (1360, 85.03),)),
                ((9,), (23,), ((125, 16.62), (309, 18.26), (599, 50.01), (609, 50.02), (689, 50.03), (729, 50.04), (749, 50.05), (769, 50.06), (899, 50.07), (919, 50.08), (1109, 50.09), (1110, 85), (1210, 85.01), (1260, 85.02), (1360, 85.03),)),
                ((10,), (0, 1, 2, 3, 4,), ((290, 16.43), (300, 16.54), (380, 17.36), (420, 17.75), (440, 17.94), (460, 18.13), (590, 19.25), (610, 19.4), (800, 20.72), (925, 50.01), (935, 50.02), (975, 50.03), (1005, 50.04), (1075, 50.05), (1105, 50.06), (1175, 50.07), (1205, 50.08), (1365, 50.09),)),
                ((10,), (5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((290, 16.43), (300, 16.54), (425, 17.11), (435, 17.2), (515, 17.36), (555, 17.57), (595, 17.75), (625, 17.85), (645, 17.94), (665, 18.13), (735, 18.49), (765, 18.77), (895, 19.25), (915, 19.4), (985, 19.42), (1015, 19.69), (1205, 20.72), (1365, 21.17),)),
                ((11,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((290, 16.66), (300, 16.77), (425, 17.36), (435, 17.45), (515, 17.61), (555, 17.83), (595, 18.01), (625, 18.11), (645, 18.2), (665, 18.39), (735, 18.76), (765, 19.04), (895, 19.52), (915, 19.68), (985, 19.7), (1015, 19.98), (1205, 21.02), (1365, 21.48),)),
            ),
            56611: (  # Sandy Creek
                ((1,), (0, 1, 2, 3, 4, 5, 6, 7, 8,), ((90, 33.44), (268.2, 35.72), (634.9, 35.73), (675.9, 38.5), (681.9, 38.66), (687.9, 38.83), (693.9, 38.99), (699.9, 39.15), (705.9, 39.32), (711.9, 39.48), (717.9, 39.64), (723.9, 39.81), (724, 39.99), (867.1, 40), (884.1, 40.22), (884.2, 75), (934.8, 75.01),)),
                ((1,), (9, 10, 11, 12, 13,), ((90, 33.44), (268.2, 35.72), (685.8, 35.73), (726.8, 38.5), (732.8, 38.66), (738.8, 38.83), (744.8, 38.99), (750.8, 39.15), (756.8, 39.32), (762.8, 39.48), (768.8, 39.64), (774.8, 39.81), (774.9, 39.99), (918, 40), (935, 40.22),)),
                ((1,), (14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((90, 33.44), (268.2, 35.72), (634.9, 35.73), (675.9, 38.5), (681.9, 38.66), (687.9, 38.83), (693.9, 38.99), (699.9, 39.15), (705.9, 39.32), (711.9, 39.48), (717.9, 39.64), (723.9, 39.81), (724, 39.99), (867.1, 40), (884.1, 40.22), (884.2, 75), (934.8, 75.01),)),
                ((2,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((41, 28.17), (47, 28.33), (53, 28.49), (59, 28.65), (65, 28.82), (71, 28.98), (77, 29.14), (83, 29.3), (89, 29.46), (106, 29.86), (284.2, 31.99), (650.9, 32), (740.9, 33.44), (741, 34.99), (884.1, 35), (884.2, 75), (934.8, 75.01),)),
                ((3,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,), ((41, 21.21), (47, 21.35), (53, 21.5), (59, 21.65), (65, 21.79), (71, 21.94), (77, 22.09), (83, 22.23), (89, 22.38), (106, 22.75), (284.2, 31.99), (650.9, 32), (740.9, 33.44), (741, 34.99), (884.1, 35), (884.2, 75), (934.8, 75.01),)),
                ((3,), (18,), ((41, 21.21), (47, 21.35), (53, 21.5), (59, 21.65), (65, 21.79), (71, 21.94), (77, 22.09), (83, 22.23), (89, 22.38), (106, 22.75), (284.2, 31.99), (701.8, 32), (791.8, 33.44), (791.9, 34.99), (935, 35),)),
                ((3,), (19, 20, 21, 22, 23,), ((41, 21.21), (47, 21.35), (53, 21.5), (59, 21.65), (65, 21.79), (71, 21.94), (77, 22.09), (83, 22.23), (89, 22.38), (106, 22.75), (284.2, 31.99), (650.9, 32), (740.9, 33.44), (741, 34.99), (884.1, 35), (884.2, 75), (934.8, 75.01),)),
                ((4,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,), ((41, 21.29), (47, 21.43), (53, 21.58), (59, 21.73), (65, 21.88), (71, 22.02), (77, 22.17), (83, 22.32), (89, 22.47), (106, 22.83), (196, 25.5), (196.1, 25.51), (339.2, 25.52), (517.4, 30.47), (884.1, 30.48), (884.2, 75), (934.8, 75.01),)),
                ((4,), (17, 18, 19,), ((41, 21.29), (47, 21.43), (53, 21.58), (59, 21.73), (65, 21.88), (71, 22.02), (77, 22.17), (83, 22.32), (89, 22.47), (106, 22.83), (196, 25.5), (196.1, 25.51), (339.2, 25.52), (517.4, 30.47), (935, 30.48),)),
                ((4,), (20, 21, 22, 23,), ((41, 21.29), (47, 21.43), (53, 21.58), (59, 21.73), (65, 21.88), (71, 22.02), (77, 22.17), (83, 22.32), (89, 22.47), (106, 22.83), (196, 25.5), (196.1, 25.51), (339.2, 25.52), (517.4, 30.47), (884.1, 30.48), (884.2, 75), (934.8, 75.01),)),
                ((5,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,), ((41, 21.65), (47, 21.8), (53, 21.94), (59, 22.09), (65, 22.24), (71, 22.38), (77, 22.53), (83, 22.68), (89, 22.83), (106, 23.19), (196, 25.5), (196.1, 25.51), (339.2, 25.52), (517.4, 30.47), (884.1, 30.48), (884.2, 75), (934.8, 75.01),)),
                ((5,), (19,), ((41, 21.65), (47, 21.8), (53, 21.94), (59, 22.09), (65, 22.24), (71, 22.38), (77, 22.53), (83, 22.68), (89, 22.83), (106, 23.19), (196, 25.5), (196.1, 25.51), (339.2, 25.52), (517.4, 30.47), (935, 30.48),)),
                ((5,), (20, 21, 22, 23,), ((41, 21.65), (47, 21.8), (53, 21.94), (59, 22.09), (65, 22.24), (71, 22.38), (77, 22.53), (83, 22.68), (89, 22.83), (106, 23.19), (196, 25.5), (196.1, 25.51), (339.2, 25.52), (517.4, 30.47), (884.1, 30.48), (884.2, 75), (934.8, 75.01),)),
                ((6,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,), ((41, 22.06), (47, 22.21), (53, 22.36), (59, 22.51), (65, 22.66), (71, 22.81), (77, 22.96), (83, 23.11), (89, 23.26), (106, 23.64), (196, 27.55), (196.1, 27.56), (339.2, 27.57), (517.4, 30.47), (884.1, 30.48), (884.2, 75), (934.8, 75.01),)),
                ((6,), (14, 15, 16, 17, 18, 19, 20,), ((41, 22.06), (47, 22.21), (53, 22.36), (59, 22.51), (65, 22.66), (71, 22.81), (77, 22.96), (83, 23.11), (89, 23.26), (106, 23.64), (196, 27.55), (196.1, 27.56), (339.2, 27.57), (517.4, 30.47), (935, 30.48),)),
                ((6,), (21, 22, 23,), ((41, 22.06), (47, 22.21), (53, 22.36), (59, 22.51), (65, 22.66), (71, 22.81), (77, 22.96), (83, 23.11), (89, 23.26), (106, 23.64), (196, 27.55), (196.1, 27.56), (339.2, 27.57), (517.4, 30.47), (884.1, 30.48), (884.2, 75), (934.8, 75.01),)),
                ((7,), (0, 1, 2, 3, 4, 5,), ((41, 22.22), (47, 22.37), (53, 22.52), (59, 22.68), (65, 22.83), (71, 22.98), (77, 23.13), (83, 23.28), (89, 23.43), (106, 23.81), (196, 27.55), (196.1, 27.56), (339.2, 27.57), (517.4, 30.47), (884.1, 30.48), (884.2, 75), (934.8, 75.01),)),
                ((7,), (6,), ((41, 22.22), (42, 22.25), (43, 22.27), (133, 27.55), (133.1, 27.56), (276.2, 27.57), (454.4, 30.47), (821.1, 30.48), (887.2, 75), (937.8, 75.01),)),
                ((7,), (7, 8, 9,), ((41, 22.22), (47, 22.37), (53, 22.52), (59, 22.68), (65, 22.83), (71, 22.98), (77, 23.13), (83, 23.28), (89, 23.43), (106, 23.81), (196, 27.55), (196.1, 27.56), (339.2, 27.57), (517.4, 30.47), (884.1, 30.48), (884.2, 75), (934.8, 75.01),)),
                ((7,), (10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,), ((41, 22.22), (47, 22.37), (53, 22.52), (59, 22.68), (65, 22.83), (71, 22.98), (77, 23.13), (83, 23.28), (89, 23.43), (106, 23.81), (196, 27.55), (196.1, 27.56), (339.2, 27.57), (517.4, 30.47), (935, 30.48),)),
                ((7,), (22, 23,), ((41, 22.22), (47, 22.37), (53, 22.52), (59, 22.68), (65, 22.83), (71, 22.98), (77, 23.13), (83, 23.28), (89, 23.43), (106, 23.81), (196, 27.55), (196.1, 27.56), (339.2, 27.57), (517.4, 30.47), (884.1, 30.48), (884.2, 75), (934.8, 75.01),)),
                ((8,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((41, 23.19), (47, 23.35), (53, 23.51), (59, 23.67), (65, 23.83), (71, 23.99), (77, 24.15), (83, 24.31), (89, 24.47), (106, 24.87), (196, 27.55), (196.1, 27.56), (339.2, 27.57), (551.4, 29.36), (679, 31.14), (813, 32.92), (935, 34.82),)),
                ((9,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,), ((41, 23.6), (47, 23.76), (53, 23.92), (59, 24.09), (65, 24.25), (71, 24.41), (77, 24.57), (83, 24.74), (89, 24.9), (106, 25.31), (196, 27.55), (196.1, 27.56), (339.2, 27.57), (551.4, 29.36), (679, 31.14), (813, 32.92), (935, 34.82),)),
                ((10,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,), ((41, 23.42), (47, 23.58), (53, 23.74), (59, 23.91), (65, 24.07), (71, 24.23), (77, 24.39), (83, 24.56), (89, 24.72), (106, 25.13), (196, 27.55), (196.1, 27.56), (408.3, 29.36), (635.8, 31.14), (669.9, 32.92), (721, 34.82), (864.1, 65), (864.2, 75), (934.8, 75.01),)),
                ((10,), (17, 18,), ((41, 23.42), (47, 23.58), (53, 23.74), (59, 23.91), (65, 24.07), (71, 24.23), (77, 24.39), (83, 24.56), (89, 24.72), (106, 25.13), (196, 27.55), (196.1, 27.56), (408.3, 29.36), (535.9, 31.14), (669.9, 32.92), (791.9, 34.82), (935, 65),)),
                ((10,), (19, 20, 21, 22, 23,), ((41, 23.42), (47, 23.58), (53, 23.74), (59, 23.91), (65, 24.07), (71, 24.23), (77, 24.39), (83, 24.56), (89, 24.72), (106, 25.13), (196, 27.55), (196.1, 27.56), (408.3, 29.36), (635.8, 31.14), (669.9, 32.92), (721, 34.82), (864.1, 65), (864.2, 75), (934.8, 75.01),)),
                ((11,), (0, 1, 2, 3, 4, 5,), ((41, 23.33), (47, 23.5), (53, 23.66), (59, 23.82), (65, 23.98), (71, 24.15), (77, 24.31), (83, 24.47), (89, 24.63), (106, 25.04), (196, 27.55), (196.1, 27.56), (408.3, 29.36), (635.8, 31.14), (669.9, 32.92), (721, 34.82), (864.1, 65), (864.2, 75), (934.8, 75.01),)),
                ((11,), (6,), ((41, 23.33), (47, 23.5), (53, 23.66), (59, 23.82), (65, 23.98), (71, 24.15), (77, 24.31), (83, 24.47), (89, 24.63), (106, 25.04), (196, 27.55), (196.1, 27.56), (408.3, 29.36), (535.9, 31.14), (669.9, 32.92), (791.9, 34.82), (935, 65),)),
                ((11,), (7, 8, 9, 10, 11, 12, 13, 14, 15, 16,), ((41, 23.33), (47, 23.5), (53, 23.66), (59, 23.82), (65, 23.98), (71, 24.15), (77, 24.31), (83, 24.47), (89, 24.63), (106, 25.04), (196, 27.55), (196.1, 27.56), (408.3, 29.36), (635.8, 31.14), (669.9, 32.92), (721, 34.82), (864.1, 65), (864.2, 75), (934.8, 75.01),)),
                ((11,), (17, 18,), ((41, 23.33), (47, 23.5), (53, 23.66), (59, 23.82), (65, 23.98), (71, 24.15), (77, 24.31), (83, 24.47), (89, 24.63), (106, 25.04), (196, 27.55), (196.1, 27.56), (408.3, 29.36), (535.9, 31.14), (669.9, 32.92), (791.9, 34.82), (935, 65),)),
                ((11,), (19, 20, 21, 22, 23,), ((41, 23.33), (47, 23.5), (53, 23.66), (59, 23.82), (65, 23.98), (71, 24.15), (77, 24.31), (83, 24.47), (89, 24.63), (106, 25.04), (196, 27.55), (196.1, 27.56), (408.3, 29.36), (635.8, 31.14), (669.9, 32.92), (721, 34.82), (864.1, 65), (864.2, 75), (934.8, 75.01),)),
                ((12,), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,), ((41, 22.84), (47, 23), (53, 23.16), (59, 23.32), (65, 23.48), (71, 23.64), (77, 23.8), (83, 23.95), (89, 24.11), (106, 24.51), (196, 27.55), (196.1, 27.56), (408.3, 29.36), (635.8, 31.14), (669.9, 32.92), (721, 34.82), (864.1, 65), (864.2, 75), (934.8, 75.01),)),
                ((12,), (17,), ((41, 22.84), (47, 23), (53, 23.16), (59, 23.32), (65, 23.48), (71, 23.64), (77, 23.8), (83, 23.95), (89, 24.11), (106, 24.51), (196, 27.55), (196.1, 27.56), (408.3, 29.36), (535.9, 31.14), (669.9, 32.92), (791.9, 34.82), (935, 65),)),
                ((12,), (18, 19, 20, 21, 22, 23,), ((41, 22.84), (47, 23), (53, 23.16), (59, 23.32), (65, 23.48), (71, 23.64), (77, 23.8), (83, 23.95), (89, 24.11), (106, 24.51), (196, 27.55), (196.1, 27.56), (408.3, 29.36), (635.8, 31.14), (669.9, 32.92), (721, 34.82), (864.1, 65), (864.2, 75), (934.8, 75.01),)),
            ),
        },
    },
}
# fmt: on

# CO2 emission rates (tCO2/MWh), derived from heat rate × fuel emission factor.
# Keyed by fuel class and efficiency bin, mirroring HEAT_RATE_BINS.
# Source: EPA eGRID 2022.
CO2_RATES: dict[str, dict[str, float]] = {
    "gas_cc": {
        "h_class": 0.36,  # EPA eGRID 2022 — H-class combined-cycle units
        "f_class": 0.38,  # EPA eGRID 2022 — F-class combined-cycle units
        "older": 0.43,  # EPA eGRID 2022 — legacy combined-cycle units
    },
    "gas_ct": {
        "aero": 0.51,  # EPA eGRID 2022 — aeroderivative combustion turbines
        "frame": 0.60,  # EPA eGRID 2022 — heavy-frame combustion turbines
        "older": 0.65,  # EPA eGRID 2022 — legacy combustion turbines
    },
    # Legacy natural-gas steam boilers (fuel gas_st, D-25 taxonomy fix).
    # 0.59 = 10.3 heat rate × 0.057 tCO2/MMBtu, the same back-solve
    # convention as FUEL_CO2_FACTOR_PER_MMBTU below, so the vintage-bin and
    # CAMPD-bin fleets stay consistent.
    "gas_st": {
        "default": 0.59,  # 10.3 × FUEL_CO2_FACTOR_PER_MMBTU["gas_st"] (0.057)
    },
    "coal": {
        "supercritical": 0.88,  # EPA eGRID 2022 — supercritical steam units
        "subcritical": 1.00,  # EPA eGRID 2022 — subcritical steam units
        "older": 1.08,  # EPA eGRID 2022 — legacy subcritical steam units
    },
    # Oil ≈ heat_rate(13.5) × distillate/residual factor(0.074) ≈ 1.0 tCO2/MWh.
    "oil": {
        "default": 1.00,  # EPA eGRID 2022 — petroleum-fired units
    },
    # Biomass biogenic CO2 is treated as carbon-neutral (not counted under
    # EPA/RGGI accounting), so its modeled CO2 rate is zero.
    "biomass": {
        "default": 0.0,  # EPA/RGGI — biogenic CO2 carbon-neutral
    },
}

# NOx emission rates (tons NOx/MWh) by fuel class.
# Source: EPA CAMPD (CEMS) 2023 annual rollup.
NOX_RATES: dict[str, float] = {
    "gas_cc": 0.00008,  # was 0.0001. EPA CEMS 2023 — SCR-equipped fleet average.
    "gas_ct": 0.00025,  # was 0.0003. EPA CEMS 2023 — mix of SCR/non-SCR CTs.
    "gas_st": 0.00025,  # EPA CEMS 2023 — legacy gas steam boilers, mostly non-SCR.
    "coal": 0.0012,  # was 0.0015. EPA CEMS 2023 — post-CSAPR compliance.
    "oil": 0.0004,  # EPA CEMS 2023 — oil-fired peakers/steam, mostly non-SCR.
    "biomass": 0.0010,  # EPA CEMS 2023 — biomass combustion, high NOx per MWh.
}

# CO2 emission factor (tCO2 per MMBtu of fuel burned) used to derive a
# generator's per-MWh CO2 rate directly from its heat rate:
#   emission_rate = heat_rate × FUEL_CO2_FACTOR_PER_MMBTU[fuel].
# Values are back-solved from the CO2_RATES / HEAT_RATE_BINS pairs above so
# the CAMPD-bin fleet stays consistent with the vintage-bin fleet: every
# gas CO2_RATES ÷ HEAT_RATE_BINS entry ≈ 0.057, every coal entry ≈ 0.100.
# The CAMPD bins carry CEMS-measured heat rates, so this lets them get an
# emission rate without a vintage lookup.
FUEL_CO2_FACTOR_PER_MMBTU: dict[str, float] = {
    "gas_cc": 0.057,  # natural gas — implied by EPA eGRID 2022 gas CC rates
    "gas_ct": 0.057,  # natural gas — same fuel as gas CC
    "gas_st": 0.057,  # natural gas — legacy gas steam boilers
    "coal": 0.100,  # coal — implied by EPA eGRID 2022 coal steam rates
    "oil": 0.074,  # distillate/residual fuel oil — EPA emission factors
    "biomass": 0.0,  # biogenic CO2 carbon-neutral under EPA/RGGI accounting
}

# ---------------------------------------------------------------------------
# Forward per-plant CO2-rate estimator (market_sim.data.emission_rates).
# The forecast-year CO2 rate for an existing unit is derived from its multi-year
# measured CAMPD history (rule-13-admissible measured input; see
# docs/handoffs/emissions-co2-rate-plan-2026-07.md). These tunables are the
# estimator's free parameters — CHOSEN ONCE from the committed leave-one-year-out
# harness (scripts/loyo_co2_rates.py) and frozen against backcast residuals
# (CLAUDE.md rules 23/24): they re-derive only when the CAMPD source data update.
# ---------------------------------------------------------------------------

# Trailing-window length (years) for the gen-weighted base rate. 0 = use ALL
# available history. Chosen ONCE from the committed LOYO harness on the full
# 7-year history (2018-2021 + 2023-2025), 2026-07-05 — the plan-§2.2 re-
# examination the 3-year default was provisional against. The FORWARD-CHAINED
# sweep (scripts/loyo_co2_rates.py --forward-chain --window-sweep, targets
# predicted from strictly-prior years — the direction matching production use,
# where "trailing" always means the years nearest the forecast year) shows a
# trailing 2-year window beats all-years uniformly on both swept ISOs:
# ERCOT wMAPE 2.59% vs 2.88% and PJM 3.35% vs 4.34% pooled, winning 8/8
# per-target comparisons and improving fleet-tons bias on 7/8 (plan §9.1
# wave-2 tables) — measured plant rates drift (aging/retrofits), so recent
# years are more predictive. (The symmetric LOYO direction inverts this
# ordering only because a "trailing" window for an early target selects the
# years FURTHEST from it — an artifact of backward prediction, not evidence
# against the window.) Re-derives only on a CAMPD source-data update (rule 23).
CO2_RATE_TRAILING_WINDOW_YEARS: int = 2

# Envelope-gate threshold: the operation-conditioned nearest-neighbor refinement
# (plan §2.1 step 2) fires ONLY when the target-year simulated operating point
# falls outside the plant's historical envelope by more than this L1 distance on
# the normalized (annual gen, starts, CF-band) descriptor. Inside the envelope
# the gen-weighted base is kept — near-duplicate history years make a single-year
# NN pick lose to the average (plan §3: oracle NN loses on 2023/2024 targets).
# Chosen once from the LOYO harness; see the plan doc for the sweep.
CO2_RATE_ENVELOPE_GATE_L1: float = 0.5

# Percentile of the per-class (plant_group × fuel) CAMPD rate distribution used
# for CEMS-uncovered plants and new entrants (plan §2.1 step 4). 50 = gen-weighted
# class median.
CO2_RATE_CLASS_MEDIAN_PERCENTILE: float = 50.0

# Whether the operation-conditioned refinement ships enabled. Per the plan's
# acceptance gate it stays OFF (estimator == pure gen-weighted a_gw) unless the
# 7-year held-in LOYO shows the envelope-gated conditioner beats plain a_gw.
# 7-YEAR VERDICT (2026-07-05, plan §9.1): the gate stays CLOSED. On the full
# 2018-2021+2023-2025 history the envelope-gated sim-conditioned estimator
# (--gate-sweep 0.1/0.25/0.5/1.0) never beats plain a_gw on ERCOT — the only
# ISO whose keeper persists simulated operation — (pooled wMAPE 2.89-2.93% vs
# a_gw 2.89%), and PJM's marginal 0.03pp gated edge is oracle-operation (no
# sim-op bundle exists), not a demonstrable sim-conditioned win. The estimator
# ships as the pure trailing-window gen-weighted average.
CO2_RATE_CONDITIONING_ENABLED: bool = False

# ---------------------------------------------------------------------------
# Forward emission-control retrofit channel
# (docs/handoffs/emission-control-retrofit-forward-channel-2026-07.md).
#
# The trailing-window CO2/NOx/SO2 estimator only picks up REALIZED emission-rate
# drift once a control shows in the measured history. It has no forward channel
# for an ANNOUNCED control install (SCR, scrubber/FGD, DSI, carbon-capture) that
# will step a covered unit's forward rate in a future year. This channel injects
# that step ahead of realized history, sourced from EIA-860's committed
# environmental-control pipeline (a forward driver — an install *date*, not a
# residual). Forecast-only, config-gated, default OFF (rule 13; see the handoff).
#
# The measured-history window feeding the estimator ends in this year: an
# environmental control already OPERATING by here is already reflected in the
# measured rate, so only controls with an Inservice Year AFTER it are forward
# steps the estimator has not yet absorbed. 2025 is the last non-quarantined
# CAMPD actual year (2022/H1-2026 are under holdout quarantine, CLAUDE.md rule
# 22). Re-derives only when the CAMPD/EIA-860 source window advances (rule 23).
CONTROL_RETROFIT_HISTORY_END_YEAR: int = 2025

# EIA-860 environmental-control-equipment ``Status`` codes that denote a
# committed-but-not-yet-operating control: PL = planned, CO = under
# construction, TS = testing, OZ = other-planned. A row in one of these with a
# future Inservice Year is an announced forward install. (Operating ``OP`` rows
# are already in the measured history; RE/CN/OS/SB are retired/cancelled/out of
# service and never fire.) Source: EIA-860 Schedule 6 status domain.
CONTROL_RETROFIT_ANNOUNCED_STATUSES: tuple[str, ...] = ("PL", "CO", "TS", "OZ")

# EIA-860 control ``Equipment Type`` -> (target pollutant, class-typical removal
# fraction). The post-control rate is the unit's own measured pre-control rate
# stepped by the fraction: ``post = pre * (1 - removal_fraction)`` — a physical
# multiplier on a measured input, exactly mirroring the CCS retrofit screen's
# ``emission_rate_co2 *= (1 - capture_rate)`` (methodology spec §5.6). Fractions
# are class-typical engineering values (EPA AP-42 Ch.1 / EIA-860 reported
# efficiencies): SCR NOx removal 80-90%; SNCR 25-40%; wet/dry FGD SO2 90-98%;
# dry sorbent injection 40-60%. CO2 (carbon capture) is intentionally ABSENT —
# economically-triggered CCS is owned by the CCS retrofit screen (one mechanism
# per phenomenon, CLAUDE.md rule 15); this table carries only the SO2/NOx
# controls the CCS screen does not. Extensible when EIA-860 gains capture codes.
CONTROL_RETROFIT_TYPE_MAP: dict[str, tuple[str, float]] = {
    "SR": ("nox", 0.90),  # Selective catalytic reduction (SCR)
    "SN": ("nox", 0.35),  # Selective non-catalytic reduction (SNCR)
    "JB": ("so2", 0.95),  # Jet-bubbling reactor (wet FGD)
    "SD": ("so2", 0.95),  # Spray-dryer / dry FGD
    "CD": ("so2", 0.95),  # Circulating dry scrubber
    "DSI": ("so2", 0.50),  # Dry sorbent injection
}

# All monetary values in this model are in constant 2026 real USD.
# Anchor date: January 1, 2026. No inflation adjustment is applied
# within the model. Nominal conversions are post-processing only
# (see results/export.py).
REAL_DOLLAR_BASE_YEAR = 2026  # Source: model convention, matches simulation start year

# Assumed long-run inflation rate for nominal-to-real conversion.
# Used to derive real discount rate from nominal WACC for LCOE calculations.
# Source: Federal Reserve 2% target + historical overshoot buffer.
INFLATION_RATE = 0.022

# Variable O&M ($/MWh) by fuel type.
# Source: NREL ATB 2024.
VOM: dict[str, float] = {
    "gas_cc": 2.0,  # NREL ATB 2024 — combined-cycle gas
    "gas_ct": 3.5,  # NREL ATB 2024 — combustion turbine gas
    "gas_st": 4.0,  # NREL ATB 2024 — legacy gas steam (higher O&M than CC)
    "coal": 4.5,  # NREL ATB 2024 — coal steam
    "nuclear": 2.5,  # NREL ATB 2024 — nuclear
    "wind": 0.0,  # NREL ATB 2024 — onshore wind
    "solar": 0.0,  # NREL ATB 2024 — utility-scale solar PV
    "oil": 4.5,  # NREL ATB 2024 — oil steam/peaker O&M (≈ coal steam)
    "biomass": 5.0,  # NREL ATB 2024 — biomass (fuel handling raises O&M)
    "hydro": 1.4,  # NREL ATB 2024 — conventional hydropower
    # The base-fuel-class VOM component is 0 for the CCS retrofit tech: the
    # incremental solvent/amine-handling O&M is priced separately as
    # CCUS_PARAMS["gas_cc_ccs_90"]["vom_adder"] in the tech's own cost build,
    # so this entry only supplies the class lookup used by model/capacity.py's
    # generic per-tech cost paths (was an inline ``.get(tech, 0.0)`` fallback).
    "gas_cc_ccs": 0.0,
}

# Pumped-storage hydro fleet parameters (EIA-860 PS units enter the storage
# block alongside batteries; EIA-860 reports power but not energy or RTE).
# Duration: the US PSH fleet averages ~10 h of storage at nameplate (DOE
# "Pumped Storage Hydropower" 2023 fact sheet; Bath County ≈ 10.5 h).
PUMPED_STORAGE_DURATION_HOURS: float = 10.0
# Round-trip efficiency: mid-range of the 70-85% PSH band (DOE/Sandia Energy
# Storage Handbook; DOE PSH fact sheet cites ~80%).
PUMPED_STORAGE_RTE: float = 0.80
# Pumped-storage dispatch adder ($/MWh discharged) by ISO — the reduced-form
# opportunity cost of the regulation/reserve duty the energy-only LP does not
# see (PSH pure O&M is < $1/MWh).
#
# PJM: RETIRED (was $10). The $10 was calibrated 2026-06-10 ("pjm 3 ps-adder")
# to pull model PS discharge from ~9-10 TWh down to a target read as "~3.5-4
# TWh/yr of EIA-923 gross generation". That target was a MEASUREMENT ERROR: the
# EIA-923 PS series for PJM is NET generation (~-2.6 TWh/yr — generation minus
# pumping load, i.e. the round-trip LOSS), NOT gross discharge. The actual
# discharge throughput implied by that measured net and the model's own RTE 0.80
# is |net|*RTE/(1-RTE) ≈ 10 TWh; triangulated against PJM's own gen-by-fuel
# (Hydro series minus EIA-923 conventional HY) it is ~6.5-7 TWh. So the model's
# original ~9-10 TWh was approximately CORRECT and the $10 adder suppressed
# legitimate arbitrage to land on the round-trip-loss figure. Per CLAUDE.md #12
# (a lever may not be tuned to a mis-measured residual with no forward analogue)
# the fitted knob is retired; PJM PS now arbitrages on its physical RTE like
# every other storage resource. EIA-930 carries no PJM PS/BAT breakout at all,
# so C5b has no clean scoreable actual — see
# docs/multi-iso/pjm-ps-cycling-diagnosis-2026-06.md. A measured PJM
# synchronized-reserve power reservation (the ERCOT reserve_storage_as_power
# analogue) is the forward-valid replacement if PS later over-cycles; that is a
# real reserve quantity, handed to the reserve workstream, not a throughput tune.
#
# ISOs absent from the map resolve to 0.0 — notably CAISO, whose adder stays
# off until a CAISO calibration pass measures Helms' reserve duty.
PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO: dict[str, float] = {}

# Per-plant cited-physical parameters for CAISO's six pumped-storage plants
# (lane 5 of the close-out campaign, GATESPEC-caiso195-ps-physical-2026-08-11;
# armed by ScenarioConfig.caiso_ps_plant_params, default off). Replaces the
# single NP15 aggregate (fleet-average duration/RTE) with per-plant units.
# EVERY value is a published public figure or fixed-constant arithmetic on
# published figures (rule 5 [R-NO-MAGIC]; rule 13 admissibility: static plant
# ratings regenerate for a forward year from the same public documents).
# power_cap stays the EIA-860 nameplate the shipped loader already reads
# (G-AGG: zero MW added); zones stay the model's own build_zone_lookup
# geography (G-ZONE: all six resolve NP15). RTE keeps PUMPED_STORAGE_RTE for
# every plant (per-plant RTE is NOT in the gatespec's parameter list).
#
# pump_mw — cited pump-side capability (LP charge cap, tighten-only vs the
#   power cap; a cited pump rating ABOVE the EIA-860 PS-unit nameplate clips
#   to it, disclosed in the PRECHECK — Hyatt/Thermalito/O'Neill):
#   * Helms 930.0: PG&E, "Helms Pumped Storage Plant" (M. Yeung, NW Wind
#     Integration Forum workshop, 2008-10-17, nwcouncil.org), p.4-5: "1,212 MW
#     total in generation mode, and 930 MW total in pump mode".
#   * Hyatt 387.0 / Robie Thermalito 89.5 / Gianelli 375.8: DWR Bulletin
#     132-22 (Sept 2025), Ch.1 SWP pumping-plants table (p.9): total motor
#     ratings 519,000 / 120,000 / 504,000 hp x 745.7 W/hp.
#   * O'Neill 26.8: USBR, EWA Draft EIS/EIR (July 2003) Ch.16 §16.2.7.1.1,
#     six 6,000-hp pump motors (Reclamation 2001) x 745.7 W/hp.
#   * Eastwood None: no public pump-mode rating found (FERC P-67 narrative
#     sources give generating rating/head only) — the component keeps the
#     unrestrained default (charge cap = power cap), the GATESPEC §4.1
#     more-pumping-capability direction for an uncited parameter.
# energy_mwh — cited reservoir volume x (cited MW / cited design flow), gross
#   volumes (overstates usable storage -> MORE cycling capability, the
#   GATESPEC §4.1 anti-flattering direction):
#   * Helms 200,424: Courtright (upper) 123,000 AF x 1,212 MW / 9,000 cfs
#     (PG&E deck p.4-5; 9,000 cfs = 743.80 AF/h).
#   * Hyatt 31,678: pump-back cycle store = Thermalito Forebay 11,800 AF +
#     Afterbay 57,000 AF (B132-22 Table 1-1) x 645 MW / 16,950 cfs (Table
#     1-4). The afterbay is the pump-back store the public record names (USBR
#     EWA EIS §16.2.5.2.6); forebay included per §4.1 (more capability).
#     Hyatt STAYS IN the storage block — this is a static cited bound, no
#     energy re-allocation, no shape (caiso-141 §G / owner ruling 4).
#   * Robie Thermalito 4,519: Afterbay 57,000 AF x 114 MW / 17,400 cfs.
#   * Gianelli 613,410: San Luis gross 2,027,800 AF (B132-22 Table 1-1) x
#     424 MW / 16,960 cfs (Table 1-4).
#   * O'Neill 4,095: O'Neill Forebay gross 56,400 AF x 25.2 MW / 4,200 cfs
#     (USBR EWA EIS: 6 units x 700 cfs, 4,200 kW each).
#   * Eastwood None: Balsam Meadow forebay volume not found in a public
#     document — the component keeps the incumbent fleet-average duration
#     (PUMPED_STORAGE_DURATION_HOURS x its EIA-860 nameplate), the uncited-
#     component default the GATESPEC's kill rule prescribes ("that component
#     out" — its parameters stay incumbent; the plant still splits out so
#     G-AGG conservation and per-plant zone/citation accounting stay whole).
# Full citation chain + reconciliation arithmetic:
# results/calibration/_caiso197_ps_citations.json and
# PRECHECK-caiso197-ps-physical-2026-08-16.md.
CAISO_PS_PLANT_PARAMS: dict[int, dict[str, float | str | None]] = {
    6100: {"name": "Helms", "pump_mw": 930.0, "energy_mwh": 200_424.0},
    437: {"name": "Edward C Hyatt", "pump_mw": 387.0, "energy_mwh": 31_678.0},
    438: {"name": "Robie Thermalito", "pump_mw": 89.5, "energy_mwh": 4_519.0},
    448: {"name": "W R Gianelli", "pump_mw": 375.8, "energy_mwh": 613_410.0},
    446: {"name": "O'Neill", "pump_mw": 26.8, "energy_mwh": 4_095.0},
    104: {"name": "J S Eastwood", "pump_mw": None, "energy_mwh": None},
}

# NYISO treaty-mandated minimum flows for the two large NYPA hydro plants.
# EIA plant IDs are the EIA-860/923 ORIS codes used throughout the model.
#
# Niagara (plant 2693 — Robert Moses Niagara Power Plant, ~2,429 MW):
#   The Treaty Between the United States and Canada Concerning Diversion of
#   the Niagara River (27 UST 1957, signed 1950; effective 1954) requires
#   maintaining scenic flows of 50,000 cfs (Nov–Mar) / 100,000 cfs (Apr–Oct)
#   over Horseshoe Falls. This reduces divertible flow to 60–75% of the ~202,000
#   cfs average natural flow, with a minimum power-generation obligation
#   corresponding to ~25% of nameplate. Source: International Joint Commission,
#   "Supplementary Order of Approval No. 2", 1953; FERC Project No. 2216 (NYPA).
#
# St-Lawrence (plant 2694 — Robert Moses Power Dam, ~912 MW):
#   The IJC Order of Approval governing Lake Ontario / St. Lawrence outflows
#   (original order 1952; superseded by "Plan 2014", effective 2017) requires
#   minimum hydraulic flows for navigation, ecology, and power. The Moses-Saunders
#   dam at Massena typically operates above 50% of nameplate continuously.
#   Source: International Joint Commission, "Lake Ontario–St. Lawrence River
#   Plan 2014", 2016; FERC Project No. 2000 (NYPA/OPG).
NYISO_HYDRO_TREATY_MIN_FLOW: dict[int, float] = {
    2693: 0.25,  # Robert Moses Niagara Power Plant — 1950 Niagara Treaty
    2694: 0.50,  # Robert Moses Power Dam (St-Lawrence) — IJC Order / Plan 2014
}

# --- Forecast hydro monthly-energy budget (G9 forward analogue) -------------
# The hydro monthly-energy-budget LP constraint (dispatch chooses *when* within
# the month) is the forward mechanism; only its monthly *level* is a measured
# input in a backcast. The forecast level is a normal-water-year climatology:
# the mean of the measured EIA-930 NG:WAT (conventional hydro) monthly series
# across the years below, so a forecast year inherits a normal water year rather
# than any single year's wet/dry draw. The window is the full EIA-930 hydro
# history available across the modeled ISOs (years a given ISO does not cover
# are simply skipped, so a short extract still yields a climatology). Built by
# data.eia_loader.climatological_monthly_hydro. Source: EIA-930 hourly NG:WAT,
# 2021-2025.
#
# ONE WINDOW, TWO SOURCES (miso-110). A BA in EIA930_PS_FOLDED_INTO_WAT below
# cannot use the NG:WAT series as a LEVEL at all — the same defect miso-109 fixed
# on the backcast path — so for those BAs data.hydro.forecast_monthly_hydro
# averages EIA-923 `HY` over this SAME window instead
# (data.hydro.climatological_monthly_hydro_923). The window constant is shared;
# what differs is which years each source can actually supply, so the REALISED
# window is logged at call time and is not assumed to equal this tuple.
#
# NOT EXTENDED for the 2022 hole, deliberately (rule 23 [R-FROZEN-DERIVE], which
# requires a SOURCE-DATA justification for a window change and there is none).
# MISO and CAISO realise only (2021, 2023, 2024, 2025) on the EIA-930 side
# because the wide per-BA extracts `data/raw/eia-930-hourly/{MISO,CISO}
# hourly.parquet` carry 7 and 9 rows for 2022 against 8760. That is an
# EXTRACT-BUILD gap, not missing source data: the per-year long-form
# `data/raw/eia-930/{MISO,CISO}_fueltype_2022.parquet` files are present and
# complete (61,320 / 70,080 rows). The remedy is rebuilding those two extracts
# in a data-intake session; moving this window would silently change the
# forecast level of every ISO to work around two files.
HYDRO_CLIMATOLOGY_YEARS: tuple[int, ...] = (2021, 2022, 2023, 2024, 2025)

# --- EIA-923 complete-filing coverage gate (miso-110) -----------------------
# Minimum share of an ISO's MODAL EIA-923 `HY` plant census that a year's filing
# must carry to enter the EIA-923 hydro climatology mean. EIA-923 vintages after
# the latest final release are monthly EARLY RELEASES covering only the
# monthly-survey (large) reporters; averaging one into a climatology would
# measure SOURCE COVERAGE, not hydrology (miso-109's "2025 trap": MISO files 14
# `HY` plants for 2025 against 163 for 2021-2024, a naive read of +918%).
#
# Identification: measured, and the two populations are separated by a wide
# EMPTY BAND, so the threshold is not a tuned edge (rule 5 [R-NO-MAGIC]).
# Over all six ISOs x 2018-2026 (scripts/probes/_miso110_forward_level_audit.py
# §A): the LARGEST early-release census ratio is 0.157 (CAISO 2025, 26/166) and
# the SMALLEST final-vintage ratio is 0.800 (ERCOT 2024, 12/15 — genuine
# attrition of very small hydro, not a coverage loss). 0.50 sits mid-band, 3.2x
# above the largest early release and 1.6x below the smallest complete filing.
# Re-derive only when the EIA-923 census data changes (rule 23). Source: on-disk
# per-year plant-census counts of the F923 monthly-generation extract.
EIA923_COMPLETE_FILING_CENSUS_FRACTION: float = 0.50

# --- BAs that fold pumped storage into EIA-930 NG: WAT (miso-108/miso-109) ---
# EIA-930's per-fuel split gives pumped storage its own `NG: PS` column. A BA
# that operates pumped storage but files NO such column has nowhere to report
# it, so its `NG: WAT` is a conventional-hydro PLUS pumped-storage-discharge
# series. The hydro LP units are conventional hydro ALONE (EIA-923 prime mover
# `HY`; data.hydro excludes `PS` — pumped storage is a storage resource, not
# inflow hydro), so pinning their monthly energy LEVEL to `NG: WAT` applies one
# population's energy to a different population's units. Rule 14 [R-ACCURATE]:
# the accurate level for these units is the EIA-923 `HY` series the per-plant
# budget already carries, and the listed ISOs take it instead of the pin.
#
# Membership is MEASURED on the BA's own data, never assumed — three signatures,
# reproduced by scripts/probes/_miso109_hydro_level_audit.py §1-§3:
#   (a) the BA's extract carries no `NG: PS` column;
#   (b) `NG: WAT` exceeds the BA's OWN conventional-hydro (`HY`) EIA-860
#       nameplate — physically impossible for inflow hydro — in hundreds of
#       hours a year; and
#   (c) there are ZERO negative `NG: WAT` hours, so pumping is not netted and
#       the contamination is one-way gross discharge.
# MISO: no `NG: PS`; `NG: WAT` peaks 3,535 / 3,964 MW (2023 / 2024) against a
# 2,478.4 MW conventional nameplate — 580 / 826 hours above it — beside a
# 2,416.8 MW PS fleet (Ludington 1,978.8, Taum Sauk 408, Degray 30); 0 negative
# hours in any year 2018-2025; `NG: WAT` 9.979 / 10.710 TWh against EIA-923 `HY`
# 8.789 / 9.041 TWh, i.e. +1.190 TWh / +13.5 % and +1.669 TWh / +18.5 %. EIA-923
# `PS` net generation is NEGATIVE every year (-0.840 / -1.033 TWh, the
# round-trip loss) — the opposite sign — independently confirming the 930 series
# is gross discharge.
#
# NO reconciliation FACTOR is applied, because none is identifiable from the
# source data (probe §4): MISO's conventional share of `NG: WAT` drifts
# 0.9937 -> 0.8442 across 2019-2024 (spread 0.15) and the monthly gap changes
# sign by month in 4 of the 5 complete-filing years. A fitted scale constant
# would be a free parameter with no forward story (rules 5 / 13 / 22).
#
# PJM (pjm-143, every number re-derived from source in that session —
# PREREG-pjm143-hydro-level-923hy-2026-07-31.md, committed before either A/B
# arm solved): no `NG: PS`; `NG: WAT` peaks 6,633 / 6,383 MW (2023 / 2024)
# against a 3,334.2 MW conventional nameplate — 1,437 / 1,572 hours above it
# (1,249-1,612 h/yr across 2019-2025) — beside a 5,046.1 MW PS fleet (Bath
# County 2,862.0, Muddy Run 1,072.0, Yards Creek 453.0, Seneca 411.8, Smith
# Mountain 247.3); 0 negative hours in any year 2019-2025; `NG: WAT` 15.451 /
# 15.819 TWh against EIA-923 `HY` 8.976 / 8.861 TWh, i.e. +6.475 TWh / +72.1 %
# and +6.957 TWh / +78.5 % — the LARGEST fold of the six ISOs (2025 not
# differenced: early release, 13 of a modal 77 plants). EIA-923 `PS` net
# generation is NEGATIVE every year (-2.525 / -2.673 TWh in 2023/24), the
# opposite sign. UNLIKE MISO, PJM's monthly gap NEVER changes sign (0 sign
# changes in all six complete-filing years, +166 to +984 GWh every month —
# Bath County cycles daily year-round), so the sign-change half of the MISO
# argument does not transfer (rule 25); the no-reconciliation-factor refusal
# at PJM rests on the conventional-share drift (0.654 -> 0.556 across
# 2019-2024, spread 0.097 — a factor fitted on one year misstates another by
# up to ~17 % relative), the 3-6x seasonal range of the gap (Jul/Aug ~900-980
# GWh vs Oct ~170-300 GWh — not one scalar), and rule 13's forward-story test.
#
# SCREENED but deliberately NOT listed — each ISO's own lane decides (rule 25):
#   NYISO — shows NONE of them (0-33 breach hours a year, <=0.007 TWh) and its
#           923 `HY` EXCEEDS `NG: WAT` by 4-6 % every year: the opposite bias,
#           not a PS fold.
#   NEISO — files `NG: PS` from Nov 2024 and has zero breach hours in 2025, so
#           its exposure is a TIME SPLIT of the older vintages, not a standing
#           fold, and needs a per-window treatment rather than this switch —
#           handled by EIA930_PS_SPLIT_COMPLETE_FROM below (neiso-72).
#
# HAZARD for a future session: the hydro dispatch ENVELOPE
# (HYDRO_ENVELOPE_PERCENTILE) and the MIN-FLOW FLOOR (HYDRO_MIN_FLOW_PERCENTILE)
# are also built from hourly `NG: WAT` and inherit the same contamination. Both
# are default-off and off in every listed ISO's keeper, so nothing is stacked
# here (rule 19), but arming either at a listed ISO needs its own source fix
# first — EIA-923 is monthly and offers no hourly substitute.
# Source: EIA-930 hourly per-BA extracts; EIA-923 monthly generation; EIA-860.
EIA930_PS_FOLDED_INTO_WAT: frozenset[str] = frozenset({"MISO", "PJM"})

# --- BAs whose EIA-930 NG: PS column starts MID-SERIES (neiso-72) ------------
# The TIME-SPLIT companion to EIA930_PS_FOLDED_INTO_WAT above: the BA DOES file
# `NG: PS`, but only from a first-filing hour, so every earlier vintage of its
# `NG: WAT` is a folded (conventional + pumped-storage-discharge) series and
# every later one is clean. Maps ISO -> the first calendar year WHOLLY on the
# split basis; a backcast year BEFORE it has its `NG: WAT` level pin REFUSED
# (the level stays on EIA-923 `HY`, the same population as the LP units) and a
# year AT/AFTER it keeps the pin. The seam year itself counts as FOLDED — a
# year is admissible on ONE source basis only, never spliced mid-year
# (design D, owner-adjudicated 2026-07-31 against the flat-refusal, mid-year-
# splice and subtract-an-estimated-PS alternatives;
# PREREG-neiso72-hydro-ps-window-2026-07-31.md §4-§4a).
#
# NEISO (neiso-72, every number from NEISO's own data — rule 25; probe
# scripts/probes/_neiso72_ps_window_audit.py): first filed `NG: PS` hour is
# 2024-11-07 00:00 (row 7440 of the 2024 extract) — ZERO filed hours in every
# month 2019-01..2024-11-06, continuous filing after, discharge-only (2025:
# +1.932 TWh, 0.000 pumping, min 0 MW). That the pre-split `NG: WAT` carries
# the PS block is measured four independent ways: (i) it exceeds NEISO's OWN
# 1,926.3 MW conventional (`HY`) EIA-860 nameplate 63-276 h/yr in 2019-2024
# and 0 h in 2025, the first fully-split year; (ii) scale-free shape
# fingerprints match the post-split WAT+PS reference (diurnal swing 2.89x,
# 19/1000 h above nameplate), not the clean WAT reference (1.48x, 0/1000 h) —
# pre-split windows run 2.20-2.70x and 13-38/1000 h; (iii) a two-component
# diurnal decomposition (self-validated: recovers 0 / 218 MW on the windows
# whose answers are known, true 0 / 219) fits 154-263 MW of PS in every
# pre-split window, 1.35-2.30 TWh/yr against the 1.932 measured post-split;
# (iv) the seam falls INSIDE November 2024 — Nov 1-6 vs Nov 7-30 collapses
# max 1,873 -> 685 MW and swing 7.11x -> 1.79x six days apart on the same
# water, while the SAME cut in the five no-seam years 2019-2023 moves only
# 0.77-1.03x. The 930-vs-923 LEVEL gap (+2.7 % / +10.1 % in 2023/2024) is far
# SMALLER than the fold because a second, opposite-signed discrepancy
# coexists: 930's BA telemetry under-counts the 173-plant 923 census by
# ~1.2-1.6 TWh/yr (Dec 2024, the one clean complete-census month, runs 8 %
# BELOW 923). Refusing the pin removes BOTH errors at once — which is why
# "930 minus an estimated PS" was refused: it recovers the telemetry subset
# (16.6 % / 19.1 % below the units' own complete-census filings) and would
# add an estimated 154-263 MW free parameter with no forward story (from 2025
# the split is filed; rules 5/13/14). NEISO's pumped storage itself is
# untouched by this guard: it is endogenous storage
# (model/storage.py::load_eia860_pumped_storage, 1,865.0 MW), so the
# pre-split pin was double-representing its discharge.
# Membership is measured, never assumed. Re-derive only when the source data
# changes (a 930 vintage that back-fills `NG: PS`, or another BA splitting
# mid-series — re-run the probe pattern). Rule 23 [R-FROZEN-DERIVE].
# Source: EIA-930 hourly per-BA extract (ISNE); EIA-923 monthly generation;
# EIA-860.
#
# SOCO (SOCO-59, 2026-09-22, every number from SOCO's own data — rule 25;
# probe scripts/probes/_soco59_phase0.py pssplit): EIA-930 publishes SOCO's
# hydro as the combined "Hydropower and Pumped Storage" column until the
# 2024-07-15 taxonomy cut-over, then files `NG: PS` for 24 hours and stops
# until 2025-01-06 01:00 (soco-data-audit §3.3), continuous after — so 2025 is
# the first wholly-split year. soco-data-audit §3.3 found the pre-split column
# never goes negative (min +32 MW) and read that as PS "not reported at all";
# that rules out folded PUMPING only. DISCHARGE is folded, measured three ways
# (the neiso-72 tests, NEISO's fold was discharge-only too): (i) the pre-split
# column exceeds SOCO's OWN 3,317.6 MW conventional-hydro EIA-860 nameplate
# (summer 3,296.8) in 6 / 29 / 6 h of 2021 / 2022 / 2023 (max 3,873 MW) and in
# 0 h of 2025's clean column; (ii) its diurnal swing (hourly-mean max/min)
# runs 2.84 / 3.12 / 3.82x, matching 2025's clean hydro PLUS measured PS
# discharge (3.77x), not 2025's clean hydro alone (2.13x); (iii) the 2023 gap
# between the column (8.446 TWh) and the 42-plant EIA-923 HY census the LP
# units carry (6.815) is 1.63 TWh, against 1.963 TWh of PS gross discharge
# measured in 2025. SOCO's pumped storage is endogenous storage
# (model/storage.py::load_eia860_pumped_storage, 1,306.6 MW), so a pre-split
# pin would double-represent its discharge exactly as NEISO's did.
EIA930_PS_SPLIT_COMPLETE_FROM: dict[str, int] = {"NEISO": 2025, "SOCO": 2025}

# --- EIA-930 published sign-inverted ``Total interchange`` windows ----------
# Per EIA-930 BA code: the inclusive ``(first, last)`` ``UTC time`` stamps of
# the extract's own clock inside which the PUBLISHED ``Total interchange``
# column carries the WRONG SIGN. Inside a window the column is negated at the
# frame-construction seam (``data.eia930.frames._repair_inverted_interchange``)
# so every reader — the served net-interchange schedule, the demand balance
# screen (``S = NG - TI``) and the hourly interchange benchmark — sees EIA's
# own sign convention (positive = net export). The raw extract is never
# modified (data/raw is immutable). Zero free parameters: the window edges are
# where the published identity flips, measured hour by hour (rule 21 / 24).
# Rule 14 [R-ACCURATE] source repair — the identity ``TI = NG - D`` and the
# independent BA-to-BA book both give the correct sign; the column is kept
# and reconciled, never replaced by an estimate.
#
# SOCO (lane R-SOCO-B, 2026-09-25, owner ruling (A) "Yes" — repair, do not
# touch the raw file; I-SOCO intake FINDING §4.1). Measured on
# ``data/raw/eia-930-hourly/SOCO hourly.parquet`` over local-year 2019
# (8,760 rows, UTC 2019-01-01 07:00 .. 2020-01-01 06:00): in EVERY one of the
# 6,071 hours from the first row through UTC 2019-09-11 05:00,
# ``Total interchange == -(Net generation - Demand)`` within 1 MW, and no hour
# there agrees with the correct sign alone (2 hours sit within 1 MW of zero
# and satisfy both); from UTC 2019-09-11 06:00 on, 2,664 of the 2,689 hours
# satisfy ``TI == NG - D`` (the other 25 are NaN) and none is inverted. The
# nine-DIBA BA-to-BA book (``eia-930-interchange/SOCO interchange
# hourly.parquet``) corroborates: inside the window corr(TI, sum of legs) =
# -1.0000 with median |TI + legs| = 0 MW (TI -4.114 TWh vs legs +4.114 TWh);
# after it median |TI - legs| = 0 MW. EIA's live BALANCE file carries the
# same inversion (FINDING-i-soco §4.1), so it is the publisher's. The window
# opens at the extract's first 2019 row because the corpus holds no earlier
# SOCO hour; nothing before it is asserted. Re-derive only when the source
# extract changes (rule 23 [R-FROZEN-DERIVE]).
EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC: dict[str, tuple[tuple[str, str], ...]] = {
    "SOCO": (("2019-01-01 07:00", "2019-09-11 05:00"),)
}

# --- ISO plant membership: drop plants the current EIA-860 recodes elsewhere --
# ``run_calibration_full._iso_plant_ids`` is the single membership seam the
# EIA-923 benchmark frame, its class shares and the must-run (biomass / OTHER)
# injection all read. Its base is eGRID 2023 ``BACODE``. For an ISO listed
# True here, plants that the CURRENT EIA-860 plant file codes to a DIFFERENT
# balancing authority are removed from it (a plant absent from the current file,
# or carrying no BA code, stays). Per-ISO (rule 25); zero free parameters — a
# partition on one published field (rules 21 / 24).
#
# SOCO (lane SOCO-60, 2026-09-23; probe scripts/probes/_soco60b_phase0.py ba —
# every number from SOCO's own data). eGRID 2023 and EIA-860 vintages
# 2018-2023 code the former Gulf Power plants — Lansing Smith 643 (CC),
# Gulf Clean Energy Center 641 (ST / CT), Pea Ridge 7715, Perdido 57502 and
# three Gulf solar plants — to SOCO; EIA-860 vintage 2024 recodes all of them
# to FPL. EIA-930's SOCO series has EXCLUDED them all along: 930 SOCO gas+coal
# against SOCO's 923 fossil WITHOUT them reads 0.997 / 1.008 / 1.004 / 1.006 /
# 1.002 / 0.981 in 2019-2024, and WITH them 0.962 / 0.971 / 0.968 / 0.973 /
# 0.965 / 0.943 (they carry 6.06-6.85 TWh/yr). The model's own SOCO fleet
# census is EIA-860 ``BA == "SOCO"`` at the current vintage (soco-data-audit §1
# row 1) and carries none of them, and SOCO's demand is the EIA-930 SOCO series.
# Left in, the benchmark scored 3.97 TWh (2024) of Lansing Smith as SOCO
# CC_REGULAR, and the combined fossil reconcile then removed the surplus by
# scaling EVERY SOCO fossil class down (x0.918 in 2024) — coal included, where
# EIA-930 and EIA-923 agree to 0.7 %. Rule 14 [R-ACCURATE]'s misalignment case:
# the real data is kept and reconciled to the model's boundary at plant grain.
# Solve-affecting only through the injection (Perdido landfill gas,
# 0.014 TWh/yr of biomass).
ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE: dict[str, bool] = {"SOCO": True}
# EXTENDED 2026-09-25 (lane R-SOCO-B): the same partition now also applies to
# the LP FLEET (``data.ba_membership.drop_current_ba_recoded_rows`` at the
# operable, retiree and mothball loaders), so benchmark, injection and fleet
# read ONE membership rule (rule 19 [R-ONE-MECH]). With
# ``eia860_vintage_tracks_solve_year`` on, vintages 2019-2023 code the former
# Gulf Power plants to SOCO, so the vintage fleet carried them although
# EIA-930's SOCO demand never included them — measured on the R-SOCO keeper
# recipe, 2,525 MW in 2023 (Crist 641 1,858 MW ST_GAS/CT, Lansing Smith 643
# 652 MW CC, Pea Ridge 7715 12 MW, Perdido 57502 3 MW) and 641 as 924 MW of
# COAL + 643 in 2019. Vintage 2024 and the canonical snapshot already code
# them FPL, so 2024/2025 are unchanged by construction.
# CORRECTED 2026-09-25 (lane R-SOCO-B2, owner ruling (C)): "EIA-930's SOCO
# demand never included them" is FALSE before hour-ending UTC 2022-07-13 12:00
# — Gulf's load and plants were inside SOCO's EIA-930 BA until then. The drop
# is therefore DATED by ``ISO_BA_EXITS`` below: it applies from that hour on
# (2023+ all year, 2022 from the stamp) and not before.

# --- Balancing authorities that JOINED a modelled region mid-backcast --------
# ``{iso: {joining_ba: (year, month)}}``: the EIA-930 BA code whose load and
# plants joined ``iso``'s balancing authority on the first day of ``month`` of
# ``year``. Read by ``data.ba_membership`` at three seams so supply and the
# measured load stay on one boundary (rule 19 [R-ONE-MECH]):
#   * LP fleet — in the join year the join-year EIA-860 vintage still codes the
#     plants to the joining BA; they are admitted and masked offline before the
#     join month (the COD-ramp month mask); before the join year they are not
#     admitted (the vintages code them to the joining BA and its load is outside
#     the ISO's EIA-930 demand); after it the vintages code them to ``iso``;
#   * EIA-923 benchmark (and the must-run injection that reads it) — the
#     eGRID-2023 membership base codes them to ``iso`` in every year, so they
#     are excluded before the join year and their months before the join month
#     are zeroed in the join year.
# The joining BA is deliberately NOT registered in ``BA_CODE_TO_ISO`` (that
# would leak it into zone lookup, eGRID, retirees and demand pools for every
# year). Zero free parameters: the date is the publisher's own record (rules
# 21 / 24); per-ISO (rule 25).
#
# SOCO (lane R-SOCO-B, 2026-09-25, owner ruling (B) "Yes"): PowerSouth Energy
# Cooperative (EIA-930 BA ``AEC``) joined the Southern Company BA on
# 2021-09-01. Measured: the SOCO<->AEC interchange leg in
# ``eia-930-interchange/SOCO interchange hourly.parquet`` runs 2019-01-01 ..
# 2021-09-01 00:00 and stops; EIA-860 vintages 2019-2021 code PowerSouth's
# plants {53, 55, 56, 533, 6192, 7063, 56522, 64469} ``AEC`` and vintages
# 2022+ code them ``SOCO`` (FINDING-i-soco-2019-2022-intake §4.2). Vintage
# 2021's operable PowerSouth generators — McWilliams 533 (653 MW CT/CA),
# McIntosh 7063 (676 MW GT/CE), Gantt 53 / Point A 55 hydro (8.2 MW),
# Springhill 56522 LFG (4.8 MW) — are appended to that vintage's processed
# table by ``scripts/data/process_eia860.py --rescope-from-parquet
# data/raw/eia-860/vintage_2021 --admit-ba AEC``.
ISO_BA_JOINS: dict[str, dict[str, tuple[int, int]]] = {"SOCO": {"AEC": (2021, 9)}}

# --- Balancing authorities that plants/load LEFT a modelled region to ---------
# ``{iso: {destination_ba: first_hour_outside}}`` — the twin of
# ``ISO_BA_JOINS`` for an EXIT. The plants that leave are exactly those the
# ``ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE`` partition selects whose CURRENT
# EIA-860 BA code is ``destination_ba``; that partition is now DATED: before
# the exit they are members (their load was inside ``iso``'s EIA-930 demand).
# ``first_hour_outside`` is the first row OUTSIDE the region, written as the
# region's EIA-930 extract's own hour-ending ``UTC time`` stamp (the same clock
# convention as ``EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC``). Hour grain
# (owner ruling (C), 2026-09-25, "Hour grain"): the LP fleet masks the exit
# year's rows at and after the stamp; the monthly EIA-923 benchmark keeps the
# split month's share measured by the plants' own CAMPD gross load before the
# stamp (hour share of the month for a plant CAMPD does not carry). Read ONLY
# by ``data.ba_membership`` (rule 19 [R-ONE-MECH]); zero free parameters, the
# stamp is measured (rules 21 / 24); per-ISO (rule 25).
#
# SOCO (lane R-SOCO-B2, 2026-09-25, owner ruling (C) "(C) dated exit"): the
# former Gulf Power plants (Crist 641, Lansing Smith 643, Pea Ridge 7715,
# Standby 50310, Santa Rosa 55242, Perdido 57502, and three solar plants) and
# Gulf's load left the Southern Company BA for FPL's at hour-ending UTC
# 2022-07-13 12:00. Measured three independent ways
# (docs/handoffs/r-soco/FINDING-r-soco-b2-boundary-2026-09-25.md, reproduced by
# scripts/probes/_rsocob2_gulf_exit.py): (1) SOCO 930 demand minus the five
# SOCO-footprint FERC-714 respondents steps down ~1,700 MW (= Gulf Power's own
# FERC-714 load) on 2022-07-13 while FPL's 930 demand steps up; (2) Gulf Power
# (FERC-714 respondent 185) files its last hour at 2022-07-13 10:00 UTC
# hour-beginning; (3) an hourly least-squares fit of SOCO 930 fossil net
# generation on CAMPD gross load loads the Gulf units at 0.83-0.89 in every
# period before the stamp and 0.014 after. Restoring them for the in-BA period
# closes the SOCO-60 B1/B2 checks (930/923 fossil 0.982 / 0.991 / 0.982 / 0.985
# for 2019-2022). Re-derive only when a source changes (rule 23).
ISO_BA_EXITS: dict[str, dict[str, str]] = {"SOCO": {"FPL": "2022-07-13 12:00"}}

# --- Hydro hourly deliverability envelope (caiso-72 STEP-2) ------------------
# Percentile of the measured EIA-930 NG:WAT hourly output, per (month x
# hour-of-day) bucket, used as the hydro fleet's hourly dispatch ceiling when
# ScenarioConfig.hydro_dispatch_envelope is on. Same construction and same
# admissibility class as the CAISO corridor ATC envelope
# (interchange_config.CAISO_CORRIDOR_FLOW_PERCENTILE, also 95): a measured
# *capability* ceiling the LP clears below — head/flow/scheduling limits that
# the nameplate pmax bound ignores — never a flow pinned to the residual.
# Identification: measured (rule 23 — re-derive only when the EIA-930 source
# extends). Source: EIA-930 hourly NG:WAT per BA extract.
HYDRO_ENVELOPE_PERCENTILE: float = 95.0

# --- Hydro minimum-flow floor (caiso-124) ------------------------------------
# The LOWER half of the same measured two-sided hydro capability envelope: the
# percentile of the measured EIA-930 NG:WAT hourly output, per CALENDAR MONTH,
# used as the hydro fleet's sustained minimum-flow level when
# ScenarioConfig.hydro_min_flow_floor is on. Two properties are load-bearing:
#   * It is the exact MIRROR of HYDRO_ENVELOPE_PERCENTILE (95 -> 5), so the
#     floor adds NO new free parameter — the two-sided envelope is identified by
#     the one percentile the ceiling already carries (DOF ledger: 0 new DOF).
#     Read as an exceedance level it is Q95, the standard hydrological low-flow
#     index that environmental / FERC-license minimum-flow conditions are
#     themselves written against (the level the fleet exceeds 95 % of the hours).
#   * The bucket is the MONTH ALONE — deliberately NOT (month x hour-of-day) as
#     the ceiling's is. A floor carrying the measured diurnal shape would pin
#     dispatch to the measured outcome (rule 13 violation, and it measures out
#     at ~75 % of the annual budget); a month-constant level is the physical
#     quantity a minimum-flow condition actually is (inflow / licence releases
#     vary seasonally, not by hour-of-day) and leaves the LP free to choose WHEN
#     to generate above it (CAISO 2023-25: the floor's energy is 36-46 % of the
#     monthly budget, so 54-64 % stays economically shaped).
# Identification: measured (rule 21 — re-derive only when the EIA-930 source
# extends, never against a residual). Source: EIA-930 hourly NG:WAT per BA
# extract; built by data.eia_loader.measured_hydro_min_flow_level.
HYDRO_MIN_FLOW_PERCENTILE: float = 100.0 - HYDRO_ENVELOPE_PERCENTILE

# --- Hydro budget period, from the project's own governing instrument --------
# (nyiso-220; charter docs/CHARTER-nyiso219-hydro-budget-period-2026-09-07.md;
#  evidence docs/FINDING-nyiso220-hydro-instrument-and-operating-ranges-2026-09-08.md)
#
# The LP's hydro row conserves energy over a PERIOD, and that period defaults to
# the calendar month — so a plant may bank energy across ~730 hours at zero cost.
# For some projects that is contradicted by the instrument that actually governs
# their water. This registry names, per ISO and EIA plant id, the period in HOURS
# over which the project's OWN governing instrument (or its measured pondage)
# permits energy to be reallocated. A plant absent from the registry keeps the
# monthly period, i.e. this is a strict, opt-in refinement of existing behaviour.
#
# ZERO FITTED SCALARS, and no value here is selected by, or swept against, any
# residual (rule 21 [R-DOF] case 3, rule 1 [R-STRUCT]). Each entry's basis:
#
#   NYISO 2694  Robert Moses St. Lawrence -> 168 h (one week)
#     Stated IN WORDS by the governing instrument, so nothing is converted or
#     assumed. The project's outflow is set by the IJC's 2016-12-08 Supplementary
#     Order of Approval under Regulation Plan 2014, "normally as specified by the
#     approved WEEKLY flow regulation plan"; within-week variation is authorised
#     by the Commission's directive on peaking and ponding (conditions in
#     Addendum No. 3 to the Operational Guides for Plan 1958-D; IJC letter
#     1983-10-13, renewed 2016-11-04 and 2021-11-30 for 2021-12-01..2026-11-30,
#     a term spanning every scored year). The ILOSLRB glossary defines "Ponding"
#     as "variation in the day-to-day flows over the course of a week", and its
#     reports state that ponding holds "the total weekly flow the same". This is
#     a PUBLISHED CATEGORICAL DURATION CLASS — rule 21 [R-DOF] case 2 — and it is
#     NYISO's own project's own instrument, never NEISO's HDP/HDR/HW taxonomy
#     (rule 25 [R-ISO-SCOPE]).
#
#   NYISO 2693  Robert Moses Niagara -> 24 h (one day)
#     DERIVED, not chosen, and the derivation is two-sided. Its instruments — the
#     1950 Niagara Diversion Treaty and the INBC 1993 Directive (rev. 2017) over
#     the Chippawa-Grass Island Pool — state NO energy or volume conservation
#     period at all (verified mechanically: the full treaty text contains zero
#     occurrences of elevation, reservoir, storage, pondage, forebay, pool,
#     monthly, weekly, accounting or average). What the plant physically has is
#     0.244 h of forebay pondage (nyiso-219, NID; a generous upper bound at
#     efficiency 1.0 on full volume), so water not diverted goes over the Falls
#     and is gone — USE IT OR LOSE IT. The granularity then follows uniquely:
#       * a 1-hour period would fix P[g,t] exactly and destroy the plant's REAL
#         diurnal variation, which the treaty itself imposes (Art. IV requires
#         100,000 cfs over the Falls in tourist-season daytime hours vs 50,000
#         cfs otherwise, so divertible water swings by ~1,416 m3/s system-wide
#         against NYPA's measured 2,183 m3/s average diversion);
#       * a 24-hour period removes exactly what the pondage forbids — banking
#         across days — while leaving the within-day shape free, which is the
#         dimension the reconciled hydro_dispatch_envelope already governs
#         (rule 19 [R-ONE-MECH]: disjoint declared windows, never stacking).
#     So 24 h is the unique granularity consistent with both the physics and the
#     treaty, given that within-day shaping must be preserved.
#
# The 161 remaining NYISO hydro plants are on domestic rivers whose operating
# bands live in unretrieved FERC licence articles, so they are DELIBERATELY
# ABSENT and keep the monthly period: rule 14 [R-ACCURATE] — do not invent an
# instrument we have not read.
#
# Identification: published governing instruments (rule 23 [R-FROZEN-DERIVE] —
# re-derive only when the instrument itself is reissued, never against a
# residual). Consumed by data.hydro.hydro_budget_period_hours when
# ScenarioConfig.hydro_budget_period_by_instrument is on.
HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT: dict[str, dict[int, int]] = {
    "NYISO": {
        2693: 24,  # Robert Moses Niagara — treaty/INBC state no period; 0.244 h pondage
        2694: 168,  # Robert Moses St. Lawrence — IJC ponding directive, stated in words
    },
}

# --- Plant -> NID impoundment cross-references HILARRI does not carry --------
# Consumed by scripts/data/build_hydro_pondage.py, the derive behind
# ScenarioConfig.hydro_pondage_bound. Each entry is a LINKAGE — "this
# published impoundment belongs to this plant" — never a numeric parameter:
# the volume and head come from NID itself, so no free parameter is added
# (rules 5 [R-NO-MAGIC] / 21 [R-DOF]). Frozen under rule 23
# [R-FROZEN-DERIVE]: an entry is added only when a linkage is established
# from a published source, never because a residual moved.
#
# NYISO 2693 Robert Moses Niagara -> NY00689 (Lewiston Pump Generating Plant /
#   Lewiston Reservoir Dike; NYPA; NID Max Storage 76,000 acre-ft; Hydraulic
#   Height 119 ft; completed 1963, the same year as the Robert Moses
#   powerhouse). HILARRI links plant 2693 only to NY16253, the 71-acre / 5,350
#   acre-ft forebay at the powerhouse — which is why nyiso-219 measured
#   Niagara's pondage at 0.244 h (about fifteen minutes) from a plant that
#   supplies most of a fleet whose MEASURED mean diurnal swing is 1,195-1,593
#   MW (nyiso-111). Those two facts cannot both describe the same machine, and
#   the resolution is that the Niagara Project's shaping store is the LEWISTON
#   RESERVOIR, not the forebay: NYPA lifts diverted Niagara River water into it
#   overnight, when the 1950 treaty and the IJC diversion schedule allow more
#   water to be taken than the load needs, and draws it back down on peak. The
#   240 MW Lewiston pump-turbines (EIA plant 2692, prime mover PS, modelled
#   separately as storage) cannot themselves account for the swing — the stored
#   water returns to the forebay and is generated through the 2,429 MW Robert
#   Moses conventional units, which is why the volume belongs to 2693. With it,
#   Niagara holds ~3.8 h against a 730-hour LP budget period; without it,
#   0.244 h, which the measured swing falsifies.
#   Source: USACE National Inventory of Dams, dam NY00689 (national CSV export,
#   vintage 2026-09-11). Cross-checked against the NYISO subset committed at
#   data/raw/nid/, which carries NY16253 but not NY00689.
HYDRO_PONDAGE_EXTRA_NID_BY_PLANT: dict[str, dict[int, tuple[str, ...]]] = {
    "NYISO": {2693: ("NY00689",)},
}

# Hydro-year scenario lever: a multiplier on the normal-water-year hydro budget
# selected by ScenarioConfig.hydro_year, the forecast wet/dry-water-year knob.
# A wet or dry water year shifts annual conventional-hydro energy by roughly
# ±15% about the normal-year mean: the EIA-930 NG:WAT 2021-2025 annual totals
# span ~0.73-1.30 of their mean across the modeled ISOs — widest in the small
# run-of-river systems (NEISO, ERCOT) and ~±5-10% in the large reservoir
# systems (CAISO, NYISO) — so ±15% brackets the central reservoir-system range.
# A round, documented scenario assumption (not a value fitted to any residual);
# "normal" = 1.0 leaves the climatology unscaled. Applied as a pure level scale
# by data.hydro.forecast_monthly_hydro — the within-month dispatch mechanism is
# untouched.
HYDRO_YEAR_MULTIPLIER: dict[str, float] = {
    "dry": 0.85,
    "normal": 1.0,
    "wet": 1.15,
}

# Nuclear monthly capacity factors (12 values, Jan–Dec) by ISO.
# Spring and fall dips reflect scheduled refueling outages.
# Source: NRC PRIS 2019-2023.
NUCLEAR_MONTHLY_CF: dict[str, list[float]] = {
    # Spring (Mar-May) and fall (Oct) dips reflect ERCOT refueling-outage
    # windows; the deep April / October troughs match the observed EIA-930
    # nuclear monthly shape for Comanche Peak and South Texas.
    # Tier: 3 (calibration)
    "ERCOT": [0.97, 0.99, 0.89, 0.78, 0.84, 0.93, 0.95, 0.96, 0.95, 0.72, 0.83, 0.99],
    "CAISO": [1.00, 0.99, 0.96, 0.95, 0.97, 1.00, 1.00, 1.00, 0.98, 0.95, 0.97, 1.00],
    "PJM": [1.00, 1.00, 0.95, 0.94, 0.97, 1.00, 1.00, 1.00, 0.97, 0.95, 0.98, 1.00],
    "NYISO": [1.00, 1.00, 0.95, 0.94, 0.97, 1.00, 1.00, 1.00, 0.97, 0.95, 0.98, 1.00],
    "NEISO": [1.00, 0.99, 0.95, 0.95, 0.98, 1.00, 1.00, 1.00, 0.97, 0.96, 0.98, 1.00],
    # MISO = 10-plant / 13-unit nuclear fleet (Clinton, Fermi, Monticello,
    # Prairie Island, Point Beach, Waterford 3, Grand Gulf, Callaway, River
    # Bend, Arkansas Nuclear One), 11,519 MW. Forecast-fallback seasonal
    # pattern = the 3-year mean of the EIA-923-derived per-year CF below;
    # spring/fall dips are the staggered refueling cadence across the fleet.
    "MISO": [0.93, 0.92, 0.85, 0.82, 0.78, 0.91, 0.98, 0.98, 0.93, 0.79, 0.84, 0.89],
    # SPP = the two-unit fleet Wolf Creek 1 (EIA 210, KS, 1,296.3 MW) + Cooper
    # (EIA 8036, NE, 801.0 MW), 2,097.3 MW nameplate. Forecast-fallback
    # seasonal pattern = the 3-year mean of the EIA-923-derived per-year CF
    # below (the MISO construction); the April and October troughs are the two
    # units' staggered ~18-month refueling cadence (Wolf Creek spring 2024 /
    # fall 2025, Cooper fall 2024). Registered 2026-09-06 (SPP-20).
    "SPP": [1.00, 1.00, 0.98, 0.79, 0.93, 1.00, 1.00, 0.96, 0.98, 0.66, 0.89, 1.00],
    # NWPP: the month-wise mean of the three NUCLEAR_MONTHLY_CF_BY_YEAR["NWPP"]
    # vectors below (Columbia Generating Station, plant 371, the footprint's
    # ONE reactor, 1,151 MW summer). The April-June trough is Columbia's
    # BIENNIAL refuelling (deep outages May-Jun 2023 and Apr-Jun 2025, none
    # in 2024 — audit §7 row 10), which a three-year mean halves rather than
    # reproduces; the by-year table below is what a backcast reads. Registered
    # 2026-09-14 (NWPP-20).
    "NWPP": [0.99, 1.00, 0.95, 0.70, 0.37, 0.47, 0.97, 0.98, 0.98, 0.99, 0.99, 0.97],
    # SOCO = the three-plant / eight-unit Southern Nuclear fleet — Farley 1-2
    # (EIA 6001, AL), Hatch 1-2 (6051, GA), Vogtle 1-4 (649, GA) — 8,282.4 MW
    # nameplate (8,080 MW net summer, the model pmax), with Vogtle 3 (2023-07)
    # and Vogtle 4 (2024-04) commissioning INSIDE the backcast window.
    # Forecast-fallback seasonal pattern = the 3-year mean of the EIA-923-
    # derived per-year CF below (the MISO/SPP construction). The Feb-Mar and
    # Sep-Oct dips are the staggered refuelling cadence (Hatch each Feb-Mar,
    # Farley Apr-Jun 2025; docs/multi-iso/soco-data-audit.md §5 row 8).
    # Registered 2026-09-14 (SOCO-20).
    "SOCO": [0.99, 0.89, 0.83, 0.89, 0.91, 0.94, 0.93, 0.98, 0.84, 0.89, 0.92, 0.98],
}

# Dormant nuclear plants the EIA-860 operable schedule lists as OP that have
# not yet returned to service: plant code -> first calendar year the unit is
# expected to generate. Backcast years before that year zero the unit's
# availability (it is physically offline, EIA-923 net generation = 0), and
# scripts/data/derive_nuclear_monthly_cf.py excludes it from the fleet pmax for
# those years so the derived CF is not diluted. Forecast runs are unaffected
# (the unit stays in the fleet at its EIA-860 capacity).
#   8011 — Crane Clean Energy Center (ex-TMI-1, 802.8 MW net summer): shut
#   2019, restart announced Sep 2024 (Constellation/Microsoft PPA) with grid
#   return targeted 2027 (EIA-860 2025ER carries it as OP with a planned 2028
#   repower year). Zero EIA-923 net generation 2023-2025; without this entry
#   the PJM backcast carried ~6.5 TWh/yr of phantom nuclear.
# Tier: 3 (calibration)
NUCLEAR_DORMANT_UNTIL: dict[int, int] = {
    8011: 2027,
}

# ERCOT's PUBLISHED ORDC price-formation order parameters, by year — the
# system-wide offer cap (HCAP, which IS the ORDC's VOLL anchor) and the minimum
# contingency level X (the reserve level at which LOLP is administratively 1.0
# and the adder pins to VOLL - lambda). BOTH ARE PUCT ORDER VALUES, not model
# parameters: they change on an order's effective date and nothing else.
#
#   through 2021 : HCAP $9,000/MWh, MCL 2,000 MW
#   from 2022-01-01: HCAP $5,000/MWh (16 TAC 25.509, PUCT Project 52631),
#                    MCL 3,000 MW (OBDRR038, PUCT Project 52373 blueprint order)
#
# WHY THE TABLE EXISTS (ercot-253, owner ruling 2026-09-06 on the 2021
# validation rung). ``ScenarioConfig.ordc_voll`` / ``ordc_mcl_mw`` ship at the
# POST-order values, and their own comments already say the pre-Uri values were
# $9,000 / 2,000 MW — so a pre-2022 backcast was solving the right market on the
# wrong published cap, and structurally could not reach that year's price level.
# Rule 14 [R-ACCURATE]: this is the accurate measured market-design input, and
# an estimate (or the wrong vintage) is not kept because it is convenient.
# Rule 21 [R-DOF]: ZERO free parameters — every value is a published order
# figure, fixed before any solve, and no year's value is selectable by a result.
#
# EXPLICIT PER YEAR, never extrapolated: a year absent from the table falls
# through to the ``ScenarioConfig`` default, which is the current post-order
# value and so is correct for every forecast year. 2022-2025 are listed at
# exactly those defaults, which is what makes every training-year and 2022-rung
# solve BYTE-IDENTICAL under this table.
# Tier: 1 (published market design)
ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR: dict[int, dict[str, float]] = {
    2019: {"ordc_voll": 9000.0, "ordc_mcl_mw": 2000.0},
    2020: {"ordc_voll": 9000.0, "ordc_mcl_mw": 2000.0},
    2021: {"ordc_voll": 9000.0, "ordc_mcl_mw": 2000.0},
    2022: {"ordc_voll": 5000.0, "ordc_mcl_mw": 3000.0},
    2023: {"ordc_voll": 5000.0, "ordc_mcl_mw": 3000.0},
    2024: {"ordc_voll": 5000.0, "ordc_mcl_mw": 3000.0},
    2025: {"ordc_voll": 5000.0, "ordc_mcl_mw": 3000.0},
}

# Per-year nuclear monthly capacity factor derived from EIA-923 net generation
# (the actual staggered refueling cadence each year, not a fixed seasonal
# average). When a (ISO, year) is present it overrides NUCLEAR_MONTHLY_CF in the
# backcast; forecast years fall back to NUCLEAR_MONTHLY_CF or the universal
# refueling-block forecaster. ERCOT = Comanche Peak (2) + South Texas (2).
# Derivation: scripts/data/derive_nuclear_monthly_cf.py (CF = fleet EIA-923 monthly
# net gen / fleet pmax x hours, capped at 1.0 — winter net capability slightly
# exceeds EIA-860 nameplate, so the cap costs ~0.7%/yr vs measured energy);
# re-run with --check after an EIA-923 refresh.
# Tier: 3 (calibration)
NUCLEAR_MONTHLY_CF_BY_YEAR: dict[str, dict[int, list[float]]] = {
    "ERCOT": {
        # 2021 derived 2026-09-06 (ercot-253, same script/source; the 2022 and
        # 2023 rows re-derived byte-identically in the same run as the producer
        # re-proof) for the rule-22 validation ladder. Feb 2021 reads 0.99: the
        # Uri STP-1 trip is a ~4-day event, and its TIMING is carried by the
        # measured daily nuclear-availability windows, not by a monthly level.
        2021: [1.00, 0.99, 0.91, 0.83, 1.00, 0.86, 0.99, 1.00, 1.00, 0.59, 0.83, 1.00],
        # 2022 derived 2026-09-05 (same script, same EIA-923 source; 2023 row
        # re-derived identically in the same run) for the rule-22 validation touchpoint.
        2022: [1.00, 1.00, 1.00, 0.85, 0.87, 1.00, 1.00, 1.00, 0.93, 0.79, 0.91, 1.00],
        2023: [1.00, 1.00, 0.89, 0.75, 0.78, 0.95, 0.99, 0.99, 0.99, 0.87, 0.91, 1.00],
        2024: [0.93, 1.00, 0.82, 0.74, 0.78, 0.98, 0.92, 0.97, 0.99, 0.68, 0.75, 1.00],
        2025: [0.97, 1.00, 1.00, 0.92, 0.89, 1.00, 1.00, 0.99, 0.94, 0.76, 0.91, 1.00],
    },
    # CAISO = Diablo Canyon units 1+2 (EIA plant 6099, fleet nameplate
    # 2,240 MW). Monthly EIA-923 net generation / (nameplate x hours in
    # month), clipped at 1.0 — the ERCOT convention. The dips are the actual
    # staggered ~18-month refueling cadence: U2 down Oct-Dec 2023, U1 down
    # Apr-May 2024, U1 Apr-May 2025 and U2 Oct 2025.
    # Source: EIA-923 Page 1 monthly net generation, 2023-2025 final.
    "CAISO": {
        # 2022 ADDED 2026-09-07 (caiso-262, the rule-22 validation touchpoint):
        # same producer, same source, same recipe as the rows below —
        # `derive_nuclear_monthly_cf.py --isos CAISO --years 2022` over EIA-923
        # Page 1 monthly net generation. The 2023-2025 rows were re-derived in
        # the SAME run as the producer re-proof (`--check`) and came back
        # byte-identical, so no existing year's values moved. The Apr 0.54 /
        # Oct 0.73 / Nov 0.58 dips are Diablo Canyon's 2022 refuelling outages
        # (the two units refuel on alternating spring/fall cycles), which is
        # the level anchor a 2022 rung would otherwise smear into the static
        # seasonal pattern.
        # 2019-2021 ADDED 2026-09-24 (i-caiso, the 2019-2021 intake): same
        # producer, same source, same recipe — `derive_nuclear_monthly_cf.py
        # --isos CAISO --years 2019 2020 2021`; `--years 2022 2023 2024 2025
        # --check` passed in the same session, so no existing year's values
        # moved. The dips are Diablo Canyon's refuelling outages (fall 2019,
        # fall 2020, spring 2021), measured rather than smeared into a static
        # seasonal CF.
        2019: [1.00, 0.66, 0.68, 0.96, 1.00, 1.00, 1.00, 1.00, 0.85, 0.50, 0.50, 0.67],
        2020: [1.00, 0.95, 1.00, 1.00, 0.96, 1.00, 0.77, 0.96, 0.99, 0.26, 0.49, 0.51],
        2021: [0.77, 0.53, 0.50, 0.57, 1.00, 1.00, 1.00, 1.00, 1.00, 0.72, 0.90, 1.00],
        2022: [0.99, 0.98, 0.88, 0.54, 1.00, 1.00, 1.00, 1.00, 1.00, 0.73, 0.58, 1.00],
        2023: [0.96, 1.00, 0.92, 1.00, 1.00, 1.00, 1.00, 0.99, 0.96, 0.47, 0.66, 0.83],
        2024: [1.00, 1.00, 1.00, 0.60, 0.62, 1.00, 1.00, 0.99, 0.94, 0.98, 1.00, 1.00],
        2025: [1.00, 1.00, 0.95, 0.71, 0.69, 1.00, 1.00, 0.90, 1.00, 0.57, 0.92, 0.97],
    },
    # PJM = the 18-plant EIA-860 operable nuclear fleet (Dresden, Quad Cities,
    # Salem, Peach Bottom, Surry, Cook, Calvert Cliffs, Perry, Braidwood,
    # Byron, LaSalle, Beaver Valley, Susquehanna, Limerick, Hope Creek, Davis
    # Besse, North Anna) — 32,689 MW after excluding the dormant Crane/TMI-1
    # restart (EIA 8011, 802.8 MW; NUCLEAR_DORMANT_UNTIL — zero EIA-923
    # output 2023-2025). Monthly EIA-923 net generation / (fleet pmax x hours
    # in month), clipped at 1.0 (ERCOT convention; the cap costs ~0.5-1.0
    # TWh/yr vs measured energy). Before this entry PJM fell back to the
    # static NUCLEAR_MONTHLY_CF seasonal pattern x (1 - EFORD), which (with
    # the phantom Crane capacity) over-produced a flat ~278 TWh vs measured
    # 272.6/272.4/270.0 — the systematic +4.5/+6.0/+8.0 TWh nuclear residual
    # of calibration runs 1-19.
    # Source: EIA-923 Page 1 monthly net generation, 2023-2025.
    # Derivation/verify: scripts/data/derive_nuclear_monthly_cf.py --isos PJM.
    "PJM": {
        2023: [1.00, 0.97, 0.90, 0.85, 0.91, 0.99, 0.99, 0.98, 0.96, 0.89, 0.96, 1.00],
        2024: [1.00, 0.98, 0.90, 0.81, 0.91, 0.99, 0.97, 0.99, 0.96, 0.90, 0.93, 1.00],
        2025: [1.00, 0.99, 0.88, 0.86, 0.91, 0.99, 0.98, 0.98, 0.94, 0.83, 0.93, 1.00],
    },
    # NYISO = FitzPatrick (EIA 6110, 844 MW), Nine Mile Point 1+2 (EIA 2589,
    # 1,903 MW combined), R E Ginna (EIA 6122, 579 MW) — fleet nameplate
    # 3,326 MW. Indian Point (EIA 8907) retired Apr 2021 and is absent from
    # the EIA-860 operable fleet. Monthly EIA-923 net generation / (fleet
    # nameplate x hours in month), clipped at 1.0 (ERCOT convention). The dips
    # are the actual staggered ~2-year refueling cadence, each verified to a
    # single reactor in the per-plant EIA-923 series:
    #   2023 Apr 0.74  — Ginna refuel (plant CF 0.28) + a Nine Mile unit (0.76).
    #   2024 Mar 0.69  — Nine Mile 2 refuel (plant CF 0.46).
    #   2024 Aug-Sep   — FitzPatrick refuel (0.63 / 0.37); Oct Ginna (0.48).
    #   2025           — only a mild Nine Mile dip (Mar 0.80); no deep refuel.
    # Source: EIA-923 Page 1 monthly net generation, 2023-2025 final.
    # Derivation/verify: scripts/data/derive_nuclear_monthly_cf.py --isos NYISO.
    # 2018-2022 added 2026-07-31 (NYISO out-of-training DATA READINESS, rule 22
    # Option-2 owner authorization) from the SAME producer and the same EIA-923
    # source, after `--check` proved the committed 2023-2025 block re-derives
    # exactly. Data-change citation per rule 23 [R-FROZEN-DERIVE]: these are new
    # YEARS of the measured series, not a re-tune of an existing one — every
    # committed 2023-2025 value is byte-unchanged.
    #   FLEET-VINTAGE CAVEAT RETIRED 2026-09-09 (session nyiso-fuelvintage-1,
    #   charter task 4 — docs/handoffs/fleet-vintage-retiree-window-charter-
    #   2026-08.md). It read: "A 2018-2021 solve is short that capacity
    #   regardless of this overlay." THAT IS NO LONGER TRUE. The charter's task
    #   2 moved RETIREMENT_WINDOW_START 2023 -> 2019 (commit 7934e92c), so
    #   load_retired_within_window now re-admits Indian Point 2 (plant 2497,
    #   retired 2020-04) and Indian Point 3 (plant 8907, retired 2021-04) —
    #   2,050.9 MW net summer of downstate nuclear — and the COD monthly online
    #   mask ages each out at its real retirement month. Measured at the loader:
    #   the NYISO injection is 45 generators / 4,187.6 MW against 14 / 491.9 MW
    #   before, i.e. 31 generators / 3,695.7 MW restored across 2019-2022. The
    #   CF overlays are INTENSIVE (a per-month capacity factor) and could never
    #   have restored missing capacity; the fleet channel is what did.
    #
    #   WHAT REMAINS TRUE, and is the successor caveat: this table is still
    #   DERIVED on the OPERABLE fleet only. derive_nuclear_monthly_cf.py builds
    #   its fleet from load_fleet_from_csv, which the retiree injection does not
    #   feed, so both numerator (EIA-923 net generation) and denominator (fleet
    #   pmax) remain the current 4-reactor upstate fleet — every committed value
    #   here is byte-unchanged by the window move, and `--check` still passes.
    #   But fleet/arrays.py applies the monthly CF UNIFORMLY to every nuclear
    #   row, so the restored Indian Point units are represented at the upstate
    #   fleet's measured monthly CF rather than at their own metered output
    #   (their PRESENCE and RETIREMENT TIMING are measured; their within-year
    #   SHAPE is the upstate fleet's). Whether to re-derive the CF over the
    #   injected fleet is a mechanism change to the derive's fleet definition,
    #   not a rule-23 [R-FROZEN-DERIVE] data refresh — the source data has not
    #   moved — so it is ROUTED to the charter rather than absorbed here.
    #   2026 is deliberately ABSENT: EIA-923 carries only Jan-Apr 2026 (zeros
    #   May onward), so a 2026 anchor would post a false zero for H1's May-Jun.
    "NYISO": {
        2018: [1.00, 1.00, 0.96, 0.80, 0.76, 0.96, 0.96, 0.90, 0.79, 0.86, 0.95, 1.00],
        2019: [1.00, 0.99, 0.89, 0.82, 0.96, 0.97, 0.98, 0.98, 1.00, 0.98, 1.00, 1.00],
        2020: [1.00, 0.90, 0.66, 0.79, 0.86, 0.99, 0.97, 0.96, 0.82, 0.95, 1.00, 1.00],
        2021: [1.00, 1.00, 0.94, 0.93, 1.00, 0.99, 1.00, 0.97, 0.99, 0.85, 0.99, 1.00],
        2022: [1.00, 0.95, 0.71, 0.94, 0.99, 0.98, 0.96, 0.93, 0.72, 0.85, 1.00, 1.00],
        2023: [1.00, 0.98, 0.86, 0.74, 0.99, 0.99, 0.96, 0.97, 0.88, 0.97, 0.99, 0.99],
        2024: [0.99, 0.99, 0.69, 1.00, 0.99, 0.98, 0.97, 0.89, 0.75, 0.90, 0.98, 0.98],
        2025: [0.98, 0.98, 0.89, 0.96, 1.00, 0.99, 0.97, 0.98, 0.98, 0.99, 0.97, 1.00],
    },
    # NEISO = Millstone units 2+3 (EIA 566, CT, 2,108 MW combined) + Seabrook
    # (EIA 6115, NH, 1,247 MW) — fleet nameplate 3,355 MW. Pilgrim (EIA 1590,
    # Plymouth MA) retired May 2019 and Vermont Yankee (EIA 7350) retired Dec
    # 2014; both are absent from the EIA-860 operable fleet. Monthly EIA-923
    # net generation / (fleet nameplate x hours in month), clipped at 1.0
    # (ERCOT convention). The dips are the actual staggered refueling cadence,
    # each verified to a single reactor going to ~0 in the per-plant EIA-923
    # series:
    #   2023 Apr 0.41 — Seabrook refuel (plant CF 0.00) + a Millstone unit (0.66).
    #   2023 Jun 0.38 — deep Millstone outage (plant CF 0.02); Seabrook full.
    #   2023 Nov 0.63 — a Millstone unit (plant CF 0.41).
    #   2024 Oct 0.44 — Seabrook refuel (0.12; Nov 0.57) + a Millstone unit (Sep 0.71).
    #   2025 Apr-May 0.75/0.77 — a Millstone unit refuel (0.59/0.64); Seabrook full year.
    # Source: EIA-923 Page 1 monthly net generation, 2023-2025 final.
    # Derivation/verify: scripts/data/derive_nuclear_monthly_cf.py --isos NEISO.
    #
    # 2019-2022 added 2026-08-14 (neiso-93 envelope repair) from the SAME
    # producer and the same EIA-923 source, after `--check` proved the
    # committed 2023-2025 block re-derives EXACTLY (byte-unchanged). Data-change
    # citation per rule 23 [R-FROZEN-DERIVE]: these are new YEARS of the
    # measured series — a SOURCE-COVERAGE extension, not a re-tune of an
    # existing one, and nothing here is identified against any year's residual.
    # Before this block an out-of-training year fell through BOTH measured
    # layers onto the static climatology NUCLEAR_MONTHLY_CF['NEISO'] (mean
    # 0.982) with no warning — worth +0.96 TWh of phantom nuclear in 2021
    # (+1.25 TWh in October alone), +0.61 TWh in 2022, +2.51 TWh in 2020
    # (measured: ASSESSMENT-neiso92-2021-readiness-2026-08-13.md §3.4).
    # Each dip is attributed to a single reactor, same standard as above:
    #   2019 Apr-May 0.69/0.79 — a Millstone unit refuel (0.50/0.66); Seabrook full.
    #   2020 Apr 0.43 — Seabrook refuel (plant CF 0.06) + a Millstone unit (0.65).
    #   2020 Oct 0.64 — a Millstone unit (plant CF 0.42; Nov 0.75).
    #   2021 Oct 0.43 — Seabrook refuel (plant CF 0.03; Nov 0.82) + Millstone (0.66).
    #   2022 Apr-May 0.70/0.63 — a Millstone unit refuel (0.53/0.41); Seabrook full.
    # CROSS-VALIDATED against EIA-930 ISNE `NUC` hourly telemetry — an
    # independent collection from EIA-923 — on the same fleet pmax
    # (scripts/probes/_neiso93_nuclear_crossval.py). |mean CF diff| 2020 0.002,
    # 2021 0.003, 2022 0.001: TIGHTER than the committed tuned years (2023
    # 0.001, 2024 0.004, 2025 0.007). Oct-2021 reads 0.43 (923) vs 0.426 (930),
    # so the deep refuelling outage is confirmed by hourly telemetry.
    #   CAVEAT (fleet vintage, material for 2019 ONLY) — RETIRED 2026-09-09 by
    #   session neiso-fuelvintage-1 (fleet-vintage charter task 4). It read:
    #   the CF is measured against the MODEL fleet's pmax, the model's NEISO
    #   nuclear fleet is the 2-plant EIA-860 operable snapshot (566 Millstone +
    #   6115 Seabrook, 3,355.4 MW), Pilgrim (EIA 1590, 673.6 MW net summer) ran
    #   Jan-May 2019 and generated 2.177 TWh before retiring 31 May 2019 but is
    #   absent from that snapshot, so "a 2019 solve is short ~2.18 TWh of
    #   nuclear regardless of this overlay". The EIA-930 cross-check showed it
    #   directly: Jan-May 2019 telemetry implied a fleet CF of 1.18-1.20
    #   (physically impossible for 3,355 MW) and the 923-930 gap collapsed to
    #   0.003-0.005 from June onward, exactly when Pilgrim stopped.
    #   WHAT CLOSED IT: the 2019-2022 retiree window (`RETIREMENT_WINDOW_START`
    #   2019, commit 7934e92c) puts Pilgrim in the parquet
    #   `eia860_generator_retired_within_window.parquet`, so
    #   `load_retired_within_window` injects it into a backcast fleet and the
    #   COD ramp (same plant code) zeros it after May 2019. It is the ONLY
    #   nuclear unit in NEISO's retiree window, so 2020-2025 are untouched.
    #   MEASURED against EIA-923 (2019 nuclear energy, GWh): actual incl.
    #   Pilgrim 29,818; this overlay on the OLD 2-plant fleet 27,698
    #   (-2.119 TWh, reproducing the caveat); on the retiree-window fleet
    #   29,879 (-0.061 TWh, -0.2 %). The shortfall is CLOSED.
    #   WHAT IS NOT CLOSED, stated rather than absorbed: the 2019 row's
    #   DENOMINATOR is still the 2-plant fleet (`derive_nuclear_monthly_cf.py`
    #   builds its fleet from `load_fleet_from_csv`, which does not union the
    #   retiree window), so Jan-May carries a monthly shape error even though
    #   the annual nets out. Re-derived on the 4,028.6 MW augmented fleet the
    #   five months read [0.98, 1.00, 0.99, 0.74, 0.76] against the committed
    #   [1.00, 1.00, 0.99, 0.69, 0.79] — worst month April, +130 GWh. NOT
    #   re-derived here on purpose: this constant is on the solve surface
    #   (`solve_surface_declared.py`), so editing it re-keys every ISO's
    #   configs, and it would do so to repair a year that is locked-test tier
    #   under an ACTIVE spend freeze and cannot be solved by anyone. The
    #   re-derive (and the derive script's fleet union behind it) is owed the
    #   day 2019 is authorized, and not before. 2020-2022 are unaffected
    #   either way (Pilgrim absent from both fleets).
    #   INDEPENDENTLY RE-DERIVED 2026-09-09 by the neiso-108 promotion lane and
    #   RECONCILED HERE (the two NEISO sessions ran in parallel and reached this
    #   same conclusion by different arithmetic; both are kept because each
    #   carries something the other does not). On the Jan-May window alone,
    #   EIA-923 for the three plants reads 13.002 TWh; this overlay on the
    #   restored 4,029.0 MW fleet gives 13.042 TWh (+0.040) against 10.862 TWh
    #   (-2.140) on the 2-plant fleet -- i.e. the fleet repair alone closes
    #   98.1 % of the gap. Two mechanical facts were re-checked rather than
    #   assumed: `monthly_online_mask(1972, 12, 2019, 5, y)` returns exactly 5
    #   online months in 2019 and 0 in every year 2020+, and the committed 2019
    #   row reproduces EXACTLY as the 2-plant EIA-923 numerator over the 3,355.4
    #   MW denominator in all twelve months, which is what pins the denominator
    #   claim above. The re-derived Jan-May figures agree to the last digit bar
    #   April (0.73 here vs 0.74 above, a 4,029.0 vs 4,028.6 MW denominator
    #   rounding), so the deferral argument is unaffected. THE REASON NOT TO
    #   RE-DERIVE IS THE ONE STATED ABOVE and it is the stronger one: this table
    #   is on the SOLVE SURFACE (`solve_surface.SURFACE_MODULES` carries
    #   `market_sim.config.constants`), so editing it re-keys configs, to repair
    #   a locked-test year under an ACTIVE freeze that nobody may solve.
    #   2026 is deliberately ABSENT: EIA-923 carries only Jan-Apr 2026, so a
    #   2026 anchor would post a false zero for H1's May-Jun.
    "NEISO": {
        2019: [1.00, 1.00, 0.99, 0.69, 0.79, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.90],
        2020: [0.99, 1.00, 0.99, 0.43, 0.71, 0.87, 0.99, 0.98, 0.99, 0.64, 0.84, 0.98],
        2021: [0.93, 1.00, 1.00, 1.00, 1.00, 0.89, 0.99, 0.98, 0.99, 0.43, 0.86, 1.00],
        2022: [0.94, 1.00, 0.99, 0.70, 0.63, 0.95, 0.99, 0.99, 0.99, 1.00, 1.00, 1.00],
        2023: [0.98, 0.98, 0.99, 0.41, 0.60, 0.38, 0.93, 0.93, 0.91, 0.84, 0.63, 0.87],
        2024: [0.88, 1.00, 1.00, 1.00, 0.99, 1.00, 0.99, 0.98, 0.81, 0.44, 0.76, 0.97],
        2025: [1.00, 1.00, 1.00, 0.75, 0.77, 1.00, 0.99, 0.93, 0.99, 0.86, 1.00, 1.00],
    },
    # MISO = the 10-plant / 13-unit EIA-860 operable nuclear fleet (Clinton,
    # Fermi, Monticello, Prairie Island 1+2, Point Beach 1+2, Waterford 3,
    # Grand Gulf, Callaway, River Bend, Arkansas Nuclear One 1+2) — fleet
    # nameplate 11,519 MW. Monthly EIA-923 net generation / (fleet pmax x hours
    # in month), clipped at 1.0 (ERCOT convention; the cap costs <1 TWh/yr vs
    # measured energy). Before this entry MISO had NO nuclear availability
    # overlay (the CAMPD/CEMS outage source is fossil-only — no nuclear), so
    # nuclear ran flat at the static-pattern x (1 - EFORD) ceiling, ~97.9 TWh
    # (~97% CF) EVERY year vs measured 87.2/90.4/90.7 — a systematic
    # +10.7/+7.5/+7.2 TWh nuclear over-injection that filled the bottom of the
    # stack and pushed coal and gas peakers out of merit (calibration runs
    # miso1-9). The dips are the actual staggered ~18-24 month refueling
    # cadence (spring/fall outage season; deep troughs verified to individual
    # reactors going to ~0 in the per-plant EIA-923 series, e.g. Prairie Island
    # / Callaway / River Bend Oct dips).
    # Source: EIA-923 Page 1 monthly net generation, 2023-2025.
    # Derivation/verify: scripts/data/derive_nuclear_monthly_cf.py --isos MISO.
    "MISO": {
        2023: [1.00, 0.94, 0.87, 0.83, 0.76, 0.93, 1.00, 0.96, 0.90, 0.68, 0.75, 0.75],
        2024: [0.78, 0.91, 0.80, 0.81, 0.83, 0.96, 1.00, 0.99, 0.97, 0.85, 0.90, 0.93],
        2025: [1.00, 0.92, 0.89, 0.82, 0.75, 0.84, 0.95, 0.98, 0.91, 0.85, 0.86, 1.00],
    },
    # SPP = Wolf Creek 1 (EIA 210, KS) + Cooper (EIA 8036, NE), the only two
    # reactors in the footprint (docs/multi-iso/spp-data-audit.md §5 row 11;
    # NRC licence rows in data/raw/nuclear-license-status/spp.csv). Monthly
    # EIA-923 net generation / (fleet pmax x hours in month), clipped at 1.0
    # (ERCOT convention). Derived at REGISTRATION (2026-09-06, lane SPP-20) by
    # the frozen script — the initial derivation from its source, never a
    # re-derivation on a residual (rule 23). The clip binds harder here than
    # for the six earlier fleets: the two units' EIA-923 output runs at or
    # above the model fleet pmax in most months (annual 17.23 / 15.30 / 16.19
    # TWh for 2023/24/25, row 11), so the flat-1.00 stretches are the cap, and
    # the cost of the cap vs measured energy is SPP-31's to quantify in
    # calibration_reference.json. The dips are the two units' staggered
    # ~18-month refueling cadence: Wolf Creek April-May 2024 and October-
    # November 2025, Cooper August-October 2024; 2023 carries no full-month
    # outage of either unit at this grain. The 2025 EIA-923 vintage is PARTIAL
    # (361 SWPP plant-rows vs 1,031 in 2024, row 11) and is re-derived when
    # the final file lands.
    # Source: EIA-923 Page 1 monthly net generation, 2023-2025.
    # Derivation/verify: scripts/data/derive_nuclear_monthly_cf.py --isos SPP.
    "SPP": {
        2023: [1.00, 0.99, 1.00, 0.97, 1.00, 1.00, 1.00, 1.00, 1.00, 0.96, 1.00, 1.00],
        2024: [1.00, 1.00, 0.95, 0.41, 0.80, 1.00, 1.00, 0.88, 0.95, 0.61, 0.98, 1.00],
        2025: [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 0.42, 0.70, 1.00],
    },
    # NWPP (registered 2026-09-14, lane NWPP-20): Columbia Generating Station
    # (plant 371, BPAT), the footprint's one reactor, against the model
    # fleet's pmax (1,151 MW summer capability). The biennial refuelling is
    # the whole of the variance: 2023 May-Jun (0.11 / 0.32), 2025 Apr-Jun
    # (0.28 / 0.00 / 0.12 — May 2025 net generation is exactly zero, so the
    # derive's -0.00 is written 0.00), none in 2024. 2025 EIA-923 is the
    # preliminary vintage (audit §8: 260 reporting plants vs 848-879);
    # re-derive when the final file lands.
    # Source: EIA-923 Page 1 monthly net generation, 2023-2025.
    # Derivation/verify: scripts/data/derive_nuclear_monthly_cf.py --isos NWPP.
    "NWPP": {
        2023: [0.97, 1.00, 0.98, 0.83, 0.11, 0.32, 0.97, 0.98, 0.99, 0.96, 0.98, 0.95],
        2024: [1.00, 1.00, 0.98, 1.00, 0.99, 0.97, 0.97, 0.98, 0.96, 1.00, 0.99, 0.98],
        2025: [0.99, 0.99, 0.89, 0.28, 0.00, 0.12, 0.98, 0.98, 0.99, 1.00, 1.00, 0.98],
    },
    # SOCO = Farley 1-2 (EIA 6001) + Hatch 1-2 (6051) + Vogtle 1-4 (649), the
    # eight Southern Nuclear reactors (docs/multi-iso/soco-data-audit.md §5
    # row 8; NRC licence rows in data/raw/nuclear-license-status/soco.csv).
    # Monthly EIA-923 net generation / (fleet pmax ONLINE in the month x hours
    # in month), clipped at 1.0. Derived at REGISTRATION (2026-09-14, lane
    # SOCO-20) by the frozen script — the initial derivation from its source,
    # never a re-derivation on a residual (rule 23). THE DENOMINATOR IS THE
    # MONTH'S ONLINE PMAX, the same grain the LP's COD ramp serves since
    # SOCO-15: Vogtle 3 (1,114 MW) enters 2023-07 and Vogtle 4 (1,114 MW)
    # 2024-04, so H1-2023 divides by 6,054 MW and H2-2023 by 7,168, not by the
    # whole 8,282 (which would have read 0.72 / 0.61 / 0.60 for Jan-Mar 2023
    # against the 0.99 / 0.85 / 0.82 below — a -27 % bias on the units that
    # WERE online, the mirror image of the phantom SOCO-15 removed). Every
    # other ISO's table is byte-identical under the same rule (--check, no
    # in-window nuclear COD elsewhere). The dips are the staggered refuelling
    # cadence — Hatch Feb-Mar every year, Farley Apr-Jun 2025 (Mar 0.70), the
    # Sep-Oct fall outages — and 2023's independent EIA-930 cross-check
    # agrees with EIA-923 to +0.58 % (audit §3.6). The 2025 EIA-923 vintage is
    # PARTIAL for the footprint (108 SOCO plants vs 311 / 330; nuclear is
    # complete, audit §1 item 9) and is re-derived when the final file lands.
    # Source: EIA-923 Page 1 monthly net generation, 2023-2025.
    # Derivation/verify: scripts/data/derive_nuclear_monthly_cf.py --isos SOCO.
    "SOCO": {
        2023: [0.99, 0.85, 0.82, 1.00, 0.99, 0.94, 0.87, 0.96, 0.88, 0.91, 0.90, 0.98],
        2024: [0.97, 0.88, 0.97, 0.84, 0.96, 0.96, 0.94, 0.99, 0.80, 0.89, 0.87, 0.97],
        2025: [1.00, 0.93, 0.70, 0.82, 0.78, 0.92, 0.98, 1.00, 0.85, 0.87, 1.00, 1.00],
    },
}

# Equivalent forced outage rate (demand) by technology class.
# Source: NERC GADS.
EFORD: dict[str, float] = {
    "gas_cc": 0.05,  # NERC GADS — combined-cycle gas
    "gas_ct": 0.06,  # NERC GADS — combustion turbine gas
    "gas_st": 0.07,  # NERC GADS — legacy gas steam (older, higher outage rate)
    "coal": 0.08,  # NERC GADS — coal steam
    "nuclear": 0.03,  # NERC GADS — nuclear
    "oil": 0.10,  # NERC GADS — oil peakers (infrequent run, higher EFOR)
    "biomass": 0.08,  # NERC GADS — biomass steam
    # CCS retrofit reuses the underlying gas_cc unit's forced-outage rate (the
    # amine/compression train adds parasitic load, not forced-outage risk, in
    # this model); supplies the class lookup used by model/capacity.py's
    # generic per-tech cost paths (was an inline ``.get(tech, 0.05)`` fallback).
    "gas_cc_ccs": 0.05,
}

# Correlated cold-event excess forced-outage curves by ISO, winterization era
# and plant group (FF-1B Stage 1; design charter
# docs/handoffs/ercot-retirement-composition-2026-07-16.md Part D). Consumed by
# data/outages.apply_correlated_outage_derate (forecast/hindcast only, gated on
# ScenarioConfig.correlated_forced_outage): per class,
#   excess(T) = clip(slope_per_c * (t0 - TMIN_sys), 0, cap)
# on the system daily MIN temperature, subtracted from availability, with
# winter_event_share (the era's climatological Dec-Feb mean of the curve) added
# back so the correlated model RELOCATES the cold-event share embedded in the
# flat GADS-based WEFOR instead of stacking on it.
#
# Source: scripts/data/derive_correlated_outage_curve.py (frozen derive, rule 23 --
# re-run only when the CAMPD / weather / EIA-930 source data updates; never
# hand-tune an entry to a residual). Measured from CAMPD TX unit-level hourly
# gross load on net-load-certified scarcity event days (in-merit certificate),
# excess over the NERC-GADS EFORD baseline: pre era anchored at Winter Storm
# Uri (2021-02-16, system TMIN -14.1 C; capacity-weighted thermal excess ~44%,
# consistent with the FERC/NERC Feb-2021 Cold Weather Report's ~half-the-fleet
# peak loss), post era fitted on Winter Storms Elliott (2022-12-23) and
# Heather (2024-01-16). Era boundary = PUCT weatherization rule 16 TAC 25.55
# (adopted Oct-2021, phase-1 compliance winter 2021-22): the weatherized fleet
# demonstrates roughly half the pre-era saturation depth. CHP classes and
# nuclear are deliberately absent (host-loaded gross output / no CAMPD trace
# cannot certify availability -- the STP-1 Uri trip is a known under-coverage).
# ERCOT-fitted; the table carries no generic fallback (rule 25 -- a curve
# fitted on one ISO's events never crosses an ISO boundary).
CORRELATED_OUTAGE_CURVE: dict[str, dict[str, dict[str, dict[str, float]]]] = {
    "ERCOT": {
        "pre": {
            # The ERCOT coal curve, carried to every coal subclass (COAL-SUB):
            # the excess is a per-unit function of TMIN alone, so each
            # subclass's units read exactly the value the bare class gave.
            "COAL_LIGNITE": {
                "slope_per_c": 0.0381,
                "cap": 0.270,
                "winter_event_share": 0.0018,
            },
            "COAL_PRB": {
                "slope_per_c": 0.0381,
                "cap": 0.270,
                "winter_event_share": 0.0018,
            },
            "COAL_BIT": {
                "slope_per_c": 0.0381,
                "cap": 0.270,
                "winter_event_share": 0.0018,
            },
            "COAL_WC": {
                "slope_per_c": 0.0381,
                "cap": 0.270,
                "winter_event_share": 0.0018,
            },
            "CC_REGULAR": {
                "slope_per_c": 0.0618,
                "cap": 0.438,
                "winter_event_share": 0.0029,
            },
            "CT_PEAKER": {
                "slope_per_c": 0.0784,
                "cap": 0.556,
                "winter_event_share": 0.0037,
            },
            "ST_GAS": {
                "slope_per_c": 0.0779,
                "cap": 0.552,
                "winter_event_share": 0.0037,
            },
        },
        "post": {
            # The ERCOT coal curve, carried to every coal subclass (COAL-SUB):
            # the excess is a per-unit function of TMIN alone, so each
            # subclass's units read exactly the value the bare class gave.
            "COAL_LIGNITE": {
                "slope_per_c": 0.0204,
                "cap": 0.077,
                "winter_event_share": 0.0004,
            },
            "COAL_PRB": {
                "slope_per_c": 0.0204,
                "cap": 0.077,
                "winter_event_share": 0.0004,
            },
            "COAL_BIT": {
                "slope_per_c": 0.0204,
                "cap": 0.077,
                "winter_event_share": 0.0004,
            },
            "COAL_WC": {
                "slope_per_c": 0.0204,
                "cap": 0.077,
                "winter_event_share": 0.0004,
            },
            "CC_REGULAR": {
                "slope_per_c": 0.0605,
                "cap": 0.157,
                "winter_event_share": 0.0011,
            },
            "CT_PEAKER": {
                "slope_per_c": 0.1878,
                "cap": 0.466,
                "winter_event_share": 0.0033,
            },
            "ST_GAS": {
                "slope_per_c": 0.1304,
                "cap": 0.306,
                "winter_event_share": 0.0023,
            },
        },
    },
}

# Annual demand growth rates by ISO, scenario path, and era. These are TOTAL
# (data-center-INCLUSIVE) rates: the near era still carries the DC boom, so at
# the default datacenter_load_path="off" they reproduce each ISO's published
# total-load forecast directly. When the DC block is ON,
# data.datacenter.add_datacenter_block RELOCATES the DC energy out of this rate
# into the explicit flat block under an energy-continuity constraint (energy
# invariant, only the peak shape flattens), so there is NO growth x DC
# double-count (CX-4 section 3.5 / FF-0D audit section 1.6).
#
# DERIVED, NOT TRANSCRIBED (SCN-LOAD 2026-09-06, owner ruling S4 / card D-4).
# Every rate below is now COMPUTED from the `load-forecast` curated datatype
# (data/dictionary/schema/load-forecast.schema.yaml; each ISO's published series
# under data/raw/load-forecast/<iso>/), replacing hand-read CAGRs. Rule 23
# [R-FROZEN-DERIVE]: the re-derivation is on the SOURCE — six published
# forecasts brought on disk for the first time, plus a MISO edition bump from
# the Sept-2025 to the 2026 LTLF — never on a residual. This lane ran no solve.
#
# THE DERIVATION, applied identically to all six ISOs:
#
#   near = CAGR of the published series over [edition's first forecast year ->
#          2031];  long = CAGR over [2031 -> min(2050, edition horizon)].
#
# The two eras TILE the span with no gap and no overlap under the model's own
# rule (scenario_resolvers.resolve_demand_growth_rate: era = "near" if
# year <= DEMAND_GROWTH_TRANSITION_YEAR else "long", applied by
# runner._scale_demand to the step y -> y+1 over range(weather_year, year)), so
# the near rate governs the transition from level(base) to level(2031) and the
# compounded level reproduces the publication at 2031 and at the horizon EXACTLY
# (verified to 1e-15 on all six). The former construction measured near over
# [base -> 2030] and long over [2031 -> horizon], leaving the 2030->2031 step
# covered by neither and overshooting the era boundary by one year of near
# growth -- material where near growth is large (ERCOT).
#
# BASIS = the ISO's published ANNUAL ENERGY series, uniformly. The model applies
# ONE flat multiplicative scalar to the whole 8760 (runner._scale_demand:
# base_demand * factor), so peak CAGR == energy CAGR by construction and only
# one can be honoured. Energy is the one the scalar can actually control: the DC
# block and the electrification layers are ENERGY-INVARIANT relocations, so they
# reshape the peak but can never repair a level error, and energy is what the LP
# integrates and what a CO2 answer needs. Rule 1 [R-STRUCT] -- the scalar owns
# the level, the block and the layers own the shape. The peak-basis CAGR each
# ISO publishes is recorded per row below as the disclosed G-L1 divergence; it
# is REPORTED, never used. (The former table mixed bases -- ERCOT/CAISO/PJM/MISO
# peak, NYISO energy, NEISO a blend of the two -- which is why several rows move
# materially; the movement is reported at full magnitude in
# docs/handoffs/FINDING-scn-load-2026-09-06.md section 4, never reconciled away,
# rule 14 [R-ACCURATE].)
#
# KNOWN, DISCLOSED, AND ROUTED: every edition's base year is 1-2 years AHEAD of
# the model's weather_year (default 2024), and _scale_demand compounds from the
# weather year -- so the model reaches 2030 having applied 1-2 extra years of
# growth relative to the publication's own base. That offset is NOT absorbed
# into these rates (burying it inside an input is exactly what rule 14 forbids);
# it is quantified per ISO in the FINDING section 5 and routed to SCN-DESK,
# because the fix is a base-year alignment or a level-index mechanism, not a
# constant.
#
# LOW / HIGH. Where the publisher issues a genuine low/high SERIES it is used;
# where it does not, the prior vintage's low/high-to-mid RATIOS are re-centred
# on the new mid (the construction this table has always declared), and the row
# says so. No band is invented, and no ISO's band crosses into another's
# (rule 25 [R-ISO-SCOPE]).
DEMAND_GROWTH_RATES: dict[str, dict[str, dict[str, float]]] = {
    # ERCOT -- 2025 Long-Term Load Forecast (posted 2025-04-08; ERCOT's LTLF page
    # still lists 2025 as the current long-term vintage). ALL THREE PATHS ARE
    # PUBLISHED SERIES, which is unique to ERCOT and comes from the components of
    # its own hourly forecast workbook:
    #   low  = base_economic_ercot -- ERCOT's organic forecast BEFORE any large-
    #          load additions (453.1 -> 499.6 TWh 2030 -> 600.6 TWh 2044), i.e.
    #          the published "large loads do not materialize" case;
    #   mid  = the ERCOT Adjusted forecast, ERCOT's own vetted/derated central
    #          case (485.9 -> 983.8 -> 1,279.8 TWh);
    #   high = the TSP Provided forecast, the transmission service providers'
    #          un-derated submissions (538.2 -> 1,555.9 -> 1,757.5 TWh).
    # The three pair 1:1 with the DATACENTER_ADDITIONS_MW paths below (no large
    # load / vetted / un-derated), so a LOAD-HI case is coherent across the two
    # axes rather than mixing bases -- the plan's G-L3 coherence question.
    # Peak-basis comparison (DISCLOSED, NOT USED): the same three cases on
    # annual peak MW give near 9.09% (mid) and 17.30% (high) vs the energy 13.48%
    # and 20.62%; ERCOT's own forecast has the system load factor rising from
    # ~65% to ~81% by 2030 as high-load-factor data centres arrive, which is what
    # the gap measures. Source: data/raw/load-forecast/ercot/ (2025 LTLF).
    "ERCOT": {
        "low": {"near": 0.019388, "long": 0.012900},
        "mid": {"near": 0.134813, "long": 0.016258},
        "high": {"near": 0.206157, "long": 0.004561},
    },
    # CAISO -- CEC California Energy Demand 2025-2045 (2025 IEPR, adopted
    # 2026-01-21), Form 1.2 Total Energy to Serve Load, summed over the three CEC
    # planning areas that make up the CAISO balancing authority (PGE + SCE +
    # SDGE; LADWP/IID/SMUD/BUG/NCNC are outside it): 215.3 -> 318.5 TWh (2045).
    # Rule 14's named exception applies -- the published boundary is the CEC
    # planning area, not the CAISO BAA -- and it is documented in
    # data/raw/load-forecast/README.md rather than silently reconciled.
    # low/high: the CED publishes NO demand-growth band (its scenario axis is
    # over load MODIFIERS -- AAEE/AAFS/AATE, BTM PV and storage, known loads --
    # not over economic growth), so the prior vintage's ratios are re-centred on
    # the new mid. The Form 1.1c data-centre scenarios were tested as a band and
    # REJECTED: the CEC's DC allocation is only ~1.8% of CAISO load, so it gives
    # a +/-0.12pt band that would collapse the growth axis rather than represent
    # it -- the basis mismatch rule 14 warns about.
    # Peak-basis comparison (DISCLOSED, NOT USED): Form 1.5 1-in-2 non-coincident
    # peak gives near 2.05% / long 1.09% vs energy 3.24% / 1.67%.
    "CAISO": {
        "low": {"near": 0.017371, "long": 0.010026},
        "mid": {"near": 0.032425, "long": 0.016710},
        "high": {"near": 0.048638, "long": 0.023394},
    },
    # PJM -- 2026 Load Forecast Report (posted 2026-01-14), the per-zone monthly
    # data workbook annualized to the RTO series: 856.1 -> 1,667.1 TWh (2046).
    # The former 0.036 near rate was the report's own headline TEN-YEAR summer-
    # peak CAGR (2026->2036) used for a near era that ends in 2030, which is the
    # window error the derivation above fixes independently of the basis change.
    # low/high: PJM issues ONE forecast, so the prior vintage's ratios are
    # re-centred on the new mid. This is the weakest cell in the table and it is
    # disclosed as such: re-centring a ratio on a much larger mid widens the band
    # in absolute terms (the high near rate is a mechanical consequence, not a
    # published number).
    # Peak-basis comparison (DISCLOSED, NOT USED): near 4.08% / long 1.89%.
    "PJM": {
        "low": {"near": 0.035914, "long": 0.013901},
        "mid": {"near": 0.064645, "long": 0.023830},
        "high": {"near": 0.107742, "long": 0.039717},
    },
    # NYISO -- 2026 Gold Book, Table I-1a "NYCA Baseline Energy and Demand
    # Forecasts", Energy-GWh Lower/Baseline/Higher columns. ALL THREE PATHS ARE
    # PUBLISHED SERIES (152.6 -> 205.8 TWh baseline at 2050; the Lower forecast
    # really does decline to 2030 on efficiency and codes, which is why the low
    # near rate is negative -- supported, not a defect).
    # This row was ALREADY derived rather than transcribed (FFR-SC 2026-08-03
    # spelled the six CAGRs out by hand in this comment block), and the curated
    # datatype REPRODUCES it: the intake's only change here is the era-window
    # correction (near now measured to 2031 rather than 2030), which moves the
    # three near rates by 3-5 basis points. The transcription is confirmed
    # correct -- and the extraction is validated against the edition's own
    # printed CAGR block (2026-31 energy -0.16% / 1.18% / 2.58%).
    # Peak-basis comparison (DISCLOSED, NOT USED): summer coincident peak gives
    # near 0.53% / long 0.59% vs energy 1.18% / 1.27%.
    "NYISO": {
        "low": {"near": -0.001611, "long": 0.002824},
        "mid": {"near": 0.011815, "long": 0.012720},
        "high": {"near": 0.025754, "long": 0.019602},
    },
    # NEISO -- ISO-NE 2026 CELT Report (2026-05-01), sheet 1.5.2 annual NET
    # energy for load: 116,679 GWh (2026) -> 127,660 GWh (2035), reproducing the
    # sheet's own printed 2026-2035 CAGR of 1.0%.
    # THE BLEND IS GONE. The former mid (0.013) averaged the published energy
    # CAGR (1.0%) and the published WINTER peak CAGR (2.9%) because "the single
    # flat scalar cannot carry both". A blend is not a published quantity and
    # cannot regenerate, so it is replaced by the energy CAGR alone -- and the
    # winter-peak divergence is now produced ENDOGENOUSLY by the heat_pump
    # electrification layer, whose anchors this same intake completed from the
    # CELT's own sheet 1.7 (see ELECTRIFICATION_LAYERS below). That is rule 19
    # [R-ONE-MECH] working: one mechanism per phenomenon, the scalar for the
    # level and the layer for the winter shape.
    # A ONE-YEAR LABEL SLIP IS ALSO FIXED: the former comment called 116,679 GWh
    # the 2025 figure; the CELT puts 117,755 GWh at 2025 (Actual) and 116,679 at
    # 2026 (SCN-WS4a section 5 item 4).
    # The long era rests on a 2031-2035 window only, because CELT is a ten-year
    # forecast; the rate flat-holds past 2035, a documented understatement rather
    # than an invented extension.
    # low/high: the CELT publishes NO growth band -- its sheet 1.6 P90...P10 band
    # is a WEATHER distribution around one forecast -- so the prior vintage's
    # ratios are re-centred on the new mid.
    # Peak-basis comparison (DISCLOSED, NOT USED): summer 0.53% / 0.90%, winter
    # 2.9% (2026-2035, ISO-NE's own printed figure) vs energy 0.74% / 1.33%.
    "NEISO": {
        "low": {"near": 0.004009, "long": 0.007759},
        "mid": {"near": 0.007446, "long": 0.013301},
        "high": {"near": 0.012601, "long": 0.022168},
    },
    # MISO -- 2026 Long-Term Load Forecast Results Summary (LTLF Workshop
    # 2026-04-13). AN EDITION BUMP: this row cited the Sept-2025 vintage until
    # this intake (rule 23 -- the re-derivation is on the source update).
    # MISO publishes the LTLF as a slide deck whose series are CHARTS, so the
    # net-energy trajectory is read from the PDF's own vector path coordinates,
    # calibrated on the axis tick text and validated against the deck's printed
    # labels: the read gives 677.7 TWh at 2026 vs the printed "~678", 1,104.0 at
    # 2046 vs "~1,104", and 1,404.5 for the High 2046 bar vs "~1,404" (the
    # SCN-WS4a slide-21 protocol).
    # low/high: MISO draws Low and High only as a 2046 ENDPOINT bar and prints
    # the pair as "~885 - 1,404 TWh", so there is no low/high series. The
    # endpoints are honoured exactly, with the mid path's near:long era ratio
    # locked, so nothing is invented -- documented limitation: MISO's band is
    # driven mostly by front-loaded data-centre uncertainty, which a
    # proportional era shape understates in the near era.
    # The vector read of the LOW 2046 bar is 903 TWh against the slide's printed
    # "~885"; the PRINTED number is used (rule 14 prefers the publication's own),
    # and the 2% disagreement is recorded in data/raw/load-forecast/README.md.
    # Peak basis: NOT AVAILABLE on the model's eras -- the 2026 LTLF publishes
    # peak only as 2026 and 2046 endpoints (124 GW -> 184 GW), which is a further
    # reason the energy basis is the one this table can actually be derived on.
    "MISO": {
        "low": {"near": 0.029732, "long": 0.008055},
        "mid": {"near": 0.054816, "long": 0.014850},
        "high": {"near": 0.082546, "long": 0.022363},
    },
    # SPP -- 2025 ITP Assessment Report v1.0, Figure 2.1 "Coincident Peak Load
    # by Model Year" (printed p. 43), curated as data/raw/load-forecast/spp/
    # spp.csv by SPP-12 (edition "2025 ITP", vintage 2025). Registered
    # 2026-09-06 by lane SPP-20. THREE DEPARTURES FROM THE TABLE'S CONVENTION,
    # each a property of what SPP publishes and each disclosed rather than
    # smoothed (rule 14 [R-ACCURATE]):
    #   1. PEAK BASIS, not energy. SPP publishes no standalone LTLF and no
    #      energy series — its forward load view lives inside the ITP cycle
    #      as four Base Reliability coincident-peak study years (2026 61.7 /
    #      2029 66.5 / 2034 69.8 / 2044 76.4 GW). The energy-basis rule above
    #      therefore cannot be honoured for SPP; this row is a PEAK CAGR, and
    #      the G-L1 divergence it would normally report against is the thing
    #      that is missing. Label: DERIVATION from four published rows, not a
    #      published figure (data/raw/load-forecast/spp/SOURCES.md says the
    #      same of the ~1.2 %/yr 2026->2044 headline).
    #   2. PIECEWISE-LINEAR INTERPOLATION between the four study years, the
    #      rule scripts/lib/load_forecast/spp.py DECLARES (interpolated peak
    #      2031 = 66.5 + (69.8 - 66.5) x 2/5 = 67.82 GW). Then the table's own
    #      era rule: near = CAGR 2026 -> 2031 = (67.82/61.7)^(1/5) - 1 =
    #      0.019095; long = CAGR 2031 -> 2044 (the edition horizon, < 2050) =
    #      (76.4/67.82)^(1/13) - 1 = 0.009206.
    #   3. low = high = mid. SPP publishes ONE case and no prior curated
    #      vintage exists to re-centre a ratio band on, so no band is
    #      invented (rule 25 — no ISO's band is borrowed). The report's
    #      RESILIENCY peaks (Figs. 2.48/2.49, pp. 82-83; +5.09 % summer /
    #      +3.7 % winter over the prior five-year ITP average) are a different
    #      published case and are deliberately not mixed in as a "high".
    # The four values are a CHART VECTOR READ whose year<->value pairing is
    # inferred (SOURCES.md, "The chart-read caveat"); replace on tabulated ITP
    # model data. Vintage offset (base year 2026 vs weather_year 2024) is the
    # same routed SCN-DESK item as every other row.
    "SPP": {
        "low": {"near": 0.019095, "long": 0.009206},
        "mid": {"near": 0.019095, "long": 0.009206},
        "high": {"near": 0.019095, "long": 0.009206},
    },
    # NWPP -- a participant-IRP ASSEMBLY, because the pool publishes no
    # footprint LTLF (data/raw/load-forecast/nwpp/nwpp.csv, 83 rows, landed
    # by NWPP-12; edition "Participant IRP assembly (2025 cycle)", vintage
    # 2025). Registered 2026-09-14 by lane NWPP-20. FOUR DEPARTURES FROM THE
    # TABLE'S CONVENTION, each a property of what is published and each
    # disclosed rather than smoothed (rule 14 [R-ACCURATE]):
    #   1. PEAK BASIS, not energy: the three covering publishers print peak
    #      series (PacifiCorp summer coincident peak before EE, Vol. 1 Table
    #      6.1; Idaho Power annual peak, 50th percentile, Table 8.2; PSE base
    #      peak before DSR, Ch. 6) — three peak definitions, no energy row.
    #   2. COVERAGE IS 40.36 % OF FOOTPRINT DEMAND, NOT THE FOOTPRINT:
    #      PacifiCorp (PACE+PACW 25.40 %), Idaho Power (IPCO 6.43 %), PSE
    #      (PSEI 8.53 %). BPAT — 20.26 %, the largest BA — files no IRP;
    #      NorthWestern / NV Energy / PGE / Avista publish theirs only as
    #      images. This row is the growth rate OF THE COVERED 40 %, applied
    #      to the whole footprint by the table's construction; nothing was
    #      scaled up (SOURCES.md 'Coverage').
    #   3. PIECEWISE-LINEAR INTERPOLATION per publisher, flat-hold outside
    #      each span, then SUMMED — the rule scripts/lib/load_forecast/
    #      nwpp.py DECLARES (covered_peak_mw). Worked: covered peak 2026 =
    #      20,144.0 MW, 2031 = 22,460.7, 2044 = 27,625.5 (the edition
    #      horizon, < 2050); near = (22,460.7/20,144.0)^(1/5) - 1 = 0.022010;
    #      long = (27,625.5/22,460.7)^(1/13) - 1 = 0.016048.
    #   4. low = high = mid. One published case per publisher (Idaho Power's
    #      10th/95th percentiles are its own weather band, not a load-growth
    #      scenario, and are not mixed in), so no band is invented.
    # NV Energy's 5,900 MW of data-centre requests by 2033 (2024 Joint IRP
    # Vol. 6 p. 3) is a published LARGE-LOAD component with no decomposition
    # into its retail forecast — routed to the capx director with the W6
    # card, never added here (see DATACENTER_ADDITIONS_MW["NWPP"]).
    "NWPP": {
        "low": {"near": 0.022010, "long": 0.016048},
        "mid": {"near": 0.022010, "long": 0.016048},
        "high": {"near": 0.022010, "long": 0.016048},
    },
    # SOCO -- Georgia Power "Budget 2025 (B2025) Load and Energy Forecast",
    # Technical Appendix Vol. 1 §1 of the 2025 IRP (Georgia PSC Docket 56002,
    # doc 221233, filed 2025-01-31, approved 2025-07-15), curated as
    # data/raw/load-forecast/soco/soco.csv by SOCO-12 (edition "Budget 2025
    # (B2025) / 2025 IRP", vintage 2025, gate G12). Registered 2026-09-14 by
    # lane SOCO-20. ENERGY basis, the table's convention (``energy_gwh``,
    # published-cell / 1000 with the unit correction SOCO-12 §4 declares):
    # 2026 102,557.4 -> 2031 165,701.5 -> 2044 194,890.0 GWh, so
    #   near = CAGR 2026 -> 2031 = (165,701.5 / 102,557.4)^(1/5) - 1 = 0.100707
    #   long = CAGR 2031 -> 2044 (the edition horizon) = (194,890.0 /
    #          165,701.5)^(1/13) - 1 = 0.012559
    # (the SPP era rule). TWO DEPARTURES, each a property of what Southern
    # publishes and each disclosed (rule 14 [R-ACCURATE]):
    #   1. THE SERIES IS GEORGIA POWER ONLY, NOT THE BALANCING AUTHORITY. The
    #      IRP workbook's "System" (IIC / SOCO-wide) column is REDACTED in every
    #      public sheet, and Alabama Power files no public IRP because Alabama
    #      has no IRP statute (SOCO-12 §0.1 / §5) — so roughly half the
    #      footprint by peak has no public forward load forecast at all.
    #      Nothing is grossed up to the footprint; a SOCO-wide forward peak is
    #      a CONSTRUCTION lane SOCO-32 must declare. Rule 14's misalignment
    #      exception (a different boundary) applies and is stated here rather
    #      than reconciled. The ~10 %/yr near-era rate is Georgia Power's own
    #      published large-load (data-centre) build-up, B2025 §1.2.1.
    #   2. low = high = mid. Georgia Power publishes ONE case (MG0) and no
    #      prior curated vintage exists to re-centre a ratio band on, so no
    #      band is invented (rule 25 — no ISO's band is borrowed).
    # Peak-basis comparison (DISCLOSED, NOT USED): the workbook's winter peak
    # gives near 12.8 % / long 2.0 %, summer 11.5 % / 2.1 % — higher than the
    # energy CAGRs because the large loads arrive as flat blocks.
    "SOCO": {
        "low": {"near": 0.100707, "long": 0.012559},
        "mid": {"near": 0.100707, "long": 0.012559},
        "high": {"near": 0.100707, "long": 0.012559},
    },
}

# Year at which demand growth transitions from near-term to long-term rate.
# Source: engineering judgment -- data center pipeline matures ~2030.
# THE FAMILY'S ONE UNSOURCED CONSTANT (gap G-D4-5, SCN-LOAD 2026-09-06): the
# six-source load-forecast intake found NO published basis for a transition year
# and did not invent one, so this stays a DISCLOSED NULL. It is now the only
# member of the load-shape constant family without a primary source; every other
# value in DEMAND_GROWTH_RATES, DATACENTER_ADDITIONS_MW, DATACENTER_ZONE_SHARE
# and ELECTRIFICATION_LAYERS traces to a published series on disk. Note that it
# is not a free parameter in the usual sense: it only says WHERE the two eras
# meet, and each era's rate is then derived against that boundary, so moving it
# re-derives both rates rather than re-tuning the level.
DEMAND_GROWTH_TRANSITION_YEAR: int = 2030

# --- As-of-vintage demand-growth tables (FH-2 mechanism; FH-3 values) --------
#     hindcast-forward plan §4 row 6
#
# DEMAND_GROWTH_RATES above is the CURRENT table: it is derived from the
# 2025/2026 LTLF / Gold Book / CELT / IEPR editions, so every rate in it encodes
# what those ISOs knew in 2025-2026 — above all the data-center boom (ERCOT mid
# near 8.5 %/yr). A full-forward hindcast (T1-FF, plan §2) that starts from a
# 2021 or 2023 base and grows demand forward MUST use the rates PUBLISHED AT
# THAT BASE YEAR, or it is not a forecast at all: applying 8.5 %/yr from 2021 to
# 2023 is +17.7 % against roughly +2 % actual, and the "error" it produces is an
# information leak wearing the costume of a forecast miss.
#
# This registry is the as-of addressing for that table, keyed
# ``{as_of_year: {iso: {low|mid|high: {near, long}}}}`` — the SAME inner shape
# as DEMAND_GROWTH_RATES, so one resolver serves both
# (config.scenario_resolvers.resolve_demand_growth_table) and there is exactly
# one growth mechanism (rule 19 [R-ONE-MECH]).
#
# The registry SHIPPED EMPTY at FH-2 (mechanism only) and is POPULATED by FH-3
# (2026-08-02) with per-ISO near/long rates read off the ERCOT LTLF / PJM LTLF /
# NYISO Gold Book / ISO-NE CELT / MISO LTLF / CEC IEPR editions published in the
# base year, each cited to its edition and table (rule 5 [R-NO-MAGIC]). FH-3
# landed 11 of 12 (ISO, vintage) cells and left CAISO 2021 as a MANUAL DOWNLOAD,
# which is what blocked FH-5's CAISO Arm K; the CEDU 2020 intake (2026-08-11,
# docs/handoffs/caiso-vintage-2021-intake-2026-08-11.md) closes it, so both
# vintages now cover all six registered ISOs — 12/12, no cell outstanding.
#
#   * ``ScenarioConfig.demand_growth_vintage = None`` (the default) resolves
#     DEMAND_GROWTH_RATES — byte-identical to every existing run; and
#   * a vintage request outside this dict RAISES
#     (``resolve_demand_growth_table``), naming the vintages on offer. It never
#     silently falls back to the current table, because a silent fallback IS the
#     leak this row exists to close.
#
# A vintage must carry every ISO it will be asked for: a missing ISO row also
# raises rather than borrowing today's rate (same reason). FH-3 extended that
# refusal one level down — a missing CASE inside a present (vintage, ISO) raises
# too, because most cells below carry ``mid`` alone (see "CASES") and the
# pre-FH-3 resolver would have fallen back to the scalar
# ``config.demand_growth_rate`` for a ``low``/``high`` request.
#
# CONSTRUCTION RULE (uniform across every cell; no cell is interpolated, per
# the FH-3 brief — an edition that could not be reached is a MANUAL DOWNLOAD
# row in docs/handoffs/fh-3-asknown-driver-vintages-2026-08.md §4, never a
# guessed rate):
#   * METRIC = the edition's own published central ANNUAL ENERGY forecast for
#     the ISO/planning footprint. Energy, not peak, because ``_scale_demand``
#     applies a FLAT hourly scalar — the model's growth rate is an energy
#     growth rate and peak follows mechanically. (This differs from the live
#     table above, which is peak-CAGR-based for several ISOs; the two bases
#     diverge wherever an ISO's peak and energy diverge under electrification,
#     which the NEISO block above already flags. Both T1-FF arms read THIS
#     table, so no arm-vs-arm comparison is affected — see the findings doc
#     §3 for the disclosure.)
#   * near = CAGR from the VINTAGE's base year (the as_of key) to
#     DEMAND_GROWTH_TRANSITION_YEAR (2030) — the base year is where
#     runner._scale_demand starts compounding. In 11 of the 12 cells the base
#     year IS the edition's first forecast year, so the two readings coincide;
#     they part company only for CAISO 2021, whose CEDU 2020 edition opens at
#     2020, and there the BASE year governs. That reading is not a choice made
#     for this cell: the CAISO 2023 cell already anchors at 2023 inside a
#     2022-2035 edition, and reproduces its stored 0.0130/0.0132 exactly.
#   * long = CAGR from 2031 to the edition's last forecast year, but ONLY when
#     the edition carries >= 3 post-2030 forecast years; otherwise long is
#     EDGE-HELD to near and marked "(long edge-held)" below. An edge-held long
#     is not a modelling risk here: T1-FF Phase A (2023-2025) and Phase B
#     (2021-2025) solve no year past 2030, so ``long`` never binds in any
#     T1-FF window — it is carried for table-shape completeness only.
#   * CASES = only what the edition PUBLISHES as a full low/base/high series.
#     Most ISOs publish a central forecast alone in these vintages, so most
#     cells carry ``mid`` only. Transporting the live table's band width onto a
#     vintage central would be inventing a growth rate no edition published.
# Per-cell arithmetic (source values, ratios, CAGRs) is tabulated in
# docs/handoffs/fh-3-asknown-driver-vintages-2026-08.md §3.
DEMAND_GROWTH_RATES_VINTAGES: dict[int, dict[str, dict[str, dict[str, float]]]] = {
    # ===== as-of 2021 (Phase B base; plan §3.1) =====
    2021: {
        # ERCOT 2021 Long-Term Load Forecast, "2021 ERCOT Monthly Peak Demand
        # and Energy Forecast 2021-2030" (posted 2020-12-28), monthly Energy
        # (MWh) summed to annual: 405,842 GWh (2021) -> 485,143 (2030).
        # Covers 2021-2030 only => long edge-held.
        "ERCOT": {"mid": {"near": 0.0200, "long": 0.0200}},
        # PJM 2021 Load Forecast Report (January 2021), Table E-1 Annual Net
        # Energy, PJM RTO: 780,068 GWh (2021) -> 804,517 (2030);
        # 806,729 (2031) -> 819,553 (2036).
        "PJM": {"mid": {"near": 0.0034, "long": 0.0032}},
        # NYISO 2021 Load & Capacity Data Report ("Gold Book", April 2021),
        # Table I-1a NYCA Baseline Energy and Demand Forecasts, Energy-GWh
        # columns Low/Baseline/High — the one edition-published low/mid/high
        # band in this vintage. Baseline 150,980 (2021) -> 145,960 (2030),
        # 146,690 (2031) -> 160,980 (2040). The NEGATIVE mid near rate is real
        # and is the point: the 2021 Gold Book forecast NY energy DECLINING to
        # 2030 on efficiency/codes, then rising on electrification.
        "NYISO": {
            "low": {"near": -0.0111, "long": 0.0054},
            "mid": {"near": -0.0038, "long": 0.0104},
            "high": {"near": 0.0050, "long": 0.0215},
        },
        # ISO-NE 2021 CELT Report (April 2021), Table 1.5.2 Annual net energy
        # for load, "Net (reduced for BTM PV and EE)": 121,692 GWh (2021) ->
        # 133,960 (2030). Horizon ends 2030 => long edge-held.
        "NEISO": {"mid": {"near": 0.0107, "long": 0.0107}},
        # MISO 2021 Independent Energy and Peak Demand Forecast (State Utility
        # Forecasting Group, Purdue, November 2021), Table 49 Gross MISO System
        # Energy: 643,003 GWh (2021) -> 714,142 (2030); 721,429 (2031) ->
        # 794,118 (2041). The edition's Table 52 publishes High/Low CAGRs but
        # no High/Low SERIES (its Appendix D carries no energy table), so no
        # near/long can be computed for those cases => mid only.
        # AS-OF CAVEAT: published November 2021, i.e. inside the base year.
        # See findings doc §3.4.
        "MISO": {"mid": {"near": 0.0117, "long": 0.0096}},
        # CAISO — CEC "California Energy Demand Forecast Update, 2020-2030
        # Baseline Forecast" (CEDU 2020, the 2020 IEPR Update demand forecast,
        # docket 20-IEPR-03), STATE Planning Area forms, ADOPTED 2021-01-26 by
        # CEC Resolution 21-0125-2 (TN 236455; Notice of Availability TN 236333,
        # 2021-01-14). Form 1.2 Total_Energy_For_Load, GWh, off the "Corrected -
        # February 2021" STATE workbooks — Low TN 236984 / Mid TN 236983 / High
        # TN 236985, each retrievable at
        # https://efiling.energy.ca.gov/GetDocument.aspx?tn=236983 (swap the tn).
        #   low  256,568.979 (2021) -> 258,557.502 (2030)  => +0.0858 %/yr
        #   mid  262,562.244 (2021) -> 284,825.953 (2030)  => +0.9084 %/yr
        #   high 268,824.268 (2021) -> 309,599.149 (2030)  => +1.5815 %/yr
        # Horizon ends 2030, i.e. ZERO post-2030 forecast years => long
        # EDGE-HELD to near, same as ERCOT/NEISO above.
        # EDITION CHOICE: CEDU 2020 is the LATEST CEC demand forecast adopted at
        # or before the 2021 base year — earlier in the base year (January) than
        # MISO's November-2021 edition above. Its successor, CED 2021 ("Demand
        # Forecast Update, 2021-2035", Resolution 22-0126-02, TN 241296), was
        # adopted 2022-01-26 and is therefore a post-base-year leak, refused on
        # the same ground FH-3 refused CEDU 2022 for this cell.
        # ALL THREE CASES are edition-published here (three separate STATE
        # workbooks), unlike the 2023 cell below where CEDU 2022 publishes a
        # single Baseline. They are an ECONOMIC/DEMOGRAPHIC band — Form 2.2
        # varies personal income, commercial employment, floorspace and
        # households across the cases — i.e. the same kind of band as NYISO's
        # Gold Book Low/Baseline/High above, NOT the weather spread FH-3 §4 M3
        # ruled out for ERCOT/PJM.
        # The "Corrected" filing (which fixed peak and sector energy totals) is
        # IMMATERIAL to Form 1.2: it moves 2021 and 2030 by <0.1 GWh on ~262,562
        # and leaves the CAGR unchanged to 6 dp, so the cell does not depend on
        # the original-vs-corrected choice; the corrected form is cited per
        # rule 14 [R-ACCURATE].
        # FOOTPRINT CAVEAT: the CEC forecast is STATEWIDE, while the model's
        # CAISO carries ~80 % of California load; the statewide growth RATE is
        # used as the CAISO proxy — the same footprint approximation the 2023
        # cell below and the live CAISO block above both make.
        # Closes the one MANUAL DOWNLOAD FH-3 left open (findings doc §4 M1).
        "CAISO": {
            "low": {"near": 0.0009, "long": 0.0009},
            "mid": {"near": 0.0091, "long": 0.0091},
            "high": {"near": 0.0158, "long": 0.0158},
        },
    },
    # ===== as-of 2023 (Phase A base; plan §3.1) =====
    2023: {
        # ERCOT 2023 Long-Term Load Forecast, "2023 ERCOT Monthly Peak Demand
        # and Energy Forecast 2023-2032" (posted 2023-01-18), monthly Energy
        # summed to annual: 445,388 GWh (2023) -> 527,020 (2030). Only 2031-2032
        # sit past the transition (< 3 years) => long edge-held.
        "ERCOT": {"mid": {"near": 0.0243, "long": 0.0243}},
        # PJM 2023 Load Forecast Report (January 2023), Table E-1 Annual Net
        # Energy, PJM RTO: 788,050 GWh (2023) -> 878,461 (2030);
        # 889,393 (2031) -> 960,428 (2038).
        "PJM": {"mid": {"near": 0.0156, "long": 0.0110}},
        # NYISO 2023 Gold Book (April 2023), Table I-1a, Energy-GWh
        # Low/Baseline/High. Baseline 151,780 (2023) -> 157,660 (2030),
        # 160,100 (2031) -> 204,030 (2040).
        "NYISO": {
            "low": {"near": 0.0038, "long": 0.0304},
            "mid": {"near": 0.0054, "long": 0.0273},
            "high": {"near": 0.0184, "long": 0.0422},
        },
        # ISO-NE 2023 CELT Report (May 2023), Table 1.5.2 net annual energy:
        # 122,057 GWh (2023) -> 140,481 (2030). Horizon ends 2032 (< 3 post-2030
        # years) => long edge-held.
        "NEISO": {"mid": {"near": 0.0203, "long": 0.0203}},
        # MISO 2023 Independent Energy and Peak Demand Forecast (SUFG/Purdue,
        # November 2023), Table 49 (base) 644,204 GWh (2023) -> 691,462 (2030),
        # 696,343 (2031) -> 758,334 (2043); Table 80 (High) 667,961 -> 747,235,
        # 754,268 -> 833,962; Table 86 (Low) 619,522 -> 635,458, 638,396 ->
        # 683,189. This edition DOES publish full 90/10 High and Low series
        # (Appendix D), so all three cases are edition-sourced.
        # AS-OF CAVEAT: published November 2023 (inside the base year), the
        # latest-published of any driver here. Findings doc §3.4.
        "MISO": {
            "low": {"near": 0.0036, "long": 0.0057},
            "mid": {"near": 0.0102, "long": 0.0071},
            "high": {"near": 0.0162, "long": 0.0084},
        },
        # CAISO — CEC "California Energy Demand Forecast, 2022-2035 Baseline
        # Forecast" (CEDU 2022), STATE Planning Area forms, January 2023;
        # Form 1.2 Total_Energy_For_Load: 269,058 GWh (2023) -> 294,482 (2030);
        # 298,860 (2031) -> 314,982 (2035). FOOTPRINT CAVEAT: the CEC forecast
        # is STATEWIDE, while the model's CAISO carries ~80 % of California
        # load; the statewide growth RATE is used as the CAISO proxy, the same
        # footprint approximation the live CAISO block above makes.
        "CAISO": {"mid": {"near": 0.0130, "long": 0.0132}},
    },
}

# --- Data-center load block (CX-4, gap G-34; FF-1C currency refresh) -------
# Cumulative data-center MW trajectories per ISO/path, consumed by
# data.datacenter.resolve_datacenter_mw (forecast-mode-only scenario axis;
# default path "off" => unused, byte-identical to today). Piecewise-linear
# between anchor years, flat after the last anchor. Anchors are ENVELOPE VALUES
# derived from the published headline figures in the design memo
# docs/handoffs/cx4-datacenter-load-design-2026-07.md §2.1 (each traced below to
# its primary ISO forecast / interconnection-queue source with the arithmetic
# shown); they are the low/mid/high support the PB sampler interpolates, refined
# on each forecast vintage from the ISO's MW-by-year table (memo §3.3, §10.6).
# parameters.json tier 2, modeled flag OFF (a forward input, not a fitted knob).
# ISOs with no published DC decomposition ship {} => 0 MW (memo §2.2).
#
# DOUBLE-COUNT SAFETY (FF-0D audit §1.6): because the near-era DEMAND_GROWTH_RATES
# are TOTAL (DC-inclusive), add_datacenter_block does NOT add this block on top of
# that growth — it RELOCATES the block's energy out of the (peaky) grown demand
# and back as a flat block (energy invariant, 2030-continuity; CX-4 §3.5). So the
# block corrects DC's hourly SHAPE without double-counting its energy. At the MID
# path the DC block sits inside each ISO's total forecast (relocate regime); a
# high/full-queue path can exceed it and then adds as genuinely incremental load.
# FF-1C (2026-07, rule 23) refreshed the MISO block (was {}) and re-confirmed the
# ERCOT/PJM/CAISO/NYISO anchors against the FF-0D-cited vintages. A 2026-07-21
# follow-up refined the MISO block to the forecast's granular DC peak-demand
# trajectory (1.2 / 20.5 / 33.5 GW at 2026 / 2030 / 2046, replacing the 2027/2030
# band) and enriched the NEISO + DATACENTER_ZONE_SHARE deferral notes.
DATACENTER_ADDITIONS_MW: dict[str, dict[str, dict[int, float]]] = {
    # ---------------------------------------------------------------------
    # DERIVED FROM THE CURATED `load-forecast` DATATYPE (SCN-LOAD 2026-09-06,
    # owner ruling S4 / card D-4). Every anchor below is now computed from a
    # published series on disk under data/raw/load-forecast/<iso>/ rather than
    # hand-read from a headline. Rule 23 [R-FROZEN-DERIVE]: the re-derivation is
    # on the SOURCE (six published forecasts brought on disk; MISO and NYISO
    # additionally an edition bump), never on a residual -- this lane ran no
    # solve. The three limitations the D-4 gap list named (gap G-D4-2) are
    # addressed row by row below: CAISO's `high := mid`, MISO's ratio-
    # extrapolated `high`, and the PJM/NYISO `low := 0` floor.
    #
    # UNITS. These are NAMEPLATE/PEAK MW: data.datacenter multiplies by
    # ScenarioConfig.datacenter_load_factor (0.85) to get the flat block MW.
    # Where a publisher issues the component as ENERGY the conversion is
    # MW = GWh x 1000 / 8760 / 0.85, so the block reproduces the published
    # ANNUAL ENERGY exactly (the round trip is closed by construction, and
    # energy is what the LP integrates); where it issues PEAK MW that value is
    # used directly and the block then carries an implied 85% load factor. Each
    # row says which. MISO is the one ISO publishing both, and they agree to
    # ~7%, which bounds the convention error.
    # ---------------------------------------------------------------------
    #
    # ERCOT -- 2025 LTLF. PEAK-MW basis, from ERCOT's own hourly forecast
    # workbook: the annual maximum of `<zone>_contracts + <zone>_officer_letters`
    # summed over the eight weather zones (the TSP-attested Large Load
    # additions), times the published ~73% data-centre share (Dec-2025 ERCOT
    # Board System Planning update, Item 16.2) -- the same basis
    # DATACENTER_ZONE_SHARE["ERCOT"] already uses, so the block's level and its
    # zonal split are now derived from ONE series.
    #   low  = 0, and it is now a MEASURED zero rather than an "honest floor"
    #          convention: ERCOT publishes `base_economic_ercot`, its organic
    #          forecast before any large-load additions, and this is that case.
    #          It pairs exactly with DEMAND_GROWTH_RATES["ERCOT"]["low"].
    #   mid  = ERCOT Adjusted large loads x 0.73 (4,817 -> 52,304 -> 57,089 MW
    #          of large load at 2025 / 2030 / 2035).
    #   high = the TSP Provided (un-derated) case: the Adjusted large load plus
    #          the published TSP-minus-Adjusted system peak gap, x 0.73. This
    #          REPLACES the former 122 GW/2030 figure, which was a raw
    #          interconnection-queue estimate (0.70 x 226 GW queue x 0.77
    #          in-service); the new value is ERCOT's own published upper
    #          FORECAST, and it pairs with DEMAND_GROWTH_RATES["ERCOT"]["high"].
    "ERCOT": {
        "low": {2025: 0.0, 2030: 0.0},
        "mid": {2025: 3516.0, 2030: 38182.0, 2035: 41675.0},
        "high": {2025: 9281.0, 2030: 88603.0, 2035: 95151.0, 2040: 97920.0},
    },
    # PJM -- 2026 Load Forecast Report, TABLE B-9b, read for the first time
    # (the D-4 gap list records it as never read). PEAK-MW basis: "Total
    # Adjustments to Summer Peak Load (MW) for Each PJM Zone and RTO
    # (2026-2046)", RTO row. Per the report's own "Load Adjustments" section
    # every adjusted zone is adjusted for growth in data center load, with DOM
    # additionally carrying a voltage-optimization program and PS port
    # electrification -- so the series is very slightly wider than data centres
    # alone, which is stated rather than netted out.
    #   low  = 0 -- RE-STATED AS A MEASURED NULL with a better citation than the
    #          former "signed-ISA subset not separately published": Table B-9b
    #          IS the vetted set (the 2026 report trimmed the near term on
    #          stricter data-centre vetting), and no lower subset is published.
    #   mid  = the published B-9b RTO series.
    #   high := mid -- PJM issues no upper case. This is the SAME documented
    #          limitation CAISO used to carry, and it moves here rather than
    #          disappearing: conservative, never overstates the upside. The
    #          former high (30 GW/2030, 60 GW/2040) is retired because it now
    #          sits BELOW the published mid, which would be incoherent.
    "PJM": {
        "low": {2026: 0.0, 2030: 0.0},
        "mid": {2026: 11479.0, 2030: 38815.0, 2035: 68977.0, 2046: 87194.0},
        "high": {2026: 11479.0, 2030: 38815.0, 2035: 68977.0, 2046: 87194.0},
    },
    # CAISO -- CEC CED 2025-2045, FORM 1.1c "Electricity Deliveries to End Users
    # by Agency (GWh) - Data Centers Only", summed over the CAISO planning areas
    # (PGE + SCE + SDGE). ENERGY basis, converted as above.
    #   THE `high := mid` GAP IS CLOSED. Form 1.1c publishes TWO data-centre
    #   scenarios and the second is the high-DC table the former comment records
    #   as "not yet read": the *Planning Forecast* allocation (the adopted
    #   central case -> mid) and the *Local Reliability Scenario* allocation
    #   (materially higher -- the case CPUC resource adequacy and CAISO local
    #   studies use -> high). At 2030 they are 12,078 vs 31,574 GWh.
    #   low = 0 is the published "no additional data centres" case: the CED
    #   applies the DC allocation as an additive load modifier on the baseline.
    #   The mid track lands within ~10% of the former 2024-IEPR-based anchors
    #   (1,622 vs 1,800 MW at 2030; 4,382 vs 4,900 at 2040), which is the
    #   vintage difference, not a correction.
    "CAISO": {
        "low": {2025: 0.0, 2030: 0.0, 2040: 0.0},
        "mid": {2025: 98.0, 2030: 1622.0, 2035: 4123.0, 2040: 4382.0},
        "high": {2025: 125.0, 2030: 4240.0, 2035: 6531.0, 2040: 6658.0},
    },
    # NYISO -- 2026 Gold Book, TABLE I-14 "Large Load Forecast" (an EDITION BUMP
    # from the 2025 Gold Book the former anchors cited). ENERGY basis, converted
    # as above, from the published NYCA annual-energy series; the zone columns
    # were validated against the publication's own NYCA total in all 16 years.
    #   THE `low := 0` FLOOR IS CLOSED. Table I-14's own footer publishes a
    #   Lower / Baseline / Higher / All-Loads breakdown at the horizon
    #   (1,221 / 2,937 / 4,393 / 12,663 MW of winter peak), so NYISO does
    #   publish a large-load band. low and high are the Baseline trajectory
    #   scaled to the published Lower and Higher endpoints (ratios 0.41573 and
    #   1.49574); the Baseline row of that footer reproduces Table I-14's own
    #   2041 winter column exactly, which is how the block was identified.
    #   The former high (10 GW by 2031) was the raw interconnection QUEUE, which
    #   this edition publishes separately as "All Loads" 12,663 MW / Table IV-7
    #   12,330 MW summer -- a different quantity from the forecast, and not the
    #   one the block represents.
    #   DOCUMENTED LIMITATION, unchanged in kind from the former row: Table I-14
    #   is a LARGE-LOAD forecast, not a data-centre-only one (Zone C's ramp is
    #   the Micron semiconductor fab), so this block is slightly wider than data
    #   centres. NYISO publishes no DC-only split. The Gold Book also states
    #   these values are already embedded in the baseline energy and peak
    #   forecasts -- the same convention the block's relocate regime assumes.
    "NYISO": {
        "low": {2026: 203.0, 2030: 713.0, 2035: 1083.0, 2040: 1195.0},
        "mid": {2026: 489.0, 2030: 1716.0, 2035: 2605.0, 2040: 2874.0},
        "high": {2026: 731.0, 2030: 2567.0, 2035: 3896.0, 2040: 4299.0},
    },
    # MISO -- 2026 LTLF (an EDITION BUMP from the Sept-2025 vintage). PEAK-MW
    # basis, from the deck's own printed numbers wherever it prints one:
    #   2026 = 1,154 MW -- slide 21's data-centre net energy at 2026 (9.4 TWh,
    #          chart read, validated against the printed 9.6) converted at
    #          MISO's OWN published ~93% data-centre load factor (slide 21 key
    #          insights: 90% hyperscale at ~95% + 10% enterprise at ~75%), not
    #          at the model's 0.85 -- the publisher's own factor is the right
    #          one for reading the publisher's own energy;
    #   2030 = 20,000 MW -- printed verbatim on slide 18 ("2030 MISO data
    #          center demand 20 GW");
    #   2046 = 1,154 + 32,000 MW -- slide 16's printed data-centre contribution
    #          to the 2026->2046 peak growth.
    #   THE `high` EXTRAPOLATION IS CLOSED. Slide 16 prints the driver's own
    #   low-high range (22 - 44 GW by 2046), so `high` is published rather than
    #   the former "2030 high/mid ratio carried forward"; the 2030 low and high
    #   anchors apply that same published range to the mid increment.
    #   THE `low := 0` FLOOR IS ALSO CLOSED for the same reason.
    #   The new mid track lands within ~2% of the former anchors
    #   (20,000 vs 20,500 at 2030; 33,154 vs 33,500 at 2046) and the new high
    #   within ~2% of the former ratio-extrapolated 44,100 -- the earlier work
    #   is confirmed, and what changes is that the numbers are now published
    #   rather than derived.
    "MISO": {
        "low": {2026: 1154.0, 2030: 14111.0, 2046: 23154.0},
        "mid": {2026: 1154.0, 2030: 20000.0, 2046: 33154.0},
        "high": {2026: 1154.0, 2030: 27067.0, 2046: 45154.0},
    },
    "NEISO": {},
    # SPP (registered 2026-09-06, lane SPP-20): {} => 0 MW, the NEISO
    # precedent and the memo §2.2 rule verbatim — the 2025 ITP publishes no
    # data-centre / large-load DECOMPOSITION of its peak series (only the
    # four Base Reliability totals in DEMAND_GROWTH_RATES["SPP"]), so nothing
    # is isolated and nothing is invented. Lands on intake of an SPP
    # large-load forecast component (routed to the capx director with card P8).
    "SPP": {},
    # NWPP (registered 2026-09-14, lane NWPP-20): {} => 0 MW, the NEISO/SPP
    # precedent and the memo §2.2 rule verbatim — the ONE published large-
    # load component in the footprint, NV Energy's "twelve ... bundled-
    # service high load factor data centers requesting 5,900 MW of capacity
    # by 2033" (2024 Joint IRP Vol. 6 printed p. 3, of 7,600 MW of large-load
    # requests; "scaled down in the retail load forecast" by an UNSTATED
    # factor into 13,288 GWh over ten years), is a request count, not a
    # DECOMPOSITION of any peak series, so nothing is isolated and nothing is
    # invented. Lands on intake of a published NWPP large-load component
    # (routed to the capx director with card N9).
    "NWPP": {},
    # SOCO (registered 2026-09-14, lane SOCO-20): {} => 0 MW, the memo §2.2
    # rule. Georgia Power's B2025 forecast DOES isolate a large-load external
    # adjustment (a 24,300 MW pipeline through the mid-2030s, 7,300 MW of it
    # committed), but publishes it CHART-BORNE and SOCO-12 transcribed no
    # ``component="large_load"`` rows (FINDING-soco-12 §7 item 4) — so
    # nothing is isolated and nothing is invented; the block rides inside
    # DEMAND_GROWTH_RATES["SOCO"]'s ~10 %/yr near era until a chart read
    # lands. Alabama Power publishes no forecast at all (SOCO-12 §5).
    "SOCO": {},
}

# Per-ISO override of the data-center block's zonal allocation, {iso: {zone:
# share}} summing to 1.0 per ISO (memo §3.3). DEFAULT (ISO absent here) = each
# zone's iso_configs load_share, applied by data.datacenter.datacenter_zone_shares.
# Override ONLY where published queue siting geography differs from the load
# distribution (memo names ERCOT North/West and PJM Dominion skews). PJM, ERCOT
# and MISO all carry published overrides below; CAISO, NYISO and NEISO stay on
# the load_share default (no per-zone DC magnitude published — see the per-ISO
# notes; NEISO additionally ships an empty DATACENTER_ADDITIONS_MW, so its block
# is 0 MW and the allocation is moot either way).
# FF-1C (2026-07) confirmed the skew DIRECTIONS are published (ERCOT LFL queue
# concentrates in North/Oncor + West; PJM DC concentrates in Dominion/DOM). The
# exact per-zone MW FRACTION tables (PJM Load Forecast Table B-9b; ERCOT LFL
# queue geography) are separate Excel/queue pulls not fetchable in-session; per
# the memo's "never invent a split" rule an ISO is overridden only when at least
# one zone's share is grounded in a published magnitude (rule 14 — a reconciled
# version of real data), never a wholesale guess.
#
# 2026-07-21 follow-up — the per-ISO status and the anchors behind it:
#   PJM — POPULATED below (rule-14 reconciled, DOM-anchored). Dominion (DOM,
#     "data center alley") hosts the world's largest DC concentration: ~20 GW DC
#     by 2037 vs PJM's ~30 GW DC by 2030 (DC = 94% of the +32 GW 2024-2030 peak
#     growth). Interpolating the ~20 GW/2037 figure back to the block's ~2030
#     horizon (~16.5 GW) over ~30 GW PJM DC 2030 gives DOM ~0.55 (band 0.45-0.60,
#     horizon-sensitive: ~0.6 near-term, ~0.4 by 2037 as other zones catch up).
#     DOM is anchored at 0.55; the residual 0.45 is distributed across the other
#     7 zones by their iso_configs load_share (the memo §3.3 default) — ONE
#     published anchor + the documented default, NOT an invented full split. This
#     materially beats the pure load_share default (which gives DOM only 0.15) for
#     siting-sensitive results (Dominion congestion / locational RA). Documented
#     limitation: ComEd (+3.7 GW to 2031), AEP and PL are the next-largest DC
#     zones, so the load_share residual mildly understates them; refine all 8
#     anchors when Table B-9b is read. Source: PJM 2025 Long-Term Load Forecast
#     Report (Table B-9b); EIA Today-in-Energy (Virginia/DOM ~20 GW).
#   ERCOT — POPULATED (2026-07-21) from ERCOT's OWN per-weather-zone large-load
#     additions, so it is a full published decomposition rather than the single
#     published anchor + load_share residual PJM ships. Basis: the 2025 ERCOT
#     Adjusted Long-Term Load Forecast (ErcotAdjustedForecast.xlsb, posted with
#     the Apr-2025 LTLF), which carries per-weather-zone `<zone>_contracts` +
#     `<zone>_officer_letters` large-load columns — the TSP-attested Large Load
#     additions that are ~73% data centers (Dec-8/9-2025 ERCOT Board System
#     Planning update, Item 16.2). Taking those columns' 2030-horizon peak MW per
#     weather zone and aggregating onto the 7 model transmission zones by the SAME
#     weather-zone -> transmission-zone crosswalk iso_configs already documents
#     (West <- FAR_WEST+WEST, North <- NORTH+NORTH_C, Northeast <- EAST,
#     Houston <- COAST, South_Central <- SOUTH_C, South <- SOUTHERN; ERCOT has no
#     Panhandle weather zone -> Panhandle 0) gives the split below (52,306 MW
#     total). It confirms the published skew with real MW — West Texas/Permian
#     (West 0.244 vs 0.149 load_share) and North/Oncor are DC-heavy, while the
#     Coast/Houston load pocket is load-heavy but NOT DC-heavy (0.114 vs 0.265
#     load_share). A source-driven decomposition (rule 23) that regenerates each
#     forecast vintage (rule 13), NOT an invented split. Source: ERCOT 2025
#     Adjusted LTLF (ErcotAdjustedForecast.xlsb), per-weather-zone contracts +
#     officer letters; end-use share from ERCOT Board Item 16.2 (Dec 2025).
#   MISO — POPULATED 2026-09-05 (SCN-WS4a), superseding the earlier "no per-zone
#     MW fraction sourced -> stays load_share default" deferral. MISO's 2026 LTLF
#     publishes a DC decomposition BY REGION, which is what this table needs:
#     slide 21 of the 2026 LTLF Results Summary ("Data Centers Net Energy, TWh;
#     Current Trajectory") stacks DC net energy into MISO North / Central / South
#     and defines those regions on the same slide as North = LRZs 1, 3;
#     Central = LRZs 2, 4, 5, 6, 7; South = LRZs 8, 9, 10. The regional split is
#     year-invariant in the published series (Central/North/South = 0.5824 /
#     0.2347 / 0.1829 at 2046 and 0.5822 / 0.2349 / 0.1829 at 2030), and the
#     series reproduces the deck's own published system totals exactly — 9.6 TWh
#     in 2026 and 266.3 TWh in 2046 vs the published "data centers expand from
#     9.6 TWh to 266 TWh" — which is the read's validation, together with the
#     independently-reported ~58% Central share of 2046 DC energy. ENERGY share ==
#     MW share here: MISO applies ONE footprint-wide ~93% DC load factor (slide 21
#     key insights, 90% hyperscale at ~95% + 10% enterprise at ~75%; no regional LF
#     is published) and our block is flat, so no basis conversion is involved.
#     Region -> model zone via the LRZ unions iso_configs already documents
#     (West = LRZ 1, Plains = LRZ 3+5, Illinois = LRZ 4, Indiana = LRZ 6,
#     East = LRZ 2+7, South = LRZ 8+9+10): MISO-South IS the published South
#     region (0.1829, no reconciliation needed), and MISO-West + the LRZ-3 half of
#     MISO-Plains are the North region while MISO-Illinois + MISO-Indiana +
#     MISO-East + the LRZ-5 half of MISO-Plains are the Central region. WITHIN each
#     region the memo §3.3 default (load_share) distributes — the same one-published-
#     anchor-plus-documented-default construction PJM ships, here with three
#     anchors. MISO-Plains is the ONE model zone that straddles a published region
#     boundary (LRZ 3 in North, LRZ 5 in Central) and the model carries no LRZ-3 vs
#     LRZ-5 load split (EIA-930 reports them as the single sub-BA 0035), so the
#     straddle is resolved on MISO's OWN published per-LRZ magnitudes: the
#     PY2025/2026 summer Local Reliability Requirement, LRZ 3 = 13,574 MW vs
#     LRZ 5 = 10,243 MW -> 0.5699 / 0.4301 (data/raw/capacity-deliverability/
#     miso/miso.csv, sourced to the PY2025-26 LOLE Study Report). Rule 14 — a
#     reconciled version of real data at a boundary our zones do not match
#     exactly, never a guess; rule 13 — it regenerates from the next LTLF vintage
#     by re-reading the same slide. The material result is that MISO-South is DC-
#     LIGHT (0.183 vs its 0.271 load_share), which is MISO's own narrative: the
#     southern LRZs grow on industrial drivers, oil-and-gas electrification and
#     green hydrogen rather than data centers (2024 LTLF whitepaper p.13), while
#     Central grows on "abundant low-cost land and industrial-focused incentives
#     that attract large hyperscale campuses" (2026 LTLF slide 21).
#     Documented limitation: the published decomposition is REGIONAL, so the
#     within-region ordering is the load_share default, not a published per-LRZ DC
#     table — MISO's driver-level per-LRZ forecast data would refine all six
#     anchors (it is behind the 403-walled www.misoenergy.org host; see
#     docs/handoffs/FINDING-scn-ws4a-2026-09-05.md §4 for the D-4 gap list).
#     Source: MISO 2026 Long-Term Load Forecast Results Summary (LTLF Workshop
#     2026-04-13, "20260413 LTLF Workshop 2026 Long Term Load Forecast
#     Summary_UPDATED", cdn.misoenergy.org) slides 21 and 26; MISO December-2024
#     Long-Term Load Forecast Whitepaper p.13; MISO PY2025-26 LOLE Study Report
#     (per-LRZ LRR) via data/raw/capacity-deliverability/miso/miso.csv.
#   CAISO / NYISO — no published per-zone DC magnitude at any read vintage; both
#     keep the load_share default (never an invented split, memo §3.3 / rule 23).
DATACENTER_ZONE_SHARE: dict[str, dict[str, float]] = {
    # PJM — reconciled DOM-anchored siting (full derivation in the note above):
    # DOM at its published ~0.55 near-2030 DC share, residual 0.45 by load_share
    # across the other 7 zones. Keys are the model zone_names; shares sum to 1.0
    # (datacenter_zone_shares raises otherwise). Refine to a full 8-zone anchor
    # when PJM Load Forecast Table B-9b (per-zone DC MW) is read.
    "PJM": {
        "PJM_ComEd": 0.062728,  # load_share 0.1185 (DC-heavy: +3.7 GW/2031, understated by residual)
        "PJM_AEP_Ohio": 0.115292,  # load_share 0.2178 (named DC-growth zone)
        "PJM_ATSI": 0.044677,  # load_share 0.0844
        "PJM_West_APS": 0.041554,  # load_share 0.0785
        "PJM_Central_PA": 0.058281,  # load_share 0.1101 (PPL/PL — named DC-growth zone)
        "PJM_Dominion": 0.550001,  # ANCHOR — published ~0.55 near-2030 DC share (world's largest DC hub)
        "PJM_EMAAC": 0.088507,  # load_share 0.1672 (incl. PSEG — named DC-growth zone)
        "PJM_SWMAAC": 0.038960,  # load_share 0.0736 (incl. BGE — named DC-growth zone)
    },
    # ERCOT — large-load-additions-anchored siting (full derivation in the note
    # above): the 2030-horizon per-weather-zone large-load additions (contracts +
    # officer letters, ~73% data centers) from ERCOT's own 2025 Adjusted LTLF
    # (ErcotAdjustedForecast.xlsb), aggregated onto the 7 model transmission zones
    # by the iso_configs weather-zone crosswalk (52,306 MW total). Keys are the
    # model zone_names in LP order; shares sum to 1.0 (datacenter_zone_shares
    # raises otherwise). Materially DC-skews toward West/Permian and South_Central
    # and away from the Houston/Coast load pocket vs the load_share default.
    "ERCOT": {
        "West": 0.244408,  # FAR_WEST 7,746 + WEST 5,038 = 12,784 MW (Permian/DC-heavy; load_share 0.1494)
        "Panhandle": 0.000000,  # no ERCOT weather zone maps here -> 0 (load_share 0.0)
        "North": 0.277388,  # NORTH 5,711 + NORTH_C 8,798 = 14,509 MW (Oncor/DFW; load_share 0.3064)
        "Northeast": 0.005219,  # EAST 273 MW (load_share 0.0351)
        "Houston": 0.114021,  # COAST 5,964 MW (load-heavy, not DC-heavy; load_share 0.2649)
        "South_Central": 0.220032,  # SOUTH_C 11,509 MW (Austin/San Antonio corridor; load_share 0.1642)
        "South": 0.138932,  # SOUTHERN 7,267 MW (load_share 0.0800)
    },
    # MISO — published-region-anchored siting (full derivation in the note above):
    # the 2026 LTLF's DC net-energy split across MISO North / Central / South
    # (0.2347 / 0.5824 / 0.1829, year-invariant), mapped onto the model's six LRZ-
    # union zones, with load_share distributing WITHIN each region and the one
    # region-straddling zone (MISO-Plains = LRZ 3 North + LRZ 5 Central) split
    # 0.5699/0.4301 on the published PY2025/26 per-LRZ LRR. Keys are the model
    # zone_names in LP order; shares sum to 1.0 (datacenter_zone_shares raises
    # otherwise). The material move vs the load_share default is MISO-South, which
    # is load-heavy but NOT DC-heavy.
    "MISO": {
        "MISO-West": 0.152557,  # LRZ 1 (MN/ND), North region; load_share 0.1466
        "MISO-Plains": 0.151060,  # LRZ 3 (IA, North) + LRZ 5 (MO, Central); load_share 0.1385
        "MISO-Illinois": 0.078214,  # LRZ 4, Central region; load_share 0.0676
        "MISO-Indiana": 0.155040,  # LRZ 6, Central region; load_share 0.1340
        "MISO-East": 0.280229,  # LRZ 2+7 (WI/MI), Central region; load_share 0.2422
        "MISO-South": 0.182900,  # LRZ 8+9+10 = the published South region exactly; load_share 0.2711
    },
}

# --- FF-G4 Option-B electrification end-use layers (additive load layers) ---
# docs/handoffs/ff-g4-load-shape-design-memo-2026-07.md §4.2/§5 (the DECIDED
# design; owner box D1 = Option B). Per-ISO, per-layer ANNUAL-ENERGY adoption
# anchors, {iso: {layer: {path: {year: GWh}}}} — the same {year: value} anchor
# grammar + low/mid/high path axis as DATACENTER_ADDITIONS_MW directly above,
# resolved by data.datacenter.resolve_electrification_gwh with the identical
# interpolation/fallback chain (piecewise-linear between anchors, flat-hold
# outside; low/high collapse onto mid when unpublished — never an invented
# band).
#
# Each layer is a real end-use with a published forward adoption trajectory and
# a physical hourly shape (memo §4.2; rule 1 [R-STRUCT]); rule-13 [R-MEASURED]
# admissibility: the anchors are published ISO forecast components that
# regenerate every vintage and respond to changed conditions — never a realized
# outcome fed back. Layers are INCREMENTAL TO THE WEATHER-YEAR BASE: the
# weather year's measured 8760 already contains realized electrification load,
# and the near-era DEMAND_GROWTH_RATES are TOTAL (electrification-inclusive),
# so add_load_layers RELOCATES each layer's energy out of the peaky-grown total
# onto the layer's own shape (energy-invariant, the DC-block algebra
# generalized — no double-count; memo §4.2 "DC interaction: clean by design").
# Anchor convention: {first-forecast-era year: 0.0, horizon year: published
# component GWh}; 0.0 at the near anchor because the component is incremental
# to the measured base (the source's own starting-year component value is the
# D4-1 intake's refinement). Flat-hold after the last anchor (the
# DATACENTER_ADDITIONS_MW convention) — a documented understatement past the
# source horizon, never an invented extension.
#
# "No published component => ship {}" (memo §4.2, the CX-4 §2.2 rule verbatim):
# an ISO with an empty layer dict is an honest no-op — the flat-scalar status
# quo persists there until its source lands (D4 intake rows, memo §8-D4).
# PROFILES are NOT stored here: the heat_pump layer's hourly shape is computed
# from the run weather year's measured NOAA GHCN daily zone temperatures
# (heating-degree construction, data.datacenter.heat_pump_layer_profile); a
# layer with no profile source registered in data.datacenter refuses to arm
# (fail-closed), which is why the ev anchors below ship {} — see each note.
ELECTRIFICATION_LAYERS: dict[str, dict[str, dict[str, dict[int, float]]]] = {
    # ---------------------------------------------------------------------
    # POPULATED FROM THE CURATED `load-forecast` DATATYPE (SCN-LOAD 2026-09-06,
    # owner ruling S4 / card D-4, gap G-D4-4 -- the row the gap list named as
    # the intake's biggest prize, because the layers were wired and EMPTY).
    # Before this intake exactly ONE cell carried numbers (NEISO heat_pump, two
    # hand anchors) and `ev` was empty in every ISO. Rule 23 [R-FROZEN-DERIVE]:
    # every value below moves because its SOURCE landed on disk, never because
    # a residual moved -- this lane ran no solve.
    #
    # WHAT BLOCKS A CELL IS NOW THE SHAPE, NOT THE NUMBERS. The layer registry
    # in data.datacenter is FAIL-CLOSED: a layer with anchors but no citable
    # hourly profile REFUSES to arm rather than inventing one (rule 5
    # [R-NO-MAGIC]). `heat_pump` has an ISO-agnostic physics profile (NOAA GHCN
    # heating-degree hours, and all six ISOs have a weather archive), so it arms
    # wherever a published energy component exists. `ev` has a profile for
    # ERCOT ONLY, because ERCOT is the only publisher issuing a machine-readable
    # hourly EV series. The other ISOs' EV ADOPTION anchors are published and
    # are curated in the datatype -- they are recorded per row below so the
    # cell arms the day a citable 8760 lands -- but the layers stay {}.
    # Rule 25 [R-ISO-SCOPE]: no ISO's profile or anchor is another's fallback.
    # ---------------------------------------------------------------------
    # NEISO -- ISO-NE 2026 CELT, sheet 1.7 "Electrification Forecast".
    #
    # heat_pump: the TWO-ANCHOR approximation ({2026: 0.0, 2035: 7165.0}) is
    # REPLACED BY THE PUBLISHED TEN-YEAR SERIES. This is a real correction, not
    # a refinement: the published trajectory is strongly convex (198 GWh in
    # 2026, 2,464 by 2030), while a straight line from a 0.0 anchor implied
    # ~796 GWh in 2027 and ~3,184 by 2030 -- overstating the near era by ~30%
    # and understating the 2030s ramp. The former comment named exactly this
    # ("the source's own starting-year component value is the D4-1 intake's
    # refinement"), and it is what landed. Values are ISO-NE's Heating category,
    # New England total, annual energy GWh; they are already INCREMENTAL to the
    # base year, which is the convention add_load_layers needs.
    # low/high collapse onto mid: the CELT publishes one forecast (its 1.6 band
    # is a WEATHER distribution), so no band is invented.
    #
    # ev: STILL {}, and the reason has changed. The adoption anchors are now
    # published and curated -- ISO-NE's Transportation category, NE total:
    # 195 / 588 / 1,036 / 1,557 / 2,167 / 2,881 / 3,715 / 4,682 / 5,798 / 7,074
    # GWh for 2026-2035 -- but the TEF deck publishes the hourly charging
    # allocation only as CHARTS (Final 2026 EV Forecast, slides 19-20), so there
    # is no citable 8760. Anchors without a shape are an open blocker, not a
    # parameter; the cell arms the day ISO-NE publishes the allocation as data.
    "NEISO": {
        "heat_pump": {
            "mid": {
                2026: 198.0,
                2027: 671.0,
                2028: 1200.0,
                2029: 1793.0,
                2030: 2464.0,
                2031: 3235.0,
                2032: 4113.0,
                2033: 5059.0,
                2034: 6082.0,
                2035: 7165.0,
            },
        },
        "ev": {},
    },
    # PJM -- STILL {} in both layers. The 2026 Load Forecast Report's data
    # workbook publishes zone x month peak and energy TOTALS only; the EV and
    # behind-the-meter components are consultant (S&P Global) inputs the report
    # describes but does not tabulate, and no end-use component series is in
    # either published workbook. Honest no-op: PJM's shape story is carried by
    # the flat data-centre block above, which is now on the published Table
    # B-9b series and is by far the larger effect (38.8 GW at 2030).
    "PJM": {"heat_pump": {}, "ev": {}},
    # NYISO -- 2026 Gold Book. THE FORMER COMMENT WAS STALE: it recorded that
    # "the memo records no annual ENERGY component series [F], and converting
    # peak MW to layer energy needs a load-factor assumption we refuse to
    # invent". The Gold Book publishes exactly that series, twice, by zone A-K
    # and out to 2056 -- Table I-13a (Building Electrification Annual Energy
    # Usage) and Table I-11b (Electric Vehicle Annual Energy Usage). No
    # load-factor assumption is involved.
    #
    # heat_pump: NOW ARMED on Table I-13a, NYCA total, which the table itself
    # labels "Cumulative FUTURE Impacts" -- i.e. already incremental to the
    # base, the convention add_load_layers needs. DOCUMENTED APPROXIMATION:
    # I-13a is NYISO's BUILDING ELECTRIFICATION component (space heating, water
    # heating, cooking and other end uses), slightly wider than heat pumps
    # alone, and NYISO publishes no heat-pump-only energy split; it is shaped
    # here on heating-degree hours, which fits the heating-dominated bulk of it
    # and overstates the heating share of the non-heating remainder. The
    # Gold Book itself notes the SUMMER peak impact is the part driven by
    # non-heating end uses (p.15), so the winter/energy majority is the right
    # one for this shape. Stated rather than hidden; the refinement is a
    # published heat-pump-only split, never a residual fit.
    # low/high collapse onto mid: the Lower/Higher demand forecasts differ in
    # their electrification assumptions but the Gold Book publishes I-13a for
    # the Baseline only.
    #
    # ev: STILL {}. Table I-11b's anchors ARE published and curated (NYCA total
    # 1,309 GWh at 2026 rising to 31,894 by 2050, "Total Cumulative Impacts",
    # so the layer would take the increment over 2026), and the Gold Book
    # DESCRIBES the shape -- winter ~1.4x summer, charging concentrated
    # 22:00-03:00 peaking ~01:00 -- but a described shape is not a citable 8760.
    # The blocker is the profile, not the numbers.
    "NYISO": {
        "heat_pump": {
            "mid": {
                2026: 449.0,
                2030: 2455.0,
                2035: 6877.0,
                2040: 12048.0,
                2045: 17169.0,
                2050: 21117.0,
            },
        },
        "ev": {},
    },
    # CAISO -- STILL {} in both layers, unchanged in kind. The CED 2025 forms
    # curated here (1.2 energy, 1.5 peak, 1.1c data centres) carry no end-use
    # electrification split; the CEC's downloadable 8760 hourly demand forecast
    # files are the right CAISO treatment and are a SEPARATE intake (FF-G4 memo
    # section 8-D4 item 4), not hand anchors here.
    "CAISO": {"heat_pump": {}, "ev": {}},
    # MISO -- STILL {} in both layers, and as with NEISO/NYISO the blocker is
    # now the shape. The 2026 LTLF's EV energy trajectory is published (slide
    # 24, read from the chart's vector coordinates and validated: the 2026->2046
    # growth reads 61.8 TWh against the deck's own printed 47-78 TWh low-high
    # range and the ~62 TWh figure) and is curated: 5.4 TWh at 2026 rising to
    # 67.2 by 2046. But MISO states it "uses NREL/DOE charging profiles" rather
    # than publishing one of its own (slide 24), so there is no MISO-specific
    # citable 8760 -- and borrowing another ISO's or a generic one would be the
    # rule 25 [R-ISO-SCOPE] violation this table refuses. MISO publishes no
    # heat-pump split at all.
    "MISO": {"heat_pump": {}, "ev": {}},
    # ERCOT -- THE FORMER COMMENT WAS STALE HERE TOO: it recorded "no published
    # end-use decomposition (large loads are embedded in the hourly LTLF
    # files)". ERCOT's 2025 Adjusted LTLF workbook carries an explicit hourly
    # per-weather-zone `<zone>_ev` component alongside `base_economic_<zone>`
    # and `<zone>_pv`.
    #
    # ev: NOW ARMED, and it is the only `ev` cell in the table that can be,
    # because ERCOT is the only publisher issuing the charging shape AS DATA:
    # the curated normalized 8,760-hour profile is
    # data/raw/load-forecast/ercot/ercot_ev_hourly_profile_2030.csv, registered
    # in data.datacenter._LAYER_PROFILE_BUILDERS for ERCOT alone.
    # Anchors are the published ERCOT-total EV energy INCREMENTAL to the
    # edition's own base year (the workbook publishes a total EV load, 1,495 GWh
    # in 2025, of which the base year's part is already inside the model's
    # measured weather-year 8760 -- so the increment is what the layer adds).
    # low/high collapse onto mid: ERCOT publishes the EV component only in the
    # Adjusted case.
    #
    # heat_pump: {} -- ERCOT publishes no heating-electrification component
    # (Texas heating is a small and largely non-electric end use), so there is
    # nothing to arm and nothing is invented.
    "ERCOT": {
        "heat_pump": {},
        "ev": {
            "mid": {
                2025: 0.0,
                2030: 5419.0,
                2035: 22837.0,
                2040: 61465.0,
                2044: 104798.0,
            },
        },
    },
    # SPP (registered 2026-09-06, lane SPP-20): both layers {} — the honest
    # no-op. The 2025 ITP publishes no heating-electrification or EV component
    # (peak totals only, data/raw/load-forecast/spp/SOURCES.md), so there is
    # no adoption anchor to curate and no citable 8760 to arm; the
    # flat-scalar status quo persists for SPP until a source lands (the PJM /
    # CAISO / MISO posture above).
    "SPP": {"heat_pump": {}, "ev": {}},
    # NWPP (registered 2026-09-14, lane NWPP-20): no publisher in the pool
    # prints a heat-pump or EV adoption series for the footprint (WA's CETA
    # and OR's HB 2021 electrification narratives carry no tabulated 8760 or
    # adoption anchor in the NWPP-12 corpus), so the flat-scalar status quo
    # persists for NWPP until a source lands — the SPP / PJM / CAISO / MISO
    # posture above.
    "NWPP": {"heat_pump": {}, "ev": {}},
    # SOCO (registered 2026-09-14, lane SOCO-20): both layers {} — the honest
    # no-op. Georgia Power's B2025 forecast publishes no heating-
    # electrification or EV component (SOCO-12 transcribed peak + energy
    # totals only, data/raw/load-forecast/soco/SOURCES.md), and Alabama Power
    # publishes nothing, so there is no adoption anchor to curate and no
    # citable 8760 to arm; the flat-scalar status quo persists for SOCO until
    # a source lands (the SPP posture above).
    "SOCO": {"heat_pump": {}, "ev": {}},
}

# Balance-point (base) temperature for the heat_pump layer's heating-degree
# hourly shape, deg C. 18.3 C = 65 F, the standard NOAA/EIA degree-day base
# temperature (NOAA NCEI degree-day methodology; EIA heating-degree-day
# definition uses the same 65 F base). The layer's hourly profile is
# HDH(h) = max(0, base - T(h)) on the run weather year's measured NOAA GHCN
# zone temperatures with the Parton & Logan (1981) diurnal reconstruction
# (data.eia930.weather.diurnal_drybulb_from_daily) — a physics construction
# that regenerates for any weather year and responds to changed conditions
# (rule 13). Frozen physical input (rule 23): moves only on a source update.
# DOCUMENTED LIMITATION (conservative): linear degree-hours omit cold-climate
# heat-pump COP rolloff and resistance-backup switchover, so the profile
# UNDERSTATES extreme-cold sharpening relative to the CELT HEF winter-peak
# contribution; the refinement channel is a published cold-climate HP
# performance curve (memo §8-D4 items 1/7), never a residual fit.
HEAT_PUMP_BALANCE_POINT_C: float = 18.3

# --- Fuel-price trajectories, availability shapes & carbon price paths ------
# MOVED to config/fuel_trajectories.py (constants split, 2026-07-20).
# All names re-exported at the top of this module.


# --- Cap-and-trade, capacity-market, adequacy & storage-value registries ----
# MOVED to config/capacity_market.py (constants split, 2026-07-20).
# All names re-exported at the top of this module.

# New entry technology cost and performance parameters.
#
# capex_per_kw and fom_per_kw_yr are DERIVED from the committed NREL ATB 2024
# (v3.0.0) extract by scripts/data/derive_entry_costs_from_atb.py — not
# hand-set. Each is the ATB Moderate-case value at the technology's base
# projection year (2026 = REAL_DOLLAR_BASE_YEAR / model start year; 2030 for
# new nuclear, ATB's earliest published nuclear year), converted from ATB 2024's
# 2022-USD basis to the model's constant-2026-USD basis with INFLATION_RATE
# (factor 1.022**(2026-2022) = 1.090947). tests/test_atb_entry_cost_
# consistency.py asserts these constants equal that derivation (CLAUDE.md
# rule 23 source-consistency); refresh for a new ATB edition by re-running
# scripts/data/fetch_nrel_atb.py then the derive script and pasting its output.
# (FF-1E — docs/handoffs/ff-inputs-currency-audit-2026-07.md §3.2 "STALE +
# UNWIRED": replaces the pre-FF-1E hand-transcribed values that carried an
# "NREL ATB 2024" label but matched no single ATB projection year — wind ≈
# ATB-2037, solar ≈ 2032, gas_cc ≈ 2049, nuclear_smr ≈ 2039 in the Moderate
# case — and were never read from the ATB extract on disk.)
#
# base_cf, learning_rate and lifetime_yr are NOT re-derived here: ATB's CF /
# heat-rate parameters and the Wright's-Law learning rates are outside the
# committed extract's CAPEX/Fixed-O&M scope (data/raw/nrel-atb/README.md), so
# they keep their prior citations. gas_cc_ccs keeps its NETL Rev 4 basis (90 %
# capture; ATB publishes only 95 %/97 % CCS) — see its inline note.
NEW_ENTRY_COSTS: dict[str, dict[str, float]] = {
    "wind": {  # onshore wind
        "capex_per_kw": 1676.6,  # ATB 2024 Moderate LandbasedWind/Class4 @2026, 2026$ (derived)
        "fom_per_kw_yr": 33.7,  # ATB 2024 Moderate @2026, 2026$ (derived)
        "learning_rate": 0.12,  # Wright's-Law rate — literature, outside ATB CAPEX/FOM scope
        "base_cf": 0.38,  # NREL ATB 2024 CF (not in the committed CAPEX/FOM extract)
        "lifetime_yr": 30,
    },
    "solar": {  # utility-scale solar PV
        "capex_per_kw": 1562.2,  # ATB 2024 Moderate UtilityPV/Class5 @2026, 2026$ (derived)
        "fom_per_kw_yr": 22.3,  # ATB 2024 Moderate @2026, 2026$ (derived)
        "learning_rate": 0.20,  # Wright's-Law rate — literature, outside ATB CAPEX/FOM scope
        "base_cf": 0.27,  # NREL ATB 2024 CF (not in the committed CAPEX/FOM extract)
        "lifetime_yr": 30,
    },
    "gas_cc": {  # combined-cycle gas
        "capex_per_kw": 1583.3,  # ATB 2024 Moderate NG 2-on-1 CC (F-Frame) @2026, 2026$ (derived)
        "fom_per_kw_yr": 36.1,  # ATB 2024 Moderate @2026, 2026$ (derived)
        "learning_rate": 0.02,  # Wright's-Law rate — mature tech, outside ATB CAPEX/FOM scope
        "base_cf": 0.55,  # NREL ATB 2024 CF (not in the committed CAPEX/FOM extract)
        "lifetime_yr": 30,
    },
    "gas_ct": {  # frame combustion turbine / peaker. base_cf is a nominal peaker
        # duty cycle; the new-entry screen prices a gas_ct on its price-duration
        # energy margin, not base_cf x mean price. ATB gives the CT the same
        # CAPEX in all three cost cases, so its tech-cost multiplier is 1.0.
        "capex_per_kw": 1428.7,  # ATB 2024 Moderate NG CT (F-Frame) @2026, 2026$ (derived)
        "fom_per_kw_yr": 27.9,  # ATB 2024 Moderate @2026, 2026$ (derived)
        "learning_rate": 0.02,  # Wright's-Law rate — mature tech, outside ATB CAPEX/FOM scope
        "base_cf": 0.12,  # nominal peaker duty cycle (not an ATB CF)
        "lifetime_yr": 30,
    },
    "nuclear_smr": {  # small modular reactor. ATB costs new nuclear from 2030 only,
        # so the base snapshot is ATB's 2030 projection (its earliest year).
        "capex_per_kw": 10527.6,  # ATB 2024 Moderate Nuclear-Small @2030, 2026$ (derived)
        "fom_per_kw_yr": 148.4,  # ATB 2024 Moderate @2030, 2026$ (derived)
        "learning_rate": 0.08,  # Wright's-Law rate — FOAK learning, outside ATB CAPEX/FOM scope
        "base_cf": 0.90,  # NREL ATB 2024 CF (not in the committed CAPEX/FOM extract)
        "lifetime_yr": 40,
    },
    "nuclear_large": {  # large LWR. ATB costs new nuclear from 2030 only.
        "capex_per_kw": 8309.0,  # ATB 2024 Moderate Nuclear-Large @2030, 2026$ (derived)
        "fom_per_kw_yr": 190.9,  # ATB 2024 Moderate @2030, 2026$ (derived)
        "learning_rate": 0.03,  # Wright's-Law rate — mature LWR, outside ATB CAPEX/FOM scope
        "base_cf": 0.92,  # NREL ATB 2024 CF (not in the committed CAPEX/FOM extract)
        "lifetime_yr": 60,
    },
    "gas_cc_ccs": {
        # capex/FOM are ATB-derived from ATB 2024's 95 % CCS class @2026 (2026$)
        # — the nearest published new-CCGT-CCS cost to the model's 90 % capture
        # (ATB has no 90 % variant; 95 % is slightly conservative). Keeping the
        # host gas_cc on ATB while gas_cc_ccs stayed on its older-dollar NETL
        # basis made the capture island look nearly free (a ~$700/kW increment
        # vs the NETL/ATB ~$1,500/kW), so both now share one ATB 2026$ basis.
        # The unit's DISPATCH physics (heat-rate penalty, emission rate) still
        # come from CCUS_PARAMS["gas_cc_ccs_90"] (90 % capture) — only the cost
        # basis is ATB's 95 % class.
        "capex_per_kw": 3104.7,  # ATB 2024 Moderate NG CC 95% CCS @2026, 2026$ (derived)
        "fom_per_kw_yr": 71.1,  # ATB 2024 Moderate @2026, 2026$ (derived)
        "learning_rate": 0.10,  # 10% cost reduction per doubling of cumulative deployment.
        # Source: Rubin et al. (2015) "The cost of CO2 capture
        # and storage", Int J Greenhouse Gas Control. Wright's-Law
        # rate, outside the ATB CAPEX/FOM extract's scope; also
        # used by the CCS retrofit screen (shared capture-equipment
        # manufacturing base).
        "base_cf": 0.80,  # Lower than unabated CC (0.85) due to higher MC
        # pushing it later in merit order at low carbon prices.
        # NREL ATB 2024 CF (not in the committed CAPEX/FOM extract).
        "lifetime_yr": 30,  # Same as gas CC host plant.
    },
}

# Measured NEW-BUILD capacity factor by (technology, ISO) — the output a plant
# built on THAT grid actually delivers, against NEW_ENTRY_COSTS[tech]["base_cf"]
# which is ONE national ATB number for every grid (wind 0.38, solar 0.27).
#
# DERIVED by scripts/data/derive_regional_renewable_cf.py from EPA eGRID
# 2022-2024 (data/raw/fleet-egrid), generator level: operating nameplate, the
# generator's own WND/SUN primary fuel, commercial-operation year >= 2018 (the
# new-build cohort, not the installed base), online before the reported year,
# capacity-weighted and pooled across the three vintages. Asserted against the
# derivation by tests/test_regional_renewable_cf.py (rule 23 [R-FROZEN-DERIVE]:
# re-derive ONLY when a new eGRID vintage lands, and cite the data change).
#
# Rows are keyed by REGION, not by balancing authority, and the BA -> region
# mapping is the model's own fleet.models.ISO_TO_BA_CODES with its
# ISO_NERC_REGION_ADMISSION predicate (rule 24 [R-REGISTRY] — the derive script
# reads that registry rather than keeping a second copy). NWPP is why that
# matters: it is a pool of SEVENTEEN balancing authorities, so its 2.96 GW of
# wind (7 BAs) and 3.05 GW of solar (10 BAs) only aggregate correctly through
# the registry. The per-BA spread inside it is real and wide — NEVP solar 0.304
# against PGE 0.172 — which is the argument for pooling the footprint the model
# actually dispatches rather than picking a representative BA.
#
# CFACT is net generation / (nameplate x 8760), so these are NET OF CURTAILMENT
# — deliberately, because the consumer divides an annual cost by DELIVERED MWh
# and a curtailed MWh is neither sold nor abating.
#
# CONSUMER: the marginal-abatement reporting surface only
# (scripts/build_mac_sidecar.py, via compute_lcoe's cf_override). NOT a solve
# input — the LP's own new-entry screen still costs candidates at the national
# base_cf, so no dispatch, no cache key and no keeper moves because this table
# exists. A grid absent for a technology (SOCO wind — no measured fleet) falls
# back to the national base_cf at the consumer.
REGIONAL_RENEWABLE_CF: dict[str, dict[str, float]] = {
    "solar": {
        "CAISO": 0.2709,
        "ERCOT": 0.2409,
        "MISO": 0.2113,
        "NEISO": 0.1755,
        "NWPP": 0.2753,
        "NYISO": 0.1684,
        "PJM": 0.2041,
        "SOCO": 0.2443,
        "SPP": 0.2266,
    },
    "wind": {
        "CAISO": 0.3714,
        "ERCOT": 0.3582,
        "MISO": 0.3988,
        "NEISO": 0.2896,
        "NWPP": 0.3517,
        "NYISO": 0.2840,
        "PJM": 0.3493,
        "SPP": 0.4126,
    },
}


# Capital-recovery period for the marginal-abatement cost basis, years.
#
# NEW_ENTRY_COSTS[tech]["lifetime_yr"] is 30 — ATB's own capital-recovery
# convention and a fair reading of PHYSICAL life. It is NOT the period over
# which a merchant wind or solar project recovers its capital: that is the
# contracted offtake term, and utility-scale wind/solar PPAs are written at
# 15-25 years (Berkeley Lab, "Utility-Scale Solar" and "Land-Based Wind Market
# Report", both reporting a ~20-yr central term; Lazard LCOE+ v18.0 levelizes
# wind and solar over 20 years on the same reasoning). Recovering capital over
# 30 years understates the annual charge a project must actually clear by
# roughly 15 %.
#
# SCOPE: the reporting surface ONLY. The LP's new-entry screen keeps the
# 30-year book life, so this constant changes no dispatch, no build decision
# and no cache key. Changing lifetime_yr itself is a solve-affecting mechanism
# change and needs its own PRECOMMIT + A/B under rule 29 [R-SCREEN].
PPA_COST_RECOVERY_YR: int = 20

# Per-tech capex + learning-rate multipliers for the PB-1 tech-cost
# uncertainty lever (ScenarioConfig.tech_cost_path / tech_cost_percentile,
# docs/handoffs/probability-bounds-plan-2026-07.md §1.1/§2.1), applied to
# NEW_ENTRY_COSTS by config.scenarios.resolve_new_entry_costs. "mid" is 1.0 by
# construction (the pinned ATB 2024 Moderate case is NEW_ENTRY_COSTS' base
# snapshot, so the neutral default is an exact no-op — default runs are
# byte-identical whatever the low/high bounds say).
#
# capex_per_kw low/high are the PUBLISHED-COST LITERATURE ENVELOPE (capacity-
# cost-grounding session 2026-07-19, superseding FF-1E's ATB-internal
# Advanced/Conservative ratios): min/max over every in-envelope, source-
# verified point of {ATB 2024 Advanced/Moderate/Conservative; EIA/Sargent &
# Lundy Jan-2024 capital-cost study; EIA AEO2026 EMM Table 3; Lazard LCOE+
# v18.0 (incl. its CCGT market-quote high case); Brattle 2025 PJM CONE
# report}, each normalized to constant 2026$ (INFLATION_RATE convention),
# divided by the ATB Moderate mid. DERIVED by
# scripts/data/derive_cost_benchmark_envelope.py from the committed ATB
# extract + data/raw/new-build-cost-benchmarks/benchmarks_2026.csv, asserted
# by tests/test_cost_benchmark_envelope.py (rule 23). Rationale: ATB's
# *internal* near-year case spread is degenerate for mature techs (the gas CT
# was 1.0/1.0 — an inert uncertainty lever — and gas CC ±1 %, unable to
# express the 2024-26 turbine-market escalation that Lazard's $2,400-2,600/kW
# CCGT market quotes and the Brattle CONE report document), while the
# cross-source spread is the honest published range. The envelope always
# contains ATB's own three cases, so it can never be narrower than FF-1E's
# basis. Per-source values + links: docs/new-build-cost-methodology-2026-07.md
# §3-4.
#
# learning_rate multipliers are NOT source-derived: ATB publishes cost
# trajectories, not Wright's-Law learning rates, so they keep their documented
# judgment basis — the trajectory-divergence channel of the tech-cost lever, a
# DOF-ledger free parameter. gas_cc_ccs dispatch physics stay NETL-based (see
# NEW_ENTRY_COSTS); its capex envelope spans S&L/AEO2026 CCS points.
TECH_COST_MULTIPLIERS: dict[str, dict[str, dict[str, float]]] = {
    "wind": {
        "low": {
            "capex_per_kw": 0.948,
            "learning_rate": 1.35,
        },  # capex: S&L 2024 onshore $1,489/kW (2023$)
        "mid": {"capex_per_kw": 1.00, "learning_rate": 1.00},
        "high": {
            "capex_per_kw": 1.402,
            "learning_rate": 0.65,
        },  # capex: Lazard v18 onshore high $2,300/kW (2025$)
    },
    "solar": {
        "low": {
            "capex_per_kw": 0.7523,
            "learning_rate": 1.25,
        },  # capex: Lazard v18 utility PV low $1,150/kW (2025$)
        "mid": {"capex_per_kw": 1.00, "learning_rate": 1.00},
        "high": {
            "capex_per_kw": 1.0513,
            "learning_rate": 0.60,
        },  # capex: ATB Conservative/Moderate @2026 (envelope max)
    },
    "gas_cc": {
        "low": {
            "capex_per_kw": 0.5852,
            "learning_rate": 1.5,
        },  # capex: S&L 2024 CC 2x2x1 H-class $868/kW (2023$, NOAK EPC basis)
        "mid": {"capex_per_kw": 1.00, "learning_rate": 1.0},
        "high": {
            "capex_per_kw": 1.6783,
            "learning_rate": 0.5,
        },  # capex: Lazard v18 CCGT market quotes $2,600/kW (2025$, post-2028 COD)
    },
    "gas_ct": {
        "low": {
            "capex_per_kw": 0.6246,
            "learning_rate": 1.5,
        },  # capex: S&L 2024 H-class frame CT $836/kW (2023$)
        "mid": {"capex_per_kw": 1.00, "learning_rate": 1.0},
        "high": {
            "capex_per_kw": 1.0372,
            "learning_rate": 0.5,
        },  # capex: Lazard v18 gas peaking high $1,450/kW (2025$)
    },
    "nuclear_smr": {
        "low": {
            "capex_per_kw": 0.6649,
            "learning_rate": 1.5,
        },  # capex: ATB Advanced/Moderate @2030 (envelope min)
        "mid": {"capex_per_kw": 1.00, "learning_rate": 1.0},
        "high": {
            "capex_per_kw": 1.3141,
            "learning_rate": 0.5,
        },  # capex: ATB Conservative/Moderate @2030 (envelope max)
    },
    "nuclear_large": {
        "low": {
            "capex_per_kw": 0.8497,
            "learning_rate": 1.5,
        },  # capex: ATB Advanced/Moderate @2030 (envelope min)
        "mid": {"capex_per_kw": 1.00, "learning_rate": 1.0},
        "high": {
            "capex_per_kw": 1.8228,
            "learning_rate": 0.5,
        },  # capex: Lazard v18 US nuclear high $14,820/kW (2025$, Vogtle-level)
    },
    "gas_cc_ccs": {
        "low": {
            "capex_per_kw": 0.8131,
            "learning_rate": 1.5,
        },  # capex: S&L 2024 CC+95% capture $2,365/kW (2023$)
        "mid": {"capex_per_kw": 1.00, "learning_rate": 1.0},
        "high": {
            "capex_per_kw": 1.0395,
            "learning_rate": 0.5,
        },  # capex: ATB Conservative/Moderate @2026 (envelope max)
    },
}

# Per-technology real WACC (FF-1E per-tech-WACC OPTION — §3.6). Consumed ONLY
# when ScenarioConfig.per_tech_wacc_enabled is True (default False, in which
# case every tech's LCOE annuity uses the single derived real_discount_rate and
# this table is untouched — byte-identical). Values are NREL ATB 2024 (v3.0.0)
# "WACC Real" (Market financial case) per ATB technology at the tech's base year
# (2026; 2030 for new nuclear — ATB's earliest nuclear year), the same base year
# NEW_ENTRY_COSTS uses. ATB stores WACC per technology (techdetail "*"), scenario
# -invariant; it varies only mildly by year as the tax-credit financing benefit
# phases out. Not in the committed CAPEX/FOM extract (fetch_nrel_atb.py filters
# to CAPEX/Fixed O&M) — extractable by adding "WACC Real" to that script's
# PARAMETERS; the values here were pulled from ATB 2024 for this option.
#
# CAVEAT (why this stays OFF until the FF-2D gate): ATB's Market WACC embeds the
# tax-equity financing benefit of the PTC/ITC, which this model ALSO credits
# separately (ira.compute_dispatch_credits, the solar ITC in compute_lcoe). So
# enabling per-tech WACC on top of the explicit IRA credits risks double-counting
# the credit benefit for wind/solar/nuclear — an interaction the owner resolves
# at FF-2D, not FF-1E.
ATB_TECH_WACC_REAL: dict[str, float] = {
    "wind": 0.050352,  # ATB 2024 WACC Real Market, LandbasedWind @2026
    "solar": 0.042271,  # ATB 2024 WACC Real Market, UtilityPV @2026
    "gas_cc": 0.053585,  # ATB 2024 WACC Real Market, NaturalGas_FE @2026
    "gas_ct": 0.053585,  # ATB 2024 WACC Real Market, NaturalGas_FE @2026
    "gas_cc_ccs": 0.053585,  # ATB 2024 WACC Real Market, NaturalGas_FE @2026
    "nuclear_large": 0.056473,  # ATB 2024 WACC Real Market, Nuclear @2030
    "nuclear_smr": 0.056473,  # ATB 2024 WACC Real Market, Nuclear @2030
    "offshore_wind": 0.051528,  # ATB 2024 WACC Real Market, OffShoreWind @2026
    "geothermal": 0.051520,  # ATB 2024 WACC Real Market, Geothermal @2026
}

# --- Emerging generation technologies -------------------------------------
# Hydrogen turbines, post-combustion CCUS, enhanced geothermal and offshore
# wind. Each enters the model as a Generator (thermal dispatch) reusing the
# existing LP variable structure — no LP formulation change.

# Hydrogen-fired turbine parameters. H2 turbines are thermal generators whose
# fuel cost is DERIVED from renewable LCOE / electrolyzer efficiency (see
# :mod:`market_sim.data.hydrogen`) rather than an exogenous price path.
#
# capex_kw / fom_kw_yr are DERIVED (capacity-cost-grounding session
# 2026-07-19; derive_cost_benchmark_envelope.py::derive_hydrogen_turbines,
# test-asserted): the model's ATB-derived gas CT/CC costs × the AEO2026 EMM
# Table 3 measured H2-turbine premium over the industrial-frame CT
# (capex $1,215/$1,158 = 1.0492; FOM $8.59/$7.18 = 1.1964 — the only
# published US-agency H2-turbine cost found; the old $1,400/$1,800 "NREL ATB
# 2024, BloombergNEF" labels were decorative, ATB carries no H2-turbine
# class). Applying the dimensionless AEO ratios to the ATB gas basis keeps
# the H2-vs-gas entry competition on ONE cost basis — mixing AEO's absolute
# FOM convention (frame CT $7.18/kW-yr) with ATB's ($27.9/kW-yr; different
# maintenance scope) would make H2 artificially cheap against its direct gas
# competitor. Heat rates / VOM / EFOR keep their DOE H2 Turbine Program /
# NETL bases (physics, not the AEO cost table's scope; AEO2026's H2-turbine
# heat rate 8,295 Btu/kWh is recorded in benchmarks_2026.csv for reference).
HYDROGEN_TURBINE_PARAMS: dict[str, dict[str, float]] = {
    "h2_ct": {  # simple-cycle H2 turbine (peaker)
        "heat_rate": 9.5,  # MMBtu/MWh. GE HA specs, DOE H2 Turbine Program 2023
        "vom": 4.0,  # $/MWh. gas CT analog + H2 premium
        "emission_rate_co2": 0.0,  # tCO2/MWh — zero direct CO2 (green H2)
        "nox_rate": 0.00015,  # tons NOx/MWh — H2 burns hot. DOE/NETL 2023
        "eford": 0.06,  # above gas CT — immature fleet. Engineering judgment
        "capex_kw": 1499.0,  # ATB gas_ct × AEO2026 H2/frame-CT capex ratio (derived)
        "fom_kw_yr": 33.4,  # ATB gas_ct FOM × AEO2026 H2/frame-CT FOM ratio (derived)
        "lifetime_yr": 30,
        "learning_rate": 0.10,  # analogy to gas CT maturation
    },
    "h2_ccgt": {  # combined-cycle H2 turbine (mid-merit/baseload)
        "heat_rate": 6.9,  # MMBtu/MWh. DOE H2 Turbine Program 2023
        "vom": 3.5,  # $/MWh. gas CC analog + H2 premium
        "emission_rate_co2": 0.0,
        "nox_rate": 0.00012,  # DOE/NETL 2023
        "eford": 0.06,
        "capex_kw": 1661.2,  # ATB gas_cc × AEO2026 H2/frame-CT capex ratio (derived)
        "fom_kw_yr": 43.2,  # ATB gas_cc FOM × AEO2026 H2/frame-CT FOM ratio (derived)
        "lifetime_yr": 30,
        "learning_rate": 0.10,
    },
}

# Electrolyzer parameters used to derive the hydrogen fuel cost. Not an LP
# variable. Efficiency is MWh_H2 / MWh_electricity (LHV basis) and improves
# linearly between the 2026 base, 2035 and 2045 milestone years.
ELECTROLYZER_PARAMS: dict[str, dict[str, float]] = {
    "pem": {
        "efficiency": 0.65,  # base year. Source: IRENA Green H2 2023
        "efficiency_2035": 0.72,  # DOE Hydrogen Shot targets
        "efficiency_2045": 0.76,  # DOE long-term targets
        "capex_kw": 1200.0,  # $/kW — for LCOH if needed. BNEF 2024
        "learning_rate": 0.18,  # aggressive — early on curve. IRENA 2023
    },
    "alkaline": {
        "efficiency": 0.63,  # Source: IRENA Green H2 2023
        "efficiency_2035": 0.68,
        "efficiency_2045": 0.72,
        "capex_kw": 800.0,
        "learning_rate": 0.12,  # more mature technology. IRENA 2023
    },
}

# MMBtu per MWh — thermodynamic identity, used to convert the derived
# hydrogen electricity cost ($/MWh) into a fuel cost ($/MMBtu).
MMBTU_PER_MWH: float = 3.412

# Approximate heat content of fuel oil, MMBtu per barrel — the bbl<->MMBtu
# conversion for the winter oil-inventory budget (component A of
# docs/multi-iso/neiso-winter-fuel-inventory-plan-2026-07.md), where the
# winter-fuel-inventory datatype records tank/inventory quantities in barrels
# but the LP budget row is in MMBtu (then MWh via heat rate).
# Source: EIA Monthly Energy Review, June 2026, Appendix A, Table A1
# ("Approximate Heat Content of Petroleum and Biofuels"), p.228.
MMBTU_PER_BBL_DISTILLATE: float = 5.825  # No. 2 distillate fuel oil
MMBTU_PER_BBL_RESIDUAL: float = 6.287  # No. 6 residual fuel oil

# Carbon capture, utilization and storage parameters. CCUS is a variant of
# the base gas CC plant: higher heat rate (parasitic capture load), higher
# VOM (solvent costs), reduced emission rate, plus a transport+storage cost
# for the captured CO2. The capture fraction itself is ScenarioConfig.
# ccs_capture_rate (NETL 2022 Case B31B) — a former "capture_rate" key here
# was dead code that silently contradicted any swept ccs_capture_rate, so it
# was deleted per rule 26 (W2-C; ces-ci-crediting-audit-2026-07.md §3.3).
# capex_kw / fom_kw_yr are the OPERATIVE new-build CCS cost (this dict, not
# NEW_ENTRY_COSTS["gas_cc_ccs"], is what capacity._emerging_lcoe screens new CCS
# on). FF-1E reconciled them onto the same ATB 2024 95%-CCS @2026 (2026$) basis
# as the re-derived gas_cc host and NEW_ENTRY_COSTS["gas_cc_ccs"] — leaving them
# on their prior "$2,500/kW / $22/kW-yr" basis while gas_cc rose to ATB 2026$
# made the capture island look nearly free (a ~$900/kW increment vs ATB's
# ~$1,500/kW). test_atb_entry_cost_consistency asserts these equal the
# NEW_ENTRY_COSTS gas_cc_ccs values. The 90 %-capture physics
# (heat_rate_penalty, ccs_capture_rate) and the NETL/CCS-Institute-cited
# adders are unchanged.
CCUS_PARAMS: dict[str, dict[str, float]] = {
    "gas_cc_ccs_90": {  # gas CCGT with 90% post-combustion capture
        "heat_rate_penalty": 1.16,  # ×base CC heat rate — 16% parasitic. NETL 2022 Rev 4, Case B31B
        "vom_adder": 8.0,  # $/MWh — amine solvent, maintenance. NETL 2022
        "co2_transport_storage": 15.0,  # $/tCO2 — pipeline + saline injection. NETL 2022, Gulf Coast
        "capex_kw": 3104.7,  # $/kW installed. ATB 2024 Moderate NG CC 95% CCS @2026, 2026$ (derived)
        "fom_kw_yr": 71.1,  # $/kW-yr. ATB 2024 Moderate NG CC 95% CCS @2026, 2026$ (derived)
        "lifetime_yr": 30,
        "learning_rate": 0.05,  # slow — limited deployment. Global CCS Institute 2024
    },
}

# Enhanced geothermal (EGS) parameters. EGS enters as a thermal generator
# with zero fuel cost and high capacity factor, dispatchable down to
# ``pmin_fraction`` of rated capacity (flexible baseload). Not intermittent.
#
# Cost grounding (capacity-cost-grounding session 2026-07-19, closing the
# FF-1E "ATB EGS classes not in the extract" gap — the four ATB 2024 EGS
# classes are NOW committed, data/raw/nrel-atb part11+):
# * capex_kw $5,000 = the DOE next-generation-geothermal commercial-liftoff
#   cost level (DOE Pathways to Commercial Liftoff: Next-Generation Geothermal
#   Power — 2030 liftoff at ~$5,000/kW, current EGS projects ~$4,500-6,000/kW;
#   primary re-fetch blocked from this environment, benchmarks_2026.csv
#   verified=0 — the old "NREL ATB 2024" label on this value was decorative).
#   ATB 2024's own EGS classes are far higher (NF-EGS Flash $9,492/kW, Deep-
#   EGS Binary $16,168/kW @2026 2026$) but derive from pre-Fervo GETEM
#   assumptions; DOE Liftoff post-dates the 2023-25 measured drilling-cost
#   declines (Utah FORGE / Fervo) and is the more current federal assessment
#   (rule 14 currency). The ATB EGS band is carried as the conservative bound
#   in the benchmark table.
# * fom_kw_yr = ATB 2024 NF-EGS Flash Moderate @2026 (2026$), DERIVED from
#   the committed extract (derive_cost_benchmark_envelope.py::derive_egs_fom,
#   test-asserted) — the cheapest published EGS-class FOM, replacing the
#   indefensible 0.0 ("captured in VOM": $1/MWh ≈ $8/kW-yr vs the $150-208
#   published EGS range). With the DOE capex level this puts the screen LCOE
#   at ~$66/MWh — inside DOE Liftoff's own $60-70/MWh 2030 corridor, a
#   cross-source coherence check documented in the methodology doc §4.
GEOTHERMAL_PARAMS: dict[str, dict[str, float]] = {
    "egs": {
        "capacity_factor": 0.90,  # high availability. DOE GeoVision 2019
        "vom": 1.0,  # $/MWh — minimal, no fuel
        "emission_rate_co2": 0.0,  # zero direct emissions
        "nox_rate": 0.0,
        "eford": 0.05,  # comparable to nuclear. DOE GeoVision 2019
        "pmin_fraction": 0.20,  # turn down to 20% for flexibility. Fervo 2024
        "capex_kw": 5000.0,  # $/kW. DOE Liftoff next-gen geothermal liftoff level
        "fom_kw_yr": 163.4,  # ATB 2024 NF-EGS Flash Moderate @2026, 2026$ (derived)
        "lifetime_yr": 30,
        "learning_rate": 0.15,  # steep — analogous to early solar. Fervo, ARPA-E
        "heat_rate": 0.0,  # no fuel
    },
}

# Offshore wind parameters. A separate renewable category from onshore wind:
# higher and less variable capacity factors, higher costs, distinct zones.
#
# capex_kw / fom_kw_yr are DERIVED from the committed ATB 2024 extract
# (scripts/data/derive_cost_benchmark_envelope.py::derive_offshore_wind,
# asserted by tests/test_cost_benchmark_envelope.py) — the dedicated
# emerging-tech-cost follow-up FF-1E flagged: fixed-bottom = OffShoreWind
# Class3 Moderate @2026; floating = Class12 Moderate @2030 (ATB's earliest
# floating year — the same earliest-published-year convention as new nuclear),
# both in constant 2026$. This replaces the prior hand-set $4,200/$5,500,
# which sat below every 2024-26 published fixed-bottom point and re-armed the
# "anchored to a later, declined ATB year" pattern FF-1E corrected in
# NEW_ENTRY_COSTS. Cross-source envelope (2026$): S&L Jan-2024 monopile
# $3,689/kW (2023$) and AEO2026 EMM $3,711/kW (2025$) sit LOW (pre-cost-crisis
# engineering bases); Lazard v18 spans $3,450-6,550/kW (2025$); ATB Moderate
# @2026 ($6,312) reflects the post-2023 offshore cost reset near Lazard's
# high — an honestly expensive tech that rarely clears the entry screen
# unsubsidized, matching observed US offshore economics. The model's own
# Wright's-Law learning then declines the floating FOAK base with global
# deployment. base_cf / lifetime / learning_rate are not ATB CAPEX/FOM
# quantities and keep their bases (per-ISO CF override structure unchanged).
OFFSHORE_WIND_PARAMS: dict[str, dict[str, float]] = {
    "fixed_bottom": {
        "base_cf": 0.45,  # annual average. NREL ATB 2024
        "capex_kw": 6312.3,  # ATB 2024 Moderate Class3 @2026, 2026$ (derived)
        "fom_kw_yr": 89.7,  # ATB 2024 Moderate Class3 @2026, 2026$ (derived)
        "lifetime_yr": 30,
        "learning_rate": 0.08,  # NREL ATB 2024, IRENA 2024
    },
    "floating": {
        "base_cf": 0.48,  # deeper water, better resource. NREL ATB 2024
        "capex_kw": 10243.8,  # ATB 2024 Moderate Class12 @2030 (earliest), 2026$ (derived)
        "fom_kw_yr": 79.0,  # ATB 2024 Moderate Class12 @2030, 2026$ (derived)
        "lifetime_yr": 30,
        "learning_rate": 0.12,  # steeper — less mature. NREL ATB 2024
    },
}

# Offshore wind hourly-profile derivation parameters. The offshore CF profile
# is derived from the onshore wind profile by a centered rolling-mean smoothing
# window plus a minimum CF floor (see :mod:`market_sim.data.renewables`).
# Source: NREL offshore wind variability studies, Musial et al. 2022.
OFFSHORE_WIND_SMOOTHING_HOURS: int = (
    6  # rolling-mean window — ocean fetch reduces gustiness
)
OFFSHORE_WIND_MIN_CF: float = 0.08  # minimum hourly CF — offshore rarely drops to zero

# Wright's Law reference cumulative installed capacity (GW global).
# Source: IRENA 2025, IEA WEO 2025, IAEA PRIS 2025, BNEF 2025, DOE LDES.
WRIGHT_REFERENCE_GW: dict[str, float] = {
    "wind": 1150.0,  # was 1020. IRENA 2025.
    "solar": 1800.0,  # was 1420. IRENA 2025.
    "li_ion": 130.0,  # was 90. BNEF 2025.
    "gas_cc": 1220.0,  # was 1200. IEA WEO 2025.
    "nuclear": 445.0,  # was 440. IAEA PRIS 2025.
    "nuclear_smr": 445.0,  # shares global nuclear fleet
    "nuclear_large": 445.0,
    "iron_air": 1.0,  # was 0.5. DOE LDES.
    "flow_battery": 3.0,  # GW global installed vanadium-redox flow. Source: PNNL 2023,
    # BNEF LDES tracker 2024 (China VRFB buildout dominates).
    "compressed_air": 1.5,  # GW global adiabatic/diabatic CAES — Huntorf, McIntosh,
    # Zhangjiakou, Jintan. Source: NREL ATB 2024, IEA 2024.
    "gas_cc_ccs": 2.0,  # GW global installed power-sector CCS as of 2024.
    # Boundary Dam (0.12 GW), miscellaneous pilots/demos.
    # Petra Nova mothballed 2020, excluded.
    # Source: Global CCS Institute Global Status Report 2024.
}

# Annual global deployment (GW/yr) by technology, used to project cumulative
# installed capacity for Wright's Law learning curves. These represent the
# worldwide market, not just the modeled ISO.
# Source: IRENA 2025, IEA WEO 2025, BNEF 2025, IAEA 2025.
GLOBAL_ANNUAL_DEPLOYMENT_GW: dict[str, float] = {
    "wind": 130.0,  # was 120. IRENA 2025.
    "solar": 400.0,  # was 350. IRENA 2025.
    "li_ion": 50.0,  # was 30. BNEF 2025.
    "gas_cc": 20.0,  # was 25. IEA WEO 2025.
    "nuclear": 10.0,  # was 8. IAEA 2025.
    "nuclear_smr": 5.0,
    "nuclear_large": 5.0,
    "iron_air": 1.0,  # was 0.5.
    "flow_battery": 0.8,  # GW/yr global VRFB additions. Source: BNEF LDES tracker 2024.
    "compressed_air": 0.3,  # GW/yr global CAES additions. Source: IEA 2024 pipeline.
    "gas_cc_ccs": 1.5,  # GW/yr global CCS additions on power plants.
    # Based on announced project pipeline (DOE OCED awards,
    # UK cluster sequencing, EU Innovation Fund).
    # Optimistic but reflects policy momentum.
    # Source: Global CCS Institute project database 2024.
}

# Annual-average renewable capacity factors (fraction) by ISO and technology.
# Used to rescale the normalized EIA-930 generation distributions into hourly
# capacity-factor profiles.
# Source: EIA Electric Power Monthly 2024, ERCOT CDR, CAISO annual report.
# PJM: wind 0.31 and solar 0.19 are grounded in the PJM 2023 EIA-930 hourly
#   extract — mean wind/solar net generation over the EIA-860 average-online
#   capacity (wind 0.309, solar 0.121 delivered). Wind is taken at the
#   measured 0.31 (EIA-930 and EIA-923 both report ~28-29 TWh). Solar is set
#   to the physical utility-PV value 0.19 (matching EIA-923's 14.3 TWh)
#   rather than the EIA-930 hourly 0.12, because EIA-930 NG:SUN under-reports
#   PJM utility solar; the EIA-930 distribution still supplies the hour-to-hour
#   shape. Source: EIA-930 PJM hourly + EIA-923 2023 net generation.
RENEWABLE_AVG_CF: dict[str, dict[str, float]] = {
    "ERCOT": {"wind": 0.35, "solar": 0.27},
    "CAISO": {"wind": 0.30, "solar": 0.28},
    "PJM": {"wind": 0.31, "solar": 0.19},
    # Tier 3 approximations for the remaining ISOs (forecast-mode inputs;
    # backcasts use measured profiles). Wind from regional fleet averages
    # (EIA EPM by-state utility-scale CFs); solar is the physical
    # utility-PV value for the latitude band. needs-citation: verify
    # against EIA-923 ISO totals before quoting a forecast.
    #
    # EXCEPTION, NYISO solar (nyiso-132, 2026-08-07): no longer Tier 3 — it is
    # MEASURED off NYISO's own market-generator registry, discharging the
    # needs-citation above for that one entry. 2026 Gold Book Table III-2a
    # reports 981.8 GWh over 573.4 MW (15 units) for 2025, and 573.4 MW x
    # 8,760 h x 0.1955 = 982.0 GWh reproduces it to 0.02 %. 2025 is the ONLY
    # admissible year: 2023/2024 read 0.1629/0.1468, contaminated by
    # commissioning ramps (registered capacity 174.4 -> 573.4 MW in 2024, mean
    # month/year-end 0.6800), and 2025 added no PV market generator at all, so
    # it is the one clean read of a mature fleet. The excluded years are the
    # identification, not a preference, and are NOT averaged in.
    # This is the normalization target derive_cf_profile scales the NYISO solar
    # shape to; it pairs with nyiso_solar_market_generator_basis, which makes
    # the registry the capacity basis, so constant and fleet are one
    # population. Zero free parameters (registry energy / registry capacity is
    # an identity). Rule 13 [R-MEASURED] admissible: regenerates from each Gold
    # Book vintage and responds to fleet change. Rule 25 [R-ISO-SCOPE]: NEISO's
    # 0.15 below is NOT covered and keeps its Tier-3 needs-citation.
    # Identification: results/calibration/PREREG-nyiso132-solar-cf-level-2026-08-07.md
    "MISO": {"wind": 0.34, "solar": 0.22},
    "NYISO": {"wind": 0.26, "solar": 0.1955},
    "NEISO": {"wind": 0.30, "solar": 0.15},
    # SPP (registered 2026-09-06, lane SPP-20): Tier 3, DERIVED from two
    # published measurements rather than hand-approximated — EIA-930 SWPP net
    # generation by fuel for 2024 (docs/multi-iso/spp-data-audit.md §3.2:
    # wind 109.758 TWh, solar 1.200 TWh, spike hour excluded) over the mean of
    # the MMU's YE-2023 and YE-2024 nameplate (SOM 2025 Fig. 2-12: wind
    # 33,725 / 34,808 MW -> 34,266.5; solar 484 / 986 MW -> 735) x 8,784 h:
    #   wind  = 109,758,000 / (34,266.5 x 8,784) = 0.3646 -> 0.36
    #   solar =   1,200,000 / (   735.0 x 8,784) = 0.1859 -> 0.19
    # Backcasts use measured profiles and never read this; it is the
    # forecast-mode normalization target. needs-citation in the table's
    # sense: verify against EIA-923 SWPP totals before quoting a forecast
    # (SPP-31 builds calibration_reference.json).
    "SPP": {"wind": 0.36, "solar": 0.19},
    # NWPP (registered 2026-09-14, lane NWPP-20): EIA-930 2024 delivered
    # energy over the seventeen-BA pool frame (wind 34.82 TWh, solar 17.18
    # TWh, Pacific local year) ÷ the mean of the year-end 2023 / 2024 EIA-860
    # nameplate on the WECC-admitted footprint (wind 12,489.8 / 13,422.3 MW;
    # solar PV 6,312.6 / 8,265.8 MW) x 8,760 h -> 0.307 / 0.269 (the SPP
    # construction; PRECOMMIT-nwpp-20 §3.7). Solar's 0.27 is Nevada's: SNV
    # holds 4,175 of the 9,751 MW. Forecast-mode normalization target only;
    # NWPP-31 builds calibration_reference.json.
    "NWPP": {"wind": 0.31, "solar": 0.27},
    # SOCO (registered 2026-09-14, lane SOCO-20): Tier 3, DERIVED from two
    # published measurements by the SPP construction — EIA-930 SOCO ``NG: SUN``
    # net generation for 2024, 10.141 TWh (docs/multi-iso/soco-data-audit.md
    # §3.1), over the mean of the EIA-860 2025 ER operable solar nameplate
    # online by YE-2023 (4,689.9 MW) and YE-2024 (5,484.9 MW) = 5,087.4 MW x
    # 8,784 h:
    #   solar = 10,141,000 / (5,087.4 x 8,784) = 0.2269 -> 0.23
    # THERE IS NO WIND IN THE SOCO FLEET — zero EIA-860 wind generators and
    # ``NG: WND`` identically 0.000 TWh in every year (audit §2.2 / R-12) — so
    # the wind entry is 0.0 and describes an empty class; a forecast wind
    # build for SOCO is blocked at QUEUE_CAP_PER_TECH_GW["SOCO"]["wind"] = 0.0
    # anyway. Backcasts use the measured profile and never read this.
    "SOCO": {"wind": 0.0, "solar": 0.23},
}

# Installed renewable nameplate capacity (MW) by ISO and technology.
# Source: ERCOT CDR Dec 2024, CAISO annual report 2024.
RENEWABLE_INSTALLED_MW: dict[str, dict[str, float]] = {
    "ERCOT": {
        "wind": 42000.0,  # was 40000. Source: ERCOT CDR Dec 2024.
        "solar": 38000.0,  # was 25000. Source: EIA Hourly Grid Monitor Oct 2025.
    },
    # CAISO re-vintaged 2026-08-04 (FFR-4D) from the hand-rounded "CAISO annual
    # report 2024" pair (wind 7000 / solar 22000) to the MEASURED EIA-860 2025
    # Early Release operable nameplate for balancing authority CISO -- the SAME
    # release and the SAME BA-code crosswalk (zone_assignment._ISO_TO_BA_CODE)
    # that STORAGE_BASE_FLEET_MW already cites for PJM/MISO/NYISO/NEISO.
    # Measured as THE SAME OBJECT the model's own backcast path resolves, so the
    # forecast base year continues from where the last measured year ends:
    # data.renewables._eia860_monthly_capacity(iso, fuel, zones, 2025) year-end,
    # i.e. the EIA-860 per-technology schedules (wind/solar operable, status OP),
    # NOT the generators parquet's prime-mover totals. The two agree exactly on
    # wind (6,326.3) and differ on solar (schedule 24,919.2 vs prime-mover PV
    # 23,996.4 -- the solar schedule carries 1,012 CISO rows to the generator
    # file's 1,005). The schedule is the right one BECAUSE it is the one the
    # backcast reads; a forecast base year on a different solar object than the
    # 2025 backcast it follows would step discontinuously at the seam.
    #   wind  = 6,326.3 MW -> 6330 (nearest 10)
    #   solar = 24,919.2 MW -> 24920 (nearest 10)
    # Independent closure check against CAISO's OWN published ledger (2026
    # Summer Loads & Resources Assessment Table 1.1, Net Dependable Capacity):
    # published wind NDC 6,330 MW vs EIA-860 6,326.3 -- agreement to 0.06 %.
    # Solar: published solar 20,459 + hybrid 2,043 = 22,502 MW NDC, below the
    # EIA-860 nameplate as expected (NDC is the post-test, post-derate value).
    # NOTE THE DIRECTION ON WIND: the accurate value is 670 MW LOWER than the
    # estimate, i.e. it makes the CAISO adequacy deficit WORSE. It is adopted
    # anyway -- rule 14 [R-ACCURATE] forbids keeping an estimate because it
    # flatters a residual. Backcast mode is UNAFFECTED: data.renewables already
    # resolves a backcast year's installed capacity from that year's EIA-860
    # month-end total and reads this registry only in forecast mode.
    # See docs/handoffs/ffr-4d-caiso-fleet-vintage-2026-08-04.md sections 3-4.
    "CAISO": {
        "wind": 6330.0,  # EIA-860 2025 ER wind schedule, CISO OP = 6,326.3 MW.
        "solar": 24920.0,  # EIA-860 2025 ER solar schedule, CISO OP = 24,919.2 MW.
    },
    # Tier 3, ~year-end-2024 utility-scale nameplate (BTM excluded).
    # Source: EIA-860 2024 / ISO planning reports, rounded. needs-citation:
    # refresh from the processed EIA-860 parquet before quoting a forecast.
    "PJM": {"wind": 11000.0, "solar": 14000.0},
    "MISO": {"wind": 32000.0, "solar": 7000.0},
    "NYISO": {"wind": 2400.0, "solar": 1500.0},
    "NEISO": {"wind": 1400.0, "solar": 2700.0},
    # SPP (registered 2026-09-06, lane SPP-20): MEASURED by the FFR-4D CAISO
    # construction — EIA-860 2025 Early Release per-technology schedules
    # (eia860_wind_operable / eia860_solar_operable, Status OP), BA code
    # SWPP, the SAME object data.renewables._eia860_monthly_capacity resolves
    # for a backcast year-end, so the forecast base year continues from where
    # the last measured year ends:
    #   wind  = 35,463.4 MW -> 35460 (nearest 10)
    #   solar =  1,441.8 MW ->  1440
    # Closure against SPP's OWN ledger: MMU SOM 2025 Fig. 2-12 nameplate
    # wind 34,808 (YE-2024) / 35,934 (YE-2025), solar 986 / 2,114 — the ER
    # vintage sits between the two year-ends, as it should
    # (docs/multi-iso/spp-data-audit.md §2.3).
    "SPP": {"wind": 35460.0, "solar": 1440.0},
    # NWPP (registered 2026-09-14, lane NWPP-20): EIA-860 2025 Early Release
    # operable schedules on the WECC-admitted seventeen-BA footprint —
    # onshore wind 14,460.3 MW, solar photovoltaic 9,751.3 MW (the audit's
    # 10,051.3 was pre-adjudication and included Pine Forest Solar I's 300.0
    # MW, rejected under ISO_NERC_REGION_ADMISSION; solar thermal 202.2 MW is
    # not in the PV row). By zone: wind NW 6,381 / EAST 4,575 / INLAND 2,148
    # / OR 1,206 / SNV 150; solar SNV 4,175 / EAST 3,048 / INLAND 1,061 / NW
    # 773 / OR 694 (PRECOMMIT-nwpp-20 §3.7).
    "NWPP": {"wind": 14460.0, "solar": 9751.0},
    # SOCO (registered 2026-09-14, lane SOCO-20): MEASURED by the FFR-4D CAISO
    # construction — EIA-860 2025 Early Release per-technology schedules,
    # Status OP, BA code SOCO, the SAME object data.renewables.
    # _eia860_monthly_capacity resolves for a backcast year-end, with the
    # rejected Massachusetts row (0.5 MW, audit §2.6(a)) excluded:
    #   solar = 5,824.4 MW -> 5820 (nearest 10)   [GA 5,000.7 / AL 387.2 /
    #                                               MS 316.5 / FL 120.0]
    #   wind  = 0.0 — the footprint has no wind (audit §2.2 / R-12)
    "SOCO": {"wind": 0.0, "solar": 5820.0},
}

# CAISO TAC-area actual hourly load (data.eia_loader) -> model zone weights.
# PG&E's TAC straddles Path 15, so it is split between NP15 and ZP26. SCE and
# SDG&E sit entirely south of Path 26 (SP15), as does the tiny VEA TAC (~80 MW,
# CAISO's southern-Nevada pocket).
#
# PGE-TAC IS MEASURED (caiso-172, 2026-08-04) — issue #1372 CLOSED. It was
# 0.86/0.14, the last residual-identified member of this table, carried on the
# rule-14 misalignment exception ("no TAC boundary exists at Path 15 to measure
# the split directly"). That premise was true and irrelevant: the exception
# licenses an estimate only when the real data is genuinely misaligned to our
# representation, and CAISO publishes the Path-15 geography itself. The split
# is now derived from published bytes by
# scripts/data/derive_caiso_path15_load_split.py (rule 23 [R-FROZEN-DERIVE] —
# re-derives ONLY when its source bytes change, never against a residual):
#   * OASIS ATL_LDF -- per-pnode Load Distribution Factors inside
#     DLAP_PGAE-APND, CAISO's own published weighting for distributing PG&E LAP
#     load onto nodes (1,668 load pnodes summing to exactly 100.000);
#   * OASIS ATL_PNODE_MAP -- CAISO's authoritative TH_NP15_GEN / TH_ZP26_GEN
#     pnode membership, i.e. the Path-15 / Path-26 boundary as CAISO defines it,
#     which is exactly the boundary this model's NP15<->ZP26 link represents.
# Joined by substation, two-tier (direct substation match; else the node's PG&E
# sub-LAP's dominant hub — SLAP_PGZP and SLAP_PGKN are 100% ZP26, the other
# thirteen ~100% NP15), residue reported and excluded from the normalisation.
# Day-weighted per year over every live effective window, backcast-mean of
# 2023-2025: NP15 0.883951 / ZP26 0.116049 (per-year spread 0.0011). Artifact:
# data/raw/zone-specific-demand/CAISO/CAISO_path15_load_split.{csv,json};
# acceptance 10/10. RECONCILIATION, not identity (rule 14's clause, documented
# as it requires): an LDF is a *typical* distribution factor, so this is a
# MEASURED STATIC scalar replacing an ASSUMED static scalar — the same kind of
# object, identified instead of guessed. It is NOT an hourly NP15/ZP26 load
# series; no such series is published. The survey that found this route and
# walled every alternative (SLD_FCST is TAC-grain under every market run;
# ENE_SLRS's TAC_NORTH spans Path 15; FERC-714 403; CEC boundary-mismatched;
# EIA-930 sub-BA demand-only) is scripts/probes/_caiso172_subtac_load_survey.py,
# committed so the verdict is re-checkable. Rule 13 [R-MEASURED] admissible:
# regenerates for a forward year from published forward bytes and responds to
# changed conditions (Kern/Fresno vs Bay-Area load growth moves it).
# SCE-TAC spans the LA_BASIN/SP15_rest split (SP15 was split into
# LA_BASIN/SDGE/SP15_rest — docs/handoffs/caiso-sp15-split-implementation-scope-2026-07-09.md
# FOUNDATION DECISIONS). w=0.835 is the LCT LA_Basin/(LA_Basin+SP15_rest)
# peak-load ratio: LA_BASIN 0.374 / (LA_BASIN 0.374 + SP15_rest 0.0735) of full
# ISO load (same LCT `peak_load` table used for the zones' static load_share,
# 2023 Table 3.3-7 / 3.2-1) — LCT-sourced, not a tuned weight. SDGE-TAC and
# VEA-TAC map 1:1 onto their own sub-zones (measured, clean).
# MWD-TAC (added caiso-175, 2026-08-05) is the Metropolitan Water District of
# Southern California metered subsystem — the SIXTH CAISO-internal area the live
# OASIS SLD_FCST domain carries. It was missing from
# scripts/data/postprocess_oasis_downloads.CAISO_TACS, so it never reached the
# committed TAC series and had no row here; because load_zonal_shares NORMALISES
# the component TACs to 1.0, its load was not dropped but silently re-apportioned
# PRO RATA across the other four (caiso-173 §C measured the misplacement at
# 0.24-0.30 % of ISO load landing north of Path 15). Measured 2023/2024/2025
# means: 119.1 / 171.6 / 144.1 MW.
#
# IT MAPS 1:1 ONTO SP15_rest, and the assignment is structural, not fitted.
# MWD's CAISO-metered load is the Colorado River Aqueduct pumping chain (Whitsett
# Intake, Gene, Iron Mountain, Eagle Mountain, Hinds) in eastern Riverside/San
# Bernardino County. The CAISO LCT study's own local-area taxonomy carries that
# corridor as `Blythe` / `Parker` — areas DISTINCT from both `LA Basin` and
# `San Diego/Imperial Valley` (data/raw/capacity-deliverability/caiso/caiso.csv)
# — and SP15_rest is defined above as exactly the SP26 residual outside those two
# pockets. The measured load shape corroborates the identification rather than
# assuming it: MWD's hour-of-day CV is 0.005 against 0.115-0.128 for the retail
# TACs (a flat industrial pumping block, not a retail diurnal shape) with a
# summer/winter ratio of 1.50 (water-delivery seasonality). Rule 14 [R-ACCURATE]:
# a measured area replaces the pro-rata estimate of it; rule 5 [R-NO-MAGIC]: the
# 1.0 is a 1:1 area containment, not a tuned split.
CAISO_TAC_ZONE_WEIGHTS: dict[str, dict[str, float]] = {
    # MEASURED: caiso-172 derive, backcast-mean 2023-2025 (see comment above).
    "PGE-TAC": {"NP15": 0.883951, "ZP26": 0.116049},
    "SCE-TAC": {"LA_BASIN": 0.835, "SP15_rest": 0.165},
    "SDGE-TAC": {"SDGE": 1.0},
    "VEA-TAC": {"SP15_rest": 1.0},
    # caiso-175: 1:1 containment, see the module note directly above.
    "MWD-TAC": {"SP15_rest": 1.0},
}

# The MEASURED 3-way PG&E TAC split for the FSNO sub-zonal partition
# (caiso-223 §C: the caiso-172 ATL_LDF construction generalized 3-way over
# DLAP_PGAE, day-weighted 2023-2025, gates 13/13 PASS, two-way control exact
# vs the committed caiso-172 artifact; source
# results/calibration/_caiso223_subzonal_scope.json). Consumed by
# data.eia930.zonal_shares ONLY when ScenarioConfig
# caiso_fsno_subzonal_topology is armed (caiso-224): the hourly PG&E TAC
# share is re-split by exact scalar rescale — NP15/FSNO/ZP26 are three
# proportional copies of the one measured PGE-TAC shape, exactly as the
# 2-way NP15/ZP26 split above is two (no hourly sub-TAC series is published;
# see the CAISO_TAC_ZONE_WEIGHTS note). Frozen derive [R-FROZEN-DERIVE]:
# re-derives only when its source data updates, never against a residual.
CAISO_TAC_ZONE_WEIGHTS_FSNO: dict[str, float] = {
    "NP15": 0.752614,
    "FSNO": 0.132592,
    "ZP26": 0.114794,
}

# NYISO local self-supply floors (transmission.inject_nyiso_local_selfsupply,
# gated on ScenarioConfig.nyiso_local_selfsupply). Per downstate load-pocket
# zone, the fraction of that zone's hourly load that must be met by IN-ZONE
# dispatchable thermal generation. Long Island (zone K) is cable-islanded and
# carries NYISO locational-minimum-installed-capacity (LMIC) / local-reliability
# rules that keep its own gas-steam + peaker fleet running rather than importing
# the full cable rating of cheap NYC gas. The economic LP under-runs the LI
# fleet (model 3.7 vs EIA-923 8.52 TWh, 2023).
#
# RULE-14 BOUNDARY MISMATCH (audit C-17, B-NYI-1, open root-cause issue #1345):
# the published Zone-K requirement is now committed on disk
# (data/raw/capacity-deliverability/nyiso/nyiso.csv, intake PR #1261): LI LCR%
# (value_pu) 1.052 / 1.053 / 1.065 for 2023/24–2025/26 with a Bulk Power
# Transmission (import) limit of only 325 / 275 / 275 MW. That LCR is a
# PEAK-HOUR installed-capacity ratio (local ICAP >= ~105% of LI peak); THIS
# parameter is an ALL-HOURS energy self-supply fraction (frac x hourly demand).
# The two live on different boundaries: substituting the LCR% (~1.05) or the
# TSL-implied peak local fraction ((peak-import)/peak ~= 0.94) into an all-hours
# energy floor would force ~16 TWh/yr of LI generation vs the ~8.5 TWh that is
# physically real (LI imports off-peak, self-supplies near peak) — LESS
# reflective of reality, so a direct scalar re-ground is INADMISSIBLE (rule #14).
# The only scalar that reproduces the realized annual share would need a
# load-duration haircut tuned to the 2023 outcome — the very rule-12 pin C-17
# means to remove. The faithful fix is a MECHANISM change (a peak-capacity / TSL
# constraint from the committed LCR table), tracked in issue #1345. THAT
# MECHANISM NOW EXISTS: ScenarioConfig.nyiso_li_lcr_tsl (default off) caps the
# NYC->Long_Island link at the published locality import limit in the HB14-21
# window (transmission.apply_nyiso_li_tsl_import_cap) and EXCLUDES Long_Island
# from this floor (rule 19 — never stacked). Empirical reconciliation of the
# boundary (CEMS LI hourly gross gen + measured zonal load, 2023-25): measured
# implied LI inflow at the top-100 load hours is 1,493/1,440/1,598 MW vs the
# mechanism's in-window import capability (TSL + 1,200 MW external ties) of
# 1,525/1,475/1,475 MW — the published construction matches the measured
# peak-hour boundary within ~5%. When the flag is OFF this 0.45 value remains
# the legacy path (residual-identified, forecast-risk; DOF ledger S5). The 0.45
# magnitude still approximates the 2023 realized LI self-supply share (~0.48) —
# it is NOT a validated forward driver and MUST NOT be quoted as one.
#
# HOURS NARROWING (floor-rederive 2026-07-05, rule-17/18; NOT a re-level): the
# floor is applied only in the afternoon-evening peak window
# (transmission.NYISO_SELFSUPPLY_FLOOR_HOURS, HB14-21) — the summer
# design-cooling condition the LCR locality requirements are defined at, where
# the LI cable-import constraint physically binds. Applied all-hours it
# force-committed in-pocket LM6000 peaker baseload overnight (D-2:
# nyiso_local_selfsupply forced 1.84/2.87/1.86 TWh of CT_PEAKER, 43/65/42% of the
# class in nyiso-48; C7 off-peak diurnal FAIL) where measured LI CT_PEAKER CF is
# ~0.06 flat and LI net import runs well below its cable ceiling
# (docs/handoffs/nyiso-downstate-reserve-incidence-2026-06.md Finding 4). The
# 0.45 LEVEL is unchanged — only the hours it had no driver for are removed. NYC (zone J) is
# deliberately ABSENT: the diagnostic shows NYC OVER-generates by +11 TWh (it
# cannot import enough, so it self-supplies) — its idle peakers are a
# reserve-scarcity gap (RCPF / mechanism B), not an energy must-run. Tier 3.
# Source: NYISO Locational Minimum ICAP Requirements / LCR reports
# (data/raw/capacity-deliverability/nyiso/nyiso.csv, intake PR #1261); EIA-923
# zone-mapped net generation; docs/nyiso-dispatch-validation-2026-06.md.
NYISO_LOCAL_SELFSUPPLY_FRAC: dict[str, float] = {
    "Long_Island": 0.45,
}


def resolve_reference_price_interface(flag: bool, iso: str) -> bool:
    """Resolve whether ``iso`` runs the reference-price interface.

    ``True`` when the CLI ``--reference-price-interface`` flag is set OR the ISO
    is in :data:`REFERENCE_PRICE_DEFAULT_ISOS` (the per-ISO default-on set). The
    node itself is still gated on the ISO having an ``INTERFACE_NEIGHBORS`` entry
    downstream, so an ISO without neighbors stays byte-identical either way.
    """
    from market_sim.config.interchange_config import REFERENCE_PRICE_DEFAULT_ISOS

    return bool(flag) or iso in REFERENCE_PRICE_DEFAULT_ISOS


# --- PJM transmission-congestion calibration (config.pjm_congestion) ----------
#
# PJM clears as a perfect copper-plate (0.000 zonal LMP spread in all 8760 hours)
# because (1) the priced external star node (PJM_external, IMPORT_NODE_LINKS
# above) wires ~30 GW of *uncongested* transfer to 5 border zones — so the
# dear-east load pockets import directly from one price hub and never pull power
# through the internal west→east lines — and (2) the internal interface TTCs in
# iso_configs._pjm_config are loose Tier-3 order-of-magnitude estimates that
# never bind. Both are fixed with MEASURED PJM data, never values tuned to the
# price/export residual (rules #11/#12).
#
# (1) External-node deliverability envelope. Each PJM_external→border link's
# signed flow is capped, per (month × hour-of-day), at the measured per-border
# net-interchange percentile (import direction up, export direction down) from
# eia_loader.pjm_zonal_interchange_envelope — the same measured tie-flow file the
# IMPORT_NODE_LINKS ratings were read from (PJM import_export_act_sch_interchange,
# data/raw/iso-specific-transmission/). The dominant direction (ComEd/AEP/EMAAC
# export, Dominion import) keeps a generous p95 ceiling the LP clears below; the
# minor direction collapses toward ~0, so the hub can no longer flood the east
# with cheap imports — closing the copper-plate bypass and shrinking the
# over-export toward the measured schedule. A capability envelope (high
# percentile), not the hourly residual, so it stays a forward-reproducible input.
PJM_EXTERNAL_FLOW_PERCENTILE: float = 95.0

# (2) Internal interface TTCs read from the measured PJM transfer-limit postings
# (data/raw/iso-specific-transmission/PJM_<year>_transfer_limits_and_flows.csv,
# pooled 2023-25 median of the per-interface ``transfer_limit`` contingency
# limit). Only interfaces with a confident named-interface mapping AND a value
# materially looser than measured are overridden; the rest keep their config
# estimate (already ≈ measured). Keyed by the model link's (from_zone, to_zone).
#   - AEP_Ohio→Dominion ← "AEP/DOM Post-Contingency"   (median 4054; ≈ config 4069)
#   - West_APS→SWMAAC   ← "AP-South Pre-Contingency"   (median 3932; the dominant
#                          west→east cut — config 4453)
#   - West_APS→Central_PA ← "Bedington-BlackOak"       (median ~1850; config 1947)
#   - ComEd→AEP_Ohio: REMOVED 2026-07-16 (pjm-cong-1). The "50045005" series
#     (median 2900) had been applied here, but PJM Manual 03 §3.8 (Rev 71)
#     defines the 5004/5005 interface as the Keystone–Juniata + Conemaugh–
#     Juniata 500 kV circuits — a western-PA→central-PA corridor cut with no
#     relation to the ComEd boundary (the real ComEd interface, CE-East, is
#     not published in this feed). The mis-mapped override was silently
#     halving the link's 6,000 MW config estimate; the link keeps its config
#     estimate (rule 14: no measured series exists on this boundary).
PJM_MEASURED_INTERNAL_TTC: dict[tuple[str, str], float] = {
    ("PJM_AEP_Ohio", "PJM_Dominion"): 4050.0,
    ("PJM_West_APS", "PJM_SWMAAC"): 3900.0,
    ("PJM_West_APS", "PJM_Central_PA"): 1850.0,
}

# (2b) HOURLY measured internal interface limits (ScenarioConfig.
# pjm_measured_interface_limits — supersedes the static medians above on the
# mapped links; same feed, hourly instead of pooled-median). Model link ->
# the published transfer-limit series (transfer-interface-limits clean
# datatype, names verbatim) whose elementwise MIN is the link's forward
# (west->east) hourly cap; where an interface publishes pre- AND
# post-contingency limits both are listed, since both are
# simultaneously-enforced security limits and the operative capability each
# hour is the tighter one.
#
# Series identity (PJM Manual 03 §3.8 Rev 71, verified 2026-07-16,
# pjm-cong-1): these are PJM's named REACTIVE TRANSFER INTERFACES — each a
# defined 500/345 kV line set whose TLC limit recomputes ~5-min; the feed's
# "Average Western/Central/Eastern" series are the hourly-averaged posted
# limits of the WESTERN/CENTRAL/EASTERN interfaces (NOT cross-interface
# regional means), and "50045005" is the 5004/5005 interface
# (Keystone–Juniata + Conemaugh–Juniata 500 kV, a western-PA→central-PA
# corridor cut).
#
# Crosswalk provenance and reconciliation (CLAUDE.md rule 14 exception
# clause — each static seed's series maps back to it 1:1):
#   - ComEd→AEP_Ohio      ← "50045005": REMOVED 2026-07-16 (pjm-cong-1).
#     Mis-attribution: the iso_configs "the 5004/5005 interface" naming of
#     the ComEd link was wrong (Manual 03 puts both circuits in
#     Pennsylvania); the real ComEd interface (CE-East) is not in the feed,
#     so the link rides its static — no measured series exists on that
#     boundary. Mapping 5004/5005 anywhere else would double-apply the
#     through-PA corridor the Eastern/Central/Western interfaces already
#     carry (rule 19); the series stays in the datatype unmapped.
#   - AEP_Ohio→Dominion   ← "AEP/DOM" (static 4069 = its 2024 mean).
#   - West_APS→SWMAAC     ← "AP-South" (static 4453 = its 2024 post mean).
#     MISALIGNMENT, documented: AP-South is the aggregate western→MAD 500 kV
#     flowgate, one of several parallel paths this 8-zone mesh splits across
#     West_APS→SWMAAC and West_APS→Dominion. It is applied ONLY to the
#     seeded link (West_APS→SWMAAC); West_APS→Dominion keeps its static
#     3,000 MW so the total west→MAD capability is the reconciled
#     measured-plus-static sum, never the single flowgate double-applied.
#   - West_APS→Central_PA ← "Bedington-BlackOak" (static 1947 = 2024 post
#     mean). Published post-contingency limits touch ≤ 0 in 2024-25 outage
#     windows; the consumer clamps the forward bound at 0 (no secure
#     transfer), never a negative bound (which would FORCE counterflow).
#   - AEP_Ohio→West_APS / ATSI→Central_PA / Central_PA→EMAAC ← the
#     "Average Western/Central/Eastern" regional envelopes that seeded their
#     statics (5029/3336/8168 = the 2024 means). MISALIGNMENT, documented:
#     an envelope is a regional mean across several member interfaces, not
#     one flowgate on the link's exact boundary (its measured ``transfers``
#     sign is unreliable for direction checks — Average Central runs
#     "negative" 80-97% of hours); the hourly envelope is still strictly
#     closer to the real capability than the constant it seeded.
# Cleveland is deliberately ABSENT (the N_TO_H pattern in
# ERCOT_GTC_LINK_MAP): it limits imports into the ATSI-Cleveland sub-pocket,
# a strict subset of the PJM_ATSI zone boundary, so applying it to
# AEP_Ohio→ATSI would cap the whole zone at one pocket's limit. SWMAAC→
# EMAAC, SWMAAC→Dominion, West_APS→Dominion and AEP_Ohio→ATSI have no
# published series on their boundary and keep their static estimates.
# Direction sanity (2023-25 measured ``transfers``): AP-South / Bedington-
# BlackOak / AEP-DOM flows are ≥ 98.5% one-directional west→east, matching
# the mapped links' forward orientation; binding (≥ 90% utilization) up to
# 6.5% of hours (BB post, 2025).
# Source: PJM Data Miner 2 transfer_limits_and_flows via
# scripts/data/curate_transfer_interface_limits.py; consumed by
# market_sim.data.transfer_interface_limits.pjm_interface_ttc_hourly.
PJM_INTERFACE_LINK_MAP: dict[tuple[str, str], tuple[str, ...]] = {
    ("PJM_AEP_Ohio", "PJM_Dominion"): ("AEP/DOM Post-Contingency",),
    ("PJM_West_APS", "PJM_SWMAAC"): (
        "AP-South Pre-Contingency",
        "AP-South Post-Contingency",
    ),
    ("PJM_West_APS", "PJM_Central_PA"): (
        "Bedington-BlackOak Pre-Contingency",
        "Bedington-BlackOak Post-Contingency",
    ),
    ("PJM_AEP_Ohio", "PJM_West_APS"): ("Average Western",),
    ("PJM_ATSI", "PJM_Central_PA"): ("Average Central",),
    ("PJM_Central_PA", "PJM_EMAAC"): ("Average Eastern",),
}

# Year-varying NYISO interface transfer limits that change with the AC
# Transmission build-out. The static limits in iso_configs._nyiso_config are
# nominal; an (iso, year) entry here overrides the matching link's TTC for that
# backcast year (run_calibration._apply_iso_year_ttc). Years/links absent here
# keep the static config value.
#
# These are the MEASURED day-ahead TTC the market actually cleared against,
# from NYISO's hour-by-hour ATC/TTC postings for the "CENT EAST" interface
# (MIS ATC_TTC files, mirrored in data/raw/NYISO/ATC_TTC.zip), aggregated
# by scripts/data/derive_nyiso_central_east_ttc.py. They supersede the earlier
# operating-study / Wood Mackenzie estimates (~2,350 pre / ~3,850 post), which
# overstated the operative DAM limit: the posted DAM TTC the dispatch must
# respect runs ~1,750 MW through Nov 2023 and ~2,850 MW from Dec 2023 on — both
# ~1,000 MW below the published "normal" ratings.
#
# NY Transco's "AC Transmission" Segment A (Central-East, Edic–New Scotland /
# Princetown–Rotterdam 345 kV) energized in December 2023, which the postings
# capture as a step from ~1,525-1,950 MW (Jan-Nov 2023) to ~2,725 MW (Dec 2023)
# and ~2,500-3,175 MW across 2024-25. NYISO_INTERFACE_TTC_BY_MONTH carries the
# within-year envelope (12 monthly means per year); _BY_YEAR carries the annual
# mean, used where no monthly table exists for the year.
# UPNY-SENY stays at its static 5,150 MW (it does not bind in the backcast).
#
# BOTH TABLES ARE BACKCAST-ONLY OVERLAYS, and the within-year variation is NOT
# a seasonal rating (nyiso-104, rule 13 [R-MEASURED] classification; D-5 row
# nyiso_central_east_measured_ttc). An earlier revision of this comment claimed
# "a recurring late-summer/shoulder derate"; that is FALSIFIED by the tables
# themselves — across 2024 and 2025, which share one post-upgrade topology, the
# level-normalized monthly shape correlates at only r=+0.21 and the Aug-Nov
# derate is +7.9 % in 2024 but +0.0 % in 2025, with the deepest-derate month
# moving Sep -> Apr. The within-year signal is that year's own realized
# transmission-outage schedule, so it has no forward analogue and must never be
# pushed into a forecast year. The forecast path is not missing anything as a
# result: the LEVEL's forward channel is the transmission-expansion registry
# (data/raw/transmission-expansion/nyiso.csv) over the static 2,850 MW, which is
# itself this series' measured post-upgrade annual mean. See
# scripts/probes/nyiso104_central_east_ttc_classification.py.
# 2018-2022 ADDED 2026-08-14 (nyiso-134), same producer and same recipe: the
# calendar-month mean of the posted CENT EAST "TTC (DAM)" column, rounded to
# 25 MW. Verified before writing — re-deriving 2023/2024/2025 from the postings
# reproduces the committed 1750/2850/2850 and every committed monthly value
# EXACTLY, so the new years rest on the identical construction.
#
# WHY THE GAP MATTERED (defect D-2,
# results/calibration/ASSESSMENT-nyiso134-2022-readiness-2026-08-14.md): both
# appliers in market_sim.pipeline.ttc used to return unchanged for a year with
# no entry, so an out-of-training solve silently fell back to the STATIC
# topology value — 2,850 MW, the POST-upgrade limit. 2022 is a PRE-upgrade year
# (the NY Transco AC Transmission project entered service Dec 2023): its
# measured annual mean is 1,825 MW, so the fallback overstated Central-East
# transfer capability by 1,025 MW (+56 %), and in Nov-2022 — measured 725 MW —
# by 3.9x. That is the ISO's main upstate->downstate congestion path, and
# relieving it suppresses exactly the downstate scarcity C3c measures. The
# appliers now FAIL LOUD rather than no-op, so a future missing year cannot
# repeat this silently.
NYISO_INTERFACE_TTC_BY_YEAR: dict[int, dict[tuple[str, str], float]] = {
    2018: {("Upstate_West", "Capital_Hudson"): 2475.0},
    2019: {("Upstate_West", "Capital_Hudson"): 2475.0},
    2020: {("Upstate_West", "Capital_Hudson"): 2400.0},
    2021: {("Upstate_West", "Capital_Hudson"): 2025.0},
    2022: {("Upstate_West", "Capital_Hudson"): 1825.0},
    2023: {("Upstate_West", "Capital_Hudson"): 1750.0},
    2024: {("Upstate_West", "Capital_Hudson"): 2850.0},
    2025: {("Upstate_West", "Capital_Hudson"): 2850.0},
}

# Measured calendar-month mean DAM TTC (MW) for the Central-East interface, one
# 12-element list (Jan..Dec) per backcast year. Applied per-hour over a single
# backcast year by run_calibration._apply_iso_monthly_ttc, which expands the
# scalar TTC array to (hours, n_links) so the dispatch runs on the measured
# within-year envelope instead of one annual value. Backcast-only (see the
# classification note on _BY_YEAR above). Regenerate with
# scripts/data/derive_nyiso_central_east_ttc.py after refreshing the postings.
NYISO_INTERFACE_TTC_BY_MONTH: dict[int, dict[tuple[str, str], list[float]]] = {
    2018: {
        ("Upstate_West", "Capital_Hudson"): [
            2700.0,
            2625.0,
            2575.0,
            2500.0,
            2350.0,
            2375.0,
            2425.0,
            2400.0,
            2350.0,
            2175.0,
            2575.0,
            2575.0,
        ]
    },
    2019: {
        ("Upstate_West", "Capital_Hudson"): [
            2650.0,
            2650.0,
            2600.0,
            2325.0,
            2300.0,
            2500.0,
            2675.0,
            2650.0,
            2475.0,
            2225.0,
            2175.0,
            2450.0,
        ]
    },
    2020: {
        ("Upstate_West", "Capital_Hudson"): [
            2400.0,
            2400.0,
            2275.0,
            2350.0,
            2400.0,
            2500.0,
            2625.0,
            2575.0,
            2375.0,
            2400.0,
            2150.0,
            2450.0,
        ]
    },
    2021: {
        ("Upstate_West", "Capital_Hudson"): [
            2550.0,
            2400.0,
            1750.0,
            1225.0,
            1475.0,
            2225.0,
            2450.0,
            2625.0,
            1950.0,
            1475.0,
            1550.0,
            2500.0,
        ]
    },
    2022: {
        ("Upstate_West", "Capital_Hudson"): [
            2625.0,
            2575.0,
            1575.0,
            1275.0,
            1125.0,
            2200.0,
            2475.0,
            2425.0,
            1700.0,
            1175.0,
            725.0,
            1975.0,
        ]
    },
    2023: {
        ("Upstate_West", "Capital_Hudson"): [
            1950.0,
            1875.0,
            1550.0,
            1450.0,
            1600.0,
            1900.0,
            1775.0,
            1650.0,
            1550.0,
            1575.0,
            1525.0,
            2725.0,
        ]
    },
    2024: {
        ("Upstate_West", "Capital_Hudson"): [
            3050.0,
            3075.0,
            3000.0,
            2875.0,
            2825.0,
            2750.0,
            2800.0,
            2700.0,
            2525.0,
            2825.0,
            2750.0,
            3075.0,
        ]
    },
    2025: {
        ("Upstate_West", "Capital_Hudson"): [
            3175.0,
            3075.0,
            2725.0,
            2500.0,
            2525.0,
            2925.0,
            3025.0,
            3000.0,
            2850.0,
            2850.0,
            2725.0,
            2900.0,
        ]
    },
}


# MEASURED TOTAL EAST cutset transfer envelope (MW), one 12-element list
# (Jan..Dec) per backcast year for the model's single Upstate_West ->
# Capital_Hudson link. Selected in place of NYISO_INTERFACE_TTC_BY_MONTH when
# ScenarioConfig.nyiso_total_east_cutset_ttc is armed (default OFF); the two
# never stack (rule 19 [R-ONE-MECH] — one seam, apply_iso_monthly_ttc).
#
# WHY (rule 14 [R-ACCURATE], the misalignment exception, VERBATIM): "a single
# GTC that is one of several parallel paths our reduced network collapses into
# one link". The five-zone reduction folds NYISO load zones A-E into
# Upstate_West, so that link IS the A-E -> F+ cutset, whose NYISO name is
# TOTAL EAST. NYISO_INTERFACE_TTC_BY_MONTH caps it at the posted CENT EAST DAM
# TTC, a NESTED SUB-CUTSET of Total East that carries about half its flow
# (2022 means: TOTAL EAST 3,170.7 MW, CENTRAL EAST 1,544.4 MW). Measured on the
# same postings, the CENT EAST cap sits BELOW the measured Total East flow in
# 86.3 / 95.8 / 61.3 / 58.2 % of the hours of 2022 / 2023 / 2024 / 2025 — in
# 2022 it cannot carry 12.261 TWh of the cutset's own measured transfer (mean
# deficit 1,399.6 MW) — so the link separates in nearly every hour and the
# upstate price collapses onto its cheapest offer.
#
# CONSTRUCTION — INHERITED, NOT CHOSEN (rule 21 [R-DOF]: zero free parameters).
# Verbatim the construction already armed for NYISO's own border links by
# nyiso_seam_deliverability_envelope (nyiso-125, matrix cell K): the p90 of the
# directionally-clipped measured transfer within each bin, here the calendar
# month — the bin NYISO_INTERFACE_TTC_BY_MONTH already uses — rounded to 25 MW,
# that table's own rounding. nyiso-125's finer month x hour-of-day bin gives a
# 2022 binding share of 9.85 % against this bin's 10.06 %, i.e. the coarser bin
# costs nothing and keeps one seam.
#
# WHAT THE nyiso-125 IDENTIFICATION REFUSAL DOES NOT REACH: that refusal is on
# the EXTERNAL border envelopes of Capital_Hudson and Upstate_West, where
# SCH - PJ - NY spans the cutset and neither NYISO's P-32 nor PJM's tie file
# separates the legs. TOTAL EAST is a single unambiguous INTERNAL cutset row
# with zero attribution freedom, so no identification choice arises here.
#
# BACKCAST-ONLY, on the identical classification as NYISO_INTERFACE_TTC_BY_MONTH
# above (rule 13 [R-MEASURED]; the forward channel for the level is the
# transmission-expansion registry). Regenerate with
# scripts/data/derive_nyiso_total_east_envelope.py.
NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH: dict[int, dict[tuple[str, str], list[float]]] = {
    2018: {
        ("Upstate_West", "Capital_Hudson"): [
            5225.0,
            4925.0,
            4650.0,
            4350.0,
            3600.0,
            4200.0,
            4450.0,
            4625.0,
            4225.0,
            3550.0,
            4625.0,
            4525.0,
        ]
    },
    2019: {
        ("Upstate_West", "Capital_Hudson"): [
            5375.0,
            4950.0,
            5150.0,
            4250.0,
            4175.0,
            4775.0,
            4875.0,
            4700.0,
            4425.0,
            4150.0,
            4250.0,
            4725.0,
        ]
    },
    2020: {
        ("Upstate_West", "Capital_Hudson"): [
            4375.0,
            4075.0,
            3700.0,
            4250.0,
            4075.0,
            4400.0,
            4325.0,
            4600.0,
            4450.0,
            4275.0,
            4150.0,
            5100.0,
        ]
    },
    2021: {
        ("Upstate_West", "Capital_Hudson"): [
            5075.0,
            5000.0,
            3875.0,
            3250.0,
            4000.0,
            4525.0,
            4900.0,
            4775.0,
            4600.0,
            3600.0,
            3700.0,
            5250.0,
        ]
    },
    2022: {
        ("Upstate_West", "Capital_Hudson"): [
            5425.0,
            5500.0,
            4350.0,
            2650.0,
            3325.0,
            3825.0,
            4275.0,
            4400.0,
            3700.0,
            3150.0,
            2225.0,
            4675.0,
        ]
    },
    2023: {
        ("Upstate_West", "Capital_Hudson"): [
            4775.0,
            4500.0,
            3600.0,
            2975.0,
            3175.0,
            3600.0,
            3650.0,
            3725.0,
            3425.0,
            3250.0,
            3700.0,
            4275.0,
        ]
    },
    2024: {
        ("Upstate_West", "Capital_Hudson"): [
            5550.0,
            4700.0,
            3325.0,
            3325.0,
            3425.0,
            4475.0,
            4600.0,
            3800.0,
            3300.0,
            3625.0,
            4375.0,
            5425.0,
        ]
    },
    2025: {
        ("Upstate_West", "Capital_Hudson"): [
            5575.0,
            5500.0,
            4225.0,
            4025.0,
            4150.0,
            3750.0,
            3675.0,
            3275.0,
            3300.0,
            3100.0,
            4375.0,
            4775.0,
        ]
    },
}


# Crosswalk from ERCOT's published Generic Transmission Constraints (GTCs, the
# stability-limited export interfaces reported in NP6-86 "SCED Shadow Prices
# and Binding Transmission Constraints") onto the reduced 7-zone topology's
# transfer links. Each GTC maps to one or more (from_zone, to_zone) links with
# a share of the GTC limit. Shares follow iso_configs._ercot_config: the single
# aggregate WESTEX (West Texas export) GTC is one boundary that the reduced
# network splits into two parallel links, apportioned in the same ~8:3 ratio
# as the static ttc_mw values (7,300 / 2,700 of the ~10,000 MW measured
# limit-at-bind) — a rule-#14 misalignment reconciliation, documented there.
# PNHNDL (Panhandle export) and EASTEX (the East Texas GTC — "a voltage
# stability limit associated with flows out of the East Texas area", created
# for "transmission outages on the 345kV system in East Texas around Tyler,
# Lufkin and Nacogdoches", ERCOT market notice archive #1557, effective
# 2017-11-02) map 1:1. EASTEX is the model Northeast zone's boundary: the
# zone IS the EAST weather zone (Tyler/Longview/Texarkana/Lufkin).
# N_TO_H is deliberately ABSENT: the single N_TO_H GTC is one of several
# parallel 345 kV North->Houston paths this reduction collapses into one link,
# so its limit alone would understate the interface (see iso_configs).
# Intra-zone GTCs (NE_LOB, VALEXP, NELRIO, RV_RH, TRDWEL, MCCAMY, ...) have no
# representable link in this topology and are ignored by the crosswalk.
# NE_LOB in particular is "North Edinburg - Lobo" — a SOUTH-TEXAS / Rio
# Grande Valley stability corridor ("South Texas wind farms ... along the
# North Edinburg - Lobo 345 kV line", ERCOT GTC Workshop definitions
# 2020-02-24; "Valley Area" in the July-2024 ROS GTC update), and the Valley
# sits inside the model's South zone. Until 2026-08 the name was misread as
# "Northeast lobe" and its series crosswalked to Northeast->North — the
# rule-14 mis-attribution repaired under signed card Z-A (ercot-234;
# docs/FINDING-ercot234-subzonal-survey-nelob-identity-2026-08-24.md).
# Source: ERCOT NP6-86-CD archives via scripts/data/derive_ttc_limits.py;
# ERCOT GTC Workshop "Current Generic Transmission Constraint Definitions"
# (2020-02-24) for the GTC identities.
ERCOT_GTC_LINK_MAP: dict[str, list[tuple[tuple[str, str], float]]] = {
    "PNHNDL": [(("Panhandle", "North"), 1.0)],
    "WESTEX": [
        (("West", "North"), 8.0 / 11.0),
        (("West", "South_Central"), 3.0 / 11.0),
    ],
    "EASTEX": [(("Northeast", "North"), 1.0)],
}

# ERCOT DC-tie physical locations on the reduced 7-zone topology, per EIA-930
# directly-interconnected BA (ercot-231, N1a). ERCOT's five asynchronous ties:
# DC-East (Monticello, ~600 MW) and DC-North (Oklaunion, ~220 MW) to SPP
# ("SWPP"); Railroad DC (~300 MW), Eagle Pass (~36 MW) and Laredo VFT
# (~100 MW) to CFE/CENACE ("CEN"). Ratings are ERCOT's published DC-tie
# operational transfer capabilities ("The ERCOT DC-Tie Operations" guide /
# CDR); zone placement follows the tie substations' physical locations —
# Monticello sits in the EAST weather zone (model Northeast), Oklaunion in
# NORTH (model North), and all three Mexico ties in the far-south border
# (model South). Shares within a neighbor split by nameplate rating
# (SWPP: 600/820 Northeast, 220/820 North; CEN: all South). Used by
# eia930.demand.ercot_tie_zone_interchange under the
# ercot_tie_zonal_interchange flag; measured per-neighbor flows come from the
# EIA-930 BA-to-BA interchange product (data/raw/eia-930-interchange/).
ERCOT_DC_TIE_ZONE_MAP: dict[str, list[tuple[str, float]]] = {
    "SWPP": [("Northeast", 600.0 / 820.0), ("North", 220.0 / 820.0)],
    "CEN": [("South", 1.0)],
}

# Percentile of the per-(month × hour-of-day) measured net-import distribution
# used as each seam's deliverability ceiling. 90 = the upper envelope minus the
# top ~10% transient/loop-flow hours (matching measured_interchange_envelope's
# default and the interface-limit duration-curve convention), keeping headroom
# above the median so the modeled seam price still sets the typical hour. A
# deliverability-headroom choice, NOT tuned to the net-MWh target.
MISO_SEAM_FLOW_PERCENTILE: float = 90.0

# PJM analogue: per-(month × hod) percentile of measured per-neighbor net
# interchange from the PJM tie-line file (aggregated from border zones to
# neighbor level via pjm_zonal_interchange_envelope). Same convention as MISO.
PJM_SEAM_FLOW_PERCENTILE: float = 90.0

# NYISO analogue (nyiso-125): per-(month × hod) percentile of the measured net
# schedule on each border link's OWN external ties, from NYISO's MIS P-32
# "Interface Limits and Flows" posting (data.nyiso_seam_envelope). Same
# DEFINITIONAL convention as MISO/PJM above and as
# eia930.envelopes.measured_interchange_envelope's default — a deliverability-
# headroom choice fixed ex ante, NOT tuned to any NYISO residual, and
# pre-registered as never-swept (PREREG-nyiso125-seam-envelope-2026-08-04 §4.1).
# Rule 25 [R-ISO-SCOPE] is satisfied because only the CONVENTION is shared: the
# capped MW are derived entirely from NYISO's own postings. Sweeping this in
# response to a score would be a rule 1 [R-STRUCT] / rule 11 violation.
NYISO_SEAM_FLOW_PERCENTILE: float = 90.0

# PJM measured-offer-surface family: the season a calendar month belongs to,
# for the within-SEASON tightness conditioning authorized by the owner
# 2026-07-27 (docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md §3,
# executed by pjm-132). A DEFINITIONAL choice, fixed in advance and never
# tuned against a result (rules 20 / 23): summer is PJM's Jun-Sep peak-load
# season (the 5CP window), winter is the Dec-Mar cold season carrying its own
# emergency procedures, and the remainder is shoulder. The split is symmetric
# (4/4/4 months) so no season's bins are structurally thinner than another's.
#
# This is the SAME map pjm-126 pre-registered and committed before any result
# was seen (`scripts/probes/pjm126_midcurve_conditioning_precheck.SEASON_OF_MONTH`,
# commit 9409f7f); it lives here so the two derives and the two solve-time
# seams share ONE definition and cannot drift apart. Moving a boundary is a new
# definitional change and needs its own memo BEFORE any result under the new
# boundaries is seen.
PJM_SEASON_OF_MONTH: dict[int, str] = {
    1: "winter",
    2: "winter",
    3: "winter",
    4: "shoulder",
    5: "shoulder",
    6: "summer",
    7: "summer",
    8: "summer",
    9: "summer",
    10: "shoulder",
    11: "shoulder",
    12: "winter",
}

# ---------------------------------------------------------------------------
# MISO Regional Directional Transfer (RDT) — contract limits, default derate,
# and the Transmission Constraint Demand Curve (TCDC) steps.
# ---------------------------------------------------------------------------
# The RDT is the contractual constraint on scheduled transfers between MISO
# Midwest and MISO South over the contract path across SPP. Contract limits
# are directional and asymmetric. Source: MISO/SPP Joint Operating Agreement
# Attach. A (RDT limits); restated in 2024 MISO State of the Market Report
# §III.B ("limiting physical flows to 3,000 MW Midwest-to-South and 2,500 MW
# South-to-Midwest").
MISO_RDT_CONTRACT_N_TO_S_MW: float = 3000.0
MISO_RDT_CONTRACT_S_TO_N_MW: float = 2500.0

# MISO's standing operating practice derates the modeled RDT limit below the
# contract limit to account for unmodeled physical flows (e.g. regulation
# deployments in the South): "MISO derates the RDT limit to 92 percent of the
# contract limit by default and often by more" (2024 MISO SOM §III.B). The
# default 92% is the published standing policy and the forward-regenerating
# quantity; the deeper condition-driven operator derates (utilization averaged
# 84% of contract when binding in 2024, i.e. ~390 MW below contract — SOM
# §II.E/III.B) are real but hourly-varying with no published series, so this
# constant deliberately UNDER-states binding-hour congestion rather than
# fitting a deeper haircut (rules 5/13: published value, not a residual fit).
MISO_RDT_DEFAULT_DERATE_FRAC: float = 0.92

# RDT Transmission Constraint Demand Curve (TCDC): MISO prices RDT violation
# rather than hard-capping it — "a two-step TCDC for the RDT with a lower step
# at $40 per MWh at the limit and the second step at $500 per MWh starting at
# 102 percent of the modeled limit" (2024 MISO SOM §III.B). Scheduled
# transfers are hard-bounded at the JOA contract limit (the entitlement);
# the TCDC governs pricing between the derated modeled limit and contract.
MISO_RDT_TCDC_STEP1_PRICE: float = 40.0
MISO_RDT_TCDC_STEP2_PRICE: float = 500.0
MISO_RDT_TCDC_STEP2_START_FRAC: float = 1.02

# Reserve Procurement Enhancement (RPE): MISO "models a Reserve Procurement
# Enhancement (RPE) constraint that limits flows between subregions after a
# supply-side contingency and has a single demand value of $200 per MWh"
# (2024 MISO SOM §III.B). It is how MISO enforces the subregional Short-Term
# Reserve requirements "over the Regional Directional Transfer (RDT)
# constraint. The RPE binds when headroom on the RDT plus the available STR
# in the importing subregion is limited" (2024 SOM §II.E). In the 2023-2025
# design the RPE demand value applies ADDITIVELY with the RDT TCDC whenever
# the RDT is in real violation: "when the transfer constraints are violated,
# it often produces subregion-wide price spreads of $700 because the demand
# curve values for the RDT ($500) and the RPE ($200) apply additively, which
# was unintended", and even small violations (the $40 first TCDC step) are
# "overpric[ed] ... by $200 per MWh" (2024 SOM §III.B pp.51-52). The IMM's
# recommendation to cap the combined effect at $500 was NOT implemented in
# the 2023-2025 window (restated in the IMM Summer-2025 quarterly, which
# books $41M of RDT+RPE congestion); if MISO adopts it, date-gate the
# re-anchor to the tariff change (rule 23: cite the data change).
MISO_RPE_DEMAND_VALUE: float = 200.0

# External zone hosting the MISO-South seam's reference-price bands when
# ScenarioConfig.miso_south_seam_split is on: the southern neighbors
# (SOCO/TVA/AECI — MISO_SEAM_DIBA["South"]) are electrically on the SOUTH
# side of the RDT, while the shared MISO_external bus links to all five
# border zones — so a single bus fabricates a free 3,000 MW
# South→external→Midwest wheel that bypasses the RDT contract path (the
# model's only binding internal boundary). Splitting the South seam onto its
# own external zone removes the fabricated bypass. (Same hazard the PJM
# import-node docstring flags; see transmission.extend_with_import_node.)
MISO_SOUTH_EXTERNAL_ZONE: str = "MISO_external_South"

# Anchored SPREAD-ONLY across-unit dispersion graft (miso-180,
# ScenarioConfig.miso_offer_spread_anchored). The anchor rank is the
# model/book distribution crossing rank on the frozen miso-179 H*
# constructions — the last 199-grid rank at which the model's affected-stack
# mc_base quantile sits at or above the eligible book's, identified ONCE by
# the pre-registered rule (PREREG-miso180-anchored-spread-2026-08-23.md §2;
# record results/calibration/_miso180_anchored_spread_precheck.json:
# single crossing, model $56.55 vs book $55.54 at the anchor, guards clear).
# Identified from INPUTS only (frozen demand-side H*, input offer surface,
# measured book) — zero LMP/residual in the path (rule 13); re-identifies
# only when the corpus/artifact updates, with the data change cited
# (rule 23). NEVER swept: an anchor tuned against C3a is the fitted-adder
# rule-1 violation (PREREG §2 anti-sweep clause).
MISO_OFFER_SPREAD_ANCHOR_RANK: float = 0.875
# sha256 of the committed identification artifact the graft consumes
# (data/raw/_validation-source/miso_offer_level_dispersion.json, the
# miso-179 pooled BOOK-ELIG 199-point vector). The apply path hard-errors on
# a mismatch while armed — the graft must never consume a drifted vector
# (rule 24: the parameter surface is pinned, not merely pathed).
MISO_OFFER_SPREAD_ARTIFACT_SHA256: str = (
    "b4e723127de638068cfacae84dd78c911e5c9a322b8738671c0dc1895eefde28"
)

# Exogenous EAC price reference ranges ($/MWh) by resource type, as
# low/mid/high values. Documentation only — these are NOT used as defaults
# (every ScenarioConfig.eac_price_* defaults to 0.0); they give plausible
# ranges for scenario authors setting EAC prices by hand.
EAC_PRICE_REFERENCE: dict[str, dict[str, float]] = {
    "eac_nuclear_zec": {"low": 10.0, "mid": 17.0, "high": 25.0},
    # Source: NY PSC Order, Case 15-E-0302; IL FEJA
    "eac_wind": {"low": 2.0, "mid": 8.0, "high": 15.0},
    # Source: PJM GATS, S&P Global Platts
    "eac_solar": {"low": 2.0, "mid": 10.0, "high": 20.0},
    # Source: PJM GATS, S&P Global Platts
    "eac_offshore_wind": {"low": 20.0, "mid": 30.0, "high": 40.0},
    # Source: NJ BPU OREC orders, NYSERDA
    "eac_geothermal": {"low": 5.0, "mid": 10.0, "high": 15.0},
    # Source: CA CES program, analogy to nuclear ZEC
    "eac_gas_cc_ccs": {"low": 10.0, "mid": 15.0, "high": 25.0},
    # Source: 45Q market + state CES analogy
    "eac_storage": {"low": 0.0, "mid": 5.0, "high": 10.0},
    # Source: limited precedent, modeling assumption
}


# Hour-of-day availability shape (relative, normalized to a mean of 1 at use so the
# enrolled annual-mean level is conserved exactly). Load Resources are large
# industrial facilities, most available to be tripped when they are consuming
# (weekday daytime/evening operating hours) and modestly less so in the deep
# overnight — a deterministic calendar shape, forward-reproducible and tied to no
# measured outcome. HE 01:00 -> 24:00 (index 0 = HE 01:00).
ERCOT_LR_RRS_AVAILABILITY_HOD: tuple[float, ...] = (
    0.92,
    0.92,
    0.92,
    0.92,
    0.92,
    0.95,  # HE 01-06 overnight (lower industrial use)
    1.02,
    1.05,
    1.05,
    1.05,
    1.05,
    1.05,  # HE 07-12 daytime operations
    1.05,
    1.05,
    1.05,
    1.05,
    1.05,
    1.05,  # HE 13-18 daytime/early-evening
    1.05,
    1.05,
    1.02,
    0.98,
    0.95,
    0.93,  # HE 19-24 evening wind-down
)


# Model-wide constants.
STORAGE_TIEBREAKER_EPSILON: float = (
    0.001  # $/MWh — prevents degenerate charge/discharge
)
HOURS_PER_YEAR: int = 8760
START_YEAR: int = 2026
END_YEAR: int = 2050

# Historical weather years available as forecast load + VRE capacity-factor
# shapes. A forecast pins one representative year (ScenarioConfig.weather_year);
# the weather-year ensemble (market_sim.ensemble) draws over a pool and reports
# the distribution. A weather draw is an admissible forecast *input*, not an
# outcome (CLAUDE.md #10), so sampling over it is methodological robustness,
# not a backcast pin.
#
# Cross-ISO default / fallback pool: the common 3-year window every ISO's
# EIA-930 ``<BA> hourly`` extract covers today (data/raw/eia-930-hourly/).
WEATHER_YEAR_POOL: tuple[int, ...] = (2023, 2024, 2025)

# Per-ISO weather-year pool (2026-07 widening, docs/handoffs/probability-bounds-
# plan-2026-07.md §2.1: "intaking more pre-2022 weather years is a cheap
# widening"). Each entry is bounded by *verified* coverage on disk, checked
# end-to-end (not just file presence): the EIA-930 BA hourly extract yields a
# clean, gap-free 8760-hour local-calendar series for demand (data/eia_loader.py
# load_demand), AND market_sim.data.renewables.load_renewable_profiles resolves
# a full wind+solar profile for the year (an ISO whose BA under-reports one
# fuel, e.g. NYISO solar, falls back to the EIA-930 generation-distribution
# parquet, which only reaches back to 2021 -- a year is listed here only if
# every fallback it needs actually covers it). Verified 2026-07-05; see
# docs/weather-pool-coverage-2026-07.md for the full per-ISO/year log and the
# skipped-ISO rationale.
#
# Holdout quarantine (CLAUDE.md rule 22): 2022 and H1-2026 are never added here,
# for any ISO, until that ISO's calibration-complete marker exists.
WEATHER_YEAR_POOL_BY_ISO: dict[str, tuple[int, ...]] = {
    # ERCOT (EIA-930 BA "ERCO"): hourly extract spans 2015-07-01..2026-06-30
    # (data/raw/eia-930-hourly/ERCO hourly.parquet). 2019-2021 verified: clean
    # 8760-hour demand series, NG: WND / NG: SUN both present and nonzero, and
    # load_renewable_profiles resolves end-to-end with no fallback needed.
    "ERCOT": (2019, 2020, 2021, 2023, 2024, 2025),
    # NEISO (BA "ISNE"): hourly extract spans 2015-07-01..2026-05-20. 2019-2021
    # verified the same way as ERCOT (both fuels reported directly, no fallback
    # to the generation-distribution parquet needed). 2020 carries the
    # COVID-19 demand-shape anomaly (a documented multi-percent spring/summer
    # load depression vs. pre-pandemic trend, EIA/FERC 2020 load-impact
    # reporting) -- an admissible historical weather-year input, but flagged so
    # ensemble consumers can weight or exclude it deliberately (see the
    # coverage note).
    "NEISO": (2019, 2020, 2021, 2023, 2024, 2025),
    # NYISO (BA "NYIS"): hourly extract spans 2015-07-01..2026-06-13, but NYIS
    # never separately reports solar generation (all-zero NG: SUN in every
    # year, including the already-supported 2023-2025), so NYISO solar always
    # falls back to the EIA-930 generation-*distribution* parquet
    # (data/raw/eia-930/eia_generation_profiles.parquet), whose own coverage
    # floor is 2021 -- 2019 and 2020 fail end-to-end
    # (market_sim.data.renewables.load_renewable_profiles raises) even though
    # the raw hourly demand extract covers them. Only 2021 is added; 2019/2020
    # stay out until the distribution parquet is rebuilt further back.
    "NYISO": (2021, 2023, 2024, 2025),
    # CAISO (BA "CISO"): api.eia.gov (scripts/data/fetch_eia930_hourly.py) is
    # blocked in this managed sandbox, but the six-month BALANCE bulk archive
    # (www.eia.gov, unblocked) covers 2019-2021 for every BA and was fetched
    # 2026-07-06 (scripts/data/fetch_eia930_balance.py) then folded into the wide
    # hourly extract (scripts/data/extend_eia930_hourly_from_balance.py). 2019-2021
    # verified end-to-end same as ERCOT. The bulk archive's legacy taxonomy
    # doesn't break out geothermal separately (folded into NG: OTH for these
    # three years only; harmless here since load_renewable_profiles reads only
    # NG: WND / NG: SUN) -- see docs/weather-pool-coverage-2026-07.md.
    "CAISO": (2019, 2020, 2021, 2023, 2024, 2025),
    # PJM (BA "PJM"): same BALANCE-bulk backfill as CAISO for the hourly
    # extract, 2026-07-06 (existing 2022+ rows untouched -- dedup keeps the
    # already-committed rows for the handful of overlapping UTC hours at the
    # 2021/2022 boundary). PJM demand now reads the hourly extract directly
    # (eia_loader._load_pjm_hourly_demand, 2026-07-07 -- the legacy
    # demand-profiles series carried a 1-2 h clock lag, zero-hour gaps, and a
    # 2024 interpolation-shaved ~104 GW ridge), so 2019/2020 demand resolves
    # end-to-end and those years are now pool CANDIDATES -- but a year enters
    # this tuple only after the full end-to-end verification protocol
    # (docs/weather-pool-coverage-2026-07.md), which 2019/2020 have not been
    # run through post-rewire; only 2021 is verified.
    "PJM": (2021, 2023, 2024, 2025),
    # MISO (BA "MISO"): same BALANCE-bulk backfill as CAISO, 2026-07-06. MISO's
    # existing extract separately reports NG: BAT (battery); the bulk archive
    # can't split that out for 2019-2021, so those years' battery generation
    # folds into NG: OTH (NaN, not zero, for a true NG: BAT read) -- immaterial
    # to the wind/solar renewables check this pool exists for.
    "MISO": (2019, 2020, 2021, 2023, 2024, 2025),
    # SPP (BA "SWPP"): hourly extract spans 2015-07-01..2026-05-21, 8,760 /
    # 8,784 / 8,760 rows for 2023 / 2024 / 2025 with no calendar gap
    # (docs/multi-iso/spp-data-audit.md §3.1). The three training years were
    # verified END-TO-END at registration (2026-09-06, lane SPP-20): load_demand
    # ("SPP", y) resolves a clean zonal 8760 (the 2023-06-12 21:00 unit-slip
    # hour repaired by _screen_demand_spikes, §3.4) and load_renewable_profiles
    # resolves wind + solar for all three with no fallback. 2019-2021 are
    # present in the extract but have NOT been run through the coverage
    # protocol (docs/weather-pool-coverage-2026-07.md) and are not listed;
    # 2022 and H1-2026 are quarantined for every ISO (rule 22).
    "SPP": (2023, 2024, 2025),
    # NWPP (registered 2026-09-14, lane NWPP-20): the seventeen-member pool
    # frame (data/eia930/frames._pool_hourly_frame) covers 2023-01 -> 2025-12
    # on every member extract landed by NWPP-11 (26,304 UTC hours each, zero
    # gaps). The three training years were verified END-TO-END at
    # registration: load_demand("NWPP", y) resolves a clean zonal (5, 8760)
    # (coincident peaks 49,290 / 52,564 / 50,953 MW reproduced), the served
    # schedule nwpp_net_interchange resolves, and load_renewable_profiles
    # resolves wind + solar for all three with no fallback. 2019-2022 member
    # extracts are not landed (plan §6 row 13 puts the back years after W4).
    "NWPP": (2023, 2024, 2025),
    # SOCO (BA "SOCO"): hourly extract spans 2023-01-01 .. 2025-12-31 UTC,
    # 8,760 / 8,784 / 8,753 local-date rows (docs/multi-iso/soco-data-audit.md
    # §3.1; America/Chicago hour-ending). The three training years were
    # verified END-TO-END at registration (2026-09-14, lane SOCO-20):
    # load_demand("SOCO", y) resolves a zonal 8760 with both demand screens
    # NO-OPS (audit §3.5), the served interchange schedule resolves, and
    # load_renewable_profiles resolves solar (the footprint has no wind).
    # 2025's 8,753 local rows are the UTC-bounded fetch, not missing data
    # (audit §3.2): the loader bridges the seven trailing hours ending 18-24
    # on 2025-12-31 and logs it; the fetch extension is routed (SOCO-11
    # manifest item [4]), so 2025 is listed with that bridge named. 2019-2022
    # are not in the extract.
    "SOCO": (2023, 2024, 2025),
}


def weather_year_pool(iso: str) -> tuple[int, ...]:
    """Return the verified weather-year pool for ``iso``.

    Looks up :data:`WEATHER_YEAR_POOL_BY_ISO`, falling back to the common
    :data:`WEATHER_YEAR_POOL` default for an ISO not yet registered there.
    """
    return WEATHER_YEAR_POOL_BY_ISO.get(iso, WEATHER_YEAR_POOL)


# ---------------------------------------------------------------------------
# Diurnal dry-bulb interpolation anchors (hour-grain temperature input)
# ---------------------------------------------------------------------------
# The curated weather tree carries DAILY TMIN/TMAX only (NOAA GHCN-D style
# extremes); the capability response of a thermal unit is an HOURLY quantity.
# ``data.eia930.weather.iso_zone_hourly_drybulb`` bridges the two with the
# standard climatological two-piece cosine reconstruction: temperature rises on
# a half-cosine from TMIN at the morning minimum to TMAX at the afternoon
# maximum, then falls on a half-cosine to the NEXT day's TMIN.
#
# The anchor hours are the conventional diurnal phase of a mid-latitude
# continental site in LOCAL STANDARD TIME: the minimum sits at/just after
# sunrise and the maximum ~2-3 h after solar noon (the surface-energy-balance
# lag). Source: Parton & Logan (1981), "A model for diurnal variation in soil
# and air temperature", Agricultural Meteorology 23:205-216 -- the reference
# TMIN/TMAX-to-hourly reconstruction, whose fitted air-temperature phase is
# sunrise for the minimum and ~1.5-3 h past solar noon for the maximum; the
# same anchors the FAO-56 / crop-model and TMY weather-generator families use.
#
# These are CLIMATOLOGICAL constants, not fitted parameters: they are set from
# the meteorology literature and then VALIDATED against ISO conduct by
# scripts/data/derive_campd_temp_derate_params.py (which reports the empirical
# best-fit phase as a cross-check), never fitted to a price or volume residual
# (rules 5 [R-NO-MAGIC], 13 [R-MEASURED], 23 [R-FROZEN-DERIVE]).
DIURNAL_TMIN_HOUR: int = 5  # local-standard-time hour of the daily minimum
DIURNAL_TMAX_HOUR: int = 15  # local-standard-time hour of the daily maximum


# ---------------------------------------------------------------------------
# Structural-error prior (PB-3, probability-bounds program)
# ---------------------------------------------------------------------------
# The published emissions band convolves the parametric input band (PB-2) with a
# prior over the model's own dispatch-skill error, fit from the committed D-7
# statistical-mode probes (docs/statistical-mode-results-2026-07.md;
# docs/handoffs/probability-bounds-plan-2026-07.md §3). Statistical mode strips
# every measured backcast overlay but keeps realized annual gas/load/weather, so
# its emissions error is *model error given true inputs* -- exactly the term that
# convolves with the input uncertainty without double-counting. These are
# post-processing parameters (they touch no solve), fit only on the backcast
# years below and echoed into ensemble_meta.json (rule 5, rule 24).

# Backcast years the structural prior is fit on. 2022 and H1-2026 stay under full
# quarantine (CLAUDE.md rule 22) -- the prior is re-fit against them exactly once,
# at the sanctioned out-of-time scoring moment, never before.
STRUCTURAL_PRIOR_FIT_YEARS: tuple[int, ...] = (2023, 2024, 2025)

# Student-t degrees of freedom for the per-ISO structural-error distribution
# (plan §3.2). nu=2 gives fat tails that, together with the small-sample scale
# inflation below, keep the prior *wider* than the plug-in normal -- the honest
# reading when each ISO's bias and noise are estimated from only three years.
STRUCTURAL_PRIOR_STUDENT_T_NU: float = 2.0

# Structural draws per parametric draw in the log-space Monte-Carlo product
# (plan §3.3): each of the n parametric members is paired with K independent
# epsilon draws to build the n*K published-quantile sample.
STRUCTURAL_PRIOR_CONVOLUTION_K: int = 25

# Horizon-widening variance multiplier lambda(h), growing with years-out to cover
# fleet-evolution (capacity-path) error. UNMEASURED until the PP-0.3 capacity
# hindcast supplies a number (plan §3.4 item 1); pinned to 0.0, which makes every
# published band "dispatch-conditional -- excludes fleet-path structural error".
# This is a placeholder awaiting measurement, never a tuned value (rule 1).
STRUCTURAL_PRIOR_HORIZON_LAMBDA: float = 0.0

# Version tag stamped into every fitted prior artifact / ensemble_meta.json so a
# band's structural layer is traceable to the fit that produced it (rule 24).
STRUCTURAL_PRIOR_VERSION: str = "pb3-statmode-d7-2026-07"

# Provenance of the fit inputs: the committed D-7 statistical-mode probe run ids
# (frontend/data/backcast/runs/<id>.js supply the per-year model CO2;
# frontend/data/backcast/bench/<ISO>/<year>.json.gz supply the actual). Frozen
# here so the measured, reproducible source of the prior is auditable and
# re-derives only when those probes update (rule 23), never against a residual.
STATMODE_PROBE_RUNS: dict[str, str] = {
    "ERCOT": "2026-07-04-statmode-d7-probe-ercot32",
    "CAISO": "2026-07-03-caiso-statmode-d-7",
    "PJM": "2026-07-03-pjm-statmode-d-7",
    "NYISO": "2026-07-03-nyiso-statmode-d-7",
    "NEISO": "2026-07-03-neiso-statmode-d-7",
    "MISO": "2026-07-03-miso-statmode-d-7",
    # SPP is DELIBERATELY ABSENT (registered 2026-09-06, lane SPP-20): a row
    # here is a committed D-7 statistical-mode probe run id, and SPP has no
    # registered run of any kind yet. structural_prior iterates this dict,
    # so the prior simply has no SPP leg until a probe exists (SPP-40+).
}

# ISOs where the model prices carbon (CAISO: CA cap-and-trade; NYISO/NEISO:
# RGGI). The R2 measured-rate CO2 basis (PR #1371, fff2c34) moves the merit
# order ONLY where carbon price > 0 -- so the 2026-07-03 statmode probes above
# are solve-stale for these three ISOs (the W3-P1 re-solves own the fix), while
# the carbon-zero ISOs (ERCOT/PJM/MISO) need only a no-solve re-score of the
# committed numbers. Source: docs/handoffs/forecast-validation-program-2026-07.md
# §0/§3.2 (W0-P4 design).
STRUCTURAL_PRIOR_CARBON_PRICED_ISOS: tuple[str, ...] = ("CAISO", "NEISO", "NYISO")


# --- ERCOT reserve-supply & on-line-capacity envelope tables ----------------
# MOVED to config/ercot_envelopes.py (constants split, 2026-07-20).
# All names re-exported at the top of this module.

# --- ERCOT ORDC-only reserve-scarcity pricing (pre-RTC+B design) -------------
# AS-plan hold preference for the ercot_ordc_only_scarcity product families:
# the single shortfall-step penalty ($/MWh) replacing the NYISO-imported
# k×VOLL/n_ramp per-product ladders. NOT a scarcity price — an LP tie-break so
# the measured DAM AS plan is HELD whenever free headroom exists (the award's
# physical withholding) and RELEASES along the ORDC total-reserve curve when
# energy is worth more, which is the ORDC design itself (Nodal Protocols
# §6.5.7.5: RT reserve scarcity prices only via the ORDC; a product-vs-
# capability squeeze triggers RUC commitment, not a price — docs/DIAGNOSIS-
# ercot-june2023-scarcity-formation-2026-07.md §4.2). Same magnitude class as
# the storage degeneracy tiebreaker ε = 0.001 $/MWh (CLAUDE.md rule 9): small
# enough never to reach an energy dual, positive so plan-holding is preferred
# over idle headroom.
ERCOT_AS_PLAN_HOLD_EPS: float = 0.001

# --- ERCOT SWCAP offer-clip dispatch-before-shed tiebreaker ($/MWh) ----------
# The ercot_offer_swcap_clip clip level is voll − this ε, never voll exactly:
# an offer clipped to precisely VOLL is LP-degenerate against the slack
# (shed) column, whose cost IS voll, and the real design breaks that tie in
# dispatch's favor — SCED dispatches every offered MW (all capped at the
# system-wide offer cap) before firm load is shed, which is an EEA emergency
# action, never an economic outcome (Nodal Protocols §6.5.9). Same magnitude
# class as the storage degeneracy tiebreaker ε (CLAUDE.md rule 9
# [R-EPSILON]) — a strict-preference tiebreak, not a fitted value; 0.01
# rather than 0.001 only to sit comfortably above HiGHS dual-feasibility
# tolerance at the $5,000 scale.
ERCOT_SWCAP_SHED_TIEBREAK_EPS: float = 0.01

# --- Federal §45 wind PTC, statutory inflation-adjusted credit ($/MWh) -------
# The IRS-published renewable-electricity production credit for WIND, by
# production (sale) calendar year, for facilities placed in service before
# 2022 — the vintage class that dominates the in-window ERCOT fleet in the
# backcast years. Sources (annual IRS inflation-adjustment notices):
#   2023: 2.8 c/kWh — 88 FR 40406 (2023-13191), IAF 1.8909
#   2024: 2.9 c/kWh — IRS 2024 §45 notice (Holland & Knight 2024-07 summary)
#   2025: 3.0 c/kWh — 90 FR 22213 (2025-09366), IAF 1.9971
# Facilities placed in service after 2021 (IRA §45 five-times rate with
# wage/apprenticeship compliance) publish slightly lower amounts under the
# finer 0.05-cent rounding (2.75 c/kWh in 2023) — a <= $1.5/MWh spread the
# single per-year level deliberately ignores (the pre-2022 vintages carry
# most in-window capacity). Years outside this table fall back to the
# registry's flat ScenarioConfig.ira_ptc_wind. Used ONLY by the
# wind_ptc_vintage_offers dispatch-offer scoping (policy.ira.
# wind_ptc_vintage_dispatch_offer); the capacity-economics screens keep the
# flat ira_ptc_wind convention.
WIND_PTC_STATUTORY_USD_PER_MWH: dict[int, float] = {
    2023: 28.0,
    2024: 29.0,
    2025: 30.0,
}

# =============================================================================
# VOLUNTARY CLEAN-ENERGY DEMAND — the SCN-WS3b scenario axis (forecast-only,
# default-off, publicly anchored; owner ruling S1 2026-09-06 on card D-3).
# =============================================================================
# The design is the SCN-WS3a memo, docs/handoffs/voluntary-clean-demand-design-
# memo-2026-09-05.md ("the memo"), §3 (the volume construction and its per-cell
# provenance table §3.3), Addendum A.1 (the anchors verified over the proxy) and
# box 5 (the levels). Consumed ONLY by policy/voluntary_demand.py, and only when
# ScenarioConfig.voluntary_clean_demand_path != "off" — a backcast/hindcast
# coerces the axis off at the config seam (rule 13 [R-MEASURED]), so nothing
# here can reach a scored run. Every number is a DECLARED what-if level with a
# public citation (rule 5 [R-NO-MAGIC]); nothing is identified against a model
# residual (rule 20 [R-DOF] — the axis is absent from every scored model) and
# nothing is proprietary (memo §1.2, ffr-5b sentence 1 honoured). EVERY LEVEL
# IN THIS REGION IS NOW COMMITTED. The two cells box 5 left owner-set —
# `f_commit` mid and the WTP-ceiling mid level — were carried here labelled
# ILLUSTRATIVE and re-presented as card D-2(b) (FINDING-scn-ws3b-2026-09-06.md
# §4); owner ruling **S9 (2026-09-06), verbatim "Take the placeholders as
# committed"**, committed them at the values already shipped, so the label
# moved and NO NUMBER MOVED (SCN-FIX2). Ruling S3 (card D-2) had already
# committed the rest of the box-5 defaults.
#
# The construction (memo §3.1), per ISO-year:
#   V = s_base(path, y) × E_nonDC(ISO, y) × w_ISO  +  f_commit(path, y) × E_DC(ISO, y)
# with E_DC the energy of the data-centre block the model already builds
# (data.datacenter.datacenter_block_energy_mwh over DATACENTER_ADDITIONS_MW
# × datacenter_load_factor) and E_nonDC the served energy that is not the block,
# both read from the run's own demand AFTER the load layers fold in — so a
# high-DC case and a high-voluntary case are coherent by construction, and the
# growth×DC relocation discipline (memo §3.4) is never double-counted.
#
# EVERY {year: value} table below uses the DATACENTER_ADDITIONS_MW grammar:
# linear between knots, EDGE-HELD outside them (a single knot = held flat).

# The default eligible set — the voluntary RENEWABLE market's set (memo §4.1):
# wind and solar are the LP's zone columns, offshore_wind and geothermal resolve
# to generator columns through FUEL_TYPE_MAP. Hydro and biomass are EXCLUDED
# (the market's dominant certification standard, Green-e Energy, admits only
# new / low-impact hydro and the LP's hydro classes carry no such attribute).
# `offshore_wind` is the memo's one addition to the charter's "wind / solar /
# geothermal" (it is wind the fleet types separately).
#   *** COMMITTED — owner ruling S10 (2026-09-06), card D-3c, verbatim
#   "Ratify the default as built": this set is the ruled default, no longer the
#   memo's recommendation. Every eligible unit is credited; there is no
#   additionality or vintage mask. *** Nuclear and gas_cc_ccs ("carbon-free"
#   programs, memo
#   §4.2) enter ONLY through the labelled ScenarioConfig.voluntary_eligible_fuels
#   override for a named arm, never here — and a gas_cc_ccs listing credits at
#   the indicator 1.0 of the name-tuple form, not the federal row's 0.95.
VOLUNTARY_ELIGIBLE_FUELS_DEFAULT: tuple[str, ...] = (
    "wind",
    "solar",
    "offshore_wind",
    "geothermal",
)

# National voluntary green-power sales as a share of ALL U.S. retail electricity
# sales, by data year — the NREL series the baseline share is read from. Each
# row is the report's own headline (abstract text, read over the proxy from
# OSTI 2026-09-06; the product tables — sales by product and by customer class,
# memo §3.3 rows 6-7 — stay `needs-citation`: docs.nrel.gov does not resolve
# through this environment's proxy).
#   2021: ~244 million MWh, ~8.0 million customers, "about 6% of all U.S. retail
#         electricity sales" — O'Shaughnessy et al., *Status and Trends in the
#         U.S. Voluntary Green Power Market (2021 Data)*, NREL, DOI 10.2172/1992505.
#   2022: ~272 million MWh, ~9.6 million customers, "about 6%" — *(2022 Data)*,
#         NREL, DOI 10.2172/2341527.
#   2023: ~319 million MWh, ~9.7 million customers, "+17% over 2022", "about 44%
#         of non-hydropower renewable energy sales and about 8% of all U.S.
#         retail electricity sales" — O'Shaughnessy, Jena, Salyer, *Status and
#         Trends in the U.S. Voluntary Power Market: 2023 Data*, NREL/TP-6A20-
#         92289, Aug 2025, DOI 10.2172/2584242.
# Provenance record consumed by the derivation tests (the path table below is
# READ from it), never by the resolver.
VOLUNTARY_NATIONAL_SHARE_OF_RETAIL_SALES: dict[int, float] = {
    2021: 0.06,
    2022: 0.06,
    2023: 0.08,
}
VOLUNTARY_NATIONAL_SALES_MWH: dict[int, float] = {
    2021: 244.0e6,
    2022: 272.0e6,
    2023: 319.0e6,
}

# s_base(path, y): the voluntary share of NON-data-centre load (the pre-existing
# market — utility green pricing, competitive suppliers, unbundled RECs, PPAs
# outside data centres, CCAs). Memo box 5, committed by S3: `mid` = the latest
# NREL national share HELD FLAT (2023: 0.08); `low` / `high` = the report
# series' own historical range, i.e. its floor (2021-2022: 0.06) and its
# ceiling (2023: 0.08). NOTE, stated rather than smoothed: the series' ceiling
# IS the latest value, so `high` coincides with `mid` under the box-5
# construction — a growing high path (e.g. the +17 %/yr 2022→2023 trend
# continued) would be an OWNER level under D-2 and is listed for
# re-presentation, never inferred here. Applied uniformly to every ISO's
# non-DC load; the per-ISO re-weighting is VOLUNTARY_BASELINE_ISO_WEIGHT.
VOLUNTARY_BASELINE_SHARE: dict[str, dict[int, float]] = {
    "low": {2023: 0.06},
    "mid": {2023: 0.08},
    "high": {2023: 0.08},
}

# w_ISO: the per-ISO re-weighting of the national share onto that ISO's non-DC
# load. The memo's allocation basis (§3.2) is each ISO's share of U.S.
# COMMERCIAL-sector retail sales (EIA Form 861, state × sector, mapped state →
# ISO on the MISO compliance-region precedent) divided by its share of total
# sales — the voluntary market's buyers are overwhelmingly commercial.
#   *** needs-intake (memo §3.3 row 9): EIA-861 is NOT in data/raw at this
#   commit and `scripts/` is outside every SCN lane's regions, so no curate
#   script could be written here. *** `None` resolves to 1.0 — the national
#   share applied to the ISO's own load, i.e. an allocation by total load
#   share — the disclosed stand-in until the intake lands. A populated cell is
#   the ratio described above (dimensionless, ~1), with its citation.
VOLUNTARY_BASELINE_ISO_WEIGHT: dict[str, float | None] = {
    "ERCOT": None,  # needs-intake (EIA-861 commercial share ÷ total share)
    "CAISO": None,  # needs-intake
    "PJM": None,  # needs-intake
    "MISO": None,  # needs-intake
    "NYISO": None,  # needs-intake
    "NEISO": None,  # needs-intake
    "SPP": None,  # needs-intake — same EIA-861 gap (registered 2026-09-06, SPP-20)
    "NWPP": None,  # needs-intake — same EIA-861 gap (registered 2026-09-14, NWPP-20)
    "SOCO": None,  # needs-intake — same EIA-861 gap (registered 2026-09-14, SOCO-20)
}

# f_commit(path, y): the share of the DC block's energy under a PUBLISHED
# 100 %-clean / carbon-free ANNUAL-matching commitment in year y (memo §3.3 rows
# 11-12; only annual matching is modelled, D-3b deferred 24/7 to the isolated
# scope2-lce-portfolio tool). Commitment anchors (memo Addendum A.1 row 11,
# company sustainability disclosures): Google 24/7 CFE by 2030 (2020 pledge);
# Microsoft "100/100/0" by 2030 (2021); Amazon 100 % annual matching reached
# 2023; Meta 100 % annual matching since 2020 but EXITED RE100 in July 2026.
#   low  = 0.0  — no committed buyer (the box-5 floor S3 committed). A.1 notes
#                 the fraction is NOT monotone (the Meta exit) and argues for a
#                 FALLING low path; that is a D-2 shape question, recorded in
#                 the FINDING, not taken here.
#   high = 1.0  — the whole block committed (box 5, S3).
#   mid  = *** COMMITTED (owner ruling S9, 2026-09-06) *** at the range
#          midpoint, the value shipped under the former ILLUSTRATIVE label —
#          card D-2(b), which box 5 left owner-set and S3 did not reach, was
#          ruled "Take the placeholders as committed", so this is a ruled
#          what-if level (rule 1 [R-STRUCT]) and not an inference. The public
#          anchor the memo names is the hyperscale share of U.S. DC energy in
#          Shehabi et al., LBNL 2024 U.S. Data Center Energy Usage Report (the
#          split IS published — A.1 row 12 — but the PDF is unreachable through
#          this environment's proxy, so it stays `needs-citation`); the memo
#          calls this the weakest-anchored cell in the construction, which the
#          ruling does not change and a reader quoting VOL-MID should carry.
VOLUNTARY_COMMITTED_DC_FRACTION: dict[str, dict[int, float]] = {
    "low": {2026: 0.0},
    "mid": {2026: 0.5},  # committed (owner ruling S9, 2026-09-06), see above
    "high": {2026: 1.0},
}

# w: the buyer's willingness-to-pay CEILING for the clean attribute, real
# 2026$/MWh (REAL_DOLLAR_BASE_YEAR) — the voluntary row's escape price, above
# which the buyer forgoes the attribute (memo §2.1; the ACP analogue of the
# compliance rows). Public range (memo §3.3 row 14): national voluntary
# unbundled RECs $2-7/MWh, cited in-repo at docs/handoffs/ces-ci-crediting-
# audit-2026-07.md §5.2 (anchored to Green-e / Platts public series; bundled-PPA
# premia are proprietary and REFUSED). `low` / `high` are the endpoints of that
# cited range; the range's dollar-year spread is inside its own width, so no
# deflation is applied.
#   mid = *** COMMITTED (owner ruling S9, 2026-09-06) *** — the range midpoint,
#         the value shipped under the former ILLUSTRATIVE label. Box 5 left the
#         ceiling an owner level and S3 did not reach it; card D-2(b) was ruled
#         "Take the placeholders as committed", so the label moved and the
#         number did not. ScenarioConfig.voluntary_wtp_ceiling_usd_per_mwh
#         overrides the path value for a labelled sensitivity.
VOLUNTARY_WTP_CEILING_USD_PER_MWH: dict[str, float] = {
    "low": 2.0,
    "mid": 4.5,  # committed (owner ruling S9, 2026-09-06), see above
    "high": 7.0,
}
