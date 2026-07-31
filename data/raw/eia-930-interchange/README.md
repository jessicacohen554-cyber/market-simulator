# eia-930-interchange — raw

`CISO interchange hourly.parquet`, `MISO interchange hourly.parquet`,
`ISNE interchange hourly.parquet`, `PJM interchange hourly.parquet` — the
EIA-930 BA-to-BA net interchange product (`TI` interchange family), long form
per directly-interconnected balancing authority (DIBA): columns
`diba, mw, local_time`. EIA sign convention: positive = the named BA exports
to the DIBA. `local_time` is the hour-ending timestamp on the BA's local
clock, spanning the covered local calendar years — 2023-2025 for
CISO/MISO/ISNE; **2019 - H1-2026 for PJM**, extended 2026-07-31 under the
rule-22 intake authorization logged in `calibration-complete.json`.

**PJM span and its two source-side limits.** The EIA API v2
`interchange-data` route returns **no PJM rows for any month of 2018**
(probed month-by-month 2026-07-31: `total: 0` for 2018-01/04/07/08/09/10/12;
first rows 2019-01) — a publication floor for this product, not a fetch gap,
so 2018 is absent rather than padded. 2026 is capped at hour-ending
**2026-07-01 00:00**, the H1 authorization boundary, not the API's own
horizon. Per-year DIBA-hour coverage: 2019 99.7% · 2020 99.4% · 2021
**95.5%** · 2022 99.5% · 2023 99.4% · 2024 99.4% · 2025 97.0% · H1-2026
95.1%. The 2021 dip is a hole in EIA's own submission — CPLE is complete
(8,759 h) while the other six DIBAs are each cut to 8,303 h by the same
~457-hour gap — the same class of incompleteness the committed 2025 block
already carries, not a fetch artifact.

ISNE's DIBAs are its three external seams: `HQT` (Hydro-Québec TransÉnergie —
the Phase II + Highgate ties), `NBSO` (New Brunswick) and `NYIS` (New York).

PJM's DIBAs are `CPLE`, `CPLW`, `DUK`, `LGEE`, `MISO`, `NYIS`, `TVA`.
**Boundary caveat:** PJM's 930 submission disagrees materially with both
PJM's own settlement-grade tie-line file
(`data/raw/iso-specific-transmission/PJM_{year}_import_export_act_sch_interchange.csv`)
and the counterparty meters on the MISO seam (2023: 56.6 TWh exported per
this product vs 35.3 TWh in the tie file vs 33.5 TWh in MISO's own 930 book
— pseudo-tie / dynamic-schedule attribution differences between
submissions). The PJM seam-ladder derivation
(`scripts/derive_pjm_seam_ladders.py`) therefore uses the tie-line file as
its flow source and keeps this parquet as the printed cross-check.

**Source:** EIA-930 (Hourly Electric Grid Monitor), public domain — see
`docs/data-licensing.md` §1.

**Regeneration:** `scripts/fetch_eia930_interchange.py` (EIA API v2
`electricity/rto/interchange-data` route, same pagination/key pattern as
`scripts/fetch_eia930_long.py`):

    EIA_API_KEY=... python scripts/data/fetch_eia930_interchange.py --ba ISNE \
        --years 2023 2024 2025

The CISO/MISO files predate the script (manual pulls of the same product);
the ISNE file was fetched with it (2026-07-06), the PJM file likewise
(2026-07-10; extended to 2019 - H1-2026 on 2026-07-31, with the committed
2023-01-01 01:00 .. 2026-01-01 00:00 block asserted content-identical across
the merge). Raw data is immutable — the script refuses to overwrite an
existing file without `--force`.

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
- `scripts/derive_pjm_seam_ladders.py` — prints PJM's file as the boundary
  CROSS-CHECK only (the ladder derivation's flow source is PJM's tie-line
  file; see the boundary caveat above).
