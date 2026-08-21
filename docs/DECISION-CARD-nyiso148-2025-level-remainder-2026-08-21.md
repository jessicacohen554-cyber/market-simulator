# DECISION CARD — NYISO's 2025 dear-gas level: the $6.57 that is not a CHP object

**Filed:** 2026-08-21, session nyiso-148. **Decision owner:** the model owner.
**Nothing is armed, changed or promoted by this card.** The NYISO keeper remains
`2026-08-19-nyiso-146c-state-scoped` (CALIBRATED).

---

## 1. WHAT THE OWNER IS BEING ASKED

Two questions, in order. The second only arises if the answer to the first is
"pursue it".

**Q1 — Scope.** Is the NYISO 2025 level a **separate chartered object** for a
NYISO lane, or is it left standing as a known, quantified defect while the lane
works other items? *(Recommendation: charter it. §4.)*

**Q2 — Reporting.** The keeper's C3a-2025 reads **−2.2 %**, comfortably inside
the ±10 % band. nyiso-147 and nyiso-148 together prove that number is held up by
**capacity the model does not carry**, not by price formation that is right.
Should the keeper's determination note and the Calibration Status page carry an
explicit annotation to that effect? *(Recommendation: yes — annotate, do not
re-grade. §5.)*

---

## 2. THE MEASUREMENT — what is now known, and how firmly

Three registered runs, one recipe, one delta at a time:

| run | what it is | 2025 system lw | C3a-2025 |
|---|---|---|---|
| `2026-08-19-nyiso-146c-state-scoped` (KEEPER) | the designated keeper | 64.96 | **−2.2 % (PASS)** |
| `2026-08-20-nyiso-147a-chp-btm` | keeper + the MEASURED CHP grid capacities | 58.36 | **−12.2 % (FAIL)** |
| `2026-08-21-nyiso-148-chp-layup` | that, + the measured CHP lay-up duty split | 59.86 | **−9.9 % (PASS)** |

Actual 2025 RT load-weighted: **66.43 $/MWh**.

* **The keeper's 2025 pass is cancellation.** Restoring ~1.3 GW of measured,
  meter-verified CHP grid capability drops every zone ~$6 and the year to
  −12.2 %. The capacity carve it removes (`CHP_BTM_PCT_BY_SECTOR["merchant"] =
  35 %`) is refuted by the plants' own market meters — NYISO Gold Book net energy
  is 100.3 % of EIA-923 net for Sithe Independence three years running
  (`FINDING-nyiso147-upstate-price-root-cause-2026-08-20.md` §3).
* **The CHP conduct repair recovers $1.50 of the $8.07 gap — 18.6 %.**
* **The remaining $6.57 is not a CHP object, and this is now proven rather than
  inferred.** The lay-up arm removes 1.68 TWh of CC_CHP energy in 2025 and the
  gas family total moves by **−0.02 TWh**: the load is simply re-served by
  CC_REGULAR (+0.76), ST_GAS (+0.61), CT_PEAKER (+0.16) and imports at almost the
  same offer. No CHP membership or capacity work can reach the remainder,
  because the marginal offer barely changes when the marginal unit is swapped
  (`RESULT-nyiso148-chp-layup-duty-2026-08-21.md` §3).

## 3. WHAT THE REMAINDER LOOKS LIKE

It is an **offer-level** object, and it is not confined to 2025 — 2025 is where
it is largest and where nothing cancels it:

* **The dear-gas year is the one that misses.** 2023 (+3.4 %) and 2024 (−3.9 %)
  sit comfortably in band on the same recipe; only 2025, whose gas is $3.52
  against $2.54/$2.19, under-prices by ~10 %. That points at how the offer stack
  responds to a fuel-price *level*, not at any year-specific input.
* **The zonal gradient is missing.** The model carries < $1.5 of spread across
  all five zones in 2024/2025 against actual gradients of $9–15
  (`ASSESSMENT-nyiso148-frontier-2026-08-21.md` §2.3). Upstate runs
  +11.4/+10.8 % and downstate −4.4/−11.4 %; the system mean nets out. Any
  candidate for the 2025 level should be judged on the gradient as well as the
  mean, or it will simply relocate the error.
