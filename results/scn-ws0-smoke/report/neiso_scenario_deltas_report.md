# Scenario delta report — NEISO — neiso_scenario_campaign_matrix_1e220957bc

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`REF` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| CARB | `eed460b6ddfaab1c` |  |
| REF | `c3592c1adbc8ac17` | **REF** |

## Headline deltas vs `REF` (final cached year)

Final cached year on disk: **2026**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|
| CARB | 13.599 | -2.709 | 6.427 | 0.000 | 61.180 | 9.760 | 0.000 | 0.345 |
| REF | 16.308 | 0.000 | 4.572 | 0.000 | 51.420 | 0.000 | 0.000 | 0.345 |

## Cumulative CO2 delta vs `REF` (Mt)

Running sum of the per-year CO2 delta, through **2026**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| CARB | 2026 | -2.709 |
| REF | 2026 | 0.000 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| CARB | biomass | 0.000 | 1.375 | 0.000 |
| CARB | gas_cc | 0.000 | -5.813 | -2.644 |
| CARB | gas_ct | 0.000 | -0.101 | -0.064 |
| CARB | gas_st | 0.000 | -0.005 | -0.002 |
| CARB | import | 0.000 | 4.564 | 0.000 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| CARB | Boston | 3.272 | -0.662 |
| CARB | Central | 1.964 | -0.338 |
| CARB | Connecticut | 5.768 | -1.034 |
| CARB | North | 2.595 | -0.676 |

## Capacity-evolution deltas vs `REF` (ledger totals, MW)

_No evolution ledgers found (backcast or fixture cache)._

## Notes & definitions

- Every delta is `case − REF` on the same year.
- `emissions_mt` is attributional in-ISO CO2 on the eGRID generation
  basis: `Σ dispatch × per-generator rate`. There is no marginal rate
  anywhere in the model (plan §2.5 G-E6); the DELTA between two
  full-system runs is itself the consequential number.
- import_co2_mt_reported is a REPORTED-ONLY disclosure line and is NEVER added into emissions_mt: the LP prices border carbon in the tranche VOM and holds import emission rates at zero so the scored total stays on the eGRID in-ISO generation basis. Tranche emission factors are the ISO's published ladder where one exists (CAISO IMPORT_TRANCHE_EF), zero for the contracted firm Hydro-Quebec seams (HQ_PhaseII, Highgate, HQ_hydro), and otherwise the CARB unspecified default 0.428 tCO2/MWh — a disclosed upper bound, not a measured seam rate.
- `unserved_mwh` is the slack column's annual energy. A case whose CO2
  falls while unserved energy rises has not decarbonized — read the two
  together.
- `curtailment_twh` / the curtailment CSV are VRE potential minus
  delivered energy; `clean_share` is credit-weighted generation over
  total generation on each case's own crediting rule.
- No --financial-reports-root given — captured prices cover the wind/solar pools only.
