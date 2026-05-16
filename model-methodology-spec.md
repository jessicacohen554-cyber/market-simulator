# Market Simulation Model — Methodology & Build Specification

**Purpose:** Explicit design specification for building an LP-based electricity market dispatch model. This document governs the model’s mathematical formulation, computational patterns, scenario architecture, and performance requirements. It is the primary instruction set for the build agent — follow it literally.

**Scope:** Two independent ISOs (ERCOT 4-zone, CAISO 1-zone + WECC import node). Hourly dispatch over a 2026–2050 trajectory. Parameterized scenario system supporting batch sweeps and single custom runs.

**Runtime:** Python 3.11+. Solver: HiGHS via `highspy`. No Pyomo, no PuLP, no scipy.optimize.

-----

## 1. LP Formulation

### 1.1 Decision Variables

For a single ISO, single year (8,760 hours):

|Variable    |Dimensions        |Description                 |
|------------|------------------|----------------------------|
|`P[g,t]`    |generators × hours|Thermal dispatch (MW)       |
|`W[z,t]`    |zones × hours     |Wind dispatched (MW)        |
|`S[z,t]`    |zones × hours     |Solar dispatched (MW)       |
|`Chg[s,t]`  |storage × hours   |Storage charge (MW)         |
|`Dis[s,t]`  |storage × hours   |Storage discharge (MW)      |
|`SOC[s,t]`  |storage × hours   |State of charge (MWh)       |
|`Flow[l,t]` |links × hours     |Transmission flow (MW)      |
|`Slack[z,t]`|zones × hours     |Unserved energy (MW)        |
|`Dump[z,t]` |zones × hours     |Overgeneration absorbed (MW)|

Renewables are **decision variables on the LHS of the energy balance**, not netted from demand. This is critical — the LP decides how much renewable generation to dispatch. Curtailment = potential minus dispatched.

The dump variable absorbs overgeneration in hours where minimum generation (must-run nuclear with `Pmin > 0`, storage mid-discharge) exceeds demand. With negative-MC renewables (e.g., wind receiving PTC production credits), the LP could otherwise face infeasibility or game production credits by overproducing credited energy just to collect the subsidy on curtailed power. The dump variable makes the LP always feasible and its cost structure prevents credit gaming.

### 1.2 Objective Function

Minimize total system cost:

```
min  Σ_g Σ_t  mc[g,t] × P[g,t]
   + Σ_z Σ_t  0 × W[z,t]  +  0 × S[z,t]        # zero marginal cost
   + Σ_s Σ_t  ε × (Chg[s,t] + Dis[s,t])          # small tiebreaker to avoid degeneracy
   + Σ_z Σ_t  VOLL[z] × Slack[z,t]
   + Σ_z Σ_t  dump_cost × Dump[z,t]
```

Where `mc[g,t] = heat_rate[g] × fuel_price[g,t] + vom[g] + emission_rate[g] × carbon_price[t] + nox_rate[g] × nox_price[t] + <other adders>`

`dump_cost = max(ε, -min(wind_mc, solar_mc) + ε)`. When renewables have zero MC, dump_cost = ε (negligible). When renewables have negative MC (e.g., wind with PTC = -$26/MWh), dump_cost = $26.001/MWh — just above the absolute value of the production credit. This ensures the LP never profits from overproducing credited renewables into the dump.

The marginal cost vector is assembled from parameters. Every cost component is a named parameter (Tier 1 or Tier 2). No hardcoded values in the cost calculation.

Storage tiebreaker `ε` = 0.001 $/MWh. Prevents degenerate solutions where the solver charges and discharges simultaneously. This is a standard trick — document it but don’t make it configurable.

### 1.3 Constraints

**Energy balance (per zone z, per hour t):**

```
Σ_{g∈z} P[g,t] + W[z,t] + S[z,t] + Σ_{s∈z} Dis[s,t] - Σ_{s∈z} Chg[s,t]
  + Σ_{imports to z} Flow[l,t] - Σ_{exports from z} Flow[l,t]
  + Slack[z,t] - Dump[z,t]
  = Demand[z,t]
```

