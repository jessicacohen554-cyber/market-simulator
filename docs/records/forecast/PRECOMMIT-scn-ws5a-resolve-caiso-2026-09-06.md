# PRECOMMIT — SCN-WS5A-RESOLVE-CAISO: CAISO's three legs re-solved at THE PIN

**Lane** SCN-WS5A-RESOLVE-CAISO · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-ws5a-resolve-caiso-0rkx2k` · **Data profile** `caiso` (full clone —
`hydrate_data.py --profile caiso` reports every blob already local) ·
**Campaign** `scn-campaign-load-2026-09-06` (unchanged — same ids, same cases, same reference
case `REF`) · **Charter** SCN-DESK ledger §0 r#13 (ruling **S8**, card D-10) + **S5**'s
model-grain paired check, split out by the owner so CAISO and MISO run in parallel with the
parent lane (rule 12 `[R-PARALLEL]`: one per-plant multi-zone ISO per box) ·
**Parent** `PRECOMMIT-scn-ws5a-resolve-2026-09-06.md` (branch
`claude/scn-ws5a-resolve-post-d77-m8m5ft`), whose §1 G-DRIFT audit this lane **inherits and
does not rewrite** · **Predecessor** `FINDING-scn-ws5a-load-caiso-2026-09-06.md` and
`STATUS-scn-ws5a-load-2026-09-06.md`.

**Pushed before the first solve** (rule 29 `[R-SCREEN]`). Every number below is zero-LP: a
resolved config at THE PIN, a committed pre-fix artifact, or arithmetic on the two. Nothing
here is revised after a solve; §5's predictions are scored as written, misses at full magnitude.

---

## 0. THE PIN — inherited, not chosen

```
bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
```

`origin/main` at the parent lane's PRECOMMIT. This lane branched off **that sha**, not off
current `main`, so every leg of the campaign sits at one base. Ancestry re-verified here with
`git merge-base --is-ancestor` rather than inherited on assertion:

| required ancestor | what it is | ancestor of THE PIN |
|---|---|---|
| `fc583339` | capx **D77** merge (the CCS retrofit emission-rate repair) | **YES** |
| `b1f77621` | capx **D65-B** merge (Acts A+B, the re-key event) | **YES** |
| `1cc45bb2` | the load campaign's frozen pre-fix pin | **YES** |

**THE PIN IS NOT MOVED AFTER THE FIRST SOLVE.** Anything landing on `main` after it is recorded
in the FINDING as post-pin, never retro-fitted and never used to re-read a result. `git fetch` /
rebase happen **between** legs, never during one; every solve is wrapped in a HEAD GUARD
(`[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90`).

## 0.1 Bottom line before any LP

1. **All three CAISO keys re-key at THE PIN, reproduced independently** (§2). The STATUS doc's
   cache blocker — *"D77 moves no cache key, so a re-solve HITS the pre-fix bundle"* — is
   defeated by construction here, and that is a measurement rather than an assumption.
2. **For CAISO the LIVE set is exactly {D77, D65-B}** (§1, measured on this lane's own resolved
   configs). CAISO's pre-vs-post difference IS the CCS repair and nothing else — unlike PJM,
   where the parent lane declares D67-ARM and D81 as additional confounds.
3. **16.2 % of CAISO's 2030 REF CO2 level is mis-rated `gas_cc_ccs`** (§3 baseline; the
   predecessor FINDING §4). CAISO carries the campaign's largest CCS fleet — 45.16 TWh at 2030
   in REF, 51.85 TWh in LOAD-HI — so the correction does **not** cancel out of the LOAD-HI delta
   (§5, prediction P-B).
4. **The default cache is empty.** `results/CAISO/` does not exist on this container (§3), so no
   pre-fix parquet bundle is reachable at any key, moved or not.

---

## 1. The CAISO-only LIVE-set verification (rule 29(b))

The G-DRIFT audit `1cc45bb2..bdfb3095` is the parent lane's, recorded in its PRECOMMIT §1
**before any arm was solved**: 34 non-merge solve-path commits, four LIVE mechanisms — capx
**D77** and **D65-B** (by design, all five re-solved ISOs) and, **PJM only**, **D67-ARM** and
**D81** — and 30 INERT commits each with a stated reason. **This lane does not re-audit it.**

What this lane *does* owe, and did: verify on **its own resolved CAISO configs** that the two
PJM-only mechanisms and the sector-gate seam are unarmed here, so the parent's PJM-only
classification actually holds for CAISO. Measured on all three legs, resolved exactly as
`runner.run_scenario_iso` does:

| field | measured (all three CAISO legs) | consequence |
|---|---|---|
| `capacity_adequacy_requirement_published_by_iso` | **`None`** | capx **D67-ARM** cannot arm — it is a `{iso: bool}` gate reached only through PJM's `default_scenario_overrides` |
| `capacity_market_supply_clearing_by_iso` | **`None`** | capx **D81**'s epoch predicate (forecast × clearing-armed × `fossil_announced_exits_enabled`) fails on its second conjunct; capx **D78**'s sector-gate offer seam fails on the same one |
| `retirement_sector_gate` | **`False`** | capx **D78** fails on its first conjunct too — CAISO satisfies neither half |

Four further INERT classifications the parent lane made generically, re-measured on the CAISO
legs specifically because they are the ones a CAISO artifact could arm:

| field | measured | the commit it disarms |
|---|---|---|
| `caiso_offer_surface_conditional` | **`False`** (with `offer_curve_by_group = {}`) | `df277e89` / `c274f1a0` / `48bcd0ec` — the CAISO measured offer-surface artifact pair |
| `hindcast` / `capacity_screen_peak_measured_hindcast` | **`False`** / **`False`** | capx **D76** (gate is the conjunction of both) |
| `capacity_no_default_cap_convention_by_iso` | **`None`** | capx **D74** |
| `mass_cap_tons_by_year` / `mass_cap_enabled` | **`None`** / **`False`** | SCN-CAP (`75a1a732`, `256fc7d1`, `89b0a9f4`) |
| `nyiso_ct_peaker_bands_measured`, `nyiso_gas_bridge_startup_aware`, `pjm_vre_accreditation_vintage` | **`False`** ×3 | nyiso-199/200/201, capx D75-R |
| `set_overrides` | **`{}`** (no `--set` on the invocation; the case rides `matrix_configs`) | capx D60-R4 `5d639e31` — both forms short-circuit on empty |

**Verdict for CAISO: form 4 is VALID and the LIVE set is `{D77, D65-B}`.** The committed pre-fix
CAISO bundle IS the control; no control solve is earned or spent.

---

## 2. Phase 0 (zero LP) — the three keys, reproduced independently

Resolved exactly as `runner.run_scenario_iso` does (`runner.py:1384-1423`):
`matrix_configs(base, sweep)` → `resolve_policy_bundle` → `set_caiso_fsno_partition` →
`apply_iso_scenario_defaults` → `.cache_key()`. A naive `config.cache_key()` in a fresh process
does **not** reproduce the solve's key, so the whole chain is walked.

| case | pre-fix key (committed `run_config.json`) | key at THE PIN | matches parent §3 |
|---|---|---|---|
| REF | `54a70e9a6e396cad` | **`2d16a246bb372e4a`** | **YES** |
| LOAD-HI | `7687ac2d1265ec14` | **`86bfde6ed2896b99`** | **YES** |
| LOAD-HI-ORGANIC | `a3472da093262e47` | **`ff8c04bc4eef6605`** | **YES** |

All three move, for the reason capx D65-B's epoch entry states: `ccs_retrofit_vom_adder`
8.0 → **2.95** is not a `_CACHE_KEY_OPTIONAL_FIELDS` member and re-keys unconditionally. **A key
that did not reproduce the parent's value would have been a STOP** (it would mean this lane's
base is not THE PIN); none did.

Resolved case fields, measured on all three legs:

| field | REF | LOAD-HI | LOAD-HI-ORGANIC |
|---|---|---|---|
| `demand_growth_path` | mid | high | high |
| `datacenter_load_path` | mid | high | mid |
| `electrification_path` | off | off | off |
| `carbon_price_path` | zero | zero | zero |
| `federal_ces_enabled` | False | False | False |
| `voluntary_clean_demand_path` | off | off | off |
| `mass_cap_enabled` | False | False | False |
| `ccs_retrofit_vom_adder` | **2.95** | 2.95 | 2.95 |
| `ccs_retrofit_capex_co2_scaling` | True | True | True |
| `ccs_retrofit_fixed_cost_co2_scaling` | **True** | True | True |
| `ccs_retrofit_capture_rate` | **0.9** | 0.9 | 0.9 |
| `ccs_retrofit_available_year` | **2028** | 2028 | 2028 |
| `mode` / `start_year` / `end_year` | forecast / 2026 / 2030 | idem | idem |

`carbon_price_path = "zero"` on every leg: **CAISO's CARB pricing enters through the ISO's own
policy configuration, not through the campaign's carbon axis**, which is why the predecessor
FINDING's "CARB priced" framing and this table are consistent rather than in conflict.

---

## 3. The cache recipe, the pre-solve state, and the pre-fix baseline

**Three independent isolations, each provable:**

1. **A NEW out-dir per leg** — `results/scn-campaign-load-2026-09-06-r2/CAISO/<CASE>/`. Nothing
   is written into the pre-fix tree, so a mis-step cannot overwrite the control being
   differenced against.
2. **THE KEY ITSELF MOVED** (§2) — a post-pin solve computes a key no pre-fix bundle occupies.
3. **THE DEFAULT CACHE IS EMPTY** — `results/CAISO/` **does not exist** on this container
   (recorded pre-solve, gate **G5(a)**); all six keys above, pre-fix and PIN, are ABSENT. The
   tree is gitignored and this container was cloned fresh, so only the committed slim artifacts
   (`full_horizon_summary.json` + `run_config.json`) are present.

**NEVER used:** the WS-4c harness helper that links arm bundles into the shared cache root. No
pre-fix bundle is linked, copied or moved into any cache root at any point.

**Precondition executed:** `data/clean` is DERIVED and gitignored, so a fresh container has none
and `run_scenario_iso` hard-fails with *"confirmed-retirements: clean partition for CAISO is
absent while `confirmed_exits_enabled` is on in forecast mode"*.
`PYTHONPATH=. uv run python scripts/regenerate_clean.py` was started **before** this PRECOMMIT
was written and must complete before the first solve.

### 3.1 Driver — `run_ces_leg.py`, per leg, one at a time

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_ces_leg.py \
    --config configs/scenarios/caiso_scenario_base_2026_2030.yaml \
    --matrix configs/scenario_campaign_matrix.yaml \
    --case <REF|LOAD-HI|LOAD-HI-ORGANIC> --campaign scn-campaign-load-2026-09-06 \
    --out-dir results/scn-campaign-load-2026-09-06-r2/CAISO/<CASE>
```

Exactly the driver the load lane used; `run_ces_leg.py` is **0 lines changed** in the whole
G-DRIFT window, so the driver is not a variable. `run_full_horizon.py` is **not** substituted:
its `--out-dir` cache redirect is real (`solve_and_summarize`, ~:736–750) but unreachable from a
campaign leg (`run_ces_leg.run_leg` hard-codes `redirect_cache=False`), and driving through it
would build each config from `reference_config()` instead of the campaign base YAML expanded
through `matrix_configs` — a config-divergence risk under a **same-id re-registration** whose
whole point is that the case is unchanged. Logs go to the session scratchpad, never into the
results tree, so no `.gitignore` change is owed. Measured cost from the predecessor: ~65 min /
15 solve-years / 4.87 GB peak RSS. Legs run **one at a time**; nothing else solves on this box.

### 3.2 The pre-fix baseline this lane differences against (committed, sha `0bf1d7f8`, `dirty=false`)

| case | year | CO2 Mt | `gas_cc_ccs` TWh | `gas_cc_ccs` MW | lw $/MWh | gen TWh |
|---|---|---|---|---|---|---|
| REF | 2026 | 31.3061 | 0.000 | 0.0 | 55.71 | 239.35 |
| REF | 2027 | 34.5149 | 0.000 | 0.0 | 55.95 | 247.13 |
| REF | 2028 | 33.3190 | 13.633 | 2903.1 | 59.41 | 255.36 |
| REF | 2029 | 31.3551 | 21.883 | 5899.9 | 62.66 | 264.02 |
| REF | **2030** | **31.1595** | **45.161** | 8687.0 | 75.29 | 272.48 |
| LOAD-HI | 2028 | 40.1176 | 14.960 | 2980.6 | 65.45 | 271.74 |
| LOAD-HI | 2029 | 39.8088 | 25.979 | 5957.0 | 71.83 | 285.25 |
| LOAD-HI | **2030** | **41.3902** | **51.849** | 8936.3 | 90.65 | 298.59 |
| ORGANIC | **2030** | **41.5031** | **51.372** | 8936.3 | 93.68 | 298.56 |

Pre-fix **ΔCO2 (LOAD-HI − REF)**: 2026 **+2.9948** · 2027 **+4.8146** · 2028 **+6.7986** ·
2029 **+8.4537** · 2030 **+10.2307** Mt.

Pre-fix invariant FAIL sets: **REF `{I7, I12}`**; **LOAD-HI `{I3, I7, I12}`**;
**LOAD-HI-ORGANIC `{I3, I7, I12}`**. No WARNs.

---

## 4. STOP gates — structural, kill-only, never gated on a residual

Pre-registered. A gate PASS means only *"the mechanism did what its own arithmetic says"*; it
promotes nothing and contributes to no determination (rules 1 `[R-STRUCT]`, 29 `[R-SCREEN]`).

| # | gate | STOP condition |
|---|---|---|
| **G1** | **IDENTITY** (ruling S5's paired check at model grain; capx D77 §4b gate 1). Scored on the re-solved **REF**, reported for the load arms. For every retrofitted unit-year, `emission_rate_co2 == host's pre-conversion measured CAMPD rate × (1 − 0.90)` to rel. tol **1e-9**, and the unit's `fuel_type` is `gas_cc_ccs`. **Zero LP, no replay:** the cumulative cohort and each host's `old_emission_rate` come from `results/CAISO/<key>/evolution_<year>.json`'s `ccs_retrofits` rows (capx D65-B-R step 0 persists the per-host record); the LP's own per-unit rate comes from `read_fleet_context(cache.get_cache_path("CAISO", key, year))` → `FleetContext.emission_rate` zipped with `.unit_ids` / `.fuel_types` | ANY unit off the identity |
| **G2** | **CONFINEMENT.** (a) within the post-fix bundle, every unit **not** in the cumulative cohort holds the same `emission_rate` in every year as in 2026; (b) 2026 and 2027 generation-by-fuel is identical to the committed pre-fix bundle for **EVERY** fuel, not just the zero-carbon ones | a non-cohort unit's rate moves; or any 2026/2027 by-fuel row moves |
| **G3** | **PRE-2028 INERTNESS, MEASURED.** Nuclear, hydro, wind and solar generation identical to the pre-fix bundle in 2026 and 2027. (`apply_ccs_retrofit` returns at `if year < ccs_retrofit_available_year` = 2028, so this is the empirical check that **both** D77 and D65-B are confined to 2028+) | any 2026/2027 zero-carbon row moves |
| **G4** | **NO COLLATERAL FLIP.** No non-target load-bearing invariant flips PASS → FAIL vs the pre-fix leg. Pre-fix FAIL sets: REF `{I7, I12}`, both load arms `{I3, I7, I12}` | a flip whose cause is **not** re-ordered dispatch. A flip **caused by** re-ordered dispatch is **REPORTED WITH ITS CAUSE NAMED**, not a STOP — the FINDING says which |
| **G5** | **CACHE-HIT PROOF**, per leg, all five: (a) `results/CAISO/<PIN key>/` did not exist before the solve (`ls` recorded pre-solve — **done, §3**); (b) the leg's `run_config.json` `cache_key` equals the §2 PIN key; (c) its `git.sha` is THE PIN or a descendant with a **zero** solve-path diff, and `git.dirty == false`; (d) `total_wall_s` is a solve's, not a cache read's, with per-year `wall_s` for all five years; (e) its 2028–2030 `gas_cc_ccs` rate is `measured host × 0.10`, not ~0.37 | any leg failing a–e. **A leg whose trajectory reproduces the pre-fix bundle to the digit is a CACHE HIT and a STOP** — reported, never registered |

**G2(b) is stated honestly, not overclaimed.** A **per-unit** diff against the pre-fix bundle is
**NOT computable**: `results/<ISO>/` is gitignored and the pre-fix parquets were never
materialized on this fresh container, so the committed record is slim
(`full_horizon_summary.json` + `run_config.json`). G2(a) — non-cohort rate invariance **within**
the post-fix bundle — and G2(b) — the full by-fuel 2026/2027 identity **against** the pre-fix
summary — are the available substance, and they are a different and weaker claim than a
per-unit pre-vs-post diff would be. They are recorded as what they are, not as a restatement of it.

**Explicitly NOT a STOP, pre-declared:** the retrofit **set** moving (capacity or membership),
the merit order re-ordering, CO2 falling by any magnitude, the LOAD-HI delta moving, or the 2030
retrofit cohort **shrinking** because correctly-rated CCS depresses the price that justified the
next retrofit (capx D77 §4.3 measured exactly that on NEISO). All of these are the repair working.

---

## 5. Predictions — pre-declared, scored as written, misses at full magnitude

Inherited verbatim from the parent PRECOMMIT §6 (CAISO rows) — this lane does not restate them
more favourably.

**P-A (level).** CAISO's 2030 REF CO2 level **FALLS** from **31.160 Mt** by order **3–8 Mt** —
the 16.2 % accounting correction (45.161 TWh × ~0.11 t/MWh over-rating ≈ 5.04 Mt) plus a
CARB-priced dispatch response.

**P-B (the delta does NOT cancel).** The **LOAD-HI ΔCO2 FALLS by 1–3 Mt** from its pre-fix
**10.231 Mt**, because the arms carry unequal CCS generation at 2030 (REF 45.16 vs LOAD-HI
51.85 TWh, an arm gap of **+6.69 TWh**), so the correction does not cancel out of the delta.

**P-C (the mechanism's sign and confinement).** The 2028–2030 `gas_cc_ccs` emission rate falls by
exactly 10× at the unit level (G1), and CO2 falls at the ISO level in every year from 2028.
**2026 and 2027 do not move at all** (G2(b), G3).

**P-D (no new FAIL class).** No re-solved CAISO leg gains an invariant FAIL ident absent from
both its own pre-fix set and the ISO's other arms. CAISO is named in the parent's second-tier
risk group (already carrying I7+I12; a changed retrofit set moves capacity), so an I3/I7/I12
movement is anticipated and is not a new class.

**P-E (the retrofit set, the one I most expect to be wrong).** D65-B cuts the capture VOM adder
8.0 → 2.95 and scales the fixed-cost legs by the host's captured-CO2 factor, both of which
*improve* the screened uplift; D77 works the other way at the margin. I make **no directional
prediction** for CAISO's 2030 retrofit capacity (pre-fix 8,687.0 MW REF / 8,936.3 MW LOAD-HI) —
it is reported at whatever it lands, and either direction is pre-declared as not a STOP.

---

## 6. Duties this lane accepts

- **No default moves, no knob moves, no `ScenarioConfig` field added, no new case, no solve
  outside these three, never a year past 2030.** **DOF ledger: ZERO free parameters**; no
  `authorized_price_tuning` (rule 1's carve-out is a backcast offer-curve channel, untouched by
  a forecast lane).
- **Consume, never edit:** everything under `src/`, `scripts/`, `configs/`, and every other
  ISO's files. **Not touched:** the parent lane's `PRECOMMIT-`/`FINDING-scn-ws5a-resolve-*.md`,
  `FINDING-scn-ws5a-load-synthesis-*.md` (the parent owns its dated ADDENDUM),
  `STATUS-scn-ws5a-load-*.md`, the readiness plan §5.1, the desk ledger,
  `program-status.json`, `ff-verdicts.json`, the backcast registry, and any ISO shard but
  CAISO's. A needed change outside these regions is a **STOP** routed to SCN-DESK in the FINDING.
- **Rule 15 `[R-DASHBOARD]` / forecast plan §7.5:** re-registration is into the **forecast**
  namespace under the same campaign and the **SAME run ids**
  (`caiso-2026-2030-scn-campaign-load-2026-09-06-{ref,load-hi,load-hi-organic}`) — only the
  sidecar's `git_sha`, key provenance and out-dir change, stated per leg in the FINDING. The
  backcast registry is never touched.
- **Rule 26 `[R-DELETE]`:** each re-registration commit **deletes** that case's pre-fix slim
  artifacts under `results/scn-campaign-load-2026-09-06/CAISO/<CASE>/` in the same commit — a
  stale bundle at a valid key is a re-armable wrong answer, and git history is the record.
- **Invariant declarations in the same commit as each re-registration**
  (`frontend/data/hindcast/invariant-failures.json`), including **deleting** any declared ident
  the re-solve no longer fails. Only CAISO's keys are touched; rebase before the last commit.
  `scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast` must be **EXIT 0**
  before every push — it is EXIT 0 on `main` today and must stay so.
- **Rule 27 `[R-PUSH]`:** no existing source file ≥300 lines is rewritten; every push touching
  one is fetch-back verified (line count + hash).
- **Rule 29(c)** does not apply: the three legs are **registered campaign arms**, not screen or
  control bundles.
- **Rule 28(b) `[R-MECH-MATRIX]`:** CAISO's `datacenter_load_block` cell is re-stamped with the
  post-fix evidence as the **LAST** commit after rebase — **one appended line, no verdict letter
  moved**.
- **Backcast byte-identity: untouched** — forecast-mode only, no default moved by this lane.
- **No CI workflow is created.** Every solve runs in-session.
