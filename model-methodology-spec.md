# Market Simulation Model — Methodology & Build Specification

**Purpose:** Methodology specification for the LP-based electricity market dispatch model. This document governs the model’s mathematical formulation, computational patterns, scenario architecture, and performance requirements. It is the primary reference for how the model works; where this document and the code disagree, the **code is the source of truth** — open a `/sync-docs` pass to reconcile.

**Scope:** Multi-ISO hourly dispatch over a 2026–2050 forecast trajectory, with a historical-backcast mode for calibration. Seven ISOs are registered in `config/iso_configs.py` — ERCOT (6 zones), CAISO (3 zones + WECC import node), PJM (4 zones), MISO (3 zones), SPP (2 zones), NYISO and NEISO — sharing one ISO-agnostic LP. ERCOT is the fully-calibrated reference; the others have topology and plant-to-zone assignment but varying data/backcast maturity (see `docs/multi-iso/`). Parameterized scenario system supporting batch sweeps and single custom runs.

**Forecast vs. backcast.** The model is fundamentally a **forecasting** tool (2026→2050). A *backcast* mode reruns a historical weather year against actuals (EIA-930, CAMPD, eGRID, EIA-923) to calibrate parameters. Several mechanisms — historic outage overlays, F923 delivered fuel prices, plant-specific CEMS emission rates, weather-year pinning — are **backcast/calibration devices only**; forecast runs use the statistical/parametric models. This distinction is called out throughout; do not conflate the two.

**Runtime:** Python 3.11+. Solver: HiGHS via `highspy`. No Pyomo, no PuLP, no scipy.optimize.

> **As-built note (reconciled with code).** This spec was originally written at Phase 0 as a pure-LP, two-ISO design. The model has since grown: an opt-in three-solve **unit-commitment** layer (still LP, not MIP — see §1.6), a **CAMPD per-plant binning** fleet representation with tranche-based rising offer curves (now the ERCOT default — see §3.3), config-driven retirement plus a **CCS-retrofit** pathway (§5), forecast/backcast **outage modelling** (§1.7), endogenous **EAC/REC** attribute credits, hydro monthly energy budgets, and five additional ISO topologies. The sections below reflect the as-built methodology.

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
   + Σ_s Σ_t  ε × Chg[s,t] + (ε − eac_storage) × Dis[s,t]   # tiebreaker, less any storage attribute credit
   + Σ_z Σ_t  VOLL[z] × Slack[z,t]
   + Σ_z Σ_t  dump_cost × Dump[z,t]
