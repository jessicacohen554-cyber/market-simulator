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
    (6.5, {"startup_per_mw": 63.8, "min_run_hours": 10, "min_down_hours": 8}),  # h-class
    (7.5, {"startup_per_mw": 48.6, "min_run_hours": 8,  "min_down_hours": 6}),  # f-class
    (99., {"startup_per_mw": 24.1, "min_run_hours": 5,  "min_down_hours": 4}),  # older
]

CT_COMMITMENT_PARAMS: list[tuple[float, dict[str, float]]] = [
    (10., {"startup_per_mw": 12.3, "min_run_hours": 1, "min_down_hours": 1}),  # aero
    (11., {"startup_per_mw": 24.5, "min_run_hours": 1, "min_down_hours": 1}),  # frame
    (99., {"startup_per_mw": 19.0, "min_run_hours": 1, "min_down_hours": 1}),  # older
]
# Coal is not commitment-screened: EIA-930 confirms ERCOT coal runs all 8,760
# hours, cycling output level rather than starting and stopping.

# CC/CT startup costs ($/MW per start) keyed by ascending heat-rate cutoff.
# Used to amortize startup cost into the monthly bid markup: a generator bids
# above marginal cost to recover startup_cost / expected_run_length.
# Source: NREL/SR-5500-55433 (Kumar et al. 2012).
CC_STARTUP_PARAMS: list[tuple[float, float]] = [
    (6.5, 63.8),   # h-class
    (7.5, 48.6),   # f-class
    (99., 24.1),   # older
]
CT_STARTUP_PARAMS: list[tuple[float, float]] = [
    (10., 12.3),   # aero
    (11., 24.5),   # frame
    (99., 19.0),   # older
]

# Coal take-or-pay supply-curve tranches: (capacity_fraction, fuel_passthrough).
# Coal plants hold take-or-pay fuel contracts, so the contracted volume bids at
# VOM only (fuel sunk) while volume above the contract bids at progressively
# more of full fuel cost. This stepped supply curve replaces a flat coal MC.
# These are the defaults for the coal_tranche_* ScenarioConfig fields.
# Source: calibrated to EIA-930 2023-2024 hourly ERCOT coal dispatch and
# eGRID 2023/2024 annual coal generation.
COAL_TRANCHES: list[tuple[float, float]] = [
    (0.30, 0.00),  # T1: take-or-pay floor — VOM only (~$4.5/MWh)
    (0.25, 0.35),  # T2: partially contracted — 35% fuel passthrough (~$11.5/MWh)
    (0.45, 1.00),  # T3: economic dispatch — full fuel cost (~$24-27/MWh)
]

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
# Source: EPA CAMPD (CEMS) 2023 annual rollup.
NOX_RATES: dict[str, float] = {
    "gas_cc": 0.00008,  # was 0.0001. EPA CEMS 2023 — SCR-equipped fleet average.
    "gas_ct": 0.00025,  # was 0.0003. EPA CEMS 2023 — mix of SCR/non-SCR CTs.
    "gas_st": 0.00025,  # EPA CEMS 2023 — legacy gas steam boilers, mostly non-SCR.
    "coal": 0.0012,     # was 0.0015. EPA CEMS 2023 — post-CSAPR compliance.
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
    "coal": 0.100,    # coal — implied by EPA eGRID 2022 coal steam rates
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
    "gas_cc": 2.0,   # NREL ATB 2024 — combined-cycle gas
    "gas_ct": 3.5,   # NREL ATB 2024 — combustion turbine gas
    "gas_st": 4.0,   # NREL ATB 2024 — legacy gas steam (higher O&M than CC)
    "coal": 4.5,     # NREL ATB 2024 — coal steam
    "nuclear": 2.5,  # NREL ATB 2024 — nuclear
    "wind": 0.0,     # NREL ATB 2024 — onshore wind
    "solar": 0.0,    # NREL ATB 2024 — utility-scale solar PV
}

