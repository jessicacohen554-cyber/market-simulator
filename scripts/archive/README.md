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
  part of the calibration record. Nothing new should be *written* here
  directly either — a new one-off probe belongs in `scripts/probes/`, and a
  script that earns a standing role belongs at `scripts/` top level. The one
  sanctioned intake is **keeper rotation** (`scripts/README.md`): when an
  ISO's next keeper registers — or a probe's rejection is adjudicated — the
  superseded run's per-run attestation/driver/validate scripts rotate here,
  imports and repo-root path math mechanically fixed, content otherwise
  unchanged.
- **2026-08-15 backlog rotation (BLOAT-B-4).** 86 scripts arrived in one pass —
  79 `gen_*_attestation.py`, `gen_nyiso130_keeper_ledger.py`, the miso-72
  lineage, the miso-74/75 probe drivers, `run_foresight_ab.py` and
  `run_calibration_eia930.py`. Pure `git mv`: the only content edits are the
  repo-root path math re-anchored one level deeper
  (`Path(__file__).resolve().parents[1]` → `parents[2]`,
  `.parent.parent` → `.parent.parent.parent`; 86 expressions, each re-verified
  to resolve to the repo root at its new depth) and one sibling import in
  `gen_caiso160_attestation.py` re-pointed to `scripts.archive.…`. See
  `scripts/README.md` "Keeper rotation" for the keep-set derivation and
  `docs/bloat-removal-plan-2026-08.md` §6.
