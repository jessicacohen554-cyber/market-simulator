# PRECOMMIT caiso-282 — pooling the RTM intake and applying the caiso-281 gates

**Lane:** CAISO calibration · **Date:** 2026-09-16 · **LP budget: ZERO** · keeper unchanged
(`2026-09-12-caiso-275-gascoupling`). **Pushed before any pooled number exists.**

**Charter (thresholds NOT moved here):**
`docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md` §4 and
`docs/ADDENDUM-caiso281-rtm-classification-is-independent-2026-09-13.md` §3.
This document fixes only the *computational choices* the charter left to the parent, so that
none of them can be chosen after a number is seen.

## 1. THE INSTRUMENT AS FROZEN — and one code-level fact recorded before any number

The 17 quarter aggregates under `results/rtm-intake/caiso281/<q>/{agg,agg_dam}` were written by
`scripts/data/aggregate_caiso_bid_ladders.py` from raw zips that no longer exist on any reachable
disk. Their content is therefore the instrument; nothing about it can be re-run here.

| held | RTM | DAM |
|---|---|---|
| quarters | 17 (2021q3 .. 2025q3) | 17 (same) |
| span | 2021-08-15 .. 2025-09-30 | 2021-08-16 .. 2025-09-30 |
| 2021q3 | 46 days (partial) | 46 days (partial) |

**Recorded from code, not from data.** `data/dictionary/schema/dam-public-bids.schema.yaml`
§"Bid MW semantics" declares `segment_mw` as the cumulative MW *at which the price starts to
apply*. The derive's `_price_at_frac` reads the **last** step at or below the target MW, which is
the step covering that MW under the declared semantics. The aggregator's `_curve_price_at` reads
`np.searchsorted(mw, target, side="left")` — the **first** breakpoint at or *above* the target —
which under the same semantics is the **next rung up** whenever the target is not exactly a
breakpoint. Both market runs were aggregated with the same code, so the RTM-vs-DAM *pairing* is
internally consistent, but the level of every sampled price carries a one-rung upward shift
relative to the derive's convention. **Whether that shift matters at the charter's tolerance is
exactly what G-REPRO exists to decide, and G-REPRO is applied unchanged.** It is recorded here so
that a G-REPRO miss has a stated code-level candidate cause *before* the miss exists, and so that
nobody can later claim the cause was found by reading the residual.

## 2. THE REPRODUCTION METHOD — every choice fixed here

The derive's own parameters and functions are imported from
`scripts/data/derive_caiso_offer_surface.py` (`BODY_FRAC` 0.35, `GAS_SLOPE_RANGE` [4, 18],
`GAS_MIN_R` 0.6, `GAS_MIN_DAYS` 120, `MIN_CAP_MW` 20, `VOM_BY_CLASS`, `CO2_FACTOR` 0.057,
`ECON_LOW_SHARE`, `G1_BOUNDS`, `_gas_staircase`, `_fleet_geometry`, `locate_st_cut`,
`_assign_classes`, `_wquantile`). Nothing is re-typed.

1. **Year capacity** — `p98` of `hour_max_mw` per resource per **calendar year**, pooled across
   that year's quarters from `hourly.parquet`. Resource-years with cap < 20 MW drop, as in the
   derive. The derive's own cap is `p98` over all segment rows rather than over hourly maxima; the
   difference is part of what G-REPRO tests.
2. **Grid rescale** — a year-capacity fraction `f_y` is read from the 20-point quarter grid at
   `f_q = f_y × cap_year / cap_quarter`, by linear interpolation (the aggregator's own choice for
   `body_px_quarter_cap`), clamped to the grid ends. The **quarter/year capacity ratio
   distribution is reported** per market (p05 / p50 / p95, and the share within ±5 %), with
   2021q3 shown separately because its quarter-p98 stands on 46 days.
3. **Body probe** — price at 0.35 × year capacity per resource-day (the parquet's per-day
   hour-median). Gas regressor: the derive's flow-day staircase keyed on the parquet `date`
   (the OASIS `STARTDATE`, the local operating day — the same local-day key the derive builds).
