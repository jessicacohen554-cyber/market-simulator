# PP-13 — Desktop-Launcher Adversarial Review (2026-07-02)

Not a build pack: the record of the focused post-merge review of the PP-10
desktop launcher (ADR 0016). PP-10 was built by a parallel session and merged
(PR #1261) *after* the PP-12 fresh-eyes audit, so `launcher.py`, the
`run_lce.sh`/`run_lce.bat` twins, and `tests/test_launcher.py` had never been
through a bug hunt. Same protocol as PP-12: audit against the governing
contract (ADR 0016 / PS-13), construct failing inputs against a live server
(not just read code), fix each confirmed defect with a regression test in the
same commit citing the finding ID.

## Scope / method

- Contract audit of `launcher.py` + scripts against ADR 0016 §1–§5.
- Live adversarial probes on the loopback server: malformed / hostile /
  oversized / concurrent request bodies, hand-rolled Content-Length headers,
  path-traversal attempts on `/reports/` and run ids, duplicate-id batches,
  non-finite numeric fields, run-time solve failures.
- Line-by-line review of the Windows-only `run_lce.bat` (cannot execute here;
  ADR 0016 §1 review-verified path — README carries the
  "not CI-tested on Windows" note).
- Self-containment grep of the emitted launch page (ADR 0016 §2, same rule as
  the ADR 0014 report): no `http(s)://`, `@import`, `<link>`, or non-`data:`
  `src=` — clean, now pinned by a regression test.

## Confirmed → fixed (each in its own commit with a regression test)

| ID | Severity | Defect | Fix |
|---|---|---|---|
| LN-1 | high | a JSON-array body or non-object entry in `runs` crashed the handler: raw `AttributeError` traceback + dropped connection (browser saw nothing) | type guards in `_read_json` / `validate_run_payload` → friendly 400 |
| LN-2 | high | `Content-Length` trusted blindly: non-integer → uncaught `ValueError` traceback; negative → handler hung in `rfile.read(-1)`; oversized → unbounded memory read | parse/validate the header, cap at `MAX_REQUEST_BYTES` (1 MiB) → 400 |
| LN-3 | medium | duplicate run ids within one submitted batch: blank-id runs of the same ISO/mode compose identical second-stamped ids, and `results/<run-id>/` is overwritten on re-use — the later run silently destroyed the earlier run's results mid-batch | `dedupe_run_ids`: auto ids get `-2`/`-3` suffixes; explicit duplicates → 400 before anything enqueues |
| LN-4 | medium | `nan` premium deltas passed validation (`d <= 0` is False for nan) and reached the LP; empty setpoint lists failed late with a misleading message | `parse_float_list` requires ≥1 finite value |
| LN-11 | medium | `contextlib.redirect_stderr` is process-wide, so handler threads logging requests mid-solve wrote into the run's captured stderr — HTTP access-log lines came back glued onto the friendly error message (observed live) | access log writes through the pre-redirect console handle |
| LN-5 | medium | `--host` flag could bind the un-authenticated server to `0.0.0.0`, contradicting ADR 0016's deliberate loopback-only stance | flag removed; server always binds `127.0.0.1` |
| LN-6 | low | status-table cells assembled via `innerHTML` template literals; the error detail echoes solver stderr, which can carry text from user-supplied input files → markup/script injection; page `fetch` failures were silent unhandled rejections | DOM-built cells via `textContent`; fetch calls wrapped with a friendly banner |
| LN-7 | low | last-used values merged into page defaults once at server start (reload never showed the latest submit); stale run-id pre-fill would overwrite that run on resubmit; SYNTHETIC flag didn't track the pre-filled LMP path | per-page-load merge; run id never pre-filled; flag recomputed from the shown path |
| LN-8 | low | client disconnect mid-response dumped a `BrokenPipeError` threading traceback to the console | `_send_bytes` catches it → one log line |
| LN-9 | hardening | run worker caught only `Exception`; a `SystemExit` (e.g. argparse `parser.error`) would kill the single worker thread silently, wedging every later queued run at "queued" — not reachable via the argv the launcher composes today, but one code change away | worker absorbs `SystemExit` into the friendly error status |
| LN-10 | test gap | ADR 0016 §1 promises the `.sh` path is CI-exercised, but tests only invoked `python -m lce_portfolio.launcher` directly — the script's `../.venv`-first resolution + import gate + `PYTHONPATH` wiring were untested | new test runs the actual `run_lce.sh` and fetches the served page |

## Probed and refuted / verified-correct

- **Run-id → rmtree traversal**: reuses `cli.validate_run_id` (the PP-12
  IO-1/CL-2 fix); `../escape` and friends → clean 400. Safe.
- **`/reports/` path traversal**: strict single-segment regex, and
  `urlparse` does not percent-decode — `../`, `%2e%2e`, `//etc/passwd`
  all 404. Safe.
- **Binding**: defaults verified live as `127.0.0.1` (ephemeral port);
  LN-5 removed the only non-loopback escape hatch.
- **Solve-failure surfacing**: a run-time failure (e.g. malformed load file
  that passes the existence check) comes back as `state: error` with the
  CLI's single friendly line — no 500, no traceback (message purity fixed
  under LN-11). Unexpected exceptions are caught in the worker: traceback
  to console, short message to the page.
- **Sequential execution**: one daemon worker drains the queue regardless of
  how many tabs/batches submit — LP solves never overlap (ADR 0016 §2).
- **CLI reuse**: runs execute through `cli.main` argv in-process
  (`build_argv`), results root via the `cli.RESULTS_ROOT` module attribute
  (read at call time) — no forked solve logic.
- **Stakeholder hard hold**: `resolve_default_lmp` only reports files already
  on disk (never invokes the exporter); `ensure_reference_load` is pure
  numpy/pandas. No market-sim solve is reachable from the launcher; the
  SYNTHETIC flag stays visible (and now tracks the pre-filled path).
- **Saved-config store**: name whitelist blocks path escapes (probed);
  params embed into the page via `</`-escaped JSON and are applied through
  form `.value` assignment only.
- **`run_lce.bat` line-by-line**: `%~dp0`/`%%~fI` root resolution, delayed
  expansion around `PYTHON_OK`/`ERRORLEVEL`, quoted path handling, the
  `where`-loop PATH fallback, and caret-escaped echos are all correct; the
  Microsoft-Store `python3.exe` stub fails the version/import gate and falls
  through to `python.exe` as intended. Behaviorally in lockstep with the
  `.sh` twin. Remains review-verified only (README notes it).

## Outcome

11 findings fixed (2 high, 4 medium, 3 low, 1 hardening, 1 test gap) in 8
commits on `claude/scope2-lce-final-build-jwce7w`; `tests/test_launcher.py`
grew from 13 to 31 tests (220 → 238 total). All three verification
commands green after every commit.
