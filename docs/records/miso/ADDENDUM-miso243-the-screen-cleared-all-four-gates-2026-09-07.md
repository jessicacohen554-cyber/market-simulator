# ADDENDUM miso-243 — **THE 2024 SCREEN CLEARS ALL FOUR PRE-REGISTERED STRUCTURAL GATES.** Recorded here BEFORE the full span is launched

**Governs:** `ADDENDUM-miso243-my-own-p2-leg-failed-and-the-screen-year-is-2024-2026-09-07.md` §3,
whose four bars were fixed **before the repair was applied to the tree and before the solve ran**.
**No bar moves.** Machine record: `results/calibration/_miso243_screen_gates.json`; evaluator
`scripts/probes/_miso243_screen_gates.py`, whose bars are **literals quoted from that addendum**.

Screen: **2024**, one year, one arm (`results/calibration/miso243_screen2024`, a **throwaway
diagnostic probe** — never registered, never a keeper, and its year is re-solved inside the full
bundle). Control: **the keeper's COMMITTED bundle** (G-CTRL form 4; **no control solve was spent**).

| gate | bar, fixed before the solve | **measured** | |
|---|---|---:|---|
| **G-1 CONFINEMENT** | slack + dump not above keeper; must-take within 0.5 % | slack **19,566.915 → 19,566.915 MWh** (Δ = 1.5e-11), dump **0 → 0**, wind / solar / nuclear / hydro **0.00 %** each | **PASS** |
| **G-2′(a) DISPLACEMENT** | `Σ|Δ class| / |Δ import|` ≤ 4.0 | Δ import **−423,500 MWh**, Σ|Δ generation| **423,112 MWh**, ratio **0.9991** | **PASS** |
| **G-2′(b) SCALE** | served energy change ≤ 0.5 % | **−0.00006 %** | **PASS** |
| **G-3 DIRECTION & MAGNITUDE** | sign NEGATIVE, and `Δq_solved ∈ [−430.60, −26.91] MW` | **−48.345 MW**, ratio to `Δq̂` **0.4491** | **PASS** |
| **G-4 COLLATERAL** | zero PASS → FAIL flips | **0 flips** | **PASS** |

**G-2′(a) is the informative one and it was falsifiable.** A ratio of **0.9991** means the seam's
lost imports are replaced almost exactly one-for-one by MISO generation: the mechanism moved a seam
and its direct displacement, and did **not** re-shuffle the fleet. A screen in which the fleet
churned several times the seam's own move would have failed here, and the bar allowed a factor of 4.

**G-3 landed at 0.449 of the pre-solve prediction, inside a window whose binding side is its lower
limit** — which is the direction the ADDENDUM §2 said it would be, *before the solve*: the measured
`(month × hod)` deliverability ceiling can only **clip** the band response, so `Δq̂` is an upper
bound in magnitude. The realized response is 45 % of the unclipped prediction, with the right sign.

**REPORTED, NEVER GATED** (`screen_collateral_gate` "moves" block; the gate is the flip count and it
is zero). Of the 11 scored moves, **9 are TOWARD actual and 2 away**: `CC_REGULAR` 3.755 → 3.870
(away), `CT_PEAKER` −1.934 → −1.830, `COAL_PRB` −3.443 → −3.360, `COAL_BIT` −3.562 → −3.532,
`ST_GAS` −5.079 → −5.038, `CC_CHP` −0.746 → −0.712, `ST_CHP` −2.762 → −2.759, `COAL_LIGNITE`
−0.773 → −0.772, system volume gas −6.76 → −6.47 and coal −7.66 → −7.55 (both toward),
`price_mean` 1.14 → 1.19 (away). **None of these is a gate**, in either direction; they are recorded
so the direction of travel is visible rather than selected from.

## What this authorizes, and what it does not

1. **The full span proceeds** — `--years 2023 2024 2025` in **ONE invocation** and **ONE bundle**
   (rule 16 `[R-ALLYEARS]`), years sequential (rule 12), the keeper's `calibration_attestation.json`
   carried forward with `governance.attested_by` + `disclosures` rewritten.
2. **The screen promoted nothing.** All four gates are STOP gates. The screen's numbers are not a
   determination, are not quoted as keeper numbers, and 2024 is re-solved inside the full bundle.
3. **No bar was moved and no gate was re-specified after seeing a number.** The two gate repairs
   this session made (P-2′ and G-2′) were both declared in a pushed addendum **before the repair
   reached the tree**, and both are stricter than what they replaced.
4. **Rule 31 `[R-RETAIN]`: the screen bundle is `.gitignore`d and stays on local disk.** It is not
   deleted, and the promotion question is surfaced explicitly in the session's final report.
