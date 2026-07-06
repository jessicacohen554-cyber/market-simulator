# zone-specific-demand — raw

Per-zone hourly/metered load, used to derive each ISO's zonal load-share
weights.

| Location | Contents | Source | Regeneration |
|---|---|---|---|
| top level | `ERCOT_Native_Load_<year>.xlsx` (2022–2025) | ERCOT MIS Native Load by Weather Zone | manual download (ERCOT MIS) |
| top level | `PJM<year>_hrl_load_metered.csv` (2023–2025) | PJM DataMiner2 metered hourly load by zone | manual download (DataMiner2) — see `docs/data-licensing.md` §4 |
| `CAISO/` | `CAISO_tac_load_hourly_<year>.csv` | CAISO OASIS `SLD_FCST` (`market_run_id=ACTUAL`) | `scripts/fetch_caiso_oasis.py` + `scripts/postprocess_oasis_downloads.py` |
| `MISO/` | `miso_subba_demand_2023-2025.csv` (see `MISO/SOURCES.md`) | EIA Hourly Electric Grid Monitor API v2 `electricity/rto/region-sub-ba-data`, pulled 2026-06-22 | re-run the API v2 pull described in `MISO/SOURCES.md` |
| `NYISO/` | `NYISO_load_actuals_<year>.csv`, `raw/*pal_csv.zip` (36 monthly archives) | NYISO OASIS "pal" actual-load zips | `scripts/process_nyiso_zonal_load.py` |

**Orphaned — not referenced by any script:**
`ERCOTSysLoadbyForecastZone2023-2025.zip` and
`cdr.np6-346-cd.00014836.20260605.133719.364.zip` (the latter matches ERCOT
NP6-346-CD "Actual System Load by Forecast Zone" naming, but nothing
currently reads it).

**Consumers:** `scripts/curate_zonal_shares.py` (reads the ERCOT/PJM files
directly), `scripts/derive_load_shares.py` (per-ISO zonal-share derivation
for all four represented ISOs).

**Licensing note:** spans CAISO (unclear/conditional), PJM (conditional,
non-member ban), NYISO (unclear/unverified), and ERCOT (permitted) — see
`docs/data-licensing.md` §§3–7.
