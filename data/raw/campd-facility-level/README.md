# campd-facility-level — raw

`<ST>_<year>.parquet` (13 states: AL, CA, DE, IL, MA, MD, ME, NH, NJ, NY, OR,
PA, TX; 2023–2025) — EPA CAMPD bulk hourly **facility-level** emissions: one
row per (facility, hour), with `unit_id = "ALL"` so the join key stays
non-null. Where a state appears in both this facility grain and the
unit-level grain (`data/raw/campd-unit-level/`), the more granular
unit-level rows win (`scripts/curate_emissions.py`).

**Source:** EPA Clean Air Markets Program Data (CAMPD), public domain — see
`docs/data-licensing.md` §1.

**Regeneration: no fetch script in this checkout.**
`scripts/fetch_campd_unit_level.py` targets the **unit-level**
(`data/raw/campd-unit-level/`) API route only and does not cover this
facility-level grain. To refresh, use the CAMPD facility-level bulk-files
route (`https://api.epa.gov/easey/bulk-files/emissions/hourly/state/...`)
mirroring the unit-level fetcher's pagination/rate-limit handling, or the
CAMPD web UI's facility-level export.

**Consumers:** `scripts/curate_emissions.py`,
`scripts/audit_capacity_vs_campd.py`.
