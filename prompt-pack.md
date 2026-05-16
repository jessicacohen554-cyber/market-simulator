# Market Sim — Reconciled Session Registry + Prompt Pack

**Merged from:** `Session-tasks.md` (metadata, dependencies, quality gates) + `prompt-pack.md` (copy-pasteable Claude Code prompts). This is the single authoritative document.

**How to use:** Work top to bottom. Each session has metadata (for you) and a prompt block (for Claude Code). Copy the fenced prompt into Claude Code, wait for completion, verify the “Done when” checklist, commit, move on.

**Tags:**

- 📂 **NEEDS DATA** — requires real data files on disk (EIA parquets, EIA-860 fleet data). Skip on first pass if data isn’t ready; come back later.
- 🔧 **CORE** — critical path for the LP engine. Do these first.
- 🧪 **QA** — testing/validation session. Don’t skip.

-----

## Phase 0 — Repo Scaffold

### Session 0.1: Initialize Project Structure

**Depends on:** Nothing
**Scope:** Light
**Outputs:** Full directory tree, `pyproject.toml`, `CONVENTIONS.md`, `CHANGELOG.md`, stub files
**Done when:** `pip install -e .` succeeds; `import market_sim` works; ruff finds no errors

```
Create the project skeleton for market-sim. Do NOT write any logic yet — just structure and stubs.

1. pyproject.toml with:
   name = "market-sim"
   requires-python = ">=3.11"
   dependencies: highspy>=1.7, numpy>=1.26, scipy>=1.12, pandas>=2.1, pyarrow>=14.0, pydantic>=2.5, pyyaml>=6.0
   optional dev deps: pytest>=8.0, ruff>=0.5
   console script: market-sim = "market_sim.runner:main"

2. Directory tree with empty __init__.py files:
   src/market_sim/ with subpackages: config/, data/, model/, policy/, results/
   tests/
   data/ (with subdirs: eia_hourly/, fleet/, reference/)
   docs/
   scripts/
   frontend/ (with subdirs: css/, js/, data/, data/results/)
   learning-hub/shared/
   context/

3. CONVENTIONS.md with these rules:
   - Python snake_case.py, frontend kebab-case
   - Public functions: verb_noun naming
   - Single-letter vars only t/g/z/s in LP construction with comment
   - Constants in config/constants.py with citation comments
   - Feature branches: phase-N/description
   - Commits: imperative present tense
   - Every public function needs a docstring
   - Raw data in data/ never modified in place

4. Empty CHANGELOG.md with a header and dated "Phase 0 started" entry.

5. Minimal README.md: project name, one-line description, "See CLAUDE.md for build instructions"

6. Create empty stub files (module-level docstrings only) for every Python module in the directory tree:
   config/scenarios.py, config/constants.py, config/iso_configs.py
   data/eia_loader.py, data/fleet.py, data/renewables.py, data/fuel.py
   model/dispatch.py, model/transmission.py, model/storage.py, model/capacity.py
   policy/ira.py, policy/rps.py, policy/carbon.py
   results/cache.py, results/outputs.py, results/emissions.py, results/export.py
   runner.py

Don't write any Python logic. Just the skeleton.
```

-----

## Phase 1 — Config & Data Layer

### Session 1.1: ScenarioConfig Dataclass + YAML Pipeline 🔧

**Depends on:** 0.1
**Scope:** Heavy
**Outputs:** `config/scenarios.py`, `tests/test_config.py`
**Done when:** All tests pass. YAML with 3 overrides loads correctly. 3×3 sweep → 9 configs. Cache key deterministic.

```
Build src/market_sim/config/scenarios.py

This is the central configuration system. Create:

1. ScenarioConfig as a Python dataclass (not Pydantic — plain dataclass with defaults):

   Tier 0 (structural):
   - weather_year: int = 2024
   - iso: str = "ERCOT"
   - voll: float = 5000.0  # $/MWh, ERCOT default
   - hours: int = 8760

   Tier 1 (scenario levers):
   - gas_price_path: str = "mid"  # "low", "mid", "high" or path to CSV
   - carbon_price: float = 0.0  # $/ton CO2
   - nox_price: float = 0.0  # $/ton NOx
   - demand_growth_rate: float = 0.01  # annual
   - renewable_buildout_pace: str = "mid"  # "slow", "mid", "aggressive"
   - storage_deployment: str = "mid"
   - retirement_aggressiveness: str = "mid"

   Tier 2 (expert/sensitivity):
   - storage_rte_4hr: float = 0.85
   - storage_rte_8hr: float = 0.80
   - discount_rate: float = 0.08
   - retirement_consecutive_years: int = 2
   - sigmoid_midpoint: float = 0.50
   - sigmoid_steepness: float = 12.0
   - fixed_om_gas_cc: float = 12.0  # $/kW-yr
   - fixed_om_gas_ct: float = 8.0
   - fixed_om_coal: float = 40.0
   - ira_ptc_wind: float = 26.0  # $/MWh
   - ira_itc_solar: float = 0.30  # 30%
   - ira_itc_storage: float = 0.30
   - ira_expiry_year: int = 2035

   Tier 3 (calibration):
   - renewable_cf_adjustment: float = 1.0
   - basis_differential_factor: float = 1.0

2. Methods:
   - cache_key() -> str: SHA256 hash of the full config dict, truncated to 16 chars
   - to_yaml(path) and from_yaml(path): round-trip YAML serialization. Only non-default values in YAML. Loading merges overrides onto defaults.
   - to_yaml_full(path): write all fields for reproducibility
   - with_overrides(**kwargs) -> ScenarioConfig: return modified copy

3. TIER_TAGS dict mapping field name -> tier number (for metadata/frontend use)

4. SweepDefinition dataclass:
   - sweep: dict[str, list] — parameter name to list of values
   - mode: str = "factorial"
   - generate() -> list[ScenarioConfig]: cartesian product
   - from_yaml(path) class method

5. Tests in tests/test_config.py:
   - Default config cache_key is deterministic (call twice, same result)
   - Changing one parameter changes the cache_key
   - YAML round-trip: write config, read back, assertEqual
   - YAML with partial overrides: unspecified fields keep defaults
   - to_yaml only writes non-default values
   - with_overrides doesn't mutate original
   - Sweep with 2 params × 3 values each → 6 configs, all unique cache keys
   - Sweep from_yaml loads correctly
```

-----

### Session 1.2: Constants Extraction 🔧

**Depends on:** 0.1
**Scope:** Moderate
**Outputs:** `config/constants.py`
**Done when:** Every constant has a citation comment. File imports without error.

