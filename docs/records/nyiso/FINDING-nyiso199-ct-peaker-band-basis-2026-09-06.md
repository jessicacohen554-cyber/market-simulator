# FINDING nyiso-199 — the `CC_REGULAR` vs `ST_GAS` / `CT_PEAKER` merit order resolves against the LP's own bounds with **no solve**: `ST_GAS` is a CLOSED cell, and `CT_PEAKER` is **100.0 % offer position in every year**, with the object localised to two bands the config's own comments call a de-leak placeholder and a start hurdle — both of which carry NYISO's own measured counterpart, already registered.

**Session:** nyiso-199 (`claude/nyiso-merit-order-calibration-n9rs17`), 2026-09-06.
**Keeper: UNCHANGED — `2026-09-06-nyiso-196-extract-basis`** (CALIBRATED, grade 7 of 8, fails 0,
C3c the lone ledgered caveat). **Nothing promoted, nothing registered.**
**Solves run: ZERO.** Every number below is from the keeper's committed artifacts plus two
`fleet_only` rebuilds (no LP, ~90 s each) — rule 29 `[R-SCREEN]` step 0.
**Control:** the keeper's committed bundle (rule 29(b) form 4). **G-DRIFT validated empirically,
not by reading the diff** — see §6.
**Machine records:** `_nyiso199_meritorder_phase0.json`, `_nyiso199_zone_offer_census.json`,
`_nyiso199_ct_band_basis_phase0.json`; probes `scripts/probes/nyiso199_*.py`.

---

## 1. The result in one paragraph

