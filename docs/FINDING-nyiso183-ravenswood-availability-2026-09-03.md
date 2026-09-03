# FINDING — nyiso-183 (`ravenswood-availability` lane): the availability hypothesis is **REFUTED on its own pre-registered gate**, the carrier is the **OFFER**, and it sits in **ONE TERM** — a heat-rate basis at Ravenswood that is ~20 pp out of line with its own class

**Session:** nyiso-183, `ravenswood-availability` lane
(`claude/nyiso-183-ravenswood-availability-b8jbex`), NYISO backcast-calibration
track, 2026-09-03. **Solves run: ZERO.**
**Keeper at entry and exit: `2026-09-02-nyiso-177-vintage-matched`**
(`results/calibration/nyiso177_vintage_B1p`) — determination **NOT-YET**, target
grade 5, fail set **{C1-2023 `ST_GAS` +3.86 TWh, C3a-2025 −11.2 %, C3c}**.
**Unchanged.** No parameter touched, no band swept, no `ScenarioConfig` field
added, no constant moved or swept, no arm built, `src/market_sim/` untouched.
**Pre-registration:** `results/calibration/PREREG-nyiso183-ravenswood-availability.md`,
pushed to `origin` at `53767546` **before the first measurement**, amended at
`3085f253` **before any gate below G0 was read**.
**Machine records:** `results/calibration/_nyiso183_ravenswood_availability.json`,
`_nyiso183_g4c_offer_position.json`, `_nyiso183_g4d_offer_anatomy.json`; probes
`scripts/probes/nyiso183_ravenswood_availability.py`,
`nyiso183_g4c_offer_position.py`, `nyiso183_g4d_offer_anatomy.py`.
**PREREG §6 S2 AND S3 BOTH FIRED — NO AVAILABILITY REPAIR IS PROPOSED**, on
their own pre-declared terms. **A different, named object is opened instead.**

---

## 1. The result in one paragraph

The brief handed this session nyiso-177's open G2 object with nyiso-181's
dispatch consequence attached, and asked whether Ravenswood's model availability
is a **mis-booking** (A) or whether its **offer** is too cheap (B). **A is
refuted, in all three years, on the gate the pre-registration fixed in
advance.** The merit-order guard's own evidence statistic separates cleanly at
Ravenswood: its guard-removed windows are out of merit for **0.995 / 0.934 /
0.958** of their hours while the plant's *running* hours are out of merit for
only **0.667 / 0.293 / 0.153** — a separation of **+0.33 / +0.64 / +0.81**
against a bar that required `oom_run` ≥ 0.90. The reclassification is material
(G2: the guard hands back **0.645 / 0.381 / 0.188** of Ravenswood's
capacity-year) but materiality without discrimination grounds nothing, and both
admissible repair forms independently collapse onto nyiso-177's
already-rejected unguarded arm (G3: `sel_fleet` **0.867** and **0.923** against
a 0.75 bar). **B fires instead, in all three years, on its pre-registered
inversion leg**: the model prices Ravenswood **3rd cheapest of 11** `ST_GAS`
plants every year while its measured SRMC ranks it **8th / 8th / 6th of 10**.
A post-hoc locator puts that inversion in **one term**: model heat rate ÷
CAMPD-measured heat rate is a tight **1.60–1.75** cluster across eight peer
plants and **1.382 / 1.417 / 1.454** at Ravenswood — the model's basis is
**9.50 MMBtu/MWh against a measured 10.71**, i.e. it prices a 1,725 MW machine
as *more* efficient than its own meter while pricing every peer *less* efficient
than theirs. At the panel's own delivered gas that is **\$11.38 / \$7.88 /
\$13.08 per MWh** too cheap. **The C1-2023 object is an offer object, and it is
one number in one bin.**

---

## 2. RULE 19 `[R-ONE-MECH]`, discharged from the code before any proposal

Which armed mechanism OWNS the outage-vs-lay-up decision for NYISO `ST_GAS` on
this keeper? The keeper's envelope reads exactly one file
(`campd-unit-outages-perunitmerit-NYISO.csv`, sha256 `45bc4f7c…`, pinned in its
own `resolved_inputs`), and what is in that file is decided inside
`derive_campd_unit_outages.main()`'s per-unit loop in a fixed order:

