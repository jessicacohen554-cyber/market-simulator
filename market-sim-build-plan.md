# Market Simulation Model — Build Plan

**Purpose:** Instruction document for building a clean, LP-based electricity market simulation model. The old repo contains a heuristic dispatch engine that cannot be salvaged architecturally, but has valuable data constants, fleet parameters, and capacity-evolution logic worth extracting. This plan specifies what to build new, what to extract, and in what order — plus a task registry for sub-agents that handle documentation, expert review, citations, and visual explainers.

**Companion document:** `model-methodology-spec.md` governs all model design decisions: LP formulation, matrix construction patterns, scenario architecture, capacity evolution logic, performance patterns, and explicit build-agent rules. **When this plan and the methodology spec conflict, the methodology spec wins.**

**Target runtime:** Python 3.11+. Solver: HiGHS via `highspy`. Frontend: static HTML/JS on GitHub Pages. CLI for batch runs and single custom scenarios.

-----

## 1. Architecture Overview

The model simulates hourly electricity dispatch across two independent ISOs (ERCOT 4-zone, CAISO 1-zone + WECC import node) for every year from 2026–2050 under a parameterized scenario system. The core loop is:

```
For each scenario config:
  For each year (2026–2050):
    1. Evolve fleet (retirements + new entry) from prior year state
    2. Assemble hourly inputs (demand, renewables, fuel prices, availability)
    3. Solve LP dispatch (8,760 hours × all zones simultaneously)
    4. Extract results: dispatch, prices (LP duals), emissions, storage SOC, curtailment
    5. Cache results as Parquet keyed by (config_hash, iso, year)
```

ERCOT and CAISO are physically independent — run as separate model instances sharing methodology and scenario definitions. Scenarios are defined by a flat config dataclass with tiered parameters — see `model-methodology-spec.md` §4 for the full scenario architecture.

### Target Directory Structure

```
market-sim/
├── README.md
├── pyproject.toml
├── CONVENTIONS.md                   # Naming, branching, commit, file conventions
├── CHANGELOG.md                     # Running log of model changes and decisions
│
├── src/
│   └── market_sim/
│       ├── __init__.py
│       ├── config/
│       │   ├── __init__.py
│       │   ├── scenarios.py         # ScenarioConfig dataclass + sweep generator
│       │   ├── constants.py         # Extracted physical/economic constants
│       │   └── iso_configs.py       # Per-ISO zone topology, VOLL, transfer limits
│       ├── data/
│       │   ├── __init__.py
│       │   ├── eia_loader.py        # EIA Hourly Grid Monitor parquet loader
│       │   ├── fleet.py             # Generator fleet builder (EIA-860 + heat rate bins)
│       │   ├── renewables.py        # Renewable CF profile loader
│       │   └── fuel.py              # Gas price + basis + carbon price curves
│       ├── model/
│       │   ├── __init__.py
│       │   ├── dispatch.py          # LP formulation + solve (THE CORE)
│       │   ├── transmission.py      # Pipe-and-bubble zone transfer constraints
│       │   ├── storage.py           # Storage parameter structs + SOC constraint builder
│       │   └── capacity.py          # Year-over-year fleet evolution engine
│       ├── policy/
│       │   ├── __init__.py
│       │   ├── ira.py               # IRA PTC/ITC credit application
│       │   ├── rps.py               # State clean energy standards (CA SB 100)
│       │   └── carbon.py            # Carbon price adder logic
│       ├── results/
│       │   ├── __init__.py
│       │   ├── cache.py             # Parquet-based scenario-year caching
│       │   ├── outputs.py           # Result dataclass definitions
│       │   ├── emissions.py         # Emissions accounting from dispatch
│       │   └── export.py            # JSON export for frontend consumption
│       └── runner.py                # Main orchestrator (scenario × year loop)
│
├── frontend/                        # GitHub Pages interactive frontend
│   ├── index.html                   # Main dashboard — scenario results explorer
│   ├── decisions.html               # Design decision tracker with form submission
│   ├── parameters.html              # Parameter citation browser
│   ├── css/
│   │   └── style.css                # Shared styles
│   ├── js/
│   │   ├── app.js                   # Core app logic, routing, state management
│   │   ├── charts.js                # D3/Plotly chart components
│   │   ├── decisions.js             # Decision form logic + localStorage cache
│   │   └── data-loader.js           # Fetch JSON results from data/ directory
│   └── data/                        # Exported model results as static JSON
│       ├── scenarios.json           # Scenario metadata
│       ├── results/                 # One JSON per scenario (lazy-loaded)
│       └── parameters.json          # Full parameter citation registry
│
├── learning-hub/                    # GitHub Pages visual explainer site
│   ├── index.html                   # Learning hub landing page with navigation
│   ├── lp-dispatch/                 # Scrollytell: "How LP dispatch works"
│   ├── capacity-evolution/          # Scrollytell: "How the fleet changes over time"
│   ├── storage-cooptimization/      # Scrollytell: "Why LP storage beats heuristics"
│   ├── transmission-pricing/        # Scrollytell: "How zones create price separation"
│   ├── scenario-uncertainty/        # Scrollytell: "N futures — reading the fan chart"
│   └── shared/                      # Shared scrollytell CSS/JS framework
│       ├── scrollytell.css
│       └── scrollytell.js
│
├── context/                         # Reference knowledge for reviewer sub-agent
│   ├── README.md
│   ├── aurora.md
│   ├── plexos.md
│   ├── reeds.md
│   ├── ipm.md
│   ├── genx.md
│   ├── regen.md
│   ├── cambium.md
│   ├── egrid.md
│   └── comparison-matrix.md
│
├── docs/                            # Auto-maintained documentation
│   ├── architecture.md
│   ├── lp-formulation.md
│   ├── data-dictionary.md
│   ├── parameter-citations.md
│   ├── calibration-log.md
│   ├── decision-log.md
│   └── reviewer-notes.md
│
├── data/
│   ├── eia_hourly/                  # EIA parquets (7 ISOs × 5 years)
│   ├── fleet/                       # EIA-860 generator data
│   └── reference/                   # eGRID emission factors, etc.
│
├── scripts/
│   ├── export_results.py            # Convert cached Parquets → frontend JSON
│   ├── validate_parameters.py       # Check all parameters have citations
│   └── build_learning_hub.py        # Generate/update learning hub pages
│
└── tests/
    ├── test_dispatch.py
    ├── test_storage.py
    ├── test_capacity.py
    └── test_integration.py
```