```

The wind/solar terms are written as zero-MC here for clarity, but in code each renewable carries its own `mc` (often *negative* once IRA production credits apply — see §1.5/§1.4). Storage discharge carries the tiebreaker `ε` less any exogenous storage attribute credit (`eac_storage`), so a credited storage technology is nudged to deliver rather than sit idle.

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

**Perfect-foresight limitation (known, accepted for now).** The full horizon is solved as one LP, so storage sees the entire year's prices at once and charges/discharges at the globally optimal hours its energy cap permits. A real operator has only ~day-ahead foresight and an imperfect price forecast, so the model is an *upper bound* on realized arbitrage and tends to over-flatten net load — which, in a backcast, can be absorbed into the thermal offer-curve parameters being calibrated against CAMPD. The `SOC ≤ energy_cap` bound keeps this small for the short-duration (≈4 h) li-ion fleet that dominates the 2023 backcast — such a battery physically cannot shift energy across days or seasons, so its only foresight advantage is picking the best in-day hours. The error grows with long-duration storage (12 h+, flow, CAES, iron-air).

Standard ways production-cost models bound storage foresight, cheapest-to-most-faithful:

1. **Daily/weekly SOC cycling caps** — force SOC back to an anchor each day (or cap daily energy throughput). Cheapest: keeps the single-LP structure, just adds rows. Kills cross-day arbitrage but leaves in-day foresight perfect. Good enough while the fleet is short-duration.
2. **Rolling (receding) horizon** — the PLEXOS/GridView/PROMOD default. Solve overlapping windows (e.g. 24–48 h with a look-ahead tail), fix the first day's decisions, carry end-of-window SOC into the next window. Caps foresight at the window length; the look-ahead tail stops the battery draining to zero at the artificial boundary. This is the most realistic option that stays deterministic, and the natural upgrade if/when LDES enters the fleet (the annual cyclic boundary becomes a per-window carried SOC).
3. **Day-ahead + real-time two-settlement** — commit on a forecast over ~24–36 h, then re-dispatch against actuals with limited foresight; captures forecast *error* explicitly. More faithful, more machinery.
4. **Price-taker arbitrage pass** — decouple storage: solve dispatch without storage → take the resulting prices → dispatch storage against them with a realistic foresight window → subtract from net load → re-solve (iterate). This is exactly the heuristic the *forward* new-entry screen already uses (`estimate_storage_revenue`), so the building block exists.
5. **Stochastic/robust optimization** — optimize over multiple price/load scenarios so no single known future can be exploited. The textbook-correct answer to foresight, rarely used in large PCMs because of cost.
6. **Empirical haircut** — accept perfect foresight, then derate storage output/efficiency to a fraction (≈80–90 %) of the theoretical-optimal spread. A pure calibration fudge, but common and cheap.

For this model, the pragmatic path is (1) as a guard once durations lengthen, escalating to (2) if a backcast shows storage materially mis-shaping net load.

**Transmission:**

```
-TTC[l] ≤ Flow[l,t] ≤ TTC[l]    # bidirectional; or use two non-negative variables
```

The topology (zones, load shares, links, TTCs) is per-ISO data in `config/iso_configs.py`; the LP itself is ISO-agnostic and reads `n_zones`, `n_links`, the node–link `incidence` matrix, and per-link `ttc`. Current topologies:

- **ERCOT** — 6 zones (West, Panhandle, North, Houston, South_Central, South) with cited inter-zone TTCs. The reference calibration.
- **CAISO** — 3 in-state zones (NP15, ZP26, SP15) split on Path 15 / Path 26, **plus** a WECC import/export node (see below).
- **PJM** — 4 aggregated zones (West, East, Central, South) rolling up PJM's 20+ transmission zones onto the chronic west→Mid-Atlantic congestion corridors.
- **MISO** — 3 zones (North, Central, South) with the MISO-South contract-path constraint.
- **SPP** — 2 zones (North, South).
- **NYISO, NEISO** — registered single-zone today; real multi-zone topology is future work (`docs/multi-iso/`).

CAISO's WECC import/export node is modeled as **pseudo-generators on a stepped supply curve**:

- Import tranches: 3–4 blocks with increasing marginal cost and MW limits (e.g., PNW hydro cheap/limited, Desert SW CCGT mid, Desert SW CT expensive). These are `P[g,t]` variables assigned to the WECC “zone” with their own cost and capacity.
- Export: allow CAISO to push power to the import node at a cost of zero or small negative (represents dumping surplus solar).
- Aggregate limit: ~12–15 GW import, ~5 GW export. Derive from EIA-930 interchange data.

**Non-negativity:** All dispatch, charge, discharge, slack, dump, SOC ≥ 0. Flows can be negative (bidirectional) or modeled as two non-negative variables per link.

### 1.4 Policy Constraint Extension Point

Some policy parameters are **cost adders** (change the objective vector): carbon price, NOx price, SO2 price. These are handled by the marginal cost assembly — no structural change to the LP.

Some policy parameters are **constraints** (add rows to the LP): NOx emission caps, RPS minimums (minimum % clean generation), potentially others.

**Build rule:** Every policy parameter in the config is tagged `kind: "adder"` or `kind: "constraint"`. The LP builder checks for active constraint-type policies and appends rows.

**RPS (active):** When `rps_enabled` is set and the ISO has an RPS floor for the year, the dispatch LP appends one annual constraint row requiring wind, solar and nuclear generation to reach `rps_target` of total demand:

```
# RPS constraint (annual)
Σ_z Σ_t (W[z,t] + S[z,t]) + Σ_{g∈nuclear} Σ_t P[g,t]
    ≥ rps_target × Σ_z Σ_t Demand[z,t]