| # | stage | code | decides | keeper |
|---|---|---|---|---|
| 1 | detector | `detect_outages_eventbased` | is there a dead span | committed |
| 2 | revealed-availability | `filter_revealed_outages` | ran through its own tight hours ⇒ not an outage | `high_load_pctl` 0.85, `min_inmerit_hours` 24 |
| 2b | full-stop override | same function | ≥ 5 d at mean CF < 0.02 ⇒ **kept as mechanical** | committed |
| **3** | **merit-order guard** | **`filter_merit_order_layup`** | **out of merit ≥ 0.90 of the span ⇒ ECONOMIC LAY-UP, leaves the envelope** | **ARMED** |
| 4 | consumer floor | `unit_outage_derate_factors` | drops < 5 d rows, excludes CTs | committed |

**Stage 3 owns it, and owns it LAST.** Stages 1–2b can only *propose* a window
as mechanical; stage 3 alone can take one back out. Every other availability
gate is off on this keeper (`unit_outage_short_windows`,
`unit_partial_outage_windows`, `unit_outage_fleet_status_scope`,
`unit_outage_mixed_gas_routing`, `unit_outage_lp_capacity_basis`,
`historic_outage_overlay` — all verified `False` in `run_config.json`);
`campd_per_unit_attribution` decides routing, not outage-vs-lay-up (nyiso-177 G1:
it moves `(2500, ST_GAS)` by ≤ 0.012); `nysdec_peaker_rule_availability` and the
nuclear family are class-disjoint. **The rule-19 answer is unambiguous and it
was fixed in the pre-registration before any number existed.**

---

## 3. G0 — the instrument, and a CORRECTION to the inherited record

**G0 AS FIRST WRITTEN FAILED, and the failure is recorded, not edited.** The
pre-registration cited nyiso-177 §2.1's **0.772 / 0.465 / 0.297** as "the keeper
path". It is not. That row is labelled *"L0 keeper (incumbent + override)"* and
describes the **superseded nyiso-159** keeper — the incumbent extract with
`outages._FLEET_GROUP_OVERRIDE` armed. The promoted B1′ recipe replaces **both**
(`campd_per_unit_attribution` disarms the override at `outages.py:327` and
selects the `-perunitmerit-` extract), and §1–§9 of nyiso-177 were written before
the ruling, so the figure was never restated.

**The CURRENT keeper's `(2500, ST_GAS)` availability is `0.786 / 0.478 / 0.309`.**
The matrix §5.5 lever queue, nyiso-181 §5.1's inherited pair and this session's
own brief all carry the stale value.

The instrument is anchored instead on nyiso-177 §2.3's two rows that **are**
reachable through the engine's public API — both exact, neither the quantity
under investigation, and a strictly harder test than the one they replace:

| leg | kwargs | measured | published | max Δ |
|---|---|---|---|---|
| **L0** incumbent + override | `per_unit=False, guard=False` | 0.7715 / 0.4645 / 0.2968 | 0.772 / 0.465 / 0.297 | **0.0005** |
| **L2** per-unit, override off | `per_unit=True, guard=False` | 0.1412 / 0.0967 / 0.1212 | 0.141 / 0.097 / 0.121 | **0.0002** |

**G0a and G0b PASS.** G0c (the keeper leg) has no published anchor at its own
configuration and is therefore not gated against one; it is built from the
keeper's own pinned input through the engine's own builder at the keeper's own
kwargs. **The correction makes the object LARGER, i.e. it cuts against this
session's own hypothesis A** — the guard hands back 0.645 rather than the 0.643
the stale pair implies.

---

## 4. G1 — HYPOTHESIS A IS REFUTED: the guard's evidence DOES discriminate

The guard removes a window on the evidence *"out of merit ≥ `MERIT_OOM_FRAC`
(0.90) of the span."* That is evidence for lay-up **only if the same condition
does not also hold while the unit is demonstrably available and generating.** So
the pre-registration fixed, before any measurement, the identical statistic
evaluated over the unit's **running** hours (`grossLoad / peak ≥ REAL_RUN_CF` —
the merit panel's own revealed-run convention), and set the bar at
`MERIT_OOM_FRAC` itself, no new number.

