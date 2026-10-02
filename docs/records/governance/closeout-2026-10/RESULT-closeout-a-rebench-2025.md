# RESULT — closeout-A: 2025 re-bench on EIA-923 Final (W1, plan §4 ★2)

> Lane `closeout-a-rebench-2025`, 2026-10-02, chartered by the Backcast close-out desk.
> Branch `claude/closeout-a-rebench-2025` off `origin/main` `1120e32c`. **Zero LP.** No keeper,
> registry sidecar, run payload, keeper bundle or `src/` file changed.

## 1. Headline

**No ISO determination moves.** Seven of nine ISOs' `bench/<ISO>/2025.json.gz` parts are
regenerated on the EIA-923 Final 2025 rows PR #7015 landed; **MISO and PJM are stopped** at
charter step 1 (a refusal that is *not* the expected 2025 `eia923` mismatch, §3). The new
completeness audit reads **22 gate-eligible (ISO, class) pairs**, as the data README predicted.
Two 2025 C1 cells that were `SKIPPED (prelim 923)` now score **FAIL**: **SPP `COAL_PRB` +10.32 TWh
(+3.4 pp)** and **NWPP `CC_REGULAR` +9.60 TWh (+3.0 pp)**. Both ISOs were already NOT-YET, so
neither determination changes, but each is a new 2025 miss that the ISO's lane now owns.

| ISO | 2025 C1 before → after | 2025 C2 before → after | ISO determination before → after |
|---|---|---|---|
| ERCOT | 2 PASS, 5 SKIP → 2 PASS, 5 SKIP (COAL_PRB +3.63 → +5.75 TWh; LIGNITE +0.70 → +1.35, both PASS) | 1 PASS, 1 SKIP → same (gas −2.6 % → −3.8 %, still SKIP) | NOT-YET → NOT-YET |
| PJM | **stopped** (§3) — 8 SKIP, part not regenerated | 2 SKIP | NOT-YET → NOT-YET |
| CAISO | 6 SKIP → **3 PASS** (CC_REG +2.57, CC_CHP +0.73, CT_PEAKER −1.55 TWh), 3 SKIP | 2 SKIP → **gas PASS**, 1 SKIP | NOT-YET → NOT-YET |
| NYISO | 6 SKIP → 7 SKIP (COAL_PRB appears as immaterial) | 2 SKIP → 2 SKIP | CALIBRATED → CALIBRATED |
| NEISO | 6 SKIP → 6 SKIP (gas/coal families still incomplete) | 2 SKIP → 2 SKIP (gas +0.9 % → +2.9 %) | CALIBRATED → CALIBRATED |
| MISO | **stopped** (§3) — 8 SKIP, part not regenerated | 2 SKIP | NOT-YET → NOT-YET |
| SPP | 8 SKIP → 5 PASS, 2 SKIP, **1 FAIL: COAL_PRB +10.32 TWh / +3.4 pp** | 2 SKIP → 2 PASS (coal flags COAL_PRB) | NOT-YET → NOT-YET |
| SOCO | 7 SKIP → **2 PASS** (COAL_PRB +3.84, COAL_BIT +0.52 TWh), 5 SKIP | 2 SKIP → **coal PASS**, gas SKIP | NOT-YET → NOT-YET |
| NWPP | 8 SKIP → 5 PASS, 2 SKIP, **1 FAIL: CC_REGULAR +9.60 TWh / +3.0 pp** | 2 SKIP → 2 PASS (gas flags CC_REGULAR) | NOT-YET → NOT-YET |

C1 = `fuelmix`, C2 = `sysvol`. "Before" is `build_status.py` at the lane's base with the committed
parts; "after" is the same with the regenerated parts and completeness map. No 2025 record of any
other criterion (C3–C8, CO2, diurnal, forced share) changes status, and no year other than 2025 is touched.

## 2. Method — why the parts were rendered from the 2025 shard legs

A bench part is written by `render_backcast.generate` → `render_calibration_html.build_payload`,
which reads the bundle's `dispatch/<year>_P1.parquet` and `system.parquet`. The multi-class slice
split of the EIA-923 actuals keys on the model's plant×class set, so the part depends on the dispatch.
**No keeper span bundle on `main` carries either file** (gitignored; verified with
`git ls-tree origin/main` on all nine). Each keeper's 2025 **shard leg** does, by full SHA:

