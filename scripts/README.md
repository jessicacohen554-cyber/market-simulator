# scripts/ — layout

Reorganized 2026-07-18 so the operational surface is separable from data
tooling and retired one-offs. References in code, tests, CI, and docs were
updated mechanically in the same change; paths quoted in frozen run records
(`results/calibration/`, `frontend/data/backcast/`) and in session logs that
predate the reorg refer to the old flat layout — the file content is unchanged,
only the directory moved.

| Location            | What lives there |
|---------------------|------------------|
| `scripts/` (top)    | Core entry points and standing tooling: calibration/backcast (`run_calibration_full.py`, `run_calibration.py`, `replay_keeper.py`), hindcast (`run_capacity_hindcast.py`, `register_hindcast.py`), the forecast program (`run_full_horizon.py`, `forecast_verdict.py`, `export_forecast_bands.py`, PB-5 assembly), scoring/verdicts (`calibration_verdict.py`, `score_*.py`, `legitimacy_diagnostics.py`), dashboard/site (`dashboard_add_run.py`, `build_manifest.py`, `build_status.py`, `render_*.py`), governance (`build_dof_ledger.py`, `regression_gate.py`, `capture_*_goldens.py`, `verify_holdout_intake.py`, `generate_parameter_registry.py`), and per-ISO gate reporters. |
| `scripts/data/`     | Data fetching and processing — everything between an external source and the model's inputs: `fetch_*` (raw downloads), `curate_*`/`process_*`/`convert_*`/`parse_*` (raw → `data/clean` per the schema contract), `derive_*` (measured-behaviour parameter derivation; CLAUDE.md rule 23 — frozen against residuals), and per-source builders (`build_*_hsl.py`, LMP references, AS withholding, …). Not core engine. |
| `scripts/archive/`  | Retired one-offs that are no longer part of the backcast, hindcast, or forecast paths: superseded per-run drivers (`run_pjm51`–`98`, `run_ercot_21`–`46`, `run_159`–`166`, …), per-run attestation generators, one-shot diagnostics/probes/analyses, completed intake/landing scripts, dead CI-upload tooling. Kept for the historical record; **not maintained**. See `scripts/archive/README.md`. |
| `scripts/lib/`      | Shared helpers imported by scripts (`clean_io.py`, `bundle_io.py`, per-datatype registries). |
| `scripts/probes/`   | Per-run probe scripts and repro artifacts, named `_<iso><run>_*` — the historical record of calibration probes. |
| `scripts/diagnostics/` | Scratch diagnostics. |

Classification rule used (and to use going forward): a script stays at top
level if it is part of a *standing* workflow — invoked by CI, a skill, tests,
the calibration/forecast/hindcast programs, or governance rules. A script tied
to one specific superseded run belongs in `archive/`; anything that fetches or
transforms data belongs in `data/`.
