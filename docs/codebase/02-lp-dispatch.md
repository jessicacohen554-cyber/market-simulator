# 2. The LP Dispatch Core

Source: `src/market_sim/model/dispatch.py` (~2,400 lines). This is the heart of
the model — a single annual 8760-hour economic-dispatch linear program, assembled
once as a sparse CSC matrix and solved by HiGHS. Energy prices are recovered as
the duals on the energy-balance constraint rows.

## 2.1 Variable layout

`VariableLayout` (lines 28–189) is an immutable map from decision variables to
flat LP column indices. Columns are **hour-major**: each hour `t` owns a
contiguous block of `vars_per_hour` columns, and the block is laid out in this
order:

| Block | Count | Symbol | Meaning |
|-------|-------|--------|---------|
| thermal | `n_gen` | `P[g,t]` | thermal generation |
| wind | `n_zones` | `W[z,t]` | wind dispatched (decision var, not netted) |
| solar | `n_zones` | `S[z,t]` | solar dispatched |
| storage charge | `n_storage` | `Chg[s,t]` | storage charging |
| storage discharge | `n_storage` | `Dis[s,t]` | storage discharging |
| storage SOC | `n_storage` | `SOC[s,t]` | state of charge |
| flow | `n_links` | `Flow[l,t]` | transmission flow (signed) |
| load slack | `n_zones` | `Slack[z,t]` | unserved energy (priced at VOLL) |
| dump | `n_zones` | `Dump[z,t]` | overgeneration / curtailment |
| reserve | `n_reserve` | `R[r,t]` | upward reserve (co-opt only) |
| ORDC shortfall | `n_ordc_steps` | `ORDC[k,t]` | reserve-demand-curve steps (co-opt only) |

`total_columns = vars_per_hour × T`. Accessor methods translate semantic indices
to column indices: `p_col(g,t)`, `w_col(z,t)`, `s_col(z,t)`, `chg_col(s,t)`,
`dis_col(s,t)`, `soc_col(s,t)`, `flow_col(ln,t)`, `slack_col(z,t)`,
`dump_col(z,t)`, `r_col(g,t)`, `ordc_col(k,t)`, plus `p_cols_gen(g)` for the full
T-length slice of one generator's columns.

When reserve co-optimization is off (the default for most ISOs), `n_reserve` and
`n_ordc_steps` are 0 and the LP is byte-identical to an energy-only program.

## 2.2 Vectorized constraint assembly

The cardinal rule (no Python loop over hours) is implemented through one pattern:
build a single per-hour sparse block, then replicate it across time with
`scipy.sparse.kron(sp.eye(T), per_hour)`. The `eye(T)` Kronecker factor places
each hour's block at column offset `t × vars_per_hour`. For unit-major blocks
(storage dynamics), the row/column indices are built with `np.arange`/broadcast
and handed to a single `coo_matrix` constructor.

`build_constraints(...)` (line 1051) stacks the row families below, in order, into
one CSR matrix with `row_lower`/`row_upper` bound vectors.

### Energy balance — rows `[0 : n_zones·T]`, equality

Per zone `z`, hour `t`:

```
Σ_{g∈z} P[g,t] + W[z,t] + S[z,t]
   − Σ_{s∈z} Chg[s,t] + Σ_{s∈z} Dis[s,t]
   + Σ_l incidence[z,l]·Flow[l,t]
   + Slack[z,t] − Dump[z,t]  =  Demand[z,t]
```

Built as `sp.kron(sp.eye(T), per_hour)` where the per-hour block horizontally
stacks `[zone_gen | I | I | −zone_storage | zone_storage | 0 | flow_block | I | −I | 0 | 0]`.
`zone_gen` is an `(n_zones, n_gen)` membership incidence (`_build_zone_gen_map`),
`zone_storage` an `(n_zones, n_storage)` membership map. The SOC columns get a
zero block here — SOC dynamics are separate rows. Row index for `(z,t)` is
`t·n_zones + z`; demand RHS is `(T, n_zones).T` raveled.

**These row duals are the locational marginal prices.** `LMP[z,t]` = dual of row
`t·n_zones + z`.

