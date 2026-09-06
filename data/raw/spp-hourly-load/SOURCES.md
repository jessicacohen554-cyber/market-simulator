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

## Appended 2026-09-06 by lane SPP-14 — the portal route is OPEN; 2023–2025 monthly files landed

- `https://portal.spp.org/file-browser-api/download/hourly-load?path=%2F2023%2F2023.zip` (1,443,643 B) and `…%2F2024%2F2024.zip` (1,448,045 B): the 12 `HOURLY_LOAD-YYYYMM.csv` members of each landed; daily members not landed.
- `https://portal.spp.org/file-browser-api/download/hourly-load?path=%2F2025%2FHOURLY_LOAD-2025MM.csv` ×12 (111–124 KB each), fetched 2026-09-06.
- Producer: `scripts/data/fetch_spp_alt_portal.py --only hourly-load`. Checksums: `SHA256SUMS.txt` (new).
- Licence: SPP Terms & Conditions, quoted verbatim in `README.md` (this update) and in `../spp-planning/SOURCES.md`.
