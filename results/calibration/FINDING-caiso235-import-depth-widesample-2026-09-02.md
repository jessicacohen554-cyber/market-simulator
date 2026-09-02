# FINDING — caiso-235: the wider sample **FAILS BOTH gates** — G-STABILITY CV **0.266** and G-LOYO **55.0 %**, five of seven folds — and it fails for a reason the caiso-234 diagnosis got WRONG. The obstacle is not sample length; it is a **REGIME BREAK between 2022 and 2023**. CAISO's measured seam envelope is **not one object over 2019–2025**: `p98(TOTAL)` runs **10,070 MW (2019–22, CV 0.023)** and **8,174 MW (2023–25, CV 0.058)** — two tightly-stable regimes separated by a **−18.8 % level shift** — while the scarcity interval moves the *other* way (**+54.2 %**). The lane's strongest quantity, `routine_total`, which cleared both gates cleanly on three years (LOYO ≤ 11.5 %), **now FAILS at 26.1 / 27.2 %** the moment a fold trains across the break. Disclosed against interest: the incumbent 8,800 MW ladder is over-deep by **only 449–1,036 MW** against the 2019–2022 envelope versus 1,493–3,059 MW against 2023–2025, so **caiso-234 §F4's over-depth bound is regime-specific, not a standing fact.** The pre-registered stop condition fired: **NO SOLVE.** Per PRECOMMIT §6 this is **TERMINAL** — seven years of measured seam flow is the whole record, so the object is closed **from data, not from effort**, and the DOF returns to the owner **permanently declared**. NO LP, NO SOLVE — committed bytes only (2026-09-02)

**Keeper `2026-09-01-caiso-231-b1-ungrounded` UNCHANGED. No mechanism armed, no
`ScenarioConfig` field added, no LP built, no solver called, nothing registered,
no matrix cell verdict moved.** `calibration-complete.json` (no CAISO marker) and
`holdout-freeze.json` (ACTIVE) untouched. **No year outside 2023–2025 was solved,
scored or registered, and no model output and no measured actual from any such year
was read** — EIA-930 corridor net-flow percentiles only, per the owner grant and
the 2026-08-06 clarification.

Pre-registration: `PRECOMMIT-caiso235-import-depth-widesample-2026-09-02.md`,
**pushed to `origin` before the derivation was executed** (commit `dc7257f5`,
branch `claude/caiso-import-depth-widesample-hjda1q`), not merely before the solve.
§9 of that document records this outcome.

Instruments (committed):

* `scripts/data/derive_caiso_import_depth_widesample.py` — the re-run, both gates,
  the §4-FORK-CHECK and the §5 ungated diagnostics.
* `results/calibration/_caiso235_import_depth_widesample.json`.
* `scripts/data/derive_caiso_import_tranches.py` — `corridor_net_import` gains an
  optional `years` argument defaulting to its existing `YEARS`. **That is the only
  edit to any pre-existing file in this session**, and all fifteen existing callers
  are byte-unaffected.

Every number reproduces from `data/raw/eia-930-interchange/CISO interchange
hourly.parquet` on the model clock (`_caiso_interchange_model_clock`,
`CAISO_CORRIDOR_DIBA`). `CAP_PCTL`, `SCARCITY_PCTL`, `CV_MAX` and `LOYO_MAX` are
all imported from files already on `main`; none was settable by this session.

---

## §0 — WHAT THIS SESSION WAS AND WAS NOT

**The estimator is NOT new, and that is verifiable rather than asserted.** §2's
gated object is computed by **calling caiso-234's own `derive_envelope`**, imported
from `scripts/data/derive_caiso_import_total_envelope.py`. The single
pre-registered change is the pooled sample: `YEARS_WIDE = 2019…2025` instead of
`2023…2025`. Percentile constants, gate thresholds, the placement convention, the
rung inventory and the node placement are all unchanged.

