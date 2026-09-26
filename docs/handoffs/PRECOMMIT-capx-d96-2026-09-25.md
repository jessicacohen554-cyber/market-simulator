# PRECOMMIT — capx D96: `neiso-t3` put back on ONE data vintage (post-F1)

**Lane:** capx **D96** · **Date:** 2026-09-25 · **Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:** `neiso`
**Branch:** `claude/capx-d96-neiso-t3-postf1`, fresh off `origin/main` **`c64e69ebeb2eb4c9e16106aa044b15285225393a`**
**Authority:** OWNER RULING **Q69** (2026-09-25, capx ledger §0bk / §3): *"Re-solve now."*
**Binding charter:** `docs/handoffs/capx-director-prompt-pack-2026-08.md` "D96" (a relaunch; the first
launch stayed PENDING for 11 h, never started, and was archived — nothing from it exists)
**Predecessors read:** `FINDING-capx-d94-2026-09-24.md` (whole) · `FINDING-capx-d92-2026-09-10.md` ·
`PRECOMMIT-capx-d92-2026-09-10.md` + ADDENDA A/B · `PRECOMMIT-capx-d94-2026-09-24.md` ·
`docs/handoffs/f1/RESULT-f1-backcast-heatrate-vintage-2026-09-24.md` + `results/cache.py`'s F1 epoch note

**PUSHED BEFORE ANY LP.** The recipe, the G-DRIFT audit, every prediction and the scoring rules are
fixed at this commit. The four shards are pinned to this commit's full 40-character SHA.

---

## 0. THE SCOPE IN ONE PARAGRAPH

capx D94 left `neiso-t3` on **two data vintages**: its FC-6 driver battery (`d94/`) is post-F1 (solved at
`924017c8`), while its primary bundle, its FC-6 paired arms and its FC-5 corridor table
(`d92/{base,carbon_plus25,gasup150,gaspm5}`) are pre-F1 (solved at `aac390a6`). This lane re-solves the four
D92 legs **on the D92 recipe, both pins included, with only the HEAD changed**, then re-scores `neiso-t3`
with the primary bundle, the paired block and the FC-5 table swapped onto `d96/` and the `d94/` driver
battery **kept**. The whole verdict then sits on one post-F1 vintage.

---

## 1. THE RECIPE — D92's, VERBATIM, WITH ONLY THE HEAD CHANGED

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
PYTHONPATH=.:src python3 scripts/run_full_horizon.py \
  --iso NEISO --start-year 2026 --end-year 2050 --golden-posture --full-solve-authorized \
  --no-ccs-retrofit-fixed-cost-co2-scaling --set ccs_retrofit_vom_adder=8.0 \
  [--set <arm override>] --out-dir results/ff-t3-neiso-golden/d96/<leg>
