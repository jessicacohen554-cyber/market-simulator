# FINDING (pjm-h2): phase 0 KILLS the card's arm — §4's lead is arithmetically wrong,
# and the real basis defect is one that has not landed yet

**Session** `pjm-h2` · **ISO** PJM · **Date** 2026-09-12 · **Base** `origin/main` @ `9ae27cd7`
**ZERO LP.** The parent never solved and no shard was launched (rule 32 `[R-SHARD]` (a)).
Committed artifacts + measured sources only. Nothing armed, nothing registered, no shared
code changed, no `ScenarioConfig` field added.
**PJM keeper UNCHANGED and re-scored before AND after: `2026-09-11-pjm-d4-4-gasoutage`,
CALIBRATED, grade 8/8, zero caveats, zero fails, empty determination basis.**

---

## 1. RESULT

> **There is no admissible coal-vs-gas merit lever to screen, and two of the card's three
> target years are not anomalous once put on the grid basis.**
>
> 1. **`FINDING-pjm-holdout-phase0` §4's "live lead" is REFUTED on arithmetic.**
>    `reconcile_vintage_classes` does **not** fire in PJM 2021 or 2022 — nor in any PJM year
>    2020-2025. §4 compared the 923 fossil total against the **undeflated** EIA-930 gas+coal
>    cell; the code deflates that target by the geo/biomass fold-in first. With the deflation
>    the ratios read **0.9713 / 0.9721**, both **inside** the 0.97 deadband. All six committed
>    PJM years are on **ONE** construction, not two.
> 2. **But the years §4 named are right, for a reason that did not exist when it was written.**
>    Today's `gov-hydro-seam-1` PS→`OTHER` repair (`26f8508b`, merged) drops PJM's `OTHER` by
>    1.78-2.67 TWh/yr, which shrinks the fold-in, which raises the reconcile target, which
>    pushes **PJM 2021 and 2022 — and nothing else, in any ISO — out of the deadband.** The
>    reconcile **will fire at PJM's next registration**, scaling every PJM fossil class by
>    **×1.0334 / ×1.0328** and removing **9.33 / 9.75 TWh** of the CC_REGULAR C1 residual.
> 3. **The merit-split refutation SURVIVES my basis finding**, because pjm-166's statistic
>    (coal share of coal+CC) is **exactly scale-invariant** under a uniform reconcile. Restoring
>    2020 — the one year pjm-166 omitted — does not produce a price signature either: the
>    model's coal-share error is **non-monotone** in the gas level.
> 4. **On the EIA-930 grid basis only 2020 is anomalous.** Held-out fossil surplus
>    **+29.6 / +8.6 / +16.3** TWh (2020/21/22) against an in-sample **+3.6 / +7.6 / +21.1**
>    (2023/24/25): 2021 and 2022 sit *inside* the in-sample range.

Rule 30(c): none of this downgrades PJM, which stays **CALIBRATED** on 2023-2025.

---

## 2. STEP 1 — THE BASIS SPLIT, QUANTIFIED PER CLASS

### 2.1 The reconcile never fired — measured, not argued

`post_sum == tgt` is the signature of a fired reconcile. It holds in **no** PJM year:

| yr | committed fossil Σ | 930 gas+coal | **fold-in** | **target** | ratio | fires? |
|---|---:|---:|---:|---:|---:|:--:|
| 2020 | 457.090 | 461.147 | 2.789 | 458.358 | 0.99723 | no |
| **2021** | 478.259 | 495.289 | **2.894** | **492.395** | **0.97129** | **no** |
| **2022** | 483.788 | 499.663 | **2.004** | **497.659** | **0.97213** | **no** |
| 2023 | 478.962 | 481.679 | 1.374 | 480.305 | 0.99720 | no |
| 2024 | 498.955 | 490.666 | 0.000 | 490.666 | 1.01689 | no |
| 2025 | 515.670 | 512.504 | 0.000 | 512.504 | 1.00618 | no |