| year | Ravenswood `ST_GAS` cap | **`oom_run`** (bar ≥ 0.90) | `oom_down` | **separation** | run hours |
|---|---|---|---|---|---|
| 2023 | 1,782 MW | **0.6669** | 0.9954 | **+0.329** | 3,945 |
| 2024 | 1,782 MW | **0.2928** | 0.9336 | **+0.641** | 2,955 |
| 2025 | 1,782 MW | **0.1531** | 0.9581 | **+0.805** | 4,578 |

**G1 DOES NOT FIRE in any year. PREREG §6 S2 fires: no availability repair is
proposed.** Ravenswood runs predominantly *in* merit and is down predominantly
*out* of merit — which is exactly what an economic lay-up looks like and exactly
what the guard is built to detect. The class agrees: the separation is +0.86 /
+0.87 at Northport's units 3 and 4, +0.89 at Bowline's unit 2, +0.92 at Roseton's
unit 1. **This independently re-confirms nyiso-178 §4's class-grain result from a
different construction and at a finer grain**, and it is the read the
pre-registration disclosed (§0 item 4) as cutting against its own hypothesis.

### 4.1 The one qualification, reported because it is real — and it changes nothing

At **unit** grain the picture is not uniform. In 2023 Ravenswood's **unit 30**
(1,000 MW, 56 % of the plant's `ST_GAS` capacity) ran 1,218 hours at
`oom_run` = **0.9195**, *above* the bar, against 7,680 lay-up hours at
`oom_down` 0.9997 — a separation of only **0.080**. For that one machine in that
one year the statistic is close to non-discriminating, and 2023 is the year of
the failing cell. Unit 10 separates by 0.293; unit 20 has **no removed window at
all**. In 2024 and 2025 unit 30's separation widens to **0.866** and **0.925**.

**This is POST-HOC, it is one unit in one year, and it does not resurrect A** —
G1 as pre-registered is measured as written and did not fire, the bar is not
moved, and §5 shows the repair route is independently blocked. It is recorded
because a reader is entitled to it.

---

## 5. G2 and G3 — material, and independently UNREPAIRABLE by this route

**G2 FIRES.** The capacity-year share stage 3 hands back at Ravenswood:

| year | keeper path | unguarded path | **share reclassified** |
|---|---|---|---|
| 2023 | 0.7860 | 0.1412 | **0.6448** |
| 2024 | 0.4778 | 0.0967 | **0.3810** |
| 2025 | 0.3092 | 0.1212 | **0.1880** |

So the mechanism is large. **But materiality without discrimination grounds
nothing**, and G3 blocks both admissible repair forms on their own pre-declared
selectivity bar (`sel_fleet` ≤ 0.75, i.e. the repair must not be the rejected
unguarded arm in disguise):

| form | what it restores | `sel_stgas` | **`sel_fleet`** | verdict |
|---|---|---|---|---|
| **R2** guard inert where `oom_run` ≥ `MERIT_OOM_FRAC` | 165,744 of 226,608 `ST_GAS` layup-hours | 0.7314 | **0.8674** | **FAILS 0.75** |
| **R1** stage-2b full-stop precedence over stage 3 | 209,280 of 226,608 | **0.9235** | — | **FAILS by construction** |

R1's *premise* is admissible on its own pre-declared bar — **92.4 %** of the
guard-removed `ST_GAS` window-hours sit in windows stage 2b would itself have
kept as mechanical (≥ 5 d at mean CF < 0.02), so stage 3 really does overrule
stage 2b at scale. But restoring 92 % of the removed windows **is** the unguarded
extract, which nyiso-177 tested (B1: grade 3, fails 4, load-weighted price
38.01 / 40.49 / 62.00 against actual RT 32.25 / 38.12 / 66.43). **PREREG §6 S3
fires. Hypothesis A is recorded UNREPAIRABLE-BY-THIS-ROUTE, and the
pre-registration's declaration that nyiso-177's rejection STILL BINDS is
honoured.**

---

## 6. G4 — HYPOTHESIS B FIRES, in all three years, on its pre-registered leg

G4c's instrument was expected to be unavailable (§0: PR #4656 is closed
unmerged, its branch deleted, no NYISO `unit_hourly` exists on `main`, and the
keeper's own invocation is recorded nowhere in the repository — neither
`run_config.json` nor `meta.json` stores an argv, so no CLI reconstruction could
be *verified* to be the keeper before the fact). **It was not needed.**
`scripts.lib.bundle_fleet.reconstruct_bundle_fleet` rebuilds the bundle's fleet
and its `mc_base` offer array **exactly as the bundle solved, with no LP**,
behind a fidelity guard that hard-fails on a dropped gate. **G4c is therefore
scored in full rather than left `PARTIALLY TESTED`.**

