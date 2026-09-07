# Scenario delta report — ERCOT — ercot_scenario_campaign_matrix_7e7ee4c943

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`CARB-LO` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| CARB-HI | `73dadcb65d74acce` |  |
| CARB-LO | `c1e09985c3e4fa56` | **REF** |
| CARB-MID | `ab8d79646b49abbd` |  |

## Headline deltas vs `CARB-LO` (final cached year)

Final cached year on disk: **2030**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| CARB-HI | 302.130 | -0.134 | 0.000 | 130111087.793 | 0 | 0.000 | 4113.400 | 1.560 | 4.926 | 0.398 |
| CARB-LO | 302.264 | 0.000 | 0.000 | 130111087.793 | 0 | 0.000 | 4111.840 | 0.000 | 4.926 | 0.398 |
| CARB-MID | 302.235 | -0.029 | 0.000 | 130111087.793 | 0 | 0.000 | 4112.340 | 0.500 | 4.926 | 0.398 |

## Cumulative CO2 delta vs `CARB-LO` (Mt)

Running sum of the per-year CO2 delta, through **2030**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| CARB-HI | 2030 | -2.861 |
| CARB-LO | 2030 | 0.000 |
| CARB-MID | 2030 | -0.743 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| CARB-HI | coal | 0.000 | -0.009 | -0.009 |
| CARB-HI | gas_cc | -0.036 | -0.142 | -0.033 |
| CARB-HI | gas_cc_ccs | 0.036 | 0.300 | 0.011 |
| CARB-HI | gas_ct | 0.000 | -0.075 | -0.050 |
| CARB-HI | gas_st | 0.000 | -0.077 | -0.053 |
| CARB-HI | solar | 0.000 | -0.018 | 0.000 |
| CARB-HI | wind | 0.000 | 0.018 | 0.000 |
| CARB-MID | gas_cc | 0.000 | 0.049 | 0.022 |
| CARB-MID | gas_cc_ccs | 0.000 | 0.032 | 0.001 |
| CARB-MID | gas_ct | 0.000 | -0.041 | -0.024 |
| CARB-MID | gas_st | 0.000 | -0.041 | -0.029 |
| CARB-MID | solar | 0.000 | -0.018 | 0.000 |
| CARB-MID | wind | 0.000 | 0.018 | 0.000 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| CARB-HI | Houston | 74.870 | -0.019 |
| CARB-HI | North | 102.709 | -0.022 |
| CARB-HI | Northeast | 20.991 | -0.004 |
| CARB-HI | South | 26.452 | 0.200 |
| CARB-HI | South_Central | 58.832 | 0.004 |
| CARB-HI | West | 18.276 | -0.293 |
| CARB-MID | Houston | 74.888 | -0.001 |
| CARB-MID | North | 102.716 | -0.015 |
| CARB-MID | Northeast | 20.998 | 0.004 |
| CARB-MID | South | 26.253 | 0.001 |
| CARB-MID | South_Central | 58.826 | -0.002 |
| CARB-MID | West | 18.554 | -0.015 |

## Capacity-evolution deltas vs `CARB-LO` (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| CARB-HI | build | gas_cc | 8018.8 | 0.0 |
| CARB-HI | build | gas_ct | 3636.4 | 0.0 |
| CARB-HI | build | solar | 10654.6 | 0.0 |
| CARB-HI | build | wind | 5000.0 | 0.0 |
| CARB-HI | retirement | gas_st | 446.0 | 0.0 |
| CARB-HI | retrofit | gas_cc_ccs | 8965.3 | 36.4 |
| CARB-LO | build | gas_cc | 8018.8 | 0.0 |
| CARB-LO | build | gas_ct | 3636.4 | 0.0 |
| CARB-LO | build | solar | 10654.6 | 0.0 |
| CARB-LO | build | wind | 5000.0 | 0.0 |
| CARB-LO | retirement | gas_st | 446.0 | 0.0 |
| CARB-LO | retrofit | gas_cc_ccs | 8928.8 | 0.0 |
| CARB-MID | build | gas_cc | 8018.8 | 0.0 |
| CARB-MID | build | gas_ct | 3636.4 | 0.0 |
| CARB-MID | build | solar | 10654.6 | 0.0 |
| CARB-MID | build | wind | 5000.0 | 0.0 |
| CARB-MID | retirement | gas_st | 446.0 | 0.0 |
| CARB-MID | retrofit | gas_cc_ccs | 8928.8 | 0.0 |

## Notes & definitions

- Every delta is `case − CARB-LO` on the same year.
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
