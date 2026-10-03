# RESULT closeout-CAISO-impl: owner rulings R-33 and R-34 implemented (2026-10-03, zero LP)

Lane closeout-CAISO-impl (desk `session_01ALecU5Wjde4tkbLrnMExT9`), from the spec in
`HANDOFF-closeout-caiso-2-impl.md` and the evidence in `FINDING-closeout-caiso-2-cc-object-2026-10-03.md`
(both in this directory).
- **Keeper unchanged:** `2026-10-02-closeout-caiso-w1-arm2`, bundle `results/calibration/closeout_caiso_w1_a2_span`.
  Nothing was written into the bundle.
- **No LP, no shard, no promotion.** No other ISO's matrix shard was edited.
- **Base:** `origin/main` `bc4555c7`, with main `469ddcd7` merged mid-lane (NWPP keeper `2026-10-03-nwpp-next-22b-w0`
  landed). The R-34 diff is measured on the merged base.

## 1. Rulings (desk relay, 2026-10-03, verbatim card choices)

- **R-33** "Refute the gas fold for CAISO": CAISO joins `EIA930_GAS_FOLD_REFUTED` in
  `scripts/lib/benchmark_semantics.py`, and the CEMS cap is kept. Benchmark-only.
- **R-34** "Mask to RT-covered hours": the C3c scarcity-tail model count is masked to the RT-covered hours.
  - CAISO 2021 is relabelled "reference-window mismatch; like-for-like under-fire 0 vs 27, C3c-2024 class".
  - The rubric version is bumped.

## 2. Render surface (step 0 and the parity gate)

- **Scratch composite:** the seven arm-2 legs were fetched by SHA and composed per the HANDOFF recipe into a scratch
  dir outside the keeper bundle. The scratch registry sidecar points only at that dir and was never committed.
- **Parity gate, on HEAD before any edit:** `regen_dashboard.py --dry-run` reported **8 identical, 0 changed, 0 new**.
  No code drift.

## 3. R-33: decouple, then refute

**Decouple.**
- `benchmark_semantics.geo_biomass_outside_930_other(classfull, e930)` returns `max(0, OTHER + biomass − 930 other)`,
  or 0 with no `other` series.
- `gas_foldin_deflation` delegates to it after the refuted check.
- `derive_caiso_supply_consistent_demand.py` now reads its add-back through `geo_biomass_term_twh` → the new helper,
  never through the deflation.

**Byte-identity proof.**
- The committed demand CSVs already differ from a HEAD re-derive in 6 of 7 years. This is the pre-existing
  R-CAISO-4 code/data drift (2022: 219.538 → 219.275 TWh); it is not this lane's.
- So the proof compares two re-derives: HEAD before the change against post-change, with the R-33 bench parts in
  place. Result: **all 7 CSVs and `provenance.json` byte-identical**.
- The committed artifacts were restored and are untouched (rule 23).

**Refute.** `EIA930_GAS_FOLD_REFUTED = {"SOCO", "CAISO"}`, with the SOCO-60 test numbers cited in the comment.

**Bench regen.**
- Only the CAISO 2019/2020/2021 parts change in content (desk ack 2026-10-03: the 0.03 TWh deviation below is accepted as measured). 2022–2025 and the run payload were byte-identical after
  R-33. In 2022–25 only the R-34 builder stamp moves; see §5.
- Completeness (`eia923_2025.json`) is unchanged.

**Expected-numbers check (deviation reported to the desk before commit).**

| `classFull.CC_REGULAR` (TWh) | 2019 | 2020 | 2021 |
|---|--:|--:|--:|
| before (deflated reconcile, ×0.888 / ×0.935 / ×0.970) | 36.069 | 43.140 | 49.163 |
| HANDOFF expected | 40.660 | 46.166 | 50.694 |
| **got** | **40.630** | **46.132** | **50.685** |

Why the deviation:
- With the deflation gone, the target is capped at `fossil_cems_grid` + oil: 59.15 / 64.81 / 68.75.
- Raw EIA-923 fossil (57.75 / 63.58 / 67.59) sits inside the 3 % deadband of that cap, so the reconcile does not
  fire. `classFull` is now the raw EIA-923 grid record.
- The HANDOFF values are ×1.0007 / ×1.0007 / ×1.0002 of it. That fits a what-if back-derived from the rounded
  factors, not a code path difference.