### Storage SOC dynamics — rows `[n_zones·T : +n_storage·T]`, equality

Unit-major (`row = s·T + t`):

```
SOC[s,t] − SOC[s,t−1] − η_chg·Chg[s,t] + Dis[s,t]/η_dis = 0     (t = 1..T−1)
SOC[s,0] − SOC[s,T−1] − η_chg·Chg[s,0] + Dis[s,0]/η_dis = 0     (cyclic)
```

Cyclic boundary ties end-of-year SOC to hour 0. The entire block is one
`coo_matrix` built from `(n_storage, T)` broadcast index arrays — no per-unit,
per-hour loop.

### Optional row families (appended in order)

| Family | Builder | Rows | Constraint |
|--------|---------|------|------------|
| Daily-cycle anchor | `_build_storage_daily_cycle_rows` | `n_storage × (n_days−1)` | `SOC[s, day_start] − SOC[s,0] = 0` (bounds arbitrage to within-day) |
| Aggregate interface | `_build_interface_rows` | `n_groups × T` | `Σ signed link flows ≤ cap` (static or per-hour seasonal TTC; one-sided or symmetric) |
| Hydro monthly | `_build_hydro_rows` | `n_hydro × 12` | `monthly_min ≤ Σ_{t∈month} P[hydro,t] ≤ monthly_energy` |
| Priced import node | `_build_import_node_rows` | `12` | `monthly_lo ≤ net import ≤ monthly_hi` |
| RPS | `_build_rps_row` | `1` | `Σ(W + S + nuclear P) ≥ rps_target · Σ demand`; dual = REC price |
| Reserve co-opt | `_build_reserve_rows` | varies | shared-headroom + balance + supply-cap rows (see §2.5) |

Every one of these is assembled with broadcast index arrays and a single sparse
constructor — month indices broadcast to `(n_units, T)` then raveled, group
indices via `np.flatnonzero`, etc.

## 2.3 The objective

`build_cost_vector(...)` (line 192) writes one flat cost array over all columns:

| Column block | Coefficient |
|--------------|-------------|
| `P[g,t]` | `mc[g,t]` (hourly marginal cost) |
| `W[z,t]` | `wind_mc[z,t]` |
| `S[z,t]` | `solar_mc[z,t]` |
| `Chg[s,t]` | `storage_epsilon` (= 0.001) |
| `Dis[s,t]` | `storage_epsilon + storage_discharge_cost − storage_discharge_eac` |
| `SOC[s,t]` | 0 |
| `Flow[l,t]` | 0 |
| `Slack[z,t]` | `voll` |
| `Dump[z,t]` | `max(storage_epsilon, −min(wind_mc, solar_mc) + storage_epsilon)` |
| `R[r,t]` | 0 (reserve cost is the opportunity cost captured by the headroom row) |
| `ORDC[k,t]` | `ordc_penalties[k]` |

The dump cost is deliberately set just above the most-negative renewable offer so
that overgeneration is never gamed to harvest a negative-MC production credit.
`mc[g,t]` itself is assembled upstream (`data/fleet.assemble_mc`) as
`heat_rate·fuel_price + vom + emission_rate·carbon_price + nox_rate·nox_price + …`,
then reduced by IRA/EAC credits and coal take-or-pay sunk-fuel fractions.

## 2.4 Bounds

`build_variable_bounds(...)` (line 1401):

| Variable | Lower | Upper |
|----------|-------|-------|
| `P[g,t]` | `pmin` or `min_gen[g,t]` (reliability floor) | `pmax · availability[g,t]` |
| `W[z,t]` | 0 | `wind_cf[z,t] · wind_cap[z]` |
| `S[z,t]` | 0 | `solar_cf[z,t] · solar_cap[z]` |
| `Chg`/`Dis` | 0 | storage power cap |
| `SOC` | 0 | storage energy cap |
| `Flow[l,t]` | `−TTC` (or 0 for one-way) | `TTC` |
| `Slack`/`Dump` | 0 | ∞ |
| `R[r,t]` | 0 | ∞ (headroom row binds it) |
| `ORDC[k,t]` | 0 | step width |

