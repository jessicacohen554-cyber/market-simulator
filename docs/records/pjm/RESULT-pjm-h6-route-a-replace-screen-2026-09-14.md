# RESULT (pjm-h6) — Route A REPLACE is KILLED AT THE SCREEN by its own pre-registered G-4

**Session** `pjm-h6` · **ISO** PJM · **Date** 2026-09-14 · **Base** `origin/main` @ `46c5702d`
**Screen** PJM 2023, A/B in ONE shard at one pinned sha. Parent ran no LP (rule 32 `[R-SHARD]` (a)).
**PJM keeper `2026-09-11-pjm-d4-4-gasoutage`: CALIBRATED, 8/8, zero caveats — UNTOUCHED.**
Charter `docs/PRECOMMIT-pjm-h5-coal-committed-charter-2026-09-13.md`; build + gates
`docs/PRECOMMIT-pjm-h6-route-a-replace-build-2026-09-14.md`.

---

## 1. RESULT

> **The arm holds its own identity perfectly and fails the market. G-1, G-2 and G-3 PASS;
> G-4 FAILS.** The pre-registered screen gate is STOP-only, so the arm does not reach the
> full span and the remaining five years are **never spent** (rule 29 `[R-SCREEN]` (2)).
>
> | gate | verdict | evidence |
> |---|---|---|
> | G-1 confinement | **PASS** | only `committed` rows move, six years, phase 0 |
> | G-2 identity | **PASS** | effective basis = measured to 1e-13, six years, three legs |
> | G-3 sign/magnitude | **PASS** | COAL_BIT falls as pre-registered; displacement ledger balances to −0.021 TWh |
> | **G-4 no load-bearing flip** | **FAIL** | **CC_REGULAR +2.79 → +13.48 TWh, PASS → FAIL** |
>
> **C1 goes 16/16 → 14/16.** The target class overshoots *through* zero by three times the
> band (COAL_BIT +2.13 → **−24.19** TWh), and the largest class in the system follows it out
> the other side. Price degrades with it: the control's annual mean is **+0.37 $/MWh** against
> the RT actual, the arm's is **+2.06**.

## 2. THE CONTROL REPRODUCES THE KEEPER — so the G-DRIFT question is answered empirically

