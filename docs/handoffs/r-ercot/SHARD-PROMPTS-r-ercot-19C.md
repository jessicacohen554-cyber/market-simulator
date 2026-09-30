# R-ERCOT-19 arm-C shard prompts (one per year, rule 36)

Arm C = keeper `2026-09-30-r-18-drag-index` recipe + `cc_committed_prior_year_commitment_eligibility=true` ONLY, on the refreshed zonal-gas table. PRECOMMIT addendum B. Solve SHA 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27.

## LEG arm-C-2019

```text
SHARD R-ERCOT-19 ARM-C 2019 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-19 (docs/handoffs/r-ercot/PRECOMMIT-r-ercot-19-south-overrun-and-hub-refresh-2026-09-30.md, addendum B). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27. If not, `git fetch origin 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27 && git checkout 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27` (detached is fine), then `git checkout -b claude/r-ercot19c-arm-2019`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  d13e00143e30075f3c3d5c4976714db38205847c2b4f0fb9aa63247b070a20e7
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
  data/raw/_validation-source/ercot_prior_year_commitment_profile.csv  472af64dfddd50543e2da4b3ccfa25ade3c45ae327de0ebbd108a80bcb738a98
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot18_span --years 2019 --set cc_committed_prior_year_commitment_eligibility=true --out-dir results/calibration/r_ercot19c_arm_2019 --note "R-ERCOT-19 ARM-C 2019: keeper 2026-09-30-r-18-drag-index recipe + cc_committed_prior_year_commitment_eligibility=true ONLY (drag-hour limb off, owner ruling "CC limb only, re-solve") (both FAIL-CLOSED in 2019: no TX 2018 CAMPD vintage; solved for recipe uniformity and as the byte-identity check) — PRECOMMIT-r-ercot-19 addendum B" 2>&1 | tee /tmp/r_ercot19c_arm_2019.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot19c_arm_2019/run_config.json after the solve:
  scenario_config: cc_committed_prior_year_commitment_eligibility = true; netload_drag_prior_year_hour_profile = false; cc_committed_offer_margin = true; netload_drag_prior_year_commitment_index = true; ercot_south_texas_pooled_basis = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true; netload_drag_merit_allocation = false; ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95.
  The solve log must contain both FAIL-CLOSED lines (2019 has no TX 2018 CAMPD vintage by design): "netload_drag_prior_year_commitment_index: no ERCOT 2018 vintage — pro-rata", "cc_committed_prior_year_commitment_eligibility: no ERCOT CC_REGULAR 2018 vintage — fail-closed" (grep "prior_year" /tmp/r_ercot19c_arm_2019.log).
  results/calibration/r_ercot19c_arm_2019/hourly/system_2019.parquet, results/calibration/r_ercot19c_arm_2019/dispatch/2019_P1.parquet and results/calibration/r_ercot19c_arm_2019/floors/2019_P1.npz must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot19c_arm_2019/\n!results/calibration/r_ercot19c_arm_2019/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot19c_arm_2019
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot19c_arm_2019/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-19 ARM-C 2019: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot19c-arm-2019 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot19c_arm_2019 | wc -l` > 0 and that it lists dispatch/2019_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; the "prior_year" log lines verbatim; solve wall-clock; P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2019.parquet rows with pass=='P1'); total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2019.parquet; the signature values you read; anything unexpected.
```

## LEG arm-C-2020

```text
SHARD R-ERCOT-19 ARM-C 2020 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-19 (docs/handoffs/r-ercot/PRECOMMIT-r-ercot-19-south-overrun-and-hub-refresh-2026-09-30.md, addendum B). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27. If not, `git fetch origin 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27 && git checkout 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27` (detached is fine), then `git checkout -b claude/r-ercot19c-arm-2020`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  d13e00143e30075f3c3d5c4976714db38205847c2b4f0fb9aa63247b070a20e7
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
  data/raw/_validation-source/ercot_prior_year_commitment_profile.csv  472af64dfddd50543e2da4b3ccfa25ade3c45ae327de0ebbd108a80bcb738a98
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot18_span --years 2020 --set cc_committed_prior_year_commitment_eligibility=true --out-dir results/calibration/r_ercot19c_arm_2020 --note "R-ERCOT-19 ARM-C 2020: keeper 2026-09-30-r-18-drag-index recipe + cc_committed_prior_year_commitment_eligibility=true ONLY (drag-hour limb off, owner ruling "CC limb only, re-solve") (prior-year measured CAMPD commitment profile weights the ERCOT-139 CC committed-block level and shapes the ST_GAS drag floor; owner decision card 2026-09-30) on the refreshed zonal-gas table — PRECOMMIT-r-ercot-19 addendum B" 2>&1 | tee /tmp/r_ercot19c_arm_2020.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot19c_arm_2020/run_config.json after the solve:
  scenario_config: cc_committed_prior_year_commitment_eligibility = true; netload_drag_prior_year_hour_profile = false; cc_committed_offer_margin = true; netload_drag_prior_year_commitment_index = true; ercot_south_texas_pooled_basis = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true; netload_drag_merit_allocation = false; ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95.
  The solve log must contain both: "netload_drag_prior_year_commitment_index ARMED (ERCOT 2020): vintage 2019, ..." and "cc_committed_prior_year_commitment_eligibility ARMED (ERCOT 2020): vintage 2019, ..." (grep "prior_year" /tmp/r_ercot19c_arm_2020.log).
  results/calibration/r_ercot19c_arm_2020/hourly/system_2020.parquet, results/calibration/r_ercot19c_arm_2020/dispatch/2020_P1.parquet and results/calibration/r_ercot19c_arm_2020/floors/2020_P1.npz must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot19c_arm_2020/\n!results/calibration/r_ercot19c_arm_2020/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot19c_arm_2020
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot19c_arm_2020/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-19 ARM-C 2020: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot19c-arm-2020 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot19c_arm_2020 | wc -l` > 0 and that it lists dispatch/2020_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; the "prior_year" ARMED log lines verbatim; solve wall-clock; P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2020.parquet rows with pass=='P1'); total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2020.parquet; the signature values you read; anything unexpected.
```

