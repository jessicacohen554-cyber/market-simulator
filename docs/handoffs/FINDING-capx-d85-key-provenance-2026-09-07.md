# FINDING — capx D85: key-provenance audit of the 15 non-reproducible committed `cache_key`s

**Session:** capx D85 (owner ruling **Q59**, capx ledger §0bb.3(a), r#57). **Model:** Fable.
**Branch:** `claude/capx-d85-key-provenance-etmyjh`, fresh off `origin/main` at `db0c1d85`
(2026-09-07). **DATA PROFILE:** code. **An AUDIT: nothing committed was rewritten, re-registered,
deleted or solved.** Instrument and record: `docs/handoffs/d85/key_provenance_census.py` →
`docs/handoffs/d85/key-provenance-census.json`.

---

## 0. The step-3 answer, first

**No stale-keyed bundle can be served to a run that should have re-solved, and the reason is the
code path, not an assertion.** Three independent layers, any one of which is sufficient:

1. **A stale key is unreachable by construction.** Every one of the 15 keys was produced by a rule
   set or an environment that today's `ScenarioConfig.cache_key()` no longer implements
   (§3). A requester today computes a *different* key for the identical config, so the stale
   directory is never addressed — it is an orphan, which costs one re-solve and never a wrong
   answer. The single exception is the D24 §4.2 collision form (a requester at the ARMED
   storage-entry default addresses the pre-flip key, §3.2), which is exactly what layer 2 exists for.
2. **The equality refusal catches the one reachable form.** `runner.run_scenario_iso`
   (`src/market_sim/runner.py:2770-2789`) serves a bundle only when `is_cached` AND
   `cache_config_disagreements` is empty; a disagreement is a logged MISS and a re-solve. Exercised on
   the real payloads (§4.2): an armed-default requester against the stored pre-R-A `config.yaml`
   returns `['storage_entry_availability_gate', 'storage_entry_cost_normalized_rank']` — refused —
   in both the present-at-False and the absent-vs-armed forms. Every forecast and hindcast
   entrypoint routes through this one function (`pipeline/api.run_scenario`, `run_full_horizon`,
   `run_capacity_hindcast`, `run_driver_battery`); the backcast lane never serves by key at all
   (`run_calibration_full.py` computes `cache_key()` for the record only — no `is_cached`, no
   `load_result`).
3. **Nothing servable is committed.** `results/<ISO>/` cache directories are gitignored. The four
   bundle directories the 15 records point at that ARE tracked carry `config.yaml` only, no
   `year_*.parquet` (§4.3), so `is_cached` is False on any fresh checkout. The stale parquet exists,
   if at all, only on the machines that solved it.

**This item is therefore BOOKKEEPING, not a defect** in the Q20 / (b′-1) sense. What remains is a
provenance property — a committed key that today's rules cannot recompute — and that is now
closed by derivation rather than by rewrite: **every one of the 15 reproduces to the exact recorded
literal under a named recipe (§2), zero unclassified.**

One thing IS worth an owner card and is priced in §5: the D76-ARM census construction (and this
lane's, inherited) hashes the solve surface **at its declaration**, which is only equal to the live
`cache_key()` while every surface row sits on its frozen declaration. Since 2026-09-07 two ISOs'
rows have moved (§3.5), so **46 further committed keys — every validated ERCOT and CAISO record —
are reproducible only under that construction** and would read as mismatches to an instrument
that hashed the live surface. That is the designed D79 re-key, not a hole, but the instrument
should say which key it is reproducing.

---

## 1. Step 1 — the count, reproduced

`scripts/probes/capxd76arm_default_flip_key_census.py --variant b` at `db0c1d85`:

| | D76-ARM (`59155c2c`) | D76-ARM-B (record `192`; text `190` at its base) | **D85 (`db0c1d85`)** |
|---|---:|---:|---:|
| committed `run_config.json` | 173 | 192 | **214** |
| reproduce recorded key | 133 | 150 | **169** |
| no recorded key | 25 | 27 | **30** |
| **do NOT reproduce** | **15** | **15** | **15** |

**The 15 are the SAME 15 files** as both prior censuses (set-equal, checked). Net +41 since
D76-ARM is 45 added and 4 pruned (`pjm_tp2022_2021_k162` and the three `scn-campaign-load-2026-09-06`
ERCOT configs, superseded by the `-r2` campaign). The 45 added are all post-registration and all
reproduce or carry no key: 37 `scn-campaign-*` policy/load configs (ERCOT r2 / CAISO / MISO / NEISO
/ NYISO / PJM), 6 calibration probes (`ercot253_2021_touchpoint`, `nyiso213_*`,
`pjm169_tp2022_2021_f2arm`, `spp40/42_*`), the `pjm-2021-2025-realized-t1h-d75rarm` hindcast, and
`ff-t3-neiso-golden/bau-d65br`. Full list in the record's `rows`.

---

## 2. Step 2 — every row classified

Recipes are defined in the instrument's docstring; each is a way the recorded key WAS produced.
`vintage` = re-hashed under the rules extracted by AST from the bundle's own `git.sha` (fetched at
depth 1; the clone is shallow at 2026-09-06).

| # | run_config | ISO | solved (UTC) | `git.sha` | recorded | class | recipe | vintage check |
|--:|---|---|---|---|---|---|---|---|
| 1 | `results/ff-t1f-s123/verify` | MISO | 2026-08-31 01:14 | `54ca19a` | `587dc5b32ba71ceb` | **(b′) pre-ledger flip** | drop R-A pair | reproduces |
| 2 | `results/ff-t1f-s6-pjm/ledger` | PJM | 2026-08-31 00:40 | `54ca19a` | `31a19d815fa319a7` | **(b′) pre-ledger flip** | drop R-A pair | reproduces |
| 3 | `…/bau-prera-2026-08-31` (root) | NEISO | 2026-08-31 03:18 | `271ad60` (gone) | `a4b11ef4aaa1be35` | **(b′) pre-ledger flip** | drop R-A pair | commit unreachable; sibling `9e56f0fe` reproduces |
| 4 | `…/bau-prera-2026-08-31/fc6/arms/base` | NEISO | 2026-08-31 18:03 | `9e56f0fe` dirty | `0365174ab16cc318` | **(b′)+(d) split-root** | drop R-A pair + fold roots | reproduces under vintage + split roots |
| 5 | `…/fc6/arms/carbon25` | NEISO | 2026-08-31 17:41 | `9e56f0fe` dirty | `7924eccc695c0168` | **(b′)+(d) split-root** | same | same |
| 6 | `…/fc6/arms/carbon_plus25` | NEISO | 2026-09-01 06:11 | `9e56f0fe` dirty (+`scenarios.py`) | `7784d408fc955785` | **(b′)+(d) split-root** | same | same |
| 7 | `…/fc6/arms/gaspm5` | NEISO | 2026-08-31 18:37 | `9e56f0fe` dirty | `1de43201e2040f7f` | **(b′)+(d) split-root** | same | same |
| 8 | `…/fc6/arms/gasup150` | NEISO | 2026-08-31 18:15 | `9e56f0fe` dirty | `13f9357712250600` | **(b′)+(d) split-root** | same | same |
| 9 | `…/ff-t3-neiso-golden/bau` (root) | NEISO | 2026-09-01 19:41 | `f0a13bf5` | `706e7ba8e6582d42` | **(a) registration lag** | un-drop `caiso_offer_surface_measured_ungrounded` | reproduces |
| 10 | `…/bau/fc6/arms/base` | NEISO | 2026-09-01 20:21 | `9f09f64e` | `706e7ba8e6582d42` | **(a) registration lag** | same | reproduces |
| 11 | `…/bau/fc6/arms/carbon_plus25` | NEISO | 2026-09-01 20:56 | `9f09f64e` | `f7cced798488ddac` | **(a) registration lag** | same | reproduces |
| 12 | `…/bau/fc6/arms/gaspm5` | NEISO | 2026-09-01 22:04 | `9f09f64e` | `2d017ed9675aa386` | **(a) registration lag** | same | reproduces |
| 13 | `…/bau/fc6/arms/gasup150` | NEISO | 2026-09-01 21:30 | `9f09f64e` | `65662ca117959ee5` | **(a) registration lag** | same | reproduces |
| 14 | `results/hindcast/miso-2021-2025-realized-t1h-d27` | MISO | 2026-09-01 03:19 | `360b83ee` | `501b5f64b8adf8d4` | **(a) registration lag** | same | reproduces |
| 15 | `tests/golden/ercot_2026_2040.run_config.json` | ERCOT | seeded 2026-07-11 | `f0f7c67d` | `0d6f2710f8dedf56` | **(d) request-not-resolution** | vintage rules + ERCOT `default_scenario_overrides` | reproduces only resolved |

**Class totals:** (a) 6 · (b′) 3 · (b′)+(d-split-root) 5 · (d-request) 1 · **unclassified 0.**

Against the classes the card anticipated: **(a)** is exactly the six D76-ARM named. **(b)** — a
flip in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` — accounts for **zero** rows, by construction:
under (b′-1) an absent field hashes at its frozen declaration, so a record's payload reproduces
whatever the live default has since become (§3.2 explains why the R-A flip is different). **(c)** —
the solve-surface fingerprint — accounts for zero of the 15 but for **46 other records** (§3.5).
**(d)** turned up twice: a solve-environment dependence of the key (§3.3) and a writer that
recorded the request rather than the resolution (§3.4).

---

## 3. The mechanisms

### 3.1 (a) Registration lag — 6 rows

`caiso_offer_surface_measured_ungrounded` landed in `aebeb60e` (caiso-231) **without** its
`_CACHE_KEY_OPTIONAL_FIELDS` entry and was registered on **2026-09-02** by the CI-red repair lane
(`scenarios.py` lines 1168–1180, `docs/FINDING-ci-red-repair-2026-09.md`). The six bundles solved
2026-09-01 (03:19 → 22:04) on trees where the field existed unregistered, so the solving code
**hashed** it at `False`; today's rule **drops** it at `False`. Un-dropping that one field
reproduces all six literals, and each also reproduces under its own vintage's rules. The record
is internally consistent — the payload carries the field at `False` — so the provenance is
recoverable; only the recomputation rule moved.

### 3.2 (b′) A default flip that PREDATES the flips ledger — 8 rows (3 alone, 5 compounded)

Not a `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` flip. Owner ruling **R-A** (PR #4442, merged
**2026-08-31T02:37:44Z**, base `9e56f0fe`) flipped `storage_entry_availability_gate` and
`storage_entry_cost_normalized_rank` `False → True` under the **pre-(b′-1)** rule, which dropped a
registered field at the **live** default of the day. A bundle that recorded the pair at `False`:

* solved before the flip (rows 1–3: 00:40–03:18 on 2026-08-31, trees at `54ca19a`/`9e56f0fe`) or
  on a detached pre-flip tree (rows 4–8) → the pair equalled the live default → **dropped**;
* is hashed today → the frozen declaration is `"True"` (the 2026-09-01 re-baseline froze every
  field at its live default *of that day*, i.e. post-R-A) → `False ≠ True` → **hashed**.

Dropping the pair reproduces rows 1–3 exactly, and rows 1–2 also reproduce under their own
vintage's rules. The instrument tries flip-field subsets smallest-first because a third such
field, `forecast_xyear_warmstart`, is also carried at its pre-flip value in these payloads, but
its flip (2026-07-26) predates the solves, so it was already hashed then and must NOT be dropped.

The re-baseline was recorded as "free" because *the default config's* key did not move. It was
free for every payload at the post-flip value or lacking the field; it was not free for the
committed records that carried the **old** value explicitly, which is what these eight are. This
is precisely the hazard `_CACHE_KEY_REGISTRATION_TIME_DEFAULTS` was backfilled to make the (c′)
check see — and it does see it (§4.2).

### 3.3 (d) Split-root fold — the 5 fc6 arms, compounded on §3.2

Rows 4–8 do NOT reproduce under their recorded commit's rules alone. Their `run_config.json`
records `git.sha = 9e56f0fe`, `branch = HEAD`, `dirty = True`; the D21 and D26 findings state the
environment: **repo worktree `/home/user/msim-vintage` with
`MARKET_SIM_DATA_ROOT=/home/user/market-simulator`**
(`FINDING-capx-d21-fc6-battery-2026-08-31.md` finding 6; `FINDING-capx-d26-p1-arm-construction-2026-09-01.md`
§3). `_cache_key_path_roots()` then returns `(<data_root>, /home/user/market-simulator),
(<repo>, /home/user/msim-vintage)`, and the six path-valued fields
(`campd_bins_path`, `plant_registry_path`, …, all under `/home/user/market-simulator/data/raw/`)
fold to `<data_root>/data/raw/…` instead of `<repo>/data/raw/…`. Re-folding under those roots
reproduces all five literals — under the vintage rules and, with the R-A pair dropped, under
today's. The `base` arm's payload is byte-identical to row 3's, and the D26 finding already
recorded that `0365174ab16cc318` and `a4b11ef4aaa1be35` are "the split-root and single-root folds
of the same config". So D21 knew; what nobody wrote down was that the record carries no field
from which a reader could tell.

**The provenance gap this exposes is in the record, not the key:** `pipeline/persist.git_state()`
records sha, branch, dirtiness and changed files, and `environment_block()` records Python and
package versions — **neither records the fold roots**, so a split-root key is not reproducible from
`run_config.json` alone. It is recoverable only because two findings happened to state the
environment in prose.

### 3.4 (d) Request, not resolution — the ERCOT golden fixture

`scripts/golden_forecast_bands.py` at `f0f7c67d` (seed 2026-07-11) built
`config = ScenarioConfig(**REFERENCE_SCENARIO_KWARGS)`, called `run_scenario_iso(config, …)`, and
wrote `"scenario_config": dataclasses.asdict(config)` — the **request**. The runner applied
ERCOT's `default_scenario_overrides = {"scarcity_price_overlay": True}` and hashed the
**resolution**. Re-applying that one override to the payload and hashing under the vintage's
seven-field, no-fold rules gives `0d6f2710f8dedf56` exactly. The fixture therefore records
`scarcity_price_overlay: False` for a solve that ran it `True` — the FFR-2E defect class
(`run_record.write_run_config`'s docstring: "the pre-solve object is a REQUEST and the on-disk
dump is the RESOLUTION"), which that single writer closed for every runner **except this script**:
`solve_reference` (line 146) and the payload (line 324) still serialize the request at HEAD, so a
future reseed would repeat the defect.

The fixture is already under an owner-signed staleness waiver (`tests/golden/staleness_waiver.json`,
D-7(i), re-issued 2026-08-02, expires 2027-01-31); the identity test it holds off compares
`ScenarioConfig(**REFERENCE_SCENARIO_KWARGS).cache_key()` against the seeded key, so it is
internally consistent with itself and unaffected by this finding. It is a fixture, not a servable
bundle, and no cache directory exists at its key.

### 3.5 (c) The solve surface — zero of the 15, 46 of the other 169

The D76-ARM census construction (`_key`) omits the `__solve_surface__` block, which was correct
when written: "BOTH keys are absent from every config today". At `db0c1d85` it is not:
`moved_rows("ERCOT") = {NUCLEAR_MONTHLY_CF_BY_YEAR}` (constants re-derived by ercot-253,
`09c812aa`, 2026-09-07) and `moved_rows("CAISO") = {NUCLEAR_MONTHLY_CF_BY_YEAR,
STATE_CARBON_PRICE_BY_ISO}` (caiso-262, `04ca0267`, 2026-09-07), neither re-declared in
`solve_surface_declared.py`. The live `cache_key()` therefore appends the block for every ERCOT and
CAISO config, and **all 29 validated ERCOT and all 17 validated CAISO records reproduce their
recorded key only with the surface at declaration** (`reproduces_at_declaration_only` in the
record). Proof that the two constructions bracket the live method: on instance payloads,
`construction(asdict(cfg), surface=True) == cfg.cache_key()` for ERCOT, CAISO and MISO rows.

This is D79's **designed** re-key (CLAUDE.md: "a re-derived registry table re-keys the ISOs whose
rows moved") and every post-D79 bundle records what it solved on in `solve_surface.json`, so it is
not a provenance hole. It IS a blind spot in the census instrument: "169 reproduce" is true of the
at-declaration key and false of the live one for 46 of them, and the two lanes' findings quote the
number without the qualifier. `SOLVE_EPOCHS` is empty at HEAD (asserted by the instrument), so
`__solve_epochs__` is not yet a third construction.

---

## 4. Step 3 — the risk, from the code path

### 4.1 Reachability, class by class

| class | can a requester today address the stale key? | why |
|---|---|---|
| (a) lag | **No** | the stale hash contains `"caiso_offer_surface_measured_ungrounded": false`; today's rule never emits that field at `False` into the hash, and at `True` it emits `true`. |
| (b′) R-A pair | **Yes — the D24 §4.2 form** | today's rule drops the pair at `True`, producing the same residual payload the pre-flip rule produced by dropping it at `False`. A requester at the armed default with an otherwise identical config lands on the stale key (measured: `head_key(payload, extra_drop=pair) == recorded`). |
| (b′)+(d) split-root | Only under the same relocated `MARKET_SIM_DATA_ROOT` | as (b′), gated on reproducing the environment. |
| (d) golden | **No** | not a bundle; no cache directory; seven of today's 275 registered fields existed. |
| (c) surface | **No** | today's ERCOT/CAISO keys carry the moved block; the at-declaration keys are orphaned until the rows are re-declared. |

### 4.2 The one reachable form is refused

`cache_config_disagreements` → `config_disagreements(stored, wanted)` (`results/cache.py:1372`),
exercised on the committed payloads:

```
stored = ff-t1f-s123 payload (pair at False); wanted = same with pair True
  -> ['storage_entry_availability_gate', 'storage_entry_cost_normalized_rank']   REFUSED (§4.1 form)
stored = same with the pair ABSENT; wanted = pair True
  -> ['storage_entry_availability_gate', 'storage_entry_cost_normalized_rank']   REFUSED (§4.2 form,
     via registration_time_default('storage_entry_availability_gate') == False)
stored = bau payload (lag field at False); wanted = identical
  -> []   served — correct, it IS the same config, and the key is unreachable anyway
```

The refusal is a logged MISS and a re-solve (`runner.py:2776-2793`), never an exception, and it sits
on the only seam that reads a bundle for a solve. Readers that load by an **explicit** key
(`ensemble.py`, `matrix.py`, the reporting scripts, `export.py`, `calibration.py`) address a
registered bundle by name, not by recomputation, so the "should have re-solved" question does not
arise there.

### 4.3 Nothing servable is committed

`results/<ISO>/` is gitignored (`.gitignore` §7). Of the 15 records' bundle directories, four are
tracked and each carries **`config.yaml` only** — `bau-prera-2026-08-31/NEISO/a4b11ef4aaa1be35`,
`bau/NEISO/706e7ba8e6582d42`, `ff-t1f-s123/verify/MISO/587dc5b32ba71ceb`,
`ff-t1f-s6-pjm/ledger/PJM/31a19d815fa319a7` — no `year_*.parquet`, so `is_cached` is `False` on any
checkout. The `miso-…-d27` hindcast and the fc6 arms track no directory at all.

**Net: the (b′) collision is real and reachable, and it is exactly the case D24-R option (c′) was
landed for; the refusal catches it on the serving seam, and on a fresh checkout there is nothing
to refuse. The item downgrades to bookkeeping.**

---

## 5. Step 4 — repairs, priced. Recommendation: (ii) + (v), nothing else

| | repair | cost | invalidates | verdict |
|---|---|---|---|---|
| (i) | **Leave as provenance-only.** | 0 | nothing | Insufficient alone: every future census re-derives the 15 (three lanes have now), and (c) will grow with every re-derived table. |
| (ii) | **Recorded exception list** — commit this record; make the census instrument consult it: a listed row must reproduce under its recorded recipe, an unlisted mismatch fails. | ~1 h: `key-provenance-census.json` is that list; wire `capxd76arm_default_flip_key_census.py` (or its successor) to read it. | nothing; changes no key, no bundle | **Recommended.** Turns a hole into a verified derivation, and makes a NEW lag/flip/environment orphan loud at PR time. |
| (iii) | **Re-register the lagging field** (un-register `caiso_offer_surface_measured_ungrounded` so the 6 keys recompute). | trivial edit | **orphans every key produced since 2026-09-02** that carries the field at `False` — 185 committed records, 163 of them validated — and every on-disk cache; moves the pinned literals | **Refused.** Cures 6 by breaking 163; and the R-A and split-root classes have no analogue. |
| (iv) | **Rewrite the 15 keys** to today's values. | trivial | the record's truth: `bau` and its `bau/fc6/arms/base` would then claim a key at which no bundle was ever solved | **Refused**, as the card already rules. |
| (v) | **Close the two record gaps forward** (no key moves): (v-a) `persist.environment_block()` records `_cache_key_path_roots()` and `MARKET_SIM_DATA_ROOT`, so a split-root key is reproducible from `run_config.json` (§3.3); (v-b) `golden_forecast_bands.py` serializes the RESOLVED config (read the cache's `config.yaml` as `write_run_config` does) so the next reseed records what solved (§3.4); (v-c) the census instrument reports BOTH the at-declaration and the live key and names which one "reproduces" means (§3.5). | ~2 h total, three small edits, zero solves | nothing; (v-b) changes a fixture only at its next owner-authorized reseed | **Recommended alongside (ii).** |
| (vi) | Re-declare the moved ERCOT/CAISO surface rows now. | `solve_surface_register.py --declare` | re-keys nothing further, but **would silently re-arm the at-declaration keys** for bundles solved on the OLD tables — the exact serve-stale hazard D79 exists to prevent | **Not this lane's call**: the re-declaration belongs to the ISO lane that re-solves its frontier on the new table, per D79. Listed so nobody reads (c) as an invitation. |

**Why (ii)+(v) and not more.** Every one of the 15 is now derivable to the literal, so the record's
truth is intact; what was missing was the derivation and, for the split-root class, one
environment fact the record should have carried. (ii) preserves the derivation as a checked
artifact; (v) stops the two record gaps recurring. Neither touches a key, a bundle, a registration
or a flip, so neither needs the Q20 / (b′-1) machinery to move.

---

## 6. What this lane did NOT do, so a successor need not check

* **No committed `cache_key`, bundle, registration, flip, or surface declaration was changed.**
  `src/market_sim/`, `scripts/`, `tests/`, `results/`, `frontend/` are untouched.
* **No solve.** The clone is `blob:none`, shallow at 2026-09-06; the six vintage commits were fetched
  at depth 1 for their `scenarios.py` / `iso_configs.py` / `runner.py` blobs only.
* **No matrix stamp** (rule 28): no mechanism was tested or armed.
* **No ledger edit**: `capx-director-ledger-2026-08.md` is the director's; the card is §0bb.3(a).
* **Not widened** to D82 / D83 / D84.
* **Not chased:** `271ad60` (row 3's recorded sha) is unreachable on the remote — a squashed branch
  commit; the sibling merge base `9e56f0fe` reproduces the row and the classification does not
  depend on it.

---

## 7. Reproduction

```bash
uv sync
# the six solve commits, if the clone is shallow (full shas in the record's rows)
for s in 54ca19ae0782871bd4adbcb482bc531a66618402 9e56f0fecd861b79bae12a2049a049fe0c62f577 \
         9f09f64e4b762b2b2dddb27661ab6b5c53b2dfd8 f0a13bf59043bad7f0d89c6a4062a160f8def7aa \
         360b83eebfecd0e6f671228ee24d1a16548ec72c f0f7c67d937c11e487255784e8298faf3c98c0c1; do
  git fetch --depth=1 origin $s; done
.venv/bin/python scripts/probes/capxd76arm_default_flip_key_census.py --variant b   # 214 / 169 / 30 / 15
.venv/bin/python docs/handoffs/d85/key_provenance_census.py \
    --out docs/handoffs/d85/key-provenance-census.json                              # exit 0, 0 unclassified
```
