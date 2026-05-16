"""Physical and economic constants with citation comments."""

# Heat rate efficiency bins (MMBtu/MWh) by fuel class and technology vintage.
# Lower heat rate means higher thermal efficiency.
# Source: EIA Table 8 (Average Tested Heat Rates by Prime Mover and Fuel Type).
HEAT_RATE_BINS: dict[str, dict[str, float]] = {
    "gas_cc": {
        "h_class": 6.3,   # EIA Table 8 — newest H-class combined-cycle units
        "f_class": 6.7,   # EIA Table 8 — F-class combined-cycle units
        "older": 7.5,     # EIA Table 8 — legacy combined-cycle units
    },
    "gas_ct": {
        "aero": 9.0,      # EIA Table 8 — aeroderivative combustion turbines
        "frame": 10.5,    # EIA Table 8 — heavy-frame combustion turbines
        "older": 11.5,    # EIA Table 8 — legacy combustion turbines
    },
    "coal": {
        "supercritical": 8.8,   # EIA Table 8 — supercritical steam units
        "subcritical": 10.0,    # EIA Table 8 — subcritical steam units
        "older": 10.8,          # EIA Table 8 — legacy subcritical steam units
    },
}

# CO2 emission rates (tCO2/MWh), derived from heat rate × fuel emission factor.
# Keyed by fuel class and efficiency bin, mirroring HEAT_RATE_BINS.
# Source: EPA eGRID 2022.
CO2_RATES: dict[str, dict[str, float]] = {
    "gas_cc": {
        "h_class": 0.36,  # EPA eGRID 2022 — H-class combined-cycle units
        "f_class": 0.38,  # EPA eGRID 2022 — F-class combined-cycle units
        "older": 0.43,    # EPA eGRID 2022 — legacy combined-cycle units
    },
    "gas_ct": {
        "aero": 0.51,     # EPA eGRID 2022 — aeroderivative combustion turbines
        "frame": 0.60,    # EPA eGRID 2022 — heavy-frame combustion turbines
        "older": 0.65,    # EPA eGRID 2022 — legacy combustion turbines
    },
    "coal": {
        "supercritical": 0.88,  # EPA eGRID 2022 — supercritical steam units
        "subcritical": 1.00,    # EPA eGRID 2022 — subcritical steam units
        "older": 1.08,          # EPA eGRID 2022 — legacy subcritical steam units
    },
}

# NOx emission rates (tons NOx/MWh) by fuel class.
# Source: EPA CEMS 2022.
NOX_RATES: dict[str, float] = {
    "gas_cc": 0.0001,  # EPA CEMS 2022 — combined-cycle gas units
    "gas_ct": 0.0003,  # EPA CEMS 2022 — combustion turbine gas units
    "coal": 0.0015,    # EPA CEMS 2022 — coal steam units
}

# Variable O&M ($/MWh) by fuel type.
# Source: NREL ATB 2024.
VOM: dict[str, float] = {
    "gas_cc": 2.0,   # NREL ATB 2024 — combined-cycle gas
    "gas_ct": 3.5,   # NREL ATB 2024 — combustion turbine gas
    "coal": 4.5,     # NREL ATB 2024 — coal steam
    "nuclear": 2.5,  # NREL ATB 2024 — nuclear
    "wind": 0.0,     # NREL ATB 2024 — onshore wind
    "solar": 0.0,    # NREL ATB 2024 — utility-scale solar PV
}

# Gas-fired generation availability factors by ISO.
# Source: NERC GADS.
GAS_AVAILABILITY_FACTOR: dict[str, float] = {
    "ERCOT": 0.83,  # NERC GADS — ERCOT gas fleet availability
    "CAISO": 0.88,  # NERC GADS — CAISO gas fleet availability
}

# Nuclear monthly capacity factors (12 values, Jan–Dec) by ISO.
# Spring and fall dips reflect scheduled refueling outages.
# Source: NRC PRIS 2019-2023.
NUCLEAR_MONTHLY_CF: dict[str, list[float]] = {
    # NRC PRIS 2019-2023 — ERCOT nuclear monthly capacity factors
    "ERCOT": [0.93, 0.93, 0.90, 0.90, 0.92, 0.93, 0.93, 0.93, 0.91, 0.90, 0.92, 0.93],
    # NRC PRIS 2019-2023 — CAISO nuclear monthly capacity factors
    "CAISO": [0.93, 0.92, 0.91, 0.90, 0.91, 0.93, 0.93, 0.93, 0.92, 0.90, 0.91, 0.93],
}

# Equivalent forced outage rate (demand) by technology class.
# Source: NERC GADS.
EFORD: dict[str, float] = {
    "gas_cc": 0.05,   # NERC GADS — combined-cycle gas
    "gas_ct": 0.06,   # NERC GADS — combustion turbine gas
    "coal": 0.08,     # NERC GADS — coal steam
    "nuclear": 0.03,  # NERC GADS — nuclear
}

