# Market Simulation Model — Session Task Registry

**Generated from:** `build-plan.md` + `market-sim-methodology.md`
**Purpose:** Every task below is scoped to fit within a single Claude session. Tasks are ordered by dependency, grouped by build phase, and tagged with inputs, outputs, and quality gates so any session can pick up where the last left off.

**How to use this document:** Start at Session 1.1 and work forward. Each session has a clear deliverable and a “done when” checklist. When starting a new session, paste the relevant session block as context along with any files it depends on.

-----

## Legend

- **Depends on:** Sessions that must be complete before starting
- **Inputs:** Files or artifacts the session needs access to
- **Outputs:** Files created or modified
- **Done when:** Checklist that confirms the session is complete
- **Estimated scope:** Rough session complexity (light / moderate / heavy)

-----

## Phase 1 — Project Skeleton + Data Layer

### Session 1.1: Repository Scaffolding

**Depends on:** Nothing — this is the starting point
**Estimated scope:** Light

Create the repo directory structure, `pyproject.toml`, `CONVENTIONS.md`, and all `__init__.py` files. No logic — just the skeleton.

**Tasks:**

1. Create the full directory tree from the build plan §1 (src/, frontend/, learning-hub/, context/, docs/, data/, scripts/, tests/).
1. Write `pyproject.toml` with the exact dependency list from build plan §8 (highspy, numpy, pandas, pyarrow, pydantic, pyyaml; dev: pytest, ruff).
1. Write `CONVENTIONS.md` covering file naming, module naming, function naming, constants rules, git conventions, documentation rules, data file rules, and frontend conventions — all per build plan §1.
1. Create placeholder `__init__.py` in every Python package.
1. Create `CHANGELOG.md` with a dated “Phase 1 started” entry.
1. Create empty stub files for every Python module listed in the directory tree (with module-level docstrings only).

**Outputs:** Full directory tree, `pyproject.toml`, `CONVENTIONS.md`, `CHANGELOG.md`, all stub files
**Done when:** `pip install -e .` succeeds; `import market_sim` works; ruff finds no errors; every module has a docstring.

-----

### Session 1.2: ScenarioConfig Dataclass + YAML Pipeline

**Depends on:** 1.1
**Estimated scope:** Heavy

Build the full `ScenarioConfig` system — the backbone of the entire model’s parameterization.

**Tasks:**

1. Implement `ScenarioConfig` as a Pydantic dataclass in `config/scenarios.py` with all four tiers of parameters (Tier 0 structural, Tier 1 scenario levers, Tier 2 expert, Tier 3 calibration) per methodology spec §4.1.
1. Implement `cache_key()` method — deterministic SHA-256 hash of the full resolved config, truncated to 16 hex chars.
1. Implement YAML loading: load a YAML file, overlay its values onto defaults, return a fully resolved `ScenarioConfig`.
1. Implement `SweepDefinition` and sweep generator: parse a sweep YAML (factorial mode), produce a list of `ScenarioConfig` objects. Deduplicate by cache key.
1. Add tier metadata as class-level annotations or a registry dict so downstream tools can query which tier a parameter belongs to.
1. Write tests: YAML round-trip, cache key determinism, cache key changes when any parameter changes, sweep generator produces correct count, deduplication works.

**Inputs:** Methodology spec §4.1–4.3 for parameter definitions and tiers
**Outputs:** `config/scenarios.py`, tests in `tests/test_scenarios.py`
**Done when:** All tests pass. A YAML with 3 overrides loads correctly. A 3×3 sweep produces 9 configs. Cache key is deterministic across runs.

-----

### Session 1.3: Constants Extraction + Core Data Types

**Depends on:** 1.1
**Estimated scope:** Moderate

Extract all physical and economic constants from the old repo and define the core Pydantic data models.

**Tasks:**

