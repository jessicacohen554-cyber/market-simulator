# RESULT (pjm-h8) — the min-load measured-offer arm is KILLED BY G-4 **by 0.711 TWh**, and
# the pre-registered inertness prediction G-5 lands at **8.4 %** against a **< 25 %** bar

**Session** `pjm-h8` · **ISO** PJM · **Date** 2026-09-16 · **Base** `origin/main` @ `bc7bbe45`
**Screen** PJM 2023, ONE arm shard at one pinned sha (`bc7bbe45`). Parent ran no LP (rule 32
`[R-SHARD]` (a)). **No control solve was spent** — G-CTRL form 4, the keeper's own committed
bundle. **PJM keeper `2026-09-11-pjm-d4-4-gasoutage`: CALIBRATED, 8/8, zero caveats — UNTOUCHED.**
Spec and pre-registration: `docs/PRECOMMIT-pjm-h8-minload-measured-offer-2026-09-16.md`.
Charter: `docs/FINDING-pjm-h8-coal-minload-is-the-undisciplined-offer-surface-2026-09-16.md`.

---

## 1. RESULT

> **The arm installs PJM's own published offers exactly, comes closer than either predecessor,
> and still misses — by seven tenths of a TWh on one non-target class.**
>
> | gate | verdict | evidence |
> |---|---|---|
> | G-1 confinement | **PASS** | 136/137/140 rows, exactly {COAL, ST_GAS} × {mustrun, committed}, three years, phase 0 |
> | G-2 identity | **PASS** | max \|P1 bid − measured target\| = **7.1e-15**, machine precision |
> | G-3 sign/magnitude | **PASS** | COAL_BIT **90.321**, inside the pre-registered interval (78.834, 105.152) |
> | **G-4 no non-target flip** | **FAIL** | **CC_REGULAR 334.381 = +8.711 TWh**, bar was ≤ 333.670 — **missed by 0.711** |
> | **G-5 inertness** | **PASS** | **mustrun = 8.4 %** of the coal energy change, bar was < 25 % |
>
> **C1 goes 16/16 → 14/16** — the same two classes as pjm-h6 and pjm-h7, at **roughly half**
> their magnitude. The remaining five years were **never spent** (rule 29 `[R-SCREEN]` clause 2).

## 2. G-5 — THE PRE-REGISTERED PREDICTION, AND IT IS THE SESSION'S REAL RESULT

The PRECOMMIT registered, before the solve, that the `mustrun` band carries **77 %** of the
arm's coal $-MW footprint but — being 84.4 % floored by `min_gen` — would produce **less than
25 %** of its coal energy change. Measured against the keeper's own committed band sidecar:

| band | control TWh | arm TWh | Δ | **share of \|Δcoal\|** | share of the arm's $-MW footprint |
|---|---:|---:|---:|---:|---:|
| **mustrun** | 42.113 | 40.700 | **−1.413** | **8.4 %** | **77 %** |
| **committed** | 51.127 | 36.453 | **−14.674** | **87.7 %** | **23 %** |
| econ (all) | 15.523 | 16.162 | +0.639 | 3.8 % | — |
| sync | 4.304 | 4.311 | +0.007 | 0.0 % | — (out of scope) |
| peak | 0.404 | 0.409 | +0.005 | 0.0 % | — |
| **total** | **113.471** | **98.035** | **−15.436** | | |

**8.4 % against a < 25 % bar — the prediction holds with room to spare, and its converse is
sharper still**: the `committed` band carries under a quarter of the price footprint and
produces **seven eighths** of the dispatch response. The `mustrun` band's energy falls
**1.413 TWh of a possible ~6.58** (its unfloored headroom), i.e. repricing 14 GW by +$20/MWh
moved 3.4 % of that band.

**This is the first measurement in this program of whether repricing floored energy is
dispatch-inert, and it settles it: it is, to 92 %.** It also retro-validates §2a of this
lane's own FINDING — the correction that demoted `mustrun` from "the object" to "mostly inert"
was made *before* this solve and is now confirmed by it.

## 3. THE C1 TABLE — PJM 2023, band ±8.00 TWh

