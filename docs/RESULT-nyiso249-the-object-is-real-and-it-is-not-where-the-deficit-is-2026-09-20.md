# RESULT — nyiso-249: the upper-tail offer dispersion is REAL and survives every denominator. It is also NOT where the C3c deficit is, and re-conditioning cannot move it there.

**Session** nyiso-249 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a)). **ZERO LP, ZERO SHARDS.**
**Date** 2026-09-20. **Base** `origin/main` at `ef6a498a`.
**Keeper (UNCHANGED, untouched)** `2026-09-20-nyiso247-fuel-invariance-disarm`, bundle
`results/calibration/nyiso247_fuelinv_span`, years {2022, 2023, 2024, 2025}. **NYISO STAYS
CALIBRATED.** No `ScenarioConfig` field was written, no keeper number moved, nothing was pruned.

> ## HEADLINE
> 1. **THE OBJECT IS REAL.** The corrected upper tail survives **every** denominator I could
>    construct: pooled p90 **+21.974** (daily hub) / **+22.525** (the model's own delivered gas for
>    CC_REGULAR + ST_GAS) / **+22.496** (the measured NYC LDC delivered index) MMBtu/MWh — a
>    **0.55 (2.5 %)** spread across denominators whose annual means differ by up to **75 %**. It is
>    **not** a fuel-basis artifact, and the arm-A reproduction check is **exact (0.0)**.
> 2. **AND IT IS NOT A C3c ROUTE.** The window it is identified in contains **7 of 153** missed
>    hours (coverage **2.2 / 0.0 / 0.0 / 12.8 %** against a pre-registered 25 %-in-two-years bar —
>    **0 of 4 years**), while **95–100 %** of that window's hours carry no actual tail at all.
> 3. **THE OBVIOUS FIX IS REFUTED, NOT MERELY REFUSED.** Re-conditioning on **load alone** — the
>    coordinate the deficit does live on, and which covers **51 %** of the missed hours — makes the
>    object **essentially vanish**: p90 falls **+21.974 → +0.930**, p75 **+4.685 → +0.276**. The
>    object is specific to the gas∧load **conjunction**; there is no upper-tail offer dispersion in
>    the deficit's own coordinate to transfer.
> 4. **SO THE DEFICIT IS NOT AN ENERGY-OFFER-LEVEL DEFECT AT ALL**, and the reason is structural:
>    **136 of 153** missed hours carry the model's maximum in **Long Island**, at the top of the
>    **load** distribution (2024 load-pct p50 **0.99**, with **0.0 %** of those hours reaching the
>    gas p90), in a zone that must **import 1,000–2,500 MW** to serve them. **P-27 is a DAY-AHEAD
>    book and C3c is scored on REAL-TIME prices** — the instrument and the phenomenon are in
>    different markets.
> 5. **NO SOLVE WAS SPENT**, exactly as addendum A1 pre-registered for this outcome. Four shards
>    were not launched to prove a prediction already falsified at zero cost.

---

## 1. WHAT WAS ASKED, AND WHAT THE PRE-REGISTRATION BOUGHT

