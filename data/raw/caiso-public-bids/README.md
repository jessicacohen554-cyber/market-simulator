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

RTM public bids (`PUB_RTM_GRP`) — **OWNER-FUNDED 2026-09-13 (caiso-281), no
longer a standing DATA NEEDED gap.** The original charter (measured DAM offer
surface, C1 lane 2026-07-16) needed DAM only. What reopened it: the DAM-derived
ladder is scored against a REAL-TIME benchmark — `calibration_verdict` gates C3a
on `rt_lw` because a perfect-foresight dispatch LP is a real-time analogue and
the DART premium is a forward risk premium the LP has no mechanism to price —
so the model's marginal-cost input and its benchmark sit on different bases.
caiso-281 measured that mismatch (CAISO implied marginal-HR bias +0.533,
t = +4.03 vs RT; −0.158, t = −0.80 vs DA) and the owner funded the intake that
can say which side is wrong.

Layout, kept deliberately separate so no glob can pool the two market runs:

    data/raw/caiso-public-bids/zips-rtm/<YYYYMMDD>_PUB_BID_RTM_v3_csv.zip

Fetched by the same downloader with `--market rtm`
(`scripts/data/fetch_caiso_public_bids.py`; `--market dam` is the default and
its URL, filename and `zips/` directory are byte-unchanged). Charter and the
pre-registered comparison rule:
`docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md`.

**RTM intake COMPLETE and the question it was funded for is ANSWERED (caiso-283,
2026-09-16).** Both market runs were fetched for 2022–2025 (2,919 trade dates,
three archive holes) and reduced to the derive's exact per-resource-year
statistics by `scripts/data/reduce_caiso_bid_year.py`
(`results/rtm-intake/caiso283/`). The reduction reproduces the committed DAM
surface to 0.000 on every band, and the same CAISO combined cycles bid the
same energy body into RTM as into DAM (CC econ bands within 0.03 across
markets): **RTM-FLAT**, `docs/RESULT-caiso283-rtm-flat-2026-09-16.md`. The
DAM-derived surface stands. Retention, measured by caiso-281: the GroupZip bid
archive serves trade dates from **2021-08-15** (ERR 1000 before it; 2020 and
H1-2021 are dead in both markets), and the boundary is rolling — re-measure,
never hardcode. Raw zips are gitignored and regenerable by the downloader
(~1.7 h per market-year at `--sleep 16`).

## Intake status (caiso-178, 2026-08-06)

**FETCHED IN FULL for the 2023–2025 training window: 1,095 of 1,096 trade dates.**
The single missing date is **2023-06-01**, a genuine OASIS archive hole — the API
answers with an `ERR_CODE 1000` "No data returned" XML *inside a valid zip*, which
the fetcher detects and distinguishes from a rate-limit page. **Zero rate-limit
failures and zero retries** across 1,096 requests at the 6 s spacing. 422 MB.

**Known scaling limit of `curate_dam_public_bids.py`:** it cannot process a full
CAISO year in a ~15 GB environment. Measured 2026-08-06 — 141 days →
12,915,667 rows at **5.51 GB peak RSS** in 65 s, so a 365-day year extrapolates to
**~14.3 GB**, because `_curate_spec` holds every day-frame and `pd.concat`s them at
once. Consumers that only need a slice should **stream day-by-day** through
`scripts/lib/dam_public_bids/caiso.py::parse_day`, as
`scripts/data/derive_caiso_battery_bid_floor.py` does (~7 min over the whole corpus,
flat memory). Curating a full year needs the concat replaced with an incremental
write; that touches the frozen `clean_io.write_clean` seam and is not done here.

**First derived use — and a closed exit.** `scripts/data/derive_caiso_battery_bid_floor.py`
(caiso-178) asked whether the corpus identifies `ScenarioConfig.battery_dispatch_adder`.
**It does not**, for a structural reason rather than a resolution one: a storage
discharge bid encodes *when* the resource intends to run, not *what* it costs to run
(modal first discharge rung = the \$1,000 soft bid cap in all three years; the
cheap-bid mass carries an hour-of-day shape peaking at h19 PT). See
`results/calibration/FINDING-caiso178-public-bid-floor-2026-08-06.md`. **Do not
re-fetch this corpus to re-ask that question** — but it remains a legitimate measured
offer-surface input for the C1 charter this fetcher was originally written for.