Two deviations from G4c's literal wording, both disclosed and neither relaxing
its \$5/MWh bar: `mc_base` (P0 base cost) rather than the P1 bid cost, because
measured SRMC (`HR × delivered fuel`) carries no startup either and P1 would be
the mismatched comparand; and a capacity-weighted time mean rather than a
load-weighted one, because no dispatch exists without an LP.

**2023, NYISO `ST_GAS` plants, model offer against measured SRMC (\$/MWh):**

| model rank | plant | cap MW | model `mc` | measured SRMC |
|---|---|---|---|---|
| 1 | 2682 S A Carlson | 45.0 | 40.14 | *(unidentified)* |
| 2 | 2527 Greenidge | 104.5 | 42.41 | 32.99 |
| **3** | **2500 Ravenswood** | **1,724.8** | **43.94** | **35.64** |
| 4 | 2490 Arthur Kill | 876.6 | 52.25 | 35.20 |
| 5 | 8906 Astoria Gen | 923.2 | 55.38 | 23.45 |
| 6 | 2625 Bowline Point | 1,159.6 | 67.30 | 32.93 |
| 7 | 2516 Northport | 1,592.2 | 71.32 | 34.05 |
| 8 | 8006 Roseton | 1,222.0 | 72.54 | 32.84 |
| 9 | 2511 E F Barrett | 372.2 | 72.89 | 33.17 |
| 10 | 2480 Danskammer | 497.3 | 74.50 | 36.54 |
| 11 | 2517 Port Jefferson | 385.0 | 78.49 | 36.51 |

| year | Ravenswood model rank | **measured rank** | peer model-`mc` median − Ravenswood | measured SRMC vs peer median | **G4c** |
|---|---|---|---|---|---|
| 2023 | 3 of 11 | **8 of 10** | **+\$23.35** | 35.64 > 33.17 | **FIRES** |
| 2024 | 3 of 11 | **8 of 10** | **+\$18.85** | 29.35 > 27.91 | **FIRES** |
| 2025 | 3 of 11 | **6 of 10** | **+\$25.37** | 56.59 > 55.40 | **FIRES** |

**Leg (ii) — the merit-position inversion — fires in every year of the training
window.** Leg (i) (`model mc` ≥ \$5 below its *own* measured SRMC) cannot fire
and is **uninformative by construction**: model `mc` carries VOM, RGGI CO2 and
the tranche multipliers that measured SRMC does not, so it is above measured
everywhere. That is a defect in leg (i)'s construction, mine, disclosed here
rather than argued around; the gate was carried entirely by the rank-based leg
(ii), which is immune to that level offset.

### 6.1 DISCLOSED INSTRUMENT REPAIR — a population trap, found by cross-check

The first cut of the measured population averaged the panel's `srmc` over
**every unit at an `ST_GAS`-labelled plant**. At Ravenswood that pulls in
**`UCC001`, the site's combined cycle, measured HR 7.137** against the steam
units' ~10.7–11.2; at Astoria it pulls in the four `RH`/`SH` heat-recovery halves
at 5.3–5.6. **This is nyiso-181 §3's population trap in mirror image.** It was
found by an **internal consistency check** — G4d's heat-rate ordering contradicted
G4c's SRMC ordering for the same plants — **not** by looking at whether a gate
fired. The population is now the keeper's **own** per-unit crosswalk
(`scripts/lib/campd_measured_classes`), with each plant's model roster taken from
the no-LP reconstruction itself.

