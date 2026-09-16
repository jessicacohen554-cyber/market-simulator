# FINDING — caiso-281 backfill shard: CAISO OASIS bid archive, 2020 Q1 — RETENTION FLOOR

**Date:** 2026-09-14 · **Lane:** CAISO (caiso-281) · **Role:** fetch+aggregate shard (backfill)
**Pin:** `7fe0a10c77983946b1e06a90ca2eea3c30794d0c` (verified before any work)
**Charter:** `docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md`
**Quarter:** 2020 Q1 (2020-01-01 .. 2020-03-31) · **Branch:** `claude/caiso281-agg-2020q1`
**Scope:** fetch only. No LP, no solve, no parser, no edit under `src/` or `scripts/`.

## 0. Headline

**G-LIVE FIRED. 2020 Q1 IS DEAD IN BOTH MARKETS. NOTHING WAS FETCHED.**

`PUB_RTM_GRP` and `PUB_DAM_GRP` both answer every probed 2020 Q1 trade date with
**ERR_CODE 1000 — "No data returned for the specified selection"**. **Six** independent
trade dates spanning all three months of the quarter, both markets, **all dead, none
unresolved**. The quarter cost **~27 requests instead of 180**, and no zip was written.

The verdict is anchored by a **positive control**: the same harness, pointed at the
sibling shard's known-live `rtm 2023-02-15`, returns a **41.5 MB CSV** and reproduces
that shard's recorded byte counts exactly (§1.1). The harness can see live data; 2020 Q1
has none.

**But the four-probe liveness test as specified would have returned the WRONG answer,
and every sibling shard probing a cold date is exposed to the same trap.** That is the
result that matters more than the boundary itself, and it is §2.

## 1. The verdict evidence (second-generation responses)

Issued through the committed downloader's own machinery (`_day_url` / `_UA` /
`_is_no_data_report` from `scripts/data/fetch_caiso_public_bids.py`). No file under
`scripts/` or `src/` was modified; the probe harness is a scratchpad script that
imports those symbols.

| # | Market | Trade date | HTTP | Bytes | `PK`? | Zip member (uncompressed) | ERR_CODE | `_is_no_data_report` |
|---|--------|-----------|------|-------|-------|---------------------------|----------|----------------------|
| 1 | rtm | 2020-02-15 | 200 | 613 | yes | `20200215_20200215_PUB_BID_RTM_v3.xml` (729 B) | **1000** | `True` |
| 2 | dam | 2020-02-15 | 200 | 613 | yes | `20200215_20200215_PUB_BID_DAM_v3.xml` (729 B) | **1000** | `True` |
| 3 | dam | 2020-01-03 | 200 | 613 | yes | `20200103_20200103_PUB_BID_DAM_v3.xml` (729 B) | **1000** | `True` |
| 4 | rtm | 2020-02-20 | 200 | 612 | yes | `20200220_20200220_PUB_BID_RTM_v3.xml` (729 B) | **1000** | `True` |
| 5 | dam | 2020-03-11 | 200 | 613 | yes | `20200311_20200311_PUB_BID_DAM_v3.xml` (729 B) | **1000** | `True` |
| 6 | rtm | 2020-01-03 | 200 | 612 | yes | `20200103_20200103_PUB_BID_RTM_v3.xml` (729 B) | **1000** | `True` |

Verbatim payload (identical modulo `TimeDate` on every row above):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<m:OASISReport xmlns:m="http://www.caiso.com/soa/OASISReport_v1.xsd">
<m:MessageHeader>
	<m:TimeDate>2026-09-14T17:07:35.420Z</m:TimeDate>
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

### 1.1 Positive control — the harness CAN detect live data

A dead-verdict shard owes proof that its instrument is not simply broken. The same
harness, same code path, same session, pointed at the 2023 Q1 sibling's confirmed-live
control date:

| Market | Trade date | Verdict | Zip bytes | Member | Member size |
|--------|-----------|---------|-----------|--------|-------------|
| rtm | **2023-02-15** | **`DATA_CSV`** | **1,447,289** | `20230215_20230215_PUB_BID_RTM_v3.csv` | **41,495,083** |
| rtm | 2020-02-15 | `ERR_1000` | 613 | `20200215_20200215_PUB_BID_RTM_v3.xml` | 729 |

Both numbers match `docs/FINDING-caiso281-rtm-2023q1-2026-09-13.md` §1 **exactly**
(1,447,289 compressed / 41,495,083 uncompressed), reproducing that shard's measurement
from a different session a day later. The live/dead contrast is **2,363×** in compressed
bytes and **56,920×** uncompressed. There is no ambiguity to adjudicate.

## 2. THE TRAP — ERR_CODE 1015, and why the specified 4-probe test is unsound on a cold date

**The four probes the prompt specified all returned `_is_no_data_report == False`.**
Read literally against the gate ("if BOTH RTM probes AND both DAM probes come back
no-data, STOP"), that is a **LIVE** verdict — and it is **wrong**.

Those four first responses were not data and not the no-data report. They were:

| Market | Trade date | Bytes | Zip member | ERR_CODE | `_is_no_data_report` |
|--------|-----------|-------|------------|----------|----------------------|
| rtm | 2020-02-15 | 645 | `20200215_20200215_PUB_RTM_GRP_RTM_N.xml` (757 B) | **1015** | `False` |
| dam | 2020-02-15 | 645 | `20200215_20200215_PUB_DAM_GRP_DAM_N.xml` (757 B) | **1015** | `False` |
| rtm | 2020-01-03 | 645 | `20200103_20200103_PUB_RTM_GRP_RTM_N.xml` (757 B) | **1015** | `False` |
| dam | 2020-01-03 | 645 | `20200103_20200103_PUB_DAM_GRP_DAM_N.xml` (757 B) | **1015** | `False` |

```xml
<m:ERROR>
<m:ERR_CODE>1015</m:ERR_CODE>
<m:ERR_DESC>GroupZip DownLoad is in Processing, Please Submit request after Sometime</m:ERR_DESC>
</m:ERROR>
```

**GroupZip is asynchronous.** A request for a trade date not already in OASIS's cache
returns ERR 1015 immediately and queues the archive job; the *next* request for the
same date returns the real answer — CSV if the data exists, ERR 1000 if it does not.

Three signatures separate the queued response from the no-data response, all measured:

* **Member filename.** Queued → `<date>_<date>_PUB_<MKT>_GRP_<MKT>_N.xml` (the `_N`
  suffix). Settled → `<date>_<date>_PUB_BID_<MKT>_v3.xml`, the same stem a live CSV uses.
* **Size.** Queued 645 B zip / 757 B member. Settled 612–613 B zip / 729 B member.
* **`_is_no_data_report`.** `False` on queued (the ERR 1000 sentinel string is genuinely
  absent), `True` on settled.

**Confirmation that 1015 is a queue state, not a property of dead dates.** Two dates
never previously requested by this shard (`rtm 2020-02-20`, `dam 2020-03-11`) returned
ERR **1015** on their first request and ERR **1000** on their second — rows 4 and 5 of §1.
The transition is the proof.

**Confirmation that the settled response is cached, not re-derived.** Six consecutive
fetches of `rtm 2020-02-15` returned a byte-identical 613-byte body
(`sha256 46a664fbc628…`) with a frozen `TimeDate` of `2026-09-14T17:07:35.420Z` — the
timestamp of the *first* settled response, minutes earlier.

### 2.1 The committed fetcher is NOT affected — do not "fix" it

`_fetch_day` handles both states correctly, by construction rather than by accident:

1. `body[:2] == b"PK"` but `len(body) == 645 < 10_000` → not accepted as data.
2. `_is_no_data_report(body)` is `False` on the 1015 → not treated as an archive hole.
3. Falls through to the retry path: prints a "non-zip body" line, sleeps 30 s, retries
   with exponential backoff — **which is exactly the correct response to "submit request
   after sometime"**.
4. The retry gets the settled response: a real CSV (`> 10_000` B → returned and written),
   or ERR 1000 (`_is_no_data_report` → `True` → returns `None` → logged
   `NO DATA in the OASIS archive — skipped`).

**No change to `scripts/data/fetch_caiso_public_bids.py` is warranted and none was made**
(shard scope; rule 27 `[R-PUSH]`). The vulnerability is specific to a **hand-rolled
single-shot probe that reads only the first response** — which is what the liveness gate
in the shard prompts specifies. The 2023 Q1 and 2025 Q3 sibling shards were not misled
only because their dates returned live CSVs on the first request (already cached, or
served synchronously); a shard probing a genuinely cold date is exposed.

### 2.2 Recommended repair to the PROBE PROTOCOL (parent's call, not this shard's)

A liveness probe must **resolve ERR 1015 before recording a verdict**: on a 1015, sleep
≥ 30 s and re-request the same date, repeating until the response is a CSV or ERR 1000.
A verdict must be recorded only from a settled response, and a probe that never settles
must be reported `UNRESOLVED` — never as `LIVE` on the strength of
`_is_no_data_report == False`.

Equivalently and more simply: **classify on `ERR_CODE`, not on the boolean.** Any
`< 10 kB` zip whose member is XML carries an `<m:ERR_CODE>`; 1000 = dead, 1015 = ask again.

## 3. What this establishes for the register

**Register item N-CA-1** records the OASIS *LMP* retention boundary at **2023-04-19** and
the 2023 Q1 sibling refuted it for the *bid* archive (`PUB_RTM_GRP` live to 2023-01-01).
This shard extends the bid-archive picture backwards:

* **2020 Q1 is not served** for `PUB_RTM_GRP` or `PUB_DAM_GRP`. Six dates, three months,
  both markets, ERR 1000 throughout.
* The bid-archive retention floor therefore lies **between 2020-03-31 and 2023-01-01**,
  and this shard does not narrow it further — eleven sibling shards are testing the
  adjacent quarters and the bracket is theirs to close.
* This is a **retention** statement about the GroupZip API, not a statement that the data
  never existed. Closing 2020–2022 would require the same hand-downloaded bulk route
  N-CA-1 already names for LMP; it is a procurement task, not a scripting task.

## 4. Request accounting

| Step | Requests | HTTP 429 | Notes |
|------|----------|----------|-------|
| Round 1 — the four specified probes, 20 s apart | 4 | 0 | all ERR 1015 (§2) |
| Round 2 — payload decode | 2 | 0 | first settled ERR 1000 |
| Round 3 — variant characterisation (6× same date) | 6 | 0 | cache confirmation |
| Round 4 — fresh cold dates | 2 | 1 | first attempt raised 429 |
| Round 5 — settlement sweep, 25 s apart, 60 s backoff | ~11 | 3 | five dates settled |
| Round 6 — positive control + unresolved-date retry | 2 | 0 | both settled |
| **Total** | **~27** | **4** | vs **180** for a blind full-quarter fetch |

`--sleep 20` was never lowered. All 429s were transient and self-healing; none was
treated as a failure.

**No date is left unresolved.** `rtm 2020-01-03` exhausted three attempts at 429 in
round 5 and was recorded `UNRESOLVED` rather than inferred; it was retried in round 6 and
settled to **ERR 1000**, completing the set at six for six.

## 5. Deliverables

**No aggregate was produced**, because nothing was fetched: STEP 2 through STEP 4 of the
shard prompt are unreachable behind the G-LIVE stop. `results/rtm-intake/caiso281/2020q1/`
does not exist. This document is the deliverable, per the shard prompt's stop-gate branch.

No zips were written to `data/raw/caiso-public-bids/`; that tree still holds only its
committed `README.md`.

**A shard that stops with a clear report is a SUCCESS.** This one stopped at the gate it
was given, and additionally reports that the gate as specified would have failed open.
