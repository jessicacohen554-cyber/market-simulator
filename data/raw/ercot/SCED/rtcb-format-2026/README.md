# rtcb-format-2026/ — RTC+B format-break quarantine (payloads untracked)

This subdirectory is the **load-bearing quarantine** for the 27 NP3-965 parts
published in the RTC+B disclosure format (`2026-02.part0002-0027`,
`2026-03.part0000`; deliveries 2025-12-05..31) — readable ONLY through
`scripts/lib/sced_rtcb_adapter.py`, and kept out of every corpus consumer by
the non-recursive top-level globs. The full story (format break, adapter
contract, why the subdirectory must never be flattened) is in the parent
`../README.md`.

The 27 parquet payloads are **gitignored as of 2026-08-15** (BLOAT-B-5 item
A2, owner-signed) — this README is tracked so the layout marker survives.
Their post-slim bytes are hashed in `../SHA256SUMS.txt` (the
`rtcb-format-2026/…` lines). **The former restore-from-pin route
(`git restore --source=726f389d…`) is DEAD**: the 2026-08-16 history rewrite
(run #18 / 31955205445; `docs/FINDING-history-rewrite-2026-08-16.md`) stripped
these blobs and the pin no longer resolves. Recovery is re-fetch: the RTC+B
publications (2026-02/03) are recent, well inside the MIS rolling retention —
`scripts/data/fetch_ercot_sced_corpus_shards.py`, then recompress per the slim
protocol (`slim_ercot_dam_disclosure.py --sced-only`, rtcb = recompress-only)
and verify against `../SHA256SUMS.txt`.

Never add this subdirectory to a corpus-root tuple, and never make the corpus
globs recursive (`sced_rtcb_adapter.assert_pre_rtcb_files` /
`.assert_no_rtcb_rows`; `tests/curation/test_sced_rtcb_adapter.py`).