The **dual variable on this constraint = zonal price ($/MWh)**. This is the model’s primary price output.

**Generator bounds:**

```
Pmin[g] ≤ P[g,t] ≤ Pmax[g] × availability[g,t]
```

Where `availability[g,t] = (1 - EFORd[g]) × seasonal_factor[g,month(t)]`. Must-run units have `Pmin > 0`.

**Renewable bounds:**

```
0 ≤ W[z,t] ≤ wind_cf[z,t] × wind_capacity[z]
0 ≤ S[z,t] ≤ solar_cf[z,t] × solar_capacity[z]
```

Capacity factor profiles sourced from EIA Hourly Grid Monitor (actual generation / installed capacity). These contain ~5% embedded historical curtailment — accepted as a known conservatism. The LP produces its own endogenous curtailment on top.

**Storage dynamics:**

```
SOC[s,t] = SOC[s,t-1] + η_chg[s] × Chg[s,t] - Dis[s,t] / η_dis[s]
0 ≤ SOC[s,t] ≤ energy_cap[s]
0 ≤ Chg[s,t] ≤ power_cap[s]
0 ≤ Dis[s,t] ≤ power_cap[s]
SOC[s,0] = SOC[s,8759]          # cyclic boundary
```

No cycling limit constraint in the initial build. The LP with perfect foresight will optimize dispatch; cycling emerges from economics. Flag for future sensitivity if unrealistic cycling appears.

**Transmission:**

```
-TTC[l] ≤ Flow[l,t] ≤ TTC[l]    # bidirectional; or use two non-negative variables
```

ERCOT: 6 bidirectional links across 4 zones (North↔South, North↔West, North↔Houston, South↔Houston, South↔West, West↔Houston).

CAISO: single zone + WECC import/export node modeled as **pseudo-generators on a stepped supply curve**:

- Import tranches: 3–4 blocks with increasing marginal cost and MW limits (e.g., PNW hydro cheap/limited, Desert SW CCGT mid, Desert SW CT expensive). These are `P[g,t]` variables assigned to the WECC “zone” with their own cost and capacity.
- Export: allow CAISO to push power to the import node at a cost of zero or small negative (represents dumping surplus solar).
- Aggregate limit: ~12–15 GW import, ~5 GW export. Derive from EIA-930 interchange data.

**Non-negativity:** All dispatch, charge, discharge, slack, dump, SOC ≥ 0. Flows can be negative (bidirectional) or modeled as two non-negative variables per link.

### 1.4 Policy Constraint Extension Point

Some policy parameters are **cost adders** (change the objective vector): carbon price, NOx price, SO2 price. These are handled by the marginal cost assembly — no structural change to the LP.

Some policy parameters are **constraints** (add rows to the LP): NOx emission caps, RPS minimums (minimum % clean generation), potentially others.

**Build rule:** Every policy parameter in the config is tagged `kind: "adder"` or `kind: "constraint"`. The LP builder checks for active constraint-type policies and appends rows:

```
# Example: RPS constraint
Σ_z (W[z,t] + S[z,t] + nuclear[z,t]) ≥ rps_target × Σ_z Demand[z,t]   # annual
```

```
# Example: NOx cap
Σ_g Σ_t nox_rate[g] × P[g,t] ≤ nox_limit                              # annual
```

**Initial build:** All policies are cost adders. The constraint extension point exists in the builder (check config, append rows if flagged) but no constraint-type policies are defined yet. This avoids variable matrix structure in the first version while keeping the door open.

-----

## 2. LP Construction Pattern — Block-Diagonal with Vectorized Assembly

This is the most performance-critical code in the model. **Do not build the constraint matrix with Python loops over hours and generators.** Use vectorized sparse matrix construction.

### 2.1 Matrix Structure

The LP for a single ISO-year has this block structure:

