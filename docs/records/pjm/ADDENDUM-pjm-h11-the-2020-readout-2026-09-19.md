# ADDENDUM — pjm-h11: the 2020 readout. C-1 measured, and the ex-ante prediction's MECHANISM lands within 0.16 TWh (2026-09-19)

**Session:** pjm-h11 (orchestrator, **zero LP minutes** — rule 32 `[R-SHARD]` (a); the solves ran in
per-year shards, one year per container, which is rule 36 `[R-YEAR-ISOLATION]` (a)).

**STATUS: ALL TWELVE LEGS HAVE LANDED — 2 arms × 6 years.** This document was first written as a
partial result while the invariance years were still solving; they have since reported and the
invariance check is recorded in §0 below.

### 0. Invariance — the arm is a clean single-year delta, confirmed through the solver

The arm adds **one key** to `PJM_SEAM_LADDER_BY_YEAR` (2020) and changes nothing else, so every
other year must be untouched. The PRECOMMIT established that at zero LP (0 of 240 shared rungs
move); these are the solved bundles, differenced class-by-class on the P1 hourlies:

| year | max \|Δ\| TWh | Σ\|Δ\| TWh | classes moved | verdict |
|---|---|---|---|---|
| 2021 | 0.000000 | 0.000000 | 0 | IDENTICAL |
| 2022 | 0.000000 | 0.000000 | 0 | IDENTICAL |
| 2023 | 0.000000 | 0.000000 | 0 | IDENTICAL |
| 2024 | 0.000000 | 0.000000 | 0 | IDENTICAL |
| 2025 | 0.000000 | 0.000000 | 0 | IDENTICAL |

**Exact, in all five years.** The promotion blocker this was gating is cleared: whatever C-1 does,
it does it to 2020 alone.

**Bundle provenance** — every leg verified by config signature before use (ARM bundles carry the
2020 ladder key with MISO export `(66.93, 57.12, 36.2, 25.46, 20.05, 15.95, 11.93, 8.68)`; CONTROL
bundles carry no 2020 key), recovery by full immutable sha:

| year | CONTROL | ARM |
|---|---|---|
| 2020 | `f3bf920ddfa9d4bd86be1c71b2984647b89d0681` | `bc7617af9b94b8f2997152ab4888c54e88690263` |
| 2021 | `e24901cb6dacd2ec6daaeafe86e7a6e4b0252c55` | `aebecf818d97d1534697b2eb9f76844f3a90b855` |
| 2022 | `50b217e854cad8068a6e4763e11a969aa4753958` | `9bd16d405e3bb5350a9592bb1245c1dabfcddeb2` |
| 2023 | `3510c19c16d9913d3920ea29c3c6c0f4c7736d16` | `e301cb5fa58af76b03d3297c6f4321829b09af88` |
| 2024 | `9e4d5b31598149a1526ccfce02d7916a99e5ea97` | `5fd266b64f50f19fa56e2876623803364a018bf6` |
| 2025 | `53a7e81dafdd512ab0a80af031e94b5615dd1565` | `efe30d52a72c460efbf619d13ebf946127ed1475` |

All carry 17 files except **ARM 2022 (15)**, which is missing `floors/2022_P1.npz` and
`hourly/unit_hourly_2022.parquet` — the SPP-48 directory-grain `.gitignore` trap on
`results/calibration/*/floors/`, which a `/**` negation cannot re-include. Neither is
registration-critical: `dispatch/2022_P1.parquet`, `hourly/network_2022.parquet`,
`hourly/class_hourly_2022.parquet` and `system.parquet` are all present.

---

## 1. The measured delta, ARM − CONTROL, 2020 (TWh)

