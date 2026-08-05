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

**Measured 2026-08-05 by FFR-5D-M** (the chartered continuation, sitting Addendum T.3): both §2
invocations run verbatim, cold, as two concurrent background jobs (rule 12) at `origin/main`
`331ac576`. Comparability re-verified at that head: no `ScenarioConfig` default moved since the
manager's check at `34473b0c` (the only diffs are docs/dashboard/2022-touchpoint files); every
`ercot_storage_as_*` sibling, `coal_perplant_offer_yearly`, and
`capacity_screen_unified_lookahead` ship default False. Runtime keys from the `cache_key=` log
lines: **shipped `6a824992b5fb1baf`** — identical to FFR-5A's recorded key — and **unified
`49eac64f146b3460`**. Read-out: `scripts/probes/ffr5d_paired_arm.py`, unmodified; full JSON at
`docs/handoffs/ffr-5d/paired-arm-probe-2026-08-05.json`. Both metas record
`leakage_violations: []`, solved {2021, 2023, 2024, 2025}, bridged {2022}.

### 3.0 Reproduction gate — BOTH §2 shipped expectations HELD

* §2(a): decided **29 / 8,217.6 MW all-coal**, `decided_year=2021`, `execute_year=2024`;
  re_confirmed 29 in 2023 on byte-identical margins (net $22.43 vs bar $58.50/kW-yr,
  p_mean $29.377); **reversed 29 in 2024; executed 0**. Exactly FFR-5A's record.
* §2(c): entry_capped **582 / 58,683.9 MW** (2022 ledger), 536 / 57,959.9 MW (2023), **none at
  the lookahead-priced screens** (2024/2025 ledgers). Exactly FFR-5A's record.

No drift — the armed arm is interpretable as a pure paired difference on one flag.

### 3.1 Read (a) — coal-cohort event sequence

| ledger yr (screen of yr−1) | shipped | unified |
|---|---|---|
| 2022 | decided 29 / 8,217.6 MW coal (exe 2024) | decided 45 / 10,942.9 MW — **all gas_st, zero coal**; gas_st lag 1 → **executed in the same 2022 ledger** |
| 2023 | re_confirmed 29 (byte-identical margins) | — |
| 2024 | **reversed 29** (net $341.47 vs bar $58.50) | — (564 units fail, ALL entry_capped, 0 admitted) |
| 2025 | — | **coal decided 11 / 1,482.1 MW** (`decided_year=2024`), exe **2027 — outside the window**; 554 entry_capped |

The coal cohort does not reverse in the unified arm — it is never decided at the 2021 screen
at all, first fails at the 2024 screen (repaired level), and its execution year (2027) falls
outside the window. The unified arm's one executed event is a **10.9 GW all-gas_st exit wave
decided at the 2021 screen and executed in the 2022 bridge-ledger year** — before the scored
window.

### 3.2 Read (b) — bar decomposition (cap-weighted, FFR-5A persisted fields)

* **Shipped coal at decide:** net $22.43/kW-yr = energy 22.43 (reserve 0, capacity 0) vs bar
  $58.50; basis p_mean $29.38 / p_max $5,000, avail 0.798 (annual time-mean), mc $26.80,
  `as_pricing=hourly_signal`. At the 2024 screen the SAME cohort re-prices to **net $341.47**
  (p_mean $65.38, p_max $5,000 — the unrepaired lookahead's manufactured pro-forma scarcity,
  74 h > $1,000 at the runtime seam log) → reversal. Unchanged from FFR-5A.
* **Unified at the 2021 screen** (under unification the entering-2022 signal is the
  growth-scaled lookahead off the 2021 solve — Uri hours price at VOLL, real model scarcity —
  instead of the shipped arm's raw-duals+overlay bridge object): gas_st fails (net $17.90 vs
  bar $35.00; avail **0.595** under the hourly-availability repair, mc $44.26, p_mean $52.72 /
  p_max $5,000) and is decided/executed; coal clears its bar and is never decided. The
  pre-registered reads show the screen's basis, not a per-repair counterfactual split — which
  repair moved which fuel across the bar is not decomposed here.
* **Unified at the 2024 screen:** the repaired level (p_mean **$9.54** / p_max **$46.22**,
  zero pro-forma scarcity hours, vs the shipped arm's mean $58.90 / 74 h > $1,000 / max $5,000
  at the same seam) prices coal at **net $0.04 vs bar $58.50 → decided**, not reversed.
* **The screen-basis flip FFR-5A measured is gone**: one object prices every screen, and the
  very seam that reverses the shipped cohort (manufactured scarcity present) decides the
  unified one (manufactured scarcity removed). The unification did what it was built to do;
  what the level repairs expose is §3.3–§3.4.

### 3.3 Read (c) — fleet-wide entry_capped census

