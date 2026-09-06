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

## Appended 2026-09-06 by lane SPP-14 — the portal route is OPEN; the root-level yearly files landed

- `https://portal.spp.org/file-browser-api/download/generation-mix-historical?path=%2FGenMix_2023.csv` (16,257,034 B), `…GenMix_2024.csv` (16,432,226 B), `…GenMix_2025.csv` (16,412,421 B), fetched 2026-09-06; the portal root also lists `GenMix_2011.csv` … `GenMix_2022.csv` (not landed — rule-22 data prep for SPP-15 if wanted).
- Producer: `scripts/data/fetch_spp_alt_portal.py --only genmix`. Checksums: `SHA256SUMS.txt` (new; the SPP-13 files stay recorded in `../spp-planning/SHA256SUMS.txt`).
