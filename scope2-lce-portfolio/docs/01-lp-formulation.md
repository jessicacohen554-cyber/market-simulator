# 01 — LP Formulation

The portfolio LP is a **capacity-choice + hourly-operation** linear program over
a single aggregated node per ISO, full 8760 hours. It is distinct from the market
simulator's dispatch LP and shares none of its code, though it mirrors the
primitives (flat column vector, vectorized sparse construction, HiGHS, duals as
prices). Implementation: `src/lce_portfolio/lp.py`.

## Sets

- `r ∈ R` — resources (generation + storage). `s ∈ S ⊂ R` — storage subset.
- `t ∈ {0, …, 8759}` — hours.

## Parameters

| Symbol | Source | Meaning |
|---|---|---|
| `load[t]` | intake (aggregated, grown) | hourly load, MWh |
| `lmp[t]` | BAU market-sim output | wholesale price, $/MWh |
| `cf[r,t]` | `profiles.py` | hourly capacity factor ∈[0,1] (0 for storage) |
| `fixed[r]` | `resources.py` | annualized fixed cost, $/MW-yr |
| `vom[r]` | `resources.py` | variable O&M, $/MWh |
| `capmax[r]`, `capmin[r]` | config / table | build bounds, MW |
| `dur[s]`, `η[s]` | table | storage duration (h) and one-way efficiency `√rte` |
| `δ` | sweep | premium cap (Mode A) or matching target (Mode B) |
| `f` | `config.excess_sale_fraction` | fraction of LMP received for surplus |

## Decision variables (flat column vector)

```
build_mw[r] | gen[r,t] | chg[s,t] | dis[s,t] | soc[s,t] | grid_buy[t] | excess[t]
```

All ≥ 0. `build_mw[r] ∈ [capmin[r], capmax[r]]`.

## Constraints

**Energy balance** (per hour, equality):
```
Σ_r gen[r,t] + Σ_s (dis[s,t] − chg[s,t]) + grid_buy[t] − excess[t] = load[t]
```

**Generation ceiling** (per resource-hour):
```
gen[r,t] ≤ cf[r,t] · build_mw[r]
```
(For storage `cf=0`, so its `gen` is pinned to 0; storage delivers via `dis`.)

**Storage SOC dynamics** (cyclic, per storage-hour):
```
soc[s,t] = soc[s,t−1] + η[s]·chg[s,t] − dis[s,t]/η[s]     (t−1 wraps 0→8759)
0 ≤ soc[s,t] ≤ dur[s] · build_mw[s]
chg[s,t] ≤ build_mw[s] ,  dis[s,t] ≤ build_mw[s]
```
Round-trip efficiency = `η²`; `η = √rte`.

## Matching & premium

Clean energy serving load in hour `t` is `load[t] − grid_buy[t]` (surplus is sold,
not counted). So:
```
annual hourly matching % = 1 − Σ_t grid_buy[t] / Σ_t load[t]
```

Net portfolio cost and premium:
```
net_cost = Σ_r fixed[r]·build_mw[r] + Σ_{r,t} vom[r]·gen[r,t]
           + Σ_t lmp[t]·grid_buy[t] − f·Σ_t lmp[t]·excess[t]
BAU      = Σ_t lmp[t]·load[t]
premium  = (net_cost − BAU) / Σ_t load[t]      # $/MWh above wholesale
```

## Objectives

**Mode A — premium_cap (default):**
```
minimize   Σ_t grid_buy[t]                         # == maximize matching
subject to net_cost − BAU ≤ δ · Σ_t load[t]        # premium ≤ δ
```
The premium row's dual is the marginal $/MWh of buying one more unit of matching.
In the non-saturated regime the premium constraint binds, so the reported
(achieved) premium equals `δ`; once matching saturates at 100% the returned
solution's premium is `≤ δ` (still valid — that matching is reachable in budget).

**Mode B — matching_target:**
```
minimize   net_cost
subject to Σ_t grid_buy[t] ≤ (1−δ)·Σ_t load[t]     # annual matching ≥ δ
           [ or  grid_buy[t] ≤ (1−δ)·load[t] ∀t    # strict per-hour 24/7 ]
```

A storage-throughput tiebreak `ε` (`config.storage_epsilon`, default 0.001 on
`chg+dis`) removes SOC degeneracy in both modes.

## Solver notes

HiGHS via `highspy`, model passed with `addCols`/`addRows` on a CSR matrix. The
solver is **interior-point (IPM), crossover off**: the 8760-hour cyclic storage
network is a long temporal coupling that the dual simplex traverses slowly (it can
stall for minutes under heavy storage use); IPM solves it in seconds and returns
the row duals we need. Construction is fully vectorized (`scipy.sparse`,
`np.tile`/`np.repeat`) — no Python loop over hours.

## Why this yields the intended behavior

Because `grid_buy` and `excess` settle at `lmp[t]`, the premium budget is spent
first on eliminating purchases in the **most expensive** hours and on resources
whose generation lands in those hours. As the premium cap rises, matching climbs
and the mix tilts toward **storage** and firmer resources to cover the hardest
(low-renewable, high-price) hours — visible directly in the sample sweep frontier.
