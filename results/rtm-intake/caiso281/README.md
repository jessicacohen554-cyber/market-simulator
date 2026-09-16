# results/rtm-intake/caiso281 — CAISO OASIS public-bid quarter aggregates (RTM + DAM)

17 quarters, 2021q3 .. 2025q3, both market runs, written by the caiso-281 fetch shards with
`scripts/data/aggregate_caiso_bid_ladders.py` from raw `PUB_RTM_GRP` / `PUB_DAM_GRP` zips that
no longer exist on any reachable disk. Per quarter: `agg/` (RTM) and `agg_dam/` (DAM), each
`hourly.parquet` + `ladder.parquet` + `agg_meta.json`. 2021q3 is partial (46 days from
2021-08-15; the OASIS GroupZip retention floor, measured). Span 2021-08-15 .. 2025-09-30.

## READ THIS BEFORE CONSUMING `ladder.parquet` (caiso-282, 2026-09-16)

**The ladder prices are sampled ONE RUNG HIGH relative to the derive's convention.**
`_curve_price_at` uses `np.searchsorted(mw, target, side="left")` — the first breakpoint at or
*above* the target — while `data/dictionary/schema/dam-public-bids.schema.yaml` declares
`segment_mw` as the MW at which a price *starts* to apply, so
`derive_caiso_offer_surface._price_at_frac` reads the last breakpoint at or *below*. Confirmed on
resource 514544 / 2023-02-15 (the ladder printed verbatim in
`docs/FINDING-caiso281-rtm-2023q1-2026-09-13.md` §3): `p080` here is $300 where the derive reads
$27.18; 7 of 20 grid points differ. Consequence, measured: the pooled DAM aggregates fail the
charter's G-REPRO on every CC band by +0.10 to +0.14 (`docs/RESULT-caiso282-rtm-pool-g-repro-
failed-2026-09-16.md` §1). **These ladders are not derive-equivalent and must not be used to
re-derive or re-adjudicate the committed offer surface.** The RTM-vs-DAM *pairing* is internally
consistent (same code both sides) and is usable only as a diagnostic.

The RTM files also carry the WEIM footprint: 57–63 % of RTM gas-like CC capacity belongs to
resource ids that never bid `PUB_DAM_GRP` in four years (RESULT §2). An RTM population is the
CAISO fleet only after restriction to seqs classified on DAM.

The aggregator is deliberately **not** patched under this data — the code at HEAD is what
produced these bytes. A corrected re-aggregation is the successor (RESULT §6).

`_caiso282_pool_*.json` are the outputs of `scripts/probes/_caiso282_rtm_pool.py` (classifier
span × `hr_cut`); every number in the RESULT comes from them.
