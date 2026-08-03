# FFR-3A-2 — consolidated T1 battery close (lane record)

This directory is the `--out-dir` root for the FFR-3A-2 battery: the T1-F re-runs
that the FFR-3D `run_config.json` repair (`34c2f25`) made scorable, the four T1-H
curve legs the C.4(c) un-pin (`36ef1a1`) re-opened, the T1-X crossover fold, and
the FC-6 driver battery.

**Everything under here except this README is gitignored** (`.gitignore`, the
`/results/ffr3a2/` rule) — same class as `results/ffr3a/` and `results/ffr3c/`.
Forecast-family legs are registered to `frontend/data/forecast/` via
`scripts/register_forecast_run.py`, never as tracked bundles here (CLAUDE.md
rule 15). The committed record is the sidecar under `frontend/data/hindcast/`
plus the readout in `docs/handoffs/ffr-3a2-battery-close-2026-08-03.md`.

Layout (FFR-3C blocker 10 — read this before looking for a ledger):

    results/ffr3a2/<tier>/<leg>/<ISO>/<cache_key>/evolution_<year>.json

The evolution ledgers live under `<out-dir>/<ISO>/<cache_key>/`, **not** the
out-dir root, and `load_ledgers_for_run` returns `{}` rather than raising, so a
wrong path reads as "no evolution happened" instead of failing loudly.
