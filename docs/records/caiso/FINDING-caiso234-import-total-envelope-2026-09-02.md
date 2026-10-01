# FINDING — caiso-234: the pre-specified TOTAL-envelope estimator **FAILS the load-bearing gate it was pre-registered against** — G-LOYO **34.2 %** on the scarcity interval against a 25 % bar — and the pre-registered stop condition fired: **NO SOLVE**. The stability leg passed, but it was **disclosed as foreseen before execution** and carries no weight. The failure is one-year-driven and diagnosed: the scarcity rung is a **9-hour-per-year order statistic**, so it is not identifiable from three years in *either* construction tried (residue CV 0.550 / LOYO 491.7 % at caiso-233 → interval CV 0.120 / LOYO 34.2 % here — a 14× improvement that still does not clear the bar). **The routine total DOES pass both gates cleanly (CV 0.058, LOYO ≤ 11.5 %) and is REFUSED as a partial swap**, exactly as §6 pre-registered. Disclosed against interest: the two estimators are **algebraically constrained to the same delivered total**, so gating the total gated their common ground. **The two-estimator budget is SPENT. The DOF is ESCALATED to the owner as a standing item.** NO LP, NO SOLVE — committed bytes only (2026-09-02)

**Keeper `2026-09-01-caiso-231-b1-ungrounded` UNCHANGED. No mechanism armed, no
`ScenarioConfig` field added, no LP built, no solver called, nothing registered,
no matrix cell verdict moved.** `calibration-complete.json` (no CAISO marker) and
`holdout-freeze.json` (ACTIVE) untouched; every read stayed inside **2023–2025**.

Pre-registration: `PRECOMMIT-caiso234-import-total-envelope-2026-09-02.md`,
**pushed to `origin` before the derivation was executed** (commit `d18fa22d`,
branch `claude/caiso-import-total-envelope-dnvmx0`), not merely before the solve.
§9 of that document records this outcome.

Instruments (committed):

* `scripts/data/derive_caiso_import_total_envelope.py` — the derivation, both
  gates, and the §5 ungated diagnostics.
* `results/calibration/_caiso234_import_total_envelope.json`.

Every number reproduces from `data/raw/eia-930-interchange/CISO interchange
hourly.parquet` on the model clock (`_caiso_interchange_model_clock`,
`CAISO_CORRIDOR_DIBA`) and the committed per-year MIC firm blocks in
`IMPORT_TRANCHES_BY_YEAR`. `CAP_PCTL`, `SCARCITY_PCTL`, `CV_MAX` and `LOYO_MAX`
are all imported from files already on `main`; none was settable by this session.

---

## §A — THE RESULT

**The gated object** (PRECOMMIT §2 — two direct statistics of the TOTAL corridor
net-import distribution, with no firm carve-out inside either):

| component | 2023 | 2024 | 2025 | pooled | CV | G-STABILITY (≤ 0.20) |
|---|--:|--:|--:|--:|--:|:--|
| `routine_total` = p98(TOTAL) | 7,873 | 7,805 | 8,845 | 8,289 | 0.058 | ok |
| `scarcity_interval` = p99.9−p98 | 1,757 | 1,307 | 1,590 | 1,795 | 0.120 | ok |
| *(reported)* `ladder_total` = p99.9 | 9,630 | 9,112 | 10,435 | 10,084 | 0.056 | — |

**G-LOYO** — derive on the pooled other two years, predict the held-out year
(bar **25 %**):

| held out | train | `routine_total` | `scarcity_interval` | worst | G-LOYO |
|---|---|--:|--:|--:|:--|
| 2023 | 2024+2025 | 7.0 % | 3.1 % | 7.0 % | ok |
| **2024** | **2023+2025** | 8.8 % | **34.2 %** | **34.2 %** | **FAIL** |
| 2025 | 2023+2024 | 11.5 % | 3.1 % | 11.5 % | ok |

**G-STABILITY ok | G-LOYO FAIL ⇒ FAIL.** The pre-registered stop condition fired.
**No LP was built and no solver was called.** §7's arms were never run, so there is
nothing to register (rule 15 applies to completed runs — the
caiso-134/140/150/202/232/233 disposition). The bar was not moved, the gated
object was not re-scoped, and no third estimator was attempted.

