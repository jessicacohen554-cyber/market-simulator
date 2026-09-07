# Scenario delta report — MISO — miso_scenario_campaign_matrix_982d651e2b

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`CES-P30` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| CES-P30 | `3a4b528c75d7fd6d` | **REF** |
| CES-T80 | `82c916d847270ebf` |  |

## Headline deltas vs `CES-P30` (final cached year)

Final cached year on disk: **2030**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| CES-P30 | 389.736 | 0.000 | 0.000 | 2823143.007 | 16098.800 | 0.000 | 181.800 | 0.000 | 0.000 | 0.327 |
| CES-T80 | 406.176 | 16.441 | 0.000 | 2823143.007 | 16098.800 | 0.000 | 181.790 | -0.010 | 0.000 | 0.263 |

## Cumulative CO2 delta vs `CES-P30` (Mt)

Running sum of the per-year CO2 delta, through **2030**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| CES-P30 | 2030 | 0.000 |
| CES-T80 | 2030 | 34.526 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| CES-T80 | biomass | 0.000 | -0.001 | -0.001 |
| CES-T80 | coal | 0.000 | -0.000 | -0.000 |
| CES-T80 | gas_cc | 8.376 | 67.395 | 22.667 |
| CES-T80 | gas_cc_ccs | -8.376 | -67.470 | -2.269 |
| CES-T80 | gas_ct | 0.000 | -7.760 | -3.959 |
| CES-T80 | gas_st | 0.000 | 0.008 | 0.004 |
| CES-T80 | nuclear | 1.000 | 7.830 | 0.000 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| CES-T80 | MISO-East | 83.252 | 3.005 |
| CES-T80 | MISO-Illinois | 39.270 | 4.163 |
| CES-T80 | MISO-Indiana | 78.709 | 1.396 |
| CES-T80 | MISO-Plains | 59.640 | -1.867 |
| CES-T80 | MISO-South | 101.747 | 9.147 |
| CES-T80 | MISO-West | 43.559 | 0.597 |

## Capacity-evolution deltas vs `CES-P30` (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| CES-P30 | build | gas_cc | 3722.0 | 0.0 |
| CES-P30 | build | gas_ct | 18129.6 | 0.0 |
| CES-P30 | build | iron_air | 9600.0 | 0.0 |
| CES-P30 | build | li_ion_4hr | 6400.0 | 0.0 |
| CES-P30 | build | oil | 17.0 | 0.0 |
| CES-P30 | build | solar | 6000.0 | 0.0 |
| CES-P30 | build | wind | 4000.0 | 0.0 |
| CES-P30 | retirement | biomass | 16.0 | 0.0 |
| CES-P30 | retirement | coal | 7794.9 | 0.0 |
| CES-P30 | retirement | gas_ct | 716.8 | 0.0 |
| CES-P30 | retirement | gas_st | 1855.8 | 0.0 |
| CES-P30 | retirement | nuclear | 617.0 | 0.0 |
| CES-P30 | retirement | oil | 119.0 | 0.0 |
| CES-P30 | retrofit | gas_cc_ccs | 8994.4 | 0.0 |
| CES-T80 | build | gas_cc | 3722.0 | 0.0 |
| CES-T80 | build | gas_ct | 18129.6 | 0.0 |
| CES-T80 | build | iron_air | 9600.0 | 0.0 |
| CES-T80 | build | li_ion_4hr | 6400.0 | 0.0 |
| CES-T80 | build | nuclear | 1000.0 | 1000.0 |
| CES-T80 | build | oil | 17.0 | 0.0 |
| CES-T80 | build | solar | 6000.0 | 0.0 |
| CES-T80 | build | wind | 4000.0 | 0.0 |
| CES-T80 | retirement | biomass | 16.0 | 0.0 |
| CES-T80 | retirement | coal | 7794.9 | 0.0 |
| CES-T80 | retirement | gas_ct | 716.8 | 0.0 |
| CES-T80 | retirement | gas_st | 1855.8 | 0.0 |
| CES-T80 | retirement | nuclear | 617.0 | 0.0 |
| CES-T80 | retirement | oil | 119.0 | 0.0 |
| CES-T80 | retrofit | gas_cc_ccs | 618.1 | -5376.3 |

## Notes & definitions

- Every delta is `case − CES-P30` on the same year.
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
- Case `CES-P30` 2028: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CES-P30` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CES-P30` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029`, `gas_ct_adequacy_2030` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CES-T80` 2028: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CES-T80` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CES-T80` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029`, `gas_ct_adequacy_2030` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- No --financial-reports-root given — captured prices cover the wind/solar pools only.
