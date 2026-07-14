---
name: calibration-report
description: Register new backcast calibration runs on the deployable results dashboard (registry sidecar + per-run JSON data), commit them conflict-free for GitHub Pages, and report the headline. Use when the user asks for "the calibration report", "the backcast report", "the dashboard", to add a new run to the dashboard, or wants to see/share calibration results visually.
---

# Backcast results dashboard

> **The bundle you register must come from an in-session solve.** Run
> `scripts/run_calibration_full.py` in the Claude session — never spin up a
> GitHub Actions workflow to produce or register a run. This repo is private and
> runner-minutes are billed (see CLAUDE.md → "GitHub Actions — never offload
> work to CI"). This skill only registers an already-produced bundle and pushes
> the dashboard files; it does not run solves on CI.

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
files by the stdlib-only `scripts/build_manifest.py`. They ARE committed (the
Run Explorer serves them via the bc-data.js fallback). **Amended 2026-07-14
(owner): the "Deploy site to GitHub Pages" workflow that used to regenerate and
commit them was removed (all GitHub Actions workflows were deleted). They are no
longer auto-refreshed — you MUST run `scripts/build_manifest.py` and commit the
regenerated `manifest.js`/`benchmark.js`/`completeness.js` yourself, in the same
push as the sidecars/payloads. A stale committed manifest makes the run invisible
in the Run Explorer.** Only `docs/codebase-site/data/backcast/` (gitignored, was
deploy-staging) stays generated-not-committed; the bc-data.js fallback loads the
committed `frontend/data/backcast/` files when it is absent.

Each run commits ONLY files in its own namespace, so any number of parallel
sessions — same ISO or different ISOs — merge to main without conflicts or
rebasing:

* `results/calibration/<name>/` — the bundle.
* `frontend/data/backcast/registry/<id>.json` — the sidecar holding the run's
  complete manifest entry (id, label, date, shorthand, definition, years, iso,
  file, bundle). **To refine a run's label or definition, edit its sidecar**
  (not manifest.js), then re-run `build_manifest.py` and commit the refreshed
  manifest.
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

4. **Keeper sidecar `market_story` (KEEPERS).** Add a `market_story` to the
   keeper's `frontend/data/backcast/registry/<keeper-id>.json` — one line per
   class the mechanism moves: WHY the real market produces that generation (a
   market story, not "the floor buys the residual"; a delta explainable only as
   residual-buying is an open root-cause issue, not a calibrated floor). The Run
   Explorer renders it on the keeper's run page.
   ```json
   "market_story": "<...>"
   ```
   **The zero-forcing ablation twin is NO LONGER required** (CLAUDE.md rule 20,
   owner amendment 2026-07-14): keepers no longer build or register a twin, and
   `--zero-forcing-ablation` is not part of the keeper workflow. Forcing-
   legitimacy rests on the DOF ledger + `legitimacy_diagnostics.json` (the C8
   forced-share gate and D-4 off-window-binding check). `audit_keepers.py` E9 no
   longer FAILs a twinless keeper — it only flags a DECLARED `ablation_twin`
   sidecar link that does not resolve. Already-registered twins may stay on the
   dashboard (keep their `ablation_twin` link); do not solve new ones.

5. **Commit + push** the per-run files AND the refreshed generated data files.
   Regenerate the manifest from the sidecars first, then stage everything:
   ```bash
   python scripts/build_manifest.py   # refreshes manifest.js/benchmark.js/completeness.js
   git add results/calibration/<name> \
           frontend/data/backcast/registry/<id>.json \
           frontend/data/backcast/runs/<id>.js \
           frontend/data/backcast/bench \
           frontend/data/backcast/manifest.js \
           frontend/data/backcast/benchmark.js \
           frontend/data/backcast/completeness.js
   git commit -m "results: <label> — <one-line what changed>"
   ```
   The generated files MUST be committed (2026-07-14 owner amendment): the deploy
   that used to refresh them was removed, so a stale committed manifest leaves the
   run invisible in the Run Explorer.
   **Never push the sidecar without its `runs/<id>.js` payload in the same
   push** — even for a rejected/non-keeper probe, even to keep an API push
   call small. `build_manifest.py` skips a sidecar with no matching payload
   silently (no error, no warning surfaced anywhere), so a sidecar-only
   registration is a run that's on record but permanently invisible in the
   Run Explorer. This already happened to five probes (nyiso-54, nyiso-58,
   pjm-84, pjm-85, caiso-66). Run the parity check locally before every push
   (the CI gate that enforced it was removed with the workflows 2026-07-14):
   `python scripts/check_registry_payload_parity.py`. There is no deploy step —
   the Run Explorer serves the committed `frontend/data/backcast/` files
   directly, so the refreshed manifest from step 5 is what makes the run show.
   Report the
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

`build_manifest.py` never regenerates status.js — it is committed on its own via
`build_status.py` (above) and the Run Explorer reads the committed copy directly.

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
