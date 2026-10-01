# ADDENDUM to PRECOMMIT-miso263 — the numeric prediction, registered BEFORE any shard reported

```
SESSION : miso-263        ISO: MISO        LP SPENT BY THE PARENT: ZERO.
WHEN    : written and committed while all six repair shards were still solving,
          so the repaired numbers are CHECKED against this rather than
          explained after the fact (rule 1 [R-STRUCT] discipline).
SOURCE  : scripts/probes/_miso263_coal_ceiling_phase0.py, committed artifacts only.
```

---

## THE PREDICTION

For each month the cap admits at most `MAX[m]` coal MWh (§1 of the PRECOMMIT:
the efficiency-ordered greedy fill, an upper bound on every feasible dispatch).
A repaired solve must therefore deliver **no more than `min(cold[m], MAX[m])`**
in each month, because the cap is the only thing that changed and it can only
remove coal. Summing that over the year gives a hard ceiling on the repaired
run's annual coal, and it is worth registering because it is **tight**:

| year | COLD keeper (as registered) | **repaired ≤** | WARM keeper | ceiling − warm |
|---|---:|---:|---:|---:|
| 2020 | 188.84 | **188.84** | 188.84 | −0.00 |
| 2021 | 251.74 | **242.91** | 241.71 | +1.20 |
| 2022 | 265.72 | **232.55** | 231.04 | +1.51 |
| 2023 | 180.60 | **180.60** | 180.42 | +0.18 |
| 2024 | 167.52 | **167.52** | 167.52 | −0.00 |
| 2025 | 201.79 | **196.87** | 196.19 | +0.67 |

*(TWh of P1 coal, all three COAL classes.)*

**So the prediction is: the repaired run reproduces the WARM keeper's coal
totals to within ~1.5 TWh in every year, and 2022 falls by ~34 TWh from the
registered cold keeper.** The ceiling sits above the warm keeper by 0.00–1.51
TWh, which is the bound's own slackness (it ignores hourly shape, must-run
floors and zonal balance), not headroom the solve is expected to use.

## WHAT EACH OUTCOME WOULD MEAN, SAID IN ADVANCE

* **Repaired coal lands at or just under the ceiling, near the warm column.**
  The diagnosis is confirmed end-to-end: the cap was the whole difference, and
  the repaired run is the keeper's recipe finally solved as written.
* **Repaired coal still EXCEEDS the ceiling.** The bound is violated by a solve
  that logged the budget line, which would mean the row is built but not
  reaching the LP — a second, deeper defect. Report it, do not compose.
* **Repaired coal lands well BELOW the warm column** (say < 225 TWh in 2022).
  Something other than the cap also moved between the two runs; the G-DRIFT
  audit (PRECOMMIT §5) would then be wrong somewhere and must be re-opened
  before anything is registered.
* **2020 / 2023 / 2024 move at all beyond rounding.** Those years violate in
  0/12 months, so a non-binding row is being added and nothing should move. A
  visible move there is evidence the row perturbs a degenerate optimum, which
  is worth reporting in its own right and does not by itself invalidate the
  repair.

## WHAT THIS IS NOT

It is not a gate and nothing is selected by it. No criterion is consulted, no
parameter is tuned, and the repaired run is not accepted or rejected on whether
it lands inside the table — the table exists so that a reader can tell whether
this session predicted its result or fitted its story to it. The promotion
decision remains the owner's (rule 31 `[R-RETAIN]`).
