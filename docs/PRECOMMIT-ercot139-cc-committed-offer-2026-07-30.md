# PRE-COMMIT — ERCOT-139: the CC committed block on the MEASURED SCED TPO offer level

**Date** 2026-07-30 · **ISO** ERCOT · **Lane** ercot139-cc-offer-shape ·
**Phase** 2 (mechanism + full-span arm) ·
**Keeper under test** `2026-07-29-ercot137-coal-margin-measured`
(bundle `results/calibration/ercot137_margin_arm`) ·
**Chartered by** `docs/DIAGNOSIS-ercot138-coal-gas-ranking-2026-07-29.md` §6
(the gas-side Phase 2 it licenses) and §7.3 (which of two forms) ·
**Derive** `scripts/data/derive_cc_committed_offer_margin.py` ·
**Precommit pushed BEFORE any solve** (rule 15/26b discipline).

This document is fixed before the LP runs. Its predictions and decision rule
are the falsifier; the run is scored against what is written here.

---

## 0. The mechanism question ERCOT-138 left open — DECIDED, with evidence

ERCOT-138 §7.3 left the choice: **(i)** re-identify the
`offer_curve_by_group['CC_REGULAR']` band multipliers on the RT instrument, or
**(ii)** a below-cost committed-CC block — the gas analogue of coal's
`_mustrun` net-margin tranche. **This lane chooses (ii).** Four reasons, each
checkable before the solve:

1. **(i) cannot reach the measurement.** §J sizes the whole offer/physical
   heat-rate markup at 1.101×, worth ~$1.54/MWh at 2024's $2.213 gas — **~29 %**
   of the ~$5.3 gap. Setting every multiplier to its physical basis exhausts (i)
   and leaves 71 % standing. A mechanism that structurally cannot reach the
   measured level is not a fix.
2. **(i) has the wrong SHAPE.** The §C gap is **−33.6 pp at ≤$10, −41.6 pp at
   ≤$15, −11.5 pp at ≤$20, −0.8 pp at ≤$25** — concentrated at the curve bottom
   and *already closed* by $25. Band multipliers scale the whole class curve
   with one base heat rate × fuel, so (i) must over-correct the ≥$20 region
   (where there is no gap) to move ≤$15. A **block at the bottom** is the
   shape-matched object.
3. **(i) has the wrong YEAR behaviour.** A heat-rate multiplier scales with
   delivered gas. A multiplier low enough to hit 2024's measured p25 of $8.38
   (≈0.50× base HR) would price 2025 at ~$12 against a measured 2025 curve
   bottom of **$18.07** — it fails out of the year it was fitted in. The
   measured bottoms move with fuel at an **implied 7.85 MMBtu/MWh** (§2 below),
   i.e. full pass-through, which is the **fuel-invariant margin form's**
   signature, not a multiplier's.
4. **(ii) is the form already validated on this exact defect's coal twin.**
   ERCOT-136/137 closed the identical structure on coal: the model's fitted
   below-cost committed block replaced by a MEASURED level + anchor on the same
   SCED TPO instrument, same loader, same corpus. §2.5: "Coal has such a
   mechanism and it is now measured. **Gas does not have one.**"

---

## 1. The arm — ONE change, one bundle, one mechanism

`cc_committed_offer_margin` (new `ScenarioConfig` gate, default off,
ERCOT-scoped by its level registry): the **CC_REGULAR `_committed` tranche**
is repriced from its band multiplier to the measured net-revenue margin form —
the exact algebra of `apply_coal_tranches`' ERCOT-137 branch:

```
mc[g, t] = heat_rate[g] × (fuel(t) − anchor) + emis(t) + level
```

implemented as `mc[g, :] += level − heat_rate[g] × anchor − vom[g]` on the
assembled cost, so the VOM already inside `mc` is folded into the measured
all-in level and never double-counted. At `fuel == anchor` the resolved bid is
**exactly `level`**. Full delivered-fuel tracking is retained; everything above
fuel is the fuel-invariant measured margin.

* `heat_rate[g]` is the **tranche's own** heat rate — per-plant, no new
  parameter, exactly as the coal form does it.
