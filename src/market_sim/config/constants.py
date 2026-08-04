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
    AS_REVENUE_PER_KW_YR_BY_ISO,
    AS_SATURATION_REF_GW_BY_ISO,
    CAMPD_BINNING_ISOS,
    CAPACITY_CURVE_ELIGIBLE_BY_ISO,
    CAP_AND_TRADE_PROGRAMS,
    CARBON_PROGRAM_PRICE_PATH_ESCALATION_MULTIPLIER,
    CARB_ALLOWANCE_BUDGET,
    CARB_FLOOR_ESCALATION,
    CARB_FLOOR_PRICE,
    CapAndTradeProgram,
    CapacityDemandCurvePoint,
    DEFAULT_MARKET_DESIGN,
    ERCOT_AS_REVENUE_PER_KW_YR,
    ERCOT_AS_SATURATION_EXPONENT,
    ERCOT_AS_SATURATION_REF_GW,
    FORECAST_POOL_REQUIREMENT_BY_ISO,
    HISTORIC_OUTAGE_OVERLAY_BY_ISO,
    HYDRO_ACCREDITATION_CREDIT_BY_ISO,
    MARKET_DESIGN,
    MARKET_DESIGN_VINTAGES,
    MISOSeasonRBDC,
    MISO_SEASONAL_RBDC,
    MarketDesign,
    MarketDesignVintage,
    NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO,
    NONFOSSIL_ANNOUNCED_HORIZON_YEARS,
    PJM_RGGI_ZONE_SHARE,
    PLANNING_RESERVE_MARGIN_BY_ISO,
    PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO,
    QUEUE_CAP_GW,
    QUEUE_CAP_PER_TECH_GW,
    RENEWABLE_CAPACITY_CREDIT,
    RENEWABLE_CAPACITY_CREDIT_BY_ISO,
    RENEWABLE_ELCC_CURVES_BY_ISO,
    RENEWABLE_NQC_CURVES_BY_ISO,
    RGGI_MEMBER_STATES_BY_YEAR,
    RGGI_RESERVE_ESCALATION,
    RGGI_STATE_CO2_BUDGET,
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
    STORAGE_TECHS,
    STORAGE_TECH_BUILD_SHARE_CAP,
    STORAGE_TECH_POWER_SHARE,
    SeasonalRBDC,
    THERMAL_ACCREDITATION_BASIS_BY_ISO,
    THERMAL_ELCC_CLASS_RATING_BY_ISO,
    _MISO_DAILY_NET_CONE_PER_MW_DAY,
    _MISO_NC_NET_CONE_PER_MW_YR,
    _MISO_RBDC_CAP_X,
    _MISO_RBDC_CURVE,
    _MISO_RBDC_ZERO_X,
    _MISO_VERTICAL_CURVE,
    _MISO_VERTICAL_STEP,
    _NEISO_FCA_CAP_X,
    _NEISO_FCA_CURVE,
    _NEISO_FCA_ZERO_X,
    _NYISO_ICAP_CURVE,
    _NYISO_NYCA_CURVE_LENGTH,
    _PJM_VRR_CURVE,
    _PJM_VRR_CURVE_2027_2028,
    _PJM_VRR_CURVE_2028_2029,
    _miso_seasonal_curve,
    _neiso_fca_vintage_curve,
    _nyiso_icap_vintage_curve,
    evaluate_demand_curve,
    evaluate_renewable_elcc_curve,
    forward_net_cone_anchor,
    resolve_capacity_curve_eligible,
    resolve_capacity_market_clearing,
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