1. Create `config/constants.py` with every constant from the extraction manifest (build plan §3): `EFFICIENCY_BINS`, `GAS_AVAILABILITY_FACTOR`, `CO2_RATES`, `NUCLEAR_MONTHLY_CF`, `DEMAND_GROWTH_RATES`, `CO2_PRICES`, storage tech params, `STATE_RPS_FLOORS`, retirement sigmoid parameters, eGRID emission factors.
1. Every constant gets an inline citation comment: source, date, page/table number.
1. Define Pydantic models in appropriate data modules: `Generator`, `StorageTech`, `Zone`, `TransferLink`, `HourlyInputs`.
1. Define `FleetArrays` dataclass per methodology spec §3.1 (pmax, pmin, heat_rate, vom, emission_rate, nox_rate, zone_idx, fuel_type, availability, unit_id — all numpy arrays).
1. Write a conversion function: list of `Generator` Pydantic models → `FleetArrays`.

**Inputs:** Old repo constants (extraction manifest in build plan §3), methodology spec §3.1
**Outputs:** `config/constants.py`, data type definitions across data modules, `FleetArrays` in `model/dispatch.py` or a shared types module
**Done when:** Every constant has a citation comment. Pydantic models validate sample data. `FleetArrays` conversion round-trips correctly.

-----

### Session 1.4: ISO Configuration + Zone Topology

**Depends on:** 1.3
**Estimated scope:** Light

Define the two ISO configurations: ERCOT 4-zone and CAISO 1-zone + WECC import node.

**Tasks:**

1. Build `config/iso_configs.py` with zone topology definitions: zone names, load allocation percentages, inter-zonal transfer links with TTC values.
1. ERCOT: 4 zones (North, South, West, Houston), 6 bidirectional links per methodology spec §1.3.
1. CAISO: 1 zone + WECC import/export node. Import modeled as pseudo-generators on a stepped supply curve (3–4 tranches). Export capped at ~5 GW.
1. VOLL values per zone (configurable, default $5,000/MWh for ERCOT, $2,000 for CAISO per build plan §5 open items).
1. Write tests: zone counts, link counts, TTC values within expected ranges, VOLL values present.

**Outputs:** `config/iso_configs.py`, tests
**Done when:** Both ISOs fully defined. Transfer link topology matches the spec. Tests pass.

-----

### Session 1.5: EIA Data Loader

**Depends on:** 1.3
**Estimated scope:** Moderate

Build the EIA Hourly Grid Monitor parquet loader, adapted from the old repo’s `eia_data_io.py`.

**Tasks:**

1. Build `data/eia_loader.py` — read EIA Hourly Grid Monitor parquet files, return typed `HourlyInputs` structs.
1. Handle 7 ISOs × multiple years of parquet data. Filter to the requested ISO and weather year.
1. Validate on load: assert 8,760 rows, no NaN values, peak demand matches known reference values.
1. Extract demand profiles, wind/solar generation profiles (for deriving capacity factors).
1. Write tests with sample/mock parquet data: row count, NaN check, peak demand check.

**Inputs:** Old repo `eia_data_io.py` (128 lines) for reference, EIA parquet file format
**Outputs:** `data/eia_loader.py`, tests
**Done when:** Loader reads a parquet, returns typed structs. All validation assertions pass on real data. Tests pass.

-----

### Session 1.6: Fleet Builder + Renewable Profile Loader

**Depends on:** 1.3, 1.5
**Estimated scope:** Moderate

Build the generator fleet from EIA-860 data and the renewable capacity factor profile loader.

**Tasks:**

1. Build `data/fleet.py` — construct generator fleet from EIA-860 data with heat rate bins (3 bins × 3 fuel classes per extraction manifest).
1. Assign generators to zones based on ISO config.
1. Apply deterministic outage derate: `Pmax × availability[g,t]` where `availability = (1 - EFORd) × seasonal_factor`.
1. Build `data/renewables.py` — load wind/solar CF profiles from EIA Hourly Grid Monitor (actual gen / installed capacity). Document the ~5% embedded curtailment conservatism.
1. Implement struct-of-arrays conversion: fleet of Generator objects → `FleetArrays` numpy arrays.
1. Write tests: total fleet capacity within 5% of known installed capacity, CF profiles in [0,1] range, `FleetArrays` shapes match.

**Outputs:** `data/fleet.py`, `data/renewables.py`, tests
**Done when:** Fleet builds for both ERCOT and CAISO. Total capacity passes the 5% check. CF profiles load cleanly. `FleetArrays` conversion works.

-----

### Session 1.7: Fuel Price Loader + Marginal Cost Assembly

