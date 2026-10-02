# Oil prices (raw)

| file | source | regenerate |
|---|---|---|
| `ny_harbor_ulsd_daily.csv` | EIA series `EER_EPD2DXL0_PF4_Y35NY_DPG` — New York Harbor Ultra-Low Sulfur No. 2 Diesel spot price FOB, $/gal, daily (EIA trading days). https://www.eia.gov/dnav/pet/hist_xls/EER_EPD2DXL0_PF4_Y35NY_DPGd.xls. Public domain (EIA). | `uv run python scripts/data/fetch_ny_harbor_distillate_daily.py --start-year 2019 --end-year 2025` |

Coverage **2019-01-02 .. 2025-12-31** (1,748 trading days). 2019-2021 (752 days)
were added 2026-10-02 (closeout-NEISO wave 1, rule 14 `[R-ACCURATE]`); the
2022-2025 rows re-fetched byte-identical. Consumed only for its within-month SHAPE
by `market_sim.data.fuel.oil_daily_shape_factors` under
`ScenarioConfig.dual_fuel_oil_daily_parity` (default off); the delivered level stays
the monthly EIA-923 receipt.

**Cross-ISO note.** Any keeper that arms `dual_fuel_oil_daily_parity` and solves
2019-2021 previously read an empty year there (all-ones shape, i.e. the flat monthly
receipt) and now reads the measured daily shape on replay. At the time of this intake
that is the NYISO keeper (`results/calibration/nyisonext26p_span/run_config.json`).

DATA NEEDED: none.