| class | CONTROL | ARM | Δ |
|---|---|---|---|
| **`import`** (negative = net export) | −40.391 | −28.344 | **+12.047** |
| CC_REGULAR | 287.452 | 283.477 | **−3.975** |
| COAL_BIT | 162.223 | 159.341 | **−2.882** |
| CT_PEAKER | 18.047 | 15.844 | −2.203 |
| VIRTUAL_DEC | −12.584 | −13.655 | −1.071 |
| ST_GAS | 8.283 | 7.277 | −1.007 |
| VIRTUAL_INC | 9.109 | 8.547 | −0.562 |
| CC_CHP / COAL_PRB / COAL_WC / CT_CHP | | | −0.161 / −0.149 / −0.106 / −0.085 |
| **fossil total** | | | **−10.574** |

Nothing else moves by ≥0.05 TWh. Nuclear, wind, hydro, OTHER and biomass are **identical to the
milli-TWh**, which is the signature of a clean single-mechanism delta: the seam repriced, the LP
re-cleared, and only the dispatchable stack followed it.

## 2. Net export, against both benchmarks

| | TWh | residual vs measured 41.626 |
|---|---|---|
| measured (PJM settlement tie file) | 41.626 | — |
| committed keeper `pjm_d4_4_TP` | 38.810 | −2.816 |
| **CONTROL at HEAD** | **40.391** | **−1.235** |
| **ARM at HEAD** | **28.344** | **−13.282** |

**The export residual gets much worse — as predicted, and by more than predicted.** The PRECOMMIT
§3.3 prediction, written before any solve, was that 2020's export residual would *worsen*, on the
grounds that the ladder's gross ceiling at the model's own price (37.340 TWh) sits **below** the
38.810 TWh the unmechanised forecast track delivers. **Direction: CONFIRMED. Magnitude:
UNDER-PREDICTED** — I wrote "toward roughly −4 TWh or worse" and the realized figure is −13.282.
Recorded as a miss on my own forecast, not smoothed over.

## 3. The control was not optional — and the +1.581 TWh gap is NOT all "HEAD drift"

The CONTROL at HEAD exports **40.391 TWh** where the committed keeper recorded **38.810** — a
**+1.581 TWh gap on 2020 with no mechanism change at all**. Had this lane differenced the arm
against the *committed keeper* instead of against a control solved the same way at the same HEAD, it
would have charged all **+1.581 TWh** of that to C-1. Rule 29 `[R-SCREEN]` (b)'s form-4 test earned
its control here in the most concrete way available.

**THE ATTRIBUTION, SETTLED BY MEASUREMENT — and I got here via a wrong turn, recorded rather than
quietly tidied.** I first called this "HEAD drift", full stop. When rule 36 `[R-YEAR-ISOLATION]`
landed mid-session I revised that to "code drift and the year-isolation artifact in unknown
proportion, and this lane cannot separate them." **That revision was over-cautious: the lane
CAN separate them, from bundles it already had.** Measuring the control against the committed
keeper on every year at once:

| year | keeper | control @ HEAD | drift | position in its solve span |
|---|---|---|---|---|
| 2020 | 38.810 | 40.391 | **+1.580** | 1st of TP |
| 2021 | 24.273 | 25.510 | **+1.236** | 2nd of TP |
| 2022 | 22.667 | 22.878 | **+0.211** | 3rd of TP |
| 2023 | 30.870 | 30.862 | −0.008 | 1st of A |
| 2024 | 22.277 | 22.277 | **−0.000** | 2nd of A |
| 2025 | 24.379 | 24.379 | **−0.000** | 3rd of A |

**Two signatures are being told apart, and they point opposite ways.**

* **The year-isolation artifact would grow with position inside a span** — miso-262's own evidence
  is that the solve "reproduced the FIRST year of each solve leg and diverged in the later ones."
  Observed here: within `pjm_d4_4_TP` the drift **shrinks** with position (1.580 → 1.236 → 0.211),
  and within `pjm_d4_4_A` it is ~0 at **every** position. **2024 and 2025 — the two most
  warm-start-exposed years in the whole PJM keeper — are drift 0.000.** That is the opposite of the
  artifact's signature, and it bounds the year-isolation effect for PJM at **≈0 on net export**.
