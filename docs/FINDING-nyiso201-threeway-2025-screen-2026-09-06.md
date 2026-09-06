# FINDING nyiso-201 — the two gate constructions nyiso-200 handed forward were BOTH mis-built and BOTH clear when corrected; the three-way arm nevertheless STOPS on 2025 at the risk this lane named before the solve — **C3a −6.9 % → −11.7 %, out of band**. And the NYC persistent-base membership review, never done before, answers Astoria 8906 **NEGATIVE from source data**.

**Session:** nyiso-201 (`claude/nyiso-201-backcast-calibration-dqn95r`), 2026-09-06.
**Keeper at open and at close: `2026-09-06-nyiso-196-extract-basis`** — CALIBRATED, grade 7 of 8,
fails 0, C3c the lone ledgered caveat. **UNCHANGED.**
**Control:** the keeper's committed bundle (rule 29(b) form 4; G-DRIFT §2.3, re-validated
empirically at this HEAD).
**Pre-registration:** `results/calibration/PREREG-nyiso201-threeway-2025-screen.md`, pushed with
**zero solves** before the arm was run.
**Machine record:** `results/calibration/_nyiso201_screen_gates_a3_2025.json` — every number this
document cites. **ONE LP spent** (a one-year rule-29 screen, ~4 min); the bundle is deleted before
merge (29(c)) and git history is the record.

---

## 1. The result in one paragraph

**The gates nyiso-200 stopped on were the wrong gates, and correcting them was worth doing: both
clear.** Gate (a) — forced energy at dark-meter plants instead of a D-4 failure-row COUNT — reads
**0.0010 → 0.0000 TWh**, i.e. the arm *removes* the keeper's only dark-meter conviction (plant 8006)
and the screen's D-4 failure list is **empty**. Gate (b) — "anchored on a dropped run" instead of
"zero floor" — clears at both named plants: 7314 carries 803 floored unit-hours and 50978 carries
231, reported at full magnitude, and the detector's new per-plant census shows both plants have
**kept** runs (120 of 333, 47 of 86), so no floor anchors on a run the screen dropped, and neither
plant draws a D-4 conviction. S-1, S-2 and G-ENGAGE all pass; the run screen is live and large in
2025 too (951 of 1,528 CC runs, 355 of 455 steam runs dropped; bridge forced volume **0.5701 →
0.1540 TWh**). **And the arm dies anyway, on the one risk this lane named in writing before the
solve: C3a-2025 goes −6.9 % → −11.7 %, outside the ±10 % band.** The PREREG says a C3a FAIL is a
STOP, full stop; it is, the span was not spent, and nothing is registered or promoted. §4 states
the stop at full magnitude. §5 is the second object, done at zero LP: the NYC persistent-base limb's
first-ever membership review answers **8906 does not qualify, and the criterion is not the thing to
look at either** — and names what the object actually is.

## 2. What was measured before the LP

**2.1 The screen year, and why choosing 2025 is not residual-driven year selection.** Rule 29 names
the screen year by the mechanism's own footprint. That year is **2023** (bridge bound 1.0034 TWh,
1.8× either other year) and **nyiso-200 already spent it**; its numbers stand and were not re-solved
or re-read. 2025 is the *other* year nyiso-200 §4 named **before any solve**, and it is the harder
of the two. This session inherited that pre-registration and took the more adverse year, which is
the opposite of the hazard the rule guards.

**2.2 How 2025 is SCORED — declared in the PREREG because it decides which gates have teeth.**
On the preliminary EIA-923 vintage, **every C1 class cell is SKIPPED** in 2025 (`CC_REGULAR` 11/20
plants missing, `CC_CHP` 12/17, `CT_PEAKER` 17/20, `ST_GAS` 3/10, `ST_CHP` 2/6) **and the C2 gas
family is SKIPPED too** (`-1.0%`). No volume criterion is gateable in 2025. What binds is **C3a**
(keeper −6.9 % against ±10 %: **3.1 pp of downward room**) and **C3b** (0.154 against ≤0.20). This
was written down before the solve, so the C3a stop below is a pre-named outcome, not a discovered
one.

**2.3 G-DRIFT (rule 29(b)), empirical, not hunk-reading.** The committed keeper-sha probe record
`_nyiso198_rebuild_checks_2024.json` (per-plant / per-band LP `pmax`, 42 leaves) re-run at this HEAD
reproduces **0 of 42 differing leaves, max |Δ| 0.0**, its own `VERDICT` field included. Form 4 is
valid: the keeper's committed bundle is the control and **no control solve was spent**.