```
A = [ B_1   0    0   ...  0    L  ]    (energy balance + generator bounds, hour 1)
    [  0   B_2   0   ...  0    L  ]    (hour 2)
    [  0    0   B_3  ...  0    L  ]    (hour 3)
    [ ...                     ... ]
    [  0    0    0   ... B_T   L  ]    (hour T)
    [       S (storage SOC linkage)    ]    (inter-temporal coupling)
    [       Policy constraints         ]    (if any active)
```

Where:

- `B_t` is the per-hour constraint block (energy balance + gen bounds + renewable bounds + transmission). Structurally identical across hours — same sparsity pattern, different RHS values and potentially different coefficient values (fuel prices can vary hourly).
- `L` is the transmission flow coefficient matrix (same every hour for pipe-and-bubble).
- `S` is the storage SOC linkage — a banded matrix coupling `SOC[s,t]` to `SOC[s,t-1]`, `Chg[s,t]`, `Dis[s,t]`.

### 2.2 Construction Algorithm

```python
# PSEUDOCODE — the builder follows this pattern

def build_lp(fleet_arrays, demand, wind_cf, solar_cf, storage, transmission, params):
    """
    fleet_arrays: struct-of-arrays (see §3.1) — pmax, pmin, mc, zone_idx, etc.
    All inputs are numpy arrays. No Python objects in the hot path.
    """
    n_gen = len(fleet_arrays.pmax)
    n_zones = params.n_zones
    n_storage = len(storage.power_cap)
    n_links = len(transmission.ttc)
    T = 8760

    # --- Variable layout (column indices) ---
    # P[g,t]: n_gen × T columns     (thermal dispatch)
    # W[z,t]: n_zones × T           (wind dispatched)
    # S[z,t]: n_zones × T           (solar dispatched)
    # Chg[s,t]: n_storage × T       (charge)
    # Dis[s,t]: n_storage × T       (discharge)
    # SOC[s,t]: n_storage × T       (state of charge)
    # Flow[l,t]: n_links × T        (transmission)
    # Slack[z,t]: n_zones × T       (unserved energy)
    # Dump[z,t]: n_zones × T        (overgeneration absorbed)
    #
    # Total columns = T × (n_gen + 4*n_zones + 3*n_storage + n_links)

    vars_per_hour = n_gen + 4*n_zones + 3*n_storage + n_links

    # --- Cost vector (objective) ---
    # Assemble as a flat array. mc[g,t] varies by hour (fuel price changes).
    # Use np.tile for static components, element-wise for dynamic.
    cost = np.zeros(vars_per_hour * T)
    # ... fill thermal costs, storage epsilon, VOLL for slack ...

    # --- Per-hour block B_t (energy balance + bounds) ---
    # Build ONE prototype sparse block for the constraint structure,
    # then use scipy.sparse.block_diag or kron to replicate across hours.
    #
    # Energy balance: n_zones rows
    # Gen upper bound: n_gen rows   (P[g,t] ≤ Pmax × avail)
    # Gen lower bound: n_gen rows   (P[g,t] ≥ Pmin)  [or combine as two-sided]
    # Wind upper bound: n_zones rows
    # Solar upper bound: n_zones rows
    # Storage charge/discharge bounds: 2*n_storage rows
    # Transmission bounds: 2*n_links rows (or use variable bounds directly)

    # KEY INSIGHT: For the energy balance rows, the coefficient pattern
    # (which generators are in which zone) is the same every hour.
    # Build a zone-membership matrix once:
    zone_gen_map = sparse.csr_matrix(...)  # n_zones × n_gen, entry = 1 if gen g in zone z

    # The per-hour block's sparsity pattern is fixed. Only RHS values change.
    # Build the pattern once, then replicate.

    # --- Storage SOC linkage ---
    # SOC[s,t] - SOC[s,t-1] - η_chg × Chg[s,t] + Dis[s,t]/η_dis = 0
    # This is a banded submatrix linking adjacent hours.
    # Build with scipy.sparse.diags: main diagonal = +1, sub-diagonal = -1,
    # plus entries for Chg and Dis columns.
    # Cyclic boundary: SOC[s,0] - SOC[s,T-1] row wraps around.

    # --- Assemble full A matrix ---
    # Use scipy.sparse.bmat or vstack to compose blocks.
    # Convert to CSC format (HiGHS native) at the end.

    # --- Pass to HiGHS ---
    h = highspy.Highs()
    h.addVars(n_cols, cost, col_lower, col_upper)
    h.addRows(n_rows, row_lower, A_csc, row_upper)  # CSC matrix
    h.run()

    # --- Extract results ---
    primal = h.getSolution().col_value      # dispatch values
    dual = h.getSolution().row_dual         # prices from energy balance rows
    # Map back to named arrays using the variable layout offsets.
```

