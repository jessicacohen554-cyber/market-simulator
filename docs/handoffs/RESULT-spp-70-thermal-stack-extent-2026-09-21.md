# RESULT — SPP-70 (2026-09-21): the stack is NOT the object. It is $29–109 wide and the model never climbs it.

```
SESSION : spp-70        ISO: SPP        KEEPER: 2026-09-20-spp-67-yearown-rate (UNCHANGED)
RUNG    : 2026-09-20-spp-67-rung-yearown (UNCHANGED)
ASK     : attribute, in $/MWh, the "~$5 band" FINDING-spp-64 §6 measured on SPP's thermal
          stack, and decide whether widening it is the lever behind five of the rung's six
          failing rows.
RESULT  : (0) THE BRIEF'S PREMISE IS FALSIFIED, AND SPP-64 §6 WAS MEASURING A DIFFERENT
              OBJECT. SPP's thermal OFFER stack is p05->p95 = $29.33 (2020) to $109.07
              (2022) wide. §6's "~$5 band" is the CLEARING PRICE averaged over the hours
              each class runs -- a statement about the price duration curve, not the stack.
          (1) THE ATTRIBUTION (the deliverable). In 2020 the $29.33 is almost entirely
              cross-plant delivered FUEL PRICE ($17.49 isolate / $12.58 flatten) and the
              COAL TAKE-OR-PAY must-run tranche ($16.80 / $10.10). Heat-rate dispersion
              contributes $9.21 isolate but **-$0.18 flatten** -- removing it changes the
              width by nothing. The offer-curve band multipliers contribute EXACTLY ZERO.
          (2) WHY ZERO: SPP's keeper prices EVERY band of EVERY material class at the SAME
              0.93. Measured within-plant heat-rate spread for CC_REGULAR, CT_PEAKER and
              ST_GAS is **exactly 0.000** in all seven years. SPP's gas fleet has a tranche
              structure with no offer curve in it.
          (3) THE LEVER IS REFUSED AT ZERO LP, ON A PRE-SOLVE GATE, IN BOTH ADMISSIBLE
              FORMS -- and NOT because a residual moved (§6).
          (4) THE REASON IT CANNOT WORK IS MEASURED, NOT ASSERTED: 12-20 % of thermal
              capacity sits ABOVE the clearing price even in the top-10 load hours of every
              year. The LP never reaches the top of the stack it already has.
LP SPENT: ZERO. No shard launched, no bundle produced, no run registered, no cell moved.
```

---

## 0. Headline

> **SPP's thermal stack has plenty of vertical extent. What is missing is the price's
> ability to leave it.** In 2020 the model's price tops out at $36.21 against a stack whose
> most expensive available row offers **$68.36**, with **5.51 GW idle above the clearing
> price in the top-10 load hours**. Adding more extent above a price that never climbs
> there is inert by construction.

This does not overturn `FINDING-spp-64`. It **confirms and sharpens** it: §5 indicted the
one-zone topology as the common cause of every open SPP gate, and §6 offered the "$5 band"
as corroboration. The corroboration was measuring the price, not the stack. The indictment
stands and is now better supported — the price is compressed while the stack is not, which
is exactly what a missing congestion rent looks like from the supply side.

---

## 1. Phase 0, step 1 — the six failing rows, re-verified

`scripts/calibration_verdict.py` on the committed sidecars. Unchanged from the brief:

| # | criterion | year | value |
|---|---|---|---|
| 1 | C1 fuel-mix, COAL_PRB | 2022 | +9.95 TWh, share +3.0 pp |
| 2 | C3a mean LMP | 2020 | **+19.3 %** (band ±10 %) |
| 3 | C3b price shape | 2020 | NRMSE 0.273 |
| 4 | C3b price shape | 2021 | NRMSE 0.245 |
| 5 | C3b price shape | 2022 | NRMSE 0.207 |
| 6 | C4 dispatch corr, gas | 2022 | r = 0.96, NRMSE 0.327 |

Keeper span re-scores **CALIBRATED**, one ledgered C3c, C1 all 16/16 / free 12/12 — byte-unchanged.
DOF ledger `--check` on the committed bundle: **`free_parameters current`**, 5 entries / 3 residual.

