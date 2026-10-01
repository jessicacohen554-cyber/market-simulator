# ADDENDUM — nyiso-223: the shard's C1 delta is a CLASS-TAXONOMY ARTIFACT

**Session:** nyiso-223 (parent) · **ISO:** NYISO · **Date:** 2026-09-10 · **ZERO LP.**
Corrects one number in `docs/RESULT-nyiso223-shard-2022.md`, written by shard `nyiso223-y2022`.

## 1. The claim being corrected

The 2022 shard reported, as its headline C1 finding:

> **CC_REGULAR moves the WRONG WAY**: 36.553 (keeper) → **36.931** (arm), i.e. **+0.378 TWh**
> further ABOVE the 31.564 actual. The over-generation gap widens from +4.989 to **+5.367 TWh**.

**That comparison mixes two bases and the +0.378 is not a dispatch move.** The shard flagged the
risk itself ("Class totals differ slightly from the D-2 `class_total_twh` column"), and could not
resolve it because the control bundle was not in its container.

## 2. The two bases

- The arm's **36.931** is the sum of `hourly/class_hourly_2022.parquet` (P1) — the **LP's own
  dispatch classes**.
- The keeper's **36.5531** is `gmModel.CC_REGULAR` from the committed run payload
  `frontend/data/backcast/runs/2026-09-09-nyiso-221-fuelvintage-tp2022.js` — the **scorer's
  reporting classes**, which carve out an `OTHER_FOSSIL` bucket that `class_hourly` does not have.

## 3. The offset, measured on TWO independent committed control bundles

| control run | `gmModel` CC_REGULAR | `class_hourly` CC_REGULAR | **offset** | CT_PEAKER offset | sum | `OTHER_FOSSIL` |
|---|---|---|---|---|---|---|
| `2026-09-07-nyiso-213-tp2022` | 36.5742 | 36.8917 | **+0.3175** | +0.3405 | +0.6580 | 0.7567 |
| `2026-09-06-nyiso-209-2022-touchpoint` | 35.9148 | 36.2440 | **+0.3292** | +0.3542 | +0.6834 | 0.7995 |

Both bundles' **totals are identical across the two bases** (154.183 and 154.169 respectively), so
nothing is created or lost — the `OTHER_FOSSIL` bucket is redistributed onto `CC_REGULAR` and
`CT_PEAKER` when the LP's own classes are summed. The offset reproduces to **0.012 TWh** across two
runs of two different recipes.

## 4. The corrected reading

Applying the measured offset to the arm's `class_hourly` figure:

| quantity | value |
|---|---|
| arm, `class_hourly` basis | 36.931 |
| measured basis offset | −0.317 to −0.329 |
| **arm, inferred `gmModel` basis** | **≈ 36.60 – 36.61** |
| control (`2026-09-09-nyiso-221-fuelvintage-tp2022`), `gmModel` | **36.5531** |
| **inferred move** | **≈ +0.05 TWh**, not +0.378 |

Corroborating: the arm's own totals match the control's to the digit — **154.191 both** — and every
class the taxonomy does not touch agrees closely (`import` 27.849 vs 27.8487; `COAL_PRB` 0.655 vs
0.6554; `CT_CHP` 2.083 vs 2.0828; `ST_CHP` 1.488 vs 1.4913; `CC_CHP` 13.430 vs 13.4171).

**So the registered PRECOMMIT §6.2 prediction — "|Δ| per class < 0.05 TWh" — is at its edge rather
than violated 8×, and the arm's mean-preservation-in-dispatch claim survives on 2022.**

## 5. What this correction is NOT

It is **inferred**, not scored. The offset is measured on control bundles of a *different recipe*
(nyiso-213 / nyiso-209), and the arm's own bundle was never scored, because:

- `replay_keeper.py` writes no `metrics.json`, and the scorer reads committed registry artifacts a
  screen bundle deliberately never has (rule 29 `[R-SCREEN]` clause 2);
- the shard could not build the `lmp` clean partition (`curate_lmp` `KeyError: 'MGHG'`, a
  pre-existing defect it correctly declined to repair), so no actual-side C3a/C3b existed there;
- the shard's container is ephemeral and there is no message channel from this parent to a running
  CCR shard, so its bundle could not be retrieved before reclamation.

**The honest status of the corrected number is therefore: strongly supported, not certified.**
Certifying it costs one re-solve of 2022 with the artifacts pushed (~12 min of LP), and that is
stated here rather than papered over.

## 6. What does NOT change

The shard's other 2022 findings stand as reported, on bases with no such ambiguity:

- **Dec 22–31 $63.87 → $66.68 (+$2.81)** against a $123.32 gap — the arm closes **~2.3 %** of its
  own target window.
- **Dec 1–21 $71.83 → $69.39 (−$2.44)** — it moves a window the keeper already matched to within
  $0.56 **away** from actual. This is the mean-preserving offset doing exactly what
  mean-preservation implies, and it is the arm's real cost.
- C3c **8–10 h of 101**; model max $2,000 (VOLL slack, 2 h).
- D-4 FAIL on 3 unit-conduct rows totalling 0.0092 TWh — pre-existing, **not arm-attributable**.
