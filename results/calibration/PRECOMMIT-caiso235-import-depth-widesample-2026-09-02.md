# PRECOMMIT — caiso-235: the caiso-234 TOTAL-envelope estimator re-run on the **2019–2025** measured seam sample

**Registered 2026-09-02, session caiso-235. Branch
`claude/caiso-import-depth-widesample-hjda1q`, cut fresh from `origin/main`
(`1aa8ac14`). PUSHED BEFORE THE DERIVATION WAS EXECUTED** — not merely before the
solve. That is the caiso-234 tightening and it is now standing practice for this
lane.

Keeper at entry: **`2026-09-01-caiso-231-b1-ungrounded`**, determination
**NOT-YET**, **C3a the SOLE load-bearing FAIL** (+4.1 / +12.5 / +15.6 %); C3c the
single ledgered caveat; C6 attested; C8 PASS. CAISO holds **no `complete` and no
`final` marker**; the holdout spend freeze is **ACTIVE**.

---

## §0 — AUTHORIZATION, ESTIMATOR ORDER, AND WHAT IS ALREADY SEEN

**§0.1 — THIS IS THE THIRD EXECUTION OF THE ESTIMATOR FAMILY AND THE SECOND OF
THIS SPECIFIC ESTIMATOR.** Stated first because it is the fact a reader most needs:

| # | session | estimator | outcome |
|---|---|---|---|
| 1 | caiso-233 | NEISO port — per-corridor p98, firm carved out of each corridor, scarcity as a residue | **FAILED** both gates (CV 0.550; LOYO 491.7 %). DO-NOT-REDO. |
| 2 | caiso-234 | TOTAL envelope — `p98(TOTAL)` + `p99.9−p98` interval, zero-DOF placement | **FAILED** G-LOYO (34.2 % vs 25 %). Stop condition fired; no solve. |
| 3 | **caiso-235 (this)** | **the caiso-234 estimator, sample widened 2023–2025 → 2019–2025. Nothing else changes.** | pre-registered here |

**§0.2 — AUTHORIZATION.** FINDING-caiso234 §G escalated this DOF to the owner with
two open questions and deliberately did not act on either. The owner charter for
this session answers both, and is this document's authorization:

1. *A re-run of the caiso-234 estimator on a WIDER MEASURED SAMPLE is NOT the
   forbidden third estimator.* The two-estimator budget (PRECOMMIT-caiso234 §0.6)
   was spent on two structurally **different** constructions. This is the **same**
   estimator — same gated object, same thresholds, same zero-DOF placement
   convention — with only its sample widened. **If any part of the construction
   changes, the budget rule re-applies and this session STOPS.**
2. *Deriving a measured input over 2019–2025 EIA-930 seam flow is DATA PREP, not a
   spend*, per the owner clarification of 2026-08-06: **"WHAT IS HELD OUT IS THE
   SCORE, NEVER THE DATA … Data intake needs NO per-ISO/per-window authorization
   and no marker."**

**This is NOT a lever-hunting authorization.** The caiso-201 resting ruling stands:
this is a rule-14 / rule-21 structural-integrity and DOF-closure lane, and **C3a is
never its objective**.

**§0.3 — THE HOLDOUT LINE THIS SESSION WILL NOT CROSS.** No year outside 2023–2025
is **SOLVED, SCORED or REGISTERED**, and **no model output and no measured actual**
from any such year is read. The only thing read from 2019–2022 is **EIA-930
corridor net-flow percentiles**. Any solve reached under §7 runs `--year 2023 2024
2025` and nothing else. `calibration-complete.json` and `holdout-freeze.json` are
untouched.

**§0.4 — EXCLUDE 2026.** The committed extract
(`data/raw/eia-930-interchange/CISO interchange hourly.parquet`) runs
**2018-12-31 → 2026-06-30**. H1-2026 is **LOCKED-TEST tier** and inside the active
freeze's scope, so **the sample is capped at 2025**. The 2018 tail (88 stamps, a
timezone artifact of the 2019-01-01 boundary) is likewise outside the programme's
working span and is excluded by the same year filter. `YEARS_WIDE = 2019…2025`,
seven complete years.