Dual on this constraint = REC price ($/MWh), which feeds into
the economic new entry screen as additional clean energy revenue.
```

The constraint creates a shadow price that raises clean revenue and compresses thermal margins, so clean additions and thermal retirements are driven entirely through the economic screens — no force-build in capacity evolution.

```
# Example: NOx cap (extension point, not yet defined)
Σ_g Σ_t nox_rate[g] × P[g,t] ≤ nox_limit                              # annual
```

Other constraint-type policies (NOx caps, etc.) are not yet defined; the extension point in the builder keeps the door open for them.

### 1.5 Emerging Technologies

Emerging generation and storage technologies are a **parameter and data-layer extension**, not an LP formulation change. Every new technology enters as either a `Generator` (thermal dispatch) or a `StorageUnit` (charge/discharge/SOC) reusing the existing LP variable structure. Each technology becomes a new-entry candidate only once the simulation reaches its configured availability year.

#### 1.5.1 Hydrogen Dispatch Model

Hydrogen is **not modeled as storage**. H2 turbines (`hydrogen_ct`, `hydrogen_ccgt`) are thermal generators whose fuel cost is *derived* from renewable electricity economics rather than an exogenous price path:

```
h2_fuel_cost_$/MMBtu = min(wind_LCOE, solar_LCOE) / η_electrolyzer / 3.412
```

where 3.412 MMBtu = 1 MWh. The `min()` picks whichever renewable is cheapest in that ISO-year; dividing by the electrolyzer efficiency converts electricity to hydrogen; dividing by 3.412 converts $/MWh to $/MMBtu. Electrolyzer efficiency is a Tier 2 parameter that improves over time (linear interpolation between the 2026, 2035 and 2045 milestone years). This formulation:

- tracks Wright's-Law cost declines in renewables automatically — cheaper renewables mean cheaper hydrogen;
- needs no exogenous hydrogen price path;
- avoids circularity — the model never prices its own fuel.

H2 turbines then dispatch on `heat_rate × h2_fuel_cost` like any thermal unit. Direct CO2 emissions are zero (green hydrogen); NOx is non-zero because hydrogen burns hot. The IRA §45V clean hydrogen production tax credit ($3/kg ≈ $26/MMBtu) is applied as a fuel-cost reduction in the new-entry LCOE screen and expires after `ira_expiry_year`.

#### 1.5.2 CCUS Dispatch Model

Carbon capture (`gas_cc_ccs`) is a **variant of the base gas CC plant**: it burns the same natural gas but carries a higher heat rate (parasitic capture load), a higher VOM (solvent costs), a reduced emission rate (capture rate applied), and a transport+storage cost for captured CO2. The marginal cost is:

```
mc = base_heat_rate × heat_rate_penalty × gas_price
   + base_vom + vom_adder
   + base_co2_rate × (1 − capture_rate) × carbon_price     # residual emissions
   + base_co2_rate × capture_rate × co2_transport_storage   # captured CO2 disposal