**The gate that failed is the one that mattered.** PRECOMMIT §0.3 disclosed
*before execution* that `CV(routine_total) = 0.0581` and `CV(p99.9) = 0.0560` were
already published in caiso-233's committed JSON and that the interval CV was a
hand calculation on those same six numbers (**"CV ≈ 0.12"** — the script returns
**0.120**). So G-STABILITY was foreseen and no part of this finding rests on it.
G-LOYO is computed on **pooled** two-year samples, which are not a function of any
committed per-year percentile; it was genuinely unseen, and it is what failed.

## §B — WHY IT FAILS: a 9-hour order statistic, and one year out of family

**§B1 — the failure is entirely in the scarcity leg, and entirely in one year.**
`routine_total` predicts out-of-sample within 7.0–11.5 % in all three folds. The
interval predicts within **3.1 %** in two folds and misses by **34.2 %** in the
third. The predicted-vs-actual detail:

| held out | predicted interval | actual interval | error |
|---|--:|--:|--:|
| 2023 | 1,811 | 1,758 | 3.1 % |
| **2024** | **1,754** | **1,307** | **34.2 %** |
| 2025 | 1,541 | 1,590 | 3.1 % |

2023 and 2025 have wide extreme tails (1,758 and 1,590 MW); 2024 has a narrow one
(1,307 MW). The only training fold that excludes 2024 is drawn entirely from the
two wide-tail years and over-predicts it. **With n = 3, a single atypical year is a
third of the sample and LOYO has no power to average it away** — which is the
honest reading of a 34.2 % miss, not a reason to discount it.

**§B2 — the interval is an extreme-tail order statistic, and that is structural.**
p99.9 of an 8,759-hour year is fixed by its **9 highest hours**, and the
(p98, p99.9] band by **167 hours**, identically in every year:

| year | n | hours > p99.9 | hours in (p98, p99.9] | p99.9 | annual max |
|---|--:|--:|--:|--:|--:|
| 2023 | 8,759 | 9 | 167 | 9,630 | 13,136 |
| 2024 | 8,759 | 9 | 167 | 9,112 | 13,312 |
| 2025 | 8,759 | 9 | 167 | 10,435 | 15,080 |

Note what moves and what does not: 2024's **p98 is within 0.9 % of 2023's**
(7,805 vs 7,873) and its **annual max is higher** (13,312 vs 13,136) — yet its
**p99.9 is 518 MW lower**. It is the *shape* of the extreme tail between p98 and
p99.9, not its level, that differs by year. A rung defined on that band inherits
a ~9-observation order statistic, and three years supply three of them.

**§B3 — the interval construction was nevertheless a large, real improvement.**
Against caiso-233's residue form, on the same data and the same bars:

| construction | CV | worst LOYO |
|---|--:|--:|
| caiso-233 — residue, p99.9(total) − Σ marginal p98 | **0.550** | **491.7 %** |
| caiso-234 — interval, p99.9(total) − p98(total) | **0.120** | **34.2 %** |

The 9.8× CV amplification and the double-counted 0.5–1.1 GW simultaneity gap that
FINDING-caiso233 §C3/§C4 diagnosed are both gone: CV falls 4.6× and worst LOYO
falls **14×**. **The diagnosis was right and the prescribed fix worked as
specified. It was not enough.** That distinction is the finding, and it is not
softened into a pass.

**§B4 — a second-order fact that matters for any pooled percentile ladder.** A
pooled percentile is the tail of a *mixture*, not a central estimate of the
per-year statistics, and the effect is concentrated exactly in the fragile leg:

| component | mean of per-year | pooled | bias | pooled above every year? |
|---|--:|--:|--:|:--|
| `routine_total` | 8,174 | 8,289 | +115 (+1.4 %) | no |
| `scarcity_interval` | 1,551 | **1,795** | **+244 (+15.7 %)** | **yes** |
| `ladder_total` | 9,726 | 10,084 | +358 (+3.7 %) | no |