```
Build src/market_sim/config/constants.py

This is a pure data file — no logic, no imports except typing. Every value has an inline citation comment.

Include these constants:

# Efficiency bins (heat rate in MMBtu/MWh) by fuel class
HEAT_RATE_BINS — gas_cc (h_class 6.3, f_class 6.7, older 7.5), gas_ct (aero 9.0, frame 10.5, older 11.5), coal (supercritical 8.8, subcritical 10.0, older 10.8)
Source: EIA Table 8.1, 2024

# CO2 emission rates (tCO2/MWh) — derived from heat rate × fuel emission factor
CO2_RATES — by fuel class and efficiency bin. Source: EPA eGRID 2022

# NOx rates (tons NOx/MWh) by class. Source: EPA CEMS 2022

# Variable O&M ($/MWh) by fuel type. Source: NREL ATB 2024

# Gas availability factors: ERCOT 0.83, CAISO 0.88. Source: NERC GADS

# Nuclear monthly CF (12 values per ISO). Source: NRC PRIS 2019-2023

# EFORd by technology. Source: NERC GADS

# Demand growth rates: low/mid/high × ERCOT/CAISO. Source: ERCOT CDR, CAISO IEPR

# Gas price paths: low/mid/high × ERCOT/CAISO ($/MMBtu delivered). Source: EIA AEO 2024
# Gas price escalation rate. Source: EIA AEO 2024

# Carbon price trajectories: zero/low/mid/high keyed by year. Source: RFF/state programs

# Storage tech params: li_ion_4hr, li_ion_8hr, iron_air — duration, RTE, cycles, cost, learning rate
Source: NREL ATB 2024, DOE LDES Liftoff

# State RPS floors: CAISO SB 100 trajectory. Source: CA SB 100

# Queue caps (GW/yr): ERCOT 12, CAISO 8. Source: ERCOT CDR, CAISO TPP

# New entry technology costs: wind, solar, gas_cc — capex, FOM, learning rate, base CF, lifetime
Source: NREL ATB 2024

# Wright's Law reference capacities (GW global installed). Source: IRENA 2024

# Model-wide: STORAGE_TIEBREAKER_EPSILON = 0.001, HOURS_PER_YEAR = 8760, START_YEAR = 2026, END_YEAR = 2050

Add a module docstring explaining this is the single source of truth for physical and economic constants.
```

-----

### Session 1.3: ISO Topology Configs 🔧

**Depends on:** 0.1
**Scope:** Light
**Outputs:** `config/iso_configs.py`, `tests/test_iso_config.py`
**Done when:** Both ISOs defined. All links reference valid zones. Tests pass.

```
Build src/market_sim/config/iso_configs.py

Define the physical topology for each ISO using Pydantic models:

1. Zone model: name (str), iso (str), load_share (float — fraction of total ISO load)

2. TransferLink model: from_zone (str), to_zone (str), ttc_mw (float), is_bidirectional (bool = True)

3. ISOConfig model: zones, links, voll, properties for n_zones, zone_names, n_links.
   validate_topology() method: check link endpoints reference valid zones, load shares sum to 1.0

4. ERCOT config:
   Zones: North (0.38), South (0.20), West (0.08), Houston (0.34)
   Links (6 bidirectional): North↔South 5000 MW, North↔West 3000 MW, North↔Houston 8000 MW,
   South↔Houston 4000 MW, South↔West 2000 MW, West↔Houston 2500 MW
   VOLL: $5,000/MWh
   (TTCs are placeholder — mark with TODO: verify from ERCOT CDR)

5. CAISO config:
   Zones: CAISO_main (1.0), WECC_import (0.0 — not a load zone)
   Links: WECC_import→CAISO_main 15000 MW
   VOLL: $2,000/MWh

6. get_iso_config(iso_name: str) -> ISOConfig factory function

Tests in tests/test_iso_config.py:
- ERCOT has 4 zones, load shares sum to 1.0
- CAISO has 2 zones (1 real + 1 import node)
- All links reference valid zone names
- Unknown ISO raises ValueError
- CAISO VOLL is 2000
```

-----

### Session 1.4: Pydantic Data Models + FleetArrays 🔧

**Depends on:** 1.2
**Scope:** Moderate
**Outputs:** `data/fleet.py`, `tests/test_fleet.py`
**Done when:** Generator model validates. FleetArrays conversion works. Shapes match.

```
Build src/market_sim/data/fleet.py

1. FUEL_TYPE_MAP dict: gas_cc=0, gas_ct=1, coal=2, nuclear=3, wind=4, solar=5, hydro=6, import=7

2. Generator Pydantic model:
   unit_id: str, name: str, zone: str, fuel_type: str, efficiency_bin: str = "default"
   pmax_mw: float, pmin_mw: float = 0.0, heat_rate: float = 0.0
   vom: float = 0.0, emission_rate_co2: float = 0.0, nox_rate: float = 0.0
   eford: float = 0.05, online_year: int = 2000, retirement_year: int | None = None
   is_must_run: bool = False

3. FleetArrays dataclass (plain dataclass, NOT Pydantic):
   pmax, pmin, heat_rate, vom, emission_rate, nox_rate: np.ndarray (n_gen,)
   zone_idx: np.ndarray int (n_gen,)
   fuel_type_idx: np.ndarray int (n_gen,)
   availability: np.ndarray (n_gen, T)
   unit_ids: list[str]
   n_gen property

4. generators_to_fleet_arrays(generators, zone_names, hours=8760) -> FleetArrays
   Availability = (1 - eford) broadcast to all hours (seasonal factors applied later).

5. Tests in tests/test_fleet.py:
   - Create 3 generators (gas_cc, gas_ct, coal) in 2 zones, convert to FleetArrays
   - Verify shapes: pmax (3,), availability (3, T)
   - zone_idx correctly maps zone names
   - fuel_type_idx matches FUEL_TYPE_MAP
   - availability = (1 - eford) for each generator
   - unit_ids list matches
```

-----

### Session 1.5: Marginal Cost Assembly 🔧

**Depends on:** 1.4
**Scope:** Light
**Outputs:** `assemble_mc()` added to `data/fleet.py`, additional tests in `tests/test_fleet.py`
**Done when:** MC assembly is fully vectorized. All test cases pass.

```
Add the assemble_mc function to src/market_sim/data/fleet.py

def assemble_mc(
    fleet: FleetArrays,
    fuel_prices: np.ndarray,   # (n_gen, T) or broadcastable
    carbon_price: np.ndarray | float,  # (T,) or scalar
    nox_price: np.ndarray | float = 0.0,
    **adders: tuple[np.ndarray, np.ndarray]  # (rate_array, price_array) pairs
) -> np.ndarray:
    """Returns (n_gen, T) marginal cost array. Fully vectorized — no loops.
    mc = heat_rate × fuel_price + vom + emission_rate × carbon_price + nox_rate × nox_price + ..."""

Use numpy broadcasting: heat_rate[:, None] * fuel_prices, etc.
Handle scalar and array carbon_price/nox_price.
**adders kwarg: each value is (generator_rate_array, hourly_price_array) for extensibility.

Append tests to tests/test_fleet.py:
- 1 gen, constant fuel price → mc = heat_rate * fuel_price + vom
- 2 gens with different heat rates → different mc values
- Carbon price increases mc proportional to emission_rate
- Custom adder (e.g. SO2) works correctly
- Time-varying fuel price produces time-varying mc
```

