# PRECOMMIT — capx D105: NEISO T1-F re-solve on keeper `2026-10-02-w0-neiso` (gate (d), one instrument)

**Lane:** capx **D105** (forecast solve shard) · **Date:** 2026-10-03 · **Model:** Fable (rule 27 `[R-PUSH]`) ·
**Data profile:** `neiso` (+ `shared`; the container is a FULL clone, so both hydrations were no-ops)
**Branch:** `claude/capx-d105-neiso-t1f`, fresh off `origin/main` **`828c54b6560b61aedc3eeebc929f9a214f808090`**
(the charter pinned `07f5b88e586909c0217c79024ffd5110c6c94c19`; origin had advanced by three merges — PR #7115
PJM-NEXT-33 census, PR #7116 closeout-CAISO-r40 (backcast `calibration_verdict.py` + CAISO attestation + status
parts), PR #7117 desk-r42 closeout plan — none touches `src/market_sim/`, `scripts/run_full_horizon.py` or
`scripts/lib/`, so the drift is INERT for the forecast path; recorded here per the charter).
**Authority:** owner ruling **Q76** (2026-10-03, capx ledger §0bn.2a rung 3; *"NEISO plus every ISO declared at
Q74"*) = plan §2.1b gate (d) for ONE instrument: **T1-F NEISO 2026–2030**. Nothing else is authorized.
**Prior:** `FINDING-capx-d102-2026-10-03.md` (every verdict STALE-SURFACE; NEISO post-verdict movers
`CC_STEAM_PART_REPAIR_ISOS`, `STORAGE_BASE_FLEET_MW`). **Chain precedents:** D50 (`FINDING-capx-d50-2026-09-04.md`,
the headline `neiso-t1f` run), D60 (`-pre-*` preservation), D99 (§2.2 probe method, scoring chain).

**Written and committed before any LP.** Hard stop 150 min wall-clock from the first command (03:42:47 UTC);
solve must have started by minute 80.

---

## 1. THE RECIPE (verbatim; the plan §2.1a owner-decided headline posture, no `--set`)

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
PYTHONPATH=.:src uv run python scripts/run_full_horizon.py \
  --iso NEISO --start-year 2026 --end-year 2030 --golden-posture \
  --out-dir results/ff-t1f-d105/neiso 2>&1 | tee results/ff-t1f-d105/neiso.log
```

Five solve-years, sequential, one invocation (rule 36 forecast clause); §2.1b window cap respected (5 years, no
`--full-solve-authorized`). No `--set`, no second recipe (rules 1, 24).

## 2. CONFIG PROBE AT ZERO LP (this HEAD)

Built exactly as the runner builds it — `run_full_horizon.main([...recipe args...])` with `solve_and_summarize`
stubbed to capture the request, then `resolve_policy_bundle` → `apply_iso_scenario_defaults(…, "NEISO")` as
`runner.run_scenario_iso` resolves it — and `dataclasses.asdict` of the resolved object diffed against the
committed headline `results/ff-t1f-d50/neiso/run_config.json` (`neiso-t1f`, PROMOTE, solved `9e48ff6`, key
`18515067bf4d2fbe`, 784 fields).

| | value |
|---|---|
| request key (pre-resolution) | `6455edce4c0dbc3e` |
| **resolved key (predicted `cache_key`)** | **`66fb439918cbefd6`** |
| D50 recorded key | `18515067bf4d2fbe` — reproduced to the character by `head_key(D50 payload, surface=False)` under the live drop rules |
| resolved fields | 949 (D50: 784) |

**Field diff, every differing field classified:**

| class | n | fields | key effect |
|---|---:|---|---|
| **schema-growth** (absent from D50, present here at its registered drop default — `False`, `None`, `"off"`, `"north_south"`, `0.288137`) | **166** | every added field but one (list in `probe_result.json`'s `added`; all in `_CACHE_KEY_OPTIONAL_FIELDS` at their `cache_key_drop_defaults()` value) | inert — verified: `head_key(D50 payload + vom + flag) = head_key(new payload)` |
| **retired** (present in D50, deleted since; rule 26) | 2 | `nyiso_firm_imports`, `retiree_cems_cap` — both in `_CACHE_KEY_RETIRED_FIELDS`, re-inserted at their retired default | inert |
| **other — owner-ruled default move, CCS seam (capx D65-B Acts A+B, OWNER RULING Q47, 2026-09-06, one PR / one re-key)** | 2 | `ccs_retrofit_vom_adder` **8.0 → 2.95** (re-identified to ATB 2024 v4.0.0, `scenarios.py` L5767 comment; `derive_entry_costs_from_atb.py::derive_ccs_retrofit_vom_adder`, pinned by `test_ccs_retrofit_fixed_cost_basis.py`); `ccs_retrofit_fixed_cost_co2_scaling` absent → **True** (default flipped False→True, declared in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`, drop value left `"False"`, so True enters the key) | **LIVE in the key**: payload-only key `18515067bf4d2fbe` → `c3519b861f920bbe` is explained by exactly these two (`head_key(D50 payload, vom→2.95)` = `a14503b0f70353d6`; + the flag = `c3519b861f920bbe` = `head_key(new payload, surface=False)`) |
| keeper-driven | 0 | — | the W0 keeper (`2026-10-02-w0-neiso`) reaches the forecast only through the solve-surface rows (§3), never through a `ScenarioConfig` field |