**The §4-FORK-CHECK passed exactly**, as pre-registered. On the 2023–2025 sample
the caiso-235 placement (with `firm_c` fixed to the 2023–2025 measured MIC mean —
PRECOMMIT §4-FORK option **(a)**) reproduces caiso-234's delivered pooled ladder to
the MW:

| rung | caiso-234 committed | caiso-234 replayed | caiso-235 fork (a) |
|---|--:|--:|--:|
| `PNW_midC` | 1,065 | 1,065 | 1,065 |
| `DSW_CCGT` | 2,100 | 2,100 | 2,100 |
| `DSW_CT` | 2,100 | 2,100 | 2,100 |
| `WECC_scarcity` | 1,795 | 1,795 | 1,795 |

So the fork is the neutral re-expression the PRECOMMIT claimed, and **every
difference reported below is attributable to the sample and to nothing else.**

**2026 was excluded**, as pre-registered: the extract runs 2018-12-31 → 2026-06-30,
and H1-2026 is LOCKED-TEST tier inside the active freeze's scope. The 2018 tail
(88 stamps, a timezone artifact of the year boundary) is outside the programme's
2019–2025 working span and excluded by the same filter. Every year in the sample
carries **n = 8,759** hours on the model clock.

## §A — THE RESULT: BOTH GATES FAIL

**G-STABILITY** — CV across the seven years of each gated component, bar **0.20**:

| component | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | pooled | CV | gate |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|:--|
| `routine_total` = p98(TOTAL) | 9,802 | 10,202 | 10,372 | 9,905 | 7,873 | 7,805 | 8,845 | 9,842 | 0.108 | ok |
| `scarcity_interval` = p99.9−p98 | 1,319 | 824 | 1,001 | 881 | 1,757 | 1,307 | 1,590 | 1,143 | **0.266** | **FAIL** |
| *(reported)* `ladder_total` = p99.9 | 11,121 | 11,026 | 11,373 | 10,785 | 9,630 | 9,112 | 10,435 | 10,984 | 0.074 | — |

**G-LOYO** — derive on the pooled other six years, predict the held-out year, bar
**25 %**. **Five of seven folds FAIL:**

| held out | `routine_total` | `scarcity_interval` | worst | G-LOYO |
|---|--:|--:|--:|:--|
| 2019 | 0.5 % | 14.9 % | 14.9 % | ok |
| **2020** | 4.9 % | **55.0 %** | **55.0 %** | **FAIL** |
| 2021 | 6.6 % | 18.3 % | 18.3 % | ok |
| **2022** | 0.8 % | **34.8 %** | **34.8 %** | **FAIL** |
| **2023** | **26.1 %** | **36.9 %** | **36.9 %** | **FAIL** |
| **2024** | **27.2 %** | 15.2 % | **27.2 %** | **FAIL** |
| **2025** | 12.1 % | **29.7 %** | **29.7 %** | **FAIL** |

**G-STABILITY FAIL | G-LOYO FAIL ⇒ FAIL.** The pre-registered stop condition
fired. **No LP was built and no solver was called.** PRECOMMIT §7's arms were never
run, so there is nothing to register (rule 15 applies to completed runs — the
caiso-134/140/150/202/232/233/234 disposition).

**The §3.1 near-miss rule fired as designed and is recorded as such.** Two folds —
hold-2025 at 29.7 % and hold-2024 at 27.2 % — landed in the pre-declared 25–30 %
band that the PRECOMMIT fixed in advance as a **FAIL**, not "essentially at the
bar". It made no difference to the verdict (hold-2020's 55.0 % settles it four
times over), which is the only circumstance in which a pre-registered tripwire is
worth anything: it was written for a case where it might have mattered, and it did
not have to be argued.

**The widening moved the answer in the wrong direction on the gate that mattered.**
Against the three-year run on the identical construction:

