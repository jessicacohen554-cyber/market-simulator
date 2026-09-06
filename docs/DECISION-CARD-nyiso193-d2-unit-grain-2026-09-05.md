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

---

## 5. ADDENDUM — nyiso-203, 2026-09-06: option (C)'s NYISO row RE-TAKEN on the CURRENT keeper

**The card's §1 table stands on `2026-09-05-nyiso-189-steam-identity`, which has since been
superseded twice.** Session nyiso-203 re-took the measurement on the live keeper
`2026-09-06-nyiso-202-startup-aware`, from an **identity-verified replay** of its own recipe
(`--replay-bundle`; 0 of 157,680 zonal prices differ across 2023–2025 and class energy is
identical to 0.000000 MWh over 14 classes, so these are the keeper's numbers). The replay bundle
was **deleted before merge**; the record is
`results/calibration/_nyiso203_c8_unit_grain.json` and
`docs/FINDING-nyiso203b-unit-grain-and-duct-lever-2026-09-06.md`.

| `ST_GAS` unit-grain forced share | 2023 | 2024 | 2025 | cap |
|---|---:|---:|---:|---:|
| card's keeper (`nyiso-189`) | 0.393 | 0.414 | 0.305 | 0.30 |
| `nyiso-192` arm | 0.369 | 0.403 | 0.287 | 0.30 |
| **CURRENT keeper (`nyiso-202`)** | **0.351** | **0.343** | **0.268** | 0.30 |
| committed plant-grain C8 (PASS) | 0.155 | 0.199 | 0.172 | 0.30 |

**The defect is unchanged in kind and reduced in extent: 2 of 3 years breach, not 3 of 3.** No
other class breaches at unit grain (`CC_REGULAR` 0.097 / 0.099 / 0.098, `CT_PEAKER` 0.000,
`CC_CHP` 0.273 / 0.219 / 0.207 and exempt).

**§2's prediction is CONFIRMED, not merely inferred.** On the keeper's committed
`legitimacy_diagnostics.json`: rule 20 leg **(b) shape `D1.passed` = True**, leg **(a) provenance
`D4.passed` = False**. A unit-grain re-base would fail NYISO `ST_GAS` in 2023 and 2024.

**What is NEW, and it narrows the ruling's cost: leg (a) is failing on almost no energy, and 3 of
its 6 rows are removable through an already-armed, already-adjudicated channel.** Five of the six
D-4 unit-conduct FAIL rows carry ≤ 0.0028 TWh. **In 2024 the ONLY `ST_GAS` failure is Danskammer
2480 at 0.0002 TWh — 0.007 % of that class-year's 3.0294 TWh of unit-grain forced energy.** A
CAMPD census of every failing plant against nyiso-140's criterion
(`scripts/probes/_nyiso203_d4_layup_census.py`) finds **2480 (12/12 zero cells, 2.9 % online)**
and **Roseton 8006 (12/12, 14.6 % online)** qualify **a fortiori** against Port Jefferson 2517
(38.6 % online), the one entry `reliability_floor_plant_exclusions` currently carries — while
Astoria 8906 (0/12, 166 MW median, 70.4 % online) and Saranac 54574 (9/12) do **not**, confirming
nyiso-201 §5. Excluding 2480 + 8006 would leave **zero `ST_GAS` D-4 failures in 2024 and 2025**
and only 2023's 8906 row (0.2271 TWh) — whose limb basis nyiso-203 separately measured **sound as
built** (`docs/FINDING-nyiso203-nyc-persistent-base-basis-2026-09-06.md`), so it is not reachable
by a basis change.

**This addendum arms nothing and recommends no option.** The exclusion entry is a NEW arm owing
its own PREREG, rule-29 screen and span, and the D-4 gate is computed per bundle, so the leg-(a)
consequence must be measured rather than read off the row list. **Option (C)'s NYISO row is
DONE** (this addendum); the other five ISOs remain unmeasured and this lane may not run them
(rule 25 `[R-ISO-SCOPE]`). **The card remains UNRULED.**

### 5.1 Correction to §3: option (C) is **2 of 6 ISOs done, and BOTH breach**

§3 option (A) says *"other ISOs' exposure is unmeasured"*. That understates the record — a
second ISO was already measured by nyiso-192 and its result is committed at
`results/calibration/_nyiso192_c8_unit_grain_NEISO-head-replay.json`:

| ISO | keeper | `ST_GAS` unit grain 2023 / 2024 / 2025 | over the 0.30 cap |
|---|---|---|---|
| NYISO | `2026-09-06-nyiso-202-startup-aware` | 0.351 / **0.343** / 0.268 | **2023, 2024** |
| NEISO | `2026-08-17-neiso-99-joint-p1` | 0.131 / 0.240 / **0.3156** | **2025** |

NEISO's other classes are clear (`CC_REGULAR` ≤0.016, `CT_PEAKER` ≤0.184, `CC_CHP` 0.000), and
its keeper is **unchanged since that measurement was taken**, so the number stands as read.

**The exposure is therefore not a NYISO peculiarity** — it is `ST_GAS` in both ISOs measured so
far, in different years. That raises option (A)'s expected cost and strengthens option (C)'s
case: four ISOs (ERCOT, CAISO, PJM, MISO) remain unmeasured, each needing one keeper replay.
**This lane cannot run them** (rule 25 `[R-ISO-SCOPE]`; the instrument is one file scored for six
ISOs) and this note changes nothing about NEISO — it cites a committed artifact, it does not act
on another ISO's lane.
