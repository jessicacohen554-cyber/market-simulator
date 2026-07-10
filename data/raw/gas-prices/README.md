# gas-prices — raw

Natural gas spot/citygate price series used for fuel-cost passthrough.

| File | Source | Regeneration |
|---|---|---|
| `henry_hub_daily.csv`, `henry_hub_monthly.csv` | EIA series `RNGWHHD` ("Natural Gas Spot and Futures Prices (NYMEX)"), EIA API v2 | `scripts/fetch_eia_gas_prices.py` |
| `eia_citygate_IL_MI_monthly_2023-2025.csv` | EIA series `N3050IL3`/`N3050MI3` ("Natural Gas Citygate Price"), EIA API v2 (see `SOURCES_miso_citygate.md` in this dir) | `scripts/fetch_eia_gas_prices.py` |
| `algonquin_citygate_daily.csv` | NGI's Daily Gas Price Index, displayed on EIA's Natural Gas Weekly Update page | `scripts/fetch_algonquin_daily_spot.py` — scrapes `https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/<year>/<mm_dd>/` |
| `transco_z6_ny_daily.csv` | NGI's Daily Gas Price Index (same page, "New York" row) | `scripts/fetch_transco_daily_spot.py` |
| `caiso_citygate_daily.csv` | NGI's Daily Gas Price Index (same page, "Cal. Comp. Avg" row) | `scripts/fetch_caiso_citygate_daily.py` |
| `transco_z6_iroquois_monthly.csv` | NGI-adjacent monthly hub series (merged by the NYISO narrative fetcher) | `scripts/fetch_nyiso_gas_narrative.py` |
| `nyiso_downstate_ct_gas_basis_monthly.csv` | derived: EIA `N3050NY3` (NY citygate) minus `transco_z6_iroquois_monthly.csv` | `scripts/fetch_nyiso_downstate_gas_basis.py` |
| `SOURCES_miso_citygate.md` | provenance note for the MISO citygate pull (pulled 2026-06-22) | — |
| `nyiso_som_hub_fuel_annual.csv` | hand-transcribed NYISO SOM Figure A-6 annual per-hub fuel index prices, 2018–2025 (5 gas hubs incl. **Iroquois Z2** + ULSK/ULSD/FO6) — the free measured Z2 annual level; SOM PDFs under `data/raw/NYISO/`; daily/monthly Z2 stays a Platts licence ask (Ask C1, `docs/handoffs/nyiso-data-asks-2026-07.md`) | `scripts/curate_nyiso_som_hub_fuel_annual.py` (transcription is by hand; each row cites doc + page) |

**⚠️ Licensing note — read before treating this directory as uniformly
public domain.** Henry Hub and the EIA-native citygate series are EIA's own
public-domain data. **`algonquin_citygate_daily.csv`, `caiso_citygate_daily.csv`,
`transco_z6_ny_daily.csv`, and `transco_z6_iroquois_monthly.csv` are a
proprietary third-party index (NGI's Daily Gas Price Index, Natural Gas
Intelligence / Hart Energy) that EIA merely displays** — not released into
the public domain by its actual owner. See `docs/data-licensing.md` §5 for
the full finding and the flag for owner review; **this README does not
resolve that finding, it points to it.**

**Consumer:** `src/market_sim/data/fuel.py` and the offer-curve passthrough
sigmoids; `gas_basis_by_iso_month.csv` (sibling top-level file, produced by
`scripts/fetch_eia_gas_prices.py`, fills hub basis for all six ISOs from
these series).
