# Storage Modeling Audit — Market Simulator & Scope 2 LCE Portfolio Tool (2026-07)

Deep audit of how energy storage is modeled in (1) the market dispatch
simulator (`src/market_sim/`) and (2) the sectioned-off Scope 2 optimization
tool (`scope2-lce-portfolio/`), cross-referenced against power-system and
corporate-CFE modeling best practices. Produced alongside ADR 0017
(`scope2-lce-portfolio/docs/decisions/0017-storage-charge-policy-excess-clean-only.md`),
which adds the requested optionality: storage in the Scope 2 tool can now be
restricted to **charging only on excess contracted clean energy in the
portfolio** instead of charging/dispatching on energy arbitrage.

---

## 1. Market simulator — how storage is modeled

### 1.1 Dispatch LP (operational model)

Per storage unit `s` (zone-aggregated per tech), the 8760-hour LP carries
`Chg[s,t]`, `Dis[s,t]`, `SOC[s,t]` columns (`model/dispatch.py`):

- **SOC dynamics, cyclic boundary:** `SOC[t] = SOC[t−1] + η_chg·Chg[t] −
  Dis[t]/η_dis`, with hour 0 wrapping to hour 8759. RTE is split evenly into
  one-way efficiencies (`η = √rte`).
- **Bounds:** `0 ≤ Chg, Dis ≤ power_cap`, `0 ≤ SOC ≤ energy_cap`; caps may be
  hour-varying `(n_storage, T)` under the intra-year COD/retirement vintage
  ramp (`storage_cap_profiles`) — first-order for CAISO's mid-year GW-scale
  additions.
