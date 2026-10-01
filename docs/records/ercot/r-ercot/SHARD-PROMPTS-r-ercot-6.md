# R-ERCOT-6 shard prompts (one per year)

Each shard's launch message names its YEAR and the PINNED SHA (the commit that carries this file). Wherever a prompt says `<PINNED_SHA>`, use the SHA from your launch message. Execute ONLY your own year's section.

## LEG arm-2019

```text
SHARD R-ERCOT-6 ARM 2019 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-6 (docs/handoffs/PRECOMMIT-r-ercot-6-unit-scoped-event-cap-2026-09-26.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot6-arm-2019`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report. A slow fetch is normal: WAIT for it in the foreground (long timeout / until-loop); never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv          6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv   837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages.csv                      b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv                d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv             2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/campd-unit-outages-hourgrain.csv            9f57063cc84f4017cd389d174863e5a7e0ff7d8d9dae6dd5ad06a04ca2e887a9
  data/raw/campd-unit-outages-short-hourgrain.csv      11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv   6b592d028a856e3d0cfe536128ff3c1fef84a57b48c356a46d8af09afc9bd761
  data/raw/reference/custom-bin-assignments.csv        90223446c501d524ca4216ed284863ad4b4a82a7f8b40210065d9ca8a465e222
  data/raw/campd-partial-outages-shaped.csv            720cb71f75bd6fb42ee572d5677951361be03929f1781f44666b4b2e88fa9295
  data/raw/campd-partial-outages-shaped-dayguard.csv   9d18dc2948f96a50403506a47c01f6b7b84ace6682bee7a139104723e0e313da
  data/raw/campd-partial-outages-units.csv             6c2541198016eb671845cc5b52baf530aa2efd7eab83ff81bfbb3aa7b87b0515
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot5_hourgrain_span --years 2019 --out-dir results/calibration/r_ercot6_arm_2019 --note "R-ERCOT-6 ARM 2019: keeper 2026-09-25-r-5-hour-grain recipe with ercot_dam_availability_event_cap_unit_scoped=true (ercot-174 unit-scoped window x partial composition, shared-unit mask at the window hour grain) — PRECOMMIT-r-ercot-6-unit-scoped-event-cap-2026-09-26" --set ercot_dam_availability_event_cap_unit_scoped=true 2>&1 | tee /tmp/r_ercot6_arm_2019.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot6_arm_2019/run_config.json after the solve:
  scenario_config: ercot_dam_availability_event_cap_unit_scoped = true; ercot_dam_availability_event_cap_reconciliation = false; ercot_dam_availability_coal_event_cap = true; ercot_dam_availability_gas_event_cap = true; unit_outage_window_hour_grain = true; ercot_partial_outage_day_guard = true; ercot_partial_outage_shaped_derate = true; measured_chp_heat_rates = false;
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  The resolved-input record in the same file (search for "campd_unit_outages") must show "path": "data/raw/campd-unit-outages-hourgrain.csv" with sha256 9f57063cc84f4017cd389d174863e5a7e0ff7d8d9dae6dd5ad06a04ca2e887a9.
  Also results/calibration/r_ercot6_arm_2019/hourly/system_2019.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot6_arm_2019/dispatch/2019_P1.parquet must exist.
  The solve log (/tmp/r_ercot6_arm_2019.log) must contain the line "ERCOT unit-scoped event-cap composition (2019)" with a NON-ZERO bin count; report that line verbatim.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot6_arm_2019/\n!results/calibration/r_ercot6_arm_2019/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot6_arm_2019
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot6_arm_2019/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-6 ARM 2019: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot6-arm-2019 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot6_arm_2019 | wc -l` > 0 and that it lists dispatch/2019_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2019.parquet rows with pass=='P1'); total P1 slack MWh; number of hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2019.parquet; the signature values and resolved-input path you read; anything unexpected.
```

## LEG arm-2020