The pooled scarcity interval **exceeds all three per-year values**, because
pooling lets the heavier-tailed years set the pooled p99.9 while the pooled p98
regresses toward the middle. Any pooled-ladder derivation that carries a
tail-interval rung inherits this upward bias; a p98-level rung is nearly immune to
it. Recorded so the next lane does not rediscover it.

## §C — THE ROUTINE LEG PASSES CLEANLY, AND IS REFUSED (against interest)

`routine_total` clears **both** gates decisively — CV **0.058** against 0.20, and
LOYO **7.0 / 8.8 / 11.5 %** against 25 %. On the §4 placement it delivers
`PNW_midC` 1,065 and `DSW_CCGT`/`DSW_CT` 2,100 MW each, and it would be easy to
admit those three rungs and leave `WECC_scarcity` at its incumbent 3,000.

**It is refused.** PRECOMMIT §6 fixed this before the numbers existed: *"Do not
re-scope the gated object to whichever component passes."*

**This refusal is harder than caiso-233's, and the difference is stated rather
than buried.** caiso-233 §D could refuse its passing `DSW_CCGT`/`DSW_CT` pair on
the merits as well as on the pre-registration, because that pass was an
*arithmetic cancellation* — two 0.16-CV series that happened to move
co-directionally in a 3-year sample. **No such argument is available here.**
`routine_total`'s stability is not a cancellation; it is a genuine property of a
p98 taken on 8,759 hours of measured flow, and it is the single most robust
quantity this lane has produced. It is refused **purely** because the gated object
was pre-registered as **both** components and admitting the passing half after
seeing which half passed is the forking path the PRECOMMIT exists to close.

The measurement is preserved in §F as evidence for the owner. **Recording it is
not acting on it**, and this session does not act on it.

## §D — §5 DELIVERED: the ungated per-rung diagnostics, at full magnitude

PRECOMMIT §5 committed in advance to publishing these whatever they said —
caiso-233's own per-rung bar applied to this ladder. They are worse than the
gated object, and in one place worse than the estimator this one replaced.

**Delivered static SPOT ladder (pooled 2023–2025, §4 placement):**

| rung | derived | incumbent | delta |
|---|--:|--:|--:|
| `PNW_midC` | 1,065 | 1,800 | −735 |
| `DSW_CCGT` | 2,100 | 1,800 | +300 |
| `DSW_CT` | 2,100 | 2,200 | −100 |
| `WECC_scarcity` | 1,795 | 3,000 | −1,205 |
| **TOTAL SPOT** | **7,060** | **8,800** | **−1,740 (−19.8 %)** |

**Per-rung stability and LOYO under this placement (REPORTED, NOT GATED):**

| rung | 2023 | 2024 | 2025 | pooled | CV | *(caiso-233 port CV)* |
|---|--:|--:|--:|--:|--:|--:|
| `PNW_midC` | 1,460 | 685 | 1,000 | 1,065 | **0.304** | *0.253* |
| `DSW_CCGT` | 2,045 | 1,875 | 2,240 | 2,100 | 0.073 | *0.026* |
| `DSW_CT` | 2,045 | 1,875 | 2,240 | 2,100 | 0.073 | *0.026* |
| `WECC_scarcity` | 1,755 | 1,305 | 1,590 | 1,795 | 0.120 | *0.550* |

| held out | `PNW_midC` | `DSW_CCGT` | `DSW_CT` | `WECC_scarcity` | worst |
|---|--:|--:|--:|--:|--:|
| 2023 | 40.1 % | 2.2 % | 2.2 % | 3.1 % | 40.1 % |
| 2024 | **83.9 %** | 16.8 % | 16.8 % | 34.5 % | **83.9 %** |
| 2025 | 4.5 % | 12.1 % | 12.1 % | 3.1 % | 12.1 % |

