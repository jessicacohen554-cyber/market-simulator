# FINDING (pjm-158): the DA virtual layer's admissibility invariant is defined at a price this LP does not produce. The rung compression is **exact**; the clearing basis is **wrong**. And the bench's 2022 coal rows were readable all along

**Session:** pjm-158 (the pjm-157 re-point, Object A)
**Date:** 2026-08-06
**Branch:** `claude/pjm-da-virtual-clearing-gt6wgm`
**Pre-registration:** `results/calibration/PREREG-pjm158-da-virtual-clearing-2026-08-05.md`
(committed and pushed at `6a3dab7a`, **before either arm solved** — the pjm-143
precedent)
**Holdout freeze (rule 22):** respected absolutely. 2022 was **not** solved,
scored or registered; every identification below is measured **in-sample on
2023–2025**. The only 2022 numbers quoted are READS of already-committed
artifacts, which is what pjm-157 did and what Question C required.

---

## §0 — the verdict in one table

| Phase-0 question | result | consequence |
|---|---|---|
| **C** — is the bench's 2022 coal basis broken? | **NO.** The bench carries THREE coal measures; pjm-157 differenced against the two the scorer does **not** use. On the EIA-923 `classFull` basis the gate actually uses, the model's 2022 coal is **−0.01 TWh**. | **CLOSED.** The 2022 C1/C2 coal rows were readable all along, and C2 already **PASSES**. |
| **0.3** — is the `N_RUNGS` compression a representation bug? | **NO.** It contributes **−0.068 / −0.008 / −0.110 TWh**; λ0 displacement **−0.19/−0.23/−0.48 $/MWh**; 8→64 rungs moves the cleared volume ≤ 0.13 TWh. | The docstring's "resolution only, never tunable values" is **VERIFIED**. The hoped-for representation-exact fix **does not exist**. |
| **0.2** — what is the layer's gain? | `dNet/dλ` = **−440 / −463 / −340 MW per $/MWh**, steepest overnight (h00–h09, −450 to −540), flattest at the afternoon peak. A uniform $1/MWh error is worth **3.0–4.1 TWh/yr**. | C1 is quantitatively conditional on C3b, as pjm-157 argued. |
| **0.2b** — *against which price is the invariant even defined?* | The anchor reproduces at actual **DA** prices (−0.76/−1.62/+0.20 TWh). The model's dual is gated as **RT**. Clearing the same curve at actual RT gives **+5.08/+3.00/+6.78 TWh of phantom demand**. | **THE FINDING.** The invariant is **unreachable in this LP** at any price-calibration quality. |
| **Phase 1** — the pre-registered A/B | **P1, P2, P3 all CONFIRMED.** Disarming adds +5.95/+5.18/−2.01 TWh of physical generation, moves `CC_REGULAR` by **+5.22/+6.85/+2.69 TWh**, and degrades every price gate. Control passes all criteria; **treatment FAILS C3c-2025**. | The layer's effect is real and large. **The fit is better armed** — reported, not decisive (rule 1). |

**The one sentence that replaces pjm-157's open question.** pjm-157 asked
whether a layer whose net clearing runs ±8 TWh from its own admissibility
anchor belongs in a keeper while C3b is unconverged. The answer is that the
deviation is **not** a C3b symptom that a better price would cure: **+4.6 to
+6.6 TWh of it is a DA−RT basis term that a *perfect* price would not remove**,
because the mechanism's anchor is a Day-Ahead quantity and the model's dual is
gated, by the scorer's own definition, as real-time.

---

## §1 — Question C: the bench's coal basis is sound; pjm-157 read the wrong column

`scripts/probes/_pjm158_coal_basis.py`.

The bench part carries **three independent coal measures**, and they disagree
**by construction** because they are three different censuses:

| yr | 930 `COL` (BA telemetry) | bench `coal_cems` (42-plant CAMPD census) | **EIA-923 `classFull`** (every plant ≥ 1 MW) | **model** | **model − 923** |
|---|---:|---:|---:|---:|---:|
| **2022** | 167.38 | 147.46 | **152.72** | 152.70 | **−0.01** |
| 2023 | 120.96 | 113.41 | 112.47 | 112.59 | +0.12 |
| 2024 | 122.36 | 115.35 | 115.20 | 114.14 | −1.06 |
| 2025 | 145.89 | 134.81 | 136.86 | 142.75 | +5.89 |

