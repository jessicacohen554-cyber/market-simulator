# RESULT closeout-CAISO wave 1, arm 2: `caiso_zonal_gas_basis`, the rule-14 fidelity arm, PROMOTED (2026-10-02)

PRECOMMIT: `PRECOMMIT-closeout-caiso-w1-arm2-zonal-gas-basis-2026-10-02.md`.
- **Desk ruling:** a declared rule-14 fidelity arm with **no gate claim**; it runs after arm 3.
- **Kill rules:** the C3a-2024 (+1.5 pp) and C4-2025 (NRMSE 0.30) tripwires only.
- **Promotion:** on structure, and only if nothing regresses.
- **Preflight:** Addenda A/B, on the arm-3 keeper's P1 marginal layer. 2024 −0.13 pp; 2021 +0.70 pp, report only.

Control: `2026-10-02-closeout-caiso-w1-arm3` (bundle `closeout_caiso_w1_a3_span`). Arm: `--set caiso_zonal_gas_basis=true`,
the only delta. **Keeper: `2026-10-02-closeout-caiso-w1-arm2`** (bundle `results/calibration/closeout_caiso_w1_a2_span`).

## Solves

Seven year-isolated shards, all pinned to `566bc8fa3dd2ad6bdd5e56a2315c744c9be83e07` (the arm-3 PR commit that carries
the control bundle). Every leg was verified before its shard was archived:
- `dispatch/<y>_P1.parquet` present;
- parent commit `566bc8fa`;
- `caiso_zonal_gas_basis: true` and `caiso_ra_min_load_frac: 0.57`.

Arm hard stop: 2019 printed no applier line (no hub-table row). 2020–2025 printed it, for example 2021 "1461 gas
units; … zonal spread −0.52..0.38 $/MMBtu" and 2025 "1476 gas units; … −0.10..0.08". Composed by
`_closeout_caiso_w1_compose_span.py`: every leg is the arm-3 recipe plus the arm field, with one solve-surface
fingerprint and one source SHA.

| Year | Shard commit (provenance; branch `claude/closeout-caiso-w1-a2-<y>`) |
|---|---|
| 2019 | `1ca02579594490fff199211726b16eebcb225b65` |
| 2020 | `07535d603a74f94f56ce1ab3bf283942ed469ac4` |
| 2021 | `905067f84abef9f4500dc431cd4ec5da2400438b` |
| 2022 | `3a53b2ceab09756b2d7d03424f70774a50b0ab59` |
| 2023 | `9794740e58ffe46c6a8563d7c23ae7f6cdb981f3` |
| 2024 | `61f6ad9322336d2a17264bce294927626976375c` |
| 2025 | `ebeacb2b9b3555dbfffec665c07cc33a4da07e34` (no per-leg diagnostics file; regenerated over the span) |

## Gate table (arm-3 keeper → arm 2), every moved scored record

| Criterion | Year | Arm 3 | Arm 2 | |
|---|---|---|---|---|
| **Determination** | all | **NOT-YET** (C1, C3a, C4) | **NOT-YET** (C1, C3a, C4) | unchanged |
| **C3a tripwire** | **2024** | +6.1 % | **+6.6 %** (+0.5 pp; bar +1.5) | ✓ |
| **C4 tripwire** | **2025** | NRMSE 0.286 | **0.283** (bar 0.30) | ✓ |
| C3a vs RT | 2021 / 2022 / 2023 / 2025 | +12.8 / +8.5 / +7.9 / +6.3 % | +12.7 / +8.6 / +7.6 / +6.0 % | |
| C1 CC_REGULAR (TWh) | 2020 / 2021 (FAIL) | +16.44 / +8.69 | +16.45 / +8.11 | 2021 eases |
| C1 CC_REGULAR (TWh) | 2022 / 2023 / 2024 / 2025 | +1.02 / −1.16 / +0.03 / −0.59 | +0.95 / −1.07 / −1.67 / −0.36 | PASS |
| C1 CT_PEAKER (TWh) | 2021 / 2024 | +2.36 / −2.07 | +2.66 / −1.04 | PASS |
| C4 gas r / NRMSE | 2020 / 2021 (FAIL) | 0.89/0.403, 0.855/0.351 | 0.893/0.399, 0.857/0.348 | eases |
| C4 gas r / NRMSE | 2023 / 2024 | 0.907/0.245, 0.92/0.244 | 0.912/0.235, 0.923/0.240 | PASS |
| C3b NRMSE | 2021 / 2023 / 2024 / 2025 | 0.150 / 0.118 / 0.120 / 0.091 | 0.148 / 0.117 / 0.122 / 0.089 | PASS |
| C3c | 2021 / 2023 / 2024 | 89 / 63 / 0 h | 88 / 67 / 0 h (RT 27 / 47 / 35) | 2021 caveat, 2024 ledgered, 2023 PASS |
| C8 CC_REGULAR forced | 2020–2025 | 5.9/6.1/7.0/7.0/9.6/12.4 % | 6.2/6.8/7.1/7.6/10.8/12.3 % | ≤ 30 % |

2019 is identical: the hub table has no 2019 row, so the applier is a no-op.

**What the arm did.** It produced the measured N–S gas gradient, which was its stated purpose.
- In 2021, NP15's load-weighted price fell (56.82 → 56.38 $/MWh) and LA_BASIN's rose (56.16 → 56.25). CC_REGULAR fell
  0.59 TWh, and CT_CHP/CT_PEAKER rose by about the same.
- In 2024 the measured spread reverses sign (north +0.30 / south −0.24 $/MMBtu). CC_REGULAR fell 1.70 TWh, and the
  long-standing CT_PEAKER under-dispatch halved (−2.07 → −1.04 TWh vs EIA-923).
- No level moved beyond ±0.5 pp. No gate claim is made, consistent with the PRECOMMIT.

**Decision (pre-registered): PROMOTE on structure.** Both tripwires held, no gate regressed, and 2019 is identical.
Rule 21: zero free parameters added; the DOF ledger keeps its 10 entries. Matrix cell `zonal_gas_basis` moves R → K
(armed in the keeper), on structure (rule 14) and not on fit.

## Promotion notes

- **The desk's two `promote_keeper.py` fixes worked first time:** E13 is tolerated before the prune, and the
  outgoing C3c 2024 exceptions ledger is carried forward.
- **Replay-guard fix, in this PR.** `scripts/lib/replay_recipe.py` refused the bundle. It had been solved at
  `566bc8fa`, before `#7025` registered `spp_mmu_offer_repair`, and the guard read "recorded None vs replay False" as
  a recipe mismatch.
  - The fix (`_registered_after_solve`) is the mirror of its rule-26 deleted-field exemption. A field absent from the
    recording is excused **only** when the replay resolves it to its registered default.
  - An absent field the replay arms is still reported.
  - Two tests are added in `tests/scoring/test_replay_recipe.py`.
  - Without the fix, every keeper solved before a new field lands fails promotion.
- **Parity check.** It flags only the 14 local per-year leg directories (both arms). They are gitignored via
  `.git/info/exclude`, never committed and never `rm`'d (rule 31), and their bytes are in the shard commits above.
