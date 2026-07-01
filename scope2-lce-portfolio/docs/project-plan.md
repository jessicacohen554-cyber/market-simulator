# Project Plan — Scope 2 Hourly LCE Portfolio Optimization Tool

> This is the origin-of-record planning document (the approved plan). The executable
> build plan and current status live in [`../PLAN.md`](../PLAN.md); the fresh-session
> build-manager prompt lives in [`management-handoff.md`](management-handoff.md).

## Context

**Why:** The market simulator produces business-as-usual (BAU) hourly LMPs per ISO. We
want a *separate* decision tool that consumes those prices and answers a corporate
procurement question: **given a company/facility 8760 load, what portfolio of clean &
low-carbon energy (LCE) resources + storage best matches that load hour-by-hour, and how
high can hourly matching go for a given cost premium above wholesale?** (e.g. "how 24/7-matched
can we get for a $1 / $2 / $5 / $7 / $10 / $20 premium?").

This is a **portfolio-selection LP**, distinct from the market **dispatch LP**. It must NOT
touch or contaminate `src/market_sim/**`. It is a **fully self-contained, vendored tool** in
the top-level directory `scope2-lce-portfolio/` — no `import market_sim` anywhere; any reused
loader logic is copied and clearly marked.

**Isolation guarantee:** the only change inside the existing repo is one pointer doc
(`docs/scope2-lce-portfolio.md`) describing what the project is and where it lives. Everything
else is under `scope2-lce-portfolio/`.

## Design Decisions (locked at inception)

| Decision | Choice |
|---|---|
| Deliverable scope (session 1) | Scaffold + docs + prompts **+ minimal working LP** on synthetic data |
| Coupling to market-sim | **Vendored** — no `import market_sim`; copied logic lives in `vendored/` with re-sync notes |
| Default optimization mode | **Premium-cap → maximize hourly CFE matching %** (Mode A). Mode B (matching-target → min premium) also supported |
| Directory | Top-level `scope2-lce-portfolio/` |

## The Optimization Model (portfolio LP)

Single aggregated node **per ISO** (intake already collapsed to hour × ISO). Full 8760 hours.

**Sets:** resources `r` (existing nuclear, new nuclear/SMR, onshore wind, offshore wind, solar PV,
geothermal, existing hydro, storage techs: 4h/8h/12h Li-ion, LDES, hydrogen); hours `t` (0..8759);
storage subset `s ⊂ r`.

**Parameters:** `load[t]` (MWh, after growth), `lmp[t]` ($/MWh, BAU input), `cf[r,t]` (∈[0,1]),
`fixed[r]` ($/MW-yr) + `vom[r]` ($/MWh) seeded from LCOE low/mid/high, `cap_max[r]`/`cap_min[r]`
(per-resource caps/floors), storage duration + round-trip efficiency.

**Decision variables (flat column vector, no per-hour Python loop):**
```
build_mw[r] | gen[r,t] | chg[s,t] | dis[s,t] | soc[s,t] | grid_buy[t] | excess[t]
```

**Core constraints:**
- Energy balance (per hour): `Σ_r gen[r,t] + Σ_s(dis - chg) + grid_buy[t] − excess[t] = load[t]`
- Generation bound: `0 ≤ gen[r,t] ≤ cf[r,t] · build_mw[r]`
- Capacity caps: `cap_min[r] ≤ build_mw[r] ≤ cap_max[r]`
- Storage SOC (cyclic): `soc[s,t] = soc[s,t-1] + η_chg·chg − dis/η_dis`, `0 ≤ soc ≤ duration·power`
- Hydro monthly energy budget (optional, future)

**Matching identity:** clean serving load in hour `t` = `load[t] − grid_buy[t]` (excess is sold, not
matched). Annual hourly matching % = `1 − Σ grid_buy / Σ load`.

**Net portfolio cost:** `Σ_r (fixed[r]·build_mw[r] + vom[r]·Σ_t gen[r,t]) + Σ_t lmp[t]·grid_buy[t] −
f·Σ_t lmp[t]·excess[t]`. **BAU baseline:** `Σ_t lmp[t]·load[t]`. **Premium ($/MWh)** =
`(net cost − BAU) / Σ load`.

**Mode A (default — premium-cap → max matching):** `min Σ grid_buy[t]` s.t.
`net cost − BAU ≤ delta · Σ load`. Sweep `delta` over any list `{1,2,5,7,10,20,…}`.
*The "target expensive LMP hours" behavior falls out for free:* under a binding premium cap, grid
purchases in high-LMP hours cost more budget and excess sold in high-LMP hours earns more, so the LP
preferentially eliminates purchases in expensive hours and favors resources correlated with them.

**Mode B (matching-target → min premium):** `min net cost` s.t. `Σ grid_buy ≤ (1−target)·Σ load`
(annual), with an optional strict per-hour `grid_buy[t] ≤ (1−target)·load[t]` for hard 24/7.

The premium-cap constraint's dual gives the marginal $/MWh of an extra point of matching.

## Directory Structure

See [`../README.md`](../README.md) for the layout. Package modules under
`src/lce_portfolio/` (`config, resources, intake, profiles, lp, sweep, outputs, cli`, plus
`vendored/`); design docs in `docs/`; decision log in `docs/decisions/`; intent-capture prompts
in `docs/planning-sessions/` (PS-01..08); build prompts in `docs/prompt-packs/` (PP-00..07);
seed cost table in `data/lcoe/`; tests in `tests/`.

## Minimal Working LP (session 1, delivered)

A runnable slice on synthetic data: 3 active resources (solar, onshore wind, 4h battery),
one ISO, full 8760, Mode A premium sweep. `examples/run_sample_sweep.py` produces a
matching%-vs-premium frontier across `{1,2,5,7,10,20}` $/MWh + build MW per resource, written to
`data/outputs/` as Parquet. Follows the LP rules (no hour loop, storage ε tiebreak, duals for
prices, docstrings). Solver is HiGHS **IPM, crossover off** (the 8760-h cyclic storage network
stalls the dual simplex).

## Planning Sessions & Prompt Packs

Each `docs/planning-sessions/PS-*.md` is a decision-capture prompt that ends by writing an ADR to
`docs/decisions/`. Each `docs/prompt-packs/PP-*.md` is a build prompt that implements the decided
behavior, gated on its upstream ADRs. Ordered PP-00 → PP-07 (scaffold/config → intake → catalog →
CF profiles → LP core → sweep/CLI → outputs/reporting → tests). Status is tracked in
[`../PLAN.md`](../PLAN.md).

## Patterns Reused (mirrored, not imported)

Flat-vector variable layout & `scipy.sparse.kron` energy balance from
`src/market_sim/model/dispatch.py`; cyclic SOC constraints from `src/market_sim/model/storage.py`;
`ScenarioConfig` dataclass style from `src/market_sim/config/scenarios.py`; Parquet result
serialization from `src/market_sim/results/outputs.py`; trivial-case-first pytest style.

## Verification

1. **Isolation:** `grep -rn "import market_sim" scope2-lce-portfolio/src` returns nothing.
2. **Minimal LP:** `../.venv/bin/python examples/run_sample_sweep.py` writes the frontier Parquet.
3. **Tests:** `../.venv/bin/python -m pytest tests/ -q` (data-free, <1s).
4. **Sweep monotonicity:** matching% non-decreasing in the premium cap.
5. **Docs coherence:** every PS maps to a `docs/decisions/` slot; every PP names its target module
   and upstream ADRs.

## Next: build management

To continue the build from a fresh session, use the copy-paste build-manager prompt in
[`management-handoff.md`](management-handoff.md).