* **C3c is a symptom of the same thing.** The arm produces **0** hours above
  $300 in 2025 against 42 actual. A price stack that cannot make the tail is the
  same stack that cannot make the dear-year level.

## 4. Q1 — OPTIONS

| # | option | what it costs | what it buys |
|---|---|---|---|
| **A** | **Charter the 2025 offer-level object** as its own NYISO lane, with the gradient and the tail as co-criteria *(RECOMMENDED)* | one or more lane sessions; identification first, no arm until a measured statistic exists | it is the last thing standing between NYISO and a frontier declaration, and it is now precisely scoped: not capacity, not membership, not the CHP fleet |
| B | Leave it standing; work the remaining queue items (Flynn start counts, the `ramp_capability` seams, the D-4 vintage guard) | nothing now | defers the frontier question; the queue items are real but none of them is load-bearing for the determination |
| C | Fold it into the existing `gas_offer_margin_zonal_anchor` lineage as a re-identification | small, but **rule 23 risk**: that anchor is a frozen measured parameter and re-deriving it against a 2025 residual is exactly what rule 23 forbids | fast, and probably wrong for that reason |

**Why A.** The object is now bounded from both sides: the CHP repair recovers
18.6 % and is done; the rest is a single, named, price-formation question. That
is the cheapest state this object will ever be in to charter.

## 5. Q2 — OPTIONS

| # | option | effect |
|---|---|---|
| **A** | **Annotate** the keeper's determination note and the Calibration Status entry: C3a-2025 passes as scored, and its margin is known to be held by a measured capacity defect *(RECOMMENDED)* | no re-grade, no criterion moves, no determination changes; a reader can no longer take the −2.2 % as evidence the 2025 level is right |
| B | Say nothing until the repair lands | the number stays quotable as validated, which the evidence no longer supports |
| C | Re-grade C3a-2025 as a caveat | **NOT recommended and arguably not available**: the criterion is scored on the load-weighted system mean and the keeper's value is correct as scored; rubric v3.1 makes C3c the only ledgerable criterion, so there is no route to ledger a C3a |

**Why A.** It is the honest reading of rule 1 `[R-STRUCT]` — the scored number is
what it is, and what it *means* is a separate statement the record should carry.
`ASSESSMENT-nyiso148-frontier-2026-08-21.md` §2.3 already records it; this option
is only about whether it also appears on the keeper's own line.

## 6. WHAT THIS CARD DOES NOT ASK FOR

* **No holdout spend.** The freeze is ACTIVE and this card requests no lift.
  Everything above is 2023–2025.
* **No promotion.** The nyiso-148 arm is REJECTED-AS-ARMED on its own gates and
  is not offered as a keeper candidate — its C1-2024 `CC_REGULAR` share crosses
  the band at +3.04 pp against ±3 pp.
* **No re-arm of `cc_reserve_duty_split`.** Its standing prereg
  (`PREREG-nyiso146b §ARM C`) is untouched and its bars are not re-litigated.
* **No change to any frozen measured artifact** — the CHP BTM shares and the
  lay-up census are both frozen (rule 23).

## 7. EVIDENCE

* `results/calibration/RESULT-nyiso148-chp-layup-duty-2026-08-21.md` §3 (energy
  conservation), §4 (why the duty band is the wrong shape)
* `results/calibration/_nyiso148_ab_gates.json` (the full gate record)
* `results/calibration/_nyiso148_chp_conduct_phase0.json` (the mechanism-blind
  conduct measurement)
* `results/calibration/RESULT-nyiso147-chp-btm-ab-2026-08-20.md`,
  `FINDING-nyiso147-upstate-price-root-cause-2026-08-20.md`
* `results/calibration/ASSESSMENT-nyiso148-frontier-2026-08-21.md` §2.3, §5