| ISO | 2025 leg | SHA (provenance) |
|---|---|---|
| NEISO | `neiso119_2025` | `5c17e451f0a0afeb62cecc55fd59c4d676a56b8b` |
| SPP | `spp100_arm_2025` | `7021af9b6056839e517715602097b70c9ab14a6a` |
| CAISO | `rcaiso20_A_2025` | `dd25e43f7b3c2d58c10595b864e3c50d6a546445` |
| SOCO | `soco96_2025` | `a8f322292558f3abc655dd9fedb8eeb8c7acbf40` |
| NWPP | `nwppnext16c_2025` | `1a41ba5122095ef749302ddf2cb9d67f4fe89dfe` |
| NYISO | `nyisonext26p_2025` | `bec68d76f2f192b381a728c84d3e45bb03db1266` |
| ERCOT | `r_ercot_24_2025` | `6abb7bef0192c9e061c5ffef656fb7d2a9f52f0f` |
| MISO (not used) | `miso280_arm_2025` | `6f39b705c5a1b7efe660b1d033934e2e786b54de` |
| PJM (not used) | `pjmnext16_A_2025` | `843493f7ec9870dd5a2e528edb0f77b4677e558f` |

For each leg, outside the repo tree: `git archive <sha> results/calibration/<leg>` →
`run_calibration_full.py --rebuild-benchmark <leg>` (the repo's own adopt-a-benchmark-change path;
it re-points only the scratch copy's meta) → `render_backcast.generate([(leg, path)], years={2025})`
with the output dirs redirected to scratch → only `bench/<ISO>/2025.json.gz` copied into the tree.
Run payloads (`runs/<id>.js`), sidecars and bundles are not regenerated.

**Control (parity) arm.** The same render was repeated with the two `_processed-legacy` EIA-923
parquets swapped back to their pre-#7015 blobs (`36046e32^`), then restored with `git checkout`:

* **ERCOT, SPP, SOCO, NWPP:** the `bench` payload is **byte-identical** to the committed part. The
  #7015 rows are therefore the whole change.
* **NEISO, CAISO, NYISO:** the control already differs from the committed part, which is pre-existing
  builder/reference drift and not #7015. NEISO: 8 fields (CT_PEAKER/ST_GAS/oil `classFull` and their
  CO2). CAISO: 18 fields (`classFull` scaled ≈ −2.7 %, `e930` cogen/CEMS grid, CO2). NYISO: plant 8906
  `npl` 1345 → 958 MW and its `campd` blob (the EIA-860 Final 2025 that landed in the same commit).
  Scored, this drift **changes no 2025 status** (control == before on every C1/C2 status; only
  CAISO C2-gas magnitude moves −2.1 % → +0.7 %, SKIP both ways). The committed parts carry both
  effects, because a part must reproduce at HEAD.
* In every regenerated part, `meta.builderFingerprint` moves to HEAD (`026141c892ee`). `meta.groups` is
  the 2025 class set, so a span-only class (NWPP `COAL_LIGNITE`) is absent from it. The assembler
  (`build_manifest.py`) unions groups across parts, so nothing is lost; that class only sorts later in
  the dashboard's group order.

NEISO also confirmed the #7015 delta is 2025-only at the frame level: the rebuilt `eia923` frame is
row-identical for 2019–2024 under old and new data, and 2025 goes from 173 to 1,644 rows.

## 3. What refused (charter step 1, verbatim)

`run_calibration_full.py --restore-shared-inputs results/calibration/<keeper bundle>`:

* **Expected 2025 mismatch (recorded, not "fixed"):** NEISO `eia923-a76984c81d70` → `0edb30122b08`;
  CAISO `b98a80836530` → `3785fa365975`; SOCO `6cb26c5d3591` → `1606828375ae`; NWPP
  `1100389783c0` → `063214082035`; NYISO `41fa13cb9274` → `6519d6df45de`; ERCOT `f114efa02db5` →
  `106ce0e9e5ca`. `campd` verified on each. For NEISO, the recorded hash does not reproduce even with
  the pre-#7015 data (`47c391a8133c`), so the recorded bytes already predate builder drift.
