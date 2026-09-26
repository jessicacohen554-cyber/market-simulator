# PRECOMMIT — NWPP-NEXT-5: EIA-860 standby (SB) units admitted by status alone, 2019–2025

**Lane:** NWPP-NEXT-5, after keeper #11 `2026-09-26-nwppnext4-coal-nested` (bundle `results/calibration/nwppnext4_span`).
**Arm id (on registration):** `2026-09-26-nwppnext5-standby`.
**Lever:** queue item 2 (SNV unserved load and SB admission), built as `ScenarioConfig.admit_standby_units`, a new
default-off, ISO-agnostic bool armed for NWPP only (in this recipe, via `--set`).
**Why not queue item 1 first:** its phase 0 ran this session and ends at an owner design ruling, as the handoff
requires. Its result is negative for C4. See `FINDING-nwppnext5-coal-take-obligation-design-2026-09-26.md`: an
admissible prior-year take obligation is a volume lever, and every price-shaped emulation lowers C4 r. Q1–Q6 there go
to the owner. So the LP budget goes to item 2.
**Written before any leg is solved.** The parent session runs no LP (rule 32(a)).

## 1. Phase 0 (zero LP)

### 1.1 What the flag admits (EIA-860 vintage per year; 2025 = the 2025 ER snapshot)

| Year | Fleet gens off → on | Added MW | Fredonia 607 (PSEI → **NWPP-NW**) | Sun Peak 54854 (NEVP → **NWPP-SNV**) | Other SB |
|---|---|---|---|---|---|
| 2019 | 468 → 503 | 579.5 | 280.0 MW, HR 9.000 | 222.0 MW, HR 13.099 | 77.5 |
| 2020 | 460 → 495 | 579.5 | 280.0, 9.000 | 222.0, 12.896 | 77.5 |
| 2021 | 448 → 487 | 590.1 | 280.0, 9.000 | 222.0, 12.987 | 88.1 |
| 2022 | 441 → 481 | 592.1 | 280.0, 9.000 | 222.0, 13.393 | 90.1 |
| 2023 | 442 → 479 | 590.6 | 280.0, 9.000 | 222.0, 13.447 | 88.6 |
| 2024 | 466 → 503 | 590.8 | 280.0, 9.000 | 222.0, 13.436 | 88.8 |
| 2025 | 445 → 482 | 590.5 | 280.0, 9.000 | 222.0, 13.436 | 88.5 |

- MW are summer capacity from `load_fleet_from_csv('NWPP', year=Y)` with the five measured-heat-rate flags on.
- "Other" is small oil/IC/diesel, one 8.5 MW biomass unit and the 9 MW Univ. of Oregon CHP.
- SB run-of-river hydro routes through the hydro loaders and is **not** reached (census: ≤ 0.08 TWh/yr).

### 1.2 Correction to the handoff's SNV claim

The handoff stated that adding 598 MW would cover 60–92 % of the SNV shed. **That treats Fredonia as an SNV unit, and
it is not.** Fredonia is in PSEI, which is zoned NWPP-NW. Only Sun Peak (222 MW) sits in SNV. Computed from keeper
#11's `hourly/system_<Y>.parquet` as the upper-bound share of SNV shed energy covered by a MW block, with every hour
capped at the block:

| Year | SNV shed GWh | hours | max MW | covered by 222 MW | covered by 598 MW (the handoff's figure) |
|---|---|---|---|---|---|
| 2019 | 33.4 | 120 | 1,303 | **57 %** | 89 % |
| 2020 | 193.7 | 455 | 1,588 | **43 %** | 82 % |
| 2021 | 110.1 | 216 | 1,695 | **37 %** | 76 % |
| 2022 | 69.9 | 199 | 1,023 | **49 %** | 91 % |
| 2023 | 20.3 | 60 | 1,218 | **53 %** | 88 % |
| 2024 | 31.8 | 52 | 1,920 | **31 %** | 66 % |
| 2025 | 2.9 | 9 | 770 | **49 %** | 94 % |

Keeper #11 also sheds outside SNV in 2022–2025 (NW 1.6 / 1.0 / 4.1 / 3.5 GWh; INLAND and OR up to 6.6 GWh in
2024). Fredonia can reach part of the NW shed. **Predicted SNV unserved:** falls by at most 31–57 %, and by less
wherever Sun Peak is on outage.

### 1.3 WECC path ratings on the SNV links

- **The modelled links are transcribed correctly** against the WECC 2024 Path Rating Catalog
  (`data/raw/nwpp-planning/transcriptions/2024_Path_Rating_Catalog_Public_v2.txt`):
  - Path 35 TOT 2C, 600 / 580 MW, p. 36.
  - Path 16 Idaho–Sierra, 500 / 360 MW, p. 19.
