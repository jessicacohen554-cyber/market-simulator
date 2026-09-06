# Scenario delta report — NYISO — nyiso_scenario_campaign_matrix_81af4882ee

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`REF` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| LOAD-HI | `470338150a2f85a0` |  |
| LOAD-HI-ORGANIC | `bf50c8305ba3c4ee` |  |
| REF | `aed447f88457dff7` | **REF** |

## Headline deltas vs `REF` (final cached year)

Final cached year on disk: **2030**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| LOAD-HI | 26.234 | 5.340 | 12.218 | 0.000 | 0 | 0.000 | 63.830 | 3.320 | 0.000 | 0.535 |
| LOAD-HI-ORGANIC | 26.313 | 5.420 | 12.216 | 0.000 | 0 | 0.000 | 64.020 | 3.510 | 0.000 | 0.534 |
| REF | 20.893 | 0.000 | 11.682 | 0.000 | 0 | 0.000 | 60.510 | 0.000 | 0.000 | 0.546 |

## Cumulative CO2 delta vs `REF` (Mt)

Running sum of the per-year CO2 delta, through **2030**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| LOAD-HI | 2030 | 16.953 |
| LOAD-HI-ORGANIC | 2030 | 17.211 |
| REF | 2030 | 0.000 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| LOAD-HI | biomass | 0.000 | 0.006 | 0.000 |
| LOAD-HI | gas_cc | -0.146 | 3.657 | 1.494 |
| LOAD-HI | gas_cc_ccs | 0.146 | 5.753 | 2.113 |
| LOAD-HI | gas_ct | 0.000 | 0.922 | 0.550 |
| LOAD-HI | gas_st | 0.000 | 2.227 | 1.183 |
| LOAD-HI | import | 0.000 | 1.251 | 0.000 |
| LOAD-HI-ORGANIC | biomass | 0.000 | 0.006 | 0.000 |
| LOAD-HI-ORGANIC | gas_cc | -0.146 | 3.445 | 1.420 |
| LOAD-HI-ORGANIC | gas_cc_ccs | 0.146 | 5.566 | 2.041 |
| LOAD-HI-ORGANIC | gas_ct | 0.000 | 1.030 | 0.612 |
| LOAD-HI-ORGANIC | gas_st | 0.000 | 2.522 | 1.346 |
| LOAD-HI-ORGANIC | import | 0.000 | 1.248 | 0.000 |
| LOAD-HI-ORGANIC | oil | 0.000 | 0.000 | 0.000 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| LOAD-HI | Capital_Hudson | 9.789 | 1.806 |
| LOAD-HI | Long_Island | 1.436 | 0.495 |
| LOAD-HI | Lower_Hudson | 0.005 | 0.002 |
| LOAD-HI | NYC | 11.152 | 2.215 |
| LOAD-HI | Upstate_West | 3.852 | 0.822 |
| LOAD-HI-ORGANIC | Capital_Hudson | 9.722 | 1.739 |
| LOAD-HI-ORGANIC | Long_Island | 1.489 | 0.549 |
| LOAD-HI-ORGANIC | Lower_Hudson | 0.004 | 0.002 |
| LOAD-HI-ORGANIC | NYC | 11.298 | 2.360 |
| LOAD-HI-ORGANIC | Upstate_West | 3.800 | 0.770 |

## Capacity-evolution deltas vs `REF` (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| LOAD-HI | build | gas_cc | 1000.0 | 0.0 |
| LOAD-HI | build | solar | 1843.4 | 0.0 |
| LOAD-HI | build | wind | 1000.0 | 0.0 |
| LOAD-HI | retirement | biomass | 8.0 | 0.0 |
| LOAD-HI | retirement | gas_ct | 19.8 | 0.0 |
| LOAD-HI | retrofit | gas_cc_ccs | 6620.6 | 146.0 |
| LOAD-HI-ORGANIC | build | gas_cc | 1000.0 | 0.0 |
| LOAD-HI-ORGANIC | build | solar | 1843.4 | 0.0 |
| LOAD-HI-ORGANIC | build | wind | 1000.0 | 0.0 |
| LOAD-HI-ORGANIC | retirement | biomass | 8.0 | 0.0 |
| LOAD-HI-ORGANIC | retirement | gas_ct | 19.8 | 0.0 |
| LOAD-HI-ORGANIC | retrofit | gas_cc_ccs | 6620.6 | 146.0 |
| REF | build | gas_cc | 1000.0 | 0.0 |
| REF | build | solar | 1843.4 | 0.0 |
| REF | build | wind | 1000.0 | 0.0 |
| REF | retirement | biomass | 8.0 | 0.0 |
| REF | retirement | gas_ct | 19.8 | 0.0 |
| REF | retrofit | gas_cc_ccs | 6474.6 | 0.0 |

## Notes & definitions

- Every delta is `case − REF` on the same year.
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
