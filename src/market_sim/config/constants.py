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
    # Additional long-duration storage technologies. ``capex_per_kw`` is the
    # total capital per kW of power (energy capex × duration + power capex),
    # matching the convention of the li-ion / iron-air entries above.
    "li_ion_12hr": {  # NREL ATB 2024 — 12-hour lithium-ion battery
        "duration_hr": 12,
        "rte": 0.78,            # lower RTE at longer duration. NREL ATB 2024
        "cycles": 4000,
        "capex_per_kw": 3560.0,  # 280 $/kWh × 12 h + 200 $/kW. NREL ATB 2024
        "capex_per_kwh": 280.0,
        "fom_per_kw_yr": 12.0,
        "learning_rate": 0.15,   # BNEF lithium-ion learning curve 2024
        "lifetime_yr": 20,
    },
    "flow_battery": {  # PNNL 2023 — vanadium redox flow battery
        "duration_hr": 10,
        "rte": 0.70,             # vanadium redox. PNNL 2023 flow battery review
        "cycles": 15000,         # long cycle life — major advantage. PNNL 2023
        "capex_per_kw": 4700.0,  # 350 $/kWh × 10 h + 1200 $/kW. PNNL 2023
        "capex_per_kwh": 350.0,
        "fom_per_kw_yr": 15.0,
        "learning_rate": 0.10,
        "lifetime_yr": 25,
    },
    "compressed_air": {  # NREL ATB 2024 — adiabatic compressed-air storage
        "duration_hr": 8,
        "rte": 0.55,             # adiabatic CAES. NREL ATB 2024
        "cycles": 10000,
        "capex_per_kw": 2700.0,  # 150 $/kWh × 8 h + 1500 $/kW. NREL ATB 2024
        "capex_per_kwh": 150.0,
        "fom_per_kw_yr": 10.0,
        "learning_rate": 0.05,   # mature concept, limited recent deployment
        "lifetime_yr": 40,       # Huntorf plant operating since 1978
    },
}

# Storage power capacity (MW) by deployment pace, for the base year (2026).
# Subsequent years grow via economics-based new entry, not this constant.
# Source: NREL ATB 2024 mid-case projections for ERCOT-scale grids.
STORAGE_BASE_FLEET_MW: dict[str, float] = {
    "low": 3_000.0,
    "mid": 8_000.0,
    "high": 20_000.0,
}

# Ceiling on total deployed storage power (MW) per ISO, capping cumulative
# new entry at a realistic share of system peak demand.
STORAGE_DEPLOYMENT_CEILING_MW: dict[str, float] = {
    "ERCOT": 45_000.0,  # ~53% of ~85 GW peak. Source: ERCOT CDR
    "CAISO": 25_000.0,  # ~52% of ~48 GW peak. Source: CAISO IEPR
}

# Max new storage power per year (MW). Source: ERCOT CDR, CAISO TPP queue data.
STORAGE_ANNUAL_BUILD_CAP_MW: dict[str, float] = {
    "ERCOT": 5_000.0,
    "CAISO": 3_000.0,
}

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
    "ERCOT": {
        "wind": 5.0, "solar": 5.0, "gas_cc": 3.0, "nuclear": 2.0,
        "geothermal": 2.0,      # engineering judgment, EGS resource potential
        "offshore_wind": 0.0,   # Gulf coast not yet leased. Source: BOEM
    },
    "CAISO": {
        "wind": 3.0, "solar": 4.0, "gas_cc": 2.0, "nuclear": 1.0,
        "geothermal": 3.0,      # CA geothermal resource assessment
        "offshore_wind": 3.0,   # BOEM Pacific lease areas, CAISO TPP
    },
}
# Hydrogen turbines (hydrogen_ct, hydrogen_ccgt) and CCUS (gas_cc_ccs) do not
# get their own per-tech queue cap: they share the ``gas_cc`` interconnection
# cap above, since they reuse the same gas-turbine supply chain and queue.

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
    "nuclear": {  # NREL ATB 2024 — advanced nuclear (SMR/Gen III+)
        "capex_per_kw": 6800.0,
        "fom_per_kw_yr": 120.0,
        "learning_rate": 0.05,
        "base_cf": 0.90,
        "lifetime_yr": 40,
    },
}

# --- Emerging generation technologies -------------------------------------
# Hydrogen turbines, post-combustion CCUS, enhanced geothermal and offshore
# wind. Each enters the model as a Generator (thermal dispatch) reusing the
# existing LP variable structure — no LP formulation change.

