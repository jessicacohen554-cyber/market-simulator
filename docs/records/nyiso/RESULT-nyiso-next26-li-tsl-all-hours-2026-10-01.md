# RESULT — NYISO-NEXT-26: the Zone-K import security cap in every hour — gates pass, effect small outside 2021; owner card — 2026-10-01

- **Pre-registration:** `docs/records/nyiso/PRECOMMIT-nyiso-next26-li-tsl-all-hours-2026-10-01.md` (merged in #6988, pin `4213945e`).
- **Phase 0:** `docs/records/nyiso/FINDING-nyiso-next26-li-import-window-phase0-2026-10-01.md`.
- **Legs:** ten year-isolated shards (rule 36), all at `4213945ed8b3cfb7fd2256b08a3fca7de9518f3d`. All 170 leg files were hash-verified against their remote blobs before the shards were archived. Provenance SHAs are in `.gitignore`.
- **G-DRIFT:** `surface_rows("NYISO")` gives 228 rows, hash `50e8e6cf8632`, identical at the keeper (`fdc41f36`) and at the pin. Hunks were classified in PRECOMMIT §1.
- **Runs registered (probes, rule 15):**
  - Arm A: `2026-10-01-nyisonext26-tslall-span` / `-2021`, bundles `results/calibration/nyisonext26_span` / `_2021`.
  - Arm B: `2026-10-01-nyisonext26p-tslprint-span` / `-2021`, bundles `nyisonext26p_span` / `_2021`.

## 1. Gates (PRECOMMIT §3)

| gate | arm A (vs keeper NEXT-21) | arm B (vs NEXT-25 arm A) |
|---|---|---|
| G-1 leg acceptance | PASS, 5/5 | PASS, 5/5 |
| G-2 live (limit 940 every hour, flow ≤ 940; control hours > 940) | PASS; control hours 2,099 / 1,246 / 1,333 / 1,056 / 1,016 | PASS; 2,103 / 1,239 / 1,333 / 1,047 / 1,003 |
| G-3 demand / slack | PASS: 0.0 / 0.0 GWh, every year | PASS: 0.0 / 0.0 |
| G-4 C6 / C8 | PASS, every run | PASS |
| G-5 no new D-4 FAIL row ≥ 5 GWh | PASS; **no new D-4 FAIL row of any size** | PASS; none |
| G-6 LI fossil toward CAMPD and import toward measured | PASS, 5/5 | PASS, 5/5 |

Gates: `results/phase0/nyiso/_nyisonext26_gates_{A,B}.json`. Zone splits: `_nyisonext26_li_gap_{keeper,A,ctlB,B}.json`.

**G-6 magnitude (arm A, MW mean):**

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| LI fossil, control → arm | 874 → 920 | 892 → 907 | 635 → 653 | 892 → 896 | 1,017 → 1,029 |
| LI fossil, CAMPD gross | 1,256 | 1,110 | 1,029 | 1,069 | 1,200 |
| LI AC import, control → arm | 744 → 697 | 586 → 571 | 669 → 651 | 494 → 489 | 422 → 410 |
| LI AC import, measured implied | 439 | 436 | 340 | 384 | 302 |

The direction is right every year. The size is 5–46 MW against a 180–390 MW fossil gap: it closes 12 % of the gap in 2021 and 2–8 % in the other years.

## 2. Scores (rubric 3.13)

| C3a (system, vs RT) | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| keeper | +2.9 | −2.4 | +1.2 | −4.0 | **−11.6 FAIL** |
| **arm A** | +3.4 | −2.3 | +1.2 | −3.9 | **−11.6 FAIL** |
| NEXT-25 arm A (#6987) | +2.9 | −2.1 | +0.4 | −2.6 | −9.6 |
| **arm B** | +3.4 | −2.1 | +0.4 | −2.6 | −9.6 |

| C3b NRMSE | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| keeper | 0.108 | 0.155 | 0.122 | 0.113 | 0.181 |
| arm A | 0.114 | 0.155 | 0.122 | 0.113 | 0.181 |
| arm B | 0.118 | 0.146 | 0.130 | 0.126 | 0.161 |

| determination | span 2022–25 | 2021 | ISO |
|---|---|---|---|
| keeper | NOT-YET (C3a 2025; C3c not lone) | CALIBRATED | NOT-YET |
| **arm A** | NOT-YET (unchanged) | CALIBRATED | NOT-YET; **no year downgrades** |
| **arm B** | **CALIBRATED** (C3c lone, rule 22) | CALIBRATED | **CALIBRATED** |

C1, C2, C4, C6 and C8 PASS in every run. C3c hour counts are unchanged from each control.

**Zone K (Long Island) error vs DA, %, control → arm:**

| year | annual | winter | spring | summer | fall |
|---|---|---|---|---|---|
| A 2021 | −16.1 → **−10.7** | −13.5 → **+3.6** | −8.9 → −8.7 | −27.7 → −27.2 | −11.3 → −11.1 |
| A 2022 | −11.3 → −10.1 | −13.2 → −9.7 | −9.8 → −9.7 | −13.2 → −12.9 | −7.1 → −7.1 |
| A 2023 | −13.9 → −13.2 | −20.0 → −19.9 | −3.5 → −3.4 | −17.3 → −15.6 | −11.1 → −10.1 |
| A 2024 | −12.0 → −11.4 | −12.0 → −10.6 | +1.2 → +1.4 | −24.5 → −24.4 | −5.6 → −5.5 |
| A 2025 | −12.8 → −11.9 | −17.6 → −15.8 | −6.3 → −5.6 | −13.2 → −13.2 | −6.4 → −6.4 |
| B 2025 | −10.9 → −10.1 | −13.0 → −11.5 | −6.8 → −6.2 | −13.1 → −13.1 | −6.7 → −6.7 |

The modelled annual K-over-J spread (arm A) rises 2.2 → 5.2, 1.3 → 2.6, 0.9 → 1.2, 0.4 → 0.7 and 0.6 → 1.3 $/MWh (2021–2025). The DA spread is 11.5, 10.8, 6.8, 4.0 and 3.5. NYC (J) error moves ≤ 0.15 $/MWh.

## 3. Against the prediction (PRECOMMIT §5)

- **K moves toward zero every year: held in direction, short in size.**
  - The static bracket was −9.3, −8.9, −11.3, −9.4 and −11.0 %. The LP reaches −10.7, −10.1, −13.2, −11.4 and −11.9 %.
  - As a share of the bracket, that is 79 % in 2021, 50 % in 2022 and 2025, and 27 % and 23 % in 2023 and 2024.
  - The prediction ("half to all"; 2022–2025 1–3 pts) holds in 2021, 2022 and 2025. It misses in 2023 (+0.7 pt) and 2024 (+0.6 pt).
- **Winter carries it: held,** except 2023, where winter is flat (−20.0 → −19.9).
- **Summer moves < 1 pt: held,** except 2023 (+1.7 pt).
- **ISO C3a moves < 1 pt: held.** The largest move is 2021, +0.5 pt, away from zero.
- **LI fossil +0.5 TWh in 2021 and +0.2–0.3 TWh in other years: short.** It rose +0.41 TWh in 2021 and +0.13 / +0.15 / +0.04 / +0.10 TWh in 2022–2025.
- **C3c LI tail rises, possibly flipping one year: refuted.** C3c hour counts are unchanged.
- **Not closed, as stated:** the summer K gap (still −13 to −27 %) and the LI-internal pockets.

**Why the LP moves less than the static bracket (measured, not diagnosed further).**
- The cap is live in 1,016–2,099 control hours a year.
- The LP meets it by moving only 5–47 MW of mean import onto LI's own fleet.
- The modelled K-over-J spread stays at 0.7–5.2 $/MWh, against 3.5–11.5 DA. So in most capped hours, the LI units that replace imports are priced close to J.
- The measured DA congestion is larger than one net 940 MW link produces. That fits open item 2 (Y49/Y50 loading set by PAR schedules and cable outages at modest net import), but this run does not test it.
- Which LI units set K in the capped hours was not decomposed here. That is a NEXT-28 phase-0 item if the owner wants it.

## 4. Reading

**Arm A** is live, zero-DOF and moves in the pre-registered direction in every year. It passes G-1 to G-6 in all five years, and no year's determination downgrades. **It meets PRECOMMIT §4's promotion rule.**

The gain is structural (rules 17 and 14) and small outside 2021. The span stays NOT-YET on C3a 2025, which this lever was never expected to fix.

**Arm B** passes every gate against NEXT-25 arm A. Its system scores are equal to NEXT-25 arm A's to 0.1 pt in 2022–2025. It adds the Zone-K improvement on top: 2025 K −10.9 → −10.1 %, and 2022 winter −12.1 → −8.8 %.

**Not promoted in this session.** RUNBOOK §4 promotes on the owner's word. #6987, which decides whether print-level enters the keeper, is still held. Promoting A now would set a keeper that #6987 option 1 would immediately supersede, and B is the same lever on the #6987 recipe. One card covers both.

## 5. DECISION CARD (owner)

| | option | effect |
|---|---|---|
| **1 (recommended)** | **Promote arm B.** It subsumes #6987 option 1: print-level plus all-hours TSL. `promote_keeper.py --iso NYISO --bundle results/calibration/nyisonext26p_span --label "nyisonext26p tslprint span" --fold results/calibration/nyisonext26p_2021="nyisonext26p tslprint 2021"`. Cells `nyiso_gas_daily_print_level` and `nyiso_li_tsl_all_hours` O → K. Then prune the NEXT-25 runs (all four) and the NEXT-26 arm-A runs, own runs only. Close #6987 with its docs merged, and decline #6984 standalone. | ISO NOT-YET → **CALIBRATED** (2025 C3a −9.6 %, 0.4 pt margin; C3c lone, rule 22). |
| 2 | **Promote arm A only** (no print-level). The same command on `nyisonext26_span` / `_2021`. `nyiso_li_tsl_all_hours` O → K. Prune arm B. | ISO stays NOT-YET (C3a 2025 −11.6 %). |
| 3 | **Promote #6987 arm A, not this lever.** Prune all four NEXT-26 runs; `nyiso_li_tsl_all_hours` → R (effect too small to carry). | ISO CALIBRATED without the Zone-K window repair. Not recommended: the lever passes its rule and is structurally owed (rule 17). |
| 4 | Decline everything. | Prune NEXT-25 and NEXT-26 runs; both cells → R. |

**Cost of option 1:** one `promote_keeper.py` run on #6987's or this PR's branch. The bundles are already slim-committed on this PR's branch (`results/calibration/nyisonext26p_span`, `_2021`). Full legs live on the shard branches `claude/nyisonext26p-2021..2025` until the lane's PR merges.