nyiso-198 handed forward the `CC_REGULAR` vs `ST_GAS` / `CT_PEAKER` merit order and instructed
that phase 0 start "at the bound that binds, not at the residual". Decomposed against
`pmin ≤ P ≤ pmax·availability` on the keeper's own committed dispatch, the two classes give
**opposite answers and only one of them is live.** `ST_GAS`'s deficit is 73 / 88 / 84 % interior,
and its interior half is the **already-adjudicated `scuc_load_pocket_commitment` cell (G)** —
nyiso-192 measured that "the market's 3.0 TWh of NYC steam in 2024 is out-of-market commitment"
and nyiso-97 §5 forbids identifying the pocket requirement from unit conduct, which is the only
instrument this lane has. **`ST_GAS` is closed; do not re-open it as a merit lever.** `CT_PEAKER`
is the live object and it is unambiguous: **100.0 % of its deficit is INTERIOR in all three
years** — 0.0 % at the availability envelope, 0.0 % at a floor, and the class carries **no
commitment mechanism at all** (forced floor 0.000 TWh, D-2 0.0 %). The model runs it at
**2.04 / 2.03 / 7.03 % of its own available capacity against a meter of 11.16 / 10.85 / 14.29 %**.
Inside the offer, the object localises to two bands, and the config's own comments name both:
`econ_low`/`econ_high` = **1.0**, which `_NYISO_OFFER_CURVE` calls a de-leak placeholder with an
**OPEN ROOT CAUSE** ("NYISO carries no independent CT part-load heat-rate spread yet … a
NYISO-grounded CT econ ramp (CAMPD CT heat-rate spread) is a later disciplined-calibration item");
and `committed` = **1.35**, which the same comment calls "the start hurdle … a ~$25/MWh fixed
commitment margin" — **on a keeper that already has `tranche_startup_amortization = True`**, so
P1's own identified startup markup ($20/MW, NREL SR-5500-55433, ÷ P0 run length) is charged to the
same tranche. That is a rule 19 `[R-ONE-MECH]` double count, measured on the keeper's own recipe.
Both bands carry NYISO's own measured counterpart, already registered and unused:
`phys_committed` 0.843, `phys_econ_low` 0.661, `phys_econ_high` 0.658
(`nyiso_campd_marginal_hr_summary.csv` p50s, n = 70). Substituting them on a **measurement-only**
rebuild moves **exactly 101 / 103 / 103 rows, every one of them `CT_PEAKER` econ or committed,
zero rows in any other class, band or ISO, and zero capacity**, and the delta is a
**fuel-invariant fixed adder — −$17.41/MWh committed and −$13.68/MWh econ, identical to the cent
in all three years across gas at very different levels.** The repair is reachable
(in-the-money CT capacity 94–276 → 342–520 MW; bound 0.82–2.41 → 3.00–4.56 TWh, bracketing the
1.91–2.85 TWh meter) and its price exposure is **stated in advance and is the session's one real
risk**: −2.75 / −2.40 / −2.74 % on the same-weights crossing indicator, which lands C3a-2025 near
**−9.6 % against a ±10 % band**. **The arm is NOT built and NOT solved**: it is an
`offer_curve_by_group` band substitution, which this lane's brief gates on an explicit owner
ruling. §7 states the ruling question, and `PREREG-nyiso199-ct-peaker-measured-bands-screen.md`
is written and pushed so the screen can execute unchanged if the ruling comes.

## 2. Phase 0a — the deficit, against the LP's own bounds

Every dispatched MW sits between `pmin` and `pmax·availability`, so in each hour where the meter
runs a class above the model, the class sits at its envelope (availability / capacity scope), at
its forced floor, or interior (offer position). Measured on the keeper's committed `class_hourly`
against the bench's own plant→class meter, on the LP's own reconstructed envelope:

| class | year | model TWh | CAMPD TWh | EIA-923 TWh | model CF | meter CF | **at envelope** | at floor | **INTERIOR** |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **`CT_PEAKER`** | 2023 | 0.421 | 2.301 | 2.114 | **2.04 %** | 11.16 % | **0.0 %** | **0.0 %** | **100.0 %** |
| | 2024 | 0.392 | 2.096 | 1.911 | **2.03 %** | 10.85 % | **0.0 %** | **0.0 %** | **100.0 %** |
| | 2025 | 1.356 | 2.757 | 2.851 | **7.03 %** | 14.29 % | **0.0 %** | **0.0 %** | **100.0 %** |
| `ST_GAS` | 2023 | 9.952 | 8.912 | 8.141 | 34.4 % | 30.8 % | 0.0 % | 27.0 % | 73.0 % |
| | 2024 | 8.739 | 10.662 | 9.913 | 35.3 % | 43.1 % | 0.0 % | 11.7 % | 88.2 % |
| | 2025 | 9.606 | 13.737 | 13.712 | 37.8 % | 54.0 % | 0.0 % | 16.3 % | 83.7 % |
| `CC_REGULAR` | 2024 | 37.067 | 36.440 | 34.060 | 85.2 % | 83.7 % | 2.0 % | 0.0 % | 98.0 % |

CF is of the LP's **own** available capacity (`Σ pmax·availability`), so the availability limb is
tested rather than assumed. The `CT_PEAKER` row is as clean as this decomposition gets: the class
is never capacity-bound, never floored, and runs at a fifth of its meter's utilisation.

**The revealed supply curve (2024), model and meter on the same denominator**, is the shape that
says the same thing without any residual in it:

| zonal LMP | hours | `CC_REGULAR` model/meter | `ST_GAS` model/meter | **`CT_PEAKER` model/meter** |
|---|---:|---|---|---|
| $25–30 | 2,058 | 81.0 / 74.9 | 21.2 / 29.9 | **0.00 / 1.24** |
| $30–35 | 2,206 | 86.4 / 85.2 | 23.0 / 34.5 | **0.02 / 3.98** |
| $35–40 | 1,653 | 87.8 / 89.2 | 30.2 / 40.6 | **0.20 / 8.97** |
| $40–50 | 1,256 | 89.8 / 91.8 | 45.1 / 48.4 | **0.69 / 17.75** |
| $50–65 | 853 | 89.6 / 86.6 | 59.7 / 62.8 | **7.33 / 33.53** |

The market brings ~9 % of its available CT fleet on by $37 and ~18 % by $45. The model brings on
essentially none below $50. `ST_GAS`'s gap, by contrast, is concentrated **below** $40 — at a
price no plausible steam offer clears, which is the out-of-market-commitment signature the
`scuc_load_pocket_commitment` cell already carries.

## 3. Phase 0b — where the object is, inside the offer

Class offers decomposed on the LP's own arrays (`mc_base`, `fuel_prices`, `heat_rate`, `vom`,
`emission_rate` × the measured RGGI price), 2024, capacity-weighted over available hours:

