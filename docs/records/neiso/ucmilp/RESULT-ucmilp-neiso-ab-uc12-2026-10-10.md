# RESULT — UC-2-NEISO relaunch at engine uc-1.2: MILP unit-commitment A/B on all seven NEISO backcast years (calibrated control) — **R: the span solves (2,555 windows, 0 infeasible); no gated flip; C3a moves away from 0 by > 1 pp in 2022 / 2024 / 2025, 2025 C3b +0.022, and |ΔC3a 2023| = 1.016 pp**

**Lane:** UC-2-NEISO · **Session:** `session_01D9RZoc9NrNhUBJLcYxyJx4` · **Date:** 2026-10-10 · **Branch:** `claude/ucmilp-2-neiso-ab-n7c2`.
**PRECOMMIT:** `PRECOMMIT-ucmilp-neiso-ab-2026-10-10.md` §§2–8 unchanged; Addendum C (relaunch ruled, pin, all seven years, G-DRIFT, diagnosis correction) and Addendum D (uc-1.2 L1 gate PASS) were pushed before any span shard. Addendum E (the budget restored to the charter rule, 228 min) was pushed while the legs ran and before any leg result was read except 2020's wall.
**Pin solved:** `eab17188c75cd0332f9323ed3464c62bc0cd1848` (main at PR #7230: engine uc-1.2, desk ruling (a), #7229 uc-params crosswalk, `uc_slim_window`).
**Supersedes for the mechanism cell:** the uc-1.1 record `RESULT-ucmilp-neiso-ab-2026-10-10.md` (R, kill #1). That record stands as the uc-1.1 history; its §5.1 diagnosis is corrected in Addendum C.
**LP in this session:** zero. There was one bench shard and seven year-isolated span shards (rule 36).
**Registered:** nothing (desk ruling, E13 keeper-only). Scoring used a local registration that was removed before the commit (PRECOMMIT §8(d)).

## 0. Headline

**At uc-1.2 the stage completes the NEISO span.**
- 2,554 of 2,555 windows are Optimal. One window (2022 window 1) hit the 600-s time limit with an incumbent at gap 1.08e-3; W2 allows 3 per year.
- No window was infeasible. 2021 and 2023, the uc-1.1 kill years, solve 365/365.
- Every leg's P1 is Optimal and unserved energy is 0 MWh in every year.

**The calibrated control does not flip on any gated criterion.** The three C3c CAVEAT → FAIL rows and the C6 UNATTESTED row are the unattested-probe artefact, at identical magnitudes.

**The verdict is still R by the fixed §7 rule, on three independent counts:**
1. **C3a moves away from 0 by more than 1 pp.** 2022 moves +2.5 → +4.0 % (+1.58 pp), 2024 +0.5 → +2.3 % (+1.82 pp) and 2025 +3.8 → +6.1 % (+2.32 pp).
2. **2025 C3b worsens by more than 0.02.** It goes 0.070 → 0.092 (+0.022).
3. **Kill #3 by the letter.** |ΔC3a 2023| = 1.016 pp against a 1-pp bar. The unrounded load-weighted mean moves $36.938 → $37.325 on a $38.10 actual. That move is *toward* the actual, by 0.016 pp past the line. Counts 1 and 2 decide the verdict without it.

**What changed from uc-1.1 is mostly scope, not quality.** Desk ruling (a) demotes every all-budget-pinned cluster to continuous. In NEISO that removes about a third of the CC fleet from the integer set, along with almost every ST_GAS and coal cluster:

| | uc-1.1 | uc-1.2 |
|---|---|---|
| CC integer clusters | 29–31 | 17–20 |
| CC integer GW | 13.6–15.2 | 8.2–10.3 |
| ST_GAS integer clusters | all | 0–3 (≤ 0.1 GW) |
| Coal integer clusters | all | 0–1 |

The smaller UC behaves differently from the uc-1.1 one:

| reading | uc-1.1 | uc-1.2 |
|---|---|---|
| Price body | lowered (C3a −1.4 … −6.5 pp) | raised slightly (+$0.15 … +$1.63/MWh; C3a +0.5 … +2.3 pp except 2020) |
| Make-whole uplift share | 3.6–6.2 % | 0.98–1.46 % (bar 2 %, met) |
| MECH 28 CC_REGULAR energy | 1–2.5 TWh/yr | 0.06–0.50 TWh/yr (0.1–1.2 % of class) |
| CC starts vs CEMS | 0.64–0.76× | 1.00–1.36×; the control is 1.00–1.38× |

**The price-side readings carry engine defect 6** (§2; desk r07): the MECH 28 floor forces CC_REGULAR `peak` tranches on in all 8,760 hours, against 14–467 h in the control. The R is the fixed rule's answer at this pin, not a structural rejection.

The structure bars for a K are not met. S2 CC moves closer to CEMS in 3 of 7 years and T2 rises in 3 of 7 years; both need ≥ 4. T1 moves *away* from 0 in every year.

### 0.1 GATESPEC §6.3 gate table

Control is keeper `2026-10-02-w0-neiso`, re-scored at HEAD on the same bench parts; it is identical to its registered record. Arm is the uc-1.2 span. Rubric 3.20 for both.

| year | C1 (class rows) | C2 | C3a (model/actual − 1) | ΔC3a pp | C3b NRMSE | C3c (> $300 h, model / RT) | C4 | C6 | C8 CC_REGULAR forced share (MECH 28 removed) | D-2 MECH 28 share CC | wall ratio | reading |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | all PASS → all PASS | PASS → PASS | +6.84 → +7.30 % PASS | +0.46 (away) | 0.105 → 0.108 PASS | PASS → PASS (0 / 0) | PASS → PASS | PASS → UNATTESTED* | 0.7 → 1.9 % (0.7 %) PASS | 1.2 % | **12.2** | no flip |
| 2020 | all PASS → all PASS | PASS → PASS | −1.23 → −1.91 % PASS | −0.68 (away) | 0.111 → 0.116 PASS | PASS → PASS (0 / 0) | PASS → PASS | — | 1.7 → 2.1 % (1.5 %) PASS | 0.6 % | **9.9** | no flip |
| 2021 | all PASS → all PASS | PASS → PASS | +2.85 → +3.37 % PASS | +0.52 (away) | 0.120 → 0.130 PASS | PASS → PASS (0 / 2) | PASS → PASS | — | → 1.8 % (1.2 %) PASS | 0.6 % | **17.6** | no flip; uc-1.1 kill year now solves |
| 2022 | all PASS → all PASS | PASS → PASS | +2.47 → +4.05 % PASS | **+1.58 (away)** | 0.091 → 0.104 PASS (+0.013) | CAVEAT → FAIL* (0 / 117, unchanged) | PASS → PASS | — | 1.1 → 1.7 % (1.1 %) PASS | 0.5 % | **22.2** | no flip; **wrong-way > 1 pp** |
| 2023 | all PASS → all PASS | PASS → PASS | −3.04 → −2.02 % PASS | **+1.02 (toward 0; 1.016 unrounded)** | 0.096 → 0.099 PASS | CAVEAT → FAIL* (0 / 15, unchanged) | PASS → PASS | — | → 1.0 % (0.4 %) PASS | 0.7 % | **20.6** | no flip; **the 1-pp bar year, 0.016 pp over** |
| 2024 | all PASS → all PASS | PASS → PASS | +0.46 → +2.28 % PASS | **+1.82 (away)** | 0.152 → 0.164 PASS (+0.012) | PASS → PASS (0 / 8) | PASS → PASS | — | 0.7 → 1.2 % (0.5 %) PASS | 0.7 % | **19.7** | no flip; **wrong-way > 1 pp** |
| 2025 | SKIPPED → SKIPPED (preliminary EIA-923) | SKIPPED | +3.80 → +6.12 % PASS | **+2.32 (away)** | **0.070 → 0.092** PASS (**+0.022**) | CAVEAT → FAIL* (0 / 20, unchanged) | PASS → PASS | — | 0.5 → 0.7 % (0.6 %) PASS | 0.1 % | **15.5** | no flip; **wrong-way > 1 pp; C3b worse > 0.02** |

\* **Unattested-probe artefact.** The probe carries no `calibration_attestation.json`, so C6 reads UNATTESTED. The rule-22 C3c ledger route is therefore unavailable, and the keeper's ledgered CAVEAT scores FAIL on the probe at the identical magnitude (SPP Addendum D(3) precedent).
- **Determination:** control CALIBRATED; arm NOT-YET, on those artefacts only. No gated criterion fails.
- **C8:** the scorer at this pin budgets `uc_schedule` energy in C8, while R4 says report-only, so the share is given both ways. CC_REGULAR stays far below the 30 % cap either way.
- **C8 control values:** the control's 2021 and 2023 C8 values are in its registered record and are not repeated here; the scorer's status for both is PASS → PASS.

**Gating rows outside the criteria (PRECOMMIT §3), all met:**
- every leg's P1 is Optimal;
- unserved energy is 0.0 MWh in both arms, every year;
- the D-4 FAIL set is identical to the control's: the 2021 `chp_steam` plant 54605 row; no new row.

**D-1 is not gating here, so it is reported only.** The arm adds 2024 COAL_BIT (profile r 0.729) and 2025 COAL_BIT (off-peak CV ratio 0.491). It drops the control's 2020 COAL_PRB row. The other D-1 rows, COAL_BIT 2020/2022/2023, COAL_PRB 2021 and CT_PEAKER 2025, are the control's own.

### 0.2 GATESPEC §6.1 wall rows

Run conditions: standard solve container, 4 cpus, `MARKET_SIM_HIGHS_THREADS=1`, solver path `{presolve on, feasibility_jump off, lp_heuristics off, symmetry on, restart off}`, `uc_slim_window=True`. The baseline is the same shard's P0 + P1 (the PRECOMMIT §5 proxy).

| ISO-year | baseline P0+P1 s | P0 s | UC Σ s (365 windows; mean / p95 MILP s) | P1 s | total s | **ratio** | integers/window (int. clusters / clusters) | nodes p50 / p95 | gap p95 | time-limit hits | non-optimal windows | peak RSS GB (UC / cgroup) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NEISO 2019 | 293.3 | 146.9 | 3,211.9 (8.68 / 32.32) | 146.4 | 3,591.8 | **12.2** | 648 (18 / 61) | 9 / 118 | 9.95e-4 | 0 | 0 | 4.29 / — |
| NEISO 2020 | 192.2 | 96.4 | 1,640.7 (4.40 / 13.71) | 95.8 | 1,899.8 | **9.9** | 684 (19 / 64) | 3 / 59 | 9.97e-4 | 0 | 0 | 4.38 / — |
| NEISO 2021 | 214.3 | 108.8 | 3,478.9 (9.43 / 39.13) | 105.5 | 3,765.5 | **17.6** | 792 (22 / 68) | 11 / 170 | 9.95e-4 | 0 | 0 | 4.46 / — |
| NEISO 2022 | 312.5 | 155.1 | 6,516.3 (17.72 / 55.45) | 157.4 | 6,924.9 | **22.2** | 684 (19 / 69) | 22 / 266 | 9.98e-4 | **1** (window 1 [24, 60), incumbent, gap 1.08e-3) | 1 | 4.38 / 5.31 |
| NEISO 2023 | 262.7 | 149.2 | 5,073.3 (13.76 / 44.47) | 113.5 | 5,414.6 | **20.6** | 792 (22 / 70) | 8 / 181 | 9.97e-4 | 0 | 0 | 4.30 / 7.21 |
| NEISO 2024 | 196.2 | 96.9 | 3,608.9 (9.80 / 50.27) | 99.3 | 3,870.2 | **19.7** | 756 (21 / 71) | 1 / 457 | 9.92e-4 | 0 | 0 | 4.31 / 5.21 |
| NEISO 2025 | 284.7 | 147.8 | 4,045.5 (10.96 / 55.47) | 136.9 | 4,409.8 | **15.5** | 684 (19 / 68) | 1 / 249 | 9.93e-4 | 0 | 0 | 4.25 / 5.12 |

- **Where the time goes.** The post-root branch-and-bound tail is 88–96 % of the stage (2022: tail 6,234 s of 6,516; presolve plus setup about 300 s; root LP 68 s). Half the integers per window does not halve the wall: the remaining CC clusters still branch.
- **Wall clock and budget.** Whole-shard wall was 32–115 min. The 228-min budget (Addendum E) was never approached; 2022 at 115 min would also have fit the original 162.
- **The baseline itself moved.** P0 + P1 here is 192–313 s against uc-1.1's 154–187 s in the same container class, so the ratios carry that noise.
- **D-2 ("Keep 3×; fund speedup") is reported, not judged.** Every year is 9.9–22.2× its P0 + P1.

## 1. The pre-fixed readings, answered (PRECOMMIT §§2–5; all seven years)

Order in every cell: 2019 · 2020 · 2021 · 2022 · 2023 · 2024 · 2025.

| # | reading | control | arm | bar | met? |
|---|---|---|---|---|---|
| T1 | M3 lower-tercile mean error $/MWh | +10.56 · +6.75 · +11.15 · +25.92 · +9.95 · +10.21 · +15.90 | +10.83 · +6.86 · +11.38 · +27.41 · +10.28 · +10.58 · +16.68 | toward 0 | **no, every year moves away** (+$0.1 … +$1.5); uc-1.1 moved toward 0 |
| T2 | ratio model/actual of hours ≤ $15 | 0.350 · 0.020 · 0.006 · 0.000 · 0.427 · 0.000 · 0.000 | 0.355 · 0.022 · 0.006 · 0.000 · 0.455 · 0.000 · 0.000 | rises | rises in 3 of 7 (2019, 2020, 2023), flat in 4 |
| T3 | ratio model/actual of hours < $0 | 0 · 0 · 0.033 · 0 · 0 · 0 · 0 | 0 · 0 · 0.033 · 0 · 0 · 0 · 0 | rises | no move |
| T4 | M4 reserve dormancy | n/a (no NEISO AS reference on disk); model share of hours with reserve MCP < $1 = 1.00 | 1.00 every year; mean MCP $0 | falls | **no move** |
| control | no PASS → FAIL flip on any gated criterion | — | **none** (artefacts aside) | none | met |
| control | \|ΔC3a 2023\| ≤ 1 pp | −3.04 % | −2.02 % (**1.016 pp**, toward the actual) | ≤ 1 pp | **not met by 0.016 pp** |
| control | P1 Optimal; unserved ≤ +500 MWh; no new D-4 FAIL row | — | 7 / 7 Optimal; 0.0 MWh; D-4 set identical | — | met |
| §7 | C3a away from 0 by > 1 pp | — | 2022 +1.58, 2024 +1.82, 2025 +2.32 pp | none | **fires (R)** |
| §7 | C3b worse by > 0.02 | — | 2025 +0.022; others +0.003 … +0.013 | none | **fires (R)** |
| S1 | MECH 28 share of class energy | 0 | CC_REGULAR 1.2 · 0.6 · 0.6 · 0.5 · 0.7 · 0.7 · 0.1 % (0.50 · 0.29 · 0.32 · 0.27 · 0.34 · 0.39 · 0.06 TWh); ST_GAS ≤ 0.3 % (2021, 2023 only); coal 0 | reported (R4) | — |
| S2 | CC_REGULAR starts per plant-year vs CEMS (M1) | 2,877 · 2,600 · 2,469 · 2,852 · 2,822 · 2,826 · 2,501, against CEMS 2,743 · 2,190 · 2,474 · 2,682 · 2,267 · 2,051 · 2,195 (1.00–1.38×) | 2,754 · 2,985 · 2,567 · 3,006 · 2,809 · 2,720 · 2,532 (1.00–1.36×) | closer to 1 in ≥ 4 of 7 | **no: closer in 3** (2019 1.049 → 1.004; 2023 1.245 → 1.239; 2024 1.378 → 1.326) |
| S2 | ST_GAS starts vs CEMS | 709 · 301 · 764 · 156 · 440 · 284 · 149, against CEMS 73 · 80 · 150 · 38 · 52 · 66 · 20 | 821 · 347 · 619 · 199 · 534 · 362 · 187 | toward CEMS | **no: higher in 6 of 7**. The ST_GAS clusters are almost all demoted to continuous, so the P1 LP cycles them as before, now around a different CC commitment |
| S3 | online capacity vs a measured series | none on disk | UC integer-cluster online mean 3.90 · 4.29 · 4.42 · 4.58 · 4.43 · 4.60 · 4.66 GW of 8.2–10.3 GW integer CC (model-internal) | — | skipped as declared |
| S4 | integer set, no-load source | UC-0 M6: 37 clusters | 18 · 19 · 22 · 19 · 22 · 21 · 19 integer clusters of 61–71; 648–792 integers per window; no-load from uc-params (#7229 crosswalk) | reported | — |
| S5 | M2(a) CEMS online at ≤ (mlf+0.10)·cap while model off, CC_REGULAR TWh | 1.30 · 1.25 · 1.04 · 0.89 · 0.69 · 2.10 · 1.59 | **3.80 · 3.97 · 3.53 · 3.10 · 4.22 · 4.30 · 3.74** | reported | the UC decommits CC in 2–3.5 TWh/yr more hours where the meter says online (as at uc-1.1) |
| W1 | wall rows | — | §0.2 | reported | — |
| W2 | time-limit hits | — | 0 · 0 · 0 · **1** · 0 · 0 · 0 | ≤ 3 / year | met |
| W3 | uplift share = Σ make-whole ÷ Σ λ·load | — | 1.31 · 1.36 · 1.26 · 1.44 · 1.46 · 1.23 · 0.98 % ($43.8 · 30.9 · 61.4 · 136.5 · 52.9 · 54.4 · 78.0 M; > 99.7 % on CC clusters) | ≤ 2 % | **met every year** (uc-1.1 breached at 3.6–6.2 %) |
| W4 | infeasible windows | — | 0 every year | 0 | **met (no kill #1)** |
| kill #2 | non-determinism | — | not exercised (one run per year; no relaunched leg) | — | — |
| kill #3 | control flip or \|ΔC3a 2023\| > 1 pp | — | no flip; 2023 1.016 pp | — | **fires by the letter** (0.016 pp, toward 0) |

## 2. What the UC did to the dispatch (zero LP, from the composed sidecars)

- **The integer set is half the size, set by the budgets, not by physics.** Ruling (a) demotes every cluster whose members are all budget-pinned. In NEISO these are clusters whose members all carry the keeper's budget rows (`neiso_oil_burn_budget`, `coal_fuel_inventory_plant_grain` and the like; the per-cluster attribution is in `uc_solve_log_<y>.json`, not re-derived here). Result: 11–13 of about 30 CC clusters (about 5 GW), all but 0–3 ST_GAS clusters, and all but 0–1 coal clusters become continuous. The UC therefore commits 8–10 GW of CC and almost nothing else. That is a property of how the keeper's budgets meet the engine, not a finding about NEISO commitment.
- **Body up, slightly, in six of seven years.** Demand-weighted mean prices, control → arm:

  | | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
  |---|---|---|---|---|---|---|---|
  | $/MWh | 34.82 → 34.97 | 24.83 → 24.66 | 49.13 → 49.38 | 93.40 → 94.84 | 36.94 → 37.33 | 41.87 → 42.63 | 72.90 → 74.53 |

  Every year except 2020 rises. The high-gas years move most: 2022 and 2025 rise $1.4–1.6. The C3a move is away from 0 in the five model-high years and in model-low 2020, and toward 0 only in model-low 2023. The scarcity tail is untouched: 0 h > $300 in both arms.
- **Energy barely moves.** CC_REGULAR shifts −0.49 … +0.21 TWh, CT_PEAKER −0.10 … +0.18 TWh, and oil +0.31 TWh (2025). C1 is untouched.
- **Cycling.** CC starts stay at the control's level (1.00–1.36× CEMS against 1.00–1.38×), and ST_GAS starts rise.
  - **CC.** The UC's integer clusters start 893–1,911 times a year in the schedule, and the continuous CC remainder still cycles in P1.
  - **ST_GAS.** The S2 bar is not met. uc-1.1's ST_GAS landing on CEMS came from integer ST_GAS clusters that uc-1.2 demotes.
- **Stacking with the kept floors.** `reliability_floor` forced CC energy is 0.20–0.69 TWh/yr in the arm, against the control's order. The UC adds 0.06–0.50 TWh of MECH 28. Neither approaches a budget.
- **Engine defect 6 is present here; the price readings are confounded.** UC-DESK r07 (main `d36e518c`, read after the legs landed) names defect 6 from ERCOT-R2: the MECH 28 cluster floor is split pro rata across a plant's offer tranches, so `_peak` tranches are forced on. The NEISO arm shows the same signature in the composed `class_band_hourly` sidecars (zero LP):

  | year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
  |---|---|---|---|---|---|---|---|
  | control: hours with CC_REGULAR `peak` band > 1 MW | 302 | 14 | 16 | 121 | 367 | 467 | 355 |
  | arm: same | 8,760 | 8,760 | 8,760 | 8,760 | 8,760 | 8,760 | 8,758 |
  | control → arm `peak` band TWh | 0.12 → 0.44 | 0.00 → 0.65 | 0.00 → 0.63 | 0.03 → 0.66 | 0.20 → 0.58 | 0.17 → 0.57 | 0.14 → 0.48 |
  | `committed` band, change in TWh | +7.2 | +7.4 | +7.4 | +7.2 | +6.5 | +4.7 | +5.4 |
  | the six `econ` bands, change in TWh | −7.5 | −7.8 | −8.0 | −8.1 | −7.0 | −5.3 | −6.0 |

  The arm's peak tranches run in every hour of the year, including the cheapest hours, which is out of merit by construction. Energy moves from the economic tranches into the committed and peak tranches at nearly constant class totals. That changes which tranche is marginal, and it plausibly drives the body-up price move and the T1 worsening. **The R stands by the §7 rule**, which was fixed ex ante and does not ask why. The desk's own reading applies here too: an R on the gates is not a structural rejection while defect 6 is unfixed. The lane does not try to separate the two effects (that needs an LP and a fixed engine).
- **Reserves untouched; uplift in proportion.** Reserve MCP stays < $1 in every hour, as in the control. Make-whole is 0.98–1.46 % of wholesale energy cost, the SPP range.

## 3. Verdict, the D-6 card, and what the record says about the mechanism

- **Verdict: `R`** (PRECOMMIT §7, fixed before any number). The engine defect is gone: no kill #1, W2/W3/W4 met, every leg Optimal. The R now rests on the control readings:
  - C3a moves away from 0 by > 1 pp in three years;
  - 2025 C3b worsens by 0.022;
  - |ΔC3a 2023| is 1.016 pp, over the 1-pp bar by 0.016 pp, on a move toward the actual.

  No gated criterion flips. The K-candidate structure bars are not met independently: S2 CC is closer in 3 of 7 years, T2 rises in 3 of 7, and T1 moves the wrong way in all seven. Absent the R triggers the reading would be **I**, but every price-side reading here is confounded by engine defect 6 (§2), so neither R nor I is a structural statement about MILP commitment in NEISO.
- **Matrix:** NEISO `unit_commitment_milp` stays **R**, with this RESULT as the citation. It replaces the uc-1.1 citation, whose R rested on an engine defect that is now fixed. The cell re-opens as `U` for one relaunch once UC-1-FIX-4 (defect 6) merges.
- **D-6 card (copy-paste):** *"UC-2 NEISO A/B at uc-1.2 (eab17188) — record R, on the control bar, not the engine. All seven years solve (2,554/2,555 windows Optimal, one time-limit hit with an incumbent, 0 infeasible; 2021/2023 now complete), wall 9.9–22.2× P0+P1, make-whole 1.0–1.5 % of energy cost. The calibrated control does not flip on any gated criterion, but the price body rises slightly: C3a moves away from 0 by 1.6 / 1.8 / 2.3 pp in 2022 / 2024 / 2025, 2025 C3b worsens 0.070→0.092, and the 1-pp bar year (2023) moves 1.016 pp (toward the actual). Ruling (a) demotes every all-budget-pinned cluster, so the UC commits only 8–10 GW of NEISO's ~15 GW CC fleet and ~no ST_GAS/coal; CC starts stay at the control's 1.0–1.4× CEMS, ST_GAS starts rise, lower-tercile error worsens $0.1–1.5. The arm carries engine defect 6 (the MECH 28 floor split pro rata onto offer tranches: CC_REGULAR `peak` tranches run 8,760 h/yr against 14–467 h in the control, 0.44–0.66 TWh), so the price readings are confounded and this R is not a structural rejection. Options: (1) record R at this pin, stage default-off for NEISO, and re-open as U for one relaunch after UC-1-FIX-4 lands [recommended]; (2) additionally re-test only if the engine gains a commitment treatment for budget-pinned clusters (the integer set here is decided by the keeper's budget rows, not by unit physics); (3) promote on structure (not recommended: no structure bar met, three wrong-way C3a moves above the bar)."*
- **Not a tuning invitation.** No `uc_*` value, floor, budget or limb was moved, and the misses are reported as misses (GATESPEC §7.1). The 2023 1.016 pp is reported at the fixed bar, not argued down.
- **For UC-DESK (read, not routed as a defect).** At NEISO, ruling (a) is the dominant effect: 33–40 → 18–22 integer clusters. It turns "does MILP commitment help NEISO" into "does commitment of the non-budget-pinned CC subset help". If the desk wants the first question answered, the budget-pinned clusters need a commitment treatment that respects their budget, which is an engine and spec question, not this lane's.

### 3.1 uc-1.1 → uc-1.2, side by side (the two records)

| | uc-1.1 (`2f872a62`) | uc-1.2 (`eab17188`) |
|---|---|---|
| years solved | 5 of 7 (2021, 2023 kill #1) | **7 of 7** |
| integer clusters / integers per window | 33–40 / 1,188–1,440 | 18–22 / 648–792 |
| ΔC3a, solved years | −1.4 … −6.5 pp (body down) | −0.7 … +2.3 pp (body up, except 2020) |
| worst C3b move | 2020 +0.026 | 2025 +0.022 |
| CC starts / CEMS | 0.64–0.76× | 1.00–1.36× |
| ST_GAS starts / CEMS | 0.5–2.2× | 4.1–11.2× |
| T1 lower-tercile error | toward 0 every year | away from 0 every year |
| uplift share | 3.6–6.2 % | 0.98–1.46 % |
| MECH 28 CC TWh | 0.94–2.48 | 0.06–0.50 |
| wall ratio | 10.4–31.0× | 9.9–22.2× |
| verdict | R (kill #1; 2020 C3b) | R (C3a wrong-way > 1 pp ×3; 2025 C3b; 2023 1.016 pp) |

## 4. Bundles, cost, what survives (rule 31: nothing deleted by the parent)

| artefact | where | promotable? |
|---|---|---|
| seven leg bundles (full, including `dispatch/<y>_P1.parquet`, 35–44 MB each; the shards' negation also carried `hourly/unit_hourly_<y>.parquet`) | shard branches `claude/ucmilp-neiso-uc12-2019` `fd59e29b` · `-2020` `a73150e8` · `-2021` `83c2bbb7` · `-2022` `c8788f1b` · `-2023` `a8202971` · `-2024` `b1c4c127` · `-2025` `a97db106`, all parented on the pin; checked out locally under `results/calibration/ucmilp_neiso_uc12_<y>/` | in form yes (rules 16, 34: a seven-year span); **no promotion proposed** (verdict R) |
| composed span `results/calibration/ucmilp_neiso_uc12_span`, slim copy | `docs/records/neiso/ucmilp/data/ucmilp_neiso_uc12_span/` (27 MB, this PR). It carries the `hourly/` sidecars including `uc_schedule_<y>`, `uc_uplift_<y>` and `unit_marginal_<y>`, plus `uc_solve_log_<y>.json`, the regenerated `legitimacy_diagnostics.json`, `metrics.json` and the configs. It has no dispatch, no `unit_hourly`, and no `network` / `reserve_family` | the record |
| uc-1.1 slim span | `docs/records/neiso/ucmilp/data/ucmilp_neiso_span/` (already on main) | history |
| uc-1.2 bench L1 + L2 | `claude/ucmilp-bench-neiso-2023-L1L2-uc12` `1c4a65f6` | bench, never registrable |
| dashboard | **nothing registered**. The local sidecar and payload used for scoring (`2026-10-10-ucmilp-neiso-uc-1`) were removed before the commit; `frontend/data/` is untouched | — |

- **Cost.** 8 shard containers: 1 bench and 7 legs at 32–115 min each. Zero LP in the parent.
- **Reproduction.** The span takes seven shards at the pin, 2 h wall in parallel.
- **Shard branches.** They are transport (rule 33). The owner may delete the eight `claude/ucmilp-*neiso*uc12*` branches once this PR merges; a session cannot (403).
- **Promotion question: none proposed; the lane recommends R.** The leg bundles will not survive this container; they survive on the shard branches.

## 5. Process record (rule 33: every shard archived; rule 31: nothing deleted by the parent)

| shard | session | outcome | branch / SHA |
|---|---|---|---|
| bench L1 + January L2, NEISO 2023, uc-1.2 | `session_016qxRqwbJ4DF5gRu1reYCMC` | PASS (Addendum D) | `claude/ucmilp-bench-neiso-2023-L1L2-uc12` `1c4a65f6` |
| 2019 | `session_019gc6z6ekJGYD95zYGcbJxv` | solved; 365/365 Optimal; pushed | `claude/ucmilp-neiso-uc12-2019` `fd59e29b` |
| 2020 | `session_013G9t3sYs2guNihU3NvwHpp` | solved; 365/365 Optimal; pushed | `claude/ucmilp-neiso-uc12-2020` `a73150e8` |
| 2021 | `session_01EUyTHJNK1CSr75bRKBQayZ` | solved; 365/365 Optimal; pushed | `claude/ucmilp-neiso-uc12-2021` `83c2bbb7` |
| 2022 | `session_01Grjpu7Sp4yrjvDJ5zFmPPt` | solved; 364/365 Optimal plus 1 time-limit hit with an incumbent; pushed. Its first watcher tracked the `setsid` launcher PID; the shard re-watched the solver PID, and nothing was killed or deleted | `claude/ucmilp-neiso-uc12-2022` `c8788f1b` |
| 2023 | `session_01MmTQNmFmtZ52Xp3zY8BJqM` | solved; 365/365 Optimal; pushed. Logged a skipped zonal-load file `NEISO_load_hourly_2023.csv` (reported, not investigated; no other leg reported it) | `claude/ucmilp-neiso-uc12-2023` `a8202971` |
| 2024 | `session_01KBgurzdL3myBzxjUnH3XsA` | solved; 365/365 Optimal; pushed | `claude/ucmilp-neiso-uc12-2024` `b1c4c127` |
| 2025 | `session_01SDURfvECyHPd11Zbs6pYB1` | solved; 365/365 Optimal; pushed | `claude/ucmilp-neiso-uc12-2025` `a97db106` |

- **Verification and archiving.** Every leg was fetched and checked before its shard was archived: parented on the pin, 21 files, and the five required files `dispatch/<y>_P1.parquet`, `uc_schedule`, `uc_uplift`, `unit_marginal` and `uc_solve_log`. All eight shards are archived.
- **Shard conduct.** Every shard ran `uv sync` once (no `.venv` in the container). None edited `src/`, `scripts/` or `frontend/data/`, and none opened a PR.
- **Naming deviation, declared.** Addendum C named the leg branches `claude/ucmilp-neiso-<y>-uc12` and the out-dirs `ucmilp_neiso_<y>`. The committed prompts (`bf80c04e`), which are what ran, use `claude/ucmilp-neiso-uc12-<y>` and `results/calibration/ucmilp_neiso_uc12_<y>`, so the uc-1.1 local bundles are not overwritten.
- **Composition.** As declared in PRECOMMIT §8(a)/(b): the scratch composer adds `gas_price_override` per year and the shared-input respan. Both composer gaps are still open at the pin. The span's `legitimacy_diagnostics.json` was regenerated over all seven years.

## Log entry

- 2026-10-10 · UC-2-NEISO `session_01D9RZoc9NrNhUBJLcYxyJx4` · `claude/ucmilp-2-neiso-ab-n7c2` · zero LP in the parent.
  - **Setup:** relaunch at `eab17188` (uc-1.2) on the owner's "Proceed", all seven years (Addendum C). uc-1.2 L1 gate PASS (Addendum D). Budget restored to 228 min (Addendum E).
  - **Solve:** seven shards, **all seven years solved**, 2,554/2,555 windows Optimal (one 2022 time-limit hit with an incumbent), 0 infeasible. Wall 9.9–22.2× P0+P1.
  - **Gates:** no gated flip. C3a 2019 +6.8→+7.3, 2020 −1.2→−1.9, 2021 +2.8→+3.4, 2022 +2.5→+4.0, 2023 −3.0→−2.0 (1.016 pp), 2024 +0.5→+2.3, 2025 +3.8→+6.1 %. 2025 C3b 0.070→0.092.
  - **Structure:** ruling (a) leaves 18–22 integer clusters (8–10 GW CC). Uplift 0.98–1.46 %. CC starts 1.00–1.36× CEMS (control 1.00–1.38×). ST_GAS starts up. T1 worse every year.
  - **Defect 6:** CC `peak` tranches forced on 8,760 h/yr (control 14–467 h); price readings confounded (desk r07).
  - **Verdict R:** C3a wrong-way > 1 pp ×3; 2025 C3b > 0.02; kill #3 by 0.016 pp. Cell `unit_commitment_milp` NEISO stays R, citation updated, re-open after UC-1-FIX-4.
  - **Housekeeping:** nothing registered, promoted or deleted; 8 shards archived.
