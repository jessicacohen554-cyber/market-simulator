# PRECOMMIT — NWPP-NEXT-6: WECC Path 76 link (arm A) and the SB-population CT heat-rate re-derive (arm AB), 2019–2025

**Control:** keeper #12 `2026-09-26-nwppnext5-standby`, using its committed bundle `results/calibration/nwppnext5_span`
(G-DRIFT form 4, §3). No control solve is spent.
**Owner rulings (2026-09-26, this session):**
- Lever 1: **yes, re-derive** `campd_ct_heat_rates_NWPP.csv` with `admit_standby_units` armed in the fleet union
  (rule 23). The basis is a population change caused by the new field, not a residual move.
- Lever 2a: **yes, NW↔SNV arm**. Book Path 76 by EIA-930 BA adjacency, gate it default-off, solve all seven years.

**Design (rule 19, one mechanism per increment).** Two chained arms, seven year-isolated shards each (rule 36):

| Arm | Recipe | Pin | Attributes |
|---|---|---|---|
| **A** | keeper #12 + `nwpp_path76_alturas_link=true` | P1 (code, before the CSV commit) | A − keeper = Path 76 |
| **AB** | arm A + the re-derived CT artifact | P2 (P1 + the CSV commit) | AB − A = the heat-rate re-derive |

AB is the promotable candidate if both increments are structurally sound. A alone is promotable if the re-derive
misbehaves.

## 1. Phase 0 (zero LP)

### 1.1 Path 76: the rating, and where it books

- **Rating.** WECC 2024 Path Rating Catalog (public), printed p. 69: Path 76 "Alturas Project", Hilltop 230/345 kV
  transformer + Hilltop–Fort Sage 345 kV, Accepted Rating **N→S 300 MW / S→N 300 MW**
  (`data/raw/nwpp-planning/transcriptions/2024_Path_Rating_Catalog_Public_v2.txt`).
- **Line owner.** HIFLD Electric Power Transmission Lines: Hilltop Tap–Warner 230 kV is "PACIFICORP AND SURPRISE VALLEY
  ELECTRIFICATION CORPORATION"; Fort Sage–Hilltop 345 kV owner "NOT AVAILABLE" (NV Energy by the catalogue).
- **BA pair — this decides the zone.** EIA-930 NEVP interchange (`data/raw/eia-930-interchange/NEVP interchange
  hourly.parquet`) lists partners BPAT, CISO, IPCO, LDWP, PACE, WALC, and **no PACW leg**. The NEVP↔BPAT leg ranges
  −246 … +182 MW (2023), −211 … +160 (2024), −203 … +161 (2025): the size of a 300 MW line. Card N5 zones are BA
  groups and may not split a BA, so the path books to the BA pair it interconnects: **BPAT (NW) ↔ NEVP (SNV)**.
- One bidirectional link, symmetric 300 MW. Tier 1 candidate (one rated path, one line).
- `data/raw/nwpp-planning/README.md` §1.3 read NW↔SNV as "not adjacent". Corrected in this lane.
- **No double count.** The served interchange (owner ruling N4) is a footprint scalar, `Σ₁₇ (NG − D)`. NEVP↔BPAT is
  internal to the footprint, so it enters only through links. Today it has no link.

### 1.2 Path 76 census on keeper #12's committed hourlies

| Year | SNV shed GWh | shed h | NW price in those h, p50 / max | ≤300 MW NW→SNV covers | measured BPAT→NEVP in shed h, mean |
|---|---|---|---|---|---|
| 2019 | 15.4 | 65 | 25 / 34 | 10.3 GWh (66 %) | n/a (930 pairs from 2023) |
| 2020 | 118.8 | 311 | 18 / 37 | 68.6 (58 %) | n/a |
| 2021 | 73.8 | 160 | 33 / 41 | 38.2 (52 %) | n/a |
| 2022 | 36.0 | 129 | 41 / 89 | 26.1 (72 %) | n/a |
| 2023 | 8.6 | 28 | 32 / 39 | 5.2 (61 %) | 164 MW |
| 2024 | 18.8 | 28 | 21 / 47 | 7.1 (38 %) | 60 MW |
| 2025 | 0.5 | 2 | 28 / 28 | 0.5 (97 %) | 124 MW |

NW is never shedding in an SNV shed hour. The real seam was carrying north-to-south power in those hours.
**Prediction:** SNV unserved falls by at most the "covers" column, and by less where the SNV-internal and other links
also bind.

### 1.3 Stated costs of arm A (before the solve)

