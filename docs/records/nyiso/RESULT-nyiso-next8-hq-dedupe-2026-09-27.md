# RESULT — NYISO-NEXT-8: HQ double count removed from the import-ladder derivation; promoted — 2026-09-27

- **Session:** NYISO-NEXT-8, the orchestrator. No LP ran in this container (rule 32 (a)).
- **PRECOMMIT:** `docs/records/nyiso/PRECOMMIT-nyiso-next8-hq-dedupe-2026-09-27.md`, which holds phase 0, G-DRIFT, the gates and the promotion rule. It was written before any solve.
- **Arm pin:** `8184ca75cbfc4142996b8cc6bb792df04e9c2f70`.
- **New keeper:** `2026-09-27-nyisonext8-hq-dedupe-span` (bundle `results/calibration/nyisonext8_span`, 2022–2025).
- **Stamped held-out run:** `2026-09-27-nyisonext8-hq-dedupe-2021` (bundle `results/calibration/nyisonext8_2021`).
- **Superseded and pruned (rule 35):** `2026-09-27-nyisonext6-li-cap-span` and its stamped 2021 run.

## 1. Headline

- **The defect.** `derive_nyiso_import_tranches.py` summed `SCH - HQ_IMPORT_EXPORT` alongside `SCH - HQ - NY`, but the first row is an accounting duplicate of the second (corr 0.955–0.993, every year 2018–2025). Every committed NYISO ladder was therefore derived on a net import that counted HQ twice.
- **The fix.** The producer now imports `nyiso_par_attribution.ACCOUNTING_DUPLICATE` and asserts it is never re-listed (rule 19). A regression test covers this.
- **Scope of the re-derivation.** Every NYISO ladder was re-derived with the same frozen formula: the pooled static ladder and every year 2018–2025. The offline duration RMSE falls from 337–902 MW to 204–297 MW. The fix landed on `main` as a direct correction to a measured input, with no new field and zero DOF.
- **Promotion.** Promoted on structure under the ex-ante rule (PRECOMMIT §7). G-1, G-2 and G-3 all pass.
- **Determination unchanged.** The span is NOT-YET (C3a 2022 −11.3 %, 2025 −11.2 %; C3c fails, but not as the only failure). 2021 is CALIBRATED.

## 2. Gates (arm vs the NEXT-6 keeper's committed bundles, form 4)

Records: `results/phase0/nyiso/_nyisonext8_gates.json` and `results/phase0/nyiso/_nyisonext8_compare_span.txt`.

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **G-1** leg acceptance (pin, recipe, inputs, LI-clip line) | pass | pass | pass | pass | pass |
| **G-2** Δ import TWh (must be ≤ +0.01 in 2021/2022) | **−0.079** | **0.000** | +0.004 | +0.011 | +0.104 |
| **G-3** C6 / C8 | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS |
| Δ system LW price ($/MWh) | +0.04 | +0.12 | +0.02 | +0.04 | −0.21 |
| Δ Upstate_West LW price ($/MWh) | +0.10 | +0.34 | −0.01 | +0.08 | −0.09 |
| max \|Δ class\| (TWh) | 0.10 (CC_CHP) | 0.02 | 0.02 | 0.07 (ST_GAS) | 0.23 (ST_GAS) |
| C3a, keeper → arm (%) | CALIBRATED → CALIBRATED | −11.5 → **−11.3** | −2.6 → −2.5 | −1.0 → −0.9 | −10.9 → **−11.2** |
| C3b NRMSE | — | 0.191 → 0.191 | 0.126 → 0.125 | 0.162 → 0.161 | 0.171 → 0.172 |

- **Directions.**
  - 2022: the static rungs rose, and the node price rose with them. Import volume held because the seam envelope caps bind.
  - 2025: the IESO and PJM_shoulder rungs fell by $13–17, so import rose 0.10 TWh and prices fell 0.21 $/MWh.
  - Both are the response the corrected input implies. C3a is not a criterion (PRECOMMIT §7).
- **D-4 unit-conduct.** The FAIL count is unchanged at 8. One row clears (2024 54574) and one appears (2025 8906).
- **Benchmark frames.** The composite adopted the span benchmark frames (`--rebuild-benchmark`). All ten of its `shared_inputs` hashes equal the NEXT-6 keeper span's, so both sides are scored on the same benchmark.

## 3. Legs (rule 36; provenance SHAs only, rule 33 (d))

| year | shard commit | files |
|---|---|---|
| 2021 | `41df05f453c8ff92c25bb86d27858cedc1fa9d66` | 18 |
| 2022 | `0b1a9021f19c7f3af05eb38cc3811929328c15b4` | 18 |
| 2023 | `0a1d99f27dd4470d4868a031fd704c262b5fff51` | 18 |
| 2024 | `b6943beab05cf1a69db82970625ea9a2c847cbe0` | 18 |
| 2025 | `1f56d8eb18403daaf69aa8da0bd02c938729a441` | 18 |

- **Prompt defect, recorded.** The shard prompt omitted `scripts/regenerate_clean.py`, the rebuild of the gitignored curated tree.
  - Three shards ran it on their own.
  - The first 2022 and 2023 shards stopped as instructed and were relaunched with the step.
  - The next handoff's shard template carries it.
- **Archived.** All seven shard sessions (five legs plus the two stopped first attempts).
- **Retrievability.**
  - The registered keeper bundle and the 2021 bundle land on `main` with this PR.
  - The per-year legs 2022–2025 are gitignored (rule 32 (d)).
  - The leg SHAs above are provenance, not a recovery route.

## 4. What remains

1. **C3a 2022 / 2025 (−11.3 / −11.2 %).** This lever was a correction, not a closer, and it moved each year by about 0.2–0.3 pp.
2. **Eastern over-delivery** (NEXT-7 §2: 4.85–7.60 TWh/yr east of Central-East). This needs neighbour-price intake: IESO hourly, PJM at the NYIS interface plus the Neptune/HTP/VFT source pnodes, and ISO-NE at the NY external nodes, 2021–2025.
3. **The >$300 RT tail** (nyiso-242).
4. **The in-city commitment requirement.** MyNYISO access is held by the owner.
5. **The 2025 downstate level shortfall.**
6. **Routed:** the 900 MW HQ_hydro always-on floor exceeds measured total net import in 0.5–6.5 % of hours every year. This is a rule-17 question (PRECOMMIT §3).
7. **Leftover branches for the owner to delete** (a session cannot delete refs):
   - `claude/nyiso-next8-hq-dedupe` (fully on `main`);
   - `claude/nyisonext8-{2021,2022,2023,2024,2025}` (bytes composed onto `main`).
