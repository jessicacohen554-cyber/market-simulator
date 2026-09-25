# FINDING — PJM-NEXT card 3: the unit-partial-derate lane is bounded at ≤ 0.27 TWh/yr (2026-09-25)

Zero LP. Handoff item 3 (`unit_partial_outage_windows`, not armed): "the HEAD deriver finds 155 raw
baseload-coal plateaus and emits 0". The proposed card was a detector change: a partial-appropriate
revealed-availability test.

## Measurement

At main `06d9a9da`, `scripts/data/derive_campd_unit_outages.py --iso PJM --years 2019..2025
--partial-windows` was run twice, both times written to scratch (**no `data/raw` file touched**):

- **with `--no-inmerit-filter`** (raw plateaus): **16 windows**, on **two plants**. These are Brunner Island
  3140 unit 3 (847.8 MW; 6 windows) and Chesterfield 3797 units 5/6 (358 / 724 MW; 10 windows). Durations
  are 5–12 days and derate factors 0.56–0.85.
- **with the HEAD filter**: **0 windows**. This reproduces the handoff's "emits 0".

The handoff's "155 raw" does not reproduce at this pin. That figure came from R-PJM's RESULT §6; the unit
set has moved since then (COAL-SUB, F1 vintage fleet).

**Upper bound on what arming could move.** Summing capacity × (1 − derate) × hours over every raw window,
**as if every one of them survived any filter**, gives:

| year | windows | derated energy-capacity (GWh) |
|---|---|---|
| 2019 | 5 | 151.9 |
| 2020 | 0 | 0 |
| 2021 | 4 | 268.0 |
| 2022 | 5 | 171.7 |
| 2023 | 1 | 47.1 |
| 2024 | 1 | 50.3 |
| 2025 | 0 | 0 |

That is at most **0.27 TWh in any year**, and it is a ceiling on capacity withheld, not on generation
displaced. The C1 misses this lane could touch are 8–26 TWh.

## Conclusion

A detector change is well designed in principle and has zero free parameters: drop a plateau only if the
unit reached its normal ceiling, `_CEILING_FRAC` × ref, in ≥ `min_inmerit_hours` tight hours. Even so,
**it cannot move any PJM criterion by a detectable amount at this pin.** Card 3 is **deprioritized**, on
magnitude and not on the residual: it cannot be a root cause of any open PJM gate. The committed stale
`campd-partial-outages-PJM.csv` (43/24/9 rows, 2023–25) stays **unarmed**, as the handoff says.
Matrix: `unit_partial_outage_windows` PJM cell unchanged. This records a magnitude bound, not a tested
verdict.
