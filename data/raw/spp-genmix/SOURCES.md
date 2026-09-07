# `spp-genmix` — SOURCES

Every URL below was probed on **2026-09-06** by lane SPP-12. None returned data;
each is a manual-manifest row until a Marketplace credential exists. No value in
this directory or its README was taken from memory.

## Host

`portal.spp.org` (`marketplace.spp.org` 302-redirects to it — verified).

### `generation-mix-historical` — Generation Mix Historical

- **Landing page:** <https://portal.spp.org/pages/generation-mix-historical>
- **Listing:** `GET https://portal.spp.org/file-browser-api/?fsName=generation-mix-historical&path=<path>&type=folder`
  (`path` percent-encoded; `path=` empty is the root; the trailing slash on
  `file-browser-api/` is part of the route)
- **Download:** `GET https://portal.spp.org/file-browser-api/download/generation-mix-historical?path=<path>`
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

## Appended 2026-09-06 by lane SPP-13 — the FTP route and the landed sample payloads

- **FTP folder (PRD):** `ftp://pubftp.spp.org/Operational_Data/GEN_MIX/` — from `SPP Markets Public Data Guide v35` (tracked at `data/raw/spp-planning/SPP_Markets_Public_Data_Guide_v35.docx`); host from `SPP Public Data Access` v3.0 p. 2 (`data/raw/spp-planning/SPP_Public_Data_Access_20230707.pdf`). Credential: `anonymous` / email. **Probed 2026-09-06: egress-blocked** (see `data/raw/spp-planning/README.md` §6).
- **`GenMix_2024_SPP.csv`, `GenMixYTD_SPP.csv`:** members of <https://www.spp.org/Documents/75871/SPP%20Markets%20Public%20Data%20Guide%20and%20Samples%20v35.zip> (fetched 2026-09-06, HTTP 200, 82,643,996 bytes, sha256 `e2e8478b…debee7`), copied out byte-for-byte (sha256 in `data/raw/spp-planning/SHA256SUMS.txt`). Zip member timestamps: 2025-12-18 / 2025-12-19.


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

### Landed by SPP-14 (row 7 — COMPLETE 2023-2025, zero missing intervals)

| File | Portal path (`fsName=generation-mix-historical`) | Rows | Span (UTC) |
|---|---|---|---|
| `GenMix_2023.csv` | `/GenMix_2023.csv` | 105,120 | 2023-01-01T06:05Z -> 2024-01-01T06:00Z |
| `GenMix_2024.csv` | `/GenMix_2024.csv` | 105,408 | 2024-01-01T06:05Z -> 2025-01-01T06:00Z (leap) |
| `GenMix_2025.csv` | `/GenMix_2025.csv` | 105,120 | 2025-01-01T06:05Z -> 2026-01-01T06:00Z |

105,120 = 365 x 288 five-minute intervals (105,408 = 366 x 288), so each year is
**complete** — the row count is the arithmetic, not a claim.

**These supersede the two v35-sample files SPP-13 landed**, which are the same
product at a different vintage but are gap-ridden and short:
`GenMix_2024_SPP.csv` starts 2024-02-15 and is missing 14.4 % of its slots;
`GenMixYTD_SPP.csv` (2025) is missing 10.8 % and stops 2025-12-16. Rule 14
`[R-ACCURATE]`: **use the `GenMix_<year>.csv` files above.** The two sample files are
left in place rather than deleted because they are lane SPP-13's landed payloads and
removing another lane's files is outside SPP-14's regions — **routed to SPP-DESK** as a
one-line prune.

Header vintages differ between the two (`GMT MKT Interval, Coal Market, Coal Self, ...`
oldest-first at the portal root vs `GMTTIME,COAL_MKT,COAL_SELF,...` newest-first in the
sample zip); the columns are the same quantities. Values are **MW**, not percentages
(SPP-13 §5 — SPP's page metadata says "percentage" and is wrong). `GenMix_2011.csv`
.. `GenMix_2022.csv` are on the same route for the rule-22 holdout years, unfetched.
## Appended 2026-09-06 by lane SPP-14 — the portal route is OPEN; the root-level yearly files landed

- `https://portal.spp.org/file-browser-api/download/generation-mix-historical?path=%2FGenMix_2023.csv` (16,257,034 B), `…GenMix_2024.csv` (16,432,226 B), `…GenMix_2025.csv` (16,412,421 B), fetched 2026-09-06; the portal root also lists `GenMix_2011.csv` … `GenMix_2022.csv` (not landed — rule-22 data prep for SPP-15 if wanted).
- Producer: `scripts/data/fetch_spp_alt_portal.py --only genmix`. Checksums: `SHA256SUMS.txt` (new; the SPP-13 files stay recorded in `../spp-planning/SHA256SUMS.txt`).
