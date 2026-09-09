# ADDENDUM miso-247 (fourth) — **`G-1` FAILED. `G-2`, `G-3` and `G-4` PASS.** The failing gate was SATISFIABLE, so **no bar is moved and no repair is made**. The full span is spent **on the OWNER's explicit instruction and on rules 1/14 — NOT on the screen's authority**, and that distinction is the point of this document

**Governs:** what happens after the 2024 screen. **No bar in
`PREREG-miso247-the-P19-posture-at-MISO-2026-09-09.md` §5 is moved, re-scoped or relaxed**, and
`G-1`'s failure is not withdrawn anywhere below. Machine records
`results/calibration/_miso247_screen_gates.json` and `_miso247_g4_collateral.json`, pushed **before**
this prose.

---

## 1. **`G-1` FAILED, AT FULL MAGNITUDE**

`P-3′` (repaired predictor, declared in ADDENDUM 2 §4 before it was computed) against the realised
`arm − keeper` energy delta, 2024. Bar: **same sign, and within `[1/3, 3]×` the magnitude, for every
class where `|prediction| ≥ 0.5` TWh.**

| class | `P-3′` pred | realised (arm−keeper) | **ratio** | in scope | `G-1` |
|---|---:|---:|---:|---|---|
| **ST_GAS** | +0.5964 | **+1.9554** | **3.279** | **YES** | **FAIL** |
| COAL | −0.8474 | −1.7200 | 2.030 | YES | PASS |
| CC_REGULAR | −0.6602 | −0.7527 | 1.140 | YES | PASS |
| CC_CHP | +0.7082 | +0.3651 | 0.515 | YES | PASS |
| *CT_PEAKER* | *+0.2849* | *+1.3440* | ***4.717*** | *no* | *—* |
| *import* | *−0.2094* | *−1.3128* | ***6.269*** | *no* | *—* |
| *ST_CHP / CT_CHP / oil* | *+0.1426 / −0.0150 / −0.0002* | *+0.1073 / −0.0260 / −0.0034* | *0.753 / 1.737 / 17.041* | *no* | *—* |

**`ST_GAS` misses by 0.279 on a bar I set myself**, before either predictor existed, and justified on
SPP-49's own ~3.6× predictor miss. **`G-1` IS `FAIL`.**

**NO BAR IS MOVED AND NO REPAIR IS MADE, and the reason is the one miso-246 fixed for this lane:
the gate was SATISFIABLE.** Three of its four in-scope classes clear it, one (`CC_REGULAR`, 1.140)
comfortably. Re-scoping `G-1` to the classes that passed, widening the band to 3.3×, dropping
`ST_GAS`, or reverting to the pre-repair `P-3` would each convert the failure into a pass **by
construction**. **None is done.** This is a **RESULT**, not a broken gate.

**`R-ALL` HONOURED (ADDENDUM 3 §3, declared before the numbers, carrying no decision rule).**
`CT_PEAKER` — the class my own repair moved out of scope — **would ALSO have failed**, at 4.717, and
so would `import` at 6.269. **That is the outcome least favourable to the repair I made, and it is
reported in the headline table rather than left to the scope rule.** `G-1`'s verdict is computed on
its four in-scope classes exactly as pre-registered and is unchanged by them.

**The pattern, stated without being used to excuse anything:** every in-scope class has the **correct
sign**, and every miss is in the **same direction** — the LP responds **more** than `P-3′` predicts
(3.28 / 2.03 / 1.14 / 0.52, and 4.72 / 6.27 out of scope). A single-zone merit re-clear with no
commitment, no transmission, no storage and no floors systematically under-predicts a response that
propagates through all four. **That is an explanation of the failure, not a defence of the arm**, and
it does not move the bar.

## 2. THE OTHER THREE GATES PASS

* **`G-2` PASS.** `wind`, `solar`, `nuclear`, `hydro`, `storage` energy delta (arm − control) is
  **exactly 0.0** on every one. `P-1` measured the moved-row set at 886 of 2,843 rows, **all
  thermal**; renewables are LP decision variables and carry no fleet row, so neither repair can reach
  their availability.
* **`G-3` PASS.** Both identities hold in the **SOLVED** year, not only the offline rebuild. The
  screen: *123 plant-months high → reference on 29 plants, 2 low, 0 negative, 0 on the US fallback, 0
  unscreened* — and **zero** occurrences in the control, which pins it `False`. The floor:
  `min_signed_dhr = 0.0` (it never lowers a rate) with `hr_after ∈ {9.0, 9.9, 39.6}` exactly.
