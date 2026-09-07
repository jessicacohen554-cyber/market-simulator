# Scenario delta report — ERCOT — ercot_scenario_campaign_matrix_7e7ee4c943

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`CES-P20+VOL-HI` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| ALL-CLEAN | `619cfffde44422b2` |  |
| CES-P20+VOL-HI | `5b7774c817ee425b` | **REF** |

## Headline deltas vs `CES-P20+VOL-HI` (final cached year)

Final cached year on disk: **2030**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| ALL-CLEAN | 317.099 | 14.020 | 0.000 | 538869515.134 | 0 | 0.000 | 4640.210 | 554.230 | 0.000 | 0.387 |
| CES-P20+VOL-HI | 303.079 | 0.000 | 0.000 | 128531459.277 | 0 | 0.000 | 4085.980 | 0.000 | 0.000 | 0.403 |

## Cumulative CO2 delta vs `CES-P20+VOL-HI` (Mt)

Running sum of the per-year CO2 delta, through **2030**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| ALL-CLEAN | 2030 | 129.708 |
| CES-P20+VOL-HI | 2030 | 0.000 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| ALL-CLEAN | gas_cc | -0.041 | 0.898 | -0.747 |
| ALL-CLEAN | gas_cc_ccs | 0.041 | 0.240 | 0.168 |
| ALL-CLEAN | gas_ct | 3.000 | 26.694 | 13.943 |
| ALL-CLEAN | gas_st | 0.000 | 0.938 | 0.657 |
| ALL-CLEAN | solar | -6.000 | -13.595 | 0.000 |
| ALL-CLEAN | wind | 3.000 | 9.175 | 0.000 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| ALL-CLEAN | Houston | 75.287 | 3.640 |
| ALL-CLEAN | North | 115.917 | 12.033 |
| ALL-CLEAN | Northeast | 21.029 | 0.041 |
| ALL-CLEAN | South | 26.337 | -0.082 |
| ALL-CLEAN | South_Central | 59.280 | -1.267 |
| ALL-CLEAN | West | 19.249 | -0.345 |

## Capacity-evolution deltas vs `CES-P20+VOL-HI` (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| ALL-CLEAN | build | gas_cc | 8018.8 | 0.0 |
| ALL-CLEAN | build | gas_ct | 6636.4 | 3000.0 |
| ALL-CLEAN | build | solar | 2654.6 | -6000.0 |
| ALL-CLEAN | build | wind | 10000.0 | 3000.0 |
| ALL-CLEAN | retirement | gas_st | 446.0 | 0.0 |
| ALL-CLEAN | retrofit | gas_cc_ccs | 8995.7 | 41.1 |
| CES-P20+VOL-HI | build | gas_cc | 8018.8 | 0.0 |
| CES-P20+VOL-HI | build | gas_ct | 3636.4 | 0.0 |
| CES-P20+VOL-HI | build | solar | 8654.6 | 0.0 |
| CES-P20+VOL-HI | build | wind | 7000.0 | 0.0 |
| CES-P20+VOL-HI | retirement | gas_st | 446.0 | 0.0 |
| CES-P20+VOL-HI | retrofit | gas_cc_ccs | 8954.6 | 0.0 |

## Notes & definitions

- Every delta is `case − CES-P20+VOL-HI` on the same year.
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
