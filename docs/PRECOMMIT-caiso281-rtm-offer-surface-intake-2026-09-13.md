# PRECOMMIT caiso-281 (second sitting) — the RTM public-bid intake, and the rule for comparing the two ladders

**Lane:** CAISO calibration · **Date:** 2026-09-13 · **LP budget: ZERO** · keeper unchanged
(`2026-09-12-caiso-275-gascoupling`). **Owner-funded** this sitting ("Yes fund it"), on
`docs/RESULT-caiso281-two-objects-not-one-and-the-bias-is-a-basis-artifact-2026-09-13.md` §5.1.

## 1. THE QUESTION, AND WHY IT IS AN INTAKE RATHER THAN A LEVER

The model's measured CC/CT offer ladder is derived from `PUB_DAM_GRP` — CAISO's **day-ahead**
bids. C3a gates on `rt_lw` — **real-time** prices — on the stated ground
(`calibration_verdict.score_price_mean_da_diagnostic`) that a perfect-foresight dispatch LP is a
real-time analogue and that the DART premium is a forward risk premium the LP has no mechanism to
price. **Both choices are individually principled; together they are a basis mismatch**, and
caiso-281's first sitting measured its size: CAISO's implied marginal-HR bias is **+0.533
(t = +4.03, p = 0.0003)** against RT and **−0.158 (t = −0.80, p = 0.43)** against DA.

`data/raw/caiso-public-bids/README.md` has carried the gap as a standing line — *"DATA NEEDED: RTM
public bids (`PUB_RTM_GRP`) are not fetched"*. This closes it.

**Rules.** The RTM ladder is a measured market input on exactly the same footing as the DAM one
(rule 13 `[R-MEASURED]`: the identical construction regenerates for a forward year from forward
drivers). Adopting it would be a rule 23 `[R-FROZEN-DERIVE]` re-derivation justified by a **NEW
SOURCE**, never by a residual. **Its sign is unknown before it is measured — that is what makes it
admissible**, and §4 fixes the verdict for both signs before either is seen.

## 2. THE DECOMPOSITION THAT MAKES QUARTER-SHARDING VALID (and the one that does not)

**The derive's CLASSIFIER cannot be sharded.** It identifies each masked resource's class by
Theil–Sen regression of its body bid price on the CA-composite citygate daily series; that
identification is carried by pooled gas-price variance — the January-2023 citygate spike to
**$24.29/MMBtu** against a 2023–25 median near $3–4. A single quarter is a near-constant regressor
and identifies nothing. **Any design that re-classifies per quarter is invalid and is refused
here.**

**The LADDER can be sharded, because the classification is already done.** The masked
`RESOURCEBID_SEQ` is **persistent across days and years** (README, verified 2026-07-16: 1,160 of
1,278 Jan-10-2024 generator seqs recur on Jul-10-2024, median max-MW drift 0.24 MW). So the
DAM-derived classification is **carried over unchanged** and each quarter shard only re-measures
the **ladder** for resources already classified. Same resources, same classes, **only the market
run differs** — which is the apples-to-apples comparison, and a tighter one than a re-classified
RTM surface would be.

**Declared cost of that carry-over, before the numbers:** a resource that bids RTM under a seq
absent from the DAM classification is unmatched and drops out. **The seq-overlap rate is itself a
reported measurement**, not an assumption, and a low overlap is a stop condition (§4, G-OVERLAP).

## 3. WHAT EACH QUARTER SHARD PRODUCES — and why it is not the zips

Raw daily zips are **gitignored by corpus convention** (the `pjm-energy-offers` precedent; the DAM
corpus is 422 MB / 1,095 dates) and `data/clean` is gitignored-by-design. Neither survives an
ephemeral shard container, so under rule 34 `[R-SHARD-PROMOTABLE]` (a) a shard that pushed neither
would produce **nothing retrievable**. Each shard therefore pushes a **compact per-quarter
aggregate** — per `(resource_seq, trade_date)`: the body probe at `BODY_FRAC = 0.35` of capacity,
the band-rung prices, max cumulative MW, and hour coverage. That is the exact intermediate the
ladder step consumes, ~10³ resources × ~90 days per quarter, a few MB — **pushable, poolable, and
sufficient**. The zips stay on shard disk and are regenerable by the committed downloader.

