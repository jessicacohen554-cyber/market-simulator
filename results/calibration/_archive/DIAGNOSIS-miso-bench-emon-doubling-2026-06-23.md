# MISO benchmark `e_mon` doubling — root-cause: prior-session environment artifact

**Status: NOT a code bug. Not reproducible on current `main` + clean `data/raw`.
The committed `bench/MISO/{2023,2024,2025}.json.gz` (from "miso6 coalclass",
ac5142d / 21753e9 / 4fc4aaa) are verified correct and were never corrupted.**

## Symptom (reported from a prior local session)
A local `dashboard_add_run` regen of `frontend/data/backcast/bench/MISO/*.json.gz`
showed per-plant `bench.plants.*.e_mon` roughly **doubled** (e.g. plant 6017,
2023: 266 → 533 GWh in Jan) and coal groups flipped **COAL_PRB → COAL**
(889 / 997 / 1893), while the fuel-level benchmark (`classFull` /
`fuelRows`: coal 174.95, gas 172.0, interchange −37.91 TWh for 2023) stayed
correct.

## Two independent symptoms, two independent causes

### 1. `e_mon` doubling — stale disposable shared parquet (environment artifact)
The per-plant `e_mon`/`e_ann` come from the bundle's EIA-923 snapshot
(`bundle_input_path(bdir, "eia923")`), a **content-addressed, gitignored,
disposable** parquet under `results/calibration/_shared/<ISO>/`. miso5 and miso6
reference *different* eia923 snapshot hashes (`6c24660cab8a` vs `e99ed7736e57`),
and that store does not survive a fresh container clone.

Rebuilding the MISO 2023 snapshot from raw data through the exact production path
(`_benchmark_eia923_frame` → `_eia923_frame` + `_backfill_eia923_with_campd` +
`_backfill_renewables_eia930`, current `main`) yields the **correct, single**
values — monthly-sum / annual ratio = **1.000**, zero duplicate `(plant_id,
klass)` rows:

| plant | klass    | annual (MWh) | Σ m01..m12 (MWh) | ratio | m01 (GWh) |
|------:|----------|-------------:|-----------------:|------:|----------:|
| 6017  | COAL_PRB |    3,082,246 |        3,082,246 | 1.000 |    266.49 |
| 889   | COAL_PRB |    5,898,854 |        5,898,854 | 1.000 |    544.37 |
| 997   | COAL_PRB |    1,427,182 |        1,427,182 | 1.000 |    163.50 |
| 1893  | COAL_PRB |    5,042,118 |        5,042,118 | 1.000 |    578.49 |

These match the committed bench exactly (6017 Jan = 266.5 GWh, etc.). The
snapshot builder groups `(plant_id, klass)` and sums monthly + annual from the
*same* rows, so a real double-count would move both symmetrically — it cannot
produce a monthly-only doubling. The doubled snapshot was therefore a **stale /
duplicated `_shared/MISO/eia923-*.parquet`** materialized in the prior session
(disposable cache, not in `data/raw`), not a defect in the current code. The
fuel-level benchmark stayed correct because it was read from the already-correct
committed bench part, not re-derived from the stale snapshot.

### 2. COAL_PRB → COAL flip — bench-supplier selection, not the 923 builder
The bench plant `group` is set from the **model dispatch** `klass` (`grp_p` in
`render_calibration_html`), i.e. it is supplied by whichever run sorts newest in
the registry for each year — **not** by the EIA-923 benchmark frame (whose
`klass` rebuilds correctly as COAL_PRB above, since `_fleet_group_by_code` /
`_coal_supply_class` read `coal_supply_MISO.csv`). The committed-correct bench
was refreshed from **miso6 coalclass** (which carries the coal-supply split). A
full local regen supplied instead by **miso5 firmhydro** — whose own SUMMARY
files the MISO coal-supply misclassification as *carried-forward* — re-stamps the
generic `COAL` group. This is a supplier choice in a local regen, not data
corruption.

## Why the committed bench is safe regardless
Deploy (`scripts/build_manifest.py` → `manifest.js` / `benchmark.js` /
`backcast-results.html`) assembles strictly from the **committed**
`bench/<ISO>/<year>.json.gz` parts; it does **not** rebuild bench from dispatch
or from the shared snapshots (which aren't committed). The doubling/flip can only
reappear via a *local* `dashboard_add_run` regen pointed at stale shared
parquets or supplied by the wrong (pre-coalclass) run. No regenerated MISO bench
was committed this session; the committed parts remain the miso6 coalclass values.

## Resolution
- No code change: the snapshot builder is correct and deterministic on `main`.
- Do **not** regenerate/commit `bench/MISO/*` from a local regen unless it is
  supplied by a coal-class-correct run (miso6) and built against a freshly
  materialized shared store.
- Verified: committed `bench/MISO/{2023,2024,2025}` all show COAL_PRB for
  889/997/1893/6017 and `Σ e_mon == e_ann × 1000` (no doubling) — left untouched.
