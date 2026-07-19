# Data Reorganization Plan — market-simulator

> Status: ARCHIVED — executed (the data/raw + data/clean split shipped).

## Context

**Why this is being done.** The repo's data is fragmented across **two competing roots** (`inputs/` and `data/`), totalling ~2.1 GB of mostly-committed files (639 tracked files under `inputs/`, no Git LFS). The model reads these files through **~9 loader modules that each hardcode paths** like `Path(__file__).parents[3] / "inputs" / "raw-data" / ...` — there is **no central path registry**, so any file move breaks the model with `FileNotFoundError`. Directory naming is inconsistent (`ercot-AS`, `PJM-AS`, `NYISO-AS`, `caiso-hsl`, `lmp-data`, `zone-specific-demand`, `ISO-specific-gen-data`), column schemas differ across ISOs (CAISO LMP uses `LMP/MCC/MCE`; PJM uses `DA_LMP/RT_LMP`; NYISO AS uses `spin_10/op_30`), and there is **no standalone data dictionary**.

**Intended outcome.** A single, navigable `data/` tree where raw downloads are walled off and untouched in `data/raw/`, and standardized model-facing files live in `data/clean/<datatype>/<ISO>/` as schema-validated Parquet, with one true data dictionary. The model becomes **less fragile** because every path resolves through a single `paths.py` registry. Raw is preserved intact; nothing is deleted until the clean tree is proven byte-for-byte equivalent in model behavior. **Documentation reconciliation is explicitly a later session** (handoff noted at the end).

**Confirmed decisions (from user):**
1. **Type-first** layout: `data/clean/<datatype>/<ISO>/`
2. **Relocate** `inputs/raw-data` → `data/raw/` via `git mv` (preserve history)
3. **Everything** goes in the tree — per-ISO market data + cross-ISO shared sources + validation actuals
4. **Parquet** canonical (CSV only for small human-edited files); dictionary in markdown + machine-readable `schema/*.yaml`

---

## Target structure

```
data/
  raw/                       # git mv of inputs/raw-data/ + data/{fleet,reference,eia_hourly}
    ercot/  lmp-data/  campd-unit-level/  campd-facility-level/
    eia-930/  eia-860/  NYISO-AS/  PJM-AS/  caiso-hsl/  gas-prices/  ...
    # CONTENTS UNTOUCHED — only relocated. This is the "separate, intact" raw archive.
  clean/                     # standardized, schema-validated, model-facing (Parquet)
    lmp/<ISO>/               # per-ISO: day-ahead + real-time
    load/<ISO>/              # per-ISO zonal/system demand
    ancillary-services/<ISO>/
    generation/<ISO>/        # gen by fuel
    renewables/<ISO>/        # wind/solar potential, HSL, curtailment, CF
    emissions/<ISO>/         # CAMPD-derived hourly + rates
    outages/<ISO>/           # CAMPD-derived outage windows
    validation/<ISO>/        # actual LMP/AS actuals for backcast scoring
    fleet/                   # SHARED: EIA-860 inventory (sliced per-ISO at load)
    fuel-prices/             # SHARED: Henry Hub + EIA-923 delivered costs
    reference/               # SHARED: eGRID, master-plant-registry, crosswalks, bin assignments
  dictionary/
    data-dictionary.md       # the one true human-readable dictionary
    schema/<datatype>.schema.yaml   # machine-readable column/dtype/unit contracts
  README.md                  # how the tree is laid out + how to regenerate clean/ from raw/
```

**Canonical conventions enforced for every clean Parquet:**
- Column names `lower_snake_case`; timestamps as `interval_start_utc` (tz-aware UTC) + optional `interval_start_local`.
- Standard keys: `iso`, `zone`/`node`, `year`, `month`, `hour`; values carry explicit units in column name where ambiguous (`*_mw`, `*_mwh`, `price_usd_per_mwh`, `*_kg`).
- One file per `<ISO>/<datatype>/<year>.parquet` (and `.../<year>-<market>.parquet` for DA/RT splits).

---

## Recommended order & dependency logic