```text
SHARD R-ERCOT-6 ARM 2020 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-6 (docs/handoffs/PRECOMMIT-r-ercot-6-unit-scoped-event-cap-2026-09-26.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot6-arm-2020`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report. A slow fetch is normal: WAIT for it in the foreground (long timeout / until-loop); never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv          6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv   837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages.csv                      b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv                d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv             2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/campd-unit-outages-hourgrain.csv            9f57063cc84f4017cd389d174863e5a7e0ff7d8d9dae6dd5ad06a04ca2e887a9
  data/raw/campd-unit-outages-short-hourgrain.csv      11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv   6b592d028a856e3d0cfe536128ff3c1fef84a57b48c356a46d8af09afc9bd761
  data/raw/reference/custom-bin-assignments.csv        90223446c501d524ca4216ed284863ad4b4a82a7f8b40210065d9ca8a465e222
  data/raw/campd-partial-outages-shaped.csv            720cb71f75bd6fb42ee572d5677951361be03929f1781f44666b4b2e88fa9295
  data/raw/campd-partial-outages-shaped-dayguard.csv   9d18dc2948f96a50403506a47c01f6b7b84ace6682bee7a139104723e0e313da
  data/raw/campd-partial-outages-units.csv             6c2541198016eb671845cc5b52baf530aa2efd7eab83ff81bfbb3aa7b87b0515
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot5_hourgrain_span --years 2020 --out-dir results/calibration/r_ercot6_arm_2020 --note "R-ERCOT-6 ARM 2020: keeper 2026-09-25-r-5-hour-grain recipe with ercot_dam_availability_event_cap_unit_scoped=true (ercot-174 unit-scoped window x partial composition, shared-unit mask at the window hour grain) — PRECOMMIT-r-ercot-6-unit-scoped-event-cap-2026-09-26" --set ercot_dam_availability_event_cap_unit_scoped=true 2>&1 | tee /tmp/r_ercot6_arm_2020.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot6_arm_2020/run_config.json after the solve:
  scenario_config: ercot_dam_availability_event_cap_unit_scoped = true; ercot_dam_availability_event_cap_reconciliation = false; ercot_dam_availability_coal_event_cap = true; ercot_dam_availability_gas_event_cap = true; unit_outage_window_hour_grain = true; ercot_partial_outage_day_guard = true; ercot_partial_outage_shaped_derate = true; measured_chp_heat_rates = false;
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  The resolved-input record in the same file (search for "campd_unit_outages") must show "path": "data/raw/campd-unit-outages-hourgrain.csv" with sha256 9f57063cc84f4017cd389d174863e5a7e0ff7d8d9dae6dd5ad06a04ca2e887a9.
  Also results/calibration/r_ercot6_arm_2020/hourly/system_2020.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot6_arm_2020/dispatch/2020_P1.parquet must exist.
  The solve log (/tmp/r_ercot6_arm_2020.log) must contain the line "ERCOT unit-scoped event-cap composition (2020)" with a NON-ZERO bin count; report that line verbatim.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot6_arm_2020/\n!results/calibration/r_ercot6_arm_2020/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot6_arm_2020
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot6_arm_2020/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-6 ARM 2020: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot6-arm-2020 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot6_arm_2020 | wc -l` > 0 and that it lists dispatch/2020_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2020.parquet rows with pass=='P1'); total P1 slack MWh; number of hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2020.parquet; the signature values and resolved-input path you read; anything unexpected.
```

## LEG arm-2021