| class | band | nameplate MW | delivered fuel $/MMBtu | offered HR | **offer $/MWh** | carbon | VOM |
|---|---|---:|---:|---:|---:|---:|---:|
| `CC_REGULAR` | econ | 3,039 | 2.44 | 7.16 | **28.48** | 8.17 | 2.00 |
| `CT_CHP` | econ | 204 | 2.10 | 7.58 | 36.25 | 16.69 | 3.50 |
| `ST_GAS` | econ | 5,692 | 2.47 | 12.72 | **48.81** | 11.04 | 4.00 |
| **`CT_PEAKER`** | **econ** | **2,468** | **4.52** | **12.69** | **67.44** | 12.61 | 3.50 |
| **`CT_PEAKER`** | **committed** | **347** | **4.35** | **15.13** | **73.95** | 11.69 | 3.50 |

Two inputs separate `CT_PEAKER` from the rest, and they are different in kind:

**(a) Delivered fuel, $4.35–4.52 against $2.04–2.47 for every other gas class.** This is
`nyiso_downstate_ct_gas_basis` (cell **K**, armed): 109 downstate CT units set to their zone's
measured daily delivered index (Transco Z6 NY daily + LDC non-firm transport). Per zone in 2024 it
is `CT_PEAKER` NYC **$4.87** / Long Island $4.05 against `CC_REGULAR` NYC $2.11 and `ST_GAS` NYC
$2.08. **This is a measured input and this session does not touch it** — a NYC peaker on non-firm
LDC service genuinely does pay above a CC holding firm interstate capacity, and rule 14
`[R-ACCURATE]` says keep the measured input.

**(b) The band multipliers, against their OWN registered measured counterparts.** Each class's
registered band over its own `phys_*` key:

| class | committed / phys | econ_low / phys | econ_high / phys |
|---|---|---|---|
| `CC_REGULAR` | 0.90 / 0.964 = **0.93** | 0.95 / 0.784 = **1.21** | 1.00 / 0.925 = **1.08** |
| `ST_GAS` | 1.05 / 1.104 = **0.95** | 1.08 / 0.830 = **1.30** | 1.13 / 0.828 = **1.37** |
| **`CT_PEAKER`** | **1.35 / 0.843 = 1.60** | **1.00 / 0.661 = 1.51** | **1.00 / 0.658 = 1.52** |

The ratio is ordered exactly against the observed error: the class the model over-runs is offered
closest to its own physics, the two it under-runs are offered furthest above. `peak` is
deliberately excluded here and from the arm — NYISO's 4.0 / 4.2 peak walls are the **$1,000
offer-cap scarcity structure** the config states them as, not a physics claim, and they are not a
merit-order defect.

**Neither band's ground is the residual, and both grounds are written in the codebase already:**

* `committed` **1.35** — `_NYISO_OFFER_CURVE` calls it "NYISO/CAISO-grounded evening-ramp start
  hurdle" and its own `phys_*` comment calls the gap "a ~$25/MWh fixed commitment margin". The
  keeper runs **`tranche_startup_amortization = True`** with `tranche_startup_measured_runs = True`,
  so P1 already amortizes `BIN_STARTUP_COST_PER_MW["CT_PEAKER"] = $20/MW` (NREL/SR-5500-55433) over
  the measured P0 run length onto **this same tranche**. Two mechanisms priced the same start:
  rule 19 `[R-ONE-MECH]`. The caiso-241 admissibility ruling
  (`PRECOMMIT-caiso241-ct-peaker-committed-2026-09-03.md` §1) names **NYISO 1.350 / 0.843**
  explicitly in the five-ISO census of this defect class, and its limb 3 binds *harder* here than
  in CAISO, where the amortization was OFF.