**§0.5 — WHAT IS ALREADY SEEN, stated against interest.** Committed on `main`
before this session, in `_caiso233_import_depth_decomp.json` and
`_caiso234_import_total_envelope.json`:

* all three **2023 / 2024 / 2025** per-year percentiles — `p98(TOTAL)` 7,873 /
  7,805 / 8,845 and `p99.9(TOTAL)` 9,630 / 9,112 / 10,435 MW, hence the three
  per-year intervals 1,757 / 1,307 / 1,590;
* the three-year gate result: CV 0.058 / 0.120 (**ok**) and the **34.2 %
  hold-2024 LOYO miss** that failed the estimator;
* the diagnosis that the miss is **sample length**, not construction (a p99.9 of an
  8,759-hour year rests on its 9 highest hours; 2024's p98 is within 0.9 % of
  2023's and its annual max is *higher*, yet its p99.9 is 518 MW lower).

**So the DIRECTION of improvement is foreseen and is claimed as no part of this
session's evidence.** Widening a sample that failed for being short is expected to
help; that expectation is exactly why the gate must be genuinely unseen to be
worth anything.

**§0.6 — WHAT IS GENUINELY UNSEEN.** Nothing on disk determines any of it:

* **every 2019, 2020, 2021 and 2022 percentile** — four of the seven per-year
  values of each gated component, never computed in this repository;
* **all seven LOYO folds**, each trained on a pooled six-year sample (a pooled
  percentile is the tail of a *mixture* and is not a function of the per-year
  percentiles — FINDING-caiso234 §B4);
* every pooled seven-year percentile, every pooled corridor weight, and every
  delivered rung value.

**G-LOYO on seven folds is the load-bearing gate.** It killed the price limb
(30.5 %, caiso-86b), the caiso-233 port (491.7 %) and the caiso-234 three-year run
(34.2 %).

**§0.7 — THE HONEST OBJECTION TO THIS SESSION, and it is not answered away.**
Re-running an estimator on more data *after* seeing it fail is a re-test, and a
re-test is a second chance. Three things are offered, none of which is a claim that
the objection is void:

1. The construction is **frozen and imported, not retyped** — §2's gated object is
   executed by calling `derive_caiso_import_total_envelope.derive_envelope`
   itself, so it is byte-identically the function that failed. The only new code
   is the year list and the §4(b) fork.
2. The remedy was **specified by the failing session in committed bytes**
   (FINDING-caiso234 §G) as the *only* candidate route, on the stated structural
   ground that the failure is a 3-observation problem in an extreme-tail order
   statistic — before any 2019–2022 number existed.
3. **This is the last one.** §6 makes it terminal in both directions: seven years
   of measured seam flow is the whole record this repository can bring, so a
   failure here closes the object **from data rather than from effort**, and the
   DOF returns to the owner as permanently declared.

**§0.8 — BUDGET, RESTATED. There is no fourth construction and no eighth year.**
If the gates fail, this session files the FINDING and stops. It does not soften a
bar, re-scope the gated object, admit a passing component, fall back to a
residual-tuned depth, propose a further widening, or reach for another estimator.

## §1 — THE OBJECT (unchanged)

The four `IMPORT_TRANCHES["CAISO"]` SPOT capacities
(`src/market_sim/model/interchange/spec.py:349`), which
`scripts/probes/_caiso186os_dof_repair.py` labels **`RESIDUAL (static, no cited
primary source)`** — CAISO's last uncited DOF:

| rung | MW | limb |
|---|--:|---|
| `PNW_midC` | 1,800 | SPOT — **ungrounded** |
| `DSW_CCGT` | 1,800 | SPOT — **ungrounded** |
| `DSW_CT` | 2,200 | SPOT — **ungrounded** |
| `WECC_scarcity` | 3,000 | SPOT — **ungrounded** |
| | **8,800** | |

`PNW_hydro_base` (1,072 / 1,558 / 1,566) and `DSW_solar_PV` (1,251 / 1,813 /
1,805) are the MIC-measured per-year FIRM pair and are **held FIXED throughout** —
re-opening a grounded rung to move a residual is rule 1 `[R-STRUCT]`.

## §2 — THE GATED OBJECT (verbatim from PRECOMMIT-caiso234 §2; UNCHANGED)

Two direct statistics of the TOTAL corridor net-import distribution
(`WECC_PNW + WECC_DSW`, EIA-930 CISO interchange on the model clock via
`corridor_net_import` / `CAISO_CORRIDOR_DIBA`):

    routine_total     = p98  ( TOTAL net import )
    scarcity_interval = p99.9( TOTAL ) - p98( TOTAL )
    ladder_total      = routine_total + scarcity_interval  =  p99.9( TOTAL )

* **No firm carve-out enters the gated object.** The firm block sits *inside* the
  derived total; the CV-0.16 DMM/MIC measurement never touches a gated statistic.
  **This is why the gates run cleanly on seven years** — the gated object has no
  dependence on any per-year quantity that is unavailable before 2023.
* **Scarcity is an INTERVAL, never a residue.**
* `CAP_PCTL = 98.0` / `SCARCITY_PCTL = 99.9`, imported unchanged from
  `derive_caiso_import_depths.py`. **Not settable by this session.**
* Executed by **importing** `derive_envelope` from
  `scripts/data/derive_caiso_import_total_envelope.py` — the caiso-234 function
  itself, not a re-implementation.

**THE ONE CHANGE, and the whole of it:** the pooled sample is
`YEARS_WIDE = (2019, 2020, 2021, 2022, 2023, 2024, 2025)` instead of
`(2023, 2024, 2025)`. `corridor_net_import()` gains an optional `years` argument
defaulting to its existing `YEARS`, so every one of its fifteen existing callers is
byte-unaffected.

## §3 — PRE-REGISTERED HONESTY GATES (constants unchanged, and NOT settable here)

Imported from `derive_caiso_import_tranches.py` (`CV_MAX` / `LOYO_MAX`, already on
`main` — the same bar the price limb was held to and failed):

* **G-STABILITY** — CV across the **seven** years of **each** of `routine_total`
  and `scarcity_interval` ≤ **0.20**. *(Partly foreseen — three of seven per-year
  values are committed; four are not.)*
* **G-LOYO** — derive both components on the pooled **other six** years, predict
  the held-out year's own values; worst held-out relative error ≤ **0.25**, over
  **seven folds**. *(Unseen — the load-bearing gate.)*

Both must pass. Neither is softenable.

**§3.1 — PRE-REGISTERED NEAR-MISS RULE, because this is exactly where a bar gets
softened.** If the worst fold lands **between 25 % and 30 %**, **that is a FAIL.**
It is not "essentially at the bar", not "a material improvement on 34.2 %", and not
a candidate for a caveat, a partial swap or a reported-not-gated admission. Said in
advance, before any number exists, so it cannot be re-argued afterwards. The same
applies to a CV that lands between 0.20 and 0.25.

## §4 — PLACEMENT CONVENTION (ZERO DOF; verbatim from PRECOMMIT-caiso234 §4, with ONE pre-registered fork)

Unchanged and mechanical:

**(a) Corridor weights.** `w_c = p98_pooled(c) / Σ_c p98_pooled(c)` — the pro-rata
reconciliation of the two marginal corridor depths to the coherent total, removing
the measured simultaneity gap. Zero parameters.

**(b) Corridor routine depth.** `routine_c = routine_total × w_c`, then
`spot_routine_c = max(0, routine_c − firm_c)`.

**(c) Within-corridor split.** Equal MW among that corridor's spot rungs —
`WECC_PNW` → (`PNW_midC`); `WECC_DSW` → (`DSW_CCGT`, `DSW_CT`). The NYISO/NEISO
rung convention; the split point is fixed by the convention, never chosen.

**(d) Scarcity.** `WECC_scarcity = scarcity_interval`, on its incumbent PALOVRDE
(`WECC_DSW`) node. Placement unchanged; only the depth is derived.

**(e) Rounding** to 5 MW (`_round_cap`).

**(f) PRICES ARE UNCHANGED.** Capacity limb only. The price Q-Q route is
**DO-NOT-REDO** (`derive_caiso_import_tranches.py`, LOYO 30.5 %, caiso-86b) — and
note that its `RUNGS` map covers **all five** priced rungs **including the two firm
ones**, so the firm *prices* are adjudicated by that same failure.

**(g) POOLED → ONE STATIC ladder.** The FIRM rows of every by-year entry keep their
measured per-year values.

### §4-FORK — THE IMPLEMENTATION FORK, DECIDED HERE, BEFORE EXECUTION

The gated object needs no firm block, but the **placement** step (b) subtracts a
per-year measured MIC firm block, and `IMPORT_TRANCHES_BY_YEAR["CAISO"]` holds
**only 2023 / 2024 / 2025**. The charter requires one of two options, chosen now
with its reasoning and **not switched after seeing which ladder is preferable**:

> **(a) CHOSEN — gate on 2019–2025 and place using the 2023–2025 measured firm
> mean**, on the ground that the firm block is a separately-grounded quantity with
> its own vintage.
>
> (b) REJECTED — extend the DMM RA × MIC intake back to 2019 as further data prep.

**Why (a), on the merits and not on convenience** — three reasons, the first
decisive:

1. **(b) would re-open a grounded rung, which rule 1 `[R-STRUCT]` forbids and this
   charter forbids by name** ("PNW_hydro_base and DSW_solar_PV stay FIXED").
   Deriving a seven-year firm mean would change `firm_c`, and `firm_c` is the
   measured DMM RA × MIC quantity — the *grounded* half of the ladder. This lane
   exists to close the **ungrounded** limb; moving the grounded one to absorb a
   wider flow sample is precisely the act the lane refuses.
2. **The two quantities have genuinely different vintages and different sources.**
   Corridor flow is EIA-930 telemetry, published for every year on one basis. The
   firm block is CAISO's *annual* "Maximum RA Import Capability" determination ×
   the DMM RA import capacity — a contracting quantity re-set each year by a
   regulatory process, whose provenance block already records that the static entry
   deliberately "carries the latest grounded (2025) volumes as the forward story".
   Averaging it over a 2019 fleet is not a longer measurement of the same object.
3. **It confines the widening to one place.** §0.2(1) authorizes a sample change
   and nothing else; adding a second measured input in the same session would be a
   construction change and would re-arm the budget rule.

**Mechanically:** `firm_c` is the mean of the committed measured MIC blocks over
`FIRM_REFERENCE_YEARS = (2023, 2024, 2025)` — **the same constant in every fold and
in every per-year diagnostic**, never a function of the sample years. This is a
strict simplification of caiso-234's `firm_c` (which averaged over whichever years
were in the fold), and it is disclosed as such.

