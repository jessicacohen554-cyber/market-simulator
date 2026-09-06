# Scenario delta report — NEISO — neiso_scenario_campaign_matrix_5fda408506

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`REF` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| LOAD-HI | `0d5c394b6c4e5cb6` |  |
| REF | `8878d29743555b45` | **REF** |

## Headline deltas vs `REF` (final cached year)

Final cached year on disk: **2030**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| LOAD-HI | 6.357 | 0.251 | 4.877 | 0.000 | 50.200 | 0.000 | 53.590 | 0.370 | 0.000 | 0.594 |
| REF | 6.106 | 0.000 | 4.766 | 0.000 | 0.000 | 0.000 | 53.220 | 0.000 | 0.000 | 0.588 |

## Cumulative CO2 delta vs `REF` (Mt)

Running sum of the per-year CO2 delta, through **2030**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| LOAD-HI | 2030 | 2.623 |
| REF | 2030 | 0.000 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| LOAD-HI | biomass | 0.000 | 0.071 | 0.006 |
| LOAD-HI | gas_cc | -0.507 | 0.261 | 0.092 |
| LOAD-HI | gas_cc_ccs | 1.018 | 3.064 | 0.141 |
| LOAD-HI | gas_ct | 0.051 | 0.019 | 0.008 |
| LOAD-HI | gas_st | 0.001 | 0.010 | 0.003 |
| LOAD-HI | import | 0.000 | 0.287 | 0.000 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| LOAD-HI | Boston | 1.104 | 0.045 |
| LOAD-HI | Central | 2.829 | 0.134 |
| LOAD-HI | Connecticut | 0.886 | 0.018 |
| LOAD-HI | North | 1.539 | 0.054 |

## Capacity-evolution deltas vs `REF` (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| LOAD-HI | build | gas_cc | 1000.0 | 0.0 |
| LOAD-HI | build | gas_ct | 50.2 | 50.2 |
| LOAD-HI | build | solar | 2000.0 | 0.0 |
| LOAD-HI | build | wind | 1000.0 | 0.0 |
| LOAD-HI | retirement | coal | 108.0 | 0.0 |
| LOAD-HI | retirement | gas_cc | 2041.1 | -511.9 |
| LOAD-HI | retirement | gas_ct | 1.6 | 0.0 |
| LOAD-HI | retirement | gas_st | 95.8 | -1.6 |
| LOAD-HI | retrofit | gas_cc_ccs | 8709.3 | 1018.0 |
| REF | build | gas_cc | 1000.0 | 0.0 |
| REF | build | solar | 2000.0 | 0.0 |
| REF | build | wind | 1000.0 | 0.0 |
| REF | retirement | coal | 108.0 | 0.0 |
| REF | retirement | gas_cc | 2552.9 | 0.0 |
| REF | retirement | gas_ct | 1.6 | 0.0 |
| REF | retirement | gas_st | 97.4 | 0.0 |
| REF | retrofit | gas_cc_ccs | 7691.3 | 0.0 |

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
- Case `LOAD-HI` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `LOAD-HI` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- No --financial-reports-root given — captured prices cover the wind/solar pools only.
