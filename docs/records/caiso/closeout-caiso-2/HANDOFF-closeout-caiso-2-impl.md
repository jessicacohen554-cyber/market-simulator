# HANDOFF — implement owner rulings R-33 and R-34 (CAISO; benchmark/rubric only, zero LP)

From lane closeout-CAISO-2 (session `session_01YJm3WSk44Cj76y2wAwGJuN`, stopped on a permission refusal). Evidence:
`FINDING-closeout-caiso-2-cc-object-2026-10-03.md` (this directory).
- **Keeper unchanged:** `2026-10-02-closeout-caiso-w1-arm2`, bundle `results/calibration/closeout_caiso_w1_a2_span`.
- **No shards, no LP.** Never write into the keeper bundle directory.

## Rulings (desk relay, 2026-10-03, verbatim card choices)

- **R-33** "Refute the gas fold for CAISO" (option A): add CAISO to `EIA930_GAS_FOLD_REFUTED`, keep the CEMS cap. This
  is benchmark-only.
- **R-34** "Mask to RT-covered hours" (option A): the C3c model tail count is masked to the RT-covered hours.
  - CAISO 2021 is relabelled "reference-window mismatch; like-for-like under-fire 0 vs 27, C3c-2024 class".
  - The rubric version is bumped.

Both rulings ship in **one PR**. Merge main first, because other lanes are landing on `calibration_verdict.py`.

## Step 0: a full bundle to render from (the keeper bundle on main is slim)

`regen_dashboard.py` needs `system.parquet`, `dispatch/` and the other root frames, and the committed keeper bundle
does not carry them. Rebuild them from the arm-2 shard legs. Every leg is still fetchable by SHA.

```bash
declare -A L=([2019]=1ca02579594490fff199211726b16eebcb225b65 [2020]=07535d603a74f94f56ce1ab3bf283942ed469ac4 \
  [2021]=905067f84abef9f4500dc431cd4ec5da2400438b [2022]=3a53b2ceab09756b2d7d03424f70774a50b0ab59 \
  [2023]=9794740e58ffe46c6a8563d7c23ae7f6cdb981f3 [2024]=61f6ad9322336d2a17264bce294927626976375c \
  [2025]=ebeacb2b9b3555dbfffec665c07cc33a4da07e34)
for y in "${!L[@]}"; do git fetch -q origin ${L[$y]}; git archive ${L[$y]} results/calibration/closeout_caiso_w1_a2_$y | tar -x -C .; done
printf 'results/calibration/closeout_caiso_w1_a2_20*/\nresults/calibration/caiso2_full_tmp/\n' >> .git/info/exclude
python scripts/probes/_closeout_caiso_w1_compose_span.py --iso CAISO --keeper results/calibration/closeout_caiso_w1_a2_span \
  --arm caiso_zonal_gas_basis=true $(for y in 2019 2020 2021 2022 2023 2024 2025; do echo --leg $y=results/calibration/closeout_caiso_w1_a2_$y; done) \
  --pinned-sha 566bc8fa3dd2ad6bdd5e56a2315c744c9be83e07 --out results/calibration/caiso2_full_tmp
K=results/calibration/closeout_caiso_w1_a2_span; T=results/calibration/caiso2_full_tmp
cp $K/calibration_attestation.json $K/fleet_census_20*.json $K/metrics.json $K/legitimacy_diagnostics.json $T/
python scripts/run_calibration_full.py --restore-shared-inputs $K   # eia923/campd/eia930, hash-verified
```

**Parity method (gate before any edit).**
1. Copy `frontend/data/backcast/registry/2026-10-02-closeout-caiso-w1-arm2.json` to a scratch registry dir.
2. Set its `"bundle"` to `results/calibration/caiso2_full_tmp`.
3. Run `python scripts/regen_dashboard.py --registry-dir <scratch> --dry-run`.
4. Measured on main `31f6af11`: **`dry-run parity: 8 identical, 0 changed, 0 new`** (the run payload plus the 7 bench
   parts). Re-confirm this on your base. A changed file here is code drift, and you must report it before the edit.

The composite's hourly sidecars, `meta.json` and `run_config*.json` are byte-identical to the committed keeper. Its
`legitimacy_diagnostics.json` is regenerated, so copy the committed one over it as above.

## R-33 implementation

1. **Decouple the demand derive first.** `scripts/data/derive_caiso_supply_consistent_demand.py` (~l.199) computes its
   geo/biomass term as `rch._gas_foldin_deflation(bench["classFull"], e930, ISO)`. Adding CAISO to the refuted set
   alone would make that term 0, so any re-derive would drop about 14 TWh of demand.
   - Add `geo_biomass_outside_930_other(classfull, e930) -> float` to `scripts/lib/benchmark_semantics.py`. It returns
     `max(0, OTHER + biomass − e930["other"])`, or 0 when there is no `other` key.
   - Have `gas_foldin_deflation` delegate to it in the re-extracted regime, after the refuted check.
   - Point the derive at the new helper. The value is identical.
   - Verify it byte-identically: run `derive_caiso_supply_consistent_demand.py --years 2019 … 2025` after the R-33
     bench regen. `git diff` on `data/raw/reference/caiso-supply-consistent-demand/` must be empty, with only the
     `provenance.json` timestamp changing, if it has one.
