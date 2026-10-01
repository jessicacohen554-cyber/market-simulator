# PREREG nyiso-146b — TWO single-delta arms against the SAME registered control: the ONLINE-HOURS LSL state leg, and the RESERVE-DUTY CC offer split

**Written and committed BEFORE either arm is solved.** Session nyiso-146
(continued — the same session that pre-registered, solved, REJECTED and
registered the per-plant min-run A/B,
`RESULT-nyiso146-perplant-min-run-ab-2026-08-19.md`). Keeper at HEAD
unchanged: `2026-08-18-nyiso-144-layup-exclusion`. Holdout freeze ACTIVE —
2023/2024/2025 only, one bundle per arm (rule 16), arms sequential (rule 12).

**The control is already solved and registered**:
`2026-08-19-nyiso-146-control` (`results/calibration/nyiso146_control`, the
keeper recipe replayed at HEAD; its production verdict reproduces the
keeper's criterion-for-criterion, C3c bit-identical 2/0/5). Each arm is ONE
`scenario_config` field against it. The arms are INDEPENDENT levers for the
two frontier-blocking objects and are scored separately; neither's verdict
conditions the other's.

---

## ARM B — `nyiso_gas_bridge_online_hours` (the ercot141 LSL state leg, CC-scoped)

### B.1 The object and the NYISO evidence

CC over-cycling (nyiso-145 defect A). The nyiso-146 min-run A/B supplied the
NYISO-specific diagnosis: the floors delivered exactly and the starts did not
move, because every gap/extension floor covers only P0-OFF hours while
Bethlehem's fragmentation lives in P1's bid-cost pass shutting the plant
INSIDE P0-committed hours. This leg floors exactly that state: the LSL block
of a synchronized unit is must-take in EVERY online hour (the gap legs model
the restart DECISION; this models the committed STATE — the ercot141 charter
verbatim). Rule 25: the ERCOT verdict transfers nothing; this is NYISO's own
test on NYISO's own evidence.

**CC-SCOPED, and the scope is pre-registered reasoning, not a residual
choice**: the leg arms only the `gas_cc` detector call. The evidence is
combined-cycle conduct; NYISO's ST_GAS fleet cycles diurnally by its own
meter (Barrett p50 run 4 h) and carries NO over-cycling evidence — an
all-online-hours LSL floor on the always-on Ravenswood steamer alone would
manufacture ~2.0 TWh of state floor with no driver evidence (measured in the
first, unscoped prediction capture and rejected on it, BEFORE any solve).

**Zero new scalars** (rule 21): the level is the bridge's existing measured
CC min-load fraction (0.523), capped by the detector at the base tranche's
own capacity; no new parameter of any kind.

### B.2 Falsifiable predictions (control-side capture, deterministic floors)

From `_nyiso146_k2_prediction_nyiso_gas_bridge_online_hours.json`
(the same capture machinery as the min-run A/B; capture-basis, with the
known capture-vs-solve basis shift disclosed there — the per-leg totals are
therefore held to the REBASED prediction `captured_arm × (solve_ctl /
captured_ctl)`, the amendment discipline the first A/B established):

* gas_cc leg floor volume EXPLODES from a gap floor to a state floor —
  captured arm totals **17.3213 / 19.1247 / 17.6596 TWh** (vs control
  1.83/1.71/1.28). The gas_st leg is **byte-identical to control** in the
  capture (2517: 29.82/63.21/36.53 GWh unchanged; 2511: 0 unchanged) — the
  scope is itself a gate.
* Predicted per-plant (capture basis): 2539 floor 779→1,323 / 490→1,914 /
  485→1,905 GWh with union starts **62→40 / 31→9 / 35→16**; 7314 floor
  131→224 / 127→264 / 80→275 GWh, union starts 69→33 / 77→23 / 52→23;
  57185 301→2,682 / 268→2,546 / 198→2,512 GWh, union starts 39→2 / 4→1 /
  6→3. (Plant 2500's CC_REGULAR rows — the mixed Ravenswood facility —
  carry a ~963-975 GWh state floor; its plant series is online 100 % of
  hours in every year, so the floor sits under real dispatch.)
* Bethlehem P1 starts collapse toward the union counts (control P1 327/526/
  262 against 6-7 metered): the state floor makes P1-on ⊇ P0-on exactly, so
  the only surviving starts are the union blocks plus rare new economic
  runs in never-on hours.

**ADVERSE CASES, registered against interest:**
* **ADV-B1 — C8/forced-share.** The CC state floor's binding share will jump
  (control bridge binding 1.39/0.91/0.80 TWh). Predicted to stay under the
  30 % cap (binding-to-volume ratio ~0.7 on the control, CC_REGULAR class
  energy ~35-45 TWh), but a C8 breach that fails the rule-20
  provenance+shape escalation KILLS the arm.
* **ADV-B2 — trough prices RISE** (pinning the cheap LSL quantity makes the
  next rung marginal — the ercot141 "lifts the trough" direction). C3a must
  hold ±10 %; C3c reported, never gated, not reached back.
* **ADV-B3 — D-4 conduct.** The floor now binds in P0-on hours; a plant
  whose model on-share far exceeds its metered on-share could bind on
  metered-zero hours. Zero new D-4 failures is the gate.

### B.3 Kill gates (arm B)

* **B-K1 EXACTNESS** — exactly one differing field:
  `nyiso_gas_bridge_online_hours` False→True.
* **B-K2(a) FLOOR DELIVERY** — the arm's gas_cc leg volumes within **±5 %**
  of the capture predictions (17.3213 / 19.1247 / 17.6596 TWh; the band
  covers the measured 0.4-4.2 % capture-vs-solve P0 basis shift, and a
  state floor is LESS basis-sensitive than the gap floors — on-hours are
  stable where run boundaries are not); the arm's gas_st leg volumes within
  **±2 %** of the CONTROL SOLVE's own (scope gate); D-4 corroboration:
  2539's and 57185's bridge binding energy RISES every year.
* **B-K2(b) STARTS** — Bethlehem's P1 starts (0.05 × capacity, bundle
  hourlies) fall **≥60 % in every year**.
