# caiso-public-bids — raw (gitignored)

`zips/<YYYYMMDD>_PUB_BID_DAM_v3_csv.zip` — CAISO OASIS "Public Bid Data"
(`PUB_DAM_GRP` GroupZip, CSV result format): one zip per DAM trade date
containing every scheduling resource's as-submitted day-ahead bids — full
piecewise energy bid curves (cumulative-MW/price breakpoints), self-schedule
MW, and AS product bids — for generators, participating loads, and
interties. Published with a 90-day lag (CAISO tariff §6.5.2.2).

Resource identity is MASKED (`SCHEDULINGCOORDINATOR_SEQ` /
`RESOURCEBID_SEQ` integer ids, no location/fuel), but the masked
`RESOURCEBID_SEQ` is **persistent across days and years** (verified
2026-07-16: 1,160 of 1,278 Jan-10-2024 generator seqs recur on Jul-10-2024,
median max-MW drift 0.24 MW), so per-resource longitudinal statistics are
meaningful.

**This directory's contents are gitignored** (see `.gitignore`) — the
3-year corpus (2023–2025) is ~1,096 daily zips ≈ 0.5–0.9 GB, past what's
practical to commit (the `pjm-energy-offers` precedent). Only this README
is tracked.

**Source:** CAISO OASIS GroupZip API,

```
https://oasis.caiso.com/oasisapi/GroupZip
    ?groupid=PUB_DAM_GRP&startdatetime=<YYYYMMDD>T08:00-0000
    &version=3&resultformat=6
```

Rate limit: OASIS returns an HTTP-200 HTML "Acceptable Use Policy
Violation" page when polled faster than ~1 request / 5 s; the fetcher
sleeps 6 s between requests and detects non-zip bodies.

**Regeneration:**

```bash
python scripts/fetch_caiso_public_bids.py               # 2023–2025
python scripts/fetch_caiso_public_bids.py --years 2025
python scripts/fetch_caiso_public_bids.py --start 2024-01-01 --end 2024-03-31
```

Coverage policy: train years 2023–2025 only (CLAUDE.md rule 22).

**Curate into the clean tree:**

```bash
python scripts/curate_dam_public_bids.py --isos CAISO
```

Writes one long-format Parquet per year to
`data/clean/dam-public-bids/CAISO/DAM/` through the frozen
`scripts.lib.clean_io.write_clean` seam (schema:
`data/dictionary/schema/dam-public-bids.schema.yaml`).

DATA NEEDED: RTM public bids (`PUB_RTM_GRP`) are not fetched — the derive
charter (measured DAM offer surface, C1 lane 2026-07-16) needs DAM only.
