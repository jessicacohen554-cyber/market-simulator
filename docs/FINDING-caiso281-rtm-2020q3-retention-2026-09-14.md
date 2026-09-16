# FINDING — CAISO OASIS public-bid archive does NOT reach 2020 Q3 (both market runs)

**Lane:** caiso-281 BACKFILL, fetch+aggregate shard, quarter **2020 Q3 (2020-07-01 .. 2020-09-30)**
**Date:** 2026-09-14 · **Pin:** `7fe0a10c77983946b1e06a90ca2eea3c30794d0c`
**Charter:** `docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md`
**Outcome:** STOPPED at the liveness gate. **Nothing fetched, nothing aggregated.** 0 of ~180 bulk
requests spent.

## 1. Verdict

`PUB_RTM_GRP` and `PUB_DAM_GRP` both return **ERR_CODE 1000 — "No data returned for the specified
selection"** for every 2020 Q3 trade date probed. **There is no asymmetry**: RTM and DAM are dead
together, on the same dates. The August 2020 California heat-storm rotating-outage episode is
**not** recoverable from this endpoint.

Register item N-CA-1 records the OASIS *LMP* boundary at 2023-04-19 as a prior. That prior was
REFUTED for bids at 2023 (the 2023-2025 span is confirmed live). This shard tested it at 2020 and
finds the bid archive **empty at 2020 Q3** — the floor is somewhere above this quarter. Eleven
sibling shards are bracketing the adjacent quarters; this shard contributes the 2020 Q3 rung only.

## 2. Probe results (verbatim)

Probes used the committed downloader's own machinery — `_day_url` / `_UA` / `_is_no_data_report`
from `scripts/data/fetch_caiso_public_bids.py` — 20 s apart, no modification to that file.

| market | trade date | HTTP | starts `PK` | zip bytes | zip member (uncompressed) | `_is_no_data_report` | ERR_CODE |
|---|---|---|---|---|---|---|---|
| rtm | 2020-08-15 | 200 | yes | 613 | `20200815_20200815_PUB_BID_RTM_v3.xml` (729 B) | **True** | 1000 |
| dam | 2020-08-15 | 200 | yes | 612 | `20200815_20200815_PUB_BID_DAM_v3.xml` (729 B) | **True** | 1000 |
| rtm | 2020-07-03 | 200 | yes | 612 | `20200703_20200703_PUB_BID_RTM_v3.xml` (729 B) | **True** | 1000 |
| dam | 2020-07-03 | 200 | yes | 612 | `20200703_20200703_PUB_BID_DAM_v3.xml` (729 B) | **True** | 1000 |
| rtm | 2020-09-15 | 200 | yes | 612 | `20200915_20200915_PUB_BID_RTM_v3.xml` (729 B) | **True** | 1000 |

Payload, identical on all five (RTM 2020-08-15 shown):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<m:OASISReport xmlns:m="http://www.caiso.com/soa/OASISReport_v1.xsd">
<m:MessageHeader>
	<m:TimeDate>2026-09-14T17:08:07.412Z</m:TimeDate>
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

## 3. Positive control — the probe method is not producing a false negative

The same code path, same session, against a date the span is known to cover:

| market | trade date | zip bytes | member | uncompressed |
|---|---|---|---|---|
| dam | 2023-08-15 | 391,131 | `20230815_20230815_PUB_BID_DAM_v3.csv` | 11,082,244 B |
| **rtm** | 2023-08-15 | 1,727,542 | `20230815_20230815_PUB_BID_RTM_v3.csv` | **49,553,121 B** |

The RTM control is the load-bearing one: `PUB_RTM_GRP` returns a 49.5 MB CSV for 2023-08-15, so a
dead RTM at 2020 is an archive boundary, **not** a bad group id, a bad URL construction, or a
User-Agent/proxy artifact.

## 4. Incidental observation for the PARENT — `_is_no_data_report` does not recognise ERR_CODE 1015

Not patched (this shard may not edit `scripts/`). Reported for the parent's decision.

The **first** request for any not-yet-cached trade date returns a *different* small zip:

```
zip=644 B  member=20200915_20200915_PUB_RTM_GRP_RTM_N.xml (757 B)
<m:ERR_CODE>1015</m:ERR_CODE>
<m:ERR_DESC>GroupZip DownLoad is in Processing, Please Submit request after Sometime</m:ERR_DESC>
```

GroupZip is asynchronous: request 1 kicks the job off and returns 1015; request 2 returns the real
answer (the CSV, or the 1000 no-data report). Note the member name differs too — `PUB_<GRP>_<MKT>_N.xml`
for 1015 versus `PUB_BID_<MKT>_v3.xml` for 1000. This is why the first pass of this shard's probe
recorded `_is_no_data_report = False` on all four dates and a re-probe recorded `True`.

Consequences in `_fetch_day`, as currently committed:

- A 1015 body is `PK`-prefixed but `<= 10_000` B and fails `_is_no_data_report`, so it falls to the
  "non-zip body" branch, prints a misleading `non-zip body (644 B)` line, and sleeps 30 s before
  retrying.
- That retry is what actually collects the payload, so the fetcher **works by accident** — the
  async handshake is absorbed by the rate-limit backoff path.
- Cost: every cold date pays a spurious 30 s backoff and one of its 5 retries. A date that is
  *genuinely* no-data burns one retry on the 1015 and then exits cleanly on the 1000.
- Risk, if a future date ever needs more than one 1015 round: the 30→60→120→240 s backoff can
  exhaust `retries=5` and raise `RuntimeError` on a date that would have succeeded.

Suggested parent-side fix (NOT applied here): recognise ERR_CODE 1015 explicitly and re-request
after a short fixed delay rather than routing it through the rate-limit backoff.

## 5. Cost

9 HTTP requests total (5 probe dates + 2 controls + 2 variant-characterisation re-requests), all
20 s apart. Zero 429s / Acceptable-Use pages observed. Bulk fetch not started: ~180 requests and
~2 h of budget not spent.