```

The captured-CO2 disposal term is a constant $/MWh and folds into the unit's VOM; the residual-emissions term is ordinary `emission_rate × carbon_price`, so standard marginal-cost assembly reproduces the formula with no special-casing. CCUS becomes **more competitive as carbon prices rise** — the residual term shrinks relative to the full carbon cost an unabated plant pays — and the model finds the carbon-price crossover endogenously. The IRA §45Q credit ($85/tCO2 stored) enters the new-entry LCOE screen as a variable-cost offset and expires after `ira_expiry_year`.

#### 1.5.3 Enhanced Geothermal

Enhanced geothermal systems (`geothermal`, EGS) enter as zero-fuel dispatchable baseload generators with a high capacity factor (~90%). They are **not intermittent** — they do not follow wind/solar CF profiles. They can provide flexibility, turning down to a `pmin` of ~20% of rated capacity. A steep learning curve is assumed (analogous to early solar). Geothermal earns the same zero-emission production tax credit as wind.

#### 1.5.4 Offshore Wind

Offshore wind (`offshore_wind`) is a **separate renewable category** from onshore wind: higher and less variable capacity factors, higher costs, and distinct zone eligibility. By default it is a candidate only in CAISO (Pacific-coast floating); the Gulf-coast ERCOT potential is left as a future sensitivity. It is modeled as a **zero-marginal-cost `Generator`** (Option A), rather than as a new LP variable class — the LP dispatches it like any other generator and curtailment falls out of the capacity bound. This keeps the LP structure unchanged.

Offshore wind capacity factors are derived from the onshore wind profile for the same ISO by applying a physical smoothing window (default 6 hours, reflecting reduced ocean gustiness), a minimum CF floor (default 8%, reflecting persistent offshore resource), and rescaling to the target annual-average CF. This preserves the real temporal patterns (diurnal, synoptic, seasonal) from the EIA-930 data while producing a less variable, higher-average profile that matches offshore wind's physical characteristics. The derived profile is injected into the generator's hourly availability array, so dispatch varies realistically across hours.

#### 1.5.5 Additional Storage Durations

Three long-duration storage technologies — 12-hour lithium-ion, vanadium-redox flow batteries and adiabatic compressed-air — are added to the storage technology menu. They use the **same LP formulation** as the existing storage units (`power_cap`, `energy_cap`, `eta_chg`, `eta_dis`); only their economics differ, which drives different dispatch patterns.

### 1.6 Unit Commitment — Three-Solve LP Heuristic

The original spec said "no unit commitment." That changed: pure merit-order LP left fast-cycling units (notably ERCOT gas CT) badly under-dispatched because a single LP solve has no notion of start-up cost or minimum run length. The model now has an **opt-in commitment layer** (`model/commitment.py`, enabled by `ScenarioConfig.commitment_enabled`, default `False`). It stays **pure LP — there is no MIP and no binary variables**; commitment is a heuristic screen applied *between* LP solves by zeroing a unit's availability in hours it is decommitted, then re-solving. Three solves per year:

- **P0 (base):** solve with base marginal cost `mc_base = fuel + VOM + carbon + NOx` (no start-up markup). Measure each unit's realized run lengths by month.
- **P1 (bid):** solve with `mc_bid = mc_base + start-up markup`, where the per-unit monthly markup amortizes `start_up_cost / avg_run_length` (ST_GAS spreads its start-ups across May–Sep). Clearing prices now embed cycling cost.
- **P2 (commitment, when enabled):** screen CC/CT units for profitable *runs* of in-merit hours (`P1_price[zone] − mc_base > 0`), then keep a run committed only if it clears all of:
  - a **start-up IRR hurdle** — the run's weighted margin exceeds `start_up_per_MW × (1 + commitment_irr_hurdle)` (default 7%);
  - **min-run / min-down** filters (drop runs shorter than the minimum; merge runs separated by less than the minimum down-time);
  - a **storage-weighted margin discount** — in hours when storage is net-charging the zone, the margin is discounted so a unit is not kept on merely to feed speculative battery charging, with a deep charging trough breaking the run.

  Coal is either pinned to its P1 dispatch (legacy/unscreened bins) or screened with a long (≈36 h) minimum run. An **adequacy backstop** restores decommitted units to their P1 fractions in any zone-hour where the screen would otherwise make P2 unable to reproduce P1 thermal output — commitment can never introduce unserved energy.

Commitment is off by default and used primarily for ERCOT calibration; the screen reads *base* MC (not bid MC) so start-up cost is not double-counted in the retirement/new-entry economics that consume these prices.

### 1.7 Outage & Availability Modelling — Forecast vs. Backcast

A unit's hourly `availability[g,t]` multiplies its `Pmax`. Two regimes:

**Forecast (statistical — the default).** Availability `= 1 − WEFOR(age) − DERATE(age) − POF(shoulder only)`, from the per-plant-group `THERMAL_AVAILABILITY` table (`config/constants.py`):
- **WEFOR** (forced-outage rate) is flat year-round and escalates with age past an onset year.
- **Planned outages (POF)** are concentrated into the spring/autumn **shoulder months** (`_CC_SHOULDER_MONTHS = {3,4,5,10,11}`) — the maintenance lull between winter and summer peaks. In the **summer peak** (`{6,7,8,9}`) planned outages are removed and only a fraction (`_SUMMER_WEFOR_SHARE = 0.30`) of the forced-outage rate applies, with the displaced outage energy redistributed into the shoulder, so firm capacity is available for the load peak.
- **Seasonal capacity derate** (ambient): gas turbines lose ~10–12.5% of capacity in summer.
- Nuclear uses a monthly capacity-factor shape (NRC PRIS refuelling pattern), refuelling concentrated in spring/autumn.

> **Roadmap (not yet built — do not document as current):** replace the flat shoulder-POF heuristic with a **historically-derived monthly maintenance profile** — the *shape and magnitude* of spring/autumn maintenance learned from historic outage data (CAMPD/GADS) and applied in **forecast** mode, rather than a single flat POF smeared across the five shoulder months. This is forecast-mode shaping (not pinned to any one backcast year) and distinct from the backcast overlay below.

**Backcast (historic overlay — calibration only).** When a backcast config sets `outage_source == "historic"`, `data/outages.py` overlays *actual* sustained outage windows (CAMPD-derived, coal/CC plants, ≥48 h CF<5% gaps) onto the model's fixed 8760-hour clock, plus a unit-level derate from the ERCOT unit-outage extract and CAMPD partial-outage (CF-ceiling) plateaus. The statistical POF for overlaid groups is dropped (`coal_drop_pof`) to avoid double-counting. **Forecast runs never use this overlay** — it exists to reproduce a specific historical year for calibration, and degrades gracefully to the statistical model when the extract is absent.

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

### 3.3 Fleet Representation & Offer Curves

The thermal fleet can be built two ways; the LP and `FleetArrays` structure are identical either way (each tranche/bin is just another row `g`).

**Legacy equal-width heat-rate bins.** EIA-860 generators aggregated into a small number of representative heat-rate bins per fuel — the original method, still used for non-ERCOT ISOs and when `use_campd_bins=False`.

**CAMPD per-plant binning (ERCOT default, `use_campd_bins=True`).** Documented in full in `docs/binning-methodology.md`. Built from EPA CAMPD gross generation (2023–24) cross-referenced with eGRID net generation and EIA-860 characteristics. Each plant gets **its own LP unit** (`inputs/custom-bin-assignments.csv`), classified into one of six dispatched groups (CC_CHP, CC_REGULAR, CT_CHP, CT_PEAKER, GAS_STEAM, COAL) plus non-dispatchable OTHER. Each bin is split into **tranches** that form a *rising offer curve* rather than a single flat marginal cost:

- **Must-Run (MR%)** — sunk-fuel coal floor or CHP behind-the-meter steam (the latter is removed from the LP and reconstructed post-dispatch by `compute_must_run_emissions()`).
- **Committed (MC%)** — minimum stable load; the tranche the commitment screen (§1.6) acts on.
- **Economic (ECON%)** — normal in-merit dispatch.
- **Peaking (PEAK%)** — duct-firing / steep cost, `pmin=0`, never screened out.

Two further refinements wired into marginal-cost assembly:
- **Coal take-or-pay tranches** — three slices at different fuel passthroughs (e.g. VOM-only / partial / full fuel cost), so a coal unit's offer rises with quantity.
- **PRB sigmoid passthrough** — Powder-River-Basin coal discounts its bid as a smooth (sigmoid) function of the gas price, with a tiered variant for load-following plants.

**Per-plant offer curves.** The tranche split and band heat rates default to per-*group* values, but an optional per-plant override sheet (`inputs/plant-tranche-config.csv`, `ScenarioConfig.plant_tranche_config_path`, off by default) lets each listed plant carry its own **five-slice rising offer curve** — Must-Run / Committed / Econ-Low / Econ-High / Peaking shares plus per-slice heat-rate multipliers — bypassing the group defaults. This is the calibration lever for shaping an individual flagship plant's dispatch without disturbing its class total (`docs/binning-methodology.md`). A companion flag `cc_peaking_per_plant` moves the duct-burner peak band's CF onset for selected F-class CCs.

When a bin maps to a single physical plant, its CO2/NOx can be overridden with **CAMPD CEMS plant-specific emission rates** (backcast accuracy) instead of the fuel-class default.

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
    4. Apply CCS retrofit screen to existing gas-CC units (§5.6)
    5. Apply known additions (EIA-860 under construction, signed PPAs)
    6. Apply economic new entry screen (LCOE vs expected revenue, including
       the prior year's REC price as clean-energy revenue)
    7. Assemble updated fleet → run dispatch LP (with RPS constraint) → cache results
```