| CAISO verdict record | before | after | status |
|---|---|---|---|
| C1 CC_REGULAR 2019 / 20 / 21 | +10.19 / +16.45 / +8.11 TWh | **+5.63 / +13.46 / +6.59** (expected +5.60 / +13.43 / +6.58) | FAIL → FAIL |
| C1 CC_CHP 2019 / 20 / 21 | +1.51 / +1.47 / +1.34 | +0.61 / +0.98 / +1.10 | PASS → PASS |
| C1 CT_PEAKER 2019 / 20 / 21 | +0.84 / +0.27 / +2.66 | +0.38 / −0.04 / +2.52 | PASS → PASS |
| C1 ST_GAS 2019 / 20 / 21 | −0.93 / −0.94 / −1.13 | −1.07 / −1.05 / −1.17 | PASS → PASS |
| C2 sysvol gas, actual, 2019 / 20 / 21 | 47.96 / 56.40 / 62.68 TWh | 54.03 / 60.31 / 64.62 | PASS → PASS |
| C8 ST_GAS 2019 immateriality text | 0.5 % of load | 0.6 % | text only |
| 2022–2025, every record | | byte-identical | |
| Determination | NOT-YET | **NOT-YET** | |

- **C2 second consumer.** CAISO does reach `calibration_verdict` ~l.2523: its `e930` carries `other`. The C2 gas
  actual therefore loses the deflation too, consistent with C1. No status moves.
- **2025 EIA-923 drift label.** No 2025 record moved, so the 2025 EIA-923 data-drift label does not apply to any
  row here.

## 4. R-34: the C3c mask and rubric v3.18

**Trivial test first** (`tests/scoring/test_tail_metric_payload.py::RtWindowMaskTests`).
- Setup: 1 zone, 24 h; RT is NaN for hours 0–11; model above threshold at hours 2, 3 and 14.
- Masked count 1, unmasked 3; the actual counts only hours 12–23.
- It failed before the render change and passes after.

**Render** (`scripts/render_calibration_html.py`).
- `_tail_hours` and `_gt_count` take `mask=`.
- In both branches, the overlay (`lam` / `lam_s`) and the fallback (max zonal dual), the model is counted only where
  the actual RT series is finite. That is the window the actual is counted on, and the same mask C3a's
  `_monthly_mae` applies.
- The payload is stamped `hoursGt200.window = "rt"`.
- The >$500 companion row is display-only and left unmasked.

**Scorer** (`scripts/calibration_verdict.py`).
- The scorer is stdlib-only and never sees hourly prices, so the mask lives in the render. The scorer side:
  - `RUBRIC_VERSION = "3.18"`, with a v3.18 block citing R-34.
  - On a stamped payload the coverage note reads "model and actual both counted on the RT-covered hours". An
    unstamped payload keeps "count is a lower bound".
  - `C3C_READING_LABELS[("CAISO", 2021)]` attaches the ruling's reading. It is fail-closed: RT-window payload and
    under-fire only, with the counts taken from the record.
- The CAISO 2021 caveat was not ledgered in the attestation. It comes from the v3.6 holdout-year standing rule,
  which still classifies it, so the relabel lives in the scorer and the keeper bundle is untouched.

**Docs.** Rubric header, §1 C3c "Window" bullet and §9 v3.18 entry; rule-history §28 (new), with "Changes to this
file" renumbered to §29.

**Per-(ISO, year, criterion) diff** of `calibration_verdict.py --json` over all 9 keepers, from main + R-33 to
main + R-33 + R-34:

| ISO-year | record | before | after | status |
|---|---|---|---|---|
| CAISO 2021 | C3c (RT) | model 88 vs 27 h, 3.26× | **model 0 vs 27 h**; reading "reference-window mismatch; like-for-like under-fire 0 vs 27, C3c-2024 class (owner ruling R-34, 2026-10-03)" | CAVEAT → CAVEAT |
| CAISO 2021 | C3c DA diagnostic (not gated) | model 88 vs DA 30 | model 0 vs DA 30 | SKIPPED → SKIPPED |
| CAISO 2023 | C3c (RT) | model 67 vs 47 h, 1.43× | **model 51 vs 47 h, 1.09×** | PASS → PASS |
| CAISO 2023 | C3c DA diagnostic (not gated) | model 67 vs DA 80 | model 51 vs DA 80 | SKIPPED → SKIPPED |
| ERCOT, MISO, NEISO, NWPP, NYISO, PJM, SOCO, SPP | every record | | identical | |

