# FINDING — CAISO gas vs EIA-930: the 930 comparison is INVALID, but there IS a real gas defect underneath it, and it is CT_PEAKER

**Session caiso-240, 2026-09-03. ZERO SOLVES** — every number below is read from
committed artifacts: the keeper's run payload and benchmark
(`frontend/data/backcast/{runs,bench}/`), the EIA-930 CISO fuel-type parquet, and
the keeper's own `run_config.json`. Nothing armed, nothing registered, no
`ScenarioConfig` field touched, keeper unchanged.

Raised by the owner: *"CAISO seems to be significantly undershooting gas compared
to EIA-930 but this isn't captured in EIA-923 data for CAISO for 2023 and 2024."*
The observation is **correct**, and the reason is now measured.

---

## §1 — HEADLINE, IN TWO PARTS

**Part 1 — the EIA-930 comparison is not a valid benchmark, and the codebase
already says so.** CAISO gas measured against EIA-930's CISO `NG` cell reads
−27.4 / −29.4 / −30.9 TWh (−31 % / −34 % / −39 %). Against the two **independent
measured plant-level records** it reads −6.9 / −3.3 / −2.7 TWh (−10 % / −5.6 % /
−5.3 %). The difference is a property of EIA-930, not of the model:
`scripts/lib/benchmark_semantics.py` declares
`EIA930_NG_CORRUPT_ONSET = {"CAISO": 2023}` and the reconcile applies a
CEMS-anchor cap so the benchmark can never scale up to that cell.

**Part 2 — but there IS a real, structural, currently-UNGATED gas defect, and
the 930 headline hides it: `CT_PEAKER`.** The model dispatches CAISO peakers at
**2.5 % / 0.8 % / 0.4 %** capacity factor against a measured **7.4 % / 7.5 % /
4.1 %** — a **66 % / 89 % / 90 %** under-run worth −2.7 / −3.8 / −2.1 TWh a year,
monotonically worsening. **C1 passes it** only because the class is small enough
to sit inside the ±8 TWh volume band and the ±3.0 pp share band. That is exactly
the failure mode the 2026-07-02 band widening was warned about.

---

## §2 — THE 930-vs-923 RECONCILIATION, MEASURED

EIA-930 CISO against the plant-level (EIA-923) benchmark, mapped onto EIA-930's
own fuel buckets (TWh):

| bucket | 2023 EIA-930 | 2023 plant-level | Δ | 2024 EIA-930 | 2024 plant-level | Δ |
|---|--:|--:|--:|--:|--:|--:|
| **NG** | 87.74 | 67.16 | **+20.58** | 85.39 | 59.26 | **+26.13** |
| COL | 0.01 | 0.06 | −0.05 | −0.00 | 0.07 | −0.08 |
| OIL | 0.54 | 0.07 | +0.47 | 0.52 | 0.05 | +0.47 |
| NUC | 17.75 | 17.72 | +0.03 | 18.35 | 18.38 | −0.03 |
| WAT | 24.40 | 23.37 | +1.02 | 22.76 | 21.34 | +1.42 |
| SUN | 37.14 | 37.17 | −0.03 | 44.73 | 44.64 | +0.09 |
| WND | 16.43 | 16.40 | +0.02 | 20.04 | 20.06 | −0.02 |
| **GEO** | **0.00** | 0.00 | 0.00 | **0.00** | 0.00 | 0.00 |
| **OTH** | **−0.05** | **13.78** | **−13.82** | **−1.15** | **12.49** | **−13.64** |
| TOTAL | 183.96 | 175.74 | +8.22 | 190.64 | 176.29 | +14.34 |

Nuclear, solar and wind agree to **±0.03 TWh** — so the two records are aligned
on everything that is cleanly attributed. The NG excess has a mirror-image
deficit in `OTH`/`GEO` of almost exactly the same size:

* **EIA-930's CISO series reports ZERO geothermal in 2023 and 2024** and a
  *negative* "other" (−0.05 / −1.15 TWh), while the plant-level record carries
  **13.78 / 12.49 TWh** of geothermal + biomass. CAISO folds that energy into its
  `NG` cell.
