# Scenario delta report — NYISO — scn-ws4-probe-nyiso

**SCN-WS4c LOAD-HI probe (campaign scn-ws4-probe)** — deltas are
case-vs-`REF` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| REF | `7c0ad83004421a23` | **REF** |
| LOAD-HI | `3f2d67121a98bcd9` |  |
| LOAD-HI-ORGANIC | `97f765a39320f765` |  |

## Headline deltas vs `REF` (final cached year)

Final cached year on disk: **2026**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| REF | 23.736 | 0.000 | 10.461 | 0.000 | 0 | 0.000 | 49.260 | 0.000 | 0.000 | 0.392 |
| LOAD-HI | 25.373 | 1.637 | 10.617 | 0.000 | 0 | 0.000 | 50.320 | 1.060 | 0.000 | 0.382 |
| LOAD-HI-ORGANIC | 25.463 | 1.727 | 10.589 | 0.000 | 0 | 0.000 | 50.550 | 1.290 | 0.000 | 0.382 |

## Cumulative CO2 delta vs `REF` (Mt)

Running sum of the per-year CO2 delta, through **2026**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| LOAD-HI | 2026 | 1.637 |
| LOAD-HI-ORGANIC | 2026 | 1.727 |
| REF | 2026 | 0.000 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| LOAD-HI | biomass | 0.000 | 0.069 | 0.000 |
| LOAD-HI | gas_cc | 0.000 | 3.479 | 1.411 |
| LOAD-HI | gas_ct | 0.000 | 0.137 | 0.092 |
| LOAD-HI | gas_st | 0.000 | 0.266 | 0.134 |
| LOAD-HI | import | 0.000 | 0.365 | 0.000 |
| LOAD-HI-ORGANIC | biomass | 0.000 | 0.107 | 0.000 |
| LOAD-HI-ORGANIC | gas_cc | 0.000 | 3.114 | 1.284 |
| LOAD-HI-ORGANIC | gas_ct | 0.000 | 0.234 | 0.147 |
| LOAD-HI-ORGANIC | gas_st | 0.000 | 0.566 | 0.296 |
| LOAD-HI-ORGANIC | import | 0.000 | 0.300 | 0.000 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| LOAD-HI | Capital_Hudson | 10.149 | 0.890 |
| LOAD-HI | Long_Island | 1.389 | 0.046 |
| LOAD-HI | Lower_Hudson | 0.002 | 0.001 |
| LOAD-HI | NYC | 10.046 | 0.582 |
| LOAD-HI | Upstate_West | 3.788 | 0.119 |
| LOAD-HI-ORGANIC | Capital_Hudson | 10.037 | 0.779 |
| LOAD-HI-ORGANIC | Long_Island | 1.460 | 0.118 |
| LOAD-HI-ORGANIC | Lower_Hudson | 0.002 | 0.001 |
| LOAD-HI-ORGANIC | NYC | 10.162 | 0.698 |
| LOAD-HI-ORGANIC | Upstate_West | 3.801 | 0.132 |

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
