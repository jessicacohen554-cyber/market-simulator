# NYISO — raw

Manually-collected NYISO planning and market reference documents:

- `<year>-Gold-Book-Public.pdf` (2018–2026) — NYISO Load & Capacity Data
  Report ("Gold Book"). **2023–2026 are gitignored payloads**; 2018–2022 stay
  tracked (see "Publication PDFs" below). The **2026** edition
  (released April 2026, 166 pp,
  sha256 `43865c1cbe38ca2ef4c8319d11454881de2b9dde3e48867dbbd2e94855b908bf`)
  was fetched 2026-08-03 (FFR-SC) from
  `https://www.nyiso.com/documents/20142/2226333/2026-Gold-Book-Public.pdf`
  — the same URL pattern this README documents for 2024 — closing FF-G4 §8-D4
  item 3. It is the source of the NYISO row of
  `constants.DEMAND_GROWTH_RATES` (Table I-1a, NYCA Baseline Energy and Demand
  Forecasts, Energy-GWh Lower/Baseline/Higher columns).
- `<year>-NYCA-Generators.xlsx` / `2025-NYCA-Existing-Generating-Facilities.xlsx`
  — NYCA generator lists.
- `NYISO-<year>-SOM-*Report*.pdf` (2020, 2022–2025) — NYISO annual State of the
  Market (SOM) reports. **Gitignored payloads** (see "Publication PDFs" below).
- `N3050NY3m.xls` — EIA New York citygate gas price monthly series.
- `nyiso load reports {1..4}.zip` — hand-made bundles of NYISO **MIS** monthly
  load archives. **Gitignored payloads** (see "Load-report zips" below).

**Regeneration: hand-assembled.** The PDFs and spreadsheets here are
**transcription sources, not machine inputs** — model constants derived from
them (Gold-Book zonal shares, the SCR/EDRP enrollment table, the SOM annual
fuel-index levels) live in `src/market_sim/config/iso_configs.py`,
`config/scenarios.py` and `scripts/data/build_nyiso_scr_edrp.py`'s `_SOURCES` /
`_ENROLLMENT` blocks, each row citing the document, table and page it was read
from. Two qualifications on the older "nothing reads these" claim, both
re-verified by fresh grep at `315a245` (2026-08-15):

- `scripts/data/build_nyiso_scr_edrp.py` **transcribes** the Gold Books (it
  cites the filenames in `_SOURCES`; it does not open them), and
  `scripts/data/curate_nyiso_som_hub_fuel_annual.py` reads the hand-transcribed
  `data/raw/gas-prices/nyiso_som_hub_fuel_annual.csv`, **not** the SOM PDFs.
  Neither breaks when a payload is absent.
- Three **frozen probes** do open Gold Book PDFs with `pypdf`
  (`_nyiso130_solar_gwh_reconciliation.py` → the 2026 edition,
  `_nyiso124_charter_g0_g1.py` → a glob over every edition,
  `_nyiso130_li_tsl_identification.py` → its own separate TSL cache). `pypdf`
  is not a project dependency and all three already report
  `{"unavailable": ...}` rather than crashing, so they degrade identically
  whether the payload is gitignored or the dependency is missing. Re-running
  one against the real bytes means restoring from the pin below first.

## Publication PDFs — payload gitignored (BLOAT-B-2)

The **5 SOM reports** and the **2023–2026 Gold Books** (44.9 + 11.1 MiB) are
**gitignored and no longer tracked at tip** — corpus conversion per
`docs/bloat-removal-plan-2026-08.md` §4.5 item B5 (class-approved under
release-plan §6 decision 4). `SHA256SUMS.txt` (this directory) is the committed
provenance record for exactly those 9 files.

**Everything else in this directory stays tracked**, including the **2018–2022
Gold Books**: they were committed 2026-08-14 by nyiso-134 as the D-3 immutable
sources behind the SCR/EDRP transcription, they are outside the owner-reviewed
BLOAT-B-2 item list (which names 2023–2026), and their re-fetch URLs are *not*
recorded (see the 2018-2022 note below — the 2023+ pattern 404s for them).

Every URL below was fetched and **verified byte-exact against the committed
file on 2026-08-15** (HTTP 200, `Content-Length` equal to the manifest's
`size_bytes`).

