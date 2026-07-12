# ERCOT probability-bounded emissions forecast — PB-5 production run (2026-07)

**STATUS: RUN IN PROGRESS — numbers in this file are placeholders until the
assembly step fills them; do not quote until this banner is removed.**

The first real probability-bounded emissions forecast for ERCOT (the calibrated
reference ISO): the landed PB-0..PB-4 machinery driven end-to-end on real HiGHS
solves, forecast mode 2026–2050. Design: `docs/handoffs/probability-bounds-plan-2026-07.md`;
this document is the PB-5 deliverable report that plan's prompt pack requires.

## Headline (placeholders)

| Year | P10 | P50 | P90 |
|---|---|---|---|
| 2030 | TBD | TBD | TBD |
| 2050 | TBD | TBD | TBD |

Published band = parametric ⊕ structural (dispatch-conditional). Fan chart:
`docs/codebase-site/forecast-bands.html#` ensemble `ercot-pb5-band-v2`.

## What was run (filled as phases complete)

- **Step 0 (measurement, complete):** one real 25-year CAMPD-binned ERCOT
  forecast member = 10,092s (2.8h) under 2-way solver contention, peak
  anon-RSS 6.25 GB; per-year cost grows from ~2.5 min (2028) to ~10-12 min
  (2040s) as the fleet complexity grows. Confirmed the plan's rule-12
  concurrency-2 cap is the right operating point (a 3rd concurrent full-size
  LP OOM-killed a member once, before a 6G swapfile was added as margin).
- **Mid-run re-pin (2026-07-12, ~03:35 UTC):** while 2 sampler members were
  ~20% solved, an external merge (unrelated PJM/MISO/capacity-validation work
  plus an AEO-trajectory correction) landed on this branch via a routine
  main-sync and changed `ScenarioConfig`'s resolved field set (10 new fields)
  and 2 field values (`ira_other_clean_last_full_year`/`_phaseout_end`),
  which shifted every downstream cache key. Rather than risk an
  internally-inconsistent band (some members solved under old inputs, some
  under new), the 2 partial members were discarded (~15 min sunk) and the
  **entire remaining batch was re-pinned to a dedicated git worktree**
  (`market-sim-pb5-pinned`, sparse-checked to `src/configs/scripts`, `data`/
  `results`/`frontend` symlinked to the main checkout) so every solve and the
  final assembly compute cache keys from one frozen code snapshot,
  immune to further concurrent-session drift on the shared branch. The new
  field values are a legitimate accuracy improvement (rule 4), so the pin
  adopts them rather than reverting to the stale ones.
- **Phase 1 — n=16 LHS sampler, 2026–2050, seed 7:** IN PROGRESS (pinned).
- **Phase 2 — reduced 3-case matrix (REF + 2 corners), not the full 13:**
  IN PROGRESS (pinned) — re-scoped from the measured per-member cost; the
  corners alone bound the deterministic envelope per the plan's own design
  (one-at-a-time attribution cases dropped for time).
- **Phase 3 — A-2 rho sensitivity, truncated 2026-2032 horizon:** not yet
  started (queued behind phases 1-2 under the rule-12 2-concurrent cap).

## Honest limitations

See `results/ensemble/ercot-pb5-band-v2/honest_limitations.json` (surfaced
verbatim on the fan-chart page) — dispatch-conditional λ(h)=0, datacenter axis
absent, AEO2025 anchors, n=16 vs the n=64 spec batch, weather pool restricted
to 2021/2023–2025 by forecast-path coverage, structural-prior basis-stale
carbon-priced ISOs, sensitivity at paired n=8.

## Findings log (filled as discovered)

- Forecast-path weather coverage gap: `WEATHER_YEAR_POOL_BY_ISO` 2019/2020
  entries fail in forecast mode (generation-distribution parquet floor 2021).