## 4. THE DECISION RULE — FIXED HERE, PUSHED BEFORE ANY RTM NUMBER EXISTS

**G-LIVE (feasibility, per shard).** `PUB_RTM_GRP` must return CSV zips, not the ERR_CODE-1000
"No data returned" report. A shard that finds its whole quarter dead **STOPS and reports the
retention boundary**; it does not retry around it. *(Register item N-CA-1 records the OASIS bid
archive's retention as unconfirmed, with the LMP boundary at 2023-04-19 as the strong prior. If
that prior holds for bids, most of the span is unreachable and the intake returns that fact.)*

**G-REPRO (the instrument must be trusted before it is believed).** The same aggregation code, run
over **DAM** zips, must reproduce the committed surface's `CC_REGULAR base_hr` **7.442** and bands
**econ_low 1.066 / econ_high 1.072 / peak 1.386** to within **±0.02 on base_hr and ±0.01 on each
band**. **If it does not, the RTM comparison is ABANDONED, not adjusted** — an instrument that
cannot reproduce the known answer cannot be trusted on the unknown one.

**G-OVERLAP.** RTM resource-seqs matching the DAM classification must cover **≥ 60 %** of the
DAM-classified CC_REGULAR + CT_PEAKER capacity. Below that the carry-over of §2 is not supported
and the result is reported as **inconclusive**, never as a ladder difference.

**THE VERDICT, both signs fixed now:**

* **RTM-BELOW** — RTM `econ_low`/`econ_high` band multipliers sit **≥ 0.05 below** their DAM
  counterparts (cap-weighted, pooled over the fetched span): the residual was an **input-vintage
  defect**. The successor is a rule-23 re-derivation on the RTM basis, **screened under rule 29
  `[R-SCREEN]` like any other mechanism** — not promoted off this measurement.
* **RTM-FLAT** — the bands differ by **< 0.05**: the gap is in the **CLEARING**, not the offers.
  The scorer's "the LP has no mechanism to price it" stands, and CAISO's residual is reported as a
  **declared model-class limitation**. **This branch closes the lane and is a real outcome, not a
  failure.**
* Anything between is **INDETERMINATE** and opens nothing.

**Two things this measurement may NOT do, whatever it returns:** it may not re-point C3a at the DA
benchmark (withdrawn at RESULT §5.1 — the LP is an RT analogue), and it may not license a
multiplier at any value (rule 1 `[R-STRUCT]` (c)). **0.05 was chosen as ~1/20 of the DAM
`peak`-band range and is fixed here; it will not be moved after the numbers land.**

## 5. SHARD DISCIPLINE (rule 32 `[R-SHARD]`)

The parent launches, pools, compares and reports; **it fetches nothing itself.** Every shard is
pinned to a **full 40-character SHA**, fetches **only its own quarter**, commits **only its own
aggregate path** with a plain `git add` after a `.gitignore` negation (rule 34 (a) — never
`git add -f`), and is forbidden `git add -A`, any edit under `src/` or `scripts/`, any dashboard
or `frontend/data/**` write, opening a PR, and deleting any result (rule 31 `[R-RETAIN]`).
**A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a
FAILURE.**

**Wave 1 is deliberately TWO shards, not twelve.** `PUB_RTM_GRP` is unverified at this writing and
OASIS rate-limits by source, so a 12-way fan-out risks spending twelve containers on a dead
endpoint or driving them all into exponential backoff. Wave 1 takes the span's **two extremes** —
**2023 Q1** (carries the citygate spike, and is the oldest, so it tests the retention boundary)
and **2025 Q3** (most recent, most likely live) — which together answer liveness, retention,
per-quarter size and timing, **the RTM CSV column layout** (unseen, and the parser cannot be
written without it), and whether two concurrent fetchers trip the rate limiter. **The remaining
ten quarters launch on their report**, sized by what they measure.
