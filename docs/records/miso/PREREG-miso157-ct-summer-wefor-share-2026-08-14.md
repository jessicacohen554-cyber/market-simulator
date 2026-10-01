# PREREG — miso-157: is MISO's peak price-setter held available at the summer peak by an **UNCITED HEURISTIC**? A measured confrontation of `SUMMER_WEFOR_SHARE = 0.30` on `CT_PEAKER`

**Session** miso-157 · **ISO** MISO · **Date** 2026-08-14 ·
**Keeper** `2026-08-09-miso-148-basis-aware` (`miso148_basis_B`), **UNCHANGED at
pre-registration** · **Model** `claude-opus-5` (rule 27 `[R-PUSH]`: this scope
may write `src/market_sim/`, so Opus/Fable only).

**This document is pushed and blob-verified against the FETCHED remote ref
BEFORE any adjudicating statistic is computed** (rule 27 `[R-PUSH]`).

**Rule 22 `[R-HOLDOUT]`:** 2023 / 2024 / 2025 ONLY. MISO holds **NEITHER**
`complete` NOR `final`. No holdout year is read, solved, scored or registered
anywhere in this session. Any run produced covers all three train years in ONE
bundle (rule 16 `[R-ALLYEARS]`).

**OWNER CHARTER (this session, 2026-08-14): branch (A), THE PEAK CUSHION** — a
rule-14 `[R-ACCURATE]` **measured availability confrontation**, explicitly *not*
a fitted derate and explicitly *not* an arm of `miso_native_outage_source` as
constructed. The same sitting **blessed the gated production-engine floor
rebuild** (`_miso156_c3a_decomposition.model_year`) as the canonical
reconstruction of the reliability-floor array, closing miso-156's open
governance item.

---

## 0. The object

miso-156 closed its lane on a question, not a lever: **what makes the model's CT
stack stop climbing at ~12 MMBtu/MWh when 28.8 is inside its own fleet's range?**
The owner chartered the cushion half of that question.

Following the charter into the code lands on one line, and it is not a
generality. For `CT_PEAKER` on this keeper, three facts compose:

1. **CAMPD contributes no measured outage to CT at all.** miso-87 measured
   **25.0 GW** of MISO peaking capacity (CT_PEAKER 22.4 + CT_CHP 2.6) carrying
   CAMPD unavailability of **exactly 0.000**, and named it *"the CT coverage
   hole … modelled today only by the statistical WEFOR/POF layer. **Own charter,
   own evidence.**"* That charter has been open since 2026-07-24. This is it.
2. **The code says so in as many words.** `data/fleet/arrays.py:412-415`:
   *"CTs have no overlay coverage and keep the full statistical model."* The
   keeper carries `wefor_residual = None` and `wefor_multiplier = 1.0`, so no
   cap and no scaling intervenes.
3. **That statistical layer removes 70 % of CT's forced outages from the summer.**
   `arrays.py:773-791`, the final `else` branch that non-floor `CT_PEAKER` rows
   take:

   ```
   summer_wefor          = _SUMMER_WEFOR_SHARE * wefor          # 0.30 · W
   availability[summer]  = 1 - summer_wefor - derate            # Jun-Sep
   availability[:]       = 1 - wefor - derate                   # winter
   availability[shoulder]= 1 - (W + 0.70·W·(122/153)) - derate   # Mar-May, Oct-Nov
   ```

And `SUMMER_WEFOR_SHARE` carries this provenance, verbatim from
`config/fuel_trajectories.py:894-900`:

> **"SOURCE: NONE — this is an UNCITED A-PRIORI HEURISTIC, declared as such
> rather than given a false provenance (CLAUDE.md rule 5 `[R-NO-MAGIC]`). …
> It was NOT fitted to any residual; no derivation, sweep or calibration lineage
> exists for the 0.30. It is declared in the MISO keeper's DOF ledger under
> identification `residual` — the strictest existing enforcement category, which
> forces an open root cause (`audit_keepers.py` E8)."**

