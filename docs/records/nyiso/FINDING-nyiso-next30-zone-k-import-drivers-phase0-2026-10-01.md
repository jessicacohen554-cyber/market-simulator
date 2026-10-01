# FINDING — NYISO-NEXT-30 phase 0: no admissible driver of the Zone-K import limit in the public postings

**Session:** NYISO-NEXT-30 orchestrator, 2026-10-01. **Solves: ZERO.**
**Keeper (unchanged):** `2026-10-01-nyisonext21-astoria-hr-span` plus the stamped `-2021` run.
**Object:** open item 2, the dominant Zone-K object since NEXT-29. 69–100 % of the annual K-over-J spread miss sits in hours where the model's `NYC>Long_Island` link is below 940 MW, while NYISO's DAM binds the Zone-K import set.
**Probe and record:** `scripts/probes/nyisonext30_zone_k_import_drivers.py`, `results/phase0/nyiso/_nyisonext30_zone_k_import_drivers.json`.

## 1. Result

1. **Public sources exist for 2021–2025, but neither is an admissible driver of the limit.**
   - MIS P-33 `outSched` carries the outage windows for every Zone-K import element.
   - MIS P-34 `ParFlows` carries measured flow on the Zone-K PARs.
2. **Outage windows do not explain the uncapped-hour congestion.** Y49/Y50 out-hours hold 31–76 % of the annual DA K−J congestion, but the outages are long and seasonal. Matched within the month, the effect is small and inconsistent. The published 940 MW already takes Y49 as its applied N-1 outage.
3. **The PAR schedules do not track the spread.**
   - The 901/903 wheel nets to 0–45 MW a year. Its correlation with the spread is −0.04 to 0.22, and 0.08 pooled once demeaned by month.
   - The Y49 East Garden City PAR flow is an operator setpoint with no published schedule rule. Feeding it in hourly would pin a measured flow on the very interface being scored (rule 13).
4. **No lever, no PRECOMMIT.** The residual goes to the owner as a model-class limitation candidate, as with CENTRAL EAST: the reduced network cannot represent Y49/Y50 loading.

## 2. Sources (grain and coverage)

| source | what | grain | 2021–2025 |
|---|---|---|---|
| P-33 `outSched` | scheduled out/in per facility (PTID + equipment name). Covers Y49 `SPRNBRK_-EGRDNCTR_345_Y49`, Y50 `DUNWODIE-SHORE_RD_345_Y50`, 901, 903, the Lake Success / Valley Stream / East Garden City PARs, the Shore Road and East Garden City 345/138 banks, and `SCH-NPX_1385` limit steps | minute timestamps, daily postings | all 60 months, HTTP 200 |
| P-34 `ParFlows` | measured flow per PAR PTID (60 PTIDs; identity from P-33 equipment names) | 5-minute | all 60 months |
| DAM limiting constraints | binding facility, contingency, shadow cost | hourly | staged (no MW limit) |

Neither posting publishes an **effective import limit**, either for the interface or for an element under an outage. The TSL report publishes one number, 940 MW. It is computed at summer design, with Y49 as the applied N-1 outage and Y50 at LTE 964 MVA as the limiting element (`FINDING-nyiso130-…` §1).

## 3. Outage windows (P-33, latest posting per window)

| out-of-service hours | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| Y49 | 4,156 | 4,369 | 3,835 | 293 | 0 |
| Y50 | 1,573 | 246 | 1,110 | 5,285 | 1,702 |
| 901 / 903 | 262 / 284 | 193 / 137 | 89 / 466 | 360 / 255 | 187 / 191 |
| share of DA K−J mass in Y49 or Y50 out-hours | 75 % | 56 % | 52 % | 76 % | 31 % |

DA K−J spread when out vs month-matched in ($/MWh; mean over months that have both states):

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| Y49 out − in (months) | +13.4 (3), median +4.0 | +6.8 (3), median +2.5 | +1.8 (1) | −0.8 (2) | — |
| Y50 out − in (months) | +6.8 (2) | +0.5 (2) | 0.0 (3), median +1.1 | +4.0 (5), median +0.4 | +0.6 (3), median −0.2 |

**Reading:**
- The raw mass share is mostly season and year: the long outages span whole quarters.
- Within the month, the outage effect is a few $/MWh at the median, has an inconsistent sign, and rests on 1–5 months a year.
- It cannot carry the uncapped-hour miss of $1.8–10.8/MWh (NEXT-29 §2), which runs in every year and season.
- **Y49 out is the published TSL's design case, so a Y49 window cannot lower the 940 MW.**
- A Y50-out limit is not published. A derate built from cable ratings would be a constructed number, not a published one (rule 1).
- Caveat: P-33 is *scheduled* outages. Actual timing would need P-34 corroboration, which exists only for PARs.

## 4. PAR schedules (P-34)

| mean (std) MW | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| 903 Lake Success PAR | 111 (72) | 128 (63) | 125 (63) | 36 (59) | 111 (64) |
| 901 Valley Stream PAR | −72 (46) | −93 (28) | −80 (35) | −38 (47) | −86 (52) |
| net wheel 901+903 | 39 (58) | 36 (66) | 45 (49) | −1 (52) | 25 (56) |
| East Garden City PAR1+2 (on Y49) | 238 (230) | 211 (224) | 209 (205) | 296 (192) | 227 (189) |

| correlation | 2021 | 2022 | 2023 | 2024 | 2025 | pooled, month-demeaned |
|---|---:|---:|---:|---:|---:|---:|
| net wheel vs DA K−J spread | −0.02 | 0.15 | 0.22 | −0.04 | 0.03 | 0.08 |
| EGC (Y49) PAR vs spread | −0.24 | 0.01 | 0.06 | 0.15 | 0.32 | 0.06 |
| net wheel vs import-set binding | 0.29 | 0.08 | 0.30 | −0.04 | 0.08 | — |

**Reading:**
- The ConEd–LIPA wheel circulates 75–130 MW through LI's 138 kV system, J→K on 903 and K→J on 901. Its net effect on the J–K interface is under 50 MW, and it does not track the spread.
- Y49's PAR flow is the variable component (std ≈ 200 MW). It is an operator setpoint, and no posting states the rule that sets it.
  - The NY–NJ PARs were admissible because NYISO publishes their percentage rule (nyiso-127).
  - No equivalent rule is published for Y49.
- An hourly Y49 input at measured flow is pinning (rule 13).

## 5. Disposition

- **LEAD B closed at zero LP.** The sources exist, and their grain is recorded above. None yields a forward-reproducible effective Zone-K limit, and none explains the uncapped-hour congestion when matched within the month.
- **Owner card (new): ledger open item 2 as a model-class limitation, like CENTRAL EAST.**
  - The binding set is Y50 for the loss of Y49 (and vice versa), loaded by I/J 345 kV flow distribution and the Y49 PAR setpoint.
  - One net J→K link cannot represent that.
  - Re-open only on published shift factors for the Zone-K import set, or a published Y49 PAR schedule rule.
- **Side note (not acted on):** 2021 shows $10/MWh of K−J spread in DAM hours with no import-set facility in the posting (2022–2025: $0.5–3.1). The 2021 DLC coverage or naming may differ. Recorded, not chased.
- No cell moves. `nyiso_li_tsl_all_hours` stays O pending card 1 (#6992).
