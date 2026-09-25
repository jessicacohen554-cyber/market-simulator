# `spp-or-mcp` — SPP operating-reserve marginal clearing prices

Opened **2026-09-06** by lane **SPP-12** (`docs/multi-iso/spp-addition-plan-2026-09.md`
§5 row SPP-12) as part of the SPP addition program. Source of record:
`SOURCES.md` beside this file.

## What this is

Manifest row 9 — **SPP-56 input only**. Card **P4** defers reserve
co-optimisation: M2 is last in the playbook order, and MISO's co-opt was inert at
its zone count, so SPP must prove non-inertness on its own data (rule 25
`[R-ISO-SCOPE]` — no verdict transfers between ISOs). These are the measured
per-Reserve-Zone clearing prices that a later SPP co-optimisation lever would be
validated against; nothing in the first keeper reads them.

The offer caps that bound these prices are already transcribed and do not depend
on this directory — see `spp-planning/transcriptions/` (Contingency Reserve Offer
Cap $100/MW, Regulation-Up/Down $500/MW, Uncertainty Reserve $1000/MW).

## SPP product(s)

| `fsName` | SPP page title | SPP's own description |
|---|---|---|
| `da-mcp` | MCP (Day-Ahead) | Provides Marginal Clearing Price information by Reserve Zone for each Day-Ahead Market solution for each Operating Day. Posting is updated each day after the DA Market results are posted. |
| `rtbm-mcp` | MCP (Real-Time) | Provides Marginal Clearing Price information by Reserve Zone for each Real-Time Balancing Market solution for each Operating Interval. Posting is updated after each study completes, roughly 5 minutes prior to the end of the operating interval. |

The descriptions are quoted from SPP's page metadata
(`GET https://portal.spp.org/api/pageConfig/by-slug/<slug>`, read 2026-09-06) —
they are SPP's words, not this repo's summary of the product.

## Expected schema and span

Expected shape: one row per Reserve Zone per market solution with the marginal
clearing price by reserve product (regulation-up, regulation-down, spinning,
supplemental, uncertainty). SPP's Reserve Zones are its own construct and will
need a crosswalk onto whatever zones card P1 registers.

## Timezone

SPP operates on **Central Prevailing Time** (`America/Chicago`) — the model's
dispatch clock for this ISO, and the same convention
`scripts/data/fetch_eia930_hourly.py` and `convert_eia930.py` already use for the
`SWPP` BA. SPP's monthly hourly rollups are published hour-ending `HE01..HE24` on
the local clock with the DST 23/25-hour days pre-folded into 24 columns; the
5-minute interval products are stamped in local time. Confirm against the first
delivered file rather than assuming.

## STATUS AT OPENING — EMPTY, PORTAL BLOCKED (2026-09-06)

**This directory carries no data files yet.** SPP's public file-browser stopped
serving data to anonymous callers; lane SPP-12 re-discovered the API from the
portal's own JS bundle and confirmed the request grammar is correct and the
product is still flagged public, but the response carries nothing.

Measured 2026-09-06 (details, and the full reachable/blocked table:
`docs/handoffs/FINDING-spp-12-2026-09-06.md`):

| Call | Result |
|---|---|
| `GET /file-browser-api/?fsName={fs}&path=&type=folder` | HTTP **200** with a literal `[]`, at every `path`/`type` form tried |
| `GET /file-browser-api/download/{fs}?path=...` | HTTP **404**, zero bytes |
| `GET /api/pageConfig/by-slug/{slug}` | HTTP 200, `isPublic: true` — the product is still declared public |
| `GET /api/principal` | `unauthenticatedUser: true`, `uiTokenPresent: false` |

The responses are SPP's own Tomcat (`JSESSIONID` + Spring-Security headers), not
an intermediary, and an invented `fsName` **404s** where a real one **200s** — so
the `200`-with-`[]` is an authorization outcome, not a wrong key. Both calls now
carry an `X-SPP-UI-Token` header in the SPA; this repo has no Marketplace
credential to populate it.

**How to fill this directory when a credential exists.** Re-read the current
endpoint form from the portal bundle first (`https://portal.spp.org/static/js/main.<hash>.js`
— the hash changes; `e2bac944` on 2026-09-06) rather than trusting this file, then
list and download per `SOURCES.md`. SPP's own **"SPP Public Data Access"** guide
(Stakeholder Center > User Guides, APIs & Integrations > Technical Reference
Documents > Public Data) documents both the Portal and an **FTP** route to these
same products; the FTP route has not been tried and may not need the UI token.