§4's 0.9654 / 0.9680 are `Σ923 / (930 gas+coal)`. The code's test is
`Σ923 / (930 gas+coal − gas_foldin_deflation)` (`render_calibration_html:1855`,
`benchmark_semantics.gas_foldin_deflation`). **The margin is 0.64 TWh (2021) and 1.06 TWh
(2022) — 0.13 % and 0.22 %.** That is why the year-shape §4 saw is real and its mechanism is not.

### 2.2 Per-class split of the residual the card asked for

`res 930` = residual against the fold-in-deflated 930 basis (i.e. what survives a basis
correction). Band 8.0 TWh.

| yr | class | model | act (923) | act (930) | **res 923** | **res 930** | basis share | gate |
|---|---|---:|---:|---:|---:|---:|---:|:--|
| **2020** | **COAL_BIT** | 153.97 | 131.14 | 131.50 | **+22.83** | **+22.47** | **1.6 %** | FAIL→FAIL |
| 2020 | CC_REGULAR | 290.56 | 283.00 | 283.79 | +7.56 | +6.77 | 10 % | PASS |
| **2021** | **CC_REGULAR** | 305.51 | 279.20 | 287.45 | **+26.31** | **+18.06** | **31 %** | FAIL→FAIL |
| 2021 | COAL_BIT | 152.07 | 150.74 | 155.20 | +1.33 | **−3.12** | — (sign flip) | PASS |
| **2022** | **CC_REGULAR** | 319.69 | 297.13 | 305.65 | **+22.56** | **+14.04** | **38 %** | FAIL→FAIL |
| 2022 | COAL_BIT | 143.63 | 136.11 | 140.02 | +7.52 | +3.61 | 52 % | PASS |

**All-fossil, six years:**

| yr | model | 923 actual | 930 target | model−923 | **basis (930−923)** | **survives (model−930)** | basis share |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 490.79 | 457.09 | 458.36 | +33.70 | **+1.27** | **+32.43** | **4 %** |
| 2021 | 503.93 | 478.26 | 492.39 | +25.67 | **+14.14** | **+11.53** | **55 %** |
| 2022 | 515.96 | 483.79 | 497.66 | +32.17 | **+13.87** | **+18.30** | **43 %** |
| 2023 | 485.30 | 478.96 | 480.31 | +6.34 | +1.34 | +5.00 | 21 % |
| 2024 | 498.26 | 498.95 | 490.67 | −0.69 | −8.29 | +7.59 | n/a |
| 2025 | 533.58 | 515.67 | 512.50 | +17.91 | −3.17 | +21.08 | −18 % |

**The answer the card asked for:** **55 % of 2021's and 43 % of 2022's all-fossil C1 residual
is the 923-vs-930 basis gap; 4 % of 2020's is.** Per class, the basis carries **31 % / 38 %**
of the two CC_REGULAR failures and **1.6 %** of 2020's COAL_BIT failure. **No C1 cell flips** —
+22.47 / +18.06 / +14.04 against an 8 TWh band are all still FAIL, so what survives the basis
correction is real model error and attributing it to the model is legitimate.

---

## 3. THE DEFECT THAT HAS NOT LANDED YET — and it is PJM-only

