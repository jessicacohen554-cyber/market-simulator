# Market Sim — Claude Code Prompt Pack

**How to use:** Run each session in order. Copy-paste the prompt into Claude Code. Wait for completion, review, commit, then move to the next. Each session should finish in 5–15 minutes.

**Pre-flight:** Make sure `CLAUDE.md` is at repo root and the methodology + build-plan markdown docs are in the repo (so Claude Code can read them if needed). Don’t paste those docs into prompts — they’re too long.

-----

## PHASE 0 — Repo Scaffold

### Session 0.1: Initialize project structure

```
Create the project skeleton for market-sim. Do NOT write any logic yet — just structure and stubs.

1. pyproject.toml with:
   name = "market-sim"
   requires-python = ">=3.11"
   dependencies: highspy>=1.7, numpy>=1.26, pandas>=2.1, pyarrow>=14.0, pydantic>=2.5, pyyaml>=6.0
   optional dev deps: pytest>=8.0, ruff>=0.5
   console script: market-sim = "market_sim.runner:main"

2. Directory tree with empty __init__.py files:
   src/market_sim/ with subpackages: config/, data/, model/, policy/, results/
   tests/
   data/ (with subdirs: eia_hourly/, fleet/, reference/)
   docs/
   scripts/
   frontend/ (with subdirs: css/, js/, data/, data/results/)
   learning-hub/

3. CONVENTIONS.md with these rules:
   - Python snake_case.py, frontend kebab-case
   - Public functions: verb_noun naming
   - Single-letter vars only t/g/z/s in LP construction with comment
   - Constants in config/constants.py with citation comments
   - Feature branches: phase-N/description
   - Commits: imperative present tense
   - Every public function needs a docstring
   - Raw data in data/ never modified in place

4. Empty CHANGELOG.md with a header

5. A minimal README.md: project name, one-line description, "See CLAUDE.md for build instructions"

Don't write any Python logic. Just the skeleton.
```

-----

## PHASE 1 — Config & Data Layer

### Session 1.1: ScenarioConfig dataclass

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

   Tier 3 (calibration):
   - renewable_cf_adjustment: float = 1.0
   - basis_differential_factor: float = 1.0

2. Methods:
   - cache_key() -> str: SHA256 hash of the full config dict, truncated to 16 chars
   - to_yaml(path) and from_yaml(path) class method: round-trip YAML serialization
     Only non-default values need to appear in YAML. Loading merges overrides onto defaults.
   - resolve(): returns a copy with any string lookups expanded (e.g. gas_price_path "high" -> actual array)

3. SweepDefinition dataclass:
   - sweep: dict[str, list] — parameter name to list of values
   - mode: str = "factorial"  # only factorial for now
   - generate() -> list[ScenarioConfig]: produces the cartesian product

4. Tests in tests/test_config.py:
   - Default config cache_key is deterministic (call twice, same result)
   - Changing one parameter changes the cache_key
   - YAML round-trip: write config, read back, assertEqual
   - YAML with partial overrides: unspecified fields keep defaults
   - Sweep with 2 params × 3 values each → 6 configs, all unique cache keys
```

### Session 1.2: Constants file

```
Build src/market_sim/config/constants.py

This is a pure data file — no logic, no imports except typing. Every value has an inline citation comment.

Include these constants (use placeholder values with TODO comments where you don't have the exact number — I'll fill them in later):

# Efficiency bins (heat rate in MMBtu/MWh) by fuel class
HEAT_RATE_BINS = {
    "gas_cc": {"h_class": 6.3, "f_class": 6.7, "older": 7.5},  # Source: EIA Table 8.1, 2024
    "gas_ct": {"aero": 9.0, "frame": 10.5, "older": 11.5},
    "coal": {"supercritical": 8.8, "subcritical": 10.0, "older": 10.8},
}

# CO2 emission rates by fuel (tCO2/MWh) — derived from EPA eGRID 2022
CO2_RATES = {
    "gas_cc": {"h_class": 0.35, "f_class": 0.37, "older": 0.42},
    "gas_ct": {"aero": 0.50, "frame": 0.58, "older": 0.64},
    "coal": {"supercritical": 0.85, "subcritical": 0.95, "older": 1.02},
}

# Gas availability factors (1 - summer derate)
GAS_AVAILABILITY = {"ERCOT": 0.83, "CAISO": 0.88}  # Source: NERC GADS

# Nuclear monthly capacity factors (fraction)
NUCLEAR_MONTHLY_CF = {
    "ERCOT": [0.95, 0.95, 0.90, 0.85, 0.80, 0.92, 0.95, 0.95, 0.93, 0.90, 0.95, 0.95],
    "CAISO": [0.90, 0.90, 0.88, 0.82, 0.78, 0.85, 0.90, 0.92, 0.90, 0.88, 0.90, 0.90],
}  # Source: NRC PRIS 2019-2023 averages

