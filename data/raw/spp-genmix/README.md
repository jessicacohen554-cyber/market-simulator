# `spp-genmix` — SPP historical generation mix

Opened **2026-09-06** by lane **SPP-12** (`docs/multi-iso/spp-addition-plan-2026-09.md`
§5 row SPP-12) as part of the SPP addition program. Source of record:
`SOURCES.md` beside this file.

## What this is

Manifest row 7. Two uses: (a) a fuel-mix sanity check on the first SPP solve —
card **P7** names "fuel-mix within order of magnitude of EIA-923" as part of the
first-solve structural STOP gate; (b) **delivered wind is the HSL denominator**.
The curtailment rate this program needs is
`curtailed / (delivered + curtailed)`, and this product supplies the `delivered`
leg while `spp-hsl/` supplies the curtailed leg. Without it the curtailment
figures in `spp-hsl/` stay as SPP publishes them (average hourly MW) and any
percentage is a derivation carrying its own arithmetic, not a published rate.

## SPP product(s)

| `fsName` | SPP page title | SPP's own description |
|---|---|---|
| `generation-mix-historical` | Generation Mix Historical | Historical generation mix files showing percentage generation by fuel type. |

The descriptions are quoted from SPP's page metadata
(`GET https://portal.spp.org/api/pageConfig/by-slug/<slug>`, read 2026-09-06) —
they are SPP's words, not this repo's summary of the product.

## Expected schema and span

Expected shape: per-interval or per-hour generation by fuel type, published as
percentages (SPP's description says "percentage generation by fuel type"), so a
MW/MWh denominator may need the load product alongside it. Verify before use —
a percentage series cannot serve as an energy denominator on its own.

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

## STATUS UPDATE 2026-09-06 — lane SPP-13: FTP route documented; TWO real payload files landed from SPP's own sample zip

FINDING: `docs/handoffs/FINDING-spp-13-2026-09-06.md`. Route reference and probe log:
`data/raw/spp-planning/README.md` §6.

**Route.** `ftp://pubftp.spp.org/Operational_Data/GEN_MIX/`, anonymous (user `anonymous`,
password = an email address — *Markets Public Data Guide v35*, "FTP Site Access"). Files:
`GenMix_YYYY_SPP.csv` (one per year), `GenMixYTD_SPP.csv`, `GenMix365_SPP.csv`,
`GenMix2Hour_SPP.csv`, each with a `_SWPW` twin for the Western BAA. **Egress-blocked from
this session** (port-21 tunnels never deliver a banner; same for control FTP hosts) — so the
2023 file and the 2024-01-01..02-14 gap below remain manual-manifest rows.

**Landed — raw, unmodified, from the *SPP Markets Public Data Guide and Samples v35* zip**
(<https://www.spp.org/Documents/75871/…v35.zip>, `www.spp.org`, HTTP 200; the zip's sha256
and the files' own sha256 are in `data/raw/spp-planning/SHA256SUMS.txt`). These are SPP's
published product files shipped as the guide's samples, not synthetic examples:

| File | Rows | Span (`GMTTIME`, UTC) | Cadence | Notes |
|---|---|---|---|---|
| `GenMix_2024_SPP.csv` | 79,103 | **2024-02-15 06:00Z → 2025-01-01 06:00Z** | 5-min (78,163 steps of 5 min; 708 of 10 min; 112 of 15 min — i.e. **13,346 missing 5-min slots**, 14.4 % of the 92,449 the span implies; 0 duplicates) | SPP's own "2024" file starts 15 Feb; Jan 1–Feb 14 2024 is **not in it** |
| `GenMixYTD_SPP.csv` | 89,826 | **2025-01-01 06:00Z → 2025-12-16 21:25Z** | 5-min (87,612 / 1,632 / 231 steps of 5 / 10 / 15 min; 10,872 missing slots, 10.8 %; 0 duplicates) | year-to-date as of the zip build (Dec 2025) |
| `GenMix365_SPP.csv` | 94,089 | 2024-12-16 20:25Z → 2025-12-16 19:30Z | 5-min | **NOT landed** — fully covered by the two above; sha256 recorded |

Schema (verbatim header, 22 columns): `GMTTIME,COAL_MKT,COAL_SELF,DIESEL_FUEL_OIL_MKT,DIESEL_FUEL_SELF,HYDRO_MKT,HYDRO_SELF,NATURAL_GAS_MKT,NATURAL_GAS_SELF,NUCLEAR_MKT,NUCLEAR_SELF,SOLAR_MKT,SOLAR_SELF,WASTE_DISPOSAL_SERVICES_MKT,WASTE_DISPOSAL_SERVICES_SELF,WIND_MKT,WIND_SELF,WASTE_HEAT_MKT,WASTE_HEAT_SELF,OTHER_MKT,OTHER_SELF,LOAD`.
**Values are MW, not percentages** — the "percentage generation by fuel type" wording in
SPP's page metadata (table above) is wrong for the historical files; the guide (p. 18) says
*"MW of generation by fuel type in use. Each fuel type split by market vs. self-commit
status"*, and `LOAD` is the STLF-sourced load (guide: *"source of the data column is
STLF"*). So delivered wind = `WIND_MKT + WIND_SELF` in MW per 5-min interval, which is the
HSL denominator this directory was opened for — **for 2024-02-15 onward only**.

**Timezone confirmed:** the stamp is `GMTTIME` in UTC with a `Z` suffix; the files are
written newest-first. Convert to Central Prevailing Time before any hour-of-day use.
