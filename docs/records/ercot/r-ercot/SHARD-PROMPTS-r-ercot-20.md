# R-ERCOT-20 GT-split shard prompts (one per year, rule 36)
Arm = keeper `2026-09-30-r-19-eia-923` recipe, unchanged, on the GT-split inputs (PRECOMMIT-r-ercot-20-gt-split-2026-09-30.md). Solve SHA bf7c1228b9450aea0bb020c48f8d5ccafdae9190.

## LEG arm-2019

```text
SHARD R-ERCOT-20 ARM 2019 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-20 (docs/records/ercot/r-ercot/PRECOMMIT-r-ercot-20-gt-split-2026-09-30.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal bf7c1228b9450aea0bb020c48f8d5ccafdae9190. If not, `git fetch origin bf7c1228b9450aea0bb020c48f8d5ccafdae9190 && git checkout bf7c1228b9450aea0bb020c48f8d5ccafdae9190` (detached is fine), then `git checkout -b claude/r-ercot20-arm-2019`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach bf7c1228b9450aea0bb020c48f8d5ccafdae9190, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  deaebee4628527450021fe348bb1359c0ff3a67afa1371c7f7d5a0f4f8ba58c6
  data/raw/reference/master-plant-registry.csv  4e9eb13427521210413370463b44837f6c3fc16b440d1e43246435827ff875dd
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_ct_heat_rates_ERCOT.csv  2b92e7c81261673fcb51a51ff246510668088255e96166bc4da3516ac1531f17
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot19a_span --years 2019 --out-dir results/calibration/r_ercot20_arm_2019 --note "R-ERCOT-20 ARM 2019: keeper 2026-09-30-r-19-eia-923 recipe unchanged, on the GT-split inputs (T H Wharton / Sand Hill / Colorado Bend simple-cycle GTs as CT_PEAKER split children 34693 / 79003 / 563503) - PRECOMMIT-r-ercot-20-gt-split" 2>&1 | tee /tmp/r_ercot20_arm_2019.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot20_arm_2019/run_config.json after the solve:
  scenario_config: ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95; netload_drag_prior_year_commitment_index = true; cc_committed_prior_year_commitment_eligibility = false (or absent); netload_drag_prior_year_hour_profile = false (or absent); cc_committed_offer_margin = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true.
  results/calibration/r_ercot20_arm_2019/hourly/system_2019.parquet, results/calibration/r_ercot20_arm_2019/dispatch/2019_P1.parquet and results/calibration/r_ercot20_arm_2019/floors/2019_P1.npz must exist, and dispatch/2019_P1.parquet must contain unit ids for plant codes 34693 and 79003 (grep the unit_id column for "_p34693_" and "_p79003_").
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot20_arm_2019/\n!results/calibration/r_ercot20_arm_2019/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot20_arm_2019
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot20_arm_2019/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-20 ARM 2019: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot20-arm-2019 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot20_arm_2019 | wc -l` > 0 and that it lists dispatch/2019_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2019.parquet rows with pass=='P1'); total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2019.parquet; P1 TWh for plant codes 3469, 34693, 7900, 79003, 56350, 563503 from dispatch/2019_P1.parquet (match unit_id on "_p<code>_"); the signature values you read; anything unexpected.
```

## LEG arm-2020

```text
SHARD R-ERCOT-20 ARM 2020 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-20 (docs/records/ercot/r-ercot/PRECOMMIT-r-ercot-20-gt-split-2026-09-30.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal bf7c1228b9450aea0bb020c48f8d5ccafdae9190. If not, `git fetch origin bf7c1228b9450aea0bb020c48f8d5ccafdae9190 && git checkout bf7c1228b9450aea0bb020c48f8d5ccafdae9190` (detached is fine), then `git checkout -b claude/r-ercot20-arm-2020`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach bf7c1228b9450aea0bb020c48f8d5ccafdae9190, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  deaebee4628527450021fe348bb1359c0ff3a67afa1371c7f7d5a0f4f8ba58c6
  data/raw/reference/master-plant-registry.csv  4e9eb13427521210413370463b44837f6c3fc16b440d1e43246435827ff875dd
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_ct_heat_rates_ERCOT.csv  2b92e7c81261673fcb51a51ff246510668088255e96166bc4da3516ac1531f17
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot19a_span --years 2020 --out-dir results/calibration/r_ercot20_arm_2020 --note "R-ERCOT-20 ARM 2020: keeper 2026-09-30-r-19-eia-923 recipe unchanged, on the GT-split inputs (T H Wharton / Sand Hill / Colorado Bend simple-cycle GTs as CT_PEAKER split children 34693 / 79003 / 563503) - PRECOMMIT-r-ercot-20-gt-split" 2>&1 | tee /tmp/r_ercot20_arm_2020.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot20_arm_2020/run_config.json after the solve:
  scenario_config: ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95; netload_drag_prior_year_commitment_index = true; cc_committed_prior_year_commitment_eligibility = false (or absent); netload_drag_prior_year_hour_profile = false (or absent); cc_committed_offer_margin = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true.
  results/calibration/r_ercot20_arm_2020/hourly/system_2020.parquet, results/calibration/r_ercot20_arm_2020/dispatch/2020_P1.parquet and results/calibration/r_ercot20_arm_2020/floors/2020_P1.npz must exist, and dispatch/2020_P1.parquet must contain unit ids for plant codes 34693 and 79003 (grep the unit_id column for "_p34693_" and "_p79003_").
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot20_arm_2020/\n!results/calibration/r_ercot20_arm_2020/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot20_arm_2020
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot20_arm_2020/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-20 ARM 2020: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot20-arm-2020 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot20_arm_2020 | wc -l` > 0 and that it lists dispatch/2020_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2020.parquet rows with pass=='P1'); total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2020.parquet; P1 TWh for plant codes 3469, 34693, 7900, 79003, 56350, 563503 from dispatch/2020_P1.parquet (match unit_id on "_p<code>_"); the signature values you read; anything unexpected.
```

## LEG arm-2021

```text
SHARD R-ERCOT-20 ARM 2021 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-20 (docs/records/ercot/r-ercot/PRECOMMIT-r-ercot-20-gt-split-2026-09-30.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal bf7c1228b9450aea0bb020c48f8d5ccafdae9190. If not, `git fetch origin bf7c1228b9450aea0bb020c48f8d5ccafdae9190 && git checkout bf7c1228b9450aea0bb020c48f8d5ccafdae9190` (detached is fine), then `git checkout -b claude/r-ercot20-arm-2021`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach bf7c1228b9450aea0bb020c48f8d5ccafdae9190, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  deaebee4628527450021fe348bb1359c0ff3a67afa1371c7f7d5a0f4f8ba58c6
  data/raw/reference/master-plant-registry.csv  4e9eb13427521210413370463b44837f6c3fc16b440d1e43246435827ff875dd
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_ct_heat_rates_ERCOT.csv  2b92e7c81261673fcb51a51ff246510668088255e96166bc4da3516ac1531f17
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot19a_span --years 2021 --out-dir results/calibration/r_ercot20_arm_2021 --note "R-ERCOT-20 ARM 2021: keeper 2026-09-30-r-19-eia-923 recipe unchanged, on the GT-split inputs (T H Wharton / Sand Hill / Colorado Bend simple-cycle GTs as CT_PEAKER split children 34693 / 79003 / 563503) - PRECOMMIT-r-ercot-20-gt-split" 2>&1 | tee /tmp/r_ercot20_arm_2021.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot20_arm_2021/run_config.json after the solve:
  scenario_config: ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95; netload_drag_prior_year_commitment_index = true; cc_committed_prior_year_commitment_eligibility = false (or absent); netload_drag_prior_year_hour_profile = false (or absent); cc_committed_offer_margin = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true.
  results/calibration/r_ercot20_arm_2021/hourly/system_2021.parquet, results/calibration/r_ercot20_arm_2021/dispatch/2021_P1.parquet and results/calibration/r_ercot20_arm_2021/floors/2021_P1.npz must exist, and dispatch/2021_P1.parquet must contain unit ids for plant codes 34693 and 79003 (grep the unit_id column for "_p34693_" and "_p79003_").
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot20_arm_2021/\n!results/calibration/r_ercot20_arm_2021/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot20_arm_2021
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot20_arm_2021/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-20 ARM 2021: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot20-arm-2021 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot20_arm_2021 | wc -l` > 0 and that it lists dispatch/2021_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2021.parquet rows with pass=='P1'); total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2021.parquet; P1 TWh for plant codes 3469, 34693, 7900, 79003, 56350, 563503 from dispatch/2021_P1.parquet (match unit_id on "_p<code>_"); the signature values you read; anything unexpected.
```

## LEG arm-2022

```text
SHARD R-ERCOT-20 ARM 2022 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-20 (docs/records/ercot/r-ercot/PRECOMMIT-r-ercot-20-gt-split-2026-09-30.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal bf7c1228b9450aea0bb020c48f8d5ccafdae9190. If not, `git fetch origin bf7c1228b9450aea0bb020c48f8d5ccafdae9190 && git checkout bf7c1228b9450aea0bb020c48f8d5ccafdae9190` (detached is fine), then `git checkout -b claude/r-ercot20-arm-2022`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach bf7c1228b9450aea0bb020c48f8d5ccafdae9190, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  deaebee4628527450021fe348bb1359c0ff3a67afa1371c7f7d5a0f4f8ba58c6
  data/raw/reference/master-plant-registry.csv  4e9eb13427521210413370463b44837f6c3fc16b440d1e43246435827ff875dd
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_ct_heat_rates_ERCOT.csv  2b92e7c81261673fcb51a51ff246510668088255e96166bc4da3516ac1531f17
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot19a_span --years 2022 --out-dir results/calibration/r_ercot20_arm_2022 --note "R-ERCOT-20 ARM 2022: keeper 2026-09-30-r-19-eia-923 recipe unchanged, on the GT-split inputs (T H Wharton / Sand Hill / Colorado Bend simple-cycle GTs as CT_PEAKER split children 34693 / 79003 / 563503) - PRECOMMIT-r-ercot-20-gt-split" 2>&1 | tee /tmp/r_ercot20_arm_2022.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot20_arm_2022/run_config.json after the solve:
  scenario_config: ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95; netload_drag_prior_year_commitment_index = true; cc_committed_prior_year_commitment_eligibility = false (or absent); netload_drag_prior_year_hour_profile = false (or absent); cc_committed_offer_margin = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true.
  results/calibration/r_ercot20_arm_2022/hourly/system_2022.parquet, results/calibration/r_ercot20_arm_2022/dispatch/2022_P1.parquet and results/calibration/r_ercot20_arm_2022/floors/2022_P1.npz must exist, and dispatch/2022_P1.parquet must contain unit ids for plant codes 34693 and 79003 (grep the unit_id column for "_p34693_" and "_p79003_").
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot20_arm_2022/\n!results/calibration/r_ercot20_arm_2022/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot20_arm_2022
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot20_arm_2022/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-20 ARM 2022: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot20-arm-2022 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot20_arm_2022 | wc -l` > 0 and that it lists dispatch/2022_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2022.parquet rows with pass=='P1'); total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2022.parquet; P1 TWh for plant codes 3469, 34693, 7900, 79003, 56350, 563503 from dispatch/2022_P1.parquet (match unit_id on "_p<code>_"); the signature values you read; anything unexpected.
```

## LEG arm-2023

```text
SHARD R-ERCOT-20 ARM 2023 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-20 (docs/records/ercot/r-ercot/PRECOMMIT-r-ercot-20-gt-split-2026-09-30.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal bf7c1228b9450aea0bb020c48f8d5ccafdae9190. If not, `git fetch origin bf7c1228b9450aea0bb020c48f8d5ccafdae9190 && git checkout bf7c1228b9450aea0bb020c48f8d5ccafdae9190` (detached is fine), then `git checkout -b claude/r-ercot20-arm-2023`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach bf7c1228b9450aea0bb020c48f8d5ccafdae9190, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  deaebee4628527450021fe348bb1359c0ff3a67afa1371c7f7d5a0f4f8ba58c6
  data/raw/reference/master-plant-registry.csv  4e9eb13427521210413370463b44837f6c3fc16b440d1e43246435827ff875dd
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_ct_heat_rates_ERCOT.csv  2b92e7c81261673fcb51a51ff246510668088255e96166bc4da3516ac1531f17
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot19a_span --years 2023 --out-dir results/calibration/r_ercot20_arm_2023 --note "R-ERCOT-20 ARM 2023: keeper 2026-09-30-r-19-eia-923 recipe unchanged, on the GT-split inputs (T H Wharton / Sand Hill / Colorado Bend simple-cycle GTs as CT_PEAKER split children 34693 / 79003 / 563503) - PRECOMMIT-r-ercot-20-gt-split" 2>&1 | tee /tmp/r_ercot20_arm_2023.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot20_arm_2023/run_config.json after the solve:
  scenario_config: ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = false; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95; netload_drag_prior_year_commitment_index = true; cc_committed_prior_year_commitment_eligibility = false (or absent); netload_drag_prior_year_hour_profile = false (or absent); cc_committed_offer_margin = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true.
  results/calibration/r_ercot20_arm_2023/hourly/system_2023.parquet, results/calibration/r_ercot20_arm_2023/dispatch/2023_P1.parquet and results/calibration/r_ercot20_arm_2023/floors/2023_P1.npz must exist, and dispatch/2023_P1.parquet must contain unit ids for plant codes 34693 and 79003 (grep the unit_id column for "_p34693_" and "_p79003_").
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot20_arm_2023/\n!results/calibration/r_ercot20_arm_2023/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot20_arm_2023
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot20_arm_2023/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-20 ARM 2023: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot20-arm-2023 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot20_arm_2023 | wc -l` > 0 and that it lists dispatch/2023_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2023.parquet rows with pass=='P1'); total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2023.parquet; P1 TWh for plant codes 3469, 34693, 7900, 79003, 56350, 563503 from dispatch/2023_P1.parquet (match unit_id on "_p<code>_"); the signature values you read; anything unexpected.
```

## LEG arm-2024

```text
SHARD R-ERCOT-20 ARM 2024 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-20 (docs/records/ercot/r-ercot/PRECOMMIT-r-ercot-20-gt-split-2026-09-30.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal bf7c1228b9450aea0bb020c48f8d5ccafdae9190. If not, `git fetch origin bf7c1228b9450aea0bb020c48f8d5ccafdae9190 && git checkout bf7c1228b9450aea0bb020c48f8d5ccafdae9190` (detached is fine), then `git checkout -b claude/r-ercot20-arm-2024`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach bf7c1228b9450aea0bb020c48f8d5ccafdae9190, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  deaebee4628527450021fe348bb1359c0ff3a67afa1371c7f7d5a0f4f8ba58c6
  data/raw/reference/master-plant-registry.csv  4e9eb13427521210413370463b44837f6c3fc16b440d1e43246435827ff875dd
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_ct_heat_rates_ERCOT.csv  2b92e7c81261673fcb51a51ff246510668088255e96166bc4da3516ac1531f17
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot19a_span --years 2024 --out-dir results/calibration/r_ercot20_arm_2024 --note "R-ERCOT-20 ARM 2024: keeper 2026-09-30-r-19-eia-923 recipe unchanged, on the GT-split inputs (T H Wharton / Sand Hill / Colorado Bend simple-cycle GTs as CT_PEAKER split children 34693 / 79003 / 563503) - PRECOMMIT-r-ercot-20-gt-split" 2>&1 | tee /tmp/r_ercot20_arm_2024.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot20_arm_2024/run_config.json after the solve:
  scenario_config: ercot_offer_swcap_clip = false; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 4.576; offer_curve_by_group.CT_PEAKER.peak = 13.15; netload_drag_prior_year_commitment_index = true; cc_committed_prior_year_commitment_eligibility = false (or absent); netload_drag_prior_year_hour_profile = false (or absent); cc_committed_offer_margin = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true.
  results/calibration/r_ercot20_arm_2024/hourly/system_2024.parquet, results/calibration/r_ercot20_arm_2024/dispatch/2024_P1.parquet and results/calibration/r_ercot20_arm_2024/floors/2024_P1.npz must exist, and dispatch/2024_P1.parquet must contain unit ids for plant codes 34693 and 79003 (grep the unit_id column for "_p34693_" and "_p79003_").
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot20_arm_2024/\n!results/calibration/r_ercot20_arm_2024/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot20_arm_2024
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot20_arm_2024/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-20 ARM 2024: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot20-arm-2024 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot20_arm_2024 | wc -l` > 0 and that it lists dispatch/2024_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2024.parquet rows with pass=='P1'); total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2024.parquet; P1 TWh for plant codes 3469, 34693, 7900, 79003, 56350, 563503 from dispatch/2024_P1.parquet (match unit_id on "_p<code>_"); the signature values you read; anything unexpected.
```

## LEG arm-2025

```text
SHARD R-ERCOT-20 ARM 2025 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-20 (docs/records/ercot/r-ercot/PRECOMMIT-r-ercot-20-gt-split-2026-09-30.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal bf7c1228b9450aea0bb020c48f8d5ccafdae9190. If not, `git fetch origin bf7c1228b9450aea0bb020c48f8d5ccafdae9190 && git checkout bf7c1228b9450aea0bb020c48f8d5ccafdae9190` (detached is fine), then `git checkout -b claude/r-ercot20-arm-2025`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach bf7c1228b9450aea0bb020c48f8d5ccafdae9190, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  deaebee4628527450021fe348bb1359c0ff3a67afa1371c7f7d5a0f4f8ba58c6
  data/raw/reference/master-plant-registry.csv  4e9eb13427521210413370463b44837f6c3fc16b440d1e43246435827ff875dd
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_ct_heat_rates_ERCOT.csv  2b92e7c81261673fcb51a51ff246510668088255e96166bc4da3516ac1531f17
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot19a_span --years 2025 --out-dir results/calibration/r_ercot20_arm_2025 --note "R-ERCOT-20 ARM 2025: keeper 2026-09-30-r-19-eia-923 recipe unchanged, on the GT-split inputs (T H Wharton / Sand Hill / Colorado Bend simple-cycle GTs as CT_PEAKER split children 34693 / 79003 / 563503) - PRECOMMIT-r-ercot-20-gt-split" 2>&1 | tee /tmp/r_ercot20_arm_2025.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot20_arm_2025/run_config.json after the solve:
  scenario_config: ercot_offer_swcap_clip = false; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 4.576; offer_curve_by_group.CT_PEAKER.peak = 13.15; netload_drag_prior_year_commitment_index = true; cc_committed_prior_year_commitment_eligibility = false (or absent); netload_drag_prior_year_hour_profile = false (or absent); cc_committed_offer_margin = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true.
  results/calibration/r_ercot20_arm_2025/hourly/system_2025.parquet, results/calibration/r_ercot20_arm_2025/dispatch/2025_P1.parquet and results/calibration/r_ercot20_arm_2025/floors/2025_P1.npz must exist, and dispatch/2025_P1.parquet must contain unit ids for plant codes 34693 and 79003 (grep the unit_id column for "_p34693_" and "_p79003_").
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot20_arm_2025/\n!results/calibration/r_ercot20_arm_2025/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot20_arm_2025
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot20_arm_2025/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-20 ARM 2025: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot20-arm-2025 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot20_arm_2025 | wc -l` > 0 and that it lists dispatch/2025_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2025.parquet rows with pass=='P1'); total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2025.parquet; P1 TWh for plant codes 3469, 34693, 7900, 79003, 56350, 563503 from dispatch/2025_P1.parquet (match unit_id on "_p<code>_"); the signature values you read; anything unexpected.
```
