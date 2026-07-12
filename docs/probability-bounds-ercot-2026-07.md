# PB-5 ERCOT probability-band exercise — closeout (2026-07-12)

**No band is published by this document.** This session re-opened PB-5 (the
production ERCOT probability-band run) and ran it partway before the owner
re-confirmed the standing 2026-07-07 deferral (gap register G-35): the model's
scenario-running capability is already demonstrated by thousands of committed
backcast/forecast solves, so a multi-day production batch has nothing left to
prove and was stopped. This document records what the partial exercise
established and closes the workstream back to G-35's deferred state.

## What this session confirms that G-35 could not before

G-35 asserted the PB-0–4 machinery (`matrix.py`, `uncertainty.py`,
`structural_prior.py`, `ensemble.py`) was "landed and unit-tested" but had
**never been exercised end-to-end on a real solve** — only a synthetic fixture
sat behind the public fan-chart page. This session ran it for real:

- **Step 0 measurement (complete):** one real 25-year CAMPD-binned ERCOT
  forecast member = 10,092s (2.8h) under 2-way solver contention, peak
  anon-RSS 6.25 GB; per-year solve cost grows from ~2.5 min (2028) to
  ~10–12 min (2040s) as fleet complexity grows. Confirms the plan's rule-12
  concurrency-2 cap as the right operating point — a 3rd concurrent full-size
  LP OOM-killed a member once during the exercise (mitigated with a 6G
  swapfile, no further incidents).
- **5 real forecast members solved end-to-end, full 2026–2050 horizon,
  via the actual PB-0/PB-2 code paths** (`matrix.py`'s named-case expansion,
  `uncertainty.py`'s LHS/copula sampler, both driving real HiGHS solves
  through `run_scenario_iso`):
  - Matrix (PB-0) cases: `REF` (9ec9c33e8accb6ab, 2.77h), `CORNER-HI-EMIT`
    (35ea26781d65a518, 2.71h), `CORNER-LO-EMIT` (190a977b9bb04986, 3.25h) —
    the deterministic-envelope machinery, verified against the committed
    13-case spec (`configs/scenario_matrix.yaml`).
  - Sampler (PB-2) draws: `draw-0000` (980403af7e771e9b, 4.2h, gas
    factor=2.03×) and `draw-0001` (172b429ec3c95ff9, 3.05h) — real LHS/Gaussian-
    copula draws from the committed spec (`configs/uncertainty_ercot.yaml`,
    seed 7), each correctly resolving to a distinct `ScenarioConfig` and
    solving cleanly through the full forecast horizon.
- **A real coverage bug found and fixed in the process:** the sampler's
  weather-year pool included 2019/2020 for ERCOT (verified only against the
  *backcast* measured-CF path per `WEATHER_YEAR_POOL_BY_ISO`), but the
  *forecast* renewables path derives CF from a different parquet whose
  coverage floor is 2021 — draws landing on 2019/2020 crashed. Fixed in
  `configs/uncertainty_ercot.yaml` (pool restricted to 2021/2023–2025,
  documented inline) and confirmed with a targeted smoke test before
  resuming the batch. This is exactly the kind of defect a synthetic-fixture-
  only exercise cannot surface.
- **Confirmed-retirement forecast channel activated:** curated the ERCOT
  confirmed-exits registry into `data/clean` (2 rows), closing a caveat the
  first (abandoned) PB-5 attempt (`ercot-pb5-band-v1`) had left open.

All 5 members' results are cached on disk (`results/ERCOT/<cache_key>/`,
gitignored per rule 7 — regenerable, not committed) but were **not** assembled
into bands, folded with the structural prior, or published to the fan chart.
At n=2 sampler draws and 3 matrix cases the sample is too thin to support any
quantile estimate the plan's own honesty standard (bootstrap CI attached to
every published quantile) would defend, so no numbers appear here.

## Reusable artifacts from this exercise (kept, not deferred)

The machinery gaps this session's dry-run would have needed anyway are now
built and committed, independent of whether/when the full batch resumes:

- `scripts/pb5_member_slice.py`, `scripts/pb5_matrix_slice.py` — sequential
  per-invocation solve drivers (rule-12 compliant: one invocation, ≤2
  concurrent, years always sequential within a member).
- `scripts/pb5_assemble.py` — assemble/limitations/sensitivity/publish
  pipeline, including loading the PB-3 structural prior from its committed
  fit artifact (`results/ensemble/structural-prior/pb3-statmode-d7-2026-07.json`)
  rather than re-fitting from run payloads the dashboard's retention policy
  has since pruned.
- `configs/uncertainty_ercot.yaml` — the forecast-path weather-pool coverage
  fix described above.
- `configs/uncertainty_ercot_rho00.yaml` / `_rho06.yaml` — the A-2 gas–load
  correlation sensitivity spec variants (paired-seed design).
- `configs/scenarios/ercot_base_2026_2032.yaml` — a truncated-horizon base
  config for cheap sensitivity probes on the golden-tested window.

## Disposition

**G-35 stays deferred**, now with direct evidence (not just inference from
unrelated solves) that the PB-0–4 pipeline itself works end-to-end. The full
production batch (n=64 sampler draws, all 13 matrix cases, published
dispatch-conditional band) remains parked until an owner decides it is worth
a multi-day scheduled run — most plausibly once backcast calibration is
further along and the resulting numbers would carry more decision weight.

No fan-chart payload was published; `frontend/data/forecast/manifest.json`
still points only at `synthetic-fixture-ercot-v1`.