# Demand growth rates (annual fraction)
DEMAND_GROWTH_RATES = {
    "low": {"ERCOT": 0.005, "CAISO": 0.002},
    "mid": {"ERCOT": 0.015, "CAISO": 0.008},
    "high": {"ERCOT": 0.030, "CAISO": 0.015},
}

# Storage technology parameters
STORAGE_TECHS = {
    "li_ion_4hr": {"duration_hr": 4, "rte": 0.85, "cycles": 5000, "cost_kwh": 250},
    "li_ion_8hr": {"duration_hr": 8, "rte": 0.80, "cycles": 4000, "cost_kwh": 200},
    "iron_air":   {"duration_hr": 100, "rte": 0.45, "cycles": 10000, "cost_kwh": 25},
}  # Source: NREL ATB 2024, DOE LDES Liftoff

# Carbon price trajectories ($/ton CO2, selected years)
CARBON_PRICE_PATHS = {
    "zero": 0.0,
    "low":  {"2026": 10, "2030": 15, "2040": 25, "2050": 35},
    "mid":  {"2026": 25, "2030": 40, "2040": 65, "2050": 85},
    "high": {"2026": 45, "2030": 75, "2040": 120, "2050": 150},
}

# State RPS floors (minimum clean energy fraction)
STATE_RPS_FLOORS = {
    "CAISO": {"2026": 0.52, "2030": 0.60, "2035": 0.75, "2040": 0.90, "2045": 1.0},
}  # Source: CA SB 100

# ERCOT queue throughput cap (GW/year)
QUEUE_CAP_GW = {"ERCOT": 12.0, "CAISO": 8.0}

Add a module docstring explaining this is the single source of truth for physical and economic constants, and that every value must have a citation comment.
```

### Session 1.3: ISO topology configs

```
Build src/market_sim/config/iso_configs.py

Define the physical topology for each ISO using Pydantic models:

1. Zone model: name (str), iso (str), load_share (float — fraction of total ISO load)

2. TransferLink model: from_zone (str), to_zone (str), ttc_mw (float), is_bidirectional (bool = True)

3. ERCOT config:
   Zones: North (0.38), South (0.20), West (0.08), Houston (0.34)
   Links (6 bidirectional): North↔South 5000 MW, North↔West 3000 MW, North↔Houston 8000 MW,
   South↔Houston 4000 MW, South↔West 2000 MW, West↔Houston 2500 MW
   (These are placeholder TTCs — mark with TODO: verify from ERCOT CDR)

4. CAISO config:
   Zones: CAISO_main (1.0), WECC_import (0.0 — not a load zone)
   Links: CAISO_main↔WECC_import 15000 MW import / 5000 MW export
   
5. ISOConfig model that bundles zones + links + metadata (iso name, n_zones, voll, etc.)

6. get_iso_config(iso_name: str) -> ISOConfig factory function

Write tests in tests/test_iso_config.py:
- ERCOT has 4 zones, load shares sum to 1.0
- CAISO has 2 zones (1 real + 1 import node)
- All links reference valid zone names
```

### Session 1.4: Pydantic data models + FleetArrays

```
Build src/market_sim/data/fleet.py

1. Generator Pydantic model:
   unit_id: str
   name: str
   zone: str
   fuel_type: str  # gas_cc, gas_ct, coal, nuclear, wind, solar, hydro
   efficiency_bin: str  # h_class, f_class, older, etc.
   pmax_mw: float
   pmin_mw: float = 0.0  # >0 for must-run units
   heat_rate: float  # MMBtu/MWh
   vom: float = 0.0  # $/MWh variable O&M
   emission_rate_co2: float = 0.0  # tCO2/MWh
   nox_rate: float = 0.0  # tons NOx/MWh
   eford: float = 0.05  # forced outage rate
   online_year: int = 2000
   retirement_year: int | None = None

2. FleetArrays dataclass (plain dataclass, not Pydantic):
   All numpy arrays indexed by generator index g:
   pmax, pmin, heat_rate, vom, emission_rate, nox_rate: np.ndarray (n_gen,)
   zone_idx: np.ndarray int (n_gen,) — maps to zone integer index
   fuel_type_idx: np.ndarray int (n_gen,) — integer enum
   availability: np.ndarray (n_gen, 8760)
   unit_id: list[str] (n_gen,) — for mapping results back

3. Conversion function:
   def generators_to_fleet_arrays(generators: list[Generator], zone_names: list[str], hours: int = 8760) -> FleetArrays
   Builds the struct-of-arrays. Availability = (1 - eford) broadcast to all hours (seasonal factors added later).

4. Tests in tests/test_fleet.py:
   - Create 3 generators, convert to FleetArrays, verify shapes
   - zone_idx correctly maps zone names to integer indices
   - availability = (1 - eford) for each generator
```

### Session 1.5: Marginal cost assembly

```
Build the assemble_mc function in src/market_sim/data/fleet.py (add to existing file).

