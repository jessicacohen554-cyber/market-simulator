# Scenario delta report — CAISO — caiso_scenario_campaign_matrix_41367ccc55

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`REF` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| LOAD-HI | `7687ac2d1265ec14` |  |
| LOAD-HI-ORGANIC | `a3472da093262e47` |  |
| REF | `54a70e9a6e396cad` | **REF** |

## Headline deltas vs `REF` (final cached year)

Final cached year on disk: **2030**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| LOAD-HI | 41.390 | 10.231 | 1.299 | 106162.576 | 14695.264 | 0.000 | 78.540 | 8.340 | 0.000 | 0.548 |
| LOAD-HI-ORGANIC | 41.503 | 10.344 | 1.272 | 188778.721 | 17049.555 | 0.000 | 79.230 | 9.030 | 0.000 | 0.547 |
| REF | 31.160 | 0.000 | 0.666 | 15724.348 | 10161.572 | 0.000 | 70.200 | 0.000 | 0.000 | 0.577 |

## Cumulative CO2 delta vs `REF` (Mt)

Running sum of the per-year CO2 delta, through **2030**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| LOAD-HI | 2030 | 33.292 |
| LOAD-HI-ORGANIC | 2030 | 33.629 |
| REF | 2030 | 0.000 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| LOAD-HI | gas_cc | -0.249 | 5.817 | 2.239 |
| LOAD-HI | gas_cc_ccs | 0.249 | 6.688 | 2.185 |
| LOAD-HI | gas_ct | 4.534 | 11.823 | 5.806 |
| LOAD-HI | import | 0.000 | 1.778 | 0.000 |
| LOAD-HI | oil | 0.000 | 0.001 | 0.001 |
| LOAD-HI-ORGANIC | gas_cc | -0.249 | 5.485 | 2.117 |
| LOAD-HI-ORGANIC | gas_cc_ccs | 0.249 | 6.211 | 1.989 |
| LOAD-HI-ORGANIC | gas_ct | 6.888 | 12.671 | 6.236 |
| LOAD-HI-ORGANIC | import | 0.000 | 1.705 | 0.000 |
| LOAD-HI-ORGANIC | oil | 0.000 | 0.001 | 0.001 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| LOAD-HI | LA_BASIN | 7.208 | 1.792 |
| LOAD-HI | NP15 | 20.792 | 6.075 |
| LOAD-HI | SDGE | 4.050 | 1.172 |
| LOAD-HI | SP15_rest | 3.505 | 0.428 |
| LOAD-HI | ZP26 | 5.836 | 0.763 |
| LOAD-HI-ORGANIC | LA_BASIN | 7.351 | 1.936 |
| LOAD-HI-ORGANIC | NP15 | 21.024 | 6.306 |
| LOAD-HI-ORGANIC | SDGE | 3.977 | 1.099 |
| LOAD-HI-ORGANIC | SP15_rest | 3.372 | 0.296 |
| LOAD-HI-ORGANIC | ZP26 | 5.780 | 0.707 |

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
| LOAD-HI | retrofit | gas_cc_ccs | 8936.3 | 249.3 |
| LOAD-HI-ORGANIC | build | gas_cc | 2000.0 | 0.0 |
| LOAD-HI-ORGANIC | build | gas_ct | 17049.6 | 6888.0 |
| LOAD-HI-ORGANIC | build | solar | 4000.0 | 0.0 |
| LOAD-HI-ORGANIC | build | wind | 1404.4 | 0.0 |
| LOAD-HI-ORGANIC | retirement | biomass | 2.3 | 0.0 |
| LOAD-HI-ORGANIC | retirement | gas_ct | 5.2 | 0.0 |
| LOAD-HI-ORGANIC | retirement | gas_st | 1525.8 | 0.0 |
| LOAD-HI-ORGANIC | retirement | nuclear | 1122.0 | 0.0 |
| LOAD-HI-ORGANIC | retrofit | gas_cc_ccs | 8936.3 | 249.3 |
| REF | build | gas_cc | 2000.0 | 0.0 |
| REF | build | gas_ct | 10161.6 | 0.0 |
| REF | build | solar | 4000.0 | 0.0 |
| REF | build | wind | 1404.4 | 0.0 |
| REF | retirement | biomass | 2.3 | 0.0 |
| REF | retirement | gas_ct | 5.2 | 0.0 |
| REF | retirement | gas_st | 1525.8 | 0.0 |
| REF | retirement | nuclear | 1122.0 | 0.0 |
| REF | retrofit | gas_cc_ccs | 8687.0 | 0.0 |

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