Actuals are the committed HEAD bench (`frontend/data/backcast/bench/PJM/2023.json.gz`
`classFull`). The CONTROL is the keeper's own committed bundle (G-CTRL form 4).

| class | actual | CONTROL | res | | **ARM h8** | **res** | |
|---|---:|---:|---:|:--|---:|---:|:--|
| **CC_REGULAR** | 325.670 | 328.529 | +2.86 | PASS | **334.381** | **+8.71** | **FAIL ← G-4** |
| nuclear | 272.591 | 272.022 | −0.57 | PASS | 272.022 | −0.57 | PASS |
| **COAL_BIT** | 103.026 | 105.125 | +2.10 | PASS | **90.321** | **−12.70** | **FAIL** (target) |
| wind | 29.626 | 29.628 | +0.00 | PASS | 29.628 | +0.00 | PASS |
| CT_PEAKER | 21.663 | 20.533 | −1.13 | PASS | 22.570 | +0.91 | PASS |
| solar | 8.977 | 8.976 | −0.00 | PASS | 8.976 | −0.00 | PASS |
| hydro | 8.976 | 8.903 | −0.07 | PASS | 8.903 | −0.07 | PASS |
| ST_GAS | 8.883 | 11.326 | +2.44 | PASS | 15.079 | +6.20 | PASS |
| CC_CHP | 6.115 | 8.541 | +2.43 | PASS | 8.649 | +2.53 | PASS |
| COAL_WC | 5.895 | 5.295 | −0.60 | PASS | 4.891 | −1.00 | PASS |
| biomass | 5.298 | 5.298 | +0.00 | PASS | 5.298 | +0.00 | PASS |
| OTHER | 4.700 | 7.225 | +2.52 | PASS | 7.225 | +2.52 | PASS |
| COAL_PRB | 3.550 | 3.052 | −0.50 | PASS | 2.823 | −0.73 | PASS |
| ST_CHP | 2.198 | 0.997 | −1.20 | PASS | 1.013 | −1.19 | PASS |
| CT_CHP | 1.875 | 1.906 | +0.03 | PASS | 1.956 | +0.08 | PASS |
| oil | 0.637 | 0.001 | −0.64 | PASS | 0.001 | −0.64 | PASS |
| | | | **16/16** | | | **14/16** | |

**Against its two predecessors, on the two classes that decide it:**

| | COAL_BIT res | CC_REGULAR res | price (simple) |
|---|---:|---:|---:|
| control / keeper | +2.10 | +2.86 | 28.802 |
| pjm-h6 (committed → 0.916) | −24.19 | +13.48 | 30.501 |
| pjm-h7 (h6 + `gas_mid` 4.58) | −20.03 | +11.71 | 30.213 |
| **pjm-h8 (measured offers)** | **−12.70** | **+8.71** | **29.430** |

**Every column improves monotonically**, and h8 is the only one of the three where the
non-target class lands within a TWh of its bar. **Price** (bench RT actual 28.44 / RT
load-weighted 29.58): control 28.802 / 29.432 (+0.36) · **arm 29.430 / 30.001 (+0.99)** —
half h6's +2.06 error. **Slack and dump are exactly 0.0**, so no scarcity artifact is in this
result.

## 4. THE PRE-REGISTERED LINEAR EXPECTATION WAS RIGHT, AND THAT IS WORTH RECORDING

PRECOMMIT §5 predicted, from the arm's effective (unfloored) footprint being ~58 % of h6's,
COAL_BIT ≈ **89.9** and CC_REGULAR ≈ **334.7**, and stated plainly that this implied a G-4
FAIL. Measured: **90.321** and **334.381** — errors of **0.4** and **0.3 TWh**.

This is the opposite of pjm-h7, whose linear pre-registration (≈86.3) missed by 3.3 TWh *in
the argued-against direction*. The difference is not luck: h7 extrapolated from an arm that
overshot its own measured correction by 2.3×, where local linearity is a poor guide; h8
extrapolated a correctly-sized move. **The prediction was pre-registered and it is reported as
made, not re-read after the fact** — and, per rule 1 `[R-STRUCT]`, it gated nothing.