| gate | caiso-234 (3 yr) | caiso-235 (7 yr) |
|---|--:|--:|
| CV `routine_total` | 0.058 ok | 0.108 ok |
| CV `scarcity_interval` | 0.120 ok | **0.266 FAIL** |
| worst LOYO | 34.2 % FAIL (1 of 3 folds) | **55.0 % FAIL (5 of 7 folds)** |

## §B — THE DIAGNOSIS: a REGIME BREAK, and the caiso-234 diagnosis was WRONG

**§B1 — the seven-year sample is not seven draws of one object.** Split it at the
2022/2023 boundary and both sub-samples are *tighter* than the pooled one:

| component | 2019–22 mean | 2019–22 CV | 2023–25 mean | 2023–25 CV | shift | 7-yr CV |
|---|--:|--:|--:|--:|--:|--:|
| `routine_total` | **10,070** | **0.023** | **8,174** | 0.058 | **−1,896 (−18.8 %)** | 0.108 |
| `scarcity_interval` | 1,006 | 0.190 | 1,551 | 0.120 | **+545 (+54.2 %)** | **0.266** |
| `ladder_total` | 11,076 | 0.019 | 9,726 | 0.056 | −1,351 (−12.2 %) | 0.074 |

Read the `routine_total` row plainly: **within 2019–2022 the routine total is
stable to a CV of 0.023** — four years of measured flow agreeing to ±2 % — and
within 2023–2025 to 0.058. **The seven-year CV of 0.108 is almost entirely the
gap BETWEEN the two regimes, not noise within either.** The same is true of the
scarcity interval, whose within-regime CVs (0.190 and 0.120) both sit inside the
0.20 bar while the pooled CV of 0.266 fails it.

**§B2 — the break is on both corridors, and it is physically legible.**

| corridor p98 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 19–22 → 23–25 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| `WECC_PNW` | 2,974 | 3,673 | 3,413 | 3,548 | 2,841 | 2,566 | 2,713 | 3,402 → 2,707 (**−20.4 %**) |
| `WECC_DSW` | 7,617 | 7,470 | 7,528 | 6,934 | 6,001 | 6,365 | 6,646 | 7,387 → 6,337 (**−14.2 %**) |

The rule-14 sign check — run for its own reasons — measures the mechanism
directly. The share of hours in which the corridor is a **net export**:

| corridor, negative-hour share | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|--:|--:|--:|
| `WECC_PNW` | 17.1 % | 3.8 % | 9.9 % | 17.7 % | **51.0 %** | **38.4 %** | **30.8 %** |
| `WECC_DSW` | 0.0 % | 0.3 % | 0.6 % | 1.4 % | 5.8 % | 5.4 % | 4.9 % |
| TOTAL | 0.8 % | 0.3 % | 1.1 % | 1.8 % | 14.2 % | 11.4 % | 9.1 % |

**The northern seam flipped.** Through 2022 CAISO imported on the PNW corridor in
82–96 % of hours; from 2023 it exports in **31–51 %** of them. That is CAISO's
in-state solar-plus-storage build displacing routine daytime imports, and it is the
same physical change that drops routine depth by ~1.9 GW while pushing the residual
reliance on deep imports into **fewer and more extreme** hours — which is exactly
the sign of the scarcity interval's **+54.2 %** move. **The two gated components
move in OPPOSITE directions across the break**, which no single pooled percentile
ladder can represent.

**§B3 — this FALSIFIES the caiso-234 §B2/§G diagnosis, and that is stated plainly
rather than folded into a caveat.** FINDING-caiso234 concluded that the obstacle
was **sample length** — a 9-hour-per-year order statistic with n = 3 — and named a
longer sample as the direct remedy, expecting ~61 tail hours and six extra folds.
**The mechanism it identified is real and its arithmetic was right; its inference
was wrong.** More years did not average the tail shape out, because the extra years
are not more observations of the same quantity — they are observations of a
**different market**. The sample-length reading was only ever available *because*
the three-year window sat entirely inside one regime, which made 2024's narrow tail
look like idiosyncratic noise rather than what §B1 now shows it to be: within-regime
variation on a level that had already shifted.