### Codebase Conventions

Document in `CONVENTIONS.md` at repo root.

**File naming:** Python `snake_case.py`. Frontend `kebab-case.html/js/css`. Markdown `kebab-case.md`. No abbreviations except established acronyms (LP, ISO, SOC, LCOE, VOLL).

**Module naming:** Single clear responsibility per module. Split at ~400 lines. Config files are pure data (no logic). Model files contain logic (no hardcoded constants — import from config).

**Function naming:** Public functions use descriptive verb-noun: `solve_dispatch()`, `evolve_fleet()`, `load_eia_profiles()`. Private helpers prefixed with `_`. No single-letter variable names except `t` (hour), `g` (generator), `z` (zone), `s` (storage) in tight LP construction loops — with a comment at the top of the block.

**Constants:** All physical/economic constants live in `config/constants.py` with inline citation comments: source, date, page/table number. No magic numbers anywhere in model code. See also `model-methodology-spec.md` §7.1 rule 1.

**Git conventions:** Feature branches named `phase-N/description`. Commits imperative present tense. Each phase merges to `main` via PR after quality gate passes.

**Documentation rule:** Every public function has a one-line docstring minimum. Every module has a module-level docstring. `docs/` files updated by documentation sub-agent after each phase merge.

**Data files:** Raw data in `data/` is never modified in place. All data files tracked via Git LFS if >10 MB.

**Frontend conventions:** No build toolchain (no webpack, no npm). Vanilla HTML/CSS/JS. Libraries loaded via CDN only (D3, Plotly). `localStorage` with `marketsim_` key prefix. JSON data files kept under 5 MB per file.

-----

## 2. Build Phases

Build in this order. Each phase produces a testable artifact before moving on.

### Phase 1 — Project Skeleton + Data Layer

**Goal:** Loadable data pipeline that produces typed input structs and the scenario config system. No optimization yet.

**Tasks:**

1. Initialize repo with `pyproject.toml` (see §8 Dependencies).
1. Build `ScenarioConfig` dataclass with tiered parameters and defaults, YAML loading, cache key generation, and sweep generator. Follow `model-methodology-spec.md` §4 exactly.
1. Define core data types as Pydantic models: `Generator`, `StorageTech`, `Zone`, `TransferLink`, `HourlyInputs`.
1. Build `eia_loader.py` — clean parquet reader for EIA Hourly Grid Monitor.
1. Build `iso_configs.py` — ERCOT 4-zone topology, CAISO single zone + WECC node.
1. Build `fleet.py` — generator fleet builder from EIA-860 data with struct-of-arrays conversion for LP construction (see `model-methodology-spec.md` §3).