* `econ_low`/`econ_high` **1.0** — the config states these are a DE-LEAK of the ERCOT generic
  fallback (was 1.27 / 1.98) to a neutral placeholder, and declares the replacement an **OPEN ROOT
  CAUSE** by name: *"NYISO carries no independent CT part-load heat-rate spread yet … a
  NYISO-grounded CT econ ramp (CAMPD CT heat-rate spread) is a later disciplined-calibration item."*
  That named input now exists and is registered on the same band dict: 0.661 / 0.658, n = 70.

## 4. Phase 0c — the measured delta, its reach, and its price exposure

A **measurement-only** `fleet_only` rebuild (no LP, no bundle, nothing registered) with
`CT_PEAKER.committed/econ_low/econ_high := phys_committed/phys_econ_low/phys_econ_high`:

**D-1, the delta is surgical and fuel-invariant.**

| year | rows moved | cells moved | pmax max‖Δ‖ | availability max‖Δ‖ | Δ committed | Δ econ | Δ peak |
|---|---:|---|---:|---:|---:|---:|---:|
| 2023 | 101 / 812 | `CT_PEAKER` econ 79, committed 22 | 0.0 | 0.0 | **−17.41** | **−13.68** | 0.00 |
| 2024 | 103 / 809 | `CT_PEAKER` econ 81, committed 22 | 0.0 | 0.0 | **−17.41** | **−13.69** | 0.00 |
| 2025 | 103 / 809 | `CT_PEAKER` econ 81, committed 22 | 0.0 | 0.0 | **−17.35** | **−13.68** | 0.00 |

Zero rows move in any other class, band or ISO; no capacity moves. The delta is identical to the
cent across three years whose CT offers differ by $22–30/MWh, because under
`gas_offer_net_revenue_margin` the reformed cost is `phys·HR·fuel + (mult − phys)·HR·anchor`:
grounding leaves the fuel-scaled physical cost **untouched** and removes **only** the
fuel-invariant margin. That is the caiso-241 signature reproduced independently on NYISO's fleet.

**D-2, it reaches the object.**

| year | in-the-money CT capacity, keeper → arm | energy bound, keeper → arm | model | meter (EIA-923) |
|---|---|---|---:|---:|
| 2023 | 99.3 → **399.2 MW** | 0.870 → **3.497 TWh** | 0.421 | 2.114 |
| 2024 | 93.9 → **341.9 MW** | 0.823 → **2.995 TWh** | 0.392 | 1.911 |
| 2025 | 275.6 → **520.0 MW** | 2.414 → **4.556 TWh** | 1.356 | 2.851 |

Not inert, and the bound brackets the meter rather than swamping it.

**D-3, the price exposure — stated in advance, and it is the risk.** Same-weights merit-order
crossing on the LP's own offer stack (the price at which the arm's cumulative available capacity
equals the keeper's at the keeper's own clearing price). **An indicator, not the scored C3a** —
the identically-constructed nyiso-198 indicator predicted −4.2 % on 2024 and the span measured
−4.20 %.

| year | keeper mean LMP | arm | Δ | keeper C3a | **implied C3a** | ±10 % band |
|---|---:|---:|---:|---:|---:|---|
| 2023 | 32.319 | 31.431 | **−2.75 %** | +4.6 % | ~+1.9 % | pass |
| 2024 | 38.293 | 37.374 | **−2.40 %** | +4.7 % | ~+2.3 % | pass |
| **2025** | 58.464 | 56.864 | **−2.74 %** | **−6.9 %** | **~−9.6 %** | **0.4 pp of margin** |