**Depends on:** 1.2, 1.3
**Estimated scope:** Moderate

Build the gas price / carbon price / basis curve loaders and the vectorized marginal cost assembly function.

**Tasks:**

1. Build `data/fuel.py` — gas price path loader (low/mid/high trajectories), basis differential by zone, carbon price trajectory, NOx price.
1. Prices should be resolvable to (n_gen, 8760) or (8760,) arrays based on fuel type mapping.
1. Implement `assemble_mc()` per methodology spec §3.2 — fully vectorized, returns `(n_gen, 8760)` marginal cost array. Extensible via `**adders` keyword arguments.
1. Write tests: MC assembly with known inputs produces expected output. Carbon price adder shifts costs correctly. Zero carbon price = no change.

**Outputs:** `data/fuel.py`, `assemble_mc()` function, tests
**Done when:** Fuel prices load for all three paths. MC assembly is fully vectorized (no Python loops). Tests pass.

-----

## Phase 2 — LP Dispatch Engine

### Session 2.1: Variable Layout + Cost Vector Construction

**Depends on:** 1.3, 1.7
**Estimated scope:** Moderate

Build the LP variable indexing system and objective function assembly. This is foundational to everything in the dispatch engine.

**Tasks:**

1. In `model/dispatch.py`, define the variable layout: column index ranges for P[g,t], W[z,t], S[z,t], Chg[s,t], Dis[s,t], SOC[s,t], Flow[l,t], Slack[z,t] per methodology spec §2.2.
1. Write helper functions to map between (variable_type, entity_index, hour) ↔ flat column index.
1. Build cost vector assembly: flat numpy array with thermal MCs, zero for renewables, ε=0.001 for storage, VOLL for slack.
1. Write tests: variable count matches expected total. Index mapping round-trips. Cost vector has correct values at correct positions.

**Outputs:** Variable layout and cost vector code in `model/dispatch.py`, tests
**Done when:** Layout computes correct total column count for ERCOT (4 zones, ~200 generators, storage, 6 links). Cost vector has no hardcoded values.

-----

### Session 2.2: Constraint Matrix — Energy Balance + Generator Bounds

**Depends on:** 2.1
**Estimated scope:** Heavy

Build the block-diagonal constraint matrix for the single-zone case (energy balance + generator bounds). This is the most performance-critical code in the model.

**Tasks:**

1. Build the zone-membership sparse matrix (n_zones × n_gen) per spec §2.2.
1. Build the per-hour prototype constraint block: energy balance rows (n_zones), generator upper bounds (n_gen), generator lower bounds (n_gen), renewable upper bounds (2 × n_zones).
1. Replicate across 8,760 hours using `scipy.sparse.kron` or `block_diag` — NO Python loops over hours.
1. Assemble RHS vectors: demand[z,t] for energy balance, pmax × availability for upper bounds, pmin for lower bounds, CF × capacity for renewable bounds.
1. Write tests: trivial 1-gen, 1-zone, 24-hour case. 2-gen case. Energy balance row sums. Matrix construction completes in < 1 second for full ERCOT fleet.

**Inputs:** Methodology spec §2.1–2.3 for construction pattern
**Outputs:** Matrix construction code in `model/dispatch.py`, tests
**Done when:** Constraint matrix builds for full ERCOT fleet. Sparsity structure is correct. No Python loops over hours. Performance < 1 second.

-----

### Session 2.3: HiGHS Solver Integration + Dual Extraction

**Depends on:** 2.2
**Estimated scope:** Moderate

Wire up the HiGHS solver, run the LP, extract dispatch results and prices from dual variables.

**Tasks:**

1. Implement `solve_dispatch()` — create HiGHS instance, pass CSC matrix, cost vector, bounds. Call `h.run()`.
1. Extract primal solution (dispatch values) and map back to named arrays using variable layout offsets.
1. Extract dual variables from energy balance constraint rows — these are the zonal prices ($/MWh).
1. Package results into a result dataclass: dispatch by generator, zonal prices, renewable dispatch, curtailment (potential - dispatched), unserved energy.
1. Write the canonical test suite from build plan Phase 2: (a) 1 gen flat demand → price = MC, (b) 2 gens demand below cheap cap → price = cheap MC, (c) demand > all capacity → price = VOLL, (d) must-run with excess → negative prices, (e) energy balance: sum(dispatch) + unserved = demand every hour.

