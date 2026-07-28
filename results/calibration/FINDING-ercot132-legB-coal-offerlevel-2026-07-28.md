# FINDING — ERCOT-132 leg B: the coal offer-LEVEL arm is REJECTED on its pre-registered gate — but two of my three predictions were wrong, and the way they were wrong is the result

**Date** 2026-07-28 · **ISO** ERCOT · **Lane** ercot132 leg B ·
**Run** `2026-07-28-ercot122-offerlevel` (bundle
`results/calibration/ercot122_offerlevel`) — **REGISTERED PROBE, REJECTED, NOT A
KEEPER CANDIDATE** ·
**Keeper** `2026-07-28-ercot129-conditional-coal-min` — **UNCHANGED**;
`frontend/data/backcast/keepers/ERCOT.json` not touched ·
**Pre-commit** `docs/PRECOMMIT-ercot132-legB-coal-offerlevel-2026-07-28.md`,
written and pushed (PR #3076, commit `2ce790b`) **before the solve started** ·
**Authority** owner overrule of `DIAGNOSIS-ercot122` §5.1's recommend-and-STOP,
on the ERCOT-118 / ERCOT-119 controlled-refutation precedent.

---

## 1. Verdict

**REJECTED.** The pre-commit §2.3 made adoption conditional on **all three** of:

| # | criterion | result | |
|---|---|---|---|
| (a) | C1 coal mean-abs error improves on 0.778 TWh | **0.679 TWh — IMPROVES** | ✅ met |
| (b) | G1 loading-vs-price does not regress below 19/21 | **18/21 — REGRESSES** | ❌ **not met** |
| (c) | no new C-gate FAIL | rubric **identical** to keeper | ✅ met |

(b) fails, so the arm is rejected. It is registered as a controlled refutation
and there is no promotion path from this lane.

## 2. What I predicted, and what actually happened

**Two of the three substantive predictions were wrong. Stating that first.**

| pre-registered | predicted | actual | |
|---|---|---|---|
| **P2** direction | coal **falls in every year** | falls **only** in 2023; **rises** in 2024 and 2025 | ✗ **wrong** |
| **P3** C1 level | mean-abs error does **not** improve; 2025 degrades | **improves** 0.778 → 0.679; **2025 improves** | ✗ **wrong** |
| **P4** G1 | **regresses** | regresses 19/21 → 18/21 | ✓ correct |
| **P5** verdict | **REJECTED** | rejected | ✓ correct |
| **P1** arming/bite | four bands resolve to the measured level | confirmed in `run_config.json` | ✓ correct |

### 2.1 Coal energy (P1 `class_hourly` sidecars vs the committed bench)

| year | keeper | arm | Δ | actual | keeper err | arm err |
|---|---|---|---|---|---|---|
| 2023 | 60.791 | 60.607 | **−0.184** | 60.420 | +0.371 | **+0.187** |
| 2024 | 58.414 | 58.448 | **+0.034** | 57.617 | +0.797 | +0.831 |
| 2025 | 61.047 | 61.197 | **+0.150** | 62.214 | −1.167 | **−1.017** |
| | | | | **mean abs** | **0.778** | **0.679** |

### 2.2 G1 — the gate that rejects it (fleet-aggregate loading vs RT price)

| year | band | hours | actual | keeper | arm | keeper Δ | arm Δ |
|---|---|---|---|---|---|---|---|
| 2023 | `<$15` | 2,665 | 0.552 | 0.507 | 0.499 | −0.046 ok | **−0.053 FAIL** |
| 2024 | `≥$50` | 760 | 0.720 | 0.772 | 0.775 | +0.052 FAIL | +0.055 FAIL |
| 2025 | `<$15` | 2,634 | 0.689 | 0.636 | 0.633 | −0.053 FAIL | −0.056 FAIL |
| | | | | | | **19/21** | **18/21** |

(the other 18 bands are within 0.05 for both). The arm **deepens every one of
the three worst bands** and flips 2023 `<$15` over the line. This is precisely
the bottom-band defect `DIAGNOSIS-ercot127` §1 identified as where the coal band
actually fails — and the lever makes it worse while the top, already matched,
drifts a further +0.002 to +0.005 dearer.

## 3. Why the level lever moved so little — the actual result

**A 6.4 GW offer-level change moved coal by at most 0.19 TWh on a ~60 TWh
class (≤0.3 %).** The lever is very nearly inert on coal energy.

That is the finding, and it **independently corroborates `DIAGNOSIS-ercot122`
§4 from the dispatch side**: coal exposes only 0.168/0.184/0.161 of online
headroom to DAM merit against CC's 0.622/0.594/0.677, and the model offers
~100 %. If the model's coal were price-responsive in these bands, a
$0.94–9.91/MWh band move would have shown up as TWh. It did not, because coal
sits at its ceiling 91–93 % of hours (`DIAGNOSIS-ercot127` §1's SUSTAIN pin).
**Moving the price of a block that is already all-in changes almost nothing.**
The defect is **REACH, not LEVEL** — measured now from two independent
directions.

**Why the direction came out mixed** (the P2 miss). My ex-ante capture was
right that the arm makes 6,432 MW dearer against 698 MW cheaper, but I read
that as a net energy fall. It is not, because the two moves land in different
hours: the `+0.94` on the 5,886 MW PRB econ ramp bites in mid-merit hours,
while the `−9.91` on the 570 MW PRB peak band bites in the tight hours where
coal is marginal and the price is high. In 2024 and 2025 the peak-band markdown
dominates and coal rises. A capacity-weighted band table cannot see that; only
the solve can. **That is a genuine limit of the ex-ante method, not a
bookkeeping slip, and it is the one thing this solve bought that the arithmetic
could not.**

## 4. The C1 improvement does NOT license the mechanism (rule 1 `[R-STRUCT]`)

C1 coal mean-abs error improves 0.778 → 0.679 TWh. **This is not a reason to
adopt it**, and per rule 1 it is not evidence for the mechanism:

1. **It fails its own pre-registered gate** (b). The gate was fixed before the
   number existed, precisely so a fit gain could not be retro-fitted into a
   justification.
2. **The transplant is basis-mismatched**, which the pre-commit established
   ex ante (§2.1). The artifact's multipliers are formed on a *pooled* divisor
   (base HR 10.341 × a flat delivered-coal price); the model prices each plant
   on its *own* heat rate through the gas-keyed passthrough sigmoids. So the
   measured $20.48/MWh lignite `econ_low` lands in the model at **$23.38**, not
   $20.5. The arm therefore does **not** put the model on the measured $/MWh
   level — it puts a pooled multiplier into a per-plant band. A fit gain from a
   quantity that is not the thing it claims to be is a coincidence, not a
   mechanism.
3. **The gain is inside the noise of the phenomenon**: 1.29 % → 1.12 % mean
   error on a 60 TWh class, from a lever measured inert on the defect.

## 5. Constraints honoured

* **§5.2** — the pooled `econ_high` 2.856 was **not** re-armed on any basis; the
  pooled artifacts stay frozen as the old-basis record.
* **§5.3** — the measured `econ_low`/`peak_typical` pair used as published,
  **not refitted**. Written as `measured − keeper delta` so the RESOLVED band
  lands on the measured value exactly (pre-commit §1.1); verified in
  `run_config.json`.
* **Single delta** — the keeper's `CC_REGULAR`/`CC_CHP` offer overrides carried
  through **verbatim** and verified byte-identical in the resolved config.
  Without that, `--offer-curve-json`'s wholesale replacement would have
  silently re-priced the gas fleet.
* **§4 / §5.4** — **no reach mechanism was built.** It stays routed to the SCED
  TPO instrument (`FINDING-ercot117` §E); pricing the unoffered ~83 % without
  that evidence would be a fitted wall (rule 13) and a second mechanism on one
  phenomenon (rule 19).
* **Rule 22** — span exactly {2023, 2024, 2025}; no holdout year touched.
* **Rule 16** — full span, one bundle, one invocation, years sequential.
* **Rule 15** — registered in-session with a hand-written sidecar `definition`
  (the auto-copied `model_changes_note` is wrong-run boilerplate on this bundle
  lineage). Retention pruned `2026-07-24-ercot108-envelope-in-lp` (16th ERCOT
  run).
* **Rule 26** — matrix cell updated in this session, rejection included.
* **No keeper file touched.** Not a keeper candidate; no promotion path.

## 6. Environment parity

Matched the ercot115–130 baselines: fresh container, no gtc-limits clean
partition → "static TTC kept" fallback 3/3 years; `hydro-plant-modes` WARNING
expected; the `ercot_wtx_curtailment_driver` kwarg-vs-`prb_overrides` stomp
WARNING appeared and is the expected benign replay-path notice. `coal_min_config`
floor armed 10 plants / 2,164 MW in all three years (keeper mechanism intact).
`ERCOT coal econ marginal-HR floor: no band below its measured basis — offer
curve unchanged` in all three years, confirming ex ante that the arm's
`econ_low` sits **above** the 0.886 measured marginal-HR clamp so the clamp
never bound.

## 7. Successor

Unchanged from `DIAGNOSIS-ercot122` §5.4, now with dispatch-side corroboration:
**the coal lane's live question is REACH.** Measure what the unoffered ~83 % of
online coal headroom is doing in real time — withheld, self-scheduled, or
telemetered down — via the SCED TPO instrument, and only then design a
mechanism. This session adds one constraint on that successor: **an offer-level
instrument cannot deliver it.** The level has now been moved onto the measured
fleet-representative value and the dispatch barely responded.