## LEG arm-C-2021

```text
SHARD R-ERCOT-19 ARM-C 2021 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-19 (docs/handoffs/r-ercot/PRECOMMIT-r-ercot-19-south-overrun-and-hub-refresh-2026-09-30.md, addendum B). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27. If not, `git fetch origin 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27 && git checkout 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27` (detached is fine), then `git checkout -b claude/r-ercot19c-arm-2021`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  d13e00143e30075f3c3d5c4976714db38205847c2b4f0fb9aa63247b070a20e7
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
  data/raw/_validation-source/ercot_prior_year_commitment_profile.csv  472af64dfddd50543e2da4b3ccfa25ade3c45ae327de0ebbd108a80bcb738a98
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot18_span --years 2021 --set cc_committed_prior_year_commitment_eligibility=true --out-dir results/calibration/r_ercot19c_arm_2021 --note "R-ERCOT-19 ARM-C 2021: keeper 2026-09-30-r-18-drag-index recipe + cc_committed_prior_year_commitment_eligibility=true ONLY (drag-hour limb off, owner ruling "CC limb only, re-solve") (prior-year measured CAMPD commitment profile weights the ERCOT-139 CC committed-block level and shapes the ST_GAS drag floor; owner decision card 2026-09-30) on the refreshed zonal-gas table — PRECOMMIT-r-ercot-19 addendum B" 2>&1 | tee /tmp/r_ercot19c_arm_2021.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot19c_arm_2021/run_config.json after the solve:
  scenario_config: cc_committed_prior_year_commitment_eligibility = true; netload_drag_prior_year_hour_profile = false; cc_committed_offer_margin = true; netload_drag_prior_year_commitment_index = true; ercot_south_texas_pooled_basis = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true; netload_drag_merit_allocation = false; ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95.
  The solve log must contain both: "netload_drag_prior_year_commitment_index ARMED (ERCOT 2021): vintage 2020, ..." and "cc_committed_prior_year_commitment_eligibility ARMED (ERCOT 2021): vintage 2020, ..." (grep "prior_year" /tmp/r_ercot19c_arm_2021.log).
  results/calibration/r_ercot19c_arm_2021/hourly/system_2021.parquet, results/calibration/r_ercot19c_arm_2021/dispatch/2021_P1.parquet and results/calibration/r_ercot19c_arm_2021/floors/2021_P1.npz must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot19c_arm_2021/\n!results/calibration/r_ercot19c_arm_2021/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot19c_arm_2021
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot19c_arm_2021/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-19 ARM-C 2021: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot19c-arm-2021 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot19c_arm_2021 | wc -l` > 0 and that it lists dispatch/2021_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; the "prior_year" ARMED log lines verbatim; solve wall-clock; P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2021.parquet rows with pass=='P1'); total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2021.parquet; the signature values you read; anything unexpected.
```

## LEG arm-C-2022

```text
SHARD R-ERCOT-19 ARM-C 2022 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-19 (docs/handoffs/r-ercot/PRECOMMIT-r-ercot-19-south-overrun-and-hub-refresh-2026-09-30.md, addendum B). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27. If not, `git fetch origin 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27 && git checkout 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27` (detached is fine), then `git checkout -b claude/r-ercot19c-arm-2022`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  d13e00143e30075f3c3d5c4976714db38205847c2b4f0fb9aa63247b070a20e7
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
  data/raw/_validation-source/ercot_prior_year_commitment_profile.csv  472af64dfddd50543e2da4b3ccfa25ade3c45ae327de0ebbd108a80bcb738a98
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot18_span --years 2022 --set cc_committed_prior_year_commitment_eligibility=true --out-dir results/calibration/r_ercot19c_arm_2022 --note "R-ERCOT-19 ARM-C 2022: keeper 2026-09-30-r-18-drag-index recipe + cc_committed_prior_year_commitment_eligibility=true ONLY (drag-hour limb off, owner ruling "CC limb only, re-solve") (prior-year measured CAMPD commitment profile weights the ERCOT-139 CC committed-block level and shapes the ST_GAS drag floor; owner decision card 2026-09-30) on the refreshed zonal-gas table — PRECOMMIT-r-ercot-19 addendum B" 2>&1 | tee /tmp/r_ercot19c_arm_2022.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot19c_arm_2022/run_config.json after the solve:
  scenario_config: cc_committed_prior_year_commitment_eligibility = true; netload_drag_prior_year_hour_profile = false; cc_committed_offer_margin = true; netload_drag_prior_year_commitment_index = true; ercot_south_texas_pooled_basis = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true; netload_drag_merit_allocation = false; ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95.
  The solve log must contain both: "netload_drag_prior_year_commitment_index ARMED (ERCOT 2022): vintage 2021, ..." and "cc_committed_prior_year_commitment_eligibility ARMED (ERCOT 2022): vintage 2021, ..." (grep "prior_year" /tmp/r_ercot19c_arm_2022.log).
  results/calibration/r_ercot19c_arm_2022/hourly/system_2022.parquet, results/calibration/r_ercot19c_arm_2022/dispatch/2022_P1.parquet and results/calibration/r_ercot19c_arm_2022/floors/2022_P1.npz must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot19c_arm_2022/\n!results/calibration/r_ercot19c_arm_2022/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot19c_arm_2022
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot19c_arm_2022/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-19 ARM-C 2022: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot19c-arm-2022 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot19c_arm_2022 | wc -l` > 0 and that it lists dispatch/2022_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; the "prior_year" ARMED log lines verbatim; solve wall-clock; P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2022.parquet rows with pass=='P1'); total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2022.parquet; the signature values you read; anything unexpected.
```