* **The offer-midcurve rebuild matches exactly.** PRECOMMIT §2.2 measured that LIVE hunk's own
  per-year footprint *before any solve*: material on 2020/2021/2022 (CC_LIKE −11.0 / −7.6 / +11.9 %,
  LONG_RUN −3.2 / −23.9 / −2.6 %) and negligible on 2023/2024/2025 (≤0.2 %, **2025 byte-identical**).
  The realized drift is material on exactly those three years and **exactly 0.000 on 2024 and
  2025** — including the byte-identical year the zero-LP analysis singled out.

**So the +1.580 TWh on 2020 IS code drift**, and specifically the rebuilt
`pjm_offer_midcurve_condbinned.json`. G-DRIFT form 4 is falsified per-year with numbers, and the
rule-36 artifact is ruled out for PJM by measurement rather than by assumption. **Rule 36(f)'s
warning still holds in general** — every ISO's keeper was CLI-solved with the knobs on — it simply
does not bite PJM's interchange here, and PJM's lane now has the measurement to say so instead of
inheriting MISO's 24 TWh figure as a worry.

*(Retained for the record, since it was published and someone may have read it: the intermediate
"cannot be separated" reading, and why it was wrong — I had the six control bundles in hand and had
not yet differenced them against the keeper year-by-year. The lesson is the cheap one: measure the
pattern before conceding an attribution is unrecoverable.)*

**What the earlier reading got right and still stands:** this lane's own bundles are rule-36 clean
by construction, for the reasons below, and the arm-vs-control delta in §1 is unaffected by any of
this because both legs ran identically.

The two causes it named were:

* **(a) genuine code drift** since the keeper's `git_sha` `f09eddbe` — the four LIVE hunks the
  PRECOMMIT §2.2 audit names; and
* **(b) the year-isolation artifact rule 36 was written out of.** The committed keeper was solved
  through the **CLI** as a **multi-year span**, where `resolve_xyear_warmstart_default` and
  `resolve_p1_basis_seed_default` flip both warm-start knobs **ON**. Rule 36(f) states the
  consequence plainly: *"Every ISO's keeper was solved through the CLI with both knobs ON, so every
  keeper carries some of this artifact and its registered numbers will move when it is next
  re-solved."* On MISO the same artifact moved a year by up to **24.18 TWh** of class dispatch, so
  1.581 TWh is well inside its demonstrated range.

**This lane's own bundles are on the CLEAN side of that line, and it is verifiable rather than
asserted.** Every shard ran `scripts/replay_keeper.py`, which (i) calls `solve_and_persist`
**directly, not through the CLI gate** (its own comment, line 46), so neither `resolve_*_default`
ever executes, and (ii) **explicitly pins** `DETERMINISM_ENV = {"MARKET_SIM_WARMSTART_XYEAR": "0"}`
(line 48). `pipeline/solve.py`'s same-year seed then cannot arm either, because `_p1_seed` requires
`_xwarm`. **So both knobs were OFF in all twelve shards** — and each shard solved exactly **one
year** in its **own container**, which is rule 36(a) verbatim. These bundles were rule-36 compliant
by construction, before rule 36 existed.

**What follows for the promotion.** The arm-vs-control *difference* in §1 is unaffected by any of
this: both legs ran identically, so anything common to them cancels. And per the measurement above,
the keeper **is** a usable comparison basis for PJM after all — the year-isolation artifact is ≈0 on
its interchange, so the committed 38.810 and the isolated 40.391 differ by code drift, which is a
known and attributed quantity rather than a confound. **A later lane may quote "+1.580 TWh on 2020,
attributable to the rebuilt offer-midcurve table" from this document; it may not quote the earlier
"unknown proportion" framing, which this section supersedes.**

Two things this does *not* license. It does not generalise past PJM: rule 36(f)'s warning stands for
every other ISO until each measures its own pattern the same way. And it does not clear the
year-isolation artifact on quantities other than net export — this table is interchange only, and a
class-level or price-level check could still find movement the `import` row integrates away.

