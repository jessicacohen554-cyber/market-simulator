# FINDING — PERF-C S5: a content-addressed disk memo for the per-year pre-LP inputs

**Shard S5 of the PERF-C lane** (`docs/handoffs/PRECOMMIT-perfc-orchestration-2026-09-20.md`
lever **L5**). Branch `claude/perfc-s5-input-memo`, pinned HEAD
`2a87343f8d7302ce84e66f45430a8d3b9e807d80`. **Zero LP solves**, zero timing work on the
solve path: every gate here is array equality on a `run_year(fleet_only=True)` rebuild.

---

## 0. Headline

Two of the four candidate products are memoized — **zonal demand** and the **renewable
CF/capacity matrices** — behind one default-ON switch, and proven byte-identical cold vs
warm on the ERCOT keeper (28/28 arrays equal, `np.array_equal`, `atol=rtol=0`). Two are
**left out on soundness grounds**, not for lack of time: `load_fleet_from_csv` and the
availability matrix (§4).

**The honest wall-clock result is that L5 is worth much less than the PRECOMMIT estimated.**
The PRECOMMIT's §1 table put L5 at **−20 to −30 s/yr on ERCOT**. Measured here on
`ERCOT 2023`, the two memoized products cost **2.86 s of a 25.25 s rebuild (11 %)** and the
memo returns them in **~0.01 s**. Against an ERCOT *year* of ~979 s (PRECOMMIT §0), that is
**~0.3 %**. The prize L5 was really aiming at is `generators_to_fleet_arrays` at **13.9 s**,
and §4.2 explains why this method cannot soundly memoize it. The PRECOMMIT's own disposition
of L5 — *"deferred: small vs L1–L3"* — is confirmed and now has numbers behind it.

The cold-vs-warm delta on the whole rebuild (cold 17.9 / 19.1 / 20.7 / 23.2 s; warm 16.0 /
17.5 / 18.7 / 19.1 s) is **inside the run-to-run noise** and is not quoted as the saving.
The per-loader measurement in §5 is.

---

## 1. What was built

| file | what |
|---|---|
| `src/market_sim/data/input_memo.py` (new, 745 lines) | the memo: request digest, recorded-source manifest, `.npz` payload, switch, hit/miss accounting |
| `src/market_sim/config/paths.py` (+7) | `INPUT_MEMO_DIR = DATA_ROOT/"data"/".input-memo"` |
| `.gitignore` (+5) | the memo tree is derived and disposable, never committed |
| `src/market_sim/data/eia930/demand.py` | `load_demand` → `_load_demand_uncached` + a memo wrapper |
| `src/market_sim/data/renewables.py` | `load_renewable_profiles` → `_load_renewable_profiles_uncached` + a memo wrapper, and `RENEWABLE_PROFILE_CONFIG_FIELDS` |
| `tests/unit/data/test_input_memo.py` (new, 28 tests) | key completeness + advisory-degradation, on tiny synthetic inputs |
| `tests/unit/data/test_input_memo_wiring.py` (new, 5 tests) | AST guards that the hand-listed key surfaces cannot rot |

**Neither loader's body moved a line.** Each was renamed to `_…_uncached` and a thin wrapper
added, so the diff of the computation itself is empty and rule 27 `[R-PUSH]`'s concern about
regenerated large-file content does not arise.

**Tests live in `tests/unit/data/`, not `tests/data/`** as the shard prompt said: `tests/data/`
does not exist in this repo, and `tests/unit/data/test_disk_memo.py` — the A-4 memo's own tests,
the direct precedent — is where a reader looks. Deviation stated rather than silently taken.

### 1.1 Reused precedent, not reinvented

`content_digest` comes from `market_sim.data.disk_memo` (item A-4) unchanged; the naming and
the advisory-cache discipline follow `market_sim.data.egrid_sheets` (item A-2). What is new is
only that the product is a tuple of numpy arrays and that the **source set is recorded rather
than declared** (§2.2).

### 1.2 The switch

