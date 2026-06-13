# ERCOT calibration — best config so far

> **STATUS (2026-06-13, post-run-97a): keeper named, calibration CLOSED on
> the corrected fleet.** Run 92 added the missing Kiamichi CC, permanently
> invalidating the run-91 tuning; the runs 93–96 campaign re-derived the
> offer-curve vectors and named run 96 (lignite floor 0.69, 5 fails); the
> runs 97a/97b per-plant campaign then localized the remaining fails to
> specific plants and fixed what was honestly fixable. **Run 97a is the
> keeper: 4 in-scope fails, every remaining fail structurally diagnosed.**
> See the "ERCOT Runs 93–96" and "ERCOT Runs 97a/97b" log entries.

Keeper: **run 97a / dashboard `run97a gas plants`** (2026-06-13, bundle
`results/calibration/run97a_gas_plants`, highspy 1.14.0). Supersedes run 96
(5 fails) and ties run 85's old 4-fail mark on the corrected (larger)
fleet. Run 97a = run 96's config (run 92 offer deltas + lignite floor 0.69)
plus three per-plant/reporting corrections:

- **`--btm-backfill-year 2024`**: the 2025 EIA-923 vintage (monthly-survey
  only) misses whole plants; the BTM add-back keyed off it zeroed San
  Jacinto's (7325) 0.86 TWh while the CAMPD-backfilled benchmark kept the
  plant — a model-vs-bench inconsistency. The backfill carries the prior
  year's class netgen ONLY for plants CAMPD shows generating (CEMS-silent
  cogens stay dropped on both sides). Measured: CT_PEAKER 2025 BTM 0 →
  0.85, CC_CHP +0.14, everything else ~0. **CT_PEAKER 2025 −1.74 → −0.90
  PASSES** — that fail was an artifact, not dispatch.
- **V H Braunig (3612) + O W Sommers (3611) `Pct_Committed` 30 → 40**
  (CPS San Antonio self-scheduled steamers, under-run all years; CAMPD
  grounds the share). Own-gain measured small (+0.17 TWh each — the ST_GAS
  committed band carries heavy startup amortization) with ~+0.4 TWh class
  knock-on: ST_GAS 2023 −0.31 → +0.06, 2024 −2.41 → −1.99 (still fails),
  2025 margin −0.99 → −0.73.

Reproduce with:

```
python scripts/run_calibration_full.py --year 2023 2024 2025 \
    --storage-daily-cycling --battery-adder 10 \
    --offer-curve-delta-json <run92/run96/run97a deltas> \  # run_config.json offer_curve_deltas
    --coal-lignite-sigmoid --lignite-floor 0.69 --lignite-ceil 1.00 \
    --prb-floor 0.74 --prb-follower-floor 0.64 \
    --curve-mid 0.35 --btm-backfill-year 2024
```

**The remaining 4 fails are all structurally diagnosed (2026-06-13
per-plant decomposition; do not chase with fleet-wide levers):**

- **CT_PEAKER 2023/2024** (−1.53/−2.56): 31–44% of actual CEMS CT energy
  runs in hours where RT price < the unit's marginal cost (the AS/RUC
  deployment + RA wedge, 1.4–2.3 TWh/yr), plus ~1.0 TWh/yr of bench in
  non-CEMS small peakers (Ector County, Permian Basin, Pearsall …) the
  merit order can't reach. The model already matches CEMS for the
  CAMPD-covered CT plants.
