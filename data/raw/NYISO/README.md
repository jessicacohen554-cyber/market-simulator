# NYISO — raw

Manually-collected NYISO planning and market reference documents:

- `<year>-Gold-Book-Public.pdf` (2023–2026) — NYISO Load & Capacity Data
  Report ("Gold Book"). The **2026** edition (released April 2026, 166 pp,
  sha256 `43865c1cbe38ca2ef4c8319d11454881de2b9dde3e48867dbbd2e94855b908bf`)
  was fetched 2026-08-03 (FFR-SC) from
  `https://www.nyiso.com/documents/20142/2226333/2026-Gold-Book-Public.pdf`
  — the same URL pattern this README documents for 2024 — closing FF-G4 §8-D4
  item 3. It is the source of the NYISO row of
  `constants.DEMAND_GROWTH_RATES` (Table I-1a, NYCA Baseline Energy and Demand
  Forecasts, Energy-GWh Lower/Baseline/Higher columns).
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

**Exception — the ATC/TTC postings are DATA NEEDED (deliberately not committed).**
`scripts/data/derive_nyiso_central_east_ttc.py` reads NYISO's day-ahead Total
Transfer Capability export, either as `atc-ttc/` (the native MIS layout: one
`<yyyymm>01atc_ttc_csv.zip` per month — gitignored, see `../.gitignore`) or the
legacy single `ATC_TTC.zip`. Neither is committed: redistribution terms are
unverified (§ below) and it is ~17 MB of raw zips whose only product is the
small Central-East constants block. **Running the script with neither present
prints the exact per-month re-fetch command** (`http://mis.nyiso.com/public/csv/
atc_ttc/<yyyymm>01atc_ttc_csv.zip`), so the derivation is reproducible from a
bare checkout. Refreshed 2026-08-14 (nyiso-134) to cover 2018-2025.

**Gold Books 2018-2022 added 2026-08-14 (nyiso-134).** The older editions are
hosted under *different* Liferay document IDs and filenames than 2023+
(`<year>-Gold-Book-Final-Public.pdf` plus a UUID path segment for 2019-2022;
`2018 Load & Capacity Data (Gold Book).pdf` under `20142/0` for 2018), so the
`20142/2226333/<year>-Gold-Book-Public.pdf` pattern does **not** extrapolate
backwards — it 404s for every one of them. Note also that the **2018 edition has
no per-zone SCR/EDRP table**; it reports NYCA totals only (p.39 prose and Tables
IV-1a/IV-1b), and the zonal projection table first appears in 2019.

**Licensing note:** NYISO's redistribution terms are unclear/unverified —
see `docs/data-licensing.md` §7.