`MARKET_SIM_INPUT_MEMO`, mirroring the shape of `MARKET_SIM_USE_CLEAN` in
`market_sim/data/clean_access.py`. **Default ON**, opt-out on `0/false/no/off`.
Default-ON is admissible *only* because a hit is byte-equal to a miss by construction — the two
key halves in §2 are what buys that, and the module docstring says so at the switch, so a change
to either must re-examine the default. `MARKET_SIM_INPUT_MEMO=0` restores the pre-memo path
exactly (tested).

### 1.3 Hit/miss reporting

`input_memo.memo_stats()` returns `{namespace: {"hit"|"miss"|"disabled": n}}`, and every
outcome is logged at INFO as `input memo HIT: demand` / `input memo MISS: renewable_profiles`.
Those are the lines quoted throughout this document.

---

## 2. The input enumeration (the deliverable that makes the key correct)

The key has two halves. **Both must hold for a memo to be served.**

### 2.1 Half 1 — the request digest (the non-file surface, enumerated)

sha256 over, in order: `SCHEMA_VERSION`, the namespace, the caller's `key_params` as canonical
JSON, a digest of **every `.py` under `src/market_sim`**, the sorted `MARKET_SIM_*` environment,
and the active EIA-860 vintage directory.

* **The package source digest** (211 files, **31 ms**, once per process) is the blunt instrument
  that makes everything else safe: any code change — a `constants.py` value, a branch in a
  loader, a switch to a read mechanism the recorder cannot see — re-keys every memo, so a memo
  written by one version of the code is never served to another.
* **The `MARKET_SIM_*` environment** is taken whole rather than as an enumerated subset, so a
  *new* gate cannot fall outside it. This is what puts `MARKET_SIM_USE_CLEAN` in the key, which
  matters because it reroutes the demand source.
* **The active EIA-860 vintage** is a *mutable module global* in `config/paths.py`
  (`set_active_eia860_vintage`), i.e. process state rather than an argument — which is exactly
  why it has to be named explicitly.

#### Product A — `load_demand` (namespace `demand`)

**The whole non-file surface is the function's own arguments.** `_load_demand_uncached` takes no
`ScenarioConfig` and reads no mutable module state, so the enumeration is the signature, in full:

| key entry | source |
|---|---|
| `iso`, `year`, `hours` | arguments (`hours` = `HOURS_PER_YEAR`) |
| `zone_names`, `load_shares` | `iso_config.zone_names`, `[z.load_share for z in iso_config.zones]` — the only two things the body reads off `iso_config` (grepped: `demand.py:1213–1218`) |
| `data_dir` | argument, as a string |
| `td_loss_factor`, `include_interchange`, `strict_demand_profile`, `caiso_demand_clock_realign`, `caiso_supply_consistent_demand`, `ercot_tie_zonal_interchange` | arguments |
| `demand_source` | `callable_signature(DEMAND_LOADERS.get(iso))` |
| `zonal_shares` | `callable_signature(_pkg_ns().load_zonal_shares)` |

The last two carry the **late-bound** collaborators. Both are resolved through the package
namespace at call time *precisely so tests can patch them*, and a patched collaborator returns
different data for identical arguments. `callable_signature` renders a real function as
`module.qualname` (stable across processes, which a `repr` carrying an address is not) and
anything else — a `Mock`, a fixture-bound lambda — as its `repr`, which is distinct per object
and therefore forces a miss. Production keeps its hits; patched code never gets one.

`tests/unit/data/test_input_memo_wiring.py::test_demand_key_covers_every_argument` re-reads the
wrapper's `key_params` literal from the AST and fails if a parameter is added without a key
entry.

**Files read** (recorded, ERCOT 2023, `ercot_tie_zonal_interchange=True`):

```
data/raw/ERCO_fueltype.parquet                              1,009,098 B
data/raw/ERCO_region.parquet                                  776,904 B
data/raw/eia-930-hourly/ERCO hourly.parquet                12,154,133 B
data/raw/eia-930-interchange/ERCO interchange hourly.parquet  357,838 B
data/raw/zone-specific-demand/ERCOT_Native_Load_2023.xlsx   1,103,792 B
```

which matches the hand grep of the code path — `frames.py:127` `_ERCO_HOURLY_FILE`,
`demand.py:786–790` the by-neighbor interchange parquet, `load_zonal_shares`' native-load
workbook — plus the two BA reference parquets read at first use. The demand-profiles fallback
(`data_dir/eia_demand_profiles.parquet`, `demand.py:1145`) does not appear because ERCOT does
not reach it; §2.2's directory guard is what covers a fallback that *would* be reached if a file
appeared.