# CCS retrofit heat rate penalty: parasitic load from amine scrubbing + CO2 compression.
# NETL Cost & Performance Baseline Rev 4 (2021): 10-14% for supercritical PC, 12-16% for NGCC.
# Default 12% reflects modern NGCC with optimized heat integration.
# The retrofit heat rate is DERIVED per unit as source_hr × (1 + penalty); it is not a
# fixed bin. At 12% penalty: H-class (6.3) → 7.06, F-class (6.9) → 7.73, older (7.5) → 8.40.
CCS_RETROFIT_HR_PENALTY_REFERENCE: dict[str, object] = {
    "netl_ngcc_range": (0.10, 0.16),
    "default": 0.12,
    "source": "NETL Cost & Performance Baseline for Fossil Energy Plants, Rev 4, 2021",
}

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
    "COAL": 0.40,  # subcritical/supercritical steam — WWSIS-2 40%
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
# an offer_curves.py docstring). The live, dispatch-affecting values are the
# ScenarioConfig.coal_tranche_{1,2,3}_{frac,fuel_passthrough} fields
# (scenarios.py), read directly by data.offer_curves._coal_tranches. A dead
# duplicate of a tunable is exactly the "re-armable answer key" rule 26 warns
# about (editing this list would silently do nothing), so it is removed
# rather than kept in sync by hand.

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
#   MISO:  3.0492 = mean(2.8392, 2.4893, 3.8190) — per-plant EIA-923 monthly
#     level + mean-preserving daily shape.
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
# 2023 application is a declared extrapolation (no 2023 SCED disclosure
# exists) — the margin is fuel-invariant by construction, gated LOYO per-year
# in the ERCOT-137 precommit. Re-derives only with its source disclosure
# (rule 23), via the same derive script; per-ISO, never transferred (rule 25).
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
# 2023 application is a declared extrapolation (no 2023 SCED disclosure
# exists) — the margin is fuel-invariant by construction, gated LOYO per-year
# in the ERCOT-139 precommit exactly as ERCOT-137's was. Re-derives only with
# its source disclosure (rule 23), via
# ``scripts/data/derive_cc_committed_offer_margin.py``. ISOs absent from the
# registry hard-fail when the flag is armed (rule 24 — never a silent
# fallback); ERCOT-identified from ERCOT conduct and never transferred
# (rule 25).
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
# 2023 application is a declared extrapolation (no 2023 SCED disclosure
# exists), gated per-year in the ERCOT-140 precommit §4.1; the ERCOT-138 §H
# same-plants 2025 flip is that precommit's declared identification risk
# (§2.2). Re-derives only with its source disclosure (rule 23), via
# ``scripts/data/derive_coal_peak_offer_margin.py``. ISOs absent from the
# registries hard-fail when the flag is armed (rule 24 — never a silent
# fallback); ERCOT-identified from ERCOT conduct and never transferred
# (rule 25).
COAL_PEAK_OFFER_LEVEL_BY_ISO: dict[str, float] = {
    "ERCOT": 35.1989,
}
COAL_PEAK_OFFER_GAS_HR_BY_ISO: dict[str, float] = {
    "ERCOT": 10.4100,
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
EIA930_PS_SPLIT_COMPLETE_FROM: dict[str, int] = {"NEISO": 2025}

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
    #   CAVEAT (fleet vintage, material for 2018-2021): the CF is measured
    #   against the MODEL fleet's pmax, and the model's NYISO nuclear fleet is
    #   the current 4-reactor EIA-860 snapshot. Indian Point 2 (retired Apr
    #   2020) and 3 (retired Apr 2021) actually ran in 2018-2021 but are absent
    #   from that snapshot, so these CFs anchor the model's 3,326 MW upstate
    #   fleet only — they do NOT restore the ~2,060 MW of retired downstate
    #   nuclear. A 2018-2021 solve is short that capacity regardless of this
    #   overlay; see the register's fleet-statics DEGRADED row.
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
    # (EIA 6115, NH, 1,247 MW) — fleet nameplate 3,355 MW. Pilgrim (EIA 6098,
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
    "NEISO": {
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
            "COAL": {"slope_per_c": 0.0381, "cap": 0.270, "winter_event_share": 0.0018},
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
            "COAL": {"slope_per_c": 0.0204, "cap": 0.077, "winter_event_share": 0.0004},
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
# total-load forecast directly (byte-identical mechanism to before this refresh).
# When the DC block is ON, data.datacenter.add_datacenter_block RELOCATES the DC
# energy out of this rate into the explicit flat block under a 2030
# energy-continuity constraint (energy invariant, only the peak shape flattens),
# so there is NO growth x DC double-count (CX-4 §3.5 / FF-0D audit §1.6). The
# implied organic-ex-DC near rate each ISO leaves after the mid DC block
# relocates is noted per block below (transparency only — it is not a live
# constant; the relocation is computed from the block MW, decoupling-safe).
#
# Near-term era = year <= DEMAND_GROWTH_TRANSITION_YEAR (2030); long-term
# (2031-2050) decelerates as the pipeline matures. The model applies a flat
# hourly scalar, so peak CAGR == energy CAGR: a near rate r reproduces
# base_peak x (1+r)^(year-weather_year). mid = each ISO's published central
# forecast; low/high bracket it on the prior-vintage band ratios re-centred on
# the new mid (the exact published low/high scenario MW-by-year tables are the
# FF-0D audit §7.3 manual downloads — headline central figures are web-confirmed).
# RE-DERIVED 2026-07 (FF-1C, rule 23) from the FF-0D-audit-cited 2025/2026 ISO
# forecast vintages, replacing the stale 2024-vintage values (and the PJM/NYISO/
# NEISO literal "TODO: verify"); see docs/handoffs/ff-inputs-currency-audit-2026-07.md
# §1.1-1.2 and docs/parameter-citations.md.
DEMAND_GROWTH_RATES: dict[str, dict[str, dict[str, float]]] = {
    # ERCOT — 2025 LTLF3 adjusted 2030 peak ~139 GW from the 85.0 GW model 2024
    # base => (139/85)^(1/6)-1 = 8.5%/yr near. A 2026 preliminary LTLF (released
    # 2026-04-15) is the next vintage (FF-0D §7.3 M5). Long 2.5%/yr (decel; no
    # newer long-era figure cited). Implied organic-ex-DC near (mid, after the
    # 37 GW DC block relocates) ~0.6%/yr — ERCOT growth is DC-dominated.
    # Source: ERCOT 2025 Long-Term Load Forecast (LTLF3); FF-0D audit §1.1.
    "ERCOT": {
        "low": {"near": 0.05, "long": 0.015},
        "mid": {"near": 0.085, "long": 0.025},
        "high": {"near": 0.115, "long": 0.04},
    },
    # CAISO — CEC California Energy Demand 2025-2045 (2025 IEPR): 1-in-2 peak
    # 46.1 (2025) -> 52.9 GW (2030) = +2.8%/yr near; 52.9 -> ~68 GW (2040) =
    # +2.5%/yr long. Implied organic-ex-DC near ~1.9%/yr (CAISO growth is mostly
    # electrification; the +1.8 GW DC adder is small). Source: CEC CED 2025-2045
    # / 2025 IEPR; FF-0D audit §1.1.
    "CAISO": {
        "low": {"near": 0.015, "long": 0.015},
        "mid": {"near": 0.028, "long": 0.025},
        "high": {"near": 0.042, "long": 0.035},
    },
    # PJM — 2026 Long-Term Load Forecast Report (posted 2026-01-14): 10-yr summer
    # peak +3.6%/yr (160 -> 222 GW by 2036) near; 20-yr +2.4%/yr (253 GW by 2046)
    # long. Near-term was trimmed on stricter DC vetting. Implied organic-ex-DC
    # near ~-0.5%/yr (PJM's non-DC load is flat-to-declining; essentially all
    # growth is the ~30 GW DC block). Source: PJM 2026 Load Forecast Report;
    # FF-0D audit §1.1.
    "PJM": {
        "low": {"near": 0.020, "long": 0.014},
        "mid": {"near": 0.036, "long": 0.024},
        "high": {"near": 0.060, "long": 0.040},
    },
    # NYISO — 2026 Load & Capacity Data Report ("Gold Book", released April 2026),
    # Table I-1a "NYCA Baseline Energy and Demand Forecasts", Energy-GWh
    # Lower/Baseline/Higher columns. RE-DERIVED 2026-08-03 (FFR-SC) on the
    # EDITION BUMP alone (rule 23 [R-FROZEN-DERIVE]) — the 2025 edition this row
    # previously cited was superseded, and FF-G4 §8-D4 item 3 flagged it stale;
    # no residual was consulted and none moved. The document landed at
    # data/raw/NYISO/2026-Gold-Book-Public.pdf.
    #
    # Basis, now formulaic instead of the FF-1C "~1.8 %/yr" reading (rule 5
    # [R-NO-MAGIC]): each case is the compound annual growth of that column's
    # own published GWh series — near = 2026 -> 2030, long = 2031 -> 2050,
    # matching DEMAND_GROWTH_TRANSITION_YEAR and the identical construction the
    # as-of-vintage registry below already uses for every NYISO row.
    #   low   150,720 -> 149,300 ; 149,510 -> 157,740  => -0.24 % / +0.28 %
    #   mid   152,600 -> 160,160 ; 161,830 -> 205,760  => +1.22 % / +1.27 %
    #   high  153,420 -> 170,180 ; 174,220 -> 251,930  => +2.63 % / +1.96 %
    # Cross-check against the edition's own published CAGR block: baseline
    # energy 2026-31 = 1.18 % and 2026-46 = 1.30 %, bracketing the 1.22/1.27
    # computed here.
    #
    # Two substantive changes beyond the level, both rule 14 [R-ACCURATE]:
    # (1) low/high are now the edition's OWN Lower/Higher Demand series rather
    # than prior-vintage band ratios re-centred on the mid — the "exact
    # published low/high tables" the header comment records as unavailable at
    # FF-1C are in this edition; (2) the low case's near rate is NEGATIVE
    # because the 2026 Gold Book's Lower Demand forecast really does have NY
    # energy declining to 2030 on efficiency/codes (the same sign the 2021
    # vintage carries below — supported, not a defect).
    # Long now slightly EXCEEDS near for the baseline: NY growth accelerates
    # post-2030 on electrification, which the near/long split represents fine.
    # Figures are TOTAL (large-load- and electrification-inclusive), the
    # convention every layer relocates out of exactly once (see
    # data.datacenter.add_load_layers).
    # Source: NYISO 2026 Gold Book, Table I-1a; supersedes FF-0D audit §1.1.
    "NYISO": {
        "low": {"near": -0.0024, "long": 0.0028},
        "mid": {"near": 0.0122, "long": 0.0127},
        "high": {"near": 0.0263, "long": 0.0196},
    },
    # NEISO — ISO-NE 2026 CELT (May 2026): net energy 116,679 (2025) -> 127,660
    # GWh (2035) ~1.0%/yr, winter net peak 20,483 (2026/27) -> 26,411 MW (2035/36)
    # ~2.6%/yr. The single flat scalar cannot carry both (energy vs peak diverge
    # under electrification — a documented limitation, CX-4 §4); mid 1.3%/yr near
    # blends them, long 1.2%/yr. NEISO ships no material DC block (~110 MW, memo
    # deferred), so organic == total. Source: ISO-NE 2026 CELT; FF-0D audit §1.1.
    "NEISO": {
        "low": {"near": 0.007, "long": 0.007},
        "mid": {"near": 0.013, "long": 0.012},
        "high": {"near": 0.022, "long": 0.020},
    },
    # MISO — Sept-2025 Long-Term Load Forecast: peak 121 (2025) -> ~163 GW (2035)
    # = +3.0%/yr; ~3.1%/yr to the 2030 near boundary from the 121.6 GW model 2024
    # base. Long 2.0%/yr (decel post-2035). Replaces the FF-0D-flagged 1%/yr
    # scalar fallback (the single largest demand gap). Implied organic-ex-DC near
    # ~-0.5%/yr (MISO growth is DC-driven; DC ~20% of energy by 2030). Source:
    # MISO 2025 Long-Term Load Forecast; FF-0D audit §1.2.
    "MISO": {
        "low": {"near": 0.018, "long": 0.012},
        "mid": {"near": 0.031, "long": 0.020},
        "high": {"near": 0.045, "long": 0.030},
    },
}

# Year at which demand growth transitions from near-term to long-term rate.
# Source: engineering judgment — data center pipeline matures ~2030.
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
# base year, each cited to its edition and table (rule 5 [R-NO-MAGIC]).
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
#   * near = CAGR from the edition's first forecast year to
#     DEMAND_GROWTH_TRANSITION_YEAR (2030).
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
        # CAISO: MISSING — the 2020/2021-vintage CEC California Energy Demand
        # STATE baseline forms are not reachable from the CEC's current
        # planning-library pages. MANUAL DOWNLOAD (findings doc §4). Left absent
        # rather than back-filled from the CEDU 2022 vintage below, which would
        # be a post-base-year leak.
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
    # ERCOT — large-load queue ~226 GW (Nov 2025) vs 63 GW (end-2024); ~70% is
    # data center; ~77% of large load targets in-service by 2030; 2030 adjusted
    # peak ~138 GW. Source: ERCOT 2025 Report on Existing & Potential Electric
    # System Constraints and Needs; ERCOT Large Load Integration / LFL officer
    # updates. low = no published signed-IA MW subset -> 0 (honest floor);
    # mid = (138 GW 2030 adj. peak - 85.5 GW 2024 record peak) ~= 52.5 GW large
    # load x 0.70 DC ~= 37 GW; high = total credible LFL: 0.70 x 226 GW = 158 GW
    # DC ultimate, 0.77 in-service by 2030 ~= 122 GW.
    "ERCOT": {
        "low": {2024: 0.0, 2030: 0.0},
        "mid": {2024: 0.0, 2030: 37000.0},
        "high": {2024: 0.0, 2030: 122000.0, 2035: 158000.0},
    },
    # PJM — DC-driven peak growth ~30 GW of ~32 GW total 2025->2030; 15-yr summer
    # peak +70 GW to ~220 GW (DC-dominant). Source: PJM 2025 Long-Term Load
    # Forecast Report (published DC decomposition). low = signed-ISA subset MW
    # not separately published -> 0; mid = 30 GW DC by 2030; high = DC-dominant
    # share of the +70 GW 15-yr peak -> ~60 GW DC by 2040.
    "PJM": {
        "low": {2025: 0.0, 2030: 0.0},
        "mid": {2025: 0.0, 2030: 30000.0},
        "high": {2025: 0.0, 2030: 30000.0, 2040: 60000.0},
    },
    # CAISO — CEC 2024 IEPR Data Center Forecast (24-IEPR-03), adopted into
    # California Energy Demand 2024-2040: DC load +1.8 GW by 2030, +4.9 GW by
    # 2040. low = IEPR low/no-DC case = 0; mid = the adopted DC adder; high = IEPR
    # high-DC MW table not yet read -> high := mid (documented limitation, memo
    # §3.1/§10.2; conservative — never overstates the upside).
    "CAISO": {
        "low": {2024: 0.0, 2030: 0.0, 2040: 0.0},
        "mid": {2024: 0.0, 2030: 1800.0, 2040: 4900.0},
        "high": {2024: 0.0, 2030: 1800.0, 2040: 4900.0},
    },
    # NYISO — 2025 Load & Capacity Data Report ("Gold Book") large-load
    # adjustments: 19 large-load projects > 3 GW combined seeking interconnection;
    # > 10 GW targeted in-service by 2031. low = signed subset MW not separately
    # published -> 0; mid = > 3 GW near-firm large-load adjustment; high = > 10 GW
    # total large-load queue by 2031.
    "NYISO": {
        "low": {2025: 0.0, 2031: 0.0},
        "mid": {2025: 0.0, 2031: 3000.0},
        "high": {2025: 0.0, 2031: 10000.0},
    },
    # MISO — Sept-2025 Long-Term Load Forecast publishes an explicit DC
    # decomposition (FF-0D audit §1.4, closing the memo §2.2 "no source" gap),
    # refined 2026-07-21 to the forecast's granular DC PEAK-DEMAND trajectory
    # (replaces the earlier 2027/2030 band approximation and its flat-hold after
    # 2030 — the 8-14 GW band was NAMEPLATE additions, a different, larger metric
    # than the peak-demand basis the block represents): DC peak demand
    # 1.2 GW (2026) -> 20.5 GW (2030) -> 33.5 GW (2046); DC = 20% of MISO energy
    # by 2030 and 25% by 2040. The 20.5 GW 2030 anchor cross-checks the energy
    # share (20.5 GW x 8760 h x 0.85 LF / 0.20 ~= 763 TWh total 2030, ~ the
    # ~774 TWh forecast). low = signed-subset MW not separately published -> 0
    # (floor convention, as PJM/NYISO); mid = the published current-trajectory
    # curve; high = the upper-DC scenario (27 GW by 2030, FF-0D §1.4), extended to
    # 2046 preserving the published 2030 high/mid ratio (33.5 x 27/20.5 ~= 44.1 GW;
    # MISO publishes no granular high beyond 2030). Growth concentrates in the
    # central region (IL/IN/MI) — a DATACENTER_ZONE_SHARE[MISO] siting candidate
    # once a per-zone MW split is published (deferred, see that table's comment).
    # Source: MISO 2025 Long-Term Load Forecast (Dec-2024 whitepaper + Sept-2025
    # update); FF-0D audit §1.2/§1.4.
    "MISO": {
        "low": {2026: 0.0, 2030: 0.0},
        "mid": {2026: 1200.0, 2030: 20500.0, 2046: 33500.0},
        "high": {2026: 1400.0, 2030: 27000.0, 2046: 44100.0},
    },
    # NEISO — ISO-NE 2026 CELT (May 2026) added a large-load (DC/crypto/large-
    # industrial) forecast framework, but its DC quantum is immaterial, and a
    # 2026-07-21 recheck of the CELT large-load deck confirmed it: only two
    # proposed large-load projects are in the formal study phase (<=285 MW total
    # nameplate; the lone NEMA data center is 200 MW nameplate -> 85 MW effective
    # after ISO-NE's milestone derating), contributing ~110 MW to summer/winter
    # peak in the 2030s rising to ~130 MW in the 2040s — <0.6% of the ~26 GW
    # winter peak, and ISO-NE states New England "has not witnessed the scale of
    # data center proposals" seen in other ISOs. Per the "no MATERIAL source =>
    # ship {}" rule this stays {} (=> 0 MW; DC stays implicit in the
    # DEMAND_GROWTH_RATES near era) until a material decomposition lands — a
    # documented deferral, not an omission (FF-0D audit §1.4, P2 low-materiality).
    # 2026-07-21 RE-VERIFICATION (this branch): re-checked the latest published
    # ISO-NE vintages — the 2026 CELT Report (published 2026-05-01) and the
    # fx2026_large_loads Large Load Forecast deck (dated 2026-03-27) are STILL the
    # current vintages; no newer ISO-NE large-load decomposition has been
    # published. The deck's energy leg corroborates the immateriality: large loads
    # consume ~800 GWh/yr over 2030-2035 rising to ~1,000 GWh in the 2040s, i.e.
    # ~0.68% of the ~117 TWh 2025 net energy — like the ~0.5%-of-peak figure, an
    # order of magnitude under the ~1% materiality bar. Deferral CONFIRMED; {}
    # holds (no forward-sourceable MW-by-year DC trajectory to populate; forcing
    # one would violate rule 5/11).
    # Source: ISO-NE 2026 CELT Report (2026-05-01) + Large Load Forecast deck
    # (fx2026_large_loads.pdf, 2026-03-27).
    "NEISO": {},
}

# Per-ISO override of the data-center block's zonal allocation, {iso: {zone:
# share}} summing to 1.0 per ISO (memo §3.3). DEFAULT (ISO absent here) = each
# zone's iso_configs load_share, applied by data.datacenter.datacenter_zone_shares.
# Override ONLY where published queue siting geography differs from the load
# distribution (memo names ERCOT North/West and PJM Dominion skews). PJM carries
# a reconciled override (below); ERCOT and MISO stay on the load_share default
# (their per-zone MW fractions are not yet sourceable — see the per-ISO notes).
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
#   MISO — growth concentrates in the central region (IL/IN/MI) per the 2025 LTLF,
#     a further siting candidate; likewise no per-zone MW fraction sourced ->
#     stays load_share default.
# MISO keeps the load_share default until a per-zone MW table lands (never an
# invented split, memo §3.3 / rule 23).
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
    # NEISO — ISO-NE 2026 CELT (May 2026), the memo §2.2 grounding row: heating
    # electrification (HEF) 7,165 GWh/yr and 5,533 MW of the 2035/36 50/50
    # winter peak; transportation electrification (TEF) 7,074 GWh/yr, 594 MW
    # summer / 1,509 MW winter peak. Named standing source documents: CELT 2026
    # forecast-data workbook; Final 2026 Heat Pump Forecast
    # (heatfx2026final.pdf); Final 2026 Electric Vehicle Forecast
    # (transfx2026final.pdf) — bot-walled manual downloads (memo §8-D4 item 1),
    # so the anchors carry the memo's fetched [F] headline figures; the
    # MW-by-year workbook refines them when the D4-1 intake lands (rule 23
    # [R-FROZEN-DERIVE]: re-derive on source update only, never on a residual).
    #
    # heat_pump: mid-only ({2026: 0, 2035: 7165 GWh}); low/high collapse onto
    # mid until the CELT scenario band is read (the resolver's documented
    # fallback — never an invented band). THIS is the layer that produces the
    # published ISO-NE winter-peaking flip (winter 2035/36) endogenously: its
    # winter-concentrated heating-degree shape grows with the trajectory and
    # the flip emerges from the driver instead of being painted on (memo §4.2).
    # The CELT 5,533 MW winter-peak contribution is RECONCILIATION CONTEXT for
    # the modeled contribution, never a fit target (rule 13 posture, memo §4.4).
    #
    # ev: {} — the TEF ADOPTION anchors are published (7,074 GWh / 594 MW
    # summer / 1,509 MW winter at 2035, recorded here for the intake session),
    # but NO NEISO-specific hourly CHARGING profile has been read from a
    # fetched source (the TEF PDF is bot-walled; NREL EFS profiles are the D4-7
    # intake). A shape we cannot cite is an open blocker, not a parameter
    # (rule 5 [R-NO-MAGIC]) — the layer arms only when its profile source
    # lands, so it ships {} rather than half-armed anchors.
    "NEISO": {
        "heat_pump": {
            "mid": {2026: 0.0, 2035: 7165.0},
        },
        "ev": {},
    },
    # PJM — the 2026 Load Forecast Report publishes EV/electrification
    # component attributions, but the component MW-by-year tables are in the
    # bot-walled report PDF/XLSX (memo §2.2 / §8-D4 item 2, audit row M11) —
    # nothing transcribed from memory (rule 5). Ships {} => honest no-op; the
    # PJM shape story (energy growing FASTER than peak, load factor RISING) is
    # carried by the flat DC block already armed via DATACENTER_ADDITIONS_MW —
    # exactly the published direction (memo §2.1), so the absent layers are the
    # smaller residual there.
    "PJM": {"heat_pump": {}, "ev": {}},
    # NYISO — 2026 Gold Book publishes PEAK-MW components (heat pumps +19 GW
    # winter / +2 GW summer by 2050; EV winter ~1.4x summer, charging
    # concentrated 22:00-03:00 peaking ~01:00) but the memo records no annual
    # ENERGY component series [F], and converting peak MW to layer energy needs
    # a load-factor assumption we refuse to invent. {} until the Gold Book
    # energy tables land (memo §8-D4 item 3).
    "NYISO": {"heat_pump": {}, "ev": {}},
    # CAISO — the CEC CED 2025 publishes downloadable 8760 hourly demand
    # forecast files (the planner's own future shape; memo §2.2) — the right
    # CAISO treatment is that intake (D4 item 4), not hand anchors here.
    "CAISO": {"heat_pump": {}, "ev": {}},
    # MISO — 2026 LTLF publishes EV energy (62 TWh of the 426 TWh 20-yr growth)
    # but no heat-pump split and no profile; DC dominates MISO's shape story
    # (its own block above). {} until the D4 item 5 intake.
    "MISO": {"heat_pump": {}, "ev": {}},
    # ERCOT — no published end-use decomposition (large loads are embedded in
    # the hourly LTLF files); growth is DC-dominated and the DC block carries
    # most of the shape story (memo §5.5 — ERCOT is last in the rollout order).
    "ERCOT": {"heat_pump": {}, "ev": {}},
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
    "MISO": {"wind": 0.34, "solar": 0.22},
    "NYISO": {"wind": 0.26, "solar": 0.15},
    "NEISO": {"wind": 0.30, "solar": 0.15},
}

