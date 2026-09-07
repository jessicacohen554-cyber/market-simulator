# Scenario delta report — MISO — miso_scenario_campaign_matrix_982d651e2b

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`CARB-HI` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| CARB-HI | `40bc61fac2b5271d` | **REF** |
| CARB-MID+LOAD-HI | `e644893331d7708f` |  |

## Headline deltas vs `CARB-HI` (final cached year)

Final cached year on disk: **2030**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| CARB-HI | 375.910 | 0.000 | 0.000 | 2824183.485 | 16098.800 | 0.000 | 200.220 | 0.000 | 0.000 | 0.327 |
| CARB-MID+LOAD-HI | 459.906 | 83.996 | 0.000 | 42391105.879 | 16098.800 | 0.000 | 998.220 | 798.000 | 0.000 | 0.290 |

## Cumulative CO2 delta vs `CARB-HI` (Mt)

Running sum of the per-year CO2 delta, through **2030**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| CARB-HI | 2030 | 0.000 |
| CARB-MID+LOAD-HI | 2030 | 284.073 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| CARB-MID+LOAD-HI | biomass | 0.000 | 0.205 | 0.320 |
| CARB-MID+LOAD-HI | coal | 0.000 | 16.635 | 17.472 |
| CARB-MID+LOAD-HI | gas_cc | -0.007 | 6.446 | 2.902 |
| CARB-MID+LOAD-HI | gas_cc_ccs | 0.007 | 0.036 | 0.019 |
| CARB-MID+LOAD-HI | gas_ct | 0.000 | 59.042 | 39.549 |
| CARB-MID+LOAD-HI | gas_st | 0.000 | 17.825 | 11.211 |
| CARB-MID+LOAD-HI | oil | 0.000 | 12.551 | 12.523 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| CARB-MID+LOAD-HI | MISO-East | 102.029 | 21.009 |
| CARB-MID+LOAD-HI | MISO-Illinois | 39.848 | 5.521 |
| CARB-MID+LOAD-HI | MISO-Indiana | 86.249 | 9.001 |
| CARB-MID+LOAD-HI | MISO-Plains | 70.654 | 11.402 |
| CARB-MID+LOAD-HI | MISO-South | 109.261 | 28.939 |
| CARB-MID+LOAD-HI | MISO-West | 51.864 | 8.124 |

## Capacity-evolution deltas vs `CARB-HI` (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| CARB-HI | build | gas_cc | 3722.0 | 0.0 |
| CARB-HI | build | gas_ct | 18129.6 | 0.0 |
| CARB-HI | build | iron_air | 9600.0 | 0.0 |
| CARB-HI | build | li_ion_4hr | 6400.0 | 0.0 |
| CARB-HI | build | oil | 17.0 | 0.0 |
| CARB-HI | build | solar | 6000.0 | 0.0 |
| CARB-HI | build | wind | 4000.0 | 0.0 |
| CARB-HI | retirement | biomass | 16.0 | 0.0 |
| CARB-HI | retirement | coal | 7794.9 | 0.0 |
| CARB-HI | retirement | gas_ct | 716.8 | 0.0 |
| CARB-HI | retirement | gas_st | 1855.8 | 0.0 |
| CARB-HI | retirement | nuclear | 617.0 | 0.0 |
| CARB-HI | retirement | oil | 119.0 | 0.0 |
| CARB-HI | retrofit | gas_cc_ccs | 8991.3 | 0.0 |
| CARB-MID+LOAD-HI | build | gas_cc | 3722.0 | 0.0 |
| CARB-MID+LOAD-HI | build | gas_ct | 18129.6 | 0.0 |
| CARB-MID+LOAD-HI | build | iron_air | 9600.0 | 0.0 |
| CARB-MID+LOAD-HI | build | li_ion_4hr | 6400.0 | 0.0 |
| CARB-MID+LOAD-HI | build | oil | 17.0 | 0.0 |
| CARB-MID+LOAD-HI | build | solar | 6000.0 | 0.0 |
| CARB-MID+LOAD-HI | build | wind | 4000.0 | 0.0 |
| CARB-MID+LOAD-HI | retirement | biomass | 16.0 | 0.0 |
| CARB-MID+LOAD-HI | retirement | coal | 7794.9 | 0.0 |
| CARB-MID+LOAD-HI | retirement | gas_ct | 716.8 | 0.0 |
| CARB-MID+LOAD-HI | retirement | gas_st | 1855.8 | 0.0 |
| CARB-MID+LOAD-HI | retirement | nuclear | 617.0 | 0.0 |
| CARB-MID+LOAD-HI | retirement | oil | 119.0 | 0.0 |
| CARB-MID+LOAD-HI | retrofit | gas_cc_ccs | 8998.0 | 6.7 |

## Notes & definitions

- Every delta is `case − CARB-HI` on the same year.
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
- Case `CARB-HI` 2028: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CARB-HI` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CARB-HI` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029`, `gas_ct_adequacy_2030` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CARB-MID+LOAD-HI` 2028: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CARB-MID+LOAD-HI` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CARB-MID+LOAD-HI` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029`, `gas_ct_adequacy_2030` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- No --financial-reports-root given — captured prices cover the wind/solar pools only.