-----

### Session 1.6: EIA Data Loader 📂 NEEDS DATA

**Depends on:** 1.4
**Scope:** Moderate
**Outputs:** `data/eia_loader.py`, `tests/test_eia_loader.py`
**Done when:** Loader reads real EIA parquets, returns typed structs. 8760 rows, no NaNs, peak demand matches.

```
Build src/market_sim/data/eia_loader.py

Read EIA Hourly Grid Monitor parquet files and return typed data structs.

1. HourlyInputs Pydantic model:
   demand: np.ndarray (n_zones, 8760) MW
   wind_generation: np.ndarray (n_zones, 8760) MW
   solar_generation: np.ndarray (n_zones, 8760) MW
   interchange: np.ndarray (8760,) MW (net imports, CAISO only)

2. Function: load_eia_hourly(iso: str, year: int, data_dir: Path) -> HourlyInputs
   - Read parquet from data/eia_hourly/
   - Filter to requested ISO and year
   - Validate: assert 8760 rows, no NaN, peak demand > 0
   - For multi-zone ISOs (ERCOT), allocate total demand to zones using load_share from iso_configs

3. Function: derive_capacity_factors(generation_mw, installed_capacity_mw) -> np.ndarray
   CF = actual_gen / installed_capacity. Document the ~5% embedded curtailment conservatism.

Tests (use sample parquet or mock data):
- Row count = 8760
- No NaN values
- Peak demand within expected range for ISO
- CF values in [0, 1] range
```

-----

### Session 1.7: Fleet Builder + Renewable Profiles 📂 NEEDS DATA

**Depends on:** 1.4, 1.6
**Scope:** Moderate
**Outputs:** `data/fleet.py` (fleet builder functions), `data/renewables.py`, tests
**Done when:** Fleet builds for ERCOT and CAISO. Total capacity within 5% of known. CF profiles clean.

```
Add fleet builder functions to src/market_sim/data/fleet.py and build src/market_sim/data/renewables.py

1. In fleet.py, add:
   def build_fleet_from_eia860(iso: str, year: int, data_dir: Path) -> list[Generator]:
   - Read EIA-860 generator data from data/fleet/
   - Assign efficiency bins using HEAT_RATE_BINS from constants
   - Assign emission rates from CO2_RATES and NOX_RATES
   - Assign VOM from constants
   - Assign generators to zones based on ISO config
   - Return list of Generator objects

2. Build data/renewables.py:
   def load_renewable_profiles(iso: str, year: int, data_dir: Path) -> tuple[np.ndarray, np.ndarray]:
   """Load wind and solar CF profiles from EIA Hourly Grid Monitor.
   Returns (wind_cf, solar_cf) each (n_zones, 8760)."""
   - Derive from EIA hourly generation / installed capacity
   - Apply renewable_cf_adjustment from ScenarioConfig
   - Document embedded ~5% curtailment conservatism

3. Seasonal availability factors:
   def apply_seasonal_factors(fleet: FleetArrays, iso: str) -> FleetArrays:
   Apply nuclear monthly CF and gas availability factors from constants.

Tests:
- Total fleet capacity within 5% of known installed capacity for ERCOT
- CF profiles in [0, 1] range
- Seasonal factors correctly applied (nuclear dips in spring/fall)
```

-----

### Session 1.8: Fuel Price Loader 📂 NEEDS DATA

**Depends on:** 1.1, 1.2
**Scope:** Moderate
**Outputs:** `data/fuel.py`, `tests/test_fuel.py`
**Done when:** Fuel prices resolve for all three paths. Prices are (n_gen, T) or broadcastable.

```
Build src/market_sim/data/fuel.py

Gas price, carbon price, and basis curve loaders.

1. def resolve_gas_prices(config: ScenarioConfig, fleet: FleetArrays, year: int) -> np.ndarray:
   """Returns (n_gen, T) fuel price array in $/MMBtu.
   Maps gas_price_path (low/mid/high) to per-ISO delivered prices from constants.
   Applies annual escalation for years beyond 2026.
   Assigns prices to generators based on fuel_type_idx.
   Non-gas generators get 0 (or their respective fuel cost)."""

2. def resolve_carbon_price(config: ScenarioConfig, year: int) -> float:
   """Resolve carbon_price — either scalar from config or interpolate from trajectory."""

3. def resolve_nox_price(config: ScenarioConfig) -> float:
   """Resolve NOx price from config."""

Tests:
- "mid" path for ERCOT returns expected $/MMBtu
- Price escalates correctly year over year
- Carbon price interpolates between trajectory years
- Non-gas generators get zero fuel price
```

-----

## Phase 2 — LP Dispatch Engine

### Session 2.1: Variable Layout + Cost Vector 🔧

**Depends on:** 1.4, 1.5
**Scope:** Moderate
**Outputs:** `VariableLayout` and `build_cost_vector` in `model/dispatch.py`, tests in `tests/test_dispatch.py`
**Done when:** Layout computes correct column counts. Cost vector places values in correct positions.

```
Create src/market_sim/model/dispatch.py — PART 1 of 4.

Build the variable layout system and cost vector assembly. DO NOT build constraints yet.

1. VariableLayout dataclass that computes column index offsets:
   Given n_gen, n_zones, n_storage, n_links, T=8760, compute:
   - vars_per_hour = n_gen + 2*n_zones + 3*n_storage + n_links + n_zones
   - Total columns = vars_per_hour * T
   - Per-hour offset properties: _p_off, _w_off, _s_off, _chg_off, _dis_off, _soc_off, _flow_off, _slack_off
   - Methods to get column index: p_col(g,t), w_col(z,t), s_col(z,t), chg_col(s,t), dis_col(s,t), soc_col(s,t), flow_col(l,t), slack_col(z,t)
   - Slice-based: p_cols_gen(g) for all T columns of generator g

2. build_cost_vector(layout, mc, voll, storage_epsilon=0.001):
   Returns flat numpy cost vector of length total_columns.
   - Thermal slots: mc[g, t]
   - Wind/solar: 0
   - Storage charge/discharge: epsilon
   - SOC/Flow: 0
   - Slack: voll

3. Tests in tests/test_dispatch.py:
   - VariableLayout with 2 gens, 1 zone, 0 storage, 0 links: verify total cols
   - Cost vector: thermal costs in correct positions, slack = voll, renewables = 0
   - Round-trip: cost_vector[layout.p_col(g, t)] == mc[g, t]

NO constraints, NO solver calls.
```

-----

### Session 2.2: Constraint Matrix — Energy Balance + Bounds 🔧

**Depends on:** 2.1
**Scope:** Heavy
**Outputs:** `build_constraints` and `build_variable_bounds` in `model/dispatch.py`, tests
**Done when:** Constraint matrix builds. Sparsity correct. No Python loops over hours. < 1 second for full fleet.