Physical-tree work (relocation, cutover) is **inherently serial** — two sessions cannot `git mv` the same tree without conflicts. Per-data-type **curation is highly parallel** because each writes a disjoint subtree. So the order is: lock the foundation serially, then fan out.

| Wave | Parallel? | Gate before it can start |
|------|-----------|--------------------------|
| **W0** Central path registry (refactor only, no moves) | serial (1 session) | — |
| **W1** Physical relocation raw → `data/raw/` | serial (1 session) | W0 green |
| **W2** Canonical schema + dictionary scaffold + shared writer util | serial (1 session) | W1 green |
| **W3** Per-datatype curation (8 sessions) | **PARALLEL** | W2 merged |
| **W4** Cutover: point loaders/scoring at `data/clean` | serial (1 session) | all W3 merged |
| **W5** Dedup, prune orphans, finalize dictionary, verify | serial (1 session) | W4 green |
| **(later)** Documentation reconciliation | separate effort | W5 done |

**Why W0 before any move:** once every path resolves through `paths.py`, the W1 physical move is a *one-file* change and the W4 cutover is localized — this is the key de-fragilization step and the safety keystone. **Why W2 before W3:** all parallel curators must conform to one schema contract and use one shared writer, or the "consistent formatting/naming" goal fails.

---

## Verification strategy (applies to every wave)

- **Golden backcast baseline:** before W0, run a reference backcast (e.g. `market-sim --iso ERCOT --mode backcast --year 2024`) and save outputs. After W1 and after W4, re-run and assert **numerically identical** results — this is the "nothing got broken" proof.
- Run the full `pytest` suite after every wave; all data-touching tests (`test_fleet`, `test_eia_loader`, `test_eia923_fuel`, `test_campd`, `test_outages`, `test_hydro`, `test_zone_assignment`, `test_calibration`, `test_runner`) must stay green.
- `grep -rn "inputs/raw-data\|parents\[3\]" src/ scripts/ tests/` must return **zero** stray hardcoded paths after W4.

---

## Session prompts (copy-paste into fresh sessions)

> Each prompt is self-contained. Run W0 → W1 → W2 serially. Then launch all eight W3 prompts in parallel. Then W4, then W5. Every prompt ends by committing + pushing to its own branch.

### WAVE 0 — Central path registry (run first, alone)

```text
TASK: De-fragilize data paths by introducing a single central path registry. DO NOT MOVE OR RENAME ANY DATA FILES in this session — this is a pure, behavior-preserving refactor.

Context: ~9 modules under src/market_sim/data/ (fleet.py, eia_loader.py, eia923.py,
campd.py, fuel.py, outages.py, renewables.py, hydro.py, zone_assignment.py) plus
scripts in scripts/ and tests/ each hardcode data paths as
`Path(__file__).parents[3] / "inputs" / "raw-data" / ...` and a second root under data/.
There is no central registry. The model reads from inputs/raw-data, inputs/processed,
inputs/calibration, and data/{fleet,reference,eia_hourly}.

Do this:
1. Create src/market_sim/config/paths.py defining: REPO_ROOT, and named constants for
   every current data location (RAW_DATA_DIR, PROCESSED_DIR, CALIBRATION_DIR, EIA_860_DIR,
   EIA_930_DIR, FLEET_DIR, REFERENCE_DIR, EIA_HOURLY_DIR, etc.) resolved the same way they
   are today, so values are byte-identical to current behavior. Add a DATA_ROOT seam:
   `DATA_ROOT = Path(os.environ.get("MARKET_SIM_DATA_ROOT", REPO_ROOT))` and build the
   rest off it. Also add forward-looking helpers (no-op for now):
   `clean_path(datatype, iso=None, year=None, market=None)` and `RAW_DIR`, `CLEAN_DIR`,
   `DICTIONARY_DIR` pointing at the FUTURE data/raw and data/clean (these are unused this session).
2. Replace every hardcoded `Path(__file__).parents[3] / ...` data path in the ~9 data
   modules, scripts/, and tests/ with an import from config.paths. Keep all current paths
   pointing where they point today.
3. Run the full test suite — it MUST be fully green and unchanged. Run a reference backcast
   (market-sim --iso ERCOT --mode backcast --year 2024) and save its output as the golden
   baseline for later waves; commit the baseline summary under results/ or note its hash.
4. `grep -rn "parents\[3\]" src/ scripts/ tests/` should now return zero data-path hits
   (only paths.py resolves the root).

Branch: claude/data-paths-registry. Commit with a clear message and push.
Constraint: zero behavioral change; no file moves; identical test + backcast results.
```

