# RESULT — R-ERCOT-6: the ercot-174 unit-scoped window × partial composition, re-tested against the repaired partial layer

**Session:** R-ERCOT-6, 2026-09-26.
**Arm run:** `2026-09-26-r-6-unit-scoped` (bundle `results/calibration/r_ercot6_unitscoped_span`, 2019–2025), registered `--no-prune`.
**Keeper and control:** `2026-09-25-r-5-hour-grain`, unchanged; nothing pruned.
**Owner leave to re-open the R cell:** "Arm B + hour-grain mask".

**Records:**
- `FINDING-r-ercot-6-double-count-retest-2026-09-26.md` (Steps 1–2, zero LP)
- `PRECOMMIT-r-ercot-6-unit-scoped-event-cap-2026-09-26.md` (sealed predictions, G-DRIFT, DOF ledger)

## Headline

- **The train tier flips CALIBRATED → NOT-YET** on C3a alone: 2023 −7.5 → **−10.6 %**, 2024 −5.6 → **−10.3 %** (band ±10 %). 2025 −6.9 → −8.9 % stays inside.
  - C3b, C3c and C8 are unchanged in verdict.
  - This is the risk the PRECOMMIT named. Under its §5 decision rule it is reported at full magnitude, **with no recommendation to revert**.
- **The mechanism did what the census said.**
  - Coal rises in every year, within the sealed in-merit bound (+0.83 to +4.75 TWh), and CC+ST falls against it.
  - Slack falls (2021 6,430 → 4,531 MWh; 2024 454 → 0).
  - The 2023/2024 coal shortfall closes: −2.40 → −1.42 and −1.93 → +0.06 TWh.
  - The 2019/2020 COAL_PRB gaps narrow: −10.77 → −9.10 and −14.12 → −13.34 TWh.
- **The costs.**
  - Coal overshoot grows where coal was already high: 2025 +1.23 → +4.08 TWh, 2022 +4.78 → +8.12 TWh.
  - 2022 flips CALIBRATED → NOT-YET on C1 CC_REGULAR (−10.04 TWh). This is a validation year and does not gate.
  - Every year's price falls 1.2–5.0 %.
- **Root cause of the C3a flip (rule 14).** It is not a defect in the arm; it adds real capacity and lowers the price in years that already read cheap. FINDING §2 shows what makes them cheap: the actual West / South-Central load-zone congestion basis, which the zonal model cannot form and which the ERCOT-117 adjudication closed on the zonal side.
  - Against HB_HUBAVG on the scorer's weights, the arm reads 2023 **−7.3 %** and 2024 **−3.4 %**.
  - The basis is **+2.35 / +2.21 $/MWh**. It is therefore what carries both years across −10 %.
  - The arm's own price move (−2.0 / −1.45 $/MWh) is smaller than that basis in each year.

## Per year (keeper → arm, official `calibration_verdict --years <Y>`)

| year | C3a | C3b | C3c (> $200 h, model vs RT) | C1 fails | verdict |
|---|---|---|---|---|---|
| 2019 | +59.8 → **+53.6 %** | 1.334 → 1.319 | 119 → 117 vs 106 | COAL_PRB −10.77 → −9.10 | NOT-YET → NOT-YET |
| 2020 | +11.7 → **+10.4 %** | 0.361 → 0.365 | 42 → 42 vs 56 | COAL_PRB −14.12 → −13.34 | NOT-YET → NOT-YET |
| 2021 | +2.6 → +1.2 % | 0.136 → 0.145 | caveat | — | CALIBRATED → CALIBRATED |
| 2022 | −8.1 → −9.2 % | 0.164 → 0.174 | 98 → 97 vs 196 (caveat) | **CC_REGULAR −10.04** | CALIBRATED → **NOT-YET** |
| **2023** | −7.5 → **−10.6 % FAIL** | 0.133 → 0.144 | 177 → 171 vs 181 | — | CALIBRATED → **NOT-YET** |
| **2024** | −5.6 → **−10.3 % FAIL** | 0.120 → 0.189 | 18 → 13 vs 53 (caveat) | — | CALIBRATED → **NOT-YET** |
| **2025** | −6.9 → −8.9 % | 0.108 → 0.128 | 1 → 0 vs 31 (caveat) | — | CALIBRATED → CALIBRATED |

- **Train-tier determination {2023, 2024, 2025}:** CALIBRATED → **NOT-YET** (C3a 2023 and 2024).
- **C8:** all 8 legitimacy gates identical to the keeper's.

## Physical outcomes, P1 (keeper → arm)

| year | LW $/MWh | slack MWh | h > $1k | coal TWh | CC+ST TWh | coal vs actual |
|---|---|---|---|---|---|---|
| 2019 | 74.94 → 72.03 (−3.9 %) | 5,806 → 5,806 | 53 → 46 | 64.18 → 66.33 (+2.15) | −1.80 | −14.03 → −11.88 |
| 2020 | 28.48 → 28.14 (−1.2 %) | 0 → 0 | 5 → 5 | 51.70 → 52.53 (+0.83) | −0.57 | −16.96 → −16.13 |
| 2021 | 169.89 → 167.51 (−1.4 %) | 6,430 → 4,531 | 123 → 122 | 71.74 → 76.49 (+4.75) | −4.02 | −3.35 → +1.40 |
| 2022 | 68.44 → 67.62 (−1.2 %) | 0 → 0 | 18 → 18 | 76.70 → 80.05 (+3.34) | −2.93 | +4.78 → +8.12 |
| 2023 | 59.47 → 57.47 (−3.4 %) | 0 → 0 | 59 → 55 | 59.89 → 60.87 (+0.98) | −0.68 | −2.40 → −1.42 |
| 2024 | 29.24 → 27.79 (−5.0 %) | 454 → 0 | 2 → 1 | 56.84 → 58.83 (+1.99) | −1.22 | −1.93 → +0.06 |
| 2025 | 33.79 → 33.06 (−2.2 %) | 0 → 0 | 0 → 0 | 64.61 → 67.46 (+2.85) | −2.02 | +1.23 → +4.08 |

