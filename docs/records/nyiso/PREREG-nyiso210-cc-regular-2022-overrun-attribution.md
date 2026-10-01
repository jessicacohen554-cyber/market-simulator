# PREREG — nyiso-210: attribute the 2022 touchpoint's CC_REGULAR +4.35 TWh over-run to a BAND, a set of MONTHS and a set of PLANTS, from committed artifacts only

**Session:** nyiso-210, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-3znirv`, off `main` `9a67ecb6`. **Date:** 2026-09-06.
**Keeper: `2026-09-06-nyiso-202-startup-aware` — UNCHANGED and not a candidate for change here.**

**ZERO LP PLANNED.** This is a rule 29 **phase-0** measurement in full: every number below comes
from artifacts already committed to `main`. No solve, no screen, no arm, no bundle, no
registration, no `ScenarioConfig` field, no coefficient, no derive script, no offer curve, no
scorer. If phase 0 returns a negative — and a clean negative is the declared success condition —
no arm reaches a solve and nothing is pre-registered beyond this document.

**THERE ARE STILL NO IN-SAMPLE RUBRIC FAILURES TO FIX.** NYISO's keeper reads **CALIBRATED,
grade 7 of 8, fails 0**, with C3c the lone ledgered, non-downgrading caveat (rubric v3.3/v3.6).
Nothing here is selected because a residual moved, and nothing here is an objective expressed as
a residual (rule 1 `[R-STRUCT]`, rule 23 `[R-FROZEN-DERIVE]`).

**Rule 22, stated:** the 2022 validation rung is **already SPENT** — solved, scored and
registered by nyiso-209 as `2026-09-06-nyiso-209-2022-touchpoint` under the re-declared
`complete` marker. This session **spends nothing**: it reads that run's committed sidecars and
payload. Reading an already-spent year's committed artifacts is touchpoint-loop **step 2**
(diagnose the object 2022 surfaced), not a new spend. **NOTHING IS IDENTIFIED AGAINST 2022**, and
nothing may be: any repair this measurement motivates is built and fitted on **2023–2025 only**
(step 3) and re-tested on 2022 afterwards (step 4). A 2022 number is selection evidence, never a
skill claim, and under rule 30(c) it never moves the ISO's determination.
**2020, 2021 and the locked test are untouched.** No marker byte moves in this session.

---

## 1. The object

The 2022 touchpoint reads **NOT-YET** on three load-bearing criteria, of which C1 is the volume
one: **CC_REGULAR +4.35 TWh / +3.3 pp**. nyiso-209 §2.4 read this as *"the same cell-G
CC_REGULAR sign the keeper carries in-sample, scaled by the 2022 fuel regime"* and named three
candidate owners for it — the NYC persistent-base reliability limb's basis (nyiso-201 §5.3 /
nyiso-203), the unit-grain D-2/C8 re-base (`DECISION-CARD-nyiso193` §5/§5.1), and the winter
downstate locational premium (`INTAKE-SPEC-nyiso156` Leg 2, blocked on identification).

**That reading is an inference, not a measurement.** The over-run has never been decomposed. This
session decomposes it, on committed artifacts, along the three axes that separate the candidate
mechanisms from one another:

| axis | what it separates |
|---|---|
| **BAND** (`committed` / `econ_low` / `econ_high` / `peak`) | forcing vs merit position vs scarcity |
| **MONTH** | a fuel-regime effect (winter-weighted, tracks the 2022 basis) vs an always-on floor (flat) |
| **PLANT** | whether 2022 surfaces the SAME plants the in-sample gap does, or a new one |

## 2. The three candidate mechanisms, and why the band axis is decisive

- **M1 — FORCING.** The commitment bridge (`nyiso_gas_commitment_bridge`, armed) and the
  reliability floors inject a `min_gen` floor of `frac x pmax x availability[t]`. That quantity
  is **independent of fuel price**: same fleet, same frozen coefficients, so its absolute MW in
  2022 should be close to its 2023-2025 level. M1 owns the `committed` band.
- **M2 — MERIT POSITION.** 2022 is a **$6.45 Henry Hub** year against roughly $2.5-3 in
  2023-2025. Every gas unit's marginal cost scales with delivered fuel, so the **absolute
  $/MWh spread** between CC_REGULAR (HR ~7) and ST_GAS (HR ~11) / CT_PEAKER **widens roughly in
  proportion to the gas level**. A model whose CC-vs-ST_GAS offer separation is too wide
  therefore over-dispatches CC **more** in a high-gas year, and does so through the
  **economic** bands. This is the mechanical content of "scaled by the fuel regime".
- **M3 — AVAILABILITY.** If the model simply has more CC_REGULAR capacity available in 2022 than
  reality did, every band lifts roughly proportionally and no band's **share** moves.

The three make **different, checkable** band signatures. That is why the band axis is measured
first and why it, not the residual, decides the verdict.

## 3. Instruments — committed artifacts only

| id | artifact | what it yields |
|---|---|---|
| **I-A** | `results/calibration/nyiso209_2022_touchpoint/hourly/class_band_hourly_2022.parquet` and `results/calibration/nyiso202_startup_aware/hourly/class_band_hourly_{2023,2024,2025}.parquet` | model CC_REGULAR MW by **band x hour**, plus `mw_oil`, P1 pass |
| **I-B** | the same bundles' `class_hourly_<year>.parquet` | model CC_REGULAR class total (band-sum reconciliation) |
| **I-C** | `frontend/data/backcast/bench/NYISO/{2022,2023,2024,2025}.json.gz`, `bench.plants[*].campd` | **measured** plant-hourly MW (base64 byte series x `npl`/100), CC_REGULAR group |
| **I-D** | `frontend/data/backcast/runs/2026-09-06-nyiso-209-2022-touchpoint.js` and `...-nyiso-202-startup-aware.js`, `plants[*].m` | **model** plant-hourly MW, same encoding |

Decoder basis: `scripts/calibration_verdict.py` L2133-2140 (`base64.b64decode(...)` byte series,
`scale = npl / 100.0`). No new decoder is written; the production one's construction is reused.

**Probe:** `scripts/probes/nyiso210_cc_overrun_attribution.py` ->
`results/calibration/_nyiso210_cc_overrun_attribution.json`.

### 3.1 Instrument identity gate — I1

Before any prediction is read, the **payload plant sum** must reconcile with the **parquet class
total** for CC_REGULAR in every one of the four years:

> **I1: `|sum_plants(model) - class_hourly(CC_REGULAR, P1)| / class_hourly <= 0.05`** in each of
> 2022, 2023, 2024, 2025.

`calibration_verdict.py` L2151-2155 shows the two series are not identical by construction (the
payload carries a class "fill" term), so a gap is expected and is reported at full magnitude.

**STOP S1:** if I1 fails in any year, the **plant-grain leg (P4) is WITHHELD** and reported as
not measurable from committed artifacts at that tolerance. The band and month legs (P1/P2/P3),
which read the parquet alone and never touch the payload, **stand regardless** — they do not
depend on the payload at all.

## 4. Predictions — declared BEFORE any value is read

All bands are CC_REGULAR, pass P1, annual TWh. "in-sample mean" = the arithmetic mean of the
keeper's 2023, 2024 and 2025 values for the same quantity. Evaluation order is **P2, then P1,
then P3**; the first to fire is the verdict, and they are disjoint by that order.

### P2 — the prediction that HURTS my preferred answer (M1, forcing)

> **P2 fires iff the `committed` band's 2022 CC_REGULAR energy exceeds its in-sample mean by
> more than +0.5 TWh.**

If P2 fires, the forcing channel is materially **larger** in 2022 than in-sample, M2 is not the
whole story, and the object routes to the reliability-floor / bridge family — the objects
nyiso-203 and `DECISION-CARD-nyiso193` §5 already carry. I state plainly that **this is the
outcome I expect NOT to see**, and that it is the one that would falsify §2's M2 reasoning and
nyiso-209 §2.4's "fuel-regime scaled" reading.

### P1 — my preferred answer (M2, merit position)

> **P1 fires iff P2 does not, AND the combined `econ_low + econ_high` share of CC_REGULAR model
> energy in 2022 exceeds its in-sample mean share by >= 3.0 percentage points.**

Corroborating (reported, not part of the firing test): under M2 the excess should be
**winter-weighted**, tracking the months in which the 2022 downstate gas basis was largest, so
the monthly model-minus-measured gap should be larger in Dec-Mar than in Jun-Sep.

### P3 — the declared third outcome (M3, availability)

> **P3 fires iff neither P2 nor P1 fires, AND the four bands' year-over-year percentage changes
> (2022 vs in-sample mean) have a coefficient of variation below 0.35** — i.e. a roughly
> proportional lift across every band, which is an availability/envelope signature rather than a
> forcing or merit one.

If none of P2, P1, P3 fires, the verdict is **UNRESOLVED at band grain** and is reported as
such — the over-run is then a mixture, and the session's result is the measured mixture plus a
statement that no single named mechanism owns it.

### P4 — plant grain (fires only if I1 passes)

> **P4 fires iff at least two of the top-3 plants by absolute 2022 (model - measured) CC_REGULAR
> energy gap are also in the top-3 by the same gap averaged over 2023-2025.**

P4 firing means 2022 scales the **same** plant-level object the keeper carries in-sample.
**Falsifier (declared):** if a plant that is NOT in the in-sample top-3 carries **more than 30 %**
of the 2022 total gap, 2022 has surfaced a **new** plant-level object, and that plant is named as
the session's handed-forward result instead.

### P5 — dual-fuel (REPORTED, never gated)

> CC_REGULAR `mw_oil` energy in 2022 is **<= 0.05 TWh**.

`dual_fuel_switching` is an armed keeper cell. 2022 carried the span's largest winter
gas-basis / oil-parity exposure, so if the model burns essentially no oil in CC_REGULAR while
measured conduct did, that is a **fourth** named object. Reported at full magnitude either way;
it never fires or blocks a verdict here.

## 5. What this session will NOT do

- **No solve of any kind**, so no screen year, no control, no G-DRIFT-earned control solve, and
  rule 29(c) has nothing to delete. `scripts/probes/nyiso198_rebuild_checks.py --year 2024` is
  run only as an environment sanity check, with `git status --porcelain -uno` confirmed empty.
- **No parameter, coefficient, offer curve, band multiplier or level change** (offer curves are
  owner court under the rule 1 `[R-STRUCT]` carve-out condition (c)).
- **No keeper change, no promotion, no D-5(b) re-key, no marker edit.** Markers are not this
  lane's beyond the D-5(b) duty, and that duty does not attach because no candidate is produced.
- **No DO-NOT-REDO cell re-tested**: no reliability-floor column (membership, fill order, fill
  level, coefficient basis, coefficient identification — nyiso-204..208), not the CH_ST_ev
  window, not the gas-bridge parameter reproduction (nyiso-209), not the duct-burner peaking
  lever (nyiso-198, R). This session **measures** where the 2022 energy sits; it does not
  re-adjudicate any of them.
- **No ruling on the five pending owner cards** ((i) nyiso-206, (ii) nyiso-207, (iii) nyiso-203
  §6, (iv) `DECISION-CARD-nyiso193` §5/§5.1, (v) nyiso-208). None is this lane's. Per (v), the
  2022 CAMPD conduct is read **only** through the already-committed bench artifact of an
  already-scored year — never to identify a coefficient.
- **No other ISO's shard, keeper, board or lane touched** (rule 25 `[R-ISO-SCOPE]`).

## 6. Deliverable

The measured band / month / plant attribution of the 2022 CC_REGULAR over-run, the P1-P5 verdicts
as declared above, this PREREG, a FINDING, the machine record, and NYISO's matrix shard cell
update in the same session (rule 28(b)). **A clean negative — including "UNRESOLVED at band
grain" — is a full result and is reported as one.**

---

*(nyiso-210, pre-registered 2026-09-06 before any value was read. Committed and pushed before the
probe was written.)*
