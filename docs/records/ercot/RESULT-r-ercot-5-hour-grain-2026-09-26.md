# RESULT — R-ERCOT-5: ERCOT CAMPD full-stop windows at their detected hour grain — PROMOTED

**Session:** R-ERCOT-5, 2026-09-25/26.
**New keeper:** `2026-09-25-r-5-hour-grain` (bundle `results/calibration/r_ercot5_hourgrain_span`, 2019–2025).
**Supersedes:** `2026-09-25-r-4-day-guard`, pruned in this session under rule 35.
**Owner ruling (verbatim):** "Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper.."

**Records:**
- `FINDING-r-ercot-5-2019-scarcity-2026-09-25.md` (the defect, zero LP)
- `PRECOMMIT-r-ercot-5-window-hour-grain-2026-09-25.md` (sealed predictions, G-DRIFT, DOF ledger)

## Headline

- **ERCOT stays CALIBRATED on the train tier {2023, 2024, 2025}.** Re-verified with `calibration_verdict --years` on the committed artifacts. **Every year's verdict is identical to the prior keeper.**
- **2019 and 2020 stay NOT-YET, but improve sharply.**
  - 2019 C3a **+99.4 % → +59.8 %**, C3b 1.837 → 1.334.
  - 2020 C3a **+19.0 % → +11.7 %**, C3b 0.457 → 0.361. ST_GAS moves out of the C1 failure list.
  - What remains is the coal offer-conduct object, which is data-blocked (the owner declined the SCED procurement).
- **Reported regressions, at full magnitude and non-downgrading:**
  - C3a moves cheaper in every train year: 2023 −4.6 → −7.5 %, 2024 +0.2 → −5.6 %, 2025 −5.4 → −6.9 %.
  - C3b rises slightly: 0.122 / 0.116 / 0.097 → 0.133 / 0.120 / 0.108.
  - 2024's C3c tail goes 26 → 18 h against 53 actual (the ledgered caveat).
  - Structural reading: the day-granular windows had been removing capacity that CEMS shows running, and that removal was supporting the price level. Removing it exposes the known under-tail (the C3c model-class caveat). Per rule 1, the correction stays in.

## Per year (keeper → arm, official `calibration_verdict`)

| year | C3a | C3b | C3c (>$200 h, model vs RT) | verdict |
|---|---|---|---|---|
| 2019 | +99.4 % → **+59.8 %** | 1.837 → **1.334** | 156 → 119 vs 106 | NOT-YET → NOT-YET |
| 2020 | +19.0 % → **+11.7 %** | 0.457 → **0.361** | 49 → 42 vs 56 | NOT-YET → NOT-YET |
| 2021 | +5.8 % → +2.6 % | 0.137 → 0.136 | 688 → 672 vs 258 (caveat) | CALIBRATED → CALIBRATED |
| 2022 | −5.0 % → −8.1 % | 0.128 → 0.164 | 99 → 98 vs 196 | CALIBRATED → CALIBRATED |
| 2023 | −4.6 % → −7.5 % | 0.122 → 0.133 | 187 → 177 vs 181 | CALIBRATED → CALIBRATED |
| 2024 | +0.2 % → −5.6 % | 0.116 → 0.120 | 26 → 18 vs 53 (caveat) | CALIBRATED → CALIBRATED |
| 2025 | −5.4 % → −6.9 % | 0.097 → 0.108 | 1 → 1 vs 31 (caveat) | CALIBRATED → CALIBRATED |

**Physical outcomes, P1 (keeper → arm):**

| year | LW $/MWh | slack MWh | h > $1k | coal TWh | CC+ST TWh |
|---|---|---|---|---|---|
| 2019 | 93.53 → 74.94 | 6,667 → 5,806 | 72 → 53 | 64.34 → 64.18 | 158.12 → 158.42 |
| 2020 | 30.33 → 28.48 | 0 → 0 | 5 → 5 | 52.22 → 51.70 | 152.59 → 153.25 |
| 2021 | 175.12 → 169.89 | 10,266 → 6,430 | 131 → 123 | 71.44 → 71.74 | 125.85 → 125.82 |
| 2022 | 70.69 → 68.44 | 0 → 0 | 22 → 18 | 76.13 → 76.70 | 139.06 → 138.47 |
| 2023 | 61.37 → 59.47 | 135 → 0 | 62 → 59 | 59.87 → 59.89 | 164.49 → 164.59 |
| 2024 | 31.06 → 29.24 | 641 → 454 | 5 → 2 | 56.58 → 56.84 | 163.45 → 163.45 |
| 2025 | 34.34 → 33.79 | 0 → 0 | 0 → 0 | 64.03 → 64.61 | 157.22 → 156.89 |

## Predictions (PRECOMMIT §4)

