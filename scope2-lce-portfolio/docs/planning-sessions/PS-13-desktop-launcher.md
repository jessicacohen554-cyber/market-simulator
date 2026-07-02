# PS-13 — Desktop Launcher (batch file → parameters → solve → report)
**DECIDED → [ADR 0016](../decisions/0016-desktop-launcher.md) (2026-07-02)**

**Goal:** decide the shape of the small desktop utility that wraps the tool —
how it is started, how run parameters are captured, which parameters are
exposed, and what Python environment it may assume — so PP-10 can build it
without open questions.

## Why it matters

The tool is feature-complete behind a CLI (`python -m lce_portfolio`), but the
intended day-to-day user starts from a double-clickable script, not a terminal
invocation with eight flags. The launcher is the last packaging step; its
decisions (platform coverage, interaction model, environment bootstrapping)
determine how much of it CI can actually exercise and how failures surface to
a non-developer.

## Questions decided (stakeholder, 2026-07-02)

1. **Platforms.** Windows `.bat` only, or `.bat` + POSIX `.sh` twins?
   → **Both**, kept behaviorally identical. The `.sh` twin is what CI can run
   end-to-end; the `.bat` gets extra-careful review and a "not CI-tested on
   Windows" note in the launcher README.
2. **Parameter capture.** Console prompts vs an editable params file vs a UI?
   → **A local HTML launch page** (stakeholder-directed option): the launcher
   opens a browser page showing every exposed parameter pre-filled with its
   default and toggleable, with a **side panel that queues multiple runs /
   views and saves configurations** for reuse. Submitting executes the queued
   run(s) and opens each finished report. Because a static HTML file cannot
   execute solves, this implies a **stdlib-only localhost HTTP server**
   (127.0.0.1, ephemeral port) started by the batch/shell script — no new
   dependencies, no external fetches (consistent with ADR 0014
   self-containment and ADR 0001 isolation).
3. **Exposed parameters.** → **The standard list**: `iso`, `mode`, premium
   deltas / matching targets, `lcoe_sensitivity`, load file path (default =
   bundled reference load), LMP file path (default = newest export, synthetic
   clearly flagged), `run-id`, open-report-when-done. Everything else remains
   a config-file knob.
4. **Python environment.** → **Repo-relative `../.venv` first, PATH fallback**
   with a version (3.11+) and import check (`highspy`, `numpy`, `pandas`) and
   a clear actionable error when neither works; ship a `requirements.txt`
   either way. No auto-bootstrap/pip-install inside the launcher.

## Outcome

ADR 0016 records the decisions; PP-10 builds `launcher/` (run_lce.bat,
run_lce.sh, README), `src/lce_portfolio/launcher.py` (server + validation +
friendly errors + browser open), and tests (saved-config round-trip, request
validation, launcher-driven end-to-end on the SAMPLE inputs via subprocess
with browser-open suppressed).
