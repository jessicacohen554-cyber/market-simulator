# scripts/archive/ — retired one-off scripts

Moved here 2026-07-18 from the flat `scripts/` directory. Everything in this
directory is a **historical artifact**: one-off run drivers for calibration
runs long since superseded by newer keepers, per-run attestation generators,
one-shot diagnostics/analyses, completed holdout-intake and doc-landing
scripts, and dead CI-upload tooling from before the runner-minutes policy.

- **Not maintained.** These scripts are not part of the backcast, hindcast, or
  forecast paths and are not covered by tests. They may assume data files,
  config fields, or module APIs that have since changed.
- Intra-repo imports were mechanically rewritten at the move
  (`scripts.X` → `scripts.archive.X` / `scripts.data.X`) so files remain
  importable, but no functional re-verification was done — treat any run of an
  archived script as an experiment.
- Registered run bundles and dashboard sidecars record the **pre-move paths**;
  those records are frozen and intentionally not rewritten. `git log --follow`
  connects the history.
- Nothing here should be deleted casually: per CLAUDE.md, probe/run scripts are
  part of the calibration record. But nothing new should be added either — a
  new one-off probe belongs in `scripts/probes/`, and a script that earns a
  standing role belongs at `scripts/` top level.
