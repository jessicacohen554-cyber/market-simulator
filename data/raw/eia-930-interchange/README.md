# eia-930-interchange — raw

`CISO interchange hourly.parquet`, `MISO interchange hourly.parquet`,
`ISNE interchange hourly.parquet` — the EIA-930 BA-to-BA net interchange
product (`TI` interchange family), long form per directly-interconnected
balancing authority (DIBA): columns `diba, mw, local_time`. EIA sign
convention: positive = the named BA exports to the DIBA. `local_time` is the
hour-ending timestamp on the BA's local clock, spanning the covered local
calendar years (2023-2025).

ISNE's DIBAs are its three external seams: `HQT` (Hydro-Québec TransÉnergie —
the Phase II + Highgate ties), `NBSO` (New Brunswick) and `NYIS` (New York).

**Source:** EIA-930 (Hourly Electric Grid Monitor), public domain — see
`docs/data-licensing.md` §1.

**Regeneration:** `scripts/fetch_eia930_interchange.py` (EIA API v2
`electricity/rto/interchange-data` route, same pagination/key pattern as
`scripts/fetch_eia930_long.py`):

    EIA_API_KEY=... python scripts/fetch_eia930_interchange.py --ba ISNE \
        --years 2023 2024 2025

The CISO/MISO files predate the script (manual pulls of the same product);
the ISNE file was fetched with it (2026-07-06). Raw data is immutable — the
script refuses to overwrite an existing file without `--force`.

**Consumers:**
- `scripts/derive_manitoba_firm_import.py` — filters MISO's file to the
  MHEB (Manitoba Hydro) DIBA for the firm-import floor.
- `scripts/derive_firm_import_floor.py` — same file.
- `scripts/derive_caiso_export_cap.py` — uses CISO's file as the realized
  ATC proxy for the export-cap derivation (a true OASIS export-ATC pull is
  an open follow-up, noted in that script).
- `scripts/derive_neiso_import_tranches.py` — uses ISNE's file (per-seam
  flow duration curves) to derive the measured NEISO import/export tranche
  ladders (`interchange_config.IMPORT_TRANCHES["NEISO"]` /
  `EXPORT_TRANCHES[_BY_YEAR]["NEISO"]`, audit C-6 closure).