```
Edit src/market_sim/model/dispatch.py — PART 2 of 4.

Add constraint matrix construction and variable bounds. Supports multi-zone, storage, and transmission from the start (with zero storage/links it reduces to single-zone).

1. _build_zone_gen_map(fleet, n_zones) -> sparse (n_zones × n_gen) zone membership matrix

2. build_constraints(layout, fleet, demand, wind_cf, wind_cap, solar_cf, solar_cap,
   incidence=None, storage params=None, ttc=None):
   Returns (A_sparse, row_lower, row_upper) as CSC matrix and bound vectors.

   Energy balance (n_zones rows per hour, equality):
   Σ_g∈z P[g,t] + W[z,t] + S[z,t] + Σ_s∈z Dis[s,t] - Σ_s∈z Chg[s,t]
   + incidence @ Flow[l,t] + Slack[z,t] = Demand[z,t]

   CRITICAL: Build the per-hour energy balance block as a sparse row, then replicate
   across T hours using scipy.sparse.kron(eye(T), block). NO Python loops over hours.

   Storage SOC dynamics (if storage present):
   SOC[s,t] - SOC[s,t-1] - η_chg*Chg[s,t] + Dis[s,t]/η_dis = 0
   Cyclic boundary: SOC[s,0] - SOC[s,T-1] = 0
   Build vectorized per storage unit using np.arange for column indices.

3. build_variable_bounds(layout, fleet, wind_cf, wind_cap, solar_cf, solar_cap,
   storage_power_cap=None, storage_energy_cap=None, ttc=None):
   Returns (col_lower, col_upper).
   Generator: pmin ≤ P ≤ pmax × availability
   Wind: 0 ≤ W ≤ cf × cap
   Solar: 0 ≤ S ≤ cf × cap
   Storage: 0 ≤ Chg,Dis ≤ power_cap; 0 ≤ SOC ≤ energy_cap
   Flow: -ttc ≤ Flow ≤ ttc

Tests:
- 1 gen, 1 zone, 24 hours: verify A shape
- Verify energy balance row has correct entries
- Demand vector in row bounds
```

-----

### Session 2.3: HiGHS Solver + Dual Extraction 🔧

**Depends on:** 2.2
**Scope:** Moderate
**Outputs:** `solve_dispatch()` and `DispatchResult` in `model/dispatch.py`, full test suite
**Done when:** All 5 canonical tests pass. Duals produce valid prices. Energy balance holds every hour.

```
Edit src/market_sim/model/dispatch.py — PART 3 of 4.

Add the solve function and result extraction.

1. DispatchResult dataclass:
   dispatch (n_gen, T), wind_dispatched (n_zones, T), solar_dispatched (n_zones, T),
   slack (n_zones, T), prices (n_zones, T), storage_charge/discharge/soc (optional),
   flows (optional), objective_value, status, build_time, solve_time

2. solve_dispatch(fleet, demand, wind_cf, wind_cap, solar_cf, solar_cap,
   mc=None, fuel_prices=None, carbon_price=0, nox_price=0, voll=5000,
   incidence=None, ttc=None, storage params=None, T=None) -> DispatchResult:
   - Build layout, cost vector, constraints, variable bounds
   - Time matrix construction
   - Create highspy.Highs(), set silent, add vars, set costs, add rows via CSC
   - h.run()
   - Check model status == optimal, raise if not
   - Extract primal → dispatch arrays using layout offsets
   - Extract dual → prices from energy balance rows (row duals, not negated)
   - Time solve
   - Log both timings

3. Canonical tests in tests/test_dispatch.py (all use T=24):
   a) 1 gen (MC=50, pmax=100), flat demand=80 → price≈50, dispatch=80
   b) 2 gens (MC=30 pmax=50, MC=60 pmax=50), demand=40 → price≈30
   c) 2 gens same, demand=70 → price≈60, cheap at 50 + expensive at 20
   d) demand=200 exceeds all capacity → slack > 0, price ≈ VOLL
   e) energy balance: sum(dispatch) + wind + solar + slack = demand, every hour
```

-----

### Session 2.4: Vectorization Audit + 8760 Performance Test 🧪

**Depends on:** 2.3
**Scope:** Moderate
**Outputs:** Performance test in `tests/test_dispatch.py`, timing instrumentation in dispatch.py
**Done when:** No `for t in range` loops in matrix builder. 8760-hour solve < 15 seconds. Energy balance holds.

```
Review and optimize src/market_sim/model/dispatch.py for performance.

1. Search the ENTIRE file for any `for t in range` or `for hour in` loops in matrix construction code (build_constraints, build_variable_bounds, build_cost_vector).
   If found, replace with vectorized operations using numpy broadcasting or scipy.sparse.
   Note: loops over generators/zones/storage units (small N) are acceptable. Loops over hours (8760) are NOT.

2. Verify timing instrumentation exists in solve_dispatch:
   Log: f"Matrix build: {build_time:.3f}s, Solve: {solve_time:.3f}s"

3. Add performance test in tests/test_dispatch.py:
   - Synthetic fleet: 200 generators, marginal costs ranging 20-80 $/MWh
   - 1 zone, no storage, no transmission (simplest full-scale case)
   - Sinusoidal demand over 8760 hours, peak = 80% of total capacity
   - Flat wind_cf=0.35, solar_cf daily pattern (0 at night, 0.6 midday)
   - Wind cap = 10% of total gen cap, solar cap = 10%
   - Solve for full 8760 hours
   - Assert build time < 3 seconds
   - Assert solve time < 15 seconds
   - Assert energy balance holds for all 8760 hours (np.allclose)
   - Print timing results

4. If performance test fails, profile and fix. Common issues:
   - CSC conversion happening multiple times (should be once at the end)
   - Dense operations where sparse would suffice
```

-----

## Phase 3 — Multi-Zone Transmission

### Session 3.1: Pipe-and-Bubble Transmission Model 🔧

**Depends on:** 2.3
**Scope:** Moderate
**Outputs:** `model/transmission.py`, tests in `tests/test_transmission.py`
**Done when:** Zonal price separation under congestion. Zero-TTC decoupling. Prices equalize without congestion.

```
Create src/market_sim/model/transmission.py

Build the pipe-and-bubble transmission model.

1. Function: build_incidence_matrix(links: list[TransferLink], zone_names: list[str]) -> scipy.sparse matrix
   Returns (n_zones, n_links) matrix. For each link:
   - from_zone row gets -1 (exporting)
   - to_zone row gets +1 (importing)
   Flow > 0 means power flows from_zone → to_zone.

2. Function: get_ttc_array(links) -> np.ndarray
   Returns (n_links,) array of TTC values in MW.

3. The incidence matrix and ttc array are passed to solve_dispatch() which already
   supports them via the incidence and ttc parameters. No changes to dispatch.py needed
   (it was built to accept these from the start).

4. Tests in tests/test_transmission.py (all T=24):
   a) 2 zones, 1 link (1000 MW), cheap gen (MC=30) only in zone A, expensive gen (MC=80) only in zone B, demand in both:
      Power flows from A to B. If link uncongested, prices equalize.
   b) Same setup but TTC=0: zones fully decouple. Zone B price = MC of zone B gen.
   c) 2 zones, surplus wind in zone A: flow = min(surplus, TTC). Zone A price ≤ zone B price.
   d) ERCOT-like: 4 zones, 6 links, generators spread across zones. Verify energy balance per zone.
```