# Annual demand growth rates by ISO and scenario path.
# Source: ERCOT CDR, CAISO IEPR.
DEMAND_GROWTH_RATES: dict[str, dict[str, float]] = {
    "ERCOT": {
        "low": 0.010,   # ERCOT CDR — low demand growth path
        "mid": 0.020,   # ERCOT CDR — mid demand growth path
        "high": 0.035,  # ERCOT CDR — high demand growth path
    },
    "CAISO": {
        "low": 0.005,   # CAISO IEPR — low demand growth path
        "mid": 0.012,   # CAISO IEPR — mid demand growth path
        "high": 0.022,  # CAISO IEPR — high demand growth path
    },
}

# Base delivered gas prices ($/MMBtu) by ISO and scenario path.
# Source: EIA AEO 2024.
GAS_PRICE_BASE: dict[str, dict[str, float]] = {
    "ERCOT": {
        "low": 2.50,   # EIA AEO 2024 — low gas price path
        "mid": 3.50,   # EIA AEO 2024 — mid gas price path
        "high": 5.50,  # EIA AEO 2024 — high gas price path
    },
    "CAISO": {
        "low": 3.00,   # EIA AEO 2024 — low gas price path
        "mid": 4.25,   # EIA AEO 2024 — mid gas price path
        "high": 6.50,  # EIA AEO 2024 — high gas price path
    },
}

# Annual real escalation rate applied to base gas prices.
# Source: EIA AEO 2024.
GAS_PRICE_ESCALATION: float = 0.02  # EIA AEO 2024 — annual gas price escalation

# Base delivered coal prices ($/MMBtu) by ISO.
# Source: EIA AEO 2024.
COAL_PRICE_BASE: dict[str, float] = {
    "ERCOT": 2.0,  # EIA AEO 2024 — delivered coal price
    "CAISO": 2.5,  # EIA AEO 2024 — delivered coal price
}

# Carbon price trajectories ($/tCO2) by scenario path and year.
# Source: RFF / state programs.
CARBON_PRICE_PATHS: dict[str, dict[int, float]] = {
    "zero": {2026: 0, 2030: 0, 2040: 0, 2050: 0},     # RFF — no carbon price
    "low": {2026: 0, 2030: 8, 2040: 18, 2050: 25},    # RFF — low carbon price path
    "mid": {2026: 0, 2030: 15, 2040: 35, 2050: 50},   # RFF — mid carbon price path
    "high": {2026: 0, 2030: 30, 2040: 70, 2050: 110},  # RFF — high carbon price path
}

# Storage technology parameters.
# Source: NREL ATB 2024 (li-ion), DOE LDES Liftoff (iron-air).
STORAGE_TECHS: dict[str, dict[str, float]] = {
    "li_ion_4hr": {  # NREL ATB 2024 — 4-hour lithium-ion battery
        "duration_hr": 4,
        "rte": 0.86,
        "cycles": 5000,
        "capex_per_kw": 1380.0,
        "capex_per_kwh": 345.0,
        "fom_per_kw_yr": 34.5,
        "learning_rate": 0.18,
    },
    "li_ion_8hr": {  # NREL ATB 2024 — 8-hour lithium-ion battery
        "duration_hr": 8,
        "rte": 0.86,
        "cycles": 5000,
        "capex_per_kw": 2760.0,
        "capex_per_kwh": 345.0,
        "fom_per_kw_yr": 55.2,
        "learning_rate": 0.18,
    },
    "iron_air": {  # DOE LDES Liftoff — 100-hour iron-air battery
        "duration_hr": 100,
        "rte": 0.50,
        "cycles": 3000,
        "capex_per_kw": 2000.0,
        "capex_per_kwh": 20.0,
        "fom_per_kw_yr": 20.0,
        "learning_rate": 0.10,
    },
}

# Total storage power capacity (MW) by deployment pace, for the base year (2026).
# Source: NREL ATB 2024 mid-case projections for ERCOT-scale grids.
STORAGE_DEPLOYMENT_MW: dict[str, float] = {
    "low": 3_000.0,
    "mid": 8_000.0,
    "high": 20_000.0,
}

# Annual compound growth rate of total deployed storage power by deployment pace.
# Applied to the STORAGE_DEPLOYMENT_MW base year capacity for every year past 2026.
# Source: NREL ATB 2024 storage deployment projections.
STORAGE_GROWTH_RATE: dict[str, float] = {
    "low": 0.05,   # NREL ATB 2024 — 5% annual growth from base
    "mid": 0.12,   # NREL ATB 2024 mid-case — 12% annual growth
    "high": 0.20,  # NREL ATB 2024 — 20% annual growth, aggressive deployment
}

# Ceiling on total deployed storage power (MW), capping compound growth so the
# fleet cannot exceed a realistic share (~50%) of ERCOT-scale system peak demand.
# Source: NREL ATB 2024 storage deployment projections.
STORAGE_DEPLOYMENT_CEILING_MW: float = 50_000.0

# Share of deployed storage power by technology type.
# Source: NREL ATB 2024 technology mix assumptions.
STORAGE_TECH_POWER_SHARE: dict[str, float] = {
    "li_ion_4hr": 0.70,
    "li_ion_8hr": 0.25,
    "iron_air": 0.05,
}