No field is unclassified. `ccs_retrofit_capex_co2_scaling` is `True` in both payloads (D60 default flip).

## 3. SOLVE-SURFACE FINGERPRINT

* **Recorded** in the D50 bundle: **absent** (`run_config.json`, `full_horizon_summary.json`, cache dir — the run
  predates capx D79's `surface_stamp`; the verdict's `provenance.solve_surface` is likewise absent). D102 §3
  reads the staleness off the dated witness (`neiso-t3-pre-d99`'s fp `8f90ae4dca904a66`, 7 moved rows).
* **Live** `surface_stamp("NEISO", resolved)` at this HEAD: fingerprint **`b514541af339c180`**, `epochs = []`
  (every `SOLVE_EPOCH` is `modes=("backcast",)`, so none reaches a forecast key — D102 §1), **9 moved rows** =
  `moved_rows("NEISO")`: `CC_STEAM_PART_REPAIR_ISOS 30824893196aaa12`, `GENERIC_BASE_OFFER_CURVE bdc2b348ec6144d1`,
  `LABELS 600aeac5bbcd256c`, `MAINTENANCE_MONTHLY_SHAPE b4da945d5a2e8f77`, `MIN_STABLE_PCT_PHYSICAL 262e67a17cf047e0`,
  `PLANT_CLASSES 3c91d80e901b878c`, `RGGI_MEMBER_STATES_BY_YEAR e432156b179ff182`, `STORAGE_BASE_FLEET_MW 50b5239e785ffb4f`,
  `THERMAL_AVAILABILITY 34ff308290e18439`. EIA-860 vintage digest `92179caf8dc3091311afbc70107198a9d1b9755a292b7117e035bb76b8626a98`.
* **Key decomposition:** `18515067bf4d2fbe` (D50) → `c3519b861f920bbe` (payload moves, §2) → **`66fb439918cbefd6`**
  (+ the 9 surface rows). Surface alone on the D50 payload would give `99ff9635abbf18a0`.

## 4. PRE-DECLARED EXPECTATIONS (graded in the FINDING)

Prior = `ff-verdicts.json["neiso-t1f"]` (D50, PROMOTE, 0 reasons, 0 caveats): FC-1 PASS · FC-2 PASS (RM band,
no cobweb, backstop 1.2 % ≤ 10 %) · FC-3 n/a · FC-4 n/a · FC-5 SKIPPED · FC-6 SKIPPED · FC-7 PASS (784 keys,
overlay-off, 8-entry ledger) · FC-8 PASS (6.7 min).

| row | expectation | why |
|---|---|---|
| FC-1 | PASS, all 14 invariants | the two CCS moves re-price the retrofit screen only; the nine surface rows are fleet/offer/availability tables the keeper already solves on in backcast |
| FC-2 | PASS; rows 1/3 unchanged in kind; **row 4 backstop share may move off 1.2 %** (expected to stay ≤ 10 %) | `STORAGE_BASE_FLEET_MW` and `THERMAL_AVAILABILITY` move the adequacy arithmetic; no mechanism changes |
| FC-3/4 | n/a (T1-F) | tier |
| FC-5 | SKIPPED unchanged | no corridor passed |
| FC-6 | SKIPPED unchanged | no battery / paired output passed |
| FC-7 | **PASS, detail string moves**: `949 config keys` (was 784); ledger **7 entries, 0 UNIDENTIFIED** (was 8 — `ccs_retrofit_capex_co2_scaling=True` is now the shipped default, so the NON-DEFAULT-scope builder no longer lists it; dry-run on the probe's resolved payload: *"INSTRUMENT — ALL 7 ENTRIES IDENTIFIED"*) | builder scope = non-default fields; `outage_source` stays `statistical` |
| FC-8 | PASS; wall **[6, 12] min** (D50 6.7 min; §2.4 anchor ~85 s median/yr → ~7 min), RSS **< 4.5 GB** (D50 3.46 GB) | T1-F budget is 45 min (`RUNTIME_WALL_BUDGET_S`) |
| **determination** | **PROMOTE → PROMOTE** | nothing above reaches a gating row |
| D102 movers | `CC_STEAM_PART_REPAIR_ISOS` and `STORAGE_BASE_FLEET_MW` are 2 of the 9 live rows; neither moves a verdict row beyond FC-2 row 4's detail and FC-7's key count | the census's prior |
| key | `66fb439918cbefd6` exact; `run_config.json` shows `ccs_retrofit_vom_adder 2.95`, `ccs_retrofit_fixed_cost_co2_scaling True`, `ccs_retrofit_capex_co2_scaling True`, `mode=forecast`, ISO NEISO | §2 |

Anything else that moves (an FC status, a reason, a caveat, a FAIL row) is **UNEXPECTED** and reported as such,
against interest, never repaired.

## 5. STOP CONDITIONS

1. `data/clean` build fails (any curate script non-zero) → STOP, report.
2. Solved `run_config.json` key ≠ `66fb439918cbefd6`, or differs on a field §2 did not classify → report; the
   bundle is still pushed; no repair.
3. Solve has not started by minute 80, or exceeds 45 min (`FC-8` budget) → STOP, push what exists, draft PR.
4. Any invariant I1–I14 FAILs → no re-solve, no threshold touched; report as UNEXPECTED, determination as scored.
5. Hard stop at 150 min.

## 6. SCORING AND REGISTRATION (zero LP, after the solve)

`check_forecast_invariants.py --run-dir results/ff-t1f-d105/neiso/NEISO/<key>` (the cache dir; output kept
beside the bundle as `invariants.txt` / `invariants.json`) → `build_forecast_dof_ledger.py results/ff-t1f-d105/neiso`
→ `forecast_verdict.py --tier t1f --summary … --run-config … --dof-ledger … --json-out
results/ff-t1f-d105/neiso/forecast_verdict.json` → `register_forecast_run.py --summary
results/ff-t1f-d105/neiso/full_horizon_summary.json --kind t1f --label d105-w0neiso --extra-meta
'{"verdict_key": "neiso-t1f", "charter_label": "capx D105 NEISO T1-F on 2026-10-02-w0-neiso"}'` (a T1-F
bundle registers through `--summary`, as D50/D60 did; `--bundle` is the hindcast path. The run id is
`neiso-2026-2030-d105-w0neiso`; the label is slug-safe because it enters the run id. `verdict_key` is the
registrar's own `meta` override (`_verdict_key`), used because `VERDICT_MAP` lives in `scripts/`, which this
shard never edits). `ff-verdicts.json`: current `neiso-t1f` copied byte-equal to `neiso-t1f-pre-d105`, new
condensed verdict written at `neiso-t1f` with `provenance` += `{run_id, session: "capx-D105"}` (writer:
`indent=1`, `ensure_ascii=True`, trailing newline — round-trip verified byte-identical). `program-status.json`
is not hand-edited. Committed bundle = the ff-t1f-d50/d60 slim convention (`run_config.json`,
`full_horizon_summary.json`, `forecast_verdict.json`, `dof_ledger.json`, invariants output, the cache dir's
`config.yaml` + `solve_surface.json` + `evolution_<year>.json`); parquet/npz/hourly/floor-retention dumps
gitignored, via a `/results/ff-t1f-d105/` block in `.gitignore` plus plain `git add`.

**Known leftover for the parent:** `VERDICT_MAP["neiso-2026-2030-d50-ccscapex"]` still reads `neiso-t1f`, so the
generated registry sidecar for the D50 run will bake the NEW verdict until the desk re-points it to
`neiso-t1f-pre-d105` (a `scripts/` edit outside this shard's charter — D60 did it in-lane).
