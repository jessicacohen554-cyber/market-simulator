# PJM-AS — raw

PJM ancillary-services market data and reference manuals:

- `reserve_market_results_<year>.parquet` / `da_reserve_market_results_<year>.parquet`
  — PJM DataMiner2 "Ancillary Services Market Results — Reserve Market
  Results" (RT / DA), 2023–2025.
- `ancillary_services_<year>.parquet` / `da_ancillary_services_<year>.parquet`
  — PJM's long/tall AS product-price feed (product in `ancillary_service`,
  price in `value`).
- `pjm_<year>_as_up_mw.parquet` — derived AS-withholding MW series (see
  below).
- `m11.pdf`, `m11v127-*.pdf`, `m11v129-*.pdf` — PJM Manual 11 (Energy &
  Ancillary Services Market Operations) revisions. **Gitignored payloads**
  (see "Reference PDFs" below).
- `shortage-pricing-fact-sheet.pdf`, `E-3-052120.pdf` — reference/methodology
  documents. Not read by any script — background only. **Gitignored payloads**.

**Source:** PJM DataMiner2 (`dataminer2.pjm.com`).

**Regeneration: hand-assembled — no fetch script for the raw DataMiner2
parquets in this checkout.** The `reserve_market_results_*` /
`da_reserve_market_results_*` / `ancillary_services_*` /
`da_ancillary_services_*` parquets were pulled manually from DataMiner2; no
`fetch_*.py` script produces them. `pjm_<year>_as_up_mw.parquet` **is**
regenerable — `scripts/build_pjm_as_withholding.py` derives it from the
`reserve_market_results_<year>.parquet` files already on disk.

**Known bug in a consumer.** `scripts/derive_pjm_ordc_overlay.py` (which
reads `reserve_market_results_{year}.parquet` / `da_reserve_market_results_{year}.parquet`)
still points its `RAW_DIR` at the pre-relocation path
`inputs/raw-data/PJM-AS` rather than `data/raw/PJM-AS` — fix before relying
on it to find these files.

**Licensing note:** PJM DataMiner2 data carries redistribution conditions —
see `docs/data-licensing.md` §4. As of this writing that section is still an
**open finding for owner review, not a resolved question**: PJM's DataMiner2
Terms of Use restrict bulk republication to PJM Members, and it is
unconfirmed whether the account used for these pulls carries that status.
Nothing in this directory changes that finding either way — it is flagged,
not acted on.

## 2018-2022 + H1-2026 holdout intake (rule-22 data intake)

