# PRECOMMIT — miso-292 Part 1: C3a load-weighted basis repair, MISO 2019 and 2022

```
LANE    : miso-292 (owner ruling "Repair basis (Recommended)", miso-291 §7)
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span), unchanged
LP      : none
```

Written before `lw_retrofit` is run.

## What changes

`scripts/data/derive_actual_lmp.py --lw-retrofit --years 2019 2022 --isos MISO` adds
`rt_lw / rt_lw_mon / da_lw / da_lw_mon / src_lw` to MISO 2019 and 2022 in
`data/raw/_validation-source/actual_lmp.json`. The same four numeric keys are then copied into
`frontend/data/backcast/bench/MISO/{2019,2022}.json.gz` `bench.avgLMP` by a surgical edit.
No bench regeneration (miso-266 hazard). Methodology citation: the rubric v2.4 C3 basis was
never applied to the two late-intaken years; this is a data-completeness repair, not a residual.

## Expected numbers (from the miso-291 reconstruction)

| year | rt_lw (full year) | C3a now (equal-hour) | C3a after (load-weighted) |
|---|---:|---:|---:|
| 2019 | ≈ 27.15 | +5.7 % | ≈ +2.8 % |
| 2022 | ≈ 74.53 | −15.5 % | ≈ −19.5 % (Jan–Oct masked via `rt_cov`) |

## Acceptance

1. `actual_lmp.json` diff touches only the MISO 2019 and 2022 records, and only adds the `*_lw`
   and `src_lw` keys. Any other byte moving is a STOP.
2. Every bench field other than the four `avgLMP.*_lw*` keys is identical after the edit.
3. Keeper re-score: determination and every criterion status unchanged; C3a 2019/2022 magnitudes
   within ±0.3 pt of the table above. A status flip or a miss outside that band is reported, not
   absorbed.