**Outputs:** `solve_dispatch()` in `model/dispatch.py`, result dataclass, tests
**Done when:** All 5 canonical tests pass. Dual extraction produces valid prices. Full ERCOT single-zone solves in < 5 seconds.

-----

## Phase 3 — Multi-Zone Transmission

### Session 3.1: Pipe-and-Bubble Transmission Model

**Depends on:** 2.3
**Estimated scope:** Moderate

Add transmission flow variables and modify the energy balance to create zonal price separation.

**Tasks:**

1. Build `model/transmission.py` — flow variables Flow[l,t] with bounds ±TTC[l].
1. Modify energy balance constraints: add flow contributions (imports positive, exports negative) per methodology spec §1.3.
1. Add flow variable columns to the LP variable layout.
1. Build CAISO import pseudo-generators: 3–4 stepped-cost tranches on the WECC node, each modeled as generator variables with their own MC and capacity bounds.
1. Write tests: (a) ERCOT West wind surplus → flows to North/Houston → West price < North price, (b) CAISO high demand → WECC imports at stepped prices, (c) zero TTC → zones fully decouple.

**Inputs:** ISO configs for zone topology and TTC values
**Outputs:** `model/transmission.py`, modified `dispatch.py`, tests
**Done when:** Zonal price separation appears under congestion. Zero-TTC decoupling test passes. CAISO imports work with stepped costs.

-----

## Phase 4 — Storage Co-Optimization

### Session 4.1: Storage Constraint Builder + SOC Dynamics

**Depends on:** 2.3
**Estimated scope:** Heavy

Add storage as LP decision variables with full SOC tracking, cyclic boundary, and round-trip efficiency.

**Tasks:**

1. Build `model/storage.py` — storage parameter structs (4hr Li-ion, 8hr, LDES, H2) from extracted constants.
1. Build the SOC linkage submatrix: banded matrix coupling SOC[s,t] to SOC[s,t-1], Chg[s,t], Dis[s,t] per methodology spec §1.3.
1. Implement cyclic boundary constraint: SOC[s,0] = SOC[s,8759].
1. Integrate storage into the energy balance: discharge adds supply, charge adds demand.
1. Add storage tiebreaker ε = 0.001 $/MWh to the cost vector.
1. Write tests: (a) flat demand, cheap off-peak / expensive on-peak → storage arbitrages, (b) SOC conservation: sum(charge × η) = sum(discharge / η), (c) cyclic boundary holds, (d) round-trip losses: total discharge < total charge × RTE.

**Inputs:** Storage tech parameters from constants, methodology spec §1.3
**Outputs:** `model/storage.py`, integration into `dispatch.py`, tests
**Done when:** All 4 storage tests pass. SOC linkage matrix is vectorized (no hour loops). Storage co-optimizes with dispatch.

-----

## Phase 5 — Capacity Evolution Engine

### Session 5.1: Known Pipeline + Retirement Logic

**Depends on:** 2.3
**Estimated scope:** Moderate

Build the first half of the capacity evolution engine: deterministic retirements and additions from EIA-860 data, plus the economic retirement sigmoid.

**Tasks:**

1. Build `model/capacity.py` — year-over-year fleet evolution framework per methodology spec §5.1.
1. Implement known retirements: EIA-860 announced retirement dates. Unit removed in the specified year.
1. Implement known additions: EIA-860 under-construction units with expected online dates.
1. Implement economic retirement screen: net revenue < going-forward cost for N consecutive years → retirement, least efficient first within fuel class (spec §5.2).
1. Extract retirement sigmoid from old repo `thermal_fleet_mw()` (lines 1837–1890).
1. Write tests: known coal retirements happen on schedule. Sigmoid triggers accelerated retirement at threshold. Retirement ordering follows heat rate.

**Inputs:** Old repo `thermal_fleet_mw()`, EIA-860 fleet data, prior year dispatch results
**Outputs:** `model/capacity.py` (retirement portion), tests
**Done when:** Known retirements match schedule. Sigmoid behavior verified. Economic retirement test passes.

