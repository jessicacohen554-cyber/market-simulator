# ADDENDUM miso-245 — **THE VERDICT IS `A-CONFIRMED` (`M` = 1), AND MY OWN R-2 SHOWS THE TEST HAS LOW DISCRIMINATING POWER.** One more instrument leg is added here — **it can only INVALIDATE** — and the rule-23 citation is re-worded to rest on what actually carries it

**Governs:** `PREREG-miso245-attribute-the-incumbent-ladder-drift-2026-09-08.md` §2.2 (how the
verdict is *read*, never the rule itself), §2.4 R-4, and §4 (the disposition this session now enters).
**Pushed BEFORE the numbers it governs. NO BAR IS MOVED. The one leg added is STRICTER — it can
invalidate the verdict and can never rescue it.** Machine record:
`results/calibration/_miso245_ladder_drift_attribution_phase0.json`; evaluator
`scripts/probes/_miso245_ladder_drift_attribution_phase0.py`, whose bars are literals quoted from the
PREREG.

---

## 0. STATED FIRST, AGAINST INTEREST — and the first disclosure is the important one

### 0a. **MY PRE-REGISTERED TEST HAS LOW DISCRIMINATING POWER, AND R-2 — WHICH I DECLARED DESCRIPTIVE-ONLY BEFORE RUNNING IT — IS WHAT SHOWS THAT**

All six gated legs pass (`FAILED_LEGS: []`) and the verdict on the pre-registered rule is

| | |
|---|---:|
| mismatching entries | **3** |
| `m_j` (hours of duration count) | **1 / 1 / 1** |
| **`M = max_j m_j`** | **1** |
| bar for `A-CONFIRMED` | ≤ **1** |
| **VERDICT** | **`A-CONFIRMED`** |

**And here is what it is worth.** R-2, the flip distance `f_j` measured on all 192 entries, reads
`min_f_over_matches` = **1**, with the *matching* entries' distribution at
**p05 = p25 = p50 = p75 = 1**, p95 = 2. **The median entry that did NOT drift is also exactly one
hour from a different cent.** "Reachable at ±1 hour" is therefore close to a property of the
**estimator's own sensitivity** — one hour of duration count moves the quantile position by
`8759/8760 ≈ 0.9999` order statistics, and adjacent DA order statistics in this price region are
typically a cent or more apart — rather than a property of the drift. A test that nearly every entry
would pass cannot, on its own, separate a one-hour sample difference from many other stories.

**The verdict stands as `A-CONFIRMED` because that is the rule fixed before the number existed, and
because PREREG §2.4 R-2 pre-committed that R-2 "cannot move the verdict in either direction."** I
honour that in the direction that costs me: R-2 does **not** convert this into `A-REFUTED`. What it
does is bound how much the verdict may be *claimed to prove*, and §1 re-words the citation
accordingly rather than banking a result the instrument does not support.

### 0b. **A POST-HOC READING OF THE SAME STATISTIC POINTS THE OTHER WAY. IT IS LABELLED POST-HOC AND IT MOVES NOTHING**

Read in the opposite direction, the same distribution corroborates a *small* perturbation: if most of
the 192 entries sit one hour from flipping, a sample drift of many hours would have flipped far more
than **3**. **This was not pre-registered** — PREREG §2.4 declared R-2's reading as "whether the three
drifted entries are also the most rounding-fragile at HEAD", which is a different question, and the
answer to *that* question is **NO, they are not distinguished** (ranks 4 / 39 / 91 of 192,
`separated: false`). **The arithmetic showing it moves nothing:** the verdict is `A-CONFIRMED` on the
pre-registered rule with or without this reading, R-2 is barred from moving it either way, and no
disposition below is conditioned on it. It is recorded because suppressing a reading that favours my
own direction would be as dishonest as suppressing one that does not — **and it is used for nothing.**

### 0c. **R-4 CAME BACK `true`, AND IT RAISES AN INSTRUMENT QUESTION MY PREREG DID NOT ASK PRECISELY ENOUGH**

