# RESULT — R-NYISO: NYISO re-solved on corrected backcast inputs (2022–2025); 2019–2021 data-blocked — 2026-09-24

**Session:** R-NYISO (orchestrator; four year-isolated shards; zero LP in this container).
**Pre-registration:** `docs/PRECOMMIT-r-nyiso-backcast-inputs-2026-09-24.md`, pinned at
`e95436d5024fc14096eed558d6dd15a65128e524` before any solve.
**Registered run:** `2026-09-24-nyiso-r-inputs-860vintage` (bundle `results/calibration/rnyiso_span`).
**Incumbent keeper, untouched:** `2026-09-22-nyiso-hydro3-ror-split`. **Nothing was promoted and
nothing was pruned** (rule 31). The promotion question is §7.

## 1. Verdict

- **Determination NOT-YET → NOT-YET.** The same two criteria fail: C1 fuel mix (2023 ST_GAS) and C3c
  price tail. Every other criterion passes in both.
- **The structural corrections landed as pre-registered:**
  - the **phantom coal is gone**: 0.665 TWh of `COAL_PRB` in 2022 → 0.0, against an actual 0.0;
  - class-table-priced thermal MW is down from **296 to 51–56** in 2022–2024;
  - every solved year reads its own EIA-860 vintage (2025 reads the canonical snapshot) and measured
    coal / ST / CC / CT / CHP heat rates.
- **The pre-registered cost also landed.** ST_GAS got 7 % cheaper, so it dispatches more:
  **C1-2023 ST_GAS worsens from +3.61 TWh (+3.0 pp) to +4.99 TWh (+4.1 pp)**, now out of band on
  volume as well as share. This is reported and root-caused (§4), **not re-tuned** (rule 1(c)).
- **Offer curves are byte-identical to the keeper's**, checked leg by leg (S1).

## 2. Leg acceptance (PRECOMMIT §6): all four legs PASS

| year | shard branch SHA (provenance) | S0 pin | S1 config / offers | S2 input sha256 | S3 fleet signature |
|---|---|---|---|---|---|
| 2022 | `ef5da7f882ca8a62c13446481e4b4c6dd6bb74be` | ✔ | ✔ | ✔ | 0 COAL rows |
| 2023 | `5fca472fa7799431a0cf7dbc10827d695172ebb9` | ✔ | ✔ | ✔ | 0 COAL rows |
| 2024 | `0373fcf372f4d6882a51c653ba79abf9bd725e28` | ✔ | ✔ | ✔ | 0 COAL rows |
| 2025 | `d0c020463ee98d2bab3714d7ab6f879f8adfc473` | ✔ | ✔ | ✔ | 27 COAL units, 0.0 MWh |

- **Solve surface:** fingerprint `9dda43dab7ce6be1`, identical across all four legs.
- **Composition:** `scripts/probes/rnyiso_compose_span.py`, zero LP.
- **Shards:** all four archived after their bytes were verified here (rule 33).

## 3. Rubric, old keeper → re-solve, per year (full magnitude)

The benchmark actuals are **identical** old vs new in every class and year. So the miso-267
benchmark-side change flagged at G-DRIFT does not move NYISO's C1, and every delta below is solve
drift.

**C1 fuel mix** (model − actual; tolerance ±3.89 TWh and ±3 pp; 2025 C1 is SKIPPED in both runs):

| year | CC_REGULAR | CC_CHP | CT_PEAKER | ST_GAS | ST_CHP | COAL_PRB |
|---|---|---|---|---|---|---|
| 2022 | +1.62 → +1.43 | −1.22 → −0.62 | −0.54 → −0.86 | **−1.62 → −0.86** | +0.63 → +0.78 | **+0.66 → 0.00** |
| 2023 | +0.05 → −0.64 | +0.20 → +0.27 | −1.81 → −1.85 | **+3.61 → +4.99 (FAIL→FAIL)** | +0.04 → +0.03 | 0 → 0 |
| 2024 | +2.91 → +2.90 | +2.00 → +1.44 | −1.57 → −1.59 | −0.35 → +0.48 | +0.10 → +0.06 | 0 → 0 |

**Everything else:**

| criterion | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| C2 volume | PASS → PASS | PASS → PASS (flags ST_GAS) | PASS → PASS | — |
| C3a mean LMP | −9.3 % → −9.4 % | −2.0 % → −3.4 % | +0.3 % → −0.9 % | −8.9 % → −9.8 % |
| C3b NRMSE | 0.186 → 0.179 | 0.120 → 0.125 | 0.161 → 0.165 | 0.156 → 0.163 |
| C3c h > $300, model vs actual | 17 → **7** vs 101 (CAVEAT) | 0 → 0 vs 10 | 0 → 0 vs 13 | 3 → 2 vs 42 |
| C4 gas r | 0.863 → 0.865 | 0.941 → 0.940 | 0.903 → 0.904 | 0.855 → 0.854 |
| C8 ST_GAS forced share | 20.5 → **16.8 %** | 14.2 → 12.2 % | 20.0 → 17.3 % | 17.1 → 14.9 % |
| C6 governance | PASS → PASS (attested; DOF ledger rebuilt; `authorized_price_tuning` null) | | | |

**Hourly price vs RT actual** (load-weighted across zones; bias and MAE in $/MWh):

| year | actual mean | keeper bias / MAE | re-solve bias / MAE |
|---|---|---|---|
| 2022 | 74.74 | −5.82 / 22.29 | −5.83 / **22.10** |
| 2023 | 30.28 | +0.21 / 8.63 | −0.17 / **8.56** |
| 2024 | 35.97 | +0.91 / 10.15 | +0.50 / **10.05** |
| 2025 | 60.72 | −3.52 / 17.59 | −4.06 / **17.54** |