So the summer-peak availability of the class that sets MISO's summer peak price
— `CT_PEAKER`, in **66.0 %** of 2025 top-200 zone-hours (miso-153 D-3), holding
**70–74 %** of the idle block and **6.31 GW within $20/MWh** of the clearing
price (miso-153 D-1) — is governed by a parameter whose own definition says it
has no source. **Rule 20 `[R-DOF]` classifies that as an open root-cause issue,
not a parameter.** This session measures whether it is right.

**Two things this document is careful not to claim.** It does not assert the
heuristic is wrong — that is the measurement. And it does not assert that
correcting it closes C3a; §5.4 pre-registers, against interest, that it
**cannot**.

### 0.1 What I inspected BEFORE writing this document (disclosure)

Plumbing, provenance, definitions and **already-published numbers** — the
miso-156 §0.1 standard. **No measured outage value, no model availability array,
no price statistic** was computed.

* `data/fleet/arrays.py` — `_thermal_outage`, `_apply_thermal_availability` and
  its five branches; `_SUMMER_MONTHS = {6,7,8,9}`,
  `_CC_SHOULDER_MONTHS = {3,4,5,10,11}`, `_SUMMER_WEFOR_SHARE`.
* `config/fuel_trajectories.py:871-900` — the `THERMAL_AVAILABILITY` table
  (`CT_PEAKER` = POF 0.03, WEFOR base 0.07 + 0.003/yr past age 20, DERATE base
  0.05 + 0.002/yr past age 20; source NERC GADS by unit type and age) and the
  `SUMMER_WEFOR_SHARE` provenance block quoted above.
* The keeper's `run_config.json` armed-field census (709 fields):
  `outage_source = historic`, `wefor_residual = None`, `wefor_multiplier = 1.0`,
  `temp_derate_classes = ['CT_CHP','ST_CHP']` (**`CT_PEAKER` absent**),
  `gt_ambient_derate = False`, `summer_derate_basis_aware = True`,
  `historic_outage_overlay = False`, `miso_native_outage_source = False`.
* `data/miso_outages.py` module docstring + composition comments;
  `data/raw/miso-generation-outages/_SOURCE.md`; the committed CSVs' **header
  line and row counts only** (16 `<Region>_<CauseType>` columns; 365 / 366 / 365
  rows for 2023 / 2024 / 2025). **I did not read a single outage MW value.**
* Published prior results, cited as such: miso-153 D-1/D-2/D-3, miso-155's CT
  volume result, miso-156's decomposition and against-interest bound, miso-86's
  reversal record, miso-87's refutation of the cross-fuel attribution lever.
* The matrix shard cells for `dam_availability_rebasis` (**R**),
  `ordc_scarcity_overlay` (**G**), `maxgen_emergency_tier_pricing` (**K**),
  `historic_outage_overlay` / `unit_outage_lp_capacity_basis` /
  `nuclear_unit_availability` (**U**).

**DISCLOSED BECAUSE IT INFORMS §5's PRIORS AND WOULD OTHERWISE LOOK PRESCIENT.**
Two committed in-repo comments carry measured summaries I read while
establishing provenance, and I register their effect on my priors rather than
pretending to a blind band:

* `miso_outages.py:95-101` — *"'Forced' and 'Unplanned' are flat year-round (no
  shoulder peak), and 'Derated' peaks in **JULY-AUGUST (10.5 GW vs 6.0 GW in
  March)** — the ambient summer capability derate GADS EFORd counts"*, and the
  unplanned-only fleet-average availability **0.816 / 0.795 / 0.763** against the
  CAMPD per-unit derate's **0.763 / 0.768 / 0.782**.
* miso-86's log entry — *"`Derated` peaks July–August as an ambient derate
  must"*, and per-class CAMPD unavailability COAL 0.332/0.325/0.264, ST_GAS
  0.589/0.529/0.508, CC_REGULAR 0.200/0.210/0.251, **CT 0.000**.

