# PREREG — nyiso-171 phase 0: identifying NYISO's CC_CHP steam-host floor

**Session:** nyiso-171 · **Date:** 2026-09-01 · **Keeper:**
`2026-08-30-nyiso-159-loss-surface` (determination **NOT-YET** on
{C3a-2025 −11.5 %, C3c}) · **Solves planned in phase 0: ZERO.**

Registered **before** `scripts/probes/nyiso171_chp_floor_identification.py` was
run, in the same commit as the probe.

## 1. The object

nyiso-169b handed forward, and nyiso-170 did not touch, a CC_CHP low-end
dynamics object that is wrong in **both** directions:

| statistic | 2023 | 2024 | 2025 |
|---|---|---|---|
| model CC_CHP p05 (MW) | 869 | 892 | 817 |
| measured CC_CHP p05 (MW) | 531 | 732 | 648 |
| error | +63.6 % | +21.8 % | +26.1 % |
| p25 error | +26 % | +38 % | +47 % |

— yet at p01 the model drops to **near zero in 96 hours of 2025**, where the
measured fleet never falls below ~280 MW and is never off.

The brief's structural reading: the model treats CC_CHP as freely dispatchable
where reality is a steam-host-following resource with a hard floor and no off
state. A combined-cycle cogenerator follows its industrial steam host, so a
floor is a physical/contractual driver with a forward analogue — admissible
under rule 13 `[R-MEASURED]` and satisfiable under rule 17 `[R-FLOOR-WINDOW]`.

## 2. Pre-registered gates

| gate | question | PASS condition |
|---|---|---|
| **A1** | rule 19 `[R-ONE-MECH]`: what already floors CC_CHP? | the D-2 attribution names exactly one mechanism, so a correction **replaces** its level source rather than stacking |
| **A2** | what floor does the model actually build, per plant? | reported, not gated — the structural fact the arm would change |
| **A3** | **THE STOP CONDITION.** Is the measured floor a per-plant property or a portfolio artifact? | `sum_p p01(gen_p) / p01(sum_p gen_p) >= 0.50` in **all three years** |
| **A4** | meter-coverage validity (the nyiso-170 §3 lesson) | plants with a silent CAMPD meter are identified and **excluded** from A3's discriminator, not convicted by it |
| **A5** | can a floor even bind, or is the collapse an outage? | the collapse hours are **scattered** (< 50 % of low-hours in runs ≥ 24 h), i.e. economic rather than outage-driven |
| **A6** | sizing and honest direction | reported, not gated |

## 3. The stop condition, stated so it can fail

A fleet series can look "never off" for two different reasons, and only one of
them is a mechanism:

* **Per-plant physics** — each cogen individually never drops below its own
  steam-host level. The floor is a property of a machine, representable as
  `min_gen`, and regenerates for a forecast year from the host's steam demand.
* **Portfolio artifact** — every plant cycles to zero on its own, but they are
  never all off at once, so only the **sum** has a floor. There is then no
  per-plant physics to represent, and a per-plant `min_gen` would force a
  machine to run in hours its own meter says it was off — a rule 17
  `[R-FLOOR-WINDOW]` violation *by construction*.

The discriminator is exact: `sum_p min_t(gen_p,t)` against `min_t(sum_p gen_p,t)`.

**If A3 returns PORTFOLIO ARTIFACT, the lane stops and says so.** The brief
names this outcome as legitimate (nyiso-152/168/169/170 precedent) and it will
not be argued around.

## 4. What is NOT pre-registered as a success

Two directions are fixed in advance so the result cannot be re-read favourably
after the fact:

1. **A floor can only raise output.** CC_CHP already over-runs its benchmark by
   **+2.77 TWh** in 2025 and its p05/p25 are **+26 %/+47 %** high. A floor
   repairs the p01 under-run and moves the over-run and the volume error
   **further in the wrong direction**. A6 reports both magnitudes. If the arm
   proceeds, this trade is stated in the finding, not buried.
2. **C3a-2025 is not expected to move.** The association nyiso-170 measured
   between gas-composition error and price deficit is explicitly *not* a
   demonstrated mechanism. Under rule 1 `[R-STRUCT]` a structurally-correct
   floor **stays in** whether or not the residual moves, and a residual that
   does not move is **not** evidence against it.

## 5. Phase 2 trigger

Phase 2 (building and solving an arm) is entered **only** if A1 PASSES, A3
returns PER-PLANT PHYSICS in all three years, and A5 shows the collapse is
economic rather than outage-driven. If A6 then sizes the forced energy at a
level too small to change any gate, the honest outcome is an **ex-ante
inertness adjudication with no solve**, which the brief names as a legitimate
and valued result.

## 6. Compliance

* Rule 13 `[R-MEASURED]` — CAMPD enters only as conduct identification. Nothing
  is pinned to observed generation; no statistic is tuned to a residual.
* Rule 19 `[R-ONE-MECH]` — A1 is the enumeration, run first and by construction.
* Rule 22 `[R-HOLDOUT]` — 2023/2024/2025 only. NYISO holds no `complete`
  marker and is absent from `final`; no out-of-training year is read, solved,
  scored or registered, and no marker is requested.
* Rule 23 `[R-FROZEN-DERIVE]` — any re-derivation of a measured artifact must
  cite a source-data or construction change, never a residual.
