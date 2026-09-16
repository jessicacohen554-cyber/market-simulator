# FINDING — CAISO OASIS public-bid archive does NOT reach 2021 Q2

**Lane:** caiso-281 BACKFILL, fetch+aggregate shard, quarter **2021 Q2 (2021-04-01 .. 2021-06-30)**
**Date:** 2026-09-14
**Pin:** `7fe0a10c77983946b1e06a90ca2eea3c30794d0c`
**Charter:** `docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md`
**Outcome:** STOPPED AT THE LIVENESS GATE. Nothing fetched, nothing aggregated. 6 HTTP requests
spent instead of ~180.

## 1. Verdict

`PUB_RTM_GRP` and `PUB_DAM_GRP` both return **ERR_CODE 1000 — "No data returned for the
specified selection"** for 2021 Q2 trade dates. **Both markets are dead at this quarter**; there
is no RTM/DAM asymmetry to exploit. Per the shard's HARD STOP 1 this is a SUCCESS: it places the
public-bid retention floor **after 2021-06-30** at a cost of four probe requests.

The register-item **N-CA-1 prior (OASIS *LMP* boundary 2023-04-19)**, which was REFUTED for bids
at 2023, is **NOT refuted at 2021** — this quarter sits below whatever the bid floor is. The
probes bound the floor from below only; they do not locate it. Sibling shards on adjacent
quarters bracket it.

## 2. Probe results, verbatim

Method: the committed downloader's own machinery — `_day_url` / `_UA` / `_is_no_data_report` from
`scripts/data/fetch_caiso_public_bids.py`, imported unmodified. 20 s between requests.
Endpoint form: `GroupZip?groupid=<PUB_RTM_GRP|PUB_DAM_GRP>&startdatetime=<YYYYMMDD>T08:00-0000&version=3&resultformat=6`

| market | trade date | HTTP | starts `PK` | bytes | zip member | member bytes | `_is_no_data_report` |
|---|---|---|---|---|---|---|---|
| rtm | 2021-05-15 | 200 | True | 612 | `20210515_20210515_PUB_BID_RTM_v3.xml` | 729 | **True** |
| dam | 2021-05-15 | 200 | True | 612 | `20210515_20210515_PUB_BID_DAM_v3.xml` | 729 | **True** |
| rtm | 2021-04-05 | 200 | True | 613 | `20210405_20210405_PUB_BID_RTM_v3.xml` | 729 | **True** |
| dam | 2021-04-05 | 200 | True | 613 | `20210405_20210405_PUB_BID_DAM_v3.xml` | 729 | **True** |

sha256 (first 16 hex) of the four bodies: `7f3453a9d9d0c0ed`, `7df6c1feb2352cdb`,
`3cc2fef4ce2a96e4`, `5908f08a56f826bb`.

All four member payloads are byte-identical apart from the `<m:TimeDate>` stamp:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<m:OASISReport xmlns:m="http://www.caiso.com/soa/OASISReport_v1.xsd">
<m:MessageHeader>
	<m:TimeDate>2026-09-14T17:07:32.824Z</m:TimeDate>
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

## 3. Positive controls — the probe harness works and the endpoint is live

Same harness, same session, same UA, one date inside the confirmed 2023-2025 span:

| market | trade date | HTTP | bytes (zip) | zip member | member bytes | `_is_no_data_report` |
|---|---|---|---|---|---|---|
| rtm | 2023-05-15 | 200 | 1,488,099 | `20230515_20230515_PUB_BID_RTM_v3.csv` | 42,967,810 | False |
| dam | 2023-05-15 | 200 | 379,296 | `20230515_20230515_PUB_BID_DAM_v3.csv` | 10,940,021 | False |

So the 2021 no-data answers are the **archive's** answer, not a transport, proxy, UA or
rate-limit artifact: the same code path one request earlier/later returns a 43 MB RTM CSV.

## 4. Rate limiting observed

- **1 × HTTP 429** ("Too Many Requests"), on the first request of the second probe run, with
  twelve sibling shards fetching concurrently. Recovered on the next attempt after the
  fetcher's 30 s backoff. **0 × 429 on all six subsequent requests.**
- Total requests spent by this shard: **10** (4 first-run probes + 1 × 429 + 6 second-run
  probes incl. the two 2023 controls). No `--sleep` was lowered.

## 5. Observation for the parent — NOT patched here (shard scope)

The two probe runs returned **two different no-data envelopes** for the same URLs, ~4 minutes
apart:

- **Run 1** (17:03Z): 645-byte zip, member `20210515_20210515_PUB_RTM_GRP_RTM_N.xml`
  (**group-level** naming, `_N` suffix), 757-byte payload, `_is_no_data_report` → **False**.
- **Run 2** (17:07Z): 612/613-byte zip, member `..._PUB_BID_RTM_v3.xml` (**report-level**
  naming), 729-byte payload, `_is_no_data_report` → **True** (§2 above).

Both are non-CSV and neither carries bid data, so the retention verdict is unaffected. But the
run-1 form is not recognised by `_is_no_data_report`, and in `_fetch_day` it would fail the
`len(body) > 10_000` test, fall through to the non-zip retry branch, exhaust 5 attempts across
~8 minutes of backoff, and raise `RuntimeError` — i.e. a **hard crash instead of the intended
"NO DATA — skipped"**, at ~8 min per affected date. Whether that variant is transient
(rate-limit-adjacent) or a second stable OASIS response form is **unmeasured** — n=4, one run.

Recorded as an observation only. `scripts/` is the parent's file and this shard does not patch
it (shard rule: "a shard that repairs infrastructure is a FAILURE").

## 6. What was NOT done

No fetch (`data/raw/caiso-public-bids/zips-rtm/` does not exist; `zips/` untouched — the
directory holds only its committed `README.md`). No aggregation. No
`results/rtm-intake/caiso281/2021q2/` tree. No LP or calibration solve. No edits under `src/` or
`scripts/`. Working tree clean apart from this document.