-----

### Session 3.2: CAISO WECC Import Tranches

**Depends on:** 3.1
**Scope:** Light
**Outputs:** `build_wecc_import_generators()` in `model/transmission.py`, tests
**Done when:** CAISO imports at stepped prices. Low demand → only cheap tranche. High demand → all tranches.

```
Add CAISO WECC import model to src/market_sim/model/transmission.py

The WECC import node is modeled as pseudo-generators with stepped marginal costs.

1. Function: build_wecc_import_generators() -> list[Generator]
   Creates synthetic Generator objects as import tranches:
   - Tranche 1: "PNW_hydro" — 3000 MW at MC=$15/MWh (zone="WECC_import")
   - Tranche 2: "DSW_CCGT" — 5000 MW at MC=$35/MWh
   - Tranche 3: "DSW_CT" — 4000 MW at MC=$55/MWh
   - Tranche 4: "Expensive_import" — 3000 MW at MC=$80/MWh
   All with heat_rate=0 (cost is set directly via vom field), eford=0.02.
   Mark with TODO: fit from EIA-930 interchange data.

2. Function: build_wecc_export_sink() -> Generator
   Export "sink" in WECC zone. pmax_mw=5000, vom=0 (or small negative).
   Lets CAISO dump surplus solar.

3. These just get appended to the generator fleet before LP construction.
   No special formulation — they participate via energy balance + transmission link.

4. Tests:
   - CAISO low demand: only cheap tranche dispatches, price ≈ $15
   - CAISO high demand: all tranches dispatch in merit order
   - CAISO surplus solar: export gen dispatches (power flows CAISO → WECC)
```

-----

## Phase 4 — Storage Co-Optimization

### Session 4.1: Storage Constraint Builder + SOC Dynamics 🔧

**Depends on:** 2.3
**Scope:** Heavy
**Outputs:** `model/storage.py`, tests in `tests/test_storage.py`
**Done when:** Storage arbitrages peak/off-peak. SOC cyclic. RTE losses correct. No hour loops.

```
Create src/market_sim/model/storage.py

Storage parameter structs. The SOC constraints are already built inside dispatch.py's
build_constraints function (it accepts storage params). This module provides the data layer.

1. StorageUnit dataclass (Pydantic):
   unit_id, zone, power_cap_mw, energy_cap_mwh, eta_charge, eta_discharge, zone_idx

2. StorageArrays dataclass (plain, struct-of-arrays):
   power_cap, energy_cap, eta_chg, eta_dis: np.ndarray (n_storage,)
   zone_idx: np.ndarray int (n_storage,)
   n_storage property

3. Function: storage_units_to_arrays(units, zone_names) -> StorageArrays

4. Function: build_default_storage(iso, config) -> list[StorageUnit]
   Creates storage fleet from constants.STORAGE_TECHS + config.storage_deployment pace.

Tests in tests/test_storage.py (all T=24 unless noted):
a) 1 storage unit (100MW/400MWh, RTE=0.85), 2 thermal gens (cheap MC=20, expensive MC=80),
   demand is low hours 0-11 (use cheap gen), high hours 12-23 (need expensive gen):
   → Storage charges during cheap hours, discharges during expensive hours
b) SOC cyclic: SOC[0] ≈ SOC[23]
c) Energy conservation: total_discharge ≈ total_charge * RTE (within 1%)
d) RTE loss: total discharge energy < total charge energy
```

-----

### Session 4.2: Multi-Zone + Storage Integration Test 🧪

**Depends on:** 3.1, 4.1
**Scope:** Moderate
**Outputs:** Integration tests in `tests/test_integration.py`
**Done when:** 4-zone + storage solve works. Energy balance per zone. Flows within TTC. 8760-hour perf < 30s.

```
Build tests/test_integration.py

Integration tests combining dispatch + transmission + storage.

1. ERCOT-like test (T=168 hours = one week):
   - 4 zones, 6 links with TTCs from iso_configs
   - 10 thermal generators spread across zones (mix of gas CC, CT, coal)
   - Wind in West zone (high CF), solar in South zone
   - 2 storage units: one in Houston (200MW/800MWh), one in North (100MW/400MWh)
   - Demand varies: low overnight, high afternoon

   Verify:
   - Storage charges when prices low (high renewables midday)
   - Storage discharges when prices high (evening peak)
   - Inter-zonal flows within TTC limits: abs(flow) <= ttc for every link, every hour
   - Energy balance per zone per hour: sum(gen) + wind + solar + discharge - charge + net_flow + slack = demand
   - Prices differ across zones when transmission congested

2. 8760-hour performance test:
   - 200 gens + 5 storage units + 4 zones + 6 links
   - Full year sinusoidal demand + realistic wind/solar profiles
   - Assert total time (build + solve) < 30 seconds
   - Assert energy balance holds for all 4 zones × 8760 hours
   - Print timing breakdown
```

-----

## Phase 5 — Capacity Evolution Engine

### Session 5.1: Retirement Logic 🔧

**Depends on:** 2.3
**Scope:** Moderate
**Outputs:** `model/capacity.py` (retirement portion), `tests/test_capacity.py`
**Done when:** Known retirements match schedule. Sigmoid triggers. Economic retirement works.

```
Build src/market_sim/model/capacity.py — PART 1: retirements

1. apply_known_retirements(fleet: list[Generator], year: int) -> list[Generator]
   Remove generators where retirement_year is not None and retirement_year <= year.

2. apply_economic_retirements(fleet, fleet_arrays, dispatch_result, prices, config,
   consecutive_loss_years: dict[str, int]) -> tuple[list[Generator], dict]:
   For each thermal generator:
   - net_revenue = Σ_t price[zone, t] * dispatch[g, t]
   - going_forward_cost = fixed_om_per_kw_yr * pmax * 1000 (convert kW→MW)
   - If net_revenue < going_forward_cost: increment loss counter
   - If counter >= config.retirement_consecutive_years: retire
   - Within fuel class, retire highest heat_rate first
   Return updated fleet and loss tracker.

3. apply_sigmoid_retirement(fleet, clean_share: float, config) -> list[Generator]
   retirement_fraction = 1 / (1 + exp(-config.sigmoid_steepness * (clean_share - config.sigmoid_midpoint)))
   Apply to coal first, then gas_ct, then gas_cc.
   Remove fraction of each class's capacity (retire least efficient units).

4. Helper: compute_clean_share(fleet) -> float
   (wind + solar + nuclear + hydro capacity) / total capacity

Tests in tests/test_capacity.py:
- Known: gen with retirement_year=2028 removed in 2028, present in 2027
- Economic: unprofitable gen with 2 consecutive loss years → retired
- Economic: profitable gen resets counter
- Sigmoid: clean_share=0.6 with midpoint=0.5 → some coal retires
- Sigmoid: clean_share=0.3 with midpoint=0.5 → minimal retirement
```