**2.4 The one code change is diagnostics-only.** To make gate (b)'s identity leg *falsifiable*
rather than asserted from the code path, the detector now records a per-unit run census
(`detected`/`kept`/`dropped`/`dropped_hours`) and the NYISO consumer rolls it up per plant into one
log line. The floor arithmetic never reads it — `runs` is rebound to `kept_runs` before every leg
exactly as before. Guarded by two new tests (a dropped-run unit reads `kept: 0` and floors nothing;
a supplied stats dict changes no floor, byte-identical). 52 pass in the NYISO bridge file, 76 in
`test_commitment.py`. Five test failures at clean HEAD (`test_default_cache_key_unmoved`, four
`test_ff_readiness_battery`) are **pre-existing**, verified by `git stash`, and are not this
session's.

## 3. The screen — every gate, as pre-registered

Arm: `nyiso_gas_bridge_startup_aware` + `nyiso_ct_peaker_bands_measured` + `cc_duct_peaking_row_scoped`
over the keeper recipe, 2025, one LP. **G-DOF +0** — no free parameter is selected anywhere.

**Census (the mechanism's own arithmetic, logged):** `gas_cc` **951 of 1,528** P0 runs dropped as
unable to repay a start (5,336 P0 online hours, 13 units); `gas_cc_state` **68 of 136** (354 h,
3 units); `gas_st` **355 of 455** (18,530 h, 7 units). Per-plant census over 19 plants.

| gate | reading | verdict |
|---|---|---|
| **S-1** direction / bound | `CT_PEAKER` **+0.858 TWh**, rises, inside the CT arm's own 2.1417 TWh bound | **pass** |
| **S-2** confinement | gas-family total **+0.044 TWh** ≤ the CT gain; only non-gas move is import **−0.075** | **pass** |
| **(a)** C8/D-4 dark-meter forced energy *(corrected)* | keeper **0.0010** → screen **0.0000 TWh** (−0.0010); the keeper's sole dark plant 8006 drops to zero; screen D-4 failure list **empty**; D-2 adds no failure | **pass** |
| **(b)** named plants 7314 / 50978 *(corrected)* | 7314 **803 unit-h / 16.14 GWh**, census 333 detected / **120 kept** / 213 dropped; 50978 **231 unit-h / 9.09 GWh**, census 86 / **47 kept** / 39; no floor with zero kept runs; **no D-4 conviction at either** (both `ct_only`-restored by the span guard, which named 9 plants incl. 7314 and 50978) | **pass** |
| **G-ENGAGE** | all three census legs present in the log | **pass** |
| **(c)** C3a-2025 — the named risk | **PASS → FAIL. −6.9 % → −11.7 %** (model 61.84 → 58.69 vs actual 66.43) | **STOP** |
| (c) C3b | NRMSE 0.154 → 0.154, PASS | pass |
| **(d)** no load-bearing flip | zero C1 flips, zero C2 flips — **vacuous in 2025**, every cell SKIPPED (§2.2) | pass (vacuous) |

**Bridge volume:** 0.5701 → **0.1540 TWh** (`CC_REGULAR` 0.4080 → 0.1468, `ST_GAS` 0.1621 →
0.0072), a fall of 0.4161 inside the 0.5701 bound, no rise. The repair is live and large in 2025,
as it was in 2023.

## 4. The stop, at full magnitude

**C3a-2025: −6.9 % → −11.7 %.** System mean price 58.86 → **55.72 $/MWh** (p95 125.52 → 117.20;
hours > $300 unchanged at 4). The band is ±10 % and the keeper had 3.1 pp of room; the arm spends
4.8 pp of it. This is the sum the PREREG said was unknown in sign: the CT arm alone read −9.1 % on
2025 (nyiso-199), the duct arm alone −10.3 % on the span (nyiso-198), and the run screen alone
*raises* price (+1.1 pp C3a in 2023). **The two price-lowering arms dominate the run screen's
price-raising one, and the sum lands outside the band.** Under the PREREG that is a STOP, full
stop, and the remaining years were not spent.

**The volume picture in 2025, reported and NOT gated (§2.2) and NOT judged (rule 1):**

| class | actual | keeper | arm | keeper err | arm err | |
|---|---|---|---|---|---|---|
| `CT_PEAKER` | 2.851 | 1.356 | 2.214 | −1.495 | **−0.637** | toward |
| `ST_CHP` | 0.800 | 1.440 | 1.322 | +0.640 | +0.522 | toward |
| `CC_REGULAR` | 33.544 | 35.102 | 36.098 | +1.558 | **+2.554** | away |
| `CC_CHP` | 16.962 | 20.344 | 20.440 | +3.382 | +3.478 | away |
| `ST_GAS` | 13.712 | 9.606 | 8.046 | −4.106 | **−5.666** | away |

Two things must be said about this table so it is not over-read in either direction. **(i)** These
actuals are the preliminary vintage that is *why* C1 is skipped in 2025 — 3 of 10 `ST_GAS` plants
and 11 of 20 `CC_REGULAR` plants are missing — so the "err" columns are not a scored result and no
verdict rests on them. **(ii)** The direction is nonetheless **materially different from 2023**,
where the same arm moved `ST_GAS` +1.81 → +0.46 and `CT_PEAKER` −1.69 → −0.99 (both toward) with
`CC_REGULAR` the lone class moving away. In 2025 only `CT_PEAKER` moves toward and `ST_GAS` moves
1.56 TWh further below an already −4.1 TWh actual. **The single-year structural story from 2023 does
not reproduce on 2025** — which is precisely what a screen on the exposed year exists to discover,
and it is a finding independent of the C3a stop.

**The promotion question, put and answered.** The PREREG named `CC_REGULAR` before the solve as the
class that moves away, under the owner's standing formula (*"if structural integrity improves but
gates regress that may still be a keeper"*). The formula is permissive but it has nothing to admit
here, for a reason stronger than nyiso-200's: **C3a is a LOAD-BEARING criterion and its failure is
not ledgerable.** The C3c standing rule reclassifies only a *lone* C3c failure, and the v3.0
fail-closed guard refuses `model-class` on C1/C2/C3a/C3b outright. A span carrying a C3a FAIL on
2025 therefore reads **NOT-YET**, and promoting it would **decertify NYISO**. "Structural integrity
improves but gates regress" is not the same thing as a determination going from CALIBRATED to
NOT-YET, and this session does not read the formula as reaching that. **No span was solved, nothing
is registered, the keeper is unchanged.**

## 5. Second object (zero LP): the NYC persistent-base membership review — Astoria 8906 answers NEGATIVE

The nyiso-200 run screen removed the bridge floor at Astoria 8906 and the reliability floor beneath
it absorbed the hours (the floor under the floor, rule 19 `[R-ONE-MECH]`). The handoff asked whether
8906's conduct qualifies it for `reliability_floor_plant_exclusions`, **from source data only**
(rule 23), never a residual. It does not, and this is the first time the question has been asked:
the calibration log records that *"the NYC persistent-base limb has never had a membership
review"*.

**5.1 The criterion, and where 8906 sits on it.** The exclusion criterion is nyiso-140's, verbatim —
*"median CF exactly 0.000 in every hour block of every year"*, i.e. **18 of 18** (year, 4-hour block)
cells at a zero median. The per-cell quantifier is what makes it a lay-up test rather than a
low-capacity-factor test: a pooled median of zero also catches ordinary cyclers, which are the
population a bridge exists to serve. From the committed NYISO population census (EPA CAMPD
unit-level hourly grossLoad, units summed to one plant series):

| plant | zero cells | pooled median MW | online share | laid up |
|---|---|---|---|---|
| Danskammer 2480, Bowline 2625, Roseton 8006, Carlson 2682, … (12 plants) | **18/18** | 0.0 | 0.01–0.29 | **True** |
| Carr Street **50978** | 16/18 | 0.0 | 0.345 | False |
| Port Jefferson 2517 | 15/18 | 0.0 | 0.375 | False |
| Flynn **7314** | 14/18 | 0.0 | 0.413 | False |
| Saranac 54574 | 12/18 | 0.0 | 0.426 | False |
| Athens 55405 | 6/18 | 330.0 | 0.583 | False |
| **Astoria 8906** | **0/18** | **166.0** | **0.667** | **False** |
| Arthur Kill 2490, Ravenswood 2500, Northport 2516, Bethlehem 2539, … | 0/18 | 101–893 | 0.81–0.99 | False |

**8906 is 0 of 18 — the maximum possible distance from qualifying.** It is not near the boundary
(the nearest non-qualifier is 50978 at 16/18); it sits in the same bucket as Ravenswood and
Northport. Its median hour produces **166 MW** and it is online **two-thirds of the year**.

**5.2 So the criterion is not the thing to look at either.** Widening the test far enough to admit
a 67 %-online plant with a 166 MW median hour would not be a lay-up test at all: it would dissolve
the exact lay-up/cycler distinction nyiso-140 established, and at 0/18 it would have to reach the
whole 0/18 bucket, i.e. Arthur Kill, Ravenswood, Northport and Bethlehem — the plants that same
analysis proved **do** run a genuine persistent baseline. Excluding 8906 by name instead would be
the per-plant list typed to make a gate pass that rule 1 `[R-STRUCT]` and rule 14 `[R-ACCURATE]`
forbid, and that nyiso-144 already refused for 7314. **The membership channel is the wrong
instrument for this plant, and the answer is a clean negative.**

**5.3 What the object actually is.** The NYC `ST_GAS` persistent base is one limb: `tmax` at
**−50 °C** (so it binds in all 8,760 hours), `floor_pct` **0.175**, `distribution` **`pro_rata`**,
`exclude_plant_codes` **empty** — and across all 46 NYISO limbs the exclusion channel carries
**exactly one** entry (Long_Island `ST_GAS` excludes 2517), so the keeper's armed
`reliability_floor_plant_exclusions=True` arms **nothing at all on the NYC limb**. Its
`threshold_basis` is a **fleet-aggregate** when-available cool-day CF p25, and it is applied **per
unit**. That is the identical basis divergence nyiso-140 diagnosed on Long_Island — *identified on a
fleet aggregate, applied per unit* — and on NYC it has never been checked. The NYC fleet spans
0.667 (8906) to 0.956 (Northport) online, so a single p25 aggregate held pro-rata in every hour
necessarily floors the lowest-duty member in hours its own meter says it is off.

**5.4 The measurement that makes it concrete, and it is year-dependent.** At 8906 in **2025**, the
arm removes the bridge row entirely (686 → 0 binding hours) and the reliability row grows **3,512 →
4,834 h** and **0.2520 → 0.3061 TWh**, so the plant's total forced energy **RISES 0.2725 → 0.3061
TWh**. In **2023** the same composition ran the other way (0.2501 → 0.2282 TWh, a fall). The
D-4 rider convicts in neither 2025 case — 8906's measured median over its binding hours is
**80.976 MW**, zero-share 0.143 (keeper) / 0.172 (arm), both **pass** — so the 2023 conviction that
stopped nyiso-200's A1 was a **year-specific** tip, not a standing property of the plant.
**Astoria is a cycler the NYC persistent base holds up in its off hours; it is not a mothballed
boiler, and no plant list fixes it.**

## 6. Disposition

**Keeper UNCHANGED: `2026-09-06-nyiso-196-extract-basis`. Nothing registered. No span solved.
Nothing promoted.** The arm was killed at its pre-registered C3a gate on the screen year, rule 29
says the remaining years are then never spent, and this session does not re-read its own gates after
they fired — selecting the gate an arm passes is the hazard the rule exists for. The screen bundle
is deleted before merge (29(c)); every number it produced is in
`_nyiso201_screen_gates_a3_2025.json` and in this document.

Unlike nyiso-200, this stop is **not** a gate-construction artifact. Both constructions nyiso-200
handed forward were corrected here and both cleared; what stopped the arm is a load-bearing
criterion leaving its band on the year the lane had never measured, exactly as the PREREG named the
risk. **The three-way pairing is now adjudicated on both of the years nyiso-200 pre-registered, and
it does not survive 2025.**

## 7. Handed forward

1. **The pairing is REFUTED as a joint arm on the training span, and its two partners stay `R`.**
   2023 was its best case and 2025 refuses it: −11.7 % C3a, plus `ST_GAS` moving 1.56 TWh further
   from an already −4.1 TWh actual. Do not re-screen the same three-way arm hoping for a different
   year; both pre-registered screen years are now spent.
2. **`nyiso_gas_bridge_startup_aware` ALONE remains the live candidate, and its 2025 screen has
   still never been spent.** It is the only one of the three with no price-lowering signature — it
   *raises* C3a (+1.1 pp in 2023) — and on 2023 alone it read zero C1 flips, C8 clean, the bridge
   two-thirds smaller and `CC_REGULAR` closer to its actual. nyiso-200's A1 was stopped by the
   failure-row COUNT gate this session retired; under gate (a) as corrected, A1-2023's reading
   (8906 total forcing 0.2501 → 0.2282 TWh, a FALL) **passes**. A next session should screen A1 on
   2025 under this PREREG's gates, and that is the shortest path left to a keeper change.
3. **The NYC persistent-base limb's BASIS, not its membership** (§5.3). The membership question is
   answered and closed negative. The open object is nyiso-140's Long_Island analysis repeated for
   NYC: whether a fleet-aggregate when-available cool-day CF p25 applied `pro_rata` and 24 h is the
   right basis for a fleet spanning 0.667–0.956 online. On Long_Island the two basis errors
   cancelled and `floor_pct` was unchanged with zero DOF; the NYC analogue has never been run. It is
   source-data-only and zero-LP up to the A/B.
4. **A note for every lane, not just this one (rule 25 scope respected — this is method, not a
   verdict transfer):** a D-4 **failure-row count** is not a forcing measure wherever two mechanisms
   floor the same plant and compose by maximum. The like-for-like measure is forced energy per
   dark-meter plant, and `scripts/probes/nyiso201_screen_gates.py::dark_plant_forced` implements it;
   it reproduces nyiso-200 §5.1's published 2023 number (0.2515 TWh) exactly, which is the check
   that it is that section's construction and not a new one.

---

*(nyiso-201, 2026-09-06. ONE solve, a one-year rule-29 screen, deleted before merge (29(c)).
Nothing registered, nothing promoted, no span spent. Keeper unchanged:
`2026-09-06-nyiso-196-extract-basis`.)*
