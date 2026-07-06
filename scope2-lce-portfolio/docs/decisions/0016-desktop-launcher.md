# 0016 — Desktop launcher: batch/shell twins → local HTML launch page → solve → report

- **Status:** accepted
- **Date:** 2026-07-02
- **Session:** PS-13 (planning-session doc removed at handoff cleanup; in git history)
- **Implemented by:** PP-10 / `launcher/`, `src/lce_portfolio/launcher.py`

## Context

The tool is feature-complete behind `python -m lce_portfolio`, but the target
user launches it by double-clicking a script, sets a handful of parameters,
and expects the HTML report to open when the solve finishes — with no
traceback ever surfacing raw. PS-13 (stakeholder, 2026-07-02) fixed the four
open packaging questions: platform coverage, parameter-capture interaction
model, the exposed parameter set, and the Python-environment assumption.

## Options considered

1. **Console prompts (`set /p`) writing a run-config JSON** — zero UI code;
   clunky for repeat runs and impossible to queue several runs at once.
2. **Editable params file the script reads** — no interaction code at all,
   but raw-JSON editing is a poor desktop experience.
3. **Local HTML launch page** — the launcher starts a stdlib-only localhost
   HTTP server and opens a browser page with all parameters shown at their
   defaults and toggleable, plus a side panel to queue multiple runs/views
   and save configurations; submit executes the queue and opens each report.
   Most code, best experience; needs a server because static HTML cannot
   execute solves.

## Decision

1. **Platforms:** ship **`launcher/run_lce.bat` and `launcher/run_lce.sh`
   twins** with identical behavior. CI exercises the `.sh`/Python path
   end-to-end; Windows-only lines are review-verified and the launcher README
   carries a "not CI-tested on Windows" note.
2. **Parameter capture:** the launcher scripts start
   `python -m lce_portfolio.launcher`, a **Python-stdlib-only local web
   server** (`http.server`, bound to `127.0.0.1` on an ephemeral port) and
   open the default browser on its **self-contained HTML launch page** (no
   CDN, no external fetch — same self-containment rule as the ADR 0014
   report; styled with the same design system). The page shows every exposed
   parameter pre-filled with its default and toggleable, and a **side panel
   that (a) queues multiple run configurations to execute in one submit and
   (b) saves/loads named configurations**. Saved configs and the last-used
   values persist server-side as JSON under `launcher/` (gitignored). Queued
   runs execute **sequentially** (one LP solve at a time); the page shows
   per-run status and links; each finished run's `results/<run_id>/report.html`
   opens automatically when "open report when done" is on.
3. **Exposed parameters (exactly):** `iso`, `mode`, premium deltas / matching
   targets, `lcoe_sensitivity`, load file path (default = bundled reference
   load), LMP file path (default = newest export, with synthetic provenance
   clearly flagged in the UI), `run-id`, open-report-when-done. All other
   knobs stay config-file-only (an advanced `--config` path may be passed to
   the underlying CLI but is not a launch-page field).
4. **Python environment:** the scripts try repo-relative **`../.venv`** first
   (from `scope2-lce-portfolio/`), then fall back to `python` on PATH gated
   by a **version (≥3.11) and import check** (`highspy`, `numpy`, `pandas`),
   failing with a clear actionable message otherwise. A `requirements.txt`
   ships with the tool. No auto-creation of venvs or pip installs inside the
   launcher.
5. **Error discipline:** the Python entry validates inputs and reports
   friendly, actionable errors (in the page and mirrored to the console);
   a raw traceback reaching the user is a bug. Browser-opening is gated
   behind a `--no-open` flag which tests (and CI) use.

## Consequences

- New module `src/lce_portfolio/launcher.py` (server + request validation +
  run execution via the existing `cli.py`/`sweep` path — reuse, don't fork)
  and `launcher/` (scripts, README, gitignored saved-config JSON).
- Stdlib-only server keeps ADR 0001 isolation intact: no new dependencies,
  no network beyond loopback.
- Tests: saved-config round-trip, request/parameter validation, and a
  launcher-invoked end-to-end run on the SAMPLE inputs via subprocess with
  `--no-open` (no browser in CI).
- Defers: packaging as a single-file executable (PyInstaller etc.),
  concurrent run execution, remote/network use of the launch page (loopback
  binding is deliberate and stays).
