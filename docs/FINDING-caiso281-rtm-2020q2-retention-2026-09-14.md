# FINDING — CAISO OASIS public-bid archive does NOT reach 2020 Q2 (caiso-281 backfill shard)

**Session:** caiso-281 FETCH+AGGREGATE shard, quarter **2020 Q2
(2020-04-01 .. 2020-06-30)**. **Lane:** CAISO RTM offer-surface intake backfill.
**Charter:** `docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md`.

**Pin:** `7fe0a10c77983946b1e06a90ca2eea3c30794d0c` (verified at session start; no
rebase, no pull).

**ZERO FETCH, ZERO SOLVE.** The liveness gate (HARD STOP 1) fired. No zips were
downloaded, no aggregation was run, nothing under `data/raw/` was written, no LP
was solved. Cost: **14 HTTP requests instead of ~180 day-fetches.**

**Headline.** 2020 Q2 is **absent from the OASIS public-bid archive on BOTH
market runs**. All four charter probes return `ERR_CODE 1000 — "No data returned
for the specified selection"`. This is a genuine archive boundary, not a
transport artifact: 2023-06-15 controls on both markets return real CSV payloads
through the identical code path, and the `version=3` confound is closed (v2 is
equally empty at the same date).

**Two results beyond this shard's quarter, material to the sibling shards:**

1. **A FALSE-BOUNDARY TRAP.** OASIS answers a cold GroupZip request with
   `ERR_CODE 1015 — "GroupZip DownLoad is in Processing"`, a **645-byte valid
   zip** that is NOT no-data. `_is_no_data_report` returns **False** for it
   (correctly). A shard that reads one 645-byte zip as "no data" will report a
   false retention floor. **Every one of this shard's four probes returned 1015
   on the first request.** The correct protocol is poll-until-conclusive.
2. **THE ARCHIVE REACHES 2022.** `PUB_RTM_GRP` **2022-06-15 is LIVE**
   (1,477,614 B CSV), while **2021-06-15 is NO DATA**. The RTM retention floor
   therefore lies in the open interval **(2021-06-15, 2022-06-15]** — earlier
   than the charter's "2023-2025 confirmed live" prior, and a full year below
   where the register's N-CA-1 LMP boundary (2023-04-19) would have put it.

---

## 1. The four charter probes — verbatim

Probed with the committed downloader's own machinery (`_day_url`, `_UA`,
`_is_no_data_report` in `scripts/data/fetch_caiso_public_bids.py`), polled to a
conclusive state. Conclusive states are `LIVE` (PK zip > 10,000 B, the predicate
`_fetch_day` itself accepts) and `NO_DATA` (`_is_no_data_report` True).

| market | trade date | HTTP | starts `PK` | bytes | zip member | `ERR_CODE` | `_is_no_data_report` | state |
|---|---|---|---|---|---|---|---|---|
| rtm | 2020-05-15 | 200 | yes | 612 | `20200515_20200515_PUB_BID_RTM_v3.xml` | 1000 | **True** | NO_DATA |
| dam | 2020-05-15 | 200 | yes | 612 | `20200515_20200515_PUB_BID_DAM_v3.xml` | 1000 | **True** | NO_DATA |
| rtm | 2020-04-03 | 200 | yes | 613 | `20200403_20200403_PUB_BID_RTM_v3.xml` | 1000 | **True** | NO_DATA |
| dam | 2020-04-03 | 200 | yes | 613 | `20200403_20200403_PUB_BID_DAM_v3.xml` | 1000 | **True** | NO_DATA |

