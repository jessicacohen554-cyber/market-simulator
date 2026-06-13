# ERCOT calibration — best config so far

> **STATUS (2026-06-13, post-run-109a): NEW KEEPER — run 109a, the CT
> AS-deployment overlay + ST availability retune.** The run-103→109 campaign
> built a measured CT_PEAKER out-of-merit deployment floor (the structural
> unlock) and re-ran the ST_GAS availability relief on top of it. Run 109a is
> the keeper: **3 in-scope fails (beats run 97a's 4)**, the ST_GAS deficit
> fixed across all three years, the LMP gate held. Supersedes run 97a. See the
> "ERCOT Runs 103–109" log entry. (run 97a remains the documented prior keeper
> and the basis the campaign stands on.)

Keeper: **run 109a / bundle `results/calibration/run109a_relief11_lig675`**
(2026-06-13, highspy 1.14.0). Run 109a = run 97a's config **plus** three
calibration moves that together fix the gas-side under-clearing run 97a left
structurally diagnosed:

- **`--ct-deployment`** (CT AS/RUC-deployment overlay, default off): a measured
  per-plant *hourly* min-generation floor that pins each CEMS-covered simple-
  cycle peaker to its observed net output ONLY in the out-of-merit hours where
  the RT price was below the unit's marginal cost — the IMM-documented
  ancillary-service / reliability-unit-commitment deployment + reserve-adequacy
  wedge the energy-only LP cannot dispatch. Measured 1.34/1.88/2.22 TWh
  out-of-merit (29.9/35.0/42.5% of covered CT CEMS energy, matching the
  documented 31/38/44%); realized net additive effect 0.84/1.41/1.58 TWh. The
  in-merit hours stay economic, so CT is NOT floored to its full CEMS output. A
  pure LP min-gen bound (no MIP — prices stay LP duals). Built by
  `scripts/derive_ct_deployment.py` → `inputs/calibration/
  ct_deployment_floor_ERCOT.parquet`; applied in
  `fleet.generators_to_fleet_arrays` (`ScenarioConfig.ct_deployment_overlay`).
  Fixes CT 2023 (−1.53 → −1.08) and lifts CT 2024/2025.
- **`--wefor-residual 0.11 --wefor-relief-groups ST_GAS,ST_CHP`**: the ST_GAS/
  ST_CHP forced-outage rate is capped at an 11% residual (the CAMPD overlay
  already carries the ≥5-day outages), modeling the real ST availability the
  full statistical WEFOR understates. With CT held up by the deployment floor,
  this relief now lands: **ST_GAS 2024 −11.0% → −5.1%, all three years pass**
  (2023 +5.4%/+0.91, 2024 −5.1%/−0.93, 2025 +1.7%/+0.26). Relief 0.11 threads
  the per-year asymmetry — gentler underfills 2024, stronger overshoots 2023.
- **`--lignite-floor 0.675`** (was 0.69): the CT overlay displaces marginal
  cheap-gas lignite in 2024, so the lignite sigmoid passthrough floor is eased
  0.69 → 0.675 to recover it; 0.675 is the thread (2023 +6.0%/+0.92 and 2024
  −6.1%/−0.85 both pass — 0.69 fails 2024, 0.66 floods 2023).

Reproduce with:

```
python scripts/run_calibration_full.py --year 2023 2024 2025 \
    --storage-daily-cycling --battery-adder 10 \
    --offer-curve-delta-json <run92/run96/run97a deltas> \  # run_config.json offer_curve_deltas
    --coal-lignite-sigmoid --lignite-floor 0.675 --lignite-ceil 1.00 \
    --prb-floor 0.74 --prb-follower-floor 0.64 \
    --curve-mid 0.35 --btm-backfill-year 2024 \
    --ct-deployment --wefor-residual 0.11 --wefor-relief-groups ST_GAS,ST_CHP
```

**The remaining 3 fails are all structurally diagnosed (do not chase):**

- **CT_PEAKER 2023/2024** (−1.08/−1.55): the deployment overlay recovers the
  CEMS-covered out-of-merit wedge (covered plants now match CEMS), but ~1.0–1.2
  TWh/yr of bench sits in **non-CEMS small peakers** (Ector County, Permian
  Basin, Pearsall …) that have no hourly CEMS for the overlay to key off and
  that the merit order cannot reach. The ST relief also costs CT ~0.4 TWh/yr
  (re-ordering the low-merit stack). Honestly diagnosed, not overlay-reachable.
- **COAL_PRB 2024** (−10.6% / −4.64 TWh): the documented cheap-gas year-gradient
  residual (run 90), now **deepened ~0.7 TWh** by the CT overlay displacing
  marginal PRB under fixed demand in the cheap-gas year. This is the cost of the
  CT/ST volume fix — accepted under the PRB carve-out. Do NOT chase (cheapening
  PRB floods 2023/2025; the CC and ST bid levers crater their classes — runs
  101/105/109b).
- **2024 coal split** (−9.5%, was −8.5% in run 97a): the same CT-displaces-coal
  effect; a ~1-point regression on the already-failing split gate, carried as
  the documented cost of recovering the out-of-merit CT gas. The gas split holds
  (+0.4% in 2024).
  *PRB per-plant detail (the run-90/97a diagnosis, unchanged):* the 2024 PRB
  deficit is **distributed cheap-gas merit displacement across the whole fleet**
  — Spruce, Parish coal, Fayette, Limestone, Martin Lake, Coleto, offset by
  Sandy Creek — not one plant. The plants are **price-responsive and the model
  captures it** (W A Parish whole-plant +0.22 / −1.36 / +0.15 TWh vs CEMS
  2023/24/25, dead-on except the single cheapest-gas year; the earlier −3.7 TWh
  "self-commitment" was a split-plant diagnostic artifact, corrected in
  `_plant_hourly_fit`). Carry under the PRB carve-out; do **not** floor or
  re-benchmark it as price-blind.

**ST_GAS is no longer a structural fail** — run 97a left ST_GAS 2024 at −1.99
(the CPS steamers + Cedar Bayou, the committed band's startup amortization
capping the per-plant gain). The CT deployment floor + the ST_GAS/ST_CHP WEFOR
relief together fill it: the availability deficit run 97a diagnosed was real,
and with CT floored the relief lands without re-cratering CT to a fail.

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
coal split is −8.5% (the distributed cheap-gas PRB/lignite residual,
still failing — fleet-wide, price-responsive, not a single-plant fix),
CT_PEAKER 2025 passes at −0.90 with 0.10 margin, and PRB's multi-year
mean sits at −2.6% (+1.0 / −9.0 / −0.2).

## Config (the knobs that matter)

- **CT AS-deployment overlay (the run-109a structural unlock):**
  `ct_deployment_overlay = on` (`--ct-deployment`). The per-plant hourly
  out-of-merit floor; see the keeper bullets above and
  `scripts/derive_ct_deployment.py` / `outages.ct_deployment_floor_for_year`.
  `ct_deployment_floor_frac = 1.0` (the full measured wedge; a safety knob to
  dial back if a year overshoots its CT bar). Default off — forecast mode and
  any other ISO are byte-identical (no artifact → no-op).
- **ST availability relief (the run-109a Phase-2 retune):**
  `wefor_residual = 0.11` scoped to `wefor_residual_groups = {ST_GAS, ST_CHP}`
  (`--wefor-residual 0.11 --wefor-relief-groups ST_GAS,ST_CHP`). Caps the
  ST_GAS/ST_CHP forced-outage rate at the 11% short-outage residual (the CAMPD
  overlay carries the ≥5-day events). Lands only because CT is floored first.
- `td_loss_factor = 0.0` (EIA-930 demand is generation-side; no gross-up).
- Locked tier-pass-2 family: per-plant CAMPD coal must-run, gas-keyed PRB
  passthrough sigmoid (baseload + follower tiers), `coal_drop_pof`,
  historic outage overlay, per-plant monthly coal pricing — all defaults of
  `run_calibration_full.py`.
- Coal passthrough sigmoids:
  - `coal_lignite_passthrough_sigmoid = on`, **floor 0.675** (the run-109a
    thread to recover the CT-displaced lignite 2024; was 0.69 run 96→97a,
    0.75 run 85→95b) / ceil 1.00.
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
  baseline bundle is now **run109a_relief11_lig675** (moved from run97a);
  `availability.parquet` + `scarcity.parquet` (flat 1400/shift0.5 default) +
  `scarcity_np6shift0.parquet` (published NP6-576-ER table, `--shift 0`,
  canonical) are committed in the bundle. 2023 energy-only LMP MAE 32.3 → 29.3
  with the adder (8% of the summer gap, 22 h >$200 vs 0); 2024/2025 hold the
  ±$1 gate (7.8 → 7.5, 2.1 → 2.1). The published NP6-576-ER seasonal μ/σ table
  (`inputs/calibration/ercot_ordc_lolp_params.csv`, user-fetched 2026-06-13)
  is used with `ordc_lolp_shift_sigma = 0` (the published Average embeds the
  PUCT 0.5σ shift; μ/σ ≈ 0.68 in every season).

## Results (P1, run 109a, vs EIA-923 incl. BTM add-back)

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR | −2.3% | +2.7% | +0.9% |
| CC_CHP | +1.0% | +0.7% | +2.2% |
| COAL_PRB | +0.0% | **−10.6%** | −0.6% |
| COAL_LIGNITE | +6.0% (+0.92 TWh) | −6.1% (−0.85 TWh) | +2.0% |
| CT_PEAKER | **−14.1% (−1.08)** | **−18.8% (−1.55)** | +2.2% (+0.16 TWh) |
| ST_GAS | +5.4% (+0.91) | −5.1% (−0.93) | +1.7% (+0.26 TWh) |
| nuclear | −0.7% | −0.7% | −0.7% |
| fuel split gas/coal | −1.8 / +1.6% | +0.4 / **−9.5%** | +2.2 / −1.8% |
| LMP MAE vs actual RT ($/MWh, energy-only) | 32.3 | 7.8 | 2.1 |

Bold = the 3 in-scope fails (CT 2023/2024, PRB 2024) + the carried 2024 coal
split. Unserved energy 0.000 in all years. Plant guard: Martin Lake /
Limestone 2023 at +380/+704 GWh; Martin Lake 2025 +1.43 TWh (the same watch
item as run 97a — unchanged by this campaign). Vs run 97a: ST_GAS fixed all
three years (2024 −11.0% → −5.1%), CT 2023/2024 improved (−1.53/−2.56 →
−1.08/−1.55), CT 2025 still passes; cost is the 2024 coal split −8.5% → −9.5%
(CT out-of-merit gas displacing marginal cheap-gas PRB) — the documented,
accepted tradeoff (user sign-off 2026-06-13).

## History

Run 97a (`run97a_gas_plants`, 4 fails) was the keeper through 2026-06-13 and
is the basis run 109a stands on; the run-103→109 campaign ("ERCOT Runs
103–109") built the CT AS-deployment overlay (the candidate mechanism run 97a
flagged) and re-ran the ST availability relief on top of it, naming run 109a
(3 fails). Before run 97a:
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