```text
SHARD R-ERCOT-6 ARM 2021 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-6 (docs/handoffs/PRECOMMIT-r-ercot-6-unit-scoped-event-cap-2026-09-26.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot6-arm-2021`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report. A slow fetch is normal: WAIT for it in the foreground (long timeout / until-loop); never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv          6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv   837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages.csv                      b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv                d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv             2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/campd-unit-outages-hourgrain.csv            9f57063cc84f4017cd389d174863e5a7e0ff7d8d9dae6dd5ad06a04ca2e887a9
  data/raw/campd-unit-outages-short-hourgrain.csv      11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv   6b592d028a856e3d0cfe536128ff3c1fef84a57b48c356a46d8af09afc9bd761
  data/raw/reference/custom-bin-assignments.csv        90223446c501d524ca4216ed284863ad4b4a82a7f8b40210065d9ca8a465e222
  data/raw/campd-partial-outages-shaped.csv            720cb71f75bd6fb42ee572d5677951361be03929f1781f44666b4b2e88fa9295
  data/raw/campd-partial-outages-shaped-dayguard.csv   9d18dc2948f96a50403506a47c01f6b7b84ace6682bee7a139104723e0e313da
  data/raw/campd-partial-outages-units.csv             6c2541198016eb671845cc5b52baf530aa2efd7eab83ff81bfbb3aa7b87b0515
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot5_hourgrain_span --years 2021 --out-dir results/calibration/r_ercot6_arm_2021 --note "R-ERCOT-6 ARM 2021: keeper 2026-09-25-r-5-hour-grain recipe with ercot_dam_availability_event_cap_unit_scoped=true (ercot-174 unit-scoped window x partial composition, shared-unit mask at the window hour grain) — PRECOMMIT-r-ercot-6-unit-scoped-event-cap-2026-09-26" --set ercot_dam_availability_event_cap_unit_scoped=true 2>&1 | tee /tmp/r_ercot6_arm_2021.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot6_arm_2021/run_config.json after the solve:
  scenario_config: ercot_dam_availability_event_cap_unit_scoped = true; ercot_dam_availability_event_cap_reconciliation = false; ercot_dam_availability_coal_event_cap = true; ercot_dam_availability_gas_event_cap = true; unit_outage_window_hour_grain = true; ercot_partial_outage_day_guard = true; ercot_partial_outage_shaped_derate = true; measured_chp_heat_rates = false;
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  The resolved-input record in the same file (search for "campd_unit_outages") must show "path": "data/raw/campd-unit-outages-hourgrain.csv" with sha256 9f57063cc84f4017cd389d174863e5a7e0ff7d8d9dae6dd5ad06a04ca2e887a9.
  Also results/calibration/r_ercot6_arm_2021/hourly/system_2021.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot6_arm_2021/dispatch/2021_P1.parquet must exist.
  The solve log (/tmp/r_ercot6_arm_2021.log) must contain the line "ERCOT unit-scoped event-cap composition (2021)" with a NON-ZERO bin count; report that line verbatim.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot6_arm_2021/\n!results/calibration/r_ercot6_arm_2021/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot6_arm_2021
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot6_arm_2021/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-6 ARM 2021: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot6-arm-2021 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot6_arm_2021 | wc -l` > 0 and that it lists dispatch/2021_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2021.parquet rows with pass=='P1'); total P1 slack MWh; number of hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2021.parquet; the signature values and resolved-input path you read; anything unexpected.
```

## LEG arm-2022

```text
SHARD R-ERCOT-6 ARM 2022 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-6 (docs/handoffs/PRECOMMIT-r-ercot-6-unit-scoped-event-cap-2026-09-26.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot6-arm-2022`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report. A slow fetch is normal: WAIT for it in the foreground (long timeout / until-loop); never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv          6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv   837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages.csv                      b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv                d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv             2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/campd-unit-outages-hourgrain.csv            9f57063cc84f4017cd389d174863e5a7e0ff7d8d9dae6dd5ad06a04ca2e887a9
  data/raw/campd-unit-outages-short-hourgrain.csv      11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv   6b592d028a856e3d0cfe536128ff3c1fef84a57b48c356a46d8af09afc9bd761
  data/raw/reference/custom-bin-assignments.csv        90223446c501d524ca4216ed284863ad4b4a82a7f8b40210065d9ca8a465e222
  data/raw/campd-partial-outages-shaped.csv            720cb71f75bd6fb42ee572d5677951361be03929f1781f44666b4b2e88fa9295
  data/raw/campd-partial-outages-shaped-dayguard.csv   9d18dc2948f96a50403506a47c01f6b7b84ace6682bee7a139104723e0e313da
  data/raw/campd-partial-outages-units.csv             6c2541198016eb671845cc5b52baf530aa2efd7eab83ff81bfbb3aa7b87b0515
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot5_hourgrain_span --years 2022 --out-dir results/calibration/r_ercot6_arm_2022 --note "R-ERCOT-6 ARM 2022: keeper 2026-09-25-r-5-hour-grain recipe with ercot_dam_availability_event_cap_unit_scoped=true (ercot-174 unit-scoped window x partial composition, shared-unit mask at the window hour grain) — PRECOMMIT-r-ercot-6-unit-scoped-event-cap-2026-09-26" --set ercot_dam_availability_event_cap_unit_scoped=true 2>&1 | tee /tmp/r_ercot6_arm_2022.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot6_arm_2022/run_config.json after the solve:
  scenario_config: ercot_dam_availability_event_cap_unit_scoped = true; ercot_dam_availability_event_cap_reconciliation = false; ercot_dam_availability_coal_event_cap = true; ercot_dam_availability_gas_event_cap = true; unit_outage_window_hour_grain = true; ercot_partial_outage_day_guard = true; ercot_partial_outage_shaped_derate = true; measured_chp_heat_rates = false;
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  The resolved-input record in the same file (search for "campd_unit_outages") must show "path": "data/raw/campd-unit-outages-hourgrain.csv" with sha256 9f57063cc84f4017cd389d174863e5a7e0ff7d8d9dae6dd5ad06a04ca2e887a9.
  Also results/calibration/r_ercot6_arm_2022/hourly/system_2022.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot6_arm_2022/dispatch/2022_P1.parquet must exist.
  The solve log (/tmp/r_ercot6_arm_2022.log) must contain the line "ERCOT unit-scoped event-cap composition (2022)" with a NON-ZERO bin count; report that line verbatim.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot6_arm_2022/\n!results/calibration/r_ercot6_arm_2022/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot6_arm_2022
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot6_arm_2022/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-6 ARM 2022: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot6-arm-2022 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot6_arm_2022 | wc -l` > 0 and that it lists dispatch/2022_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2022.parquet rows with pass=='P1'); total P1 slack MWh; number of hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2022.parquet; the signature values and resolved-input path you read; anything unexpected.
```

