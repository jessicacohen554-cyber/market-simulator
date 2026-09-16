# RESULT caiso-282 — the pooled RTM intake: G-REPRO FAILS, the comparison is ABANDONED, and the cause is in the instrument

**Lane:** CAISO calibration · **Date:** 2026-09-16 · **LP spent: ZERO** · keeper unchanged
(`2026-09-12-caiso-275-gascoupling`, CALIBRATED 2023–2025, lone ledgered C3c). Nothing
promoted, nothing registered, no mechanism cell moved, no threshold moved.

**Charter:** `docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md` §4 +
`docs/ADDENDUM-caiso281-rtm-classification-is-independent-2026-09-13.md` §3.
**Method fixed before any number:** `docs/PRECOMMIT-caiso282-rtm-pool-and-gates-2026-09-16.md`
(pushed at `b2101553`). **Instrument:** `scripts/probes/_caiso282_rtm_pool.py`; its three
outputs sit beside the data under `results/rtm-intake/caiso281/_caiso282_pool_*.json`.

## 0. Headline

| gate | result | what it means |
|---|---|---|
| **G-REPRO** | **FAIL** — CC bands +0.098 / +0.142 / +0.098 against ±0.01 | the instrument cannot reproduce the known answer |
| G-POP | FAIL — RTM CC bucket 2.6–3.3× the CAISO CC fleet | the RTM population is not the CAISO fleet |
| **Verdict** | **ABANDONED** — no RTM-BELOW / RTM-FLAT reading is issued | charter §4, applied as written |

Both failures have a **code-level cause identified from the schema and the aggregator source,
not from the residual**, and the first was written into the PRECOMMIT (§1) *before* the number
existed. Neither is fixable from the committed parquet: the raw zips are gone, so the
successor is a re-aggregation, costed in §6.

## 1. G-REPRO — the population reproduces, the bands do not

The committed artifact classified on 2023-01-01..2025-12-31. Run the pooled DAM aggregates
through the derive's own classifier on the same span (less 2025 Q4, not held):

| CC_REGULAR | committed artifact | pooled DAM (this instrument) |
|---|---|---|
| bucket | 46 resources / 11,935 MW / G1 0.871 | **41 / 11,421 MW / G1 0.833** |
| `base_hr` | 7.442 | 7.442 (fleet-geometry constant; reproduces by construction) |
| CC slope, cap-wtd median | not published | 6.54 MMBtu/MWh |
| econ_low | 1.066 | **1.164 (+0.098)** |
| econ_high | 1.072 | **1.214 (+0.142)** |
| peak | 1.386 | **1.484 (+0.098)** |

| CT_PEAKER | committed | pooled DAM |
|---|---|---|
| bucket | 7,391 MW / 0.970 | 10,204 MW / 1.340 |
| econ_low / econ_high / peak | 1.103 / 1.146 / 1.154 | 1.082 / 1.141 / 1.148 (−0.021 / −0.005 / −0.006) |

**The population is reproduced** (41 vs 46 resources, 4 % on MW, G1 inside its bound). **Every CC
band is biased upward by 0.10–0.14, three to fourteen times the tolerance**, while CT's near-flat
curves reproduce to 0.02. That pattern is the signature of the cause recorded in PRECOMMIT §1:

> `aggregate_caiso_bid_ladders._curve_price_at` reads `np.searchsorted(mw, target, side="left")`
> — the first breakpoint at or *above* the target — while the schema declares `segment_mw` as
> the MW at which a price *starts* to apply, so the derive's `_price_at_frac` reads the last
> breakpoint at or *below*. The aggregator samples one rung high.

**Confirmed on the one raw ladder the intake preserved verbatim** (resource 514544, 2023-02-15,
`FINDING-caiso281-rtm-2023q1` §3): the committed `ladder.parquet` holds **$300 at 80 % of
capacity where the derive's convention reads $27.18**; 7 of the 20 grid points sit one rung
high. A CC curve is steep exactly where the CC bands live (the RTM curve population has a
median of **2 rungs**), so "one rung high" often means reading the top price across the whole
body — which is why CC fails by 0.1 and CT, near-flat, does not.