#### Product B — `load_renewable_profiles` (namespace `renewable_profiles`)

Takes a whole `ScenarioConfig`, so the enumeration is the **transitive closure of every `config`
read** reachable from the implementation. Derived by AST walk, not by eye: nine fields, and the
closure is **contained in `renewables.py`** (the only unresolved callee is the `getattr` builtin),
which is what makes it checkable.

```
eia860_vintage_year          mode
ercot_wtx_curtailment_driver nyiso_solar_market_generator_basis
hindcast                     renewable_cf_adjustment
spp_curtailment_ceiling      vintage_capacity_ramp
vre_curtailment_oversupply_allocation
```

Functions in the closure: `_load_renewable_profiles_uncached` → `_zone_renewable_shapes` →
`_wind_zone_shape_enabled`, `_wind_zone_reanalysis_shapes`. Registered as
`renewables.RENEWABLE_PROFILE_CONFIG_FIELDS` and re-derived from the AST by
`test_renewable_config_fields_are_the_full_transitive_closure`, which **fails** if an edit adds a
`config` read without adding it to the tuple, or if `config` is ever forwarded out of the module
(at which point the closure stops being provable here and the test says so).

Plus `iso`, `year`, `hours`, `zone_names`, `data_dir`.

**The rest of `ScenarioConfig` is deliberately NOT in the key.** A field this loader never reads
cannot change its answer, and folding the whole config in would miss on every unrelated
offer-curve edit — which is precisely the case §3.2 measures.

### 2.2 Half 2 — the source manifest (the file surface, recorded)

Every data file the computation actually *reads* is captured through a `sys.addaudithook`
recorder while `compute()` runs, digested, and written to `manifest.json`; on a lookup every one
must still hash identically or the memo is discarded. Also recorded: a **listing digest** (names
and sizes, never an mtime) of every directory those files live in.

**Recording rather than declaring is deliberate.** A hand-written path list is only as correct as
the enumeration, and a missed path is a silently stale array on the solve path. The recorder
cannot miss a file the computation opened.

Measured properties of the mechanism (all 2026-09-20, CPython 3.11.15 / pyarrow 24.0.0):

| call | raises an audit event? |
|---|---|
| `pandas.read_parquet`, `read_csv`, `read_excel`, `numpy.load` | **yes** (`open`) — pandas opens the handle in Python |
| `pyarrow.parquet.read_table(path)` / `ParquetFile(path)` | **no** — pyarrow's native filesystem |
| `Path.exists()` / `os.path.exists()` / `os.stat()` | **no** |

Both gaps are closed rather than assumed away:

* **Absence.** A loader that falls back because a file is *missing* (`if not path.exists(): return None`)
  leaves no read to record, and `exists` raises nothing — so the **directory listing** is what
  catches that file's later arrival. Proven in §3.3.
* **Native pyarrow.** No module on either memoized product's read path uses it. The repo's single
  direct-pyarrow read is `data/outages.py:601` (`pq.read_schema`), on the **availability** path,
  which is not memoized. Should one ever appear, the package source digest in half 1 changes in
  the same commit, so no stale memo survives it.

Derived mirrors that A-2/A-4 write *beside their sources* (`.<16 hex>.` in the name) are excluded
from directory listings, so warming an eGRID mirror cannot invalidate this memo.

### 2.3 Fail-closed on an unaccountable read

A recorded read that is neither a data-tree input nor on a known-irrelevant prefix (the package
source, the interpreter and site-packages, `/proc`, `/sys`, `/etc`, zoneinfo) makes the product
**unmemoizable**: nothing is written and every later call recomputes. A product that recorded *no*
data input is refused for the same reason — it could never be invalidated.

This is what protects a caller who has redirected a loader's inputs somewhere the manifest does
not model (a test patching `EIA_HOURLY_DIR` to a scratch path, most of all). A manifest that
verified against files the computation never used would be exactly the stale-array failure the
module exists to make impossible.