The lane was briefed to build a form for nyiso-248's corrected upper-tail object
(**p50 −0.123 / p75 +4.685 / p90 +21.974**, not nyiso-246's arm-A `+2.035` / `25.845`), because
**C3c is NYISO's lone failing criterion in every year** — model **16 / 0 / 0 / 3** hours > $300
against **101 / 10 / 13 / 42** actual — and the reserve / RCPF / ORDC successor is foreclosed in
full (nyiso-242 §4).

Three documents were pushed **before** any gated number existed, and each one paid for itself:

| doc | sha | what it fixed ex ante |
|---|---|---|
| `PRECOMMIT-nyiso249-upper-tail-offer-dispersion-2026-09-20.md` | `f8046c19` | the G-DRIFT audit; the G-2 ladder + its collapse bar; the form and three refused alternatives; the level guard; C1-2023 ST_GAS by name; the C3c prediction; rule 19 / 25; the anti-sweep clause |
| `ADDENDUM-…-a1-the-window-must-reach-the-deficit…` | `fc83c5c1` | **G-3** and its 25 %-in-two-years bar, **with both outcomes' consequences written down** |
| `ADDENDUM-…-a2-the-counter-argument-to-g3…` | `b4ee414c` | **G-6**, as routing only, with "a large W2 tail is not a promise / a small one is equally informative" fixed before the measurement |

**The prediction in PRECOMMIT §6 (2022 ≥ 25 h, 2025 ≥ 8 h above $300) is reported as FALSIFIED
before the solve**, which is what it was written to be able to do.

---

## 2. G-DRIFT — form 4 valid, and the one live hunk checked by EXECUTION

`git diff 42d75053 origin/main` over the solve path: **6 files, 588 insertions**, from `1fd5d769`
(caiso-293), `f7d6112c` (pjm-h14), `cc66a606` (SPP-67). All six classified **INERT** — three new
`bool = False` fields all absent from the keeper's recipe, a default-`1.0` dataclass attribute, a
gated branch, a new function with one gated caller, and an SPP-keyed registry entry NYISO cannot
reach.

**G-DRIFT-M** then *executed* the only hunk on a path NYISO runs (`fleet/arrays.py`'s CHP min-gen
window): 2023, **712 generators, 14 CHP-floored, `chp_grid_pmin_on_frac ∈ [1.0, 1.0]`**, all three
new fields `False`. **Form 4 valid; the keeper's committed bundle is the control; no control solve
earned.** Reading a branch is weaker than running it.

---

## 3. G-1 — THE DERIVE REPAIR, OWED REGARDLESS OF THE VERDICT

`derive_nyiso_offer_level_dispersion` reached for `gas_series_by_year()` in **two** places — the
`state_windows` conditioner and the `year_unit_rows` denominator — which is how nyiso-248 came to
find two independent channels each carrying about half of a finding that did not survive their
joint correction. The gas array is now a **parameter** feeding both roles from one place
(`state_windows(gas)`, `build(out, gas, gas_label)`), with `None` reproducing the committed
artifact and `--gas daily` reaching the corrected coordinate. Self-test passes (T-1 / T-2 / T-3).
**They can never again resolve independently.**

---

## 4. G-2 — THE DENOMINATOR LADDER: THE OBJECT IS REAL

`m = bid bottom / G` makes `G` a **choice**, and a delivered-over-hub basis that widens in tight
hours manufactures a positive delta from a unit whose true heat rate never moved. That is the
identical artifact shape nyiso-248 found twice, and the model **already prices part of that basis**
(`nyiso_downstate_ct_gas_daily` SETS downstate CT_PEAKER to the measured LDC index), so under rule
19 `[R-ONE-MECH]` it had to be settled before a form existed.

Conditioner held at the corrected **daily** coordinate; **only the denominator changes**:

| arm | denominator | n | p10 | p25 | **p50** | **p75** | **p90** | p99 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **A** | monthly step *(= committed artifact)* | 1184 | −16.474 | −0.690 | **+2.035** | **+11.928** | **+27.880** | +96.710 |
| **D** | daily hub *(nyiso-248's correction)* | 1214 | −17.053 | −2.225 | **−0.123** | **+4.685** | **+21.974** | +88.716 |
| **E** | model's own delivered gas, CC_REGULAR + ST_GAS | 1214 | −21.322 | −3.754 | −0.645 | +3.739 | **+22.525** | +111.543 |
| **F** | measured **NYC LDC delivered** index | 1214 | −8.863 | −0.671 | +0.087 | +5.927 | **+22.496** | +61.140 |

**HARD GATE: arm A reproduces the committed artifact with max abs error `0.0`.**

**The invariance is the finding, and it is stronger than it looks.** The three corrected arms sit
at *very* different levels — 2024 annual mean **2.822** (hub) against **4.925** (LDC), a 75 % gap;
2025 max **84.967** against **100.870** — yet their pooled p90 lands within **0.55 MMBtu/MWh**.
Under the pre-registered reading (PRECOMMIT §2.3) that is the **"survives under both E and F"**
branch: **not a fuel artifact; the object is conduct.**

**Reported against itself:** the median is dead under *every* corrected arm (−0.123 / −0.645 /
+0.087), so nyiso-248's correction is confirmed twice over and **no part of nyiso-246's `+2.035`
or `25.845` survives**. And p10–p25 are negative throughout: the *lower* tail of units **lowers**
its implied heat rate in tight hours — a real feature of the book that no form here addresses.

---

## 5. G-3 — THE WINDOW DOES NOT REACH THE DEFICIT. **0 OF 4 YEARS.**

Using the C3c gate's own two quantities (`missed_mask`: actual RT hub > $300 **and** model max
zonal dual ≤ $300):

| year | actual > $300 | **missed** | tight hours | **missed inside tight** | **COVERAGE** | EXPOSURE *(tight hours with no actual tail)* |
|---|---:|---:|---:|---:|---:|---:|
| 2022 | 101 | 91 | 138 | **2** | **2.2 %** | 136 / 138 = **98.6 %** |
| 2023 | 10 | 10 | 22 | **0** | **0.0 %** | 22 / 22 = **100 %** |
| 2024 | 13 | 13 | 61 | **0** | **0.0 %** | 61 / 61 = **100 %** |
| 2025 | 42 | 39 | 108 | **5** | **12.8 %** | 103 / 108 = **95.4 %** |
| **total** | 166 | **153** | 329 | **7** | **4.6 %** | — |

**Bar: ≥ 25 % in at least two years. Result: 0 of 4.** The form fires in 329 hours across four
years, of which **322 had no market tail to find**, and reaches **7** of the 153 hours the gate
actually counts. This is not a near miss.

---

## 6. G-4 / G-5 — WHY: THE DEFICIT IS **LONG ISLAND AT PEAK LOAD**, NOT GAS SCARCITY

| year | missed | **model-max zone** | load-pct p50 (share ≥ p90) | gas-pct share ≥ p90 | model max price in those hours (p50 / p90 / max) |
|---|---:|---|---|---:|---|
| 2022 | 91 | **Long_Island 77**, NYC 14 | 0.81 (28.6 %) | 47.2 % | 158.25 / 286.46 / **298.81** |
| 2023 | 10 | **Long_Island 10** | 0.97 (70.0 %) | 10.0 % | 87.15 / 180.44 / 195.93 |
| 2024 | 13 | **Long_Island 13** | 0.99 (69.2 %) | **0.0 %** | 63.12 / 82.18 / 89.49 |
| 2025 | 39 | **Long_Island 36**, NYC 3 | 1.00 (92.3 %) | 15.4 % | 173.91 / 243.28 / 278.70 |

**136 of 153 (88.9 %) are Long Island.** The hours are top-of-**load** and — in 2024 — literally
**none** of them reaches the gas p90. Months confirm it: 2023 is September-led, 2024 is July-led,
2025 is June + July (29 of 39). Only 2022 is a winter-gas year, and it is the sole year with any
coverage at all.

**And Long Island is import-dependent in exactly those hours** (G-5): LI demand averages
**3,032 / 3,786 / 3,832 / 4,470 MW** (max 5,489) against LI's own available thermal of
**2,601 / 2,893 / 2,918 / 3,249 MW** — so 1,000–2,500 MW must be imported, and the LI dual is set
at a locational margin, not by an ISO-wide offer level.

**Two things measured here that a successor should not re-derive:**
* **The keeper IS climbing into the peak band** — `peak` carries **1.22 / 3.78 / 2.49 / 4.79 %** of
  dispatched MW in the missed hours. The stack's top is being used; it is not high enough, or the
  marginal unit is elsewhere. "The peak band is never reached" is **false**.
* **INSTRUMENT GAP:** `class_hourly` and `class_band_hourly` carry **no zone column**, so per-zone
  idle capacity is **not computable from a committed keeper bundle**. `nyiso242_tail_reachability`'s
  headline ("4,689 MW idle sub-$300 in 2022's missed hours, therefore unreachable by price
  formation") is an **ISO-wide** number, and these are **locational** hours — the bound may
  therefore not be binding on the LI price at all. Answering that needs `dispatch/<year>_P1.parquet`
  or a zone column on the class sidecar.

---

## 7. G-6 — THE COUNTER-ARGUMENT IS REFUTED, NOT MERELY REFUSED

A2 pre-registered the obvious objection — *"condition on load instead, where the deficit is"* —
and committed to measuring it rather than dismissing it. Denominator held at the corrected daily
array; only the conditioner changes:

| variant | tight | n | p25 | p50 | **p75** | **p90** | p99 | **coverage of missed** |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **W1** | `gas ≥ p90 AND load ≥ p90` *(registered)* | 1214 | −2.225 | −0.123 | **+4.685** | **+21.974** | +88.716 | 4.6 % |
| **W2** | **`load ≥ p90` alone** *(the deficit's coordinate)* | 1235 | −0.848 | −0.064 | **+0.276** | **+0.930** | +21.358 | **51.0 %** |
| **W3** | `gas ≥ p90` alone | 1232 | −3.461 | −1.121 | +0.000 | **+2.244** | +43.624 | 32.7 % |

**W1 reproduces ladder arm D to every reported digit** — the hard gate A2 set.

**The object collapses in the deficit's own coordinate: p90 +21.974 → +0.930, a 24× fall; p75
+4.685 → +0.276, a 17× fall.** At a typical delivered gas of ~$5/MMBtu, W2's p90 is **+$4.65/MWh**
of offer — against a deficit of **$200+**.

So the objection does not merely fail on identification grounds. **There is no upper-tail offer
dispersion in load-tight hours to transfer.** The measured object is specific to the
gas∧load **conjunction**, and NYISO's price-tail deficit is not a gas-scarcity phenomenon. W3
(+2.244) shows the gas leg alone carries little of it either: **the conjunction is the object**.

---

## 8. WHAT THIS MEANS — STATED IN BOTH DIRECTIONS

**FOR the object.** It is measured, it is conduct, it survives three denominators spanning a 75 %
level range, it is rule-13 admissible (an offer, never an outcome; both coordinates regenerate
forward), and it would carry **zero fitted parameters** — `τ` is read off the book at p75 and p90.
The model's conditional offer-level channel is **empty** after nyiso-247's disarm, so arming it
would **replace nothing and stack on nothing** (rule 19 discharged). Rule 1 `[R-STRUCT]` is clear
that a structurally-faithful mechanism is not rejected because a residual did not move.

**AGAINST spending a solve on it now.** It was briefed as the C3c route and that purpose is
falsified. Its window is **98.6–100 %** hours with no market tail; its most likely LP effect is
near-**inert** (the book itself says the lifted units are not the marginal ones — which is why the
market's own price stayed below $300 in 322 of those 329 hours); and it would put **C1-2023
ST_GAS**, already at **+3.59 TWh / +3.0 pp** against ±3.82 / ±3 pp, at risk for a change with no
named benefit. PRECOMMIT §9 made the solve conditional on every zero-LP gate clearing. **G-3 did
not clear, so no shard was launched** — which is precisely what A1 pre-registered for this branch.

**The deepest structural point, and it is the one to carry forward:** **P-27 is the DAY-AHEAD
genbids book; C3c is scored on REAL-TIME hourly prices.** A real-time shortage event does not
appear in a day-ahead offer book at all. Together with nyiso-245's refutation of the within-unit
**shape** form (market +$0.12/MWh against the model's +$11.34 — the model already over-steepens by
11×), **both legs of the energy-offer side are now measured on NYISO's own corpus, and neither
carries the deficit.** The offer side was named "the only live route" because the reserve side was
foreclosed; this session's finding is that **it is not a live route either — because the
instrument and the phenomenon are in different markets.**

---

## 9. THE QUESTION FOR THE OWNER — TWO OF THEM, AND NEITHER IS TAKEN HERE

Rule 31 `[R-RETAIN]`: **nothing was deleted; no bundle was produced, so there is nothing whose
retention is at stake.** Rule 15 `[R-DASHBOARD]`: **no run completed, so there is nothing to
register** — the keeper's dashboard entry is untouched and correct.

1. **Should a successor arm `nyiso_offer_tail_dispersion` on STRUCTURAL grounds alone**, knowing it
   is not a C3c route, is probably close to price-inert, and puts C1-2023 ST_GAS at its boundary?
   The PRECOMMIT's form, identification and gates are written and would need no redesign. **My
   recommendation: NO, not now** — it is a real object and it belongs on the successor list, but a
   four-shard span for a near-inert change with a named C1 risk is worse value than the two items
   in §10, and it will still be there afterwards. That is a recommendation, not a decision.
2. **Should C3c's route be re-opened on the LOCATIONAL / REAL-TIME side?** §6 and §8 say that is
   where the deficit is, and §6's instrument gap says the committed bundles currently cannot even
   measure it. This is the substantive question this session surfaces.

---

## 10. WHAT THE NEXT LANE SHOULD DO — routed, with the cost of each stated

1. **RE-RUN THE REACHABILITY BOUND PER ZONE, ON LONG ISLAND.** `nyiso242_tail_reachability`'s
   "unreachable by price formation" verdict is ISO-wide, and **88.9 % of the deficit is locational**.
   If LI carries little idle sub-$300 capacity in its own missed hours while the ISO carries GW,
   the bound never applied to these hours and **the locational question is wrongly closed**.
   **Cost: one keeper replay per year to get `dispatch/<year>_P1.parquet`, OR a zone column added
   to the `class_hourly` sidecar** (the cheaper and more durable fix — every future lane inherits
   it). Until one of those lands, this question is not answerable from a committed bundle.
2. **THE C3c DEFICIT IS A REAL-TIME OBJECT AND EVERY OFFER INSTRUMENT THE LANE FAMILY OWNS IS
   DAY-AHEAD.** Both DA offer legs — level (this session) and shape (nyiso-245) — are now measured
   and neither carries it. A successor needs an **RT** instrument (NYISO publishes RT genbids
   separately) or an **RT mechanism**, and should say which before designing anything.
3. **DO NOT re-propose the upper-tail dispersion as a C3c route** (rule 28(a) DO-NOT-REDO from this
   session). The object is real; its **window is not where the deficit is**, and **re-conditioning
   it onto the deficit's coordinate destroys it** (p90 21.974 → 0.930). Both halves are measured
   and committed.
4. **Unchanged and still open:** D-4 reads `passed=False` in every year (`reliability_floor ×
   ST_GAS`, `nyiso_gas_commitment_bridge × CC_REGULAR`) while C8 passes; the **G2 hydro loss**
   (Upstate_West ≤ $0 price fabrication) still needs a new candidate after nyiso-238 killed all
   four at zero LP; and `_hub_overlay_series`' missing daily branch remains **cross-ISO /
   owner-court** under rule 25.

---

## 11. ARTIFACTS

| path | gate | what |
|---|---|---|
| `scripts/probes/nyiso249_gdrift_mechanical.py` → `_nyiso249_gdrift_mechanical.json` | **G-DRIFT-M** | form 4 verified by execution, not by reading |
| `scripts/data/derive_nyiso_offer_level_dispersion.py` | **G-1** | the gas array is a parameter feeding BOTH roles |
| `scripts/probes/nyiso249_denominator_ladder.py` → `_nyiso249_denominator_ladder.json` | **G-2** | the 4-arm denominator ladder + level census + the exact arm-A check |
| `scripts/probes/nyiso249_window_tail_overlap.py` → `_nyiso249_window_tail_overlap.json` | **G-3** | coverage and exposure against the C3c gate's own quantities |
| `scripts/probes/nyiso249_deficit_coordinates.py` → `_nyiso249_deficit_coordinates.json` | **G-4** | where the deficit is: zone, month, hour, load/gas percentile |
| `scripts/probes/nyiso249_li_reachability.py` → `_nyiso249_li_reachability.json` | **G-5** | the per-zone bound + the sidecar zone-column gap |
| `results/calibration/_nyiso249_li_demand_bands.json` | **G-5** | LI demand vs LI supply; band mix in the missed hours |
| `scripts/probes/nyiso249_window_variants.py` → `_nyiso249_window_variants.json` | **G-6** | W1 / W2 / W3, each with its own coverage |

**Shards launched: none. Bundles produced: none. LP spent: none.** Total cost: one fleet-cache
rebuild (~4 min), one P-27 re-fetch (48 archives, **byte-identical** to the tracked record), and
seven probes.
