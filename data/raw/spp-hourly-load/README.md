# `spp-hourly-load` — SPP hourly load by area

Opened **2026-09-06** by lane **SPP-12** (`docs/multi-iso/spp-addition-plan-2026-09.md`
§5 row SPP-12) as part of the SPP addition program. Source of record:
`SOURCES.md` beside this file.

## What this is

This is the **zonal load** input for an SPP backcast (manifest row 6,
`docs/multi-iso/spp-addition-plan-2026-09.md` §6). It is the ISO-published
counterpart to the EIA-930 sub-BA demand that lane SPP-11 fetches: where the
sub-BA product gives ~17 EIA-defined sub-balancing areas, this product gives
SPP's own Balancing Area / legacy Control Area rollup, which is the boundary
SPP's own market reports use. Whichever of the two is used, the other is the
cross-check — and per rule 14 `[R-ACCURATE]` a disagreement between them is a
finding to root-cause, never a reason to pick the one that fits better.

## SPP product(s)

| `fsName` | SPP page title | SPP's own description |
|---|---|---|
| `hourly-load` | Hourly Load | Historical load data rolled up at an hourly level and grouped by Balancing Area Name and Control Area (legacy BA). |

The descriptions are quoted from SPP's page metadata
(`GET https://portal.spp.org/api/pageConfig/by-slug/<slug>`, read 2026-09-06) —
they are SPP's words, not this repo's summary of the product.

## Expected schema and span

Expected shape (from SPP's product description above — **not** yet verified
against a delivered file): one row per hour per area, columns for the interval
stamp, Balancing Area Name, Control Area, and MW. Span on the portal is a rolling
window with archived years as `/<year>/<year>.zip`; the backcast needs
**2023-2025**, and 2019-2022 only as a rule-22 intake batch after a `complete`
marker.

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

## STATUS UPDATE 2026-09-06 — lane SPP-13: FTP route documented (anonymous), egress-blocked; schema verified; monthly peak file landed

FINDING: `docs/handoffs/FINDING-spp-13-2026-09-06.md`. Route reference and probe log:
`data/raw/spp-planning/README.md` §6.

**Route.** `ftp://pubftp.spp.org/Operational_Data/HourlyLoad/`, anonymous (user `anonymous`,
password = an email address — *Markets Public Data Guide v35*). Guide p. 19, verbatim:
*"Daily files deleted after the monthly roll up file is created. File Name:
DAILY_HOURLY_LOAD-YYYYMMDD.csv … File Name: HOURLY_LOAD-YYYYMM.csv"*. **Egress-blocked from
this session** — the 2023–2025 monthly files remain a manual-manifest row.

**Schema — VERIFIED from SPP's v35 sample `DAILY_HOURLY_LOAD-20260217.csv`** (576 rows,
one day, NOT landed): header `Market Hour,Balancing Area Name,Control Zone Name,Forecast Area
Type,Load MW`; sample row `2/17/2026 7:00,SPP,CSWS,CF,4607.037`. `Balancing Area Name` ∈
{`SPP`, `SWPW`}; `Control Zone Name` is the legacy control area — the same tokens as the
EIA-930 sub-BAs SPP-11 fetched (`CSWS`, `EDE`, `GRDA`, `KACY`, `KCPL`, `LES`, `MPS`, `NPPD`,
`OKGE`, `OPPD`, `SECI`, `SPRM`, `SPS`, `WAUE`, `WFEC`, `WR`, …), which is what makes the two
products cross-checkable at zone level; `Forecast Area Type` ∈ {`CF` conforming, `NC`
non-conforming}. The sample day runs `2/17/2026 7:00` → `2/18/2026 6:00`, i.e. **the `Market
Hour` stamp is UTC** (06:00Z = 00:00 CST) despite the column name — confirm on a summer file
before assuming a fixed 6-hour offset.

**Landed — `Peak_Load_by_Month.csv`** (41 rows), raw from the same v35 zip
(`ftp://pubftp.spp.org/Operational_Data/Peak_Load/`, guide p. 19: *"peak loads in MWs for
every month in each interconnection and includes the interval in which each month's peak
load occurred. Files replaced monthly."*). Header `MKTINTERVAL,LOCALINTERVAL,MONTH,YEAR,INTERCONNECTION,MAX_LOAD`;
span **2024-02 → 2026-01**, `INTERCONNECTION` ∈ {`EAST`, `WEST`}; both a UTC and a local
stamp per row (e.g. `2024-02-16 15:40:00,2024-02-16 09:40:00` — a 6 h offset in February).
Use: a zero-cost check of the model's monthly peak against SPP's own, for 2024–2025 East.


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

**Landed:** `hourly-load-2023.zip`, `hourly-load-2024.zip` — SPP's own yearly
archives of the daily `DAILY_HOURLY_LOAD-YYYYMMDD.csv` files. **2025 is not yet
rolled into a year zip** (SPP zips a year about two years on), so it is served as 365
daily files at `/2025/` and is fetched per-day from the same route when a lane needs
it. SPP changed this product's format on **2026-03-24** (wide -> long); 2023-2025 are
the wide format.