The control leg exists because PRECOMMIT §3.1 could not classify `9398000d` (SOCO-15 COD ramp
at the LP unit's own grain) INERT for PJM at zero LP, which voided G-CTRL form 4. **Measured,
the drift is nil**: the control's 2023 COAL_BIT is **105.152 TWh** against the keeper's own
scored **105.125** — a gap of **0.027 TWh**, three orders of magnitude below the 8.00 TWh
band — and the control scores **C1 16/16 PASS**, which is the keeper's committed headline
(`C1 all 16/16 · free 12/12`) exactly.

So form 4 *would* have been valid, and the extra ~18 min of LP bought the certainty rather
than a correction. Recorded as the honest outcome of a conservative call, not as a saving.

## 3. THE C1 TABLE — PJM 2023, band ±8.00 TWh

Actuals are the committed HEAD bench (`frontend/data/backcast/bench/PJM/2023.json.gz`).

| class | actual | CONTROL | res | | ARM | res | | |
|---|---:|---:|---:|:--|---:|---:|:--|:--|
| **CC_REGULAR** | 325.670 | 328.456 | +2.79 | PASS | **339.154** | **+13.48** | **FAIL** | **← G-4 flip** |
| nuclear | 272.591 | 272.022 | −0.57 | PASS | 272.022 | −0.57 | PASS | |
| **COAL_BIT** | 103.026 | 105.152 | +2.13 | PASS | **78.834** | **−24.19** | **FAIL** | target |
| wind | 29.626 | 29.628 | +0.00 | PASS | 29.628 | +0.00 | PASS | |
| CT_PEAKER | 21.663 | 20.550 | −1.11 | PASS | 26.282 | +4.62 | PASS | |
| ST_GAS | 8.883 | 11.332 | +2.45 | PASS | 14.706 | +5.82 | PASS | |
| CC_CHP | 6.115 | 8.542 | +2.43 | PASS | 8.067 | +1.95 | PASS | |
| COAL_WC | 5.895 | 5.296 | −0.60 | PASS | 4.915 | −0.98 | PASS | |
| COAL_PRB | 3.550 | 3.053 | −0.50 | PASS | 3.388 | −0.16 | PASS | |
| ST_CHP | 2.198 | 0.997 | −1.20 | PASS | 1.029 | −1.17 | PASS | |
| CT_CHP | 1.875 | 1.901 | +0.03 | PASS | 1.275 | −0.60 | PASS | |
| *(solar, hydro, biomass, OTHER, oil unchanged or inert)* | | | | PASS | | | PASS | |
| | | | **16/16** | | | **14/16** | | |

**Price** (model annual mean vs the bench's own reference): actual RT **28.44** / RT load-wtd
**29.58**; control **28.806** / 29.436; arm **30.501** / 31.261. The control is near-exact and
the arm is **+2.06 $/MWh** long — reported, and not the reason for the kill.

## 4. THE DISPLACEMENT LEDGER — the response is coherent, which is what makes the kill credible

The arm is not misbehaving numerically. Energy balances to **−0.021 TWh** system-wide and every
MWh coal loses lands somewhere sensible in the merit order:

| out | TWh | | in | TWh |
|---|---:|---|---|---:|
| COAL_BIT | −26.32 | | CC_REGULAR | +10.70 |
| CT_CHP | −0.63 | | CT_PEAKER | +5.73 |
| CC_CHP | −0.48 | | ST_GAS | +3.37 |
| COAL_WC | −0.38 | | imports (less net export) | +2.84 |
| | | | VIRTUAL_INC | +2.76 |
| | | | VIRTUAL_DEC (less decrement) | +2.01 |
| | | | COAL_PRB | +0.34 |

**G-3 therefore PASSES**: the sign is the one pre-registered in charter §5, the magnitude is in
the range a +17.6561 $/MWh lift on 12,550 MW of unfloored min-load capacity implies, and there
is no unexplained sink. The mechanism does exactly what its own arithmetic said it would.

## 5. WHAT THIS ACTUALLY SHOWS — and why it is NOT "revert the accurate input"

Rule 14 `[R-ACCURATE]` names this situation precisely: *"If swapping a hand estimate for real
data makes the backcast worse, that is a signal that something else in the model is
miscalibrated and the estimate was silently compensating for it. Treat the worse fit as a
discovered bug: keep the accurate input, find and fix the real root cause."*

That is the correct reading here, and the screen has made the compensation visible rather than
refuting the measurement:

* **The measurement is not in doubt.** `avg_committed_p50` = 0.916 is PJM's own committed CAMPD
  artifact — the same file, the same column, that every registered `phys_committed` key
  reproduces byte for byte. G-2 proves the arm installs it exactly.
* **The registered 0.548 was therefore carrying something else.** 26.3 TWh — a quarter of PJM's
  coal generation — is the size of what it was carrying. A band-level parameter 40 % below its
  own measured physics, holding a quarter of a fuel's output in place, is a compensation, not a
  calibration.
* **The charter already named the most likely thing being compensated, and this lane is barred
  from touching it.** §9: the bituminous sigmoid's `gas_mid` is registered at **3.40**, matching
  neither its own derive script at HEAD (**7.08**) nor the model's own measured delivered coal
  (**4.58**); it inflates the passthrough in **every** year, and at 7.08 the curve would sit at
  its floor in four of six years — *"the centre's drift is where essentially all of the
  sigmoid's effect comes from."* REPLACE removes that mis-grounded centre from the **committed**
  band and leaves it on **econ/peak**. So the arm corrects the min-load block while the
  incremental bands above it keep riding an inflated curve — and coal's whole offer stack ends
  up too dear relative to gas. That is a coherent, testable root cause, and it sits inside the
  **owner-declared-closed pjm-142 frontier**, which is why this lane escalated it rather than
  settling it.

**The honest conclusion is not "0.548 is right".** It is: *the committed band's measured basis
is right, the incumbent value was compensating for the econ-band sigmoid's mis-grounded centre,
and the two cannot be fixed one at a time.*

## 6. THE PROMOTION JUDGMENT (rule 31 `[R-RETAIN]`) — asked and answered

**RECOMMENDATION: DO NOT PROMOTE.** Stated against the owner's 2026-09-14 ruling rather than
around it.

The ruling is *"if structural integrity improves but gates regress that **may** still be a
keeper"* — permissive, not mandatory, and it explicitly does **not** lower the bar for the
structural argument. Applied here:

* the structural gain is **real but narrow** — one band now sits at its measured basis;
* the cost is **not a gate regression at the margin** — it is the model's fuel mix moving
  decisively away from reality on the **two largest classes in the system**, 24 and 13 TWh
  outside an 8 TWh band, plus a price that was near-exact going +2.06 $/MWh long;
* and rule 1 `[R-STRUCT]`'s own first half does not end at "keep the mechanism" — it continues
  *"(then fix the actual root cause per #11)"*. §5 identifies that root cause. Promoting now
  would ship the broken residual and retire the diagnostic that produced it.

**Nothing is deleted** (rule 31). Both bundles are pushed and retrievable; the decision is the
owner's and this document changes nothing about that.

## 7. RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e))

Both bundles are **on `origin`**, complete with the per-plant layer a registration needs
(`dispatch/2023_P1.parquet`, `btm.parquet`, `system.parquet`, all seven `hourly/` sidecars):

```
branch  claude/pjm-h6-screen-2023
SHA     dadda81404cb36b5dff338c6660e224e083b7209
recover git checkout dadda81404cb36b5dff338c6660e224e083b7209 -- \
          results/calibration/pjm_h6_screen2023_ctl \
          results/calibration/pjm_h6_screen2023_arm
```

A promotion from this state costs **zero re-solves for 2023** and five further years (~90 min)
for the rest of PJM's registered span. The branch **stays** until the owner rules (rule 33
`[R-SHARD-ARCHIVE]` (f)(3)); the shard container is archived (bytes verified in the parent
first, per (a)).

## 8. WHAT WAS NOT DONE, AND WHY

* **The six-year span was NOT spent.** Rule 29 `[R-SCREEN]` (2): the full span runs only if the
  screen clears its pre-registered gate. It did not. ~90 min of LP saved, which is the outcome
  the screen exists to produce.
* **No keeper touched, nothing registered.** The screen bundles are throwaway probes (clause 2)
  and are never registered; every number this lane cites is in this document.
* **The `gas_mid` re-centring was NOT opened.** Still escalated, still inside the pjm-142 closed
  frontier — now with a measured 26.3 TWh reason to look at it.
* **Nothing deleted** (rule 31 `[R-RETAIN]`).

## 9. MATRIX (rule 28 `[R-MECH-MATRIX]` (b))

`committed_band_measured_basis` PJM cell **O → R**, with this document as the citation. Every
other ISO stays `U` (rule 25 — nothing transfers; a target ISO derives its own parameters from
its own market's artifact).

## 10. RULES

Rule 1 `[R-STRUCT]` (the gate is structural and STOP-only; the arm is judged on what the
mechanism does, and the residual never selected it) · rule 14 `[R-ACCURATE]` (§5 — the worse
fit is treated as a discovered bug, and the accurate input is not buried back inside an
inaccurate one) · rule 19 `[R-ONE-MECH]` (the two halves stayed one mechanism throughout) ·
rule 21 `[R-DOF]` (zero free parameters; nothing swept) · rule 29 `[R-SCREEN]` (the screen
killed the arm and the remaining years were never spent — the pre-registered good outcome) ·
rule 30(c) (no held-out year touches PJM's determination) · rule 31 `[R-RETAIN]` (nothing
deleted; the promotion question is put to the owner) · rule 32 `[R-SHARD]` (the parent ran no
LP) · rule 33 `[R-SHARD-ARCHIVE]` (fetched, checked out, verified, then archived; recovery by
full SHA) · rule 34 `[R-SHARD-PROMOTABLE]` (the shard pushed both bundles with their per-plant
layer).
