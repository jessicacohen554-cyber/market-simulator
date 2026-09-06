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


---

## STATUS UPDATE 2026-09-06 — lane SPP-13: FTP route documented (anonymous), egress-blocked; schema verified from SPP's own samples

FINDING: `docs/handoffs/FINDING-spp-13-2026-09-06.md`. Route reference and probe log:
`data/raw/spp-planning/README.md` §6.

**Route.** SPP's *Public Data Access* guide (v3.0, July 2023) names the programmatic route:
**`ftp://pubftp.spp.org`**, and the *Markets Public Data Guide v35* states the credential —
**`anonymous` / any email address**. No Marketplace token is needed. Folders (PRD):
`Markets/RTBM/BINDING_CONSTRAINTS/` and `Markets/DA/BINDING_CONSTRAINTS/`; grammar
`RTBM-BC-YYYYMMDDHHMM.csv` (5-min) · `RTBM-DAILY-BC-YYYYMMDD.csv` · `DA-BC-YYYYMMDDHHMM.csv`
(daily, hourly rows) · `DA-BC-MONTHLY-YYYYMM.csv` · `DA-BC-YEARLY-YYYY.zip`, with daily runs
under a `By_Day/` folder inside each month and files older than 2 years zipped. **From this
session the route is transport-blocked** — the egress relays TLS-on-443 only; a port-21
tunnel never delivers a banner, and the same is true for `ftp.gnu.org` / `ftp.debian.org`
(control). The four-group table below therefore stays **UNSERVED**, for a different reason
than SPP-12 recorded: not a credential, a network policy. **This directory still carries no
2023–2025 data.**

**Schema — now VERIFIED from the v35 sample files** (SPP's own publication, dated
2026-01-28/29; the samples are one interval / one day and are NOT landed here):