MAE improves slightly in every year. The mean bias moves down by $0.4–0.5 in 2023–2025.

**Class P1 TWh deltas** (re-solve − keeper; |Δ| ≥ 0.05):

- **2022:** COAL_PRB −0.665, ST_GAS +0.811, CC_CHP +0.608, CT_PEAKER −0.358, CC_REGULAR −0.311,
  CT_CHP −0.233, nuclear −0.163, ST_CHP +0.145, hydro +0.073.
- **2023:** ST_GAS +1.381, CC_REGULAR −0.692, CT_CHP −0.558, nuclear −0.184, CC_CHP +0.068.
- **2024:** ST_GAS +0.835, CC_CHP −0.554, CT_CHP −0.228.
- **2025:** ST_GAS +0.820, CC_CHP −0.468, CT_CHP −0.324, CC_REGULAR +0.056.

## 4. Root cause of the C1-2023 regression (rule 14)

The corrected input is the more accurate one and it stays in. Measured CAMPD steady-state
operating rates replace eGRID plant-average annual rates. The eGRID averages include start-up and
low-load hours, so for NYISO's low-CF steam fleet they overstate the marginal rate. ST_GAS falls from
16.97 to about 15.7 MMBtu/MWh.

The ST_GAS over-dispatch in 2023 was already at its band edge under the incumbent (+3.61 TWh), with
its heat rates overstated. That means **the pre-F1 heat rate was partly compensating for something
else**. The candidates are the ones the lever queue already names:

- the ST_GAS offer position (nyiso-179 / -184 / -187);
- the reliability-floor and commitment scaffolding. The legs' `legitimacy_diagnostics` flag D-4
  binding in every year, including ST_GAS floor conduct at plants 2480 and 8906 in 2023.

That compensation is now exposed and is the open root-cause item. **It is not closed here by
re-tuning a multiplier**, which rule 1(c) forbids in an input-correction lane.

2022 improves on the same mechanism: ST_GAS −1.62 → −0.86 TWh against an actual that is higher that
year.

## 5. Census deltas (from PRECOMMIT §2)

| year | EIA-860 source | thermal MW | class-table MW |
|---|---|---|---|
| 2022 | canonical → `vintage_2022` | 28,219 → 26,897 | 296 → 51 |
| 2023 | canonical → `vintage_2023` | 28,219 → 26,523 | 296 → 51 |
| 2024 | canonical → `vintage_2024` | 28,226 → 26,556 | 299 → 56 |
| 2025 | canonical → canonical | unchanged | 299 → 299 |

- **2025** keeps 1,487 MW of zero-availability retired coal, including Dunkirk's 234 MW that still
  carries a class-table rate. It is inert.
- **ST_GAS heat rate** falls about 1.2 MMBtu/MWh in every year.
- **Outage inputs are byte-identical to the keeper's.**

## 6. What was not done, and why

- **2019, 2020 and 2021 are DATA-BLOCKED** (PRECOMMIT §5). Both blockers are still true at HEAD:
  - NYISO solar reads the NEISO row of `eia_generation_profiles.parquet`, which starts at 2021 and has
    no producer script;
  - `NYISO_reserve_requirements_<Y>.csv` covers 2022–2025 only, and the armed
    `nyiso_dynamic_reserve_requirements` refuses a static fallback.

  Solving those years on a substituted input would be a different model. They are routed as two
  intakes, not attempted.
- **Short-gas and partial-derate outage windows are not armed.** Both are measured-I for NYISO: the
  partial file has 0 rows, and short-gas carries a non-contaminated headroom census. The
  mechanism-matrix cells were updated with the F2 coverage.
- **No change to heat-rate precedence.** Bethlehem 2539 is the only overlap between measured CC and
  the eGRID steam-collapse rate, and its measured CC row is a CT-only rate that its own per-year guard
  refuses in 6 of 7 years. The steam-collapse rate (6.877) correctly wins.
- **Routed cross-ISO (F1 follow-up):** the pooled-row boundary guard can pass by averaging
  opposite-sign failures.

## 7. Retrievability (rule 34 (e)) and the decision owed (rule 31)

**Where the bytes are:**

- **On this lane's branch, landing on `main` with its PR:**
  - the slim composite bundle (`meta`, `run_config`, `metrics`, `legitimacy_diagnostics`,
    `calibration_attestation`, 20 `hourly/` sidecars);
  - the registry sidecar and run payload;
  - the NYISO bench parts.

  That is enough to re-score, render the dashboard and promote.
- **The four per-year legs, with `dispatch/`:** on this container's disk, gitignored. They **will not
  survive the session**. The shard SHAs above are provenance only. A re-registration from scratch
  would cost a re-solve: about 13–17 min per year across four parallel shards.

**Recommendation: promote, as the structurally correct NYISO backcast.**

- It removes 0.665 TWh of phantom 2022 coal dispatch.
- It prices the whole thermal fleet at year-correct, plant-specific rates, as the owner instructed
  every backcast should.
- It moves no tuned parameter.

**Against it:** C1-2023 ST_GAS moves further out of band (+3.61 → +4.99 TWh). The determination stays
NOT-YET either way, so promotion changes no headline.

If promoted, rule 35 applies: the registered year union is {2022–2025}, which this run covers
exactly, and the incumbent is pruned in the promoting session.

**OWNER QUESTION: promote `2026-09-24-nyiso-r-inputs-860vintage` as the NYISO keeper
(superseding `2026-09-22-nyiso-hydro3-ror-split`)?**