### 2.4 A defect found and fixed: the manifest must only ever GROW

**Measured on the ERCOT keeper while writing §3.3, and it defeated the first implementation.**
Several inputs are read through an `lru_cache`, so a recompute *in a process that is already warm*
reads fewer files than the cold one did. Rewriting the manifest from that call alone dropped
`ERCO hourly.parquet` (12 MB) from the recorded set — after which re-encoding that file served a
**stale array with a HIT**. The first run of the §3.3 probe reproduced exactly that.

Fixed two ways, both in `input_memo.py`:

1. `_NAMESPACE_READS` accumulates every read a namespace makes in the process and unions it into
   every manifest that namespace writes.
2. `_previous_sources` reads whatever manifest is already at the key and unions it in, so the
   recorded set is **monotone across processes**. A manifest can now lose a source only when the
   file itself is gone.

Guarded by `test_manifest_only_ever_grows`. Unioning is a strict over-approximation: at worst an
unrelated change costs a recompute, and a manifest that names too much can never serve a stale
array, which a manifest that names too little can.

**The residual, stated rather than hidden.** A file already cached by some *non-memoized* code
path before a namespace's very first memo call in a process is never recorded at all. What covers
it is that `data/raw` is immutable by repo convention (never modified in place), so a changed
input arrives as a new or replaced file — which the directory-listing digests catch. The mutable
surface is `data/clean`, and that is reached only under `MARKET_SIM_USE_CLEAN`, which is in the
key.

---

## 3. The proofs (all zero-LP)

Harness: `run_year(fleet_only=True)` on the ERCOT keeper
`results/calibration/ercot_mer20260919_five_year`, **year 2023**, the recipe read exactly as
`scripts/legitimacy_diagnostics._rebuild_fleet_arrays` reads it.

> **Correction to the shard prompt.** It named `run_config_carveout_2023.json` as the recipe.
> That file's `calibration_flags` block is a **35-key summary** and under-specifies the fleet —
> using it raises `ValueError: gas_offer_margin_zonal_anchor is armed without
> gas_offer_net_revenue_margin` before any array is built. The full recipe is the bundle's
> **`meta.json` (317 keys)** with the composed bundle's own
> `config_partition_overrides["2023"]` applied on top; that is the 2023 carve-out, and it is
> what `_rebuild_fleet_arrays` uses.

### 3.1 Cold vs warm — 28/28 arrays byte-identical

Cold = memo directory empty; warm = memo populated; two separate processes. Compared with
`np.array_equal` plus dtype and shape equality (`atol=rtol=0`).

| product | shape | dtype | result |
|---|---|---|---|
| `demand` | (7, 8760) | float64 | **EQUAL** |
| `wind_cf` / `solar_cf` | (7, 8760) | float64 | **EQUAL** |
| `wind_cap` / `solar_cap` | (7,) | float64 | **EQUAL** |
| `wind_mc` / `solar_mc` | () | float64 | **EQUAL** |
| `mc_base` | (2323, 8760) | float64 | **EQUAL** |
| `fuel_prices` | (2323, 8760) | float64 | **EQUAL** |
| `fleet_arrays.availability` | (2323, 8760) | float64 | **EQUAL** |
| `fleet_arrays.min_gen` | (2323, 8760) | float64 | **EQUAL** |
| `fleet_arrays.min_gen_mechanism` | (2323, 8760) | int8 | **EQUAL** |
| `fleet_arrays.pmax` / `pmin` / `heat_rate` / `vom` / `ramp10` | (2323,) | float64 | **EQUAL** |
| `fleet_arrays.emission_rate` / `nox_rate` / `so2_rate` | (2323,) | float64 | **EQUAL** |
| `fleet_arrays.zone_idx` / `fuel_type_idx` / `plant_code` | (2323,) | int64 | **EQUAL** |
| `fleet_arrays.unit_ids` / `efficiency_bin` | (2323,) | `<U41` / `<U10` | **EQUAL** |
| `fleet_arrays.plant_group` / `state` | (2323,) | object | **EQUAL** |
| `storage_power_cap` | (5, 8760) | float64 | **EQUAL** |

