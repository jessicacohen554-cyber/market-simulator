# Session prompt — ERCOT spatial reliability-deployment (RUC) overlay

ROLE & GOAL
Fix the ERCOT **spatial dispatch imbalance** in the keeper backcast
(results/calibration/run115b_ccduct_prb73_relief06): the model systematically
**over-generates North** and **under-generates South_Central / West / Northeast**
across classes (worst on the high-HR thermal and COAL_PRB). A prior session ruled
out the merit, load-allocation, and inter-zonal-TTC explanations, processed the
ERCOT zonal prices, and validated the correct scoping (see EVIDENCE). Build a
**spatial reliability-deployment overlay**: a per-plant hourly min-gen floor for
the load-pocket thermal fleet, scoped on the **load-zone congestion subset** — the
generalization of the CT deployment overlay (`scripts/data/derive_ct_deployment.py`,
`outages.ct_deployment_floor_for_year`, `ScenarioConfig.ct_deployment_overlay`).
Read docs/calibration-best-so-far.md + docs/calibration-log.md first.

DATA (already processed — artifact committed; do NOT reprocess)
- `data/raw/_validation-source/actual_lmp_zonal_ERCOT.parquet` is committed
  (`year, hour, settlement_point, rt, da`, 8760-hour clock, 15 hub/load-zone points,
  2023-2025). It was built by `scripts/data/derive_ercot_zonal_lmp.py` from the committed
  ERCOT SPP archives in `data/raw/lmp-data/` (`*RTMLZHBSPP_<year>.zip` RTM
  15-min averaged to hourly, `*DAMLZHBSPP_<year>.zip` DAM hourly; each zip = one
  .xlsx with 12 monthly sheets). The deriver is there only to regenerate if needed —
  use the committed parquet directly. (Ignore the `*realtime_zone_csv.zip` /
  `*_smd_hourly.xlsx` in that dir — those are NYISO / ISO-NE.)
- Hubs `HB_NORTH/HOUSTON/SOUTH/WEST/PAN/BUSAVG/HUBAVG`; load zones
  `LZ_NORTH/HOUSTON/SOUTH/WEST/AEN/CPS/LCRA/RAYBN`. Plant→load-zone map:
  `South_Central→avg(LZ_AEN,LZ_CPS,LZ_LCRA)` (Austin+San Antonio+LCRA),
  `West→LZ_WEST`, `Northeast→LZ_RAYBN`, `Houston→LZ_HOUSTON`, `South→LZ_SOUTH`,
  `North→LZ_NORTH`. (`HB_HUBAVG` reproduces the system `actual_lmp_hourly_ERCOT` rt.)

EVIDENCE (verify briefly, then build — do NOT re-derive)
- Zonal net export, 2025 model (gen−load, TWh): Houston −33.6, South_Central −19.7,
  North +11.7, Panhandle +19.1, South +13.4, West +6.6. Thermal miss vs CAMPD (TWh):
  **North +6.1, South_Central −8.7, West −1.8, Northeast −1.0, Houston +0.6.**
  CC_REGULAR 2025 miss by zone: **North +4.5 TWh** (7/14 over) is most of the +3.6
  class over-run — the "efficient over-run" is substantially a North effect.
- **Load allocation is exact** (model zonal demand == ERCOT native-load shares).
  **Inter-zonal TTC is ruled out**: North→Houston 8000→4810 and halving SC imports
  were both exact no-ops (the meshed 7-zone bidirectional network delivers cheap
  power regardless; TTCs already match the NP6-86 SCED archive,
  `scripts/data/derive_ttc_limits.py`). The binding ERCOT constraints are intra-zonal
  pockets the 7-zone model can't form (NE_LOB 15%, Rio Grande Valley
  VALEXP+NELRIO+ZAPSTR+BEARKT ≈21%, HMLTN 7.7%, WHARTN).