4. **Classification** — Theil–Sen slope of body price on gas over **every pooled day
   2021-08-15 .. 2025-09-30**, per market, independently (addendum §2). Gates as the derive's:
   slope in [4, 18], `r ≥ 0.6`, `≥ 120` days with `gas.std() ≥ 0.5`, `min_mw ≥ −1` (from
   `hour_min_mw`). Two cuts, both the derive's own: **`hr_cut = 8.5`** and `st_cut` located by
   `locate_st_cut` on the CT-side density (three-way classification, CC + CT consumed, ST_GAS
   reported — the committed artifact's `--st-split-report-only` construction).
   *The addendum §2 wrote "`--hr-cut 8.4`"; the committed artifact's provenance carries
   `hr_cut: 8.5` and the derive's default is 8.5. G-REPRO reproduces the artifact, so 8.5 is the
   primary cut; 8.4 is reported as a robustness row and gates nothing.*
5. **Band statistics** — the derive's windows from the model's class geometry
   (`pct_committed` / `pct_peaking` / `econ_low_share`). Per resource-day, the band price is the
   integral of the grid-sampled step function over the window (price at grid point `f_k` applies
   on `(f_{k−1}, f_k]`, `f_0 = 0`), divided by the window width — the grid's exact analogue of
   `_band_price`. Then `mult = (band_price − VOM) / (base_hr × (gas + 0.057 × carbon_year))`,
   resource-**year** median over days, capacity-weighted class median across resources with the
   derive's weight (the resource's first classified year capacity).
6. **Two pools, fixed.**
   * **G-REPRO pool:** DAM, 2023-01-01 .. 2025-09-30. The committed artifact was derived on
     2023-01-01 .. 2025-12-31 (1,095 of 1,096 dates); **2025 Q4 is not held** and this is stated
     rather than hidden. The artifact's own LOYO worst-deviation (0.011 / 0.025 / 0.077 on
     econ_low / econ_high / peak) bounds what a year-composition difference can do.
   * **Verdict pool:** both markets, **2022-01-01 .. 2025-09-30**, the same dates in each.
     **2021 is excluded from band statistics** because `STATE_CARBON_PRICE_BY_ISO["CAISO"]` has
     no 2021 row (an open, registered gap in `constants.py`, not a value this lane may invent);
     2021 days remain in the classifier, which needs no carbon price.
   * Robustness rows, gating nothing: 2023–2025 only; per year; `hr_cut` 8.4.

## 3. THE GATES — charter values, verbatim

* **G-REPRO (hard stop).** Pooled DAM must reproduce CC_REGULAR `base_hr` 7.442 (±0.02) and
  bands econ_low 1.066 / econ_high 1.072 / peak 1.386 (±0.01 each). **`base_hr` is the model's
  fleet-geometry constant in the derive, not a measured quantity, so it reproduces by
  construction; the three bands are the substantive test.** The CC bucket's capacity-weighted
  median Theil–Sen slope is reported beside it as the measured base-HR analogue, gating nothing.
  A miss on any band → **the comparison is ABANDONED, no verdict is issued**, and §1's recorded
  candidate cause is reported as what a re-aggregation would have to fix.
* **G-POP.** RTM G1 ratios inside CC_REGULAR [0.5, 1.3] and CT_PEAKER [0.5, 1.6]; outside →
  INCONCLUSIVE. Seq Jaccard (RTM-classified vs DAM-classified sets, per class) is a diagnostic.
* **Verdict** (only if G-REPRO and G-POP pass), on **CC_REGULAR** — the object every caiso-276..281
  finding names (the market prices at the efficient CC's own heat rate; the model clears one band
  up). CT_PEAKER is reported alongside and decides nothing. `Δ = RTM − DAM` on econ_low and
  econ_high, verdict pool:
  * **RTM-BELOW** — both Δ ≤ −0.05;
  * **RTM-FLAT** — both |Δ| < 0.05;
  * otherwise **INDETERMINATE**.

Whatever returns: C3a stays on RT (RESULT caiso-281 §5.1) and no multiplier is licensed
(rule 1 `[R-STRUCT]` (c)).

## 4. WHAT THIS SESSION DOES NOT DO

No LP. No fetch. No edit to the aggregator or the derive. No threshold moved. No re-derived
artifact written under `data/raw/_validation-source/`. No `ScenarioConfig` field, no mechanism
cell, no keeper change. Instrument: `scripts/probes/_caiso282_rtm_pool.py`; result:
`docs/RESULT-caiso282-…`.