# Gas-fired generation availability factors by ISO.
# Source: NERC GADS 2019-2023.
GAS_AVAILABILITY_FACTOR: dict[str, float] = {
    "ERCOT": 0.85,  # was 0.83. NERC GADS 2019-2023, ERCOT fleet.
    "CAISO": 0.89,  # was 0.88. NERC GADS 2019-2023, CAISO fleet.
    "PJM": 0.87,    # NERC GADS 2019-2023, PJM fleet. TODO: verify
    "NYISO": 0.86,  # NERC GADS 2019-2023, NYISO fleet. TODO: verify
    "NEISO": 0.85,  # NERC GADS 2019-2023, ISO-NE fleet. TODO: verify
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
    "PJM":   [1.00, 1.00, 0.95, 0.94, 0.97, 1.00, 1.00, 1.00, 0.97, 0.95, 0.98, 1.00],
    "NYISO": [1.00, 1.00, 0.95, 0.94, 0.97, 1.00, 1.00, 1.00, 0.97, 0.95, 0.98, 1.00],
    "NEISO": [1.00, 0.99, 0.95, 0.95, 0.98, 1.00, 1.00, 1.00, 0.97, 0.96, 0.98, 1.00],
}

# Equivalent forced outage rate (demand) by technology class.
# Source: NERC GADS.
EFORD: dict[str, float] = {
    "gas_cc": 0.05,   # NERC GADS — combined-cycle gas
    "gas_ct": 0.06,   # NERC GADS — combustion turbine gas
    "gas_st": 0.07,   # NERC GADS — legacy gas steam (older, higher outage rate)
    "coal": 0.08,     # NERC GADS — coal steam
    "nuclear": 0.03,  # NERC GADS — nuclear
}

# Annual demand growth rates by ISO, scenario path, and era.
# Near-term (2026-2030): elevated by data center and industrial load.
# Long-term (2031-2050): decelerates as pipeline matures.
# Source: EIA STEO July 2025, ERCOT CDR Dec 2024, CAISO IEPR 2024.
DEMAND_GROWTH_RATES: dict[str, dict[str, dict[str, float]]] = {
    "ERCOT": {
        "low":  {"near": 0.03, "long": 0.015},
        "mid":  {"near": 0.05, "long": 0.025},
        "high": {"near": 0.08, "long": 0.04},
    },
    "CAISO": {
        "low":  {"near": 0.005, "long": 0.005},
        "mid":  {"near": 0.015, "long": 0.010},
        "high": {"near": 0.025, "long": 0.018},
    },
    # PJM Fleet Parameters — Source: PJM Load Forecast Report 2024, Table B-1.
    # Tier: 2. TODO: verify
    "PJM": {
        "low":  {"near": 0.020, "long": 0.010},
        "mid":  {"near": 0.035, "long": 0.018},
        "high": {"near": 0.060, "long": 0.030},
    },
    # NYISO Fleet Parameters — Source: NYISO Gold Book 2024, Table I-3.
    # Tier: 2. TODO: verify
    "NYISO": {
        "low":  {"near": 0.005, "long": 0.005},
        "mid":  {"near": 0.015, "long": 0.010},
        "high": {"near": 0.025, "long": 0.018},
    },
    # NEISO Fleet Parameters — Source: ISO-NE CELT Report 2024.
    # Tier: 2. TODO: verify
    "NEISO": {
        "low":  {"near": 0.005, "long": 0.005},
        "mid":  {"near": 0.015, "long": 0.010},
        "high": {"near": 0.025, "long": 0.018},
    },
}

# Year at which demand growth transitions from near-term to long-term rate.
# Source: engineering judgment — data center pipeline matures ~2030.
DEMAND_GROWTH_TRANSITION_YEAR: int = 2030

