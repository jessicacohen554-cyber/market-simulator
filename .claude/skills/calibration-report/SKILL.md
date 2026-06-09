---
name: calibration-report
description: Generate/refresh the deployable backcast results dashboard (backcast-results.html + per-run JSON data) from persisted calibration bundles, commit it for GitHub Pages, and report the headline. Use when the user asks for "the calibration report", "the backcast report", "the dashboard", to add a new run to the dashboard, or wants to see/share calibration results visually.
---

# Backcast results dashboard

Generate and deploy the JSON-driven backcast results dashboard. The page is
a static shell (`backcast-results.html` at the repo root) that loads run data
from `frontend/data/backcast/` and is served by GitHub Pages, so a new run is
picked up automatically once its data file + manifest entry are written. Full
generator: `scripts/render_backcast.py` (data + shell) and
`scripts/_backcast_shell.py` (the UI). The standalone embedded report
(`scripts/render_calibration_html.py`) is retained only for one-off
self-contained sends; the dashboard is the standard format.

The shell shows **one run at a time** (the old multi-run comparison mode was
retired) in three views: **Run report** (default — per-year scorecard, class-
tolerance and dispatch-correlation heatmaps across all testing years, monthly
LMP vs actuals, and auto-generated diagnostics that localize each miss by
season/zone/plant), **Charts** (per-year deep-dive incl. commitment heatmaps
and the month/zone volume-miss bars), and **Tables** (generation mix and
reference tables). The diagnostics are computed client-side from the run
payload, so they appear automatically for every newly pushed bundle.

## Registry-driven regeneration (CI)

The dashboard run set is now tracked by per-run **registry sidecars** at
`frontend/data/backcast/registry/<id>.json` (`{id, label, bundle, iso}`). The
GitHub Actions pipeline (`.github/workflows/calibration-run.yml`) drops a sidecar
per run; `scripts/regen_dashboard.py` then rebuilds the shared manifest/benchmark/
html deterministically from **all** sidecars (so concurrent runs never drop each
other). To refresh the whole dashboard from the registered set, prefer:

```bash
python scripts/regen_dashboard.py
```

Add a run to the registry (writes its sidecar + `runs/<id>.js`, no shared-file
edit) with `scripts/dashboard_add_run.py --label "<name>" --bundle <dir>`. The
manual `render_backcast.py` flow below still works for one-off/ad-hoc sets.

## Run set

Each run is one calibration bundle in `results/calibration/<dir>/`. The
dashboard shows the **recent meaningful runs**; add new ones as they are
produced. The current set (label = bundle dir):

```
committed baseline = results/calibration/task1_committed_pct
new tranche +PT    = results/calibration/newtranche_passthru
new tranche noPT   = results/calibration/newtranche_nopassthru
tranchefix run1    = results/calibration/tranchefix_run1
tranchefix run2 sigmoid = results/calibration/tranchefix_run2_sigmoid
```

Run id = `<bundle date>-<shorthand>`; shorthand + the 1-3 sentence definition
are auto-derived from each bundle's `run_config.json` model-changes note. Edit
`frontend/data/backcast/manifest.js` afterward to refine a label/definition.

### PJM run naming convention

From 2026-06 onward, label **PJM** runs sequentially as `pjm 1 <keyword>`,
`pjm 2 <keyword>`, ... — a running integer plus a brief keyword descriptor of
what changed (e.g. `pjm 1 gas-basis`, `pjm 2 ct-hurdle`). The next number is one
more than the highest existing `pjm N ...` label in the registry. ERCOT keeps
its `runNN` scheme.

## Steps

1. **Confirm the bundles exist** (each needs `dispatch/<year>_P1.parquet`,
   `campd.parquet`, `eia923.parquet`, `eia930.parquet`, `meta.json`):
   ```bash
   ls -d results/calibration/{task1_committed_pct,newtranche_passthru,newtranche_nopassthru,tranchefix_run1,tranchefix_run2_sigmoid}
   ```
   Missing benchmark parquets can be rebuilt in place
   (`run_calibration_full.py --rebuild-benchmark DIR`) — never re-solve the LP
   just to make the report.

2. **Generate** (reads parquets only; no LP solve). Pass every run as
   `LABEL=BUNDLE`; to add a run, append it to the list:
   ```bash
   python scripts/render_backcast.py \
     "committed baseline=results/calibration/task1_committed_pct" \
     "new tranche PT=results/calibration/newtranche_passthru" \
     "new tranche noPT=results/calibration/newtranche_nopassthru" \
     "tranchefix run1=results/calibration/tranchefix_run1" \
     "tranchefix run2 sigmoid=results/calibration/tranchefix_run2_sigmoid"
   ```
   Writes `backcast-results.html` (repo root) and
   `frontend/data/backcast/{manifest.js,benchmark.js,runs/<id>.js}`.

3. **Sanity-check the shell** (the JS is non-trivial — verify it parses and
   renders headless before deploying):
   ```bash
   python -c "import re;open('/tmp/s.js','w').write(re.findall(r'<script>([\s\S]*?)</script>',open('backcast-results.html').read())[-1])"
   node --check /tmp/s.js && echo SYNTAX_OK
   ```

4. **Deploy**: commit `backcast-results.html` + `frontend/data/backcast/` and
   push. The page is then live on the repo's GitHub Pages site at
   `…/backcast-results.html`. Report the headline as the run scorecard shows
   it: classes in tolerance per year, system volume error, fleet dispatch r,
   LMP Δ vs actual, and the worst-offending classes (with the dashboard's
   diagnostics pointer for each, e.g. "summer-concentrated, peak tranche").

## Notes

- The dashboard fetches data via `<script src>` + `DecompressionStream`, which
  works on GitHub Pages **and** when opened locally — but needs a current
  browser. Opening `backcast-results.html` by double-click works because data
  is loaded by script tag (not `fetch`), so there is no `file://` CORS trap.
- This is a **reporting** tool: it never edits the model or `config/`. The two
  capture metrics and the CHP behind-the-meter add-back live in the generator;
  don't second-guess them here.
- To change scope (years, ISO, plant filter), adjust the bundles passed, not
  the generated HTML/JSON.
