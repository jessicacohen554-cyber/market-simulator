# ADDENDUM to PRECOMMIT-caiso262 — the RTM_LMP_GRP sizing, measured (§2.2 executed)

**Session caiso-262, 2026-09-07.** Executed after
`PRECOMMIT-caiso262-2022-touchpoint-2026-09-07.md` was pushed, on the date the
PRECOMMIT fixed (**2022-06-01**) and against the decision table it fixed
(§2.3). No price was read; nothing was scored.

## §1 — The measurement

24 requests at `version=3` over the trade date's local hours, plus one
`version=1` request at local hour 00 for comparison, ≥ 6 s apart.

| | `version=1` | `version=3` |
|---|---|---|
| requests per trade date | 1 per operating hour | **1 per operating hour** |
| `Content-Disposition` | `…_RTM_LMP_GRP_01_N_v1_csv.zip` | `…_RTM_LMP_GRP_{01…24}_N_v3_csv.zip` |
| group index ↔ `OPR_HR` | 01 ↔ 1 | **exact, all 24** (`OPR_HR` `['1']`…`['24']`) |
| zip bytes | 7.48 MB | 8.34 – 9.07 MB (mean 8.75) |
| members | **1** (`PRC_INTVL_LMP_RTM_01_v1.csv`) | **5**, one per LMP_TYPE (`…_LMP_`, `_MCC_`, `_MCL_`, `_MCE_`, `_MGHG_`) |
| `LMP_TYPE` carried | LMP, MCC, MCE, MCL — **no MGHG** | LMP, MCC, MCE, MCL, **MGHG** |
| price column | **`MW`** | **`VALUE`** |
| nodes / intervals | 16,577 / 12 (5-min) | 16,577 / 12 (5-min) |
| kept-node rows | 480 (10 nodes × 12 × 4 types) | 120 per member × 5 = 600 |
| trading hubs present | yes | yes (`TH_NP15/SP15/ZP26_GEN-APND`) |

**Whole trade date at v3: 24 requests, 210.0 MB, 292 s wall (145 s of it
download).**

## §2 — The charter's "7 groups/day" is FALSE; corrected by measurement

`docs/handoffs/caiso-2022-price-archive-intake-charter-2026-09.md` §6 and the
2026-09-06 CORRECTION paragraph of `data/raw/lmp-data/CAISO/README.md` both
state that `RTM_LMP_GRP` at `version=3` was "7 groups/day" in the tracked
January-2023 zips, leaving open the hope that v3 would cost 7 requests per day
instead of 24.

It does not. **v3 is one operating hour per request, exactly as v1 is.** The
PRECOMMIT §2.1 predicted this before measuring, from the tracked manifest
itself: `data/raw/lmp-data/CAISO/SHA256SUMS.txt` carries group indices
`01`…`24` for 2023-01-01 (21 of 24 present) and `01`…`08` for 2023-01-02 — i.e.
"7 groups" was a count of how many hours had been hand-downloaded on some
dates, never a property of the delivery. The measurement above confirms it on
2022 data. Both documents are corrected in place by this session.

**Consequence:** the RTM 2022 year is **8,760 requests**, exactly the charter
§4 sizing. There is no cheaper version.

## §3 — Decisions taken, each against the PRECOMMIT §2.3 row it fired

1. **`version=3` is the crawl version.** PRECOMMIT §2.3 row 1 ("v3 delivers one
   operating hour per request → crawl 24 requests/trade date"). v3 is chosen
   over v1 on **rule 14 `[R-ACCURATE]`**, not on cost: v3 carries **MGHG**, and
   the committed `CAISO_rtm_hourly_{2023,2024,2025}.csv` all carry a fully
   populated `MGHG` column. Crawling v1 would land a 2022 year whose MGHG is
   entirely NaN — a schema hole no other year has. v3 also matches the version
   the tracked RTM corpus was built with. Cost of the choice: +1.27 MB per
   request (210 vs 180 MB/day).
2. **The fold now normalises the price column.** PRECOMMIT §2.3 row 4 fired
   exactly as written: v3 names it `VALUE`, and
   `fold_caiso_oasis_grp_zips._window_frames` hard-required `MW` in its
   `usecols`, so it would have raised on the first zip.
   `_KEEP` becomes `_KEEP_KEYS` + `_VALUE_COLS = ("MW", "VALUE")`; the column is
   resolved **per member** from the header and renamed to `MW`, so every window
   CSV keeps one schema and `postprocess_oasis_downloads._lmp_frames` (which
   already accepted either name) is untouched. **This is a schema repair, not a
   data change**: the two names carry the same published quantity, and the DAM
   v12 path still reads `MW` and is unaffected. Note the fold had never in fact
   processed an RTM v3 zip — the tracked January-2023 RTM zips were
   deliberately left unfolded (`fold_caiso_oasis_grp_zips` docstring: ~34
   scattered hours cannot honestly stand for a month), so the `MW` contract had
   only ever been exercised on DAM.
3. **The crawl folds ONCE per trade date, after all of its groups are on
   disk.** `fold` skips a window whose CSV already exists, so the pre-existing
   fold-after-each-zip loop would have written each day's window **from hour 01
   alone** and silently discarded hours 02–24. This is the defect the
   PRECOMMIT §2.1 named before the code was touched.
4. **Hours are enumerated as instants, not as `range(24)`** — local midnight to
   the next local midnight, stepping one hour, with the arithmetic done in UTC.
   Verified: 2022-03-13 → **23** requests, 2022-11-06 → **25**, every other
   2022 date → 24. A fixed 24 would have dropped the fall-back repeat hour and
   duplicated the spring-forward gap.
5. **Pacing is an interval floor between request STARTS, not idle time after
   each response.** The OASIS acceptable-use limit is a request *rate*
   (~1 / 5 s); the pre-existing loop slept the full `--sleep` *after* each
   response, giving ~12 s between starts on a ~6 s download and roughly
   doubling an 8,760-request crawl. The crawl runs at `--sleep 7`, and because
   the measured download is ~8 s the floor rarely binds — **measured spacing is
   ≥ 7.96 s between request starts**, comfortably inside the AUP. The AUP-HTML
   detection and exponential back-off are unchanged.

## §4 — The crawl, as launched

`fetch_caiso_oasis_grp.py --market rtm --start 2022-01-01 --end 2022-12-31
--sleep 7`, background, **python PID 3795**, log + JSON summary in the session
scratchpad; resumable at both grains (a trade date whose window CSV exists is
skipped; within a date, an hour whose zip is already on disk is not
re-fetched).

**Validated on one full day before launch** (2022-01-01): 24/24 groups,
170.5 MB, 191 s, window `rtm_grp_20220101_20220101.csv` = **14,400 rows** (10
nodes × 12 intervals × 24 hours × 5 LMP types), 288 distinct intervals spanning
`2022-01-01T08:00Z … 2022-01-02T07:55Z` (the PST trade date exactly), all three
hubs present, every zip deleted after the fold, window gitignored.

**Projected year: 8,760 requests, ≈ 62 GB transferred (never retained),
≈ 19.4 h wall, ≈ 290 MB of window CSVs on disk.** The charter's ≈ 24 h estimate
holds; the interval pacing is what brings it under.

## §5 — Disclosure

PRECOMMIT §10 #1 recorded, before measuring, that I expected to contradict two
committed documents on the "7 groups/day" claim. **I did, and the measurement
agrees with the prediction.** That is stated as a disclosure rather than a
result: the prediction came from reading the tracked manifest, which is
evidence that was already on disk and that the two documents did not consult —
not from any insight of mine.