- **Over-flow.** The LP arbitrages the link to its rating. Upper bound on keeper #12 prices, counting hours with a
  >$1 spread: N→S 0.80 / 1.11 / 1.52 / 1.88 / 1.62 / 0.72 / 0.61 TWh, S→N 0.31 / 0.25 / 0.23 / 0.09 / 0.10 / 0.30 /
  0.38 TWh. Measured BPAT→NEVP averages 20–28 MW (≈0.2 TWh/yr). The link will likely over-flow the measured seam.
  That is the ordinary behaviour of a rated LP link, **not a reason to derate it** (rules 1 / 13 / 14).
- **Where it lands.** Cheap NW energy displaces SNV gas: SNV CC_REGULAR and CT down, NW hydro/gas up. C1 CC_REGULAR
  2020 (+9.40 TWh) may move toward the band. That is not the reason for the arm.
- C4 coal: small moves through price only.

### 1.4 The CT re-derive (arm AB)

Command, at P1: `python3 scripts/data/derive_campd_ct_heat_rates.py --iso NWPP --admit-standby-units`.
The script is otherwise unchanged. That includes neiso-118's class-preserving union (`union_fleet(fleets,
klass=TARGET_CLASS)`), which landed on `main` after keeper #12's pin.

**Measured at P1 (zero LP):**
- **Without** `--admit-standby-units`, the script reproduces the committed artifact **byte-for-byte**. So neiso-118's
  `klass` union adds nothing for NWPP.
- **With** it, the 86 existing rows are **byte-identical**, and 16 rows are added: plants 607 and 54854, each with
  the pooled row (`year = 0`) plus seven per-year rows. Nothing else moves.

| Plant | Model rate today | Measured pooled | Per-year range | CAMPD units |
|---|---|---|---|---|
| Fredonia 607 (NW, 280 MW) | 9.000 (eGRID 4.918 clamped, SPP-49) | **10.413** | 9.97–10.85 | CT3 10.20, CT4 10.42 gross |
| Sun Peak 54854 (SNV, 222 MW) | 13.436 (eGRID) | **12.893** | 12.84–12.93 | units 3/4/5, 12.57–12.89 gross |

- The artifact's other 12 plants: coverage becomes 14 / 36 plants, 3,096 / 4,188 MW (73.9 %).

**Prediction.** Proxy: back out Fredonia's current offer threshold from its keeper CF on the NW price-duration curve,
scale by HR/9.0, and read the new CF. It is sensitive, because the NW curve is flat near that threshold.

| Year | Fredonia CF keeper #12 | EIA-923 CF | predicted CF |
|---|---|---|---|
| 2019 | 0.20 | 0.08 | ~0.01 |
| 2020 | 0.18 | 0.08 | ~0.00 |
| 2021 | 0.03 | 0.16 | ~0.02 |
| 2022 | 0.10 | 0.11 | ~0.09 |
| 2023 | 0.22 | 0.39 | ~0.15 |
| 2024 | 0.66 | 0.23 | ~0.43 |
| 2025 | 0.64 | 0.04 (partial) | ~0.42 |

- **A partial fix, stated.** 2024–25 stay about 2× EIA-923.
- The measured rate is CT3/CT4's (P&W, 2001) applied to all 280 MW, so the 1984 CT1/CT2 frames remain probably
  under-priced.
- Sun Peak moves 13.44 → ~12.89 (−4 %), so its energy may rise slightly.
- CT_PEAKER NW energy falls by roughly 0.2–0.6 TWh in 2024–25.

## 2. Years

The registered NWPP set is {2019 … 2025} (rules 34(c), 35(c), 36). All seven are solved per arm: 14 shards.

## 3. G-DRIFT: keeper `git_sha` `19f2eace` → P1 (rule 29(b) form 4)

The diff runs over `git diff 19f2eace origin/main` on `src/market_sim`, `scripts/run_calibration*.py`,
`scripts/replay_keeper.py`, `scripts/lib`, `_validation-source`, `reference` and `_processed-legacy`: 14 files.

| Hunk | Class | Why |
|---|---|---|
| `scenarios.py`: `ercot_dam_availability_event_cap_per_unit`, `unit_outage_netload_mask_repair`, `miso_winter_gas_daily_delivered` | INERT | Default False and absent from the NWPP recipe. |
| `fleet/arrays.py`: per-unit DAM-availability cap | INERT | Behind `ercot_dam_availability_event_cap_per_unit` and ERCOT-only `partial_outage_unit_deficits(iso="ERCOT")`. The nested `unit_outage_short_windows` read sits inside that `_per_unit` branch. |
| `outages.py`: `-netloadmask-` CSV selectors, `unit_outage_short_active_units`, `high_load_mask` gains `"SPP": "SWPP"` | INERT | The selectors fire only with `unit_outage_netload_mask_repair` (False). The new helper is reached only from the ERCOT per-unit branch. The mask key is SPP's. |
| `fuel/basis/miso.py`, `fuel/resolve.py`, `fuel/__init__.py`, `resolved_inputs.py`, `run_calibration.py` (8 lines) | INERT | `apply_miso_winter_gas_daily_delivered`: MISO-scoped and flag-gated. |
| `scripts/lib/bundle_io.py` | INERT | Provenance capture of CSV names (accounting). |
| `scripts/lib/heat_rate_years.py` `union_fleet(klass=…)` | INERT for the solve | Derive-time only. It **does** enter arm AB's artifact: see §1.4. |
| `_processed-legacy/campd_ct_heat_rates_NEISO*.csv` | INERT | Another ISO's artifact. |
| **This lane:** `nwpp_path76_alturas_link` (field, cache key, `iso_configs.nwpp_path76_alturas_links`, `pipeline.ttc.apply_nwpp_path76_link`, the calls in `run_calibration.run_year` and `runner.run_scenario_iso`) | **LIVE, arm A** | Off-path identity is pinned by `tests/unit/config/test_nwpp_path76_alturas_link.py`: same object, same cache key. |
| **This lane:** `derive_campd_ct_heat_rates.py --admit-standby-units`, and the re-derived `campd_ct_heat_rates_NWPP.csv` at P2 | **LIVE, arm AB only** | The CSV commit lands after P1. |

**Verdict:** form 4 is valid. Keeper #12's committed bundle is the control for arm A, and arm A is the control for
arm AB.

## 4. Recipe (per shard)

```
mkdir -p /tmp/n49 && git fetch --depth=1 origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 \
  && git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/replay_keeper.py /tmp/n49/results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/nwppnext6<arm>_<Y> --years <Y> \
  --set eia860_vintage_tracks_solve_year=true \
  --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true \
  --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_partial_outage_windows=true \
  --set mid_vintage_exit_carry=true --set partial_plant_exit_carry=true \
  --set nwpp_demand_plant_basis=true \
  --set coal_committed_nested_on_mustrun=true \
  --set admit_standby_units=true \
  --set nwpp_path76_alturas_link=true \
  [<Y> in 2019, 2020, 2021, 2022 ONLY:] --set hydro_backfill_year=null \
  --note "NWPP-NEXT-6 arm <arm>: keeper #12 recipe + nwpp_path76_alturas_link [+ SB-population CT re-derive]"