### 2.3 Critical Performance Rules for the Build Agent

1. **No Python loops over hours in matrix construction.** Use `np.tile`, `np.repeat`, `scipy.sparse.kron`, `scipy.sparse.block_diag`. If you find yourself writing `for t in range(8760):` in the matrix builder, stop and vectorize.
1. **Build the sparsity pattern once, fill values separately.** The CSC column pointers and row indices are the same for every hour-block. Compute them once, then fill the `data` array with vectorized operations.
1. **Struct-of-arrays for fleet data.** Convert Pydantic generator objects to parallel numpy arrays (`pmax_array`, `heat_rate_array`, `zone_idx_array`, `mc_array`) before entering the LP builder. The builder never touches Python objects.
1. **RHS vector assembly is also vectorized.** `Demand[z,t]` is a `(n_zones, T)` array. Generator availability bounds are `pmax[:, None] * availability[:, :]`. These are numpy broadcasts, not loops.
1. **Pre-allocate the CSC arrays.** Count nonzeros analytically (you know the structure), allocate `data`, `indices`, `indptr` arrays once, fill them.
1. **Target: matrix construction < 1 second, solve < 5 seconds, total < 10 seconds per ISO-year.**

-----

## 3. Data Layout & Struct-of-Arrays

### 3.1 Fleet Arrays

The fleet is loaded from EIA-860 data and internal parameters into Pydantic models for validation. Before LP construction, convert to:

```python
@dataclass
class FleetArrays:
    """Parallel arrays indexed by generator index g. All numpy."""
    pmax: np.ndarray          # (n_gen,) MW
    pmin: np.ndarray          # (n_gen,) MW — 0 for non-must-run
    heat_rate: np.ndarray     # (n_gen,) BTU/kWh
    vom: np.ndarray           # (n_gen,) $/MWh
    emission_rate: np.ndarray # (n_gen,) tCO2/MWh
    nox_rate: np.ndarray      # (n_gen,) lb NOx/MWh (or tons, be consistent)
    zone_idx: np.ndarray      # (n_gen,) int — which zone
    fuel_type: np.ndarray     # (n_gen,) int enum — for grouping/reporting
    availability: np.ndarray  # (n_gen, 8760) — EFORd × seasonal factor
    unit_id: np.ndarray       # (n_gen,) str — for result mapping back to names
```

### 3.2 Marginal Cost Assembly

```python
def assemble_mc(fleet: FleetArrays, fuel_prices: np.ndarray,
                carbon_price: np.ndarray, nox_price: np.ndarray,
                **adders) -> np.ndarray:
    """
    Returns (n_gen, 8760) marginal cost array.
    fuel_prices: (n_gen, 8760) or (n_fuel_types, 8760) mapped via fleet.fuel_type
    carbon_price: (8760,) or scalar
    All adders are keyword arguments — extensible for any future cost component.
    """
    mc = fleet.heat_rate[:, None] * fuel_prices + fleet.vom[:, None]
    mc += fleet.emission_rate[:, None] * carbon_price[None, :]
    mc += fleet.nox_rate[:, None] * nox_price[None, :]
    for name, (rate_array, price_array) in adders.items():
        mc += rate_array[:, None] * price_array[None, :]
    return mc
```