## LEG arm-2023

```text
SHARD R-ERCOT-6 ARM 2023 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-6 (docs/handoffs/PRECOMMIT-r-ercot-6-unit-scoped-event-cap-2026-09-26.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot6-arm-2023`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report. A slow fetch is normal: WAIT for it in the foreground (long timeout / until-loop); never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv          6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv   837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages.csv                      b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv                d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv             2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/campd-unit-outages-hourgrain.csv            9f57063cc84f4017cd389d174863e5a7e0ff7d8d9dae6dd5ad06a04ca2e887a9
  data/raw/campd-unit-outages-short-hourgrain.csv      11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv   6b592d028a856e3d0cfe536128ff3c1fef84a57b48c356a46d8af09afc9bd761
  data/raw/reference/custom-bin-assignments.csv        90223446c501d524ca4216ed284863ad4b4a82a7f8b40210065d9ca8a465e222
  data/raw/campd-partial-outages-shaped.csv            720cb71f75bd6fb42ee572d5677951361be03929f1781f44666b4b2e88fa9295
  data/raw/campd-partial-outages-shaped-dayguard.csv   9d18dc2948f96a50403506a47c01f6b7b84ace6682bee7a139104723e0e313da
  data/raw/campd-partial-outages-units.csv             6c2541198016eb671845cc5b52baf530aa2efd7eab83ff81bfbb3aa7b87b0515
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot5_hourgrain_span --years 2023 --out-dir results/calibration/r_ercot6_arm_2023 --note "R-ERCOT-6 ARM 2023: keeper 2026-09-25-r-5-hour-grain recipe with ercot_dam_availability_event_cap_unit_scoped=true (ercot-174 unit-scoped window x partial composition, shared-unit mask at the window hour grain) — PRECOMMIT-r-ercot-6-unit-scoped-event-cap-2026-09-26" --set ercot_dam_availability_event_cap_unit_scoped=true 2>&1 | tee /tmp/r_ercot6_arm_2023.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot6_arm_2023/run_config.json after the solve:
  scenario_config: ercot_dam_availability_event_cap_unit_scoped = true; ercot_dam_availability_event_cap_reconciliation = false; ercot_dam_availability_coal_event_cap = true; ercot_dam_availability_gas_event_cap = true; unit_outage_window_hour_grain = true; ercot_partial_outage_day_guard = true; ercot_partial_outage_shaped_derate = true; measured_chp_heat_rates = false;
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = false; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  The resolved-input record in the same file (search for "campd_unit_outages") must show "path": "data/raw/campd-unit-outages-hourgrain.csv" with sha256 9f57063cc84f4017cd389d174863e5a7e0ff7d8d9dae6dd5ad06a04ca2e887a9.
  Also results/calibration/r_ercot6_arm_2023/hourly/system_2023.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot6_arm_2023/dispatch/2023_P1.parquet must exist.
  The solve log (/tmp/r_ercot6_arm_2023.log) must contain the line "ERCOT unit-scoped event-cap composition (2023)" with a NON-ZERO bin count; report that line verbatim.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot6_arm_2023/\n!results/calibration/r_ercot6_arm_2023/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot6_arm_2023
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot6_arm_2023/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-6 ARM 2023: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot6-arm-2023 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot6_arm_2023 | wc -l` > 0 and that it lists dispatch/2023_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2023.parquet rows with pass=='P1'); total P1 slack MWh; number of hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2023.parquet; the signature values and resolved-input path you read; anything unexpected.
```