**D-4, the footprint (no meter, no residual in the metric)** — newly in-the-money CT MWh:
**2023 2.627 TWh > 2024 2.173 > 2025 2.142**. Under rule 29 the screen year is therefore **2023**;
the exposed year is **2025**. The brief's instruction applies exactly — nyiso-198's screen cleared
a year the risk did not live in — so the pre-registration screens **both**.

## 5. What this says about the keeper, whatever the disposition

1. **`CT_PEAKER` carries no commitment mechanism and never has.** Forced floor 0.000 TWh, D-2
   0.0 %, 0 hours at a floor in three years. Every other thermal class in the NYISO keeper is
   floored somewhere. The class runs on offer merit alone, and its offer is 1.5–1.6× its own
   registered measured basis.
2. **The `committed` 1.35 and P1's startup amortization are both live on this keeper**, charging
   the same tranche for the same start. That is true today, on the designated keeper, regardless
   of whether anything is armed.
3. **`ST_GAS` is not a merit-order lever and should stop being proposed as one.** Its gap lives
   below $40 where no steam offer clears; the cell that owns it is `scuc_load_pocket_commitment`
   (**G**), and the instrument that would size it is the one nyiso-97 §5 forbids.
4. **This is the pairing nyiso-198's rejected arm asked for, and the two push opposite ways.**
   `cc_duct_peaking_row_scoped` moved +1.1 to +1.4 TWh **into** `CC_REGULAR` out of `ST_GAS` and
   `CT_PEAKER`; this arm moves energy **out of** `CC_REGULAR` into `CT_PEAKER`. They are not
   additive and must not be screened separately and summed. The matrix's re-test condition for
   cell `cc_duct_peaking_row_scoped` ("re-arm it PAIRED with the merit-order repair, never alone")
   is satisfiable only by a joint screen, which the pre-registration provides for as a second arm.

## 6. G-DRIFT — rule 29(b) form 4, validated empirically rather than by reading the diff

`git diff f7bb76a5..HEAD` over the solve path touches 49 files / 6,122 insertions, which a hunk
classification could argue either way. Two zero-cost empirical checks settle it instead, and both
are stronger than the diff reading:

* **Check 1 — the HEAD-reconstructed envelope against the keeper's COMMITTED dispatch.**
  `max(model / Σ pmax·availability)` per class-year is **exactly 1.00000** in 15 of 18 class-years
  and ≤ 1 in all 18 (`CT_PEAKER` 0.976 / 0.945 / 0.976, `ST_GAS` 2024 0.995). A HEAD fleet that had
  drifted in capacity or availability would break the bound or fail to touch it.
* **Check 2 — a committed keeper-sha probe record re-run at HEAD.** Every row of nyiso-198's
  `_nyiso198_cricket_partload_phase0.json` `lp_units` block reproduces at HEAD to its own recorded
  precision: pmax 330.42 / 85.14 ×6 / 245.64, heat rates 6.3117 … 15.7791, mean offers 27.248 …
  53.728, mean availability 0.5097 — **max ‖Δ‖ = 0.0024**, which is that record's own 3–4 dp
  rounding. The capacity basis, heat rates, delivered fuel, carbon and margin path are unchanged.

**Form 4 is valid: the keeper's committed bundle is the control, and no control solve is owed.**

## 7. The one thing this session cannot decide

The arm is an `offer_curve_by_group` band substitution, and this lane's brief gates any such
change on an explicit owner ruling. **No arm was built, no field was added, no solve was spent.**
The ruling question, stated exactly:

> May NYISO's `CT_PEAKER` `committed` / `econ_low` / `econ_high` be set to that class's OWN
> registered measured `phys_committed` / `phys_econ_low` / `phys_econ_high` (0.843 / 0.661 /
> 0.658) — as a gated, registered `ScenarioConfig` field on the caiso-241 construction, selecting
> no value, adding no free parameter and no DOF entry — and screened under rule 29 on 2023 (the
> footprint year) **and** 2025 (the exposed year) before any span is spent?

