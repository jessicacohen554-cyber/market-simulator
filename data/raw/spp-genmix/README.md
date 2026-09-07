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

**Landed:** `GenMix_2023.csv`, `GenMix_2024.csv`, `GenMix_2025.csv` — SPP's own
complete 5-minute generation-mix files, 105,120 / 105,408 / 105,120 rows, i.e.
365x288 / 366x288 / 365x288 intervals with **no missing slot in any year**. Row 7 of
the manifest is **fully served for 2023-2025**.

They **supersede** the two v35-sample files (`GenMix_2024_SPP.csv` starting 2024-02-15
with 14.4 % of slots missing; `GenMixYTD_SPP.csv` missing 10.8 % and stopping
2025-12-16) under rule 14 `[R-ACCURATE]`. The sample files are left in place because
they are lane SPP-13's payloads and deleting another lane's files is outside SPP-14's
regions — **routed to SPP-DESK** as a prune. Values are MW, not percentages.
---

## STATUS UPDATE 2026-09-06 — lane SPP-14: the ROOT-LEVEL yearly files 2023–2025 LANDED from SPP's own portal (row 7 SERVED, with a discrepancy stated)

FINDING: `docs/handoffs/FINDING-spp-14-2026-09-06.md`. **Route (measured 2026-09-06 by SPP-14):** `https://portal.spp.org/file-browser-api/download/<fsName>?path=<p>` and the `?fsName=<fs>&path=<p>&type=folder` listing — **serving data to an anonymous caller again**, no `X-SPP-UI-Token`, no cookie, no User-Agent dependence (curl default, `python-requests/2.32.3`, an empty UA and a Chrome UA all return the same bytes). The `200 []` / `404` SPP-12 and SPP-13 measured earlier the same day did not reproduce; the FTP route (port 21) stays egress-blocked and was not needed. Producer: `scripts/data/fetch_spp_alt_portal.py` (re-fetches every file below; verify against `SHA256SUMS.txt`). Payloads are SPP's own files, byte-for-byte as served (the `data/raw/` contract).

| File | Source path | Span | Rows | Header |
|---|---|---|---:|---|
| `GenMix_2023.csv` | `generation-mix-historical /GenMix_2023.csv` | 2023-01-01T06:05Z → 2024-01-01T06:00Z | 105,120 | `GMT MKT Interval, Coal Market, Coal Self, Diesel Fuel Oil Market, Diesel Fuel Oil Self, Hydro Market, Hydro Self, Natural Gas Market, Gas Self, Nuclear Market, Nuclear Self, Solar Market, Solar Self, Waste Disposal Services Market, Waste Disposal Services Self, Wind Market, Wind Self, Waste Heat Market, Waste Heat Self, Other Market, Other Self, Load` |
| `GenMix_2024.csv` | `/GenMix_2024.csv` | 2024-01-01T06:05Z → 2025-01-01T06:00Z | 105,408 | same |
| `GenMix_2025.csv` | `/GenMix_2025.csv` | 2025-01-01T06:05Z → 2026-01-01T06:00Z | 105,120 | same (the final 2026-01-01T06:00Z row is empty) |

These are **complete** 5-minute series (12 × 8,760 = 105,120 intervals; 2024 leap = 105,408), where the `SPP/`-sub-folder product SPP-13 landed (`GenMix_2024_SPP.csv`, `GenMixYTD_SPP.csv`) carries 10.8–14.4 % missing intervals and a different header (`GMTTIME, COAL_MKT, …, LOAD`). **They are NOT the same series.** Measured on the 79,103 common 2024 stamps: fuel totals (market + self) agree only loosely — coal corr 0.985 (mean 8,016 vs 8,135 MW), gas 0.986 (9,588 vs 9,764), wind 0.956 (12,725 vs 11,876), load 0.948 (32,855 vs 32,915) — with exact agreement (< 1 MW) at 0–37 % of stamps per fuel, and **no 5/10/60-minute timestamp shift reconciles them** (correlations unchanged under ±5, ±10, +60 min). The market/self split differs most (root coal-self mean 3,611 vs 6,215; gas-market 8,575 vs 3,583). Which of SPP's two publications is the footprint SPP-32 wants is **reported, not decided** here; the root files are the ones the `gridstatus` SPP client (0.36.0) reads as `generation-mix-historical`. The `SPP/` sub-folder also serves `GenMix365_SPP.csv` (18.1 MB) and `GenMixYTD_SPP.csv` (12.3 MB, newer than the landed one) and a `SWPW/` sibling for the WEIS BAA — not landed. Stamps are UTC (`Z`), values MW (guide p. 18). Licence: SPP Terms \& Conditions (<https://www.spp.org/terms-conditions/>, read 2026-09-06), verbatim: *"Permission is implicitly granted to copy and distribute (via computer network or printed form) in whole or in part (with appropriate citation) EXCEPT when such materials will be used, in whole or in part, within a commercial publication (printed or otherwise) or when the author(s) or SPP will be quoted in commercial materials, forums or publications. Any commercial use of these materials requires prior, express written authorization from the author(s) or a duly authorized officer of SPP."*


---

## MERGE RECONCILIATION 2026-09-06 — BOTH SPP-14 landings are in this directory

The two SPP-14 status sections above were written by **two parallel sessions of the same
lane**, each describing only its own landing, and both landings are now present. Neither
section is wrong; each is partial. What this directory actually holds is the union, and the
file listing beside this README is the authority — not either section's "Landed:" line.

`SHA256SUMS.txt` beside this file was regenerated over the **merged** directory, so it covers
every file here, from either landing.