-----

### Session 5.2: New Entry + Learning Curves + IRA Credits

**Depends on:** 5.1
**Scope:** Heavy
**Outputs:** `model/capacity.py` (entry portion), `policy/ira.py`, `policy/rps.py`, tests
**Done when:** LCOE decreases with learning. IRA reduces LCOE. Queue cap binds. RPS forces builds.

```
Edit src/market_sim/model/capacity.py — PART 2: new entry

1. In policy/ira.py:
   def apply_ira_credits(tech_type, lcoe, year, config) -> float:
   PTC for wind: subtract config.ira_ptc_wind from LCOE ($/MWh)
   ITC for solar/storage: multiply capex component by (1 - config.ira_itc_solar)
   Credits phase out after config.ira_expiry_year.

2. In policy/rps.py:
   def get_rps_target(iso, year) -> float | None:
   Interpolate from STATE_RPS_FLOORS in constants. Return None if no RPS.

3. In capacity.py:
   def wright_cost(base_cost, cumulative_gw, reference_gw, learning_rate) -> float:
   cost = base_cost * (cumulative_gw / reference_gw) ** (-log2(1-learning_rate)/log2(2))
   Simpler: cost = base_cost * (cumulative_gw / reference_gw) ** (-learning_rate)

   def compute_lcoe(tech_type, year, config, cumulative_gw=None) -> float:
   LCOE with Wright's Law + IRA credits.
   Use NEW_ENTRY_COST from constants for base costs.

   def estimate_expected_revenue(prices, cf, hours=8760) -> float:
   Expected annual revenue per MW from price duration curve × capacity factor.

   def apply_economic_new_entry(fleet, prices, year, config, iso) -> list[Generator]:
   For each candidate tech: if expected_revenue > LCOE, add up to queue cap.
   Queue cap from QUEUE_CAP_GW. Priority: highest margin first.

   def apply_rps_mandate(fleet, year, config) -> list[Generator]:
   If clean_share < rps_target, force-build cheapest clean tech to fill gap.

4. Main evolution function:
   def evolve_fleet(fleet, prior_results, year, config, loss_tracker) -> tuple[list, dict]:
   Order: known retirements → economic retirements → sigmoid → known additions
   (online_year == year) → economic new entry → RPS mandates.

Tests:
- LCOE decreases over time with learning
- IRA credit reduces LCOE; expires after ira_expiry_year
- Queue cap limits annual additions
- evolve_fleet applies steps in order
- RPS mandate forces builds when clean share below target (CAISO)
```

-----

### Session 5.3: Capacity Evolution Year-Loop Integration

**Depends on:** 5.1, 5.2
**Scope:** Moderate
**Outputs:** Complete `model/capacity.py`, `policy/carbon.py`, integration tests
**Done when:** 5-year trajectory runs. Fleet changes are deterministic. Two scenarios diverge correctly.

```
Wire together the complete year-over-year evolution loop.

1. Build policy/carbon.py:
   def resolve_carbon_price(config, year) -> float:
   If config.carbon_price is scalar, return it.
   If it's a path string, interpolate from CARBON_PRICE_PATHS in constants.

2. Verify evolve_fleet handles edge cases:
   - Year 2026 (no prior results): skip economic retirement, only apply known pipeline
   - Empty fleet after retirements: should still work (new entry fills gap)
   - All clean fleet: sigmoid has no thermal to retire

3. Policy extension point (stub for now):
   In dispatch.py or a policy module, add a check:
   def get_active_policy_constraints(config, year) -> list:
   Returns empty list for now. When constraint-type policies are added later,
   they'll return sparse matrix rows to append to the LP.

4. Integration tests:
   - 3-year trajectory (2026-2028) with small fleet, verify fleet composition each year
   - Two scenarios identical except gas_price_path: fleets identical year 1, diverge by year 3
   - Coal plant with retirement_year=2027: present in 2026, gone in 2027
   - Fleet capacity never goes to zero (new entry should fill gaps)
```

-----

## Phase 6 — Scenario Runner + Caching

### Session 6.1: Parquet Cache + Result Serialization

**Depends on:** 5.3
**Scope:** Moderate
**Outputs:** `results/cache.py`, `results/outputs.py`, tests
**Done when:** Save/load round-trips. is_cached works. Config YAML saved alongside.

```
Build src/market_sim/results/cache.py and src/market_sim/results/outputs.py

1. In outputs.py: extend DispatchResult with to_parquet(path) and from_parquet(path).
   Schema: flatten arrays to one row per hour. Columns: hour, zone, dispatch_by_gen (or aggregate),
   price, wind, solar, slack, emissions, storage_soc, flows, etc.
   Use pyarrow for Parquet writing.

2. In cache.py:
   def get_cache_path(iso, cache_key, year) -> Path:
       return Path(f"results/{iso}/{cache_key}/year_{year}.parquet")

   def is_cached(iso, cache_key, year) -> bool
   def save_result(result, config, iso, year): save parquet + config.yaml
   def load_result(iso, cache_key, year) -> DispatchResult

3. Tests:
   - Save result, load back, all arrays match (np.allclose)
   - is_cached True after save, False before
   - Config YAML present alongside parquet
   - Loading nonexistent path raises appropriate error
```

-----

### Session 6.2: Runner Orchestrator + CLI

**Depends on:** 6.1
**Scope:** Moderate
**Outputs:** `runner.py`, tests
**Done when:** Single-run CLI works. Caching skips completed years. Sweep generates parallel runs.

```
Build src/market_sim/runner.py

1. def run_scenario_iso(config, iso) -> str:
   Run all years 2026-2050 for one scenario × one ISO. Sequential.
   For each year: check cache → evolve fleet → assemble inputs → solve → save → log.
   Returns cache_key.

2. def main():
   argparse CLI with two subcommands:
   - run: python -m market_sim run --config scenario.yaml [--iso ERCOT]
   - sweep: python -m market_sim sweep --sweep sweep.yaml [--workers N]

   Sweep mode: generate configs, use ProcessPoolExecutor across (config, iso) pairs.
   Workers default to cpu_count - 1.

3. Logging: Python logging module. Log full resolved config at start.
   Log per-year: "Solved: ERCOT 2026 in 3.2s" or "Cached: ERCOT 2026"

Tests (mock the solve step for speed):
- Run 3 years → 3 cache files created
- Re-run → all 3 skipped (check log messages)
- Sweep with 2 configs → 2 cache directories
```

-----

## Phase 7 — Outputs + Emissions + Calibration

### Session 7.1: Emissions Accounting + JSON Export

**Depends on:** 6.1
**Scope:** Moderate
**Outputs:** `results/emissions.py`, `results/export.py`, `scripts/export_results.py`, `docs/data-dictionary.md`
**Done when:** Emissions vectorized. Export produces valid JSON < 2 MB. Data dictionary covers all fields.