Lower is clipped to upper so an outage hour (`availability = 0`) forces `P = 0`
even where `pmin > 0`.

## 2.5 Reserve co-optimization (optional)

When enabled (`energy_reserve_coopt`, or ERCOT's `ercot_multiproduct_as_coopt`),
`_build_reserve_rows` (line 631) adds two row subfamilies plus an optional cap:

- **Shared headroom** (`n_headroom_rows × n_zones × T`): for headroom row `h`,
  zone `z`: `Σ_{elig g∈z} P[g] + Σ_{p∈h} R[p,z] ≤ zone_capacity + extra`. Reserve
  can only come from unloaded headroom on eligible (online) thermal units; gated
  classes contribute `−ρ·P` instead of `+P`.
- **Reserve balance** (`n_families × T`): `Σ_z R[class,z] + Σ_k ORDC[k] ≥
  requirement[f,t]`. The shortfall steps `ORDC[k]` let the requirement be met at a
  penalty price, which is exactly the scarcity adder. Each family's balance dual
  contributes to the reserve clearing price.
- **Reserve-supply cap** (optional, `n_headroom_rows × T`): a measured ceiling
  (e.g. ERCOT RTOLCAP) on cleared reserve per product, correcting the
  perfect-foresight LP's tendency to over-supply phantom reserve.

Per-ISO requirement/eligibility/penalty inputs are assembled in `results/scarcity.py`
(ERCOT multi-product, PJM stepped ORDC) and the runner's `*_reserve_coopt_inputs`
helpers (PJM/NYISO/MISO). See [`05-policy.md`](05-policy.md) §5.5.

## 2.6 Results and prices

`DispatchResult` (line 1549) holds the solved quantities and prices:

```
dispatch[n_gen,T], wind_dispatched[n_zones,T], solar_dispatched[n_zones,T],
slack[n_zones,T], dump[n_zones,T], prices[n_zones,T],
storage_charge/discharge/soc[n_storage,T], flows[n_links,T],
objective_value, status, build_time, solve_time,
reserve_dispatch[n_reserve,T], reserve_price[T],
reserve_price_by_family[T,n_families], rps_shadow_price
```

Price recovery:
- **Energy LMP**: `prices[z,t]` = dual of energy-balance row `t·n_zones + z`.
- **RPS shadow price**: dual of the RPS row.
- **Reserve clearing price**: sum of reserve-balance row duals for the hour
  (per-family breakdown in `reserve_price_by_family`).

## 2.7 HiGHS interface and warm-start

The LP is loaded into HiGHS via `addCols()` (bounds + objective + matrix) and
`addRows()` (CSR row bounds + matrix). Notable choices:

- **Presolve off** — the 8760-hour LP is already tight; presolve added ~17 s for
  negligible reduction.
- **Dual simplex** default, so re-solves warm-start from the prior basis.
- Thread count via env var `MARKET_SIM_HIGHS_THREADS`.
- Post-solve the primal status is checked; anything other than optimal fails the
  solve.

### `DispatchModel` — re-costable LP (lines 1653–2149)

`DispatchModel` builds the constraint matrix and bounds **once**, then lets the
objective be re-costed in place via `changeColsCost()`. This is what makes the
P0→P1→P2 sequence cheap: P1 warm-starts from P0's basis with only the cost vector
changed (startup markup added), converging in a handful of simplex iterations
instead of a cold solve. `solve_dispatch(...)` (line 2243) is the one-shot wrapper
that builds a `DispatchModel` and calls `.solve()`.

### Cross-year warm-start

`CrossYearBasis` (line 1609) freezes a solved HiGHS basis (column/row statuses)
plus the layout identity and unit IDs. `export_cross_year_basis()` /
`apply_cross_year_basis()` carry a basis into the next year: surviving units are
remapped by `unit_id`, index-stable blocks (W/S/storage/flow/slack/dump) copy
directly, and new units start nonbasic-at-bound. This warm-starts year N+1 from
year N's optimum.
</content>
