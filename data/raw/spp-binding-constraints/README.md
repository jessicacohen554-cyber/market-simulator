# `spp-binding-constraints` — SPP DA + RTBM binding constraints (flowgates)

Opened **2026-09-06** by lane **SPP-12** (`docs/multi-iso/spp-addition-plan-2026-09.md`
§5 row SPP-12) as part of the SPP addition program. Source of record:
`SOURCES.md` beside this file.

## What this is

Manifest row 8, and **the deciding evidence for owner card P1 (topology)**. The
card asks whether SPP registers as 2 zones (North/South) or 3 (adding the
SPS / Texas-Panhandle pocket), and its stated test is a measured one: the share
of RT binding hours carried by **SPS-tie flowgates** versus the **N-S corridor**
flowgates. The plan's recommendation promotes the SPS pocket to a registered zone
only if the SPS-tie share is at least the N-S share. That number cannot be
computed from anything else in this repo — OASIS (`oasis.oati.com/SWPP`) is
blocked and EIA publishes no flowgate data — so card P1 stays **unserved** on its
own terms until this directory has data.

Second use: the flowgate list and its effective limits are the input SPP-53 needs
for a measured N-S transfer limit, in place of the ITP-transcribed estimate that
rule 14 `[R-ACCURATE]` would otherwise have to carry as a reconciled figure.

## SPP product(s)

| `fsName` | SPP page title | SPP's own description |
|---|---|---|
| `da-binding-constraints` | Binding Constraints (Day-Ahead) | Provides binding constraint information for each Day-Ahead Market solution for each Operating Day. Posting is updated each day after the DA Market results are posted. |
| `rtbm-binding-constraints` | Binding Constraints (Real-Time) | Provides binding constraint information, including effective limits associated with binding constraints, for each Real-Time Balancing Market solution for each Operating Interval. Posting is updated after each study completes, approximately 5 minutes prior to the end of the operating interval. |

The descriptions are quoted from SPP's page metadata
(`GET https://portal.spp.org/api/pageConfig/by-slug/<slug>`, read 2026-09-06) —
they are SPP's words, not this repo's summary of the product.

## The binding-share table this directory owes card P1 (SPP-DESK r#2)

Card P1 was **RULED "2 zones now, two ranked levers"**: both the SPS /
Texas-Panhandle pocket (**SPP-54**) and an Oklahoma pocket (**SPP-57**) are
pre-declared structural levers, and the table below is what **ranks** them. The
grouping is therefore fixed in advance, before any data exists to fit it to —
which is the point: a grouping chosen after seeing the shares would be exactly the
residual-driven selection rule 1 `[R-STRUCT]` forbids.

**Four groups**, and every binding row lands in exactly one:

| Group | Contents |
|---|---|
| `n_s_corridor` | the North↔South corridor flowgates — the interface the 2-zone topology actually models |
| `sps_tie` | SPS / Texas-Panhandle tie flowgates — ranks lever **SPP-54** |
| `oklahoma_internal` | Oklahoma-internal flowgates — **Osage–Webber Tap**, **Russett–South Brown**, and the OKC / Tulsa FCA flowgates — ranks lever **SPP-57** |
| `other` | everything else; reported, never dropped, so the shares sum to 1 |

**Report per year, per group, for the RT (RTBM) market:**

1. **share of RT binding hours** — hours in which at least one flowgate in the
   group binds, over 8760;
2. **mean shadow price** while binding, $/MWh.

Both legs matter and they can disagree: a group that binds often at a low shadow
price is a different object from one that binds rarely and expensively, and a
ranking on hours alone would hide the second. Report both rather than a product of
them.

Provenance of the three named Oklahoma flowgates: the **SPP-DESK r#2 addendum to
SPP-12**, which attributes them to `docs/multi-iso/spp-data-audit.md` §6.1. **That
audit document does not exist in the tree as of 2026-09-06** — SPP-10 has not
landed it — so the names are carried here from the addendum and should be
re-checked against §6.1 once it does. They are a starting list, not a closed one:
the group is "Oklahoma-internal", and the actual membership has to be derived from
the delivered flowgate names, which is a judgement the session with the data
makes and records.

**Status: UNSERVED.** The table cannot be computed — this directory is empty
because the source is blocked (below). Card P1's ranking of SPP-54 vs SPP-57
therefore has **no measured input yet**, and no substitute exists in this repo:
OASIS is blocked, and EIA publishes nothing at flowgate resolution. This is the
single largest gap SPP-12 leaves behind.

What *is* available, and what it can and cannot settle: the SPP MMU publishes the
**North–South hub spread** annually, transcribed to
`data/raw/spp-planning/spp_hub_spread_annual.csv`. That series ranks *years* by
N↔S separation — which is enough to choose a screen year — but it says nothing
about which **flowgates** carry the congestion, so it cannot rank SPP-54 against
SPP-57. Only this directory can.

## Expected schema and span

Expected shape: one row per binding constraint per market solution — DA per
Operating Day, RTBM per Operating Interval (5-minute) — with the constraint /
flowgate name, monitored and contingent elements, shadow price, and (RTBM) the
effective limit. Monthly rollup files are the tractable form; the per-interval
RTBM archive for a full year is large.

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

