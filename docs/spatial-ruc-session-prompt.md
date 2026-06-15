# Session prompt — ERCOT spatial reliability-deployment (RUC) overlay

ROLE & GOAL
Fix the ERCOT **spatial dispatch imbalance** in the keeper backcast
(results/calibration/run115b_ccduct_prb73_relief06): the model systematically
**over-generates North** and **under-generates South_Central / West / Northeast**
across classes (worst on the high-HR thermal and COAL_PRB). This is a transmission
/ local-reliability gap, not a merit gap — a prior session ruled out the merit and
TTC explanations (see EVIDENCE). Build a **spatial reliability-deployment overlay**:
a per-plant hourly out-of-merit min-gen floor for the load-pocket thermal fleet,
scoped with **ERCOT zonal/hub prices** — the direct generalization of the existing
CT deployment overlay (`scripts/derive_ct_deployment.py`,
`outages.ct_deployment_floor_for_year`, `ScenarioConfig.ct_deployment_overlay`).
Read docs/calibration-best-so-far.md + docs/calibration-log.md first.

DATA (present in repo — needs processing)
- ERCOT Load-Zone-&-Hub settlement-point prices are committed in
  `inputs/raw-data/lmp-data/`:
    * RTM (real-time, 15-min): `*RTMLZHBSPP_2023.zip`, `*_2024.zip`, `*_2025.zip`
    * DAM (day-ahead, hourly):  `*DAMLZHBSPP_2023.zip`, `*_2024.zip`
  (NOTE: the `*realtime_zone_csv.zip` / `*_smd_hourly.xlsx` files in the same dir
  are NYISO / ISO-NE — ignore them.)
- Each zip contains ONE `.xlsx` (read with `pandas.read_excel(..., engine="openpyxl")`,
  NOT read_csv). Columns: `Delivery Date, Delivery Hour, Delivery Interval,
  Repeated Hour Flag, Settlement Point Name, Settlement Point Type,
  Settlement Point Price`. Hubs: `HB_NORTH, HB_HOUSTON, HB_SOUTH, HB_WEST, HB_PAN,
  HB_BUSAVG, HB_HUBAVG`. Load zones: `LZ_NORTH, LZ_HOUSTON, LZ_SOUTH, LZ_WEST,
  LZ_AEN, LZ_CPS, LZ_LCRA, LZ_RAYBN`. RTM has 4 intervals/hour → average to hourly
  (handle the `Repeated Hour Flag = Y` fall-DST hour; Delivery Hour is 1–24).
- FIRST extend `scripts/derive_actual_lmp.py` (today it keeps only HB_HUBAVG) to
  write `inputs/calibration/actual_lmp_zonal_ERCOT.parquet`
  (`year, hour, settlement_point, rt, da`) on the model's fixed 8760-hour clock.
  Map to the 7 model zones via the LZ load zones (finer than the hubs):
    `LZ_NORTH→North`, `LZ_RAYBN→Northeast`, `LZ_HOUSTON→Houston`,
    `LZ_WEST→{West, Panhandle}`, `LZ_SOUTH→South`,
    `{LZ_AEN, LZ_CPS, LZ_LCRA}→South_Central` (Austin + CPS San Antonio + LCRA).
  (Hub fallback: `HB_NORTH→North/NE/Pan`, `HB_HOUSTON→Houston`, `HB_WEST→West`,
  `HB_SOUTH→South/South_Central`, `HB_PAN→Panhandle`.) Sanity-check that
  `HB_HUBAVG` reproduces the existing `actual_lmp_hourly_ERCOT.parquet` `rt`.

EVIDENCE FROM THE PRIOR SESSION (do not re-derive — verify briefly then build)
- Zonal net export, 2025 model (gen−load, TWh): Houston −33.6, South_Central −19.7,
  North +11.7, Panhandle +19.1, South +13.4, West +6.6. Thermal miss vs CAMPD (TWh):
  **North +6.1, South_Central −8.7, West −1.8, Northeast −1.0, Houston +0.6.**
- CC_REGULAR 2025 miss by zone: **North +4.5 TWh** (7/14 plants over) is most of the
  +3.6 TWh class over-run — the "efficient over-run" is substantially a North effect.