def assemble_mc(
    fleet: FleetArrays,
    fuel_prices: np.ndarray,   # (n_gen, 8760) or broadcastable
    carbon_price: np.ndarray,  # (8760,) or scalar
    nox_price: np.ndarray,     # (8760,) or scalar
    **adders: tuple[np.ndarray, np.ndarray]  # (rate_array, price_array) pairs
) -> np.ndarray:
    """
    Returns (n_gen, 8760) marginal cost array.
    Fully vectorized — no loops.
    mc = heat_rate × fuel_price + vom + emission_rate × carbon_price + nox_rate × nox_price + ...
    """

Implementation: use numpy broadcasting. heat_rate[:, None] * fuel_prices, etc.
The **adders kwarg allows extensibility — each is a (generator_rate, hourly_price) pair.

Tests in tests/test_fleet.py (append):
- 1 generator, constant fuel price → mc = heat_rate * fuel_price + vom
- 2 generators with different heat rates → different mc values
- Adding carbon_price increases mc proportional to emission_rate
- Custom adder works correctly
```

-----

## PHASE 2 — LP Dispatch Engine

This is the hardest phase. Split into 4 sessions to avoid timeouts.

### Session 2.1: Variable layout + cost vector

```
Create src/market_sim/model/dispatch.py — PART 1 of 4.

Build the variable layout system and cost vector assembly. DO NOT build constraints yet.

1. VariableLayout dataclass that computes column index offsets:
   Given n_gen, n_zones, n_storage, n_links, T=8760, compute:
   - vars_per_hour = n_gen + 2*n_zones + 3*n_storage + n_links + n_zones
   - Total columns = vars_per_hour * T
   - Methods to get column slice for any variable type at any hour:
     p_idx(g, t), w_idx(z, t), s_idx(z, t), chg_idx(s, t), dis_idx(s, t),
     soc_idx(s, t), flow_idx(l, t), slack_idx(z, t)
   - Also: slice-based access for "all generators at hour t" etc.

2. build_cost_vector function:
   Takes FleetArrays, mc array (n_gen, 8760), voll, storage_epsilon=0.001, n_storage, n_links, n_zones, T
   Returns flat numpy cost vector of length total_columns.
   - Thermal slots filled from mc array
   - Wind/solar slots = 0
   - Storage charge/discharge = epsilon
   - SOC slots = 0
   - Flow slots = 0
   - Slack slots = voll

3. Tests in tests/test_dispatch.py:
   - VariableLayout with 2 gens, 1 zone, 0 storage, 0 links: verify total cols = (2+2+0+0+1)*T
   - Cost vector: thermal costs in correct positions, slack = voll, renewables = 0
   - Round-trip: cost_vector[layout.p_idx(g, t)] == mc[g, t] for several g, t values

NO constraints, NO solver calls in this session. Just layout and cost vector.
```

### Session 2.2: Energy balance + generator bound constraints

```
Edit src/market_sim/model/dispatch.py — PART 2 of 4.

Add constraint matrix construction for energy balance and generator bounds. NO storage yet, NO transmission yet. Single zone only.

Build a function:
def build_single_zone_constraints(layout, fleet, demand, wind_cf, wind_cap, solar_cf, solar_cap, T=8760):
    Returns (A_sparse, row_lower, row_upper) as scipy.sparse CSC matrix and bound vectors.

Constraints (per hour t):
1. Energy balance (1 row per hour, equality):
   Σ_g P[g,t] + W[0,t] + S[0,t] + Slack[0,t] = demand[t]
   Row has +1 for each P[g,t], +1 for W, +1 for S, +1 for Slack. RHS = demand[t].

2. Generator upper bounds (n_gen rows per hour):
   P[g,t] ≤ pmax[g] * availability[g,t]
   Single entry per row.

3. Generator lower bounds (n_gen rows per hour, only if pmin > 0):
   P[g,t] ≥ pmin[g]

4. Wind upper bound (1 row per hour): W[0,t] ≤ wind_cf[t] * wind_cap
5. Solar upper bound (1 row per hour): S[0,t] ≤ solar_cf[t] * solar_cap

CRITICAL: Build vectorized. Strategy:
- Precompute the sparsity pattern for ONE hour-block (indices + indptr)
- Use scipy.sparse.kron or block_diag to replicate across all hours
- Fill the data array with vectorized numpy operations
- Convert final result to CSC

Do NOT loop over hours in Python. Use scipy.sparse.kron(eye(T), hour_block_pattern) or similar.

Tests:
- 1 gen, 1 zone, 24 hours: A matrix has correct shape (24 energy + 24 upper + 24 lower = 72 rows)
- Verify specific entries: A[energy_row_5, p_col_gen0_hour5] == 1.0
- demand vector correctly placed in row bounds
```

### Session 2.3: Solve + extract duals

```
Edit src/market_sim/model/dispatch.py — PART 3 of 4.

Add the solve function that ties layout + cost + constraints together and calls HiGHS.

