# RESULT caiso-283 — the exact re-derivation reproduces the surface to the third decimal, and the RTM ladder reads FLAT

**Lane:** CAISO calibration · **Date:** 2026-09-16 · **LP spent: ZERO** · keeper unchanged
(`2026-09-12-caiso-275-gascoupling`, CALIBRATED 2023–2025, lone ledgered C3c). Nothing promoted,
nothing registered, no mechanism cell moved, no threshold moved, no artifact re-derived.

**Charter:** `docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md` §4.
**Method fixed before any number:** `docs/PRECOMMIT-caiso283-rtm-exact-rederive-2026-09-16.md`
(pushed at `f7534746`, the SHA every shard was pinned to). **Instrument:** eight fetch shards
running `scripts/data/reduce_caiso_bid_year.py` (data: `results/rtm-intake/caiso283/<year>_<MKT>/`),
pooled by `scripts/probes/_caiso283_pool.py` (outputs `_caiso283_pool_*.json` beside the data).

## 0. Headline

| gate | result |
|---|---|
| **G-REPRO** | **PASS — exact.** Pooled DAM 2023–2025 reproduces CC_REGULAR 1.066 / 1.072 / 1.386 and CT_PEAKER 1.103 / 1.146 / 1.154 with deviation **0.000** on every band, the unarmed committed band (1.030 / 1.162) included, and the same population: 46 / 11,935 MW, 70 / 7,391 MW, 30 / 2,559 MW, `st_cut` 11.738. |
| **G-OVERLAP** | **PASS — 100 %.** All 116 DAM-classified CC + CT resources (19,325 MW) bid RTM. |
| **Verdict** | **RTM-FLAT.** CC_REGULAR Δ(RTM − DAM) = **−0.006 econ_low / +0.025 econ_high**, both inside the pre-registered 0.05. |

**Consequence, per the charter's own branch:** the gap between the model's offer surface and the
real-time price it is scored against is **in the clearing, not in the offers**. CAISO combined
cycles bid the same energy body into the real-time market that they bid into the day-ahead
market. The scorer's stated position — the DART premium is a forward risk premium a
perfect-foresight LP has no mechanism to price — stands, and **CAISO's residual C3a miss is a
declared model-class limitation**, not an input-vintage defect. **This branch closes the lane.**

## 1. G-REPRO — the instrument reproduces the derive

The committed artifact was derived 2026-09-06 from a 1,095-day DAM corpus that no longer exists.
Eight shards re-fetched 2022–2025 for both market runs (2,919 trade dates; three archive holes:
2022-06-01 DAM, 2023-06-01 DAM, 2024-07-03 RTM) and reduced each market-year to the derive's own
estimation unit — p98 capacity over segment rows, `_price_at_frac` body, `_band_price` mults per
class geometry, resource-year median over hours — through the curate parser. The parent then ran
the derive's classifier on DAM 2023–2025:

| | committed artifact | this re-derivation | dev |
|---|---|---|---|
| CC bucket | 46 res / 11,935 MW / G1 0.871 | 46 / 11,935 / 0.871 | 0 |
| CT bucket | 7,391 MW / 0.970 | 7,391 / 0.970 | 0 |
| ST bucket, `st_cut` | 2,559 MW, 11.738 | 2,559, 11.738 | 0 |
| CC econ_low / econ_high / peak | 1.066 / 1.072 / 1.386 | 1.066 / 1.072 / 1.386 | 0.000 |
| CT econ_low / econ_high / peak | 1.103 / 1.146 / 1.154 | 1.103 / 1.146 / 1.154 | 0.000 |
| per-year CC econ_low 2023/24/25 | 1.063 / 1.027 / 1.085 | 1.063 / 1.027 / 1.085 | 0.000 |

Every published number of the artifact, per-year detail included, is reproduced from a fresh
fetch by independent code paths that share only the derive's functions. The caiso-282
instrument's +0.10..+0.14 miss is therefore fully attributed to that instrument (rung convention
plus quarter-grid approximations), and the artifact itself is confirmed as a faithful
measurement of CAISO's day-ahead bids. `hr_cut` 8.4: 45 CC resources, bands 1.066 / 1.071 /
1.385 — robust.

## 2. The verdict — same resources, both markets, 2022–2025

