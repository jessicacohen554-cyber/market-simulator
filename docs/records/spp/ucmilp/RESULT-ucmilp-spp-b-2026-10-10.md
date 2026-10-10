# RESULT — UC-2-SPP-B: MILP unit-commitment A/B on every SPP backcast year with both conduct floors OFF — **R (targets moved the wrong way; control flips)**; the stacking hypotheses H3/H4 met, H1/H2 sign right but short

**Lane:** UC-2-SPP-B · **Session:** `session_01N2LCxAQwPFjvYwCdSH4uCx` (Fable) · **Dates:** 2026-10-09 → 2026-10-10 · **Branch:** `claude/ucmilp-2-spp-b-v3k`.
**PRECOMMIT:** `PRECOMMIT-ucmilp-spp-b-2026-10-09.md` (pushed before any shard; Addenda A–D before any number existed).
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`) on owner ruling D-6 SPP (2026-10-09): *"Record R + test floors-off arm (Recommended)"*; arm variant ruled D-5b (2026-10-10): *"Add a clean floor-off switch (Recommended)"* → field `coal_sync_floor_release` (PR #7219).
**Pin solved:** `9cb0eecb1fd97f52e3e1b75cb1380aeb7f6f52eb` (main at the merge of PR #7219; engine uc-1.1). **LP in this session:** zero (seven year-isolated shards, rule 36).
**Arm (V2):** keeper recipe + `unit_commitment_milp=true` + `st_gas_mustrun_per_plant=false` + `coal_sync_floor_release=true` + `uc_solver_preset="highs_default"` (declared ex ante, Addendum C). **Control:** keeper `2026-10-03-closeout-spp-nuc-keeper`. **Arm A:** `RESULT-ucmilp-spp-ab-2026-10-04.md` (PR #7207, floors kept, verdict R).
**Not registered** (desk ruling on arm A: audit E13 admits keepers and folded runs only). Slim span: `docs/records/spp/ucmilp/data/ucmilp_spp_b_span/`. Rubric 3.20 for all three columns.

## 0. Headline

**With the floors off, the UC alone under-commits SPP's steam gas and prices the body HIGH.** ST_GAS P1 energy falls to 4.1–9.8 TWh (control 4.5–13.8; actual
is 3–10 TWh above the control), CT_PEAKER rises 3.0–4.5 TWh/yr to fill the hours, and the mean P1 price lands $0.8–3.1/MWh above the control in every year.
The three target rows move the **wrong way, past the control**: 2020 C3a +27.7 → **+32.4 %** (arm A +19.0), 2019 C3a +12.3 → **+17.2 %** (A +10.3), 2020 C3b 0.345 →
**0.380** (A 0.273). The same upward shift repairs the two model-low years arm A broke — 2023 C3a −15.9 → **−0.2 %** PASS, 2024 C3a −22.6 → **−5.1 %** PASS and
C3b 0.344 → 0.197 PASS — and 2021 C3a flips PASS → FAIL (+7.1 → +14.5 %). C1 ST_GAS flips PASS → FAIL in five years (−8.4 to −10.5 TWh), CT_PEAKER in 2020 (+9.0),
CC_REGULAR 2024/2025 and COAL_PRB 2025 stay flipped from arm A. **Kill #3 (control flip) fired on real moves and every target row moved the wrong way → `R`**
(PRECOMMIT §7). The stacking hypotheses answer cleanly: **H3 met** (C8 ST_GAS forced share 1.6–7.1 %, every year PASS; with MECH 28 removed, 0.0 %), **H4 met**
(PRB starts rise toward CEMS in 7 of 7 years: 0.30–1.23× CEMS vs arm A's 0.23–0.41×), **H1 and H2 sign right but short of the half-way bar** (CC recovers
21–47 % of its arm-A loss; coal gives back 15–89 % of its arm-A gain). The two arms are two different failure modes of one mechanism: floors kept = coal over-held,
body low in 2023–25; floors off = ST_GAS under-committed, body high in 2019–21. Neither matches the keeper's floors, and no year-uniform form appears.

### 0.1 GATESPEC §6.3 gate table — control (keeper) · arm A (floors kept) · arm B (floors off), every registered year

| year | C1 class rows (control · A · B) | C2 | C3a (control · A · B) | C3b | C3c* | C4 | C8 ST_GAS forced share (control · A · B) | wall ratio A · B | reading met? |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | CC +2.25 · −6.05 · −4.29 PASS; PRB +0.24 · +6.74 · +5.53 PASS; **ST_GAS −4.96 · −5.06 · −8.43 PASS→PASS→FAIL**; CT +1.49 · +2.47 · +4.92 PASS | PASS ×3 | +12.3 · +10.3 · **+17.2 %** FAIL ×3 | 0.160 · 0.143 · 0.199 PASS ×3 | CAVEAT · FAIL · FAIL (0 h / 47 h, unchanged) | PASS ×3 | 18.1 · 27.7 · **1.6 %** PASS ×3 | 10.2 · **14.6** | **T2 wrong way** (past control); T4 sign right, small; control **flip** (C1 ST_GAS) |
| 2020 | CC +1.60 · −4.99 · −2.38 PASS; PRB −3.03 · +3.51 · +0.56 PASS; ST_GAS −3.42 · −3.81 · −7.32 PASS; **CT +6.15 · +6.10 · +9.03 PASS→PASS→FAIL** | PASS ×3 | +27.7 · +19.0 · **+32.4 %** FAIL ×3 | 0.345 · 0.273 · **0.380** FAIL ×3 | CAVEAT · FAIL · FAIL (0 h / 23 h) | PASS ×3 | 15.7 · 25.7 · **4.2 %** PASS ×3 | 6.9 · **14.7** | **T1, T3 wrong way**; control **flip** (C1 CT_PEAKER) |
| 2021 | CC −8.92 · −13.53 · −11.97 FAIL ×3; PRB +10.98 · +12.77 · +11.56 FAIL ×3; ST_GAS −2.83 · −2.01 · −5.32 PASS; CT +1.31 · +3.48 · +4.87 PASS | PASS ×3 | **+7.1 · +3.8 · +14.5 % PASS→PASS→FAIL** | 0.176 · 0.122 · 0.128 PASS ×3 | CAVEAT · FAIL · FAIL (372 · 387 · 398 h vs 140 h) | PASS ×3 | 28.8 · 36.8 F · **4.6 %** PASS | 8.6 · **12.3** | control **flip** (C3a); arm A's C8 flip cleared |
| 2022 | CC −9.16 · −13.13 · −11.27 FAIL ×3; PRB +10.75 · +12.16 · +10.42 FAIL ×3; **ST_GAS −5.18 · −3.69 · −8.49 PASS→PASS→FAIL**; CT −1.39 · +1.04 · +2.93 PASS | PASS ×3 | −4.8 · −9.4 · **+2.3 %** PASS ×3 | 0.175 · 0.186 · 0.130 PASS ×3 | CAVEAT · FAIL · FAIL (0 · 0 · 1 h vs 99 h) | gas FAIL ×3, coal PASS ×3 | 33.8 grounded · 39.2 F · **7.1 %** PASS | 8.7 · **10.1** | control **flip** (C1 ST_GAS); arm A's C8 flip cleared |
| 2023 | CC −4.49 · **−10.18 F** · −7.89 PASS; PRB +0.57 · +6.40 · +3.53 PASS; **ST_GAS −5.55 · −5.44 · −10.52 PASS→PASS→FAIL**; CT +2.83 · +3.73 · +7.03 PASS | PASS ×3 | −6.4 · **−15.9 F** · **−0.2 %** PASS | 0.176 · **0.233 F** · 0.151 PASS | FAIL ×3 (0 h / 42 h) | PASS ×3 | 23.1 · 33.6 F · **6.0 %** PASS | 5.1 · **15.8** | arm A's 4 flips cleared; control **flip** (C1 ST_GAS) |
| 2024 | CC −5.80 · **−11.83 F** · **−9.32 F**; PRB +0.82 · +7.52 · +3.50 PASS; **ST_GAS −6.31 · −5.82 · −10.32 PASS→PASS→FAIL**; CT +2.36 · +2.84 · +6.57 PASS | PASS ×3 | −11.2 F · −22.6 F · **−5.1 % PASS** | 0.216 F · 0.344 F · **0.197 PASS** | FAIL ×3 (0 h / 59 h) | PASS ×3 | 18.3 · 28.3 · **5.0 %** PASS ×3 | 8.0 · **17.5** | declared cost row turns into the 2 gains; control **2 flips** (C1 CC, ST_GAS) |
| 2025 | CC −7.86 · **−13.76 F** · **−11.33 F**; PRB +7.39 · **+10.21 F** · **+9.24 F**; **ST_GAS −6.91 · −4.20 · −10.09 PASS→PASS→FAIL**; CT −0.05 · +1.56 · +4.17 PASS | PASS ×3 | −4.3 · −10.0 · **+2.9 %** PASS ×3 | 0.153 · 0.174 · 0.153 PASS ×3 | FAIL ×3 (0 h / 68 h) | PASS ×3 | 17.7 · 31.4 F · **6.0 %** PASS | 7.9 · **13.4** | control **3 flips** (C1 CC, PRB, ST_GAS); arm A's C8 flip cleared |

\* C3c CAVEAT → FAIL in 2019–2022 is the attestation artefact of arm A's Addendum D (a probe carries no `calibration_attestation.json`, so the keeper's
rule-22 ledger route is unavailable); magnitudes are compared instead (identical in 2019/2020; 372 → 398 h in 2021; 0 → 1 h in 2022). Every other flip is real.
**Arm B vs keeper: 14 downgrades (10 real: C1 ST_GAS 2019/2022/2023/2024/2025, C1 CT_PEAKER 2020, C1 CC_REGULAR 2024/2025, C1 COAL_PRB 2025, C3a 2021; 4 C3c
artefacts), 2 upgrades (2024 C3a, 2024 C3b).** Arm A vs keeper was 14 downgrades (10 real), 0 upgrades. Determination: control NOT-YET (grade 3 of 8 scored),
arm A NOT-YET (1 of 7), arm B NOT-YET (2 of 7; 5 FAIL criteria plus the unattested C6). D-4: the control's seven FAIL rows (all `st_gas_mustrun_per_plant`
plants 1230/3008/6193) are absent in arm B as expected; no new D-4 FAIL row; floors codes 3 and 16 absent in every leg; every D-2 class row PASS.

### 0.2 GATESPEC §6.1 wall rows (every shard, standard solve container, `uc_solver_preset=highs_default`; baseline = the same shard's P0 + P1)

| ISO-year | baseline P0+P1 s | P0 s | UC Σ s (365 windows; mean / p95 MILP s) | P1 s | total s | **ratio** total/(P0+P1) | vs ruled D-2 ceiling 3× | integers/window | nodes p50/p95 | gap p95 | time-limit hits | peak RSS GB (UC / cgroup) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SPP 2019 | 176.4 | 85.2 | 2335.6 (6.34 / 14.62) | 91.2 | 2575.5 | **14.6** | 4.9× over | 3,384 (94 int. of 226) | 1 / 1 | 5.1e-4 | 0 | 4.10 / 6.96 |
| SPP 2020 | 193.0 | 89.3 | 2578.0 (7.00 / 15.59) | 103.7 | 2835.7 | **14.7** | 4.9× over | 3,312 (92 / 219) | 1 / 1 | 6.0e-4 | 0 | 5.08 / 6.92 |
| SPP 2021 | 222.1 | 109.9 | 2419.6 (6.54 / 16.73) | 112.2 | 2725.4 | **12.3** | 4.1× over | 3,168 (88 / 208) | 1 / 1 | 8.7e-4 | 0 | 5.07 / 6.97 |
| SPP 2022 | 183.8 | 84.1 | 1600.0 (4.32 / 11.34) | 99.7 | 1852.3 | **10.1** | 3.4× over | 3,096 (86 / 219) | 1 / 1 | 8.1e-4 | 0 | 4.11 / 6.90 |
| SPP 2023 | 188.4 | 87.1 | 2725.1 (7.40 / 16.18) | 101.3 | 2983.1 | **15.8** | 5.3× over | 3,096 (86 / 218) | 1 / 1 | 6.1e-4 | 0 | 4.05 / 7.38 |
| SPP 2024 | 181.3 | 85.9 | 2907.9 (7.90 / 18.48) | 95.4 | 3163.5 | **17.5** | 5.8× over | 2,988 (83 / 221) | 1 / 1 | 8.2e-4 | 0 | 4.09 / 6.95 |
| SPP 2025 | 255.0 | 128.0 | 3058.2 (8.28 / 19.48) | 127.0 | 3421.9 | **13.4** | 4.5× over | 2,952 (82 / 217) | 1 / 1 | 8.7e-4 | 0 | 4.11 / 6.90 |

Every window Optimal (2,555 of 2,555), every MILP at the root (nodes p50 = p95 = 1), 0 time-limit hits (W2 met), 0 infeasible (W4 met, kill #1 not fired),
no pre-fixing (fixed_on = fixed_off = 0), unserved 0.0 MWh in every year. **Every year is above the ruled D-2 ceiling of 3× (10.1–17.5×; a cost finding,
GATESPEC §7.3).** The ratios are 1.2–3.1× arm A's (5.1–10.2×) at the same integer set: this arm solved at `uc_solver_preset=highs_default` (the uc-1.1 path,
pinned so the engine lane's UC-SPEED "lean" preset could not enter the A/B, Addendum C) and without the floors the per-window MILP has more free integer
state (mean 4.3–8.3 s vs 2.6–4.9 s). Whole-shard wall (launch 00:52Z → push) 39–67 min; four of seven (2020, 2023, 2024, 2025) ran past the 59-min budget, each
with its artefact already written and pushed (PRECOMMIT §5 stops a shard approaching the budget *with no artifact*; none was PENDING > 45 min).

## 1. The pre-fixed readings, answered (PRECOMMIT §§2–5)

| # | reading | control | arm A | **arm B** | bar | met? |
|---|---|---|---|---|---|---|
| T1 | 2020 C3a (model 21.09 · 19.66 · **21.86** vs actual 17.54) | +27.7 % | +19.0 % | **+32.4 %** | ≤ +18.85 % | **no — wrong way, past the control** |
| T2 | 2019 C3a (23.41 · 23.00 · **24.43** vs 21.84) | +12.3 % | +10.3 % | **+17.2 %** | ≤ +11.15 % | **no — wrong way, past the control** |
| T3 | 2020 C3b NRMSE | 0.345 | 0.273 | **0.380** | ≤ 0.2725 | **no — wrong way, past the control** |
| T4 | low-price-hour ratios model/actual (≤ $15 · < $0) | 2019 0.025 · 0.040; 2020 0.150 · 0.111 | 2019 0.094 · 0.271; 2020 0.310 · 0.456 | 2019 **0.064 · 0.049**; 2020 **0.205 · 0.124** | both rise | **yes (sign)**, a third to a tenth of arm A's move; 2021–25 ≤ $15 0.34–0.56 (control 0.23–0.44, A 0.43–0.73), < $0 0.40–0.66 (control 0.44–0.73, A 0.91–1.29: B is *below* the control on negative hours in 2021–25) |
| T5 | M4 reserve dormancy (model share of hours with MCP < $1 vs actual) | 1.00 vs 0.09 / 0.08 | 1.00 | **1.00** (unchanged; model mean MCP $0) | falls | **no — no move** (as arm A) |
| cost | 2024 C3a / C3b (declared, sign unpredicted) | −11.2 % F / 0.216 F | −22.6 % / 0.344 | **−5.1 % PASS / 0.197 PASS** | reported | the declared cost row is the arm's one gain (2 upgrades) |
| cost | C1 coal rows 2021–25 (PRECOMMIT §4 "expected cost") | PRB +10.98 F / +10.75 F / +0.57 / +0.82 / +7.39 | +12.77 F / +12.16 F / +6.40 / +7.52 / +10.21 F | **+11.56 F / +10.42 F / +3.53 / +3.50 / +9.24 F** | low-side flip = kill #3 | no low-side flip: coal falls back toward the control, never below it; PRB 2025 stays FAIL on the high side (A's flip, 1.85 TWh over the band); LIG +0.6 … −2.3 TWh, PASS ×7 |
| control | no PASS → FAIL flip vs the keeper | — | 10 real + 4 artefacts | **10 real** (C1 ST_GAS ×5, CT_PEAKER 2020, CC 2024/2025, PRB 2025, C3a 2021) **+ 4 artefacts** (C3c 2019–22) | none | **breached → kill #3** |
| control | every leg Optimal; unserved ≤ +500 MWh; no new D-4 FAIL row | — | met | P1 Optimal ×7; unserved 0.0 MWh ×7; D-4 FAIL rows 0 (control 7, all the released `st_gas_mustrun_per_plant` plants) | — | met |
| S1 | MECH 28 share of class energy | 0 | CC 2.3–5.2 %, PRB 0.9–2.7 %, ST_GAS 1.7–2.5 % (12.0 % 2025) | **CC 1.5–4.7 %, PRB 1.7–3.5 %, LIG 0.2–3.2 %, ST_GAS 1.6–7.1 %** (0.13–0.79 TWh of UC floor on ST_GAS; 0.61–1.31 TWh on CC; 1.39–2.34 TWh on PRB) | reported (R4) | the only forcing left in the bundle besides nuclear / CHP / hydro min-flow |
| S2 | starts per plant-year vs CEMS (M1, model : CEMS) | CC 2,073–3,847 : 1,211–1,728 (1.6–2.3×); PRB 77–285 : 259–372 (0.30–0.95×); ST_GAS 440–868 : 796–1,351 (0.45–0.95×) | CC 0.52–0.77×; PRB 0.23–0.41×; ST_GAS 0.14–0.27× | **CC 670–1,331 (0.52–0.79×); PRB 78–336 (0.30–1.23×); LIG 8–20 (0.40–1.25×); ST_GAS 73–298 (0.09–0.33×)** | CC toward CEMS | CC unchanged from arm A (the floors never touched CC's starts); coal cycles like CEMS once the floor is gone (H4); ST_GAS cycles even less than arm A in 2019–21 because it is barely committed |
| S3 | online capacity vs SPP portal series | — | skipped (comparator not on disk) | skipped, same reason; `online_mw` is in `uc_schedule_<y>.parquet` | — | — |
| S4 | integer set, fallback shares | — | 82–94 of 208–226; no-load `uc-params` 122–123 | **identical: 94/92/88/86/86/83/82 integer clusters of 226/219/208/219/218/221/217; no-load `uc-params` 122–123, class fallback 86–103** | reported | the floors do not change the integer set |
| W1 | wall rows | — | 5.1–10.2× | **10.1–17.5×** (§0.2) | ruled ceiling 3× | **above the ceiling in every year** (cost finding) |
| W2 | time-limit hits | — | 0 | **0 / 365 ×7** | ≤ 3 | met |
| W3 | uplift share = Σ make-whole ÷ Σ λ_P1·load (same instrument on both arms; reproduces arm A's row) | — | 1.0 / 2.2 / 3.2 / 3.0 / 3.4 / 4.4 / 3.0 % ($64–347 M) | **0.15 / 0.42 / 0.35 / 0.33 / 0.45 / 0.46 / 0.40 %** ($10–43 M/yr) | ≤ 2 % | **met every year** — the make-whole in arm A was the floors' forced energy undercutting the UC's committed clusters; without floors the committed set recovers its cost in the LMP |
| W4 | infeasible windows | — | 0 | **0** | 0 | met |
| kill #1 | infeasible window | — | not fired | **not fired** | — | — |
| kill #2 | non-determinism | — | not exercised | **not exercised** (the seven interrupted first-launch shards pushed nothing; one completed run per year) | — | — |
| kill #3 | control flip | — | fired | **fired** | — | **R** |

## 2. The hypothesis readings H1–H4 (PRECOMMIT §4; one instrument per row over all three bundles, zero LP)

| # | reading | control | arm A | **arm B** | bar | met? |
|---|---|---|---|---|---|---|
| H1 | CC_REGULAR P1 TWh, 2019→2025 | 46.12 / 46.78 / 25.78 / 26.75 / 41.26 / 40.09 / 34.76 | 37.74 / 40.12 / 21.10 / 22.73 / 35.57 / 34.05 / 28.86 | **39.51 / 42.74 / 22.68 / 24.60 / 37.86 / 36.56 / 31.30** | B > A every year AND B − A ≥ ½(control − A) in ≥ 4 of 7 | **sign met (7 of 7 up); magnitude NOT met (0 of 7)** — B recovers 21 / 39 / 34 / 47 / 40 / 42 / 41 % of arm A's CC loss |
| H2 | COAL_PRB + COAL_LIGNITE P1 TWh | 87.84 / 71.71 / 100.54 / 101.55 / 73.70 / 67.23 / 88.15 | 95.56 / 79.58 / 103.46 / 103.64 / 80.17 / 74.38 / 91.46 | **94.40 / 76.69 / 102.10 / 101.79 / 77.20 / 69.95 / 90.09** | B < A every year AND A − B ≥ ½(A − control) in ≥ 4 of 7 | **sign met (7 of 7 down); magnitude NOT met (2 of 7: 2022, 2024)** — B gives back 15 / 37 / 47 / 89 / 46 / 62 / 41 % of arm A's coal gain. PRB alone: 82.48 / 66.69 / 91.91 / 88.56 / 68.93 / 63.53 / 83.62 (bar met in 2021/2022/2024, 3 of 7). LIG alone does **not** fall: 11.92 / 10.00 / 10.19 / 13.23 / 8.27 / 6.42 / 6.47 vs A 11.87 / 9.94 / 10.34 / 13.35 / 8.38 / 6.83 / 6.87 — the coal floor held PRB, not lignite |
| H3 | C8 ST_GAS forced share (scorer at the pin) / with MECH 28 removed | 0.181 / 0.157 / 0.288 / 0.338 F / 0.231 / 0.183 / 0.177 (same) | 0.277 / 0.257 / 0.368 F / 0.392 F / 0.336 F / 0.283 / 0.314 F (0.259 / 0.239 / 0.349 / 0.375 / 0.312 / 0.263 / 0.194) | **0.016 / 0.042 / 0.046 / 0.071 / 0.060 / 0.050 / 0.060 (0.0 ×7)** | B < A every year AND ≤ 0.30 every year | **MET** — arm A's four C8 FAILs and the control's 2022 conditional clear; the only ST_GAS forcing is the UC's own schedule (0.13–0.79 TWh) |
| H4 | PRB starts, model : CEMS (ratio) | 77:259 (0.30) / 134:341 (0.39) / 146:278 (0.53) / 161:274 (0.59) / 285:301 (0.95) / 211:372 (0.57) / 198:305 (0.65) | 60 (0.23) / 83 (0.24) / 94 (0.34) / 108 (0.39) / 124 (0.41) / 111 (0.30) / 88 (0.29) | **78 (0.30) / 121 (0.35) / 223 (0.80) / 336 (1.23) / 305 (1.01) / 277 (0.74) / 302 (0.99)** | ratio B > A in ≥ 5 of 7 | **MET (7 of 7)** — PRB cycles like its meter in 2021–25 once no floor holds it in; LIG 8 / 14 / 17 / 20 / 16 / 15 / 17 vs CEMS 15 / 35 / 33 / 20 / 19 / 12 / 23 (A: 8 / 11 / 11 / 7 / 1 / 2 / 2). Magnitude reported, not judged |

**Reading H1–H4 together.** The stacking arm A diagnosed was real: the kept floors, not the UC, were holding coal online (H4) and forcing ST_GAS (H3), and
removing them gives back part of the CC → coal swap (H1/H2 sign). But the UC alone keeps 53–79 % of that swap (CC still −4.3 to −12.0 TWh vs actual) **and
removes half to three-quarters of SPP's steam-gas energy** (ST_GAS 4.1–9.8 TWh vs control 4.5–13.8 and actual ≈ 7–20): with start and no-load cost paid in the UC objective
and SPP's low gas prices, the integer stage finds the steam units uneconomic and serves their hours with CTs (CT_PEAKER +3.0 … +4.5 TWh vs control; +9.0 TWh
vs actual in 2020). The ST_GAS energy SPP actually sees is self-committed (ASSESSMENT §6; the regulated owners' conduct the `st_gas_mustrun_per_plant` floor
stood in for); the UC's cost-minimising commitment does not reproduce it, and that is the mechanism behind every wrong-way target row.

## 3. What the UC without floors did to the dispatch (zero LP, from the composed sidecars)

- **Body up everywhere.** Mean P1 price vs control: +$1.0 / +0.8 / +2.8 / +3.1 / +1.6 / +1.6 / +2.1 per MWh (2019→2025); arm A was −$0.4 … −2.9. Lower-tercile
  error (M3) 12.8 / 13.5 / 13.9 / 9.2 / 9.4 / 10.4 / 12.5 $/MWh — back at the control's 9.7–14.8 (arm A had taken it to +0.5 … +10.6). Upper-tercile error
  improves by $2–7/MWh in every year (−9.5 … −24.3 vs control −7.4 … −31.4): the extra CT energy prices the peaks closer to actual. Scarcity hours unchanged
  (0 h in six years; 356 → 398 h in 2021; 1 h in 2022).
- **ST_GAS to CTs.** ST_GAS −3.5 / −4.0 / −2.8 / −3.2 / −5.0 / −4.0 / −3.2 TWh vs control; CT_PEAKER +3.5 / +3.0 / +3.8 / +4.5 / +4.3 / +4.2 / +4.4 TWh. CC +1.8–2.6 TWh
  vs arm A, still −2.2 … −6.6 vs control. PRB −0.3 … +5.3 TWh vs control, lignite ≈ arm A.
- **Cycling.** PRB starts 0.30–1.23× CEMS (control 0.30–0.95×, arm A 0.23–0.41×); CC 0.52–0.79× (unchanged from A); ST_GAS 0.09–0.33× (A 0.14–0.27×).
- **Reserves untouched.** Reserve MCP < $1 in every hour, as in both other bundles.
- **Uplift collapses** to 0.15–0.46 % of wholesale energy cost ($10–43 M/yr; arm A $64–347 M): the committed clusters recover their cost at the higher LMP.
- **Zero conduct forcing.** D-2 mechanisms binding: `uc_schedule` only (0.13–0.79 TWh ST_GAS, 0.61–1.31 CC, 1.39–2.34 PRB, 0.03–0.31 LIG); `coal_mustrun` and
  `st_gas_mustrun_per_plant` absent (control 3.4–7.2 and 2.0–3.0 TWh; arm A 7.5–12.7 and 2.9–4.3 TWh — the UC had *raised* the floors' forced energy).

## 4. Verdict, the D-6 card, and what the record says about the mechanism

- **Verdict: `R`** (PRECOMMIT §7: every target row moved the wrong way past its control — C3a 2019 and 2020 up, C3b 2020 up — and kill #3 fired on ten real
  flips). H3 and H4 met, H1/H2 sign right and short; T4 sign right and small; T5 unmoved. Mixed rule: the worst of the three target rows is "wrong way" in all three.
- **Matrix:** SPP `unit_commitment_milp` stays **R**, evidence now both arms (this RESULT appended to the cell); `coal_sync_floor_release` SPP cell:
  exercised once inside this A/B (its only designed use), the keeper byte-identical — stays `U` as minted (no adjudication of the field on its own; the field
  did what it was built to do: floors codes 3/16 absent, availability basis unchanged). Verdicts are per-ISO; other ISOs stay `U`.
- **D-6 card (copy-paste):** *"UC-2 SPP-B floors-off arm — record R. At 9cb0eecb (field PR #7219, uc_solver_preset=highs_default) the UC with both conduct floors
  off solves every SPP year (365/365 Optimal, 0 time-limit hits, 10–18× the P0+P1 wall vs the ruled 3× ceiling). The stacking was real: C8 ST_GAS forced share
  falls to 1.6–7.1 % (every year PASS, MECH 28 only), PRB starts return to 0.3–1.2× CEMS (7 of 7 up vs arm A), CC recovers 21–47 % and coal gives back 15–89 %
  of arm A's swap (signs right, half-way bars missed). But the UC alone under-commits steam gas (ST_GAS −8.4 … −10.5 TWh vs actual, CT_PEAKER +3–9) and prices
  the body HIGH: 2020 C3a +27.7 → +32.4 % (arm A +19.0), 2019 +12.3 → +17.2 % (A +10.3), 2020 C3b 0.345 → 0.380 (A 0.273); 2021 C3a flips to +14.5 %; C1 ST_GAS
  flips in five years. The same shift repairs arm A's 2023/2024 damage (2023 C3a −0.2 %, 2024 −5.1 % PASS, 2024 C3b PASS) and uplift falls to < 0.5 %. Two arms,
  two failure modes, no year-uniform form. Options: (1) record R for both arms, stage stays default-off for SPP, the keeper's floors stand [recommended];
  (2) hold for a UC-3 question on what holds SPP steam gas online (a measured self-commitment share as a UC-side must-run input, rule 13 admissibility to be
  argued) — not a tuning of uc_*; (3) promote on structure (not recommended: 10 real control flips, three wrong-way targets)."*
- **Not a tuning invitation.** No `uc_*` value was moved; `uc_solver_preset=highs_default` was declared before any number existed (Addendum C). The field
  `coal_sync_floor_release` is a switch, not a parameter.
- **For the frontier ledger (SPP-F2):** the reopen condition *"a commitment mechanism that lowers 2019/20 and also lifts 2023–25"* is now tested both with and
  without the conduct floors. With floors it lowers both; without floors it lifts both. The row's "why" stands, sharpened: the conduct floors and the
  integer commitment move the body in opposite directions and neither alone reproduces the 2019/20-vs-2023/25 split.

## 5. Bundles, cost, what survives (rule 31: nothing deleted)

| artefact | where | promotable? |
|---|---|---|
| seven leg bundles (full, incl. `dispatch/<y>_P1.parquet`, `floors/`, `unit_hourly`, 20 files each) | shard branches `claude/ucmilp-spp-b-2019` leg `5dc80330` (branch head `2aed628a` adds an unused `_shared` one-year-frames commit) · `-2020` `4060ef29` · `-2021` `448bb482` · `-2022` `be2b87ca` · `-2023` `6eb23e77` · `-2024` `e1bbb5c5` · `-2025` `f9e23ad8` (all parented on `9cb0eecb`); checked out locally under `results/calibration/ucmilp_spp_b_<y>/` (excluded via `.git/info/exclude`, never committed here) | yes in form (rule 34); **no promotion proposed** |
| composed span `results/calibration/ucmilp_spp_b_span` (slim: hourly sidecars incl. `uc_schedule_<y>`, `uc_uplift_<y>`, `unit_marginal_<y>`, `uc_solve_log_<y>.json`, regenerated `legitimacy_diagnostics.json`, `metrics.json`, `run_config*.json`, `meta.json`) | this PR, `docs/records/spp/ucmilp/data/ucmilp_spp_b_span/` (28 MB; no `dispatch/`, `floors/`, `unit_hourly`, `network`) | not registered (E13) |
| shared benchmark frames | the span's `meta.json` re-pointed to the keeper's own frames (`campd-8b15fb193a60`, `eia923-ada99c7451fd`, `eia930-c3bec7e7b952`, …, already on main) | — |
| scoring artefacts | local only: `frontend/data/backcast/registry/*ucmilp-spp-b*`, `runs/*ucmilp-spp-b*` written by `dashboard_add_run.py --no-prune` solely so `calibration_verdict.py --json` would score the bundle (it refuses an unregistered one); the same was done for arm A's registry file (removed from main by the desk); **none committed** | — |

Cost: 14 shard containers (7 interrupted at the HOLD with nothing pushed, 7 solved at `9cb0eecb`, 39–66 min each); zero LP in the parent. Cost to reproduce:
seven shards at `9cb0eecb`, ~40–65 min wall each. **Promotion question: none is proposed**; the lane recommends `R`. The leg bundles survive only on the
shard branches (transport, rule 33); the owner may delete the seven `claude/ucmilp-spp-b-<y>` branches and the field branch once this PR merges (a session
cannot, 403). All 14 shard sessions archived; none left alive.

## 6. Process record — see PRECOMMIT Addenda A–D

1. **The HOLD (Addendum B).** Seven shards launched 18:08Z at `6cf95135` with V1 (`coal_sync_srmc_tranche=false`); UC-DESK's HOLD (queued 18:01Z) arrived 18:14Z;
   all seven interrupted and archived by 18:17Z, nothing pushed. V1 was rejected zero-LP: the switch also re-prices the PRB `_sync` band (735–798 MW,
   $19–23 → $4.2–4.5/MWh, below the cheapest CC tranche in 82–87 % of hours) — a second logical delta.
2. **The field (Addendum C, PR #7219).** `coal_sync_floor_release` gates the MECH 3 floor in `arrays.py::_compose_min_gen_floors` so the `_sync` band's
   pricing and availability basis are untouched (a first cut at the assembly stamp moved coal availability by 214 MW-mean and was withdrawn). Toy and
   SPP-keeper full-data tests: only `min_gen` moves, on coal `_mustrun`/`_sync` rows, to zero. Pin = the merge SHA; `uc_solver_preset=highs_default` pinned
   so UC-SPEED's new default could not enter the A/B.
3. **Composition (as arm A's Addendum D, disclosed):** the scratch copy of `_ucmilp_compose_span.py` with `gas_price_override` in the per-year field set
   and the keeper composer's `_respan_shared_inputs` applied; `--restore-shared-inputs` found every shared input already resolving. The script on main was
   not edited (routed to the engine lane with arm A's finding).
4. **Shard caveats:** every leg confirmed the three UC files + `unit_marginal`, the four flag values and floors codes 3/16 = 0; the split-remap probe warning
   and the `uv sync` note appeared as in arm A; 2019's branch carries an extra `_shared` commit the composition did not use.
5. **Post-pin drift:** `main` moved 4 commits past the pin during composition (PR #7221, `claude/ucmilp-fix-window-slice`, UC engine); not on the solved
   bundles. This PR rebases onto it for the matrix stamp only.

## Log entry

- 2026-10-09/10 · UC-2-SPP-B `session_01N2LCxAQwPFjvYwCdSH4uCx` (Fable) · `claude/ucmilp-2-spp-b-v3k` · zero LP in the parent · PRECOMMIT before any shard;
  HOLD + V1 rejected zero-LP (`_sync` re-pricing) · owner D-5b → field `coal_sync_floor_release` (PR #7219) · pin `9cb0eecb`, `uc_solver_preset=highs_default`
  declared · 7/7 legs solved (2,555/2,555 windows Optimal, 0 time-limit hits, wall 10.1–17.5× P0+P1 vs ruled 3×) · **verdict R**: 2020 C3a +27.7 → +32.4 %,
  2019 +12.3 → +17.2 %, 2020 C3b 0.345 → 0.380 (all wrong way, past control); 2021 C3a → +14.5 % FAIL; C1 ST_GAS FAIL ×5 (−8.4 … −10.5 TWh), CT_PEAKER 2020,
  CC 2024/25, PRB 2025; gains 2024 C3a −5.1 % / C3b 0.197 PASS, 2023 C3a −0.2 % · H3 met (C8 ST_GAS 1.6–7.1 %), H4 met (PRB starts 0.3–1.2× CEMS, 7/7 up),
  H1/H2 sign right, half-way bars missed · uplift 0.15–0.46 % · reserve dormancy unmoved · not registered (E13) · slim span under
  `docs/records/spp/ucmilp/data/ucmilp_spp_b_span/` · cell `unit_commitment_milp` SPP stays R (evidence: both arms) · D-6: record R, stage default-off for SPP,
  keeper floors stand · no promotion proposed.
