# ERCOT calibration — best config so far

> **STATUS (2026-06-12, post-run-96): keeper named, calibration CLOSED on
> the corrected fleet.** Run 92 added the missing Kiamichi CC (EIA 55501,
> 1370 MW — the TX-state filter had dropped the one out-of-state ERCOT-BA
> plant), permanently invalidating the run-91 tuning (see the "ERCOT Run 92"
> log entry). The runs 93–96 campaign re-derived the offer-curve response
> vectors on the corrected fleet (fresh Jacobian pure pairs: CC econ_high,
> CC committed) and solved the keeper doses against the measured constraint
> system. **Run 96 is the keeper.** See the "ERCOT Runs 93–96" log entry
> for the vectors and the dose solve.

Keeper: **run 96 / dashboard `run96 lignite keeper`** (2026-06-12, bundle
`results/calibration/run96_lignite_keeper`, highspy 1.14.0). Supersedes
run 91 (no longer reproducible — pre-Kiamichi fleet) and run 92 (the
corrected baseline, 6 class fails). Run 96 = run 92's config + **one move**:
the lignite passthrough-sigmoid cheap-gas floor 0.75 → **0.69** (the run-95
measured endpoint). That flips COAL_LIGNITE 2024 (−1.66 → −0.95 TWh) with
no new fails, no regressions, both gates held → **5 in-scope fails** vs
run 92's 6 and run 91's pre-fix 3 (not comparable — smaller fleet). Against
run 85's old 4-fail mark: the measured vectors show 4 is not reachable on
the corrected fleet — the CC-committed probe (run 95b) refills PRB/ST_GAS
2024 at only +0.47/+0.20 TWh per delta-unit against the +1.53/+1.40 needed,
inside a 2023 coal-split budget that caps the dose at ~0.2 — and the CT
fail is partially structural (AS-deployment energy the energy-only LP
cannot dispatch; IMM 2023 SOM, see the ORDC log entry). Reproduce with:

```
python scripts/run_calibration_full.py --year 2023 2024 2025 \
    --storage-daily-cycling --battery-adder 10 \
    --offer-curve-delta-json <run92/run96 deltas> \  # run_config.json offer_curve_deltas
    --coal-lignite-sigmoid --lignite-floor 0.69 --lignite-ceil 1.00 \
    --prb-floor 0.74 --prb-follower-floor 0.64 \
    --curve-mid 0.35
```

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

Never regress a class vs the keeper. Run 96's five fails: CT_PEAKER all
years (−1.51 / −2.54 / −1.74 TWh — the last ~1–1.5 TWh is potentially
structural AS-deployment energy, do not chase it with fleet-wide levers),
COAL_PRB 2024 (−8.8%) and ST_GAS 2024 (−2.41 TWh) — the 2024 cheap-gas
residual. Honest caveats: ST_GAS 2025 passes at −0.99 with 0.01 TWh margin
(the scarcest budget — any CT cheapening flips it, the run-94 lesson), the
2024 coal split is −8.3% (improved from run 92's −9.3, still failing), and
PRB's multi-year mean sits at −2.5% (+1.3 / −8.8 / −0.1).

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
  baseline bundle is now **run96_lignite_keeper** (moved from
  run92_kiamichi); `availability.parquet` + `scarcity.parquet` are committed
  in the bundle. 2023 LMP MAE 32.1 → 28.0 with the adder; 2024/2025 hold
  the ±$1 gate (7.3 → 7.9, 2.2 → 2.2).

## Results (P1, vs EIA-923 incl. BTM add-back)

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR | −1.6% | +3.7% | +2.0% |
| CC_CHP | +1.0% | +0.8% | +2.1% |
| COAL_PRB | +1.3% | −8.8% | −0.1% |
| COAL_LIGNITE | +5.4% (+0.82 TWh) | −6.8% (−0.95 TWh) | +2.0% |
| CT_PEAKER | −19.7% | −30.8% | −23.5% |
| ST_GAS | −1.8% | −13.2% | −6.5% (−0.99 TWh) |
| nuclear | −0.7% | −0.7% | −0.7% |
| fuel split gas/coal | −2.1 / +2.3% | +0.0 / −8.3% | +2.1 / −1.5% |
| LMP MAE vs actual RT ($/MWh, energy-only) | 32.1 | 7.3 | 2.2 |

Unserved energy 0.000 in all years. Plant guard: Martin Lake / Limestone
2023 at +546/+773 GWh (improved from run 92's +582/+797 — the floor cut
redistributes lignite toward the non-guard plants); Martin Lake 2025
+1.46 TWh (watch on any further coal-side move).

## History

Run 92 (`run92_kiamichi`, the Kiamichi fleet fix) is the corrected-fleet
baseline this keeper stands on; run 91 (`run91_cc_shave055`) was the last
pre-fix keeper and is not reproducible on current inputs; run 85
(`run85_coal_soft`) before it. Runs 93/94/95/95b are the measured probes
(response vectors in the "ERCOT Runs 93–96" log entry) that priced every
live lever on the corrected fleet; their bundles stay in
`results/calibration/`. The structural follow-ups stand: the CT_PEAKER
AS-deployment wedge (ORDC log entry), the CT_CHP 2025 benchmark gap, and
the NP6-576-ER seasonal μ/σ table for the ORDC overlay.