**§4-FORK-CHECK, pre-registered:** the widened script asserts that its placement
reproduces caiso-234's delivered pooled ladder **exactly** when run on the
2023–2025 sample (`PNW_midC` 1,065 / `DSW_CCGT` 2,100 / `DSW_CT` 2,100 /
`WECC_scarcity` 1,795 = 7,060 MW). If it does not, the fork is not the neutral
re-expression claimed here and this session **stops and reports that instead**.

## §5 — REPORTED AT FULL MAGNITUDE, NOT GATED

The FINDING will publish, whatever they say, and without re-scoping anything on the
strength of them:

1. all seven per-year gated components and per-year implied rung capacities, with
   their CVs — **including the four never-before-computed years**;
2. per-rung LOYO under the §4 placement — **caiso-233's own per-rung bar applied to
   this ladder**, which both predecessors failed;
3. the per-year corridor weights `w_c` and the simultaneity gap;
4. delivered vs incumbent, per rung and in total;
5. the **rule-14 EIA-930 sign check** on all seven years (every gated percentile
   must be strongly positive; the negative-hour share is reported per corridor);
6. the **sample-adequacy record**, measured before this document was written and
   reported whatever it shows: all 11 CISO DIBAs are present in all seven years,
   with per-DIBA non-null hourly coverage of 8,563–8,784 rows/year. `PACW` is the
   one gappy series (8,563 in 2022 to 8,761 in 2020; 8,702–8,730 in 2023–2025) and
   the `groupby.sum()` in `corridor_net_import` treats a missing DIBA-hour as a
   zero contribution rather than a null. **That behaviour is pre-existing and
   unchanged** — it applied identically to the 2023–2025 run — but it slightly
   understates `WECC_PNW` in the affected hours, and 2022's gap is the largest in
   the sample. Disclosed here rather than discovered later.