# --- Henry Hub Natural Gas Price Trajectories ($/MMBtu, real 2024$) ---
# Source: EIA Annual Energy Outlook 2025 (AEO2025), released April 15, 2025
# Table 13: Natural Gas Supply, Disposition, and Prices
# Reference case, High Oil and Gas Supply case, Low Oil and Gas Supply case
# URL: https://www.eia.gov/outlooks/aeo/
# Note: AEO2025 assumptions frozen as of December 2024.
# All prices in real 2024 dollars per MMBtu.
# The model runs 2026-2050. The 2025 entry is included for interpolation
# context (it is the shared near-term anchor across all three cases).
#
# These trajectories replace the prior GAS_PRICE_BASE + GAS_PRICE_ESCALATION
# approach, which used a flat 2%/yr exponential that diverged from EIA's
# modeled supply/demand/LNG-export dynamics.
#
# AEO2025 Reference case: Henry Hub rises from $2.88 (2025) to $4.80 (2050),
# driven by LNG export growth through mid-2030s and rising marginal
# production costs as producers access less economical resources.
# Source: https://www.eia.gov/todayinenergy/detail.php?id=65724
#
# The model's gas_price_path lever ("low"/"mid"/"high") maps to AEO cases:
#   "low"  -> AEO High Oil and Gas Supply case (more supply -> lower prices)
#   "mid"  -> AEO Reference case
#   "high" -> AEO Low Oil and Gas Supply case (less supply -> higher prices)
#
# TODO: verify against AEO Table 13. The values below are approximate
# interpolations from published AEO2025 charts and text. Verify/update by
# running scripts/fetch_eia_aeo.py with an EIA API key, or against the AEO
# Data Browser at https://www.eia.gov/outlooks/aeo/data/browser/ (Table 13).
# AEO2026 was released April 8, 2026 and may carry updated trajectories.
#
# The 2023 and 2024 entries are historical actuals, not AEO projections:
# they are the EIA Henry Hub spot price annual averages ($2.54 in 2023,
# $2.19 in 2024) and are identical across all three paths because a
# realized price has no scenario branching.
# Source: EIA Henry Hub Natural Gas Spot Price, annual averages.
# URL: https://www.eia.gov/dnav/ng/hist/rngwhhdA.htm

HENRY_HUB_TRAJECTORIES: dict[str, dict[int, float]] = {
    # AEO High Oil and Gas Supply case -> model "low" gas price path.
    # Higher resource recovery + faster tech improvement = lower prices.
    "low": {
        2023: 2.54, 2024: 2.19,  # EIA Henry Hub spot annual average (historical)
        2025: 2.88, 2026: 2.70, 2027: 2.55, 2028: 2.50, 2029: 2.48,
        2030: 2.45, 2031: 2.43, 2032: 2.42, 2033: 2.41, 2034: 2.40,
        2035: 2.40, 2036: 2.42, 2037: 2.45, 2038: 2.48, 2039: 2.52,
        2040: 2.55, 2041: 2.60, 2042: 2.65, 2043: 2.70, 2044: 2.75,
        2045: 2.80, 2046: 2.85, 2047: 2.90, 2048: 2.95, 2049: 3.00,
        2050: 3.05,
    },
    # AEO Reference case -> model "mid" gas price path.
    "mid": {
        2023: 2.54, 2024: 2.19,  # EIA Henry Hub spot annual average (historical)
        2025: 2.88, 2026: 3.40, 2027: 3.20, 2028: 3.30, 2029: 3.40,
        2030: 3.50, 2031: 3.55, 2032: 3.60, 2033: 3.65, 2034: 3.70,
        2035: 3.80, 2036: 3.90, 2037: 4.00, 2038: 4.05, 2039: 4.10,
        2040: 4.15, 2041: 4.20, 2042: 4.25, 2043: 4.30, 2044: 4.40,
        2045: 4.45, 2046: 4.50, 2047: 4.55, 2048: 4.65, 2049: 4.70,
        2050: 4.80,
    },
    # AEO Low Oil and Gas Supply case -> model "high" gas price path.
    # Lower resource recovery + slower tech = higher prices.
    "high": {
        2023: 2.54, 2024: 2.19,  # EIA Henry Hub spot annual average (historical)
        2025: 2.88, 2026: 3.60, 2027: 3.80, 2028: 4.10, 2029: 4.40,
        2030: 4.70, 2031: 4.90, 2032: 5.10, 2033: 5.30, 2034: 5.50,
        2035: 5.70, 2036: 5.90, 2037: 6.10, 2038: 6.30, 2039: 6.50,
        2040: 6.70, 2041: 6.90, 2042: 7.10, 2043: 7.30, 2044: 7.50,
        2045: 7.70, 2046: 7.90, 2047: 8.10, 2048: 8.30, 2049: 8.50,
        2050: 8.70,
    },
}

