# PRECOMMIT — ercot-192: the two COAL limbs' 2023 application, re-adjudicated under a FRESH precommit (signature B1)

**Session** ercot-192 · **ISO** ERCOT only (rule 25 `[R-ISO-SCOPE]`) ·
**Years** ⊆ {2023, 2024, 2025} (rule 22 `[R-HOLDOUT]`) ·
**Model** Opus (rule 27 `[R-PUSH]`) ·
**Branch** `claude/ercot-192-b1-coal-limbs-3qzot2`

**Authority.** `docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md`
**card B, signature B1** (owner, 2026-08-11): *"re-adjudicate under a fresh
precommit before any arm."* Sequenced after **A1**, which landed 2026-08-12 (PR
#3887, keeper `2026-08-12-run191-dam-deriver-regate` on the repaired DAM
family), so B1 is unblocked. Matrix `docs/mechanism-testing-matrix.md` §5.1
**item 13** (ercot-169) and **item 14** (ercot-171) are the record this
supersedes-or-confirms; nothing in either is rewritten by this file.

**This file is pushed BEFORE any level is measured and before any solve.** The
only measurement that precedes it is the Phase-0a *instrument-structure* read of
§1c, which reads coverage and headroom composition and **no price of any kind**.

---

## 0. WHAT THIS LANE IS, AND — STATED FIRST — WHAT IT IS NOT

**It IS a mechanism-correctness lane** under rules 1 `[R-STRUCT]` and 23
`[R-FROZEN-DERIVE]`: an armed identification constant is applied to a solve year
in which its own instrument, run on that year's own disclosure, reads **14.4×
outside the constant's identification band**. Whether that is a real
mis-identification or an artefact of the instrument's coverage is the object.

**It is NOT C3a-2023 spend.** Card Q, ruling **Q-B**, was signed final at
ercot-191: the ercot-170 coverage licence failed on the repaired deriver
(L1 0.3857 vs 0.90), and *no further ERCOT C3a-2023 work is authorized*; ERCOT
stands at **NOT-YET on C3a-2023 as a model-class limit**, item 11 **CLOSED**.
This lane does not re-open it. Concretely, and binding on every later section:

* the lane's purpose is the **mis-identification** (rules 1 / 23), not the
  2023 price residual;
* **any 2023 price movement is REPORTED at full magnitude and is never
  targeted**, never a gate, and never the promotion basis;
* the promotion rule of §7 is **direction-blind** by construction — it cannot
  read the residual's sign;
* **no C3a-2023 improvement may be claimed, quoted, or implied** in the
  FINDING, the calibration-log entry, the registry sidecar or the matrix cell,
  whichever way the number moves.

**Fences carried, unchanged.** The C3c ledger is untouched. The closed faces are
untouched. **Item 11 stays CLOSED.** No rubric amendment, no
`LEDGERABLE_CRITERIA` / `MAX_LEDGERED_CAVEATS` change, no holdout marker granted
or spent, no `calibration-complete.json` re-key (ERCOT holds neither `complete`
nor `final`). No PR unless asked.

---

## 1. THE OBJECT

### 1a. The two limbs, and their live status

| limb | mechanism | constants | tranche | status entering this lane |
|---|---|---|---|---|
| **A** | `coal_offer_net_revenue_margin` (ERCOT-137) | `COAL_OFFER_MARGIN_LEVEL_BY_ISO` 15.8807, `COAL_OFFER_MARGIN_ANCHOR_BY_ISO` 1.7387 | coal `_mustrun` | **2023 application CONFIRMED at ercot-171** (level₂₀₂₃ 16.0111 = +0.14× the ±0.9300 band); the declared-extrapolation note is retired BY VERIFICATION |
| **C** | `coal_peak_offer_margin` (ERCOT-140) | `COAL_PEAK_OFFER_LEVEL_BY_ISO` 35.1989, `COAL_PEAK_OFFER_GAS_HR_BY_ISO` 10.4100 (anchor SHARED: `GAS_OFFER_MARGIN_ANCHOR_BY_ISO` 2.2494) | coal `_peak` | **NOT-IDENTIFIABLE-2023 CONFIRMED at ercot-171**; extrapolation note STANDS; no candidate arm named |

Both are armed on the run191 keeper (`coal_offer_net_revenue_margin: true`,
`coal_peak_offer_margin: true`), so both are live in the 2023 solve.