PREREG §2.4 R-4 asked whether the same-seam no-wash clamp binds *anywhere* under perturbation. It
does — **`clamp_binds_anywhere_in_any_scan: true`** — which is unsurprising, because the scan sweeps
the count over its entire feasible range and an export quantile driven to the top of the DA
distribution must eventually exceed `min(imp) − NO_WASH_EPS`. **But the question that actually
matters is narrower and I did not gate it:** if a mismatching entry's *reaching* value were the
**clamp** rather than the quantile, then `m_j` would be measuring the clamp and not the sample, and
the verdict would be an artifact of a mechanism miso-244 already **REFUTED** as the cause.

> **`G-CLAMP-N` — DECLARED HERE, BEFORE ITS NUMBER EXISTS, AND IT CAN ONLY INVALIDATE.**
> For each mismatching entry `j`, at its own reaching perturbation `Δ_j` and at `Δ ∈ {−1, 0, +1}`,
> the estimator's value must be the **UNCLAMPED** quantile: `v_raw,j(Δ) ≤ lim_seam`, with `lim`
> the same-seam no-wash limit computed on the **unperturbed** import list.
>
> **If it fails at ANY entry, that entry's `m_j` is VOID, the `A-CONFIRMED` verdict is WITHDRAWN,
> and this session publishes that failure FIRST and at full magnitude before anything else.**
> **It cannot rescue anything**: passing changes no number, moves no bar and adds no evidence — it
> only removes a way the verdict could be false.

### 0d. **THE FOOTPRINT IS RE-MEASURED, NOT QUOTED — AND IT WILL AGREE WITH ITS PREDECESSOR BY CONSTRUCTION**

PREREG §4 step 3 names the screen year by `argmax_year L` and adds *"if a re-measured footprint names
a different year, the footprint wins, not this sentence."* This session therefore **re-runs
miso-244's own liveness gate** (`scripts/probes/_miso244_liveness_gate.py`) **BEFORE any edit to the
committed table**, because after the reconciliation the committed and HEAD-derived ladders are the
same object and the gate would have nothing to measure.

**DISCLOSED AGAINST INTEREST BEFORE THE NUMBERS EXIST:** that re-run is a deterministic estimator on
the same series and the same committed sidecars, so agreement with miso-244's published
`L` = 0.00000 / **0.00982** / 0.00000 and `Δq̂` = **+3.682 MW** is **EXPECTED**, not independent
corroboration, and it will not be presented as such. Its only job is to confirm that the year the
screen runs in is named by a measurement taken in this session rather than copied from a handoff.

---

## 1. **THE RULE-23 CITATION, RE-WORDED HERE — because §0a means the ±1 result cannot carry it alone**

PREREG §4 step 1 said the re-derive "cites this session's attribution measurement as the data change
rule 23 requires." **Given §0a that wording over-claims, so it is corrected here, before the commit
exists, and in the direction that asks LESS of my own result:**

> **What carries the citation** is that the estimator is **frozen and unchanged** — `G-RAW` reads
> `max_abs_delta` **0.0** across all 192 entries at HEAD, and miso-244 §3 eliminated the whole
> `h = q·(n−1)` estimator family arithmetically — while the frozen estimator's output **on the source
> data as it stands at HEAD** differs from the committed table at exactly three entries. A frozen
> formula whose output has moved has had its **input** move. That inference is complete without `M`.
>
> **What `M = 1` adds is a BOUND on the magnitude** of that input difference: one hour of duration
> count at each affected depth, `1.14e-4` of the year, with the sign quantile monotonicity requires
> at every entry (`G-DIR`). **It is corroborative, it is measured at the low power §0a states, and it
> is reported as such — never as the load-bearing citation.**
>
> **What is still NOT identified, and is stated rather than papered over:** *which* hours of which
> source series differ, and on what date the vintage changed. **P-1's provenance reading is a read of
> the record with no decision rule attached and cannot supply that**, and the 2026-08-16 history
> rewrite makes sha archaeology unreliable by CLAUDE.md's own statement. The re-derive therefore
> reconciles a **stale output to its own frozen formula on current data** — rule 14 `[R-ACCURATE]`'s
> plain instruction — and does not claim to have named the revision event.