# Hydrogen-fired turbine parameters. H2 turbines are thermal generators whose
# fuel cost is DERIVED from renewable LCOE / electrolyzer efficiency (see
# :mod:`market_sim.data.hydrogen`) rather than an exogenous price path.
HYDROGEN_TURBINE_PARAMS: dict[str, dict[str, float]] = {
    "h2_ct": {  # simple-cycle H2 turbine (peaker)
        "heat_rate": 9.5,          # MMBtu/MWh. GE HA specs, DOE H2 Turbine Program 2023
        "vom": 4.0,                # $/MWh. NREL ATB 2024 (gas CT analog + H2 premium)
        "emission_rate_co2": 0.0,  # tCO2/MWh — zero direct CO2 (green H2)
        "nox_rate": 0.00015,       # tons NOx/MWh — H2 burns hot. DOE/NETL 2023
        "eford": 0.06,             # above gas CT — immature fleet. Engineering judgment
        "capex_kw": 1400.0,        # $/kW. NREL ATB 2024, BloombergNEF H2 Outlook 2024
        "fom_kw_yr": 12.0,         # $/kW-yr. NREL ATB 2024
        "lifetime_yr": 30,
        "learning_rate": 0.10,     # analogy to gas CT maturation
    },
    "h2_ccgt": {  # combined-cycle H2 turbine (mid-merit/baseload)
        "heat_rate": 6.9,          # MMBtu/MWh. DOE H2 Turbine Program 2023
        "vom": 3.5,                # $/MWh. NREL ATB 2024
        "emission_rate_co2": 0.0,
        "nox_rate": 0.00012,       # DOE/NETL 2023
        "eford": 0.06,
        "capex_kw": 1800.0,        # $/kW — premium over gas CCGT. NREL ATB 2024
        "fom_kw_yr": 15.0,         # $/kW-yr. NREL ATB 2024
        "lifetime_yr": 30,
        "learning_rate": 0.10,
    },
}

# Electrolyzer parameters used to derive the hydrogen fuel cost. Not an LP
# variable. Efficiency is MWh_H2 / MWh_electricity (LHV basis) and improves
# linearly between the 2026 base, 2035 and 2045 milestone years.
ELECTROLYZER_PARAMS: dict[str, dict[str, float]] = {
    "pem": {
        "efficiency": 0.65,        # base year. Source: IRENA Green H2 2023
        "efficiency_2035": 0.72,   # DOE Hydrogen Shot targets
        "efficiency_2045": 0.76,   # DOE long-term targets
        "capex_kw": 1200.0,        # $/kW — for LCOH if needed. BNEF 2024
        "learning_rate": 0.18,     # aggressive — early on curve. IRENA 2023
    },
    "alkaline": {
        "efficiency": 0.63,        # Source: IRENA Green H2 2023
        "efficiency_2035": 0.68,
        "efficiency_2045": 0.72,
        "capex_kw": 800.0,
        "learning_rate": 0.12,     # more mature technology. IRENA 2023
    },
}

# MMBtu per MWh — thermodynamic identity, used to convert the derived
# hydrogen electricity cost ($/MWh) into a fuel cost ($/MMBtu).
MMBTU_PER_MWH: float = 3.412

# Carbon capture, utilization and storage parameters. CCUS is a variant of
# the base gas CC plant: higher heat rate (parasitic capture load), higher
# VOM (solvent costs), reduced emission rate, plus a transport+storage cost
# for the captured CO2.
CCUS_PARAMS: dict[str, dict[str, float]] = {
    "gas_cc_ccs_90": {  # gas CCGT with 90% post-combustion capture
        "heat_rate_penalty": 1.16,      # ×base CC heat rate — 16% parasitic. NETL 2022 Rev 4, Case B31B
        "vom_adder": 8.0,               # $/MWh — amine solvent, maintenance. NETL 2022
        "capture_rate": 0.90,           # fraction of CO2 captured. NETL 2022 Case B31B
        "co2_transport_storage": 15.0,  # $/tCO2 — pipeline + saline injection. NETL 2022, Gulf Coast
        "capex_kw": 2500.0,             # $/kW installed. NREL ATB 2024
        "fom_kw_yr": 22.0,              # $/kW-yr. NREL ATB 2024
        "lifetime_yr": 30,
        "learning_rate": 0.05,          # slow — limited deployment. Global CCS Institute 2024
    },
}