**The repair MOVED verdicts: G4c 2024 and 2025 went `False → True`.** No bar was
touched, and the pre-fix numbers are stated here so the move is auditable
(pre-fix Ravenswood measured SRMC 35.96 / 26.93 / 52.32; post-fix 35.64 / 29.35 /
56.59).

---

## 7. G4d — WHERE the inversion sits: **one term**, the heat-rate basis

**POST-HOC, no bar declared, not scored — a locator, not a gate.** Model heat
rate (capacity-weighted over the plant's eight `ST_GAS` tranches, from the same
fidelity-guarded no-LP reconstruction) against the CAMPD-measured heat rate
computed by the merit panel's **own documented formula**
(`Σ heatInput / Σ grossLoad` over running hours, clipped to
`[MERIT_HR_MIN, MERIT_HR_MAX]`), on the repaired population:

**ratio model ÷ measured, 2023 / 2024 / 2025**

| plant | 2023 | 2024 | 2025 |
|---|---|---|---|
| **2500 Ravenswood** | **1.382** | **1.417** | **1.454** |
| 2527 Greenidge | 1.636 | 1.651 | 1.596 |
| 2625 Bowline Point | 1.650 | 1.604 | 1.643 |
| 2516 Northport | 1.676 | 1.675 | 1.699 |
| 2490 Arthur Kill | 1.678 | 1.684 | 1.749 |
| 2517 Port Jefferson | 1.720 | 1.745 | 1.731 |
| 2480 Danskammer | 1.739 | 1.686 | 1.738 |
| 8006 Roseton | 1.748 | 1.696 | 1.655 |
| 2511 E F Barrett | 1.749 | 1.744 | 1.671 |
| **8906 Astoria Gen** | **3.365** | **3.419** | **3.464** |

Eight peers cluster in **1.596–1.749**, median **1.699 / 1.685 / 1.685** — that
cluster *is* the class's uniform offer-curve markup, which makes the ratio a
clean like-for-like statistic. **Ravenswood sits far below it and Astoria far
above it, and they are the only two outliers.**

At tranche grain the object is a single number. Ravenswood's `ST_GAS` committed
tranche carries **9.975 MMBtu/MWh**, i.e. a base of **9.50** at the class's
committed multiplier 1.05 — **cross-checked independently against its own peak
tranche**, 39.900 ÷ the class peak multiplier 4.20 = **9.50** to four figures.
The same identity holds at Northport (11.432 ÷ 1.05 = 45.727 ÷ 4.20 = **10.887**)
and Barrett (11.630 ÷ 1.05 = 46.518 ÷ 4.20 = **11.076**), which confirms the
fleet `heat_rate` array carries the plain multiplier form rather than the
`phys_*` physical basis, so the recovered bases are exact and not an assumption
about which multiplier applies. Measured, on `ST_GAS` units only:

| plant | model base HR | measured HR | **model ÷ measured** |
|---|---|---|---|
| **Ravenswood** | **9.50** | **10.71** | **0.887** |
| Northport | 10.89 | 10.10 | 1.078 |
| E F Barrett | 11.08 | 9.88 | 1.121 |

