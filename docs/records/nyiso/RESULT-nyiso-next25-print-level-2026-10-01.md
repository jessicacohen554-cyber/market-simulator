# RESULT — NYISO-NEXT-25: daily gas at each day's own Z6 print — arm A passes its promotion rule; owner card — 2026-10-01

- **Pre-registration:** `docs/records/nyiso/PRECOMMIT-nyiso-next25-print-level-2026-10-01.md` (merged in #6986, pin `f43f609b`).
- **Phase 0:** `docs/records/nyiso/FINDING-nyiso-next25-offcap-winter-gap-phase0-2026-10-01.md`.
- **Legs:** ten year-isolated shards (rule 36), all pinned at `f43f609b`. Each leg's bytes were verified against its remote blob before its shard was archived. Provenance SHAs are in `.gitignore`.
- **Runs registered (probes, rule 15):**
  - Arm A: `2026-10-01-nyisonext25-printlevel-span` / `-2021`, bundles `results/calibration/nyisonext25_span` / `_2021`.
  - Arm B: `2026-10-01-nyisonext25f-flowprint-span` / `-2021`, bundles `nyisonext25f_span` / `_2021`.

## 1. Gates (PRECOMMIT §4)

| gate | arm A (vs keeper) | arm B (vs NEXT-23 arm) |
|---|---|---|
| G-1 leg acceptance | PASS, 5/5 | PASS, 5/5 |
| G-2 2025 Jan off-cap NYC price rises | PASS: $85.14 → **$95.88** (24 days) | PASS: $71.49 → $91.05 |
| G-3 demand / slack | PASS: 0.0 / 0.0 GWh, every year | PASS: 0.0 / 0.0 |
| G-4 C6 / C8 | PASS | PASS |
| G-5 no new D-4 FAIL row ≥ 5 GWh | PASS; listed: 2022 bridge × ST_GAS 8906, **1.0 GWh** | PASS; listed: 2022 bridge × CC_REGULAR 54574, 1.4 GWh |

Gates: `results/phase0/nyiso/_nyisonext25_gates_{A,B}.json`.

## 2. Scores (rubric 3.13)

| C3a (system, vs RT) | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| keeper | +2.9 | −2.4 | +1.2 | −4.0 | **−11.6 FAIL** |
| NEXT-23 arm | +3.5 | −1.7 | +1.7 | −3.1 | −12.7 FAIL |
| **arm A** | +2.9 | −2.1 | +0.4 | −2.6 | **−9.6 PASS** |
| arm B | +2.4 | −0.4 | +0.0 | −1.8 | −10.3 FAIL |

| C3b NRMSE | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| keeper | 0.108 | 0.155 | 0.122 | 0.113 | 0.181 |
| arm A | 0.113 | 0.147 | 0.130 | 0.126 | 0.161 |
| arm B | 0.113 | 0.119 | 0.123 | 0.137 | 0.166 |

| determination | span 2022–25 | 2021 | ISO |
|---|---|---|---|
| keeper | NOT-YET (C3a 2025; C3c 2023–25 not lone) | CALIBRATED | NOT-YET |
| **arm A** | **CALIBRATED** (C3c lone → auto-ledgered caveat, rule 22) | CALIBRATED | **CALIBRATED** |
| arm B | NOT-YET (C3a 2025 −10.3 %) | CALIBRATED | NOT-YET |

C1, C2, C4, C6 and C8 PASS in every run. C3c counts are unchanged: 8 h vs 42 h in 2025.

**Zones, 2025, vs DA (annual / winter):**

| zone | keeper | arm A |
|---|---|---|
| NYC | −9.1 / −13.7 | −7.1 / −8.7 |
| Capital_Hudson | −11.1 / −17.5 | −9.1 / −12.8 |
| Long_Island | −12.8 / −17.6 | −10.9 / −13.0 |
| Upstate_West | −1.6 / −0.6 | +0.5 / +4.9 |

## 3. Against the prediction (PRECOMMIT §6)

- **C3a 2025 improves by 2–5 pts: held at the low end (+2.0).** The LP moved less than the phase-0
  bracket (NYC 2025 −7.1 vs bracket −6.7…−5.0). That is expected: the bracket scales gas-marginal hours
  only.
- **2023 winter worsens: held.** NYC winter −3.3 → −6.4 % (Feb factor 1.14). Annual C3a 2023 still improves
  (+1.2 → +0.4).
- **Upstate_West rises: held.** 2025 winter −0.6 → +4.9 %.
- **B moves 2025 further than A: refuted.** B is at −10.3 % vs A's −9.6 %. Flow-dating moves the MLK
  package off 1/17. The cap-binding days lose more than the print-level repair returns. B is better than A
  in 2022–2024 (C3a and winter zones).
- **The Central East deficit remains (ledgered): held.** Capital_Hudson is still −9 % annual in 2025.

## 4. Reading

The repair is live and moves in the pre-registered direction. It is zero-DOF and passes every
pre-registered gate.

**Arm A meets PRECOMMIT §5's promotion rule:** G-1 to G-5 hold in all five years, and no determination
downgrades. The span and the ISO move NOT-YET → CALIBRATED.

**Margin caveat, stated plainly:** C3a 2025 is −9.6 % against a ±10 % gate, which is 0.4 pt of margin. The
determination flip rests on a small margin from a structural change. It does not rest on a tuned value.

## 5. DECISION CARD (owner)

| | option | effect |
|---|---|---|
| **1 (recommended)** | **Promote arm A** (`promote_keeper.py --bundle results/calibration/nyisonext25_span --fold results/calibration/nyisonext25_2021=...`). Cell `nyiso_gas_daily_print_level` O → K. | ISO NOT-YET → **CALIBRATED**. Prunes NEXT-21's stores (they stay in git history). |
| 2 | Promote arm B instead. This is the composite: flow-date (#6984) plus print-level, the most complete reading of the source convention. | Span NOT-YET (C3a 2025 −10.3 %); ISO NOT-YET. Needs a ruling on #6984 as well. |
| 3 | Decline both. | Prune the four NEXT-25 runs; cell → R with this citation. |

**#6984 interaction.** If option 1 is taken, NEXT-23's flow-date alone (C3a 2025 −12.7 %) is dominated
by A on every 2025 number. Arm B shows that flow-dating's 2022–2024 gains survive on top of print-level.
Recommendation: **decline #6984 as a standalone promotion.** Keep `nyiso_gas_flow_date` open (O),
recorded as "composes with print-level; 2025 −0.7 pt vs A".

## Ruling (2026-10-02)

**Superseded by NEXT-26 arm B** (print-level + all-hours Zone-K TSL), promoted on the owner's ruling 'Promote arm B'. The four NEXT-25 runs were never merged to `main`; this record, its probes and gate JSON are kept.
