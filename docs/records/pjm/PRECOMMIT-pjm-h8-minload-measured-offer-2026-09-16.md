# PRECOMMIT (pjm-h8) — the MIN-LOAD measured-offer arm

**Session** `pjm-h8` · **ISO** PJM · **Date** 2026-09-16 · **Base** `origin/main` @ `8b9b32e4`
**ZERO LP IN THE PARENT** (rule 32 `[R-SHARD]` (a)). Every number below is
`run_year(fleet_only=True)` on the keeper's own `meta.json` recipe plus direct calls to the
real markup builder — the rule 29 `[R-SCREEN]` clause-0 path.
**PJM keeper `2026-09-11-pjm-d4-4-gasoutage`: CALIBRATED, 8/8, zero caveats — UNTOUCHED**
(re-verified at HEAD this session under HEAD's diagnostics generator).

Chartered by the **OWNER RULING 2026-09-16**, which (a) re-opened the pjm-142 frontier for
the min-load offer basis and (b) declined to promote the pjm-h7 joint arm. The frontier's
own closure note names the re-opening condition — *"a NEW defect or a NEW measured
identification with its own charter"* — and
`docs/FINDING-pjm-h8-coal-minload-is-the-undisciplined-offer-surface-2026-09-16.md` is that
identification. This document is written **before any solve** and carries every number the
lane will cite.

---

## 1. THE ARM

`pjm_offer_midcurve_minload_segments = ("LONG_RUN",)` — PJM's **already-armed** measured-offer
surface is extended to the min-load rungs (`mustrun` / `committed`) of the LONG_RUN segment,
in **LEVEL form**.

**Why LEVEL and not the floor the rest of the surface uses (rule 19 `[R-ONE-MECH]`).** Those
rows' bids are currently set by the coal take-or-pay / passthrough construction — a **cost**
argument (the fuel is already bought, so marginal cost ≈ VOM). A *floor* would leave that
construction live in every hour it exceeded the measured level, i.e. two mechanisms setting
one row. **LEVEL replaces it**: the bid IS PJM's own measured offer, one mechanism per row.
The existing `peak_segments` extension is priced the same way for the mirror-image reason.

**Non-selective within the segment (pjm-h5's objection, honoured).** The scope is the
**segment**, never a class: both COAL and ST_GAS min-load rungs move, and **ST_GAS's move
DOWN** (it sits at 1.217-1.556 of measured). A coal-only form is the rule-1 `[R-STRUCT]`
selection pjm-h5 refused and the `offer_curve_by_group` DO-NOT-REDO note forbids.

**`sync` is NOT in scope, and that is the choice that does NOT flatter the residual.** PJM
coal's `sync` rung sits at within-plant share **0.871** — ABOVE the econ band — and reads
**1.31 / 1.40 / 1.33×** measured. It is a top-of-curve rung, not min-load. Repricing it in
LEVEL form would make coal **cheaper** and push COAL_BIT the other way; it is excluded on the
structural definition of the min-load block, stated here so the scope cannot be read as
selecting the rungs that help.

## 2. THE OPERAND IS MEASURED, AND NOTHING IS SWEPT (rule 21 `[R-DOF]`)

**Zero free parameters. Zero scalars. No value is chosen at all.** The arm sets a scope, and
the prices come from `data/raw/_validation-source/pjm_offer_midcurve_condbinned.json` — PJM
DataMiner2's `energy_market_offers` feed, 36 month-files, 2023-2025, capacity-weighted
medians, multipliers only (the prices carry a redistribution restriction), frozen against
residuals under rule 23 `[R-FROZEN-DERIVE]` and **already trusted by this keeper** for coal's
`econ` and `peak` rungs. Rule 13's forward test is met: the surface is a formulaic input keyed
on a forward-native net-load percentile and a delivered-gas series, so it regenerates for a
forecast year.

**ONE new `ScenarioConfig` field**, `pjm_offer_midcurve_minload_segments` (default `None`,
PJM-gated, byte-inert flag-off): registered in `_CACHE_KEY_OPTIONAL_FIELDS` with its frozen
declared default, and registered on its family row `pjm_midcurve_belt` in the base mechanism
matrix (rule 28 `[R-MECH-MATRIX]` (c), the sub-scalar escape hatch). `check_cache_key_registration`
and `check_mechanism_matrix` both PASS at HEAD.

## 3. PHASE 0 — ZERO LP, THREE YEARS, ALL GATES ALREADY MEASURED

`scripts/probes/_pjm_h8_minload_arm_phase0.py`: the fleet is built ONCE per year and the real
`build_pjm_offer_midcurve_conditional_markup` is called TWICE (control scope, arm scope) and
the markups differenced — the `pjm121_level_form_precheck` pattern, needed because the markup
is a **P1** `mc_bid_adjust` that a `fleet_only` build cannot show.

### 3.1 G-1 CONFINEMENT — **PASS, all three years**

136 / 137 / 140 rows move. Classes **exactly** `{COAL, ST_GAS}`; bands **exactly**
`{mustrun, committed}`; **zero** stray rows and **zero** expected-but-unmoved rows, asserted
in the probe rather than eyeballed.

### 3.2 G-2 IDENTITY — **PASS, all three years, at MACHINE PRECISION**

On every moved row the resulting P1 bid **is** the measured target:
`max |mc_base + markup − measured_target|` = **7.1e-15 / 1.4e-14 / 2.8e-14**. The LEVEL form
installs PJM's own published offer exactly — not approximately.

### 3.3 G-3 MAGNITUDE — the pre-solve table, **and the floor coverage that reframes it**

| yr | class | band | MW | cap-wtd Δ$/MWh | **floored share** |
|---|---|---|---:|---:|---:|
| 2023 | COAL | mustrun | 14,062 | **+20.14** | **84.4 %** |
| 2023 | COAL | committed | 12,550 | **+6.72** | **0.7 %** |
| 2023 | ST_GAS | committed | 2,432 | **−8.45** | 5.6 % |
| 2024 | COAL | mustrun | 14,062 | +17.94 | 86.2 % |
| 2024 | COAL | committed | 12,550 | +5.38 | 3.1 % |
| 2024 | ST_GAS | committed | 2,436 | −9.36 | 9.7 % |
| 2025 | COAL | mustrun | 14,198 | +18.94 | 85.7 % |
| 2025 | COAL | committed | 12,550 | +5.43 | 2.4 % |
| 2025 | ST_GAS | committed | 2,436 | **−22.84** | 8.5 % |

**THE FLOOR COLUMN IS THE POINT, and it CORRECTS this lane's own FINDING §1-§2.** That
document called the `mustrun` band "the object" on its 269,727 $-MW price gap. Measured here,
**84-86 % of that band is forced by `min_gen`** — so most of its repricing is an objective
constant that cannot change dispatch. The `committed` band is **0.7-3.1 %** floored, i.e.
essentially fully economic. **The dispatch-relevant move is the committed band alone**, and
PJM's own offers put it at **+6.72 $/MWh** against the **+17.66** pjm-h6 applied.

Effective (unfloored) coal footprint: mustrun 20.14 × 14,062 × 0.156 ≈ **44,180 $-MW** plus
committed 6.72 × 12,550 × 0.993 ≈ **83,742** = **~127,900 $-MW**, against h6's ~220,000 —
**about 58 % of h6's effective push.**

## 4. THE SCREEN — 2023, named on FOOTPRINT before the solve

**Screen year 2023**, pre-registered in the FINDING (§8.3) **before this arm was built**: it
is the maximum of the min-load gap footprint (385,579 > 2025's 336,430 > 2024's 326,706),
which is the mechanism's own measured footprint per rule 29 clause (1) — **never** the
residual. (It is not the largest-residual year either: that is 2020.)

### 4.1 G-CTRL — **form 4, NO CONTROL SOLVE IS SPENT**

The pjm-h6/h7 2023 control is committed on `origin` with its full per-plant layer and h6
measured that it reproduces the keeper (COAL_BIT 105.152 vs the keeper's scored 105.125, gap
0.027 TWh; C1 **16/16**, the keeper's committed headline exactly).

**G-DRIFT** from that control's sha `46c5702d` to this PRECOMMIT's base `8b9b32e4`. The two
commits pjm-h7 audited (`3857d801` coal-stocks intake, zero importers; `f2191f5d` NWPP
refactor where `ba_codes("PJM") == ("PJM",)` makes `.isin(codes)` identical to `== code`, plus
an eGRID repair plant PJM's fleet carries 0 rows for) remain **INERT by measurement**. The
only solve-path change since is **this lane's own**, and it is inert by construction at the
control's config: the new field defaults to `None`, the `minload_scope` set is then empty, and
the targeting predicate's added disjunct `minload_targeted` is identically `False` — verified
empirically, since the probe's control leg calls the *patched* builder and reproduces the
unpatched markup with **zero** moved rows outside the arm scope (G-1, three years).
**All hunks INERT ⇒ form 4 is valid and the screen spends ONE LP.**

### 4.2 THE GATE — pre-registered, STRUCTURAL, STOP-ONLY, never read on the target residual

The arm proceeds past the screen only if ALL hold. The gate **may kill the arm; it may never
promote one**; it contributes to no determination.

* **G-1 confinement** — §3.1. *(Already PASS, three years.)*
* **G-2 identity** — §3.2. *(Already PASS, three years, machine precision.)*
* **G-3 SIGN/MAGNITUDE — the pre-registered INTERVAL**, bounded on both sides by numbers that
  are **already measured** rather than assumed (the pjm-h7 method note):

  > **78.834 < COAL_BIT(arm) < 105.152 TWh**
  > (lower = pjm-h6's armed landing, upper = the control's)

  The arm raises coal's bid everywhere in its min-load block, so COAL_BIT must fall below the
  control; and its effective push is **~58 %** of h6's, so under a monotone response it cannot
  fall below h6's landing. A landing outside that interval means the mechanism is not doing
  what its own arithmetic says, and the arm STOPS.
* **G-4 NO NON-TARGET LOAD-BEARING FLIP** — no non-target load-bearing criterion (C1 on another
  class, C2, C3a, C3b) crosses PASS → FAIL against the control. **CC_REGULAR is the named
  watch**: it killed both predecessors (control 328.456 = +2.79 PASS). Band ±8.00 TWh ⇒ the arm
  must land **CC_REGULAR ≤ 333.670 TWh**.
* **G-5 INERTNESS — this arm's own falsifiable prediction, and the reason the LP is worth
  spending even if G-4 fails.** The `mustrun` band carries **77 %** of the arm's coal $-MW
  footprint (283,209 of 367,545 in 2023) but is **84.4 %** floored. Pre-registered claim:

  > **the `mustrun` band produces LESS THAN 25 % of the arm's total COAL energy change**,
  > measured from `dispatch/2023_P1.parquet` by band, arm vs control.

  If it produces more, the floor measurement is wrong and §3.3's reframing — including the
  correction to this lane's own FINDING — falls with it. **No prior session has measured
  whether repricing floored energy is dispatch-inert**, and the screen measures it either way.

## 5. EXPECTED, REPORTED, GATING NOTHING — including the outcome that would kill it

**A locally-linear read predicts this arm FAILS G-4, and that is stated here so the result
cannot be spun either way.** h6 moved effective ~220,000 $-MW and lost 26.318 TWh of COAL_BIT.
This arm moves ~127,900 effective, so a linear response predicts ≈ **−15.3 TWh** →
COAL_BIT ≈ **89.9** (residual ≈ −13.1, **FAIL**), with CC_REGULAR absorbing h6's 41 % share →
≈ **334.7** (**FAIL**, bar 333.670).

**Why a linear read is not admissible as a gate, and is not one here** (rule 1 `[R-STRUCT]`):
pjm-h7 pre-registered exactly such an estimate (≈86.3 TWh) and the measured landing was
**82.996** — the error was in the *opposite* direction to the argued one. A linear
extrapolation from a 2.3×-overshooting arm is a poor guide to a correctly-sized one. Two
further effects push the other way and are not in the linear number: the ST_GAS leg makes
ST_GAS **cheaper** (−8.45 $/MWh on 2,432 MW), so displaced coal can land on ST_GAS rather than
on the CC_REGULAR bar; and 84 % of the mustrun move is inert (G-5).

**The result is informative whichever way it lands**, which is rule 29's test for spending the
LP:

* **Coal survives at PJM's own measured offers** ⇒ the min-load block was the undisciplined
  surface, the arm earns the six-year span, and h6's kill is explained as a 2.3× overshoot.
* **Coal collapses anyway** ⇒ a much larger structural statement, and a *new* one: the model
  has nothing that keeps PJM coal running at the offers PJM's own units submit — and D-2
  (§4d of the FINDING) has already shown it is **not** a floor, since 96 % of PJM coal is
  economic dispatch. That result would redirect the lane away from the offer stack entirely.

**Neither number is a gate in either direction.** G-3 is an interval on what the mechanism
*does*, G-4 a non-target flip check, G-5 a structural prediction. The target residual selects
nothing.

## 6. WHAT IS NOT TOUCHED

* The keeper, its recipe, its registration and PJM's `CALIBRATED` headline — all unchanged.
* `gas_mid` (3.40 live) — **untouched**, and the rule-23 wart stands undiminished. This arm is
  **sigmoid-invariant**: the passthrough multiplies every coal band by the same hourly scalar,
  so it cancels in the within-unit comparison that produced this charter. The standalone
  `gas_mid` → 4.58 accuracy repair remains unchartered (pjm-h7 §4/§5).
* The `committed` band's registered multiplier 0.548 — **not moved**. The arm overrides those
  rows' P1 bid wholesale rather than re-tuning a multiplier, which is why it adds **zero** free
  parameters. Reverting anything stays refused (rule 14 `[R-ACCURATE]`).
* `sync`, `econ`, `peak` rungs — unmoved (§1, G-1).
* CC_LIKE min-load rows — out of scope: CC_REGULAR `committed` is 28,818 MW at 1.19-1.24× of
  measured, so a LEVEL form there would cut the largest class in the system by ~20 % in one
  step. Left for its own charter, named here rather than silently omitted.
* Standing escalations carried forward unchanged: PS-net-inclusive `OTHER` as the
  `gas_foldin_deflation` operand; the EIA-930 PJM 2021 `net_gen` corruption; the display-stale
  `volErr`/`nonFosErr` in the PJM 2021/2022 run payloads.
* The two pre-existing parity REDs (`caiso279_ablate_dswcouple_span`, `soco15_spp_arm`) — not
  PJM's, not touched.

## 7. RULES

Rule 1 `[R-STRUCT]` (§4.2 the gate is structural and STOP-only; §5 the direction is reported
and gates nothing; the residual selects no parameter, and §1's `sync` exclusion is the choice
that does not flatter it) · rule 13 `[R-MEASURED]` (§2 the operand is PJM's own published
offers, a formulaic input with a forward analogue) · rule 14 `[R-ACCURATE]` (§6 nothing is
reverted; the accurate input is preferred) · rule 19 `[R-ONE-MECH]` (§1 LEVEL replaces
take-or-pay rather than stacking a floor on it) · rule 21 `[R-DOF]` (§2 zero free parameters,
zero scalars, nothing swept) · rule 23 `[R-FROZEN-DERIVE]` (§2 the surface is frozen; nothing
re-derived) · rule 24 `[R-REGISTRY]` (§2 one registered field, cache-key registered) ·
rule 25 `[R-ISO-SCOPE]` (PJM's own offers, PJM's own fleet; nothing transfers) ·
rule 28 `[R-MECH-MATRIX]` (§2 the field is registered on its family row in the same PR) ·
rule 29 `[R-SCREEN]` (clause 0 = this document; clause (1) screen year on footprint, fixed in
the FINDING before the arm was built; clause (b) G-DRIFT discharged at zero LP, form 4 valid)
· rule 30(c) (no held-out year touches PJM's determination) · rule 31 `[R-RETAIN]` (nothing
deleted; the promotion question goes to the owner) · rule 32 `[R-SHARD]` (a) (the parent runs
no LP; the screen is one shard) · rule 34 `[R-SHARD-PROMOTABLE]` (the shard pushes its bundle
with the per-plant layer).