**EXTRACT from old repo:**

- `eia_data_io.py` (128 lines) — clean parquet loader. Adapt to return typed structs.
- Constants to `constants.py` (see §3 Extraction Manifest for full list).
- Fleet data: base year demand, peak demand values.

**Build from scratch:**

- `iso_configs.py` — zone topology, load allocation percentages.
- `scenarios.py` — ScenarioConfig, SweepDefinition, sweep generator, YAML parsing.

**Tests:** Load EIA parquets → assert 8,760 rows, no NaNs, peak demand matches known values. Build generator fleet → assert total capacity within 5% of known installed capacity. ScenarioConfig round-trips through YAML. Cache key is deterministic and changes when any parameter changes.

-----

### Phase 2 — LP Dispatch Engine (Single Zone, No Storage)

**Goal:** Solve a single-zone, single-year dispatch LP and extract prices from duals.

This is the most critical phase. The old repo’s dispatch is a greedy heuristic — it must be replaced entirely.

**Build `dispatch.py` from scratch following `model-methodology-spec.md` §1 (formulation) and §2 (construction pattern).** Key requirements:

- Renewables are decision variables on the LHS of energy balance (spec §1.3)
- Block-diagonal vectorized matrix construction — no Python loops over hours (spec §2.2, §2.3)
- Struct-of-arrays fleet data via `FleetArrays` (spec §3)
- Cost vector assembled from scenario parameters via `assemble_mc()` (spec §3.2)
- Prices extracted as LP duals on energy balance constraints

**DO NOT extract from old repo:** The entire dispatch path (`lmp_engine.py` dispatch kernel, `searchsorted` pricing, `demand-quantile adders`, Numba `@njit` loops) is heuristic and architecturally incompatible.

**Tests:**

- Trivial case: 1 generator, flat demand → price = marginal cost (verify dual)
- 2 generators, demand below cheaper gen capacity → price = cheap gen MC
- Demand exceeds all capacity → price = VOLL
- Must-run unit with excess capacity → negative prices emerge naturally
- Energy balance: `sum(dispatch) + unserved = demand` for every hour

-----

### Phase 3 — Multi-Zone Transmission + CAISO Imports

**Goal:** Add pipe-and-bubble transmission model to create zonal price separation.

**Build from scratch in `transmission.py`.** No transmission model exists in the old repo. Follow `model-methodology-spec.md` §1.3 for the formulation (flow variables, energy balance modification, CAISO import tranches as pseudo-generators with stepped costs).

Old repo has `EXTERNAL_CLEAN_IMPORTS_TWH` with CAISO=0 — not usable. Build CAISO import curve empirically from EIA-930 interchange data.

**Tests:**

- ERCOT: West zone wind surplus → flows to North/Houston → West price < North price
- CAISO: High demand → imports from WECC at stepped prices
- Zero transfer limits → zones decouple completely (prices diverge)

-----

### Phase 4 — Storage Co-Optimization

**Goal:** Add storage as LP decision variables with SOC tracking.

**Build from scratch in `storage.py`.** Follow `model-methodology-spec.md` §1.3 for the formulation (SOC dynamics, cyclic boundary, charge/discharge bounds, energy balance modification, storage tiebreaker epsilon).

**EXTRACT storage technology parameters from old repo `pipeline_config.py` lines 368–397** — see §3 Extraction Manifest. These become Tier 2 parameters in the scenario config.

**DO NOT extract** the old repo’s storage dispatch — it’s a greedy Numba heuristic. The LP replaces it entirely.

**Tests:**

- Flat demand, cheap off-peak / expensive on-peak → storage charges off-peak, discharges on-peak
- SOC conservation: `sum(charge × η) = sum(discharge / η)` over full year
- Cyclic boundary: SOC[0] = SOC[8759]
- Round-trip losses: total discharge energy < total charge energy by (1 - RTE)

-----

### Phase 5 — Capacity Evolution Engine

**Goal:** Year-over-year fleet updates — retirements, new entry, policy mandates.

Follow `model-methodology-spec.md` §5 for the one-pass sequential architecture. This is where the old repo has the most valuable extractable logic — see §3 Extraction Manifest for the full list.

**EXTRACT from old repo** (adapt, don’t copy verbatim):

- Year-loop skeleton from `step2_3_de_pathway_tf.py`
- Wright’s Law learning curves from `step6_1`
- LCOE calculation with IRA credits from `step6_1`
- Retirement sigmoid from `pipeline_config` `thermal_fleet_mw()`
- Queue caps and build rate limits from `step6_1`
- State RPS floors from `pipeline_config`

