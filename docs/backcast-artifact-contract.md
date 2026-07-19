# Backcast Artifact Contract — bundle / registry / payload / bench / dashboard

> Status: ACTIVE — the written schema for the calibration-run artifact chain.
> Area: Calibration / dashboard. Precondition doc for any dashboard-adjacent
> refactor (refactor-consolidation plan §7-G). Documentation only — this file
> describes surfaces that already exist in code; **code is the source of truth**
> (CLAUDE.md), so where a field here disagrees with the producing script, the
> script wins and this doc is the bug.

## 0. What this is and why it is frozen

A calibration run produces two kinds of on-disk output:

1. a **bundle** under `results/calibration/<bundle>/` — the full solve record
   (dispatch, system duals, floors, provenance, the scorer's inputs); and
2. a set of **dashboard artifacts** under `frontend/data/backcast/` — the
   committed registry sidecar, the gzip+base64 run payload, the per-(ISO, year)
   bench part, and the all-ISO status/keeper/marker files the GitHub-Pages
   dashboard serves.

These two chains are joined by the run id (`<YYYY-MM-DD>-<shorthand>`) and by
the sidecar's `bundle` field. Three consumers reconstruct a run **from these
bytes alone**, so their field names and byte layout are a contract, not an
implementation detail:

- **the scorer** (`scripts/calibration_verdict.py`) reads the sidecar + payload
  + bench + bundle `run_config.json`/`meta.json`/`calibration_attestation.json`/
  `legitimacy_diagnostics.json` and re-derives the keeper verdict — it never
  re-solves;
- **the deploy** (`.github/workflows/deploy-pages.yml`) rebuilds
  `manifest.js`/`benchmark.js`/`completeness.js` from the committed sidecars +
  bench parts with **stdlib-only** scripts on a sparse, blobless checkout;
- **replay / goldens** (`scripts/replay_keeper.py`,
  `scripts/capture_keeper_goldens.py`) reconstruct the exact
  `solve_and_persist` kwargs from `meta.json` and re-solve byte-faithfully.

Rule 15 freezes the `frontend/data/backcast/` location and the "results live on
the dashboard" workflow; rule 20 ("keepers re-score in place") freezes every
field name a committed verdict is computed from — renaming one silently
re-grades every already-registered keeper. The **FROZEN list** in §9 enumerates
exactly what must not be renamed; §8 is the byte-determinism rule that lets
concurrent registrations merge without conflict.

## 1. Locations and path constants

| Constant (in `scripts/*`) | Path | Contents |
|---|---|---|
| bundle root | `results/calibration/<bundle>/` | one run's full solve outputs (mostly gitignored; the slim files below are committed) |
| `DATA` | `frontend/data/backcast/` | committed dashboard artifacts (frozen location, rule 15) |
| `REGISTRY_DIR` | `frontend/data/backcast/registry/` | one `<id>.json` sidecar per registered run |
| `RUNS_DIR` | `frontend/data/backcast/runs/` | one `<id>.js` gzip+base64 payload per run |
| `BENCH_DIR` | `frontend/data/backcast/bench/<ISO>/` | `<year>.json.gz` bench parts |
| `COMPLETENESS_DIR` | `frontend/data/backcast/completeness/` | `eia923_<year>.json` (EIA-923 vintage completeness) |
| — | `frontend/data/backcast/tail/actual_tail.json` | measured scarcity-tail counts (C3c actual) |
| — | `frontend/data/backcast/keepers.json` | current keeper per ISO + `keepers` array + frontier map |
| — | `frontend/data/backcast/calibration-complete.json` | holdout-quarantine markers + intake log |
| — | `frontend/data/backcast/statmode_d7.json` | D-7 statistical-mode fail-gap (reported) |
| generated | `frontend/data/backcast/{manifest,benchmark,completeness,status}.js` | assembled by the deploy; committed copy is local-preview only |

`manifest.js` / `benchmark.js` / `completeness.js` are **generated** — never
hand-committed; the deploy rebuilds them from the sidecars + bench parts so
concurrent same-ISO runs never conflict on them (`render_backcast.py` header;
build plan rule 15 / Git §3). `status.js` is the one exception — it is
**committed**, not deploy-rebuilt, because the C6 governance verdict reads
bundle files under `results/calibration/` that the sparse Pages checkout does
not fetch (`build_status.py` module docstring).

---

## 2. Bundle files (`results/calibration/<bundle>/`)

### 2.1 `meta.json` — the replay contract (~200 flag keys)

Written by `scripts/run_calibration_full.py` (the `meta = {...}` block, ~line
4101) from the exact keyword arguments `solve_and_persist` was called with.
This is the **authoritative snapshot** of the run's recipe: `replay_keeper.py`
and `capture_keeper_goldens.py` map each key back to a `solve_and_persist`
kwarg and re-solve; `--reuse-solved` reconstructs prior-year kwargs from it. It
carries ~200 keys — every calibration knob — so only the structural/identity
keys are tabulated here; the rest are the flat flag surface (coal/CT/CC
tranche, sigmoid overrides, mustrun, passthrough, ERCOT gas-basis, storage
cycling, …) that mirror the CLI one-for-one.

| Key | Type | Role |
|---|---|---|
| `timestamp` | ISO-8601 string (`isoformat(timespec="seconds")`) | run time; its date **derives the run id** (`render_backcast._run_meta`) |
| `iso` | string | ISO name (`ERCOT`, `PJM`, …); routes bench/zone/actuals lookups |
| `years` | list[int] | solved years (rule 16: all scorable years in one bundle) |
| `hours` | int | hours per year (8760); C3c/overlay array length |
| `passes` | sorted list[str] | which solve passes ran (`["P1"]`, or `["P1","P2"]`) |
| `commitment`, `commitment_screen_coal` | bool | legacy-P2 opt-in state |
| `gas_prices`, `outage_source` | string | provenance-only (ignored by replay) |
| `git_sha`, `highspy_version` | string | environment provenance (ignored by replay) |
| `coal_*`, `ct_*`, `cc_*`, `st_gas_*`, `tranche_*`, `*_overrides`, `ercot_*_gas_*`, `storage_*`, … | mixed | the ~180 remaining recipe knobs — the replayable flag surface |
| `reuse` | dict (optional) | `--reuse-solved` per-year source-bundle labeling (provenance only) |

**Replay mapping** (`replay_keeper.py`): `_REMAP` renames the handful of keys
whose `meta` spelling differs from the kwarg (e.g. `commitment_screen_coal` →
`screen_coal`, `coal_prb_sigmoid_overrides` → `prb_overrides`); `_IGNORE` drops
provenance/derived keys (`timestamp`, `passes`, `git_sha`, `highspy_version`,
`iso`, `years`, `hours`, `reuse`, `td_loss_factor`, …). Everything else is a
live kwarg. Adding a new solve knob means adding it to `meta` **and** teaching
replay whether it is a kwarg or ignored — a `meta` key with no home fails the
capture fidelity oracle loudly rather than silently.

### 2.2 `run_config.json` — self-contained run record

Written by `run_calibration_full.write_run_config`. Consumed by the scorer's
C6 governance gate, D-9 quarantine (`legitimacy_diagnostics.run_d9`), and
`render_backcast`/`build_manifest` for the run's free-text definition.

| Key | Type | Role |
|---|---|---|
| `timestamp` | string | mirrors `meta.timestamp` |
| `git` | dict | `{sha, dirty, …}` git provenance; `dirty` triggers a `model_changes.diff` sidecar |
| `model_changes_note` | string | free-text note; auto-derives the sidecar `shorthand`/`definition` |
| `ablation_of` | string \| null | D-3: base keeper this bundle ablates (historical; new twins no longer produced, rule 20 amended) |
| `calibration_flags` | dict | the subset of `meta` the scorer reads (iso/years/hours/passes/overrides/`git_sha`/…) |
| `scenario_config` | dict | **`dataclasses.asdict(cfg)`** — the entire resolved `ScenarioConfig` (D-9 reads its forbidden-flag keys) |
| `reuse` | dict (optional) | mirrors `meta.reuse` on a mixed reuse bundle |

`scenario_config` is a flat dump of the frozen `ScenarioConfig` dataclass;
loaders tolerate schema drift by keeping only fields the current dataclass
still defines (`render_calibration_html._tranche_bands_for_bundle`).

### 2.3 `metrics.json` — condensed verdict sidecar

Written by `calibration_verdict.write_metrics_sidecar` /
`condensed_metrics` (`--write-metrics`), indent=2. It is the scorer's **own**
condensed output — never hand-maintained. Fields: `run_id`, `iso`, `label`,
`target_years`, `scorable_years`, `data_blocked_years`, `rubric_version`,
`determination`, `reasons`, `notes`, `criteria` (`{cid: {label, tier, status,
caveat_kind?}}`), `caveats`, `grade_summary`, `free_class_score`. Small enough
to `git show` / `jq`; the per-class/per-year detail lives in the payload and
`legitimacy_diagnostics.json`.

### 2.4 `legitimacy_diagnostics.json` — `legitimacy-diagnostics/v1`

Written by `scripts/legitimacy_diagnostics.py --json-out` (`build_json_report`).
This is the committed contract the rubric's C7 (diurnal shape, reads **D1**) and
C8 (forced-energy share, reads **D2**) score from — the scorer **re-states**
these gates, never recomputes them, so the S1 suite stays the single
implementation.

Top-level shape:

```json
{
  "schema": "legitimacy-diagnostics/v1",
  "bundle": "results/calibration/<bundle>",
  "iso": "<ISO>",
  "years": [2023, 2024, 2025],
  "diagnostics": { "D1": {...}, "D2": {...}, "D4": {...}, "D5": {...}, "D9": {...}, "D10": {...}, "D6": {...} },
  "gates": { ... }
}
```

Each `diagnostics[<key>]` is `{name, passed, rows, summary, failures, notes}`
(from the `GateResult` dataclass). The `GateResult.name` prefix (`"D-1"`, …)
maps to the short key via `_JSON_KEYS` (note `"D-10"` is checked before `"D-1"`
because it is a prefix). Row schemas (each row is one dict; `verdict` is
`"pass"`/`"FAIL"` or a skip string):

- **D1** diurnal shape — `rows[]`: `year, class, profile_r, model_offpeak_cv,
  actual_offpeak_cv, cv_ratio, gated, verdict`. C7 reads these for gated classes
  (`CT_PEAKER`, `ST_GAS`).
- **D2** forced-energy attribution — `rows[]` (class × mechanism): `year, class,
  mechanism, forced_twh, class_total_twh, share_of_class`. `summary[]`
  (per-class total the C8 gate consumes): `year, class, forced_twh,
  class_total_twh, forced_share, limit, load_share, immaterial, lower_bound,
  verdict`.
- **D4** off-window binding — `rows[]`: `year, floor, window` (`"h<start>-<end-1>"`),
  `floored_twh, offwindow_twh, offwindow_share, verdict`. Windows are declared in
  the module-level `D4_WINDOWS` (`{(mech_id, class|None): (start, end)}`, local
  hours `[start, end)`); a mechanism forcing an over-budget class needs a cited
  `D4_WINDOWS` entry for the rubric-v2.2 grounded-above-budget pass path.
- **D5** forecast/backcast parity — `rows[]`: `mechanism, difference`
  (`"backcast-only"`/`"forecast-only"`), `declared_overlay, note, verdict`
  (`"declared"`/`"FAIL"`).
- **D9** overlay quarantine — `rows[]`: `bundle, check, value, verdict`. Read
  in CI (`--keepers`) to assert measured-outcome overlays are OFF.
- **D10** free-class-only rescore — `rows[]`: `year, fuel, provenance` (+ a
  `PINNED` flag when riding the L1 delivered-outcome renewable bound). Report-only.
- **D6** holdout quarantine (`--keepers` CI mode only; not written per-bundle) —
  `rows[]`: `run, iso, holdout_years, calibration_complete, verdict`.

`gates{}` embeds the thresholds so the verdict re-states, never re-types them:
`d1_min_profile_r` (0.8), `d1_min_cv_ratio` (0.5), `d1_offpeak_last_hour` (14),
`d1_gated_classes`, `d2_peaker_max_share` (0.15), `d2_merchant_max_share`
(0.30), `d2_exempt_classes`, `d4_max_offwindow_share` (0.05).

### 2.5 `calibration_attestation.json` — `calibration-attestation/v1`

The C6 governance-gate input (read by `calibration_verdict.load_artifacts`).
Top-level `schema` + a `governance` block asserting the CLAUDE.md legitimacy
rules for the run:

| `governance` key | Type | Rule |
|---|---|---|
| `levers_trace_to_measured_input` | bool | rule 10 (measured input, not the answer) |
| `no_fit_to_price_residuals` | bool | rule 11 |
| `no_pinning_to_actuals` | bool | rule 10 |
| `outage_filter_exogenous_net_load` | bool | rule 10 (availability is a physical event) |
| `attested_by` | string | who/what attested (keeper name + rationale) |
| `note` | string | free-text description of the run's structural levers |

### 2.6 `floors/<year>_<pass>.npz` — D-2/D-4 forced-energy input

Written by `run_calibration_full._save_floor_arrays` (`np.savez_compressed`),
one file per solved pass (`P1`, and `P2` when a legacy-P2 bundle ran). Consumed
by `legitimacy_diagnostics.py` (preferred over the `run_year(fleet_only=True)`
rebuild when present). Arrays and dtypes:

| Array | dtype | Shape | Meaning |
|---|---|---|---|
| `min_gen` | `float32` | `(n_gen, T)` | the min-gen lower bound the LP actually saw |
| `mechanism` | `int8` | `(n_gen, T)` | parallel `data.floor_mechanisms` id (0 = no floor) |
| `unit_ids` | `str` | `(n_gen,)` | LP unit alignment |
| `plant_code` | `int64` | `(n_gen,)` | plant code per unit |
| `plant_group` | `str` | `(n_gen,)` | plant class per unit |

No file is written for a fleet with no floor matrix (`min_gen is None`).

### 2.7 `p2_state/<year>.pkl.gz` — pickle v1 (+ planned v2 envelope)

Written by `run_calibration_full._save_p2_state` (`--persist-p2-state`):
`gzip.open(...); pickle.dump(p2_state, protocol=HIGHEST_PROTOCOL)`. The pickle
is the cached P1 inputs so the archived legacy-P2 pass can re-run as a
post-process. **Pickle identity is frozen** (refactor plan §1): the payload
binds these classes to their exact module paths —
`data.fleet.{Generator,FleetArrays}`, `model.dispatch.DispatchResult`,
`config.scenarios.ScenarioConfig`, `model.storage.StorageUnit`,
`results.outputs.FleetContext`, `config.iso_configs.TransferLink`. When any
defining module becomes a package, these classes must be defined **physically
in the package `__init__.py`** so `__module__` is byte-identical both ways.

- **v1 (current on disk):** the payload is the bare `p2_state` dict (keys
  include `year`, `config`, `fleet_arrays`, `fleet_arrays_p2`, `storage_units`,
  `links`, `dual_fuel_oil_mask`, `ercot_ordc_realized_adder`, …).
- **v2 (planned, refactor plan A4):** wrap as `{'format_version': 2, 'git_sha':
  …, 'state': …}`; a bare dict continues to read as v1. The plan also hardens
  `run_p2_layer`'s config rebuild to a defaults-merge instead of
  `with_overrides` on stale instances.

### 2.8 Supporting bundle parquet (gitignored; read at render time)

Not committed, but the render/scorer read them to bake scalars into the
committed payload/bench: `dispatch/<year>_{P1,P2}.parquet` (per-generator-hour
dispatch), `system.parquet` (per-zone hourly price + demand duals),
`storage.parquet` (per-unit charge/discharge), `btm.parquet` (behind-the-meter
CHP host supply held out of the LP), `scarcity.parquet` (post-solve overlay:
`year, hour, scarcity_adder, lmp, lmp_scarcity`), `model_changes.diff`
(uncommitted-edit snapshot when `git.dirty`).

---

## 3. Registry & dashboard artifacts (`frontend/data/backcast/`)

### 3.1 `registry/<id>.json` — manifest sidecar (`ENTRY_FIELDS`)

The full record a run commits so the deploy assembler
(`build_manifest.py::_load_entries`) can build `manifest.js` **from sidecars
alone** — no bundle access, no pandas, no model package. Produced by
`render_backcast.manifest_entry` (+ the `bundle` field written by the
`calibration-report` skill / `dashboard_add_run.py`).

Required — `build_manifest.ENTRY_FIELDS`:

| Field | Type | Role |
|---|---|---|
| `id` | string | `<YYYY-MM-DD>-<shorthand>` run id |
| `label` | string | display label (shorthand with `-`→space) |
| `date` | string | `id[:10]` |
| `shorthand` | string | kebab slug (`_slug`, ≤4 words; trailing `ablation` preserved) |
| `definition` | string | 1–3 sentence run definition (from `run_config.model_changes_note`) |
| `years` | list[int] | rendered years |
| `iso` | string | ISO name |
| `file` | string | `frontend/data/backcast/runs/<id>.js` |

Optional — `OPTIONAL_ENTRY_FIELDS` (passed through when present, never
required): `ablation_twin`, `market_story`, `ablation_of`. Plus `bundle`
(repo-relative bundle path) — **not** in `ENTRY_FIELDS` (the shell never needs
it) but load-bearing for the scorer (`load_artifacts` resolves the bundle from
it) and `resolve_run_id`. A skinny legacy sidecar (`{id, label, bundle, iso}`)
is upgraded from the bundle's `meta`/`run_config` (`_upgrade_skinny`);
`check_registry_payload_parity.py` enforces sidecar↔payload 1:1 (both
directions) and keeper/`ablation_*` cross-references.

### 3.2 `runs/<id>.js` — the run payload (`window.BC.runGz`)

Written by `render_backcast.generate`. The file is exactly one assignment
(**WIRE FORMAT** — the wrapper string is parsed by regex on the read side, so
it is frozen byte-for-byte):

```js
window.BC=window.BC||{};window.BC.runGz=window.BC.runGz||{};
window.BC.runGz["<id>"]="<gzb64 of the run model payload>";
```

The value is the **double-encoded** gzip+base64 of the per-run model dict
(`json.dumps(_gzb64(model))` — a JSON string literal whose contents are the
base64). The browser (`bc-data.js::loadRun` → `inflateGz`) `atob`s + gunzips it;
the scorer (`calibration_verdict._decode_run_js`) matches `= "<b64>"` with
`re.search(r'=\s*"([A-Za-z0-9+/=]+)"', text)` then `gzip.decompress`. The
decoded payload is `{label, years: {<year>: {...}}}`; each **year key** carries
(built in `render_calibration_html.build_payload`):

| Payload year key | Meaning |
|---|---|
| `plants` | `{plant_code: {m, m_ann, m_mon, r, nrmse, cap, tr?, b923?}}` — per-plant model CF (base64 uint8), annual/monthly TWh/GWh, capture metrics |
| `nonfossil` | `{nuclear, wind, solar}` model annual TWh |
| `fuelRows` | per-EIA-930-fuel `{fuel, m, b, r, nrmse}` (C2/C4 system fuel-vs-930 table; `m` = model TWh, total load = Σ `fuelRows[*].m`) |
| `gmModel` | `{class: TWh}` grid-delivered model generation mix |
| `lmp` | `{zone: {p, d, pMon, dMon}}` load-weighted price + demand weights (C3a/C3b) |
| `volErr` | signed volume error by `{class: {src, zoneMon|sys}}` (heatmap) |
| `co2` | `{model, byClass, basis:"full-plant"}` (C5a) |
| `storage` | `{throughput_twh, monthly_net_gwh}` (run-page diagnostic) |
| `lmpDeltaHr` | base64 int16 model−actual RT LMP per hour (Report tab; populate-on-render) |
| `lmpScar` | `{zone: {pMonScar}}` overlaid monthly price (when a scarcity sidecar exists) |
| `ordc` | `{maeEnergyOnly, maeOverlay, hoursGt200:{actual,model,overlay?}, hoursGt500{}, series, reldeployMw}` (C3c settlement tail) |

### 3.3 `bench/<ISO>/<year>.json.gz` — bench parts

Written by `render_backcast._write_bench_part`
(`gzip.compress(json.dumps(part).encode(), compresslevel=9, mtime=0)`). The
**committed source of truth** for the shared benchmark: each run rewrites only
its own ISO/years ("newest bundle covering the year wins"), and
`build_manifest._assemble_benchmark` unions the parts into `benchmark.js`. A
part is `{"meta": {...}, "bench": {...}}`:

- `meta`: `groups` (canonical fossil-class order), `groupLabel`, `zones`,
  `years` (`[int(year)]`).
- `bench` (per year — the actual benchmark all VOLUME/price/CO2 gates score
  against):

| Bench key | Contents |
|---|---|
| `plants` | `{code: {name, zone, group, npl, nodata, campd (b64 uint8), c_ann, c_mon, e_ann, btm, e_mon, ct_only?, ct_ratio?}}` |
| `e930` | per-fuel actual TWh: `gas, coal, nuclear, wind, solar` + optional `other`, `coal_cems`, and (corrupt-NG-cell ISOs) `gas_cems_grid`, `gas_cogen_grid`, `fossil_cems_grid` |
| `classFull` | `{class: TWh}` grid-delivered EIA-923 class total (BTM-subtracted), variable-renewables routed to 930 via `actuals_source` |
| `avgLMP` | actual mean LMP: `{da, rt, da_mon, rt_mon, da_lw, rt_lw, da_lw_mon, rt_lw_mon}` (equal-hour then load-weighted variants — key order is the frozen serialization order) |
| `storage` | `{throughput_twh, monthly_net_gwh}` actual storage discharge |
| `co2` | `{egrid, byClass, intensity, covPct, btmClass, basis:"full-plant"}` (C5a actual) |
| `ctOnly` | provenance rows for CT-only CEMS reporters (present only when non-empty) |

### 3.4 Generated dashboard files

| File | Producer | Globals (WIRE FORMAT) | Consumer |
|---|---|---|---|
| `manifest.js` | `build_manifest.main` (deploy) | `window.BC.meta`, `window.BC.manifest` | `bc-data.js::initBC`/`_probeDataRoot` |
| `benchmark.js` | `build_manifest.main` (deploy) | `window.BC.benchGz` (`{iso: gzb64}`) | `bc-data.js::loadBench` |
| `completeness.js` | `build_manifest.main` (deploy) | `window.BC.completeness` (`{year:{iso:{class:{status,gate}}}}`) | dashboard mix-table shading |
| `status.js` | `build_status.build` (**committed**) | `window.BC.status` | `bc-data.js::loadStatus` |

`manifest.js`/`benchmark.js`/`completeness.js` serialize with
`json.dumps(..., sort_keys=True)`; `status.js` with `sort_keys=True,
separators=(",",":")`. Each is written as
`window.BC=window.BC||{};window.BC.<name>=<json>;` — the `window.BC=window.BC||{}`
guard and assignment target are the wire format `bc-data.js` reads.

`window.BC.status` payload (`build_status`): `{generated, rubric_version,
rubric[], benchmark, methodology, keepers[]}` where each `keepers[]` entry is a
full `calibration_verdict.determine` verdict (so the page can never disagree
with the scorer), optionally carrying `frontier` and a reported `statmode_d7`
block. `--check` compares everything but `generated` to detect drift.

### 3.5 `keepers.json` — current keeper per ISO

Read by `build_status.py` (drives the Calibration Status page) and
`check_registry_payload_parity.py` (keeper→sidecar→payload existence). Shape:

- `"<ISO>": "<run id>"` — one per ISO (the display keeper);
- `"keepers": [<run id>, …]` — the array `build_status` iterates and the parity
  gate checks;
- `"note"` — human note;
- `"frontier": {"<ISO>": {declared, withdrawn?, note}}` — declarative
  frontier-achieved badges (never gating).

### 3.6 `calibration-complete.json` — holdout markers + intake log

Read by `legitimacy_diagnostics.load_calibration_complete` /
`run_d6_quarantine` (CI) and `run_calibration_full.py`'s `--year` guard. Keys:
`note`, `intake_log[]` (per-authorization `{date, scope, by, validation}`), and
`complete` — the marker map `{"<ISO>": {declared, keeper, by}}`. An ISO in
`complete` authorizes the one-shot frozen-config holdout score of 2022 /
2019 / H1-2026 (rule 22). Absent a marker, any registered bundle with a solve
year outside `{2023,2024,2025}` FAILs D-6.

### 3.7 `tail/actual_tail.json` — measured scarcity-tail actual (C3c)

Written by `scripts/data/derive_actual_tail.py`; read by the scorer's C3c gate
and surfaced by `build_status.py`. Shape: `{"isos": {"<ISO>": {"<year>":
{da_coverage, da_gt, rt_coverage, rt_gt, hours, threshold}}}}` — the count of
hours the hub RT/DA average cleared above the per-ISO threshold. 2023–2025 only.

### 3.8 `statmode_d7.json` — D-7 statistical-mode gap (reported)

Read by `build_status.py` and attached to each keeper verdict as
`statmode_d7`. Shape: `{note, measured, source, isos: {"<ISO>": {keeper_fails,
statmode_fails, probe_run_id, measured_against, note}}}`. Purely reported
(never gating); `stale` is set on the verdict when `measured_against` ≠ the
current keeper.

---

## 4. The three byte codecs (WIRE FORMAT — frozen)

These three encodings are what make the payloads compact **and**
byte-deterministic across re-renders (§8). The parameters below are the
contract.

### 4.1 `gzb64` — gzip + base64 of a JSON object

Identical implementation in `render_backcast._gzb64`,
`build_manifest._gzb64`, and `render_calibration_html.main`:

```python
base64.b64encode(gzip.compress(json.dumps(obj).encode(), compresslevel=9, mtime=0)).decode()
```

The three fixed parameters are the wire format: **`compresslevel=9`**,
**`mtime=0`** (so unchanged input → identical bytes → no git churn / clean
concurrent merge), and **default `json.dumps` separators** (`", "` / `": "` —
no `separators=` override on the payload/bench path; only `status.js` and the
`.js` globals use `sort_keys`/compact separators). Decode side:
`bc-data.js::inflateGz` (`atob` → `DecompressionStream('gzip')`) and
`calibration_verdict` (`base64.b64decode` → `gzip.decompress`). Bench parts use
the same codec but write the **gzip bytes directly** to `.json.gz` (no base64
wrapper); `benchmark.js` re-wraps them in base64 per ISO.

### 4.2 CF uint8 — per-plant capacity-factor series (`_b64`)

`render_calibration_html._b64`. Encodes an hourly CF series as base64 of a
length-8760 `uint8` array:

```python
a = np.clip(np.nan_to_num(cf), 0, 250).round().astype(np.uint8)   # cf passed in as 100*mw/nameplate
# pad/truncate to 8760, then base64(a.tobytes())
```

So each hour is **`round(100 * mw / nameplate)`** clipped to `[0, 250]` (a value
>100 is a plant over its nameplate; the 250 ceiling is headroom, still one
byte). Length is padded with zeros / truncated to exactly `_T = 8760`. Decode
side: `base64.b64decode(...)[:t]` yields the byte-per-hour percent
(`calibration_verdict` per-plant capture; browser heatmaps). This quantization
(±0.5% of nameplate) is exactly the tolerance D-2's "at floor" test budgets for.

### 4.3 int16 signed series — LMP delta heatmap (`_b64_i16`)

`render_calibration_html._b64_i16`. Encodes a signed hourly series (model
`$/MWh` minus actual `$/MWh`) as base64 of a length-8760 **little-endian
`int16`** array:

```python
out = np.full(v.shape, -32768, dtype="<i2")          # sentinel
out[finite] = np.clip(np.round(v[finite]), -32767, 32767).astype("<i2")
# pad to 8760 with the sentinel, then base64(out.tobytes())
```

The contract: **`<i2` little-endian** (so the browser's `Int16Array` decode is
machine-independent of the render host), 1-`$/MWh` resolution over
`[-32767, 32767]`, and **`-32768` reserved as the NOT-A-NUMBER sentinel** for
hours with no model dual or no actual price (rendered neutral, never colored).
The value is the absolute delta per hour — there is no delta-vs-previous-hour
step in the current implementation; the "int16-delta" naming refers to the
*price delta* (model − actual), not a temporal difference. Consumed only by the
Report-tab delta heatmap (`lmpDeltaHr`).

## 5. `window.BC.*` global names (WIRE FORMAT)

The dashboard shares one namespace; every producer opens with
`window.BC=window.BC||{}` and every consumer reads a fixed property name. These
names are frozen (renaming one breaks the shell and every `bc-data.js` entry
point):

| Global | Producer | Consumer (`bc-data.js`) |
|---|---|---|
| `window.BC.meta` | `manifest.js` | `initBC`, `getMeta`, `iso*` accessors |
| `window.BC.manifest` | `manifest.js` | run list |
| `window.BC.benchGz` | `benchmark.js` | `loadBench` (`inflateGz` per ISO) |
| `window.BC.completeness` | `completeness.js` | `getCompleteness` |
| `window.BC.status` | `status.js` | `loadStatus` |
| `window.BC.runGz["<id>"]` | `runs/<id>.js` | `loadRun` (then `delete`s the entry) |

`keepers.json` and `registry/<id>.json` are fetched as plain JSON (`loadKeepers`
/ `loadRegistry`), not via a `window.BC` global. `bc-data.js` self-heals
`DATA_ROOT` from `data/backcast` to the `../../frontend/data/backcast` fallback
for local `file://` preview (`_probeDataRoot`).

## 6. Producer → consumer summary

| Artifact | Producer script | Primary consumer(s) |
|---|---|---|
| `meta.json` | `run_calibration_full.py` | `replay_keeper.py`, `capture_keeper_goldens.py`, `render_backcast.py`, `--reuse-solved` |
| `run_config.json` | `run_calibration_full.write_run_config` | `calibration_verdict` (C6), `legitimacy_diagnostics.run_d9`, `render_backcast` |
| `metrics.json` | `calibration_verdict.write_metrics_sidecar` | humans / `git show` / CI |
| `legitimacy_diagnostics.json` | `legitimacy_diagnostics.py --json-out` | `calibration_verdict` (C7/C8) |
| `calibration_attestation.json` | (calibration session / attestation tooling) | `calibration_verdict` (C6) |
| `floors/<year>_<pass>.npz` | `run_calibration_full._save_floor_arrays` | `legitimacy_diagnostics` (D2/D4) |
| `p2_state/<year>.pkl.gz` | `run_calibration_full._save_p2_state` | `run_calibration_full.run_p2_layer` |
| `registry/<id>.json` | `render_backcast.manifest_entry` + `dashboard_add_run.py` | `build_manifest`, `calibration_verdict.load_artifacts`, parity gate |
| `runs/<id>.js` | `render_backcast.generate` | `bc-data.js::loadRun`, `calibration_verdict._decode_run_js` |
| `bench/<ISO>/<year>.json.gz` | `render_backcast._write_bench_part` | `build_manifest._assemble_benchmark`, `calibration_verdict.load_artifacts` |
| `manifest/benchmark/completeness.js` | `build_manifest.py` (deploy) | `bc-data.js` |
| `status.js` | `build_status.py` (committed) | `bc-data.js::loadStatus` |
| `keepers.json` | calibration session (hand-edited) | `build_status`, parity gate |
| `calibration-complete.json` | calibration session (hand-edited) | `legitimacy_diagnostics` (D6), `run_calibration_full` `--year` guard |
| `tail/actual_tail.json` | `scripts/data/derive_actual_tail.py` | `calibration_verdict` (C3c), `build_status` |
| `statmode_d7.json` | `scripts/run_statmode_probe.py` (registered) | `build_status` |

The deploy chain (`deploy-pages.yml`): sparse+blobless checkout of `frontend`,
`docs/codebase-site`, `scripts`, `learning-hub` → `build_manifest.py --site-dir
_site` → `build_codebase_site_backcast.py --site-dir _site` →
`register_hindcast.py --page-only --site-dir _site`. These three scripts must
stay **stdlib-only** (no numpy/pandas/model deps) and are named by literal path
in the workflow — moving or renaming them breaks the deploy.

## 7. Run-id derivation (frozen)

`render_backcast._run_meta` / `_slug`: `id = "<date>-<shorthand>"`, `date =
meta.timestamp[:10]`, `shorthand = _slug(note or bundle.name)` (kebab, stop-word
filtered, ≤4 words — a trailing `ablation` survives the cap so a twin's id is
its keeper's slug + `-ablation`). The id is the join key across the whole chain;
`replay_keeper.py` preserves `meta.timestamp` so a re-solve fixes a keeper **in
place** rather than minting a new id.

## 8. Byte-determinism rationale (conflict-free concurrent registration)

Every serialized artifact is byte-deterministic **by design** so that two
sessions registering different-ISO (or same-ISO, same-content) runs in parallel
never produce a spurious diff or a merge conflict:

- **gzip `mtime=0`** on every `gzb64`/`.json.gz` write — the gzip header would
  otherwise embed the wall-clock mtime, making identical input produce different
  bytes every render.
- **`sort_keys=True`** on the assembled `.js` globals, and **`sorted(...)`** over
  every `set` before it is serialized in `build_payload`
  (`gmModel`/`gm_model_full`/`groups`) — Python set iteration order is
  hash-randomized per process, so an unchanged run must not reorder.
- **Per-run / per-part files, never a shared mutable index.** Each session
  writes only its own `registry/<id>.json`, `runs/<id>.js`, and
  `bench/<ISO>/<year>.json.gz`; the shared `manifest.js`/`benchmark.js`/
  `completeness.js` are **rebuilt by the deploy** from those parts, so two
  concurrent registrations touch disjoint files and merge cleanly ("newest
  bundle covering the year wins" makes even a same-year bench overwrite
  order-independent when content matches).
- **Frozen key order where it is not sorted** — the `avgLMP` variant order and
  the bench-part field order are the committed serialization order, so a
  re-render is byte-stable against historically committed parts.

The result: registration is append-only at the file level, the dashboard is
reproducible from committed bytes, and the deploy is a pure function of the
sidecars + parts.

## 9. FROZEN list — rule-20 re-score-in-place forbids renaming these

Renaming or reshaping any of the following silently re-grades every registered
keeper (rule 20) or breaks the deploy/replay/parity chain. A refactor may move
code but must **not** rename these fields/paths/strings:

**Paths / locations**
- `frontend/data/backcast/` and its subtree names: `registry/`, `runs/`,
  `bench/<ISO>/`, `completeness/`, `tail/`, and the files `keepers.json`,
  `calibration-complete.json`, `statmode_d7.json`, `status.js`,
  `manifest.js`, `benchmark.js`, `completeness.js`, `tail/actual_tail.json`.
- bundle paths of already-registered runs (the sidecar `bundle` field); run-id
  slug derivation (`<date>-<shorthand>`).
- the three deploy scripts by literal path/command in `deploy-pages.yml`:
  `build_manifest.py`, `build_codebase_site_backcast.py`,
  `register_hindcast.py` (stdlib-only, sparse checkout).

**Wire-format strings**
- the `runs/<id>.js` wrapper (`window.BC.runGz["<id>"]="…"`) — matched by
  `_decode_run_js`'s `= "<b64>"` regex.
- the `window.BC.*` global names: `meta`, `manifest`, `benchGz`, `completeness`,
  `status`, `runGz`.
- the three codecs' parameters: `gzb64` (`compresslevel=9`, `mtime=0`, default
  json separators), CF uint8 (`round(100*mw/nameplate)`, clip `[0,250]`, length
  8760), int16 (`<i2` little-endian, `-32768` NaN sentinel).

**Field names read by a committed verdict**
- sidecar `ENTRY_FIELDS` (`id, label, date, shorthand, definition, years, iso,
  file`) + `bundle` + `OPTIONAL_ENTRY_FIELDS` (`ablation_twin, market_story,
  ablation_of`).
- `legitimacy-diagnostics/v1`: the `schema` string, the `D1`/`D2`/`D4`/`D5`/
  `D9`/`D10` keys, the D-1 gate columns (`profile_r`, `cv_ratio`, `gated`), the
  D-2 summary columns (`forced_share`, `class_total_twh`, `limit`, `load_share`,
  `immaterial`), the D-4 columns (`offwindow_share`, `window`), and the `gates{}`
  threshold keys.
- `calibration-attestation/v1` governance keys (§2.5).
- payload year keys and bench keys the scorer reads: `fuelRows[].{fuel,m,b,r,
  nrmse}`, `lmp[zone].{p,d,pMon,dMon}`, `gmModel`, `co2.{model,basis}`,
  `ordc.{hoursGt200,maeOverlay,…}`; bench `e930` fuel keys (incl. `coal_cems`,
  `gas_cems_grid`, `gas_cogen_grid`, `fossil_cems_grid`), `classFull`, `avgLMP`
  variant keys + order, `co2.{egrid,intensity,basis}`, `plants[].{campd,c_ann,
  e_ann,btm,nodata,ct_only}`.
- `meta.json` replay keys + `run_config.json` `scenario_config`/
  `calibration_flags` keys (replay + goldens + `--reuse-solved` reconstruct from
  them); the frozen `ScenarioConfig` field names/defaults (its `cache_key`
  hashes `asdict(self)`).

**Pickle identity** — the seven `p2_state`-borne classes at their exact module
paths (§2.7).