**28 products, 28 EQUAL, 0 DIFFER.** `demand`, `wind_cf`, `wind_cap`, `solar_cf`, `solar_cap` are
the memoized products themselves; the other 23 are the downstream arrays built from them, which
is what makes this a gate on the rebuild rather than on the memo in isolation.

Memo log: cold `MISS: demand`, `MISS: renewable_profiles`; warm `HIT: demand`,
`HIT: renewable_profiles`.

### 3.2 A flipped offer-curve multiplier still HITS — and is still correct

Flipped **one** registered band multiplier, the rule-1 `[R-STRUCT]` authorized price-tuning
channel: `offer_curve_by_group["CC_CHP"]["peak"] 4.248 → 4.4614` (passed to `run_year` as
`offer_curve_overrides`).

| run | demand | renewable_profiles |
|---|---|---|
| flipped, warm memo | **HIT** | **HIT** |
| flipped, cold memo | MISS | MISS |

* **flip-warm vs flip-cold: all 28 products EQUAL.** The memo returned the same answer the cold
  rebuild computed under the flipped kwargs.
* **flip-cold vs unflipped: `fleet_arrays.heat_rate` and `mc_base` DIFFER.** The flip genuinely
  bit — without this the HIT would prove nothing.

That pair is the whole case for enumerating `key_params` narrowly instead of hashing the whole
`ScenarioConfig`: the memo is insensitive to a parameter its products do not read, and correct
under it.

### 3.3 A touched source MISSES

Run against a **hard-link mirror** of `data/` under `MARKET_SIM_DATA_ROOT`, so no file in the repo
was modified (rule 31 `[R-RETAIN]`, and `data/raw` is immutable).

| step | change | outcome |
|---|---|---|
| 1 | cold | MISS |
| 2 | — | **HIT**, array equal to cold |
| 3 | a new file appears in a watched directory (`eia-930-hourly/ZZZ probe.parquet`, never read by the loader) | **MISS** ✔ |
| 4 | that file removed again | MISS — step 3's recompute had re-keyed the manifest to the polluted listing; array equal to cold |
| 5 | `ERCO hourly.parquet` re-encoded, same values, sha16 `1b47e133…` → `54b5a002…` | **MISS** ✔, recomputed array equal to cold |

Step 5 is the run that exposed §2.4: **before** the monotone-manifest fix it returned a HIT.
Step 5 changes the file's size as well as its bytes, so it does not isolate the digest check from
the listing check; `test_source_content_change_at_identical_size_misses` does isolate it, on a
synthetic source of unchanged length.

### 3.4 Tests

| suite | result |
|---|---|
| `tests/unit/data/test_input_memo.py` | **28 passed** (0.21 s) |
| `tests/unit/data/test_input_memo_wiring.py` | **5 passed** (0.07 s) |
| `tests/regression/test_regression_smoke.py` | **36 passed** (0.18 s) |
| `tests/unit/data` (2,360 tests, fast tier) | 2,356 passed, 19 skipped, **5 failed** |
| `ruff check` + `ruff format --check` on every changed file | clean |

**All 5 failures are PRE-EXISTING at the pinned HEAD** and reproduce identically with this
shard's changes stashed (`git stash -u`, re-run, same 5). They touch no file this shard edits.
Not repaired here — *a shard that stops with a clear report is a SUCCESS; a shard that repairs
infrastructure is a FAILURE.*

```
tests/unit/data/test_caiso_st_gas_peak_measured.py::…::test_registry_value_matches_the_committed_artifact
        AssertionError: 1.154 != 1.166  (CT_PEAKER peak band vs the committed OASIS artifact)
tests/unit/data/test_fleet.py::TestLoadRetiredWithinWindow::test_neiso_includes_mystic_cc
tests/unit/data/test_gas_offer_zonal_anchor_vintage.py::test_training_window_mean_reproduces_the_registered_zone_table
tests/unit/data/test_gas_offer_zonal_anchor_vintage.py::test_reference_zone_window_mean_is_the_iso_anchor
tests/unit/data/test_soco_zonal_gas_hub.py::test_no_applier_is_armed_for_soco
```

---

## 4. What was left out, and why

### 4.1 `load_fleet_from_csv` — left out

Three reasons, in the order that decides it:

