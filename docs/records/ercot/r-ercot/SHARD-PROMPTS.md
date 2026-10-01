# R-ERCOT shard prompts (one per leg)
Each shard's launch message names its LEG and the PINNED SHA (the commit that carries this file). Wherever a prompt below says `<PINNED_SHA>`, use the SHA from your launch message. Execute ONLY your own leg's section.

## LEG arm-2019

```text
SHARD R-ERCOT ARM 2019 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT (docs/handoffs/PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot-arm-2019`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/campd-unit-outages.csv            b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv      d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv   2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/reference/custom-bin-assignments.csv 19d726cd5936f8bdc193671be71c593d3976c1913932c74f042f90966c447fcd
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv 3ebfd9b50146bf6246436e121316b2cb740e00e0177dd7f0e9dcdf8fc0d1ab2a
  data/raw/_processed-legacy/chp_power_only_heat_rates_ERCOT.csv 2f1dfd18cf7c80c438dd2e54300daba4857c9ac1d2dbcaa01c6aa4c5c96c1bcc
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified, in the foreground (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/ercot_mer20260919_five_year --years 2019 --out-dir results/calibration/r_ercot_arm_2019 --note "R-ERCOT ARM 2019: incumbent recipe + corrected backcast inputs (vintage EIA-860, year-matched plant HR, short-gas/coal CAMPD windows) — PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24" --set eia860_vintage_tracks_solve_year=true --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true --set ercot_offer_swcap_clip=true --set "offer_curve_by_group=$(cat docs/handoffs/r-ercot/carveout_a_offer_curve_by_group.json)" 2>&1 | tee /tmp/r_ercot_arm_2019.log

Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot_arm_2019/run_config.json -> scenario_config after the solve:
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, measured_chp_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  Also results/calibration/r_ercot_arm_2019/hourly/system_2019.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot_arm_2019/dispatch/2019_P1.parquet must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot_arm_2019/\n!results/calibration/r_ercot_arm_2019/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot_arm_2019
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot_arm_2019/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT ARM 2019: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot-arm-2019 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot_arm_2019 | wc -l` > 0 and that it lists dispatch/2019_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2019.parquet rows with pass=='P1'); total P1 slack MWh; annual P1 TWh by class from hourly/class_hourly_2019.parquet; the signature values you read; the 'R-ERCOT year-matched bin heat rates' log line if present; anything unexpected.

```

## LEG arm-2020

```text
SHARD R-ERCOT ARM 2020 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT (docs/handoffs/PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot-arm-2020`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/campd-unit-outages.csv            b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv      d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv   2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/reference/custom-bin-assignments.csv 19d726cd5936f8bdc193671be71c593d3976c1913932c74f042f90966c447fcd
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv 3ebfd9b50146bf6246436e121316b2cb740e00e0177dd7f0e9dcdf8fc0d1ab2a
  data/raw/_processed-legacy/chp_power_only_heat_rates_ERCOT.csv 2f1dfd18cf7c80c438dd2e54300daba4857c9ac1d2dbcaa01c6aa4c5c96c1bcc
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified, in the foreground (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/ercot_mer20260919_five_year --years 2020 --out-dir results/calibration/r_ercot_arm_2020 --note "R-ERCOT ARM 2020: incumbent recipe + corrected backcast inputs (vintage EIA-860, year-matched plant HR, short-gas/coal CAMPD windows) — PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24" --set eia860_vintage_tracks_solve_year=true --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true --set ercot_offer_swcap_clip=true --set "offer_curve_by_group=$(cat docs/handoffs/r-ercot/carveout_a_offer_curve_by_group.json)" 2>&1 | tee /tmp/r_ercot_arm_2020.log

Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot_arm_2020/run_config.json -> scenario_config after the solve:
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, measured_chp_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  Also results/calibration/r_ercot_arm_2020/hourly/system_2020.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot_arm_2020/dispatch/2020_P1.parquet must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot_arm_2020/\n!results/calibration/r_ercot_arm_2020/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot_arm_2020
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot_arm_2020/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT ARM 2020: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot-arm-2020 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot_arm_2020 | wc -l` > 0 and that it lists dispatch/2020_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2020.parquet rows with pass=='P1'); total P1 slack MWh; annual P1 TWh by class from hourly/class_hourly_2020.parquet; the signature values you read; the 'R-ERCOT year-matched bin heat rates' log line if present; anything unexpected.

```

## LEG arm-2021

```text
SHARD R-ERCOT ARM 2021 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT (docs/handoffs/PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot-arm-2021`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/campd-unit-outages.csv            b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv      d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv   2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/reference/custom-bin-assignments.csv 19d726cd5936f8bdc193671be71c593d3976c1913932c74f042f90966c447fcd
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv 3ebfd9b50146bf6246436e121316b2cb740e00e0177dd7f0e9dcdf8fc0d1ab2a
  data/raw/_processed-legacy/chp_power_only_heat_rates_ERCOT.csv 2f1dfd18cf7c80c438dd2e54300daba4857c9ac1d2dbcaa01c6aa4c5c96c1bcc
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified, in the foreground (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/ercot_mer20260919_five_year --years 2021 --out-dir results/calibration/r_ercot_arm_2021 --note "R-ERCOT ARM 2021: incumbent recipe + corrected backcast inputs (vintage EIA-860, year-matched plant HR, short-gas/coal CAMPD windows) — PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24" --set eia860_vintage_tracks_solve_year=true --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true 2>&1 | tee /tmp/r_ercot_arm_2021.log

Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot_arm_2021/run_config.json -> scenario_config after the solve:
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, measured_chp_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  Also results/calibration/r_ercot_arm_2021/hourly/system_2021.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot_arm_2021/dispatch/2021_P1.parquet must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot_arm_2021/\n!results/calibration/r_ercot_arm_2021/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot_arm_2021
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot_arm_2021/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT ARM 2021: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot-arm-2021 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot_arm_2021 | wc -l` > 0 and that it lists dispatch/2021_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2021.parquet rows with pass=='P1'); total P1 slack MWh; annual P1 TWh by class from hourly/class_hourly_2021.parquet; the signature values you read; the 'R-ERCOT year-matched bin heat rates' log line if present; anything unexpected.

```

## LEG arm-2022

```text
SHARD R-ERCOT ARM 2022 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT (docs/handoffs/PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot-arm-2022`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/campd-unit-outages.csv            b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv      d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv   2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/reference/custom-bin-assignments.csv 19d726cd5936f8bdc193671be71c593d3976c1913932c74f042f90966c447fcd
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv 3ebfd9b50146bf6246436e121316b2cb740e00e0177dd7f0e9dcdf8fc0d1ab2a
  data/raw/_processed-legacy/chp_power_only_heat_rates_ERCOT.csv 2f1dfd18cf7c80c438dd2e54300daba4857c9ac1d2dbcaa01c6aa4c5c96c1bcc
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified, in the foreground (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/ercot_mer20260919_five_year --years 2022 --out-dir results/calibration/r_ercot_arm_2022 --note "R-ERCOT ARM 2022: incumbent recipe + corrected backcast inputs (vintage EIA-860, year-matched plant HR, short-gas/coal CAMPD windows) — PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24" --set eia860_vintage_tracks_solve_year=true --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true 2>&1 | tee /tmp/r_ercot_arm_2022.log

Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot_arm_2022/run_config.json -> scenario_config after the solve:
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, measured_chp_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  Also results/calibration/r_ercot_arm_2022/hourly/system_2022.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot_arm_2022/dispatch/2022_P1.parquet must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot_arm_2022/\n!results/calibration/r_ercot_arm_2022/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot_arm_2022
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot_arm_2022/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT ARM 2022: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot-arm-2022 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot_arm_2022 | wc -l` > 0 and that it lists dispatch/2022_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2022.parquet rows with pass=='P1'); total P1 slack MWh; annual P1 TWh by class from hourly/class_hourly_2022.parquet; the signature values you read; the 'R-ERCOT year-matched bin heat rates' log line if present; anything unexpected.

```

## LEG arm-2023

```text
SHARD R-ERCOT ARM 2023 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT (docs/handoffs/PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot-arm-2023`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/campd-unit-outages.csv            b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv      d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv   2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/reference/custom-bin-assignments.csv 19d726cd5936f8bdc193671be71c593d3976c1913932c74f042f90966c447fcd
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv 3ebfd9b50146bf6246436e121316b2cb740e00e0177dd7f0e9dcdf8fc0d1ab2a
  data/raw/_processed-legacy/chp_power_only_heat_rates_ERCOT.csv 2f1dfd18cf7c80c438dd2e54300daba4857c9ac1d2dbcaa01c6aa4c5c96c1bcc
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified, in the foreground (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/ercot_mer20260919_five_year --years 2023 --out-dir results/calibration/r_ercot_arm_2023 --note "R-ERCOT ARM 2023: incumbent recipe + corrected backcast inputs (vintage EIA-860, year-matched plant HR, short-gas/coal CAMPD windows) — PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24" --set eia860_vintage_tracks_solve_year=true --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true 2>&1 | tee /tmp/r_ercot_arm_2023.log

Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot_arm_2023/run_config.json -> scenario_config after the solve:
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = false; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, measured_chp_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  Also results/calibration/r_ercot_arm_2023/hourly/system_2023.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot_arm_2023/dispatch/2023_P1.parquet must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot_arm_2023/\n!results/calibration/r_ercot_arm_2023/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot_arm_2023
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot_arm_2023/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT ARM 2023: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot-arm-2023 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot_arm_2023 | wc -l` > 0 and that it lists dispatch/2023_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2023.parquet rows with pass=='P1'); total P1 slack MWh; annual P1 TWh by class from hourly/class_hourly_2023.parquet; the signature values you read; the 'R-ERCOT year-matched bin heat rates' log line if present; anything unexpected.

```

## LEG arm-2024

```text
SHARD R-ERCOT ARM 2024 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT (docs/handoffs/PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot-arm-2024`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/campd-unit-outages.csv            b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv      d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv   2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/reference/custom-bin-assignments.csv 19d726cd5936f8bdc193671be71c593d3976c1913932c74f042f90966c447fcd
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv 3ebfd9b50146bf6246436e121316b2cb740e00e0177dd7f0e9dcdf8fc0d1ab2a
  data/raw/_processed-legacy/chp_power_only_heat_rates_ERCOT.csv 2f1dfd18cf7c80c438dd2e54300daba4857c9ac1d2dbcaa01c6aa4c5c96c1bcc
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified, in the foreground (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/ercot_mer20260919_five_year --years 2024 --out-dir results/calibration/r_ercot_arm_2024 --note "R-ERCOT ARM 2024: incumbent recipe + corrected backcast inputs (vintage EIA-860, year-matched plant HR, short-gas/coal CAMPD windows) — PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24" --set eia860_vintage_tracks_solve_year=true --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true 2>&1 | tee /tmp/r_ercot_arm_2024.log

Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot_arm_2024/run_config.json -> scenario_config after the solve:
  ercot_offer_swcap_clip = false; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 4.576; offer_curve_by_group.CT_PEAKER.peak = 13.15;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, measured_chp_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  Also results/calibration/r_ercot_arm_2024/hourly/system_2024.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot_arm_2024/dispatch/2024_P1.parquet must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot_arm_2024/\n!results/calibration/r_ercot_arm_2024/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot_arm_2024
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot_arm_2024/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT ARM 2024: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot-arm-2024 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot_arm_2024 | wc -l` > 0 and that it lists dispatch/2024_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2024.parquet rows with pass=='P1'); total P1 slack MWh; annual P1 TWh by class from hourly/class_hourly_2024.parquet; the signature values you read; the 'R-ERCOT year-matched bin heat rates' log line if present; anything unexpected.

```

## LEG arm-2025

```text
SHARD R-ERCOT ARM 2025 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT (docs/handoffs/PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot-arm-2025`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/campd-unit-outages.csv            b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv      d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv   2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/reference/custom-bin-assignments.csv 19d726cd5936f8bdc193671be71c593d3976c1913932c74f042f90966c447fcd
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv 3ebfd9b50146bf6246436e121316b2cb740e00e0177dd7f0e9dcdf8fc0d1ab2a
  data/raw/_processed-legacy/chp_power_only_heat_rates_ERCOT.csv 2f1dfd18cf7c80c438dd2e54300daba4857c9ac1d2dbcaa01c6aa4c5c96c1bcc
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified, in the foreground (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/ercot_mer20260919_five_year --years 2025 --out-dir results/calibration/r_ercot_arm_2025 --note "R-ERCOT ARM 2025: incumbent recipe + corrected backcast inputs (vintage EIA-860, year-matched plant HR, short-gas/coal CAMPD windows) — PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24" --set eia860_vintage_tracks_solve_year=true --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true 2>&1 | tee /tmp/r_ercot_arm_2025.log

Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot_arm_2025/run_config.json -> scenario_config after the solve:
  ercot_offer_swcap_clip = false; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 4.576; offer_curve_by_group.CT_PEAKER.peak = 13.15;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, measured_chp_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  Also results/calibration/r_ercot_arm_2025/hourly/system_2025.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot_arm_2025/dispatch/2025_P1.parquet must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot_arm_2025/\n!results/calibration/r_ercot_arm_2025/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot_arm_2025
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot_arm_2025/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT ARM 2025: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot-arm-2025 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot_arm_2025 | wc -l` > 0 and that it lists dispatch/2025_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2025.parquet rows with pass=='P1'); total P1 slack MWh; annual P1 TWh by class from hourly/class_hourly_2025.parquet; the signature values you read; the 'R-ERCOT year-matched bin heat rates' log line if present; anything unexpected.

```

## LEG ctl-2021

```text
SHARD R-ERCOT CTL 2021 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT (docs/handoffs/PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot-ctl-2021`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/campd-unit-outages.csv            b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv      d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv   2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/reference/custom-bin-assignments.csv 19d726cd5936f8bdc193671be71c593d3976c1913932c74f042f90966c447fcd
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv 3ebfd9b50146bf6246436e121316b2cb740e00e0177dd7f0e9dcdf8fc0d1ab2a
  data/raw/_processed-legacy/chp_power_only_heat_rates_ERCOT.csv 2f1dfd18cf7c80c438dd2e54300daba4857c9ac1d2dbcaa01c6aa4c5c96c1bcc
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified, in the foreground (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/ercot_mer20260919_five_year --years 2021 --out-dir results/calibration/r_ercot_ctl_2021 --note "R-ERCOT CTL 2021: CONTROL: incumbent recipe at HEAD, F1/R-ERCOT flags pinned off — PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24" --set eia860_vintage_tracks_solve_year=false --set measured_ct_heat_rates=false --set measured_coal_heat_rates=false --set measured_st_heat_rates=false --set measured_cc_heat_rates=false --set measured_chp_heat_rates=false --set unit_outage_short_windows=false --set unit_outage_short_windows_gas=false 2>&1 | tee /tmp/r_ercot_ctl_2021.log

Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot_ctl_2021/run_config.json -> scenario_config after the solve:
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, measured_chp_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = false.
  Also results/calibration/r_ercot_ctl_2021/hourly/system_2021.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot_ctl_2021/dispatch/2021_P1.parquet must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot_ctl_2021/\n!results/calibration/r_ercot_ctl_2021/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot_ctl_2021
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot_ctl_2021/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT CTL 2021: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot-ctl-2021 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot_ctl_2021 | wc -l` > 0 and that it lists dispatch/2021_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2021.parquet rows with pass=='P1'); total P1 slack MWh; annual P1 TWh by class from hourly/class_hourly_2021.parquet; the signature values you read; the 'R-ERCOT year-matched bin heat rates' log line if present; anything unexpected.

```

## LEG ctl-2022

```text
SHARD R-ERCOT CTL 2022 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT (docs/handoffs/PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot-ctl-2022`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/campd-unit-outages.csv            b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv      d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv   2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/reference/custom-bin-assignments.csv 19d726cd5936f8bdc193671be71c593d3976c1913932c74f042f90966c447fcd
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv 3ebfd9b50146bf6246436e121316b2cb740e00e0177dd7f0e9dcdf8fc0d1ab2a
  data/raw/_processed-legacy/chp_power_only_heat_rates_ERCOT.csv 2f1dfd18cf7c80c438dd2e54300daba4857c9ac1d2dbcaa01c6aa4c5c96c1bcc
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified, in the foreground (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/ercot_mer20260919_five_year --years 2022 --out-dir results/calibration/r_ercot_ctl_2022 --note "R-ERCOT CTL 2022: CONTROL: incumbent recipe at HEAD, F1/R-ERCOT flags pinned off — PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24" --set eia860_vintage_tracks_solve_year=false --set measured_ct_heat_rates=false --set measured_coal_heat_rates=false --set measured_st_heat_rates=false --set measured_cc_heat_rates=false --set measured_chp_heat_rates=false --set unit_outage_short_windows=false --set unit_outage_short_windows_gas=false 2>&1 | tee /tmp/r_ercot_ctl_2022.log

Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot_ctl_2022/run_config.json -> scenario_config after the solve:
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, measured_chp_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = false.
  Also results/calibration/r_ercot_ctl_2022/hourly/system_2022.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot_ctl_2022/dispatch/2022_P1.parquet must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot_ctl_2022/\n!results/calibration/r_ercot_ctl_2022/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot_ctl_2022
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot_ctl_2022/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT CTL 2022: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot-ctl-2022 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot_ctl_2022 | wc -l` > 0 and that it lists dispatch/2022_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2022.parquet rows with pass=='P1'); total P1 slack MWh; annual P1 TWh by class from hourly/class_hourly_2022.parquet; the signature values you read; the 'R-ERCOT year-matched bin heat rates' log line if present; anything unexpected.

```

## LEG ctl-2023

```text
SHARD R-ERCOT CTL 2023 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT (docs/handoffs/PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot-ctl-2023`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/campd-unit-outages.csv            b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv      d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv   2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/reference/custom-bin-assignments.csv 19d726cd5936f8bdc193671be71c593d3976c1913932c74f042f90966c447fcd
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv 3ebfd9b50146bf6246436e121316b2cb740e00e0177dd7f0e9dcdf8fc0d1ab2a
  data/raw/_processed-legacy/chp_power_only_heat_rates_ERCOT.csv 2f1dfd18cf7c80c438dd2e54300daba4857c9ac1d2dbcaa01c6aa4c5c96c1bcc
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified, in the foreground (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/ercot_mer20260919_five_year --years 2023 --out-dir results/calibration/r_ercot_ctl_2023 --note "R-ERCOT CTL 2023: CONTROL: incumbent recipe at HEAD, F1/R-ERCOT flags pinned off — PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24" --set eia860_vintage_tracks_solve_year=false --set measured_ct_heat_rates=false --set measured_coal_heat_rates=false --set measured_st_heat_rates=false --set measured_cc_heat_rates=false --set measured_chp_heat_rates=false --set unit_outage_short_windows=false --set unit_outage_short_windows_gas=false 2>&1 | tee /tmp/r_ercot_ctl_2023.log

Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot_ctl_2023/run_config.json -> scenario_config after the solve:
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = false; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, measured_chp_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = false.
  Also results/calibration/r_ercot_ctl_2023/hourly/system_2023.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot_ctl_2023/dispatch/2023_P1.parquet must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot_ctl_2023/\n!results/calibration/r_ercot_ctl_2023/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot_ctl_2023
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot_ctl_2023/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT CTL 2023: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot-ctl-2023 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot_ctl_2023 | wc -l` > 0 and that it lists dispatch/2023_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2023.parquet rows with pass=='P1'); total P1 slack MWh; annual P1 TWh by class from hourly/class_hourly_2023.parquet; the signature values you read; the 'R-ERCOT year-matched bin heat rates' log line if present; anything unexpected.

```

## LEG ctl-2024

```text
SHARD R-ERCOT CTL 2024 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT (docs/handoffs/PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot-ctl-2024`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/campd-unit-outages.csv            b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv      d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv   2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/reference/custom-bin-assignments.csv 19d726cd5936f8bdc193671be71c593d3976c1913932c74f042f90966c447fcd
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv 3ebfd9b50146bf6246436e121316b2cb740e00e0177dd7f0e9dcdf8fc0d1ab2a
  data/raw/_processed-legacy/chp_power_only_heat_rates_ERCOT.csv 2f1dfd18cf7c80c438dd2e54300daba4857c9ac1d2dbcaa01c6aa4c5c96c1bcc
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified, in the foreground (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/ercot_mer20260919_five_year --years 2024 --out-dir results/calibration/r_ercot_ctl_2024 --note "R-ERCOT CTL 2024: CONTROL: incumbent recipe at HEAD, F1/R-ERCOT flags pinned off — PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24" --set eia860_vintage_tracks_solve_year=false --set measured_ct_heat_rates=false --set measured_coal_heat_rates=false --set measured_st_heat_rates=false --set measured_cc_heat_rates=false --set measured_chp_heat_rates=false --set unit_outage_short_windows=false --set unit_outage_short_windows_gas=false 2>&1 | tee /tmp/r_ercot_ctl_2024.log

Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot_ctl_2024/run_config.json -> scenario_config after the solve:
  ercot_offer_swcap_clip = false; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 4.576; offer_curve_by_group.CT_PEAKER.peak = 13.15;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, measured_chp_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = false.
  Also results/calibration/r_ercot_ctl_2024/hourly/system_2024.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot_ctl_2024/dispatch/2024_P1.parquet must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot_ctl_2024/\n!results/calibration/r_ercot_ctl_2024/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot_ctl_2024
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot_ctl_2024/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT CTL 2024: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot-ctl-2024 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot_ctl_2024 | wc -l` > 0 and that it lists dispatch/2024_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2024.parquet rows with pass=='P1'); total P1 slack MWh; annual P1 TWh by class from hourly/class_hourly_2024.parquet; the signature values you read; the 'R-ERCOT year-matched bin heat rates' log line if present; anything unexpected.

```

## LEG ctl-2025

```text
SHARD R-ERCOT CTL 2025 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT (docs/handoffs/PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot-ctl-2025`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/campd-unit-outages.csv            b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv      d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv   2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/reference/custom-bin-assignments.csv 19d726cd5936f8bdc193671be71c593d3976c1913932c74f042f90966c447fcd
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv 3ebfd9b50146bf6246436e121316b2cb740e00e0177dd7f0e9dcdf8fc0d1ab2a
  data/raw/_processed-legacy/chp_power_only_heat_rates_ERCOT.csv 2f1dfd18cf7c80c438dd2e54300daba4857c9ac1d2dbcaa01c6aa4c5c96c1bcc
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified, in the foreground (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/ercot_mer20260919_five_year --years 2025 --out-dir results/calibration/r_ercot_ctl_2025 --note "R-ERCOT CTL 2025: CONTROL: incumbent recipe at HEAD, F1/R-ERCOT flags pinned off — PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24" --set eia860_vintage_tracks_solve_year=false --set measured_ct_heat_rates=false --set measured_coal_heat_rates=false --set measured_st_heat_rates=false --set measured_cc_heat_rates=false --set measured_chp_heat_rates=false --set unit_outage_short_windows=false --set unit_outage_short_windows_gas=false 2>&1 | tee /tmp/r_ercot_ctl_2025.log

Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot_ctl_2025/run_config.json -> scenario_config after the solve:
  ercot_offer_swcap_clip = false; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 4.576; offer_curve_by_group.CT_PEAKER.peak = 13.15;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, measured_chp_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = false.
  Also results/calibration/r_ercot_ctl_2025/hourly/system_2025.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot_ctl_2025/dispatch/2025_P1.parquet must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot_ctl_2025/\n!results/calibration/r_ercot_ctl_2025/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot_ctl_2025
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot_ctl_2025/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT CTL 2025: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot-ctl-2025 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot_ctl_2025 | wc -l` > 0 and that it lists dispatch/2025_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2025.parquet rows with pass=='P1'); total P1 slack MWh; annual P1 TWh by class from hourly/class_hourly_2025.parquet; the signature values you read; the 'R-ERCOT year-matched bin heat rates' log line if present; anything unexpected.

```