# --- Regional Basis Differentials ($/MMBtu, relative to Henry Hub) ---
# Source: EIA Natural Gas Weekly Update, 2024-2025 average basis
# URL: https://www.eia.gov/naturalgas/weekly/
# Waha (West Texas/ERCOT): historically trades at a discount to Henry Hub
#   due to Permian associated gas oversupply and pipeline constraints.
# SoCal Citygate (CAISO): historically trades at a premium to Henry Hub
#   due to pipeline constraints into California and limited local production.
# These are annual average differentials, held constant across the
# projection period for simplicity.
#
# Delivered price = Henry Hub + basis differential
GAS_BASIS_DIFFERENTIAL: dict[str, float] = {
    "ERCOT": -0.50,   # Waha discount; EIA NG Weekly, 2024 avg
    "CAISO": 1.20,    # SoCal Citygate premium; EIA NG Weekly, 2024 avg
}

# --- Monthly Gas Price Seasonality Factors ---
# Source: EIA Henry Hub spot price monthly averages, 2019-2024 (excluding
#   anomalous Feb 2021 Uri event and Jan 2026 spike).
# Computed as avg monthly price / annual avg price for each year, then
#   averaged across years. Captures the winter heating premium and
#   shoulder-season discount. Applied as multiplicative factors to the
#   annual trajectory price. Sum of factors / 12 = 1.0 (budget-neutral).
GAS_MONTHLY_SEASONALITY: dict[int, float] = {
    1: 1.15,   # January — winter heating demand peak
    2: 1.10,   # February
    3: 1.02,   # March — shoulder
    4: 0.92,   # April — injection season begins
    5: 0.90,   # May
    6: 0.93,   # June — cooling demand starts
    7: 0.95,   # July
    8: 0.95,   # August
    9: 0.90,   # September — low demand
    10: 0.95,  # October — pre-winter
    11: 1.05,  # November — heating season starts
    12: 1.18,  # December — winter peak
}

# Base delivered coal prices ($/MMBtu) by ISO.
# Source: EIA AEO 2024.
COAL_PRICE_BASE: dict[str, float] = {
    "ERCOT": 2.0,  # EIA AEO 2024 — delivered coal price
    "CAISO": 2.5,  # EIA AEO 2024 — delivered coal price
}

# Annual real escalation rate for coal prices.
# Reflects mine closures, rising rail transport costs, and declining
# domestic demand reducing economies of scale.
# Source: EIA AEO 2024 coal supply module — ~1% real escalation.
COAL_PRICE_ESCALATION: float = 0.01