## Predictions (PRECOMMIT §4)

- **P1:**
  - Coal Δ within [+0.2, in-merit]: **met**, all seven years.
  - CC+ST falls by Δcoal ± 0.7: met in four years. **Missed narrowly** in 2021 (gap 0.73), 2024 (0.77) and 2025 (0.83); the remainder displaced CT_PEAKER (−0.36 / −0.54 / −0.58 TWh) and CC_CHP (−0.18 to −0.30 TWh).
- **P2: met.** No price rise; slack and h > $1k never rise.
- **P3:**
  - ≤ 3 % fall in 2020/2022/2025: met.
  - **2023 missed (−3.4 %).**
  - ≤ 8 % fall in 2019/2021/2024: met.
- **P4: missed.** 2023 −10.6 % and 2024 −10.3 % fall outside their sealed ranges ([−10.0, −7.5] and [−8.1, −5.6]). 2025 −8.9 % is within its range.
- **P5: met.**
  - 2023/2024 shortfalls narrow.
  - 2025 and 2022 overshoots grow.
  - 2019/2020 COAL_PRB gaps narrow, by ≤ the in-merit lift.
- **P6: met.** C8 gates are identical.

## Assessment and recommendation

**The rule 1 case holds.**
- The product composition removes the same CAMPD unit's downtime twice, and the census shows 1.0–3.7 TWh/yr of coal capability held below the plants' own same-hour output.
- The arm fixes that at zero new parameters, and every physical prediction on direction held.

**The case against it is real, and not only the C3a flip.**
- 2022 and 2025 coal overshoot grows by 3.3 / 2.9 TWh. So about half the lift (the above-CEMS half, FINDING §1) is restoring capability that the product was, in effect, correctly removing: a different unit's partial downtime at the same plant.
- The unit-scoped rule takes `min()` whenever ANY unit is shared, which drops the other units' plateau at that hour.
- That is the same over-restoration FINDING §1 measured for finer-grain-wins, in a smaller dose.

**The structurally exact construction is neither product nor min().** It would remove each unit's downtime once:
- per unit: the window where the unit is windowed, and its own partial plateau elsewhere;
- this needs the partial layer at **unit** grain inside the cap (`unit_partial_outage_windows`, which the keeper does not arm).

**Recommendation: do not promote this arm.**
- Keep the cell at R, with this test recorded as the evidence for why: it over-restores at shared plants.
- Name the per-unit composition as the successor construction.
- This recommendation rests on the C1 over-restoration evidence (rule 14), **not** on the C3a flip. The C3a flip is the LZ basis object.

**The owner decides** (rules 31/35). If the owner promotes anyway, ERCOT's train determination becomes NOT-YET on C3a 2023/2024.

## Where the bytes are (rule 34(e))

- **On `main` once this PR merges:** the registered arm bundle (rule-15 shape: slim files and hourly sidecars), its registry sidecar and its run payload.
  - `dispatch/` and `floors/` are gitignored as for every registered bundle. They are on this session's local disk only and will not survive the session.
- **Per-year shard legs** (provenance only, rule 33(d); **cost to re-solve any leg ~15–20 min of LP**):

| year | shard commit |
|---|---|
| 2019 | `369e8a8fa8a94d2f62886e14d0dcf0c1e4a12bdf` |
| 2020 | `de0c1d0a6e92b1ebd879e63ae1f33ffbcf7c0000` |
| 2021 | `de2556b338893684137f02904513eb2540446e38` |
| 2022 | `6aecacf5a808de41c2e1e9887eda21fc634b042c` |
| 2023 | `f87df21ae5f3aa369d80e053ddffc48dc4478492` |
| 2024 | `ac7d3770b384034d6523519fd4b9f8890fba3a06` |
| 2025 | `63ea8f891eae6287879ef64cfc1c9f10a0a72524` |

**Leftover refs the owner must delete (sessions cannot, rule 33(f)):** `claude/r-ercot6-arm-{2019,2020,2021,2022,2023,2024,2025}`.

## Owner ruling (2026-09-26)

**"Don't promote (Recommended)."** Actions taken in this session:
- The keeper stays `2026-09-25-r-5-hour-grain`, and ERCOT stays CALIBRATED on the train tier.
- `2026-09-26-r-6-unit-scoped` is pruned through `prune_iso_runs.py --iso ERCOT --force-uncite`, which removed the registry sidecar, run payload and bundle together (rule 15; rule 31 trigger (i)). Git history plus this doc are the record.
- Matrix cell `ercot_dam_availability_event_cap_unit_scoped` goes O → **R**, re-affirmed with this test as evidence.
- The named successor is a per-unit window × partial composition (each unit's downtime removed once). It needs the unit-grain partial layer inside the cap.
- The `unit_outage_active_units(hour_grain=)` consistency repair stays in code. It is default-inert and makes the field the construction it claims to be if it is ever re-armed.