**§B4 — the honest consequence, stated before anyone offers it as a rescue.** §B1
invites an obvious move: *the object is stable within each regime, so derive on the
recent regime alone.* **That move is not available, twice over.** First, deriving on
2023–2025 alone **is caiso-234**, and it FAILED — its scarcity leg missed at 34.2 %.
Second, any regime-aware form — a break dummy, a regime-restricted percentile, a
recency weighting — is a **different construction**, which PRECOMMIT §0.2 and §0.8
forbid absolutely: the owner grant licensed a widened sample and nothing else, and
the estimator budget re-arms the instant the construction changes. **There is no
third construction and no eighth year.**

## §C — WHAT NEWLY BROKE: the lane's strongest quantity

`routine_total` was the single most robust thing these three sessions produced.
FINDING-caiso234 §F2 recorded it as **"IDENTIFIABLE from three years"** — CV 0.058,
out-of-sample error 7.0–11.5 % — and §C refused it as a partial swap *purely* on
the pre-registration, conceding that "no such argument is available here" for
refusing it on the merits.

**On the wider sample it FAILS G-LOYO at 26.1 % (hold-2023) and 27.2 %
(hold-2024).** The mechanism is transparent: those are the two folds whose training
sets are dominated by the *other* regime, so the prediction is pulled toward the
pre-2023 level of ~10.1 GW against actuals of 7.8–7.9 GW. Symmetrically, the
2019–2022 folds predict at **0.5–6.6 %** — the earlier regime's four years predict
each other almost perfectly.

**This is the most consequential single number in the finding, and it cuts against
the lane's own prior direction.** The quantity caiso-234 was closest to admitting,
and that a reader might reasonably have argued should have been admitted, is
**out-of-sample invalid across the regime break**. Had the partial swap been taken
on the three-year evidence, this session would be reporting that a *grounded* rung
had been sized on a window that concealed a 1.9 GW structural shift. **The
pre-registration that refused it did real work**, and that is worth recording
precisely because it was refused reluctantly.

## §D — THE DELIVERED LADDER IS NOT STABLE TO THE SAMPLE CHOICE

The §4 placement, unchanged, on the two samples:

| rung | caiso-234 (2023–25) | caiso-235 (2019–25) | incumbent | Δ estimator |
|---|--:|--:|--:|--:|
| `PNW_midC` | 1,065 | **1,730** | 1,800 | **+665 (+62 %)** |
| `DSW_CCGT` | 2,100 | **2,545** | 1,800 | +445 (+21 %) |
| `DSW_CT` | 2,100 | **2,545** | 2,200 | +445 (+21 %) |
| `WECC_scarcity` | 1,795 | **1,145** | 3,000 | **−650 (−36 %)** |
| **TOTAL SPOT** | **7,060** | **7,965** | **8,800** | **+905 (+12.8 %)** |

**The same estimator, the same convention, one sample change — and the delivered
ladder moves by 12.8 % in total and by 36–62 % on two of four rungs, in opposite
directions.** A quantity whose derived value swings that far on the choice of
measurement window is **not identified**, independently of any gate. This is the
plainest statement of the result and it does not require reading a CV: **there is
no fact of the matter about these four depths that seven years of EIA-930 flow can
settle.**

## §E — AGAINST INTEREST: the incumbent is NOT badly over-deep. caiso-234 §F4's bound is REGIME-SPECIFIC

This reframes the direction the lane has been travelling in since caiso-233, and it
is reported first rather than buried.