This is fully vectorized — no loops. Adding a new cost adder means adding a rate array to FleetArrays and a price trajectory to the scenario config.

-----

## 4. Scenario Architecture

### 4.1 Tiered Parameter System

Every model input is a named parameter with a default value and a tier assignment.

**Tier 0 — Structural.** Changes the LP’s shape or invalidates cross-scenario comparisons. Set once per model configuration.

Examples: weather year, ISO selection, zone topology, hourly resolution, VOLL by zone, storage technology menu (which types exist).

**Tier 1 — Scenario levers.** The parameters varied across runs. Define the uncertainty space.

Examples: gas price path, carbon price trajectory, NOx price, demand growth rate, renewable buildout pace, storage deployment, retirement aggressiveness.

`storage_deployment` sets the base-year (2026) storage fleet size. Subsequent years grow via economic screening.

**Tier 2 — Expert/sensitivity.** Changeable but normally held at defaults.

Examples: heat rates by unit, storage RTE, discount rate, forced outage rates, technology learning curves, CAISO import curve shape, VOM by technology.

**Tier 3 — Calibration.** Tuned during validation, then frozen.

Examples: renewable CF adjustment factors, seasonal availability patterns, basis differentials, WECC import tranche parameters.

**Implementation:**

```python
@dataclass
class ScenarioConfig:
    """Full model parameterization. Every field has a default.
    Tier tags are metadata — they don't affect runtime behavior."""

    # --- Tier 0: Structural ---
    weather_year: int = 2024
    iso: str = "ERCOT"              # or "CAISO"
    voll: float = 5000.0            # $/MWh
    # ...

    # --- Tier 1: Scenario levers ---
    gas_price_path: str = "mid"     # or array, or path to CSV
    carbon_price: float = 0.0       # $/ton — scalar or trajectory
    nox_price: float = 0.0
    demand_growth_rate: float = 0.01
    # ...

    # --- Tier 2: Expert ---
    storage_rte_4hr: float = 0.85
    discount_rate: float = 0.08
    # ...

    # --- Tier 3: Calibration ---
    # ...

    def cache_key(self) -> str:
        """Deterministic hash of the full config. Used for result caching."""
        return hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True).encode()
        ).hexdigest()[:16]
```

### 4.2 Single-Run Mode

CLI accepts a YAML file that overrides any parameter:

```bash
python -m market_sim run --config my_scenario.yaml
```

```yaml
# my_scenario.yaml — only specify overrides, everything else uses defaults
iso: ERCOT
gas_price_path: high
carbon_price: 45.0
nox_price: 2.5
demand_growth_rate: 0.025
storage_rte_4hr: 0.82   # testing sensitivity
```

Unspecified parameters use `ScenarioConfig` defaults. The full resolved config is logged with every run.

### 4.3 Batch Sweep Mode

A sweep definition specifies which Tier 1 parameters to vary and what values to test. The sweep generator produces a list of `ScenarioConfig` objects.

```yaml
# sweep_gas_carbon.yaml
sweep:
  gas_price_path: [low, mid, high]
  carbon_price: [0, 25, 50]
# All other parameters at defaults. This produces 9 scenarios.
```

```yaml
# sweep_demand_buildout.yaml
sweep:
  demand_growth_rate: [0.005, 0.015, 0.03]
  renewable_buildout_pace: [slow, mid, aggressive]
# 9 more scenarios, orthogonal to the gas×carbon sweep.
```

Sweeps can be composed (run multiple sweep files) or run independently. The runner deduplicates by cache key — if a scenario exists from a previous sweep, it’s skipped.

**No full factorial on all dimensions.** The user pairs parameters deliberately. The sweep generator supports `mode: factorial` (default), `mode: lhs` (Latin hypercube — future), or `mode: list` (explicit list of configs).

### 4.4 Caching

Each scenario-year result is stored as a **single Parquet file**:

```
results/
  {iso}/
    {cache_key}/
      year_2026.parquet
      year_2027.parquet
      ...
      year_2050.parquet
      config.yaml          # full resolved ScenarioConfig for reproducibility
```

