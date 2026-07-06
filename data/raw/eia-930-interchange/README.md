# eia-930-interchange — raw

`CISO interchange hourly.parquet`, `MISO interchange hourly.parquet` — the
EIA-930 BA-to-BA net interchange product (`TI` interchange family), long
form per directly-interconnected balancing authority (DIBA): columns
`diba, mw, local_time`. EIA sign convention: positive = the named BA exports
to the DIBA.

**Source:** EIA-930 (Hourly Electric Grid Monitor), public domain — see
`docs/data-licensing.md` §1.

**Regeneration: no fetch script in this checkout under this exact name.**
Like the original `data/raw/eia-930-hourly/` extracts, these two files
appear to be a manual pull (no committed script writes to
`eia-930-interchange/` specifically). To refresh, use the EIA API v2
`electricity/rto/interchange-data` route for the `MISO`/`CISO` BAs following
the same pagination pattern as `scripts/fetch_eia930_long.py`, writing the
long-form `diba, mw, local_time` schema above.

**Consumers:**
- `scripts/derive_manitoba_firm_import.py` — filters MISO's file to the
  MHEB (Manitoba Hydro) DIBA for the firm-import floor.
- `scripts/derive_firm_import_floor.py` — same file.
- `scripts/derive_caiso_export_cap.py` — uses CISO's file as the realized
  ATC proxy for the export-cap derivation (a true OASIS export-ATC pull is
  an open follow-up, noted in that script).