Two things are already true and do not depend on the answer: the object is real and measured, and
the C3a-2025 exposure is real and pre-named. **The honest expectation is that this arm improves
C1 `CT_PEAKER` and `CC_REGULAR` and puts C3a-2025 within ~0.4 pp of its band** — which is why the
pre-registration screens the exposed year rather than the footprint year alone, and why its S-4
gate stops the arm there rather than at the span.

*(nyiso-199, 2026-09-06. ZERO solves. Nothing registered, nothing promoted, no `ScenarioConfig`
field added. Keeper unchanged: `2026-09-06-nyiso-196-extract-basis`.)*

---

# §8 — THE SCREENS RAN. **2023 CLEARS. 2025 STOPS — and NOT on the pre-named risk.** The arm is killed at the screen, the span was never spent, and the thing that stopped it is a new finding.

**Owner ruling** (PREREG Addendum A, pushed before the field existed): arm both bands, screen
2023 + 2025. Executed exactly. **Field:** `nyiso_ct_peaker_bands_measured` (gated, default off,
NYISO-scoped, registered in `_CACHE_KEY_OPTIONAL_FIELDS` with its pinned default in the same
commit; base matrix row + a cell in all six shards, same commit). **Two solves, both one-year
throwaway probes** — never registered, deleted before merge (rule 29(c)); every number this
session will ever cite from them is in this section and in
`_nyiso199_screen_gates_{2023,2025}.json`.

## 8.1 Pre-solve F-gates: all four PASS on the BUILT field

The field reproduces the phase-0 measurement-only rebuild exactly. Resolved bands in every year:
`committed 0.843, econ_low 0.661, econ_high 0.658`, with `peak 4.0`, `pct_peaking 7.0` and
`econ_low_share 0.526` **untouched**.

| gate | 2023 | 2024 | 2025 |
|---|---|---|---|
| **F-1** rows moved (predicted) | 101 (101) | 103 (103) | 103 (103) — all `CT_PEAKER` econ+committed, **zero elsewhere** |
| **F-2** `pmax` / `availability` max‖Δ‖ | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| **F-3** Δ committed / econ $/MWh | −17.41 / −13.68 | −17.41 / −13.69 | −17.35 / −13.68 |
| **F-4** Δ peak | 0.00 | 0.00 | 0.00 |

## 8.2 SCREEN A — 2023, the footprint year: **CLEAR on all four gates**

| class | keeper TWh | screen TWh | Δ | C1 keeper | C1 screen | actual |
|---|---:|---:|---:|---|---|---:|
| **`CT_PEAKER`** | 0.421 | **1.418** | **+0.997** | −1.69 TWh, −1.3 pp | **−0.70 TWh, −0.5 pp** | 2.114 |
| `ST_GAS` | 9.952 | 9.322 | −0.630 | +1.81, +1.6 pp | **+1.18, +1.1 pp** | 8.141 |
| `CC_REGULAR` | 33.840 | 33.571 | −0.269 | +0.83, +1.2 pp | **+0.56, +0.9 pp** | 33.012 |
| `CC_CHP` | 15.751 | 15.667 | −0.084 | +0.95, +1.0 pp | **+0.86, +0.9 pp** | 14.802 |
| `CT_CHP` | 1.500 | 1.467 | −0.033 | | | |
| import | 23.341 | 23.339 | −0.003 | | | |

* **S-1 PASS** — +0.997 TWh, inside the arm's own 2.627 TWh pre-solve reachability bound. **59 % of
  `CT_PEAKER`'s gap to its meter closes.**
* **S-2 PASS** — gas-family total **−0.023 TWh**; the largest non-gas move is import at 0.003 TWh.
  A clean within-family reallocation.