## §6 — STOP CONDITION (pre-registered, and TERMINAL)

If **either** gate in §3 fails — including a §3.1 near miss — **file the FINDING
and do NOT solve.** Do not soften a threshold; do not re-scope the gated object; do
not admit whichever component passes (caiso-234 §C refused a **cleanly passing**
`routine_total` on exactly this ground); do not fall back to a residual-tuned
depth; **do not propose a further widening or a fourth construction.**

**Seven years of measured seam flow is the whole record.** A failure here closes
the object **from data, not from effort**, and the FINDING must report it in those
words and return the DOF to the owner as **permanently declared**.

## §7 — PRE-REGISTERED SOLVE DESIGN (reached ONLY on a gate PASS)

* **A0 control** — `--replay-bundle results/calibration/caiso231_b1_ungrounded` at
  this HEAD, isolating the delta from HEAD drift.
* **B1 treatment** — the same, plus the derived depths as the **ONLY** delta, armed
  by a new **default-off** `ScenarioConfig` gate **`caiso_import_depth_measured`**
  so both arms run at ONE HEAD and the incumbent literals stay untouched for every
  other lane. Rule 28(c): its base mechanism-matrix row plus a cell line in **every**
  ISO shard land in the same PR; the CAISO cell verdict (rule 28(b)) is this
  session's to move.
