---
name: calibration-report
description: Generate the interactive HTML calibration report (CAMPD-vs-model heatmaps, dispatch profiles, annual/monthly charts, per-plant r/NRMSE) from persisted calibration bundles and send it as a chat artifact. Use when the user asks for "the calibration report", "the HTML report", "the dashboard", or wants to see/share calibration results visually.
---

# Calibration report

Render and deliver the standard interactive calibration report. Full format
spec: `docs/calibration-report.md`.

## Steps

1. **Pick bundles.** Default to `results/calibration/stgas_{2023,2024,2025}`.
   If the user names specific bundle dirs or years, use those instead. Each
   bundle must contain `dispatch/<year>_P1.parquet`, `campd.parquet`,
   `eia923.parquet`, `eia930.parquet`, `btm.parquet`, `meta.json`.

2. **Check the bundles exist** before generating:
   ```bash
   ls -d results/calibration/stgas_2023 results/calibration/stgas_2024 results/calibration/stgas_2025
   ```
   If one is missing, tell the user and offer to produce it
   (`run_calibration_full.py --persist-bundle ...`) or rebuild its benchmark
   in place (`run_calibration_full.py --rebuild-benchmark DIR`). Do **not**
   re-solve the LP just to make the report — it's a post-processing step.

3. **Generate** (this only reads parquets; no LP solve):
   ```bash
   python scripts/render_calibration_html.py
   # or with explicit bundles / output:
   # python scripts/render_calibration_html.py BUNDLE [BUNDLE ...] --out FILE
   ```
   Output: `results/calibration/calibration-report.html`.

4. **Send it** with `SendUserFile` (the HTML is self-contained). Caption with
   the headline so the user sees it without opening: the per-group hourly
   r/NRMSE and any group whose annual total is off by more than ~10%.

## Guardrails

- This is a **reporting** tool. It never edits the model or
  `config/scenarios.py`, and the CHP behind-the-meter add-back it applies
  exists only in the report (heatmap / dispatch / fit), never in the LP. Don't
  change model code while running this skill.
- Only plants that both contribute to the grid LP and report to CAMPD are
  included — that scoping lives in the generator; don't second-guess it here.
- If the user wants different scope (e.g. a single ISO, extra years, a
  different plant filter), pass bundles/flags rather than hand-editing the
  generated HTML.