| File | Document | Source URL |
|---|---|---|
| `2023-Gold-Book-Public.pdf` | 2023 Load & Capacity Data Report | <https://www.nyiso.com/documents/20142/2226333/2023-Gold-Book-Public.pdf> |
| `2024-Gold-Book-Public.pdf` | 2024 Load & Capacity Data Report | <https://www.nyiso.com/documents/20142/2226333/2024-Gold-Book-Public.pdf> |
| `2025-Gold-Book-Public.pdf` | 2025 Load & Capacity Data Report | <https://www.nyiso.com/documents/20142/2226333/2025-Gold-Book-Public.pdf> |
| `2026-Gold-Book-Public.pdf` | 2026 Load & Capacity Data Report | <https://www.nyiso.com/documents/20142/2226333/2026-Gold-Book-Public.pdf> |
| `NYISO-2020-SOM-Report-final-5-18-2021.pdf` | 2020 SOM for the NYISO markets | <https://www.nyiso.com/documents/20142/2223763/NYISO-2020-SOM-Report-final-5-18-2021.pdf/c540fdc7-c45b-f93b-f165-12530be925c7> |
| `NYISO-2022-SOM-Full-Report__5-16-2023-final.pdf` | 2022 SOM | <https://www.potomaceconomics.com/wp-content/uploads/2023/05/NYISO-2022-SOM-Full-Report__5-16-2023-final.pdf> |
| `NYISO-2023-SOM-Full-Report__5-13-2024-Final.pdf` | 2023 SOM | <https://www.potomaceconomics.com/wp-content/uploads/2024/05/NYISO-2023-SOM-Full-Report__5-13-2024-Final.pdf> |
| `NYISO-2024-SOM-Full-Report_5-14-2025-final.pdf` | 2024 SOM | <https://www.potomaceconomics.com/wp-content/uploads/2025/05/NYISO-2024-SOM-Full-Report_5-14-2025-final.pdf> |
| `NYISO-2025-SOM-Report__5-19-2026-final.pdf` | 2025 SOM | <https://www.potomaceconomics.com/wp-content/uploads/2026/05/NYISO-2025-SOM-Report__5-19-2026-final.pdf> |