The ERR_CODE 1000 payload, verbatim (rtm 2020-05-15, member
`20200515_20200515_PUB_BID_RTM_v3.xml`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<m:OASISReport xmlns:m="http://www.caiso.com/soa/OASISReport_v1.xsd">
<m:MessageHeader>
	<m:TimeDate>2026-09-14T17:08:41.806Z</m:TimeDate>
	<m:Source>OASIS</m:Source>
	<m:Version>v20131201</m:Version>
</m:MessageHeader>
<m:MessagePayload>
<m:RTO>
<m:name>CAISO</m:name>
<m:DISCLAIMER_ITEM>
<m:DISCLAIMER>The contents of these pages are subject to change without notice. Decisions based on information contained within the California ISO's web site are the visitor's sole responsibility.</m:DISCLAIMER>
</m:DISCLAIMER_ITEM>
<m:ERROR>
<m:ERR_CODE>1000</m:ERR_CODE>
<m:ERR_DESC>No data returned for the specified selection</m:ERR_DESC>
</m:ERROR>

</m:RTO>
</m:MessagePayload>
</m:OASISReport>
```

Per the charter's HARD STOP 1 — both RTM probes **and** both DAM probes no-data —
the shard **stopped without fetching**. There is no RTM/DAM asymmetry to report:
both market runs are equally absent at this quarter.

## 2. The ERR_CODE 1015 trap — why the first pass was inconclusive

**All four probes returned `ERR_CODE 1015` on their FIRST request**, and 1015 is
not an answer. The GroupZip endpoint assembles bundles asynchronously: the first
request *triggers* assembly and returns a placeholder; a later request retrieves
the result. The two states are distinguishable only by opening the zip:

| | `ERR_CODE 1000` (no data) | `ERR_CODE 1015` (processing) |
|---|---|---|
| bytes | 611-613 | 644-645 |
| zip member | `..._PUB_BID_<MKT>_v3.xml` | `..._PUB_<MKT>_GRP_<MKT>_N.xml` |
| `_is_no_data_report` | **True** | **False** |
| meaning | conclusive: archive hole | transient: poll again |

Both are `PK` zips of ~the same size, and **neither** satisfies
`_fetch_day`'s live predicate (`PK` and `> 10_000` B). The member name is the
cheapest reliable discriminator: the `_N.xml` suffix marks the placeholder.

The committed fetcher already handles this correctly and needs no change — 1015
falls through `_fetch_day`'s two accept branches into the exponential-backoff
retry (30 s → 300 s), which is the right behaviour. **No infrastructure was
touched by this shard.** The trap is for *probe* code, not for the fetcher:
a one-shot probe that classifies on size alone will read 1015 as no-data.

Observed transition (rtm 2020-05-15): request 1 → 1015 placeholder; request 2
(+20 s) → 1000 no-data. Four of the six poll targets needed ≥ 2 requests to
reach a conclusive state.

## 3. Controls — the protocol can detect "live"

A no-data result is only evidence of a boundary if the same code path returns
data where data exists. It does, on both markets, at full payload size:

| market | trade date | state | bytes | zip member |
|---|---|---|---|---|
| rtm | 2023-06-15 | **LIVE** | 1,589,532 | `20230615_20230615_PUB_BID_RTM_v3.csv` |
| dam | 2023-06-15 | **LIVE** | 385,611 | `20230615_20230615_PUB_BID_DAM_v3.csv` |

Note the member extension: a live day returns **`.csv`**, a dead day returns
**`.xml`**. Note also that RTM's payload is ~4.1× DAM's at the same trade date —
descriptive only, and consistent with the charter's standing note that DAM
publishes fewer priced resource-hours. No inference is drawn here.

## 4. Confound closed — this is a DATE boundary, not a `version=3` artifact

The fetcher pins `version=3` in `_day_url`. If the 2020 archive published under
an earlier report version, a v3 query could return no-data over data that
exists. Tested directly at the same trade date:

| groupid | version | trade date | state | member |
|---|---|---|---|---|
| `PUB_RTM_GRP` | 2 | 2020-05-15 | **NO_DATA** (ERR 1000) | `20200515_20200515_PUB_BID_RTM_v2.xml` |
| `PUB_RTM_GRP` | 1 | 2020-05-15 | inconclusive — 1015/429 through 4 polls | `..._RTM_N.xml` |
| `PUB_RTM_GRP` | 3 | 2020-05-15 | **NO_DATA** (ERR 1000) | `20200515_20200515_PUB_BID_RTM_v3.xml` |

v2 is empty at the same date as v3, so the boundary is **not** a v3 artifact. v1
never resolved past the placeholder within its poll budget and is left open;
given v2 and v3 agree, it is not worth further requests, and v1 is in any case
not the report the intake consumes.

## 5. Bracket — where the floor actually is (beyond this shard's quarter)

Two extra `PUB_RTM_GRP` v3 probes, reported so eleven sibling shards do not each
have to rediscover the order of magnitude:

| trade date | state | bytes |
|---|---|---|
| 2022-06-15 | **LIVE** | 1,477,614 |
| 2021-06-15 | **NO_DATA** (ERR 1000) | 612 |

**The RTM retention floor lies in (2021-06-15, 2022-06-15].** This shard did not
narrow it further — the sibling shards are quartering that interval, and
duplicating their requests would only add OASIS load. Stated as measured: two
single-day probes twelve months apart bound the floor; they do not establish
that every day inside the live side is present (isolated archive holes are known
to exist on live spans — the fetcher's `_is_no_data_report` docstring cites
2023-06-01).

## 6. What this shard did NOT do

No zips fetched. No aggregation run. Nothing written under `data/raw/`. No edit
under `src/` or `scripts/` — the 1015 trap in §2 is documented, **not patched**;
the fetcher's existing retry already covers it, and it is the parent's file
either way. No `.gitignore` edit, no dashboard script, nothing under
`frontend/data/**`, no PR, no result deleted, no LP or calibration solve.

## 7. Recommendation to the parent

1. **2020 Q2 cannot be backfilled.** Both market runs are absent. The quarter
   should be struck from the backfill plan rather than retried.
2. **Fix the probe protocol before trusting any sibling's boundary**, if those
   shards classified on a single request or on byte size: a 645-byte
   `..._GRP_<MKT>_N.xml` zip is ERR 1015 *processing*, not no-data (§2). Any
   sibling reporting a no-data floor off one request should be re-run
   poll-until-conclusive. This shard's own first pass would have reported a
   false boundary on that reading.
3. **Re-aim the backfill at (2021-06-15, 2022-06-15]** — the live archive
   extends at least to 2022-06-15 on RTM, a year earlier than the charter's
   prior, so there is materially more recoverable history than the plan assumed.
   Register item N-CA-1's 2023-04-19 OASIS *LMP* boundary is refuted for *bids*
   at 2022 as well as at 2023.

**Reported descriptively. No conclusion is drawn here about whether RTM and DAM
ladders differ** — the charter fixes that rule and the parent applies it.
