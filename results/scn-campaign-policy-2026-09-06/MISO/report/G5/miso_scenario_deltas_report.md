# Scenario delta report — MISO — miso_scenario_campaign_matrix_982d651e2b

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-`VOL-MID` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| VOL-HI | `7e1a2a2145711bab` |  |
| VOL-MID | `dc8ca3580e277d72` | **REF** |

## Headline deltas vs `VOL-MID` (final cached year)

Final cached year on disk: **2030**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| VOL-HI | 410.199 | -0.000 | 0.000 | 2824183.485 | 16098.800 | 0.000 | 181.740 | 0.000 | 0.000 | 0.255 |
| VOL-MID | 410.199 | 0.000 | 0.000 | 2824183.485 | 16098.800 | 0.000 | 181.740 | 0.000 | 0.000 | 0.255 |

## Cumulative CO2 delta vs `VOL-MID` (Mt)

Running sum of the per-year CO2 delta, through **2030**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| VOL-HI | 2030 | -0.000 |
| VOL-MID | 2030 | 0.000 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| VOL-HI | gas_ct | 0.000 | 0.000 | -0.000 |
| VOL-HI | gas_st | 0.000 | 0.000 | 0.000 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| VOL-HI | MISO-East | 83.256 | -0.000 |
| VOL-HI | MISO-Plains | 59.636 | 0.000 |
| VOL-HI | MISO-South | 101.748 | -0.000 |
| VOL-HI | MISO-West | 43.639 | 0.000 |

## Capacity-evolution deltas vs `VOL-MID` (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| VOL-HI | build | gas_cc | 3722.0 | 0.0 |
| VOL-HI | build | gas_ct | 18129.6 | 0.0 |
| VOL-HI | build | iron_air | 9600.0 | 0.0 |
| VOL-HI | build | li_ion_4hr | 6400.0 | 0.0 |
| VOL-HI | build | oil | 17.0 | 0.0 |
| VOL-HI | build | solar | 6000.0 | 0.0 |
| VOL-HI | build | wind | 4000.0 | 0.0 |
| VOL-HI | retirement | biomass | 16.0 | 0.0 |
| VOL-HI | retirement | coal | 7794.9 | 0.0 |
| VOL-HI | retirement | gas_ct | 716.8 | 0.0 |
| VOL-HI | retirement | gas_st | 1855.8 | 0.0 |
| VOL-HI | retirement | nuclear | 617.0 | 0.0 |
| VOL-HI | retirement | oil | 119.0 | 0.0 |
| VOL-HI | retrofit | gas_cc_ccs | 618.1 | 0.0 |
| VOL-MID | build | gas_cc | 3722.0 | 0.0 |
| VOL-MID | build | gas_ct | 18129.6 | 0.0 |
| VOL-MID | build | iron_air | 9600.0 | 0.0 |
| VOL-MID | build | li_ion_4hr | 6400.0 | 0.0 |
| VOL-MID | build | oil | 17.0 | 0.0 |
| VOL-MID | build | solar | 6000.0 | 0.0 |
| VOL-MID | build | wind | 4000.0 | 0.0 |
| VOL-MID | retirement | biomass | 16.0 | 0.0 |
| VOL-MID | retirement | coal | 7794.9 | 0.0 |
| VOL-MID | retirement | gas_ct | 716.8 | 0.0 |
| VOL-MID | retirement | gas_st | 1855.8 | 0.0 |
| VOL-MID | retirement | nuclear | 617.0 | 0.0 |
| VOL-MID | retirement | oil | 119.0 | 0.0 |
| VOL-MID | retrofit | gas_cc_ccs | 618.1 | 0.0 |

## Notes & definitions

- Every delta is `case − VOL-MID` on the same year.
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
- Case `VOL-HI` 2028: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `VOL-HI` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `VOL-HI` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029`, `gas_ct_adequacy_2030` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `VOL-MID` 2028: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `VOL-MID` 2029: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- Case `VOL-MID` 2030: ledger names reserve-backstop unit(s) `gas_ct_adequacy_2028`, `gas_ct_adequacy_2029`, `gas_ct_adequacy_2030` absent from the cached fleet — `backstop_built_mwh` excludes them (MW still counted from the ledger).
- No --financial-reports-root given — captured prices cover the wind/solar pools only.