### WAVE 1 — Physical relocation raw → data/raw/ (run after W0)

```text
TASK: Collapse the two data roots into one by relocating all raw downloads into data/raw/,
using git mv to preserve history. Depends on the paths.py registry from branch
claude/data-paths-registry (rebase/branch off it).

Do this:
1. `git mv inputs/raw-data data/raw`. Then fold the legacy second root in:
   `git mv data/fleet data/raw/fleet-egrid`, `git mv data/reference data/raw/reference`,
   `git mv data/eia_hourly data/raw/eia-930-hourly` (choose names that don't collide with
   existing data/raw subdirs; document the mapping in the commit body).
2. Relocate inputs/processed -> data/raw/_processed-legacy and
   inputs/calibration -> data/raw/_validation-source for now (they get curated in W3; keep
   intact). Move loose files inputs/{master-plant-registry.csv, custom-bin-assignments.csv,
   tx-jan-aug23-unit-outages.csv} into data/raw/reference/ via git mv.
3. Update ONLY src/market_sim/config/paths.py so RAW_DATA_DIR/PROCESSED_DIR/CALIBRATION_DIR/
   etc. resolve to the new data/raw/... locations. No other source file should change.
4. Fix the .gitignore entries that reference old paths (e.g. inputs/raw-data/eia-860/*.csv,
   inputs/processed/*.parquet whitelist) to their new data/raw/... equivalents.
5. Run full pytest (must be green) and re-run the ERCOT 2024 backcast — assert results are
   NUMERICALLY IDENTICAL to the W0 golden baseline. If anything differs, stop and report.

Branch: claude/data-relocate-raw. Constraint: contents of relocated files are byte-identical;
only their location and paths.py change. Commit + push.
```

### WAVE 2 — Schema contracts + dictionary scaffold + shared writer (run after W1)

```text
TASK: Establish the standardization contract that all parallel curation sessions will follow.
Depends on branch claude/data-relocate-raw.

Do this:
1. Create data/dictionary/schema/ with one <datatype>.schema.yaml per clean datatype:
   lmp, load, ancillary-services, generation, renewables, emissions, outages, validation,
   fleet, fuel-prices, reference. Each schema declares canonical columns: name, dtype, unit,
   nullability, and key columns. Enforce conventions: lower_snake_case columns;
   tz-aware UTC `interval_start_utc` (+ optional `interval_start_local`); standard keys
   iso/zone/node/year/month/hour; explicit units in names (*_mw, *_mwh,
   price_usd_per_mwh, *_kg). Base the canonical AS/LMP/load column sets on a reconciliation
   of the divergent per-ISO source columns (see inventory: CAISO LMP=LMP/MCC/MCE/MCL/MGHG;
   PJM=DA_LMP/RT_LMP; NYISO AS=spin_10/nonsync_10/op_30/reg_cap, etc.) into ONE schema each.
2. Create scripts/lib/clean_io.py with a shared writer used by ALL curation scripts:
   `write_clean(df, datatype, iso=None, year=None, market=None)` that validates df against the
   datatype schema (column presence, dtypes, units metadata, UTC tz), writes Parquet to
   config.paths.clean_path(...), and embeds schema-version + source-provenance in parquet
   metadata. Add `validate_clean(path)` for round-trip checks.
3. Write the data/dictionary/data-dictionary.md skeleton: one section per datatype, an ISO
   coverage matrix (ERCOT/CAISO/PJM/MISO/SPP/NYISO/NEISO x years), and a "regenerate from
   raw" pointer. Leave per-column detail to be auto-filled in W5.
4. Add a target-layout note to data/README.md. Add unit tests for clean_io (schema pass/fail).

Branch: claude/data-schema-contract. Do NOT curate real data yet. Commit + push.
```

