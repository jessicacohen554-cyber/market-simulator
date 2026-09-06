# `spp-hourly-load` — SOURCES

Every URL below was probed on **2026-09-06** by lane SPP-12. None returned data;
each is a manual-manifest row until a Marketplace credential exists. No value in
this directory or its README was taken from memory.

## Host

`portal.spp.org` (`marketplace.spp.org` 302-redirects to it — verified).

### `hourly-load` — Hourly Load

- **Landing page:** <https://portal.spp.org/pages/hourly-load>
- **Listing:** `GET https://portal.spp.org/file-browser-api/?fsName=hourly-load&path=<path>&type=folder`
  (`path` percent-encoded; `path=` empty is the root; the trailing slash on
  `file-browser-api/` is part of the route)
- **Download:** `GET https://portal.spp.org/file-browser-api/download/hourly-load?path=<path>`
- **Header required:** `X-SPP-UI-Token: <Marketplace UI token>` — **this repo has none**
- **Probed 2026-09-06:** listing HTTP **200** `[]` · download HTTP **404** · `isPublic` **true**

## Authoritative reference for the access route

- **SPP System Interfaces Stakeholder Reference Guide** —
  <https://www.spp.org/media/2598/spp-system-interfaces-stakeholder-reference-guide.pdf>
  (tracked at `data/raw/spp-planning/spp-system-interfaces-stakeholder-reference-guide.pdf`).
  Its **Public Data Specifications** section names the **"SPP Public Data Access"**
  guide — "Reference guide for accessing public data via the SPP Portal **and FTP**" —
  under Stakeholder Center > User Guides, APIs & Integrations > Technical Reference
  Documents > Public Data. The FTP route is **untried** and is the most promising
  unblocked path.

## Blocked / alternative hosts

| Host | Status 2026-09-06 | Note |
|---|---|---|
| `portal.spp.org` file-browser | listings `200 []`, downloads `404` | needs `X-SPP-UI-Token` |
| `marketplace.spp.org` | `302` to `portal.spp.org` | not a separate route |
| `oasis.oati.com/SWPP` | blocked (per plan §2.4) | login required |
| `www.spp.org` | **200, fully reachable** | planning PDFs — see `data/raw/spp-planning/` |

## Appended 2026-09-06 by lane SPP-13 — the FTP route and the landed peak file

- **FTP folders (PRD):** `ftp://pubftp.spp.org/Operational_Data/HourlyLoad/` · `ftp://pubftp.spp.org/Operational_Data/Peak_Load/` — from `SPP Markets Public Data Guide v35` (`data/raw/spp-planning/SPP_Markets_Public_Data_Guide_v35.docx`); host from `SPP Public Data Access` v3.0 p. 2. Credential `anonymous` / email. **Probed 2026-09-06: egress-blocked** (`data/raw/spp-planning/README.md` §6).
- **`Peak_Load_by_Month.csv`:** member of <https://www.spp.org/Documents/75871/SPP%20Markets%20Public%20Data%20Guide%20and%20Samples%20v35.zip> (fetched 2026-09-06; zip sha256 `e2e8478b…debee7`), copied byte-for-byte (sha256 in `data/raw/spp-planning/SHA256SUMS.txt`).
- Schema source for `HOURLY_LOAD-YYYYMM.csv`: the zip's `DAILY_HOURLY_LOAD-20260217.csv` sample (not landed).


## Appended 2026-09-06 by lane SPP-14 — THE PORTAL ROUTE IS OPEN, ANONYMOUS, OVER HTTPS

**This supersedes the "Blocked / alternative hosts" row above for `portal.spp.org`.**
Lane SPP-14 re-probed the portal while sweeping third-party sources and found both
file-browser calls answering anonymously over plain HTTPS — no `X-SPP-UI-Token`, no
cookie, no FTP. The two corrections, each measured 2026-09-06:

| Call | SPP-12 read | SPP-14 measured |
|---|---|---|
| `GET /file-browser-api/download/<fs>?path=<FILE path>` | `404`, zero bytes | **HTTP 200, `text/csv`**, the real file. The 404s were path-shaped: the route serves *files*, so a folder path — or a path that does not exist in that product's archive layout — 404s correctly |
| `GET /file-browser-api/?fsName=<fs>&path=%2F&type=folder` | `200 []` at "every path/type form" | **HTTP 200 with the real JSON directory array.** The literal `[]` reproduces only for `path=` **empty**, which is the SPA's own first call — an empty-path artifact, not authorization |
| `Range:` requests | not tried | **honoured** (`Accept-Ranges: bytes`, `206`), so an archived `<year>/<year>.zip` is read member-by-member without downloading the body |

Corroborating witness: the open-source `gridstatus` package's SPP client reads these
same URLs with a bare `pandas.read_csv(url)` and carries no credential at all
(`gridstatus/spp.py` v0.36.0, sdist read 2026-09-06 from `files.pythonhosted.org`).

**Licence.** SPP states no licence or redistribution restriction on these public
market files; they are published as SPP's public data (guide: `SPP Public Data
Access` v3.0, tracked in `data/raw/spp-planning/`). Landed byte-for-byte, unmodified.

**Producer:** `scripts/data/fetch_spp_alt_portal.py` (rows 6-9);
`scripts/data/build_spp_lmp_reference.py` **runs unmodified** against this route (row 5).

### Landed by SPP-14 (row 6 — 2023 and 2024)

| File | Portal path (`fsName=hourly-load`) | Bytes |
|---|---|---|
| `hourly-load-2023.zip` | `/2023/2023.zip` | 1,443,643 |
| `hourly-load-2024.zip` | `/2024/2024.zip` | 1,448,045 |

SPP rolls a year into `<year>/<year>.zip` about two years on (guide p. 8: *"Public
Data files will be zipped (.zip) after 2 years"*), so **2025 is still served as 365
daily `DAILY_HOURLY_LOAD-YYYYMMDD.csv` files** at `/2025/` (~4.1 KB each) and is not
landed as a single archive here; fetch it per-day from the same route. The
destination name carries the `fsName` because several products publish a bare
`<year>.zip`.

Format note carried from the `gridstatus` client (v0.36.0): SPP changed the hourly-load
file format on **2026-03-24** — wide before, long after. The 2023-2025 files are the
wide format.