**Raw files land here untouched** — exactly as downloaded, never edited in place
(the `data/raw/` contract). Record the observed schema, span and timezone in the
table above this line when the first files land.


---

## STATUS UPDATE 2026-09-06 — lane SPP-13: FTP route documented (anonymous), egress-blocked; schema verified from SPP's own samples

FINDING: `docs/handoffs/FINDING-spp-13-2026-09-06.md`. Route reference and probe log:
`data/raw/spp-planning/README.md` §6.

**Route.** `ftp://pubftp.spp.org/Markets/DA/MCP/` and `ftp://pubftp.spp.org/Markets/RTBM/MCP/`,
anonymous (user `anonymous`, password = an email address — *Markets Public Data Guide v35*).
Grammar: `DA-MCP-YYYYMMDDHHMM.csv` (daily file, hourly rows); `RTBM-MCP-YYYYMMDDHHMM.csv`
(5-min), `RTBM-MCP-DAILY-YYYYMMDD.csv`, `RTBM_MCP_YYYY.csv` (annual, zipped). **Egress-blocked
from this session** — this directory still carries no data.

**Schema — VERIFIED from the v35 samples** (one day / one interval, NOT landed):

| File | Header (verbatim) |
|---|---|
| `DA-MCP-202601300100.csv` (192 rows = 24 h × 8 reserve zones) | `Interval,GMTIntervalEnd,Reserve Zone,RegUP,RegDN,Spin,Supp,RampUP,RampDN,UncUP` |
| `RTBM-MCP-DAILY-20260123.csv` (2,304 rows = 288 × 8) | `Interval,GMTIntervalEnd,Reserve Zone,RegUPService,RegDNService,RegUpMile, RegDNMile,RampUP,RampDN,Spin,Supp,UncUP` |
| `RTBM-MCP-202601291620.csv` (8 rows) | same + trailing `BAA` column |

`Reserve Zone` is `1`…`7` plus `SWPW` (the Western BAA as its own zone); `Interval` is local
Central time, `GMTIntervalEnd` UTC. Prices are $/MW at 4-decimal precision; the sample
interval shows `Spin` = `Supp` = 0 with `RegUPService` 142.65, which is the ordinary SPP
pattern of contingency-reserve prices sitting at zero outside shortage — the SPP-56 question
is how often they do not.


---

## STATUS UPDATE 2026-09-06 (lane SPP-14) — THE PORTAL ROUTE IS OPEN; THIS DIRECTORY IS SERVED

The "portal blocked" status above is **superseded**. `portal.spp.org`'s file-browser
download and listing calls both answer **anonymously over plain HTTPS** — no
`X-SPP-UI-Token`, no cookie, no FTP — and honour `Range`. What SPP-12 measured were
two path-shape artifacts, not an authorization wall: the download route serves
*files* (a folder path 404s correctly), and the listing returns `[]` only for
`path=` **empty**, the SPA's own first call, while `path=%2F` returns the real
directory array. The corroborating witness is the open-source `gridstatus` client,
which reads these same URLs with a bare `pandas.read_csv(url)` and carries no
credential at all. Full route table, the licence position and the whole alternative-
source sweep: `SOURCES.md` beside this file, `data/raw/spp-lmp-alt/SOURCES.md`, and
`docs/handoffs/FINDING-spp-14-2026-09-06.md`.

**Do not re-derive the access route from the "how to fill this directory" paragraph
above** — it is kept as the incident record, not as instructions.

**Landed:** `da-mcp-2023.zip`, `da-mcp-2024.zip` (418,589 / 417,669 B). **RTBM MCP is
reachable on the same route and deliberately not landed** — ~47 MB per year, ~141 MB
for the span, which is not a pack this lane pushes for a row scoped to SPP-56 alone:
`python scripts/data/fetch_spp_alt_portal.py --product rtbm-mcp --years 2023 2024`.
2025 is served per-month for both products.
---

## STATUS UPDATE 2026-09-06 — lane SPP-14: 2023–2025 LANDED from SPP's own portal (row 9 SERVED)