-----

### Session 5.2: New Entry + Learning Curves + IRA Credits

**Depends on:** 5.1
**Estimated scope:** Heavy

Build the economic new entry screen with LCOE, Wright’s Law learning curves, IRA credit application, and build rate caps.

**Tasks:**

1. Extract Wright’s Law `wright_cost()` from old repo step6_1 (lines 540–573).
1. Extract LCOE calculation with IRA credits from step6_1 `get_resource_lcoe()` (lines 876–992).
1. Implement technology-level new entry screen: expected revenue (from prior year price duration curve) vs LCOE → economic if revenue > LCOE.
1. Apply IRA PTC/ITC credits to LCOE reduction per `policy/ira.py`.
1. Cap annual builds per technology (ERCOT ~12 GW/yr queue throughput).
1. Implement technology priority ordering: policy-mandated first, then ranked by revenue-minus-LCOE margin.
1. Build `policy/ira.py` — PTC for wind, ITC for solar/storage. Credit values from IRS Final Rules 2024.
1. Build `policy/rps.py` — state RPS floors (CA SB 100 trajectory). Forces additional clean builds if below target.
1. Write tests: LCOE below expected revenue → entry appears. Queue cap limits builds. RPS floor forces uneconomic clean builds in CAISO.

**Inputs:** Old repo step6_1 learning curves and LCOE, IRS rules, RPS schedules
**Outputs:** `model/capacity.py` (entry portion), `policy/ira.py`, `policy/rps.py`, tests
**Done when:** Learning curves reduce costs over time. IRA credits reduce LCOE. Queue caps bind. RPS test passes for CAISO.

-----

### Session 5.3: Full Capacity Evolution Integration + Year Loop

**Depends on:** 5.1, 5.2
**Estimated scope:** Moderate

Wire together the complete year-over-year evolution loop and test multi-year fleet trajectories.

**Tasks:**

1. Extract year-loop skeleton from old repo `step2_3_de_pathway_tf.py` (lines 546–814). Adapt to the one-pass architecture.
1. Integrate: known retirements → economic retirements → known additions → economic entry → RPS compliance → updated fleet.
1. Build `policy/carbon.py` — carbon price adder logic (simple: adds to MC via `assemble_mc()`, tagged `kind: "adder"`).
1. Implement the policy constraint extension point from spec §1.4: LP builder checks for active constraint-type policies, appends rows if flagged.
1. Write tests: 3-year trajectory with known inputs. Fleet evolves correctly. Two scenarios diverge only on gas price → fleets identical year 1, diverge later.

**Outputs:** Complete `model/capacity.py`, `policy/carbon.py`, integration tests
**Done when:** A 5-year trajectory runs end-to-end. Fleet changes are deterministic and reproducible. Policy extension point exists (even if no constraint-type policies are active yet).

-----

## Phase 6 — Scenario Runner + Caching

### Session 6.1: Parquet Cache + Single-Run CLI

**Depends on:** 5.3
**Estimated scope:** Moderate

Build the result caching layer and single-scenario CLI runner.

**Tasks:**

1. Build `results/cache.py` — Parquet-based caching at `results/{iso}/{cache_key}/year_{YYYY}.parquet` plus `config.yaml`.
1. Implement check-before-run: if parquet exists, skip that year.
1. Build `results/outputs.py` — result dataclass definitions with all hourly output fields: dispatch by generator, zonal prices, emissions, storage SOC/charge/discharge, curtailment, capacity factors, unserved energy, inter-zonal flows.
1. Build `runner.py` — main orchestrator. Single-run mode: `python -m market_sim run --config scenario.yaml`.
1. Log the full resolved ScenarioConfig at the start of every run.
1. Write tests: run 1 scenario × 3 years → cached → re-run skips all 3. Corrupt one cache file → only that year re-runs.

**Outputs:** `results/cache.py`, `results/outputs.py`, `runner.py`, CLI entry point, tests
**Done when:** Single scenario runs end-to-end for 3+ years. Caching works. Re-run skips completed years. CLI accepts YAML.

-----

### Session 6.2: Batch Sweep + Parallel Execution

**Depends on:** 6.1
**Estimated scope:** Moderate

