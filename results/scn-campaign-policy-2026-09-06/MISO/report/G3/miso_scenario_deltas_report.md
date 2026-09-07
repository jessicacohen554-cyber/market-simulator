# Scenario delta report — MISO — miso_scenario_campaign_matrix_982d651e2b

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`CES-P10` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| CES-P10 | `e4ba286178e0d499` | **REF** |
| CES-P20 | `472af7fd5ba90f99` |  |

## Headline deltas vs `CES-P10` (final cached year)

Final cached year on disk: **2030**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| CES-P10 | 389.771 | 0.000 | 0.000 | 2824183.485 | 16098.800 | 0.000 | 181.730 | 0.000 | 0.000 | 0.326 |
| CES-P20 | 389.751 | -0.020 | 0.000 | 2824183.485 | 16098.800 | 0.000 | 181.730 | 0.000 | 0.000 | 0.327 |

## Cumulative CO2 delta vs `CES-P10` (Mt)

Running sum of the per-year CO2 delta, through **2030**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| CES-P10 | 2030 | 0.000 |
| CES-P20 | 2030 | -0.148 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| CES-P20 | biomass | 0.000 | 0.000 | -0.000 |
| CES-P20 | gas_cc | -0.001 | -0.246 | -0.018 |
| CES-P20 | gas_cc_ccs | 0.001 | 0.254 | 0.002 |
| CES-P20 | gas_ct | 0.000 | -0.001 | -0.001 |
| CES-P20 | gas_st | 0.000 | -0.008 | -0.004 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| CES-P20 | MISO-East | 79.973 | -0.032 |
| CES-P20 | MISO-Illinois | 35.113 | -0.003 |
| CES-P20 | MISO-Indiana | 77.699 | -0.001 |
| CES-P20 | MISO-Plains | 61.502 | -0.001 |
| CES-P20 | MISO-South | 92.429 | 0.016 |
| CES-P20 | MISO-West | 43.035 | -0.000 |

## Capacity-evolution deltas vs `CES-P10` (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| CES-P10 | build | gas_cc | 3722.0 | 0.0 |
| CES-P10 | build | gas_ct | 18129.6 | 0.0 |
| CES-P10 | build | iron_air | 9600.0 | 0.0 |
| CES-P10 | build | li_ion_4hr | 6400.0 | 0.0 |
| CES-P10 | build | oil | 17.0 | 0.0 |
| CES-P10 | build | solar | 6000.0 | 0.0 |
| CES-P10 | build | wind | 4000.0 | 0.0 |
| CES-P10 | retirement | biomass | 16.0 | 0.0 |
| CES-P10 | retirement | coal | 7794.9 | 0.0 |
| CES-P10 | retirement | gas_ct | 716.8 | 0.0 |
| CES-P10 | retirement | gas_st | 1855.8 | 0.0 |
| CES-P10 | retirement | nuclear | 617.0 | 0.0 |
| CES-P10 | retirement | oil | 119.0 | 0.0 |
| CES-P10 | retrofit | gas_cc_ccs | 8996.5 | 0.0 |
| CES-P20 | build | gas_cc | 3722.0 | 0.0 |
| CES-P20 | build | gas_ct | 18129.6 | 0.0 |
| CES-P20 | build | iron_air | 9600.0 | 0.0 |
| CES-P20 | build | li_ion_4hr | 6400.0 | 0.0 |
| CES-P20 | build | oil | 17.0 | 0.0 |
| CES-P20 | build | solar | 6000.0 | 0.0 |
| CES-P20 | build | wind | 4000.0 | 0.0 |
| CES-P20 | retirement | biomass | 16.0 | 0.0 |
| CES-P20 | retirement | coal | 7794.9 | 0.0 |
| CES-P20 | retirement | gas_ct | 716.8 | 0.0 |
| CES-P20 | retirement | gas_st | 1855.8 | 0.0 |
| CES-P20 | retirement | nuclear | 617.0 | 0.0 |
| CES-P20 | retirement | oil | 119.0 | 0.0 |
| CES-P20 | retrofit | gas_cc_ccs | 8996.6 | 0.1 |

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
- Case `CES-P10` 2028: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CES-P10` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CES-P10` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029`, `gas_ct_adequacy_2030` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CES-P20` 2028: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CES-P20` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CES-P20` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029`, `gas_ct_adequacy_2030` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- No --financial-reports-root given — captured prices cover the wind/solar pools only.
