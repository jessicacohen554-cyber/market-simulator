# Scenario delta report — PJM — pjm_scenario_campaign_matrix_3eee8f1195

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`REF` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| LOAD-HI | `d1da885b4fdc4e6b` |  |
| REF | `67a786980ac38749` | **REF** |

## Headline deltas vs `REF` (final cached year)

Final cached year on disk: **2030**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| LOAD-HI | 608.471 | 145.431 | 14.948 | 63687856.088 | 8956.400 | 0.000 | 891.740 | 824.710 | 0.000 | 0.263 |
| REF | 463.039 | 0.000 | 5.866 | 77827.937 | 8956.400 | 0.000 | 67.030 | 0.000 | 0.000 | 0.310 |

## Cumulative CO2 delta vs `REF` (Mt)

Running sum of the per-year CO2 delta, through **2030**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| LOAD-HI | 2030 | 468.681 |
| REF | 2030 | 0.000 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| LOAD-HI | biomass | 0.000 | 1.012 | 0.000 |
| LOAD-HI | coal | 0.000 | 0.255 | 0.447 |
| LOAD-HI | gas_cc | -0.459 | 16.594 | 7.750 |
| LOAD-HI | gas_cc_ccs | 0.459 | 5.996 | 0.345 |
| LOAD-HI | gas_ct | 0.000 | 152.601 | 95.313 |
| LOAD-HI | gas_st | 0.000 | 40.981 | 25.593 |
| LOAD-HI | import | 0.000 | 21.218 | 0.000 |
| LOAD-HI | nuclear | 1.000 | 8.278 | 0.000 |
| LOAD-HI | oil | 0.000 | 16.359 | 15.984 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| LOAD-HI | PJM_AEP_Ohio | 225.356 | 42.474 |
| LOAD-HI | PJM_ATSI | 18.784 | 8.535 |
| LOAD-HI | PJM_Central_PA | 59.024 | 18.566 |
| LOAD-HI | PJM_ComEd | 54.841 | 21.170 |
| LOAD-HI | PJM_Dominion | 62.938 | 14.215 |
| LOAD-HI | PJM_EMAAC | 54.284 | 19.126 |
| LOAD-HI | PJM_SWMAAC | 23.746 | 13.198 |
| LOAD-HI | PJM_West_APS | 109.499 | 8.146 |

## Capacity-evolution deltas vs `REF` (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| LOAD-HI | build | gas_cc | 4000.0 | 0.0 |
| LOAD-HI | build | gas_ct | 10642.0 | 842.8 |
| LOAD-HI | build | iron_air | 9600.0 | 0.0 |
| LOAD-HI | build | li_ion_4hr | 6400.0 | 3200.0 |
| LOAD-HI | build | nuclear | 1000.0 | 1000.0 |
| LOAD-HI | build | solar | 6000.0 | 0.0 |
| LOAD-HI | build | wind | 1500.0 | 0.0 |
| LOAD-HI | retirement | coal | 4242.4 | 0.0 |
| LOAD-HI | retirement | gas_ct | 86.9 | 0.0 |
| LOAD-HI | retirement | gas_st | 460.0 | 0.0 |
| LOAD-HI | retirement | oil | 702.0 | 0.0 |
| LOAD-HI | retrofit | gas_cc_ccs | 2707.7 | 459.0 |
| REF | build | gas_cc | 4000.0 | 0.0 |
| REF | build | gas_ct | 10642.0 | 0.0 |
| REF | build | iron_air | 9600.0 | 0.0 |
| REF | build | li_ion_4hr | 3200.0 | 0.0 |
| REF | build | solar | 6000.0 | 0.0 |
| REF | build | wind | 1500.0 | 0.0 |
| REF | retirement | coal | 4242.4 | 0.0 |
| REF | retirement | gas_ct | 86.9 | 0.0 |
| REF | retirement | gas_st | 460.0 | 0.0 |
| REF | retirement | oil | 702.0 | 0.0 |
| REF | retrofit | gas_cc_ccs | 2248.7 | 0.0 |

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
- Case `LOAD-HI` 2028: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `LOAD-HI` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `LOAD-HI` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029`, `gas_ct_adequacy_2030` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `REF` 2027: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `REF` 2028: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `REF` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027`, `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `REF` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2027`, `gas_ct_adequacy_2029`, `gas_ct_adequacy_2030` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- No --financial-reports-root given — captured prices cover the wind/solar pools only.
