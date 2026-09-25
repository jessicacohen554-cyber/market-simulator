# PRECOMMIT — R-ERCOT-2: restore ERCOT DAM availability 2018–2020, and test the CHP heat-rate composition

**Session:** R-ERCOT, 2026-09-25. It orchestrates the shards and never solves itself (rule 32(a)).
**Owner instruction:** *"Both"* — do both follow-ups offered after the promotion of `2026-09-24-r-inputs-2019-2025`:
- (A) the CHP-off test;
- (B) the re-derive of the missing DAM availability back-years, followed by a 2019/2020 re-solve.

**Keeper under test:** `2026-09-24-r-inputs-2019-2025` (bundle `results/calibration/r_ercot_arm_span`, 2019–2025). The ISO reads NOT-YET, on 2023 C3b 0.232.

## 1. Data restoration (zero LP), done in this commit

**The defect.** `data/raw/ercot-thermal-dam-availability{,-hourly}.csv` and `…-site-hourly.parquet` carried only 2021–2025 on `main`. Yet `calibration-complete.json`'s intake_log records the 2018–2022 block as derived (+7,304 rows).

**Root cause, measured.** `scripts/data/derive_ercot_thermal_dam_availability.py` rewrote all three outputs to exactly `--years`. A later run over 2021–2025 therefore silently dropped 2018–2020.

**Fix: the script now MERGES by year.**
- A new `--write-years` flag names the years to write.
- Rows of every other year are kept byte-frozen.
- Rule 23 `[R-FROZEN-DERIVE]`: no constant, threshold or identification rule changed. This is data-completeness restoration of the source already on disk (the `data/raw/ercot-AS/60d_DAM_Gen_Resource_Data_2018..2022_*` extracts).

**Invocation.** `--years 2018 … 2025 --write-years 2018 2019 2020`, so the rating-fallback pool is the full span.

**Proof:**
- The committed 2021–2025 rows are byte-identical in both CSVs and `DataFrame.equals` in the parquet.
- A full-span replace would NOT have been identical: the cross-year rating fallback moves 4,520 day-class `rating_mw` values by up to 153 MW (avail up to 0.0134). That is why merge, not replace, is used.
- 2019/2020 fleet-only rebuild on the keeper recipe: the DAM overlay now fires (plant-grain, 12 CC / 10 coal / 4 ST / 2 CT crosswalked plants).
- Mean available MW, against the R-ERCOT arm census:

| class | 2019 | 2020 |
|---|---|---|
| COAL | 9,717 → 10,535 | 9,574 → 10,383 |
| CC_REGULAR | 23,387 → 23,824 | 22,476 → 23,002 |
| ST_GAS | 8,564 → 8,260 | 7,534 → 7,382 |
| CT_PEAKER | 4,015 → 3,987 | 4,228 → 4,127 |

- Inert for every keeper year 2021–2025, because those rows are byte-frozen.

## 2. Shards: nine legs, one year each (rule 36), pinned to this commit's SHA

All legs replay `results/calibration/r_ercot_arm_span` with `scripts/replay_keeper.py --years <Y>`. The keeper's own `config_partition_overrides` supplies each year's recipe: carve-out A for 2019–2022, carve-out B for 2023, forward for 2024/2025.

| leg | years | delta over the keeper recipe | purpose |
|---|---|---|---|
| `chpoff-<Y>` | 2019, 2020, 2021, 2022, 2023, 2024, 2025 | `--set measured_chp_heat_rates=false` (ONLY) | (A) isolate the CHP power-only rate. A full span, so it is registrable and promotable (rules 16/34(c)) |
| `dam-<Y>` | 2019, 2020 | none (keeper recipe on the restored data) | (B) 2019/2020 with DAM availability |

The keeper's own committed 2021–2025 numbers are the control for `chpoff` 2021–2025. The data change is byte-inert there, so G-DRIFT between the keeper SHA and this one is limited to this commit's data rows for 2018–2020.

**Signature hard stops.**
- Partition per year: 2019–2022 `swcap=true`, `ep_ref=true`, `CC_REGULAR.peak 151.008`; 2023 `swcap=true`, `ep_ref=false`; 2024/25 `swcap=false`, `CC_REGULAR.peak 4.576`.
- `measured_chp_heat_rates` is **false** on chpoff legs and **true** on dam legs.
- The other seven R-ERCOT flags are **true** on every leg.

## 3. Sealed predictions

- **P1 (A).** CC_CHP energy rises and CT_CHP falls against the keeper, in every chpoff year. These are the exact reverse signs of R-ERCOT P1.
- **P2 (A).** In 2023, C3b moves back toward the pre-R-ERCOT 0.146. **If the CHP composition is the cause, 2023 C3b ≤ 0.20** and the train tier reads CALIBRATED. If it stays > 0.20, the CHP rate is NOT the main cause, and that is reported as a refutation.
- **P3 (B).** 2019/2020 slack falls from 101 / 11 GWh, and COAL_PRB rises toward the actual. If C3a stays > +50 %, the missing DAM data was not the main 2019/2020 cause.
- **P4.** No re-tuning in either direction (rule 1(c)). A result that moves a gate the wrong way is reported at full magnitude.

## 4. Retention

- Every leg pushes its full bundle to its own branch (rule 34(a)).
- The parent fetches, verifies, composes, archives (rule 33) and registers every completed candidate (rule 15).
- Nothing is promoted without the owner (rule 31).
