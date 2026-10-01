# FINDING — CAISO OASIS public-bid archive does NOT reach 2021 Q1 (both markets)

**Lane:** caiso-281 BACKFILL, fetch+aggregate shard, quarter **2021 Q1 (2021-01-01 .. 2021-03-31)**.
**Date:** 2026-09-14. **Pin:** `7fe0a10c77983946b1e06a90ca2eea3c30794d0c`.
**Charter:** `docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md`.

## Verdict

**STOPPED AT THE LIVENESS GATE. NOTHING FETCHED, NOTHING AGGREGATED.**
Both `PUB_RTM_GRP` and `PUB_DAM_GRP` return OASIS **ERR_CODE 1000 — "No data returned
for the specified selection"** for every probed 2021 Q1 trade date. The archive does not
reach this quarter on either market run. Cost: 15 HTTP requests instead of ~180.

This is the shard's result, not a failure. Register item **N-CA-1** (OASIS *LMP* boundary
at 2023-04-19) was a prior for the *bid* boundary; it was refuted at 2023 — the 2023 span
is live — and it is **not** refuted at 2021: 2021 Q1 is dead for bids.

## The probe matrix — verbatim

The gate mandated four probes (rtm/dam × 2021-02-15/2021-01-04). **All four are dead.**
Each row is the *resolved* response (see "the 1015 ack" below — a first request on an
uncached date returns an async job ack, not an answer, so the resolved response is the
one that carries the verdict).

| market | trade date | HTTP | zip B | starts `PK` | member | member B | `ERR_CODE` | `_is_no_data_report` |
|---|---|---|---|---|---|---|---|---|
| rtm | 2021-02-15 | 200 | 613 | yes | `20210215_20210215_PUB_BID_RTM_v3.xml` | 729 | **1000** | **True** |
| dam | 2021-02-15 | 200 | 613 | yes | `20210215_20210215_PUB_BID_DAM_v3.xml` | 729 | **1000** | **True** |
| rtm | 2021-01-04 | 200 | 613 | yes | `20210104_20210104_PUB_BID_RTM_v3.xml` | 729 | **1000** | **True** |
| dam | 2021-01-04 | 200 | 613 | yes | `20210104_20210104_PUB_BID_DAM_v3.xml` | 729 | **1000** | **True** |
| rtm | 2021-03-10 *(extra)* | 200 | 612 | yes | `20210310_20210310_PUB_BID_RTM_v3.xml` | 729 | **1000** | **True** |

`rtm 2021-02-15` was resolved three times in succession (20 s apart): identical
613 B / 729 B / ERR 1000 / `_is_no_data_report=True` on all three.

**No RTM-vs-DAM asymmetry.** Both market runs are dead at 2021 Q1, in the same way.

The no-data payload, verbatim and identical across all five dates but for the timestamp:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<m:OASISReport xmlns:m="http://www.caiso.com/soa/OASISReport_v1.xsd">
<m:MessageHeader>
	<m:TimeDate>2026-09-14T17:10:55.764Z</m:TimeDate>
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

## POSITIVE CONTROL — the method is sound, the quarter is empty

A "no data" reading is only worth something if the same probe returns data where data
exists. Both markets were probed on **2023-02-15**, inside the span the charter records
as confirmed live, through the identical code path in the same session:

| market | trade date | zip B | member | member B | verdict |
|---|---|---|---|---|---|
| rtm | 2023-02-15 | **1,447,289** | `20230215_20230215_PUB_BID_RTM_v3.csv` | **41,495,083** | **LIVE — CSV** |
| dam | 2023-02-15 | **337,568** | `20230215_20230215_PUB_BID_DAM_v3.csv` | **9,521,057** | **LIVE — CSV** |

Live dates return a `.csv` member of tens of MB; 2021 Q1 returns a 729 B `.xml` error.
The difference is three orders of magnitude and a different file type — not a marginal
call. The 2021 Q1 emptiness is a property of the archive, not of the probe.

## The 1015 ack — an OASIS protocol detail, NOT a downloader defect

Worth recording because it initially looked like a detector blind spot, and is not.

A **first (cache-miss)** request for a trade date returns a 645 B zip holding a **757 B**
member named `<date>_<date>_PUB_RTM_GRP_RTM_N.xml` carrying:

```xml
<m:ERR_CODE>1015</m:ERR_CODE>
<m:ERR_DESC>GroupZip DownLoad is in Processing, Please Submit request after Sometime</m:ERR_DESC>
```

That is an **asynchronous job-submission acknowledgement**, not an answer. `GroupZip`
queues the extract and serves the result on a subsequent request; the completed artifact's
internal `TimeDate` stays frozen at the original submission instant (measured: cold ack at
`17:10:55.756Z`, warm result at `17:10:55.764Z`, 8 ms apart, stable across later re-requests).

`_is_no_data_report` returns **False** on the 1015 ack, which is **correct** — a 1015 is not
a no-data report. `_fetch_day` then classifies it as a non-zip body, sleeps its 30 s backoff,
and the next attempt receives the real ERR 1000, which `_is_no_data_report` recognizes and
which `_fetch_day` correctly converts to a `None` "archive hole — skipped".

**The committed downloader handles this correctly and needs no change.** The only cost is one
extra request plus a 30 s backoff per uncached date. Per rule 27 and the shard charter, no
edit was made under `scripts/`; this is reported for the parent, not patched.

*Caveat, stated rather than smoothed over:* the 2023 control dates returned CSV on attempt 1
with no 1015, but those may already have been cached by a sibling shard. Whether a live,
uncached date also costs a 1015 round-trip is **not established** by this shard's evidence.

## What this shard did and did not do

- **Did not** fetch: `--market rtm` and `--market dam` for 2021 Q1 were never invoked.
- **Did not** aggregate: no `agg` / `agg_dam` outputs exist, so the STEP 6 aggregate
  statistics (n_resources, n_resource_hours, ladder rows, hours-per-(resource,day),
  `body_px_quarter_cap`, Jaccard) are **undefined for this quarter** — there is no data
  to describe. They are not omitted; they do not exist.
- **Did not** write anything under `data/raw/` — `data/raw/caiso-public-bids/` still holds
  only its `README.md`.
- **429 count: 0.** No HTTP-429 and no rate-limit HTML page was observed in 15 requests at
  20 s spacing, alongside the concurrent sibling shards.
- **Archive holes:** the entire quarter is a hole on both markets — dates probed
  2021-01-04, 2021-02-15, 2021-03-10 across RTM and DAM.

## For the parent

The retention floor for CAISO public **bid** data lies **after 2021 Q1** on both market runs.
Eleven sibling shards are testing adjacent quarters; this result brackets the floor from
below and the 2023-live control brackets it from above. Descriptive only — no inference is
drawn here about RTM-vs-DAM ladder differences, which the charter reserves to the parent.

The `data/raw/caiso-public-bids/README.md` retention note should record the measured 2021 Q1
no-data boundary once the sibling shards have bracketed it; that edit is the parent's, not
this shard's.