Add sweep mode and parallel execution across (config, iso) pairs.

**Tasks:**

1. Add sweep CLI: `python -m market_sim sweep --sweep sweep_definition.yaml`.
1. Implement `ProcessPoolExecutor` parallelism per methodology spec §6.1 — independent work units are (scenario_config, iso) pairs; years run sequentially within each.
1. Implement memory management per spec §6.3: fresh HiGHS instance per solve, write to Parquet immediately, don’t accumulate LP objects.
1. Write tests: parallel and serial produce identical results. Two sweeps share cached results. Deduplication by cache key works.

**Outputs:** Sweep mode in `runner.py`, tests
**Done when:** A 2×2 sweep runs on 2+ cores. Results match serial execution. Deduplication works across sweep files.

-----

## Phase 7 — Outputs + Emissions + Calibration

### Session 7.1: Emissions Accounting + Output Export

**Depends on:** 6.1
**Estimated scope:** Moderate

Build the vectorized emissions calculation and the JSON export pipeline for the frontend.

**Tasks:**

1. Build `results/emissions.py` — vectorized emissions: `dispatch × emission_rate_array` (struct-of-arrays, no loops).
1. Build `results/export.py` — convert cached Parquets → JSON for frontend consumption. Per-scenario JSON under 2 MB (aggregate hourly → daily or summary stats).
1. Build `scripts/export_results.py` — CLI script that runs the export pipeline.
1. Define the Parquet schema formally in `docs/data-dictionary.md`: every column, type, unit, range.
1. Write tests: emissions sum is correct for a known dispatch. Export produces valid JSON under size limit.

**Outputs:** `results/emissions.py`, `results/export.py`, `scripts/export_results.py`, data dictionary
**Done when:** Emissions calculation is fully vectorized. Export produces loadable JSON. Data dictionary covers all fields.

-----

### Session 7.2: Calibration Framework + Validation

**Depends on:** 7.1
**Estimated scope:** Heavy

Build the calibration framework and run the first validation pass.

**Tasks:**

1. Extract calibration framework structure from old repo `calibrate_lmp_model.py` (adapt, don’t copy dispatch logic).
1. Extract P10/P50/P90 fan-band framework from `validate_market_forecasts.py`.
1. Implement calibration diagnostic order: (1) generation mix by fuel type ±5% of benchmarks, (2) price duration curve shape, (3) average price, (4) capacity factors.
1. Implement workflow: input parity check → dispatch comparison → price comparison.
1. Build `docs/calibration-log.md` — running log of calibration attempts, results, and parameter adjustments.
1. Write tests: calibration check correctly flags a scenario that’s >5% off on gen mix.

**Outputs:** Calibration code, `docs/calibration-log.md`, validation tests
**Done when:** Calibration framework runs against at least one scenario. Diagnostic output is produced. ±5% gen mix check works.

-----

## Phase 8 — Interactive Frontend

### Session 8.1: Frontend Skeleton + Design System

**Depends on:** 7.1
**Estimated scope:** Moderate

Build the shared HTML/CSS/JS skeleton, routing, and design system for the GitHub Pages frontend.

**Tasks:**

1. Create `frontend/css/style.css` — consistent design system: fuel/resource color tokens, typography, layout grid, responsive breakpoints (desktop-first).
1. Create `frontend/js/app.js` — core routing and state management (no framework — vanilla JS).
1. Create `frontend/js/data-loader.js` — fetch JSON from `data/` directory, lazy-load per-scenario files.
1. Create `frontend/index.html` — shell with navigation to all three pages.
1. Establish CDN imports for Plotly.js and D3.js.
1. Apply `localStorage` key prefix convention: `marketsim_`.

**Outputs:** Frontend skeleton files, design system CSS
**Done when:** Shell loads in browser. Navigation works. Data loader fetches a sample JSON successfully.

-----

### Session 8.2: Results Dashboard (index.html)

**Depends on:** 8.1, 7.1
**Estimated scope:** Heavy

Build the scenario results explorer dashboard with Plotly charts.

**Tasks:**