**DO NOT extract:** `coal_fraction_at_clean_pct()` from `dispatch_utils` (inconsistent). `step6_1` milestone-year-only logic (we run every year).

**Tests:**

- Known coal retirement schedule → correct units removed in correct years
- Clean share above sigmoid threshold → accelerated thermal retirement
- LCOE below expected revenue → new entry appears (capped by queue)
- CAISO RPS floor binding → forces additional clean builds even if uneconomic

-----

### Phase 6 — Scenario Runner + Caching

**Goal:** Full orchestration with Parquet caching and parallel execution.

**Build `runner.py` and `cache.py`.** Follow `model-methodology-spec.md` §4.4 (caching) and §6 (parallelism).

Key implementation points:

- Cache structure: one Parquet per scenario-year at `results/{iso}/{cache_key}/year_{YYYY}.parquet` plus `config.yaml`
- Check-before-run: skip if Parquet exists
- Parallel execution via `ProcessPoolExecutor` across `(config, iso)` pairs
- Single-run mode: `python -m market_sim run --config scenario.yaml`
- Batch sweep mode: `python -m market_sim sweep --sweep sweep_definition.yaml`
- Log the full resolved `ScenarioConfig` at the start of every run

**Execution workflow:**

- Run corner scenarios first (extremes of key dimensions) → validate calibration
- Then expand to sweep batches
- Caching means re-running is cheap — only new/changed scenarios compute

**Tests:**

- Run 1 scenario × 3 years → results cached → re-run skips all 3
- Corrupt one cache file → only that year re-runs
- Two scenarios diverge only in gas price → fleets identical year 1, diverge later
- Parallel and serial produce identical results

-----

### Phase 7 — Outputs + Emissions + Calibration

**Goal:** Complete output suite and calibration framework.

**Output variables (per zone, per hour):** Dispatch by generator (MW), zonal price ($/MWh), emissions (tCO2), storage SOC/charge/discharge, renewable curtailment, capacity factors, unserved energy, inter-zonal flows. All stored in the per-scenario-year Parquet.

**Emissions accounting:** Vectorized — `dispatch × emission_rate_array`. No Python loops. See `model-methodology-spec.md` §3 for the struct-of-arrays pattern.

**EXTRACT calibration approach from old repo:**

- `calibrate_lmp_model.py` — framework structure (adapt, don’t copy dispatch logic)
- `validate_market_forecasts.py` — benchmark comparison; P10/P50/P90 fan-band framework

**Calibration targets:**

- ±5% on generation mix by fuel type vs. published benchmarks on common inputs
- Diagnostic order: (1) generation mix, (2) price duration curve, (3) avg price, (4) capacity factors
- Workflow: input parity first → dispatch comparison → price comparison

-----

### Phase 8 — Interactive Frontend (GitHub Pages)

**Goal:** A static HTML site hosted on GitHub Pages for exploring results, reviewing design decisions, and browsing parameters. No backend — everything reads from exported JSON and caches to `localStorage`.

**Pages:**

1. **`index.html` — Results Dashboard.** Scenario selector (dropdown or matrix grid). For a selected scenario: generation mix stacked area chart (2026–2050), emissions trajectory line chart, price duration curves by zone, storage utilization heatmap. All charts via Plotly.js. Lazy-load per-scenario JSON on selection.
1. **`decisions.html` — Decision Tracker.** Each decision domain is a collapsible section. Open/leaning decisions render as forms with radio buttons + notes textarea. Submit caches to `localStorage` (`marketsim_decision_{id}`). Decided items shown read-only with green checkmarks. Export button dumps all decisions as JSON.
1. **`parameters.html` — Parameter Citation Browser.** Searchable/filterable table of every model parameter. Columns: parameter name, value, unit, source, source date, page/table reference, URL, notes. Loaded from `parameters.json`. Filter by domain. Click-to-expand for full citation details.

**Data pipeline:** `scripts/export_results.py` converts cached Parquets → JSON files in `frontend/data/`. Keep per-scenario JSON under 2 MB. Full hourly stays in backend cache.

**Hosting:** GitHub Pages from repo root. No CI required — push static files.

**Design:** Consistent design system for colors and typography. Responsive but desktop-first.

**Tests:** `decisions.html` — fill a form, reload, confirm `localStorage` persists. `index.html` — load a scenario JSON, verify chart renders without console errors.

-----