These fix the *direction* of Leg 1's primary comparator before I measure it, so
**my §5 prior for `R_meas^MISO` is informed, not blind, and I say so.** What they
do **not** fix, and what this session actually adjudicates: the composite
unplanned-only ratio at the model's own Jun–Sep partition, the class-resolved
CAMPD cross-check, the model-side ratio, and the MW at stake — none of which is
published anywhere.

---

## 1. What is established and is NOT re-derived

* miso-152's monthly localization; miso-153's D-1 cushion, D-3 peak-setter and
  D-4 reserve inertness; miso-155's CT volume result (**−0.89 / −0.26 / −0.52 %**,
  so there is no CT volume residual left to attribute); miso-156's decomposition,
  its two minted verdicts and its computed against-interest bound.
* **DO-NOT-REDO (rule 28(a)), none re-tested here:** `gas_hub_basis_overlay`
  **R**, `ramp_envelopes` **I**, `measured_offer_surface` **R**, the across-unit
  dispersion object (**CLOSED**, three grounds), the base-band inversion
  (IMMATERIAL), the D-4 all-hours window flag (WITHDRAWN), CT min-run/min-down
  (ABSENT), `cc_nameplate_summer_derate` (wrong direction),
  `gas_commitment_bridge` (cannot bind), C7 `COAL_PRB` (owner-DEPRIORITIZED),
  and **the CT offer-LEVEL lever on volume grounds** (miso-155 §8).

---

## 2. Rule 28(a) — why this is NOT a re-test of `dam_availability_rebasis` **R**, confronted head-on

MISO already tried a published-outage lever and it was reverted. The distinction
is load-bearing, so it is made **before** the measurement, not after:

| | what was closed | what this session does |
|---|---|---|
| **miso-85/86, `dam_availability_rebasis` R** | **ARMED** `miso_native_outage_source`, **replacing** the CAMPD per-unit derate with a uniform whole-fleet **LEVEL** envelope. Reverted on **grain** (owner call): the record has no fuel identity, so it returned ~5 GW of out-of-service coal to the merit order and stripped ~4–5 GW off peakers *"nothing says were out"*. | **Arms nothing.** No overlay is applied; CAMPD keeps every class it covers; no MW is attributed across fuels. |
| **miso-87, cross-fuel attribution — REFUTED AT CHARTER** | Ground 1: the **level** reconciliation is ~0 in 2023–24 and **flips sign** in 2025 — the record's resolution limit. Ground 2: **no admissible key** to attribute MW across fuels; using CAMPD as the key reduces to a scalar level knob. | Uses **no key and no level**. The measured quantity is a **within-series seasonal RATIO** (Jun–Sep ÷ annual) of one published series, which attributes nothing and needs no thermal share. |

**And miso-87 named this exact successor as the thing that remained open:** *"the
CT coverage hole — 25.0 GW … carrying CAMPD unavailability of exactly 0.000,
modelled today only by the statistical WEFOR/POF layer. **Own charter, own
evidence.**"*

**The ratio construction is not free of the grain problem, only of that
version of it,** and the residual exposure is pre-registered as **T-25**: a
whole-fleet ratio transfers to a thermal class only if the thermal share of
offline MW is not itself seasonal. That assumption is counter-measured, not
assumed, and **B-DISAGREE exists precisely to fail this session if the two
comparators diverge** — which is the miso-87 Ground-1 signature reproduced as a
kill gate rather than argued away.

---

## 3. Rule 19 `[R-ONE-MECH]` — everything that already shapes `CT_PEAKER` availability at the summer peak, enumerated before any lever

1. **`SUMMER_WEFOR_SHARE = 0.30`** (global constant, no `ScenarioConfig`
   override exists) — **the object**. Owns the *seasonal shape* of forced
   outages. Annual outage energy is conserved by construction.
2. **`THERMAL_AVAILABILITY["CT_PEAKER"]`** — owns the *level* (WEFOR + DERATE +
   POF, NERC GADS-cited). **Not this session's object**; a level change is a
   different mechanism and is not proposed.
