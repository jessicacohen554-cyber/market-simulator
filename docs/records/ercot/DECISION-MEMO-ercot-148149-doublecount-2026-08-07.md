# DECISION MEMO — the ERCOT-148/149 product ceiling vs the outage double-count (owner briefing, requested 2026-08-07)

**For the owner. Requested via the ercot-175 session's decision card ("Need a
briefing first"). Nothing here is decided; the event-cap ceiling lane stays
FROZEN until you rule. Sources: `FINDING-ercot172/173/174-*.md`,
`results/calibration/ercot174_attribution_check.json`, PRECOMMIT-ercot172 §5.**

## 1. The collision in one paragraph

The model derates plants using two instruments read from the same CEMS
record: a **window layer** (unit-level full-stop outage windows) and a
**partial layer** (plant-aggregate depressed-output plateaus). The armed rule
(ERCOT-148/149, an owner adjudication) multiplies them. ercot-174 proved that
at 94–96 % of the hours where both are active they are measuring **the same
unit's downtime twice** (e.g. Limestone 2024: LIM1's one outage appears in
both layers; the product holds the whole plant at 22 % while LIM2 ran
normally). The product is therefore a double-count almost everywhere it
binds. But every admissible way of removing the double-count — blanket
`min()` (ercot-173, solved, REJECTED), unit-scoped `min()` (ercot-174,
stopped pre-solve because it is 94–96 % the same arm), or finer-grain-wins
(named, not built) — restores **1–2.7 TWh/yr of coal dispatch** above the
ceiling the ERCOT-148/149 ruling deliberately imposed. The two rulings cannot
both stand, and no composition rule reconciles them.

## 2. What the one solved test showed (ercot-173, the only A/B on record)

The fix behaves exactly as predicted where it is right, and damages exactly
where predicted too:

* **Right**: the fabricated 2024 maintenance-season price spikes collapse
  (C3a-2024 +10.5 % → +3.1 %; the 2024-04-28 phantom shed clears; spike-day
  error 382 → 120 $/h; NRMSE-2024 3.00 → 2.26). This is the real defect the
  double-count causes.
* **Wrong**: the restored coal floods 2023/2025 with cheap in-window energy
  (class energy +2–5 %; G-COAL148 fails at 2–5× its 0.5 TWh bar in every
  year; model tail counts move AWAY from actual in all three years).
* ercot-174 then proved no unit-grain refinement escapes this: ρ = 0.94–0.96
  of the rejected arm's lift survives unit scoping, robust across the whole
  attribution-threshold range.

**Key nuance**: even the "correct" fix does NOT close the 2024 object fully —
W A Parish h2827 still shows ceiling 0.36 vs measured CEMS 0.78. The residual
defect is **ercot-172 fault 3**: a multi-week *average* plateau used as an
*hourly* ceiling. A plant averaging 40 % over three weeks routinely ran at
80 % on individual afternoons; the plateau ceiling forbids that.

## 3. The reading the records support

The double-count and the coal flood are **not a paradox — they are one
defect seen from two sides**. The partial layer's plateau is too *low* at the
hours that matter (it is a multi-week mean applied hourly, fault 3) and
redundant with the window layer where units fully stop. Multiplying the two
hides the fault-3 error by over-derating everywhere; removing the product
exposes it as a coal flood. So the choice is not really "cap vs
double-count" — it is whether to keep the compensating error pair, or to fix
the partial layer's construction so the double-count removal stops flooding.

## 4. Options

| option | what it does | evidence status | risk |
|---|---|---|---|
| **A. Keep the product cap; stay frozen** (status quo) | Keeps 2023/2025 well-behaved; keeps the 2024 fabricated spikes and the known double-count | Fully measured | The 2024 C3a/C3b defect stays; the model carries a knowingly-wrong mechanism (rule 1 tension, documented) |
| **B. Adopt a composition fix now** (blanket or unit-scoped `min()`, or finer-grain-wins) | Fixes 2024, floods 2023/2025 coal +1–2.7 TWh/yr | Two arms adjudicated R; finer-grain-wins is strictly MORE restorative, so it moves G-COAL148 further the same way | Repeals ERCOT-148/149 as a side effect; fails the standing gates it would be scored on |
| **C. Re-charter the PARTIAL LAYER'S construction first** (fault 3): replace the multi-week flat plateau with an hourly-faithful ceiling (e.g. plateau-window CEMS-shaped or duration-scoped derate), THEN remove the double-count against the repaired layer | Attacks the root; both prior records predict the flood shrinks because the restored ceiling is no longer a too-low flat mean | NOT yet built — needs its own charter, derive-construction change under rule 23, own precommit + gates | A derive change (heavier session); outcome not guaranteed — but it is the only route both FINDINGs name as remaining |

## 5. Recommendation

**Option C, sequenced after the currently-authorized ercot-151 lane.** A and
B are both adjudicated dead ends on the existing record (A by rule 1, B by
the gates). C is the only unexplored structural route, it is exactly what
ercot-174 §3b item 3 names as "the sole remaining structural route to the
2024 object", and it dissolves the collision instead of picking a loser: with
an hourly-faithful partial ceiling, removing the double-count should no
longer flood 2023/2025, so the ERCOT-148/149 protection and the
double-count removal can finally coexist. Until C is built and gated, the
product cap stays armed (its compensating error is the lesser harm and is
fully documented).

**If you approve this direction**, the ruling to record is: *"The ceiling
lane stays frozen for composition-rule work; a fault-3 partial-layer
construction re-charter is authorized as its successor, with G-COAL148
carried live."* No repeal of ERCOT-148/149 occurs unless/until that arm
passes its gates.