**Zero free parameters.** Reconciling three committed quantile values to the frozen estimator's own
output adds no degree of freedom; the DOF ledger stays **41/2**. **No residual, no criterion and no
band comparison enters this decision, in either direction** (rule 1 `[R-STRUCT]`).

---

## 2. **THE EDIT, PUBLISHED HERE BEFORE IT IS MADE**

Exactly three entries of `MISO_SEAM_LADDER_BY_YEAR` (`src/market_sim/model/interchange/spec.py`)
move, each to the value `derive()` returns at HEAD, and **the other 189 must be byte-identical**
(checked, not assumed):

| year | seam | side | band | from | **to** | live on the keeper? |
|---|---|---|---|---:|---:|---|
| 2023 | PJM | import | 5 | 27.86 | **27.87** | **no** — displaced by the PJM hourly overlay |
| 2023 | South | export | 4 | 27.69 | **27.70** | **yes** |
| 2024 | South | export | 5 | 23.77 | **23.76** | **yes** |

`_MISO244_KNOWN_LADDER_DIVERGENCES` in
`tests/iso/miso/test_miso_seam_ladder.py` is **DELETED** (rule 26 `[R-DELETE]` — a dead exception
list is a re-armable answer key), and
`TestLadderRegistry::test_incumbent_registry_reproduces_the_frozen_derivation` must then pass at
`atol=0.005` on **all 192 entries with no exceptions**. **The tolerance is never widened.**

**THE FINGERPRINT IS PRESERVED IN THE RECORD, WHICH IS WHY THIS IS NOW ADMISSIBLE.** miso-244 refused
the re-derive because it would erase the last copy of the derivation vintage before the drift was
diagnosed. The diagnosis now exists at full precision — the three coordinates, their counts
(5,415 / 3,259 / 3,044), their interpolation records and their committed values are in
`_miso244_incumbent_ladder_cent_phase0.json`, `_miso245_ladder_drift_attribution_phase0.json` and
both FINDINGs — so the order the handoff fixed (*diagnose before re-deriving*) has been honoured, not
short-circuited.

---

## 3. WHAT IS GATED FROM HERE, AND WHAT IS REPORTED

**GATED**: `G-CLAMP-N` (§0c); the **byte-identity of the other 189 entries** after the edit; the
**re-derive reproduction pin** at `atol=0.005` on all 192 with the exception list deleted;
**G-DRIFT** `a667073f..HEAD` with `surface_stamp` (PREREG §4 step 2), which decides only whether the
keeper's committed bundle may serve as the control; and the **four STRUCTURAL STOP-only screen
gates**, which are declared in a **SECOND pushed addendum before the screen runs** and are not
written here.

**REPORTED, NEVER GATED**: everything in §0; the re-measured `L` / `Δq̂` footprint (§0d); R-1, R-2,
R-3, R-4, R-5 and P-1 as PREREG §2.4 declares them; and every band and criterion value of the keeper.
**No scored criterion, no residual and no band comparison appears in any bar, here or in the screen.**

## 4. Non-claims

1. **The verdict is not re-opened and no bar moves.** `A-CONFIRMED` on `M = 1` stands exactly as
   pre-registered; §0a limits what it is *claimed to prove*, not what it *is*.
2. **§0b is used for nothing**, and the arithmetic showing it changes no disposition is given in place.
3. **This addendum solves nothing and authorizes no LP by itself.** The screen remains conditional on
   `G-CLAMP-N`, on the reproduction pin, on G-DRIFT, and on the four gates of the second addendum.
4. **No `ScenarioConfig` field is created or changed**, DOF stays 41/2, and no cell verdict moves in
   either direction on the strength of anything here.
5. **No out-of-training year is solved, scored or registered**, and no marker is sought.
6. **MISO has no failing gate**, this session does not invent one, C3c is untouched, and nothing here
   trades a passing gate for anything.
