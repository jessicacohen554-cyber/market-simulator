# 1. Architecture

This page describes the system as a whole: the package layout, the end-to-end
run pipeline, the multi-year solve loop, and the non-negotiable design rules the
code enforces.

## 1.1 Package layout

```
src/market_sim/
├── __main__.py          # `python -m market_sim` → runner.main()
├── runner.py            # orchestrator: run_scenario_iso, run_sweep, main()
├── ensemble.py          # weather-year ensemble (distribution over weather draws)
├── config/
│   ├── scenarios.py     # ScenarioConfig dataclass + YAML loading (the run spec)
│   ├── constants.py     # ~3,900 lines of cited physical/economic constants
│   ├── iso_configs.py   # per-ISO topology (zones, links, interface limits)
│   ├── paths.py         # central on-disk path registry + EIA-860 vintage seam
│   └── plant_taxonomy.py# canonical fuel/class/coal-rank taxonomy
├── data/                # loaders: Pydantic objects + numpy arrays from disk
│   ├── fleet.py         # Generator, FleetArrays, CAMPD binning, tranche curves
│   ├── eia930/          # EIA-930 loaders package (frames/demand/zonal_shares/envelopes/weather/actuals)
│   ├── eia_loader.py    # facade → eia930 (aliases the historical import path; W-D2 split)
│   ├── fuel.py          # gas/coal/oil/H2 delivered prices
│   ├── renewables.py    # wind/solar hourly capacity factors
│   ├── outages.py       # historic availability overlays (backcast)
│   ├── hydro.py         # hydro monthly energy budgets
│   ├── hydrogen.py      # derived H2 fuel economics
│   ├── campd.py         # EPA CAMPD hourly CEMS (emissions, net-gen benchmark)
│   ├── egrid.py         # eGRID + CAMPD plant CO2 rates
│   ├── zone_assignment.py # eGRID geography → model zone
│   ├── eia923.py        # EIA-923 monthly fuel cost & generation
│   ├── cod_ramp.py      # commercial-operation-date vintage masking
│   ├── neighbor_price.py# forecast-grade neighbor reference prices (seams)
│   ├── ownership.py / ownership_config.py # generator → parent company
├── model/               # the LP core
│   ├── dispatch.py      # variable layout, constraints, objective, HiGHS, duals
│   ├── capacity.py      # one-pass capacity evolution (6 steps)
│   ├── commitment.py    # P0→P1→P2 unit-commitment screen
│   ├── transmission.py  # pipe-and-bubble network, priced import/export nodes
│   ├── storage.py       # storage units, SOC dynamics, value-stack entry
│   └── ancillary.py     # ERCOT AS revenue for capacity economics
├── policy/              # exogenous policy layers
│   ├── ira.py           # IRA PTC/ITC, §45V hydrogen, §45Q CCUS
│   ├── rps.py           # RPS target lookup (LP constraint, dual = REC price)
│   ├── carbon.py        # carbon price resolution (flat/state/trajectory)
│   ├── eac.py           # environmental attribute credits → MC reduction
│   └── constraints.py   # policy-constraint assembly (extension point)
└── results/             # outputs
    ├── cache.py         # one Parquet per scenario-year, check-before-run
    ├── outputs.py       # FleetContext + DispatchResult serialization
    ├── emissions.py     # CO2/NOx from dispatch; CHP must-run reconstruction
    ├── export.py        # 25-year → compact annual-summary JSON
    ├── calibration.py   # backcast diagnostics vs EIA actuals
    ├── plant_financials.py # bin→plant P&L disaggregation, company rollup
    ├── rcpf.py          # NYISO reserve-constraint penalty overlay
    └── scarcity.py      # ERCOT ORDC + PJM reserve scarcity pricing
```

The dependency direction is strictly downward: `runner` → `model` + `data` +
`policy` + `results` → `config`. Nothing in `config` imports upward.

