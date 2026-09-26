# RESULT — NWPP-NEXT-6: WECC Path 76 link and the SB-population CT heat-rate re-derive, 2019–2025 → KEEPER #13

**Run:** `2026-09-26-nwppnext6-path76-ctrederive` (arm AB), bundle `results/calibration/nwppnext6ab_span`.
**PRECOMMIT:** `docs/handoffs/PRECOMMIT-nwppnext6-path76-and-ct-rederive-2019-2025-2026-09-26.md`.
**Control:** keeper #12 `2026-09-26-nwppnext5-standby`, using its committed bundle (G-DRIFT form 4, PRECOMMIT §3).
**Solved by:** 14 year-isolated shards (rule 36): arm A at `e29efd5f`, arm AB at `0a84941d`. The parent ran no LP.
All 14 legs passed hard stops 1–7. Four arm-A shards restarted mid-run and finished later.
**Status: PROMOTED** to NWPP keeper #13 on the owner's standing structure ruling.
- Keeper #12 and arm A (`2026-09-26-nwppnext6-path76`) were pruned (rule 35).
- `audit_keepers --iso NWPP` PASSES (E14 package-pin warnings only).

## 1. Determination

**NOT-YET on {fuelmix, dispatch_corr}**, the same set as keeper #12. C2, C6 and C8 PASS. Price is UNSCORED
(rubric v3.8).

| Criterion | Keeper #12 | Arm A (Path 76 only) | **AB (promoted)** |
|---|---|---|---|
| C1 CC_REGULAR 2019 | +7.42 | — | +7.77 PASS |
| C1 CC_REGULAR 2020 | +9.40 FAIL | +9.81 FAIL | **+9.94 FAIL** |
| C1 CC_REGULAR 2024 | +7.67 PASS | PASS | **+8.30 FAIL** (band 8.00) ← the one flip |
| C1 CT_PEAKER 2020 | +3.63 | — | +2.95 |
| C1 CT_PEAKER 2024 | +1.31 | — | +0.40 |
| C4 gas 2020 NRMSE | 0.310 | 0.311 | 0.307 (FAIL) |
| C4 coal r 2023 / 2024 / 2025 | 0.669 / 0.586 / 0.664 | 0.669 / 0.583 / 0.663 | 0.673 / 0.582 / 0.655 (FAIL) |

- **Arm A alone: zero flips.** Every one of its FAILs was already a FAIL in keeper #12.
- **The CC_REGULAR 2024 flip, attributed** (2024 CC_REGULAR TWh):

  | Keeper #12 | Arm A | AB |
  |---|---|---|
  | 64.58 | 64.85 | 65.21 |

  - The Path 76 link adds +0.27 TWh and the re-derive +0.36 TWh.
  - It is CT_PEAKER energy (the Fredonia over-run) substituting onto CC. CT falls 0.2–0.9 TWh/yr; CC rises by
    about the same.
  - CC_REGULAR is already 7–10 TWh long in 2019, 2020 and 2024, so this is a pre-existing structural defect that a
    corrected input exposes (rule 14). It is **routed as lever 4, never tuned** (rules 1 / 13).

## 2. What moved

| Year | Unserved GWh, keeper → AB | Fredonia GWh, AB (keeper #12; EIA-923) | Sun Peak GWh | Path 76 TWh N→S / S→N | h at rating |
|---|---|---|---|---|---|
| 2019 | 15.4 → 4.5 | 185 (495; 196) | 9 | 1.32 / 1.09 | 7,359 |
| 2020 | 118.8 → 46.6 | 40 (431; 195) | 194 | 1.69 / 0.71 | 7,232 |
| 2021 | 73.8 → 34.0 | 11 (68; 386) | 47 | 1.92 / 0.55 | 7,715 |
| 2022 | 37.8 → 7.5 | 201 (247; 273) | 19 | 2.23 / 0.28 | 7,991 |
| 2023 | 9.0 → 1.5 | 201 (533; 967) | 18 | 1.94 / 0.52 | 7,618 |
| 2024 | 27.1 → 13.6 | 670 (1,610; 554) | 51 | 1.41 / 1.03 | 7,515 |
| 2025 | 2.6 → 1.2 | 989 (1,575; 110 partial) | 36 | 1.39 / 1.04 | 7,470 |

- **Unserved energy falls 52–86 % in every year.** Arm A alone produces the identical unserved figures: the link does
  it, not the heat rate.
- The 2020–21 SNV residual (46.6 / 34.0 GWh) is beyond the 300 MW block. The PRECOMMIT census bounded the link's reach
  at 52–58 % in those years, and the realised cut is 61 % / 54 %.
- **Fredonia.** The measured rate brings 2024 from 2.9× EIA-923 to 1.2×, and 2019 to within 6 %.
  - It now under-runs in 2021 and 2023. Its dispatch is highly sensitive around a flat NW price, as PRECOMMIT §1.4
    stated.
  - 2025 (989 GWh) is still well above the partial EIA-923 year.
- **Path 76 over-flows, as stated before the solve.** It sits at its 300 MW rating 83–91 % of hours, in **both**
  directions (a price-arbitrage LP link). The measured BPAT→NEVP seam averages only 20–28 MW net.
  - That is a real structural gap: the model has no loop-flow or contract-path limitation on an internal link.
  - It is recorded, not tuned. A derate to the measured flow would be the rule-13 answer-key the program forbids.

## 3. Routed (for the next lane)

1. **C1 CC_REGULAR long, 2019 / 2020 / 2024** (+7.8 / +9.9 / +8.3 TWh): lever 4. Diagnose by merit order, heat-rate
   class and hydro year.
2. **C4 coal 2023–25 r:** lever 3. Run a zero-LP driver census of real hourly coal swing before choosing a mechanism.
   Owner questions Q1–Q6 in `FINDING-nwppnext5-coal-take-obligation-design-2026-09-26.md` are still open.
3. **SNV 2020–21 residual shed and the NEVP served-schedule import rigidity** (Path 81 SNTI): lever 2b.
4. **Internal-link over-flow.** All NWPP links arbitrage to their rating. Whether a measured-flow basis belongs in the
   model is a structural question, not a tuning one.
5. **Jim Bridger (8066)** has no measured coal tranche row (lever 5).

## 4. Retrievability (rule 34(e))

- The composite bundle (slim files and `hourly/`), its registry sidecar and its run payload land on `main` with this
  lane's PR.
- The 14 per-year legs are gitignored on local disk and do not survive the session.
- Leg SHAs are provenance only (rule 33(d)); recovery of any leg is a re-solve (~25 min per year).

| Year | Arm A | Arm AB |
|---|---|---|
| 2019 | `3961f07b` | `8ea98e94` |
| 2020 | `4acf4fd9` | `d0c7388e` |
| 2021 | `e8146491` | `c7a95375` |
| 2022 | `1f42d401` | `0900342f` |
| 2023 | `31a920c1` | `acc93951` |
| 2024 | `f3231b1a` | `c1628302` |
| 2025 | `e1a9c87f` | `c3897a90` |

- All 14 shard sessions are archived.
- **Leftover shard branches for the owner to delete** (a session cannot delete refs):
  `claude/nwppnext6a-{2019..2025}` and `claude/nwppnext6ab-{2019..2025}`.
