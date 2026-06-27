"""Physical and economic constants with citation comments."""

from dataclasses import dataclass, field

from market_sim.config.paths import CALIBRATION_DIR

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
# Coal is not commitment-screened: EIA-930 confirms ERCOT coal runs all 8,760
# hours, cycling output level rather than starting and stopping.

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
HYDRO_CLIMATOLOGY_YEARS: tuple[int, ...] = (2021, 2022, 2023, 2024, 2025)

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

# Gas-fired generation availability factors by ISO.
# Source: NERC GADS 2019-2023.
GAS_AVAILABILITY_FACTOR: dict[str, float] = {
    "ERCOT": 0.85,  # was 0.83. NERC GADS 2019-2023, ERCOT fleet.
    "CAISO": 0.89,  # was 0.88. NERC GADS 2019-2023, CAISO fleet.
    "PJM": 0.87,  # NERC GADS 2019-2023, PJM fleet. TODO: verify
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
# scripts/derive_nuclear_monthly_cf.py excludes it from the fleet pmax for
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
    # Derivation/verify: scripts/derive_nuclear_monthly_cf.py --isos PJM.
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
    # Derivation/verify: scripts/derive_nuclear_monthly_cf.py --isos MISO.
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
}

# Annual demand growth rates by ISO, scenario path, and era.
# Near-term (2026-2030): elevated by data center and industrial load.
# Long-term (2031-2050): decelerates as pipeline matures.
# Source: EIA STEO July 2025, ERCOT CDR Dec 2024, CAISO IEPR 2024.
DEMAND_GROWTH_RATES: dict[str, dict[str, dict[str, float]]] = {
    "ERCOT": {
        "low": {"near": 0.03, "long": 0.015},
        "mid": {"near": 0.05, "long": 0.025},
        "high": {"near": 0.08, "long": 0.04},
    },
    "CAISO": {
        "low": {"near": 0.005, "long": 0.005},
        "mid": {"near": 0.015, "long": 0.010},
        "high": {"near": 0.025, "long": 0.018},
    },
    # PJM Fleet Parameters — Source: PJM Load Forecast Report 2024, Table B-1.
    # Tier: 2. TODO: verify
    "PJM": {
        "low": {"near": 0.020, "long": 0.010},
        "mid": {"near": 0.035, "long": 0.018},
        "high": {"near": 0.060, "long": 0.030},
    },
    # NYISO Fleet Parameters — Source: NYISO Gold Book 2024, Table I-3.
    # Tier: 2. TODO: verify
    "NYISO": {
        "low": {"near": 0.005, "long": 0.005},
        "mid": {"near": 0.015, "long": 0.010},
        "high": {"near": 0.025, "long": 0.018},
    },
    # NEISO Fleet Parameters — Source: ISO-NE CELT Report 2024.
    # Tier: 2. TODO: verify
    "NEISO": {
        "low": {"near": 0.005, "long": 0.005},
        "mid": {"near": 0.015, "long": 0.010},
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
        2023: 2.54,
        2024: 2.19,  # EIA Henry Hub spot annual average (historical)
        2025: 3.52,  # EIA Henry Hub spot annual average (2025 historical actual,
        # matches calibration_reference.henry_hub_actual; was a stale 2.88
        # forecast value). Consumed only by the backcast neighbor-price seam for
        # 2025 (forecasts start at START_YEAR 2026), so this keeps each
        # neighbor's gas consistent with the ISO's own 2025 delivered gas.
        2026: 2.70,
        2027: 2.55,
        2028: 2.50,
        2029: 2.48,
        2030: 2.45,
        2031: 2.43,
        2032: 2.42,
        2033: 2.41,
        2034: 2.40,
        2035: 2.40,
        2036: 2.42,
        2037: 2.45,
        2038: 2.48,
        2039: 2.52,
        2040: 2.55,
        2041: 2.60,
        2042: 2.65,
        2043: 2.70,
        2044: 2.75,
        2045: 2.80,
        2046: 2.85,
        2047: 2.90,
        2048: 2.95,
        2049: 3.00,
        2050: 3.05,
    },
    # AEO Reference case -> model "mid" gas price path.
    "mid": {
        2023: 2.54,
        2024: 2.19,  # EIA Henry Hub spot annual average (historical)
        2025: 3.52,  # EIA Henry Hub spot annual average (2025 historical actual,
        # matches calibration_reference.henry_hub_actual; was a stale 2.88
        # forecast value). Consumed only by the backcast neighbor-price seam for
        # 2025 (forecasts start at START_YEAR 2026), so this keeps each
        # neighbor's gas consistent with the ISO's own 2025 delivered gas.
        2026: 3.40,
        2027: 3.20,
        2028: 3.30,
        2029: 3.40,
        2030: 3.50,
        2031: 3.55,
        2032: 3.60,
        2033: 3.65,
        2034: 3.70,
        2035: 3.80,
        2036: 3.90,
        2037: 4.00,
        2038: 4.05,
        2039: 4.10,
        2040: 4.15,
        2041: 4.20,
        2042: 4.25,
        2043: 4.30,
        2044: 4.40,
        2045: 4.45,
        2046: 4.50,
        2047: 4.55,
        2048: 4.65,
        2049: 4.70,
        2050: 4.80,
    },
    # AEO Low Oil and Gas Supply case -> model "high" gas price path.
    # Lower resource recovery + slower tech = higher prices.
    "high": {
        2023: 2.54,
        2024: 2.19,  # EIA Henry Hub spot annual average (historical)
        2025: 3.52,  # EIA Henry Hub spot annual average (2025 historical actual,
        # matches calibration_reference.henry_hub_actual; was a stale 2.88
        # forecast value). Consumed only by the backcast neighbor-price seam for
        # 2025 (forecasts start at START_YEAR 2026), so this keeps each
        # neighbor's gas consistent with the ISO's own 2025 delivered gas.
        2026: 3.60,
        2027: 3.80,
        2028: 4.10,
        2029: 4.40,
        2030: 4.70,
        2031: 4.90,
        2032: 5.10,
        2033: 5.30,
        2034: 5.50,
        2035: 5.70,
        2036: 5.90,
        2037: 6.10,
        2038: 6.30,
        2039: 6.50,
        2040: 6.70,
        2041: 6.90,
        2042: 7.10,
        2043: 7.30,
        2044: 7.50,
        2045: 7.70,
        2046: 7.90,
        2047: 8.10,
        2048: 8.30,
        2049: 8.50,
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
#   (gas_hub_basis_overlay; data/raw/gas_basis_by_iso_month.csv),
#   which makes this scalar a forward-year/fallback value only — like the
#   CAISO +1.20 seed.
# MISO: a footprint-wide blend with no single hub. Northern MISO gas plants
#   (IL/WI/MI/MN) price off Chicago Citygate / MichCon (a modest premium driven
#   by interstate transport), while southern MISO (LA/MS/AR) prices essentially
#   at Henry Hub (near-zero basis). The public proxy is the EIA Illinois
#   natural-gas *citygate* series (n3050il3m): 2024 monthly avg = $3.495/Mcf
#   = $3.37/MMBtu (1 Mcf ~ 1.037 MMBtu) vs Henry Hub $2.22/MMBtu -> a raw
#   +$1.15/MMBtu. BUT that EIA "citygate" is the LDC-delivered price (it bakes
#   in full distribution transport), an UPPER BOUND that overstates power-plant
#   burn cost: the Chicago Citygate *trading hub* spot traded ~Henry Hub parity
#   in 2024 (Midwest hubs were weak vs HH), and most MISO gas plants buy nearer
#   the trading hub plus a small transport adder, not the LDC citygate. To keep
#   MISO on the same plant-delivered footing as the PJM/NYISO EIA-923 basis
#   (and not overstate the large southern-MISO Henry-Hub-priced fleet), we
#   reconcile the LDC-citygate proxy down to a footprint blend of +0.30/MMBtu
#   (≈ trading-hub parity + modest northern transport, net of ~$0 southern
#   basis). Refine with EIA-923 MISO Schedule-5 plant receipts in M8.
#   Source: EIA Illinois citygate (n3050il3m) + Henry Hub spot, 2024 avg.
# These are annual average differentials, held constant across the
# projection period for simplicity.
#
# Delivered price = Henry Hub + basis differential
GAS_BASIS_DIFFERENTIAL: dict[str, float] = {
    "ERCOT": -0.50,  # Waha discount; EIA NG Weekly, 2024 avg
    "CAISO": 1.20,  # SoCal Citygate premium; EIA NG Weekly, 2024 avg
    "PJM": 0.67,  # EIA-923 delivered-gas basis (see below)
    "NYISO": 0.55,  # EIA-923 delivered-gas basis (see below)
    "NEISO": 1.10,  # EIA-923 delivered-gas basis, normal-year (see below)
    "MISO": 0.30,  # Chicago Citygate footprint blend, reconciled (see above)
}

# --- Monthly Gas Price Seasonality Factors ---
# Source: EIA Henry Hub spot price monthly averages, 2019-2024 (excluding
#   anomalous Feb 2021 Uri event and Jan 2026 spike).
# Computed as avg monthly price / annual avg price for each year, then
#   averaged across years. Captures the winter heating premium and
#   shoulder-season discount. Applied as multiplicative factors to the
#   annual trajectory price. Sum of factors / 12 = 1.0 (budget-neutral).
GAS_MONTHLY_SEASONALITY: dict[int, float] = {
    1: 1.15,  # January — winter heating demand peak
    2: 1.10,  # February
    3: 1.02,  # March — shoulder
    4: 0.92,  # April — injection season begins
    5: 0.90,  # May
    6: 0.93,  # June — cooling demand starts
    7: 0.95,  # July
    8: 0.95,  # August
    9: 0.90,  # September — low demand
    10: 0.95,  # October — pre-winter
    11: 1.05,  # November — heating season starts
    12: 1.18,  # December — winter peak
}

# Base delivered coal prices ($/MMBtu) by ISO.
# Source: EIA AEO 2024.
COAL_PRICE_BASE: dict[str, float] = {
    "ERCOT": 2.0,  # EIA AEO 2024 — delivered coal price
    "CAISO": 2.5,  # EIA AEO 2024 — delivered coal price
    "PJM": 2.3,  # Central/Northern Appalachian bituminous + PRB-by-rail
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
    "MISO": 1.9,  # MISO's coal fleet burns a Powder River Basin sub-bituminous
    #   (rail-delivered to the upper-Midwest North/Central) + Illinois Basin
    #   bituminous blend, delivered cheaper than Appalachian (PRB minemouth is
    #   low-cost; ILB is local to the footprint). EIA AEO 2024 delivered coal
    #   price, PRB+ILB blend; refined per-plant by the EIA-923 monthly
    #   fuel-cost overlay where reported (MISO has full CEMS/EIA-923 coverage).
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

# NOTE: AGT_DAILY_BASIS_CONVEXITY (the within-month NEISO daily-AGT-basis
# demand-convexity exponent, formerly 7.0) was RETIRED 2026-06. It redistributed
# the measured monthly AGT basis across a month's days proportional to NEISO
# demand raised to the exponent, with the exponent *chosen so the resulting
# gas->oil switching tracked the measured EIA-930 oil burn* — i.e. a within-month
# shape fitted to the electricity/oil outcome, which violates the measured-input
# rule (CLAUDE.md #12: never tune an input to the residual it is validated
# against). It is replaced by a real-data construction in
# market_sim.data.fuel.iso_hub_daily_gas_prices: the within-month AGT basis is
# anchored to the real Algonquin Citygate daily spot prints EIA publishes in its
# Weekly Update narrative (data/raw/gas-prices/algonquin_citygate_daily.csv,
# scripts/fetch_algonquin_daily_spot.py), interpolated on their true calendar
# days and mean-preserved to the measured monthly basis; sparse-print months
# borrow the measured Transco Z6 NY daily-basis shape (AGT~=Transco basis, slope
# ~0.95). Every driver is now free, EIA-sourced, forward-applicable gas-market
# data with no electricity/oil tuning. See docs/multi-iso/neiso-data-audit.md §2c.

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
    "CC_CHP": (0.05, 0.04, 0.002, 20, 0.02, 0.001, 25),
    "CC_REGULAR": (0.05, 0.05, 0.002, 20, 0.02, 0.001, 25),
    "CT_CHP": (0.03, 0.05, 0.002, 20, 0.03, 0.001, 20),
    "CT_PEAKER": (0.03, 0.07, 0.003, 20, 0.05, 0.002, 20),
    "ST_GAS": (0.06, 0.21, 0.003, 30, 0.04, 0.002, 30),
    "ST_CHP": (0.05, 0.08, 0.002, 25, 0.03, 0.0015, 25),
    "COAL": (0.07, 0.12, 0.005, 40, 0.03, 0.002, 35),
    # Oil and biomass entries apply when a unit carries a matching plant-group
    # tag; EIA-classified oil/biomass units (no plant_group) fall back to the
    # flat 1 - EFORD derate. Source: NERC GADS by unit type and age.
    "OIL": (0.06, 0.10, 0.003, 30, 0.04, 0.002, 30),
    "BIOMASS": (0.07, 0.10, 0.002, 25, 0.04, 0.0015, 25),
}

# Forecast-mode monthly planned-maintenance shape (12 weights, Jan..Dec) per
# plant group. Replaces the flat shoulder-POF heuristic (POF smeared uniformly
# across _CC_SHOULDER_MONTHS = {3,4,5,10,11}) with the historically-derived
# *timing* of spring/autumn maintenance learned from the CAMPD unit-outage
# extracts (all six ISOs, 2023-2025 pooled — a forecast shape, NOT pinned to any
# one backcast year). Each weight is the planned-maintenance excess over the
# annual-minimum (forced-outage-floor) month, normalized to a month-length-
# weighted mean of 1 (Sum w[m]*hours[m] = 8760). At apply time
# (data.fleet.generators_to_fleet_arrays, FORECAST mode only) the per-hour
# planned-maintenance derate is B_group * w[group][month], where the group's
# annual POF budget B_group = POF * shoulder_hours / 8760 comes from
# THERMAL_AVAILABILITY. Because w has a month-weighted mean of 1, the annual
# planned-outage budget is conserved EXACTLY (Sum maint[m]*hours[m] =
# POF*shoulder_hours) — only its seasonal distribution is sharpened from the
# rigid 5-month block to the measured curve (peaks Apr/Oct-Nov, ~0 in the
# Jul/Aug summer peak, modest in winter). This is methodology spec section 1.7's
# documented forecast roadmap item and is distinct from the backcast historic
# outage overlay (data/outages.py), which is untouched.
# Derivation/verify: scripts/derive_maintenance_shape.py (reads the committed
# data/raw/campd-unit-outages*.csv). Groups with too few observations (e.g.
# CT_PEAKER — combustion turbines are excluded from the unit-outage detector)
# fall back to the pooled all-thermal shape "_POOLED".
MAINTENANCE_MONTHLY_SHAPE: dict[str, tuple[float, ...]] = {
    "COAL": (
        0.239,
        1.125,
        1.757,
        1.923,
        1.559,
        0.568,
        0.000,
        0.174,
        1.003,
        1.442,
        1.481,
        0.772,
    ),
    "CC_REGULAR": (
        0.608,
        0.961,
        1.765,
        2.175,
        1.591,
        0.473,
        0.000,
        0.007,
        0.449,
        1.524,
        1.554,
        0.910,
    ),
    "CC_CHP": (
        0.574,
        0.851,
        1.658,
        2.217,
        1.775,
        0.516,
        0.000,
        0.072,
        0.505,
        1.736,
        1.481,
        0.623,
    ),
    "CT_PEAKER": (
        0.581,
        1.131,
        1.719,
        1.926,
        1.499,
        0.514,
        0.000,
        0.132,
        0.731,
        1.394,
        1.478,
        0.929,
    ),
    "CT_CHP": (
        1.261,
        1.336,
        1.692,
        2.107,
        1.582,
        0.874,
        0.010,
        0.000,
        0.223,
        0.787,
        1.270,
        0.907,
    ),
    "ST_GAS": (
        1.136,
        1.553,
        1.567,
        1.346,
        1.140,
        0.488,
        0.000,
        0.328,
        0.882,
        0.971,
        1.314,
        1.330,
    ),
    "ST_CHP": (
        0.867,
        0.949,
        1.495,
        1.576,
        1.174,
        0.337,
        0.000,
        0.427,
        0.753,
        1.831,
        1.620,
        0.975,
    ),
    # Pooled all-thermal fallback for sparse/excluded groups (e.g. CT_PEAKER).
    "_POOLED": (
        0.581,
        1.131,
        1.719,
        1.926,
        1.499,
        0.514,
        0.000,
        0.132,
        0.731,
        1.394,
        1.478,
        0.929,
    ),
}

# Carbon price trajectories ($/tCO2) by scenario path and year.
# Source: RFF / state programs.
CARBON_PRICE_PATHS: dict[str, dict[int, float]] = {
    "zero": {2026: 0, 2030: 0, 2040: 0, 2050: 0},  # RFF — no carbon price
    "low": {2026: 0, 2030: 8, 2040: 18, 2050: 25},  # RFF — low carbon price path
    "mid": {2026: 0, 2030: 15, 2040: 35, 2050: 50},  # RFF — mid carbon price path
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
        "capex_per_kw": 1140.0,  # was 1380. ~$285/kWh × 4hr. NREL ATB 2024b, BNEF 2025.
        "capex_per_kwh": 285.0,  # was 345. LFP pack costs ~$100/kWh + BOS.
        "fom_per_kw_yr": 30.0,  # was 34.5.
        "learning_rate": 0.18,
    },
    "li_ion_8hr": {  # NREL ATB 2024 — 8-hour lithium-ion battery
        "duration_hr": 8,
        "rte": 0.86,
        "cycles": 5000,
        "capex_per_kw": 2280.0,  # was 2760. $285/kWh × 8hr.
        "capex_per_kwh": 285.0,  # was 345.
        "fom_per_kw_yr": 48.0,  # was 55.2.
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
        "rte": 0.78,  # lower RTE at longer duration. NREL ATB 2024
        "cycles": 4000,
        "capex_per_kw": 3100.0,  # was 3560. $240/kWh × 12hr + $220/kW.
        "capex_per_kwh": 240.0,  # was 280.
        "fom_per_kw_yr": 10.0,  # was 12.0.
        "learning_rate": 0.15,  # BNEF lithium-ion learning curve 2024
        "lifetime_yr": 20,
    },
    "flow_battery": {  # PNNL 2023 — vanadium redox flow battery
        "duration_hr": 10,
        "rte": 0.70,  # vanadium redox. PNNL 2023 flow battery review
        "cycles": 15000,  # long cycle life — major advantage. PNNL 2023
        "capex_per_kw": 4700.0,  # 350 $/kWh × 10 h + 1200 $/kW. PNNL 2023
        "capex_per_kwh": 350.0,
        "fom_per_kw_yr": 15.0,
        "learning_rate": 0.10,
        "lifetime_yr": 25,
    },
    "compressed_air": {  # NREL ATB 2024 — adiabatic compressed-air storage
        "duration_hr": 8,
        "rte": 0.55,  # adiabatic CAES. NREL ATB 2024
        "cycles": 10000,
        "capex_per_kw": 2700.0,  # 150 $/kWh × 8 h + 1500 $/kW. NREL ATB 2024
        "capex_per_kwh": 150.0,
        "fom_per_kw_yr": 10.0,
        "learning_rate": 0.05,  # mature concept, limited recent deployment
        "lifetime_yr": 40,  # Huntorf plant operating since 1978
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
    "PJM": 75_000.0,  # ~50% of ~150 GW peak. Source: PJM Load Forecast Report 2024
    "NYISO": 16_000.0,  # ~50% of ~32 GW peak. Source: NYISO Gold Book 2024
    "NEISO": 13_000.0,  # ~50% of ~26 GW peak. Source: ISO-NE CELT Report 2024
}

# Max new storage power per year (MW). Source: ERCOT CDR, CAISO TPP queue data,
# eastern-ISO interconnection-queue throughput.
STORAGE_ANNUAL_BUILD_CAP_MW: dict[str, float] = {
    "ERCOT": 5_000.0,
    "CAISO": 3_000.0,
    "PJM": 4_000.0,  # large queue but slower interconnection. Source: PJM queue 2024
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
    # MISO runs a SEASONAL Planning Resource Auction (PRA): 4 seasons, clearing
    # in $/MW-day with a sloped demand curve anchored on Net-CONE. We anchor on
    # MISO's published Net-CONE (the demand-curve reference), NOT the volatile
    # PRA clearing price (PY24/25 annualized ~$21/MW-day vs PY25/26 ~$217/MW-day
    # — the summer-only spike to $666.50/MW-day), consistent with how PJM/NYISO/
    # NEISO anchor on net-CONE rather than a single auction print.
    #   Reference resource: advanced combustion turbine. Gross CONE PY2024/25
    #   ~$330/MW-day (= 330 x 365 / 1000 = $120.45/kW-yr). MISO's published
    #   average Net-CONE for the North/Central region is ~$79,800/MW-yr
    #   (= $79.8/kW-yr; equivalently $79,800/365 = $218.6/MW-day net-CONE
    #   reference), i.e. gross CONE less the ~$40/kW-yr inframarginal E&AS
    #   offset. We use 80.0 $/kW-yr.
    #   PRA -> $/kW-yr conversion: $/MW-day x 365 / 1000 = $/kW-yr.
    # Net-CONE varies by LRZ (PY25/26 gross CONE $321/MW-day LRZ10 to
    # $373/MW-day LRZ5) and by season; the single North/Central anchor is a
    # representative value pending the M8 seasonal/zonal RA-timing build.
    # Source: MISO CONE & Net-CONE Update (RASC, 2024-09-23) and MISO PRA
    # results postings (PY2024/25, PY2025/26). See parameter-citations.md.
    "MISO": MarketDesign(capacity_market=True, net_cone_per_kw_yr=80.0),
}

DEFAULT_MARKET_DESIGN: MarketDesign = MarketDesign(capacity_market=False)

# Target planning reserve margin per ISO for the reserve-margin adequacy
# backstop (capacity.py::apply_reserve_margin_build). Each ISO sets its own
# installed-reserve-margin / planning-reserve-margin target through its
# resource-adequacy process; ERCOT's 13.75% is its economically-optimal RM and
# is NOT every ISO's target. The reserve-margin build resolves
# ``PLANNING_RESERVE_MARGIN_BY_ISO.get(iso, config.planning_reserve_margin)``,
# so an explicit ScenarioConfig.planning_reserve_margin still overrides this
# registry and an ISO absent here falls back to that scalar. Values are on the
# same nameplate/ICAP basis the backstop uses (firm gap over peak).
PLANNING_RESERVE_MARGIN_BY_ISO: dict[str, float] = {
    # Economically-optimal RM for ERCOT's energy-only market. Source: Brattle
    # & Astrapé, "Estimating the Economically Optimal Reserve Margin in ERCOT"
    # (2022 update for the PUCT). This is the parity value (fallback default).
    "ERCOT": 0.1375,
    # CPUC Resource Adequacy program planning reserve margin (15%). Source:
    # CPUC RA proceeding (R.21-10-002 / Decision adopting 15% PRM).
    "CAISO": 0.15,
    # PJM Installed Reserve Margin, raised to ~17.8% for the 2025/2026 delivery
    # year. Source: PJM 2024 IRM/FPR study (PC, 2024-03-20), IRM ~17.8%.
    "PJM": 0.178,
    # MISO ICAP Planning Reserve Margin Requirement (PRMR). Source: MISO
    # Planning Year 2024-25 LOLE Study Report (ICAP PRM ~17.9%).
    "MISO": 0.179,
    # SPP planning reserve margin, increased from 12% to 15% effective the 2023
    # summer season. Source: SPP Planning Criteria Rev 4.1A (2023), §PRM.
    "SPP": 0.15,
    # NYCA Installed Reserve Margin set by NYSRC. Source: NYSRC 2025-2026 IRM
    # Final Base Case (24.4%); NYISO's IRM is structurally high (locality +
    # transmission-security constraints).
    "NYISO": 0.244,
    # ISO-NE: FCM sizes capacity to Net ICR rather than publishing a single RM,
    # so this uses the NERC reference margin level for ISO-NE (~15.7%) as a
    # stand-in until the ICR-implied margin is wired in. Source: NERC 2023 LTRA
    # reference margin levels. needs-citation (firm ISO-NE RM filing).
    "NEISO": 0.157,
}

# ERCOT ancillary-service market revenue ($/kW-yr) credited in the capacity
# economics when ScenarioConfig.as_revenue_enabled (ERCOT energy-only; the
# capacity-market ISOs recover fixed cost through capacity_revenue_per_mw_yr).
# This is an exogenous, calibrated revenue stream — the AS analogue of the
# scarcity overlay — NOT an AS co-optimization (out of scope). Base rates are
# the 2023 calibration point (IMM 2023 SOM / Modo Energy): batteries earned
# ~$169/kW-yr from AS in 2023 (~85% of their ~$196/kW total), the AS-eligible
# fleet then ~4 GW. Thermal AS is a smaller per-kW slice (peakers/steam carry
# more Reg/RRS/Non-Spin per MW than baseload CC). Source: Potomac Economics
# 2023/2024 ERCOT State of the Market; Modo Energy ERCOT BESS revenue index.
ERCOT_AS_REVENUE_PER_KW_YR: dict[str, float] = {
    "storage": 169.0,
    "gas_ct": 22.0,
    "gas_st": 15.0,
    "gas_cc": 8.0,
}

# Capacity credit (ELCC) of variable resources for the planning-reserve-margin
# adequacy accounting — the firm fraction of nameplate each contributes to the
# system peak. Thermal is accredited at 1 - EFORd (UCAP); storage uses
# STORAGE_ELCC_BY_DURATION; these are the wind/solar/hydro values. ERCOT-class
# summer-peak ELCC: solar contributes more than wind at the late-afternoon net
# peak, both far below nameplate. Source: ERCOT CDR / ELCC studies, NREL/E3.
RENEWABLE_CAPACITY_CREDIT: dict[str, float] = {
    "wind": 0.16,
    "solar": 0.18,
    "offshore_wind": 0.30,
    "hydro": 0.50,
}

# AS is a small, quickly-saturated market: per-kW AS revenue falls steeply as
# the AS-eligible (mostly storage) fleet grows past the calibration point.
# Modeled as revenue_per_kw = base * (ref_gw / max(storage_gw, ref_gw)) **
# exponent. Calibrated so the observed crash is reproduced: storage AS ~$169/kW
# at ~4 GW (2023) -> ~$40/kW at ~6.5 GW (2024) -> ~$15-20/kW at ~10 GW (2025);
# Modo reports AS revenue down ~90% 2023->2025. The same saturation applies to
# thermal AS (batteries displaced thermal from Reg/RRS/ECRS).
ERCOT_AS_SATURATION_REF_GW: float = 4.0
ERCOT_AS_SATURATION_EXPONENT: float = 2.5

# ISOs that have a per-plant CAMPD bin artifact and therefore take the
# offer-curve (per-plant tranche) binning path in the runner instead of the
# legacy equal-width ``aggregate_fleet`` heat-rate binning. ERCOT is driven by
# the curated ``data/raw/reference/custom-bin-assignments.csv``; CAISO/NEISO/NYISO/PJM/MISO
# are covered by the CAMPD-derived ``data/raw/_processed-legacy/thermal_tranches_<ISO>.csv``
# (and the committed ``data/raw/_processed-legacy/bin_assignments_<ISO>.csv`` review
# artifacts). The ISO WITHOUT a bin artifact (SPP) is intentionally absent
# and falls back to ``aggregate_fleet`` exactly as before. The runner gate keys
# off this set so the per-plant path unlocks per ISO as its artifact lands.
CAMPD_BINNING_ISOS: frozenset[str] = frozenset(
    {"ERCOT", "CAISO", "NEISO", "NYISO", "PJM", "MISO"}
)

# Effective default for the historic (facility-summed) CAMPD outage overlay,
# per ISO. The overlay hard-zeros coal/CC tranches when a plant's CEMS facility
# sum drops out. It is the PRIMARY outage layer only where the unit-level
# derate merely SUPPLEMENTS it, and is redundant (double-counting) where the
# unit-level file is the COMPLETE CAMPD-derived source. The runner resolves the
# effective flag as ``HISTORIC_OUTAGE_OVERLAY_BY_ISO.get(iso, <config flag>)``,
# so an ISO absent from this map keeps the global ``ScenarioConfig`` default.
# Reasoning per ISO:
#   ERCOT  True  — facility-summed legacy extract is the primary layer; the
#                  unit-level derate only catches single-unit losses it hides.
#   CAISO  False — unit-level file derived fresh from ALL CAMPD units (complete).
#   NEISO  False — same: complete CAMPD-derived unit-level source.
#   NYISO  False — same: complete CAMPD-derived unit-level source.
#   PJM    False — unit-level file built fresh by derive_campd_unit_outages.py
#                  is the complete source; stacking the facility overlay on top
#                  double-counts and over-derates (see scenarios.py).
HISTORIC_OUTAGE_OVERLAY_BY_ISO: dict[str, bool] = {
    "ERCOT": True,
    "CAISO": False,
    "NEISO": False,
    "NYISO": False,
    "PJM": False,
}

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
    "CAISO": 8,  # CAISO TPP — annual queue throughput cap
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
        "wind": 5.0,
        "solar": 5.0,
        "gas_cc": 3.0,
        "gas_ct": 3.0,
        "nuclear": 2.0,
        "geothermal": 2.0,  # engineering judgment, EGS resource potential
        "offshore_wind": 0.0,  # Gulf coast not yet leased. Source: BOEM
    },
    "CAISO": {
        "wind": 3.0,
        "solar": 4.0,
        "gas_cc": 2.0,
        "gas_ct": 1.0,
        "nuclear": 1.0,
        "geothermal": 3.0,  # CA geothermal resource assessment
        "offshore_wind": 3.0,  # BOEM Pacific lease areas, CAISO TPP
    },
    # Eastern-ISO per-tech caps: Tier 3, sized from each ISO's recent build
    # mix (LBNL "Queued Up" 2024; ISO planning reports). needs-citation.
    "PJM": {
        "wind": 1.5,
        "solar": 6.0,
        "gas_cc": 4.0,
        "gas_ct": 2.0,
        "nuclear": 1.0,
        "geothermal": 0.0,  # no utility-scale resource in footprint
        "offshore_wind": 2.0,  # NJ/MD/DE BOEM lease areas
    },
    "MISO": {
        "wind": 4.0,
        "solar": 6.0,
        "gas_cc": 3.0,
        "gas_ct": 2.0,
        "nuclear": 1.0,
        "geothermal": 0.0,
        "offshore_wind": 0.0,  # Great Lakes not leased
    },
    "SPP": {
        "wind": 4.0,
        "solar": 3.0,
        "gas_cc": 2.0,
        "gas_ct": 1.0,
        "nuclear": 0.5,
        "geothermal": 0.0,
        "offshore_wind": 0.0,
    },
    "NYISO": {
        "wind": 1.0,
        "solar": 2.0,
        "gas_cc": 1.0,
        "gas_ct": 0.5,
        "nuclear": 0.5,
        "geothermal": 0.0,
        "offshore_wind": 1.5,  # NY Bight BOEM lease areas
    },
    "NEISO": {
        "wind": 1.0,
        "solar": 2.0,
        "gas_cc": 1.0,
        "gas_ct": 0.5,
        "nuclear": 0.5,
        "geothermal": 0.0,
        "offshore_wind": 2.0,  # MA/RI BOEM lease areas
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
    "gas_ct": {  # NREL ATB 2024 frame combustion turbine / peaker. Annualized
        # fixed cost (capex annuity + FOM) ~ the Brattle ERCOT CONE-for-2026
        # frame-CT reference (~$162/kW-yr gross). base_cf is a nominal peaker
        # duty cycle; the new-entry screen prices a gas_ct on its price-duration
        # energy margin, not base_cf x mean price.
        "capex_per_kw": 1250.0,
        "fom_per_kw_yr": 21.0,
        "learning_rate": 0.02,
        "base_cf": 0.12,
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
        "capex_per_kw": 2300.0,  # $/kW total plant cost (host CCGT + capture island).
        # Source: NETL Cost & Performance Baseline Rev 4, 2021.
        # Reflects 90% capture, amine-based post-combustion.
        "fom_per_kw_yr": 45.0,  # $/kW-yr. Source: NETL Rev 4.
        "learning_rate": 0.10,  # 10% cost reduction per doubling of cumulative deployment.
        # Source: Rubin et al. (2015) "The cost of CO2 capture
        # and storage", Int J Greenhouse Gas Control.
        # Range in literature: 0.08–0.12 for first-of-a-kind
        # industrial process technologies.
        # CCS is early on its deployment curve (~2 GW base),
        # so each doubling comes quickly and has large effect.
        "base_cf": 0.80,  # Lower than unabated CC (0.85) due to higher MC
        # pushing it later in merit order at low carbon prices.
        "lifetime_yr": 30,  # Same as gas CC host plant.
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
        "heat_rate": 9.5,  # MMBtu/MWh. GE HA specs, DOE H2 Turbine Program 2023
        "vom": 4.0,  # $/MWh. NREL ATB 2024 (gas CT analog + H2 premium)
        "emission_rate_co2": 0.0,  # tCO2/MWh — zero direct CO2 (green H2)
        "nox_rate": 0.00015,  # tons NOx/MWh — H2 burns hot. DOE/NETL 2023
        "eford": 0.06,  # above gas CT — immature fleet. Engineering judgment
        "capex_kw": 1400.0,  # $/kW. NREL ATB 2024, BloombergNEF H2 Outlook 2024
        "fom_kw_yr": 12.0,  # $/kW-yr. NREL ATB 2024
        "lifetime_yr": 30,
        "learning_rate": 0.10,  # analogy to gas CT maturation
    },
    "h2_ccgt": {  # combined-cycle H2 turbine (mid-merit/baseload)
        "heat_rate": 6.9,  # MMBtu/MWh. DOE H2 Turbine Program 2023
        "vom": 3.5,  # $/MWh. NREL ATB 2024
        "emission_rate_co2": 0.0,
        "nox_rate": 0.00012,  # DOE/NETL 2023
        "eford": 0.06,
        "capex_kw": 1800.0,  # $/kW — premium over gas CCGT. NREL ATB 2024
        "fom_kw_yr": 15.0,  # $/kW-yr. NREL ATB 2024
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

# Carbon capture, utilization and storage parameters. CCUS is a variant of
# the base gas CC plant: higher heat rate (parasitic capture load), higher
# VOM (solvent costs), reduced emission rate, plus a transport+storage cost
# for the captured CO2.
CCUS_PARAMS: dict[str, dict[str, float]] = {
    "gas_cc_ccs_90": {  # gas CCGT with 90% post-combustion capture
        "heat_rate_penalty": 1.16,  # ×base CC heat rate — 16% parasitic. NETL 2022 Rev 4, Case B31B
        "vom_adder": 8.0,  # $/MWh — amine solvent, maintenance. NETL 2022
        "capture_rate": 0.90,  # fraction of CO2 captured. NETL 2022 Case B31B
        "co2_transport_storage": 15.0,  # $/tCO2 — pipeline + saline injection. NETL 2022, Gulf Coast
        "capex_kw": 2500.0,  # $/kW installed. NREL ATB 2024
        "fom_kw_yr": 22.0,  # $/kW-yr. NREL ATB 2024
        "lifetime_yr": 30,
        "learning_rate": 0.05,  # slow — limited deployment. Global CCS Institute 2024
    },
}

# Enhanced geothermal (EGS) parameters. EGS enters as a thermal generator
# with zero fuel cost and high capacity factor, dispatchable down to
# ``pmin_fraction`` of rated capacity (flexible baseload). Not intermittent.
GEOTHERMAL_PARAMS: dict[str, dict[str, float]] = {
    "egs": {
        "capacity_factor": 0.90,  # high availability. DOE GeoVision 2019
        "vom": 1.0,  # $/MWh — minimal, no fuel. NREL ATB 2024
        "emission_rate_co2": 0.0,  # zero direct emissions
        "nox_rate": 0.0,
        "eford": 0.05,  # comparable to nuclear. DOE GeoVision 2019
        "pmin_fraction": 0.20,  # turn down to 20% for flexibility. Fervo 2024
        "capex_kw": 5000.0,  # $/kW — high upfront, early-stage. NREL ATB 2024
        "fom_kw_yr": 0.0,  # $/kW-yr — captured in VOM. NREL ATB 2024
        "lifetime_yr": 30,
        "learning_rate": 0.15,  # steep — analogous to early solar. Fervo, ARPA-E
        "heat_rate": 0.0,  # no fuel
    },
}

# Offshore wind parameters. A separate renewable category from onshore wind:
# higher and less variable capacity factors, higher costs, distinct zones.
OFFSHORE_WIND_PARAMS: dict[str, dict[str, float]] = {
    "fixed_bottom": {
        "base_cf": 0.45,  # annual average. NREL ATB 2024
        "capex_kw": 4200.0,  # $/kW. NREL ATB 2024
        "fom_kw_yr": 80.0,  # $/kW-yr — marine access premium. NREL ATB 2024
        "lifetime_yr": 30,
        "learning_rate": 0.08,  # NREL ATB 2024, IRENA 2024
    },
    "floating": {
        "base_cf": 0.48,  # deeper water, better resource. NREL ATB 2024
        "capex_kw": 5500.0,  # $/kW — early stage. NREL ATB 2024
        "fom_kw_yr": 95.0,
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
    "SPP": {"wind": 0.41, "solar": 0.24},
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
    # CAISO WECC import supply merit order. Tier 3 (calibration) — block
    # CAPACITIES tile the EIA-930 CISO net-interchange duration curve (held
    # fixed); block PRICES re-fitted in BUNDLE mode against the SOLVED CAISO
    # price duration curve (P9/P12 structural re-price, docs/calibration-log.md
    # "CAISO 4 — import re-price"). CAISO is a heavy, growing net importer:
    # −28.9 / −32.4 / −36.2 TWh, imports in 86% / 89% / 91% of hours across
    # 2023-25 (~20-25% of energy) — the biggest supply block after gas. Median
    # import ~4.2 GW, deepest hour ~11.0 GW; aggregate 11.4 GW sits between that
    # and the ~12-15 GW WECC simultaneous-import rating (COI/Path 66 ~4.8 GW +
    # PDCI ~3.1 GW + Path 46 West-of-River + Path 45).
    #
    # WHY THESE PRICES (the re-price lesson): the prior placeholder priced every
    # block BELOW the modeled gas merit order, so the 11.4 GW stack cleared
    # ~continuously and net imports scored 214/152/146% of actual with gas at
    # −41/−19/+13% vs EIA-923. The cheap blocks are INFRAMARGINAL baseload —
    # re-pricing them below gas moves neither price nor quantity (gas sets the
    # marginal price above them). The over-import was the TOP blocks
    # (DSW_CCGT/CT/scarcity) sitting below gas; the fix prices them ABOVE the
    # in-state gas merit order, so desert-SW gas imports cost ≈ CA gas + wheeling
    # (their physical delivered cost) and back off to gas. Converged keeper
    # (caiso_reprice_pass4): net imports 134/83/92% of actual (down from
    # 214/152/146), gas −11/+13/+48% (2023 recovered from −41%). Prices are
    # pre-carbon delivered-WECC costs (energy + wheeling), cheapest first and
    # all above every export sink (no import↔export arbitrage); the CARB
    # border-carbon adder (~+$12-15/MWh, EF 0.428 × allowance) is layered on at
    # build time (build_import_generators) — now applied in the calibration
    # path too (run_calibration.run_year, previously dropped). Block proxies:
    #   - PNW_hydro_base: COI firm Pacific-NW hydro economy energy; the
    #     always-on baseload, just below gas-CC. eff ≈ $40-43 w/ carbon.
    #   - PNW_midC: Mid-Columbia hydro/wind shoulder over COI/PDCI.
    #   - DSW_solar_PV: desert-SW solar + Palo Verde nuclear midday, Path 46.
    #   - DSW_CCGT / DSW_CT: desert-SW gas combined-cycle / combustion turbine
    #     (Mead / Four Corners) — priced at CA-gas-equivalent + wheeling, i.e.
    #     ABOVE in-state gas, so they peak rather than baseload.
    #   - WECC_scarcity: west-wide peak economy energy in CAISO heat events;
    #     clears only in 2023's price tail (~2 TWh), ~0 in 2024/25.
    # LIMITATION (static-node, documented like PJM/NYISO): a single price vector
    # cannot hit all three years within ±15% — 2023 has a fat price tail (p90
    # $119; wet-hydro + lowest-storage year) while 2024/25 are compressed (p90
    # $75/$80), an import-% offset of ~50-60 pts invariant to the price level.
    # The keeper minimizes total error (2024/25 within ±15%, 2023 the +34%
    # outlier). A year-keyed (availability/season) import lever is the structural
    # next step. Note: the modeled CAISO price level runs high vs actual_lmp
    # (model ~$60 vs CAISO 2024 RT ~$33) — a pre-existing P10/price-level item
    # (baseline was already ~$53), since real imports are cheap-but-transmission-
    # limited and a fixed-capacity priced node trades price-suppression for
    # quantity-correctness. import-hour share / negative-price hours / midday
    # export sign-flip stay P6-owned (delivered-not-potential solar feed).
    # Source: EIA-930 CISO net-interchange 2023-2025; CAISO OASIS path ratings;
    # solved bundle results/calibration/caiso_reprice_pass4.
    "CAISO": [
        ("PNW_hydro_base", 800.0, 28.0),  # COI firm PNW hydro — baseload
        ("PNW_midC", 1800.0, 36.0),  # Mid-C hydro/wind shoulder
        ("DSW_solar_PV", 1800.0, 48.0),  # Desert SW solar + Palo Verde
        ("DSW_CCGT", 1800.0, 68.0),  # Desert SW combined-cycle gas
        ("DSW_CT", 2200.0, 110.0),  # Desert SW combustion turbine
        ("WECC_scarcity", 3000.0, 180.0),  # Peak west-wide scarcity energy
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
    # NOTE: the NYISO block above is the 2023 / default ladder. Its neighbor-hub
    # prices are pinned to 2023 hub levels, so in higher-gas years the static
    # ladder sits stale-cheap and the model over-imports on a flat ~max schedule
    # (2025: model −34.7 vs actual −19.1 TWh, diurnal corr −0.80). The real
    # neighbors (PJM West, ISO-NE) are themselves gas-priced and rise with the
    # year, so the willingness-to-sell into NY rises too. IMPORT_TRANCHES_BY_YEAR
    # below carries the year-grounded NYISO ladder; see its comment for the
    # measured neighbor-hub ratios. (This generalizes the PJM static-node
    # year-compromise noted in EXPORT_TRANCHES["PJM"] — NYISO's neighbor spread
    # is too wide for a single static compromise to span.)
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
# Year-grounded import ladders. An (iso, year) entry overrides IMPORT_TRANCHES
# for that backcast year; ISO-years absent here fall back to the static ladder
# (so forecast years and un-tabulated ISOs are unchanged). Used by
# transmission.build_import_generators(iso, year=...).
#
# NYISO (Step 4, "import discipline") — the priced node's blocks proxy
# gas-priced neighbor hubs, so the ladder is DERIVED from the measured
# neighbor-hub RT LMP each year (data/raw/_validation-source/actual_lmp.json,
# rt / rt_pct) instead of being hand-set or ratio-scaled, anchored on each
# tie's ROLE in the merit order:
#   marginal gas ties = neighbor hub p75[y] + 1.5 — PJM_west (clears ~50% of
#     hours) and ISONE_tie (~20%) clear only in NYISO's upper-price hours, so
#     the neighbor price *given NYISO imports through that seam* is the
#     neighbor's upper quartile (anchoring on the annual mean over-cheapens the
#     deep imports and pulls the high-gas year below actual). p75:
#       PJM Western Hub  32.7 / 33.9 / 47.9  -> PJM_west
#       ISO-NE Mass Hub  38.4 / 43.4 / 81.1  -> ISONE_tie
#   baseload ties = home base + 1.5 + linkage*Δ(PJM mean) — HQ (~zero-SRMC
#     hydro, 100% of hours) and Ontario (surplus nuclear/hydro, ~70-97%) are
#     always-on and gas-insensitive; they anchor on their own home price (HQ
#     economy energy ~$11.5; Ontario HOEP 2023 ~US$21) and rise only with
#     export opportunity cost (HQ 0.5x, Ontario 1.0x the PJM annual increment).
#   import_scarcity = mean(PJM p95, Mass Hub p95)[y] — the neighbors' peak
#     economy energy in NYISO's tightest hours, which falls in the low-gas
#     year instead of sitting stale-expensive at the old hand-set $75.
# The 1.5 adder is NYISO import marginal losses + the seam transaction margin.
# Capacities are unchanged — the duration-curve fit (derive_import_tranches.py)
# is capacity-keyed; only the price ladder tracks the year. Regenerate with
# scripts/derive_nyiso_import_ladder.py. Tier 3 (calibration).
IMPORT_TRANCHES_BY_YEAR: dict[str, dict[int, list[tuple[str, float, float]]]] = {
    "NYISO": {
        2023: [
            ("HQ_hydro", 900.0, 13.0),
            ("IESO_Ontario", 1200.0, 22.5),
            ("PJM_west", 1100.0, 34.2),
            ("ISONE_tie", 800.0, 39.9),
            ("import_scarcity", 1900.0, 68.4),
        ],
        2024: [
            ("HQ_hydro", 900.0, 13.5),
            ("IESO_Ontario", 1200.0, 23.6),
            ("PJM_west", 1100.0, 35.4),
            ("ISONE_tie", 800.0, 44.9),
            ("import_scarcity", 1900.0, 79.7),
        ],
        2025: [
            ("HQ_hydro", 900.0, 20.2),
            ("IESO_Ontario", 1200.0, 37.0),
            ("PJM_west", 1100.0, 49.4),
            ("ISONE_tie", 800.0, 82.6),
            ("import_scarcity", 1900.0, 135.2),
        ],
    },
}


# NYISO local self-supply floors (transmission.inject_nyiso_local_selfsupply,
# gated on ScenarioConfig.nyiso_local_selfsupply). Per downstate load-pocket
# zone, the fraction of that zone's hourly load that must be met by IN-ZONE
# dispatchable thermal generation. Long Island (zone K) is cable-islanded and
# carries NYISO locational-minimum-installed-capacity (LMIC) / local-reliability
# rules that keep its own gas-steam + peaker fleet running rather than importing
# the full cable rating of cheap NYC gas. The economic LP under-runs the LI
# fleet (model 3.7 vs EIA-923 8.52 TWh, 2023). The fraction is anchored on the
# 2023 realized LI self-supply share (8.52 TWh gen / ~17.6 TWh load = 0.48),
# which is what the LMIC requirement enforces — a load-scaling, forward-
# reproducible rule, NOT a pin to measured generation (CLAUDE.md rule #12). Set
# a touch below the realized share so the floor never over-forces. NYC (zone J)
# is deliberately ABSENT: the diagnostic shows NYC OVER-generates by +11 TWh
# (it cannot import enough, so it self-supplies) — its idle peakers are a
# reserve-scarcity gap (RCPF / mechanism B), not an energy must-run. Tier 3.
# Source: NYISO Locational Installed Capacity Requirements (Gold Book); EIA-923
# zone-mapped net generation; docs/nyiso-dispatch-validation-2026-06.md.
NYISO_LOCAL_SELFSUPPLY_FRAC: dict[str, float] = {
    "Long_Island": 0.45,
}

# NYISO firm (must-flow) import baseload (transmission.inject_nyiso_firm_imports,
# gated on ScenarioConfig.nyiso_firm_imports). Per priced-node import tranche,
# the fraction of its capacity that flows as FIRM, price-insensitive baseload
# (the long-term Hydro-Québec / Ontario schedules that flow regardless of NY's
# hourly price), set as an hourly min_gen floor on that import row. HQ is firm
# economy hydro that already clears ~100% of 2023 hours, so flooring it is
# structurally faithful and never binds tighter than reality; Ontario is left
# economic (0.0) so the firm floor stays below the measured lightest-import hour
# (NY imported >=922 MW in 98% of 2023 hours) and cannot force a phantom
# over-import. The lever's real value is cheap-overnight hours and lower-price
# years (2024) where the economic node would otherwise back the baseload off.
# FORWARD-REPRODUCIBLE (a firm schedule reproduces for any year); Tier 3.
NYISO_FIRM_IMPORT_FLOOR_FRAC: dict[str, float] = {
    "HQ_hydro": 1.0,
    "IESO_Ontario": 0.0,
}

# NYISO priced import-node monthly net-throughput band half-width (fraction of
# the measured monthly net import), used by the boundary-flow calibration
# constraint (transmission.build_import_node_reconciliation /
# dispatch._build_import_node_rows, gated on
# ScenarioConfig.nyiso_import_reconciliation). The constraint pins the priced
# node's monthly NET interchange to the measured EIA-930 schedule
# (eia_loader.nyiso_net_interchange) — replacing the static economic tranche
# ladder's near-flat clearing (which deviates +-1-5 TWh/yr from the metered
# schedule and does NOT track its 23.45->20.35->19.09 TWh year-over-year decline)
# with the authoritative measurement (CLAUDE.md rule #11). The band is NOT a fit
# to a residual-minimizing volume: the TARGET is the measured schedule itself;
# the half-width only leaves the priced tranches room to set the marginal price
# *within* each month's envelope (the LP still chooses which hours/tranches clear
# to set the hourly LMP) and gives feasibility headroom against the firm-import
# floor / hourly link TTCs. 0.02 (+-2%) keeps the annual total within a basis-
# width of measured while preserving hourly price formation; tighten toward 0
# (a hard monthly pin) only if a year drifts. FORWARD-REPRODUCIBLE: in a forecast
# the same constraint is sourced from the neighbor's forecast net position (or
# relaxed to the bare priced node), so the dispatch validated here is the
# dispatch forecast. Tier 3 (measured schedule, EIA-930).
NYISO_IMPORT_RECON_BAND_FRAC: float = 0.02

# Manitoba Hydro firm-hydro import into MISO-North (transmission.
# build_miso_firm_imports / inject_miso_firm_imports, gated on
# ScenarioConfig.miso_firm_imports). Manitoba Hydro is MISO's single largest
# import source and the structural reason MISO is a net IMPORTER: it sells
# ~10-15 TWh/yr of FIRM contracted hydro into MISO-North (Minnesota) over the
# Manitoba<->US HVDC / 500 kV ties (the Nelson River bipoles deliver to Dorsey,
# then the international border; the Great Northern Transmission Line, in service
# 2020, backs the Manitoba Hydro <-> Minnesota Power firm contract). This import
# sits OUTSIDE the gas-margin reference-price seam (INTERFACE_NEIGHBORS["MISO"],
# PJM/SPP/SERC): firm hydro has no gas x heat-rate price analogue, so it is a
# SEPARATE block priced as firm hydro -- a low, near-constant energy offer
# reflecting the contract -- landing directly in MISO-North (the model zone the
# ties physically enter; counted as net interchange via its fuel_type="import").
# Volume is sourced from the Manitoba Hydro export-contract band (~10-15 TWh/yr),
# NOT fitted to the EIA-930 net-interchange residual (claude.md rule #12): a firm
# contract reproduces for any forward year and responds to a changed contract.
#   - MW 1,400: the contracted firm baseload, ~12.3 TWh/yr at constant flow --
#     the midpoint of Manitoba Hydro's 10-15 TWh/yr US export band. (Manitoba
#     Hydro generates ~30-37 TWh/yr of hydro and exports a large share south.)
#   - offer $8/MWh: firm hydro contract energy -- well below MISO's gas-set LMP
#     (Indiana-Hub RT ~$31-43, so the block clears INFRAMARGINALLY and displaces
#     marginal gas), above the $0 dump floor (so it never games negative-MC
#     credits). Tier 3 estimate; the block is firm-floored, so the offer is
#     inframarginal and does NOT set price -- it only places the block correctly
#     in the merit order.
#   - floor frac 1.0: the contract is firm must-flow, so the full block flows
#     every hour regardless of MISO's hourly price (the Hydro-Quebec firm-import
#     pattern, NYISO_FIRM_IMPORT_FLOOR_FRAC) -- near-constant by design.
MISO_MANITOBA_FIRM_IMPORT_MW: float = 1400.0
MISO_MANITOBA_FIRM_IMPORT_OFFER: float = 8.0
MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC: float = 1.0
MISO_MANITOBA_FIRM_IMPORT_ZONE: str = "MISO-North"
MISO_MANITOBA_FIRM_IMPORT_NAME: str = "Manitoba_firmhydro"

# Per-year MEASURED Manitoba firm-hydro delivery into MISO (BACKCAST ONLY).
# The flat MISO_MANITOBA_FIRM_IMPORT_MW above is the forecast-native contract
# MIDPOINT (~12.3 TWh/yr, the middle of Manitoba Hydro's 10-15 TWh/yr US export
# band) and is the correct forward default — but for a backcast year the firm
# delivery is a known PHYSICAL quantity that swings with Manitoba's hydro
# conditions, so it is overlaid here from the measured directed-flow series,
# exactly as the nuclear refuel derate (NUCLEAR_MONTHLY_CF_BY_YEAR) and the seam
# deliverability envelope (MISO_SEAM_DIBA) overlay their measured-availability
# inputs. Manitoba ran a multi-year DROUGHT through 2024-2025 (low Nelson/Winnipeg
# River runoff), collapsing its firm southbound exports — Manitoba Hydro reported
# sharply reduced US exports and even net imports in FY2024/25. The flat 1400 MW
# block therefore over-injects ~6-10 TWh/yr of phantom cheap must-flow energy into
# MISO-North, depressing MISO's own LMP so it under-imports from PJM, under-exports
# South, and backfills domestic coal/gas/CT under-gen (miso12 import composition).
#
# Values are the GROSS directed firm import (hours MISO imports from the MHEB BA),
# annualized to a flat MW at 8760 h, from data/raw/eia-930-interchange/
# "MISO interchange hourly.parquet" (the same EIA-930 BA-to-BA INTERCHANGE product
# the seam envelope uses; EIA sign + = MISO exports to MHEB, so import = -mw, the
# negative-flow hours summed). The gross firm DELIVERY (not the net MHEB
# interchange) is the right physical analogue: the contract still delivers ~2 TWh
# even in drought-2025, while MISO's occasional surplus sell-back to Manitoba is a
# separate (un-modeled, seam-excluded) transaction, not a reason to net the firm
# block negative. This is NOT a fit to MISO's net-interchange residual (rules
# #11/#12): it is the directed firm-delivery quantity computed BEFORE any LP runs,
# regenerable for a forward year from Manitoba's hydro outlook + contract, and
# flow-responsive (the 2025 drought collapse is the input changing, not a tune).
# Reproduce / re-check with scripts/derive_manitoba_firm_import.py.
#   2023: 6.36 TWh -> 726 MW | 2024: 4.65 TWh -> 531 MW | 2025: 1.96 TWh -> 224 MW
MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR: dict[int, float] = {
    2023: 726.0,
    2024: 531.0,
    2025: 224.0,
}


def resolve_miso_manitoba_firm_import_mw(year: int | None, mode: str) -> float:
    """Return the Manitoba firm-import block capacity (MW) for ``year``/``mode``.

    In ``mode == "backcast"`` with ``year`` in
    :data:`MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR`, return the measured per-year
    firm-hydro delivery (drought-responsive); otherwise return the flat
    forecast-native contract midpoint :data:`MISO_MANITOBA_FIRM_IMPORT_MW`. A
    forecast year (or a backcast year with no measured overlay) is therefore
    byte-identical to the prior flat-block behaviour.
    """
    if mode == "backcast" and year in MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR:
        return MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR[year]
    return MISO_MANITOBA_FIRM_IMPORT_MW


# ISOs whose backcasts enable the Manitoba firm-hydro import block BY DEFAULT
# (resolve_miso_firm_imports), no --miso-firm-imports flag required. The firm
# Manitoba contract is the structural reason MISO is a net IMPORTER and sits
# outside the gas-margin seam, so it is the correct default for the MISO
# backcast (decided after the miso5_firmhydro solve confirmed it moves net
# interchange toward EIA-930 actual while leaving the LMP/fuel mix faithful).
# Every other ISO is byte-identical (the block is MISO-only regardless).
MISO_FIRM_IMPORT_DEFAULT_ISOS: frozenset[str] = frozenset({"MISO"})


def resolve_miso_firm_imports(flag: bool | None, iso: str) -> bool:
    """Resolve the ``--miso-firm-imports`` tri-state flag for ``iso``.

    ``flag`` is ``True``/``False`` when set explicitly on the CLI
    (``--miso-firm-imports`` / ``--no-miso-firm-imports``), or ``None`` to fall
    back to the per-ISO default in :data:`MISO_FIRM_IMPORT_DEFAULT_ISOS`. The
    block itself is MISO-only downstream (``build_miso_firm_imports`` returns
    nothing otherwise), so a non-MISO ISO stays byte-identical either way.
    """
    if flag is not None:
        return flag
    return iso in MISO_FIRM_IMPORT_DEFAULT_ISOS


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
        ("export_solar", 2500.0, 8.0),  # midday surplus sold to WECC
        ("export_curtail", 4000.0, 0.0),  # deep oversupply curtailment floor
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
    # data/raw/iso-specific-transmission/
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


# ISOs whose backcasts serve the seam through the forecast-grade reference-price
# interface (build_reference_price_node + inject_reference_price_mc) BY DEFAULT,
# with no --reference-price-interface flag required. MISO is the first: it is a
# large structural net importer with no fitted IMPORT_TRANCHES ladder, so the
# reference-price node (each neighbor priced from its own gas × heat-rate × load
# shape, the LP clearing the volume on the spread) is the only correct default —
# and it is forecast-native (claude.md rule #12). PJM stays ABSENT: its
# calibrated backcast serves the measured tie schedule by default, and the flag
# is the opt-in that validates its reference node. ERCOT (no INTERFACE_NEIGHBORS
# entry) is byte-identical regardless.
REFERENCE_PRICE_DEFAULT_ISOS: frozenset[str] = frozenset({"MISO"})


def resolve_reference_price_interface(flag: bool, iso: str) -> bool:
    """Resolve whether ``iso`` runs the reference-price interface.

    ``True`` when the CLI ``--reference-price-interface`` flag is set OR the ISO
    is in :data:`REFERENCE_PRICE_DEFAULT_ISOS` (the per-ISO default-on set). The
    node itself is still gated on the ISO having an ``INTERFACE_NEIGHBORS`` entry
    downstream, so an ISO without neighbors stays byte-identical either way.
    """
    return bool(flag) or iso in REFERENCE_PRICE_DEFAULT_ISOS


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
    # MISO's external node is appended on demand (like PJM/NYISO); the
    # calibrated 3-zone (North/Central/South) topology is untouched. MISO is a
    # large structural net IMPORTER (EIA-930 net interchange −38/−23/−19 TWh,
    # 2023-25), so the seam is served by the forecast-grade reference-price
    # interface (INTERFACE_NEIGHBORS["MISO"]), not the fitted tranche ladder.
    "MISO": "MISO_external",
}

# Links joining an appended external zone to its border zones:
# (border zone, TTC MW). CAISO needs no entry — its links are part of its
# topology (Path 66/COI, Path 46/WOR). PJM TTCs bound the widest measured
# 2023-24 per-border-zone tie flow (eia_loader.pjm_zonal_interchange):
# ComEd −2.3..+7.4 GW, AEP-Ohio −1.0..+4.8, ATSI −5.7..+5.0, Dominion
# −6.2..+3.1, EMAAC −0.1..+5.7. West-APS / Central-PA / SWMAAC carry no
# mapped ties. Source: PJM tie-line actual interchange
# (data/raw/iso-specific-transmission/). Tier 3 — verify against
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
    # UPNY-SENY, Dunwoodie-South). The TTCs must land each tie in the model
    # zone it PHYSICALLY enters, otherwise cheap imports bypass the binding
    # internal interface and erase the real congestion spread. The per-tie
    # entry zones and ratings below are MEASURED from NYISO's hourly
    # ExternalLimitsFlows postings (data/raw/NYISO/External Limit
    # Flow*.zip; "Positive Limit" column, 2023): each SCH-* intertie mapped
    # to its model zone (derive: per-tie median positive limit by zone).
    #   - Upstate_West (zones A–E): HQ Châteauguay (1.5 GW) + Cedars (0.25)
    #     into zone D North, IESO/Ontario (1.75) into A/D, PJM AC ties
    #     (2.2, Homer City/Keystone) into zone A West. The dominant import
    #     gateway (~1.7 GW measured net). Capacity capped at 3.0 GW (the
    #     ties are rarely simultaneous; measured deepest upstate import and
    #     the Central-East cut both sit well below the tie-rating sum).
    #   - NYC (zone J): PJM Hudson Transmission (HTP 660) + Linden VFT (315)
    #     — the in-city DC/PAR cables, ~1.0 GW.
    #   - Long_Island (zone K): PJM Neptune (660) + ISO-NE Cross-Sound (330)
    #     + Northport–Norwalk / NPX_1385 (200) ≈ 1.2 GW.
    #   - Capital_Hudson (F–G) and Lower_Hudson (H–I) have NO net-import tie:
    #     Capital's only external interface is NY↔NE (SCH-NE-NY), which runs
    #     a net EXPORT (~-0.5 GW measured), and Lower_Hudson is internal.
    #     Both are therefore served across Central-East from upstate (or by
    #     in-zone gas), which is what preserves the measured west→east spread.
    #     The NE export is a ~0.5 GW second-order effect deferred to an
    #     export-side refinement. Tier 2 — measured tie ratings/locations.
    "NYISO": [
        ("Upstate_West", 3000.0),
        ("NYC", 1000.0),
        ("Long_Island", 1200.0),
    ],
    # NEISO needs no entry: its HQ_import links (HQ Phase II → Boston,
    # Highgate/NB → North, NYISO ties → Connecticut) are baked into
    # _neiso_config, so extend_with_import_node is a no-op there.
    #
    # MISO external node → border-zone links, one per seam, landed on the model
    # zone the seam PHYSICALLY enters so each neighbor's energy routes through
    # the right border (and the SERC seam stays south of the binding RDT
    # Central↔South contract path rather than wheeling around it):
    #   - PJM → MISO-Central (the IL/IN/MI eastern border): 7,300 MW, the
    #     simultaneous p99.5 of PJM's OWN measured tie flow across the PJM-MISO
    #     seam (PJM Data Miner import_export_act_sch_interchange, pooled
    #     2023-25) — the identical physical seam the PJM build rates at 7,300 MW
    #     for its MISO neighbor (constants INTERFACE_NEIGHBORS["PJM"]). Same
    #     reproducible flow-envelope rating, read for the mirror direction.
    #   - SPP → MISO-North (the Dakotas/IA/NE western border, the wind-export
    #     corridor): 4,000 MW. MISO/SPP coordinated AC interface (Joint
    #     Operating Agreement market-to-market flowgates). Tier 3 — verify
    #     against MISO/SPP OASIS firm transfer capability.
    #   - SERC/South → MISO-South (the Entergy↔SERC border, TVA/Southern/AECI):
    #     3,000 MW. MISO-South external interties to the SERC bilateral
    #     footprint. Tier 3 — verify against SERC/MISO-South interface ratings.
    # Link TTCs sum (14,300 MW) to the seam interface limits, so the border
    # links never bind tighter than the cited per-neighbor ratings. These are
    # physical transfer ratings (reproducible for a forward year, responsive to
    # the flow), NOT values fitted to the −38/−23/−19 TWh net-import target.
    "MISO": [
        ("MISO-Central", 7300.0),
        ("MISO-North", 4000.0),
        ("MISO-South", 3000.0),
    ],
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
# by scripts/derive_nyiso_central_east_ttc.py. They supersede the earlier
# operating-study / Wood Mackenzie estimates (~2,350 pre / ~3,850 post), which
# overstated the operative DAM limit: the posted DAM TTC the dispatch must
# respect runs ~1,750 MW through Nov 2023 and ~2,850 MW from Dec 2023 on — both
# ~1,000 MW below the published "normal" ratings.
#
# NY Transco's "AC Transmission" Segment A (Central-East, Edic–New Scotland /
# Princetown–Rotterdam 345 kV) energized in December 2023, which the postings
# capture as a step from ~1,525-1,950 MW (Jan-Nov 2023) to ~2,725 MW (Dec 2023)
# and ~2,500-3,175 MW across 2024-25, with a recurring late-summer/shoulder
# derate. NYISO_INTERFACE_TTC_BY_MONTH carries that seasonal envelope (12
# monthly means per year); _BY_YEAR carries the annual mean as the scalar
# fallback for paths that do not apply the monthly profile (e.g. forecast).
# UPNY-SENY stays at its static 5,150 MW (it does not bind in the backcast).
NYISO_INTERFACE_TTC_BY_YEAR: dict[int, dict[tuple[str, str], float]] = {
    2023: {("Upstate_West", "Capital_Hudson"): 1750.0},
    2024: {("Upstate_West", "Capital_Hudson"): 2850.0},
    2025: {("Upstate_West", "Capital_Hudson"): 2850.0},
}

# Measured calendar-month mean DAM TTC (MW) for the Central-East interface, one
# 12-element list (Jan..Dec) per backcast year. Applied per-hour over a single
# backcast year by run_calibration._apply_iso_monthly_ttc, which expands the
# scalar TTC array to (hours, n_links) so the dispatch runs on the seasonal
# Central-East envelope instead of one annual value. Regenerate with
# scripts/derive_nyiso_central_east_ttc.py after refreshing the postings.
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


# --- Forecast-grade reference-price interface (multi-ISO, ISO-agnostic) ---
# The fitted IMPORT_TRANCHES/EXPORT_TRANCHES above are a backcast fit: their
# prices/capacities are tuned to each ISO's net-interchange duration curve, so
# they need re-fitting per year and are blind to neighbor fundamentals — fine
# for a backcast, wrong for a 2026-2050 forecast. The reference-price interface
# replaces them with a *forecast-native* construction: each neighbor's energy
# price is built from forward drivers (its gas hub price and its load shape) and
# the seam clears on the spread against the ISO's own price, bounded by the real
# interface limit. Nothing here is tuned to the net-MWh target, so the backcast
# (does the seam reproduce the measured net export *without being told to*?)
# becomes genuine validation rather than a fit. See model-methodology-spec §8.3
# and src/market_sim/data/neighbor_price.py.
#
#   neighbor_price[h] = (henry_hub[year] + gas_basis) x marginal_heat_rate
#                       x load_shape(neighbor_load[h])
#   import when ISO_price > neighbor_price + hurdle
#   export when ISO_price < neighbor_price - hurdle
#   |flow| <= interface_limit_mw
@dataclass(frozen=True)
class NeighborInterface:
    """One external seam to a neighboring balancing authority.

    Every field is a forecast input (a forward gas/load driver) or a
    physically-pinned structural constant (heat rate, hurdle, interface
    rating) — none is tuned to a net-interchange target. ``ba_code`` names
    the EIA-930 balancing authority whose hourly load drives the neighbor's
    price *shape*; when that per-BA extract is absent (e.g. the Carolinas,
    which have no standalone extract yet) ``proxy_ba`` supplies a stand-in
    load shape one seam removed, and the neighbor still prices individually.
    Drop in the real ``<ba_code> hourly.parquet`` later and the proxy is
    bypassed automatically — no structural change. A neighbor that resolves
    to neither its own nor a proxy extract folds into the capacity-weighted
    aggregate (:meth:`InterfacePrices.aggregate`).

    Attributes:
        name: Human label for the seam, e.g. ``"MISO"``.
        ba_code: Primary EIA-930 BA code for the neighbor's load shape.
        proxy_ba: Fallback BA code for the load shape when ``ba_code`` has no
            extract; ``None`` to fold straight into the aggregate.
        gas_basis: $/MMBtu basis of the neighbor's gas hub vs Henry Hub.
        marginal_heat_rate: MMBtu/MWh of the neighbor's *effective* price-
            setting margin — calibrated so ``gas x heat_rate`` reproduces the
            neighbor's own realized annual LMP, NOT a single physical unit's
            heat rate. It runs higher than a CC's ~7 because a real RTO's LMP
            sits above bare gas-burn cost (older marginal units, congestion,
            scarcity and reserve adders). Anchoring to the neighbor's measured
            price formation — a reproducible, gas-responsive quantity — keeps
            the seam forecast-native (the level scales with forward gas) while
            never being tuned to the ISO's net-MWh flow (claude.md rule #11).
        hurdle: $/MWh seam friction (wheeling + losses + scheduling), the
            dead-band the ISO↔neighbor spread must clear before flow starts.
        interface_limit_mw: bidirectional transfer rating bounding seam flow.
        border_zones: ISO model zones the seam physically lands on.
        load_shape_exponent: convexity of the price response to neighbor
            load; 1.0 is a parameter-free, mean-preserving linear shape
            (>1 adds a peak premium from climbing the neighbor's offer stack).
        hr_by_year: optional ``{year: heat_rate}`` overriding
            ``marginal_heat_rate`` for a specific backcast year. The single
            ``marginal_heat_rate`` is a multi-year MEAN of the neighbor's
            realized LMP / Henry-Hub ratio; that ratio drifts year to year
            (MISO 12.5 / 14.1 / 12.2 for 2023-25), so the mean over-prices the
            neighbor in the dear-gas year and under-prices it in the cheap-gas
            year — opening / closing a fake seam export spread (the PJM 2025
            over-export / 2024 under-export). Each entry re-anchors the heat
            rate to the neighbor's OWN measured annual-mean realized LMP for
            that year (claude.md rule #12: measured neighbor price formation
            over a multi-year estimate; never tuned to the ISO's flow — rule
            #11). A year absent here (every forecast year, and neighbors with
            no organized-market LMP such as the Carolinas) falls back to the
            structural ``marginal_heat_rate``, so forecast runs are
            byte-identical. Derive with
            ``scripts/derive_neighbor_hr_by_year.py``.
        firm_export_floor_by_year: optional ``{year: floor_mw}`` of PJM's FIRM
            (must-flow) scheduled export over this seam. PJM exports to MISO /
            NYISO in ~87-100% of hours at a mean spread (~$1.5) too thin for a
            pure hourly energy-spread seam to clear every hour, because a large
            share of the flow is firm, long-term SCHEDULED capacity/energy that
            flows regardless of the hourly price (the mirror of the Hydro-Quebec/
            Manitoba firm imports that floor NYISO/MISO). The economic seam alone
            backs this firm base off in cheap hours, so the seam under-exports in
            the cheap-price years (the PJM 2023 NYISO +4.3 vs +18.5 TWh miss).
            Each entry forces the cheapest export tranches on at ``floor_mw`` so
            the firm base flows every hour, the economic tranches clearing on top
            (:func:`market_sim.model.transmission.inject_reference_price_firm_export`).
            The floor is the p10 of PJM's OWN measured per-tie SCHEDULED export
            (the firm base scheduled in >=90% of hours), NOT the realized
            ``actual_flow`` that is the validation target (rule #11) — a measured
            market-operations input whose forward analogue is the contracted firm
            schedule (rule #12). A year absent here (forecast years, the net-
            IMPORT seams) carries no floor, so the run is byte-identical. Derive
            with ``scripts/derive_firm_export_floor.py``.
    """

    name: str
    ba_code: str
    gas_basis: float
    marginal_heat_rate: float
    hurdle: float
    interface_limit_mw: float
    border_zones: tuple[str, ...]
    proxy_ba: str | None = None
    load_shape_exponent: float = 1.0
    hr_by_year: dict[int, float] | None = field(default=None, compare=False)
    firm_export_floor_by_year: dict[int, float] | None = field(
        default=None, compare=False
    )


# Per-ISO neighbor registry for the reference-price interface. ISO-agnostic
# machinery, parameterized here per ISO + data. PJM is the validated ISO; other
# ISOs adopt the same construction once their neighbor specs are filled in (so
# they stay byte-identical until then). Tier 3 (calibration) — interface limits
# and gas bases carry "verify against published ratings / EIA-923" caveats.
#
# PJM seams (PJM is a structural net exporter): MISO to the west, NYISO to the
# north/east, the Carolinas/Southeast to the south, and the TVA + LGEE (Kentucky/
# Tennessee) footprints to the south-west that PJM net-IMPORTS from (~8 TWh/yr,
# previously unmodeled). PJM exports because its
# resource mix (coal retirements + efficient new CCs, generation near load) sets
# an LMP *below* its neighbors' — confirmed in the field (PJM 2024 State of the
# Market §9; ACORE/PJM-MISO joint studies) and in the price levels: MISO RT LMP
# averaged ~$36/MWh in 2023 and ~$31 in 2024 (Potomac Economics MISO IMM SOM) vs
# PJM's ~$28/$30, and the measured net export shrinks with the spread
# (+40 -> +33 -> +18 TWh, 2023-25).
#
# Effective marginal heat rate per neighbor is calibrated so gas x HR reproduces
# the neighbor's OWN realized annual LMP (rule #11: anchor to the neighbor's
# measured price formation, never to PJM's flow); the year-to-year level then
# rides on the Henry Hub trajectory, so it is forecast-native.
#   - MISO (basis ~0, Chicago Citygate ~flat to HH): HR 12.9, anchored to MISO's
#     OWN realized Indiana-Hub RT LMP / Henry Hub. This REPLACES the prior 14.2
#     ESTIMATE (rule #12: measured data over an estimate). 14.2 came from the IMM
#     State-of-the-Market ~$36 all-MISO-footprint average; the seam actually
#     clears against the PJM-border INDIANA.HUB, whose measured RT LMP is
#     $31.8/$30.8/$42.85 (2023-25, the fetched docs.misoenergy.org ex-post
#     extract), i.e. LMP/HH = 12.5/14.1/12.2, mean 12.9. The old 14.2 over-priced
#     the border hub by +13% (2023) / +17% (2025), inflating the PJM->MISO spread
#     and over-exporting; 12.9 is the like-for-like measured ratio. Regenerate
#     with scripts/derive_neighbor_convexity.py (reports the implied HR).
#   - NYISO (basis +0.55, EIA-923 delivered): HR 13.1, anchored to the actual
#     NYISO RT LMP $36 (2024) / delivered gas $2.74. CAVEAT: NYISO downstate is
#     congestion/scarcity-dominated, so its implied ratio is NOT stable (9.8 in
#     2023, 13.1 in 2024, 17.7 in 2025); 13.1 is the mid-year anchor and will
#     understate NY's tight years. NYISO is the smallest PJM seam (EMAAC only).
#   - Carolinas (basis ~0): HR 13.5, an ESTIMATE pending a Duke (DUK) LMP/extract
#     — the Southeast is not an organized market, so this is anchored to a
#     ~$30/MWh SERC bilateral level / Henry Hub, priced on the SOCO load shape.
# Hurdle $1/MWh is the MARGINAL delivery-loss component of an incremental seam
# transaction (~3% x the ~$35/MWh seam energy). This REPLACES the prior $2 (the
# OMS-RSC inter-RTO "wheeling/transaction adder") because $2 conflated TWO costs
# into one marginal threshold: (a) firm point-to-point transmission service /
# capacity reservation, which is paid by FIRM scheduled transactions — now
# modeled explicitly as the firm-export floor (firm_export_floor_by_year), which
# flows regardless of the hourly spread and so implicitly bears that charge; and
# (b) marginal losses on the incremental economic flow. Under the PJM-MISO and
# PJM-NYISO Joint Operating Agreements / market-to-market coordination the
# coordinated economic flow pays NO pancaked through-and-out transmission rate, so
# the only marginal friction left for the economic increment is losses (~$1). The
# old single $2 hurdle simultaneously over-charged the economic margin (PJM
# exports at a ~$1.5 mean PJM-MISO spread, which $2 mostly blocks -> the MISO/
# NYISO under-export) AND omitted the firm base (-> the 2023 NYISO collapse).
# Splitting them — firm floor + $1 losses hurdle — is a physical decomposition,
# not a flow fit (rule #11): the $1 is losses x price, the floor is measured
# scheduled volume; neither sees the realized net-MWh target.
#
# Interface limits are the firm continuous transfer capability of each seam,
# derived from PJM's OWN published per-tie interchange (the Data Miner
# import_export_act_sch_interchange extract): each external tie is mapped to its
# seam, the per-tie hourly actual flow is summed to the *simultaneous* seam
# transfer, and the limit is the p99.5 of |seam flow| pooled over 2023-25 — the
# duration curve's upper envelope minus the top ~0.5% transient/loop-flow hours.
# This is a reproducible physical rating (regenerable for a forward year,
# responsive to changed flows), NOT a value tuned to the net-MWh target (rule
# #11): the envelope is computed from the flow series before any LP runs. The
# prior 10/3/3.5 GW were envelopes of the widest *single-tie* maxima, which
# over-stated the simultaneous MISO seam (ties don't all peak at once) and
# under-stated the multi-line NYISO seam. Re-derive / verify with
# scripts/derive_interface_limits.py (--check asserts these still match):
#   MISO      7,300 MW (was 10,000; simultaneous export p99.5 7,290, max 8,789)
#   NYISO     3,900 MW (was  3,000; export p99.5 3,866, max 4,204 — cross-checks
#             the published facility ratings: Neptune 660 + Hudson HTP 660 +
#             Linden VFT 330 + PJM-NY AC ties ~2,000 ~= 3,650 MW)
#   Carolinas 2,400 MW (was  3,500; |flow| p99.5 2,418 on the Duke/Progress ties
#             — note PJM net-*imports* over this seam, exporting only ~17% of
#             hours, so the limit binds mostly on the import side)
#   TVA       1,600 MW (the single TVA tie's |flow| p99.5, pooled 2023-25; PJM
#             net-imports ~6 TWh/yr, exporting only 3-9% of hours)
#   LGEE      1,100 MW (the single LGEE tie's |flow| p99.5; PJM net-imports
#             ~2.3 TWh/yr, exporting ~16-19% of hours)
# (LAGN remains unmapped — its measured flow is ~0.)
#
# load_shape_exponent (price-vs-load convexity): the flow-responsive seam
# (neighbor_price.seam_tranche_prices) prices each export band at the neighbor's
# price read at its load *reduced* by the band's flow, so the neighbor's
# willingness-to-pay slides down its own gas x HR x (load/mean)**exp supply
# curve as PJM exports into it. With exp=1.0 (linear) the slope is too gentle —
# a <=7.3 GW seam flow against a ~75 GW neighbor barely moves its price, so the
# seam pins at the interface cap and the model over-exports (the pjm_30/pjm_31
# +78-89 TWh residual vs measured +40/+33/+18). A real marginal supply curve is
# convex, so exp>1. The exponent is recovered as a MEASURED market quantity
# (scripts/derive_neighbor_convexity.py, rule #11 — never tuned to PJM's net
# export): regress log(neighbor realized RT LMP) on log(neighbor load/mean) in
# log-log space; the slope IS the exponent. It is dimensionless, regenerable for
# a forward year and load-responsive, so it stays forecast-native.
#   - NYISO: 1.63, SELF-DERIVED from NYISO's own realized RT LMP vs its EIA-930
#     load (gross-load regressor — the series the model multiplies), pooled
#     2023-24, R2 0.36, stable by year (1.64/1.63). This is the model-consistent
#     anchor.
#   - MISO: 1.60, SELF-DERIVED from MISO's own realized Indiana-Hub RT LMP (the
#     fetched docs.misoenergy.org extract) vs its EIA-930 load, pooled 2023-25,
#     R2 0.24, by year 1.42/1.80/1.60. This REPLACES the borrowed 1.63 with the
#     measured value (rule #12) — and confirms the borrow was sound (MISO's own
#     convexity ~= NYISO's), so it is NOT what drove the pjm_32 over-export; the
#     MISO-level (heat-rate) re-anchor above is.
#   - Carolinas: 1.60, still borrowed (no organized-market LMP — Duke FERC-714
#     hourly-lambda reshape is a verified follow-up) but now set to the MEASURED
#     thermal-neighbor value: MISO 1.60 and NYISO 1.63 self-derive to the same
#     ~1.6, cross-validated by NEISO 2.04 / ERCOT-net 1.47. Carolinas is the
#     smallest seam and a net IMPORT path (PJM exports over it ~17% of hours), so
#     its exponent barely moves the result. Not a PJM-flow fit: the value comes
#     from the neighbors' own LMP-vs-load elasticity, blind to PJM's net export.
#     (CAISO's gross exponent collapses to
#     0.47 under heavy solar, which is exactly why gross-load convexity is used
#     ONLY for these low-solar thermal neighbors; CAISO net-load holds at 1.00.)
INTERFACE_NEIGHBORS: dict[str, list[NeighborInterface]] = {
    "PJM": [
        NeighborInterface(
            name="MISO",
            ba_code="MISO",
            gas_basis=0.0,
            marginal_heat_rate=12.9,
            hurdle=1.0,
            interface_limit_mw=7300.0,
            border_zones=("PJM_ComEd", "PJM_AEP_Ohio", "PJM_ATSI"),
            load_shape_exponent=1.60,
            # Per-year measured anchor (derive_neighbor_hr_by_year.py): the 12.9
            # mean over-priced the MISO border hub +7% in dear-gas 2025 (measured
            # ratio 12.0) and under-priced it -7% in 2024 (13.9), flipping the
            # largest PJM seam to a fake export in 2025. Anchored to the measured
            # Indiana-Hub RT LMP each year.
            hr_by_year={2023: 12.38, 2024: 13.92, 2025: 12.03},
            # Firm scheduled-export floor (derive_firm_export_floor.py, p10 of
            # PJM's measured per-tie SCHEDULED export). MISO's firm base is large
            # in 2023 and collapses to ~0 by 2025 as MISO tightened — so MISO is
            # mostly ECONOMIC and the under-export is fixed by the losses-only
            # hurdle above, the floor only binding the cheap-spread hours of 2023.
            firm_export_floor_by_year={2023: 1250.0, 2024: 100.0, 2025: 0.0},
        ),
        NeighborInterface(
            name="NYISO",
            ba_code="NYIS",
            gas_basis=GAS_BASIS_DIFFERENTIAL["NYISO"],
            marginal_heat_rate=13.1,
            hurdle=1.0,
            interface_limit_mw=3900.0,
            border_zones=("PJM_EMAAC",),
            load_shape_exponent=1.63,
            # Per-year measured anchor (derive_neighbor_hr_by_year.py): NYISO's
            # LMP/HH ratio is the least stable seam (downstate congestion/
            # scarcity), so the 13.1 mean badly over-prices cheap-2023 (measured
            # 9.7) and under-prices tight-2025 (14.7). Anchored to the measured
            # NYISO RT LMP each year. Smallest PJM seam (EMAAC only). CAVEAT: this
            # is NYISO's NYC-weighted SYSTEM-average LMP, not the PJM-NY (west-NY)
            # BORDER the seam physically clears against; the system average is
            # congestion-inflated in tight hours, so the economic seam still
            # over-exports NY in dear-2025 (the scope-B border-price re-anchor is
            # a follow-up, gated on a committed west-NY hourly LMP extract).
            hr_by_year={2023: 9.66, 2024: 12.92, 2025: 14.67},
            # Firm scheduled-export floor (derive_firm_export_floor.py, p10 of
            # PJM's measured per-tie SCHEDULED export). NYISO export is firm-
            # dominated (100% of hours, a stable ~900-1650 MW scheduled base), so
            # the volatile system-avg HR drove the 2023 collapse (model +4.3 vs
            # measured +18.5): the firm base flows regardless of the cheap-2023
            # spread. The economic tranches clear on top.
            firm_export_floor_by_year={2023: 900.0, 2024: 1400.0, 2025: 1650.0},
        ),
        NeighborInterface(
            name="Carolinas",
            ba_code="DUK",
            proxy_ba="SOCO",
            gas_basis=0.0,
            # 11.6 reconciles the HR to its OWN documented basis — the ~$30/MWh
            # SERC bilateral level / Henry Hub: $30 / $2.54 (2023 HH) / 1.02
            # (load-shape mean) = 11.6. The prior 13.5 produced $34 at 2023 HH
            # (+14% above the stated $30 anchor) and was the HIGHEST HR of any
            # PJM neighbor — implausible for the nuclear/CC-heavy Southeast, a
            # structurally cheaper region PJM net-IMPORTS from. The reconciled
            # value prices the Carolinas at/below PJM, flipping the seam to the
            # net-import direction PJM's OWN published per-tie interchange shows
            # (Data Miner: PJM net-imports -5..-6 TWh/yr over the Duke/Progress
            # ties, ~17% export hours). NOT tuned to that flow (rule #11): the
            # value comes from the documented $30 SERC anchor and the per-tie
            # data only VALIDATES the resulting direction. Estimate, pending a
            # measured Duke FERC-714 hourly system-lambda extract (rule #12); no
            # organized-market LMP exists for the Southeast, so no hr_by_year.
            marginal_heat_rate=11.6,
            hurdle=1.0,
            interface_limit_mw=2400.0,
            border_zones=("PJM_Dominion",),
            load_shape_exponent=1.60,
        ),
        NeighborInterface(
            name="TVA",
            ba_code="TVA",
            proxy_ba="SOCO",
            gas_basis=0.0,
            # Southeast SERC structural HR, identical basis to the reconciled
            # Carolinas seam: ~$30/MWh SERC bilateral level / Henry Hub. TVA is a
            # nuclear/coal/hydro-heavy footprint structurally CHEAPER than PJM, so
            # PJM net-IMPORTS from it (PJM Data Miner per-tie: PJM net-imports
            # ~6 TWh/yr over the TVA tie, exporting only 3-9% of hours). No
            # organized-market LMP exists for the Southeast, so this is the same
            # documented $30 SERC anchor the Carolinas use (rule #12: documented
            # estimate where measured is absent); the per-tie data only VALIDATES
            # the resulting net-import direction, it is NOT tuned to it (rule #11).
            marginal_heat_rate=11.6,
            hurdle=1.0,
            # p99.5 |flow| of PJM's measured TVA tie, pooled 2023-25
            # (derive_interface_limits.py): 1565/1539/1678 -> 1600 MW.
            interface_limit_mw=1600.0,
            border_zones=("PJM_AEP_Ohio", "PJM_Dominion"),
            load_shape_exponent=1.60,
        ),
        NeighborInterface(
            name="LGEE",
            ba_code="LGEE",
            proxy_ba="SOCO",
            gas_basis=0.0,
            # Louisville Gas & Electric / KU (Kentucky): a coal-heavy, low-cost
            # footprint PJM net-IMPORTS from (~2.3 TWh/yr, exporting ~16-19% of
            # hours). Priced on the same documented Southeast SERC $30/HH basis as
            # TVA / the Carolinas (rule #12); per-tie data validates the direction
            # (rule #11), not tuned to it.
            marginal_heat_rate=11.6,
            hurdle=1.0,
            # p99.5 |flow| of PJM's measured LGEE tie, pooled 2023-25
            # (derive_interface_limits.py): 1143/1096/995 -> 1100 MW.
            interface_limit_mw=1100.0,
            border_zones=("PJM_West_APS", "PJM_AEP_Ohio"),
            load_shape_exponent=1.60,
        ),
    ],
    # MISO seams (MISO is a structural net IMPORTER): PJM to the east, SPP to
    # the west, and the SERC/Southeast bilateral footprint to the south. MISO
    # imports because its own LMP sits ABOVE its cheaper neighbors' — the
    # measured Indiana-Hub RT LMP averaged $31.8/$30.8/$42.9 (2023-25, the
    # committed actual_lmp_hourly_MISO product) vs PJM's $28.4/$29.5/$42.9 and
    # SPP's wind-set ~$25/$23 — and the measured net import is large
    # (−37.9/−23.1/−19.0 TWh, EIA-930). Each neighbor is priced from its OWN
    # forward drivers (gas × heat-rate × its load shape); nothing here is tuned
    # to the net-MWh target (claude.md rules #1/#12), so the backcast net
    # import is genuine validation, not a fit.
    #
    # Effective marginal heat rate per neighbor is anchored to the neighbor's
    # OWN realized annual LMP / Henry Hub (rule #12: the neighbor's measured
    # price formation, never MISO's flow); the level then rides the Henry Hub
    # trajectory ($2.54/$2.19/$3.52 MMBtu actual, 2023-25), so it is
    # forecast-native:
    #   - PJM (basis ~0, Chicago/M3 ~flat to HH): HR 12.3, the 3-year mean of
    #     PJM's MEASURED RT-LMP/HH ratio (11.2/13.5/12.2, from
    #     actual_lmp_hourly_PJM divided by the actual Henry Hub). CAVEAT: the
    #     ratio is not stable across years (PJM 2023 ran cheap at 11.2), so the
    #     single mean over-prices PJM in 2023 and under-prices it in 2024 — a
    #     mid-year anchor, not a fit.
    #   - SPP (basis ~0, wind-set): HR 10.0 structural, now anchored per year to
    #     SPP's MEASURED realized RT-LMP/HH (9.24/10.65/7.70, from the committed
    #     actual_lmp_hourly_SPP product — system mean of SPPNORTH_HUB +
    #     SPPSOUTH_HUB from the SPP Integrated Marketplace — divided by actual
    #     Henry Hub). The flat 10.0 over-prices wind-set SPP in dear-gas 2025
    #     (ratio 7.70): high HH does not lift SPP's wind-marginal LMP. SPP is
    #     wind-rich and reliably cheaper than MISO (RT ~$23.5/$23.3/$27.1).
    #   - SERC/South (basis ~0): HR 12.0, an ESTIMATE — the Southeast is not an
    #     organized market, so this is anchored to a ~$30/MWh SERC bilateral
    #     level / actual Henry Hub (ratios 11.8/12.3/11.9), priced on the
    #     Southern Company (SOCO) load shape.
    # Hurdle $2/MWh is the inter-RTO wheeling/transaction adder (OMS-RSC seams
    # interface-pricing study), as in the PJM build. load_shape_exponent 1.0 is
    # the parameter-free, mean-preserving linear shape — so each neighbor's
    # annual-mean price equals its anchored gas × HR exactly (no convexity
    # inflation of the mean); the seam still self-limits below the cap through
    # MISO's OWN falling LMP dual as it imports (the LP equilibrium). A peak-
    # premium convexity (exp > 1, as PJM uses) is a documented future refinement
    # once the base seam is validated. Interface limits: see IMPORT_NODE_LINKS.
    "MISO": [
        NeighborInterface(
            name="PJM",
            ba_code="PJM",
            gas_basis=0.0,
            marginal_heat_rate=12.3,
            hurdle=2.0,
            interface_limit_mw=7300.0,
            border_zones=("MISO-Central",),
            load_shape_exponent=1.0,
            # Per-year measured anchor (derive_neighbor_hr_by_year.py --iso MISO):
            # the flat 12.3 mean UNDER-prices the PJM hub in dear-gas 2024
            # (measured ratio 13.49), so the largest MISO seam over-imports from
            # PJM (-59 vs actual -23 TWh net interchange); 2025 (12.18) and 2023
            # (11.2) re-anchor each year to PJM's own realized RT LMP / Henry Hub.
            # Measured neighbor price-formation input (rule #12), blind to MISO's
            # own interchange (rule #11 — the derivation never sees MISO flow).
            hr_by_year={2023: 11.2, 2024: 13.49, 2025: 12.18},
        ),
        NeighborInterface(
            name="SPP",
            ba_code="SWPP",
            gas_basis=0.0,
            marginal_heat_rate=10.0,
            hurdle=2.0,
            interface_limit_mw=4000.0,
            border_zones=("MISO-North",),
            load_shape_exponent=1.0,
            # Per-year measured anchor (derive_neighbor_hr_by_year.py --iso MISO):
            # SPP's realized RT hub LMP / Henry Hub from the committed
            # actual_lmp_hourly_SPP product (RT $23.5/$23.3/$27.1, system mean of
            # SPPNORTH_HUB + SPPSOUTH_HUB, SPP Integrated Marketplace; DA mean
            # $25.6 in 2023 matches the Potomac Economics SPP IMM print) / actual
            # Henry Hub ($2.54/$2.19/$3.52). The flat 10.0 mean badly OVER-prices
            # wind-set SPP in dear-gas 2025 (measured ratio 7.70 << 10.0 — the
            # high HH does NOT lift SPP's wind-marginal LMP), so the SPP seam
            # under-imports and MISO over-runs its own coal: a suspect for the
            # 2025 MISO net-interchange sign-flip. 2023 (9.24) / 2024 (10.65)
            # re-anchor each year to SPP's OWN realized price. Measured neighbor
            # price-formation input (rule #12), blind to MISO's interchange
            # (rule #11 — the derivation never sees MISO flow).
            hr_by_year={2023: 9.24, 2024: 10.65, 2025: 7.7},
        ),
        NeighborInterface(
            name="South",
            ba_code="SOCO",
            gas_basis=0.0,
            marginal_heat_rate=12.0,
            hurdle=2.0,
            interface_limit_mw=3000.0,
            border_zones=("MISO-South",),
            load_shape_exponent=1.0,
        ),
    ],
}

# --- MISO per-seam measured BA-to-BA deliverability envelope ----------------
# Maps each MISO reference-price seam (the INTERFACE_NEIGHBORS["MISO"] names) to
# the EIA-930 Directly-Interconnected-BA codes whose measured hourly directed
# interchange physically crosses that seam's border zone. The seam's per-hour
# import-deliverability ceiling is the (month × hour-of-day) high-percentile of
# the summed measured NET IMPORT over its DIBAs (data/raw/eia-930-interchange/
# MISO interchange hourly.parquet; EIA sign + = MISO exports to the DIBA, so net
# import = −sum). This is an ATC/transfer-capability proxy — the seam's
# *deliverable* import in that period, congestion/firm-rights-limited below the
# nameplate interface rating — applied as a one-sided (import-direction) hourly
# upper bound (transmission.inject_miso_seam_flow_limit). It is a reproducible
# physical transfer characteristic (regenerable for a forward year from the
# directed-flow series, responsive to changed flows), NOT a value fitted to
# MISO's net-interchange residual (claude.md rules #1/#12): the envelope is
# computed from the per-seam directed flow before any LP runs, the export
# direction stays economic, and a high percentile keeps headroom above the
# median so price — not the cap — sets the typical hour.
#
# Border mapping (geographic, eastern/western/southern):
#   - PJM seam (MISO-Central, eastern IL/IN/MI border): PJM (the dominant
#     net-import tie) + IESO/Ontario (the Michigan international tie, a real
#     ~3-7 TWh/yr import that physically enters the same eastern border).
#   - SPP seam (MISO-North, western Dakotas/IA/NE border): SWPP (the MISO/SPP
#     coordinated AC interface) + SPA (Southwestern Power Administration federal
#     hydro in the SPP footprint). MISO nets ~0/slight EXPORT here — the measured
#     net import is near zero, so the seam's import cap is small and the spurious
#     cheap-wind over-import is removed; the wind-import hours the p90 still
#     captures stay available.
#   - South seam (MISO-South, Entergy↔SERC border): SOCO + TVA + AECI + LGEE +
#     SIKE. MISO net-EXPORTS to the south (TVA dominant, ~+13-18 TWh/yr), so the
#     summed net import is negative in most buckets and the import cap clips to
#     ~0 — the export direction (priced seam economics) carries MISO's real
#     southern export.
# Manitoba Hydro (MHEB) is deliberately EXCLUDED: it is modeled as the separate
# firm-hydro block (MISO_MANITOBA_FIRM_IMPORT_*), not the gas-margin seam. The
# three seam caps + the firm block thus reconstruct the full measured MISO net
# interchange.
MISO_SEAM_DIBA: dict[str, tuple[str, ...]] = {
    "PJM": ("PJM", "IESO"),
    "SPP": ("SWPP", "SPA"),
    "South": ("SOCO", "TVA", "AECI", "LGEE", "SIKE"),
}

# Percentile of the per-(month × hour-of-day) measured net-import distribution
# used as each seam's deliverability ceiling. 90 = the upper envelope minus the
# top ~10% transient/loop-flow hours (matching measured_interchange_envelope's
# default and the interface-limit duration-curve convention), keeping headroom
# above the median so the modeled seam price still sets the typical hour. A
# deliverability-headroom choice, NOT tuned to the net-MWh target.
MISO_SEAM_FLOW_PERCENTILE: float = 90.0

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
    # MISO uses the reference-price node (flow-bounded by the cited interface
    # limit), like PJM/NYISO — no extra availability derate.
    "MISO": 0.0,
}

# Per-tranche CO2 emission factor (tCO2/MWh) for the CARB border-carbon
# adjustment on imports. CARB assesses its allowance obligation on the
# *specified* emissions of an import — zero for firm hydro / solar / nuclear
# delivered under an e-tag — and falls back to CARB_UNSPECIFIED_IMPORT_EF
# (0.428) ONLY for unspecified power. Charging the flat 0.428 on every block
# (the prior build-time behaviour) over-prices CAISO's clean import blocks
# (PNW hydro, desert-SW solar/Palo Verde) by ~$12-15/MWh, lifting them above
# the in-state gas merit order so the model burns domestic gas midday instead
# of importing the cheap zero-carbon energy CAISO actually takes — inflating
# the spring/midday price floor (model ~$46 vs actual ~$14 in Apr-May). Each
# tranche now carries its resource's EF; build_import_generators scales the
# border adder by ef / CARB_UNSPECIFIED_IMPORT_EF, so a tranche absent from
# this map keeps the full unspecified default (byte-identical for any ISO
# without an entry). Gas EFs ≈ heat rate × 0.0531 tCO2/MMBtu (CCGT ~7, CT ~10.4).
IMPORT_TRANCHE_EF: dict[str, dict[str, float]] = {
    "CAISO": {
        "PNW_hydro_base": 0.0,  # firm Pacific-NW hydro — specified, zero-EF
        "PNW_midC": 0.0,  # Mid-Columbia hydro/wind
        "DSW_solar_PV": 0.0,  # desert-SW solar + Palo Verde nuclear
        "DSW_CCGT": 0.37,  # desert-SW combined-cycle gas (~7 HR)
        "DSW_CT": 0.55,  # desert-SW combustion turbine (~10.4 HR)
        "WECC_scarcity": CARB_UNSPECIFIED_IMPORT_EF,  # unspecified west-wide
    },
}

# Per-tranche physical delivered-cost basis over the measured WECC neighbor-hub
# price, for CAISO priced imports under ``--caiso-import-hub-prices``.
# measured_import_hub_prices now returns the FULL delivered nodal LMP (energy +
# congestion + loss = MCE+MCC+MCL) AT the neighbor scheduling point (Malin / Palo
# Verde), so the per-node congestion/loss already separate the PNW and desert-SW
# hubs (MALIN != PALOVRDE) and the marginal LOSS is measured, not modeled.
#
# Each tuple is (loss_fraction, wheeling $/MWh). NOTE: as of the per-hub nodal
# fetch (2026-06-23), the loss_fraction is RETAINED ONLY FOR DOCUMENTATION /
# bidir-fallback — inject_caiso_import_hub_prices NO LONGER applies it, because
# the measured nodal MCL now carries the real loss and the multiplicative markup
# would double-count it (rules #11/#12: prefer the measured loss, ground the
# change). Only the wheeling charge is added: the OATT point-to-point
# wheeling/access charge ($/MWh) a marketer pays the intervening BAA(s) to
# deliver to the CAISO border — a real commercial charge that is NOT part of
# CAISO's nodal LMP and is forward-reproducible (NOT a residual-fitted offset,
# rule #12). The gas blocks (DSW_CCGT/CT) are re-priced off measured gas by
# inject_caiso_import_gas_coupling AFTER this, so the wheel mainly shapes the
# non-gas blocks (PNW_*, DSW_solar_PV).
#
# Per tranche/path (loss fraction [now documentation-only], wheeling $/MWh):
#   - PNW_hydro_base: firm COI economy energy, single BPA point-to-point.
#     ~660-mi AC path, losses ~4%; PTP wheeling ~$2.0/MWh.
#   - PNW_midC: Mid-Columbia shoulder over COI/PDCI — deeper, multi-BAA wheel
#     (BPA + PacifiCorp). Losses ~5%; stacked PTP ~$5.0/MWh.
#   - DSW_solar_PV: Path 46 / West-of-River desert-SW solar + Palo Verde.
#     ~280-mi path, losses ~3%; WALC/Path-46 PTP ~$4.0/MWh.
#   - DSW_CCGT / DSW_CT: same Path-46 basis (overwritten by gas coupling).
#   - WECC_scarcity: peak west-wide economy energy, congested wheel ~$6.0/MWh.
# Source: WECC transmission loss factors; BPA / PacifiCorp / WALC OATT
# point-to-point transmission rate schedules. Tier 3 — verify against the
# posted OATT rates and WECC path loss studies.
CAISO_IMPORT_DELIVERY_BASIS: dict[str, tuple[float, float]] = {
    "PNW_hydro_base": (0.04, 2.0),
    "PNW_midC": (0.05, 5.0),
    "DSW_solar_PV": (0.03, 4.0),
    "DSW_CCGT": (0.03, 4.0),
    "DSW_CT": (0.03, 4.0),
    "WECC_scarcity": (0.03, 6.0),
}

# Backwards-compatible aliases for the original CAISO-only WECC names.
WECC_IMPORT_TRANCHES: list[tuple[str, float, float]] = IMPORT_TRANCHES["CAISO"]
WECC_EXPORT_CAP_MW: float = EXPORT_TRANCHES["CAISO"][0][1]
WECC_IMPORT_EFORD: float = IMPORT_EFORD["CAISO"]

# --- CAISO per-hub signed intertie (the diurnal-shape + per-hub-basis fix) ----
# CAISO's WECC tie is TWO physically distinct corridors, each terminating at a
# different neighbor hub: COI / Path 66 (the California–Oregon Intertie, ~Malin /
# Mid-C) lands in NP15 to the north, and Path 46 / West-of-River (~Palo Verde /
# desert-SW) lands in SP15 to the south. The keeper pools every import tranche
# (Malin- AND Palo-Verde-priced) plus one AVERAGED-hub export sink onto a single
# external bubble, so (a) the cheap midday Palo Verde block can fill the whole
# 8.3 GW import budget over either link (the priority-1 over-import), and (b) the
# independent import/export legs never net, so the diurnal interchange sign is
# inverted (priority-2). The single-flow bidir node fixed the netting but had to
# AVERAGE the two hubs into one price, discarding the per-hub basis. Splitting
# the node into the two real corridors — each a SINGLE signed flow priced at its
# OWN measured hub — recovers BOTH: per-hub basis (Malin != Palo Verde) AND
# per-hub netting (each corridor carries one net direction per hour, so the
# Palo-Verde leg reverses to EXPORT in the midday solar glut instead of
# over-importing). The simultaneous-import cap (8.3 GW) stays as the existing
# WECC_import_simultaneous interface limit, now spanning the two corridor links.
# Source: CAISO config COI(NP15)/Path-46(SP15) link ratings (WECC Path Rating
# Catalog); EIA-930 CISO net-interchange diurnal profile; measured WECC intertie
# nodal LMP per scheduling point (Malin/Palo Verde).
#
# Per-hub external zones and the corridor link each terminates on (the link is
# re-homed from WECC_import to the hub zone by
# transmission.split_caiso_import_node_per_hub):
CAISO_PER_HUB_IMPORT_ZONES: dict[str, str] = {
    "MALIN": "WECC_PNW",  # COI / Path 66 → NP15 (north)
    "PALOVRDE": "WECC_DSW",  # Path 46 / West-of-River → SP15 (south)
}
# CAISO import tranche → the WECC neighbor hub (and therefore the per-hub zone)
# whose measured intertie LMP is the tranche's real delivered energy cost. The
# PNW blocks (firm hydro + Mid-C shoulder) clear over Malin/COI; the desert-SW
# blocks (solar + Palo Verde nuclear, then SW gas) and the west-wide scarcity
# block clear over Palo Verde / Path-46. This is the single source of truth for
# the mapping (eia_loader.measured_import_hub_prices imports it), so the loader
# and the per-hub builder/injector can never drift apart.
CAISO_IMPORT_TRANCHE_HUB: dict[str, str] = {
    "PNW_hydro_base": "MALIN",
    "PNW_midC": "MALIN",
    "DSW_solar_PV": "PALOVRDE",
    "DSW_CCGT": "PALOVRDE",
    "DSW_CT": "PALOVRDE",
    "WECC_scarcity": "PALOVRDE",
}

# Measured WECC corridor deliverability envelope (``caiso_corridor_flow_limit``).
# ------------------------------------------------------------------------------
# Each CAISO import corridor (COI/Path-66 into NP15, Path-46/WOR into SP15) has a
# diurnal *deliverable* ceiling that is far below its physical line rating: the
# desert-SW and Pacific-NW neighbors are themselves long on solar midday, so the
# transfer they can actually schedule into a simultaneously-long CAISO collapses
# from ~6 GW overnight to ~3-4 GW midday (DSW) and ~2.3 GW → ~0.8 GW (PNW). The
# per-hub injector prices the whole neighbor stack at the cheap midday hub LMP,
# so without a deliverability ceiling the LP pulls the neighbors' (idle) thermal
# tranches over the line up to the 8.3 GW simultaneous cap — the spurious ~5 GW
# midday over-import behind the inverted diurnal residual.
#
# The ceiling is the per-(month × hour-of-day) high percentile of the MEASURED
# net import on each corridor, from EIA-930 BA-to-BA interchange
# (data/raw/eia-930-interchange/CISO interchange hourly.parquet), aggregated by
# the CISO↔DIBA → corridor map below. It is an ATC proxy (the operational
# transfer ceiling, TTC net of parallel commitments and reliability margins),
# applied as a one-sided hourly upper bound on the corridor link's import-
# direction flow — the model still clears its own merit order *below* the
# ceiling, so this is a capability limit, not an outcome pinned to the residual
# (rule #12). The export direction keeps the physical link TTC (midday CA export
# is real). Forward analogue: a forecast year uses the path's forecast ATC; the
# percentile-of-history envelope is the backcast-mode reconstruction of it.
#
# CISO DIBA → corridor, split geographically at Path-15 (north of Path-15 lands
# on NP15 via COI; south lands on SP15 via Path-46/49 and the Mexico tie). The
# two corridors together carry CISO's whole external net interchange, so every
# DIBA is assigned to exactly one. Source: EIA-930 BA reference table; CAISO
# transmission topology (COI/Path-66, Path-46 West-of-River, Path-49 East-of-
# River, Path-15 north/south split).
CAISO_CORRIDOR_DIBA: dict[str, str] = {
    # North / COI / Path-66 → NP15 (Pacific NW + northern-CA BAs)
    "BPAT": "WECC_PNW",  # Bonneville (Pacific NW, COI)
    "PACW": "WECC_PNW",  # PacifiCorp West (Oregon, COI)
    "BANC": "WECC_PNW",  # Balancing Authority of Northern California (Sacramento)
    "TIDC": "WECC_PNW",  # Turlock ID (Central Valley)
    # South / Path-46 (West-of-River) + Path-49 + Mexico tie → SP15 (desert-SW)
    "AZPS": "WECC_DSW",  # Arizona Public Service (Palo Verde)
    "SRP": "WECC_DSW",  # Salt River Project (Arizona)
    "WALC": "WECC_DSW",  # WAPA Lower Colorado (Arizona)
    "NEVP": "WECC_DSW",  # NV Energy (southern Nevada)
    "IID": "WECC_DSW",  # Imperial Irrigation District (SE California desert)
    "LDWP": "WECC_DSW",  # LA Dept of Water & Power (LA basin, Path-46 adjacent)
    "CEN": "WECC_DSW",  # CFE Baja California (Mexico tie into SP15)
}
# Percentile of the measured per-(month × hour-of-day) corridor net import used
# as the deliverability ceiling. p95 = the operational transfer ceiling (an ATC
# proxy): high enough that the LP clears below it in the typical hour (not a pin
# to the mean), low enough that it removes the unphysical midday flood. Not tuned
# to the price/volume residual — it is the standard high-percentile ATC envelope.
CAISO_CORRIDOR_FLOW_PERCENTILE: float = 95.0


# --- CAISO per-hub FORWARD intertie seam (reference price + ATC) ---------------
# The forward-grade replacement for the two MEASURED CAISO levers above (the
# measured WECC hub LMP that `caiso_per_hub_intertie` prices each corridor at,
# and the measured p95 net-import envelope that `caiso_corridor_flow_limit`
# caps it at). Both measured series go inert in a forecast year (no OASIS LMP,
# no future EIA-930 interchange), so the forecast CAISO loses all import price-
# formation and deliverability shaping. This block carries the SAME forecast-
# native construction PJM/MISO use for their seams (constants
# INTERFACE_NEIGHBORS, src/market_sim/data/neighbor_price.py), specialized to
# CAISO's two physical WECC corridors:
#
#   per-hub price[h] = (henry_hub[year] + gas_basis) × marginal_heat_rate
#                      × load_shape(neighbor)[h]
#
# Each corridor proxies one WECC neighbor hub — COI/Path-66 → the Pacific-NW at
# Malin (WECC_PNW), Path-46/WOR → the desert-SW at Palo Verde (WECC_DSW). The
# level rides the forward Henry Hub trajectory (so a dear-gas year reprices
# imports up); the SHAPE rides the neighbor's own hourly tightness. Because the
# desert-SW LMP is *solar*-driven (its midday trough is the solar glut, not a
# gross-load peak), WECC_DSW shapes on the region's NET load (load − solar −
# wind), while the hydro-following Pacific-NW shapes on gross load. The shape is
# proxied from the EIA-930 CISO extract (the only WECC hourly series in-repo —
# the desert-SW shares CAISO's solar resource and time zone), a forward driver
# that responds to a changed solar build, NOT the measured Palo Verde/Malin LMP
# (the honesty line: price formation from forward gas/HR/shape, never pinned to
# the measured realization — CLAUDE.md #10/#12). The measured hub LMP stays the
# BACKCAST realization the formula is validated against (scripts/
# compare_caiso_intertie_formula_vs_measured.py).
#
# marginal_heat_rate is the neighbor's EFFECTIVE price-setting heat rate
# (gas × HR ≈ the hub's realized annual LMP), the NeighborInterface convention.
# It is a 3-year-mean structural value (NOT a per-year measured anchor — that
# would pin the level to the realization), so forecast years stay byte-stable
# and the backcast carries the documented gas-insensitivity residual: the
# Pacific-NW/desert-SW marginal price is often hydro/solar-set, so it does NOT
# rise with Henry Hub the way a pure gas margin would (the same effect SPP's
# wind-set LMP shows in INTERFACE_NEIGHBORS["MISO"]). gas_basis values are the
# neighbor's gas hub vs Henry Hub (PNW Sumas/Stanfield discounts; desert-SW
# Permian/El-Paso ~ flat-to-premium). Tier 3 — verify against measured hub LMP
# means (MALIN 50.4/40.1/38.0, PALOVRDE 48.3/33.3/32.5 $/MWh 2023-25) and the
# posted WECC gas-hub bases.
@dataclass(frozen=True)
class CaisoHubNeighbor:
    """One CAISO WECC import corridor priced as a forward reference-price seam.

    The per-corridor analogue of :class:`NeighborInterface`, specialized to the
    two CAISO WECC ties. Every field is a forward driver or a physically-pinned
    structural constant — none is tuned to CAISO's net-interchange flow or to
    the measured hub LMP (CLAUDE.md #10/#11).

    Attributes:
        zone: The per-hub corridor zone (``WECC_PNW`` / ``WECC_DSW``).
        hub: The measured WECC scheduling-point hub the corridor proxies
            (``MALIN`` / ``PALOVRDE``) — used only to label the corridor and to
            line up the backcast validation, never read into the forward price.
        gas_basis: $/MMBtu basis of the neighbor's gas hub vs Henry Hub.
        marginal_heat_rate: MMBtu/MWh effective price-setting heat rate
            (gas × HR ≈ the hub's realized annual LMP); a 3-year-mean structural
            value, never a per-year measured anchor.
        load_shape_kind: ``"net"`` (load − solar − wind, the solar-driven
            desert-SW) or ``"gross"`` (load, the hydro-following Pacific-NW).
        load_shape_exponent: convexity of the price-vs-tightness response
            (1.0 = parameter-free mean-preserving linear shape).
        atc_base_fraction: forward ATC ceiling as a fraction of the corridor's
            physical TTC — the share of the path available for CAISO economy
            imports after firm reservations / parallel commitments (a posted-ATC
            capability ratio, NOT the measured p95 flow).
        atc_solar_floor: floor on the midday solar deliverability derate, so a
            fully-saturated midday corridor still delivers this fraction of its
            ATC ceiling.
    """

    zone: str
    hub: str
    gas_basis: float
    marginal_heat_rate: float
    load_shape_kind: str
    load_shape_exponent: float
    atc_base_fraction: float
    atc_solar_floor: float


# The two CAISO WECC corridors, keyed by per-hub zone. HR anchors: MALIN
# (Pacific-NW) ~16.0 reproduces the 3-year mean Malin LMP ($42.8) at the 3-year
# mean delivered gas ($2.75 − 0.30 PNW discount = $2.45 → 42.8/2.45 ≈ 17.5,
# trimmed to 16 for the dear-2025 gas-insensitivity); PALOVRDE (desert-SW) ~13.0
# reproduces the 3-year mean Palo Verde LMP ($38.0) at ($2.75 + 0.30 → $3.05 →
# 38/3.05 ≈ 12.5). The desert-SW shapes on NET load (signed: its midday trough
# rides the solar glut and the price approaches its cheap floor midday); the
# Pacific-NW shapes on gross load. ATC base fractions are posted-ATC capability
# ratios over the physical corridor TTC (COI 4,800 MW, Path-46/WOR 10,623 MW),
# NOT the measured p95: COI/Path-66 carries large firm Pacific-NW hydro contracts
# and the parallel PDCI, so only a small slice (~0.30) of its TTC is open to CAISO
# economy imports; Path-46/WOR has more economy headroom (~0.50). The solar derate
# (and its floor) shape the midday collapse off the region's forward solar, not
# the measured flow. These are capability judgments grounded in the corridors'
# firm-commitment structure (regenerable for a forward year, responsive to a TTC
# upgrade), never tuned to CAISO's net-import volume (CLAUDE.md #11/#12).
CAISO_PER_HUB_NEIGHBORS: dict[str, CaisoHubNeighbor] = {
    "WECC_PNW": CaisoHubNeighbor(
        zone="WECC_PNW",
        hub="MALIN",
        gas_basis=-0.30,  # PNW Sumas/Stanfield discount to Henry Hub
        marginal_heat_rate=16.0,
        load_shape_kind="gross",  # hydro-following; no solar midday trough
        load_shape_exponent=1.0,
        atc_base_fraction=0.30,  # COI economy-ATC slice (firm hydro + PDCI parallel)
        atc_solar_floor=0.30,
    ),
    "WECC_DSW": CaisoHubNeighbor(
        zone="WECC_DSW",
        hub="PALOVRDE",
        gas_basis=0.30,  # desert-SW Permian/El-Paso ~ flat-to-premium
        marginal_heat_rate=13.0,
        load_shape_kind="net",  # solar-driven; midday net-load trough
        load_shape_exponent=1.0,
        atc_base_fraction=0.50,
        atc_solar_floor=0.30,
    ),
}

# Strength of the midday solar deliverability derate: ATC(t) = TTC ×
# atc_base_fraction × clip(1 − k × solar_frac(t), atc_solar_floor, 1), where
# solar_frac(t) = CISO solar generation / CISO demand (a forward driver). k = 1.5
# collapses the corridor to its floor at ~47% midday solar penetration (the
# observed CISO midday share), reproducing the structural midday import collapse
# the measured p95 envelope carries — but indexed to forward solar, not the
# measured flow. Tier 3.
CAISO_CORRIDOR_ATC_SOLAR_K: float = 1.5

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

# --- ERCOT multi-product AS co-optimization (RTC+B) ------------------------
# ERCOT co-optimizes energy with FOUR upward ancillary-service products, each
# with its own procurement requirement and VOLL-anchored AS Demand Curve. Under
# RTC+B (live 2025-12-05) these clear inside SCED, so the binding product's
# reserve dual lifts the energy price endogenously — the forward analogue of the
# measured DAM-AS MCPC overlay (results.scarcity.ercot_dam_as_overlay_series).
# Each entry is (product name, ASPLANNP433 AncillaryType code, headroom tier),
# ordered highest response-quality first. The headroom TIER encodes the quality
# cascade (higher-quality substitutes down): "fast" products (Regulation-Up,
# Responsive Reserve, ERCOT Contingency Reserve) need synchronized/spinning
# headroom; "all" (Non-Spin) can additionally be met by a 30-minute offline
# quick-start unit, so it draws on the larger online+quick-start pool. The
# requirement is the ERCOT-published procurement quantity (ASPLANNP433),
# never fitted to a price; the demand-curve price is VOLL-anchored market design
# (the AS offer cap), so the scarcity INCIDENCE comes from the hourly responsive
# headroom in the shared-headroom RHS, not from any tuned per-product level.
# Source: ERCOT Nodal Protocols §6.4 (AS products & substitution cascade),
# NPRR1108/RTC+B AS Demand Curves, ASPLANNP433 (AS Plan) requirement reports.
ERCOT_AS_PRODUCTS: tuple[tuple[str, str, str], ...] = (
    ("RegUp", "REGUP", "fast"),
    ("RRS", "RRS", "fast"),
    ("ECRS", "ECRS", "fast"),
    ("NonSpin", "NSPIN", "all"),
)

# --- ERCOT forward AS requirement-setting methodology (G3) -----------------
# Per-product forward formulas req_product(t) = f(net-load, ramp, VRE-share,
# forecast-error quantile, largest-contingency / load-ratio share) — the forward
# analogue of reading the measured AS Plan (ASPLANNP433). They reproduce ERCOT's
# *published* AS Methodology drivers (NP3-160-CD "Methodology for Setting Day-Ahead
# and Real-Time Ancillary Service Requirements"): RegUp/RegDown from the net-load
# forecast-error distribution, RRS from the largest-contingency frequency-response
# floor plus a low-inertia adder, ECRS from the net-load ramp / forecast-error risk
# over its deployment window (the ~2 GW ramp-risk product, live 2023-06-10), and
# NonSpin from the longer-horizon net-load uncertainty (a load-ratio / net-load
# share). The scale coefficients are CALIBRATED to reproduce the published
# ASPLANNP433 *requirement MW* (the validation target — a procurement quantity,
# never a price; CLAUDE.md #12), so the formula is forward-reproducible (it
# regenerates for a forecast year from forecast net-load/VRE and grows as VRE
# penetration grows) while matching the measured level. Modeled-vs-measured
# validation: docs/ercot-as-forward-requirement-2026-06.md.
#
# Net-load day-ahead forecast-error standard deviation, combined in quadrature
# from independent load / wind / solar error sources:
#   sigma_fe(t) = sqrt((F_LOAD*load)^2 + (F_WIND*wind)^2 + (F_SOLAR*solar)^2)
# The component fractions are the published-order day-ahead error magnitudes
# (load ~1% of load; wind ~10% of output; solar ~18% of output — solar's relative
# DA error is the largest and dominates the VRE-driven growth in the requirement).
ERCOT_AS_FE_FRAC_LOAD: float = 0.01  # load DA forecast-error, frac of load MW
ERCOT_AS_FE_FRAC_WIND: float = 0.10  # wind DA forecast-error, frac of wind output
ERCOT_AS_FE_FRAC_SOLAR: float = 0.18  # solar DA forecast-error, frac of solar output

# RegUp = REGUP_FLOOR + REGUP_SIGMA_COEF * sigma_fe, clipped. Regulation covers the
# within-hour (sub-SCED) net-load variability — a small fraction of the hourly DA
# error — so the sigma coefficient is the sub-hourly slice of the DA error std.
ERCOT_AS_REGUP_FLOOR_MW: float = 275.0
ERCOT_AS_REGUP_SIGMA_COEF: float = 0.065
ERCOT_AS_REGUP_MIN_MW: float = 80.0
ERCOT_AS_REGUP_MAX_MW: float = 1100.0

# RRS = RRS_FLOOR + RRS_INERTIA_COEF * vre_share, clipped. The floor is the
# largest-contingency frequency-response requirement (~2300 MW, the two-largest-
# unit design basis); the adder grows with VRE share as synchronous inertia falls
# (low-inertia hours need more responsive reserve to arrest frequency).
ERCOT_AS_RRS_FLOOR_MW: float = 2300.0
ERCOT_AS_RRS_INERTIA_COEF_MW: float = 1160.0  # per unit VRE share (0-1)
ERCOT_AS_RRS_MAX_MW: float = 3300.0

# ECRS = ECRS_BASE + ECRS_SIGMA_COEF * sigma_fe + ECRS_RAMP_COEF * ramp_up,
# clipped. The ~2 GW ramp-risk product: net-load forecast-error plus the forward
# net-load up-ramp over its deployment window (ERCOT_AS_RAMP_WINDOW_HOURS), the
# solar-driven evening ramp it is designed to cover. Live 2023-06-10; the forward
# formula treats it as a permanent product (the onset is a backcast detail carried
# by the measured series).
ERCOT_AS_ECRS_BASE_MW: float = 950.0
ERCOT_AS_ECRS_SIGMA_COEF: float = 0.24
ERCOT_AS_ECRS_RAMP_COEF: float = 0.017
ERCOT_AS_ECRS_MIN_MW: float = 500.0
ERCOT_AS_ECRS_MAX_MW: float = 3300.0

# NonSpin = NSPIN_BASE + NSPIN_LOAD_COEF * load + NSPIN_RAMP_COEF * ramp_up,
# clipped. The longer-horizon net-load-uncertainty reserve (replaceable from
# offline quick-start capacity), sized as a LOAD-RATIO share of system load plus
# the forward net-load up-ramp it must cover — ERCOT's published Non-Spin driver
# (a load-ratio / net-load share). The load term carries the diurnal/seasonal
# shape (Non-Spin peaks with load, into the evening), the ramp term the
# evening-ramp risk.
ERCOT_AS_NSPIN_BASE_MW: float = 2475.0
ERCOT_AS_NSPIN_LOAD_COEF: float = 0.00418  # frac of load MW (load-ratio share)
ERCOT_AS_NSPIN_RAMP_COEF: float = 0.025  # per MW forward net-load up-ramp
ERCOT_AS_NSPIN_MIN_MW: float = 1400.0
ERCOT_AS_NSPIN_MAX_MW: float = 5700.0

# Forward net-load up-ramp deployment window (hours) the ECRS ramp term integrates
# over — the forward maximum net-load up-swing within this many hours of t, the
# horizon ECRS is sized to cover.
ERCOT_AS_RAMP_WINDOW_HOURS: int = 3

# --- ERCOT ORDC scarcity overlay ------------------------------------------
# Multi-step RTORPA price floor: (reserve threshold MW, floor $/MWh) steps.
# The adder is floored at $20/MWh when reserves <= 6,500 MW and at $10/MWh
# when 6,500 < reserves <= 7,000 MW. Source: OBDRR048, PUCT-approved
# 2023-10-12, effective 2023-11-01 (ERCOT market notice M-A101623-01);
# retired with the ORDC at RTC+B go-live (2025-12-05).
ORDC_FLOOR_STEPS: tuple[tuple[float, float], ...] = (
    (6500.0, 20.0),
    (7000.0, 10.0),
)
# First hour (non-leap hour-of-year index) of 2023-11-01, the OBDRR048
# effective date: Jan-Oct = 304 days.
ORDC_FLOOR_START_HOUR_2023: int = 304 * 24

# --- PJM Primary Reserve requirement (energy+reserve co-optimization) -------
# PJM sets the synchronized/primary reserve requirement from the Most-Severe
# Single Contingency (MSSC): PJM Manual 13 (Emergency Operations) / Manual 11
# sec 4.4. The Primary Reserve Requirement is held at ~1.5x the MSSC (the
# largest single resource/tie loss), the binding upward 10-minute product that
# nests Synchronized. Approximated in-model as factor x the fleet's Largest
# Single Contingency (the largest single dispatchable unit), giving a
# fleet-responsive, near-flat requirement: with the model's largest PJM unit
# this reproduces the measured PJM_RTO pr_req_mw (mean ~3.42 GW, 2024) — the
# honesty gate in tests/test_reserve_coopt.py, validated against
# data/raw/PJM-AS. Forecast-applicable: the MSSC moves with the fleet
# (retire the largest unit -> the requirement falls), unlike replaying the
# measured hourly series. The ORDC demand curve that PRICES a shortfall is the
# published two-step curve in data/raw/_validation-source/pjm_ordc_curve.csv.
PJM_PRIMARY_RESERVE_LSC_FACTOR: float = 1.5
PJM_ORDC_CURVE_PATH: str = str(CALIBRATION_DIR / "pjm_ordc_curve.csv")

# --- MISO market-wide operating-reserve demand curve (energy+reserve co-opt) -
# MISO co-optimizes energy with its market-wide operating reserves (Regulating +
# Contingency = Spinning + Supplemental) against a VOLL-anchored Reliability-Based
# Demand Curve (RBDC). When cleared market-wide reserves fall below the
# requirement, the demand curve sets the reserve clearing price, and through
# energy/reserve co-optimization that shadow price flows into the LMP — the
# scarcity tail a perfect-foresight energy-only LP cannot produce. This is the
# MISO analogue of the PJM ORDC / NYISO RCPF co-optimization
# (:func:`market_sim.results.scarcity.miso_reserve_coopt_inputs`); a single
# market-wide reserve family (footprint-wide clearing, like PJM's RTO-wide),
# not locational. Nothing here is fitted to the LMP residual.
#
# Requirement basis (MISO BPM-002 "Energy and Operating Reserve Markets" /
# Schedule 28): the Market-Wide Reserve Requirement = Regulating Reserve +
# Contingency Reserve, where the Contingency Reserve Requirement is the Most
# Severe Single Contingency (MSSC) — the largest single resource whose loss must
# be covered. The MSSC is fleet-derived
# (:func:`scarcity.largest_single_contingency_mw`), so the requirement responds
# to the fleet (retire the largest plant and it falls) and is forecast-valid,
# not a replay of a measured series. The regulation component is a near-constant
# footprint quantity.
MISO_REGULATING_RESERVE_MW: float = 400.0  # Market-wide regulating-reserve
# procurement, MW. MISO procures ~300–500 MW of Regulation footprint-wide
# (Regulating Reserve, MISO BPM-002 §4 / Schedule 28). Tier-3 (calibration):
# documented estimate, verify against the posted MISO market-wide regulation
# requirement; the MSSC contingency term dominates the requirement.
MISO_RESERVE_DEMAND_CURVE_MAX: float = 3500.0  # $/MWh. Maximum market-wide
# reserve shadow price = MISO's Value of Lost Load proxy, the anchor of MISO's
# Reliability-Based Demand Curve for operating reserves (MISO Schedule 28-A;
# VOLL-anchored RBDC, eff. ~2022). Tier-3 (calibration): verify the exact posted
# stepped breakpoints; the curve is linearised between sourced anchors below.
MISO_RESERVE_DEMAND_CURVE_CRITICAL_MW: float = 0.0  # Reserve level (MW) at/below
# which the maximum penalty applies. 0 → the demand curve ramps linearly from $0
# at the requirement to MISO_RESERVE_DEMAND_CURVE_MAX at zero cleared reserve —
# the documented piecewise-linear stand-in for the posted stepped curve, the
# same convention as the NYISO/NEISO demand curves (NYISO_RCPF_PRODUCTS).

# --- NYISO RCPF (Reserve Constraint Penalty Factor) scarcity overlay -------
# NYISO does not use an ERCOT-style ORDC/LOLP curve. Real-time scarcity is
# priced by the Reserve Constraint Penalty Factors: when dispatchable
# headroom falls below an operating-reserve requirement, the reserve
# demand curve sets the reserve clearing price, and that shadow price
# enters the LBMP through energy/reserve co-optimization. The products are
# nested (spinning subset of 10-minute-total subset of 30-minute-total), so
# in a deepening shortage the penalties STACK into the energy price — which
# is how NYISO RT LMP reaches the high-hundreds/low-thousands ($1,147/MWh
# max in 2023) off a ~$2,000 energy offer cap.
#
# Each product is (name, requirement_mw, critical_mw, max_penalty_$/MWh):
#   * requirement_mw — reserve target; the curve is $0 at or above it.
#   * critical_mw    — reserve level at/below which the maximum penalty
#                      applies; the curve ramps linearly from $0 at
#                      requirement_mw to max_penalty at critical_mw (a
#                      piecewise-linear stand-in for the published stepped
#                      demand curve — the anchors are sourced, the slope
#                      between them is linearised pending the full tariff
#                      step table; nothing here is fitted to LMP residuals).
#   * max_penalty    — the maximum allowable reserve shadow price ($/MWh).
#
# Requirements: NYISO sets 10-min spinning = 1/2 largest contingency,
# 10-min total = largest contingency, 30-min total = 2x largest
# contingency. Largest single contingency ~1,310 MW (NYISO Transmission &
# Dispatch Operations Manual; 2025 value) -> 655 / 1,310 / 2,620 MW.
# 30-min demand curve: $750/MWh maximum shadow price, applied at/below the
# 1,965 MW critical level, nine-step downward-sloping over the top 655 MW
# (FERC Docket ER21-502, eff. 2021; NYISO MST Rate Schedule 4). The
# 10-minute products carry the higher value of faster response; their
# maxima are the published RS4 ceilings ($750 non-sync, $775 spinning) and
# ramp from the requirement (no published intermediate breakpoint -> linear
# to zero reserve). Locational reserves (East F-K 1,200 MW, SENY $500/MWh,
# NYC, Long Island) are NOT here: they need per-zone headroom, which lands
# with the zonal-congestion fix; this system-wide NYCA overlay matches the
# NYCA-hub RT price the backcast reports.
NYISO_RCPF_PRODUCTS: tuple[tuple[str, float, float, float], ...] = (
    ("nyca_30min_total", 2620.0, 1965.0, 750.0),
    ("nyca_10min_total", 1310.0, 0.0, 750.0),
    ("nyca_10min_spin", 655.0, 0.0, 775.0),
)

# --- NYISO locational (zonal) RCPF reserve products ------------------------
# NYISO's reserve market is LOCATIONAL: nested reserve regions (NYCA ⊃ East ⊃
# SENY ⊃ NYC) each carry their own reserve requirement and demand curve, so a
# downstate shortage stacks region penalties into the *zonal* LBMP even when
# the system as a whole is long on reserves. This is why the system-wide
# NYCA overlay (NYISO_RCPF_PRODUCTS above) fires $0 in the backcast's tightest
# hours — measured NYCA-wide headroom never nears 2,620 MW — while the
# measured per-zone reserve price cascades from upstate to New York City
# (process_nyiso_as.py: WEST stacked RT reserve mean $2.20 → N.Y.C. $6.37,
# max $2,448). The downstate scarcity is real but locational, set by the
# reserve shortage *inside* the import-constrained NYC/SENY load pocket, not
# by a NYCA-wide shortfall.
#
# Each region maps to the model zones physically inside it (the five-zone
# topology in iso_configs._nyiso_config). The region's reserve headroom is
# the sum of those zones' dispatchable headroom; a model zone's locational
# adder is the sum of the demand-curve prices of every region that contains
# it. This reproduces the measured cascade tiers (per-zone RT reserve price,
# scripts/process_nyiso_as.py): zones A–E see the NYCA component only; zone F
# adds East; zones G–K add SENY; zone J adds NYC. The NYCA (system-wide) tier
# stays in NYISO_RCPF_PRODUCTS and is applied to every zone on top of these.
#
# Each region: member model zones + a product table with the same
# (name, requirement_mw, critical_mw, max_penalty_$/MWh) convention and
# piecewise-linear demand curve as NYISO_RCPF_PRODUCTS.
#   * East — NYISO requires 1,200 MW of 30-minute Reserves to be located east
#     of the Central-East interface (zones F–K); the 30-minute reserve demand
#     curve maximum is $500/MWh (FERC Docket ER21-502, the SENY/East 30-minute
#     uplift from $25 to $500/MW, eff. 2021; NYISO MST Rate Schedule 4).
#     Model zones F–K → Capital_Hudson, Lower_Hudson, NYC, Long_Island.
#   * NYC — NYISO procures 500 MW of 10-minute and 1,000 MW of 30-minute
#     Reserves within zone J (New York City); demand-curve maximum $500/MWh
#     (FERC ER21-502; NYISO MST RS4 / "Establishing Zone J Operating
#     Reserves"). Model zone J → NYC.
#   * SENY (zones G–K → Lower_Hudson, NYC, Long_Island) also carries a
#     30-minute requirement priced to a $500/MWh maximum (FERC ER21-502).
#     PLACEHOLDER requirement 1,100 MW: bracketed by the two *sourced* nested
#     tariff anchors East (F–K) 1,200 MW ⊇ SENY (G–K) ⊇ NYC (J) 1,000 MW, so
#     SENY ∈ [1,000, 1,200] MW; 1,100 is the midpoint. This is NOT yet the
#     tariff value — the modeled SENY-tier adder is validated against the
#     measured G–K reserve prices (process_nyiso_as.py), not fitted to them.
#     TODO(SENY-MW): replace 1,100 with the published Rate Schedule 4 SENY
#     30-minute requirement once sourced (pull NYISO MST RS4 / Potomac SOM).
#     SOURCING NOTE (2026-06): the primary docs carrying the exact SENY MW
#     (NYISO "Locational Reserve Requirements" PDF, Potomac NYISO SOM, the S&P
#     2019 SENY-launch article, NYISO MST RS4) are all PDF/binary or 403-gated
#     and would not render in the calibration container, so the exact figure
#     could not be pulled here. The nested bracket 1,000 (NYC J 30-min,
#     reconfirmed via NYISO MST) < SENY (G–K) < 1,200 (East F–K) still holds;
#     1,100 stays as the documented midpoint until a renderable source lands.
# critical_mw is 0 for every locational product (the demand curve ramps
# linearly from $0 at the requirement to the maximum penalty at zero
# reserves) — the documented stand-in for the published stepped curve, the
# same convention as the NYCA 10-minute products. Nothing here is fitted to
# LMP residuals; the model adder is validated against the measured per-zone
# RT reserve price (actual_as_reserve_NYISO.parquet).
NYISO_RCPF_LOCATIONAL: dict[str, dict] = {
    "East": {
        "zones": ("Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"),
        "products": (("east_30min_total", 1200.0, 0.0, 500.0),),
    },
    "SENY": {
        "zones": ("Lower_Hudson", "NYC", "Long_Island"),
        # PLACEHOLDER MW (1,100, bracket midpoint) — TODO(SENY-MW): source the
        # Rate Schedule 4 SENY 30-min requirement; penalty $500 is sourced.
        "products": (("seny_30min_total", 1100.0, 0.0, 500.0),),
    },
    "NYC": {
        "zones": ("NYC",),
        "products": (
            ("nyc_30min_total", 1000.0, 0.0, 500.0),
            ("nyc_10min_total", 500.0, 0.0, 500.0),
        ),
    },
}

# --- NEISO (ISO-NE) RCPF (Reserve Constraint Penalty Factor) scarcity overlay -
# ISO-NE, like NYISO and unlike ERCOT, prices real-time scarcity through
# Reserve Constraint Penalty Factors rather than an ORDC/LOLP curve. When
# dispatchable headroom falls below an operating-reserve requirement, the
# reserve-constraint penalty sets the reserve clearing price, and through
# energy/reserve co-optimization that shadow price flows into the LMP. The
# three products are nested (TMSR ⊂ total 10-minute ⊂ total 30-minute), so in
# a deepening shortage the penalties STACK into the energy price. ISO-NE is a
# capacity-market region (FCM), so in calm hours fixed cost is recovered
# through capacity, not energy — the overlay owns the price TAIL only and is
# $0 whenever reserves clear the requirement (the vast majority of backcast
# hours; this lever matters for forward/scarcity scenarios, not the calm
# 2023-25 backcast). Mirrors NYISO_RCPF_PRODUCTS; same post-solve, LP-untouched
# convention (results.rcpf / docs/nyiso-rcpf-overlay.md).
#
# Each product is (name, requirement_mw, critical_mw, max_penalty_$/MWh).
#
# Requirements (ISO-NE OP-8, "Operating Reserve and Regulation"):
#   * Total 10-minute reserve (TMSR + TMNSR) = the largest First Contingency.
#   * TMSR (ten-minute spinning)             = 1/2 of the First Contingency.
#   * Total 30-minute reserve (+ TMOR)       = First Contingency
#                                              + 1/2 of the Second Contingency.
# First/Second Contingency magnitude: ISO-NE's largest single contingencies
# are the big nuclear units / major imports (Millstone 3 ~1,205 MW, Seabrook
# ~1,245 MW). DOCUMENTED ESTIMATE 1,200 MW each pending the exact OP-8 posted
# values -> TMSR 600, 10-min-total 1,200, 30-min-total 1,800 MW.
# TODO(NE-contingency): replace 1,200 MW with the posted OP-8 First/Second
# Contingency once sourced; the magnitude is the only estimated input.
#
# Penalties (RCPF, ISO-NE Tariff Market Rule 1 / DA-AS settlement reference):
# TMSR $50/MWh, TMNSR (total 10-min) $1,500/MWh, TMOR (total 30-min)
# $1,000/MWh. These are SOURCED tariff values, not fitted. critical_mw = 0
# for every product (the demand curve ramps linearly from $0 at the
# requirement to the max penalty at zero reserves — the documented
# piecewise-linear stand-in for the posted stepped curve, the same convention
# as the NYISO 10-minute products). Local Reserve Zone (NEMA/Boston, CT, SWCT)
# second-contingency reserves carry a $250/MWh TMOR RCPF; like NYISO's
# locational tier they need per-zone headroom and are deferred to a locational
# follow-up — this system-wide overlay matches the pool RT price.
NEISO_RCPF_PRODUCTS: tuple[tuple[str, float, float, float], ...] = (
    ("ne_30min_total", 1800.0, 0.0, 1000.0),
    ("ne_10min_total", 1200.0, 0.0, 1500.0),
    ("ne_10min_spin", 600.0, 0.0, 50.0),
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
# the weather-year ensemble (market_sim.ensemble) draws over this whole pool and
# reports the distribution. Bounded by the hourly EIA-930 coverage on disk
# (data/raw/eia-930/, 2023-2025); extend as later years land. A weather draw is
# an admissible forecast *input*, not an outcome (CLAUDE.md #10), so sampling
# over it is methodological robustness, not a backcast pin.
WEATHER_YEAR_POOL: tuple[int, ...] = (2023, 2024, 2025)