- **CRITICAL scoping finding (the prior session's key result):** ERCOT *hubs*
  converge (HB_HOUSTON only +1.0/MWh over HB_NORTH in 2025), so a naïve out-of-merit
  test (CEMS net where price < plant MC) is **~44 TWh on hub AND ~42 TWh on the
  load-zone price** — it does NOT scope (these are expensive high-HR plants running
  below *every* price level in a low-price year). The **LOAD ZONES** carry the local
  signal the hubs wash out: LZ_WEST +10.2/MWh (Permian, hot 16% of hours), LZ_LCRA
  +5.4, LZ_AEN +3.9, LZ_CPS +3.5. The energy the model actually MISSES is the
  **congestion subset**: CEMS net where the plant is economic at its LOAD-ZONE price
  but not at the system hub —
      **net_mw > min_mw  AND  LZ_price > plant_MC  AND  HB_HUBAVG < plant_MC**
  Measured (this is the scopeable wedge): **2.7 / 3.7 / 4.8 TWh (2023/24/25)** —
  ~40% of the ~11.5 TWh net under-zone gap. The remaining ~6.7 TWh ran below even the
  local price = genuine RUC/reliability commitment (the irreducible piece, like the
  CT non-CEMS gap — a separate top-down floor or finer zones, NOT price-recoverable).

MECHANISM TO BUILD (generalize CT deployment, scoped on the congestion subset)
1. `scripts/data/derive_reliability_deployment.py` (or `--class`/`--zone`/`--use-zonal`
   flags on `derive_ct_deployment.py`). For each CEMS-covered thermal plant
   (CC_REGULAR, COAL, ST_GAS, CC_CHP) in the under-running zones (South_Central,
   West, Northeast) and each hour: a **deployment hour** ⇔
       `net_mw > min_mw  AND  LZ_price(plant_zone) > MC  AND  HB_HUBAVG < MC`
   (`MC = plant_avg_HR × hr_mult × gas_price + vom`; LZ/HB from
   `actual_lmp_zonal_ERCOT.parquet`). Floor = measured CEMS net in deployment hours,
   else 0. This recovers the congestion energy the single-system-price LP misses
   WITHOUT over-crediting (expect ~2.7/3.7/4.8 TWh, NOT 44).
2. Wire `ScenarioConfig.reliability_deployment_overlay` (+ `_floor_frac` safety knob)
   and apply as a sparse per-plant hourly min-gen bound in
   `fleet.generators_to_fleet_arrays`, mirroring the CT deployment block (keep
   WEFOR/POF — floor is sparse and below pmax). Default off; ERCOT-backcast only;
   forecast/other-ISO byte-identical.
3. `--report` first: per-year deployment energy + share of covered CEMS by
   zone/class, BEFORE writing the artifact. Confirm it lands at ~the congestion
   wedge, not full CEMS.
4. (Optional second lever for the residual ~6.7 TWh RUC piece, if the congestion
   floor alone doesn't close the North-over/SC-under gap: a top-down zone-level
   floor sized to the measured CAMPD−model net gap, capped at CEMS — or finer zones
   that split the Valley/Permian pockets behind their real binding limits.)

GUARDRAILS / GATE
- Universal gate (this project's standard): every in-scope class, every year,
  **|model−actual| ≤ 0.33% of ISO annual generation** (≈1.5 TWh; ISO gen
  446/463/488 TWh). Report at 0.33% and 0.5% (~2.3 TWh, the energy-only noise floor).
- The overlay must **reduce North over-generation and the SC/West/NE under-run** and
  shrink the **CC_REGULAR North +4.5 TWh**, WITHOUT over-crediting (gas/coal
  fuel-split within ±2.5%). Prices stay LP duals (min-gen bound, no MIP). Don't
  regress CT deployment or the coal/PRB carve-outs. LMP is loose this campaign —
  only flag large swings.

REPRODUCE THE KEEPER (then add `--reliability-deployment`)
    python scripts/run_calibration_full.py --year 2023 2024 2025 \
      --storage-daily-cycling --battery-adder 10 \
      --offer-curve-delta-json <run115b deltas from meta.json> \
      --coal-lignite-sigmoid --lignite-floor 0.675 --lignite-ceil 1.00 \
      --prb-floor 0.73 --prb-follower-floor 0.63 \
      --curve-mid 0.35 --btm-backfill-year 2024 \
      --ct-deployment --cc-duct-peaking \
      --wefor-residual 0.06 --wefor-relief-groups ST_GAS,ST_CHP
Single year ≈ 5 min; 15 GB / 4 cores ⇒ run ≤2 years concurrently (3 OOMs).
The prior session's merit-axis fix (CC econ-ramp restoration) is the artifact
`data/raw/_validation-source/offer_curve_deltas_cc_merit_ramp.json` (CC_REGULAR econ_low
−0.24 / econ_high −0.20; fixes the flat-band cycling). Keep it; this overlay is the
orthogonal spatial axis. Fold both into a clean-gate keeper at the end.

DELIVERABLE
Before/after zonal net-export + thermal-miss-by-zone tables; deployment energy by
zone/class (proving it lands at the ~2.7/3.7/4.8 TWh congestion wedge, not 44);
confirmation the CC North over-run and the SC/West/NE under-run shrink; no class
regresses the universal gate; commitment heatmaps for the pocket plants. Log as a
MEASURED PROBE until it beats run115b; promote per the keeper process.
