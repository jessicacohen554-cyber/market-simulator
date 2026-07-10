# zone-specific-demand — raw

Per-zone hourly/metered load, used to derive each ISO's zonal load-share
weights.

| Location | Contents | Source | Regeneration |
|---|---|---|---|
| top level | `ERCOT_Native_Load_<year>.xlsx` (2022–2025) **and** `ERCOT_Native_Load_<year>.csv` (2018–2021, 2026 H1) | ERCOT "Historical Hourly Load Data" (`ercot.com/gridinfo/load/load_hist`), report NP6-345-CD "Actual System Load by Weather Zone" — **not** NP3-565-CD (that ID is the unrelated 7-day load *forecast* product; corrected 2026-07-10 holdout intake) | `https://www.ercot.com/files/docs/<pub-year>/<mm>/<dd>/Native_Load_<year>.zip` (annual zip, one xlsx inside, identical column layout to the 2022-2025 files); 2018–2021 + 2026 H1 landed 2026-07-10 rule-22 holdout intake (validation/locked-test years, no-LP fetch only — see `docs/data-register-2026-07.md`), committed as **CSV** (byte-identical values, `pd.read_excel(...).to_csv(...)` re-export) rather than `.xlsx` because this session's GitHub write path (`push_files`/`create_or_update_file`) transports UTF-8 text only, not binary blobs — a tooling constraint, not a data change |
| top level | `PJM<year>_hrl_load_metered.csv` (2023–2025) | PJM DataMiner2 metered hourly load by zone | manual download (DataMiner2) — see `docs/data-licensing.md` §4 |
| `CAISO/` | `CAISO_tac_load_hourly_<year>.csv` | CAISO OASIS `SLD_FCST` (`market_run_id=ACTUAL`) | `scripts/fetch_caiso_oasis.py` + `scripts/postprocess_oasis_downloads.py` |
| `MISO/` | `miso_subba_demand_2023-2025.csv` (see `MISO/SOURCES.md`) | EIA Hourly Electric Grid Monitor API v2 `electricity/rto/region-sub-ba-data`, pulled 2026-06-22 | re-run the API v2 pull described in `MISO/SOURCES.md` |
| `NYISO/` | `NYISO_load_actuals_<year>.csv`, `raw/*pal_csv.zip` (36 monthly archives) | NYISO OASIS "pal" actual-load zips | `scripts/process_nyiso_zonal_load.py` |

**Chunked-file convention (2026-07-10 rule-22 holdout intake):** this
session's GitHub write path (`push_files`/`create_or_update_file`) accepts
only UTF-8 text, one literal string per call, with an empirically small
per-call ceiling (~90 KB) — far below the multi-MB size of a raw annual
load file, and it cannot carry binary content at all. Files that don't fit
are committed gzip-compressed, base64-encoded, and split into ~90 KB text
parts named `<original-filename>.gz.b64.part001`, `part002`, ... Rebuild
the original file with `python scripts/reassemble_chunked_raw.py
<path/to/original-filename>` (finds the matching parts automatically). This
is a transport workaround only — the reassembled bytes are byte-identical
to the source download, not a data change.

**Known raw-file quirk:** `ERCOT_Native_Load_2026.xlsx` (H1 2026, fetched
2026-07-10) contains May 2026 twice (744 duplicate `Hour Ending` rows) — a
revision artifact in ERCOT's own published workbook, left byte-verbatim
since this is an immutable raw download; any consumer must dedupe on
`Hour Ending` before use.

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
