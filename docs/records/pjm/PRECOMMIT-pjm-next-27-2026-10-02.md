# PRECOMMIT: PJM-NEXT-27. Coal-coverage rows plus their per-year `online_frac`, one data delta at W0

Written 2026-10-02, **before any PJM-NEXT-27 shard launched**. Zero LP so far.

**Keeper:** `2026-09-30-pjm-next16-ovec` (`pjmnext16_A_span`). The W0 PJM keeper (`2026-10-02-w0-pjm-fix2`,
bundle `w0_pjm_span`) is in PR #7069, not yet on `main`.

**Owner ruling (PJM-NEXT-26 card):** *"Hold; fix fractions."* Do not promote the coal rows alone. Derive per-year
`online_frac` for the 18 appended plants and re-solve the rows and fractions together as one data delta, on the W0
posture, against the W0 PJM control.

## 1. Arm (data only, no `ScenarioConfig` change)

- **`thermal_tranches_PJM.csv`:** the PJM-NEXT-25 append, byte for byte (`b6da7580`, sha256 `31455aaa…`).
- **`thermal_tranches_online_frac_by_year_PJM.csv`:** 60 rows appended for the 18 plants.
  - sha256 `5cf77a47` blob → `b87a4ac2…`. The incumbent file is an exact byte-prefix.
  - Derived by `derive_thermal_tranche_online_frac_by_year.py --iso PJM --years 2019 … 2025
    --coal-unit-coverage-plants <18 codes>`.
- **Estimator:** the coverage construction's own (`coal_unit_coverage_rows`).
  - The series is each plant's CEMS-labelled coal units only.
  - The denominator is that year's EIA-860 coal nameplate.
  - An hour counts when net > `_SYNC_MW_NAMEPLATE_FRAC` × nameplate.
  - A row exists for exactly the plant-years the pooled row pools. Pooling the 60 rows reproduces every
    appended `online_frac` exactly (18 of 18; the script refuses to write otherwise).
