# PRECOMMIT — SCN-WS5A-RESOLVE-MISO: ruling S8 executed on MISO's three legs

**Lane** SCN-WS5A-RESOLVE-MISO · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-ws5a-resolve-miso-0s8zln` · **Data profile** `miso` (full clone — every
blob local) · **Campaign** `scn-campaign-load-2026-09-06` (unchanged: same ids, same cases, same
reference case) · **Parent lane** SCN-WS5A-RESOLVE (`claude/scn-ws5a-resolve-post-d77-m8m5ft`),
which owns NEISO/NYISO/PJM · **Inherited charter** `PRECOMMIT-scn-ws5a-resolve-2026-09-06.md` —
THE PIN, the G-DRIFT audit, the cache recipe, gates G1–G5 and the per-ISO predictions are that
document's; this one executes MISO's third of it and **does not rewrite it**.

**Pushed before the first solve** (rule 29 `[R-SCREEN]`). Every number below is zero-LP: a resolved
config at THE PIN, a committed pre-fix artifact, or arithmetic on the two. Nothing here is revised
after a solve; §5's predictions are scored as written, misses at full magnitude.

---

## 0. THE PIN — quoted, not chosen

```
bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
```

Verified locally: `git checkout -B claude/scn-ws5a-resolve-miso-0s8zln bdfb3095…` → `HEAD =
bdfb3095e9fa0cd2bec3f4e843f320b42588c72b`, working tree clean. It is `origin/main` at the parent
lane's PRECOMMIT and a descendant of `fc583339` (capx D77) and `b1f77621` (capx D65-B). **It is not
moved after the first solve**; anything landing on `main` afterwards is recorded in the FINDING as
post-pin and never used to re-read a result.

### 0.1 Bottom line before any LP

1. **All three MISO keys re-key at THE PIN and I reproduced them myself** (§2). The cache blocker
   the STATUS doc named is defeated by measurement, not by assumption.
2. **For MISO the LIVE set is exactly {D77, D65-B}** (§1). D67-ARM, D78 and D81 are all INERT here,
   each on a field I resolved off my own configs rather than inherited.
3. **MISO's contamination is small and it does not cancel in the delta.** 334.5 MW / 2.02 TWh at
   2029 and 334.5 MW / 2.50 TWh at 2030 in REF, against 484.1 MW / 3.72 TWh in LOAD-HI — ≈1.1 Mt on
   a 412.634 Mt 2030 REF level, **0.27 %**. Small enough that "MISO's levels are tolerably stale" is
   a reasonable judgement; **not** small enough for "MISO is unaffected", which is why it is measured.

---

## 1. LIVE-SET VERIFICATION — MISO only, from my own resolved configs

The parent lane's G-DRIFT audit (`1cc45bb2..bdfb3095`, 41 files / +5,362 / −433 over 34 non-merge
commits) is inherited. I re-confirmed its shape (`git diff --stat` over the same window reproduces
41 files / +5,362 / −433) and re-checked, on my own resolved legs, every classification that could
break **for MISO specifically**.

| mechanism | arming condition | MISO resolved value | verdict |
|---|---|---|---|
| capx **D77** (CCS retrofit emission-rate seam) | any converted unit | non-empty cohort from 2029 (§3) | **LIVE** |
| capx **D65-B** Acts A+B | `ccs_retrofit_vom_adder`, `ccs_retrofit_fixed_cost_co2_scaling` | **2.95** / **True** | **LIVE** |
| capx **D67-ARM** | `capacity_adequacy_requirement_published_by_iso` | **`None`** | **INERT** |
| capx **D78** (sector-gate offer seam) | `retirement_sector_gate=True` **AND** a clearing-armed ISO | gate **`True`**, clearing **`None`** | **INERT** |
| capx **D81** | forecast **AND** clearing-armed **AND** `fossil_announced_exits_enabled` | forecast ✓, clearing **`None`**, exits `True` | **INERT** |

**D78 is the one worth re-checking rather than inheriting, and it holds.** MISO is the only ISO in
the campaign that satisfies D78's *first* arming condition — `retirement_sector_gate = True`,
arriving through `iso_configs.py:1100`'s `default_scenario_overrides`. Its second condition is a
clearing-armed ISO, and MISO resolves `capacity_market_supply_clearing_by_iso = None`. The
inertness is **asserted by test**, not argued: `tests/unit/model/test_capacity.py:7250`
(`test_exit_exempt_is_byte_identical_to_exempt_when_the_clearing_is_off`, capx D78 T2) names
"MISO's armed keeper posture" explicitly and asserts the whole screen output — pipeline rows,
retired, `floor_retained`, state, survivors — is byte-identical under both decision rules. The
cache epoch entry (`results/cache.py`, "Epoch 2026-09-06d") reaches the same conclusion from the
other side: *"every MISO bundle with the gate on … the clearing is off there, and the D78
construction is byte-identical with the clearing off"*. D81's own epoch entry ("2026-09-06e")
scopes its blast radius to *"forecast mode on an ISO whose `capacity_market_supply_clearing_by_iso`
row is on (PJM alone at this date)"* — MISO is not in it.

**The three MISO fields the G-DRIFT window added are OFF on all three legs, and inert by
construction:**

| field | resolved | why inert |
|---|---|---|
| `miso_gas_marginal_commodity_pricing` | `False` | `apply_miso_gas_marginal_commodity` returns `None` at its first statement (`basis/miso.py:482`); `resolve_fuel_prices` then takes the incumbent `apply_miso_winter_citygate_daily` branch verbatim (`fuel/resolve.py:228–230`) |
| `miso_gas_variable_transport` | `False` | read only inside the armed branch; the unarmed guard's `ValueError` needs it `True`, so it does not fire |
| `miso_seam_neighbour_anchored_ladder` | `False` | `interchange/miso.py:305` — *"byte-identical when `False`"* |

`data/raw/reference/miso_ct_netload_drag.json` (miso-230) has **no consumer under
`src/market_sim/`** — verified: only `scripts/data/derive_miso_ct_netload_drag.py`,
`scripts/legitimacy_diagnostics.py` and a probe read it.

**Also unchanged in the window:** `scripts/run_ces_leg.py` and
`configs/scenarios/miso_scenario_base_2026_2030.yaml` — **0 lines each**. The driver is not a
variable.

**Verdict: MISO's pre-vs-post difference IS the CCS repair (D77 + D65-B) and nothing else.**

---

## 2. Phase 0 (zero LP) — I reproduce all three keys

Resolved exactly as `runner.run_scenario_iso` does (`runner.py:1384–1423`): `matrix_configs(base,
sweep)` → `resolve_policy_bundle` → `set_caiso_fsno_partition(False)` → `apply_iso_scenario_defaults`
→ `.cache_key()`. A naive `config.cache_key()` in a fresh process does **not** reproduce the solve's
key; this chain does.

| case | pre-fix key (committed `run_config.json`) | key at THE PIN (computed here) | charter's declared PIN key | match |
|---|---|---|---|---|
| REF | `b08a51a33ab6bb9d` | **`f1b3caa22b3f14ff`** | `f1b3caa22b3f14ff` | **YES** |
| LOAD-HI | `6f4fff944c9b5528` | **`9688b06c1b0a5a54`** | `9688b06c1b0a5a54` | **YES** |
| LOAD-HI-ORGANIC | `eca5bcfb14a379ad` | **`b87deb7735c242a0`** | `b87deb7735c242a0` | **YES** |

Both columns reproduce independently: the pre-fix keys are read back out of the three committed
`run_config.json` files and match the charter's table; the PIN keys are computed at THE PIN and
match the charter's table. **My base is THE PIN.**

Why they move: capx D65-B changes `ccs_retrofit_vom_adder` 8.0 → **2.95**, which is not a
`_CACHE_KEY_OPTIONAL_FIELDS` member and so re-keys unconditionally. D77 alone would not have moved
them — that is the STATUS doc's blocker, and it is dead at this pin.

**Resolved case fields, measured:**

| field | REF | LOAD-HI | LOAD-HI-ORGANIC |
|---|---|---|---|
| `demand_growth_path` | mid | high | high |
| `datacenter_load_path` | mid | high | mid |
| `electrification_path` / `carbon_price_path` | off / **zero** | off / zero | off / zero |
| `federal_ces_enabled` / `voluntary_clean_demand_path` / `mass_cap_enabled` | False / off / False | idem | idem |
| `ccs_retrofit_vom_adder` | **2.95** | 2.95 | 2.95 |
| `ccs_retrofit_fixed_cost_co2_scaling` / `_capex_co2_scaling` | **True** / True | True / True | True / True |
| `ccs_retrofit_capture_rate` / `_available_year` | **0.9** / 2028 | 0.9 / 2028 | 0.9 / 2028 |
| `mode` / `start_year` / `end_year` | forecast / 2026 / 2030 | idem | idem |

**`carbon_price_path = "zero"`** is the fact that sizes the prediction: a mis-rated
`emission_rate_co2` reaches marginal cost only through the carbon adder, so in MISO the repair is
an accounting correction plus whatever the retrofit screen does with it — not the large merit-order
re-ordering NEISO/NYISO/CAISO will show.

---

## 3. The pre-fix control — the committed bundle IS the control (rule 29(b) form 4)

Read from the three committed `full_horizon_summary.json` files. **No control solve is spent.**

| case | year | CO2 Mt | CCS TWh | CCS MW | LW $/MWh | peak GW | total TWh |
|---|---|---|---|---|---|---|---|
| REF | 2026 | 368.5353 | 0.0000 | 0.0 | 44.60 | 134.61 | 717.969 |
| REF | 2027 | 371.1727 | 0.0000 | 0.0 | 53.79 | 139.42 | 757.878 |
| REF | 2028 | 382.4341 | **0.0000** | **0.0** | 91.94 | 144.63 | 800.134 |
| REF | 2029 | 390.0939 | 2.0175 | 334.5 | 90.71 | 150.26 | 844.725 |
| REF | 2030 | **412.6343** | 2.5047 | 334.5 | 206.36 | 156.35 | 890.520 |
| LOAD-HI | 2026 | 387.0428 | 0.0000 | 0.0 | 59.63 | 141.82 | 756.112 |
| LOAD-HI | 2027 | 406.8978 | 0.0000 | 0.0 | 106.33 | 149.99 | 818.761 |
| LOAD-HI | 2028 | 434.0574 | 0.0000 | 0.0 | 301.08 | 159.13 | 884.284 |
| LOAD-HI | 2029 | 458.0065 | 2.5693 | 334.5 | 473.62 | 169.32 | 952.851 |
| LOAD-HI | 2030 | **485.4964** | 3.7192 | 484.1 | 1073.91 | 180.65 | 1003.096 |
| ORGANIC | 2026 | 387.0428 | 0.0000 | 0.0 | 59.63 | 141.82 | 756.112 |
| ORGANIC | 2027 | 406.8513 | 0.0000 | 0.0 | 109.04 | 150.97 | 818.722 |
| ORGANIC | 2028 | 433.6667 | 0.0000 | 0.0 | 329.94 | 161.09 | 884.013 |
| ORGANIC | 2029 | 457.3120 | 2.5693 | 334.5 | 482.68 | 172.26 | 952.421 |
| ORGANIC | 2030 | **485.4276** | 3.7192 | 484.1 | 1047.14 | 184.56 | 1004.068 |

**Pre-fix ΔCO2 (LOAD-HI − REF) at 2030 = 72.8621 Mt.** Pre-fix invariant FAIL set: **{I3, I7, I12}**
on all three legs, 14 scored. Wall 1577.7 / 1567.8 / 1565.0 s; peak RSS 9884 / 9872 / 9869 MB.
Pre-fix `git.sha`: REF `6f18377f`, LOAD-HI `2ed69a34`, ORGANIC `9170899f`, all `dirty=False`, all
pre-D77.

**Two properties of this control that shape the gates:**

1. **The cohort is EMPTY until 2029.** 0.0 TWh and 0.0 MW of `gas_cc_ccs` in 2028, even though
   `ccs_retrofit_available_year = 2028`. So G1's identity table will be **empty-but-valid for
   2026–2028**, and I will report it as empty rather than as a vacuous PASS.
2. **LOAD-HI and LOAD-HI-ORGANIC carry IDENTICAL CCS pre-fix** — 2.5693 TWh / 334.5 MW at 2029 and
   3.7192 TWh / 484.1 MW at 2030, to the digit. Whether that survives the repair is a §5 report item.

**Zero-carbon control rows for G3** (TWh, identical across all three arms in 2026 **and** 2027):
nuclear **90.198884**, hydro **9.292516**, wind **94.368276**, solar **9.200799**.

---

## 4. Execution — the recipe, unchanged from the charter

**Precondition, discharged before the first solve:** `data/clean` is DERIVED and gitignored, so a
fresh container has none and `run_scenario_iso` hard-fails on the MISO `confirmed-retirements` clean
partition. `PYTHONPATH=. uv run python scripts/regenerate_clean.py` runs first (started at the top of
this session, alongside this phase 0).

Three legs, **one at a time, nothing else solving** — MISO measured 78.5 min / 15 solve-years and
**9.65–9.88 GB peak RSS on a 15 GB box**, so rule 12's one-invocation cap is necessary, not cautious.

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_ces_leg.py \
    --config configs/scenarios/miso_scenario_base_2026_2030.yaml \
    --matrix configs/scenario_campaign_matrix.yaml \
    --case <REF|LOAD-HI|LOAD-HI-ORGANIC> --campaign scn-campaign-load-2026-09-06 \
    --out-dir results/scn-campaign-load-2026-09-06-r2/MISO/<CASE>
```