| year | measured p98 | measured p99.9 | incumbent full ladder | **over-depth vs p99.9** |
|---|--:|--:|--:|--:|
| 2019 | 9,802 | 11,121 | 11,822 † | **+701** |
| 2020 | 10,202 | 11,026 | 11,822 † | **+796** |
| 2021 | 10,372 | 11,373 | 11,822 † | **+449** |
| 2022 | 9,905 | 10,785 | 11,822 † | **+1,036** |
| 2023 | 7,873 | 9,630 | 11,123 | +1,493 |
| 2024 | 7,805 | 9,112 | 12,171 | +3,059 |
| 2025 | 8,845 | 10,435 | 12,171 | +1,736 |

† 2019–2022 have no committed MIC firm vintage, so the incumbent ladder for those
years is shown as the 8,800 MW spot literals plus the fork-(a) firm reference
(3,022 MW). Flagged, not smoothed: the firm block is the one quantity this row
cannot state on its own vintage.

**FINDING-caiso233 §E and FINDING-caiso234 §F4 both recorded "the incumbent ladder
is over-deep against the measured envelope by 1,493 / 3,059 / 1,736 MW" as a
durable measured fact. It is not durable — it is a statement about 2023–2025.**
Against the 2019–2022 envelope the same 8,800 MW literals are over-deep by only
**449–1,036 MW**, i.e. within ~4–9 % of the measured p99.9 total.

**The implication is uncomfortable and is stated anyway: the incumbent literals
look like a defensible representation of the seam as it behaved through 2022, which
CAISO's solar-and-storage build has since moved out from under.** They remain
correctly labelled `RESIDUAL (static, no cited primary source)` — nothing here
supplies the missing citation, and a plausible-looking number is not a grounded
one. But the lane's working characterisation of them as *measurably too deep* was
resting on a three-year window, and this session removes that support rather than
keeping it.

## §F — §5 DELIVERED: the ungated per-rung diagnostics, at full magnitude

PRECOMMIT §5 committed in advance to publishing these whatever they said.

**Per-rung stability under the §4 placement (REPORTED, NOT GATED):**

| rung | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | pooled | CV | *(caiso-234 CV)* |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `PNW_midC` | 1,355 | 1,965 | 1,835 | 1,955 | 1,130 | 845 | 1,165 | 1,730 | **0.286** | *0.304* |
| `DSW_CCGT` | 2,715 | 2,610 | 2,755 | 2,465 | 1,860 | 1,970 | 2,330 | 2,545 | 0.137 | *0.073* |
| `DSW_CT` | 2,715 | 2,610 | 2,755 | 2,465 | 1,860 | 1,970 | 2,330 | 2,545 | 0.137 | *0.073* |
| `WECC_scarcity` | 1,320 | 825 | 1,000 | 880 | 1,755 | 1,305 | 1,590 | 1,145 | **0.265** | *0.120* |

**Per-rung LOYO — caiso-233's own bar applied to this ladder:**

| held out | `PNW_midC` | `DSW_CCGT` | `DSW_CT` | `WECC_scarcity` | worst |
|---|--:|--:|--:|--:|--:|
| 2019 | 31.7 % | 7.2 % | 7.2 % | 14.8 % | 31.7 % |
| 2020 | 17.3 % | 3.3 % | 3.3 % | **55.2 %** | **55.2 %** |
| 2021 | 7.6 % | 9.8 % | 9.8 % | 18.5 % | 18.5 % |
| 2022 | 14.8 % | 4.5 % | 4.5 % | 34.7 % | 34.7 % |
| 2023 | **55.3 %** | 38.4 % | 38.4 % | 36.8 % | **55.3 %** |
| 2024 | **108.9 %** | 30.5 % | 30.5 % | 14.9 % | **108.9 %** |
| 2025 | 51.1 % | 10.1 % | 10.1 % | 29.6 % | 51.1 % |

