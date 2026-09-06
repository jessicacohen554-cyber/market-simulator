# CES premium-ladder campaign report — NEISO — neiso_ces_premium_matrix_poc_f1b2dc5e9f

**deterministic scenario range -- NOT a probability band** — deltas are
case-vs-BAU differences on one deterministic ladder, not a probability
statement. Dollars are real 2026$.

## Cases

| Case | Cache key | Crediting | Premium @2026 ($/MWh) |
|---|---|---|---|
| BAU | `5e2c52ea81694c10` | (CES off) | 0.00 |
| CES-20 | `43b921da2f0bcfc7` | clean_capture | 20.00 |
| CES-40 | `7d36e0b517ffb0e3` | clean_capture | 40.00 |

## Clean-share vs premium

Final cached year on disk: **2030**.

| case | premium_usd_per_mwh | clean_share | negative_price_hours | avg_price_usd_per_mwh |
|---|---|---|---|---|
| BAU | 0.000 | 0.500 | 0.000 | 66.840 |
| CES-20 | 20.000 | 0.622 | 0.000 | 52.720 |
| CES-40 | 40.000 | 0.828 | 0.000 | 41.460 |

## Capacity deltas vs BAU (final year, GW)

| case | fuel | capacity_gw | capacity_gw_bau | capacity_gw_delta |
|---|---|---|---|---|
| CES-20 | gas_cc | 2.846 | 3.036 | -0.190 |
| CES-20 | gas_cc_ccs | 8.993 | 8.803 | 0.190 |
| CES-40 | gas_cc | 2.842 | 3.036 | -0.194 |
| CES-40 | gas_cc_ccs | 8.997 | 8.803 | 0.194 |

## Capacity-evolution deltas vs BAU (ledger totals, MW)

| case | event | tech | mw | mw_delta |
|---|---|---|---|---|
| BAU | build | gas_cc | 1000.0 | 0.0 |
| BAU | build | gas_ct | 50.2 | 0.0 |
| BAU | build | solar | 2000.0 | 0.0 |
| BAU | build | wind | 1000.0 | 0.0 |
| BAU | retirement | coal | 108.0 | 0.0 |
| BAU | retirement | gas_cc | 2041.1 | 0.0 |
| BAU | retirement | gas_ct | 1.6 | 0.0 |
| BAU | retirement | gas_st | 95.8 | 0.0 |
| BAU | retrofit | gas_cc_ccs | 8802.6 | 0.0 |
| CES-20 | build | gas_cc | 1000.0 | 0.0 |
| CES-20 | build | gas_ct | 50.2 | 0.0 |
| CES-20 | build | solar | 2000.0 | 0.0 |
| CES-20 | build | wind | 1000.0 | 0.0 |
| CES-20 | retirement | coal | 108.0 | 0.0 |
| CES-20 | retirement | gas_cc | 2041.1 | 0.0 |
| CES-20 | retirement | gas_ct | 1.6 | 0.0 |
| CES-20 | retirement | gas_st | 95.8 | 0.0 |
| CES-20 | retrofit | gas_cc_ccs | 8993.1 | 190.4 |
| CES-40 | build | gas_cc | 1000.0 | 0.0 |
| CES-40 | build | gas_ct | 50.2 | 0.0 |
| CES-40 | build | solar | 2000.0 | 0.0 |
| CES-40 | build | wind | 1000.0 | 0.0 |
| CES-40 | retirement | coal | 108.0 | 0.0 |
| CES-40 | retirement | gas_cc | 2041.1 | 0.0 |
| CES-40 | retirement | gas_ct | 1.6 | 0.0 |
| CES-40 | retirement | gas_st | 95.8 | 0.0 |
| CES-40 | retrofit | gas_cc_ccs | 8997.0 | 194.4 |

## Premium capture (credited delivered / potential MWh)

| case | premium_usd_per_mwh | credited_delivered_mwh | credited_potential_mwh | premium_capture_rate |
|---|---|---|---|---|
| BAU | 0.000 | 61776574.037 | 131337863.268 | 0.470 |
| CES-20 | 20.000 | 76710145.384 | 132922680.148 | 0.577 |
| CES-40 | 40.000 | 102262434.977 | 132955514.433 | 0.769 |

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