- **COAL_PRB 2024** (−3.94): essentially one plant — W A Parish (−3.7),
  a never-off self-scheduled baseload (8,760 CAMPD op-hours every year,
  median 38–45% of cap vs the model's 15% floor) with no plant-specific
  F923 coal price. Run 97b measured the committed-share fix BACKFIRING
  (−0.82): under `commitment_screen_coal` a bigger unprofitable committed
  block is decommitted wholesale. Parish's wedge is the same
  self-commitment structure as the CT class.
- **ST_GAS 2024** (−1.99): the CPS steamers + Cedar Bayou; the committed
  band's startup amortization caps the honest per-plant gain measured in
  97a.

## Success bar (size-aware)

Judge each class by size, not a flat percentage (a flat % is loosest exactly
where the system mix is dominated):

- class total **≥ 20 TWh** (CC_REGULAR, CC_CHP, COAL_PRB): within **±5%** every
  year.
- class total **< 20 TWh** (ST_GAS, COAL_LIGNITE, CT_PEAKER, CT_CHP): within
  **±1 TWh** (absolute) every year.
- CT_CHP excluded (known +28% 2025 CHP-benchmark gap).
- **Fuel-split gate (added 2026-06-12):** total gas and total coal generation
  each within **±2.5%** per year. Benchmark sourcing (user judgment,
  2026-06-12): **EIA-923 is the single source of truth for 2023/2024 fossil
  classes including the coal/gas divide** (model totals include the BTM CHP
  add-back, since 923 reports whole-plant output); **2025 fossil is checked
  grid-only against EIA-930** (the 2025 923 vintage is incomplete — the
  CT_CHP +28% gap); **solar/wind are benchmarked against EIA-930 only** and
  sit outside this gate. The two sources differ structurally (930 gas runs
  ~14% below 923 gas on the ~35 TWh of behind-the-meter CHP host supply), so
  never mix them within a year.
- PRB carve-out (user judgment, 2026-06-12): PRB stays on the ±5% class bar
  and its year-to-year spread is accepted as long as the multi-year mean is
  centered (the run-90 gradient finding: 2023 responds at ~2.2× 2024 per
  unit passthrough, so a per-year PRB fix structurally over-trades).
- LMP gate: monthly demand-weighted LMP MAE vs actual RT within **±$1/yr**
  of the corrected-fleet baseline (32.1 / 7.3 / 2.2 — run 92), defined on
  the **energy-only LMP** (raw duals). The ORDC overlay series
  (`lmp_scarcity`) is additive and never gates volumes or LMP.

Never regress a class vs the keeper. Run 97a's four fails are the
structurally diagnosed set above. Honest caveats: ST_GAS 2025 now passes
at −0.73 (the run-97a CPS move bought the −0.99 knife edge 0.26 TWh of
margin; any CT cheapening still spends it, the run-94 lesson), the 2024
coal split is −8.5% (the Parish/lignite cheap-gas residual, still
failing), CT_PEAKER 2025 passes at −0.90 with 0.10 margin, and PRB's
multi-year mean sits at −2.6% (+1.0 / −9.0 / −0.2).

## Config (the knobs that matter)

- `td_loss_factor = 0.0` (EIA-930 demand is generation-side; no gross-up).
- Locked tier-pass-2 family: per-plant CAMPD coal must-run, gas-keyed PRB
  passthrough sigmoid (baseload + follower tiers), `coal_drop_pof`,
  historic outage overlay, per-plant monthly coal pricing — all defaults of
  `run_calibration_full.py`.
- Coal passthrough sigmoids:
  - `coal_lignite_passthrough_sigmoid = on`, **floor 0.69** (the run-96
    move; was 0.75 from run 85 through run 95b) / ceil 1.00.
  - `coal_prb_passthrough_floor = 0.74`, `coal_prb_follower_floor = 0.64`.
  - Gas-mid/slope at the built-in defaults (2.85 / 2.5) for all tiers (the
    run-90 year-gradient finding: do NOT retune these for 2024).
- **`offer_curve_smoothing_mid = 0.35`** (`--curve-mid 0.35`, the run-89 add).
- Fleet: **Kiamichi (EIA 55501) is in the registry + bins** (the run-92 fix)
  with the run-94 cost-side trim committed (split 20/65/15, econ HR mult
  1.06). It still over-runs its EIA actual (6.0/6.8/6.2 TWh vs ~5.2) —
  a within-class watch item; the capacity-withholding trim (peaking share
  15 → 30) was measured dead in run 95 (the over-run is bid-price-driven).
- Per-plant committed shares (the run-97a adds): **Braunig (3612) and
  Sommers (3611) `Pct_Committed` 40** (was 30). NOTE for future per-plant
  CC moves: `cc_committed_per_plant`/`cc_peaking_per_plant` override the
  CSV shares for CAMPD-covered CC plants (the Sand Hill 7900 edit was a
  measured no-op; Kiamichi takes CSV values only because it has no CAMPD
  extract) — per-plant CC offer surgery needs `--plant-tranche-config`.
- **`--btm-backfill-year 2024`** (the run-97a add, in the keeper command):
  CAMPD-gated prior-year 923 carry for plants missing from the incomplete
  2025 vintage (San Jacinto's CT_PEAKER add-back).
- `storage_daily_cycling = on`; **`battery_dispatch_adder = 10.0`** $/MWh;
  nuclear per-year EIA-923 monthly CF overlay (−0.7%/yr).
- Full offer-curve deltas vs calibrated defaults (identical to run 92/91,
  recorded in the bundle's `run_config.json`): CC_REGULAR {committed −0.05,
  econ_low −0.10, econ_high −0.40, peak +0.32}; CC_CHP {econ_high +0.43,
  peak −0.50, pct_peaking −4}; CT_CHP {committed −0.20, econ_low −0.08,
  econ_high +0.10, peak −0.08}; CT_PEAKER {committed −0.34, econ_high
  +0.20}; ST_GAS {committed −0.385, econ_low −0.13, econ_high −0.35, peak
  −1.0}; COAL_PRB {committed −0.04, econ_low −0.30, econ_high +0.44, peak
  +0.082}; COAL_LIGNITE {committed −0.07, econ_low +0.076, econ_high −0.037}.
- **ORDC scarcity overlay** (`docs/ordc-overlay.md`): the post-solve
  baseline bundle is now **run97a_gas_plants** (moved from run96, before
  that run92_kiamichi); `availability.parquet` + `scarcity.parquet` are
  committed in the bundle. 2023 LMP MAE 32.1 → 28.0 with the adder;
  2024/2025 hold the ±$1 gate (7.4 → 8.0, 2.2 → 2.2).

## Results (P1, vs EIA-923 incl. BTM add-back)

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR | −1.7% | +3.6% | +1.9% |
| CC_CHP | +1.0% | +0.8% | +2.3% |
| COAL_PRB | +1.0% | −9.0% | −0.2% |
| COAL_LIGNITE | +5.3% (+0.82 TWh) | −7.0% (−0.97 TWh) | +2.0% |
| CT_PEAKER | −19.9% | −31.0% | −12.2% (−0.90 TWh) |
| ST_GAS | +0.4% | −11.0% | −4.8% (−0.73 TWh) |
| nuclear | −0.7% | −0.7% | −0.7% |
| fuel split gas/coal | −2.0 / +2.1% | +0.1 / −8.5% | +2.1 / −1.5% |
| LMP MAE vs actual RT ($/MWh, energy-only) | 32.1 | 7.3 | 2.2 |

Unserved energy 0.000 in all years. Plant guard: Martin Lake / Limestone
2023 at +498/+760 GWh (improved from run 92's +582/+797 — the floor cut
redistributes lignite toward the non-guard plants); Martin Lake 2025
+1.45 TWh (watch on any further coal-side move).

## History

Run 96 (`run96_lignite_keeper`, the lignite-floor move, 5 fails) was the
keeper for the first half of 2026-06-12→13; run 92 (`run92_kiamichi`, the
Kiamichi fleet fix) is the corrected-fleet baseline both stand on; run 91
(`run91_cc_shave055`) was the last pre-fix keeper and is not reproducible
on current inputs; run 85 (`run85_coal_soft`) before it. Runs 93/94/95/95b
are the measured class-lever probes ("ERCOT Runs 93–96" log entry) and
runs 97a/97b the per-plant campaign ("ERCOT Runs 97a/97b") — 97b measured
the coal committed-share lever backfiring under the commitment screen.
Bundles stay in `results/calibration/`. Structural follow-ups: the
CT/Parish AS-deployment + self-commitment wedge (an explicit deployment
overlay from measured out-of-merit CEMS hours is the candidate mechanism),
the Sand Hill per-plant tranche config (its CT capacity dispatches at the
blended 7.37 CC heat rate — ~1.5 TWh of the CC 2024 over-run), the CT_CHP
2025 benchmark gap, and the NP6-576-ER seasonal μ/σ table for the ORDC
overlay (ercot.com egress-blocked again 2026-06-13).
