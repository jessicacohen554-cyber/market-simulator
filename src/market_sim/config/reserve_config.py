"""Unified reserve co-optimization configuration and dispatch-kwargs builder.

Replaces the 6 per-ISO ``*_reserve_coopt_inputs()`` functions in
``results/scarcity.py`` and the 200-line ``if/elif`` ISO dispatch chain in
``runner.py`` with a single config-driven system. Every ISO's reserve physics
is ported into a per-ISO private helper that produces a ``ReserveDesign``;
``build_reserve_dispatch_kwargs`` converts it into the dict that
``dispatch.py`` (``_build_reserve_rows``) consumes. The LP builder is
untouched — mathematical results are byte-identical for all 6 ISOs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from market_sim.config.constants import ERCOT_AS_PLAN_HOLD_EPS, MISO_RPE_DEMAND_VALUE
from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

# ---------------------------------------------------------------------------
# Reserve-product constants (moved from config/constants.py)
# ---------------------------------------------------------------------------

RESERVE_FUEL_TYPES: frozenset[str] = frozenset(
    {"gas_cc", "gas_ct", "gas_st", "coal", "nuclear", "oil"}
)

QUICK_START_FUEL_TYPES: frozenset[str] = frozenset({"gas_ct", "oil"})

NYISO_SPIN_FRACTION: float = 0.5

NYISO_DOWNSTATE_SPIN_ZONES: frozenset[str] = frozenset({"NYC"})

# ERCOT multi-product AS products: (display_name, ASPLANNP433_code, tier).
ERCOT_AS_PRODUCTS: tuple[tuple[str, str, str], ...] = (
    ("RegUp", "REGUP", "fast"),
    ("RRS", "RRS", "fast"),
    ("ECRS", "ECRS", "fast"),
    ("NonSpin", "NSPIN", "all"),
)

# Per-product sustained-delivery duration (hours), INDEX-ALIGNED with
# ERCOT_AS_PRODUCTS above (RegUp, RRS, ECRS, Non-Spin). This is the energy an
# Energy Storage Resource (ESR) must have available to cover an AS award for
# its full deployment duration — ERCOT's State-of-Charge (SOC) requirement: at
# the start of any hour with a discharging AS award, the ESR must hold SOC ≥
# Σ_p (award_p × duration_p). A 100 MW / 100 MWh (1-h) battery can therefore
# back 100 MW of RegUp/RRS but at most 25 MW of 4-h Non-Spin. This is what
# stops a short-duration battery from selling long-duration products on its
# full power, and is the physical driver of the endogenous storage energy-vs-AS
# split's duration gate (config.ercot_storage_as_duration_gate,
# dispatch._build_reserve_rows). Source: ERCOT Nodal Protocols §3.17.3 "State
# of Charge Requirements for Energy Storage Resources" and §8.1 (AS
# definitions); durations RegUp 1 h, RRS 1 h, ECRS 2 h, Non-Spin 4 h per the
# ERCOT ESR SOC methodology (Business Practice Manual, Dec 2022; ERCOT
# Ancillary Services Study Final White Paper, Sept 2024). Not fitted — the
# published deployment durations. Cited in docs/parameter-citations.md.
ERCOT_AS_PRODUCT_DURATION_H: tuple[float, ...] = (1.0, 1.0, 2.0, 4.0)

# --- ERCOT forward AS requirement-setting methodology (G3) -----------------
ERCOT_AS_FE_FRAC_LOAD: float = 0.01
ERCOT_AS_FE_FRAC_WIND: float = 0.10
ERCOT_AS_FE_FRAC_SOLAR: float = 0.18

ERCOT_AS_REGUP_FLOOR_MW: float = 275.0
ERCOT_AS_REGUP_SIGMA_COEF: float = 0.065
ERCOT_AS_REGUP_MIN_MW: float = 80.0
ERCOT_AS_REGUP_MAX_MW: float = 1100.0

ERCOT_AS_RRS_FLOOR_MW: float = 2300.0
ERCOT_AS_RRS_INERTIA_COEF_MW: float = 1160.0
ERCOT_AS_RRS_MAX_MW: float = 3300.0

ERCOT_AS_ECRS_BASE_MW: float = 950.0
ERCOT_AS_ECRS_SIGMA_COEF: float = 0.24
ERCOT_AS_ECRS_RAMP_COEF: float = 0.017
ERCOT_AS_ECRS_MIN_MW: float = 500.0
ERCOT_AS_ECRS_MAX_MW: float = 3300.0

ERCOT_AS_NSPIN_BASE_MW: float = 2475.0
ERCOT_AS_NSPIN_LOAD_COEF: float = 0.00418
ERCOT_AS_NSPIN_RAMP_COEF: float = 0.025
ERCOT_AS_NSPIN_MIN_MW: float = 1400.0
ERCOT_AS_NSPIN_MAX_MW: float = 5700.0

ERCOT_AS_RAMP_WINDOW_HOURS: int = 3

# --- ORDC floor steps (OBDRR048) -------------------------------------------
ORDC_FLOOR_STEPS: tuple[tuple[float, float], ...] = (
    (6500.0, 20.0),
    (7000.0, 10.0),
)
ORDC_FLOOR_START_HOUR_2023: int = 304 * 24

# --- ERCOT ECRS deployment design (pre-RTC+B), date gates -------------------
# From ECRS go-live (Operating Day 2023-06-10, ERCOT market notice
# M-D050523-01; the onset itself is carried by the ASPLANNP433 data, which has
# no ECRS rows before it) through 2024-07-31, ERCOT had NO price-based ECRS
# release to SCED: awarded ECRS was telemetered as AS Responsibility, carved
# out of the SCED-dispatchable range (HASL), and released only by
# manual/automatic reliability deployment (frequency < 59.91 Hz, or 10-minute
# projected net-load capacity insufficiency — ERCOT Ancillary Services Study,
# Final White Paper, Sept 2024). The IMM found this "led to artificial
# shortage pricing … which we estimate doubled average energy prices between
# June and December 2023," raising real-time costs by more than $12B (Potomac
# Economics, 2023 State of the Market Report, §II.G / recommendation 2023-3).
# ERCOT changed the release design via operating procedures effective
# 2024-08-01: ECRS is released to SCED on a sustained power-balance violation
# (>= 40 MW under-generation for 10 consecutive minutes) and dispatched at the
# resources' own energy offers — the PUCT rejected NPRR1224's $750/MWh offer
# floor at its 2024-07-25 open meeting, so there is NO administrative release
# price. Non-leap fleet clock: Jan-Jul = 212 days -> 2024-08-01 00:00 is hour
# 212*24 = 5088. Published market-design dates, never fitted to a price
# residual (docs/parameter-citations.md "ERCOT ECRS deployment design").
ERCOT_ECRS_RELEASE_REFORM_YEAR: int = 2024
ERCOT_ECRS_RELEASE_REFORM_HOUR: int = 212 * 24  # 2024-08-01 00:00

# --- PJM -------------------------------------------------------------------
PJM_PRIMARY_RESERVE_LSC_FACTOR: float = 1.5
from market_sim.config.paths import CALIBRATION_DIR  # noqa: E402

PJM_ORDC_CURVE_PATH: str = str(CALIBRATION_DIR / "pjm_ordc_curve.csv")

# Model zones inside PJM's Mid-Atlantic/Dominion (MAD) Reserve Subzone
# (Manual 11 sec 4.2: the MAAC transmission zones plus Dominion). Crosswalk
# onto the 8-zone model topology (iso_configs._pjm_config): PJM_EMAAC (PSEG,
# JCPL, PECO, DPL, AECO, RECO), PJM_SWMAAC (BGE, PEPCO), PJM_Central_PA (PPL,
# PENELEC, METED — all MAAC) and PJM_Dominion (DOM). Known misalignment
# (CLAUDE.md #13 reconciliation): PJM_Central_PA also rolls up EKPC (eastern
# Kentucky, NOT in MAD), a small co-op (~2% of PJM load) our reduced topology
# cannot split out — including Central_PA whole errs by that sliver rather
# than dropping the PPL/PENELEC/METED bulk of the subzone.
PJM_MAD_ZONES: tuple[str, ...] = (
    "PJM_Central_PA",
    "PJM_Dominion",
    "PJM_EMAAC",
    "PJM_SWMAAC",
)

# --- MISO ------------------------------------------------------------------
MISO_REGULATING_RESERVE_MW: float = 400.0
# VOLL / reserve-demand-curve ceiling: $3,500/MWh is the in-force MISO tariff
# value (Schedule 28) for the ENTIRE calibration window. MISO's shortage-pricing
# reform (FERC docket ER25-579, approved April 2025) raises VOLL $3,500 ->
# $10,000/MWh and replaces the stepped ORDC with an LOLP-based curve, but with a
# targeted effective date of 2025-09-30 (MISO MSC deck MSC-2019-1, Aug-2025).
# 37 of the 38 scored 2025 DA tail hours precede 9/30/2025 (only Oct-6 follows),
# and all 2023/2024 tail hours are under the $3,500 regime, so this constant is
# correct for effectively the entire scored 2023-2025 backcast window — NO
# backcast change. The post-9/30 $10,000-VOLL / LOLP-ORDC regime is a
# FORECAST-lane charter (2026+ forecast runs currently inherit $3,500 — a
# measured tariff update with this citation, its own small charter); it must NOT
# be half-implemented (a VOLL step without the LOLP curve is a wrong mechanism).
# See docs/parameter-citations.md and docs/handoffs/miso-price-formation-design-
# 2026-07.md §2c (primary-document verification, 2026-07-15).
MISO_RESERVE_DEMAND_CURVE_MAX: float = 3500.0
MISO_RESERVE_DEMAND_CURVE_CRITICAL_MW: float = 0.0

# MISO Zonal Operating Reserve Demand Curve (config.miso_zonal_reserves):
# the PUBLISHED stepped curve, BPM-002 §5.2.1.2 / Tariff Schedule 28-A —
# (width as a fraction of the zonal requirement, penalty $/MWh), cheapest
# band (smallest shortfall) first, the ordering model.dispatch consumes:
#   * 80-100% of the zonal requirement cleared -> $200/MWh;
#   * 10-80%  -> $1,100/MWh (Energy Offer Price Cap $1,000 + Contingency
#     Reserve Offer Price Cap $100);
#   * 0-10%   -> VOLL ($3,500, Schedule 28) minus the Zonal Regulating
#     Reserve Demand Curve price (the monthly average peaker proxy, Schedule
#     28 §IV — posted monthly values run ~$156-$222 across 2025-26, so $200
#     Tier-3 -> a $3,300 top step; the top band prices only the last 10% of
#     the requirement, so the proxy's month-to-month wiggle is immaterial).
# Zone set and requirement basis are in _miso_design.
MISO_ZONAL_ORDC_STEPS: tuple[tuple[float, float], ...] = (
    (0.20, 200.0),
    (0.70, 1100.0),
    (0.10, 3300.0),
)
# Default zonal reserve family set (config.miso_zonal_reserve_zones override):
# MISO-South only — the sub-region whose reserves are separated from the
# Midwest pool by the RDT contract-path limit (scope doc §6). MISO-East
# (Michigan pocket) is the optional second family.
MISO_ZONAL_RESERVE_DEFAULT_ZONES: tuple[str, ...] = ("MISO-South",)

# MISO Midwest sub-region (config.miso_midwest_subregional_reserves, the
# engagement-depth lane, miso-71). The 5 PHYSICAL Midwest model zones — the
# North + Central ASM cleared-offers regions (the report's own grain), which
# together form the importing subregion on the North side of the Regional
# Directional Transfer (RDT). External seam buses are excluded by construction
# (the F5 external-bus precedent: only the RDT is a represented and
# measured-binding internal reserve-deliverability boundary). The family holds
# the MEASURED Midwest revealed OR reservation (data.miso_reserve_requirements
# "MISO-Midwest" leg = cleared reg+spin+supp over {North, Central}) IN these
# zones and prices a shortfall at the PUBLISHED Reserve Procurement Enhancement
# demand value (constants.MISO_RPE_DEMAND_VALUE = $200/MWh, 2024 SOM §III.B —
# the demand value of exactly this sub-regional reserve-deliverability
# construct). The per-Reserve-Zone §5.2.1.2 Zonal ORDC steps are DELIBERATELY
# NOT used: the per-zone Zonal ORDC never separated in 26,280 measured
# 2023-2025 hours (design §1b/§2a) — pricing a region at those deep steps would
# be structure the measured record refutes (rule 1). Zero fitted scalars (the
# series is measured, the $200 is a cited constant, the zone list is topology).
MISO_MIDWEST_ZONES: tuple[str, ...] = (
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
)

# MISO ELMP emergency-pricing tier offer floors (config.maxgen_emergency_
# tier_pricing, the F5 scarcity-depth lane): the price applied to emergency
# supply in ELMP inside a DECLARED capacity-emergency window. Primary source,
# footnoted identically in the 2023 SOM (Report Body fn.21) and the 2024/2025
# SOMs (fn.17), all archived in data/raw/MISO/:
#   "Emergency supply is priced by applying a $500/MWh offer price floor
#    (Tier 1) to this supply in ELMP when MISO declares a Max Gen Warning and
#    a $1000/MWh floor (Tier 2) in a Max Gen Event Step 2."
# The 2023 SOM p.10-11 ladder scopes the tiers: Warning and Event Step 1 run
# Tier-1 pricing (Step 1 commits emergency-only units / activates emergency
# ranges — more Tier-1 MW, no new pricing tier); Step 2+ runs Tier 2. The
# Alert rung ("allows 4-hour online resources to set price in ELMP") changes
# price FORMATION only, not the margin — LP-native, no constant here. In-LP
# these floors reprice the load-slack (the administrative last-resort supply)
# inside declared Warning+ window zone-hours via min(iso voll, floor); the
# RBDC/zonal-ORDC curves above are never edited (rule 19; the frozen design
# is docs/handoffs/miso-f5-scarcity-depth-design-2026-07.md §1).
MISO_EMERGENCY_TIER1_OFFER_FLOOR: float = 500.0
MISO_EMERGENCY_TIER2_OFFER_FLOOR: float = 1000.0

# --- CAISO (config.caiso_reserve_coopt, _caiso_design, issue #1492) ---------
# BAL-002-WECC-3 R1 Contingency Reserve requirement: max(most-severe single
# contingency, 3% of hourly-integrated load + 3% of hourly-integrated
# generation). With generation ≈ load the load+gen basis is ≈6% of load; the
# CAISO DMM Annual Report AS chapters report CAISO operational practice
# procuring ≈6.3% of the load forecast (net imports pull the true value toward
# ~5.4%). We anchor the hourly requirement at 6% of load with the fleet-derived
# MSSC (largest_single_contingency_mw) as the floor — both forward-responsive
# (retire the largest plant and the floor falls; the 6% tracks the load
# forecast). Never fitted to a price residual (rule 5/23).
CAISO_CONTINGENCY_FRAC: float = 0.06

# BAL-002-WECC-3 retired the WECC-2a R2 half-spinning requirement (FERC
# approval 2021); CAISO operational practice per the DMM AS chapters keeps
# spinning ≈ non-spinning ≈ half of the contingency reserve. Half/half split of
# the BAL-002 requirement across the two co-optimized products.
CAISO_SPIN_FRACTION: float = 0.5

# CAISO Soft Energy Bid Cap (tariff §30.4.1.2 / §39.6.1.1): $1,000/MWh, the
# anchor the §27.1.2.3.5 scarcity reserve demand curves are quoted as a
# percentage of. The $2,000 Hard cap applies only to resources with a verified
# cost basis above $1,000; the published scarcity-curve $ values (non-spin
# $500/$600/$700, spin $100) are the SOFT-cap percentages, so the soft cap is
# the operative anchor for the demand curve.
CAISO_ENERGY_BID_CAP_SOFT: float = 1000.0

# CAISO scarcity reserve demand curves, tariff §27.1.2.3.5 (Fifth Replacement
# FERC Electric Tariff, as of 2025-11-19), each as an ascending-shortage
# sequence of (fraction-of-soft-bid-cap, cumulative shortage-MW upper edge of
# the tier); the final tier's edge is ``inf`` (to the requirement). Cheapest
# (shallowest shortage) tier first — the convention model.dispatch consumes.
#   * Spinning: 10% of the bid cap ($100/MWh), FLAT at any shortage depth
#     (§27.1.2.3.5) — one tier spanning the whole requirement.
CAISO_SPIN_DEMAND_CURVE: tuple[tuple[float, float], ...] = (
    (0.10, float("inf")),  # $100/MWh, all shortage depths
)
#   * Non-Spinning: 50% ($500) for shortage ≤ 70 MW, 60% ($600) for 70–210 MW,
#     70% ($700) for > 210 MW (§27.1.2.3.5). ABSOLUTE-MW tiers (not fractions of
#     the hourly requirement), so a low-requirement hour simply never reaches
#     the deeper tiers.
CAISO_NONSPIN_DEMAND_CURVE: tuple[tuple[float, float], ...] = (
    (0.50, 70.0),  # $500/MWh, first 70 MW of shortage
    (0.60, 210.0),  # $600/MWh, 70–210 MW
    (0.70, float("inf")),  # $700/MWh, beyond 210 MW
)

# CAISO Spin/Non-Spin sustain duration (hours) — the storage SOC gate's dur_c.
# A resource with a Spinning or Non-Spinning Reserve award must convert the
# full reserved capacity to energy within 10 minutes of dispatch and MAINTAIN
# that output for at least 30 minutes from reaching the award capacity (CAISO
# Tariff AS certification, §8.4 / Appendix K). For storage, CAISO enforces
# exactly this through the ancillary-services state-of-charge constraint
# (ASSOC): an ESR's SOC must cover award × duration (CAISO "Ancillary service
# state of charge constraint" stakeholder initiative; DMM 2023/2024 Special
# Reports on Battery Storage). Published market design, never fitted (rule 5).
CAISO_AS_SUSTAIN_DURATION_H: float = 0.5

# CAISO hydro 10-minute deliverable-ramp fraction of nameplate. Conventional
# hydro governors ramp ~15-25+%/min (NREL WWSIS-2, NREL/TP-5500-55588 App. H —
# the same published source family as fleet.RAMP10_FRAC_BY_GROUP's thermal
# classes), so full nameplate is reachable inside the 10-minute reserve
# window; the tariff's spin/non-spin certification bar is exactly that
# 10-minute full-conversion capability, and CAISO hydro is a major certified
# spin/non-spin provider (DMM Annual Report AS chapters). Class physics, not a
# fitted value; ISO-local because only the CAISO design admits hydro reserve
# (fleet.RAMP10_FRAC_* stay thermal-only for every other ISO).
CAISO_HYDRO_RAMP10_FRAC: float = 1.0

# --- NYISO RCPF products ---------------------------------------------------
NYISO_RCPF_PRODUCTS: tuple[tuple[str, float, float, float], ...] = (
    ("nyca_30min_total", 2620.0, 1965.0, 750.0),
    ("nyca_10min_total", 1310.0, 0.0, 750.0),
    ("nyca_10min_spin", 655.0, 0.0, 775.0),
)

# Locational operating-reserve requirements & demand-curve values, grounded in
# the NYISO State of the Market (SOM) report — the primary source (2023/2024/
# 2025 SOM, "Operating Reserves and Regulation" subsection, e.g. 2024 SOM p.297;
# reproduced identically across all three report years). The SOM enumerates the
# as-enforced products verbatim:
#   * 10-minute East — 1,200 MW in Eastern New York (zones F–K), $775/MW.
#   * 30-minute SENY — "at least 1,300 MW" for ALL hours in Southeast NY, $500/MW
#     (an additional condition-varying increment binds a subset of hours at
#     $40/MW — the #1344 dynamic-requirement channel, not the static base here).
#   * 30-minute NYC — 1,000 MW in New York City, $25/MW.
#   * 10-minute NYC —   500 MW in New York City, $25/MW.
# These supersede the earlier placeholders (East 30-min/$500, SENY 1,100 MW
# nesting-midpoint stand-in, NYC $500) — grounded in the published curve, not
# fitted to LMP residuals (rules 12/13). The product NAME encodes the reserve
# class (``_nyiso_design``: a "10min" product draws only quick-start-eligible
# {gas_ct, oil} headroom; a "30min" product draws the full thermal reserve
# fleet), so East 10-min is met by the downstate F–K peaker fleet — the units
# the real market commits for reserve. ``critical=0`` keeps each product's
# demand curve a single linear ramp from requirement→$0 down to 0 MW→max penalty
# (the SOM's finer step table is approximated by the ``n_ramp`` shortfall steps
# in ``_nyiso_design``). Region membership carries the NYCA ⊃ East ⊃ SENY ⊃ NYC
# nesting: a zone's locational adder stacks every region that contains it.
NYISO_RCPF_LOCATIONAL: dict[str, dict] = {
    "East": {
        "zones": ("Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"),
        "products": (("east_10min_total", 1200.0, 0.0, 775.0),),
    },
    "SENY": {
        "zones": ("Lower_Hudson", "NYC", "Long_Island"),
        "products": (("seny_30min_total", 1300.0, 0.0, 500.0),),
    },
    "NYC": {
        "zones": ("NYC",),
        "products": (
            ("nyc_30min_total", 1000.0, 0.0, 25.0),
            ("nyc_10min_total", 500.0, 0.0, 25.0),
        ),
    },
}

# --- NEISO RCPF products ---------------------------------------------------
NEISO_RCPF_PRODUCTS: tuple[tuple[str, float, float, float], ...] = (
    ("ne_30min_total", 1800.0, 0.0, 1000.0),
    ("ne_10min_total", 1200.0, 0.0, 1500.0),
    ("ne_10min_spin", 600.0, 0.0, 50.0),
)

# --- ERCOT load-resource RRS-UFR enrollment forecast (G4) ------------------
ERCOT_LR_RRS_ENROLL_BASE_YEAR: int = 2025
ERCOT_LR_RRS_ENROLL_BASE_MW: float = 900.0
ERCOT_LR_RRS_ENROLL_GROWTH_MW_PER_YR: float = 60.0
ERCOT_LR_RRS_ENROLL_CAP_MW: float = 1400.0


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ReserveFamily:
    """One reserve balance-row family (a region x product pair)."""

    name: str
    requirement: np.ndarray  # (T,) MW
    zone_mask: np.ndarray  # (n_zones,) bool
    ordc_penalties: np.ndarray  # ascending shortfall-step $/MWh
    ordc_step_widths: np.ndarray  # corresponding widths MW
    reserve_class: int = 0  # eligibility-class index


@dataclass
class ReserveDesign:
    """Complete reserve co-optimization specification for one ISO-year."""

    families: list[ReserveFamily]
    eligible: np.ndarray  # (n_classes, n_gen) bool
    storage_eligible: bool = False
    # (n_reserve_classes,) per-product sustained-delivery duration in hours
    # (ERCOT duration gate, ercot_storage_as_duration_gate). When set, storage's
    # endogenous AS gets its own RS[c,z] columns bounded by a SOC duration gate
    # in dispatch._build_reserve_rows. None keeps storage pooled in the shared
    # headroom (the pre-gate endogenous split).
    storage_duration_h: Optional[np.ndarray] = None
    supply_cap: Optional[np.ndarray] = None  # (n_headroom_rows, T) MW
    # (n_headroom_rows, T) MW — the committed on-line CAPACITY envelope (ERCOT
    # ercot_online_capacity_envelope, G-22 commitment thinness). Where supply_cap
    # bounds only the cleared RESERVE, this caps the shared headroom's ENERGY +
    # RESERVE at the on-line HSL, so the LP cannot dispatch/reserve more thermal
    # than the real system had on-line (scarcity.ercot_online_capacity_envelope_mw).
    # Non-envelope tiers carry the uncapped sentinel. None keeps the LP unchanged.
    online_capacity_cap: Optional[np.ndarray] = None
    # (n_hr, T) MW — the same committed on-line capability envelope kept as a
    # PRICING-ONLY basis (ercot_ordc_only_scarcity, ercot57 joint round v3):
    # never installed as an LP row. Pre-RTC+B SCED carries no committed-
    # capability constraint in the dispatch engine (commitment is RUC/self-
    # commitment, already embodied in availability + floors); the ORDC prices
    # the REALIZED headroom relative to on-line capability post-hoc, so the
    # envelope's only role is measuring that capability for the post-solve
    # RTORPA (scarcity.ercot_ordc_realized_adder). The v2 probe showed why the
    # hard row is wrong: anchoring an LP cap to reality's committed level
    # converts every model-vs-reality supply-mix difference at tight hours
    # into VOLL load-shed (833 GWh across 470 summer hours) — the ercot41/43
    # over-fire signature, now isolated from availability and span demand.
    online_capacity_pricing_mw: Optional[np.ndarray] = None
    # Envelope-CLASS-consistent P-sum mask for the post-solve realized-room
    # RTORPA, (n_gen,) bool (ERCOT-68 room decomposition, 2026-07-15). The
    # identified room is env_all − CAMPD gross over the envelope's own share
    # classes, so the model analogue must subtract dispatch over EXACTLY those
    # classes. headroom_eligible[all-tier] is the LP shared-headroom set
    # (RESERVE_FUEL_TYPES — nuclear/oil included, correctly, for the physical
    # rows whose RHS carries their availability); the envelope's basis carries
    # NO nuclear/oil capability (no share table), so summing their dispatch
    # into the pricing room fabricated ~4.4 GW of phantom tightness (the
    # leg-J December over-fire: recomputed 2024 adder mean $60 -> $1.5/MWh,
    # >$10 h 1,226 -> 63, vs measured RTORPA mean $0.20, 26 h).
    online_capacity_pricing_elig: Optional[np.ndarray] = None
    headroom_eligible: Optional[np.ndarray] = None  # (n_hr, n_gen) bool
    headroom_products: Optional[np.ndarray] = None  # (n_hr, n_families) bool
    headroom_extra_cap: Optional[np.ndarray] = None
    online_gated: Optional[np.ndarray] = None  # (n_classes,) bool
    online_rho: float = 1.0
    # Per-generator reserve spec (dispatch._build_reserve_rows_pergen): one
    # R column per reserve-providing asset, bounded by its 10-min deliverable
    # ramp. ``pergen_gen_idx`` lists every member generator; ``pergen_col``
    # maps each member to its R column (plant-level aggregation — tranches of
    # one plant share a column; ``None`` = one column per member). When set,
    # the zone-aggregate scoping fields above (supply_cap/online_gated/
    # headroom_*) must be None — the per-unit bound supersedes them.
    pergen_gen_idx: Optional[np.ndarray] = None  # (n_members,) fleet indices
    pergen_col: Optional[np.ndarray] = None  # (n_members,) R column per member
    pergen_ramp10: Optional[np.ndarray] = None  # (n_r,) static or (n_r, T)
    # hourly (availability-scaled) MW ramp10 caps
    # Per-pool PRODUCT split (PJM pjm_reserve_pergen_sync): when set,
    # ``pergen_col`` maps members to JOINT-HEADROOM POOLS and
    # ``pergen_col_pool[r]`` maps each R column to its pool, so several
    # product columns (synchronized / non-synchronized) share one pool's
    # joint P+R row and its capacity RHS. ``balance_col_mask[f, r]`` is each
    # family's complete R-column selection (zone ∧ product), replacing the
    # zone-only selection. Both ``None`` on every other path (byte-identical:
    # columns ≡ pools, zone selection).
    pergen_col_pool: Optional[np.ndarray] = None  # (n_r,) pool per R column
    balance_col_mask: Optional[np.ndarray] = None  # (n_fam, n_r) bool
    # Commitment-posture lever (miso_commitment_posture, design note §A): the
    # postured subset of the pergen pools. ``posture_pools`` indexes the R
    # columns that get an online-capacity variable U[p,t] (fast-start pools —
    # capacity-weighted min-down ≤ 2 h AND startup < $30/MW — are exempt,
    # rule 18); ``posture_mlf`` is each postured pool's capacity-weighted
    # CEMS-measured min-stable-when-online fraction (thermal_tranches
    # committed_pct, WWSIS-2 class gap-fill); ``posture_startup`` its
    # capacity-weighted NREL class startup cost in $/MW.
    posture_pools: Optional[np.ndarray] = None  # (q,) R-pool indices
    posture_mlf: Optional[np.ndarray] = None  # (q,) min-stable fraction 0..1
    posture_startup: Optional[np.ndarray] = None  # (q,) $/MW per start


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_reserve_design(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    zone_names: list[str],
    *,
    system_load: np.ndarray | None = None,
    wind_gen: np.ndarray | None = None,
    solar_gen: np.ndarray | None = None,
    sim_year: int | None = None,
) -> ReserveDesign:
    """Build the reserve co-optimization design for any ISO.

    Dispatches to the correct per-ISO helper based on ``config.iso``.
    """
    iso = str(config.iso)
    if iso == "ERCOT":
        if getattr(config, "ercot_multiproduct_as_coopt", False):
            return _ercot_multiproduct_design(
                config,
                fleet_arrays,
                hours,
                zone_names,
                system_load=system_load,
                wind_gen=wind_gen,
                solar_gen=solar_gen,
                sim_year=sim_year,
            )
        return _ercot_design(
            config,
            fleet_arrays,
            hours,
            sim_year=sim_year,
            system_load=system_load,
            wind_gen=wind_gen,
            solar_gen=solar_gen,
        )
    if iso == "PJM":
        return _pjm_design(config, fleet_arrays, hours, zone_names)
    if iso == "MISO":
        return _miso_design(config, fleet_arrays, hours, zone_names)
    if iso == "NYISO":
        return _nyiso_design(config, fleet_arrays, hours, zone_names)
    if iso == "NEISO":
        return _neiso_design(config, fleet_arrays, hours, zone_names)
    if iso == "CAISO":
        return _caiso_design(
            config,
            fleet_arrays,
            hours,
            zone_names,
            system_load=system_load,
            sim_year=sim_year,
        )
    raise ValueError(f"No reserve design for ISO {iso!r}")


def build_reserve_dispatch_kwargs(
    design: ReserveDesign,
) -> dict:
    """Convert a ``ReserveDesign`` into the ``dispatch_kwargs`` dict.

    The returned dict can be passed directly to ``dispatch_kwargs.update()``.
    """
    families = design.families
    if not families:
        return {}

    n_fam = len(families)
    T = families[0].requirement.shape[0]
    n_zones = families[0].zone_mask.shape[0]

    requirement = np.zeros((n_fam, T), dtype=float)
    zone_mask = np.zeros((n_fam, n_zones), dtype=bool)
    counts = np.zeros(n_fam, dtype=int)
    reserve_class = np.zeros(n_fam, dtype=int)
    pen_list: list[np.ndarray] = []
    wid_list: list[np.ndarray] = []

    for f, fam in enumerate(families):
        requirement[f, :] = fam.requirement
        zone_mask[f, :] = fam.zone_mask
        reserve_class[f] = fam.reserve_class
        pen_list.append(fam.ordc_penalties)
        wid_list.append(fam.ordc_step_widths)
        counts[f] = fam.ordc_penalties.shape[0]

    ordc_penalties = np.concatenate(pen_list) if pen_list else np.zeros(0)
    ordc_step_widths = np.concatenate(wid_list) if wid_list else np.zeros(0)

    # Squeeze to (T,) / (n_gen,) for single-family ISOs with one class, to
    # match the old functions' return shapes exactly.
    if n_fam == 1 and design.headroom_eligible is None:
        out_req = requirement[0]  # (T,)
        out_elig = design.eligible[0] if design.eligible.ndim == 2 else design.eligible
    else:
        out_req = requirement
        out_elig = design.eligible

    kw: dict = dict(
        reserve_requirement=out_req,
        reserve_eligible=out_elig,
        ordc_penalties=ordc_penalties.astype(float),
        ordc_step_widths=ordc_step_widths.astype(float),
    )

    if design.storage_eligible:
        kw["reserve_storage"] = True

    # ERCOT storage AS duration gate: per-product durations activate the explicit
    # RS[c,z] storage-reserve columns + SOC gate in dispatch._build_reserve_rows.
    if design.storage_duration_h is not None:
        kw["reserve_storage_duration_h"] = design.storage_duration_h

    # Multi-family: zone mask, counts, class
    if n_fam > 1 or design.headroom_eligible is not None:
        kw["reserve_balance_zone_mask"] = zone_mask
        kw["reserve_balance_ordc_counts"] = counts
        kw["reserve_balance_class"] = reserve_class

    # Headroom rows (ERCOT multiproduct quality cascade)
    if design.headroom_eligible is not None:
        kw["reserve_headroom_eligible"] = design.headroom_eligible
        kw["reserve_headroom_products"] = design.headroom_products

    if design.headroom_extra_cap is not None:
        kw["reserve_headroom_extra_cap"] = design.headroom_extra_cap

    # Online-gated reserve (NYISO synchronised, PJM)
    if design.online_gated is not None:
        kw["reserve_online_gated"] = design.online_gated
        kw["reserve_online_rho"] = design.online_rho

    # Supply cap (ERCOT RTOLCAP, PJM deliverable ramp)
    if design.supply_cap is not None:
        kw["reserve_supply_cap"] = design.supply_cap

    # On-line-capacity envelope (ERCOT G-22 commitment thinness)
    if design.online_capacity_cap is not None:
        kw["reserve_online_capacity_cap"] = design.online_capacity_cap

    # Per-generator reserve columns (PJM pjm_reserve_pergen)
    if design.pergen_gen_idx is not None:
        kw["reserve_pergen_gen_idx"] = design.pergen_gen_idx
        kw["reserve_pergen_ramp10"] = design.pergen_ramp10
        if design.pergen_col is not None:
            kw["reserve_pergen_col"] = design.pergen_col
        # Product-split pergen layout (PJM pjm_reserve_pergen_sync): several
        # R columns share one joint-headroom pool, families select columns.
        if design.pergen_col_pool is not None:
            kw["reserve_pergen_col_pool"] = design.pergen_col_pool
        if design.balance_col_mask is not None:
            kw["reserve_balance_col_mask"] = design.balance_col_mask

    # Commitment-posture pools (MISO miso_commitment_posture, design note §A)
    if design.posture_pools is not None and design.posture_pools.size:
        kw["reserve_posture_pools"] = design.posture_pools
        kw["reserve_posture_mlf"] = design.posture_mlf
        kw["reserve_posture_startup"] = design.posture_startup

    return kw


# ---------------------------------------------------------------------------
# Per-ISO private helpers — ported physics from scarcity.py
# ---------------------------------------------------------------------------


def _reserve_eligible(fleet_arrays: FleetArrays) -> np.ndarray:
    """ISO-agnostic thermal reserve-eligibility mask ``(n_gen,)``."""
    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    return np.isin(fuel_names, sorted(RESERVE_FUEL_TYPES))


# Commitment-posture fast-start exemption thresholds (CLAUDE.md rule 18 /
# design note §A): a pool whose capacity-weighted class physics sit at or
# under BOTH thresholds is fast-start — it restarts inside the operating
# hour, so the real market cycles it freely and its OFFLINE capacity still
# provides MISO offline supplemental reserve (asm_rt_co
# OfflineSupplementalOffer). Same parameter basis as the CAISO RA bridge's
# RA_BRIDGE_ECON_MIN_DOWN_HOURS gate — physics thresholds, never class names.
POSTURE_FAST_START_MIN_DOWN_H: float = 2.0
POSTURE_FAST_START_STARTUP_PER_MW: float = 30.0


def _posture_pool_params(
    fleet_arrays: FleetArrays,
    pergen_gen_idx: np.ndarray,
    pergen_col: np.ndarray,
    n_r: int,
    iso: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-pool commitment-posture parameters for the pergen (zone, fuel) pools.

    Returns ``(posture_pools, posture_mlf, posture_startup)`` — the R-pool
    indices that carry an online-capacity variable U (the non-fast-start
    subset), each pool's capacity-weighted min-stable-when-online fraction,
    and its capacity-weighted startup cost in $/MW. Every input is measured or
    published (zero fitted parameters, design note §A driver clause):

    * **Startup cost / min-down** per member from the NREL/SR-5500-55433 class
      tables (``COMMITMENT_PARAMS_BY_FUEL`` keyed by heat rate for gas
      CC/CT/ST; ``BIN_STARTUP_COST_PER_MW['COAL']`` +
      ``COAL_BIN_MIN_DOWN_HOURS`` for coal). Fuels with no table (oil — the
      quick-start IC/CT class ``_commitment_params`` never screens) count as
      fast-start.
    * **Min-stable fraction** per member from the plant's CEMS-measured
      ``committed_pct`` (``thermal_tranche_overrides`` —
      ``derive_thermal_tranches.py``'s min-stable-when-online percentile,
      re-derived only on source-data updates, rule 23), gap-filled with the
      WWSIS-2 published class value (``MIN_STABLE_PCT_PHYSICAL``).
    * **Fast-start exemption** (rule 18, parameter gate): capacity-weighted
      pool min-down ≤ 2 h AND startup < $30/MW → no U column.
    """
    from market_sim.config.constants import MIN_STABLE_PCT_PHYSICAL
    from market_sim.data.fleet import (
        BIN_STARTUP_COST_PER_MW,
        COAL_BIN_MIN_DOWN_HOURS,
        thermal_tranche_overrides,
    )
    from market_sim.model.commitment import COMMITMENT_PARAMS_BY_FUEL

    gidx = np.asarray(pergen_gen_idx, dtype=int)
    cap = np.asarray(fleet_arrays.pmax, dtype=float)[gidx]
    hr = np.asarray(fleet_arrays.heat_rate, dtype=float)[gidx]
    fuels = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx[gidx]])
    groups = (
        np.asarray(fleet_arrays.plant_group)[gidx]
        if getattr(fleet_arrays, "plant_group", None) is not None
        else np.array([""] * gidx.size)
    )
    plants = np.asarray(fleet_arrays.plant_code, dtype=int)[gidx]

    # Member startup ($/MW) and min-down (h) from the published class tables.
    startup = np.zeros(gidx.size)
    min_down = np.zeros(gidx.size)
    for j in range(gidx.size):
        f = fuels[j]
        if f == "coal":
            startup[j] = BIN_STARTUP_COST_PER_MW["COAL"]
            min_down[j] = float(COAL_BIN_MIN_DOWN_HOURS)
            continue
        table = COMMITMENT_PARAMS_BY_FUEL.get(f)
        if table is None:
            # No commitment table (oil quick-start) — fast-start by physics.
            continue
        params = table[-1][1]
        for cutoff, p in table:
            if hr[j] < cutoff:
                params = p
                break
        startup[j] = float(params["startup_per_mw"])
        min_down[j] = float(params["min_down_hours"])

    # Member min-stable-when-online fraction: CEMS-measured committed_pct per
    # plant, WWSIS-2 class gap-fill for uncovered plants.
    overrides = thermal_tranche_overrides(iso)
    mlf = np.zeros(gidx.size)
    for j in range(gidx.size):
        row = overrides.get((int(plants[j]), str(groups[j])))
        if row is not None:
            mlf[j] = float(row[0]) / 100.0
        else:
            mlf[j] = float(MIN_STABLE_PCT_PHYSICAL.get(str(groups[j]), 0.0))
    mlf = np.clip(mlf, 0.0, 1.0)

    # Capacity-weighted pool aggregation (np.add.at scatter, no pool loop).
    col = np.asarray(pergen_col, dtype=int)
    pool_cap = np.zeros(n_r)
    pool_su = np.zeros(n_r)
    pool_md = np.zeros(n_r)
    pool_mlf = np.zeros(n_r)
    np.add.at(pool_cap, col, cap)
    np.add.at(pool_su, col, cap * startup)
    np.add.at(pool_md, col, cap * min_down)
    np.add.at(pool_mlf, col, cap * mlf)
    with np.errstate(invalid="ignore", divide="ignore"):
        pool_su = np.where(pool_cap > 0, pool_su / pool_cap, 0.0)
        pool_md = np.where(pool_cap > 0, pool_md / pool_cap, 0.0)
        pool_mlf = np.where(pool_cap > 0, pool_mlf / pool_cap, 0.0)

    fast_start = (pool_md <= POSTURE_FAST_START_MIN_DOWN_H) & (
        pool_su < POSTURE_FAST_START_STARTUP_PER_MW
    )
    posture_pools = np.flatnonzero(~fast_start)
    return (
        posture_pools,
        pool_mlf[posture_pools],
        pool_su[posture_pools],
    )


