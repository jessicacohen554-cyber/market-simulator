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
