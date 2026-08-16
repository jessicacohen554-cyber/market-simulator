# FINDING — ercot-210 / CONDUCT-PHASE-0: the scarcity-conduct offer layer is **NOT-TRANSFERABLE**, and for storage the failure is **model-free**. Door D is the recorded floor.

> Status: RECORD — for the owner. Read-only measurement on committed corpora.
> **NO LP, no solve, no year solved or scored, no run registered, no
> `ScenarioConfig` field, no CLI flag, no mechanism-matrix cell or row edit, no
> keeper contact.** Executed under owner signature **X-1** against the
> pre-registered
> `docs/PRECOMMIT-ercot210-conduct-transfer-phase0-2026-08-16.md`, pushed before
> any delivery-2023 SCED row was read.
>
> Keeper at session start and end: **`2026-08-15-ercot204-rule26-delete`** —
> determination NOT-YET, fail set {C3a-2023, C3b-2023}, C3c the single ledgered
> CAVEAT ×3. Untouched by this session.

---

## 0. VERDICT

**NOT-TRANSFERABLE.** Under the pre-registered rule (precommit §7.1: PASS
requires T1 ∧ T2 ∧ T3 ∧ T4 ∧ T5), **all five gates fail**. Per §7.1 this session
therefore **charters nothing**, mints no matrix cell, and records **Door D (card
W wait-for-data, ~mid-2027) as the floor**, with the exhaustion proof extended
one model class up — from "the within-class mechanism space is exhausted" to
"the conduct class immediately above it is not identifiable from
forward-computable drivers at the grain the committed corpora support."

**But the verdict is not uniform across the object, and the split is the
finding.** The two classes card R names behave oppositely:

| | THERMAL top-of-stack | STORAGE |
|---|---|---|
| T4 within-regime transfer (2024 → 2025) | **6 / 6** admissible months in band | **1 / 6** |
| T5 model-free tie test | **0 of 4,501** tie-pairs exceed the band; max irreducible error **$25.49/MWh** | **1,111 of 1,168 (95.1 %)** exceed; max irreducible error **$2,487.50/MWh** |
| 2023 out-of-year headline | every month in band | **−51 % to −97 %** |

**Thermal top-of-stack conduct IS expressible as a function of forward-computable
drivers.** Storage conduct is not — and T5 proves that model-free: 95.1 % of
hour-pairs that are indistinguishable in driver space (all four scaled drivers
within τ = 0.05, same season flag) carry storage offer levels further apart than
the pass band, so **no function of these drivers whatsoever** can fit both
members. That is ercot-195 V0's own argument, re-run at hour grain instead of
inherited from seven annual points — and this time it returns a *class-split*
answer rather than a blanket one.

**Storage is the object.** ercot-161 measured that **0.91 of the 1.10 GW offered
≥ $500 at the top-100 gap hours was storage**. The class that transfers is the
one that was never forming the 2023 tail; the class that forms the tail is the
one that does not transfer.

---

## 1. WHAT WAS ASKED, AND WHAT WAS MEASURED

ASSESSMENT-ercot209 §3 Door A asked whether ERCOT scarcity-hour offer surfaces
are expressible as a function of forward-computable drivers such that a function
fit **only** on 2024/2025 60-day disclosures reproduces the 2023 scarcity-hour
surfaces **at matched tightness**.

Measured, exactly as pre-registered: one row per (delivery hour × class) over
above-LSL SCED2 offer segments capped at HASL (the ERCOT-154/161 population
discipline, ONTEST excluded, absolute $/MWh); responses `p50`, `p90`, `s500`;
drivers **quantity-only** (within-year PRC percentile, RTOLCAP percentile, AS
position, SOC/availability proxy, season). Fit on delivery-2024/2025 at tightness
≥ p90; transferred to delivery-2023 at tightness ≥ p98.

