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
HYDRO_CLIMATOLOGY_YEARS: tuple[int, ...] = (2021, 2022, 2023, 2024, 2025)

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

# --- Data-center load block (CX-4, gap G-34) ------------------------------
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
    # MISO / NEISO — no published DC decomposition located (memo §2.2); ship {}
    # => 0 MW every path/year until a primary source is read (a pure data-intake
    # follow-up, no fitted placeholder). The near-term DEMAND_GROWTH_RATES still
    # carry their DC boom implicitly until then.
    "MISO": {},
    "NEISO": {},
}

# Per-ISO override of the data-center block's zonal allocation, {iso: {zone:
# share}} summing to 1.0 per ISO (memo §3.3). DEFAULT (ISO absent here) = each
# zone's iso_configs load_share, applied by data.datacenter.datacenter_zone_shares.
# Override ONLY where published queue siting geography differs from the load
# distribution (memo names ERCOT North/West and PJM Dominion skews). Ships EMPTY:
# no published per-zone DC siting fractions are yet sourced, so every ISO uses its
# load_share default; adding a documented siting split is a data-intake follow-up.
DATACENTER_ZONE_SHARE: dict[str, dict[str, float]] = {}

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
# RE-DERIVED 2026-07 (P-1D, CLAUDE.md rule 23) from the actual AEO2025 Table
# 13 data (data/raw/eia-aeo/eia_aeo2025_fuel_prices.part*.csv, API-fetched by
# scripts/fetch_eia_aeo.py in the P-0C intake), replacing the prior
# hand-typed "approximate interpolations from published AEO2025 charts and
# text" this TODO used to flag. Re-derive with
# scripts/derive_fuel_trajectories.py::derive_gas_trajectory and paste; see
# docs/handoffs/aeo-verification-2026-07-11.md for the before/after diff.
# AEO2026 was released April 8, 2026 and may carry updated trajectories —
# re-run scripts/fetch_eia_aeo.py --aeo-year 2026 when that vintage is wanted.
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
        2026: 2.11,
        2027: 2.03,
        2028: 2.14,
        2029: 2.21,
        2030: 2.32,
        2031: 2.42,
        2032: 2.68,
        2033: 2.76,
        2034: 2.79,
        2035: 2.81,
        2036: 2.82,
        2037: 2.79,
        2038: 2.78,
        2039: 2.79,
        2040: 2.84,
        2041: 2.89,
        2042: 2.92,
        2043: 2.91,
        2044: 2.88,
        2045: 2.89,
        2046: 2.92,
        2047: 2.90,
        2048: 2.89,
        2049: 2.86,
        2050: 2.83,
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
        2026: 2.74,
        2027: 2.62,
        2028: 2.73,
        2029: 2.89,
        2030: 3.08,
        2031: 3.23,
        2032: 3.70,
        2033: 4.10,
        2034: 4.34,
        2035: 4.43,
        2036: 4.42,
        2037: 4.37,
        2038: 4.31,
        2039: 4.24,
        2040: 4.27,
        2041: 4.34,
        2042: 4.42,
        2043: 4.56,
        2044: 4.64,
        2045: 4.70,
        2046: 4.78,
        2047: 4.83,
        2048: 4.83,
        2049: 4.81,
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
        2026: 4.07,
        2027: 4.12,
        2028: 4.44,
        2029: 4.94,
        2030: 5.90,
        2031: 6.58,
        2032: 7.28,
        2033: 7.63,
        2034: 7.84,
        2035: 8.02,
        2036: 8.32,
        2037: 8.40,
        2038: 8.31,
        2039: 8.47,
        2040: 8.50,
        2041: 8.55,
        2042: 8.50,
        2043: 8.36,
        2044: 8.55,
        2045: 8.59,
        2046: 8.69,
        2047: 8.97,
        2048: 9.25,
        2049: 9.50,
        2050: 9.75,
    },
    # --- Capacity-hindcast gas paths (W2-P5, plan §1.2) --------------------
    # "hindcast_realized": the year's ACTUAL Henry Hub spot annual average
    # ($/MMBtu), the realized-fuel variant of the capacity hindcast. Values are
    # the annual mean of data/raw/gas-prices/henry_hub_monthly.csv (EIA Henry
    # Hub spot), matching the historical entries already carried in the low/mid/
    # high paths above (2023: 2.54, 2024: 2.19, 2025: 3.53). 2022 is DELIBERATELY
    # omitted (rule 22 quarantine bridge — the hindcast never solves or reads
    # 2022, and its 2022 evolution step draws the 2021 value via driver_year).
    "hindcast_realized": {
        2021: 3.91,  # EIA Henry Hub spot annual mean (henry_hub_monthly.csv)
        2023: 2.54,
        2024: 2.19,
        2025: 3.53,
    },
    # "hindcast_asknown_aeo2021": the AEO2021 Reference case Henry Hub
    # trajectory (EIA, Annual Energy Outlook 2021, published Feb 2021 — the
    # contemporaneous as-known-then forecast for a 2021-start hindcast). The
    # realized−asknown gap isolates fuel-input (gas-forecast) error from
    # capacity-path error (plan §1.4 baseline (c)). 2022 omitted per the bridge.
    # Source: AEO2021 Reference, Table "Henry Hub spot price" (2020$ ≈ 2026$ at
    # this precision; the level is only a sensitivity axis, not a keeper input).
    "hindcast_asknown_aeo2021": {
        2021: 3.07,
        2023: 2.86,
        2024: 2.88,
        2025: 2.93,
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

# Annual real escalation rate for coal prices — retained as the DEFAULT
# forward shape only where no AEO year is available (before START_YEAR, or a
# horizon extension beyond COAL_PRICE_TRAJECTORIES' last year is handled by
# the flat hold, not this rate). Reflects mine closures, rising rail transport
# costs, and declining domestic demand reducing economies of scale.
# Source: EIA AEO 2024 coal supply module — ~1% real escalation.
COAL_PRICE_ESCALATION: float = 0.01

# --- National delivered coal-price trajectories (real 2024$/MMBtu) ---
# AEO2025 Table 15 ("Coal Supply, Disposition, and Prices"), delivered to the
# electric power sector, national ("usa") — data/raw/eia-aeo/
# eia_aeo2025_fuel_prices.part*.csv, derived via
# scripts/derive_fuel_trajectories.py::derive_coal_trajectory (P-1D, CLAUDE.md
# rule 23 — resolves the D2 gap: "coal flat 1%/yr escalation" with no AEO
# grounding). Replaces the flat COAL_PRICE_ESCALATION forward SHAPE — each
# ISO's own COAL_PRICE_BASE level anchor is unchanged (a single national
# series can't resolve ERCOT lignite vs PJM Appalachian vs MISO PRB+ILB basin
# economics, the CLAUDE.md rule-14 misalignment exception), but the year-over-
# year real growth now tracks the AEO's modeled coal-supply dynamics instead
# of a guessed constant rate. Scenario mapping matches
# HENRY_HUB_TRAJECTORIES: highogs -> "low", ref2025 -> "mid", lowogs -> "high"
# (AEO's High/Low Oil and Gas Supply cases also vary coal-sector fuel
# competition and mining diesel costs, so the same axis is reused rather than
# inventing an independent coal scenario lever). Selected via
# ``ScenarioConfig.coal_price_path`` (default "mid").
COAL_PRICE_TRAJECTORIES: dict[str, dict[int, float]] = {
    "low": {
        2024: 2.4892,
        2025: 2.4487,
        2026: 2.3346,
        2027: 2.2747,
        2028: 2.1624,
        2029: 2.1008,
        2030: 2.1363,
        2031: 2.0803,
        2032: 1.9438,
        2033: 1.9227,
        2034: 1.9102,
        2035: 1.8753,
        2036: 1.9415,
        2037: 1.7727,
        2038: 1.7835,
        2039: 1.6129,
        2040: 1.6268,
        2041: 1.6452,
        2042: 1.6734,
        2043: 1.6889,
        2044: 1.6997,
        2045: 1.7125,
        2046: 1.7257,
        2047: 2.5028,
        2048: 2.5050,
        2049: 2.5103,
        2050: 2.5186,
    },
    "mid": {
        2024: 2.4894,
        2025: 2.4296,
        2026: 2.3760,
        2027: 2.3295,
        2028: 2.2352,
        2029: 2.2066,
        2030: 2.2390,
        2031: 2.1980,
        2032: 1.9780,
        2033: 1.9591,
        2034: 1.9663,
        2035: 1.9590,
        2036: 1.9698,
        2037: 1.9409,
        2038: 1.9523,
        2039: 2.0667,
        2040: 2.0647,
        2041: 2.0645,
        2042: 2.0657,
        2043: 2.0720,
        2044: 2.0491,
        2045: 2.0574,
        2046: 1.8790,
        2047: 2.3516,
        2048: 2.3543,
        2049: 2.3533,
        2050: 2.3608,
    },
    "high": {
        2024: 2.4888,
        2025: 2.4729,
        2026: 2.5108,
        2027: 2.4361,
        2028: 2.3718,
        2029: 2.3786,
        2030: 2.4118,
        2031: 2.3955,
        2032: 2.2343,
        2033: 2.2295,
        2034: 2.2286,
        2035: 2.2222,
        2036: 2.2280,
        2037: 2.2003,
        2038: 2.1834,
        2039: 2.1566,
        2040: 2.1498,
        2041: 2.1658,
        2042: 2.1537,
        2043: 2.1320,
        2044: 2.0534,
        2045: 2.0908,
        2046: 2.0391,
        2047: 2.1600,
        2048: 2.1896,
        2049: 2.1906,
        2050: 2.1325,
    },
}

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

# --- Coal-vs-gas passthrough sigmoid re-derivation inputs ---------------------
# Physical/measured inputs that ``scripts/derive_coal_sigmoid.py`` reads to
# re-derive the per-(ISO, supply) gas-keyed coal passthrough sigmoid
# (``COAL_SIGMOID_DEFAULTS`` in scenarios.py) from the EIA Annual Coal Report
# region f.o.b.-mine price + BLS PPI coal-mining series intaked in #1803
# (data/raw/coal-prices/, docs/handoffs/coal-price-data-intake-2026-07.md).
# These are grounded commodity/heat/transport facts — NOT tuned to any ISO's
# price/volume residual (CLAUDE.md rules 10/11/23). See the derive script's
# module docstring for how each feeds the floor/ceil/gas_mid/gas_slope fit.
#
# Approximate heat content of coal by rank (MMBtu per short ton). Converts the
# ACR f.o.b. $/ton price to $/MMBtu so it is comparable to gas.
# Source: EIA Monthly Energy Review, Appendix A5, "Approximate Heat Content of
# Coal and Coal Coke" (production-basis average heat contents).
COAL_HEAT_CONTENT_MMBTU_PER_TON: dict[str, float] = {
    "BIT": 24.93,  # bituminous
    "SUB": 17.46,  # subbituminous (PRB)
    "LIG": 13.30,  # lignite
    "ANT": 25.09,  # anthracite (not in any modeled fleet; completeness)
}

# Delivered-cost commodity share by delivery mode: the fraction of a coal
# plant's DELIVERED $/MMBtu that is the mine-gate (f.o.b.) commodity, the
# remainder being rail/transport. Used to lift the ACR f.o.b. price to a
# delivered cost comparable to the model's ``COAL_PRICE_BASE`` (delivered =
# f.o.b. / commodity_share). PRB-by-rail reuses the cited PRB decomposition
# (:data:`PRB_COMMODITY_SHARE`, 0.42 — long-haul rail dominates delivered
# cost). Mine-mouth lignite is ~all commodity (no rail). Interior/Appalachian
# bituminous railed short-haul into the MISO/PJM footprint carries a much
# smaller freight fraction than long-haul PRB.
# Source: EIA Coal Transportation Rates to the Electric Power Sector (rail
# freight as a share of delivered cost: ~55-60% for long-haul PRB, ~15% for
# short-haul Interior/Appalachian bituminous); mine-mouth lignite ~0.
COAL_DELIVERY_COMMODITY_SHARE: dict[str, float] = {
    "prb": PRB_COMMODITY_SHARE,  # 0.42, long-haul rail
    "subbituminous": PRB_COMMODITY_SHARE,  # same basin economics as prb
    "bituminous": 0.85,  # short-haul Interior/Appalachian rail
    "lignite": 1.00,  # mine-mouth, no transport
    "waste": 1.00,  # reclamation fuel, near-mine
}

# Representative heat rates (MMBtu/MWh) for locating the coal-vs-gas-CC merit
# crossover in gas-price space (``gas_mid``): the gas price at which a gas-CC's
# fuel cost equals the coal plant's fuel cost is
# ``gas_mid = coal_delivered$/MMBtu x COAL_HR / CC_HR``. Representative EIA
# Table 8 tested heat rates (subcritical steam coal; F-class combined cycle) —
# the class-typical values, not per-plant (the LP still prices each unit at its
# own heat rate; these only place the crossover the sigmoid centers on).
COAL_SIGMOID_REP_HR_COAL: float = 10.0  # HEAT_RATE_BINS["coal"]["subcritical"]
COAL_SIGMOID_REP_HR_GAS_CC: float = 6.7  # HEAT_RATE_BINS["gas_cc"]["f_class"]

# Minimum delivered gas price ($/MMBtu) observed over the backcast window
# (2023-2025), per ISO — the cheapest-gas anchor for the sigmoid floor: coal's
# deepest bid discount is the fraction that pulls it to merit-order parity with
# the cheapest gas it competes against (``floor = gas_min / gas_mid``). A
# market fact (the observed gas trough), not a residual.
# Source: EIA-923 Schedule-5 delivered gas cost to each ISO's gas fleet, 2024
# (the cheapest of 2023-2025); Henry Hub 2024 ~$2.19 + small regional basis.
COAL_SIGMOID_BACKCAST_GAS_MIN_MMBTU: dict[str, float] = {
    "ERCOT": 2.00,
    "MISO": 2.19,
    "PJM": 2.86,  # +0.67 EIA-923 delivered basis (GAS_BASIS_DIFFERENTIAL)
    "CAISO": 3.40,
    "NYISO": 2.74,
    "NEISO": 3.29,
}

# Baseline logistic slope (per $/MMBtu) for a coal supply group whose plants
# all draw one producing region, so the annual region f.o.b. resolves no
# cross-plant crossover dispersion (e.g. MISO's all-PRB group). The physical
# crossover-sharpness prior at the mechanism's established scale; a multi-region
# group (e.g. MISO bituminous spanning IL/IN/KY/ENC) instead derives its slope
# from the real across-region delivered-cost dispersion. Clipped to
# [SLOPE_MIN, SLOPE_MAX]. PPI intra-year variability adds a (small, ~2% CV)
# fuzzing term to the dispersion.
COAL_SIGMOID_BASELINE_SLOPE: float = 2.5
COAL_SIGMOID_SLOPE_MIN: float = 1.0
COAL_SIGMOID_SLOPE_MAX: float = 4.0

# Lowest the sigmoid floor may go: a coal plant never bids below this fraction
# of full delivered fuel cost. Bounds the cheap-gas discount so the floor stays
# a merit-order discount, not an unbounded giveaway (the sunk take-or-pay
# tonnage is a SEPARATE mechanism, coal_takeorpay_from_data).
COAL_SIGMOID_FLOOR_MIN: float = 0.50

# Follower-tier (low-must-run PRB cyclers, mustrun <= coal_prb_follower_mustrun_max)
# deepen their cheap-gas discount vs the baseload PRB tier: a cycler bids nearer
# its avoidable cost. Applied as a multiplicative discount on the baseload
# floor/ceil. Matches the established baseload->follower ordering (follower
# floor/ceil below baseload).
COAL_SIGMOID_FOLLOWER_DISCOUNT: float = 0.87

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
# takes precedence, and this flat value fills unreported months and any
# forecast year outside OIL_PRICE_TRAJECTORIES' range.
OIL_PRICE_PER_MMBTU: float = 18.0

# --- Forecast-year oil-price trajectories (real 2024$/MMBtu) ---
# AEO2025 Table 12 ("Petroleum and Other Liquids Prices"), electric-power
# distillate + residual fuel oil, averaged (same blend construction as
# OIL_PRICE_PER_MMBTU above) — data/raw/eia-aeo/
# eia_aeo2025_fuel_prices.part*.csv, derived via
# scripts/derive_fuel_trajectories.py::derive_oil_trajectory (P-1D, CLAUDE.md
# rule 23). AEO prices this series at $/gal; converted to $/MMBtu via EIA fuel
# heat contents (0.1385 MMBtu/gal distillate, 0.1497 MMBtu/gal residual).
# Replaces the flat OIL_PRICE_PER_MMBTU scalar for FORECAST years (backcast
# months keep the measured EIA-923 receipt series; OIL_PRICE_PER_MMBTU stays
# the fallback for unreported backcast months and any year outside this
# table's range). Selected via ``ScenarioConfig.oil_price_path`` (default
# "mid"); scenario mapping matches HENRY_HUB_TRAJECTORIES (highogs -> "low",
# ref2025 -> "mid", lowogs -> "high").
OIL_PRICE_TRAJECTORIES: dict[str, dict[int, float]] = {
    "low": {
        2024: 21.67,
        2025: 20.49,
        2026: 19.98,
        2027: 19.48,
        2028: 18.91,
        2029: 18.42,
        2030: 17.95,
        2031: 17.91,
        2032: 17.80,
        2033: 17.93,
        2034: 17.94,
        2035: 17.95,
        2036: 17.98,
        2037: 18.07,
        2038: 18.18,
        2039: 18.22,
        2040: 18.26,
        2041: 18.27,
        2042: 18.30,
        2043: 18.85,
        2044: 18.62,
        2045: 18.54,
        2046: 18.59,
        2047: 18.67,
        2048: 18.75,
        2049: 18.76,
        2050: 18.72,
    },
    "mid": {
        2024: 21.67,
        2025: 19.07,
        2026: 18.41,
        2027: 18.51,
        2028: 18.68,
        2029: 18.91,
        2030: 19.22,
        2031: 19.25,
        2032: 19.49,
        2033: 19.78,
        2034: 19.91,
        2035: 20.09,
        2036: 20.13,
        2037: 20.23,
        2038: 20.38,
        2039: 20.45,
        2040: 20.58,
        2041: 20.73,
        2042: 20.76,
        2043: 20.91,
        2044: 20.83,
        2045: 20.64,
        2046: 20.90,
        2047: 21.41,
        2048: 21.46,
        2049: 21.52,
        2050: 21.70,
    },
    "high": {
        2024: 21.67,
        2025: 22.30,
        2026: 21.91,
        2027: 21.45,
        2028: 21.12,
        2029: 20.84,
        2030: 20.82,
        2031: 20.90,
        2032: 21.27,
        2033: 21.64,
        2034: 21.81,
        2035: 21.99,
        2036: 22.39,
        2037: 22.59,
        2038: 22.73,
        2039: 22.97,
        2040: 23.10,
        2041: 23.21,
        2042: 23.23,
        2043: 23.21,
        2044: 23.23,
        2045: 23.26,
        2046: 23.49,
        2047: 23.84,
        2048: 24.08,
        2049: 24.22,
        2050: 24.29,
    },
}

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

# --- Nuclear fuel price ($/MMBtu, real 2024$) ---
# D2 fix (P-1D, CLAUDE.md rule 23): nuclear was priced at $0/MMBtu alongside
# wind/solar/hydro (fuel.py's non-fuel-burning default), but nuclear plants do
# burn a real, priced fuel. The EIA Uranium Marketing Annual Report publishes
# no $/MMBtu series directly (data/raw/uranium-marketing/, P-0C intake) — only
# front-end U3O8 purchase price ($/lb U3O8e) and SWU enrichment-services
# price, both nominal. This series is derived
# (scripts/derive_fuel_trajectories.py::derive_nuclear_fuel_trajectory) by
# deflating both to real 2024$ (INFLATION_RATE) and building up a delivered
# $/MMBtu cost from the standard LWR fuel-cycle physical constants (World
# Nuclear Association "Nuclear Fuel Cycle": ~8.9 kg natural U3O8 and ~7.3 SWU
# per kg of ~4.4% LEU at a 0.25-0.3% tails assay) plus WNA-cited conversion
# (~$10/kgU) and fabrication (~$300/kgLEU) costs — neither published as a time
# series by EIA, so held flat in real terms — divided by the heat content of
# a representative 45,000 MWd/tHM US LWR burnup (NRC/EIA-cited current-fleet
# average). 2006 is the first year with both a U3O8 and a SWU price (SWU
# series starts there); years without both are not derived (no guessing).
# Forecast years (2025-2050) hold the last derived value (2024: $0.576/MMBtu)
# flat in real terms — neither EIA nor AEO publishes a forward SWU/U3O8
# trajectory, so a hold-flat real anchor is the documented, non-speculative
# default (same "no silent compounding tail" principle as the
# fuel.resolve_annual_gas_price extrapolation fix). ScenarioConfig-overridable
# via ``nuclear_fuel_price_override`` ($/MMBtu, e.g. for a sensitivity case).
NUCLEAR_FUEL_PRICE_HISTORICAL: dict[int, float] = {
    2006: 0.5608,
    2007: 0.6831,
    2008: 0.7884,
    2009: 0.7994,
    2010: 0.8235,
    2011: 0.8528,
    2012: 0.8456,
    2013: 0.8115,
    2014: 0.7540,
    2015: 0.7175,
    2016: 0.6796,
    2017: 0.6318,
    2018: 0.5979,
    2019: 0.5551,
    2020: 0.5102,
    2021: 0.5051,
    2022: 0.5283,
    2023: 0.5568,
    2024: 0.5760,
}

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

# --- Named carbon-program price paths (P-1D: wires the previously-dead
# ``ScenarioConfig.carbon_program_price_path`` field, CLAUDE.md rule 23) ---
# An explicit, scenario-matrix alternative to the single default floor-band
# escalator (:func:`market_sim.policy.cap_and_trade.projected_price`), in the
# same spirit as the exogenous RFF :data:`CARBON_PRICE_PATHS` low/mid/high
# scenario paths (an explicitly-labelled sensitivity axis, not a fitted value,
# CLAUDE.md rule 1):
#   "low"  — anchors on the program's own published REGULATORY FLOOR
#            (:data:`CARB_FLOOR_PRICE`, CAISO-only — no RGGI floor-price
#            series is landed in-repo) and escalates at CPI only
#            (:data:`INFLATION_RATE`) — a lower bound where the market never
#            clears above its floor with no real risk premium. RGGI ISOs fall
#            back to "mid" (undocumented floor series -> no guessing).
#   "mid"  — IDENTICAL to the default (``carbon_program_price_path=None``):
#            anchors on the last measured clearing price and escalates at the
#            program's own published reserve/CCR rate
#            (:data:`CARB_FLOOR_ESCALATION` / :data:`RGGI_RESERVE_ESCALATION`).
#   "high" — the same anchor, escalated at DOUBLE the published reserve rate
#            — an explicit upper-bound sensitivity multiplier (no separate
#            primary-sourced "high" trajectory exists for either program;
#            multiplier documented here rather than invented as a fake data
#            point).
CARBON_PROGRAM_PRICE_PATH_ESCALATION_MULTIPLIER: dict[str, float] = {
    "mid": 1.0,
    "high": 2.0,
}


@dataclass(frozen=True)
class CapAndTradeProgram:
    """One ISO's cap-and-trade program definition (registry value).

    Attributes:
        name: Program label ("CARB" or "RGGI").
        member_states: Postal codes of every state the program has ever
            covered within this ISO's footprint (historical union — e.g. PJM
            includes Virginia even though it exited 1 Jan 2024). Actual
            year-by-year membership is resolved from
            :data:`RGGI_MEMBER_STATES_BY_YEAR`, not this tuple directly;
            this is the documentary / crosswalk reference other code
            intersects against.
        price_key: Key into :data:`STATE_CARBON_PRICE_BY_ISO` for the
            measured backcast allowance price, and the anchor for the
            forecast projection. ``None`` for a program with no measured
            series in-repo (PJM).
        escalation_rate: Nominal per-year forward escalation applied to the
            last measured price to build the projected forecast adder.
        external_nodes: Zone names that are priced import/external nodes,
            not in-region load — excluded from membership (m_zone = 0).
        zone_share: Optional per-zone, per-year RGGI-member fraction (0..1)
            overriding the uniform-membership default, for multi-state
            roll-up zones (PJM) whose fossil fleet spans member and
            non-member states. Keyed ``{zone: {year: share}}`` because a
            zone's member share can move year to year (Virginia's exit).
            ``None`` → uniform membership (1.0 on every load zone). This is
            the *zone-level* fallback; a generator with a real, resolvable
            ``plant_code`` is instead tested exactly against its own plant's
            state (per-unit membership,
            ``policy.cap_and_trade.per_generator_membership``) — the
            fractional share only applies where the fleet representation
            can't resolve individual units to a single state (legacy
            equal-width heat-rate bins, whose ``plant_code`` is synthetic).
    """

    name: str
    member_states: tuple[str, ...]
    price_key: str | None
    escalation_rate: float
    external_nodes: tuple[str, ...] = ()
    zone_share: "dict[str, dict[int, float]] | None" = None


# PJM's footprint straddles RGGI members (MD, DE, NJ; VA was a member through
# 2023 and exited 1 Jan 2024) and non-members (OH, IN, KY, WV, IL, most of PA),
# and its zones are multi-state roll-ups, so a clean 0/1 zone map is impossible
# (plan §5). `m_zone[z]` is the RGGI-member share of zone z's operating fossil
# nameplate capacity, computed by `scripts/derive_pjm_rggi_zone_share.py` from
# the year-matched EIA-860 plant/generator tables (state + capacity), the same
# PJM zone assignment the dispatch model uses
# (`data.zone_assignment.build_zone_lookup("PJM")`), and
# `RGGI_MEMBER_STATES_BY_YEAR` (Virginia's 2024 exit is directly visible below:
# PJM_Dominion — VA+NC — drops from ~0.99 to 0.0). Keyed by zone then year;
# 2024 and 2025 share the same underlying EIA-860-vintage fleet snapshot up to
# small year-over-year additions/retirements, so only the legal membership
# differs from 2023. This is the *zone-level* fallback consumed only by
# generators whose `plant_code` cannot be resolved to a single physical plant
# (legacy equal-width bins); a real plant_code is tested exactly against its
# own state instead (`policy.cap_and_trade.per_generator_membership`). Still
# ships inert by default: PJM has no measured price series (`price_key=None`
# below) so the adder path stays $0 regardless of membership, and the
# mass-cap row only activates when a user explicitly sets
# `mass_cap_enabled=True` (default off, rule 24).
PJM_RGGI_ZONE_SHARE: dict[str, dict[int, float]] = {
    "PJM_ComEd": {2023: 0.0, 2024: 0.0, 2025: 0.0},
    "PJM_AEP_Ohio": {2023: 0.0, 2024: 0.0, 2025: 0.0},
    "PJM_ATSI": {2023: 0.0, 2024: 0.0, 2025: 0.0},
    "PJM_West_APS": {2023: 0.0108, 2024: 0.0, 2025: 0.0},
    "PJM_Central_PA": {2023: 0.0, 2024: 0.0, 2025: 0.0},
    "PJM_Dominion": {2023: 0.9881, 2024: 0.0, 2025: 0.0},
    "PJM_EMAAC": {2023: 0.7327, 2024: 0.7252, 2025: 0.7221},
    "PJM_SWMAAC": {2023: 0.9976, 2024: 0.9976, 2025: 0.9976},
}

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
    # PJM: partial RGGI membership via fractional per-zone share
    # (PJM_RGGI_ZONE_SHARE). member_states is the historical union (VA
    # included even though it exited 1 Jan 2024) — actual year membership
    # comes from RGGI_MEMBER_STATES_BY_YEAR. Still inert by default: no
    # measured price series (price_key=None) keeps the adder at $0, and the
    # mass-cap row is opt-in (mass_cap_enabled, default off).
    "PJM": CapAndTradeProgram(
        name="RGGI",
        member_states=("MD", "DE", "NJ", "VA"),
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
# RGGI member states by year (postal codes). Virginia joined RGGI's CO2 Budget
# Trading Program in 2021 (regulation 9 VAC 5-140) and exited effective 1 Jan
# 2024 (2023 Va. Acts of Assembly ch. 2/3, repealing the program); Pennsylvania's
# entry remains enjoined by the Commonwealth Court (Shirkey v. DEP, ongoing) and
# was never an actual member, so PA is never included. Used to (a) resolve
# per-generator RGGI membership exactly from a plant's own state (§5 per-unit
# mask) and (b) sum each RGGI ISO's own member-state budgets (below) instead of
# the regional over-bound. 2022 omitted (holdout quarantine, CLAUDE.md rule 22);
# years beyond 2025 hold the 2025 (post-VA-exit) set — no further membership
# changes are enacted as of this writing.
# Source: RGGI, Inc. participating-states list (rggi.org/program-overview-and-
# design/elements); Virginia Clean Economy and Equity Act repeal, effective
# 2024-01-01.
RGGI_MEMBER_STATES_BY_YEAR: dict[int, frozenset[str]] = {
    2023: frozenset({"NY", "CT", "MA", "ME", "NH", "RI", "VT", "MD", "DE", "NJ", "VA"}),
    2024: frozenset({"NY", "CT", "MA", "ME", "NH", "RI", "VT", "MD", "DE", "NJ"}),
    2025: frozenset({"NY", "CT", "MA", "ME", "NH", "RI", "VT", "MD", "DE", "NJ"}),
}

# RGGI CO2 allowance budgets (short tons/yr), regional ("RGGI") and per
# member-state (postal code). Per-state values are each state's "CO2 Allowance
# Base Budget" — the gross annual issuance under its own CO2 Budget Trading
# Program regulation, BEFORE the Third Adjustment for Banked Allowances (TABA,
# a bank-clearing haircut) — because this model's row is an explicitly no-bank
# instrument (plan §8); using the (smaller) bank-adjusted budget would smuggle
# banked-market scarcity into a mechanism defined not to have one. A RGGI ISO's
# power-sector row sums its own member states' base budgets
# (policy/cap_and_trade.py::_published_power_sector_budget), which is a much
# tighter, more faithful bound than the regional total (rule 12: prefer the
# accurate figure). "RGGI" is kept as the regional fallback for years without a
# per-state breakdown (2027-2030 projections) or an unmapped ISO.
# 2023-2025: exact per-state and regional totals from RGGI, Inc.'s official
# "Distribution of VYyyyy CO2 Allowances By State" spreadsheets ("CO2 Allowance
# Base Budget" column), rggi.org/sites/default/files/Uploads/Allowance-Tracking/
# {2023,2024,2025}_Allowance-Distribution.xlsx (release date 2026-06-23); this
# replaces the prior ICAP-ETS-profile regional estimate (93.0M/69.0M/67.0M) with
# the primary source's exact totals (112,457,784 / 84,162,784 / 81,347,784).
# 2027-2030 regional-only: 2021 Model Rule ~2.9%/yr decline (a labelled forward
# trajectory, not measured); no per-state breakdown is published for projected
# years, so a RGGI ISO's forecast-year row falls back to this regional
# over-bound (documented, still slack). 2022/2026 omitted (rule 22 quarantine).
RGGI_STATE_CO2_BUDGET: dict[str, dict[int, float]] = {
    "RGGI": {
        2023: 112_457_784.0,
        2024: 84_162_784.0,
        2025: 81_347_784.0,
        2027: 63_200_000.0,
        2028: 61_400_000.0,
        2029: 59_600_000.0,
        2030: 57_900_000.0,
    },
    "CT": {2023: 4_566_218.0, 2024: 4_418_921.0, 2025: 4_271_624.0},
    "DE": {2023: 3_178_264.0, 2024: 3_075_739.0, 2025: 2_973_215.0},
    "ME": {2023: 2_569_587.0, 2024: 2_487_656.0, 2025: 2_405_725.0},
    "MD": {2023: 15_772_679.0, 2024: 15_263_882.0, 2025: 14_755_086.0},
    "MA": {2023: 11_220_454.0, 2024: 10_858_504.0, 2025: 10_496_554.0},
    "NH": {2023: 3_723_549.0, 2024: 3_604_823.0, 2025: 3_486_098.0},
    "NJ": {2023: 16_380_000.0, 2024: 15_840_000.0, 2025: 15_300_000.0},
    "NY": {2023: 27_295_284.0, 2024: 26_414_791.0, 2025: 25_534_298.0},
    "RI": {2023: 1_763_884.0, 2024: 1_706_986.0, 2025: 1_650_085.0},
    "VT": {2023: 507_865.0, 2024: 491_482.0, 2025: 475_099.0},
    # Virginia: 2023 only (exited 1 Jan 2024, RGGI_MEMBER_STATES_BY_YEAR above).
    "VA": {2023: 25_480_000.0},
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
# PJM/MISO/NYISO/NEISO — EIA-860 2025 Early Release energy-storage schedule
# (data/raw/eia-860/eia860_energy_storage_operable.parquet +
# ..._proposed.parquet), plants assigned to each ISO by balancing-authority
# code (eia860_plant.parquet "Balancing Authority Code" joined on Plant Code —
# the zone_assignment._ISO_TO_BA_CODE crosswalk, not a raw state filter, since
# MISO/PJM member utilities split several states e.g. Illinois). mid = operable
# Status="OP" nameplate MW; high = mid + proposed-schedule Status in
# {U, V, TS} ("under construction" through "complete, not yet commercial"),
# matching CAISO's "operational + under construction" definition above;
# low = mid x 0.75 (CAISO's own low/mid ratio), rounded to the nearest 10 MW.
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
    "PJM": {
        "low": 380.0,
        "mid": 500.0,
        "high": 870.0,
    },
    "MISO": {
        "low": 600.0,
        "mid": 800.0,
        "high": 1_440.0,
    },
    "NYISO": {
        "low": 190.0,
        "mid": 250.0,
        "high": 280.0,
    },
    "NEISO": {
        "low": 580.0,
        "mid": 770.0,
        "high": 1_280.0,
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
class CapacityDemandCurvePoint:
    """One point on a normalized (dimensionless) capacity demand curve.

    ``reserve_ratio`` is the accredited firm capacity as a fraction of the
    published reliability requirement (``accredited_firm_capacity_mw /
    requirement_mw``; 1.0 = exactly at the requirement).
    ``price_frac_net_cone`` is the capacity price at that reserve position as
    a *multiple of net-CONE* (1.0 = net-CONE, 0.0 = zero-cross, > 1.0 = the
    price cap / shortage region). Points are ordered left-to-right by
    ``reserve_ratio`` and the curve is monotone non-increasing in it.
    """

    reserve_ratio: float
    price_frac_net_cone: float


def evaluate_demand_curve(
    points: "tuple[CapacityDemandCurvePoint, ...]", reserve_position: float
) -> float:
    """Piecewise-linear value of a normalized capacity demand curve.

    ``points`` are ordered left-to-right by ``reserve_ratio`` (ascending). The
    return is the capacity price as a *fraction of net-CONE* at
    ``reserve_position``, linearly interpolated between the two bracketing
    points and **flat-extrapolated** past both ends — so below the leftmost
    point the price clamps to the cap (the highest fraction) and above the
    rightmost point it clamps to the zero-cross value (0.0 for every published
    curve). Returns ``0.0`` for an empty curve. Pure Python (no numpy) so the
    config layer keeps its light import surface.
    """
    if not points:
        return 0.0
    x = float(reserve_position)
    if x <= points[0].reserve_ratio:
        return points[0].price_frac_net_cone
    if x >= points[-1].reserve_ratio:
        return points[-1].price_frac_net_cone
    for lo, hi in zip(points, points[1:]):
        if lo.reserve_ratio <= x <= hi.reserve_ratio:
            span = hi.reserve_ratio - lo.reserve_ratio
            if span <= 0.0:
                return lo.price_frac_net_cone
            frac = (x - lo.reserve_ratio) / span
            return lo.price_frac_net_cone + frac * (
                hi.price_frac_net_cone - lo.price_frac_net_cone
            )
    return points[-1].price_frac_net_cone  # unreachable; satisfies type checkers


@dataclass(frozen=True)
class MarketDesign:
    """Storage revenue-stack switches and parameters for one ISO/market.

    ``capacity_market`` gates the resource-adequacy value stream entirely.
    ``net_cone_per_kw_yr`` is the marginal cost of new entry of the capacity
    resource the market prices against (the FIXED clearing-price anchor), in
    $/kW-yr. A storage unit earns ``net_cone × ELCC(duration) × derate`` of it,
    where the ELCC (effective load-carrying capability) credit rises with
    duration and the derate falls as storage saturates the peak.

    **CR-1 sloped demand curve (default-off).** When
    ``ScenarioConfig.capacity_market_clearing`` is on and this ISO carries a
    published ``demand_curve``, the fixed price is replaced by the market's own
    net-CONE-anchored sloped curve evaluated at the system's accredited reserve
    position — ``VRR(reserve_position) × net_cone_curve_per_kw_yr`` (see
    :meth:`capacity_price_per_firm_mw_yr`). The curve is the normalized,
    dimensionless shape (:class:`CapacityDemandCurvePoint`); the $ level is
    ``net_cone_curve_per_kw_yr`` (the PUBLISHED net-CONE, distinct from the
    legacy ``net_cone_per_kw_yr`` fixed anchor so the default path stays
    byte-identical until the P-2A default flip reconciles the two). Every curve
    number traces to the P-0B ``capacity-market-demand-curve`` datatype
    (``data/raw/capacity-market/demand-curve``); the reconciliation is asserted
    in ``tests/test_capacity_demand_curve.py`` (rule 13 — published input, never
    a fit target).
    """

    capacity_market: bool
    net_cone_per_kw_yr: float = 0.0
    # CR-1 sloped demand curve (normalized (reserve_ratio, price/net-CONE)
    # points, ascending reserve_ratio); empty ⇒ no published curve, fixed
    # fallback. ``net_cone_curve_per_kw_yr`` is the PUBLISHED net-CONE anchor
    # the curve scales (kept separate from the legacy fixed anchor above for
    # default byte-identity). ``demand_curve_delivery_year`` / ``_source`` are
    # provenance for the reconciliation test + docs.
    demand_curve: tuple[CapacityDemandCurvePoint, ...] = ()
    net_cone_curve_per_kw_yr: float = 0.0
    demand_curve_delivery_year: str = ""
    demand_curve_source: str = ""

    def capacity_price_per_firm_mw_yr(
        self,
        config: "object | None" = None,
        reserve_position: "float | None" = None,
    ) -> float:
        """Capacity clearing price in $/firm-MW-yr — the shared seam (rule 19).

        All three capacity screens (retirement, thermal entry, storage entry)
        price adequacy through this one function, then apply their own
        accreditation (thermal ``× (1 − EFORd)``; storage ``× ELCC × derate``),
        so there is one curve per ISO and no screen-specific curves.

        Two modes:

        * **Fixed** (default, and whenever the curve gate is off, the ISO has
          no published curve, or no ``reserve_position`` is supplied): the flat
          ``net_cone_per_kw_yr × 1000``, byte-identical to the pre-CR-1 stub.
        * **Curve** (CR-1): when ``config.capacity_market_clearing`` is on, this
          ISO has a published ``demand_curve``, and a ``reserve_position``
          (accredited firm capacity ÷ the shared adequacy requirement) is
          supplied — ``VRR(reserve_position) × net_cone_curve_per_kw_yr × 1000``,
          where ``VRR`` is the normalized sloped curve
          (:func:`evaluate_demand_curve`).

        Energy-only ISOs (``capacity_market`` False — ERCOT and any ISO absent
        from :data:`MARKET_DESIGN`) return ``0.0`` in **both** modes.
        ``config`` is duck-typed via ``getattr`` so the config layer needs no
        import of :class:`ScenarioConfig`.
        """
        if not self.capacity_market:
            return 0.0
        if (
            reserve_position is not None
            and self.demand_curve
            and config is not None
            and getattr(config, "capacity_market_clearing", False)
        ):
            anchor = self.net_cone_curve_per_kw_yr or self.net_cone_per_kw_yr
            frac = evaluate_demand_curve(self.demand_curve, float(reserve_position))
            return frac * anchor * 1000.0
        if self.net_cone_per_kw_yr <= 0.0:
            return 0.0
        return self.net_cone_per_kw_yr * 1000.0


# --- CR-1 sloped capacity demand curves (normalized) ----------------------
#
# Each ISO's published capacity demand curve, reduced to the dimensionless
# (reserve_ratio, price/net-CONE) shape the CR-1 mechanism evaluates at the
# model's own accredited reserve position (accredited_firm_capacity_mw /
# requirement_mw; 1.0 = at the requirement). Consumed only when
# ScenarioConfig.capacity_market_clearing is on (default off). Every number
# traces to the P-0B capacity-market-demand-curve datatype
# (data/raw/capacity-market/demand-curve/<iso>/<iso>.csv); the reconciliation
# is asserted in tests/test_capacity_demand_curve.py (rule 13 — published
# market-design input, never a fit target). The $ level each curve scales is
# MarketDesign.net_cone_curve_per_kw_yr (the PUBLISHED net-CONE), kept distinct
# from the legacy fixed net_cone_per_kw_yr so the default path is byte-identical
# until the P-2A default flip reconciles them.
#
# PJM 2026/2027 RPM BRA (the current published curve with a full cap/net-CONE/
# zero triple). x = pct_of_requirement curve points (0.99, 1.015, 1.045);
# y-fractions: cap = price_cap/net_cone = 329.17/212.14 = 1.5517 (both
# $/MW-day, so the ratio is basis-independent), the middle point is Net CONE by
# PJM Manual 18 §3.4 construction (1.0), the third point is the published
# zero-cross (y=0). Net-CONE anchor 77.431 $/kW-yr — the published UCAP net-CONE
# 212.14 $/MW-day × 365 / 1000 (the demand-curve reference the VRR curve is
# drawn around, and the basis the auction clears in). P-2B Option A anchor
# re-derivation (R1, accreditation-basis memo 2026-07-12 §4.2): supersedes the
# legacy 60.396 $/kW-yr (60,396 $/MW-yr ICAP-annual row), which mis-scaled the
# UCAP-cleared curve by PJM's ~0.78 ICAP↔UCAP factor (P-2A Pass-1B uniform
# −22%). Both figures are on disk in the same 2026/27 net_cone rows.
_PJM_VRR_CURVE: tuple[CapacityDemandCurvePoint, ...] = (
    CapacityDemandCurvePoint(0.99, 1.5517),  # price cap (329.17/212.14)
    CapacityDemandCurvePoint(1.015, 1.0),  # Net CONE reference point
    CapacityDemandCurvePoint(1.045, 0.0),  # zero-cross (published y=0)
)
# NYISO 2025-2026 ICAP demand curve, NYCA (system) locality, modeled ANNUALLY
# (the ISO clears monthly; CR-3 adds the seasonal split). The curve is a single
# straight line: net-CONE at the requirement, zero at the requirement + the
# published 12% "Demand Curve Length" (zero-cross 1.12), extended left to the
# maximum clearing price. Cap fraction = summer max/reference-point =
# 21.69/5.72 = 3.792 (both $/kW-month, so basis-independent); its reserve
# position (0.665) is where that fraction meets the reference→zero line. The
# reference point is placed at net-CONE (frac 1.0) at the requirement — the
# documented annual reduction of NYISO's seasonal reference-point prices.
# Net-CONE anchor 50.55 $/kW-yr (NYCA Annual Reference Value).
_NYISO_ICAP_CURVE: tuple[CapacityDemandCurvePoint, ...] = (
    CapacityDemandCurvePoint(0.665, 3.792),  # max clearing price (21.69/5.72)
    CapacityDemandCurvePoint(1.0, 1.0),  # reference point = Net CONE
    CapacityDemandCurvePoint(1.12, 0.0),  # zero (100% + 12% curve length)
)
# ISO-NE FCA/MRI curve, modeled ANNUALLY. Price levels from FCA 18 (2027/2028):
# cap = starting price/net-CONE = 14.525/9.078 = 1.600 ($/kW-month, ratio
# basis-independent); net-CONE at the requirement (1.0). The reserve-position
# geometry is taken from the last FCA that published explicit curve points
# (FCA 11, 2020/2021, in MW): its Net ICR (where price = that year's net-CONE
# 11.64) ≈ 34,217 MW, so the cap plateau end (33,457 MW) is 0.978 and the
# zero-cross (37,053 MW) is 1.083 of the requirement. A first-order linear
# reduction of the MRI slope (skips FCA 11's interior kink); refined in CR-3.
# Net-CONE anchor 108.94 $/kW-yr (9.078 $/kW-month × 12).
_NEISO_FCA_CURVE: tuple[CapacityDemandCurvePoint, ...] = (
    CapacityDemandCurvePoint(0.978, 1.600),  # starting price (14.525/9.078)
    CapacityDemandCurvePoint(1.0, 1.0),  # Net CONE at requirement
    CapacityDemandCurvePoint(1.083, 0.0),  # zero-cross (FCA 11 geometry)
)
# MISO seasonal PRA reliability-based demand curve (RBDC), modeled ANNUALLY
# (CR-3 adds the four-season split). The P-0B intake captured MISO's CONE
# levels and PRA clearing OUTCOMES but not the RBDC's own shape parameters, so
# only the price levels are data-derived: net-CONE at the requirement (1.0);
# cap = North/Central gross CONE / net CONE ≈ 127,361 / 79,800 = 1.596 (annual
# $/MW-yr; the RBDC caps at gross CONE). The cap (0.97) and zero-cross (1.05)
# reserve positions are FIRST-ORDER representative values (documented, not
# claimed as published — the seasonal RBDC parameters land in CR-3), so the
# reconciliation test asserts only the net-CONE anchor and the cap fraction.
# Net-CONE anchor 79.8 $/kW-yr (North/Central Net CONE, 79,800 $/MW-yr).
_MISO_RBDC_CURVE: tuple[CapacityDemandCurvePoint, ...] = (
    CapacityDemandCurvePoint(0.97, 1.596),  # ≈ gross/net CONE (RBDC cap)
    CapacityDemandCurvePoint(1.0, 1.0),  # Net CONE at requirement
    CapacityDemandCurvePoint(1.05, 0.0),  # zero-cross (first-order, CR-3)
)

# Per-ISO market design. ISOs absent here fall back to ``DEFAULT_MARKET_DESIGN``
# (energy-only) so a new ISO is conservative until its capacity rules are added.
MARKET_DESIGN: dict[str, MarketDesign] = {
    # Energy-only: scarcity is monetized through the energy price, not a
    # separate capacity payment. Source: ERCOT market design (ORDC).
    "ERCOT": MarketDesign(capacity_market=False),
    # RA program with a soft capacity price — no centralized auction/demand
    # curve, so CAISO keeps the FIXED proxy in BOTH modes (documented
    # low-fidelity member of the registry, CR-1 §3.2). Re-cited: the 90 $/kW-yr
    # anchor ≈ the CPM soft-offer cap ($7.34/kW-month × 12 = $88.08/kW-yr,
    # FERC ER24-1225 effective 2024-06-01), between it and the CPUC 2023 RA
    # report system price ($14.51/kW-month = $174/kW-yr for 2024). No
    # demand_curve ⇒ capacity_price_per_firm_mw_yr returns the fixed anchor even
    # when capacity_market_clearing is on. Source: CPUC 2023 Resource Adequacy
    # Report; CAISO CPM soft-offer-cap tariff (P-0B caiso.csv).
    "CAISO": MarketDesign(capacity_market=True, net_cone_per_kw_yr=90.0),
    # Capacity markets. The legacy net_cone_per_kw_yr is the FIXED-mode anchor
    # (kept labeled legacy — the fixed-mode default is byte-identical, and its
    # own re-derivation to the published UCAP basis is reserved for the P-2A
    # default flip, R4/accreditation-basis memo §4.3); net_cone_curve_per_kw_yr
    # is the PUBLISHED UCAP net-CONE the CR-1 curve scales, now on PJM's own
    # UCAP basis (R1 above).
    # Source: PJM 2026/2027 BRA planning parameters (fixed anchor ~$100/kW-yr
    # legacy; curve anchor 77.431 $/kW-yr = 212.14 $/MW-day UCAP).
    "PJM": MarketDesign(
        capacity_market=True,
        net_cone_per_kw_yr=100.0,
        demand_curve=_PJM_VRR_CURVE,
        net_cone_curve_per_kw_yr=77.431,
        demand_curve_delivery_year="2026/2027",
        demand_curve_source=(
            "PJM 2026/2027 RPM BRA Planning Period Parameters (Net CONE, price "
            "cap) + Manual 18 Rev.62 §3.4 VRR curve points"
        ),
    ),
    # Source: NYISO ICAP demand-curve reset net-CONE (fixed anchor ~$110/kW-yr).
    "NYISO": MarketDesign(
        capacity_market=True,
        net_cone_per_kw_yr=110.0,
        demand_curve=_NYISO_ICAP_CURVE,
        net_cone_curve_per_kw_yr=50.55,
        demand_curve_delivery_year="2025-2026",
        demand_curve_source=(
            "NYISO 'Demand Curve Parameters 2025-2026', NYCA locality (Annual "
            "Reference Value, summer reference-point/max clearing price, 12% "
            "Demand Curve Length)"
        ),
    ),
    # Source: ISO-NE FCM net-CONE (fixed anchor ~$95/kW-yr).
    "NEISO": MarketDesign(
        capacity_market=True,
        net_cone_per_kw_yr=95.0,
        demand_curve=_NEISO_FCA_CURVE,
        net_cone_curve_per_kw_yr=108.94,
        demand_curve_delivery_year="2027-2028",
        demand_curve_source=(
            "ISO-NE FCA 18 (2027/2028) Net CONE + starting price; FCA 11 "
            "(2020/2021) demand-curve points for the reserve-position geometry"
        ),
    ),
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
    # The CR-1 curve scales the published North/Central Net CONE (79.8 $/kW-yr);
    # the fixed anchor keeps its 80.0 rounding for default byte-identity.
    "MISO": MarketDesign(
        capacity_market=True,
        net_cone_per_kw_yr=80.0,
        demand_curve=_MISO_RBDC_CURVE,
        net_cone_curve_per_kw_yr=79.8,
        demand_curve_delivery_year="2025-2026",
        demand_curve_source=(
            "MISO PY2025-26 PRA Results Posting (North/Central Net CONE + LRZ "
            "gross CONE for the cap); RBDC shape reserve positions first-order "
            "(seasonal parameters land in CR-3)"
        ),
    ),
}

DEFAULT_MARKET_DESIGN: MarketDesign = MarketDesign(capacity_market=False)

# Target planning reserve margin per ISO for the reserve-margin adequacy
# backstop (capacity.py::apply_reserve_margin_build). Each ISO sets its own
# installed-reserve-margin / planning-reserve-margin target through its
# resource-adequacy process; ERCOT's 13.75% is its Board target RM and is NOT
# every ISO's target. The reserve-margin build resolves
# ``PLANNING_RESERVE_MARGIN_BY_ISO.get(iso, config.planning_reserve_margin)``,
# so an explicit ScenarioConfig.planning_reserve_margin still overrides this
# registry and an ISO absent here falls back to that scalar. Each value is on
# the counting basis of its OWN ISO's published construction: the requirement
# and the accredited-capacity ledger must use the same convention (see
# THERMAL_ACCREDITATION_BASIS_BY_ISO / RENEWABLE_CAPACITY_CREDIT_BY_ISO /
# ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO below).
PLANNING_RESERVE_MARGIN_BY_ISO: dict[str, float] = {
    # ERCOT Board-established minimum target reserve margin (13.75% of peak),
    # the benchmark the CDR's planning reserve margins are read against.
    # NOT an economic optimum: the Brattle/Astrapé MERM/EORM studies for the
    # PUCT ("Estimation of the Market Equilibrium and Economically Optimal
    # Reserve Margins for the ERCOT Region", 2018) put the market-equilibrium
    # RM near 10.25% and the economic optimum near 9%. The 13.75% target is
    # defined on the CDR counting convention — seasonal-rated thermal (no
    # EFORd derate), ELCC-accredited wind/solar/storage, firm peak load net
    # of load-side products — which the per-ISO accreditation registries
    # below put the floor/backstop ledger on (audit 2026-07-06, L-7c).
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

# Data-horizon gate for honoring an ANNOUNCED (non-fossil) EIA-860 retirement
# date deterministically. A self-reported planned-retirement year is credible
# only at the same near-term grain the additions pipeline trusts its U/V/TS
# statuses: within EIA860_OPERABLE_VINTAGE + this many years. Beyond the horizon
# an announced non-fossil date is honored ONLY if the unit carries a binding
# instrument in the confirmed-retirements registry; otherwise it is ignored, so
# the 2040-2072 hydro-relicense / solar-EOL placeholders stop force-retiring and
# far-dated nuclear announcements fall to the economic screen (+ registry). Set
# to 5 per the methodology spec's "after the data horizon (~2030) the model is
# fully economics-driven" line (§1.7 / §5); symmetric with the additions
# pipeline's near-term-only firm-status window. Consumed by
# model.capacity.apply_announced_retirements.
NONFOSSIL_ANNOUNCED_HORIZON_YEARS: int = 5

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
# system peak. Thermal is accredited at 1 - EFORd (UCAP) unless the ISO's
# published basis says otherwise (THERMAL_ACCREDITATION_BASIS_BY_ISO); storage
# uses STORAGE_ELCC_BY_DURATION; these are the GENERIC wind/solar/hydro
# fallback values (NREL/E3 ELCC studies). ISOs with a published accreditation
# of their own override them in RENEWABLE_CAPACITY_CREDIT_BY_ISO — a generic
# value must never masquerade as an ISO's published basis (rule 25 analogue).
RENEWABLE_CAPACITY_CREDIT: dict[str, float] = {
    "wind": 0.16,
    "solar": 0.18,
    "offshore_wind": 0.30,
    "hydro": 0.50,
}

# Per-ISO overrides of RENEWABLE_CAPACITY_CREDIT for the adequacy ledger (the
# retirement reliability floor and the reserve-margin backstop, capacity.py).
# ISOs absent here use the generic values above — byte-identical fallback.
# ERCOT values are the ISO's OWN published accreditation: the December 2025
# CDR counts wind/solar at probabilistic ELCCs. Implied percentages = the
# CDR's summer ELCC MW (operational + CDR-eligible planned, peak-load-hour
# column) over installed nameplate (ERCOT Fact Sheet, June 2026: wind
# 40,739 MW, utility-scale solar 39,591 MW):
#   wind : 8,210 / 40,739 = 20.2% for 2026, stable at 20.5-20.8% through
#          2030 -> 0.20.
#   solar: 11,097 / 39,591 = 28.0% for 2026, diluting to 20.5-21.1% by
#          2028-2030 as penetration grows -> 0.21 (the CDR's own plateau;
#          conservative for 2026-27, right for the forecast horizon where
#          the floor decision matters).
# Source: ERCOT, "Report on the Capacity, Demand and Reserves (CDR) in the
# ERCOT Region", December 2025 (Seasonal Summary + ELCC tabs); ERCOT Fact
# Sheet, July 2026. See docs/handoffs/ercot-accreditation-audit-2026-07-06.md.
# (ERCOT deliberately stays HERE, not in RENEWABLE_ELCC_CURVES_BY_ISO below:
# the CDR seasonal-rating accreditation basis stays per the CR-3 plan §3.4.1
# and the P-2B adopted basis — "ERCOT/CAISO untouched".)
RENEWABLE_CAPACITY_CREDIT_BY_ISO: dict[str, dict[str, float]] = {
    "ERCOT": {"wind": 0.20, "solar": 0.21},
}


@dataclass(frozen=True)
class RenewableElccCurve:
    """One ISO's published ELCC/accreditation curve for a VRE resource class.

    ``points`` are ``(penetration, credit)`` pairs ascending in penetration:
    ``credit`` is the accredited firm fraction of nameplate (0.41 = 41 % of
    nameplate counts toward the requirement) and ``penetration`` is measured
    on ``penetration_basis`` —

    * ``"pct_of_peak_load"`` — installed nameplate of the class as a percent
      of the system peak (MISO's published axis; the classic ELCC-literature
      basis). Evaluation needs the model's peak demand.
    * ``"installed_mw"`` — absolute installed nameplate MW of the class
      (PJM's ELCC/RRS axis). Evaluation needs only the model's installed MW.
    * ``None`` — a single published point with no penetration axis (NYISO's
      CAFs): the curve is a constant and ``points`` holds one pair whose
      penetration value is ignored. Never fabricate an axis the ISO did not
      publish (P-0B intake discipline / schema note).

    Evaluated by :func:`evaluate_renewable_elcc_curve` — piecewise-linear,
    flat-clamped at both ends (beyond the last published point the credit
    holds its endpoint value; no extrapolated slope is invented). The
    penetration argument is the MODEL'S OWN installed share, so the credit
    regenerates forward and responds to modeled build (rule 13).
    """

    penetration_basis: str | None
    points: tuple[tuple[float, float], ...]
    source: str


def evaluate_renewable_elcc_curve(
    curve: "RenewableElccCurve",
    installed_mw: float | None,
    peak_demand_mw: float | None,
) -> float | None:
    """Credit fraction of ``curve`` at the model's own penetration.

    Resolves the curve's penetration axis from the model quantities: the
    class's installed nameplate for ``"installed_mw"``, ``100 × installed /
    peak`` for ``"pct_of_peak_load"``, and nothing for a single-point curve
    (constant). Linear interpolation between published points, flat-clamped
    outside them (mirrors :func:`evaluate_demand_curve` — no slope beyond
    the published domain). Returns ``None`` when the axis quantity the curve
    needs is unavailable (caller falls back to the point-basis resolution),
    so a missing peak can never silently misprice a pct-of-peak curve. Pure
    Python — the config layer keeps its light import surface.
    """
    if not curve.points:
        return None
    if curve.penetration_basis is None:
        return curve.points[0][1]
    if installed_mw is None:
        return None
    if curve.penetration_basis == "pct_of_peak_load":
        if peak_demand_mw is None or peak_demand_mw <= 0.0:
            return None
        x = 100.0 * float(installed_mw) / float(peak_demand_mw)
    elif curve.penetration_basis == "installed_mw":
        x = float(installed_mw)
    else:  # unknown basis — never guess a conversion
        return None
    pts = curve.points
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for (x_lo, c_lo), (x_hi, c_hi) in zip(pts, pts[1:]):
        if x_lo <= x <= x_hi:
            span = x_hi - x_lo
            if span <= 0.0:
                return c_lo
            return c_lo + (x - x_lo) / span * (c_hi - c_lo)
    return pts[-1][1]  # unreachable; satisfies type checkers


# Penetration-indexed ELCC accreditation curves per ISO (CR-3.1, plan
# docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md §3.4.1;
# adopted basis = P-2B Option A per-ISO published-basis consistency,
# docs/handoffs/accreditation-basis-memo-2026-07-12.md §4.1). Replaces the
# flat generic wind 0.16 / solar 0.18 for exactly the ISOs with a published
# ELCC study on disk (data/raw/capacity-market/elcc/<iso>/<iso>.csv, the
# P-0B/N6 intake); every point below is digitized from those committed rows
# and reconciled against them by tests/test_renewable_elcc_curves.py — a
# published market-design input, never a fit target (rules 13/23).
#
# Resolution ladder (model/capacity.py::resolve_renewable_capacity_credit):
# curve here (when ScenarioConfig.renewable_elcc_curves is on) → per-ISO
# point override (RENEWABLE_CAPACITY_CREDIT_BY_ISO) → generic fallback
# (RENEWABLE_CAPACITY_CREDIT). ISOs / classes ABSENT here keep the flat
# constants — a cited, neutral fallback (rule 25 spirit), never a foreign
# study masquerading as the ISO's basis:
#
# * NEISO — NO ISO-published ELCC study: the on-disk rows are third-party
#   (2022 GE/NRDC, 2024 E3/Mettetal — both explicitly "not ISO-NE-adopted");
#   ISO-NE accredits intermittents via seasonal claimed capability today.
#   Falls back to the generic constants until ISO-NE's RCA marginal-ELCC
#   values are published/intaken.
# * CAISO — the on-disk CPUC E3/Astrapé study publishes INCREMENTAL
#   (marginal-tranche) ELCCs conditioned on the IRP portfolio (solar rises
#   6.6→8.8 % with storage buildout), not fleet-average accreditation;
#   using a marginal value as the whole-fleet ledger credit would misstate
#   the supply block (rule 15's misalignment exception, documented). CAISO
#   keeps the generic fallback ("CAISO untouched", P-2B §4.1) pending a
#   class-average NQC/ELCC intake.
# * ERCOT — CDR seasonal-rating basis stays in
#   RENEWABLE_CAPACITY_CREDIT_BY_ISO above (plan §3.4.1).
RENEWABLE_ELCC_CURVES_BY_ISO: dict[str, dict[str, RenewableElccCurve]] = {
    "PJM": {
        # PJM accredits every class at its published ELCC class rating
        # (2025/26 CIFP reform; P-2B Option A end-to-end basis). The official
        # final ratings pair each class's rating with its installed MW
        # (ELCC/RRS Table 5), giving a 2-point installed-MW axis. Onshore
        # wind rates 41 % at both published fleet sizes — flat over the
        # observed range, clamped at 0.41 beyond it. (PJM's preliminary
        # ER24-99 indicative table shows the marginal rating declining
        # 35 % → 19 % by 2032/33, but it is delivery-year-indexed with no
        # published MW axis — never converted here; extend when PJM
        # publishes the pairing. R3/Option-A step 3 covers thermal classes.)
        "wind": RenewableElccCurve(
            penetration_basis="installed_mw",
            points=((3549.0, 0.41), (3956.0, 0.41)),
            source=(
                "PJM 2026/27 + 2027/28 BRA final ELCC class ratings, Onshore "
                "Wind 41%/41% at 3,549/3,956 MW installed (2025 PJM ELCC/RRS "
                "Table 24 ratings, Table 5 installed MW) — "
                "data/raw/capacity-market/elcc/pjm/pjm.csv"
            ),
        ),
        # Model 'solar' = the PJM solar fleet: MW-weighted blend of the two
        # published solar classes per vintage (same-document arithmetic):
        #   2026/27: (8,713×11% + 1,189×8%) / 9,902  = 10.64 %
        #   2027/28: (11,612×8% + 1,494×7%) / 13,106 =  7.89 %
        # Declining with penetration, clamped at 0.0789 beyond 13.1 GW —
        # in line with (slightly above) the ER24-99 indicative tracking-solar
        # trajectory (~5-8 % by the early 2030s), so the clamp is the
        # conservative published anchor, not an invented slope.
        "solar": RenewableElccCurve(
            penetration_basis="installed_mw",
            points=((9902.0, 0.1064), (13106.0, 0.0789)),
            source=(
                "PJM 2026/27 + 2027/28 BRA final ELCC class ratings, "
                "Tracking Solar 11%/8% at 8,713/11,612 MW + Fixed-Tilt Solar "
                "8%/7% at 1,189/1,494 MW, MW-weighted per vintage — "
                "data/raw/capacity-market/elcc/pjm/pjm.csv"
            ),
        ),
    },
    "MISO": {
        # MISO's 2019 Wind & Solar Capacity Credit Report publishes the
        # genuine article: the adopted ("MISO Capacity Credit") class-average
        # wind accreditation by penetration as % of coincident peak, PY2010-
        # PY2020. All published points as-is (the PY2012/PY2015 pair is one
        # deduplicated point — identical x and y), including the real
        # year-to-year wiggle; sorted by penetration. Beyond 16.7 % of peak
        # the credit clamps at 0.166 — conservative against the PY2023-24 /
        # PY2025-26 seasonal marginal ELCCs (18.1-30.7 % at ~28.3 GW
        # installed, a different axis+grain, recorded in the same CSV but
        # not blended into this annual class-average curve).
        # MISO SOLAR has no published probabilistic ELCC curve (only flat
        # seasonal defaults for <30-day-metered resources) → generic
        # fallback, per the registry-level note above.
        "wind": RenewableElccCurve(
            penetration_basis="pct_of_peak_load",
            points=(
                (7.6, 0.080),
                (9.7, 0.129),
                (11.8, 0.141),
                (12.2, 0.147),
                (13.0, 0.133),
                (13.1, 0.156),
                (13.7, 0.156),
                (14.8, 0.152),
                (16.7, 0.166),
            ),
            source=(
                "MISO 2019 Wind & Solar Capacity Credit Report, Tables "
                "2-1/2-2 'MISO Capacity Credit (%)' vs 'Historical "
                "Penetration (%)' (PY2010-PY2020) — "
                "data/raw/capacity-market/elcc/miso/miso.csv"
            ),
        ),
    },
    "NYISO": {
        # NYISO publishes single current-point Capacity Accreditation
        # Factors (CAFs) per Capacity Accreditation Resource Class and
        # locality — a marginal-reliability-based rating applied to every MW
        # of the class (NYISO's adopted design), with NO penetration axis.
        # Single-point curves (constant), never a fabricated axis. Values
        # are the Rest-of-State column — the locality where nearly all NYISO
        # land-based wind and utility solar physically sits; offshore wind
        # uses Long Island, the only locality with OSW resources.
        "wind": RenewableElccCurve(
            penetration_basis=None,
            points=((0.0, 0.1684),),
            source=(
                "NYISO 2025-2026 Final CAFs (2.4.2025), land-based wind, ROS "
                "column 16.84% — data/raw/capacity-market/elcc/nyiso/nyiso.csv"
            ),
        ),
        "solar": RenewableElccCurve(
            penetration_basis=None,
            points=((0.0, 0.1224),),
            source=(
                "NYISO 2025-2026 Final CAFs (2.4.2025), solar, ROS column "
                "12.24% — data/raw/capacity-market/elcc/nyiso/nyiso.csv"
            ),
        ),
        "offshore_wind": RenewableElccCurve(
            penetration_basis=None,
            points=((0.0, 0.3579),),
            source=(
                "NYISO 2025-2026 Final CAFs (2.4.2025), offshore wind, LI "
                "column 35.79% — data/raw/capacity-market/elcc/nyiso/nyiso.csv"
            ),
        ),
    },
}

# Thermal accreditation basis for the same adequacy ledger, per ISO. Default
# (ISO absent): "ucap" = pmax x (1 - EFORd). Two published-basis alternatives:
#
# * "seasonal_rating" counts thermal at its rating with NO forced-outage
#   derate — ERCOT's CDR convention, where forced-outage risk lives in the
#   13.75% Board target margin rather than in the capacity count (the CDR's
#   "Installed Seasonal-rated Thermal Capacity" rows carry no EFORd derate).
#   Mixing UCAP-derated supply with the rating-basis 13.75% target
#   double-counts forced-outage risk (~4.4 GW on the 2026 ERCOT thermal
#   fleet). Source: December 2025 CDR, Seasonal Summary.
# * "elcc_class_rating" counts thermal at its published ELCC CLASS rating —
#   PJM's 2025/26 CIFP-reform convention, where EVERY resource class (thermal
#   included) is accredited at an ELCC-based class rating, not (1 - EFORd).
#   The per-fuel-class ratings are :data:`THERMAL_ELCC_CLASS_RATING_BY_ISO`;
#   this pairs the supply ledger with the FPR requirement (R2), which is
#   likewise stated on PJM's ELCC-reform UCAP basis (P-2B Option A per-ISO
#   published-basis consistency — accreditation-basis memo 2026-07-12 §4.1,
#   R3). Read exactly as "seasonal_rating" is by :func:`_thermal_firm_mw`.
THERMAL_ACCREDITATION_BASIS_BY_ISO: dict[str, str] = {
    "ERCOT": "seasonal_rating",
    "PJM": "elcc_class_rating",
}

# PJM thermal ELCC class ratings (2025/26 CIFP reform) — the firm fraction of
# nameplate PJM accredits each dispatchable class at, the thermal analogue of
# RENEWABLE_ELCC_CURVES_BY_ISO for the dispatchable fleet (R3, P-2B Option A
# supply basis). Consumed only for ISOs whose
# THERMAL_ACCREDITATION_BASIS_BY_ISO is "elcc_class_rating". Each value is the
# 2026/2027 BRA official/final class-average rating — the delivery-year vintage
# matching the demand-curve anchor (R1) and the requirement's near-term FPR
# (R2) — mapped to the model's fuel_type. Digitized from and reconciled against
# the committed rows (data/raw/capacity-market/elcc/pjm/pjm.csv,
# resource_class ... "2026/2027 BRA (official/final)") by
# tests/test_capacity.py — a published market-design input, never a fit target
# (rules 13/23). Classes ABSENT here fall back to UCAP (1 - EFORd), a cited
# neutral fallback (rule 25 spirit) — never a foreign rating: model 'biomass'
# has NO PJM thermal ELCC class in the 2026/27 final ratings (Waste-to-Energy
# Steam appears only in 2027/28), so it keeps UCAP. (The 2027/28 vintage moves
# these ±1-2 points — coal 83, CC 74, nuclear 95 unchanged; CT 60->61; Steam
# 73->72 — so the near-term vintage is a conservative published anchor, not an
# invented value.)
THERMAL_ELCC_CLASS_RATING_BY_ISO: dict[str, dict[str, float]] = {
    "PJM": {
        "nuclear": 0.95,  # Nuclear
        "coal": 0.83,  # Coal
        "gas_cc": 0.74,  # Gas Combined Cycle
        "gas_ct": 0.60,  # Gas Combustion Turbine
        "gas_st": 0.73,  # Steam (gas/oil steam)
        "oil": 0.91,  # Diesel Utility (the 2026/27 official oil/diesel class)
    },
}

# Load-side capacity products netted out of gross peak in the ISO's own
# firm-peak-load construction, as a fraction of the gross seasonal peak.
# ERCOT (Dec 2025 CDR Seasonal Summary, summer-2026 peak-load-hour column):
# Load Resources providing RRS 935 + Non-Spin 50 + ECRS 300 + controllable
# LRs 20 + Emergency Response Service 2,750 + TDSP standard-offer load
# management 303 + distribution voltage reduction 1,162 = 5,520 MW on the
# 95,419 MW gross seasonal peak = 5.8%. These are standing ERCOT
# demand-response programs whose enrollment scales roughly with load, so a
# fraction of peak regenerates for forward years (rule 13 admissible: a
# market-design input, not an outcome). Rooftop-PV netting is EXCLUDED —
# EIA-930 demand is already net of behind-the-meter PV. ISOs absent here
# net nothing (neutral fallback).
ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO: dict[str, float] = {
    "ERCOT": 0.058,
}

# Firm import contribution of asynchronous external ties counted by the
# ISO's own adequacy ledger but absent from the model topology (the model's
# ERCOT has no import node). ERCOT: 817 MW, "based on average net import
# contribution during the EEA events: summer 2023 and winter 2020/2021 EEA
# events" — December 2025 CDR, Seasonal Summary (non-synchronous ties row).
ADEQUACY_EXTERNAL_TIE_FIRM_MW: dict[str, float] = {
    "ERCOT": 817.0,
}

# ICAP-basis planning-reserve-margin correction (stage-5 §6 ICAP/UCAP
# pairing audit, 2026-07-06). PJM's IRM and MISO's ICAP-basis PRM in
# :data:`PLANNING_RESERVE_MARGIN_BY_ISO` are stated on INSTALLED capacity —
# each ISO's own filing pairs it with a separate UNFORCED-capacity-basis
# requirement, since the model's supply-side ledger
# (:func:`market_sim.model.capacity.accredited_firm_capacity_mw`) counts
# these ISOs' thermal fleet at UCAP (``1 - EFORd``, the registry default).
# Testing an ICAP-basis requirement against UCAP-basis supply double-counts
# forced-outage risk, the same error class the ERCOT accreditation audit
# fixed for CDR seasonal-rating vs UCAP. Values are each ISO's OWN published
# ICAP<->UCAP conversion ratio (not a model-derived pool EFORd, so nothing
# here depends on the model's own fleet mix):
#   PJM: FPR / (1 + IRM) = 0.9170 / 1.191 = 0.7699 (2026/2027 BRA planning
#     parameters — "Public Installed Reserve Margin (IRM), Forecast Pool
#     Requirement (FPR)"; FPR states the SAME required reserve level as the
#     IRM but in UCAP terms, so this ratio is the ISO's own ICAP->UCAP
#     conversion, stable year to year even as the target IRM itself moves).
#   MISO: (1 + PRM_UCAP) / (1 + PRM_ICAP) = 1.079 / 1.157 = 0.9326 (PY
#     2025-2026 LOLE Study Report, Module E-1 — Summer PRM stated both ways:
#     ICAP 15.7%, UCAP 7.9%).
# ISOs absent here are byte-identical (ratio 1.0, i.e. their registered PRM
# is already on the model's own supply basis — ERCOT's is fixed at the CDR
# seasonal-rating basis by the accreditation audit, not this registry).
PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO: dict[str, float] = {
    "PJM": 0.9170 / 1.191,
    "MISO": 1.079 / 1.157,
}

# Published Forecast Pool Requirement (FPR) per ISO and delivery year — the
# reliability requirement stated on the ISO's OWN UCAP basis as a fraction of
# forecast peak load (R2, accreditation-basis memo 2026-07-12 §4.2). PJM's
# post-CIFP FPR = (1 + IRM) x Reference-Resource Accredited-UCAP factor, so it
# already folds BOTH the reserve margin AND the ICAP->UCAP conversion into one
# published number; the UCAP requirement is simply firm_peak x FPR.
# :func:`market_sim.model.capacity.resolve_adequacy_requirement_mw` PREFERS a
# published FPR for the matching delivery year and falls back to the
# (1 + PRM) x icap_to_ucap_ratio construction otherwise (so an ISO/year absent
# here is byte-identical to the pre-R2 behaviour). Devintaging the requirement
# onto the published FPR replaces the mixed-vintage composite the fallback
# builds (PJM 1.178 x 0.7699 = 0.907 vs the published 2026/2027 FPR 0.9170).
# Values are digitized from the committed demand-curve rows
# (data/raw/capacity-market/demand-curve/pjm/pjm.csv, metric
# forecast_pool_requirement) and reconciled against them by
# tests/test_capacity.py — a published market-design input, never a fit target
# (rules 13/23). Only the post-CIFP reformed delivery years (2025/2026+) carry
# a UCAP-basis FPR; pre-reform years fall through to the fallback.
FORECAST_POOL_REQUIREMENT_BY_ISO: dict[str, dict[str, float]] = {
    "PJM": {
        "2025/2026": 0.9380,  # (1+0.178) x 0.7963; PPP posted 2024-04-08
        "2026/2027": 0.9170,  # 146,105 MW UCAP / 159,329 MW peak; PPP 2025-05-09
        "2027/2028": 0.9260,  # (1+0.200) x 0.7717; BRA report 2025-12-17
    },
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
# Generic fallback for ISOs without a published storage class-rating table of
# their own (STORAGE_ELCC_BY_DURATION_BY_ISO overrides it per ISO).
STORAGE_ELCC_BY_DURATION: list[tuple[float, float]] = [
    (2.0, 0.40),
    (4.0, 0.60),
    (6.0, 0.75),
    (8.0, 0.87),
    (10.0, 0.93),
    (12.0, 0.97),
    (24.0, 1.00),
]

# Per-ISO published storage ELCC class-rating tables, overriding the generic
# STORAGE_ELCC_BY_DURATION above for exactly the ISOs that publish their own
# duration->credit ratings (R3, P-2B Option A supply basis). PJM accredits
# storage at its published ELCC class ratings under the same 2025/26 CIFP
# reform as the thermal fleet (THERMAL_ELCC_CLASS_RATING_BY_ISO) — this is the
# ONE storage-accreditation mechanism for PJM, replacing (not stacking on) the
# generic table (rule 19, no double-derate; the marginal-ELCC saturation derate
# below still applies on top, as it does for every ISO). Values are the
# 2026/2027 BRA official/final storage class ratings (matching the thermal
# vintage), digitized from and reconciled against the committed rows
# (data/raw/capacity-market/elcc/pjm/pjm.csv, "N-hr Storage" resource classes)
# by tests/test_capacity.py. Notably LOWER than the generic NREL/E3 curve
# (PJM 4h 0.50 vs 0.60, 8h 0.62 vs 0.87) — the reformed market's own numbers,
# not a fit. Endpoints clamp: below 4h at the 4h rating, above 10h at the 10h
# rating (PJM publishes 4/6/8/10-hr; no 2h or >10h class), consistent with the
# generic table's flat-clamp behaviour.
STORAGE_ELCC_BY_DURATION_BY_ISO: dict[str, list[tuple[float, float]]] = {
    "PJM": [
        (4.0, 0.50),
        (6.0, 0.58),
        (8.0, 0.62),
        (10.0, 0.72),
    ],
}

# Marginal ELCC saturation. As cumulative storage power approaches the
# deployment ceiling (≈ half the system peak), each additional MW of storage
# adds less firm capacity — the well-documented decline in marginal storage
# ELCC at high penetration, which is what tilts the economics from short-
# toward long-duration storage. The marginal credit is multiplied by
# ``(1 - penetration)^STORAGE_ELCC_SATURATION_EXPONENT`` where ``penetration``
# is existing storage power / ceiling. Source: NREL ELCC saturation studies.
STORAGE_ELCC_SATURATION_EXPONENT: float = 1.5

# Portfolio (aggregate accreditation) ELCC dilution — the CDR's own
# fleet-average BESS ELCC compresses as storage penetration grows (ERCOT
# accreditation audit, 2026-07-06, §3): "model 2026 storage firm 11.7 GW vs
# the CDR-implied 12.3 GW (operational + planned, ELCC 60.2% on 20,438 MW
# installed) — close at fleet level," with the flagged follow-up "the CDR's
# own BESS ELCC dilutes 60% -> 46% by 2030 as penetration triples." Modeled
# in ``capacity.py::_storage_portfolio_elcc_dilution`` as a LINEAR
# interpolation between the two cited (penetration, ELCC) anchors — no
# fitted exponent, no guessed intermediate MW: at the reference MW below
# (today's validated point) the dilution factor is 1.0 (the audit's "close
# at fleet level today" finding, unchanged); at full deployment-ceiling
# penetration it is the CDR's own ratio, 46/60.2 (below); in between it is
# a straight line between those two real data points. ISOs absent from
# either registry get no dilution (byte-identical).
STORAGE_ELCC_DILUTION_REFERENCE_MW_BY_ISO: dict[str, float] = {
    "ERCOT": 20_438.0,  # Dec 2025 CDR: operational + CDR-eligible planned BESS
    # nameplate MW, the installed base the audit's 60.2% portfolio ELCC is
    # reported against.
}

# The CDR's own fleet-average BESS ELCC ratio at full deployment-ceiling
# penetration relative to the reference-MW ELCC above: 46% / 60.2% (accred-
# itation audit §3, "dilutes 60% -> 46% by 2030"). A floor, not a fitted
# curve — the model has no CDR data point between the two cited years, so
# the dilution factor is linear between them (see the reference-MW
# registry's docstring); this is the value the line reaches at penetration
# = 1.0, not a value asserted to land exactly in 2030.
STORAGE_ELCC_DILUTION_CEILING_RATIO_BY_ISO: dict[str, float] = {
    "ERCOT": 0.46 / 0.602,
}

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

# RPS Alternative Compliance Payment (ACP) ceiling, $/MWh, by ISO.
#
# Every real RPS/CES carries an ACP (or an equivalent non-compliance penalty):
# a load-serving entity short of physical RECs pays the ACP rate per deficient
# MWh instead of the standard physically failing. The ACP is therefore the
# price ceiling of the REC market — the marginal cost of the last unit of
# compliance — so the model enters it as the cost of an RPS ACP escape column
# (dispatch.build_cost_vector), which both keeps the annual RPS row feasible
# when in-region wind+solar cannot reach the target and caps the row's dual
# (the REC shadow price) at this ceiling. Rule 13 admissible: a published policy
# parameter that regenerates for any forecast year and responds to conditions
# (as the fleet builds VRE the escape goes unused and the dual falls below it).
# Tier 3 (calibration) — verify against each state's current ACP schedule.
# Sources:
#   CAISO — CA RPS non-compliance penalty $50/MWh (Pub. Util. Code §399.15;
#     CPUC RPS enforcement), the effective ACP ceiling for SB 100 compliance.
#   NYISO — NY Clean Energy Standard Tier 1 ACP (NYSERDA/PSC Case 15-E-0302);
#     ~$40/MWh order of magnitude for recent compliance years.
#   NEISO — MA Class I RPS ACP ($67.62/MWh, 2024, 225 CMR 14.08) blended with
#     CT Class I ($55/MWh, Conn. Gen. Stat. §16-245a) across the six-state
#     region; ~$65/MWh regional Class I ACP.
# ISOs without a STATE_RPS_FLOORS entry (ERCOT, PJM) need no ACP — their RPS row
# is never built, so the escape column is absent and the LP is byte-identical.
STATE_RPS_ACP: dict[str, float] = {
    "CAISO": 50.0,
    "NYISO": 40.0,
    "NEISO": 65.0,
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
# Crosswalk provenance and reconciliation (CLAUDE.md rule 14 exception
# clause — each static seed's series maps back to it 1:1):
#   - ComEd→AEP_Ohio      ← "50045005": iso_configs already names this link
#     "the 5004/5005 interface"; the static 6000 was a loose estimate
#     (measured mean ~2,750-3,100).
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
# scripts/curate_transfer_interface_limits.py; consumed by
# market_sim.data.transfer_interface_limits.pjm_interface_ttc_hourly.
PJM_INTERFACE_LINK_MAP: dict[tuple[str, str], tuple[str, ...]] = {
    ("PJM_ComEd", "PJM_AEP_Ohio"): ("50045005 Post-Contingency",),
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
    # CAISO (BA "CISO"): api.eia.gov (scripts/fetch_eia930_hourly.py) is
    # blocked in this managed sandbox, but the six-month BALANCE bulk archive
    # (www.eia.gov, unblocked) covers 2019-2021 for every BA and was fetched
    # 2026-07-06 (scripts/fetch_eia930_balance.py) then folded into the wide
    # hourly extract (scripts/extend_eia930_hourly_from_balance.py). 2019-2021
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
            0.6110,
            0.5678,
            0.5251,
            0.4928,
            0.4435,
            0.3979,
            0.3429,
            0.2934,
            0.2679,
            0.1621,
        ),
        (
            0.5876,
            0.5444,
            0.5153,
            0.4647,
            0.4135,
            0.3837,
            0.3597,
            0.3364,
            0.2798,
            0.2338,
        ),
        (
            0.5964,
            0.5105,
            0.5159,
            0.5149,
            0.5026,
            0.4625,
            0.4130,
            0.3471,
            0.2531,
            0.1866,
        ),
        (
            0.5844,
            0.5158,
            0.5115,
            0.4651,
            0.4190,
            0.3804,
            0.3382,
            0.2851,
            0.2255,
            0.1562,
        ),
    ),
    "CC_REGULAR": (
        (
            0.2387,
            0.2454,
            0.2403,
            0.2314,
            0.2145,
            0.1876,
            0.1626,
            0.1443,
            0.1349,
            0.1079,
        ),
        (
            0.2209,
            0.2673,
            0.2670,
            0.2466,
            0.2234,
            0.2150,
            0.2028,
            0.1923,
            0.1781,
            0.1335,
        ),
        (
            0.2800,
            0.2888,
            0.2789,
            0.2254,
            0.1995,
            0.1732,
            0.1415,
            0.1167,
            0.0941,
            0.0718,
        ),
        (
            0.2532,
            0.2543,
            0.2543,
            0.2356,
            0.2052,
            0.1857,
            0.1652,
            0.1438,
            0.1112,
            0.0757,
        ),
    ),
    "CC_CHP": (
        (
            0.3011,
            0.2446,
            0.2092,
            0.1718,
            0.1483,
            0.1303,
            0.1161,
            0.0979,
            0.0884,
            0.0680,
        ),
        (
            0.2813,
            0.2435,
            0.2188,
            0.1988,
            0.1822,
            0.1728,
            0.1594,
            0.1565,
            0.1353,
            0.1069,
        ),
        (
            0.1580,
            0.1453,
            0.1546,
            0.1257,
            0.1209,
            0.1085,
            0.0965,
            0.0776,
            0.0686,
            0.0607,
        ),
        (
            0.2829,
            0.2541,
            0.2360,
            0.2094,
            0.1770,
            0.1582,
            0.1382,
            0.0972,
            0.0724,
            0.0620,
        ),
    ),
    "CT_PEAKER": (
        (
            0.0136,
            0.0147,
            0.0196,
            0.0232,
            0.0290,
            0.0414,
            0.0714,
            0.1155,
            0.1349,
            0.1467,
        ),
        (
            0.0329,
            0.0450,
            0.0489,
            0.0619,
            0.0975,
            0.0997,
            0.1494,
            0.1873,
            0.2406,
            0.2386,
        ),
        (
            0.0274,
            0.0312,
            0.0295,
            0.0108,
            0.0146,
            0.0144,
            0.0223,
            0.0333,
            0.0884,
            0.1085,
        ),
        (
            0.0378,
            0.0393,
            0.0410,
            0.0423,
            0.0425,
            0.0483,
            0.0476,
            0.0441,
            0.1176,
            0.1283,
        ),
    ),
    "CT_CHP": (
        (
            0.0454,
            0.0343,
            0.0325,
            0.0282,
            0.0242,
            0.0186,
            0.0233,
            0.0171,
            0.0162,
            0.0392,
        ),
        (
            0.0498,
            0.0559,
            0.0696,
            0.0747,
            0.0727,
            0.0797,
            0.0832,
            0.0819,
            0.0812,
            0.0612,
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
            0.0355,
            0.0436,
            0.0390,
            0.0273,
            0.0231,
            0.0200,
            0.0205,
            0.0187,
            0.0152,
        ),
    ),
    "ST_GAS": (
        (
            0.0211,
            0.0211,
            0.0211,
            0.0724,
            0.1054,
            0.1017,
            0.1228,
            0.1786,
            0.3014,
            0.3539,
        ),
        (
            0.1314,
            0.1703,
            0.2491,
            0.2929,
            0.3013,
            0.3309,
            0.3332,
            0.3595,
            0.3663,
            0.3060,
        ),
        (
            0.1455,
            0.1454,
            0.3084,
            0.3393,
            0.4066,
            0.4537,
            0.5087,
            0.5255,
            0.4477,
            0.3141,
        ),
        (
            0.2501,
            0.2631,
            0.2866,
            0.2989,
            0.3610,
            0.3833,
            0.4191,
            0.4472,
            0.4350,
            0.3384,
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
            0.9361,
            0.9231,
            0.9055,
            0.8762,
            0.8365,
            0.7448,
            0.6469,
            0.5350,
        ),
        (
            0.9257,
            0.9031,
            0.8851,
            0.8502,
            0.7932,
            0.7540,
            0.5987,
            0.5718,
            0.4462,
            0.2842,
        ),
        (
            0.8100,
            0.7987,
            0.7923,
            0.8307,
            0.8076,
            0.7925,
            0.7923,
            0.7648,
            0.6445,
            0.3691,
        ),
        (
            0.9212,
            0.9031,
            0.9031,
            0.8570,
            0.8307,
            0.7903,
            0.7713,
            0.7688,
            0.6208,
            0.3615,
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
            0.6578,
            0.6759,
            0.6759,
            0.6759,
            0.6759,
            0.6759,
            0.6759,
            0.6759,
            0.6759,
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
ERCOT_RTOLCAP_FWD_DELIV_COEF: float = 0.8959
# Off-line deliverability coefficient: fit to the measured RTOFFCAP MW quantity
# (off-line startable quick-start capacity clears a smaller reserve fraction than
# the on-line fit). Not a price.
ERCOT_RTOLCAP_FWD_OFFLINE_DELIV_COEF: float = 0.7756
# Forward on-line storage responsive-reserve fraction of installed storage power
# (ERCOT observed AS-award / installed-storage ~0.35 across 2023-2025). FORECAST
# only; in backcast the storage term reads the measured storage-AS series
# (mode-aware, like the G4 load-resource credit).
ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC: float = 0.35

# --- ERCOT on-line-CAPACITY envelope (G-22 commitment thinness) ---------------
# The committed on-line HSL fraction per responsive class, conditioned on the
# same net-load-decile x season axes as ERCOT_RTOLCAP_FWD_ONLINE_SHARE above.
# Where the RTOLCAP share is the on-line *headroom* (HSL - gross), this is the
# on-line *capacity* (HSL) fraction itself. The on-line-capacity envelope
# (scarcity.ercot_online_capacity_envelope_mw, gated ercot_online_capacity_envelope)
# caps the multi-product co-opt's shared-headroom ENERGY+RESERVE at
#     online_cap_env(t) = ERCOT_ONLINE_CAP_DELIV_COEF
#                         x Sum_c ERCOT_ONLINE_CAP_SHARE_c[season,decile] x cap_c(t)
# so the LP cannot dispatch or reserve more thermal than the real system had
# on-line -- removing the ~3.2 GW phantom sub-$200 spare P1 perfect commitment
# manufactures beyond measured RTOLCAP (FINDING-ercot-priceshape-2026-07 §3,
# structural conclusion #2). Derived by
# scripts/derive_ercot_rtolcap_forward.py --emit online-cap-constant from the
# committed CAMPD unit extracts (Sum_online eff_cap / installed_cap, pooled-year
# median). Rule #23: re-derives only on a CAMPD / measured-RTOLCAP source-data
# update, never a residual. Identification (envelope - gross reproduces measured
# RTOLCAP level/band/coverage) gated by scripts/validate_ercot_online_capacity.py.

# Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON);
# each inner tuple is the 10 net-load-percentile deciles (low→high).
ERCOT_ONLINE_CAP_SHARE: dict[str, tuple[tuple[float, ...], ...]] = {
    "COAL": (
        (
            0.9525,
            0.9717,
            0.9717,
            0.9717,
            0.9717,
            0.9717,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
        ),
        (
            0.9242,
            0.9242,
            0.9242,
            0.9242,
            0.9242,
            0.9025,
            0.9025,
            0.9525,
            0.9025,
            0.8776,
        ),
        (
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
        ),
        (
            0.9242,
            0.9242,
            0.9717,
            0.9717,
            0.9717,
            0.9717,
            0.9717,
            1.0000,
            1.0000,
            1.0000,
        ),
    ),
    "CC_REGULAR": (
        (
            0.4194,
            0.4974,
            0.5762,
            0.6525,
            0.6991,
            0.7315,
            0.7453,
            0.7777,
            0.8339,
            0.8900,
        ),
        (
            0.3933,
            0.5444,
            0.6376,
            0.6859,
            0.7083,
            0.7428,
            0.7731,
            0.8237,
            0.8523,
            0.8657,
        ),
        (
            0.5756,
            0.5925,
            0.6462,
            0.6657,
            0.7004,
            0.7300,
            0.7449,
            0.7628,
            0.7809,
            0.8097,
        ),
        (
            0.4370,
            0.5380,
            0.6202,
            0.6651,
            0.6797,
            0.7212,
            0.7458,
            0.7743,
            0.7848,
            0.8107,
        ),
    ),
    "CC_CHP": (
        (
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
        ),
        (
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
        ),
        (
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
        ),
        (
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6480,
            0.6383,
            0.6249,
            0.6249,
            0.6249,
        ),
    ),
    "CT_PEAKER": (
        (
            0.0507,
            0.0507,
            0.0639,
            0.0769,
            0.0945,
            0.1230,
            0.1641,
            0.2533,
            0.3536,
            0.4567,
        ),
        (
            0.0753,
            0.0969,
            0.1176,
            0.1490,
            0.2066,
            0.2440,
            0.3768,
            0.4296,
            0.5450,
            0.7131,
        ),
        (
            0.0650,
            0.0763,
            0.0443,
            0.0443,
            0.0827,
            0.0827,
            0.0847,
            0.1148,
            0.2158,
            0.4981,
        ),
        (
            0.0945,
            0.0969,
            0.0969,
            0.1037,
            0.1185,
            0.1234,
            0.1411,
            0.1257,
            0.2657,
            0.5198,
        ),
    ),
    "CT_CHP": (
        (
            0.3241,
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3698,
            0.3698,
        ),
        (
            0.3331,
            0.3241,
            0.3241,
            0.3241,
            0.3241,
            0.3241,
            0.3241,
            0.3241,
            0.3241,
            0.3503,
        ),
        (
            0.3065,
            0.3065,
            0.3065,
            0.2994,
            0.2994,
            0.2994,
            0.2994,
            0.2994,
            0.2994,
            0.3236,
        ),
        (
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3236,
            0.3236,
            0.3503,
        ),
    ),
    "ST_GAS": (
        (
            0.0228,
            0.0228,
            0.0228,
            0.1153,
            0.1153,
            0.1429,
            0.1734,
            0.2880,
            0.5149,
            0.8842,
        ),
        (
            0.1602,
            0.2592,
            0.3493,
            0.4078,
            0.4598,
            0.5093,
            0.5788,
            0.6631,
            0.7193,
            0.8014,
        ),
        (
            0.1734,
            0.1734,
            0.3117,
            0.4077,
            0.4818,
            0.6042,
            0.6791,
            0.7454,
            0.8204,
            0.9105,
        ),
        (
            0.2819,
            0.3269,
            0.3631,
            0.3975,
            0.5241,
            0.5730,
            0.6396,
            0.6782,
            0.7822,
            0.8796,
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
# Envelope deliverability coefficient: fit to reproduce the measured on-line HSL
# MW quantity (CAMPD on-line gross + measured thermal RTOLCAP) in the BINDING
# REGIME (top-30% net-load hours), on the PRODUCTION cap basis (model
# FleetArrays pmax by responsive plant_group + summer derate, matching
# scarcity.ercot_online_capacity_envelope_mw exactly — the derive's own
# CAMPD-nameplate class cap runs ~20-30% too tight in the LP). The binding regime
# is where the envelope is not slack and its reproduction of the measured RTOLCAP
# capability decides whether the co-opt tightens. A whole-year fit reproduces the
# annual mean but lets the pooled-median share undershoot the *committable*
# capacity in the tight tail (room collapses far below measured RTOLCAP ->
# over-fire); the envelope is a CAP (upper bound on what can be on-line), so it
# is fit where it binds. On this basis the binding regime reproduces measured
# RTOLCAP within -1/+2/-1% (2023/24/25); the slack hours (over-reproduced) never
# reach the LP because the ENERGY term keeps the envelope slack there. With the
# model's unconstrained thermal dispatch ~= measured CAMPD gross in these hours
# (verified on the control arm, within 0.2-1.4 GW), the resulting in-LP on-line
# room reproduces measured RTOLCAP + ~1 GW. A measured-MW-quantity fit to the
# RTOLCAP band, never a price (rule #13).
ERCOT_ONLINE_CAP_DELIV_COEF: float = 1.0830

# --- ERCOT EXTREME-PEAK-RESOLVED on-line-capacity envelope (G-22, §5 path) ----
# The filed forward path after the ercot41 rejection (docs/handoffs/
# ercot-online-capacity-envelope-2026-07.md §5): the base envelope reproduced
# measured RTOLCAP in the binding regime (+-2%) but its pooled decile-9 share
# median under-stated the committable capacity in the top-2% net-load hours, so
# the in-LP room collapsed (4.4/6.7 GW vs measured 8.0/11.1 in 2023/24) and the
# ORDC over-fired. Two refinements, both identified on measured MW quantities
# (rules #13/#14/#23 -- never a price), derived by
# scripts/derive_ercot_rtolcap_forward.py --emit online-cap-extreme-constant:
#
# 1. SHAPE -- ERCOT_ONLINE_CAP_SHARE_EXTREME resolves the committed on-line HSL
#    fraction on 14 net-load bins (deciles 0-8 + five 2-percentile sub-bins of
#    the top decile, scarcity.ercot_online_cap_extreme_bin). The measured CAMPD
#    commitment saturation rises through the sub-bins (summer CT_PEAKER
#    0.40->0.61, ST_GAS 0.83->0.97) where the single decile-9 median collapsed
#    it. Sub-bin cells with < 24 pooled hours across the source years (one
#    diurnal cycle; the spring top-decile is that thin) inherit the parent
#    decile-9 same-season median -- a hierarchical coarsening, never a new
#    number.
# 2. LEVEL -- ERCOT_ONLINE_CAP_DELIV_PROFILE_EXTREME replaces the scalar
#    deliverability with a per-bin profile: deliv_b = pooled_mean_b(target) /
#    pooled_mean_b(share-composite on the production cap basis), where
#        target(t) = CAMPD on-line gross(t)
#                    + (measured RTOLCAP(t) - storage AS(t) - LR credit(t)),
#    the measured THERMAL on-line HSL identity. The same ratio-of-means
#    identification as the base deliv fit, resolved on the same axis as the
#    share, because a single scalar provably cannot carry the capability margin
#    that GROWS toward the extreme peak: after netting the measured storage-AS
#    and load-resource series (both already credited against the requirement in
#    the keeper LP -- keeping them in a THERMAL cap would double-count),
#    measured thermal RTOLCAP still exceeds the CAMPD share-reconstruction by
#    ~2.3-3.4 GW in the top-2% (non-CEMS capability + telemetered HSL above the
#    summer-derated nameplate, exactly where scarcity operations muster
#    everything). The profile is monotone-rising through the binding bins
#    (1.05 -> 1.10), the measured signature of that margin.
#
# Identification (validate_ercot_online_capacity.py --extreme): headroom
# remainder reproduces measured RTOLCAP in the binding regime at -0/+3/-2%
# (2023/24/25) AND in the top-2% extreme tail at -23/-2/+18% -- the pooled
# top-bin mean is exact by construction; the per-year spread is the cross-year
# capability difference at a fixed within-year rank (2023's scarcity summer
# mustered more absolute capability than 2025's milder tail), which a
# year-symmetric pooled coefficient cannot span without year-pinning
# (forbidden). Recorded as the residual ledger, not tuned.
# Rule #23: re-derives only on a CAMPD / measured-RTOLCAP / storage-AS /
# LR-credit source-data update, never a residual.

# Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON);
# each inner tuple is the 14 extreme-resolved net-load bins (deciles 0-8 +
# five 2-pp sub-bins of the top decile, low->high).
ERCOT_ONLINE_CAP_SHARE_EXTREME: dict[str, tuple[tuple[float, ...], ...]] = {
    "COAL": (
        (
            0.9525,
            0.9717,
            0.9717,
            0.9717,
            0.9717,
            0.9717,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
        ),
        (
            0.9242,
            0.9242,
            0.9242,
            0.9242,
            0.9242,
            0.9025,
            0.9025,
            0.9525,
            0.9025,
            0.8776,
            0.8776,
            0.8776,
            0.8776,
            0.8776,
        ),
        (
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
        ),
        (
            0.9242,
            0.9242,
            0.9717,
            0.9717,
            0.9717,
            0.9717,
            0.9717,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
        ),
    ),
    "CC_REGULAR": (
        (
            0.4194,
            0.4974,
            0.5762,
            0.6525,
            0.6991,
            0.7315,
            0.7453,
            0.7777,
            0.8339,
            0.8655,
            0.8840,
            0.8833,
            0.8921,
            0.9040,
        ),
        (
            0.3933,
            0.5444,
            0.6376,
            0.6859,
            0.7083,
            0.7428,
            0.7731,
            0.8237,
            0.8523,
            0.8657,
            0.8657,
            0.8657,
            0.8657,
            0.8657,
        ),
        (
            0.5756,
            0.5925,
            0.6462,
            0.6657,
            0.7004,
            0.7300,
            0.7449,
            0.7628,
            0.7809,
            0.7968,
            0.7999,
            0.7999,
            0.8177,
            0.8293,
        ),
        (
            0.4370,
            0.5380,
            0.6202,
            0.6651,
            0.6797,
            0.7212,
            0.7458,
            0.7743,
            0.7848,
            0.7955,
            0.8106,
            0.8051,
            0.8212,
            0.8293,
        ),
    ),
    "CC_CHP": (
        (
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
        ),
        (
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
        ),
        (
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
        ),
        (
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6943,
            0.6480,
            0.6383,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
            0.6249,
        ),
    ),
    "CT_PEAKER": (
        (
            0.0507,
            0.0507,
            0.0639,
            0.0769,
            0.0945,
            0.1230,
            0.1641,
            0.2533,
            0.3536,
            0.3711,
            0.4197,
            0.4486,
            0.4267,
            0.5636,
        ),
        (
            0.0753,
            0.0969,
            0.1176,
            0.1490,
            0.2066,
            0.2440,
            0.3768,
            0.4296,
            0.5450,
            0.7131,
            0.7131,
            0.7131,
            0.7131,
            0.7131,
        ),
        (
            0.0650,
            0.0763,
            0.0443,
            0.0443,
            0.0827,
            0.0827,
            0.0847,
            0.1148,
            0.2158,
            0.3950,
            0.4509,
            0.4891,
            0.5204,
            0.6108,
        ),
        (
            0.0945,
            0.0969,
            0.0969,
            0.1037,
            0.1185,
            0.1234,
            0.1411,
            0.1257,
            0.2657,
            0.4120,
            0.4845,
            0.5022,
            0.5680,
            0.6151,
        ),
    ),
    "CT_CHP": (
        (
            0.3241,
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3698,
            0.3503,
            0.3503,
            0.3698,
            0.3503,
            0.3698,
        ),
        (
            0.3331,
            0.3241,
            0.3241,
            0.3241,
            0.3241,
            0.3241,
            0.3241,
            0.3241,
            0.3241,
            0.3503,
            0.3503,
            0.3503,
            0.3503,
            0.3503,
        ),
        (
            0.3065,
            0.3065,
            0.3065,
            0.2994,
            0.2994,
            0.2994,
            0.2994,
            0.2994,
            0.2994,
            0.3065,
            0.3065,
            0.3236,
            0.3490,
            0.3490,
        ),
        (
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3422,
            0.3236,
            0.3236,
            0.3236,
            0.3576,
            0.3648,
            0.3648,
            0.3648,
        ),
    ),
    "ST_GAS": (
        (
            0.0228,
            0.0228,
            0.0228,
            0.1153,
            0.1153,
            0.1429,
            0.1734,
            0.2880,
            0.5149,
            0.7454,
            0.8157,
            0.8842,
            0.7894,
            0.9282,
        ),
        (
            0.1602,
            0.2592,
            0.3493,
            0.4078,
            0.4598,
            0.5093,
            0.5788,
            0.6631,
            0.7193,
            0.8014,
            0.8014,
            0.8014,
            0.8014,
            0.8014,
        ),
        (
            0.1734,
            0.1734,
            0.3117,
            0.4077,
            0.4818,
            0.6042,
            0.6791,
            0.7454,
            0.8204,
            0.8756,
            0.8842,
            0.9105,
            0.9241,
            0.9681,
        ),
        (
            0.2819,
            0.3269,
            0.3631,
            0.3975,
            0.5241,
            0.5730,
            0.6396,
            0.6782,
            0.7822,
            0.8092,
            0.8842,
            0.8780,
            0.8842,
            0.9418,
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
            0.0000,
            0.0000,
            0.0000,
            0.0000,
        ),
    ),
}
# Per-bin deliverability profile (14 extreme-resolved net-load bins, low->high;
# construction/identification documented in the block comment above).
ERCOT_ONLINE_CAP_DELIV_PROFILE_EXTREME: tuple[float, ...] = (
    1.0105,
    0.9383,
    0.9367,
    0.9541,
    0.9773,
    1.0030,
    1.0295,
    1.0518,
    1.0731,
    1.0715,
    1.0741,
    1.0752,
    1.0889,
    1.1004,
)

# --- ERCOT MEASURED-FLEET-BASIS on-line-capacity envelope (ercot57 joint) -----
# The joint-round re-identification of the G-22 envelope on the measured fleet
# (owner-sanctioned 2026-07-11; ERCOT-57 calibration-log entry): the ercot41/43
# A/Bs ran on the phantom-tight statistical availability stack, and their share
# tables (committed on-line HSL / INSTALLED capacity) conflate the commitment
# choice with the outage state — in the extreme tail reality musters near-max
# availability, so a pooled share-of-installed under-states committable
# capacity exactly there (the ercot43 top-2% room collapse, 2023 ledger −23%).
# This basis decomposes them for the measured-availability classes
# (ERCOT_ONLINE_CAP_MEASURED_AVAIL_CLASSES, the 60-Day-DAM disclosure deriver's
# scope): share = committed on-line HSL ÷ MEASURED AVAILABLE capacity (the
# class-day disclosure fraction × installed), and the LP basis is the fleet's
# finished availability (measured under ercot_thermal_dam_availability in
# backcast; the statistical stack forward — the G4 mode-aware seam). Uncovered
# classes keep the extreme variant's installed × summer-derate basis. Derived
# by scripts/derive_ercot_rtolcap_forward.py --emit online-cap-measured-constant;
# identification gate scripts/validate_ercot_online_capacity.py --measured.
# Rule #23: re-derives only on a disclosure / CAMPD / measured-RTOLCAP /
# storage-AS / LR-credit source-data update, never a residual (this derivation
# cites the data/raw/ercot-thermal-dam-availability.csv intake, ERCOT-57).
ERCOT_ONLINE_CAP_MEASURED_AVAIL_CLASSES: tuple[str, ...] = (
    "CC_REGULAR",
    "CT_PEAKER",
)
# Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON);
# each inner tuple is the 14 extreme-resolved net-load bins (deciles 0-8 + five 2-pp sub-bins of the top decile, low->high).
ERCOT_ONLINE_CAP_SHARE_MEASURED: dict[str, tuple[tuple[float, ...], ...]] = {
    "COAL": (
        (
            0.9525,
            0.9717,
            0.9717,
            0.9717,
            0.9717,
            0.9717,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
        ),
        (
            0.9242,
            0.9242,
            0.9242,
            0.9242,
            0.9242,
            0.9025,
            0.9025,
            0.9525,
            0.9025,
            0.8776,
            0.8776,
            0.8776,
            0.8776,
            0.8776,
        ),
        (
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
        ),
        (
            0.9242,
            0.9242,
            0.9717,
            0.9717,
            0.9717,
            0.9717,
            0.9717,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
            1.0000,
        ),
    ),
    "CC_REGULAR": (
        (
            0.4737,
            0.5700,
            0.6493,
            0.7323,
            0.8063,
            0.8379,
            0.8588,
            0.8964,
            0.9292,
            0.9450,
            0.9451,
            0.9459,
            0.9449,
            0.9451,
        ),
        (
            0.6566,
            0.8758,
            0.9929,
            1.0565,
            1.0655,
            1.0755,
            1.0946,
            1.1108,
            1.1104,
            1.1082,
            1.1082,
            1.1082,
            1.1082,
            1.1082,
        ),
        (
            0.6882,
            0.8102,
            0.8305,
            0.8329,
            0.8566,
            0.8741,
            0.8874,
            0.9031,
            0.9210,
            0.9422,
            0.9422,
            0.9449,
            0.9428,
            0.9469,
        ),
        (
            0.6999,
            0.8488,
            0.9181,
            0.9692,
            0.9596,
            0.9515,
            0.9245,
            0.9153,
            0.9229,
            0.9409,
            0.9367,
            0.9360,
            0.9330,
            0.9299,
        ),
    ),
    "CC_CHP": (
        (
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
        ),
        (
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
        ),
        (
            0.7204,
            0.7204,
            0.7204,
            0.7204,
            0.7204,
            0.7204,
            0.7204,
            0.7204,
            0.7204,
            0.7204,
            0.7204,
            0.7204,
            0.7204,
            0.7204,
        ),
        (
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.8005,
            0.7445,
            0.7445,
            0.7204,
            0.7204,
            0.7204,
            0.7204,
            0.7204,
            0.7204,
            0.7204,
        ),
    ),
    "CT_PEAKER": (
        (
            0.0570,
            0.0583,
            0.0688,
            0.0781,
            0.1040,
            0.1288,
            0.1815,
            0.2583,
            0.3740,
            0.4045,
            0.4595,
            0.4803,
            0.4741,
            0.6330,
        ),
        (
            0.1014,
            0.1330,
            0.1542,
            0.2060,
            0.2805,
            0.3246,
            0.5339,
            0.5416,
            0.6927,
            0.9233,
            0.9233,
            0.9233,
            0.9233,
            0.9233,
        ),
        (
            0.0809,
            0.0951,
            0.1032,
            0.0573,
            0.0821,
            0.0972,
            0.1017,
            0.1372,
            0.2733,
            0.4882,
            0.5392,
            0.5930,
            0.6387,
            0.7475,
        ),
        (
            0.1249,
            0.1268,
            0.1325,
            0.1344,
            0.1438,
            0.1590,
            0.1451,
            0.1356,
            0.3024,
            0.5194,
            0.5845,
            0.6307,
            0.6937,
            0.7466,
        ),
    ),
    "CT_CHP": (
        (
            0.3843,
            0.4117,
            0.4117,
            0.4117,
            0.4117,
            0.4117,
            0.4117,
            0.4117,
            0.4645,
            0.4335,
            0.4645,
            0.4490,
            0.4335,
            0.4645,
        ),
        (
            0.4117,
            0.3843,
            0.3843,
            0.3843,
            0.3843,
            0.3843,
            0.3843,
            0.4117,
            0.3843,
            0.4089,
            0.4089,
            0.4089,
            0.4089,
            0.4089,
        ),
        (
            0.3794,
            0.3794,
            0.3794,
            0.3603,
            0.3603,
            0.3603,
            0.3603,
            0.3603,
            0.3603,
            0.3794,
            0.3794,
            0.4064,
            0.4357,
            0.4357,
        ),
        (
            0.4117,
            0.4117,
            0.4117,
            0.4117,
            0.4117,
            0.4117,
            0.4117,
            0.4064,
            0.4064,
            0.4357,
            0.4357,
            0.4597,
            0.4597,
            0.4357,
        ),
    ),
    "ST_GAS": (
        (
            0.0228,
            0.0228,
            0.0228,
            0.1153,
            0.1153,
            0.1248,
            0.1734,
            0.2898,
            0.5741,
            0.7805,
            0.8973,
            0.8973,
            0.8026,
            0.9545,
        ),
        (
            0.1602,
            0.2592,
            0.3400,
            0.4153,
            0.4490,
            0.5154,
            0.5610,
            0.6631,
            0.7184,
            0.8014,
            0.8014,
            0.8014,
            0.8014,
            0.8014,
        ),
        (
            0.1734,
            0.1734,
            0.3496,
            0.4077,
            0.4886,
            0.5796,
            0.6791,
            0.7717,
            0.8204,
            0.8756,
            0.9105,
            0.9105,
            0.9418,
            0.9681,
        ),
        (
            0.2865,
            0.3269,
            0.3631,
            0.4073,
            0.5097,
            0.5904,
            0.6426,
            0.6704,
            0.7822,
            0.8357,
            0.8780,
            0.8780,
            0.8780,
            0.9418,
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
            0.0000,
            0.0000,
            0.0000,
            0.0000,
        ),
    ),
}
ERCOT_ONLINE_CAP_DELIV_PROFILE_MEASURED: tuple[float, ...] = (
    0.9254,
    0.8582,
    0.8686,
    0.8733,
    0.8944,
    0.9271,
    0.9527,
    0.9642,
    0.9743,
    0.9701,
    0.9700,
    0.9738,
    0.9838,
    0.9933,
)

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
