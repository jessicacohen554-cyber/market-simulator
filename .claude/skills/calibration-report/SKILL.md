---
name: calibration-report
description: Register new backcast calibration runs on the deployable results dashboard (registry sidecar + per-run JSON data), commit them conflict-free for GitHub Pages, and report the headline. Use when the user asks for "the calibration report", "the backcast report", "the dashboard", to add a new run to the dashboard, or wants to see/share calibration results visually.
---

# Backcast results dashboard

Register calibration runs on the JSON-driven backcast results dashboard. The
dashboard is the pair of codebase-site pages served by GitHub Pages:

* `docs/codebase-site/backcast-runs.html` — the **Run Explorer** (per-run
  detail; deep-linkable via `#iso=<ISO>&run=<run-id>`).
* `docs/codebase-site/calibration-status.html` — the **Calibration Status**
  all-ISO keeper summary (deep-linkable via `#iso=<ISO>`).

Both load run data from `data/backcast/` (deploy-built copy) with a fallback
to `frontend/data/backcast/` via `docs/codebase-site/js/bc-data.js`. Data
generator: `scripts/render_backcast.py` (per-run payloads + bench parts). The
old root `backcast-results.html` is a static redirect stub to these pages —
never regenerate or edit it. The standalone embedded report
(`scripts/render_calibration_html.py`) is retained only for one-off
self-contained sends; the dashboard is the standard format.

The Run Explorer shows **one run at a time** in three views: **Run report**
(default — per-year scorecard, class-tolerance and dispatch-correlation
heatmaps across all testing years, monthly LMP vs actuals, and auto-generated
diagnostics that localize each miss by season/zone/plant), **Charts**
(per-year deep-dive incl. commitment heatmaps and the month/zone volume-miss
bars), and **Tables** (generation mix and reference tables). The diagnostics
are computed client-side from the run payload, so they appear automatically
for every newly pushed bundle.

## How publishing works (conflict-free by construction)

