# gas-prices — raw

Natural gas spot/citygate price series used for fuel-cost passthrough.

| File | Source | Regeneration |
|---|---|---|
| `henry_hub_daily.csv`, `henry_hub_monthly.csv` | EIA series `RNGWHHD` ("Natural Gas Spot and Futures Prices (NYMEX)"), EIA API v2 | `scripts/fetch_eia_gas_prices.py` |
| `eia_citygate_IL_MI_monthly_2023-2025.csv` | EIA series `N3050IL3`/`N3050MI3` ("Natural Gas Citygate Price"), EIA API v2 (see `SOURCES_miso_citygate.md` in this dir) | `scripts/fetch_eia_gas_prices.py` |
| `eia_delivered_gas_{OK,KS,TX,NM}_monthly_2023-2025.csv`, `eia_N3045{OK,KS,TX,NM}3m_2026-09-06.xls` | EIA series `N3045<ST>3` ("Natural Gas Price Sold to Electric Power Consumers", $/Mcf, monthly) for the SPP footprint's gas states, 2023-01..2025-12 — pulled 2026-09-06 from the key-free dnav workbooks `https://www.eia.gov/dnav/ng/hist_xls/N3045<ST>3m.xls`, committed beside the CSVs as evidence. **OK is NA for every month of 2025** (EIA's own gap: `N3045OK3` last publishes 2024-12 while KS/TX/NM run to 2026-06) and **NM prints negative months** (Waha/Permian negative basis, real). Details and the consumer caveats: `SOURCES_spp_gas.md`. Public domain (EIA). | manual pull; re-fetch the xls and re-cut 2023-01..2025-12 |
| `eia_delivered_gas_{OK,KS,TX,NM}_monthly_2019-2022.csv` | The same four EIA `N3045<ST>3` series for 2019-01..2022-12 — the SPP back-year intake (SPP-15, `docs/handoffs/FINDING-spp-15-2026-09-06.md`; charter `docs/multi-iso/spp-addition-plan-2026-09.md` §8 SPP-15, r#4 am.1). Cut from the SAME committed `eia_N3045<ST>3m_2026-09-06.xls` workbooks, which were re-fetched 2026-09-06 and are sha256-identical (no EIA revision, so no new workbook is committed); the cut reproduces all four `_2023-2025.csv` files byte-identically before being applied to this window. **OK is NA for all 36 months of 2019-2021** — `N3045OK3` publishes nothing between 2014-04 and 2021-12, so of 2019-2025 Oklahoma exists only for 2022/2023/2024. **2021-02 is Winter Storm Uri**: KS $65.23, TX $61.88, NM $24.82 /Mcf, real and carried verbatim. Rule 22 data prep, not a spend. Caveats: `SOURCES_spp_gas.md`. Public domain (EIA). | manual pull; re-cut 2019-01..2022-12 from the committed xls |
| `eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv`, `SHA256SUMS_N3045_state_workbooks_2026-09-08.txt` | EIA series `N3045<ST>3` for ALL states + DC + `N3045US3` ("Natural Gas Price Sold to Electric Power Consumers", $/Mcf, monthly), 2018-01..2026-06 on a complete state x month grid (`NA` where unpublished) — pulled 2026-09-08 from the same key-free dnav workbooks as the SPP-state files (which it reproduces value for value). The reference for the EIA-923 own-month gas-price plausibility screen (`plant_prices.py`, SPP-49 / SPP-46 R-1). Workbooks not committed; identity in the SHA256SUMS file. Details and the consumer caveats: `SOURCES_eia_delivered_gas_electric_power_by_state.md`. Public domain (EIA). | manual pull; re-fetch the 52 xls and re-cut 2018-01..2026-06 |
| `algonquin_citygate_daily.csv` | NGI's Daily Gas Price Index, displayed on EIA's Natural Gas Weekly Update page | `scripts/fetch_algonquin_daily_spot.py` — scrapes `https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/<year>/<mm_dd>/` |
| `transco_z6_ny_daily.csv` | NGI's Daily Gas Price Index (same page, "New York" row) | `scripts/fetch_transco_daily_spot.py` |
| `caiso_citygate_daily.csv` | NGI's Daily Gas Price Index (same page, "Cal. Comp. Avg" row) | `scripts/fetch_caiso_citygate_daily.py` |
| `miso_citygate_daily.csv` | NGI's Daily Gas Price Index (same page, "Chicago" row) — MISO North/Central Chicago Citygate daily; see `SOURCES_miso_citygate.md` | `scripts/fetch_miso_citygate_daily.py` — scrapes the same EIA NG Weekly archive |
| `transco_z6_iroquois_monthly.csv` | NGI-adjacent monthly hub series (merged by the NYISO narrative fetcher) | `scripts/fetch_nyiso_gas_narrative.py` |
| `nyiso_downstate_ct_gas_basis_monthly.csv` | derived: EIA `N3050NY3` (NY citygate) minus `transco_z6_iroquois_monthly.csv` | `scripts/fetch_nyiso_downstate_gas_basis.py` |
| `eia_citygate_CA_monthly.csv`, `eia_N3050CA3m_2026-09-04.xls` | EIA series `N3050CA3` ("Natural Gas Citygate Price in California", $/Mcf, monthly) as PUBLISHED on 2026-09-04 — `https://www.eia.gov/dnav/ng/hist_xls/N3050CA3m.xls` (the dnav page `hist/n3050ca3m.htm` shows the same cells). Committed as EVIDENCE (caiso-246): the survey is **NA for 2025-09, 2025-10, 2025-11 and 2026-04**, so the CAISO hub-basis coverage gap in `gas_basis_by_iso_month.csv` is the SOURCE's, not the fetch's. `published` column = `value` / `NA`. Public domain (EIA). | manual pull; re-fetch the xls when EIA back-fills |
| `SOURCES_miso_citygate.md` | provenance note for the MISO citygate pull (pulled 2026-06-22) | — |
| `SOURCES_nwpp_gas.md` | **NWPP** (lane NWPP-12, 2026-09-13): no new series — which hub prices which card-N5 zone (Sumas / Stanfield / Opal / Kern River), the **measured 2.51× internal gas spread** across the footprint (NWMT 1.815 vs PACE 4.564 $/MMBtu, 2023–2025), and the established negative that Stanfield / Opal / Kern River have **no free public series** reachable (EIA's weekly table carries four points only; `ice_natgas-<yr>final.xlsx` is 404). Points consumers at the committed per-state `N3045` table and the per-plant EIA-923 series instead | — (a provenance note; nothing regenerates) |
| `nyiso_som_hub_fuel_annual.csv` | hand-transcribed NYISO SOM Figure A-6 annual per-hub fuel index prices, 2018–2025 (5 gas hubs incl. **Iroquois Z2** + ULSK/ULSD/FO6) — the free measured Z2 annual level; SOM PDFs under `data/raw/NYISO/`; daily/monthly Z2 stays a Platts licence ask (Ask C1, `docs/handoffs/nyiso-data-asks-2026-07.md`) | `scripts/curate_nyiso_som_hub_fuel_annual.py` (transcription is by hand; each row cites doc + page) |

**⚠️ Licensing note — read before treating this directory as uniformly
public domain.** Henry Hub and the EIA-native citygate series are EIA's own
public-domain data. **`algonquin_citygate_daily.csv`, `caiso_citygate_daily.csv`,
`miso_citygate_daily.csv`, `transco_z6_ny_daily.csv`, and
`transco_z6_iroquois_monthly.csv` are a
proprietary third-party index (NGI's Daily Gas Price Index, Natural Gas
Intelligence / Hart Energy) that EIA merely displays** — not released into
the public domain by its actual owner. See `docs/data-licensing.md` §5 for
the full finding and the flag for owner review; **this README does not
resolve that finding, it points to it.**

**Consumer:** `src/market_sim/data/fuel.py` and the offer-curve passthrough
sigmoids; `gas_basis_by_iso_month.csv` (sibling top-level file, produced by
`scripts/fetch_eia_gas_prices.py`, fills hub basis for all six ISOs from
these series).