**The model has Ravenswood ~11 % MORE efficient than its own meter while it has
every peer 8–12 % LESS efficient than theirs — a ~20-percentage-point relative
error on a 1,725 MW plant.** Bringing it onto its own class's measured
relationship would raise its model heat rate by **3.39 / 2.81 / 2.35
MMBtu/MWh**, i.e. by **\$11.38 / \$7.88 / \$13.08 per MWh** at the merit panel's
own delivered gas price (3.357 / 2.809 / 5.558 \$/MMBtu). Its model CO2 rate
moves with it (0.4508 against peers' 0.52–0.62), because both terms are driven
by the same basis. VOM is a uniform \$4.00 across the class and the tranche
multipliers are class-uniform, so **neither can carry this** — it is the heat
rate alone.

---

## 8. The upstream cause — NAMED and SIZED, explicitly **NOT** adjudicated

A hypothesis for *why* the basis is wrong, offered with its code site so the
successor can test it, and claimed as nothing more:

The eGRID heat-rate join reads **`PLHTIAN` / `PLNGENAN` / `PLHTRT`
(`fleet/eia860.py:624`) — PLANT-grain quantities**, so at a mixed site the steam
bin can inherit a facility-blended rate. Ravenswood is the NYISO `ST_GAS` class's
only large mixed site: nyiso-181 §6.1 measured that it carries **7 `CC_REGULAR`
LP rows beside its 8 steam rows**, and the reconstruction confirms a
`CC_REGULAR` bin at base HR ≈ 8.80. The direction and rough magnitude fit:
Ravenswood's **facility-blended** measured heat rate is **8.24** against the
**steam-only 10.71**, and the model's 9.50 sits between them.

**This is the same facility-summed-denominator defect family nyiso-177 repaired
on the OUTAGE and TRANCHE paths** — its promotion note names
`derive_thermal_tranches._fleet_nameplate_and_group`'s largest-nameplate proxy
and `derive_campd_unit_outages._resolve_unit_group`'s last-writer-wins
short-circuit — **surviving in the HEAT-RATE path, which
`campd_per_unit_attribution` does not reach.**

**What is NOT established:** this session did not trace why Ravenswood's
`CC_REGULAR` and `ST_GAS` bins carry *different* bases (8.80 vs 9.50), which a
pure plant-grain join would not produce. So a second term is at work and the
attribution is **incomplete**. Astoria's mirror-image 3.4× outlier is likewise
unexplained and is not assumed to share a cause. **No repair is proposed here**
— identifying the join is the successor's object, and PREREG §5 F4 forbids this
session adding a mechanism.

---

## 9. Honest expected value — what is NOT delivered

* **No repair, no arm, no keeper, no registered run.** S2 and S3 both fired on
  their pre-declared terms, so no non-control solve was run and rule 15 has
  nothing to register — the nyiso-179 / -180 / -181 zero-solve precedent, and the
  correct outcome rather than a gap.
* **The C1-2023 gate is not moved.** This session refutes one explanation,
  converts a second from testimony into measurement, and localises it to one
  term. It repairs nothing.
* **My own G0 bar was mis-specified**, citing the superseded keeper's
  availability as the current keeper's. Recorded FAILED, replaced by two harder
  published anchors, and the stale number corrected in the record.
* **My own G4c leg (i) was a badly-constructed statistic** — model `mc` and
  measured SRMC are not on the same basis in level — and it could not have fired.
  The gate was carried by leg (ii) alone.
* **My own measured population was wrong on first cut** (§6.1), and the repair
  moved two verdicts. Found by internal cross-check, disclosed, no bar touched.
* **§8's upstream attribution is a hypothesis, not a finding.** The CC/ST base
  difference is unexplained; Astoria's outlier is unexplained.
* **G4d has no bar and adjudicates nothing.** It is a locator. Nothing was
  adopted or rejected on it.
* **The over-booking (nyiso-177 G2) is UNREPAIRED**, and this session's result
  makes it worse-looking, not better: the guard's classification is *sound* at
  Ravenswood, so the 0.50–0.56 booked share is not reachable by fixing it.
* **nyiso-181's dispatch-side numbers remain unreproducible** (PR #4656 closed
  unmerged, branch deleted). Nothing here rests on them: every number in §§3–7 is
  measured from committed bytes or from the no-LP reconstruction.
* **The two secondary items are NOT sized.** `mustrun_layup_window_mask` is
  excluded from this object by construction (nyiso-181 established Ravenswood's
  excess is not forced) and its resolver extension stays unmade; the NYC
  persistent-base limb membership review was not opened — no plant on it meets
  nyiso-140's standard (§7 of nyiso-181), and S6 pre-committed against opening it
  on anything less.

---

## 10. Governance

* **Rule 1 `[R-STRUCT]`** — no residual was consulted in choosing what to
  measure, and nothing was adopted or rejected on whether it moved a fit. The
  instrument repair in §6.1 was triggered by an internal contradiction between
  two of this session's own measurements, never by a gate outcome.