FINDING: `docs/handoffs/FINDING-spp-14-2026-09-06.md`. **Route (measured 2026-09-06 by SPP-14):** `https://portal.spp.org/file-browser-api/download/<fsName>?path=<p>` and the `?fsName=<fs>&path=<p>&type=folder` listing — **serving data to an anonymous caller again**, no `X-SPP-UI-Token`, no cookie, no User-Agent dependence (curl default, `python-requests/2.32.3`, an empty UA and a Chrome UA all return the same bytes). The `200 []` / `404` SPP-12 and SPP-13 measured earlier the same day did not reproduce; the FTP route (port 21) stays egress-blocked and was not needed. Producer: `scripts/data/fetch_spp_alt_portal.py` (re-fetches every file below; verify against `SHA256SUMS.txt`). Payloads are SPP's own files, byte-for-byte as served (the `data/raw/` contract).

| File(s) | Source path on the portal | Content |
|---|---|---|
| `RTBM_MCP_2023.csv.zip`, `RTBM_MCP_2024.csv.zip` | member `<yr>/<yr>AnnualRollup/RTBM_MCP_<yr>.csv.zip` of `rtbm-mcp /<yr>/<yr>.zip` (the 104k five-minute `RTBM-MCP-*.csv` members are NOT landed) | SPP's own annual roll-up of the 5-minute RTBM MCPs: 630,720 rows (2023) / 632,448 (2024, leap) = 105,120 (105,408) intervals × 6 rows (reserve zones `1`…`5` + `SPP`). Header 2023: `Interval,GMTIntervalEnd,Reserve Zone,RegUPService,RegDNService,RegUpMile, RegDNMile,RampUP,RampDN,Spin,Supp`; 2024 adds `UncUP` (the uncertainty product) |
| `RTBM_MCP_2025.csv.zip` | `rtbm-mcp /2025/2025AnnualRollup/RTBM_MCP_2025.csv.zip` | 630,720 rows, same 12-column 2024 header |
| `DA-MCP-2023.zip`, `DA-MCP-2024.zip` | `da-mcp /<yr>/<yr>.zip` (whole archive, 0.4 MB each) | 365 daily `DA-MCP-YYYYMMDD0100.csv` (one operating day of hourly rows × reserve zones); header `Interval,GMTIntervalEnd,Reserve Zone,RegUP,RegDN,Spin,Supp,RampUP,RampDN` |
| `da-mcp-2025/DA-MCP-2025MMDD0100.csv` ×365 | `da-mcp /2025/<mm>/DA-MCP-2025MMDD0100.csv` (no 2025 archive exists yet — SPP zips a year after ~2 years) | 13 KB each, same header as 2024 (`UncUP` where present) |

**Timezone confirmed on the files:** `Interval` is Central Prevailing Time, `GMTIntervalEnd` UTC (6 h ahead in January). Reserve zones are SPP's numbered reserve zones (`RESZONE` in `../spp-planning/SL_to_Pnode_to_Zone_with_Area.csv`) plus the `SPP` system row. Licence: SPP Terms \& Conditions (<https://www.spp.org/terms-conditions/>, read 2026-09-06), verbatim: *"Permission is implicitly granted to copy and distribute (via computer network or printed form) in whole or in part (with appropriate citation) EXCEPT when such materials will be used, in whole or in part, within a commercial publication (printed or otherwise) or when the author(s) or SPP will be quoted in commercial materials, forums or publications. Any commercial use of these materials requires prior, express written authorization from the author(s) or a duly authorized officer of SPP."*


---

## MERGE RECONCILIATION 2026-09-06 — BOTH SPP-14 landings are in this directory

The two SPP-14 status sections above were written by **two parallel sessions of the same
lane**, each describing only its own landing, and both landings are now present. Neither
section is wrong; each is partial. What this directory actually holds is the union, and the
file listing beside this README is the authority — not either section's "Landed:" line.

`SHA256SUMS.txt` beside this file was regenerated over the **merged** directory, so it covers
every file here, from either landing.

## Span extended to 2019 — lane SPP-80, 2026-09-25

The RTBM and DA operating-reserve MCP roll-ups for **2019, 2020, 2021 and 2022** are now landed beside 2023–2025, fetched over the same anonymous portal route, unmodified. URLs, member names, byte counts and the measured schema drift are in `SOURCES.md` (SPP-80 appendix), and sha256 values are in `SHA256SUMS.txt`. Use: `docs/handoffs/FINDING-spp-80-upper-tercile-premium-2026-09-25.md`.