* **S-3 PASS** — **zero C1 PASS → FAIL flips**; C3a **+4.6 % → +2.9 %** (PASS, closer to zero);
  C3b NRMSE 0.119 unchanged.
* **C8 / D-4 PASS** — D-2 passes both sides; the same two pre-existing 2023 `ST_GAS` D-4 rows
  (plants 2480, 8906) on both, **no new row**; `CT_PEAKER` still carries no forcing at all.

**Every class that moves, moves toward its actual.** The observed price move is **−1.7 %** against
the crossing indicator's −2.75 % — the indicator over-predicts the fall.

## 8.3 SCREEN B — 2025, the exposed year: **STOP**

**The pre-named C3a-2025 risk did NOT land.** C3a goes **−6.9 % → −9.1 %** against a ±10 % band —
degraded, still **PASS**, with 0.9 pp of margin, not the ~−9.6 % the indicator implied and nowhere
near the failure nyiso-198's unscreened year produced.

| class | keeper TWh | screen TWh | Δ | actual (prelim EIA-923) |
|---|---:|---:|---:|---:|
| **`CT_PEAKER`** | 1.356 | **2.672** | **+1.316** | 2.851 — **93.7 % of the gap closed** |
| `ST_GAS` | 9.606 | 8.745 | −0.861 | 13.712 |
| `CC_REGULAR` | 35.102 | 34.879 | −0.223 | 33.544 |
| `CC_CHP` | 20.344 | 20.205 | −0.139 | 16.962 |
| import | 19.335 | 19.293 | −0.042 | |

S-1 **PASS** (+1.316 inside the 2.142 bound). S-2 **PASS** (gas family +0.016 TWh). S-3 **PASS**
(no C1 flips — 2025's class cells are SKIPPED on the preliminary EIA-923 vintage; C3a PASS as
above; C3b 0.154 unchanged).

**C8 / D-4 STOPS IT, and the failure is a genuine structural defect the arm introduces.** The
`nyiso_gas_commitment_bridge × CC_REGULAR` unit-conduct rows, keeper vs screen, 2025:

| plant | keeper: floored TWh / binding h / measured median MW / zero-share | screen | verdict |
|---|---|---|---|
| 50292 | 0.1140 / 2,985 / 57.6 MW / 16.1 % | 0.1139 / 2,982 / 59.4 / 14.1 % | pass → pass |
| 2539 | 0.1023 / 415 / 660.8 / 2.9 % | 0.1036 / 421 / 660.8 / 2.9 % | pass → pass |
| 55405 | 0.0634 / 279 / 281.0 / 6.5 % | 0.0724 / 319 / 281.0 / 13.2 % | pass → pass |
| **7314** | **not floored at all** | **0.0669 / 3,210 h / 0.0 MW / 76.2 %** | **— → FAIL** |
| 57185 | 0.0334 / 174 / 242.8 / 4.6 % | 0.0377 / 195 / 275.6 / 4.1 % | pass → pass |
| **50978** | **not floored at all** | **0.0141 / 352 h / 0.0 MW / 69.9 %** | **— → FAIL** |
| 56940 / 56234 / 54574 | pass | pass | unchanged |

The arm brings **two plants the keeper never floors** into the commitment bridge's binding set, and
both have a **measured median output of 0.0 MW** over the hours the floor asserts they must be
online — 7314 for **3,210 hours** with the meter dark in 76.2 % of them. Rule 17
`[R-FLOOR-WINDOW]` names this exactly: *"A floor binding in hours its own driver evidence says the
class is offline is a bug by definition, whatever it does to the residual."*

**The mechanism is legible.** Cheaper CT capacity displaces `CC_REGULAR` in the **P0** base-cost
pass; two plants whose P0 pattern previously never produced a committed run now show a short
detected run, which `nyiso_gas_bridge_min_run` **extends to the class min-run and floors** — at
plants the meter says are off. This is a **P0-pattern dependence in the bridge**, not a defect in
the band grounding: the arm changes no floor and touches no bridge parameter. It is nonetheless a
real defect **caused by** arming the arm, and the pre-registered gate is the gate.