**The measured defect (card B).** The delivery-2023 COAL corpus's two most
common submitted TOP steps are **$78.00** (21,677 intervals) and **$75.01**
(17,869); **$34.82** — the 2024/25 level — is a distant tenth. The constant's own
instrument reads **p90 = 75.00** on delivery-2023, i.e.

    level₂₀₂₃ = 75.00 − 10.4100 × (2.6012 − 2.2494) = 75.00 − 3.6622 = 71.3378

against the armed **35.1989** — **+36.14 = 14.4× the ±$2.5062 band**, i.e. the
armed constant is ≈ **half** the measured 2023 top. The direction corroborates,
at fleet scale and on an independent instrument, what ercot-168 measured and
promoted (Oak Grove's overnight top $60.26/$61.46).

**Limb A is carried, not assumed.** ercot-171 already CONFIRMED it, but through
the S1 resource-drop rule. This lane re-reads limb A through §2's instrument as
a **second, independent route**. A disagreement is a finding about ercot-171, not
about limb A's arming, and would be reported and STOP (§6) — it does not license
any change to limb A.

### 1b. Identification source (rule 23 `[R-FROZEN-DERIVE]` citation)

The **committed delivery-2023 SCED 60-Day NP3-965 corpus**
(`data/raw/ercot/SCED`, 996 shards; the ercot-157 re-upload). Its landing is the
rule-14/23 data-vintage trigger that dissolves these constants' declared premise
*"no 2023 SCED disclosure exists"* — the same trigger item 12 / ercot-168
executed for the per-plant curves. **No residual is consulted at any point of the
derivation.** Nothing here re-derives against a model output; the source is a
disclosure, and the re-derivation is licensed by its arrival, not by a fit.

### 1c. INSTRUMENT-DESIGN BASIS — the Phase-0a structure read (measured before this file; NO price read)

`scripts/probes/ercot192_coal_peak_structure_phase0a.py` →
`results/calibration/ercot192_coal_peak_structure.json`. It reports only
`ercot123._decompose`'s own coverage/headroom quantities. Matched window
(h11–22 CST, the identification subsets' window):

| quantity | delivery-2023 | 2024/25 subsets (res-hours pooled) |
|---|---|---|
| `curve_share` (unweighted share of resource-intervals with a curve) | **0.97022** | 0.99623 |
| `a_offered` (headroom-weighted offered share) | **0.94775** | 0.99672 |
| share of RT headroom `h_rt` sitting in no-curve rows | 0.05175 | 0.003–0.007 |
| of that no-curve headroom: **(b) price-taking / self-schedule** | **0.98787** | 0.9876–0.9917 |
| of that no-curve headroom: (e) genuine residual | 0.01213 | 0.008–0.012 |
| loading (netout/HSL) of the no-curve rows | 0.98047 | 0.954–0.984 |

Per-resource, the shortfall is where ercot-169 located it: `MLSES_UNIT1/2/3`
0.7572 / 0.7611 / 0.7970, then `WAP_WAP_G8` 0.9489 and `CALAVERS_JKS2` 0.9827;
every other COAL resource is ≥ 0.9984.

**Two candidate repairs are REFUSED on this read, before any level is measured.**
Recording them here is the point of a fresh precommit — neither may be revived
later in this lane:

* **REFUSED — own-conduct imputation.** Filling each no-curve resource-interval
  with that resource's own modal curve would fix `curve_share` without dropping
  anyone. It is **inadmissible**: 98.8 % of the missing headroom is ERCOT-123
  bucket **(b), price-taking**, and the rows are loaded at 98 % of HSL. A
  self-schedule is a resource *making no incremental offer*. Imputing a curve
  there would **invent an offer that was not submitted** — a measured *outcome*
  manufactured into an input, i.e. rule 13 `[R-MEASURED]`.
* **REFUSED — re-expressing the licence on the exposure-matched quantity.** An
  incremental-MW-weighted statistic integrates over offered MW, so `a_offered`
  is arguably the exposure-matched licensing quantity rather than the unweighted
  `curve_share`. It is **refused anyway, and refused because it is measured
  first**: on delivery-2023 `a_offered` is **0.94775**, i.e. *worse* than
  `curve_share`. Substituting it would not rescue the limb, and a licensing
  quantity may never be chosen after seeing which one passes.

**The floor is not lowered.** `LICENCE_FLOOR = 0.9876` (ERCOT-138 §3.4) stands
exactly as ercot-169 and ercot-171 left it. **No resource is dropped** (that is
ercot-171's S1, refuted for limb C at 7.6× band). **No month is selected** (that
is ercot-171's S2, pre-refused there). This lane changes none of them.

---

## 2. THE INSTRUMENT — a COVERAGE BOUND, not a coverage repair

ercot-171 closed with: *"an instrument that does not select on the tail would
need its own charter."* This is that charter, and it takes the one route that
requires **no repair at all**.

**The construction.** Limb C's statistic is a quantile α = 0.90 of a
**weighted** distribution over offered MW; limb A's is a quantile α = 0.50 of an
HSL-weighted distribution over rows that carry a curve. In both cases the
missing rows contribute **zero weight**. So instead of guessing what the missing
rows would have said, bound it: give the missing weight *M* the most extreme
admissible price in each direction and recompute the quantile on the observed
weight *O*.

    append M at −∞  ⇒  q_low  = α + (α − 1) · M/O
    append M at +∞  ⇒  q_high = α · (1 + M/O)

so the true α-quantile, **under ANY imputation of the missing rows whatsoever**,
lies in `[ Q(q_low), Q(q_high) ]` of the observed distribution. This is an exact
identification interval, not an estimate.

**Why this is the right instrument for B1, stated before the numbers:**

1. **It selects nothing.** No resource dropped, no month kept, no price
   invented, no licensing quantity swapped, no floor moved. The observed
   distribution is the corpus's, unrestricted.
2. **It is adversarial in both directions.** The lower bound assumes the
   worst case *for the finding*; the upper bound assumes the worst case
   against it.
3. **It converts card B's assertion into a measurement.** Card B argues *"a
   1.7 pp coverage shortfall cannot produce a 2× level shift."* That is an
   assertion in the record. `q_low` is exactly that claim's arithmetic, and it
   can fail.
4. **It is falsifiable.** If the interval straddles the armed band, the answer
   is NOT-IDENTIFIABLE-2023 and this lane stops with no arm (§6). §3 fixes that
   branch before the read.

*M* is taken as the no-curve rows' full RT-dispatchable headroom `h_rt` for
limb C (the most weight that could conceivably have been offered and was not),
and the no-curve rows' `HSL` for limb A (that instrument's own weight). Both are
the maximal admissible *M*, so the interval is conservative.

**Harness.** `scripts/lib/sced_corpus_instruments.py` is imported and **not
re-implemented** — `load_corpus_year`, `restrict_hours`, `curve_bottom`,
`inc_bid_quantiles`, `coverage`, `LIMBS`, `fuel_basis_by_year` verbatim, exactly
as ercot-169 and ercot-171 used them. The bound is a re-weighting of the same
statistic, added in `scripts/probes/ercot192_coal_limbs_bound_phase0.py`.

---

## 3. PHASE-0 GATES — pre-registered, values fixed here

| gate | statement | branch on failure |
|---|---|---|
| **G-FOOT** | The unrestricted pipeline reproduces the eight committed subset-class reads (`bot_p50` 16.86 / 16.37 / 15.00 / 15.00; `p90` 34.82 / 34.82 / 43.00 / 48.01) to ≤ $0.02, and the fuel basis reproduces ERCOT-138 §J `fuel_capwtd` 2.213 / 3.232 to ≤ 0.001. | **STOP.** A harness that cannot reproduce the record cannot adjudicate it. |
| **G-NEUT** | The **identical bound construction** applied to the four committed 2024/25 identification subsets must leave each constant inside its own band: the res-hours-pooled bound interval for limb C must **contain** 35.1989, and for limb A must **contain** 15.8807. | **STOP.** A bound that displaces the constant where the instrument is licensed is not a bound, it is a filter — the ercot-171 G-NEUT lesson, applied to this instrument. |
| **G-BOUND** | The delivery-2023 bound interval must lie **ENTIRELY OUTSIDE** the constant's identification band (limb C: ±$2.5062 around 35.1989; limb A: ±$0.9300 around 15.8807) for a **REFUTED** verdict, or **ENTIRELY INSIDE** it for **CONFIRMED**. Any interval that straddles the band edge is **NOT-IDENTIFIABLE-2023, and this lane stops with no arm.** | see §6 |
| **G-WINDOW** | The verdict must hold on **both** the matched window (h11–22 CST) and the full day, and must not depend on the CPT/CST clock convention (sensitivity reported). | Report the disagreement; a verdict that holds on only one window is **NOT-IDENTIFIABLE-2023.** |

Bands, floors and committed reads above are the identifications' own, read back
from `constants.py` and `LIMBS`; **none may be moved after measurement.**

---

## 4. THE PER-YEAR APPLICATION QUESTION, AND THE ONLY ARM THIS LANE MAY BUILD

**The question card B asks:** *how should the two COAL limbs be applied in 2023?*
Three answers were logically open — (i) unchanged (the extrapolation stands),
(ii) not applied in 2023 at all, (iii) applied at a **2023-keyed measured
level**. This lane may build **(iii) and only (iii)**, and only if §3 returns
REFUTED.

**The precedent is ercot-168's `coal_perplant_offer_yearly` (matrix item 12),**
and the arm follows it exactly:

* a **year-keyed level registry**, `COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO`, keyed
  `{ISO: {year: level}}`, consumed behind a new registered `ScenarioConfig` gate
  **`coal_peak_offer_yearly_level`** (requires `coal_peak_offer_margin`, rule 24
  `[R-REGISTRY]`; ERCOT-only, rule 25);
* a solve year **PRESENT** in the table takes its measured level; a year
  **ABSENT** (2024, 2025) falls through to `COAL_PEAK_OFFER_LEVEL_BY_ISO`
  **bit-identically** — the ercot-168 G-BIT discipline;
* the **slope is NOT re-identified**. `COAL_PEAK_OFFER_GAS_HR_BY_ISO` 10.4100 and
  the shared anchor `GAS_OFFER_MARGIN_ANCHOR_BY_ISO` 2.2494 are unchanged: one
  year cannot identify a slope, and the shared anchor is rule-19 `[R-ONE-MECH]`
  bookkeeping for the whole gas offer surface. The year table replaces the
  **LEVEL at the shared anchor**, nothing else.
* **the armed value is fixed by the instrument, never chosen.** It is the
  constant's OWN statistic on the delivery-2023 rows, with the constant's OWN
  fuel response removed, on the constant's OWN window — the point estimate
  inside §3's bound interval. **No value that moves a residual may be
  substituted for it** (rule 13; and the residual is not even read until after
  the arm is built).
* **`coal_perplant_offer_yearly` is NOT extended.** The `_peak` tranche keeps its
  ERCOT-140 owner exactly as item 12 left it; this changes that owner's 2023
  level, not who owns the tranche (rule 19).

**Limb A builds no arm** in either branch. It is CONFIRMED (ercot-171), and a
second confirmation changes nothing to arm.

**DOF (rule 23 `[R-DOF]`).** The arm adds **one measured scalar and zero fitted
scalars**. It is nonetheless a registry entry and enters the keeper's DOF ledger
with its identification source. **Independently of the outcome of this lane, and
filed at card B:** the three margin constants (`COAL_OFFER_MARGIN_LEVEL_BY_ISO`,
`CC_COMMITTED_OFFER_LEVEL_BY_ISO`, `COAL_PEAK_OFFER_LEVEL_BY_ISO` +
`COAL_PEAK_OFFER_GAS_HR_BY_ISO`) carry **no dedicated DOF-ledger entries** in the
keeper attestation. **This session adds them whatever else happens**, carrying
limb B's ercot-169 verification and limb A's ercot-171 verification into the
ledger.

---

## 5. THE A/B — pre-registered

**Recipe.** The **run191 keeper recipe, replayed unchanged** — bundle
`results/calibration/ercot191_dam_rederive_regate`, through the sanctioned
`scripts/replay_keeper.py` channel (`build_kwargs` off the committed
`meta.json`; the miso-50..53 lesson). **Full span `--year 2023 2024 2025`,
years SEQUENTIAL within each invocation and the two invocations run
one-at-a-time** (rule 12 `[R-PARALLEL]`: a per-plant ERCOT year peaked at
12.71 GB RSS on run188, and this box has 15 GB — concurrency would OOM).

* **CONTROL arm** — the replay with the gate OFF.
* **TREATMENT arm** — the identical replay `--set coal_peak_offer_yearly_level=true`.

Single delta. Both arms are registered on the dashboard (rule 15
`[R-DASHBOARD]`), **rejection included**.

| gate | statement | kind |
|---|---|---|
| **G-BIT** | 2024 and 2025 outputs must be **bit-identical** between control and arm (prices, dispatch, objective). The year table carries 2023 only; any 2024/25 motion means the implementation leaked outside its year. | **KILL** |
| **G-COAL148** | Carried **LIVE** (D2 lineage — the 2026-08-09 owner ruling, card D2 option C; PRECOMMIT-ercot172 §5). Coal dispatch above the incumbent product ceiling may not **RISE** more than **0.5 TWh in any year**, scored per plant off both bundles' own dispatch parquets by `scripts/probes/ercot185_coal148.py` against the same-HEAD control. | **KILL** |
| **G-SHED** | No **new** shed year vs the control (the ercot-48/49 manufactured-shortage falsifier). | **KILL** |
| **G-DOF** | Zero fitted scalars; the added level is the instrument's own point estimate, byte-traceable to the probe artifact. | **KILL** |
| **G-OWNER** | The standing owner guard, per year: C3a-2024 stays PASS, C3b-2024 stays under 0.20, C3a-2025 stays within its −9.1 % bound. | **REPORT + escalate** |
| **G-DET** | The determination and its fail set are re-scored and reported as measured. **No determination improvement is claimed for this lane** (§0). | report |
| **[7c] shape** | The operating-shape report gate is **reported UN-TARGETED**, as at ercot-191. | report |

**LOYO (rule 22).** The arm is a **single measured constant applied to one
year**, so leave-one-year-out within 2023–2025 is structurally N/A — 2024 and
2025 are bit-identical by G-BIT, which *is* the held-out evidence: the change
cannot buy in-sample gain anywhere but 2023. The per-year guard table stands in
its place (the ercot-173 / ercot-188 precedent).

---

## 6. KILL AND STOP RULES

1. **G-FOOT fails** → STOP. No verdict, no arm. Report the harness defect.
2. **G-NEUT fails** → STOP. The bound is a filter; report it as ercot-171's
   lesson reproduced on a second instrument, and **NOT-IDENTIFIABLE-2023
   STANDS**.
3. **G-BOUND straddles, or G-WINDOW disagrees** → STOP with **no arm**.
   NOT-IDENTIFIABLE-2023 stands, ercot-169 §6 option 1 holds, and the record
   gains a measured identification interval — which is itself the deliverable.
4. **G-BOUND returns CONFIRMED** (interval entirely inside the band) → the 2023
   application is **retired by verification** like limb A; constants comment +
   matrix + DOF ledger only, **no arm, no solve**.
5. **Any KILL gate in §5 fails** → the arm is **REJECTED-AS-ARMED**. Both arms
   are still registered (rule 15) and the matrix cell records the rejection.
6. **At every stop**, item 13's cell and evidence in the ERCOT matrix shard are
   updated **in this session** (rule 28b `[R-MECH-MATRIX]`), rejection included,
   and the calibration-log entry is written.

---

## 7. THE PROMOTION RULE — direction-blind, fixed before any residual is seen

**The keeper moves if and only if:**

1. §3 returns **REFUTED** on limb C under G-NEUT + G-BOUND + G-WINDOW; **and**
2. every **KILL** gate in §5 passes (G-BIT, G-COAL148, G-SHED, G-DOF); **and**
3. G-OWNER's per-year guards do not escalate.

**That is the whole rule, and it does not read the residual.** It is the
**standing structural standard** the owner applied at ercot-188/E2 and ercot-191:
*where the record establishes that a keeper rests on an identification the
evidence calls wrong, the structurally-faithful input is armed and the residual
moves are reported at full magnitude and are never the basis* (rules 1
`[R-STRUCT]` / 14 `[R-ACCURATE]`). A worse residual does not block the
promotion; a better one does not earn it, and — per §0 — **may not be claimed**.

If the keeper moves, the promoting session **re-stamps the ERCOT matrix shard
(keeper id + open gates) and the §5.1 header**, runs the
`calibration-keeper-auditor` agent scoped `--iso ERCOT`, and commits the keeper
`hourly/` sidecars (rule 15). ERCOT holds no `complete` marker, so no
`calibration-complete.json` re-key applies (rule 22 / D-5(b)).

---

## 8. WHAT THIS LANE DOES NOT DO

* No C3a-2023 spend, no item-11 re-opening, no card-Q re-litigation (§0).
* No C3c ledger change, no rubric amendment, no marker granted or spent.
* No change to limb A's arming, to limb B (`cc_committed_offer_margin`), or to
  `coal_perplant_offer_yearly` / `coal_perplant_offer_level`.
* No new instrument for the 2024/25 years: the committed identification stands
  and is the thing G-NEUT protects.
* No slope re-identification, no anchor movement, no licensing-floor movement.
* No per-year CT re-identification (ERCOT-147 stays REFUSED), no ercot-168
  OPTION B (stays DEFERRED).
* No GitHub Actions workflow; the solves run in-session.
