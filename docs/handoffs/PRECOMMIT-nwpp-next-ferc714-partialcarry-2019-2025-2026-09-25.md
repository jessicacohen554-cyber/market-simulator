# PRECOMMIT — NWPP-NEXT: keeper recipe + measured PSEI fill + partial-plant exit carry, 2019–2025

**Lane:** NWPP-NEXT (follow-ups after R-NWPP, keeper `2026-09-24-rnwpp-inputs-span`). **Date:** 2026-09-25.
**Written before any LP is solved.** Every number below comes from zero-LP work in the parent session. The parent
never solves (rule 32(a)). Each year is solved in its own shard (rule 36).

## 0. What this arm is, in one line

The R-NWPP keeper recipe, unchanged, plus two measured-input repairs. Neither is tuned against a residual (rules 1,
13, 14):

1. **The pool member gap guard + FERC 714 PSEI load** (this lane's commit `9e3b40d1`, landed before this doc).
   EIA-930 is missing PSEI demand for 384 hours of 2019 (longest run 192 h) and 8,659 hours of 2020. The pool frame
   used to draw a straight line across those holes. The rule is now:
   * **Holes over 72 h** (the single-BA frame's own `_HOURLY_FRAME_MAX_GAP`) take PSEI's FERC Form 714 Part III
     Schedule 2 hourly load. That load is first reconciled to PSEI's same-year EIA-930 basis. Both terms are measured,
     not chosen:
     * the clock offset with the best first-difference correlation among −1 / 0 / +1 h;
     * the median hourly EIA/FERC ratio.
   * **Net generation** is filled from PSEI's own `NG:` fuel columns. The identity holds to 0.0027 TWh on 2019's
     reported hours.
   * **A hole no measured source closes** now refuses the pool rather than being interpolated.
2. **`partial_plant_exit_carry = true`**, an existing gated `ScenarioConfig` field. `mid_vintage_exit_carry` only
   restores **whole-plant** exits, so it misses a unit that retired mid-year while its sister unit stayed operable.
   This field is the channel that restores those units. It is the root cause of the "Centralia 1 not restored"
   question the handoff raised: plant 3845 stays on the operable sheet through unit 2, so `_mid_vintage_exit_rows`
   drops unit 1 by construction (`fleet/eia860.py:2811-2817`).

## 1. Zero-LP evidence (parent, 2026-09-25)

### 1.1 Pool frame, before → after the guard

The comparison is a byte comparison of `_pool_hourly_frame("NWPP", y)` at the parent commit versus `9e3b40d1`.

| Year | Demand TWh | Changed |
|---|---|---|
| 2019 | 279.2033 → **279.2258** | PSEI's 384 gap hours only. Net generation −0.0232 TWh, interchange −0.0457 TWh. |
| 2020 | 262.2416 (fabricated) → **273.3680** | Before: PSEI drawn through ~101 points. After: FERC × 1.1905 at −1 h, overlap n = 101. |
| 2021–2025 | — | **Byte-identical frames.** No member gap exceeds 1 h. |

**Calibration reference rebuild** (`--isos NWPP`): NWPP 2019 demand moves by +0.0225 TWh and NWPP 2020 is added.
Nothing else moves.

**2020 benchmark:** coal 52.354, gas_cc 62.771, gas_ct 4.097, gas_st 1.649, hydro 130.793, nuclear 9.427,
solar 7.737, wind 27.874 TWh.

### 1.2 PSEI: EIA-930 against FERC 714, the measured regime

| Period | Best offset | Median ratio |
|---|---|---|
| 2019 | −1 h | 1.205–1.218 |
| 2020 (≈100 h) | −1 h | 1.15–1.23 |
| 2021-01-01 onward | 0 h | 0.996–0.999 |

The basis and the clock both change at the year boundary. That is why the fill reconciles within the year and never
splices the raw series.

**Side finding, not repaired here.** EIA-930 PSEI demand for 2021-08-02 → 08-15 sits 1,699 MW below FERC 714 on
average, about 0.573 TWh. No value is missing, so the guard does not see it. It lives in a keeper year (2021) and is
routed.

### 1.3 `partial_plant_exit_carry` census

The census is a fleet-only rebuild of the keeper recipe with the flag on, compared with the keeper
(`scripts/probes/_rnwpp_census.py`).

| Year | Units | Added pmax | Added available TWh | What |
|---|---|---|---|---|
| 2019 | 623 → 628 | 75.0 MW | **0.601** | Kennecott (56163) coal |
| 2020 | 636 → 649 | 1,359.0 MW | **2.779** | Centralia 1 (3845, 670 MW, 2.49 TWh), Colstrip 1–2 (6076, retired 2020-01, 0.29 TWh), Kennecott at 0 |
| 2021 | 634 → 647 | 1,359.0 MW | **0.000** | COD ramp zeroes them; LP columns only |
| 2022 | 628 → 646 | 1,365.2 MW | **0.030** | UW Power Plant ST_GAS 0.026, Sinclair CHP 0.003; the rest at 0 |
| 2023 | 629 → 629 | 0 | 0 | none (`vintage_2023` has no retired sheet) |
| 2024 | 652 → 652 | 0 | 0 | none |
| 2025 | 653 → 679 | 1,370.9 MW | **0.000** | LP columns only |

## 2. Recipe (per shard; offer curves UNCHANGED)

The shard first restores the NWPP-49 bundle from git history into a directory **outside** the repo. It was pruned at
the R-NWPP promotion, and it is the bundle R-NWPP replayed:

```
mkdir -p /tmp/n49 && git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/replay_keeper.py /tmp/n49/results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/nwppnext_<Y> --years <Y> \
  --set eia860_vintage_tracks_solve_year=true \
  --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true \
  --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_partial_outage_windows=true \
  --set mid_vintage_exit_carry=true --set partial_plant_exit_carry=true \
  [<Y> in 2019, 2020, 2021, 2022 ONLY:] --set hydro_backfill_year=null \
  --note "NWPP-NEXT: R-NWPP recipe + FERC 714 PSEI fill (gap guard) + partial_plant_exit_carry"
```

* The recipe was dry-run in the parent with `solve_and_persist` stubbed. For 2019 / 2020 / 2023 it binds
  `partial_plant_exit_carry=True` and the recorded `hydro_backfill_year`.
* The −1 h / scale PSEI reconciliation is computed at load time. There is **no new free parameter** (rules 21/24):
  * the offset is chosen from three candidates by the data's own correlation;
  * the level is the data's own median;
  * the 72 h bar is the pre-existing single-BA constant.
* `offer_curve_by_group` sha256 must be `ac3344c3ef16e3ae63673a92886aa2873fc7090543eb04e6d6abf89fb52c73c2` in every
  leg. `authorized_price_tuning`: NONE (price unscored, rubric v3.8).
* `unit_outage_short_windows_gas` stays **off**. The cell stays U, per R-NWPP §4.

## 3. Years and the rule-35(c) union

* **Registered NWPP year set today:** {2019, 2021, 2022, 2023, 2024, 2025}.
* **This arm solves** {2019, **2020**, 2021, 2022, 2023, 2024, 2025}, which is the whole union plus 2020 (rule 34(c)).
* **Seven shards**, one per year (rule 36).

## 4. G-DRIFT (keeper legs at `b6ce536ad1e7e41e083b81f784f8e94084bbce2f` → pin), rule 29(b)

See §4 addendum below. It is written from the parent's hunk audit before any leg is solved.

## 5. Shard hard stops (any miss = STOP, no push)

1. `git rev-parse HEAD` equals the pinned SHA in the shard prompt.
2. Input sha256 values (full):
   * `data/raw/campd-unit-outages-NWPP.csv` `73f1b0e812960434a0e4a4ce87fb1f7e38e58b4a39c96e5c22fba69180eb6238`
   * `data/raw/campd-unit-outages-short-NWPP.csv` `d53d6c7bf42a4e72c99f97040eda524d0759d23140a7af0e80d12ee1f695acfc`
   * `data/raw/campd-partial-outages-NWPP.csv` `e5060145a3d0d3d3a29d880f4df83e2dca2523474ff0d29d1b6c41938b9b3dc0`
   * `data/raw/_processed-legacy/campd_ct_heat_rates_NWPP.csv` `b5c09a911c4780400acbfa4a340247d89fa190e64a0f1b4d7588094f3321395d`
   * `data/raw/_processed-legacy/campd_coal_heat_rates_NWPP.csv` `5181a7338137181a17ae2cc1fc8a376f740f126c7e4a3555a11dfc4aa418cff2`
   * `data/raw/_processed-legacy/campd_st_heat_rates_NWPP.csv` `b4a743396a27b8a12adf2b9ed3c683c8f2c287a6a03494e99d6f5d79adbc6da3`
   * `data/raw/_processed-legacy/campd_cc_heat_rates_NWPP.csv` `ca5c43bf97307c31b698c201ff4b52d992c8f1b835de5cbe648dd8448a23f91b`
   * `data/raw/_processed-legacy/chp_power_only_heat_rates_NWPP.csv` `71beb192dcda6a82076c51231ada884fb3723d79a5dd8e3334b1d3a50911d80b`
   * `data/raw/eia-930-hourly/PSEI hourly.parquet` `545e8df527a6825b73137b9a940a51ad73b285f5dbd7e7ca1af0ca8ae2992172`
   * `data/raw/eia-930-hourly/BPAT hourly.parquet` `47a23eeb240c6604bf639c319c35f4343aec229919d78bd6e42b8d88c7fd39a0`
   * `data/raw/eia-930-interchange/GRID interchange hourly.parquet` `c7ef6c41f434c6077c337a205651c7dce0ad7c5665a7a230e8f7ae994c2aaf4d`
   * `data/raw/ferc-714/psei_hourly_planning_area_demand_2018_2024.csv` `7ee7922e55ca2953688697fa630baee29537e96ce9ff17d4de5042cfa5851a47`
3. After the solve, `run_config.json` `scenario_config` shows:
   * every §2 flag true, including `partial_plant_exit_carry`;
   * `unit_outage_short_windows_gas` false;
   * `hydro_backfill_year` null for 2019–2022 and 2024 for 2023–2025;
   * the `offer_curve_by_group` sha256 as in §2, computed as
     `sha256(json.dumps(sc["offer_curve_by_group"], sort_keys=True))`.
4. **2019 and 2020 only:** the solve log shows the line `pool <Y>: PSEI EIA-930 demand missing … filled … from FERC
   714`. 2020 must show scale ≈ 1.1905 and lag −1. If it is absent, the leg ran the old fill: STOP.
5. The bundle contains `dispatch/<Y>_P1.parquet`, `hourly/class_hourly_<Y>.parquet`, `hourly/system_<Y>.parquet`,
   `run_config.json` and `meta.json`. **It does NOT need** `run_config_<Y>.json`, `metrics.json` or
   `legitimacy_diagnostics.json`, which the parent builds at composition. `hourly/hydro_cascade_<Y>` may be absent
   before 2023.

## 6. Reported, never gated

* C1–C8 per year against the keeper (2019, 2021–2025), and 2020 fresh.
* Class TWh deltas, coal r, and CT_PEAKER.
* The per-year movement is attributed to the two repairs using §1.1 and §1.3:
  * **2023 and 2024 carry neither repair's energy.** They are therefore a free drift check against the keeper, and
    any non-zero delta there is G-DRIFT's to explain.
  * **2021 and 2025** add zero-availability LP columns only.
* Price is UNSCORED (rubric v3.8). **Nothing is selected on a gate** (rule 1). The owner decides promotion (rule 31).

## 7. Cost and retrievability

* Seven shards in parallel, about 60–100 min each (R-NWPP §8), so about 1.5–2 h wall.
* Each shard pushes its FULL bundle to its own branch `claude/nwppnext-<Y>` (rule 34(a)).
* The parent fetches, verifies and composes (2023 leg first), then lands on `main` what must survive (rule 33(f)).
