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
| `dur[s]`, `η[s]` | table | storage duration (h) and one-way efficiency `√rte` (fixed-duration only) |
| `dur_min[s]`, `dur_max[s]` | table | min/max duration hours for split-storage (0 for fixed-duration) |
| `hydro_budget[m]` | table | ISO monthly hydro energy budget (MWh), fleet total, or omitted |
| `δ` | sweep | premium cap (Mode A) or matching target (Mode B) |
| `f` | `config.excess_sale_fraction` | fraction of LMP received for surplus |

## Decision variables (flat column vector)

```
build_mw[r] | gen[r,t] | chg[s,t] | dis[s,t] | soc[s,t] | grid_buy[t] | excess[t] | build_energy[k] | exc_ex[t]
```

All ≥ 0. `build_mw[r] ∈ [capmin[r], capmax[r]]`. Split-storage resources (LDES, hydrogen) carry
an additional energy-capacity variable `build_energy[k]` (MWh), costed at `$/MWh-yr` and
bounded within per-tech `[duration_min_h × build_mw, duration_max_h × build_mw]` (ADR 0006).
Fixed-duration storage has no such column; its energy sizing is `duration_h × build_mw`.
`exc_ex[t]` (existing-attributable excess) exists only when `additionality_only` is on —
see Additionality accounting below. (Block order matches `lp.py`'s `_Layout`:
`build_energy` and `exc_ex` come *after* `excess`.)

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
0 ≤ soc[s,t] ≤ dur[s] · build_mw[s]                        (fixed-duration)
  or
dur_min[s] · build_mw[s] ≤ soc[s,t] ≤ dur_max[s] · build_mw[s]   (split-storage, energy-bound)
  or equivalently  soc[s,t] ≤ build_energy[s]               (for split: power and energy chosen separately)
chg[s,t] ≤ build_mw[s] ,  dis[s,t] ≤ build_mw[s]
```
Round-trip efficiency = `η²`; `η = √rte`.

**Hydro monthly energy budget** (fleet-shared: one row per month, summing every
budget-flagged resource — the table budget is the ISO contractable-fleet total,
not a per-resource allowance; audit LP-3):
```
Σ_{r: is_budget_hydro} Σ_t∈month gen[r,t] ≤ hydro_budget[m]
```
Calendar months are indexed 0–11 with fixed day counts (Jan 31 days, …, Dec 31);
aggregated from the 8760 hourly gen columns via vectorized month binning (ADR 0008).

## Matching & premium

**VOLUMETRIC hourly matching** (ADR 0007): within each hour, clean energy counts
toward matching only up to that hour's load. Matched energy in hour `t` is
`min(clean_serving_load_t, load_t) = load_t − grid_buy_t`, and surplus is excluded.
The score is:
```
annual hourly matching % = Σ_t matched_t / Σ_t load_t = 1 − Σ_t grid_buy[t] / Σ_t load[t]
```
This is the **percentage of annual load energy matched at hourly granularity**, *not*
"% of hours at 100% matching" (strict per-hour variant available via `strict_hourly_matching`
in Mode B). Storage is charged from the aggregate node; grid purchases are counted unmatched
at purchase time even if later discharged (conservative, no round-trip laundering).
**Residual carbon:** grid_buy is attributed hour-by-hour at the market simulator's
fossil-only **average** emission rate (tCO₂/MWh, attributional/location-based accounting;
ADR 0013, superseding ADR 0007's marginal-rate attribution), plus — since ADR 0012 — the
residual stack emissions of partial-capture resources (gas CC + CCS) at their per-resource
rate:
```
residual_co2_tons = Σ_t grid_buy[t] × fossil_avg_co2_rate[t]          # grid_co2_tons
                  + Σ_r Σ_t gen[r,t] × emission_rate_ton_mwh[r]       # resource_co2_tons
```
Both components are reported separately (`grid_co2_tons`, `resource_co2_tons`) per frontier
point. Reporting only — the matching metric and matching sums are unchanged: a resource that
clears the ADR 0012 threshold (capture > 0.90, residual < 0.050 tCO₂/MWh, enforced at
catalog load) counts **fully** toward hourly matching, with no intensity-weighted discount.

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
The stored `shadow_price` is the premium row's dual: **MWh of unmatched load
removed per $ of premium budget** (negative, since relaxing the budget lowers
`Σ grid_buy`). The "marginal $/MWh of buying one more unit of matching" is its
reciprocal with the sign flipped (`1/|dual|`), not the dual itself.
In the non-saturated regime the premium constraint binds, so the reported
(achieved) premium equals `δ`; once matching saturates at 100% the returned
solution's premium is `≤ δ` (still valid — that matching is reachable in budget).

**Additionality accounting** (ADR 0008 as amended 2026-07-02, audit LP-1): With
`config.additionality_only=True`, existing (PPA) resources no longer count toward
matching — but only the existing energy that *serves load*. Exported existing
energy is surplus, and per ADR 0007 surplus is excluded from the metric entirely.
The accounting identity is:
```
unmatched_t = grid_buy_t + max(0, Σ_{r∈existing} gen[r,t] − excess_t)
matching_pct = 1 − Σ_t unmatched_t / Σ_t load_t
```
Excess is attributed to existing generation *first* (the only LP-expressible
attribution). In the LP this is the auxiliary block `exc_ex[t] ≥ 0` with
`exc_ex[t] ≤ excess[t]` and `exc_ex[t] ≤ Σ_{r∈existing} gen[r,t]`: Mode A adds
`+1` on existing gen and `−1` on `exc_ex` to the matching objective; Mode B puts
the same net term on the matching constraint's buy side. Optimization pressure
drives `exc_ex[t] → min(excess_t, Σ existing gen_t)`; the reported metric is
recomputed from the primal `gen`/`excess` values, never from `exc_ex` itself.

**Mode B — matching_target:**
```
minimize   net_cost + ε·Σ_t excess[t]
subject to Σ_t grid_buy[t] ≤ (1−δ)·Σ_t load[t]     # annual matching ≥ δ
           [ or  grid_buy[t] ≤ (1−δ)·load[t] ∀t    # strict per-hour 24/7 ]
```
The `ε` on `excess` (audit LP-2; `config.storage_epsilon`) breaks the zero-cost
simultaneous buy+sell ray that exists at `f = 1.0` (ADR 0005): `+lmp` on
`grid_buy` exactly cancels `−f·lmp` on `excess`, and the crossover-off IPM
(ADR 0003) would otherwise return an arbitrary interior point of that fat
optimal face, corrupting the reported matching %, grid CO₂, and buy/surplus
MWh. Reported `net_cost`/`premium` are recomputed from `lmp` post-hoc, so the
ε never leaks into the premium. Mode A is immune (its objective prices each
buy-MWh at +1).

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
