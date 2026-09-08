# CHARTER — the hydro budget period for the **whole fleet**, not just the two projects with a retrieved instrument

**Owner instruction, 2026-09-08, verbatim:** *"I don't think the other 145 should keep the month
that's the problem I think that's way too generous for how flexible hydro is. this deserves a
charter to get right"*.
**From:** session nyiso-220, NYISO `backcast-calibration` lane.
**ZERO LP in this document.** It authorizes nothing; building any of it is a separate owner decision
on §9. **Keeper `2026-09-07-nyiso-213-summer-seam` untouched** — nothing armed, registered or
promoted, no marker moved, no held-out year spent.

> **The headline.** The owner is right, and the evidence is already measured. On the screen arm's own
> per-unit hourlies, the **145 plants I left on a monthly budget are 18.8 % of hydro energy but carry
> 61.4 % of the remaining cross-day footprint** — an own-energy swing rate of **17.96 %, nearly 7×
> the 2.61 % of the two plants I did constrain**. School Street physically holds **0.101 h** — about
> six minutes — and swings **19.37 %** of its annual energy across days. **And the reason I left them
> alone was my own error**, not a data gap (§3): I applied an *instrument* test to plants whose
> identification route is *measured pondage*, which needs no instrument and which NID already covers
> for **98.53 % of fleet MW**.

---

## 1. Scope discipline, stated first

* **No in-sample rubric failure is being targeted.** NYISO reads **CALIBRATED**, grade 7/8, zero
  failing criteria across 2023–2025, C3c the lone ledgered caveat. Hydro is **not a rubric criterion**
  — no hydro row in `fuelRows`, no hydro record in any C-criterion. The object here is **structural**.
* **2022 is not touched.** Rule 22 `[R-HOLDOUT]`: the holdout motivates, never gates, and identifies
  nothing.
* **Nothing here is gated on a price residual** (rule 1 `[R-STRUCT]`). Rule 14 `[R-ACCURATE]` cuts
  both ways and is restated in §7 *before* any build: if the faithful representation makes the price
  fit worse, **it stays**.
* **Rule 25 `[R-ISO-SCOPE]`:** this charter is **NYISO-first**. NID covers every US dam, so the
  method is ISO-agnostic, but **no verdict or parameter transfers** — each ISO derives its own from
  its own fleet, and enters the matrix as `U`.

## 2. The object, measured — not asserted

From the nyiso-220 screen arm (`nyiso220_arm_2025`, a single-delta `replay_keeper` A/B on the keeper
recipe), decomposed over its **per-unit** hourlies. Zero further LP.

| | energy | share of hydro energy | cross-day footprint | share of residual footprint | swing rate (own energy) |
|---|---:|---:|---:|---:|---:|
| **Constrained** (2693 Niagara 24 h, 2694 St. Lawrence 168 h) | 19.541 TWh | **81.2 %** | 0.510 TWh | 38.6 % | **2.61 %** |
| **Unconstrained** (145 plants, still monthly) | 4.518 TWh | **18.8 %** | 0.811 TWh | **61.4 %** | **17.96 %** |

**The disproportion is the finding:** a fifth of the energy carries three-fifths of the defect, and
swings nearly seven times as hard per MWh. The worst offenders are small plants that physically hold
minutes:

| plant | name | measured pondage (generous upper bound) | swings, % of own annual energy |
|---|---|---:|---:|
| 2605 | School Street | **0.101 h** | **19.37 %** |
| 54953 | Hudson Falls | 0.163 h | 17.50 % |
| 54580 | Curtis | 2.024 h | 15.28 % |
| 2609 | Sherman Island | 20.659 h | 16.80 % |
| 2614 | Stewarts Bridge | 55.93 h | 21.50 % |
| 2612 | Spier Falls | 82.802 h | 17.61 % |
| 50512 | Glen Park | **no NID dam — no pondage at all** | 19.18 % |

*(Niagara does not appear: at a 24 h period it is fully constrained. St. Lawrence is the largest
single contributor at 8.17 % of its own energy, which is **correct and licensed** — its instrument
authorises exactly that day-to-day movement within the week.)*

## 3. My error, named — an instrument test applied to a pondage question

The nyiso-220 build registered only the two projects whose **governing instrument** I had retrieved,
and defended leaving the other 145 on a month with rule 14 `[R-ACCURATE]` — *"do not invent an
instrument we have not read"*. **That argument is sound but applies to the wrong route.** There are
two independent identification routes, and I conflated them:

* **Route A — the instrument states the conservation period.** St. Lawrence, 168 h, quoted verbatim
  from the IJC peaking-and-ponding directive. **Requires a document.**
* **Route B — measured pondage physically bounds banking.** Niagara, 24 h, from the treaty's silence
  *plus* the measured 0.244 h forebay. **Requires no instrument at all** — and nyiso-219 already
  measured pondage for **152 plants / 98.53 % of fleet MW** from the committed NID intake.