# State renewable/clean energy standard floors (clean energy fraction) by ISO and year.
# Source: CA SB 100.
STATE_RPS_FLOORS: dict[str, dict[int, float]] = {
    "ERCOT": {2026: 0.0, 2030: 0.0, 2040: 0.0, 2045: 0.0},  # No binding state RPS floor
    "CAISO": {  # CA SB 100 — clean energy trajectory
        2026: 0.50,
        2030: 0.60,
        2040: 0.80,
        2045: 1.00,
    },
}

# Annual interconnection queue caps (GW/yr) by ISO.
# Source: ERCOT CDR, CAISO TPP.
QUEUE_CAP_GW: dict[str, float] = {
    "ERCOT": 12,  # ERCOT CDR — annual queue throughput cap
    "CAISO": 8,   # CAISO TPP — annual queue throughput cap
}

# Per-technology annual interconnection queue caps (GW/yr) by ISO.
# Source: ERCOT CDR, CAISO TPP — approximate historical queue throughput by tech
# The sum of per-tech caps can exceed the ISO total cap (QUEUE_CAP_GW) — both bind independently.
QUEUE_CAP_PER_TECH_GW: dict[str, dict[str, float]] = {
    "ERCOT": {"wind": 5.0, "solar": 5.0, "gas_cc": 3.0},
    "CAISO": {"wind": 3.0, "solar": 4.0, "gas_cc": 2.0},
}

# New entry technology cost and performance parameters.
# Source: NREL ATB 2024.
NEW_ENTRY_COSTS: dict[str, dict[str, float]] = {
    "wind": {  # NREL ATB 2024 — onshore wind
        "capex_per_kw": 1300.0,
        "fom_per_kw_yr": 28.0,
        "learning_rate": 0.12,
        "base_cf": 0.38,
        "lifetime_yr": 30,
    },
    "solar": {  # NREL ATB 2024 — utility-scale solar PV
        "capex_per_kw": 1100.0,
        "fom_per_kw_yr": 16.0,
        "learning_rate": 0.20,
        "base_cf": 0.27,
        "lifetime_yr": 30,
    },
    "gas_cc": {  # NREL ATB 2024 — combined-cycle gas
        "capex_per_kw": 1200.0,
        "fom_per_kw_yr": 30.0,
        "learning_rate": 0.02,
        "base_cf": 0.55,
        "lifetime_yr": 30,
    },
}

# Wright's Law reference cumulative installed capacity (GW global).
# Source: IRENA 2024.
WRIGHT_REFERENCE_GW: dict[str, float] = {
    "wind": 1020.0,   # IRENA 2024 — global installed onshore + offshore wind
    "solar": 1420.0,  # IRENA 2024 — global installed solar PV
    "li_ion": 90.0,   # IRENA 2024 — global installed li-ion grid storage
}

# Annual-average renewable capacity factors (fraction) by ISO and technology.
# Used to rescale the normalized EIA-930 generation distributions into hourly
# capacity-factor profiles.
# Source: EIA Electric Power Monthly 2024, ERCOT CDR, CAISO annual report.
RENEWABLE_AVG_CF: dict[str, dict[str, float]] = {
    "ERCOT": {"wind": 0.35, "solar": 0.27},
    "CAISO": {"wind": 0.30, "solar": 0.28},
}

# Installed renewable nameplate capacity (MW) by ISO and technology.
# Source: ERCOT CDR Dec 2024, CAISO annual report 2024.
RENEWABLE_INSTALLED_MW: dict[str, dict[str, float]] = {
    "ERCOT": {"wind": 40000.0, "solar": 25000.0},
    "CAISO": {"wind": 7000.0, "solar": 20000.0},
}

# CAISO WECC import supply curve tranches: (name, capacity MW, marginal cost $/MWh).
# Ordered cheapest first. Represents the aggregate WECC supply available to CAISO.
# TODO: fit from EIA-930 interchange data. Current values are hand-set placeholders.
# Source: placeholder pending EIA-930 calibration.
WECC_IMPORT_TRANCHES: list[tuple[str, float, float]] = [
    ("PNW_hydro", 3000.0, 15.0),      # Pacific NW hydro — cheap but limited
    ("DSW_CCGT", 5000.0, 35.0),        # Desert SW combined-cycle gas
    ("DSW_CT", 4000.0, 55.0),          # Desert SW combustion turbine
    ("Expensive_import", 3000.0, 80.0), # High-cost marginal import
]

# CAISO export capability to WECC (MW).
# Source: placeholder pending EIA-930 calibration.
WECC_EXPORT_CAP_MW: float = 5000.0

# WECC import tranche forced outage rate.
# Source: NERC GADS — representative availability for out-of-state imports.
WECC_IMPORT_EFORD: float = 0.02

# Model-wide constants.
STORAGE_TIEBREAKER_EPSILON: float = 0.001  # $/MWh — prevents degenerate charge/discharge
HOURS_PER_YEAR: int = 8760
START_YEAR: int = 2026
END_YEAR: int = 2050