* Scope: `plant_group == "CC_REGULAR"`, `_committed*` tranche suffixes, CAMPD
  bin path. `CC_CHP` is EXCLUDED — ERCOT-138's `MODEL_CC_GROUPS` is
  `("CC_REGULAR",)` and CC_CHP is reported there as a sensitivity, never pooled
  into the measured CC control (its committed state is owned by its steam host,
  rule 19). The mechanism's population is therefore **exactly** the
  measurement's population.
* Applied to the **BASE** cost, so P0 run discovery and the P1 bid see the same
  offer curve — like the two margin forms it mirrors, and unlike the P1-only
  offer surfaces.

### 1.1 Rule 19 `[R-ONE-MECH]` — this REPLACES, it does not stack

Enumerated from the keeper's own `run_config.json` before the solve. What
prices the CC_REGULAR `_committed` row today:

| mechanism | armed | touches `_committed`? |
|---|---|---|
| `offer_curve_by_group['CC_REGULAR']` band multipliers | yes | **YES — `committed` 0.998 × base HR. This is the sole owner.** |
| `gas_offer_net_revenue_margin` (anchor 2.2494) | yes | **No, provably.** Markup = `max(0, 0.998 − phys_committed 1.006)` = **0**; §J measures its delta at **$0.00 at p25/p50**. |
| `ercot_offer_surface_cleared_share` (+`_rt`) | yes | **No.** Its docstring scopes it to `econ*` rows of CC_REGULAR/CT_PEAKER and explicitly cedes "the committed/mustrun blocks … to the bridge/floor structure". |
| `ercot_offer_surface_conditional` | yes | **No.** `peak*` rungs only. |
| `ercot_gas_commitment_bridge` @ 0.574 | yes | **A FLOOR, not a price.** Moves `min_gen`, never `mc`. |
| `ercot_offer_surface_lowcurve` / `_floorscoped` | **off** | n/a — see §4.2. |

**Exactly one mechanism prices this row, and this arm replaces it.** The band's
`committed` multiplier becomes inert for CC_REGULAR (the repriced rows ignore
it); `econ_low` / `econ_high` / `peak` / the `peak_ladder` and every other class
are **untouched**.

---

## 2. The identification — MEASURED, zero fitted parameters

`scripts/data/derive_cc_committed_offer_margin.py` (rule-23 frozen; reads only
COMMITTED artifacts, re-runs nothing):

* **ANCHOR = 2.2494 $/MMBtu** — NOT newly derived. The already-committed
  `GAS_OFFER_MARGIN_ANCHOR_BY_ISO['ERCOT']`, reused so the whole gas offer
  surface keeps **one** identification point that cannot drift against itself
  (rule 19 bookkeeping).
* **LEVEL = 10.354 $/MWh** — the real CC fleet's RT supply-curve bottom
  expressed at that anchor. Source: `ercot136_coal_headroom_conduct.json`
  `B1_curve_bottom`, **CC** rows (60-Day SCED `Submitted TPO-Price1`
  capacity-weighted p50, pooled res-hours-weighted over the four 2024–2025
  subsets) — the same measurement, instrument, construction and loader that
  supplied coal's promoted level, read off its COAL twin.

The raw bottoms are **not** year-invariant ($10.07 in 2024, $18.07 in 2025)
because delivered gas moved $2.213 → $3.232. The form's claim is that the
*residual above fuel* is invariant, so the level is identified by removing the
corpus's OWN measured fuel response — **no model heat rate, no fitted slope**:

```
HR_implied = (18.0694 − 10.0681) / (3.232 − 2.213) = 7.8521 MMBtu/MWh
level_i    = bottom_i − HR_implied × (fuel_i − anchor)
```

| subset | res-hours | bottom | fuel | anchored level |
|---|---|---|---|---|
| 2024 tail | 56,200 | 9.83 | 2.213 | **10.1158** |
| 2024 control | 47,486 | 10.35 | 2.213 | **10.6358** |
| 2025 control | 49,818 | 17.39 | 3.232 | **9.6746** |
| 2025 tail | 51,238 | 18.73 | 3.232 | **11.0146** |
| **pooled** | 204,742 | | | **10.354** |

**The identification's own quality statistic:** cross-subset dispersion falls
from **±42.98 %** raw to **±6.47 %** anchored. The form removes 85 % of the
dispersion it is claimed to explain. `HR_implied` = 7.85 MMBtu/MWh is a
physically sensible CC offer heat rate (the model's own cap-weighted CC offer
HR is 7.610), which is the functional form's falsifier and it passes.