- **Load allocation is exact** (model zonal demand == ERCOT native-load weather-zone
  shares to the decimal). NOT the cause.
- **Inter-zonal TTC is ruled out**: tightening North→Houston (8000→4810, the
  SCED-derived limit) and halving South_Central imports were BOTH exact no-ops. The
  meshed 7-zone bidirectional network delivers cheap North/West/Panhandle power to
  load regardless. TTCs already match the NP6-86 SCED archive (West→North 7287,
  Panhandle 2695, West→SC 2733); `scripts/derive_ttc_limits.py`.
- The binding ERCOT constraints are **intra-zonal pockets the 7-zone model cannot
  form**: NE_LOB 15% (already modeled as Northeast→North), Rio Grande **Valley**
  cluster (VALEXP+NELRIO+ZAPSTR+BEARKT ≈ **21%** of SCED intervals), HMLTN 7.7%,
  WHARTN. The under-zone thermal ran **44 TWh "out of merit vs the hub"** in 2025 —
  i.e. it ran when the *system* price was below its cost because the *local* price
  was elevated (import-constrained pockets). Hub-price scoping OVER-credits 44 TWh;
  this is exactly why **zonal prices are required**.

MECHANISM TO BUILD (generalize CT deployment)
1. New deriver (or `--class`/`--zone` flags on `derive_ct_deployment.py`):
   `scripts/derive_reliability_deployment.py`. For each CEMS-covered thermal plant
   in the **import-constrained zones** (South_Central, West, Northeast; consider the
   Valley LZ if split) and each hour it generated:
       deployment hour  ⇔  net_mw > min_mw  AND  **zonal/hub RT LMP < plant MC**
   (MC = plant_avg_HR × hr_mult × gas_price + vom). Floor = measured CEMS net in
   deployment hours, else 0. Use the plant's **ZONAL hub price**, not HB_HUBAVG —
   this is the whole point; it shrinks the 44 TWh hub-wedge to the genuine local
   out-of-merit subset.
2. Wire `ScenarioConfig.reliability_deployment_overlay` (+ `_floor_frac` safety knob)
   and apply as a sparse per-plant hourly min-gen bound in
   `fleet.generators_to_fleet_arrays`, mirroring the CT deployment block exactly
   (these units keep WEFOR/POF since the floor is sparse and below pmax). Default
   off; ERCOT-backcast only; forecast/other-ISO byte-identical.
3. `--report` first: print per-year deployment energy and its share of covered CEMS
   by zone/class BEFORE writing the artifact. **Guardrail (CT-overlay discipline):
   the floor must be the out-of-merit subset, not full CEMS** — expect roughly the
   net zonal gap (SC ≈ +8.7, West ≈ +1.8, NE ≈ +1.0 TWh in 2025), NOT 44 TWh.

GUARDRAILS / GATE
- Universal gate (this project's new standard, replacing ±5%/±1 TWh): every in-scope
  class, every year, **|model−actual| ≤ 0.33% of ISO annual generation** (≈1.5 TWh;
  ISO gen 446/463/488 TWh 2023/24/25). Report at 0.33% and 0.5%.
- The overlay must **reduce North over-generation and the SC/West/NE under-run**
  WITHOUT over-crediting (net gas/coal fuel-split gate within ±2.5%). It should pull
  North CCs down (helping the CC_REGULAR over-run) as a side effect — verify the CC
  North +4.5 TWh shrinks.
- Prices stay LP duals (min-gen bound, no MIP). Don't regress CT deployment, the
  coal/PRB carve-outs, or the LMP gate (energy-only MAE; the prior user said LMP is
  loose this campaign — only flag large swings).

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

DELIVERABLE
Measured before/after of the zonal net-export + thermal-miss-by-zone table, the
deployment energy by zone/class (proving it's the out-of-merit subset, ~net gap not
44 TWh), confirmation the CC_REGULAR North over-run and the SC/West/NE under-run both
shrink, no class regresses the universal gate, and the commitment heatmaps for the
pocket plants. Log as a MEASURED PROBE until it beats run115b; promote per the keeper
process. NOTE: a separate merit-axis fix (CC econ-ramp restoration) was landed in the
prior session — keep it; this overlay is the orthogonal spatial axis.
