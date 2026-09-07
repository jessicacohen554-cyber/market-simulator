# Scenario delta report — ERCOT — ercot_scenario_campaign_matrix_7e7ee4c943

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`CES-T80` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| CARB-MID+LOAD-HI | `b99311bb1f3032e0` |  |
| CES-T80 | `e6638b058ce4d5fb` | **REF** |
| VOL-HI | `76ef5a80df6a9277` |  |

## Headline deltas vs `CES-T80` (final cached year)

Final cached year on disk: **2030**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| CARB-MID+LOAD-HI | 317.099 | 15.488 | 0.000 | 538869515.134 | 0 | 0.000 | 4640.210 | 443.830 | 4.908 | 0.384 |
| CES-T80 | 301.611 | 0.000 | 0.000 | 143667237.858 | 0 | 0.000 | 4196.380 | 0.000 | 0.000 | 0.394 |
| VOL-HI | 312.865 | 11.255 | 0.000 | 127220357.427 | 0 | 0.000 | 4092.420 | -103.960 | 0.000 | 0.372 |

## Cumulative CO2 delta vs `CES-T80` (Mt)

Running sum of the per-year CO2 delta, through **2030**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| CARB-MID+LOAD-HI | 2030 | 123.012 |
| CES-T80 | 2030 | 0.000 |
| VOL-HI | 2030 | 20.035 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| CARB-MID+LOAD-HI | gas_cc | -0.047 | 1.588 | 0.268 |
| CARB-MID+LOAD-HI | gas_cc_ccs | 3.047 | 24.368 | 0.946 |
| CARB-MID+LOAD-HI | gas_ct | 3.000 | 26.627 | 13.861 |
| CARB-MID+LOAD-HI | gas_st | 0.000 | 0.583 | 0.414 |
| CARB-MID+LOAD-HI | solar | -6.000 | -13.986 | 0.000 |
| CARB-MID+LOAD-HI | wind | 0.000 | -4.517 | 0.000 |
| VOL-HI | gas_cc | 3.185 | 25.076 | 9.505 |
| VOL-HI | gas_cc_ccs | -0.185 | -0.350 | -0.074 |
| VOL-HI | gas_ct | 0.500 | 4.100 | 2.048 |
| VOL-HI | gas_st | 0.000 | -0.329 | -0.224 |
| VOL-HI | solar | 1.500 | 3.399 | 0.000 |
| VOL-HI | wind | -5.000 | -15.292 | 0.000 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| CARB-MID+LOAD-HI | Houston | 75.287 | 0.876 |
| CARB-MID+LOAD-HI | North | 115.917 | 10.691 |
| CARB-MID+LOAD-HI | Northeast | 21.029 | 0.028 |
| CARB-MID+LOAD-HI | South | 26.337 | -0.186 |
| CARB-MID+LOAD-HI | South_Central | 59.280 | -0.542 |
| CARB-MID+LOAD-HI | West | 19.249 | 4.622 |
| VOL-HI | Houston | 74.771 | 0.359 |
| VOL-HI | North | 112.171 | 6.945 |
| VOL-HI | Northeast | 20.987 | -0.014 |
| VOL-HI | South | 26.497 | -0.026 |
| VOL-HI | South_Central | 59.731 | -0.090 |
| VOL-HI | West | 18.709 | 4.081 |

## Capacity-evolution deltas vs `CES-T80` (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| CARB-MID+LOAD-HI | build | gas_cc | 8018.8 | 3000.0 |
| CARB-MID+LOAD-HI | build | gas_ct | 6636.4 | 3000.0 |
| CARB-MID+LOAD-HI | build | solar | 2654.6 | -6000.0 |
| CARB-MID+LOAD-HI | build | wind | 10000.0 | 0.0 |
| CARB-MID+LOAD-HI | retirement | gas_st | 446.0 | 0.0 |
| CARB-MID+LOAD-HI | retrofit | gas_cc_ccs | 8995.7 | 3046.8 |
| CES-T80 | build | gas_cc | 5018.8 | 0.0 |
| CES-T80 | build | gas_ct | 3636.4 | 0.0 |
| CES-T80 | build | solar | 8654.6 | 0.0 |
| CES-T80 | build | wind | 10000.0 | 0.0 |
| CES-T80 | retirement | gas_st | 446.0 | 0.0 |
| CES-T80 | retrofit | gas_cc_ccs | 5948.9 | 0.0 |
| VOL-HI | build | gas_cc | 8018.8 | 3000.0 |
| VOL-HI | build | gas_ct | 4136.4 | 500.0 |
| VOL-HI | build | solar | 10154.6 | 1500.0 |
| VOL-HI | build | wind | 5000.0 | 0.0 |
| VOL-HI | retirement | gas_st | 446.0 | 0.0 |
| VOL-HI | retrofit | gas_cc_ccs | 5763.8 | -185.2 |

## Notes & definitions

- Every delta is `case − CES-T80` on the same year.
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