`scripts/fetch_pjm_as.py` fetches four PJM DataMiner2 feeds directly (same
`api.pjm.com/api/v1` REST endpoint and public subscription key documented in
`scripts/fetch_pjm_energy_offers.py` — PJM's own key, published in the
DataMiner2 site's `settings.json`, not a secret):

- `reserve_market_results` (RT) / `ancillary_services` (RT) — retention
  verified live (each feed's own `/metadata` response) back to **2013-06-14**
  and **2012-10-01** respectively, so 2018-2022 land as full calendar years
  and H1-2026 lands Jan 1 - Jun 30 only (per the intake authorization —
  the fetcher hard-caps at 2026-06-30 and never requests further).
- `da_reserve_market_results` (DA) / `da_ancillary_services` (DA) — retention
  verified live to start **2022-10-01 only**. This is PJM's Reserve Price
  Formation market redesign (new DA reserve products went live mid-2022), not
  a retention window — 2018-2021 genuinely do not exist for these two feeds,
  so the fetcher writes nothing for those years (never an empty/fabricated
  file). 2022 is fetched Oct-Dec only.

**Partial-year naming:** any year whose fetched window is not the full
calendar year (the 2022 DA retention floor, or the H1-2026 scope cap) is
written as `<feed>_<year>_partial.parquet`, never under the plain
`<feed>_<year>.parquet` name — see `fetch_pjm_as.py`'s module docstring for
why (it keeps `build_pjm_as_withholding.py`'s plain-name lookup from ever
picking up a partial year and building/crashing on a fabricated full-year
series). `build_pjm_as_withholding.py --year 2018 2019 2020 2021 2022` builds
the derived withholding series for the five new full years; H1-2026 is
deliberately not buildable there.

Regeneration (still manual for 2023-2025; scripted for 2018-2022 + H1-2026):

    python scripts/fetch_pjm_as.py --years 2018 2019 2020 2021 2022 --h1-2026

This is data intake only (CLAUDE.md rule 22), authorized 2026-07-10; it never
solves or scores a dispatch, and it does not touch the calibration-complete
marker or any dashboard registry.

**Consumers:** `scripts/curate_ancillary_services.py`,
`scripts/build_pjm_as_withholding.py`, `scripts/derive_pjm_ordc_overlay.py`.

## Reference PDFs — payload gitignored (BLOAT-B-2)

The **5 PDFs** in this directory (17.2 MiB) are **gitignored and no longer
tracked at tip** — corpus conversion per `docs/bloat-removal-plan-2026-08.md`
§4.5 item B5 (class-approved under release-plan §6 decision 4). Only
`SHA256SUMS.txt` (scoped to these 5 files) records them. **The `.parquet` data
in this directory is untouched and stays tracked** — `results/scarcity.py`,
`data/fleet/withholding.py` and `build_pjm_as_withholding.py` read those, never
the PDFs. Re-verified by fresh grep at `315a245` (2026-08-15): no consumer in
`src/`, `scripts/` or `tests/` opens any PDF here.

| File | Document | Source URL | Byte-exact today? |
|---|---|---|---|
| `m11.pdf` | PJM Manual 11 — *current* revision at intake | <https://www.pjm.com/-/media/DotCom/documents/manuals/m11.pdf> | **No** — living URL, see below |
| `m11v127-energy-and-ancillary-services-market-operations-11-15-2023.pdf` | Manual 11 rev. 127, eff. 2023-11-15 | <https://www.pjm.com/-/media/documents/manuals/archive/m11/m11v127-energy-and-ancillary-services-market-operations-11-15-2023.pdf> | Yes |
| `m11v129-energy-and-ancillary-services-market-operations-02-22-2024.pdf` | Manual 11 rev. 129, eff. 2024-02-22 | <https://www.pjm.com/-/media/documents/manuals/archive/m11/m11v129-energy-and-ancillary-services-market-operations-02-22-2024.pdf> | Yes |
| `shortage-pricing-fact-sheet.pdf` | PJM Shortage Pricing fact sheet | <https://www.pjm.com/-/media/DotCom/about-pjm/newsroom/fact-sheets/shortage-pricing-fact-sheet.pdf> | Yes |
| `E-3-052120.pdf` | **FERC** order 171 FERC ¶ 61,153 (2020-05-21), PJM reserve price formation | <https://www.ferc.gov/sites/default/files/2020-06/E-3-052120.pdf> | Yes |

Verified 2026-08-15 by fetching each URL and comparing `Content-Length` to
`SHA256SUMS.txt`. Two notes worth keeping:

- **`E-3-052120.pdf` is a FERC document, not a PJM one** — it is the
  Commission's May-2020 order on PJM reserve price formation. Every plausible
  `pjm.com` path for it returns PJM's 24,827-byte soft-404 page, which is how
  this was mis-filed as a PJM manual in the first place.
- **`m11.pdf` is the only payload here that is not byte-reproducible.** It was
  saved from the *living* "current revision" URL, which PJM overwrites on every
  manual revision; that URL served 6,855,912 B on 2026-08-15 against the
  committed snapshot's 6,854,614 B. Route 1 below is the byte-exact recovery.
  Dated revisions live under
  `https://www.pjm.com/-/media/documents/manuals/archive/m11/m11v<NNN>-energy-and-ancillary-services-market-operations-<MM-DD-YYYY>.pdf`
  (the pattern the two archived revisions above use).

### Recovery / re-fetch

1. **Restore from git history — exact bytes, always available.** History is
   kept (no rewrite):

   ```
   git restore --source=315a24524a851566c3d32cc88668fa32dcbd1d74 -- data/raw/PJM-AS
   ```

   **Pin sha `315a24524a851566c3d32cc88668fa32dcbd1d74`** — the last commit at
   which these PDFs were tracked (origin/main, 2026-08-15).

2. **Re-fetch from the publishers.** Run from this directory:

   ```
   xargs -n1 curl -fLO <<'URLS'
   https://www.pjm.com/-/media/DotCom/documents/manuals/m11.pdf
   https://www.pjm.com/-/media/documents/manuals/archive/m11/m11v127-energy-and-ancillary-services-market-operations-11-15-2023.pdf
   https://www.pjm.com/-/media/documents/manuals/archive/m11/m11v129-energy-and-ancillary-services-market-operations-02-22-2024.pdf
   https://www.pjm.com/-/media/DotCom/about-pjm/newsroom/fact-sheets/shortage-pricing-fact-sheet.pdf
   https://www.ferc.gov/sites/default/files/2020-06/E-3-052120.pdf
   URLS
   sha256sum -c <(awk '$1 !~ /^#/ && NF>=3 {s=$1; $1=$2=""; sub(/^ +/,""); print s "  " $0}' SHA256SUMS.txt)
   ```

   Expect `m11.pdf` to FAIL that check — that is the living-URL drift above,
   not a corrupted download.