# Enhanced geothermal (EGS) parameters. EGS enters as a thermal generator
# with zero fuel cost and high capacity factor, dispatchable down to
# ``pmin_fraction`` of rated capacity (flexible baseload). Not intermittent.
GEOTHERMAL_PARAMS: dict[str, dict[str, float]] = {
    "egs": {
        "capacity_factor": 0.90,   # high availability. DOE GeoVision 2019
        "vom": 1.0,                # $/MWh — minimal, no fuel. NREL ATB 2024
        "emission_rate_co2": 0.0,  # zero direct emissions
        "nox_rate": 0.0,
        "eford": 0.05,             # comparable to nuclear. DOE GeoVision 2019
        "pmin_fraction": 0.20,     # turn down to 20% for flexibility. Fervo 2024
        "capex_kw": 5000.0,        # $/kW — high upfront, early-stage. NREL ATB 2024
        "fom_kw_yr": 0.0,          # $/kW-yr — captured in VOM. NREL ATB 2024
        "lifetime_yr": 30,
        "learning_rate": 0.15,     # steep — analogous to early solar. Fervo, ARPA-E
        "heat_rate": 0.0,          # no fuel
    },
}

# Offshore wind parameters. A separate renewable category from onshore wind:
# higher and less variable capacity factors, higher costs, distinct zones.
OFFSHORE_WIND_PARAMS: dict[str, dict[str, float]] = {
    "fixed_bottom": {
        "base_cf": 0.45,           # annual average. NREL ATB 2024
        "capex_kw": 4200.0,        # $/kW. NREL ATB 2024
        "fom_kw_yr": 80.0,         # $/kW-yr — marine access premium. NREL ATB 2024
        "lifetime_yr": 30,
        "learning_rate": 0.08,     # NREL ATB 2024, IRENA 2024
    },
    "floating": {
        "base_cf": 0.48,           # deeper water, better resource. NREL ATB 2024
        "capex_kw": 5500.0,        # $/kW — early stage. NREL ATB 2024
        "fom_kw_yr": 95.0,
        "lifetime_yr": 30,
        "learning_rate": 0.12,     # steeper — less mature. NREL ATB 2024
    },
}

# Wright's Law reference cumulative installed capacity (GW global).
# Source: IRENA 2024, IEA WEO 2024, IAEA PRIS 2024, DOE LDES Liftoff.
WRIGHT_REFERENCE_GW: dict[str, float] = {
    "wind": 1020.0,    # IRENA 2024 — global installed onshore + offshore wind
    "solar": 1420.0,   # IRENA 2024 — global installed solar PV
    "li_ion": 90.0,    # IRENA 2024 — global installed li-ion grid storage
    "gas_cc": 1200.0,  # IEA WEO 2024 — global installed gas combined-cycle
    "nuclear": 440.0,  # IAEA PRIS 2024 — global installed nuclear
    "iron_air": 0.5,   # DOE LDES Liftoff — global installed iron-air (nascent)
}

# Annual global deployment (GW/yr) by technology, used to project cumulative
# installed capacity for Wright's Law learning curves. These represent the
# worldwide market, not just the modeled ISO.
# Source: IRENA 2024, IEA WEO 2024.
GLOBAL_ANNUAL_DEPLOYMENT_GW: dict[str, float] = {
    "wind": 120.0,     # IRENA 2024 — ~120 GW/yr global wind additions
    "solar": 350.0,    # IRENA 2024 — ~350 GW/yr global solar additions
    "li_ion": 30.0,    # BloombergNEF 2024 — ~30 GW/yr grid storage
    "gas_cc": 25.0,    # IEA WEO 2024 — ~25 GW/yr global gas CC additions
    "nuclear": 8.0,    # IAEA 2024 — ~8 GW/yr global nuclear additions
    "iron_air": 0.5,   # DOE estimate — nascent, <1 GW/yr
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

# Exogenous REC price reference ranges ($/MWh) by resource type, as
# low/mid/high values. Documentation only — these are NOT used as defaults
# (every ScenarioConfig.rec_price_* defaults to 0.0); they give plausible
# ranges for scenario authors setting REC prices by hand.
REC_PRICE_REFERENCE: dict[str, dict[str, float]] = {
    "nuclear_zec": {"low": 10.0, "mid": 17.0, "high": 25.0},
    # Source: NY PSC Order, Case 15-E-0302; IL FEJA
    "wind_rec": {"low": 2.0, "mid": 8.0, "high": 15.0},
    # Source: PJM GATS, S&P Global Platts
    "solar_rec": {"low": 2.0, "mid": 10.0, "high": 20.0},
    # Source: PJM GATS, S&P Global Platts
    "gas_cc_ccs": {"low": 0.0, "mid": 15.0, "high": 30.0},
    # Source: 45Q credit ranges
    "storage": {"low": 0.0, "mid": 5.0, "high": 15.0},
    # Source: emerging state programs
}

# Model-wide constants.
STORAGE_TIEBREAKER_EPSILON: float = 0.001  # $/MWh — prevents degenerate charge/discharge
HOURS_PER_YEAR: int = 8760
START_YEAR: int = 2026
END_YEAR: int = 2050
