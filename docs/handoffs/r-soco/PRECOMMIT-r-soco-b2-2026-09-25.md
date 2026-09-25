# PRECOMMIT — R-SOCO-B2: date the Gulf Power exit (ruling (C)) and re-solve SOCO 2019–2025

Base: `main` @ `a1b8ebd9` (R-SOCO-B #6608 merged). Branch `claude/soco-boundary-gap-2019-2021-42xe0j`. This file
was written before any shard was launched. The parent solves nothing (rule 32(a)); each year is solved in its own
shard (rule 36).

**Owner ruling (C), 2026-09-25**, in answer to `FINDING-r-soco-b2-boundary-2026-09-25.md`: "(C) dated exit" at
"Hour grain". The finding measured that the former Gulf Power plants and Gulf's load were inside SOCO's EIA-930 BA
until hour-ending UTC 2022-07-13 12:00. R-SOCO-B's R2 had removed them in every year.

## 1. The repair: R4, `ISO_BA_EXITS`

| what | where |
|---|---|
| `constants.ISO_BA_EXITS = {"SOCO": {"FPL": "2022-07-13 12:00"}}`. The value is the first row OUTSIDE the region, written as the extract's own hour-ending `UTC time`. It dates R2 and never reverts it (rule 14). | `constants.py`, declared at the inert `{}` (`a4d0fee78b233797`), so only SOCO's key moves |
| **Exit members.** These are the current-recoded plants whose destination BA is registered **and** which some EIA-860 vintage up to the exit year coded SOCO. The second condition matters: the recode map also names every plant that was always FPL's, and those must never be admitted. Result: exactly the nine Gulf plants, members in 2019–2022 and none from 2023. | `ba_membership.{ba_exit_stamps, exit_member_plants, _coded_to_region_by}` |
| **Fleet.** The recode drop keeps exit members in any year up to the exit year (`drop_current_ba_recoded_rows(..., year=)`). The operable and mothball loaders admit them whatever BA code the vintage gives. `fleet/arrays.py` masks them offline from LP row **4637** of 2022, the row whose `UTC time` is 2022-07-13 12:00, with `min_gen` scaled the same way. | `fleet/eia860.py`, `fleet/arrays.py`, `ba_membership.ba_exit_first_outside_row` |
| **Data.** `vintage_2022` codes Santa Rosa 55242 as `FPL`, and the modelled-BA build filter had dropped its rows. They are appended with `process_eia860.py --rescope-from-parquet data/raw/eia-860/vintage_2022 --admit-plant 55242` (new flag, which appends only the named plant's missing rows). 20,400 → 20,402 rows, CT01 + ST01, eGRID heat rate 7.458. The committed rows are frame-identical and the dtypes are equal. | `scripts/data/process_eia860.py` |
| **Benchmark / injection.** `_iso_plant_ids(iso, year)` puts exit members back through 2022. `_eia923_frame` zeroes their Aug–Dec 2022 and scales July 2022 by each plant's own CAMPD gross-load share before the stamp: Crist 0.4002, Smith 0.4267, Santa Rosa 0.3936. Plants CAMPD does not carry get the hour share, 0.3952. | `run_calibration_full.py`, `ba_membership.ba_exit_month_share` |

Zero free parameters and zero `ScenarioConfig` fields. The stamp is measured, and the shares are CAMPD's own numbers
or the clock's. The mechanism-matrix row `iso_ba_exit_membership` is added in the base file with a cell in all
nine shards (SOCO `O`, others `U`). There is a cache-epoch prose entry. The attestation tooling is extended:
`rsocob_compose_span.py` asserts Gulf is present in 2019–2022, has zero dispatch from row 4637 of 2022 and is absent
from 2023, and `gen_rsocob_attestation.py` checks the fourth registry.

## 2. Phase-0 census (zero LP): `rsocob2_boundary/census/<Y>_post.json`, vs R-SOCO-B's `rsocob_phase0/<Y>_post.json`

Keeper recipe, `fleet_only=True`, `scripts/probes/_rsocob_phase0.py <Y> post`.

| year | Gulf LP MW | Gulf avail TWh | CC_REGULAR MW | COAL MW | CT_PEAKER MW | ST_GAS MW | EIA-923 Gulf in benchmark, TWh |
|---|---|---|---|---|---|---|---|
| 2019 | 0 → **1,826.6** | 0 → 14.605 | 16,647.5 → 17,503.1 | 14,150.3 → **15,074.3** | 9,349.8 → 9,361.8 | 3,141.1 | 0 → **8.011** |
| 2020 | 0 → **1,826.6** | 0 → 14.605 | 16,624.0 → 17,479.6 | 14,148.0 → 15,072.0 | 9,341.9 → 9,353.9 | 3,141.1 | 0 → **7.790** |
| 2021 | 0 → **2,760.8** | 0 → 14.413 | 17,272.4 → 18,128.0 | 14,116.0 | 10,037.0 → 10,983.2 | 3,141.1 → **4,065.1** | 0 → **7.219** |
| 2022 | 0 → **2,760.8** (incl. Santa Rosa 236) | 0 → **10.962**; monthly GWh 1,818 / 1,642 / 1,709 / 1,654 / 1,709 / 1,727 / **702.8** / 0 / 0 / 0 / 0 / 0 | 17,268.9 → 18,124.5 | 11,512.0 | 9,379.4 → 10,325.6 | 3,141.1 → **4,065.1** | 0 → **4.053** |
| 2023–2025 | 0 | 0 | unchanged | unchanged | unchanged | unchanged | 0 |

**Demand and served interchange are unchanged in every year**, as is the PowerSouth fleet. The EIA-923 benchmark
frame for 2023–2025 is identical.

**Same-container proof that 2023+ is inert.** A census run at clean `origin/main` (`a1b8ebd9`) in this container
equals this branch's census **byte for byte** in 2023. In 2021 it equals this branch in every field except the
Gulf-related ones.

**Environmental note.** R-SOCO-B's committed census JSONs were produced in a different container. They differ
from both of this container's runs in fields this lane does not touch. Hydro availability agrees once the
recipe's `curate_hydro_plant_modes.py --iso SOCO` has run. The AEC availability differs by about +0.5 %, and so does
2023 AEC per-plant MW (e.g. McWilliams 249.2 vs 654.1 MW). `git diff 6edbeb61 origin/main` over the solve paths
**and all of `data/`** contains only R-SOCO-B's own commit, so this is derived-data state in that container,
**not code drift**. **E2 below is the test that matters**, and it is solved in fresh shards on the recipe.

## 3. Proof that only SOCO moves

- **`ScenarioConfig(iso, mode).cache_key()`, main vs branch, backcast and forecast.** ERCOT, CAISO, MISO, PJM,
  NYISO, NEISO, SPP and NWPP are **identical**. The SOCO backcast key moves `17ae20ef9a57180a` → `2fc3d828f0f39303`.
- **`load_fleet_from_csv(X, vintage_2022, year=2022)`, main vs branch.** The fleet hash is **identical** for all
  eight others. SOCO goes 402 → 421 units.
- **`solve_surface_register.py --diff HEAD`.** 312 → 313 names, **0 values moved**, 1 added (`ISO_BA_EXITS`).
  `check_cache_key_registration.py`: ok. `check_mechanism_matrix.py --base origin/main`: ok.
- **Tests.** `tests/unit/data/test_ba_membership.py`: 12 passed (5 new). Across `tests/unit/data`, the
  fleet / COD / vintage / solve-surface files and `test_persisted_identity`: 2,599 passed and 5 failed. **All 5
  fail identically at base `a1b8ebd9`**, so they are pre-existing: `test_caiso_st_gas_peak_measured`,
  `test_fleet_arrays_golden::ercot_2023`, two `test_gas_offer_zonal_anchor_vintage`, and
  `test_unit_outage_dark_unit_years::test_committed_soco_companion…`.

## 4. G-DRIFT (rule 29(b))

The R-SOCO-B legs were solved at `f2a5412e` on base `b5e3b914`, and their rebase G-DRIFT onto `6edbeb61` was all
INERT (R-SOCO-B PRECOMMIT addendum). `git diff 6edbeb61 origin/main` over `src/market_sim scripts/run_calibration*.py
scripts/lib data/` is R-SOCO-B's own commit `9f0e8f81` (R1/R2/R3), with nothing else. On top of that sits this
lane's R4, which is **LIVE in 2019–2022** and **INERT in 2023–2025** by the same-container census above.
**So the 2023–2025 legs must reproduce R-SOCO-B's committed composite legs, and 2024–2025 must reproduce the
keeper's.** That is E2.

The R-SOCO-B leg branches were deleted on the lane-PR merge. Only `claude/rsocob-2021` (fbe97e08) remains, and it is
superseded. The parked composite `claude/r-soco-b-hold` @ `99906f86` has no `dispatch/` files. **All seven years
are therefore solved.**

## 5. The recipe (one shard per year; the R-SOCO-B §6 recipe, new out-dir)

```
uv sync
python3 scripts/hydrate_data.py --profile soco
PYTHONPATH=. uv run python scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. uv run python scripts/data/curate_demand_profile.py
uv run python scripts/replay_keeper.py results/calibration/rsoco_corrected_inputs_span --years <Y> \
  --out-dir results/calibration/rsocob2_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true \
  --note "R-SOCO-B2 <Y>: R-SOCO keeper recipe on the repaired SOCO BA boundary (R1 2019 interchange sign, R2 Gulf recode drop, R3 PowerSouth join 2021-09-01, R4 Gulf exit dated 2022-07-13 12:00 UTC); multipliers unchanged"
```

**Per-leg hard stops.** `git rev-parse HEAD` equals the pinned SHA. `run_config.json` shows the five `--set`
fields True. `solve_surface.moved` names `EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC`, `ISO_BA_JOINS` **and**
`ISO_BA_EXITS`. Every band is 1.0. `dispatch/<Y>_P1.parquet` is present. The Gulf plants (641, 643) are in
`dispatch/<Y>_P1_fleet.parquet` for Y ≤ 2022 and absent for Y ≥ 2023.

**Parent seam.** Fetch each leg and run `rsocob_compose_span.py --check-only`, which asserts the four repairs:
Gulf present ≤ 2022 with zero dispatch from row 4637 of 2022; PowerSouth zero Jan–Aug 2021; 2019 demand 245.097.
Then compose, and run the Task-3 chain.

## 6. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

- **E1 (2019–2022, R4).** Adding 1.8–2.8 GW of in-BA Gulf capacity at fixed demand and fixed served interchange
  gives the following. **Gulf dispatch is positive.** The Gulf units are Smith CC, Santa Rosa CC, Crist coal in
  2019–2020 and Crist gas/CT from 2021. **Their energy displaces other SOCO units**: the classes most exposed are
  CT_PEAKER, then CC_REGULAR. In 2019–2020 COAL rises by Crist's share. **Unserved does not rise.** The
  benchmark gains Gulf's 8.0 / 7.8 / 7.2 / 4.1 TWh, mostly CC_REGULAR and ST_GAS (COAL_BIT in 2019–2020).
- **E2 (2023–2025).** |Δ class TWh| ≤ 0.01 on every class, and identical unserved MWh: against R-SOCO-B's
  composite legs (2023) and against the keeper's legs (2024, 2025). A larger move falsifies §4 and is reported as a
  finding.
- **E3 (B1/B2).** `gen_soco60b` passes on 2019–2024 with no scope limit. 930/923 fossil is **0.982 / 0.991 /
  0.982 / 0.985** for 2019–2022 (FINDING §1) and 1.002 / 0.981 for 2023 / 2024, and 930 gas ≤ 923 gas in every year.
- **E4.** The R-SOCO-B checks persist: 2019 demand-with-interchange is 245.097 TWh, and PowerSouth is 0 Jan–Aug
  2021 and positive Sep–Dec.
- **E5.** C3a/b/c are UNSCORABLE in every year (no SOCO price). C6 PASS.

## 7. Promotion recommendation rule (fixed now)

Recommend this run as the SOCO keeper **iff** all seven legs solve cleanly with the posture and the four repairs
verified (§5), **and** E2 holds (or its deviation is fully explained by an identified code path), **and** E3 passes
without a scope limit. This holds **whatever the C1–C8 gates do**; rule 14 applies. The owner decides (rule 31). If
the run is promoted, rule 35 prunes `2026-09-24-r-soco-corrected-inputs`, and the incoming run covers the union
{2023, 2024, 2025} and adds 2019–2022. The parked `2026-09-25-r-soco-b-boundary` is superseded and never lands.