| File | Header (verbatim) | Notes |
|---|---|---|
| `RTBM-DAILY-BC-20260128.csv` (21,592 rows) | `Interval,GMTIntervalEnd,Constraint Name,Constraint Type,NERCID,TLR Level,State,Shadow Price,Monitored Facility,Contingent Facility,Source Limit,Real Time Effective Limit,Initial Effective Limit,Interconnect` | one row per constraint per 5-min interval; `Interval` is **local Central time**, `GMTIntervalEnd` is UTC (6 h ahead on the sample's January day); `State` ∈ {`BINDING`, `BREACHED`, `ACTIVATED`}; `Constraint Type` ∈ {`FG` flowgate, `WRC`, …}; `Interconnect` ∈ {`E`, `W`} (East = the RTO footprint) |
| `RTBM-BC-202601291600.csv` (87 rows) | same 14 columns | the single-interval file |
| `DA-BC-202601290100.csv` (64 rows) | `Interval,GMTIntervalEnd,Constraint Name,Constraint Type,NERCID,State,Shadow Price,Monitored Facility,Contingent Facility, Contingency Name,Interconnect` | one row per constraint per **hour**, whole operating day in one file; no effective-limit columns |
| `Congestion-Constraint-202512.csv` (381 rows) | `DATE,CONSTRAINTNAME,MONITORED_FACILITY,CONTINGENT_FACILITY,CONTINGENCY_NAME,TOTAL,INTERCONNECT` | **monthly DA congestion dollars by constraint** (`Markets/DA/Congestion-Constraint`) — a tiny complement to the four-group table (dollars, not binding hours) |
| `M2M-Current-Flowgate-List-20260129.csv` (66 rows) | `NERCID, Constraint Name, Monitoring RTO, NON Monitoring RTO` | the M2M seam flowgates (e.g. `FORTIEHANWAH`-class rows) |

Sample rows, verbatim, so the grouping session knows what a flowgate name looks like:
`BEAEURFLIBRO,FG,5218,CME,ACTIVATED,0.0000,LN BEAVER1 - EURK_SPA,CSWS AECI:FLINTCRK BROOK_LN:345:1:,307,297.79,297.79,E` and
`PAOLI2_9404_A_LN,MCE,,BINDING,1492.7777,LN PAOLI2 - LEXNGT2,BASE,BASE,E`. The `Monitored
Facility` string (`LN <from> - <to>`) plus `Contingent Facility` is what maps a row to a
group; the four-group spec above is **unchanged** by this update (rule 1 — fixed before the
data). The `Real Time Effective Limit` column is the measured per-flowgate limit SPP-53 needs.

**Timezone confirmed against the samples:** `Interval` is Central Prevailing Time and
`GMTIntervalEnd` is UTC; the January sample shows the 6-hour (CST) offset.

**Oklahoma group membership — re-checked, as the spec above asked.** `docs/multi-iso/spp-data-audit.md`
§6.1 now exists (SPP-10 landed, PR #5254) and names exactly the two flowgates carried above —
*Osage–Webber Tap 138 kV, northern Oklahoma* (RT avg shadow $75.47/MWh 2025) and
*Russett–South Brown 138 kV, southern Oklahoma* (RT $61/MWh) — plus the 2024 FCAs Oklahoma City
and Tulsa (Lubbock and Kansas City are the other two, and belong to `sps_tie` / `other`
respectively). The starting list stands; nothing was added or removed.

---

## STATUS UPDATE 2026-09-06 — lane SPP-14: RTBM 2023–2025 LANDED from SPP's own portal; the four-group table is SERVED (in the FINDING); the effective-limit column does NOT exist before 2026-01-28

FINDING: `docs/handoffs/FINDING-spp-14-2026-09-06.md` §5 (the table, the membership rules, the sensitivities). **Route (measured 2026-09-06 by SPP-14):** `https://portal.spp.org/file-browser-api/download/<fsName>?path=<p>` and the `?fsName=<fs>&path=<p>&type=folder` listing — **serving data to an anonymous caller again**, no `X-SPP-UI-Token`, no cookie, no User-Agent dependence (curl default, `python-requests/2.32.3`, an empty UA and a Chrome UA all return the same bytes). The `200 []` / `404` SPP-12 and SPP-13 measured earlier the same day did not reproduce; the FTP route (port 21) stays egress-blocked and was not needed. Producer: `scripts/data/fetch_spp_alt_portal.py` (re-fetches every file below; verify against `SHA256SUMS.txt`). Payloads are SPP's own files, byte-for-byte as served (the `data/raw/` contract).

| File(s) | Source path on the portal | Rows | Schema |
|---|---|---:|---|
| `RTBM-BC-YEARLY-2023.csv.zip`, `RTBM-BC-YEARLY-2024.csv.zip` | member `<yr>/RTBM-BC-YEARLY-<yr>.csv.zip` of `rtbm-binding-constraints /<yr>/<yr>.zip` (58.7 / 70.1 MB archives, whose 365 daily + ~285 five-minute members are NOT landed) | 3,680,061 / 4,085,945 | **10 columns**: `Interval,GMTIntervalEnd,Constraint Name,Constraint Type,NERCID,TLR Level,State,Shadow Price,Monitored Facility,Contingent Facility` |
| `RTBM-BC-MONTHLY-2025MM.csv.zip` ×12 | `rtbm-binding-constraints /2025/<mm>/RTBM-BC-MONTHLY-2025MM.csv.zip` | 5,528,453 (year) | same 10 columns |

**The 14-column schema SPP-13 verified from the 2026-01-28 sample is NEW.** Every 2023–2025 roll-up AND every one of the 731 daily files inside the 2023/2024 archives carries the 10-column form; probed daily files 2025-01-15, -06-15, -10-15, -12-15, 2026-01-15, -20, -25, -27 are 10-column and 2026-01-28 / 2026-06-01 are 14-column — so `Source Limit`, `Real Time Effective Limit`, `Initial Effective Limit` and `Interconnect` **begin with the 2026-01-28 daily file**. Consequences: (i) the SPP-53 measured N↔S limit input (`Real Time Effective Limit` per flowgate) is **not obtainable for 2023–2025 from this archive** — it exists only from 2026-01-28 forward; (ii) East/West cannot be filtered by column for 2023–2025; the FINDING's grouping classifies West rows by the contingency's area tokens and reports the remainder.

Coverage per year (all States): 2023 104,610 distinct 5-min intervals, 2024 105,179, 2025 104,821 (a year has 105,120 / 105,408). `State` counts — 2023: ACTIVATED 3,239,886 · BINDING 339,620 · BREACHED 100,555; 2024: 3,577,946 · 387,035 · 120,964; 2025: 5,014,349 · 403,159 · 110,945. `Constraint Type` ∈ {`FG`, `M2M`, `RTCA`}. Timezone confirmed: `Interval` local Central, `GMTIntervalEnd` UTC. `Shadow Price` is **negative** in SPP's convention (the marginal value of relaxing the limit); the FINDING reports `|Shadow Price|`. Licence: SPP Terms \& Conditions (<https://www.spp.org/terms-conditions/>, read 2026-09-06), verbatim: *"Permission is implicitly granted to copy and distribute (via computer network or printed form) in whole or in part (with appropriate citation) EXCEPT when such materials will be used, in whole or in part, within a commercial publication (printed or otherwise) or when the author(s) or SPP will be quoted in commercial materials, forums or publications. Any commercial use of these materials requires prior, express written authorization from the author(s) or a duly authorized officer of SPP."*

**The four-group spec above is UNCHANGED.** The membership RULES the FINDING applied are recorded there (§5.1) and are a judgement of this session: named ITP interfaces `SPPSPSTIES` / `SPSNMTIES` and the Potter County interchange → `sps_tie`; the two named Oklahoma flowgates and contingencies confined to `OKGE/WFEC/GRDA` (with `CSWS` admitted only beside one of them) → `oklahoma_internal`; contingencies touching a Kansas-corridor area `WR/SECI/KCPL/MPS/KACY` (the areas between the Nebraska North hub and the Oklahoma South hub — `SPPNORTH_HUB` = OPPD/NPPD/LES nodes, `SPPSOUTH_HUB` = OKGE/WFEC/CSWS nodes, from `../spp-planning/Hub_Definitions.csv` joined to the SL map) → `n_s_corridor`; everything else → `other`, with its sub-lines reported.
