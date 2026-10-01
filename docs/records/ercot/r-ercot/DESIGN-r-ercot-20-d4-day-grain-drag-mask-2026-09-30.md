# DESIGN — R-ERCOT-20: a day-grain mask for the residual `st_netload_drag` D-4 rows

Date 2026-09-30. **Zero LP. Not built.** Owner instruction: "Design d4".

Probes:
- `scripts/probes/_r_ercot20_d4_gap_census.py` → `r_ercot20_d4_gap_census.json`, `r_ercot20_d4_short_cover.json`
- `scripts/probes/_r_ercot20_d4_mask_footprint.py` (on the keeper's 2024/2025 legs, provenance SHAs `adfb6b34` / `29adb883`)

## 1. The object

The rider fails a plant whose own measured median MW, over the hours its drag floor binds, is 0.

There are 8 residual FAIL rows, all rubric-invisible:

| Plant | Fail years |
|---|---|
| 3452 Lake Hubbard | 2019, 2020, 2021, 2023 |
| 3628 R W Miller | 2019, 2020 |
| 3491 Handley | 2024, 2025 |

**Off-stretch census** (CAMPD plant total = 0):

| Plant-year | Zero h | < 1 day | 1–5 days | ≥ 5 days | ≥ 5 days already masked |
|---|---|---|---|---|---|
| 3452 2019 | 7,135 | 801 | 2,077 | 4,257 | 4,257 |
| 3452 2020 | 6,602 | 1,221 | 1,260 | 4,121 | 4,121 |
| 3452 2021 | 6,836 | 936 | 1,710 | 4,190 | 4,190 |
| 3452 2023 | 5,043 | 616 | 1,907 | 2,520 | 2,520 |
| 3628 2019 | 5,439 | 1,573 | 2,369 | 1,497 | 1,497 |
| 3628 2020 | 6,377 | 819 | 2,588 | 2,970 | 2,970 |
| 3491 2024 | 6,065 | 937 | 2,556 | 2,572 | 2,572 |
| 3491 2025 | 5,962 | 929 | 2,917 | 2,116 | 2,116 |

- The ercot-256 lay-up mask (≥ 5-day windows, K) already removes every ≥ 5-day stretch.
- **The residual is 1–5-day shutdowns plus intra-day cycling.**
- The R-ERCOT-19 month × hour profile could not reach this: it is a calendar-average shape, and these are specific days.

## 2. Designs tested at zero LP

| Design | New parameter | Handley 2024: binding h / median MW / zero share | Handley 2025 | Drag TWh removed 2024 / 2025 | Rider |
|---|---|---|---|---|---|
| Keeper | — | 4,389 / **0** / 0.57 | 4,891 / **0** / 0.58 | — | FAIL |
| **D-A**: also read the committed, unread 1–5-day economic lay-up companion `campd-unit-outages-layup-shortgas.csv` | none | 3,792 / **0** / 0.55 | 4,244 / **0** / 0.55 | 0.058 / 0.017 | **still FAIL** |
| **D-B**: mask binding hours inside a same-year CAMPD **plant-level all-units-off stretch ≥ 24 h** (hour grain) | the 24 h boundary | 2,620 / **104** / 0.29 | 2,877 / **105** / 0.28 | 0.140 / 0.042 | **pass** |

- **Why D-A misses.** The detector works in whole calendar days, so a 30-hour shutdown that straddles midnight holds no full off-day. Across the 8 rows the companion adds only 571–1,147 zero-hours; 1,230–2,868 stay uncovered. D-A is the clean one (it is the unread half of an existing detector, with zero new constants), but it **misses its object**. Do not build it for this purpose.
- **D-B hits** on the two rows that could be checked at zero LP (Handley 2024/25). The side-effect on Lake Hubbard/Miller 2024/25, which already pass, is removal of 0.004–0.08 TWh.
- **The 2019–2023 rows are unverified**: their floors are not on disk. The census (1–5-day hours ≫ < 1-day hours in every row) says D-B should flip them, but that is a prediction, not a measurement.

## 3. D-B as a mechanism

- **Construction.** A sub-gate inside `netload_drag_layup_window_mask` (rule 19: one mask family, one floor).
  - For each drag-covered ST_GAS plant, take the same-year CAMPD hourly plant total. Every stretch of ≥ 24 consecutive hours with all units at zero gross load removes that plant's drag floor for the stretch.
  - It composes with the ≥ 5-day mask by union. It removes floor only; it never adds energy.
- **Mode.** Backcast only. A forecast run gets `{}`, exactly as ercot-256's gate does.
- **DOF.** One declared structural constant: 24 h, the daily commitment cycle (the grain at which RUC and DAM commitment are decided).
  - It was **not swept**: only 24 h was measured.
  - It is still a choice, and it would be ledgered as one.
- **Rule 17 (for).** "A floor binding in hours its own driver evidence says the class is offline is a bug by definition." The drag is a RUC proxy. A day with every unit off is a day RUC did not hold the plant.
- **Rule 13 (the real cost).** A same-year, day-grain on/off record is close to the plant's **commitment outcome**.
  - ercot-256 was admitted as a *lay-up* (≥ 5 days, a strategic state).
  - At 24 h, the mask starts to encode the daily commitment the model should produce itself.
  - It removes forcing, never adds output, and never touches the forecast. But the dispatch being validated then differs from the one being forecast in exactly these plant-days.
- **Payoff.** Small.
  - Rubric-invisible.
  - ST_GAS forced energy falls ≈ 0.04–0.14 TWh per affected plant-year.
  - C8 ST_GAS sits 16–30 % and depends on D-4 only when a year runs over budget (2022, where no row fails today).

## 4. Recommendation

Do **not** build D-B now.

- It clears 8 rubric-invisible rows at the price of a new same-year commitment-grain input (rule 13) and a declared 24 h constant (rule 21).
- It would become worth building if a year's C8 ST_GAS goes over budget with one of these plants carrying the forced energy. The rider would then decide a determination.
- Kept as the ready design. D-A is recorded as tested and non-reaching.
