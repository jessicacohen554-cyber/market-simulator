# RESULT — pjm-h20: Card C, the CC/CT pair, all six PJM years (2026-09-24)

Companion to `docs/PRECOMMIT-pjm-h20-card-c-cc-level-ct-max-2026-09-24.md` (pushed before any solve;
shards pinned to `9f8e95dfebb9c7c6d722f5c4a1ee5845ffe75c3e`). **Every number this lane cites is here.**

Arm = PJM keeper `2026-09-23-pjm-h19-dbs-span` recipe **+ `pjm_offer_midcurve_level_segments=["CC_LIKE"]`
+ `pjm_ct_measured_max_reprice=true`**, nothing else. Control = the committed keeper bundles (rule 29(b) form 4).
Registered, `--no-prune`: **`2026-09-24-pjm-h20-cardc-span`** (2023–25) + **`2026-09-24-pjm-h20-cardc-touchpoint`**
(2020–22, stamped to the arm span). **Promotion: NOT RECOMMENDED; owner ruling pending (§6).**

## 1. Verdict

**The price half of the prediction held. The volume half broke.** Pricing CC econ rungs at PJM's own
offer removes the CC-marginal overshoot and lifts every price statistic. But it makes CC too cheap
relative to the rest of the stack: CC over-dispatches by 19–43 TWh every year, CT collapses, and the
span drops **CALIBRATED → NOT-YET** on C1.

| determination | keeper | arm |
|---|---|---|
| span 2023–25 | CALIBRATED 8/8 | **NOT-YET** (C1 FAIL) |
| touchpoint 2020–22 | NOT-YET (C1, C3a, C3b) | NOT-YET (C1, C3b) — **C3a FAIL → PASS** |

## 2. Scored moves (arm vs keeper, same HEAD benchmark; bench parts byte-unchanged at registration)

| record | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| C3a mean LMP, keeper → arm (actual) | 24.28 → **22.07** (21.20) | 38.57 → 36.64 (38.53) | 66.36 → 66.91 (74.07) | 29.77 → 28.45 (29.58) | 30.41 → 30.10 (31.36) | 42.79 → 42.92 (45.89) |
| C3a status | **FAIL → PASS** | PASS | **FAIL → PASS** (−9.7 %) | PASS | PASS | PASS |
| C3b NRMSE | 0.155 → **0.059** | 0.104 → 0.113 | 0.242 → 0.248 (FAIL) | 0.113 → **0.072** | 0.124 → **0.094** | 0.143 → **0.105** |
| CC_REGULAR TWh (actual) | 285.6 → **325.9** (283.4) | 290.2 → **320.6** (289.4) | 319.2 → **338.5** (308.0) | 329.5 → **358.0** (325.7) | 336.3 → **362.3** (335.6) | 333.3 → **363.0** (330.7)¹ |
| CC_REGULAR C1 | PASS → **FAIL** | PASS → **FAIL** | FAIL → FAIL | PASS → **FAIL** | PASS → **FAIL** | SKIPPED¹ |
| CT_PEAKER TWh (actual) | 15.5 → 9.5 (18.7) | 12.8 → 9.1 (21.5) | 16.8 → 8.9 (19.7) | 20.4 → **8.5** (21.7) | 25.6 → **11.4** (24.2) | 30.2 → 12.7 (24.1)¹ |
| CT_PEAKER C1 | PASS → **FAIL** | FAIL → FAIL | PASS → **FAIL** | PASS → **FAIL** | PASS → **FAIL** | SKIPPED¹ |
| COAL_BIT TWh (actual) | 157.0 → **134.2** (131.5) | 175.8 → **159.0** (156.6) | 143.8 → 138.2 (141.1) | 104.1 → 99.2 (103.4) | 103.8 → 99.3 (105.4) | 133.4 → 126.8 |
| COAL_BIT C1 | **FAIL → PASS** | **FAIL → PASS** | PASS | PASS | PASS | SKIPPED¹ |
| CT_PEAKER D-2 forced share | 0.21 → **0.42** | 0.32 → **0.50** | 0.25 → **0.59** | 0.12 → **0.44** | 0.13 → **0.44** | 0.14 → **0.50** |

¹ 2025 C1 records read SKIPPED in both runs (benchmark coverage), so the 2025 volume move is unscored.

C8 reads PASS in both runs despite the CT forced share. C2, C3c, C4 and C6 are unchanged at PASS/CAVEAT.

**Error by actual-price region** (load-weighted $/MWh contribution to the annual mean, keeper → arm):

| year | bottom 50 % | p50–p95 | top 5 % |
|---|---|---|---|
| 2020 | +2.60 → **+1.35** | +1.90 → +0.98 | −1.47 → −1.51 |
| 2021 | +2.76 → **+1.49** | −0.09 → −0.80 | −2.67 → −2.61 |
| 2022 | +4.80 → **+3.26** | −2.46 → −1.52 | −10.35 → −9.21 |
| 2023 | +3.22 → **+2.11** | −0.81 → −1.19 | −2.35 → −2.19 |
| 2024 | +3.24 → **+2.27** | −1.30 → −1.04 | −3.08 → −2.68 |
| 2025 | +3.78 → **+2.49** | −2.08 → −1.29 | −5.01 → −4.38 |

## 3. Gates (PRECOMMIT §6)