**Every fold fails the per-rung bar.** `PNW_midC` remains the worst rung, as in both
predecessors, and the mechanism caiso-234 §D named survives intact: PNW's spot rung
is what is left after a moving weight is applied to a moving total and a fixed firm
block is taken out of a **small** corridor residue (845–1,965 MW), so it
concentrates every source of variation. The `DSW_CCGT`/`DSW_CT` pair, which passed
caiso-233's per-rung CV at 0.026 and caiso-234's at 0.073, now sits at **0.137 with
30–38 % LOYO across the break** — its earlier stability was, as caiso-233 §D
suspected of it, a within-window property rather than a market structure.

**Corridor weights and the simultaneity gap** (per-year `w_PNW`; the DSW share is
its complement):

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | pooled |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| `w_PNW` | 0.281 | 0.330 | 0.312 | 0.338 | 0.321 | 0.287 | 0.290 | 0.318 |
| simultaneity gap (MW) | 789 | 941 | 569 | 577 | 969 | 1,126 | 514 | 773 |

The weights are the *least* disturbed quantity in the whole exercise (0.281–0.338
across seven years, CV 0.068) — the two corridors' **relative** depths are far more
stable than either's level. Recorded because it is the one thing here a future lane
could build on.

**Rule-14 EIA-930 sign check: passes on all seven years.** Every gated percentile
is strongly positive (TOTAL p98 7,805–10,372; TOTAL p99.9 9,112–11,373). The
negative-hour shares are §B2's table and are reported there because they are
evidence, not merely a caveat check.

**Sample adequacy, as pre-committed in PRECOMMIT §5(6):** all 11 CISO DIBAs are
present in all seven years, per-DIBA non-null coverage 8,563–8,784 rows/year, and
every year resolves to n = 8,759 on the model clock. `PACW` is the one gappy series
(8,563 in 2022; 8,702–8,730 in 2023–25) and `corridor_net_import`'s `groupby.sum()`
treats a missing DIBA-hour as a zero contribution, slightly understating
`WECC_PNW` in those hours. **Pre-existing and unchanged** — it applied identically
to the caiso-234 run — and far too small to produce a 1.9 GW level shift, but
disclosed rather than left to be discovered.

## §G — WHAT THE THREE EXECUTIONS TOGETHER ESTABLISH

Durable, measured, and not contingent on any one estimator's split:

1. **The measured seam envelope is a well-measured object *within a regime* and NOT
   a stationary one across the working span.** 2019–22 `p98(TOTAL)` CV **0.023**;
   2023–25 CV **0.058**; pooled **0.108**, with the excess almost entirely
   between-regime (§B1).
2. **A structural break sits at the 2022/2023 boundary**, −18.8 % in routine depth
   and +54.2 % in the scarcity interval, driven by the PNW seam flipping from
   82–96 % import-hours to 49–69 % (§B2). It is physically legible as CAISO's
   in-state solar-plus-storage build displacing routine daytime imports.
3. **The four SPOT depths are NOT identified by seven years of EIA-930 flow.** The
   delivered ladder moves 12.8 % in total and 36–62 % on individual rungs on the
   sample choice alone, with the same estimator and the same convention (§D).
4. **`routine_total` is not out-of-sample valid across the break** (26.1 / 27.2 %),
   which retires FINDING-caiso234 §F2's "identifiable from three years" (§C).
5. **The incumbent 8,800 MW ladder's measured over-depth is regime-specific**:
   +449…+1,036 MW against 2019–22, +1,493…+3,059 against 2023–25. caiso-233 §E /
   caiso-234 §F4's bound is **withdrawn as a standing fact** and restated as a
   2023–2025 statement (§E).
6. **The corridor SPLIT is the stable part** (`w_PNW` 0.281–0.338, CV 0.068)
   even as both levels move — the one quantity here with any claim to being a
   market structure.
7. **The rule-14 EIA-930 admissibility check passes on all seven years**, so the
   failure is a property of the object and not of the data source (§F).