3. **`wefor_multiplier = 1.0`** — a registered level knob, at neutral. Owns
   scaling, not season.
4. **`ct_floor_plants` (reliability must-run floor units)** — a *different
   availability branch entirely* (`availability = 1 − derate`: **no WEFOR in any
   month, no POF**). This sub-population is not governed by the object at all;
   separating it is trap **T-24** and surprise trigger **S-FLOORPOP**.
5. **Ambient/capability derates — none reach `CT_PEAKER` on this keeper:**
   `temp_derate_classes` is `['CT_CHP','ST_CHP']`, `gt_ambient_derate = False`,
   and `cc_nameplate_summer_derate` is CC-only. So no second mechanism is being
   stacked on the same phenomenon.

**Conclusion drawn before measuring:** for non-floor `CT_PEAKER`, summer
availability is `1 − 0.30·WEFOR − DERATE` and **nothing else**. One mechanism,
one phenomenon.

---

## 4. The measurement — two legs, both fixed here

**Instrument.** `scripts/probes/_miso157_ct_summer_wefor.py`, record
`results/calibration/_miso157_ct_summer_wefor.json`. Production types only, the
keeper's own config, `weather_year` pinned per solve year.

### Leg 1 — SHAPE: is 0.30 supported by measurement?

Three ratios, all Jun–Sep ÷ full-year on the **model's own month partition**
`_SUMMER_MONTHS = {6,7,8,9}`:

* **`R_mod`** — the model's own `CT_PEAKER` cap-weighted mean *unavailability*
  (`1 − availability`), Jun–Sep ÷ annual, from the production
  `generators_to_fleet_arrays` array. Reported **separately** for the non-floor
  and `ct_floor_plants` populations (T-24).
* **`R_meas^MISO`** — MISO's published record, **unplanned-only composite**
  (`Derated + Forced + Unplanned`, `Planned` excluded — the composition settled
  at miso-85 and not re-opened), region `MISO`, daily MW, Jun–Sep ÷ annual.
  Reported **also on the `Derated` bucket alone** (T-25), that being the ambient
  component whose thermal attribution is physical rather than assumed.
* **`R_meas^CAMPD`** — the same ratio computed from MISO's committed CAMPD
  per-unit outage extract over the classes CAMPD actually covers (COAL, ST_GAS,
  CC_REGULAR, CC_CHP, ST_CHP), capacity-weighted. **Class-resolved and
  MISO-specific**, and therefore the answer to miso-87 Ground 2's contamination
  worry — at the price of the documented phantom-outage bias
  (`FINDING-ercot79-phantom-outage-2026-07.md`), whose direction is pre-declared
  in §5.

Also reported, because miso-152/153 localized the miss to **Jun+Jul** while the
model's partition is **Jun–Sep**: every ratio on **both** windows (T-29). The
model-partition figure is the adjudicating one; the Jun+Jul figure is reported
alongside and never substituted for it.

### Leg 2 — MAGNITUDE: can it reach the cushion?

Pure arithmetic on the model's own arrays, no solve:

    ΔMW(top-200) = Σ_g pmax[g] · ( avail[g, 0.30] − avail[g, R*] )   over CT_PEAKER,
                   averaged over the top-200 model-demand hours of Jun–Sep

with `R*` the adjudicated measured share from Leg 1. Compared against miso-153
D-1's published **6.31 GW of CT idle within $20/MWh** of the 2025 clearing price
and **11.25 GW** of total idle CT — the cushion the lever would have to eat into
to move the marginal unit.

**No LP is solved in Phase 0.** Leg 2 bounds the reach; it does not claim a price
effect.

---

## 5. Priors — two-sided, numeric, committed before measurement

