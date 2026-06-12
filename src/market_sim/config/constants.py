"""Physical and economic constants with citation comments."""

from dataclasses import dataclass

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
    # Oil and biomass classify into a single "default" bin (the EIA-source
    # classifier carries no vintage sub-bins for them, see fleet._efficiency_bin).
    "oil": {
        "default": 13.5,        # EIA Table 8 — petroleum-fired GT/steam (oil peaker)
    },
    "biomass": {
        "default": 13.5,        # EIA Table 8 — wood/biomass steam (low-efficiency)
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
    # Oil ≈ heat_rate(13.5) × distillate/residual factor(0.074) ≈ 1.0 tCO2/MWh.
    "oil": {
        "default": 1.00,        # EPA eGRID 2022 — petroleum-fired units
    },
    # Biomass biogenic CO2 is treated as carbon-neutral (not counted under
    # EPA/RGGI accounting), so its modeled CO2 rate is zero.
    "biomass": {
        "default": 0.0,         # EPA/RGGI — biogenic CO2 carbon-neutral
    },
}

# NOx emission rates (tons NOx/MWh) by fuel class.
# Source: EPA CAMPD (CEMS) 2023 annual rollup.
NOX_RATES: dict[str, float] = {
    "gas_cc": 0.00008,  # was 0.0001. EPA CEMS 2023 — SCR-equipped fleet average.
    "gas_ct": 0.00025,  # was 0.0003. EPA CEMS 2023 — mix of SCR/non-SCR CTs.
    "gas_st": 0.00025,  # EPA CEMS 2023 — legacy gas steam boilers, mostly non-SCR.
    "coal": 0.0012,     # was 0.0015. EPA CEMS 2023 — post-CSAPR compliance.
    "oil": 0.0004,      # EPA CEMS 2023 — oil-fired peakers/steam, mostly non-SCR.
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
    "coal": 0.100,    # coal — implied by EPA eGRID 2022 coal steam rates
    "oil": 0.074,     # distillate/residual fuel oil — EPA emission factors
    "biomass": 0.0,   # biogenic CO2 carbon-neutral under EPA/RGGI accounting
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
    "oil": 4.5,      # NREL ATB 2024 — oil steam/peaker O&M (≈ coal steam)
    "biomass": 5.0,  # NREL ATB 2024 — biomass (fuel handling raises O&M)
    "hydro": 1.4,    # NREL ATB 2024 — conventional hydropower
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
# see (PSH pure O&M is < $1/MWh; with no adder the LP arbitrages PS every day
# the spread clears RTE losses and overshoots observed PS energy ~2-3x).
# PJM: $10 calibrated so PJM PS lands near its observed ~3.5-4 TWh/yr of
# EIA-923 gross generation (calibration-log 2026-06-10, "pjm 3 ps-adder").
# ISOs absent from the map resolve to 0.0 — notably CAISO, whose adder stays
# off until a CAISO calibration pass measures Helms' reserve duty.
PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO: dict[str, float] = {"PJM": 10.0}

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

# Per-year nuclear monthly capacity factor derived from EIA-923 net generation
# (the actual staggered refueling cadence each year, not a fixed seasonal
# average). When a (ISO, year) is present it overrides NUCLEAR_MONTHLY_CF in the
# backcast; forecast years fall back to NUCLEAR_MONTHLY_CF or the universal
# refueling-block forecaster. ERCOT = Comanche Peak (2) + South Texas (2).
# Derivation: scripts/derive_nuclear_monthly_cf.py (CF = fleet EIA-923 monthly
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
    # Derivation/verify: scripts/derive_nuclear_monthly_cf.py --isos NYISO.
    "NYISO": {
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
    # Derivation/verify: scripts/derive_nuclear_monthly_cf.py --isos NEISO.
    "NEISO": {
        2023: [0.98, 0.98, 0.99, 0.41, 0.60, 0.38, 0.93, 0.93, 0.91, 0.84, 0.63, 0.87],
        2024: [0.88, 1.00, 1.00, 1.00, 0.99, 1.00, 0.99, 0.98, 0.81, 0.44, 0.76, 0.97],
        2025: [1.00, 1.00, 1.00, 0.75, 0.77, 1.00, 0.99, 0.93, 0.99, 0.86, 1.00, 1.00],
    },
}

# Equivalent forced outage rate (demand) by technology class.
# Source: NERC GADS.
EFORD: dict[str, float] = {
    "gas_cc": 0.05,   # NERC GADS — combined-cycle gas
    "gas_ct": 0.06,   # NERC GADS — combustion turbine gas
    "gas_st": 0.07,   # NERC GADS — legacy gas steam (older, higher outage rate)
    "coal": 0.08,     # NERC GADS — coal steam
    "nuclear": 0.03,  # NERC GADS — nuclear
    "oil": 0.10,      # NERC GADS — oil peakers (infrequent run, higher EFOR)
    "biomass": 0.08,  # NERC GADS — biomass steam
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
#   Measured check (EIA-923 Schedule 5, quantity-weighted delivered gas to
#   CAISO plants minus Henry Hub annual average): +$7.06 in 2023 (the
#   Dec-22/Jan-23 western gas crisis — Jan-2023 delivered $38.7/MMBtu vs
#   HH $3.27), +$2.26 in 2024, +$1.12 in 2025. The +1.20 seed is only
#   right in a normal year; CAISO backcasts therefore default to
#   gas_monthly_actuals (measured ISO-month delivered gas), which makes
#   this scalar a forward-year/fallback value only.
# PJM: no single hub. PJM gas burn spans the Appalachian supply basin
#   (Dominion South / TETCO M2, a structural Marcellus *discount* to Henry
#   Hub from takeaway-constrained oversupply) and the Mid-Atlantic load
#   pocket (TETCO M3 and Transco Zone 6 non-NY, a modest annual *premium*
#   with large winter spikes). Rather than blend hub quotes by hand, the
#   +0.67 scalar is the empirical generation-weighted basis measured from
#   EIA-923 itself: the quantity-weighted delivered gas cost to PJM gas
#   plants (Schedule 5 fuel receipts) minus the Henry Hub annual average was
#   +$0.67/MMBtu in BOTH 2023 ($3.21 vs $2.54) and 2024 ($2.86 vs $2.19).
#   Source: scripts/derive_coal_supply.py-style EIA-923 receipt aggregation;
#   same EIA family as the ERCOT/CAISO figures. Caveat: Schedule-5 gas
#   reporting is sparse (~26 PJM plants), likely skewed toward the eastern
#   premium hubs, so this may run slightly high for the western price-taking
#   CCs — but it replaces the prior unvalidated +0.30 placeholder and lands
#   PJM CC dispatch on EIA-923 actuals without distorting the offer curve.
# NYISO: gas burn spans Transco Zone 6 NY / Iroquois (a steep winter premium
#   when downstate pipeline capacity is scarce) and the upstate path-priced
#   CCs. As with PJM, the +0.55 scalar is the generation-weighted basis
#   measured directly from EIA-923: the quantity-weighted delivered gas cost
#   to New York gas plants (Schedule 5 fuel receipts) minus the Henry Hub
#   annual average was +$0.53 (2023: 3.07 vs 2.54), +$0.44 (2024: 2.63 vs
#   2.19) and +$0.55 (2025: 4.08 vs 3.53) — a stable +0.54 quantity-weighted
#   over 2023-2025. Source: EIA-923 Schedule 5 receipt aggregation, same EIA
#   family as the ERCOT/CAISO/PJM figures. Caveat: a single annual scalar
#   flattens NY's pronounced winter blowout (the same Schedule-5 receipts show
#   monthly basis reaching +$3-7 in Jan/Dec) — enable
#   gas_plant_monthly_fuel_pricing for the monthly shape when winter price
#   fidelity matters.
# NEISO: New England gas burn prices off Algonquin Citygate (AGT), the
#   pipeline-constrained hub whose winter basis blows out to many multiples
#   of Henry Hub (doc-08 design decision 1). The +1.10 scalar is the
#   EIA-923 delivered-basis seed for *normal* (non-arctic-event) years:
#   quantity-weighted delivered gas cost to New England plants (Schedule 5
#   fuel receipts) minus the Henry Hub annual average was +$1.17 in 2024
#   (3.37 vs 2.19) and +$1.07 in Apr-Sep 2025 (4.60 vs 3.53); 2023 measured
#   +$3.17 (5.70 vs 2.54), inflated by the Jan/Feb-2023 arctic events
#   (Jan-23 delivered $15.17/MMBtu). Source: EIA-923 Schedule 5 receipt
#   aggregation, same EIA family as the other ISOs. STRONG caveat: only TWO
#   New England plants report Schedule-5 gas receipts (EIA plant codes 1660,
#   6081 — partly LNG-supplied), so the sample is far sparser than
#   PJM/NYISO. NEISO backcasts therefore default to gas_monthly_actuals +
#   the measured Algonquin hub-month basis overlay
#   (gas_hub_basis_overlay; inputs/raw-data/gas_basis_by_iso_month.csv),
#   which makes this scalar a forward-year/fallback value only — like the
#   CAISO +1.20 seed.
# These are annual average differentials, held constant across the
# projection period for simplicity.
#
# Delivered price = Henry Hub + basis differential
GAS_BASIS_DIFFERENTIAL: dict[str, float] = {
    "ERCOT": -0.50,   # Waha discount; EIA NG Weekly, 2024 avg
    "CAISO": 1.20,    # SoCal Citygate premium; EIA NG Weekly, 2024 avg
    "PJM": 0.67,      # EIA-923 delivered-gas basis (see below)
    "NYISO": 0.55,    # EIA-923 delivered-gas basis (see below)
    "NEISO": 1.10,    # EIA-923 delivered-gas basis, normal-year (see below)
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
    "PJM": 2.3,    # Central/Northern Appalachian bituminous + PRB-by-rail
    #   delivered blend. Source: EIA AEO 2024 delivered coal price; refined
    #   per-plant by the EIA-923 monthly fuel-cost overlay where reported.
    "NYISO": 2.3,  # NY's grid coal fleet is retired (Somerset/Cayuga, 2020),
    #   so no unit prices off this in a 2023+ backcast; carried as a defensive
    #   Appalachian-delivered fallback (≈ PJM) for any residual/legacy coal
    #   unit. Source: EIA AEO 2024 delivered coal price.
    "NEISO": 3.0,  # New England's only coal in the backcast window is
    #   Merrimack Station (NH, ~440 MW bituminous-by-rail, ~5% CF,
    #   deactivated Jun-2025). Its delivered cost is confidential (no
    #   EIA-923 Schedule-5 receipts; EIA state tables suppress NH coal), so
    #   this is the PJM bituminous blend (2.3) plus a rail-into-New-England
    #   premium — a Tier-3 placeholder that only prices a near-idle peaking
    #   coal unit. Refine in NEISO calibration (doc-08 P11/P12) if Merrimack
    #   dispatch is visibly mis-leveled.
}

# Annual real escalation rate for coal prices.
# Reflects mine closures, rising rail transport costs, and declining
# domestic demand reducing economies of scale.
# Source: EIA AEO 2024 coal supply module — ~1% real escalation.
COAL_PRICE_ESCALATION: float = 0.01

# Delivered oil fuel price ($/MMBtu) for oil-fired peakers and steam units.
# Distillate (No. 2) fuel oil dominates the NYISO/ISO-NE oil peaker fleet;
# residual (No. 6) is the legacy oil-steam fuel. The blended delivered cost
# sits far above gas, so oil clears only in scarcity (peaker behaviour) —
# critical to Northeast winter price formation. Held flat (no commodity
# trajectory) since oil rarely runs and is not a price-setting baseload fuel.
# Source: EIA distillate (~$20/MMBtu) and residual (~$14/MMBtu) fuel oil
# delivered to the electric power sector, 2023-2024 average.
# Also the dual-fuel switching parity fallback: in backcast years the measured
# EIA-923 Schedule 5 monthly Petroleum receipt series
# (market_sim.data.fuel.iso_monthly_oil_prices; PJM ~$17-23/MMBtu, 2023-2025)
# takes precedence, and this flat value fills unreported months and forward
# years.
OIL_PRICE_PER_MMBTU: float = 18.0

# Delivered biomass fuel price ($/MMBtu) for wood/MSW/landfill-gas units.
# Biomass fuel is largely a low-cost waste/byproduct stream (mill residue,
# refuse, landfill gas), so its delivered cost is well below oil and roughly
# at parity with cheap coal on a $/MMBtu basis.
# Source: EIA wood & waste biomass delivered fuel cost, AEO 2024 (~$2.5/MMBtu).
BIOMASS_PRICE_PER_MMBTU: float = 2.5

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
    # Oil and biomass entries apply when a unit carries a matching plant-group
    # tag; EIA-classified oil/biomass units (no plant_group) fall back to the
    # flat 1 - EFORD derate. Source: NERC GADS by unit type and age.
    "OIL":        (0.06, 0.10, 0.003, 30, 0.04, 0.002, 30),
    "BIOMASS":    (0.07, 0.10, 0.002, 25, 0.04, 0.0015, 25),
}

# Carbon price trajectories ($/tCO2) by scenario path and year.
# Source: RFF / state programs.
CARBON_PRICE_PATHS: dict[str, dict[int, float]] = {
    "zero": {2026: 0, 2030: 0, 2040: 0, 2050: 0},     # RFF — no carbon price
    "low": {2026: 0, 2030: 8, 2040: 18, 2050: 25},    # RFF — low carbon price path
    "mid": {2026: 0, 2030: 15, 2040: 35, 2050: 50},   # RFF — mid carbon price path
    "high": {2026: 0, 2030: 30, 2040: 70, 2050: 110},  # RFF — high carbon price path
}

# State carbon-program allowance prices ($/tCO2, metric) by ISO and
# calendar year. Each year is the simple average of the four quarterly
# auction clearing prices (both programs clear each auction at one uniform
# price, and quarterly volumes are near-equal, so the simple mean is the
# volume-weighted mean to within cents). Backcasts charge this allowance
# cost on every in-state fossil unit's marginal cost via
# resolve_carbon_price (default-on; see ScenarioConfig.state_carbon_pricing).
#
# CAISO — CA cap-and-trade (CARB), $/metric ton as published.
# Source: CARB "Summary of Auction Settlement Prices and Results" /
#   CA-Quebec joint auction summary results reports (ww2.arb.ca.gov),
#   cross-checked against the WCI auction price history.
#   2023: Feb $27.85, May $30.33, Aug $35.20, Nov $38.73 -> $33.03
#   2024: Feb $41.76, May $37.02, Aug $30.24, Nov $31.91 -> $35.23
#   2025: Feb $29.27, May $25.87 (floor), Aug $28.76, Nov $28.32 -> $28.06
# NYISO is a RGGI state: every in-state fossil unit surrenders one RGGI CO2
# allowance per (short) ton emitted, so the auction clearing price enters
# marginal cost exactly as the CARB allowance does for CAISO. Each year is the
# simple average of that calendar year's four quarterly RGGI auction current-
# control-period clearing prices (the auctions clear at one uniform price and
# quarterly volumes are near-equal, so the simple mean is the volume-weighted
# mean to the cent). At a ~0.37 tCO2/MWh gas-CC rate this adds ~$5/MWh (2023) to
# ~$8/MWh (2025) — material to the NYISO price level though smaller than CA
# cap-and-trade (doc-07 design decision 4). Source: RGGI, Inc. auction results
# ("CO2 Allowances Sold for $X in the Nth RGGI Auction" press releases,
# rggi.org/auctions/auction-results):
#   2023: A59 (Mar) $12.50, A60 (Jun) $12.73, A61 (Sep) $13.85,
#         A62 (Dec) $14.88 -> $13.49
#   2024: A63 (Mar) $16.00, A64 (Jun) $21.03, A65 (Sep) $25.75,
#         A66 (Dec) $20.05 -> $20.71
#   2025: A67 (Mar) $19.76, A68 (Jun) $19.63, A69 (Sep) $22.25,
#         A70 (Dec) $26.73 -> $22.09
# Caveat: RGGI allowances are denominated per *short* ton CO2 while the model's
# emission_rate_co2 is per *metric* tonne, so charging these prices against the
# metric-tonne rate understates the true allowance cost by ~10.2% (1 t = 1.1023
# short tons). The understatement is small and keeps each stored value an exact,
# citable match to the published RGGI clearing prices; a future refinement can
# scale by 1.1023 if winter price fidelity demands it. Like CAISO, RGGI carries
# no border carbon adjustment on imports (contrast CARB's unspecified-import EF),
# so the NYISO import node is unaffected.
#
# NEISO — the same RGGI auctions (all six New England states are RGGI
# members, so the allowance cost applies ISO-wide; doc-08 design decision
# 3), but stored CONVERTED to the model's $/metric-tonne emission-rate
# unit at 1 short ton = 0.907185 t (x 1.10231):
#   2023: $13.49/short ton -> $14.87/t
#   2024: $20.71/short ton -> $22.83/t
#   2025: $22.09/short ton -> $24.35/t
# (Auction-level prices and source as the NYISO block above; press-release
# URLs rggi.org/sites/default/files/Uploads/Auction-Materials/
# {59..70}/PR*_Auction{59..70}.pdf, retrieved 2026-06-11.)
# HARMONIZATION NOTE: NYISO (above) deliberately stores the published
# short-ton clearing prices (exact citable match, ~10.2% understatement);
# NEISO stores the metric-converted values (unit-exact MC). The two RGGI
# entries should be unified one way or the other in a joint NYISO/NEISO
# calibration pass.
STATE_CARBON_PRICE_BY_ISO: dict[str, dict[int, float]] = {
    "CAISO": {2023: 33.03, 2024: 35.23, 2025: 28.06},
    "NYISO": {2023: 13.49, 2024: 20.71, 2025: 22.09},
    "NEISO": {2023: 14.87, 2024: 22.83, 2025: 24.35},
}

# CARB default emission factor for unspecified-source imported electricity
# (tCO2e/MWh). CAISO levies a border carbon adjustment on unspecified WECC
# imports at this factor x the allowance price; applied to the WECC import
# tranche prices (model/transmission.py::build_wecc_import_generators).
# Source: CARB Mandatory GHG Reporting Regulation (MRR), 17 CCR §95111(b) —
#   default emission factor for unspecified power, 0.428 MT CO2e/MWh.
CARB_UNSPECIFIED_IMPORT_EF: float = 0.428

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
# new entry at a realistic share of system peak demand. Each value is roughly
# half of the ISO's coincident peak — the share studies put at the point where
# incremental storage capacity value falls off sharply.
STORAGE_DEPLOYMENT_CEILING_MW: dict[str, float] = {
    "ERCOT": 45_000.0,  # ~53% of ~85 GW peak. Source: ERCOT CDR
    "CAISO": 25_000.0,  # ~52% of ~48 GW peak. Source: CAISO IEPR
    "PJM": 75_000.0,    # ~50% of ~150 GW peak. Source: PJM Load Forecast Report 2024
    "NYISO": 16_000.0,  # ~50% of ~32 GW peak. Source: NYISO Gold Book 2024
    "NEISO": 13_000.0,  # ~50% of ~26 GW peak. Source: ISO-NE CELT Report 2024
}

# Max new storage power per year (MW). Source: ERCOT CDR, CAISO TPP queue data,
# eastern-ISO interconnection-queue throughput.
STORAGE_ANNUAL_BUILD_CAP_MW: dict[str, float] = {
    "ERCOT": 5_000.0,
    "CAISO": 3_000.0,
    "PJM": 4_000.0,    # large queue but slower interconnection. Source: PJM queue 2024
    "NYISO": 1_500.0,  # Source: NYISO interconnection queue 2024
    "NEISO": 1_200.0,  # Source: ISO-NE interconnection queue 2024
}

# Cap on the share of one year's storage build budget that any single
# technology may take. Below 1.0 the annual build diversifies across the
# profitable technologies in merit order rather than the top-margin tech
# monopolizing the whole budget (the "winner-take-all" failure mode).
# Source: modeling assumption — interconnection queues and supply chains
# spread build across durations even when one tech leads on margin.
STORAGE_TECH_BUILD_SHARE_CAP: float = 0.6

# Share of deployed storage power by technology type.
# Source: NREL ATB 2024 technology mix assumptions.
STORAGE_TECH_POWER_SHARE: dict[str, float] = {
    "li_ion_4hr": 0.70,
    "li_ion_8hr": 0.25,
    "iron_air": 0.05,
}


# --- Storage capacity / resource-adequacy value, by market design ---------
#
# The storage new-entry screen stacks two value streams: energy arbitrage
# (every market) and resource-adequacy capacity value (only markets that pay
# for capacity). ERCOT is energy-only — scarcity value already flows through
# the energy price via ORDC/VOLL — so its capacity stream is OFF. The capacity
# markets (PJM/NYISO/ISO-NE) and CAISO's RA program pay a separate capacity
# price, so theirs is ON. Toggling ``capacity_market`` per ISO keeps the screen
# modular as market designs diverge.


@dataclass(frozen=True)
class MarketDesign:
    """Storage revenue-stack switches and parameters for one ISO/market.

    ``capacity_market`` gates the resource-adequacy value stream entirely.
    ``net_cone_per_kw_yr`` is the marginal cost of new entry of the capacity
    resource the market prices against (the clearing-price anchor), in
    $/kW-yr. A storage unit earns ``net_cone × ELCC(duration) × derate`` of it,
    where the ELCC (effective load-carrying capability) credit rises with
    duration and the derate falls as storage saturates the peak.
    """

    capacity_market: bool
    net_cone_per_kw_yr: float = 0.0


# Per-ISO market design. ISOs absent here fall back to ``DEFAULT_MARKET_DESIGN``
# (energy-only) so a new ISO is conservative until its capacity rules are added.
MARKET_DESIGN: dict[str, MarketDesign] = {
    # Energy-only: scarcity is monetized through the energy price, not a
    # separate capacity payment. Source: ERCOT market design (ORDC).
    "ERCOT": MarketDesign(capacity_market=False),
    # RA program with a soft capacity price. Source: CAISO RA, CPUC net-CONE.
    "CAISO": MarketDesign(capacity_market=True, net_cone_per_kw_yr=90.0),
    # Capacity markets. Net-CONE anchors near the CT reference resource.
    # Source: PJM 2025/26 BRA planning parameters (net-CONE ~$100/kW-yr).
    "PJM": MarketDesign(capacity_market=True, net_cone_per_kw_yr=100.0),
    # Source: NYISO ICAP demand-curve reset net-CONE.
    "NYISO": MarketDesign(capacity_market=True, net_cone_per_kw_yr=110.0),
    # Source: ISO-NE FCM net-CONE.
    "NEISO": MarketDesign(capacity_market=True, net_cone_per_kw_yr=95.0),
}

DEFAULT_MARKET_DESIGN: MarketDesign = MarketDesign(capacity_market=False)

# Effective load-carrying capability (ELCC) of storage as a function of
# duration (hours), as (duration_hr, credit) breakpoints; linearly
# interpolated, clamped at the ends. Short-duration storage covers only the
# sharpest peak hours so its firm-capacity credit is well below 1; the credit
# saturates toward 1.0 as duration lengthens enough to ride through a
# multi-hour net-peak. Source: NREL/E3 ELCC studies, PJM ELCC class ratings.
STORAGE_ELCC_BY_DURATION: list[tuple[float, float]] = [
    (2.0, 0.40),
    (4.0, 0.60),
    (6.0, 0.75),
    (8.0, 0.87),
    (10.0, 0.93),
    (12.0, 0.97),
    (24.0, 1.00),
]

# Marginal ELCC saturation. As cumulative storage power approaches the
# deployment ceiling (≈ half the system peak), each additional MW of storage
# adds less firm capacity — the well-documented decline in marginal storage
# ELCC at high penetration, which is what tilts the economics from short-
# toward long-duration storage. The marginal credit is multiplied by
# ``(1 - penetration)^STORAGE_ELCC_SATURATION_EXPONENT`` where ``penetration``
# is existing storage power / ceiling. Source: NREL ELCC saturation studies.
STORAGE_ELCC_SATURATION_EXPONENT: float = 1.5

# Cycling-degradation cost. Each MWh discharged consumes a slice of the
# battery's cycle life; replacing it costs a fraction of the energy-capacity
# capex (only the cell stack degrades, not the power electronics / BOS, and
# warranties run to ~80% retention, so the full energy capex over rated cycles
# overstates the true marginal cost). Degradation $/MWh discharged =
# capex_per_kwh × 1000 / cycles × STORAGE_DEGRADATION_REPLACEMENT_FRACTION.
# Source: modeling simplification grounded in NREL ATB augmentation costs and
# LFP warranty cycle life; tunable.
STORAGE_DEGRADATION_REPLACEMENT_FRACTION: float = 0.25

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
    # Eastern-ISO caps are Tier 3 approximations of recent annual
    # commercial-operation throughput (not queue *requests*, which run far
    # higher). Source: LBNL "Queued Up" 2024 completion-rate analysis; ISO
    # planning reports. needs-citation: verify against each ISO's latest
    # planning report before quoting any eastern-ISO forecast.
    "PJM": 10,
    "MISO": 10,
    "SPP": 6,
    "NYISO": 4,
    "NEISO": 4,
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
    # Eastern-ISO per-tech caps: Tier 3, sized from each ISO's recent build
    # mix (LBNL "Queued Up" 2024; ISO planning reports). needs-citation.
    "PJM": {
        "wind": 1.5, "solar": 6.0, "gas_cc": 4.0, "nuclear": 1.0,
        "geothermal": 0.0,      # no utility-scale resource in footprint
        "offshore_wind": 2.0,   # NJ/MD/DE BOEM lease areas
    },
    "MISO": {
        "wind": 4.0, "solar": 6.0, "gas_cc": 3.0, "nuclear": 1.0,
        "geothermal": 0.0,
        "offshore_wind": 0.0,   # Great Lakes not leased
    },
    "SPP": {
        "wind": 4.0, "solar": 3.0, "gas_cc": 2.0, "nuclear": 0.5,
        "geothermal": 0.0,
        "offshore_wind": 0.0,
    },
    "NYISO": {
        "wind": 1.0, "solar": 2.0, "gas_cc": 1.0, "nuclear": 0.5,
        "geothermal": 0.0,
        "offshore_wind": 1.5,   # NY Bight BOEM lease areas
    },
    "NEISO": {
        "wind": 1.0, "solar": 2.0, "gas_cc": 1.0, "nuclear": 0.5,
        "geothermal": 0.0,
        "offshore_wind": 2.0,   # MA/RI BOEM lease areas
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
    "flow_battery": 3.0,    # GW global installed vanadium-redox flow. Source: PNNL 2023,
                            # BNEF LDES tracker 2024 (China VRFB buildout dominates).
    "compressed_air": 1.5,  # GW global adiabatic/diabatic CAES — Huntorf, McIntosh,
                            # Zhangjiakou, Jintan. Source: NREL ATB 2024, IEA 2024.
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
    "flow_battery": 0.8,    # GW/yr global VRFB additions. Source: BNEF LDES tracker 2024.
    "compressed_air": 0.3,  # GW/yr global CAES additions. Source: IEA 2024 pipeline.
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
    "SPP": {"wind": 0.41, "solar": 0.24},
    "NYISO": {"wind": 0.26, "solar": 0.15},
    "NEISO": {"wind": 0.30, "solar": 0.15},
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
    # Tier 3, ~year-end-2024 utility-scale nameplate (BTM excluded).
    # Source: EIA-860 2024 / ISO planning reports, rounded. needs-citation:
    # refresh from the processed EIA-860 parquet before quoting a forecast.
    "PJM": {"wind": 11000.0, "solar": 14000.0},
    "MISO": {"wind": 32000.0, "solar": 7000.0},
    "SPP": {"wind": 34000.0, "solar": 600.0},
    "NYISO": {"wind": 2400.0, "solar": 1500.0},
    "NEISO": {"wind": 1400.0, "solar": 2700.0},
}

# Priced import/export node, per ISO (playbook §8.2): an interconnected ISO
# models its neighbors as a zero-load external zone holding a stepped import
# supply curve (tranches the LP dispatches in merit order) and a set of
# export sinks (negative-generation blocks priced at the neighbors'
# willingness-to-pay). Net interchange then responds to the ISO's own prices:
# imports clear when the internal price exceeds a tranche's cost, exports
# when it falls below a sink's price.
#
# IMPORT_TRANCHES / EXPORT_TRANCHES entries: (name, capacity MW, $/MWh).
IMPORT_TRANCHES: dict[str, list[tuple[str, float, float]]] = {
    # CAISO WECC import supply merit order. Tier 3 (calibration) — fitted to
    # the pooled 2023-2025 EIA-930 CISO net-interchange duration curve by
    # scripts/derive_import_tranches.py (measured-only mode; the existing CAISO
    # bundle has no priced node, so a bundle-mode price fit would be circular).
    # CAISO is a heavy, growing net importer: −28.9 / −32.4 / −36.2 TWh and
    # imports in 86% / 89% / 91% of hours across 2023-25, ~20-25% of energy —
    # the single biggest supply block after gas. Block capacities tile the
    # import duration curve (median import ~4.2 GW, deepest hour ~11.0 GW);
    # the cheap PNW_hydro_base block is the near-always-on baseload and the
    # desert-SW gas/scarcity blocks layer in as CAISO's price climbs. Fit
    # quality vs the measured series (price-orthogonal optimal placement, the
    # bound the LP can reach): annual net imports within 1-3%, duration-curve
    # RMSE ~560 MW (was ~1,400 for the prior placeholder), import-hour share
    # 83-88% vs 86-91% measured. Aggregate import capacity 11.4 GW sits between
    # the deepest measured hour (11.0 GW) and the ~12-15 GW WECC simultaneous-
    # import rating (COI/Path 66 ~4.8 GW + PDCI ~3.1 GW + Path 46 West-of-River
    # + Path 45). Prices are pre-carbon delivered WECC energy costs, cheapest
    # first and all above every export sink (no import↔export arbitrage); the
    # CARB border-carbon adder is layered on at build time
    # (build_import_generators). Block price proxies:
    #   - PNW_hydro_base: COI firm Pacific-NW hydro, near-zero SRMC sold at
    #     economy energy; the always-on baseload. ~$14 (cf NYISO HQ_hydro $14).
    #   - PNW_midC: Mid-Columbia hydro/wind shoulder over COI/PDCI. ~$26.
    #   - DSW_solar_PV: desert-SW solar + Palo Verde nuclear midday, Path 46.
    #   - DSW_CCGT / DSW_CT: desert-SW gas combined-cycle / combustion turbine
    #     (Mead / Four Corners), on-peak.
    #   - WECC_scarcity: west-wide peak economy energy in CAISO heat events.
    # Modeled clearing-frequency validation (vs the solved CAISO price duration
    # curve) lives in the LMP/benchmark pass (CAISO P10/P11), not here.
    # Source: EIA-930 CISO net-interchange 2023-2025; CAISO OASIS path ratings.
    "CAISO": [
        ("PNW_hydro_base", 800.0, 14.0),    # COI firm PNW hydro — baseload
        ("PNW_midC", 1800.0, 26.0),         # Mid-C hydro/wind shoulder
        ("DSW_solar_PV", 1800.0, 34.0),     # Desert SW solar + Palo Verde
        ("DSW_CCGT", 1800.0, 48.0),         # Desert SW combined-cycle gas
        ("DSW_CT", 2200.0, 66.0),           # Desert SW combustion turbine
        ("WECC_scarcity", 3000.0, 92.0),    # Peak west-wide scarcity energy
    ],
    # PJM scarcity imports (MISO / NYISO / the Carolinas selling into PJM
    # when PJM prices spike). Total capacity bounds the deepest measured
    # net-import hour (−2.9 GW in 2023, −3.8 GW in 2024). Prices sit above
    # every PJM export sink so import and export blocks can never clear
    # against each other in the same hour. Tier 3 (calibration) — fitted to
    # the 2023 net-interchange duration curve; see EXPORT_TRANCHES["PJM"]
    # for the method and sources.
    "PJM": [
        ("import_scarcity_1", 1000.0, 46.0),
        ("import_scarcity_2", 3000.0, 60.0),
    ],
    # NYISO is a large, near-constant net importer: EIA-930 (NYIS hourly)
    # shows imports in 100% of 2023 hours, −2,677 MW avg (+23.45 TWh net
    # import), 922 MW in the lightest-import hour (p2) up to 5,929 MW deepest.
    # The supply curve is the neighbor merit order, cheapest first; each block
    # is priced at the neighbor hub it proxies and sized to a step of the
    # import duration curve (scripts/derive_import_tranches.py against the
    # NYIS net-interchange series). Imports clear when NYISO's internal price
    # rises above a block's price — so the cheap HQ/Ontario hydro is the
    # always-on baseload and PJM/ISO-NE/scarcity blocks layer in as price
    # climbs. Tier 3 (calibration). Neighbor-price proxies:
    #   - HQ_hydro: Hydro-Québec is ~95% hydro with near-zero SRMC; the
    #     Châteauguay/Cedars economy-energy price into NY zones D–F runs a
    #     winter premium. Proxy ~$14/MWh. Source: HQ generation mix (HQ
    #     Annual Report); NYISO–HQ Châteauguay interface schedules.
    #   - IESO_Ontario: Ontario HOEP averaged ≈C$28/MWh (≈US$21) in 2023 on
    #     surplus nuclear+hydro baseload (often low/negative). Proxy ~$24.
    #     Source: IESO Hourly Ontario Energy Price (HOEP) 2023.
    #   - PJM_west: PJM Western Hub / AEP-Dayton day-ahead LMP averaged
    #     ≈$30/MWh in 2023 (cheap Marcellus gas). Proxy ~$34. Source: PJM
    #     Western Hub LMP, Monitoring Analytics SOM 2023.
    #   - ISONE_tie: ISO-NE Mass Hub LMP averaged ≈$38/MWh in 2023. Proxy
    #     ~$44 (it sets the upper-middle imports). Source: ISO-NE Mass Hub.
    #   - import_scarcity: HQ/PJM peak economy energy in NYISO scarcity hours
    #     (top decile, where NYISO LMP > $70). Source: NYISO LMP tail.
    "NYISO": [
        ("HQ_hydro", 900.0, 14.0),
        ("IESO_Ontario", 1200.0, 24.0),
        ("PJM_west", 1100.0, 34.0),
        ("ISONE_tie", 800.0, 44.0),
        ("import_scarcity", 1900.0, 75.0),
    ],
    # NEISO is a steady net importer (EIA-930 ISNE hourly): −1,728 MW avg /
    # +15.14 TWh net import in 2023 (98% import hours), easing to −1,175 MW /
    # +10.30 TWh in 2024 (84%). Imports peak at ~4,386 MW. Blocks priced at
    # the neighbor hub, cheapest first; the HQ HVDC ties are the always-on
    # baseload. Tier 3 (calibration). Neighbor-price proxies:
    #   - HQ_PhaseII: the ~2,000 MW Hydro-Québec Phase II HVDC into NEMA
    #     (Sandy Pond); HQ hydro SRMC near zero, sold at economy energy.
    #     Proxy ~$18. Source: ISO-NE external-interface schedules; HQ mix.
    #   - Highgate: the VT–HQ HVDC tie (~225 MW) into northern NE; same HQ
    #     hydro proxy, slight wheeling premium ~$22. Source: ISO-NE/VELCO
    #     Highgate ratings.
    #   - NB_north: the New England–New Brunswick ties into Maine (~700 MW),
    #     NB hydro/nuclear. Proxy ~$30. Source: ISO-NE–NB interface.
    #   - NYISO_CT: the NYISO ties into Connecticut — Cross-Sound Cable
    #     (346 MW) + Northport–Norwalk (200 MW) + the NY–NE AC interface.
    #     Priced at the NYISO Hud Valley / Mass Hub seam ~$36. Source:
    #     NYISO–ISO-NE interface schedules.
    #   - import_scarcity: HQ/NY peak economy energy in ISNE scarcity hours.
    "NEISO": [
        ("HQ_PhaseII", 1000.0, 18.0),
        ("Highgate", 300.0, 22.0),
        ("NB_north", 800.0, 30.0),
        ("NYISO_CT", 1100.0, 36.0),
        ("import_scarcity", 1200.0, 68.0),
    ],
}

# Export sinks: each block absorbs up to its capacity as *negative*
# generation, paying its $/MWh price (the LP credits the price as avoided
# cost, so the ISO exports whenever its marginal cost is below it).
EXPORT_TRANCHES: dict[str, list[tuple[str, float, float]]] = {
    # CAISO midday solar-oversupply exports. Tier 3 (calibration) — fitted
    # alongside the import tranches to the pooled 2023-2025 CISO
    # net-interchange duration curve (scripts/derive_import_tranches.py). CAISO
    # exports in ~14% / 11% / 9% of hours (2023-25), shrinking as in-state load
    # and storage grow; within-export magnitude is small (median ~1.2 GW) with
    # a ~6.4 GW peak. Two sinks tile that tail: a shallow block that absorbs
    # the common midday surplus sold to WECC neighbors, and a deeper block for
    # extreme oversupply that clears only against in-state curtailment. Both
    # priced below every import tranche (no import↔export arbitrage); the
    # shallow block carries a small positive willingness-to-pay (neighbors buy
    # cheap CA solar), the deep block the $0 curtailment floor. Adding the two
    # sinks brings the joint duration-curve RMSE to ~560 MW and annual net
    # interchange to ~100% of measured. Source: EIA-930 CISO net interchange.
    "CAISO": [
        ("export_solar", 2500.0, 8.0),     # midday surplus sold to WECC
        ("export_curtail", 4000.0, 0.0),   # deep oversupply curtailment floor
    ],
    # PJM was a ~40 TWh / +4,564 MW-avg net exporter in 2023, easing to
    # +32.7 TWh in 2024 and +18.0 TWh in 2025 (EIA-930). Blocks proxy the
    # neighbor demand stack (NYISO cables, MISO, the Carolinas/TVA):
    # capacities fitted to the 2023 net-interchange duration curve against
    # the pjm_6 baseline price duration (quantile pairing,
    # scripts/derive_import_tranches.py). Prices were originally fitted to
    # 2023 alone (sinks 18-42), which over-exported 2024 by +9.6 TWh and
    # 2025 by +7.5 TWh — the surplus backfilled by marginal gas (PJM run-16
    # residuals). PJM run 18 shifted every sink down $6 to the values
    # below: the three-year compromise that brings 2024 gas inside the 5%
    # class tolerance and lands 2024/2025 net interchange near the EIA-930
    # actuals, trading away some 2023 export depth (the neighbor-demand
    # year-shape is price-orthogonal, so a static price-keyed node cannot
    # hit 2023's +40 and 2024's +33 simultaneously). PJM run 19 then put
    # $4 back on the two cheapest sinks: dropping the trough floor to
    # $12-14 had pushed cheap-hour prices below the coal committed bids,
    # bleeding 2023/24 coal out of its class tolerance — the upper four
    # sinks keep the full -$6 that did the gas-2024 work. Backcasts without
    # --priced-interchange ignore these blocks: they serve the measured
    # tie-line schedule instead (eia_loader.pjm_net_interchange). NOTE: the
    # 2025 tie-line CSV diverges from EIA-930 May-2025 onward (+32.9 vs
    # +18.0 TWh annual) — fit against EIA-930, not the tie-line file, for
    # 2025+. Tier 3 (calibration); source CSV:
    # inputs/raw-data/iso-specific-transmission/
    # PJM_2023_import_export_act_sch_interchange.csv +
    # results/calibration/pjm_6_ccpeak, repriced on pjm_16_bit_trim.
    "PJM": [
        ("export_firm", 700.0, 36.0),
        ("export_peak", 1700.0, 30.0),
        ("export_mid", 1700.0, 24.0),
        ("export_shoulder", 1800.0, 19.0),
        ("export_offpeak", 1800.0, 18.0),
        ("export_trough", 2100.0, 16.0),
    ],
    # NYISO almost never exports (EIA-930 NYIS: net export ≤ +131 MW in 2023,
    # +449 in 2024 — well under 1% of hours), so a single small sink absorbs
    # the rare upstate-hydro/wind surplus in near-zero-price hours. Priced
    # below every import tranche (no import↔export arbitrage). Tier 3.
    # Source: NYIS net-interchange tail (export-positive p100); the neighbor
    # WTP in those hours is Ontario HOEP / PJM West off-peak (~$10).
    "NYISO": [
        ("export_surplus", 600.0, 10.0),
    ],
    # NEISO exports more than NYISO — up to ~1,045 MW (2023) and ~1,770 MW
    # (2024) in low-load/high-hydro hours (the 2% export share in 2023 grew
    # to 16% in 2024 as load softened). Two sinks proxy the neighbor demand
    # stack (surplus to NY/NB): a shallow firm block and a deeper trough
    # block, both priced below every NEISO import tranche. Tier 3. Source:
    # ISNE net-interchange tail; NYISO/NB off-peak WTP.
    "NEISO": [
        ("export_firm", 700.0, 16.0),
        ("export_trough", 1100.0, 8.0),
    ],
}

# ISOs whose backcasts serve interchange through the priced import/export node
# by default (no --priced-interchange flag required).
#
# CAISO is the canonical case: load_demand does NO interchange netting for
# CAISO (the CISO series is net load; eia_loader.load_demand leaves the
# interchange array zero regardless of include_interchange), so without the
# priced node the domestic fleet must serve all of CAISO's ~30 TWh/yr of net
# imports itself and over-generates gas. There is no measured-schedule mode for
# CAISO to displace, so priced interchange is the only correct default. The
# WECC_import node is baked into _caiso_config, so enabling it is free.
#
# PJM/NYISO/NEISO are deliberately ABSENT: their calibrated backcast topologies
# serve the *measured* tie-line schedule by default, and --priced-interchange
# is the opt-in used to validate the node's tranche calibration.
PRICED_INTERCHANGE_DEFAULT_ISOS: frozenset[str] = frozenset({"CAISO"})


def resolve_priced_interchange(flag: bool | None, iso: str) -> bool:
    """Resolve the ``--priced-interchange`` tri-state flag for ``iso``.

    ``flag`` is ``True``/``False`` when set explicitly on the CLI
    (``--priced-interchange`` / ``--no-priced-interchange``), or ``None`` to
    fall back to the per-ISO default in
    :data:`PRICED_INTERCHANGE_DEFAULT_ISOS`.
    """
    if flag is not None:
        return flag
    return iso in PRICED_INTERCHANGE_DEFAULT_ISOS

# Name of each ISO's external import/export zone. CAISO's is baked into its
# topology (_caiso_config); PJM's is appended on demand by
# transmission.extend_with_import_node, so the calibrated 8-zone backcast
# topology (which serves the *measured* interchange schedule instead) is
# untouched.
IMPORT_ZONE: dict[str, str] = {
    "CAISO": "WECC_import",
    "PJM": "PJM_external",
    # NYISO's external node is appended on demand (like PJM); the backcast
    # 5-zone topology is untouched.
    "NYISO": "NYISO_external",
    # NEISO's is baked into _neiso_config (like CAISO's WECC_import): the
    # HQ_import zone already carries the HQ Phase II tie, so the import
    # tranches/sinks land there and extend_with_import_node is a no-op.
    "NEISO": "HQ_import",
}

# Links joining an appended external zone to its border zones:
# (border zone, TTC MW). CAISO needs no entry — its links are part of its
# topology (Path 66/COI, Path 46/WOR). PJM TTCs bound the widest measured
# 2023-24 per-border-zone tie flow (eia_loader.pjm_zonal_interchange):
# ComEd −2.3..+7.4 GW, AEP-Ohio −1.0..+4.8, ATSI −5.7..+5.0, Dominion
# −6.2..+3.1, EMAAC −0.1..+5.7. West-APS / Central-PA / SWMAAC carry no
# mapped ties. Source: PJM tie-line actual interchange
# (inputs/raw-data/iso-specific-transmission/). Tier 3 — verify against
# PJM's published interface ratings.
IMPORT_NODE_LINKS: dict[str, list[tuple[str, float]]] = {
    "PJM": [
        ("PJM_ComEd", 7500.0),
        ("PJM_AEP_Ohio", 4900.0),
        ("PJM_ATSI", 5800.0),
        ("PJM_Dominion", 6300.0),
        ("PJM_EMAAC", 5700.0),
    ],
    # NYISO external node → border-zone links. The single external bubble
    # holds all import tranches/sinks; the LP routes each through whichever
    # link reaches load, subject to the internal interfaces (Central-East,
    # UPNY-SENY, Dunwoodie-South). TTCs envelope the real interface ratings
    # of the ties landing in each model zone (sum ≈ 6.4 GW ≥ the 5.9 GW
    # deepest measured import). Tier 3 — verify against NYISO operating-limit
    # postings. Source: NYISO interface limits ("Gold Book"); tie ratings.
    #   - Upstate_West: IESO/Ontario (Niagara zone A + St-Lawrence ~2.0 GW)
    #     plus PJM West (Homer City/Keystone ~1.0 GW).
    #   - Capital_Hudson: HQ Châteauguay/Cedars (~1.1 GW) + the NY–NE AC
    #     interface (~0.6 GW).
    #   - Lower_Hudson: PJM into the lower Hudson Valley / 5018 line toward
    #     NYC (~1.2 GW).
    #   - Long_Island: ISO-NE Cross-Sound Cable (346 MW) + Northport–Norwalk
    #     (200 MW) ≈ 0.55 GW.
    "NYISO": [
        ("Upstate_West", 3000.0),
        ("Capital_Hudson", 1700.0),
        ("Lower_Hudson", 1200.0),
        ("Long_Island", 550.0),
    ],
    # NEISO needs no entry: its HQ_import links (HQ Phase II → Boston,
    # Highgate/NB → North, NYISO ties → Connecticut) are baked into
    # _neiso_config, so extend_with_import_node is a no-op there.
}

# Import tranche forced outage rate, per ISO. CAISO's WECC supply blocks
# carry a generation-like availability (NERC GADS — representative for
# out-of-state generation); PJM's blocks are scheduled interties whose
# availability is already embedded in the fitted capacities.
IMPORT_EFORD: dict[str, float] = {
    "CAISO": 0.02,
    "PJM": 0.0,
    # NYISO/NEISO blocks are scheduled interties (HQ HVDC, PJM/Ontario/NB
    # AC ties) whose availability is already embedded in the fitted
    # capacities — no extra derate, as for PJM.
    "NYISO": 0.0,
    "NEISO": 0.0,
}

# Backwards-compatible aliases for the original CAISO-only WECC names.
WECC_IMPORT_TRANCHES: list[tuple[str, float, float]] = IMPORT_TRANCHES["CAISO"]
WECC_EXPORT_CAP_MW: float = EXPORT_TRANCHES["CAISO"][0][1]
WECC_IMPORT_EFORD: float = IMPORT_EFORD["CAISO"]

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