The capacity-evolution mechanisms are steps 2–6. The RPS is no longer a force-build step: it is enforced as an LP constraint in the dispatch (step 7), and its shadow price feeds back into the economic new-entry screen the following year. Known retirements and known additions (the EIA-860 near-term pipeline) remain deterministic — these are committed projects, not modeled decisions. After the data horizon (~2030), the model is fully economics-driven.

### 5.2 Economic Retirement

A unit retires if its **net revenue < going-forward cost** for N consecutive years, where N varies by fuel type:

- **Coal:** 1 consecutive loss year (faster exit — reflects regulatory risk and carbon liability)
- **Gas CT:** 2 consecutive loss years
- **Gas CC:** 3 consecutive loss years (most patient — higher capital sunk, longer expected life)

Revenue and cost definitions:

- Net revenue = `Σ_t price[z,t] × dispatch[g,t]` plus attribute payments (`max(exogenous EAC, prior-year RPS/REC shadow price) × annual_gen`), from the prior year’s LP results. A profitable year resets the unit's consecutive-loss counter to zero.
- Going-forward cost = fixed O&M × FOM multiplier (not capital — sunk cost)
- FOM multipliers: coal = 1.3× (captures regulatory risk, carbon liability, ESG pressure), gas = 1.0×
- Retirement ordering: within each fuel class, least efficient (highest heat rate) retires first

