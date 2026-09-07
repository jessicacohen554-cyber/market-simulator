# Scenario delta report — ERCOT — ercot_scenario_campaign_matrix_7e7ee4c943

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`CES-P10` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| CES-P10 | `17e0b252e13a484a` | **REF** |
| CES-P20 | `5a89c34af859160c` |  |
| CES-P30 | `8588e1b0d055e772` |  |

## Headline deltas vs `CES-P10` (final cached year)

Final cached year on disk: **2030**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| CES-P10 | 302.836 | 0.000 | 0.000 | 130111087.793 | 0 | 0.000 | 4110.560 | 0.000 | 4.925 | 0.398 |
| CES-P20 | 303.079 | 0.243 | 0.000 | 128531459.277 | 0 | 0.000 | 4085.980 | -24.580 | 4.913 | 0.399 |
| CES-P30 | 299.586 | -3.250 | 0.000 | 132119833.248 | 0 | 0.000 | 4077.110 | -33.450 | 4.910 | 0.406 |

## Cumulative CO2 delta vs `CES-P10` (Mt)

Running sum of the per-year CO2 delta, through **2030**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| CES-P10 | 2030 | 0.000 |
| CES-P20 | 2030 | 0.569 |
| CES-P30 | 2030 | -5.065 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| CES-P20 | gas_cc | 0.015 | 0.110 | 0.391 |
| CES-P20 | gas_cc_ccs | -0.014 | -0.043 | -0.041 |
| CES-P20 | gas_ct | 0.000 | 0.010 | -0.015 |
| CES-P20 | gas_st | 0.000 | -0.134 | -0.092 |
| CES-P20 | solar | -2.000 | -4.517 | 0.000 |
| CES-P20 | wind | 2.000 | 6.114 | 0.000 |
| CES-P30 | gas_cc | -1.014 | -7.768 | -3.151 |
| CES-P30 | gas_cc_ccs | 0.014 | -0.503 | 0.012 |
| CES-P30 | gas_ct | 0.000 | 0.006 | -0.023 |
| CES-P30 | gas_st | 0.000 | -0.125 | -0.088 |
| CES-P30 | solar | -4.000 | -9.040 | 0.000 |
| CES-P30 | wind | 5.000 | 15.282 | 0.000 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| CES-P20 | Houston | 71.647 | -0.447 |
| CES-P20 | North | 103.884 | -1.344 |
| CES-P20 | Northeast | 20.987 | -0.006 |
| CES-P20 | South | 26.419 | -0.013 |
| CES-P20 | South_Central | 60.547 | 1.719 |
| CES-P20 | West | 19.594 | 0.334 |
| CES-P30 | Houston | 71.595 | -0.499 |
| CES-P30 | North | 102.303 | -2.925 |
| CES-P30 | Northeast | 20.989 | -0.004 |
| CES-P30 | South | 26.488 | 0.056 |
| CES-P30 | South_Central | 60.542 | 1.714 |
| CES-P30 | West | 17.669 | -1.591 |

## Capacity-evolution deltas vs `CES-P10` (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| CES-P10 | build | gas_cc | 8018.8 | 0.0 |
| CES-P10 | build | gas_ct | 3636.4 | 0.0 |
| CES-P10 | build | solar | 10654.6 | 0.0 |
| CES-P10 | build | wind | 5000.0 | 0.0 |
| CES-P10 | retirement | gas_st | 446.0 | 0.0 |
| CES-P10 | retrofit | gas_cc_ccs | 8969.5 | 0.0 |
| CES-P20 | build | gas_cc | 8018.8 | 0.0 |
| CES-P20 | build | gas_ct | 3636.4 | 0.0 |
| CES-P20 | build | solar | 8654.6 | -2000.0 |
| CES-P20 | build | wind | 7000.0 | 2000.0 |
| CES-P20 | retirement | gas_st | 446.0 | 0.0 |
| CES-P20 | retrofit | gas_cc_ccs | 8954.6 | -14.9 |
| CES-P30 | build | gas_cc | 7018.8 | -1000.0 |
| CES-P30 | build | gas_ct | 3636.4 | 0.0 |
| CES-P30 | build | solar | 6654.6 | -4000.0 |
| CES-P30 | build | wind | 10000.0 | 5000.0 |
| CES-P30 | retirement | gas_st | 446.0 | 0.0 |
| CES-P30 | retrofit | gas_cc_ccs | 8983.4 | 14.0 |

## Notes & definitions

- Every delta is `case − CES-P10` on the same year.
- `emissions_mt` is attributional in-ISO CO2 on the eGRID generation
  basis: `Σ dispatch × per-generator rate`. There is no marginal rate
  anywhere in the model (plan §2.5 G-E6); the DELTA between two
  full-system runs is itself the consequential number.
- import_co2_mt_reported is a REPORTED-ONLY disclosure line and is NEVER added into emissions_mt: the LP prices border carbon in the tranche VOM and holds import emission rates at zero so the scored total stays on the eGRID in-ISO generation basis. Tranche emission factors are the ISO's published ladder where one exists (CAISO IMPORT_TRANCHE_EF), zero for the contracted firm Hydro-Quebec seams (HQ_PhaseII, Highgate, HQ_hydro), and otherwise the CARB unspecified default 0.428 tCO2/MWh — a disclosed upper bound, not a measured seam rate.
- `unserved_mwh` is the slack column's annual energy. A case whose CO2
  falls while unserved energy rises has not decarbonized — read the two
  together. A CO2 number read under binding slack is understated by
  the shed energy (plan §2.4 G-L4).
- `backstop_built_mw` is the reserve-margin adequacy backstop's gas_ct
  on the books in the year (ledger `thermal_additions` rows tagged
  `source == "reserve_backstop"`, that year or earlier, net of a later
  retirement); `backstop_built_mwh` is those units' energy in the
  year's dispatch. It is the administratively-built share of a curve-ON
  ISO's response (PJM/MISO/NYISO/NEISO/CAISO); energy-only ERCOT has no
  backstop by market design, reads 0.0 here, and reports its adequacy
  through `unserved_mwh` instead (SCN-WS4b adequacy reading).
- `curtailment_twh` / the curtailment CSV are VRE potential minus
  delivered energy; `clean_share` is credit-weighted generation over
  total generation on each case's own crediting rule.
- No --financial-reports-root given — captured prices cover the wind/solar pools only.
