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

Three PJM coal plants carry **`npl = 1 MW`** in the bench because the nameplate
lookup ran against an operable vintage that no longer contains them:

| bench id | plant | state | note |
|---|---|---|---|
| 2866 | **W H Sammis** | OH | retired 2023 |
| 3122 | **Homer City Generating Station** | PA | 2,012 MW BIT, retired |
| 10678 | **AES Warrior Run Cogeneration** | MD | coal cogen |

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

**Caveat, stated plainly.** The anchor is sensitive to the reference price, which
is itself part of the finding: across PJM's published hubs the same curve's
annual net spans **12.7–24.4 TWh** (2024: EASTERN −1.5, AEP-DAYTON −6.3, WESTERN
−14.0, DOMINION −14.2). The canonical committed system series is the right
reference and it does give ≈ 0, so the admissibility argument stands *as
written* — but "≈ 0" is a property of the curve **evaluated at one particular
price**, not of the curve.

---

## §5 — Phase 1: the pre-registered A/B

*(Filled in below once both arms land; predictions are frozen in the
pre-registration and were pushed before either arm solved.)*

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
