# RESULT — UC-3-CAISO: the CAISO UC A/B at the clean engine (uc-1.4) — **R, and the UC-2 reading is confirmed: it was not a defect-6 artefact**

**Lane:** UC-3-CAISO (Opus) · **Date:** 2026-10-14 · **Branch:** `claude/ucmilp-3-caiso-ab`.
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`), owner ruling 2026-10-14 decision 7 (relaunch every UC-2 ISO at uc-1.4).
**PRECOMMIT:** `PRECOMMIT-ucmilp3-caiso-ab-2026-10-14.md` (pushed `87c23363` before any shard; readings, kills and verdict rule are the
UC-2 PRECOMMIT's §§2–7, unchanged). **Pin solved:** `87c233638eb0eb48af4f0ddd4b2b24b23a9da0fe` (= main `580c4fbf` + records; engine **uc-1.4**).
**LP in this session:** zero (seven year-isolated shards). **Registered:** nothing (E13). The scorer needs a sidecar + payload, so the span was
registered locally, scored, and both removed before commit; the seven regenerated bench parts were restored with `git checkout`.

## 0. Headline

The clean engine reproduces UC-2 almost exactly. **Forced peak-tranche energy is 0.00 TWh in every year** (uc-1.1: 0.52–0.76 TWh/yr), so
defect 6 is gone, and the verdict does not move: **the same 12 real control flips fire** (C1 CC_REGULAR 2022–25, C1 CT_PEAKER 2021,
C3a 2022–25, C3b 2022–23, C4 2025) → kill #3 → **R**. The engine delta uc-1.1 → uc-1.4 moves CC_REGULAR a further −0.14 to −0.65 TWh/yr and the
CAISO load-weighted price +$0.10–0.57/MWh, both small and both in the direction away from the control. As predicted ex ante (PRECOMMIT §4),
CAISO's UC-2 `R` was structural, not a defect-6 artefact.

What the UC does in CAISO, again: CC_REGULAR starts fall from 2.6–3.3× CEMS to **0.29–0.72×**, sub-min-up energy falls 13–19 % → 1.4–3.4 %, and
CC energy falls **8.1–10.4 TWh in every year**. That clears the three C1 over-runs (2019–21 FAIL → PASS) and breaks the four model-low years
(2022–25 PASS → FAIL). The replacement energy is imports (+4.6–7.6 TWh) and CTs (+2.3–3.9 TWh). The price body rises **$2.6–7.5/MWh in every
year and in every hour class**, not only the trough.

### 0.1 Gate table — control (keeper re-scored at the pin) → arm (uc-1.4)

| year | C1 CC_REGULAR (TWh) | C1 CT_PEAKER | C3a | C3b | C3c (>$200 h vs actual) | C4 gas r / NRMSE | C8 CC (scored → w/o MECH 28) | unserved | uplift % | CC starts model/CEMS | forced `_peak*` TWh | wall ÷ (P0+P1) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | +5.63 FAIL → **−2.91 PASS** | +0.38 → +3.82 PASS | no ref | no ref | skipped | .888/.385 → .892/.339 FAIL | 8.6 % → 1.9 % / 0.0 % | 0 | 0.05 | 7,470 → 1,055 / 2,679 (0.39×) | 0.00 | 2.41 |
| 2020 | +13.46 FAIL → **+3.95 PASS** | −0.04 → +3.80 PASS | no ref | no ref | skipped | .893/.399 → .884/.348 FAIL | 6.2 → 1.5 / 0.0 | 0 (dump 823 MWh) | 0.04 | 8,078 → 913 / 3,160 (0.29×) | 0.00 | 1.84 |
| 2021 | +6.59 FAIL → **−2.71 PASS** | +2.52 PASS → **+5.37 FAIL** | +12.7 % → **+19.8 %** (CAVEAT → FAIL\*) | 0.148 → **0.218** (CAVEAT → FAIL\*) | 0 vs 27, unchanged (artefact\*) | .857/.348 → .853/.319 FAIL | 6.8 → 1.6 / 0.0 | 0 | 0.11 | 8,700 → 1,854 / 3,289 (0.56×) | 0.00 | 1.80 |
| 2022 | +0.95 PASS → **−8.75 FAIL** | −0.63 → +1.72 PASS | +8.6 % PASS → **+17.3 % FAIL** | 0.121 PASS → **0.221 FAIL** | 515 → 548 vs 510 PASS | .909/.249 → .921/.266 PASS | 7.1 → 1.0 / 0.0 | 0 | 0.09 | 10,028 → 2,509 / 3,467 (0.72×) | 0.00 | 3.19 |
| 2023 | −1.07 PASS → **−9.27 FAIL** | −1.14 → +1.45 PASS | +7.6 % PASS → **+16.6 % FAIL** | 0.117 PASS → **0.216 FAIL** | 51 → 88 vs 47 PASS | .912/.235 → .910/.271 PASS | 7.6 → 1.7 / 0.0 | 0 | 0.16 | 9,528 → 2,306 / 3,222 (0.72×) | 0.00 | 3.10 |
| 2024 | −1.67 PASS → **−9.80 FAIL** | −1.04 → +2.20 PASS | +6.6 % PASS → **+15.4 % FAIL** | 0.122 → 0.189 PASS | 0 → 1 vs 35 (artefact\*) | .923/.240 → .932/.265 PASS | 10.8 → 2.6 / 0.0 | 0 | 0.26 | 9,692 → 1,662 / 2,898 (0.57×) | 0.00 | 1.99 |
| 2025 | −0.36 PASS → **−10.77 FAIL** | −1.74 → +0.52 PASS | +6.0 % PASS → **+18.2 % FAIL** | 0.089 → 0.197 PASS | 0 vs 8 PASS | .887/.283 PASS → **.907/.321 FAIL** | 12.3 → 3.2 / 0.0 | 0 | 0.15 | 9,322 → 1,526 / 2,820 (0.54×) | 0.00 | 2.03 |

\* The probe has no `calibration_attestation.json`, so C6 reads UNATTESTED and the keeper's ledgered caveats are unavailable (UC-2 PRECOMMIT §3).
Compared by magnitude: C3a/C3b 2021 moved past their bands the wrong way on their own; C3c 2021/2024 did not move materially. Determination
NOT-YET → NOT-YET. **Sensitivity:** re-scored on the bench parts the local registration regenerated, the flip set is the same 12.

### 0.2 Wall rows (GATESPEC §6.1; baseline = the same shard's P0 + P1, the UC-2 §5 proxy; `MARKET_SIM_HIGHS_THREADS=1`)

| year | P0 s | UC (markup) s | P1 s | total s | **ratio** | MILP mean / p95 s | nodes p50 / p95 | gap p95 | TL hits | int. clusters / clusters | RSS UC / cgroup GB |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 731.5 | 2,120.0 | 821.4 | 3,738.9 | **2.41** | 5.52 / 10.45 | 1 / 29 | 9.3e-4 | 0 | 32 / 110 | 7.41 / 8.35 |
| 2020 | 849.1 | 1,207.2 | 657.3 | 2,766.5 | **1.84** | 3.03 / 5.64 | 1 / 7.8 | 9.4e-4 | 0 | 35 / 114 | 7.50 / 8.37 |
| 2021 | 832.2 | 1,188.9 | 715.9 | 2,788.3 | **1.80** | 2.99 / 5.72 | 1 / 9.8 | 9.3e-4 | 0 | 33 / 112 | 7.60 / 8.39 |
| 2022 | 743.6 | 3,278.6 | 782.5 | 4,869.6 | **3.19** | 8.69 / 9.78 | 1 / 10.2 | 9.9e-4 | **2** (w359 gap 1.23e-3, w362 1.05e-3; 600 s each) | 34 / 115 | 7.58 / 8.74 |
| 2023 | 498.8 | 2,372.1 | 657.8 | 3,589.5 | **3.10** | 6.20 / 16.80 | 1 / 57.8 | 9.5e-4 | 0 | 34 / 115 | 7.52 / 8.51 |
| 2024 | 715.0 | 1,257.1 | 614.4 | 2,649.2 | **1.99** | 3.13 / 5.75 | 1 / 4.8 | 9.1e-4 | 0 | 34 / 115 | 7.55 / 8.49 |
| 2025 | 677.7 | 1,294.5 | 639.0 | 2,671.2 | **2.03** | 3.26 / 6.75 | 1 / 14.6 | 9.8e-4 | 0 | 33 / 114 | 7.64 / 8.57 |

2,553 of 2,555 windows Optimal, 2 time-limit (both 2022, gap ≤ 1.23e-3, incumbent kept); 0 infeasible. W2 (≤ 3 per year) met. Ratio 1.8–3.2×
(UC-2 at uc-1.1: 1.9–4.1×); 2022 and 2023 read above the 3× D-2 ceiling (reported, not judged). Integer set unchanged from UC-2 (ruling (a)
removes no CAISO cluster: none is all budget-pinned). Shards: 2020 relaunched once inside its container after its own 120-min background cap;
2022/2024 first launches exited 127 on a missing `/usr/bin/time` before any solve. None changed a setting.

## 1. Readings (UC-2 PRECOMMIT §§2–6, unchanged)

| # | reading | control | arm (uc-1.4) | bar | met? |
|---|---|---|---|---|---|
| T1a–c | C1 CC_REGULAR 2019 / 2020 / 2021 | +5.63 / +13.46 / +6.59 | −2.91 / +3.95 / −2.71 | ≤ +5.24 / +9.03 / +5.71 | **yes** |
| T2 | C3a 2021 | +12.7 % | +19.8 % | ≤ +11.35 % | **no — wrong way** |
| T3 | CC_REGULAR starts | 7,470–10,028 (2.6–3.3× CEMS) | 913–2,509 (0.29–0.72×) | ≤ midpoint every year | **yes** (overshoots below CEMS) |
| T4 | CC energy in sub-min-up runs | 12.8–19.4 % | 1.4–3.4 % | falls | yes |
| T5 | reserve dormancy (MCP < $1) | 1.00 | 1.00 (mean MCP $0) | falls | no move |
| kill #1 | infeasible window | — | none | — | not fired |
| kill #2 | non-determinism | — | not exercised | — | — |
| kill #3 | control flip | — | **12 real flips** | none | **fired** |
| control | unserved ≤ +500 MWh; P1 Optimal; no new D-4 row | — | 0 MWh every year; Optimal; D-4 rows = the keeper's own `chp_steam` plants | — | met |
| S1 | MECH 28 share of CC energy | 0 | 1.0–3.2 % (0.44–0.96 TWh); C8 w/o MECH 28 = 0.0 % | reported | — |
| S5 | where CC energy goes (arm − control, TWh) | — | imports +4.8 / +5.8 / +6.0 / +7.1 / +5.1 / +4.6 / +7.6; CT_PEAKER +3.5 / +3.9 / +2.9 / +2.4 / +2.6 / +3.2 / +2.3; CC_CHP +0.1–0.3; ST_GAS 0 to −0.6 | — | — |
| W3 | uplift ÷ Σλ·load | — | 0.04–0.26 % ($3–22 M/yr) | ≤ 2 % | met |

**Verdict: R** (kill #3, and T2 the wrong way). Mixed rows: T1a–c, T3, T4 met; T5 no move.

## 2. Price diagnosis (zero LP; `data/ucmilp3_readings/price_class_diag.{py,json}`)

CAISO load-weighted P1 price over the five CAISO zones, control → UC-2 (uc-1.1) → **UC-3 (uc-1.4)**, $/MWh:
2019 38.1 → 42.0 → 42.3 · 2020 34.3 → 36.8 → 36.9 · 2021 54.6 → 58.5 → 58.7 · 2022 88.0 → 95.0 → 95.5 · 2023 56.5 → 61.1 → 61.5 · 2024 35.3 → 38.2 → 38.4 · 2025 35.1 → 39.2 → 39.3.

- **Sign: up in every year and every hour class.** By control-price tercile the rise is low +2.7 to +6.3, mid +2.0 to +5.5, high +2.8 to +10.8
  $/MWh; by hour of day it is spread evenly (overnight +1.8 to +6.9, solar 10–16 h +3.0 to +8.4, evening 17–21 h +3.2 to +7.2). Hours ≤ $15 fall
  14–56 % (e.g. 2024 1,024 → 837; 2025 869 → 664); negative hours fall 12–57 %.
- **Who is marginal:** in the low tercile hydro rows carry the marginal flag in 95–99 % of hours in both arms; CC_REGULAR's share falls
  (e.g. 2023 4.2 → 2.0 %), CT_PEAKER's rises (0.4 → 1.0 %). CAISO's hydro is energy-budgeted, so its offer is the budget's shadow value: when CC
  energy is replaced by dearer imports and CTs, that water value rises and carries the increase into every hour. So the uniform lift is not
  "the trough lost its price-setter", as UC-2 read it. It is the system's marginal replacement cost rising, transmitted through hydro opportunity cost.
- **The structural question this leaves** is unchanged from UC-2. The keeper's passing C3a 2022–25 depends on the RA bridge holding ~4–5
  TWh/yr of CC online that physics (CEMS starts) says was not running in that pattern. Without it, the model's replacement supply is dearer
  than CAISO's real one. The bridge's side effect was therefore standing in for an object the model lacks, most plausibly the import /
  WEIM price print (already named in the CAISO closeout record; DO-NOT-REDO without a measured intertie print). That is a calibration-lane
  question, not a UC parameter. No tuning was done.

## 3. Verdict, D-6 card, matrix

- **Verdict R**, now on the clean engine. CAISO `unit_commitment_milp` cell → **R**, evidence this RESULT (it supersedes the UC-2 evidence the
  desk held).
- **D-6 card (copy-paste):** *"UC-3 CAISO A/B at uc-1.4 — record R. Defect 6 was small in CAISO (0.5–0.8 TWh/yr forced peak) and is now 0.00; the
  clean A/B reproduces UC-2's 12 control flips. The UC fixes CC cycling (starts 2.6–3.3× → 0.29–0.72× CEMS) and the 2019–21 CC over-run, but
  takes 8–10 TWh/yr of CC off in every year (2022–25 model-low years fail) and lifts the price $2.6–7.5/MWh in every hour class through
  dearer imports/CTs and hydro water value. Options: (1) record R, stage default-off for CAISO [recommended]; (2) hold pending a measured
  import-price object in a CAISO calibration lane, then re-run this A/B; (3) promote on structure (not recommended: 12 flips)."*

## 4. Bundles and cost (rule 31: nothing deleted)

| artefact | where |
|---|---|
| seven leg bundles (full, incl. `dispatch/<y>_P1.parquet`, 93–112 MB each; no file > 95 MB, nothing split) | `claude/ucmilp3-caiso-2019` `767adce6` · `-2020` `a292a3ad` · `-2021` `899971d2` · `-2022` `b45ce12c` · `-2023` `13e8a61c` · `-2024` `5e43faa0` · `-2025` `659d72a7` (all parented on `87c23363`) |
| slim span (hourly sidecars incl. `uc_schedule`, `uc_uplift`, `unit_marginal`; `uc_solve_log_<y>.json`; regenerated `legitimacy_diagnostics.json`; `metrics.json`; run configs; no `dispatch/`, no `unit_hourly`) | `docs/records/caiso/ucmilp/data/ucmilp3_caiso_span/` |
| readings (verdict JSONs control/arm/regenerated-bench sensitivity, M1/M3/M4 screen, fix4 readings, price diagnosis, wall rows) | `docs/records/caiso/ucmilp/data/ucmilp3_readings/` |

Cost: 7 shard containers, LP 43–81 min each, 0 relaunches by the parent. No promotion is proposed. The seven `claude/ucmilp3-caiso-*` branches
are transport only; the owner may cut them once this PR merges (a session cannot delete them; 403).

## Log entry

- 2026-10-14 · UC-3-CAISO (Opus) · `claude/ucmilp-3-caiso-ab` · PRECOMMIT `87c23363` before any shard · 7 legs at uc-1.4, 2,553/2,555 windows
  Optimal (2 TL, 2022), 0 infeasible, 0 unserved · forced peak 0.00 TWh (uc-1.1: 0.5–0.8) · **R**: the same 12 control flips as UC-2 (C1 CC 2022–25,
  CT 2021, C3a 2022–25, C3b 2022–23, C4 2025); T1a–c, T3, T4 met; C3a 2021 +12.7 → +19.8 % · price +$2.6–7.5/MWh in every hour class
  (imports/CTs + hydro water value) · wall 1.8–3.2× · not registered · cell `unit_commitment_milp` CAISO → R (clean engine).

---

## Addendum A — the relaunch at engine uc-1.5 (defect 7 fixed): **still R, but narrowed from 12 control flips to 4, all C3a**

**Pin:** `2dd69d5aa936547b402a1ba54d2eba57e759b7e7` (#7246, uc-1.5). Shards ran at `de1d9005`, which is the pin plus records only. The
PRECOMMIT Addendum A was pushed before any number: arm, readings, kills and verdict rule are unchanged. 2023 is the FIX-5 repro leg
`a2635bd6`, reused because G-DRIFT `f92d01ea → 2dd69d5a` touches no `src/`, `scripts/` or `configs/` and the recipe is identical. Branch
`claude/ucmilp-3-caiso-ab-uc15`. LP in the parent: zero. Nothing registered; the scoring sidecar and payload were removed and the bench
parts restored.

### A.1 Gate table: control → uc-1.4 → **uc-1.5**

| year | C1 CC_REGULAR (TWh) | C1 CT_PEAKER | C3a | C3b | C3c h (actual) | C4 gas NRMSE | C8 CC scored / w/o MECH 28 | CC starts ÷ CEMS | uplift % |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | +5.63 F → −2.91 P → **+2.11 P** | +0.38 → +3.82 → +1.64 P | no ref | no ref | — | .385 → .339 → .373 F | 8.6 → 1.9 → 3.7 % / 0.0 | 2.79 → 0.39 → **0.45** | 0.06 |
| 2020 | +13.46 F → +3.95 P → **+10.33 F** | −0.04 → +3.80 → +1.33 P | no ref | no ref | — | .399 → .348 → .386 F | 6.2 → 1.5 → 3.0 / 0.0 | 2.56 → 0.29 → **0.34** | 0.09 |
| 2021 | +6.59 F → −2.71 P → **+3.10 P** | +2.52 P → +5.37 F → **+3.44 P** | +12.7 % C → +19.8 % → **+15.7 %** (F\*) | 0.148 C → 0.218 → **0.178 P** | 0 vs 27 (artefact\*) | .348 → .319 → .335 F | 6.8 → 1.6 → 3.3 / 0.0 | 2.65 → 0.56 → **0.54** | 0.10 |
| 2022 | +0.95 P → −8.75 F → **−3.38 P** | −0.63 → +1.72 → +0.15 P | +8.6 % P → +17.3 % F → **+12.5 % F** | 0.121 P → 0.221 F → **0.162 P** | 515 → 548 → 521 (510) P | .249 → .266 → .249 P | 7.1 → 1.0 → 2.5 / 0.0 | 2.89 → 0.72 → **0.82** | 0.09 |
| 2023 | −1.07 P → −9.27 F → **−3.96 P** | −1.14 → +1.45 → −0.43 P | +7.6 % P → +16.6 % F → **+11.4 % F** | 0.117 P → 0.216 F → **0.158 P** | 51 → 88 → 73 (47) P | .235 → .271 → .248 P | 7.6 → 1.7 → 3.3 / 0.0 | 2.96 → 0.72 → **0.78** | 0.15 |
| 2024 | −1.67 P → −9.80 F → **−4.76 P** | −1.04 → +2.20 → −0.07 P | +6.6 % P → +15.4 % F → **+10.5 % F** | 0.122 → 0.189 → 0.152 P | 0 vs 35 (artefact\*) | .240 → .265 → .240 P | 10.8 → 2.6 → 4.9 / 0.0 | 3.34 → 0.57 → **0.64** | 0.21 |
| 2025 | −0.36 P → −10.77 F → **−4.43 P** | −1.74 → +0.52 → −1.20 P | +6.0 % P → +18.2 % F → **+11.5 % F** | 0.089 → 0.197 → 0.136 P | 0 vs 8 P | .283 P → .321 F → **.278 P** | 12.3 → 3.2 → 6.0 / 0.0 | 3.31 → 0.54 → **0.65** | 0.25 |

\* Attestation artefacts, as in §0.1 (C6 UNATTESTED). Unserved energy is 0 MWh in every year, forced `_peak*` energy is 0.00 TWh, and
C3c 2021/2024 are unchanged. **Sensitivity:** on the regenerated bench parts the same 4 flips fire.

**Readings (UC-2 PRECOMMIT §§2–7):**
- **T1a** met: 2019 +2.11 ≤ +5.24.
- **T1b** NOT met: 2020 moved the right way, +13.46 → +10.33, but only 3.13 TWh against the 4.43 bar. C1 stays FAIL.
- **T1c** met: 2021 +3.10 ≤ +5.71.
- **T2** wrong way: C3a 2021 +12.7 → +15.7 %.
- **T3** met in every year: 0.34–0.82× CEMS, all under the midpoints.
- **T4** falls: 1.2–3.0 % of CC energy is in sub-min-up runs, against 12.8–19.4 %.
- **T5** no move: model reserve dormancy stays 1.00.
- **Kill #3 fires on 4 real flips, C3a 2022 / 2023 / 2024 / 2025, at +12.5 / +11.4 / +10.5 / +11.5 % against the ±10 % band → verdict R.**
- What uc-1.5 removed from the uc-1.4 flip set:
  - C1 CC_REGULAR 2022–25 (now −3.4 to −4.8 TWh, inside the bands)
  - C1 CT_PEAKER 2021
  - C3b 2022–23
  - C4 2025

### A.2 What defect 7 was doing, and what is left (zero LP; `data/ucmilp15_readings/price_class_diag.{py,json}`)

**Class energy, uc-1.5 minus uc-1.4 (TWh):**
- CC_REGULAR: +5.0 / +6.4 / +5.8 / +5.4 / +5.3 / +5.0 / +6.3
- imports: −2.6 / −3.7 / −3.6 / −3.6 / −3.2 / −2.7 / −4.4
- CT_PEAKER: −1.6 to −2.5

The double-counted no-load had made committed CC look dearer than it is (CAISO 2023: $307 M, 12.4 % of CC energy cost; FINDING-ucmilp-fix5). Removing it brought back roughly 60 % of the CC
energy the uc-1.4 arm had lost. Against the control, CC is still −2.9 to −4.3 TWh/yr, imports +1.9 to +3.4, CT +0.5 to +1.4.

**Price (CAISO load-weighted, $/MWh), control → uc-1.4 → uc-1.5:**
- 2019: 38.1 → 42.3 → 40.8
- 2020: 34.3 → 36.9 → 35.5
- 2021: 54.6 → 58.7 → 56.7
- 2022: 88.0 → 95.5 → 91.4
- 2023: 56.5 → 61.5 → 58.7
- 2024: 35.3 → 38.4 → 36.7
- 2025: 35.1 → 39.3 → 37.0

So the residual lift over the control is **+$1.4–3.4/MWh, about half of uc-1.4's**.

**Shape of the residual lift:**
- It sits mostly in the **low tercile** (+1.6 to +4.0) and in **solar hours, 10–16 h** (+1.5 to +5.1).
- The high tercile is +0.6 to +4.0, and overnight is +0.5 to +2.3.
- Hours at or below $15 still fall: 2024 1,024 → 864; 2025 869 → 677.
- Hydro carries the marginal flag in 96–99 % of low-tercile hours in every arm. CC_REGULAR's share falls slightly, e.g. 2023 4.2 → 2.8 %.

**Reading:**
- The mechanism is the same as at uc-1.4, at about half the size. The UC still keeps ~3–4 TWh/yr of CC off that the keeper's RA bridge
  held on. The import ladder and CTs replace it at a higher price, and the energy-budgeted hydro's water value carries that into the
  low-price and solar hours.
- C3a's band is ±10 %. The keeper sat at +6.0 to +8.6 % in 2022–25, so a +3.9 to +5.5 pt lift is enough to cross it.
- The C1 and starts readings say the UC's commitment is now closer to physics than the keeper's. CC is −3 to −5 TWh in the model-low years
  against −0.4 to −1.7 in the keeper, but inside the band; starts are 0.34–0.82× CEMS against 2.6–3.3×. The price says the replacement supply
  is still dearer than CAISO's real one.
- That is the same object the uc-1.4 reading named: a measured import / WEIM price print. It is a calibration-lane question, not a `uc_*`
  value. Nothing was tuned.

### A.3 Wall (uc-1.5)

| year | P0 s | UC s | P1 s | total s | ratio total ÷ (P0+P1) | MILP mean / p95 s | nodes p95 | TL hits | int / clusters |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | 765.5 | 8,849.3 | 814.1 | 10,495.8 | **6.64** | 23.9 / 98.4 | 382 | **6** (w38, 43–45, 56–57; gap ≤ 3.18e-3) | 32 / 110 |
| 2020 | ≈1,010 (derived) | 1,727.7 (Σ UC) | 853.8 | 3,665.7 | ≈1.97 | 4.51 / 7.53 | 10.8 | 0 | 35 / 114 |
| 2021 | 927.1 | 1,500.1 | 1,029.2 | 3,533.5 | 1.81 | 3.77 / 8.12 | 11 | 0 | 33 / 112 |
| 2022 | 763.6 | 2,814.2 | 838.3 | 4,488.9 | 2.80 | 7.39 / 16.03 | 41.8 | 1 (w364, gap 1.27e-3) | 34 / 115 |
| 2023 (FIX-5 leg) | — | 1,878.6 (Σ UC) | — | — | — (not in that leg's record) | 4.95 / 9.37 | 24 | 0 | — |
| 2024 | 664.7 | 1,383.4 | 516.0 | 2,621.9 | 2.22 | 3.50 / 7.35 | 13.8 | 0 | 34 / 115 |
| 2025 | 820.2 | 1,317.5 | 641.8 | 2,850.6 | 1.95 | 3.30 / 6.99 | 11 | 0 | 33 / 114 |

- 2,548 of 2,555 windows were Optimal; 7 hit the time limit, every one with an incumbent at gap ≤ 3.18e-3; 0 were infeasible.
- W2 (≤ 3 time-limit hits per year) is **breached in 2019 (6)**. It is reported, not a kill (GATESPEC §5 kills only infeasibility).
- **Cost finding for the desk:** CAISO 2019 at uc-1.5 is 4.3× slower per window than at uc-1.4 (23.9 s vs 5.5 s). The slow windows
  cluster in mid-to-late February. One pass through them ran at 96.6 s per window (shard report, 14:46Z). The cheaper CC
  energy may make more commitment combinations near-tie for the MILP to separate (hypothesis, not tested here). Ratio 6.6× against the 3× D-2 ceiling.
- 2020's P0 is derived (total − UC − P1 − ~75 s I/O) because the shard was archived before it posted its phase line.

### A.4 Verdict and card

- **Verdict R on the clean engine (uc-1.5)**, by kill #3 on C3a 2022–25 only. T1a/T1c/T3/T4 met; T1b moved right but sub-bar; T2 wrong
  way. The cell stays **R**, with evidence re-pointed to this addendum.
- **D-6 card (copy-paste):** *"UC-3 CAISO at uc-1.5 — record R (narrow). Fixing defect 7 restores ~60 % of the CC energy uc-1.4 lost.
  Of the 12 control flips, 8 clear: C1 CC 2022–25, CT 2021, C3b 2022–23, C4 2025. C1 CC_REGULAR 2019/2021 go FAIL → PASS; CC starts fall
  2.6–3.3× → 0.34–0.82× CEMS. The 4 left are all C3a 2022–25 (+10.5 to +12.5 % vs the ±10 % band): the price body still sits
  $1.4–3.4/MWh above the keeper, because ~3–4 TWh/yr of CC is replaced by imports/CTs, carried through hydro water value. Options:
  (1) record R, stage default-off for CAISO [recommended]; (2) hold for a measured import-price object (CAISO calibration lane), then re-run;
  (3) promote on structure: closer to physics on commitment and C1, but 4 C3a flips and a 6.6× wall in 2019."*

### A.5 Bundles

- **Legs:**
  - `claude/ucmilp15-caiso-2019` `6bc13434`
  - `-2020` `8739f36c`
  - `-2021` `c7f819c4`
  - `-2022` `ea4e243e`
  - `-2024` `b0f55c2e`
  - `-2025` `9ea376e4`
  - 2023 is `claude/ucmilp-fix5-caiso-2023` `a2635bd6`
  - All are full bundles with `dispatch/`; no file is over 95 MB and none was split.
- **Slim span:** `docs/records/caiso/ucmilp/data/ucmilp15_caiso_span/`.
- **Readings:** `data/ucmilp15_readings/`.
- **Shards:** 6 launched, 6 archived. Nothing was deleted (rule 31); no promotion is proposed.

#### Log entry

- 2026-10-14 · UC-3-CAISO uc-1.5 relaunch · `claude/ucmilp-3-caiso-ab-uc15` · Addendum A `de1d9005` before any number · 6 legs + reused
  FIX-5 2023 · **R (narrow)**: 4 flips, all C3a 2022–25 (+10.5 to +12.5 %); C1 CC 2019/2021 FAIL → PASS, 2020 +13.46 → +10.33 (sub-bar);
  CC starts 0.34–0.82× CEMS; price +$1.4–3.4/MWh vs keeper (uc-1.4: +2.6–7.5) · wall 1.8–2.8×, 2019 6.6× (6 TL) · cell R.
