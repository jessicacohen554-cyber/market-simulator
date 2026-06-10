---
name: calibration-report
description: Register new backcast calibration runs on the deployable results dashboard (registry sidecar + per-run JSON data), commit them conflict-free for GitHub Pages, and report the headline. Use when the user asks for "the calibration report", "the backcast report", "the dashboard", to add a new run to the dashboard, or wants to see/share calibration results visually.
---

# Backcast results dashboard

Register calibration runs on the JSON-driven backcast results dashboard. The
page is a static shell (`backcast-results.html`) that loads run data from
`frontend/data/backcast/` and is served by GitHub Pages. Full generator:
`scripts/render_backcast.py` (data + shell) and `scripts/_backcast_shell.py`
(the UI). The standalone embedded report (`scripts/render_calibration_html.py`)
is retained only for one-off self-contained sends; the dashboard is the
standard format.

The shell shows **one run at a time** (the old multi-run comparison mode was
retired) in three views: **Run report** (default — per-year scorecard, class-
tolerance and dispatch-correlation heatmaps across all testing years, monthly
LMP vs actuals, and auto-generated diagnostics that localize each miss by
season/zone/plant), **Charts** (per-year deep-dive incl. commitment heatmaps
and the month/zone volume-miss bars), and **Tables** (generation mix and
reference tables). The diagnostics are computed client-side from the run
payload, so they appear automatically for every newly pushed bundle.

## How publishing works (conflict-free by construction)

The shared dashboard files — `backcast-results.html`,
`frontend/data/backcast/manifest.js`, `benchmark.js` — are **generated and
gitignored. NEVER commit them** (git won't let you). They are assembled from
the committed per-run files by the stdlib-only `scripts/build_manifest.py`:
locally for preview, and by the "Deploy site to GitHub Pages" workflow at
deploy time (the only workflow; it runs in under a minute on every merge to
main).

Each run commits ONLY files in its own namespace, so any number of parallel
sessions — same ISO or different ISOs — merge to main without conflicts or
rebasing:

* `results/calibration/<name>/` — the bundle.
* `frontend/data/backcast/registry/<id>.json` — the sidecar holding the run's
  complete manifest entry (id, label, date, shorthand, definition, years, iso,
  file, bundle). **To refine a run's label or definition, edit its sidecar**
  (not manifest.js) and merge; the next deploy picks it up.
* `frontend/data/backcast/runs/<id>.js` — the run's payload.
* `frontend/data/backcast/bench/<ISO>/<year>.json.gz` — per-(ISO, year)
  benchmark parts. Byte-deterministic: they only show up in `git status` when
  the benchmark genuinely changed (new ISO/year, taxonomy change), which is
  rare. Commit them when they do.

## Run naming

Run id = `<bundle date>-<shorthand>`; shorthand + the 1-3 sentence definition
are auto-derived from each bundle's `run_config.json` model-changes note.

From 2026-06 onward, label **PJM** runs sequentially as `pjm 1 <keyword>`,
`pjm 2 <keyword>`, ... — a running integer plus a brief keyword descriptor of
what changed (e.g. `pjm 1 gas-basis`, `pjm 2 ct-hurdle`). The next number is
one more than the highest existing `pjm N ...` label in the registry. ERCOT
keeps its `runNN` scheme.

## Steps

1. **Confirm the bundle exists** (needs `dispatch/<year>_P1.parquet`,
   `campd.parquet`, `eia923.parquet`, `eia930.parquet`, `meta.json`).
   Missing benchmark parquets can be rebuilt in place
   (`run_calibration_full.py --rebuild-benchmark DIR`) — never re-solve the LP
   just to make the report.

2. **Register the run** (reads parquets only; no LP solve):
   ```bash
   python scripts/dashboard_add_run.py --label "run73 ct-hurdle" \
       --bundle results/calibration/Run-73
   ```
   Writes the sidecar + `runs/<id>.js` + the bench parts for its ISO/years,
   and refreshes the local (gitignored) preview. Prints `RUN_ID=<id>`.

3. **Preview locally** (assembles the full dashboard from ALL registered runs,
   instant, no bundle access):
   ```bash
   python scripts/build_manifest.py
   ```
   Then sanity-check the shell parses (the JS is non-trivial):
   ```bash
   python -c "import re;open('/tmp/s.js','w').write(re.findall(r'<script>([\s\S]*?)</script>',open('backcast-results.html').read())[-1])"
   node --check /tmp/s.js && echo SYNTAX_OK
   ```

4. **Commit + push** the per-run files only:
   ```bash
   git add results/calibration/<name> \
           frontend/data/backcast/registry/<id>.json \
           frontend/data/backcast/runs/<id>.js \
           frontend/data/backcast/bench
   git commit -m "results: <label> — <one-line what changed>"
   ```
   Merging to main auto-deploys (single Pages workflow, <1 min). Report the
   headline as the run scorecard shows it: classes in tolerance per year,
   system volume error, fleet dispatch r, LMP Δ vs actual, and the worst-
   offending classes (with the dashboard's diagnostics pointer for each, e.g.
   "summer-concentrated, peak tranche").

After bulk changes (deleting/relabelling bundles, payload schema changes), do
a full rebuild with `python scripts/regen_dashboard.py` (re-renders every
registered run from its bundle) and commit any changed `runs/*.js`, sidecars
and bench parts.

## Notes

- The dashboard fetches data via `<script src>` + `DecompressionStream`, which
  works on GitHub Pages **and** when opened locally — but needs a current
  browser. Opening `backcast-results.html` by double-click works because data
  is loaded by script tag (not `fetch`), so there is no `file://` CORS trap.
  (Locally, run `python scripts/build_manifest.py` first if the gitignored
  shell/manifest/benchmark aren't present in your checkout yet.)
- Avoid editing shared, append-style files (e.g. `docs/calibration-log.md`)
  from parallel sessions — that is the one remaining way two sessions can
  conflict. Put per-run findings in the run's sidecar definition or a
  `SUMMARY-*.md` inside the bundle dir, and update the shared log in one
  place afterwards.
- This is a **reporting** tool: it never edits the model or `config/`. The two
  capture metrics and the CHP behind-the-meter add-back live in the generator;
  don't second-guess them here.
- To change scope (years, ISO, plant filter), adjust the bundles passed, not
  the generated HTML/JSON.