* **Rule 5 `[R-NO-MAGIC]` / 21 `[R-DOF]` / 23 `[R-FROZEN-DERIVE]`** — **zero
  parameters touched, zero swept, nothing re-derived.** `MERIT_OOM_FRAC`,
  `MERIT_RCC_PCTL`, `MERIT_HR_MIN/MAX`, `FULL_STOP_OVERRIDE_CF/DAYS`,
  `HIGH_LOAD_PCTL`, `MIN_INMERIT_HOURS`, `UNIT_OUTAGE_MIN_DAYS`, `REAL_RUN_CF`
  and `ST_GAS_CF_PEAK` are all READ at their committed values (S1).
* **Rule 13 `[R-MEASURED]`** — measured CAMPD conduct and delivered fuel prices
  DIAGNOSE only; nothing is pinned. PREREG §5 F6 pre-emptively forbade the
  same-year hourly availability gate that would close C1-2023 and has no forward
  analogue; it was not built. The §7 statistic would regenerate for a forward
  year from CAMPD + fuel prices and responds to changed conditions.
* **Rule 14 `[R-ACCURATE]`** — §7 is this rule pointing at an open object: the
  accurate measured heat rate reads 10.71 and the model's basis reads 9.50.
* **Rule 15 `[R-DASHBOARD]`** — zero non-control solves, nothing to register (§9).
* **Rule 16 `[R-ALLYEARS]` / 12 `[R-PARALLEL]`** — every measurement spans 2023 +
  2024 + 2025; no solve, so no year loop and no concurrency.
* **Rule 17 `[R-FLOOR-WINDOW]`** — not engaged: nyiso-181 established this object
  is not forced, and no floor was touched (F7).
* **Rule 19 `[R-ONE-MECH]`** — discharged in §2 from the code before any
  proposal; both admissible repair forms were CONSTRAINTS on the existing stage
  3, never a stage 5, and neither was built.
* **Rule 20 `[R-FORCED-BUDGET]`** — untouched. The D-2 / C8 grain under-count
  stays escalated to the scorer lane (nyiso-181 §6.1), not acted on here.
* **Rule 22 `[R-HOLDOUT]`** — every year is 2023 / 2024 / 2025. NYISO is absent
  from both `complete` and `final`; **no marker was requested**; the locked-test
  freeze is untouched; no out-of-training year was solved, scored or registered.
* **Rule 24 `[R-REGISTRY]`** — **no new tunable**, no env-var knob, no CLI flag,
  no per-plant dict (F1 / S4).
* **Rule 25 `[R-ISO-SCOPE]`** — NYISO only; only the NYISO matrix shard edited.
* **Rule 27 `[R-PUSH]`** — **no existing source file was modified**;
  `src/market_sim/` is byte-untouched. The three probes are new files and the
  pushed blobs are the exact local bytes.
* **Rule 28 `[R-MECH-MATRIX]`** — §11.

* **Tests** — `tests/unit` + `tests/iso/nyiso`: **4,475 passed, 28 skipped,
  1 xfailed, 200 subtests passed**, with **4 failures in
  `tests/unit/results/test_export.py`**. Those four are the pre-existing
  environment failure nyiso-177 §9 recorded (a missing `confirmed-retirements`
  clean partition), and this session **proved** rather than asserted it: after
  `scripts/regenerate_clean.py confirmed-retirements`, that file runs
  **14 passed, 0 failed**. Effective result **4,489 passed, 0 failed**.

**One side effect, disclosed:** `data/clean/` (gitignored, derived and
disposable) was regenerated for `capacity-deliverability`,
`nyiso-interface-flows` and `confirmed-retirements` — the first two because the
no-LP reconstruction requires them and they were absent in this container, the
third to discharge the test question above. No raw input was written.

## 11. Matrix (rule 28 duty b)

NYISO shard only. **One verdict moves; the rest are annotated.**