**Under rule 29 the arm is STOPPED at the screen. The 2023–2025 span was never spent, no bundle
was produced, and nothing is registered.**

## 8.4 The recommendation: **DO NOT PROMOTE on this evidence — and the arm is not dead**

Against the owner's standing formula (*"if structural integrity improves but gates regress that may
still be a keeper"* — permissive, not automatic), stated honestly on both halves:

* **The structural half is strong and is not in doubt.** Zero free parameters, no DOF entry, values
  taken from the class's own registered measurement; two independent ex-ante grounds (a rule 19
  double count that is live on this very keeper, and an OPEN ROOT CAUSE the config declares by
  name); the offer delta is surgical and fuel-invariant; and where it clears, **every class moves
  toward its actual** — `CT_PEAKER` closing 59 % of its gap in 2023 and 93.7 % in 2025.
* **The pre-named risk was screened and survived.** C3a-2025 −9.1 %, PASS. That is precisely what
  screening the exposed year was for, and it worked.
* **But a protective gate fires on a defect the arm itself creates.** Two plants floored for
  3,210 and 352 hours against dark meters is not a residual regression — it is the thing rule 17
  calls a bug by definition, and C8/D-4 is protective tier. A keeper that introduces it would be
  buying a real volume gain with a fabricated commitment.

**What the screen bought:** for two one-year solves instead of a full span, it found an interaction
the span would have buried inside a determination — and it found it in the year that a
footprint-only screen would never have looked at. That is the nyiso-198 lesson, applied and paying.

## 8.5 Handed forward — the next lever is now specific

1. **THE OBJECT IS THE BRIDGE'S P0-PATTERN DEPENDENCE, NOT THE BAND.** `nyiso_gas_bridge_min_run`
   extends a short detected P0 run to the class min-run and floors it. When cheaper supply moves CC
   out of merit, that turns *marginal* plants into *floored* ones at exactly the plants whose meters
   are dark. The eligibility test should be conditioned on the unit's own measured conduct in the
   window — the same D-4 statistic the diagnostic already computes — rather than on a P0 pattern
   that a merit change can manufacture. Fix that, then re-arm this field **paired**, exactly as
   nyiso-198's `cc_duct_peaking_row_scoped` is waiting to be re-armed paired with a merit repair.
2. **THE THREE-WAY PAIRING IS NOW THE REAL QUESTION.** `cc_duct_peaking_row_scoped` (cell R) moves
   energy INTO `CC_REGULAR`; this field moves it OUT. They are opposed, and the bridge sits between
   them. A session that fixes the bridge can screen all three together on 2023 + 2025 with the
   gates already written here.
3. **`ST_GAS` remains closed** (`scuc_load_pocket_commitment`, cell **G**) and should stop being
   proposed as a merit lever — §2 measured why.
4. **Plant 7314 context, stated not excused:** it is one of the three plants the fleet builder
   already reconciles for corrupt EIA-860 summer-capacity rows ("fleet pmax sum 199.5 MW exceeds
   trusted bound 170.0 MW") and it sits in the bench's `ctOnly` set at ratio 1.43. That does not
   make the off-window binding acceptable; it makes 7314 the right first plant to look at.
5. **Repo-wide, outside this lane (rule 25):** the caiso-241 sibling
   `caiso_ct_peaker_committed_measured` has the same latent silent-no-op exposure through the
   generic `prb_overrides` channel — its consumer is inside `backcast_config`, which runs *before*
   `prb_overrides` applies. This field ships a fail-loud guard; the sibling has none.

*(nyiso-199 §8, 2026-09-06. TWO solves, both one-year screens, both deleted before merge. Nothing
registered, nothing promoted, no span spent. Keeper unchanged:
`2026-09-06-nyiso-196-extract-basis`.)*