`gov-hydro-seam-1` (`26f8508b`, merged today) does two things. Its §5 published the first —
`hydro` moves onto the conventional-only 923 `HY` population. **The second moves `OTHER`**, and
that is the one with a gate behind it: `classify_plant` now routes WAT/**PS** to `OTHER`, and
EIA-923 books PS as **net** generation, which is **negative**.

Re-derived at HEAD and at `26f8508b~1` (control). **The control reproduces the committed
`classFull` exactly for every class carrying no BTM subtrahend, and reproduces §5's published
hydro deltas to 4 dp** — so the arm-minus-control difference is attributable to this change alone:

| yr | `OTHER` cmt → HEAD | fold-in cmt → HEAD | target cmt → HEAD | ratio cmt → HEAD | **reconcile** |
|---|---|---|---|---|:--|
| 2020 | 7.600 → 5.816 | 2.789 → 1.006 | 458.36 → 460.14 | 0.99723 → 0.99337 | no |
| **2021** | 7.543 → **5.693** | 2.894 → **1.044** | 492.39 → **494.25** | 0.97129 → **0.96766** | **FIRES ×1.03343** |
| **2022** | 6.993 → **4.614** | 2.004 → **0.000** | 497.66 → **499.66** | 0.97213 → **0.96823** | **FIRES ×1.03281** |
| 2023 | 7.225 → 4.700 | 1.374 → 0.000 | 480.31 → 481.68 | 0.99720 → 0.99436 | no |
| 2024 | 7.321 → 4.648 | 0.000 → 0.000 | — | 1.01689 | no |
| 2025 | 4.778 → 2.118 | 0.000 → 0.000 | — | 1.00618 | no |

**Blast radius, swept over all 42 committed bench parts in all seven ISOs: exactly two
ISO-years — PJM 2021 and PJM 2022.** No other ISO-year changes its reconcile decision (MISO,
NEISO, NYISO, CAISO, SPP all move ratio by <0.009 and none crosses the band).

### 3.1 What it does to the scored numbers

Re-scored all 8 registered PJM runs against HEAD-basis bench parts (repaired `hydro` **and**
`OTHER`, then reconciled):

* **DETERMINATIONS: zero flips.** Keeper `CALIBRATED` → `CALIBRATED` (grade 8 → 8, zero status
  flips, 10 cosmetic share_pp/`SKIPPED`-diagnostic records move). Touchpoint `NOT-YET` →
  `NOT-YET` (grade 4 → 4).
* **MAGNITUDES move materially** on the touchpoint (26 records):

| record | before | after |
|---|---|---|
| C1 CC_REGULAR 2021 | **+26.31 TWh** FAIL | **+16.98 TWh** FAIL |
| C1 CC_REGULAR 2022 | **+22.56 TWh** FAIL | **+12.81 TWh** FAIL |
| C1 COAL_BIT 2021 | +1.33 TWh | **−3.71 TWh** (sign flip) |
| C1 COAL_BIT 2022 | +7.52 TWh | +3.05 TWh |
| C1 COAL_BIT 2020 | +22.83 TWh FAIL | **+22.83 TWh FAIL (unmoved)** |
| C8 hydro 2020/2021 | PASS | SKIPPED (now immaterial, 1.3 % < 2 % floor) |

### 3.2 The `gov-hydro-seam-1` gate-neutrality claim: headline holds, magnitudes do not

That session measured "0 differences across all 47 registered runs" by substituting **only the
repaired `hydro`** into the bench parts, on the stated reasoning that "`reconcile_vintage_classes`
scales **fossil** classes only". That is true of what the reconcile *scales* — but the reconcile's
**trigger** reads `classFull['OTHER']` through `gas_foldin_deflation`, and the PS→`OTHER` half of
its own change moves `OTHER`. **Its conclusion survives** (I verified: no PJM determination flips),
but its magnitudes claim does not — up to 9.75 TWh of a scored C1 residual moves. Reported, not
absorbed; this is a correction to an existing measurement, not a new defect in the change.

### 3.3 ESCALATED — the construction question I will not settle

Is PS-net-inclusive `OTHER` the right operand for `gas_foldin_deflation`? It compares
`923 OTHER + biomass` against EIA-930 "Other Fuel Sources". **930's Other carries no pumped
storage** (PJM folds PS into `NG: WAT` — `EIA930_PS_FOLDED_INTO_WAT`), so subtracting a negative
PS net from the 923 side compares two different populations. Two defensible readings:

* **(a) HEAD is right.** `OTHER` is the class; the reconcile was being suppressed by the
  `classify_plant` defect, and firing it puts a genuinely 3.3 %-short 923 vintage on the grid
  basis the model is scored on — rule 14 `[R-ACCURATE]`.
* **(b) HEAD is wrong here.** The fold-in wants *generation by other fuels*, so it should read
  `OTHER` **excluding** PS — which is the committed value, and the reconcile correctly does not fire.

`gas_foldin_deflation` and `classify_plant` are **shared ISO-agnostic code** and a PJM lane does
not make that call (rule 25 `[R-ISO-SCOPE]`; the pjm-h1 precedent escalated exactly this class of
question). **Owner's call.** It is worth 9.3-9.8 TWh of PJM's held-out C1 residual and **no
determination anywhere.**

---

## 4. STEP 2 — WHY THERE IS NO ADMISSIBLE ARM

### 4.1 The merit-split cell is `R`, and my basis finding cannot re-open it

pjm-166 adjudicated the coal-vs-CC merit-order-position object REFUTED
(`FINDING-pjm166-c1-object-phase0-2026-09-06.md` §1.1-1.3). Its statistic is **coal share of
(coal + CC_REGULAR)**, and a uniform reconcile scales numerator and denominator **identically** —
so **the share is exactly invariant** to everything in §2 and §3. My basis finding is new evidence
about the *volumes*; it is provably **no** evidence about the *split*. Rule 28(a) holds: the cell
stays `R`.

### 4.2 Restoring 2020 — the year pjm-166 omitted — does not produce a price signature

pjm-166 §1.2's sign test ran 2021-2025. 2020 is the cheapest-gas year of the six and was absent.
Restored, ranked by the EIA electric-power gas level:

| gas $/MMBtu | yr | model coal share | actual | **Δ pp** |
|---:|---|---:|---:|---:|
| **1.94** | **2020** | 35.77 % | 32.89 % | **+2.88** |
| 2.38 | 2024 | 25.19 % | 25.58 % | −0.39 |
| 2.49 | 2023 | 25.67 % | 25.67 % | +0.00 |
| 3.59 | 2021 | 35.03 % | 37.18 % | −2.14 |
| 3.74 | 2025 | 30.48 % | 29.29 % | +1.18 |
| 6.47 | 2022 | 33.46 % | 33.95 % | −0.49 |

**Non-monotone.** 2025 (+1.18) and 2021 (−2.14) sit 0.15 $/MMBtu apart with opposite-signed,
large errors. A merit-position error does not look like this. 2020 is an outlier in magnitude,
not the top of a trend — and an arm picked because 2020's Δ is the largest would be picking on
the residual, which rules 1 `[R-STRUCT]` and 29 `[R-SCREEN]` forbid.

### 4.3 On the grid basis only 2020 is anomalous — and it is additive, not a reordering

Model vs the EIA-930 series (the authority C2 and the LP are on):

| yr | fossil Δ | nuclear Δ | hydro Δ | oil Δ | **total gen vs 930 net_gen** | **DA-virtual net** |
|---|---:|---:|---:|---:|---:|---:|
| **2020** | **+29.64** | +2.74 | −5.87 | −2.01 | **+10.84** | −1.88 |
| 2021 | +8.64 | −0.80 | −6.26 | −2.29 | n/a (corrupt series, §5) | **−9.97** |
| 2022 | +16.30 | −0.27 | −7.03 | −2.78 | **+7.51** | **−12.14** |
| 2023 | +3.62 | −1.79 | −6.56 | −2.71 | −7.48 | +1.99 |
| 2024 | +7.59 | −1.65 | −7.00 | −4.14 | −8.29 | +2.42 |
| 2025 | +21.08 | −1.52 | −7.04 | −5.31 | −0.82 | −2.41 |

The held-out years generate **~15 TWh more** relative to the meter than the in-sample years, and
the **DA-virtual net cleared position swings ~12-14 TWh** across the tier boundary — **pjm-166's
successor, now corroborated on a third year and sized.** 2020 additionally carries a **+8.44 TWh
(+1.11 %) demand over-statement** and a **−2.85 TWh** export shortfall, which together close its
+10.84 TWh generation excess. The hydro Δ (−5.9 to −7.0, every year) is the `NG: WAT` PS fold and
is an accounting artifact, not dispatch (pjm-143 / pjm-h1).

**Successor, unchanged and not mine to open:** the DA-virtual layer's net cleared position — cell
adjudicated `K`, escalated to the owner inside the closed price-formation frontier. Plus, for 2020
only, the demand over-statement.

---

## 5. THE CORRUPT EIA-930 2021 `net_gen` — VERIFIED, AND THE ANSWER IS "LIVE PATH, INERT EFFECT"

The card asked this be verified rather than assumed. Both halves measured:

* **The scorer never reads it.** `net_gen` appears **zero** times in `scripts/calibration_verdict.py`;
  `_gen_totals` (the C1 share denominator and the C2 roll-up) sums `classFull` and `gmModel` only.
  **C2 is cleared.**
* **The benchmark builder DOES read it, and it IS corrupted in the live path:**

| yr | 930 `net_gen` TWh | Σ fuel series | `_vintage_completeness` |
|---|---:|---:|---:|
| 2020 | 801.19 | 782.73 | 0.9926 |
| **2021** | **4,939.01** | 829.30 | **0.1654** ← corrupt |
| 2022 | 841.84 | 838.33 | 0.9831 |

`_vintage_completeness(2021, PJM)` reads **0.1654** against a true ~0.98, so **both** consumers
(`_reconciled_mustrun_class`, `_backfill_renewables_eia930`'s biomass carry) **enter** their
`< 0.90` branch. They do not fire, because each guards with `est > annual` and
`est = prior × 0.1654` is far below:

| yr | class | annual | prior | est | carry |
|---|---|---:|---:|---:|:--|
| 2021 | biomass | 5.957 | 5.907 | **0.977** | blocked |
| 2021 | OTHER | 7.543 | 7.600 | **1.257** | blocked |

**Verdict: inert in effect, but it is a latent trap rather than a safe series** — the guard holds
only because the corruption is ~6×. A milder one (completeness ≈ 0.85) would fire and replace the
class total. 2020's own margin is thin (`est` 7.209 vs `annual` 7.600). **Escalated for repair of
the committed extract; not repaired here** (shared data artifact, no PJM-lane authority).

---

## 6. WHAT I DID NOT DO, AND WHY

* **No LP, no shard, no screen.** Rule 29 `[R-SCREEN]` clause 0: the zero-LP phase kills arms, and
  it killed this one. A screen gate on a 2021/2022 C1 number would have been gated on a quantity
  about to move 9-10 TWh for reasons that are not the model.
* **No benchmark code touched** (§3.3, rule 25).
* **No mechanism tested**, so **no matrix cell verdict moves** (rule 28). The PJM shard's
  `hydro_level_923_hy` cell is re-stamped with §3's correction to its own evidence line.
* **G-DRIFT not re-run**: moot with no solve. PJM's form-4 baseline is already established
  (pjm-d4-4: the keeper's 833-field `cache_key()` is identical at its `git_sha` and at HEAD).
* **The 2021/2022 basis question is NOT settled by me** — it is escalated (§3.3).

## 7. RULES

Rule 29 `[R-SCREEN]` clause 0 (zero-LP phase 0 first; it killed the arm — the pre-registered good
outcome). Rule 28 `[R-MECH-MATRIX]` (a) (no re-test of an `R` cell; §4.1 shows the new evidence is
provably orthogonal to the adjudicated statistic). Rule 30(c) (held-out years never downgrade PJM).
Rule 31 `[R-RETAIN]` (nothing solved, nothing to retain). Rule 32 `[R-SHARD]` (a) (the parent never
solved). Rule 25 `[R-ISO-SCOPE]` (§3.3 escalated, not executed).