**Coverage achieved** (precommit §4's inventory, realised):

| year | hours requested | hours with offer rows | resources with HSL reference |
|---|---:|---:|---:|
| 2024 | 2,629 | **2,503** (95.2 %) | 738 |
| 2025 | 2,434 | **2,432** (99.9 %) | 833 |
| 2023 | 175 | **175** (100 %) | 657 |

The 126 missing 2024 hours are the **deliveries 2024-01-10..23** MIS gap the
precommit recorded in advance; no 2023 hour is lost. The restored corpus verified
**1,023 / 1,023 OK** against `SHA256SUMS.txt`, so these are the same bytes every
prior ERCOT lane read.

The §4 diagnostics were added to the probe *after* the verdict was computed. The
re-run with them present reproduces **`VERDICT`, T1, T2, T3, T4, T5, `coverage`
and the selected forms byte-identically** — checked, not asserted — so nothing in
this finding's interpretation section reaches back into a gate.

---

## 2. THE GATES, AT FULL MAGNITUDE

### 2.1 T5 — the model-free tie test. The decisive one.

A **τ-tied pair** is a (fit-year hour, 2023 hour) pair whose four scaled drivers
all agree within τ = 0.05 and whose season flag matches. For such a pair, any
function `f` of those drivers returns near-identical values, so its error on at
least one member is ≥ half the measured gap — an **irreducible error**, independent
of functional form, fitting method, or sample size.

| class | tie-pairs | exceeding T1's band | share | max irreducible error | verdict |
|---|---:|---:|---:|---:|---|
| THERMAL | 4,501 | **0** | 0.0 % | **$25.49/MWh** | **PASS** |
| STORAGE | 1,168 | **1,111** | **95.1 %** | **$2,487.50/MWh** | **FAIL** |

Storage hours that are *identical* in tightness, online capability, AS position
and availability carry median offer levels up to **$4,975/MWh apart**. No
conduct function on this driver set can reproduce both. This is not a statement
about the six candidate forms — it is a statement about the drivers.

### 2.2 T4 — the within-regime control. This is not a 2023-boundary effect.

Fit on 2024 alone, predict 2025 — both post-ECRS, same $5,000 SWCAP, one design
regime. If the object were merely confounded by the 2023 regime boundary, this
control would pass.

| class | admissible months | in band | relative errors |
|---|---:|---:|---|
| THERMAL | 6 | **6** | +0.7 % to +14.5 % |
| STORAGE | 6 | **1** | **−89.2 % to +471 %** |

Storage conduct does not transfer **one year forward inside a single regime**.
The ECRS/ORDC-vintage confound the precommit named up front is therefore *not*
the explanation for the storage failure — it is refuted as the explanation by
this control. (For thermal, the control passing is what licenses reading its
2023 pass as real rather than lucky.)

### 2.3 T1 / T2 — the out-of-year transfer, LOYO across 2023 months

STORAGE headline (`p50`, $/MWh), fit {2024 ∪ 2025} → 2023:

| month | hours | measured | predicted | rel err | in band |
|---|---:|---:|---:|---:|---|
| Jun | 2 | 5,000.00 | 831.57 | **−83.4 %** | no |
| Jul | 6 | 4,999.98 | 156.28 | **−96.9 %** | no |
| **Aug** | 9 | **3,361.12** | **752.97** | **−77.6 %** | **no** |
| **Sep** | 4 | **4,052.48** | **1,974.36** | **−51.3 %** | **no** |
| Dec | 1 | 271.81 | 348.95 | +28.4 % | yes |

THERMAL headline (`p90`, $/MWh) is in band in every month (measured $29.90–$75.00
against predicted $34.95–$37.01).

`s500` (T2) tells the same story: storage measured shares of 0.69–1.00 against
predicted 0.29–0.57 (Aug **−47.3 %**, outside band); thermal in band throughout,
though only because its measured shares are ~0.01 and the ±0.15 absolute floor
dominates — stated so the thermal pass is not over-read.

**T1 and T2 fail on their named-months clause**: the precommit required Aug-2023
**and** Sep-2023 both in band, and storage misses both.

### 2.4 T3 — non-degeneracy. Fails on measurement; but half of *how* it fails is my design's fault.

T3 asked whether the fitted function predicts a *higher* headline at the tightest
2 % than at the 40–60 % band, by ≥ 3×. It returns **0.219** (storage) and
**0.734** (thermal) — not merely flat but **inverted**.

**The inversion should not be read at face value, because the gate as I wrote it
is confounded.** The fit population is tightness ≥ p90; T3 evaluates the function
at tightness 0.40–0.60, **outside its own fit support**, through a logit link.
That is a defect in precommit §7's T3, authored by this session, and it is
reported rather than quietly restated.

**But the substantive question survives the confound, and T3 still fails.** The
*measured* contrast over the same rows (§4, gating nothing) is:

| class | measured tight (p98) | measured mid (0.40–0.60) | measured ratio | T3 bar |
|---|---:|---:|---:|---:|
| STORAGE | $1,055.60 | $695.89 | **1.52×** | 3× |
| THERMAL | $37.30 | $44.67 | **0.84×** | 3× |

So: storage conduct *does* rise with tightness, in the right direction, but only
**1.52×** — half the bar. Thermal top-of-stack is genuinely **flat-to-inverted**
(0.84×) in measurement, not merely in extrapolation. **Neither class reaches the
bar on measured data**, so T3's FAIL is real; only the *magnitude* of the
predicted inversion is an artifact.

T3 is in any case **not load-bearing for the verdict**: T1, T2, T4 and T5 all fail
on storage independently, and §3.2 shows the verdict is robust without it.

---

## 3. TWO HONEST PROBLEMS WITH THIS SESSION'S OWN INSTRUMENT

Reported because the record is worth more than the result.

### 3.1 A plumbing defect that produced a false first verdict — caught by the precommit's own coverage block

The **first** execution returned NOT-TRANSFERABLE on all five gates. It was not a
measurement. Its coverage block showed **15 of 2,629** fit hours and **2 of 175**
test hours carrying offer rows, and **no candidate form was ever fitted** — the
gates were failing vacuously.

Root cause: `load_segments` bound the kept-shard set to `keep`, then rebound the
same name to the timestamp-validity mask inside the loop; from the second shard
onward `p not in keep` tested a `Path` against a boolean Series' index and skipped
every remaining shard. Renamed `keep_shards` / `ts_ok`; **nothing else changed** —
no threshold, band, fold rule, driver, population filter or functional form. The
verdict reported here is from the fixed run, whose coverage is in §1.

That the defect was caught at all is the precommit's doing: it required a coverage
block in the JSON, and a five-gate wipeout with an empty `selected` map is not a
finding, it is a smell. **A pre-registered coverage requirement is a cheap
falsifier and every future Phase-0 in this program should carry one.**

### 3.2 A pre-registered constant that turned out to be unsatisfiable — and the verdict's robustness to it

Precommit §6.3 made a monthly fold **admissible** at ≥ 10 evaluation hours. At the
p98 cut, **post-ECRS 2023 carries only 22 hours across all seven months**, the
largest being 9 (August). So **no post-ECRS 2023 month is admissible**, and
T1/T2's "≥ 5 of 7 admissible folds" clause is **unsatisfiable by construction**.

A verdict resting on that clause would be an artifact of my own constant. It does
not:

- T1 and T2 also carry a **named-months clause** (Aug-2023 and Sep-2023 both in
  band) that is independent of admissibility. Storage misses Aug by −77.6 % and
  Sep by −51.3 %; both gates fail on substance.
- Re-running T1/T2 with admissibility relaxed to **≥ 1 hour** (reported, gating
  nothing) leaves the verdict where it was — and sharpens the class split:

  | | admissible folds | in band |
  |---|---:|---:|
  | STORAGE T1 | 5 | **1** |
  | STORAGE T2 | 5 | **2** |
  | THERMAL T1 | 5 | **5** |
  | THERMAL T2 | 5 | **5** |

- **T4 and T5 do not touch the 2023 fold rule at all** and both fail for storage.

So the verdict is robust to the defective constant. The constant is still wrong,
and a Phase-1 charter reusing this design must fix it.

### 3.3 The reason behind §3.2 is itself a substantive finding

Why is post-ECRS 2023 so thin at the tightest 2 %? Because **2023's tightest hours
by PRC are not its scarcity-priced hours**:

| 2023 tightest-2 % hours, by month | Jan 55 · Feb 12 · Mar 5 · Apr 32 · May 44 · Jun 7 · Jul 6 · **Aug 9** · **Sep 4** · Dec 1 |
|---|---|

**August 2023 sits at a mean tightness percentile of 0.470 and September at
0.372** — the two months carrying **96.2 %** of the C3b-2023 squared residual
(`ercot193_c3b_decomposition`) were, on average, *median-tightness* months by
measured physical reserve. Only 9 of August's 744 hours reach the year's tightest
2 %.

This matters beyond the fold arithmetic. **The driver the whole conduct-function
family is built on does not select the object it is meant to explain.** ERCOT's
August-2023 price formation was not a response to the year's most extreme reserve
conditions — consistent with, and now independently measured alongside, the
committed record that the 2023 tail formed at RTORPA p50 ≈ $1–5 with no
administrative scarcity to recover (ercot-102, ercot52 cap-dual).

---

## 4. WHAT THE MEASURED (NOT PREDICTED) NUMBERS SAY ABOUT WHY STORAGE FAILS

All three years, same statistic, same population rule, **matched tightness
percentile** (the p98 cut) — offered volume beside offered price:

| year | STORAGE offered MW/h | STORAGE `p50` | THERMAL offered MW/h | THERMAL `p90` |
|---|---:|---:|---:|---:|
| 2023 | **3,023** | **$2,713.97** | 66,197 | $38.78 |
| 2024 | **8,360** | **$1,280.84** | 76,100 | $36.08 |
| 2025 | **25,266** | **$989.81** | 80,711 | $38.32 |

At matched tightness, storage offered volume grew **8.4×** (3.0 → 25.3 GW) while
its median offer price fell **2.7×** ($2,714 → $990). Thermal moved by neither
measure — volume +22 %, price within $2.70 across three years — which is exactly
why thermal transfers and storage does not.

The function is not failing to see a driver; **the mapping itself moved**, and it
moved in the direction competitive entry predicts. Monthly detail is starker
still: 2023 storage `p50` runs **$3,361–$5,000** (Jun–Sep) against **$560–$1,912**
in 2025.

**This is ASSESSMENT-ercot209 §3 Door A's own "against" argument, now measured
rather than argued:** *submitted offers are outcomes of the equilibrium under
validation.* A storage offer surface is a function of the competitive state of the
storage fleet — which roughly tripled across 2023 → 2025 — not of system tightness
alone. Conditioning on tightness cannot recover it, and T5 shows no other function
of these drivers can either.

---

## 5. ADMISSIBILITY, ARGUED BOTH WAYS (the §2.6 pattern)

**The case that this result should NOT close Door A.** (i) The driver set is
small — five quantities. SOC is proxied by `HSL / HSL_ref` rather than read
directly, and a true SOC/AS-position series (the DAM ESR data, or an RT SOC
telemetry stream) might carry the missing information; T5 refutes *these* drivers,
not every conceivable driver. (ii) The storage evaluation rests on 22 post-ECRS
2023 hours; that is thin, and §3.2 shows the fold design was not built for it.
(iii) T3's *predicted* inversion is confounded by extrapolation (§2.4), so that
gate's headline number is not clean evidence — though its measured counterpart
still misses the bar in both classes, so this is the weakest of the four.
(iv) Thermal transfers cleanly, so the *method* works — a narrower Phase-1 scoped
to thermal top-of-stack is not refuted by anything here.

**The case that it SHOULD.** (i) T5 is model-free and enormous: 95.1 % of tied
pairs, max irreducible error $2,487.50/MWh, against a $50 floor. Adding drivers
must not merely help — it must break 1,111 near-exact ties, and the ties are on
*storage's own telemetered position*, which is where an SOC driver would live.
(ii) T4 kills the regime explanation: storage fails 2024 → 2025 inside one regime,
so this is not about 2023. (iii) §4 identifies a mechanism for the failure —
competitive state, an equilibrium object — that no forward-computable driver can
carry by construction, because it is the very thing a forecast would have to
predict. (iv) §3.3 shows tightness does not even *select* the object. (v) Card
W (ercot-200) already measured design-regime identification unachievable on the
committed anchors; this is the same wall at a finer grain.

**Where that leaves it.** The pre-registered rule decides, and it decided:
NOT-TRANSFERABLE, nothing chartered. The genuinely open remainder is **not** the
storage conduct function — it is the two narrower questions in §6, which are for
the owner and which this session does not charter.

---

## 6. WHAT IS HANDED BACK TO THE OWNER, UNCHARTERED

No Phase-1 build charter is drafted: §7.1 authorises one **only** on a
TRANSFERABLE verdict, and the verdict is NOT-TRANSFERABLE. Three items are named,
none chartered, none costed:

1. **A thermal-only conduct layer is not refuted by this test** — T4 6/6, T5 0 of
   4,501, every 2023 month in band. It is also **not the 2023 object**: thermal
   top-of-stack offers ~1 % of MW ≥ $500 while storage offers 69–100 %, so a
   thermal conduct layer would not move the 2023 tail. Recorded so the record does
   not later mis-read "NOT-TRANSFERABLE" as covering both classes; it does not.
2. **A direct SOC/AS-position driver** (60-Day DAM ESR data, committed at
   `data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_ESR_Data_*`) is the one driver
   addition with a principled claim on the storage ties, since the ties sit on
   storage's own position. Whether it survives §5's model-free objection is
   unmeasured. Any such re-test is a **new** owner card, and would need to state
   why it is not a re-run of a stopped lane.
3. **Door D stands as the floor**, per X-1 and ASSESSMENT-ercot209 §3: ERCOT
   bandwidth returns to the R-A re-pointed queue, and the conduct question reopens
   with real anchors at the 2026 SOM (~mid-2027). ASSESSMENT-ercot209 §4's other
   two recommended sessions — **REPORTING-TEXT-1** (Door C) and **RESERVE-BASIS-1**
   (the ercot-204 §A ORDC pricing-region question) — are untouched by this result
   and remain the strongest live items.

---

## 7. GOVERNANCE

- **Q-B FINAL and R-A cited and honoured, SCOPED by X-1, not reopened.** **No
  C3a, C3b or C3c value was computed in any year.** The C3a-2023 −33.2 %, the
  C3b-2023 0.604 and the 58/181 tail counts appear here only as citations to
  committed artifacts, none re-scored. No lever was run, no offer-curve constant
  touched.
- **Rule 13 `[R-MEASURED]`:** delivery-2023 conduct entered as the evaluation
  target only, measured-vs-measured. Nothing measured here feeds any model input,
  and no artifact of this session is consumable by a solve.
- **The quantity-only claim is auditable, not asserted:** the probe writes its
  reserve-telemetry read set (`hour`, `prc`, `rtolcap`) and its refused set
  (`system_lambda`, `rtorpa`, `rtoffpa`, `rtordpa`) into the output JSON. No
  settlement price, LMP, RTSPP or model output was read at any point — the rule
  19/13 line the published-RTORPA overlay crossed (ercot-204 §A / ercot-203b).
- **Rule 28 `[R-MECH-MATRIX]`: no matrix row or cell edit.** No mechanism was
  tested — this is the ercot-182/189/196/200 *card-is-a-read* precedent. The
  conduct-layer cell stays absent, not `R`: a Phase-0 identifiability measurement
  adjudicates no mechanism, and minting a verdict cell would overstate what was
  done.
- **DO-NOT-REDO (rule 28a) honoured** and argued in precommit §3 against all four
  dead instruments. V0's verdict was **not** assumed — its own tie test was re-run
  at hour grain as T5, and it returned a *different, class-split* answer, which is
  the honest way to inherit a stop.
- **Rule 22 `[R-HOLDOUT]`:** years {2023, 2024, 2025} only; no holdout year read,
  no marker sought or spent. **Rule 25:** ERCOT only. **Rules 5/24:** no config
  surface. No `.github/workflows` added. No other branch touched, no PR opened.
- **Rule 27 `[R-PUSH]`:** every file ≥ 300 lines edited locally and blob-verified
  against the remote after push.
- **Data recovery:** the BLOAT-B-5 window and 3 of 4 probe extracts were restored
  from the README's pinned `git restore --source=726f389d…`, never a fresh MIS
  fetch. The RTC+B quarantine was restored but **not read**; corpus globs stay
  non-recursive and this lane stops at delivery 2025-12-04.
- **Keeper at session start and end:** `2026-08-15-ercot204-rule26-delete`.
- **Artifacts:** this finding, the precommit, `scripts/probes/ercot210_conduct_transfer_phase0.py`,
  `results/calibration/ercot210_conduct_transfer_phase0.json`, one calibration-log
  entry (ercot-210), and the X-1 signature appended to ASSESSMENT-ercot209.
  Nothing else.