**One further consequence for rule 32 `[R-SHARD]`, recorded because this lane argued the other
way.** Earlier in this session I told the owner that the per-year fan-out they instructed was a rule
32(b) violation being taken as an owner override. **Rule 36(a) now codifies the opposite**: *"This is
the one place rule 32 `[R-SHARD]` (b)'s ban on per-year fan-out does NOT apply … A registrable
backcast run is therefore one shard per year, composed."* The owner's instruction was the rule
arriving early, not an exception to it, and the reasoning rule 36(a) gives is exactly the one that
made it work here — rule 34 `[R-SHARD-PROMOTABLE]` (a) made every shard push its FULL bundle
including `dispatch/<y>_P1.parquet`, so the legs compose.

## 4. THE STRIKING ONE: the mechanism reproduces its own ex-ante prediction to 0.16 TWh

PRECOMMIT §3.3 measured, at zero LP from the committed sidecar, that 2020's gap between the ladder
evaluated **at the model's own border-zone price** and the ladder evaluated **at the measured DA
price** is **13.441 TWh** — the largest of any year (next is 2021 at 7.82), and the reason the
PRECOMMIT named 2020's internal price as the defect the ladder would expose.

The realized export shortfall the arm produces is **13.282 TWh**.

**13.441 predicted, 13.282 realized — a difference of 0.16 TWh, about 1 %.** These are different
computations on different objects (an offline rung-clearing integral against a solved LP's
interchange), so exact agreement is not expected and the closeness should not be over-read. But it is
strong evidence that the ladder is doing **exactly** what the offline analysis said it would: it
converts 2020's depressed internal price into a visible volume error rather than absorbing it. That
is the rule 14 `[R-ACCURATE]` story stated in the PRECOMMIT — *the estimate was silently
compensating* — landing as a measurement.

## 5. What this does to C1, the criterion that actually fails

2020's two worst C1 classes both move **toward** measurement (FINDING pjm-h10 §4.2 baselines):

| class | was, vs EIA-923 | arm Δ | after |
|---|---|---|---|
| CC_REGULAR | **+7.5** over | −3.975 | ~**+3.5** over |
| COAL_BIT | **+16.9** over | −2.882 | ~**+14.0** over |

So the arm **improves the failing criterion** while worsening interchange volume.

**And interchange volume is not a scored criterion.** FINDING pjm-h10 §7.1 established that no
rubric criterion tests total system energy or interchange volume — `sysvol` (C2) is gas/coal
families only. Adding one was a **governance proposal** in §7, explicitly *not adopted*, and §7.4
recommended against gating it precisely because it would penalise the ISOs that model the seam as a
market. So on the current rubric the regression this arm causes is **unscored**, and the improvement
it causes is **on the criterion that fails**.

**Stated against interest:** that is a favourable accounting, and I am not going to let it pass
unchallenged. A −13.3 TWh interchange error is a real defect whether or not a gate looks at it, and
"the thing I made worse happens not to be measured" is the kind of argument rule 1 `[R-STRUCT]`
exists to distrust. The honest reading is that C-1 **relocates** 2020's error: out of the
unmechanised forecast track's flattering export number and into a visible, attributable seam
shortfall that points straight at the internal price. That relocation is the point — it is what
makes the next defect findable — but it is a relocation, not a net reduction in error.

## 6. Keeper judgement — NOT YET, and what is still missing

Against the owner's stated criterion (*"if structural integrity improves but gates regress that may
still be a keeper"*), C-1 on 2020 is a **strong candidate**: structure improves (a keeper year now
runs the keeper's own measured seam mechanism instead of the forecast track), the failing criterion
improves, zero parameters were added, and what regresses is unscored.

**Three things must land before I would recommend promoting:**

1. **The five invariance years.** ARM 2021–2025 are predicted byte-identical to their controls (the
   PRECOMMIT verified 0 of 240 shared ladder rungs move). If any of them moves, the arm is not the
   single-year delta it is claimed to be and this readout is not safe to promote.
