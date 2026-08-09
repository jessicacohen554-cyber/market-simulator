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
RGGI_MEMBER_STATES_BY_YEAR: dict[int, frozenset[str]] = {
    2021: frozenset({"NY", "CT", "MA", "ME", "NH", "RI", "VT", "MD", "DE", "NJ", "VA"}),
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
        Every pre-CR-1 call site passes ``year=None`` (only storage new entry
        threads it), so the registry default curve/anchor governs and the price
        is byte-identical; and at a delivery year whose vintage equals the
        registry reference (e.g. PJM 2026), the vintage override reproduces the
        registry price exactly.
        """
        if not self.capacity_market:
            return 0.0
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
# MISO PRA reliability-based demand curve (RBDC), ANNUAL (single-season)
# reduction — RETAINED for the P-0B reconciliation test and as the registry
# ``demand_curve``; the SEASONAL grain (:data:`MISO_SEASONAL_RBDC`, RC-1C below)
# is what the pricing seam actually evaluates when the gate is on. The P-0B
# intake captured MISO's CONE levels and PRA clearing OUTCOMES but not the RBDC's
# own shape parameters, so only the price levels are data-derived: net-CONE at
# the requirement (1.0); cap = North/Central gross CONE / net CONE ≈
# 127,361 / 79,800 = 1.596 (annual $/MW-yr; the RBDC caps at gross CONE). The cap
# (0.97) and zero-cross (1.05) reserve positions are FIRST-ORDER representative
# values (documented, not claimed as published), so the reconciliation test
# asserts only the net-CONE anchor and the cap fraction.
# Net-CONE anchor 79.8 $/kW-yr (North/Central Net CONE, 79,800 $/MW-yr).
_MISO_RBDC_CURVE: tuple[CapacityDemandCurvePoint, ...] = (
    CapacityDemandCurvePoint(0.97, 1.596),  # ≈ gross/net CONE (RBDC cap)
    CapacityDemandCurvePoint(1.0, 1.0),  # Net CONE at requirement
    CapacityDemandCurvePoint(1.05, 0.0),  # zero-cross (first-order)
)

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
# The net-CONE REFERENCE (the frac-1.0 requirement point) is the published ANNUAL
# North/Central net-CONE spread FLAT across 365 days (218.63 $/MW-day) — MISO
# publishes the seasonal GROSS-CONE caps and the ANNUAL net-CONE, not a separate
# seasonal net-CONE — so the requirement-point price is flat while the per-season
# CAP fraction (the published seasonal quantity) is seasonal_gross_daily ÷ daily
# net-CONE. This keeps the annualization self-consistent: at the requirement
# (position 1.0) the seasonal sum returns EXACTLY the annual net-CONE
# (Σ_s 1.0 × daily_net × days_s = daily_net × 365 = 79,800), reducing to the
# annual curve; short positions pick up the seasonal caps. The cap/zero reserve
# POSITIONS stay first-order (0.97 / 1.05), identical to the annual curve — the
# RBDC's own shape parameters were not published (P-0B).
_MISO_NC_NET_CONE_PER_MW_YR: float = 79_800.0  # N/C net-CONE, PY2025-26 (miso.csv)
_MISO_DAILY_NET_CONE_PER_MW_DAY: float = _MISO_NC_NET_CONE_PER_MW_YR / 365.0  # 218.63
_MISO_RBDC_CAP_X: float = 0.97  # first-order (shared with the annual curve)
_MISO_RBDC_ZERO_X: float = 1.05  # first-order


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


def _miso_seasonal_curve(
    gross_cone_per_mw_day: float,
) -> tuple[CapacityDemandCurvePoint, ...]:
    """One season's normalized RBDC: cap = seasonal gross CONE ÷ flat daily net-CONE.

    ``gross_cone_per_mw_day`` is the published seasonal "CONE (Seasonal)" figure
    (North/Central). The requirement point (1.0) is the flat daily net-CONE; the
    cap/zero reserve positions are first-order (shared with the annual curve).
    """
    cap_frac = gross_cone_per_mw_day / _MISO_DAILY_NET_CONE_PER_MW_DAY
    return (
        CapacityDemandCurvePoint(_MISO_RBDC_CAP_X, cap_frac),  # season gross-CONE cap
        CapacityDemandCurvePoint(1.0, 1.0),  # flat daily net-CONE at the requirement
        CapacityDemandCurvePoint(_MISO_RBDC_ZERO_X, 0.0),  # zero-cross (first-order)
    )


# PY2025-26 seasonal gross CONE ($/MW-day), North/Central — miso.csv "CONE
# (Seasonal)" rows (Summer 1384.36, Fall 1399.58, Winter 1415.13, Spring
# 1384.36 = annual gross CONE 127,361 ÷ days_in_season).
MISO_SEASONAL_RBDC: SeasonalRBDC = SeasonalRBDC(
    seasons=(
        MISOSeasonRBDC("summer", 92, _miso_seasonal_curve(1384.36)),
        MISOSeasonRBDC("fall", 91, _miso_seasonal_curve(1399.58)),
        MISOSeasonRBDC("winter", 90, _miso_seasonal_curve(1415.13)),
        MISOSeasonRBDC("spring", 92, _miso_seasonal_curve(1384.36)),
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
#   NEISO anchor = net-CONE ($/kW-month) × 12; FCA 11 reserve-position geometry,
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


# ISO-NE FCA vintages share FCA 11's (2020/2021) reserve-position geometry —
# its published MW curve normalized by the Net ICR gives cap-plateau end 0.978
# and zero-cross 1.083 of the requirement (the same first-order construction the
# registry ``_NEISO_FCA_CURVE`` uses; the interior MRI kink is skipped, refined
# in CR-3). Each vintage varies only its cap fraction and anchor.
_NEISO_FCA_CAP_X: float = 0.978
_NEISO_FCA_ZERO_X: float = 1.083


def _neiso_fca_vintage_curve(
    net_cone_month: float, starting_price_month: float
) -> tuple[CapacityDemandCurvePoint, ...]:
    """One ISO-NE FCA delivery-year vintage curve on FCA 11's geometry.

    Cap fraction = ``starting_price_month / net_cone_month`` (both $/kW-month,
    ratio basis-independent); net-CONE at the requirement; zero at 1.083.
    """
    return (
        CapacityDemandCurvePoint(
            _NEISO_FCA_CAP_X, starting_price_month / net_cone_month
        ),  # starting (max) price
        CapacityDemandCurvePoint(1.0, 1.0),  # Net CONE at requirement
        CapacityDemandCurvePoint(_NEISO_FCA_ZERO_X, 0.0),  # zero-cross
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
        MarketDesignVintage(
            "2020-2021", 11.64 * 12.0, _neiso_fca_vintage_curve(11.64, 18.624)
        ),
        MarketDesignVintage(
            "2021-2022", 8.04 * 12.0, _neiso_fca_vintage_curve(8.04, 12.864)
        ),
        MarketDesignVintage(
            "2022-2023", 8.156 * 12.0, _neiso_fca_vintage_curve(8.156, 13.05)
        ),
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
    * ``year`` before the earliest vintage HOLDS-FIRST to it (e.g. a MISO year
      before PY2025-26 gets the 2025-26 RBDC — a documented stand-in for the
      unpublished pre-RBDC vertical curve);
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
    # MISO ICAP Planning Reserve Margin Requirement (PRMR). Source: MISO
    # Planning Year 2024-25 LOLE Study Report (ICAP PRM ~17.9%).
    "MISO": 0.179,
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
    # value over a generic estimate). Vintage = CCP 2026/2027 (FCA 17), the
    # delivery year covering the 2026 forecast base year, matching the vintage
    # the other capacity anchors use: Net ICR 30,305 MW / summer 50/50 peak
    # 27,298 MW - 1 = 11.02%. Both are ISO-NE's own published, forward-
    # regenerable values (recomputed each FCA), and the 50/50 peak is on the same
    # "Net (with Reductions for BTM PV)" basis as the model's EIA-930 demand, so
    # the margin pairs cleanly with the model's peak. Source: ISO New England,
    # "Installed Capacity Requirement, Related Values, and HQICCs for the
    # 2026-2027 Capacity Commitment Period" (FCA 17), FERC Docket ER23-405-000,
    # filed 2022-11-08: ICR 31,306 MW, HQICC 1,001 MW, Net ICR 30,305 MW (p.2-3);
    # 50/50 summer peak 27,298 MW (p.9-10, 2022 CELT). Kept as an explicit
    # expression so both published MW values stay traceable (rule 5).
    "NEISO": 30_305.0 / 27_298.0 - 1.0,  # Net ICR / 50-50 peak - 1 = 0.1102 (FCA 17)
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
    # NEISO (FF-2B, 2026-07-19): ISO-NE's Forward Capacity Market clears Demand
    # Resources — energy efficiency, load management, and distributed generation
    # — as capacity SUPPLY that holds a Capacity Supply Obligation against the
    # Net ICR, exactly the PJM situation (DR is a cleared supply product, not a
    # load-forecast netting), so — as for PJM — the value is a documented
    # reconciliation (rule 14), never a raw fraction of peak. FCA 17 (CCP
    # 2026/2027) cleared 2,940 MW of demand resources (ISO-NE FCA 17
    # initial-results press release, 2023-03-10: "2,940 MW (including 130 MW new)
    # of demand resources, including energy efficiency, load management, and
    # distributed generation resources"). Divided by the Net ICR requirement
    # (30,305 MW — the quantity these resources clear against, NOT the ICAP peak),
    # so under the Net-ICR requirement path the netted credit reproduces ISO-NE's
    # own supply-side counting: requirement = peak × (1 − f) × (1 + PRM_NetICR) =
    # (peak / CELT_peak) × (Net_ICR − DR) when peak = CELT_peak. Recurring FCM
    # product that regenerates each delivery year and scales with enrolment
    # (rule 13). Refresh on a vintage re-anchor (source-data change, rule 23),
    # never a residual.
    "NEISO": 2_940.0 / 30_305.0,
}

# Firm import capacity counted by the ISO's own resource-adequacy ledger,
# credited on the supply side of
# :func:`market_sim.model.capacity.accredited_firm_capacity_mw` (via
# :func:`market_sim.model.capacity._firm_import_mw`) exactly where each ISO's
# own ledger counts it. Two provenance cases share this one registry (rule 19,
# one mechanism per phenomenon — "firm import the adequacy ledger counts"):
#   (a) ISOs the model has NO import node for (ERCOT, PJM) — the firm tie is
#       otherwise entirely absent from the model, so this is its only entry.
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
#   rule 13; the 2025 DMM report is not yet published). NOT the Maximum Import
#   Capability (16,148 MW) — the MIC is a deliverability LIMIT, not the RA
#   capacity actually contracted, and crediting it would overstate.
# * NEISO (FF-2B, 2026-07-19): 567 MW of import capacity that cleared FCA 17
#   (CCP 2026/2027) holding Capacity Supply Obligations — "567 MW of imports
#   from New York, Québec, and New Brunswick" (ISO-NE FCA 17 initial-results
#   press release, 2023-03-10). These are Import Capacity Resources that count
#   as SUPPLY toward the Net ICR; the HQICC tie benefit (1,001 MW) is already
#   netted from the requirement (Net ICR = ICR − HQICC, see the NEISO
#   PLANNING_RESERVE_MARGIN entry) and is NOT double-counted here. The model's
#   HQ_import node hosts imports in dispatch but the accredited ledger omits the
#   cleared import CSOs — case (b) above. Recurring FCM product (rule 13).
ADEQUACY_EXTERNAL_TIE_FIRM_MW: dict[str, float] = {
    "ERCOT": 817.0,
    "PJM": 1_281.7,  # 2026/2027 BRA Report Table 7 (cleared import UCAP)
    "CAISO": 3_371.0,  # DMM 2024 Table 15.6 RA Imports (= model firm import tranches)
    "NEISO": 567.0,  # FCA 17 cleared imports (NY/QC/NB), CSO-holding supply
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
# tuned to clear the I7 adequacy invariant (rules 5/13/21).** Each ISO's
# published construction splits hydro into a controllable/reservoir class and a
# limited-control / run-of-river class, at materially different factors. The
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
# * NEISO / ERCOT — ABSENT, so they fall back to the generic published class
#   derate :data:`RENEWABLE_CAPACITY_CREDIT`\\ ["hydro"] = 0.50 (the same
#   fallback every uncredited class already takes, rule 25 spirit — never a
#   foreign ISO's factor). No ISO-published hydro class factor was located for
#   either this session: ISO-NE's FCM qualifies hydro at Seasonal Claimed
#   Capability with intermittent hydro at a median-output construction
#   (per-resource, no published class rating), and ERCOT is energy-only with no
#   accreditation product. Both are open items in the FFR-1C findings doc.
HYDRO_ACCREDITATION_CREDIT_BY_ISO: dict[str, float] = {
    "CAISO": 0.7041,  # CPUC/CAISO CY2025 NQC tech factor, non-disp. hydro, Sep
    "NYISO": 0.3844,  # NYISO 2025-26 Final CAF, Limited Control Run of River, RoS
    "MISO": 0.62,  # MISO PY2025-26 Indicative DLOL, Run-of-River Hydro, Summer
    "PJM": 0.38,  # PJM 2026/27 BRA final ELCC class rating, Hydro Intermittent
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
        # FFR-2C 2026-08-02: published alongside the 2028/2029 net-CONE
        # re-anchor. (1+0.200) x 0.7834 (Pool-Wide Accredited UCAP Factor);
        # both endorsed at the 2026-02-19 MRC meeting. Workbook
        # 'Planning Parameters' sheet, FPR row, RTO column.
        "2028/2029": 0.9401,
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
    # "CAISO": {"storage": ...},   # pending cited SOM/DMM AS-revenue intake
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
}

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
}
# Hydrogen turbines (hydrogen_ct, hydrogen_ccgt) and CCUS (gas_cc_ccs) do not
# get their own per-tech queue cap: they share the ``gas_cc`` interconnection
# cap above, since they reuse the same gas-turbine supply chain and queue.