| gate | result |
|---|---|
| **G1c self-check** | **PASS** in all six shards: the phase-0 census reproduced before each solve. |
| **G1a** CC-marginal price falls ≥ $1.50 | **PASS** in direction; the bottom-half term falls $1.0–1.5 every year. |
| **G1b** CT TWh never rises, falls 2022–25 | **PASS**, and far larger than intended: −24 % to −58 %. |
| **G2** bottom-50 % error falls ≥ $1.0 every year | **PASS** (−0.97 in 2024, at the bar). |
| **G2** C3a direction | Held as stated. 2020 improved into PASS; 2023/2024 moved negative (still PASS); 2025 held because the CT leg offset the CC leg. |
| **G2** C1 direction | Held in sign (CC up, COAL_BIT down, CT down); the **magnitude was not predicted** — CC +19 to +43 TWh. |
| **G3** no silent breakage | **FAILS**: C1 regresses in every scored year; the span determination falls. Reported at full magnitude. |

## 4. Where the extra CC energy comes from (P1 TWh, arm − keeper)

| year | CC_REGULAR | COAL_BIT | CT_PEAKER | net import | DA virtual INC |
|---|---|---|---|---|---|
| 2020 | +42.7 | −22.7 | −6.1 | −3.0 | −4.5 |
| 2021 | +30.4 | −16.9 | −3.7 | −2.1 | −1.7 |
| 2022 | +19.4 | −5.6 | −8.0 | −2.2 | −2.5 |
| 2023 | +28.5 | −4.9 | −11.9 | −4.4 | −4.3 |
| 2024 | +26.0 | −4.6 | −14.2 | −2.7 | −4.4 |
| 2025 | +29.7 | −6.5 | −17.4 | −2.1 | −4.6 |

In the coal-heavy years CC displaces coal, which is what fixes COAL_BIT 2020/21. In 2023–25 it mostly
displaces CT. In every year it also pushes PJM further into exports.

## 5. Reading, under rules 1 and 14

1. **The CC half's cause was real and is still real.** The fitted CC econ rungs sit above PJM's own
   published offers, and replacing them with the measured level fixes the price exactly where
   pjm-h18 located the error.
2. **Using the accurate input made the fit worse, so something else is miscalibrated (rule 14).** With
   CC offered at PJM's own level, the model's CC fleet dispatches 8–15 % more energy than PJM's CCs
   actually produced. The fitted `econ_high` 1.5× was hiding a CC **volume** defect by pricing CC out.
   That matches pjm-h2b (model CC online +7.7/+8.8/+5.8 pp too high in 2020–22). The candidates are
   CC availability, derates and commitment. None was measured here.
3. **The CT half over-expresses.** CT energy falls 24–58 %, and what remains is 42–59 % forced by
   floors (D-2). The floors are now doing the dispatch, which is the signature rule 18 targets. CT
   priced at PJM's measured offer still runs far less than PJM's CTs did, consistent with pjm-123's
   finding that the measured CT surface does not rank tight hours the way the market does.
4. **So this is a trade, not a structural gain.** Price structure improves; dispatch structure
   degrades on both CC and CT. It does not meet the bar the owner set ("structural integrity improves
   but gates regress").

## 6. Promotion — the question for the owner

**Recommendation: do NOT promote.** Keep `2026-09-23-pjm-h19-dbs-span` as keeper.

**FOR.** Zero free parameters; rule-14 measured inputs; touchpoint C3a FAIL → PASS; C3b better in
four of six years; the long-standing COAL_BIT 2020/21 C1 failures clear.

**AGAINST.** The span loses CALIBRATED. CC_REGULAR and CT_PEAKER both fail C1 in every scored year.
CT output becomes floor-driven (forced share ≈ 0.5). The CT switch is a registered backcast-only
overlay, never the forecast method.

**If NOT promoted** (recommended): `prune_iso_runs.py --iso PJM` removes the two h20 runs once the owner
rules. `audit_keepers --iso PJM` reads E13 on them until then.

**If promoted:** rule 35 order, as in pjm-h19 §8. The year union {2020…2025} is covered exactly by the pair.

## 7. Next card (routed, not launched)

**Locate the CC volume defect before any CC offer change.** Zero LP first: compare model CC
online-hours and capacity factor by plant against CAMPD/CEMS in 2020 and 2023, on the keeper and on
this arm's committed hourlies. Then attribute the 26–45 TWh to availability, derate, min-load or
commitment. Only then revisit the level form. Do not re-arm the CT max-seam until the CT surface's
tight-bin ranking (pjm-123) is resolved.

## 8. Retrievability (rule 34(e))

The two registered composites (slim keeper shape) and their payloads are **committed on this lane's
branch** and land on `main` with its PR. The six per-year legs (17 files each, `dispatch/<y>_P1.parquet`
included) are on this container only, gitignored. Any leg not on `main` costs a ~15–20 min re-solve.

Provenance SHAs (rule 33(d), not a recovery route): 2020 `30a0fcc5`, 2021 `196a2016`, 2022 `3ee80dfc`,
2023 `e7cdb7ef`, 2024 `34e34286`, 2025 `61c3c77f`. All six shards archived.
**Leftover refs the owner must delete (a session gets HTTP 403):** `claude/pjm-h20-cardc-2020` … `-2025`,
plus pjm-h19's `claude/pjm-h19-dbs-2020` … `-2025`.