| # | quantity | prior band | centre |
|---|---|---|---|
| **P-1** | `R_mod` (non-floor CT_PEAKER) | **0.40 – 0.65** | **0.55** |
| **P-2** | `R_meas^MISO`, unplanned-only composite | **1.00 – 1.35** | **1.15** |
| **P-3** | `R_meas^CAMPD`, class-resolved | **0.55 – 1.05** | **0.80** |
| **P-4** | `ΔMW(top-200)`, 2025 | **1.0 – 3.0 GW** | **1.9 GW** |
| **P-5** | `ct_floor_plants` share of CT_PEAKER capacity | **5 – 30 %** | **15 %** |

**P-1 is derived, not guessed, and its arithmetic is on the record so a miss is
diagnostic.** For a median-age (~30 yr) CT_PEAKER: `W = 0.07 + 10×0.003 = 0.10`,
`D = 0.05 + 10×0.002 = 0.07`, `P = 0.03`. Summer unavailability
`= 0.30×0.10 + 0.07 = 0.100`; annual `≈ W + D + (5/12)·P = 0.100 + 0.070 + 0.0125
= 0.1825`; ratio **0.548**. This also predicts summer availability ≈ **0.90**,
which is why **V1** can gate on miso-153's published 0.923/0.926/0.919.

**P-2 is INFORMED by the §0.1 disclosure**, not blind: the committed comment
already says `Derated` peaks Jul–Aug and Forced/Unplanned are flat, so a
composite ratio above 1 is expected. The band's *lower* half is what carries
information — a composite at or below 1.00 would mean the flat buckets dominate
the ambient one and my reading is wrong.

**P-3 is pre-declared as the hostile comparator.** CAMPD's detector books
economic idleness as outage, and CC/coal are economically idle in the
**shoulder**, not in summer — so I expect CAMPD's summer ratio to read **low**,
and a low value is **NOT** evidence for the 0.30 heuristic. I register the
direction of that bias now so it cannot be produced later as an excuse; and
**B-DISAGREE and S-PHANTOM both exist to stop me doing exactly that.**

**Two-sided against my own branch.** If `R_meas^MISO` lands **below 1.00**, the
charter's premise is refuted: the real MISO fleet genuinely does carry less
unplanned unavailability in summer, 0.30 is merely un-cited rather than wrong,
and **B-SUPPORTED stops the session**. Equally, if `ΔMW` lands **below 0.5 GW**
against a 6.31 GW cushion, the shape can be as wrong as it likes and the lever
still cannot lift a marginal unit (**B-INERT**, rule 26).

### 5.4 What this lever CANNOT do — registered before measuring so it cannot be re-scoped later

