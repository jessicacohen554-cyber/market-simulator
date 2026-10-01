# ADDENDUM miso-244 — **THE VERDICT IS `V-NOT-A-TIE`: THE CENT IS NOT A ROUNDING ARTIFACT AND NOT A CLAMP.** And **MY OWN LIVENESS GATE NAMED THE WRONG BUS** — disclosed and repaired here, **STRICTER**, before its numbers exist

**Governs:** `PREREG-miso244-diagnose-the-incumbent-ladder-cent-2026-09-08.md` §2.3 (the verdict's
sub-classification), §2.4 (the cause prediction) and **§3 (the liveness gate `L`)**.
**Pushed BEFORE `L` is computed. NO BAR IS MOVED. The one repair made is STRICTER than what it
replaces.** Machine record: `results/calibration/_miso244_incumbent_ladder_cent_phase0.json`;
evaluator `scripts/probes/_miso244_incumbent_ladder_cent_phase0.py`, whose bars are literals quoted
from the PREREG.

---

## 0. STATED FIRST, AGAINST INTEREST — three disclosures, and two of them cost this session something

### 0a. **MY PRE-REGISTERED SUB-CLASSIFIERS CAME BACK EMPTY.** The gap is `UNEXPLAINED`, not `CLAMP-TRANSCRIPTION`

PREREG §2.3 offered exactly two named sub-classes for a `V-NOT-A-TIE` verdict, and **the record
refuses both**:

* **D-4** — none of the three mismatching entries is a no-wash-clamped band. `is_clamped_export` is
  **`false`** for all three, and HEAD's `derive()` raised **zero clamp notes in any year** (the
  derive docstring's and `spec.py`'s own claim that the ordering *"holds naturally in all years"* is
  **confirmed**, not contradicted).
* **D-5** — the alternative clamp taken off the ROUNDED imports reproduces **none** of them:
  it yields **13.39 / 50.98 / 57.85** against committed **27.86 / 27.69 / 23.77**. Not close, and
  not the mechanism.

So the handoff's second candidate — *"a no-wash clamp that fired at derivation time and was
hand-transcribed"* — is **REFUTED**, and its first — *"a rounding artifact"* — is refuted by the
verdict statistic itself (§1). **What is left is the third, `real drift`, and this session cannot
name its cause without breaking its own §2.4 pre-commitment (§0b).** That is a weaker result than a
fully identified cause, and it is stated as such rather than dressed up.

### 0b. **§2.4 BINDS THIS SESSION AGAINST FINDING THE CAUSE, AND I AM HONOURING IT RATHER THAN READING AROUND IT**

PREREG §2.4 fixed, before any number existed: *"This is the ONLY alternative construction this
session will try … No second transformation is tried; searching transformations until one reproduces
would be the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids, applied to a derive instead of a
solve."* The clause was written for the `V-ARTIFACT` branch, but **its prohibition is unconditional
in form, so it binds here too.**

It would be easy, and wrong, to now re-run the derive under a different quantile convention, a
perturbed exceedance count, or a re-fetched source vintage until the committed table reappeared —
and to present whichever one worked as "the cause". **This session does not do that.** The cause is
handed forward as a named successor **with a pre-specifiable test** (§3), for a session that can
pre-register it cleanly. What that costs is stated plainly: **the drift is demonstrated but not
attributed.**

**One thing is nevertheless settled, and it is ARITHMETIC on D-1′'s own already-computed output, not
a new construction:** the three mismatches are **mutually inconsistent under any single quantile
convention in numpy's `h = q·(n−1)` family** (`linear`, `lower`, `higher`, `nearest`, `midpoint`).
Entries 1 and 2 both require the **lower** order statistic — `frac` **0.618** and **0.628** with
`x_lo`/`x_hi` exactly one cent apart, and committed **= round(x_lo, 2)** in both. Entry 3 **refutes
`lower`**: there `x_lo == x_hi == 23.760000` (a degenerate position, so **all five methods return
23.76**) while committed is **23.77**. **No uniform change of estimator explains both**, which
eliminates the "the code's convention changed" family and leaves the **sample** as what moved.

### 0c. **MY OWN LIVENESS GATE `L` NAMED THE WRONG BUS.** Found before it ran, repaired here, and the repair is STRICTER

