# NYISO — raw

Manually-collected NYISO planning and market reference documents:

- `<year>-Gold-Book-Public.pdf` (2023–2025) — NYISO Load & Capacity Data
  Report ("Gold Book").
- `<year>-NYCA-Generators.xlsx` / `2025-NYCA-Existing-Generating-Facilities.xlsx`
  — NYCA generator lists.
- `NYISO-<year>-SOM-*-Report*.pdf` — NYISO annual State of the Market (SOM)
  reports.
- `N3050NY3m.xls` — EIA New York citygate gas price monthly series.
- `nyiso load reports {1..4}.zip` — NYISO OASIS load-report bulk downloads.

**Regeneration: hand-assembled — refetch procedure unknown for most files
here.** No script in `scripts/` or `src/` reads the Gold Book PDFs, the
NYCA-Generators spreadsheets, the SOM PDFs, `N3050NY3m.xls`, or the
`nyiso load reports *.zip` — they are cited only as manually-transcribed
background sources in `docs/nyiso-load-basis-handoff.md` and
`docs/multi-iso/nyiso-data-audit.md` (which does cite the live Gold Book URL,
e.g. `https://www.nyiso.com/documents/20142/2226333/2024-Gold-Book-Public.pdf`
for the 2024 edition — the pattern generalizes by year). Model constants
derived by hand from these documents (Gold-Book zonal shares, etc.) live in
`src/market_sim/config/iso_configs.py` and `config/scenarios.py`, not a
regeneration script.

**Exception — `ATC_TTC.zip` is DATA NEEDED.** `scripts/derive_nyiso_central_east_ttc.py`
expects `data/raw/NYISO/ATC_TTC.zip` (NYISO's day-ahead Total Transfer
Capability MIS export) and is **not currently present in this directory** —
re-fetch from NYISO's MIS ATC_TTC report posting before running that script.

**Licensing note:** NYISO's redistribution terms are unclear/unverified —
see `docs/data-licensing.md` §7.