* **SPP:** `every shared benchmark input already resolves` (its store entries are present locally), so
  nothing was regenerated or compared.
* **MISO — STOPPED:** `--restore-shared-inputs results/calibration/miso280_span: 'campd' REGENERATED TO
  DIFFERENT BYTES than the solve read. meta.json records : ../_shared/MISO/campd-ea64a30b70a8.parquet
  rebuild produced : ../_shared/MISO/campd-fe5d500c94b8.parquet`
* **PJM — STOPPED:** `--restore-shared-inputs results/calibration/pjmnext16_A_span: 'campd' REGENERATED
  TO DIFFERENT BYTES than the solve read. meta.json records : ../_shared/PJM/campd-81e30da05901.parquet
  rebuild produced : ../_shared/PJM/campd-0789c1dbbf0d.parquet`

The harness denied no command. MISO's and PJM's 2025 parts stay preliminary. Their 2025 C1 rows now
read `complete` in places (the completeness map is ISO-wide) but stay **SKIPPED**: both ISOs' gas and
coal families audit incomplete, so they hold **zero** gate-eligible pairs and nothing scores against
the preliminary part. Unblocking them needs a ruling on the `campd` drift. It is the same CAMPD-builder
basis split `restore` is designed to refuse, and it predates this lane.

## 4. Completeness audit (`audit_eia923_completeness.py --year 2025`, committed)

22 gate-eligible pairs: ERCOT 2 (COAL_PRB, COAL_LIGNITE), CAISO 4 (CC_REGULAR, CC_CHP, CT_PEAKER,
CT_CHP), SPP 7, NWPP 7, SOCO 2 (COAL_PRB, COAL_BIT). Family-incomplete, so no gate: MISO, PJM, NYISO,
NEISO (both families), ERCOT gas, CAISO coal, SOCO gas (ST_CHP 1/26 plants missing).

## 5. Derived input moved: `data/raw/reference/nwpp_plant_basis_energy.csv`

`tests/unit/data/test_nwpp_demand_plant_basis.py::test_artifact_matches_bench_parts` pins this CSV to
the NWPP bench parts. It was re-derived with `scripts/data/derive_nwpp_plant_basis_energy.py` (rule 23:
its source data changed, namely EIA-923 Final 2025 via this re-bench). 2025 rows: **COL 42.0700 →
39.8545 TWh, NG 75.1592 → 74.1331 TWh**. **The NWPP keeper arms `nwpp_demand_plant_basis`**, so its
2025 solve input moved. The NWPP keeper's 2025 leg is now G-DRIFT LIVE against HEAD on this input, and
the next NWPP lane owes it a classification. The derive still writes only the preliminary-vintage
families for 2025; whether a Final vintage should widen that set is the NWPP lane's call.

## 6. Checks

* `build_status.py --iso all` → `build_status.py --check`: in sync (9 keepers).
* `check_bench_freshness.py`: no HARD failure; the seven regenerated parts reproduce at HEAD.
* Fast tier `pytest -n auto -m "not slow and not integration and not fulldata"`: 11,141 passed. Two
  failures are **pre-existing on `main` and unrelated**:
  `tests/unit/data/test_gas_offer_zonal_anchor_vintage.py::{test_training_window_mean_reproduces_the_registered_zone_table, test_reference_zone_window_mean_is_the_iso_anchor}`
  (Upstate_West runtime window mean 2.003931 vs registered 2.0346; they fail identically with this
  lane's changes stashed). The NWPP artifact test failed until §5 and passes after it.

## 7. Follow-ups for the desk

1. **MISO / PJM 2025 re-bench:** rule on the `campd` restore refusal (§3), then rerun this procedure
   on the two legs above.
2. **SPP COAL_PRB 2025 +10.32 TWh** and **NWPP CC_REGULAR 2025 +9.60 TWh**: new scored misses, routed
   to each ISO's lever sequence (plan §3).
3. **NWPP 2025 G-DRIFT** on the plant-basis anchor (§5).
