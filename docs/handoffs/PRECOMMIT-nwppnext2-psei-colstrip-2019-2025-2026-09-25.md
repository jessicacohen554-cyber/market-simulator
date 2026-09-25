# PRECOMMIT — NWPP-NEXT-2: PSEI Colstrip double-booking + non-balance demand repair, 2019–2025

**Lane:** NWPP-NEXT-2 (follow-ups after keeper #8 `2026-09-25-nwpp-next-ferc714-partial`)
**Arm id (on registration):** `2026-09-25-nwppnext2-psei-colstrip`
**Written before any leg is solved.** The parent session runs no LP (rule 32(a)).

## 1. What changes, and why (rule 14; FINDING-nwppnext2-psei-basis-2026-09-25.md)

The arm is **one data-construction repair and nothing else**. The recipe, offer curves and flags are all the
keeper's own.

1. **PSEI's Colstrip share is booked by two BAs.** The fix is `constants.EIA930_REMOTE_GENERATION_DOUBLE_BOOKED`:
   PSEI's own published `NG: COL` is removed from its NG and D. NWMT keeps booking all of Colstrip.
   - Expected LP-array effect: 2019 requirement −4.480 TWh, 2020 −2.152 TWh. The C4 coal bench falls by the same
     amounts.
2. **The PSEI 2021-08-02 → 08-16 window is a non-balance reading.** `TI` is NaN and `D == NG` in 336 hours, so the
   window is filled from FERC 714 by the existing gap guard. This is energy-neutral: it shifts 336 hours of zonal
   split and demand/export.
3. **One member-demand builder** (`frames._pool_member_demand`) now serves both the pool total and the zonal
   regroup. This fixes the rule-19 drift in which the 2020 PSEI zonal share was interpolated.

Zero new free parameters (rules 21 / 24). Nothing was selected on a gate (rule 1). The C1 / C4 movement is reported,
never gated.

## 2. Recipe (per shard; identical to PRECOMMIT-nwpp-next §2 except the out-dir and note)

```
mkdir -p /tmp/n49 && git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/replay_keeper.py /tmp/n49/results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/nwppnext2_<Y> --years <Y> \
  --set eia860_vintage_tracks_solve_year=true \
  --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true \
  --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_partial_outage_windows=true \
  --set mid_vintage_exit_carry=true --set partial_plant_exit_carry=true \
  [<Y> in 2019, 2020, 2021, 2022 ONLY:] --set hydro_backfill_year=null \
  --note "NWPP-NEXT-2: keeper #8 recipe + PSEI Colstrip double-booking + non-balance demand repair"
```

- Offer fingerprint: `sha256(json.dumps(sc["offer_curve_by_group"], sort_keys=True))` =
  `6a13731e43c4e60d5ea84fcc08ce0695bb0f5e5287c6568ec7bf2eda75410c61`, the COAL-SUB fold of the keeper curve.
- `authorized_price_tuning`: NONE. Price is UNSCORED (rubric v3.8).
- `unit_outage_short_windows_gas` stays off (cell U).

## 3. Years (rule 34(c) / 35(c))

- The registered NWPP set is {2019 … 2025}. This arm solves **all seven**.
- **Seven shards, one per year** (rule 36).
- 2022–2025 are byte-identical inputs at the array level (FINDING §2), so they are a free drift check against the
  keeper.

## 4. G-DRIFT (keeper `git_sha` `fd35f164a` → pin), rule 29(b)

The command was `git diff fd35f164a HEAD --` over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`,
`_validation-source` and `reference`. Before this lane's commit the diff is 11 files.

| Hunk | Class | Why |
|---|---|---|
| PJM-NEXT `fleet_zone_vintage_coords` (scenarios, cache, runner, zone_assignment, eia860, run_calibration) | INERT | Default-off and absent from the NWPP recipe. |
| R-SOCO-B2 `ISO_BA_EXITS` (constants, ba_membership, arrays, run_calibration_full EIA-923 month share) | INERT | Only SOCO is registered. The helpers return empty for NWPP. |
| run_calibration_full benchmark-union flag read (4 blocks instead of 2) | INERT | `benchmark_membership_vintage_union` is `false` in the keeper's run_config. |
| **This lane** (frames, actuals, constants, curate_zonal_shares, calibration_reference NWPP demand) | **LIVE for 2019–2021, INERT for 2022–2025** | Array-level old/new diff, FINDING §2. |

**Verdict:** form 4 is valid, and the committed `nwppnext_span` bundle is the control. No control solve is spent.

## 5. Shard hard stops (any miss = STOP, no push)

1. `git rev-parse HEAD` equals the pinned SHA.
2. Input sha256 values:
   - `data/raw/campd-unit-outages-NWPP.csv` `73f1b0e812960434a0e4a4ce87fb1f7e38e58b4a39c96e5c22fba69180eb6238`
   - `data/raw/campd-unit-outages-short-NWPP.csv` `d53d6c7bf42a4e72c99f97040eda524d0759d23140a7af0e80d12ee1f695acfc`
   - `data/raw/campd-partial-outages-NWPP.csv` `e5060145a3d0d3d3a29d880f4df83e2dca2523474ff0d29d1b6c41938b9b3dc0`
   - `data/raw/_processed-legacy/campd_coal_heat_rates_NWPP.csv` `5181a7338137181a17ae2cc1fc8a376f740f126c7e4a3555a11dfc4aa418cff2`
   - `data/raw/eia-930-hourly/PSEI hourly.parquet` `545e8df527a6825b73137b9a940a51ad73b285f5dbd7e7ca1af0ca8ae2992172`
   - `data/raw/eia-930-hourly/NWMT hourly.parquet` `c60dca786dba7a11b48520b425a84fba0cf5948a2b070f2669a7fc54778656d3`
   - `data/raw/ferc-714/psei_hourly_planning_area_demand_2018_2024.csv` `7ee7922e55ca2953688697fa630baee29537e96ce9ff17d4de5042cfa5851a47`
3. `run_config.json` `scenario_config` shows:
   - every §2 flag true;
   - `unit_outage_short_windows_gas` false;
   - the §2 offer fingerprint.
4. `meta.json` `hydro_backfill_year` is null for 2019–2022 and 2024 for 2023–2025.
5. Solve-log fingerprints:
   - **2020:** `PSEI EIA-930 demand missing 8659 h` … `lag -1 h` … `scale 1.0619`. The old code read scale 1.19.
   - **2019:** `PSEI EIA-930 demand missing 384 h`.
   - **2021:** `PSEI EIA-930 demand missing 336 h`. The old code logged no PSEI line in 2021.
   - **2022–2025:** no PSEI demand line.
6. The bundle contains `dispatch/<Y>_P1.parquet`, `hourly/class_hourly_<Y>.parquet`, `hourly/system_<Y>.parquet`,
   `run_config.json` and `meta.json`.

## 6. Reported, never gated

- C1–C8 per year against the keeper.
- Class TWh deltas, coal r and CT_PEAKER.
- 2022–2025 are expected to be identical to the keeper. Any delta there is G-DRIFT's to explain.
- Price is UNSCORED. Promotion: the owner's standing instruction is to promote on improved structure with no gate
  regressions; otherwise the promotion question is asked (rule 31).

## 7. Cost and retrievability

- Seven shards in parallel, about 60–100 min each (R-NWPP §8).
- Each pushes its FULL bundle to `claude/nwppnext2-<Y>` (rule 34(a)), using the `.gitignore` negation and a plain
  `git add`.
- The parent composes, with the 2023 leg first, then registers the run and lands the promotable bundle on `main`
  before this lane's PR merges (rule 33(f)).
