# ADDENDUM caiso-281 — G-OVERLAP is UNRUNNABLE as written; RTM is classified INDEPENDENTLY

**Charter:** `docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md`
**Date:** 2026-09-13 · **Written and pushed BEFORE any RTM byte exists** — wave 1 was launched
minutes earlier and its shards have returned nothing. **This amendment is therefore structural,
not result-driven, and that is the only reason it is permitted to touch a pre-registered gate.**

## 1. THE DEFECT IN MY OWN CHARTER

Charter §2 carries the DAM classification over to RTM by masked `RESOURCEBID_SEQ`, and §4's
**G-OVERLAP** gates on *"RTM resource-seqs matching the DAM classification must cover ≥ 60 % of
the DAM-classified CC_REGULAR + CT_PEAKER capacity."*

**That gate cannot be run, because the per-resource DAM classification is not committed anywhere.**
Checked at HEAD: the three committed artifacts under `data/raw/_validation-source/` are all
**class-level aggregates** —

* `caiso_offer_curve_measured.json` → keys `_provenance`, `CC_REGULAR`, `CT_PEAKER`;
* `caiso_offer_surface_condbinned.json` → the same three keys;
* `caiso_offer_surface_summary.csv` → **13 lines**, columns `class, bin, n_units, n_rows,
  rung1..5_mult`.

None carries a seq. The seq-level classification lived only in the derive's memory over a
**gitignored** 422 MB DAM corpus, and reconstructing it means re-fetching all 1,095 DAM trade
dates. **I wrote a gate against an artifact that does not exist.** Recorded plainly because a
charter that quietly drops a gate is worth less than one that says why.

## 2. THE REPLACEMENT, WHICH IS THE BETTER DESIGN ANYWAY

**RTM is classified INDEPENDENTLY, by the derive's own published method, and the comparison is made
at CLASS level — where the committed DAM numbers actually live.**

* Each quarter shard emits per-`(resource_seq, trade_date)` rows: the body probe at
  `BODY_FRAC = 0.35` of capacity, capacity, the band-rung prices, hour coverage. That is
  **exactly the Theil–Sen classifier's own input**, so nothing is pre-judged at shard level.
* The **parent pools every quarter** and runs the published classifier unchanged — Theil–Sen slope
  of body bid price on the CA-composite citygate daily series (trade+1 flow-day staircase), gas
  gate `slope ∈ [4.0, 18.0]`, `r ≥ 0.6`, `≥ 120` resource-days, class split at
  `--hr-cut 8.4` — then computes `base_hr` and the `econ_low / econ_high / peak` bands.
* **Charter §2's refusal of per-quarter classification is UNTOUCHED and is the reason pooling is
  in the parent:** the classifier is identified by the January-2023 citygate spike to
  **$24.29/MMBtu** against a 2023–25 median near $3–4. A quarter is a near-constant regressor.

**What this costs, stated:** the comparison is now between two *independently classified* surfaces,
so a band difference could in principle come from a different resource population rather than a
different ladder. **That is measured, not assumed** — G-POP below replaces G-OVERLAP.

## 3. THE AMENDED GATES

**G-OVERLAP is WITHDRAWN** (unrunnable; §1).

**G-POP (its replacement).** Report, for RTM against the committed DAM surface, the **G1 capacity
reconciliation** the derive already computes per class (`bucket_mw / fleet_mw`, DAM's committed
values: CC_REGULAR **0.871**, CT_PEAKER **0.970**). RTM's ratios must land within the derive's own
published bounds — CC_REGULAR `[0.5, 1.3]`, CT_PEAKER `[0.5, 1.6]`. Outside them, the RTM
population is not the same fleet and the result is **inconclusive**, never a ladder difference.
Additionally report the **resource-seq Jaccard overlap** between the RTM-classified and
DAM-classified sets as a **diagnostic** — informative, and gating nothing.

**G-REPRO is UNCHANGED and is now doing more work.** The pooled aggregator, run over **DAM** zips,
must reproduce `CC_REGULAR base_hr` **7.442** and bands **1.066 / 1.072 / 1.386** to **±0.02** and
**±0.01**. Since RTM is now independently classified, G-REPRO is the *only* thing standing between
this instrument and a spurious difference — **if it fails, the comparison is ABANDONED, not
adjusted.** It requires a DAM re-fetch of the same quarters, which is **added to the plan and
costed** rather than skipped: each quarter's shard fetches **both** market runs for its dates, so
the DAM control is same-dates and same-code, not a comparison against a three-year-old artifact.

**The §4 verdict thresholds — RTM-BELOW at ≥ 0.05, RTM-FLAT at < 0.05 — are UNCHANGED.** Nothing
about this amendment touches what counts as a difference; it changes only how the two ladders are
built, and it makes the test *harder* to pass, not easier.

## 4. CONSEQUENCE FOR THE REMAINING WAVES

Wave 1 (2023 Q1, 2025 Q3) is **unaffected** — its job is liveness, retention boundary, the RTM CSV
layout, per-quarter size and timing, and whether concurrent fetchers trip the OASIS limiter. None
of that depends on classification. Waves 2+ fetch **RTM and DAM for the same dates**, roughly
doubling per-quarter request count (≈ 180 requests/quarter at 8 s ≈ 24 min of spacing), which is
**stated here so the shard budget is set honestly** rather than discovered mid-fetch.
