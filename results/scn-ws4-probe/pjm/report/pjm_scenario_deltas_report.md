# Scenario delta report — PJM — scn-ws4-probe-pjm

**SCN-WS4c LOAD-HI probe (campaign scn-ws4-probe)** — deltas are
case-vs-`REF` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| REF | `058444cfe884b79b` | **REF** |
| LOAD-HI | `7370b703046ef374` |  |

## Headline deltas vs `REF` (final cached year)

Final cached year on disk: **2026**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| REF | 349.092 | 0.000 | 0.417 | 0.000 | 0 | 0.000 | 39.410 | 0.000 | 0.000 | 0.389 |
| LOAD-HI | 369.175 | 20.084 | 0.756 | 0.000 | 0 | 0.000 | 40.770 | 1.360 | 0.000 | 0.371 |

## Cumulative CO2 delta vs `REF` (Mt)

Running sum of the per-year CO2 delta, through **2026**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| LOAD-HI | 2026 | 20.084 |
| REF | 2026 | 0.000 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| LOAD-HI | biomass | 0.000 | 0.369 | 0.000 |
| LOAD-HI | coal | 0.000 | 5.456 | 5.864 |
| LOAD-HI | gas_cc | 0.000 | 29.634 | 11.712 |
| LOAD-HI | gas_ct | 0.000 | 3.855 | 2.174 |
| LOAD-HI | gas_st | 0.000 | 0.593 | 0.333 |
| LOAD-HI | import | 0.000 | 1.163 | 0.000 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| LOAD-HI | PJM_AEP_Ohio | 135.206 | 5.451 |
| LOAD-HI | PJM_ATSI | 9.156 | 0.820 |
| LOAD-HI | PJM_Central_PA | 31.071 | 2.750 |
| LOAD-HI | PJM_ComEd | 30.301 | 2.252 |
| LOAD-HI | PJM_Dominion | 28.599 | 2.401 |
| LOAD-HI | PJM_EMAAC | 23.213 | 2.655 |
| LOAD-HI | PJM_SWMAAC | 15.451 | 0.971 |
| LOAD-HI | PJM_West_APS | 96.178 | 2.782 |

## Capacity-evolution deltas vs `REF` (ledger totals, MW)

_No evolution ledgers found (backcast or fixture cache)._

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
- No --financial-reports-root given — captured prices cover the wind/solar pools only.