Route B was always available for the 145. Not using it was not caution about data we lack; it was a
misapplied test. **Rule 14 in fact points the other way here**: an accurate measured pondage is
available and a monthly period is the estimate that is silently compensating for its absence.

**A validation that makes Route B credible rather than merely available.** Where both routes exist,
they **agree, 2 for 2, on 71.4 % of fleet MW**:

| plant | Route B (measured pondage) | its bucket | Route A (instrument) | agree? |
|---|---:|---|---:|---|
| 2693 Niagara | 0.244 h | daily (< 24 h) | 24 h (derived from treaty silence + pondage) | ✔ |
| 2694 St. Lawrence | 73.07 h | weekly (24–168 h) | **168 h, stated in words by the IJC directive** | ✔ |

The independent, document-based answer for St. Lawrence lands in the bucket the measured pondage
predicts. That is the only out-of-sample test of Route B available, and it passes.

## 4. What a pondage-bucketed assignment would actually do

Census over the committed pondage index, using calendar-natural buckets (24 h / 168 h / 730 h — the
LP's own period grid, not fitted thresholds):

| bucket | plants | MW | % fleet MW |
|---|---:|---:|---:|
| **daily (< 24 h)** | 115 | 3,319.9 | **70.92 %** |
| **weekly (24–168 h)** | 22 | 1,166.6 | **24.92 %** |
| monthly-ish (168–730 h) | 7 | 46.3 | 0.99 % |
| **month or longer (≥ 730 h)** | 7 | 78.1 | **1.67 %** |
| **no pondage (no NID dam)** | 12 | 70.1 | 1.50 % |

**Only 1.67 % of fleet MW has the storage to justify the monthly period the model currently gives
100 % of it.** That is the quantitative form of the owner's instinct.

## 5. The risks — named before any build, because they are what a charter is for

**R1 — the head proxy, and it is the big one.** Pondage hours are `E = ρgVH / pmax`, so the bucket
depends on **head**. NID's `Hydraulic Height` covers only **20.50 % of fleet MW**; **78.03 % falls
back to a labelled dam-height proxy whose error runs in BOTH directions**, and 1.47 % has neither.
For Niagara this did not matter — the proxy erred in a known direction and the conclusion survived a
3× correction (0.244 h → ~0.75 h, still ≪ 24 h). **For a plant near a bucket boundary it matters
completely**: Spier Falls at 82.8 h (weekly) and Curtis at 2.0 h (daily) are both on the proxy, and a
2× head error moves either across a boundary. **This is the single most likely way a fleet-wide
build is wrong**, and it is not resolved by anything currently in the repo.

**R2 — over-constraint, which is this mechanism's known failure mode.** A shorter period is strictly
a *restriction* of the feasible set. With only **2** plants constrained, the screen's confinement
gate already **nearly missed** (CT_PEAKER +1.983 % against a 2.0 % gate, inside by 0.017 pp).
Constraining ~98 % of hydro MW is a far larger restriction and thermal displacement could be
substantial. Feasibility itself is a real possible outcome, not a bug to code around.

**R3 — rule 19 `[R-ONE-MECH]` must be re-decided, not inherited.** The Q2 posture (RECONCILE) was
settled on overlap arithmetic computed when **two** plants would be constrained. `hydro_dispatch_
envelope` is a **fleet-aggregate** hourly ceiling; extending the period to ~147 plants materially
raises the overlap, and the replace-vs-reconcile question must be **re-run at phase 0 on the new
arithmetic**. It may come out differently. Stacking remains not an option.

**R4 — the bucketing rule is where a free parameter would sneak in.** Mapping continuous pondage
hours onto a discrete period is a *rule*, and rule 21 `[R-DOF]` case 3 forbids choosing it because it
moves a criterion. It must be **declared ex ante in the PRECOMMIT and never swept**. Floor-to-the-
coarsest-period-not-exceeding-pondage is the natural, conservative reading; it is **not decided
here**.

**R5 — 12 plants (1.50 % of MW) have no pondage at all**, Glen Park among them, and it swings
19.18 %. A default is needed and every choice is a judgement: keep the month (generous, status quo),
inherit the fleet median, or inherit by river. **Not decided here.**

**R6 — the "generous upper bound" framing inverts when used to ASSIGN rather than to REFUTE.**
nyiso-219 built pondage deliberately as an upper bound (full volume, efficiency 1.0) because an upper
bound is *logically sufficient to refute* a monthly period. Using the same number to *assign* a
period is a different use: an overstated pondage assigns too long a period, i.e. the mechanism would
be **too weak, not too strong**. That direction is the safe one, and it should be stated in the
build rather than discovered.

## 6. Why this is one mechanism, not a second one

The existing `hydro_budget_period_by_instrument` field already takes a **per-plant** period map from
a registry; extending coverage is **populating that registry**, not adding a mechanism. That matters
for rule 19: there is no new floor, no new row family, and nothing to stack. The likely change is a
**rename** (the field's name presumes Route A, which is now the minority route — perhaps
`hydro_budget_period_by_storage`) plus a derived registry rather than a hand-listed one, with
Route A **overriding** Route B wherever an instrument has actually been read.

## 7. What a build must satisfy

* **Rule 17 `[R-FLOOR-WINDOW]`** — driver: measured usable storage; window: all hours of every
  period (no diurnal shape pinned); forward story: pondage is a licensed physical parameter that
  regenerates for any forecast year and re-derives only when NID updates (rule 23
  `[R-FROZEN-DERIVE]`).
* **Rule 13 `[R-MEASURED]`** — pondage is a physical input, not an outcome. **Still forbidden:** any
  period set at the actual's own measured within-month daily sd; any shape pinned to `NG: WAT`
  (reaches r = 1.000 by construction — tripwire: a within-month r near ~0.95); any period **swept**
  against the gates.
* **Rule 21 `[R-DOF]`** — the DOF ledger carries the bucketing rule and the R5 default as declared,
  un-swept choices, and says plainly that 78 % of MW rests on a head proxy.
* **Rule 14 `[R-ACCURATE]`, both ways** — hydro is ~20 % of NYISO generation, so this **will** move
  C3a/C3b/C3c. **If the faithful representation makes the price fit worse, it STAYS** and the worse
  fit is a discovered root-cause question. Precedent: the 2026-07-25 probe made C3a-2023 worse
  (+18.3 → +22.2 %) and was still recorded as **mechanism confirmed**.
* **Rule 24 `[R-REGISTRY]`** — one registry, in `constants.py`, with per-entry citations; no
  per-plant dict in a `data/` module.

## 8. How it would be screened (rule 29 `[R-SCREEN]`)

**Phase 0, zero LP, first and blocking:** the derived registry, the bucket census, the **re-run**
rule-19 overlap arithmetic (R3), and a pre-solve footprint prediction per plant from the arm's
existing per-unit hourlies — which already exist, so the prediction is checkable before any solve.
**One screen year**, named in the PRECOMMIT, chosen on the mechanism's own largest footprint, never
on a residual. **Gates STRUCTURAL and STOP-only**, self-contained where possible, and explicitly
**not** the within-month r versus actual. **G-CTRL form 4** — the keeper's committed bundle is the
control via a single-delta `replay_keeper --set` A/B, which is what made the nyiso-220 screen valid
after a first attempt with bare CLI defaults produced nonsense (hydro −13 %, CT_PEAKER +458 %) and
was discarded. **Rule 31 `[R-RETAIN]`** — bundles gitignored, never `rm`, promotion question surfaced
before the session ends.

## 9. The questions for the owner

* **Q1 — extend to the whole fleet on measured pondage?** The object is quantified (§2) and the
  route validates 2-for-2 against the instrument route (§3). Approving this is approving Route B as
  an identification basis in its own right, not merely as Niagara's special case.
* **Q2 — the bucketing rule (R4).** Floor-to-the-coarsest-period-not-exceeding-pondage, or something
  else? It must be fixed **before** any solve and never swept. **This is the main DOF and I have
  deliberately not chosen it.**
* **Q3 — the head proxy (R1).** 78 % of fleet MW rests on a dam-height proxy with two-sided error.
  Options: (a) proceed and declare it, since R6 says the error direction is the safe one;
  (b) fund a head intake first (FERC licence documents carry head per project — but FERC text is
  **not retrievable from this container**, §nyiso-220 finding §1); (c) restrict the mechanism to
  plants with a true `Hydraulic Height` (20.50 % of MW) and leave the rest on the month, which is
  the conservative half-measure.
* **Q4 — the 12 plants with no pondage (R5).** Keep the month, or inherit a default?
* **Q5 — scope.** NYISO-only, or is this chartered as a general per-ISO mechanism from the start?
  Rule 25 means each ISO derives its own either way; the question is whether other lanes are told to
  expect it.

## 10. What this charter deliberately does NOT decide

It does not choose the bucketing rule, the R5 default, or the head-proxy posture; it does not re-run
the rule-19 arithmetic; it does not rename the field; it does not claim the mechanism would improve
any criterion; and it **does not authorize a solve**. The nyiso-220 screen result stands as it is —
five gates cleared on 2 plants, with a price effect of **−0.226 %** on load-weighted LMP, i.e.
**structurally correct and nearly price-neutral**. Nothing in this charter promotes it.

**No new pending owner card beyond §9.** The seven unrelated pending rulings (nyiso-206, -207, -203,
DECISION-CARD-nyiso193 §5/5.1, -208, -214 §6, -215 §6) are untouched.
