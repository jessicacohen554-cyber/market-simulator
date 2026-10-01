# PRECOMMIT caiso-283 — the successor: re-aggregate exactly, classify on DAM, carry to RTM

**Lane:** CAISO calibration · **Date:** 2026-09-16 · **LP budget: ZERO** · keeper unchanged.
**Owner instruction:** *"Just do the successor"* (on RESULT caiso-282 §6). **Pushed before any
shard is launched and before any pooled number exists.**

**Charter, unchanged:** `docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md` §4 —
G-REPRO ±0.02 / ±0.01, G-OVERLAP ≥ 60 %, the 0.05 verdict thresholds. The caiso-281 addendum
withdrew G-OVERLAP only because the DAM classification was not computable; it is computable now,
so **the original §2 carry-over design is used and G-OVERLAP is RESTORED verbatim.** G-POP
(independent RTM classification) is reported as a diagnostic and gates nothing.

## 1. What changes in the instrument, and why each change is exact

| caiso-281 aggregator (quarter, grid) | caiso-283 reducer (market-year, exact) |
|---|---|
| rung: first breakpoint at/above target — **wrong** | last breakpoint at/below — the derive's `_price_at_frac` (fixed in the aggregator too, with a test on the verbatim 514544 ladder) |
| capacity: quarter p98 of hourly max | **year p98 over segment rows** — the derive's `cap_ry`, exact from a value-count histogram |
| ladder: 20-point grid, per-day hour-median, parent integrates | **`_band_price` per resource-hour**, every class geometry × band, mult with the derive's gas staircase and CARB netting, **resource-year median over hours** — the derive's estimation unit |
| body: grid interpolation at 0.35 | `_price_at_frac(seg, 0.35)` per hour, per-(resource, local day) median |
| parser: own CSV reader | **`scripts/lib/dam_public_bids/caiso.parse_day`**, the curate step's parser (RLE expansion included) |

Script: `scripts/data/reduce_caiso_bid_year.py`. Test: `tests/curation/test_caiso_bid_reducers.py`
(pass-1 capacity equals `Series.quantile(0.98)`; body and band columns equal direct calls of the
derive's functions on the same frame; 514544 body reads $18.59). The derive gains one
module-level function, `class_band_windows`, that its own closure now delegates to — no
behaviour change. Not reproduced, stated: the net-load-binned peak ladder, which no gate reads.

## 2. Shards (rule 32 (c), rule 34)

**Eight shards, one per (year, market): 2022–2025 × {DAM, RTM}.** Each fetches its full calendar
year (`fetch_caiso_public_bids.py --market <m> --start <y>-01-01 --end <y>-12-31 --sleep 16`),
reduces it, commits `results/rtm-intake/caiso283/<year>_<MKT>/` (two parquets + `meta.json`,
a few MB) to its own branch `claude/caiso283-<year>-<mkt>` with a `.gitignore` negation and a
plain `git add`, and reports. **2021 is dropped**: the classifier is run on the artifact's own
2023–2025 span (§3), and 2021 has no registered CARB price so it can carry no band — under this
design it contributes nothing. **2025 Q4 is included** (published; the artifact used it), so
G-REPRO reads the artifact's exact span.

Sleep 16 s × 8 concurrent ≈ one request per 2 s aggregate, between the measured-safe 3-way/8 s and
12-way/20 s points; 429s self-heal in the committed fetcher and are never a failure. ERR 1015 is
a queue state the fetcher retries through. Expected wall: ~1.7 h fetch + ~0.5 h reduce per shard.

## 3. The parent (zero LP), fixed before the shards return

1. **Classify on DAM 2023–2025** — the artifact's own span — with the derive's classifier
   (Theil–Sen on `body_daily`, gates [4, 18] / r ≥ 0.6 / ≥ 120 days / min_mw ≥ −1 / cap ≥ 20),
   `hr_cut = 8.5`, `st_cut` by `locate_st_cut`, CC + CT consumed, ST reported.
2. **G-REPRO:** DAM bands = cap-weighted (first classified year's cap) median over the bucket's
   resource-years of `m_<cls>_<band>`, 2023–2025. Must match 1.066 / 1.072 / 1.386 (CC) to ±0.01.
   Hard stop; on a miss the comparison is abandoned again and the residual is reported at full
   magnitude. Also reported: CT 1.103 / 1.146 / 1.154 (not gated by the charter), G1, G4.
3. **Carry the DAM classification to RTM by seq.** **G-OVERLAP:** RTM resource-years must cover
   ≥ 60 % of the DAM-classified CC_REGULAR + CT_PEAKER capacity; below that, INCONCLUSIVE.
4. **Verdict pool: 2022–2025, both markets, same seqs.** On **CC_REGULAR**, Δ = RTM − DAM on
   econ_low and econ_high: both ≤ −0.05 → RTM-BELOW; both |Δ| < 0.05 → RTM-FLAT; else
   INDETERMINATE. CT_PEAKER and peak reported. Robustness rows (gating nothing): 2023–2025 only;
   per year; `hr_cut` 8.4.
5. Diagnostic only: independent RTM classification and its G1 (the caiso-282 G-POP).

Whatever returns: C3a stays on RT, no multiplier at any value.

## 4. Housekeeping the successor owes

When the eight shards have landed and been verified (rule 33 (a): fetch, checkout, sha256 against
each shard's `meta.json`), the caiso-281 quarter aggregates under `results/rtm-intake/caiso281/`
— 174 MB written by the defective convention — are **deleted from `main`** in the parent
(rule 26 `[R-DELETE]`; git history is the record), keeping the README, manifests and verbatim
samples. Shards are archived once their bytes are in hand and never before.