Robustness rows, gating nothing: `hr_cut` 8.4 moves CC to 40 resources and every band by
≤ 0.001. Classifying on the **full** 2021-08..2025-09 span instead admits 104 CC resources /
21.1 GW (G1 1.54 — the DAM control itself leaves the derive's bound), and the bands rise further
(1.277 / 1.396 / 1.571): the extra 2021–22 gas variance admits ~60 resources the artifact never
saw. Reported because the PRECOMMIT fixed the full span as primary; the artifact-span row above
is the fair reproduction and both fail.

**The declared quarter/year capacity approximation is measured and is not the cause**: the
quarter-p98 / year-p98 ratio has p50 = 1.000 in both markets, p05 = 0.84 (DAM) / 0.95 (RTM),
84 % / 94 % of resource-quarters within ±5 %; the partial 2021q3 behaves the same (p05 0.88 /
0.95). 2021q3 stayed in the classifier and out of every band statistic (no 2021 CARB price).

## 2. G-POP — the RTM population is not the CAISO fleet

| RTM, independently classified | CC_REGULAR | CT_PEAKER |
|---|---|---|
| bucket (artifact-span classifier) | 153 res / 35,846 MW / **G1 2.615** | 63 / 8,277 MW / 1.087 |
| bucket (full-span classifier) | 208 / 45,415 MW / **3.313** | 125 / 13,417 MW / 1.762 |
| bound | [0.5, 1.3] | [0.5, 1.6] |
| seq Jaccard vs DAM-classified (diagnostic) | 0.24 / 0.32 | 0.41 / 0.32 |
| **capacity whose seq never bids DAM anywhere in the span** | **62.5 % / 56.6 %** | 23.4 % / 41.7 % |

Three times the CAISO CC fleet passes the gas-coupling gate in RTM, and well over half of it
belongs to resource ids that **never appear in `PUB_DAM_GRP` across four years**. A CAISO-BAA
generator bids the day-ahead market; a WEIM participating resource bids only the real-time
market. The RTM bid file is the WEIM footprint, and an independent classifier on it measures a
different fleet on a different gas basis (RTM CC econ_low 0.77–0.88 — below fuel cost at the
CA citygate, exactly what a Rockies/Permian-priced unit regressed on CA gas looks like).
INCONCLUSIVE by the charter, and it would have been so even had G-REPRO passed.

## 3. The one diagnostic that survives, stated with its limits

The charter's ORIGINAL §2 design — carry the **DAM** classification over by seq — is runnable
now that the intake holds same-date DAM aggregates, and it is the only comparison in which the
population and the (shifted) sampling convention are identical on both sides. On the
DAM-classified CC bucket (41 resources, all 41 with RTM rows), verdict pool 2022-01..2025-09:

| CC_REGULAR, same 41 resources | committed | econ_low | econ_high | peak |
|---|---|---|---|---|
| RTM | 1.071 | 1.131 | 1.153 | 1.332 |
| DAM | 1.060 | 1.136 | 1.184 | 1.348 |
| **Δ RTM − DAM** | +0.011 | **−0.005** | **−0.031** | −0.016 |

CT_PEAKER (86 resources, 81 with RTM rows): Δ = +0.089 / +0.052 / +0.051 / +0.045 (RTM *above*
DAM). Rung counts are matched across markets on the shared population (median 3 rungs both;
74 % of resources identical, 17 % coarser in RTM), so the shift does not bias the pair one way.

**This is a DIAGNOSTIC, not a verdict.** G-REPRO failed, and the charter says the comparison is
then abandoned rather than adjusted. What the diagnostic says, at full magnitude: the same CAISO
combined-cycle resources bid their RTM energy body within 0.03 of their DAM body. It points at
RTM-FLAT. It is not entitled to *be* RTM-FLAT until an instrument that reproduces the known
answer says so.

## 4. What this does NOT do

* No verdict. The RTM-BELOW / RTM-FLAT branch is not taken; the lane is not closed on this.
* C3a stays on RT (RESULT caiso-281 §5.1). No multiplier at any value (rule 1 (c)).
* No edit to `aggregate_caiso_bid_ladders.py` or the derive: the committed parquet was produced
  by the code at HEAD, and changing the code under it would make the data's provenance false.
  `results/rtm-intake/caiso281/README.md` (added) names the convention so no later reader
  consumes the ladders as derive-equivalent.
* No `ScenarioConfig` field, no mechanism tested, no matrix cell (rule 28 duty (b) keys on
  testing a mechanism; none was).

## 5. The keeper's price basis — checked on the owner's instruction, already RT

Owner, mid-session: *"rescore the keeper so it's against rt LMP"*. Scored at HEAD
(`scripts/calibration_verdict.py --run-id …`), every price criterion of both keeper runs already
gates on the real-time series, in every year:

| year | C3a metric label | model / RT actual | C3b actual series | C3c actual |
|---|---|---|---|---|
| 2022 (folded) | vs RT (load-weighted) | 94.07 / 84.49 (+11.3 %, FAIL) | `rt_lw_mon` | RT hourly, 510 h |
| 2023 | vs RT (load-weighted) | 55.89 / 54.17 (+3.2 %) | `rt_lw_mon` | RT hourly, 47 h, coverage 100 % |
| 2024 | vs RT (load-weighted) | 37.55 / 34.65 (+8.4 %) | `rt_lw_mon` | RT hourly, 35 h |
| 2025 | vs RT (load-weighted) | 37.06 / 34.42 (+7.7 %) | `rt_lw_mon` | RT hourly, 8 h |

The DA comparison exists only as the never-gated `da_diagnostic` row. The RT source is
`data/raw/lmp-data/CAISO/CAISO_rtm_hourly_<year>.csv` (three trading hubs, full year in
2022/2024/2025; 2023 short 48 hours, Jan 4–11, filled from DA in the hourly parquet only).
**A rescore would be byte-identical, so none was written.**

## 6. Successor, costed — an owner decision, not taken here

1. **Fix the rung convention in the aggregator** (one line: last breakpoint at or below the
   target, first-rung fallback below the curve start — the derive's `_price_at_frac`), verified
   against the 514544 ladder above.
2. **Re-fetch and re-aggregate all 34 quarter-markets.** ~15 min per quarter-market at
   `--sleep 8`, two-way concurrency measured safe: ≈ 4.5 h wall on two shards, or 17 shards at
   ~30 min each. Zero LP. Rule 34: every shard pushes its aggregate.
3. **Use the charter's original §2 design**: classify on DAM, carry the classification to RTM
   by seq, restrict RTM to the DAM-classified set. G-OVERLAP becomes runnable (the DAM
   classification is computed in the same parent), and G-POP is replaced by the overlap it was
   standing in for. This is what removes the WEIM population, and §3 shows the intake already
   supports it.
4. Re-run G-REPRO first. If it passes on the corrected instrument, the §3 diagnostic becomes a
   verdict under the unchanged 0.05 threshold.

Without step 1 no amount of re-pooling helps; without step 3 no RTM verdict is about CAISO.

## 7. OOM — the workaround, applied

Three concurrent runs of the probe were killed at the 13.36 GiB nested-cgroup ceiling with no
swap (rule 32 (c)(8)). `scripts/prepare_solve_container.py` provisioned a 10 GiB swapfile
(ceiling 13.36 + 10.0 = 23.4 GiB); the same three runs then completed concurrently with exit 0
and outputs byte-identical to the sequential runs. Every solve entry point already calls this
provisioner itself; a zero-LP probe that pools ~3 GB of parquet in pandas needs it invoked by
hand, and that is the one-line workaround.