### Phase 9 — Learning Hub (Scrollytell Visual Explainers)

**Goal:** Visual, narrative HTML pages that explain how each major model component works. Hosted alongside the frontend on GitHub Pages.

**Pages (one scrollytell per topic):**

1. **LP Dispatch** — “How the model decides who generates.” Simplified 5-generator, 24-hour example. Merit order stacking, LP solver animation, dual variable = price. Side-by-side: heuristic vs. LP.
1. **Capacity Evolution** — “How the fleet changes over time.” Animated fleet waterfall chart 2026–2050. Sigmoid retirement trigger. Wright’s Law cost curves.
1. **Storage Co-optimization** — “Why LP storage beats rules of thumb.” Animated SOC profile over a week. Greedy vs. LP global optimum. Round-trip efficiency losses.
1. **Transmission & Zonal Pricing** — “How zones create price separation.” Map-based ERCOT 4-zone with animated flows. Congestion → price divergence. Copper-plate vs. zonal.
1. **Scenario Uncertainty** — “N futures — reading the fan chart.” Interactive fan chart builder. Toggle scenario dimensions on/off, watch P10/P50/P90 bands respond.

**Shared framework (`learning-hub/shared/`):** Lightweight scrollytell engine — intersection observer triggers, sticky chart panels, narrative text blocks. No library dependency beyond D3 for charts.

**Build the shared framework and LP Dispatch page first.** Remaining pages built by the visual learning sub-agent.

-----

## 3. Extraction Manifest

Summary of every file/function to extract from the old repo, organized by destination.

### Constants & Parameters → `config/constants.py`

|Source File                |What                     |Lines    |Notes                         |
|---------------------------|-------------------------|---------|------------------------------|
|`lmp_engine.py`            |`EFFICIENCY_BINS`        |85–113   |3 bins × 3 fuel classes       |
|`lmp_engine.py`            |`GAS_AVAILABILITY_FACTOR`|—        |ERCOT 0.83, CAISO 0.88        |
|`lmp_engine.py`            |`CO2_RATES`              |—        |By fuel class + efficiency bin|
|`pipeline_config.py`       |`NUCLEAR_MONTHLY_CF`     |—        |Per-ISO monthly factors       |
|`pipeline_config.py`       |`DEMAND_GROWTH_RATES`    |—        |L/M/H by ISO                  |
|`pipeline_config.py`       |`CO2_PRICES`             |—        |L/M/H carbon paths            |
|`pipeline_config.py`       |Storage tech params      |368–397  |4hr, 8hr, LDES, H2            |
|`pipeline_config.py`       |`STATE_RPS_FLOORS`       |—        |CAISO SB 100 trajectory       |
|`pipeline_config.py`       |`thermal_fleet_mw()`     |1837–1890|Retirement sigmoid            |
|`egrid_emission_rates.json`|Unit emission factors    |full file|EPA CEMS source               |

All extracted constants become parameters in the `ScenarioConfig` at the appropriate tier (see `model-methodology-spec.md` §4.1). No hardcoded values.

### Data Loaders → `data/`

|Source File     |What          |Lines           |Notes                    |
|----------------|--------------|----------------|-------------------------|
|`eia_data_io.py`|Parquet loader|full (128 lines)|Clean; adapt return types|

### Capacity Evolution → `model/capacity.py`

|Source File               |What                      |Lines    |Notes                             |
|--------------------------|--------------------------|---------|----------------------------------|
|`step2_3_de_pathway_tf.py`|Year-loop skeleton        |546–814  |Core trajectory architecture      |
|`step2_3_de_pathway_tf.py`|Floor ratchet + demand adj|800–808  |                                  |
|`step2_3_de_pathway_tf.py`|Vintage ledger            |744–773  |Build tracking                    |
|`step2_3_de_pathway_tf.py`|Gas reliability sizing    |694      |Peak gap analysis                 |
|`step6_1`                 |`wright_cost()`           |540–573  |Learning curves (verified)        |
|`step6_1`                 |`QUEUE_CAP_GW`            |94–103   |ERCOT 12 GW/yr                    |
|`step6_1`                 |Learning rates            |107–168  |By technology                     |
|`step6_1`                 |`get_resource_lcoe()`     |876–992  |LCOE with IRA                     |
|`step6_1`                 |Emission cap + RPS floor  |1599–1700|Reference only                    |
|`step6_1_solvers.py`      |`FloorRatchet`            |—        |Or use simpler inline from step2_3|

### Calibration → `results/`

