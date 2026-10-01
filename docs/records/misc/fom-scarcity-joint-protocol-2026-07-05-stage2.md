# FOM + scarcity joint protocol — Stage 2 re-run (2026-07-05, W2-P3 Stage 2)

*Executes the Stage-2 leg of `docs/handoffs/capacity-economics-plan-2026-07.md` §5: the
step-2 **revenue-side fix** (landed this session) and the §5.4-gated **grid re-run against
the accredited floor** the Stage-1 reconciliation note required before any FOM flip. The
Stage-1 report (`fom-scarcity-joint-protocol-2026-07-05.md`) and its grid JSON remain the
record of the Stage-1 decision; this file and `fom-scarcity-grid-2026-07-05-stage2.json`
are the Stage-2 record. Forecast probes only — nothing here registers on the backcast
dashboard, and nothing touches 2022 / H1-2026 (rule 22).*

**Headline decision: the ATB FOM defaults are again NOT flipped.** With the accredited
floor (PR #1413) and the revenue-side fix both in, the going-forward FOM level is **still
inert** in the ERCOT verification grid — the capacity trajectory is byte-identical across
the FOM axis in all six ERCOT cells and both PJM cells (zero economic retirements
anywhere; CO₂ identical to 3 decimals). What masks it has *changed*: it is no longer the
Stage-1 nameplate-ledger bug (fixed), but **genuine accredited-adequacy shortage under
mid-growth ERCOT demand** — the floor now correctly un-retires every screen-eligible unit
because the requirement really is unmet, and the harness's force-enabled adequacy backstop
floods the system with gas-CT (12 GW in 2027; 15.2 GW over the first three evolution
years), collapsing the scarcity signal that the fixed revenue stack would otherwise
collect. Per rule 1 the FOM values stay frozen at their externally-identified targets
(CT 21 / CC 30 / coal 45 — DOF ledger below); the tornado FOM-band re-centring and the
`fom_and_scarcity` paired perturbation remain deferred with the flip.

---

## 1. The revenue-side fix (plan §5 step 2) — what landed

The Stage-1 audit measured the retirement screen collecting ~1.5 $/kW-yr for the ERCOT
CT fleet against the Potomac SOM observable of ≈68 $/kW-yr (new-proxy CT, 2024) — a ~40×
structural understatement. Root cause: the screen evaluated **realized LP dispatch**
margin against a price signal that includes the **post-solve ORDC adder the dispatch
never saw** — an out-of-merit peaker was credited none of the scarcity rent the signal
carries, and no mechanism paid its reserve headroom. Two structural changes, zero fitted
parameters (rule 1; the SOM tables are the validity check, never a target):

1. **Pro-forma margin basis.** The retirement screen now evaluates the *attainable*
   inframarginal margin — per-hour `max(0, price − mc, r) × pmax × availability` — the
   unit's optimal response to the screen's own signal, which is exactly the construction
   of the Potomac SOM net-revenue tables and the basis the thermal *new-entry* screen
   already used (an incumbent was previously judged on a strictly lower basis than an
   identical entrant).
2. **Hourly reserve-price valuation** (`screen_reserve_value_enabled`, default on): each
   reserve-eligible unit's hour is valued at its best use — energy or reserve, never both
   on the same MW (the co-optimization arbitrage condition). The signal is the reserve
   co-opt's own duals under `ercot_thermal_as_endogenous` (all-products tier for
   synchronized units, Non-Spin tier for offline-capable quick-starts, mirroring the
   co-opt's headroom cascade), else the post-solve ORDC scarcity adder — grounded in
   ERCOT market design: RTORPA/RTOFFPA pay real-time on-line/off-line reserves the same
   ORDC price the energy adder carries (Nodal Protocols §6.5.7.5). When the hourly signal
   is present it is the SOLE thermal AS pricing (rule 19); the annual endogenous per-fuel
   rate and the calibrated exogenous flat rate are superseded, eliminating the
   upper-bound double-count the annual headroom rate would carry against a pro-forma
   energy margin.

Also landed at the same call sites (plan §6 CX-6c): wind/solar entry candidates now value
their **build zone's hourly CF profile against that zone's prices** (shape-aware capture,
including each tech's actual share of scarcity-priced hours) instead of a flat annual
mean, with the scalar base-CF screen as fallback.

### 1.1 Does the fix move the observable?

First screen year (entering 2027, evaluating 2026 — the only year before the backstop
flood, see §2) on the default capacity-economics footing (`ordc`), capacity-weighted
fleet $/kW-yr:

| Fuel | Stage-1 screen revenue | Stage-2 screen revenue | Going-forward bar (legacy / ATB) | SOM anchor (new proxy, 2024) |
|---|---:|---:|---|---:|
| gas_ct | 1.3–1.6 | **17.2** | 8 / 21 | ≈ 68 |
| gas_cc | ≈ 39 | **47.2** | 12 / 30 | ≈ 89 |

The CT stack moves ~11× toward the observable. The residual CT gap vs SOM is expected in
sign and rough size: the SOM figure prices a *new efficient proxy* (HR 10.5, VOM $4) in
the **realized 2024** market, while the screen prices the *fleet-average existing* CT in
a **mid-growth simulated 2026** whose scarcity is mild; the SOM anchor is an upper bound
for the fleet average (Stage-1 report §1.1 caveat). No multiplier is added to close the
rest of the gap (rules 1/14/26).

## 2. The 2×3 grid re-run against the accredited floor (plan §5 step 3)

`scripts/archive/run_fom_scarcity_grid.py`, ERCOT 2026-2031 mid-growth, legacy equal-width
fleet, `reserve_margin_build_enabled=True` in every cell (the backstop is default-off in
a normal forecast; the harness enables it so adequacy pressure is *observable* as forced
MW), 2 workers, 33 min wall-clock. Grid JSON:
`fom-scarcity-grid-2026-07-05-stage2.json`.

| Cell | 2026-2031 CO₂ (Mt) | thermal retired (GW) | backstop 2027-2031 (MW) | floor-retained 2027→2031 (MW) |
|---|---:|---:|---|---|
| ercot legacy × off   | 1105.607 | 0 | 12000/1529/1684/6546/6822 | 12678 → 56849 |
| ercot **atb** × off   | 1105.607 | 0 | identical | 12678 → 59493 |
| ercot legacy × ordc  | 1105.607 | 0 | identical | 12678 → 56849 |
| ercot **atb** × ordc  | 1105.607 | 0 | identical | 12678 → 59493 |
| ercot legacy × coopt | 1105.417 | 0 | identical | 12678 → 56849 |
| ercot **atb** × coopt | 1105.417 | 0 | identical | 12678 → 59493 |
| pjm legacy           | 2384.441 | 0 | 10000/10000/9774/3830/4173 | 0 |
| pjm **atb**           | 2384.441 | 0 | identical | 0 |

**The FOM level changes nothing, again** — but for a different reason than Stage 1:

1. **The accredited floor binds because adequacy is genuinely short.** Under mid growth
   the requirement `peak × 1.1375` outruns the accredited fleet
   (thermal at UCAP + wind/solar pools at capacity credit + storage ELCC) every year, so
   the floor un-retires every screen-eligible unit — 12.7 GW (the coal fleet) entering
   2027, growing to ~50-69 GW-flagged by 2029-2031 as the price collapse (next item)
   pushes ever more of the fleet below its bar. Unlike Stage 1's nameplate-ledger bug,
   this retention is the mechanism *working as designed*: the adequacy layer overrides
   the economics because the capacity is needed. The FOM level cannot flip a retirement
   the adequacy layer overrides.
2. **The backstop flood erases the scarcity the fixed revenue stack would collect.** The
   12 GW gas-CT force-build entering 2027 (identical in every cell) floods reserves, so
   from the 2028 screen on the ORDC adder ≈ 0 and CT revenue collapses back to
   1.9-2.5 $/kW-yr (`ordc` trajectory: 17.2 → 1.9 → 1.3 → 1.6 → 2.5). The `coopt` cells
   show the same shape from near-zero reserve duals. This is the plan §1.4 tripwire
   ("backstop firing at scale = the fleet is being built by the requirement, not the
   economics") — with the caveat that the harness itself enables the backstop; in a
   default forecast (backstop off) the same adequacy pressure would instead express as
   scarcity prices and economic CT/storage entry.

### 2.1 PJM check (FOM axis, capacity-market revenue side)

Both PJM cells identical across the FOM axis. Screen revenue: CT ≈ 95 $/kW-yr (94.5
capacity payment + 0.7 energy), CC ≈ 130 (95 capacity + 34.7 energy). The capacity
payment (net-CONE × UCAP) **covers ATB-level FOM for both classes** (95 > 21, 130 > 30),
so the plan §5.3 trigger for re-checking `net_cone_per_kw_yr` against the published
BRA/CONE filing does not fire. (The PJM backstop's ~10 GW/yr forced builds are
FOM-invariant and flagged as an adequacy-accounting question for the PJM hindcast
follow-up, not a FOM finding.)

## 3. Acceptance gates & decision (plan §5.4)

| Gate | Observed (atb × ordc) | Pass? |
|---|---|---|
| 2026-2028 thermal retirement pace 0.5-2 GW/yr | 0 GW (floor retains all eligible) | ✗ |
| Backstop ≈ 0 in years 1-3 | 15,214 MW | ✗ |

**Decision: DO NOT flip.** The FOM level remains unobservable in the realized fleet:
flipping CT 8→21 / CC 12→30 / coal 40→45 moves zero MW and zero tonnes, so a flip would
still be a no-op falsely credited with the plan §1.4 emissions effect. The ATB values
remain the frozen, externally-identified targets (§4). **What still masks FOM, precisely:**
ERCOT mid-growth adequacy shortage → the (now correctly-accredited) floor un-retires
every eligible unit → the harness-enabled backstop backfills and collapses scarcity →
screen revenue falls below every candidate bar so *relative* bar levels never decide
anything. Unblocking paths (any of): (a) growth-lagged entry closing the adequacy gap
economically (the foresight lookahead arm, plan §2.3 — re-run still open, §5); (b) a
grid variant with the backstop off, where adequacy expresses as scarcity price and the
screens see it (a harness change, recorded as the natural Stage-3 probe); (c) demand
paths where ERCOT is not perpetually short. None of these is a reason to bend FOM or
revenue toward each other (rules 1/14).

## 4. DOF-ledger entries (rule 21, updated)

| Parameter | Default | Identified target | Identification source | Status |
|---|---|---|---|---|
| `fixed_om_gas_ct` | 8.0 | **21.0** | NREL ATB 2024 Gas CT (F-frame) FOM | target frozen; flip blocked — FOM inert behind adequacy retention (§3) |
| `fixed_om_gas_cc` | 12.0 | **30.0** | NREL ATB 2024 Gas CC FOM | target frozen; flip blocked |
| `fixed_om_coal` | 40.0 | **45.0** | NREL ATB 2024 / EIA-S&L existing-coal FOM | target frozen; flip blocked |
| `screen_reserve_value_enabled` | True | — (mechanism gate, no numeric DOF) | ERCOT Nodal Protocols §6.5.7.5 (RTORPA/RTOFFPA); co-opt duals are the model's own | **zero fitted parameters** — the signal is the already-cited ORDC curve / the LP's own duals; off = ablation |
| revenue stack (screens) | pro-forma + hourly reserve | CT/CC ≈ SOM (68/89 $/kW-yr, upper anchors) | Potomac ERCOT SOM Fig 56 | first-screen-year CT 1.5→17.2, CC 39→47.2; residual gap = fleet-average-vs-new-proxy + simulated-2026-vs-realized-2024 scarcity, NOT closed by any multiplier |

## 5. Deferred / open (with reasons)

1. **FOM default flip + tornado FOM-band re-centring + `fom_and_scarcity` paired
   perturbation** — deferred with the flip (re-centring bands on unmoved defaults would
   misreport the base case; Stage-1 report §6.1 unchanged).
2. **Foresight A/B re-run** (`scripts/run_foresight_ab.py`, plan §2.4) — still the open
   next step, now doubly motivated: the lookahead arm is unblocking-path (a) of §3. Not
   run this session (8 × 15-year ERCOT forecasts exceed the session budget after the
   grid + hindcast re-runs); the pre-rebase A/B artifacts remain invalid per the Stage-1
   reconciliation note 3.
3. **Backstop-off grid variant** — the natural Stage-3 probe isolating whether FOM
   becomes observable once adequacy expresses as price instead of forced MW.

*Grid JSON: `docs/handoffs/fom-scarcity-grid-2026-07-05-stage2.json`. Produced
2026-07-05, W2-P3 Stage 2.*