DAM classification carried to RTM by masked seq (the charter's original §2 design). CC_REGULAR,
46 resources in both markets, capacity-weighted medians over resource-years:

| CC_REGULAR | committed | econ_low | econ_high | peak |
|---|---|---|---|---|
| DAM | 0.992 | 1.056 | 1.047 | 1.268 |
| RTM | 1.017 | 1.050 | 1.072 | 1.214 |
| **Δ RTM − DAM** | +0.025 | **−0.006** | **+0.025** | −0.054 |

Per year, Δ econ_low / econ_high: 2022 +0.009 / +0.017 · 2023 −0.007 / +0.015 ·
2024 +0.019 / −0.001 · 2025 +0.005 / +0.055. Robustness: 2023–2025 only → +0.002 / +0.025
(RTM-FLAT); `hr_cut` 8.4 → −0.006 / +0.027 (RTM-FLAT). **The body of the CC ladder is the same
ladder in both markets, in every year, on every cut.**

Reported at full magnitude, deciding nothing:

* **CC peak sits BELOW DAM in real time**: −0.054 pooled, −0.13 on 2023–2025, −0.265 in 2024.
  The scarcity rung is bid lower in RTM, not higher. Whatever the RT price tail is made of, it is
  not a higher real-time offer from the combined cycles.
* **CT_PEAKER sits ABOVE DAM in real time**, +0.045 to +0.070 on every band, driven by 2025
  (+0.04..+0.18) and 2024; 2022–2023 are flat. Peakers ask more in RTM. Not the verdict class,
  and stated so before the numbers (PRECOMMIT §3.4).
* Independent RTM classification (the caiso-282 G-POP, diagnostic only): 155 CC-like resources /
  35.5 GW, G1 2.59, 62 % of that capacity never bidding DAM — the WEIM footprint, as measured
  before. The carry-over design is what makes the RTM comparison about CAISO.

## 3. What this closes, and what it does not

* **Closed:** the RESULT caiso-281 §5.1 successor. The offer surface's day-ahead basis is not an
  input defect; re-deriving it on RTM bids would move the CC econ bands by < 0.03 and is not
  warranted (rule 23 `[R-FROZEN-DERIVE]`: a re-derivation needs a new source that says something
  different, and this one does not). **The DAM-derived artifact stands, unchanged.**
* **Closed:** the ×0.92 multiplier's last motivation. It was a hand-sized correction for a basis
  mismatch; the basis is now measured flat on the offer side. Rule 1 (c) and rule 14 already
  refused it; this removes the story behind it.
* **Declared:** CAISO's 2022 C3a miss (+11.3 % vs RT, folded rung) and the in-sample +0.53
  MMBtu/MWh marginal-HR bias vs RT are a **model-class limitation** — a perfect-foresight LP
  clears without the real-time uncertainty that the RT price carries — carried as such on the
  keeper's record. Under rule 30 (c) the folded 2022 rung never downgraded the ISO; nothing in
  the scorer moves, and no caveat is manufactured to make it read better.
* **Not closed, named:** where the RT price tail comes from if not from higher RT offers (CC peak
  is *lower* in RTM). That is a clearing / commitment question, consistent with caiso-275's
  successor object ("CAISO commitment, not the import offer"), and it is that lane's, not this one's.
* **DO-NOT-REDO (rule 28 a), added:** an RTM-basis offer surface for CAISO CC. Measured FLAT on
  the exact instrument; do not re-fetch or re-derive it without a new question.

## 4. Housekeeping done here

* The caiso-281 quarter aggregates (34 × `agg/` + `agg_dam/`, 174 MB, written by the defective
  rung convention) are **deleted from `main`** (rule 26; git history is the record). Kept: the
  README (now marked superseded), the shard manifests and verbatim samples (a test fixture), and
  the caiso-282 probe outputs.
* `results/rtm-intake/caiso283/` (4.7 MB) carries the eight exact reductions with metas
  (`git_sha` f7534746 on every one, parquet sha256s verified by the parent before archiving).
* Shard branches, immutable recovery SHAs: 2022 DAM `733868ed`, 2022 RTM `d50968b4`,
  2023 DAM `88e61e82`, 2023 RTM `c02ccc2c`, 2024 DAM `b2759091`, 2024 RTM `a9b12811`,
  2025 DAM `1720a79d`, 2025 RTM `985ad7e5`. All eight shards archived after verification
  (rule 33 a). The bundles are now on this branch, so the shard branches carry nothing unique.
* `data/raw/caiso-public-bids/README.md`: the RTM "DATA NEEDED" paragraph is retired.
* The raw zips (~2.4 GB per RTM year) lived only on the shard containers and are gone; the
  reductions are the deliverable and the fetcher regenerates the zips (~1.7 h per market-year).