### 2.1 Independent second instrument — 3.02 % apart

The CC min-load block's own declared `Min Gen Cost` p50, at **70.0–82.0 %**
coverage (`C_min_gen_cost`, CC rows), run within ~$1/MWh of the TPO bottom in
**all four** subsets. Same construction on that second instrument:
`HR_implied` 7.6262, **level 10.6662** — **3.02 %** from the primary, its own
dispersion 40.27 % → 6.70 %. Coal's corroborating instrument sat at 28–31 %
coverage; CC's sits at 70–82 %, so this level is **the better-attested of the
two**.

### 2.2 Licensing — the CC class passes the same RT test coal passed

`A_ercot123_reproduced`, CC rows: `curve_share` **0.9518 / 0.9505 / 0.9714 /
0.9798**, self-schedule 0.008–0.035, residual 0.007–0.015 (ERCOT-138 §3.4).
The "a near-zero/whatever bid is faithful" escape does not apply.

---

## 3. Predictions — fixed before the solve

### 3.1 The offer surface (the direct target, measurable without gates)

The repriced committed bid at 2024's $2.213 gas: `HR_c × (2.213 − 2.2494) +
10.354` ≈ **$10.1**, against a measured 2024 bottom of **$9.83–10.35**. At
2025's $3.232: ≈ **$17.7**, against measured **$17.39–18.73**. The keeper's
committed bid today is **$17.33 / $17.79 / $24.78 / $25.83** — i.e. **+$7.1 to
+$7.5 dear in every one of the four subsets**, and that near-constant excess is
what this level removes.

`inc_share` (2024 tail), committed = 27.74 % of class capability:

| | ≤$10 | ≤$15 | ≤$20 | ≤$25 |
|---|---|---|---|---|
| measured | 0.345 | 0.647 | 0.805 | 0.866 |
| keeper | 0.009 | 0.231 | 0.690 | 0.858 |
| **predicted** | **~0.15** | **~0.51** | 0.690 | 0.858 |

**Predicted: ≤$15 gap −41.6 pp → ~−14 pp (67 % closed); ≤$20 and ≤$25
UNCHANGED** (the block was already inside both). §E gas_leg at p25/p50
predicted **+6.64/+5.28 → ~+2 to +3.6 / ~+1.5**.

### 3.2 The gates

* **C1 coal — predicted to IMPROVE.** This is the structural target: coal
  +6.2/+8.8/+8.6 TWh over actual, displaced ~1:1 from gas (corr −0.93..−0.97).
  A cheaper CC committed block takes that back directly.
* **C3a mean LMP — predicted to WORSEN, modestly and boundedly.** Already
  −35.2/−14.5/−12.1 %. The effect is **confined to the trough band**: in any
  hour clearing above ~$17.3 (2024) the committed block is already fully
  dispatched, so repricing it changes neither dispatch nor dual; in any hour
  clearing below ~$10 it is out either way. Only hours clearing **between ~$10
  and ~$17.3** move. Predicted annual-mean effect **−$0.5 to −1.5/MWh**
  (C3a 2024 ≈ −14.5 % → −17 to −20 %). This is expected and is **NOT** on its
  own a rejection trigger — C3a is the standing open root-cause lane.
* **C3c scarcity tail — predicted ≈UNCHANGED.** Two independent reasons, both
  structural: (a) the repriced block is deep **inframarginal** in every hour
  above ~$17/MWh, so it cannot move a >$200 count; (b) ERCOT-119 proved the
  118/119 drain (72→49, 13→3) was owned by the **econ** legs, and the rebasis
  also moved **peak** — this arm touches neither econ nor peak. If C3c drains
  materially anyway, that falsifies this reasoning: see §4.1.
* **C3b / C4 / C7 / C8** — no directional prediction; reported as they fall.

---

## 4. TWO PRE-REGISTERED FAILURE MODES

### 4.1 ERCOT-119's C3c drain — ORDINARY REJECTION, pre-declared

ERCOT-118 and ERCOT-119 are ordinary rejections on C3c, **identically**
(72→49 hours, 13→3), and deflating the CC curve is what caused it. **Any arm
that breaches C3c is an ORDINARY REJECTION of this arm, declared now, before
the solve.** Concretely: if the model's >$200 count falls outside
[0.5×, 2.0×] the committed RT actual in a year where the keeper was inside it,
or falls materially relative to the keeper's own count, the arm is rejected —
whatever it does to C1 or to the offer-shape target.

Two notes recorded with the pre-registration, so the record is honest either
way:

* §3.2 predicts C3c is ≈unchanged **for a stated structural reason**. This
  pre-registration is therefore a genuine test of that reason, not a
  formality. A breach means the inframarginality argument is wrong.
* **The rule-1 `[R-STRUCT]` tension is real and is surfaced, not buried.** A
  measured, structurally-grounded mechanism rejected on a fit gate is exactly
  what rule 1 forbids in general, and the ERCOT-137 promotion ("If structural
  integrity improves but gates regress that may still be a keeper") is standing
  precedent the other way. This lane honours the pre-registration as written —
  a C3c breach ⇒ arm NOT promoted — and **surfaces the override to the owner**
  (§6.1) rather than deciding it. The mechanism, the measurement and the matrix
  cell are registered either way; only the *promotion* is withheld.

**If C3c does drain, the diagnosis is already fixed:** the measured bottom is
cheap *because* it sits on an **inflexible, already-committed** block that
cannot set the margin (ERCOT-64: "the model reproduces the measured 'LSL block
never sets the margin' inflexibility via the STATE alone"). Posting that price
on a *flexible* LP tranche makes it price-setting. The successor is then the
**commitment STATE** (the bridge's floor coverage outside gap hours), **NOT
another price lever** — and emphatically not a re-tuned level, which would be
a residual fit (rule 13).

### 4.2 The p90 finding runs OPPOSITE in sign — stated ex ante

ERCOT-138 §5.6: at p90 the model's **coal** curve runs **$9.6–15.5/MWh UNDER**
measured in all four subsets (−10.21 / −9.60 / −11.59 / −15.49) — it tops out
too low. CC's p90 is dear in 2024 (+5.13/+4.93) but **under** in 2025
(−0.12/−8.02).

**So the model's curve is too FLAT: too dear at the bottom, too cheap at the
top. No single level lever serves both the crossing band and the tail, and
this arm does not attempt to.** It is a bottom-of-curve mechanism only. The
top-decile defect is coal-owned, year-dependent on gas, and belongs to the
near-tail / C3c lane already attributed by ERCOT-99/101/107/108/119. Any
reading of this arm's result that treats a tail regression as evidence about
the crossing band, or vice versa, is a category error and is refused here in
advance.

### 4.3 Rule 26(a) clearance — why this is not a refuted mechanism re-run

`ercot_offer_surface_lowcurve` was probe-REFUTED and
`_floorscoped` probe-adjudicated PROVABLY INERT. This arm is neither:

| | refuted v2 lowcurve | inert floor-scoped | **this arm** |
|---|---|---|---|
| instrument | DAM `Min Gen Cost` | DAM `Min Gen Cost` | **RT SCED `TPO-Price1`** (the instrument ERCOT-136 licensed) |
| rows | committed **AND econ** rungs | committed, bridge-floored hours only | **`_committed` only, all hours** |
| form | P1-only binned multiplier ladders | P1-only markdown | **base-cost level + anchor** |
| why it failed | repriced **above-floor mid-merit** capacity at the LSL bid | window where the row is **pinned** ⇒ cannot price | — |

The stated cause of the v2 refutation is the **econ** rows, which this arm does
not touch; the stated cause of the floor-scoped inertness is the **pinned
window**, which this arm is not scoped to. §J is the new evidence rule 26(a)
requires: it is about a *different object* (this band's markup vs its
multipliers, on the RT instrument).

---

## 5. The decision rule — fixed now

1. **C3c breach ⇒ ORDINARY REJECTION** (§4.1). Registered as a rejected probe
   with its matrix cell; not promoted.
2. **C3c intact + C1 coal improves ⇒ KEEPER CANDIDATE**, surfaced to the owner
   on the ERCOT-137 standard (structural integrity improves, C3a regresses as
   predicted and pre-registered). Promotion is the owner's call, not this
   session's.
3. **C3c intact + C1 coal does NOT improve ⇒ the mechanism is right and
   something else owns the coal over-run.** Registered as a rejected probe;
   the finding is that the ranking's *quantity* consequence is not carried by
   the CC committed bid, which retires this lane's hypothesis and hands the
   coal over-run back to the D-2/G1 enumeration.
4. A result outside all three is reported as it falls; nothing is re-tuned to
   land inside one. **No parameter in this arm is swept.** The level is
   measured; if it is wrong the derive's source artifacts are wrong (rule 23).

---

## 6. Open owner rulings surfaced (NOT decided here)

1. **Carried from ERCOT-137 §7 / ERCOT-138 §7.1, still open:** delete outright
   vs leave inert the retired `coal_tranche_1_fuel_passthrough` pricing path
   and the legacy non-CAMPD `split_coal_tranches` `_t1/_t2/_t3` path (rule 26
   `[R-DELETE]`).
2. **Carried from ERCOT-138 §7.2, still open:**
   `ercot_offer_hrmult_ep_rebasis` and `_bands` are solve-affecting
   `ScenarioConfig` fields with **no mechanism-matrix row** — a rule-26(c) gap
   predating both lanes. The CI guard passes because it only checks fields new
   against base. Recorded, not fixed here.
3. **NEW (§4.1):** whether a C3c breach should override the pre-registration
   under rule 1 `[R-STRUCT]` and the ERCOT-137 "structural integrity improves
   but gates regress" precedent. This lane honours the pre-registration; the
   override is the owner's.

---

## 7. Honest limits, stated before it runs

1. **The measured corpus is probe days, not a span** — 79 delivery days,
   2024–2025 only, hours 11–22 for three of four subsets, 4 intervals/hour.
   **No 2023 SCED exists**, so the 2023 application of the level is a declared
   extrapolation — admissible because the margin is fuel-invariant by
   construction, and gated leave-one-year-out within 2023–2025 exactly as
   ERCOT-137's was.
2. **A 5 % off-anchor slope basis note.** The level is identified at
   `HR_implied` 7.85 but applied at each tranche's own heat rate (CC committed
   ≈ 7.47). At the identification point the bid is exactly `level`, so the
   ercot132-leg-B basis-**mismatch** failure mode cannot recur; off-anchor the
   two slopes differ by ~5 %, bounded to ≤ ~$0.4/MWh across the 2023–2025 fuel
   range. Declared, not corrected — correcting it would require a fitted slope.
3. **The P1 startup amortization and the ARMED P1 gas surfaces make the
   keeper's scored CC curve DEARER than §2.1's base-cost table shows**, so the
   defect this arm repairs is understated, not overstated. Direction-safe.
4. **`ercot_gas_bridge_min_load_frac` 0.574 is unchanged and untouched.** The
   floor is a state, this is a price; they compose, and the arm does not move
   the floor.

---

## 8. Scope

Full span **`--year 2023 2024 2025` in ONE bundle** (rule 16). Holdout years
(2022 / 2019 / ≤2021 / H1-2026) untouched (rule 22). ERCOT-scoped only
(rule 25 — the level is ERCOT-identified from ERCOT data and enters
`CC_COMMITTED_OFFER_LEVEL_BY_ISO` for ERCOT alone; other ISOs hard-fail rather
than inherit it). No residual-tuned adder (rule 13). Availability stays
MEASURED (rule 14 — the retired estimate is not re-tuned around). One
mechanism per phenomenon (rule 19, §1.1). New `ScenarioConfig` field carries
its mechanism-matrix row in the same push (rule 26c). No new GitHub Actions
workflow. Registration keeper-or-rejected with the matrix cell stamped in this
same session (rules 15/26b).

Every CLOSED lane honoured: the COAL side of the ranking (ercot138 — bands
exonerated, no coal offer lever), `gas_offer_net_revenue_margin` as this
defect's lever (ercot138 §J — inert, $0.00 at p50),
`ercot_offer_hrmult_ep_rebasis` / `_bands` (ercot118/119),
`measured_ct_heat_rates` on this defect, coal min-load PRICE (ercot137), coal
offer REACH (ercot123 §7.1), coal offer LEVEL rebasis (ercot132 leg B), pooled
`econ_high` 2.856 (ercot122 §5.2), F923 delivered-coal price as a price
question (ercot135 §3), coal ramp trajectory (ercot127/132), availability
ENVELOPE layer (ercot126), min-config upper bound (ercot130), plant-grain
fractional min-load floor (ercot127 §3), unit-grain commitment STATE
(ercot128), age/temp derates (ercot121 §1a), EP-rebasis C3c (ercot119),
`ercot_zonal_gas_basis`, West/Panhandle topology split.
