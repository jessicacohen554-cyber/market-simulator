# `spp-or-mcp` — SOURCES

Every URL below was probed on **2026-09-06** by lane SPP-12. None returned data;
each is a manual-manifest row until a Marketplace credential exists. No value in
this directory or its README was taken from memory.

## Host

`portal.spp.org` (`marketplace.spp.org` 302-redirects to it — verified).

### `da-mcp` — MCP (Day-Ahead)

- **Landing page:** <https://portal.spp.org/pages/da-mcp>
- **Listing:** `GET https://portal.spp.org/file-browser-api/?fsName=da-mcp&path=<path>&type=folder`
  (`path` percent-encoded; `path=` empty is the root; the trailing slash on
  `file-browser-api/` is part of the route)
- **Download:** `GET https://portal.spp.org/file-browser-api/download/da-mcp?path=<path>`
- **Header required:** `X-SPP-UI-Token: <Marketplace UI token>` — **this repo has none**
- **Probed 2026-09-06:** listing HTTP **200** `[]` · download HTTP **404** · `isPublic` **true**

### `rtbm-mcp` — MCP (Real-Time)

- **Landing page:** <https://portal.spp.org/pages/rtbm-mcp>
- **Listing:** `GET https://portal.spp.org/file-browser-api/?fsName=rtbm-mcp&path=<path>&type=folder`
  (`path` percent-encoded; `path=` empty is the root; the trailing slash on
  `file-browser-api/` is part of the route)
- **Download:** `GET https://portal.spp.org/file-browser-api/download/rtbm-mcp?path=<path>`
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

## Appended 2026-09-06 by lane SPP-13 — the FTP route

- **FTP folders (PRD):** `ftp://pubftp.spp.org/Markets/DA/MCP/` · `ftp://pubftp.spp.org/Markets/RTBM/MCP/` — from `SPP Markets Public Data Guide v35` (`data/raw/spp-planning/SPP_Markets_Public_Data_Guide_v35.docx`); host from `SPP Public Data Access` v3.0 p. 2. Credential `anonymous` / email. **Probed 2026-09-06: egress-blocked** (`data/raw/spp-planning/README.md` §6).
- Schema source: the v35 zip's `DA-MCP-202601300100.csv`, `RTBM-MCP-DAILY-20260123.csv`, `RTBM-MCP-202601291620.csv` samples (not landed).


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

### Landed by SPP-14 (row 9 — DA MCP 2023 and 2024)

| File | Portal path (`fsName=da-mcp`) | Bytes |
|---|---|---|
| `da-mcp-2023.zip` | `/2023/2023.zip` | 418,589 |
| `da-mcp-2024.zip` | `/2024/2024.zip` | 417,669 |

**RTBM MCP is reachable on the same route and deliberately NOT landed here:**
`fsName=rtbm-mcp`, `/2023/2023.zip` = 47,156,480 B and `/2024/2024.zip` =
47,605,298 B — ~141 MB for the three years, which is a pack this lane will not push
for a row the plan scopes to SPP-56 alone. Fetch it when SPP-56 needs it:
`python scripts/data/fetch_spp_alt_portal.py --product rtbm-mcp --years 2023 2024`.
2025 is served per-month at `/2025/<MM>/` (plus a `2025AnnualRollup` folder) for both
products, not as a year zip.
## Appended 2026-09-06 by lane SPP-14 — the portal route is OPEN; 2023–2025 MCPs landed

- `https://portal.spp.org/file-browser-api/download/rtbm-mcp?path=%2F2023%2F2023.zip` (47,156,480 B), `…%2F2024%2F2024.zip` (47,605,298 B): only the `RTBM_MCP_<yr>.csv.zip` annual-roll-up member landed. `…?path=%2F2025%2F2025AnnualRollup%2FRTBM_MCP_2025.csv.zip` (3,255,073 B).
- `https://portal.spp.org/file-browser-api/download/da-mcp?path=%2F2023%2F2023.zip` (418,589 B), `…%2F2024%2F2024.zip` (417,669 B) landed whole; `…?path=%2F2025%2F<mm>%2FDA-MCP-2025MMDD0100.csv` ×365 landed under `da-mcp-2025/`.
- Producer: `scripts/data/fetch_spp_alt_portal.py --only or-mcp`. Checksums: `SHA256SUMS.txt` (new).

## Appended 2026-09-25 by lane SPP-80 — RTBM and DA MCPs 2019–2022 (landed)

- RTBM: `https://portal.spp.org/file-browser-api/download/rtbm-mcp?path=%2F<yr>%2F<yr>.zip`
  (2019 39,487,625 B · 2020 39,836,815 B · 2021 40,240,738 B · 2022 45,111,097 B); only the
  `<yr>/<yr>AnnualRollup/RTBM_MCP_<yr>.csv.zip` member landed (2,768,789 / 2,796,437 /
  2,787,862 / 2,413,800 B), range-read as SPP-14 did for 2023–2024. The 2022 roll-up folder
  also carries two half-year files (`RTBM_MCP_2022-0101-0517.csv.zip`,
  `RTBM_MCP_2022-0518-1231csv.zip`); the full-year `RTBM_MCP_2022.csv.zip` spans
  2022-01-01 06:05Z → 2023-01-01 06:00Z (521,825 rows) and is the one landed.
- DA: `https://portal.spp.org/file-browser-api/download/da-mcp?path=%2F<yr>%2F<yr>.zip`, landed
  whole as `da-mcp-<yr>.zip` (364,665 / 386,866 / 463,733 / 418,932 B), same convention as 2023–24.
- **Schema drift across the span (measured, not assumed):** 2019–2021 carry
  `RegUPService, RegDNService, RegUpMile, RegDNMile, Spin, Supp`; 2022 adds `RAMPUP, RAMPDN`
  (upper-case headers); 2023 adds `UncUP` and a system-wide `SPP` reserve zone alongside 1–5.
  First non-zero RT ramp-up MCP 2022-03-01 (the SOM-stated launch date); first non-zero
  uncertainty MCP 2023-10-09 (product implemented 2023-07-06, 2023 SOM PDF p.120).
- Checksums appended to `SHA256SUMS.txt`. Producer and use as in the binding-constraint row.