1. **It does not cost enough to be worth a correctness surface.** Measured: **0.26 s** cumulative
   in the ERCOT 2023 rebuild (§5), 0.07 s on a repeat call. A memo cannot pay for its own risk
   here.
2. **It returns a Pydantic object graph** (`list[Generator]`, 1,450 objects), not arrays. A memo
   would need a provably exact round-trip of that graph — a **second** correctness surface the
   `.npz` array path does not have, and one whose failure mode is a silently altered fleet.
3. **It has a documented side effect.** It writes the binned fleet to
   `data/raw/_processed-legacy/{iso}_fleet_binned.parquet`, which `load_binned_fleet` reads. A
   memo hit would skip that write, so the memo would be observably different from the call —
   which is the one thing this module promises never to be.

Its **non-file** surface *is* fully enumerable (15 explicit arguments, no `ScenarioConfig`), so if
a future lane wants it, reason 1 is the one to re-measure and reasons 2–3 are the work.

### 4.2 The availability matrix — left out

This is the product L5 was really aiming at: `generators_to_fleet_arrays` is **13.86 s** of the
25.25 s rebuild, of which `_apply_outage_overlays` is **8.94 s** and `_compose_min_gen_floors`
**2.09 s** (`_availability_matrix` itself is only 0.73 s). It is left out anyway, because its
input set is **not fully enumerable by the method this module rests on**:

* **The `ScenarioConfig` closure is 92 fields and OPEN.** The same AST walk that resolved
  renewables to nine contained fields resolves `generators_to_fleet_arrays` to 92 — and it does
  **not** close: `campd_attribution_selectors` forwards `config` out of `arrays.py` into another
  module, so the closure cannot be completed, or guarded against drift, the way
  `RENEWABLE_PROFILE_CONFIG_FIELDS` is. A key that is 92-of-more fields is not a key; it is a
  guess with 92 terms in it.
* **Two of its arguments are the products of other computations** — `generators` (the 1,450-object
  Pydantic fleet) and the `load_shape` / `netload_shape` / `ct_campd_shape` arrays — so the key
  would have to hash those too, which re-raises §4.1's reason 2.

