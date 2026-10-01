# PRE-REGISTRATION (pjm-158): does `pjm_da_virtual_bids` belong in the PJM keeper?

**Session:** pjm-158 (the pjm-157 re-point, Object A)
**Date:** 2026-08-05
**Branch:** `claude/pjm-da-virtual-clearing-gt6wgm`
**Status at time of writing:** Phase 0 COMPLETE (zero LP solves). **Neither arm
has solved.** This file is committed and pushed BEFORE either arm runs (the
pjm-143 precedent), so the predictions below are falsifiable.

---

## §0 — what Phase 0 established (all in-sample 2023–2025, no solve, no 2022)

Probes: `scripts/probes/_pjm158_coal_basis.py`,
`_pjm158_virtual_gain.py`, `_pjm158_virtual_basis.py`.

**(a) Question C is CLOSED — the 2022 coal rows were always readable.** The
bench carries THREE coal measures and pjm-157 differenced against the two the
scorer does **not** use. 2022 is absent from `completeness.js`, so
`family_is_complete(PJM, "coal", 2022)` is `True` and C1/C2 score against
EIA-923 `classFull` (which counts every plant ≥ 1 MW):

| yr | 930 `COL` | bench CAMPD `coal_cems` (42-plant census) | **EIA-923 `classFull`** | **model** | **model − 923** |
|---|---:|---:|---:|---:|---:|
| 2022 | 167.38 | 147.46 | **152.72** | 152.70 | **−0.01** |
| 2023 | 120.96 | 113.41 | 112.47 | 112.59 | +0.12 |
| 2024 | 122.36 | 115.35 | 115.20 | 114.14 | −1.06 |
| 2025 | 145.89 | 134.81 | 136.86 | 142.75 | +5.89 |

The 2022 C2 row already **PASSES** in the committed touchpoint metrics. The
apparent sign disagreement was a choice-of-basis artifact, not a dispatch
defect.

**(b) The rung compression is EXACT — no representation bug is available.**
Attribution chain, TWh, `+` = net virtual DEMAND:

| step | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| 1 anchor: raw curve @ actual DA | −0.755 | −1.620 | +0.204 |
| 2 + model price level | −7.408 | −6.649 | +0.852 |
| 3 + zonal dual dispersion | −7.395 | −6.577 | +0.925 |
| 4 + `N_RUNGS` ladder compression | −7.462 | −6.585 | +0.815 |
| 5 OBSERVED (the LP's own clearing) | −7.451 | −6.552 | +0.905 |

Compression contributes **−0.068 / −0.008 / −0.110 TWh**; λ0 displacement is
**−0.19 / −0.23 / −0.48 $/MWh**; `N_RUNGS` 8→64 moves the cleared volume by
≤ 0.13 TWh. The docstring's "resolution only, never tunable values" is
**verified**. The reconstruction reproduces the LP to ≤ 0.09 TWh, so nothing
material is unexplained.

**(c) The gain.** `dNet/dλ` = **−440 / −463 / −340 MW per $/MWh** (mean,
central difference at the actual DA price; stable across ±$1/±$5/±$10).
Steepest overnight (h00–h09, −450 to −540) and flattest at the afternoon peak
(h15–h18, −265 to −428). A uniform $1/MWh dual error is worth **3.0–4.1
TWh/yr** of cleared virtual.

**(d) THE STRUCTURAL FINDING — the invariant is defined at a price the model
does not produce.** The anchor reproduces at actual **DA** prices
(−0.76/−1.62/+0.20 TWh vs pjm-105's −0.68/−0.95/+1.32, the difference being
rung discretization). But the model's dual is a **real-time** marginal-energy
analogue *by explicit design* (`render_calibration_html`: "the model's clearing
price is a real-time marginal-energy analogue (no day-ahead unit-commitment
smoothing)"). Clearing the SAME measured curve at actual **RT**:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| anchor @ actual **DA** (the rule-13 reference) | −0.755 | −1.620 | +0.204 |
| anchor @ actual **RT** (the model's own price target) | **+5.082** | **+3.001** | **+6.781** |
| **DA−RT basis term** | **+5.836** | **+4.621** | **+6.577** |

**A model whose dual reproduced actual RT exactly would clear this layer at
+5.1 / +3.0 / +6.8 TWh of phantom DEMAND, not ≈ 0.** The admissibility
invariant is unreachable in this LP regardless of price-calibration quality.
That is a rule-1 statement about the implementation, and it is established
without any solve.

**(e) The mirror-image observation.** pjm-102 was condemned for +10.3/+14.8/
+17.2 TWh of phantom **demand**. The adopted symmetric form clears at
−7.45/−6.55/+0.91 TWh net demand — i.e. up to **7.45 TWh of phantom
SUPPLY**. pjm-105's own results table records that the layer moved 2024
`CC_REGULAR` from **+9.07 → −1.78 TWh**, which is why it was adopted. Phase 0
says that repair was delivered by phantom net supply.

---

## §1 — arms

Both arms solve at **HEAD** on this branch. HEAD is **NOT** solve-identical to
the keeper's basis (`bc9e6dbf`): `git diff --stat bc9e6dbf..HEAD -- src/market_sim
scripts/run_calibration_full.py scripts/lib` is 37 files / 6,414 insertions, so
the committed `pjm152_collapse_A` bundle **cannot** serve as the control and
both arms must solve. This was checked, not assumed.

| arm | command |
|---|---|
| **CONTROL** `pjm158_ctl_A` | `.venv/bin/python scripts/replay_keeper.py results/calibration/pjm152_collapse_A --out-dir results/calibration/pjm158_ctl_A` |
| **TREATMENT** `pjm158_novirt_B` | same `+ --set pjm_da_virtual_bids=false` |

`replay_keeper.py` replays the keeper's own `meta.json` kwargs, so the two arms
differ in exactly one field. Years **2023 2024 2025 in one invocation, solved
sequentially** (rules 16 / 12). No out-of-training year is solved, scored or
registered; the holdout freeze is untouched.

*Environment note (rule 12):* this container has **15 GB RAM and 0 swap**
against pjm-156's measured ~16 GB/year peak, so the arms run **sequentially**,
not concurrently, with a swapfile added first. Concurrency licence does not
override an OOM.

---

## §2 — falsifiable predictions

**P1 — system generation improves (the handoff's prediction).** Disarming
removes net virtual SUPPLY of 7.451 / 6.552 TWh (2023/24) and net virtual
DEMAND of 0.905 TWh (2025), so the model's EIA-930 NG-equivalent error should
move
`−9.94 / −9.25 / +1.72` → **`−2.49 / −2.70 / +0.81`** (first order).
**FALSIFIED** if the NG-equivalent error fails to move toward zero in at least
2 of 3 years. *Caveat pre-registered:* the seam (`import`) is unconstrained
(pjm-135 M4), so the star node may absorb part of the removed supply; P1 is
therefore a direction test, not an equality test.

**P2 — `CC_REGULAR` DEGRADES, and that is the point.** The 7.45/6.55 TWh of
removed phantom supply must be served by the marginal class, so C1
`CC_REGULAR` should move from `+3.28 / +6.32 / +10.73` **away** from zero in
2023/2024 — toward pjm-104's pre-mechanism `+9.07` in 2024. **This is the
prediction that makes the session a rule-1 test rather than a fit contest:** if
`CC_REGULAR` degrades exactly as the layer's phantom supply is withdrawn, the
mechanism's C1 credit was phantom-energy credit. **FALSIFIED** if `CC_REGULAR`
is materially unchanged (|Δ| < 2 TWh in both 2023 and 2024) — which would mean
the cleared virtual was NOT displacing CC and pjm-157 §1.1's causal story is
wrong.

**P3 — prices degrade.** The layer exists to deepen DA procurement ~7–11 GW at
peak hours, so C3a/C3b/C3c should get **worse**, most visibly in the overnight
trough where the measured gain is steepest. **FALSIFIED** if any price
criterion materially *improves*.

**P4 — the DA−RT basis is invariant to the arms.** It is a property of the
measured curve and the two measured price series, not of the model, so it
stays +5.84/+4.62/+6.58 TWh whatever the solve does. Any arm-dependence would
mean the probe is wrong.

---

## §3 — decision rule (rule 1 governs; the fit does not)

The question is **not** "which arm has the lower MAE". Rule 1
`[R-STRUCT]` forbids both "kill it because disarming improves MAE" and "keep it
because arming improves MAE". The question is whether an implementation whose
own admissibility invariant is **unreachable in this LP** belongs in a keeper.

1. **If P2 confirms** (CC_REGULAR degrades as phantom supply is withdrawn) —
   the layer's C1 credit is phantom-energy credit, the same failure class as
   the condemned pjm-102 clamp with the sign reversed. Recommend the matrix
   cell move `K` → **`R`** for PJM and the flag leave the keeper recipe, and
   say plainly that the fit gets worse.
2. **If P2 is falsified** (CC_REGULAR barely moves) — the cleared virtual is
   NOT displacing the marginal class, pjm-157 §1.1's channel is wrong, and the
   cell stays `K` with the DA−RT basis logged as an open defect.
3. **Either way** the DA−RT basis finding (§0d) stands on its own and is
   reported, because it is a no-solve measurement.

Promotion of any recipe change is scored **leave-one-year-out within
2023–2025** before it lands. **No 2022 number enters this decision at any
point.**

---

## §4 — what this session will NOT do

Pin, clamp, scale or otherwise force the layer's cleared volume toward the
measured reference (rule 13 / the condemned pjm-102 clamp); re-test the CC
gas-elasticity object (refuted at pjm-157, slope ratio 0.959); re-open the
diurnal-amplitude family or the overnight gas commitment bridge (closed /
`R` at pjm-142); open net interchange (chartered at pjm-135); transplant a
NEISO parameter (rule 25); or solve, score or register any out-of-training
year (rule 22; the freeze is active).
