# Scenario delta report — ERCOT — ercot_scenario_campaign_matrix_78b01278f2

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`REF` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| LOAD-HI | `31cf71afda5c610d` |  |
| LOAD-HI-ORGANIC | `c5255cea87fbaacf` |  |
| REF | `6e40769352a572ba` | **REF** |

## Headline deltas vs `REF` (final cached year)

Final cached year on disk: **2030**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| LOAD-HI | 342.281 | 13.407 | 0.000 | 538869515.134 | 0 | 0.000 | 4640.210 | 547.790 | 4.908 | 0.307 |
| LOAD-HI-ORGANIC | 342.284 | 13.410 | 0.000 | 538858662.605 | 0 | 0.000 | 4643.720 | 551.300 | 4.908 | 0.307 |
| REF | 328.874 | 0.000 | 0.000 | 127220357.427 | 0 | 0.000 | 4092.420 | 0.000 | 4.919 | 0.317 |

## Cumulative CO2 delta vs `REF` (Mt)

Running sum of the per-year CO2 delta, through **2030**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| LOAD-HI | 2030 | 130.355 |
| LOAD-HI-ORGANIC | 2030 | 125.728 |
| REF | 2030 | 0.000 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| LOAD-HI | gas_cc | 0.000 | 1.207 | 0.945 |
| LOAD-HI | gas_ct | 2.500 | 22.549 | 11.824 |
| LOAD-HI | gas_st | 0.000 | 0.912 | 0.639 |
| LOAD-HI | solar | -7.500 | -16.989 | 0.000 |
| LOAD-HI | wind | 5.000 | 15.299 | 0.000 |
| LOAD-HI-ORGANIC | gas_cc | 0.000 | 1.211 | 0.946 |
| LOAD-HI-ORGANIC | gas_ct | 2.500 | 22.549 | 11.824 |
| LOAD-HI-ORGANIC | gas_st | 0.000 | 0.915 | 0.640 |
| LOAD-HI-ORGANIC | solar | -7.500 | -16.987 | 0.000 |
| LOAD-HI-ORGANIC | wind | 5.000 | 15.296 | 0.000 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| LOAD-HI | Houston | 77.819 | 1.232 |
| LOAD-HI | North | 135.765 | 11.094 |
| LOAD-HI | Northeast | 21.029 | 0.042 |
| LOAD-HI | South | 26.594 | 0.097 |
| LOAD-HI | South_Central | 60.893 | 0.328 |
| LOAD-HI | West | 20.181 | 0.615 |
| LOAD-HI-ORGANIC | Houston | 77.819 | 1.232 |
| LOAD-HI-ORGANIC | North | 135.765 | 11.094 |
| LOAD-HI-ORGANIC | Northeast | 21.032 | 0.045 |
| LOAD-HI-ORGANIC | South | 26.594 | 0.097 |
| LOAD-HI-ORGANIC | South_Central | 60.893 | 0.328 |
| LOAD-HI-ORGANIC | West | 20.181 | 0.615 |

## Capacity-evolution deltas vs `REF` (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| LOAD-HI | build | gas_cc | 8018.8 | 0.0 |
| LOAD-HI | build | gas_ct | 6636.4 | 2500.0 |
| LOAD-HI | build | solar | 2654.6 | -7500.0 |
| LOAD-HI | build | wind | 10000.0 | 5000.0 |
| LOAD-HI | retirement | gas_st | 446.0 | 0.0 |
| LOAD-HI-ORGANIC | build | gas_cc | 8018.8 | 0.0 |
| LOAD-HI-ORGANIC | build | gas_ct | 6636.4 | 2500.0 |
| LOAD-HI-ORGANIC | build | solar | 2654.6 | -7500.0 |
| LOAD-HI-ORGANIC | build | wind | 10000.0 | 5000.0 |
| LOAD-HI-ORGANIC | retirement | gas_st | 446.0 | 0.0 |
| REF | build | gas_cc | 8018.8 | 0.0 |
| REF | build | gas_ct | 4136.4 | 0.0 |
| REF | build | solar | 10154.6 | 0.0 |
| REF | build | wind | 5000.0 | 0.0 |
| REF | retirement | gas_st | 446.0 | 0.0 |

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
