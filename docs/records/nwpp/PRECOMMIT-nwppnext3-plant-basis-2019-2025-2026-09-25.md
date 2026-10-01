# PRECOMMIT — NWPP-NEXT-3: the plant-basis demand anchor (FINDING-nwpp-45 §8, framing 2), 2019–2025

**Lane:** NWPP-NEXT-3 (after keeper #9 `2026-09-25-nwppnext2h-cascade-2019`)
**Arm id (on registration):** `2026-09-25-nwppnext3-plant-basis`
**Owner ruling (this session, 2026-09-25):** on FINDING-nwpp-45 §8 the owner chose **framing 2 — anchor the
demand construction to the plant basis C1 scores on: EIA-930 hourly shape, EIA-923 plant energy.** Framing 1
was ruled and executed earlier (NWPP-47, +2.0–2.2 TWh/yr).
**Written before any leg is solved.** The parent session runs no LP (rule 32(a)).

## 1. What changes (one new gated field, zero free parameters)

`ScenarioConfig.nwpp_demand_plant_basis` (default off, NWPP-only; requires `nwpp_grid_carried_wind_served`).
`envelopes.nwpp_plant_basis_correction` is added to the NWPP-20 served schedule. For each EIA-930 fuel family
`f` the footprint series `S_f` is:

- `NG: <f>`;
- for NG, net of GRID's remaining Southwest legs;
- for OTH, `NG: OTH + NG: OIL`.

The hourly correction is:

```
Δ_f[t] = (E_f − Σ S_f) · max(S_f[t], 0) / Σ max(S_f, 0)
```

- `E_f` is the family's grid-delivered EIA-923 plant total. It comes from
  `data/raw/reference/nwpp_plant_basis_energy.csv` (sha256 `ea090a08…d036ee`), which
  `scripts/data/derive_nwpp_plant_basis_energy.py` derives from the committed bench parts' `classFull`.
- Wind and solar are skipped: their benchmark *is* the EIA-930 series.
- On a **preliminary EIA-923 vintage** (2025 has a committed completeness part) only COL and NG are anchored. The
  bench repairs only those two families. Every other class is the raw incomplete survey: 2025 OTH reads 4.27 TWh
  against 8.2–8.8 in complete years.
- Negative prints get no share of the correction.
- A year missing from the artifact FAILS rather than falling back.

**Zero-LP array effect** (`scripts/probes/_nwppnext3_plant_basis_phase0.py`, on the keeper recipe):

| year | keeper demand | arm demand | Δ TWh | gas | coal | hydro | OTH | hourly Δ min / p50 / max MW |
|---|---|---|---|---|---|---|---|---|
| 2019 | 274.995 | 279.581 | +4.586 | +1.60 | +1.96 | +0.55 | +0.49 | 262 / 538 / 748 |
| 2020 | 285.472 | 292.940 | +7.467 | +4.04 | +2.77 | +0.50 | +0.14 | 287 / 865 / 1421 |
| 2021 | 283.809 | 289.358 | +5.548 | +6.07 | −2.48 | +1.73 | +0.24 | 205 / 617 / 1185 |
| 2022 | 293.882 | 298.960 | +5.078 | +6.21 | −2.07 | +0.89 | +0.04 | 87 / 577 / 1208 |
| 2023 | 272.535 | 280.261 | +7.726 | +7.17 | −1.87 | +2.70 | −0.26 | 398 / 882 / 1428 |
| 2024 | 279.821 | 290.216 | +10.395 | +11.84 | −3.87 | +2.86 | −0.47 | 249 / 1204 / 2784 |
| 2025 | 290.700 | 302.532 | +11.832 | +12.02 | −0.19 | — | — | 167 / 1404 / 4253 |

NUC moves by less than 0.03 TWh. The residual `NG_adj − Σ fuel columns` (EIA-930's total against its own fuel
breakdown) is left untouched: −1.24 / +1.21 / +0.13 / −0.15 / +0.10 / +0.24 / +0.30 TWh. The 2019 figure is
driven by unit-slip prints in `NG: WND` (+1,087,589 MW at h3204), so it has no plant basis to replace it with.

**Rule 13 / rule 1, stated up front.** This reconciles a measured input toward the scored basis, which is exactly
what FINDING-nwpp-45 §8 flagged as sitting close to rule 13. It is adopted **by explicit owner ruling** under
rule 14's misalignment exception: the demand leg and the score leg measure the same footprint in two sources that
disagree (FINDING-nwpp-45 §3.1, FINDING-nwpp-47 §3).

- What is anchored is the **energy requirement per fuel family**. No class, unit or hour is pinned.
- The LP still decides the class split, the zonal split and the hourly dispatch.
- Nothing was selected on a gate.
- Forward story: the per-family 923/930 basis ratio from the latest final vintage would carry forward. That is not
  implemented, and the forecast lane is untouched (the default is off).

## 2. Recipe (per shard; the NWPP-NEXT-2 recipe plus ONE `--set`)

```
mkdir -p /tmp/n49 && git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/replay_keeper.py /tmp/n49/results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/nwppnext3_<Y> --years <Y> \
  --set eia860_vintage_tracks_solve_year=true \
  --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true \
  --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_partial_outage_windows=true \
  --set mid_vintage_exit_carry=true --set partial_plant_exit_carry=true \
  --set nwpp_demand_plant_basis=true \
  [<Y> in 2019, 2020, 2021, 2022 ONLY:] --set hydro_backfill_year=null \
  --note "NWPP-NEXT-3: keeper #9 recipe + nwpp_demand_plant_basis (framing 2)"
```

- Offer fingerprint: `6a13731e43c4e60d5ea84fcc08ce0695bb0f5e5287c6568ec7bf2eda75410c61`, unchanged.
- `authorized_price_tuning`: none. Price is unscored (rubric v3.8).

## 3. Years (rules 34(c), 35(c), 36)

The registered NWPP set is {2019 … 2025}. All seven are solved, **one shard per year**.

## 4. G-DRIFT (keeper `git_sha` `2b8a6bc3` → pin), rule 29(b) form 4

The command was `git diff 2b8a6bc3 <pin> --` over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`,
`_validation-source` and `reference`.

| Hunk | Class | Why |
|---|---|---|
| miso-272 `cc_block_summer_rating` (scenarios, eia860, arrays, assembly, run_calibration) | INERT | Default-off field, absent from the NWPP recipe. Every new code path is behind `if cc_block_summer_rating`. |
| soco-67 `unit_outage_precod_clip` (outages.py, outage_detect) | INERT | Default-off field, absent from the recipe. The new clip runs only under `if precod_clip`. |
| ercot `ercot_partial_outage_day_guard` | INERT | Default-off, ERCOT branch. |
| `solve_surface_declared` pin for `EIA930_REMOTE_GENERATION_DOUBLE_BOOKED`, PJM-NEXT FR-22 declaration | INERT | Declarations only. The constant's value is the keeper's. |
| SPP-80 / SPP-81 `_validation-source` parquet | INERT | Another ISO's artifact. |
| **This lane** (envelopes, demand, runner, run_calibration*, scenarios field, reference CSV) | **LIVE** | The arm itself. Off-path byte-identity is pinned by test. |

**Verdict:** form 4 is valid. The committed `nwppnext2h_span` bundle is the control, and no control solve is spent.

## 5. Shard hard stops (any miss = STOP, no push)

1. `git rev-parse HEAD` equals the pin. If it does not, run `git fetch --depth=1 origin <pin> && git checkout --detach <pin>`
   and re-check. That checks out the pin; it is not a sync.
2. The input sha256 values match the PRECOMMIT-nwppnext2 §5.2 list, plus these (all listed in the prompt):
   - `data/raw/reference/nwpp_plant_basis_energy.csv`
   - the two `nwpp-hydro` cascade CSVs
   - `GRID interchange hourly.parquet`
3. `run_config*.json` `scenario_config` shows every §2 flag true, including `nwpp_demand_plant_basis` and
   `nwpp_grid_carried_wind_served`. The offer fingerprint is `6a13731e…`.
4. `meta.json` `hydro_backfill_year` is null for 2019–2022 and 2024 for 2023–2025.
5. `hourly/system_<Y>.parquet`, pass P1, `demand` summed equals the arm demand in §1 ±0.05 TWh. **This is the
   check that the arm is live.**
6. The bundle contains `dispatch/<Y>_P1.parquet`, `hourly/class_hourly_<Y>.parquet`, `hourly/system_<Y>.parquet`
   and `hourly/hydro_cascade_<Y>.parquet`. `run_config_<Y>.json`, `metrics.json` and `legitimacy_diagnostics.json`
   are not required.

## 6. Reported, never gated

- C1–C8 per year against the keeper.
- Class TWh deltas, coal r, CT_PEAKER, and slack/VOLL. The peak rises up to +4.25 GW in 2025, so any shed is
  reported.
- Direction expected: the thermal requirement rises by the §1 Δ. How it splits across CC_REGULAR, CT, ST and coal
  is the solve's to say. **No number here is a prediction the arm is judged on** (rule 1).
- Promotion follows the owner's standing instruction: promote on improved structure, with regressions reported at
  full magnitude. Otherwise the promotion question is asked (rule 31).

## 7. Cost and retrievability

- Seven shards in parallel, about 5–40 min per year (up to ~3 h for 2024 on past evidence).
- Each pushes its full bundle to `claude/nwppnext3-<Y>` (rule 34(a)), using the `.gitignore` negation and a plain
  `git add`.
- The parent composes, with the 2023 leg first, registers, and lands the bundle on `main` before this lane's PR
  merges (rule 33(f)).
