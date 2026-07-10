# NYISO-AS — raw

`NYISO_as_da_<year>.csv` / `NYISO_as_rt_<year>.csv` (2023–2025, plus
2018–2022 + H1-2026 landed by the holdout-intake workflow below) — NYISO
ancillary-services day-ahead/real-time clearing prices:
`Time Stamp, Name, spin_10, nonsync_10, op_30, reg_cap`. NYISO publishes
clearing prices only (no cleared MW).

**Source:** NYISO MIS public postings, monthly zips of daily CSVs:
`http://mis.nyiso.com/public/csv/rtasp/<yyyymm01>rtasp_csv.zip` (real-time,
5-minute) and `http://mis.nyiso.com/public/csv/damasp/<yyyymm01>damasp_csv.zip`
(day-ahead, hourly). Confirmed live (HTTP 200, header schema byte-identical)
across 2018-01 through 2026-05 — no format change found across that span; the
per-zone column set and the 11 NYISO zone names (`WEST, GENESE, CENTRL,
NORTH, MHK VL, CAPITL, HUD VL, MILLWD, DUNWOD, N.Y.C., LONGIL`) are stable.

**Fetch:** `scripts/fetch_nyiso_as.py` — downloads the monthly rtasp/damasp
zips straight into the gitignored `data/raw/NYISO-AS/raw/` staging dir
(`RAW_DIR`), one zip per (market, month), idempotent (skips an
already-downloaded non-empty file).

**Regeneration:** `scripts/process_nyiso_as.py` — folds those monthly zips of
daily CSVs (real-time 5-minute `<YYYYMM01>rtasp_csv.zip`, day-ahead hourly
`<YYYYMM01>damasp_csv.zip`) into the per-year CSVs above, and (for `rt`, on
demand) the calibration-reference parquet
`data/raw/_validation-source/actual_as_reserve_NYISO.parquet`.

**Fixed 2026-07-10 (was broken end-to-end — no automated fetch path
existed).** Two stale-path bugs from the W1 data-root relocation
(`inputs/raw-data/` → `data/raw/`, `inputs/calibration/` →
`data/raw/_validation-source/`) are corrected: `AS_DIR` now points at
`data/raw/NYISO-AS` and `CAL_DIR` at `data/raw/_validation-source`. The
script also no longer depends on a pre-existing `NYISO-AS-Data.zip` outer
zip (never committed here, for any year including 2023-2025) — it reads
`RAW_DIR` directly once `fetch_nyiso_as.py` has populated it; the outer-zip
extraction is kept only as a legacy fallback for a hand-assembled bundle.

**Holdout intake:** `.github/workflows/holdout-intake-nyiso-as.yml` runs the
fetch + fold pipeline on a GitHub Actions runner (large multi-year payload,
too big for this session's push path) to land 2018-2022 + H1-2026 under the
2026-07-10 session-logged owner authorization (CLAUDE.md rule 22; data
intake only — no LP solve, no scoring, no calibration-complete marker
touched). Self-triggers on a push to the workflow file itself.

**Consumers:** `scripts/curate_ancillary_services.py`,
`scripts/derive_nyiso_rcpf_overlay.py`.