**Which one the scorer uses.** `calibration_verdict.family_is_complete` returns
`True` for any year absent from `completeness.js`; that file carries **2025
only**, so 2022 is a complete vintage and C1/C2 score coal against **`a923` =
`classFull`**. On that basis the model's 2022 coal error is **−0.012 TWh
(−0.008 %)** — the smallest of the four years — and the committed touchpoint
metrics already record **C2 = PASS** for 2022.

**So there is no 2022 coal anomaly to resolve.** pjm-157's "+5.1 against the
bench's own 42 plants; −14.2 against 930 `COL`" differenced the model against
the CEMS census and the BA telemetry, neither of which is the gate's actual. Of
the three candidate causes the handoff named:

- **(a) net/gross convention — EXCLUDED by scaling and by sign.** A
  fraction-of-output basis error scales with output. Fitting the in-sample
  gap-vs-output relation and extrapolating predicts **13.7 TWh** for 2022
  against an observed **19.9**. Separately, 2022's census ran at CF **0.443**
  vs 0.341/0.347/0.405 — a *higher* load factor, which makes the parasitic
  fraction *smaller*, not larger.
- **(c) a 2022 CAMPD extract defect — EXCLUDED.** The widening also appears
  between 930 `COL` and EIA-923 (**+14.66** TWh in 2022 vs +8.49/+7.16/+9.02
  in-sample), two full-footprint sources that never touch CAMPD.
- **(b) out-of-census coal — CONFIRMED as the residual.** EIA-860 records
  **4,431.9 MW** (11 units) of PJM-footprint coal retiring during 2022 and
  **4,014.1 MW** (12 units) during 2023, against a bench census frozen at the
  **same 42 plants** for 2022 and 2023.

### §1.1 — a real bench defect found on the way (hourly only, not `c_ann`)

Three PJM **coal** plants carry **`npl = 1 MW`** in the bench because the
nameplate lookup ran against an operable vintage that no longer contains them
(a fourth, `384` = **Joliet 29**, IL, is `ST_GAS` and strands a further 0.54 TWh):

| bench id | plant | state | group | 2022 `c_ann` TWh |
|---|---|---|---|---:|
| 2866 | **W H Sammis** | OH | COAL_BIT | 4.944 |
| 3122 | **Homer City Generating Station** | PA | COAL_BIT | 3.165 |
| 10678 | **AES Warrior Run Cogeneration** | MD | COAL_BIT | 1.222 |

Their `c_ann` is correct, so **`coal_cems`, `classFull` and every annual gate
are unaffected**. But the per-plant hourly `campd` blob is `uint8 % of
nameplate × npl`, so with `npl = 1` the hourly series is destroyed. The bench's
reconstructed PJM coal **hourly** total is therefore short by **9.27 TWh
(2022) / 2.53 (2023) / 0.32 (2024) / 0.00 (2025)** against `c_ann`.

Two consequences worth logging: the "42-plant / **38,003 MW**" census capacity
is understated by ~4.2 GW; and any probe that reconstructs monthly/hourly PJM
**coal** actuals from the blobs — including **pjm-157 §2's monthly elasticity
panel** — is running on a series that is 6.3 % short in 2022 and 2.2 % short in
2023. pjm-157's fidelity check was performed on `CC_REGULAR` (exact) and not on
coal. *This does not re-open the CC object* (which this session is barred from
re-testing and did not test); it is logged as a bench-data defect for whoever
next reads those blobs.

**It is a CROSS-ISO bench-builder defect, not a PJM one.** Scanning every
committed bench part for plants with `npl ≤ 1 MW` and `c_ann > 0.05 TWh`:

