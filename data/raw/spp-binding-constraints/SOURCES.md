# `spp-binding-constraints` — SOURCES

Every URL below was probed on **2026-09-06** by lane SPP-12. None returned data;
each is a manual-manifest row until a Marketplace credential exists. No value in
this directory or its README was taken from memory.

## Host

`portal.spp.org` (`marketplace.spp.org` 302-redirects to it — verified).

### `da-binding-constraints` — Binding Constraints (Day-Ahead)

- **Landing page:** <https://portal.spp.org/pages/da-binding-constraints>
- **Listing:** `GET https://portal.spp.org/file-browser-api/?fsName=da-binding-constraints&path=<path>&type=folder`
  (`path` percent-encoded; `path=` empty is the root; the trailing slash on
  `file-browser-api/` is part of the route)
- **Download:** `GET https://portal.spp.org/file-browser-api/download/da-binding-constraints?path=<path>`
- **Header required:** `X-SPP-UI-Token: <Marketplace UI token>` — **this repo has none**
- **Probed 2026-09-06:** listing HTTP **200** `[]` · download HTTP **404** · `isPublic` **true**

### `rtbm-binding-constraints` — Binding Constraints (Real-Time)

- **Landing page:** <https://portal.spp.org/pages/rtbm-binding-constraints>
- **Listing:** `GET https://portal.spp.org/file-browser-api/?fsName=rtbm-binding-constraints&path=<path>&type=folder`
  (`path` percent-encoded; `path=` empty is the root; the trailing slash on
  `file-browser-api/` is part of the route)
- **Download:** `GET https://portal.spp.org/file-browser-api/download/rtbm-binding-constraints?path=<path>`
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

- **Reference:** `SPP Public Data Access` v3.0 (July 2023) — <https://www.spp.org/Documents/28853/SPP%20Public%20Data%20Access%2020230707.pdf>
  (tracked at `data/raw/spp-planning/SPP_Public_Data_Access_20230707.pdf`), p. 2: programmatic access is FTP, `ftp://pubftp.spp.org`.
- **Credential:** `SPP Markets Public Data Guide v35` (tracked as `data/raw/spp-planning/SPP_Markets_Public_Data_Guide_v35.docx`), "FTP Site Access": user `anonymous`, password = an email address.
- **Folders:** `ftp://pubftp.spp.org/Markets/RTBM/BINDING_CONSTRAINTS/` · `ftp://pubftp.spp.org/Markets/DA/BINDING_CONSTRAINTS/` · `ftp://pubftp.spp.org/Markets/DA/Congestion-Constraint`
- **Probed 2026-09-06:** `CONNECT pubftp.spp.org:21` through the session egress → tunnel opens, **no FTP banner within 36 s**, relay closes; identical for control hosts `ftp.gnu.org:21` and `ftp.debian.org:21` → **egress policy blocks FTP**, not SPP. Ports 443/990 reset after ClientHello. `WebFetch`: "Unsupported protocol ftp:".
- **Schema source:** sample files inside <https://www.spp.org/Documents/75871/SPP%20Markets%20Public%20Data%20Guide%20and%20Samples%20v35.zip> (82.6 MB, not tracked; sha256 in `data/raw/spp-planning/SHA256SUMS.txt`).