- Only `rubric_version` moves, in every run.
- The DA diagnostic rows print the same model count as the gated row, so they move with it by construction.
- Every determination is unchanged: CAISO, ERCOT, MISO, NWPP, PJM, SOCO and SPP read NOT-YET; NEISO and NYISO read
  CALIBRATED.
- The status parts for every ISO were rebuilt. For the other eight ISOs only `generated` and `rubric_version` moved.

**Other ISOs' payloads were not re-rendered.**
- They keep the pre-mask count and no `window` stamp. By the closeout-CAISO-2 census
  (`_closeout_caiso_2_c3c_window.py`), the pre-mask count equals the masked count for every one of them: MISO 2022
  reads 0 → 0, SPP 2019–25 read identically, and every other ISO-year has full RT coverage.
- Their verdicts carry the old "lower bound" note until their next render.

## 5. Bench-part builder stamp (54 other-ISO parts re-stamped)

`render_calibration_html.py` is a `PAYLOAD_SOURCES` member of `scripts/lib/bench_stamp.py`, so the R-34 render edit
moved the payload fingerprint (`29bf6a6f5186` → `92dfc33f7e7b`; aggregate `026141c892ee` → `9ebd23f9ea8f`). That
made 54 of 61 committed bench parts read STALE. `check_bench_freshness.py` went HARD red, and
`test_bench_stamp_payload.py::test_d_every_committed_part_resolves_to_a_known_builder_state` failed.

**Adjudication (the Y-8 method): the edit is bench-inert.**
- By construction: the R-34 hunks write only `run_years[year]["ordc"]` (run payload). They never read or write
  `bench[...]`, and the two helpers they change are called nowhere on the bench path.
- Empirically: the CAISO re-render under the new builder reproduced the 2022–25 bench blocks byte-identically, and
  2019–21 identically to the R-33 render.

**Re-stamp.**
- Only `meta.builderFingerprint` was rewritten, on the 54 non-CAISO parts: 48 from `026141c892ee`, 6 NWPP from the
  historical `f979bd82fd43`, which maps to the same pre-edit payload `29bf6a6f5186`.
- Each part's own gzip round-trip was verified exact first, with the writer's format: level 9, mtime 0.
- `bench` and every other `meta` field are verified unchanged on all 54.
- After: `check_bench_freshness.py`: **0 STALE** of 61. The stamp tests pass.
- **One knock-on, NWPP provenance only.** `data/raw/reference/nwpp_plant_basis_energy.csv` records the sha256 of
  each NWPP bench part it is derived from (`tests/unit/data/test_nwpp_demand_plant_basis.py::test_artifact_matches_bench_parts`
  pins that). The stamp rewrite changed those bytes, so the CSV was re-derived
  (`scripts/data/derive_nwpp_plant_basis_energy.py`; rule 23: its source bytes changed).
  - Only the `source_sha256` column moves. Every `year` / `family` / `twh` / `source` value is identical on all 44
    rows.
  - The file is not on the solve surface, and `twh` is the only column any solve reads.

## 6. Gates (step 4)

| Gate | Result |
|---|---|
| `audit_keepers.py --iso CAISO --check` | PASS, 0 failures, 0 warnings |
| `check_registry_payload_parity.py` | OK, 9 runs, 9 bundle dirs |
| `check_mechanism_matrix.py --base origin/main` | exit 0 |
| `check_bench_freshness.py` | 0 STALE / 61 |
| fast lane `pytest -n auto -m "not slow and not integration and not fulldata"` | 11,373 passed, 66 skipped, 3 xfailed; 1 failed (`test_nwpp_demand_plant_basis::test_artifact_matches_bench_parts`, caused by the re-stamp and repaired above; it then passes). The two failures the charter lists as pre-existing on main did not fail here. |

## 7. Matrix

- No cell verdict moves; no mechanism was tested.
- The CAISO shard's `gates` stamp quoted the pre-ruling fail-set numbers (C1 +10.19 / +16.45 / +8.11, C3c 2021
  "88 vs 27 h"). A dated re-score note now heads it. No other cell's text is wrong.

## 8. Follow-up noted, not done

- `EIA930_GAS_FOLDS_GEO_BIOMASS = {"CAISO"}`, the legacy no-`other`-series allowlist, now holds only a refuted BA,
  so that branch is unreachable for every committed bundle.
  - It is left in place because its removal is outside both rulings (rule 26 candidate).
  - Its tests are pinned on a stand-in BA.
