# PRECOMMIT — capx D99: T1.6 re-pointed to `entry_pipeline_aware_signal`, T1.6b on the 2041–2050 mean

**Lane:** capx **D99** · **Date:** 2026-09-26 · **Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:** `neiso`
**Branch:** `claude/capx-d99-t16-repoint`, fresh off `origin/main` **`f1ea324acd17`** (`f1ea324a…`, PR #6721)
**Authority:** OWNER RULING **Q72** (2026-09-26, capx ledger §0bl / §3): *"Re-point, 2041–2050 mean"* =
DESIGN-capx-d97 §6 option **(a)** with sub-choice **(a-2)**. Rejected by the owner: (a-1) the final-year scalar,
and retiring T1.6 for NEISO.
**Binding charter:** `docs/handoffs/capx-director-prompt-pack-2026-08.md` "D99".
**Design (read whole; its §3 outcome map A–E, honesty clause and "no third lever" BIND):**
`docs/handoffs/DESIGN-capx-d97-t16-repoint-2026-09-25.md`.
**Precedents cited:** Q27 / capx **T16-A** (`FINDING-capx-t16a-ladder-repoint-2026-09-02.md`, the previous
T1.6 re-point) and capx **D35** (`FINDING-capx-d35-p2-scope-2026-09-02.md`, the worked FC-6 re-scope);
D94 (`FINDING-capx-d94-2026-09-24.md`, the golden-recipe battery discipline); D96
(`FINDING-capx-d96-2026-09-25.md`, whose `base` leg is this ladder's short rung); D90-R A.2 (the controlled swap).

**PUSHED BEFORE ANY LP.** The ladder definition, the metric construction, the recipe, the G-DRIFT audit, every
prediction and the scoring rule are fixed at this commit. The one shard is pinned to this commit's full
40-character SHA.

---

## 0. THE ACT IN ONE PARAGRAPH

T1.6 ("RPS/ACP vs VRE supply, short → long") could not discriminate in NEISO because its lever
(`entry_rate_limits`) sits behind the binder that actually caps NEISO VRE flow at C/L = 1.5 GW/yr — the
pending-stock netting in `new_entry.py` (DESIGN-d97 §1.4). This lane (1) re-points the ladder to
`entry_pipeline_aware_signal` (`vre_short` = False, the golden's own posture; `vre_long` = True), (2) moves
T1.6b onto the **2041–2050 horizon mean** of the REC dual ÷ ACP (T1.6a untouched), (3) solves the one rung that
does not already exist, in one shard, and (4) re-scores `neiso-t3` FC-6 by a controlled swap of the battery,
preserving the prior verdict at `neiso-t3-pre-d99`.

---

## 1. THE LADDER-DEFINITION AND SCORER CHANGE (made in this commit; zero LP)

### 1.1 The re-point (`scripts/run_driver_battery.py::build_ladders`, T1.6)

| | before (Q27 / T16-A) | **after (Q72 / D99)** |
|---|---|---|
| `vre_short` | `{"entry_rate_limits": True}` | **`{"entry_pipeline_aware_signal": False}`** |
| `vre_long` | `{"entry_rate_limits": False}` | **`{"entry_pipeline_aware_signal": True}`** |
| T1.6a | `rps_dual_over_acp` `le_target` 1.0 | **unchanged** |
| T1.6b | `rps_dual_over_acp` `monotone_down` | `rps_dual_over_acp_mean_2041_2050` `monotone_down` |

A **re-point under the pre-registration, not an amendment of it** — the same act T16-A performed and
verified (plan §2's T1.6 "Ladder" cell names an economic condition, "VRE fleet held short vs long", not a
field; T16-A §2). `entry_rate_limits` is no longer perturbed: both rungs carry the golden's own `True`. The
comment block records the Q27 history in place and appends the Q72 re-point, the binder trace, the lever's
owner-signed provenance (FFR-5C, D-17(a)) and the **declared confound** (DESIGN-d97 §2.5(b): the thermal caps
un-net too; `entry_thermal_gw` / `co2_mt_total` / `reserve_margin_final` are reported beside the dual).

### 1.2 The (a-2) metric (`_extract_metrics`)

`rps_dual_over_acp_mean_2041_2050` = mean over solve years 2041…2050 of `result.rps_shadow_price` ÷ the ISO's
ACP (`_acp_ceiling`), rounded 4 dp — the same cache reads, the same ACP ratio and the same rounding as the
final-year `rps_dual_over_acp`. The window is a named module constant `T16B_MEAN_WINDOW = (2041, 2050)` with
the Q72 citation (rule 5). **Emitted only when every window year was solved and carries a dual**; a run that
stops short (a 2026–2030 smoke) or misses a year gets no value, so T1.6b SKIPs as vacuous — never a
partial-window mean. `rps_dual_over_acp` itself (T1.6a's metric) is byte-unchanged.

### 1.3 The plan-§2 edit

`docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md` §2 Tier-1 table, T1.6 row: the
"Ladder" and claim text are untouched; one italic sentence is appended recording the Q72 scoring
construction (T1.6a on the final-year dual; T1.6b on the 2041–2050 mean; rules unchanged).

### 1.4 Tests

`tests/scoring/test_driver_battery.py`: the T16-A pin class `TestT16Repoint` is updated to pin the Q72 rungs,
T1.6a unchanged and T1.6b on the window metric, plus the window constant; a new `TestT16bHorizonMeanMetric`
pins the construction on stub cache reads (a step-and-cobweb series: final year 1.0, window mean 0.5; a
2026–2030 run emits no window metric; a missing window-year dual emits no window metric).

**Scorer test lane, run here:** `pytest tests/scoring` → **1,660 passed, 17 failed, 18 skipped**. The 17
failures are **pre-existing and environmental** (un-hydrated data: SOCO bench, `ff_readiness`, the golden
manifest, the keeper solve pin reading the local `highspy`); the **identical 17-test fail set** was measured on
`origin/main` `f1ea324a` with this lane's changes stashed. `ruff check` / `ruff format --check` clean.

### 1.5 Cross-lane re-grade — every OTHER registered verdict, artifact-only

`forecast_verdict.py` is **not edited** and does not import `run_driver_battery` (its one mention is a
docstring). The battery is consumed only as a committed JSON artifact, so no registered verdict's scorer path
changes. Measured anyway, on the 110 board verdicts:

| class | n | method | result |
|---|---:|---|---|
| re-scorable from tracked artifacts (`rescore_forecast_verdicts.py`, dry run) | 25 | run at `main` (stashed) and at this branch | **25/25 `moved: nothing`, HOLD→HOLD, output identical but for the wall-clock stamp** |
| battery-bearing: `neiso-t3`, `neiso-t3-pre-d96` | 2 | `forecast_verdict.py --tier t3` over each record's committed inputs, at this branch | **both reproduce NON-PROVENANCE IDENTICAL** (categories, caveats, determination, reasons, rubric, schema, tier) |
| no tracked artifact (FFR-3A-class gitignored bundles; historical `-pre-*` records) | 83 | scorer code path byte-unchanged; no battery JSON rewritten | cannot move |

Re-scored 25: `caiso-t1h ercot-t1h ercot-t1x-ffr2a miso-t1h miso-t1h-pre-d31 miso-t1h-pre-d33 miso-t1h-pre-d46
miso-t1h-pre-d53 miso-t1h-pre-d60 miso-t1x-ffr2a neiso-t1h neiso-t1h-pre-d45r neiso-t1h-pre-d46 neiso-t1x
neiso-t1x-pre-rcrepair nyiso-t1h nyiso-t1h-d45r-curveon nyiso-t1h-pre-d60 nyiso-t1x pjm-t1h-d45r-fixed
pjm-t1h-d62-pubbar pjm-t1h-pre-d45r pjm-t1h-pre-d57 pjm-t1x-ffr2a spp-t1h`. Re-run after the final rebase
and reported in the FINDING.

---

## 2. THE RUNGS — `vre_short` IS D96 `base`; ONE RUNG IS SOLVED

### 2.1 The recipe (DESIGN-d97 §3, D94/D96 discipline)

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
PYTHONPATH=.:src python3 scripts/run_full_horizon.py \
  --iso NEISO --start-year 2026 --end-year 2050 --golden-posture --full-solve-authorized \
  --no-ccs-retrofit-fixed-cost-co2-scaling --set ccs_retrofit_vom_adder=8.0 \
  [--set entry_pipeline_aware_signal=True] --out-dir results/ff-t3-neiso-golden/d99/<rung>
```

`neiso-t3` golden recipe at D96's vintage, **both pins** (`ccs_retrofit_vom_adder` 8.0 via `--set`;
`ccs_retrofit_fixed_cost_co2_scaling` False via the runner's own flag), `entry_rate_limits` = True (the
golden's own; not passed, not perturbed), and the rung override through the generic `--set` (SCN-WS0; validated
against `ScenarioConfig`, recorded in `set_overrides`). **No `src/` or `scripts/` edit is needed to solve.**

### 2.2 Config probe at zero LP (this HEAD)

Each rung's config was built exactly as the runner builds it (`run_full_horizon.main` with
`solve_and_summarize` stubbed → `resolve_policy_bundle` → `apply_iso_scenario_defaults`):

| rung | resolved key | vs D96 `base` recorded payload |
|---|---|---|
| `vre_short` | **`dbef1ecac9596c90`** = D96 `base`'s literal, to the character | 13 fields differ, **0 real**: each absent from D96's payload and `False` here (schema growth — `caiso_import_gas_coupling_ladder_only`, `caiso_intertie_gap_fill_measured_{dam,gas}`, `cc_eia923_identity_emission_basis`, `coal_committed_nested_on_mustrun`, `nuclear_dormancy_defers_to_vintage_exit`, `nwpp_demand_plant_basis`, `nyiso_ldc_generator_delivered_gas`, `pjm_zonal_gas_basis_skip_923_priced`, `reliability_floor_layup_window_mask`, `unit_outage_{membership_repair,unit_fuel_routing}`, `wefor_residual_short_screened_coal`); key-inert (the key reproduces) |
| `vre_long` | **`883f25eb5ee3e55e`** (predicted) | the same 13 + exactly `entry_pipeline_aware_signal: False → True` |

### 2.3 G-DRIFT — `5a48f437` (D96's pin) → `f1ea324a` (this lane's base): **ALL-INERT**

Window: `git diff 5a48f437 f1ea324a -- src/market_sim scripts/run_full_horizon.py scripts/lib data/raw` — **20
code files, 20 `data/raw` paths**; `scripts/run_full_horizon.py`, `scripts/lib/**`, `config/iso_configs.py`,
`config/solve_surface*.py` and all seven `SURFACE_MODULES` are **unchanged** (so no NEISO surface row moved —
consistent with §2.2's key reproduction). Every hunk classified (delegated reader, checked here):

| file(s) | what changed | class | reason |
|---|---|---|---|
| `config/scenarios.py` | 13 new `bool = False` fields, each in `_CACHE_KEY_OPTIONAL_FIELDS` at drop value `"False"`; 3 `TIER_TAGS`; `_BACKCAST_ONLY_OVERLAY_FIELDS` += 1; a comment | INERT | all default False and absent from the recipe; **`_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` untouched**, no `__post_init__` added; key reproduces (§2.2) |
| `config/paths.py` | `EIA_923_GENERATION_FUEL_{DIR,PATH}` | INERT | readers are `scripts/data` derive/fetch scripts and one probe only |
| `data/eia930/demand.py`, `runner.py:521`, `data/eia930/envelopes.py` (NWPP block) | `nwpp_demand_plant_basis` | INERT | `iso == "NWPP"`, flag False; `_hindcast_measured_demand` is hindcast-only |
| `data/eia930/envelopes.py` (intertie), `model/interchange/{caiso,spec}.py`, `data/neighbor_price.py`, `data/fuel/electric_power.py` | CAISO DAM/gas gap-fill, ladder-only coupling | INERT | CAISO seam only; flags False |
| `data/fleet/arrays.py` | nuclear-dormancy skip; short-screened coal WEFOR; outage hour-grain / membership / fuel routing | INERT | `mode == "backcast"` (≈L416); `wefor_residual` None; the outage block is inside `outage_source == "historic"` (≈L1226) and the recipe is `statistical` |
| `data/fleet/campd_bins.py` | `_measured_rate_map` accepts `eia923_identity`; identity CC HR; CO2 re-base in `apply_plant_emission_rates_v2`; nested committed coal | INERT — **two of these run** | the widened flag filter runs, but no NEISO `_processed-legacy` artifact carries an `eia923_identity` row (checked per file); the v2 re-base runs but its identity map is `{}` unless `cc_eia923_identity_emission_basis` and `measured_cc_heat_rates` (both False) |
| `data/floor_mechanisms.py` | `EXTRA_ZERO_FORCING_FIELDS` += 1 | INERT | ablation-twin builder only |
| `data/fuel/{__init__,basis/*,resolve}.py` | NYISO LDC delivered gas; PJM skip-923 cells | INERT | NYISO/PJM predicates + False flags; NYISO path reached only via `run_calibration.py` |
| `data/resolved_inputs.py` | two provenance-record kwargs | INERT | record only, values False |
| `data/outages.py`, `model/interchange/core.py` | ERCOT hour-grain / member-repair / short-screened selectors; layup mask kwarg | INERT | historic-overlay / backcast / reliability-floor (False) paths |
| `data/raw` (CAISO CC HR, CAISO DAM gap-fill, ERCOT hour-grain outage CSVs, PJM member-repair CSVs, MISO short CSVs, EIA-923 gen-fuel, NYISO LDC transport + PDFs, NWPP plant basis) | — | INERT | other ISOs' per-ISO files, historic overlays, or no engine reader |

`scripts/run_calibration.py` also changed (+181) and is **off the forecast path** (nothing on the
`run_full_horizon` → `pipeline.api` → `runner` chain imports it).

**Verdict: all-INERT ⇒ D96 `base` IS the `vre_short` rung at this HEAD, and this lane solves ONE rung
(`vre_long`), as the charter directs.** Confidence: high — the audit is corroborated by the §2.2 key
reproduction, and D96's own E1 showed its window's all-INERT audit held byte-for-byte.

### 2.4 The `vre_short` row, built here at zero LP (`docs/handoffs/d99/battery_golden_rung.py reuse`)

D96's cache parquets are off `main` (its shard branches are cut), so `vre_short`'s row is built as follows,
and the construction is declared here, before any LP:

* **Asserted byte-identical:** D96 `base` vs D94 `vre_short` — all **25/25 evolution ledgers** (`cmp`) and every
  `trajectory` cell (D96 E1). Same config (§2.2).
* **Cache-grain metrics** (`co2_mt_total` 151.2747, `renewable_build_gw` 33.0, `entry_thermal_gw` 7.4839,
  `rps_dual_over_acp` 1.0, …) are D94's committed `vre_short` row, computed by the instrument's own
  `_extract_metrics` at cache grain (D94 §5).
* **The one new metric** is computed from D96 `base`'s committed ledgers' `rps_dual`, which the runner writes as
  `round(result.rps_shadow_price, 6)` for NEISO's scalar row: 2041–2050 all **50.0** ⇒
  **`rps_dual_over_acp_mean_2041_2050` = 1.0**. The ledger-vs-cache grain equality is **validated on
  `vre_long`**, where the shard computes it at cache grain and the helper prints the ledger-grain value beside it.
* `overrides` recorded as `{"entry_pipeline_aware_signal": false}`; a `reused_from` block names the leg, the
  key and the basis. Written to `results/ff-t3-neiso-golden/d99/vre_short/_battery_metrics/NEISO/`.

---

## 3. THE SHARD (rule 32 `[R-SHARD]`; this session runs no LP)

**One shard, one indivisible 2026–2050 invocation** (a forecast horizon is an evolution chain; rule 36(c)).

* `source_revision` = **this PRECOMMIT commit's full 40-char SHA**; first hard stop `git rev-parse HEAD` equals
  it. **No rebase, pull or sync.**
* Own `--out-dir` `results/ff-t3-neiso-golden/d99/vre_long/`, own branch `claude/capx-d99-vre_long`.
* **Rule 34 (a):** append `!results/ff-t3-neiso-golden/d99/vre_long/**` to `.gitignore`, then a **plain**
  `git add .gitignore results/ff-t3-neiso-golden/d99/vre_long`; never `-f`, never `-A` / `.`. Slim files first
  (one commit, pushed), cache parquets after.
* After the solve: `docs/handoffs/d99/battery_golden_rung.py metrics --out-dir … --rung vre_long` (zero LP; it
  REFUSES on a config-signature mismatch).
* Hard stops: SHA; the solved `run_config.json` shows both pins, `entry_rate_limits` True,
  `entry_pipeline_aware_signal` True, `mode=forecast`, ISO NEISO; key = `883f25eb5ee3e55e` (a mismatch is
  **reported, not repaired**; the shard still pushes).
* Budget: container preparation (`prepare_solve_container.py`, `hydrate_data.py --profile neiso`,
  `regenerate_clean.py`; ~45–60 min measured by D92) + a **~35–45 min** solve.
* Forbidden by name: edits under `src/` or `scripts/`; anything under `frontend/data/**`;
  `dashboard_add_run.py` / `build_manifest.py` / `build_status.py` / `prune_iso_runs.py`; opening a PR; deleting
  any result. *"A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a
  FAILURE."*

**The parent** fetches the branch; verifies config signature + pins + key off `run_config.json`;
`git ls-tree` > 0 files under the bundle (rule 34(d)); recomputes the battery row from the fetched caches;
lands the slim bundle + row on this branch (rule 33(f)); **only then** archives the shard. The shard's
cache-parquet branch is **not merged** (D94/D96 precedent); per-year parquets stay off `main`.

---

## 4. PREDICTIONS — FIXED HERE

### 4.1 The outcome map (DESIGN-d97 §3, binding) with its (a-2) reading

Short rung is fixed: `rps_dual_over_acp` **1.0**, window mean **1.0**. The dual cannot exceed the ACP (the
ACP column caps it), so the long rung's window mean is ≤ 1.0 by construction.

| # | measured (long rung) | T1.6a (final-year) | T1.6b (2041–2050 mean) | FC-6 battery row | FC-6 |
|---|---|---|---|---|---|
| **A** | VRE ≫ short (≥ 50 GW) **and** 2050 dual < 50 | PASS, non-vacuous `[1.0, <1]` | PASS, non-vacuous | **PASS** | **CAVEAT → PASS** |
| **B** | VRE ≫ short, dual leaves the ACP inside 2041–2050, **2050 dual back at 50** (cobweb parity) | PASS **vacuous** `[1.0, 1.0]` | PASS, **non-vacuous** — the case (a-2) exists for | CAVEAT (1 vacuous row, T1.6a) | CAVEAT |
| B′ | VRE ≫ short, dual leaves the ACP **only before 2041** | vacuous | vacuous (mean 1.0) | CAVEAT (2 vacuous) | CAVEAT |
| **C** | `renewable_build_gw` long = 33.0 (no re-size) | vacuous | vacuous | CAVEAT | CAVEAT — **§1.4's seam trace is wrong**; report the binder from the ledgers' `queue_budget_gw` / margin rows; no third lever |
| **D** | VRE ≫ short, dual 50.0 in **all 25** years | vacuous | vacuous | CAVEAT | CAVEAT — **§1.2's arithmetic is wrong**; report eligible vs obligation per year; no third lever |
| **E** | long > short on either metric | FAIL | FAIL | FAIL | FAIL — reachable only through an ACP violation; a root-cause object, never a threshold widened |

**The determination stays HOLD under every letter** (FC-1/2/3/4/7 FAIL on instruments this lane does not
touch). Only FC-6's status and the battery-row detail string can move; in the A case the caveat list drops
`FC-6 driver response`. `program-status.json` moves only if the NEISO `fc` FC-6 letter moves (A only).

### 4.2 Point predictions, graded at full magnitude in the FINDING

| # | prediction | label |
|---|---|---|
| P1 | outcome letter: **A or B** (joint ≈ 0.6); C ≈ 0.1; D ≈ 0.25; B′ ≈ 0.05; E ≈ 0 | my odds |
| P2 | `renewable_build_gw` long ∈ **[55, 66] GW** (DESIGN-d97 band); my point **58** | design band, binding |
| P3 | first year with `rps_dual < 50` in `vre_long` ∈ **[2038, 2043]**; my point **2041** (curtailment at 40+ GW pushes it past the 2039 nameplate crossing) | design band, binding |
| P4 | long window mean ∈ **[0.2, 0.9]**; point **0.5** (the design's [0.3, 0.7] for B) | mine |
| P5 | P(2050 dual back at 50 \| off-ACP inside the window) ≈ **0.5** — i.e. A vs B is a coin flip, so B is not a surprise | design |
| P6 | `entry_thermal_gw` moves by **≥ 0.5 GW** (either direction) vs 7.4839 | design (the confound is live) |
| P7 | `co2_mt_total` long **<** 151.2747 Mt; magnitude undeclared (the CCS wave also moves) | design |
| P8 | `reserve_margin_final` long ≠ 0.06107 (moves); direction undeclared | mine, weak |
| P9 | key `883f25eb5ee3e55e` exact | strong (§2.2) |
| P10 | wall ∈ [30, 50] min, RSS < 5 GB (D94 37.4 / 33.5 min, 3.4 GB; D96 33.4–50.3 min, 3.5–3.7 GB) | design |
| P11 | ledger-grain window mean = cache-grain window mean on `vre_long` (to 4 dp) | strong |
| P12 | every FC status other than FC-6 and every reason/caveat other than FC-6's are unchanged; FC-6 paired P1/P2/P3 rows byte-identical (their inputs are carried) | near-certainty |

**The one-sentence summary I will be graded on:** *Un-netting the pending stock roughly doubles NEISO's VRE
build to ~58 GW, the REC dual leaves the $50 ACP around 2041, and the 2041–2050 mean reads the regime (~0.5)
that the final-year point cannot — so T1.6b passes non-vacuously, while FC-6 clears to PASS only if the 2050
dual also stays off the ACP.*

---

## 5. THE RE-SCORE — CONTROLLED SWAP (D90-R A.2)

**Step 0, the control, ALREADY ESTABLISHED at this HEAD before any LP.** `forecast_verdict.py --tier t3` over
the standing record's committed inputs — `--summary/--run-config/--dof-ledger/--attestation` = `d96/base/*`;
`--hindcast-score` = `hindcast/neiso-2021-2025-realized-t1h-d46/NEISO/da19b85495178949/score.json`;
`--crossover-score` = `hindcast/neiso-2023-2027-crossover-rcrepair/NEISO/07e416f3f8072e7c/crossover_score.json`;
`--paired-invariants` = `d96/paired_invariants.json`; `--corridor` = `ff-corridor/dispositions/neiso-t3.json`;
`--driver-battery` = `d94/driver-battery-neiso-2026-09-24.json` — reproduces `ff-verdicts.json["neiso-t3"]`
**NON-PROVENANCE IDENTICAL** (categories, caveats, determination, iso, reasons, rubric, schema, tier; `notes`
are registry-authored). Measured here, with this lane's scorer change applied.

**Step 1, the swap:** only `--driver-battery` → `results/ff-t3-neiso-golden/d99/driver-battery-neiso-2026-09-26.json`,
assembled by `docs/handoffs/d99/battery_golden_rung.py assemble` from the `vre_short` (reused) and `vre_long`
(solved) rows through the instrument's own `run_ladder`. Every other input is held byte-identical.

**Registration.** The prior `neiso-t3` record is preserved **byte-equal at `neiso-t3-pre-d99`**. Scoring happens
**after this lane's final rebase**. **This lane is the SOLE writer of `frontend/data/forecast/ff-verdicts.json`
this window.** `program-status.json` moves only if an FC letter moves.

**Assembly validation, declared:** before the swap, `assemble` over the two **D94** rows with the D94
registry would have re-emitted D94's battery; since the registry moved, the D99 helper is validated instead by
(i) the `reuse` assertions (§2.4) and (ii) the parent recomputing `vre_long`'s row from the fetched caches and
matching the shard's row byte-for-byte.

## 6. RULE 28 / 31 / 33 / BOUNDARIES

* **Rule 28:** no `ScenarioConfig` field is added and no default moves ((c) does not fire; `mechanism-matrix-guard`
  unaffected). (a) discharged by D97 §4 (NEISO `entry_pipeline_aware_signal` cell `U`/`U`, not `R`/`I`/`G`).
  (b): the NEISO shard's `entry_pipeline_aware_signal` cell gets its `ev` stamp citing this lane, and **stays
  `U`** — an instrument perturbation inside a ladder is not an arming adjudication (28(d); T16-A precedent).
* **Rule 25:** nothing is armed anywhere; `vre_long` is a ladder perturbation.
* **Rule 31:** no solved bundle is deleted. **Rule 33(f):** the shard branch is transport; the slim bundle
  lands here before this PR merges; leftover refs named for the owner. **Rule 27:** every pushed file of
  300+ lines blob-verified.
* No backcast artifact, keeper, marker or freeze is touched. `src/` untouched. `scripts/` edit: exactly
  `run_driver_battery.py` (the ladder + metric, charter item 2).
