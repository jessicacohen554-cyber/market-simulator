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
re-downloaded and verified against it, the 2022 (and, if wanted, 2019–2021)
history is fetchable, and the refs/pull salvage paragraph above is moot for
these bytes. Fetcher: `scripts/data/fetch_caiso_oasis_grp.py` (GroupZip per
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
