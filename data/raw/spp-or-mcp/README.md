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
