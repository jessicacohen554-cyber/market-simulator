# RESULT — UC-2-CAISO: MILP unit-commitment A/B on every CAISO backcast year — **R (control flips; the price body moves the wrong way), while the CC over-run and the CC cycling it was chartered against both clear their bars**

**Lane:** UC-2-CAISO · **Session:** `session_01T6HUKtuBPRdR9nXaHvALxT` (Fable) · **Date:** 2026-10-10 · **Branch:** `claude/ucmilp-2-caiso-ab-c3q9`.
**PRECOMMIT:** `PRECOMMIT-ucmilp-caiso-ab-2026-10-10.md` (pushed `1ad259fd` before any number; Addenda A–D before each step).
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`, 2026-10-10); owner direction *"launch shards for other ISOs to test"*.
**Pin solved:** `dc3860bef44f8ac0e322f92da94fd6c011bec381` (main at the merge of PR #7221). **LP in this session:** zero (seven year-isolated shards, rule 36, plus one bench shard for the L1 gate).
**Registered:** nothing (desk ruling 2026-10-10: audit E13 admits only keepers or folded runs). The scorer needs a registry sidecar and a run
payload, so the span was registered LOCALLY (`dashboard_add_run.py --no-prune`), scored, and the sidecar/payload removed before any commit —
no registration reaches `main`. Rubric 3.20 for both arms; the control is the keeper bundle re-scored at the pin (PRECOMMIT §3).

## 0. Headline

**The integer commitment stage does exactly what UC-0 said the RA must-offer bridge was doing wrong, and the gates say the bridge's
side effect was holding the price body up.** With the bridge replaced by the UC (no-load and start cost paid once, min-up/min-down by
measured physics), CAISO's combined cycles stop cycling: CC_REGULAR starts fall from 2.6–3.3× CEMS to **0.35–0.75× CEMS** in every year
(T3 met everywhere), the energy inside sub-min-up runs falls from 13–19 % of CC energy to **2–6 %** (T4), and CC_REGULAR energy falls
**7.7–10.3 TWh in every year**. That clears the three C1 over-run targets — **2019 +5.63 → −2.26 TWh, 2020 +13.46 → +4.48, 2021 +6.59 →
−2.51, all FAIL → PASS** (T1a–c met) — but the same shift puts the three model-low years through the band the other way (**C1 CC_REGULAR
2022/2023/2024/2025 PASS → FAIL at −8.2/−8.9/−9.4/−10.6 TWh**), lands 2.2–3.7 TWh/yr on CT_PEAKER (**2021 PASS → FAIL, +5.31 TWh**) and 4.4–7.6
TWh/yr on imports. And the price body goes **up, not down**: the CC the UC decommits was the trough price-setter the bridge held online,
so the lower tercile is set by imports and CTs — **C3a 2021 +12.7 → +19.5 % (T2 wrong way), C3a 2022/2023/2024/2025 +8.6/+7.6/+6.6/+6.0 → +16.6/+16.0/
+14.8/+17.9 % PASS → FAIL, C3b 2021 0.148 → 0.215, 2022 0.121 → 0.213 and 2023 0.117 → 0.207 FAIL**, and the keeper's own C4-2025 tripwire trips (NRMSE
0.283 → 0.318). **Kill #3 (control flip) fired on real moves → verdict `R`** (PRECOMMIT §7). It is the mirror image of SPP: there the UC
lowered the body and stacked on kept coal floors; here the mechanism it replaces was itself the trough-depressing floor, and removing it
without anything else in its place raises the body. The reading the owner needs is structural, not a tuning invitation: the RA
must-offer bridge was doing two jobs in the keeper — holding CC online (wrong, UC-0 M1) and setting trough prices (apparently right
for the gates) — and the UC fixes the first by giving up the second.

### 0.1 GATESPEC §6.3 gate table — control (keeper `2026-10-02-closeout-caiso-w1-arm2`, re-scored at the pin) → arm, every registered year

| year | C1 (class rows) | C2 | C3a | C3b | C3c | C4 (gas r / NRMSE) | C8 (CC_REGULAR share) | D-2 MECH 28 share (CC_REGULAR) | wall ratio total/(P0+P1) | reading met? |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | **CC +5.63 → −2.26 TWh FAIL → PASS**; CT_PEAKER +0.38 → +3.55 PASS (band ±4.84) | PASS → PASS | no reference (R-40) | no reference | SKIPPED | 0.888/0.385 → 0.891/0.343 FAIL → FAIL | 8.6 → 1.3 % PASS | 1.3 % | 3.01 | **T1a met**; T3 met (1,069 vs bar 5,075) |
| 2020 | **CC +13.46 → +4.48 TWh FAIL → PASS** (share +5.4 → +1.1 pp); CT_PEAKER −0.04 → +3.57 PASS (±4.60) | PASS → PASS | no reference | no reference | SKIPPED | 0.893/0.399 → 0.887/0.347 FAIL → FAIL | 6.2 → 1.3 % PASS | 1.3 % | 2.03 | **T1b met**; T3 met (1,101 vs 5,619) |
| 2021 | **CC +6.59 → −2.51 TWh FAIL → PASS**; **CT_PEAKER +2.52 → +5.31 PASS → FAIL** (±4.83, share +3.1 pp) | PASS → PASS | **+12.7 → +19.5 %** (in-window; CAVEAT → FAIL*) | 0.148 → **0.215** (CAVEAT → FAIL*, over the 0.20 band) | 0 h vs 27 h, unchanged (CAVEAT → FAIL*, artefact) | 0.857/0.348 → 0.853/0.320 FAIL → FAIL | 6.8 → 1.4 % PASS | 1.4 % | 1.86 | **T1c met; T2 WRONG WAY**; T3 met (1,984 vs 5,995); control: **flip** (C1 CT_PEAKER) |
| 2022 | **CC +0.95 → −8.16 TWh PASS → FAIL** (±5.01, share −4.3 pp); CT_PEAKER −0.63 → +1.47 PASS | PASS → PASS | **+8.6 → +16.6 % PASS → FAIL** | **0.121 → 0.213 PASS → FAIL** | 515 h → 546 h vs 510 h PASS → PASS (1.07×) | 0.909/0.249 → 0.921/0.264 PASS → PASS | 7.1 → 0.9 % PASS | 0.9 % | 4.06 | T3 met (2,602 vs 6,748); control: **3 flips** |
| 2023 | **CC −1.07 → −8.94 TWh PASS → FAIL** (±5.27); CT_PEAKER −1.14 → +1.20 PASS | PASS → PASS | **+7.6 → +16.0 % PASS → FAIL** | **0.117 → 0.207 PASS → FAIL** | 51 h → 84 h vs 47 h PASS → PASS (1.79×) | 0.912/0.235 → 0.911/0.269 PASS → PASS | 7.6 → 1.6 % PASS | 1.6 % | 3.35 | control: **3 flips** |
| 2024 | **CC −1.67 → −9.35 TWh PASS → FAIL** (±5.29); CT_PEAKER −1.04 → +1.95 PASS | PASS → PASS | **+6.6 → +14.8 % PASS → FAIL** | 0.122 → 0.185 PASS | 0 h vs 35 h, unchanged (CAVEAT → FAIL*, artefact) | 0.923/0.240 → 0.933/0.262 PASS → PASS | 10.8 → 2.8 % PASS | 2.8 % | 2.26 | control: **2 flips** |
| 2025 | **CC −0.36 → −10.63 TWh PASS → FAIL** (±5.08); CT_PEAKER −1.74 → +0.41 PASS | PASS → PASS | **+6.0 → +17.9 % PASS → FAIL** | 0.089 → 0.194 PASS | 0 h vs 8 h PASS → PASS | **0.887/0.283 → 0.908/0.318 PASS → FAIL** (the R-14 tripwire) | 12.3 → 3.1 % PASS | 3.1 % | 1.91 | control: **3 flips** |

\* The probe carries no `calibration_attestation.json`, so C6 reads UNATTESTED and the keeper's ledgered/reference-coverage caveats are
unavailable to it (PRECOMMIT §3; SPP Addendum D.3): the 2021 C3a/C3b rows read FAIL where the keeper reads CAVEAT, the 2019/2020 price rows
are absent (the keeper reads "reference absent — accepted caveat"), and C3c 2021/2024 read FAIL at identical magnitudes. The magnitudes are
compared directly: C3a 2021 and C3b 2021 moved past their bands in the wrong direction on their own; C3c 2021/2024 did not move. Every
other flip above is real. Determination: NOT-YET → NOT-YET.

**Benchmark basis (PRECOMMIT §3).** Both arms scored on the committed CAISO bench parts (STALE at HEAD per `check_bench_freshness.py`). The
local registration regenerated the seven parts; re-scoring both arms on the regenerated parts changes no status in the table (control C1
CC_REGULAR 2025 reads +0.80 instead of −0.36 TWh; shares move ≤ 0.4 pp); the parts were restored byte-for-byte (`git checkout`) and the
regenerated versions are not committed — the STALE condition is routed to the CAISO lane / desk (§5).

### 0.2 GATESPEC §6.1 wall rows (every shard, standard solve container, `MARKET_SIM_HIGHS_THREADS=1`; baseline = the same shard's P0 + P1, PRECOMMIT §5 proxy)

| ISO-year | baseline P0+P1 s | P0 s | UC Σ s (365 windows; mean / p95 MILP s) | P1 s | total s | **ratio** total/(P0+P1) | integers/window (int. clusters / clusters) | nodes p50/p95 | gap p95 | time-limit hits | peak RSS GB (UC stage / cgroup) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CAISO 2019 | 1,057.6 | 514.4 | 2,029.4 (5.50 / 16.30) | 543.2 | 3,182.1 | **3.01** | 1,152 (32 / 110) | 1 / 52.8 | 9.3e-4 | 0 | 7.41 / 8.47 |
| CAISO 2020 | 1,476.8 | 734.6 | 1,414.5 (3.80 / 5.03) | 742.2 | 3,002.7 | **2.03** | 1,260 (35 / 114) | 1 / 1 | 9.4e-4 | 0 | 7.48 / 8.56 |
| CAISO 2021 | 1,765.2 | 749.0 | 1,415.5 (3.80 / 7.04) | 1,016.2 | 3,287.6 | **1.86** | 1,188 (33 / 112) | 1 / 6.6 | 9.3e-4 | 0 | 7.58 / 8.57 |
| CAISO 2022 (attempt 1, budget 54 min) | — | 799.6 | > 2,400 (stopped by the budget, no per-window log) | — | — | — | 1,224 (34 / 115) | — | — | — | 5.29 at the stop |
| CAISO 2022 (attempt 2, budget 120 min) | 1,208.9 | 580.6 | 3,622.0 (9.86 / 35.39) | 628.3 | 4,911.4 | **4.06** | 1,224 (34 / 115) | 1 / 86.8 | 9.8e-4 | 0 | 7.57 / 8.78 |
| CAISO 2023 | 863.4 | 388.1 | 1,943.1 (5.27 / 11.31) | 475.3 | 2,891.0 | **3.35** | 1,224 (34 / 115) | 1 / 32.8 | 9.6e-4 | 0 | 7.52 / 8.63 |
| CAISO 2024 | 1,038.2 | 516.5 | 1,214.7 (3.27 / 5.08) | 521.7 | 2,342.5 | **2.26** | 1,224 (34 / 115) | 1 / 9 | 9.1e-4 | 0 | 7.55 / 8.61 |
| CAISO 2025 | 1,234.1 | 517.0 | 1,043.9 (2.80 / 4.86) | 717.1 | 2,362.9 | **1.91** | 1,188 (33 / 114) | 1 / 10 | 9.8e-4 | 0 | 7.63 / 8.69 |

Every window Optimal in every leg (2,555 of 2,555); 0 time-limit hits (W2 met); 0 infeasible (W4 met); no pre-fixing. The L1 gate
(PRECOMMIT Addendum C): CAISO 2021 window 0 Optimal at the root in 4.1 s, January 31/31 at 3.5 s per window — January is the year's fast
season; 2019 and 2023 average 5.3–5.5 s with p95 11–16 s and p95 node counts of 33–53, and 2022 (the $6.45 gas year, 515 scarcity hours) averages 9.9 s with p95 35 s and a p95 node count of 87: its UC stage took 60 min (attempt 1 stopped at the 54-min budget with the stage unfinished; attempt 2's P0 took 580.6 s where attempt 1's took 799.6 s — cross-container noise of the order SPP saw).
**D-2 ceiling 3× is reported, not judged:** against it, 2019, 2022 and 2023 read above (3.01, 4.06, 3.35), the other years below
(1.9–2.3); the CAISO baseline year is itself 14–29 min, so the stage adds 17–34 min per year.

## 1. The pre-fixed readings, answered (PRECOMMIT §§2–5)

| # | reading | control | arm | bar | met? |
|---|---|---|---|---|---|
| T1a | C1 CC_REGULAR 2019 | +5.63 TWh FAIL | **−2.26 TWh PASS** | ≤ +5.24 | **yes** (through the band to the other side, inside it) |
| T1b | C1 CC_REGULAR 2020 | +13.46 TWh FAIL | **+4.48 TWh PASS** | ≤ +9.03 | **yes** |
| T1c | C1 CC_REGULAR 2021 | +6.59 TWh FAIL | **−2.51 TWh PASS** | ≤ +5.71 | **yes** |
| T2 | C3a 2021 (RT-covered window) | +12.7 % | **+19.5 %** | ≤ +11.35 % | **no — wrong way** (+6.8 pts) |
| T3 | CC_REGULAR starts vs CEMS (`screen_year` M1, both bundles) | 7,470 / 8,078 / 8,700 / 10,028 / 9,528 / 9,692 / 9,322 (2.6–3.3× CEMS) | **1,069 / 1,101 / 1,984 / 2,602 / 2,408 / 1,711 / 1,534 (0.35–0.75× CEMS)** | ≤ 5,075 / 5,619 / 5,995 / 6,748 / 6,375 / 6,295 / 6,071 | **yes, every year — and overshoots below CEMS** (SPP: 0.52–0.77×). The engine's own unit-level count Σ`v` (all integer classes) is 2,557 / 3,009 / 4,774 / 6,615 / 5,724 / 4,225 / 3,497 |
| T4 | CC energy in sub-min-up runs | 13.7 / 12.8 / 14.6 / 19.4 / 14.7 / 16.2 / 16.6 % | **1.8 / 3.8 / 5.3 / 4.6 / 5.8 / 2.9 / 1.8 %** | falls | **yes** |
| T5 | M4 reserve dormancy | model 1.00 vs actual 0.28–0.69 | **1.00** (unchanged; mean MCP $0) | falls | **no — no move** (as SPP: the online-capacity envelope prices no CAISO reserve) |
| M3 (reported) | low-price-hour ratios ≤ $15 / < $0; lower-tercile error | 2021 0.53 / 0.61, +$11.8; 2022 0.70 / 0.80, +$15.9; 2023 0.60 / 0.75, +$11.8; 2024 0.64 / 0.77, +$9.8; 2025 0.65 / 0.91, +$7.6 | 2021 **0.40 / 0.54, +$15.2**; 2022 0.60 / 0.65, +$21.4; 2023 0.49 / 0.63, +$15.7; 2024 0.52 / 0.68, +$13.7; 2025 0.50 / 0.79, +$12.7 | — | the body moves UP $3–7/MWh everywhere (system mean 2021 56.1 → 60.0, 2022 91.7 → 98.5, 2023 58.3 → 62.8, 2024 36.9 → 39.8, 2025 36.5 → 40.6; 2019 38.6 → 42.5, 2020 35.5 → 38.0 unscoreable) |
| control | no PASS → FAIL flip | — | **12 real flips**: C3a 2022/2023/2024/2025; C3b 2022/2023; C1 CC_REGULAR 2022/2023/2024/2025; C1 CT_PEAKER 2021; C4 2025 (+ the attestation artefacts: C3c 2021/2024, C3a/C3b 2021 CAVEAT → FAIL, C6) | none | **breached → kill #3** |
| control | every leg Optimal; unserved ≤ +500 MWh; no new D-4 FAIL row | — | P1 Optimal in every leg; unserved 0.0 MWh every year (dump 855 MWh in 2020 vs 2,392 control; 0 elsewhere); D-4 FAIL rows = the control's own `chp_steam` plants (10034, 10649, 10650, 50612, 54749, 54768), no new row; D-1 ST_GAS rows differ (control fails 2021/2024/2025, arm 2023/2024/2025) on a class at 0.0–0.8 % of load, not gated | — | met |
| S1 | MECH 28 share of class energy | 0; `ra_mustoffer_bridge` 6.2–12.3 % of CC | CC_REGULAR **1.3 / 1.3 / 1.4 / 0.9 / 1.6 / 2.8 / 3.1 %** (0.38–1.04 TWh); CT_PEAKER 0; ST_GAS ≤ 0.02 TWh; COAL_BIT ≤ 0.02 TWh | reported (R4) | C8 passes as scored and with MECH 28 removed |
| S2 | = T3 | | | | |
| S3 | online capacity vs a measured series | no CAISO comparator on disk (PRECOMMIT §4) | skipped; `online_mw` reported in the sidecars | — | — |
| S4 | integer set, fallback shares | UC-0 M6: 32 clusters, 17.2 GW; no-load fitted 68/66 | 32–35 integer clusters of 110–115 (298–319 fleet rows), 1,152–1,260 integers per 36-h window; no-load fit 66–68 units per year | reported | — |
| S5 | where the decommitted CC energy goes (arm − control, TWh) | — | imports **+4.4 / +5.5 / +5.9 / +6.7 / +5.1 / +4.4 / +7.6**; CT_PEAKER **+3.2 / +3.7 / +2.8 / +2.1 / +2.4 / +3.0 / +2.2**; CC_CHP +0.1–0.3; ST_GAS −0.1–−0.6; solar +0.1–0.2 (less dump); hydro/wind/nuclear 0 | — | the CAISO analogue of SPP's CC → coal: CC → imports + CTs |
| W1 | wall rows | — | §0.2 | reported | — |
| W2 | time-limit hits | — | 0 / 365 in every leg | ≤ 3 | met |
| W3 | uplift share = Σ make-whole ÷ Σ λ·load | — | **0.06 / 0.05 / 0.12 / 0.10 / 0.20 / 0.34 / 0.18 %** ($4–29 M/yr) | ≤ 2 % | met (an order of magnitude below SPP's 1–4 %) |
| W4 | infeasible windows | — | 0 | 0 | met |
| kill #1 | infeasible window | — | none | — | not fired |
| kill #2 | non-determinism | — | not exercised (2022's first attempt produced no schedule) | — | — |
| kill #3 | control flip | — | **fired** | — | **R** |

**C8 under owner ruling R4.** MECH 28 (`uc_schedule`) is budgeted by the scorer at this pin; at 1.3–3.1 % of CC energy it is far below the
30 % cap either way, and no other floor on a UC class is armed in CAISO, so the stacking channel SPP showed (a kept conduct floor binding
more under the UC) has no CAISO counterpart: `chp_steam` forced energy is unchanged (CHP classes are not UC classes), and the RA-bridge row
simply disappears (its 3.7–4.8 TWh/yr of forced CC energy was the keeper's largest merchant floor).

## 2. What the UC did to the dispatch (zero LP, from the composed sidecars)

- **CC stops cycling, then runs less.** Starts fall 4–7× (2019: 7,470 → 1,069), below CEMS in every year; sub-min-up energy falls from
  6–10 TWh to 1–3 TWh. With the bridge no longer floor-holding P0's short runs and no-load paid in the objective, the UC keeps a CC
  offline through the trough instead of cycling it, and the CC energy that goes is the trough energy: CC_REGULAR −7.7 to −10.3 TWh/yr.
- **Imports and CTs fill the trough.** Imports +4.4 to +7.6 TWh/yr (the priced DSW/hub ladder, PRECOMMIT §1's named channel), CT_PEAKER
  +2.1 to +3.7 TWh/yr (CTs cover the ramps a decommitted CC no longer covers). CT_PEAKER 2021 crosses its band (+5.31 TWh vs ±4.83).
- **The price body rises.** The bridge-held CC was offering at its committed band in the trough; its replacement (import ladder steps,
  CT offers) is dearer, so the lower tercile rises $3–7/MWh and the ≤ $15 and negative-hour counts fall (2021: 134 → 102 and 25 → 22
  hours; 2022: 439 → 376 and 190 → 154). C3a moves from +6 to +13 % model-high to +15 to +20 %; C3b 2021/2022/2023 cross 0.20. Scarcity
  hours: 2022 515 → 546 h and 2023 51 → 84 h (both still in band), 2021/2024/2025 unchanged at 0.
- **Reserves untouched** (MCP < $1 every hour, as in the control). **Uplift negligible** (≤ 0.34 % of energy cost).
- **C4 hourly gas correlation:** NRMSE improves in the model-high years (2019 0.385 → 0.343, 2020 0.399 → 0.347, 2021 0.348 → 0.320,
  all still FAIL) and worsens in the model-low years (2022 0.249 → 0.264, 2023 0.235 → 0.269, 2024 0.240 → 0.262, **2025 0.283 → 0.318 FAIL**).

## 3. Verdict, the D-6 card, and what the record says about the mechanism

- **Verdict: `R`** (PRECOMMIT §7: kill #3 fired, and T2 moved the wrong way past its control). T1a–c, T3 and T4 met; T5 did not move.
- **Matrix:** CAISO `unit_commitment_milp` → **R**, evidence this RESULT (stamped by this lane as its last commit; integer state is the new
  evidence vs the keeper's bridge cells, rule 28). Per-ISO; other ISOs stay `U`.
- **D-6 card (copy-paste):** *"UC-2 CAISO A/B — record R. The MILP UC stage at dc3860be solves every CAISO year (2,555/2,555 windows Optimal,
  0 time-limit hits, 1.9–4.1× the P0+P1 wall; 2022 needed a 120-min budget). It fixes the CC cycling UC-0 named — starts 2.6–3.3× CEMS →
  0.35–0.75×, sub-min-up energy 13–19 % → 2–6 % — and clears all three C1 CC_REGULAR over-run targets (2019/2020/2021 FAIL → PASS). But
  CC energy falls 8–10 TWh in EVERY year, flipping C1 CC_REGULAR 2022/2023/2024/2025 and CT_PEAKER 2021 PASS → FAIL, and the price body rises
  $3–7/MWh: C3a 2021 +12.7 → +19.5 % (wrong way), C3a 2022/2023/2024/2025 and C3b 2022/2023 PASS → FAIL, C4 2025 trips its R-14 tripwire. The RA
  must-offer bridge was holding CC online in the trough and setting trough prices with it; the UC removes both. Options: (1) record R,
  stage stays default-off for CAISO [recommended]; (2) hold pending a D-5 re-ruling that keeps a priced trough mechanism beside the UC
  (not the bridge: rule 19) — the finding says the missing object is whatever sets CAISO's trough price when CC is offline, which the
  closeout record already names as the DSW/WEIM import print (DO-NOT-REDO without a measured intertie print); (3) promote on structure
  (not recommended: 12 real control flips)."*
- **Not a tuning invitation.** No `uc_*` value was moved; the 2022 relaunch changed only a wall budget (Addendum D).
- **For the CAISO lever queue:** the UC is the cleanest evidence yet that CAISO's C1 2019–2021 over-run IS the bridge (it clears with the
  bridge gone), and that the keeper's passing C3a 2022–2025 depends on the bridge's trough floor. Both readings are structural facts about
  the keeper, not numbers to reach.

## 4. Bundles, cost, what survives (rule 31: nothing deleted)

| artefact | where | promotable? |
|---|---|---|
| seven leg bundles (full, incl. `dispatch/<y>_P1.parquet`; 95–112 MB each, `unit_hourly_<y>.parquet` included by the prompt's `**` negation) | shard branches `claude/ucmilp-caiso-2019` `52c4f7d3` · `-2020` `5ba2c963` · `-2021` `21245317` · `-2022` `de4c8c2f` (attempt 2) · `-2023` `3f7ab193` · `-2024` `45c411aa` · `-2025` `a793a5ee` (all parented on `dc3860be`); checked out locally under `results/calibration/ucmilp_caiso_<y>/` | yes in form (rule 34); no promotion recommended |
| composed span `results/calibration/ucmilp_caiso_span` (gitignored locally; the slim copy below is the record) | this container only | — |
| **slim span** (hourly `class_band_hourly`, `class_hourly`, `system`, `storage`, `unit_marginal`, `uc_schedule`, `uc_uplift` per year; `uc_solve_log_<y>.json`; regenerated `legitimacy_diagnostics.json`; `metrics.json` from the local scoring; `run_config*.json`, `meta.json`; no `dispatch/`, no `unit_hourly`) | `docs/records/caiso/ucmilp/data/ucmilp_caiso_span/` on this branch | record, not a run |
| L1 gate bench | `claude/ucmilp-bench-caiso-2021-L1` `241f9679` (`l1.json`, `l2.json`, `l2_profile.md`) | — |
| registration | none on `main`; the local sidecar/payload were removed before commit; the six regenerated bench parts restored | — |

Cost: 1 bench shard crashed on the harness pickle defect (fixed by PR #7221), 1 bench shard passed, 7 span shards solved, 1 span shard
stopped at its budget and was relaunched — 10 containers, 25–100 min each; zero LP in the parent. **Promotion question: none is
proposed**; the lane recommends `R`. Shard branches are transport (rule 33): the owner may delete the eight `claude/ucmilp-*caiso*`
branches once this PR merges (a session cannot, 403).

## 5. Process record

1. L1 gate attempt 1 at `2f872a62`: `YearCapture.save` could not pickle the keeper's RA-bridge P1 hook closure (PRECOMMIT Addendum A) → PR #7221
   (UC-DESK, from the UC-2-ERCOT fixes) → re-pin `dc3860be` (Addendum B) → L1 gate PASSED (Addendum C).
2. Every shard container lacked `.venv`; `uv sync` as RUNBOOK §0 setup, desk-ruled fine.
3. 2022 stopped at the 54-min budget (P0 800 s + > 40 min UC); relaunched once at 120 min (Addendum D).
4. Scoring needs a registered run: local registration, scored, files removed before commit; the registration regenerated the STALE CAISO bench
   parts (`check_bench_freshness.py` 7/7 STALE at the pin) — both arms scored on the committed parts (primary) and on the regenerated parts
   (sensitivity: no status changes). **Routed to the CAISO lane / desk:** the committed CAISO parts do not reproduce under the builder at HEAD,
   and the keeper re-scored at the pin reads C1 CC_REGULAR +5.63/+13.46/+6.59 TWh where its registered record reads +10.19/+16.45/+8.11.
5. Composer gaps (SPP Addendum D) unchanged at the pin: `gas_price_override` per-year handled by a scratch copy; the respan step applied from
   the CAISO keeper composer only to feed the local registration — the seven-year rebuild reproduced the keeper's own frame hashes exactly
   (`eia930-d44f3b3a0aee`, `eia923-7b9c8f11474a`, `campd-9f21d7777a17`), so the arm is scored on the control's benchmark basis.
6. The shard prompt's `!results/calibration/<out>/**` negation commits `unit_hourly_<y>.parquet` (44–60 MB/yr) to the leg branches; rule 15
   keeps it off `main` — the slim span excludes it. Routed to the desk for `shard_prompt.py`.
7. Shards: 10 launched (2 bench, 7 span, 1 relaunch), 10 archived; none left alive. Local disk exhaustion at the slim copy (252 GB volume at 100 %): the six-leg PREVIEW composite (a derived scratch copy, never a solve) and the final composite's `dispatch/` copies (byte-duplicates of the leg bundles, which remain on their shard branches and locally) were deleted, named here per rule 31; no leg bundle was touched.

## Log entry

- 2026-10-10 · UC-2-CAISO `session_01T6HUKtuBPRdR9nXaHvALxT` (Fable) · `claude/ucmilp-2-caiso-ab-c3q9` · zero LP in the parent · PRECOMMIT `1ad259fd`
  before any shard; L1 gate at `2f872a62` stopped on the bench pickle defect (PR #7221) → pin `dc3860be`, L1 PASSED (window 0 + 31/31
  Optimal) · 7 legs solved (2022 on a 120-min relaunch), 2,555/2,555 windows Optimal, 0 TL hits · **verdict R**: C1 CC_REGULAR 2019/2020/2021
  FAIL → PASS (−2.26/+4.48/−2.51 TWh) and CC starts 2.6–3.3× → 0.35–0.75× CEMS, but C3a 2021 +12.7 → +19.5 % (wrong way), C3a 2022–25 and
  C3b 2022–23 PASS → FAIL, C1 CC 2022–25 and CT_PEAKER 2021 PASS → FAIL, C4 2025 0.283 → 0.318 (12 real flips); CC → imports + CTs 8–10 TWh/yr; uplift ≤ 0.34 %;
  wall 1.9–4.1× P0+P1 · not registered (E13); slim span under `docs/records/caiso/ucmilp/data/` · cell `unit_commitment_milp` CAISO → R ·
  D-6: record R, stage default-off for CAISO · no promotion proposed.
