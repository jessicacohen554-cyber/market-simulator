# Scenario delta report — MISO — miso_scenario_campaign_matrix_982d651e2b

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`CES-P20+VOL-HI` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| ALL-CLEAN | `00edacf5f50c88fc` |  |
| CES-P20+VOL-HI | `ed42e5d7d1d95d3e` | **REF** |

## Headline deltas vs `CES-P20+VOL-HI` (final cached year)

Final cached year on disk: **2030**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| ALL-CLEAN | 455.858 | 66.109 | 0.000 | 42379462.680 | 16098.800 | 0.000 | 997.860 | 816.130 | 0.000 | 0.298 |
| CES-P20+VOL-HI | 389.750 | 0.000 | 0.000 | 2824183.485 | 16098.800 | 0.000 | 181.730 | 0.000 | 0.000 | 0.327 |

## Cumulative CO2 delta vs `CES-P20+VOL-HI` (Mt)

Running sum of the per-year CO2 delta, through **2030**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| ALL-CLEAN | 2030 | 224.233 |
| CES-P20+VOL-HI | 2030 | 0.000 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| ALL-CLEAN | biomass | 0.000 | 0.072 | 0.033 |
| ALL-CLEAN | coal | 0.000 | -0.695 | -0.863 |
| ALL-CLEAN | gas_cc | -0.001 | 19.287 | 5.606 |
| ALL-CLEAN | gas_cc_ccs | 0.001 | 0.011 | 0.232 |
| ALL-CLEAN | gas_ct | 0.000 | 53.452 | 36.339 |
| ALL-CLEAN | gas_st | 0.000 | 20.024 | 12.244 |
| ALL-CLEAN | nuclear | 1.000 | 7.830 | 0.000 |
| ALL-CLEAN | oil | 0.000 | 12.556 | 12.518 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| ALL-CLEAN | MISO-East | 102.033 | 22.054 |
| ALL-CLEAN | MISO-Illinois | 35.854 | 0.748 |
| ALL-CLEAN | MISO-Indiana | 86.250 | 8.551 |
| ALL-CLEAN | MISO-Plains | 70.649 | 9.148 |
| ALL-CLEAN | MISO-South | 109.228 | 16.799 |
| ALL-CLEAN | MISO-West | 51.843 | 8.809 |

## Capacity-evolution deltas vs `CES-P20+VOL-HI` (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| ALL-CLEAN | build | gas_cc | 3722.0 | 0.0 |
| ALL-CLEAN | build | gas_ct | 18129.6 | 0.0 |
| ALL-CLEAN | build | iron_air | 9600.0 | 0.0 |
| ALL-CLEAN | build | li_ion_4hr | 6400.0 | 0.0 |
| ALL-CLEAN | build | nuclear | 1000.0 | 1000.0 |
| ALL-CLEAN | build | oil | 17.0 | 0.0 |
| ALL-CLEAN | build | solar | 6000.0 | 0.0 |
| ALL-CLEAN | build | wind | 4000.0 | 0.0 |
| ALL-CLEAN | retirement | biomass | 16.0 | 0.0 |
| ALL-CLEAN | retirement | coal | 7794.9 | 0.0 |
| ALL-CLEAN | retirement | gas_ct | 716.8 | 0.0 |
| ALL-CLEAN | retirement | gas_st | 1855.8 | 0.0 |
| ALL-CLEAN | retirement | nuclear | 617.0 | 0.0 |
| ALL-CLEAN | retirement | oil | 119.0 | 0.0 |
| ALL-CLEAN | retrofit | gas_cc_ccs | 8998.0 | 1.4 |
| CES-P20+VOL-HI | build | gas_cc | 3722.0 | 0.0 |
| CES-P20+VOL-HI | build | gas_ct | 18129.6 | 0.0 |
| CES-P20+VOL-HI | build | iron_air | 9600.0 | 0.0 |
| CES-P20+VOL-HI | build | li_ion_4hr | 6400.0 | 0.0 |
| CES-P20+VOL-HI | build | oil | 17.0 | 0.0 |
| CES-P20+VOL-HI | build | solar | 6000.0 | 0.0 |
| CES-P20+VOL-HI | build | wind | 4000.0 | 0.0 |
| CES-P20+VOL-HI | retirement | biomass | 16.0 | 0.0 |
| CES-P20+VOL-HI | retirement | coal | 7794.9 | 0.0 |
| CES-P20+VOL-HI | retirement | gas_ct | 716.8 | 0.0 |
| CES-P20+VOL-HI | retirement | gas_st | 1855.8 | 0.0 |
| CES-P20+VOL-HI | retirement | nuclear | 617.0 | 0.0 |
| CES-P20+VOL-HI | retirement | oil | 119.0 | 0.0 |
| CES-P20+VOL-HI | retrofit | gas_cc_ccs | 8996.6 | 0.0 |

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
- Case `ALL-CLEAN` 2028: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `ALL-CLEAN` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `ALL-CLEAN` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029`, `gas_ct_adequacy_2030` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CES-P20+VOL-HI` 2028: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CES-P20+VOL-HI` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `CES-P20+VOL-HI` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029`, `gas_ct_adequacy_2030` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- No --financial-reports-root given — captured prices cover the wind/solar pools only.