2. **`metrics.json` is ABSENT from every one of these single-year replay bundles.** So no official
   C1/C2/C3a/C3b/C3c verdict exists for them and every number above is computed by this session from
   the class hourlies. A promotion needs the scored verdict, which is parent-side zero-LP work but
   is **not done yet** and must not be assumed.
3. **Composition.** Rule 35 `[R-PROMOTE]`: PJM registers as TWO runs (keeper 2023–2025 + touchpoint
   2020–2022 folded by `holdout.keeper`), so the per-year bundles must compose into two three-year
   runs and survive `render_calibration_html.build_payload`, which reads the bundle-root
   `system.parquet`. Unverified.

Rule 31 `[R-RETAIN]`: nothing is deleted, and the promotion question goes to the owner with these
numbers rather than being pre-empted either way.

---

## 7. C-2 MEASURED — and it REFUTES the import leg of FINDING pjm-h10 §2.5

§2.5 could only infer the gross export / gross import split, and said so plainly: *"Read the import
column as an INFERENCE, not a measurement… it inherits both their errors."* That caution was
correct. All twelve bundles now carry `hourly/network_<year>.parquet`, so the split is measured.

**Both sides computed on the SAME basis — system net position by hour** (model: the five
`PJM_external>PJM_<zone>` link rows summed per hour; measured: PJM's settlement tie file summed per
hour over its tie lines). TWh:

| year | model gross exp | measured gross exp | model gross imp | measured gross imp | export short |
|---|---|---|---|---|---|
| 2020 (control) | 40.391 | 41.626 | **0.000** | **0.000** | −1.235 |
| 2021 | 25.510 | 37.825 | 0.007 | 0.011 | **−12.315** |
| 2022 | 22.878 | 31.909 | 0.019 | 0.135 | **−9.031** |
| 2023 | 30.862 | 40.090 | 0.002 | 0.116 | **−9.228** |
| 2024 | 22.277 | 33.133 | 0.048 | 0.308 | **−10.856** |
| 2025 | 24.379 | 33.527 | 0.019 | 0.603 | **−9.148** |

**THE RESULT: the shortfall is ~100 % EXPORT-SIDE. There is no import-side excess.** Measured PJM is
a near-pure net exporter — its system-level gross import is **0.000–0.603 TWh** across six years —
and **the model reproduces that structure exactly** (0.000–0.048 TWh). §2.5's inferred
*"implied import-side excess of 4.083 / 2.830 / 4.398 / 6.114 / 4.658 TWh"* is **refuted**: on the
like-for-like basis the model does not over-import at all.

**This retires a named suspect.** `interchange/spec.py`'s own comment warns of *"phantom imports that
displace CC_REGULAR dispatch, the C1 FAIL"*, and §2.5 read its import column as evidence for it.
Measured, **PJM's system-level phantom imports are ~zero in every year.** Whatever drives PJM's
CC_REGULAR over-run, it is not phantom imports at the system boundary. §2.5's other half stands and
is now the whole of it: the model under-exports, by 9.0–12.3 TWh.

**An error of mine, caught inside this analysis and recorded rather than silently dropped.** My first
pass computed the model's gross legs **per link** (preserving inter-border counterflow, which gave
"gross import 16–34 TWh") and compared them against a **system-net** measured number. That is
apples-to-oranges and produced a spurious +13 to +18 TWh "over-import". The two bases must match; on
the matched basis the import leg vanishes. The per-link counterflow is real — §2.7 describes it as
wheel-through — but it is *internal to an hour* and cancels at the boundary the measured file reports.

**What C-1 did to the 2020 seam, mechanically.** Per-link (counterflow preserved), ARM − CONTROL:
gross export **56.631 → 47.801 (−8.829)**, gross import **16.240 → 19.458 (+3.218)**, net
**40.391 → 28.344 (−12.047)**. Every border moves in the import direction, and the **ATSI** border
flips sign outright, −0.598 → +4.797 (a +5.395 TWh swing). So the ladder does not merely throttle
export: it re-prices the borders relative to each other and turns one of them around. On the
system-net basis that all resolves to a pure 12.047 TWh reduction in net export, away from measured.