## 1.2 The stack

From `pyproject.toml`:

| Dependency | Role |
|------------|------|
| `highspy` (≥1.7) | HiGHS LP solver — the only solver. **Pure LP, no MIP.** |
| `numpy` (≥1.26) | array computing; all hour iteration is vectorized |
| `scipy` (≥1.12) | `scipy.sparse` — CSR/CSC/COO/kron constraint assembly |
| `pandas` (≥2.1) | tabular I/O |
| `pyarrow` (≥14.0) | Parquet results persistence |
| `pydantic` (≥2.5) | config + topology validation |
| `pyyaml` (≥6.0) | scenario YAML files |

`pyproject.toml` + `uv.lock` are the dependency source of truth; `requirements.txt`
is a generated pip fallback. **Forbidden** (per project rules): Pyomo, PuLP,
scipy.optimize, Numba — the LP is assembled as a CSC matrix and handed directly
to HiGHS.

## 1.3 The end-to-end pipeline

```
ScenarioConfig (YAML → pydantic)
        │
        ▼
get_iso_config(iso)  ── zones, links, interface limits, VOLL
        │
        ▼
weather-fixed inputs (loaded ONCE per run)
   • base zonal demand (EIA-930, allocated to zones by load share)
   • wind/solar CF + capacity (per zone, per hour)
   • transmission incidence matrix, TTC array, interface groups
   • CAMPD operational bins (if use_campd_bins)
   • priced import/export generators (CAISO/PJM seams)
        │
        ▼
for year in START_YEAR .. END_YEAR  (SEQUENTIAL — never parallel):
   ┌───────────────────────────────────────────────┐
   │ 1. build (year 1) or evolve (years 2+) the fleet         │
   │ 2. generators_to_fleet_arrays() → FleetArrays (SoA)      │
   │ 3. assemble_mc(): per-(g,t) marginal cost vector         │
   │ 4. cache check → load_result() and skip if present       │
   │ 5. P0 solve  (base MC; discover run lengths)             │
   │ 6. P1 solve  (base + startup markup; SETS PRICES)        │
   │ 7. P2 solve  (optional commitment screen; default off)   │
   │ 8. post-solve: CHP must-run, ORDC scarcity overlay       │
   │ 9. save_result() Parquet; build prior_results feedback   │
   └──────────────────────────────────────────────┘
        │  (prices → next year's capacity economics)
        ▼
results/<iso>/<cache_key>/year_<year>.parquet (+ _p1 if commitment)
        │
        ▼
optional: calibration report (backcast) / annual JSON / ensemble dist
```

Steps 1–9 live in `runner.run_scenario_iso()`. The LP itself (steps 5–7) is
`model.dispatch`. Capacity evolution (step 1, years 2+) is `model.capacity.evolve_fleet()`.

### Struct-of-arrays boundary

A hard architectural seam: rich Pydantic `Generator` objects exist only during
fleet construction. Before the LP is built, the fleet is flattened into
`FleetArrays` — parallel numpy arrays (`pmax`, `pmin`, `heat_rate`, `vom`,
`emission_rate`, `zone_idx`, `fuel_type_idx`, `availability[n_gen,T]`, …). **The
LP builder touches only arrays and scalars**, never Pydantic objects. This is
what makes the matrix assembly vectorizable.

## 1.4 The multi-year feedback loop

Each solved year produces a `prior_results` dict consumed by the next year's
`evolve_fleet()`:

| Carried forward | Used by |
|-----------------|---------|
| zonal prices (`econ_prices`, scarcity-adjusted) | economic retirement, new-entry, CCS-retrofit screens |
| RPS shadow price (REC price) | new-entry revenue for clean techs |
| peak demand | reserve-margin adequacy backstop |
| dispatch result, marginal cost (`mc_cost`) | inframarginal energy-margin retirement screen |
| wind/solar/storage capacity | next year's dispatch variable bounds |
| global cumulative deployment | Wright's-Law learning curves on capex |

