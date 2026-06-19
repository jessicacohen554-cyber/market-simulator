# CAISO lever B (citygate-spot gas) — validation result (2026-06-19)

Branch: `claude/caiso-modeling-accuracy-td82v4`. Validates lever B from
`DIAGNOSIS-caiso-import-ladder-2026-06-19.md`: price the CAISO marginal gas at the
measured trading-hub **commodity spot** (Henry Hub month + state-citygate basis)
instead of the F923 **all-in delivered** cost (which loads in sunk pipeline
transport). Mechanism = the existing `gas_hub_basis_overlay`, now fed by the
`gas_basis_by_iso_month.csv` filled for all ISOs by the `fetch-eia-gas-prices`
workflow; activated for a run with `--gas-hub-basis-overlay`.

## Data landed

`fetch-eia-gas-prices` (after fixing the monthly-Henry-Hub series — RNGWHHM
returns empty, so monthly is derived from the daily RNGWHHD) committed, on `main`:
citygate basis for all 7 ISOs (CAISO 132 mo, ERCOT/MISO/SPP/PJM/NYISO + NEISO,
preserving NEISO's measured AGT rows) + a populated `henry_hub_monthly.csv`. The
model loads CAISO 2024 basis `[1.02, 3.67, 2.59, 0.97, 0.30, −0.12, 0.80, 1.04,
0.08, 0.91, 1.49, 1.51]` $/MMBtu over Henry Hub. Overlay fires: "1139 gas
generators repriced at the measured hub spot in 12/12 months (winter max $5.40)".

## Result — CAISO 2024 (load-weighted system LMP)

`--commitment --priced-interchange --hydro-backfill-year 2024 --hydro-eia930-monthly`
± `--gas-hub-basis-overlay`.

| | mean | p50 | Apr | May | Jun | Jul | Dec | gas TWh |
|---|---|---|---|---|---|---|---|---|
| baseline | 55.0 | 56.0 | 39.8 | 37.8 | 44.6 | 59.3 | 77.4 | 70.9 |
| **lever B** | **47.0** | **48.0** | 35.4 | 32.6 | 38.7 | 48.7 | 59.1 | **76.1** |
| actual RT | 32.9 | 34.0 | 13.5 | 10.9 | 22.0 | 42.8 | 42.0 | (67.7) |

**Price: works as diagnosed.** Mean **−$8.0** (55→47), median −$8, every month
lower (Dec −18, Jul −11). Closes ~36% of the +$22 body gap; the remaining ~$13 is
the structural floor + the import side (lever A), exactly as the diagnosis
predicted (gas cost is only part of the body).

**Volume: the catch.** Gas rises **70.9 → 76.1 TWh** (EIA-923 67.7, now +8.4 /
+12%): cheaper gas wins dispatch back from imports. So lever B **is not a clean
standalone keeper** — it trades the gas-volume mix for the price.

## Conclusion / next

Lever B is grounded (measured commodity spot, no curve-fitting) and measurably
lowers the body, but it must be **paired with lever A** (measured-hub import
prices, `caiso_import_hub_prices`, re-cheapening imports so they hold their share)
to keep gas near EIA-923 while still lowering price. The combined A+B run is the
next step, gated on confirming the OASIS intertie APNode names via
`fetch-caiso-intertie-lmp` `mode=probe`. Neither lever's default is flipped in
`_calibration_config` (NEISO-only for the gas overlay) — both stay opt-in until
the combined run validates.
