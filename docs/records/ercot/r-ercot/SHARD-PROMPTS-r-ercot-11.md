# R-ERCOT-11 shard prompts (one per year)

Each shard's launch message names its YEAR and the PINNED SHA (the commit that carries this file). Wherever a prompt says `<PINNED_SHA>`, use the SHA from your launch message. Execute ONLY your own year's section.

## LEG arm-2019

```text
SHARD R-ERCOT-11 ARM 2019 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-11 (docs/records/ercot/PRECOMMIT-r-ercot-11-parish-split-2026-09-28.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot11-arm-2019`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report. A slow fetch is normal: WAIT for it in the foreground (long timeout / until-loop); never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv          6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv   837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages.csv                      be846bf880d4f05697acf7c87f5ba6c9bc884c87b480b6674731c495467d5cd4
  data/raw/campd-unit-outages-short.csv                d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv             679880f766187a949dbca28a87fd35c135f889a341fb761da165457138ddf8f1
  data/raw/campd-unit-outages-hourgrain.csv            40a4b2961a9589871d70684a8766c5a9a72c8be8553d70c52574fe467ac2ff74
  data/raw/campd-unit-outages-short-hourgrain.csv      11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv   43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv        ed9091397f4804fa4533218539bb6e449dd6231fbf7978a52a63a94dd2f2dc83
  data/raw/campd-partial-outages-shaped.csv            3f1b421d7337e971fc265f9103bc3377ebc0857fd4876fb58d4fbb356c89e40a
  data/raw/campd-partial-outages-shaped-dayguard.csv   3c384fc0c465b686f5b520334d335c3bfa0058c2c129e6416563af25fffe719c
  data/raw/campd-partial-outages-units.csv             b6145d5a3d01373356bde6138a6f4ea7d284346b613125a0ac63d167d92cd426
  data/raw/reference/ercot-dam-plant-crosswalk.csv     721b284b67b54e6c49790be5a0a3ca23b0d666ad73ef2239cafcf91c206051c6
  data/raw/reference/ercot-dam-gas-site-seeds.csv      0ff1948f98d6281edb1d41d8666fe885db96874f41d0836ff2282c1ecbd66a10
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv 633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot10_parish_span --years 2019 --out-dir results/calibration/r_ercot11_arm_2019 --note "R-ERCOT-11 ARM 2019: keeper 2026-09-27-r-10-parish-fuelscope recipe, UNCHANGED flags, on the R-ERCOT-11 input corrections (W A Parish split to EIA-860 nameplate: coal 3470 2736.8 MW / gas steam 34702 1255.3 MW; split-child rows 34702/49392 read their measured ST heat rate) — PRECOMMIT-r-ercot-11-parish-split-2026-09-28" 2>&1 | tee /tmp/r_ercot11_arm_2019.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot11_arm_2019/run_config.json after the solve:
  scenario_config: ercot_dam_availability_event_cap_unit_scoped = false; ercot_dam_availability_event_cap_reconciliation = false; ercot_dam_availability_coal_event_cap = true; ercot_dam_availability_gas_event_cap = true; unit_outage_window_hour_grain = true; ercot_partial_outage_day_guard = true; ercot_partial_outage_shaped_derate = true; measured_chp_heat_rates = false;
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  The resolved-input record in the same file (search for "campd_unit_outages") must show "path": "data/raw/campd-unit-outages-hourgrain.csv" with sha256 40a4b2961a9589871d70684a8766c5a9a72c8be8553d70c52574fe467ac2ff74.
  Also results/calibration/r_ercot11_arm_2019/hourly/system_2019.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot11_arm_2019/dispatch/2019_P1.parquet must exist.
  The solve log (/tmp/r_ercot11_arm_2019.log) must contain "Loaded 305 per-plant CAMPD bins" and must NOT contain "ERCOT unit-scoped event-cap composition" (305 = the keeper fleet incl. Jack Fusco). The "R-ERCOT year-matched bin heat rates" line for your year MUST read "sheet 0 MW" (the split-child heat-rate fix); if it shows a non-zero sheet MW, STOP. Report verbatim the "partial-outage derate" log line(s) for your year and the "R-ERCOT year-matched bin heat rates (2019)" line verbatim.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot11_arm_2019/\n!results/calibration/r_ercot11_arm_2019/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot11_arm_2019
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot11_arm_2019/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-11 ARM 2019: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot11-arm-2019 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot11_arm_2019 | wc -l` > 0 and that it lists dispatch/2019_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2019.parquet rows with pass=='P1'); total P1 slack MWh; number of hours whose max zonal P1 price exceeds $1,000; P1 TWh of plant 3470 (W A Parish coal), 34702 (W A Parish gas steam) and 49392 (Barney Davis steam) from dispatch/<YEAR>_P1.parquet (sum the rows whose plant_code column equals the code; if there is no plant_code column, use unit ids containing "3470_" / "34702_" / "49392_" and say which you used); annual P1 TWh by class from hourly/class_hourly_2019.parquet; the signature values and resolved-input path you read; anything unexpected.
```

