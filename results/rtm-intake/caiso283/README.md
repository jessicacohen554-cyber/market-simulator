# results/rtm-intake/caiso283 — exact per-market-year reductions of CAISO OASIS public bids

Eight reductions, 2022–2025 × {DAM, RTM}, written by `scripts/data/reduce_caiso_bid_year.py`
in fetch shards pinned to `f7534746cc4decff3aa5f8f9dd622a38163781a2` (each `meta.json` carries
`git_sha`, the zip count, the missing dates, and the sha256 of both parquets; the parent verified
every hash before archiving the shards). Per directory:

* `resource_year.parquet` — per resource-year: `cap_mw` (p98 over segment rows, the derive's
  own statistic), `min_mw`, hour/day counts, and `m_<CLASS>_<band>` — the resource-year median
  over hours of the derive's band multiplier for every class geometry × band. The parent picks
  the class after classifying; nothing here is pre-judged.
* `body_daily.parquet` — per (resource, local day): median body price at 35 % of capacity, the
  Theil–Sen classifier's daily table.

**These reproduce the committed DAM surface exactly** (`docs/RESULT-caiso283-rtm-flat-2026-09-16.md`
§1: deviation 0.000 on every band and the same bucket populations), which is what makes the
RTM-vs-DAM comparison in `_caiso283_pool_*.json` trustworthy. Pooling instrument:
`scripts/probes/_caiso283_pool.py`. Verdict: RTM-FLAT (CC econ bands within 0.03 across markets).

Not reproduced, stated: the net-load-binned peak ladder (`caiso_offer_surface_condbinned.json`),
which no gate reads. Archive holes: 2022-06-01 DAM, 2023-06-01 DAM, 2024-07-03 RTM.