PREREG §3 specifies `L` *"on the model basis (the keeper's committed `MISO_external` P1 price from
`hourly/system_<year>.parquet`)"*. **That is not the bus the South seam's bands clear against.** The
keeper arms `miso_south_seam_split=True`, and
`interchange/miso.py::split_miso_south_external_node` re-homes the MISO-South border link onto its
own zone, stating in its own docstring: *"The South seam's reference-price bands must be hosted in
the new zone by `build_reference_price_node` (`zone_overrides`)."* The keeper's committed sidecar
carries **both** buses — `system_2023.parquet` `zone` ∈ {…, `MISO_external`, `MISO_external_South`},
8,760 P1 rows each — so a gate written on `MISO_external` alone would have measured the footprint of
a South band move **on a bus that band is not hosted on**.

**This is a defect in this session's own gate specification, found before the gate ran, and it is
disclosed rather than quietly satisfied** — the miso-243 §0b template.

> **`L′` — THE REPAIR, declared here before any of its numbers exist.** `L` and `Δq̂` are computed
> on **`MISO_external_South`** (the bus the moving bands are hosted on) **AND** on `MISO_external`
> (the bus the PREREG named), and **the gate is the MAXIMUM over the two buses.**
>
> **Every bar is unchanged and untouched:** the correction is measured **INERT**, and **no screen
> solve is authorized**, iff `max_bus max_year L ≤ 0.001` **AND** `max_bus max_year |Δq̂| ≤ 5 MW`.
> The screen-year rule (`argmax_year L`, ties to the earliest) is unchanged.

**Taking the maximum over two buses is strictly harder to pass than either bus alone**, so the
repair can only make the gate stop the session more readily, never less — the direction PREREG §1's
disclosure duty requires. **No bar is moved, no statistic is redefined, and the disposition attached
to `L` in PREREG §3 is untouched.**

---

## 1. THE VERDICT, and the six provenance legs plus the identity leg that all had to pass first

**Every GATED leg passes** (`FAILED_LEGS: []`), so the instrument reproduces the record it is
diagnosing before it adjudicates anything:

| leg | what it reproduces, in the predecessor's own metric | bar | **measured** |
|---|---|---|---|
| **G-RAW** | this probe's own raw replication of `_derive_one` satisfies `round(raw,2) == derive()`, all 192 entries | exact | **0.0** |
| **G-P2** | miso-243's P-2 per-seam `max\|committed − derive\|`, all 12 cells | exact at 2 dp | **exact** |
| **G-SPP** | the committed per-year SPP hourly ladder reproduces from HEAD's repaired derive, 48 entries | exactly 0.0 | **0.0** |
| **G-POOL** | the committed POOLED forward SPP ladder reproduces, 16 entries | exactly 0.0 | **0.0** |
| **G-DOC** | the derive's own docstring `corr(measured SPP flow, MISO DA − SPP hub DA)` = +0.041 / −0.020 / +0.050 | ≤ 0.002 | **0.0409 / −0.0200 / 0.0503** |
| **G-ROW** | 8,760 rows/year, hub join row-count preserved, `n(R_D)` = 8,754 / 8,757 / 8,757 | exact | **exact** |
| **I-1** *(identity, on the COMMITTED table)* | `P(flow > mid_k)` inside `[P(da > c_k) − 0.002, P(da ≥ c_k) + 0.002]`, all 192 both sides | 0 excess | **0.0, every seam, every year** |

**I-1 had the power to void this session's whole framing** — a committed table that failed it did not
come from this construction on this row set — **and it passes exactly.** The committed table *is* the
output of this estimator on this row set, everywhere. That is what makes the three cents meaningful
rather than noise.

**THE VERDICT (PREREG §2.3, rule fixed before any number existed):**

| | |
|---|---:|
| entries compared | **192** |
| mismatching | **3** |
| **`t_max`** (how far past the half-cent boundary the current estimate sits) | **0.0049998** |
| bar for `V-ARTIFACT` | ≤ **1e-4** |
| **VERDICT** | **`V-NOT-A-TIE`** |

`t_max` misses the tie bar by a factor of **50**. **The committed values are not roundings of the
current estimates**, and the three entries — located here for the first time, since miso-243
published only per-seam maxima — are:

| year | seam | side | band | committed | **raw at HEAD** | rounds to | `t` |
|---|---|---|---|---:|---:|---:|---:|
| 2023 | **PJM** | import | 5 | 27.86 | 27.8661823 | 27.87 | 0.00118 |
| 2023 | **South** | export | 4 | 27.69 | 27.6962804 | 27.70 | 0.00128 |
| 2024 | **South** | export | 5 | 23.77 | 23.7600002 | 23.76 | **0.00500** |

**The directions are MIXED** (committed is one cent LOW at the first two, one cent HIGH at the
third), which is itself evidence against any systematic construction difference and for §0b's
elimination.

