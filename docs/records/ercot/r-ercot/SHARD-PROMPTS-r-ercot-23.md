# R-ERCOT-23 shard prompts (two legs: 2019 and 2021 — rule 36; 2020/2022/2024/2025 recompose from the r-22 legs, G-DRIFT ALL INERT; 2023 owner hold)

Pinned SHA `651723e30ac9598689bffb9782493a58eb493445` (the code + PRECOMMIT commit). Generated from `SHARD-PROMPTS-r-ercot-22.md` with the keeper bundle, out-dir, `--set ercot_swcap_effective_hourly=true` and hard-stop 3 substituted.

> Paths in the prompts below are as they stood at the pinned SHA; `docs/handoffs/r-ercot/` moved to `docs/records/ercot/r-ercot/` in cleanup-C after the shards ran.

## LEG arm-2019

```text
SHARD R-ERCOT-23 ARM 2019 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-23 (docs/handoffs/r-ercot/PRECOMMIT-r-ercot-23-swcap-effective-hourly-2026-10-01.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal 651723e30ac9598689bffb9782493a58eb493445. If not, `git fetch origin 651723e30ac9598689bffb9782493a58eb493445 && git checkout 651723e30ac9598689bffb9782493a58eb493445` (detached is fine), then `git checkout -b claude/r-ercot23-arm-2019`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach 651723e30ac9598689bffb9782493a58eb493445, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  5550b1451d5f07c6e5fd4736ad469376db28a1df6a0830796d41b0c9f9ad2cc0
  data/raw/reference/master-plant-registry.csv  0558423968967e6bf054c5a3b3400dba5e6beb520b9da22167ba94ca6ece9d3e
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  1a1a79c32dee6ee6be6b5a666cd946c0f8101a5cdd63f811c87ed65b4e65e6db
  data/raw/_processed-legacy/campd_ct_heat_rates_ERCOT.csv  2b92e7c81261673fcb51a51ff246510668088255e96166bc4da3516ac1531f17
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
  data/raw/ercot/ercot_2019_ordc_reserves_hourly.parquet  983124c8fa66f1d2537bc687d4bdb71bd67cd3041eea55edc2cccc9d96812614
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot22_span --years 2019 --set ercot_swcap_effective_hourly=true --out-dir results/calibration/r_ercot23_arm_2019 --note "R-ERCOT-23 ARM 2019: keeper 2026-10-01-r-22-ordc-shift recipe unchanged + ercot_swcap_effective_hourly (2021 LCAP window, protocol price cap) - PRECOMMIT-r-ercot-23-swcap-effective-hourly" 2>&1 | tee /tmp/r_ercot23_arm_2019.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot23_arm_2019/run_config.json after the solve:
  scenario_config: ercot_swcap_effective_hourly = true; ordc_lolp_shift_sigma = 0.25; ordc_voll = 9000.0; ordc_mcl_mw = 2000.0; voll = 9000.0; ercot_swcap_vintage = true; ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95; netload_drag_prior_year_commitment_index = true; cc_committed_offer_margin = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true.
  The solve log must NOT contain "ercot_swcap_effective_hourly: ORDC penalties re-anchored" (2019 has no LCAP window).
  results/calibration/r_ercot23_arm_2019/hourly/system_2019.parquet, results/calibration/r_ercot23_arm_2019/dispatch/2019_P1.parquet and results/calibration/r_ercot23_arm_2019/floors/2019_P1.npz must exist, and the summed pmax_mw of dispatch/2019_P1_fleet.parquet rows whose unit_id contains "_p55154_" must be >= 600.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot23_arm_2019/\n!results/calibration/r_ercot23_arm_2019/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot23_arm_2019
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot23_arm_2019/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-23 ARM 2019: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot23-arm-2019 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot23_arm_2019 | wc -l` > 0 and that it lists dispatch/2019_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; the two ercot_swcap_effective_hourly log lines (or their absence); P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2019.parquet rows with pass=='P1'); demand-weighted mean of the ordc_adder column; max over hours of the demand-weighted P1 system price; total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2019.parquet; the signature values you read; anything unexpected.
```

## LEG arm-2021

```text
SHARD R-ERCOT-23 ARM 2021 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-23 (docs/handoffs/r-ercot/PRECOMMIT-r-ercot-23-swcap-effective-hourly-2026-10-01.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal 651723e30ac9598689bffb9782493a58eb493445. If not, `git fetch origin 651723e30ac9598689bffb9782493a58eb493445 && git checkout 651723e30ac9598689bffb9782493a58eb493445` (detached is fine), then `git checkout -b claude/r-ercot23-arm-2021`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach 651723e30ac9598689bffb9782493a58eb493445, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  5550b1451d5f07c6e5fd4736ad469376db28a1df6a0830796d41b0c9f9ad2cc0
  data/raw/reference/master-plant-registry.csv  0558423968967e6bf054c5a3b3400dba5e6beb520b9da22167ba94ca6ece9d3e
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  1a1a79c32dee6ee6be6b5a666cd946c0f8101a5cdd63f811c87ed65b4e65e6db
  data/raw/_processed-legacy/campd_ct_heat_rates_ERCOT.csv  2b92e7c81261673fcb51a51ff246510668088255e96166bc4da3516ac1531f17
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
  data/raw/ercot/ercot_2021_ordc_reserves_hourly.parquet  f6d3a3d04867d6a3be45bbe3dc6fc10448510400c752725deebdb8590fbd18eb
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot22_span --years 2021 --set ercot_swcap_effective_hourly=true --out-dir results/calibration/r_ercot23_arm_2021 --note "R-ERCOT-23 ARM 2021: keeper 2026-10-01-r-22-ordc-shift recipe unchanged + ercot_swcap_effective_hourly (2021 LCAP window, protocol price cap) - PRECOMMIT-r-ercot-23-swcap-effective-hourly" 2>&1 | tee /tmp/r_ercot23_arm_2021.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot23_arm_2021/run_config.json after the solve:
  scenario_config: ercot_swcap_effective_hourly = true; ordc_lolp_shift_sigma = 0.5; ordc_voll = 9000.0; ordc_mcl_mw = 2000.0; voll = 9000.0; ercot_swcap_vintage = true; ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95; netload_drag_prior_year_commitment_index = true; cc_committed_offer_margin = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true.
  The solve log MUST contain "ercot_swcap_effective_hourly: ORDC penalties re-anchored on the effective SWCAP in 7272 of 8760 hours" and "ercot_swcap_effective_hourly: load-shed cost at the effective SWCAP in 7272 of 8760 hours" — if the log carries no INFO-level lines at all, do NOT stop on this check alone; report that instead.
  results/calibration/r_ercot23_arm_2021/hourly/system_2021.parquet, results/calibration/r_ercot23_arm_2021/dispatch/2021_P1.parquet and results/calibration/r_ercot23_arm_2021/floors/2021_P1.npz must exist, and the summed pmax_mw of dispatch/2021_P1_fleet.parquet rows whose unit_id contains "_p55154_" must be >= 600.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot23_arm_2021/\n!results/calibration/r_ercot23_arm_2021/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot23_arm_2021
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot23_arm_2021/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-23 ARM 2021: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot23-arm-2021 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot23_arm_2021 | wc -l` > 0 and that it lists dispatch/2021_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; the two ercot_swcap_effective_hourly log lines (or their absence); P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2021.parquet rows with pass=='P1'); demand-weighted mean of the ordc_adder column; max over hours of the demand-weighted P1 system price; total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2021.parquet; the signature values you read; anything unexpected.
```
