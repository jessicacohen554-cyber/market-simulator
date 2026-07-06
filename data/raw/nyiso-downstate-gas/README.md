# nyiso-downstate-gas (raw source pointer)

The `nyiso-downstate-gas` curated datatype (daily downstate NYISO delivered-gas
index for the LM6000 CT peaker fleet) is built from measured series that already
live under `data/raw/gas-prices/` — this datatype adds no new raw files, it
reconciles existing ones (like the consolidated `fuel-*` datatypes). Curated by
`scripts/curate_nyiso_downstate_gas.py` via `scripts/lib/nyiso_downstate_gas.py`.

## Source files (all under `data/raw/gas-prices/`)

| File | Role | Source | Cadence |
|------|------|--------|---------|
| `transco_z6_ny_daily.csv` | pipeline-hub daily spot the peakers price off | EIA Natural Gas Weekly Update "New York" spot (NGI Daily GPI); `scripts/fetch_transco_daily_spot.py` | daily (trading days) |
| `henry_hub_daily.csv` | Henry Hub daily spot (provenance component) | EIA DNAV `RNGWHHD`; `scripts/fetch_eia_gas_prices.py` | daily (trading days) |
| `nyiso_downstate_ct_gas_basis_monthly.csv` | monthly LDC city-gate premium over the Transco hub (floored 0) | EIA NG `N3050NY3` citygate − measured Transco Z6 NY monthly; `scripts/fetch_nyiso_downstate_gas_basis.py` | monthly |

## Construction

Free-data memo §1.4 (`docs/handoffs/free-data-sourcing-2026-07.md`):

```
delivered_gas[day] = transco_z6_ny[day] + ldc_premium[month]
```

The measured Transco Z6 NY pipeline-hub **daily** spot (captures cold-snap
blowouts on the exact days the peakers run) plus the measured **monthly** LDC
city-gate premium over that hub (distribution + demand-charge + interruptible
adder; published only monthly). Every component is a measured, forward-native
market/tariff input that regenerates for a forward year and responds to changed
conditions — rule-13 admissible. Nothing is fitted to a price/volume residual.

Non-trading days in the daily hub series are linearly interpolated onto every
calendar day (the same gap-fill the daily fuel overlays use). The monthly LDC
premium is broadcast to each day of its month.

## DATA NEEDED

- Nothing blocking. The three source files are committed and cover 2023–2025.
- **Sharpening (optional, not blocking):** a true *daily* downstate city-gate
  index (Transco Z6 NY / Algonquin Citygate / Iroquois Z2 from ICE/Platts/NGI)
  would replace the monthly LDC premium with daily resolution — paywalled
  (`docs/handoffs/free-data-sourcing-2026-07.md` §1.5). The free monthly LDC
  premium is the best available proxy for the intra-month interruptible spike.
- Forward years: extend `transco_z6_ny_daily.csv` and
  `nyiso_downstate_ct_gas_basis_monthly.csv` as new months land, then re-run
  `python scripts/curate_nyiso_downstate_gas.py`.

## ISO coverage

Only NYISO has a downstate LDC-island non-firm peaker construct. Other ISOs have
no analog (energy-only ERCOT, firm-transport CC fleets elsewhere) and register no
spec — see `scripts/lib/nyiso_downstate_gas.REGISTRY`.