These thresholds and multipliers are no longer hardcoded — they are `ScenarioConfig` fields (`retirement_years_{coal,gas_ct,gas_cc}` = 1/2/3, `retirement_fom_multiplier_{coal,gas_ct,gas_cc}` = 1.3/1.0/1.0, `retirement_reserve_margin` = 0.15), so retirement aggressiveness is a Tier-1 sensitivity lever. The defaults above are the as-built values.

**Reliability floor:** Thermal capacity cannot fall below `(peak_demand - firm_clean) × (1 + reserve_margin)`, where `reserve_margin` defaults to 15% (Tier 2 parameter) and `firm_clean = nuclear + hydro capacity`. If economic retirements would breach the floor, the most efficient units are retained.

**Design note:** Sigmoid retirement was considered and rejected in favor of fully economic retirement with fuel-type-aware thresholds. The economic approach is more transparent — every retirement is traceable to a revenue shortfall — and avoids the arbitrary sigmoid midpoint parameter. The coal FOM multiplier (1.3×) captures the non-economic pressures (regulatory risk, ESG) that the sigmoid was designed to model.

### 5.3 Economic New Entry

Screen by technology: if `expected_revenue > LCOE`, the technology is economic for entry.

- Expected revenue estimated from prior year’s price duration curve
- LCOE from technology cost assumptions with learning curves (Tier 2 parameters)
- IRA credits reduce LCOE (PTC for wind, ITC for solar/storage — Tier 1 parameters)
- Annual build rate capped per technology (e.g., ERCOT ~12 GW/yr queue throughput)
- Clean technologies (wind, solar) earn the prior year's REC price — the RPS constraint's shadow price — as additional expected revenue, so a binding RPS pulls more of them across the LCOE hurdle
- Technology priority: ranked by revenue-minus-LCOE margin, highest first

**Technology availability gating.** The candidate set is not fixed. The classic four technologies (wind, solar, gas CC, nuclear) are always eligible, but each emerging technology (hydrogen turbines, CCUS, enhanced geothermal, offshore wind — see §1.5) joins the candidate pool only once the simulation year reaches its configured availability year (`h2_available_year`, `ccs_available_year`, `egs_available_year`, `offshore_wind_available_year`). Offshore wind additionally enters only in ISOs listed in `offshore_wind_eligible_isos`. The screening order is therefore: (1) build the year's eligible candidate set, (2) compute each candidate's LCOE and margin, (3) rank and build subject to queue caps. Hydrogen turbines and CCUS share the `gas_cc` per-tech queue cap (shared gas-turbine supply chain); geothermal and offshore wind have their own per-tech caps.

### 5.4 Known Pipeline

EIA-860 provides: units under construction (with expected online date), announced retirements (with expected date). These are deterministic — they happen regardless of economics. Transition point from known to modeled: ~2030 for near-term pipeline, model takes over for years beyond the data horizon.

### 5.5 Storage New Entry

Storage enters via economics-based screening on a **value stack**, compared
against annualized cost (capex × CRF + FOM, with IRA ITC and a Wright's-Law
learning curve):

**1. Energy arbitrage** over **duration-sized windows**, net of cycling
degradation. The year is split into windows of `block_days = max(1,
ceil(duration_hr / 12))` days; in each window the unit charges its cheapest
`duration_hr` hours and discharges its dearest, for one cycle per window:

```
Revenue_energy = Σ_windows max(0, discharge_avg - charge_avg/RTE - degr) × duration
```

