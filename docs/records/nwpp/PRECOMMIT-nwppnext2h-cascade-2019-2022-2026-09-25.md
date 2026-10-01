# PRECOMMIT — NWPP-NEXT-2 arm H: hydro cascade binding in 2019–2022 (on top of the PSEI repair)

**Arm id (on registration):** `2026-09-25-nwppnext2h-cascade-2019`
**Base arm:** `2026-09-25-nwppnext2-psei-colstrip` (PRECOMMIT-nwppnext2-psei-colstrip-2019-2025-2026-09-25.md, pin `2b8a6bc3`)
**Written before any leg is solved.** The parent runs no LP (rule 32(a)).

## 1. What changes

The only change is **data coverage**: the NWPP cascade artifacts now carry 2019–2022 per-plant-month rows
(FINDING-nwppnext2-hydro-cascade-2019-2022-2026-09-25.md, commit `aff853ea`).

- `hydro_cascade_coupling` is already `True` in the keeper recipe. It was inert before 2023 only for lack of data.
- In 2019–2022 it now binds on 5 plants (CHJ, WEL, RIS, BON, IHR) over 5 links, with τ [0,1,1,0,0] h. That adds
  43,800 water-balance rows and 87,600 columns per year.
- **Rule 23:**
  - τ, the pondage band, the NID areas and the coupled flags stay as trained on 2023–24.
  - `nwpp_hydro_cascade_links.csv` is byte-identical.
  - GCL→CHJ September 2019 reads 2.67 % against the 2 % side-inflow gate. It is reported and NOT refit.
- `hydro_backfill_year` stays **null** for 2019–2022. Final EIA-923 needs no backfill (rule 14).
- Zero new free parameters. No new `--set` beyond the base arm's recipe.

## 2. Years

| Years | Treatment |
|---|---|
| **2019–2022** | Solved here, **four shards**, one per year (rule 36). Recipe = base-arm §2 exactly, with out-dir `nwppnext2h_<Y>`. |
| **2023–2025** | **Taken from the base arm's legs**, not re-solved. |

**G-DRIFT for 2023–2025 (form 4, zero LP), `2b8a6bc3` → this pin:**
- The only solve-path change is `aff853ea` (hydro artifacts plus the three `scripts/data` builders, which never run
  inside a solve).
- Every committed 2023–2025 artifact row is identical: CSV lines are a superset, and parquet rows are frame-equal on
  the old years. So the LP arrays for 2023–2025 are identical and the base legs are this arm's legs.
- All other commits between the pins are docs, probes and the attestation generator: INERT.
- The composite therefore covers all seven years (rule 34(c)).

## 3. Shard hard stops

1. `git rev-parse HEAD` must equal the pin. **If it does not** (this environment has been cloning `main`), the shard
   runs `git fetch --depth=1 origin <pin> && git checkout --detach <pin>` and re-checks. That checks out the pin; it
   is not a sync.
2. The base-arm §5.2 input sha256 values, plus
   `data/raw/nwpp-hydro/nwpp_hydro_cascade_monthly.csv` and `data/raw/nwpp-hydro/nwpp_hydro_cascade_links.csv`,
   match the values in the shard prompt.
3. The offer fingerprint is `6a13731e…`, the flags are as in the base arm, and `hydro_cascade_coupling` is true.
4. `meta.json` `hydro_backfill_year` is null.
5. The bundle contains `hourly/hydro_cascade_<Y>.parquet`, which was absent before 2023 in the keeper. If it is
   absent, the cascade did not bind: STOP. It also contains `dispatch/<Y>_P1.parquet`,
   `hourly/class_hourly_<Y>.parquet`, `hourly/system_<Y>.parquet`, `run_config.json` and `meta.json`.
6. Solve-log PSEI line as in the base arm: 2019 scale 1.0251, 2020 scale 1.0619, 2021 336 h, none in 2022.

## 4. Reported, never gated

- Per year against the base arm and the keeper: C1–C8, hydro intra-day swing, coal r.
- Nothing is selected on a gate (rule 1). Promotion is under the owner's standing instruction or rule 31.

## 5. Cost

- Four shards, about 60–100 min each.
- Each pushes its full bundle to `claude/nwppnext2h-<Y>` (rule 34(a)).
