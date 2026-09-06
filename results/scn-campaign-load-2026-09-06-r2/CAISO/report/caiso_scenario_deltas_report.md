# Scenario delta report — CAISO — caiso_scenario_campaign_matrix_0acbe61dd8

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`REF` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| LOAD-HI | `86bfde6ed2896b99` |  |
| LOAD-HI-ORGANIC | `ff8c04bc4eef6605` |  |
| REF | `2d16a246bb372e4a` | **REF** |

## Headline deltas vs `REF` (final cached year)

Final cached year on disk: **2030**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| LOAD-HI | 29.208 | 9.251 | 0.901 | 106162.576 | 14695.264 | 0.000 | 75.640 | 9.450 | 0.000 | 0.600 |
| LOAD-HI-ORGANIC | 29.446 | 9.488 | 0.829 | 188778.721 | 17049.555 | 0.000 | 76.220 | 10.030 | 0.000 | 0.600 |
| REF | 19.957 | 0.000 | 0.297 | 15724.348 | 10161.572 | 0.000 | 66.190 | 0.000 | 0.000 | 0.645 |

## Cumulative CO2 delta vs `REF` (Mt)

Running sum of the per-year CO2 delta, through **2030**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| LOAD-HI | 2030 | 31.460 |
| LOAD-HI-ORGANIC | 2030 | 31.941 |
| REF | 2030 | 0.000 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| LOAD-HI | gas_cc | -0.083 | 10.874 | 4.379 |
| LOAD-HI | gas_cc_ccs | 0.082 | 3.653 | 0.138 |
| LOAD-HI | gas_ct | 4.534 | 9.718 | 4.733 |
| LOAD-HI | import | 0.000 | 2.255 | 0.000 |
| LOAD-HI | oil | 0.000 | 0.001 | 0.001 |
| LOAD-HI-ORGANIC | gas_cc | -0.083 | 10.394 | 4.198 |
| LOAD-HI-ORGANIC | gas_cc_ccs | 0.082 | 3.451 | 0.130 |
| LOAD-HI-ORGANIC | gas_ct | 6.888 | 10.559 | 5.159 |
| LOAD-HI-ORGANIC | import | 0.000 | 2.036 | 0.000 |
| LOAD-HI-ORGANIC | oil | 0.000 | 0.001 | 0.001 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| LOAD-HI | LA_BASIN | 6.411 | 1.887 |
| LOAD-HI | NP15 | 12.430 | 4.326 |
| LOAD-HI | SDGE | 1.874 | 0.580 |
| LOAD-HI | SP15_rest | 3.889 | 1.388 |
| LOAD-HI | ZP26 | 4.604 | 1.069 |
| LOAD-HI-ORGANIC | LA_BASIN | 6.560 | 2.035 |
| LOAD-HI-ORGANIC | NP15 | 12.603 | 4.499 |
| LOAD-HI-ORGANIC | SDGE | 1.880 | 0.586 |
| LOAD-HI-ORGANIC | SP15_rest | 3.826 | 1.326 |
| LOAD-HI-ORGANIC | ZP26 | 4.578 | 1.042 |

## Capacity-evolution deltas vs `REF` (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| LOAD-HI | build | gas_cc | 2000.0 | 0.0 |
| LOAD-HI | build | gas_ct | 14695.3 | 4533.7 |
| LOAD-HI | build | solar | 4000.0 | 0.0 |
| LOAD-HI | build | wind | 1404.4 | 0.0 |
| LOAD-HI | retirement | biomass | 2.3 | 0.0 |
| LOAD-HI | retirement | gas_ct | 5.2 | 0.0 |
| LOAD-HI | retirement | gas_st | 1525.8 | 0.0 |
| LOAD-HI | retirement | nuclear | 1122.0 | 0.0 |
| LOAD-HI | retrofit | gas_cc_ccs | 8968.4 | 82.7 |
| LOAD-HI-ORGANIC | build | gas_cc | 2000.0 | 0.0 |
| LOAD-HI-ORGANIC | build | gas_ct | 17049.6 | 6888.0 |
| LOAD-HI-ORGANIC | build | solar | 4000.0 | 0.0 |
| LOAD-HI-ORGANIC | build | wind | 1404.4 | 0.0 |
| LOAD-HI-ORGANIC | retirement | biomass | 2.3 | 0.0 |
| LOAD-HI-ORGANIC | retirement | gas_ct | 5.2 | 0.0 |
| LOAD-HI-ORGANIC | retirement | gas_st | 1525.8 | 0.0 |
| LOAD-HI-ORGANIC | retirement | nuclear | 1122.0 | 0.0 |
| LOAD-HI-ORGANIC | retrofit | gas_cc_ccs | 8968.4 | 82.7 |
| REF | build | gas_cc | 2000.0 | 0.0 |
| REF | build | gas_ct | 10161.6 | 0.0 |
| REF | build | solar | 4000.0 | 0.0 |
| REF | build | wind | 1404.4 | 0.0 |
| REF | retirement | biomass | 2.3 | 0.0 |
| REF | retirement | gas_ct | 5.2 | 0.0 |
| REF | retirement | gas_st | 1525.8 | 0.0 |
| REF | retirement | nuclear | 1122.0 | 0.0 |
| REF | retrofit | gas_cc_ccs | 8885.7 | 0.0 |

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
- Case `LOAD-HI` 2027: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `LOAD-HI` 2028: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027`, `gas_ct_adequacy_2028` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `LOAD-HI` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027`, `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `LOAD-HI` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027`, `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029`, `gas_ct_adequacy_2030` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `LOAD-HI-ORGANIC` 2027: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `LOAD-HI-ORGANIC` 2028: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027`, `gas_ct_adequacy_2028` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `LOAD-HI-ORGANIC` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027`, `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `LOAD-HI-ORGANIC` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027`, `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029`, `gas_ct_adequacy_2030` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `REF` 2027: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `REF` 2028: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027`, `gas_ct_adequacy_2028` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `REF` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027`, `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `REF` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027`, `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029`, `gas_ct_adequacy_2030` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- No --financial-reports-root given — captured prices cover the wind/solar pools only.