## LEG arm-2020

```text
SHARD R-ERCOT-11 ARM 2020 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-11 (docs/records/ercot/PRECOMMIT-r-ercot-11-parish-split-2026-09-28.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot11-arm-2020`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report. A slow fetch is normal: WAIT for it in the foreground (long timeout / until-loop); never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv          6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv   837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages.csv                      be846bf880d4f05697acf7c87f5ba6c9bc884c87b480b6674731c495467d5cd4
  data/raw/campd-unit-outages-short.csv                d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv             679880f766187a949dbca28a87fd35c135f889a341fb761da165457138ddf8f1
  data/raw/campd-unit-outages-hourgrain.csv            40a4b2961a9589871d70684a8766c5a9a72c8be8553d70c52574fe467ac2ff74
  data/raw/campd-unit-outages-short-hourgrain.csv      11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv   43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv        ed9091397f4804fa4533218539bb6e449dd6231fbf7978a52a63a94dd2f2dc83
  data/raw/campd-partial-outages-shaped.csv            3f1b421d7337e971fc265f9103bc3377ebc0857fd4876fb58d4fbb356c89e40a
  data/raw/campd-partial-outages-shaped-dayguard.csv   3c384fc0c465b686f5b520334d335c3bfa0058c2c129e6416563af25fffe719c
  data/raw/campd-partial-outages-units.csv             b6145d5a3d01373356bde6138a6f4ea7d284346b613125a0ac63d167d92cd426
  data/raw/reference/ercot-dam-plant-crosswalk.csv     721b284b67b54e6c49790be5a0a3ca23b0d666ad73ef2239cafcf91c206051c6
  data/raw/reference/ercot-dam-gas-site-seeds.csv      0ff1948f98d6281edb1d41d8666fe885db96874f41d0836ff2282c1ecbd66a10
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv 633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot10_parish_span --years 2020 --out-dir results/calibration/r_ercot11_arm_2020 --note "R-ERCOT-11 ARM 2020: keeper 2026-09-27-r-10-parish-fuelscope recipe, UNCHANGED flags, on the R-ERCOT-11 input corrections (W A Parish split to EIA-860 nameplate: coal 3470 2736.8 MW / gas steam 34702 1255.3 MW; split-child rows 34702/49392 read their measured ST heat rate) — PRECOMMIT-r-ercot-11-parish-split-2026-09-28" 2>&1 | tee /tmp/r_ercot11_arm_2020.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot11_arm_2020/run_config.json after the solve:
  scenario_config: ercot_dam_availability_event_cap_unit_scoped = false; ercot_dam_availability_event_cap_reconciliation = false; ercot_dam_availability_coal_event_cap = true; ercot_dam_availability_gas_event_cap = true; unit_outage_window_hour_grain = true; ercot_partial_outage_day_guard = true; ercot_partial_outage_shaped_derate = true; measured_chp_heat_rates = false;
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  The resolved-input record in the same file (search for "campd_unit_outages") must show "path": "data/raw/campd-unit-outages-hourgrain.csv" with sha256 40a4b2961a9589871d70684a8766c5a9a72c8be8553d70c52574fe467ac2ff74.
  Also results/calibration/r_ercot11_arm_2020/hourly/system_2020.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot11_arm_2020/dispatch/2020_P1.parquet must exist.
  The solve log (/tmp/r_ercot11_arm_2020.log) must contain "Loaded 305 per-plant CAMPD bins" and must NOT contain "ERCOT unit-scoped event-cap composition" (305 = the keeper fleet incl. Jack Fusco). The "R-ERCOT year-matched bin heat rates" line for your year MUST read "sheet 0 MW" (the split-child heat-rate fix); if it shows a non-zero sheet MW, STOP. Report verbatim the "partial-outage derate" log line(s) for your year and the "R-ERCOT year-matched bin heat rates (2020)" line verbatim.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot11_arm_2020/\n!results/calibration/r_ercot11_arm_2020/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot11_arm_2020
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot11_arm_2020/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-11 ARM 2020: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot11-arm-2020 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot11_arm_2020 | wc -l` > 0 and that it lists dispatch/2020_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2020.parquet rows with pass=='P1'); total P1 slack MWh; number of hours whose max zonal P1 price exceeds $1,000; P1 TWh of plant 3470 (W A Parish coal), 34702 (W A Parish gas steam) and 49392 (Barney Davis steam) from dispatch/<YEAR>_P1.parquet (sum the rows whose plant_code column equals the code; if there is no plant_code column, use unit ids containing "3470_" / "34702_" / "49392_" and say which you used); annual P1 TWh by class from hourly/class_hourly_2020.parquet; the signature values and resolved-input path you read; anything unexpected.
```