* After deflating the fold-in, the residual excess is **+6.8 / +12.5 TWh**, which
  tracks the total-generation difference (+8.2 / +14.3 TWh) — a BA-footprint /
  small-generator coverage difference on top of the fuel mis-attribution.

**This is already adjudicated in the codebase, and my independent measurement
reproduces its numbers.** `scripts/lib/benchmark_semantics.py`:

> *"CAISO 2023 grid gas is EIA-923 **67.20 TWh** and CAMPD CEMS + non-CEMS cogen
> **68.74 TWh** — agreeing within 2.3 % — while the fold-in-deflated 930 NG cell
> reads **74.23 TWh**: +10.5 % over 923, +8.0 % over CEMS, far outside the 3 %
> `VINTAGE_RECONCILE_FRAC` deadband. Deflated-930 over EIA-923 runs **+10.5 %
> (2023) → +21.1 % (2024) → +32.8 % (2025)**, so the contamination is a monotone
> ramp."*

I measure EIA-923 gas at **67.16 TWh** (they say 67.20) and deflated-930 at
**73.95** (they say 74.23). **Two independent measured records agree within
2.3 %; EIA-930 disagrees with both and its disagreement grows every year.** The
model is calibrated to the agreeing pair. Nothing about CAISO gas should be
inferred from the EIA-930 CISO NG cell.

---

## §3 — WHAT THE VALID COMPARISON SHOWS: THE DEFECT IS CT_PEAKER

Model minus the plant-level actual, per class (TWh), and the model/actual ratio:

| class | 2023 | 2024 | 2025 | ratio 2023 / 2024 / 2025 |
|---|--:|--:|--:|---|
| CC_REGULAR | −2.94 | −0.01 | −0.96 | 0.94 / 1.00 / 0.98 |
| CC_CHP | +0.82 | +0.86 | +0.48 | 1.11 / 1.13 / 1.07 |
| **CT_PEAKER** | **−2.71** | **−3.84** | **−2.11** | **0.34 / 0.11 / 0.10** |
| CT_CHP | −0.86 | −0.78 | −0.10 | 0.59 / 0.61 / 0.92 |
| ST_GAS | −1.11 | +0.50 | +0.02 | — |
| **gas total** | **−6.86** | **−3.31** | **−2.69** | |

**It is not a capacity problem.** Model and benchmark share the same plant
registry, so nameplate is identical (CT_PEAKER 6,370 / 6,549 / 6,499 MW). It is
a **dispatch** problem:

| class | 2023 actual CF | 2023 model CF | 2024 actual / model | 2025 actual / model |
|---|--:|--:|---|---|
| CC_REGULAR | 37.7 % | 35.6 % | 33.3 % / 33.3 % | 29.0 % / 28.3 % |
| CC_CHP | 53.3 % | 59.0 % | 46.9 % / 52.8 % | 49.0 % / 52.4 % |
| **CT_PEAKER** | **7.4 %** | **2.5 %** | **7.5 % / 0.8 %** | **4.1 % / 0.4 %** |
| CT_CHP | 67.2 % | 39.8 % | 63.7 % / 38.9 % | 41.5 % / 38.2 % |

CC_REGULAR tracks reality closely in all three years. **CT_PEAKER does not run.**
The per-zone-month error series in the run payload (`volErr.CT_PEAKER`) shows
`e` between **−0.71 and −1.00 in every zone and every month** of 2023 and
−0.85 to −1.00 in 2024 — uniform, not seasonal. This is structural.

*(Second, smaller item recorded in passing: `CT_CHP`'s model CF is pinned near
39 % in all three years while the actual falls 67 % → 64 % → 42 %. It is a pinned
CHP class, so it cannot track — that is a known representation boundary, not a
new defect, and C1 excludes CT_CHP by construction.)*

---

## §4 — THE MECHANISM, AND WHY IT HAS NEVER BEEN ADJUDICATED ON ITS OWN TERMS

CAISO's `CT_PEAKER` offer band on the keeper, from its own `run_config.json`:

```
committed 1.35    <-- fitted        phys_committed 0.991   <-- MEASURED
econ_low  1.145                     phys_econ_low  0.686   <-- MEASURED
econ_high 1.166                     phys_econ_high 0.710   <-- MEASURED
peak      1.166                     phys_peak      1.0
```

The min-load band is priced **+36 % above the class's own measured physical
min-load burn** and **+16 % above its measured bid** (1.166, the CT bucket's
`caiso_offer_curve_measured.json` value). Under `gas_offer_net_revenue_margin`
that markup becomes a fuel-invariant margin of
`(1.35 − 0.991) × 10.862 MMBtu/MWh × 4.796 $/MMBtu ≈ **$18.7/MWh**` on the
committed band, with a further ~$24/MWh across the econ ramp
(`1.145 − 0.686`). A CAISO peaker is therefore offered at roughly **cost plus
$19–24/MWh in every band** — a start-cost hurdle large enough to hold it out of
the merit order, which is what the 2.5 % → 0.4 % capacity factor is.

**Why this is a NEW object and not a re-litigation of Lever A.** caiso-238 graded
the five live `committed` bands **F4 — refused on rule**, under the adjudicated
Lever-A / rule-19 lesson, and caiso-231 applied that refusal uniformly. But Lever
A adjudicated the **opposite pathology**: a committed band sitting *below* cost
(CC_REGULAR 0.90 × avg HR, priced ~$1.2/MWh under true marginal cost and below
its own `econ_low`) which emulated commitment and flooded cheap CC around the
clock. The refusal's stated ground is *"min-load self-commitment conduct belongs
to unit commitment, not the P1 offer"* — a reason to not price commitment
**cheaply** into the offer. CAISO's `CT_PEAKER` committed band is **1.36× its own
measured physical basis**, i.e. an unidentified hurdle in the other direction,
and its consequence is a measured 66–90 % volume miss. **That specific claim has
never been put, and the DO-NOT-REDO entries all concern arming the measured
*bid* (1.166) — a different object from the measured *physical* basis (0.991),
exactly the distinction caiso-239 drew and acted on.**

---

## §5 — DIRECTION, DISCLOSED

Unusually, the structurally-faithful repair here is **favourable** to the sole
failing gate. Lowering CT_PEAKER's committed band toward its measured basis would
(a) raise CT_PEAKER volume toward the actual — a C1 improvement on a class
currently missing by 66–90 %; and (b) put a cheaper rung into the evening merit
order, which pushes C3a **down** in the hours it is over. Per rule 1
`[R-STRUCT]` that is **not** an argument for it — it is disclosed so a future
session cannot present it as a C3a lever. The object is a rule-14
`[R-ACCURATE]` / rule-21 `[R-DOF]` grounding of a fitted scalar against its own
measured counterpart, and it must be argued and gated as one.

---

## §6 — WHAT SHOULD AND SHOULD NOT BE CONCLUDED

**Should:**
1. **Never benchmark CAISO gas against EIA-930's CISO NG cell.** It is formally
   corrupt from 2023 (`EIA930_NG_CORRUPT_ONSET`), folds ~13 TWh/yr of
   geothermal + biomass, and drifts +10.5 % → +21.1 % → +32.8 % against two
   records that agree with each other within 2.3 %.
2. **CT_PEAKER is the open CAISO gas defect** — measured, structural, uniform
   across zones and months, and worsening. It is the strongest un-adjudicated
   CAISO volume object on record.
3. **C1's widened bands do not gate it.** A −3.8 TWh miss on a class that is
   90 % absent passes both legs. Worth the owner's attention as a rubric
   question independent of CAISO.

**Should not:**
4. This does **not** mean the model's gas total is wrong by 27 TWh. It is wrong
   by 3–7 TWh against the valid benchmark, and CT_PEAKER is over half of it.
5. This is **not** a licence to arm the measured CT bid multiplier (1.166) —
   that remains the adjudicated Lever-A refusal. The object is the **physical**
   basis (0.991), and it needs its own charter, precommit and A/B.
