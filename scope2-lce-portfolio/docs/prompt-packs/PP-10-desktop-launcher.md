# PP-10 — Desktop launcher

**Upstream:** ADR 0016 (`docs/decisions/0016-desktop-launcher.md`).
**Targets:** `launcher/run_lce.sh`, `launcher/run_lce.bat`, `launcher/README.md`,
`src/lce_portfolio/launcher.py`, `requirements.txt`, `tests/test_launcher.py`.
**Status:** complete (2026-07-02).

## Principle

The tool is feature-complete behind `python -m lce_portfolio`; PP-10 packages
it for a double-click user. `launcher.py` is a **Python-stdlib-only** local
HTTP server (`http.server`, loopback-bound, ephemeral port by default) that
serves a self-contained HTML launch page (inline CSS/JS, no CDN, no external
fetch) and executes queued runs **sequentially** through the existing
`cli.py`/`sweep` code path — no forked solve logic, no new dependency.

## Scope (ADR 0016, exactly)

1. Platform twins: `launcher/run_lce.sh` and `launcher/run_lce.bat`, identical
   behavior. CI exercises the `.sh`/Python path (`tests/test_launcher.py`);
   the `.bat` twin is review-verified only, flagged "not CI-tested on Windows"
   in `launcher/README.md`.
2. Launch page: every exposed parameter pre-filled with its default and
   toggleable; a side panel that (a) queues multiple run configurations for
   one submit and (b) saves/loads named configurations. Saved configs +
   last-used values persist as JSON under `launcher/` (gitignored). Queued
   runs execute one LP solve at a time; each finished run's
   `results/<run_id>/report.html` opens automatically when
   "open report when done" is on.
3. Exposed parameters, exactly: `iso`, `mode`, premium deltas / matching
   targets, `lcoe_sensitivity`, load file path (default = bundled reference
   load, generated on demand), LMP file path (default = newest export found
   on disk; a `_dummy` file is flagged **SYNTHETIC**), `run-id`,
   open-report-when-done. Everything else stays config-file-only.
4. Python resolution: `../.venv` (repo-relative) first, else `python3`/`python`
   on `PATH` gated by a version (>=3.11) **and** import (`highspy`, `numpy`,
   `pandas`) check, else a clear actionable exit. `requirements.txt` ships;
   no auto venv creation or `pip install` inside the launcher.
5. Error discipline: friendly, actionable errors in the page and mirrored to
   the console; a raw traceback reaching the user is a bug. Browser opening
   (initial page + per-run report) is gated behind `--no-open`, used by tests.

## Design notes

- `LauncherState` runs one daemon worker thread draining a `queue.Queue` of
  jobs, so concurrent HTTP submissions never overlap solves.
- Each queued run calls `lce_portfolio.cli.main(argv)` in-process (HiGHS
  logging is already silenced in `lp.py`); `cli.RESULTS_ROOT` is reassigned
  to the launcher's `--results` directory once at startup so the results
  store location is configurable without forking the CLI.
- `validate_run_payload` re-uses `PortfolioConfig.__post_init__` for
  range/type rules and `cli.validate_run_id` for run-id safety rather than
  duplicating either.
- The launcher never invokes the market-sim LMP exporter itself (unlike
  `examples/run_real_sweep.py`'s `generate_dummy_lmp`) — it only reports
  what's already on disk under `--inputs-dir`, so it can never trigger a
  market-sim solve (stakeholder hard hold).
- `/reports/<run_id>/(report.html|report.json)` is served directly from the
  results store (regex-constrained path, no traversal) so the launch page can
  link to a finished run's report without a `file://` URI.

## Acceptance

- `../.venv/bin/python -m pytest tests/ -q` green, including
  `tests/test_launcher.py`: saved-config round-trip, request/parameter
  validation (bad iso, bad mode, missing file → friendly error payloads, no
  traceback), and an end-to-end subprocess run (`--no-open`, scratch
  `--results`/`--state-dir`) against SAMPLE fixtures through to
  `results/<run_id>/report.html`.
- `./launcher/run_lce.sh --no-open --port <N>` serves the launch page at
  `http://127.0.0.1:<N>/`.
- `grep -rnE "^\s*(import market_sim|from market_sim)" src/ scripts/ tests/`
  empty (standalone isolation intact).
