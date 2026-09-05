# DECISION CARD — nyiso-193 (scorer-lane proposal): re-base the D-2 forced-energy row and the C8 gate to UNIT grain across all six ISOs?

**For:** the owner and the scorer / governance lane. **From:** session nyiso-193, NYISO
`backcast-calibration` lane, 2026-09-05. **Zero solve; no scorer edit; nothing armed or
re-scored.** The NYISO lane may not change `scripts/legitimacy_diagnostics.py` (code-generic
across six ISOs; rule 25) — this card carries the measurement and asks for the ruling.

## 1. The defect (nyiso-181 §6, measured on the current keeper at nyiso-192)

`aggregate_floors_by_plant` tests the PLANT total dispatch against the PLANT total floor. A
unit pinned at its own floor inside a plant whose other units run freely is above the plant
floor in aggregate and its forced energy VANISHES from D-2 and therefore from C8. Measured
with D-2's own `at_floor_mask` and tolerances on the bundles' `unit_hourly` + `floors`
(`scripts/probes/nyiso192_c8_unit_grain.py`):

| bundle | class | committed plant-grain C8 (2023 / 2024 / 2025) | unit-grain forced share | cap |
|---|---|---|---|---|
| keeper `2026-09-05-nyiso-189-steam-identity` | `ST_GAS` | 0.197 / 0.236 / 0.183 PASS | **0.393 / 0.414 / 0.305** | 0.30 |
| same | `CC_REGULAR` | 0.027 / 0.009 / 0.012 | 0.123 / 0.119 / 0.113 | 0.30 |
| arm `2026-09-05-nyiso-192-astoria-panel` | `ST_GAS` | 0.171 / 0.238 / 0.186 PASS | **0.369 / 0.403 / 0.287** | 0.30 |

Every keeper `ST_GAS` year is above the cap at unit grain. Ravenswood is the mechanism made
visible: eight steam tranches at floor beside seven free-running CC units.

## 2. Why it is the owner's ruling, not a lane fix

* The instrument is one file scored for all six ISOs; re-basing it moves every ISO's
  protective gate at once (rule 25; the miso-170/171 `FloorClassMatrix` repair went through
  the same door).
* NYISO's `complete` + `frontier` (Q38, Q39) and its §2.1b campaign authorisation (Q45) all
  stand on a CALIBRATED determination whose C8 PASS the committed scorer's own mask does not
  reproduce at unit grain. Left unruled, that is the nyiso-130 / Q5-W pattern in waiting.
* Rule 20 already says what happens on a breach: a material class above its cap is NOT an
  automatic fail — it escalates to a conditional pass on **D-4 off-window provenance + D-1
  shape**. NYISO's D-4 currently reads `passed: false` on the per-unit conduct rider
  (nyiso-181 §6.1), so a re-based C8 would most likely FAIL for NYISO unless the rider is
  grounded.

## 3. Options

* **(A) Re-base D-2 / C8 to unit grain** (scorer lane): `aggregate_floors_by_plant` keeps the
  plant LABEL for the denominator and attributes at-floor energy per UNIT; every keeper
  re-scores in place (scorer-only, no solve); ISOs that breach go through rule 20's
  provenance + shape path. Cost: a cross-ISO re-score whose NYISO outcome is predictable
  (above); other ISOs' exposure is unmeasured and must be measured first with the same probe.
* **(B) Keep the plant-grain instrument by explicit ruling**, recorded where the rubric lives,
  with the unit-grain number REPORTED alongside C8 on every determination (a reported-only
  stream, the C5a pattern). Honest and cheap; leaves the cap's letter and its measurement
  disagreeing.
* **(C) Measure first**: run `nyiso192_c8_unit_grain.py` on every ISO's keeper bundle (needs
  a same-HEAD replay where `unit_hourly` / `floors` are not on disk — under rule 29(b) the
  keeper's committed bundle is the control, so this is one replay per ISO), then choose A or
  B on the six numbers. **Recommended.**

## 4. What the NYISO lane will do with the ruling

(A): re-verify the NYISO keeper and, if C8 fails, ground the `ST_GAS` floors' D-4 window
(the `D4_WINDOWS` entry rule 20 names) before any promotion talk; (B): add the reported
number to the keeper's determination note; (C): supply the NYISO number (done) and stand by.