8. Method facts for any pooled percentile ladder in this repo: a pooled tail
   *interval* is biased upward relative to its constituent years (caiso-234 §B4),
   and **a pooled percentile across a regime break is not an estimate of anything**
   — it is a mixture whose value is set by the sample's regime composition (§B1).

## §H — CLOSURE: the DOF is returned to the owner PERMANENTLY DECLARED

**The pre-registered stop condition fired and PRECOMMIT §6 makes it terminal.**
Nothing was softened: the 0.20 / 0.25 bars are the imported constants, the near-miss
band was declared a FAIL in advance and two folds landed in it, the gated object was
not re-scoped, no component was admitted after seeing which passed (and this time
**none** passed), no residual-tuned fallback was reached for, and **no further
widening or fourth construction is proposed.**

**The object is closed from DATA, not from effort.** Three pre-registered
executions have now failed on the same four capacities:

| # | session | construction | outcome |
|---|---|---|---|
| 1 | caiso-233 | per-corridor p98, firm carved out per corridor, scarcity as a residue | CV 0.550 / LOYO 491.7 % — **FAIL** |
| 2 | caiso-234 | TOTAL envelope, scarcity as an interval, 2023–2025 | CV 0.120 / LOYO 34.2 % — **FAIL** |
| 3 | caiso-235 | **the same estimator, 2019–2025** | CV 0.266 / LOYO 55.0 %, 5 of 7 folds — **FAIL** |

and the third failure is the one that closes the question, because it is **not a
failure of the estimator**. 2019–2025 is the whole measured record this repository
can bring to bear — the extract's remaining coverage is H1-2026, which is
locked-test tier — and that record does not contain a single stationary object to
estimate. A fourth construction would be estimator-shopping against a
non-stationarity that no construction can remove, and an eighth year does not
exist.

**DOF ledger `spot_capacity`: CLOSED AS NOT IDENTIFIABLE from EIA-930 seam flow,
and returned to the owner permanently declared.** The incumbent
`PNW_midC` 1,800 / `DSW_CCGT` 1,800 / `DSW_CT` 2,200 / `WECC_scarcity` 3,000 =
8,800 MW literals stand unchanged and stay labelled **`RESIDUAL (static, no cited
primary source)`** — with §E's correction attached to the record: they are not
measurably over-deep in general, only against the post-2022 regime.

**What would re-open it is a different KIND of evidence, not more of this one**, and
naming it is not a proposal to pursue it: a published CAISO source that sizes
economic (non-RA) import availability directly, on the annual cadence the MIC/DMM
firm block already uses. Absent that, the honest position is that these four
capacities are a **declared, uncited residual** — which is what the label already
says.

## §I — RECORD CHANGES

* Keeper, markers, freeze, determination (**NOT-YET**, C3a sole load-bearing FAIL
  at +4.1 / +12.5 / +15.6 %; C3c the single ledgered caveat; C6 attested; C8 PASS):
  **UNCHANGED**.
* **No dashboard registration** — no run was solved (rule 15 applies to completed
  runs; the caiso-134/140/150/202/232/233/234 disposition).
* **No `ScenarioConfig` field added.** `caiso_import_depth_measured` was
  pre-registered in PRECOMMIT §7 but is reached only on a gate PASS, so it was
  never written and **rule 28(c) does not apply**.
* Matrix (rule 28(b), **CAISO shard only**) — **evidence append, no verdict move**:
  `import_hub_pricing` (K) gains this session's result, the regime break, the §E
  withdrawal of the over-depth bound, and the closure. **DO-NOT-REDO now covers all
  three executions** and, per §H, the object itself.
* `docs/calibration-log/caiso.md` — entry appended.
* `scripts/data/derive_caiso_import_tranches.py` — `corridor_net_import(years=YEARS)`
  (default-preserving; all fifteen existing callers byte-unaffected).
* DOF ledger `spot_capacity`: **CLOSED — not identifiable**, returned to the owner
  permanently declared (§H).