---

## 2. Phase 0, step 2 — THE ATTRIBUTION

The LP's own offer array `mc_base`, rebuilt through the sanctioned `fleet_only` path
(`scripts/lib/bundle_fleet.reconstruct_bundle_fleet`), one interpreter per year (trap (b)).
Width is the capacity-weighted p05→p95 of annual-mean `mc` across thermal rows, weighted by
`pmax × mean availability` — the MW actually offered.

### 2a. The stack is wide, and its width tracks the gas price

| year | gas $/MMBtu | thermal GW | p05 | p50 | p95 | **p05→p95** |
|---|---:|---:|---:|---:|---:|---:|
| 2019 | 2.57 | 33.1 | 4.50 | 20.92 | 38.23 | **33.73** |
| **2020** | **2.03** | **32.0** | **4.50** | **19.91** | **33.83** | **29.33** |
| 2021 | 3.72 | 31.3 | 4.50 | 42.62 | 104.79 | **100.29** |
| 2022 | 6.45 | 32.6 | 4.50 | 48.20 | 113.57 | **109.07** |
| 2023 | 2.54 | 31.9 | 4.50 | 24.66 | 49.49 | **44.99** |
| 2024 | 2.19 | 31.2 | 4.50 | 24.14 | 50.74 | **46.24** |
| 2025 | 3.52 | 32.5 | 4.50 | 27.02 | 63.36 | **58.86** |

The $4.50 floor in every year is the **coal take-or-pay must-run tranche**, which offers at
VOM alone (its fuel is already bought). That is intended, not an artifact.

### 2b. Which construction supplies the width — `mc = HR × FP + VOM + residual`

**ISOLATE** = only that term keeps its per-row values (the width it can carry alone).
**FLATTEN** = only that term collapses to its capacity-weighted mean (the width lost by
removing it). Neither is a decomposition alone — the `HR × FP` product carries an
interaction — so both are reported and the bracket is stated rather than hidden.

| year | FULL | iso HR | iso FP | iso VOM | iso RES | flat HR | flat FP | flat VOM | flat RES |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2019 | 33.73 | 9.90 | **20.62** | 2.50 | 18.01 | **+0.30** | 16.93 | −0.50 | 11.01 |
| **2020** | **29.33** | 9.21 | **17.49** | 2.50 | 16.80 | **−0.18** | 12.58 | −0.72 | 10.10 |
| 2021 | 100.29 | 21.22 | **85.99** | 2.50 | 17.59 | +4.30 | 78.06 | −1.00 | 10.56 |
| 2022 | 109.07 | 24.90 | **85.26** | 2.50 | 20.19 | +9.47 | 83.24 | −1.00 | 12.21 |
| 2023 | 44.99 | 15.08 | 22.18 | 2.50 | 20.38 | +8.97 | 22.21 | −0.13 | 11.85 |
| 2024 | 46.24 | 14.95 | 24.44 | 2.50 | 17.66 | +9.44 | 25.34 | −1.25 | 11.04 |
| 2025 | 58.86 | 17.64 | 37.07 | 2.50 | 18.78 | +8.46 | 35.95 | −1.00 | 12.41 |

Answering the brief's four candidates directly, in $/MWh, for **2020**:

| candidate | verdict | measured |
|---|---|---|
| **(c) one gas price for every gas unit** | **FALSE, and it is the LARGEST contributor** | delivered gas p05→p95 spans **$1.477→$3.151/MMBtu** across **55 distinct** plant prices = **$14.32/MWh** at the fleet median HR. `gas_plant_monthly_fuel_pricing=True` prices 410 rows from their own plant and gap-fills 835 from nearby plants; `gas_price_override = 2.03` is an anchor near the p50 ($2.187), not a flat price. |
| **residual (not in the brief's list)** | **the coal take-or-pay tranche, second largest** | the residual term is **exactly 0.00 on every gas row and every coal econ row**; it is −$16.54 on COAL_PRB `mustrun` and −$27.03 on COAL_LIGNITE `mustrun`. Carbon price is 0. |
| **(a) heat-rate spread too tight** | **NOT the constraint** | isolate $9.21, but **flatten −$0.18** — with fuel-price dispersion present, removing HR dispersion entirely changes the width by nothing. |
| **(b) VOM flat across classes** | **TRUE but immaterial, and it works BACKWARDS** | isolate $2.50 in every one of the seven years; flatten **−$0.72**, i.e. flattening VOM makes the stack *wider* — VOM is negatively correlated with fuel cost (coal $4.50 / CC $2.00). |
| **(d) tranche band shares** | **the shares are fine; the band PRICES are the defect** | §3. |

---

## 3. THE DEFECT THE ATTRIBUTION FINDS — SPP's gas fleet has no offer curve

Within-plant spread across a plant's own tranches, capacity-weighted across plants:

| class | 2020 GW | bands/plant | **within-plant HR spread** | **within-plant mc spread** |
|---|---:|---:|---:|---:|
| COAL_PRB | 11.16 | 5.26 | 0.729 | **$15.26** (94 % of its own mean) |
| COAL_LIGNITE | 1.50 | 5.00 | 0.729 | **$20.86** (117 %) |
| **CC_REGULAR** | **7.16** | **3.77** | **0.000** | **$0.00** |
| **CT_PEAKER** | **8.71** | **3.65** | **0.000** | **$0.00** |
| **ST_GAS** | **2.91** | **4.00** | **0.000** | **$0.00** |

Per-band capacity-weighted `mc / HR / GW`, 2020 — the four gas bands are the same number:

| class | committed | econ-lo | econ-hi | peak |
|---|---|---|---|---|
| COAL_PRB | 19.30 / 9.63 / 3.3 | 19.61 / 9.76 / 2.6 | 19.61 / 9.76 / 2.1 | 19.58 / 9.69 / 0.2 |
| CC_REGULAR | 16.69 / 6.67 / 2.5 | 17.08 / 6.81 / 2.0 | 17.08 / 6.81 / 2.0 | **16.26** / 6.73 / 0.7 |
| CT_PEAKER | 25.70 / 9.58 / 0.9 | 26.45 / 9.67 / 3.8 | 26.45 / 9.67 / 3.4 | **26.36** / 9.66 / 0.6 |
| ST_GAS | 24.86 / 9.58 / 0.6 | 25.12 / 9.58 / 1.0 | 25.12 / 9.58 / 1.0 | **25.06** / 9.58 / 0.4 |

*(the residual cross-band differences are plant COMPOSITION, not slope — the within-plant
spread above is exactly zero. The `peak` band is the CHEAPEST of the four in all three gas
classes.)*

**The cause, located.** The keeper's `calibration_flags.offer_curve_overrides` sets
`{committed, econ_low, econ_high, peak} = 0.93` on **ten classes** — every material gas and
coal class. Since `bins_to_fleet` builds each band as `base_hr × mult`, four equal
multipliers give four equal heat rates. The structural shares are untouched
(`pct_peaking` 8 / 7 / 15 %, `econ_low_share` 0.50–0.55 — all at their generic values), so
the tranche machinery still partitions the plant; only the price shape is gone.

**This is not the shipped default.** `pipeline/backcast_config.py` ships CC_REGULAR at
`0.92 / 1.06 / 1.27 / 2.25` and CT_PEAKER at `1.55 / 1.27 / 1.98 / 13.15`. The SPP ISO
deep-merge `_SPP_OFFER_CURVE` flattens **coal only**, to the identity 1.0, and says so:
*"only the price SHAPE across the tranches is flattened to SRMC"*. **Gas was flattened by the
run recipe, not by that code block** — and flattened to 0.93 rather than to the identity, so
it carries a uniform 7 % heat-rate discount on top.

**A gas plant does not offer its min-load block, its economic range and its peak-fire block
at the same heat rate.** That is a real structural defect and this lane names it rather than
burying it. It is also, measurably, **not the object behind the six failing rows** — §4–§5.

---

## 4. WHY NO BAND MULTIPLIER CAN REACH THE FAILING ROWS — the stack is never climbed

Per hour, the thermal MW available at a `mc` **above** the clearing price (the headroom the
LP declined to use), from the same reconstruction joined to the bundle's committed P1 prices:

| year | top-10 load hours | top-100 | top-500 | all hours | hours with < 1 GW headroom | max offer | max price |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019 | **6.29 GW (14.9 %)** | 5.17 (12.5 %) | 6.04 (15.1 %) | 13.69 (41.4 %) | 19 / 8760 | 100.98 | 181.28 |
| **2020** | **5.51 GW (13.1 %)** | 6.12 (15.0 %) | 7.29 (18.4 %) | 14.52 (45.4 %) | **7 / 8760** | **68.36** | **36.21** |
| 2022 | **8.17 GW (18.8 %)** | 8.39 (19.5 %) | 9.36 (22.3 %) | 16.24 (49.8 %) | 7 / 8760 | 1673.24 | 1102.11 |
| 2025 | **5.33 GW (12.2 %)** | 8.36 (20.0 %) | 9.50 (23.6 %) | 14.89 (45.8 %) | 10 / 8760 | 234.93 | 996.20 |

**The model is not capacity-short.** In every year, in its own peak hours, it leaves
12–20 % of its thermal fleet unused above the clearing price. In 2020 it leaves $32/MWh of
unused vertical extent above the highest price it produces all year.

---

## 5. SIZING THE LEVER ANYWAY — a validated zero-LP merit-order reconstruction

Because "inert" should be measured, not inferred. Per hour, sort the LP's own rows by
`mc_base[:, t]`, cumulate `pmax × availability`, read the `mc` at the thermal energy the LP
actually served (committed `class_hourly`). **Validated against the committed P1 price
first** — a counterfactual is quoted only where the instrument reproduces the incumbent:

| year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| r | +0.918 | +0.840 | +0.979 | +0.746 | +0.853 | +0.560 | +0.727 |
| mean err $/MWh | −0.69 | −0.01 | +2.14 | +1.98 | +0.90 | +0.52 | +0.95 |
| MAE $/MWh | 0.75 | 1.47 | 3.55 | 4.07 | 2.27 | 2.92 | 2.37 |

Two arms, gas classes only (SPP's coal keeps the keeper band in both, so the gas question is
isolated):

* **IDENTITY 1.0** — the rule-25-clean move: remove the uniform 7 % discount, import no
  other ISO's shape. Still flat, so it adds no slope.
* **GENERIC** — the shipped non-PJM/non-ERCOT curve, *including* CT_PEAKER `peak = 13.15`.
  **Rule 25 `[R-ISO-SCOPE]` inadmissible for SPP** (it is ERCOT/PJM-fitted lineage); quoted
  as the family's **upper bound**, never as a proposal.

### 5a. C3a (±10 %) under each arm — the pre-solve gate

| year | model | actual | **now** | **IDENTITY** | **GENERIC** |
|---|---:|---:|---|---|---|
| 2019 | 22.46 | 20.85 | +7.7 % PASS | **+11.3 % FAIL** | +26.7 % FAIL |
| **2020** | 19.71 | 16.52 | **+19.3 % FAIL** | **+23.5 % FAIL** | **+39.9 % FAIL** |
| 2021 | 38.36 | 37.36 | +2.7 % PASS | +8.8 % PASS | +32.0 % FAIL |
| 2022 | 42.31 | 44.09 | −4.0 % PASS | +1.5 % PASS | +19.2 % FAIL |
| **2023** | 25.16 | 25.13 | +0.1 % PASS | +4.7 % PASS | **+25.8 % FAIL** |
| **2024** | 25.05 | 25.45 | −1.6 % PASS | +3.1 % PASS | **+29.9 % FAIL** |
| **2025** | 28.97 | 28.60 | +1.3 % PASS | +6.7 % PASS | **+33.0 % FAIL** |

### 5b. And neither arm touches 2020's tail

Model hours > $100 in the reconstruction, 2020: keeper **0**, IDENTITY **0**, GENERIC **0** —
against an actual 2020 with **88 h > $100 and 23 h > $200**. The GENERIC arm prices
CT_PEAKER's peak band at $261/MWh in 2020 and it is *still* never marginal, because that band
is 0.61 GW sitting at the top of a stack with 5.51 GW of headroom beneath it. §4 predicted
this; the counterfactual confirms it.

**THE ARITHMETIC CEILING.** At 2020's $2.03/MMBtu gas, offering $200/MWh needs an effective
heat rate of **96.8 MMBtu/MWh**. The p99.5 gas heat rate in SPP's whole 2020 fleet is
**11.33**. A marginal-cost stack reaches a $200 hour only through a band multiplier near 10×
— and the one arm that has one (GENERIC, 13.15) cannot deploy it because the LP stops
5.5 GW short.

---

## 6. THE VERDICT, AND WHY IT IS NOT "THE RESIDUAL DIDN'T MOVE"

Rule 1 `[R-STRUCT]` forbids rejecting a structurally-correct mechanism because the fit got
worse. This lane does **not** do that, and the distinction is load-bearing:

1. **The GENERIC arm is refused on RULE 25, before any score is read.** It is ERCOT/PJM
   fitted lineage; SPP's own code block already declined it for coal on exactly that ground.
   Its C3a column is reported for completeness, not as the reason.
2. **The IDENTITY arm is refused because it is not the repair.** It removes a discount
   without adding a slope — within-plant spread stays exactly 0.000 — so it fixes nothing
   structural while costing 2019's C3a PASS. Refusing a move that changes only the level is
   rule 1's *first* half, not its second.
3. **The structural repair — a measured, SPP-specific rising curve — is NOT refused. It is
   SEQUENCED**, and §4 is the reason: its effect is bounded by a stack the LP never climbs.
   Arming it now would spend seven shards to move a price band that is already 5.5 GW of
   headroom away from where the repair acts.
4. **Rule 14 `[R-ACCURATE]` names what the flat 0.93 is doing.** *"If swapping a hand
   estimate for real data makes the backcast worse, that is a signal that something else in
   the model is miscalibrated and the estimate was silently compensating for it."* Removing
   the discount (IDENTITY) raises the mean by $0.69–$2.45 and breaks a year. **The uniform
   7 % discount is a fleet-wide level suppression holding the body down to the right annual
   mean** — and `FINDING-spp-64` §1 already measured why the body has to carry the mean:
   with no congestion rent and 167 negative hours against 1,018, there is nothing else to
   carry it.

**So the offer-curve family is sequenced BEHIND R-bc**, on the same reasoning
`FINDING-spp-64` §9 used to sequence R-ba — and now with a measured bound rather than an
inference. The prediction that follows, recorded so a successor can score it: once R-bc
lands a price-forming curtailment and the negative hours and congestion rent appear, the
body falls, the 7 % discount stops being load-bearing, and the offer-curve repair becomes
affordable. **Until then it is a correct repair with no room to act.**

---

## 7. What this lane got wrong, and corrected before publishing

The first counterfactual used **hand-transcribed** generic multipliers for CT_PEAKER
(`1.00/1.00/1.20/3.00`) and ST_GAS (`1.00/1.00/1.15/2.20`). The real shipped values are
`1.55/1.27/1.98/**13.15**` and `0.81/1.05/1.40/4.20`. The error **understated the lever by
roughly half** (2020 mean +1.99 vs the correct +3.39) and would have understated its tail
entirely. Caught by reading the source rather than trusting the transcription, re-run on all
seven years, and every number in §5 is from the corrected pass. Recorded here because a
sizing instrument is only worth its inputs.

---

## 8. Governance

* **Rule 1 `[R-STRUCT]` / 13 / 14** — §6. No mechanism selected, kept or rejected because a
  residual moved; the flat curve is named as a structural defect even though repairing it
  scores worse, and the compensation it is performing is named rather than absorbed.
* **Rule 19 `[R-ONE-MECH]`** — enumeration of what already prices an SPP gas tranche:
  `offer_curve_by_group` (uniform 0.93), delivered F923 plant-monthly fuel price, class VOM.
  `pmin_mw` / `min_run_hours` / `min_down_hours` / `startup_cost_per_mw` are 0 on every SPP
  fossil unit (SPP-44/63, unchanged). Nothing stacks; nothing was added.
* **Rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`** — zero `ScenarioConfig` fields added, zero
  tunables introduced, zero free parameters proposed. Keeper ledger re-checked **current**
  (5 entries / 3 residual).
* **Rule 25 `[R-ISO-SCOPE]`** — nothing transferred. The GENERIC curve is quoted as an
  upper-bound instrument and explicitly refused as a proposal for exactly this reason.
* **Rule 28 `[R-MECH-MATRIX]`** — `offer_curve_by_group` stays **`K`** (the keeper's curve is
  unchanged); its evidence line gains this lane's attribution, the zero within-plant spread,
  and the two-arm pre-solve refusal. `internal_congestion_split` stays **`U`**, annotated
  with §4/§6. No cell moved.
* **Rule 29 `[R-SCREEN]` clause 0 / (b)** — every arm had a computable pre-solve gate and
  failed it, so no LP was spent. Form 4 (the keeper's committed bundle as control) is valid
  and was verified **empirically** rather than by code audit: the keeper solved at
  `40eeb43a`, this lane reconstructs at HEAD with fourteen solve-path files changed between,
  and in both bundles **no class ever dispatches above the reconstructed availability in any
  hour (worst excess 0.0 MW)**, with several classes touching it exactly.
* **Rules 31 `[R-RETAIN]` / 32 `[R-SHARD]` (a)** — the parent solved nothing, launched no
  shard, produced no bundle, deleted nothing. §9.

---

## 9. Promotion question (rule 31 `[R-RETAIN]`) — asked, not pre-empted

**There is nothing to promote.** Zero LP was spent, no bundle exists, no keeper or rung file
was touched, and no gitignored artifact exists that would die with this container. The keeper
`2026-09-20-spp-67-yearown-rate` and the rung `2026-09-20-spp-67-rung-yearown` are
byte-unchanged; SPP's headline stays **CALIBRATED** on its train tier.

**The open question this lane does NOT decide** remains SPP-68's:
`2026-09-20-spp-68-ceiling-span` and `2026-09-20-spp-68-rung-ceiling` are still registered
as non-keeper runs, so `audit_keepers --iso SPP` reports **2 E13 failures by design**. Not
this lane's promotion question; not pruned here.

---

## 10. Probes committed (all zero-LP, all re-runnable)

| script | what it does |
|---|---|
| `scripts/probes/_spp70_stack_extent_phase0.py` | per-year `fleet_only` extraction of `mc_base` / `fuel_prices` / row labels (one interpreter per year, trap (b)) |
| `scripts/probes/_spp70_stack_extent_report.py` | the reducer — tables A (stack), B (attribution), C (where the width lives), D (per-class), E (fuel dispersion) |
| `scripts/probes/_spp70_headroom.py` | §4, capacity above the clearing price per hour |
| `scripts/probes/_spp70_meritorder_counterfactual.py` | §5, validated merit-order reconstruction + the two arms |
| `scripts/probes/_spp70_fidelity.py` | §8, the empirical G-DRIFT check (committed dispatch vs HEAD-reconstructed availability) |

---

## 11. What this does NOT establish

* **It does not measure the LP's hourly marginal cost under a counterfactual solve.** §5 is a
  merit-order reconstruction; it ignores transmission, storage, ramp and min-gen. It is
  validated against the incumbent (r 0.56–0.98, MAE $0.75–4.07) and is a **sizing**
  instrument, not a substitute for a solve. Its verdict is safe only because the gate it
  fails is failed by a wide margin in every year.
* **It does not price SPP's real offer behaviour.** No SPP energy-offer corpus was read; the
  within-plant slope a measured repair would need is not derived here. That derivation
  (`measured_ct_heat_rates` / `measured_cc_heat_rates`, both **`U`** for SPP) is the
  successor's, and it should be done **after** R-bc, not before.
* **It does not re-open R-ba.** The ST_GAS/CT_PEAKER inversion is untouched and still
  bounded exactly as `FINDING-spp-64` §9 left it.
* **It says nothing about any other ISO.** Every number is SPP's own, from SPP's own bundles.