```
Build src/market_sim/results/emissions.py, results/export.py, and scripts/export_results.py

1. emissions.py:
   def compute_emissions(dispatch, emission_rates) -> np.ndarray:
       """(n_gen, T) × (n_gen,) → (T,) total CO2 per hour. Vectorized."""
       return (dispatch * emission_rates[:, None]).sum(axis=0)
   Same pattern for NOx.

2. export.py:
   def export_scenario_json(cache_key, iso, output_dir):
   Load all 25 years of Parquet, aggregate to annual summaries:
   { cache_key, iso, config, years: { "2026": { generation_twh by fuel, emissions_mt,
     avg_price, peak_price, curtailment_twh, capacity_gw by fuel, storage_cycles }, ... } }
   Keep < 2 MB per file.

3. scripts/export_results.py:
   CLI: find all completed scenarios in results/, export each to frontend/data/results/.
   Build frontend/data/scenarios.json with metadata.

4. Create docs/data-dictionary.md: every Parquet column with name, type, unit, range.

Tests:
- Emissions = sum(dispatch × rates), matches manual calc
- Export produces valid JSON, file size < 2 MB
- Curtailment = potential - dispatched, always >= 0
```

-----

### Session 7.2: Calibration Framework 📂 NEEDS DATA

**Depends on:** 7.1
**Scope:** Heavy
**Outputs:** Calibration code, `docs/calibration-log.md`, validation tests
**Done when:** Calibration diagnostic runs. ±5% gen mix check works.

```
Build calibration framework.

1. def check_generation_mix(result, benchmark, tolerance=0.05) -> dict:
   Compare generation by fuel type (TWh) against benchmark.
   Return {fuel: {model, benchmark, pct_diff, pass_fail}} for each fuel.

2. def check_price_duration_curve(prices, benchmark_prices) -> dict:
   Compare sorted price arrays. Return shape metrics (P10, P50, P90, mean).

3. def run_calibration_check(scenario_cache_key, iso, benchmarks) -> CalibrationReport:
   Diagnostic order: (1) gen mix, (2) price duration curve, (3) avg price, (4) capacity factors.

4. CalibrationReport dataclass with pass/fail per diagnostic + details.

5. Create docs/calibration-log.md template.

Tests:
- Gen mix check correctly flags >5% deviation
- Gen mix check passes within tolerance
- Price duration curve comparison produces sensible metrics
```

-----

## Phase 8 — Interactive Frontend

### Session 8.1: Frontend Skeleton + Design System

**Depends on:** 7.1
**Scope:** Moderate
**Outputs:** `frontend/css/style.css`, `frontend/js/app.js`, `frontend/js/data-loader.js`, `frontend/index.html` shell
**Done when:** Shell loads in browser. Navigation works. Data loader fetches sample JSON.

```
Build frontend skeleton: index.html, css/style.css, js/app.js, js/data-loader.js

1. style.css — design system:
   - CSS custom properties for fuel colors: --gas-cc: #4A90D9, --gas-ct: #7BB3E0,
     --coal: #8B4513, --nuclear: #9B59B6, --wind: #2ECC71, --solar: #F1C40F,
     --storage: #E67E22, --hydro: #1ABC9C
   - Typography, layout grid, responsive breakpoints (desktop-first)
   - Navigation bar styles, card styles, chart container styles

2. app.js — minimal routing/state:
   - Track current page, selected scenario, selected year
   - Navigation between index, decisions, parameters pages

3. data-loader.js:
   - fetch('data/scenarios.json') on load
   - Lazy-load per-scenario JSON on selection
   - Cache in memory (not localStorage)

4. index.html — shell with nav bar linking to all 3 pages
   - CDN imports: Plotly.js, D3.js
   - Placeholder chart containers

5. Root index.html at repo root linking to frontend/ and learning-hub/
```

-----

### Session 8.2: Results Dashboard

**Depends on:** 8.1
**Scope:** Heavy
**Outputs:** `frontend/js/charts.js`, complete `frontend/index.html`
**Done when:** All 4 chart types render. Scenario switching works. No console errors.

```
Build frontend/js/charts.js and complete frontend/index.html

1. Scenario selector: dropdown populated from scenarios.json

2. Chart panels:
   a) Generation mix stacked area chart (2026-2050) — Plotly.js
   b) Emissions trajectory line chart
   c) Price duration curve (sorted descending) for selected year
   d) Capacity mix bar chart for selected year

3. Year slider to select which year's duration curve / capacity bar to show

4. charts.js functions:
   renderGenerationMix(data), renderEmissions(data),
   renderPriceDuration(data, year), renderCapacity(data, year)

5. Use fuel color tokens from CSS custom properties.
   Responsive layout. Plotly.js from CDN.
```

-----

### Session 8.3: Decision Tracker + Parameter Browser

**Depends on:** 8.1
**Scope:** Moderate
**Outputs:** `frontend/decisions.html`, `frontend/js/decisions.js`, `frontend/parameters.html`, `frontend/data/parameters.json`
**Done when:** Decision forms persist via localStorage. Parameter table searchable and filterable.

```
Build frontend/decisions.html, js/decisions.js, parameters.html, and data/parameters.json

1. decisions.html — decision tracker with form persistence:
   Define 10+ decisions as JS data (weather_year, caiso_voll, ercot_ttc_source,
   caiso_import_curve, p10p50p90_method, etc. from build-plan §5).
   Collapsible sections by domain. Radio buttons + notes textarea.
   Save to localStorage: marketsim_decision_{id}
   Restore on load. Export button dumps JSON to clipboard.

2. parameters.html — citation browser:
   Load from parameters.json. Searchable, filterable by domain and tier.
   Table: Name, Value, Unit, Tier, Source, Domain.
   Click row to expand full citation details.

3. parameters.json — initial 20-30 parameters from constants.py.
   Schema: param_id, display_name, value, unit, domain, tier, source, source_date,
   page_or_table, url, notes, old_repo_location, last_verified
```

-----

## Phase 9 — Learning Hub

### Session 9.1: Shared Scrollytell Framework

**Depends on:** Nothing (can run in parallel)
**Scope:** Moderate
**Outputs:** `learning-hub/shared/scrollytell.js`, `scrollytell.css`, `learning-hub/index.html`
**Done when:** Test page scrolls correctly. Transitions trigger. Works on mobile.

```
Build learning-hub/shared/scrollytell.css, scrollytell.js, and learning-hub/index.html

1. scrollytell.js — lightweight engine:
   - IntersectionObserver detects which narrative step is in view
   - Fires 'step-enter'/'step-exit' events with step index
   - Sticky chart panel stays fixed while narrative scrolls
   - Auto-advances through animation states

2. scrollytell.css:
   - Two-column: sticky chart (60%) + scrolling narrative (40%)
   - Mobile: stacks vertically
   - Step highlighting with accent color

3. learning-hub/index.html — landing page:
   Cards linking to: LP Dispatch, Capacity Evolution, Storage, Transmission, Scenarios
   D3.js from CDN. No other dependencies.
```