```

Arms A and AB run the **identical command**. They differ only in the pin, so they differ only in the CSV.

## 5. Hard stops (any miss means STOP, no push)

1. `git rev-parse HEAD` equals the arm's pin.
2. `sha256sum data/raw/_processed-legacy/campd_ct_heat_rates_NWPP.csv`:
   - arm A: `b5c09a911c4780400acbfa4a340247d89fa190e64a0f1b4d7588094f3321395d` (keeper #12's artifact);
   - arm AB: `29baa2f1ecfa10d9734c7e44cc306a88d527adb28968ea260f3409de37d7ff92`.
3. `scenario_config` in `run_config.json` differs from keeper #12's `results/calibration/nwppnext5_span/run_config_<Y>.json`
   `scenario_config` only in:
   - `nwpp_path76_alturas_link` False/absent → True;
   - keys absent in the keeper and False in the arm (post-keeper default-off fields).
4. `meta.json` `hydro_backfill_year` is null for 2019–2022 and 2024 for 2023–2025.
5. `hourly/system_<Y>.parquet`, pass P1: summed `demand` equals keeper #12 ±0.05 TWh. The values are 279.581 /
   292.940 / 289.358 / 298.960 / 280.261 / 290.216 / 302.532.
6. **Arm-live.** The solve log carries `NWPP Path 76 (Alturas): NWPP-NW<->NWPP-SNV 300 MW appended`.
7. The bundle contains `dispatch/<Y>_P1.parquet`, `hourly/class_hourly_<Y>.parquet`, `hourly/system_<Y>.parquet`,
   `hourly/unit_hourly_<Y>.parquet`, `hourly/hydro_cascade_<Y>.parquet` and `flows.parquet`.

## 6. Reported, never gated

- C1–C8 per year: A vs keeper #12, and AB vs A.
- SNV / NW unserved energy.
- Path 76 flow: annual energy by direction, hours at rating, and its mean against measured BPAT→NEVP.
- Class TWh deltas, CT_PEAKER by zone, Fredonia and Sun Peak GWh against EIA-923, and C4 coal r.

**Promotion** follows the owner's standing structure ruling: promote if structural integrity improves, with every
regression reported at full magnitude.

## 7. Cost and retrievability

- 14 shards in parallel, about 15–45 min per year.
- Each pushes its full bundle to `claude/nwppnext6<arm>-<Y>` (rule 34(a)), using the `.gitignore` negation and a
  plain `git add`.
- The parent composes each arm (2023 leg first), registers both, and lands the promoted bundle on `main` before this
  lane's PR merges (rule 33(f)).

## 8. Launch record (appended after the pins; nothing above it changed)