The window is sized so a full charge and full discharge never overlap
(`2 × duration ≤ 24 × block_days`). This matters: a **fixed 24-hour window
collapses the spread to zero for any duration at or beyond a day**, so
long-duration storage (iron-air, flow, CAES) would screen as worthless and
could never build. The duration-sized window lets multi-day assets realize
multi-day arbitrage. `degr` is a per-MWh cycling-degradation cost
(energy-capex slice over rated cycle life), which penalizes high-cycling
short-duration storage more than long-life chemistries.

**2. Capacity (resource-adequacy) value**, paid **only in capacity markets**.
Governed by a per-ISO `MarketDesign` switch (`MARKET_DESIGN`): energy-only
ERCOT pays nothing here (scarcity already flows through the ORDC/VOLL energy
price), while PJM/NYISO/ISO-NE and CAISO's RA pay
`net_cone × ELCC(duration) × (1 − penetration)^k`. The ELCC capacity credit
**rises with duration**; the saturation derate **falls as storage approaches
the deployment ceiling**. Together they make short-duration capacity value
collapse at high penetration while long-duration retains its firm credit —
the mechanism that tilts new entry toward longer durations as storage
saturates. The stack is toggleable via `config.storage_capacity_value` and
`config.storage_degradation`.

Profitable techs are ranked by total margin (energy + capacity − cost) and
built in merit order, but no single tech may take more than
`STORAGE_TECH_BUILD_SHARE_CAP` of one year's budget, so the build diversifies
across durations rather than the top-margin tech monopolizing it. Builds are
attributed to each tech's own learning curve (li-ion durations share one
curve; iron-air/flow/CAES each have their own). Subject to annual build cap
and cumulative ceiling per ISO (both now defined for ERCOT, CAISO, PJM,
NYISO, ISO-NE). Base-year fleet set by `storage_deployment`; all subsequent
growth is endogenous.

### 5.6 CCS Retrofit Screen

Beyond *new* `gas_cc_ccs` entry (§1.5.2), existing gas-CC units can be **retrofitted** with post-combustion capture (`model/capacity.py`, gated on `ccs_retrofit_available_year`, default 2028). Each year, every gas-CC unit with at least `ccs_retrofit_min_remaining_life` (15) years of useful life left is screened on **simple payback**: annual savings = carbon avoided + EAC/45Q revenue − margin loss from the higher heat rate (`ccs_retrofit_hr_penalty` = 12%) − the capture VOM adder (`ccs_retrofit_vom_adder` = $8/MWh). A unit retrofits when payback is shorter than its remaining life. Retrofit capex (`ccs_retrofit_capex_kw` ≈ $900/kW) follows the same Wright's-Law learning curve as new CCS, the emission rate drops by `ccs_retrofit_capture_rate` (90%), and total retrofits are capped at `ccs_retrofit_max_gw_per_year` (3 GW/yr) per ISO. This is a distinct capacity-evolution mechanism from retirement and new entry — an existing asset changes its characteristics in place.

### 5.7 Hydro Energy Budgets

Hydro is not a free-running thermal unit. When `hydro_monthly_energy` is supplied, the dispatch LP adds, per hydro generator per month, a two-sided **energy-budget** constraint `hydro_min ≤ Σ_{t∈month} P[g,t] ≤ hydro_max` (plus an optional run-of-river minimum-flow floor). The unit chooses *when* within the month to generate, not *how much* in total — an inter-temporal coupling like storage SOC, but on a monthly horizon.

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

These remain firm:

- **No MIP.** Still pure LP — no binary variables. The commitment layer (§1.6) is a *heuristic screen between LP solves*, not a mixed-integer program; fractional dispatch within a committed unit is acceptable.
- No ramp constraints. Flag as future enhancement.
- No ORDC / operating reserve demand curve. Scarcity shows up via VOLL.
- No separate pricing model. Prices are LP duals. Period.
- No representative weeks or days. Full 8760 always.
- No convergence iteration in capacity evolution. One pass per year.
- No web framework or API server. CLI + YAML + Parquet files.

Originally listed here but **since built** (kept as LP, no MIP):

- ~~No unit commitment~~ → opt-in three-solve commitment heuristic, §1.6 (default off).
- ~~No stochastic outages, deterministic derate only~~ → forecast still uses statistical/deterministic derate; backcast adds a *historic* CAMPD outage overlay for calibration, §1.7 (forecast runs do not use it).