* **B-K3 OBJECT** — (a) 2539: arm starts < control AND median run length
  rises, all years; metered direction (327/526/262 → toward 6-7).
  (b) no-degrade cohort (the min-run prereg's table and 1.5×ctl_err+5
  bars, measured identically). (c) 7314: arm starts ≤ control (its floor
  and union starts both move toward metered).
* **B-K4 D-4/D-2 (K6′)** — zero NEW D-4 unit-conduct failures; the
  pre-registered CC forced-share rise escalates and clears only with zero
  new D-4 failures AND zero new D-1 misses; C8 PASS every year.
* **B-K5** — C1/C2/C3a/C3b/C4/C6/C8: no PASS→FAIL vs control. C3c the
  standing ledgered caveat, reported at full magnitude.
* **B-K6** — gate-side LOYO: B-K2(b)/B-K3(a) hold in each year separately.
  (Derive-side is vacuous: the leg introduces NO new measured value.)

**Promote criterion: B-K1–B-K6 clean (B-K4 may escalate and clear).**

---

## ARM C — `cc_reserve_duty_split` (the duty-role mirror split)

### C.1 The object and the identification

Merit-order inversion on capacity-only small CCs (nyiso-145 defect B):
Sterling **221×/128×**, Batavia **66×/105×**, Massena **25×/40×**, Allegany
**43×/33×** of EIA-923 net on the registered control's own bundles, model
on-shares 0.87-0.99 vs metered 0.01-0.06, ZERO floor involved. These plants
(the Seneca Power Partners fleet + peers) hold Gold-Book CRIS capacity while
essentially never selling energy; the LP sees only their competitive heat
rates. EIA-860 status reads `OP` (measured and refuted as a discriminator ex
ante) and none of them file EIA-923 Schedule 5 fuel costs (measured: zero
rows), so the admissible identification is the measured DUTY ROLE — the
`cc_intermediate_split` lineage, mirrored: that family flattens offers for
the measured HIGH-CF cohort; this steepens them for the measured RESERVE
cohort.

* **Membership** (frozen artifact, rule 23; mechanism-blind):
  `reserve_duty_cc_NYISO.csv` — plant-summed CAMPD on-share (or EIA-923
  pooled CF where no CEMS record exists — Allegany) **≤ 0.10**, a
  population-gap separator: the live-fleet distribution runs {0.012, 0.017,
  0.024, 0.025, 0.040, 0.047, 0.064} then a **2.7× gap** to {0.17 Pinelawn,
  0.22 Castleton, 0.34 Carr St, ...}. Qualifying set (7):
  **10620, 7784, 50744, 54593, 54592, 10621, 54034**. Carr Street and
  Pinelawn (the mild 2-3× cyclers) are deliberately NOT members — their
  over-run is an offer/commitment question, and membership would bury it
  (the nyiso-144 plant-7314 discipline).
* **Level** (zero new scalars, rule 21): the class curve's existing peak
  band, AS THE RECIPE RESOLVES IT: the cohort's whole dispatchable capacity
  becomes the peak band (`pct_mc = 0, pct_peak = 100 − pct_mr`), priced by
  the same resolution every CC peak band gets in this recipe.
  *(PLUMBING AMENDMENT, disclosed before the arm's VALID solve: the first
  solve of this arm was INERT — the `fleet_to_bins` frame seam was
  clobbered downstream in `bins_to_fleet` by the recipe's
  `offer_curve_by_group.pct_peaking`, `cc_peaking_per_plant` and
  `cc_duct_peaking` overrides (pct_peak 100 → 8 → 0), leaving dispatch
  byte-identical; the inert bundle is registered as a probe. The override
  now applies LAST in `bins_to_fleet` (the same supersession precedence
  `cc_duct_peaking` itself claims), verified in-process against the arm's
  own recorded `run_config`: the cohort collapses to one peak tranche at
  the recipe's CC peak multiplier — measured `offer["peak"] = 2.25×`, so
  Sterling prices at hr 19.26 ≈ $51/MWh in 2023, the level whose
  share-above was measured at 0.02-0.04 against 0.01-0.06 metered
  on-shares in the phase-0 table. No gate changes; C-K2's ≥80 % bars
  stand.)*