## LEG arm-2024

```text
SHARD R-ERCOT-6 ARM 2024 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-6 (docs/handoffs/PRECOMMIT-r-ercot-6-unit-scoped-event-cap-2026-09-26.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot6-arm-2024`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report. A slow fetch is normal: WAIT for it in the foreground (long timeout / until-loop); never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv          6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv   837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages.csv                      b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv                d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv             2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/campd-unit-outages-hourgrain.csv            9f57063cc84f4017cd389d174863e5a7e0ff7d8d9dae6dd5ad06a04ca2e887a9
  data/raw/campd-unit-outages-short-hourgrain.csv      11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv   6b592d028a856e3d0cfe536128ff3c1fef84a57b48c356a46d8af09afc9bd761
  data/raw/reference/custom-bin-assignments.csv        90223446c501d524ca4216ed284863ad4b4a82a7f8b40210065d9ca8a465e222
  data/raw/campd-partial-outages-shaped.csv            720cb71f75bd6fb42ee572d5677951361be03929f1781f44666b4b2e88fa9295
  data/raw/campd-partial-outages-shaped-dayguard.csv   9d18dc2948f96a50403506a47c01f6b7b84ace6682bee7a139104723e0e313da
  data/raw/campd-partial-outages-units.csv             6c2541198016eb671845cc5b52baf530aa2efd7eab83ff81bfbb3aa7b87b0515
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot5_hourgrain_span --years 2024 --out-dir results/calibration/r_ercot6_arm_2024 --note "R-ERCOT-6 ARM 2024: keeper 2026-09-25-r-5-hour-grain recipe with ercot_dam_availability_event_cap_unit_scoped=true (ercot-174 unit-scoped window x partial composition, shared-unit mask at the window hour grain) — PRECOMMIT-r-ercot-6-unit-scoped-event-cap-2026-09-26" --set ercot_dam_availability_event_cap_unit_scoped=true 2>&1 | tee /tmp/r_ercot6_arm_2024.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot6_arm_2024/run_config.json after the solve:
  scenario_config: ercot_dam_availability_event_cap_unit_scoped = true; ercot_dam_availability_event_cap_reconciliation = false; ercot_dam_availability_coal_event_cap = true; ercot_dam_availability_gas_event_cap = true; unit_outage_window_hour_grain = true; ercot_partial_outage_day_guard = true; ercot_partial_outage_shaped_derate = true; measured_chp_heat_rates = false;
  ercot_offer_swcap_clip = false; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 4.576; offer_curve_by_group.CT_PEAKER.peak = 13.15;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  The resolved-input record in the same file (search for "campd_unit_outages") must show "path": "data/raw/campd-unit-outages-hourgrain.csv" with sha256 9f57063cc84f4017cd389d174863e5a7e0ff7d8d9dae6dd5ad06a04ca2e887a9.
  Also results/calibration/r_ercot6_arm_2024/hourly/system_2024.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot6_arm_2024/dispatch/2024_P1.parquet must exist.
  The solve log (/tmp/r_ercot6_arm_2024.log) must contain the line "ERCOT unit-scoped event-cap composition (2024)" with a NON-ZERO bin count; report that line verbatim.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot6_arm_2024/\n!results/calibration/r_ercot6_arm_2024/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot6_arm_2024
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot6_arm_2024/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-6 ARM 2024: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot6-arm-2024 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot6_arm_2024 | wc -l` > 0 and that it lists dispatch/2024_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2024.parquet rows with pass=='P1'); total P1 slack MWh; number of hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2024.parquet; the signature values and resolved-input path you read; anything unexpected.
```

