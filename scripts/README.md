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

## Bootstrap & shared CLI helpers

`market_sim` is always importable (editable install), but the `scripts`
package is only importable with the repo root on `sys.path`. Every
`scripts.*`-importing tool uses the same **canonical three-line bootstrap** at
the top of the file, before any `from scripts.…` import:

```python
import sys
from market_sim.config.paths import REPO_ROOT
sys.path.insert(0, str(REPO_ROOT))
```

after which `from scripts.lib.cli import add_iso_arg` (etc.) resolves
regardless of the script's depth or the process's working directory. Do **not**
hand-roll `Path(__file__).resolve().parents[N]` repo-root math or insert
`REPO / "scripts"` — the bootstrap above is depth-independent. `scripts.lib.cli`
also exposes `repo_root()` (a re-export of `config.paths.REPO_ROOT`) and the
canonical argparse builders `add_iso_arg` / `add_years_arg` (its help text
documents the rule-22 holdout gate) / `add_out_dir_arg` / `add_bundle_arg`;
`--iso` is constrained to `iso_configs.SUPPORTED_ISOS`, so a new ISO propagates
everywhere without touching a hardcoded tuple.

Exception: the stdlib-only dashboard-deploy trio (`build_manifest.py`,
`build_codebase_site_backcast.py`, `register_hindcast.py`) runs on a bare
`python3` with no installed deps and keeps its own stdlib bootstrap — it must
not import `scripts.lib.cli` (which imports `market_sim`).

## Dashboard retention (top-15 per ISO, all three stores)

The backcast dashboard keeps the **top 15 runs per ISO** (user-set 2026-06-21,
superseding the earlier 10-run rule). A registered run lives in **three stores**
that must stay in lockstep:

1. `frontend/data/backcast/registry/<id>.json` — the manifest sidecar.
2. `frontend/data/backcast/runs/<id>.js` — the run payload.
3. `results/calibration/<bundle>/` — the solved bundle (the sidecar's `bundle`
   field).

`scripts/dashboard_add_run.py` **governs all three**: after registering a run it
runs `prune_iso`, which keeps the 15 newest runs for that ISO (by date, then id)
and deletes the sidecar, payload **and** mapped bundle dir of every displaced
oldest run *together*. Two protections are never pruned regardless of age: any
current keeper in `keepers.json`, and any run referenced by a surviving
sidecar's `ablation_twin`/`ablation_of` link. Pass `--no-prune` to register
without sweeping (used by the one-time backfill/cleanup operations); the caller
stages the deletions with the rest of the commit.

`scripts/check_registry_payload_parity.py` is the CI gate for this invariant and
checks **both directions**: a sidecar with no payload (invisible in the Run
Explorer) *and* an **orphan payload** with no sidecar (a dead `runs/<id>.js`
left behind if a sidecar were ever pruned without its payload). Run it before
every dashboard push. Bundles no longer referenced by any sidecar are swept in
the owner-signed one-time bundle sweep, not by `prune_iso` (which only touches
the bundle of a run it is actively pruning).