def _quick_start_eligible(fleet_arrays: FleetArrays) -> np.ndarray:
    """Quick-start (10-min capable) subset of the reserve fleet ``(n_gen,)``."""
    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    return np.isin(fuel_names, sorted(QUICK_START_FUEL_TYPES))


# CHP plant groups excluded from the ERCOT posture candidate set (rule 19 —
# their committed state is owned by the CHP steam floors, not the posture).
_ERCOT_POSTURE_CHP_GROUPS = ("CC_CHP", "CT_CHP", "ST_CHP")


def ercot_commitment_posture_spec(
    config,
    fleet_arrays: FleetArrays,
) -> Optional[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
    """Return the STANDALONE energy-only posture spec for ERCOT, or ``None``.

    ERCOT runs a fleet-wide ORDC co-opt with no pergen substrate, so the
    commitment-posture lever (``ercot_commitment_posture``, design note §A;
    ``docs/handoffs/ercot-commitment-thinness-2026-07.md``) is built
    reserve-decoupled: pool the MERCHANT GAS fleet by (zone, fuel-class) and
    posture the non-fast-start pools with only the energy-side rows (headroom
    + min-load + startup), leaving ERCOT's reserve design untouched.

    Returns ``(posture_gen_idx, posture_col, posture_mlf, posture_startup)`` —
    the member fleet indices, each member's dense postured-pool index
    (``0..q-1``), and the per-pool measured min-load fraction and NREL-table
    startup ($/MW). Every input is measured/published (rules 5/13/23):

    * **Scope (rule 19):** candidates are gas_cc + gas_ct units, excluding the
      CHP groups (:data:`_ERCOT_POSTURE_CHP_GROUPS`); coal and gas_st are
      already excluded by fuel — their committed state is owned by other D-2
      mechanisms (coal take-or-pay/must-run, gas_st netload drag, CHP steam
      floors). Members are pooled by (zone, fuel-class), the MISO convention.
    * **Fast-start exemption (rule 18, physics, never class tuples):** the
      capacity-weighted pool fast-start gate of :func:`_posture_pool_params`
      (min-down ≤ 2 h AND startup < $30/MW) exempts the gas_ct pools, so only
      the gas_cc pools carry a U column.
    * **Startup** per pool: the NREL/SR-5500-55433 class tables, capacity-
      weighted (identical to :func:`_posture_pool_params`).
    * **mlf** per pool: the MEASURED committed-CC LSL/HSL capacity-weighted p50
      (60-Day DAM disclosure, ERCOT-62 derive — the same frozen value the
      ``ercot_gas_commitment_bridge`` uses), exposed as
      ``ercot_commitment_posture_min_load_frac`` (frozen rule 23). Non-CC
      postured pools (none in practice) keep the physical WWSIS-2 fallback.
    """
    if not getattr(config, "ercot_commitment_posture", False):
        return None

    fuel = np.asarray(fleet_arrays.fuel_type_idx, dtype=int)
    cc_idx = FUEL_TYPE_NAMES.index("gas_cc")
    ct_idx = FUEL_TYPE_NAMES.index("gas_ct")
    groups = (
        np.asarray(fleet_arrays.plant_group)
        if getattr(fleet_arrays, "plant_group", None) is not None
        else np.array([""] * fuel.size, dtype=object)
    )
    is_chp = np.isin(groups.astype(str), _ERCOT_POSTURE_CHP_GROUPS)
    members = np.flatnonzero(np.isin(fuel, [cc_idx, ct_idx]) & ~is_chp)
    if members.size == 0:
        return None

    # Pool by (zone, fuel-class) — the MISO/CAISO/PJM convention.
    zone = np.asarray(fleet_arrays.zone_idx, dtype=int)[members]
    keys = np.stack([zone, fuel[members]], axis=1)
    _, col = np.unique(keys, axis=0, return_inverse=True)
    n_r = int(col.max()) + 1

    posture_pools, pool_mlf_phys, pool_su = _posture_pool_params(
        fleet_arrays, members, col, n_r, "ERCOT"
    )
    if posture_pools.size == 0:
        return None

    # Per-pool fuel class (for the measured-mlf override).
    pool_fuel = np.zeros(n_r, dtype=int)
    pool_fuel[col] = fuel[members]
    posture_fuel = pool_fuel[posture_pools]

    # Measured mlf: gas_cc pools take the frozen LSL/HSL p50; any non-CC
    # postured pool keeps the physical WWSIS-2 fallback from _posture_pool_params.
    mlf = np.asarray(pool_mlf_phys, dtype=float).copy()
    mlf[posture_fuel == cc_idx] = float(
        getattr(config, "ercot_commitment_posture_min_load_frac", 0.574)
    )

    # Dense-remap members onto the postured pools (0..q-1).
    remap = np.full(n_r, -1, dtype=int)
    remap[posture_pools] = np.arange(posture_pools.size)
    member_new_col = remap[col]
    keep = member_new_col >= 0
    return (
        members[keep],
        member_new_col[keep].astype(int),
        mlf,
        np.asarray(pool_su, dtype=float),
    )


# ---- ERCOT single-product -------------------------------------------------


def _ercot_design(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    *,
    sim_year: int | None = None,
    system_load: np.ndarray | None = None,
    wind_gen: np.ndarray | None = None,
    solar_gen: np.ndarray | None = None,
) -> ReserveDesign:
    """ERCOT single-product ORDC co-optimization (the lumped contingency reserve).

    The reserve-supply cap (``ercot_reserve_supply_cap``) is applied inside the
    design (audit-wiring gap A5, folded here in orchestrator-unification
    Stage 2): previously only ``_ercot_multiproduct_design`` set
    ``supply_cap``, so a single-product forecast ERCOT co-opt ran uncapped —
    the backcast reached the cap only through ``run_calibration.py``'s
    post-design overwrite. One edit here caps both orchestrators; the
    mode-aware source (measured RTOLCAP parquet in backcast, WS-A forward
    formula from the threaded drivers in forecast) is
    ``scarcity.ercot_rtolcap_supply_cap_mw``.
    """
    from market_sim.results.scarcity import (
        ercot_ecrs_requirement_mw,
        ercot_load_resource_reserve_credit_mw,
        ercot_ordc_demand_steps,
        ercot_rtolcap_supply_cap_mw,
        ercot_storage_as_reserve_mw,
        resolve_lolp_params,
    )

    mu, sigma = resolve_lolp_params(config, hours)
    mu_s = float(np.mean(mu))
    sigma_s = float(np.mean(sigma))
    req_total, penalties, widths = ercot_ordc_demand_steps(
        voll=config.ordc_voll,
        mcl_mw=config.ordc_mcl_mw,
        mu_mw=mu_s,
        sigma_mw=sigma_s,
        shift_sigma=config.ordc_lolp_shift_sigma,
        multistep_floor=config.ordc_multistep_floor,
    )
    requirement = np.full(int(hours), req_total, dtype=float)

    if getattr(config, "ercot_ecrs_requirement", False) and int(
        config.weather_year
    ) >= int(getattr(config, "ercot_ecrs_requirement_from_year", 2023)):
        requirement = requirement + ercot_ecrs_requirement_mw(
            int(config.weather_year), hours
        )

    if getattr(config, "ercot_load_resource_reserve", False) and int(
        config.weather_year
    ) >= int(getattr(config, "ercot_load_resource_reserve_from_year", 2023)):
        load_mw = ercot_load_resource_reserve_credit_mw(config, hours, year=sim_year)
        requirement = np.maximum(requirement - load_mw, float(config.ordc_mcl_mw))

    if (
        getattr(config, "ercot_storage_as_reserve", False)
        and getattr(config, "storage_as_commitment", False)
        and not getattr(config, "ercot_storage_as_endogenous", False)
        and int(config.weather_year)
        >= int(getattr(config, "ercot_storage_as_reserve_from_year", 2025))
    ):
        storage_as_mw = ercot_storage_as_reserve_mw(int(config.weather_year), hours)
        requirement = np.maximum(requirement - storage_as_mw, float(config.ordc_mcl_mw))

    eligible = _reserve_eligible(fleet_arrays)
    n_zones = int(np.max(fleet_arrays.zone_idx)) + 1
    zone_mask = np.ones(n_zones, dtype=bool)

    fam = ReserveFamily(
        name="ercot_ordc",
        requirement=requirement,
        zone_mask=zone_mask,
        ordc_penalties=penalties,
        ordc_step_widths=widths,
        reserve_class=0,
    )
    # A5 fold: mode-aware supply cap (measured RTOLCAP in backcast — identical
    # to the retired run_calibration post-design overwrite; WS-A forward
    # formula from the threaded drivers in forecast, previously unreachable
    # for the single-product design). Gated by config.ercot_reserve_supply_cap.
    supply_cap = ercot_rtolcap_supply_cap_mw(
        config,
        hours,
        fleet_arrays,
        system_load=system_load,
        wind_gen=wind_gen,
        solar_gen=solar_gen,
    )
    return ReserveDesign(
        families=[fam],
        eligible=eligible.reshape(1, -1),
        storage_eligible=True,
        supply_cap=supply_cap,
    )


# ---- ERCOT multi-product ---------------------------------------------------


def _ercot_multiproduct_design(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    zone_names: list[str],
    *,
    system_load: np.ndarray | None = None,
    wind_gen: np.ndarray | None = None,
    solar_gen: np.ndarray | None = None,
    sim_year: int | None = None,
) -> ReserveDesign:
    """ERCOT multi-product AS co-optimization (RegUp/RRS/ECRS/NonSpin)."""
    from market_sim.results.scarcity import (
        ercot_as_forward_drivers,
        ercot_as_forward_requirement_mw,
        ercot_as_plan_requirement_mw,
        ercot_load_resource_reserve_credit_mw,
        ercot_rtolcap_supply_cap_mw,
        nyiso_rcpf_product_shortfall_steps,
    )

    T = int(hours)
    n_zones = int(np.max(fleet_arrays.zone_idx)) + 1
    products = list(ERCOT_AS_PRODUCTS)
    n_prod = len(products)
    voll = float(config.ordc_voll)
    crit_frac = float(getattr(config, "ercot_as_critical_frac", 0.0))
    n_ramp = int(getattr(config, "ercot_as_n_ramp", 12))
    year = int(config.weather_year)

    forward_drivers: dict[str, np.ndarray] | None = None
    if (
        getattr(config, "ercot_as_forward_requirement", False)
        and system_load is not None
        and wind_gen is not None
        and solar_gen is not None
    ):
        forward_drivers = ercot_as_forward_drivers(system_load, wind_gen, solar_gen)

    requirement = np.zeros((n_prod, T), dtype=float)
    families: list[ReserveFamily] = []
    released_ecrs_families: list[ReserveFamily] = []
    zone_mask_all = np.ones(n_zones, dtype=bool)

    for p, (_name, code, _tier) in enumerate(products):
        req_t = ercot_as_forward_requirement_mw(config, code, T, forward_drivers)
        if req_t is None:
            req_t = ercot_as_plan_requirement_mw(year, T, code)
        requirement[p, :] = req_t
        req_peak = float(req_t.max())
        if req_peak <= 0.0:
            pens = np.zeros(0)
            wids = np.zeros(0)
        elif getattr(config, "ercot_ordc_only_scarcity", False):
            # Pre-RTC+B ORDC-only design (the ercot57 product-ladder question,
            # docs/DIAGNOSIS-ercot-june2023-scarcity-formation-2026-07.md §4.2):
            # 2023-25 ERCOT has NO real-time per-product scarcity pricing — RT
            # reserve scarcity prices via the ORDC on the REALIZED total online
            # reserves, added post-SCED (RTSPP = SPP + RTORPA;
            # scarcity.ercot_ordc_realized_adder is the pricing side), and a
            # product-vs-capability squeeze triggers RUC commitment, not a
            # price. So the standing product families keep the measured AS-plan
            # requirement but their shortfall costs only the plan-hold epsilon:
            # held whenever free headroom exists (the DAM award's physical
            # withholding), never priced into the energy dual. The pre-reform
            # ECRS_withheld family below keeps its rigid VOLL step (the
            # IMM-documented no-price-release design, separately grounded).
            # The in-LP ORDC total family is forbidden alongside this flag
            # (ScenarioConfig.__post_init__, rule 19).
            pens = np.array([ERCOT_AS_PLAN_HOLD_EPS], dtype=float)
            wids = np.array([req_peak], dtype=float)
        else:
            crit = crit_frac * req_peak
            pens, wids = nyiso_rcpf_product_shortfall_steps(
                req_peak, crit, voll, n_ramp=n_ramp
            )
        # ECRS conservative-deployment design (pre-2024-08-01, published): no
        # price-based release to SCED, so the ECRS demand is a single step AT
        # THE OFFER CAP for the full requirement — the withheld ~2 GW raises
        # the energy dual endogenously in tight hours (the IMM-documented 2023
        # "artificial shortage pricing"). From the 2024-08-01 operating-
        # procedure reform the family reverts to the standing VOLL-anchored
        # ramp (a releasable reserve). A year straddling the reform is split
        # into two disjoint-window families sharing the ECRS reserve class
        # (requirement zeroed outside each window) — penalty steps are static
        # per family, so the date gate lives in the requirement mask. See the
        # ERCOT_ECRS_RELEASE_REFORM_* citation block above.
        if (
            getattr(config, "ercot_ecrs_conservative_deployment", False)
            and code == "ECRS"
            and req_peak > 0.0
        ):
            if year < ERCOT_ECRS_RELEASE_REFORM_YEAR:
                rigid_end = T  # whole year (ECRS onset carried by the data)
            elif year == ERCOT_ECRS_RELEASE_REFORM_YEAR:
                rigid_end = min(ERCOT_ECRS_RELEASE_REFORM_HOUR, T)
            else:
                rigid_end = 0  # post-reform years: standing curve only
            if rigid_end > 0:
                req_rigid = req_t.copy()
                req_rigid[rigid_end:] = 0.0
                families.append(
                    ReserveFamily(
                        name=f"{_name}_withheld",
                        requirement=req_rigid,
                        zone_mask=zone_mask_all.copy(),
                        ordc_penalties=np.array([voll], dtype=float),
                        ordc_step_widths=np.array(
                            [float(req_rigid.max())], dtype=float
                        ),
                        reserve_class=p,
                    )
                )
                if rigid_end < T and float(req_t[rigid_end:].max()) > 0.0:
                    req_rel = req_t.copy()
                    req_rel[:rigid_end] = 0.0
                    # Appended AFTER the four product families so the first
                    # n_prod family columns keep their product identity for
                    # every downstream consumer (as-aware value, MCPC audit).
                    released_ecrs_families.append(
                        ReserveFamily(
                            name=f"{_name}_released",
                            requirement=req_rel,
                            zone_mask=zone_mask_all.copy(),
                            ordc_penalties=pens,
                            ordc_step_widths=wids,
                            reserve_class=p,
                        )
                    )
                continue
        families.append(
            ReserveFamily(
                name=_name,
                requirement=req_t,
                zone_mask=zone_mask_all.copy(),
                ordc_penalties=pens,
                ordc_step_widths=wids,
                reserve_class=p,
            )
        )

    # Load-Resource RRS-UFR supply credit (G4).
    if getattr(config, "ercot_load_resource_reserve", False) and year >= int(
        getattr(config, "ercot_load_resource_reserve_from_year", 2023)
    ):
        rrs_idx = next(
            (i for i, (_n, c, _t) in enumerate(products) if c == "RRS"), None
        )
        if rrs_idx is not None and requirement[rrs_idx].max() > 0.0:
            lr_mw = ercot_load_resource_reserve_credit_mw(config, T, year=sim_year)
            requirement[rrs_idx, :] = np.maximum(requirement[rrs_idx, :] - lr_mw, 0.0)
            families[rrs_idx] = ReserveFamily(
                name=families[rrs_idx].name,
                requirement=requirement[rrs_idx],
                zone_mask=families[rrs_idx].zone_mask,
                ordc_penalties=families[rrs_idx].ordc_penalties,
                ordc_step_widths=families[rrs_idx].ordc_step_widths,
                reserve_class=families[rrs_idx].reserve_class,
            )

    # Measured battery AS-award supply credit on the PRODUCT requirements
    # (config.ercot_storage_as_product_credit; the multi-product analogue of
    # the single-product design's ercot_storage_as_reserve netting). Under the
    # measured storage path (storage_as_commitment, not endogenous) the
    # battery capacity that actually cleared RegUp/RRS/ECRS is reserved OUT of
    # the storage power cap, so the co-opt's residual fleet can no longer
    # supply those product MW — without a credit the products pull the
    # batteries' ~1.2-2.8 GW of awarded AS from THERMAL headroom instead,
    # over-withholding energy capacity the real market never withheld from
    # SCED. The credit nets the measured per-hour battery AS award
    # (60-Day DAM awards, scarcity.ercot_storage_as_reserve_mw — a measured
    # procurement quantity, never a price) pro-rata across the FAST products'
    # requirements (batteries cleared RegUp/RRS/ECRS; Non-Spin is untouched),
    # after the LR credit and WITHOUT touching the families' penalty curves
    # (same convention as the LR credit: steps stay sized to the published
    # plan). No-op when the endogenous split is on (the battery is then inside
    # the co-opt and needs no netting) or before the measured-series
    # from-year. Windowed ECRS families (conservative deployment) keep their
    # date windows via their own requirement masks.
    if (
        getattr(config, "ercot_storage_as_product_credit", False)
        and getattr(config, "storage_as_commitment", False)
        and not getattr(config, "ercot_storage_as_endogenous", False)
        and year >= int(getattr(config, "ercot_storage_as_reserve_from_year", 2025))
    ):
        from market_sim.results.scarcity import ercot_storage_as_reserve_mw

        storage_award = ercot_storage_as_reserve_mw(year, T)  # (T,)
        fast_idx = [p for p, (_n, _c, tier) in enumerate(products) if tier == "fast"]
        fast_total = requirement[fast_idx, :].sum(axis=0)  # (T,)
        if storage_award.max() > 0.0 and fast_total.max() > 0.0:
            with np.errstate(invalid="ignore", divide="ignore"):
                share = np.where(
                    fast_total > 0.0, requirement[fast_idx, :] / fast_total, 0.0
                )  # (n_fast, T)
            credited = np.maximum(requirement[fast_idx, :] - share * storage_award, 0.0)
            requirement[fast_idx, :] = credited
            for f, fam in enumerate(families):
                p = int(fam.reserve_class)
                if p not in fast_idx:
                    continue
                # Apply the credited product requirement inside the family's
                # own active window (zero outside it — the ECRS split).
                new_req = np.where(fam.requirement > 0.0, requirement[p, :], 0.0)
                families[f] = ReserveFamily(
                    name=fam.name,
                    requirement=new_req,
                    zone_mask=fam.zone_mask,
                    ordc_penalties=fam.ordc_penalties,
                    ordc_step_widths=fam.ordc_step_widths,
                    reserve_class=fam.reserve_class,
                )
            for f, fam in enumerate(released_ecrs_families):
                p = int(fam.reserve_class)
                if p not in fast_idx:
                    continue
                new_req = np.where(fam.requirement > 0.0, requirement[p, :], 0.0)
                released_ecrs_families[f] = ReserveFamily(
                    name=fam.name,
                    requirement=new_req,
                    zone_mask=fam.zone_mask,
                    ordc_penalties=fam.ordc_penalties,
                    ordc_step_widths=fam.ordc_step_widths,
                    reserve_class=fam.reserve_class,
                )

    full_elig = _reserve_eligible(fleet_arrays)
    reserve_eligible = np.tile(full_elig, (n_prod, 1))

    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    responsive = np.isin(fuel_names, sorted(RESERVE_FUEL_TYPES))
    quick = np.isin(fuel_names, sorted(QUICK_START_FUEL_TYPES))
    fast_elig = responsive & ~quick
    headroom_eligible = np.vstack([fast_elig, responsive])
    headroom_products = np.zeros((2, n_prod), dtype=bool)
    for p, (_name, _code, tier) in enumerate(products):
        headroom_products[1, p] = True
        if tier == "fast":
            headroom_products[0, p] = True

    # Mode-aware: measured RTOLCAP/RTOFFCAP parquet in backcast (flag off), or the
    # WS-A forward formula in forecast / under the ercot_reserve_supply_forward
    # probe flag (built from the fleet + forecast net-load threaded in here).
    supply_cap = ercot_rtolcap_supply_cap_mw(
        config,
        T,
        fleet_arrays,
        system_load=system_load,
        wind_gen=wind_gen,
        solar_gen=solar_gen,
    )

    # On-line-capacity envelope (config.ercot_online_capacity_envelope, G-22
    # commitment thinness; or its extreme-peak-resolved variant
    # config.ercot_online_capacity_envelope_extreme, the §5 forward path): caps
    # the shared-headroom ENERGY+RESERVE at the committed on-line HSL so the LP
    # cannot serve/reserve more thermal than the real system had on-line (the
    # ~3.2 GW phantom sub-$200 spare). Net-load driver threaded in here exactly
    # like the forward RTOLCAP supply cap; the cap is anchored to measured
    # RTOLCAP, never a price (rule #13). None (gate off) leaves the LP
    # unchanged.
    online_capacity_cap = None
    if (
        getattr(config, "ercot_online_capacity_envelope", False)
        or getattr(config, "ercot_online_capacity_envelope_extreme", False)
        or getattr(config, "ercot_online_capacity_envelope_measured", False)
    ):
        from market_sim.results.scarcity import ercot_online_capacity_envelope_mw

        if system_load is not None:
            wind = (
                np.zeros_like(np.asarray(system_load, dtype=float))
                if wind_gen is None
                else np.asarray(wind_gen, dtype=float)
            )
            solar = (
                np.zeros_like(np.asarray(system_load, dtype=float))
                if solar_gen is None
                else np.asarray(solar_gen, dtype=float)
            )
            net_load = np.asarray(system_load, dtype=float) - wind - solar
            online_capacity_cap = ercot_online_capacity_envelope_mw(
                config,
                fleet_arrays,
                T,
                net_load=net_load,
                headroom_eligible=headroom_eligible,
                headroom_products=headroom_products,
            )

    # ORDC-only scarcity pricing (v3): the envelope is a PRICING-ONLY basis —
    # pre-RTC+B SCED carries no committed-capability constraint, so the array
    # moves to online_capacity_pricing_mw (read by the post-solve RTORPA,
    # scarcity.ercot_ordc_realized_adder) and the LP row is NOT installed
    # (see the ReserveDesign field comment for the v2 hard-row failure).
    online_capacity_pricing_mw = None
    online_capacity_pricing_elig = None
    if getattr(config, "ercot_ordc_only_scarcity", False):
        online_capacity_pricing_mw = online_capacity_cap
        online_capacity_cap = None
        # Envelope-CLASS-consistent P-sum mask for the realized-room RTORPA
        # (ERCOT-68 fix): dispatch is subtracted over exactly the classes whose
        # capability the envelope's share tables carry — the identified
        # construction's model analogue. Nuclear/oil stay in headroom_eligible
        # (the physical LP rows carry their availability on the RHS) but are
        # excluded here, where the basis carries no capability for them.
        if online_capacity_pricing_mw is not None:
            from market_sim.results.scarcity import (
                ercot_online_capacity_envelope_classes,
            )

            env_classes = ercot_online_capacity_envelope_classes(config)
            plant_group = getattr(fleet_arrays, "plant_group", None)
            if plant_group is not None:
                online_capacity_pricing_elig = responsive & np.isin(
                    np.asarray(plant_group), sorted(env_classes)
                )

    # Storage AS duration gate (config.ercot_storage_as_duration_gate): the
    # published per-product SOC durations (ERCOT_AS_PRODUCT_DURATION_H, index-
    # aligned with ERCOT_AS_PRODUCTS) that bound the endogenous storage split by
    # stored energy. Only meaningful alongside the endogenous split
    # (ercot_storage_as_endogenous) — the measured storage treatment reserves the
    # award out of the cap instead, and mixing the two over-withholds (the
    # ercot30 blow-up). None (default) keeps storage pooled in the shared
    # headroom (the pre-gate endogenous split, run164).
    storage_duration_h = None
    if getattr(config, "ercot_storage_as_duration_gate", False) and getattr(
        config, "ercot_storage_as_endogenous", False
    ):
        storage_duration_h = np.asarray(ERCOT_AS_PRODUCT_DURATION_H, dtype=float)
        if storage_duration_h.shape[0] != n_prod:
            raise ValueError(
                "ERCOT_AS_PRODUCT_DURATION_H must be index-aligned with "
                f"ERCOT_AS_PRODUCTS ({n_prod} products), got "
                f"{storage_duration_h.shape[0]}"
            )

    # Lumped ORDC TOTAL-reserve family (config.ercot_ordc_total_reserve): the
    # published RTORPA mechanism of the pre-RTC+B regime, layered ON TOP of the
    # per-product AS families — the faithful 2023-25 stack is both together.
    # RTSPP = SCED energy price + ORDC(total online reserves): the ORDC values
    # the AGGREGATE reserve level, and every product's held MW counts toward it
    # (as RTOLCAP counts online batteries and AS responsibility alike). So the
    # family is ALL-CLASS (reserve_class -1): its balance row sums every
    # product's R over all zones, adding NO new reserve columns and NO new
    # headroom — capacity is never double-procured, only the total level is
    # additionally demanded/priced by the LOLP×VOLL curve (the same
    # ercot_ordc_demand_steps the single-product co-opt uses, incl. the
    # OBDRR048 floors). Reserve held beyond the AS plans up to the ORDC span
    # (~10.7 GW at the default μ/σ) is thereby valued — the structural form of
    # the measured ~2× RTOLCAP-vs-AS-plan coverage. The two supply credits the
    # single-product family applies carry over unchanged in meaning:
    # * Load-Resource RRS-UFR (measured NP3-911 / forward enrollment, G4) is
    #   load-side reserve the LP has no generator columns for; it counts toward
    #   RTORPA's total online reserves, so it nets off this family's RHS
    #   (floored at MCL) exactly as it nets off the RRS product family's.
    # * The measured storage-AS credit applies only when storage is NOT an
    #   endogenous reserve supplier (ercot_storage_as_endogenous off): when
    #   endogenous, cleared storage AS is inside the R sum already.
    # NOT applied here: ercot_ecrs_requirement (the ECRS plan add-on belongs to
    # the single-product family, where no ECRS product exists; here the ECRS
    # family carries it) — adding it would double-count the ECRS demand.
    # Appended LAST so the first n_prod family columns keep their product
    # identity for every downstream consumer (as-aware value, MCPC audit).
    total_families: list[ReserveFamily] = []
    if getattr(config, "ercot_ordc_total_reserve", False):
        from market_sim.results.scarcity import (
            ercot_ordc_demand_steps,
            ercot_storage_as_reserve_mw,
            resolve_lolp_params,
        )

        mu, sigma = resolve_lolp_params(config, T)
        mu_s = float(np.mean(mu))
        sigma_s = float(np.mean(sigma))
        req_total, total_pens, total_wids = ercot_ordc_demand_steps(
            voll=config.ordc_voll,
            mcl_mw=config.ordc_mcl_mw,
            mu_mw=mu_s,
            sigma_mw=sigma_s,
            shift_sigma=config.ordc_lolp_shift_sigma,
            multistep_floor=config.ordc_multistep_floor,
        )
        total_req = np.full(T, req_total, dtype=float)
        if getattr(config, "ercot_load_resource_reserve", False) and year >= int(
            getattr(config, "ercot_load_resource_reserve_from_year", 2023)
        ):
            lr_mw = ercot_load_resource_reserve_credit_mw(config, T, year=sim_year)
            total_req = np.maximum(total_req - lr_mw, float(config.ordc_mcl_mw))
        if (
            getattr(config, "ercot_storage_as_reserve", False)
            and getattr(config, "storage_as_commitment", False)
            and not getattr(config, "ercot_storage_as_endogenous", False)
            and year >= int(getattr(config, "ercot_storage_as_reserve_from_year", 2025))
        ):
            storage_as_mw = ercot_storage_as_reserve_mw(year, T)
            total_req = np.maximum(total_req - storage_as_mw, float(config.ordc_mcl_mw))
        total_families.append(
            ReserveFamily(
                name="ercot_ordc_total",
                requirement=total_req,
                zone_mask=zone_mask_all.copy(),
                ordc_penalties=total_pens,
                ordc_step_widths=total_wids,
                reserve_class=-1,  # all-class: sums every product's reserve
            )
        )

    return ReserveDesign(
        families=families + released_ecrs_families + total_families,
        eligible=reserve_eligible,
        storage_eligible=True,
        storage_duration_h=storage_duration_h,
        headroom_eligible=headroom_eligible,
        headroom_products=headroom_products,
        supply_cap=supply_cap,
        online_capacity_cap=online_capacity_cap,
        online_capacity_pricing_mw=online_capacity_pricing_mw,
        online_capacity_pricing_elig=online_capacity_pricing_elig,
    )


def ercot_commitment_headroom_overrides(
    fleet_arrays: FleetArrays,
    committed: np.ndarray,
    headroom_eligible: np.ndarray,
) -> dict:
    """Commitment-state-aware reserve-headroom overrides for the ERCOT P2 solve.

    The P1 multi-product co-opt draws reserve on ALL-online availability — a
    perfect-foresight fiction that leaves ~8-9 GW of phantom headroom exactly
    where 2023's scarcity lived. The AS-aware P2 solve already zeroes
    decommitted units' availability out of the shared-headroom RHS; this
    completes the commitment-state re-scope with the two pieces the static
    eligibility masks cannot express (ERCOT's published RTOLCAP/RTOFFCAP
    online/offline reserve split, made endogenous):

    * **fast row = the full responsive set** (quick-start included). Membership
      in the online (synchronized) reserve pool is decided PER HOUR by the
      commitment state through the P2 availability — an online CT is
      synchronized and backs RegUp/RRS-PFR/ECRS exactly like an online CC,
      while a decommitted (offline) unit's zeroed availability contributes
      nothing. The static "slow-start classes only" fast row was the
      no-commitment-state approximation.
    * **offline quick-start capacity → Non-Spin only**: a decommitted gas-CT /
      oil peaker can synchronize within ERCOT's 30-minute Non-Spin window, so
      its (original, outage-derated) capacity enters the "all" headroom row's
      RHS as ``reserve_headroom_extra_cap`` — reserve-only, no energy term
      (the unit is offline) — and never the fast row. A cold slow-start unit
      still backs neither tier.

    Both re-scopes are the solve's own commitment state applied to physical
    start-capability classes — forward-regenerable, no measured series and no
    fitted parameter (CLAUDE.md #1/#11).

    Args:
        fleet_arrays: The ORIGINAL (pre-commitment) fleet — its availability
            prices the offline quick-start capacity; the P2 fleet's zeroed
            hours would erase exactly the capacity this credits.
        committed: ``(n_gen, T)`` commitment mask from the AS-aware screen
            (adequacy floor applied).
        headroom_eligible: The P1 design's ``(n_hr, n_gen)`` row eligibility
            (fast, all).

    Returns:
        Dict of dispatch-kwargs overrides: ``reserve_headroom_eligible`` and
        ``reserve_headroom_extra_cap`` (``(n_hr, n_zones, T)``).
    """
    he = np.atleast_2d(np.asarray(headroom_eligible, dtype=bool)).copy()
    if he.shape[0] != 2:
        raise ValueError(
            "ercot_commitment_headroom_overrides expects the 2-row "
            f"(fast, all) ERCOT headroom spec, got {he.shape[0]} rows"
        )
    responsive = _reserve_eligible(fleet_arrays)
    quick = _quick_start_eligible(fleet_arrays)
    # Fast (synchronized) row: full responsive set; the P2 availability carries
    # the per-hour online/offline distinction.
    he[0] = responsive
    cap = fleet_arrays.pmax[:, None] * np.asarray(
        fleet_arrays.availability, dtype=float
    )
    offline_quick = (quick & responsive)[:, None] & ~np.asarray(committed, dtype=bool)
    off_cap = np.where(offline_quick, cap, 0.0)  # (n_gen, T)
    zone_idx = np.asarray(fleet_arrays.zone_idx, dtype=int)
    n_zones = int(zone_idx.max()) + 1
    T = cap.shape[1]
    extra = np.zeros((he.shape[0], n_zones, T), dtype=float)
    np.add.at(extra[1], zone_idx, off_cap)  # "all" row only — Non-Spin tier
    return {
        "reserve_headroom_eligible": he,
        "reserve_headroom_extra_cap": extra,
    }


# ---- PJM ------------------------------------------------------------------


PJM_PERGEN_SIZE_SPLIT_MEAN_MULTIPLE: float = 2.0  # size-split pooling
# threshold (pjm_reserve_pergen_size_split): a plant is "large enough to
# individually matter" for reserve pricing when its capacity exceeds this
# multiple of its OWN (zone, fuel-class) pool's mean plant capacity —
# self-normalizing (derived from the pool's own capacity distribution, no
# absolute MW cutoff) rather than a fitted price parameter (rule 5): this
# gates LP GRANULARITY (which plants get an individual reserve column vs
# share a pooled one), never a breakpoint, penalty, or offer curve. Value
# chosen from the measured PJM 2024 fleet's row-count/memory tradeoff: 2.0x
# -> 95 pools / 27.0% MW split individually / ~2.1x the base 39-pool tier's
# joint+balance rows, staying inside a defensible headroom over the
# already-near-ceiling (~15.3 GB) base sync-split tier; 1.5x -> 141 pools
# measured at ~2.45x the row count, too aggressive given the base tier's
# already-thin margin (see the pjm-88 size-split A/B and the memory-infeasible
# full per-plant tier at 407 pools this sits well under).


def pjm_pergen_structure(
    fleet_arrays: FleetArrays,
    size_split_mean_multiple: float | None = None,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Return the PJM pergen ``(gen_idx, col, n_r)`` (zone, fuel-class) pooling.

    Members are the reserve-eligible units that can deliver within 10 minutes
    (``FleetArrays.ramp10 > 0`` — an exact reduction: a zero-ramp column would
    be fixed at 0); ``col`` maps each member to its (zone, fuel-class) pool.
    Shared between :func:`_pjm_design`'s pergen branch and the P0→P1
    sync-cap recompute (``pipeline.commitment.pjm_pergen_sync_reserve_caps``)
    so the pooling is identical by construction.

    ``size_split_mean_multiple`` (``pjm_reserve_pergen_size_split``, GATED
    default ``None``): when set, each base (zone, fuel-class) pool is further
    split — a PLANT (tranches summed) whose capacity exceeds
    ``size_split_mean_multiple`` × its pool's mean plant capacity gets its
    OWN individual pool; the remaining (smaller) plants stay pooled together
    in the base (zone, fuel-class) pool, exactly as the ``None`` path. This
    concentrates LP granularity on the plants large enough to individually
    set the marginal reserve opportunity cost (the pjm-87 diagnosis: with
    39 uniform pools the LP can virtually always source PJM's small measured
    requirement from SOME idle pool, diluting the price even when a specific
    dominant plant is fully energy-loaded) without the memory-infeasible cost
    of a full per-plant tier (407 pools / 814 sync-split R columns — ~10x the
    base tier, beyond the documented 2026-07-02 P1 OOM precedent at a smaller
    scale). ``None`` is byte-identical to the pre-split layout.
    """
    ramp10 = getattr(fleet_arrays, "ramp10", None)
    if ramp10 is None:
        raise ValueError(
            "pjm_reserve_pergen requires FleetArrays.ramp10 (the 10-min "
            "deliverable ramp, fleet._ramp10_capability)"
        )
    ramp10 = np.asarray(ramp10, dtype=float)
    eligible = _reserve_eligible(fleet_arrays)
    gen_idx = np.flatnonzero(eligible & (ramp10 > 0.0))
    fuel = np.asarray(fleet_arrays.fuel_type_idx, dtype=int)[gen_idx]
    zone = np.asarray(fleet_arrays.zone_idx, dtype=int)[gen_idx]
    keys = np.stack([zone, fuel], axis=1)
    _, base_col = np.unique(keys, axis=0, return_inverse=True)
    base_col = base_col.astype(int)
    if size_split_mean_multiple is None:
        n_r = int(base_col.max()) + 1 if base_col.size else 0
        return gen_idx, base_col, n_r

    plant = np.asarray(fleet_arrays.plant_code, dtype=int)[gen_idx]
    # Per-(pool, plant) capacity: aggregate tranches of one plant within one
    # base pool (a plant cannot span zones or fuel classes, so this is an
    # exact per-plant total). pool_plant_id keys the unique (pool, plant)
    # pairs; member_pp maps each member row to its pair's index.
    pmax = np.asarray(fleet_arrays.pmax, dtype=float)[gen_idx]
    pool_plant_keys = np.stack([base_col, plant], axis=1)
    pool_plant_id, member_pp = np.unique(pool_plant_keys, axis=0, return_inverse=True)
    n_pp = pool_plant_id.shape[0]
    pp_cap = np.zeros(n_pp, dtype=float)
    np.add.at(pp_cap, member_pp, pmax)
    pp_pool = pool_plant_id[:, 0]

    # Pool mean plant capacity (mean over DISTINCT plants, not tranches).
    n_base = int(base_col.max()) + 1 if base_col.size else 0
    pool_plant_count = np.zeros(n_base, dtype=float)
    pool_cap_sum = np.zeros(n_base, dtype=float)
    np.add.at(pool_plant_count, pp_pool, 1.0)
    np.add.at(pool_cap_sum, pp_pool, pp_cap)
    with np.errstate(invalid="ignore", divide="ignore"):
        pool_mean_cap = np.where(
            pool_plant_count > 0, pool_cap_sum / pool_plant_count, 0.0
        )
    pp_large = pp_cap > (size_split_mean_multiple * pool_mean_cap[pp_pool])

    # Column assignment: large (pool, plant) pairs each get a unique new
    # column (0..n_large-1); every other member keeps its base pool id,
    # offset past the large columns and re-densified via np.unique so ids
    # stay contiguous even when a base pool has zero small members left.
    large_pp_idx = np.flatnonzero(pp_large)
    n_large = large_pp_idx.size
    pp_to_large_col = np.full(n_pp, -1, dtype=int)
    pp_to_large_col[large_pp_idx] = np.arange(n_large)
    member_large_col = pp_to_large_col[member_pp]
    is_large_member = member_large_col >= 0

    small_base = np.where(is_large_member, -1, base_col)
    _, small_dense = np.unique(small_base[~is_large_member], return_inverse=True)
    col = np.empty(gen_idx.size, dtype=int)
    col[is_large_member] = member_large_col[is_large_member]
    col[~is_large_member] = n_large + small_dense
    n_r = int(col.max()) + 1 if col.size else 0
    return gen_idx, col, n_r


def pjm_pergen_pool_ramp10(
    fleet_arrays: FleetArrays,
    gen_idx: np.ndarray,
    col: np.ndarray,
    n_r: int,
    member_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Per-pool hourly availability-scaled 10-min deliverable ramp, ``(n_r, T)``.

    ``member_mask`` (``(n_members, T)`` bool/float) optionally scopes members
    per hour — the sync/non-sync product split multiplies the online (or
    offline-fast-start) pattern in before pooling. The dense member-level
    intermediate is released before return (the G-40 subset-build discipline).
    """
    ramp = np.asarray(fleet_arrays.ramp10, dtype=float)[gen_idx]
    avail = np.asarray(fleet_arrays.availability, dtype=float)[gen_idx]
    member_ramp_t = ramp[:, np.newaxis] * avail  # (n_members, T)
    if member_mask is not None:
        member_ramp_t = member_ramp_t * member_mask
    out = np.zeros((n_r, member_ramp_t.shape[1]), dtype=float)
    np.add.at(out, col, member_ramp_t)
    del member_ramp_t
    return out


def _pjm_design(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    zone_names: list[str] | None = None,
) -> ReserveDesign:
    """PJM energy+reserve co-optimization (measured Primary requirement + published ORDC).

    Two layouts, both on the measured Primary requirement and the published
    two-step ORDC:

    * Zone-aggregate (default): the legacy single RTO family drawing on total
      eligible zone headroom, optionally re-scoped by the deliverable supply
      cap (``pjm_reserve_supply_cap``) and/or online gating
      (``pjm_reserve_online_gated``).
    * Per-generator (``pjm_reserve_pergen``): one R column per (zone,
      fuel-class) pool of reserve-eligible units with nonzero 10-min ramp
      (``R[r] ≤ Σ FleetArrays.ramp10 × availability``, hourly), joint
      ``Σ P + R ≤ Σ cap`` per pool-hour, and TWO nested measured balance
      families per Manual 11 sec 4.2 — the RTO Reserve Zone (``pr_req_mw``)
      and the Mid-Atlantic/Dominion Reserve Subzone (``mad_pr_req_mw``, zones
      :data:`PJM_MAD_ZONES`; a MAD MW counts toward both, the NYISO nesting
      template). Reserve then competes with energy at the marginal pool,
      which is what prices the sub-shortage opportunity-cost band
      (docs/multi-iso/pjm-reserve-ordc.md Phase 2). Class-level pooling
      everywhere is the documented 15 GB memory tier the miso-39 keeper
      proved (the finer plant-in-MAD tier OOM'd in P1, 2026-07-02 memtest).
      The zone-aggregate scoping flags are ignored in this mode (the
      per-pool ramp10 bound supersedes them). The forecast path (no measured
      series) falls back to the 1.5×MSSC formula for the RTO family and
      omits the MAD family.
    """
    from market_sim.results.scarcity import (
        largest_single_contingency_mw,
        load_pjm_measured_mad_reserve_requirement,
        load_pjm_measured_mad_sync_reserve_requirement,
        load_pjm_measured_reserve_requirement,
        load_pjm_measured_sync_reserve_requirement,
        load_pjm_ordc_curve,
        pjm_ordc_shortfall_steps,
        pjm_primary_reserve_requirement,
        pjm_reserve_deliverable_supply_cap_mw,
    )

    year = int(config.weather_year)
    req = load_pjm_measured_reserve_requirement(year, hours)
    if req is None:
        eligible_mask = _reserve_eligible(fleet_arrays)
        lsc = largest_single_contingency_mw(
            fleet_arrays.pmax,
            availability=fleet_arrays.availability,
            reserve_mask=eligible_mask,
            plant_code=fleet_arrays.plant_code,
        )
        req = pjm_primary_reserve_requirement(lsc, hours)
    req = np.asarray(req, dtype=float)

    curve = load_pjm_ordc_curve(PJM_ORDC_CURVE_PATH)
    steps = curve[("Primary", "RTO")]
    outer_offset = float(max(o for o, _ in steps))
    _req_total_nom, penalties, widths = pjm_ordc_shortfall_steps(
        steps, float(np.mean(req))
    )
    widths = np.asarray(widths, dtype=float).copy()
    widths[-1] = float(np.max(req))

    requirement = req + outer_offset
    eligible = _reserve_eligible(fleet_arrays)
    T = int(hours)
    n_zones = int(np.max(fleet_arrays.zone_idx)) + 1
    zone_mask = np.ones(n_zones, dtype=bool)

    fam = ReserveFamily(
        name="pjm_primary",
        requirement=requirement,
        zone_mask=zone_mask,
        ordc_penalties=penalties.astype(float),
        ordc_step_widths=widths.astype(float),
        reserve_class=0,
    )

    if getattr(config, "pjm_reserve_pergen", False):
        families = [fam]
        # Nested MAD subzone family — measured backcast series only; a
        # forecast year (no series) runs the RTO family alone.
        mad_req = load_pjm_measured_mad_reserve_requirement(year, hours)
        if mad_req is not None and zone_names:
            mad_steps = curve[("Primary", "MAD")]
            mad_offset = float(max(o for o, _ in mad_steps))
            mad_req = np.asarray(mad_req, dtype=float)
            _mad_total, mad_pen, mad_wid = pjm_ordc_shortfall_steps(
                mad_steps, float(np.mean(mad_req))
            )
            mad_wid = np.asarray(mad_wid, dtype=float).copy()
            mad_wid[-1] = float(np.max(mad_req))
            mad_mask = np.array([z in PJM_MAD_ZONES for z in zone_names], dtype=bool)
            if mad_mask.any():
                families.append(
                    ReserveFamily(
                        name="pjm_primary_mad",
                        requirement=mad_req + mad_offset,
                        zone_mask=mad_mask,
                        ordc_penalties=mad_pen.astype(float),
                        ordc_step_widths=mad_wid.astype(float),
                        reserve_class=0,
                    )
                )
        # R-column granularity: one column per (zone, fuel-class) EVERYWHERE
        # — the class-level aggregate tier the miso-39 KEEPER runs
        # (_miso_design pergen branch), adopted after the finer tiers were
        # memory-falsified on this box (docs/multi-iso/pjm-reserve-ordc.md
        # Phase 2 memtests, 2026-07-02): per-tranche OOM'd at ~15.9 GB and
        # the plant-in-MAD tier (257 R columns -> 2.25M joint rows) solved
        # P0 at ~15.1 GB but was OOM-killed in the P1 warm-start — the HiGHS
        # basis workspace scales with the joint-row count. The class tier
        # (8 zones x ~6 thermal classes, <=~48 columns/hour, ~5x fewer
        # joint rows) is the pattern MISO proved feasible on the same 15 GB
        # box. Same physics at every tier (sum ramp10[members] ==
        # sum RAMP10_FRAC x pmax, measured-reconciled under
        # measured_ramp_capability); the MAD balance family still selects
        # its member zones' columns (columns are zone-pure). The tier is a
        # documented memory scope-down, never a breakpoint/penalty change
        # (CLAUDE.md #1/#11). Pooling shared with the P0->P1 sync-cap
        # recompute via pjm_pergen_structure (grouping identical by
        # construction). pjm_reserve_pergen_size_split (GATED) further
        # splits each pool's large plants into individual columns — the
        # pjm-87 diagnosis's remedy for pooling-diluted opportunity-cost
        # pricing; None (default) is byte-identical to the pre-split layout.
        size_split = (
            PJM_PERGEN_SIZE_SPLIT_MEAN_MULTIPLE
            if getattr(config, "pjm_reserve_pergen_size_split", False)
            else None
        )
        pergen_gen_idx, pergen_col, n_r = pjm_pergen_structure(
            fleet_arrays, size_split_mean_multiple=size_split
        )
        # Hourly availability-scaled deliverable ramp per column, (n_r, T):
        # a unit on outage (or derated) contributes proportionally less
        # 10-minute ramp — the CAMPD outage overlay (backcast) / forecast
        # availability thins the pool's deliverable cap in exactly the hours
        # capacity is out (the _miso_design convention). Physical input, not
        # a fitted parameter.
        col_ramp10 = pjm_pergen_pool_ramp10(
            fleet_arrays, pergen_gen_idx, pergen_col, n_r
        )
        if getattr(config, "pjm_reserve_pergen_sync", False):
            # Per-gen OPPORTUNITY-COST co-opt (pjm_reserve_pergen_sync, the
            # G-20b successor build): the Synchronized sub-product gets its
            # own measured balance families and the pool R columns split into
            # a SYNC product (online 10-min ramp only — scoped at the P0->P1
            # seam, pipeline.commitment.build_pjm_reserve_p1_prep) and a
            # NON-SYNC product (offline fast-start ramp, Manual 11 sec 4.2),
            # sharing each pool's joint P+R headroom row. See the
            # ScenarioConfig field docstring for the full design.
            if getattr(config, "pjm_commitment_posture", False):
                raise ValueError(
                    "pjm_reserve_pergen_sync is mutually exclusive with "
                    "pjm_commitment_posture — the posture U/SU re-anchor and "
                    "the sync online scoping gate the same phenomenon "
                    "(CLAUDE.md rule 19: one mechanism per phenomenon)"
                )
            # Synchronized requirement: measured (backcast) or the Manual 11
            # sec 4.3 rule SR = Largest Single Contingency (forecast).
            sr_req = load_pjm_measured_sync_reserve_requirement(year, hours)
            if sr_req is None:
                lsc = largest_single_contingency_mw(
                    fleet_arrays.pmax,
                    availability=fleet_arrays.availability,
                    reserve_mask=eligible,
                    plant_code=fleet_arrays.plant_code,
                )
                sr_req = np.full(T, max(0.0, float(lsc)), dtype=float)
            sr_req = np.asarray(sr_req, dtype=float)
            sr_steps = curve[("Synchronized", "RTO")]
            sr_offset = float(max(o for o, _ in sr_steps))
            _sr_total, sr_pen, sr_wid = pjm_ordc_shortfall_steps(
                sr_steps, float(np.mean(sr_req))
            )
            sr_wid = np.asarray(sr_wid, dtype=float).copy()
            sr_wid[-1] = float(np.max(sr_req))
            families.append(
                ReserveFamily(
                    name="pjm_sync",
                    requirement=sr_req + sr_offset,
                    zone_mask=zone_mask,
                    ordc_penalties=sr_pen.astype(float),
                    ordc_step_widths=sr_wid.astype(float),
                    reserve_class=0,
                )
            )
            mad_mask_arr = (
                np.array([z in PJM_MAD_ZONES for z in zone_names], dtype=bool)
                if zone_names
                else None
            )
            mad_sr_req = load_pjm_measured_mad_sync_reserve_requirement(year, hours)
            has_mad_sr = (
                mad_sr_req is not None
                and mad_mask_arr is not None
                and mad_mask_arr.any()
            )
            if has_mad_sr:
                mad_sr_steps = curve[("Synchronized", "MAD")]
                mad_sr_offset = float(max(o for o, _ in mad_sr_steps))
                mad_sr_req = np.asarray(mad_sr_req, dtype=float)
                _msr_total, msr_pen, msr_wid = pjm_ordc_shortfall_steps(
                    mad_sr_steps, float(np.mean(mad_sr_req))
                )
                msr_wid = np.asarray(msr_wid, dtype=float).copy()
                msr_wid[-1] = float(np.max(mad_sr_req))
                families.append(
                    ReserveFamily(
                        name="pjm_sync_mad",
                        requirement=mad_sr_req + mad_sr_offset,
                        zone_mask=mad_mask_arr,
                        ordc_penalties=msr_pen.astype(float),
                        ordc_step_widths=msr_wid.astype(float),
                        reserve_class=0,
                    )
                )
            # Column layout: [0, n_r) = SYNC product, [n_r, 2*n_r) = NON-SYNC
            # product; both columns of pool p share joint row p.
            col_pool = np.tile(np.arange(n_r, dtype=int), 2)
            # Pool zone (columns are zone-pure): pool p's zone from any member.
            pool_zone = np.zeros(n_r, dtype=int)
            pool_zone[pergen_col] = np.asarray(fleet_arrays.zone_idx, dtype=int)[
                pergen_gen_idx
            ]
            sync_sel = np.concatenate(
                [np.ones(n_r, dtype=bool), np.zeros(n_r, dtype=bool)]
            )
            all_sel = np.ones(2 * n_r, dtype=bool)
            # Family order mirrors the `families` list construction above:
            # PR_RTO [, PR_MAD], SR_RTO [, SR_MAD]. Primary is served by both
            # products (SR ⊆ PR nesting — a synchronized MW counts toward
            # Primary); Synchronized only by the SYNC columns.
            masks: list[np.ndarray] = [all_sel]
            if len(families) >= 2 and families[1].name == "pjm_primary_mad":
                mad_pool = mad_mask_arr[pool_zone]
                masks.append(np.tile(mad_pool, 2))
            masks.append(sync_sel)
            if has_mad_sr:
                mad_pool = mad_mask_arr[pool_zone]
                masks.append(np.concatenate([mad_pool, np.zeros(n_r, dtype=bool)]))
            balance_col_mask = np.stack(masks, axis=0)
            # P0 caps (no commitment pattern yet — the base-cost discovery run
            # treats the fleet as all-online): SYNC = the full availability-
            # scaled pool deliverable ramp, NON-SYNC = 0. The P0->P1 seam
            # recomputes both from the P0 run pattern
            # (pipeline.commitment.pjm_pergen_sync_reserve_caps).
            pergen_ramp10_2p = np.vstack([col_ramp10, np.zeros_like(col_ramp10)])
            return ReserveDesign(
                families=families,
                eligible=eligible.reshape(1, -1),
                storage_eligible=False,
                pergen_gen_idx=pergen_gen_idx,
                pergen_col=pergen_col.astype(int),
                pergen_ramp10=pergen_ramp10_2p,
                pergen_col_pool=col_pool,
                balance_col_mask=balance_col_mask,
            )
        # Commitment-posture lever (design note §A; PJM port
        # docs/handoffs/pjm-commitment-posture-port-2026-07.md): U/SU columns
        # on the non-fast-start pools, gated on pjm_commitment_posture. Shares
        # MISO's _posture_pool_params verbatim (measured/published pool params
        # only — CEMS committed_pct mlf, NREL class startup, physics fast-start
        # gate rule 18). No new design, no fitted parameter.
        posture_pools = posture_mlf = posture_startup = None
        if getattr(config, "pjm_commitment_posture", False):
            posture_pools, posture_mlf, posture_startup = _posture_pool_params(
                fleet_arrays,
                pergen_gen_idx,
                pergen_col,
                n_r,
                str(config.iso),
            )
        return ReserveDesign(
            families=families,
            eligible=eligible.reshape(1, -1),
            storage_eligible=False,
            pergen_gen_idx=pergen_gen_idx,
            pergen_col=pergen_col.astype(int),
            pergen_ramp10=col_ramp10,
            posture_pools=posture_pools,
            posture_mlf=posture_mlf,
            posture_startup=posture_startup,
        )

    supply_cap = pjm_reserve_deliverable_supply_cap_mw(config, fleet_arrays, T)

    online_gated = None
    online_rho = 1.0
    if getattr(config, "pjm_reserve_online_gated", False):
        rho = float(getattr(config, "pjm_reserve_online_rho", 1.0))
        online_gated = np.array([True])
        online_rho = rho

    return ReserveDesign(
        families=[fam],
        eligible=eligible.reshape(1, -1),
        storage_eligible=False,
        supply_cap=supply_cap,
        online_gated=online_gated,
        online_rho=online_rho,
    )


# ---- MISO -----------------------------------------------------------------


def _miso_design(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    zone_names: list[str] | None = None,
    n_ramp: int = 8,
) -> ReserveDesign:
    """MISO energy+reserve co-optimization: market-wide RBDC, optional zonal.

    Always builds the market-wide RBDC family (requirement = MSSC +
    regulating, demand curve ramping to the $3,500/MWh VOLL anchor — MISO
    BPM-002 / Schedule 28/28-A, unchanged from the miso3/miso-34 probes).

    When ``config.miso_zonal_reserves`` is on (GATED, default off) it appends
    one LOCATIONAL operating-reserve family per zone in
    ``config.miso_zonal_reserve_zones`` (default
    :data:`MISO_ZONAL_RESERVE_DEFAULT_ZONES` = MISO-South), the NYISO
    nested-family template: MISO enforces a minimum Zonal Operating Reserve
    Requirement per Reserve Zone (BPM-002 §3.3/§3.3.2), anchored to the
    pre-determined largest zonal contingency event — modeled as the
    within-zone MSSC (fleet-derived, forward-responsive) — and shortfalls
    price at the published Zonal Operating Reserve Demand Curve
    (:data:`MISO_ZONAL_ORDC_STEPS`, BPM-002 §5.2.1.2). The zonal family
    shares the market-wide family's reserve class, so a South reserve MW
    counts toward both constraints (nested, like NYISO East ⊂ NYCA). Zero
    parameters fitted to the price residual.
    """
    from market_sim.results.scarcity import (
        largest_single_contingency_mw,
        nyiso_rcpf_product_shortfall_steps,
    )

    eligible = _reserve_eligible(fleet_arrays)
    mssc = largest_single_contingency_mw(
        fleet_arrays.pmax,
        availability=fleet_arrays.availability,
        reserve_mask=eligible,
        plant_code=fleet_arrays.plant_code,
    )
    req = float(mssc) + MISO_REGULATING_RESERVE_MW
    penalties, widths = nyiso_rcpf_product_shortfall_steps(
        req,
        MISO_RESERVE_DEMAND_CURVE_CRITICAL_MW,
        MISO_RESERVE_DEMAND_CURVE_MAX,
        n_ramp=n_ramp,
    )
    T = int(hours)
    n_zones = int(np.max(fleet_arrays.zone_idx)) + 1
    zone_mask = np.ones(n_zones, dtype=bool)
    requirement = np.full(T, req, dtype=float)

    # Measured hourly requirement basis (miso_measured_reserve_requirements,
    # Lane-2 miso-56): the market-wide RBDC family takes the measured hourly
    # cleared reg+spin+supp series in place of the flat fleet-MSSC + 400 MW
    # estimate, and the South zonal family below takes the measured South
    # reservation in place of the within-zone-MSSC static (which overstates
    # the real ~0.3-0.5 GW South holding several-fold). Shortfall steps keep
    # their published static shape and translate with the hourly requirement
    # (the NYISO dynamic-requirements convention). Rule-13 measured quantity
    # intake, rule-14 mandatory swap; hard-errors when the parquet is absent.
    measured_req: dict[str, np.ndarray] = {}
    if getattr(config, "miso_measured_reserve_requirements", False):
        from market_sim.data.miso_reserve_requirements import (
            load_miso_reserve_requirements,
        )

        measured_req = load_miso_reserve_requirements(int(config.weather_year), T)
        requirement = measured_req["market"]
        if float(requirement.max()) > req:
            # Feasibility guard: static widths must span the requirement in
            # every hour (widths are per-family constants). Re-anchor the
            # published ramp shape to the measured peak when it exceeds the
            # fleet-MSSC + regulating static basis.
            penalties, widths = nyiso_rcpf_product_shortfall_steps(
                float(requirement.max()),
                MISO_RESERVE_DEMAND_CURVE_CRITICAL_MW,
                MISO_RESERVE_DEMAND_CURVE_MAX,
                n_ramp=n_ramp,
            )

    families = [
        ReserveFamily(
            name="miso_rbdc",
            requirement=requirement,
            zone_mask=zone_mask,
            ordc_penalties=penalties.astype(float),
            ordc_step_widths=widths.astype(float),
            reserve_class=0,
        )
    ]

    if getattr(config, "miso_zonal_reserves", False):
        if not zone_names:
            raise ValueError(
                "miso_zonal_reserves requires zone_names to map zonal reserve "
                "families onto model zones"
            )
        zone_index = {name: i for i, name in enumerate(zone_names)}
        zonal_zones = tuple(
            getattr(config, "miso_zonal_reserve_zones", None)
            or MISO_ZONAL_RESERVE_DEFAULT_ZONES
        )
        for zname in zonal_zones:
            if zname not in zone_index:
                raise ValueError(
                    f"miso_zonal_reserve_zones entry {zname!r} is not a model "
                    f"zone (zones: {list(zone_names)})"
                )
            z = zone_index[zname]
            in_zone = np.asarray(fleet_arrays.zone_idx, dtype=int) == z
            # Zonal requirement = the largest zonal contingency event: the
            # within-zone MSSC over reserve-eligible units (plant-aggregated
            # common-mode, availability-aware) — BPM-002 §3.3.2's minimum
            # zonal requirement basis, per the MISO STR design's
            # "pre-determined largest zonal events".
            zonal_req = float(
                largest_single_contingency_mw(
                    fleet_arrays.pmax,
                    availability=fleet_arrays.availability,
                    reserve_mask=eligible & in_zone,
                    plant_code=fleet_arrays.plant_code,
                )
            )
            if zonal_req <= 0.0:
                continue
            zmask = np.zeros(n_zones, dtype=bool)
            zmask[z] = True
            zonal_requirement = np.full(T, zonal_req, dtype=float)
            width_anchor = zonal_req
            if zname in measured_req:
                # Measured hourly South reservation replaces the within-zone
                # MSSC static; the published §5.2.1.2 curve fractions anchor
                # to the measured series' annual MAX so the stepped curve
                # spans the requirement in every hour (widths are static per
                # family — a narrower anchor could leave requirement beyond
                # the priced steps, an infeasibility, in peak-requirement
                # hours). Shape preserved, published proportions unchanged.
                zonal_requirement = measured_req[zname]
                width_anchor = float(np.max(zonal_requirement))
            zonal_pen = np.array([p for _, p in MISO_ZONAL_ORDC_STEPS])
            zonal_wid = np.array(
                [frac * width_anchor for frac, _ in MISO_ZONAL_ORDC_STEPS]
            )
            families.append(
                ReserveFamily(
                    name=f"miso_zonal_or_{zname.lower().replace('-', '_')}",
                    requirement=zonal_requirement,
                    zone_mask=zmask,
                    ordc_penalties=zonal_pen,
                    ordc_step_widths=zonal_wid,
                    reserve_class=0,
                )
            )

    if getattr(config, "miso_midwest_subregional_reserves", False):
        # Midwest sub-regional reserve-holding family (miso-71 engagement-depth
        # lane; the MISO_MIDWEST_ZONES citation block above carries the basis).
        # The measured Midwest OR reservation is forced to sit IN the 5
        # physical Midwest zones, closing the ledgered "RPE Only" STR-scarcity
        # gap (miso_rpe_pricing DOF ledger) the congestion-blind market-wide
        # RBDC family leaves open: a cost-minimizing LP otherwise satisfies the
        # market-wide requirement with reserve parked in the RDT-trapped South
        # surplus and converts every Midwest MW of headroom to energy in a
        # Midwest event (2025 SOM p.8/pp.8-9; design §1c). ENERGY-SIDE — it does
        # NOT make the reserve curves fire (design §2c): the family dual sits at
        # the re-dispatch opportunity cost in almost every hour and reaches the
        # $200 RPE step only where the M-2-thinned fleet cannot hold the
        # measured (feasible) requirement. reserve_class 0 nests a Midwest
        # reserve MW into BOTH the Midwest and market-wide requirements (the
        # NYISO East ⊂ NYCA template; measured Midwest + measured South =
        # measured market, so the market family becomes implied-slack — recorded
        # in the DOF ledger, not a defect).
        if not zone_names:
            raise ValueError(
                "miso_midwest_subregional_reserves requires zone_names to map "
                "the Midwest sub-region onto model zones"
            )
        mw_zone_index = {name: i for i, name in enumerate(zone_names)}
        mw_mask = np.zeros(n_zones, dtype=bool)
        for zname in MISO_MIDWEST_ZONES:
            if zname not in mw_zone_index:
                raise ValueError(
                    f"MISO_MIDWEST_ZONES entry {zname!r} is not a model zone "
                    f"(zones: {list(zone_names)})"
                )
            mw_mask[mw_zone_index[zname]] = True
        if "MISO-Midwest" in measured_req:
            # Measured hourly Midwest revealed OR holding (the miso-56 intake's
            # North+Central leg) — rule-14 measured basis, the adopted input.
            midwest_requirement = np.asarray(measured_req["MISO-Midwest"], dtype=float)
        else:
            # Fallback / forward generator (flag on but the measured series off,
            # or a forecast year): the within-region MSSC over reserve-eligible
            # Midwest units — fleet-derived, forward-responsive (rule 13), the
            # same static basis the South family falls back to.
            mw_region = np.isin(
                np.asarray(fleet_arrays.zone_idx, dtype=int),
                np.array([mw_zone_index[z] for z in MISO_MIDWEST_ZONES], dtype=int),
            )
            midwest_mssc = float(
                largest_single_contingency_mw(
                    fleet_arrays.pmax,
                    availability=fleet_arrays.availability,
                    reserve_mask=eligible & mw_region,
                    plant_code=fleet_arrays.plant_code,
                )
            )
            midwest_requirement = np.full(T, midwest_mssc, dtype=float)
        # Single shortfall step [(1.0, RPE $200)] width-anchored at the series
        # max (South-family feasibility convention: a static width must span
        # the requirement in every hour). The published RPE demand value is the
        # SOLE step — the per-zone ORDC ladder is measured-refuted (§2a).
        mw_anchor = float(np.max(midwest_requirement))
        if mw_anchor > 0.0:
            families.append(
                ReserveFamily(
                    name="miso_subregional_or_midwest",
                    requirement=midwest_requirement,
                    zone_mask=mw_mask,
                    ordc_penalties=np.array([MISO_RPE_DEMAND_VALUE], dtype=float),
                    ordc_step_widths=np.array([1.0 * mw_anchor], dtype=float),
                    reserve_class=0,
                )
            )

    if getattr(config, "miso_reserve_pergen", False):
        # PER-ASSET reserve columns (dispatch._build_reserve_rows_pergen), the
        # MISO analogue of PJM's pjm_reserve_pergen: reserve competes with
        # energy on the same marginal asset (joint sum P + R <= sum cap per
        # column-hour) and cleared reserve is bounded by the 10-minute
        # deliverable ramp (R[r] <= sum FleetArrays.ramp10 =
        # RAMP10_FRAC_BY_GROUP x pmax, NREL/TP-5500-55588 App. H class ramp
        # rates — capacity- and class-derived, so it regenerates for a
        # forecast fleet). This is what lets the RBDC / zonal ORDC families
        # actually run short: without a deliverability bound the perfect-
        # foresight LP always clears the requirement from slow-unit headroom
        # by re-dispatch (miso-38 gate 4: reserve prices at the $8-21
        # opportunity cost, never at the published curve steps).
        #
        # R-column granularity: one column per (zone, fuel-class) EVERYWHERE
        # — the class-level aggregate tier (columns scale with zones x
        # classes, ~30-40/hour at 7 zones), NOT per plant. The per-plant and
        # per-tranche tiers are documented memory-infeasible at MISO plant
        # scale on the 15 GB calibration box (miso-reserve-coopt.md memory
        # note; the 6-zone zone-aggregate co-opt already peaks ~13 GB with a
        # ~16 GB transient). Same physics at every tier (sum ramp10[members]
        # == sum RAMP10_FRAC x pmax); the tier is a documented memory
        # scope-down, never a breakpoint/penalty change (CLAUDE.md #1/#10).
        ramp10 = getattr(fleet_arrays, "ramp10", None)
        if ramp10 is None:
            raise ValueError(
                "miso_reserve_pergen requires FleetArrays.ramp10 (the 10-min "
                "deliverable ramp, fleet._ramp10_capability)"
            )
        ramp10 = np.asarray(ramp10, dtype=float)
        # Members: reserve-eligible units deliverable within 10 min
        # (ramp10 > 0 — nuclear runs baseload and carries no upward reserve).
        # Exact reduction: a zero-ramp column would be fixed at 0.
        pergen_gen_idx = np.flatnonzero(eligible & (ramp10 > 0.0))
        fuel = np.asarray(fleet_arrays.fuel_type_idx, dtype=int)[pergen_gen_idx]
        zone = np.asarray(fleet_arrays.zone_idx, dtype=int)[pergen_gen_idx]
        keys = np.stack([zone, fuel], axis=1)
        _, pergen_col = np.unique(keys, axis=0, return_inverse=True)
        n_r = int(pergen_col.max()) + 1 if pergen_col.size else 0
        # Hourly availability-scaled deliverable ramp per column, (n_r, T):
        # a unit on outage (or derated) contributes proportionally less
        # 10-minute ramp — the CAMPD outage overlay (backcast) / forecast
        # availability thins the pool's deliverable cap in exactly the hours
        # capacity is out. Physical input, not a fitted parameter.
        avail = np.asarray(fleet_arrays.availability, dtype=float)[pergen_gen_idx]
        member_ramp_t = ramp10[pergen_gen_idx][:, np.newaxis] * avail  # (m, T)
        col_ramp10 = np.zeros((n_r, member_ramp_t.shape[1]), dtype=float)
        np.add.at(col_ramp10, pergen_col, member_ramp_t)
        # Commitment-posture lever (design note §A): U/SU columns on the
        # non-fast-start pools, gated on miso_commitment_posture. Pool
        # parameters are measured/published only (_posture_pool_params).
        posture_pools = posture_mlf = posture_startup = None
        if getattr(config, "miso_commitment_posture", False):
            posture_pools, posture_mlf, posture_startup = _posture_pool_params(
                fleet_arrays,
                pergen_gen_idx,
                pergen_col,
                n_r,
                str(config.iso),
            )
        return ReserveDesign(
            families=families,
            eligible=eligible.reshape(1, -1),
            storage_eligible=False,
            pergen_gen_idx=pergen_gen_idx,
            pergen_col=pergen_col.astype(int),
            pergen_ramp10=col_ramp10,
            posture_pools=posture_pools,
            posture_mlf=posture_mlf,
            posture_startup=posture_startup,
        )

    return ReserveDesign(
        families=families,
        eligible=eligible.reshape(1, -1),
        storage_eligible=False,
    )


# ---- NYISO -----------------------------------------------------------------


def _nyiso_design(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    zone_names: list[str],
    n_ramp: int = 8,
) -> ReserveDesign:
    """NYISO locational energy+reserve co-optimization (nested RCPF families).

    Requirement basis: each family's requirement is the static published MW
    (``NYISO_RCPF_PRODUCTS`` / ``NYISO_RCPF_LOCATIONAL``) unless
    ``config.nyiso_dynamic_reserve_requirements`` is on, in which case any
    family with a measured as-enforced hourly series
    (``data.nyiso_reserve_requirements``, the issue-#1344 Ask-B intake) takes
    that series instead — the condition-varying requirement that can bind in
    the hours the static one provably never does. The ORDC shortfall steps
    keep the published static (requirement, critical, penalty) SHAPE and
    translate with the hourly requirement (the published RCPF is itself a
    stepped curve; translating preserves its penalties and widths).

    Rule-19 reconciliation: the post-solve RCPF overlay (``results.rcpf``,
    ``config.nyiso_rcpf_enabled``) prices the same phenomenon these in-LP
    families do. Enabling both is a hard error — the overlay is the
    post-solve comparator for co-opt-off runs only, never a stack on the
    co-opt duals (CLAUDE.md rule 19: one mechanism per phenomenon).
    """
    from market_sim.results.scarcity import (
        nyiso_rcpf_product_shortfall_steps,
        nyiso_spin_requirement_mw,
    )

    if bool(getattr(config, "nyiso_rcpf_enabled", False)):
        raise ValueError(
            "nyiso_rcpf_enabled=True with energy_reserve_coopt: the post-solve "
            "RCPF overlay (results.rcpf) and the in-LP RCPF reserve families "
            "price the same phenomenon (reserve-shortage rent in the LBMP). "
            "One mechanism per phenomenon (CLAUDE.md rule 19) — keep the "
            "overlay as the co-opt-off comparator, or disable the co-opt."
        )

    dynamic_req: dict[str, np.ndarray] = {}
    if bool(getattr(config, "nyiso_dynamic_reserve_requirements", False)):
        from market_sim.data.nyiso_reserve_requirements import (
            load_nyiso_reserve_requirements,
        )

        # weather_year is the backcast fleet-clock year (the calibration
        # harness constructs one config per solve year, weather_year=year).
        dynamic_req = load_nyiso_reserve_requirements(
            int(config.weather_year), int(hours)
        )

    T = int(hours)
    zone_index = {name: i for i, name in enumerate(zone_names)}
    n_zones = len(zone_names)

    raw_families: list[tuple[tuple[int, ...], str, tuple[float, float, float]]] = []
    nyca_products = tuple(
        getattr(config, "nyiso_rcpf_products", None) or NYISO_RCPF_PRODUCTS
    )
    all_zones = tuple(range(n_zones))
    for name, req, crit, pen in nyca_products:
        raw_families.append(
            (all_zones, str(name), (float(req), float(crit), float(pen)))
        )

    locational = getattr(config, "nyiso_rcpf_locational", None) or NYISO_RCPF_LOCATIONAL
    for region in locational.values():
        member_idx = tuple(zone_index[z] for z in region["zones"] if z in zone_index)
        if not member_idx:
            continue
        for name, req, crit, pen in region["products"]:
            raw_families.append(
                (member_idx, str(name), (float(req), float(crit), float(pen)))
            )

    synch = bool(getattr(config, "nyiso_synchronised_reserve", False))
    commit_gated = synch and bool(getattr(config, "commitment_enabled", False))
    if synch:
        nyc_idx = tuple(i for z, i in zone_index.items() if z == "NYC")
        spin_req = nyiso_spin_requirement_mw(config)
        if nyc_idx:
            spin_name = "nyc_spin_commit" if commit_gated else "nyc_spin_online"
            raw_families.append((nyc_idx, spin_name, (spin_req, 0.0, 500.0)))

    families: list[ReserveFamily] = []
    for member_idx, name, (req, crit, pen) in raw_families:
        zmask = np.zeros(n_zones, dtype=bool)
        zmask[list(member_idx)] = True
        rclass = (
            2
            if "spin_online" in name
            else (1 if "10min" in name or "spin" in name else 0)
        )
        if name in dynamic_req:
            # Measured as-enforced hourly requirement (issue #1344): the
            # condition-varying series replaces the static published MW for
            # this family; the ORDC steps below stay anchored to the static
            # published shape and translate with the requirement.
            requirement_arr = dynamic_req[name]
        else:
            requirement_arr = np.full(T, req, dtype=float)
        p, w = nyiso_rcpf_product_shortfall_steps(req, crit, pen, n_ramp=n_ramp)
        families.append(
            ReserveFamily(
                name=name,
                requirement=requirement_arr,
                zone_mask=zmask,
                ordc_penalties=p,
                ordc_step_widths=w,
                reserve_class=rclass,
            )
        )

    full_elig = _reserve_eligible(fleet_arrays)
    quick_elig = _quick_start_eligible(fleet_arrays)
    if synch and not commit_gated:
        eligible = np.vstack([full_elig, quick_elig, quick_elig])
        online_gated = np.array([False, False, True], dtype=bool)
        q_idx = np.flatnonzero(quick_elig)
        pmin_q = np.asarray(fleet_arrays.pmin, dtype=float)[q_idx]
        pmax_q = np.asarray(fleet_arrays.pmax, dtype=float)[q_idx]
        valid = (pmin_q > 0) & (pmax_q > pmin_q)
        if valid.any():
            ratio = (pmax_q[valid] - pmin_q[valid]) / pmin_q[valid]
            online_rho = float(
                np.clip(np.average(ratio, weights=pmax_q[valid]), 0.5, 4.0)
            )
        else:
            online_rho = 1.0
    else:
        eligible = np.vstack([full_elig, quick_elig])
        online_gated = None
        online_rho = 1.0

    return ReserveDesign(
        families=families,
        eligible=eligible,
        storage_eligible=True,
        online_gated=online_gated,
        online_rho=online_rho,
    )


# ---- NEISO ----------------------------------------------------------------


def _neiso_design(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    zone_names: list[str],
    n_ramp: int = 8,
) -> ReserveDesign:
    """NEISO system-wide energy+reserve co-optimization (3-level RCPF nesting).

    Requirement basis: each family's requirement is the static published MW
    (``NEISO_RCPF_PRODUCTS``) unless
    ``config.neiso_dynamic_reserve_requirements`` is on, in which case any
    family with a measured as-enforced hourly series
    (``data.neiso_reserve_requirements``, the ISO Express Hourly Reserve
    Requirements intake — the NEISO analogue of the NYISO issue-#1344 Ask-B
    channel) takes that series instead — the condition-varying requirement
    that can bind in the hours the static one provably never does (reserve
    dual $0.00 in all 26,280 train hours at the static values, neiso-56).
    The ORDC shortfall steps keep the published static (requirement,
    critical, penalty) SHAPE and translate with the hourly requirement (the
    published RCPF is itself a stepped curve; translating preserves its
    penalties and widths).

    Rule-19 reconciliation: the post-solve RCPF overlay (``results.rcpf``,
    ``config.neiso_rcpf_enabled``) prices the same phenomenon these in-LP
    families do. Enabling both is a hard error — the overlay is the
    post-solve comparator for co-opt-off runs only, never a stack on the
    co-opt duals (CLAUDE.md rule 19: one mechanism per phenomenon).
    """
    from market_sim.results.scarcity import nyiso_rcpf_product_shortfall_steps

    if bool(getattr(config, "neiso_rcpf_enabled", False)):
        raise ValueError(
            "neiso_rcpf_enabled=True with energy_reserve_coopt: the post-solve "
            "RCPF overlay (results.rcpf) and the in-LP RCPF reserve families "
            "price the same phenomenon (reserve-shortage rent in the LMP). "
            "One mechanism per phenomenon (CLAUDE.md rule 19) — keep the "
            "overlay as the co-opt-off comparator, or disable the co-opt."
        )

    dynamic_req: dict[str, np.ndarray] = {}
    if bool(getattr(config, "neiso_dynamic_reserve_requirements", False)):
        from market_sim.data.neiso_reserve_requirements import (
            load_neiso_reserve_requirements,
        )

        # weather_year is the backcast fleet-clock year (the calibration
        # harness constructs one config per solve year, weather_year=year).
        dynamic_req = load_neiso_reserve_requirements(
            int(config.weather_year), int(hours)
        )

    T = int(hours)
    n_zones = len(zone_names)
    all_zones = tuple(range(n_zones))
    products = tuple(
        getattr(config, "neiso_rcpf_products", None) or NEISO_RCPF_PRODUCTS
    )

    families: list[ReserveFamily] = []
    for name, req, crit, pen in products:
        zmask = np.zeros(n_zones, dtype=bool)
        zmask[list(all_zones)] = True
        rclass = 1 if "10min" in str(name) or "spin" in str(name) else 0
        if str(name) in dynamic_req:
            # Measured as-enforced hourly requirement (Limb A): the
            # condition-varying series replaces the static published MW for
            # this family; the ORDC steps below stay anchored to the static
            # published shape and translate with the requirement.
            requirement_arr = dynamic_req[str(name)]
        else:
            requirement_arr = np.full(T, float(req), dtype=float)
        p, w = nyiso_rcpf_product_shortfall_steps(
            float(req), float(crit), float(pen), n_ramp=n_ramp
        )
        families.append(
            ReserveFamily(
                name=str(name),
                requirement=requirement_arr,
                zone_mask=zmask,
                ordc_penalties=p,
                ordc_step_widths=w,
                reserve_class=rclass,
            )
        )

    full_elig = _reserve_eligible(fleet_arrays)
    quick_elig = _quick_start_eligible(fleet_arrays)
    eligible = np.vstack([full_elig, quick_elig])

    return ReserveDesign(
        families=families,
        eligible=eligible,
        storage_eligible=True,
    )


# ---- CAISO ----------------------------------------------------------------


def _caiso_reserve_eligible(fleet_arrays: FleetArrays) -> np.ndarray:
    """CAISO-local reserve-eligibility mask ``(n_gen,)``.

    The shared thermal mask (:data:`RESERVE_FUEL_TYPES`) PLUS hydro — the
    ISO-local seam the issue-#1492 design calls for: CAISO hydro (166 plants,
    ~6.4 GW) is a major certified spin/non-spin provider (DMM Annual Report AS
    chapters). Hydro carries no entry in ``fleet.RAMP10_FRAC_BY_*`` (thermal
    tables, other ISOs' designs stay hydro-free), so ``_caiso_design``
    backfills its 10-minute deliverable ramp from
    :data:`CAISO_HYDRO_RAMP10_FRAC` locally. Hydro's monthly energy budget
    (``dispatch._build_hydro_rows``) bounds only its dispatched energy — held
    (undeployed) reserve spends no water, so the budget and the reserve
    headroom compose correctly. Kept a distinct function so the extension
    lives here, never as a branch in the shared ``_reserve_eligible``.
    """
    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    return _reserve_eligible(fleet_arrays) | (fuel_names == "hydro")


def caiso_pergen_structure(
    fleet_arrays: FleetArrays,
) -> tuple[np.ndarray, np.ndarray, int, np.ndarray]:
    """CAISO pergen reserve-pool structure ``(gen_idx, col, n_r, ramp10)``.

    The (zone, fuel-class) pooling of every CAISO-reserve-eligible unit
    (:func:`_caiso_reserve_eligible` — thermal + hydro) with a nonzero
    10-minute deliverable ramp. Shared by ``_caiso_design`` (layout
    construction) and ``pipeline.commitment.caiso_pergen_sync_reserve_caps``
    (the P0→P1 online-scoping seam) so the column order is identical by
    construction — the ``pjm_pergen_structure`` convention. ``ramp10`` is
    returned with the CAISO-local hydro backfill applied
    (:data:`CAISO_HYDRO_RAMP10_FRAC`: hydro has no CEMS so no measured
    ramp-capability row exists, and the shared thermal ``RAMP10_FRAC``
    tables stay hydro-free for every other ISO).
    """
    eligible = _caiso_reserve_eligible(fleet_arrays)
    ramp10 = getattr(fleet_arrays, "ramp10", None)
    if ramp10 is None:
        raise ValueError(
            "caiso_reserve_coopt requires FleetArrays.ramp10 (the 10-min "
            "deliverable ramp, fleet._ramp10_capability)"
        )
    ramp10 = np.asarray(ramp10, dtype=float)
    # Hydro 10-minute deliverable ramp, backfilled ISO-locally: full nameplate
    # inside the 10-minute window is hydro governor class physics (the
    # CAISO_HYDRO_RAMP10_FRAC citation block). Only rows the CAISO-local
    # eligibility mask admits are touched; other ISOs never reach this.
    fuel_names_all = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    is_hydro = fuel_names_all == "hydro"
    ramp10 = np.where(
        is_hydro & (ramp10 <= 0.0),
        CAISO_HYDRO_RAMP10_FRAC * np.asarray(fleet_arrays.pmax, dtype=float),
        ramp10,
    )
    pergen_gen_idx = np.flatnonzero(eligible & (ramp10 > 0.0))
    fuel = np.asarray(fleet_arrays.fuel_type_idx, dtype=int)[pergen_gen_idx]
    zone = np.asarray(fleet_arrays.zone_idx, dtype=int)[pergen_gen_idx]
    keys = np.stack([zone, fuel], axis=1)
    _, pergen_col = np.unique(keys, axis=0, return_inverse=True)
    n_r = int(pergen_col.max()) + 1 if pergen_col.size else 0
    return pergen_gen_idx, pergen_col.astype(int), n_r, ramp10


def caiso_pergen_pool_ramp10(
    fleet_arrays: FleetArrays,
    gen_idx: np.ndarray,
    col: np.ndarray,
    n_r: int,
    ramp10: np.ndarray,
    member_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Availability-scaled per-pool 10-minute deliverable ramp ``(n_r, T)``.

    A unit on outage (or derated) contributes proportionally less 10-minute
    ramp, thinning the pool's cap in exactly the hours capacity is out —
    physical, not fitted. ``member_mask`` (``(n_members, T)`` bool) restricts
    the sum to a member subset per hour — the online / offline-fast-start
    scoping of the ``caiso_reserve_online_scoped`` product split (the
    ``pjm_pergen_pool_ramp10`` convention). ``None`` sums every member.
    """
    gidx = np.asarray(gen_idx, dtype=int)
    avail = np.asarray(fleet_arrays.availability, dtype=float)[gidx]
    member_ramp_t = np.asarray(ramp10, dtype=float)[gidx][:, np.newaxis] * avail
    if member_mask is not None:
        member_ramp_t = np.where(member_mask, member_ramp_t, 0.0)
    col_ramp10 = np.zeros((n_r, member_ramp_t.shape[1]), dtype=float)
    np.add.at(col_ramp10, np.asarray(col, dtype=int), member_ramp_t)
    return col_ramp10


def _caiso_locational_as_families(
    zone_names: list[str] | None,
    n_zones: int,
    hours: int,
    sim_year: int | None,
    spin_pen: np.ndarray,
    spin_wid: np.ndarray,
    nonspin_pen: np.ndarray,
    nonspin_wid: np.ndarray,
) -> list[ReserveFamily]:
    """Build the measured zone-masked SP26/NP26 spin/non-spin reserve families.

    Reads the CAISO OASIS AS_REQ regional MINIMUM series
    (``data.caiso_as_requirements.load_caiso_as_requirements``) for ``sim_year``
    and returns one :class:`ReserveFamily` per (region, product) whose
    ``zone_mask`` selects the model zones south / north of Path 26
    (``REGION_ZONES``). The shortfall steps reuse the system product's published
    tariff curves — a regional shortfall prices at the same ORDC, and each
    system step total spans the (smaller) regional requirement, keeping the
    balance feasible at zero reserve.

    Requires ``sim_year`` (the requirement is a forward-indexed measured series);
    raises when it is absent so the flag never silently adds an empty family.
    """
    from market_sim.data.caiso_as_requirements import (
        REGION_ZONES,
        load_caiso_as_requirements,
    )

    if sim_year is None:
        raise ValueError(
            "caiso_locational_as_families=True requires sim_year (the measured "
            "OASIS AS_REQ requirement is indexed by backcast year)."
        )
    if zone_names is None:
        raise ValueError("caiso_locational_as_families=True requires zone_names.")

    names = list(zone_names)
    idx = {z: i for i, z in enumerate(names)}
    req = load_caiso_as_requirements(int(sim_year), hours, bound="min")
    steps = {
        "spin": (spin_pen, spin_wid),
        "nonspin": (nonspin_pen, nonspin_wid),
    }
    region_key = {"AS_SP26": "sp26", "AS_NP26": "np26"}

    families: list[ReserveFamily] = []
    for region, zones in REGION_ZONES.items():
        mask = np.zeros(n_zones, dtype=bool)
        for z in zones:
            if z in idx:  # WECC import nodes / absent zones simply drop out
                mask[idx[z]] = True
        if not mask.any():
            continue
        for product in ("spin", "nonspin"):
            key = f"{region_key[region]}_{product}"
            if key not in req:
                continue
            pen, wid = steps[product]
            families.append(
                ReserveFamily(
                    name=f"caiso_{region_key[region]}_{product}",
                    requirement=req[key].astype(float),
                    zone_mask=mask,
                    ordc_penalties=pen,
                    ordc_step_widths=wid,
                    reserve_class=0,
                )
            )
    return families


def _caiso_design(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    zone_names: list[str] | None = None,
    *,
    system_load: np.ndarray | None = None,
    sim_year: int | None = None,
) -> ReserveDesign:
    """CAISO per-generator energy+reserve co-optimization (issue #1492, L-10).

    Two co-optimized upward contingency-reserve products — **Spinning** and
    **Non-Spinning** — drawn from ONE shared per-generator R pool (the MISO
    ``miso_reserve_pergen`` structure): one ``R[r,t]`` column per (zone,
    fuel-class) pool of reserve-eligible thermal units with nonzero 10-minute
    ramp, joint ``Σ P + R ≤ Σ pmax·availability`` per pool-hour, and
    ``R[r] ≤ Σ FleetArrays.ramp10`` as a variable bound. Both product families
    span every CAISO zone and share the pool, so a shortfall in either prices
    the same marginal MW and the two shortfall duals SUM into the energy LMP —
    the §27.1.2.4 co-optimization behaviour ("upward products sum toward the bid
    cap when all short"). The pergen ramp bound is what makes the requirement
    bite: a zone-aggregate ungated family clears inertly from ~10 GW of idle
    evening CC headroom at zero opportunity cost (the MISO lesson, issue #1492).

    Requirement (BAL-002-WECC-3 R1 Contingency Reserve): the hourly
    ``max(MSSC, CAISO_CONTINGENCY_FRAC × load)`` — the fleet-derived
    most-severe single contingency (``largest_single_contingency_mw``,
    availability-aware, plant-aggregated) floored under 6% of load — split
    :data:`CAISO_SPIN_FRACTION` half spinning / half non-spinning (WECC-3 +
    DMM practice). When ``system_load`` is unavailable the requirement falls
    back to the flat MSSC floor. Shortfalls price at the PUBLISHED tariff
    §27.1.2.3.5 scarcity reserve demand curves
    (:data:`CAISO_SPIN_DEMAND_CURVE` / :data:`CAISO_NONSPIN_DEMAND_CURVE`)
    against the :data:`CAISO_ENERGY_BID_CAP_SOFT` anchor — every step a tariff
    value, zero fitted breakpoints (rules 5/23).

    Participation (issue #1492 design constraints 2/3, completed): **storage**
    — CAISO's dominant AS provider (DMM 2023-25 battery special reports) —
    backs reserve through the duration-gated per-zone ``RS[c,z]`` columns
    (``dispatch._build_reserve_rows_pergen`` storage gate): power competition
    against its own charge/discharge and an ASSOC state-of-charge gate at the
    published 30-minute sustain (:data:`CAISO_AS_SUSTAIN_DURATION_H`).
    **Hydro** — a major certified spin/non-spin provider — joins the pergen
    pool via :func:`_caiso_reserve_eligible`, with its 10-minute deliverable
    ramp backfilled from :data:`CAISO_HYDRO_RAMP10_FRAC` (hydro has no CEMS,
    so no measured ramp-capability row exists; the thermal ``RAMP10_FRAC``
    tables stay hydro-free for every other ISO). Both ADD reserve supply, so
    this completed build prices LESS scarcity than the thermal-only caiso-59
    probe — the honest direction (the issue's ex-ante note: the thermal-only
    pool over-states scarcity).

    Online-quality scoping (``caiso_reserve_online_scoped``, GATED default
    off — the issue-#1492 "correct build" increment, C1 lane 2026-07-16):
    splits each pool into a SPIN product column (online 10-minute ramp only —
    spinning reserve is synchronized capacity, tariff §8.4 / Appendix K;
    scoped at the P0→P1 seam from the model's own P0 run pattern,
    ``pipeline.commitment.caiso_pergen_sync_reserve_caps`` — the
    ``pjm_reserve_pergen_sync`` convention) and a NONSPIN column (offline
    fast-start ramp; offline slow iron backs nothing), sharing the pool's
    joint P+R headroom row. The families become the nested tariff
    procurement: spin (½ requirement, spin curve, SPIN columns + storage RS)
    and contingency-total (FULL requirement, non-spin curve, all columns —
    downward substitution). Mutually exclusive with
    ``caiso_commitment_posture`` (rule 19) and not composed with
    ``caiso_locational_as_families``.

    Remaining gap: **Regulation Up/Down** (no forward-derivable requirement
    series; RegDown is a downward product the upward-headroom pergen row does
    not model).
    """
    from market_sim.results.scarcity import (
        caiso_reserve_demand_steps,
        largest_single_contingency_mw,
    )

    eligible = _caiso_reserve_eligible(fleet_arrays)
    # Pool structure + hydro-backfilled ramp10 from the shared helper — the
    # same call pipeline.commitment.caiso_pergen_sync_reserve_caps makes at
    # the P0→P1 seam, so the column order is identical by construction.
    pergen_gen_idx, pergen_col, n_r, ramp10 = caiso_pergen_structure(fleet_arrays)

    online_scoped = bool(getattr(config, "caiso_reserve_online_scoped", False))
    if online_scoped and getattr(config, "caiso_commitment_posture", False):
        raise ValueError(
            "caiso_reserve_online_scoped and caiso_commitment_posture are "
            "mutually exclusive (CLAUDE.md rule 19 — one mechanism per "
            "phenomenon): the posture U re-anchor and the seam online scoping "
            "gate the same online-capacity phenomenon"
        )
    if online_scoped and getattr(config, "caiso_locational_as_families", False):
        raise ValueError(
            "caiso_reserve_online_scoped is not composed with "
            "caiso_locational_as_families: the regional families need "
            "(zone AND product) balance_col_mask rows, which are not built"
        )

    T = int(hours)
    n_zones = int(np.max(fleet_arrays.zone_idx)) + 1

    # BAL-002-WECC-3 Contingency Reserve: max(MSSC, 6% load), hourly. MSSC is
    # the largest single *plant* over reserve-eligible units (common-mode,
    # availability-aware) — forward-responsive.
    mssc = float(
        largest_single_contingency_mw(
            fleet_arrays.pmax,
            availability=fleet_arrays.availability,
            reserve_mask=eligible,
            plant_code=fleet_arrays.plant_code,
        )
    )
    if system_load is not None:
        load = np.asarray(system_load, dtype=float).reshape(-1)
        if load.shape[0] != T:
            raise ValueError(f"caiso system_load length {load.shape[0]} != hours {T}")
        contingency = np.maximum(mssc, CAISO_CONTINGENCY_FRAC * load)  # (T,)
    else:
        # No load series available (should not happen on the solve path): fall
        # back to the flat MSSC floor so the design is still well-formed.
        contingency = np.full(T, mssc, dtype=float)
    spin_req = CAISO_SPIN_FRACTION * contingency
    nonspin_req = (1.0 - CAISO_SPIN_FRACTION) * contingency

    # Static ORDC steps sized to each product's MAX hourly requirement (tier
    # edges are fixed tariff MW; total width ≥ the tightest-hour requirement
    # keeps the balance feasible at zero reserve). Spin flat; non-spin tiered.
    spin_pen, spin_wid = caiso_reserve_demand_steps(
        float(spin_req.max(initial=0.0)),
        CAISO_SPIN_DEMAND_CURVE,
        CAISO_ENERGY_BID_CAP_SOFT,
    )
    nonspin_pen, nonspin_wid = caiso_reserve_demand_steps(
        float(nonspin_req.max(initial=0.0)),
        CAISO_NONSPIN_DEMAND_CURVE,
        CAISO_ENERGY_BID_CAP_SOFT,
    )

    all_zones = np.ones(n_zones, dtype=bool)
    if online_scoped:
        # Nested procurement (the tariff/BPM structure, the PJM PR⊇SR /
        # NYISO 30min⊇10min⊇spin convention): the SPIN family (½ the
        # BAL-002-WECC-3 requirement, §27.1.2.3.5 spin curve) is servable
        # only by the SPIN product columns + storage RS, and the
        # CONTINGENCY-TOTAL family carries the FULL requirement over ALL
        # columns with the non-spin curve — a spin MW substitutes down
        # (BPM AS downward substitution), and a total shortage with spin
        # met is by construction a non-spin shortage. This replaces the
        # co-drawn half/half convention, whose shared column pool made the
        # effective procurement max(half, half); when both families are
        # short the two shortfall duals still SUM into the marginal online
        # unit's LMP (§27.1.2.4), exactly as the co-drawn form priced it.
        total_pen, total_wid = caiso_reserve_demand_steps(
            float(contingency.max(initial=0.0)),
            CAISO_NONSPIN_DEMAND_CURVE,
            CAISO_ENERGY_BID_CAP_SOFT,
        )
        families = [
            ReserveFamily(
                name="caiso_spin",
                requirement=spin_req.astype(float),
                zone_mask=all_zones,
                ordc_penalties=spin_pen,
                ordc_step_widths=spin_wid,
                reserve_class=0,
            ),
            ReserveFamily(
                name="caiso_contingency_total",
                requirement=contingency.astype(float),
                zone_mask=all_zones,
                ordc_penalties=total_pen,
                ordc_step_widths=total_wid,
                reserve_class=0,
            ),
        ]
    else:
        families = [
            ReserveFamily(
                name="caiso_spin",
                requirement=spin_req.astype(float),
                zone_mask=all_zones,
                ordc_penalties=spin_pen,
                ordc_step_widths=spin_wid,
                reserve_class=0,
            ),
            ReserveFamily(
                name="caiso_nonspin",
                requirement=nonspin_req.astype(float),
                zone_mask=all_zones,
                ordc_penalties=nonspin_pen,
                ordc_step_widths=nonspin_wid,
                reserve_class=0,
            ),
        ]

    # Locational AS families (caiso_locational_as_families, default off): the
    # measured OASIS AS_REQ regional MINIMA south / north of Path 26 as
    # zone-masked spin/non-spin requirements, so a SoCal (SP26) reserve
    # shortfall must be covered by SoCal units — the locational driver the
    # system-wide co-opt cannot express. Shortfalls price at the SAME published
    # tariff curves (the system steps comfortably span each regional
    # requirement). EX-ANTE INERT on the current split topology — see the flag
    # docstring and FINDING-caiso71-locational-as-inert-2026-07-10.
    if getattr(config, "caiso_locational_as_families", False):
        families.extend(
            _caiso_locational_as_families(
                zone_names,
                n_zones,
                int(hours),
                sim_year,
                spin_pen,
                spin_wid,
                nonspin_pen,
                nonspin_wid,
            )
        )

    # PER-ASSET R columns (dispatch._build_reserve_rows_pergen), one per
    # (zone, fuel-class) pool of reserve-eligible units deliverable within
    # 10 min (structure from caiso_pergen_structure above). Availability-scaled
    # hourly deliverable ramp per column, (n_r, T) — physical, not fitted.
    col_ramp10 = caiso_pergen_pool_ramp10(
        fleet_arrays, pergen_gen_idx, pergen_col, n_r, ramp10
    )

    if online_scoped:
        # Product-split column layout (the pjm_reserve_pergen_sync structure):
        # [0, n_r) = SPIN columns, [n_r, 2*n_r) = NONSPIN columns; both
        # columns of pool p share joint P+R headroom row p. Family masks:
        # spin is servable only by SPIN columns (+ storage RS — a battery is
        # spin-quality, the ASSOC gate unchanged); the contingency-total
        # family draws every column. P0 caps carry the all-online assumption
        # (the base-cost discovery run has no commitment pattern yet): SPIN =
        # the full availability-scaled pool deliverable ramp, NONSPIN = 0.
        # The P0→P1 seam recomputes both from the P0 run pattern
        # (pipeline.commitment.caiso_pergen_sync_reserve_caps).
        col_pool = np.tile(np.arange(n_r, dtype=int), 2)
        spin_sel = np.concatenate([np.ones(n_r, dtype=bool), np.zeros(n_r, dtype=bool)])
        balance_col_mask = np.stack([spin_sel, np.ones(2 * n_r, dtype=bool)], axis=0)
        return ReserveDesign(
            families=families,
            eligible=eligible.reshape(1, -1),
            # Storage participation is unchanged from the unscoped design:
            # RS[0,z] backs BOTH nested families (spin-quality) through the
            # duration-gated columns at the published 30-minute ASSOC sustain.
            storage_eligible=True,
            storage_duration_h=np.array([CAISO_AS_SUSTAIN_DURATION_H], dtype=float),
            pergen_gen_idx=pergen_gen_idx,
            pergen_col=pergen_col,
            pergen_ramp10=np.vstack([col_ramp10, np.zeros_like(col_ramp10)]),
            pergen_col_pool=col_pool,
            balance_col_mask=balance_col_mask,
        )

    # Commitment-posture lever (design note §A): U/SU columns on the
    # non-fast-start pools, gated on caiso_commitment_posture — MISO's
    # _posture_pool_params verbatim (measured/published pool params, rule-18
    # fast-start exemption by pool physics). Makes reserve provision cost a
    # real start + min-load ride, so the spin/non-spin requirement can
    # commit gas the way CAISO's RTPD/RUC does (caiso-70 FINDING redirect).
    posture_pools = posture_mlf = posture_startup = None
    if getattr(config, "caiso_commitment_posture", False):
        posture_pools, posture_mlf, posture_startup = _posture_pool_params(
            fleet_arrays,
            pergen_gen_idx,
            pergen_col,
            n_r,
            str(config.iso),
        )

    return ReserveDesign(
        families=families,
        eligible=eligible.reshape(1, -1),
        # Storage participation (issue #1492 constraint 2): batteries + pumped
        # storage back reserve via the duration-gated RS[c,z] columns with the
        # published 30-minute ASSOC sustain. One reserve class on this layout,
        # so the single duration applies to both co-drawn products.
        storage_eligible=True,
        storage_duration_h=np.array([CAISO_AS_SUSTAIN_DURATION_H], dtype=float),
        pergen_gen_idx=pergen_gen_idx,
        pergen_col=pergen_col.astype(int),
        pergen_ramp10=col_ramp10,
        posture_pools=posture_pools,
        posture_mlf=posture_mlf,
        posture_startup=posture_startup,
    )