def solve_dispatch(
    fleet: FleetArrays,
    demand: np.ndarray,        # (T,) for single zone
    wind_cf: np.ndarray,       # (T,)
    wind_cap: float,
    solar_cf: np.ndarray,      # (T,)
    solar_cap: float,
    voll: float = 5000.0,
    T: int = 8760,
) -> DispatchResult:

Steps:
1. Build VariableLayout
2. Build cost vector (use assemble_mc from fleet module, or pass mc directly)
3. Build constraint matrix and bounds
4. Set variable lower bounds (all >= 0) and upper bounds (inf for most, specific for bounded vars)
5. Create highspy.Highs() instance
6. Load the LP: h.addVars, h.addRows with CSC matrix
7. h.run()
8. Check status — if not optimal, raise with diagnostic info
9. Extract primal solution → map back to named arrays using layout
10. Extract dual solution → energy balance duals = zonal prices

DispatchResult dataclass:
- dispatch: np.ndarray (n_gen, T) — thermal dispatch MW
- wind_dispatched: np.ndarray (T,)
- solar_dispatched: np.ndarray (T,)
- slack: np.ndarray (T,) — unserved energy
- prices: np.ndarray (T,) — dual on energy balance
- objective_value: float
- status: str

Tests in tests/test_dispatch.py:
- 1 gen (MC=50, pmax=100), flat demand=80 → price=50 for all hours, dispatch=80
- 2 gens (MC=30 pmax=50, MC=60 pmax=50), demand=40 → price=30, only cheap gen runs
- 2 gens, demand=70 → price=60, cheap gen at 50 + expensive gen at 20
- demand=200 exceeds capacity → slack > 0, price = VOLL
- energy balance: dispatch + wind + solar + slack = demand, every hour (use np.allclose)

Use T=24 for all tests to keep solve fast.
```

### Session 2.4: Vectorization audit + 8760 test

```
Review and optimize src/market_sim/model/dispatch.py for performance.

1. Search the entire file for any `for t in range` or `for hour in` loops in matrix construction.
   If found, replace with vectorized scipy.sparse operations.

2. Add timing instrumentation:
   import time at the top. In solve_dispatch, time matrix construction and solve separately.
   Log both: f"Matrix build: {build_time:.3f}s, Solve: {solve_time:.3f}s"

3. Add a performance test in tests/test_dispatch.py:
   - Create a synthetic fleet: 200 generators across a range of marginal costs (20-80 $/MWh)
   - Sinusoidal demand profile over 8760 hours, peak = 80% of total capacity
   - Flat wind_cf=0.35, solar_cf following a daily pattern (0 at night, peak 0.6 midday)
   - Solve for full 8760 hours
   - Assert matrix build < 2 seconds (relaxed target for now)
   - Assert solve < 10 seconds
   - Assert energy balance holds for all 8760 hours
   - Print timing results

4. If the 8760-hour test fails on time, profile and identify the bottleneck.
   Common fix: ensure CSC conversion happens once at the end, not inside a loop.

Don't change the public API — just optimize internals and add the perf test.
```

-----

## PHASE 3 — Multi-Zone Transmission

### Session 3.1: Transmission model

```
Create src/market_sim/model/transmission.py

Build the pipe-and-bubble transmission model. This adds flow variables and modifies the energy balance.

1. TransmissionModel dataclass:
   - links: list of TransferLink (from iso_configs)
   - n_links: int
   - ttc: np.ndarray (n_links,) — MW limits
   - incidence_matrix: np.ndarray (n_zones, n_links) — +1 for receiving zone, -1 for sending zone

   Method: build_incidence_matrix(links, zone_names) -> sparse matrix
   For bidirectional links, flow > 0 means from_zone → to_zone.

2. Modify dispatch.py energy balance to accept flow variables:
   Energy balance row for zone z now includes:
   ... + Σ (incidence[z,l] * Flow[l,t]) + Slack[z,t] = Demand[z,t]

3. Add flow bound constraints: -ttc[l] ≤ Flow[l,t] ≤ ttc[l]
   (Or set as variable bounds directly in HiGHS — even simpler.)

4. Update solve_dispatch to accept multi-zone inputs:
   - demand: np.ndarray (n_zones, T) instead of (T,)
   - wind/solar per zone
   - TransmissionModel
   - Returns prices per zone: np.ndarray (n_zones, T)

5. Tests in tests/test_transmission.py:
   - 2 zones, 1 link (1000 MW), cheap gen in zone A, demand in zone B:
     Power flows from A to B, prices equalize
   - Same but link TTC = 0: zones decouple, zone B hits VOLL or expensive gen
   - 2 zones, surplus wind in zone A: flow = min(surplus, TTC), zone A price ≤ zone B price

Use T=24 for tests.
```

### Session 3.2: CAISO import tranches

```
Add CAISO WECC import model to src/market_sim/model/transmission.py

The WECC import node is modeled as pseudo-generators with stepped marginal costs on a supply curve.

