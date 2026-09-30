# RESULT — miso-292 Part 1: MISO 2019/2022 now scored on the load-weighted C3 basis. Determination unchanged; C3b 2022 flips PASS → FAIL.

```
LANE      : miso-292 (owner ruling "Repair basis (Recommended)", miso-291 §7)
PRECOMMIT : docs/PRECOMMIT-miso292-c3a-lw-basis-2026-09-30.md
KEEPER    : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span), unchanged
LP        : none
```

## 1. What was done

1. `uv run python scripts/data/derive_actual_lmp.py --lw-retrofit --years 2019 2022 --isos MISO`.
   `actual_lmp.json` gained `rt_lw / rt_lw_mon / da_lw / da_lw_mon / src_lw` on MISO 2019 and 2022
   and nothing else (the only removed line is the trailing-comma change on the preceding key).
2. The four numeric keys were copied into `frontend/data/backcast/bench/MISO/{2019,2022}.json.gz`
   `bench.avgLMP` by a surgical edit (same writer settings as `write_bench_part`: `json.dumps`,
   gzip level 9, mtime 0; `meta.builderFingerprint` untouched). The script asserted the original
   bytes round-trip exactly and that the decoded part, minus the four added keys, equals the
   original. **No bench regeneration**, so the miso-266 hazard never arises.
3. `check_bench_freshness.py --iso MISO`: 7 parts, 0 STALE, before and after.
4. `status/MISO.js` rebuilt (`build_status.py --iso MISO`); only the 2019/2022 price records moved.

## 2. Numbers

| | precommit | measured |
|---|---:|---:|
| 2019 `rt_lw` | ≈ 27.15 | **27.15** |
| 2022 `rt_lw` (full staged year) | ≈ 74.53 | **73.45** |
| 2022 scored actual (Jan–Oct masked, from `rt_lw_mon`) | — | **73.56** |

The precommit's 74.53 for 2022 did not reproduce (−1.08). The scored quantity is the Jan–Oct
hour-weighted mean of `rt_lw_mon` (73.56), which is what the rubric compares; the full-year field is
never scored for 2022 because Nov/Dec are partially staged.

Keeper re-score (`calibration_verdict.py --run-id 2026-09-28-miso-280-splitremap`), before → after:

| criterion-year | before | after | status |
|---|---:|---:|---|
| C3a 2019 | +5.7 % (equal-hour) | **+2.8 %** | PASS → PASS |
| C3a 2022 | −15.5 % (equal-hour) | **−18.5 %** | FAIL → FAIL |
| C3b 2019 | NRMSE 0.089 | **0.080** | PASS → PASS |
| C3b 2022 | NRMSE 0.190 | **0.224** | **PASS → FAIL** |
| DA diagnostic 2019 / 2022 | +3.5 % / −15.9 % | +0.7 % / −18.8 % | reported only |

Determination NOT-YET → NOT-YET; `reasons`, `caveats`, `grade_summary` byte-identical (C3b was
already failing on 2021). Train tier 2023–2025 untouched: CALIBRATED.

## 3. Reading

- C3a 2022 lands at −18.5 %, not the −19.5 % miso-291 estimated; the difference is the same
  full-year vs masked-months point as above.
- **C3b 2022 is a new failure-year**, which the precommit did not predict. The equal-hour monthly
  actual understated the summer months relative to the load-weighted one (Jun–Aug `rt_lw_mon`
  91.4 / 92.6 / 105.8 vs equal-hour 86.0 / 88.4 / 100.8), and the model's summer is where the
  Indiana congestion gap sits. It is the same object as C3a 2022 seen monthly, not a second defect.
- Rule 14 `[R-ACCURATE]` governs: the load-weighted basis is the consistent measure every other MISO
  year already uses, so it stays even though 2022 reads worse.

## 4. Where MISO stands

Full span NOT-YET on: C1 ST_GAS 2019, C3a 2022 (−18.5 %), C3b 2021 (0.252), **C3b 2022 (0.224, new)**.
No frontier. The 2022 pair is the object of the flowgate charter
(`docs/CHARTER-miso292-flowgate-program-2026-09-30.md`).