* `--year 2023 2024 2025` in **ONE invocation, years sequential** (rules 12/16) —
  **the solve stays inside the training window regardless of the derivation's
  sample.** The two invocations launched concurrently (rule 12's cap of 2 for
  CAISO's per-plant multi-zone LP). Scored on **P1**. **Both arms registered**
  (rule 15).

## §8 — PRE-REGISTERED C3a DIRECTION AND MAGNITUDE

Baseline (committed artifacts, `2026-09-01-caiso-231-b1-ungrounded`):
**2023 +4.1 % (pass) / 2024 +12.5 % FAIL / 2025 +15.6 % FAIL.**

* **DIRECTION (the falsifiable claim): NEGATIVE in all three years.** The derived
  ladder is *shallower* than the incumbent — FINDING-caiso234 §F4 measures the
  incumbent stack **1,493 / 3,059 / 1,736 MW deeper** than the measured p99.9 total
  envelope — so B1 removes above-market import depth, and FINDING-caiso232 §D's
  corr(monthly residual, model import volume) = **+0.419** means less import volume
  must move λ **down**.
* **MAGNITUDE: |ΔC3a| ≤ 3 pp per year.** FINDING-caiso202 §C attributes **< 5 %**
  of the C3a positive gap directly to the import legs. **A depth change cannot
  close C3a and is not meant to.**
* **CHANNEL CHECK (pre-registered so a null is not re-interpreted after the fact).**
  The keeper runs `caiso_corridor_flow_limit=True`, so each corridor's import is
  already clipped hour-by-hour at its measured (month × hour-of-day) p95
  deliverability envelope, and both corridors sit far inside their physical link
  TTCs (COI ≈ 4,800 MW; Path-46/WOR ≈ 10,623 MW). **A near-zero ΔC3a with
  substantially unchanged model import volume is an ADMISSIBLE, ANTICIPATED and
  KEEPER-ELIGIBLE outcome** — it means the measured envelope binds before the rung
  depth does, and the derivation is a structural regrounding with no residual
  signature. A move **larger** than 3 pp means an undeclared channel: **diagnose
  it, do not bank it.**
* **This is a DOF-closure lane, not a residual lane.** Per rule 1 `[R-STRUCT]` the
  derivation is **never** weighed against the price residual: a C3a regression does
  not veto a grounded depth, and a C3a improvement does not license an ungrounded
  one. The owner's standing standard applies verbatim — *"If structural integrity
  improves but gates regress that may still be a keeper."*

## §9 — OUTCOME (recorded 2026-09-02, same session)

**THE STOP CONDITION FIRED, ON BOTH GATES.**

* **G-STABILITY FAIL** — `scarcity_interval` CV **0.266** against the 0.20 bar
  (`routine_total` 0.108, ok).
* **G-LOYO FAIL** — worst held-out error **55.0 %** against the 25 % bar, with
  **five of seven folds failing** (14.9 / **55.0** / 18.3 / **34.8** / **36.9** /
  **27.2** / **29.7 %**).

**The §3.1 near-miss rule fired as written.** Hold-2025 (29.7 %) and hold-2024
(27.2 %) landed in the pre-declared 25–30 % band that this document fixed in
advance as a **FAIL**. It changed no verdict — hold-2020's 55.0 % settles it — but
it was there for a case where it might have, and it did not have to be argued.

**The §4-FORK-CHECK passed exactly**: on the 2023–2025 sample the fork-(a)
placement reproduces caiso-234's committed ladder to the MW (1,065 / 2,100 / 2,100
/ 1,795 = 7,060), so every difference reported is attributable to the sample alone.

