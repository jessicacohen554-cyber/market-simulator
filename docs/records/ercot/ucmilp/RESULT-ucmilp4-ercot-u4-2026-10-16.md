# RESULT — UC-4-ERCOT: arm U4, all seven ERCOT years, 2026-10-16

**Verdict: R (KILL #4, unserved energy; KILL #3, 11 control flips).** Not registered (charter; E13). Read against
`PRECOMMIT-ucmilp4-ercot-u4-2026-10-15.md` §§1–3 and Addenda A–E, which were fixed before any U4 number.

## 1. What ran

- **Pin:** uc-1.8 (`41cd55dc`, Addendum E; FIX-8 inert in outcome for ERCOT, FIX-9 LIVE on the solver path only).
  The shards ran at lane head `7024a383`.
- **Control:** keeper `2026-10-02-closeout-l1-coal-fuel` committed bundle. No control solve (rule 29b). The rescore
  under rubric 3.20 is identical to UC-3's (148/148 rows, 0 diffs).
- **Arm U4:** keeper + `unit_commitment_milp=true` + `uc_commitment_demand_source="da_forecast"` + per-unit `ut_h`/`mlf`
  (data epochs 2026-10-15a/b; `dt` stays class-table) + `ercot_gas_commitment_bridge=false` (rule-19 substitution). It
  keeps the keeper's reserve co-opt, so the u-gate is live (61–62 integer clusters). Nothing else changes.
- **Coverage:** all 7 years, one shard each, solved alone (rule 36). 365 windows per year (2,555 in total). Gap p95
  < 1e-3 every year. Composed and scored locally with `calibration_verdict`.

| year | leg (branch `claude/ucmilp4-ercot-<y>`) | Σ MILP s (mean / p95) | UC-3 uc-1.5 Σ MILP s | nodes p95 | gap p95 | TL hits | int / clusters | class-fallback (int) | peak RSS GiB | uplift $M (% of λ·load) | P1 dump MWh |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | `486151a7` | 10,419 (28.5 / 41.4) | 8,082 | 1 | 8.6e-4 | 0 | 62/141 | 49 (6) | 10.08 (12.61 run) | 33.9 (0.15 %) | 0 |
| 2020 | `d0d90c4b` | 11,276 (30.9 / 50.3) | 7,780 | 1 | 9.2e-4 | 0 | 61/141 | 50 (6) | 10.21 | 50.5 (0.42 %) | 0 |
| 2021 | `ab096e4c` | 16,183 (44.3 / 73.9) | 21,017 | 6.6 | 9.8e-4 | 0 | 61/139 | 50 (6) | 11.28 | 195.3 (0.20 %) | 0 |
| 2022 | `8acc4158` | 15,424 (42.3 / 62.8) | 19,100 | 1 | 9.3e-4 | **1** | 61/139 | 50 (6) | 11.30 | 112.5 (0.31 %) | 0 |
| 2023 | `9d031790` | 12,873 (35.3 / 54.1) | 8,837 | 1 | 8.9e-4 | 0 | 61/139 | 48 (6) | 11.48 | 35.1 (0.15 %) | 0 |
| 2024 | `61946aa0` | 11,546 (31.6 / 47.0) | 9,508 | 1 | 9.2e-4 | 0 | 61/139 | 49 (6) | 11.36 | 32.9 (0.22 %) | 0 |
| 2025 | `7f213c84` | 7,732 (21.2 / 43.8) | 13,261 | 1 | 9.8e-4 | 0 | 61/140 | 49 (6) | 11.46 | 59.4 (0.32 %) | 0 |

- **Wall:** 2019 total 11,431 s, which is **15.65×** P0+P1. The other legs reported their MILP sums (above), but not P0/P1
  split in a form this record kept. Their ratio is the same order: Σ MILP alone is 7.7k–16.2k s against UC-3's P0+P1 of
  0.9–1.7k s. Reported against the owner's 3×, not judged (D-2).
- **Memory:** peak RSS 10.1–11.5 GiB against the owner's 17.0 GiB gate (r16). The attempts
  blocked before the ruling are in Addenda B–D.
- **Pass bars:** uplift ≤ 2 % met in every year. TL hits ≤ 1 % of windows met (1/2,555).

## 2. Kills

| # | kill | result |
|---|---|---|
| 1 | infeasible window / no incumbent | did not fire |
| 2 | P1 infeasible | did not fire |
| 3 | control flip | **FIRES**: 11 flips (§3) |
| 4 | unserved > keeper + 500 MWh | **FIRES**: 2021 **129,429 MWh** (keeper 3,012.6; bar 3,512.6); 2022 **1,076 MWh** (bar 500); 0 in the other five years |
| 5 | non-determinism | not exercised (no leg completed twice) |

**KILL #4, mechanism (zero LP).**
- In 2021 the unserved energy falls in **66 hours: Uri, days 39–44 (8–13 Feb), plus day 102**. In those hours DF − actual
  averages **−5,230 MW** (min −10,436 MW).
- In 2022 it falls in **3 hours on day 356 (Elliott)**, with DF − actual ≈ −3.8 GW.
- The UC commits slow-start capacity against the measured DA forecast. P1 clears on actual load (rule 4). Between the two
  there is no real-time or RUC recommitment stage, so a large under-forecast cannot be covered by capacity left
  uncommitted and becomes slack at VOLL.
- This is structural, not an engine defect. ERCOT does run a RUC, and the arm as built has no analogue for it. The
  DF increment row (`uc_solve_log.engine.commitment_demand`) shows minima of −4.7 to −13.4 GW in every year, but only the
  two cold-snap events coincide with tight supply.

## 3. Gate table, control → U4 (UC-3 uc-1.5 as reference)

`data/ucmilp4_ercot_span/readings/gate_table.md` has every row. The flips:

| year | row | control | UC-3 uc-1.5 | **U4** |
|---|---|---|---|---|
| 2019 | C3a | +6.2 % P | +17.8 % F | **+29.9 % F** |
| 2020 | C3a | +2.5 % P | +19.6 % F | **+25.1 % F** |
| 2020 | C8 ST_GAS (as scored) | 23.6 % P | 30.2 % F | **33.1 % F** |
| 2021 | C1 CC | −0.83 TWh P | −8.37 F | **−9.35 F** |
| 2021 | C3a | +0.8 % P | +10.2 % F | **+52.0 % F** |
| 2021 | C3b | 0.066 P | 0.123 P | **1.593 F** |
| 2022 | C1 CC | −3.47 TWh P | −9.69 F | **−10.73 F** |
| 2022 | C3a | −8.4 % P | +8.4 % P | **+13.6 % F** |
| 2022 | C3b | 0.178 P | 0.176 P | **0.266 F** |
| 2022 | C8 ST_GAS (as scored) | 28.7 % P | 30.3 % F | **32.2 % F** |
| 2024 | C1 CC | −4.45 TWh P | −12.36 F | **−12.18 F** |

- **R4:** C8 with MECH 28 removed. 2022 ST_GAS falls to 12.1 % and 2020 to 9.4 %, both passing under R4 (`readings/r4.txt`).
  That leaves **9 flips under the inherited exclusions**.
- **Against UC-3, U4 adds 3 flips:** 2022 C3a, and C3b in 2021 and 2022.
- **Gains vs control:**
  - C1 CC and PRB in 2019/2020 go FAIL → PASS. T4 is met, as it was at UC-3.
  - 2024 C3a goes −11.3 % → +3.8 %.
  - 2024 C3c goes 11 h C → 27 h P.

**Price diagnosis.** Demand-weighted mean $/MWh, P1:

| year | U4 | UC-3 | U4 excl. U4 slack hours | UC-3, same hours |
|---|---|---|---|---|
| 2019 | 60.48 | 54.86 | 60.48 | 54.86 |
| 2020 | 31.77 | 30.38 | 31.77 | 30.38 |
| 2021 | 252.31 | 182.85 | 174.42 | 170.62 |
| 2022 | 85.31 | 81.40 | 83.02 | 81.27 |
| 2023 | 53.69 | 54.68 | 53.69 | 54.68 |
| 2024 | 32.35 | 32.67 | 32.35 | 32.67 |
| 2025 | 38.06 | 38.80 | 38.06 | 38.80 |

- The 2021 C3a/C3b move is mostly the 66 VOLL hours.
- Outside the slack hours, U4 sits $0.1–5.6 above UC-3 in 2019–22 and $0.3–1.0 below it in 2023–25.
- The 2019/2020 rise over UC-3 (+$5.6 / +$1.4) is where DA over-forecast hours do not offset under-forecast hours. It
  sits on top of the UC-3 decommitment pattern, which persists (§4).

## 4. Commitment readings

**Starts ÷ CEMS** (UC-3 convention, `_ucmilp_benefit_screen.screen_year`; `readings/arm_screen.json`):

| year | CC_REGULAR U4 (UC-3) | ST_GAS U4 (UC-3) | COAL_PRB U4 (UC-3) |
|---|---|---|---|
| 2019 | 417/3,070 = **0.14×** (0.11×) | 551/1,011 = 0.55× (0.46×) | 76/17 = 4.5× (3.4×) |
| 2020 | 869/3,489 = **0.25×** (0.22×) | 515/952 = 0.54× (0.47×) | 194/23 = 8.4× (7.0×) |
| 2021 | 2,286/3,849 = 0.59× (0.53×) | 436/1,042 = 0.42× (0.31×) | 11/30 = 0.37× (0.37×) |
| 2022 | 2,501/3,617 = 0.69× (0.56×) | 464/1,329 = 0.35× (0.24×) | 28/29 = 0.97× (0.86×) |
| 2023 | 745/2,689 = 0.28× (0.24×) | 623/936 = 0.67× (0.54×) | 44/38 = 1.16× (1.08×) |
| 2024 | 778/2,264 = 0.34× (0.25×) | 469/736 = 0.64× (0.54×) | 56/40 = 1.40× (1.48×) |
| 2025 | 990/2,556 = 0.39× (0.34×) | 361/981 = 0.37× (0.28×) | 28/31 = 0.90× (0.84×) |

- Every gas row moves toward CEMS compared with UC-3.
- **T1 is still wrong-sign against the control:** 2019/2020 control 0.16×/0.55× vs U4 0.14×/0.25×, with bars
  [0.40, 2.5] / [0.74, 1.35].
- **T3 is wrong-sign:** C3b 2019/2020 is 0.500 / 0.369 against bars ≤ 0.208 / ≤ 0.204.
- **T5** (troughs) was not separately computed. The kills already decide the verdict.

**Mean online GW from `uc_schedule`, UC-3 → U4:**
- CC: 19.95 vs 20.06 (2019) … 19.43 vs 19.39 (2025), Δ −0.3 to +0.04 GW.
- ST_GAS: +0.07 to +0.17 GW.
- So DA-forecast commitment barely moves the online fleet on average. Its effect is concentrated in the forecast-error
  tails.

**DF increment** (`commitment_demand`), mean / top-100 median / min / max MW:

| year | DF increment | QA-dropped hours |
|---|---|---|
| 2019 | 107 / 24 / −5,718 / 9,506 | 0 |
| 2020 | 130 / −68 / −4,740 / 9,114 | 0 |
| 2021 | 181 / 846 / −10,436 / 13,647 | 53 |
| 2022 | 112 / 916 / −13,350 / 8,717 | 0 |
| 2023 | 266 / 729 / −7,623 / 9,700 | 0 |
| 2024 | 198 / 14 / −6,947 / 13,174 | 0 |
| 2025 | 657 / 788 / −9,447 / 11,607 | 72 |

## 5. Defects and gaps

- **No engine defect.** Kills #1 and #2 did not fire. There was 1 TL hit, held at its incumbent.
- **Six integer clusters run on class-fallback parameters every year:** ST_GAS and CC_REGULAR in every year, plus one
  COAL_PRB from 2023 (`src` `MIN_STABLE_PCT_PHYSICAL[...]`, noload class-fallback), as at UC-3. `dt_h` is class-table for every cluster. Only
  `ut_h` is per-unit.
- **2021 reused its schedule** (`reused_schedule`, input digest `bc93aafb…`) from the same leg's first pass within the
  run. This is not a cross-year warm start.
- **The forced `_peak*` above-price reading (defect 6) was not computed for U4.** Total P1 output on `peak*` bands is
  0.33–2.32 TWh/yr. Only the above-price share is the defect-6 test.
- **The P0/P1 wall split is kept for 2019 only** (§1).
- **Coverage gaps:** none (7/7 years).

## 6. Recommendation

Record **R** for `unit_commitment_milp` (record stands) and for `uc_commitment_demand_source` in ERCOT, as armed. The
evidence that DA-forecast commitment needs a recommitment (RUC/RT) stage before it can be scored is the 2021/2022
slack. Without one, it converts measured forecast error into VOLL energy. That is a structural gap, and no parameter
should be fitted to close it. This is not a ruling on the field in other ISOs (rules 25 / 28d).

## 7. Bundles, cost, housekeeping

| artefact | where | promotable? |
|---|---|---|
| U4 legs | `claude/ucmilp4-ercot-2019` `486151a7` · `-2020` `d0d90c4b` · `-2021` `ab096e4c` · `-2022` `8acc4158` · `-2023` `9d031790` · `-2024` `61946aa0` · `-2025` `7f213c84`; 21 files each, `dispatch/<y>_P1.parquet` included, `unit_hourly` left out (rule 15) | in form (rule 34, all seven years); not recommended (R) |
| slim span + readings | `docs/records/ercot/ucmilp/data/ucmilp4_ercot_span/` (40 MB): `meta`, `run_config*`, `legitimacy_diagnostics.json`, `uc_solve_log_<y>.json`, `hourly/{class_band_hourly,class_hourly,system,storage,reserve_family,uc_schedule,uc_uplift}_<y>`, `readings/` (control and arm verdicts, flip diff, R4, starts screen, gate table, compose log) | not registered (E13) |

- **Composition:** `ucmilp3_ercot_span/scripts/compose_ercot.py`. The local span `results/calibration/ucmilp4_ercot_span`
  is gitignored and will not survive the container (rule 31).
- **Shards:** all 7 shard sessions were archived after `git ls-tree` plus byte verification (rule 33).
- **Branches for the owner to cut** (a session cannot delete them): `claude/ucmilp4-ercot-2019` … `-2025`.
- **Promotion question (rule 31):** this lane recommends no promotion. The leg bundles live only on the shard branches
  above.