* **`campd_outage_merit_order_guard` stays `K`, and is now POSITIVELY
  CORROBORATED rather than merely inherited.** Its evidence statistic separates
  down-hours from run-hours at Ravenswood by +0.33 / +0.64 / +0.81 (G1), the
  test the pre-registration set up to falsify it. Annotated with the correction
  that the keeper's `(2500, ST_GAS)` availability is 0.786 / 0.478 / 0.309, and
  with the measured fact that stage 3 overrules the stage-2b full-stop override
  on **92.4 %** of the `ST_GAS` window-hours it removes — real, and NOT a
  defect on this evidence.
* **`offer_curve_by_group` gains the NEW OPEN OBJECT** (`O`): the `ST_GAS`
  heat-rate basis at Ravenswood, 9.50 against a measured 10.71, ratio
  1.382 / 1.417 / 1.454 against an eight-peer cluster of 1.60–1.75, worth
  \$11.38 / \$7.88 / \$13.08 per MWh and inverting the plant four to five places
  in the merit order in every training year.
* **`campd_per_unit_attribution` stays `K`**, annotated: its repair does **not**
  reach the heat-rate path, which is where §7's residue lives.
* `reliability_floor`, `reliability_floor_plant_exclusions`,
  `mustrun_layup_window_mask`, `nyiso_gas_commitment_bridge`, `ramp_envelopes`
  and `energy_reserve_coopt` are **not** re-opened and their cells are not
  rewritten.

## 12. Handed forward

1. **THE C1-2023 OBJECT IS AN OFFER OBJECT, AND IT IS ONE TERM.** The model's
   `ST_GAS` heat-rate basis at Ravenswood is 9.50 MMBtu/MWh against a measured
   10.71 — ~11 % more efficient than its meter, where every peer's basis is
   8–12 % *less* efficient than its own. Worth **\$11.38 / \$7.88 / \$13.08 per
   MWh**; it puts 1,725 MW third in the merit order when the meter puts it
   eighth of ten. **This is where the successor goes.**
2. **DO NOT RE-OPEN THE AVAILABILITY ROUTE.** G1 refuted it on a
   pre-registered, falsifiable, per-unit test in all three years, and G3
   independently showed both admissible repair forms are nyiso-177's rejected
   unguarded arm in disguise (`sel_fleet` 0.867 / 0.923 against 0.75). **DO-NOT-REDO**
   unless new evidence addresses the separation directly.
3. **THE UPSTREAM JOIN IS THE NEXT QUESTION, AND IT IS NAMED.**
   `fleet/eia860.py:624` reads **plant-grain** eGRID `PLHTIAN`/`PLNGENAN`/`PLHTRT`;
   Ravenswood's facility blend is 8.24 against a steam-only 10.71 and the model
   sits at 9.50 between them. **Not adjudicated** — the unexplained CC/ST base
   split (8.80 vs 9.50) means a second term is at work. Start there, from source
   data, never from a residual.
4. **ASTORIA (8906) IS THE MIRROR-IMAGE OUTLIER**, ratio 3.365 / 3.419 / 3.464,
   priced far too EXPENSIVE — a plausible contributor to nyiso-181's
   −5.197 / −6.776 / −7.957 TWh other-ten-plant deficit. Unexplained here and not
   assumed to share Ravenswood's cause.
5. **THE INHERITED AVAILABILITY NUMBER WAS STALE.** `0.772 / 0.465 / 0.297` is
   the **superseded** nyiso-159 keeper's; the current keeper reads
   `0.786 / 0.478 / 0.309`. The §5.5 lever queue is corrected in this session.
6. **UNCHANGED and not opened:** C3a-2025 (owner-court,
   `DECISION-CARD-nyiso148` Q1); C3c (SUPPORTING, not lone); the D-2 / C8 grain
   under-count (escalated, code-generic, scorer lane); the nyiso-177 G2
   over-booking (unrepaired, and now shown NOT reachable through the guard); the
   `mustrun_layup_window_mask` resolver extension; the NYC persistent-base limb
   membership review.
7. **PR #4656 IS CLOSED UNMERGED AND ITS BRANCH IS DELETED** — nyiso-181's
   dispatch-side numbers do not reproduce from `main`. This session's results do
   not depend on them: `bundle_fleet.reconstruct_bundle_fleet` gives the keeper's
   own offer with no LP and no bundle beyond the committed one, and is the
   instrument a successor should reach for first.