- **P1 (every year): met** on price, slack and tail hours; none rises.
  - Coal falls in 2019 (−0.16 TWh) and 2020 (−0.52 TWh) against the predicted 0 to +0.8. **Missed**: the extra gas edge capacity displaces some coal in the low-gas years.
  - Gas moves within ±1.5 TWh: met.
- **P2 (2019): partly met.**
  - Hours > $1k 72 → 53: met.
  - C3a improves (by 39.6 pts, beyond the predicted 3–20 pts) and stays FAIL.
  - C3b stays FAIL: met.
  - Slack falls only 13 %: **missed** the ≥ 20 % prediction.
- **P3 (2020):** C3a moves 7.3 pts toward actual, **beyond** the predicted ≤ 3. It stays FAIL, as predicted. The COAL_PRB gap widens by 0.56 TWh, against the predicted narrowing of < 0.5 TWh.
- **P4 (2021): met.** Slack falls, C3b stays PASS, C3a moves 3.2 pts cheaper.
- **P5 (2022–2025): partly met.**
  - Every year stays CALIBRATED, and the train determination stays CALIBRATED: met.
  - 2024 tail ≤ 26 h: met.
  - The C3a moves exceed the predicted ≤ 4 pts in 2024 (5.8 pts). 2022 moves 3.1 pts, within the bound.
  - 2023 C3b 0.133 ≤ 0.15: met.
- **P6 (C8): met.** The composite regenerated legitimacy diagnostics exit non-zero on the same pre-existing D-4 off-window rows the keeper carries. No C8 forced-share gate changed the determination.

## Promotion

1. **Year union (rule 35(b)):** read before the prune, {2019..2025}. The new keeper covers all seven years.
2. **Composition:** `_r_ercot_compose_span.py --side arm --chp-off` (hour-grain flag uniform on every leg); `stamp_config_partition --check` passes. The per-year `config_partition_overrides` are **byte-equal to the outgoing keeper's**, so no multiplier moved.
3. **Re-keyed:**
   - `keepers/ERCOT.json` (all three partition configs, plus an `r_ercot5_extension` block)
   - `calibration-complete.json`
   - `status/ERCOT.js` (rebuilt)
   - matrix shard (`unit_outage_window_hour_grain` O → **K**)
   - the §5.1 prose header
4. **Checked, in order (rule 35(e)):**
   - `audit_keepers --iso ERCOT` before the prune: E1 passed; E13 flagged only the outgoing run.
   - `prune_iso_runs.py --iso ERCOT --force-uncite` removed `2026-09-25-r-4-day-guard`'s three stores.
   - After the prune: **0 failures, 0 warnings**.
5. **Parity gate:** clean apart from the seven local per-year leg dirs. They are uncommitted and excluded via `.git/info/exclude`, so CI never sees them.

## Where the bytes are (rule 34(e))

- **On `main` once this PR merges:** the registered keeper bundle (rule-15 shape), its registry sidecar and its run payload.
- **Per-year shard legs** at the SHAs below. These are provenance only (rule 33(d)); the four earliest branches were already deleted by the environment when PR #6687 merged.
- **Cost to re-solve any leg:** one ERCOT year, ~15–20 min of LP.

| year | shard commit |
|---|---|
| 2019 | `9da5055db1370eeb8d2eb2692fcfcc48b560902b` |
| 2020 | `bad2a9560f16ba8733815cdab09cb333b6585c1b` |
| 2021 | `3346360b5e052910fe3877b8993c04e01401d8d9` |
| 2022 | `b95dcbb6d2f23db882dd60d156833191c10f67ea` |
| 2023 | `6c66f6e3dce01889616fac824638fa0b49d55de8` |
| 2024 | `731c93c1ed138ec93b7cc5382f93979d2ca088b6` |
| 2025 | `59157159b5f0864fe493bde6641afa01f74c2658` |

**Leftover refs the owner must delete (sessions cannot, rule 33(f)):** `claude/r-ercot5-arm-2021`, `claude/r-ercot5-arm-2023`, `claude/r-ercot5-arm-2024`, plus any of the older families still present: `claude/r-ercot4-arm-{2019..2025}`, `claude/r-ercot-arm-{2019..2025}`, `claude/r-ercot-ctl-{2021..2025}`, `claude/r-ercot2-*`.

## Named next objects

1. **The window × partial double count** (ercot-173/174, matrix R). Against the repaired partial layer, it still holds coal 2–5 TWh/yr below its own same-hour CEMS output (FINDING §5). This is new evidence for a re-test of `ercot_dam_availability_event_cap_unit_scoped`, and it needs the owner's leave to re-open an R cell.
2. **The 2019/2020 coal offer-conduct object.** Data-blocked.
3. **Fleet coverage.** Decker Creek steam units 1–2 (−565 MW, 2019–2021) are missing from the bin sheet. Brazos Valley / Jack Fusco (55357) has an EIA-860 BA of MISO vs NERC region TRE and needs a cited crosswalk. Hidalgo 7762 vs 55545.
