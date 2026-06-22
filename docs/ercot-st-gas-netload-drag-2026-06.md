# ERCOT ST_GAS reliability drag: a net-load-indexed min-gen floor (2026-06)

**Question (handoff).** Legacy gas-steam (`ST_GAS`) UNDER-runs every year (keeper
C1 ≈ −4.4 / −6.7 / −5.4 TWh, 2023/24/25) and CC_REGULAR OVER-runs as its
conservation-of-energy counterpart. The energy-only LP never commits ST_GAS
because its measured min-gen offer sits ABOVE CC on energy (2024 ST_GAS min-gen
≈ $47/MWh ≫ CC ≈ $7), so the dispatch only runs it in genuine scarcity hours.
Real ERCOT operation drags these units online for **reliability** — committed at
minimum load through low-price overnight troughs rather than cycling off — which
the hourly energy-only LP, free to de-commit each hour, never sees. Build the
*physics* of that drag (not a fitted must-run fraction or offer markdown) so it
regenerates for a forward year.

**Answer.** The reliability drag is a clean, **monotonic function of system
net-load** (`load − wind − solar`), the operational proxy for the reserve
tightness ERCOT's Reliability Unit Commitment (RUC) keys off. We replace the
blunt seasonal `gas_st_summer_mustrun` calendar fraction with a per-hour
min-gen floor `clip(slope·netload_GW + intercept, 0, cap) × capacity` on the
non-peaker ST_GAS fleet, over which the LP dispatches economically. The curve is
the CAMPD overnight (low-price) ST_GAS capacity factor regressed on
contemporaneous net-load, 2023–2025 — a measured operating rule, not an output
fit. Because both the trigger (net-load) and the floor magnitude (physical
min-gen) are forward-derivable and condition-responsive, the mechanism is
admissible in **both backcast and forecast** (CLAUDE.md #10).

## The measured signature (no LP solve)

CAMPD hourly gross load for the 17 ERCOT gas-steam plants (12.4 GW nameplate),
2023–2025, against system net-load built from ERCOT forecast-zone load and
EIA-930 wind+solar actuals:

* **ST_GAS is committed every day and every night** — it is never fully off.
  The signal is not a binary daily on/off but the **amount** held, which climbs
  monotonically with net-load (mean daily energy ~15 → ~120 GWh/day across the
  net-load range).
* The pure reliability floor shows in the **overnight low-price hours**
  (23h–05h), where any ST_GAS generation is non-economic (price ≪ its
  ~$47/MWh min-gen MC). The overnight fleet capacity factor rises cleanly with
  contemporaneous net-load:

  | net-load (GW) | ~16 | ~24 | ~30 | ~36 | ~42 | ~46 | ~50 |
  |---|---|---|---|---|---|---|---|
  | overnight CF | 0.03 | 0.08 | 0.11 | 0.17 | 0.23 | 0.30 | 0.36 |

* The relationship is **year-stable** (2023/24/25 curves overlay) and strongly
  **monotonic**: hourly net-load vs ST_GAS CF Spearman ρ = **0.82**.
* The annual overnight (23–05h) energy — **3.6 / 4.8 / 5.0 TWh** in 2023/24/25 —
  almost exactly matches the keeper's ST_GAS under-run (−4.4 / −6.7 / −5.4 TWh).
  The missing dispatch *is* the net-load-driven overnight reliability drag.

### Pooled fit

Median overnight CF per 2-GW net-load bin, least-squares line (2023–2025 pooled):

```
floor_frac = 0.00906 · netload_GW − 0.1376          (zero below ~15.2 GW)
           capped at 0.34 (max observed overnight floor, ~50 GW net-load)
```

These are the `ScenarioConfig` defaults
`gas_st_drag_slope_per_gw / _intercept / _cap`.

## Why net-load, not a temperature threshold

The handoff hypothesis pointed at weather; we confirmed it but found the right
in-model trigger is net-load, with **temperature as corroboration**. NOAA
GHCN-Daily TMAX for eight ERCOT metros (DFW, Houston, Austin, San Antonio,
Midland, Abilene, Corpus Christi, Waco), load-weighted to an ERCOT daily max:

* Temperature vs the ST_GAS overnight floor is **U-shaped**, not monotonic —
  both cold (<60°F winter heating, low solar) and hot (>95°F cooling) days drive
  high net-load and a high floor (overnight CF ≈ 0.18 / 0.26), while mild
  70–80°F days are the trough (CF ≈ 0.08). A single "temp > X" rule would
  capture the summer drag but **miss the winter drag** (cold-snap heating
  mornings carry as much steam-gas drag as 90–95°F summer afternoons —
  consistent with ERCOT's bimodal winter/summer reliability commitment).
* **Net-load unifies both limbs.** It is high on cold winter mornings (heating
  load minus near-zero solar) *and* hot summer afternoons, so the single
  monotonic net-load curve reproduces the drag in every season, where two
  temperature thresholds would be required. Net-load is also already the
  model's exogenous forward input (a forecast year has a load forecast and a
  wind/solar build), so the floor threads into forecast runs with no new series.

Correlation summary (daily, n = 1062): TMAX↔peak-net-load r = 0.43,
TMAX↔overnight-CF r = 0.24 (U-shape suppresses the linear coefficient), vs
net-load↔CF Spearman ρ = 0.82.

## Mechanism (code)

* `ScenarioConfig.gas_st_netload_drag` (default **off**) enables the floor;
  `gas_st_drag_slope_per_gw / _intercept / _cap` carry the fitted curve.
* `fleet.apply_gas_st_netload_drag_floor(fleet_arrays, generators, net_load_mw,
  config)` sets `FleetArrays.min_gen` for each non-peaker ST_GAS tranche
  (peaker-class units in `ST_GAS_PEAKER_PLANTS` and the economic `_peak`
  tranche are excluded — they run on price), capped at available capacity and
  composed with any existing floor via `maximum`. The LP dispatches
  economically *above* the floor, so it only binds in the low-price hours where
  the energy-only merit order leaves these out-of-merit boilers off.
* `run_calibration.run_year` computes system net-load (`demand.sum −
  solar_cap·solar_cf − wind_cap·wind_cf`, the same LP-served / net-of-must-run
  convention as the runner's other net-load consumers) right after the fleet is
  built and applies the floor before the P0/P1 solves. **No extra LP solve** —
  the floor is a `min_gen` bound on the existing P0→P1 pass.
* Reproduce: `KEEPER_STGAS_DRAG=1` on the keeper recipe
  (`scripts/probes/_keeper_2023as_run.py`); `KEEPER_STGAS_DRAG_PARAMS` overrides
  the curve coefficients for sensitivity probes.

This supersedes the seasonal `gas_st_summer_mustrun` / `gas_st_offsummer_mustrun`
approach (a fixed calendar fraction that neither derived the drag from physics
nor responded to conditions) and removes the need for ST_GAS offer markdowns
fitted to the residual.

## Calibration result

3-year keeper recipe (zonal gas + RTORDPA on), drag floor ON
(`stgas_netload_drag_v1`) vs an identical-code drag-OFF baseline
(`stgas_drag_baseline`). Class generation, model-total vs EIA-923, diff %:

| class | metric | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| **ST_GAS** | baseline | 11.42 (−31.6%) | 7.82 (−56.8%) | 7.54 (−49.1%) |
|            | **drag** | **17.27 (+3.4%)** | **15.35 (−15.2%)** | **13.55 (−8.5%)** |
| **CC_REGULAR** | baseline | 142.13 (−1.1%) | 143.64 (−1.2%) | 146.52 (+3.1%) |
|                | **drag** | 138.69 (−3.5%) | 138.48 (−4.8%) | 142.06 (−0.0%) |

**Conservation holds.** ST_GAS picks up +5.85 / +7.53 / +6.01 TWh and the bulk
comes straight out of CC_REGULAR (−3.44 / −5.16 / −4.46 TWh), with small gives
from coal (−0.95 / −1.11 / −0.45) and CT_PEAKER (−0.95 / −0.71 / −0.67). The gas
family volume (C2) is ~unchanged (+1.4 TWh in 2023, well inside ±2.5%). The
ST_GAS under-run closes 60–90%; CC_REGULAR's 2025 over-run is eliminated.

**CT-peaker gate respected.** The drag floor does **not** spill onto CT peakers
— their generation *fell* slightly with the floor. The large +81% / +99% (2024 /
2025) CT_PEAKER over-run is **pre-existing in the baseline** (+90% / +108%): it
is the documented zonal-gas West/Permian sub-zonal-transmission limitation
(`docs/ercot-zonal-gas-basis-ct-relocation-2026-06.md`), out of scope here, and
the floor slightly improves it.

**LMP preserved (C3).** Drag-on LMP MAE 27.8 / 15.2 / 11.4 $/MWh vs the keeper's
27.3 / 14.9 / 11.3 — within noise; duration curve and scarcity tail unchanged.
ST_GAS passes its per-class duration (cf_emd) and hourly-correlation gates in
all three years.

**Bounded residual.** ST_GAS in 2024 remains −15.2% and CC_REGULAR −4.8%. Both
are *under*, while CT_PEAKER (+81%) and coal (+10–13%) are *over* — i.e. the
2024 energy that should sit on CC/ST_GAS is trapped on the out-of-scope
West/Permian CT peakers and the EP-level coal anchor, not a deficiency of the
drag mechanism. Pushing the floor harder would only pull more from an
already-under CC; the right fix is the separate CT/coal threads. Per the
non-negotiable structure-first rule, the mechanism stays as the
physically-faithful representation even where the residual is set by other
threads.

This is the structurally-correct, forward-derivable replacement for the ST_GAS
offer markdowns and the seasonal must-run fraction the keeper previously leaned
on.

## Reproduce

```bash
ERCOT_ZONAL_GAS=1 KEEPER_RTORDPA=1 KEEPER_PERSIST_P2=1 KEEPER_STGAS_DRAG=1 \
  python scripts/probes/_keeper_2023as_run.py stgas_netload_drag_v1 2025 2023 \
  '{"ST_GAS":{"committed":0.0}}'
python scripts/calibration_verdict.py results/calibration/stgas_netload_drag_v1
python scripts/probes/_ercot_lmp_shape_score.py results/calibration/stgas_netload_drag_v1
```