**Stated against interest.** A share correction is a **pure seasonal
reallocation** that conserves annual outage energy (the code's own docstring:
*"The annual-average availability of each unit is unchanged — only the seasonal
shape moves"*). Working the arithmetic forward with P-2's centre: Δunavailability
`= (1.15 − 0.30) × 0.10 = 0.085` on ~22.4 GW of CT_PEAKER ⇒ **~1.9 GW**, which is
**~30 % of the 6.31 GW within-$20/MWh cushion**. Spread over Jun–Sep (2,928 h,
33 % of the year) and offset by *cheaper* shoulder months, I pre-register the
expected 2025 annual C3a improvement at **+0.3 to +1.5 pp on a −15.6 % miss** —
i.e. **this lever closes on the order of a tenth of the gap and cannot close
C3a.** If it is armed it will be armed under rule 1 `[R-STRUCT]` — because a
parameter with no source governs the price-setting class and a measured one is
available — **never** as a fix for C3a.

**S-REACH** (§6.1) fires if the measured reach exceeds **+3 pp**, because that
would mean this arithmetic is wrong by 2× or more and the instrument should be
disbelieved before it is celebrated.

### 5.5 AGAINST-INTEREST BOUND and the EXPECTED 2023 EFFECT — stated BEFORE any solve

The bound (inherited, computed at miso-156): **a lever that lifts 2023's mean by
more than +3 % is a REGRESSION even if 2025 improves.** 2023's model mean is
**$32.18**, so the ceiling is **+$0.965/MWh**.

**This lever is summer-scoped, and 2023's summer is where it is most exposed:**
2023's Jun+Jul Δ₁ is **NEGATIVE (−5.090 $/MWh)** — in 2023's summer the model's
marginal unit is **already more expensive** than the market's. Raising 2023's
summer availability cost pushes that cell **further the wrong way**. The annual
figure hides this; I am not hiding behind it.

**Pre-registered expected 2023 effect: +$0.4 to +$0.9 /MWh annual mean
(+1.2 % to +2.8 %) — inside the +3 % bound, but with under one percentage point
of margin.** Kill gate **K-1** makes that binding: a measured 2023 lift above
**+3.0 %** kills the lever regardless of what 2025 does.

---

## 6. Branches — fixed here, with their consequences

| branch | condition | consequence |
|---|---|---|
| **B-ARM** | `R_meas^MISO ≥ 1.00` **AND** `R_meas^CAMPD ≥ 0.90` **AND** `ΔMW(2025) ≥ 1.0 GW` | The heuristic is refuted **with a measured replacement in hand**. Proceed to Phase 1: a **MISO-scoped `ScenarioConfig` field** (rules 24/25 — the global constant is never edited), a **SECOND pre-registration stating the expected 2023 effect**, then the rule-12 per-year solve chain. |
| **B-DISAGREE** | the two measured comparators differ by **> 0.25** in ratio | The miso-87 Ground-1 signature. **NO LEVER, NO SOLVE.** Both reported at full magnitude; the disagreement *is* the finding. |
| **B-SUPPORTED** | `R_meas^MISO < 1.00` **AND** `R_meas^CAMPD < 1.00` | Measurement supports the heuristic's **direction**. The charter's premise is refuted. Report the measured value, **arm nothing**, **STOP**. |
| **B-INERT** | `ΔMW(2025) < 0.5 GW` | Whatever the shape says, the lever cannot reach the cushion (rule 26). Report and **STOP**. |

**Precedence: B-DISAGREE > B-INERT > B-SUPPORTED > B-ARM.** A session that can
reach B-ARM only by ignoring a fired higher-precedence branch does not reach it.

**In every branch the full ratio table is reported for all three years, both
windows, both CT populations, and all three comparators.** No branch permits
arming a mechanism whose comparator did not clear, and none permits quoting the
Jun+Jul window as the adjudicating one.

### 6.1 Pre-committed surprise triggers

| trigger | fires when | what I do |
|---|---|---|
| **S-V1** | the reconstruction misses miso-153's published CT Jun+Jul availability by > 0.02, or D-1's top-200 available GW by > 2 % | The instrument is not the one that cleared. **Stop, debug, disclose before any conclusion.** No adjudicating statistic is quoted. |
| **S-FLOORPOP** | `ct_floor_plants` exceeds **40 %** of CT_PEAKER capacity | The object is **not** the dominant CT availability channel — the reliability floor is, and rule 19 re-points the charter. Disclose and re-scope; do not proceed on the pooled number. |
| **S-PHANTOM** | `R_meas^CAMPD < 0.70` | The phantom-outage bias is too large for CAMPD to serve as the cross-check at all. Say so; the branch then rests on **one** comparator, which is **weaker**, and B-DISAGREE is evaluated on that basis rather than waived. |
| **S-AGE** | cap-weighted CT_PEAKER WEFOR falls outside **0.07 – 0.13** | §5.4's ΔMW arithmetic is mis-parameterized. Re-derive it from the measured age distribution and report both. |
| **S-REACH** | estimated 2025 C3a reach exceeds **+3 pp** | Too good for the mechanism's own arithmetic. **Disbelieve and re-derive** before reporting it as a result. |
| **S-DERATE-SPLIT** | the `Derated`-only ratio and the composite ratio differ by **> 0.30** | The composite is being driven by a bucket whose thermal attribution is assumed rather than physical (T-25). Report both; adjudicate on the **more conservative** of the two. |

---

## 7. Validity gates — reproduce published numbers BEFORE any adjudicating statistic

Run first, in this order. The miso-154 void-run precedent is binding.

* **V1 — the reconstruction is the keeper's own fleet availability.** Reproduce
  miso-153's published `CT_PEAKER` Jun+Jul cap-weighted availability
  **0.923 / 0.926 / 0.919** to **±0.02**, and D-1's top-200 total available
  **93.28 / 92.41 / 89.09 GW** to **±2 %**. A miss fires **S-V1**.
* **V2 — the fleet census matches.** `n_gen` = **2929 / 2923 / 2923**
  (miso-155/156); carry-zone count **== 6**.
* **V3 — the measured record's own internal identity.** `MISO_<cause>` must equal
  `North_<cause> + Central_<cause> + South_<cause>` to **±1 MW** on every day of
  every year, and the row counts must be **365 / 366 / 365**. This is the record
  checking itself — a second derivation, not a spot check (T-3).
* **V4 — `weather_year` pinned per solve year** via
  `dataclasses.replace(cfg, weather_year=y)`; V1 is its control.

**Environment integrity, to be executed and recorded in the finding:**
`git status --short | grep -c '^ D'`; whether a `.venv` shipped; `data/clean`
state.

**Contingency, pre-registered.** If Phase 1 is reached but the rule-12 per-year
chain cannot complete all three years in this session, **no solve-based statistic
is quoted**: the session reports Phase 0 complete, the lever named-but-not-armed,
and registers **nothing**. A partial-year solve is **never** registered
(rule 16 `[R-ALLYEARS]`).

### 7.1 Kill gates for Phase 1 (binding if B-ARM is taken)

* **K-1** — 2023 annual mean LMP lift **> +3.0 %**: **KILL** (§5.5).
* **K-2** — any currently-PASSING gated criterion (C1, C2, C3a-2023, C3a-2024,
  C4, C6, C8) crosses into FAIL in any year: **KILL**.
* **K-3** — the arm changes annual mean `CT_PEAKER` availability by more than
  **1e-6** in any year: **KILL** — the mechanism is a seasonal reallocation, and
  a level change means it is not the mechanism claimed (T-27).
* **K-4** — the field is not MISO-scoped, or the global constant is edited:
  **KILL** (rules 24/25).

---

## 8. Traps, each with its counter-measurement

T-1…T-8 are inherited and re-run unchanged; T-24…T-29 are new to this charter.

| # | Trap | Counter-measurement |
|---|---|---|
| **T-1** | `_miso134` is HARD-WIRED to another bundle | Repoint to `miso148_basis_B` and **assert** at import |
| **T-2** | 3-arg `getattr` on the offer/availability path encodes a wrong field name | **Zero** 3-argument `getattr(` added; `grep` count reported; `ruff` clean |
| **T-3** | **Disbelieve clean zeros** | Every exact `0.0` in a reported aggregate gets a **second, different derivation** or is reported unverified |
| **T-4** | `SimpleNamespace` fixtures encode the same wrong name as the code | Production types only; assert no `SimpleNamespace` |
| **T-5** | `MISO_external*` are IMPORT NODES | Assert carry-zone count **== 6**; import nodes excluded from every aggregate |
| **T-6** | `_apply_outage_overlays` keys the CAMPD derate on `config.weather_year`, not the solve year (`arrays.py:1091-1092`) | `dataclasses.replace(cfg, weather_year=y)` **per solve year**; V1 is its control |
| **T-7** | An inert instrument looks like a fix | Report **GW and $/MWh magnitudes**, never only ratios and shares |
| **T-8** | A re-implemented production function reproduces my expectation, not the model's | **Assert** `generators_to_fleet_arrays.__module__`; the availability array is the production one, never rebuilt by hand |
| **T-24** | `ct_floor_plants` CT rows take a **different branch** (`1 − derate`, no WEFOR, no POF) and would dilute a pooled ratio | The two populations are measured and reported **separately**, never pooled; **S-FLOORPOP** gates the split |
| **T-25** | The MISO record is **whole-fleet**; a seasonal ratio transfers to a thermal class only if the thermal share of offline MW is not itself seasonal | Report the ratio on the **`Derated` bucket alone** (physically ambient/thermal) beside the composite; **S-DERATE-SPLIT** fires on divergence, and the **more conservative** figure adjudicates |
| **T-26** | CAMPD CT unavailability is quoted as **exactly 0.000** (miso-87) — a clean zero on the load-bearing class | Re-derive it **independently from the committed MISO CAMPD extract** rather than citing miso-87; report the second derivation's value whatever it is |
| **T-27** | A share change that also moves the annual level is not the mechanism claimed | Assert annual-mean availability invariant to **< 1e-6** under the counterfactual share (also kill gate **K-3**) |
| **T-28** | The 0.30 is a **global** constant, so a "MISO fix" silently moves five other ISOs | No edit to `SUMMER_WEFOR_SHARE`. Any Phase-1 arm is a **new MISO-scoped `ScenarioConfig` field** defaulting to 0.30 elsewhere (kill gate **K-4**), with its matrix row + a cell line in every shard in the same PR (rule 28(c)) |
| **T-29** | The model's summer is **Jun–Sep** while the miss is localized to **Jun+Jul** — picking the favourable window post hoc | **Both** windows reported for every ratio in every year; the **model-partition (Jun–Sep)** figure is the adjudicating one, fixed here |

---

## 9. Rules engaged

* **Rule 1 `[R-STRUCT]`** — the object is a parameter whose own definition says
  it has no source, governing the price-setting class. It is judged on whether
  measurement supports it, **never** on whether correcting it improves C3a —
  and §5.4 registers, before measuring, that it largely will not.
* **Rule 5 `[R-NO-MAGIC]` / 20 `[R-DOF]`** — `SUMMER_WEFOR_SHARE` is already
  carried in the keeper's DOF ledger under identification `residual`. Replacing
  a `residual` with a measured value **reduces** the ledger's open count; it
  adds no free parameter.
* **Rule 13 `[R-MEASURED]`** — the measured inputs are physical availability
  records; the forward analogue of a seasonal forced-outage share is the same
  statistical layer re-keyed, so it regenerates for a forecast year. Nothing is
  pinned to a price outcome and no residual is tuned to.
* **Rule 14 `[R-ACCURATE]`** — a measured seasonal shape is preferred to an
  uncited heuristic; §2 refuses in advance to reach it by the grain-broken route
  already rejected at miso-86.
* **Rule 19 `[R-ONE-MECH]`** — §3 enumerates every channel touching CT summer
  availability **before** any lever is named, and finds the object owns it alone.
* **Rules 24 `[R-REGISTRY]` / 25 `[R-ISO-SCOPE]` / 28(c)** — no global constant
  is edited; any arm is a MISO-scoped `ScenarioConfig` field in
  `run_config.json`, with its matrix row and a cell line in every shard in the
  same PR. Kill gate **K-4**.
* **Rule 23 `[R-FROZEN-DERIVE]`** — the measured share is derived from source
  data, never re-derived against a residual; a later change must cite a data
  change.
* **Rules 12 / 15 / 16 / 22** — years sequential in one bundle, any completed run
  registered in this session, all three train years, no holdout year touched.
* **Rule 27 `[R-PUSH]`** — Opus; local edits pushed as exact on-disk bytes; every
  push touching a ≥300-line file blob-verified immediately.
* **Rule 28(a)/(b)** — no `R`/`I`/`G` cell is re-tested (§2); the MISO shard is
  updated this session whatever the outcome.

---

## 10. Disclosure standard

Any statistic computed in this session that is **not** specified in §4–§8 is
labelled **NOT PRE-REGISTERED** where it is reported, with its
counter-measurement and its **full magnitude** — in the favourable and the
unfavourable branch alike. Scope extensions are disclosed, never silently folded
in.