**REPORTED, and it does not move the verdict (PREREG §2.4).** The cause prediction's antecedent
(`V-ARTIFACT`) is **false**, so no falsification is owed; the measurement was made anyway and is
published: snapping `da` to exact cents in float64 **does not** reproduce the committed table
(`max_abs_delta` 0.01 / 0.01 / 0.00). The `da` column is stored **float32** (43,800 rows; only
**4.7 %** of values are exactly 2-dp in float64), which is why the tie hypothesis was worth testing —
and it is now **refuted on the numbers**, not on a hunch.

---

## 2. WHAT IS GATED FROM HERE, AND WHAT IS REPORTED — unchanged from PREREG §1 except for §0c's bus

**GATED**: `L′` (§0c) alone. Its disposition is PREREG §3's, verbatim and unamended.
**REPORTED, NEVER GATED**: everything in §1 above, D-3/D-4/D-5/D-1′/D-1″/D-6, the F6 liveness scope,
the per-band moves below, and every band or criterion value of the keeper.

**THE BANDS THAT ACTUALLY MOVE, and the F6 scope they move inside.** Read from the keeper's
committed `run_config.json` (`miso_seam_measured_ladder` / `…neighbour_anchored_ladder` /
`…neighbour_hourly_ladder` / `…neighbour_hourly_spp` all `True`) and from
`inject_miso_seam_ladder_prices`, which overlays the PJM-hourly then the SPP-hourly ladder **on top
of** the incumbent table as alternatives that displace and never stack: **only the `South` and
`Manitoba` rows of `MISO_SEAM_LADDER_BY_YEAR` are priced into this keeper's LP.** So

* **PJM 2023 import band 5 is INERT on this keeper** (displaced by the hourly overlay) — the
  handoff's claim, verified here independently from the committed config and the injection code;
* **Manitoba has no mismatch in any year**;
* the live moves are exactly two, both on the **export** side, so `Δn̄_i ≡ 0` and
  `Δq̂ = −375 MW × Δn̄_e` (South's own step, `3000 / 8`):
  * **2023 South export band 4: 27.69 → 27.70** (easier to clear ⇒ `n_e` can only rise ⇒ `Δq̂ ≤ 0`);
  * **2024 South export band 5: 23.77 → 23.76** (harder to clear ⇒ `n_e` can only fall ⇒ `Δq̂ ≥ 0`);
  * **2025: nothing moves at all.**

Band-count membership is evaluated in each side's own operand form — an import band `k` is in merit
iff `p(t) ≥ imp_k`, an export band iff `p(t) ≤ exp_k` — with `p(t)` the bus's committed **P1** price.
**Zero scored criterion, zero band comparison and zero residual enters `L′`.**

---

## 3. What this addendum hands forward, and what it does NOT do

1. **NAMED SUCCESSOR, with the test it should pre-register.** The drift is **demonstrated and
   unattributed**. §0b's elimination leaves the **sample** as what moved, and the successor's
   hypothesis is therefore pre-specifiable rather than searched: *if the committed table came from
   this estimator on a marginally different sample, each mismatching entry's committed value is
   reachable by perturbing that entry's own integer exceedance/depth COUNT by at most ±1 hour out of
   8,760, holding estimator and price series fixed; a single entry needing more REFUTES it.* **This
   session does not run it** (§0b) and does not claim its outcome.
2. **THE MISSING RULE-23 REPRODUCTION PIN (PREREG F5) is now the more consequential half of the
   finding.** `MISO_SEAM_LADDER_BY_YEAR` is the only MISO seam ladder with no test that re-runs its
   derive and compares; the SPP-hourly pin next to it (`atol=0.005`) would have caught this on the
   day it appeared. Whether it is added here is decided after `L′`, because the construction of such
   a pin depends on whether the table is reconciled first.
3. **It moves no bar**, changes no decision rule, adds no tolerance, and applies no repair to any
   committed table.
4. **It solves nothing and authorizes no LP.** PREREG §3's authorization remains conditional on
   `L′`, and `L′` is a STOP-only gate that can only refuse.
5. **Every number here is UN-TARGETABLE**, nothing is tuned or reconciled to a predecessor's value,
   and where a value agrees with one (G-P2, G-DOC, G-ROW) it is disclosed as **expected** — a
   deterministic estimator run twice on the same series — rather than presented as independent
   corroboration.
6. **MISO has no failing gate**, this session does not invent one, C3c is untouched, and nothing
   here trades a passing gate for anything.