1. Build scenario selector (dropdown or matrix grid).
1. Build generation mix stacked area chart (2026–2050) per selected scenario.
1. Build emissions trajectory line chart.
1. Build price duration curves by zone.
1. Build storage utilization heatmap.
1. All charts via Plotly.js, using the fuel color tokens from the design system.
1. Lazy-load per-scenario JSON on selection.
1. Write manual test: load a scenario JSON → verify all 4 chart types render without console errors.

**Outputs:** Complete `frontend/index.html`, `frontend/js/charts.js`
**Done when:** Dashboard renders all 4 chart types from exported JSON. Scenario switching works. No console errors.

-----

### Session 8.3: Decision Tracker + Parameter Browser

**Depends on:** 8.1
**Estimated scope:** Moderate

Build the design decision tracker and parameter citation browser pages.

**Tasks:**

1. Build `frontend/decisions.html` — collapsible decision domains, radio buttons + notes textarea for open decisions, read-only with green checkmarks for decided items.
1. Build `frontend/js/decisions.js` — form submission caches to `localStorage` (`marketsim_decision_{id}`). Export button dumps all decisions as JSON.
1. Build `frontend/parameters.html` — searchable/filterable table of every model parameter from `parameters.json`. Filter by domain. Click-to-expand for full citation details.
1. Write tests: fill a decision form → reload → confirm localStorage persists. Parameter table renders and filters correctly.

**Outputs:** `decisions.html`, `parameters.html`, `decisions.js`
**Done when:** Decision forms persist across reload. Export works. Parameter table is searchable and filterable.

-----

## Phase 9 — Learning Hub (Scrollytell)

### Session 9.1: Shared Scrollytell Framework

**Depends on:** Nothing (can run in parallel with later phases)
**Estimated scope:** Moderate

Build the reusable scrollytell engine that all learning hub pages share.

**Tasks:**

1. Build `learning-hub/shared/scrollytell.js` — lightweight engine using Intersection Observer API for scroll-triggered transitions. Sticky chart panels. Narrative text blocks.
1. Build `learning-hub/shared/scrollytell.css` — responsive layout (mobile + desktop), consistent typography, fuel color tokens matching the frontend.
1. Build `learning-hub/index.html` — landing page with navigation to all 5 topic pages.
1. Test on mobile viewport: sticky panels work, scroll triggers fire.

**Outputs:** Shared scrollytell framework, learning hub landing page
**Done when:** A test page with placeholder content scrolls correctly on desktop and mobile. Transitions trigger on scroll.

-----

### Session 9.2: LP Dispatch Scrollytell

**Depends on:** 9.1, 2.3
**Estimated scope:** Heavy

Build the first and highest-priority scrollytell explainer: “How the model decides who generates.”

**Tasks:**

1. Build `learning-hub/lp-dispatch/index.html` — narrative + interactive visualization.
1. Create simplified 5-generator, 24-hour example with D3 visuals.
1. Animate merit order stacking.
1. Show LP solver choosing dispatch levels.
1. Explain dual variable = price with visual proof.
1. Side-by-side comparison: heuristic vs. LP results.
1. Use actual model results where possible, synthetic data where pedagogically clearer.

**Outputs:** Complete LP Dispatch scrollytell page
**Done when:** Page tells the full story from merit order through LP pricing. Animations trigger on scroll. Works on mobile.

-----

### Session 9.3: Capacity Evolution Scrollytell

**Depends on:** 9.1, 5.3
**Estimated scope:** Moderate

**Tasks:**

1. Build `learning-hub/capacity-evolution/index.html`.
1. Animated fleet waterfall chart 2026–2050 showing retirements and additions.
1. Sigmoid retirement trigger visualization.
1. Wright’s Law cost curve animation.

**Outputs:** Capacity evolution scrollytell page
**Done when:** Waterfall chart animates on scroll. Sigmoid and learning curve explanations are clear.

-----

### Session 9.4: Remaining Scrollytell Pages

**Depends on:** 9.1, 4.1, 3.1
**Estimated scope:** Heavy (3 pages)

Build the remaining three scrollytell pages. Can be split across multiple sessions if needed.

**Tasks:**