Exactly the driver the load lane used. **Not** `run_full_horizon.py`: its `--out-dir` cache redirect
is real but unreachable from a campaign leg (`run_ces_leg.run_leg` hard-codes `redirect_cache=False`),
and driving through it would build the config from `reference_config()` instead of the campaign base
YAML + `matrix_configs` — a config-divergence risk under a same-id re-registration. Logs go to the
session scratchpad, never into the results tree, so no `.gitignore` change is owed. Every solve is
HEAD-guarded (`[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90`); `git fetch`/rebase happen **between**
legs, never during one.

**Three independent cache isolations, each provable:** (1) a new out-dir per leg
(`…-r2/MISO/<CASE>/`), so nothing is ever written into the pre-fix tree; (2) **the key itself moved**
(§2) — the decisive one, and a measurement; (3) `results/MISO/` **does not exist** on this container
(verified pre-solve: the directory is absent, all three PIN keys absent). The WS-4c harness helper
that links arm bundles into a shared cache root is **never** used.

---

## 5. STOP gates and predictions — pre-registered, scored as written

Gates are **structural and STOP-only**. A PASS means only "the mechanism did what its own arithmetic
says"; it promotes nothing and contributes to no determination (rules 1 `[R-STRUCT]`, 29 `[R-SCREEN]`).

