# Scenario matrix -- ERCOT -- ercot_ces_premium_matrix_poc_63d7e388c9

**DETERMINISTIC SCENARIO RANGE -- NOT A PROBABILITY BAND**

13 named AEO/IPM-style cases (docs/handoffs/probability-bounds-plan-2026-07.md §1.2), not a factorial sweep and not a sampled distribution. No likelihood attaches to any case or to the envelope between them.

## Cases run

| Case | Cache key |
|---|---|
| BAU | `d88c8585e76f2935` |
| CES-20 | `075e6aa30813f061` |
| CES-40 | `383509581661faba` |

## Emissions trajectory (Mt CO2)

| Year | BAU | CES-20 | CES-40 |
|---|---|---|---|
| 2026 | 189.17 | 189.17 | 189.17 |
| 2027 | 206.58 | 206.58 | 206.58 |
| 2028 | 232.30 | 232.26 | 232.25 |
| 2029 | 260.98 | 243.65 | 243.54 |
| 2030 | 285.32 | 257.68 | 257.64 |

## Envelope (min/max across cases)

| Year | Min Mt (case) | Max Mt (case) |
|---|---|---|
| 2026 | 189.17 (BAU) | 189.17 (BAU) |
| 2027 | 206.58 (BAU) | 206.58 (BAU) |
| 2028 | 232.25 (CES-40) | 232.30 (BAU) |
| 2029 | 243.54 (CES-40) | 260.98 (BAU) |
| 2030 | 257.64 (CES-40) | 285.32 (BAU) |