## LEG arm-2021

```text
SHARD R-ERCOT-11 ARM 2021 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-11 (docs/records/ercot/PRECOMMIT-r-ercot-11-parish-split-2026-09-28.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot11-arm-2021`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report. A slow fetch is normal: WAIT for it in the foreground (long timeout / until-loop); never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv          6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv   837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages.csv                      be846bf880d4f05697acf7c87f5ba6c9bc884c87b480b6674731c495467d5cd4
  data/raw/campd-unit-outages-short.csv                d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv             679880f766187a949dbca28a87fd35c135f889a341fb761da165457138ddf8f1
  data/raw/campd-unit-outages-hourgrain.csv            40a4b2961a9589871d70684a8766c5a9a72c8be8553d70c52574fe467ac2ff74
  data/raw/campd-unit-outages-short-hourgrain.csv      11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv   43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv        ed9091397f4804fa4533218539bb6e449dd6231fbf7978a52a63a94dd2f2dc83
  data/raw/campd-partial-outages-shaped.csv            3f1b421d7337e971fc265f9103bc3377ebc0857fd4876fb58d4fbb356c89e40a
  data/raw/campd-partial-outages-shaped-dayguard.csv   3c384fc0c465b686f5b520334d335c3bfa0058c2c129e6416563af25fffe719c
  data/raw/campd-partial-outages-units.csv             b6145d5a3d01373356bde6138a6f4ea7d284346b613125a0ac63d167d92cd426
  data/raw/reference/ercot-dam-plant-crosswalk.csv     721b284b67b54e6c49790be5a0a3ca23b0d666ad73ef2239cafcf91c206051c6
  data/raw/reference/ercot-dam-gas-site-seeds.csv      0ff1948f98d6281edb1d41d8666fe885db96874f41d0836ff2282c1ecbd66a10
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv 633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot10_parish_span --years 2021 --out-dir results/calibration/r_ercot11_arm_2021 --note "R-ERCOT-11 ARM 2021: keeper 2026-09-27-r-10-parish-fuelscope recipe, UNCHANGED flags, on the R-ERCOT-11 input corrections (W A Parish split to EIA-860 nameplate: coal 3470 2736.8 MW / gas steam 34702 1255.3 MW; split-child rows 34702/49392 read their measured ST heat rate) — PRECOMMIT-r-ercot-11-parish-split-2026-09-28" 2>&1 | tee /tmp/r_ercot11_arm_2021.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot11_arm_2021/run_config.json after the solve:
  scenario_config: ercot_dam_availability_event_cap_unit_scoped = false; ercot_dam_availability_event_cap_reconciliation = false; ercot_dam_availability_coal_event_cap = true; ercot_dam_availability_gas_event_cap = true; unit_outage_window_hour_grain = true; ercot_partial_outage_day_guard = true; ercot_partial_outage_shaped_derate = true; measured_chp_heat_rates = false;
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  The resolved-input record in the same file (search for "campd_unit_outages") must show "path": "data/raw/campd-unit-outages-hourgrain.csv" with sha256 40a4b2961a9589871d70684a8766c5a9a72c8be8553d70c52574fe467ac2ff74.
  Also results/calibration/r_ercot11_arm_2021/hourly/system_2021.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot11_arm_2021/dispatch/2021_P1.parquet must exist.
  The solve log (/tmp/r_ercot11_arm_2021.log) must contain "Loaded 305 per-plant CAMPD bins" and must NOT contain "ERCOT unit-scoped event-cap composition" (305 = the keeper fleet incl. Jack Fusco). The "R-ERCOT year-matched bin heat rates" line for your year MUST read "sheet 0 MW" (the split-child heat-rate fix); if it shows a non-zero sheet MW, STOP. Report verbatim the "partial-outage derate" log line(s) for your year and the "R-ERCOT year-matched bin heat rates (2021)" line verbatim.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot11_arm_2021/\n!results/calibration/r_ercot11_arm_2021/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot11_arm_2021
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot11_arm_2021/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-11 ARM 2021: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot11-arm-2021 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot11_arm_2021 | wc -l` > 0 and that it lists dispatch/2021_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2021.parquet rows with pass=='P1'); total P1 slack MWh; number of hours whose max zonal P1 price exceeds $1,000; P1 TWh of plant 3470 (W A Parish coal), 34702 (W A Parish gas steam) and 49392 (Barney Davis steam) from dispatch/<YEAR>_P1.parquet (sum the rows whose plant_code column equals the code; if there is no plant_code column, use unit ids containing "3470_" / "34702_" / "49392_" and say which you used); annual P1 TWh by class from hourly/class_hourly_2021.parquet; the signature values and resolved-input path you read; anything unexpected.
```