| # | gate | STOP condition |
|---|---|---|
| **G1** | **identity** (ruling S5's paired check at model grain; D77 §4b gate 1) — for every retrofitted unit-year, `emission_rate_co2 == old_emission_rate × (1 − 0.90)` to rel. tol **1e-9**, and `fuel_type == "gas_cc_ccs"`. Scored on REF, reported for the load arms. **Zero LP**: the cumulative cohort and each host's `old_emission_rate` come from `results/MISO/<key>/evolution_<year>.json`'s `ccs_retrofits` rows (D65-B-R step 0 persists them — `evolve.py::_CCS_RETROFIT_LEDGER_SCALING_FIELDS`); the LP's own per-unit rate from `results.outputs.read_fleet_context(...)` → `emission_rate` zipped with `unit_ids` / `fuel_types` | any converted unit off the identity |
| **G2** | **confinement** — (a) inside the post-fix bundle, every unit NOT in the cumulative cohort holds the same `emission_rate` in every year as in 2026; (b) 2026 and 2027 generation-by-fuel identical to the pre-fix bundle for **every** fuel | a non-cohort unit's rate moves, or a 2026/2027 fuel row moves |
| **G3** | **pre-2028 inertness, measured** — nuclear / hydro / wind / solar generation identical to §3's control in 2026 and 2027 | any 2026/2027 zero-carbon row moves |
| **G4** | **no collateral flip** — no non-target load-bearing invariant flips PASS → FAIL vs the pre-fix leg (pre-fix FAIL set {I3, I7, I12} on all three) | a flip whose cause is **not** re-ordered dispatch. A flip *caused by* re-ordered dispatch is **reported with its cause named**, not a STOP |
| **G5** | **cache-hit proof**, per leg, all five: (a) `results/MISO/<PIN key>/` absent pre-solve; (b) `run_config.json` `cache_key` = the §2 PIN key; (c) `git.sha` = THE PIN or a descendant with zero solve-path diff, `git.dirty == false`; (d) `total_wall_s` is a solve's with per-year `wall_s` for all five years; (e) the 2029–2030 `gas_cc_ccs` rate is `measured host × 0.10`, not ~0.37 | any leg failing a–e. **A leg reproducing the pre-fix trajectory to the digit is a CACHE HIT and a STOP — reported, never registered** |

**G2(a)/(b) is the available substance, and I state the limit plainly rather than dressing it up:**
a **per-unit diff against the pre-fix bundle is NOT computable**. `results/<ISO>/` is gitignored and
the pre-fix parquets were never materialized on this fresh container, so the committed pre-fix record
is slim (`full_horizon_summary.json` + `run_config.json`) and carries no per-unit rates. G2(a) tests
confinement **within** the post-fix bundle against its own 2026 baseline; G2(b) tests the whole
2026/2027 fuel vector against the committed control. Together they are weaker than a per-unit diff
and stronger than G3 alone — that is the honest description.

### 5.1 EXPLICITLY NOT A STOP (pre-declared)

The retrofit **set** moving (capacity or membership); the merit order re-ordering; CO2 falling by any
magnitude; the LOAD-HI delta moving; the 2030 retrofit cohort **shrinking** because correctly-rated
CCS depresses the price that justified the next retrofit (D77 §4.3 measured exactly that on NEISO).
All are the repair working.

### 5.2 Predictions — scored as written, misses at full magnitude

| # | prediction | basis |
|---|---|---|
| **P1** | **2030 REF CO2 FALLS from 412.634 Mt, by order 0.5–2 Mt** | 2.5047 TWh × ≈0.37 t/MWh × 0.9 ≈ 0.83 Mt of pure accounting, plus a small retrofit-screen response. Carbon is **0** in MISO, so the merit order barely moves |
| **P2** | **LOAD-HI ΔCO2 FALLS by 0.2–1 Mt** from its pre-fix **72.8621 Mt** | the arms carry unequal CCS at 2030 (REF 2.5047 vs LOAD-HI 3.7192 TWh), so ≈1.21 TWh × 0.37 × 0.9 ≈ 0.40 Mt does **not** cancel |
| **P3** | **2026 and 2027 do not move at all** | `apply_ccs_retrofit` returns at `year < 2028`; G3 is the empirical check |
| **P4** | **No new invariant FAIL ident appears** — the set stays {I3, I7, I12} on all three legs | D67-ARM/D78/D81 are all inert here (§1), so the only channel is the retrofit set moving capacity |
| **P5** | *(report item, not a prediction)* whether LOAD-HI and LOAD-HI-ORGANIC still carry **identical** `gas_cc_ccs` after the repair | they do pre-fix, to the digit (§3) |

**The one I most expect to be wrong is P1's band.** D65-B cuts the capture VOM adder 8.0 → 2.95 and
scales the fixed-cost legs by the host's captured-CO2 factor — both make retrofits *easier* — while
D77 works the other way at the margin. A larger 2029/2030 cohort would push the fall past 2 Mt; that
would be a miss on the band and **not** a gate failure.

---

## 6. Duties this lane accepts

- **No default moves, no knob moves, no `ScenarioConfig` field added, no new case, no solve outside
  these three, never a year past 2030. DOF ledger: ZERO free parameters.** No `authorized_price_tuning`
  (rule 1's carve-out is a backcast offer-curve channel; a forecast lane does not touch it).
- **Consume, never edit:** everything under `src/`, `scripts/`, `configs/`, and every other ISO's
  files. **Not touched:** the parent lane's `PRECOMMIT-`/`FINDING-scn-ws5a-resolve-2026-09-06.md`,
  `FINDING-scn-ws5a-load-synthesis-2026-09-06.md`, `STATUS-scn-ws5a-load-2026-09-06.md`, the
  readiness plan §5.1, the desk ledger, `program-status.json`, `ff-verdicts.json`, the backcast
  registry, any ISO shard but MISO's. Rollup numbers are routed to the parent lane **through this
  lane's FINDING**, never by editing the synthesis. Anything outside these regions ⇒ **STOP and route
  to SCN-DESK in the FINDING**.
- **Rule 15 / forecast plan §7.5:** re-registration into the **forecast** namespace, same campaign,
  the **same three run ids** (`miso-2026-2030-scn-campaign-load-2026-09-06-{ref,load-hi,load-hi-organic}`).
  Only the sidecar's `git_sha`, key provenance and out-dir change, and the FINDING says so per leg.
- **Rule 26 `[R-DELETE]`:** each re-registration commit **deletes** that case's pre-fix slim artifacts
  under `results/scn-campaign-load-2026-09-06/MISO/<CASE>/` — a stale bundle at a valid key is a
  re-armable wrong answer; git history is the record.
- **Invariant declarations in the same commit as each re-registration**
  (`frontend/data/hindcast/invariant-failures.json`), **including deleting** any declared ident the
  re-solve no longer fails. Append-only shared state: **MISO's keys only**, rebase before the last
  commit. `scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast` must be
  **EXIT 0** before every push (it is EXIT 0 on main today).
- **Rule 27 `[R-PUSH]`:** no existing source file ≥300 lines is rewritten; every push touching one is
  fetch-back verified (line count + hash).
- **Rule 29(c) does not apply:** these three are **registered campaign arms**, not screen or control
  bundles, so DELETE-BEFORE-MERGE is not owed on them. No screen bundle and no control bundle is
  produced (§3: the control is the committed pre-fix bundle).
- **Rule 28(b):** the `datacenter_load_block` cell of `docs/codebase-site/data/mechanism-matrix/MISO.js`
  is re-stamped with the post-fix evidence as the **LAST** commit after rebase — one appended line,
  no verdict letter moved. Rule 28(c) is not engaged: no `ScenarioConfig` field is added.
- **Backcast byte-identity: untouched** — forecast-mode only, no default moved by this lane.
- **No CI workflow is created.** Every solve runs in-session.
- **Then:** re-run `scripts/report_scenario_deltas.py` for MISO and refresh
  `results/scn-campaign-load-2026-09-06/MISO/{bundle,report}/`. The whole-campaign
  `collate_scenario_campaign.py` is the **parent lane's** to run, not this one's.
