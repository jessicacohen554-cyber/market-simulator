# PRECOMMIT — capx D106: NYISO T1-F re-solve on keeper `2026-10-02-w0-nyiso` (gate (d), one instrument)

**Lane:** capx **D106** (forecast solve shard) · **Date:** 2026-10-03 · **Model:** Fable (rule 27 `[R-PUSH]`) ·
**Data profile:** `nyiso` (+ `shared`; the container is a FULL clone, so both hydrations were no-ops, as for D105)
**Branch:** `claude/capx-d106-nyiso-t1f`, fresh off `origin/main` **`e2e296a43a86f70da5babc7f386d1bbc71e0874d`**
(the charter pinned `9f2fe6dfb284ba21e1daf20cb61917522813bc33`; origin had advanced by 17 commits / 6 merges —
PR #7135 SPP keeper text, #7139 NWPP keeper promotion (+ `program-status.json` re-key), #7140 closeout-PJM-nuc
records, #7141 solve-container swap provisioning (`scripts/lib/solve_container.py`, `prepare_solve_container.py`,
`shard_prompt.py`), #7142 NWPP sidecar text, and the R-49 SOCO coal-yard rows in `scripts/run_calibration.py`
(backcast runner only). None touches `src/market_sim/`, `scripts/run_full_horizon.py`, `scripts/lib/key_provenance.py`,
`forecast_verdict.py`, `build_forecast_dof_ledger.py` or `register_forecast_run.py`, so the drift is INERT for the
forecast path; recorded here per the charter. The clone is shallow, so the drift was read off the GitHub commit API.)
**Authority:** owner ruling **Q76** (2026-10-03, capx ledger §0bn.2a rung 3; *"NEISO plus every ISO declared at
Q74"* — NYISO declared `complete` at Q74, PR #7118, keeper `2026-10-02-w0-nyiso`) = plan §2.1b gate (d) for ONE
instrument: **T1-F NYISO 2026–2030**. Nothing else is authorized.
**Prior:** `FINDING-capx-d102-2026-10-03.md` (every verdict STALE-SURFACE; NYISO live moved rows = 11, post-verdict
movers `CC_STEAM_PART_REPAIR_ISOS`, `STORAGE_BASE_FLEET_MW`). **Sibling:** D105 (`PRECOMMIT-/FINDING-capx-d105-2026-10-03.md`,
PR #7138, NEISO: PROMOTE → PROMOTE, key moved by the two Q47 CCS defaults + 9 surface rows). **Chain precedents:**
D60 (`FINDING`/`PREDECL-capx-d60`, the headline `nyiso-t1f` run, `-pre-*` preservation), D99 (§2.2 probe method).

**Written and committed before any LP.** Hard stop 150 min wall-clock from the first command (05:28:45 UTC);
solve must have started by minute 80.

---

## 1. THE RECIPE (verbatim; the plan §2.1a owner-decided headline posture, no `--set`)

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
PYTHONPATH=.:src uv run python scripts/run_full_horizon.py \
  --iso NYISO --start-year 2026 --end-year 2030 --golden-posture \
  --out-dir results/ff-t1f-d106/nyiso 2>&1 | tee results/ff-t1f-d106/nyiso.log
```

Five solve-years, sequential, one invocation (rule 36 forecast clause); §2.1b window cap respected (5 years, no
`--full-solve-authorized`). No `--set`, no second recipe (rules 1, 24). `--golden-posture` resolves NYISO
curve-**OFF** (`capacity_market_clearing_by_iso` omits NYISO by owner decision C.4(a) B1), exactly as D60 solved.

## 2. CONFIG PROBE AT ZERO LP (this HEAD)

Built exactly as the runner builds it — `run_full_horizon.main([...recipe args...])` with `solve_and_summarize`
stubbed to capture the request, then `resolve_policy_bundle` → `apply_iso_scenario_defaults(…, "NYISO")` as
`runner.run_scenario_iso` resolves it — and `dataclasses.asdict` (YAML round-tripped, as the cache's `config.yaml`
and `run_config.json` record it) diffed against the committed headline `results/ff-t1f-d60/nyiso/run_config.json`
(`nyiso-t1f`, PROMOTE, solved `e7412237`, scored `7ed062ba`, key `19a9690bb12c8459`, 794 fields).
Probe output kept at `results/ff-t1f-d106/probe_result.json`.

| | value |
|---|---|
| request key (pre-resolution) | `f6cd689772b46485` |
| **resolved key (predicted `cache_key`)** | **`374fa81075c95ff8`** |
| D60 recorded key | `19a9690bb12c8459` — reproduced to the character by `head_key(D60 payload, surface=False)` under the live drop rules |
| resolved fields | 949 (D60: 794) |

**Field diff, every differing field classified:**

| class | n | fields | key effect |
|---|---:|---|---|
| **schema-growth** (absent from D60, present here at its registered drop default) | **156** | every added field but one (list in `probe_result.json`'s `classes.schema_growth`; all in `_CACHE_KEY_OPTIONAL_FIELDS` at their `cache_key_drop_defaults()` value) | inert — verified: `head_key(D60 payload + vom + flag)` = `head_key(new payload, surface=False)` = `f62431376dd9df03` |
| **retired** (present in D60, deleted since; rule 26) | 2 | `nyiso_firm_imports`, `retiree_cems_cap` — both in `_CACHE_KEY_RETIRED_FIELDS`, re-inserted at their retired default | inert |
| **other — owner-ruled default move, CCS seam (capx D65-B Acts A+B, OWNER RULING Q47, 2026-09-06)** | 2 | `ccs_retrofit_vom_adder` **8.0 → 2.95** (re-identified to ATB 2024; the same move D105 §2 classified); `ccs_retrofit_fixed_cost_co2_scaling` absent (`None` in D60) → **True** (default flipped, declared in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`, drop value left `"False"`, so True enters the key) | **LIVE in the key**: `19a9690bb12c8459` → `1da87a9755382292` (vom alone) → `f62431376dd9df03` (+ flag) = `head_key(new payload, surface=False)` — exactly these two |
| keeper-driven | 0 | — | the W0 keeper (`2026-10-02-w0-nyiso`) reaches the forecast only through the solve-surface rows (§3), never through a `ScenarioConfig` field |

No field is unclassified. `ccs_retrofit_capex_co2_scaling` is `True` in both payloads; `capacity_market_clearing`
`False` and `capacity_market_clearing_by_iso = {CAISO, MISO, NEISO, PJM: True}` in both (NYISO curve-OFF);
`nyiso_requirement_forecast_peak True` in both; `outage_source = statistical`; `mode = forecast`.

## 3. SOLVE-SURFACE FINGERPRINT

* **Recorded** in the D60 bundle: **absent** (the cache dir `NYISO/19a9690bb12c8459/` holds `config.yaml` and the
  five evolution ledgers only — the run predates capx D79's `surface_stamp`; the verdict's `provenance.solve_surface`
  is likewise absent). D102 §3 reads the staleness off the dated NEISO witness.
* **Live** `surface_stamp("NYISO", resolved)` at this HEAD: fingerprint **`1bde698e1ca4ad89`**, 228 rows,
  `epochs = []` (every `SOLVE_EPOCH` is `modes=("backcast",)`, so none reaches a forecast key — D102 §1),
  **11 moved rows** = `moved_rows("NYISO")` (the D102 census count for NYISO, HIT):
  `CC_STEAM_PART_REPAIR_ISOS 30824893196aaa12`, `GAS_OFFER_MARGIN_ANCHOR_BY_ISO 2e0bbf78a1ae14de`,
  `GAS_OFFER_MARGIN_ANCHOR_BY_ZONE 118ab6ce71c39f16`, `GENERIC_BASE_OFFER_CURVE bdc2b348ec6144d1`,
  `LABELS 600aeac5bbcd256c`, `MAINTENANCE_MONTHLY_SHAPE b4da945d5a2e8f77`, `MIN_STABLE_PCT_PHYSICAL 262e67a17cf047e0`,
  `PLANT_CLASSES 3c91d80e901b878c`, `RGGI_MEMBER_STATES_BY_YEAR e432156b179ff182`,
  `STORAGE_BASE_FLEET_MW c3139fbe1bfa3c5b`, `THERMAL_AVAILABILITY 34ff308290e18439`. EIA-860 vintage digest
  `92179caf8dc3091311afbc70107198a9d1b9755a292b7117e035bb76b8626a98` (same as D105). Two rows NEISO does not carry
  (`GAS_OFFER_MARGIN_ANCHOR_BY_ISO/_BY_ZONE`) and a different `STORAGE_BASE_FLEET_MW` row hash — the rows are
  ISO-scoped.
* **Key decomposition:** `19a9690bb12c8459` (D60) → `f62431376dd9df03` (payload moves, §2) → **`374fa81075c95ff8`**
  (+ the 11 surface rows) = `head_key(new payload, surface=True)`. Surface alone on the D60 payload would give
  `20de519d89d203a7`.

## 4. PRE-DECLARED EXPECTATIONS (graded in the FINDING)

Prior = `ff-verdicts.json["nyiso-t1f"]` (D60-R3, PROMOTE, 0 reasons, 0 caveats, rubric 1.1): FC-1 PASS (14) ·
FC-2 PASS (RM band, no cobweb, backstop 0.0 % ≤ 10 %) · FC-3 n/a · FC-4 n/a · FC-5 SKIPPED · FC-6 SKIPPED ·
FC-7 PASS (794 keys, gates `['capacity_market_clearing']`, overlay-off, 3-entry ledger all IDENTIFIED) · FC-8 PASS (10.9 min).
Priors: D102 (11 NYISO movers) and D105's outcome (PROMOTE → PROMOTE; every FC status unchanged; FC-2 row 4 and the
FC-7 detail strings moved; trajectory moved far more than the verdict through CCS dispatch).