1. **Storage Co-optimization** — `learning-hub/storage-cooptimization/`: animated SOC profile, greedy vs. LP comparison, RTE loss visualization.
1. **Transmission & Zonal Pricing** — `learning-hub/transmission-pricing/`: map-based ERCOT 4-zone with animated flows, congestion → price divergence, copper-plate vs. zonal.
1. **Scenario Uncertainty** — `learning-hub/scenario-uncertainty/`: interactive fan chart builder, toggle scenario dimensions, P10/P50/P90 bands respond.

**Outputs:** Three scrollytell pages
**Done when:** All 5 learning hub pages are live and navigable from the landing page.

-----

## Sub-Agent Sessions

These run on their own cadence, triggered by the completion of specific build phases.

### Session SA-1: Documentation Pass (runs after each phase)

**Depends on:** Completion of any build phase
**Estimated scope:** Moderate per pass

**Tasks per pass:**

1. Update `docs/architecture.md` to reflect current module structure.
1. Update `docs/data-dictionary.md` with any new fields, types, ranges.
1. Update `docs/lp-formulation.md` if dispatch/storage/transmission constraints changed.
1. Append new decisions to `docs/decision-log.md` with date and rationale.
1. Update `CHANGELOG.md` with dated entries.
1. Audit: every public function has a docstring. Flag any that don’t.

**Done when:** All public functions documented. Data dictionary covers all Parquet columns. Architecture diagram matches reality.

-----

### Session SA-2: Expert Review (runs after Phase 2, 5, 7)

**Depends on:** Phase 2, Phase 5, or Phase 7 completion
**Estimated scope:** Heavy

**Tasks:**

1. Populate `context/` folder with methodology summaries of reference models (Aurora, PLEXOS, ReEDS, IPM, GenX, US-REGEN, Cambium, eGRID) and the cross-model comparison matrix.
1. Review LP formulation against standard production cost modeling practice.
1. Review capacity evolution against established capacity expansion approaches.
1. Review storage formulation against NREL ATB defaults.
1. Review scenario architecture — is the parameter space sufficient?
1. Produce `docs/reviewer-notes.md` with finding → implication → recommendation format and severity tags ([CRITICAL], [IMPORTANT], [MINOR]).

**Done when:** Reviewer notes document is complete. All CRITICAL findings have a response plan.

-----

### Session SA-3: Parameter Citation Audit

**Depends on:** 1.3 (initial), then incremental after each phase
**Estimated scope:** Moderate

**Tasks:**

1. Build `docs/parameter-citations.md` — full citation for every constant.
1. Build `frontend/data/parameters.json` — machine-readable citation registry matching the §9 schema (param_id, display_name, value, unit, domain, tier, source, source_date, page_or_table, url, notes, old_repo_location, last_verified).
1. Trace every constant to a primary source. Flag parameters where source is another model’s assumption.
1. Flag parameters older than 3 years for refresh review.
1. Build `scripts/validate_parameters.py` — cross-checks every constant in `constants.py` and every default in `ScenarioConfig` has a matching entry in `parameters.json`.

**Done when:** `validate_parameters.py` passes with zero missing citations. Every parameter has all required fields populated.

-----

## Dependency Quick-Reference

```
1.1 ──┬── 1.2
      ├── 1.3 ──┬── 1.4
      │         ├── 1.5 ──── 1.6
      │         └── 1.7
      │              │
      └──────────────┴── 2.1 ── 2.2 ── 2.3 ── 3.1 ── 4.1
                                                         │
                                              5.1 ── 5.2 ── 5.3
                                                              │
                                                    6.1 ── 6.2
                                                     │
                                              7.1 ── 7.2
                                               │
                                        8.1 ──┬── 8.2
                                              └── 8.3

9.1 ──┬── 9.2
      ├── 9.3
      └── 9.4

SA-1: after each phase merge
SA-2: after 2.3, 5.3, 7.2
SA-3: after 1.3, then incremental
```

-----

## Session Checklist Template

Copy this to the top of each session’s conversation:

```
SESSION: [number]
PHASE: [phase name]
DEPENDS ON (completed): [list]
GOAL: [one sentence]
KEY FILES TO REFERENCE:
  - build-plan.md §[relevant sections]
  - market-sim-methodology.md §[relevant sections]
  - [any outputs from prior sessions]
QUALITY GATE: [from build plan §6]
```