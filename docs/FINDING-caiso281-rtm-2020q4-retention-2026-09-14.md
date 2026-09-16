# FINDING — caiso-281 backfill shard, 2020 Q4: OASIS PUB_BID archive does NOT reach this quarter

**Lane:** caiso-281 RTM offer-surface intake, BACKFILL wave (charter:
`docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md`).
**Shard:** 2020 Q4 (2020-10-01 .. 2020-12-31), fetch+aggregate.
**Date:** 2026-09-14. **Pin:** `7fe0a10c77983946b1e06a90ca2eea3c30794d0c`.

## Result

**STOPPED AT THE LIVENESS GATE. Nothing fetched, nothing aggregated.** Both
`PUB_RTM_GRP` and `PUB_DAM_GRP` answer every probed 2020 Q4 trade date with
the OASIS `ERR_CODE 1000` "No data returned for the specified selection"
report instead of a CSV payload. The archive does not reach 2020 Q4 on
**either** market run — there is no RTM/DAM asymmetry to exploit here.

Cost: 9 HTTP requests (4 gate probes + 4 confirmation re-probes + 1 positive
control) instead of the ~180 the bulk fetch would have spent.

## Probe results (verbatim)

All four gate probes, `--sleep 20` spacing, using the committed downloader's
own `_day_url` / `_UA` / `_is_no_data_report`
(`scripts/data/fetch_caiso_public_bids.py`), HTTP **200** on every request,
body starts with `PK` on every request:

| # | market | trade date | status | PK | bytes | zip member | `_is_no_data_report` |
|---|--------|-----------|--------|----|-------|-----------|----------------------|
| 1 | rtm | 2020-11-15 | 200 | True | 645 | `20201115_20201115_PUB_RTM_GRP_RTM_N.xml` | **False** (see §Hazard) |
| 2 | dam | 2020-11-15 | 200 | True | 645 | `20201115_20201115_PUB_DAM_GRP_DAM_N.xml` | **False** (see §Hazard) |
| 3 | rtm | 2020-10-03 | 200 | True | 645 | `20201003_20201003_PUB_RTM_GRP_RTM_N.xml` | **False** (see §Hazard) |
| 4 | dam | 2020-10-03 | 200 | True | 645 | `20201003_20201003_PUB_DAM_GRP_DAM_N.xml` | **False** (see §Hazard) |

Confirmation re-probes of the same four (market, date) pairs, same URLs,
returned the other envelope shape and resolved the detection cleanly:

| market | trade date | status | bytes | zip member | member bytes | `_is_no_data_report` |
|--------|-----------|--------|-------|-----------|--------------|----------------------|
| rtm | 2020-11-15 | 200 | 612 | `20201115_20201115_PUB_BID_RTM_v3.xml` | 729 | **True** |
| dam | 2020-10-03 | 200 | 612 | `20201003_20201003_PUB_BID_DAM_v3.xml` | 729 | **True** |
| dam | 2020-11-15 | 200 | 613 | `20201115_20201115_PUB_BID_DAM_v3.xml` | 729 | **True** |
| rtm | 2020-10-03 | 200 | 613 | `20201003_20201003_PUB_BID_RTM_v3.xml` | 729 | **True** |

Payload, byte-identical across all four confirmation re-probes apart from the
`TimeDate` stamp:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<m:OASISReport xmlns:m="http://www.caiso.com/soa/OASISReport_v1.xsd">
<m:MessageHeader>
	<m:TimeDate>2026-09-14T17:09:06.561Z</m:TimeDate>
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

URLs probed (unmodified `_day_url` output):

```
https://oasis.caiso.com/oasisapi/GroupZip?groupid=PUB_RTM_GRP&startdatetime=20201115T08:00-0000&version=3&resultformat=6
https://oasis.caiso.com/oasisapi/GroupZip?groupid=PUB_DAM_GRP&startdatetime=20201115T08:00-0000&version=3&resultformat=6
https://oasis.caiso.com/oasisapi/GroupZip?groupid=PUB_RTM_GRP&startdatetime=20201003T08:00-0000&version=3&resultformat=6
https://oasis.caiso.com/oasisapi/GroupZip?groupid=PUB_DAM_GRP&startdatetime=20201003T08:00-0000&version=3&resultformat=6
```