### WAVE 3 — Per-datatype curation (run ALL 8 IN PARALLEL after W2 is merged)

> Shared preamble for every W3 prompt — paste it at the top of each:
> *"Depends on branches claude/data-paths-registry, claude/data-relocate-raw, claude/data-schema-contract (branch off the merge). RULES: data/raw is READ-ONLY — never modify it. Write ONLY to data/clean/<datatype>/<ISO>/ using scripts/lib/clean_io.write_clean(). Conform exactly to data/dictionary/schema/<datatype>.schema.yaml. Do NOT touch any loader in src/market_sim/data/ (cutover is a later wave). Deduplicate inputs where the same data appears twice. Each curation script lives in scripts/data/curate_<datatype>.py, is idempotent and re-runnable, and writes a coverage report. Commit + push to the named branch."*

```text
[W3a · branch claude/curate-lmp]
Curate LMP for all ISOs. Read raw lmp-data/<ISO>/ (CSVs + OASIS zips for NYISO/NEISO,
CAISO RTM/DAM hourly, PJM monthly index, ERCOT zonal). Normalize the divergent per-ISO
columns into the canonical lmp schema, split day-ahead vs real-time, attach component
columns (energy/congestion/loss/ghg) where available. Write
data/clean/lmp/<ISO>/<year>-<market>.parquet. Produce a coverage matrix (ISO x year x market).
```

```text
[W3b · branch claude/curate-load]
Curate load/demand for all ISOs from raw zone-specific-demand/ (PJM hrl_load_metered CSVs,
ERCOT Native Load xlsx weather zones, NYISO zonal CSVs, CAISO TAC loads) plus EIA-930 demand
as fallback. Map source zones to canonical model zones, standardize to UTC hourly mw. Write
data/clean/load/<ISO>/<year>.parquet. Note any ISO lacking zonal detail (uses EIA-930 system).
```

```text
[W3c · branch claude/curate-as]
Curate ancillary services from raw NYISO-AS/, PJM-AS/, ercot-AS/ (+ ercot/). Reconcile
product names (NYISO spin_10/nonsync_10/op_30/reg_cap; PJM reserve products; ERCOT RegUp/
RegDown/RRS/ECRS/NonSpin) into the canonical AS schema with a product dimension. Write
data/clean/ancillary-services/<ISO>/<year>.parquet.
```

```text
[W3d · branch claude/curate-generation]
Curate generation-by-fuel from raw ISO-specific-gen-data/ (PJM/ERCOT gen_by_fuel CSVs) and
EIA-930 fuel mix. Standardize fuel-type taxonomy across ISOs, UTC hourly mw per fuel. Also
dedup the redundant root-level eia-930 fueltype/region parquets noted in the inventory
(NYIS_*, CISO_*). Write data/clean/generation/<ISO>/<year>.parquet.
```

```text
[W3e · branch claude/curate-renewables]
Curate renewables from raw caiso-hsl/, ercot-hsl/, caiso-curtailment/, and EIA-930
wind/solar. Produce hourly uncurtailed potential + capacity factor + curtailment per ISO.
Write data/clean/renewables/<ISO>/<year>.parquet.
```

```text
[W3f · branch claude/curate-emissions-outages]
Curate emissions + outages from raw campd-unit-level/ and campd-facility-level/ (state-year
parquets). Keep facility vs unit granularity distinct (they are NOT duplicates). Standardize
units to kg, hour 1-8760, canonical keys. Reproduce the derived artifacts (plant emission
rates, parasitic load, outage windows) into data/clean/emissions/<ISO>/ and
data/clean/outages/<ISO>/. Map states to ISO footprints.
```

```text
[W3g · branch claude/curate-shared]
Curate the SHARED cross-ISO sources: EIA-860 fleet inventory -> data/clean/fleet/;
gas prices (Henry Hub daily/monthly) + EIA-923 delivered fuel costs -> data/clean/fuel-prices/;
eGRID 2023 + master-plant-registry + custom-bin-assignments + crosswalks ->
data/clean/reference/. Standardize columns/units; keep human-edited CSVs as CSV but copy a
canonical parquet alongside.
```