## LEG arm-2022

```text
SHARD R-ERCOT-11 ARM 2022 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-11 (docs/records/ercot/PRECOMMIT-r-ercot-11-parish-split-2026-09-28.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot11-arm-2022`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report. A slow fetch is normal: WAIT for it in the foreground (long timeout / until-loop); never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv          6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv   837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages.csv                      be846bf880d4f05697acf7c87f5ba6c9bc884c87b480b6674731c495467d5cd4
  data/raw/campd-unit-outages-short.csv                d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv             679880f766187a949dbca28a87fd35c135f889a341fb761da165457138ddf8f1
  data/raw/campd-unit-outages-hourgrain.csv            40a4b2961a9589871d70684a8766c5a9a72c8be8553d70c52574fe467ac2ff74
  data/raw/campd-unit-outages-short-hourgrain.csv      11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv   43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv        ed9091397f4804fa4533218539bb6e449dd6231fbf7978a52a63a94dd2f2dc83
  data/raw/campd-partial-outages-shaped.csv            3f1b421d7337e971fc265f9103bc3377ebc0857fd4876fb58d4fbb356c89e40a
  data/raw/campd-partial-outages-shaped-dayguard.csv   3c384fc0c465b686f5b520334d335c3bfa0058c2c129e6416563af25fffe719c
  data/raw/campd-partial-outages-units.csv             b6145d5a3d01373356bde6138a6f4ea7d284346b613125a0ac63d167d92cd426
  data/raw/reference/ercot-dam-plant-crosswalk.csv     721b284b67b54e6c49790be5a0a3ca23b0d666ad73ef2239cafcf91c206051c6
  data/raw/reference/ercot-dam-gas-site-seeds.csv      0ff1948f98d6281edb1d41d8666fe885db96874f41d0836ff2282c1ecbd66a10
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv 633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot10_parish_span --years 2022 --out-dir results/calibration/r_ercot11_arm_2022 --note "R-ERCOT-11 ARM 2022: keeper 2026-09-27-r-10-parish-fuelscope recipe, UNCHANGED flags, on the R-ERCOT-11 input corrections (W A Parish split to EIA-860 nameplate: coal 3470 2736.8 MW / gas steam 34702 1255.3 MW; split-child rows 34702/49392 read their measured ST heat rate) — PRECOMMIT-r-ercot-11-parish-split-2026-09-28" 2>&1 | tee /tmp/r_ercot11_arm_2022.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot11_arm_2022/run_config.json after the solve:
  scenario_config: ercot_dam_availability_event_cap_unit_scoped = false; ercot_dam_availability_event_cap_reconciliation = false; ercot_dam_availability_coal_event_cap = true; ercot_dam_availability_gas_event_cap = true; unit_outage_window_hour_grain = true; ercot_partial_outage_day_guard = true; ercot_partial_outage_shaped_derate = true; measured_chp_heat_rates = false;
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  The resolved-input record in the same file (search for "campd_unit_outages") must show "path": "data/raw/campd-unit-outages-hourgrain.csv" with sha256 40a4b2961a9589871d70684a8766c5a9a72c8be8553d70c52574fe467ac2ff74.
  Also results/calibration/r_ercot11_arm_2022/hourly/system_2022.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot11_arm_2022/dispatch/2022_P1.parquet must exist.
  The solve log (/tmp/r_ercot11_arm_2022.log) must contain "Loaded 305 per-plant CAMPD bins" and must NOT contain "ERCOT unit-scoped event-cap composition" (305 = the keeper fleet incl. Jack Fusco). The "R-ERCOT year-matched bin heat rates" line for your year MUST read "sheet 0 MW" (the split-child heat-rate fix); if it shows a non-zero sheet MW, STOP. Report verbatim the "partial-outage derate" log line(s) for your year and the "R-ERCOT year-matched bin heat rates (2022)" line verbatim.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot11_arm_2022/\n!results/calibration/r_ercot11_arm_2022/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot11_arm_2022
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot11_arm_2022/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-11 ARM 2022: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot11-arm-2022 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot11_arm_2022 | wc -l` > 0 and that it lists dispatch/2022_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2022.parquet rows with pass=='P1'); total P1 slack MWh; number of hours whose max zonal P1 price exceeds $1,000; P1 TWh of plant 3470 (W A Parish coal), 34702 (W A Parish gas steam) and 49392 (Barney Davis steam) from dispatch/<YEAR>_P1.parquet (sum the rows whose plant_code column equals the code; if there is no plant_code column, use unit ids containing "3470_" / "34702_" / "49392_" and say which you used); annual P1 TWh by class from hourly/class_hourly_2022.parquet; the signature values and resolved-input path you read; anything unexpected.
```