* **Why 1.55× is predicted sufficient — the model's own revealed merit
  cliff**: Carthage (hr 9.7, econ mc $26.6 in 2023) and Syracuse (9.55)
  dispatch at ~1 % on the control while Sterling (8.56, $23.7) dispatches
  92 % — a $3/MWh cliff. The peak routing moves every cohort plant's mc
  **$10-16 above** the cliff (Sterling $23.7 → $33.5 in 2023), far past the
  point where the model's own economics already hold identical plants at
  ~1 %.

### C.2 Falsifiable predictions

* Cohort model energy collapses: control 2023 GWh {Sterling 471, Massena
  550, Batavia 404, Allegany 509, Syracuse 25, Carthage 2.8, Rensselaer 19}
  ≈ 1.98 TWh phantom → predicted **≥80 % falls** for each of the four
  object plants in every year.
* The displaced energy re-dispatches WITHIN the class and imports — with
  Bethlehem (0.34× at control-2023) the natural absorber; its energy is
  predicted to RISE toward its EIA-923 net (reported, not gated).
* **ADV-C1** — C1 CC_REGULAR class volume moves by up to ~2 TWh; C1 must
  stay PASS. **ADV-C2** — upstate prices may firm slightly (the phantom
  cheap capacity leaves the merit order); C3a ±10 % holds. **ADV-C3** —
  Allegany/54034's small bridge floors vanish with their P0 runs (floor
  follows dispatch); D-2 attribution shrinks accordingly — zero new D-4.

### C.3 Kill gates (arm C)

* **C-K1 EXACTNESS** — exactly one differing field: `cc_reserve_duty_split`
  False→True.
* **C-K2 LIVENESS** — the arm's solve logs the armed cohort (7 plants,
  verbatim codes); each of {50744, 54592, 54593, 7784}'s model/EIA-923
  ratio falls by **≥80 %** vs the control in 2023 and 2024 (2025's
  preliminary vintage: reported, not gated — the C1 guard's own
  convention); an inert arm fails.
* **C-K3 NO-DEGRADE** — for every NON-cohort CC plant-year in the min-run
  prereg's baseline table: start-count error ≤ 1.5×control error + 5; C1
  stays PASS in every year.
* **C-K4 D-4/D-2 (K6′)** — zero new D-4 failures; no material class's
  forced share rises without clearing the two K6′ legs; C8 PASS.
* **C-K5** — C1/C2/C3a/C3b/C4/C6/C8: no PASS→FAIL vs control; C3c
  reported.
* **C-K6 LOYO** — derive-side, measured BEFORE this prereg was committed:
  membership is stable in all three 2-year subsets for all 7 members
  (worst case Rensselaer: pooled 0.064; drop-2023 0.074, drop-2024 0.080,
  drop-2025 0.036 — all ≤ 0.10) and no non-member enters (Pinelawn's best
  subset 0.16 > 0.10). Gate-side: C-K2 holds per-year (2023 and 2024
  separately).

**Promote criterion: C-K1–C-K6 clean (C-K4 may escalate and clear).**

---

## GOVERNANCE

* Both arms are registered on the dashboard whatever their outcomes
  (rule 15), the NYISO shard cells updated in this session (rule 28b);
  `cc_reserve_duty_split` is registered on the `offer_curve_by_group` row's
  def (the duty-role-split family home, rule 28c escape-hatch convention)
  and `nyiso_gas_bridge_online_hours` on the `gas_commitment_bridge` row's
  def (the bridge-leg convention).
* If BOTH arms clear their gates, a COMBINED candidate (control + both
  fields) is solved as the promotion candidate, scored on the same gates
  (each leg's own gates evaluated vs the same control; K1 measured as one
  delta against each single arm), and the promotion follows the keeper
  workflow (rule 22 D-5(b) re-key included). If only one clears, that arm
  is the candidate. If neither, both register as rejections.

## REPRODUCTION

```
python scripts/data/derive_reserve_duty_cc.py --iso NYISO
NYISO146_ARM_FIELD=nyiso_gas_bridge_online_hours \
  python scripts/probes/_nyiso146_k2_prediction.py

# arm B — control recipe + the online-hours leg
python scripts/run_calibration_full.py \
  --replay-bundle results/calibration/nyiso146b_armB_recipe \
  --out-dir results/calibration/nyiso146b_online_arm

# arm C — control recipe + the reserve-duty split
python scripts/run_calibration_full.py \
  --replay-bundle results/calibration/nyiso146b_armC_recipe \
  --out-dir results/calibration/nyiso146b_reserve_arm
```

(each recipe is the keeper's `meta.json` plus its ONE field, set in the
recipe rather than on the command line — the established replay convention.)