1. Function: build_wecc_import_generators() -> list[Generator]
   Creates 3-4 synthetic Generator objects representing import tranches:
   - Tranche 1: "PNW_hydro" — 3000 MW at $15/MWh (cheap Pacific NW hydro)
   - Tranche 2: "DSW_CCGT" — 5000 MW at $35/MWh (Desert Southwest gas CC)
   - Tranche 3: "DSW_CT" — 4000 MW at $55/MWh (Desert Southwest gas CT)
   - Tranche 4: "Expensive_import" — 3000 MW at $80/MWh (marginal import)
   All assigned to zone "WECC_import".
   Mark with TODO: fit these from EIA-930 interchange data.

2. For CAISO export: add an export "sink" generator in WECC zone with negative cost
   (or zero cost) and capacity limit of 5000 MW. This lets CAISO dump surplus solar.

3. These pseudo-generators just get added to the fleet before LP construction.
   No special LP formulation needed — they participate normally via the energy balance
   and transmission link between CAISO_main and WECC_import.

4. Test:
   - CAISO with low demand: only cheap import tranche dispatches
   - CAISO with high demand: all tranches dispatch in order, prices follow stepped curve
   - CAISO with surplus solar: export to WECC (negative flow or export gen dispatches)
```

-----

## PHASE 4 — Storage

### Session 4.1: Storage SOC constraints

```
Create src/market_sim/model/storage.py

Build the storage formulation as an add-on to the dispatch LP.

1. StorageUnit dataclass:
   unit_id: str
   zone: str
   power_cap_mw: float    # charge and discharge limit
   energy_cap_mwh: float  # SOC limit
   eta_charge: float      # charging efficiency
   eta_discharge: float   # discharging efficiency
   zone_idx: int          # integer zone index

2. StorageArrays dataclass (struct-of-arrays):
   power_cap, energy_cap, eta_chg, eta_dis: np.ndarray (n_storage,)
   zone_idx: np.ndarray int (n_storage,)

3. Function: build_storage_constraints(layout, storage, T=8760)
   Returns sparse constraint matrix rows and bounds for:

   a) SOC dynamics (n_storage * T rows, equality):
      SOC[s,t] - SOC[s,t-1] - eta_chg[s] * Chg[s,t] + Dis[s,t] / eta_dis[s] = 0

   b) Cyclic boundary (n_storage rows, equality):
      SOC[s,0] - SOC[s,T-1] = 0

   c) SOC upper bounds: SOC[s,t] ≤ energy_cap[s]  (can use variable bounds)
   d) Charge bounds: Chg[s,t] ≤ power_cap[s]  (can use variable bounds)
   e) Discharge bounds: Dis[s,t] ≤ power_cap[s]  (can use variable bounds)

   The SOC dynamics matrix is banded — build it with scipy.sparse.diags:
   Main diagonal = +1 (SOC[s,t]), sub-diagonal = -1 (SOC[s,t-1]),
   plus columns for Chg and Dis.

   CRITICAL: Vectorize. Do NOT loop over hours.

4. Update energy balance in dispatch.py to include storage:
   + Dis[s,t] - Chg[s,t] for each storage unit s in zone z

5. Storage tiebreaker: cost vector has ε=0.001 for Chg and Dis columns (already in build_cost_vector).

Tests in tests/test_storage.py:
- 1 storage unit, 24 hours, cheap hours 0-11, expensive hours 12-23:
  Storage charges during cheap hours, discharges during expensive hours
- SOC cyclic: SOC[0] == SOC[23] (within tolerance)
- Energy conservation: sum(charge * eta) ≈ sum(discharge / eta) over 24 hours
- RTE loss: total discharge energy < total charge energy
```

### Session 4.2: Storage integration test

```
Add an integration test combining dispatch + transmission + storage.

In tests/test_storage.py, add:

1. ERCOT-like test: 4 zones, 6 links, 10 thermal generators spread across zones,
   wind in West zone, solar in South zone, 2 storage units (one in Houston, one in North).
   T=168 hours (one week) for reasonable solve time.

   Verify:
   - Storage charges when prices are low (high renewables)
   - Storage discharges when prices are high (evening peak)
   - Inter-zonal flows are within TTC limits
   - Energy balance holds per zone per hour
   - Prices differ across zones when transmission is congested

2. Also run the 8760-hour performance test with storage included:
   200 gens + 5 storage units + 4 zones + 6 links.
   Time the full build+solve. Print results.
   Assert solve < 15 seconds (relaxed for multi-zone + storage).
```

-----

## PHASE 5 — Capacity Evolution

### Session 5.1: Retirement logic

```
Build src/market_sim/model/capacity.py — PART 1: retirements

1. Function: apply_known_retirements(fleet: list[Generator], year: int) -> list[Generator]
   Removes generators where retirement_year <= year.
   Returns the filtered list.

