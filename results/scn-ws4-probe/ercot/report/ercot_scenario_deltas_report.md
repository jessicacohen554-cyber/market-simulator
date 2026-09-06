# Scenario delta report — ERCOT — scn-ws4-probe-ercot

**SCN-WS4c LOAD-HI probe (campaign scn-ws4-probe)** — deltas are
case-vs-`REF` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| REF | `8e01cd28ea757f1a` | **REF** |
| LOAD-HI | `7172ac611ebbf67c` |  |
| LOAD-HI-ORGANIC | `e4a9e2dbb5ee5528` |  |

## Headline deltas vs `REF` (final cached year)

Final cached year on disk: **2026**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| REF | 189.167 | 0.000 | 0.000 | 0.000 | 0 | 0.000 | 30.570 | 0.000 | 4.334 | 0.432 |
| LOAD-HI | 202.854 | 13.687 | 0.000 | 0.000 | 0 | 0.000 | 32.330 | 1.760 | 4.334 | 0.409 |
| LOAD-HI-ORGANIC | 203.940 | 14.774 | 0.000 | 143390.925 | 0 | 0.000 | 64.680 | 34.110 | 4.334 | 0.409 |

## Cumulative CO2 delta vs `REF` (Mt)

Running sum of the per-year CO2 delta, through **2026**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| LOAD-HI | 2026 | 13.687 |
| LOAD-HI-ORGANIC | 2026 | 14.774 |
| REF | 2026 | 0.000 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| LOAD-HI | coal | 0.000 | 0.034 | 0.034 |
| LOAD-HI | gas_cc | 0.000 | 23.907 | 10.036 |
| LOAD-HI | gas_ct | 0.000 | 4.717 | 2.440 |
| LOAD-HI | gas_st | 0.000 | 1.975 | 1.178 |
| LOAD-HI | solar | 0.000 | 0.000 | 0.000 |
| LOAD-HI-ORGANIC | coal | 0.000 | 0.122 | 0.128 |
| LOAD-HI-ORGANIC | gas_cc | 0.000 | 18.515 | 7.974 |
| LOAD-HI-ORGANIC | gas_ct | 0.000 | 6.184 | 3.303 |
| LOAD-HI-ORGANIC | gas_st | 0.000 | 5.539 | 3.368 |
| LOAD-HI-ORGANIC | solar | 0.000 | 0.000 | 0.000 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| LOAD-HI | Houston | 36.338 | 2.580 |
| LOAD-HI | North | 72.187 | 5.286 |
| LOAD-HI | Northeast | 18.683 | 0.218 |
| LOAD-HI | South | 19.070 | 1.689 |
| LOAD-HI | South_Central | 51.672 | 3.183 |
| LOAD-HI | West | 4.903 | 0.732 |
| LOAD-HI-ORGANIC | Houston | 37.538 | 3.780 |
| LOAD-HI-ORGANIC | North | 71.643 | 4.741 |
| LOAD-HI-ORGANIC | Northeast | 19.042 | 0.577 |
| LOAD-HI-ORGANIC | South | 19.062 | 1.681 |
| LOAD-HI-ORGANIC | South_Central | 51.646 | 3.156 |
| LOAD-HI-ORGANIC | West | 5.010 | 0.839 |

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