## Positive control — the null is the archive, not this container

An identical request on a known-live date, same machinery, same proxy, same
session, one request:

```
CONTROL rtm 2023-11-15: status=200  1,568,139 B  PK=True
  namelist: ['20231115_20231115_PUB_BID_RTM_v3.csv']  (n=1)
  member: 45,192,225 B
  head: STARTTIME,STOPTIME,STARTTIME_GMT,STOPTIME_GMT,STARTDATE,MARKET_RUN_ID,
        RESOURCE_TYPE,SCHEDULINGCOORDINATOR_SEQ,RESOURCEBID_SEQ,
        TIMEINTERVALSTART,TIMEINTERVALEND,TIMEINTERVALSTART_GMT,TIMEINTERVALEND_GM
  _is_no_data_report: False
```

So the endpoint, the `resultformat=6` CSV contract, the `_UA` header and the
egress path all work from here. The 2020 Q4 `ERR_CODE 1000` is a property of
the CAISO archive, not of this shard's machinery. **This control was added by
the shard and was not in its prompt**, on the ground that a bare "no data"
result is not distinguishable from a broken probe without one.

## What this does and does not establish

- **Establishes:** 2020 Q4 is EMPTY on both `PUB_RTM_GRP` and `PUB_DAM_GRP`,
  at two trade dates ~6 weeks apart (2020-10-03, 2020-11-15), each confirmed
  twice. The retention floor for PUB_BID is therefore **later than
  2020-11-15**.
- **Does NOT establish:** where the floor actually sits. Two dates in one
  quarter cannot bracket it. Eleven sibling shards are probing adjacent
  quarters; the parent brackets the boundary from the union.
- **Register item N-CA-1** records the OASIS *LMP* boundary at 2023-04-19 as a
  prior. That prior was refuted for *bids* at 2023 (the 2023-2025 span is
  confirmed live, and the control above re-confirms 2023-11-15). It is
  **untested between 2021-01-01 and 2022-12-31** — this shard says nothing
  about that interval either way.

## Operational hazard for the PARENT (not patched here — parent's file)

`_is_no_data_report` **did not detect** the no-data response on the first four
requests. OASIS returned two different envelope shapes for the same URLs:

- **Shape A** (observed on the first 4 requests): 645 B zip, member named
  `<date>_<date>_PUB_<GROUPID>_<RUN>_N.xml` → `_is_no_data_report` **False**.
- **Shape B** (observed on the next 4): 612-613 B zip, member named
  `<date>_<date>_PUB_BID_<RUN>_v3.xml`, containing the ERR_CODE 1000 text →
  `_is_no_data_report` **True**.

Consequence if a bulk fetch were pointed at a dead date range and Shape A came
back: `_fetch_day` takes neither early return (the body is `PK` but
`len(body) <= 10_000`, and the no-data check reads False), so it falls through
to the rate-limit branch, sleeps 30 → 60 → 120 → 240 s across 5 attempts, and
then raises `RuntimeError`. A dead quarter would burn ~12.5 min per trade date
and abort rather than skipping cleanly. Shape A's member was not read for
content in the first batch, so **whether Shape A also carries ERR_CODE 1000 is
unverified** — the shard did not re-request it to find out.

Per rule 32(c)(6) and STEP 4 of the shard prompt, `scripts/` was not touched.
This is reported for the parent to adjudicate.

## Deliverables

No `results/rtm-intake/caiso281/2020q4/` bundle exists — nothing was fetched,
so there is nothing to aggregate, commit or promote. No zips were written to
`data/raw/caiso-public-bids/` (verified: the tree still contains only
`README.md`). This document is the entire record, as the gate specifies.
