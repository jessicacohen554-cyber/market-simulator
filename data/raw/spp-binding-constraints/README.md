# `spp-binding-constraints` — SPP DA + RTBM binding constraints (flowgates)

Opened **2026-09-06** by lane **SPP-12** (`docs/multi-iso/spp-addition-plan-2026-09.md`
§5 row SPP-12) as part of the SPP addition program. Source of record:
`SOURCES.md` beside this file.

> ## STATUS CORRECTION — **THE DATA HAS LANDED. THIS DIRECTORY IS SERVED.**
>
> *(Repaired 2026-09-11 by lane **SPP-29**. `FINDING-spp-64-2026-09-10.md` §8 flagged the
> "Status: UNSERVED" lines below as stale; SPP-29 read the archive and repairs them here rather
> than leaving a third lane to rediscover it. The narrative below is left INTACT as the record of
> what SPP-12 and SPP-13 actually found — the two stale status lines are annotated in place, not
> rewritten.)*
>
> Landed: `RTBM-BC-YEARLY-2023.csv.zip` and `RTBM-BC-YEARLY-2024.csv.zip` (3.68 M / 4.09 M
> constraint-intervals), twelve `RTBM-BC-MONTHLY-2025NN.csv.zip`, `Flowgates.csv`,
> `Temp_Flowgate.csv`, and two derived limit parquets. Delivered schema, verified by SPP-29:
> `Interval,GMTIntervalEnd,Constraint Name,Constraint Type,NERCID,TLR Level,State,Shadow Price,
> Monitored Facility,Contingent Facility` — the 10-column yearly form, **without** the three
> effective-limit columns the v35 sample carries. **`Interval` is stamped interval-ENDING local
> Central**, so `00:05:00` belongs to hour 0; a consumer that floors it to the hour without
> accounting for that shifts every row by one interval.
>
> **What is now computable, and one warning about it.** Card P1's SPP-54-vs-SPP-57 ranking is
> computable on its own pre-declared terms — but flowgate group membership **must be fixed in a
> PRECOMMIT before any share is read** (rule 1 `[R-STRUCT]`; deriving membership while looking at
> the shares is residual-driven selection). Two measurements already on the record should be read
> first, because both cut against a zonal split: 2024 congestion rent is spread over **444**
> monitored facilities — 23 for half, **115 for 90 %** (`FINDING-spp-64` §8) — and congestion
> **does not select SPP's price tail at all**: tail hours sit at the 53rd percentile of binding
> count and `spearman(hourly rent, RT hub price) = +0.019`
> (`FINDING-spp-29-c3c-price-tail-2026-09-11.md` §1b).

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

**Status: ~~UNSERVED~~ SERVED as of 2026-09-08 — see the STATUS CORRECTION at the top of this
file. The paragraph below is SPP-12's 2026-09-06 record and is retained as history; its factual
claims about this directory being empty are NO LONGER TRUE.** The table cannot be computed — this
directory is empty because the source is blocked (below). Card P1's ranking of SPP-54 vs SPP-57
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
>
> **SUPERSEDED 2026-09-11 (SPP-29).** The paragraph above is SPP-13's 2026-09-06 transport record
> and is retained as history. The data has since landed by another route (`SOURCES.md`): the
> 2023 and 2024 yearly archives and the twelve 2025 monthlies are in this directory. The
> four-group table is computable, subject to the membership-before-shares discipline named at the
> top of this file.

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

### What SPP-14 measured, and what it did NOT commit

**The four-group table is COMPUTED.** The whole RTBM binding-constraint archive was
pulled and parsed in-session — `/2023/2023.zip` (58.7 MB), `/2024/2024.zip` (70.1 MB),
`/2025/RTBM-BC-YEARLY-2025.csv.zip` (25.0 MB), inflating to 1.68 GB of yearly-rollup
CSV — and the four-group binding-share and shadow-price table for 2023-2025 is in
`docs/handoffs/FINDING-spp-14-2026-09-06.md` §5, with the derived group membership in
§4.1. **Card P1's ranking of SPP-54 vs SPP-57 now has its measured input.**