The shard prompt allowed exactly this ("only if its ~15-flag input set is fully enumerable — if
not, leave it out and say why"). The measured answer is that it is not ~15 flags; it is 92 and
open.

**What a future lane should do instead.** The 8.94 s in `_apply_outage_overlays` is the largest
single pre-LP item in the rebuild and it is *not* obviously config-dense at its hot points; a
narrower memo sited *inside* it — on the outage-event frame keyed by its own source files, where
the closure is small — is a better shaped lever than one wrapped around the whole fleet build.
That is a new card, not a continuation of this one.

---

## 5. Measured cost attribution (`run_year(fleet_only=True)`, ERCOT 2023, cold memo)

cProfile, cumulative seconds. Total under the profiler 25.25 s (~19–21 s unprofiled).

| function | cum s | calls | memoized? |
|---|---:|---:|---|
| `generators_to_fleet_arrays` | 13.86 | 2 | no — §4.2 |
| ↳ `_apply_outage_overlays` | 8.94 | 2 | no |
| ↳ `_compose_min_gen_floors` | 2.09 | 2 | no |
| ↳ `_availability_matrix` | 0.73 | 2 | no |
| `build_base_fleet` | 12.70 | 1 | partly (contains the fleet load) |
| **`load_demand`** | **2.54** | 1 | **yes** |
| **`load_renewable_profiles`** | **0.32** | 1 | **yes** |
| `load_fleet_from_csv` | 0.26 | 1 | no — §4.1 |

Isolated loader timings (cold process, ERCOT 2023):

```
_load_demand_uncached                 1.43 s        load_demand        memo warm  0.01 s
_load_renewable_profiles_uncached     0.18 s        load_renewable…    memo warm  0.00 s
load_fleet_from_csv  (1st / 2nd)      0.25 / 0.07 s
```

**Memoized coverage: 2.86 s of 25.25 s ≈ 11 % of the rebuild, ≈ 0.3 % of an ERCOT year.**

---

## 6. Cache location and operation

* **Location** `data/.input-memo/<namespace>/<request-digest>/{manifest.json,payload.npz}`,
  resolved through `config/paths.INPUT_MEMO_DIR` (never `Path(__file__).parents[...]`), so it
  follows `MARKET_SIM_DATA_ROOT` with everything else.
* **Gitignored** — derived and disposable. Deleting the tree costs only the rebuild it was saving.
* **Concurrency** every write is to a process-unique temporary name then `os.replace`d, so rule
  12's two simultaneous invocations see a complete file or none. The `.npz` temporary keeps its
  suffix, because `numpy.savez` appends `.npz` to a name that lacks one.
* **Size** ERCOT 2023: `demand` 491 KB, `renewable_profiles` 982 KB per (ISO, year).
* **Security posture** `numpy.savez` with `allow_pickle=False` on both write and read; dtype and
  shape are re-checked against the manifest before an array is returned. No executable payload,
  no path that could deserialize into code — the same property A-4 gets from refusing anything but
  JSON.
* **Advisory** every failure — unreadable source, unwritable root, corrupt manifest, truncated
  payload — logs and falls through to the computation. Tested.

---

## 6b. Governance exposure, named rather than left for a successor to find

`MARKET_SIM_INPUT_MEMO` is **an off-registry env-var knob**, and rule 24 `[R-REGISTRY]` says
every tunable that can change a solve appears in `ScenarioConfig`/`constants.py` and the run's
`run_config.json`. The claim that admits it is that it **cannot** change a solve — a hit is
byte-equal to a miss by construction — and that claim is what §3.1–§3.3 measure.

That is precisely the shape of the claim rule 36 `[R-YEAR-ISOLATION]` (e) **withdrew** for
`MARKET_SIM_WARMSTART_XYEAR` and `MARKET_SIM_P1_BASIS_SEED`: both were documented as
basis-neutral, both were tolerated off-registry as performance knobs on that basis, and the
neutrality was later falsified on the calibration path (MISO 2022: 24 TWh off CC_REGULAR,
43,160 price cells moved). So the exposure is stated here in full:

* **What is different.** Those two knobs changed the *solver's path* — a different vertex of a
  degenerate LP is a different answer, and the neutrality claim was about the optimum rather
  than about bytes. This memo changes no computation at all: on a hit it returns the array a
  miss would have computed, from a file written by a miss, verified by content. The neutrality
  is an identity, not an empirical property of a solver.
* **What would falsify it anyway.** An incomplete key. §2 is therefore written as an
  enumeration with two AST guards behind it, and §2.4 records the one incompleteness that was
  actually found — by probe, not by argument — and what now prevents it.
* **What a successor owes.** If either enumerated surface stops being provable — `config`
  forwarded out of `renewables.py`, a `load_demand` argument added without a key entry, a
  loader moved onto native pyarrow — the wiring test fails *first*. If instead the knob is ever
  wanted as anything other than an opt-out kill switch, rule 24 applies and it belongs in
  `ScenarioConfig` and the cache key, not in the environment.

No `ScenarioConfig` field is added by this shard, so rule 25 `[R-MECH-MATRIX]` duty (c) does not
bind and no matrix row is owed. `scripts/check_mechanism_matrix.py` and
`scripts/check_cache_key_registration.py` were both run: their findings
(CAISO/PJM keeper-stamp drift; `PPA_COST_RECOVERY_YR` and `REGIONAL_RENEWABLE_CF` undeclared)
**reproduce at the pinned base** and belong to other lanes.

---

## 7. What this does NOT claim

* **No keeper moves and none was re-solved.** No LP ran in this shard. The cold/warm gate is a
  `fleet_only` rebuild, which is the exact product being memoized — it is *not* evidence about
  dispatch, prices, or any scored metric.
* **ERCOT 2023 only.** The equality proof is one ISO-year. The mechanism is ISO-agnostic and the
  key construction is not ERCOT-specific, but no other ISO-year has been run through it.
* **The saving is small and is stated as small.** See §0. If the PERF-C parent is choosing where
  to spend, L1/L3 remain the levers; L5 is now measured rather than estimated, and the number is
  ~0.3 % of a year.
* **`generators_to_fleet_arrays` is the unclaimed 13.9 s**, and §4.2 says why this method does not
  reach it and what would.