- **Costs:** ε = 0.001 $/MWh throughput tiebreaker on charge+discharge
  (degeneracy rule #9); per-unit discharge `vom` carrying the battery
  dispatch adder (`battery_dispatch_adder`, default 0) or the pumped-storage
  adder (now 0 everywhere after the fitted PJM $10 adder was correctly
  retired as an off-registry-style artifact); optional discharge EAC credit.
- **Grid interaction:** storage participates in the zonal energy balance like
  any resource — it charges from whatever the balance supplies and its
  discharge earns the LP dual. This is *correct* for a wholesale market
  model: merchant storage genuinely arbitrages.
- **Perfect-foresight mitigations:** an annual LP with cyclic SOC gives
  storage perfect price foresight and over-flattens net load relative to real
  bidders. The codebase mitigates with three structural (not fitted) devices:
  (a) measured hourly ERCOT up-AS power reservation
  (`reserve_storage_as_power`) — cleared AS MW cannot also arbitrage, and it
  passes the rule-13 admissibility test (regenerates from forward AS
  requirements); (b) reserve co-optimization rows where storage headroom
  `cap − Dis + Chg` backs upward reserve; (c) an optional daily SOC-anchor
  block (`storage_daily_cycle_hours`) pinning day-start SOC to hour-0 level —
  a diagnostic limiter on multi-day banking.
- **Fleet data:** EIA-860 energy-storage schedule per zone (backcast), with
  pumped storage recovered from the *generator* schedule (prime mover `PS`) —
  a real gap in naive battery-only loaders, correctly closed. EIA-860 lacks
  RTE/PS energy capacity, so cited constants fill in
  (`PUMPED_STORAGE_RTE/DURATION_HOURS`), with the 4-hour Li-ion RTE routed
  through `ScenarioConfig.storage_rte_4hr` so calibration sweeps reach the
  backcast fleet.

### 1.2 Capacity evolution (investment model)

Storage entry (`apply_storage_new_entry`) screens a **value stack** per tech:
duration-windowed arbitrage revenue (window widens with duration so LDES sees
multi-day spreads; net of cycle-life degradation cost), RA capacity value
(net-CONE × duration-interpolated ELCC × penetration-saturation derate,
capacity-market ISOs only, locational deliverability factor when gated on),
and AS revenue (ERCOT, saturating in penetration). Build is merit-ordered
with a per-tech share cap, annual cap, and cumulative ceiling; capex follows
Wright's-Law learning with IRA ITC phaseout.

### 1.3 Cross-reference vs best practice

| Practice (reference) | Market sim | Assessment |
|---|---|---|
| Linear SOC with one-way efficiencies, no simultaneous chg/dis via ε or binaries | η=√rte split, ε tiebreak | ✅ standard LP treatment; ε matches HiGHS-era practice; binaries rightly avoided |
| Horizon boundary condition on SOC (cyclic or fixed terminal) | cyclic annual | ✅ cyclic is the cleanest artifact-free choice for a full-year LP |
| Limit perfect-foresight over-cycling (rolling horizon, AS deduction, cycle limits) | measured AS reservation + optional daily anchor + throughput adder | ✅ structurally sound; the *measured* AS series is backcast-only — a forecast analogue (AS requirement × storage share) exists via `as_revenue` saturation but not as an hourly power reservation. Worth a follow-up. |
| Duration-dependent ELCC with marginal saturation (NREL/E3, PJM class ratings) | interpolated breakpoint table + `(1−pen)^1.5` derate | ✅ matches the published shape; breakpoints cited |
| Degradation as $/MWh throughput from cycle life (NREL ATB augmentation) | energy-capex slice / rated cycles × 0.25 replacement fraction | ✅ reasonable; the 0.25 fraction is a documented, tunable simplification |
| Storage as price-taker in investment screens vs price-maker reality | prior-year prices, one cycle per window | ⚠️ known optimism at high penetration (no self-cannibalization of spreads within the screen year); partially offset by the saturation derates. Acceptable for a one-pass evolution (rule #10). |
| No cross-ISO tuned parameters | PS adder map now empty; battery adder per-config | ✅ consistent with rules 24–26 |

**Verdict:** the market-sim storage model is methodologically sound for its
purpose (wholesale dispatch + entry). Arbitrage behavior is *supposed* to be
there. No violations of the repo's non-negotiable rules found; one follow-up
(forecast-mode hourly AS power reservation) noted.

---

## 2. Scope 2 tool — how storage is modeled

### 2.1 Formulation (`lce_portfolio/lp.py`)

Portfolio LP (capacity choice + hourly operation, single node): per storage
tech, `chg/dis/soc` columns with the same cyclic SOC, `η=√rte`, ε tiebreak,
and power bounds tied to `build_mw`. Fixed-duration techs get
`soc ≤ duration_h × build_mw`; LDES/hydrogen carry an independent
`build_energy` column with separately annualized $/kW and $/kWh capex and
duration bounds (ADR 0006) — this power/energy split sizing is best practice
for LDES studies and better than many published tools. IPM with crossover
off is an appropriate, documented speed choice; degeneracy rays are ε-priced
(audit LP-2 fix).

### 2.2 The finding that motivated this audit: storage arbitrage

In the pre-ADR-0017 formulation, storage charges from the **aggregate node**:
the energy balance `Σgen + Σdis − Σchg + grid_buy − excess = load` lets
charging be sourced from grid purchases, and discharge be exported through
`excess` at full LMP (`excess_sale_fraction = 1.0`, ADR 0005). Consequences:

- **The optimizer can run storage as a merchant trading book.** Wherever the
  matching constraint leaves headroom (Mode B below-100% targets; Mode A via
  the premium budget, which arbitrage revenue relaxes), the cost-minimizing
  solution buys cheap grid energy into the battery and sells the peak. The
  new regression test demonstrates this directly: solar + battery under a
  $5/$500 spread grid-charges overnight in a Mode B solve.
- **The accounting itself is honest** (this is important): grid purchases are
  counted unmatched at purchase time and carry hourly residual CO₂ (ADR
  0007/0013), so arbitrage never *launders* matching percentage. But the
  *portfolio* and the *premium* are shaped by trading rents, and the stored
  energy has mixed, unattributed provenance — which conflicts with how CFE
  storage accounting is defined (below).

### 2.3 Cross-reference vs CFE best practice

| Practice | Scope 2 tool (before) | After ADR 0017 |
|---|---|---|
| Storage discharge counts as CFE only if charged from qualifying clean generation (EnergyTag granular certificates; Google 24/7 methodology; M-RETS storage EACs) | no charge-source attribution; mixed provenance | `excess_clean_only` guarantees clean-only charging by construction |
| System studies model participant storage charging from the contracted portfolio (Riepin & Brown 2022 PyPSA 24/7; Xu/Jenkins Princeton 24/7) | grid charging allowed | optional policy matches the literature's participant-storage constraint |
| Volumetric hourly matching, surplus excluded (CFE score) | ✅ ADR 0007, correctly conservative | unchanged |
| Residual carbon at hourly average grid rate (GHG Protocol location-based, attributional) | ✅ ADR 0013 | unchanged |
| No round-trip laundering of grid energy into "matched" | ✅ purchases counted at buy time | strengthened: grid energy can't enter storage at all |

Additional (latent) findings, no behavior change today:

- **S2-1 (latent):** storage-row `vom` in `resource_costs.csv` is applied to
  the `gen[r,t]` columns, which are pinned to 0 for storage (`cf = 0`) — a
  nonzero storage VOM would be silently ignored rather than priced on
  discharge. All shipped storage rows carry `vom = 0`, so this is a trap, not
  a live bug. Recommend: raise on nonzero storage `vom` at load time, or wire
  it onto the `dis` columns (market-sim does the latter).
- **S2-2 (observation):** with `excess_sale_fraction = 1.0` the buy+sell ray
  is ε-priced in Mode B only (Mode A's objective covers it) — already
  documented as audit LP-2; the ADR 0017 rows additionally cap `excess` by
  clean generation under the new policy, shrinking that degenerate face.

### 2.4 The new optionality (implemented)

`PortfolioConfig.storage_charge_policy` — `"arbitrage"` (default, historical
behavior, zero new rows) or `"excess_clean_only"`, which adds per-hour rows

```
Σ_s chg[s,t] + excess[t] ≤ Σ_r gen[r,t]
```

so storage charges **only on the portfolio's excess contracted clean
generation**: no grid charging, no re-sold grid purchases, and (via the
energy balance) grid purchases and discharge serve load only — the merchant
channel is closed and storage is a pure clean-shifting matching device.
Exposed as `--storage-charge-policy` on the CLI and as a config-file field;
flows into run metadata automatically. The strict per-hour form
`chg_t ≤ max(0, Σgen_t − load_t)` is nonconvex (needs integers, forbidden by
the LP-only design), so the linear rows above are the tightest expressible
form; the accepted residual — charging from clean generation while some load
is grid-served in the same hour — remains honestly penalized in both the
matching metric and residual CO₂ (details in ADR 0017).

Tests: `tests/test_storage_charge_policy.py` (arbitrage baseline reproduces
grid charging; policy eliminates it; clean-surplus shifting is preserved;
degenerate no-generation fleet idles; both policies agree when no arbitrage
rent exists; config validation).

**Divert-and-backfill closure (ADR 0018, 2026-07-04).** The accepted residual
above is now (a) *visible* everywhere — every solve reports
`divert_backfill_mwh = Σ_t min(Σ_s chg[s,t], grid_buy[t])` on `PortfolioResult`,
in the frontier parquet, and per setpoint in the ADR 0014 report (zero means
charging never coincided with a grid purchase) — and (b) *closable* on demand
via a third policy `"excess_headroom_only"`. That policy keeps the ADR 0017 rows
and adds an iterative LP cut loop (`lp.solve_with_charge_policy`): solve, pin the
charge columns of any hour that both charged storage and bought from the grid
(tolerance `EXCESS_HEADROOM_TOL_MWH = 1e-3` MWh, above IPM interior noise),
re-solve, repeat until none remain (≤ `T` iterations, ≤ 3 in practice; each
solve a pure LP — no MIP). It is a conservative restriction: it can under-use
storage relative to the true (nonconvex) optimum but never overstates matching.
The static alternative `chg_t − Σ gen_t ≤ −load_t` (forces gen ≥ load every
hour) and binaries were both rejected — see ADR 0018. Tests:
`tests/test_excess_headroom_policy.py`.

---

## 3. Boundary check

The isolation boundary holds: the Scope 2 tool still imports nothing from
`market_sim` (the change touches only `scope2-lce-portfolio/`), and the
market simulator's storage model is untouched by this audit.
