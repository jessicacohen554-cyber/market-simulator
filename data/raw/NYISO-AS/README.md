# NYISO-AS — raw

`NYISO_as_da_<year>.csv` / `NYISO_as_rt_<year>.csv` (2023–2025) — NYISO
ancillary-services day-ahead/real-time clearing prices:
`Time Stamp, Name, spin_10, nonsync_10, op_30, reg_cap`. NYISO publishes
clearing prices only (no cleared MW).

**Source:** NYISO OASIS ancillary-services daily/real-time price postings.

**Regeneration:** `scripts/process_nyiso_as.py` — folds monthly zips of
daily CSVs (real-time 5-minute `<YYYYMM01>rtasp_csv.zip`, day-ahead hourly
`<YYYYMM01>damasp_csv.zip`) into the per-year CSVs above.

**Known bug — do not trust as-is.** The script's `AS_DIR` constant still
points at the pre-relocation path `inputs/raw-data/NYISO-AS` (retired by the
W1 data-root relocation into `data/raw/`; see `data/README.md`), not
`data/raw/NYISO-AS/`. Re-running the script as committed will not find these
files or a `raw/` subdirectory of source zips (none currently exists here).
Fix the constant before relying on this script to regenerate the CSVs.

**Consumers:** `scripts/curate_ancillary_services.py`,
`scripts/derive_nyiso_rcpf_overlay.py`.
