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

**Re-fetchability: NONE — history-as-archive is the only recovery.** The OASIS
LMP retention boundary is a *moving* ~39-month window (a property of the
PRC_LMP report itself): binary-searched at **2023-04-19 on 2026-07-31** and
already **2023-04-22 by 2026-08-04** (`fetch_caiso_oasis.py` docstring — do not
hardcode a boundary; re-measure it). Every trade date in these zips is far past
it, so no OASIS query and no fresh hand-download can ever serve them again.
History is kept — the conversion untracked the payloads at tip, it did **not**
rewrite history — so the exact bytes remain fetchable forever from the promisor
remote at the pin sha:

```
git restore --source=726f389d94c45141bac83eacfdaea5e18a465c56 -- data/raw/lmp-data/CAISO
```

Verify a restore against `SHA256SUMS.txt` (`sha256sum -c`, from this
directory, on the `*_csv.zip` lines).

**Consumers of the zips** (all tolerate their absence at tip):
`scripts/data/fold_caiso_oasis_grp_zips.py` — the standing folder that turns
restored GRP zips into the hourly aggregates above (the aggregates already
carry this fold, so it re-runs only after a restore); and frozen probes from
the caiso-163…168 lanes (frozen record — they degrade gracefully when the
payloads are absent, and a restore from the pin revives them byte-exactly).

**Future OASIS pulls stay out of the pack by design:** `.gitignore` carries
`data/raw/lmp-data/CAISO/2???????_2???????_*_csv.zip`, so a fresh SingleZip /
GRP hand-download lands untracked; fold it with
`fold_caiso_oasis_grp_zips.py` / `postprocess_oasis_downloads.py` and commit
only the aggregate deltas.

Immutable raw source root: never modified in place (repo data contract).
