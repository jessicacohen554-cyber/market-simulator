# Scenario delta report — MISO — scn-ws4-probe-miso

**SCN-WS4c LOAD-HI probe (campaign scn-ws4-probe)** — deltas are
case-vs-`REF` differences on one deterministic case set,
not a probability statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Reference? |
|---|---|---|
| REF | `8e72c2256983f981` | **REF** |
| LOAD-HI | `759ccceb7923b1fe` |  |
| LOAD-HI-ORGANIC | `abe5759c41a76e7b` |  |

## Headline deltas vs `REF` (final cached year)

Final cached year on disk: **2026**.

| case | emissions_mt | emissions_mt_delta | import_co2_mt_reported | unserved_mwh | backstop_built_mw | backstop_built_mwh | avg_price_usd_per_mwh | avg_price_usd_per_mwh_delta | curtailment_twh | clean_share |
|---|---|---|---|---|---|---|---|---|---|---|
| REF | 353.037 | 0.000 | 0.000 | 48093.807 | 0 | 0.000 | 37.870 | 0.000 | 0.000 | 0.296 |
| LOAD-HI | 362.029 | 8.992 | 0.000 | 77034.471 | 0 | 0.000 | 39.970 | 2.100 | 0.000 | 0.288 |
| LOAD-HI-ORGANIC | 362.038 | 9.001 | 0.000 | 77976.319 | 0 | 0.000 | 40.130 | 2.260 | 0.000 | 0.288 |

## Cumulative CO2 delta vs `REF` (Mt)

Running sum of the per-year CO2 delta, through **2026**.

| case | year | cumulative_emissions_mt_delta |
|---|---|---|
| LOAD-HI | 2026 | 8.992 |
| LOAD-HI-ORGANIC | 2026 | 9.001 |
| REF | 2026 | 0.000 |

## By-fuel deltas (final year)

| case | fuel | capacity_gw_delta | generation_twh_delta | emissions_mt_delta |
|---|---|---|---|---|
| LOAD-HI | biomass | 0.000 | 0.171 | 0.021 |
| LOAD-HI | coal | 0.000 | 1.201 | 1.265 |
| LOAD-HI | gas_cc | 0.000 | 13.546 | 5.598 |
| LOAD-HI | gas_ct | 0.000 | 2.716 | 1.532 |
| LOAD-HI | gas_st | 0.000 | 1.103 | 0.558 |
| LOAD-HI | oil | 0.000 | 0.018 | 0.018 |
| LOAD-HI-ORGANIC | biomass | 0.000 | 0.171 | 0.021 |
| LOAD-HI-ORGANIC | coal | 0.000 | 1.201 | 1.264 |
| LOAD-HI-ORGANIC | gas_cc | 0.000 | 13.511 | 5.588 |
| LOAD-HI-ORGANIC | gas_ct | 0.000 | 2.735 | 1.544 |
| LOAD-HI-ORGANIC | gas_st | 0.000 | 1.118 | 0.567 |
| LOAD-HI-ORGANIC | oil | 0.000 | 0.018 | 0.018 |

## By-zone CO2 deltas (final year, Mt)

| case | zone | emissions_mt | emissions_mt_delta |
|---|---|---|---|
| LOAD-HI | MISO-East | 90.599 | 2.181 |
| LOAD-HI | MISO-Illinois | 29.821 | 0.569 |
| LOAD-HI | MISO-Indiana | 64.286 | 1.916 |
| LOAD-HI | MISO-Plains | 58.079 | 0.566 |
| LOAD-HI | MISO-South | 78.834 | 2.985 |
| LOAD-HI | MISO-West | 40.409 | 0.775 |
| LOAD-HI-ORGANIC | MISO-East | 90.597 | 2.179 |
| LOAD-HI-ORGANIC | MISO-Illinois | 29.823 | 0.570 |
| LOAD-HI-ORGANIC | MISO-Indiana | 64.283 | 1.913 |
| LOAD-HI-ORGANIC | MISO-Plains | 58.075 | 0.562 |
| LOAD-HI-ORGANIC | MISO-South | 78.856 | 3.006 |
| LOAD-HI-ORGANIC | MISO-West | 40.405 | 0.771 |

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