## LEG arm-C-2023

```text
SHARD R-ERCOT-19 ARM-C 2023 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-19 (docs/handoffs/r-ercot/PRECOMMIT-r-ercot-19-south-overrun-and-hub-refresh-2026-09-30.md, addendum B). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27. If not, `git fetch origin 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27 && git checkout 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27` (detached is fine), then `git checkout -b claude/r-ercot19c-arm-2023`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  d13e00143e30075f3c3d5c4976714db38205847c2b4f0fb9aa63247b070a20e7
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
  data/raw/_validation-source/ercot_prior_year_commitment_profile.csv  472af64dfddd50543e2da4b3ccfa25ade3c45ae327de0ebbd108a80bcb738a98
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot18_span --years 2023 --set cc_committed_prior_year_commitment_eligibility=true --out-dir results/calibration/r_ercot19c_arm_2023 --note "R-ERCOT-19 ARM-C 2023: keeper 2026-09-30-r-18-drag-index recipe + cc_committed_prior_year_commitment_eligibility=true ONLY (drag-hour limb off, owner ruling "CC limb only, re-solve") (prior-year measured CAMPD commitment profile weights the ERCOT-139 CC committed-block level and shapes the ST_GAS drag floor; owner decision card 2026-09-30) on the refreshed zonal-gas table — PRECOMMIT-r-ercot-19 addendum B" 2>&1 | tee /tmp/r_ercot19c_arm_2023.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot19c_arm_2023/run_config.json after the solve:
  scenario_config: cc_committed_prior_year_commitment_eligibility = true; netload_drag_prior_year_hour_profile = false; cc_committed_offer_margin = true; netload_drag_prior_year_commitment_index = true; ercot_south_texas_pooled_basis = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true; netload_drag_merit_allocation = false; ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = false; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95.
  The solve log must contain both: "netload_drag_prior_year_commitment_index ARMED (ERCOT 2023): vintage 2022, ..." and "cc_committed_prior_year_commitment_eligibility ARMED (ERCOT 2023): vintage 2022, ..." (grep "prior_year" /tmp/r_ercot19c_arm_2023.log).
  results/calibration/r_ercot19c_arm_2023/hourly/system_2023.parquet, results/calibration/r_ercot19c_arm_2023/dispatch/2023_P1.parquet and results/calibration/r_ercot19c_arm_2023/floors/2023_P1.npz must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot19c_arm_2023/\n!results/calibration/r_ercot19c_arm_2023/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot19c_arm_2023
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot19c_arm_2023/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-19 ARM-C 2023: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot19c-arm-2023 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot19c_arm_2023 | wc -l` > 0 and that it lists dispatch/2023_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; the "prior_year" ARMED log lines verbatim; solve wall-clock; P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2023.parquet rows with pass=='P1'); total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2023.parquet; the signature values you read; anything unexpected.
```

## LEG arm-C-2024

```text
SHARD R-ERCOT-19 ARM-C 2024 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-19 (docs/handoffs/r-ercot/PRECOMMIT-r-ercot-19-south-overrun-and-hub-refresh-2026-09-30.md, addendum B). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27. If not, `git fetch origin 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27 && git checkout 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27` (detached is fine), then `git checkout -b claude/r-ercot19c-arm-2024`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  d13e00143e30075f3c3d5c4976714db38205847c2b4f0fb9aa63247b070a20e7
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
  data/raw/_validation-source/ercot_prior_year_commitment_profile.csv  472af64dfddd50543e2da4b3ccfa25ade3c45ae327de0ebbd108a80bcb738a98
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot18_span --years 2024 --set cc_committed_prior_year_commitment_eligibility=true --out-dir results/calibration/r_ercot19c_arm_2024 --note "R-ERCOT-19 ARM-C 2024: keeper 2026-09-30-r-18-drag-index recipe + cc_committed_prior_year_commitment_eligibility=true ONLY (drag-hour limb off, owner ruling "CC limb only, re-solve") (prior-year measured CAMPD commitment profile weights the ERCOT-139 CC committed-block level and shapes the ST_GAS drag floor; owner decision card 2026-09-30) on the refreshed zonal-gas table — PRECOMMIT-r-ercot-19 addendum B" 2>&1 | tee /tmp/r_ercot19c_arm_2024.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot19c_arm_2024/run_config.json after the solve:
  scenario_config: cc_committed_prior_year_commitment_eligibility = true; netload_drag_prior_year_hour_profile = false; cc_committed_offer_margin = true; netload_drag_prior_year_commitment_index = true; ercot_south_texas_pooled_basis = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true; netload_drag_merit_allocation = false; ercot_offer_swcap_clip = false; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 4.576; offer_curve_by_group.CT_PEAKER.peak = 13.15.
  The solve log must contain both: "netload_drag_prior_year_commitment_index ARMED (ERCOT 2024): vintage 2023, ..." and "cc_committed_prior_year_commitment_eligibility ARMED (ERCOT 2024): vintage 2023, ..." (grep "prior_year" /tmp/r_ercot19c_arm_2024.log).
  results/calibration/r_ercot19c_arm_2024/hourly/system_2024.parquet, results/calibration/r_ercot19c_arm_2024/dispatch/2024_P1.parquet and results/calibration/r_ercot19c_arm_2024/floors/2024_P1.npz must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot19c_arm_2024/\n!results/calibration/r_ercot19c_arm_2024/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot19c_arm_2024
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot19c_arm_2024/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-19 ARM-C 2024: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot19c-arm-2024 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot19c_arm_2024 | wc -l` > 0 and that it lists dispatch/2024_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; the "prior_year" ARMED log lines verbatim; solve wall-clock; P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2024.parquet rows with pass=='P1'); total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2024.parquet; the signature values you read; anything unexpected.
```

