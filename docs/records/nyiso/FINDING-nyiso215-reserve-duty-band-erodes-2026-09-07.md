# FINDING nyiso-215 — the seven single-`_peak` plants are the **deliberate** `cc_reserve_duty_split` cohort, its membership survives audit, and its **level does not**: a duty-role cohort is held out of merit by a duct-firing physics multiplier fixed in heat-rate space, and the protection erodes as the price level rises

**Session:** nyiso-215, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-acwrdd`, on `main` at `dcb609f4`. **Date:** 2026-09-07.
**Keeper:** `2026-09-07-nyiso-213-summer-seam` — **keeper unchanged; nothing promoted, nothing
armed, nothing registered, no marker moved.**
**Pre-registration:** `results/calibration/PREREG-nyiso215-reserve-duty-single-peak.md`, committed
and pushed at `f0cf9d54` **before P1–P5 were measured** and not edited since.
**Machine record:** `results/calibration/_nyiso215_reserve_duty_census.json` and
`_nyiso215_band_energy_bound.json`. **Instruments:**
`scripts/probes/nyiso215_reserve_duty_census.py`, `scripts/probes/nyiso215_band_energy_bound.py`.
**ZERO LP: no solve was spent.** Every fleet rebuild is `fleet_only=True`; every dispatch number
is read from the keeper's own committed sidecars (rule 29(b) form 4 — **no control solve**).

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES.** NYISO's keeper reads **CALIBRATED** with **zero
failing criteria** across 2023–2025 — re-verified this session at HEAD, artifact-only
(`scripts/calibration_verdict.py --run-id`, §7). Nothing below was selected because a residual
moved (rule 1 `[R-STRUCT]`); no residual was consulted at any point, and the 2022 held-out rung is
named nowhere as a target (rule 22 `[R-HOLDOUT]`).

---

## 0. The result in one paragraph

nyiso-214 §7 named seven small `CC_REGULAR` plants — 441.7 MW — whose *entire* capacity is one
tranche labelled `_peak`, and asked whether that is a builder artifact. **It is not.** They are
exactly the `reserve_duty = True` cohort of `cc_reserve_duty_split` (nyiso-146), a deliberate,
measured-conduct-gated duty-role mechanism armed in the keeper; with the flag off **all seven**
regain 7–8 tranches. Its **membership survives audit**: the cohort's single 0.10 threshold is
applied to two different statistics — a CAMPD online share at 19 plants and an EIA-923 pooled
capacity factor at 3 — and the fallback is empirically one-sided toward inclusion (median ratio
**0.473**, boundary-clean **0.418**, and 19 of 20 ratios below 1), but the one plant that rides it
(7784 Allegany) qualifies on **every** reconciliation tested (implied online share 0.037 / 0.041 /
0.059, all inside the cohort's own measured band 0.012–0.064). **What does not survive is the
level.** The split routes the cohort to the *class* curve's peak band — `2.25 × base`, a number
identified as large-CC **duct-firing physics** (`phys_peak = peak = 2.25`) and borrowed here to
express a **duty role**, explicitly to avoid a new scalar under rule 21 `[R-DOF]`. A multiplier
fixed in heat-rate space is a fixed *cost* offer, so its protection erodes as the market price
level rises: across 2023 → 2025 the cohort's implied economic on-share goes **4.2 % → 16.7 % →
52.1 %** against a measured duty of 3.6 % online and a measured capacity factor of **0.14 %**, and
the keeper's own committed band sidecar puts **≥ 0.855 × the cohort's entire 2023 measured annual
energy through in 38 hours**. This is a rule-19 `[R-ONE-MECH]` basis borrow of the same family
nyiso-212/-213 repaired and nyiso-214 measured, and it is handed to the owner as a decision card
(§6) — **nothing is built, armed, or recommended.**

---

## 1. P1 — reproduction bar: **FIRES**, and the VOID did not fire

Declared: the set of `CC_REGULAR` plants carried 100 % in `_peak` unit ids is exactly
{10621, 54034, 7784, 10620, 54592, 50744, 54593} and their summed `pmax` is 441.7 MW ± 2.0 MW;
**VOID** on any set difference or a > 5 % MW difference.

Measured on a `fleet_only` rebuild of the keeper's own 2025 recipe: the set matches **exactly**,
and the sum is **441.700 MW** — nyiso-214's committed census reproduced to **0.0 %** on this
session's own HEAD. Per plant: 10621 102.7, 54034 78.0, 7784 67.0, 10620 53.6, 54592 53.6,
50744 43.9, 54593 42.9 MW.

An independent cross-check falls out of the same rebuild: the class's total `_peak` capacity is
**1,158.461 MW**, so the non-cohort (duct) population is **716.761 MW** against nyiso-214 §6
form A's **716.8 MW** — agreement to **0.039 MW**, from a different instrument.

## 2. P2 — causation: the split, decisively; **the magnitude limb misses, and the gate is NOT rewritten**

Declared: with `cc_reserve_duty_split = False` **alone**, ≥ 5 of 7 plants acquire ≥ 2 tranches
**and** the class `_peak` capacity falls ≥ 400 MW. **REFUTES** at ≥ 3 remaining single-tranche.

Measured: **7 of 7** become multi-tranche — 8, 8, 8, 8, 8, 7, 7 tranches — and **zero** remain
single. The refuting limb is emphatically not met, and the small-band-filter explanation
(nyiso-198's Riverbay 52168 defect) is excluded by execution. But the class `_peak` capacity falls
**397.748 MW**, **2.252 MW short** of the declared 400.0.

**So P2 does not FIRE on its literal terms, and — following nyiso-212, which killed its own arm on
gates whose wording was its own — the gate is reported as written, not restated.** Worse, my
declared INDETERMINATE clause covered "5 or 6 of 7 … and fall < 400 MW"; the measured 7 of 7 with
a fall < 400 MW lands in a **gap in my own outcome partition**, which was not exhaustive. That is
a defect in the pre-registration, disclosed here rather than papered over.

A **post-hoc diagnostic** (`_nyiso215_band_energy_bound.json`, labelled as such and not used to
move the gate) explains the arithmetic: with the split off the seven do not lose their peak band
entirely — they fall back to the ordinary class peaking allocation, **retaining 43.952 MW**, i.e.
**9.951 %** of cohort capacity against the class curve's `pct_peaking = 8.0` (the excess being the
per-plant `cc_peaking_per_plant` / duct values some of the seven carry). 441.700 − 43.952 =
397.748. **The 400 MW bar was mis-set by me, by exactly the quantity I failed to account for.**
The causation conclusion rests on the 7-of-7 tranche limb, which fired without qualification.

## 3. P3 — basis asymmetry: (a) **FIRES**, (b) **HOLDS**

The cohort's 0.10 threshold is applied to a CAMPD plant-summed **online share** where a CEMS
record exists and to an EIA-923 pooled net **capacity factor** where none does. The derive
script's docstring calls these "the same meter class"; this is the first session to measure it.

**(a) Declared: median CF / online-share ratio < 0.85 over the plants carrying both. FIRES.**
Over all 20 such plants the median is **0.4730** (range 0.1702–1.4575). The single ratio above 1 is
**2500 Ravenswood at 1.4575 — a capacity factor of 1.383, physically impossible**, and it is one of
nyiso-214's boundary-contaminated plants (CAMPD/EIA-923 facility spans 7.05 × the model plant). On
nyiso-214's own boundary discipline the sub-population is clean: over the **17 boundary-clean**
plants **every** ratio is below 1, median **0.4180**, range 0.1702–0.9414.

**A correction to this session's own stated reasoning, made because it was wrong:** the PREREG
argued the ordering CF ≤ online share as an analytic identity. **It is not one** — the two
statistics use different numerators (EIA-923 *net* generation vs CAMPD *gross* load) and different
denominators (the *raw fleet CSV* `pmax` vs the plant's own p99.5 HSL), so nothing forbids a ratio
above 1, and one was measured. The one-sidedness is **empirical (19 of 20; 17 of 17
boundary-clean), not analytic**, and it is stated that way from here on.

**(b) Declared: 7784's implied online share < 0.10. HOLDS, robustly.** 7784's EIA-923 CF is
0.0173; dividing by the three defensible reconciliation medians gives an implied online share of
**0.0366** (all-plant), **0.0414** (boundary-clean), **0.0590** (the cohort's own low-duty regime,
median 0.2932). All three sit **inside** the cohort's own measured online-share band
(0.0122–0.0635) and none is near 0.10. A **second**, independent basis wrinkle points the same way
and is stated rather than absorbed: the derive's CF denominator is the raw fleet CSV `pmax`
(60.0 MW at 7784) while the LP dispatches 67.0 MW, so the LP-basis CF is **lower** still
(0.0155) — pushing further below the threshold, not toward it.

**The reverse error is not available in this population.** The other two fallback-basis plants are
54808 NYU (0.5138) and 57664 Astoria II (0.7138), both far above 0.10 on the statistic that
under-reads; since every boundary-clean ratio is < 1, neither could cross downward. **The defect
can only wrongly include, it does so at most at one plant, and at that plant it does not.**

**Verdict on membership: a real two-basis construction defect, quantified at a factor of ~2, that
is provably non-load-bearing here.** No re-derivation is licensed — rule 23 `[R-FROZEN-DERIVE]`:
no source data changed, and this probe writes no artifact.

## 4. P4 — conduct: **FIRES**. The band is a fixed cost, and the price level outruns it

For each cohort plant, on the keeper's own hourly `(n_gen, T)` `mc_base` and its own zone's
committed **P1** LMP, the **implied economic on-share** is the share of 8,760 hours with
`mc_peak ≤ LMP`. It is an **upper bound** (it ignores reserves, ramping, min-up and outages, and
`mc_base` excludes the P1 startup markup, so it is if anything generous).

Declared: the capacity-weighted implied on-share exceeds **3.0 ×** the capacity-weighted measured
duty in ≥ 2 of 3 years. **REFUTES at ≤ 1.5 × in ≥ 2 years** — the outcome that would have
vindicated the incumbent as a clean negative.

| year | implied on-share | measured duty (pooled) | **ratio** | Upstate_West mean LMP | cohort mean `mc_peak` |
|---|---:|---:|---:|---:|---:|
| 2023 | 0.0422 | 0.0358 | **1.18** | $24.48 | $44–51 |
| 2024 | 0.1670 | 0.0358 | **4.66** | $35.83 | $45–54 |
| 2025 | **0.5210** | 0.0358 | **14.54** | **$53.91** | $58–71 |

Two of three years clear 3.0 ×, so **P4 fires**; and the refuting limb is met in only one year
(2023), so it does not fire.

**The mechanism is visible in the table and it is not a residual.** The cohort's own offer cost
rises ~30 % across the span (fuel), while the zone price rises **120 %**. A multiplier fixed in
**heat-rate space** produces an offer fixed in **cost space**, and a duty role is not a cost
property — it is a *price-percentile* property. In 2023 the band happened to sit near the right
percentile of the Upstate_West price distribution; by 2025 the distribution has moved through it
and six of the seven plants are in merit for **58–68 %** of hours against meters reading 1.2–4.7 %.

**Stated at the gate, and it is a real cost to this reading:** the seventh plant, **54034
Rensselaer** (Capital_Hudson), moves the **opposite** way — implied 0.0038 / 0.0064 / 0.0098
against a measured 0.0635, i.e. the same mechanism **over**-corrects there by roughly an order of
magnitude in every year. The mechanism is therefore not merely mis-levelled in one direction; it
is **un-levelled**, and its error changes sign by zone. Reported at full magnitude.

**And the erosion is not a model artifact.** The keeper's own promotion note records C3a
+4.3 / +5.3 / **−7.3** %: in 2025 the model's price level sits ~7 % **below** actual. Measured
against the real 2025 price distribution the implied on-share would be **higher**, not lower.

## 5. P5 — the committed bundle's own band dispatch: **the mean limb fires, the exceedance limb misses**

Declared for 2025: `CC_REGULAR` `peak` band mean ≥ 120 MW **and** the share of hours above
716.8 MW ≥ 2.0 %. **REFUTES** at mean < 40 MW and exceedance < 0.5 %.

Measured (committed `class_band_hourly`, P1): 2025 mean **135.993 MW** (limb cleared),
exceedance **1.1872 %** (limb missed by 0.81 pp). **P5 therefore does not FIRE on its literal
terms**, and — as with P2 — the gate stands as written. The refutation is nowhere near met
(135.993 ≫ 40; 1.1872 ≫ 0.5), so the "something other than the band holds them down" reading I
pre-declared for a P4-fires/P5-refutes pair **is not triggered**.

The band's realised mean tracks P4's implied share monotonically across all three years —
**44.107 → 53.523 → 135.993 MW** against implied **0.042 → 0.167 → 0.521** — which is the
consistency P4 and P5 were declared to have.

**The decisive number is the bound, and it needs no attribution assumption at all** (post-hoc
diagnostic D1, labelled as such). Because the duct population's whole capacity is **716.761 MW**
(§1), every MW the band carries **above** that line is provably cohort generation:

| year | band peak energy | **cohort lower bound** | hours | cohort EIA-923 net | bound ÷ measured |
|---|---:|---:|---:|---:|---:|
| 2023 | 386.4 GWh | **4.778 GWh** | 38 | 5.589 GWh | **0.855** |
| 2024 | 468.9 GWh | 0.021 GWh | 2 | 6.371 GWh | 0.003 |
| 2025 | 1,191.3 GWh | **5.801 GWh** | 104 | *(unavailable)* | — |

**In 2023 the model puts at least 85.5 % of the cohort's entire measured annual energy through in
38 hours — 0.43 % of the year — and that is a strict lower bound**, counting only hours in which
the band exceeds the duct population's total capacity and ignoring every other hour. The cohort's
measured capacity factor is **0.00144** (5.589 GWh over 441.7 MW).

**Three limits on this bound, stated rather than absorbed.** (i) It is model **gross** band MW
against EIA-923 **net** generation. (ii) It is a **lower** bound only, so 2024's 0.003 is **not**
evidence the cohort under-runs that year — it says only that the band stayed under the duct
ceiling, which the duct population alone can produce. (iii) **2025 has no denominator**: EIA-923
returns 0.0 for these plants on the preliminary vintage, which is the same incompleteness that
makes the keeper's own C1 2025 class cells SKIPPED (11/20 `CC_REGULAR` plants missing, 45 %
reporting). The 2025 ratio is **undefined, not zero**, and is printed as such.

## 6. OWNER DECISION CARD — the duty-role level's basis. **Nothing is built, armed or proposed**

The membership rule is sound (§3). The open question is the **level**, and it is a modelling
decision with a forward story at stake, not this lane's call.

`cc_reserve_duty_split`'s own docstring is explicit that the level is borrowed: *"the level is the
class's existing identified peak multiplier — zero new scalars (rule 21)."* That is an honest
rule-21 `[R-DOF]` motivation, and its consequence is now measured: **one number, `2.25`, carries
two unrelated meanings** — the duct-firing physical heat-rate increment of a large 2×1 combined
cycle (`phys_peak`, which nyiso-194 and nyiso-195 have already closed in **both** directions), and
the out-of-merit distance of a capacity-only cogen. This is the rule 19 `[R-ONE-MECH]` shape
nyiso-212/-213 repaired at the summer seam and nyiso-214 measured at the duct gap, appearing a
third time in the same class.

**The question for the owner:** should a duty-role cohort's offer position be expressed in
**cost** space (a heat-rate multiplier, as now — which the meter says drifts out of position as
the price level moves, and whose error changes sign by zone), or in **price-percentile** space
(an offer positioned at the percentile of its own zone's price distribution that its measured duty
implies)? And if the latter, is a percentile read off the model's own price distribution
admissible under rule 13 `[R-MEASURED]`'s forward test, or does it have to be identified from the
plants' measured conduct alone?

**Deliberately not answered here**, and deliberately not sized: sizing a form invites choosing one,
and this session has **no dispatch evidence at plant grain** (the committed sidecars are class- and
band-level; a plant-grain answer needs a replay this session did not spend). Two constraints any
successor inherits, stated so the card is not re-opened naively:

* **The band's price is closed in both directions** — nyiso-194 killed the CC_REGULAR peak band
  UP (2.25 → 2.50) on shape, nyiso-195 killed the econ ramp DOWN to its `phys_*` basis on
  direction, `phys_peak == peak`, and rule 1's carve-out conditions are not met. **A successor
  must not move `2.25`**; it must give the duty-role cohort its own basis, or route it elsewhere.
* **54034 Rensselaer is a counter-example inside the cohort** (§4) and any form must explain it,
  not average it away.

**This card is NEW and prejudges none of the six pending owner rulings**, including nyiso-214 §6's
membership card: that card is about `cc_duct_peaking`'s **membership** at the large flagged
plants; this one is about `cc_reserve_duty_split`'s **level** at seven small unflagged ones. The
two mechanisms are disjoint by cohort — **two of these seven (50744, 54593) carry no `Y` row at
all** — and no form of A/B/C/D/E is built, armed, screened or recommended here.

## 7. Governance, environment, and things found on the way

* **Rule 29 `[R-SCREEN]`:** step 0 only. **No screen, no control, no bundle, no LP.** Nothing to
  delete before merge under 29(c); the control question does not arise. **G-DRIFT** was audited
  hunk-by-hunk in the PREREG §6 (`51f2fc2d` → `dcb609f4`, 11 files, +9,341/−22): ten INERT
  (CAISO/SPP branches, and the `capacity_screen_peak_measured_hindcast` flip whose consumer a
  `mode="backcast"` run never enters), one **LIVE but out of this session's scope**
  (`data/eia930/actuals.py`'s `_screen_fuel_spike_columns`, which screens `NG:` unit-slip hours for
  **every** BA and can therefore move the C1/C4 benchmark — **recorded, not absorbed: a NYISO lane
  that re-solves or re-scores C1/C4 owes it a check**). **Inertness confirmed by execution, not by
  reading:** `scripts/probes/nyiso196_rebuild_checks.py --year 2024` reproduced its committed
  record **byte-identically** with `git status --porcelain -uno` empty, and P1 reproduced
  nyiso-214's 441.7 MW census to 0.0 % and its 716.8 MW duct figure to 0.039 MW.
* **Rule 22 `[R-HOLDOUT]`:** training-tier only — 2023–2025 meters and the keeper's own fleet and
  sidecars. **No out-of-training year was solved, scored or registered.** `complete` / `frontier`
  and the locked-test freeze are untouched; **2020/2021 stay unspent and were not this session's
  spend**; `final` remains never granted.
* **Rule 15 `[R-DASHBOARD]`:** no run was produced, so there is nothing to register and
  keeper-only retention is untouched.
* **Rule 28 `[R-MECH-MATRIX]`:** `cc_reserve_duty_split` is registered on the `offer_curve_by_group`
  base row; NYISO's shard cell is stamped in this session with this audit, negative half included.
* **Rule 23 `[R-FROZEN-DERIVE]`:** `derive_reserve_duty_cc.py` was **audited, never re-derived**.
* **Markers:** none moved. No promotion contemplated, so D-5(b) does not attach.
* **The six pending owner rulings are untouched**; §6 opens a **seventh** card and prejudges none.

**Determination re-verified, and a reader trap found while doing it.** The keeper reads
**CALIBRATED** — `scripts/calibration_verdict.py --run-id 2026-09-07-nyiso-213-summer-seam` at this
HEAD, committed artifacts only, no solve: grade 7 scored, **0 fails**, C3c the lone ledgered caveat
(2 h / 0 h / 3 h vs 10 / 13 / 42 h > $300), C1 14/14 free 10/10, C2 / C3a / C3b / C4 / C6 / C8
PASS. **But the bundle's own committed `results/calibration/nyiso213_summer_seam/metrics.json`
reads `determination: NOT-YET`**, on the single reason *"governance gate UNATTESTED: no governance
attestation in bundle"* — a stale in-run artifact written before `calibration_attestation.json`
(which **is** present) landed in the bundle. It is **not** a determination defect: nothing reads it
to determine anything, and the scorer's `--run-id` path — the route rule 22 D-5(b) mandates —
re-scores from artifacts and returns CALIBRATED. It **is** a trap, and this session walked into it
before checking. **It is systemic, not NYISO's:** the identical stale reason appears in
`neiso105_offerlevel`, `neiso99_joint_B`, `nyiso202_startup_aware`, `nyiso213_tp2022`,
`pjm169_tp2022_2021_f2arm` and `pjm_debugb_inputclock_A`. **Not repaired here** — it would touch
four other ISOs' committed bundles, which is out of this lane (rule 27 `[R-PUSH]`, and the per-ISO
discipline of the keeper shards) — and it is reported so the next auditor reads the scorer, not
the file.

**No unit test covers `cc_reserve_duty_split`'s split behaviour.** `grep` over `tests/` returns
only cache-key fixtures. Named, not closed: a guard encoding the *current* two-basis membership
mix would lock in §3's defect, and the level question is unresolved, so the useful test is the one
a successor form writes.

* **Environment, measured at HEAD `dcb609f4`:** `data/clean` built with
  `curate_capacity_deliverability.py` + `curate_nyiso_interface_flows.py` only. Test set run this
  session, **named rather than inherited** — `tests/scoring/test_gate_a_provenance.py`,
  `tests/unit/data/test_cc_summer_derate_reconciled_basis.py`,
  `tests/scoring/test_holdout_render_parity.py`, `tests/unit/data/test_campd_bins.py` —
  **75 passed, 0 failed**. `ruff format --check .` reads **1,405 files already formatted** and
  `ruff check` passes. **No pre-existing failure was found at this HEAD**, re-measured rather than
  inherited: the `test_gate_a_provenance::test_live_board_passes` failure that nyiso-210/-211/-212
  recorded, and that nyiso-213 and nyiso-214 re-measured as repaired, is still passing.

## 8. Reported at full magnitude

* **Two of five pre-registered gates did not fire on their literal terms** (P2's 400 MW magnitude
  limb, short by 2.252 MW; P5's 2.0 % exceedance limb, short by 0.81 pp), and **neither gate was
  rewritten after the numbers were seen**. P2's outcome partition was additionally **not
  exhaustive** — the measured 7-of-7 with a fall < 400 MW falls through all three declared
  branches. Both misses are on magnitude sub-bars whose qualitative limbs fired unambiguously, and
  saying so is not the same as saying the gates fired.
* **This session's own analytic claim in the PREREG was wrong and is corrected in §3**: CF ≤ online
  share is not an identity, and one measured ratio exceeds 1.
* **P4's denominator is pooled and its numerator is per-year.** The cohort CSV's `duty_stat` is a
  single pooled 2023–2025 figure, so **all** of the ratio's year-to-year movement comes from the
  model side. The comparison against a pooled target is still the right one — that is the target
  the mechanism was built to reproduce — but the year profile is a statement about the model, not
  about changing conduct.
* **P4 is an upper bound and the LP does not realise it.** At the 2025 implied share the cohort
  would produce ~2,015 GWh at full `pmax`; the whole peak band's realised 2025 energy is
  1,191.3 GWh, duct included. The upper bound is **not** a claim about realised energy — the
  realised claim is D1's lower bound, and only that.
* **The one intra-cohort counter-example is named, not averaged**: 54034 Rensselaer runs the
  mechanism the wrong way by an order of magnitude in all three years (§4).
* **The favourable direction of §6's framing was noticed after the measurement, not before**, and
  no successor form is sized or recommended — deliberately, because sizing invites choosing.
* **Nothing here is dispatch evidence at plant grain.** Every dispatch number is class- or
  band-level, read from committed sidecars. A plant-grain answer needs a replay this session did
  not spend, and the finding claims nothing that requires one.

*(nyiso-215, 2026-09-07. Zero LP. The gates were written and pushed before the census; three fired,
two missed a magnitude limb and were reported as written; the object moved from "is this a builder
artifact" — answered no — through a membership audit that the incumbent survives, to a measured
level defect handed to the owner rather than levered.)*