# Thermal-fleet availability model by plant-group category. Three additive
# components (summed, not compounded):
#  * POF   — planned outage factor; applied only in the shoulder months.
#  * WEFOR — weighted equivalent forced outage rate; flat year-round, and
#            escalates linearly with plant age past an onset year.
#  * DERATE — weather + performance-decline capacity loss; flat year-round,
#            and likewise escalates with age past an onset year.
# A unit's availability is 1 - WEFOR(age) - DERATE(age) - POF(shoulder only),
# where WEFOR(age) = base + max(0, age - onset) * rate (and likewise DERATE).
# Each entry is (POF, WEFOR_base, WEFOR_rate, WEFOR_onset, DERATE_base,
# DERATE_rate, DERATE_onset). Source: NERC GADS by unit type and age.
THERMAL_AVAILABILITY: dict[str, tuple[float, ...]] = {
    "CC_CHP":     (0.05, 0.04, 0.002, 20, 0.02, 0.001, 25),
    "CC_REGULAR": (0.05, 0.05, 0.002, 20, 0.02, 0.001, 25),
    "CT_CHP":     (0.03, 0.05, 0.002, 20, 0.03, 0.001, 20),
    "CT_PEAKER":  (0.03, 0.07, 0.003, 20, 0.05, 0.002, 20),
    "ST_GAS":     (0.06, 0.21, 0.003, 30, 0.04, 0.002, 30),
    "ST_CHP":     (0.05, 0.08, 0.002, 25, 0.03, 0.0015, 25),
    "COAL":       (0.07, 0.12, 0.005, 40, 0.03, 0.002, 35),
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
        "capex_per_kw": 1140.0,    # was 1380. ~$285/kWh × 4hr. NREL ATB 2024b, BNEF 2025.
        "capex_per_kwh": 285.0,    # was 345. LFP pack costs ~$100/kWh + BOS.
        "fom_per_kw_yr": 30.0,     # was 34.5.
        "learning_rate": 0.18,
    },
    "li_ion_8hr": {  # NREL ATB 2024 — 8-hour lithium-ion battery
        "duration_hr": 8,
        "rte": 0.86,
        "cycles": 5000,
        "capex_per_kw": 2280.0,    # was 2760. $285/kWh × 8hr.
        "capex_per_kwh": 285.0,    # was 345.
        "fom_per_kw_yr": 48.0,     # was 55.2.
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
        "capex_per_kw": 3100.0,  # was 3560. $240/kWh × 12hr + $220/kW.
        "capex_per_kwh": 240.0,  # was 280.
        "fom_per_kw_yr": 10.0,   # was 12.0.
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

# Storage power capacity (MW) for the base year (2026).
# Subsequent years grow via economics-based new entry, not this constant.
# Source: ERCOT Monthly Dec 2025 — battery capacity ~17 GW.
# CAISO TPP 2024 — ~8 GW operational + under construction.
STORAGE_BASE_FLEET_MW: dict[str, dict[str, float]] = {
    "ERCOT": {
        "low": 12_000.0,
        "mid": 17_000.0,
        "high": 25_000.0,
    },
    "CAISO": {
        "low": 6_000.0,
        "mid": 8_000.0,
        "high": 12_000.0,
    },
    # PJM/NYISO/NEISO base storage — approximate operational + queued
    # battery capacity. TODO: verify (PJM Load Forecast Report 2024,
    # NYISO Gold Book 2024, ISO-NE CELT Report 2024).
    "PJM": {
        "low": 3_000.0,
        "mid": 5_000.0,
        "high": 9_000.0,
    },
    "NYISO": {
        "low": 1_000.0,
        "mid": 1_500.0,
        "high": 3_000.0,
    },
    "NEISO": {
        "low": 500.0,
        "mid": 1_000.0,
        "high": 2_000.0,
    },
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
    "NYISO": {  # NY CLCPA — 70% renewable by 2030, 100% zero-emission by 2040
        2026: 0.40,
        2030: 0.70,
        2040: 1.00,
        2045: 1.00,
    },
    "NEISO": {  # MA Clean Energy Standard + regional state CES blend
        2026: 0.30,
        2030: 0.45,
        2040: 0.70,
        2045: 0.80,
    },
    # PJM spans many states with differing RPS rules and no single
    # ISO-wide clean-energy floor, so no PJM entry is defined here.
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
    "nuclear_smr": {  # NREL ATB 2024, NuScale FOAK estimates
        "capex_per_kw": 6800.0,
        "fom_per_kw_yr": 100.0,
        "learning_rate": 0.08,
        "base_cf": 0.90,
        "lifetime_yr": 40,
    },
    "nuclear_large": {  # NREL ATB 2024 mid-case, Lazard LCOE v17
        "capex_per_kw": 8500.0,
        "fom_per_kw_yr": 130.0,
        "learning_rate": 0.03,
        "base_cf": 0.92,
        "lifetime_yr": 60,
    },
    "gas_cc_ccs": {
        "capex_per_kw": 2300.0,    # $/kW total plant cost (host CCGT + capture island).
                                    # Source: NETL Cost & Performance Baseline Rev 4, 2021.
                                    # Reflects 90% capture, amine-based post-combustion.
        "fom_per_kw_yr": 45.0,     # $/kW-yr. Source: NETL Rev 4.
        "learning_rate": 0.10,     # 10% cost reduction per doubling of cumulative deployment.
                                    # Source: Rubin et al. (2015) "The cost of CO2 capture
                                    # and storage", Int J Greenhouse Gas Control.
                                    # Range in literature: 0.08–0.12 for first-of-a-kind
                                    # industrial process technologies.
                                    # CCS is early on its deployment curve (~2 GW base),
                                    # so each doubling comes quickly and has large effect.
        "base_cf": 0.80,           # Lower than unabated CC (0.85) due to higher MC
                                    # pushing it later in merit order at low carbon prices.
        "lifetime_yr": 30,         # Same as gas CC host plant.
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

# Offshore wind hourly-profile derivation parameters. The offshore CF profile
# is derived from the onshore wind profile by a centered rolling-mean smoothing
# window plus a minimum CF floor (see :mod:`market_sim.data.renewables`).
# Source: NREL offshore wind variability studies, Musial et al. 2022.
OFFSHORE_WIND_SMOOTHING_HOURS: int = 6  # rolling-mean window — ocean fetch reduces gustiness
OFFSHORE_WIND_MIN_CF: float = 0.08      # minimum hourly CF — offshore rarely drops to zero

# Wright's Law reference cumulative installed capacity (GW global).
# Source: IRENA 2025, IEA WEO 2025, IAEA PRIS 2025, BNEF 2025, DOE LDES.
WRIGHT_REFERENCE_GW: dict[str, float] = {
    "wind": 1150.0,    # was 1020. IRENA 2025.
    "solar": 1800.0,   # was 1420. IRENA 2025.
    "li_ion": 130.0,   # was 90. BNEF 2025.
    "gas_cc": 1220.0,  # was 1200. IEA WEO 2025.
    "nuclear": 445.0,  # was 440. IAEA PRIS 2025.
    "nuclear_smr": 445.0,    # shares global nuclear fleet
    "nuclear_large": 445.0,
    "iron_air": 1.0,   # was 0.5. DOE LDES.
    "gas_cc_ccs": 2.0,   # GW global installed power-sector CCS as of 2024.
                          # Boundary Dam (0.12 GW), miscellaneous pilots/demos.
                          # Petra Nova mothballed 2020, excluded.
                          # Source: Global CCS Institute Global Status Report 2024.
}

# Annual global deployment (GW/yr) by technology, used to project cumulative
# installed capacity for Wright's Law learning curves. These represent the
# worldwide market, not just the modeled ISO.
# Source: IRENA 2025, IEA WEO 2025, BNEF 2025, IAEA 2025.
GLOBAL_ANNUAL_DEPLOYMENT_GW: dict[str, float] = {
    "wind": 130.0,     # was 120. IRENA 2025.
    "solar": 400.0,    # was 350. IRENA 2025.
    "li_ion": 50.0,    # was 30. BNEF 2025.
    "gas_cc": 20.0,    # was 25. IEA WEO 2025.
    "nuclear": 10.0,   # was 8. IAEA 2025.
    "nuclear_smr": 5.0,
    "nuclear_large": 5.0,
    "iron_air": 1.0,   # was 0.5.
    "gas_cc_ccs": 1.5,   # GW/yr global CCS additions on power plants.
                          # Based on announced project pipeline (DOE OCED awards,
                          # UK cluster sequencing, EU Innovation Fund).
                          # Optimistic but reflects policy momentum.
                          # Source: Global CCS Institute project database 2024.
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
    "ERCOT": {
        "wind": 42000.0,   # was 40000. Source: ERCOT CDR Dec 2024.
        "solar": 38000.0,  # was 25000. Source: EIA Hourly Grid Monitor Oct 2025.
    },
    "CAISO": {
        "wind": 7000.0,    # unchanged. Source: CAISO annual report 2024.
        "solar": 22000.0,  # was 20000. Source: CAISO annual report 2024.
    },
}

# CAISO WECC import supply curve tranches: (name, capacity MW, VOM $/MWh).
# These represent the aggregate WECC supply merit order available to CAISO.
#
# CALIBRATION TODO (high priority before running CAISO scenarios):
# 1. Pull CAISO net interchange from EIA-930 hourly data (2022-2024).
# 2. Correlate hourly import MW vs. CAISO day-ahead price.
# 3. Fit a 3-4 step supply curve to the import-vs-price scatter.
# 4. Validate aggregate import capacity against CAISO OASIS path ratings
#    (Path 15, Path 26, Path 46, PDCI — sum ~12-15 GW).
# 5. Validate export capability against CAISO curtailment + export data.
#
# Current values are engineering estimates, not empirically fitted.
# Source: engineering judgment from EIA-930 visual inspection, CAISO OASIS.
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

# Model-wide constants.
STORAGE_TIEBREAKER_EPSILON: float = 0.001  # $/MWh — prevents degenerate charge/discharge
HOURS_PER_YEAR: int = 8760
START_YEAR: int = 2026
END_YEAR: int = 2050