## LEG arm-2023

```text
SHARD R-ERCOT-11 ARM 2023 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-11 (docs/records/ercot/PRECOMMIT-r-ercot-11-parish-split-2026-09-28.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot11-arm-2023`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report. A slow fetch is normal: WAIT for it in the foreground (long timeout / until-loop); never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv          6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv   837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages.csv                      be846bf880d4f05697acf7c87f5ba6c9bc884c87b480b6674731c495467d5cd4
  data/raw/campd-unit-outages-short.csv                d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv             679880f766187a949dbca28a87fd35c135f889a341fb761da165457138ddf8f1
  data/raw/campd-unit-outages-hourgrain.csv            40a4b2961a9589871d70684a8766c5a9a72c8be8553d70c52574fe467ac2ff74
  data/raw/campd-unit-outages-short-hourgrain.csv      11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv   43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv        ed9091397f4804fa4533218539bb6e449dd6231fbf7978a52a63a94dd2f2dc83
  data/raw/campd-partial-outages-shaped.csv            3f1b421d7337e971fc265f9103bc3377ebc0857fd4876fb58d4fbb356c89e40a
  data/raw/campd-partial-outages-shaped-dayguard.csv   3c384fc0c465b686f5b520334d335c3bfa0058c2c129e6416563af25fffe719c
  data/raw/campd-partial-outages-units.csv             b6145d5a3d01373356bde6138a6f4ea7d284346b613125a0ac63d167d92cd426
  data/raw/reference/ercot-dam-plant-crosswalk.csv     721b284b67b54e6c49790be5a0a3ca23b0d666ad73ef2239cafcf91c206051c6
  data/raw/reference/ercot-dam-gas-site-seeds.csv      0ff1948f98d6281edb1d41d8666fe885db96874f41d0836ff2282c1ecbd66a10
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv 633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot10_parish_span --years 2023 --out-dir results/calibration/r_ercot11_arm_2023 --note "R-ERCOT-11 ARM 2023: keeper 2026-09-27-r-10-parish-fuelscope recipe, UNCHANGED flags, on the R-ERCOT-11 input corrections (W A Parish split to EIA-860 nameplate: coal 3470 2736.8 MW / gas steam 34702 1255.3 MW; split-child rows 34702/49392 read their measured ST heat rate) — PRECOMMIT-r-ercot-11-parish-split-2026-09-28" 2>&1 | tee /tmp/r_ercot11_arm_2023.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot11_arm_2023/run_config.json after the solve:
  scenario_config: ercot_dam_availability_event_cap_unit_scoped = false; ercot_dam_availability_event_cap_reconciliation = false; ercot_dam_availability_coal_event_cap = true; ercot_dam_availability_gas_event_cap = true; unit_outage_window_hour_grain = true; ercot_partial_outage_day_guard = true; ercot_partial_outage_shaped_derate = true; measured_chp_heat_rates = false;
  ercot_offer_swcap_clip = true; ercot_zonal_spread_ep_referenced = false; offer_curve_by_group.CC_REGULAR.peak = 151.008; offer_curve_by_group.CT_PEAKER.peak = 433.95;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  The resolved-input record in the same file (search for "campd_unit_outages") must show "path": "data/raw/campd-unit-outages-hourgrain.csv" with sha256 40a4b2961a9589871d70684a8766c5a9a72c8be8553d70c52574fe467ac2ff74.
  Also results/calibration/r_ercot11_arm_2023/hourly/system_2023.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot11_arm_2023/dispatch/2023_P1.parquet must exist.
  The solve log (/tmp/r_ercot11_arm_2023.log) must contain "Loaded 305 per-plant CAMPD bins" and must NOT contain "ERCOT unit-scoped event-cap composition" (305 = the keeper fleet incl. Jack Fusco). The "R-ERCOT year-matched bin heat rates" line for your year MUST read "sheet 0 MW" (the split-child heat-rate fix); if it shows a non-zero sheet MW, STOP. Report verbatim the "partial-outage derate" log line(s) for your year and the "R-ERCOT year-matched bin heat rates (2023)" line verbatim.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot11_arm_2023/\n!results/calibration/r_ercot11_arm_2023/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot11_arm_2023
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot11_arm_2023/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-11 ARM 2023: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot11-arm-2023 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot11_arm_2023 | wc -l` > 0 and that it lists dispatch/2023_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2023.parquet rows with pass=='P1'); total P1 slack MWh; number of hours whose max zonal P1 price exceeds $1,000; P1 TWh of plant 3470 (W A Parish coal), 34702 (W A Parish gas steam) and 49392 (Barney Davis steam) from dispatch/<YEAR>_P1.parquet (sum the rows whose plant_code column equals the code; if there is no plant_code column, use unit ids containing "3470_" / "34702_" / "49392_" and say which you used); annual P1 TWh by class from hourly/class_hourly_2023.parquet; the signature values and resolved-input path you read; anything unexpected.
```

