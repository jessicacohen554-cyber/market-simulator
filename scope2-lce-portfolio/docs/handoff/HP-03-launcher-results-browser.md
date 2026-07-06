# HP-03 — Launcher: past-runs browser, run log, template & annual-average integration

**Model:** Sonnet · **Depends on:** HP-01 · **Unblocks:** HP-04
**Targets:** `src/lce_portfolio/launcher.py`, `launcher/README.md`,
`.gitignore`, `tests/test_launcher.py`

Paste the block below into a fresh Claude Code session on
`jessicacohen554-cyber/market-simulator`.

```text
You are finalizing the standalone Scope 2 LCE portfolio tool in
scope2-lce-portfolio/ (repo jessicacohen554-cyber/market-simulator). Develop
on a fresh branch off latest origin/main named scope2/hp-03-launcher-browser
(or your session's designated branch); push there; open NO pull request.
Precondition: HP-01 (annual-average LMP intake, lmp_kind provenance) is
merged — verify it's present before starting; stop and report if not.

GOAL
Upgrade the existing desktop launcher (ADR 0016, src/lce_portfolio/launcher.py:
stdlib-only local HTTP server + self-contained HTML page) with three
user-facing capabilities, WITHOUT weakening its hardened posture:
(A) a past-runs browser, (B) a persistent run log, (C) first-class input
selection: bundled/available files and the annual-average LMP mode.

CONTEXT (read first)
- src/lce_portfolio/launcher.py end to end (server, form, queue, /reports/
  route, path-safety regexes, MAX_REQUEST_BYTES, loopback binding)
- launcher/README.md and docs/decisions/0016-desktop-launcher.md
- PLAN.md §8 note on the PP-13 adversarial review (11 hardening findings —
  the fixes live in the current code; treat them as a regression contract)
- tests/test_launcher.py (existing end-to-end style: real server on an
  ephemeral port, no browser)
- data/templates/README.md (input contracts incl. annual-average mode).

REQUIREMENTS
A. Past-runs browser. A section (or /runs page) listing every results/<run_id>/
   directory that contains a run_metadata.json: run id, ISO, mode, setpoints,
   lmp_kind, timestamp, solve status, with a link to its cached report.html
   through the existing /reports/ route (extend that route's strict regex
   pattern — never relax it). Sort newest first. Malformed/partial run dirs
   render as a flagged row, never a traceback.
B. Run log. Append one JSON line per finished run (id, params, status,
   wall-time, error summary on failure) to launcher/run_log.jsonl —
   machine-local state like saved_configs.json, so gitignore it. Surface the
   last N entries in the UI. Queue behavior stays sequential and unchanged.
C. Input selection. The load-file and LMP-file fields gain a server-side
   dropdown of candidate files: data/inputs/*, data/bundled/lmp/* (if HP-02
   has landed — degrade gracefully if the dir is absent), data/templates/*
   and the reference load; free-text path entry stays. Annual-average LMP
   files (detected by schema or by the user picking one) get a visible
   FLAT-PRICE badge exactly like the existing SYNTHETIC badge idiom, and the
   queued-run confirmation restates it. Add a small "Templates" help link
   block pointing at data/templates/ file paths with one-line schema
   summaries (served as text from disk paths — do not inline-copy the CSVs).

SECURITY / POSTURE REGRESSION CONTRACT (all must still hold)
- Server binds 127.0.0.1 only; request bodies capped at MAX_REQUEST_BYTES;
  run ids and every new path segment validated against the existing safe-name
  regexes; the /reports/ (and any new) route must be non-escapable
  (reject .., absolute paths, symlink tricks — test it).
- Directory listings for the dropdowns expose ONLY the whitelisted
  directories above, never arbitrary filesystem browsing.
- Errors reach the browser as short friendly messages, full detail to the
  terminal only. Page stays fully self-contained (inline CSS/JS, no CDN, no
  external fonts) and on the existing design tokens.

TESTS (extend tests/test_launcher.py in its existing style)
- Runs list renders committed sample results (SAMPLE_premium_cap_*) with a
  working report link; malformed run dir shows flagged row.
- run_log.jsonl gains exactly one well-formed line per completed run.
- Dropdown endpoint returns only whitelisted files; a crafted ../ or
  absolute-path run id / report path is rejected (404/400, no traceback).
- Annual-average file selection shows the FLAT-PRICE badge and the queued
  run completes end-to-end on a tiny synthetic annual-average file.

VERIFY before commit (from scope2-lce-portfolio/):
  python -m pytest tests/ -q
  grep -rn "import market_sim" src/ || echo OK-standalone
  launcher smoke: python -m lce_portfolio.launcher --no-open --port 0 (start,
  fetch /, stop) — the test suite should already cover this.
Update launcher/README.md for the three new capabilities. Small imperative
commits, rebase on origin/main, git push; on a single 413 switch to
mcp__github__push_files. No PRs, no raw model IDs in commits/code. Finish by
summarizing changes + verify output.
```
