# RESULT — NYISO-NEXT-15: per-landing-link monthly import band on five years — 2026-09-30

- **Session:** NYISO-NEXT-15, the orchestrator. This container ran no LP (rule 32 (a)).
- **Phase 0:** `docs/FINDING-nyiso-next15-landing-allocation-phase0-2026-09-30.md`.
- **PRECOMMIT:** `docs/PRECOMMIT-nyiso-next15-landing-band-2026-09-30.md`. Its gates (§4) and promotion rule (§5) were fixed before any solve.
- **Owner decision cards (this session):** "Build + test 5 yrs"; "P-32 per link"; "Promote per rule".
- **Code:** PR #6900 (`nyiso_import_landing_band`, default off, zero free parameters).
- **Arm pin:** `4c98e6dd460af9a600d48039176e0378cd577bf6`.
- **New keeper:** `2026-09-30-nyisonext15-landing-band-span`, bundle `results/calibration/nyisonext15_span`, years 2022–2025.
- **Stamped held-out run:** `2026-09-30-nyisonext15-landing-band-2021`, bundle `results/calibration/nyisonext15_2021`.
- **Superseded and pruned (rule 35):** `2026-09-30-nyisonext14-total-east-span` and its stamped 2021 run.

## 1. Headline

- **Structure: met.** Every pooled import link now carries its measured schedule (G-2), and all other gates hold in all five years.
- **Rubric: span CALIBRATED → NOT-YET.** C3b 2022 moves 0.195 → 0.200 and crosses the ≤ 0.20 band, so the ledgered C3c is no longer the lone failure.
- **The Upstate_West overshoot is not an import-allocation effect.** The link now carries 150–420 MW more in the market's CENTRAL EAST binding hours, but zonal prices move ≤ $0.8/MWh, and the binding-hour lift and spread do not improve.

## 2. Gates and reported numbers (arm vs the NEXT-14 keeper's committed bundles, form 4)

Records: `results/calibration/_nyisonext15_gates.json`, `_nyisonext15_compare_span.txt`, `_nyisonext15_compare_2021.txt`.

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **G-1** leg acceptance | pass | pass | pass | pass | pass |
| **G-2** Upstate_West import, arm / measured MW (keeper) | 2,208 / 2,165 (1,792) | 1,848 / 1,825 (1,505) | 1,151 / 1,128 (820) | 1,037 / 1,019 (644) | 756 / 741 (477) |
| **G-2** NYC import, arm / measured MW (keeper) | 634 / 621 (840) | 698 / 684 (871) | 741 / 726 (972) | 754 / 739 (889) | 826 / 809 (962) |
| **G-3** link at its bound, % of h (band 1–50) | 16.9 | 27.2 | 17.3 | 8.9 | 12.8 |
| **G-4** Upstate_West h ≤ $0 | 0 | 0 | 0 | 0 | 0 |
| **G-5** C6 / C8 | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS |
| **G-6** P1 load slack, GWh (keeper) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| link flow in market CE-binding h, arm / keeper / measured TE (MW) | 4,142 / 3,719 / 4,197 | 3,856 / 3,479 / 4,556 | 3,399 / 3,059 / 3,777 | 3,722 / 3,574 / 5,212 | 3,904 / 3,674 / 5,039 |
| C3a, keeper → arm | +10.9 → +11.4 % | +2.3 → +3.2 % | +5.0 → +5.6 % | −1.4 → −1.6 % | −8.8 → −9.2 % |
| C3b NRMSE, keeper → arm | 0.165 → 0.169 | 0.195 → **0.200** | 0.141 → 0.146 | 0.155 → 0.158 | 0.160 → 0.164 |
| Upstate_West $/MWh, keeper → arm | 41.07 → 41.23 | 77.40 → 78.14 | 32.14 → 32.36 | 35.55 → 35.45 | 57.52 → 57.24 |
| binding-hour lift vs market (keeper) | 1.20 (1.37) | 0.65 (0.74) | 0.93 (1.07) | 0.87 (0.31) | 0.59 (0.69) |
| CH − UW spread in binding h, model (measured basis) | 2.3 (20.2) | 5.5 (55.8) | 1.6 (19.7) | 1.7 (34.7) | 2.4 (42.1) |
| price MAE $/MWh, keeper → arm | 11.75 → 11.89 | 25.92 → 26.50 | 9.44 → 9.56 | 9.41 → 9.45 | 24.87 → 24.96 |
| NYC ST_GAS TWh, keeper → arm (EIA-923) | — | 4.80 → 5.03 (2.27) | 8.31 → 8.65 (2.56) | — | — |

- The phase-0 prediction held on flows (Upstate_West +264 to +416 MW) and failed on price: the extra upstate import crosses the link without congesting it. The link's cap is the monthly p90 TOTAL EAST level, and its binding still does not track the market's.
- NYC steam rises as NYC imports fall to their measured level. That is the NYC steam object (queue item 4), now exposed rather than masked by the phantom downstate import.

## 3. Legs (rule 36; provenance SHAs only, rule 33 (d))

| year | shard commit | files |
|---|---|---|
| 2021 | `caa7a405fff2fe7c9f053dc54e5a0357a5187f4e` | 17 |
| 2022 | `8433152e1b6568630f447ba56528af6258e36b75` | 17 |
| 2023 | `b4cefa9585b06960e6839e352ead337094e18969` | 17 |
| 2024 | `77dbf840e10f67f91100d55fb91795f8582ea741` | 17 |
| 2025 | `eedd688cc0ba59738bd82c3ee5c1af750ddb0f60` | 17 |

- **Retrievability.** The keeper bundle `nyisonext15_span` and the 2021 bundle land on `main` with this PR. The 2022–2025 legs are gitignored (rule 32 (d)). Recovering a leg not on `main` costs a re-solve (~5 min of LP per year).

## 4. What remains

1. **C3b 2022 (0.200).** The 2022 monthly price shape sits on the band edge.
2. **The Upstate_West overshoot and the wrong-hours binding.** Not an import effect (§2). The remaining halves: upstate generation and load in the market's binding hours, and how one zonal link represents the CENTRAL EAST sub-cutset inside TOTAL EAST.
3. **2025 peak formation** (C3a −9.2 %): winter gas days, the June heat wave, the >$300 tail.
4. **NYC steam** (2023 8.65 vs 2.56 TWh) and the in-city commitment requirement (MyNYISO access is owner-held).
5. **The `complete` marker** stays withdrawn (the keeper reads NOT-YET).
