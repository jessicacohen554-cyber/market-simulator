"""Physical and economic constants with citation comments."""

from dataclasses import dataclass


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
# S5): replace when an independent merchant-CHP host-load source is found.
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

# Per-plant ERCOT CC_REGULAR peaking-tranche % (top slice of nameplate priced
# at the duct-burner peak multiplier), used in place of the generic offer
# curve's pct_peaking when ScenarioConfig.cc_peaking_per_plant is set — moves
# the peaking band earlier on the CF axis (15% => peaking starts at 85% of
# nameplate). Residual-identified, forecast-risk: applied to exactly the four
# F-class(late) 2x1 CCs the model over-ran in the 80-90% CF range (not a
# published or physically-measured turbine limit) — open root-cause item for
# the DOF ledger (S5).
CC_REGULAR_PEAKING_PCT_BY_PLANT: dict[int, float] = {
    58001: 15.0,  # Temple Power Station
    58005: 15.0,  # Rayburn Energy Station LLC
    59812: 15.0,  # Wolf Hollow II
    60122: 15.0,  # Colorado Bend II
}

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
CT_ECON_HR_OVERRIDE_DEFAULT: float = 1.1  # CT_CHP economic band ≈ 1.1× base HR
CT_PEAK_HR_OVERRIDE_DEFAULT: float = 1.3  # CT_CHP peak band ≈ 1.3× base HR

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
# available history. LOYO (plan §2.2): with a 3-year history the all-years
# gen-weighted average won (wMAPE 2.20% vs 2.28% simple / 2.46% recency);
# re-validated against the 7-year history before any narrower window is adopted.
CO2_RATE_TRAILING_WINDOW_YEARS: int = 0

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
CO2_RATE_CONDITIONING_ENABLED: bool = False

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
#
# scalar-remediation B-XISO-1 / audit C-18 (2026-07-05): the previous per-ISO
# values (ERCOT 0.85, CAISO 0.89, PJM 0.87, NYISO 0.86, NEISO 0.85) carried a
# "was 0.83"/"was 0.88" calibration-nudge trail and three "TODO: verify" tags
# under a bare "NERC GADS" label with no source on disk. Verified against
# NERC's actual public GADS product:
# data/raw/reference/nerc-gads-eford-2019-2023/ (Generating Unit Statistical
# Brochure 3, 2019-2023, "Units Reporting Events"; fetched 2026-07-05).
#
# That brochure is NERC-WIDE — it has no NERC-Region or ISO/RTO breakdown, so
# there is no published "ERCOT-fleet" / "CAISO-fleet" EFORd to verify the old
# per-ISO split against; those fleet-specific labels were never a real
# citation (rule-14 misalignment: the published data's boundary is NERC-wide,
# not per-ISO). Reconciled disposition per rule 14 (real data over a clean
# guess, boundary documented): use ONE NERC-wide figure for every ISO rather
# than inventing an unsupported per-ISO split. The published row is
# "FOSSIL Gas Primary, All Sizes" (CT+CC+gas-steam pooled by fuel — the
# closest published match to this constant's single "gas-fired generation"
# concept), EFORd = 13.44% -> availability = 1 - 0.1344 = 0.8656, rounded
# 0.866. Values below unified accordingly; all previous nudge-trail comments
# removed (CLAUDE.md rule 26 — no re-armable narrative).
#
# BOUNDARY / DOUBLE-COUNTING (rule-14 misalignment clause): this constant is
# NOT read anywhere in src/market_sim (grepped clean 2026-07-05) -- it is
# dead/orphaned, so today it cannot double-count with anything and changing
# its value has zero dispatch/MC effect. If it is ever wired into
# data.fleet.generators_to_fleet_arrays (or elsewhere) as a further derate on
# top of a generator's own `eford` (which already resolves via
# get_eford()/EFORD for generic units, or a CAMPD-derived capacity-weighted
# eford for per-plant bins -- both already NERC-GADS-sourced, see EFORD
# below), it MUST replace -- never multiply on top of -- that per-unit
# availability, or NERC's EFORd gets applied twice to the same gas fleet.
# Open root-cause issue (R2-vs-R5 disposition: wire in with a fleet-mix
# reconciliation vs. delete as dead code) — still open:
# https://github.com/jessicacohen554-cyber/market-simulator/issues/1349
GAS_AVAILABILITY_FACTOR: dict[str, float] = {
    "ERCOT": 0.866,  # NERC GADS 2019-2023, "FOSSIL Gas Primary, All Sizes"
    "CAISO": 0.866,  # (NERC-wide -- no per-ISO GADS breakdown exists, see
    "PJM": 0.866,  # module comment above). data/raw/reference/
    "NYISO": 0.866,  # nerc-gads-eford-2019-2023/nerc_gads_eford_2019-2023.csv
    "NEISO": 0.866,  # row "FOSSIL  Gas Primary       All Sizes": EFORd=13.44
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
    # CCS retrofit reuses the underlying gas_cc unit's forced-outage rate (the
    # amine/compression train adds parasitic load, not forced-outage risk, in
    # this model); supplies the class lookup used by model/capacity.py's
    # generic per-tech cost paths (was an inline ``.get(tech, 0.05)`` fallback).
    "gas_cc_ccs": 0.05,
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

# CAISO citygate -> burner-tip transport adder ($/MMBtu). The CAISO gas-hub
# overlay (gas_hub_basis_overlay) reprices each gas unit at the measured SoCal /
# PG&E Citygate spot (EIA N3050CA3 - Henry Hub, data/raw/gas_basis_by_iso_month.csv).
# That citygate is the price where the interstate pipe hands to the CA LDC; a
# power plant deep in the SoCalGas / PG&E system pays the citygate PLUS the LDC
# intrastate backbone + local transmission to its burner tip, so the plant's true
# delivered fuel cost (the cost-based DEB bid in CAISO's mitigated market) is the
# citygate + that transport. The adder is the MEASURED differential between the
# two EIA series: CA delivered-to-electric-power (N3045CA3, 2024 annual $3.98/Mcf
# = $3.84/MMBtu) minus the CA citygate (N3050CA3, 2024 $3.38/MMBtu) = +$0.46. It
# is a slow-moving regulated intrastate tariff (held flat across years like the
# basis differentials) and forward-reproducible (rule #11) — NOT tuned to the
# price or interchange residual. Without it the pure citygate under-prices the
# marginal CC to ~the import price and collapses the import knife-edge (the
# discovered caiso-38 under-import); reconciling up to the measured census level
# restores it. Source: EIA N3045CA3 - N3050CA3, 2024 annual.
CAISO_CITYGATE_TRANSPORT_ADDER: float = 0.46

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

# --- ERCOT lignite / PRB delivered coal cost, 2023-2025 -----------------------
# ERCOT's two coal supply classes are genuinely different costs: mine-mouth
# lignite (no transport, take-or-pay contract) vs PRB-by-rail (commodity +
# rail freight). Both are measured delivered-fuel-cost inputs — a physical/
# market input admissible under CLAUDE.md rule #13 (forward-reproducible,
# responds to changed conditions), not a fitted/residual value, despite the
# unhelpful "calibration" naming these constants used to carry.
#
# Mine-mouth lignite: held flat 2023-2025 (no transport cost to escalate),
# then compounds at COAL_PRICE_ESCALATION from 2026. Source: operator/EIA cost
# data.
LIGNITE_PRICE_2023_25: float = 1.45
# PRB-by-rail: measured delivered cost, 2023-2025 (EIA-923 Schedule-5 receipts
# / operator cost data). From 2026 the forward curve decomposes the 2023-2025
# average into commodity (42%), diesel-driven rail freight (12%, held flat —
# the model carries no forward diesel price curve) and non-diesel rail
# freight (46%, escalates at COAL_PRICE_ESCALATION); the commodity component
# holds flat through 2030 then declines 1.5%/yr as coal demand falls.
PRB_PRICE_BY_YEAR: dict[int, float] = {2023: 2.15, 2024: 2.00, 2025: 2.00}
PRB_COMMODITY_SHARE: float = 0.42
PRB_RAIL_DIESEL_SHARE: float = 0.12
PRB_RAIL_NONDIESEL_SHARE: float = 0.46
PRB_COMMODITY_DECLINE: float = 0.015  # annual, from 2031 as demand falls
PRB_COMMODITY_FLAT_THROUGH: int = 2030

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

# Per-plant ERCOT coal sustained-output ceilings (fraction of capacity_mw):
# the demonstrated physical maximum a unit's CEMS record shows it can sustain
# (boiler/turbine derates below nameplate), applied as an availability ceiling
# year-round on top of the age-based THERMAL_AVAILABILITY model.
#
# Source: scripts/derive_coal_max_cf.py — the pooled 99th percentile of each
# plant's daily-max capacity factor (gross_mw / capacity_mw) on days it ran
# (daily-mean CF > 0.06), across all CAMPD hourly extract years on record
# (2023-2025, data/raw/campd-facility-level/TX_*.parquet). A near-maximum
# rather than the true max: robust to a single-hour telemetry spike, not
# softened by economic part-load (which compresses the mean, not the top
# tail). Re-run the script and update this table when a new CAMPD year lands;
# never hand-tune an entry to a backcast residual (CLAUDE.md rule #22).
#
# Plants whose demonstrated ceiling reached or exceeded nameplate (Oak Grove
# 6180 p99=1.02, Coleto Creek 6178 p99=1.10, San Miguel 6183 p99=1.07) carry no
# entry: their own CEMS record shows no sub-nameplate physical limit, so the
# generic age-based availability model governs them unconstrained.
COAL_MAX_CF_BY_PLANT: dict[int, float] = {
    298: 0.95,  # Limestone
    6179: 0.99,  # Fayette (Sam Seymour)
    7097: 0.95,  # J K Spruce
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


# ---------------------------------------------------------------------------
# Cap-and-trade / mass-cap program registry
# ---------------------------------------------------------------------------
# The economy-wide, multi-sector, banked allowance markets (CARB, RGGI) enter
# dispatch as an *exogenous allowance-price adder* — measured in backcast,
# projected forward — not as an endogenous power-only cap, because their real
# clearing price is set by a banked multi-sector market this power model does
# not contain (docs/handoffs/emissions-mass-cap-plan-2026-07.md §2). The
# optional endogenous mass-cap *row* (dual = allowance price) faithfully
# represents a power-sector-specific budget (EPA 111(d)/CSAPR or a user
# scenario), NOT the RGGI/CARB market price. Both route carbon through the same
# emission_rate x membership channel; the resolver (policy/cap_and_trade.py)
# picks exactly one source per (program, ISO, year, solve).

# Forward-year allowance-price escalation rates (nominal, per year). The
# projected forecast adder anchors on the last realized clearing price
# (STATE_CARBON_PRICE_BY_ISO) and escalates at the program's published
# price-containment-band rate. This is an explicitly-labelled scenario
# trajectory (a floor-band escalator), NOT a market-price forecast, and it is
# never tuned to a residual (plan §7, §8; CLAUDE.md rule 1).
#
# CARB Auction Reserve (floor) price rises 5% + CPI annually (CA Cap-and-Trade
# Regulation, 17 CCR §95911(c)(1)); ~2%/yr CPI-U → ~7%/yr nominal. CA prices
# have hugged the floor+premium band, so the floor escalator is the natural
# forecast trajectory for CAISO.
CARB_FLOOR_ESCALATION: float = 0.07
# RGGI Cost Containment Reserve (CCR) trigger price rises 7%/yr nominal
# (RGGI 2017 Model Rule §5.3(c)); used as the forward escalation of the last
# realized RGGI clearing price for NYISO/NEISO.
RGGI_RESERVE_ESCALATION: float = 0.07


@dataclass(frozen=True)
class CapAndTradeProgram:
    """One ISO's cap-and-trade program definition (registry value).

    Attributes:
        name: Program label ("CARB" or "RGGI").
        member_states: Postal codes of the program's member states whose
            in-state fossil fleet surrenders allowances. Documentary /
            crosswalk reference; membership is resolved per zone below.
        price_key: Key into :data:`STATE_CARBON_PRICE_BY_ISO` for the
            measured backcast allowance price, and the anchor for the
            forecast projection. ``None`` for a program with no measured
            series in-repo (PJM).
        escalation_rate: Nominal per-year forward escalation applied to the
            last measured price to build the projected forecast adder.
        external_nodes: Zone names that are priced import/external nodes,
            not in-region load — excluded from membership (m_zone = 0).
        zone_share: Optional per-zone RGGI-member fraction (0..1) overriding
            the uniform-membership default, for multi-state roll-up zones
            (PJM). ``None`` → uniform membership (1.0 on every load zone).
    """

    name: str
    member_states: tuple[str, ...]
    price_key: str | None
    escalation_rate: float
    external_nodes: tuple[str, ...] = ()
    zone_share: "dict[str, float] | None" = None


# PJM's footprint straddles RGGI members (MD, DE, NJ; VA was a member through
# 2023 and exited 1 Jan 2024) and non-members (OH, IN, KY, WV, IL, most of PA),
# and its zones are multi-state roll-ups, so a clean 0/1 zone map is impossible
# (plan §5). The RGGI-member share of each zone's fossil capacity must come
# from an EIA-860 plant-coordinate → state → RGGI-membership-by-year crosswalk
# (a data-intake step, not yet landed). Until that crosswalk exists this map is
# empty, so PJM membership resolves to all-zeros and the PJM RGGI adder is a
# no-op (ships OFF, plan §5, §11). Populate per zone once the crosswalk lands.
PJM_RGGI_ZONE_SHARE: dict[str, float] = {}

# ISO → cap-and-trade program. ERCOT and MISO have no program (no entry).
CAP_AND_TRADE_PROGRAMS: dict[str, CapAndTradeProgram] = {
    # CAISO ≈ California: whole-ISO CARB membership; WECC_import is external.
    "CAISO": CapAndTradeProgram(
        name="CARB",
        member_states=("CA",),
        price_key="CAISO",
        escalation_rate=CARB_FLOOR_ESCALATION,
        external_nodes=("WECC_import",),
    ),
    # NYISO ≡ New York, a RGGI state: whole-ISO membership.
    "NYISO": CapAndTradeProgram(
        name="RGGI",
        member_states=("NY",),
        price_key="NYISO",
        escalation_rate=RGGI_RESERVE_ESCALATION,
    ),
    # NEISO ≡ the six New England states, all RGGI members: whole-ISO
    # membership; HQ_import (Hydro-Québec) is an external priced node.
    "NEISO": CapAndTradeProgram(
        name="RGGI",
        member_states=("CT", "ME", "MA", "NH", "RI", "VT"),
        price_key="NEISO",
        escalation_rate=RGGI_RESERVE_ESCALATION,
        external_nodes=("HQ_import",),
    ),
    # PJM: partial RGGI membership via fractional per-zone share (ships OFF
    # until the EIA-860→state crosswalk lands; PJM_RGGI_ZONE_SHARE empty).
    "PJM": CapAndTradeProgram(
        name="RGGI",
        member_states=("MD", "DE", "NJ"),
        price_key=None,
        escalation_rate=RGGI_RESERVE_ESCALATION,
        zone_share=PJM_RGGI_ZONE_SHARE,
    ),
}

# Short ton -> metric tonne. RGGI allowances are denominated in SHORT tons of
# CO2 (1 allowance = 1 short ton), but the model's internal emission-rate mass
# unit is the metric tonne (data/fleet.py: "the model's internal emission-rate
# mass unit"), so a RGGI budget must be converted before it becomes a mass-cap
# row RHS. 1 short ton = 907.18474 kg (NIST HB 44).
SHORT_TON_TO_METRIC_TONNE: float = 0.90718474

# Power-sector CO2 mass-cap budgets for the OPTIONAL endogenous mass-cap row
# (mass_cap_enabled, default OFF). These mirror the cited raw schedules under
# data/raw/policy/{carb-cap-schedule,rggi-co2-budgets}/ (curated to
# data/clean/ via scripts/curate_*.py; the clean tree is gitignored so the
# authoritative in-repo value lives here, same intake discipline as
# STATE_CARBON_PRICE_BY_ISO). A row built from a budget here is a power-sector,
# no-bank SCENARIO instrument (plan §2, §8) — NOT the RGGI/CARB market price,
# which is set by a banked, multi-sector market this power model does not
# contain (that faithful representation is the measured/projected adder above).
# Because these region-/economy-wide budgets vastly exceed any single modeled
# ISO's power-sector emissions, the row is (correctly) slack and its dual ~0 for
# a real ISO — the mechanism is validated on the trivial binding fixture
# (tests/test_dispatch.py::TestMassCapConstraint), not by binding here. NO 2022
# or H1-2026 rows (holdout quarantine, CLAUDE.md rule 22).

# California GHG annual allowance budget (MMT CO2e/yr; 1 CA GHG allowance = 1
# metric tonne CO2e). Declines per the Scoping Plan trajectory. This is the
# whole-economy CARB cap (electricity + industry + fuels), so a CAISO
# power-sector row against it is deeply slack.
# Source: CARB Cap-and-Trade Regulation, 17 CCR §95841 Table 6-2 (annual
# allowance budgets 2021-2031). 2022 and 2026 omitted (holdout quarantine).
CARB_ALLOWANCE_BUDGET: dict[int, float] = {
    2023: 294.1,
    2024: 280.7,
    2025: 267.4,
    2027: 240.6,
    2028: 227.3,
    2029: 213.9,
    2030: 200.5,
    2031: 193.8,
}
# CARB Auction Reserve (floor) price by year ($/tonne), rising 5% + CPI per
# §95911(c). Landed as the cited floor-band artifact; the CAISO forecast adder
# escalator lives in CARB_FLOOR_ESCALATION above.
# Source: CARB Annual Auction Reserve Price Notices, 2023-2025.
CARB_FLOOR_PRICE: dict[int, float] = {
    2023: 22.21,
    2024: 24.04,
    2025: 25.94,
}
# RGGI regional CO2 allowance budget (short tons/yr). Keyed by "RGGI" for the
# regional total; per-state budgets can be added under their postal codes once
# the RGGI per-state allowance-distribution table is intaken (until then a RGGI
# ISO's power-sector row uses the regional cap — an even looser over-bound, so
# still slack). 2023-2025 are the published regional cap; 2027-2030 project the
# 2021 Model Rule ~2.9%/yr decline (a labelled forward trajectory, not measured).
# Source: RGGI, Inc. regional cap trajectory (ICAP ETS profile); the 2023->2024
# step reflects Virginia's 1 Jan 2024 exit. 2022/2026 omitted (quarantine).
RGGI_STATE_CO2_BUDGET: dict[str, dict[int, float]] = {
    "RGGI": {
        2023: 93_000_000.0,
        2024: 69_000_000.0,
        2025: 67_000_000.0,
        2027: 63_200_000.0,
        2028: 61_400_000.0,
        2029: 59_600_000.0,
        2030: 57_900_000.0,
    },
}

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
# artifacts). The runner gate keys
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

# Per-tech capex + learning-rate multipliers for the PB-1 tech-cost
# uncertainty lever (ScenarioConfig.tech_cost_path / tech_cost_percentile,
# docs/handoffs/probability-bounds-plan-2026-07.md §1.1/§2.1), applied to
# NEW_ENTRY_COSTS by config.scenarios.resolve_new_entry_costs. Cases map to
# NREL ATB 2024 technology innovation scenarios: "low"=Advanced (full
# learning/cost-decline realized), "mid"=Moderate, "high"=Conservative
# (costs stay closer to flat). "mid" is 1.0 on every tech BY CONSTRUCTION --
# NEW_ENTRY_COSTS' base values are the model's existing reference case, not
# a re-scraped ATB Moderate figure, so the neutral default must be an exact
# no-op. The low/high spreads are engineering-judgment magnitudes anchored to
# ATB's published case *definitions* and typical per-tech spread ordering
# (solar/nuclear widest -- immature or FOAK cost curves; gas narrowest --
# mature, well-characterized plant costs); this environment could not reach
# atb.nrel.gov to pull the exact 2024 scraped case ratios, so a follow-up
# should replace these with exact figures the next time ATB is re-pulled
# (PP-3.2 item 2 tracks the next AEO/ATB refresh).
TECH_COST_MULTIPLIERS: dict[str, dict[str, dict[str, float]]] = {
    "wind": {
        "low": {"capex_per_kw": 0.85, "learning_rate": 1.35},
        "mid": {"capex_per_kw": 1.00, "learning_rate": 1.00},
        "high": {"capex_per_kw": 1.12, "learning_rate": 0.65},
    },
    "solar": {
        "low": {"capex_per_kw": 0.65, "learning_rate": 1.25},
        "mid": {"capex_per_kw": 1.00, "learning_rate": 1.00},
        "high": {"capex_per_kw": 1.15, "learning_rate": 0.60},
    },
    "gas_cc": {
        "low": {"capex_per_kw": 0.95, "learning_rate": 1.5},
        "mid": {"capex_per_kw": 1.00, "learning_rate": 1.0},
        "high": {"capex_per_kw": 1.08, "learning_rate": 0.5},
    },
    "gas_ct": {
        "low": {"capex_per_kw": 0.95, "learning_rate": 1.5},
        "mid": {"capex_per_kw": 1.00, "learning_rate": 1.0},
        "high": {"capex_per_kw": 1.08, "learning_rate": 0.5},
    },
    "nuclear_smr": {
        "low": {"capex_per_kw": 0.80, "learning_rate": 1.5},
        "mid": {"capex_per_kw": 1.00, "learning_rate": 1.0},
        "high": {"capex_per_kw": 1.25, "learning_rate": 0.5},
    },
    "nuclear_large": {
        "low": {"capex_per_kw": 0.90, "learning_rate": 1.5},
        "mid": {"capex_per_kw": 1.00, "learning_rate": 1.0},
        "high": {"capex_per_kw": 1.15, "learning_rate": 0.5},
    },
    "gas_cc_ccs": {
        "low": {"capex_per_kw": 0.85, "learning_rate": 1.5},
        "mid": {"capex_per_kw": 1.00, "learning_rate": 1.0},
        "high": {"capex_per_kw": 1.20, "learning_rate": 0.5},
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
# a direct Path-15 sub-TAC load measurement becomes available.
CAISO_TAC_ZONE_WEIGHTS: dict[str, dict[str, float]] = {
    "PGE-TAC": {"NP15": 0.86, "ZP26": 0.14},
    "SCE-TAC": {"SP15": 1.0},
    "SDGE-TAC": {"SP15": 1.0},
    "VEA-TAC": {"SP15": 1.0},
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
# constraint from the committed LCR table), tracked in issue #1345; until then
# the value is LEFT at 0.45 (residual-identified, forecast-risk; DOF ledger S5)
# rather than replaced by a knowingly-wrong LCR substitution. The 0.45 magnitude
# still approximates the 2023 realized LI self-supply share (~0.48) — it is NOT
# a validated forward driver and MUST NOT be quoted as one. NYC (zone J) is
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
#   - ComEd→AEP_Ohio    ← "50045005 Post-Contingency"  (median 2900; config 6000
#                          was the loose one the diagnosis flagged)
#   - AEP_Ohio→Dominion ← "AEP/DOM Post-Contingency"   (median 4054; ≈ config 4069)
#   - West_APS→SWMAAC   ← "AP-South Pre-Contingency"   (median 3932; the dominant
#                          west→east cut — config 4453)
#   - West_APS→Central_PA ← "Bedington-BlackOak"       (median ~1850; config 1947)
PJM_MEASURED_INTERNAL_TTC: dict[tuple[str, str], float] = {
    ("PJM_ComEd", "PJM_AEP_Ohio"): 2900.0,
    ("PJM_AEP_Ohio", "PJM_Dominion"): 4050.0,
    ("PJM_West_APS", "PJM_SWMAAC"): 3900.0,
    ("PJM_West_APS", "PJM_Central_PA"): 1850.0,
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
# Source: ERCOT NP6-86-CD archives via scripts/derive_ttc_limits.py; ERCOT
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
# the weather-year ensemble (market_sim.ensemble) draws over this whole pool and
# reports the distribution. Bounded by the hourly EIA-930 coverage on disk
# (data/raw/eia-930/, 2023-2025); extend as later years land. A weather draw is
# an admissible forecast *input*, not an outcome (CLAUDE.md #10), so sampling
# over it is methodological robustness, not a backcast pin.
WEATHER_YEAR_POOL: tuple[int, ...] = (2023, 2024, 2025)


# ---------------------------------------------------------------------------
# ERCOT forward RTOLCAP/RTOFFCAP online-responsive reserve-supply shares (WS-A)
# ---------------------------------------------------------------------------
# Forward analogue of the measured ERCOT on-line responsive reserve-supply cap
# (scarcity.ercot_rtolcap_supply_cap_mw, which returns None for years with no
# measured ercot_<year>_ordc_reserves_hourly.parquet -> forecast years ran
# UNCAPPED). Derived by scripts/derive_ercot_rtolcap_forward.py from the committed
# CAMPD unit extracts + the measured RTOLCAP/RTOFFCAP MW QUANTITY series (never a
# price; honesty gate). RE-DERIVE ONLY on a source-data update (rule #23), never a
# residual. online_share_c = median over CAMPD of the class on-line headroom-
# realization fraction Sigma_online(eff_cap-gross)/installed_cap, conditioned on
# (season, net-load percentile decile); offline_share_c the OFF-line startable
# quick-start analogue for RTOFFCAP. Season 0=winter(DJF) 1=spring(MAM)
# 2=summer(JJA) 3=fall(SON); inner tuples are the 10 net-load deciles (low->high).
ERCOT_RTOLCAP_FWD_N_SEASON: int = 4
ERCOT_RTOLCAP_FWD_N_DECILE: int = 10
# Season index by calendar month (Jan..Dec).
ERCOT_RTOLCAP_FWD_SEASON_BY_MONTH: tuple[int, ...] = (
    0,
    0,
    1,
    1,
    1,
    2,
    2,
    2,
    3,
    3,
    3,
    0,
)
# Reserve-eligible thermal classes forming on-line RTOLCAP.
ERCOT_RTOLCAP_FWD_ONLINE_CLASSES: tuple[str, ...] = (
    "COAL",
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
)
# Quick-start classes forming off-line RTOFFCAP.
ERCOT_RTOLCAP_FWD_OFFLINE_CLASSES: tuple[str, ...] = (
    "CT_PEAKER",
    "CT_CHP",
)
ERCOT_RTOLCAP_FWD_ONLINE_SHARE: dict[str, tuple[tuple[float, ...], ...]] = {
    "COAL": (
        (
            0.6087,
            0.5673,
            0.5217,
            0.4914,
            0.4492,
            0.3962,
            0.3451,
            0.2969,
            0.2672,
            0.1623,
        ),
        (
            0.5900,
            0.5421,
            0.5146,
            0.4685,
            0.4163,
            0.3816,
            0.3569,
            0.3401,
            0.2811,
            0.2345,
        ),
        (
            0.6055,
            0.5418,
            0.5257,
            0.5132,
            0.5045,
            0.4611,
            0.4092,
            0.3460,
            0.2533,
            0.1859,
        ),
        (
            0.5879,
            0.5189,
            0.5099,
            0.4622,
            0.4179,
            0.3796,
            0.3352,
            0.2844,
            0.2257,
            0.1570,
        ),
    ),
    "CC_REGULAR": (
        (
            0.2377,
            0.2455,
            0.2395,
            0.2318,
            0.2118,
            0.1871,
            0.1612,
            0.1444,
            0.1366,
            0.1080,
        ),
        (
            0.2207,
            0.2677,
            0.2644,
            0.2462,
            0.2254,
            0.2142,
            0.2028,
            0.1946,
            0.1819,
            0.1392,
        ),
        (
            0.2674,
            0.2970,
            0.2736,
            0.2266,
            0.1972,
            0.1710,
            0.1410,
            0.1168,
            0.0941,
            0.0716,
        ),
        (
            0.2526,
            0.2568,
            0.2544,
            0.2342,
            0.2041,
            0.1846,
            0.1654,
            0.1436,
            0.1106,
            0.0758,
        ),
    ),
    "CC_CHP": (
        (
            0.3000,
            0.2435,
            0.2043,
            0.1719,
            0.1480,
            0.1311,
            0.1148,
            0.0979,
            0.0906,
            0.0675,
        ),
        (
            0.2817,
            0.2435,
            0.2173,
            0.1989,
            0.1814,
            0.1728,
            0.1592,
            0.1553,
            0.1364,
            0.1069,
        ),
        (
            0.1860,
            0.1720,
            0.1482,
            0.1250,
            0.1199,
            0.1070,
            0.0963,
            0.0774,
            0.0680,
            0.0609,
        ),
        (
            0.2869,
            0.2554,
            0.2352,
            0.2055,
            0.1772,
            0.1588,
            0.1382,
            0.0967,
            0.0719,
            0.0622,
        ),
    ),
    "CT_PEAKER": (
        (
            0.0137,
            0.0141,
            0.0217,
            0.0204,
            0.0315,
            0.0419,
            0.0650,
            0.1139,
            0.1351,
            0.1470,
        ),
        (
            0.0327,
            0.0447,
            0.0504,
            0.0616,
            0.0971,
            0.1063,
            0.1549,
            0.1850,
            0.2400,
            0.2390,
        ),
        (
            0.0269,
            0.0304,
            0.0242,
            0.0108,
            0.0148,
            0.0170,
            0.0222,
            0.0345,
            0.0910,
            0.1078,
        ),
        (
            0.0358,
            0.0387,
            0.0408,
            0.0426,
            0.0429,
            0.0510,
            0.0479,
            0.0444,
            0.1172,
            0.1291,
        ),
    ),
    "CT_CHP": (
        (
            0.0445,
            0.0347,
            0.0330,
            0.0263,
            0.0247,
            0.0205,
            0.0233,
            0.0171,
            0.0162,
            0.0392,
        ),
        (
            0.0506,
            0.0537,
            0.0695,
            0.0755,
            0.0731,
            0.0795,
            0.0837,
            0.0823,
            0.0815,
            0.0628,
        ),
        (
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0108,
        ),
        (
            0.0328,
            0.0352,
            0.0445,
            0.0390,
            0.0268,
            0.0238,
            0.0205,
            0.0200,
            0.0187,
            0.0152,
        ),
    ),
    "ST_GAS": (
        (
            0.0211,
            0.0211,
            0.0472,
            0.0851,
            0.1002,
            0.1045,
            0.1192,
            0.1786,
            0.2943,
            0.3536,
        ),
        (
            0.1291,
            0.1828,
            0.2495,
            0.2772,
            0.3017,
            0.3298,
            0.3312,
            0.3591,
            0.3656,
            0.3174,
        ),
        (
            0.1456,
            0.2235,
            0.3094,
            0.3514,
            0.4091,
            0.4522,
            0.4999,
            0.5172,
            0.4480,
            0.3125,
        ),
        (
            0.2351,
            0.2659,
            0.2879,
            0.2967,
            0.3575,
            0.3883,
            0.4042,
            0.4458,
            0.4345,
            0.3385,
        ),
    ),
    "ST_CHP": (
        (
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
        ),
        (
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
        ),
        (
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
        ),
        (
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
        ),
    ),
}
ERCOT_RTOLCAP_FWD_OFFLINE_SHARE: dict[str, tuple[tuple[float, ...], ...]] = {
    "CT_PEAKER": (
        (
            0.9493,
            0.9493,
            0.9307,
            0.9303,
            0.9055,
            0.8759,
            0.8433,
            0.7684,
            0.6426,
            0.5343,
        ),
        (
            0.9266,
            0.9031,
            0.8815,
            0.8522,
            0.7953,
            0.7392,
            0.6000,
            0.5641,
            0.4546,
            0.2869,
        ),
        (
            0.8100,
            0.7923,
            0.8132,
            0.8307,
            0.8076,
            0.7923,
            0.7923,
            0.7569,
            0.6400,
            0.3676,
        ),
        (
            0.9256,
            0.9031,
            0.9031,
            0.8570,
            0.8307,
            0.7903,
            0.7713,
            0.7688,
            0.6208,
            0.3611,
        ),
    ),
    "CT_CHP": (
        (
            0.6759,
            0.6578,
            0.6578,
            0.6578,
            0.6578,
            0.6578,
            0.6578,
            0.6578,
            0.6302,
            0.6302,
        ),
        (
            0.6759,
            0.6759,
            0.6759,
            0.6759,
            0.6759,
            0.6759,
            0.6759,
            0.6759,
            0.6497,
            0.6497,
        ),
        (
            0.5685,
            0.5685,
            0.5685,
            0.5756,
            0.5756,
            0.5756,
            0.5756,
            0.5756,
            0.5756,
            0.5514,
        ),
        (
            0.6578,
            0.6578,
            0.6578,
            0.6497,
            0.6302,
            0.6302,
            0.6011,
            0.5831,
            0.5756,
            0.5514,
        ),
    ),
}
# Deliverability coefficient: fit to the measured RTOLCAP MW quantity (pooled
# 2023-2025 LS), centering the forward level (like G3 ASPLANNP433). Not a price.
ERCOT_RTOLCAP_FWD_DELIV_COEF: float = 0.8899
# Off-line deliverability coefficient: fit to the measured RTOFFCAP MW quantity
# (off-line startable quick-start capacity clears a smaller reserve fraction than
# the on-line fit). Not a price.
ERCOT_RTOLCAP_FWD_OFFLINE_DELIV_COEF: float = 0.7748
# Forward on-line storage responsive-reserve fraction of installed storage power
# (ERCOT observed AS-award / installed-storage ~0.35 across 2023-2025). FORECAST
# only; in backcast the storage term reads the measured storage-AS series
# (mode-aware, like the G4 load-resource credit).
ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC: float = 0.35
