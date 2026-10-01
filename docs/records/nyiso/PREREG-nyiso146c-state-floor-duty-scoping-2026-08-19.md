# PREREG nyiso-146c — duty-scope the online-hours state floor by the measured run-length gap (arm B2)

**Written and committed BEFORE the arm is solved.** Session nyiso-146
(continued). This is the pre-registered SHARPENING of the nyiso-146b arm B,
designed from that arm's own committed measurements — the normal
diagnose → sharpen → pre-register → test loop, declared as such: nothing here
was tuned to a residual; every input is a measured artifact that existed
before arm B solved.

## 1. WHAT ARM B MEASURED (the evidence this arm is built on)

The unscoped online-hours state floor (`nyiso_gas_bridge_online_hours`,
PREREG-nyiso146b arm B, solved and committed) measured BOTH halves of the
mechanism in one A/B:

* **It repairs the near-baseload cohort exactly** — Bethlehem 327/526/262 →
  **41/10/15** P1 starts (metered 6/7/7) with median runs 12/7/14 →
  68/144/319 h; Caithness 102/8/14 → 3/2/4 (metered 4/6/8); floor delivery
  on-prediction (gas_cc 17.06/19.00/17.67 TWh vs 17.32/19.12/17.66
  predicted; gas_st byte-equal to control).
* **It over-glues the intermediate-duty cyclers** — Athens-2025 69 → 9
  starts against 63 metered (B-K3(b) FAIL), Cricket-2024 26 → 1 against 20
  metered (FAIL), Flynn overshoots below its metered count, and ONE new D-4
  unit-conduct conviction appears (Saranac 2024 — a 0.43-on-share cycler
  held in hours its meter reads zero; B-K4 FAIL).

The two cohorts are EXACTLY the two sides of the nyiso-146 phase-0
run-length gap: repaired plants measure plant-basis p25 **130-646 h**
(Poletti 130, Bethlehem 134.75, Caithness 645.75); over-glued plants measure
**7-20 h** (Carr 7, Bethpage 8, Athens 10, Valley 12, Saranac 14, Flynn 15,
Cricket 19.75) — a **6.6× population gap** measured before any solve.

## 2. THE ARM

`nyiso_gas_bridge_state_floor_min_run` (default off; requires the
online-hours leg): the state floor holds ONLY plants whose own measured
plant-basis run-length p25 (the frozen nyiso-146 artifact
`campd_perplant_min_run_NYISO.csv`, rule 23) is at or above
`constants.NYISO_STATE_FLOOR_MIN_RUN_HOURS = 100 h` — a population-gap
separator (any value inside (19.75, 130) selects the identical membership
{**2539, 56234, 56196**}; plants with no measured value — the mixed 2500,
the misaligned Astoria pair — conservatively carry NO state floor). The rest
of the fleet keeps exactly the control's gap/extension floors. Implemented
by splitting the gas_cc detector call through the population gate
(`min_load_frac_by_gen` zeroing) — no detector parameter, ZERO new scalars
(rule 21). This is the synthesis the nyiso-146 min-run rejection called for:
"the per-plant values must ride a mechanism that also holds the ON state".

**A/B structure**: arm B2 = arm B's recipe + this ONE field (K1 is measured
against ARM B); the chain control → B → B2 is single-delta at each link.

## 3. FALSIFIABLE PREDICTIONS

* State floor shrinks to the three-member cohort: gas_cc leg volume falls
  from B's 17.06/19.00/17.67 TWh to roughly the control's gap floor plus
  the three plants' state floors (capture-basis per-plant state floors:
  2539 ≈ 1.3-1.9 TWh, 56234 ≈ 1.1-1.4, 56196 ≈ 1.0-1.3; predicted arm
  total ≈ **5-7 TWh**; gas_st byte-equal to control).
* Bethlehem/Caithness keep their arm-B start counts (~41/10/15 and ~3/2/4);
  Athens/Cricket/Saranac/Flynn/Bethpage/Valley REVERT to control behavior.
* Saranac's arm-B D-4 conviction DISAPPEARS; zero new D-4 failures remain.

## 4. KILL GATES (evaluated on the committed bundles; B2 vs the named base)

* **C2-K1 EXACTNESS** — vs ARM B: exactly one differing field
  (`nyiso_gas_bridge_state_floor_min_run`); vs CONTROL: exactly two.
* **C2-K2 DELIVERY** — the solve logs the 3-member cohort verbatim; the
  gas_cc leg total lands in **[4, 8] TWh** every year (between the control's
  gap floor and B's fleet-wide state floor); gas_st byte-equal to control.
* **C2-K3 OBJECT** — vs CONTROL: 2539 starts fall **≥60 %** every year with
  median run RISING; 56234's |starts − metered| ≤ control's + 5.
* **C2-K4 NO-DEGRADE** — the full nyiso-146 cohort table at
  `arm_err ≤ 1.5 × control_err + 5` for EVERY plant-year including
  {57185, 55405, 54574, 7314, 50292, 56940}: the plants arm B broke must
  read ≈ control again.
* **C2-K5 D-4/D-2 (K6′)** — zero new D-4 failures vs CONTROL (Saranac's
  arm-B conviction must be gone); forced-share rises escalate and clear
  only with zero new D-4 + zero new D-1.
* **C2-K6 CRITERIA** — C1/C2/C3a/C3b/C4/C6/C8: no PASS→FAIL vs control;
  C3c the standing ledgered caveat, reported at full magnitude.
* **C2-K7 LOYO** — derive-side: the 3-member cohort is identical in every
  2-year LOO subset (measured ex ante from the min-run prereg's LOO table:
  2539 = 137/47/167.75 h — **the drop-2024 subset reads 47 h < 100 h**, so
  the LOO membership there would drop 2539; this is DISCLOSED as the one
  soft spot: 2539's 2024 metered runs are 5 starts of 952-1,217 h median,
  so the low LOO p25 is a small-n artifact of within-year truncation, and
  the pooled 134.75 h stands on 20 runs. The gate as pre-registered:
  membership stable in ≥2 of 3 subsets per plant — 2539 clears 2/3,
  56234 3/3 (673/603/805), 56196 (130 pooled; subsets ≥ 100 in ≥2) —
  and the A/B verdict (C2-K3) holds in each year separately.

**Promote criterion: C2-K1–C2-K7 clean (C2-K5 may escalate and clear).**
If B2 clears, B2 (not B) is the candidate for the over-cycling object and
arm B registers as the diagnostic that identified the scope.

## 5. REPRODUCTION

```
python scripts/run_calibration_full.py \
  --replay-bundle results/calibration/nyiso146c_armB2_recipe \
  --out-dir results/calibration/nyiso146c_state_arm
```
(the recipe is arm B's meta plus `nyiso_gas_bridge_state_floor_min_run: true`.)