|Source File                   |What                |Notes                           |
|------------------------------|--------------------|--------------------------------|
|`calibrate_lmp_model.py`      |Framework structure |Adapt; don’t copy dispatch logic|
|`validate_market_forecasts.py`|Benchmark comparison|P10/P50/P90 fan-band framework  |

### DO NOT Extract (Replaced by LP)

|Source                                       |Reason                                                        |
|---------------------------------------------|--------------------------------------------------------------|
|`lmp_engine.py` dispatch kernel              |Heuristic merit order, not LP                                 |
|`lmp_engine.py` pricing logic                |`searchsorted` + demand-quantile adders — replaced by LP duals|
|Numba `@njit` storage loops                  |Greedy heuristic — replaced by LP co-optimization             |
|`dispatch_utils.coal_fraction_at_clean_pct()`|Inconsistent with `thermal_fleet_mw()`                        |
|`step6_1` milestone-year-only logic          |We run every year                                             |
|`EXTERNAL_CLEAN_IMPORTS_TWH` (CAISO=0)       |Not usable; build import curve from scratch                   |

-----

## 4. Key Design Constraints

Non-negotiable architectural decisions. See `model-methodology-spec.md` for full rationale.

1. **Full 8,760-hour resolution.** No representative weeks/days.
1. **LP dispatch, not heuristic.** Prices from dual variables. No separate pricing model.
1. **HiGHS via `highspy`.** Direct CSC matrix construction. No Pyomo, no PuLP.
1. **Vectorized LP construction.** Block-diagonal pattern. No Python loops over hours.
1. **Storage is LP co-optimized.** SOC as decision variable. Not greedy heuristic.
1. **Renewables are decision variables.** On LHS of energy balance with MC=0, upper bound = CF × capacity. LP decides curtailment.
1. **Negative prices emerge naturally** from LP. No price floor.
1. **Deterministic outage derate** (Pmax × availability factor). Not stochastic.
1. **Parquet caching.** Every scenario-year result persisted. Check-before-run. Stop/resume capable.
1. **Run every year 2026–2050.** No milestone years. 25 annual simulations per scenario.
1. **Every input is a parameter.** No hardcoded values. Tiered parameter system (spec §4.1).
1. **One-pass capacity evolution.** No within-year convergence iteration (spec §5.1).

-----

## 5. Open Items to Resolve During Build

|Item                              |Decision Needed                       |Default If Unresolved               |
|----------------------------------|--------------------------------------|------------------------------------|
|Representative weather year       |Which year from 2022–2025 is base case|Use 2024 (most recent complete year)|
|CAISO VOLL                        |$1,000 vs $2,000                      |$2,000 (closer to admin cap)        |
|ERCOT inter-zonal TTC values      |Need from ERCOT CDR reports           |Use published planning estimates    |
|CAISO import supply curve tranches|Need empirical fit from EIA-930       |Use 3-step approximation            |
|P10/P50/P90 methodology           |Define methodology during calibration |Percentiles across scenario ensemble|

-----

## 6. Quality Gates

Before moving to the next phase, verify:

|Phase           |Gate                                                                                                                                  |
|----------------|--------------------------------------------------------------------------------------------------------------------------------------|
|1 — Data        |All EIA parquets load; fleet capacity within 5% of known totals; no NaN/gaps; ScenarioConfig YAML round-trips; cache key deterministic|
|2 — LP Dispatch |Single-zone prices match marginal cost of marginal unit; energy balance holds exactly; dual extraction works; matrix builds in <1 sec |
|3 — Transmission|Zonal price separation appears under congestion; zero-limit test decouples zones                                                      |
|4 — Storage     |SOC conserved; cyclic boundary holds; RTE losses correct; storage arbitrages peak/off-peak                                            |
|5 — Capacity    |Known retirements match schedule; sigmoid accelerates at threshold; LCOE screening adds units below queue cap                         |
|6 — Runner      |Caching works (skip on re-run); parallel scenarios produce identical results to serial; single-run CLI works; sweep CLI works         |
|7 — Outputs     |Emissions sum matches expected order of magnitude; generation mix within ±5% of reference; price duration curve shape reasonable      |
|8 — Frontend    |Dashboard loads scenario JSON and renders charts; decision forms persist to localStorage; parameter table is searchable and complete  |
|9 — Learning Hub|At least LP Dispatch scrollytell is live; shared framework works on mobile; all animations trigger correctly on scroll                |

-----

## 7. Performance Targets

See `model-methodology-spec.md` §6.2 for the full table. Summary:

- Single LP solve: **< 5 seconds**
- Matrix construction: **< 1 second**
- Full scenario-year: **< 10 seconds**
- Memory per LP solve: **< 2 GB**

-----

## 8. Dependencies

```toml
[project]
name = "market-sim"
requires-python = ">=3.11"
dependencies = [
    "highspy>=1.7",
    "numpy>=1.26",
    "pandas>=2.1",
    "pyarrow>=14.0",
    "pydantic>=2.5",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.5"]
```

No Pyomo, no PuLP, no scipy.optimize. Direct `highspy` matrix construction for maximum performance.

Frontend: no build toolchain. Vanilla HTML/CSS/JS + CDN libs (Plotly.js for charts, D3.js for scrollytell visuals).

-----

## 9. Parameter Citation Registry

Every numeric parameter in the model must have a citation entry in `docs/parameter-citations.md` and in `frontend/data/parameters.json`. No magic numbers.

**Required fields per parameter:**

|Field              |Description                           |Example                        |
|-------------------|--------------------------------------|-------------------------------|
|`param_id`         |Unique key matching code variable name|`gas_cc_hclass_heat_rate`      |
|`display_name`     |Human-readable name                   |Gas CC H-class Heat Rate       |
|`value`            |Numeric value as used in model        |6.3                            |
|`unit`             |Physical unit                         |MMBtu/MWh                      |
|`domain`           |Model domain                          |Supply Stack                   |
|`tier`             |Parameter tier (0–3)                  |2                              |
|`source`           |Publication or dataset name           |EIA Table 8.1                  |
|`source_date`      |Publication date                      |2024-06                        |
|`page_or_table`    |Specific location in source           |Table 8.1, p. 47               |
|`url`              |Direct link if available              |https://www.eia.gov/…          |
|`notes`            |Context, caveats, why this value      |H-class represents newest CCGTs|
|`old_repo_location`|Where extracted from (if applicable)  |`lmp_engine.py:87`             |
|`last_verified`    |Date someone confirmed this value     |2026-05-14                     |

**Validation script:** `scripts/validate_parameters.py` cross-checks that every constant in `config/constants.py` and every default in `ScenarioConfig` has a matching entry in `parameters.json`. Fails if any are missing.

**Known parameter sources to compile:**

- EIA: Table 8.1 (heat rates), Hourly Grid Monitor (load/gen profiles), Form 860 (fleet data)
- EPA: eGRID (emission factors), CEMS (unit-level emissions)
- NREL: ATB 2024 (technology costs, storage parameters)
- DOE: LDES Liftoff report (iron-air storage)
- Hydrogen Council 2024 (H2 storage parameters)
- NERC: GADS (forced outage rates by technology class)
- NRC: PRIS (nuclear capacity factors 2019–2023)
- ERCOT: CDR reports (transfer limits, installed capacity), Potomac Economics SOM
- CAISO: OASIS (transfer capability), DMM annual report
- IRS: Final Rules 2024 (IRA credit values)
- CBO: IRA scoring (credit duration/phase-out)
- LBNL: “IRA at Two” (credit uptake analysis)

-----

## 10. Sub-Agent Task Registry

Delegated workstreams with distinct personas and deliverables. Run as separate sessions with focused instructions.

-----

### SA-1: Documentation Agent

**Persona:** Technical writer with energy modeling background.

**Trigger:** After each phase merge to `main`.

**Responsibilities:**

- Update `docs/architecture.md` to reflect current system state
- Update `docs/data-dictionary.md` with new fields, types, ranges
- Update `docs/lp-formulation.md` if dispatch/storage/transmission constraints change
- Maintain `docs/decision-log.md` — append new decisions with date and rationale
- Maintain `CHANGELOG.md` with dated entries per phase
- Ensure every public function has a docstring; flag any that don’t

**Quality gate:** All public functions documented. No undefined terms in data dictionary. Architecture diagram matches actual module structure.

-----

### SA-2: Expert Reviewer Agent

**Persona:** Independent energy market modeler. 15+ years across production cost models (Aurora, PLEXOS, ReEDS, IPM, GenX, US-REGEN, Cambium). Objective, constructive, specific.

**Trigger:** After Phase 2 (LP dispatch), Phase 5 (capacity evolution), and Phase 7 (calibration outputs). Also on-demand.

**Context:** Reads from `context/` folder containing methodology summaries of reference models.

**Responsibilities:**

