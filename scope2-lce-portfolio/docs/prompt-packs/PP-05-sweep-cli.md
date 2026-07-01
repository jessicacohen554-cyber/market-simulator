# PP-05 — Sweep Driver & CLI

**Upstream:** ADR 0002. **Targets:** `src/lce_portfolio/sweep.py`,
`cli.py`, `__main__.py`.
**Status:** done (sequential sweep, CLI, console script).

## Build / deepen

1. **Sweep robustness.** Handle infeasible/failed setpoints gracefully (record
   status, continue). Optionally sweep both `low/mid/high` sensitivities in one
   call and label results.
2. **Multi-ISO batch.** A CLI mode that loops ISOs present in the intake, writing
   one output set per ISO (still one LP per (iso, setpoint); no cross-ISO coupling).
3. **Performance.** Solves are independent — the sweep may run them in parallel
   *processes* (each IPM solve is memory-bounded; cap concurrency). Keep a
   sequential default for reproducibility. **Do not** parallelize inside a single
   solve.
4. **Config-file entry.** Accept a `--config file.yaml` (with PP-00's loader) so
   runs are reproducible artifacts.

## Acceptance

`test_sweep` asserts the frontier is **non-decreasing in the premium cap** (more
budget ⇒ matching ≥) and that Mode B premiums are non-increasing in the target's
slack; CLI smoke test runs the sample end-to-end and writes both Parquet files.