2. Function: apply_economic_retirements(
    fleet: list[Generator],
    fleet_arrays: FleetArrays,
    dispatch_result: DispatchResult,
    prices: np.ndarray,  # (n_zones, T)
    config: ScenarioConfig,
    consecutive_loss_years: dict[str, int],  # unit_id -> count of unprofitable years
) -> tuple[list[Generator], dict[str, int]]:

   For each thermal generator:
   - Compute net revenue = Σ_t price[zone, t] * dispatch[g, t]
   - Compute going_forward_cost = fixed_om * pmax * 8760 (annualized)
   - If net_revenue < going_forward_cost: increment consecutive_loss_years[unit_id]
   - If consecutive_loss_years >= config.retirement_consecutive_years: mark for retirement
   - Within each fuel class, retire highest heat_rate first

   Returns updated fleet and updated loss-year tracker.

3. Function: apply_sigmoid_retirement(
    fleet: list[Generator], clean_share: float, config: ScenarioConfig
) -> list[Generator]:
   Accelerated retirement when clean_share exceeds a threshold.
   Sigmoid function: retirement_fraction = 1 / (1 + exp(-k * (clean_share - midpoint)))
   k and midpoint are Tier 2 parameters in config (add them if not present).
   Applies to coal first, then gas CT, then gas CC.

Tests in tests/test_capacity.py:
- Known retirement: generator with retirement_year=2028 removed in year 2028, present in 2027
- Economic: unprofitable generator with 2 consecutive loss years → retired
- Sigmoid: clean_share=0.6 with midpoint=0.5 → some coal retires
```

### Session 5.2: New entry + year-over-year loop

```
Edit src/market_sim/model/capacity.py — PART 2: new entry + evolution loop

1. Function: compute_lcoe(tech_type, year, config) -> float
   LCOE with Wright's Law learning curve:
   cost = base_cost * (cumulative_capacity / reference_capacity) ^ (-learning_rate)
   Apply IRA credits: PTC for wind ($/MWh reduction), ITC for solar/storage (% capex reduction)
   Tier 1 parameters for IRA credit values and phase-out schedule.

2. Function: apply_economic_new_entry(
    fleet: list[Generator], prices: np.ndarray, year: int, config: ScenarioConfig
) -> list[Generator]:
   For each candidate technology (wind, solar, li_ion_4hr, gas_cc):
   - Compute LCOE
   - Estimate expected revenue from price duration curve of prior year
   - If expected_revenue > LCOE: economic, add capacity up to annual queue cap
   - Queue cap from constants.QUEUE_CAP_GW

3. Function: apply_rps_mandate(fleet, year, config) -> list[Generator]:
   If ISO has RPS floors (CAISO), check if current clean share meets target.
   If not, force-build cheapest clean technology to fill the gap.

4. Main evolution function:
   def evolve_fleet(
       fleet: list[Generator],
       prior_results: DispatchResult | None,
       year: int,
       config: ScenarioConfig,
       loss_tracker: dict,
   ) -> tuple[list[Generator], dict]:
   Applies in order:
   1. Known retirements
   2. Economic retirements (if prior_results exist)
   3. Sigmoid retirements
   4. Known additions (generators with online_year == year)
   5. Economic new entry
   6. RPS mandates
   Returns updated fleet and loss tracker.

Tests:
- LCOE decreases over time with learning curve
- IRA credit reduces LCOE
- Queue cap limits annual additions
- evolve_fleet applies steps in correct order
- RPS mandate forces builds when clean share is below target
```

-----

## PHASE 6 — Runner + Caching

### Session 6.1: Cache system

```
Build src/market_sim/results/cache.py

1. DispatchResult needs a to_parquet(path) and from_parquet(path) method.
   Schema: one row per hour, columns for each output variable.
   Use pyarrow for writing.

2. Cache functions:
   def get_cache_path(iso: str, cache_key: str, year: int) -> Path:
       return Path(f"results/{iso}/{cache_key}/year_{year}.parquet")

   def is_cached(iso, cache_key, year) -> bool:
       return get_cache_path(iso, cache_key, year).exists()

   def save_result(result: DispatchResult, config: ScenarioConfig, iso: str, year: int):
       path = get_cache_path(iso, config.cache_key(), year)
       path.parent.mkdir(parents=True, exist_ok=True)
       result.to_parquet(path)
       # Also save config.yaml alongside if not already present
       config_path = path.parent / "config.yaml"
       if not config_path.exists():
           config.to_yaml(config_path)

   def load_result(iso, cache_key, year) -> DispatchResult:
       return DispatchResult.from_parquet(get_cache_path(iso, cache_key, year))

Tests:
- Save a result, load it back, all arrays match (np.allclose)
- is_cached returns True after save, False before
- Config YAML saved alongside results
```

### Session 6.2: Runner orchestrator

```
Build src/market_sim/runner.py

