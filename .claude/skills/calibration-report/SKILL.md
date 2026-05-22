---
name: calibration-report
description: Generate/refresh the deployable backcast comparison dashboard (backcast-results.html + per-run JSON data) from persisted calibration bundles, commit it for GitHub Pages, and report the headline. Use when the user asks for "the calibration report", "the backcast report", "the dashboard", to add a new run to the dashboard, or wants to see/share calibration results visually.
---

# Backcast results dashboard

Generate and deploy the JSON-driven backcast comparison dashboard. The page is
a static shell (`backcast-results.html` at the repo root) that loads run data
from `frontend/data/backcast/` and is served by GitHub Pages, so a new run is
picked up automatically once its data file + manifest entry are written. Full
generator: `scripts/render_backcast.py` (data + shell) and
`scripts/_backcast_shell.py` (the UI). The standalone embedded report
(`scripts/render_calibration_html.py`) is retained only for one-off
self-contained sends; the dashboard is the standard format.

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
   `…/backcast-results.html`. Report the headline (per-class Class capture% and
   Plant capture% across runs, and any class off by >10% vs EIA-923).

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
