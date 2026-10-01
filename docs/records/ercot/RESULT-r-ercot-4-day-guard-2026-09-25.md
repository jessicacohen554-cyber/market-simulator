# RESULT — R-ERCOT-4: same-day CEMS guard on the shaped partial-outage layer — PROMOTED

**Session:** R-ERCOT-4, 2026-09-25.
**New keeper:** `2026-09-25-r-4-day-guard` (bundle `results/calibration/r_ercot4_dayguard_span`, 2019–2025).
**Supersedes:** `2026-09-25-r-ercot2-chp-off`, pruned in this session under rule 35.

**Owner rulings (verbatim):**
- Arm: "Yes to arming".
- Promote: "Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper.."

**Records:**
- `FINDING-r-ercot-4-validation-years-2026-09-25.md` (the defect)
- `PRECOMMIT-r-ercot-4-day-guard-2026-09-25.md` (sealed predictions, G-DRIFT)

## Headline

- **ERCOT stays CALIBRATED on the train tier {2023, 2024, 2025}.** This was re-verified from committed artifacts with `calibration_verdict --years`.
- **2021 validation flips NOT-YET → CALIBRATED.** C3b goes 0.203 → **0.137**.
  - October 2021's phantom scarcity event is gone: the model's October mean falls from $154.7 to $86.8, against $52.3 actual.
- **2019 and 2020 stay NOT-YET.** Their object is the coal offer-conduct gap from FINDING-r-ercot-3. The owner declined the 2019–2022 SCED procurement, so it stays data-blocked.

## Per year (keeper → arm, official `calibration_verdict`)

| year | C3a | C3b | C3c (>$200 h, model vs RT) | year verdict |
|---|---|---|---|---|
| 2019 | +101.1 % → +99.4 % | 1.850 → 1.837 | 158 → 156 h vs 106 | NOT-YET → NOT-YET |
| 2020 | +20.1 % → +19.0 % | 0.459 → 0.457 | 51 → 49 h vs 56 | NOT-YET → NOT-YET |
| **2021** | +9.4 % → **+5.8 %** | 0.203 FAIL → **0.137 PASS** | 698 → 688 h vs 258 (caveat) | **NOT-YET → CALIBRATED** |
| 2022 | −1.8 % → −5.0 % | 0.100 → 0.128 | 102 → 99 h vs 196 | CALIBRATED → CALIBRATED |
| 2023 | −3.7 % → −4.6 % | 0.137 → **0.122** | 189 → 187 h vs 181 | CALIBRATED → CALIBRATED |
| 2024 | +1.9 % → +0.2 % | 0.141 → **0.116** | 29 → 26 h vs 53 (PASS → **ledgered caveat**) | CALIBRATED → CALIBRATED |
| 2025 | −5.2 % → −5.4 % | 0.096 → 0.097 | 1 → 1 h vs 31 (caveat) | CALIBRATED → CALIBRATED |

**C1 coal gap:**
- 2019 COAL_PRB −10.73 → −10.54 TWh.
- 2020 −13.75 → −13.56 TWh.
- Both close by < 1.5 TWh, as predicted.

**Physical outcomes, P1:**

| year | P1 slack (MWh) | hours > $1,000 |
|---|---|---|
| 2019 | 7,206 → 6,667 | 74 → 72 |
| 2021 | 14,907 → 10,266 | 142 → 131 |
| 2022 | 0 → 0 | 25 → 22 |
| 2023 | 163 → 135 | 66 → 62 |
| 2024 | 687 → 641 | 8 → 5 |

- Coal energy rises in every year, by 0.17–0.41 TWh.
- Load-weighted price falls in every year.

**Reported regression, at full magnitude:**
- 2024 C3c moves PASS → ledgered caveat: 26 vs 53 tail hours, 0.49×.
- It is non-downgrading (rubric v3.3), and 2025 already carried the same caveat.
- Mechanism: coal the model had wrongly marked unavailable now clears some of 2024's tight hours. That is the direction the physical correction implies.

## Predictions (PRECOMMIT §4)

- **P1 (2021): met.**
  - C3b ≤ 0.17 → 0.137.
  - C3a fell into [+3, +8] % → +5.8 %.
- **P2: met.** Coal up and price down in every year.
- **P3 / P4: met.** 2019/2020 improve and stay FAIL; C1 closes by < 1.5 TWh.
- **P5: met.** 2022–2025 stay CALIBRATED, and every C3a moves ≤ 4 pts toward cheaper (the largest is 2022, at −3.2 pts).
- **P6 (C8): met.** No forced-share gate changed.

## Promotion

1. **Year union (rule 35(b)):** read from both sidecars before the prune, {2019..2025}. The new keeper covers all seven years.
2. **Re-keyed** to the new run:
   - `keepers/ERCOT.json`: all three partition configs, plus an `r_ercot4_extension` block.
   - `calibration-complete.json`.
   - `status/ERCOT.js` rebuilt.
   - Matrix shard re-stamped; `ercot_partial_outage_day_guard` O → **K**.
3. **Checked, in order (rule 35(e)):**
   - `audit_keepers --iso ERCOT` before the prune: E1 passed, and E13 flagged only the outgoing run.
   - `prune_iso_runs.py --iso ERCOT --force-uncite` removed `2026-09-25-r-ercot2-chp-off`'s three stores.
   - `audit_keepers` after the prune: **0 failures, 0 warnings**.
4. **Parity gate:** clean apart from the seven local per-year leg dirs. Those are uncommitted and excluded via `.git/info/exclude` (rule 31's local-only case), so CI never sees them.
5. **Composition:** `stamp_config_partition --check` passes.
   - The per-year `config_partition_overrides` are **byte-equal to the outgoing keeper's**, so no multiplier moved.
   - The only `scenario_config` differences are `ercot_partial_outage_day_guard` and `fleet_zone_vintage_coords`. The latter was added after the keeper was solved and is recorded here at its default of False; G-DRIFT classified it inert.

## Where the bytes are (rule 34(e))

- **On `main` once this PR merges:** the registered keeper bundle in its rule-15 committed shape, the registry sidecar and the run payload.
- **Per-year shard bundles** (`claude/r-ercot4-arm-{2019..2025}`): shard legs at the SHAs below, provenance only. They are transport, not storage (rule 33(f)).

| year | shard commit |
|---|---|
| 2019 | `74205a1be3b461cb74f0d7cae515167736f56817` |
| 2020 | `72ea5ae80efac5e7019406523d298ba22d06fd87` |
| 2021 | `00f18c7554d66c55791385da3a7368d5332ed8f8` |
| 2022 | `852483e74f9853b45809f80e66b39c5f8efabca3` |
| 2023 | `1ee4988d259fc81c625141b67c119b97802a1c44` |
| 2024 | `67b42097ca572e0976b25dafe97bdb6bcf2f0558` |
| 2025 | `40168ad3466528b1f225809bb6eb2f21069a52b3` |

- **Cost to re-solve any leg:** one ERCOT year, about 13–18 min of LP.

## Also found on the way

`derive_partial_outages.py` had been silently broken by COAL-SUB: its `_DETECT_GROUPS` filter lost every coal plateau. It is repaired through `artifact_class`, and the committed 2019–2026 extracts now reproduce line-for-line.