Years run strictly **sequentially within one invocation** — a single year's
8760-hour LP already uses several GB of RAM, so concurrent year solves would OOM.
Independent *invocations* (different ISOs/configs with separate `--out-dir`) are
the parallelism unit.

## 1.5 Forecast vs backcast

The mode is the explicit `ScenarioConfig.mode` field (`"forecast"` default, or
`"backcast"`) — **never inferred** from other parameters. A forecast with a pinned
gas price is still a forecast.

| Aspect | forecast | backcast |
|--------|----------|----------|
| renewable capacity | forecast trajectory / Wright's Law | that year's EIA-860 actuals |
| renewable profiles | statistical / forecast HSL | measured EIA-930 / measured HSL |
| fossil retirements | economics (`apply_economic_retirements`) | EIA-860 announced + COD ramp |
| planned additions | injected from EIA-860 pipeline | not injected (snapshot is fixed) |
| fuel prices | Henry Hub trajectory + basis | EIA-923 monthly receipts overlay |
| outages | statistical WEFOR/POF | measured CAMPD outage windows |
| hydro | climatology × wet/normal/dry | measured EIA-930 monthly |
| nuclear CF | static seasonal pattern | measured per-(ISO,year) |

Historic overlays (CAMPD outage windows, F923 delivered fuel, plant-specific CEMS
emission rates, weather-year pinning) are **backcast/calibration only**. The
admissibility rule the code follows: a measured input is allowed only if it is a
*reproducible physical/market input* that could be regenerated for a forward year
and would respond to changed conditions — never a measured *outcome* fed back to
force the fit.

## 1.6 Design rules the code enforces

These are visible directly in the source and are worth internalizing before
reading the subsystem pages:

1. **Prices are LP duals** on the energy-balance rows. There is no separate
   pricing model. (`model/dispatch.py`)
2. **No Python loops over hours in LP construction.** Hour replication is
   `scipy.sparse.kron(eye(T), per_hour_block)`; indices are built with
   `np.arange`/`np.tile`/`np.repeat` and raveled.
3. **Renewables are decision variables** (`W[z,t]`, `S[z,t]`) on the LHS of the
   energy balance with MC≈0 and upper bound `CF × capacity` — never netted from
   demand.
4. **Full 8760 hours always** — no representative days/weeks.
5. **Struct-of-arrays before LP construction** (the FleetArrays seam above).
6. **One Parquet per scenario-year**, check-before-run caching (`results/cache.py`).
7. **One-pass capacity evolution** — no within-year convergence iteration.
8. **Storage tiebreaker ε = 0.001 $/MWh** on charge+discharge prevents degeneracy.
9. Every public function and module carries a docstring.

## 1.7 The LP at a glance

One annual program per ISO-year. Flat column vector, per-hour block repeated T=8760
times:

```
P[g,t] | W[z,t] | S[z,t] | Chg[s,t] | Dis[s,t] | SOC[s,t] | Flow[l,t] | Slack[z,t] | Dump[z,t]
   [ + R[r,t] | ORDC[k,t]  when reserve co-optimization is enabled ]
```

Objective (minimize):

```
Σ mc[g,t]·P + wind_mc·W + solar_mc·S + ε·(Chg+Dis) + dis_cost·Dis
  + VOLL·Slack + dump_cost·Dump + ordc_penalty·ORDC
```

Core constraints: per-zone hourly energy balance (equality; its dual is the LMP),
generator bounds `pmin ≤ P ≤ pmax·availability`, renewable bounds `0 ≤ W/S ≤ cf·cap`,
cyclic storage SOC dynamics, transmission `-TTC ≤ Flow ≤ TTC`, optional hydro
monthly-energy budgets, optional RPS, optional reserve co-optimization.

The full formulation is in [`02-lp-dispatch.md`](02-lp-dispatch.md).