- **A rated path into SNV is missing.** Path 76 "Alturas Project" (Hilltop 230/345 kV transformer; Hilltop–Fort Sage
  345 kV), p. 69, is rated **N→S 300 / S→N 300 MW**. Fort Sage is NV Energy (Sierra) and Hilltop is on the
  Oregon/California border.
  - `data/raw/nwpp-planning/README.md` §1.3 records "NW ↔ SNV, OR ↔ SNV: not adjacent in the catalogue's path set".
    That is false by Path 76.
  - Terminal ownership has to be read before the link can be booked to NW or OR (Hilltop's owner decides it).
  - **Routed, not built here.** It is a topology change and needs its own lane (rule 19: one mechanism per arm).
- **External SNV seams**, which are interchange and not internal links:
  - Path 24 PG&E–Sierra (p. 25).
  - Path 81 SNTI, 4,533 / 3,790 MW (southern Nevada ↔ the Desert Southwest).
  - These enter as the served measured NEVP interchange schedule (owner ruling N4). The model therefore cannot import
    more in a scarcity hour than NEVP actually scheduled. That is a second, structural candidate for the SNV shed and
    is routed too.

### 1.4 Stated costs (before the solve)

- **Fredonia takes the SPP-49 simple-cycle floor, HR 9.000.** Its eGRID plant rate is 4.918. That is an undercount:
  CAMPD, and so eGRID's heat input, cover only CT3/CT4 (2 × 58.9 MW), while generation covers all four units.
  - `campd_ct_heat_rates_NWPP.csv` was derived on the OP-only fleet and has no row for 607 or 54854.
  - **It is not re-derived here.** Rule 23 re-derives only on a source-data change, and a population change is an
    owner question.
  - Fredonia CT1/CT2 (1984 frame units) are therefore probably priced **below** their true rate, which makes the NW
    CT energy it adds an **upper** figure.
- **CT_PEAKER energy rises.** The census scoping bound is +0.27–1.08 TWh/yr at the class CF, against a benchmarked
  0.25 / 0.31 / 0.46 / 0.31 / 1.00 / 0.59 / 0.11 TWh on these plants.
  - With Fredonia at HR 9.0 the NW part may exceed the class-average CF.
  - The 2020 and 2025 CT over-runs can widen.
- **No outage coverage.** Neither plant has a row in any NWPP CAMPD outage extract (`campd-unit-outages{,-short,
  -e923}-NWPP.csv`, `campd-partial-outages-NWPP.csv`), so both carry class-default availability.
- **C4 coal and C1 CC_REGULAR are not targeted.** Small moves are possible through prices.
- **Promotion** follows the owner's standing structure ruling: promote if structural integrity improves, with every
  regression reported at full magnitude. Admitting units that exist and are benchmarked is the structural claim
  (rule 14).

## 2. G-DRIFT: keeper `git_sha` `fac3d392` → pin (rule 29(b) form 4)

The diff runs over `git diff fac3d392 origin/main` on `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`,
`_validation-source` and `reference`: 158 commits, 23 files.

| Hunk | Class | Why |
|---|---|---|
| `scenarios.py`: seven new fields — `reliability_floor_layup_window_mask`, `caiso_import_gas_coupling_ladder_only`, `caiso_intertie_gap_fill_measured_gas/dam`, `unit_outage_membership_repair`, `unit_outage_unit_fuel_routing`, `nuclear_dormancy_defers_to_vintage_exit` | INERT | All default False and absent from the NWPP recipe. No `_DEFAULT_FLIPS` entry was added. |
| `fleet/arrays.py`: hour-grain predicate, `membership_repair` / `unit_fuel_routing`, nuclear dormancy | INERT | `unit_outage_window_hour_grain` is False in the NWPP recipe, so both old and new predicates are False. The other two are the default-off fields above. |
| `outages.py`: selector extensions (hour-grain, member-repair, layup resolvers) | INERT | Every branch needs a flag that is False here, or runs ERCOT only. |
| `run_calibration.py`: `resolve_coal_budget_arms`, layup shares, CAISO gap-fill args | INERT | Coal budget arms are False (the refactor keeps the raise). Layup is off. The gap-fill args are CAISO only. |
| `campd_bins.py` `_APPLIED_MEASURED_FLAGS ∋ "eia923_identity"`, CC identity rates | INERT | No NWPP artifact carries an `eia923_identity` row, and `campd_*_heat_rates_NWPP.csv` is unchanged since `fac3d392`. |
| `coal_fuel_inventory.reconcile_floors_to_yard_budget` | INERT | Reached only under a coal budget arm, and NWPP has none. |
| `eia930/envelopes.py`, `neighbor_price.py`, `electric_power.py`, `interchange/{caiso,core,spec}.py`, `fuel/{resolve,basis/pjm}.py`, `resolved_inputs.py` | INERT | CAISO intertie, PJM basis and the NYISO layup mask, each behind a default-off flag or a foreign-ISO branch. |
| `paths.py` `EIA_923_GENERATION_FUEL_*`, `scripts/lib/{key_provenance,forecast_parity_registry}.py`, `_validation-source` CAISO files | INERT | Path constants, accounting and CAISO data. |
| **This lane:** `admit_standby_units` (the field plus its cache key, `paths.set_eia860_standby_admission`, the `eia860._rows_to_generators` status seam, the outage cache-key suffix and fleet-status scope, the re-carry SB discard, and the two entry-point setters) | **LIVE** | The arm. Off-path identity is pinned by `tests/unit/data/test_admit_standby_units.py`. The `tests/unit/{config,data}` fail set is identical to the pre-change tree. |

**Verdict:** form 4 is valid. Keeper #11's committed bundle is the control, and no control solve is spent.

## 3. Recipe (per shard): keeper #11's recipe plus ONE `--set`

```
mkdir -p /tmp/n49 && git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/replay_keeper.py /tmp/n49/results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/nwppnext5_<Y> --years <Y> \
  --set eia860_vintage_tracks_solve_year=true \
  --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true \
  --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_partial_outage_windows=true \
  --set mid_vintage_exit_carry=true --set partial_plant_exit_carry=true \
  --set nwpp_demand_plant_basis=true \
  --set coal_committed_nested_on_mustrun=true \
  --set admit_standby_units=true \
  [<Y> in 2019, 2020, 2021, 2022 ONLY:] --set hydro_backfill_year=null \
  --note "NWPP-NEXT-5: keeper #11 recipe + admit_standby_units"
```

## 4. Years, shards and hard stops

**Years (rules 34(c), 35(c), 36):** the registered NWPP set is {2019 … 2025}. All seven are solved, one shard per year.

**Hard stops.** Any miss means STOP, with no push.
1. `git rev-parse HEAD` equals the pin.
2. **Before the solve (zero LP):** the §1.1 fleet check for the shard's year reproduces added MW, Fredonia 280.0 MW
   and Sun Peak 222.0 MW, each within ±0.2 MW.
3. `scenario_config` in `run_config.json` differs from the committed keeper's
   `results/calibration/nwppnext4_span/run_config_<Y>.json` `scenario_config` in **exactly one key**:
   `admit_standby_units` False → True.
4. `meta.json` `hydro_backfill_year` is null for 2019–2022 and 2024 for 2023–2025.
5. `hourly/system_<Y>.parquet`, pass P1: summed `demand` equals keeper #11 ±0.05 TWh. The values are 279.581 /
   292.940 / 289.358 / 298.960 / 280.261 / 290.216 / 302.532.
6. **Arm-live check.** `dispatch/<Y>_P1.parquet` or `hourly/unit_hourly_<Y>.parquet` carries units for plant codes
   607 and 54854. Use a plant-code column if one exists; otherwise match unit ids with the regex `(?<!\d)607(?!\d)`
   or `(?<!\d)54854(?!\d)`. Colstrip 6076 must NOT match.
7. The bundle contains `dispatch/<Y>_P1.parquet`, `hourly/class_hourly_<Y>.parquet`, `hourly/system_<Y>.parquet`,
   `hourly/unit_hourly_<Y>.parquet` and `hourly/hydro_cascade_<Y>.parquet`.

## 5. Reported, never gated; routed

**Reported:**
- C1–C8 per year against keeper #11.
- Class TWh deltas, CT_PEAKER by zone, SNV and NW unserved energy, and C4 coal r.

**Routed:**
- Path 76 Alturas (§1.3).
- The served-NEVP-schedule import rigidity (§1.3).
- The CT heat-rate artifact population (§1.4).
- Lever-1 owner questions Q1–Q6 (`FINDING-nwppnext5-coal-take-obligation-design-2026-09-26.md`).

## 6. Cost and retrievability

- Seven shards run in parallel, about 15–45 min per year.
- Each pushes its full bundle to `claude/nwppnext5-<Y>` (rule 34(a)), using the `.gitignore` negation and a plain
  `git add`.
- The parent composes (2023 leg first), registers, and lands the bundle on `main` before this lane's PR merges
  (rule 33(f)).
