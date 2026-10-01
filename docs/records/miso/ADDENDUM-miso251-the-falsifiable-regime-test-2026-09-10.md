# ADDENDUM to PRECOMMIT-miso251 — the 2020/2021 rungs become a FALSIFIABLE TEST of the 2022 diagnosis

**Written BEFORE either rung is solved.** ZERO LP in this document. The prediction below is
pushed to `main` and pinned as a SHA before the shards that test it are created, so it cannot be
rewritten to fit what comes back.

## 1. Where the ladder stands

| rung | determination | why |
|---|---|---|
| **2022** (`2026-09-10-miso-251-screen2022`) | **NOT-YET** | C1 (4 classes), C3a −13.8 %, C3b 0.209, C4 coal r 0.744. C6 PASS, C8 PASS, C3c CAVEAT. |

The PRECOMMIT §5.1 "proceed if 2022 reads CALIBRATED" condition is **not met**, and the owner's
instruction for that case is explicit: *"diagnose and launch an lp screen on the holdout year miss
to see if the new config fixes that year before launching individual shards for each year of the
full span."*

**Diagnosed and screened.** The one candidate the diagnosis could actually name — MISO's 2022 zonal
load allocation, which was silently falling back to flat sample averages — was repaired and
re-solved. It moved the miss by **0.00 TWh** of coal (+50.53 both ways). Zonal allocation is
**eliminated**. No full-span shards are launched on the strength of a screen that cleared nothing.

## 2. What the 2020 and 2021 rungs now are

Not "the next rungs of a ladder that already stopped". They are the **discriminating test** of the
only diagnosis on the table, and the fuel record makes them one:

| year | Henry Hub $/MMBtu | position vs the regime the offer bands were identified in |
|---|---|---|
| 2024 | 2.19 | training |
| **2020** | **2.03** | **essentially IN-regime — below the training floor by $0.16** |
| 2023 | 2.54 | training |
| 2025 | 3.52 | training |
| **2021** | **3.72** | **just OUTSIDE — above the training ceiling by $0.20** |
| **2022** | **6.45** | **1.8× the ceiling, 2.9× the floor** |

The keeper's coal residual across its own training years, from committed artifacts:

| year | HH | coal residual | gas-CC residual |
|---|---|---|---|
| 2024 | 2.19 | −9.18 TWh | +2.97 |
| 2023 | 2.54 | −5.77 TWh | −6.80 |
| 2025 | 3.52 | −10.66 TWh (report-only, preliminary vintage) | −4.03 |
| **2022** | **6.45** | **+50.46 TWh** | **−16.41** |

Coal sits 6–11 TWh **light** everywhere in $2.19–3.52 and 50 TWh **heavy** at $6.45. That is a step
change at the edge of the regime, not a drift.

## 3. THE PREDICTION, and what falsifies it

**HYPOTHESIS (H1) — the 2022 miss is REGIME-BOUND.** The coal/gas merit-order crossing is
misplaced only where gas is far outside the band-identification regime; the recipe is not generally
broken out of sample.

**H1 predicts, on the keeper's frozen recipe:**

* **2020 (HH 2.03, in-regime): `|coal residual| < 15 TWh`**, i.e. in family with the −5.8 / −9.2 /
  −10.7 TWh of the training years, and of the same SIGN (coal light, not heavy).
* **2021 (HH 3.72, just outside): coal residual between 2020's and 2022's**, and much closer to
  2020's — a $0.20 excursion past the ceiling should not buy a 50 TWh error.

**H1 IS FALSIFIED IF** 2020 returns a coal excess of the 2022 kind (say `> +20 TWh`) at $2.03 gas.
That would mean the recipe fails out of sample **generally**, the gas regime is a coincidence, and
the 2022 result is not a range problem but a validity problem — a materially worse finding, and one
that would have to be reported as such.

**This is a STRUCTURAL gate, not a residual gate (rule 29 `[R-SCREEN]`).** It asks whether the
mechanism behaves as its own arithmetic implies across fuel regimes. It is STOP-only: it can kill
the fuel-regime explanation, it cannot promote anything, it contributes to no determination, and
**no parameter is cut, swept or selected against it either way.** Nothing in either rung's outcome
authorises an offer-curve change; rule 1 `[R-STRUCT]` (b)/(c) still require one config across every
scored year, declared ex ante.

## 4. Why the offer-curve latitude is NOT taken here

The owner's standing permission — *"Don't be afraid to tune the fossil offer curve if there's a
level issue across all years in a span"* — is conditioned on **a level issue across all years**.
There is not one. C3a on the keeper's own span reads **+4.9 % (2023), +1.8 % (2024), −6.2 %
(2025)**, all PASS, in both directions. A band multiplier is a common-mode lever; there is no
common mode to remove. Pulling 2022's −13.8 % up would push 2023 further past +4.9 %, and choosing
the factor so that 2022 lands is per-year fitting against a gate — precisely what rule 1's carve-out
condition (c) refuses. **The lever is declined on the evidence, not on caution**, and if the span
ever does show a common-mode level error the decision should be revisited on that evidence.

## 5. Scope, and what these rungs CANNOT say

Both rungs are **price-bench blind**: `actual_lmp.json` carries no MISO block before 2022, so C3a,
C3b and C3c are unscorable on 2020 and 2021 and both will read `CALIBRATED-WITH-CAVEATS` at best on
`unscored criteria: price_mean, price_shape`. **That is a fact about MISO's LMP retention, not a
model result**, and it is reported as such everywhere it appears. What they CAN say is C1 (7/9
classes complete on both years — a better fuel-mix bench than the keeper's own 2025, where all 8
are SKIPPED), C2, C4 and C8. C1 is the criterion the prediction in §3 is made on, so the test is
answerable on exactly the evidence these years carry.

Under rule 30(c) neither rung can move MISO's determination in either direction.

## 6. Shard plan

| shard | branch | scope | registerable |
|---|---|---|---|
| RUNG-2021 | `claude/miso251-tp2021` | 2021 | yes, own bundle |
| RUNG-2020 | `claude/miso251-tp2020` | 2020 | yes, own bundle |

Launched in **parallel**, as two independent single-year touchpoint bundles (rule 32 `[R-SHARD]`
(b): ~20 min each, where a two-year span shard would be ~40). Nothing is composed, so each year
keeps its own input snapshot and the shard protocol §3 hazard does not arise. They write disjoint
paths (`registry/<id>.json`, `runs/<id>.js`, `bench/MISO/<year>.json.gz`). Both carry the same two
declared source-forced degradations as 2022, for the same purged-source reason, and neither tunes
anything.