1. Main function:
   def run_scenario_iso(config: ScenarioConfig, iso: str) -> str:
       """Run all years 2026-2050 for one scenario × one ISO. Returns cache_key."""
       iso_config = get_iso_config(iso)
       fleet = load_base_fleet(iso)  # placeholder: load from data/fleet/
       loss_tracker = {}
       prior_result = None

       for year in range(2026, 2051):
           if is_cached(iso, config.cache_key(), year):
               prior_result = load_result(iso, config.cache_key(), year)
               logger.info(f"Cached: {iso} {year}")
               continue

           fleet, loss_tracker = evolve_fleet(fleet, prior_result, year, config, loss_tracker)
           # assemble inputs, solve dispatch
           result = solve_dispatch(...)
           save_result(result, config, iso, year)
           prior_result = result
           logger.info(f"Solved: {iso} {year} in {result.solve_time:.1f}s")

       return config.cache_key()

2. CLI entry points using argparse:
   python -m market_sim run --config path/to/scenario.yaml
   python -m market_sim sweep --sweep path/to/sweep.yaml [--workers N]

   For sweep mode:
   - Load SweepDefinition from YAML
   - Generate configs
   - Use ProcessPoolExecutor with --workers (default: cpu_count - 1)
   - Run each (config, iso) pair in parallel

3. Logging: use Python logging. Log full resolved config at start of each scenario.

Tests:
- Mock the solve step. Run 3 years → 3 cache files created.
- Re-run → all 3 skipped (check logs for "Cached" messages).
- Sweep with 2 configs → 2 independent runs.
```

-----

## PHASE 7 — Outputs + Emissions

### Session 7.1: Emissions + output formatting

```
Build src/market_sim/results/emissions.py and src/market_sim/results/outputs.py

1. emissions.py:
   def compute_emissions(dispatch: np.ndarray, emission_rates: np.ndarray) -> np.ndarray:
       """Vectorized: (n_gen, T) × (n_gen,) -> (T,) total CO2 per hour."""
       return (dispatch * emission_rates[:, None]).sum(axis=0)

   def compute_nox_emissions(dispatch, nox_rates):
       Same pattern.

2. outputs.py — DispatchResult should include (update if needed):
   - dispatch (n_gen, T)
   - wind_dispatched (n_zones, T)
   - solar_dispatched (n_zones, T)
   - storage_charge (n_storage, T)
   - storage_discharge (n_storage, T)
   - storage_soc (n_storage, T)
   - flows (n_links, T)
   - slack (n_zones, T)
   - prices (n_zones, T)
   - emissions_co2 (T,)
   - curtailment_wind (n_zones, T): potential - dispatched
   - curtailment_solar (n_zones, T)
   - objective_value: float
   - solve_time: float

3. Add summary statistics method to DispatchResult:
   def summarize(self) -> dict: returns annual totals, averages, peaks, capacity factors

Tests:
- Emissions = sum of dispatch × rates
- Curtailment = potential - dispatched, always >= 0
```

### Session 7.2: JSON export for frontend

```
Build src/market_sim/results/export.py and scripts/export_results.py

1. export.py:
   def export_scenario_json(cache_key: str, iso: str, output_dir: Path):
       """Load all 25 years of Parquet results, aggregate to annual summaries, write JSON."""
       Export per scenario:
       {
           "cache_key": "...",
           "iso": "...",
           "config": { ... resolved config ... },
           "years": {
               "2026": {
                   "generation_twh": {"gas_cc": X, "gas_ct": X, "coal": X, "nuclear": X, "wind": X, "solar": X},
                   "emissions_mt_co2": X,
                   "avg_price": X,
                   "peak_price": X,
                   "curtailment_twh": X,
                   "unserved_energy_mwh": X,
                   "capacity_gw": {"gas_cc": X, ...},
                   "storage_cycles": X,
               },
               "2027": { ... },
               ...
           }
       }
       Keep under 2 MB per file. Hourly data stays in Parquet.

2. scripts/export_results.py:
   CLI script that finds all completed scenarios in results/ and exports each to
   frontend/data/results/{cache_key}.json
   Also builds frontend/data/scenarios.json with metadata for all scenarios.

Tests:
- Export a 3-year scenario, verify JSON structure, verify file size < 2 MB
```

-----

## PHASE 8 — Frontend

### Session 8.1: Results dashboard

```
Build frontend/index.html, frontend/css/style.css, frontend/js/app.js, frontend/js/charts.js, frontend/js/data-loader.js

Results dashboard — static HTML page that loads scenario JSONs and renders charts.

1. Layout:
   - Header with project title
   - Scenario selector: dropdown populated from scenarios.json
   - Chart area with 4 panels:
     a) Generation mix stacked area (2026-2050) — Plotly.js
     b) Emissions trajectory line chart
     c) Price duration curve (sort prices descending) for selected year
     d) Capacity mix bar chart for selected year
   - Year slider to pick which year's duration curve / capacity bar to show

2. data-loader.js:
   - fetch scenarios.json on load
   - Lazy-load per-scenario JSON on selection
   - Cache loaded JSONs in memory (not localStorage — they may be large)

