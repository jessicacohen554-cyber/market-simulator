# Market Simulation Model — Claude Code Instructions

## What This Is

LP-based electricity market dispatch simulator. Forecasting model (2026–2050) with a historical-backcast mode for calibration. Multi-ISO: seven ISOs registered in `config/iso_configs.py` — ERCOT (6 zones, the calibrated reference), CAISO (3 zones + WECC import node), PJM (4 zones), MISO (3 zones), SPP (2 zones), NYISO, NEISO — sharing one ISO-agnostic LP. Hourly 8760 dispatch, parameterized scenario system.

**Forecast vs backcast:** the model forecasts by default. Historic overlays — CAMPD outage windows, F923 delivered fuel prices, plant-specific CEMS emission rates, weather-year pinning — are **backcast/calibration only**; never treat them as the forecast methodology.

## Stack

- Python 3.11+, HiGHS via `highspy`, numpy, scipy.sparse, pandas, pyarrow, pydantic, pyyaml
- **FORBIDDEN:** Pyomo, PuLP, scipy.optimize, Numba. Direct CSC matrix → HiGHS only.

## Architecture

```
src/market_sim/
  config/    → scenarios.py (ScenarioConfig dataclass), constants.py, iso_configs.py (7-ISO topology)
  data/      → eia_loader.py, fleet.py (CAMPD binning), renewables.py, fuel.py, outages.py, hydro.py, ownership.py
  model/     → dispatch.py (LP core), commitment.py (3-solve UC screen), transmission.py, storage.py, capacity.py
  policy/    → ira.py, rps.py, carbon.py, eac.py, constraints.py
  results/   → cache.py, outputs.py, emissions.py, export.py, calibration.py, plant_financials.py
  runner.py  → main orchestrator (P0→P1→P2 solve loop, year evolution)
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

Flat column vector: P[g,t] | W[z,t] | S[z,t] | Chg[s,t] | Dis[s,t] | SOC[s,t] | Flow[l,t] | Slack[z,t] | Dump[z,t]
Total columns = T × (n_gen + 4×n_zones + 3×n_storage + n_links), T=8760

## Objective

min Σ mc[g,t]×P[g,t] + ε×(Chg+Dis) + VOLL×Slack + dump_cost×Dump
Where mc = heat_rate × fuel_price + vom + emission_rate × carbon_price + nox_rate × nox_price + …
dump_cost = max(ε, -min(wind_mc, solar_mc) + ε) — prevents gaming of negative-MC production credits

## Key Constraints

- Energy balance (per zone, per hour): thermal + wind + solar + discharge - charge + net_flow + slack - dump = demand
- Generator bounds: pmin ≤ P[g,t] ≤ pmax × availability[g,t]
- Renewable bounds: 0 ≤ W/S ≤ cf × capacity
- Storage SOC: SOC[t] = SOC[t-1] + η_chg×Chg[t] - Dis[t]/η_dis, cyclic boundary
- Transmission: -TTC ≤ Flow ≤ TTC

## Capacity Evolution (per year, one-pass)

1. Known retirements → 2. Economic retirements (fuel-type-aware thresholds + reliability floor) → 3. Known additions → 4. CCS retrofit screen (existing gas-CC) → 5. Economic new entry → 6. dispatch with RPS as an LP constraint (shadow price feeds next year's entry screen)

Economic retirement uses per-fuel thresholds, now `ScenarioConfig` fields (not hardcoded): coal=1yr, gas_ct=2yr, gas_cc=3yr; coal FOM multiplier 1.3× for regulatory/ESG risk; reliability floor prevents thermal below (peak - firm_clean) × 1.15. RPS is **not** a force-build step — it's an annual LP constraint whose dual is the REC price (see methodology spec §1.4, §5).

CCS retrofit (§5.6): gas-CC units with ≥15 yr life left retrofit when simple payback beats remaining life; capped at 3 GW/yr/ISO, gated on `ccs_retrofit_available_year`.

Storage grows via an economics-based **value stack** (not compound growth): duration-sized arbitrage windows (net of cycling degradation) **plus** resource-adequacy capacity value, paid only in capacity markets via the per-ISO `MARKET_DESIGN` registry (energy-only ERCOT pays none; PJM/NYISO/ISO-NE/CAISO pay net-CONE × ELCC × saturation derate). ELCC rises with duration → tilts entry toward long-duration at high penetration. Build budget diversifies across techs (`STORAGE_TECH_BUILD_SHARE_CAP`); base-year fleet from `storage_deployment`, all later growth endogenous, capped per ISO. Toggles: `storage_capacity_value`, `storage_degradation`. (Methodology spec §5.5.)

## Dispatch & Commitment (per year)

Three LP solves (`runner.py`, `model/commitment.py`): **P0** base-cost (discover run lengths) → **P1** bid-cost (base + amortized startup markup, sets clearing prices) → **P2** optional commitment screen (`commitment_enabled`, default off) that decommits unprofitable CC/CT runs via an IRR hurdle + min-run/min-down + storage-weighted margin discount, with an adequacy backstop. Still pure LP — no MIP.

## Fleet Representation

ERCOT default is **CAMPD per-plant binning** (`use_campd_bins=True`): one LP unit per plant, each split into must-run / committed / economic / peaking tranches forming a rising offer curve (coal take-or-pay + PRB sigmoid passthrough). See `docs/binning-methodology.md`. Other ISOs / `use_campd_bins=False` use legacy equal-width heat-rate bins.

## Naming Conventions

- Python: snake_case. Functions: verb_noun (solve_dispatch, evolve_fleet, load_eia_profiles).
- Single-letter vars only in LP construction: t=hour, g=generator, z=zone, s=storage, with comment.
- Feature branches: phase-N/description. Commits: imperative present tense.

## Testing Pattern

Always test with trivial cases first: 1 gen, 1 zone, 24 hours. Then scale up.

## Reference Docs (in repo)

- `model-methodology-spec.md` — LP formulation, commitment, fleet/offer curves, capacity evolution, outage modelling, scenario architecture (THE SPEC)
- `market-sim-build-plan.md` — phase plan, extraction manifest, directory structure
- `docs/binning-methodology.md` — CAMPD per-plant binning & tranche offer curves (ERCOT default)
- `docs/parameter-citations.md` — every numeric input traced to a primary source
- `docs/multi-iso/` — protocol & status for adding ISOs beyond ERCOT
- `docs/calibration-log.md`, `docs/calibration-session-log.md` — calibration history
- **Code is the source of truth.** When docs and code disagree, fix the docs (run `/sync-docs`). When the methodology is genuinely ambiguous, the spec wins.