| row | expectation | why |
|---|---|---|
| FC-1 | PASS, all 14 invariants | the two CCS moves re-price the retrofit screen only; the eleven surface rows are fleet/offer/availability/RGGI tables the keeper already solves on in backcast |
| FC-2 | PASS; rows 1/3 unchanged in kind; **row 4 backstop share may move off 0.0 %** (expected to stay ≤ 10 %) | `STORAGE_BASE_FLEET_MW` and `THERMAL_AVAILABILITY` move the adequacy arithmetic; D105 saw 1.2 → 0.0 %; no mechanism changes |
| FC-3/4 | n/a (T1-F) | tier |
| FC-5 | SKIPPED unchanged | no corridor passed |
| FC-6 | SKIPPED unchanged | no battery / paired output passed |
| FC-7 | **PASS, detail string moves**: `949 config keys` (was 794), gates unchanged; overlay-off PASS; ledger **3 entries, 0 UNIDENTIFIED, unchanged** (`forecast_xyear_warmstart`, `nyiso_requirement_forecast_peak`, `nyiso_requirement_vintage_factors`; dry-run of `build_forecast_dof_ledger.py` on the probe's resolved payload: *"INSTRUMENT — ALL 3 ENTRIES IDENTIFIED"*) | builder scope = non-default fields; `ccs_retrofit_capex_co2_scaling` was already the shipped default at D60, so unlike D105 no entry drops |
| FC-8 | PASS; wall **[7, 15] min** (D60 10.9 min = 656 s, per-year 189/130/112/115/110 s; §2.4 carries NO NYISO anchor; D105 ran 1.7× its D50), RSS **< 4.5 GB** (D60 3.45 GB) | T1-F budget is 45 min (`RUNTIME_WALL_BUDGET_S`) |
| **determination** | **PROMOTE → PROMOTE** | nothing above reaches a gating row |
| D102 movers | `CC_STEAM_PART_REPAIR_ISOS` and `STORAGE_BASE_FLEET_MW` are 2 of the 11 live rows; neither moves a verdict row beyond FC-2 row 4's detail and FC-7's key count | the census's prior |
| trajectory (not scored) | CO2 and `gas_cc` energy fall from 2028 as the converted `gas_cc_ccs` fleet dispatches at the 2.95 $/MWh adder (D105 §3 pattern); reported against interest, not attributed (one instrument, no control) | D105 |
| key | `374fa81075c95ff8` exact; `run_config.json` shows `ccs_retrofit_vom_adder 2.95`, `ccs_retrofit_fixed_cost_co2_scaling True`, `ccs_retrofit_capex_co2_scaling True`, `capacity_market_clearing False`, `mode=forecast`, ISO NYISO | §2 |

Anything else that moves (an FC status, a reason, a caveat, a FAIL row) is **UNEXPECTED** and reported as such,
against interest, never repaired.

## 5. STOP CONDITIONS

1. `data/clean` build fails (any curate script non-zero) → STOP, report.
2. Solved `run_config.json` key ≠ `374fa81075c95ff8`, or differs on a field §2 did not classify → report; the
   bundle is still pushed; no repair.
3. Solve has not started by minute 80, or exceeds 45 min (`FC-8` budget) → STOP, push what exists, draft PR.
4. Any invariant I1–I14 FAILs → no re-solve, no threshold touched; report as UNEXPECTED, determination as scored.
5. Hard stop at 150 min.

## 6. SCORING AND REGISTRATION (zero LP, after the solve)

`check_forecast_invariants.py --run-dir results/ff-t1f-d106/nyiso/NYISO/<key>` (the cache dir; output kept
beside the bundle as `invariants.txt` / `invariants.json`) → `build_forecast_dof_ledger.py results/ff-t1f-d106/nyiso`
→ `forecast_verdict.py --tier t1f --summary … --run-config … --dof-ledger … --invariants … --json-out
results/ff-t1f-d106/nyiso/forecast_verdict.json` → `register_forecast_run.py --summary
results/ff-t1f-d106/nyiso/full_horizon_summary.json --kind t1f --label d106-w0nyiso --extra-meta
'{"verdict_key": "nyiso-t1f", "charter_label": "capx D106 NYISO T1-F on 2026-10-02-w0-nyiso"}'` (the D105 chain;
run id `nyiso-2026-2030-d106-w0nyiso`). `ff-verdicts.json`: current `nyiso-t1f` copied byte-equal to
`nyiso-t1f-pre-d106`, new condensed verdict written at `nyiso-t1f` with `provenance` += `{run_id, session: "capx-D106"}`
(writer: `indent=1`, `ensure_ascii=True`, trailing newline — round-trip verified byte-identical on this HEAD).
`program-status.json` is not hand-edited. Committed bundle = the ff-t1f-d105 slim convention (`run_config.json`,
`full_horizon_summary.json`, `forecast_verdict.json`, `dof_ledger.json`, invariants output, the cache dir's
`config.yaml` + `solve_surface.json` + `evolution_<year>.json`, plus `probe_result.json`); parquet/npz/hourly/
floor-retention dumps and the log gitignored, via a `/results/ff-t1f-d106/` block in `.gitignore` plus plain `git add`.

**Known leftovers for the parent:** (a) `VERDICT_MAP["nyiso-2026-2030-d60-arm"]` still reads `nyiso-t1f`, so the
generated registry sidecar for the D60 run will bake the NEW verdict until the desk re-points it to
`nyiso-t1f-pre-d106` (a `scripts/` edit outside this shard's charter, as D105 left for NEISO); (b) D105's PR #7138
is not yet on `main`, so this PR and #7138 both touch `ff-verdicts.json`, `CHANGELOG.md` and `.gitignore` —
disjoint keys/blocks, a textual merge the desk resolves at whichever merges second.
