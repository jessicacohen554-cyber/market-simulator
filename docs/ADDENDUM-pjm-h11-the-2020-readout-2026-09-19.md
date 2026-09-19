# ADDENDUM — pjm-h11: the 2020 readout. C-1 measured, and the ex-ante prediction's MECHANISM lands within 0.16 TWh (2026-09-19)

**Session:** pjm-h11 (orchestrator, **zero LP minutes** — rule 32 `[R-SHARD]` (a); the solves ran in
per-year shards). **Partial result**: 2020 is the only year the arm can move and both its legs have
landed, so it is reported now. The five invariance years (ARM 2021–2025) are still solving and the
verdict is **not final** until they report.

**Bundles** (17 files each, verified by config signature before use):
`pjm_h11_ctl_2020` @ `f3bf920ddfa9d4bd86be1c71b2984647b89d0681` (control sha `0fae26c3`, no 2020
ladder key) · `pjm_h11_arm_2020` @ `bc7617af9b94b8f2997152ab4888c54e88690263` (arm sha `3b719484`,
2020 ladder key present).

---

## 1. The measured delta, ARM − CONTROL, 2020 (TWh)

| class | CONTROL | ARM | Δ |
|---|---|---|---|
| **`import`** (negative = net export) | −40.391 | −28.344 | **+12.047** |
| CC_REGULAR | 287.452 | 283.477 | **−3.975** |
| COAL_BIT | 162.223 | 159.341 | **−2.882** |
| CT_PEAKER | 18.047 | 15.844 | −2.203 |
| VIRTUAL_DEC | −12.584 | −13.655 | −1.071 |
| ST_GAS | 8.283 | 7.277 | −1.007 |
| VIRTUAL_INC | 9.109 | 8.547 | −0.562 |
| CC_CHP / COAL_PRB / COAL_WC / CT_CHP | | | −0.161 / −0.149 / −0.106 / −0.085 |
| **fossil total** | | | **−10.574** |

Nothing else moves by ≥0.05 TWh. Nuclear, wind, hydro, OTHER and biomass are **identical to the
milli-TWh**, which is the signature of a clean single-mechanism delta: the seam repriced, the LP
re-cleared, and only the dispatchable stack followed it.

## 2. Net export, against both benchmarks

| | TWh | residual vs measured 41.626 |
|---|---|---|
| measured (PJM settlement tie file) | 41.626 | — |
| committed keeper `pjm_d4_4_TP` | 38.810 | −2.816 |
| **CONTROL at HEAD** | **40.391** | **−1.235** |
| **ARM at HEAD** | **28.344** | **−13.282** |

**The export residual gets much worse — as predicted, and by more than predicted.** The PRECOMMIT
§3.3 prediction, written before any solve, was that 2020's export residual would *worsen*, on the
grounds that the ladder's gross ceiling at the model's own price (37.340 TWh) sits **below** the
38.810 TWh the unmechanised forecast track delivers. **Direction: CONFIRMED. Magnitude:
UNDER-PREDICTED** — I wrote "toward roughly −4 TWh or worse" and the realized figure is −13.282.
Recorded as a miss on my own forecast, not smoothed over.

## 3. G-DRIFT form 4 is now falsified WITH A NUMBER — and this is why the control was not optional

The CONTROL at HEAD exports **40.391 TWh** where the committed keeper recorded **38.810** — a
**+1.581 TWh HEAD drift on 2020 with no mechanism change at all**. That is the empirical
quantification pjm-h10 owed and could not produce (its shards never survived to a scored number).

Had this lane differenced the arm against the *committed keeper* instead of against a control solved
at the same HEAD, it would have attributed **+1.581 TWh of pure HEAD drift to C-1**. Rule 29
`[R-SCREEN]` (b)'s form-4 test earned its control here in the most concrete way available.

## 4. THE STRIKING ONE: the mechanism reproduces its own ex-ante prediction to 0.16 TWh