- **Rule 21:** zero DOF. **Rule 23:** the citation is the coverage append (the pooled rows' own source change);
  the incumbent rows are untouched. **Rule 14:** the per-year row replaces the pooled fallback the gate declares
  when no own-year row exists. **Rule 13:** backcast only (`coal_sync_online_frac_per_year`); forecast keeps
  the pooled fraction.
- **Known gap, stated:** where a plant's fleet carries coal capacity but CEMS labels no coal unit that year, there
  is no row and the pooled fallback stands. Example: Brunner Island 3140 in 2020.

**Per-year vs pooled `online_frac` (the two plants S3 names):**

| plant | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | pooled |
|---|---|---|---|---|---|---|---|
| 883 Waukegan | 0.437 | 0.270 | 0.679 | – | – | – | 0.462 |
| 3149 Montour | 0.236 | 0.047 | 0.209 | 0.219 | 0.143 | 0.493 | 0.225 |

## 2. Zero-LP verification (done; `results/phase0/pjm/_pjmnext27_frac_fleet_delta.json`)

Three fleet builds per year of `pjmnext16_A_span` with the ten W0 fields: `main`, `rows` (= PJM-NEXT-26), and
`rows_frac` (this arm).

- **Confinement:** `rows → rows_frac` moves 0 units outside the 18 plants in every year.
- **Floored TWh at the 18 plants:**

  | | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
  |---|---|---|---|---|---|---|---|
  | main | 0.31 | 0.22 | 0.31 | 0.22 | 0.01 | 0.00 | 0 |
  | rows (NEXT-26) | 6.55 | 5.56 | 5.00 | 3.17 | 0.99 | 0.44 | 0.02 |
  | rows + frac | 6.79 | 5.70 | 5.23 | 3.29 | 0.52 | 0.51 | 0.02 |

- **What it says:** the fractions mostly reallocate floor across years rather than shrink it.
  - Waukegan 883: 2019 0.43 → 0.42, 2020 0.33 → 0.29, 2021 0.61 → 0.74 TWh.
  - Montour 3149: 2019 0.201 → 0.205, 2020 0.025 → 0.018 TWh.
  - Homer City 3122 2023: 0.81 → 0.34 TWh.

## 3. G-DRIFT (rule 29(b))

- `25da6022 → 3ec2fd3e`: `ADDENDUM-pjm-next-26` §3, all INERT.
- `3ec2fd3e → 0663760b` (58 commits; solve path: `run_calibration.py`, `runner.py`, `scenarios.py`,
  `fleet/arrays.py`, `fleet/models.py`, `results/export.py`):
  - Every hunk is behind `spp_mmu_offer_repair`, which is SPP-only and default off. That covers the
    `emergency_band` pool, the multiplicative MMU bands and the export fuel tag.
  - The rest is replay-guard tooling (`replay_recipe.py`) or off-path (`stb_ep724.py`, `storage_compare.py`).
  - **All INERT for PJM.**
- The W0 control's kept 2024–25 legs (`ce8820dd`) are covered by closeout-B's `KEPT-LEG-INERT-PROOF-2026-10-02.md`.

## 4. Control (fixed here, ex ante)

- **Primary control: `results/calibration/w0_pjm_span`** as committed on `claude/w0-pjm-fix2` @ `bd703ae8`
  (PR #7069), every year 2019–2025. S1–S4 are read against it. If #7069 merges first, the same bundle on `main`.
- **Reported, not used to decide:**
  - the PJM-NEXT-26 legs (`claude/pjm-next-26-<Y>`; W0 + rows), which isolate the fraction half of the delta;
  - the incumbent keeper `pjmnext16_A_span`.

## 5. Pre-fixed readings (S1–S4 carried from PRECOMMIT-pjm-next-25 §4; controls per §4)

| id | statement | falsified if |
|---|---|---|
| S1 | Slack + dump ≤ control + 0.01 TWh in every year | exceeded |
| S2 | Appended-cohort within-plant contrast (`_pjmnext24_within_across.within`, actual-RT margin, on each bundle's `unit_marginal` layer) moves toward real in 2019–2021 | the model − real gap is not smaller than the control's in ≥ 2 of 3 years |
| S3 | Rule 20 / D-2: no coal class > 30 % forced. D-4 (`legitimacy_diagnostics.json`) adds no coal off-window unit-conduct failure that the control lacks, **explicitly including Waukegan 883 and Montour 3149 in every year** | any new coal D-4 failure, at 883, 3149 or elsewhere |
| S4 | 2023–2025 C1/C3 verdicts unchanged vs the control | any training-tier cell flips |
| P1 | COAL_BIT 2019 and 2021 move up vs the control, by 1–6 TWh | down, or > 6 |
| P2 | No failing cell outside COAL_BIT / CC_REGULAR 2019–2022 flips to PASS | (informational) |
| F1 | Against the NEXT-26 legs, the D-4 off-window share at 883 falls in 2020, and at 3149 in 2020 | (informational; isolates the fraction half) |

**Honest prior, stated before the solve.** Phase 0 shows 883 and 3149 keep essentially their 2019 floors (0.437
vs 0.462; 0.236 vs 0.225). PJM-NEXT-26's 2019 off-window failures there (0.138; 0.001) are therefore expected to
persist, so **S3 is more likely than not to fail again in 2019.** That would mean the off-window conduct comes
from the window's placement (top load-ranked hours), not its size. The reading is not re-cut if so.

**Decision rule.**
- **If S1–S4 hold:** recommend promotion on structure (rule 1; owner: *"If structural integrity improves but
  gates regress that may still be a keeper"*), after the W0 keeper is on `main`.
- **Otherwise:** do not recommend. Present the owner a decision card with the S3 conduct read.

## 6. Execution

- **Shards:** seven, one per year (rule 36). Each is pinned to this branch's full SHA and replays
  `pjmnext16_A_span` with the ten W0 `--set` fields (`ADDENDUM-pjm-next-26` §2).
- **Shard prompt:** `scripts/shard_prompt.py --iso PJM --all-years`, plus the PJM-NEXT-26 lessons:
  - step 0 is `git fetch origin <sha> && git checkout --detach <sha>`;
  - DATA SETUP is `uv sync`; `fetch_pjm_da_virtuals --years <Y> --feeds hrl_da_incs_decs`;
    `regenerate_clean --solve-profile PJM`; run with `.venv/bin/python`;
  - a legitimacy FAIL is informational;
  - push `hourly/unit_marginal_<Y>.parquet`.
- **Compose and read:**
  - Compose with `_pjmnext26_compose_span.py` (re-pointed).
  - Read S1/S2/P1 with `_pjmnext26_readings.py` (re-pointed: candidate vs `w0_pjm_span`, NEXT-26 legs reported).
  - S3 from `legitimacy_diagnostics.py`; S4 with `calibration_verdict.determine` on 2023–2025, then
    `iso_determination`.