**Consequence for the lane.** The export leg is the whole defect and C-1 makes it larger on 2020
while leaving 2021–2025 untouched. That does not change the promotion case stated in §6 — C-1's
basis is rules 14/23 and the improvement it buys is on C1's classes — but it sharpens what the next
lane should chase: **a PJM export-volume defect, on a seam whose import side is already correct.**

---

## 8. C1 ON THE RUBRIC'S OWN BAND — and why this lane STOPPED SHORT of promoting

`calibration_verdict.py` scores C1 per class on a volume band of
`min(max(2 % load, 3 % actual gen), 8 TWh)`. For PJM (~800 TWh load) the **8 TWh cap binds on every
class**, so C1-2020 is a clean per-class ±8 TWh test. Computed against the FINDING pjm-h10 §4.2
EIA-923 baseline, carried onto each bundle by its own per-class delta:

| class | registered keeper | CONTROL @ HEAD | ARM @ HEAD |
|---|---|---|---|
| **COAL_BIT** | **+16.90 FAIL** | **+25.16 FAIL** | **+22.27 FAIL** |
| CC_REGULAR | +7.50 ok | +4.32 ok | **+0.35 ok** |
| CT_PEAKER | +0.80 | −0.48 | −2.68 |
| ST_GAS | +1.60 | +1.07 | +0.06 |
| others (wind, nuclear, solar, COAL_PRB, CT_CHP, ST_CHP, OTHER, COAL_WC, biomass, hydro) | | unchanged or ≤0.15 | |
| **classes out of band** | **1** | **1** | **1** |
| **sum \|error\|** | **48.2** | **52.37** | **47.05** |

**The arm is unambiguously better than its own control**: COAL_BIT −2.89, CC_REGULAR −3.97 to a
near-exact +0.35, total absolute error −5.32 TWh. That is the C-1 effect, cleanly isolated.

**But the control is not what is registered, and that is the finding.** The offer-midcurve HEAD
drift (§3) degrades C1-2020 **on its own, with no mechanism change**: COAL_BIT **+16.90 → +25.16**,
a **+8.26 TWh** deterioration on the single class that fails C1. C-1 recovers **2.89** of that,
leaving **+22.27** — still **5.37 TWh worse than the registered keeper** on the failing class.

So "is C-1 an improvement" has three different answers depending on the comparison, and they do not
agree:

| comparison | verdict |
|---|---|
| ARM vs its own CONTROL (same code) | **improvement**, clearly |
| ARM vs the REGISTERED keeper, total \|error\| | **marginal improvement** (47.05 vs 48.2) |
| ARM vs the REGISTERED keeper, **on the failing class** | **REGRESSION** (+22.27 vs +16.90) |

**This lane therefore did not self-promote**, despite holding an owner instruction to promote on an
improvement. Registering this arm would put a run on the dashboard whose **failing criterion reads
worse than the keeper it replaces**, for a cause C-1 did not create and only partly offsets. That is
a materially different thing from what "promote if it is an improvement" is naturally read to mean,
and rule 31 `[R-RETAIN]` puts the decision with the owner rather than with the session's own reading.
The bundles are retained and the question is asked with these numbers.

**THE REAL FINDING HERE IS NOT C-1.** It is that **a committed input rebuild silently cost PJM
8.26 TWh on C1-2020's failing class** — larger than anything C-1 does, invisible until a control was
solved at HEAD, and already latent in `main` for every PJM lane that re-solves from now on. The
offer-midcurve table is the named object (§3). **That is the defect the next lane should chase**,
and it is a bigger one than the seam.

*(All figures parent-computed from the committed class hourlies plus the §4.2 baseline. No
`metrics.json` exists in a single-year replay bundle, so no scorer-emitted C1 record has been
produced for these runs; the band and its cap are read from `calibration_verdict.py` itself.)*
