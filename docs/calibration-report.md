# Calibration report — the output-format artifact

`scripts/render_calibration_html.py` renders the standard interactive
calibration report: a single self-contained HTML file (no external JS/CSS,
safe to send as a chat artifact or open offline). This is **the** deliverable
format for a calibration run — generate it, eyeball it, send it.

## Generate

```bash
# default: results/calibration/stgas_{2023,2024,2025}
python scripts/render_calibration_html.py

# explicit bundles + custom output path
python scripts/render_calibration_html.py \
    results/calibration/stgas_2023 results/calibration/stgas_2024 \
    --out /tmp/calibration-report.html
```

Output: `results/calibration/calibration-report.html` (default). Each bundle
is a persisted run directory containing `dispatch/<year>_P1.parquet`,
`campd.parquet`, `eia923.parquet`, `eia930.parquet`, `btm.parquet` and
`meta.json`. The report is a **post-processing step** — it never re-solves the
LP. If a bundle is missing, produce it with `run_calibration_full.py`
(`--persist-bundle`), or rebuild a benchmark in place with
`run_calibration_full.py --rebuild-benchmark DIR`.

## What's in it

Top toggle: **Charts** page and **Tables** page.

### Charts
Selectors: year (2023/2024/2025), group, and plant (aggregate or a single
plant). Groups: `COAL_LIGNITE`, `COAL_PRB`, `CC_REGULAR`, `CC_CHP`,
`CT_PEAKER`, `ST_GAS`.

- **Commitment heatmap** — 24h × 365d capacity-factor grids, CAMPD actual vs
  model result, on a shared 0–100% colour ramp. The hourly model and CAMPD
  series are embedded base64 `uint8` (CF 0–100), decoded client-side.
- **Dispatch comparison** — average hourly profile (CF% or MW) for the
  selected period (annual or a month), with the must-run-floor line and
  avg-actual / avg-model / bias / peak-hour / hourly-r-NRMSE stats.
- **Annual total** — bar chart, model vs CAMPD vs EIA-923 (TWh).
- **Monthly generation** — line chart, model vs CAMPD vs EIA-923 (GWh).

### Tables
Per-plant hourly r / NRMSE vs CAMPD net (after parasitic correction), plus the
per-year thermal-by-class (vs EIA-923) and fuel hourly-fit (vs EIA-930) tables.

## Conventions baked into the report (read before interpreting it)

These live **only** in the report generator — none of them touch the model /
LP dispatch or `config/scenarios.py`. They make the comparison fair; they do
not change any calibrated result.

- **Plant scope.** A plant is included only if it *both* contributes to the
  grid LP (`grid > 0`) *and* reports to CAMPD (`campd > 0`). No-CAMPD plants
  and full-BTM (host-steam-only, no grid contribution) plants are dropped
  everywhere — aggregate and per-plant.
- **CHP behind-the-meter add-back.** CHP host-steam must-run is removed from
  the grid LP (it's behind the meter), so the model shows only the economic
  export while CAMPD reports the whole plant. For CHP plants the report adds
  the must-run back flat (`nameplate × must-run%`) — but **only** in the
  hourly *shape* views: the heatmap, the dispatch profile, and the hourly
  r/NRMSE fit. The **annual and monthly total** charts stay grid-only (the
  true model output). Non-CHP must-run is already in the grid LP, so nothing
  is added there.
- **CAMPD net.** CAMPD gross is converted to net with the parasitic-load
  factors before any comparison; r/NRMSE are computed against that net.

## Skill

`/calibration-report` (`.claude/skills/calibration-report/SKILL.md`) runs the
generator on the default bundles and sends the HTML as a chat artifact.
