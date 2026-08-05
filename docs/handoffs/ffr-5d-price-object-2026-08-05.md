# FFR-5D — Unify the capacity screens on the lookahead price object and repair its level

**Session.** FFR Wave 5, IMPLEMENTATION lane (owner decision D-19(a), sitting Addendum S.3/S.5,
signed 2026-08-05). Branch `claude/ffr-5d-capacity-unification-iut1uy`, off `origin/main`
`57d4d66a` (PR #3577 / FFR-5C verified MERGED at `f664d37c` before branching — step-0
precondition). ERCOT keeper at dispatch: `2026-08-05-run167b-soc-reserve`; every
`ercot_storage_as_*` sibling ships default False, so the FFR-5A shipped posture (and this
lane's paired-arm comparability) is unchanged at this head.

**This lane arms nothing, promotes nothing, tunes nothing.** It lands ONE gated
`ScenarioConfig` field (`capacity_screen_unified_lookahead`, default OFF, byte-identical off),
measures a shipped-vs-armed paired arm on the FFR-5A posture, and reports. Any future
arming/promotion decision scores leave-one-year-out within 2023-2025 FIRST (rule 22) — the
next session inherits that duty; nothing here discharges it.

---

## 1. What landed (PR: field + unification + repairs + tests + matrix row)

* `capacity_screen_unified_lookahead` (`scenarios.py:3161`, GATED default OFF), registered in
  `_CACHE_KEY_OPTIONAL_FIELDS` + the defaults ledger (hash-dropped at default: every
  pre-existing cache key byte-stable; an armed run gets a distinct key). Matrix row added in
  the same PR (rule 28(c)); harness flag `--capacity-screen-unified-lookahead`
  (None-sentinel inherit) + `META_RECORD_SPEC` `FromConfig` row.
* **Unification** (armed): the runner's price-signal seam (`runner.py`,
  `_screen_signal_for`) prices a lookahead signal for EVERY entering year the last solved
  year's `prior_results` will screen — the next year always, a bridged next year included
  (growth-scaled fallback: `is_hindcast_bridge_year` joins `is_crossover_forward_year` in the
  measured-demand guard, so the bridged year's measured load is NEVER read — rule-22
  compliance by construction, the quarantine assertions untouched), and the bridge-adjacent
  year after a bridged next year (the bridge iteration never solves, so `prior_results` stays
  pointed at the last solved year and its screens would otherwise consume a signal priced for
  the wrong year). The signals live in `unified_signals: {entering_year: (n_zones, T)}`; the
  top of the year loop swaps the entering year's own signal into
  `prior_results.price_signal` BEFORE any screen consumes it — `evolve_fleet` (retirement
  pipeline decide AND re-screens, CCS, economic entry) and the storage screen both read that
  one field, so every screen for an entering year sees ONE object (rule 19).
* **Level repairs** (armed; each from existing model state, ZERO new tunables — rules 23/24):
  * (a) **storage enters the stack** — `_storage_peak_shave_net_load`: the entering storage
    fleet (`StorageArrays` power/energy caps, final-hour values under vintage-ramp 2-D
    profiles; energy-cap-weighted `eta_chg*eta_dis` round-trip) as a per-day energy-limited
    peak-shave/valley-fill on net load, vectorized per-day bisection (rule 2). The fill level
    is bounded by the shave level so charge/discharge hours are disjoint by construction.
  * (b) **entering-year VRE capacity** — the evolved zonal `wind_cap`/`solar_cap` pools x the
    model's own hourly `wind_cf`/`solar_cf` (the same arrays that bound `W[z,t]`/`S[z,t]`)
    replace the prior year's REALIZED dispatched VRE output (which embeds prior-year
    curtailment). FFR-5C `pipeline_vre` still adds on top.
  * (c) **hourly availability** — the outage model's `(n_gen, T)` availability replaces the
    annual time-mean stack derate; merit order (time-mean mc) unchanged; the per-hour
    cumulative stack and per-hour reserves feed the same ORDC tail. Left-searchsorted tie
    semantics proven identical to the scalar path.
  * **No repair was escalated** — all three built from existing state with no invented
    parameter.
* **Byte-identity proof (off)**: `tests/unit/model/test_capacity_screen_unified_lookahead.py`
  — the pre-FFR-5D hand-computed signal series reproduce exactly with every new argument at
  its default, and explicit-defaults == omitted-defaults byte-equal; the pre-existing
  `test_price_signal.py` / `test_entry_pipeline_aware_signal.py` suites pass unchanged
  (1038 model + 457 config unit tests green; harness/meta provenance suites green).

## 2. PRE-REGISTERED READS (written and committed BEFORE either arm was solved)

Paired arms on the FFR-5A §1 posture exactly (every optional flag omitted so shipped
defaults inherit; the armed arm adds ONLY the new flag):

```
uv run python scripts/run_capacity_hindcast.py \
  --iso ERCOT --vintage 2020 --start-year 2021 --end-year 2025 \
  --forward-from-base --arm realized \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr5d-shipped

uv run python scripts/run_capacity_hindcast.py \
  --iso ERCOT --vintage 2020 --start-year 2021 --end-year 2025 \
  --forward-from-base --arm realized --capacity-screen-unified-lookahead \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr5d-unified
```

Cold solves (fresh container, `results/` gitignored), 4 LP years each (2022 bridged),
years sequential within each invocation. Cache keys read from the runtime `cache_key=` line
only. The reads, fixed now:

* **(a) The coal cohort's event sequence** — decided / re_confirmed / reversed / executed
  counts+MW by ledger year, `decided_year` read off event rows (the ffr-3q3 §3.2 trap), at
  `<out-dir>/ERCOT/<runtime-key>/evolution_<year>.json`. Shipped expectation (reproduction):
  decided 29 / 8,218 MW all-coal `decided_year=2021`, re_confirmed 2023 byte-identical,
  reversed 2024, executed 0.
* **(b) The enriched `pipeline_events` bar decomposition** — FFR-5A's persisted ledger fields
  (`net_revenue_usd`, `going_forward_cost_usd`, `energy_margin_usd`, `reserve_uplift_usd`,
  `screen_price_mean/max_usd_mwh`, `mc_mean_usd_mwh`, `availability_mean`, `as_pricing`),
  cap-weighted over the cohort at each screen. They persist from the FFR-5A enrichment — no
  re-instrumentation.
* **(c) The fleet-wide `entry_capped` census** — count/MW by fuel per ledger year (shipped
  expectation: 582 / 58,684 MW at the decide screen; 0 at the lookahead-based screens).
* **(d) Scored thermal exits vs the 1.534 GW actual** — executed retirements by fuel/year in
  each arm against the real 2023-25 ERCOT exits (three units > 300 MW).

**THE HONEST EXPECTATION, STATED BEFORE SOLVING:** the armed arm unifies the OBJECT (no
screen-basis flip at the bridge) and lowers the object's LEVEL (the three repairs remove
manufactured pro-forma scarcity), but it may STILL not resolve the real 1.534 GW of exits —
FFR-5A §6.3 measured that BOTH consistent bases fail to reproduce them (raw fails the whole
66.9 GW merchant fleet; unrepaired lookahead fails no one), and the repaired level has never
been measured. Whatever the armed arm shows is a FINDING, not a failure; no repair may be
tuned toward 1.534 GW (rule 1) — the repaired level is a measurement, and if the cohort
still reverses (or nothing ever fails, or everything fails) that number goes to the owner
as-is.

## 3. Measured results — the paired arms

*(filled after the pre-registered solves; nothing above this line changed after solving)*

## 4. Governance position

*(filled after registration)*
