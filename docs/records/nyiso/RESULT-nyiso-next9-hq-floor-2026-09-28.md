# RESULT — NYISO-NEXT-9: the always-on 900 MW HQ_hydro import floor removed; promoted — 2026-09-28

- **Session:** NYISO-NEXT-9, the orchestrator. No LP ran in this container (rule 32 (a)).
- **PRECOMMIT:** `docs/PRECOMMIT-nyiso-next9-hq-floor-2026-09-28.md`, which holds phase 0, G-DRIFT, the gates and the promotion rule. It was written before any solve.
- **Arm pin:** `7900ac511f710940bc039aa4de354646d4e10f26`.
- **New keeper:** `2026-09-28-nyisonext9-hq-floor-span` (bundle `results/calibration/nyisonext9_span`, 2022–2025).
- **Stamped held-out run:** `2026-09-28-nyisonext9-hq-floor-2021` (bundle `results/calibration/nyisonext9_2021`).
- **Superseded and pruned (rule 35):** `2026-09-27-nyisonext8-hq-dedupe-span` and its stamped 2021 run.

## 1. Headline

- **The object.** `nyiso_firm_imports` floored the 900 MW `HQ_hydro` import rung at full output in every hour. The floor had:
  - **no published driver**: there is no HQ firm energy contract for 2021–2025. Gold Book Table V-1 is aggregate ICAP from all neighbours; Table III-3d is realized GWh; CHPE enters service only in 2026;
  - **an outcome-percentile level** (rule 13): "≥ 922 MW in 98 % of 2023 hours" of measured total net import;
  - **no window** (rule 17): its D-4 window was h0–23, so D-4 passed vacuously. It bound below its own driver data (measured net import < 900 MW in 46 / 322 / 277 / 572 / 514 h in 2021–2025).
- **The change.** The keeper recipe changes in one field, `nyiso_firm_imports` true → false. It is an existing field, so there is no code change, no new field and zero DOF; one unledgered outcome-level floor is removed.
  - The monthly import level stays set by the measured EIA-930 band (`nyiso_import_reconciliation`, rule 19).
  - `HQ_hydro` is now an ordinary economic rung at its measured Q–Q price.
- **Promotion.** Promoted on structure under the ex-ante rule (PRECOMMIT §7). G-1, G-2 and G-3 all pass.
- **Determination unchanged.** The span is NOT-YET (C3a 2022 −11.3 %, 2025 −11.4 %; C3c fails, but not as the only failure). 2021 is CALIBRATED.
- **As predicted ex ante, this is not a C3a closer.** Removing the floor lets the monthly band move the same volume into higher-priced hours, so prices move slightly *down*.

## 2. Gates (arm vs the NEXT-8 keeper's committed bundles, form 4)

Records: `results/calibration/_nyisonext9_gates.json` and `results/calibration/_nyisonext9_compare_span.txt`.

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **G-1** leg acceptance (pin, one-field delta, inputs, no D-2 `firm_import`) | pass | pass | pass | pass | pass |
| **G-2(a)** hours with import < 900 MW, keeper → arm | 0 → 0 | 0 → 0 | 0 → 52 | 0 → 162 | 0 → 172 |
| measured hours < 900 MW | 46 | 322 | 277 | 572 | 514 |
| **G-2(b)** Δ import TWh (bound 4 %) | 0.000 | 0.000 | 0.000 | 0.000 | −0.006 |
| **G-3** C6 / C8 | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS |
| Δ system LW price ($/MWh) | 0.00 | 0.00 | −0.01 | −0.01 | −0.12 |
| C3a, keeper → arm (%) | CALIBRATED → CALIBRATED | −11.3 → −11.3 | −2.5 → −2.5 | −0.9 → −0.9 | −11.2 → **−11.4** |
| C3b NRMSE | — | 0.191 → 0.191 | 0.125 → 0.125 | 0.161 → 0.162 | 0.172 → 0.173 |

- **D-2:** the `firm_import` row falls from 7.884 TWh/yr to none.
- **D-4:** the unit-conduct FAIL rows are unchanged (8, same units).
- **No criterion changes verdict in any year.**
- **Benchmark frames:** all ten of the composite's `shared_inputs` hashes equal the NEXT-8 keeper span's, and all ten of the 2021 bundle's equal the NEXT-8 2021 bundle's.
- **Still binding in a few hours.** The arm imports ≥ 900 MW in far more hours than measured does (52–172 vs 277–572 below 900). The rest of that gap is the economic ladder plus the monthly band, not a floor.

## 3. Legs (rule 36; provenance SHAs only, rule 33 (d))

| year | shard commit | files |
|---|---|---|
| 2021 | `256972f4590944bb84602e344b4be0fef0e72ca7` | 17 |
| 2022 | `04514ab6cc76831cb6dd57421df4b9f5d8f28dee` | 17 |
| 2023 | `0b0e6631c68ac8ae45b78bbdb98a5c4c27ae747e` | 17 |
| 2024 | `cf22a08d8a8528ec44bbc2ea12758b6b83f61b46` | 17 |
| 2025 | `cec0c6a2fd8aa237cde688709ca33a0ac244c771` | 17 |

- **Incidents, recorded.**
  - The first 2024 shard ended its turn while `regenerate_clean.py` was running and never resumed. It was archived and relaunched, and the relaunched shard then looped on an OOM in `emissions-unit-annual` for about 90 minutes.
  - A backup 2024 shard was launched; it was stopped and archived unsolved once the retry landed.
  - The next handoff's shard template says: never end the turn while a job is running, and do not retry a failing curation datatype.
- **Archived:** every shard session.
- **Retrievability.**
  - The registered keeper bundle and the 2021 bundle land on `main` with this PR.
  - The per-year legs 2022–2025 are gitignored (rule 32 (d)).
  - The leg SHAs above are provenance, not a recovery route.

## 4. What remains

1. **C3a 2022 / 2025 (−11.3 / −11.4 %).** Unmoved by this lane.
2. **Eastern over-delivery** (NEXT-7 §2: 4.85–7.60 TWh/yr east of Central-East). This needs neighbour-price intake: IESO hourly, PJM at the NYIS interface plus the Neptune/HTP/VFT source pnodes, and ISO-NE at the NY external nodes, 2021–2025.
3. **The >$300 RT tail** (nyiso-242).
4. **The in-city commitment requirement.** MyNYISO access is held by the owner.
5. **The 2025 downstate level shortfall.**
6. **Owner question (rule 26).** `inject_nyiso_firm_imports`, `NYISO_FIRM_IMPORT_FLOOR_FRAC` and the `nyiso_firm_imports` field survive, default-off. No keeper arms them any more. Deleting them touches forecast recipes and tests, so it is left for the owner.
7. **Leftover branches for the owner to delete** (a session cannot delete refs): `claude/nyisonext9-{2021,2022,2023,2024}` and `claude/nyisonext9-2025`. The bytes are composed onto `main`. `claude/nyisonext9-2024b` was never pushed.