The shared dashboard data files — `frontend/data/backcast/manifest.js`,
`benchmark.js`, `completeness.js` — are assembled from the committed per-run
files by the stdlib-only `scripts/build_manifest.py`. They ARE committed (so a
raw checkout's local preview works via the bc-data.js fallback), **but you
must never hand-commit them.** The "Deploy site to GitHub Pages" workflow is
their single writer: on every merge to main it regenerates them, commits them
back (with `GITHUB_TOKEN`, which does not re-trigger the deploy), and copies
the full data set into `docs/codebase-site/data/backcast/` (gitignored,
deploy-staging only) via `scripts/build_codebase_site_backcast.py`. Run
`scripts/build_manifest.py` locally only to *preview* — leave the resulting
changes to those files uncommitted; the deploy reconciles them.

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

**Retention rule (2026-06-21, user-set; supersedes the 10-run rule of
2026-06-17): the dashboard keeps the top 15 runs per ISO.** Register EVERY
completed run — keeper or probe alike (mark rejected probes "(PROBE)" in the
sidecar definition). **Do not run a probe bundle without registering it** —
the dashboard is the only way the user sees results; an unregistered /tmp
probe leaves them flying blind. When over the 15-run limit, delete the
displaced **oldest** runs' sidecar (`registry/<id>.json`) and payload
(`runs/<id>.js`) in the same commit — drop the oldest even when an old run
scored better, because the model design evolves and only the prior keeper
stays a meaningful comparison. Then regen/rebuild the manifest. Bundles in
`results/calibration/` are kept — only the dashboard registration is pruned.

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
   and refreshes the local (gitignored) preview. Prints `RUN_ID=<id>` **and the
   run's calibration determination** (`DETERMINATION: CALIBRATED |
   CALIBRATED-WITH-CAVEATS | NOT-YET`) — `scripts/calibration_verdict.py` scores
   the just-written committed artifacts against
   `docs/calibration-determination-rubric.md` (the re-determination trigger:
   every registered run re-runs the scorer). Re-print any run's determination
   with `python scripts/calibration_verdict.py results/calibration/<name>`
   (add `--json` for the machine verdict). A `NOT-YET` with an out-of-tolerance
   criterion is real — either it is a `MODEL MISS` to fix, or it is an accepted
   measured-input limitation that must be recorded in the bundle's
   `calibration_attestation.json` exceptions ledger (governance attestation +
   per-caveat metric/year/magnitude/reason) before it can become a `CAVEAT`.

3. **Preview locally** (assembles the full dashboard data from ALL registered
   runs, instant, no bundle access):
   ```bash
   python scripts/build_manifest.py
   ```
   Then open the Run Explorer over a local server (bc-data.js falls back to
   `frontend/data/backcast/` when the deploy-built copy is absent; `file://`
   won't work because keepers.json is fetched):
   ```bash
   python -m http.server 8000  # then open
   # http://localhost:8000/docs/codebase-site/backcast-runs.html#iso=<ISO>&run=<RUN_ID>
   ```

4. **Register the ablation twin (KEEPERS ONLY — CLAUDE.md rule 20 / audit D-3).**
   Before a run can become (or stay) a keeper it must have a **registered
   zero-forcing ablation twin**: a reference solve with every merchant floor/
   bridge OFF (keeping only nuclear must-run, CHP steam-following, coal
   take-or-pay), so the keeper-vs-twin per-class delta shows what each floor
   buys. `audit_keepers.py` **E9** FAILs a (non-grandfathered) keeper without one.

   a. **Solve the twin** as a *concurrent separate invocation* from the keeper
      (rule 12; cap 2 for per-plant multi-zone ISOs), SAME full year span:
      ```bash
      python scripts/run_calibration_full.py --iso <ISO> --year 2023 2024 2025 \
          <the keeper's exact flags> \
          --out-dir results/calibration/<name> --zero-forcing-ablation
      # → solves into results/calibration/<name>-ablation, records
      #   "ablation_of": "<name>" in that bundle's run_config.json
      ```
   b. **Register the twin** with an id that suffixes the keeper's id with
      `-ablation` (so it lands at `registry/<keeper-id>-ablation.json`):
      ```bash
      python scripts/dashboard_add_run.py --label "<keeper label> (ABLATION TWIN)" \
          --bundle results/calibration/<name>-ablation
      ```
      Mark the sidecar definition "(ABLATION TWIN of <keeper-id>)".
   c. **Link it from the keeper sidecar.** Add to
      `frontend/data/backcast/registry/<keeper-id>.json`:
      ```json
      "ablation_twin": "<keeper-id>-ablation",
      "market_story": "<one line per class the floor moves: WHY the real market
          produces that generation — a market story, not 'the floor buys the
          residual'. A delta explainable only as residual-buying is an open
          root-cause issue, not a calibrated floor.>"
      ```
      The Run Explorer renders the keeper-vs-twin per-class delta and the
      `market_story` on the keeper's run page.

5. **Commit + push** the per-run files only (include the twin's files and the
   updated keeper sidecar when a twin was registered):
   ```bash
   git add results/calibration/<name> \
           frontend/data/backcast/registry/<id>.json \
           frontend/data/backcast/runs/<id>.js \
           frontend/data/backcast/bench
   git commit -m "results: <label> — <one-line what changed>"
   ```
   **Never push the sidecar without its `runs/<id>.js` payload in the same
   push** — even for a rejected/non-keeper probe, even to keep an API push
   call small. `build_manifest.py` skips a sidecar with no matching payload
   silently (no error, no warning surfaced anywhere), so a sidecar-only
   registration is a run that's on record but permanently invisible in the
   Run Explorer. This already happened to five probes (nyiso-54, nyiso-58,
   pjm-84, pjm-85, caiso-66) and is now a CI gate
   (`scripts/check_registry_payload_parity.py`, wired into `ci.yml`) — a PR
   that adds a sidecar without its payload fails CI. Run it locally before
   pushing if you're unsure: `python scripts/check_registry_payload_parity.py`.
   Merging to main auto-deploys (single Pages workflow, <1 min). Report the
   headline **led by the calibration determination** (CALIBRATED /
   CALIBRATED-WITH-CAVEATS / NOT-YET and, when not CALIBRATED, the deciding
   criterion), then the run scorecard: classes in tolerance per year, system
   volume error, fleet dispatch r, LMP Δ vs actual, and the worst-offending
   classes (with the dashboard's diagnostics pointer for each, e.g.
   "summer-concentrated, peak tranche"). Commit the bundle's
   `calibration_attestation.json` alongside the other per-run files whenever it
   exists or is added.

After bulk changes (deleting/relabelling bundles, payload schema changes), do
a full rebuild with `python scripts/regen_dashboard.py` (re-renders every
registered run from its bundle) and commit any changed `runs/*.js`, sidecars
and bench parts.

## Calibration Status page (all-ISO summary)

**Calibration Status** (`docs/codebase-site/calibration-status.html`) is a
one-page, every-ISO summary of each market's current keeper: the headline
determination, the C1–C8 status matrix with per-year magnitudes and the
MODEL-MISS vs ACCEPTED-LIMITATION classification (C7 diurnal shape and C8
forced-energy share read the bundle's committed `legitimacy_diagnostics.json`
— generate it with `scripts/legitimacy_diagnostics.py --bundle <dir> --iso
<ISO> --json-out <dir>/legitimacy_diagnostics.json` when registering a run,
or those two HARD criteria show SKIPPED and cap the determination), the D-7
statistical-mode gap as a REPORTED line, the tests conducted, and the
best-practice justification, with a deep link into each keeper's Run Explorer
report. It renders client-side from `status.js` (`window.BC.status`).

Unlike manifest.js/benchmark.js, **status.js is a committed file** (built where
the bundles live, not at deploy time): the C6 governance verdict reads each
bundle's `calibration_attestation.json`, which the Pages deploy's sparse
checkout does not fetch. So when a keeper changes:

1. Update the current keeper run id for that ISO in
   `frontend/data/backcast/keepers.json`.
2. **Run the keeper-text auditor.** Editing `keepers.json` fires the
   `keeper-audit.sh` PostToolUse hook, which asks you to launch the
   `calibration-keeper-auditor` subagent (Agent tool, `subagent_type:
   calibration-keeper-auditor`). It runs `scripts/audit_keepers.py` to confirm
   every keeper's run-report header (its registry-sidecar `definition`) and the
   Calibration Status page still match the keeper's actual results, repairs any
   placeholder/stale text, and rebuilds `status.js`. You can also run it directly:
   ```bash
   python scripts/audit_keepers.py            # exits 1 on any FAIL
   ```
3. Regenerate + commit the status data (re-runs `calibration_verdict.py` for
   every keeper, so the page can never disagree with the gate):
   ```bash
   python scripts/build_status.py
   git add frontend/data/backcast/keepers.json frontend/data/backcast/status.js
   ```
   `python scripts/build_status.py --check` fails (exit 1) if status.js is stale
   vs the current verdicts — a cheap CI/pre-commit guard.

`build_manifest.py` never regenerates status.js — the deploy just copies the
committed file to the pages' data dir.

## Notes

- The dashboard pages load run data via `<script src>` +
  `DecompressionStream`, which needs a current browser. Serve locally over
  HTTP (`python -m http.server`) — `keepers.json` is fetched, so plain
  `file://` opening hits the CORS trap. Run `python scripts/build_manifest.py`
  first if `manifest.js`/`benchmark.js` aren't fresh in your checkout.
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
