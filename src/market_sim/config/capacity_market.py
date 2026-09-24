"""Capacity-market, cap-and-trade, adequacy and storage-value registries.

Split out of ``config/constants.py`` (refactor-consolidation plan §5, D-1:
constants split, 2026-07). Pure transplant — every value and citation comment
is byte-identical to its pre-split form; ``config.constants`` re-exports the
entire surface, so both import paths resolve to the same objects.

Contents: the cap-and-trade / mass-cap program registry (CapAndTradeProgram,
CARB/RGGI budgets), storage techs and deployment caps, the capacity demand
curves (CapacityDemandCurvePoint / evaluate_demand_curve, MarketDesign,
resolve_capacity_market_clearing, seasonal RBDC, per-delivery-year vintages),
renewable/storage/thermal ELCC and accreditation registries, planning reserve
margins, RPS floors, and interconnection queue caps.
"""

import logging
from dataclasses import dataclass

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
# nameplate capacity, computed by `scripts/data/derive_pjm_rggi_zone_share.py` from
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
# 2020-2022 ADDED (pjm-h22, 2026-09-24): same script, same recipe, run over
# 2020-2025 against the year-matched `vintage_2020..2022` EIA-860 tables; the
# rerun reproduces the committed 2023-2025 values EXACTLY. Without these rows
# `_zone_share_for_year` held 2023's Dominion 0.9881 into 2020, a year Virginia
# was not a member.
PJM_RGGI_ZONE_SHARE: dict[str, dict[int, float]] = {
    "PJM_ComEd": {2020: 0.0, 2021: 0.0, 2022: 0.0, 2023: 0.0, 2024: 0.0, 2025: 0.0},
    "PJM_AEP_Ohio": {2020: 0.0, 2021: 0.0, 2022: 0.0, 2023: 0.0, 2024: 0.0, 2025: 0.0},
    "PJM_ATSI": {2020: 0.0, 2021: 0.0, 2022: 0.0, 2023: 0.0, 2024: 0.0, 2025: 0.0},
    "PJM_West_APS": {
        2020: 0.0107,
        2021: 0.0102,
        2022: 0.0102,
        2023: 0.0108,
        2024: 0.0,
        2025: 0.0,
    },
    "PJM_Central_PA": {
        2020: 0.0,
        2021: 0.0,
        2022: 0.0,
        2023: 0.0,
        2024: 0.0,
        2025: 0.0,
    },
    "PJM_Dominion": {
        2020: 0.0,
        2021: 0.9893,
        2022: 0.9894,
        2023: 0.9881,
        2024: 0.0,
        2025: 0.0,
    },
    "PJM_EMAAC": {
        2020: 0.7336,
        2021: 0.7346,
        2022: 0.7331,
        2023: 0.7327,
        2024: 0.7252,
        2025: 0.7221,
    },
    "PJM_SWMAAC": {
        2020: 0.998,
        2021: 0.9979,
        2022: 0.9976,
        2023: 0.9976,
        2024: 0.9976,
        2025: 0.9976,
    },
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
# data/clean/ via scripts/data/curate_*.py; the clean tree is gitignored so the
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
#
# 2021 ADDED (FH-2, hindcast-forward plan §4 row 14): 2021 is the hindcast SEED
# solve year (holdout_policy.HINDCAST_SEED_YEARS), so it is a year the model
# actually solves, and without its own row per_generator_membership fell back to
# ``max(RGGI_MEMBER_STATES_BY_YEAR)`` — the 2025, post-Virginia-exit set — for a
# 2021 solve, silently un-enrolling Virginia in the very year it joined. The row
# is a published legal fact (participating-states list), carries no measured
# quantity, and is byte-neutral for every 2023-2025 run (a new key only).
# **2022 is NOT added**: it is the plan's evolved-never-solved bridge year whose
# contract is that its data is never read (FH-1 §6), and this file's own
# convention omits 2022/H1-2026 rows under rule 22 whose intake clause requires
# per-window owner authorization. Recorded on the FH-2 disclose list instead.
# Source: RGGI, Inc. participating-states list (rggi.org/program-overview-and-
# design/elements); Virginia joined effective 2021-01-01 (9 VAC 5-140, Art. 8);
# Virginia Clean Economy and Equity Act repeal, effective 2024-01-01.
#
# 2020 AND 2022 ADDED (pjm-h22, 2026-09-24): `[R-HOLDOUT]` — the rule-22
# quarantine the 2022 omission above cites — was REMOVED 2026-09-09, and PJM's
# keeper solves every year 2020-2025 (rules 16/34(c)), so the 2022 fallback to
# the 2025 set un-enrolled Virginia in a year it was a member. Published legal
# facts, no measured quantity: New Jersey rejoined effective 2020-01-01
# (N.J.A.C. 7:27C, adopted 2019; RGGI, Inc. "New Jersey Rejoins RGGI",
# 2020-01-01) and Virginia was a member 2021-2023 (sources above). 2020 is the
# 2025 set exactly (NJ in, VA not yet), so the 2020 row is byte-neutral for
# every consumer; the 2022 row adds VA.
RGGI_MEMBER_STATES_BY_YEAR: dict[int, frozenset[str]] = {
    2020: frozenset({"NY", "CT", "MA", "ME", "NH", "RI", "VT", "MD", "DE", "NJ"}),
    2021: frozenset({"NY", "CT", "MA", "ME", "NH", "RI", "VT", "MD", "DE", "NJ", "VA"}),
    2022: frozenset({"NY", "CT", "MA", "ME", "NH", "RI", "VT", "MD", "DE", "NJ", "VA"}),
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
#
# Li-ion capex/FOM are DERIVED from the committed NREL ATB 2024 extract
# (scripts/data/derive_cost_benchmark_envelope.py::derive_storage_li_ion,
# asserted by tests/test_cost_benchmark_envelope.py — capacity-cost-grounding
# session 2026-07-19): ATB Moderate utility-scale battery @2026 in the model's
# constant 2026$ (the exact FF-1E NEW_ENTRY_COSTS convention). This REPLACES
# the prior hand-set values (4hr $1,140/kW, 8hr $2,280, 12hr $3,100) whose
# "NREL ATB 2024 / BNEF 2025" labels matched no published ATB point — the
# committed ATB battery rows were on disk but never read. The re-derived level
# sits mid-envelope of the 2024-2026 literature for an all-in developer basis:
# S&L Jan-2024 150MW/600MWh $1,744/kW (2023$); AEO2026 EMM $1,521/kW (2025$);
# Brattle 2025 PJM CONE BESS 4-hr $1,750-1,980/kW (nominal 2028 online, incl.
# interconnection + owner costs); Lazard LCOS v10.0 utility 4-hr computes
# $565-1,459/kW (2025$, EPC-scope, excl. augmentation — its low end is a
# minimal-BOS config, not an all-in developer cost). Full table + links:
# data/raw/new-build-cost-benchmarks/ and
# docs/new-build-cost-methodology-2026-07.md §4.
#
# li_ion_12hr extends ATB's own EXACTLY-linear power/energy cost split across
# its 2/4/6/8/10-hr classes to 12 h (fixed $/kW power component + $/kWh energy
# slope; residual 0 on the committed extract — the derive script hard-fails if
# ATB's structure stops being linear). capex_per_kwh is the bundled
# capex_per_kw / duration convention the degradation term uses. rte / cycles /
# learning_rate / lifetime are NOT ATB CAPEX/FOM quantities and keep their
# existing bases (rte 0.86 li-ion, ATB round-trip efficiency; learning 0.18
# BNEF li-ion learning curve).
#
# iron_air (DOE Pathways to Commercial Liftoff: Long Duration Energy Storage,
# May 2023; Form Energy's public <$20/kWh energy-cost target corroborates) and
# flow_battery / compressed_air (PNNL 2022 Grid Energy Storage Technology Cost
# and Performance Assessment, Viswanathan et al., PNNL-33283: VRFB 100MW/10hr
# total installed ≈$443.5/kWh 2021$; CAES geology-dependent, model config is
# non-cavern adiabatic) keep their recorded values: their primaries could not
# be re-fetched from this environment at the 2026-07-19 intake
# (liftoff.energy.gov DNS-unreachable, pnnl.gov PDF bot-walled) so they are
# benchmarks_2026.csv verified=0 rows — citations corrected here (the old
# "PNNL 2023"/"NREL ATB 2024" labels pointed at documents that do not carry
# CAES/VRFB numbers), values unchanged, flagged for browser re-verification.
STORAGE_TECHS: dict[str, dict[str, float]] = {
    "li_ion_4hr": {  # 4-hour lithium-ion battery
        "duration_hr": 4,
        "rte": 0.86,
        "cycles": 5000,
        "capex_per_kw": 1810.3,  # ATB 2024 Moderate 4Hr Battery @2026, 2026$ (derived)
        "capex_per_kwh": 452.6,  # capex_per_kw / 4 h (bundled convention, derived)
        "fom_per_kw_yr": 40.9,  # ATB 2024 Moderate @2026, 2026$ (derived)
        "learning_rate": 0.18,
    },
    "li_ion_8hr": {  # 8-hour lithium-ion battery
        "duration_hr": 8,
        "rte": 0.86,
        "cycles": 5000,
        "capex_per_kw": 3154.3,  # ATB 2024 Moderate 8Hr Battery @2026, 2026$ (derived)
        "capex_per_kwh": 394.3,  # capex_per_kw / 8 h (bundled convention, derived)
        "fom_per_kw_yr": 73.4,  # ATB 2024 Moderate @2026, 2026$ (derived)
        "learning_rate": 0.18,
    },
    "iron_air": {  # DOE LDES Liftoff (May 2023) — 100-hour iron-air battery
        "duration_hr": 100,
        "rte": 0.50,
        "cycles": 3000,
        "capex_per_kw": 2000.0,  # verified=0 (primary unreachable 2026-07-19)
        "capex_per_kwh": 20.0,  # Form Energy public <$20/kWh energy-cost target
        "fom_per_kw_yr": 20.0,
        "learning_rate": 0.10,
    },
    # Additional long-duration storage technologies. ``capex_per_kw`` is the
    # total capital per kW of power (energy capex × duration + power capex),
    # matching the convention of the li-ion / iron-air entries above.
    "li_ion_12hr": {  # 12-hour lithium-ion battery (ATB linear split @12 h)
        "duration_hr": 12,
        "rte": 0.78,  # lower RTE at longer duration
        "cycles": 4000,
        "capex_per_kw": 4498.4,  # ATB 2024 linear power/energy split @12h, 2026$ (derived)
        "capex_per_kwh": 374.9,  # capex_per_kw / 12 h (bundled convention, derived)
        "fom_per_kw_yr": 105.8,  # ATB 2024 linear FOM split @12h, 2026$ (derived)
        "learning_rate": 0.15,  # BNEF lithium-ion learning curve 2024
        "lifetime_yr": 20,
    },
    "flow_battery": {  # PNNL-33283 (2022) — vanadium redox flow battery
        "duration_hr": 10,
        "rte": 0.70,  # vanadium redox. PNNL-33283
        "cycles": 15000,  # long cycle life — major advantage. PNNL-33283
        "capex_per_kw": 4700.0,  # 350 $/kWh × 10 h + 1200 $/kW power (verified=0)
        "capex_per_kwh": 350.0,
        "fom_per_kw_yr": 15.0,
        "learning_rate": 0.10,
        "lifetime_yr": 25,
    },
    "compressed_air": {  # PNNL-33283 (2022) — adiabatic compressed-air storage
        "duration_hr": 8,
        "rte": 0.55,  # adiabatic CAES
        "cycles": 10000,
        "capex_per_kw": 2700.0,  # 150 $/kWh × 8 h + 1500 $/kW power (verified=0;
        # non-cavern adiabatic config — salt-cavern CAES is cheaper but
        # geology-gated, which this ISO-agnostic entry screen cannot site)
        "capex_per_kwh": 150.0,
        "fom_per_kw_yr": 10.0,
        "learning_rate": 0.05,  # mature concept, limited recent deployment
        "lifetime_yr": 40,  # Huntorf plant operating since 1978
    },
}

# First calendar year each STORAGE_TECHS technology class is admissible for
# economic new entry, consumed by model.storage._storage_entry_candidates
# under ScenarioConfig.storage_entry_availability_gate (GATED default OFF) —
# the storage analogue of the thermal path's _EMERGING_AVAILABLE_YEAR gate
# (capacity_evolution/new_entry.py). Repairs defect D-2 of
# docs/FINDING-entry-screen-t1h-2026-08.md (the T1-H lane decided 3 GW of
# 100-hour iron-air + 2 GW of vanadium flow in a 2023 ERCOT decision year);
# charter docs/PRECOMMIT-t1h-capacity-entry-2026-08-30.md Phase-1 Leg A.
#
# DERIVATION (measured, never invented — rule 5 [R-NO-MAGIC]; the Phase-0
# census, docs/FINDING-t1h-capacity-entry-phase0-2026-08-30.md §2.2, is the
# committed record): each year is the FIRST YEAR WITH NONZERO NATIONAL
# OPERATING CAPACITY of the technology class in the EIA-860 2025 Early
# Release energy-storage schedule
# (data/raw/eia-860/eia860_energy_storage_operable.parquet, min "Operating
# Year" per "Storage Technology 1" code). A class with zero national
# operating base EVER is FAIL-CLOSED (None = never admissible) until a first
# observed year exists in the data. Rule 13 [R-MEASURED] admissibility: a
# first-commercial-operation year is a market fact that regenerates for any
# forward year from the then-current EIA-860 vintage and responds to actual
# deployment (a class's first COD landing moves its gate), and it is an
# INPUT (eligibility), never a pin of the model's build volume to observed
# CODs.
#
#   LIB (all li-ion durations): first US operating year 2012
#       (42,350.6 MW / 957 units operable at the 2025 ER). The three li-ion
#       entries share the LIB class — EIA-860 classes by chemistry, not
#       duration.
#   FLB (vanadium redox flow):  first US operating year 2017
#       (321.0 MW / 11 units).
#   MAB (metal-air, iron-air):  first US operating year 2024
#       (1.6 MW / 1 unit — Form Energy's first COD).
#   compressed_air: None (FAIL-CLOSED). The class this entry models is
#       NON-CAVERN ADIABATIC CAES (its own capex comment above), and the
#       EIA-860 record contains ZERO MW of it ever: CAES is absent from the
#       energy-storage schedule entirely, and the only US CAES generator
#       (eia860_generator_operable.parquet, Prime Mover "CE": McIntosh AL,
#       110 MW, Operating Year 1991) is a DIABATIC salt-cavern unit — the
#       geology-gated technology the capex comment above explicitly says
#       this ISO-agnostic screen does not model. It therefore cannot supply
#       the modeled class's first observed year, and the gate fails closed.
STORAGE_TECH_AVAILABLE_YEAR: dict[str, int | None] = {
    "li_ion_4hr": 2012,  # EIA-860 2025 ER, LIB class first operating year
    "li_ion_8hr": 2012,  # EIA-860 2025 ER, LIB class first operating year
    "li_ion_12hr": 2012,  # EIA-860 2025 ER, LIB class first operating year
    "iron_air": 2024,  # EIA-860 2025 ER, MAB class first operating year
    "flow_battery": 2017,  # EIA-860 2025 ER, FLB class first operating year
    "compressed_air": None,  # fail-closed: zero national base of the modeled
    # (non-cavern adiabatic) class ever — see derivation note above
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
    # CAISO re-vintaged 2026-08-04 (FFR-4D). The shipped row was the only CAISO
    # entry NOT built by the EIA-860 construction documented above -- it came
    # from "CAISO TPP 2024 - ~8 GW operational + under construction", a
    # hand-rounded 2023-vintage figure. Re-derived by that same documented
    # construction on the same EIA-860 2025 Early Release release:
    #   mid  = operable Status="OP" nameplate, BA CISO = 15,448.4 -> 15_450
    #   high = mid + proposed Status in {U,V,TS} = 19,262.3 -> 19_260
    #   low  = rounded mid x 0.75 = 11,587.5 -> 11_590
    # The construction reproduces the four ISOs it already governs EXACTLY
    # (MISO 801.9->800, PJM 497.1->500, NYISO 252.7->250 / 278.3->280,
    # NEISO 765.4->770 / 1,280.1->1,280), which is what licenses applying it
    # here. Independent closure check against CAISO's own published ledger:
    # 14,131 MW battery Net Dependable Capacity (2026 Summer Loads & Resources
    # Assessment Table 1.1) vs 15,448.4 MW EIA-860 nameplate -- NDC is 91.5 %
    # of nameplate, the expected post-derate relationship.
    # Rule 23 [R-FROZEN-DERIVE]: the re-derivation licence is the SOURCE-DATA
    # vintage (EIA-860 2025 ER, already on disk and already cited by the four
    # rows above), NOT a residual. ERCOT's row is the other hand-entered entry
    # (17,000 vs 13,709.3 by this construction) and is deliberately UNTOUCHED
    # -- rule 25 [R-ISO-SCOPE]; it is routed, not fixed, in the FFR-4D handoff.
    # See docs/handoffs/ffr-4d-caiso-fleet-vintage-2026-08-04.md sections 3-4.
    "CAISO": {
        "low": 11_590.0,
        "mid": 15_450.0,
        "high": 19_260.0,
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
    # SPP (registered 2026-09-06, lane SPP-20): the SAME documented EIA-860
    # construction as the PJM/MISO/NYISO/NEISO rows and the FFR-4D CAISO
    # re-derivation, on the same EIA-860 2025 Early Release, BA code SWPP:
    #   mid  = operable Status="OP" nameplate               =   450.5 ->   450
    #   high = mid + proposed Status in {U, V, TS} (+67.0)  =   517.5 ->   520
    #   low  = mid x 0.75                                   =   337.9 ->   340
    # Cross-check against SPP's OWN ledger: the MMU counts 14 market-registered
    # storage resources / 728 MW at YE-2025 INCLUDING six pumped-storage units
    # (SOM 2025 §2.7, PDF p. 70; batteries alone 422 MW, Fig. 2-12) — EIA-860's
    # 450.5 MW battery schedule sits between the YE-2024 (142 MW) and YE-2025
    # (422 MW) market counts plus unregistered sites, as the vintage implies
    # (docs/multi-iso/spp-data-audit.md §2.3). Zero DOF; rule 13-admissible.
    "SPP": {
        "low": 340.0,
        "mid": 450.0,
        "high": 520.0,
    },
    # NWPP (registered 2026-09-14, lane NWPP-20): the same EIA-860 2025 Early
    # Release construction, on the WECC-admitted seventeen-BA footprint
    # (fleet.models.footprint_plant_mask):
    #   mid  = operable Status="OP" battery nameplate = 2,321.0 -> 2_320
    #   high = mid + proposed Status in {U,V,TS} = 2,321.0 + 2,147.0 -> 4_470
    #   low  = rounded mid x 0.75 = 1,740
    # (docs/handoffs/PRECOMMIT-nwpp-20-2026-09-14.md §3.7). Zero DOF; rule
    # 13-admissible. NEVP holds 1,135 MW of the operable 2,321 (audit §2.4).
    "NWPP": {
        "low": 1_740.0,
        "mid": 2_320.0,
        "high": 4_470.0,
    },
    # SOCO (registered 2026-09-14, lane SOCO-20): the SAME documented EIA-860
    # construction, on the same EIA-860 2025 Early Release, BA code SOCO —
    # EXCLUDING the McIntosh compressed-air unit (plant 7063, 110 MW on the
    # energy-storage schedule), which owner card S7 carries as a 25 MW gas CT
    # on the generator schedule instead (model.storage.load_eia860_storage
    # skips compressed-air rows for the same reason; rule 19, one unit once),
    # and excluding the rejected 1.0 MW Massachusetts battery (audit §2.6(a)):
    #   mid  = operable Status="OP" batteries              =   147.7 ->   150
    #   high = mid + proposed Status in {U, V} (+775.0)     =   922.7 ->   920
    #          (no TS row; U 765.0 = Hammond, Robins AFB, Moody AFB, McGrau
    #          Ford; V 10.0 = Allatoona)
    #   low  = mid x 0.75                                   =   110.8 ->   110
    # Context, not a ceiling: the L (regulatory-approved) rows add 600 MW for
    # 2029 (Dega, Pepper Hammock) and P 76 MW for 2027. Zero DOF;
    # rule 13-admissible.
    "SOCO": {
        "low": 110.0,
        "mid": 150.0,
        "high": 920.0,
    },
}

# ISOs whose BACKCAST resolves its storage base fleet AS OF THE SOLVE YEAR from
# EIA-860 (model.storage.load_eia860_storage) instead of the forward-looking
# STORAGE_BASE_FLEET_MW ladder above, under ScenarioConfig.
# storage_measured_base_fleet. This is the storage analogue of what
# data.renewables ALREADY does for wind/solar -- a backcast year takes that
# year's EIA-860 month-end capacity and only a forecast reads the scenario
# constant (FFR-4D, rule 14 [R-ACCURATE]).
#
# SCOPES THE BACKCAST LEG ONLY. The capacity-hindcast leg of the same seam
# (FFR-9A, model.storage.measured_storage_base_fleet_active) seeds from the
# run's own EIA-860 vintage in EVERY ISO without consulting this registry: a
# hindcast is not a keeper, so the keeper-byte-identity rationale below does
# not reach it (the FFR-3V renewable-seed precedent).
#
# CAISO only, deliberately (rule 25 [R-ISO-SCOPE]). CAISO is where the vintage
# error is first-order: its measured battery fleet doubles across the
# calibration window (7,492 / 11,131 / 15,448 MW at year-end 2023 / 2024 / 2025)
# while the scalar supplies a flat 8,000 MW, so a 2025 backcast runs 48 % short
# of the fleet that actually operated. The other five ISOs are NOT enrolled here
# because each enrollment moves that ISO's designated keeper and must be
# re-solved and re-gated in that ISO's own lane; for PJM / MISO / NYISO / NEISO
# the shipped scalar is within a few MW of the measured fleet anyway (the four
# were derived from it), so the correction there is immaterial. ERCOT is the one
# other ISO with a material gap (17,000 shipped vs 13,709.3 measured) and is
# routed, not fixed, in docs/handoffs/ffr-4d-caiso-fleet-vintage-2026-08-04.md.
STORAGE_MEASURED_BASE_FLEET_ISOS: frozenset[str] = frozenset({"CAISO"})

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
    "MISO": 62_000.0,  # ~50% of ~124 GW coincident peak. Source: MISO OMS Survey / Planning Resource Auction 2024
    # SPP: ~50% of the 56,184 MW all-time coincident peak (2023-08-21; SPP
    # Fast Facts, updated Sept 2026 — docs/multi-iso/spp-data-audit.md §2.3),
    # the same half-of-peak convention as every row above. Registered
    # 2026-09-06 by lane SPP-20.
    "SPP": 28_000.0,
    # NWPP: ~50 % of the 52,564 MW 2024 coincident footprint peak (EIA-930
    # Demand (Adjusted) over the seventeen BAs, docs/multi-iso/nwpp-data-
    # audit.md §4.2), the same half-of-peak convention as every row above.
    # Registered 2026-09-14 by lane NWPP-20.
    "NWPP": 26_000.0,
    # SOCO: ~50 % of the 47,368 MW measured all-time BA peak (2024-01-17 07:00
    # Central, EIA-930 ``Demand``; docs/multi-iso/soco-data-audit.md §3.1 —
    # a WINTER peak, card S6), the same half-of-peak convention as every row
    # above. Registered 2026-09-14 by lane SOCO-20.
    "SOCO": 23_700.0,
}

# Max new storage power per year (MW). Source: ERCOT CDR, CAISO TPP queue data,
# eastern-ISO interconnection-queue throughput.
STORAGE_ANNUAL_BUILD_CAP_MW: dict[str, float] = {
    "ERCOT": 5_000.0,
    "CAISO": 3_000.0,
    "PJM": 4_000.0,  # large queue but slower interconnection. Source: PJM queue 2024
    "NYISO": 1_500.0,  # Source: NYISO interconnection queue 2024
    "NEISO": 1_200.0,  # Source: ISO-NE interconnection queue 2024
    "MISO": 4_000.0,  # very large storage queue but slow interconnection (PJM-like). Source: MISO Generator Interconnection Queue 2024
    # SPP: MEASURED-ANCHORED, not an estimate. Demonstrated peak annual battery
    # COD 2021-2025 = 0.422 GW (EIA-860 2025 ER, BA SWPP, `Operating Year` by
    # technology; docs/multi-iso/spp-data-audit.md §5 row 12), so 500 MW is
    # the smallest 0.5 GW step at or above it — the QUEUE_CAP_GW convention
    # ("modestly above demonstrated peak annual COD"). Context, not a
    # ceiling: the battery-storage queue grew +6 GW to 31 GW in 2025 (SOM 2025
    # §2.5, PDF pp. 54-55, row 12b). Registered 2026-09-06 by lane SPP-20.
    "SPP": 500.0,
    # NWPP: smallest 0.5 GW step >= the demonstrated peak annual battery COD
    # on the footprint, 0.919 GW (2025; 0.898 in 2024 — EIA-860 2025 ER
    # Operating Year, audit §7 row 7 basis). Registered 2026-09-14 (NWPP-20).
    "NWPP": 1_000.0,
    # SOCO: MEASURED-ANCHORED by the same rule. Demonstrated peak annual
    # battery COD 2021-2025 in the EIA-860 2025 ER, BA SOCO, `Operating Year`
    # = 0.065 GW (2024, Mossy Branch; 2021 0.040 / 2022 0.040 / 2023 0.002;
    # docs/multi-iso/soco-data-audit.md §5 row 9), so 500 MW is the smallest
    # 0.5 GW step at or above it — the QUEUE_CAP_GW convention. Context, not a
    # ceiling: 775 MW is under construction (U/V) for 2026 and 600 MW more is
    # PSC-approved (L) for 2029 (STORAGE_BASE_FLEET_MW["SOCO"] derivation).
    # Registered 2026-09-14 by lane SOCO-20.
    "SOCO": 500.0,
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
    # RC-1C: MISO alone clears a SEASONAL PRA (four seasons, $/MW-day). When
    # present, the curve branch prices the market's own seasonal SUM
    # (:func:`seasonal_rbdc_price_per_firm_mw_yr`) instead of the single annual
    # ``demand_curve``; every other ISO leaves this ``None`` (annual grain).
    seasonal_rbdc: "SeasonalRBDC | None" = None

    def capacity_price_per_firm_mw_yr(
        self,
        config: "object | None" = None,
        reserve_position: "float | None" = None,
        iso: "str | None" = None,
        year: "int | None" = None,
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

        The curve gate is resolved per ISO through
        :func:`resolve_capacity_market_clearing` (RC-1B): when ``iso`` is given
        the ``config.capacity_market_clearing_by_iso`` override governs, else the
        scalar ``config.capacity_market_clearing``. Passing ``iso=None`` (every
        pre-CR-1 call site) reproduces the scalar-gated behavior byte-identically.

        ``year`` selects the per-delivery-year vintage (RC-1B item 2). It is
        consulted through :func:`resolve_demand_curve_vintage` ONLY inside the
        curve branch and ONLY when BOTH ``iso`` and ``year`` are supplied — the
        matched vintage's own ``net_cone_curve_per_kw_yr`` anchor and
        ``demand_curve`` shape then govern (a vintage whose shape is not
        normalizable carries ``demand_curve=()`` and prices on its flat anchor).
        Every pre-CR-1 call site passes ``year=None`` — the retirement,
        thermal-entry and storage-entry screens all thread the delivery year
        now (D28 doc-sync: the former "only storage new entry threads it"
        note was stale) — so the registry default curve/anchor governs only
        year-less callers, and at a delivery year whose vintage equals the
        registry reference (e.g. PJM 2026), the vintage override reproduces
        the registry price exactly.
        """
        if not self.capacity_market:
            return 0.0
        # capx D57 (2026-09-05, DESIGN-capx-d54 §3.5 / §7.2): the PRE-PRICED
        # object. When the supply-clearing gate
        # (:func:`resolve_capacity_market_supply_clearing`) is on, the
        # retirement screen has already cleared the fleet's net-ACR sell-offer
        # stack against this delivery year's VRR curve, and the thermal-entry
        # and storage-entry screens are PRICE TAKERS at that clearing price
        # (design §4.4: entry does not offer into the same stack, rule 19). The
        # runner / evolve_fleet thread the clearing result through the SAME
        # ``reserve_position`` slot every consumer already passes verbatim, so
        # the seam stays single: a :class:`ClearedCapacityPrice` (duck-typed on
        # ``price_per_firm_mw_yr``) short-circuits the curve evaluation; a
        # float position takes the census path below, byte-identically.
        _cleared = getattr(reserve_position, "price_per_firm_mw_yr", None)
        if _cleared is not None:
            return float(_cleared)
        # FFR-4F: CAISO's RA-MPB anchor, gated default-OFF. Resolved BEFORE the
        # curve branch because it replaces CAISO's capacity PRICE outright
        # (rule 19 -- it does not stack on, or re-anchor, a curve). It cannot
        # shadow a sloped curve today: CAISO publishes none, so this ISO always
        # reaches the flat branch below; the placement is so that stays true if
        # a curve is ever added without someone reconciling the two mechanisms.
        # Every other ISO resolves ``None`` here and is byte-identical.
        _caiso_anchor = resolve_caiso_ra_mpb_anchor(config, iso)
        if _caiso_anchor is not None:
            return _caiso_anchor * 1000.0
        if (
            reserve_position is not None
            and (self.demand_curve or self.seasonal_rbdc)
            and config is not None
            and resolve_capacity_market_clearing(config, iso)
            # RC-1C curve-eligibility governance gate (in addition to the
            # clearing gate): an ISO prices on its sloped curve only once its
            # accreditation-pairing basis is signed off; an INELIGIBLE ISO
            # prices its FIXED anchor even with the gate on. iso=None (no ISO
            # supplied) bypasses the gate → default path byte-identical. (NYISO
            # became eligible when its R5a ICAP->UCAP pairing landed — FF-3D
            # 2026-07-18; every registry ISO is now eligible.)
            and resolve_capacity_curve_eligible(iso)
        ):
            curve = self.demand_curve
            anchor = self.net_cone_curve_per_kw_yr or self.net_cone_per_kw_yr
            seasonal = self.seasonal_rbdc
            # RC-1B item 2: per-delivery-year vintage override — consulted ONLY
            # when BOTH iso and year are supplied. Every pre-CR-1 call site
            # passes year=None (guarded here), so it never fires and the price
            # stays byte-identical; only storage new entry threads a year.
            if iso is not None and year is not None:
                vintage = resolve_demand_curve_vintage(iso, year)
                if vintage is not None:
                    anchor = vintage.net_cone_curve_per_kw_yr or anchor
                    curve = vintage.demand_curve
                    seasonal = vintage.seasonal_rbdc
            # RC-1C: MISO seasonal grain — the market's own seasonal revenue SUM
            # (four seasonal RBDC evaluations at the one annual reserve position),
            # replacing the annual-curve approximation. Pre-RBDC MISO vintages
            # carry ``seasonal_rbdc=None`` + a vertical ``demand_curve``, so they
            # fall through to the scalar-curve branch below.
            if seasonal is not None:
                return seasonal_rbdc_price_per_firm_mw_yr(
                    seasonal, float(reserve_position)
                )
            if curve:
                frac = evaluate_demand_curve(curve, float(reserve_position))
                return frac * anchor * 1000.0
            # Vintage published a net-CONE anchor but no normalizable curve
            # shape (demand_curve=()): fall back to its flat anchor.
            return anchor * 1000.0
        if self.net_cone_per_kw_yr <= 0.0:
            return 0.0
        return self.net_cone_per_kw_yr * 1000.0


def resolve_capacity_market_clearing(
    config: "object | None", iso: "str | None" = None
) -> bool:
    """Return whether the CR-1 sloped capacity curve is active for ``iso``.

    The one seam every capacity-price call site reads the clearing gate
    through (RC-1B; P-2A §7 per-ISO flip). Resolution order:

    * ``config.capacity_market_clearing_by_iso`` (a ``{iso: bool}`` mapping)
      wins when it carries a row for ``iso`` — this is what lets a flip be ON
      for one ISO while OFF elsewhere;
    * otherwise the scalar ``config.capacity_market_clearing`` governs
      (default off).

    ``iso=None`` or a config without the mapping falls straight through to the
    scalar, so every pre-existing (scalar-only) call path is byte-identical.
    ``config`` is duck-typed via ``getattr`` so the config layer needs no
    import of :class:`ScenarioConfig`.
    """
    if config is None:
        return False
    by_iso = getattr(config, "capacity_market_clearing_by_iso", None)
    if by_iso and iso is not None and iso in by_iso:
        return bool(by_iso[iso])
    return bool(getattr(config, "capacity_market_clearing", False))


# capx D57: the ISOs for which the supply-clearing predicate has already
# logged its "curve gate off" refusal once per process (log-once discipline;
# the predicate is called per screen year and per consumer).
_SUPPLY_CLEARING_REFUSED_LOGGED: set[str] = set()


def resolve_capacity_market_supply_clearing(
    config: "object | None", iso: "str | None" = None
) -> bool:
    """Return whether the fleet's sell-offer stack CLEARS the curve for ``iso``.

    capx D57 (2026-09-05), building DESIGN-capx-d54-pjm-clearing-half
    §7.1: the sibling of :func:`resolve_capacity_market_clearing`. The CR-1
    curve gate decides WHICH curve prices adequacy; this gate decides the
    QUANTITY it is evaluated at — the auction's cleared quantity (the
    intersection of the fleet's net-ACR sell-offer stack with the published
    VRR curve, ``model/capacity_evolution/adequacy.py::
    clear_capacity_supply_stack``) instead of the installed-fleet census
    (:func:`~market_sim.model.capacity_evolution.adequacy.
    capacity_reserve_position`). Resolution:

    * ``config.capacity_market_supply_clearing_by_iso`` (a ``{iso: bool}``
      mapping, GATED default ``None`` ⇒ every ISO off ⇒ byte-identical) must
      carry a ``True`` row for ``iso``;
    * the CR-1 curve gate must ALSO resolve ON for ``iso`` and the ISO must be
      curve-eligible — a stack cannot clear against a flat net-CONE anchor
      (the design's stated precondition). A supply row armed over a curve
      gate that is off returns ``False`` and logs once.

    Generic in form, PJM-scoped by data (rule 25): PJM is the only registry
    ISO whose real mechanism is a sell-offer auction cleared against a VRR
    curve (design §4.9 — NYISO's spot market literally evaluates its curve at
    a census quantity; ISO-NE / MISO would be their own lanes). ``iso=None``
    or a config without the mapping is ``False`` so every pre-existing call
    path is byte-identical. Duck-typed via ``getattr`` like its sibling.
    """
    if config is None or iso is None:
        return False
    by_iso = getattr(config, "capacity_market_supply_clearing_by_iso", None)
    if not by_iso or not bool(by_iso.get(iso, False)):
        return False
    if not (
        resolve_capacity_market_clearing(config, iso)
        and resolve_capacity_curve_eligible(iso)
    ):
        if iso not in _SUPPLY_CLEARING_REFUSED_LOGGED:
            _SUPPLY_CLEARING_REFUSED_LOGGED.add(iso)
            logging.getLogger(__name__).warning(
                "capacity_market_supply_clearing_by_iso[%s] is armed but the CR-1 "
                "curve gate is off (or the ISO is curve-ineligible): a sell-offer "
                "stack cannot clear against a flat anchor — supply clearing "
                "resolves OFF for this ISO (DESIGN-capx-d54 §7.1)",
                iso,
            )
        return False
    return True


def resolve_capacity_going_forward_bar_published(
    config: "object | None", iso: "str | None" = None
) -> bool:
    """Return whether the screen's going-forward bar is the PUBLISHED ACR for ``iso``.

    capx D62 (2026-09-06), executing ``docs/handoffs/
    FINDING-capx-d61-2026-09-05.md`` §4. The third member of this module's
    per-ISO capacity-gate family, resolved exactly like its two siblings above.
    Resolution:

    * ``config.capacity_going_forward_bar_published_by_iso`` (a ``{iso: bool}``
      mapping, GATED default ``None`` ⇒ every ISO off ⇒ byte-identical) must
      carry a ``True`` row for ``iso``.

    WHAT IT CHANGES: the going-forward bar the retirement screen tests net
    revenue against — ``ScenarioConfig.fixed_om_<fuel> ×
    retirement_fom_multiplier_<fuel>``, an ATB **proxy**, becomes the ISO's own
    published default gross Avoidable Cost Rate (PJM Manual 18 Rev 62
    §5.4.8.4(B)), read from ``data/raw/capacity-market/avoidable-cost-rate/``
    through :mod:`market_sim.data.avoidable_cost_rate`. Because the D57
    clearing's ``offer_g = max(0, GFC_g − EAS_g) / (A_g × 365)`` reads the SAME
    ``going_forward_cost``, the exit bar and the sell-offer cap stay ONE object
    (DESIGN-capx-d54 §3.5; rule 19 [R-ONE-MECH]). It also arms the ONE
    out-of-market leg of the screen's margin, the published reactive component.

    NO SCALAR FIELD EXISTS and none may be added (rule 24 [R-REGISTRY]): the
    values are DATA, with source doc and page, and a different bar is a change
    to the published table.

    INDEPENDENT OF THE CLEARING HALF, deliberately: the bar is the screen's own
    going-forward cost and is meaningful with or without a cleared sell-offer
    stack, so this gate does NOT require
    :func:`resolve_capacity_market_supply_clearing` (unlike that gate, which
    genuinely cannot clear a stack against a flat anchor). Armed alongside it,
    the one bar serves both.

    Generic in form, PJM-scoped by data (rule 25 [R-ISO-SCOPE]): PJM is the only
    registry ISO publishing a generic technology-class going-forward bar that
    its own market caps sell offers with, and an ISO with no intaken table
    resolves to the ATB path for every unit. ``iso=None`` or a config without
    the mapping is ``False`` so every pre-existing call path is byte-identical.
    Duck-typed via ``getattr`` like its siblings.
    """
    if config is None or iso is None:
        return False
    by_iso = getattr(config, "capacity_going_forward_bar_published_by_iso", None)
    if not by_iso:
        return False
    return bool(by_iso.get(iso, False))


def resolve_capacity_adequacy_requirement_published(
    config: "object | None", iso: "str | None" = None
) -> bool:
    """Return whether ``iso``'s adequacy requirement is its OWN PUBLISHED MW.

    capx D67 (2026-09-06), executing ``docs/handoffs/
    FINDING-capx-d66-2026-09-06.md`` §8 card A. The fourth member of this
    module's per-ISO capacity-gate family, resolved exactly like its three
    siblings above.

    Resolution:

    * ``config.capacity_adequacy_requirement_published_by_iso`` (a
      ``{iso: bool}`` mapping, GATED default ``None`` => every ISO off =>
      byte-identical) must carry a ``True`` row for ``iso``.

    WHAT IT CHANGES: the OPERAND of the adequacy requirement the retirement
    reliability floor, the reserve-margin build backstop and the CR-1 position
    all test — ``model screen peak x FPR``, a RECONSTRUCTION, becomes the ISO's
    own published Reliability Requirement in MW for the delivery year the
    screen prices (:data:`RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO`, read at
    :func:`~market_sim.model.capacity_evolution.retirements.
    gross_adequacy_requirement_mw`). Because all three consume the one
    resolver, the requirement stays ONE object on every path (rule 19
    [R-ONE-MECH]; DESIGN-capx-d54 §3).

    WHY. D66 §3.1 decomposed the D57 clearing's remaining position error
    additively and measured the REQUIREMENT — not the supply census — as 78 %
    of it in 2024/25 and 67 % in 2025/26: the model's screen peak runs 2,481 MW
    (1.6 %) and 4,636 MW (3.0 %) above the peak PJM's own Reliability
    Requirement implies, and ``FPR x delta-peak`` reproduces
    ``R_model - R_published`` to the MW with zero residual. Reading the
    published MW makes the requirement INDEPENDENT of the model's peak in every
    in-table delivery year, which is what the auction's own denominator is.

    NO SCALAR FIELD EXISTS and none may be added (rule 24 [R-REGISTRY]): the
    values are DATA with source doc and page, digitized from the committed
    demand-curve rows and reconciled against them byte-for-byte by test.

    INDEPENDENT of the clearing half and of the published-bar gate: the
    requirement is the adequacy bar with or without a cleared sell-offer stack,
    so this gate requires neither. Armed alongside them, one requirement serves
    all three.

    Generic in form, PJM-scoped by DATA (rule 25 [R-ISO-SCOPE]): an ISO with no
    intaken table keeps its existing construction in every year, so the flag
    armed on another ISO's run is inert by construction — another ISO's
    analogue is that ISO's lane, on its own filings. NEISO's published Net ICR
    is the SAME idea already built as its own resolver (capx D40); it keeps
    its own gate rather than being folded in here, because the two series are
    different published quantities on different bases.

    ``iso=None`` or a config without the mapping is ``False`` so every
    pre-existing call path is byte-identical. Duck-typed via ``getattr`` like
    its siblings.
    """
    if config is None or iso is None:
        return False
    by_iso = getattr(config, "capacity_adequacy_requirement_published_by_iso", None)
    if not by_iso:
        return False
    return bool(by_iso.get(iso, False))


_NO_DEFAULT_CAP_REFUSED_LOGGED: set[str] = set()


def resolve_capacity_no_default_cap_convention(
    config: "object | None", iso: "str | None" = None
) -> bool:
    """Return whether a class with NO published default cap is a $0 price taker.

    capx D74 (2026-09-06), executing ``FINDING-capx-d61-2026-09-05.md`` §4 card
    (c) as widened by ``FINDING-capx-d62`` §9 item 2 — design
    ``DESIGN-capx-d74-pjm-steam-oil-convention-2026-09-06.md`` §3. The FIFTH
    member of this module's per-ISO capacity-gate family, resolved like its
    four siblings above, with ONE extra precondition. Resolution:

    * ``config.capacity_no_default_cap_convention_by_iso`` (a ``{iso: bool}``
      mapping, GATED default ``None`` ⇒ every ISO off ⇒ byte-identical) must
      carry a ``True`` row for ``iso``;
    * :func:`resolve_capacity_going_forward_bar_published` must ALSO resolve
      ON for ``iso``. The convention is a LIMB of the published default-ACR
      table — the row the table prints "NA" — and over the ATB FOM proxy no
      such cell exists, so a row armed over an unarmed bar returns ``False``
      and logs once (the :func:`resolve_capacity_market_supply_clearing`
      requires-the-curve pattern).

    WHAT IT CHANGES: a screened thermal unit whose published resource class
    carries no default gross ACR for the delivery year the screen prices (PJM
    Manual 18 Rev 62 §5.4.8.4(B): "Steam Oil & Gas" through DY 2025/26; §5.4.1:
    a sell offer above $0 needs a unit-specific ACR filing "or ... the default
    gross Avoidable Cost Rate of the applicable resource type, if available")
    is EXEMPT from the merchant screen in that year and sits in the D57
    stack's price-taking block at $0 on its accredited MW — its exit is its
    owner's filing (steps 0 / 1b), decided nowhere else. ZERO free parameters,
    NO scalar field (rule 24): one published boolean per class × delivery
    year, read from the intaken table by
    :func:`market_sim.data.avoidable_cost_rate.no_default_cap_class`.

    Generic in form, PJM-scoped by data (rule 25 [R-ISO-SCOPE]): an ISO with no
    intaken default-ACR table has no "NA" cell and the predicate is False for
    every unit. ``iso=None`` or a config without the mapping is ``False`` so
    every pre-existing call path is byte-identical. Duck-typed via ``getattr``
    like its siblings.
    """
    if config is None or iso is None:
        return False
    by_iso = getattr(config, "capacity_no_default_cap_convention_by_iso", None)
    if not by_iso or not bool(by_iso.get(iso, False)):
        return False
    if not resolve_capacity_going_forward_bar_published(config, iso):
        if iso not in _NO_DEFAULT_CAP_REFUSED_LOGGED:
            _NO_DEFAULT_CAP_REFUSED_LOGGED.add(iso)
            logging.getLogger(__name__).warning(
                "capacity_no_default_cap_convention_by_iso[%s] is armed but the "
                "published going-forward-bar gate is off: the convention is a "
                "limb of the published default-ACR table and has no cell to read "
                "over the ATB proxy — it resolves OFF for this ISO "
                "(DESIGN-capx-d74 §3.3)",
                iso,
            )
        return False
    return True


@dataclass(frozen=True)
class ClearedCapacityPrice:
    """The PRE-PRICED capacity object a cleared market hands its price takers.

    capx D57 (DESIGN-capx-d54 §3.5 / §7.2): when
    :func:`resolve_capacity_market_supply_clearing` is on, the retirement
    screen clears the sell-offer stack once per screen year and the thermal
    new-entry and storage-entry screens read the resulting clearing price as
    price takers (design §4.4). It travels through the one ``reserve_position``
    slot every capacity-price consumer already threads verbatim, and
    :meth:`MarketDesign.capacity_price_per_firm_mw_yr` short-circuits on its
    ``price_per_firm_mw_yr`` — one seam, no second price path (rule 19).
    ``cleared_position`` and ``census_position`` are carried for ledgers and
    logs only; nothing re-evaluates the curve at either.
    """

    price_per_firm_mw_yr: float
    cleared_position: float
    census_position: float
    source: str = "supply_clearing"


# --- CR-1C curve eligibility (governance gate) ----------------------------
#
# Whether an ISO may price adequacy on its SLOPED demand curve when
# capacity_market_clearing is on. Eligibility is a GOVERNANCE gate layered on
# top of the clearing gate: an ISO is curve-eligible only once its
# accreditation-pairing basis (the flip-gate's item 1,
# docs/handoffs/forecast-retirement-calibration-plan-2026-07.md §2.1) is
# owner-signed. Every registry ISO is now eligible: PJM (R1-R4 landed), NEISO
# (R5b landed), MISO (EFORd pairing ~consistent, keep-and-verify), and NYISO —
# whose ICAP->UCAP translation-factor pairing (R5a) landed 2026-07-18 as the
# owner-selected Option B (NYCA-wide static proxy;
# docs/handoffs/nyiso-neiso-capacity-pairing-adjudication-2026-07-15.md §3,
# PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"]), so a curve-ON
# NYISO position is now measured on the correct basis. The global default
# clearing gate is off, so eligibility only bites under an explicit per-ISO
# curve-ON probe arm; it is NOT a default-behavior change (the production flip
# is FF-2C, owner-gated). An ISO absent here defaults ELIGIBLE (a new
# curve-carrying ISO is not silently blocked, and iso=None call sites stay
# byte-identical) — ineligibility is opt-in and cited.
CAPACITY_CURVE_ELIGIBLE_BY_ISO: dict[str, bool] = {
    "PJM": True,
    "NEISO": True,
    "MISO": True,
    # R5a pairing landed (FF-3D 2026-07-18): NYISO's ICAP-stated IRM is now
    # paired onto the model's UCAP supply basis via the NYCA translation factor
    # (PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"], Option B), so
    # a curve-ON position is measured on the correct basis. Eligibility only
    # ALLOWS the curve when capacity_market_clearing is explicitly enabled; the
    # production clearing default stays OFF (that flip is FF-2C, owner-gated).
    "NYISO": True,
    "CAISO": True,  # bilateral RA, no demand_curve — eligibility is moot
}


def resolve_capacity_curve_eligible(iso: "str | None") -> bool:
    """Return whether ``iso`` may price adequacy on its sloped curve (RC-1C).

    The governance gate the CR-1 curve branch of
    :meth:`MarketDesign.capacity_price_per_firm_mw_yr` consults *in addition to*
    the clearing gate. ``iso=None`` (pre-RC-1C call sites that pass no ISO) and
    any ISO absent from :data:`CAPACITY_CURVE_ELIGIBLE_BY_ISO` return ``True`` so
    the default path is byte-identical and a new curve ISO is not silently
    blocked. Every registry ISO is currently eligible (NYISO's ``False`` was
    lifted when its R5a pairing landed — FF-3D 2026-07-18); the registry stays
    so a future ISO can be gated ineligible by an explicit, cited ``False``.
    """
    if iso is None:
        return True
    return CAPACITY_CURVE_ELIGIBLE_BY_ISO.get(iso, True)


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
# ISO-NE FCA/MRI curve, modeled ANNUALLY. Re-derived 2026-08-31 (NEISO-RC-R
# R2 — the CR-3 refinement the previous comment promised; charter
# docs/handoffs/capx-director-prompt-pack-2026-08.md §NEISO-RC-R) from
# PUBLISHED auction evidence only:
#
#   * Cap = starting price / net-CONE = 14.525/9.078 = 1.600 (FCA 18,
#     $/kW-month, ratio basis-independent); cap-plateau end retained at FCA
#     11's published plateau end normalized by its Net ICR (33,457/34,075 —
#     the only FCA that ever published the cap x-position).
#   * Net-CONE at the requirement (1.0): the MRI demand-curve design's
#     calibration point (price = Net CONE at the Net ICR).
#   * The interior/tail is the MEASURED MRI-era curve: the FCA clears ON the
#     system-wide demand curve, so each auction's published (cleared MW,
#     clearing price), normalized by that FCA's own published Net ICR and
#     net-CONE, is a point on the published curve. Verified exactly on the
#     two FCAs whose curve segments are themselves published (FCA 11:
#     $5.297 @ 35,835 MW on the slide-14 table; FCA 13: $3.800 @ 34,839 MW
#     on the ICR-filing tail segment, = 3.802 computed). The five pure-MRI-era
#     clearing points (FCA 14–18, 2020–2024 auctions) are monotone in
#     normalized space — five years tracing one common tail.
#   * Zero-cross 35,713/33,750 = 1.0582: the only published zero-quantity of
#     the MRI era (FCA 13 ICR filing, testimony p.48 — the tail segment ends
#     at $0 @ 35,713 MW); its published slope (−18.0 in normalized units)
#     also matches the last measured segment's continuation.
#
# This REPLACES the first-order linear FCA-11-geometry reduction (zero-cross
# 1.083), which OVERPAID the measured curve everywhere in (1.0, 1.083):
# e.g. 0.457 vs measured 0.244 at x=1.0451. Every number traces to the P-0B
# datatype rows added by the R2 intake (data/raw/capacity-market/demand-curve/
# neiso/neiso.csv + README sha-256 identity table); no parameter comes from
# any model residual (rules 13/14/23 — the FINDING-capx-neiso-rc-phase0 §6 R2
# admissibility route). Net-CONE anchor 108.94 $/kW-yr (9.078 × 12).
_NEISO_MRI_CLEARING_POINTS: tuple[CapacityDemandCurvePoint, ...] = (
    # (cleared MW / Net ICR, clearing price / net-CONE), per-FCA published:
    CapacityDemandCurvePoint(31_556.0 / 30_550.0, 3.580 / 9.078),  # FCA 18
    CapacityDemandCurvePoint(31_370.0 / 30_305.0, 2.590 / 7.359),  # FCA 17
    CapacityDemandCurvePoint(32_810.0 / 31_645.0, 2.591 / 7.468),  # FCA 16
    CapacityDemandCurvePoint(34_621.0 / 33_270.0, 2.611 / 8.707),  # FCA 15
    CapacityDemandCurvePoint(33_956.0 / 32_490.0, 2.001 / 8.187),  # FCA 14
)
_NEISO_FCA_CURVE: tuple[CapacityDemandCurvePoint, ...] = (
    CapacityDemandCurvePoint(
        33_457.0 / 34_075.0, 14.525 / 9.078
    ),  # cap plateau end (FCA 11 published) at the FCA 18 starting price
    CapacityDemandCurvePoint(1.0, 1.0),  # Net CONE at requirement (MRI design)
    *_NEISO_MRI_CLEARING_POINTS,  # measured MRI-era curve points (FCA 14–18)
    CapacityDemandCurvePoint(
        35_713.0 / 33_750.0, 0.0
    ),  # zero-cross: FCA 13 published tail zero-quantity
)
# MISO PRA reliability-based demand curve (RBDC) — PUBLISHED SHAPE (capx D31,
# 2026-09-02; supersedes the P-0B first-order stand-in whose cap/zero reserve
# positions 0.97/1.05 were documented as representative, not published).
#
# WHAT THE PUBLISHED CURVE IS. MISO's RBDC (effective PY2025-26; FERC
# ER23-2977, accepted 187 FERC ¶ 61,202) is derived per season and subregion
# from the Marginal Reliability Impact curve of the LOLE model — MRI =
# avoided EUE per incremental UCAP MW — scaled so the four seasonal curves at
# the reliability requirement sum to the annual Net CONE (RBDC White Paper,
# RASC 2023-09-06, §3.1/§4.3: "the scaling factor is calculated to support
# annual revenue prices at annualized Net CONE when the system is at the
# reliability requirement in all four seasons"), capped at the seasonal CONE.
# The resulting final curves are LOLE-model outputs published ONLY as chart
# images in the PY2025-26 PRA Results Posting (pp.4/15-17, one chart per
# subregion x season) — no numeric table is reachable (demand-curve README).
#
# PROVENANCE OF THESE POINTS. The eight subregional charts were digitized at
# pixel resolution (scripts/data/digitize_miso_rbdc_charts.py; per-panel
# validation against the posting's own labeled clearing points, $0.2-$3.2 on
# seven panels) into data/raw/capacity-market/demand-curve/miso/miso.csv, and
# the four SYSTEM curves below are the PRMR-weighted horizontal aggregate of
# the two subregional curves (the market's total-demand construction absent a
# binding SRPBC), normalized by the System Initial PRMR (x) and the flat
# daily net-CONE (y) — scripts/data/derive_miso_rbdc_system_curves.py, whose
# output the reconciliation test asserts these constants EQUAL, so they can
# never drift from the committed data. Observed structure: the cap plateau
# (= seasonal CONE) runs to ~the Initial PRMR (summer N/C plateau ends at
# x=0.9994) and the curve decays near-exponentially (log-linear R^2
# 0.99-1.00) to a season-specific zero — summer x~1.080, spring x~1.046,
# fall/winter approaching zero asymptotically past the chart windows (their
# tails flat-clamp at the last observed point, <=$7/MW-day). Validation at
# the market's own cleared positions: +0.1% (summer $667.13 vs $666.50),
# -3.5% (fall — the SRPBC bound that season and split subregional prices
# $91.60/$74.09, which a single system curve cannot express), -1.1%
# (winter), -1.0% (spring); seasonal revenue sum at the cleared positions
# $78,743 vs the actual $79,070.6/MW-yr (-0.4%). The pre-repair first-order
# shape paid $52.1/kW-yr at the measured PY2025-26 position (D28 §4.iii).
# Net-CONE anchor 79.8 $/kW-yr (North/Central annual Net CONE, miso.csv).
_MISO_RBDC_SUMMER_POINTS: tuple[CapacityDemandCurvePoint, ...] = (
    CapacityDemandCurvePoint(0.9967, 6.1924),
    CapacityDemandCurvePoint(0.9977, 5.8805),
    CapacityDemandCurvePoint(1.0027, 5.78),
    CapacityDemandCurvePoint(1.0082, 4.1665),
    CapacityDemandCurvePoint(1.0166, 3.1086),
    CapacityDemandCurvePoint(1.0348, 1.6719),
    CapacityDemandCurvePoint(1.0567, 0.5647),
    CapacityDemandCurvePoint(1.0587, 0.5006),
    CapacityDemandCurvePoint(1.0673, 0.2266),
    CapacityDemandCurvePoint(1.0738, 0.0792),
    CapacityDemandCurvePoint(1.0743, 0.0581),
    CapacityDemandCurvePoint(1.0751, 0.0552),
    CapacityDemandCurvePoint(1.0754, 0.0371),
    CapacityDemandCurvePoint(1.0785, 0.0139),
    CapacityDemandCurvePoint(1.0804, 0.0),
)
_MISO_RBDC_FALL_POINTS: tuple[CapacityDemandCurvePoint, ...] = (
    CapacityDemandCurvePoint(0.9707, 6.2604),
    CapacityDemandCurvePoint(0.9746, 5.0028),
    CapacityDemandCurvePoint(0.9802, 3.7312),
    CapacityDemandCurvePoint(0.9841, 3.0335),
    CapacityDemandCurvePoint(0.989, 2.3419),
    CapacityDemandCurvePoint(0.9932, 1.8715),
    CapacityDemandCurvePoint(0.9978, 1.4699),
    CapacityDemandCurvePoint(1.0024, 1.1545),
    CapacityDemandCurvePoint(1.0068, 0.9226),
    CapacityDemandCurvePoint(1.0117, 0.7247),
    CapacityDemandCurvePoint(1.0189, 0.4958),
    CapacityDemandCurvePoint(1.0249, 0.3511),
    CapacityDemandCurvePoint(1.0326, 0.2403),
    CapacityDemandCurvePoint(1.0461, 0.1247),
    CapacityDemandCurvePoint(1.0514, 0.0354),
    CapacityDemandCurvePoint(1.0624, 0.0011),
)
_MISO_RBDC_WINTER_POINTS: tuple[CapacityDemandCurvePoint, ...] = (
    CapacityDemandCurvePoint(0.9693, 6.33),
    CapacityDemandCurvePoint(0.9756, 4.6644),
    CapacityDemandCurvePoint(0.983, 3.3337),
    CapacityDemandCurvePoint(0.99, 2.4193),
    CapacityDemandCurvePoint(0.9962, 1.8379),
    CapacityDemandCurvePoint(1.0045, 1.2548),
    CapacityDemandCurvePoint(1.009, 1.0289),
    CapacityDemandCurvePoint(1.0122, 0.8832),
    CapacityDemandCurvePoint(1.0193, 0.641),
    CapacityDemandCurvePoint(1.0254, 0.4944),
    CapacityDemandCurvePoint(1.0355, 0.3128),
    CapacityDemandCurvePoint(1.042, 0.227),
    CapacityDemandCurvePoint(1.0507, 0.1526),
    CapacityDemandCurvePoint(1.0682, 0.0679),
    CapacityDemandCurvePoint(1.085, 0.0303),
    CapacityDemandCurvePoint(1.0915, 0.0031),
)
_MISO_RBDC_SPRING_POINTS: tuple[CapacityDemandCurvePoint, ...] = (
    CapacityDemandCurvePoint(0.9511, 6.1924),
    CapacityDemandCurvePoint(0.9519, 5.8805),
    CapacityDemandCurvePoint(0.9564, 4.7005),
    CapacityDemandCurvePoint(0.9638, 3.2735),
    CapacityDemandCurvePoint(0.9687, 2.572),
    CapacityDemandCurvePoint(0.9746, 1.919),
    CapacityDemandCurvePoint(0.981, 1.4073),
    CapacityDemandCurvePoint(0.9869, 1.05),
    CapacityDemandCurvePoint(0.9932, 0.77),
    CapacityDemandCurvePoint(0.999, 0.5745),
    CapacityDemandCurvePoint(1.0026, 0.5006),
    CapacityDemandCurvePoint(1.0115, 0.3198),
    CapacityDemandCurvePoint(1.0225, 0.1691),
    CapacityDemandCurvePoint(1.0304, 0.0879),
    CapacityDemandCurvePoint(1.0377, 0.0371),
    CapacityDemandCurvePoint(1.0463, 0.0),
)

# Season day weights: each season's published "CONE (Seasonal)" $/MW-day x
# days = the full annual gross CONE (Summer 92, Fall 91, Winter 90, Spring 92;
# Σ=365) — PY2025-26 PRA Results Posting p.26, North/Central column.
_MISO_SEASON_DAYS: tuple[tuple[str, int], ...] = (
    ("summer", 92),
    ("fall", 91),
    ("winter", 90),
    ("spring", 92),
)
_MISO_SEASON_POINTS: dict[str, tuple[CapacityDemandCurvePoint, ...]] = {
    "summer": _MISO_RBDC_SUMMER_POINTS,
    "fall": _MISO_RBDC_FALL_POINTS,
    "winter": _MISO_RBDC_WINTER_POINTS,
    "spring": _MISO_RBDC_SPRING_POINTS,
}


def _miso_annual_reduction() -> tuple[CapacityDemandCurvePoint, ...]:
    """Annual (single-curve) reduction of the four seasonal RBDCs.

    The days-weighted mean of the seasonal curves on the union of their
    x-breakpoints — ``frac_annual(x) = Σ_s frac_s(x) × days_s / 365`` — so the
    registry ``demand_curve`` (consumed only when ``seasonal_rbdc`` is absent,
    which never happens for the PY2025-26 vintage; retained as the annual
    reconciliation object) is derived from the same published points and can
    never disagree with the seasonal grain it reduces.
    """
    xs = sorted({p.reserve_ratio for pts in _MISO_SEASON_POINTS.values() for p in pts})
    out = []
    for x in xs:
        frac = (
            sum(
                evaluate_demand_curve(_MISO_SEASON_POINTS[s], x) * days
                for s, days in _MISO_SEASON_DAYS
            )
            / 365.0
        )
        out.append(CapacityDemandCurvePoint(x, frac))
    return tuple(out)


_MISO_RBDC_CURVE: tuple[CapacityDemandCurvePoint, ...] = _miso_annual_reduction()

# --- MISO seasonal RBDC (RC-1C, prereq 4a) --------------------------------
#
# MISO is the ONLY capacity-market ISO whose PRA clears SEASONALLY (four seasons,
# $/MW-day, under the Reliability-Based Demand Curve from PY2025-26). The market's
# own settlement construction is a seasonal SUM: a resource earns
# Σ_season (ACP_season [$/MW-day] × days_in_season) over the planning year. The
# model reproduces THAT construction — :meth:`MarketDesign.
# capacity_price_per_firm_mw_yr` evaluates a per-season RBDC at the system's
# accredited reserve position and sums × days_in_season — replacing the annual
# approximation above (which mis-annualized a summer $/MW-day print as if it ran
# all 365 days).
#
# The four seasons and their day counts fall straight out of the data: each
# season's published gross "CONE (Seasonal)" $/MW-day × days = the FULL annual
# gross CONE (North/Central summer 1384.36 × 92 = 127,361 $/MW-yr = annual gross
# CONE), so days = annual_gross_cone / seasonal_gross_cone_daily — Summer 92
# (Jun-Aug), Fall 91 (Sep-Nov), Winter 90 (Dec-Feb, non-leap), Spring 92
# (Mar-May); Σ = 365. Source: MISO PY2025-26 PRA Results Posting p.26 "CONE
# (Seasonal)" table, North/Central column (miso.csv seasonal gross-CONE rows).
#
# ONE-POSITION LIMIT (documented, not a bug — do not "fix" by inventing seasonal
# accreditation): the model holds ONE annual accredited reserve position and
# evaluates all four seasonal curves at it. It has no seasonal accreditation
# basis (seasonal firm MW), so it CANNOT reproduce the observed seasonal price
# CONCENTRATION (PY2025-26 cleared summer $666.50 vs $33-92 the other seasons),
# which comes from seasonal SUPPLY differences. Concretely: at a SHORT annual
# position it prices ALL four seasons near their gross-CONE caps (OVER-stating —
# reality had only the binding season short), and at a LONG annual position it
# prices all four near zero (UNDER-stating — missing the binding season's real
# contribution). Reality's "≈net-CONE, concentrated in summer" needs the four
# seasonal positions to differ, which only a seasonal accreditation basis
# supplies (a future item; the fleet-independent seasonal Pass 1 in
# scripts/validate_capacity_prices.py DOES reproduce the concentration because it
# uses each season's own published position). What the seasonal grain DOES add
# over the annual approximation: (a) the annualization is the market's seasonal
# SUM, so summer's high $/MW-day is weighted by its 92 days, not 365 (fixing the
# old ~3x over-statement — Σ ACP×days ≈ annual net-CONE); (b) each season's price
# ceiling is its OWN gross-CONE cap (summer's is ~6.3x the flat daily net-CONE,
# because summer packs the full annual gross CONE into 92 days), so a SHORT
# position can recover up to gross CONE from the binding season alone — the
# RBDC's real scarcity behaviour.
#
# The y-NORMALIZATION anchor is the published ANNUAL North/Central net-CONE
# spread FLAT across 365 days (218.63 $/MW-day) — MISO publishes the seasonal
# CONE caps and the ANNUAL net-CONE, not a separate seasonal net-CONE — so a
# season's frac is its $/MW-day price ÷ the flat daily net-CONE (each cap
# frac ≈ 6.2-6.3 because a seasonal CONE packs the full annual gross CONE
# into one season's days). Unlike the superseded first-order construction,
# the published curves do NOT pass through (1.0, flat-net-CONE) per season:
# each sits near its CAP at the requirement (summer N/C reads ~$1,300/MW-day
# at the Initial PRMR on the chart) and decays only past it, so the sum at
# x=1.0 is ~$209.5k/MW-yr, ~2.6x annual net-CONE. The net-CONE calibration
# the design targets (White Paper §4.3's scaling + long-run Monte Carlo) is
# instead realized where the market actually CLEARS: the seasonal revenue
# sum at PY2025-26's four cleared positions is $79,070.6/MW-yr ≈ the
# $79,800 net-CONE anchor, and these digitized curves reproduce that sum at
# those positions to -0.4% (the reconciliation test asserts it). The curve
# SHAPE itself — cap span, decay, zero — is now the published one:
# see the provenance block above _MISO_RBDC_SUMMER_POINTS (capx D31).
_MISO_NC_NET_CONE_PER_MW_YR: float = 79_800.0  # N/C net-CONE, PY2025-26 (miso.csv)
_MISO_DAILY_NET_CONE_PER_MW_DAY: float = _MISO_NC_NET_CONE_PER_MW_YR / 365.0  # 218.63


@dataclass(frozen=True)
class MISOSeasonRBDC:
    """One MISO PRA season: its normalized RBDC + its day weight (RC-1C)."""

    name: str
    days: int
    demand_curve: tuple[CapacityDemandCurvePoint, ...]


@dataclass(frozen=True)
class SeasonalRBDC:
    """MISO's four-season RBDC, evaluated at ONE annual reserve position (RC-1C).

    :func:`seasonal_rbdc_price_per_firm_mw_yr` sums, over the four seasons,
    ``evaluate_demand_curve(season.demand_curve, position) ×
    daily_net_cone_per_mw_day × season.days`` — the market's own seasonal
    settlement (Σ ACP_season[$/MW-day] × days_in_season). At the requirement
    (position 1.0) every season pays the flat daily net-CONE, so the sum is
    exactly the annual net-CONE; a SHORT position lifts each season toward its
    own gross-CONE cap. See the module comment above for the one-position limit.
    """

    seasons: tuple[MISOSeasonRBDC, ...]
    daily_net_cone_per_mw_day: float


def seasonal_rbdc_price_per_firm_mw_yr(
    seasonal: "SeasonalRBDC", reserve_position: float
) -> float:
    """MISO annual capacity price ($/firm-MW-yr) — the seasonal RBDC sum (RC-1C).

    ``Σ_season evaluate_demand_curve(season.demand_curve, reserve_position) ×
    daily_net_cone_per_mw_day × season.days``. The ONE ``reserve_position`` feeds
    all four seasons (the annual-position limit documented above).
    """
    x = float(reserve_position)
    total = 0.0
    for s in seasonal.seasons:
        frac = evaluate_demand_curve(s.demand_curve, x)
        total += frac * seasonal.daily_net_cone_per_mw_day * float(s.days)
    return total


# The four seasonal SYSTEM curves are the published-shape point tuples above
# (digitized subregional charts, PRMR-weighted system aggregate — provenance
# block at _MISO_RBDC_SUMMER_POINTS). Each season's cap frac IS its published
# seasonal CONE ÷ flat daily net-CONE (summer 1384.36/218.63... aggregated
# with South's 1282.61 to the System cap fractions the tuples carry).
MISO_SEASONAL_RBDC: SeasonalRBDC = SeasonalRBDC(
    seasons=tuple(
        MISOSeasonRBDC(name, days, _MISO_SEASON_POINTS[name])
        for name, days in _MISO_SEASON_DAYS
    ),
    daily_net_cone_per_mw_day=_MISO_DAILY_NET_CONE_PER_MW_DAY,
)

# Pre-RBDC MISO PRA (PY2009-10 .. PY2024-25) used a VERTICAL demand curve capped
# at CONE (FERC ER23-2977; data/raw/.../demand-curve/miso/README.md): price = CONE
# when the zone is short, ≈0 when long, NO sloped interior. Represented as a
# near-vertical step anchored on gross CONE (the ceiling): frac 1.0 (= the
# gross-CONE anchor) at/below the requirement, dropping to 0 just above it. No
# invented slope (rule 13). These vintages carry ``seasonal_rbdc=None`` so the
# seam prices this step, not the seasonal RBDC.
_MISO_VERTICAL_STEP: float = 1e-6
_MISO_VERTICAL_CURVE: tuple[CapacityDemandCurvePoint, ...] = (
    CapacityDemandCurvePoint(1.0, 1.0),  # at/short of requirement: CONE ceiling
    CapacityDemandCurvePoint(1.0 + _MISO_VERTICAL_STEP, 0.0),  # just long: zero
)

# FFR-4F (2026-08-09) — CAISO's RA capacity-price anchor, on its own rule 14
# [R-ACCURATE] merits. GATED default-OFF behind
# ``ScenarioConfig.caiso_ra_mpb_capacity_anchor``; see
# docs/handoffs/ffr-4f-caiso-anchor-merits-2026-08-09.md.
#
# THIS IS NOT A ROW-4 FIX. FC-2 row 4's movement is a reported side effect of
# this correction, never its objective and never its success metric. The owner
# DECLINED the anchor as a ROUTE to row 4 (D-15's charter), and FFR-3W §5.3
# stated the trap before anyone measured it: closing row 4 through the entry
# screen still builds the CTs California does not need, just through the
# economic channel instead of the administrative one. This mechanism exists
# because the shipped anchor is mis-specified ON ITS OWN TERMS, which is a
# rule 14 defect whatever it does to any gate.
#
# WHAT THE SHIPPED ANCHOR IS. ``net_cone_per_kw_yr=88.08`` for CAISO is the CPM
# SOFT-OFFER CAP: FERC ER24-1225 (187 FERC P 61,032, eff. 2024-06-01) derives it
# as "$73.41/kW-yr GOING-FORWARD FIXED COST of a 550 MW CC reference unit x
# 1.20". Three independent category errors, each established from the source
# document's own words and none of them a residual argument (FFR-3W §2.3):
#   (a) a GOING-FORWARD cost (FOM + sustaining capital for an EXISTING unit,
#       containing no capex annuity by construction) used against a NEW-ENTRY
#       gross fixed cost that is 78.2 % capex annuity;
#   (b) a 550 MW COMBINED-CYCLE reference unit used to price a frame
#       COMBUSTION TURBINE — different capex/kW, FOM/kW and duty cycle;
#   (c) an administrative CEILING on backstop OFFERS, not a price any resource
#       is paid. All five 2023 CPM designations cleared exactly AT the cap
#       (data/raw/capacity-market/auction-price/caiso/), i.e. it binds as a
#       regulatory ceiling on ~256 MW of last-resort procurement.
# The above-cap path confirms (a) at the DESIGN level rather than merely in this
# vintage's arithmetic: a resource may offer above the cap only by cost-
# justifying to FERC on ITS OWN going-forward fixed costs, "using the same cost
# categories used to establish the CPM soft offer cap". CPM compensation is a
# RETENTION price structure end to end.
#
# WHAT REPLACES IT, AND THE RULE 14 MISALIGNMENT RECONCILIATION. CAISO publishes
# NO net-CONE and no new-entry capacity price -- it runs no centralized capacity
# auction and no demand curve, so the object our registry slot is named after
# does not exist for this ISO (structurally absent, not un-fetched). The slot is
# not really "net-CONE" for CAISO; it is "the price a firm MW of CAISO RA is
# paid", which is what all three screens multiply by their accreditation. The
# published object that IS that quantity is the CPUC PCIA **Resource Adequacy
# Market Price Benchmark**: the volume-weighted average of ALL IOU/CCA/ESP RA
# transactions for a stated DELIVERY year, unified to a single RA value by
# D.25-06-049 OP 1 and issued every October under D.22-01-023.
#
#   2026 Forecast (delivery 2026) 11.53 $/kW-mo x 12 = 138.36 $/kW-yr  <- adopted
#   2025 Final    (delivery 2025) 11.21 $/kW-mo x 12 = 134.52 $/kW-yr
#
# The 2026 Forecast vintage is adopted because the model's forecast base year is
# 2026 and that row is the published FORWARD-delivery price. It is corroborated
# by three independent CPUC values already committed for this ISO: the RA Report
# transacted series 11.10 (2023), 11.87 (2025) and the 11.21 Final above -- four
# published numbers inside 11.10-11.87 $/kW-mo, against the 7.34 the cap sets.
#
# The two misalignments FFR-3W §4 filed against this replacement, RECONCILED
# rather than guessed (rule 14's own misalignment clause):
#   1. "A whole-market average dominated by EXISTING resources is not a
#      new-entrant price." Real property, but not a defect for THIS slot. CAISO
#      RA is a fungible bilateral product: a System RA MW from a new CT and one
#      from an existing CC are the same product at the same price, and CAISO has
#      no vintage-differentiated RA price because it has no auction in which new
#      entry sets a clearing price. So the transacted average IS what a new
#      entrant is paid. That this price may be too low to call forth merchant
#      entry is a MARKET OUTCOME the screen must be free to report -- grossing
#      it up so entry turns profitable would be tuning an input to a desired
#      output (rules 1/13). It is deliberately not done, and the screen may well
#      still return `unprofitable` at this anchor (FFR-3W §2.1 puts the CT
#      break-even at 10.88-11.36 $/kW-mo, i.e. astride this value).
#   2. "The price is per NQC kW; the screens apply a UCAP accreditation." The
#      residual is small and measurable rather than assumed: CAISO's own
#      published gas-class ratio is NQC/NDC = 25,866/26,958 = 0.9595 (2026 SLRA
#      Table 1.1, data/raw/capacity-market/loads-resources/caiso/), against the
#      model's 1 - EFORd of 0.9400 for gas_ct and 0.9500 for gas_cc. Pairing an
#      NQC-basis price with the model's UCAP fraction therefore UNDER-credits
#      thermal capacity revenue by ~2.0 % (CT) / ~1.0 % (CC) -- conservative,
#      two orders below the 57 % price error being corrected, and left
#      UNCORRECTED here on purpose: inventing a gross-up would be a second,
#      unmeasured mechanism (rule 19) fitted to nothing.
#
# Rule 13 [R-MEASURED] admissibility: the MPB is a measured market input, not a
# measured OUTCOME. CPUC Energy Division publishes it every October for the next
# delivery year under a standing decision, so the same quantity regenerates for
# a forward year and responds to changed market conditions -- the test rule 13
# sets. Nothing here is pinned to a model residual.
#
# Rule 25 [R-ISO-SCOPE]: CAISO only, by construction -- the resolver returns
# ``None`` for every other ISO, so no other market's anchor can move.
CAISO_RA_MPB_ANCHOR_PER_KW_YR: float = 138.36  # 11.53 $/kW-mo x 12


def resolve_caiso_ra_mpb_anchor(
    config: "object | None", iso: "str | None" = None
) -> float | None:
    """Return CAISO's RA-MPB capacity anchor in $/kW-yr, or ``None`` if unarmed.

    The one seam the FFR-4F anchor correction resolves through, so all five
    capacity-price consumers (retirement screen, thermal entry, VRE entry,
    storage entry, plant-financials reporting) move together or not at all
    (rule 19 ``[R-ONE-MECH]``) -- every one of them threads ``iso`` into
    :meth:`MarketDesign.capacity_price_per_firm_mw_yr`, so the gate cannot fire
    for some screens and not others.

    Returns ``None`` -- meaning "registry anchor governs, byte-identically" --
    unless ``iso`` is CAISO **and** ``config.caiso_ra_mpb_capacity_anchor`` is
    armed. ``config`` is duck-typed via ``getattr`` so the config layer needs no
    import of :class:`ScenarioConfig`, and a ``None`` config or a config
    predating the field resolves unarmed.
    """
    if iso != "CAISO" or config is None:
        return None
    if not getattr(config, "caiso_ra_mpb_capacity_anchor", False):
        return None
    return CAISO_RA_MPB_ANCHOR_PER_KW_YR


# Per-ISO market design. ISOs absent here fall back to ``DEFAULT_MARKET_DESIGN``
# (energy-only) so a new ISO is conservative until its capacity rules are added.
MARKET_DESIGN: dict[str, MarketDesign] = {
    # Energy-only: scarcity is monetized through the energy price, not a
    # separate capacity payment. Source: ERCOT market design (ORDC).
    "ERCOT": MarketDesign(capacity_market=False),
    # RA program with a soft capacity price — no centralized auction/demand
    # curve, so CAISO keeps the FIXED proxy in BOTH modes (documented
    # low-fidelity member of the registry, CR-1 §3.2; RA-not-auction, so the
    # FF-2C gate flip is a pricing no-op — flip memo §1.5). FF-2C R4 (owner
    # sign-off 2026-07-19): the fixed anchor is re-derived from the 90 rounding
    # to the EXACT published CPM soft-offer cap — $7.34/kW-month × 12 = $88.08/
    # kW-yr (FERC ER24-1225 effective 2024-06-01), between it and the CPUC 2023
    # RA report system price ($14.51/kW-month = $174/kW-yr for 2024). No
    # demand_curve ⇒ capacity_price_per_firm_mw_yr returns the fixed anchor even
    # when capacity_market_clearing is on. Source: CPUC 2023 Resource Adequacy
    # Report; CAISO CPM soft-offer-cap tariff (P-0B caiso.csv).
    #
    # FFR-4F 2026-08-09: this 88.08 anchor is MIS-SPECIFIED ON ITS OWN TERMS —
    # it is the CPM soft-offer cap, i.e. an administrative ceiling on backstop
    # offers built from an EXISTING 550 MW COMBINED-CYCLE's going-forward fixed
    # cost, used as the entry price for a new COMBUSTION TURBINE. The corrected
    # anchor (CPUC unified RA Market Price Benchmark, 138.36 $/kW-yr) is built
    # and GATED default-OFF behind ``caiso_ra_mpb_capacity_anchor``; see
    # CAISO_RA_MPB_ANCHOR_PER_KW_YR above for the full derivation and the rule
    # 14 misalignment reconciliation. The shipped value stays here as the
    # default until the arming posture is an owner decision (rules 5/24/28).
    "CAISO": MarketDesign(capacity_market=True, net_cone_per_kw_yr=88.08),
    # Capacity markets. FF-2C R4 (owner sign-off 2026-07-19, accreditation-basis
    # memo §4.3-R4): the legacy fixed-mode net_cone_per_kw_yr anchor is
    # re-derived to the SAME published UCAP net-CONE basis as the CR-1 curve
    # anchor now that the default flip has landed — the ~$100/kW-yr placeholder
    # (neither the ICAP 60.4 nor UCAP 77.4 published figure, kept only for
    # pre-flip default byte-identity) is retired. Both anchors are now on PJM's
    # own published UCAP basis.
    # Source: PJM 2026/2027 BRA planning parameters — 212.14 $/MW-day UCAP
    # net-CONE × 365 / 1000 = 77.431 $/kW-yr (fixed anchor = curve anchor).
    "PJM": MarketDesign(
        capacity_market=True,
        net_cone_per_kw_yr=77.431,
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
    # Source: ISO-NE FCM net-CONE. FF-2C R4 (owner sign-off 2026-07-19): the
    # fixed anchor is re-derived from the ~$95/kW-yr placeholder to the SAME
    # published FCA 18 (2027/2028) net-CONE the CR-1 curve scales — 9.078
    # $/kW-month × 12 = 108.936 $/kW-yr (fixed anchor = curve anchor 108.94).
    "NEISO": MarketDesign(
        capacity_market=True,
        net_cone_per_kw_yr=108.94,
        demand_curve=_NEISO_FCA_CURVE,
        net_cone_curve_per_kw_yr=108.94,
        demand_curve_delivery_year="2027-2028",
        demand_curve_source=(
            "ISO-NE FCA 18 (2027/2028) Net CONE + starting price; MRI-era "
            "geometry from published FCA 14-18 clearing outcomes on their own "
            "Net ICRs + the FCA 13 ICR filing's published tail zero-quantity "
            "(NEISO-RC-R R2, 2026-08-31)"
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
    # FF-2C R4 (owner sign-off 2026-07-19): the fixed anchor is re-derived from
    # the 80.0 rounding to the SAME published North/Central Net CONE (79.8
    # $/kW-yr) the CR-1 curve scales, now that the default flip has landed (the
    # rounding was kept only for pre-flip default byte-identity).
    "MISO": MarketDesign(
        capacity_market=True,
        net_cone_per_kw_yr=79.8,
        demand_curve=_MISO_RBDC_CURVE,
        net_cone_curve_per_kw_yr=79.8,
        demand_curve_delivery_year="2025-2026",
        demand_curve_source=(
            "MISO PY2025-26 PRA Results Posting (North/Central Net CONE + LRZ "
            "gross CONE for the cap); RBDC shape reserve positions first-order. "
            "Seasonal grain: RC-1C (MISO_SEASONAL_RBDC)"
        ),
        # RC-1C: MISO clears SEASONALLY — the seam sums the four seasonal RBDCs
        # (× days) instead of the single annual demand_curve when the gate is on.
        seasonal_rbdc=MISO_SEASONAL_RBDC,
    ),
    # SPP is DELIBERATELY ABSENT (registered 2026-09-06, lane SPP-20; plan
    # docs/multi-iso/spp-addition-plan-2026-09.md §2.3). SPP has no
    # centralized capacity market: resource adequacy is a bilateral
    # load-responsible-entity OBLIGATION to hold Accredited Capacity against
    # the Planning Criteria Base PRM (v5.0A §4, PLANNING_RESERVE_MARGIN_BY_ISO
    # ["SPP"]), with deficiency payments rather than an auction clearing
    # price. The energy-only fallback (DEFAULT_MARKET_DESIGN, capacity_market=
    # False) is therefore SPP's actual market reality, not a placeholder:
    # storage / VRE entry earn no capacity payment there exactly as in ERCOT.
    # Every capacity-market-only registry in this module (demand curves,
    # vintages, ICAP/UCAP translations, locality areas) is likewise absent for
    # SPP by the same reasoning; the exclusion list is FINDING-spp-20 §4.
    #
    # NWPP is DELIBERATELY ABSENT too (registered 2026-09-14, lane NWPP-20;
    # owner ruling N7): no centralized capacity market exists anywhere in the
    # seventeen-BA footprint — resource adequacy is each vertically-integrated
    # participant's own IRP obligation, and the one pool-wide construct, the
    # Western Resource Adequacy Program (WRAP), is a forward-showing program
    # whose first BINDING season is Winter 2027-28 (WPP BPM 109 printed
    # p. 4), i.e. FORECAST-SIDE ONLY and out of every scored year. NWPP takes
    # DEFAULT_MARKET_DESIGN (capacity_market=False, the ERCOT/SPP branch); no
    # entry in _CURVE_ISOS / _CAPACITY_ISOS follows; every capacity-market-
    # only registry in this module is likewise absent for NWPP by the same
    # reasoning (FINDING-nwpp-20 §4 carries the exclusion list).
    # SOCO is DELIBERATELY ABSENT too (registered 2026-09-14, lane SOCO-20;
    # owner card S6, ruled 2026-09-13: "absent from MARKET_DESIGN, _CURVE_ISOS,
    # _CAPACITY_ISOS"). The Southern Company balancing authority is
    # VERTICALLY INTEGRATED: no capacity auction of any kind exists, and
    # resource adequacy is each operating company's IRP obligation against
    # the Southern Company System Target Reserve Margin (26 % winter / 20 %
    # summer, 2024 Reserve Margin Study — PLANNING_RESERVE_MARGIN_BY_ISO
    # ["SOCO"]), enforced by state commissions (Georgia PSC certification /
    # decertification under the IRP Act; Alabama has no IRP statute), never
    # by a clearing price. DEFAULT_MARKET_DESIGN (capacity_market=False) is
    # therefore SOCO's actual reality, not a placeholder: no storage / VRE
    # entry earns a capacity payment, exactly as in ERCOT and SPP. Every
    # capacity-market-only registry in this module is likewise absent for
    # SOCO; the exclusion list is FINDING-soco-20 §4.
}

DEFAULT_MARKET_DESIGN: MarketDesign = MarketDesign(capacity_market=False)


@dataclass(frozen=True)
class MarketDesignVintage:
    """One delivery-year vintage of an ISO's capacity demand curve (RC-1B item 2).

    The per-delivery-year override :func:`resolve_demand_curve_vintage` returns,
    consulted by :meth:`MarketDesign.capacity_price_per_firm_mw_yr` only when a
    solve prices a specific ``year`` under the CR-1 clearing gate. Each field
    overrides the same-named :class:`MarketDesign` field for that delivery year:

    * ``net_cone_curve_per_kw_yr`` — the PUBLISHED net-CONE anchor (in $/kW-yr)
      the curve scales, for THIS delivery year.
    * ``demand_curve`` — the normalized (reserve_ratio, price/net-CONE) shape, or
      ``()`` when the delivery year publishes a net-CONE anchor but not a
      normalizable curve shape (rule 13: never fabricate an unpublished point) —
      the price then falls back to the flat vintage anchor.

    ``delivery_year`` is the ISO's own label ("2026/2027", "2025-2026"); its
    leading four digits are the delivery period's start calendar year — the key
    :func:`resolve_demand_curve_vintage` maps a model year onto. Every number
    traces to the P-0B ``capacity-market-demand-curve`` datatype
    (``data/raw/capacity-market/demand-curve/<iso>/<iso>.csv``); the
    reconciliation is asserted in ``tests/test_capacity_demand_curve.py``.
    """

    delivery_year: str
    net_cone_curve_per_kw_yr: float
    demand_curve: tuple[CapacityDemandCurvePoint, ...] = ()
    # RC-1C: MISO PY2025-26 carries the seasonal RBDC here so a per-delivery-year
    # solve prices the seasonal grain; pre-RBDC MISO vintages leave this None and
    # carry a vertical ``demand_curve`` instead. Every other ISO leaves it None.
    seasonal_rbdc: "SeasonalRBDC | None" = None


# --- Per-delivery-year vintage curves & anchors (RC-1B item 2) -------------
#
# MARKET_DESIGN_VINTAGES below carries each capacity-market ISO's demand curve
# for every published delivery year (not just the single MARKET_DESIGN
# reference), so a forecast solve prices adequacy on the delivery year it is
# actually simulating. Anchors and cap fractions are read off the SAME raw
# datatype the registry reference is (data/raw/capacity-market/demand-curve),
# on the SAME per-ISO conventions:
#   PJM   anchor = published UCAP net-CONE ($/MW-day) × 365 / 1000;
#         cap    = price_cap / net-CONE (both $/MW-day UCAP).
#   NYISO anchor = NYCA Annual Reference Value ($/kW-yr); first-order straight
#         line, net-CONE at the requirement, zero at 1 + 12% curve length,
#         cap = max clearing / reference-point price (both $/kW-month).
#   NEISO anchor = net-CONE ($/kW-month) × 12; per-design-family published
#         shapes (FCA 11 exact table / FCA 13 transition construction /
#         measured MRI-era clearing points — NEISO-RC-R R2, 2026-08-31),
#         cap = starting price / net-CONE (both $/kW-month).
#   MISO  anchor = North/Central Net CONE ($/MW-yr) / 1000; first-order RBDC.
# A delivery year that publishes a net-CONE anchor but no normalizable shape
# carries demand_curve=() and prices on the flat anchor (rule 13). The vintage
# that equals the MARKET_DESIGN reference REUSES its exact curve/anchor object,
# so pricing that delivery year is byte-identical to the registry default.

# PJM 2027/2028 BRA — the same Manual 18 §3.4 post-CIFP VRR points as 2026/2027
# (0.99, 1.015, 1.045); cap = price cap / net-CONE = 333.44 / 242.52 (both
# $/MW-day UCAP). Source: 2027/2028 RPM BRA Planning Period Parameters
# (posted 2025-08-26), Table 3 + VRR/Summary sections.
_PJM_VRR_CURVE_2027_2028: tuple[CapacityDemandCurvePoint, ...] = (
    CapacityDemandCurvePoint(0.99, 333.44 / 242.52),  # price cap
    CapacityDemandCurvePoint(1.015, 1.0),  # Net CONE reference point
    CapacityDemandCurvePoint(1.045, 0.0),  # zero-cross (published y=0)
)

# PJM 2028/2029 BRA (FFR-2C re-anchor 2026-08-02; rule 23 — the DATA changed,
# not a residual: PJM published a new delivery-year parameter set on 2026-03-20,
# added the VRR curve 2026-04-29, and the BRA itself cleared in July 2026).
# Source: the machine-readable 2028/2029 RPM BRA Planning Period Parameters
# workbook (sha256 b1863615b0e366ab605aa26f3e9b84af4380ce924ec42c0c0b31a7a75557ca09
# committed at data/raw/capacity-market/demand-curve/pjm/, rows in pjm.csv) —
# the narrative report's Table 3 is an IMAGE, which is what blocked FF-G3 from
# encoding this vintage at design time.
#
# THREE ways this vintage differs from every earlier PJM vintage; each is
# published, none is a modelling choice:
#  1. **Level.** Net CONE UCAP = 325.69 $/MW-day (workbook 'Net CONE' sheet RTO
#     row: Gross CONE UCAP 776.14 − Forward Net E&AS Revenue Offset UCAP
#     450.448). That is +34.3 % over the 2027/2028 anchor (242.52) — the first
#     delivery year on the Quad/Periodic Review gross-CONE values (FERC Docket
#     ER26-455, approved 2026-01-21), not an escalation of the old basis.
#  2. **Shape.** FOUR published (level, price) points, not the Manual-18
#     0.99/1.015/1.045 three-point construction: the report's own Summary says
#     "The VRR Curve equation has changed, impacting the prices used and point c
#     of the VRR Curve". x = published UCAP Level MW ÷ the published Reliability
#     Requirement adjusted for FRR (145,149.08535) — NO EE Addback term, because
#     post-CIFP energy efficiency is netted inside the load forecast and the
#     2028/29 workbook publishes no such row (the 2021/22-2025/26 vintages add
#     one). The denominator is confirmed by PJM's own numbers: point (b) lands
#     on 1.015000 and point (d) on 1.060000 exactly.
#  3. **A price FLOOR that binds.** FERC Docket ER26-1556 collars the curve at
#     325.00 / 175.00 $/MW-day UCAP (= the workbook's ICAP cap/floor 256.75 /
#     138.25 ÷ the 0.79 Reference Resource Accredited UCAP Factor). So points
#     (c) and (d) sit AT the floor and the curve never reaches zero:
#     evaluate_demand_curve flat-extrapolates past the last point, so a long
#     PJM position in 2028+ earns 175/325.69 = 0.5373 × net-CONE rather than 0.
#     That is the published market design for this delivery year, not a
#     representation choice — and it is the one structural change (rule 1) the
#     re-anchor carries beyond the level.
_PJM_VRR_CURVE_2028_2029: tuple[CapacityDemandCurvePoint, ...] = (
    CapacityDemandCurvePoint(146703.0 / 145149.08535, 325.00 / 325.69),  # (a) cap
    CapacityDemandCurvePoint(147326.3 / 145149.08535, 277.36 / 325.69),  # (b)
    CapacityDemandCurvePoint(149736.8 / 145149.08535, 175.00 / 325.69),  # (c) floor
    CapacityDemandCurvePoint(153858.0 / 145149.08535, 175.00 / 325.69),  # (d) floor
)

# NYISO NYCA "Demand Curve Length" — the zero-crossing offset above the
# requirement, fixed at 12% for the entire 2021-2025 DCR cycle (Analysis Group
# DCR report Table 2, C-Central/NYCA), so it is not a per-vintage parameter.
_NYISO_NYCA_CURVE_LENGTH: float = 0.12


def _nyiso_icap_vintage_curve(
    ref_point_month: float,
    max_price_month: float,
    length: float = _NYISO_NYCA_CURVE_LENGTH,
) -> tuple[CapacityDemandCurvePoint, ...]:
    """One NYISO NYCA ICAP demand-curve vintage (annualized, first-order).

    The same straight-line construction as the registry ``_NYISO_ICAP_CURVE``:
    net-CONE (fraction 1.0) at the requirement, zero at ``1 + length``, and the
    max-clearing-price cap (fraction = ``max_price_month / ref_point_month``,
    both $/kW-month so basis-independent) placed where that fraction meets the
    reference→zero line.
    """
    cap_frac = max_price_month / ref_point_month
    x_cap = 1.0 - (cap_frac - 1.0) * length
    return (
        CapacityDemandCurvePoint(x_cap, cap_frac),  # max clearing price
        CapacityDemandCurvePoint(1.0, 1.0),  # reference point = Net CONE
        CapacityDemandCurvePoint(1.0 + length, 0.0),  # zero-cross
    )


# ISO-NE FCA vintages (NEISO-RC-R R2 re-derivation 2026-08-31 — see the
# ``_NEISO_FCA_CURVE`` comment for the full published-evidence basis). Three
# published shape families, matched to each delivery year's own auction design:
#
#   * 2020-21 / 2021-22 (FCA 11/12): FCA 11's EXACT published piecewise table
#     (a2_fca11_demand_curves.pdf slide 14), normalized by its published Net
#     ICR 34,075 MW — replacing the first-order linear reduction that skipped
#     the interior kink. FCA 12 published no table of its own; it shares the
#     design family AND the identical cap fraction (both starting prices are
#     1.600 × net-CONE), so it reuses FCA 11's normalized shape (its own
#     measured clearing point, 0.576 @ 1.0327, sits 4.9% below the shape's
#     kink shelf 0.604 — the recorded approximation error).
#   * 2022-23 (FCA 13): its OWN published transition-period construction
#     (ICR filing ER19-291-000, testimony p.48): MRI-based region down to
#     $7.03/kW-month (34,097 MW), then the published linear tail to $0 at
#     35,713 MW. The FCA 13 clearing ($3.800 @ 34,839 MW) lands on that tail
#     segment exactly.
#   * 2023-24 … 2027-28 (FCA 14–18): the pooled measured MRI-era shape
#     (``_NEISO_MRI_CLEARING_POINTS`` + the FCA 13 published zero-quantity),
#     so each vintage's curve passes through its OWN auction's measured
#     point by construction. Per-vintage cap fraction = that FCA's published
#     starting price / net-CONE.
_NEISO_FCA_CAP_X: float = 33_457.0 / 34_075.0  # FCA 11 published plateau end
_NEISO_MRI_ZERO_X: float = 35_713.0 / 33_750.0  # FCA 13 published tail zero

# FCA 11 (2020-2021): the exact published 4-breakpoint piecewise curve,
# x = MW / Net ICR (34,075), y = $/kW-month / net-CONE (11.64). Note the
# FCA 11/12 design pays 1.112 × net-CONE AT the requirement (the net-CONE
# calibration point at the Net ICR arrived with the MRI-era curves).
_NEISO_FCA11_CURVE: tuple[CapacityDemandCurvePoint, ...] = (
    CapacityDemandCurvePoint(33_457.0 / 34_075.0, 18.624 / 11.64),  # cap end
    CapacityDemandCurvePoint(34_718.0 / 34_075.0, 7.03 / 11.64),  # kink
    CapacityDemandCurvePoint(35_437.0 / 34_075.0, 7.03 / 11.64),  # shelf end
    CapacityDemandCurvePoint(37_053.0 / 34_075.0, 0.0),  # published zero
)

# FCA 13 (2022-2023): cap (published starting price 13.05 / net-CONE 8.156 =
# 1.600), net-CONE at the requirement, then the published transition tail.
_NEISO_FCA13_CURVE: tuple[CapacityDemandCurvePoint, ...] = (
    CapacityDemandCurvePoint(_NEISO_FCA_CAP_X, 13.05 / 8.156),
    CapacityDemandCurvePoint(1.0, 1.0),  # Net CONE at requirement
    CapacityDemandCurvePoint(34_097.0 / 33_750.0, 7.03 / 8.156),  # tail start
    CapacityDemandCurvePoint(_NEISO_MRI_ZERO_X, 0.0),  # published zero
)


def _neiso_fca_vintage_curve(
    net_cone_month: float, starting_price_month: float
) -> tuple[CapacityDemandCurvePoint, ...]:
    """One ISO-NE MRI-era FCA delivery-year vintage curve (FCA 14–18 family).

    Cap fraction = ``starting_price_month / net_cone_month`` (both $/kW-month,
    ratio basis-independent) at FCA 11's published plateau end; net-CONE at
    the requirement (the MRI design calibration); the pooled measured MRI-era
    clearing points; zero at FCA 13's published tail zero-quantity (1.0582).
    """
    return (
        CapacityDemandCurvePoint(
            _NEISO_FCA_CAP_X, starting_price_month / net_cone_month
        ),  # starting (max) price
        CapacityDemandCurvePoint(1.0, 1.0),  # Net CONE at requirement
        *_NEISO_MRI_CLEARING_POINTS,  # measured MRI-era curve (FCA 14–18)
        CapacityDemandCurvePoint(_NEISO_MRI_ZERO_X, 0.0),  # zero-cross
    )


# Per-ISO vintages, ascending by delivery-period start year. A vintage equal to
# the MARKET_DESIGN reference REUSES that registry curve object + anchor.
MARKET_DESIGN_VINTAGES: dict[str, tuple[MarketDesignVintage, ...]] = {
    "PJM": (
        # Pre-CIFP vintages (2021/22-2024/25): normalized shapes derived
        # ENTIRELY from each year's own published Planning Period Parameters
        # workbook (RC-1A intake 2026-07-16, data/raw/capacity-market/
        # demand-curve/pjm/pjm.csv + the committed pjm-<yr>-planning-
        # parameters.xlsx copies): x = published VRR point UCAP Level MW ÷
        # (published Reliability Requirement adjusted for FRR + published EE
        # Addback) — PJM's own auction-demand denominator, verified to
        # reproduce the Manual-18 pct_of_requirement fractions to <=0.1% on
        # the 2025/2026 vintage where PJM publishes both forms; y = published
        # VRR point UCAP Price ÷ published UCAP net-CONE (the filings'
        # explicit 1.5x / 0.75x / 0 construction — published values, not a
        # formula guess). Zero fitted parameters (rule 13); reconciliation
        # asserted in tests/test_capacity_demand_curve.py. Anchors unchanged
        # (published UCAP net-CONE $/MW-day, annualized). This replaces the
        # earlier ()-flat-anchor representation, whose position-independent
        # price silently reverted the curve mechanism to fixed-mode for any
        # gate-ON run threading a pre-2026 delivery year (the RC-1A probe).
        MarketDesignVintage(
            "2021/2022",
            321.57 * 365.0 / 1000.0,
            (
                CapacityDemandCurvePoint(156809.2 / 157073.7, 482.36 / 321.57),
                CapacityDemandCurvePoint(160909.3 / 157073.7, 241.18 / 321.57),
                CapacityDemandCurvePoint(168712.9 / 157073.7, 0.0),
            ),
        ),
        MarketDesignVintage(
            "2022/2023",
            260.5 * 365.0 / 1000.0,
            (
                CapacityDemandCurvePoint(136075.5 / 137461.6, 390.75 / 260.5),
                CapacityDemandCurvePoint(139656.3 / 137461.6, 195.38 / 260.5),
                CapacityDemandCurvePoint(146471.2 / 137461.6, 0.0),
            ),
        ),
        MarketDesignVintage(
            "2023/2024",
            274.96 * 365.0 / 1000.0,
            (
                CapacityDemandCurvePoint(135913.6 / 137291.5, 412.44 / 274.96),
                CapacityDemandCurvePoint(139473.2 / 137291.5, 206.22 / 274.96),
                CapacityDemandCurvePoint(146247.9 / 137291.5, 0.0),
            ),
        ),
        MarketDesignVintage(
            "2024/2025",
            293.19 * 365.0 / 1000.0,
            (
                CapacityDemandCurvePoint(138341.3 / 139722.9, 439.79 / 293.19),
                CapacityDemandCurvePoint(141910.4 / 139722.9, 219.89 / 293.19),
                CapacityDemandCurvePoint(148703.1 / 139722.9, 0.0),
            ),
        ),
        # 2025/2026: same construction from the workbook's published UCAP
        # (Level, Price) points (curve_point_ucap rows — the workbook
        # publishes the point prices the narrative PDF leaves formula-
        # defined; point (a) 451.61 $/MW-day is that year's published curve
        # maximum, distinct from the pre-CIFP 1.5x construction and from the
        # ER25-1357 collar scoped to 2026/27-2027/28). x-fractions land on
        # the committed Manual-18 pct curve_point rows (0.989/1.016/1.068)
        # to <=0.1%.
        MarketDesignVintage(
            "2025/2026",
            228.81 * 365.0 / 1000.0,
            (
                CapacityDemandCurvePoint(133554.2 / 135023.4, 451.61 / 228.81),
                CapacityDemandCurvePoint(137160.4 / 135023.4, 171.61 / 228.81),
                CapacityDemandCurvePoint(144105.7 / 135023.4, 0.0),
            ),
        ),
        MarketDesignVintage("2026/2027", 77.431, _PJM_VRR_CURVE),  # registry ref
        MarketDesignVintage(
            "2027/2028", 242.52 * 365.0 / 1000.0, _PJM_VRR_CURVE_2027_2028
        ),
        # 2028/2029 — the FFR-2C re-anchor (see _PJM_VRR_CURVE_2028_2029 above
        # for the three published discontinuities). Anchor = published Net CONE
        # UCAP 325.69 $/MW-day x 365/1000 = 118.877 $/kW-yr, on the same
        # per-ISO convention as every other PJM vintage. This is now the
        # hold-last vintage, so it governs 2028-2050 in a forecast.
        MarketDesignVintage(
            "2028/2029", 325.69 * 365.0 / 1000.0, _PJM_VRR_CURVE_2028_2029
        ),
    ),
    "NYISO": (
        # 2021-2022/2022-2023 published NO NYCA Annual Reference Value and no
        # price cap — only a monthly reference-point price + IRM — so they carry
        # a ()-shape and a FLAT anchor = the published NYCA reference-point price
        # × 12 (a unit conversion of the monthly net-CONE-equivalent point; on a
        # slightly higher basis than the later Annual Reference Value anchors,
        # which net E&AS across all 12 months — used only as the flat fallback
        # for these two past ()-vintages, never a curve). Reference points:
        # 2021-2022 = 7.81, 2022-2023 = 8.87 $/kW-month (nyiso.csv NYCA row).
        MarketDesignVintage("2021-2022", 7.81 * 12.0),
        MarketDesignVintage("2022-2023", 8.87 * 12.0),
        MarketDesignVintage("2023-2024", 74.13, _nyiso_icap_vintage_curve(7.55, 15.62)),
        MarketDesignVintage("2024-2025", 72.35, _nyiso_icap_vintage_curve(7.41, 17.32)),
        MarketDesignVintage("2025-2026", 50.55, _NYISO_ICAP_CURVE),  # registry ref
        # 2026-2027 (FFR-2C re-anchor 2026-08-02; rule 23 — the DATA changed:
        # NYISO posted the second annual update of the 2025-2029 DCR by its
        # tariff deadline 2025-11-30). Same construction as every ARV-era
        # vintage: anchor = NYCA Annual Reference Value ($/kW-yr, the F-Capital
        # representative zone this DCR cycle), shape from the summer
        # reference-point / max-clearing-price pair and the published 12 %
        # Demand Curve Length. Source: NYISO "Demand Curve Parameters
        # CY 2026-2027" (nyiso.csv 2026-2027 rows; sha256 713560dc…207cc).
        # Gross CONE 131.94 − Net EAS 74.24 = 57.70 reconciles the anchor.
        # NOTE (disclosure, not a defect): NYISO is deliberately absent from
        # ScenarioConfig.capacity_market_clearing_by_iso, so the seam prices its
        # FIXED net_cone_per_kw_yr and this vintage is INERT in the shipped
        # posture. It is landed for currency and to make the FF-3D flip
        # decidable on current data, not to change a price today.
        MarketDesignVintage("2026-2027", 57.70, _nyiso_icap_vintage_curve(6.53, 22.41)),
    ),
    "NEISO": (
        # NEISO-RC-R R2 (2026-08-31): per-design-family published shapes — see
        # the block comment above _NEISO_FCA_CAP_X for the three families.
        MarketDesignVintage("2020-2021", 11.64 * 12.0, _NEISO_FCA11_CURVE),
        # FCA 12: same design family and identical published cap fraction
        # (12.864/8.04 = 18.624/11.64 = 1.600) — reuses FCA 11's exact shape.
        MarketDesignVintage("2021-2022", 8.04 * 12.0, _NEISO_FCA11_CURVE),
        MarketDesignVintage("2022-2023", 8.156 * 12.0, _NEISO_FCA13_CURVE),
        MarketDesignVintage(
            "2023-2024", 8.187 * 12.0, _neiso_fca_vintage_curve(8.187, 13.099)
        ),
        MarketDesignVintage(
            "2024-2025", 8.707 * 12.0, _neiso_fca_vintage_curve(8.707, 13.932)
        ),
        MarketDesignVintage(
            "2025-2026", 7.468 * 12.0, _neiso_fca_vintage_curve(7.468, 12.4)
        ),
        MarketDesignVintage(
            "2026-2027", 7.359 * 12.0, _neiso_fca_vintage_curve(7.359, 12.761)
        ),
        MarketDesignVintage("2027-2028", 108.94, _NEISO_FCA_CURVE),  # registry ref
    ),
    "MISO": (
        # Pre-RBDC vintages (PY2021/22-2024/25): a VERTICAL demand curve capped at
        # CONE (FERC ER23-2977) — no sloped shape ever published, so they carry
        # the vertical step (_MISO_VERTICAL_CURVE) anchored on North/Central gross
        # CONE (the LRZ 1-7 mean, the same North/Central aggregation the registry
        # reconciliation test uses), NOT the PY2025-26 sloped RBDC (rule 13: "do
        # not invent slope"). Anchors: 2021/22 & 2022/23 gross CONE in $/MW-day
        # (× 365/1000); 2023/24 & 2024/25 in $/MW-yr (÷1000). ``seasonal_rbdc``
        # stays None, so the seam prices the vertical step for these years.
        MarketDesignVintage(
            "2021-2022", 91.86, _MISO_VERTICAL_CURVE
        ),  # 251.68 $/MW-day
        MarketDesignVintage(
            "2022-2023", 91.06, _MISO_VERTICAL_CURVE
        ),  # 249.49 $/MW-day
        MarketDesignVintage(
            "2023-2024", 103.04, _MISO_VERTICAL_CURVE
        ),  # 103,040 $/MW-yr
        MarketDesignVintage(
            "2024-2025", 123.50, _MISO_VERTICAL_CURVE
        ),  # 123,501 $/MW-yr
        # PY2025-26: the seasonal RBDC (RC-1C). demand_curve keeps the annual
        # reduction for reconciliation; seasonal_rbdc is what the seam evaluates.
        # PY2026-27 is omitted (per-LRZ Net CONE only, no N/C aggregate — rule 5;
        # RBDC chart 403-blocked), so hold-last serves PY2025-26 forward.
        MarketDesignVintage(
            "2025-2026", 79.8, _MISO_RBDC_CURVE, seasonal_rbdc=MISO_SEASONAL_RBDC
        ),  # registry ref
    ),
}


def resolve_demand_curve_vintage(
    iso: "str | None", year: "int | None"
) -> "MarketDesignVintage | None":
    """Return the capacity demand-curve vintage governing ``iso``'s ``year``.

    The per-delivery-year selector behind :meth:`MarketDesign.
    capacity_price_per_firm_mw_yr`'s ``year`` argument (RC-1B item 2). An ISO's
    vintages (:data:`MARKET_DESIGN_VINTAGES`) are ordered ascending by
    delivery-period start year (the leading four digits of
    :attr:`MarketDesignVintage.delivery_year`); resolution is a step function:

    * ``year`` at or after a vintage's start year selects that vintage (the
      latest such — the ISO's most-recent published parameters for that year);
    * ``year`` before the earliest vintage HOLDS-FIRST to it (e.g. a MISO
      year before PY2021-22 gets the 2021-22 VERTICAL vintage — the earliest
      published pre-RBDC step; D28 doc-sync: this example formerly claimed
      pre-2025 years held to the RBDC, stale since the vertical vintages
      landed);
    * ``year`` after the latest vintage HOLDS-LAST to it (the forward-carry a
      forecast uses — the most-recent published curve governs future years).

    Returns ``None`` when ``iso``/``year`` is ``None`` or the ISO has no vintage
    table (CAISO/ERCOT, or any ISO absent from :data:`MARKET_DESIGN_VINTAGES`) —
    the caller then keeps the registry-default curve/anchor byte-identically.
    """
    if iso is None or year is None:
        return None
    vintages = MARKET_DESIGN_VINTAGES.get(iso)
    if not vintages:
        return None
    chosen = vintages[0]
    for v in vintages:
        if year >= int(v.delivery_year[:4]):
            chosen = v
        else:
            break
    return chosen


# --- FF-G3: forward net-CONE evolution beyond the last published vintage ----
#
# ``resolve_demand_curve_vintage`` HOLDS-LAST for any year after an ISO's most
# recent published delivery-year vintage (docstring third bullet): a 2026-2050
# forecast reads one frozen net-CONE anchor for every year past the last
# auction on disk. FF-G3 designs the explicit alternative — an escalation rule
# with a cited forward story — WITHOUT flipping any default (the shipped mode
# stays ``"hold_last"``, byte-identical) and WITHOUT touching the pricing seam
# (:meth:`MarketDesign.capacity_price_per_firm_mw_yr`; the FF-2C wiring lane
# owns that + the per-ISO clearing flips). See
# docs/capacity-price-forward-methodology-2026-07.md for the per-ISO grounding
# tables, delta ledger, field survey, and owner-decision box.
#
# FIELD FINDING (agent survey 2026-07-20; PJM OATT Attachment DD §5.10(a)(iv)
# BLS-Composite index ×1.022; NYISO tariff MST 5.14.1.2.2.1 composite BLS
# (WPUID612/WPU1197) + BEA GDP-deflator blend; ISO-NE Tariff §III.13 interim
# inflation/fuel updates + Handy-Whitman on qualification thresholds; MISO
# Tariff §69A.8 annual GDP-deflator recompute; Brattle 2025 PJM CONE report):
# every ISO escalates GROSS CONE by a construction-cost index and RE-NETS the
# E&AS offset each year — net-CONE is a derived residual, NEVER indexed
# directly. Brattle's own out-year guidance is to escalate the Reference Price
# "on inflation only", i.e. ~0.0 in REAL terms; the sharp recent moves (PJM CC
# gross CONE +44% vs the 2022 study) are STEP re-anchorings picked up by
# intaking each newly-published vintage, not a smooth real trend. Hence the
# cited central REAL rate below is 0.0 for every ISO: a positive value is an
# explicit structural-tightness SENSITIVITY (the 2022-25 turbine surge
# persisting), never a fit (rule 1/13).
NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO: dict[str, float] = {
    "PJM": 0.0,
    "NYISO": 0.0,
    "NEISO": 0.0,
    "MISO": 0.0,
    "CAISO": 0.0,  # no vintage table (fixed CPM-soft-cap proxy); rate unused
}


def forward_net_cone_anchor(
    iso: "str | None",
    year: "int | None",
    escalation: str = "hold_last",
    *,
    rate: "float | None" = None,
    eas_offset_per_kw_yr: "float | None" = None,
) -> "float | None":
    """Return the $/kW-yr net-CONE anchor governing ``iso``'s ``year`` (FF-G3).

    The forward-evolution resolver layered on top of
    :func:`resolve_demand_curve_vintage`. It applies an escalation rule ONLY to
    years *after* the last published vintage's delivery-period start year; a
    year at or before the last vintage returns that vintage's published anchor
    unchanged (the published parameter is the measured input — rule 13).

    ``escalation``:

    * ``"hold_last"`` (default) — byte-identical to
      ``resolve_demand_curve_vintage(iso, year).net_cone_curve_per_kw_yr``. The
      status quo the pricing seam reads today.
    * ``"reindex_net"`` — the last published net-CONE grown by
      ``(1 + rate) ** (year − last_start)``. A cheap approximation; the field
      does NOT index net-CONE directly (see the module finding), so this is a
      documented lower-fidelity option.
    * ``"reindex_gross"`` — the FIELD-STANDARD construction: escalate GROSS CONE
      (``net + eas_offset``) by ``(1 + rate)`` per year and re-subtract the E&AS
      offset — ``(net + eas) * (1 + rate) ** n − eas``. ``eas_offset_per_kw_yr``
      is the published gross−net gap held real-flat here (an offline illustration
      for the methodology doc); the STRUCTURALLY-FAITHFUL version re-nets against
      the model's OWN simulated E&AS margin each forecast year and is wired at
      solve time by FF-2C (this session designs, does not wire).

    ``rate`` (real, per year) defaults to
    :data:`NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO` for ``iso`` (0.0 → every
    mode collapses to ``hold_last``, the byte-identity guarantee and the honest
    central finding). Returns ``None`` when ``iso``/``year`` is ``None`` or the
    ISO has no vintage table (CAISO/ERCOT) — the caller then keeps the fixed
    registry proxy, exactly as :func:`resolve_demand_curve_vintage` does.

    **The zero-rate identity is EXACT, by short-circuit (FFR-3D).** At ``r ==
    0`` the escalation factor is exactly ``1``, so every mode is mathematically
    ``base`` and the function returns ``base`` unchanged. Computing it instead
    — ``(base + eas) * 1.0 ** n − eas`` — does NOT reproduce ``base`` in binary
    floating point: the re-netting cancels in real arithmetic but not in IEEE
    754, and it missed by ~1.4e-14 on 233 of the ISO×year×offset combinations
    swept at the published anchors (PJM 2029+: ``118.87685`` →
    ``118.87684999999999``). The docstring promised the identity; the
    arithmetic did not deliver it. The short-circuit removes round-off from a
    cancellation, changing no mathematics — and it is what lets
    ``net_cone_forward_escalation`` default to ``"reindex_gross"`` (owner D-3a,
    signed 2026-08-03 "byte-identical to hold_last at the signed 0.0 real
    rate") without that default quietly perturbing the anchor.

    It also removes the spurious ``eas_offset_per_kw_yr`` requirement at
    ``r == 0``, where the offset provably cancels. That matters for the flipped
    default: no caller supplies an offset yet (FF-2C owns the wiring), so a
    default-posture call would otherwise RAISE the moment the seam is wired.
    The requirement still holds for a non-zero rate, where the offset genuinely
    determines the answer.

    Not consumed by the live pricing seam yet (scope guard: FF-2C owns
    :meth:`MarketDesign.capacity_price_per_firm_mw_yr`); exercised by tests and
    the offline divergence quantification in the methodology doc.
    """
    vintage = resolve_demand_curve_vintage(iso, year)
    if vintage is None or year is None:
        return None
    base = vintage.net_cone_curve_per_kw_yr
    if escalation == "hold_last":
        return base
    if escalation not in ("reindex_net", "reindex_gross"):
        raise ValueError(
            "forward_net_cone_anchor: escalation must be one of "
            "('hold_last', 'reindex_net', 'reindex_gross'), got "
            f"{escalation!r}"
        )
    last_start = int(vintage.delivery_year[:4])
    n = year - last_start
    if n <= 0:
        # Year at/before the resolved (last published) vintage — published
        # anchor, never escalated (rule 13: the measured parameter governs).
        return base
    r = NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO.get(iso, 0.0) if rate is None else rate
    if r == 0.0:
        # EXACT zero-rate identity (see docstring). (1 + 0) ** n == 1, so both
        # reindex modes are `base` in real arithmetic; returning it directly
        # avoids the float round-off that the gross re-netting would otherwise
        # introduce into a cancellation. This is BEFORE the offset check on
        # purpose: at r == 0 the offset cancels, so demanding it would be a
        # requirement for a value that cannot affect the result.
        return base
    if escalation == "reindex_net":
        return base * (1.0 + r) ** n
    if eas_offset_per_kw_yr is None:
        raise ValueError(
            "forward_net_cone_anchor(escalation='reindex_gross') requires "
            "eas_offset_per_kw_yr at a non-zero rate (the published gross−net "
            "gap, or the model's simulated E&AS offset once FF-2C wires it)"
        )
    gross = base + eas_offset_per_kw_yr
    return gross * (1.0 + r) ** n - eas_offset_per_kw_yr


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
    # MISO Summer ICAP Planning Reserve Margin, PY 2025-26 — the SAME DOCUMENT
    # as the ICAP→UCAP conversion below
    # (PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["MISO"] = 1.079/1.157):
    # MISO PY 2025-26 LOLE Study Report, Module E-1, Summer PRM stated both
    # ways — ICAP 15.7%, UCAP 7.9%. The composite requirement is therefore
    # peak × 1.157 × (1.079/1.157) = peak × 1.079, exactly the document's own
    # UCAP-stated requirement construction. Re-vintaged 2026-08-30 (capx
    # S-123 lane S-1; rule 23 — the SOURCE DATA updated: PY 2025-26 publishes
    # both halves of the pair, where the prior 0.179 was the PY 2024-25 ICAP
    # PRM crossed with the PY 2025-26 conversion, a mixed-vintage composite
    # (peak × 1.09952) equal to NEITHER planning year's published requirement.
    # Expected effect, declared in advance so it cannot be back-fitted:
    # −2,637.4 MW of requirement at the FFR-1C 2026 peak —
    # FINDING-capx-d2b-i7-ledger-2026-08-25.md §2.3.)
    "MISO": 0.157,
    # NYCA Installed Reserve Margin set by NYSRC. Source: NYSRC 2025-2026 IRM
    # Final Base Case (24.4%); NYISO's IRM is structurally high (locality +
    # transmission-security constraints).
    "NYISO": 0.244,
    # ISO-NE: the FCM sizes capacity to a Net Installed Capacity Requirement
    # (Net ICR = ICR - HQICC), NOT a published reserve-margin percentage, so the
    # ISO's own planning reserve margin is the Net-ICR-implied margin over its
    # summer 50/50 peak-load forecast. FF-2B (2026-07-19) replaced the prior
    # 0.157 NERC-reference-margin stand-in with ISO-NE's own Net ICR construction
    # (capacity-clearing flip memo R-7(i); rule 12 -- prefer the ISO's published
    # value over a generic estimate). Vintage anchor = CCP 2026/2027, the
    # delivery year covering the 2026 forecast base year, matching the vintage
    # the other capacity anchors use; value vintage = ISO-NE's NEWEST same-cycle
    # restatement of that CCP (rule 23: re-derive on publication): the ARA 3
    # ICR-Related Values, Net ICR 30,050 MW / summer 50/50 peak 26,648 MW - 1
    # = 12.77% (capx-S4b re-vintage 2026-08-30, superseding the original FCA-17
    # auction values 30,305 / 27,298 = 11.02%, Docket ER23-405-000). Both are
    # ISO-NE's own published, forward-regenerable values (recomputed each
    # FCA/ARA cycle), and the 50/50 peak is on the same "Net (with Reductions
    # for BTM PV)" basis as the model's EIA-930 demand (the filing's peaks embed
    # the CELT §6.3 PDR reconstitution adjustments), so the margin pairs cleanly
    # with the model's peak. Source: ISO New England, "Installed Capacity
    # Requirement, HQICCs and Other Related Values for the 2026-2027 and
    # 2027-2028 CCPs for use in Annual Reconfiguration Auctions", FERC filing
    # 2025-11-21, p.12 (ARA 3 of CCP 2026-27): ICR 31,059 MW, HQICC 1,009 MW,
    # Net ICR 30,050 MW, 50/50 summer peak 26,648 MW. Committed extract +
    # source identities: data/raw/capacity-market/icr-ara/neiso/. Kept as an
    # explicit expression so both published MW values stay traceable (rule 5).
    "NEISO": 30_050.0 / 26_648.0
    - 1.0,  # Net ICR / 50-50 peak - 1 = 0.1277 (ARA 3, CCP 2026/27)
    # SPP (registered 2026-09-06, lane SPP-20; owner ruling r#3 on card P10's
    # PRM correction): the LIVE SPP East BAA Summer Base PRM, 16 %.
    # Source: SPP Planning Criteria v5.0A §4 "Planning Reserve Margin",
    # printed p. 10 (data/raw/spp-planning/SPP_Planning_Criteria_v5.0A.pdf,
    # transcribed in that directory's README §1): East 16 % Summer 2026-2028,
    # rising to 17 % from Summer 2029; Winter 36 % (2026/27-2028/29) -> 38 %
    # (2029/30). SPP sets SEPARATE Base PRMs per BAA — the West BAA (19 %
    # Summer 2027 / 40 % Winter) is the WEIS/Western area and NOT the RTO
    # footprint this model represents, so the East value is the one that
    # applies. This constant is consumed only by the forecast-lane adequacy
    # floor / build backstop, so the live vintage is the right one; the
    # PY2023-2025 value was 15 % (Planning Criteria Rev 4.1A §4 p. 9, "The
    # Planning Reserve Margin shall be fifteen percent (15%)", audit §5 row
    # 1), recorded here as history. The 2029 step to 17 % and the winter leg
    # are NOT encoded — this registry carries one summer scalar per ISO and
    # no winter leg for any ISO; SPP-55 / the capx director own any seasonal
    # extension. Counting basis: Accredited Capacity of wind/solar/storage
    # plus demonstrated net capability of conventional resources (the
    # criteria's own LOLE construction).
    "SPP": 0.16,
    # NWPP (registered 2026-09-14, lane NWPP-20; owner ruling N7, "ONE SCALAR
    # NOW, DECLARED"): 14.4 % = PacifiCorp 2025 IRP Vol. 1 printed p. 131,
    # "the 14.4 percent PRM for July ... adopted from WRAP for the 2025 IRP"
    # (data/raw/nwpp-planning/README.md §4.1) — the one published,
    # per-season, WRAP-derived number in the footprint, and July is the
    # season of the footprint's COINCIDENT peak in all three years, which is
    # the peak this scalar is tested against. The mismatch it cannot express
    # is declared at full magnitude on _nwpp_config: 8 winter-peaking BAs /
    # 6 summer / 1 flipping; NWPP-NW peaks in winter (0.86/0.80/0.82) while
    # NWPP-SNV peaks in summer at 1.95/2.06/1.87x its winter load; NWPP-INLAND
    # mixes both regimes. PacifiCorp's own winter figure is 16.8 % (December,
    # same page); Avista 16 % summer / 24 % winter; NorthWestern takes WRAP's
    # monthly (Jun 26.2 / Jul 14.5 / Aug 16.1 / Sep 14.2 %, 2026 MT IRP Table
    # 39). No single WRAP-wide PRM exists (FSPRMs are monthly and per
    # subregion by construction) and WRAP binds only from Winter 2027-28,
    # past the window. Per-zone seasonal PRM is pre-declared lever NWPP-57.
    "NWPP": 0.144,
    # SOCO (registered 2026-09-14, lane SOCO-20; owner card S6, ruled
    # 2026-09-13: "Register winter 26.0 % as the scalar, misalignment
    # documented"): Southern Company's own published long-term WINTER Target
    # Reserve Margin, 26.00 %. Source: "2024 Reserve Margin Study of the
    # Target Reserve Margin for the Southern Company System" (Jan 2025;
    # Executive Summary, RECOMMENDATIONS; transcription data/raw/soco-planning/
    # transcriptions/2024_Reserve_Margin_Study_Southern_Company_System.txt,
    # values table README §1) — the study's scope is exactly the IIC companies,
    # so it covers Alabama Power (which files no public IRP) as well as
    # Georgia and Mississippi Power. THE SEASONAL STRUCTURE, STATED ON THE
    # FIELD because this registry holds ONE scalar per ISO: the study sets
    # winter 26.00 % / summer 20.00 % long-term (25.5 / 19.5 inside three
    # years, winter EORM 22.75 / summer 18.25, winter 1:10 LOLE threshold
    # 25.75 %), and WINTER IS THE BINDING SEASON — SOCO is winter-peaking in
    # two of the three backcast years (EIA-930 BA peak 47,368 MW on 2024-01-17
    # 07:00 and 46,490 MW on 2025-01-22 08:00 Central, against 45,558 MW on
    # 2023-08-25 16:00; in 2025 the summer peak sits 0.25 % below winter),
    # the all-time system maximum in the 10-K is the 2024-01-17 winter event,
    # and NERC's SERC-Southeast probabilistic risk lands in winter mornings
    # (SOCO-12 §1.3). Georgia Power ALONE stays summer-peaking, and NERC
    # classifies SERC-SE as summer-peaking — adequacy binds in winter while
    # energy peaks in summer, which is why the two TRMs differ by six points.
    # Consumed only by the forecast-lane adequacy floor / build backstop
    # against the model's ANNUAL peak, so pairing the winter margin with a
    # summer-peaking model year overstates the requirement by the 26/20
    # spread in that year — a seasonal registry for every ISO was offered and
    # DECLINED as an ISO-addition act (card S6); it stays a chartered lane.
    # Counting basis: the study's own LOLE construction (capacity net of
    # market assistance modelled — see ADEQUACY_EXTERNAL_TIE_FIRM_MW["SOCO"]).
    "SOCO": 0.26,
}

# Data-horizon gate for honoring an ANNOUNCED (non-fossil) EIA-860 retirement
# date deterministically. A self-reported planned-retirement year is credible
# only at the same near-term grain the additions pipeline trusts its U/V/TS
# statuses: within the ACTIVE operable-snapshot vintage + this many years
# (vintage-aware since FH-1 — apply_announced_retirements resolves
# data.fleet.operable_vintage_year, so a vintage-seeded hindcast measures the
# horizon from its own seed year; non-vintage runs keep
# EIA860_OPERABLE_VINTAGE + this many years exactly). Beyond the horizon
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
        # MISO SOLAR has no published probabilistic ELCC *curve* — only the
        # flat seasonal class-average defaults below, wired at FFR-4B (owner
        # decision D-12, sitting Addendum O, 2026-08-04) under rule 14
        # [R-ACCURATE]: the ISO's own published number is on disk and cited,
        # so it displaces the generic 0.18 fallback whatever it does to a fit.
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
        # SOLAR — MISO's published SEASONAL class-average capacity credit,
        # reconciled to this registry's ANNUAL grain (FFR-4B / owner D-12).
        # The PY2025-26 Wind and Solar Capacity Credit Report's cover-page
        # Highlights publish a flat default seasonal solar capacity credit of
        # 50 % for Summer / Fall / Spring and 5 % for Winter 2025-26. It is a
        # FLAT default, not a penetration curve, so this is a single-point
        # (constant) curve — never fabricate the axis MISO did not publish
        # (the P-0B intake discipline the NYISO CAF entries below follow).
        #
        # SEASONAL -> ANNUAL SELECTION RULE (settled here, not left implicit):
        # DURATION-WEIGHTED MEAN OVER MISO'S FOUR PRA SEASONS, which reduces
        # to the equal-weighted arithmetic mean because the four seasons are
        # equal-length quarters:
        #     (50 + 50 + 5 + 50) / 4 = 38.75 %  ->  0.3875
        # Grounding, in two published facts and one property of this model:
        #  (a) MISO's Planning Resource Auction has been SEASONAL since
        #      PY2023-24 (FERC-accepted seasonal resource-adequacy construct,
        #      ER22-495; Tariff Module E-1). It clears FOUR separate seasonal
        #      auctions, each with its own requirement and its own price, over
        #      a June 1 - May 31 Planning Year split into four THREE-MONTH
        #      seasons: Summer (Jun-Aug), Fall (Sep-Nov), Winter (Dec-Feb),
        #      Spring (Mar-May). A resource is paid in EVERY season on THAT
        #      season's accredited capacity — it is not denied its summer
        #      revenue because its winter credit is low, which is why a
        #      peak-risk MINIMUM rule (winter 5 %) is wrong for MISO however
        #      right it is for a single-requirement annual construct.
        #  (b) Annual capacity revenue is therefore
        #      SUM_s (price_s x days_s x credit_s). This model carries ONE
        #      annual capacity price per firm MW
        #      (MarketDesign.capacity_price_per_firm_mw_yr) and ONE annual
        #      credit, which is exactly the assertion that the four seasonal
        #      prices are equal; under that assertion the revenue-preserving
        #      annual-equivalent credit is the duration-weighted mean of the
        #      seasonal credits. Equal-length seasons make it the plain mean.
        # This is the rule-14 [R-ACCURATE] "reconciled version of the real
        # data" for a genuine time-aggregation misalignment — documented, and
        # preferred over both the raw lift (summer-only 0.50, which pays the
        # winter quarter a credit MISO does not grant) and the guess it
        # replaces (the generic 0.18 flat fallback, no MISO content at all).
        # Exact-day weighting (92/91/90/92 days) gives 142/365 = 0.3890, a
        # +0.0015 difference that is an order of magnitude below the grain of
        # the published 50 %/5 % figures themselves; the equal weights are
        # taken as the settled rule and the day-weighted variant is recorded
        # here only to show the choice does not carry the result.
        # ONE credit serves BOTH consumers of the single adequacy resolver
        # (rule 19 [R-ONE-MECH]): the entry screen's VRE capacity payment and
        # the adequacy ledger (retirement reliability floor, reserve-margin
        # backstop, CR-1 reserve position) — see FFR-4B's asymmetry section.
        "solar": RenewableElccCurve(
            penetration_basis=None,
            points=((0.0, 0.3875),),
            source=(
                "MISO PY2025-26 Wind and Solar Capacity Credit Report, cover-"
                "page Highlights: default seasonal solar capacity credit 50 % "
                "Summer/Fall/Spring + 5 % Winter 2025-26, duration-weighted "
                "over MISO's four equal-length PRA seasons (= equal-weighted "
                "mean) -> 0.3875 — "
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

# --------------------------------------------------------------------------- #
# The DELIVERY-YEAR VINTAGE axis on VRE accreditation (capx D75-R, 2026-09-06)
# --------------------------------------------------------------------------- #
# THE DEFECT (FINDING-capx-d66-2026-09-06.md §8 card B, measured in
# FINDING-capx-d75-2026-09-06.md §3): RENEWABLE_ELCC_CURVES_BY_ISO["PJM"] above
# is digitized from PJM's 2026/27 + 2027/28 BRA final ratings — the ER24-99
# MARGINAL-ELCC construct — and both classes CLAMP on every PJM pool in the
# 2021-2025 hindcast window (wind >= 3,956 MW -> 0.41; solar <= 9,902 MW ->
# 0.1064). So the model accredits PJM VRE at the 2026/27 rating in EVERY
# delivery year, including three whose auctions cleared on a DIFFERENT published
# rating set under a DIFFERENT (class-average) construct. That is the same
# mixed-vintage defect capx D48 repaired on the thermal and requirement halves,
# left open on the VRE half — which is why this registry is keyed and gated in
# the D48 family rather than as a mechanism of its own (rule 19 [R-ONE-MECH]).
#
# EVERY VALUE IS A PUBLISHED PJM CLASS RATING, transcribed to
# data/raw/capacity-market/elcc/pjm/pjm.csv with source doc + page + sha256 per
# row by the D75-R intake, and reconciled to those committed rows BYTE-FOR-BYTE
# by tests/unit/data/test_renewable_elcc_curves.py. ZERO free parameters beyond
# the ONE declared reconciliation named below (rules 5/13/21/23).
#
# THE ONE RECONCILIATION, DECLARED AT THE SEAM (director ruling R1, 2026-09-06,
# on FINDING-capx-d75-2026-09-06.md §8(a) option (1)). The model carries ONE
# `solar` class; PJM rates TWO (Solar Fixed Panel / Solar Tracking Panel).
# Blending them needs a fixed-tilt / tracking installed-MW split, and PJM
# PUBLISHES NO SUCH SPLIT FOR ANY PRE-REFORM VINTAGE — seven primary documents
# read, none carries the pairing (FINDING §2). The ruling: carry PJM's OWN
# published Table-5 mix as a documented CROSS-VINTAGE reconciliation under rule
# 14 [R-ACCURATE]'s misalignment exception — a published PJM number on the wrong
# vintage, stated as such here and in the finding, with FINDING §3's bracket
# recorded as its sensitivity. It is the 2026/27 pairing the solar curve above
# already reconciles against (Fixed-Tilt 1,189 MW vs Tracking 8,713 MW), written
# as the arithmetic rather than a rounded literal so no magic number exists
# (rule 5) and the test re-derives it from the same committed rows.
#
# WHAT IS FORBIDDEN HERE, BY NAME (rule 13 [R-MEASURED], ruling R1): a split
# sized to the position residual; a split backed out of PJM's cleared solar
# UCAP (that would derive an input from the very outcome the census is compared
# against); and any adder, haircut or blend weight chosen for what it does to a
# gate. The EIA-860 `Fixed Tilt?` / `Single-Axis Tracking?` derivation — the one
# route that regenerates forward from the model's own build (FINDING §8(a)
# option (2)) — is a SEPARATE data-intake card and is deliberately not taken
# here.
#
# THE CONCLUSION IS MIX-INSENSITIVE, which is why one declared mix is enough to
# decide the card: the sign is DOWN in every in-scope delivery year at every
# admissible mix, and DY 2024/25's break-even blend is 0.5527 — ABOVE PJM's own
# tracking rating of 0.50 — so the implied fixed share is NEGATIVE (-0.310) and
# no admissible mix can flip it (FINDING §3).
PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE: float = 1189.0 / (1189.0 + 8713.0)
"""Fixed-tilt share of PJM's rated solar fleet, 12.01 % (2026/27 pairing).

PJM's ELCC/RRS Table 5 (pp.16-17) installed MW for the 2026/2027 BRA —
Fixed-Tilt Solar 1,189 MW against Tracking Solar 8,713 MW — the ONLY vintages
for which PJM pairs installed MW with class ratings at all. Applied to the
PRE-reform vintages below as a declared cross-vintage reconciliation (director
ruling R1; rule 14's misalignment exception), never as a fitted weight.
"""

# Per-delivery-year published VRE ELCC class ratings for the ISOs that publish
# them, read at rung 0 of resolve_renewable_capacity_credit's ladder under the
# default-OFF ``ScenarioConfig.pjm_vre_accreditation_vintage`` gate (predicate
# :func:`~market_sim.model.capacity_evolution.retirements.
# vre_accreditation_vintage_armed`, which additionally requires D48's own gate —
# see its docstring for why the VRE half can never be vintaged while the thermal
# half is not). Keyed by the delivery-year label
# :func:`~market_sim.data.capacity_deliverability.resolve_delivery_year`
# builds, exactly as the D48 thermal and requirement halves are.
#
# NO HOLD-LAST, DELIBERATELY. A delivery year absent from the table — every year
# from 2026/27 onward, and every pre-ELCC year through 2022/23 — falls straight
# through to the penetration-indexed curve above, which is digitized from the
# 2026/27+ ratings and is the right basis there. Carrying a pre-reform class
# rating forward past the reform would be exactly the mixed-vintage error this
# registry exists to remove. Pre-ELCC years (PJM's ELCC construct first applied
# to the 2023/2024 BRA, ratings posted 2021-12-16) have no published rating of
# any kind and stay on the incumbent curve, out of this card's scope.
RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO: dict[str, dict[str, dict[str, float]]] = {
    "PJM": {
        # 2023/2024 BRA — the FIRST delivery year PJM's ELCC construct applied
        # to (its ratings posted 2021-12-16; the December 2021 report's own
        # Table 3 is titled "Comparison of ELCC Class Ratings, 2024/2025 BRA vs
        # 2023/2024 BRA"). Onshore Wind 15 %, Solar Fixed Panel 38 %, Solar
        # Tracking Panel 54 %. Class-average construct.
        "2023/2024": {
            "wind": 0.15,
            "solar": (
                PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE * 0.38
                + (1.0 - PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE) * 0.54
            ),
        },
        # 2024/2025 — the December 2023 study's FINAL ratings, NOT the December
        # 2021 preliminary set (wind 16 %, solar 36/54 %) the repo carried
        # alone until the D75-R intake. The 2024/25 BRA was delayed and
        # re-executed (FERC ER23-729) and PJM re-ran the ELCC study; the
        # December 2023 report states in terms that "only the 2024/2025 values
        # are final". Onshore Wind 21 %, Solar Fixed 33 %, Solar Tracking 50 %.
        # Wiring the superseded set would put a stale published number on the
        # accreditation path, which rule 14 forbids as squarely as an estimate.
        "2024/2025": {
            "wind": 0.21,
            "solar": (
                PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE * 0.33
                + (1.0 - PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE) * 0.50
            ),
        },
        # 2025/2026 — PJM's FINAL ratings for the delivery year, applied to its
        # Third Incremental Auction (posted 2025-03-12). The first
        # marginal-ELCC delivery year, and the one this card would leave
        # mis-vintaged if the axis stopped at the reform boundary: the wired
        # 2026/27 set reads 41 / 8 / 11 % where this delivery year's own final
        # ratings are 38 / 10 / 14 % (FINDING-capx-d75 §5). Rating the thermal
        # classes at all, this posting independently CONFIRMS
        # THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO["PJM"] == "2025/2026".
        #
        # OPEN, AND NOT CLOSED HERE (FINDING §5): this is the 3IA vintage. The
        # 2025/26 BRA (held July 2024) cleared on the ratings current then, and
        # that report's tables are images that do not extract. This lane reads
        # the delivery year's FINAL ratings — the same "what did this delivery
        # year actually settle on" question the 2024/25 row answers with the
        # Dec-2023 study — and says so rather than leaving it implicit.
        "2025/2026": {
            "wind": 0.38,
            "solar": (
                PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE * 0.10
                + (1.0 - PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE) * 0.14
            ),
        },
    },
}

# Published CLASS-AVERAGE accreditation held behind its own default-off gate
# (``ScenarioConfig.caiso_nqc_accreditation``, FFR-3P 2026-08-04). Read at rung
# 0 of the SAME ladder as RENEWABLE_ELCC_CURVES_BY_ISO by the SAME resolver
# (:func:`market_sim.model.capacity.resolve_renewable_capacity_credit`) — one
# accreditation mechanism, one resolver (rule 19); this registry only holds the
# entries whose admission is gated, so an unarmed run is byte-identical.
#
# WHY IT IS A SEPARATE REGISTRY RATHER THAN A CAISO KEY ABOVE. The
# ``renewable_elcc_curves`` gate ships default-ON, so adding CAISO to
# RENEWABLE_ELCC_CURVES_BY_ISO would change every CAISO forecast solve on the
# next commit. FFR-3P's charter requires the arm to ship DEFAULT-OFF pending an
# owner decision on arming posture (rules 5/24/28), and this is the cheapest
# honest way to hold a published value inert until that decision.
#
# CAISO — the rule 14 [R-ACCURATE] repair. Before this entry the ISO with the
# most elaborate published VRE accreditation in the country was accredited on
# the GENERIC non-CAISO fallback (RENEWABLE_CAPACITY_CREDIT: solar 0.18, wind
# 0.16), measured invariant across a 0.2x-2.0x penetration sweep (FFR-3H §3.3).
# The values below are CAISO's OWN published accreditation, read from the SAME
# workbook and the SAME "Tech Factors" tab that
# HYDRO_ACCREDITATION_CREDIT_BY_ISO["CAISO"] already cites — the solar and wind
# blocks that sit directly above the "Non-dispatchable Hydro" block it reads.
#
#   Source: CAISO, "Net Qualifying Capacity Report for Compliance Year 2026",
#   tab "2026 Tech Factors" (Solar Fixed / Solar Tracking / Solar Thermal
#   Exceedance and Wind Exceedance blocks) x tab "2026 NQC List" (the per-
#   resource monthly NQC MW that supplies the fleet mix). Committed at
#   data/raw/capacity-market/nqc/caiso/net-qualifying-capacity-report-cy2026.xlsx;
#   CPUC adopted QC methodology D.10-06-036 App. B.
#
# THE BLEND IS SAME-DOCUMENT ARITHMETIC, exactly like PJM's two-class solar
# rating above. CAISO publishes per-(technology, region) factors while the model
# carries one `solar` and one `wind` class, so each published sub-class factor is
# weighted by that sub-class's nameplate in CAISO's own NQC List
# (scripts/data/derive_caiso_nqc_class_factors.py, which recovers the mix from
# the identity NQC = Pmax x factor; review artifact
# data/raw/capacity-market/nqc/caiso/caiso_nqc_class_factors.csv, reconciled
# against these literals by tests/unit/data/test_caiso_nqc_class_factors.py).
#   solar: 12,470.4 MW matched over 200 resources — tracking 5,167.5 Socal +
#          2,691.3 Norcal, fixed 2,030.5 Socal + 1,664.2 Norcal, thermal 917.0.
#   wind : 6,211.3 MW matched over 97 resources — 4,752.8 Socal + 1,458.5 Norcal.
# The out-of-state wind geographies CAISO also publishes (AZ / NM / WA-OR,
# 0.24-0.31 in the peak months) are EXCLUDED: they accredit imported wind, which
# the model credits at the seam through ADEQUACY_EXTERNAL_TIE_FIRM_MW, and
# folding them into the in-ISO pool would double-count it (the _firm_import_mw
# discipline, rule 19).
#
# MONTH SELECTION — the identical rule the hydro entry already applies. CAISO's
# accreditation is published per MONTH and the model's ledger carries one annual
# credit against the annual peak, so the registry takes the MINIMUM over CAISO's
# Jul/Aug/Sep peak-risk months, and the credit therefore holds in whichever of
# them the model's peak lands (HYDRO_ACCREDITATION_CREDIT_BY_ISO["CAISO"] takes
# Sep on exactly this rule). Published CY2026 peak-month factors:
#   solar: Jul 0.6365 / Aug 0.2096 / Sep 0.3942  -> 0.2096 (Aug binds)
#   wind : Jul 0.3873 / Aug 0.3359 / Sep 0.2202  -> 0.2202 (Sep binds)
# Collapsing a monthly (slice-of-day) accreditation onto one annual credit is a
# TIME-AGGREGATION misalignment against the model's representation, so under rule
# 14 this is the RECONCILED version of the real data, not a raw lift — and the
# reconciliation is stated rather than buried. Resolving the credit at the
# model's OWN peak month instead is the routed refinement (it needs the peak
# month threaded into the ledger, which today receives only peak MW); it would
# RAISE solar materially in a September-peaking year (0.3942 vs 0.2096).
#
# NO PENETRATION AXIS IS FABRICATED (the RenewableElccCurve contract). CAISO's
# published class accreditation is an exceedance statistic on measured
# production, not a marginal-ELCC curve, so it carries no penetration axis and
# is encoded as a single-point constant — the same shape NYISO's CAFs take.
# CAISO's marginal-ELCC study exists (data/raw/capacity-market/elcc/caiso/
# caiso.csv) and is deliberately NOT used here: a marginal-tranche value is not
# a whole-fleet ledger credit (the misalignment the note above records).
#
# VINTAGE. CY2026, matching the forecast base year. The CY2027 draft-final
# report moves the AUGUST solar factors sharply (tracking Norcal 0.2672 ->
# 0.6020), which would move the solar peak-risk minimum from Aug 0.2096 to Sep
# 0.3944 — recorded so the vintage is visibly load-bearing. Refresh on a
# published-vintage update (rule 23), never on a residual.
RENEWABLE_NQC_CURVES_BY_ISO: dict[str, dict[str, RenewableElccCurve]] = {
    "CAISO": {
        "solar": RenewableElccCurve(
            penetration_basis=None,
            points=((0.0, 0.2096),),
            source=(
                "CAISO Net Qualifying Capacity Report, Compliance Year 2026, "
                "'2026 Tech Factors' solar exceedance blocks blended on the "
                "'2026 NQC List' fleet mix (12,470.4 MW / 200 resources); "
                "August = min over the Jul/Aug/Sep peak-risk months — "
                "data/raw/capacity-market/nqc/caiso/"
                "net-qualifying-capacity-report-cy2026.xlsx"
            ),
        ),
        "wind": RenewableElccCurve(
            penetration_basis=None,
            points=((0.0, 0.2202),),
            source=(
                "CAISO Net Qualifying Capacity Report, Compliance Year 2026, "
                "'2026 Tech Factors' Wind Exceedance Norcal/Socal blended on "
                "the '2026 NQC List' fleet mix (6,211.3 MW / 97 resources; "
                "out-of-state AZ/NM/WA-OR excluded — credited at the seam via "
                "ADEQUACY_EXTERNAL_TIE_FIRM_MW); September = min over the "
                "Jul/Aug/Sep peak-risk months — data/raw/capacity-market/nqc/"
                "caiso/net-qualifying-capacity-report-cy2026.xlsx"
            ),
        ),
    },
}

# Thermal accreditation basis for the same adequacy ledger, per ISO. Default
# (ISO absent): "ucap" = pmax x (1 - EFORd). Three published-basis alternatives:
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
# * "claimed_capability" counts thermal at its Qualified Capacity with NO
#   forced-outage derate — ISO-NE's FCM convention. A resource's summer QC is
#   the median of its last five years' Seasonal Claimed Capability (Market
#   Rule 1 §III.13.1.2.2.1.1, eff. 2025-05-03); a full-text search of the
#   235-page III.13/III.14 tariff for "EFORd" returns zero matches. EFORd
#   enters only the system-wide GE MARS/ICR reliability sizing (ICR Reference
#   Guide §5.6.1), never an individual resource's accredited MW; individual
#   forced-outage/performance risk is instead priced ex post through
#   Pay-for-Performance (§III.13.7.2), so applying (1-EFORd) here would
#   double-derate a risk ISO-NE already prices separately. Numerically identical
#   to "seasonal_rating" (returns 1.0) but kept a DISTINCT basis because the
#   *reason* for no derate differs (ERCOT: target margin; ISO-NE: ex-post PFP) —
#   a citation trail must trace to the actual mechanism, not a numerically-
#   convenient neighbor (rule 5/13; R5b, pairing-adjudication 2026-07-15 §1).
#   Dating caveat: current through the FCM's CCP2027-2028 sunset (final FCA held
#   Feb 2024), not validated against the successor accreditation-reform process.
THERMAL_ACCREDITATION_BASIS_BY_ISO: dict[str, str] = {
    "ERCOT": "seasonal_rating",
    "PJM": "elcc_class_rating",
    "NEISO": "claimed_capability",
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

# --------------------------------------------------------------------------- #
# The DELIVERY-YEAR VINTAGE axis on THERMAL accreditation (capx D84, 2026-09-07)
# --------------------------------------------------------------------------- #
# THE DEFECT (FINDING-capx-d75r-2026-09-06.md §6 item 4, which ROUTED this card
# here). THERMAL_ELCC_CLASS_RATING_BY_ISO["PJM"] above is a SINGLE-VINTAGE table
# — its own comment says so: "the 2026/2027 BRA official/final class-average
# rating". But THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO["PJM"] is
# "2025/2026", so DY 2025/2026 is the FIRST delivery year accredited on the
# ELCC-class design at all — and it has its OWN published final class ratings,
# which DIFFER: Gas Combined Cycle 78 vs 74, Gas Combustion Turbine 63 vs 60,
# Steam 74 vs 73, Diesel Utility 92 vs 91 (Nuclear 95 and Coal 83 equal). One
# post-reform rating table is therefore applied to a delivery year that settled
# under a different published rating set. That is the SAME mixed-vintage defect
# capx D48 repaired on the basis axis and capx D75-R repaired on the VRE axis,
# left open on the thermal RATING axis — which is why this registry is keyed and
# gated INSIDE the D48 family rather than as a mechanism of its own (rule 19
# [R-ONE-MECH]), exactly as D75-R's is.
#
# THE BASIS IS RULE 14 [R-ACCURATE], NEVER THE RESIDUAL. These are the ISO's own
# published accreditation values for the delivery year each auction actually
# settled on. Preferring the published vintage is what the rule requires
# whatever it does to the fit, and a rating vintage is never selected by what it
# does to a criterion (rule 1 [R-STRUCT]).
#
# EVERY VALUE IS A PUBLISHED PJM CLASS RATING already committed to
# data/raw/capacity-market/elcc/pjm/pjm.csv by the D75-R intake (which carried
# the thermal rows alongside the VRE ones — FINDING-capx-d75r §6 item 4: "The
# intake now carries them"), with source doc + page per row, and reconciled to
# those committed rows BYTE-FOR-BYTE by tests/unit/data/test_thermal_elcc_
# vintage_ratings.py. ZERO free parameters and ZERO scalar fields (rules 5/13/
# 21/23/24): nothing here is typed that the csv does not carry, and nothing is
# blended, reconciled or weighted — unlike the VRE half, PJM rates each of the
# model's thermal classes with exactly ONE published class, so D75-R's single
# cross-vintage reconciliation has NO analogue here and none is introduced.
#
# THE ADMISSIBILITY RULE, fixed before any solve and not selectable by a result:
# a published rating enters this registry iff it is (i) elcc_type
# "class_average" — the construct the accredited-UCAP census is built from, so
# the "marginal" indicative rows are excluded by construction — AND (ii) an
# OFFICIAL/FINAL posting FOR that delivery year, so every "preliminary,
# non-binding, indicative" row is excluded. Applied to the committed csv that
# admits exactly three PJM vintages: 2025/2026 3IA (final for DY 2025/2026,
# posted 2025-03-12), 2026/2027 BRA (official/final) and 2027/2028 BRA
# (official/final).
#
# WHICH POSTING GOVERNS DY 2025/2026 — and the trap that is NOT available. This
# registry reads the delivery year's FINAL ratings, i.e. the 3IA posting of
# 2025-03-12: the same "what did this delivery year actually settle on" question
# D75-R's own 2025/2026 VRE row answers with the same posting, and its 2024/2025
# row answers with the Dec-2023 final study rather than the Dec-2021
# preliminary set. The alternative — the ratings current when the 2025/26 BRA
# was held in July 2024 — IS NOT SOURCEABLE: that report's tables are images
# that do not extract (FINDING-capx-d75-2026-09-06.md §5, FINDING-capx-d75r §6
# item 3). A BRA-vintage rule that cannot be sourced is not available to this
# lane; the rule actually used is stated here rather than left implicit.
#
# NO HOLD-LAST, DELIBERATELY — the same reasoning as D75-R's registry. A
# delivery year absent from the table falls straight through to the incumbent
# single-vintage THERMAL_ELCC_CLASS_RATING_BY_ISO, which IS the 2026/27 set and
# is the right basis wherever no other final rating is published (2028/29 onward
# carries only preliminary marginal ratings, which the admissibility rule
# excludes). Carrying a rating forward past its own posting would rebuild the
# very mixed-vintage error this registry removes.
#
# PRE-REFORM YEARS NEVER REACH THIS TABLE, and the two vintage axes COMPOSE
# rather than STACK (rule 19). resolve_thermal_accreditation_basis already
# resolves "ucap" for a delivery year strictly before the reform entry under the
# D48 arm, so the elcc_class_rating branch — the only place this registry is
# read — is not taken there at all. In the PJM 2021-2025 hindcast window that
# leaves exactly ONE delivery year on this axis: DY 2025/2026.
#
# THE CLASS MAPPING IS UNCHANGED. This axis moves the VINTAGE only: it reuses
# THERMAL_ELCC_CLASS_RATING_BY_ISO's model-fuel -> PJM-class mapping exactly
# (gas_ct -> "Gas Combustion Turbine", not the Dual Fuel class; oil -> "Diesel
# Utility"; gas_st -> "Steam"), and a model fuel the incumbent table does not
# carry (biomass) stays absent here and keeps its UCAP fallback. Re-mapping a
# class would be a second mechanism on the same phenomenon (rule 19).
#
# Read at the TOP of thermal_accreditation_fraction's elcc_class_rating branch
# under the default-OFF ``ScenarioConfig.pjm_thermal_accreditation_vintage``
# gate (predicate :func:`~market_sim.model.capacity_evolution.retirements.
# thermal_accreditation_vintage_armed`, which additionally requires D48's own
# gate — see its docstring). Keyed by the delivery-year label
# :func:`~market_sim.data.capacity_deliverability.resolve_delivery_year` builds,
# exactly as the D48 and D75-R halves are.
THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO: dict[str, dict[str, dict[str, float]]] = {
    "PJM": {
        # 2025/2026 — PJM's FINAL class ratings for the delivery year, applied
        # to its Third Incremental Auction (posted 2025-03-12); the same posting
        # RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO["PJM"]["2025/2026"] reads. This
        # is the FIRST delivery year on the ELCC-class design
        # (THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO["PJM"]), which this
        # posting independently confirms by rating the thermal classes at all,
        # and it is the ONE row the defect above is about.
        "2025/2026": {
            "nuclear": 0.95,  # Nuclear (equal to the 2026/27 set)
            "coal": 0.83,  # Coal (equal to the 2026/27 set)
            "gas_cc": 0.78,  # Gas Combined Cycle (2026/27: 0.74)
            "gas_ct": 0.63,  # Gas Combustion Turbine (2026/27: 0.60)
            "gas_st": 0.74,  # Steam (2026/27: 0.73)
            "oil": 0.92,  # Diesel Utility (2026/27: 0.91)
        },
        # 2026/2027 BRA (official/final) — the vintage the incumbent
        # single-vintage table already carries, restated here so the registry is
        # the ISO's published rating SERIES rather than a one-year patch. An
        # exact no-op against the incumbent by construction, and asserted so by
        # test: if these two ever diverge, one of them is wrong.
        "2026/2027": {
            "nuclear": 0.95,
            "coal": 0.83,
            "gas_cc": 0.74,
            "gas_ct": 0.60,
            "gas_st": 0.73,
            "oil": 0.91,
        },
        # 2027/2028 BRA (official/final) — the LAST vintage the admissibility
        # rule admits. Outside the 2021-2025 hindcast window entirely; it is
        # here because the rule above admits it, not because any measurement
        # asked for it, and it is what makes the "no hold-last" fall-through
        # start at DY 2028/2029 rather than at 2027/2028.
        "2027/2028": {
            "nuclear": 0.95,
            "coal": 0.83,
            "gas_cc": 0.74,
            "gas_ct": 0.61,
            "gas_st": 0.72,
            "oil": 0.92,
        },
    },
}

# First delivery year on which an ISO's CURRENT thermal accreditation design
# (THERMAL_ACCREDITATION_BASIS_BY_ISO) applies, per ISO — the vintage axis of
# the accreditation basis (capx D48, 2026-09-04, executing
# FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md §2.3 item 1). Consumed ONLY
# under the default-OFF ``ScenarioConfig.pjm_accreditation_design_vintage``
# gate (rule 28 row ``pjm_accreditation_design_vintage``): for a delivery year
# strictly BEFORE the entry the thermal fleet is accredited on the design the
# auction of that year actually cleared on — UCAP, ``1 − EFORd`` — and from
# the entry onward on the registry basis, exactly as the published design
# switched. Off, every solve is byte-identical to the single-vintage basis.
#
# * PJM — "2025/2026": the Critical Issue Fast Path (CIFP) accreditation
#   reform, PJM's ER24-99 filing (2023-10-13), accepted by FERC on 2024-01-30
#   (166 FERC ¶ 61,058), first applied in the 2025/2026 BRA (held July 2024):
#   every resource class, thermal included, is accredited at an ELCC-based
#   class rating (Manual 21A "Determination of Accredited UCAP", Rev. 0
#   eff. 2024-05-21). Before it (2021/22–2024/25) PJM Manual 18 §4.2.1 /
#   Manual 21 §2 accredited a generation Capacity Resource at Installed
#   Capacity × (1 − EFORd) — the UCAP design the registry default reproduces.
#   D45 §2.2 measured the consequence of accrediting the 2021–2024 fleet on
#   the 2025/26+ ELCC-class design: ELCC supply understates the UCAP fleet by
#   ~15 % (137.6 vs ~162 GW thermal), and, paired with the composite
#   requirement, lands the model's position at 1.14–1.18 where the auctions
#   sat at 1.05. Rule 13: the design switch is a market-design date (an
#   instrument on file at the run's information cutoff — the D42/D44 vintage
#   gate), and the identical construction regenerates forward (the current
#   design carries forward; a future re-design is intaken as a new entry).
#   Rule 23: refresh on a published design change only, never a residual.
THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO: dict[str, str] = {
    "PJM": "2025/2026",
}

# Demand-response / load-management capacity products counted in the ISO's
# own adequacy construction, expressed as the netting fraction applied to the
# model's gross peak in :func:`market_sim.model.capacity.
# resolve_adequacy_requirement_mw` (``firm_peak = peak × (1 − fraction)``,
# netted BEFORE the FPR / (1+PRM)×ratio multiplication). These are standing
# DR programs whose enrollment/participation scales roughly with load, so a
# fraction regenerates for forward years and responds to changed conditions
# (rule 13 admissible: a market-design input, not an outcome). ISOs absent
# here net nothing (neutral fallback).
# * ERCOT (Dec 2025 CDR Seasonal Summary, summer-2026 peak-load-hour column):
#   Load Resources providing RRS 935 + Non-Spin 50 + ECRS 300 + controllable
#   LRs 20 + Emergency Response Service 2,750 + TDSP standard-offer load
#   management 303 + distribution voltage reduction 1,162 = 5,520 MW on the
#   95,419 MW gross seasonal peak = 5.8%. Netting from the peak IS ERCOT's
#   own construction (the CDR's "Firm Peak Load"). Rooftop-PV netting is
#   EXCLUDED — EIA-930 demand is already net of behind-the-meter PV.
# * PJM (W2-D, closes gap G10 / W1-B B1): PJM does NOT net DR from its load
#   forecast — DR clears the BRA as a SUPPLY-side capacity resource, so the
#   published construct misaligns with this registry's netting form and the
#   value is a documented reconciliation (rule 14), never a raw fraction of
#   peak. Published anchors (2026/2027 BRA Report, posted 2025-07-22): DR
#   cleared 5,795 MW UCAP (Table 6, RPM cleared + FRR-committed — offered
#   equals cleared; includes the DR Accredited-UCAP factor) against the RTO
#   Reliability Requirement of 146,105 MW UCAP (p.3). Because this registry
#   nets the gross peak BEFORE the FPR multiplication, dividing DR by the
#   published UCAP requirement (= peak × FPR) — not by the ICAP peak — makes
#   the netted credit reproduce PJM's supply-side counting exactly under the
#   published-FPR path: requirement = peak×FPR − f×peak×FPR = peak×FPR −
#   DR×(peak/peak_PJM). Dividing by the ICAP forecast peak (159,329 MW →
#   3.64%) would silently scale DR by FPR ≈ 0.917, an 8% distortion with no
#   basis in PJM's construct. Price Responsive Demand (105.5 MW UCAP
#   2026/27) is EXCLUDED — PJM nets PRD from the Reliability Requirement
#   through a separate construct, and omitting it is conservative. Vintage
#   anchored to the 2026/2027 BRA to match the model's other PJM adequacy
#   anchors (THERMAL_ELCC_CLASS_RATING_BY_ISO, the 2026/27 FPR); the
#   2027/2028 BRA (posted 2025-12-17) has DR 7,641 MW UCAP on a 152,400 MW
#   requirement (5.0%) after PJM moved DR to all-hours availability — refresh
#   on a vintage re-anchor (a source-data change, rule 23), never a residual.
ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO: dict[str, float] = {
    "ERCOT": 0.058,
    # 5,795 MW UCAP DR ÷ 146,105 MW UCAP RTO Reliability Requirement = 3.97%
    # (2026/2027 BRA Report Table 6 / p.3 — reconciliation documented above).
    "PJM": 5_795.0 / 146_105.0,
    # MISO (capx S-123 lane S-3a, 2026-08-30 — the LMR reconciliation named by
    # FINDING-capx-d2b-i7-ledger-2026-08-25.md §2.2b): MISO does NOT net
    # load-modifying resources from its load forecast — LMRs qualify as ZRCs
    # and clear the Planning Resource Auction as capacity SUPPLY toward the
    # PRMR (the exact PJM situation: DR is a cleared supply product), so the
    # value is a documented reconciliation (rule 14), never a raw fraction of
    # peak. Numerator: Demand Resources CLEARED in the PY 2025/26 PRA, Summer
    # 2025 season = 9,004.4 MW ZRC (offered equals cleared) — PY 2025/26 PRA
    # Results Posting (05/29/2025, corrections), p.22 "Summer Supply Offered
    # and Cleared Comparison Trend", category "Demand Resources".
    # Denominator: the System Summer INITIAL PRMR = 135,213.4 MW SAC (same
    # posting, p.18 zonal-results System column) — the pre-auction
    # requirement, peak_forecast × (1 + PRM_UCAP), the exact analogue of the
    # PJM entry's pre-auction RTO Reliability Requirement. Because this
    # registry nets the gross peak BEFORE the (1 + PRM) × ratio
    # multiplication, dividing by the published requirement (not the ICAP
    # peak) makes the netted credit reproduce MISO's supply-side counting:
    # netted MW = f × peak × 1.079 = 9,004.4 × (model peak × 1.079 /
    # 135,213.4) — exactly the cleared DR when the model's peak matches
    # MISO's forecast. The other two LMR-side categories are EXCLUDED,
    # conservatively (the PJM PRD-exclusion precedent — omitting
    # under-credits, never overstates): Behind-the-Meter Generation (Summer
    # cleared 4,282.8 MW ZRC) because an unmeasurable share of registered
    # BTMG operates at peak in the normal course and is then already embedded
    # in the model's EIA-930 metered demand path, so netting the full ZRC
    # would risk a double count; Energy Efficiency (27.6 MW) because realized
    # EE is embedded in metered demand by construction (and is immaterial).
    # Routed refinement: an operating-mode split of MISO's registered BTMG
    # fleet would license the BTMG share — a published-source intake, never a
    # residual fit. Rule 13: DR participation is a recurring seasonal market
    # product that responds to conditions (Summer cleared: 7,694.6 in 2023 →
    # 8,109.4 in 2024 → 9,004.4 in 2025, same table). Vintage = PY 2025-26,
    # the MISO anchor vintage (see the external-tie and PRM entries); refresh
    # together on a PY 2026-27 re-anchor (rule 23).
    "MISO": 9_004.4 / 135_213.4,
    # NEISO (FF-2B, 2026-07-19): ISO-NE's Forward Capacity Market clears Demand
    # Resources — energy efficiency, load management, and distributed generation
    # — as capacity SUPPLY that holds a Capacity Supply Obligation against the
    # Net ICR, exactly the PJM situation (DR is a cleared supply product, not a
    # load-forecast netting), so — as for PJM — the value is a documented
    # reconciliation (rule 14), never a raw fraction of peak. Vintage = the
    # ARA-3 restatement of CCP 2026/2027 (capx-S4b re-vintage 2026-08-30,
    # rule 23 on the Nov 21 2025 ARA ICR filing; supersedes the FCA-17 initial
    # clearing, 2,940 MW / 30,305 MW): the demand-capacity-resource CSO total
    # INCLUDING ARA 3 results, 2,639.682 MW summer (2026 CELT Report, sheet
    # 4.1 "Summary of CSOs", ISO New England Total DCR Total — the same-cycle
    # companion of the ARA-3 Net ICR: requirement-for-the-auction paired with
    # obligations-from-the-auction, the exact FCA-17 pairing discipline at the
    # newer vintage; committed extract data/raw/capacity-market/icr-ara/neiso/).
    # Divided by the ARA-3 Net ICR (30,050 MW — the quantity these resources
    # clear against, NOT the ICAP peak), so under the Net-ICR requirement path
    # the netted credit reproduces ISO-NE's own supply-side counting:
    # requirement = peak × (1 − f) × (1 + PRM_NetICR) =
    # (peak / CELT_peak) × (Net_ICR − DR) when peak = CELT_peak. Recurring FCM
    # product that regenerates each delivery year and scales with enrolment
    # (rule 13). Refresh on a vintage re-anchor or a newer same-cycle
    # publication (source-data change, rule 23), never a residual.
    "NEISO": 2_639.682 / 30_050.0,
}

# Demand Resource capacity COUNTED AS SUPPLY in the ISO's own adequacy
# construction, in accredited MW per delivery year — the supply-side
# alternative to the peak-netting form above (capx D48, 2026-09-04,
# executing FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md §2.3 item 2).
# Consumed ONLY under the default-OFF ``ScenarioConfig.
# pjm_demand_response_supply`` gate (rule 28 row ``pjm_demand_response_supply``)
# by :func:`market_sim.model.capacity_evolution.retirements.
# resolve_demand_response_supply_mw`: an in-table delivery year ADDS the
# published MW to the accredited-supply ledger (``accredited_firm_capacity_mw``
# — hence the CR-1 reserve position, the reliability floor and the backstop,
# one ledger, rule 19) and the gross peak is NOT netted
# (ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO is bypassed for that ISO-year), so
# the position is stated on the auction's own RAW convention — DR in the
# cleared quantity, the Reliability Requirement un-netted — which is exactly
# the x-convention of PJM's VRR curve (Manual 18 §3.4: UCAP % of the
# Reliability Requirement). Off, every solve is byte-identical to the netting.
#
# * PJM (RPM BRA, UCAP): the OFFERED Demand Resource quantity per delivery
#   year, 2020/21–2027/28 — PJM's own RTO trend table (2027/2028 BRA Report,
#   Dec 17 2025, Table 5 "Generation, DR and EE Resources offered and cleared
#   in the RTO translated into UCAP"), digitized from and reconciled
#   byte-for-byte against the committed rows
#   data/raw/capacity-market/auction-supply/pjm/pjm.csv (metric ``offered``,
#   category ``demand_resources``; every row cross-checked to its own
#   delivery year's BRA report — see that file's README) by
#   tests/unit/model/test_capacity.py. OFFERED, not cleared, because the
#   model's position is a CENSUS position — the whole installed fleet
#   against the requirement, whether or not a unit clears — and the market's
#   census analogue for DR is the qualified DR that offers; the CLEARED rows
#   (committed alongside) are the auction's outcome, a validation observable,
#   never an input (rule 13). RPM-only: DR nominated in FRR plans is not in
#   the series (2026/27: +264.4 MW would be), a conservative under-credit
#   (the PRD-exclusion precedent). Rule 13 forward story: DR participation is
#   a recurring market product that regenerates every auction and responds
#   to conditions (11,887 → 6,085 MW over 2021/22 → 2025/26 as the annual
#   Capacity Performance requirement tightened); strictly beyond the last
#   published delivery year the resolver HOLDS-LAST (card C-A 2026-08-25) as
#   the last published DR-to-Reliability-Requirement RATIO × the model's
#   gross requirement (DEMAND_RESPONSE_SUPPLY_HOLD_LAST_RATIO_BY_ISO — a ratio,
#   the same construction the netting fraction above already uses, so the
#   held quantity scales with load). Pre-table years fall through to the
#   netting. Refresh on the next BRA report (rule 23), never on a residual.
DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO: dict[str, dict[str, float]] = {
    "PJM": {
        "2020/2021": 9_846.7,
        "2021/2022": 11_886.8,
        "2022/2023": 10_513.0,
        "2023/2024": 10_116.7,
        "2024/2025": 10_146.4,
        "2025/2026": 6_084.8,  # Table 8 annual 5,962.5 + 122.3 summer matched
        "2026/2027": 5_530.6,
        "2027/2028": 7_298.6,
    },
}

# Hold-last object for delivery years strictly beyond the last published DR
# supply row (card C-A convention; the NET_ICR_HOLD_LAST_RATIO_BY_ISO
# precedent): the last delivery year's published offered DR over its
# published RTO Reliability Requirement — 2027/2028: 7,298.6 MW UCAP DR
# (above) over the 152,400 MW UCAP Reliability Requirement (2027/2028 BRA
# Report, Dec 17 2025, "Reliability Requirement increase from 146,105 MW to
# 152,400 MW (UCAP)"; the same operand the ADEQUACY_DEMAND_RESPONSE_FRACTION
# _BY_ISO["PJM"] citation block records for the 2027/28 re-anchor). Applied
# to the model's own gross (un-netted) requirement so the held DR scales
# with load. Kept as an explicit expression so both published MW stay
# traceable (rule 5). Supersedes itself when a later delivery year's row
# lands above (rule 23).
DEMAND_RESPONSE_SUPPLY_HOLD_LAST_RATIO_BY_ISO: dict[str, float] = {
    "PJM": 7_298.6 / 152_400.0,
}

# Internal-supply accounting ratio — the measured wedge between the model's
# census-accreditation ledger and the market's own counted supply, applied to
# every INTERNAL contribution of the adequacy accounting (the whole ledger
# except the external-tie credit) wherever firm capacity is summed toward the
# adequacy requirement: the CR-1 reserve position, the retirement reliability
# floor (aggregate test AND its per-unit retention increments), and the
# reserve-margin build backstop's crediting of a new unit. ISOs absent here
# carry the neutral 1.0 (their ledger basis is unchanged, byte-identical).
#
# * MISO (capx D31, 2026-09-02 — executing D28 §6.1's position audit): the
#   model's MISO ledger counts the whole census fleet at 1 − EFORd plus the
#   class-credit pools, but MISO's real adequacy supply is the offered
#   Seasonal Accredited Capacity of PRA-participating resources — SAC
#   accreditation (Schedule 53 availability-based, not 1 − EFORd) times
#   participation. Category-by-category against the PRA's own accounting
#   (data/raw/capacity-market/auction-supply/miso/miso.csv): the External
#   Resources category is matched exactly (ADEQUACY_EXTERNAL_TIE_FIRM_MW =
#   the cleared external ZRC), Demand Resources are netted on the
#   requirement side (the registry above), BTMG/EE are excluded (documented
#   conservative S-123 choice), and the remaining INTERNAL GENERATION
#   aggregate over-counts the market's offered accounting by the two clean
#   overlap years' measured ratios: Summer-2023 offered Generation ZRC
#   122,375.6 ÷ the model's 2023 entering internal firm 143,822.1 = 0.85095,
#   and Summer-2024 offered 123,395.6 ÷ 143,749.5 = 0.85845 (model
#   denominators: the committed D27 T1-H entering-fleet ledgers
#   [results/hindcast/miso-2021-2025-realized-t1h-d27 evolution_2023/2024
#   fleet_by_fuel_before at 1−EFORd, + wind 26,050×0.166 + solar 2,048×0.3875
#   + hydro 2,464.9/2,371.5×0.62 + storage 1,963.7] — the model's own
#   documented bases, computed before any exit decision so no model outcome
#   enters). Identified on the SUMMER season (the annual peak the
#   requirement anchors to; the one-position architecture holds one annual
#   ratio — the per-season refinement is the documented seasonal-
#   accreditation future item). Capacity-weighted two-year mean:
#   (122,375.6 + 123,395.6) / (143,822.1 + 143,749.5) = 0.85465.
#   Rule 13: the offered-supply accounting is the market's recurring census
#   analogue (stable ±0.4% across the two identification years while
#   clearing varied), regenerates every auction cycle, and enters
#   formulaically (evolved census × ratio) — the CLEARED quantities are
#   never targeted. Rule 14: a reconciled bridge between a published record
#   and the model's own census basis (the PRA publishes no registered-ICAP
#   companion to decompose accreditation from participation; the per-class
#   SAC intake is the routed refinement). Refresh on a PY re-anchor or a
#   fleet-vintage change (rule 23), never on a residual. NOT applied to
#   per-unit capacity REVENUE (a unit that participates earns its own
#   accredited revenue; the aggregate wedge includes non-participants), so
#   thermal_accreditation_fraction is deliberately untouched — the ledger
#   and the unit payment diverge by exactly this documented factor.
ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO: dict[str, float] = {
    "MISO": (122_375.6 + 123_395.6) / (143_822.1 + 143_749.5),
}

# The SAME ratio re-identified on the fleet in the posture the run applies
# (capx D51, 2026-09-04, executing FINDING-capx-d49-2026-09-04.md §2.6 —
# rule 23 [R-FROZEN-DERIVE]: a re-derivation triggered by a POSTURE change of
# the fleet the ratio was identified on, never by a residual). Resolved ONLY
# under the default-off gate ``ScenarioConfig.adequacy_accounting_ratio_dated_
# net`` (retirements.resolve_internal_supply_accounting_ratio); unarmed, the
# D31 registry above keeps resolving byte-identically. ISOs absent here fall
# through to the D31 registry even when armed (rule 25 [R-ISO-SCOPE]).
#
# * MISO: D31's denominators are the committed D27 T1-H entering-fleet
#   ledgers — a census that still carried the 2021–2023 real exits (St Clair,
#   Schahfer, Meramec, Edwards, Trenton Channel, Dolet Hills, River Rouge,
#   Gallagher …) the PRA had already dropped, so the 0.8546 absorbed them.
#   Since owner ruling Q30 / capx D44 (fossil_announced_exits_enabled default
#   ON, 2026-09-03) the fossil-dates channel removes those same plants
#   explicitly at step 1b AND the ratio still applies — the same MW netted
#   TWICE, dropping the consumed position 5.8 / 6.9 pts short of the market's
#   own (D49 §2.4). ONE term moved: the same PRA Summer offered Generation
#   ZRC numerators over the same D31 denominators NET of the accredited dated
#   exits, where the dated exits are the per-fuel D27 − D46 (dates-ON)
#   ``fleet_by_fuel_before`` difference at 1 − EFORd — measured on the
#   committed ledgers (results/hindcast/miso-2021-2025-realized-t1h-{d27,d46}),
#   never retyped: 4,508.5 MW (2023 entering; the 893.6 MW pre-start backlog +
#   the 2022 bridge's 2,108.6 MW fossil drops + 1,896.3 MW derates) and
#   7,977.6 MW (2024 entering; + 2023's 2,162.3 drops + 1,602.4 derates).
#   Per-year 122,375.6 / 139,313.6 = 0.87842 and 123,395.6 / 135,771.9 =
#   0.90884; capacity-weighted two-year mean 0.893436 (a 1.04539× scale on
#   the D31 value). Everything else is HELD exactly as D31 identified it: the
#   numerators, the class bases (1 − EFORd; wind 0.166; solar 0.3875; hydro
#   0.62; storage firm), the prior-solved-year pool convention, the Summer
#   season, the two-year mean, the D27 pools (the D33 VRE additions are a
#   model outcome and must not enter, exactly as D31 held) and the unscaled
#   external tie. Derived and reconciled by test from those three committed
#   inputs by scripts/data/derive_miso_adequacy_accounting_ratio.py
#   (tests/curation/test_derive_miso_adequacy_accounting_ratio.py), so the
#   value can never drift from the committed data. Zero free parameters.
#   Rule 14 sign: the position moves UP ~4.5 % of internal supply — on the
#   vertical PY2024 vintage the whole $113.6 → $0/kW-yr cliff for the fleet
#   at once — so the undated cohort returns BELOW the bar into the
#   floor-capped regime; exits do not get easier. Pre-declared
#   docs/handoffs/PREDECL-capx-d51-2026-09-04.md; measured on the suffixed
#   A/B `miso-t1h-d51-ratio` (FINDING-capx-d51-2026-09-04.md). The owner arms
#   or declines; nothing here changes an unarmed solve.
ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO: dict[str, float] = {
    "MISO": (122_375.6 + 123_395.6) / (139_313.6 + 135_771.9),
}

# Firm import capacity counted by the ISO's own resource-adequacy ledger,
# credited on the supply side of
# :func:`market_sim.model.capacity.accredited_firm_capacity_mw` (via
# :func:`market_sim.model.capacity._firm_import_mw`) exactly where each ISO's
# own ledger counts it. Two provenance cases share this one registry (rule 19,
# one mechanism per phenomenon — "firm import the adequacy ledger counts"):
#   (a) ISOs the model has NO import node for (ERCOT, PJM, NYISO, MISO) — the
#       firm tie is otherwise entirely absent from the persistent fleet, so this
#       is its only adequacy entry (NYISO's and MISO's dispatch-side imports
#       flow through the interchange model — for MISO the Manitoba firm-hydro
#       block, never fleet units — see their bullets below).
#   (b) ISOs whose import node DOES live in the dispatch topology (CAISO's
#       WECC_import, NEISO's HQ_import — FF-2B, 2026-07-19). This adequacy
#       credit does NOT double-count the dispatch node: the accredited ledger
#       is a static firm-capacity accounting built from the persistent
#       ``fleet``, which never contains the import pseudo-generators (they live
#       only in the transient dispatch fleet), so the credit is purely additive
#       to the fleet's firm MW, never derived from dispatch flow.
# ISOs absent here add nothing (byte-identical).
# * ERCOT: 817 MW asynchronous (DC) ties, "based on average net import
#   contribution during the EEA events: summer 2023 and winter 2020/2021 EEA
#   events" — December 2025 CDR, Seasonal Summary (non-synchronous ties row).
# * PJM (W2-D, closes gap G10 / W1-B B1): 1,281.7 MW UCAP of capacity
#   imports cleared in the 2026/2027 BRA (BRA Report, posted 2025-07-22,
#   Table 7 "Capacity Imports (UCAP) Offered and Cleared by Region": NORTH
#   250.8 + WEST 1 0.0 + WEST 2 568.0 + SOUTH 1 226.2 + SOUTH 2 236.7).
#   This is the CIL firm-import treatment: external generation may count
#   toward PJM's requirement only inside the Capacity Import Limit framework
#   (firm transmission + the enhanced pseudo-tie requirements of FERC Order
#   ER17-1138 / prior-CIL-exception rows) — the CLEARED import UCAP is what
#   PJM's ledger actually counted for the delivery year, whereas the CIL
#   itself is a study limit and would overstate. Rule 13: BRA import
#   participation is a recurring market product that regenerates each
#   delivery year and responds to conditions (2027/2028 BRA: 1,005.9 MW
#   UCAP), not an outcome pin. Vintage anchored to the 2026/2027 BRA
#   alongside the DR fraction above.
# * CAISO (FF-2B, 2026-07-19): 3,371 MW of firm RA import contracts. CAISO's
#   CPUC resource-adequacy program credits imports toward the system RA
#   requirement as capacity-backed, must-offer supply (self-scheduled or bid at
#   or below $0/MWh during the availability-assessment hours, CPUC D.20-06-028).
#   The model's WECC_import node hosts these in dispatch but the accredited
#   ledger (fleet-based) omits them — case (b) above. Value = the measured
#   average system RA "Imports" capacity, CAISO DMM Annual Report on Market
#   Issues & Performance, 2024 report (Aug 2025) Table 15.6 = 3,371 MW (excl.
#   "Imports-MSS", internal metered subsystems); this is exactly the model's own
#   firm CAISO import tranches (interchange_config.IMPORT_TRANCHES["CAISO"]:
#   PNW_hydro_base 1,566 + DSW_solar_PV 1,805 = 3,371), so dispatch and adequacy
#   read the same firm-import quantity. Latest measured year carried forward as
#   the forward story (RA import contracting is a persistent market structure —
#   rule 13). The 2025 DMM report published 2026-06-26; its Table 16.7
#   "Imports" 1,710 MW is on a CHANGED analysis-hour basis (spring-heavy
#   AAH, total RA 46,169 vs 52,646 MW) and is NOT adopted — rule 14
#   misalignment, adjudicated caiso-252 (2026-09-05); full note at
#   interchange/spec.py IMPORT_TRANCHES_BY_YEAR. NOT the Maximum Import
#   Capability (16,148 MW) — the MIC is a deliverability LIMIT, not the RA
#   capacity actually contracted, and crediting it would overstate.
# * NEISO (FF-2B, 2026-07-19; ARA-3 re-vintage capx-S4b, 2026-08-30): the net
#   import Capacity Supply Obligation for CCP 2026/2027 INCLUDING ARA 3
#   results — 409.31 MW (2026 CELT Report, sheet 4.1 "Summary of CSOs",
#   ISO NEW ENGLAND Net Import Total: New Brunswick 177.0 + New York AC Ties
#   232.31; committed extract data/raw/capacity-market/icr-ara/neiso/). It
#   moves with the requirement re-vintage because it is the same-cycle
#   restatement of the FCA-17 cleared-import credit it supersedes ("567 MW of
#   imports from New York, Québec, and New Brunswick", FCA 17 initial-results
#   press release, 2023-03-10) — holding it at the FCA-17 print against an
#   ARA-3 requirement would mix vintages inside one adequacy comparison.
#   These are Import Capacity Resources that count as SUPPLY toward the Net
#   ICR; the HQICC tie benefit (1,009 MW at ARA 3) is already netted from the
#   requirement (Net ICR = ICR − HQICC, see the NEISO PLANNING_RESERVE_MARGIN
#   entry) and is NOT double-counted here. The model's HQ_import node hosts
#   imports in dispatch but the accredited ledger omits the cleared import
#   CSOs — case (b) above. Recurring FCM product (rule 13).
# * NYISO (capx D-2 external-capacity intake, 2026-08-25, closing the FC-1 I7
#   base-year gap of FINDING-capx-d2-adequacy-nyiso-2026-08-24.md §6):
#   2,749.9 MW UCAP = 3,168.5 MW ICAP × (1 − 0.1321). The 3,168.5 MW is
#   NYISO's own published external capacity: 2026 Gold Book (Load & Capacity
#   Data Report, April 2026 — data/raw/NYISO/2026-Gold-Book-Public.pdf,
#   sha256 in that directory's SHA256SUMS.txt), Table V-1 "Summary of
#   Projected Net Capacity Purchases from External Control Areas", Summer
#   2026 total (ISO-NE 67.3 + HQ 2,443.0 + IESO 3.3 + PJM 654.9), NET of
#   capacity exports. These purchases are the UDR / External-CRIS / ETCNL /
#   FCFSR-backed ICAP-market products (table note 2) that NYISO's own NYCA
#   Capacity Schedule counts toward Total Resource Capability (Table V-2a:
#   37,697.7 + 3,168.5 = 40,866.2 MW, Summer 2026). Basis: the Gold Book
#   schedule states seasonal capability (ICAP), while the model's NYISO
#   requirement is UCAP — peak × (1 + IRM) × (1 − 0.1321), see
#   PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO — so the entry converts
#   with the SAME published NYCA ICAP→UCAP translation factor the requirement
#   side applies (NYSRC 2025-2026 IRM Study Technical Appendices, App. D
#   Table D.2): one basis across both sides of the adequacy comparison
#   (rule 19), the same documented rule-14 reconciliation pattern as the PJM
#   DR entry. Conservative direction: NYISO's actual ledger derates each
#   external resource by its OWN EFORd / UDR line availability (ICAP Manual
#   §4.5), typically below the NYCA-wide 13.21 % fleet derate applied here,
#   so this construction can only under-credit, never manufacture firm MW.
#   Corroboration: NYISO 2025 SOM (Potomac Economics, May 2026 — same
#   directory, sha-recorded) Figure A-97 shows net capacity imports
#   transacting in UCAP at O(1,500–2,500) MW monthly, May 2023–Apr 2026.
#   NYISO's model topology has NO import node (five internal zones only);
#   dispatch-side imports enter through the interchange model
#   (model/interchange/nyiso.py), never the persistent fleet, so the credit
#   is additive with no double-count — the ERCOT/PJM provenance case (a).
#   It is deliberately NOT the model's 900 MW HQ firm dispatch floor (an
#   inherited ladder constant, not a published RA accreditation — see
#   scripts/data/derive_nyiso_import_tranches.py) and NOT the 4,350 MW
#   Simultaneous Import Limit (a deliverability LIMIT — the exact error the
#   CAISO entry rejects for the MIC). Rule 13: Gold Book capacity purchases
#   are re-published annually and respond to conditions (Table V-1: 3,168.5
#   in 2026 → 3,149.3 in 2027 → 3,299.9 in 2028) — a recurring ICAP-market
#   product, never an outcome pin.
# * MISO (capx S-123 lane S-2, 2026-08-30, the second instance of the NYISO
#   external-capacity defect — FINDING-capx-d2b-i7-ledger-2026-08-25.md
#   §2.2a/§6): 3,505.9 MW ZRC = the External Resources CLEARED in the
#   PY 2025/26 Planning Resource Auction, Summer 2025 season. Source: MISO
#   PY 2025/26 PRA Results Posting (05/29/2025, corrections —
#   https://cdn.misoenergy.org/2025%20PRA%20Results%20Posting%2020250529_Corrections694160.pdf),
#   p.22 "Summer Supply Offered and Cleared Comparison Trend", Planning
#   Resource category "External Resources", Cleared (ZRC) Summer 2025 —
#   offered equals cleared (3,505.9 both). This is the categorical row of
#   MISO's own supply accounting: the five category rows (Generation /
#   External Resources / BTM Generation / Demand Resources / Energy
#   Efficiency) sum to the System committed total 137,559.3 MW, i.e. exactly
#   what MISO's ledger counted toward the PRMR. Basis: one ZRC = 1 MW of
#   Seasonal Accredited Capacity (SAC), MISO's availability-based
#   UCAP-equivalent unit — the SAME basis as the requirement side's
#   peak × (1 + PRM_UCAP 7.9%) construction from the same planning year's
#   LOLE study (see PLANNING_RESERVE_MARGIN_BY_ISO), so no conversion factor
#   is needed: the NYISO entry's × 0.8679 one-basis translation is the
#   identity here (rule 19, one basis across both sides). Season = Summer,
#   matching the summer-peak adequacy ledger (the same season discipline as
#   the MISO DLOL hydro credit below). Vintage = PY 2025-26, the anchor
#   vintage of EVERY other MISO adequacy input (PRM pair, DLOL hydro credit,
#   RBDC/CONE) — deliberately NOT the PY 2026-27 posting, which would remake
#   the mixed-vintage composite the S-1 re-vintage just removed; refresh all
#   four operands together on a PY 2026-27 re-anchor (rule 23, source-data
#   change). It is deliberately NOT the model's 1,400 MW Manitoba firm-hydro
#   dispatch constant (an inherited ladder spec constant —
#   MISO_FIRM_IMPORT_DEFAULT_ISOS / interchange spec — not a published RA
#   accreditation), NOT the zonal tables' ERZ-column committed 1,580.1 MW
#   (only the portion clearing in the External Resource Zones proper; the
#   category row is MISO's full external-resource supply count), and NOT any
#   CIL (a deliverability LIMIT — the CAISO-entry discipline). Rule 13: the
#   PRA re-clears every planning year and the quantity responds to conditions
#   (Summer cleared external ZRC: 4,072.5 in 2023 → 4,309.8 in 2024 → 3,505.9
#   in 2025, same table). Dispatch-side MISO imports flow through the
#   interchange model, never the persistent fleet — provenance case (a), no
#   double-count.
ADEQUACY_EXTERNAL_TIE_FIRM_MW: dict[str, float] = {
    "ERCOT": 817.0,
    "PJM": 1_281.7,  # 2026/2027 BRA Report Table 7 (cleared import UCAP)
    "CAISO": 3_371.0,  # DMM 2024 Table 15.6 RA Imports (= model firm import tranches)
    "NEISO": 409.31,  # CCP 2026/27 net import CSO incl. ARA 3 (2026 CELT 4.1)
    # 2026 Gold Book Table V-1 Summer-2026 external purchases (ICAP) × the
    # published NYCA ICAP→UCAP translation factor — same factor as the
    # requirement side (one basis, rule 19); see the citation block above.
    "NYISO": 3_168.5 * (1.0 - 0.1321),
    # PY 2025/26 PRA Summer cleared External Resources (ZRC = SAC MW, already
    # the requirement side's UCAP-equivalent basis); see the citation block.
    "MISO": 3_505.9,
    # SPP (registered 2026-09-06, lane SPP-20): 0.0 — the ``.get(iso, 0.0)``
    # fallback made EXPLICIT rather than left implicit. No published SPP
    # resource-adequacy accreditation of firm external ties has been
    # transcribed into the tree (SPP-12 swept the Planning Criteria, ASOMs
    # and Protocols and landed none; the MMU's seam figures in SOM 2025 §2.8
    # are tie RATINGS — ">6,000 MW SPP<->MISO", ">5,000 MW AECI", "720 MW
    # ERCOT DC" — not RA-counted firm capacity, so entering them here would
    # count deliverability LIMITS as supply, the CAISO-entry discipline this
    # block already refuses). The demand-response row the MMU does publish
    # (793 / 970 / 1,016 MW, Fig. 2-12) is a different operand
    # (ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO) and is routed to the
    # forecast lane. A cited value replaces this zero on intake.
    "SPP": 0.0,
    # NWPP (registered 2026-09-14, lane NWPP-20): no published RA-counted firm
    # tie — WRAP's Forward Showing is non-binding in every scored year (first
    # binding season Winter 2027-28, WPP BPM 109 p. 4) and the WECC path
    # ratings on the CAISO / Canada / Southwest seams are transfer limits,
    # not supply. The .get fallback made explicit, exactly as SPP's.
    "NWPP": 0.0,
    # SOCO (registered 2026-09-14, lane SOCO-20): 0.0, EXPLICIT AND CITED, for
    # a reason the SPP row does not have. Southern's 2024 Reserve Margin Study
    # DOES publish external transfer capabilities into the System (Tables
    # I.1 / I.2 "Avg TC", e.g. MISO-South 1,791 / 2,374 MW, TVA 480 / 478,
    # Duke 34 / 407; and a Capacity Benefit Margin of 300 + 250 + 250 + 100 =
    # 900 MW across MISO-South / TVA / FPL / Duke) — but the 26 % Target
    # Reserve Margin it recommends is derived WITH that market assistance
    # already modelled ("calibration benchmarked modeled energy with actual,
    # eight-year average, non-PPA market transactions into and out of the
    # Southern Company region", SOCO-12 README §4c). The TRM is therefore net
    # of the ties, and counting them here as firm supply against it would
    # count them twice (rule 19). They are the seam input for INTERFACE_
    # NEIGHBORS["SOCO"] (card S4), not RA supply. A cited RA-counted firm-tie
    # figure replaces this zero on intake.
    "SOCO": 0.0,
}

# Conventional-hydro accreditation for the same adequacy ledger, per ISO — the
# firm fraction of the modelled hydro fleet's nameplate each ISO's OWN published
# resource-adequacy construction counts toward its requirement (FFR-1C, closing
# audit finding FR-3 / gap-register R5c). Consumed by
# :func:`market_sim.model.capacity_evolution.adequacy._hydro_firm_mw`, which
# pairs it with the model's own hydro nameplate (the same EIA-860/EIA-923 plant
# population :func:`market_sim.data.hydro.build_hydro_fleet` puts in the LP) —
# hydro is an energy-budget resource that never enters the persistent ``fleet``,
# so before FFR-1C it contributed 0 MW to the accredited ledger for EVERY ISO
# while being fully dispatched (docs/handoffs/ff-2b-adequacy-basis-2026-07.md
# §2.2/§2.3/§4).
#
# **Every value below is an ISO-published accreditation factor, never a value
# tuned to clear the I7 adequacy invariant (rules 5/13/21).** Each class-rating
# ISO's published construction splits hydro into a controllable/reservoir class
# and a limited-control / run-of-river class, at materially different factors
# (NEISO is the exception: ISO-NE publishes no class rating at all, so its
# entry aggregates the ISO's own per-resource qualified-capability record —
# see its bullet). The
# model carries NO per-plant RA class assignment for its hydro fleet (the
# ORNL-EHA ``hydro-plant-modes`` classifier behind ``hydro_ror_split`` is a
# curated CLEAN partition, absent from a default raw-path run and reviewed only
# for some ISOs), so this registry carries **one credit per ISO: the LOWER —
# limited-control / run-of-river / non-dispatchable — published class factor**.
# That choice is deliberate and conservative in the only direction that matters
# for an adequacy ledger: it can never manufacture firm MW the ISO would not
# count, so any I7 movement is a floor on the published credit, not a fit. The
# per-plant class split (which would raise CAISO/NYISO/MISO toward their
# reservoir factors) is a routed refinement — it needs a published plant->CARC /
# plant->class intake, not a parameter (see the FFR-1C findings doc).
#
# * CAISO — 0.7041. CPUC/CAISO Final Net Qualifying Capacity Report for
#   Compliance Year 2025 ("2025 Tech Factors" tab, "Non-dispatchable Hydro":
#   monthly QC factors as a fraction of Pmax, the 3-year 2021-2023 average the
#   report itself publishes). The CPUC's adopted QC methodology counts
#   DISPATCHABLE hydro at its most recent maximum-capability (Pmax) test = 1.00
#   and NON-DISPATCHABLE hydro at historical production (CPUC 2023 Resource
#   Adequacy Report §5 "Net Qualifying Capacity"; adopted QC Methodology Manual,
#   D.10-06-036 App. B §§7,10). 0.7041 is the SEPTEMBER factor — the minimum
#   over CAISO's Jul/Aug/Sep peak-risk months (Jul 0.7252, Aug 0.7084, Sep
#   0.7041; the model's own CAISO peak lands in Aug 2023/2025 and Sep 2024), so
#   the credit holds in whichever of the three the annual peak falls. Rule 13:
#   the factor is re-published every compliance year off a rolling 3-year
#   production window and responds to water conditions.
#   Source: https://www.caiso.com/documents/final-net-qualifying-capacity-report-for-compliance-year-2025.xlsx
# * NYISO — 0.3844. NYISO 2025-2026 **Final Capacity Accreditation Factors**
#   (ICAPWG/MIWG, 2025-02-04), CARC "Limited Control Run of River", Rest-of-State
#   column = 38.44% (GHI 41.44%; the class does not exist in NYC/LI). NYISO's
#   controllable classes accredit far higher in the SAME table — "Large Hydro"
#   100.00% and "Large Hydro with partial Pump Storage" 100.00% — so 0.3844 is
#   the conservative end of NYISO's own published hydro accreditation, not a
#   blended or fitted value. CAFs are re-derived annually from the IRM/LCR base
#   case (rule 13).
#   Source: https://www.nyiso.com/documents/20142/49572424/2025-2026%20Final%20CAF%20and%20PLW_%202.4.2025_Final.pdf
# * MISO — 0.62. MISO PY 2025-2026 **Indicative Resource Class-level UCAP
#   (DLOL)**, expressed as a percentage of ICAP, Summer column: "Run-of-River
#   Hydro" 62% (Fall 52%, Winter 58%). The same table publishes "Reservoir
#   Hydro" 89% Summer. MISO's summer column is the right season for a
#   summer-peak adequacy ledger. (Single-document arithmetic for the fleet blend
#   is available and recorded for the routed refinement: the companion
#   Indicative PRMR table gives Summer class UCAP of 1,846 MW reservoir /
#   721 MW run-of-river, implying ICAP 2,074 / 1,163 MW and an MW-weighted fleet
#   credit of 0.793 — NOT adopted here because the model cannot assign its own
#   plants to the two classes.) DLOL accreditation is re-run every planning year
#   (rule 13).
#   Source: https://cdn.misoenergy.org/Indicative%20DLOL%20Results%20PY%202025-2026667100.pdf
# * PJM — 0.38. PJM 2026/2027 BRA official/final ELCC class ratings, class
#   "Hydro Intermittent" = 38% at 519 MW installed — the committed row in
#   data/raw/capacity-market/elcc/pjm/pjm.csv (the same intake
#   RENEWABLE_ELCC_CURVES_BY_ISO["PJM"] and THERMAL_ELCC_CLASS_RATING_BY_ISO
#   read, and the same 2026/27 vintage they are anchored to). PJM's controllable
#   class "Hydro with Non-Pumped Storage" rated 96% in the predecessor Dec-2021
#   ELCC report; the 2027/28 final vintage moves Hydro Intermittent to 39%.
# * NEISO — 1,396.472 / 1,899.5 = 0.7352 (capx-S4, 2026-08-30; closes the
#   FFR-1C open item). ISO-NE publishes NO hydro class rating — the FCM
#   qualifies hydro PER-RESOURCE (summer Qualified Capacity = the 5-yr median
#   of the resource's summer Seasonal Claimed Capability ratings, Market Rule 1
#   §III.13.1.2.2.1.1; intermittent resources at a median-reliability-hours
#   output construction) — so the class factor is the AGGREGATE of ISO-NE's own
#   per-resource summer claimed capability over its ACTIVE conventional-hydro
#   fleet, divided by the model's own accreditation basis. Numerator: ISO-NE
#   SCC Monthly Report, August 2026 vintage (published 2026-08-06), sheet
#   SCC_Report_Current, ACTIVE assets of hydraulic-turbine unit types
#   HDP/HDR/HW/HL (conventional pondage/run-of-river/tidal; type PS reversible
#   = pumped storage EXCLUDED, a storage resource in this model), summer SCC
#   column: 244 assets, 1,396.472 MW. The 200 intermittent run-of-river assets
#   enter at ISO-NE's own "Median Reliability Hours Calculation" values, so the
#   tariff's intermittent-hydro construction is applied by ISO-NE itself, not
#   approximated here. Denominator: the model's NEISO hydro accreditation basis
#   modelled_hydro_nameplate_mw = 1,899.5 MW (2024 final EIA-923 census) — the
#   SAME population and MW total this factor multiplies in _hydro_firm_mw, so
#   the credited ledger term equals ISO-NE's own published aggregate capability
#   (1,396.5 MW) by construction, and model plants absent from the FCM record
#   enter at zero (conservative floor, the registry-wide discipline).
#   Season: SUMMER, matching the Net-ICR/summer-50/50-peak requirement basis
#   every other NEISO adequacy anchor uses. Vintage-stable: the same
#   aggregation on the August 2024 / August 2025 reports gives 0.7389 / 0.7063.
#   Rule 13: SCC is re-published monthly per-resource and responds to fleet and
#   hydrology changes; re-derive on a newer vintage (rule 23), never a residual.
#   Population bound: SCC assets below the ~1 MW EIA census threshold total
#   16.7 MW (0.9% of the numerator) — the only overstatement channel, documented
#   in docs/handoffs/FINDING-capx-s4-neiso-hydro-2026-08-30.md.
#   Source: https://www.iso-ne.com/static-assets/documents/100038/scc_august_2026.xlsx
#   (per-asset extract + provenance: data/raw/capacity-market/scc/neiso/).
# * ERCOT — ABSENT, so it falls back to the generic published class derate
#   :data:`RENEWABLE_CAPACITY_CREDIT`\\ ["hydro"] = 0.50 (the same fallback
#   every uncredited class already takes, rule 25 spirit — never a foreign
#   ISO's factor). ERCOT is energy-only with no accreditation product; open
#   item in the FFR-1C findings doc. Effect is confined to the ledger's
#   reported reserve margin (ERCOT's reliability floor is skipped by market
#   design and its backstop is off).
HYDRO_ACCREDITATION_CREDIT_BY_ISO: dict[str, float] = {
    "CAISO": 0.7041,  # CPUC/CAISO CY2025 NQC tech factor, non-disp. hydro, Sep
    "NYISO": 0.3844,  # NYISO 2025-26 Final CAF, Limited Control Run of River, RoS
    "MISO": 0.62,  # MISO PY2025-26 Indicative DLOL, Run-of-River Hydro, Summer
    "PJM": 0.38,  # PJM 2026/27 BRA final ELCC class rating, Hydro Intermittent
    # ISO-NE Aug-2026 SCC report Σ(summer SCC, ACTIVE conventional hydro) over
    # the model's own accreditation basis (rule 5: explicit expression so both
    # published MW values stay traceable, the PLANNING_RESERVE_MARGIN_BY_ISO
    # ["NEISO"] precedent).
    "NEISO": 1_396.472 / 1_899.5,  # = 0.7352
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
#     ICAP 15.7%, UCAP 7.9%). Since the capx S-123 / S-1 re-vintage
#     (2026-08-30) the PRM entry above is the SAME document's ICAP 15.7%, so
#     the pair composes to the document's own peak × 1.079 UCAP requirement
#     rather than the former mixed-vintage composite.
#   NYISO: 1 - NYCA translation factor = 1 - 0.1321 = 0.8679. NYISO states its
#     NYCA Minimum UCAP Requirement as ICAP requirement x (1 - translation
#     factor), where the translation factor ("Derate Factor") is the qualified
#     fleet's capacity-weighted forced-outage (EFORd) derate, Sigma(UCAP)/
#     Sigma(ICAP) (NYISO ICAP Manual Manual-04 §2.5). The model counts NYISO
#     thermal at UCAP (1 - EFORd, the default supply basis; NYISO is absent from
#     THERMAL_ACCREDITATION_BASIS_BY_ISO), so this ratio pairs the ICAP-stated
#     IRM (24.4%) onto that same UCAP basis — the direct MISO analogue. Value is
#     the most-recently-realized NYCA-wide factor, 2024-2025 capability year,
#     from NYSRC 2025-2026 IRM Study Technical Appendices (Dec 6 2024), Appendix
#     D §D.1.1 Table D.2 "NYCA ICAP to UCAP Translation" (Derate Factor col).
#     Reconciled against the same study's Table D.1: (1 + EC-approved IRM 22.0%)
#     x (1 - 0.1321) - 1 = 5.9% = the published 2024-2025 "NYCA Equivalent UCAP
#     Requirement". Static-proxy (Option B, owner-selected FF-3D 2026-07-18,
#     pairing-adjudication 2026-07-15 §3): NYISO recomputes this factor twice
#     per Capability Year from the then-qualified fleet, so it is intentionally
#     time-varying (rising with wind penetration: 0.083 in 2020-2021 -> 0.132 in
#     2024-2025) — carrying the realized value forward is a lagged snapshot, the
#     weaker rule-13 forward story the adjudication flagged for B vs the
#     recommended lagged-model-derived Option A. Cited to
#     demand-curve/nyiso/nyiso.csv (metric=icap_ucap_translation_factor);
#     reconciled to that CSV by tests/test_capacity.py (R5a basis-consistency).
# ISOs absent here are byte-identical (ratio 1.0, i.e. their registered PRM
# is already on the model's own supply basis — ERCOT's is fixed at the CDR
# seasonal-rating basis by the accreditation audit, not this registry).
PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO: dict[str, float] = {
    "PJM": 0.9170 / 1.191,
    "MISO": 1.079 / 1.157,
    "NYISO": 1.0 - 0.1321,  # 1 - NYCA translation (Derate) factor, CY 2024-2025
}

# Published Forecast Pool Requirement (FPR) per ISO and delivery year — the
# reliability requirement stated on the ISO's OWN UCAP basis as a fraction of
# forecast peak load (R2, accreditation-basis memo 2026-07-12 §4.2). PJM's
# post-CIFP FPR = (1 + IRM) x Reference-Resource Accredited-UCAP factor, so it
# already folds BOTH the reserve margin AND the ICAP->UCAP conversion into one
# published number; the UCAP requirement is simply firm_peak x FPR.
# :func:`market_sim.model.capacity.resolve_adequacy_requirement_mw` PREFERS a
# published FPR for the matching delivery year, HOLDS-LAST beyond the table's
# final entry (owner-signed convention, card C-A 2026-08-25 — the
# `resolve_demand_curve_vintage`/`forward_net_cone_anchor` forward-carry
# precedent; see resolve_forecast_pool_requirement's docstring), and falls
# back to the (1 + PRM) x icap_to_ucap_ratio construction otherwise (so an ISO
# absent here, or a delivery year BEFORE the table's first entry, is
# byte-identical to the pre-R2 behaviour). Devintaging the requirement
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
        # FFR-2C 2026-08-02: published alongside the 2028/2029 net-CONE
        # re-anchor. (1+0.200) x 0.7834 (Pool-Wide Accredited UCAP Factor);
        # both endorsed at the 2026-02-19 MRC meeting. Workbook
        # 'Planning Parameters' sheet, FPR row, RTO column.
        "2028/2029": 0.9401,
        # 2029/2030: NOT YET PUBLISHED (capx S-5 check 2026-08-30; the
        # 2029/30 BRA is scheduled for Dec 2026). Until intake, 2029/30+
        # HOLD-LAST to 0.9401 in resolve_forecast_pool_requirement (card C-A
        # convention). Add the row here on publication (rule 23
        # [R-FROZEN-DERIVE]) — the hold supersedes itself automatically.
    },
}

# Published PRE-REFORM Forecast Pool Requirement per ISO and delivery year —
# the reliability requirement the auction ACTUALLY cleared on, stated as a
# fraction of forecast peak on the pre-reform UCAP design (capx D48,
# 2026-09-04, executing FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md §2.3
# item 1 — the requirement half of the accreditation-design devintage).
# Consumed ONLY under the default-OFF ``ScenarioConfig.
# pjm_accreditation_design_vintage`` gate by :func:`market_sim.model.
# capacity_evolution.retirements.resolve_pre_reform_pool_requirement`, which
# is consulted BEFORE the post-reform table above inside
# ``resolve_adequacy_requirement_mw``; off, every pre-reform delivery year
# keeps the composite fallback byte-identically (the table above deliberately
# starts at the reformed 2025/2026, so these rows are never reached unarmed).
#
# * PJM: FPR = (1 + IRM) × (1 − pool-average EFORd) under the pre-CIFP design
#   (Manual 18 §4.2.1 — the UCAP Reliability Requirement is forecast peak ×
#   FPR, so the published RTO Reliability Requirements 166,355.1 / 163,268.9 /
#   163,166.2 / 164,107.6 MW UCAP divide by these to the forecast peaks). Each
#   value is digitized from the committed demand-curve rows
#   (data/raw/capacity-market/demand-curve/pjm/pjm.csv, metric
#   ``forecast_pool_requirement``, delivery years 2021/2022–2024/2025 — the
#   per-DY Planning Period Parameters workbooks committed beside them) and
#   reconciled against them by tests/unit/model/test_capacity.py — a
#   published market-design input, never a fit target (rules 13/23).
#   Information gate (rule 13, the D42/D44 vintage construction): a delivery
#   year's parameters are posted years before the delivery year begins
#   (2021/22 posted 2018-02-01; 2022/23 2021-02-08; 2023/24 2022-02-28;
#   2024/25 set for the Dec-2022 BRA), so the value screened in model year Y
#   for delivery year Y/Y+1 was on file at every information cutoff the
#   hindcast uses. Pre-2021/22 delivery years have no committed row and fall
#   through to the composite exactly as the post-reform table's pre-table
#   years do; the SAME delivery year is never in both tables (asserted by
#   test), so the two resolvers can never disagree on a year.
FORECAST_POOL_REQUIREMENT_PRE_REFORM_BY_ISO: dict[str, dict[str, float]] = {
    "PJM": {
        "2021/2022": 1.0898,  # PPP posted 2018-02-01, Table 1 (IRM 15.8 %)
        "2022/2023": 1.0868,  # PPP posted 2021-02-08, Table 1 (IRM 14.5 %)
        "2023/2024": 1.0901,  # PPP posted 2022-02-28, Table 1 (IRM 14.8 %)
        "2024/2025": 1.0894,  # PPP workbook, Planning Parameters sheet (IRM 14.7 %)
    },
}

# Published RTO-wide Reliability Requirement, in UCAP MW, keyed by delivery-year
# label "YYYY/YYYY+1" — the ABSOLUTE adequacy requirement of the auction whose
# delivery year the retirement screen prices (capx D67, 2026-09-06, executing
# FINDING-capx-d66-2026-09-06.md §8 card A).
#
# WHY. HEAD reconstructs the requirement as ``model screen peak × FPR``, so the
# bar the reliability floor, the build backstop and the CR-1 position test moves
# with the model's own peak forecast rather than sitting where PJM set it. D66
# §3.1 decomposed the D57 clearing's remaining position error additively and
# measured that leg at 78 % of it in 2024/25 and 67 % in 2025/26: the model's
# screen peak runs 2,481 MW (1.6 %) and 4,636 MW (3.0 %) above the peak PJM's
# own Reliability Requirement implies, and ``FPR × Δpeak`` reproduces
# ``R_model − R_published`` to the MW with ZERO residual. Reading the published
# MW makes the requirement independent of the model's peak in every in-table
# delivery year (∂R/∂peak = 0), which is what the auction's own denominator is.
#
# THE SERIES. Digitized from the committed demand-curve rows
# (data/raw/capacity-market/demand-curve/pjm/pjm.csv, metric
# ``reliability_requirement``, RTO area) and reconciled against them
# byte-for-byte by tests/unit/model/test_capacity.py — a published market-design
# input, never a fit target (rules 13/23), on the SAME provenance discipline
# NET_ICR_REQUIREMENT_MW_BY_ISO carries below. Every row cites its RPM BRA
# Planning Parameters workbook, sheet and row.
#
# THE WHOLE-RTO ROW IS THE OPERAND, and the choice is fixed in code rather than
# per run (PRECOMMIT-capx-d67 §3). PJM also publishes ``reliability_requirement
# _frr_adj`` and ``ee_addback``, whose SUM is the denominator that reproduces
# PJM's published cleared position to four decimals in all four years (D66 §1.2)
# — but that pair is the RPM-ONLY comparator and is basis-mismatched to this
# model: the model runs the entire RTO, all load and all resources, while RPM is
# net of an FRR block of 31.0 / 31.3 / 32.1 / 10.9 GW across these years. The
# model's census is whole-RTO, so its requirement is the whole-RTO row.
# Selecting between the two by result would be rule-21 [R-DOF] territory.
#
# CONSUMER. ``retirements.gross_adequacy_requirement_mw`` — armed ONLY by the
# default-OFF ``ScenarioConfig.capacity_adequacy_requirement_published_by_iso``
# gate (rule 28 row ``capacity_adequacy_requirement_published``); off, every
# solve of every ISO is byte-identical. The value returned is GROSS of demand
# response, the same basis ``peak × FPR`` returns at that seam, so the D48
# DR-as-supply branch in ``resolve_adequacy_requirement_mw`` decides netting
# unchanged: this gate moves the requirement's OPERAND, never its netting
# convention, its peak or its accreditation.
#
# HOLD-LAST / GAPS (declared ex ante, PRECOMMIT-capx-d67 §4). An in-table
# delivery year returns the published MW. The in-table GAP (2026/27 and 2027/28
# publish an FPR but no Reliability Requirement row), every pre-table year, and
# every year strictly BEYOND the 2028/29 forward edge all return ``None`` and
# fall through to the FPR path — which itself holds-last the published FPR.
# That fall-through IS the ratio hold-last NEISO's sibling implements
# explicitly: for PJM the last published RR-to-forecast-peak ratio *is* the
# published FPR, because PJM constructs ``RR = forecast peak × FPR`` by
# definition and the arithmetic closes on the committed rows (2025/26:
# 144,450 ÷ 0.9380 = 153,997.9; 2028/29: 156,012.885 ÷ 0.9401 = 165,953.7). So
# no absolute MW is ever held over a forward horizon (which would fail the
# rule-13 forward test), no new constant is introduced, the held bar still
# scales with load, and the mechanism's footprint is exactly the delivery years
# the published table covers — every forecast year past 2028/29 is
# byte-identical to the unarmed path.
#
# FORWARD STORY (rule 13). The Reliability Requirement is a recurring published
# planning quantity: PJM re-derives and posts it for EVERY delivery year in the
# BRA Planning Parameters, and it responds to load, reserve margin and
# accreditation-design conditions by construction. New rows are intaken on
# publication (rule 23 [R-FROZEN-DERIVE]), never against a residual.
RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO: dict[str, dict[str, float]] = {
    "PJM": {
        # 2021/2022 PPP workbook dated 2018-05-03, '2021-2022 Parameters'
        # sheet, Reliability Requirement row, RTO column.
        "2021/2022": 166355.1,
        # 2022/2023 PPP workbook, 'Planning Parameters' sheet, same row/column.
        "2022/2023": 163268.9,
        # 2023/2024 PPP workbook dated 2022-06-21, same sheet/row/column.
        "2023/2024": 163166.2,
        # 2024/2025 PPP workbook dated 2024-05-08, same sheet/row/column.
        "2024/2025": 164107.6,
        # 2025/2026 PPP workbook posted 2024-04-08, same sheet/row/column. The
        # level drops ~20 GW against 2024/25 because this is the FIRST
        # post-CIFP delivery year: the requirement moves to the accredited-UCAP
        # basis (FPR 1.0894 -> 0.9380), which is the same regime break D48
        # vintages the accreditation side of.
        "2025/2026": 144450.0,
        # 2026/2027 and 2027/2028: NO Reliability Requirement row is committed
        # (both publish an FPR). Deliberately absent, not zero — an in-table
        # gap falls through to the FPR path (see HOLD-LAST / GAPS above); a
        # mid-table hole is a data problem hold-last must not paper over.
        # 2028/2029 PPP workbook initially posted 2026-03-20 (FFR-2C intake
        # 2026-08-02), 'Planning Parameters' sheet, Reliability Requirement row
        # (A15), RTO column. Carried at the published precision.
        "2028/2029": 156012.88535,
    },
}

# Published per-Capacity-Commitment-Period Net Installed Capacity Requirement
# (Net ICR = ICR − HQICCs), in MW, keyed by CCP label "YYYY/YYYY+1" — the
# ISO-NE analogue of :data:`FORECAST_POOL_REQUIREMENT_BY_ISO` (capx D40,
# 2026-09-02, executing FINDING-capx-d33-neiso-position-2026-09-02.md §4 R-A).
#
# WHY. ISO-NE publishes NO reserve-margin percentage: the FCM procures to an
# absolute Net ICR that is re-derived and filed for EVERY CCP (the FCA ICR
# filings, Docket ER-series each November). HEAD's NEISO requirement is the
# composite ``peak × (1 − f_DR) × (1 + PRM)`` with BOTH factors anchored to ONE
# vintage (the ARA-3 restatement of CCP 2026/27 — see the PLANNING_RESERVE_MARGIN
# _BY_ISO["NEISO"] entry). Algebraically that composite IS the published
# construction ``(Net ICR − DCR CSO) × peak / CELT_peak`` at exactly one CCP;
# every other delivery year inherits that CCP's ratio, while the published
# series itself fell 34,075 → 30,550 MW (FCA 11 → 18) and the model's hindcast
# weather-year peaks sit far below the CELT 50/50 forecasts the ratio was built
# on. D33 measured the consequence: −6,018 MW (−18.5 %) of requirement in 2023,
# worth +23.8 reserve-ratio points of the model's +21.4-pt long-position error
# on its own, decaying to +2.0–2.5 pts at the anchor vintage exactly as a
# frozen-vintage artifact must.
#
# THE SERIES. FCA-vintage (primary auction) Net ICRs, digitized from the
# committed demand-curve rows (data/raw/capacity-market/demand-curve/neiso/
# neiso.csv, metric ``reliability_requirement``; every row cites ISO-NE's
# summary_of_historical_icr_values.xlsx sheet/row, one row cross-checked to the
# FCA 13 ICR-filing testimony) and reconciled against them byte-for-byte by
# tests/unit/model/test_capacity.py — a published market-design input, never a
# fit target (rules 13/23). The FCA vintage (not the ARA restatement) is
# deliberate: the R2 vintage curves (``_NEISO_MRI_CLEARING_POINTS``) normalize
# their x by the SAME FCA Net ICR, so position and curve share one denominator
# object (D33 §4 R-B — one convention on both sides of evaluate_demand_curve).
# The ARA-3 / ARA-2 restatements (30,050 / 29,855 MW, icr-ara extract) are the
# same-cycle LATER vintages of the last two CCPs; they are not mixed into the
# series, and the last one supplies the hold-last ratio below instead.
#
# CONSUMER. ``retirements.resolve_published_net_icr_mw`` — armed ONLY by the
# default-OFF ``ScenarioConfig.neiso_net_icr_requirement`` gate (rule 28 row
# ``neiso_net_icr_requirement``); off, every NEISO solve is byte-identical to
# the composite. In-table CCPs return the absolute MW (the model's peak drops
# out — the auction's own denominator, D33 R-A shape (i)); years BEFORE the
# first entry (pre-FCA 11) and any in-table gap fall through to the composite
# exactly as the PJM FPR table does; years strictly BEYOND the last entry
# hold-last (card C-A 2026-08-25) — see NET_ICR_HOLD_LAST_RATIO_BY_ISO for why
# the held object is a ratio, not the MW. The requirement the floor/backstop/
# CR-1 position test is then ``Net ICR × (1 − f_DR)`` — the DR registry entry
# is DEFINED as a fraction OF Net ICR (see its citation block), so under this
# path the netted MW reproduces ISO-NE's own supply-side DCR counting.
# FORWARD STORY (rule 13): the Net ICR is a recurring published planning
# quantity that regenerates every capability year and responds to load /
# BTM-PV / tie conditions by construction; the FCM sunset (FCA 18 was the last
# forward auction) hands the continuation to CAR-SA's successor parameters,
# intaken on publication (rule 23) as new rows here.
NET_ICR_REQUIREMENT_MW_BY_ISO: dict[str, dict[str, float]] = {
    "NEISO": {
        "2020/2021": 34_075.0,  # FCA 11 (ER17-320-000)
        "2021/2022": 33_725.0,  # FCA 12 (ER18-263-000)
        "2022/2023": 33_750.0,  # FCA 13 (ER19-291-000; testimony p.10)
        "2023/2024": 32_490.0,  # FCA 14 (ER20-311-000)
        "2024/2025": 33_270.0,  # FCA 15 (ER21-371-000)
        "2025/2026": 31_645.0,  # FCA 16 (ER22-378-000)
        "2026/2027": 30_305.0,  # FCA 17 (ER23-405-000)
        "2027/2028": 30_550.0,  # FCA 18 (ER24-362-000) — the LAST FCA held
    },
}

# Hold-last object for delivery years strictly beyond an ISO's last published
# Net ICR CCP (card C-A convention). PJM's held object is the FPR — a RATIO to
# peak, so the held requirement still scales with load. An absolute Net ICR
# held flat over a 2028–2050 horizon would NOT respond to changed conditions
# (a growing peak against a frozen MW bar is a collapsing margin by
# construction), failing the rule-13 forward test; so the held object here is
# the last CCP's own published Net-ICR-to-50/50-peak ratio, applied to the
# model's peak: ``requirement = peak × ratio × (1 − f_DR)`` — the SAME
# construction the composite fallback uses, re-anchored on the LAST CCP.
# Value: ISO-NE's newest same-cycle restatement of CCP 2027/28 (ARA 2, the
# 2025-11-21 ICR-related-values filing, p.12 — committed extract
# data/raw/capacity-market/icr-ara/neiso/ara_requirement_values.csv rows
# ``2027-2028 / ARA 2``): Net ICR 29,855 MW over the 50/50 summer peak net of
# BTM PV 26,417 MW = 1.13015. Kept as an explicit expression so both published
# MW stay traceable (rule 5). Supersedes itself the moment a later CCP's rows
# land in NET_ICR_REQUIREMENT_MW_BY_ISO (rule 23).
NET_ICR_HOLD_LAST_RATIO_BY_ISO: dict[str, float] = {
    "NEISO": 29_855.0 / 26_417.0,  # ARA 2 of CCP 2027/28: Net ICR / 50-50 peak
}

# --------------------------------------------------------------------------- #
# NYISO adequacy-requirement devintage (capx D52, 2026-09-04, executing
# FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md §5.2.4 items 1 and 2 — the
# NYISO per-ISO repair lane D45's §9 close-out names). THREE registries, ONE
# published source: NYSRC "New York Control Area Installed Capacity
# Requirement for the Period May 2026 through April 2027" — Technical Report
# Appendices (Dec 2025), Appendix D §D.1.1 Table D.2 "New York Control Area
# ICAP to UCAP Translation" (report p.68 = PDF p.86; sha256
# 714aeeb9156795108147982f93cf90f885ed110835e0a6f2fa257f809da419d5, D45 §8,
# re-fetched and hash-matched by D52). Per capability year (May–April, labelled
# by its start year, "YYYY/YYYY+1") the table publishes the ICAP-market
# FORECAST PEAK LOAD (MW), the EC-approved INSTALLED CAPACITY REQUIREMENT (the
# adopted IRM, %), the DERATE FACTOR (the NYCA ICAP→UCAP translation factor)
# and the resulting ICAP / UCAP requirements — the NYISO analogue of PJM's
# published FPR and ISO-NE's published Net ICR: a market-design PARAMETER on
# file before the capability year begins, never a fit target (rules 13/23).
# Every row is digitized into the committed
# data/raw/capacity-market/demand-curve/nyiso/nyiso.csv (metrics
# icap_market_forecast_peak / irm_adopted / icap_ucap_translation_factor /
# ucap_requirement) and reconciled against it — and against the table's own
# identity peak × (1 + IRM) × (1 − derate) = UCAP requirement (< 1 MW) — by
# tests/unit/model/test_capacity.py::TestNyisoRequirementDevintage.
#
# WHAT IT REPAIRS (D45 §5.2, re-measured by D52's pre-declaration §1): at
# default the NYISO requirement is peak × 1.244 × (1 − 0.1321) on the MODEL's
# peak — the 2025-26 IRM crossed with the 2024-25 derate, a mixed single
# vintage — and the capacity screens consume it on the capacity-screen seam's
# growth-scaled weather-year peak, which in the 2021–2025 hindcast sits
# 2.1–3.6 GW of requirement BELOW the published NYCA UCAP requirement in every
# scored year (the position artifact behind the +189 % curve-ON over-fire).
# CONSUMERS: two default-OFF ScenarioConfig gates, each consulting exactly one
# registry object (rule 19), inside ``retirements.gross_adequacy_requirement_mw``:
#   * ``nyiso_requirement_forecast_peak`` → NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO:
#     the requirement is priced on the PUBLISHED forecast peak of the
#     capability year (item 1). In-table years only; outside the table the
#     model's own peak is the (forward) forecast and is used unchanged — no
#     hold-last, because a held MW peak against a growing load would fail the
#     rule-13 forward test.
#   * ``nyiso_requirement_vintage_factors`` → NYCA_IRM_ADOPTED_BY_ISO +
#     NYCA_ICAP_UCAP_TRANSLATION_BY_ISO: the factor is the capability year's
#     adopted IRM × (1 − derate) (item 2, the D40 vintage axis); strictly
#     beyond the last published pair HOLD-LAST (card C-A) as that pair's ratio
#     (2025/26: 1.244 × 0.870 = 1.0823 vs the composite 1.0797, +0.24 %);
#     pre-table years fall through to the composite.
# Both on ⇒ the in-table requirement IS Table D.2's UCAP requirement, the
# model's peak dropping out exactly as under the NEISO Net ICR / PJM FPR
# paths. INFORMATION GATE (rule 13, the D42/D44 construction): a row of
# capability year Y/Y+1 is read in model year Y only. Every parameter in it
# is fixed BEFORE the capability year begins (May 1, Y): the IRM is adopted by
# the NYSRC Executive Committee in December Y−1 (the committed csv rows carry
# the dates — 2020-12-04 / 2021-12-03 / 2022-12-09 / 2023-12-08 / 2024-12-06),
# the forecast peak is the load forecast NYISO adopts for that capability
# year's ICAP requirement, and the summer translation factor is posted ahead
# of the May capability period. A later capability year's row is never read
# for an earlier model year and the hold-last extends the table's forward
# edge only. FORWARD STORY: the same construction regenerates every capability
# year from the then-current Gold Book forecast + adopted IRM + translation
# factor; new rows land on publication (rule 23). Rule 25: NYISO only — the
# registries hold one ISO and the gate predicates require an entry.
# --------------------------------------------------------------------------- #
NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO: dict[str, dict[str, float]] = {
    "NYISO": {  # Table D.2 "Forecast Peak Load (MW)", capability year
        "2020/2021": 32_296.0,
        "2021/2022": 32_333.0,
        "2022/2023": 31_767.0,
        "2023/2024": 32_049.0,
        "2024/2025": 31_542.0,
        "2025/2026": 31_469.0,
    },
}

# Table D.2 "Installed Capacity Requirement (%)" − 100 %, i.e. the EC-approved
# (adopted) IRM as a fraction. Differs from the IRM STUDY base-case value the
# `irm` csv rows carry in 2023/24 (study 19.9 → adopted 20.0) and 2024/25
# (study 23.1 → adopted 22.0); the adopted value is what the ICAP market
# requirement was set on (Table D.1 "EC Approved IRM"; 2020/21 = 18.9 % there
# and in Table D.2's 118.9). EC approval dates for 2021/22–2025/26: 2020-12-04,
# 2021-12-03, 2022-12-09, 2023-12-08, 2024-12-06 (the committed `irm` rows'
# citations); 2020/21's date is not carried in-repo and is not invented here.
NYCA_IRM_ADOPTED_BY_ISO: dict[str, dict[str, float]] = {
    "NYISO": {
        "2020/2021": 0.189,
        "2021/2022": 0.207,
        "2022/2023": 0.196,
        "2023/2024": 0.200,
        "2024/2025": 0.220,
        "2025/2026": 0.244,
    },
}

# Table D.2 "Derate Factor" — the NYCA-wide ICAP→UCAP translation factor for
# the capability year's summer period (ICAP Manual §2.5: UCAP requirement =
# ICAP requirement × (1 − factor)). The 2020/21–2024/25 values are the
# committed `icap_ucap_translation_factor` csv rows (byte-equal, asserted by
# test); 2025/26 (0.1300) is D52's intake from the 2026-27 appendices. The
# single-vintage PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"]
# above stays the 2024/25 value (1 − 0.1321) — the unarmed composite is
# byte-identical by construction; only the armed path reads this table.
NYCA_ICAP_UCAP_TRANSLATION_BY_ISO: dict[str, dict[str, float]] = {
    "NYISO": {
        "2020/2021": 0.0830,
        "2021/2022": 0.0877,
        "2022/2023": 0.0978,
        "2023/2024": 0.1014,
        "2024/2025": 0.1321,
        "2025/2026": 0.1300,
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

# --------------------------------------------------------------------------- #
# NYISO LOCALITY capacity demand curves (capx D59, 2026-09-05 — executing
# FINDING-capx-d52-2026-09-04.md §8(2) route 1 / D45 §5.2.4 item 3; design
# docs/handoffs/DESIGN-capx-d59-nyiso-locality-2026-09-05.md). GATED by the
# default-OFF ``ScenarioConfig.locality_capacity_curves``; NYISO-only in DATA
# (rule 25 [R-ISO-SCOPE]: every registry below holds one ISO, and the gate
# predicate ``retirements.locality_capacity_curves_armed`` requires an entry).
#
# NYISO's ICAP Spot Market Auction clears a Market-Clearing Price for the NYCA
# AND for each Locality (New York City = Load Zone J, Long Island = Zone K, the
# G-J Locality = zones G–J): "The Market-Clearing Price for a Locality will be
# the price at which the supply curve for that Locality intersects the Demand
# Curve for that Locality unless the Market-Clearing Price determined for Rest
# of State is higher in which case the Market-Clearing Price for that Locality
# will be set at the Market-Clearing Price for Rest of State." (NYISO Installed
# Capacity Manual §5.15.2, manual p.206; sha256 b0104a503be85aa705250221360fd101
# 6addaee6ccf41a78aed7fe488659a497, fetched 2026-09-05). The locality demand
# curves are published per capability year on the SAME sheet as the NYCA curve
# (NYISO "Demand Curve Parameters" / the ICAPWG annual-update decks) and are
# digitized in the committed data/raw/capacity-market/demand-curve/nyiso/
# nyiso.csv (areas NYC / LI / G-J beside NYCA), reconciled row-for-row by
# tests/unit/model/test_capacity.py::TestNyisoLocalityCapacityCurves. Each
# vintage is the IDENTICAL straight-line construction the NYCA vintages use
# (``_nyiso_icap_vintage_curve``): net-CONE fraction 1.0 at the locality's
# requirement, zero at 1 + the locality's published Demand Curve Length (18 %
# for NYC and LI, 15 % for G-J, vs 12 % NYCA — Analysis Group DCR Table 2), the
# cap where the summer max-clearing / reference-point ratio meets the line;
# anchor = the locality's Annual Reference Value ($/kW-yr). 2021-22 / 2022-23
# published no ARV → flat anchor = the reference-point price × 12 with a
# ()-shape, exactly the NYCA convention for those two vintages.
#
# Only NYC and LI are representable on the 5-zone model (a locality must be a
# UNION of model zones; G-J spans Capital_Hudson = F+G, so it is not — DESIGN
# §1); G-J's rows stay in the csv, unconsumed, and the crosswalk keeps its
# ``aggregate`` exclusion. ``LOCALITY_CAPACITY_AREAS_BY_ISO`` maps each
# representable locality's demand-curve label onto the capacity-deliverability
# area label whose ``requirement`` rows (the published Locational Minimum ICAP
# Requirement, LCR Report table row [G]) the mechanism reads through the
# EXISTING curated reader ``data.capacity_deliverability.requirement_by_area``
# (rule 6 — never a re-typed dict), and whose model zones come from the
# crosswalk's ``leaf`` rows (``capacity_area_crosswalk.map_area``).
_NYISO_LOCALITY_CURVE_LENGTH: float = (
    0.18  # NYC and LI Demand Curve Length, all vintages
)

LOCALITY_CAPACITY_AREAS_BY_ISO: dict[str, dict[str, str]] = {
    "NYISO": {"NYC": "NYC", "LI": "Long Island"},
}

LOCALITY_MARKET_DESIGN_VINTAGES: dict[
    str, dict[str, tuple[MarketDesignVintage, ...]]
] = {
    "NYISO": {
        "NYC": (
            MarketDesignVintage("2021-2022", 21.28 * 12.0),
            MarketDesignVintage("2022-2023", 22.77 * 12.0),
            MarketDesignVintage(
                "2023-2024",
                154.53,
                _nyiso_icap_vintage_curve(21.20, 29.63, _NYISO_LOCALITY_CURVE_LENGTH),
            ),
            MarketDesignVintage(
                "2024-2025",
                150.98,
                _nyiso_icap_vintage_curve(19.84, 31.63, _NYISO_LOCALITY_CURVE_LENGTH),
            ),
            MarketDesignVintage(
                "2025-2026",
                140.47,
                _nyiso_icap_vintage_curve(17.37, 41.30, _NYISO_LOCALITY_CURVE_LENGTH),
            ),
            MarketDesignVintage(
                "2026-2027",
                144.08,
                _nyiso_icap_vintage_curve(17.81, 42.67, _NYISO_LOCALITY_CURVE_LENGTH),
            ),
        ),
        "LI": (
            MarketDesignVintage("2021-2022", 17.60 * 12.0),
            MarketDesignVintage("2022-2023", 17.59 * 12.0),
            MarketDesignVintage(
                "2023-2024",
                66.26,
                _nyiso_icap_vintage_curve(13.08, 24.21, _NYISO_LOCALITY_CURVE_LENGTH),
            ),
            MarketDesignVintage(
                "2024-2025",
                61.24,
                _nyiso_icap_vintage_curve(11.29, 26.59, _NYISO_LOCALITY_CURVE_LENGTH),
            ),
            MarketDesignVintage(
                "2025-2026",
                49.61,
                _nyiso_icap_vintage_curve(6.80, 28.16, _NYISO_LOCALITY_CURVE_LENGTH),
            ),
            MarketDesignVintage(
                "2026-2027",
                57.58,
                _nyiso_icap_vintage_curve(7.89, 29.09, _NYISO_LOCALITY_CURVE_LENGTH),
            ),
        ),
    },
}

# External Unforced Capacity Deliverability Rights INTO each locality — the
# locality-attributable part of the D2 external-capacity tie (which the NYCA
# ledger already carries inside ADEQUACY_EXTERNAL_TIE_FIRM_MW["NYISO"]; these
# rows enter the LOCALITY ICAP census only, never the NYCA half, so nothing is
# double-counted). ICAP Manual §4.9.6 "UDRs awarded, not subject to the above
# limits" (manual p.94): Cross Sound Cable 330 MW (ISO-NE → K), Neptune 660 MW
# (PJM → K), Linden VFT 315 MW (PJM → J), Hudson Transmission Project 660 MW
# (PJM → J; footnote 1: "On April 30, 2022, the CRIS Rights for the Hudson
# Transmission Project expired … in 2024 … elected partial CRIS of 85 MW"),
# Champlain Hudson Power Express 1,250 MW (HQ → J; in service CY 2026/27).
# Rows are (locality curve label, line, ICAP MW, first capability-year start,
# last capability-year start inclusive); a right applies in model year Y iff
# first ≤ Y ≤ last (the information gate: the CRIS lapse and the CHPE
# in-service date are on file). Rule 13: rights are re-published in every
# manual revision and respond to conditions (the HTP lapse IS such a response).
NYISO_LOCALITY_UDR_ICAP_MW: tuple[tuple[str, str, float, int, int], ...] = (
    ("LI", "Cross Sound Cable (ISO-NE -> Zone K)", 330.0, 0, 9999),
    ("LI", "Neptune (PJM -> Zone K)", 660.0, 0, 9999),
    ("NYC", "Linden VFT (PJM -> Zone J)", 315.0, 0, 9999),
    (
        "NYC",
        "Hudson Transmission Project (PJM -> Zone J), CRIS through CY 2021/22",
        660.0,
        0,
        2021,
    ),
    ("NYC", "Hudson Transmission Project, 85 MW CRIS elected 2024", 85.0, 2024, 9999),
    (
        "NYC",
        "Champlain Hudson Power Express (HQ -> Zone J), in service CY 2026/27",
        1250.0,
        2026,
        9999,
    ),
)

# Published peaking-plant GROSS Cost of New Entry ($/kW-yr) by capacity region
# and capability year — the same "Demand Curve Parameters" sheets as the ARV
# rows (nyiso.csv ``gross_cone`` rows; 2023-2024 / 2024-2025 from the ICAPWG
# annual-update decks p.31 / p.30, 2025-2026 from the posted parameter sheet,
# 2026-2027 already committed by FFR-2C). The entry screen's locality siting
# leg (DESIGN §5.5) scales a candidate's annualized fixed cost by
# ``GrossCONE_L / GrossCONE_NYCA`` of the delivery year's vintage — NYISO's own
# published locality cost differential (rule 13; no zone premium is invented).
# Hold-last beyond the table (a RATIO, like the D52 factor pair); hold-first
# before it (the 2021-25 DCR cycle's earliest published sheet on disk).
LOCALITY_GROSS_CONE_BY_ISO: dict[str, dict[str, dict[str, float]]] = {
    "NYISO": {
        "2023/2024": {"NYCA": 120.04, "G-J": 157.61, "NYC": 212.81, "LI": 168.15},
        "2024/2025": {"NYCA": 132.98, "G-J": 174.72, "NYC": 229.11, "LI": 186.37},
        "2025/2026": {"NYCA": 127.71, "G-J": 127.58, "NYC": 222.73, "LI": 137.03},
        "2026/2027": {"NYCA": 131.94, "G-J": 131.80, "NYC": 230.10, "LI": 141.57},
    },
}


def resolve_locality_curve_vintage(
    iso: "str | None", locality: str, year: "int | None"
) -> "MarketDesignVintage | None":
    """Return the locality demand-curve vintage governing ``iso``/``locality``/``year``.

    The locality analogue of :func:`resolve_demand_curve_vintage`, with the
    same step-function resolution (hold-first before the earliest published
    vintage, hold-last beyond the latest — the forward carry a forecast uses).
    Returns ``None`` when the ISO or locality has no table, so a caller keeps
    the NYCA price alone.
    """
    if iso is None or year is None:
        return None
    vintages = LOCALITY_MARKET_DESIGN_VINTAGES.get(iso, {}).get(locality)
    if not vintages:
        return None
    chosen = vintages[0]
    for v in vintages:
        if year >= int(v.delivery_year[:4]):
            chosen = v
        else:
            break
    return chosen


def locality_curve_price_per_firm_mw_yr(
    iso: "str | None", locality: str, year: "int | None", position: float
) -> "float | None":
    """The locality's published curve at ``position``, in $/firm-MW-yr, or ``None``.

    ``evaluate_demand_curve(vintage.demand_curve, position) × ARV × 1000`` on the
    delivery year's vintage; a ()-shape vintage prices its flat anchor (the
    NYCA convention). ``None`` when no vintage exists — the caller then settles
    on the NYCA price alone (ICAP Manual §5.15.2: a locality is never paid
    below Rest of State).
    """
    vintage = resolve_locality_curve_vintage(iso, locality, year)
    if vintage is None:
        return None
    anchor = float(vintage.net_cone_curve_per_kw_yr)
    if vintage.demand_curve:
        return (
            evaluate_demand_curve(vintage.demand_curve, float(position))
            * anchor
            * 1000.0
        )
    return anchor * 1000.0


def resolve_locality_gross_cone_ratio(
    iso: "str | None", locality: str, year: "int | None"
) -> "float | None":
    """Published ``GrossCONE_locality / GrossCONE_NYCA`` for the delivery year, or ``None``.

    Step-function vintage resolution as :func:`resolve_locality_curve_vintage`
    (hold-first / hold-last). ``None`` when the ISO has no table or the
    locality is absent from it.
    """
    if iso is None or year is None:
        return None
    table = LOCALITY_GROSS_CONE_BY_ISO.get(iso)
    if not table:
        return None
    labels = sorted(table, key=lambda lbl: int(lbl[:4]))
    chosen = labels[0]
    for lbl in labels:
        if int(year) >= int(lbl[:4]):
            chosen = lbl
        else:
            break
    row = table[chosen]
    if locality not in row or "NYCA" not in row or row["NYCA"] <= 0.0:
        return None
    return float(row[locality]) / float(row["NYCA"])


# Per-ISO exogenous AS-revenue registry — the modular generalization of the
# ERCOT-only rates above. ``model.ancillary.as_revenue_per_mw_yr`` resolves the
# credit from here by the run's ISO, so ANY ISO slots in by adding its
# ``{fuel: $/kW-yr}`` rate here plus its saturation reference fleet in
# AS_SATURATION_REF_GW_BY_ISO — no code change. ERCOT is the existing 2023
# calibration (referenced, so byte-identical). Every OTHER ISO is deliberately
# UNPOPULATED: an ISO absent here earns no exogenous AS credit (0), so the
# default (``as_revenue_enabled`` off) and every non-ERCOT run stay
# byte-identical until a rate is intaken. To populate an ISO, add its measured
# AS-market revenue (regulation + reserves, at the reference-fleet year, from
# that ISO's market-monitor SOM/DMM report — e.g. CAISO DMM Special Report on
# Battery Storage; PJM/NYISO/ISO-NE/MISO IMM State-of-the-Market ancillary
# sections) AND its reference-fleet GW below (the code fails loud if a rate is
# added without a matching ref). Rule 13: each rate is a measured AS-market
# outcome that regenerates forward via the saturation decline and responds to
# the fleet — the same admissibility as the ERCOT calibration. Capacity
# evolution is forecast-only, so nothing here touches a backcast keeper.
AS_REVENUE_PER_KW_YR_BY_ISO: dict[str, dict[str, float]] = {
    "ERCOT": ERCOT_AS_REVENUE_PER_KW_YR,
    # CAISO: measured DAM battery AS revenue at the 2023 reference fleet —
    # Daily Energy Storage Report battery awards × OASIS PRC_AS DAM clearing
    # prices (nested-region settlement), over the measured EIA-860 CAISO
    # battery fleet (monthly-avg 5,517 MW): $81.8M central → 14.82 $/kW-yr
    # (bracket 12.65–16.99; 2024 7.41, 2025 5.68 — the saturation check).
    # Cross-validated against DMM 2023/2024 Special Reports on Battery
    # Storage (net revenue $78/$53 per kW-yr, energy 62 %/82 %, RT-BCR
    # 7 %/4 % ⇒ AS+other ≤ $24.1/$7.4). Storage only — CAISO thermal AS is
    # unidentified (no per-resource-type award series) and earns 0. DA-leg
    # only (no mileage, no RT increment), so conservatively low.
    # Identification precommit-staged before its entry-screen effect was
    # computed; the measured effect flips no storage tech's entry sign.
    # Source: docs/FINDING-caiso-value-stack-d9-2026-08.md +
    # results/calibration/caiso_storage_as_revenue_phase0.json (probe
    # scripts/probes/caiso_storage_as_revenue_phase0.py).
    "CAISO": {"storage": 14.82},
    # "PJM": {...}, "NYISO": {...}, "NEISO": {...}, "MISO": {...}
}

# Per-ISO AS-market saturation reference fleet (GW): the AS-eligible (mostly
# storage) fleet size at which the ISO's AS_REVENUE_PER_KW_YR_BY_ISO base rate
# was measured. Per-ISO because AS-market DEPTH differs — ERCOT's small AS
# market saturates far faster than PJM's/MISO's larger footprints. The decline
# SHAPE (ERCOT_AS_SATURATION_EXPONENT) is shared. Must carry an entry for every
# ISO that has a rate above (enforced in as_revenue_per_mw_yr).
AS_SATURATION_REF_GW_BY_ISO: dict[str, float] = {
    "ERCOT": ERCOT_AS_SATURATION_REF_GW,
    # CAISO: the 2023 average measured EIA-860 battery fleet the 14.82 rate
    # was measured at. The shared 2.5 exponent is KEPT deliberately: CAISO's
    # own measured decline is milder (implied 1.34 for 2023→24, 0.76 for
    # 2024→25 — requirement growth offsets fleet growth), so 2.5 UNDER-credits
    # AS past the reference — conservative, and a CAISO-fitted exponent would
    # be 2 DOF on 3 observations (owner-ratified 2026-08-25; see
    # docs/FINDING-caiso-value-stack-d9-2026-08.md §2.4).
    "CAISO": 5.517,
}

# ISOs that have a per-plant CAMPD bin artifact and therefore take the
# offer-curve (per-plant tranche) binning path in the runner instead of the
# legacy equal-width ``aggregate_fleet`` heat-rate binning. ERCOT is driven by
# the curated ``data/raw/reference/custom-bin-assignments.csv``; CAISO/NEISO/NYISO/PJM/MISO
# are covered by the CAMPD-derived ``data/raw/_processed-legacy/thermal_tranches_<ISO>.csv``
# (and the committed ``data/raw/_processed-legacy/bin_assignments_<ISO>.csv`` review
# artifacts). The runner gate keys
# off this set so the per-plant path unlocks per ISO as its artifact lands.
# SPP is DELIBERATELY ABSENT at registration (2026-09-06, lane SPP-20): its
# ``thermal_tranches_SPP.csv`` / ``bin_assignments_SPP.csv`` artifacts are
# SPP-30's frozen derives and do not exist yet, and membership here without
# the artifact would send the runner down the per-plant path to a missing
# file. SPP-30 adds "SPP" in the PR that lands the artifact (the same
# per-ISO unlock every other member took); until then SPP takes the legacy
# equal-width path, which its first solve does not use anyway (plan §4: no
# solve before SPP-30/31/32 land — gate G4).
#
# NWPP is ABSENT BY OWNER RULING, not by omission (N8, NWPP desk sitting #4,
# 2026-09-14: "LEGACY HEAT-RATE BINS FOR THE FIRST KEEPER; CAMPD PER-PLANT AS
# A LEVER" — use_campd_bins=False). CEMS reaches 30.98 % of footprint
# nameplate / 41.8-43.6 % of energy (NWPP-10 §2 item 8) because 36.3 % of the
# footprint is hydro that CEMS can never cover, and 939 plants x 5 zones is
# the largest per-plant LP the repo would hold (gate G21). Per-plant binning
# is a pre-declared W5 lever; the ID/OR/UT/WA CEMS NWPP-11 landed still feed
# outages, emission rates and commitment evidence.
# SOCO is DELIBERATELY ABSENT at registration for the identical reason
# (2026-09-14, lane SOCO-20): ``thermal_tranches_SOCO.csv`` /
# ``bin_assignments_SOCO.csv`` are SOCO-30's frozen derives from the AL/GA
# CEMS SOCO-11 landed, and do not exist yet. SOCO-30 adds "SOCO" with the
# artifact (SOCO plan §4, gate G4: no solve before SOCO-30/31/32 land).
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

# Published WHOLE-CLASS storage accreditation — the realized firm fraction of
# NAMEPLATE an ISO's own resource-adequacy ledger counts for its entire storage
# class, for the ISOs that accredit storage WITHOUT publishing a duration ->
# credit table. Consulted (per ISO, behind that ISO's own default-OFF gate) by
# `model.storage.storage_accreditation_credit`, where it REPLACES the
# by-duration lookup outright rather than multiplying it (rule 19
# [R-ONE-MECH]: one storage-accreditation mechanism per ISO, never a stack).
#
# WHY A WHOLE-CLASS OBJECT RATHER THAN A CAISO ROW IN THE TABLE ABOVE (FFR-4E,
# and the reconciliation FFR-4D §6.1 routed rather than guessed at):
#   * CAISO PUBLISHES NO STORAGE DURATION TABLE. The CY2026 NQC report's
#     "2026 Tech Factors" tab carries technology factors for solar (fixed /
#     tracking / thermal), wind, non-dispatchable hydro, geothermal,
#     cogeneration and biomass -- and NO battery row, because batteries are
#     DISPATCHABLE and are accredited at demonstrated capability. The
#     assessment says so in terms (2026 SLRA Technical Appendix §1.1.1): "For
#     dispatchable resources like battery and natural gas plants, the NQC value
#     is typically near its NDC or installed capacity." A CAISO entry in the
#     by-duration registry would be an INVENTED object, so none is minted.
#   * THE BASIS HAD TO BE CORRECTED, and this is the whole substance of the
#     reconciliation. CAISO's published ratio is NQC/NDC = 13,365/14,131 =
#     0.9458. The model multiplies a storage unit's EIA-860 NAMEPLATE
#     `power_cap_mw`, and CAISO's NDC is only 91.47 % of that nameplate
#     (14,131 / 15,448.4). Quoting 0.9458 against nameplate would over-credit
#     the class by 8.1 pp -- exactly the substitution rule 14
#     [R-ACCURATE]'s misalignment clause forbids. The registry value is
#     therefore NQC / NAMEPLATE, both terms measured:
#         13,365 MW  published September NQC, 2026 SLRA Technical Appendix
#                    Table 1.1 Battery row, digitized first-party by
#                    scripts/data/derive_caiso_slra_class_accreditation.py
#                    into data/raw/capacity-market/loads-resources/caiso/
#                    (that table's NQC column foots EXACTLY to its own
#                    published 59,069 MW total, which is the parse's proof)
#         15,448.4 MW EIA-860 2025 Early Release, BA CISO, Status "OP"
#                    nameplate -- the SAME object STORAGE_BASE_FLEET_MW
#                    ["CAISO"] is built from, so numerator and denominator
#                    describe one fleet.
#     -> 13,365 / 15,448.4 = 0.865138.
#   * IT DELIBERATELY KEEPS THE DELIVERABILITY HAIRCUT the published ratio
#     embeds (Table 1.1's battery row is 0.98872 full-capacity-deliverable /
#     0.96272 interim / 0.58924 partial / 0.0 energy-only). The model has NO
#     per-resource deliverability status for storage -- `capacity_deliverability
#     _limits` prices a zonal/seam quantity, not a resource's queue outcome --
#     so excluding it would credit MW CAISO's own ledger does not count. The
#     deliverability-clean alternative is also NOT CONSTRUCTIBLE on this basis:
#     its numerator is published per tranche but its nameplate denominator is
#     not, and no CAISO-resource-ID -> EIA-860 crosswalk exists in this repo.
#     The whole-class ratio is the only construction both of whose terms are
#     measured, which is why it is the one adopted.
#   * FORWARD ADMISSIBILITY (rule 13 [R-MEASURED]): both terms regenerate for a
#     forward year from published sources on annual cycles, and the ratio
#     responds to changed conditions (it moves as the fleet's duration mix,
#     degradation and deliverability resolution move). It is an accreditation
#     RULE, not a model outcome, and nothing in it is fitted to a residual.
#
# MEASURED CONTEXT FOR THE MAGNITUDE, so the number is not read as a fudge: the
# CAISO battery fleet's REAL duration mix (EIA-860, MW-weighted: 72.9 % at ~4 h,
# 21.3 % under 2.5 h, energy-weighted mean 3.43 h) puts the GENERIC NREL/E3
# table at 0.5589 -- BELOW the 0.6875 the synthetic 70/25/5 forecast mix
# produces. The gap to CAISO's realized 0.8651 is therefore NOT a duration-mix
# artifact; it is CAISO's accreditation METHODOLOGY, which derates a
# dispatchable resource by demonstrated capability and not by duration at all.
# Using the real mix in a by-duration table would have made the error WORSE,
# which is the measurement that settles the §6.1 reconciliation question.
STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO: dict[str, float] = {
    "CAISO": 13_365.0 / 15_448.4,  # = 0.865138; see the derivation above.
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
#
# CAISO IS DELIBERATELY ABSENT, AND THE ASSUMPTION IS STATED RATHER THAN
# INVENTED (FFR-4E, adjudicating FFR-4D §7 D-4: "CAISO's storage ELCC portfolio
# dilution is a hard 1.0 -- a much larger assumption at 15,450 MW than at
# 8,000"). The published CAISO/CPUC sources were examined for a portfolio
# dilution object at citation quality and NONE qualifies:
#   * The committed E3/Astrape "Incremental ELCC Study"
#     (data/raw/capacity-market/elcc/caiso/caiso.csv) publishes MARGINAL
#     tranche ELCCs, not a fleet-average. Its 4-hour series is also NON-
#     MONOTONE in penetration (96.3 -> 90.7 -> 75.1 @1,759 MW -> 76.6 @4,123
#     -> 74.0 @6,553 -> 76.5) and its axis is CUMULATIVE MW *ADDED SINCE A
#     BASELINE*, not total installed MW -- a different quantity from the
#     `existing_storage_mw` this dilution is indexed on. Fitting a portfolio
#     line through a non-monotone marginal series on an incompatible axis
#     would be inventing a curve, which rule 5 [R-NO-MAGIC] and rule 14's
#     misalignment clause both refuse. The README on that intake already
#     records why the marginal study cannot serve as a whole-fleet ledger
#     credit; this is the same finding for the same reason.
#   * CAISO's SLRA Table 1.1 publishes ONE realized point, not a curve.
# So the factor stays 1.0 for CAISO, which is EXACTLY RIGHT AT THE REFERENCE
# FLEET and increasingly generous above it: the whole-class ratio in
# STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO is CAISO's REALIZED, ALREADY-DILUTED
# fleet-average at 15,448 MW installed, so applying any further dilution at that
# fleet size would DOUBLE-DERATE it. THE STATED CAVEAT: above ~15.4 GW a
# forecast credits new CAISO storage at the accreditation its 2026 fleet
# realized, with no penetration compression. That assumption runs IN FAVOUR of
# accredited capacity (it makes adequacy look better, not worse), and it is a
# named open item rather than a modeled effect. A published CAISO/CPUC
# portfolio-ELCC-vs-penetration series would close it; until one exists, a
# stated assumption beats an invented curve.
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
#
# CITATION CORRECTED 2026-08-07 (caiso-179). This block previously read
# "Source: modeling simplification grounded in NREL ATB augmentation costs and
# LFP warranty cycle life; tunable." BOTH halves of that attribution are wrong,
# and the correction is recorded rather than left standing (rule 5
# [R-NO-MAGIC]):
#   * NREL ATB 2024 and its own storage basis (Cole & Karmakar, NREL/TP-6A40-
#     85332, and the 2025 update 93281) publish NO per-MWh augmentation cost and
#     NO cycle life. They do the OPPOSITE: "assume no variable O&M (VOM) costs.
#     All operating costs are instead represented using fixed O&M (FOM) costs.
#     The FOM costs include battery augmentation costs, which enables the system
#     to operate at its rated capacity throughout its 15-year lifetime" (ATB 2024
#     Utility-Scale Battery Storage). There is no ATB augmentation table to read.
#   * No primary, named, public LFP *warranty* document was locatable; the public
#     record is vendor summaries quoting ranges (4,000-10,000 cycles, 70-80 %
#     end-of-life retention), which identifies nothing.
# The ONE primary source that does publish a complete (cycles, retention) pair
# is PNNL-33283 Table 4.2 (LFP, end of life at 60 % of rated energy). Combined
# with the ATB's own energy-vs-power cost share for this tech (0.742426,
# recovered EXACTLY from ATB's published duration construction), it implies an
# equivalent fraction of 0.309-0.387 at the committed ``cycles`` -- i.e. this
# 0.25 is 19-35 % LOW, not high.
#
# THE VALUE IS DELIBERATELY LEFT AT 0.25. caiso-179 pre-registered that an
# identified-but-refuted result changes nothing (BRANCH III-R): the implied
# dispatch adder is $28.00-$35.00/MWh, refuted twice over in CAISO (caiso-101's
# solved +/-15 % throughput guard at $14.25; caiso-176's revealed-conduct
# reading), and the identification still carries a selectable depth-of-discharge
# row, so it is not a clean replacement either. Re-pricing this constant is a
# FORECAST-lane act with six-ISO reach (it feeds only the storage new-entry
# screen at storage.py::estimate_storage_revenue, never the LP objective and
# never a backcast) and is chartered there, not taken by a CAISO backcast
# session. Derivation + gates: results/calibration/FINDING-caiso179-degradation-
# split-2026-08-07.md, instrument scripts/probes/_caiso179_degradation_split.py,
# record results/calibration/_caiso179_degradation_split.json.
STORAGE_DEGRADATION_REPLACEMENT_FRACTION: float = 0.25

# State renewable-portfolio-standard floors (RENEWABLE-tier fraction) by ISO
# and year. Every trajectory is the statute's (or the load-weighted blend of
# member states') RENEWABLE tier — the wind+solar-analogue obligation the RPS
# LP row enforces. Nuclear-counting clean/carbon-free/zero-emission tiers
# (CLCPA 100x40, SB 100 zero-carbon, MA CES, MN/MI carbon-free) do NOT belong
# on these trajectories (FFR-7B Arm 1; FFR-6B §8) — they are a separate
# clean-tier row family (FFR-6B §6.3). Per-ISO statutory citations in each
# block; eligible generation per row: RPS_ELIGIBLE_FUELS_BY_ISO below.
#
# AS-OF STATUS (FH-2, hindcast-forward plan §4 row 14). policy.rps.get_rps_target
# edge-holds below the first knot, so any year before an ISO's earliest knot
# receives that knot's target. Only CAISO carries historic (pre-2026) knots
# today, from the statute itself (see its block). The other five ISOs' earliest
# knot is still 2026, so a forward-lane run of a historic year (T1-H / T1-X /
# T1-FF are all mode="forecast") receives the 2026 target — an as-of violation
# that is DISCLOSED, not fixed here, because their 2026 knots are not published
# scalars but this repo's own load-weighted blends of per-state renewable-tier
# schedules (see the PJM/MISO blocks): a historic knot means re-blending each
# state's THEN-CURRENT schedule on that year's load weights, which is a cited
# derivation (a bounded FH-3-style intake), never an interpolation of the 2026
# blend. Backcast keepers are unaffected in every case — pipeline.backcast_config
# sets rps_enabled=False, so no backcast builds an RPS row.
STATE_RPS_FLOORS: dict[str, dict[int, float]] = {
    "ERCOT": {2026: 0.0, 2030: 0.0, 2040: 0.0, 2045: 0.0},  # No binding state RPS floor
    "CAISO": {  # CA RPS renewable tier (Pub. Util. Code §399.15(b)(2))
        # HISTORIC (as-of) knots, FH-2: before these landed the earliest knot was
        # 2026, and get_rps_target edge-holds below the first knot, so EVERY
        # pre-2026 year in a forward-lane run (T1-H / T1-X / T1-FF hindcast, all
        # mode="forecast") received the 2026 target — a 2021 solve compelled to
        # a 50 % clean share five years before the law required it
        # (hindcast-forward plan §4 row 14). Both knots are the STATUTORY
        # procurement targets in force at that date, not an interpolation:
        #   2021 → 33 %: SB X1-2 (2011), Pub. Util. Code §399.15(b)(2)(B), "33 %
        #     of retail sales by December 31, 2020" — the standing requirement
        #     through compliance period 4 (2021-2024).
        #   2024 → 44 %: SB 100 (2018), same section — "44 % by December 31,
        #     2024" (its next interim knots are 52 % by 2027 and 60 % by 2030,
        #     already bracketed by the 2026/2030 knots below).
        # Rule 13 admissible: a published policy parameter that regenerates for
        # any year from the statute and responds to conditions. Backcast keepers
        # are UNAFFECTED — pipeline.backcast_config sets rps_enabled=False, so no
        # backcast builds an RPS row at all; and every knot at/after 2026 is
        # untouched, so plain 2026+ forecasts are byte-identical.
        2021: 0.33,
        2024: 0.44,
        2026: 0.50,
        2030: 0.60,
        # FFR-7B Arm 1 (rule 14 [R-ACCURATE]; FFR-6B §8.1): the former
        # 2040: 0.80 / 2045: 1.00 knots were SB 100's ZERO-CARBON path
        # (§454.53, as amended by SB 1020: 90% 2035 / 95% 2040 / 100% 2045
        # — counts large hydro and nuclear), spliced onto this RENEWABLE
        # (RPS) row mid-trajectory. The RPS itself is 60% by 2030 and "not
        # less than 60 percent" for ALL SUBSEQUENT YEARS (Pub. Util. Code
        # §399.15(b)(2)(C), verified verbatim 2026-08-06), so the renewable
        # row plateaus at 0.60; the zero-carbon tier is a separate
        # clean-tier row family (FFR-6B §6.3), never a widening of this row.
        # Eligible set: RPS_ELIGIBLE_FUELS_BY_ISO (geothermal/biomass count).
        2040: 0.60,
        2045: 0.60,
    },
    "NYISO": {  # NY CLCPA renewable tier — 70% renewable by 2030 (PSL §66-p)
        # FFR-7B Arm 1 (rule 14 [R-ACCURATE]; FFR-6B §8.1): the former
        # 2040/2045 knots (1.00) encoded the CLCPA's 100%-by-2040
        # ZERO-EMISSION standard (PSL §66-p(2)(b), nuclear-counting) on this
        # RENEWABLE row — with a wind+solar-only eligible set, that pinned
        # the row's dual at the ACP ceiling for the whole horizon. The
        # statutory RENEWABLE target (§66-p(2)(a)) is 70% by 2030 and NO
        # post-2030 renewable percentage exists in the statute (verified
        # against PSL §66-p text, 2026-08-06), so the renewable row plateaus
        # at 0.70. The zero-emission tier is a separate clean-tier row family
        # (FFR-6B §6.3) — never a widening of this row. The 2026 knot is the
        # pre-existing Tier-1 procurement-ramp interpolation, untouched.
        # Eligible set: RPS_ELIGIBLE_FUELS_BY_ISO (existing hydro counts).
        2026: 0.40,
        2030: 0.70,
        2040: 0.70,
        2045: 0.70,
    },
    "NEISO": {
        # New England load-weighted NEW-RENEWABLE tier blend (Class I / RES
        # analogue — the wind+solar-tier convention shared with PJM/MISO).
        # FFR-7B Arm 1 (rule 14 [R-ACCURATE]; FFR-6B §8.1): the former knots
        # (.30/.45/.70/.80) were self-described as a "MA Clean Energy
        # Standard + regional state CES blend" — the MA CES (225 CMR 25.00)
        # is the NUCLEAR-COUNTING clean tier, not the renewable tier, so the
        # out-year knots overstated the wind+solar obligation and pinned the
        # row's dual at the ACP ceiling. Corrected to the per-state
        # new-renewable-tier schedules (each verified against statute text,
        # 2026-08-06), blended on the ISO-NE state load shares the ACP block
        # already carries (MA .48 / CT .24 / NH .09 / ME .09 / RI .06 /
        # VT .04):
        #   MA Class I (G.L. c.25A §11F, 2021 c.8): +3%/yr 2025-29, +1%/yr
        #     after → 30% 2026, 40% 2030, 50% 2040, 55% 2045.
        #   CT Class I (CGS §16-245a / PA 18-50): 32% 2026 → 40% 2030,
        #     plateaus (no statutory increase after 2030).
        #   RI RES (R.I.G.L. §39-26-4, 2022 amendment): 41% 2026, 72% 2030,
        #     100% by 2033 and thereafter.
        #   ME Class I+IA (35-A M.R.S. §3210, LD 1494; LD 1868 (2025)
        #     extension): 33% 2026, 50% 2030, 60% by 2040 and thereafter.
        #   NH (RSA 362-F:3): Class I 15% + Class II 0.7% flat from 2025 —
        #     0.157 at every knot (no escalation).
        #   VT (30 V.S.A. §8005, Act 179 2024): new-renewable analogue
        #     (Tier II distributed + Tier IV new in-region) ≈ .07/.14/.40/.40
        #     — Tier I is EXCLUDED as misaligned (it counts existing large
        #     hydro incl. HQ imports, rule 14 exception); VT is 4% of load,
        #     so its ±20 pp tier-attribution uncertainty moves the blend
        #     < 1 pp (below the rounding grain).
        # Blend: 2026 .292, 2030 .396, 2040 .480, 2045 .504 — stored rounded.
        # Tier 3 (calibration); a per-state re-blend on refreshed load
        # weights is a bounded intake follow-up. The nuclear-counting MA
        # CES/state clean tiers leave this row (clean-tier family, FFR-6B
        # §6.3). Eligible set: RPS_ELIGIBLE_FUELS_BY_ISO (offshore wind —
        # the region's dominant Class I compliance build — now counts).
        2026: 0.29,
        2030: 0.40,
        2040: 0.48,
        2045: 0.50,
    },
    "PJM": {
        # PJM has no single ISO-wide standard: this is the PJM-load-weighted
        # blend of its member states' RPS *renewable-tier* obligations (the
        # wind+solar analogue — Class I / Tier I incl. solar, NOT the
        # clean-energy tiers that count nuclear), so a share of PJM load in
        # low/no-RPS states (PA/OH flat ~8%, WV/KY/TN/IN none) dilutes the
        # aggressive states (NJ/MD 50% by 2030, IL 40%, DC 87%, VA ~37%,
        # MI 40%). Blended ~18.5% (2026) → 23% (2030) → 30% (2040) → 33%
        # (2045). Consistent with the other ISOs' convention (the full
        # renewable target is applied as the wind+solar floor; the tiers'
        # small biomass/landfill/hydro share is folded in). Rule 13 admissible
        # (policy parameter, forward-reproducible, relaxes as VRE builds).
        # Tier 3 (calibration). Load weights REFRESHED to the primary Monitoring
        # Analytics "Percentage of PJM Load by State" 2024 annual file
        # (PJM_Load_by_State_2024_20250716.XLS; FF-1E-policy 2026-07-19):
        # OH 20.1 / PA 18.9 / VA 17.6 / IL 11.6 / NJ 9.6 / MD 7.8 / WV 4.6 /
        # KY 3.0 / IN 2.75 / DE 1.5 / DC 1.25 / MI 0.56 / NC 0.55 / TN 0.21 %.
        # (Corrects the prior approximate weights, which understated OH 14→20
        # and VA 14→18 and OMITTED KY 3% — all low/no-RPS load.) Re-blending the
        # per-state renewable-tier schedules (PJM-EIS "Comparison of RPS Programs
        # in PJM States", 4/15/2025) on these corrected weights reproduces the
        # 2030 knot at ~0.22 — within Tier-3 tolerance of the 0.23 below, KEPT
        # (the OH/KY-down and VA-up corrections offset). Knots stay approximate;
        # a full per-state re-blend is a bounded intake follow-up.
        2026: 0.185,
        2030: 0.23,
        2040: 0.30,
        2045: 0.33,
    },
    "MISO": {
        # Like PJM, MISO has no single ISO-wide standard: this is the
        # MISO-load-weighted blend of its member states' RPS *renewable-tier*
        # obligations (the wind+solar analogue — the renewable standard, NOT the
        # nuclear-counting clean/carbon-free tiers), so the large share of MISO
        # load in no-RPS states dilutes the aggressive ones. It is markedly
        # lower than PJM because MISO-South (AR/LA/MS/E-TX, 27.1% of load) and
        # MISO-Indiana (IN/KY, 13.4%) carry NO binding RPS at all, and
        # MISO-Plains is mostly no-mandate Iowa. Rule 13 admissible (policy
        # parameter, forward-reproducible, relaxes as VRE builds). Tier 3
        # (calibration).
        #
        # Rule 5 reconciliation (RPS is state-level; MISO is the model zone):
        # the blend is anchored on THIS MODEL'S OWN measured MISO zone load
        # shares (iso_configs.build_miso_config, from EIA-930 sub-BA data,
        # summing to 1.0) — West 0.1466 (MN/ND/SD/MT), Plains 0.1385 (IA/MO),
        # Illinois 0.0676 (IL-Ameren), Indiana 0.1340 (IN/KY), East 0.2422
        # (WI/MI), South 0.2711 (AR/LA/MS/E-TX). Each multi-state zone is split
        # to its member states by EIA-861 2023 retail sales restricted to the
        # MISO-served portion (MN≈.77/ND/SD/MT of West; IA≈.57/MO of Plains;
        # MI≈.57/WI of East). Per-state renewable-tier trajectories:
        #   MN — 55% renewable by 2035 (2023 HF7 / Minn. Stat. §216B.1691; the
        #     80/90/100% 2030-40 targets are CARBON-FREE incl. nuclear/hydro,
        #     excluded), ramped from the pre-2023 25%-by-2025 standard:
        #     .26→.40→.55→.55.
        #   MI — 50% renewable by 2030, 60% by 2035 (2023 PA 235 / SB 271; the
        #     100%-clean-by-2040 CES is nuclear-counting, excluded), ramped from
        #     the prior 15%-by-2021: .35→.50→.60→.60.
        #   IL (Ameren/MISO portion only; ComEd is PJM) — 40% by 2030, 50% by
        #     2040 (CEJA / 20 ILCS 3855): .25→.40→.50→.50.
        #   MO 15% by 2021 (RSMo §393.1030) and MT 15% — flat .15. WI 10%
        #     (Wis. Stat. §196.378) — flat .10. IA (105-MW nominal mandate, no
        #     %), IN/ND/SD (voluntary goals), AR/LA/MS/KY/E-TX (no RPS) — 0.
        # Zone-blended → MISO-wide: 2026≈0.114, 2030≈0.161, 2040≈0.198, held
        # flat to 2045 (every binding state's renewable tier plateaus by 2035-40;
        # further decarbonization is the excluded clean tier). Knots stored
        # rounded; a full per-utility re-blend is a bounded intake follow-up.
        2026: 0.11,
        2030: 0.16,
        2040: 0.20,
        2045: 0.20,
    },
    # SPP (registered 2026-09-06, lane SPP-20; owner ruling P1 block, r#2):
    # ALL-ZERO on the ERCOT precedent, with the REAL row ROUTED to the
    # forecast lane (docs/multi-iso/spp-data-audit.md §5 row 13). Why zero is
    # honest for the backcast: pipeline.backcast_config sets rps_enabled=False,
    # so no backcast builds an RPS row and SPP's first keeper is unaffected.
    # Why it is ARGUABLE for the forecast, stated rather than buried: the
    # footprint's statutes are mostly voluntary or repealed — KS mandate
    # REPEALED to a voluntary 20 %-of-peak goal (House Sub. for SB 91, 2015,
    # effective 2016-01-01); OK / ND / SD voluntary goals; NE none (public
    # power); TX 5,880 MW goal long met; AR / LA none; MN / IA / MT shares
    # immaterial (75 / 539 / 168 MW) — but TWO are real renewable-tier
    # mandates on IOUs: MO 15 % by 2021 (Prop C, RSMo §393.1030) and NM's
    # Energy Transition Act 2019 (SB 489: 50 % renewable by 2030, 80 % by
    # 2040 for IOUs; SPS is an NM IOU). A load-weighted SPP-wide blend of
    # those two is a cited derivation the capx director charters with card
    # P8 (SPP-60), never a value W2 invents. No STATE_RPS_ACP row follows,
    # exactly as ERCOT has none.
    "SPP": {2026: 0.0, 2030: 0.0, 2040: 0.0, 2045: 0.0},
    # NWPP (registered 2026-09-14, lane NWPP-20): an all-zero block on the
    # SPP precedent, so no backcast builds an RPS row and the first keeper is
    # unaffected — and it is MORE arguable for the forecast than SPP's, stated
    # rather than buried. The footprint spans seven regimes that cannot be
    # expressed as one ISO-level fraction without averaging across a legal
    # boundary (docs/multi-iso/nwpp-data-audit.md §7.4): WA's Clean Energy
    # Transformation Act (RCW 19.405 — coal-free, then GHG-neutral, then
    # 100 % clean; a CES, not an RPS; 31.7 GW of the footprint), OR HB 2021
    # (ORS 469A.400-.475, an emissions-reduction schedule to 100 %), NV's
    # NRS 704.7801-.7828 percentage RPS, UT's non-binding cost-conditioned
    # goal (UCA 54-17-601), MT's modest MCA 69-3-2001 RPS, and NO mandate at
    # all in WY and ID (15 % of nameplate). The obligations attach to RETAIL
    # providers, not balancing authorities — PacifiCorp serves six states
    # under six regimes from one system. The numeric schedules were NOT
    # transcribed by NWPP-12 (a mis-transcribed percentage is exactly the
    # magic number rule 5 forbids); a load-weighted blend is a cited
    # derivation for the capx director with the W6 card (N9), never a value
    # W2 invents. No STATE_RPS_ACP row follows, exactly as ERCOT and SPP.
    "NWPP": {2026: 0.0, 2030: 0.0, 2040: 0.0, 2045: 0.0},
    # SOCO (registered 2026-09-14, lane SOCO-20): NO binding state RPS floor
    # in any footprint state — and this is an ANSWERED zero, not a blank.
    # DSIRE: "Alabama does not have a renewable energy portfolio standard or
    # a voluntary renewable energy target" (programs.dsireusa.org/system/
    # program/al); Georgia has no RPS and no voluntary target (.../ga);
    # Mississippi has no RPS and therefore no SREC market (docs/multi-iso/
    # soco-data-audit.md §5 row 10). Georgia's solar build (5.0 GW) is
    # IRP-certificated procurement, not a portfolio standard. No STATE_RPS_ACP
    # row follows, exactly as ERCOT and SPP have none. Backcasts set
    # rps_enabled=False regardless.
    "SOCO": {2026: 0.0, 2030: 0.0, 2040: 0.0, 2045: 0.0},
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
# Tier 3 (calibration). Sources — per-state ACP schedules re-verified against
# primary regulators/statutes (FF-1E-policy 2026-07-19):
#   CAISO — CA RPS non-compliance penalty $50/MWh per deficient REC (Pub. Util.
#     Code §399.15; CPUC RPS enforcement), the effective ACP ceiling for SB 100
#     compliance. VERIFIED CURRENT (unchanged).
#   NYISO — NY Clean Energy Standard Tier 1. NYSERDA ELIMINATED the fixed Tier 1
#     ACP after compliance year 2024 ("no ACPs will be collected for compliance
#     year 2025 onward"); the post-2024 Tier 1 obligation is a cost-recovery
#     charge (NYSERDA net REC-procurement cost ÷ statewide load), not a $/MWh
#     buyout. $40/MWh is KEPT as the forward REC-price-ceiling proxy — the
#     historical Tier 1 ACP order of magnitude, consistent with index-REC net
#     cost (NYSERDA/PSC Case 15-E-0302). Tier 3; a strike-price-derived ceiling
#     is a bounded follow-up.
#   NEISO — load-weighted New England Class I / renewable-tier ACP. REFRESHED:
#     MA Class I RPS ACP is $40/MWh (Compliance Year 2023+, then CPI-adjusted —
#     225 CMR 14.08(3)(a)(2): a 2021 reform that RESET the rate DOWN a $60/$50/
#     $40 glide from the pre-2021 CPI-escalated ~$67 series; the old $67.62 was
#     stale). Blended with CT Class I $55 (Conn. Gen. Stat. §16-245a), NH Class I
#     $62.24 (2024)/$63.29 (2025) (NH DoE, ½-CPI-adjusted), ME Class I $50
#     statutory max (35-A M.R.S. §3210), RI RES $83.37 (2024, RI PUC) over ISO-NE
#     state load shares (MA ≈48 / CT ≈24 / NH ≈9 / ME ≈9 / RI ≈6 / VT ≈4 %) ⇒
#     ≈$50/MWh regional Class I ACP (was $65, stale on the old MA input).
#   PJM — PJM-load-weighted blend of member-state Tier-I (non-solar) ACPs:
#     PA $45 (Tier I, 73 Pa. Code §75), DC $50 & NJ $50 (Class I), VA ~$47
#     (2021 $45 +1%/yr, Code §56-585.5), MD ~$30 declining to $22.35 by 2030
#     (MD PSC RPS report, CY2024), DE $25, OH $45; IL/NC/KY are cost-capped or
#     RPS-free with no ACP. Load-weighted on the corrected weights above ≈ $45,
#     unchanged. Source: PJM-EIS "Comparison of RPS Programs in PJM States"
#     (4/15/2025).
#   MISO — $30/MWh, a deliberately LOW forward REC-price-ceiling proxy (cf. the
#     NYISO note: a proxy kept where no liquid statutory buyout governs). Unlike
#     PJM/New England, MISO has NO robust current $/MWh ACP: its binding states
#     enforce via budget/rate-cap/physical-compliance, not a high buyout —
#     Illinois's ARES ACP (16-115D) was RETIRED under CEJA's centralized IPA
#     procurement, Missouri caps RPS cost at 1%/yr of rates and excuses the
#     obligation above it (RSMo §393.1030), and MN/MI compliance is physical
#     with PUC/MPSC-set penalties, no fixed rate. With abundant Midwest wind,
#     compliance-REC clearing prices run well below the coastal ISOs, so the
#     REC-market ceiling here is genuinely soft. $30 (< PJM $45, < NEISO $50)
#     anchors on current IPA Adjustable-Block / utility-scale REC clearing
#     prices (low-$30s/MWh) as the marginal buyout proxy. Tier 3; a per-utility
#     REC-price-ceiling refinement is a bounded follow-up.
# ISOs without a STATE_RPS_FLOORS entry (ERCOT) need no ACP — their RPS row is
# never built, so the escape column is absent and the LP is byte-identical.
STATE_RPS_ACP: dict[str, float] = {
    "CAISO": 50.0,
    "NYISO": 40.0,
    "NEISO": 50.0,  # was 65.0 — stale MA Class I input ($67.62→$40); see above
    "PJM": 45.0,
    "MISO": 30.0,  # low forward REC-price-ceiling proxy — see note above
}

# Statute-defined RPS-row eligible fuel sets by ISO (FFR-7B Arm 1; FFR-6B §8).
#
# Each entry names the fuel classes (FUEL_TYPE_MAP names) the ISO's governing
# *renewable-tier* statute counts toward its target. The RPS LP row counts
# wind/solar via their zone columns and resolves every other name to the
# matching thermal-block generator columns (model.lp.rows.
# _resolve_rps_eligible_gen_idx) — the eligible set is data, never a hardcoded
# class tuple at the row builder (FFR-6B §6.3(2)). Rule 14 [R-ACCURATE]: the
# previous universal wind+solar-only convention under-counted what the
# statutes count (NYISO by 20.2 pp, CAISO by 7.1 pp — FFR-6B §8.2, measured
# eGRID 2023 shares of ISO load), pinning those rows' duals at the ACP
# ceiling for the whole horizon — a mechanism-generated $40-50/MWh entry
# subsidy with no statute behind it (FFR-6B §8.3). Nuclear is NEVER eligible
# here (CX-6a): a clean/carbon-free tier that counts nuclear is a separate
# row family (FFR-6B §6.3), not a widening of the renewable row — the row
# builder refuses it by name.
#
# Sources (rule 5):
#   NYISO — NY PSL §66-p(1)(b) (CLCPA): "renewable energy systems" = solar,
#     on-land and offshore wind, HYDROELECTRIC (no new-build restriction —
#     existing large hydro, NYPA's Niagara/St. Lawrence, counts toward the
#     70x30 target), geothermal, tidal/wave/ocean thermal, non-fossil fuel
#     cells. Biomass/biogas are NOT in the statutory definition (verified
#     against §66-p text 2026-08-06 — legacy PSC Tier 1 orders admitted some
#     biomass, but the statute does not; FFR-6B §8.2's parenthetical
#     over-included it). Model classes: + hydro, offshore_wind.
#   CAISO — Pub. Res. Code §25741(a) (RPS-eligible renewable energy
#     resource): wind, solar, GEOTHERMAL, BIOMASS, small hydro ≤30 MW.
#     Model classes: + geothermal, biomass, offshore_wind. Small hydro ≤30 MW
#     is statutorily eligible but EXCLUDED here as misaligned to our
#     representation (rule 14 exception): the fleet's single "hydro" class
#     aggregates small RPS-eligible hydro with large (>30 MW) NON-eligible
#     hydro (~10% of CA load), so counting the class literally would
#     over-count by an order of magnitude more than the ~1 pp the small-hydro
#     share adds; the residual under-count is within the folded-in tolerance
#     adjudicated sound for PJM/MISO (FFR-6B §8.2).
#   NEISO — MA Class I (225 CMR 14.05): new wind (on/offshore), solar,
#     small hydro, low-emission biomass, landfill gas; EXCLUDES existing
#     large hydro (and the HQ_import node is not in-region generation).
#     Model classes: + offshore_wind (the region's dominant Class I
#     compliance build); small-hydro/biomass share stays folded in
#     (~3.8 pp, FFR-6B §8.2 — same convention as PJM/MISO).
#   PJM / MISO — NO entry (wind+solar-only row unchanged): their blends'
#     "small biomass/landfill/hydro folded in" convention is measured
#     accurate to within ~2 pp (FFR-6B §8.2) — adjudicated sound.
#   ERCOT — no RPS row is ever built (all-zero STATE_RPS_FLOORS entry).
RPS_ELIGIBLE_FUELS_BY_ISO: dict[str, tuple[str, ...]] = {
    "NYISO": ("wind", "solar", "offshore_wind", "hydro"),
    "CAISO": ("wind", "solar", "offshore_wind", "geothermal", "biomass"),
    "NEISO": ("wind", "solar", "offshore_wind"),
}

# The MISO "Midwest footprint" REC-eligibility region: every model zone except
# MISO-South. Delivery-based state standards (MN §216B.1691's
# delivered-to-Minnesota-retail construction; WI/MO likewise) accept
# certificates generated anywhere in MISO's Midwest region, while MISO-South
# (AR/LA/MS/E-TX — no binding RPS, and separated by the RDT) is outside every
# Midwest state's eligibility geography (FFR-6B §2.1).
MISO_RPS_MIDWEST_FOOTPRINT_ZONES: tuple[str, ...] = (
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
)

# Per-state MISO RPS compliance regions (FFR-7B Arm 2 / FFR-6B E-1).
#
# MISO is the ONE ISO where the single ISO-wide RPS row is wrong: a single row
# silently asserts free intra-ISO REC trade, which is TRUE in PJM/NEISO/NYISO/
# CAISO (footprint-wide REC products / one obligated state) and FALSE in MISO —
# Michigan's credits must come from systems "located within this state"
# (MCL 460.1029, tracked in MIRECS), Illinois's CEJA obligation is discharged
# through centralized IPA procurement, and Minnesota's §216B.1691 standard is a
# delivered-to-MN-retail obligation. Measured consequence (FFR-6B §2.2):
# MISO-East owes 0.328 of zone load against 0.081 measured VRE (2030) while
# MISO-Plains runs a 41.5 pp surplus — Iowa's surplus paying Michigan's bill,
# which Michigan's statute forbids. The K-row generalization gives each state
# standard its own constraint row with its own eligibility mask.
#
# EVERY number below is copied from the cited derivation already recorded in
# the STATE_RPS_FLOORS["MISO"] comment block above (FFR-7B §6.1(7): "copy, do
# not re-derive") — per-state renewable-tier trajectories at the same
# 2026/30/40/45 knot convention, and within-zone state load shares from
# EIA-861 2023 retail sales restricted to the MISO-served portion. Rule 5
# [R-NO-MAGIC] / rule 13 [R-MEASURED]: statutory levels + measured load
# shares, zero fitted parameters.
#
#   MN — Minn. Stat. §216B.1691 (2023 HF7), 55% renewable by 2035; MN ≈ .77 of
#     MISO-West load. Eligibility: the Midwest footprint (delivery-based
#     standard, self-supplied by vertically-integrated utilities across MISO
#     Midwest).
#   MI — 2023 PA 235 (SB 271) / MCL 460.1028; 50% by 2030, 60% by 2035;
#     MI ≈ .57 of MISO-East load. Eligibility: MISO-East ONLY — MCL 460.1029
#     restricts credits to systems "located within this state" (MIRECS, a
#     Michigan-only registry). This restriction IS the E-1 defect's core.
#   WI — Wis. Stat. §196.378, flat 10%; WI ≈ .43 of MISO-East load.
#     Eligibility: Midwest footprint (WI accepts regional RECs).
#   IL — CEJA (P.A. 102-0662) / 20 ILCS 3855, Ameren/MISO portion; 40% by
#     2030, 50% by 2040. Whole zone (share 1.0 — MISO-Illinois IS the IL-Ameren
#     footprint). Eligibility: MISO-Illinois (the CEJA IPA-procurement narrow
#     reading, documented; FFR-6B §3.4 permits the wider adjacent reading — the
#     narrow one is taken so the row never silently re-imports the Iowa
#     surplus the family exists to fence off).
#   MO — RSMo §393.1030, flat 15% (cost-capped); MO ≈ .43 of MISO-Plains load.
#     Eligibility: Midwest footprint.
#   MT — EXCLUDED (FFR-6B §1.4): MN ≈ .77 of MISO-West is cited but the .23
#     ND/SD/MT residual is not decomposed; MT's 15% standard is bracketed at
#     ±0.0345 on the West target by MT taking none or all of it. Recorded as
#     the open one-EIA-861-line intake; excluding it is the conservative
#     (obligation-understating) side of the bracket.
#   IA / ND / SD / IN / KY / AR / LA / MS / E-TX — no binding standard, no row.
#
# The rows' ONLY output is a price (each row's dual = that compliance market's
# REC price, capped by its ACP escape). E-1 NEVER ACQUIRES A BUILD LIMB
# (FFR-6B §5.3): a force-build limb would stack against the FFR-5E procurement
# channel — the rule-19 [R-ONE-MECH] failure FFR-5B already refused.
MISO_RPS_COMPLIANCE_REGIONS: dict[str, dict] = {
    "MN": {
        "obligated_zone": "MISO-West",
        "obligated_load_share": 0.77,
        "floors": {2026: 0.26, 2030: 0.40, 2040: 0.55, 2045: 0.55},
        "eligible_zones": MISO_RPS_MIDWEST_FOOTPRINT_ZONES,
    },
    "MI": {
        "obligated_zone": "MISO-East",
        "obligated_load_share": 0.57,
        "floors": {2026: 0.35, 2030: 0.50, 2040: 0.60, 2045: 0.60},
        "eligible_zones": ("MISO-East",),
    },
    "WI": {
        "obligated_zone": "MISO-East",
        "obligated_load_share": 0.43,
        "floors": {2026: 0.10, 2030: 0.10, 2040: 0.10, 2045: 0.10},
        "eligible_zones": MISO_RPS_MIDWEST_FOOTPRINT_ZONES,
    },
    "IL": {
        "obligated_zone": "MISO-Illinois",
        "obligated_load_share": 1.0,
        "floors": {2026: 0.25, 2030: 0.40, 2040: 0.50, 2045: 0.50},
        "eligible_zones": ("MISO-Illinois",),
    },
    "MO": {
        "obligated_zone": "MISO-Plains",
        "obligated_load_share": 0.43,
        "floors": {2026: 0.15, 2030: 0.15, 2040: 0.15, 2045: 0.15},
        "eligible_zones": MISO_RPS_MIDWEST_FOOTPRINT_ZONES,
    },
}

# Per-state MISO CLEAN/CARBON-FREE tier compliance regions (FFR-7B Arm 3 /
# FFR-6B E-2) — a SECOND, INDEPENDENT row family on the Arm-2 K-row
# machinery, never a widening of the renewable row (the renewable row keeps
# its statute's renewable eligibility; a state with both tiers gets TWO rows,
# which is what the statutes say — FFR-6B §6.3(1)).
#
# Adjudication (FFR-6B §6.2, measured eGRID 2023 at both grains): built
# ISO-wide the clean row is SLACK in every modelled year through 2040
# (-22.9 pp falling to -6.9 pp) — an inert mechanism; at the state-group
# grain it binds materially in two zones covering 39% of MISO load
# (MISO-West short 14.0 pp by 2030 rising to 29.4 pp by 2040; MISO-East
# short 21.7 pp by 2035 rising to 33.1 pp by 2040). Hence exactly two rows.
#
# Each row's QUALIFYING SET is per-statute DATA resolved against
# FUEL_TYPE_MAP (rule 18's spirit — never a hardcoded class tuple at the
# builder), because the statutes genuinely differ (FFR-6B §6.3(2)):
#   MN — Minn. Stat. §216B.1691 subd. 2g (2023 HF7): 80% carbon-free by 2030
#     (IOU; the .80 knot follows the FFR-6B §6.2 adjudication table) / 90% by
#     2035 / 100% by 2040. Carbon-free INCLUDES HYDROGEN AND BIOMASS →
#     nuclear, hydro, wind, solar, hydrogen_ct, hydrogen_ccgt, biomass.
#     Obligated: MN ≈ .77 of MISO-West (the same EIA-861 split as the
#     renewable row). Eligibility: Midwest footprint (same delivery
#     construction as its renewable tier).
#   MI — 2023 PA 235 (SB 271): 80% clean by 2035 — THE INTERIM KNOT MISSING
#     from the old code comment, the knot that makes MISO-East bind five
#     years earlier — / 100% by 2040. Clean = renewables + nuclear +
#     QUALIFIED CCS GAS (90% capture) → nuclear, hydro, wind, solar,
#     biomass, gas_cc_ccs. Obligated: MI ≈ .57 of MISO-East. Eligibility:
#     MISO-East ONLY (the same MCL 460.1029 in-state restriction as its
#     renewable tier).
#   IL — NO ROW, RECORDED AS THE NULL IT IS (FFR-6B §6.1): CEJA
#     (P.A. 102-0662) sets a state POLICY GOAL of 100% clean by 2050 plus
#     dated SOURCE-SIDE fossil-emission phase-outs — a different instrument,
#     not an LSE share obligation. A clean row for Illinois would invent an
#     obligation the statute does not impose.
#
# Trajectory convention: a clean tier imposes NOTHING before its first
# statutory compliance knot — policy.clean_tiers returns 0.0 for years
# strictly before the first knot (NOT the edge-hold used by the RPS
# trajectories, which would compel 80% carbon-free in 2026, four years
# before the law requires it). Interpolation between knots is linear, as
# everywhere else.
#
# FEASIBILITY ESCAPE (required — FFR-6B §6.3: "a 100%-by-2040 clean row MUST
# carry a feasibility escape; a hard row is an infeasibility bomb"): each row
# carries its own ACP-style escape column priced at STATE_RPS_ACP["MISO"]'s
# $30/MWh forward REC-price-ceiling proxy — reused, documented: neither MN
# nor MI publishes a $/MWh clean-tier buyout (MN/MI compliance is physical
# with PUC/MPSC-set penalties), so the same deliberately-low Midwest
# attribute-price ceiling proxy bounds the clean dual.
MISO_CLEAN_TIER_REGIONS: dict[str, dict] = {
    "MN": {
        "obligated_zone": "MISO-West",
        "obligated_load_share": 0.77,
        "floors": {2030: 0.80, 2035: 0.90, 2040: 1.00, 2045: 1.00},
        "eligible_zones": MISO_RPS_MIDWEST_FOOTPRINT_ZONES,
        "qualifying_fuels": (
            "nuclear",
            "hydro",
            "wind",
            "solar",
            "hydrogen_ct",
            "hydrogen_ccgt",
            "biomass",
        ),
    },
    "MI": {
        "obligated_zone": "MISO-East",
        "obligated_load_share": 0.57,
        "floors": {2035: 0.80, 2040: 1.00, 2045: 1.00},
        "eligible_zones": ("MISO-East",),
        "qualifying_fuels": (
            "nuclear",
            "hydro",
            "wind",
            "solar",
            "biomass",
            "gas_cc_ccs",
        ),
    },
}

# Annual interconnection queue caps (GW/yr) by ISO.
#
# Semantics: this is a *ceiling* on the total nameplate MW the economic
# new-entry screen (capacity_evolution.new_entry) and the reserve-margin
# adequacy backstop (capacity_evolution.adequacy) may build in a single
# forecast year -- the institutional/physical interconnection *throughput*
# limit, i.e. how much capacity can plausibly reach commercial operation
# (COD) per year. It is deliberately NOT the queue-*request* volume (which
# runs at 100s of GW/ISO and never all builds), and NOT a central-case
# forecast -- it caps the pace, so a value modestly above each ISO's
# demonstrated peak annual COD is correct. Rule-13 admissible: a published
# throughput ceiling that regenerates for any forecast year.
#
# Sourcing convention below: each cap is anchored to the ISO's cited recent
# peak annual COD (a measured throughput). Where a cap sits materially ABOVE
# demonstrated throughput it is a forward-ceiling *estimate* (driver: queue
# reform clearing backlog / offshore-wind pipeline bursts) and is LABELLED
# as such -- see docs/handoffs/queue-cap-citation-2026-07.md (rule 11
# follow-up; NYISO/NEISO strike-a-real-throughput-number is open there).
QUEUE_CAP_GW: dict[str, float] = {
    # ERCOT: CDR interconnection throughput; recent COD ~5-10 GW/yr (mostly
    # solar+storage). ERCOT Capacity, Demand & Reserves report (ercotcdr).
    "ERCOT": 12,
    # CAISO: Transmission Planning Process deliverability throughput; recent
    # COD ~4-8 GW/yr. CAISO 20-Year TPP / annual TPP.
    "CAISO": 8,
    # PJM: demonstrated peak annual COD ~8-10 GW in the 2015-2018 gas
    # build-out (2013-2017 added ~11 GW of gas CC alone; S&P: 2017 additions
    # led by gas-CC + renewables). Recent COD is backlog-depressed -- ~2 GW
    # (2023), 4.8 GW (2024), 2.8 GW (2025) -- but the reformed cluster ("Cycle")
    # process is clearing a large backlog (~63 GW queued for 2025-2028 review;
    # first cycle drew 220 GW of requests), so 10 GW/yr is a defensible forward
    # throughput ceiling at the demonstrated historical peak. CITED.
    # Sources: EIA Today-in-Energy id=37293 (PJM gas build-out); S&P Global
    # "PJM 2017 capacity additions"; PJM Inside Lines 2024/2025 year-in-review
    # (recent COD); Utility Dive "PJM ... less than 2 GW added" (728145).
    "PJM": 10,
    # MISO: recent COD 5.6 GW (2023), 7.5 GW (2024), ~26.8 GW over 2023-2025
    # (~9 GW/yr and rising, ~60% solar). 10 GW/yr forward ceiling sits just
    # above the demonstrated ~9 GW/yr throughput. CITED.
    # Source: MISO System Planning Committee "Resource Adequacy & Generator
    # Interconnection Queue Update" (2025-09/2025-12); MISO GI queue-cycle
    # results (misoenergy.org).
    "MISO": 10,
    # NYISO: measured COD throughput is SMALL -- ~2,274 MW of additions total
    # over 2019-2024 (~0.5 GW/yr; NYISO 2024 Gold Book / Power Trends). The
    # 4 GW/yr cap is a forward-ceiling ESTIMATE well above demonstrated
    # throughput, justified only by the CLCPA offshore-wind + downstate
    # pipeline able to commission in bursts (a single OSW project is ~1-2.5 GW).
    # LABELLED ESTIMATE -- not a measured throughput; see the handoff follow-up.
    "NYISO": 4,
    # NEISO: measured COD throughput is likewise SMALL (~0.5-1.5 GW/yr, mostly
    # solar + storage; ISO-NE Annual Markets Report Fig. 1-9). The 43 GW queue
    # is dominated by slow-moving offshore wind. The 4 GW/yr cap is a
    # forward-ceiling ESTIMATE above demonstrated throughput, driver = MA/RI/CT
    # OSW pipeline bursts. LABELLED ESTIMATE -- see the handoff follow-up.
    "NEISO": 4,
    # SPP (registered 2026-09-06, lane SPP-20): MEASURED. Demonstrated peak
    # annual all-technology COD in the EIA-860 2025 ER, BA SWPP, by `Operating
    # Year`: 4.125 GW (2016) over 2015-2025; 3.907 GW (2025) over 2021-2025
    # (series 3.533 / 3.237 / 2.091 / 1.150 / 3.907 GW for 2021-2025). 4.5
    # GW/yr is the smallest 0.5 GW step at or above the eleven-year peak —
    # this table's own convention, "modestly above demonstrated peak annual
    # COD"; the five-year window would give 4.0, and the longer window is
    # taken because SPP's 2016-2017 wind build (4.1 / 3.8 GW) is a
    # demonstrated throughput, not an outlier. Context, not a ceiling: the
    # end-2025 GI queue is ~149 GW (SOM 2025 §2.5, PDF pp. 54-55), ~35 GW of
    # it executed and on schedule (docs/multi-iso/spp-data-audit.md §5 rows
    # 12/12b). CITED.
    "SPP": 4.5,
    # NWPP (registered 2026-09-14, lane NWPP-20): smallest 0.5 GW step >= the
    # demonstrated all-technology peak annual COD on the WECC-admitted
    # footprint, 4.491 GW (2024; 2025: 3.471; 2015-2025 window; EIA-860 2025
    # ER Operating Year — the same identification ERCOT's own entry uses,
    # PRECOMMIT-nwpp-20 §3.7). CITED to the committed sheets, not a queue
    # report: the pool publishes no interconnection-queue total.
    "NWPP": 4.5,
    # SOCO (registered 2026-09-14, lane SOCO-20): MEASURED. Demonstrated peak
    # annual all-technology COD in the EIA-860 2025 ER, BA SOCO, by `Operating
    # Year`: 3.348 GW in 2023 (Barry A3 774.0 + Lowman Energy Center 732.7 MW
    # of gas CC, Vogtle 3 1,114 MW, 690 MW of solar, small rows) over both the
    # 2015-2025 series (0.192 / 0.760 / 0.466 / 0.049 / 0.701 / 0.734 /
    # 0.912 / 0.603 / 3.348 / 1.974 / 0.344 GW) and the 2021-2025 window.
    # 3.5 GW/yr is the smallest 0.5 GW step at or above it — this table's own
    # convention. 2024 (1.974: Vogtle 4 + 795 MW solar) is the second-largest
    # year, so the cap is not a single-plant artifact. CITED (docs/multi-iso/
    # soco-data-audit.md §5 row 9 for the basis; the step is this table's).
    "SOCO": 3.5,
}

# Per-technology annual interconnection queue caps (GW/yr) by ISO.
# Source: ERCOT CDR, CAISO TPP — approximate historical queue throughput by tech
# The sum of per-tech caps can exceed the ISO total cap (QUEUE_CAP_GW) — both bind independently.
QUEUE_CAP_PER_TECH_GW: dict[str, dict[str, float]] = {
    "ERCOT": {
        # Wind: UNCHANGED at 5.0 and still correct on the same record that
        # moved solar. Demonstrated peak annual ERCOT wind COD 2021-2025 is
        # 3.95 GW (2021) -- the cap sits 1.26x above its own peak, the same
        # multiplier solar's 5.0 carried at its 2021 vintage -- and wind
        # throughput then FELL (1.46 / 1.73 / 1.67 GW in 2023-2025), so this
        # cap does not bind. Measured in the same RC-DERIVE pass as solar
        # below (FINDING §1); deliberately NOT re-derived.
        "wind": 5.0,
        # Solar: 5.0 -> 8.0 GW/yr. A rule-23 re-derivation on a DATA change,
        # NOT a residual: the 2024 and 2025 CODs landed and moved the record
        # this cap claims to bound.
        #   Basis: demonstrated peak annual ERCOT solar COD over 2021-2025 =
        #   7.74 GW (2025). EIA-860 2025 Early Release, Balancing Authority
        #   Code = ERCO, nameplate AC; series 3.97 / 2.53 / 3.55 / 7.29 /
        #   7.74 GW. 8.0 is the smallest 0.5 GW step at or above that peak,
        #   which is this table's own documented convention (a cap set
        #   "modestly above demonstrated peak annual COD", see QUEUE_CAP_GW).
        #   Robustness: 7.5-8.5 GW across all five pre-registered windows x
        #   four identifications; no window, statistic or identification lands
        #   near 5.0. Defensible band 8.0-9.5 -- 8.0 is the conservative end,
        #   only 1.03x the demonstrated peak.
        #   Vintage: 5.0 WAS right for its own record. At the 2021-2023
        #   vintages the visible peak was 3.96-3.97 GW and 5.0 sat 1.26x above
        #   it; it went stale when 2024-2025 throughput roughly doubled.
        #   Rule 13: unchanged in kind -- still a published throughput ceiling
        #   that regenerates for any forward year, now at a current value.
        #   Source: docs/FINDING-rc-ercot-solar-queue-cap-2026-08-11.md
        #   (pre-registration d938f29, measurement 6e6e50b).
        #   ADOPTED by owner decision D-31, signed 2026-08-13 (owner sitting
        #   Addendum AT.1); adoption docs/handoffs/d31-adopt-2026-08-13.md.
        "solar": 8.0,
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
    # Eastern-ISO per-tech caps are ENGINEERING-JUDGMENT ESTIMATES: the cited
    # ISO-total throughput ceiling (QUEUE_CAP_GW, above) disaggregated by each
    # ISO's recent build mix -- solar/storage-led in PJM & MISO, offshore-wind-
    # weighted in NYISO & NEISO (EIA 2026 outlook: solar 51% / storage 28% /
    # wind 14% of planned US additions; LBNL "Queued Up" 2024 queue mix; each
    # ISO's planning report). Not a per-tech measured throughput -- the split is
    # a judgment; the binding ISO-total is the cited quantity. Same rule-11
    # follow-up as QUEUE_CAP_GW (docs/handoffs/queue-cap-citation-2026-07.md).
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
    # SPP (registered 2026-09-06, lane SPP-20): each cap is the smallest
    # 0.5 GW step at or above the demonstrated peak annual COD of that
    # technology in the EIA-860 2025 ER, BA SWPP (`Operating Year`), the
    # ERCOT RC-DERIVE convention, on the PRIMARY 2021-2025 window
    # (docs/multi-iso/spp-data-audit.md §5 row 12: wind 3.416 / solar 0.563 /
    # gas_ct 1.019 / gas_cc 0.000 / storage 0.422 GW). Where the five-year
    # window records ZERO COD the 2015-2025 window is used instead and said so
    # — a 0.0 cap would assert the technology can NEVER be built, which the
    # longer record contradicts.
    "SPP": {
        "wind": 3.5,  # 2021-2025 peak 3.416 GW (2015-2025: 3.886)
        "solar": 1.0,  # 2021-2025 peak 0.563 GW
        "gas_cc": 1.0,  # 2021-2025 = 0.000 -> 2015-2025 window, peak 0.600 GW
        "gas_ct": 1.5,  # 2021-2025 peak 1.019 GW
        # Nuclear: no demonstrated COD in either window (true of every ISO in
        # this table); 0.5 is the smallest non-zero step the table uses for a
        # technology with no throughput record — a forward-ceiling ESTIMATE,
        # LABELLED as such, never a measured throughput.
        "nuclear": 0.5,
        "geothermal": 0.0,  # no demonstrated COD and no cited EGS resource
        "offshore_wind": 0.0,  # landlocked footprint
    },
    # NWPP (registered 2026-09-14, lane NWPP-20): MEASURED — demonstrated
    # peak annual COD on the WECC-admitted footprint, EIA-860 2025 ER
    # ``Operating Year`` (the same identification ERCOT's own entry uses;
    # docs/multi-iso/nwpp-data-audit.md §7 row 7, re-measured post-
    # adjudication in PRECOMMIT-nwpp-20 §3.7), each cap the smallest step
    # above its record; the 2019-2025 window first, 2015-2025 where the
    # shorter window records ZERO COD (a 0.0 cap would assert the technology
    # can NEVER be built, which the longer record contradicts).
    "NWPP": {
        "wind": 1.5,  # 2019-2025 peak 1.484 GW (2020)
        "solar": 2.0,  # 2019-2025 peak 1.953 GW (2024)
        "gas_cc": 0.5,  # 2019-2025 = 0.000 -> 2015-2025 window, peak 0.500 GW (2016)
        "gas_ct": 0.5,  # 2019-2025 peak 0.456 GW (2024)
        # Nuclear: no demonstrated COD in either window (Columbia is 1984);
        # 0.5 is the table's smallest non-zero step for a technology with no
        # throughput record — a forward-ceiling ESTIMATE, LABELLED as such.
        "nuclear": 0.5,
        # Geothermal: a REAL record here (NV/OR/ID/UT geothermal — 0.127 GW in
        # 2018, 0.048 in 2023, 0.029 in 2024); 0.2 is the smallest 0.1 GW
        # step above the 2015-2025 peak, on a finer step than the 0.5 GW the
        # table uses for GW-scale technologies because the record is sub-GW.
        "geothermal": 0.2,
        "offshore_wind": 0.0,  # no BOEM lease area serves the footprint; OR's
        #   floating-wind lease areas (Coos Bay / Brookings) are CAISO-adjacent
        #   and unbuilt — no demonstrated COD
    },
    # SOCO (registered 2026-09-14, lane SOCO-20): each cap is the smallest
    # 0.5 GW step at or above the demonstrated peak annual COD of that
    # technology in the EIA-860 2025 ER, BA SOCO (`Operating Year`), the same
    # convention as SPP, on the 2021-2025 window with the 2015-2025 window as
    # the fallback where the five-year record is empty or near-empty
    # (docs/multi-iso/soco-data-audit.md §5 row 9: solar 2023 1.11 / 2024
    # 0.72 / 2025 0.34 GW by the audit's technology grouping; gas CC 2023
    # 1.51 GW; batteries 2024 0.065 GW; wind 0.000 in every year).
    "SOCO": {
        # WIND: zero demonstrated COD in ANY year of 2015-2025 and ZERO wind
        # generators in the fleet (audit §2.2 / R-12) — a physical fact about
        # the Southeast's wind resource, not a data gap — so 0.0 is the
        # honest cap; a nonzero step would assert a throughput no record
        # supports. Re-opened only on a cited SOCO wind COD.
        "wind": 0.0,
        "solar": 1.0,  # 2021-2025 peak 0.870 GW (2021)
        "gas_cc": 1.5,  # 2021-2025 peak 1.507 GW (2023: Barry A3 + Lowman)
        # gas_ct: 0.005 GW in 2021-2025 -> 2015-2025 window, peak 0.050 GW
        # (2019, Kimberly-Clark Mobile CHP). 0.5 is the smallest step.
        "gas_ct": 0.5,
        # NUCLEAR: the ONLY ISO in this table with a demonstrated nuclear
        # COD — Vogtle 3 (1,114 MW, 2023) and Vogtle 4 (1,114 MW, 2024) —
        # so 1.5 is MEASURED here where every peer row is a labelled estimate.
        "nuclear": 1.5,
        "geothermal": 0.0,  # no demonstrated COD and no cited resource
        "offshore_wind": 0.0,  # no BOEM lease area off the Gulf panhandle
    },
}
# Hydrogen turbines (hydrogen_ct, hydrogen_ccgt) and CCUS (gas_cc_ccs) do not
# get their own per-tech queue cap: they share the ``gas_cc`` interconnection
# cap above, since they reuse the same gas-turbine supply chain and queue.