## 5. WHAT THIS ACTUALLY SHOWS — the successor question, sharply posed

**Priced at PJM's own published offers, the model's coal falls 12.70 TWh BELOW what PJM's coal
actually generated.** The control sits at +2.10; the measured-offer basis takes it to −12.70.
That is the PRECOMMIT §5 second branch, and it is now the measured outcome:

> **the model has nothing that keeps PJM coal running at the offers PJM's own units submit.**

Rule 19's D-2 attribution already closed the obvious escape: **96 % of PJM coal is economic
dispatch** (`coal_mustrun` 3.79 %, `reliability_floor` 0.18 %, `chp_steam` 0.03 %), so the
missing 12.7 TWh **cannot be a floor that is absent**. Two candidate readings remain, and this
lane does not adjudicate between them:

* **(a) A real commitment/obligation the model lacks.** PJM coal is long-min-run
  (the measured segment's own definition is min_runtime > 16 h) and cannot chase the margin
  hour to hour; PJM has **no** P1-native commitment bridge, where CAISO, ERCOT and NYISO each
  have one. That is a structural absence, not a tuning gap.
* **(b) The measured comparator is not exact at these shares.** The `LONG_RUN` segment is coal
  **plus** gas-steam, and ST_GAS bids dearer — the FINDING's §4(a) control shows the band-to-band
  *pattern* survives that admixture, but its *level* carries it. A coal-only re-derive of
  `derive_pjm_offer_midcurve.py` would settle this, at a data cost (~1-2 GB re-fetch) and zero LP.

**(b) is the cheaper test and it should be run first.** If the coal-only ladder sits materially
below the blended one, the arm's +6.72 $/MWh on `committed` is an over-correction and the
remaining question is how much; if it does not, (a) is the object and the lane moves off the
offer stack entirely and onto PJM commitment.

## 6. WHAT THIS DOES **NOT** ADJUDICATE

* **It does not vindicate the registered 0.548.** A screen that kills an arm never certifies
  the incumbent (the pjm-h7 §4 principle, restated). The measured-offer gap at that band is
  real, measured, and still open.
* **It does not license reverting anything** (rule 14 `[R-ACCURATE]`).
* **It says nothing about `gas_mid`.** The arm is sigmoid-invariant by construction. The
  standalone `gas_mid` → 4.58 accuracy repair remains unchartered (pjm-h7 §4/§5).
* **It does not adjudicate CC_LIKE min-load**, deliberately out of scope (PRECOMMIT §6:
  CC_REGULAR `committed` is 28.8 GW at 1.19-1.24× measured, so a LEVEL form there would cut the
  largest class in the system by ~20 % in one step). Its own charter, if anyone wants it.
* **`sync` stays out of scope** and moved 0.007 TWh, confirming the structural exclusion was
  inert rather than load-bearing.

## 7. THE PROMOTION JUDGMENT (rule 31 `[R-RETAIN]`) — asked, not pre-empted

**RECOMMENDATION: DO NOT PROMOTE — but this is the closest call of the three, and it is the
owner's.**

Stated against the owner's 2026-09-14 standard (*"if structural integrity improves but gates
regress that **may** still be a keeper"*) rather than around it. What is genuinely better here
than in h6/h7: the structural case is the strongest of the three — it installs PJM's **own
published offers** (G-2 at 7e-15) on the one rung of PJM's coal stack that no measured artifact
governed, with **zero free parameters**; and every scored magnitude improves. What still stands
against it: the incumbent keeper is **16/16 with zero caveats**, this run is **14/16**, its
target class moves *further* from actual (+2.10 → −12.70) rather than closer, and the class it
breaks is the largest in the system. Shipping it would trade a clean determination for a
structural argument whose own §5 says the root cause is **not yet identified**.

## 8. RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e))

On `origin`, complete with the per-plant layer a registration needs (15 files incl.
`dispatch/2023_P1.parquet`, `btm.parquet`, `system.parquet`, all five `hourly/` sidecars —
including `class_band_hourly_2023.parquet`, which is what made §2 measurable):

```
branch  claude/pjm-h8-screen-2023
SHA     b2b3d7d572ce56cd0fc25c4e08c8b46fce740be7
recover git checkout b2b3d7d572ce56cd0fc25c4e08c8b46fce740be7 -- \
          results/calibration/pjm_h8_screen2023_arm
```

Verified this session by `git ls-tree` (15 files) **and** by checkout + config-signature read:
`pjm_offer_midcurve_minload_segments: ["LONG_RUN"]`, `pjm_offer_midcurve_segments:
["LONG_RUN","CC_LIKE"]`, `meta.git_sha bc7bbe45`. A promotion from this state costs **zero
re-solves for 2023** and five further years (~90-105 min) for the rest of PJM's registered span
(2020-2025, rule 35 `[R-PROMOTE]` (c)).

**RULE 33 `[R-SHARD-ARCHIVE]` (f)(4) — A PRIOR RECOVERY COMMAND IS NOW DEAD, recorded rather
than left to fail silently.** `docs/RESULT-pjm-h6-route-a-replace-screen-2026-09-14.md` §7 and
`docs/RESULT-pjm-h7-gasmid-joint-screen-2026-09-14.md` §7 both pin recovery to shas on branches
that **no longer resolve** (`dadda814…` unreachable: *"could not get object info"*;
`claude/pjm-h6-screen-2023` gone from `origin`). Those bundles are **not recoverable by
checkout** — reproducing either now costs a re-solve. This lane did not delete them; the
branches were disposed of by the environment. It is why this document's own recovery line is a
**full immutable SHA** and why the same SHA is written into `.gitignore` beside the bundle.

## 9. WHAT WAS SPENT, AND WHAT WAS NOT

* **ONE LP** — PJM 2023, one arm leg, ~13 min. **No control solve**: G-CTRL form 4 against the
  keeper's own committed bundle, whose 2023 COAL_BIT (105.125) and C1 (16/16) are the keeper's
  published headline exactly.
* **The six-year span was NOT spent** (~90-105 min saved) — the pre-registered STOP gate fired.
* **The shard stalled once** at ~13.5 min, idle in `review_ready`, having announced its commit
  step without executing it; it was resumed by a one-shot Routine bound to its session and
  completed the push. Recorded because it is a reproducible shard-orchestration failure mode,
  not a model result.
* **Nothing registered, no keeper touched, nothing deleted.** The screen bundle is a throwaway
  probe (rule 29 clause 2), gitignored with its recovery SHA (rule 31), and every number this
  lane cites is in this document.

## 10. MATRIX (rule 28 `[R-MECH-MATRIX]` (b))

`pjm_midcurve_belt` PJM cell stays **K** (the mechanism is armed on the keeper and unchanged),
with its new sub-gate `pjm_offer_midcurve_minload_segments` adjudicated **R** at the 2023
screen, this document the citation.

## 11. RULES

Rule 1 `[R-STRUCT]` (every gate structural and STOP-only, fixed before the solve, never read on
the target residual — and G-4 killed the arm on a non-target class) · rule 13 `[R-MEASURED]`
(the operand is PJM's own published offers) · rule 14 `[R-ACCURATE]` (§5-§6 — the worse fit is
treated as a discovered root cause, and nothing is reverted) · rule 19 `[R-ONE-MECH]` (LEVEL
form replaced the take-or-pay construction rather than stacking; the D-2 enumeration closed the
floor escape) · rule 21 `[R-DOF]` (zero free parameters; nothing swept) · rule 29 `[R-SCREEN]`
(clause 0 phase 0; screen year on footprint; clause (b) form 4, no control solve; the remaining
years were never spent; clause (c) the bundle is gitignored, never merged) · rule 30(c) (no
held-out year touches PJM's determination) · rule 31 `[R-RETAIN]` (nothing deleted; the
promotion question is put to the owner) · rule 32 `[R-SHARD]` (a) (the parent ran no LP) ·
rule 33 `[R-SHARD-ARCHIVE]` (fetched, checked out, verified, then archived; recovery by full
SHA; §8 records two now-dead prior recovery commands) · rule 34 `[R-SHARD-PROMOTABLE]` (the
shard pushed its bundle with the per-plant layer; retrievability stated in §8).