**Read plainly: under caiso-233's bar this ladder also fails, and `PNW_midC` is
WORSE here than in the estimator it replaced** (CV 0.304 vs 0.253; worst LOYO
83.9 % vs 45.5 %). The zero-DOF placement did not fix the per-rung problem — **it
relocated it.** The mechanism is visible in the corridor weights, which are
themselves a moving quantity (`w_PNW` = 0.321 / 0.287 / 0.290): PNW's spot rung is
what is left after a moving weight is applied to a moving total and a moving
CV-0.16 firm block is taken out of the remainder, so it accumulates three sources
of variation into the corridor's *small* residue (685–1,460 MW). The
`caiso-233 §C2` diagnosis — that PNW's instability is inherited from the firm
carve-out — survives this estimator intact, because §F1's prescription removes the
carve-out from the **gated statistic** but cannot remove it from the **placement**:
the firm rungs are grounded and must sit inside the total, so the subtraction
happens somewhere no matter what is gated.

## §E — THE SHARPEST OBJECTION, and it is arithmetic (disclosed against interest)

PRECOMMIT §0.5 conceded that moving the gated object after a failure is the shape
of gate-shopping and rested on two answers. Execution surfaced a **third fact,
stronger than either answer, which was not known when the PRECOMMIT was written**
and which is recorded here because it cuts against this session:

**The two estimators are algebraically constrained to deliver the same total.**

    caiso-233:  Σ_c [ p98(c) − firm_c ] + [ p99.9(TOT) − Σ_c p98(c) ]  =  p99.9(TOT) − Σ_c firm_c
    caiso-234:  Σ_c [ routine·w_c − firm_c ] + [ p99.9(TOT) − routine ] =  p99.9(TOT) − Σ_c firm_c

Both reduce to **p99.9(TOTAL) − Σ firm**, identically, for any corridor weights
that sum to 1. Numerically: 10,084.0 − 3,021.7 = **7,062.3 MW**, and both
estimators' pooled delivered totals round to **7,060 MW**. Their agreement on the
total is **an identity, not convergent evidence**, and must never be cited as
independent corroboration.

The consequence for §0.5: gating the total gated **the one quantity the two
estimators could not have disagreed about**, and left ungated **precisely the
quantity caiso-233 failed on** — the split. A reader is entitled to that
objection, and it is stronger than the one the PRECOMMIT anticipated.

**Two things keep the record clean.** First, the move was specified in committed
bytes by the failed session itself (§F3), on structural grounds, before either
estimator's numbers existed — the identity was not the reason it was chosen, and
nobody had computed it. Second, and decisively: **the objection is moot in
outcome. The estimator failed anyway.** The weaker gate did not buy a pass, so
nothing in this repository rests on the move. Had it passed, §D's per-rung
diagnostics were pre-committed for exactly this reason and would have had to be
argued through.

## §F — WHAT THE TWO ESTIMATORS TOGETHER ESTABLISH

Durable, measured, and not contingent on either estimator's split:

1. **The measured seam depth is a stable, measurable object.** Corridor p98
   CV 0.042 (both corridors); TOTAL p98 CV 0.058; TOTAL p99.9 CV 0.056.
2. **The routine total is IDENTIFIABLE from three years.** `p98(TOTAL)` = 7,873 /
   7,805 / 8,845 MW, CV 0.058, out-of-sample error 7.0–11.5 %. This is the
   strongest quantity the lane has produced and it passed both bars. (§C: measured
   and recorded, **not acted on**.)
3. **The scarcity rung is NOT identifiable from three years, in either
   construction.** As a residue: CV 0.550, LOYO 491.7 %. As an interval:
   CV 0.120, LOYO 34.2 %. Root cause (§B2): a 9-hour-per-year order statistic
   whose *tail shape* moves independently of the level.
4. **The incumbent ladder is over-deep against the measured envelope** —
   re-computed here and unchanged from caiso-233 §E:

   | year | incumbent ladder | measured p98 | measured p99.9 | **over-depth vs p99.9** |
   |---|--:|--:|--:|--:|
   | 2023 | 11,123 | 7,873 | 9,630 | **+1,493** |
   | 2024 | 12,171 | 7,805 | 9,112 | **+3,059** |
   | 2025 | 12,171 | 8,845 | 10,435 | **+1,736** |

   Direction is consistent with FINDING-caiso232 §D's corr(monthly residual, model
   import volume) = **+0.419**. It remains **a bound on the sum, not a per-rung
   derivation**, and — per §E — the two estimators' agreement on it is an identity.
   **Still not acted on**: converting it into a depth cut without per-rung
   identification is the rule-13 `[R-MEASURED]` act this lane exists to avoid.