| ledger yr | shipped | unified |
|---|---|---|
| 2022 | 582 / 58,683.9 MW (coal 5.7 / cc 30.7 / ct 11.0 / st 11.3 GW) | none |
| 2023 | 536 / 57,959.9 MW | none |
| 2024 | none | 564 / 62,971.7 MW (coal 14.0 / cc 37.2 / ct 11.4 / st 0.35 GW) |
| 2025 | none | 554 / 66,060.5 MW (coal 12.5 / cc 40.2 / ct 13.0 / st 0.35 GW) |

The census **moves ends rather than shrinking**: under the shipped object the whole merchant
fleet fails at the raw-dual screens and nobody fails at the manufactured lookahead; under the
unified object nobody (but gas_st) fails at the Uri-priced screens and essentially the whole
merchant fleet (66.1 GW by 2025) fails at the repaired forward level, held online only by the
adequacy admission cap. FFR-5A §6.3's "both consistent bases fail the fleet" finding survives
the level repairs — at the repaired level it is the admission cap, not the margin bar, doing
all the retention work.

### 3.4 Read (d) — scored thermal exits vs the 1.534 GW actual

From the committed `crossover_score.json` retirement scorecards (2023–2025 window):

| | actual | shipped | unified |
|---|---|---|---|
| total GW | 1.534 | **0.000** (err −100 %) | **10.943** (err +613.5 %) |
| composition | coal 0.932 / gas_ct 0.502 / gas_cc 0.080 / biomass 0.019 | — | **gas_st 10.943 (actual gas_st exits: 0.0)** |
| unit recall > 300 MW | 3 units | 0 / 3 | 0 / 3 |
| band | | FAIL | FAIL |

The unified execution lands in the 2022 bridge-ledger year, before the scored window; inside
2023–2025 **both arms execute nothing**. Side effects: additions (decision basis) 27.0 GW
shipped → **17.0 GW** unified vs 55.4 GW actual — the repaired lower level also admits less
entry; reserve margins 34.8 / 39.8 / 47.8 % (shipped 2023/24/25) vs **21.9 / 26.7 / 31.8 %**
(unified). Dispatch skill is essentially unmoved (C3a gaps 2.15/12.93/3.34 shipped vs
2.14/13.65/3.97 unified) — the flag touches screens, not dispatch, as designed.

**The §2 honest expectation held, in its sharpest form:** the armed arm unifies the object and
removes the manufactured level, and it **still does not resolve the real exits** — it swaps
"retire nothing" for "retire a 10.9 GW gas-steam lump in one pre-window year, none of it the
fuel that actually exited." Per rule 1, no repair was or will be tuned toward 1.534 GW; this
number goes to the manager as-is.

## 4. Governance position

*(filled after registration)*

* **Registered, hindcast namespace only:** `ercot-2021-2025-t1ff-armr-ffr5d-shipped` /
  `ercot-2021-2025-t1ff-armr-ffr5d-unified` (`frontend/data/hindcast/*.json` sidecars via
  `register_hindcast.py`, `meta.kind="full_forward"`, slim bundle files committed under the
  standing convention). Evidence runs under Q.2, expected to be superseded when keepers
  settle. Never the backcast registry (plan §7.5).
* **Nothing armed, promoted, or tuned.** `capacity_screen_unified_lookahead` stays default
  OFF; no model code changed in this continuation; the arms inherit the FFR-5A shipped
  posture verbatim (re-verified at head, §3 preamble).
* **Matrix (rule 28(b)):** the ERCOT cell for `capacity_screen_unified_lookahead` keeps
  verdict **O** with the measured citation appended — the paired-arm measurement is done, but
  the arming/lift adjudication belongs to the manager (Addendum I.1), read against Addendum
  G.2's three binds.
* **G.2's binds, as they land here:** (1) attribution is clean — one flag, distinct runtime
  cache keys, and the shipped arm reproduces FFR-5A's recorded values exactly, so the delta
  is the mechanism's, not drift's; (2) the sign inversion G.2 flagged on I12 is now measured
  on the retirement layer itself — 0 GW → 10.9 GW of the wrong fuel in the wrong year; (3)
  vacancy is not validation — inside the scored 2023–2025 window both arms execute nothing,
  so the in-window retirement layer remains untested at BOTH postures.
* **Rule 22:** solves {2021, 2023–2025}, 2022 bridged (never solved, measured data never
  read — `leakage_violations: []` in both metas); scoring bounded to 2023–2025 on both sides;
  the T1-FF window is legal under the holdout freeze's enumerated carve-out; no marker
  touched.
* Any future arming decision scores leave-one-year-out within 2023–2025 FIRST (§0 of this
  handoff, unchanged; rule 22). The FH-4/FH-5 lift determination is the manager's, not this
  lane's.