PRECOMMIT §3.3 measured, at zero LP from the committed sidecar, that 2020's gap between the ladder
evaluated **at the model's own border-zone price** and the ladder evaluated **at the measured DA
price** is **13.441 TWh** — the largest of any year (next is 2021 at 7.82), and the reason the
PRECOMMIT named 2020's internal price as the defect the ladder would expose.

The realized export shortfall the arm produces is **13.282 TWh**.

**13.441 predicted, 13.282 realized — a difference of 0.16 TWh, about 1 %.** These are different
computations on different objects (an offline rung-clearing integral against a solved LP's
interchange), so exact agreement is not expected and the closeness should not be over-read. But it is
strong evidence that the ladder is doing **exactly** what the offline analysis said it would: it
converts 2020's depressed internal price into a visible volume error rather than absorbing it. That
is the rule 14 `[R-ACCURATE]` story stated in the PRECOMMIT — *the estimate was silently
compensating* — landing as a measurement.

## 5. What this does to C1, the criterion that actually fails

2020's two worst C1 classes both move **toward** measurement (FINDING pjm-h10 §4.2 baselines):

| class | was, vs EIA-923 | arm Δ | after |
|---|---|---|---|
| CC_REGULAR | **+7.5** over | −3.975 | ~**+3.5** over |
| COAL_BIT | **+16.9** over | −2.882 | ~**+14.0** over |

So the arm **improves the failing criterion** while worsening interchange volume.

**And interchange volume is not a scored criterion.** FINDING pjm-h10 §7.1 established that no
rubric criterion tests total system energy or interchange volume — `sysvol` (C2) is gas/coal
families only. Adding one was a **governance proposal** in §7, explicitly *not adopted*, and §7.4
recommended against gating it precisely because it would penalise the ISOs that model the seam as a
market. So on the current rubric the regression this arm causes is **unscored**, and the improvement
it causes is **on the criterion that fails**.

**Stated against interest:** that is a favourable accounting, and I am not going to let it pass
unchallenged. A −13.3 TWh interchange error is a real defect whether or not a gate looks at it, and
"the thing I made worse happens not to be measured" is the kind of argument rule 1 `[R-STRUCT]`
exists to distrust. The honest reading is that C-1 **relocates** 2020's error: out of the
unmechanised forecast track's flattering export number and into a visible, attributable seam
shortfall that points straight at the internal price. That relocation is the point — it is what
makes the next defect findable — but it is a relocation, not a net reduction in error.

## 6. Keeper judgement — NOT YET, and what is still missing

Against the owner's stated criterion (*"if structural integrity improves but gates regress that may
still be a keeper"*), C-1 on 2020 is a **strong candidate**: structure improves (a keeper year now
runs the keeper's own measured seam mechanism instead of the forecast track), the failing criterion
improves, zero parameters were added, and what regresses is unscored.

**Three things must land before I would recommend promoting:**

1. **The five invariance years.** ARM 2021–2025 are predicted byte-identical to their controls (the
   PRECOMMIT verified 0 of 240 shared ladder rungs move). If any of them moves, the arm is not the
   single-year delta it is claimed to be and this readout is not safe to promote.
2. **`metrics.json` is ABSENT from every one of these single-year replay bundles.** So no official
   C1/C2/C3a/C3b/C3c verdict exists for them and every number above is computed by this session from
   the class hourlies. A promotion needs the scored verdict, which is parent-side zero-LP work but
   is **not done yet** and must not be assumed.
3. **Composition.** Rule 35 `[R-PROMOTE]`: PJM registers as TWO runs (keeper 2023–2025 + touchpoint
   2020–2022 folded by `holdout.keeper`), so the per-year bundles must compose into two three-year
   runs and survive `render_calibration_html.build_payload`, which reads the bundle-root
   `system.parquet`. Unverified.

Rule 31 `[R-RETAIN]`: nothing is deleted, and the promotion question goes to the owner with these
numbers rather than being pre-empted either way.
