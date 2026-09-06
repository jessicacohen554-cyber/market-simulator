# PREREG ADDENDUM A — nyiso-208. **DECLARED POST-HOC.** Two physically-motivated construction variants, committed BEFORE they are run

**This addendum is POST-HOC and is labelled so everywhere it is cited.** It was written *after*
M1–M6 were read, and it exists only because M1 landed on the pre-registered **VERDICT U
(UNIDENTIFIED)** branch. It is committed and pushed **before the checks it declares are executed**,
for the reason `PREREG-nyiso207` addendum §A and `PREREG-nyiso206` addendum §B exist: a search run
after seeing a miss is exactly the kind that finds what it is looking for, so its scope, its
thresholds and its reporting rule are fixed in advance and in public.

## A.1 Why the search is worth running at all

The pre-registered result is that the Capital_Hudson hot-limb slope measures **0.0502/°C** against a
frozen **0.0246/°C** — a factor of **2.04** — while **all three control slopes reproduce to four
decimal places** and **no span in the M5 search comes within 0.018 of the frozen value**. That is
verdict **U**, and it stands whatever this addendum finds.

What it changes for the owner is the *strength* of U. "Unidentified, one construction tried" and
"unidentified, every plausible construction ruled out" are different cards. The declared POST-HOC
diagnostic in the main probe supplies the motive: CH's when-available daily CF is **not a
well-behaved regressand** — 60.4 % of days are exactly 0, 2.28 % exceed 1.0, and the maximum is
**4.63**, because the outage derate reaches **99.64 %** of CH hours and drives the `avail`
denominator toward zero while metered output continues. An OLS slope on that population has heavy
leverage from a small number of physically-impossible readings.

## A.2 The two variants, and nothing else

Both are motivated by the **1.0 physical bound the model's own NYC cap knot already invokes**
(*"clamped at the 1.0 physical bound"*, CSV row 8): a fleet cannot generate above its available
capacity, so a when-available CF above 1.0 is a derate artifact, not conduct.

- **A1 — CF clipped at 1.0**, shipped `avail` basis, pooled 2023–2025. One change from the shipped
  construction.
- **A2 — CF clipped at 1.0 on the nameplate basis** (M4's denominator + A1's clip). Two changes.

**No third variant will be tried**, and no other span, window, quantile, estimator or fleet subset
will be searched. The out-of-training extracts (`NY_2019/2020/2021/2022`) stay **unread**, as PREREG
§7 binds — a pre-2023 identification span therefore remains an **untested hypothesis** and will be
named as such on the card rather than resolved here.

## A.3 Prediction, declared before running

**A1 will be LOWER than 0.0502** — i.e. clipping moves toward the frozen value — because CH's fleet
runs hardest on hot days, so the CF > 1 artefacts should sit disproportionately on the hot side of
the regression and carry the slope upward. **I do not predict it reaches 0.0246.**

## A.4 Reporting rule — binding

1. A hit (`|slope − 0.0246| ≤ 0.0010`) is reported as **"reproducible only under a variant the CSV
   prose does not name"** — never as identification of the shipped construction, which has already
   been measured and missed.
2. The multiple-comparison caveat **compounds**: these two comparisons are added to M5's five, so
   the census now carries **seven** comparisons against a ±0.0010 window. Any hit is reported with
   that count attached.
3. A miss on both is reported as **strengthening verdict U**.
4. **No coefficient is edited and no replacement value is proposed in either case**, exactly as
   PREREG §7 binds in every branch. `0.0502`, `0.0400` and whatever A1/A2 return are **measurements
   of the gap**, not candidate values.

---

*(nyiso-208 addendum A. Zero LP. Declared POST-HOC, committed before execution.)*