**The payload is not committed** (charter: the table goes in the FINDING; 154 MB of
zips is not this lane's pack). Git history is the record, per rule 15; the pull is one
command against the route in `SOURCES.md`.

**Landed instead — the two flowgate registries**, which are small, permanent, and are
what makes the group membership measured rather than asserted:

| File | Rows | Carries |
|---|---|---|
| `Flowgates.csv` | 823 | permanent flowgates: `From Area`/`To Area` control-area codes, `Voltage`, seasonal `Normal`/`Emergency` MW ratings, `IROLLimit` |
| `Temp_Flowgate.csv` | 3,298 | the `TMP*`/`TEMP*` temporary constraints that carry most SPP binding: same area codes, `NormLimit`/`EmerLimit`, `CreatedTime` |

**The four groups are UNCHANGED.** They were fixed in this README before any data
existed (rule 1 `[R-STRUCT]`) and SPP-14 changed no group, no definition, and no
ranking test. What this README expressly reserved to "the session with the data" —
*"the actual membership has to be derived from the delivered flowgate names, which is
a judgement the session with the data makes and records"* — is recorded area-code by
area-code in FINDING-spp-14 §4.1. Both Oklahoma flowgates the README names are present
in the delivered data (`LN OSAGE_OG - WEBBTAP4`, `LN RUSSETT - SBROWN`), as is the
`SPSNMTIES` interface SPP-13 §4 named.

### SCHEMA CORRECTION — SPP-53 cannot get its limit from this archive

`FINDING-spp-13` §3 recorded a **14-column** schema including **`Real Time Effective
Limit`**, read from the v35 zip's `RTBM-DAILY-BC-20260128.csv` sample, and concluded
that column was SPP-53's measured N<->S limit input. **The archive SPP serves carries
only 10 columns for the whole calibration span.** Measured 2026-09-06 by fetching the
header of the served file for each date: 2023-06-01, 2024-06-01 (via the yearly
rollups), 2025-06-01, 2025-12-01, 2026-01-28, 2026-03-23 and 2026-03-24 are all **10**
columns; 2026-04-01, -04-08, -04-15, -05-01, -06-01, -07-01, -08-01 and -09-01 are
**14**. The break is the same **2026-03-24** format change the `gridstatus` client
records for hourly load. So:

- **2023-2025 have no effective-limit column at all** — the row-8 archive cannot supply
  SPP-53's measured N<->S limit for the years the model calibrates on;
- from **2026-04** forward it can.

SPP-53 therefore stays on the rule-14 `[R-ACCURATE]` Tier-3 reconciled estimate that
ruling P11 set for SPP-20. The better measured substitute now in the tree is
`Flowgates.csv`'s seasonal `Normal`/`Emergency` MW ratings, which are published, dated
and per-flowgate.
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


---

## MERGE RECONCILIATION 2026-09-06 — BOTH SPP-14 landings are in this directory

The two SPP-14 status sections above were written by **two parallel sessions of the same
lane**, each describing only its own landing, and both landings are now present. Neither
section is wrong; each is partial. What this directory actually holds is the union, and the
file listing beside this README is the authority — not either section's "Landed:" line.

`SHA256SUMS.txt` beside this file was regenerated over the **merged** directory, so it covers
every file here, from either landing.

---

## STATUS UPDATE 2026-09-07 — lane SPP-53: the 2026 corridor-limit sidecar LANDED; the N↔S link TTC is derived (3,400 MW)

FINDING: `docs/handoffs/FINDING-spp-53-2026-09-07.md` (construction fixed first in
`PRECOMMIT-spp-53-2026-09-07.md`). **The four-group spec above and `docs/handoffs/spp14/groups.py`
are UNCHANGED** — the corridor rows below are selected by those rules verbatim.

**Where the effective-limit column actually begins — a correction to both SPP-14 sections above.**
Every one of the 221 daily files `RTBM-DAILY-BC-20260128.csv` → `20260905.csv` was pulled and its
rows counted by field count: the 14-column rows (`Source Limit`, `Real Time Effective Limit`,
`Initial Effective Limit`, `Interconnect`) first appear on **2026-03-17** (a whole 14-column day),
then **2026-03-18 → 03-24 are 10-column again**, **2026-03-25 is MIXED** (9,784 ten-field rows, then
2,419 fourteen-field rows from interval 10:25 local under a 10-column header), **03-26 → 03-31 are
10-column**, and **every day from 2026-04-01 is 14-column**. The `20260128.csv` the portal serves is
10-column (14,501 rows) — the 14-column, 21,592-row file of that name SPP-13 read was the v35 guide's
*sample*, not the served archive. So the measured-limit series runs **2026-03-17 (one day),
2026-03-25 (part), and 2026-04-01 → latest**.

**Landed — the reduced sidecar** (the LMP-sidecar precedent: the 221 daily pulls, ~550 MB, are not
committed; git history + the fetch command are the record):

| File | Rows | Span (`GMTIntervalEnd`, UTC) | Constraints | What it carries |
|---|---:|---|---:|---|
| `rtbm_bc_corridor_limits_2026.parquet` (1,435,141 B) | 563,450 | 2026-03-17 05:05 → 2026-09-06 05:00 (162 days) | 166 | every `State ∈ {BINDING 35,096, BREACHED 4,667, ACTIVATED 523,687}` row of the 14-column daily files whose constraint is `n_s_corridor` under `groups.py`'s rules; columns `Constraint Name`, `Monitored Facility`, `Contingent Facility`, `State`, `Shadow Price`, `Source Limit`, `Real Time Effective Limit`, `Initial Effective Limit`, `Interconnect`, `GMTIntervalEnd` (the 8 the charter named plus `State` and `Shadow Price`, so the binding subset is selectable without the pulls). `Interconnect` is blank on 3,452 rows of 2026-03-17/18 as served. |

Fetch command (SPP-14's producer, listing + download; the loop is in the FINDING §3):
`python scripts/data/fetch_spp_alt_portal.py --list rtbm-binding-constraints --path /2026/<mm>/By_Day`
then `download("rtbm-binding-constraints", "/2026/<mm>/By_Day/RTBM-DAILY-BC-<yyyymmdd>.csv")` for
every day ≥ 2026-01-28; parse with `csv.reader` (a 14-field row under a 10-column header is a
schema-break row, not an error). sha256 in `SHA256SUMS.txt`.

**What the sidecar says (derates are the norm):** over its 39,763 BINDING/BREACHED rows the
effective limit sits below the `Source Limit` in **99.2 %** of intervals, at a median ratio of
**0.92** — SPP runs the corridor's elements at a derated real-time limit almost always, which is why
the limit-at-bind (the ERCOT instrument), not the registry rating, is the primary L_f. The
per-constituent table (n, median / p10 / p90, source limit, derate share) is FINDING-spp-53 §3.

---

## STATUS UPDATE 2026-09-07 — lane SPP-57: the 2026 Oklahoma-set limit sidecar LANDED; the two chain-link TTCs are derived (N↔OK 6,500 MW, OK↔S 6,700 MW)

Companion to the SPP-53 section above, same construction, same daily pull (221 files, 160
14-column days, 2026-03-17 → 2026-09-05), same parser (`docs/handoffs/spp57/extract_2026.py`,
group rules copied verbatim from `spp14/groups.py`); only the group filter differs.

**`rtbm_bc_oklahoma_limits_2026.parquet`** — 1,083,301 rows, 262 constraints, every
`State ∈ {BINDING 87,678, BREACHED 6,770, ACTIVATED 988,853}` row of the 14-column files whose
constraint is `oklahoma_internal` (770,908 rows), `sps_tie` (154,118) or a CSWS-only `other`
row (158,275) — the OK↔S and Oklahoma-entry candidate set of `PRECOMMIT-spp-57-2026-09-07.md`
§3.2. Columns: the ten of the corridor sidecar plus `group`. Derates over the binding rows:
99.4 % of intervals below `Source Limit`, median ratio 0.91.

What it fed (FINDING-spp-57 §3): the per-constituent limit-at-bind `L_f` for the Oklahoma-set,
SPS-tie and CSWS constituents of both links; the corridor constituents keep SPP-53's committed
`L_f`. The four-group spec above is untouched.

## Span extended to 2019 — lane SPP-80, 2026-09-25

The RTBM binding-constraint roll-ups for **2019, 2020, 2021 and 2022** are now landed beside 2023–2025, fetched over the same anonymous portal route, unmodified. URLs, member names, byte counts and the measured schema drift are in `SOURCES.md` (SPP-80 appendix), and sha256 values are in `SHA256SUMS.txt`. Use: `docs/handoffs/FINDING-spp-80-upper-tercile-premium-2026-09-25.md`.