```

| leg | arm override (D92 PRECOMMIT §4, verbatim) | serves |
|---|---|---|
| `base` | — | primary bundle (FC-1…FC-4, FC-7, FC-8); FC-5 model basis; FC-6 paired base operand |
| `carbon_plus25` | `--set carbon_price_delta=25.0` | FC-6 P1 / P1.premise |
| `gasup150` | `--set gas_price_factor=1.5` | FC-6 P2 |
| `gaspm5` | `--set gas_price_factor=1.05` | FC-6 P3 |

**Both `neiso-t3` pins on every leg:** `ccs_retrofit_fixed_cost_co2_scaling=False` via the runner's own
`--no-ccs-retrofit-fixed-cost-co2-scaling` (a `reference_config` argument, applied before ISO-default
resolution) and `ccs_retrofit_vom_adder=8.0` via `--set` (recorded in `run_config.json` `set_overrides`).
Each shard verifies both off its solved `run_config.json` before it pushes.

### 1.1 The config, built at this HEAD at zero LP, is D94 `vre_short`'s config exactly

Each leg's config was built here exactly as the runner builds it (`run_full_horizon.main` with
`solve_and_summarize` stubbed → `resolve_policy_bundle` → `apply_iso_scenario_defaults`):

* `base` vs **`d94/vre_short`**'s recorded payload: **4 fields differ, 0 real** — `cc_block_summer_rating`,
  `ercot_partial_outage_day_guard`, `fleet_zone_vintage_coords`, `unit_outage_precod_clip`, each absent from
  the older payload and `False` here (schema growth). Proof they are key-inert: `head_key(vre_short payload,
  surface=True)` = **`dbef1ecac9596c90`** = the `base` key predicted below, to the character.
* `base` vs `d92/base`'s payload: 42 fields differ, all schema growth (the 38 D94 §2.1 listed plus the 4).
* Each arm differs from `base` in exactly its one override. All four resolve `ccs_retrofit_vom_adder=8.0`,
  `ccs_retrofit_fixed_cost_co2_scaling=False`.

### 1.2 Predicted keys (the runner's `ScenarioConfig.cache_key()` on the resolved config)

| leg | predicted key | D92 key (pre-F1) |
|---|---|---|
| `base` | **`dbef1ecac9596c90`** | `dd8203a8bf1546b9` |
| `carbon_plus25` | **`f66e7b51d3731465`** | `f00aa4b9148bc316` |
| `gasup150` | **`d3ff933838e3fb12`** | `51c20a5583394d8d` |
| `gaspm5` | **`8d23ff10a99c4a8a`** | `e8bcc0b30e6388b3` |

**Why none equals D94's `vre_short` literal `1be407901f4f8000`** though the config is identical: the NEISO
solve surface (`config/solve_surface.py`, capx D79) is now off its declaration on **seven** rows —
`GENERIC_BASE_OFFER_CURVE`, `LABELS`, `MAINTENANCE_MONTHLY_SHAPE`, `MIN_STABLE_PCT_PHYSICAL`,
`PLANT_CLASSES`, `RGGI_MEMBER_STATES_BY_YEAR`, `THERMAL_AVAILABILITY` — against **one** (`RGGI…`) at
`924017c8`. The six new rows are the coal-subclass change (§2). A key move is a hash fact, not a solve fact;
§2 is where it is decided whether any of those rows reaches a NEISO forecast number.

---

## 2. G-DRIFT — `924017c8` (D94's pin) → `c64e69eb` (this lane's base)

**Verdict: every hunk is INERT for a NEISO 2026–2050 forecast. No LIVE hunk. The key moves; the solve
should not.** Window: `git diff 924017c8 c64e69eb -- src/market_sim scripts/run_full_horizon.py scripts/lib
data/raw` — 49 code files (+3,391 / −234), ~250 `data/raw` paths. `scripts/run_full_horizon.py` itself is
unchanged. Audited hunk by hunk (delegated reader, checked here) **and measured at zero LP**:

* **Fleet probe (measured, not argued).** The NEISO forecast base fleet and `FleetArrays` for 2026 were built
  twice on this recipe — once from a `git archive` of `924017c8`, once at HEAD. **474 generators both times;
  every numeric array identical** (availability, pmax, min_gen, heat rates, …). The only differences are two
  string labels, `plant_group` and `efficiency_bin`, on Merrimack's three tranches: `COAL` → `COAL_BIT`.
* **Config probe.** The config-only payload hashes identically at both commits; §1.1 shows the leg configs
  are D94 `vre_short`'s payload plus four default-`False` schema-growth fields.

| file(s) | what changed | class | reason |
|---|---|---|---|
| `config/plant_taxonomy.py`, `data/coal.py`, `data/fleet/eia860.py:1821` | bare `COAL` class eliminated; every coal unit carries its subclass (owner, 2026-09-25) | INERT | Merrimack (plant 2364) already resolved to `bituminous` from EIA-923 receipts at the base; relabel only, fleet probe identical |
| `data/fleet/{arrays,campd_bins,assembly,__init__,withholding,offer_surfaces}.py` | lookups through `artifact_class`; subclass copies of COAL-keyed tables; BA-membership masks | INERT | identical values; masks gated `mode=="backcast"` (`arrays.py` ~4293/4333); heat-rate re-resolve needs `heat_rate_year`, backcast only; `offer_surfaces` hunk is PJM |
| `data/offer_curves.py`, `pipeline/offer_curve_base/generic.py` | coal reads `curves[subclass]`; COAL fallback curve deleted | INERT | NEISO forecast `offer_curve_by_group` is `{}`; the generic base curve is read only by `backcast_config` |
| `pipeline/{backcast_config,commitment}.py` | COAL curves deleted; bare-COAL refusal; ERCOT RUC / PJM startup | INERT | backcast-only or another ISO's branch |
| `data/fuel/plant_prices.py`, `data/winter_fuel_inventory.py` | donor class / class membership via `artifact_class` | INERT | same pooling and membership; delivered-fuel overlay is backcast |
| `data/{outages,caiso_outages,miso_outages,pjm_outages,campd}.py` | pre-COD clip (default off), ERCOT day guard, gas-short scope split | INERT | historic-outage overlays are backcast-only; `campd.py` parasitic default returns the same 0.070 |
| `data/{ba_membership (new),ferc714 (new)}.py`, `data/eia930/*` | SOCO/AEC/Gulf boundary, SOCO interchange sign, PSEI, CISO hydro backfill, NWPP FERC-714 | INERT | other ISOs; the repair functions return the input unchanged for ISNE |
| `data/zone_assignment.py`, `runner.py:1400` | `fleet_zone_vintage_coords` plumbing | INERT | default off, runner passes `False` |
| `model/reserves/spec.py`, `model/interchange/{core,spec}.py` | `COAL_CLASSES` in posture pool / floor limbs; MISO/PJM 2019 ladders | INERT | same values (reliability floor default off); other ISOs, 2019 |
| `results/{scarcity,cache}.py` | ERCOT envelopes; four epoch notes | INERT | ERCOT; **no same-key invalidation reaches a NEISO forecast** (the R-NEISO note is backcast) |
| `config/scenarios.py` | 4 new fields, all default `False`, registered in `_CACHE_KEY_OPTIONAL_FIELDS`; `_retire_bare_coal_class`; MISO sigmoid | INERT | no default flip, no `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` entry; guard passes on this config |
| `config/{constants,fuel_trajectories,capacity_market}.py` | subclass copies of MIN_STABLE / THERMAL_AVAILABILITY / MAINTENANCE shape; SOCO/PSEI/CAISO/PJM rows; RGGI 2019 row | INERT | identical NEISO tuples (fleet probe); RGGI: all NE states members every year, and 2026+ lookups unchanged |
| `config/{iso_configs,paths,ercot_envelopes,solve_surface_declared}.py` | comment; paths; ERCOT token; six new declarations | INERT | none reaches the NEISO forecast path |
| `scripts/lib/*` (9 files) | scoring, benchmark, key-provenance lag-class rule, parity | INERT | tooling; not on the `run_full_horizon` path |
| `data/raw/campd-unit-outages-NEISO.csv` (+meta) | West Springfield 1642 windows 2019–2021 | INERT | historic outage overlay, backcast-only, years < 2026 |
| `data/raw/_processed-legacy/bin_assignments_NEISO.csv` | Merrimack `COAL` → `COAL_BIT` | INERT | every number identical |
| `data/raw/eia-860/vintage_2021`, `vintage_2022` | vintage tables | INERT | vintage tables are backcast-only; the forecast reads the canonical snapshot, unchanged in this window |
| other `data/raw` (lmp, eia-930*, nwpp, spp, soco, NYISO-AS, gas-prices SOCO, `_validation-source`, ferc-714, caiso-outlook, reference ERCOT, carbon-auction CARB 2019, coal sigmoid MISO) | — | INERT | other ISOs or validation/scoring only |

**The key moves through the solve surface only.** NEISO `moved_rows` goes from `{RGGI_MEMBER_STATES_BY_YEAR}`
at `924017c8` to seven rows at HEAD (§1.2). The coal-subclass commit copied COAL-keyed values into subclass
keys without re-declaring the six tables, so their live hashes left their frozen declarations (the same
happens in every ISO). That changes the `__solve_surface__` payload and hence the literal; no `SolveEpoch`
applies. **Confidence:** high for the 2026 fleet (measured); medium-high for 2027–2050 (retirement and entry key
on `fuel_type`, not `plant_group`; no surviving `== "COAL"` comparison in `src`, grepped; Merrimack exits on its
filed date at step 1b). **What F1 did is NOT in this window** — it is in D94's (`aac390a6 → 924017c8`), and
D94's `vre_short` already carries it. So the D92 → D96 difference is expected to be F1's, now on all four
legs, plus nothing.

---

## 3. THE SHARDS (rule 32 `[R-SHARD]`; this session runs no LP)

Four legs → **four concurrent shards**, each ONE indivisible 2026–2050 invocation (a forecast horizon is an
evolution chain; rule 36 `[R-YEAR-ISOLATION]` (c) and rule 12 leave it unsharded by year).

* `source_revision` = **this PRECOMMIT's full 40-character SHA**; first hard stop `git rev-parse HEAD` equals
  it. **No rebase, pull or sync.**
* Own `--out-dir` `results/ff-t3-neiso-golden/d96/<leg>/`, own branch `claude/capx-d96-<leg>`.
* **Rule 34 (a): the FULL out-dir is pushed** — append `!results/ff-t3-neiso-golden/d96/<leg>/**` to
  `.gitignore`, then a **plain** `git add .gitignore results/ff-t3-neiso-golden/d96/<leg>`; never `-f`, never
  `-A` / `.`. Slim files first (one commit, pushed), cache parquets after (separate commits).
* Hard stops: SHA; the solved `run_config.json` shows both pins, `mode=forecast`, ISO NEISO, and exactly the
  leg's override; the key equals the §1.2 prediction (a mismatch is **reported, not repaired** — the shard
  still pushes, since the bytes are the evidence).
* **Budget, stated:** container preparation (`prepare_solve_container.py`, `hydrate_data.py --profile neiso`,
  `regenerate_clean.py`: ~45–60 min measured by D92) **+ a ~30–47 min solve** (D92 31.8–46.9, D94
  33.5–37.4). One longer shard per leg, never a fan-out (rule 32(b)).
* Forbidden by name: edits under `src/` or `scripts/`; anything under `frontend/data/**`;
  `dashboard_add_run.py` / `build_manifest.py` / `build_status.py` / `prune_iso_runs.py`; opening a PR;
  deleting any result. *"A shard that stops with a clear report is a SUCCESS; a shard that repairs
  infrastructure is a FAILURE."*
* Report: key, wall, `global_peak_rss_mb`, the `container preflight:` / `memory peak:` lines if printed,
  cumulative CO2, per-year CO2 2026/2029/2030/2035/2040/2050, 2030 and 2050 `gas_cc_ccs` MW, RM₂₀₅₀, and the
  pushed commit SHAs.

**The parent** fetches each branch; verifies config signature + both pins + key off `run_config.json`;
`git ls-tree` shows >0 files under the bundle (rule 34(d)); lands the slim bundle on this branch (rule 33(f));
and **only then** archives the shard. Per-year parquets stay off `main` (the `.gitignore` lines added in this
commit); re-deriving from them after the shard branches are cut costs a re-solve (~35–45 min per leg).

---

## 4. PREDICTIONS — FIXED HERE

Anchors: `d92/*` (same recipe, pre-F1, `aac390a6`) and **`d94/vre_short`** (same config as `base`, post-F1,
`924017c8`). Metrics: cumulative CO2 = Σ `trajectory[].co2_mt` 2026–2050 (the summary grain D92/D94
validated against the instrument); 2030 CCS = `capacity_by_fuel_mw.gas_cc_ccs` at 2030; RM₂₀₅₀ =
`trajectory[2050].reserve_margin`; P1 margin = base − carbon_plus25 cumulative CO2.

### 4.1 THE EXPECTATION TO BEAT: `base` vs `d94/vre_short`

**Prediction E1 (the strongest in this document): `base` reproduces `d94/vre_short` BYTE-FOR-BYTE on the
trajectory** — cumulative CO2 **151.2747 Mt**, 2030 CCS **6,979.7 MW**, RM₂₀₅₀ **0.06107**, and **zero
differing cells** across 25 years × every `trajectory` field. Basis: identical config (§1.1), an all-INERT
audit with a measured-identical fleet (§2), and the solver's measured determinism on this recipe (D92's L0
reproduced `d90-rescore` with zero differing cells over a 573-commit window). **Not labelled a
near-certainty:** it is the test of §2's 2027–2050 half, which was argued rather than measured.

**What a miss would mean, said in advance.** Any non-zero cell is a LIVE hunk the audit missed, and it would
most likely sit in the coal-subclass relabel (the only hunk class touching a NEISO unit) reaching an
evolution-year code path keyed on `plant_group`. A miss would be reported cell-by-cell with its size, and
**E1's grade would be MISS whatever the magnitude** — "close" is not a hit for a byte-identity claim. A tiny
miss (< 0.1 % cumulative, marginal-tie cells) would point at a degenerate tie broken differently by a
relabelled column order; a large one at a real mechanism.

### 4.2 Per leg — direction AND magnitude vs the same D92 leg

The F1 shift D94 measured on `base` (pre-F1 → post-F1) is **−2.04 % cumulative CO2, +331.4 MW 2030 CCS,
−0.0028 RM₂₀₅₀**. The arms are predicted to move **the same direction as `base`, with magnitudes of the same
order**. That is a WEAK prediction — F1 changes heat rates, which re-rank gas units and the CCS retrofit
screen, and nothing forces an arm to respond as the base did — and it is labelled weak.

| leg | metric | D92 (pre-F1) | **predicted D96** | direction | grade rule |
|---|---|---|---|---|---|
| `base` | cum CO2 | 154.4195 | **151.2747 exactly** | ↓ −3.1448 (−2.04 %) | E1 |
| `base` | CCS 2030 | 6,648.3 | **6,979.7 exactly** | ↑ +331.4 | E1 |
| `base` | RM₂₀₅₀ | 0.06388 | **0.06107 exactly** | ↓ −0.0028 | E1 |
| `carbon_plus25` | cum CO2 | 103.5042 | **[96.0, 104.0]** | ↓ 0 to −7 % | HIT iff in bracket and < D92 |
| `carbon_plus25` | CCS 2030 | 7,821.3 | **[7,821.3, 8,600]** | ↑ 0 to +800 | HIT iff in bracket |
| `carbon_plus25` | RM₂₀₅₀ | 0.06235 | **[0.055, 0.066]** | ↓ or flat | HIT iff in bracket |
| `gasup150` | cum CO2 | 208.9630 | **[198.0, 209.0]** | ↓ 0 to −5 % | HIT iff in bracket and < D92 |
| `gasup150` | CCS 2030 | 3,551.1 | **[3,551.1, 4,400]** | ↑ 0 to +850 | HIT iff in bracket |
| `gasup150` | RM₂₀₅₀ | 0.07996 | **[0.072, 0.083]** | ↓ or flat | HIT iff in bracket |
| `gaspm5` | cum CO2 | 168.0340 | **[159.0, 168.0]** | ↓ 0 to −5 % | HIT iff in bracket and < D92 |
| `gaspm5` | CCS 2030 | 5,984.2 | **[5,984.2, 6,800]** | ↑ 0 to +800 | HIT iff in bracket |
| `gaspm5` | RM₂₀₅₀ | 0.04737 | **[0.040, 0.050]** | ↓ or flat | HIT iff in bracket |

**FC-6 paired-P1 margin** (base − carbon_plus25): D92 **50.9153 Mt** → predicted **[47.0, 55.0] Mt**, i.e.
**|Δ| < 4 Mt, sign not claimed** (base falls 3.14 Mt by E1; the carbon arm is predicted to fall by a similar
amount, so the margin is roughly flat). **P1 stays PASS** (high < base) — a near-certainty given D92's 33 %
margin. P1.premise stays PASS at `+25.00 $/t` in all 25 years — **near-certainty, worth nothing**. P2 stays
PASS with all signs correct and its `not scored at this grain` clause. P3 stays PASS with builds moved
**< 5 %**.

Per-leg wall: **[28, 50] min**, peak RSS **< 5 GB** (D92 31.8–46.9 min, 3.65–3.81 GB; D94 33.5–37.4 min,
3.39–3.45 GB).

### 4.3 Status predictions — the zero-LP dry run already carries most of the information

Two dry runs were done here **before any leg exists**, on committed artifacts:

* **FC-5.** `docs/handoffs/d92/rebase_disposition.py` over `d94/vre_short` (the config-identical post-F1
  proxy): **0 of 54 rows change class**; 25 EXPLAINED DIVERGENCE / 29 IN CORRIDOR, unchanged. The co2 rows
  move −25.0 → −28.2 % (2030), −57.0 → −58.6 % (2035), −60.0 → −61.5 % (2040);
  `generation:total@2040` stays −15.3 % (the row that sits 0.3 pt past the line).
* **Whole verdict.** `forecast_verdict.py --tier t3` with `--summary/--run-config` swapped to
  `d94/vre_short` (paired + corridor carried): **HOLD, every status, reason and caveat identical**; only
  three detail strings move — FC-2 `final RM 6.4% → 6.1%`, FC-2 `backstop share 1.0% → 1.2%`, FC-7
  `837 → 875 config keys` (schema growth), FC-8 `wall 31.9 → 37.4 min`.

| # | prediction | label |
|---|---|---|
| S1 | **DETERMINATION stays HOLD**; FC-1…FC-8 = FAIL FAIL FAIL FAIL CAVEAT CAVEAT FAIL PASS, unchanged | **near-certainty** (FC-1/2/3/4/7 fail on instruments this lane does not touch or on structure that E1 reproduces) |
| S2 | **Reasons and caveats identical** | near-certainty |
| S3 | **FC-5 stays CAVEAT with 25 EXPLAINED / 29 IN CORRIDOR / 0 UNEXPLAINED; no row changes class** | strong — follows from E1 + the dry run; a miss here means E1 missed too |
| S4 | **FC-6 stays CAVEAT, still on the two vacuous T1.6 rows** (the battery is kept) | near-certainty |
| S5 | **FC-7 does not move** (same 2 UNIDENTIFIED entries); D90-R Addendum B not triggered | near-certainty |
| S6 | **Exactly these detail strings move and no others:** FC-2 `final RM 6.4% → 6.1%`, FC-2 `backstop share 1.0% → 1.2%`, FC-6 P1 / P2 / P3 operands, FC-7 `837 → 875 config keys`, FC-8 wall. FC-1's I3 detail string **identical** | strong — the dry run over `vre_short` shows the non-FC-6 half exactly; a different set means E1 missed |
| S7 | **`program-status.json` untouched** (no FC letter moves) | near-certainty |

**The one-sentence summary I will be graded on:** *F1 was the whole of the vintage gap and this window adds nothing: `base` lands on D94's `vre_short` to the
last cell, the three arms each move a little in the same direction, the P1 margin barely moves, and not one
FC status, reason or caveat changes — the verdict is simply on one vintage again.*

---

## 5. THE RE-SCORE — A CONTROLLED SWAP, IN TWO STEPS

**Step 0 — the control, ALREADY ESTABLISHED at this HEAD before any LP.** `forecast_verdict.py --tier t3`
over the committed inputs —

| flag | artifact | D96 |
|---|---|---|
| `--summary` / `--run-config` | `d92/base/*` | **SWAPPED → `d96/base/*`** |
| `--dof-ledger` / `--attestation` | `d92/base/*` | **SWAPPED → `d96/base/*`**, generated/authored exactly as D92 §11 did (same instrument; the two pins stay `unattested`, so FC-7 cannot move for that reason) |
| `--hindcast-score` | `hindcast/neiso-2021-2025-realized-t1h-d46/NEISO/da19b85495178949/score.json` | carried (a T1-H instrument, not a `neiso-t3` leg; out of charter) |
| `--crossover-score` | `hindcast/neiso-2023-2027-crossover-rcrepair/NEISO/07e416f3f8072e7c/crossover_score.json` | carried (same) |
| `--paired-invariants` | `d92/paired_invariants.json` | **SWAPPED → `d96/paired_invariants.json`** |
| `--corridor` | `ff-corridor/dispositions/neiso-t3.json` | **RE-AUTHORED on `d96/base`**, prior preserved byte-equal at `neiso-t3-pre-d96.json` |
| `--driver-battery` | `d94/driver-battery-neiso-2026-09-24.json` | **KEPT** (already post-F1) |

— reproduces `ff-verdicts.json["neiso-t3"]` **NON-PROVENANCE IDENTICAL** (`categories`, `caveats`,
`determination`, `iso`, `reasons`, `rubric_version`, `schema`, `tier` all identical). Measured here.

**The instruments, validated at this HEAD before use:**

* `docs/handoffs/d92/assemble_paired_invariants.py results/ff-t3-neiso-golden/d92` re-emits the committed
  `d92/paired_invariants.json` **byte-identically**. It is the registered FC-6 paired path, at the same
  summary grain D92 registered, so the paired diff is a data diff and not a grain change. P2 therefore keeps
  its `[not scored at this grain: objective↑]` clause (D92 Addendum B §B.2(2)). **Declared now:** because the
  shards push full bundles this time, the parent will ALSO run the cache-grain
  `check_forecast_invariants` paired path as a **reported cross-check, not registered** — changing the
  registered grain inside a vintage swap would confound the two.
* `docs/handoffs/d92/rebase_disposition.py` over `d92/base` reproduces **54/54** committed FC-5
  `model_value`s, and **54/54** `divergence_pct`s when the divergence is taken from the 4-dp-rounded model
  value (the table's own convention; from the raw value one row, `generation:oil@2040`, reads −83.6 vs the
  committed −84.0). The new table uses the same convention.

**FC-5 is re-authored exactly as D92 §6.2:** every `model_value` / `divergence_pct` recomputed mechanically;
`model_source` re-pointed at `d96/base`; an explanation is re-authored where a row's class changes or its
text is falsified by the new number; **quoted numbers inside a carried explanation are refreshed to the new
bundle** (a stale quoted figure is a falsified sentence). Anchors untouched (rule 13 `[R-MEASURED]`). A row
is never talked into corridor.

**FC-7 — D90-R Addendum B's four clauses, followed literally if FC-7 moves.** It is predicted not to.

**Registration.** The prior `neiso-t3` record is preserved byte-equal at **`neiso-t3-pre-d96`**. Scoring and
registration happen **after this lane's final rebase**; a later rebase re-stamps `scored_at_sha` by an
artifact-only re-score. **This lane is the sole writer of `frontend/data/forecast/ff-verdicts.json` this
window.** `program-status.json` moves only if a NEISO `fc` letter moves.

## 6. KEY PROVENANCE (concurrent lane D95)

`check_key_provenance.py` at this HEAD, before any leg: **245 committed run configs; 188 reproduce, 29 have
no key, 28 mismatch = 16 KNOWN + 10 LAG + 2 UNKNOWN** — the two UNKNOWN are `d94/{vre_short,vre_long}/run_config.json`, D95's to attribute; this lane does not
touch them. (Observed, not attributed: they were keyed on a live surface that has since moved further — §1.2.) The four `d96` run_configs must reproduce their own keys at this lane's merge; the
census is re-run after landing and reported (expected: 249 / 192 reproduce, UNKNOWN still 2). If the NEISO
solve surface moves again between the solve and the merge, the `d96` records join the same class as the two
D94 records, and that is reported rather than listed.

## 7. RULE 31 / 33 / BOUNDARIES

* **No solved bundle is deleted, for any reason.** Parquets are kept off `main` by `.gitignore`, never `rm`.
  The promotion question is asked in the FINDING.
* Shard branches are transport (rule 33(f)): what must survive lands on this branch before the PR merges.
  No shard branch is mirrored or preserved; the leftover refs are named for the owner.
* **No file under `src/` or `scripts/` is edited.** Rule 28 `[R-MECH-MATRIX]` does not fire: no mechanism is
  proposed, tested or added; no `ScenarioConfig` field changes.
* No backcast artifact, keeper, marker or freeze is touched.
