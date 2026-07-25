# Archived — the `frontend/` Scenario Results Dashboard (pages + JS)

> Status: ARCHIVED 2026-07-25 (owner decision **D-7**,
> `docs/refactor-consolidation-plan-2026-07.md` §9). Historical record, not
> maintained. Nothing links these pages and the Pages deploy no longer serves
> them.

## What this is

The three-page static app that used to live at `frontend/index.html`,
`frontend/decisions.html` and `frontend/parameters.html` with its four scripts
under `frontend/js/`. It was the *forecast/scenario* results explorer: a
scenario picker + year slider driving four Plotly panels (generation mix,
emissions, price-duration, capacity), a `localStorage`-backed decision tracker,
and a searchable parameter-citation browser.

| File | Purpose |
|---|---|
| `index.html` | Scenario picker + year slider -> four Plotly panels |
| `decisions.html` | Build-plan §5 decision tracker (radio + notes, `localStorage`) |
| `parameters.html` | Citation browser over `frontend/data/parameters.json`; JS inline |
| `js/app.js` | `window.App` — in-memory state + nav-active detection |
| `js/data-loader.js` | `window.DataLoader` — scenario index + lazy per-scenario JSON |
| `js/charts.js` | `window.Charts` — the four Plotly renderers |
| `js/decisions.js` | Decision catalogue + render/persist for `decisions.html` |

## Why it was archived

It never had data. `index.html` renders from `frontend/data/scenarios.json` +
`frontend/data/results/*.json`, written by `scripts/export_results.py` — which
was never run and whose output was never committed, so the page has shipped
"No scenarios exported yet" for its whole life while the site's landing page
advertised it as one of four destinations. The 2026-06-19 frontend audit
(`docs/frontend-audit.md` §3) recorded it as a dormant feature and put the
keep-or-retire call to the owner; D-7 answered **archive**.

The live surfaces that replaced it in practice are the codebase-explorer pages
under `docs/codebase-site/` — the Run Explorer and Calibration Status for
backcast results, the Forecast Run Explorer and Program Status for the forecast
program.

## What did NOT move

- **`frontend/data/**` — untouched.** That is the live dashboard data path
  (`frontend/data/backcast/` is a CLAUDE.md rule-15 frozen surface with
  concurrent calibration sessions registering into it), plus the still-live
  `frontend/data/parameters.json` registry, which `scripts/generate_parameter_registry.py`
  writes and `scripts/validate_parameters.py` checks. D-7 archives pages and JS
  only.
- **`frontend/css/style.css` — untouched.** It is the live design system for the
  root `index.html` and `model-updates.html`, not part of this app.
- **`scripts/export_results.py` — untouched.** It still exports scenario JSON;
  reviving the app is a matter of running it, not rewriting it.

## Reviving it

The pages use paths relative to `frontend/` (`css/style.css`, `js/*.js`,
`data/*.json`), so they run unchanged from that directory:

```sh
git mv docs/archive/frontend-scenario-app/*.html frontend/
git mv docs/archive/frontend-scenario-app/js/*.js frontend/js/
python scripts/export_results.py          # populates data/scenarios.json + data/results/
# then restore the landing-page card in index.html and the nav link in model-updates.html
```

`docs/archive/` is outside the Pages deploy's sparse checkout
(`frontend`, `learning-hub`, `docs/codebase-site`, `scripts`), so while the app
sits here it is not staged into `_site` and cannot be served.
