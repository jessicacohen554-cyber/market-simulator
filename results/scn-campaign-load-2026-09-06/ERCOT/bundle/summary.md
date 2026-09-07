# Scenario matrix -- ERCOT -- ercot_scenario_campaign_matrix_81af49756e

**DETERMINISTIC SCENARIO RANGE -- NOT A PROBABILITY BAND**

13 named AEO/IPM-style cases (docs/handoffs/probability-bounds-plan-2026-07.md §1.2), not a factorial sweep and not a sampled distribution. No likelihood attaches to any case or to the envelope between them.

## Cases run

| Case | Cache key |
|---|---|
| LOAD-HI | `ec2ea8193e2e45a1` |
| LOAD-HI-ORGANIC | `0c87f2f2467e95b3` |
| REF | `de9c68e19316910e` |

## Emissions trajectory (Mt CO2)

| Year | LOAD-HI | LOAD-HI-ORGANIC | REF |
|---|---|---|---|
| 2026 | 256.02 | 255.26 | 214.39 |
| 2027 | 298.77 | 294.83 | 255.97 |
| 2028 | 301.53 | 301.58 | 285.70 |
| 2029 | 313.15 | 313.17 | 297.24 |
| 2030 | 325.46 | 325.47 | 312.87 |

## Envelope (min/max across cases)

| Year | Min Mt (case) | Max Mt (case) |
|---|---|---|
| 2026 | 214.39 (REF) | 256.02 (LOAD-HI) |
| 2027 | 255.97 (REF) | 298.77 (LOAD-HI) |
| 2028 | 285.70 (REF) | 301.58 (LOAD-HI-ORGANIC) |
| 2029 | 297.24 (REF) | 313.17 (LOAD-HI-ORGANIC) |
| 2030 | 312.87 (REF) | 325.47 (LOAD-HI-ORGANIC) |
