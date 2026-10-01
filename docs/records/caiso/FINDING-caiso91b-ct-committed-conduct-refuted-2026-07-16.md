# FINDING — C1 candidate 2 (Panoche-class committed-tranche gate): refuted by the class's own measured conduct, NO LP

**Session 2026-07-16 (C1 CC-over/CT-under lane, chartered candidate 2). No
solve — a rule-17 evidence adjudication from CAMPD facility-level CEMS
(`CA_{2023,2024,2025}.parquet`, full-8760 grids; absent rows = offline), the
same no-LP refutation class as the SOC-aware storage credit (diagnosis §3).**

## 1. What was chartered

Revisit the G-20 exclusion of CT_PEAKER from the per-plant committed-tranche
mustrun family on CAISO's own evidence — the handoff's reading was "Panoche's
own multi-year evidence is the opposite (block-loaded when online,
tolling/RA contract)". The revisit was gated on rule 17 (driver, window,
forward story) + a D-4 window declaration + estimation-stage CV/LOYO.

## 2. The measured conduct (the rule-17 test, run)

Top-4 plants = 62 % of mapped-class CEMS energy (top-15 = 89.5 %); pooled
2023–2025, online = grossLoad > 5 MW on the full-8760 grid:

| plant | online (all hours) | CF when on (med) | runs (n / med / p95) | days with a run | shape |
|---|---|---|---|---|---|
| Panoche 56803 (388 MW) | **42.0 %** | 0.79 | 1,107 / **7 h** / 24 h | 86 % | belly-off (hod 10-14 ≈ 16-24 %), evening 70-73 %, overnight 34-50 %; winter + summer heavy |
| Sentinel 57482 (850 MW) | 14.3 % | 0.37 | 751 / 4 h / 11 h | 56 % | summer-evening peaker |
| Walnut Creek 57515 (500 MW) | 13.7 % | 0.39 | 571 / 6 h / 12 h | 46 % | summer-evening peaker |
| Marsh Landing 57267 (720 MW) | 5.2 % | 0.28 | 164 / 8 h / 17 h | 16 % | summer-evening peaker |

**No plant in the class's dominant set exhibits committed (always-on)
conduct.** The committed-tranche mustrun family represents plants that stay
online at min-load through their off-hours; the class's flagship cycles
~once per day (1,107 starts in 3 years, median run 7 h) and is fully off in
58 % of all hours. The prior "block-loaded when online, 10,942 pooled online
hours" reading is correct about the CF LEVEL during runs (0.79 median) but
the runs are DAILY BLOCKS, not commitment. There is no committed window to
declare in D-4 — the rule-17 test the charter demanded fails on its own
evidence, the same way G-20's PJM/Dominion evidence failed it.

## 3. What the conduct actually is (where C1-CT routes instead)

* **Panoche = merit-like dispatch at a marginal cost ~$5-10 under the
  model's rung.** Its daily blocks span the evening ramp → overnight →
  morning and vanish in the solar belly — the shape of a unit whose bid
  clears overnight/evening λ but not midday λ. Jan-2024 is the clean
  quantitative case: at the measured staircase citygate (~$5.5/MMBtu
  off-storm), fuel-only SRMC ≈ 9.35 × 5.5 + VOM ≈ $57 sits BELOW the model's
  own January NP15 λ (mean $68, p75 $68) — yet the model dispatched ~0,
  because its carbon- and multiplier-loaded econ rung (~$73) prices it out.
  Under its PG&E toll the offtaker bids variable cost; the admissible
  representation of that bid is the MEASURED CAISO DAM offer surface (OASIS
  Public Bids, 90-day-lag masked curves) — the already-named separate intake
  charter — never a re-tuned multiplier (rule 25) and never a floor.
  2024 confirms: 87–143 GWh in EVERY month (CF 42 %) — year-round mid-merit
  conduct, not scaffolding. (2023 winter is different: Jan-2023 it ran only
  189 h through the gas spike — consistent with cost-based cycling, not
  must-run.)
* **Sentinel / Walnut Creek / Marsh Landing = the evening-merit λ gap.**
  Summer-evening short runs (4–8 h medians) at 5–14 % online are exactly
  what the model would produce if the evening price/stack were right — the
  same defect that owns the C3c summer remainder (diagnosis §4). No
  commitment mechanism applies.

## 4. Disposition

* Candidate 2 is **CLOSED — refuted without a solve** on the class's own
  measured conduct. Any implementable "committed-tranche gate" for these
  plants would have to window on their observed hours, which is a rule-14
  actuals-pin (the already-adjudicated `ct_mustrun_per_plant` family).
* The C1 CT_PEAKER under-run routes to: (a) the **measured DAM offer-surface
  intake** (own charter — the Panoche bid wedge and the class's econ rungs),
  and (b) the **evening-merit λ level** (the summer-evening trio; same lane
  as the C3c summer remainder). Candidate 3 (overnight CC cycling) remains
  the open chartered candidate for the CC side.
* With candidate 1 (online-scoped reserve co-opt, `caiso-91`: measured
  inert, duals zero in all 26,280 hours) and candidate 2 both closed, the C1
  cluster's remaining chartered owner is candidate 3 plus the two named
  routes above — an owner checkpoint before further solves.