Before running a scenario-year, check if the parquet exists. If yes, skip. This makes the system stop/resume capable and avoids recomputing validated results.

The Parquet contains all hourly outputs for that ISO-year: dispatch by unit, zonal prices, emissions, storage SOC, curtailment, flows, slack. Schema is fixed and documented in a data dictionary.

-----

## 5. Capacity Evolution — One-Pass Sequential

### 5.1 Architecture

Fleet evolves year-over-year within a scenario. Year N+1’s fleet depends on Year N’s dispatch and price results. **No within-year convergence iteration.** This is a deliberate simplification — the one-pass approach is standard in screening models and avoids instability.

```
For year in 2026..2050:
    1. Start with fleet from prior year (or base fleet for 2026)
    2. Apply known retirements (EIA-860 announced)
    3. Apply economic retirement screen (fuel-type-aware, uses Year N-1 results)
    4. Apply known additions (EIA-860 under construction, signed PPAs)
    5. Apply economic new entry screen (LCOE vs expected revenue)
    6. Apply policy-mandated builds (RPS compliance)
    7. Assemble updated fleet → run dispatch LP → cache results
```

### 5.2 Economic Retirement

A unit retires if its **net revenue < going-forward cost** for N consecutive years, where N varies by fuel type:

- **Coal:** 1 consecutive loss year (faster exit — reflects regulatory risk and carbon liability)
- **Gas CT:** 2 consecutive loss years
- **Gas CC:** 3 consecutive loss years (most patient — higher capital sunk, longer expected life)

Revenue and cost definitions:

- Net revenue = `Σ_t price[z,t] × dispatch[g,t]` (from prior year’s LP results)
- Going-forward cost = fixed O&M × FOM multiplier (not capital — sunk cost)
- FOM multipliers: coal = 1.3× (captures regulatory risk, carbon liability, ESG pressure), gas = 1.0×
- Retirement ordering: within each fuel class, least efficient (highest heat rate) retires first

**Reliability floor:** Thermal capacity cannot fall below `(peak_demand - firm_clean) × (1 + reserve_margin)`, where `reserve_margin` defaults to 15% (Tier 2 parameter) and `firm_clean = nuclear + hydro capacity`. If economic retirements would breach the floor, the most efficient units are retained.

**Design note:** Sigmoid retirement was considered and rejected in favor of fully economic retirement with fuel-type-aware thresholds. The economic approach is more transparent — every retirement is traceable to a revenue shortfall — and avoids the arbitrary sigmoid midpoint parameter. The coal FOM multiplier (1.3×) captures the non-economic pressures (regulatory risk, ESG) that the sigmoid was designed to model.

### 5.3 Economic New Entry

Screen by technology: if `expected_revenue > LCOE`, the technology is economic for entry.

- Expected revenue estimated from prior year’s price duration curve
- LCOE from technology cost assumptions with learning curves (Tier 2 parameters)
- IRA credits reduce LCOE (PTC for wind, ITC for solar/storage — Tier 1 parameters)
- Annual build rate capped per technology (e.g., ERCOT ~12 GW/yr queue throughput)
- Technology priority: policy-mandated first, then ranked by revenue-minus-LCOE margin

### 5.4 Known Pipeline

EIA-860 provides: units under construction (with expected online date), announced retirements (with expected date). These are deterministic — they happen regardless of economics. Transition point from known to modeled: ~2030 for near-term pipeline, model takes over for years beyond the data horizon.

### 5.5 Storage New Entry

Storage enters via economics-based screening. For each technology,
expected arbitrage revenue from the prior year's price profile is
compared against annualized cost (capex × CRF + FOM, with IRA ITC).
Revenue = Σ_days max(0, discharge_avg - charge_avg/RTE) × duration.
Profitable techs ranked by margin, built highest-margin first,
subject to annual build cap and cumulative ceiling per ISO. Base-year
fleet set by storage_deployment parameter; all subsequent growth
is endogenous.

-----