* **`G-4` PASS — 0 collateral flips.** Reported, not gated, because they are moves and not flips:
  **five gas classes move TOWARD** the actual (`CC_REGULAR` 3.87→3.149, `CT_PEAKER` −1.83→−0.482,
  `ST_GAS` −5.038→−3.167, `CC_CHP` −0.712→−0.347, `ST_CHP` −2.759→−2.677), **three coal classes move
  AWAY** (`COAL_PRB` −3.36→−4.59, `COAL_BIT` −3.532→−3.988, `COAL_LIGNITE` −0.772→−0.805), system
  volume gas **toward** (−6.47→−3.52) and coal **away** (−7.55→−9.27), and **mean price moves toward,
  1.19 → 0.54.**

## 3. **WHAT THE EARNED CONTROL BOUGHT — the session's most useful number**

`D-1` cost this session a control solve. It bought an attribution that is **measured, not assumed**:

| class | **A** = arm − control | **B** = control − keeper |
|---|---:|---:|
| ST_GAS | **+1.9155** | +0.0399 |
| COAL | **−1.7948** | +0.0748 |
| CT_PEAKER | **+1.6171** | **−0.2732** |
| import | **−1.3788** | +0.0660 |
| CC_REGULAR | **−0.8167** | +0.0640 |
| CC_CHP | **+0.3403** | +0.0248 |

**A carries essentially the whole response. B is small and correctly signed** — the heat-rate floor
makes 624.8 MW of small simple-cycle plant dearer, so `CT_PEAKER` falls by 0.2732 TWh and every other
class moves under 0.08 TWh as a re-clearing consequence. **`D-4` IS NOT FALSIFIED: no class moved in
`control − keeper` that `D-1` did not predict.** Had the audit missed a hunk, this column is where it
would have shown, and it does not.

## 4. **WHY THE FULL SPAN IS SPENT ANYWAY — the authority is named, and it is NOT the screen's**

Rule 29 `[R-SCREEN]`'s screen is a **STOP** gate, and on the rule as written **`G-1`'s failure stops
this arm from reaching the full span on the session's own authority.** It is not being reinterpreted.
Two things that are not the screen carry the full span instead, and both are stated so a reader can
reject either:

1. **THE OWNER'S EXPLICIT INSTRUCTION, received mid-session, verbatim:** *"Is this a recommended
   keeper candidate? If so plz promote. If structural integrity improves but gates regress that may
   still be a keeper.."* A promotion determination cannot be produced from a one-year screen — rule 16
   `[R-ALLYEARS]` requires 2023–2025 in one invocation and one bundle — so answering the question at
   all requires the span.
2. **RULES 1 `[R-STRUCT]` AND 14 `[R-ACCURATE]`, which point the same way independently.** Both P19
   objects are **measured-input construction repairs with zero free parameters**, already adopted
   **repo-wide by owner ruling**: an own-reported plant-month outside `[0.5, 2.0] ×` its own state's
   measured delivered price is an average cost on the wrong basis, and a simple-cycle-only plant
   cannot beat the best bare turbine. Rule 14 says keep the accurate input **even if the fit gets
   worse**, and rule 1 says a structurally-correct mechanism is **never** judged by the residual.
   **MISO's keeper is the only artifact in the program still standing on the pre-repair inputs**, and
   `B` cannot be declined at all — it is ungated, so **every** future MISO solve carries it.

**WHAT IS NOT CLAIMED BY THIS.** The full span is **not** a screen pass, and nothing below may be
read as one. `G-1` stands `FAIL` on the record, unrepaired, in this document and in the FINDING.
Whether the resulting bundle is promoted is the **owner's** decision on the evidence, and the
evidence includes this failure.

## 5. Non-claims

1. **`G-1`'s failure is not withdrawn, re-scoped, repaired or explained away**, and its per-class
   values are fixed in §1 before anything else is written.
2. **No bar is moved anywhere in this session.**
3. **The screen did not clear**, and the full span's authority is named in §4 rather than borrowed
   from it.
4. **`R-ALL` reports the two out-of-scope classes that would also have failed**, against interest.
5. **Zero free parameters**; DOF **41/2**; no `ScenarioConfig` field created or changed; both P19
   objects are repo-wide owner-ruled defaults, not MISO inventions.
6. **2023–2025 only**; no marker sought or implied; **C3c untouched** and a target in neither
   direction.
7. **2025 C1/C2 are SKIPPED** on the preliminary EIA-923 vintage; no 2025 C1 pass is read as
   evidence.
