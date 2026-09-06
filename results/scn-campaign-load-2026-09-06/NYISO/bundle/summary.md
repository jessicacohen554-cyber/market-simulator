# Scenario matrix -- NYISO -- nyiso_scenario_campaign_matrix_84955cc82d

**DETERMINISTIC SCENARIO RANGE -- NOT A PROBABILITY BAND**

13 named AEO/IPM-style cases (docs/handoffs/probability-bounds-plan-2026-07.md §1.2), not a factorial sweep and not a sampled distribution. No likelihood attaches to any case or to the envelope between them.

## Cases run

| Case | Cache key |
|---|---|
| LOAD-HI | `c2ceaefa4afafcda` |
| LOAD-HI-ORGANIC | `27f19f22105ab6cb` |
| REF | `f10cc93084b4c0db` |

## Emissions trajectory (Mt CO2)

| Year | LOAD-HI | LOAD-HI-ORGANIC | REF |
|---|---|---|---|
| 2026 | 25.38 | 25.37 | 23.69 |
| 2027 | 27.07 | 27.09 | 24.59 |
| 2028 | 20.27 | 20.34 | 17.16 |
| 2029 | 15.99 | 16.09 | 13.71 |
| 2030 | 14.02 | 14.17 | 10.90 |

## Envelope (min/max across cases)

| Year | Min Mt (case) | Max Mt (case) |
|---|---|---|
| 2026 | 23.69 (REF) | 25.38 (LOAD-HI) |
| 2027 | 24.59 (REF) | 27.09 (LOAD-HI-ORGANIC) |
| 2028 | 17.16 (REF) | 20.34 (LOAD-HI-ORGANIC) |
| 2029 | 13.71 (REF) | 16.09 (LOAD-HI-ORGANIC) |
| 2030 | 10.90 (REF) | 14.17 (LOAD-HI-ORGANIC) |