## 6. Parallelism & Performance

### 6.1 Parallel Execution

Independent work units: `(scenario_config, iso)` pairs. Within each work unit, years run sequentially (capacity evolution dependency).

```python
from concurrent.futures import ProcessPoolExecutor

def run_scenario_iso(config: ScenarioConfig, iso: str):
    """Run all 25 years for one scenario × one ISO. Sequential."""
    fleet = load_base_fleet(iso, config)
    for year in range(2026, 2051):
        cache_path = get_cache_path(iso, config.cache_key(), year)
        if cache_path.exists():
            results = load_cached(cache_path)
        else:
            fleet = evolve_fleet(fleet, results_prev, year, config)
            inputs = assemble_inputs(fleet, year, config)
            results = solve_dispatch(inputs)
            save_parquet(results, cache_path)
        results_prev = results
    return config.cache_key()

# Main runner
with ProcessPoolExecutor(max_workers=N_CORES) as pool:
    futures = []
    for config in scenario_configs:
        for iso in config.isos:
            futures.append(pool.submit(run_scenario_iso, config, iso))
    for f in as_completed(futures):
        print(f"Completed: {f.result()}")
```

### 6.2 Performance Targets

|Operation                                             |Target      |
|------------------------------------------------------|------------|
|LP matrix construction (1 ISO, 1 year)                |< 1 second  |
|LP solve (HiGHS, 1 ISO, 1 year, 8760 hrs)             |< 5 seconds |
|Full scenario-year (evolve + assemble + solve + cache)|< 10 seconds|
|Single scenario × 1 ISO × 25 years                    |< 5 minutes |
|Memory per LP solve                                   |< 2 GB      |
|20 scenarios × 2 ISOs on 8 cores                      |< 30 minutes|

### 6.3 Memory Management

Each worker builds and discards the LP per year. Do not accumulate LP objects across years. The HiGHS instance should be created fresh per solve (or cleared with `h.clear()`). Only the result arrays (dispatch, prices, emissions) persist in memory during the year-loop, and they’re written to Parquet immediately.

-----

## 7. Build Agent Instructions

### 7.1 Rules

1. **No magic numbers.** Every numeric value comes from `ScenarioConfig` or `constants.py` with a citation comment.
1. **No Python loops in the LP builder.** Vectorize with numpy/scipy.sparse. If writing `for t in range(8760)`, stop and restructure.
1. **Every input is a parameter.** If you’re tempted to hardcode a value, add it to `ScenarioConfig` with a default and a tier tag.
1. **Struct-of-arrays before LP construction.** Convert fleet objects to `FleetArrays` numpy arrays. The LP builder’s only imports from the data layer are arrays and scalars.
1. **Test each phase independently.** Trivial test cases before scaling up: 1 generator, 1 zone, 24 hours. Then 2 generators. Then full fleet.
1. **Parquet for all result storage.** No CSV, no HDF5, no pickle. Parquet with PyArrow, column types documented in a schema file.
1. **YAML for all configuration.** Scenario configs, sweep definitions, ISO topology — all YAML with Pydantic validation on load.
1. **Cache key = hash of full resolved config.** Not a human-readable name. The config.yaml saved alongside results provides readability.
1. **Log the full resolved config at the start of every run.** If a run produces unexpected results, the first diagnostic is “what config was actually used.”
1. **Renewables are decision variables.** They appear on the LHS of energy balance with zero marginal cost and upper bound = CF × capacity. They are NOT subtracted from demand on the RHS.

### 7.2 What NOT to Build

- No unit commitment (MIP). Pure LP. Fractional dispatch is acceptable.
- No ramp constraints in initial build. Flag as future enhancement.
- No stochastic outages. Deterministic derate only.
- No ORDC / operating reserve demand curve. Scarcity shows up via VOLL.
- No separate pricing model. Prices are LP duals. Period.
- No representative weeks or days. Full 8760 always.
- No convergence iteration in capacity evolution. One pass per year.
- No web framework or API server. CLI + YAML + Parquet files.