2. `EIA930_GAS_FOLD_REFUTED = frozenset({"SOCO", "CAISO"})`, with a comment citing R-33 and the SOCO-60 test numbers:
   930 gas − 923 gas FULL is −3.71 / −0.45 / +1.05 against F 14.76 / 15.07 / 14.48.
3. Update `tests/scoring/test_benchmark_semantics.py::test_gas_foldin_deflation_refuted_ba_is_zero`: it asserts the
   set equals `{"SOCO"}`. Add a test for the new helper (CAISO returns the same value the old deflation returned).
4. **Check the second consumer.** `calibration_verdict.py` ~l.2523 (C2 sysvol gas) also subtracts
   `bs.gas_foldin_deflation`, when `"other" in e930`. Determine whether CAISO reaches that branch. The lane's what-if
   patched only the bench parts, so C2 was not exercised. Report any C2 movement.
5. Regenerate the CAISO bench parts and run payload: the same `regen_dashboard.py --registry-dir <scratch>` without
   `--dry-run`; never commit the scratch registry sidecar (the committed one keeps its keeper bundle path). Then regenerate `completeness`
   (`audit_eia923_completeness.py`) and `build_status.py` for CAISO.
   - **Expected `classFull.CC_REGULAR`:** 40.660 / 46.166 / 50.694 (2019 / 2020 / 2021).
   - **Expected 2022–25:** unchanged, because 2022–24 are in band and the CEMS cap governs 2025.
   - **Expected verdict records:** C1 CC_REGULAR 2019 / 20 / 21 move from +10.19 / +16.45 / +8.11 to **+5.60 / +13.43 /
     +6.58**, all still FAIL.
   - **Expected C1 for the other classes:** CC_CHP +0.60 / +0.98 / +1.10, CT_PEAKER +0.38 / −0.05 / +2.52, ST_GAS
     −1.07 / −1.05 / −1.17, all PASS.
   - **Expected determination:** NOT-YET.

## R-34 implementation

The model count lives in the run payload. `scripts/render_calibration_html.py` ~l.2510–2570 writes
`ordc.hoursGt200.{model, overlay, actual}`, and `calibration_verdict.score_price_tail` reads it.
- **Mask in the render.** In both the overlay branch (`_gt_count(lam, thr)` / `_gt_count(lam_s, thr)`) and the
  fallback branch (`_tail_hours(model_price_by_zone, thr)`), count the model only on hours where the RT actual is
  finite. Use `_actual_rt_padded(iso, year, hours)` or `_actual_lmp_hourly`; NaN means no reference.
  - Give `_tail_hours` an optional `mask` argument.
  - Stamp `hoursGt200.window = "rt"` so a payload rendered before the change is identifiable.
- **Trivial test first.** Use 1 zone and 24 h. The actual RT is NaN for hours 0–11 and finite for 12–23. Put model
  prices above the threshold at hours 2, 3 and 14. The masked count is 1, the unmasked count 3, and the actual count
  only covers hours 12–23.
- **Rubric bump.** `RUBRIC_VERSION = "3.17"` becomes `"3.18"` in `calibration_verdict.py`. Add the v3.18 block
  comment citing R-34. Update `docs/calibration-determination-rubric.md` §5 (C3c) and
  `docs/governance/rule-history.md`.
  - The coverage note "count is a lower bound" in `score_price_tail` becomes a statement that both counts are on the
    RT-covered hours.
- **Rebuild status for every ISO.** The version stamp changes every part.

**Expected diff.** Take a per-(ISO, year, criterion) diff of `calibration_verdict.py --json`, before and after, over
every keeper. Only these may move:

| ISO-year | RT coverage | model, before | model, after | actual RT | status |
|---|--:|--:|--:|--:|---|
| CAISO 2021 | 0.652 | 88 | **0** | 27 | CAVEAT, relabelled (the C3c-2024 class) |
| CAISO 2023 | 0.995 | 67 | **51** | 47 | PASS → PASS |

Measured with `scripts/probes/_closeout_caiso_2_c3c_window.py`:
- MISO 2022 (coverage 0.863) reads 0 → 0.
- SPP 2019–25 (0.999) read identical (374 → 374 in 2021).

Only the CAISO payload is re-rendered. Other ISOs' payloads keep the pre-mask count, which equals the masked count for
all of them by this census. Say so in the RESULT.

- The CAISO 2021 relabel lives in the caveat label or classification text. Find where the "measured-input limitation"
  wording is produced, or ledger it in the keeper's `calibration_attestation.json` exceptions, and check whether the
  2021 caveat is ledgered.
- **Keep the determination unchanged.** CAISO stays NOT-YET.

## Close

1. Run `audit_keepers.py --check` (CAISO) and the registry parity gate.
2. Record both rulings verbatim in a RESULT beside this file.
3. Update the CAISO cells touched (evidence only) in `docs/codebase-site/data/mechanism-matrix/CAISO.js`. No verdict
   moves.
4. Open the PR, self-merge it on green, and report to the desk.