## LEG arm-2024

```text
SHARD R-ERCOT-11 ARM 2024 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-11 (docs/records/ercot/PRECOMMIT-r-ercot-11-parish-split-2026-09-28.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot11-arm-2024`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report. A slow fetch is normal: WAIT for it in the foreground (long timeout / until-loop); never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv          6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv   837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages.csv                      be846bf880d4f05697acf7c87f5ba6c9bc884c87b480b6674731c495467d5cd4
  data/raw/campd-unit-outages-short.csv                d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv             679880f766187a949dbca28a87fd35c135f889a341fb761da165457138ddf8f1
  data/raw/campd-unit-outages-hourgrain.csv            40a4b2961a9589871d70684a8766c5a9a72c8be8553d70c52574fe467ac2ff74
  data/raw/campd-unit-outages-short-hourgrain.csv      11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv   43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv        ed9091397f4804fa4533218539bb6e449dd6231fbf7978a52a63a94dd2f2dc83
  data/raw/campd-partial-outages-shaped.csv            3f1b421d7337e971fc265f9103bc3377ebc0857fd4876fb58d4fbb356c89e40a
  data/raw/campd-partial-outages-shaped-dayguard.csv   3c384fc0c465b686f5b520334d335c3bfa0058c2c129e6416563af25fffe719c
  data/raw/campd-partial-outages-units.csv             b6145d5a3d01373356bde6138a6f4ea7d284346b613125a0ac63d167d92cd426
  data/raw/reference/ercot-dam-plant-crosswalk.csv     721b284b67b54e6c49790be5a0a3ca23b0d666ad73ef2239cafcf91c206051c6
  data/raw/reference/ercot-dam-gas-site-seeds.csv      0ff1948f98d6281edb1d41d8666fe885db96874f41d0836ff2282c1ecbd66a10
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv 633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot10_parish_span --years 2024 --out-dir results/calibration/r_ercot11_arm_2024 --note "R-ERCOT-11 ARM 2024: keeper 2026-09-27-r-10-parish-fuelscope recipe, UNCHANGED flags, on the R-ERCOT-11 input corrections (W A Parish split to EIA-860 nameplate: coal 3470 2736.8 MW / gas steam 34702 1255.3 MW; split-child rows 34702/49392 read their measured ST heat rate) — PRECOMMIT-r-ercot-11-parish-split-2026-09-28" 2>&1 | tee /tmp/r_ercot11_arm_2024.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot11_arm_2024/run_config.json after the solve:
  scenario_config: ercot_dam_availability_event_cap_unit_scoped = false; ercot_dam_availability_event_cap_reconciliation = false; ercot_dam_availability_coal_event_cap = true; ercot_dam_availability_gas_event_cap = true; unit_outage_window_hour_grain = true; ercot_partial_outage_day_guard = true; ercot_partial_outage_shaped_derate = true; measured_chp_heat_rates = false;
  ercot_offer_swcap_clip = false; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 4.576; offer_curve_by_group.CT_PEAKER.peak = 13.15;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  The resolved-input record in the same file (search for "campd_unit_outages") must show "path": "data/raw/campd-unit-outages-hourgrain.csv" with sha256 40a4b2961a9589871d70684a8766c5a9a72c8be8553d70c52574fe467ac2ff74.
  Also results/calibration/r_ercot11_arm_2024/hourly/system_2024.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot11_arm_2024/dispatch/2024_P1.parquet must exist.
  The solve log (/tmp/r_ercot11_arm_2024.log) must contain "Loaded 305 per-plant CAMPD bins" and must NOT contain "ERCOT unit-scoped event-cap composition" (305 = the keeper fleet incl. Jack Fusco). The "R-ERCOT year-matched bin heat rates" line for your year MUST read "sheet 0 MW" (the split-child heat-rate fix); if it shows a non-zero sheet MW, STOP. Report verbatim the "partial-outage derate" log line(s) for your year and the "R-ERCOT year-matched bin heat rates (2024)" line verbatim.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot11_arm_2024/\n!results/calibration/r_ercot11_arm_2024/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot11_arm_2024
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot11_arm_2024/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-11 ARM 2024: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot11-arm-2024 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot11_arm_2024 | wc -l` > 0 and that it lists dispatch/2024_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2024.parquet rows with pass=='P1'); total P1 slack MWh; number of hours whose max zonal P1 price exceeds $1,000; P1 TWh of plant 3470 (W A Parish coal), 34702 (W A Parish gas steam) and 49392 (Barney Davis steam) from dispatch/<YEAR>_P1.parquet (sum the rows whose plant_code column equals the code; if there is no plant_code column, use unit ids containing "3470_" / "34702_" / "49392_" and say which you used); annual P1 TWh by class from hourly/class_hourly_2024.parquet; the signature values and resolved-input path you read; anything unexpected.
```