# Installed renewable nameplate capacity (MW) by ISO and technology.
# Source: ERCOT CDR Dec 2024, CAISO annual report 2024.
RENEWABLE_INSTALLED_MW: dict[str, dict[str, float]] = {
    "ERCOT": {
        "wind": 42000.0,  # was 40000. Source: ERCOT CDR Dec 2024.
        "solar": 38000.0,  # was 25000. Source: EIA Hourly Grid Monitor Oct 2025.
    },
    "CAISO": {
        "wind": 7000.0,  # unchanged. Source: CAISO annual report 2024.
        "solar": 22000.0,  # was 20000. Source: CAISO annual report 2024.
    },
    # Tier 3, ~year-end-2024 utility-scale nameplate (BTM excluded).
    # Source: EIA-860 2024 / ISO planning reports, rounded. needs-citation:
    # refresh from the processed EIA-860 parquet before quoting a forecast.
    "PJM": {"wind": 11000.0, "solar": 14000.0},
    "MISO": {"wind": 32000.0, "solar": 7000.0},
    "NYISO": {"wind": 2400.0, "solar": 1500.0},
    "NEISO": {"wind": 1400.0, "solar": 2700.0},
}

# CAISO TAC-area actual hourly load (data.eia_loader) -> model zone weights.
# PG&E's TAC straddles Path 15, so it is split between NP15 and ZP26 with
# fixed weights that preserve the prior NP15:ZP26 = 0.43:0.07 ratio (no TAC
# boundary exists at Path 15 to measure the split directly). SCE and SDG&E sit
# entirely south of Path 26 (SP15), as does the tiny VEA TAC (~80 MW, CAISO's
# southern-Nevada pocket). Estimated, not measured — the 0.86/0.14 PG&E split
# has unverified provenance (Tier 3 — calibration; forecast-risk): refine when
# a direct Path-15 sub-TAC load measurement becomes available. This IS the
# rule-14/rule-12 misalignment exception (a single measured TAC-area load
# spanning a boundary — Path 15 — that our zone model splits, with no direct
# way to measure the sub-split): the estimate is legitimately kept, not an
# answer key, per docs/handoffs/scalar-remediation-plan-2026-07.md C-16.
# G-26/issue #1372 status (2026-07-05 B-CAI-1 attempt, per the DOF ledger):
# FERC-714 unreachable (403/502 via proxy), CEC planning-area geography
# boundary-mismatched to Path 15. RE-CHECKED 2026-07-07: CAISO OASIS
# (oasis.caiso.com SingleZip, SLD_FCST/ACTUAL) IS now reachable from this
# environment (a zipped-XML load-forecast file fetched successfully) —
# contradicts the 2026-07-05 "OASIS unreachable" finding and re-opens this
# item as actionable. Not completed here: finding the specific OASIS report
# that publishes NP15/ZP26 sub-TAC zonal load (vs. TAC-area load, which is
# already used), downloading/parsing it, and validating a re-derivation
# against the CAISO keeper is a data-intake project (new frozen derive
# script + re-solve + registration, rule 23), not a documentation edit — left
# for that dedicated session with this reachability finding as the unblock.
# SCE-TAC spans the LA_BASIN/SP15_rest split (SP15 was split into
# LA_BASIN/SDGE/SP15_rest — docs/handoffs/caiso-sp15-split-implementation-scope-2026-07-09.md
# FOUNDATION DECISIONS). w=0.835 is the LCT LA_Basin/(LA_Basin+SP15_rest)
# peak-load ratio: LA_BASIN 0.374 / (LA_BASIN 0.374 + SP15_rest 0.0735) of full
# ISO load (same LCT `peak_load` table used for the zones' static load_share,
# 2023 Table 3.3-7 / 3.2-1) — LCT-sourced, not a tuned weight. SDGE-TAC and
# VEA-TAC map 1:1 onto their own sub-zones (measured, clean).
CAISO_TAC_ZONE_WEIGHTS: dict[str, dict[str, float]] = {
    "PGE-TAC": {"NP15": 0.86, "ZP26": 0.14},
    "SCE-TAC": {"LA_BASIN": 0.835, "SP15_rest": 0.165},
    "SDGE-TAC": {"SDGE": 1.0},
    "VEA-TAC": {"SP15_rest": 1.0},
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
NYISO_INTERFACE_TTC_BY_YEAR: dict[int, dict[tuple[str, str], float]] = {
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

# ERCOT SCED cadence: one SCED execution every ~5 minutes (ERCOT Nodal
# Protocols §6.5.7.1), i.e. 12 intervals per clock hour. Used to time-average
# the per-interval measured GTC limits (gtc-limits clean datatype) onto the
# hourly LP clock: an hour's transfer-energy cap is the mean of its
# per-interval caps, with intervals where the constraint was not in SCED's
# active set standing in at the constraint's measured envelope.
ERCOT_SCED_INTERVALS_PER_HOUR: int = 12

# Crosswalk from ERCOT's published Generic Transmission Constraints (GTCs, the
# stability-limited export interfaces reported in NP6-86 "SCED Shadow Prices
# and Binding Transmission Constraints") onto the reduced 7-zone topology's
# transfer links. Each GTC maps to one or more (from_zone, to_zone) links with
# a share of the GTC limit. Shares follow iso_configs._ercot_config: the single
# aggregate WESTEX (West Texas export) GTC is one boundary that the reduced
# network splits into two parallel links, apportioned in the same ~8:3 ratio
# as the static ttc_mw values (7,300 / 2,700 of the ~10,000 MW measured
# limit-at-bind) — a rule-#14 misalignment reconciliation, documented there.
# PNHNDL (Panhandle export) and NE_LOB (Northeast Texas export lobe) map 1:1.
# N_TO_H is deliberately ABSENT: the single N_TO_H GTC is one of several
# parallel 345 kV North->Houston paths this reduction collapses into one link,
# so its limit alone would understate the interface (see iso_configs).
# Intra-zone GTCs (VALEXP, EASTEX, TRDWEL, MCCAMY, ...) have no representable
# link in this topology and are ignored by the crosswalk.
# Source: ERCOT NP6-86-CD archives via scripts/data/derive_ttc_limits.py; ERCOT
# "The Use of GTCs in ERCOT" (July 2020) for the GTC definitions.
ERCOT_GTC_LINK_MAP: dict[str, list[tuple[tuple[str, str], float]]] = {
    "PNHNDL": [(("Panhandle", "North"), 1.0)],
    "WESTEX": [
        (("West", "North"), 8.0 / 11.0),
        (("West", "South_Central"), 3.0 / 11.0),
    ],
    "NE_LOB": [(("Northeast", "North"), 1.0)],
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
