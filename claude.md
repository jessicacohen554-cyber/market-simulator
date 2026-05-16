# Market Simulation Model — Claude Code Instructions

## What This Is

LP-based electricity market dispatch simulator. Two ISOs (ERCOT 4-zone, CAISO 1-zone + WECC import node), hourly dispatch 2026–2050, parameterized scenario system.

## Stack

- Python 3.11+, HiGHS via `highspy`, numpy, scipy.sparse, pandas, pyarrow, pydantic, pyyaml
- **FORBIDDEN:** Pyomo, PuLP, scipy.optimize, Numba. Direct CSC matrix → HiGHS only.

## Architecture

```
src/market_sim/
  config/    → scenarios.py (ScenarioConfig dataclass), constants.py, iso_configs.py
  data/      → eia_loader.py, fleet.py, renewables.py, fuel.py
  model/     → dispatch.py (LP core), transmission.py, storage.py, capacity.py
  policy/    → ira.py, rps.py, carbon.py
  results/   → cache.py, outputs.py, emissions.py, export.py
  runner.py  → main orchestrator
tests/       → pytest, one file per module
```

## Non-Negotiable Rules

1. **No Python loops over hours in LP construction.** Use np.tile, np.repeat, scipy.sparse.kron, block_diag. If you write `for t in range(8760):` in the matrix builder, stop and vectorize.
1. **Renewables are decision variables** on LHS of energy balance with MC=0, upper bound = CF × capacity. NOT netted from demand.
1. **Prices = LP duals** on energy balance constraints. No separate pricing model.
1. **No magic numbers.** Every value from ScenarioConfig or constants.py with citation comment.
1. **Struct-of-arrays before LP construction.** Convert Pydantic objects → FleetArrays (parallel numpy arrays). LP builder only touches arrays and scalars.
1. **Parquet for results.** One file per scenario-year. Check-before-run caching.
1. **Full 8760 hours always.** No representative days/weeks.
1. **Storage tiebreaker ε = 0.001 $/MWh** on charge+discharge to prevent degeneracy.
1. **One-pass capacity evolution.** No within-year convergence iteration.
1. **Every public function gets a docstring.** Every module gets a module-level docstring.

## LP Variable Layout (per ISO-year)

Flat column vector: P[g,t] | W[z,t] | S[z,t] | Chg[s,t] | Dis[s,t] | SOC[s,t] | Flow[l,t] | Slack[z,t]
Total columns = T × (n_gen + 2×n_zones + 3×n_storage + n_links + n_zones), T=8760

## Objective

min Σ mc[g,t]×P[g,t] + ε×(Chg+Dis) + VOLL×Slack
Where mc = heat_rate × fuel_price + vom + emission_rate × carbon_price + nox_rate × nox_price + …

## Key Constraints

- Energy balance (per zone, per hour): thermal + wind + solar + discharge - charge + net_flow + slack = demand
- Generator bounds: pmin ≤ P[g,t] ≤ pmax × availability[g,t]
- Renewable bounds: 0 ≤ W/S ≤ cf × capacity
- Storage SOC: SOC[t] = SOC[t-1] + η_chg×Chg[t] - Dis[t]/η_dis, cyclic boundary
- Transmission: -TTC ≤ Flow ≤ TTC

## Naming Conventions

- Python: snake_case. Functions: verb_noun (solve_dispatch, evolve_fleet, load_eia_profiles).
- Single-letter vars only in LP construction: t=hour, g=generator, z=zone, s=storage, with comment.
- Feature branches: phase-N/description. Commits: imperative present tense.

## Testing Pattern

Always test with trivial cases first: 1 gen, 1 zone, 24 hours. Then scale up.

## Reference Docs (in repo)

- `market-sim-methodology.md` — LP formulation, matrix construction, scenario architecture (THE SPEC)
- `build-plan.md` — phase plan, extraction manifest, directory structure
- When in doubt, methodology spec wins.