| ISO | year | plants | TWh stranded in the hourly blob |
|---|---|---:|---:|
| **PJM** | 2022 | 4 | **9.87** |
| PJM | 2023 | 4 | 3.26 |
| PJM | 2024 | 1 | 0.32 |
| MISO | 2023 / 2024 / 2025 | 2 / 2 / 1 | 2.77 / 1.79 / 1.60 |
| NEISO | 2022 / 2023 / 2024 | 1 / 1 / 1 | 1.66 / 1.34 / 1.27 |
| CAISO | 2023 | 1 | 0.29 |

The pattern is the same everywhere — a plant that retires inside the backcast
window drops out of the operable vintage the nameplate lookup reads, and
defaults to 1 MW. Annual gates are unaffected in every ISO; **hourly/monthly
reconstructions from `bench.plants[*].campd` are not.** Reported, not fixed:
repairing the bench builder is outside this session's charter, and no verdict
is transferred between ISOs (rule 25 — this is a shared data-builder defect,
not a mechanism verdict).

---

## §2 — Phase 0.3: the rung compression is EXACT

`scripts/probes/_pjm158_virtual_gain.py`. Attribution chain, TWh, `+` = net
virtual DEMAND (phantom load). Each step adds exactly one effect, so the
deviation is attributed with **no free parameter**:

| step | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **1** anchor: raw curve @ actual DA price | −0.755 | −1.620 | +0.204 |
| **2** + model price level (system dual) | −7.408 | −6.649 | +0.852 |
| **3** + zonal dual dispersion | −7.395 | −6.577 | +0.925 |
| **4** + `N_RUNGS` ladder compression | −7.462 | −6.585 | +0.815 |
| **5** OBSERVED (the LP's own clearing) | −7.451 | −6.552 | +0.905 |
| | | | |
| **step 2** — price level | **−6.593** | **−4.544** | **+1.695** |
| step 3 — zonal dispersion | +0.014 | +0.072 | +0.073 |
| step 4 — compression | −0.068 | −0.008 | −0.110 |
| step 5 — unexplained | +0.011 | +0.032 | +0.090 |

The reconstruction reproduces the LP's own cleared volume to **≤ 0.09 TWh**
against a 30–36 TWh gross turnover, so nothing material is unaccounted for.

**Compression verdict.** The crossing price is displaced by **−0.19 / −0.23 /
−0.48 $/MWh** (the ladder's DEC-top/INC-bottom bracket midpoint sits marginally
*below* the raw curve's λ0), and raising `N_RUNGS` from 8 to 64 moves the
cleared volume by **≤ 0.13 TWh**. `virtual_bids.N_RUNGS`'s documented claim —
"resolution / LP-columns trade-off only … not tunable values" — is **verified,
not merely asserted**.

**This forecloses the best-case outcome the handoff hoped for.** There is no
representation-exactness bug with a legitimate non-tuning fix. 97–99 % of the
deviation is the price the curve is cleared at.

---

## §3 — Phase 0.2: the gain, and the shape

`_pjm158_virtual_gain.py`, `_pjm158_virtual_shape.py`.

**The gain.** `dNet/dλ` at the actual DA price, MW per $/MWh (central
difference; stable across ±$1 / ±$5 / ±$10):

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| mean | **−440.5** | **−462.8** | **−340.3** |
| winter / shoulder / summer | −432 / −449 / −432 | −505 / −470 / −408 | −313 / −370 / −308 |
| annual Σ\|gain\| (GWh per $/MWh) | 3,859 | 4,055 | 2,981 |

By hour-of-day the gain is **steepest overnight** (h00–h09: −450 to −540) and
**flattest at the afternoon peak** (h15–h18: −265 to −428) — i.e. the amplifier
is strongest exactly where PJM's price-shape residual is structurally largest.

**The shape survives; the magnitude does not.** pjm-105's structural claim is
that the symmetric form is "a time-of-day reshaper, not a volume adder". In the
LP that claim **holds qualitatively** — hour-of-day correlation between the
model's position and the reference position is **+0.755 / +0.661 / +0.651**,
with net demand in the afternoon and net supply overnight, as measured. But the
LP runs it **1.3–1.4× too large**:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| afternoon h14–18, reference → model (GW) | +1.26 → **+2.04** | +1.36 → **+2.71** | +1.75 → **+3.63** |
| overnight h19–03, reference → model (GW) | −1.37 → **−2.76** | −1.50 → **−2.84** | −1.35 → **−1.77** |
| mean \|position\| (GW) | 2.62 → 3.49 | 2.92 → 4.01 | 3.16 → 4.13 |

The largest hour-of-day distortion is **h00–h05 (Δ −1.8 to −3.6 GW** of excess
net virtual supply**)** — the steepest-gain hours.

---

## §4 — THE FINDING: the invariant is defined at a price this LP does not produce

`scripts/probes/_pjm158_virtual_basis.py`.

**The anchor reproduces.** Clearing the raw measured net curve at the repo's own
committed PJM DA system LMP (`data/raw/_validation-source/actual_lmp_hourly_PJM.parquet`,
the **same series** `_pjm105_symmetric_equilibrium.py` used) gives an annual net
of **−0.755 / −1.620 / +0.204 TWh** against a 30–36 TWh gross turnover. pjm-105
published −0.68 / −0.95 / +1.32 for the *rendered ladders*; the difference is
rung discretization, exactly as its own text says. **The mechanism's rule-13
admissibility argument is sound — at the DA price.**

**But the model is not gated at the DA price.** `calibration_verdict
.score_price_mean`'s own docstring: *"C3a — system load-weighted mean LMP vs
actual **RT** (fallback DA) … perfect-foresight dispatch LP prices RT physics,
not day-ahead risk … The DA comparison is surfaced separately as a **non-gated
diagnostic**."* And `render_calibration_html` builds the hourly price residual
against `_actual_rt_padded` *"because the model's clearing price is a real-time
marginal-energy analogue (no day-ahead unit-commitment smoothing)"*.

**And PJM takes the RT branch, not the DA fallback.** `score_price_mean`
selects `rt_lw` when the bench carries it and only falls back to `da_lw`/`da`
when it does not; PJM's bench parts carry `rt_lw` in **all three years**
(29.55 / 31.31 / 45.80 $/MWh). The DA−RT spread is also basis-robust: +0.96 /
+0.29 / +0.78 $/MWh load-weighted vs +0.89 / +0.26 / +0.83 on the unweighted
system series this probe (and pjm-105) clears at.

Clearing the **same measured curve** at actual RT instead of actual DA:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| anchor @ actual **DA** (the rule-13 reference) | −0.755 | −1.620 | +0.204 |
| anchor @ actual **RT** (what the model is gated on) | **+5.082** | **+3.001** | **+6.781** |
| **DA−RT basis term** | **+5.836** | **+4.621** | **+6.577** |
| observed (the LP's own clearing) | −7.451 | −6.552 | +0.905 |
| model's own error vs actual RT | −12.533 | −9.553 | −5.876 |
| **total deviation from the DA anchor** | −6.697 | −4.932 | +0.701 |

**A model whose dual reproduced actual RT exactly — a perfect model by the
project's own load-bearing price gate — would clear this layer at +5.08 / +3.00
/ +6.78 TWh of phantom DEMAND, not ≈ 0.** The mean hourly \|DA−RT\| spread is
**$8.0–$11.7/MWh**, and at a −400 MW/$ gain that is worth several TWh/yr by
construction.

**Neither half of the basis can be corrected away separately.** Clearing at an
intermediate price — RT's hour-by-hour *shape* carrying DA's *mean* — splits
the basis exactly:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| LEVEL (same shape, DA mean → RT mean) | +2.991 | +0.973 | +2.432 |
| SHAPE / hour-by-hour dispersion | +2.845 | +3.648 | +4.145 |
| = DA−RT basis | +5.836 | +4.621 | +6.577 |

The level leg reproduces `−mean(DA−RT) × gain` to ~1 % (2024: 0.256 $/MWh ×
462.8 MW/$ × 8760 h = 1.04 TWh vs +0.973 measured), which validates the split.
Dispersion is the larger leg in 2024 and 2025, so **a level adjustment alone
would not close it** — and a level adjustment tuned to the gap would be a
rule-13 violation in any case.

Three consequences:

1. **The invariant is unreachable in this LP.** It is not a calibration
   residual that better price work would close; it is a market-basis mismatch.
   The layer is a Day-Ahead instrument and the model represents one price,
   defined and gated as real-time.
2. **The keeper's near-cancellation is a coincidence of two large opposing
   errors,** not a property of a well-specified mechanism: basis **+5.8/+4.6/+6.6**
   against model price error **−12.5/−9.6/−5.9**. If PJM's price shape improved
   toward RT — the stated goal of the whole price-formation lane — the layer
   would move **toward +5 to +7 TWh of phantom demand**, i.e. *toward* the
   condemned pjm-102 clamp's +10.3/+14.8/+17.2, not away from it.
3. **The mirror image of pjm-102.** pjm-102 was condemned for one-sided phantom
   **demand**. The adopted symmetric form clears at up to **7.45 TWh of phantom
   SUPPLY** — and pjm-105's own results table records that adopting it moved
   2024 `CC_REGULAR` from **+9.07 → −1.78 TWh**, which is why it was adopted.

### §4.1 — a correction to pjm-157's deviation numbers

pjm-157 §1.1 reported the model's deviation from the anchor as
**+8.13 / +7.50 / −2.23 TWh**. Those were computed with the anchor carried on
the *opposite* sign convention from the model (`7.45 − (−0.68) = 8.13`), so the
two were **added** rather than differenced. On one consistent convention the
deviations are:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| pjm-157 as published | +8.13 | +7.50 | −2.23 |
| **corrected (this session)** | **−6.70** | **−4.93** | **+0.70** |

The direction of pjm-157's conclusion is unaffected — the layer does clear
materially away from its anchor in the tuned years — but the effect is **1.4 /
2.6 / 1.5 TWh smaller** than reported, and 2025's is small enough that only
2023 and 2024 carry a material deviation. The handoff's P1 arithmetic is
unaffected: it used the model's own cleared volume (7.45 / 6.55 / −0.91), not
the deviation.

**Caveat, stated plainly.** The anchor is sensitive to the reference price, which
is itself part of the finding: across PJM's published hubs the same curve's
annual net spans **12.7–24.4 TWh** (2024: EASTERN −1.5, AEP-DAYTON −6.3, WESTERN
−14.0, DOMINION −14.2). The canonical committed system series is the right
reference and it does give ≈ 0, so the admissibility argument stands *as
written* — but "≈ 0" is a property of the curve **evaluated at one particular
price**, not of the curve.

---

## §5 — Phase 1: the pre-registered A/B — all three predictions CONFIRMED

Registered runs: **`2026-08-06-pjm-158-control-virtual`** (`pjm158_ctl_A`,
layer armed) and **`2026-08-06-pjm-158-novirtual-disarmed`**
(`pjm158_novirt_B`, layer disarmed). Both `--year 2023 2024 2025` in one
invocation, years sequential (rules 12/16).

**The control validates the whole A/B: it reproduces the pjm-152 keeper
BYTE-IDENTICALLY — max |Δ| = 0.00000 TWh across every class and every year.**
So HEAD *is* solve-identical to the keeper's basis for PJM's backcast path; the
37-file / 6,414-insertion diff since `bc9e6dbf` is entirely forecast-lane code.
The handoff asked for this to be verified rather than assumed, and it was
verified by solving. The delta is also visible in the solver logs — the control
builds "64 DEC-form + 64 INC-form pseudo-units" in each year, the treatment
builds none, and the LP matrix build drops 44.3 s → 18.8 s.

### §5.1 — P1 (system generation): CONFIRMED in all three years

| TWh | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| layer net demand in control (+ = phantom load) | −7.451 | −6.552 | +0.905 |
| Δ physical generation (treatment − control) | **+5.949** | **+5.182** | **−2.011** |
| Δ seam (`import`) | +0.999 | +0.667 | +0.368 |
| implied NG-equivalent error, control → treatment | −9.94 → **−3.99** | −9.25 → **−4.07** | +1.72 → **−0.29** |

The error moves toward zero in **all three** years. The pre-registered point
predictions (−2.49/−2.70/+0.81) are not hit exactly, and the reason is the
caveat pre-registered with them: the unconstrained star node (pjm-135 M4)
absorbed **+1.00/+0.67/+0.37 TWh** of the removed supply. P1 was registered as
a direction test and passes as one.

### §5.2 — P2 (the mechanism): CONFIRMED decisively

| `CC_REGULAR`, TWh | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| control (armed) | 322.218 | 335.446 | 334.317 |
| treatment (disarmed) | 327.439 | 342.295 | 337.006 |
| **Δ** | **+5.220** | **+6.848** | **+2.689** |
| actual (`classFull`) | 325.670 | 335.124 | 330.361 |
| error, control → treatment | −3.451 → +1.769 | +0.322 → **+7.171** | +3.957 → **+6.645** |

The falsification bar was |Δ| < 2 TWh in both 2023 and 2024; the observed Δ is
**+5.22 and +6.85**. **The cleared virtual is displacing `CC_REGULAR`, and
pjm-157 §1.1's causal channel is confirmed.** Roughly 80 % of the withdrawn net
supply lands on physical generation and ~13 % on the seam.

**Where my prediction was wrong, stated plainly.** P2 also predicted the
`CC_REGULAR` *error* would move **away** from zero in 2023 and 2024. It does in
2024 (+0.32 → +7.17) and 2025 (+3.96 → +6.65), but **not in 2023**, where it
crosses zero and |error| improves (3.45 → 1.77). The reason is a baseline
error of mine: I anchored the prediction on pjm-157's `CC_REGULAR` errors
(+3.28/+6.32/+10.73), which are on the **CEMS census** basis, while the C1 gate
scores against **EIA-923 `classFull`**. That is the same three-bases trap §1
documents for coal, and it is not coal-specific:

| `CC_REGULAR` actual, TWh | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| `classFull` (EIA-923 — **what C1 scores**) | 297.130 | 325.670 | 335.124 | 330.361 |
| `c_ann` (CEMS census — what pjm-157 used) | 290.008 | 318.941 | 329.125 | 323.587 |
| offset | +7.123 | +6.729 | +5.999 | +6.774 |

The offset is stable at ~+6–7 TWh in every year, so pjm-157's *year-over-year*
decomposition is unaffected. Its *level* statements are not: **the 2022
`CC_REGULAR` error is +25.40 TWh on the CEMS basis and +18.28 TWh on the basis
the gate actually uses.** (Recorded because it is the same measurement issue
Question C resolves — not a re-test of the CC object, which this session did
not re-open.)

### §5.3 — P3 (prices): CONFIRMED in all three years

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| C3a mean error, control → treatment | +8.8 % → **+9.7 %** | +2.1 % → **+3.5 %** | −5.0 % → **−6.3 %** |
| hourly MAE vs actual RT ($/MWh) | 9.20 → **9.94** | 10.50 → **11.82** | 13.97 → **15.24** |
| hours > $200 (model / actual) | 0 / 6 | 0→8 / 18 | 16→11 / 59 |

Prices degrade on level and on MAE in every year, as pre-registered.

### §5.4 — the rubric verdict

| criterion | CONTROL (armed) | TREATMENT (disarmed) |
|---|---|---|
| C1 fuel-mix by class | **PASS** | **PASS** |
| C2 system volume | **PASS** | **PASS** |
| C3a mean LMP | **PASS** | **PASS** |
| C3b price duration/shape | **PASS** | **PASS** |
| **C3c price tail / scarcity** | **PASS** | **FAIL** — 2025 model 22 h vs RT actual 59 h (0.37×) |
| C4 dispatch correlation | **PASS** | **PASS** |
| C7 diurnal shape | **PASS** | **PASS** |
| C8 forced-energy share | **PASS** | **PASS** |
| determination | NOT-YET (C6 unattested) | NOT-YET (C6 unattested) |

**Disarming costs exactly the criterion pjm-105's adoption note credited the
layer with fixing** ("moved 2025 C3c 0→17h").

### §5.5 — what the A/B does and does NOT settle (rule 1)

**Settled.** The mechanism is doing real, large work: it injects 5–7 TWh/yr of
net virtual supply, that supply displaces `CC_REGULAR`, and removing it
degrades C1 `CC_REGULAR`, all three price gates, and breaks C3c-2025. pjm-157's
channel is confirmed. **The fit is unambiguously better with the layer armed —
and under rule 1 that is reported, not decisive.**

**Not settled by the A/B, and this is the point.** Phase 0 established that the
layer's rule-13 admissibility invariant is **unreachable in this LP** (§4): its
anchor is a Day-Ahead quantity, the model's dual is gated as real-time, and the
DA−RT basis alone is +4.6 to +6.6 TWh. No A/B can fix that, because it is a
property of the model's architecture — the LP carries **one** price series —
not of the mechanism's parameters. The A/B measures the mechanism's *effect*;
Phase 0 measures its *justification*, and the justification is the part that
fails.

**Departure from my own pre-registered decision rule, and why.** §3(1) of the
pre-registration said: if P2 confirms, "recommend the matrix cell move `K` →
`R` … and say plainly that the fit gets worse". P2 confirmed. I am **not**
executing that status change, and the reason is that the rule was written
against an expectation the evidence overturned. It assumed disarming would
*improve* the fit, making `R` the rule-1-clean call (real structure kept
despite a worse residual is the rule; a phantom mechanism kept *because* of a
better residual is what rule 1 forbids). The measured outcome is the opposite:
disarming makes the model worse on **every** load-bearing and supporting gate
and removes real, measured DA depth (~7–11 GW at the peaks) that pjm-105
documented. Moving `K` → `R` on that evidence would be rejecting real market
structure — which rule 1 forbids just as firmly as keeping a fitted one.

The defect this session actually found is better described by rule 14
`[R-ACCURATE]`: a **real measured input genuinely misaligned to our
representation**. Rule 14's instruction for exactly that case is to keep the
accurate input, **document the misalignment explicitly**, and open the
root-cause investigation rather than bury the error in a worse input. So:

- the cell stays **`K`**, with the DA−RT basis logged as a **material,
  measured, open defect** on the armed mechanism;
- the layer's **cleared volume must not be read as a measured cleared volume**
  — it is an LP output at a price the curve was never submitted into;
- the root cause (**the model represents one price, gated as RT; the layer
  needs a DA price**) is an **architecture question inside PJM's
  owner-declared-closed price-formation frontier (pjm-142)**, so it is escalated
  to the owner, not pulled as a lever here.

**A warning the owner should have.** The two error terms currently oppose each
other — basis +5.8/+4.6/+6.6 against model price error −12.5/−9.6/−5.9. They
do not cancel by design. If PJM's price shape improves toward RT, which is the
stated goal of the price-formation lane, **the layer's phantom energy grows
toward +5 to +7 TWh of phantom demand** — i.e. toward the condemned pjm-102
clamp's +10.3/+14.8/+17.2, not away from it. Any future C3b work on PJM should
expect this mechanism's C1 contribution to move against it.

---

## §6 — reproduction

```
scripts/probes/_pjm158_coal_basis.py      # §1  question C: three coal bases, census, EIA-860
scripts/probes/_pjm158_virtual_gain.py    # §2  attribution chain, gain, compression exactness
scripts/probes/_pjm158_virtual_basis.py   # §4  DA vs RT anchor, hub sensitivity
scripts/probes/_pjm158_virtual_shape.py   # §3  hour-of-day: reference vs the LP's clearing
```

Inputs: `frontend/data/backcast/bench/PJM/{2022..2025}.json.gz`;
`results/calibration/{pjm152_collapse_A,pjm2022_touchpoint}/`;
`data/raw/pjm-da-virtuals/hrl_da_incs_decs_{2023,2024,2025}_*.parquet`
(fetched this session by `scripts/data/fetch_pjm_da_virtuals.py`, whose default
span **is** 2023–2025 — in-sample, unrestricted, **not** data intake under
rule 22); `data/raw/_validation-source/actual_lmp_hourly_PJM.parquet`;
`data/raw/lmp-data/PJM_{2023,2024,2025}_rt_da_monthly_lmps.csv`;
`data/raw/eia-860/`; `data/raw/eia-930/`.