- Review LP formulation against standard production cost modeling practice
- Review capacity evolution against established capacity expansion approaches
- Review storage formulation against NREL ATB defaults
- Review scenario architecture — is the parameter space sufficient? Any missing dimensions?
- Review calibration targets — is ±5% achievable and sufficient?
- Produce `docs/reviewer-notes.md`. Format: finding → implication → recommendation. Severity: `[CRITICAL]`, `[IMPORTANT]`, `[MINOR]`.

**Context folder contents (`context/`):**

|File                  |Contents                                                                 |
|----------------------|-------------------------------------------------------------------------|
|`aurora.md`           |Aurora methodology: dispatch, transmission, capacity expansion           |
|`plexos.md`           |PLEXOS: MILP/LP modes, transmission, storage, pricing                    |
|`reeds.md`            |NREL ReEDS: capacity expansion, time slices, renewable supply curves     |
|`ipm.md`              |EPA IPM/NEEDS: regulatory focus, multi-pollutant, retirement logic       |
|`genx.md`             |MIT GenX: configurable LP, representative periods, multi-stage investment|
|`regen.md`            |EPRI US-REGEN: economy-wide, capacity expansion + dispatch               |
|`cambium.md`          |NREL Cambium: marginal emission rates, Scope 2 accounting                |
|`egrid.md`            |EPA eGRID: emission factors methodology, subregion definitions           |
|`comparison-matrix.md`|Cross-model comparison table                                             |

-----

### SA-3: Parameter Citation Agent

**Persona:** Research analyst. Meticulous with sources. Zero tolerance for unsourced numbers.

**Trigger:** After Phase 1, then incrementally as parameters are added.

**Responsibilities:**

- Build and maintain `docs/parameter-citations.md` and `frontend/data/parameters.json`
- Trace every constant to primary source and fill all citation fields (§9 schema)
- Verify values haven’t been updated since publication
- Flag parameters where primary source is another model’s assumption (not empirical)
- Flag parameters older than 3 years for refresh review
- Run `scripts/validate_parameters.py` — zero missing citations

-----

### SA-4: Visual Learning Agent (Scrollytell)

**Persona:** Data visualization designer and technical storyteller. D3.js fluent.

**Trigger:** LP Dispatch page after Phase 2. Rest after Phase 7.

**Responsibilities:**

- Build shared scrollytell framework (`learning-hub/shared/`)
- Create each scrollytell page (Phase 9 list)
- Narrative text + interactive visualization with scroll-triggered transitions
- Use actual model results where possible, synthetic examples where pedagogically clearer
- Mobile and desktop support
- Consistent fuel/resource color tokens

**Priority order:** LP Dispatch → Capacity Evolution → Scenario Uncertainty → Storage → Transmission

-----

### SA-5: Ad-Hoc Feature Agent

**Persona:** Pragmatic full-stack developer.

**Trigger:** On demand as needs emerge.

**Likely candidates:** Diff viewer (compare scenarios side-by-side), export to PPTX, sensitivity tornado charts, cost allocation waterfall, Jupyter notebook templates for ad-hoc analysis.

-----

## 11. Task Dependency Map

```
Phase 1 (Data + Config) ────┬──> Phase 2 (LP Dispatch) ──> Phase 3 (Transmission) ──> Phase 4 (Storage)
                             │                                                              │
                             │                                                              v
                             │                                                        Phase 5 (Capacity)
                             │                                                              │
                             │                                                              v
                             │                                                        Phase 6 (Runner)
                             │                                                              │
                             │                                                              v
                             │                                                        Phase 7 (Outputs)
                             │                                                              │
                             │                                                    ┌─────────┼──────────┐
                             │                                                    v         v          v
                             │                                              Phase 8     Phase 9    SA-2 Review
                             │                                             (Frontend) (Learning)  (Phase 7)
                             │
                             ├──> SA-3 (Parameter Citations) — starts after extraction
                             └──> Context folder population — prerequisite for SA-2

SA-1 (Docs)      — runs after every phase merge
SA-2 (Reviewer)  — runs after Phase 2, Phase 5, Phase 7
SA-3 (Citations) — runs after Phase 1, then incrementally
SA-4 (Visuals)   — LP Dispatch after Phase 2; rest after Phase 7
SA-5 (Ad-hoc)    — on demand throughout
```

-----

## 12. GitHub Pages Configuration

The repo serves two GitHub Pages sites from the same branch:

- **Frontend:** `market-sim/frontend/` → main results dashboard
- **Learning Hub:** `market-sim/learning-hub/` → visual explainers

Simple root `index.html` routes to both. No build step, no CI/CD for pages — push and it’s live. Model runs happen locally; results exported to JSON and committed.