## LEG arm-2025

```text
SHARD R-ERCOT-6 ARM 2025 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-6 (docs/handoffs/PRECOMMIT-r-ercot-6-unit-scoped-event-cap-2026-09-26.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot6-arm-2025`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report. A slow fetch is normal: WAIT for it in the foreground (long timeout / until-loop); never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv          6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv   837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages.csv                      b569de2a48d0b6e03b22272d1fb165e11b826b6c11b4dfd4f622e63f96d32812
  data/raw/campd-unit-outages-short.csv                d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv             2ac566acf5f9391566b35254690c37ec90c89fbe5f832b5544d90cd0605ebe37
  data/raw/campd-unit-outages-hourgrain.csv            9f57063cc84f4017cd389d174863e5a7e0ff7d8d9dae6dd5ad06a04ca2e887a9
  data/raw/campd-unit-outages-short-hourgrain.csv      11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv   6b592d028a856e3d0cfe536128ff3c1fef84a57b48c356a46d8af09afc9bd761
  data/raw/reference/custom-bin-assignments.csv        90223446c501d524ca4216ed284863ad4b4a82a7f8b40210065d9ca8a465e222
  data/raw/campd-partial-outages-shaped.csv            720cb71f75bd6fb42ee572d5677951361be03929f1781f44666b4b2e88fa9295
  data/raw/campd-partial-outages-shaped-dayguard.csv   9d18dc2948f96a50403506a47c01f6b7b84ace6682bee7a139104723e0e313da
  data/raw/campd-partial-outages-units.csv             6c2541198016eb671845cc5b52baf530aa2efd7eab83ff81bfbb3aa7b87b0515
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot5_hourgrain_span --years 2025 --out-dir results/calibration/r_ercot6_arm_2025 --note "R-ERCOT-6 ARM 2025: keeper 2026-09-25-r-5-hour-grain recipe with ercot_dam_availability_event_cap_unit_scoped=true (ercot-174 unit-scoped window x partial composition, shared-unit mask at the window hour grain) — PRECOMMIT-r-ercot-6-unit-scoped-event-cap-2026-09-26" --set ercot_dam_availability_event_cap_unit_scoped=true 2>&1 | tee /tmp/r_ercot6_arm_2025.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot6_arm_2025/run_config.json after the solve:
  scenario_config: ercot_dam_availability_event_cap_unit_scoped = true; ercot_dam_availability_event_cap_reconciliation = false; ercot_dam_availability_coal_event_cap = true; ercot_dam_availability_gas_event_cap = true; unit_outage_window_hour_grain = true; ercot_partial_outage_day_guard = true; ercot_partial_outage_shaped_derate = true; measured_chp_heat_rates = false;
  ercot_offer_swcap_clip = false; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 4.576; offer_curve_by_group.CT_PEAKER.peak = 13.15;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  The resolved-input record in the same file (search for "campd_unit_outages") must show "path": "data/raw/campd-unit-outages-hourgrain.csv" with sha256 9f57063cc84f4017cd389d174863e5a7e0ff7d8d9dae6dd5ad06a04ca2e887a9.
  Also results/calibration/r_ercot6_arm_2025/hourly/system_2025.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot6_arm_2025/dispatch/2025_P1.parquet must exist.
  The solve log (/tmp/r_ercot6_arm_2025.log) must contain the line "ERCOT unit-scoped event-cap composition (2025)" with a NON-ZERO bin count; report that line verbatim.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot6_arm_2025/\n!results/calibration/r_ercot6_arm_2025/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot6_arm_2025
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot6_arm_2025/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-6 ARM 2025: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot6-arm-2025 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot6_arm_2025 | wc -l` > 0 and that it lists dispatch/2025_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2025.parquet rows with pass=='P1'); total P1 slack MWh; number of hours whose max zonal P1 price exceeds $1,000; annual P1 TWh by class from hourly/class_hourly_2025.parquet; the signature values and resolved-input path you read; anything unexpected.
```