-----

### Session 9.2: LP Dispatch Scrollytell

**Depends on:** 9.1
**Scope:** Heavy
**Outputs:** `learning-hub/lp-dispatch/index.html`
**Done when:** Full story from merit order to LP pricing. Animations trigger on scroll.

```
Build learning-hub/lp-dispatch/index.html — "How the Model Decides Who Generates"

5-generator, 24-hour example with D3 animated visuals. Steps:
1. "Meet the generators" — 5 blocks with marginal costs
2. "Stack them by cost" — animate into merit order
3. "Draw the demand line" — 24-hour demand curve
4. "The LP fills from cheapest" — animate dispatch stacking
5. "The price = the last unit needed" — highlight marginal gen, show dual = price
6. "Add wind at zero cost" — wind displaces expensive gens
7. "Surplus wind → curtailment" — excess wind, price drops
8. "Why LP beats heuristics" — side-by-side comparison

D3.js for animated bar charts. Synthetic data.
```

-----

### Session 9.3: Capacity Evolution Scrollytell

**Depends on:** 9.1
**Scope:** Moderate
**Outputs:** `learning-hub/capacity-evolution/index.html`
**Done when:** Waterfall animates. Sigmoid and learning curve explanations clear.

```
Build learning-hub/capacity-evolution/index.html

1. Animated fleet waterfall chart 2026-2050 (retirements leaving, additions entering)
2. Sigmoid retirement trigger visualization (interactive slider for clean_share)
3. Wright's Law cost curve animation (cumulative capacity → declining cost)
```

-----

### Session 9.4: Remaining Scrollytell Pages

**Depends on:** 9.1
**Scope:** Heavy (3 pages, can split into separate sessions)

```
Build three remaining scrollytell pages:

1. learning-hub/storage-cooptimization/index.html:
   Animated SOC profile over a week. Greedy vs LP global optimum side-by-side.
   RTE loss visualization.

2. learning-hub/transmission-pricing/index.html:
   Map-based ERCOT 4-zone with animated flows. Congestion → price divergence.
   Copper-plate vs zonal comparison.

3. learning-hub/scenario-uncertainty/index.html:
   Interactive fan chart builder. Toggle scenario dimensions on/off.
   P10/P50/P90 bands respond.
```

-----

## Sub-Agent Sessions

*These run on their own cadence, triggered by phase completions.*

### Session SA-1: Documentation Pass (after each phase merge)

```
Update all docs to reflect current system state:
1. docs/architecture.md — module structure and data flow
2. docs/data-dictionary.md — all Parquet columns, types, units, ranges
3. docs/lp-formulation.md — current constraint set
4. docs/decision-log.md — append new decisions with dates
5. CHANGELOG.md — dated entries for this phase
6. Audit: flag any public function missing a docstring
```

-----

### Session SA-2: Expert Review (after Phase 2, 5, 7)

```
Review model against industry standard practice. Read context/ folder (Aurora, PLEXOS,
ReEDS, IPM, GenX, US-REGEN, Cambium, eGRID summaries).

Produce docs/reviewer-notes.md:
- LP formulation vs production cost modeling standards
- Capacity evolution vs capacity expansion approaches
- Storage formulation vs NREL ATB defaults
- Scenario parameter space completeness
- Calibration target achievability

Format: finding → implication → recommendation. Tags: [CRITICAL], [IMPORTANT], [MINOR].
```

-----

### Session SA-3: Parameter Citation Audit (after Phase 1, then incremental)

```
Build and maintain the full parameter citation registry.

1. docs/parameter-citations.md — every constant traced to primary source
2. frontend/data/parameters.json — machine-readable with full schema:
   param_id, display_name, value, unit, domain, tier, source, source_date,
   page_or_table, url, notes, old_repo_location, last_verified

3. scripts/validate_parameters.py — cross-check every constant in constants.py
   and every ScenarioConfig default has a matching parameters.json entry.

4. Flag parameters sourced from other models (not empirical).
5. Flag parameters older than 3 years.
```

-----

## Dependency Map

```
0.1 ──┬── 1.1 (ScenarioConfig)
      ├── 1.2 (Constants)
      ├── 1.3 (ISO Configs)
      │
      ├── 1.4 (Fleet/FleetArrays) ── 1.5 (MC Assembly)
      │         │
      │    1.6 (EIA Loader) 📂 ── 1.7 (Fleet Builder) 📂
      │
      └── 1.8 (Fuel Loader) 📂
               │
      1.4+1.5 ─┴── 2.1 (Layout) ── 2.2 (Constraints) ── 2.3 (Solve) ── 2.4 (Perf) 🧪
                                                              │
                                                    3.1 (Transmission) ── 3.2 (CAISO Imports)
                                                              │
                                                    4.1 (Storage) ── 4.2 (Integration) 🧪
                                                              │
                                                    5.1 (Retirements) ── 5.2 (New Entry) ── 5.3 (Year Loop)
                                                                                                │
                                                                                    6.1 (Cache) ── 6.2 (Runner)
                                                                                         │
                                                                                7.1 (Emissions+Export) ── 7.2 (Calibration) 📂
                                                                                         │
                                                                                8.1 (Frontend Skeleton)
                                                                                    ├── 8.2 (Dashboard)
                                                                                    └── 8.3 (Decisions+Params)

9.1 (Scrollytell Framework) ──┬── 9.2 (LP Dispatch)
                              ├── 9.3 (Capacity)
                              └── 9.4 (Storage + Transmission + Scenarios)

SA-1: after each phase
SA-2: after 2.3, 5.3, 7.2
SA-3: after 1.2, then incremental
```

-----

## Total: 31 sessions + 3 sub-agent sessions

|Phase         |Sessions|Scope                            |
|--------------|--------|---------------------------------|
|0 Scaffold    |0.1     |1 light                          |
|1 Config+Data |1.1–1.8 |3 moderate, 2 heavy, 1 light, 2 📂|
|2 LP Engine   |2.1–2.4 |1 heavy, 2 moderate, 1 QA        |
|3 Transmission|3.1–3.2 |1 moderate, 1 light              |
|4 Storage     |4.1–4.2 |1 heavy, 1 QA                    |
|5 Capacity    |5.1–5.3 |1 heavy, 2 moderate              |
|6 Runner      |6.1–6.2 |2 moderate                       |
|7 Outputs     |7.1–7.2 |1 moderate, 1 📂 heavy            |
|8 Frontend    |8.1–8.3 |1 heavy, 2 moderate              |
|9 Learning Hub|9.1–9.4 |1 heavy, 2 moderate, 1 heavy     |
|Sub-agents    |SA-1–3  |recurring                        |

**Critical path (skip 📂 sessions first pass):** 0.1 → 1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 2.1 → 2.2 → 2.3 → 2.4 → 3.1 → 4.1 → 5.1 → 5.2 → 5.3 → 6.1 → 6.2 → 7.1 = **18 sessions to a working model.**