5. **The rule-14 EIA-930 caveat check passes again** (`--report`): every gated
   percentile is strongly positive; negative-hour shares 51.0/38.4/30.8 % (PNW),
   5.8/5.4/4.9 % (DSW), 14.2/11.4/9.1 % (total).
6. **A method fact for any pooled percentile ladder in this repo** (§B4): a pooled
   tail *interval* is biased **upward relative to every constituent year**
   (+15.7 % here, exceeding all three); a pooled p98 *level* is nearly immune
   (+1.4 %).

## §G — ESCALATION: the DOF is not closable from three years of EIA-930

**The two-estimator budget is SPENT** (PRECOMMIT §0.6). Per the prompt's standing
instruction and §6, this session **stops**. The DOF ledger entry `spot_capacity`
stays **OPEN** and is escalated to the owner as a **standing item**, with this
record:

* the object is measurable and the total envelope is well identified (§F1–§F2);
* the incumbent is measurably over-deep by 1.5–3.1 GW (§F4);
* the **scarcity rung** is the binding obstacle, and it is an obstacle of
  **sample length**, not of construction (§B2–§B3, §F3);
* **two structurally distinct estimators have now been refused on pre-registered
  gates**, and a third on the same three years would be estimator-shopping.

**One candidate route exists, and this session did not take it.** The failure is a
3-observation problem in an extreme-tail order statistic; the direct remedy is a
**longer measured sample**, not a different estimator. The programme's working
span is **2019–2025**, and under the owner's 2026-08-06 clarification —
*"WHAT IS HELD OUT IS THE SCORE, NEVER THE DATA … Data intake needs NO
per-ISO/per-window authorization and no marker"* — deriving a measured input over
2019–2025 EIA-930 flow is **data prep, not a spend**: no year is solved, scored or
registered, and no model output or measured actual is read. On seven years the
p99.9 band rests on ~61 hours rather than 9, and LOYO gains six folds instead of
three.

**This is put to the owner, not executed**, for two reasons that are this
session's to state and not to resolve: (a) it re-runs the caiso-234 estimator on a
sample wider than the one pre-registered here, so it needs its own
pre-registration and, given the budget language above, an explicit owner decision
that a wider-sample re-run of the **same** estimator is not the forbidden third;
and (b) the ladder would then be informed by measured flow from years CAISO may
later spend as validation touchpoints — which the 2026-08-06 clarification appears
to anticipate and permit (*"already configured precisely like the frontier keeper,
with nothing left to prepare"*), but which is a governance judgment for the owner
rather than an inference for a lane.

Until then the incumbent 8,800 MW literals stand, unchanged and still labelled
`RESIDUAL (static, no cited primary source)`.

## §H — RECORD CHANGES

* Keeper, markers, freeze, determination (**NOT-YET**, C3a sole load-bearing FAIL
  at +4.1 / +12.5 / +15.6 %; C3c the single ledgered caveat; C6 attested; C8 PASS):
  **UNCHANGED**.
* **No dashboard registration** — no run was solved (rule 15 applies to completed
  runs; the caiso-134/140/150/202/232/233 disposition).
* **No `ScenarioConfig` field added.** `caiso_import_depth_measured` was
  pre-registered in PRECOMMIT §7 but is reached only on a gate PASS, so it was
  never written and **rule 28(c) does not apply**.
* Matrix (rule 28(b), **CAISO shard only**) — **evidence append, no verdict move**:
  `import_hub_pricing` (K) gains this session's result, the identity of §E, and the
  escalation. The caiso-233 DO-NOT-REDO stands and is joined by this one.
* `docs/calibration-log/caiso.md` — entry appended.
* DOF ledger `spot_capacity`: **OPEN**, escalated (§G).