3. charts.js:
   - Fuel color mapping: gas_cc=#4A90D9, gas_ct=#7BB3E0, coal=#8B4513,
     nuclear=#9B59B6, wind=#2ECC71, solar=#F1C40F, storage=#E67E22, hydro=#1ABC9C
   - Functions: renderGenerationMix(data), renderEmissions(data),
     renderPriceDuration(data, year), renderCapacity(data, year)

4. Use Plotly.js from CDN. No npm, no build step.
   Responsive layout but desktop-first.

5. Root index.html at repo root that links to frontend/index.html and learning-hub/index.html.
```

### Session 8.2: Decision tracker page

```
Build frontend/decisions.html and frontend/js/decisions.js

Interactive decision tracker with form persistence.

1. Define decision domains as a JS data structure:
   [
     {
       id: "weather_year",
       domain: "Structural",
       question: "Which weather year for base case?",
       options: ["2022", "2023", "2024", "2025"],
       status: "open",  // "open", "leaning", "decided"
       leaning: "2024",
       notes: ""
     },
     {
       id: "caiso_voll",
       domain: "Structural",
       question: "CAISO VOLL level?",
       options: ["$1,000/MWh", "$2,000/MWh"],
       status: "open",
       leaning: "$2,000/MWh",
       notes: ""
     },
     // Add 8-10 more from build-plan §5 Open Items + reasonable additions
   ]

2. Render: collapsible sections by domain. Each decision shows:
   - Question text
   - Radio buttons for options
   - Notes textarea
   - Status badge (open/leaning/decided)

3. On change: save to localStorage with key marketsim_decision_{id}
   On load: restore from localStorage

4. Export button: JSON dump of all decisions to clipboard

5. Clean styling consistent with index.html
```

### Session 8.3: Parameter citation browser

```
Build frontend/parameters.html and create frontend/data/parameters.json

1. parameters.json: Create an initial version with 20-30 parameters from constants.py.
   Schema per entry matches build-plan §9:
   { param_id, display_name, value, unit, domain, tier, source, source_date,
     page_or_table, url, notes, old_repo_location, last_verified }

2. parameters.html:
   - Search box (filters by param_id, display_name, source, domain)
   - Filter dropdowns: by domain, by tier
   - Table with columns: Name, Value, Unit, Tier, Source, Domain
   - Click row to expand: shows full citation details (all fields)
   - Sortable columns

3. Load from parameters.json. No build step.
   Consistent styling with other frontend pages.
```

-----

## PHASE 9 — Learning Hub (optional, do after core model works)

### Session 9.1: Scrollytell framework

```
Build learning-hub/shared/scrollytell.css and scrollytell.js, plus learning-hub/index.html

Lightweight scrollytell engine:
1. scrollytell.js:
   - Uses IntersectionObserver to detect which narrative step is in view
   - Fires custom events: 'step-enter', 'step-exit' with step index
   - Sticky chart panel stays fixed while narrative text scrolls
   - Auto-advances through animation states

2. scrollytell.css:
   - Two-column layout: sticky chart (60% width) + scrolling narrative (40%)
   - Mobile: stacks vertically, chart shrinks
   - Step highlighting: active step has accent color, others fade
   - Smooth transitions between chart states

3. learning-hub/index.html:
   Landing page with cards linking to each topic:
   - LP Dispatch, Capacity Evolution, Storage, Transmission, Scenarios
   - Each card has a short description and an icon/illustration

Keep it minimal. D3.js from CDN for charts. No other dependencies.
```

### Session 9.2: LP Dispatch explainer

```
Build learning-hub/lp-dispatch/index.html

Scrollytell page: "How the Model Decides Who Generates"

Use the shared scrollytell framework. 5-generator, 24-hour example.

Steps:
1. "Meet the generators" — show 5 generators as blocks with their marginal costs
2. "Stack them by cost" — animate into merit order
3. "Draw the demand line" — show 24-hour demand curve
4. "The LP fills from cheapest" — animate dispatch filling from bottom of merit order
5. "The price = the last unit needed" — highlight marginal generator, show dual = price
6. "Add wind at zero cost" — insert wind, show it displaces expensive generators
7. "Surplus wind → curtailment" — show what happens when wind exceeds demand
8. "Why LP beats heuristics" — side-by-side: LP global optimum vs. greedy

Use D3.js for the animated bar charts. Synthetic data, not real model results.
```

-----

## TIPS FOR EACH SESSION

1. **Copy-paste one session prompt at a time.** Don’t combine sessions.
1. **After each session succeeds:** `git add -A && git commit -m "phase X.Y: description"`
1. **If it times out mid-session:** paste “Continue where you left off” — Claude Code can see the files on disk.
1. **If it writes buggy code:** paste “Run the tests and fix any failures” as a follow-up.
1. **If tests fail on import:** paste “Run pytest tests/test_X.py -x and fix the first failure.”
1. **Before Phase 2:** manually verify `pip install -e .` works, and that `from market_sim.config.scenarios import ScenarioConfig` imports without error.
1. **Before Phase 8:** run the model on a toy scenario and export JSON so the frontend has data to load.