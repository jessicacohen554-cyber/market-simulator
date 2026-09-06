# Scenario matrix -- NYISO -- nyiso_scenario_campaign_matrix_81af4882ee

**DETERMINISTIC SCENARIO RANGE -- NOT A PROBABILITY BAND**

13 named AEO/IPM-style cases (docs/handoffs/probability-bounds-plan-2026-07.md §1.2), not a factorial sweep and not a sampled distribution. No likelihood attaches to any case or to the envelope between them.

## Cases run

| Case | Cache key |
|---|---|
| LOAD-HI | `470338150a2f85a0` |
| LOAD-HI-ORGANIC | `bf50c8305ba3c4ee` |
| REF | `aed447f88457dff7` |

## Emissions trajectory (Mt CO2)

| Year | LOAD-HI | LOAD-HI-ORGANIC | REF |
|---|---|---|---|
| 2026 | 25.38 | 25.37 | 23.69 |
| 2027 | 27.07 | 27.09 | 24.59 |
| 2028 | 27.66 | 27.73 | 24.11 |
| 2029 | 27.65 | 27.75 | 23.75 |
| 2030 | 26.23 | 26.31 | 20.89 |

## Envelope (min/max across cases)

| Year | Min Mt (case) | Max Mt (case) |
|---|---|---|
| 2026 | 23.69 (REF) | 25.38 (LOAD-HI) |
| 2027 | 24.59 (REF) | 27.09 (LOAD-HI-ORGANIC) |
| 2028 | 24.11 (REF) | 27.73 (LOAD-HI-ORGANIC) |
| 2029 | 23.75 (REF) | 27.75 (LOAD-HI-ORGANIC) |
| 2030 | 20.89 (REF) | 26.31 (LOAD-HI-ORGANIC) |