```text
[W3h · branch claude/curate-validation]
Curate validation actuals from raw _validation-source (former inputs/calibration):
actual_lmp_hourly_<ISO>, actual_lmp_zonal_<ISO>, actual_as_reserve_<ISO>, renewable_capacity.
Standardize to the validation schema. Write data/clean/validation/<ISO>/. These are the
backcast scoring references.
```

### WAVE 4 — Cutover (serial, after all W3 merged)

```text
TASK: Point the model and calibration scoring at data/clean instead of data/raw. Depends on
all W3 branches merged.

Do this, ONE datatype at a time, validating after each:
1. For each loader in src/market_sim/data/ (fleet, eia_loader, eia923, campd, fuel, outages,
   renewables, hydro, zone_assignment), switch its read paths to config.paths.clean_path(...)
   for the standardized clean files, using the new canonical column names. Update calibration
   scoring to read data/clean/validation/.
2. After each datatype switch, run the relevant tests; after all are switched, run the FULL
   suite and re-run the ERCOT 2024 backcast. Assert results match the W0 golden baseline
   within tolerance (document any intended difference from schema normalization; if a column
   rename changed a value, that is a bug — fix it).
3. `grep -rn "data/raw\|_processed-legacy\|_validation-source\|parents\[3\]" src/ tests/`
   must return zero (model reads only data/clean + the registry).

Branch: claude/data-cutover. Commit + push. If any backcast number moves unexpectedly, STOP
and report rather than masking it.
```

### WAVE 5 — Dedup, prune, finalize dictionary (serial, after W4)

```text
TASK: Finalize the reorg. Depends on branch claude/data-cutover.

Do this:
1. Remove now-orphaned intermediate dirs that nothing reads (former inputs/processed cache
   that is regenerable, redundant duplicate parquets confirmed unused). NEVER delete anything
   under data/raw/ — raw stays intact. Confirm via grep that each removed path has zero refs.
2. Auto-generate the per-column detail in data/dictionary/data-dictionary.md from the
   schema/*.yaml + actual delivered parquet metadata (column, dtype, unit, source, coverage).
   Fill the ISO x datatype x year coverage matrix from what W3 actually produced.
3. Update data/README.md with the final tree + a "how to regenerate data/clean from data/raw"
   runbook listing each scripts/data/curate_*.py.
4. Final full pytest + ERCOT 2024 backcast vs golden baseline. Report the before/after repo
   tree and confirm single-root, schema-validated, deduplicated state.

Branch: claude/data-finalize. Commit + push.
```

---

## Handoff: documentation session (next, separate)

After W5, a **separate documentation session** reconciles prose with the new reality using the existing `sync-docs` skill. Scope to flag for that session (from the staleness audit): `market-sim-build-plan.md` data-layout section (now wrong), `claude.md` architecture diagram (`data/ → ...` paths moved), and pointing all data references at the new `data/clean` + `data/dictionary/data-dictionary.md`. That session should also delete/retire the obsolete `inputs/`-based descriptions. (Resolved separately on `claude/docs-entrypoint`: the README now carries a Quickstart + install/run instructions; `pyproject.toml` + `uv.lock` are the single dependency source of truth, with `requirements.txt` reduced to a clearly-labelled generated pip fallback; and the empty `context/` folder is now documented by `context/README.md` rather than referenced as if populated.)

## Risks & mitigations

- **2GB in git, no LFS:** moves use `git mv` (no blob duplication); a later optional session can evaluate Git LFS / history slimming — out of scope here.
- **Numerical drift from column normalization:** the golden-baseline backcast comparison after W1 and W4 is the guard; any unexplained move is treated as a bug.
- **Parallel W3 collisions:** prevented by disjoint subtrees + shared `clean_io` writer + read-only `data/raw`.
- **Cutover risk concentrated in W4:** done serially, one datatype at a time, behind the full test suite + backcast.