## LEG arm-2025

```text
SHARD R-ERCOT-11 ARM 2025 — ONE ERCOT BACKCAST YEAR, ONE SOLVE. You are a SHARD of parent session R-ERCOT-11 (docs/records/ercot/PRECOMMIT-r-ercot-11-parish-split-2026-09-28.md). CLAUDE.md is binding.
DATA PROFILE: ercot
MODEL: Opus/Fable. BUDGET: ~25 min of LP. If you reach 40 min with no bundle, STOP and report.

HARD STOP 1 — PINNED SHA: `git rev-parse HEAD` must equal <PINNED_SHA>. If not, `git fetch origin <PINNED_SHA> && git checkout <PINNED_SHA>` (detached is fine), then `git checkout -b claude/r-ercot11-arm-2025`. NEVER rebase, NEVER git pull, NEVER merge, NEVER "sync" to main. If you cannot reach <PINNED_SHA>, STOP and report. A slow fetch is normal: WAIT for it in the foreground (long timeout / until-loop); never end your turn while a fetch or the solve is running.

SETUP (only this): `python3 scripts/hydrate_data.py --profile ercot` (no-op on a full clone), then `uv sync --no-dev && uv pip install tzdata` (tzdata is a known missing runtime dep).

HARD STOP 2 — INPUT sha256 (`sha256sum`) must read exactly:
  data/raw/ercot-thermal-dam-availability.csv          6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638
  data/raw/ercot-thermal-dam-availability-hourly.csv   837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b
  data/raw/ercot-thermal-dam-availability-site-hourly.parquet bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0
  data/raw/campd-unit-outages.csv                      be846bf880d4f05697acf7c87f5ba6c9bc884c87b480b6674731c495467d5cd4
  data/raw/campd-unit-outages-short.csv                d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef
  data/raw/campd-unit-outages-shortgas.csv             679880f766187a949dbca28a87fd35c135f889a341fb761da165457138ddf8f1
  data/raw/campd-unit-outages-hourgrain.csv            40a4b2961a9589871d70684a8766c5a9a72c8be8553d70c52574fe467ac2ff74
  data/raw/campd-unit-outages-short-hourgrain.csv      11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f
  data/raw/campd-unit-outages-shortgas-hourgrain.csv   43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431
  data/raw/reference/custom-bin-assignments.csv        ed9091397f4804fa4533218539bb6e449dd6231fbf7978a52a63a94dd2f2dc83
  data/raw/campd-partial-outages-shaped.csv            3f1b421d7337e971fc265f9103bc3377ebc0857fd4876fb58d4fbb356c89e40a
  data/raw/campd-partial-outages-shaped-dayguard.csv   3c384fc0c465b686f5b520334d335c3bfa0058c2c129e6416563af25fffe719c
  data/raw/campd-partial-outages-units.csv             b6145d5a3d01373356bde6138a6f4ea7d284346b613125a0ac63d167d92cd426
  data/raw/reference/ercot-dam-plant-crosswalk.csv     721b284b67b54e6c49790be5a0a3ca23b0d666ad73ef2239cafcf91c206051c6
  data/raw/reference/ercot-dam-gas-site-seeds.csv      0ff1948f98d6281edb1d41d8666fe885db96874f41d0836ff2282c1ecbd66a10
  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919
  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv 633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c
Any mismatch: STOP, push nothing, report.

THE SOLVE — run exactly this from the repo root, unmodified (one year only):
PYTHONPATH=.:src:scripts uv run python scripts/replay_keeper.py results/calibration/r_ercot10_parish_span --years 2025 --out-dir results/calibration/r_ercot11_arm_2025 --note "R-ERCOT-11 ARM 2025: keeper 2026-09-27-r-10-parish-fuelscope recipe, UNCHANGED flags, on the R-ERCOT-11 input corrections (W A Parish split to EIA-860 nameplate: coal 3470 2736.8 MW / gas steam 34702 1255.3 MW; split-child rows 34702/49392 read their measured ST heat rate) — PRECOMMIT-r-ercot-11-parish-split-2026-09-28" 2>&1 | tee /tmp/r_ercot11_arm_2025.log

Run the solve in the FOREGROUND of one Bash call with a long timeout, or background it and WAIT on it with an until-loop — NEVER end your turn while the solve is running.
Never pass --no-container-preflight. Do not set MARKET_SIM_WARMSTART_XYEAR or MARKET_SIM_P1_BASIS_SEED (replay_keeper pins them off; rule 36).

HARD STOP 3 — CONFIG SIGNATURE, read from results/calibration/r_ercot11_arm_2025/run_config.json after the solve:
  scenario_config: ercot_dam_availability_event_cap_unit_scoped = false; ercot_dam_availability_event_cap_reconciliation = false; ercot_dam_availability_coal_event_cap = true; ercot_dam_availability_gas_event_cap = true; unit_outage_window_hour_grain = true; ercot_partial_outage_day_guard = true; ercot_partial_outage_shaped_derate = true; measured_chp_heat_rates = false;
  ercot_offer_swcap_clip = false; ercot_zonal_spread_ep_referenced = true; offer_curve_by_group.CC_REGULAR.peak = 4.576; offer_curve_by_group.CT_PEAKER.peak = 13.15;
  eia860_vintage_tracks_solve_year, measured_ct_heat_rates, measured_coal_heat_rates, measured_st_heat_rates, measured_cc_heat_rates, unit_outage_short_windows, unit_outage_short_windows_gas ALL = true.
  The resolved-input record in the same file (search for "campd_unit_outages") must show "path": "data/raw/campd-unit-outages-hourgrain.csv" with sha256 40a4b2961a9589871d70684a8766c5a9a72c8be8553d70c52574fe467ac2ff74.
  Also results/calibration/r_ercot11_arm_2025/hourly/system_2025.parquet must exist with a marginal_emission_rate column, and results/calibration/r_ercot11_arm_2025/dispatch/2025_P1.parquet must exist.
  The solve log (/tmp/r_ercot11_arm_2025.log) must contain "Loaded 305 per-plant CAMPD bins" and must NOT contain "ERCOT unit-scoped event-cap composition" (305 = the keeper fleet incl. Jack Fusco). The "R-ERCOT year-matched bin heat rates" line for your year MUST read "sheet 0 MW" (the split-child heat-rate fix); if it shows a non-zero sheet MW, STOP. Report verbatim the "partial-outage derate" log line(s) for your year and the "R-ERCOT year-matched bin heat rates (2025)" line verbatim.
If any of this is wrong: STOP, do NOT push the bundle, report exactly what you saw.

PUSH THE FULL BUNDLE (rule 34(a)) — exactly these commands; NO `git add -f`, NO `git add -A`, NO `git add .`:
  printf '\n!results/calibration/r_ercot11_arm_2025/\n!results/calibration/r_ercot11_arm_2025/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/r_ercot11_arm_2025
  git status --short    # staged paths MUST be only .gitignore and results/calibration/r_ercot11_arm_2025/ — otherwise `git restore --staged` the extras and report
  git commit (message "R-ERCOT-11 ARM 2025: shard bundle", with the Co-Authored-By trailer)
  push to origin claude/r-ercot11-arm-2025 with -u (on HTTP 408/500: `git config http.version HTTP/1.1` and retry; network errors retry up to 4x with backoff)
Then verify `git ls-tree -r HEAD -- results/calibration/r_ercot11_arm_2025 | wc -l` > 0 and that it lists dispatch/2025_P1.parquet.

FORBIDDEN, by name: git add -A / git add . / git add -f; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, calibration_verdict registration, or anything under frontend/data/backcast/**; ANY edit under src/ or scripts/ (including replay_keeper.py); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.
A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.

FINAL MESSAGE — REPORT IN NUMBERS: the SHA you solved at; the pushed commit's FULL 40-char SHA and branch; the ls-tree file count; the `container preflight:` and `memory peak:` log lines verbatim; solve wall-clock; P1 load-weighted mean price over all zones (sum(price*demand)/sum(demand) over hourly/system_2025.parquet rows with pass=='P1'); total P1 slack MWh; number of hours whose max zonal P1 price exceeds $1,000; P1 TWh of plant 3470 (W A Parish coal), 34702 (W A Parish gas steam) and 49392 (Barney Davis steam) from dispatch/<YEAR>_P1.parquet (sum the rows whose plant_code column equals the code; if there is no plant_code column, use unit ids containing "3470_" / "34702_" / "49392_" and say which you used); annual P1 TWh by class from hourly/class_hourly_2025.parquet; the signature values and resolved-input path you read; anything unexpected.
```
