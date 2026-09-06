# CES premium-ladder campaign report — ERCOT — ercot_ces_premium_matrix_poc_63d7e388c9

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-BAU differences on one deterministic ladder, not a probability
statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Crediting | Premium @2026 ($/MWh) |
|---|---|---|---|
| BAU | `d88c8585e76f2935` | (CES off) | 0.00 |
| CES-20 | `075e6aa30813f061` | clean_capture | 20.00 |
| CES-40 | `383509581661faba` | clean_capture | 40.00 |

## Clean-share vs premium

Final cached year on disk: **2030**.

| case | premium_usd_per_mwh | clean_share | negative_price_hours | avg_price_usd_per_mwh |
|---|---|---|---|---|
| BAU | 0.000 | 0.321 | 0.000 | 2098.990 |
| CES-20 | 20.000 | 0.475 | 843.710 | 1409.260 |
| CES-40 | 40.000 | 0.476 | 874.430 | 1407.180 |

## Capacity deltas vs BAU (final year, GW)

| case | fuel | capacity_gw | capacity_gw_bau | capacity_gw_delta |
|---|---|---|---|---|
| CES-20 | gas_cc | 30.303 | 41.260 | -10.957 |
| CES-20 | solar | 52.000 | 38.100 | 13.900 |
| CES-20 | wind | 52.000 | 42.553 | 9.447 |
| CES-40 | gas_cc | 30.304 | 41.260 | -10.956 |
| CES-40 | solar | 52.000 | 38.100 | 13.900 |
| CES-40 | wind | 52.000 | 42.553 | 9.447 |

## Capacity-evolution deltas vs BAU (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| BAU | build | gas_cc | 4018.8 | 0.0 |
| BAU | build | gas_ct | 1291.0 | 0.0 |
| BAU | build | solar | 100.0 | 0.0 |
| BAU | build | wind | 553.1 | 0.0 |
| BAU | retirement | gas_st | 446.0 | 0.0 |
| CES-20 | build | gas_cc | 2018.8 | 0.0 |
| CES-20 | build | gas_ct | 1291.0 | 0.0 |
| CES-20 | build | solar | 14000.0 | 13900.0 |
| CES-20 | build | wind | 10000.0 | 9446.9 |
| CES-20 | retirement | gas_st | 446.0 | 0.0 |
| CES-20 | retrofit | gas_cc_ccs | 8957.3 | 8957.3 |
| CES-40 | build | gas_cc | 2018.8 | 0.0 |
| CES-40 | build | gas_ct | 1291.0 | 0.0 |
| CES-40 | build | solar | 14000.0 | 13900.0 |
| CES-40 | build | wind | 10000.0 | 9446.9 |
| CES-40 | retirement | gas_st | 446.0 | 0.0 |
| CES-40 | retrofit | gas_cc_ccs | 8955.7 | 8955.7 |

## Premium capture (credited delivered / potential MWh)

| case | premium_usd_per_mwh | credited_delivered_mwh | credited_potential_mwh | premium_capture_rate |
|---|---|---|---|---|
| BAU | 0.000 | 237252369.839 | 251805561.470 | 0.942 |
| CES-20 | 20.000 | 356048426.757 | 386736271.902 | 0.921 |
| CES-40 | 40.000 | 356462415.930 | 386722831.872 | 0.922 |

## Largest company revenue deltas vs BAU

_No financial report parquets found — run `scripts/generate_financial_reports.py` per case first._

## Notes & definitions

- `clean_share` = credit-weighted generation / total generation, using
  each case's own crediting RULE (reporting-side, ungated by
  `federal_ces_enabled`) so the BAU anchor is the real physical clean
  share. Storage discharge is excluded from both sides (owner D5).
- `negative_price_hours` is the zone-averaged count of hours clearing
  below $0/MWh (total negative zone-hours / zone count).
- `premium_capture_rate` prices credited potential at nameplate energy
  for thermal units (per-unit availability is not persisted in the
  cached context) and CF-weighted available energy for wind/solar, so
  it blends economic dispatch depth with curtailment erosion.
- `attribute_revenue` is the certificate line only (max of legacy
  `eac_price_*` and federal premium × credit fraction, one certificate
  per MWh); PTC/ITC/45U/45Q tax credits are deliberately excluded.
- Campaign runs are gated on the §7 capacity-screen readiness criteria
  (plan D9/W3-R); treat capacity-evolution deltas produced before that
  GO as structural smoke, not results.
- No financial report parquets for case(s): `BAU`, `CES-20`, `CES-40` — run scripts/generate_financial_reports.py per case for full revenue deltas.