## LEG arm-C-2025

```text
SHARD R-ERCOT-19 ARM-C 2025 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-19 (docs/handoffs/r-ercot/PRECOMMIT-r-ercot-19-south-overrun-and-hub-refresh-2026-09-30.md, addendum B). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 45 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27. If not, `git fetch origin 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27 && git checkout 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27` (detached is fine), then `git checkout -b claude/r-ercot19c-arm-2025`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach 41e0f2422bf7147a2f66652aa5bcefeffe0d1e27, STOP and report. A slow fetch is normal: WAIT for it in the foreground; never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata`.

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv  6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv  837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet  bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages-hourgrain.csv  c72e4645175d5a2c1a5b7c5eb736d54686bf4186152497b2a18cb32b4ad8353d
  data/raw/campd-unit-outages-short-hourgrain.csv  11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv  43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv  d13e00143e30075f3c3d5c4976714db38205847c2b4f0fb9aa63247b070a20e7
  data/raw/reference/ercot-dam-plant-crosswalk.csv  bfe4a9c89b3e92b3c4e3ede5223bd97fbf425682ddb621744a0e61720e133eb5
  data/raw/_processed-legacy/campd_coal_heat_rates_ERCOT.csv  a32bff14195cf649aa3cca7cafe1dc7b0a1c56dc5fabfb3806b836e643475929
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv  b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv  633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
  data/raw/ercot_zonal_gas_hub.csv  a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26
  data/raw/_validation-source/ercot_stgas_overnight_commitment.csv  285c74f13b862ca2f888f803d0f9c222d5a18638210ec15f3eb8a0fa4028c0de
  data/raw/_validation-source/ercot_prior_year_commitment_profile.csv  472af64dfddd50543e2da4b3ccfa25ade3c45ae327de0ebbd108a80bcb738a98
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot18_span --years 2025 --set cc_committed_prior_year_commitment_eligibility=true --out-dir results/calibration/r_ercot19c_arm_2025 --note "R-ERCOT-19 ARM-C 2025: keeper 2026-09-30-r-18-drag-index recipe + cc_committed_prior_year_commitment_eligibility=true ONLY (drag-hour limb off, owner ruling "CC limb only, re-solve") (prior-year measured CAMPD commitment profile weights the ERCOT-139 CC committed-block level and shapes the ST_GAS drag floor; owner decision card 2026-09-30) on the refreshed zonal-gas table — PRECOMMIT-r-ercot-19 addendum B" 2>&1 | tee /tmp/r_ercot19c_arm_2025.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot19c_arm_2025/run_config.json after the solve:
  scenario_config: cc_committed_prior_year_commitment_eligibility = true; netload_drag_prior_year_hour_profile = false; cc_committed_offer_margin = true; netload_drag_prior_year_commitment_index = true; ercot_south_texas_pooled_basis = true; gas_st_netload_drag = true; netload_drag_layup_window_mask = true; netload_drag_merit_allocation = false; ercot_offer_swcap_clip = false; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 4.576; offer_curve_by_group.CT_PEAKER.peak = 13.15.
  The solve log must contain both: "netload_drag_prior_year_commitment_index ARMED (ERCOT 2025): vintage 2024, ..." and "cc_committed_prior_year_commitment_eligibility ARMED (ERCOT 2025): vintage 2024, ..." (grep "prior_year" /tmp/r_ercot19c_arm_2025.log).
  results/calibration/r_ercot19c_arm_2025/hourly/system_2025.parquet, results/calibration/r_ercot19c_arm_2025/dispatch/2025_P1.parquet and results/calibration/r_ercot19c_arm_2025/floors/2025_P1.npz must exist.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot19c_arm_2025/\n!results/calibration/r_ercot19c_arm_2025/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot19c_arm_2025
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot19c_arm_2025/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-19 ARM-C 2025: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot19c-arm-2025 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot19c_arm_2025 | wc -l` > 0 and that it lists dispatch/2025_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/, scripts/ or data/; opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; the "prior_year" ARMED log lines verbatim; solve wall-clock; P1 load-weighted mean price (sum(price*demand)/sum(demand) over hourly/system_2025.parquet rows with pass=='P1'); total P1 slack MWh; hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2025.parquet; the signature values you read; anything unexpected.
```