**No LP was built and no solver was called.** §7's arms were never run; nothing is
registered. The bar was not moved, the gated object was not re-scoped, no component
was admitted after seeing which passed — and this time **none passed**, including
`routine_total`, the quantity caiso-234 §C refused reluctantly and recorded as the
strongest the lane had produced.

**One correction to this document, against interest, and it is the substance of
the result.** §0.5 recorded the caiso-234 diagnosis — that the obstacle is **sample
length** — as established and foreseen, and §0.5 conceded that a widening was
therefore *expected* to help. **The execution falsified the diagnosis.** The
obstacle is a **REGIME BREAK at the 2022/2023 boundary**: `p98(TOTAL)` runs
10,070 MW over 2019–22 (CV **0.023**) and 8,174 MW over 2023–25 (CV 0.058), a
−18.8 % level shift, while the scarcity interval moves **+54.2 %** the other way.
The extra years are not more observations of the same quantity. The direction of
improvement this document said was foreseen **did not materialise, and the reason
it did not is the finding.**

**Per §6 the outcome is TERMINAL.** Seven years of measured seam flow is the whole
record; the object is closed **from data, not from effort**; no further widening and
no fourth construction is proposed. DOF ledger `spot_capacity`: **CLOSED as NOT
IDENTIFIABLE** from EIA-930 seam flow and returned to the owner permanently
declared.

Full result, the regime-break decomposition, the §5 diagnostics published as
promised, and the §E withdrawal of caiso-233/234's over-depth bound as a standing
fact: `FINDING-caiso235-import-depth-widesample-2026-09-02.md`.
