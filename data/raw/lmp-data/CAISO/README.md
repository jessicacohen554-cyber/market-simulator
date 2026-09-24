# lmp-data/CAISO — raw

Two populations live here; only the first is tracked.

## 1. Hourly aggregates (tracked — the corpus product, golden-tier-listed)

`CAISO_dam_hourly_<year>.csv` / `CAISO_rtm_hourly_<year>.csv` — hourly DAM
(PRC_LMP v12) and hourly-averaged RTM (PRC_INTVL_LMP 5-minute) trading-hub
prices, columns `interval_start_gmt, node, LMP, MCC, MCE, MCL, MGHG`. Built by
`scripts/data/postprocess_oasis_downloads.py` from OASIS pulls
(`scripts/data/fetch_caiso_oasis.py`); consumed by the clean-LMP curation and
`derive_caiso_loss_surface.py`. These are the files every runtime consumer
reads, and they stay tracked.

## 2. OASIS GRP SingleZip dailies (60 zips — UNTRACKED 2026-08-15, BLOAT-B-5 item B3, owner-signed)

`YYYYMMDD_YYYYMMDD_DAM_LMP_GRP_N_N_v12_csv.zip` and
`…_RTM_LMP_GRP_01..07_N_v3_csv.zip` — hand-downloaded OASIS GRP bulk archives
for January-2023 trade dates (~Jan 1–25), 559.9 MiB, committed during the
caiso-163…168 nodal-decomposition lanes. Untracking them restores this corpus's
own design (`postprocess_oasis_downloads.py` docstring: "the raw OASIS window
CSVs are bulky … the repo keeps tidy hourly aggregates instead and the raw
files are staged out"). Their bytes are pinned by `SHA256SUMS.txt` in this
directory (tracked).

**Re-fetchability: NONE. And the history-as-archive recovery this conversion
was built on is GONE: these bytes are UNRECOVERABLE from this repository since
2026-08-16.** The OASIS
LMP retention boundary is a *moving* ~39-month window (a property of the
PRC_LMP report itself): binary-searched at **2023-04-19 on 2026-07-31** and
already **2023-04-22 by 2026-08-04** (`fetch_caiso_oasis.py` docstring — do not
hardcode a boundary; re-measure it). Every trade date in these zips is far past
it, so no OASIS query and no fresh hand-download can ever serve them again.
The recovery contract written at conversion time — "history is kept … the
exact bytes remain fetchable forever from the promisor remote at
`git restore --source=726f389d…`" — was invalidated by the 2026-08-16 history
rewrite (`cleanup-large-blobs.yml` run #18 / 31955205445, owner decision
superseding the Addendum AQ NO-GO; `docs/FINDING-history-rewrite-2026-08-16.md`):
the 60 zip blobs were stripped, the pin no longer resolves, and its rewritten
twin `4759a16023f4` retains only the 8 non-payload files here (verified
2026-08-16). What remains: the tracked hourly aggregates (§1, the product
every consumer reads, already folded from these zips) and `SHA256SUMS.txt`,
which stays as the identity record of what was held. Last-resort salvage: as
of 2026-08-16 the pre-rewrite trees are still incidentally reachable through
GitHub's `refs/pull/*` retention (e.g. `git fetch origin refs/pull/3978/head`)
— unadvertised, no durability guarantee; if these bytes ever matter again,
salvage them from there BEFORE GitHub compacts, because no other copy exists
anywhere.

**CORRECTION 2026-09-06 (session caiso-261) — "Re-fetchability: NONE" above is
FALSE for the GroupZip endpoint, and the pinned bytes ARE reproducible.** The
~39-month retention is a property of the per-node `SingleZip` reports
(`PRC_LMP` / `PRC_INTVL_LMP`), not of the all-node *GroupZip* bulk archives:
measured 2026-09-06 through the session proxy,
`GroupZip?groupid=DAM_LMP_GRP&startdatetime=20230101T08:00-0000&version=12&resultformat=6`
returned HTTP 200 / 11,938,424 bytes whose **sha256 equals the manifest line
for `20230101_20230101_DAM_LMP_GRP_N_N_v12_csv.zip` above (`6523fedd…`)**, and
the same request for 2022-06-01 (and every 2022 trade date crawled since)
returns the full four-component archive, while the per-node `SingleZip` for the
same date returns "no data". So every zip in `SHA256SUMS.txt` can be
re-downloaded and verified against it, the 2022 history is fetchable, and the
refs/pull salvage paragraph above is moot for these bytes.

**BOUNDED 2026-09-07 (session caiso-263) — "and, if wanted, 2019–2021" was
WRONG, and this correction is itself corrected: GroupZip has its OWN retention
boundary, LONGER than the per-node one but not absent.** Binary-searched
2026-09-07 through the session proxy, `DAM_LMP_GRP` v12: **2021-04-26 → 3,018-byte
"No data returned" envelope, 2021-04-27 → 9.85 MB archive**, so the earliest
trade date served is **2021-04-27**. It is a property of the report, not of the
version or the market — v1 and v3 age out on the same dates, and `RTM_LMP_GRP`
v3 tracks it (no data at 2020-04-01, 6.94 MB at 2021-04-27) — and it MOVES with
the calendar exactly as the per-node one does, so **re-measure it, never
hardcode it**. Consequence for the holdout ladder (rule 22): the 2022 rung's
prices are fetchable and were fetched; **2019, 2020 and Jan–Apr 2021 hub/DLAP
LMPs are NOT obtainable from OASIS by any endpoint**, so a price basis for those
rungs needs a different source adjudicated under rule 14, not another crawl. Fetcher: `scripts/data/fetch_caiso_oasis_grp.py` (GroupZip per
trade date → `fold_caiso_oasis_grp_zips.fold` → zip deleted, extract-and-
discard). `RTM_LMP_GRP` is served as **hour groups — one operating hour per request at
BOTH `version=1` and `version=3`**, so a real-time year is 8,760 requests.
*(The clause here previously read "the tracked Jan-2023 `v3` zips were 7
groups/day", leaving open a hope that v3 batched hours. It does not: MEASURED
2026-09-07 on 2022-06-01 (caiso-262, `ADDENDUM-caiso262-rtm-sizing-2026-09-07.md`),
24 v3 requests returned 24 archives with the group index tracking `OPR_HR`
exactly, 8.34–9.07 MB each, 210.0 MB and 292 s for the trade date. "7
groups/day" was a miscount of how many hours had been hand-downloaded on some
January-2023 dates — `SHA256SUMS.txt` above carries group indices `01`…`24`.)*
The two versions differ in **shape, not content**: v1 returns ONE member with
every `LMP_TYPE` and names the price column `MW`; **v3 returns FIVE members,
one per type — and it is the only one of the two that carries `MGHG`** — and
names the column `VALUE`. The 2022 crawl uses **v3** under rule 14
`[R-ACCURATE]`, because the committed `CAISO_rtm_hourly_{2023,2024,2025}.csv`
all carry a populated `MGHG` column that v1 could not fill;
`fold_caiso_oasis_grp_zips` resolves either price-column name and normalises to
`MW`. Charter:
`docs/handoffs/caiso-2022-price-archive-intake-charter-2026-09.md`.
`CAISO_dam_hourly_2022.csv` (added by that crawl) carries the 10-node set the
GRP fold keeps (3 hubs + 4 DLAPs + MALIN_5_N101 / CAPTJACK_5_N003 /
PALOVRDE_ASR-APND), exactly as the GRP-folded Jan–Mar 2023 rows of
`CAISO_dam_hourly_2023.csv` already do.

**2021 Q3 (PARTIAL YEAR — added 2026-09-07).** `CAISO_dam_hourly_2021.csv`
covers **trade dates 2021-07-01 .. 2021-09-30 ONLY** (2,208 h x the same
10-node set, 22,080 rows, no gaps, no nulls; `LMP == MCE+MCC+MCL` to 7e-05).
It was fetched by the same GroupZip route as 2022 — `DAM_LMP_GRP` v12, one
request per trade date, 92/92 fetched, 0 missing, 0 partial, 0.949 GB
transferred in 875 s — which confirms by measurement that GroupZip serves
2021 as readily as 2022 (the per-node `SingleZip` API cannot: 2021 is far
past its moving ~39-month retention). Like 2021/2022 generally, the v12 DAM
archive carries four components and therefore **no `MGHG` column**; 2023+
files have one.

**This partial year is NOT scoreable, by design and without any extra guard.**
`scripts/data/derive_actual_lmp.py`'s `CAISO_MIN_HOURS = 6500` rejects it
(2,208 h), and 2021 is deliberately absent from `CAISO_PARTIAL_YEARS`, so no
CAISO 2021 bench year is emitted and the quarter cannot masquerade as a full
one. Completing 2021 means crawling the remaining nine months by the same
command; nothing else changes.

**`CAISO_rtm_hourly_2021.csv` is INCOMPLETE and being filled incrementally
(2026-09-07).** RTM is served one operating hour per request, so Q3 alone is
2,208 requests, and OASIS applies a SUSTAINED-RATE quota that a short DAM
crawl never reaches: measured here, RTM trade dates 1 and 2 cost 208 s and
217 s, after which the rate collapsed by roughly an order of magnitude
(HTTP 429 with the fetcher's exponential back-off absorbing it). The crawl is
therefore committed day-by-day as trade dates complete — **read the file's own
`interval_start_gmt` span for the authoritative coverage; do not assume Q3 is
whole.** Rows already present are final: each trade date is folded only after
all 24 of its hour-groups are on disk, the merge de-dups on
(`interval_start_gmt`, `node`) keeping the last write, and RTM v3 populates
`MGHG` exactly as the 2023-2025 files do. Resuming needs only
`fetch_caiso_oasis_grp.py --market rtm --start <first missing date> --end
2021-09-30`. As with DAM, `CAISO_MIN_HOURS = 6500` means no 2021 bench year is
emitted from a partial file.

**2021 Q4 ADDED 2026-09-08 (session caiso-264) — the quarter above is now
Q3+Q4 for DAM, and RTM's incremental fill jumped to Q4.** Crawled by the same
GroupZip route and command, trade dates **2021-10-01 .. 2021-12-31**: 92/92
dates on BOTH markets, 0 missing, 0 partial — `DAM_LMP_GRP` v12 0.93 GB in
846 s, `RTM_LMP_GRP` v3 2,208 requests / 16.14 GB in 18,869 s (the sustained-
rate quota above is real: 144 HTTP 429s, all absorbed by the back-off).
Q4 contributes **2,209 hours** per market, not 2,208 — 92 x 24 + the
**2021-11-07 fall-back hour**. Current coverage after the merge (the files'
own spans remain authoritative):

| file | rows | distinct hours | coverage |
|---|--:|--:|---|
| `CAISO_dam_hourly_2021.csv` | 44,170 | 4,417 | Q3 + Q4 complete |
| `CAISO_rtm_hourly_2021.csv` | 23,530 | 2,353 | 2021-07-01..07-06 + all of Q4 |

So RTM's Q3 fill stopped after 6 trade dates and **2021-07-07 .. 2021-09-30 is
the remaining RTM hole**; DAM has none in Q3-Q4. Both files stay unscoreable
by the same `CAISO_MIN_HOURS = 6500` guard (4,417 h and 2,353 h), and 2021
stays out of `CAISO_PARTIAL_YEARS`.

**The DST hour is the one thing a resumed RTM crawl must get right.** The
intra-day resume probe was keyed on the REQUEST index while OASIS names zips
by OPERATING HOUR, so on a DST date requests skipped themselves: this
quarter's first pass folded 2021-11-07 with 24 of its 25 hours, and it was
re-fetched on the fixed fetcher (caiso-262's removal of the probe + the
per-day hour-coverage check). Anyone resuming with a pre-fix checkout will
silently damage 2021-11-07 again. Audit after any crawl: distinct clock hours
per trade date must equal that date's true operating-hour count (25 on the
fall-back date, 23 on spring-forward), not the number of successful requests.

**The three WECC intertie nodes are present in the DAM file for both quarters,
so `wecc_intertie_lmp_hourly_CAISO.parquet` (still 2022-2025 only) can be
extended to 2021 without re-crawling** — though `fetch_caiso_intertie_lmp.py
--from-grp-windows` reads the per-day `dam_grp_*` windows, which are
gitignored and no longer on disk, so that path needs either a re-crawl or a
small reader change.

**Consumers of the zips** (all tolerate their absence at tip):
`scripts/data/fold_caiso_oasis_grp_zips.py` — the standing folder that turns
restored GRP zips into the hourly aggregates above (the aggregates already
carry this fold, so it re-runs only if payloads are ever salvaged back); and
frozen probes from the caiso-163…168 lanes (frozen record — they degrade
gracefully when the payloads are absent, which since 2026-08-16 is their
permanent state absent a refs/pull salvage).

**Future OASIS pulls stay out of the pack by design:** `.gitignore` carries
`data/raw/lmp-data/CAISO/2???????_2???????_*_csv.zip`, so a fresh SingleZip /
GRP hand-download lands untracked; fold it with
`fold_caiso_oasis_grp_zips.py` / `postprocess_oasis_downloads.py` and commit
only the aggregate deltas.

Immutable raw source root: never modified in place (repo data contract).

## 2021 Q2 prices fetched (caiso-264, 2026-09-07)

The boundary recorded above was re-measured independently this session and **reproduces to
the day**: `DAM_LMP_GRP` v12 returns the "No data" envelope for 2021-03-31 / 04-01 / 04-02 /
04-15 / 04-22 / 04-26 and a 9.85 MB archive for **2021-04-27**; `RTM_LMP_GRP` v3 tracks it
exactly (04-26 HE01 no data, 04-27 HE01 6.94 MB). Two independent bisections agreeing is the
strongest form the claim can take — and it still **MOVES**, so re-measure, never hardcode.

Fetched, the full obtainable head of the owner's April–June window:

| market | command | result |
|---|---|---|
| DAM | `fetch_caiso_oasis_grp.py --market dam --start 2021-04-27 --end 2021-06-30 --sleep 6` | **65/65 dates, 0 missing, 0 partial**; 0.653 GB, 580 s |
| RTM | `… --market rtm … --sleep 7` | **65/65 dates, 0 missing, 0 partial**; 1,560 hour-group requests, 10.969 GB, 13,690 s |

Folded to `CAISO_dam_hourly_2021.csv` / `CAISO_rtm_hourly_2021.csv` — 15,600 rows each
(1,560 h × 10 nodes), **schema and node set identical to the 2022–2026 aggregates**, so
rule-14 alignment is exact and no reconciliation is engaged. Verified before commit: DAM
1,560 distinct hours = exactly 65 × 24; RTM 18,720 five-minute intervals = exactly 65 × 288;
0 zips left behind. Hub means DAM NP15 $42.67 / SP15 $38.37 / ZP26 $36.78, RTM $36.32 /
$32.04 / $29.81 per MWh (RT under DA at every hub — the ordinary spring DA premium).
`wecc_intertie_lmp_hourly_CAISO.parquet` 70,080 → 87,600 rows, 2021 carrying exactly 1,560
finite hours per hub on the dense 8,760 calendar; the 2022–2025 rows are untouched (2022
MALIN $86.39 / PALOVRDE $82.95 reproduce caiso-261's recorded figures).

**ORDERING TRAP.** `fetch_caiso_intertie_lmp.py --from-grp-windows` reads the in-tree
`dam_grp_*_*.csv` windows, and `postprocess_oasis_downloads.py --stage-dir` MOVES them out.
Run the intertie builder **first**, or it silently finds nothing.

**What 2021 can ever contain.** The obtainable span is 2021-04-27..12-31 = 249 d = **5,976 h**
against `derive_actual_lmp.CAISO_MIN_HOURS = 6500`, and `CAISO_PARTIAL_YEARS` is
`frozenset({2026})` — so **2021 cannot clear the guard even if every remaining day is
fetched**, and a 2021 price basis needs an explicit, declared `CAISO_PARTIAL_YEARS`
amendment (NOT made here). Of that ceiling 1,560 h are in hand and 4,416 h (Jul 1 – Dec 31)
are still served **today**; the ceiling falls 24 h per day of delay. Full record:
`docs/handoffs/FINDING-caiso-2021-price-boundary-backfill-2026-09-07.md`.

## CORRECTION 2026-09-10 (session caiso-274) — the GroupZip boundary is now **2021-08-12**

The caiso-263 measurement recorded above (earliest served DAM trade date
**2021-04-27**, binary-searched 2026-09-07) is **stale**. Re-binary-searched
2026-09-10 through the session proxy, `DAM_LMP_GRP` v12: **2021-08-11 returns
the ~3 KB "No data returned" envelope and 2021-08-12 returns a 10,362,306-byte
archive**, so **2021-08-12 is the earliest trade date served today**.
`RTM_LMP_GRP` v3 tracks it exactly (no data 2021-08-11; 7,603,266 B at
2021-08-12). Control: 2023-01-01 DAM returned HTTP 200 / 11,938,424 B — the
byte size pinned in `SHA256SUMS.txt` — so the endpoint is healthy from this
container and the small responses are the no-data envelope, not a throttle.
Both boundary probes were repeated and reproduced their verdict.

**That is ~3.5 months of reach lost in 3 calendar days.** The rate is not
smooth-sliding-window behaviour and this session does not claim to explain it;
it is reported as measured. Treat the archive as **actively perishing**: the
instruction this file and `fetch_caiso_oasis_grp.py` already carry — *re-measure
the boundary, never hardcode it* — is the operative one, and the two dates now
recorded here are both historical readings, not constants.

**Consequences for the paragraph above ("What 2021 can ever contain").** Its
arithmetic stands but its obtainable set has shrunk: the DAM ceiling of 5,976 h
against `derive_actual_lmp.CAISO_MIN_HOURS = 6500` is unchanged (2021 still
cannot clear the guard without an explicit `CAISO_PARTIAL_YEARS` amendment), and
the committed 2021 DAM aggregate now holds **5,977 finite hours over 249 trade
days** — i.e. essentially all of the obtainable span, and **none of the 116
missing DAM trade days is fetchable any more**. The RTM aggregate holds 4,513 h
over 188 trade days; of its missing days exactly **50 (2021-08-12 … 2021-09-30)
were still reachable** on 2026-09-10 and were fetched by this session.

**2020 is unreachable on every known route** — per-node `SingleZip` (~39-month
window), GroupZip (this boundary), and the hand-downloaded GRP zips whose bytes
the 2026-08-16 history rewrite stripped. A 2020 CAISO price basis does not
exist and cannot be produced.

Full record: `docs/FINDING-caiso274-2020-2021-intake-census-2026-09-10.md` §6.

## 2026-09-24 (session i-caiso) — 2021 reference derived; boundary re-probed

`actual_lmp.json` / `actual_lmp_hourly_CAISO.parquet` / `tail/actual_tail.json`
now carry a CAISO **2021** record, derived from the committed 2021 aggregates by
`derive_actual_lmp.py` under the new `CAISO_RETENTION_PARTIAL_YEARS = {2021}`:
DA 5,977 h (Apr 27 – Dec 31), RT 5,713 h, each with a `*_cov` monthly coverage
vector so the verdict's like-for-like month mask drops Jan–Apr (and RT August,
0.6465) instead of reading them as full months. The C3c tail row records
`rt_coverage 0.652` and is reported as a lower bound. Every other ISO-year and
every other CAISO row is byte-identical.

GroupZip `DAM_LMP_GRP` v12 re-probed 2026-09-24: 2019-06-01, 2020-06-01 and
2021-08-12 return the 644-byte no-data envelope; 2021-09-01 returns 10.08 MB.
**2019 and 2020 CAISO hub prices remain unobtainable on every known route.**

