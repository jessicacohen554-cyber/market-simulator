# RESULT — NYISO-NEXT-12: the NE AC tie on its own two-way node; promoted on structure — 2026-09-29

- **Session:** NYISO-NEXT-12, the orchestrator. This container ran no LP (rule 32 (a)).
- **PRECOMMIT:** `docs/records/nyiso/PRECOMMIT-nyiso-next11-ne-ac-node-2026-09-28.md`. The gates (§6) and promotion rule (§7) were fixed before any solve. §9 addenda 2–4 hold the G-DRIFT top-ups and the launch defect.
- **Owner ruling in force:** Q-a (2026-09-28): NE AC as its own node, promoted on structure only (rule 1), never on C3a.
- **Arm pin:** `7d238cc95ed843e93c9b934e97983926345479dc` (after PR #6867).
- **New keeper:** `2026-09-29-nyisonext12-neac-node-span` (bundle `results/calibration/nyisonext12_span`, 2022–2025).
- **Stamped held-out run:** `2026-09-29-nyisonext12-neac-node-2021` (bundle `results/calibration/nyisonext12_2021`).
- **Superseded and pruned (rule 35):** `2026-09-28-nyisonext9-hq-floor-span` and its stamped 2021 run.

## 1. Headline

- **Promoted.** G-1, G-2 (a)(b)(c) and G-3 all hold in all five years, so the pre-registered rule promotes.
- **Determination unchanged: NOT-YET.** C3a 2022 −10.1 % and 2025 −11.3 % are still outside ±10 %. C3c fails, not lone. 2021 is CALIBRATED.
- **One new failure.** C1 2023 ST_GAS moves from +2.7 pp (PASS) to +3.2 pp (FAIL). The excess sits in NYC steam: Ravenswood 4.24 TWh and Arthur Kill 1.72 TWh modelled, against 0.79 and 1.04 TWh on EIA-923. That is the in-city commitment problem already on the queue.
- **Price moves the right way, but not enough to close C3a.** C3a moves 2021 −6.5 → −1.7 %, 2022 −11.3 → −10.1 %, 2025 −11.4 → −11.3 %. Hourly price MAE falls in every year.
- **The node itself is only partly right.** It is two-way in every year, as intended. But it sits at its posted export limit 307–969 h/yr, where the measured tie does so 0–4 h/yr. It under-exports in 2021–2023 and over-exports in 2024–2025. PRECOMMIT §4 named this risk ex ante: the bands are driven by the keeper's Capital_Hudson price, which is too low (the C3a shortfall).

## 2. Gates (arm vs the NEXT-9 keeper's committed bundles, form 4)

Records: `results/phase0/nyiso/_nyisonext12_gates.json`, `_nyisonext12_g2b.json`, `_nyisonext12_compare_span.txt`, `_nyisonext12_compare_2021.txt`.

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **G-1** leg acceptance | pass | pass | pass | pass | pass |
| **G-2(a)** hours exporting / importing (P1) | 3354 / 4754 | 2546 / 5311 | 4571 / 3485 | 7499 / 967 | 7730 / 543 |
| **G-2(b)** counted once (zero LP) | pass | pass | pass | pass | pass |
| **G-2(c)** Δ import TWh (bound 4 %) | +0.246 of 27.34 | 0.000 of 27.85 | −0.058 of 23.32 | +0.141 of 20.57 | −0.007 of 19.37 |
| **G-3** C6 / C8 | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS |
| node net TWh (measured) | −0.74 (−5.17) | −1.25 (−3.51) | −2.98 (−4.47) | −7.35 (−5.84) | −7.56 (−5.76) |
| h at posted import / export bound | 170 / 335 | 451 / 307 | 9 / 382 | 38 / 891 | 4 / 969 |
| C3a, keeper → arm | −6.5 → −1.7 % | −11.3 → −10.1 % | −2.5 → −2.1 % | −0.9 → −0.9 % | −11.4 → −11.3 % |
| C3b NRMSE, keeper → arm | 0.187 → 0.153 | 0.191 → 0.192 | 0.125 → 0.118 | 0.162 → 0.160 | 0.173 → 0.177 |
| price MAE $/MWh, keeper → arm | 10.79 → 10.11 | 21.89 → 21.06 | 8.75 → 8.25 | 10.17 → 9.60 | 25.53 → 24.33 |
| C1 ST_GAS share | −0.5 → −0.7 pp | +0.1 → +0.2 pp | **+2.7 → +3.2 pp (FAIL)** | +0.2 → +0.6 pp | preliminary 923, not gated |
| C3c > $300 h, model (RT actual) | — | 5 → 3 (101) | 0 → 0 (10) | 0 → 0 (13) | 2 → 8 (42) |

- **Zonal load-weighted price, Δ $/MWh (arm − keeper).** Downstate zones rise in 2023–2025 by +0.4 to +2.0; upstate and the pooled node fall. In 2021–2022 the pattern reverses: upstate rises by up to +6.7 and downstate falls by up to −0.7.
- **Pooled Capital_Hudson envelope (G-2(b)), mean import MW with NE row → arm:** 2022 280 → 465, 2023 406 → 596, 2024 369 → 680, 2025 464 → 722.
- **D-4 unit-conduct FAIL rows 8 → 10 on the registered span** (9 → 11 counting the held-out 2021 run's one row).
  - New: 2023 54574 CC_REGULAR, 2023 8906 ST_GAS, 2024 54574 CC_REGULAR, 2025 54574 CC_REGULAR.
  - Gone: 2022 54574 CC_REGULAR, 2025 8906 ST_GAS.
  - All are `nyiso_gas_commitment_bridge` rows. C8 passes every year.
- **Benchmark frames.** All ten `shared_inputs` hashes equal the keeper's, for both the span and 2021.

## 3. Legs (rule 36; provenance SHAs only, rule 33 (d))

| year | shard commit | files |
|---|---|---|
| 2021 | `7fee44437c1ace3e9c3f49d6f3d1dc0667a97918` | 17 |
| 2022 | `7d8c14c24ae9c5fe60dd54e1ece5d1b2d37d79d3` | 17 |
| 2023 | `9744b9edd71eb46c1d7a5092bf64ef747b223a5a` | 17 |
| 2024 | `83710bcb63096828f7cb1e0dffd2d28a42e9d1f0` | 17 |
| 2025 | `e64f4c487af1e310649d1b63d3809a590cd9c363` | 17 |

- **Incident, first wave.** The first wave was pinned at `4ba64817`. All five legs failed at LP construction (`layout.py:336`, zone index 6 of 6), 41–49 s in, and nothing was solved.
  - Cause: `run_calibration_full.solve_and_persist` builds its own topology copy to size demand and never applied the NE AC split.
  - Fixed in PR #6867, beside the MISO south-seam split. The fix is reached only with the flag armed on NYISO, so the keeper and every other ISO are byte-identical.
  - The first wave was archived and relaunched.
- **G-1 check fix.** A field that post-dates the keeper is read at its dataclass default. The keeper recorded no `nyiso_ne_ac_node`, which means it solved at `False`.
- **Archived:** all ten shard sessions (both waves).
- **Retrievability.**
  - The keeper bundle `nyisonext12_span` and the 2021 bundle land on `main` with this PR.
  - The per-year legs 2022–2025 are gitignored (rule 32 (d)).
  - The leg SHAs above are provenance, not a recovery route.

## 4. What remains

1. **C3a 2022 / 2025 (−10.1 / −11.3 %).**
2. **The node sits at its posted bound 307–969 h/yr against 0–4 h measured, and over-exports in 2024–2025.** This is not a new free parameter to tune. It reads as the keeper's Capital_Hudson under-pricing showing through. The pricing object downstream is the lever, not the node.
3. **NYC steam over-dispatch** (C1 2023 ST_GAS) and **the in-city commitment requirement**. MyNYISO access is held by the owner.
4. **Rating-bound downstate lines** (Neptune / VFT / CSC) as availability blocks at published ratings (rule 13: no hourly-schedule pinning).
5. **The >$300 RT tail** (nyiso-242: worth $5.44/MWh in 2022, foreclosed by idle sub-gate capacity).
6. **The 2025 downstate level shortfall.**
7. **IESO May–Dec 2025 price** is a public-data gap (Market Renewal).
8. **The pooled `NYISO_external` export sink** is pinned to 0 in P1 by the gas bridge (caiso-138 §D). It cannot be revived as-is (PRECOMMIT-nyiso-next11 §2).
9. **Leftover branches for the owner to delete** (a session cannot delete refs): `claude/nyisonext12-{2021,2022,2023,2024,2025}`. The bytes are composed onto `main`.