The Gold Book URL pattern `…/20142/2226333/<year>-Gold-Book-Public.pdf` holds
for 2023–2026 (all four verified). The SOM reports come from Potomac Economics
(NYISO's Market Monitoring Unit) under `wp-content/uploads/<YYYY>/<MM>/`, where
the segment is the WordPress upload month and does **not** generalize from the
report year — take the URLs verbatim. The 2020 SOM is the one still served by
NYISO itself, and is the copy `scripts/data/fetch_nyiso_lrr_pdfs.py` already
fetches with an md5 check. Landing pages:
<https://www.nyiso.com/markets-monitoring> ·
<https://www.potomaceconomics.com/markets-monitored/new-york-iso/>.

### Recovery / re-fetch

1. **Restore from git history — DEAD since the 2026-08-16 history rewrite**
   (`cleanup-large-blobs.yml` run #18 / 31955205445, owner decision;
   `docs/FINDING-history-rewrite-2026-08-16.md`). The pin
   `315a24524a851566c3d32cc88668fa32dcbd1d74` no longer resolves and its
   rewritten twin `94b9cda540b8` no longer carries these payloads (verified
   2026-08-16) — the blobs were stripped. `SHA256SUMS.txt` stays as the
   identity record a re-fetch is verified against.

2. **Re-fetch from the publishers.** Run from this directory:

   ```
   xargs -n1 curl -fLO <<'URLS'
   https://www.nyiso.com/documents/20142/2226333/2023-Gold-Book-Public.pdf
   https://www.nyiso.com/documents/20142/2226333/2024-Gold-Book-Public.pdf
   https://www.nyiso.com/documents/20142/2226333/2025-Gold-Book-Public.pdf
   https://www.nyiso.com/documents/20142/2226333/2026-Gold-Book-Public.pdf
   https://www.potomaceconomics.com/wp-content/uploads/2023/05/NYISO-2022-SOM-Full-Report__5-16-2023-final.pdf
   https://www.potomaceconomics.com/wp-content/uploads/2024/05/NYISO-2023-SOM-Full-Report__5-13-2024-Final.pdf
   https://www.potomaceconomics.com/wp-content/uploads/2025/05/NYISO-2024-SOM-Full-Report_5-14-2025-final.pdf
   https://www.potomaceconomics.com/wp-content/uploads/2026/05/NYISO-2025-SOM-Report__5-19-2026-final.pdf
   URLS
   curl -fL -o NYISO-2020-SOM-Report-final-5-18-2021.pdf \
     'https://www.nyiso.com/documents/20142/2223763/NYISO-2020-SOM-Report-final-5-18-2021.pdf/c540fdc7-c45b-f93b-f165-12530be925c7'
   sha256sum -c <(awk '$1 !~ /^#/ && NF>=3 {s=$1; $1=$2=""; sub(/^ +/,""); print s "  " $0}' SHA256SUMS.txt)
   ```

   (The 2020 SOM's URL ends in a Liferay UUID segment, so `-O` would name the
   file after the UUID — `scripts/data/fetch_nyiso_lrr_pdfs.py --force` does the
   same fetch with an md5 check if you prefer the scripted path.)

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

## Load-report zips — payload gitignored (BLOAT-B-2)

`nyiso load reports {1..4}.zip` (65.2 MiB) are **gitignored and no longer
tracked at tip** — corpus conversion per `docs/bloat-removal-plan-2026-08.md`
§4.6 item B6 (class-approved under release-plan §6 decision 4). They are
recorded in this directory's `SHA256SUMS.txt`.

**Zero consumers, re-verified by fresh grep at `315a245` (2026-08-15):** nothing
in `src/`, `scripts/` or `tests/` opens these filenames, and no code opens any
zip under `data/raw/NYISO/` other than `ATC_TTC.zip` / `atc-ttc/`. The zonal
load series the model actually reads is the derived
`data/raw/zone-specific-demand/NYISO_load_actuals_<year>.csv`, built by
`scripts/data/process_nyiso_zonal_load.py` from a **different** directory
(`data/raw/zone-specific-demand/NYISO/raw/<YYYYMM01>pal_csv.zip`) — that path is
golden-tier-listed and untouched here.

### What is inside them

The four outer zips are ad-hoc groupings from a manual browser download (dated
2026-06-19), not a product boundary — the same MIS product appears in several of
them. Their members are the standard `<YYYYMM01><product>_csv.zip` monthly
archives:

| Outer zip | Members | Products and month spans |
|---|---:|---|
| `nyiso load reports 1.zip` | 54 | `zonalBidLoad` 2022-01 … 2026-06 |
| `nyiso load reports 2.zip` | 22 | `pal` 2023-01 … 2026-06 |
| `nyiso load reports 3.zip` | 48 | `pal` 2022-01 … 2026-02 (29) · `palIntegrated` 2022-06 … 2023-12 (19) |
| `nyiso load reports 4.zip` | 77 | `pal` 2022-01 … 2025-08 (23) · `palIntegrated` 2022-01 … 2026-06 (54) |

The three products, all permanently-archived NYISO MIS public series:

| Product | Series | URL pattern |
|---|---|---|
| `pal` | P-58B Real-Time Actual Load, 5-minute, by load zone | `http://mis.nyiso.com/public/csv/pal/<YYYYMM>01pal_csv.zip` |
| `palIntegrated` | Integrated Real-Time Actual Load, hourly, by load zone | `http://mis.nyiso.com/public/csv/palIntegrated/<YYYYMM>01palIntegrated_csv.zip` |
| `zonalBidLoad` | P-59 DAM zonal bid load (Energy Bid / Bilateral / Price Cap / **Virtual** Load and Supply) | `http://mis.nyiso.com/public/csv/zonalBidLoad/<YYYYMM>01zonalBidLoad_csv.zip` |

All three patterns were fetched and verified on 2026-08-15 (e.g.
`20230101pal_csv.zip` → HTTP 200, 786,710 B, matching that member's size inside
`nyiso load reports 2.zip`). MIS monthly archives are the permanent public
series — unlike the ERCOT MIS rolling window, there is no known retention cliff.

### Recovery / re-fetch

1. **Restore from git history — DEAD since the 2026-08-16 history rewrite**
   (`cleanup-large-blobs.yml` run #18 / 31955205445, owner decision;
   `docs/FINDING-history-rewrite-2026-08-16.md`). The pin
   `315a24524a851566c3d32cc88668fa32dcbd1d74` no longer resolves and its
   rewritten twin `94b9cda540b8` no longer carries these zips (verified
   2026-08-16) — the blobs were stripped. The outer browser-download bundles
   are gone for good (they were never reproducible); the MEMBERS are the
   recoverable form, via route 2. `SHA256SUMS.txt` stays as the record of
   what the bundles held.

2. **Re-fetch the monthly archives from MIS.** There is no fetch script and the
   outer bundles are not reproducible (they are a browser-download artifact);
   fetch the members directly instead, which is the useful form anyway:

   ```
   for product in pal palIntegrated zonalBidLoad; do
     for ym in $(seq -f '2022%02g' 1 12) $(seq -f '2023%02g' 1 12) \
               $(seq -f '2024%02g' 1 12) $(seq -f '2025%02g' 1 12) \
               $(seq -f '2026%02g' 1 6); do
       curl -fLO "http://mis.nyiso.com/public/csv/$product/${ym}01${product}_csv.zip"
     done
   done
   ```

   **Holdout note (rule 22):** the spans run through 2026-06, i.e. into the
   locked-test H1-2026 window. That is fine — data intake is unrestricted and
   applied consistently across years; what is gated is *solving, scoring or
   registering* an out-of-training year. Nothing reads these files at all.
