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
files by the stdlib-only `scripts/build_manifest.py`. The **"Deploy site to
GitHub Pages" workflow** (`.github/workflows/deploy-pages.yml`) regenerates them
from the sidecars at deploy time and publishes the site, so a registered run
appears on the LIVE dashboard once the deploy runs — you do NOT need to commit
these files for the live site. *Amended 2026-07-14 (owner): the deploy was
rebuilt as a simplified job that no longer commits the refreshed files back to
main, so the committed `frontend/data/backcast/` copies are used only by the
local `file://` preview (the bc-data.js fallback) and may lag the sidecars.
Optionally run `scripts/build_manifest.py` and commit them to keep that preview
current.* Only `docs/codebase-site/data/backcast/` (gitignored) stays
generated-not-committed — the deploy builds it into the published artifact.

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
probe leaves them flying blind. Retention is now **automatic and governs all
three stores**: `dashboard_add_run.py` runs `prune_iso` after every
registration, keeping the 15 newest runs for that ISO (by date, then id) and
deleting the displaced **oldest** runs' sidecar (`registry/<id>.json`),
payload (`runs/<id>.js`) **and** mapped `results/calibration/<bundle>/` dir
together (drop the oldest even when an old run scored better — only the prior
keeper stays a meaningful comparison as the design evolves). Keepers
(`keepers.json`) and ablation-referenced twins are never pruned; pass
`--no-prune` to register without sweeping. The pruned deletions are staged
with your commit; then regen/rebuild the manifest. See **scripts/README.md →
"Dashboard retention (top-15 per ISO, all three stores)"** for the full rule
and the `check_registry_payload_parity.py` both-direction gate.

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

5. **Commit + push** the per-run files. The Pages deploy rebuilds the manifest
   from these sidecars, so they are all the live dashboard needs:
   ```bash
   git add results/calibration/<name> \
           frontend/data/backcast/registry/<id>.json \
           frontend/data/backcast/runs/<id>.js \
           frontend/data/backcast/bench
   git commit -m "results: <label> — <one-line what changed>"
   ```
   *Optional (local `file://` preview only): run `python scripts/build_manifest.py`
   and also commit the refreshed `manifest.js`/`benchmark.js`/`completeness.js` to
   keep the committed copies in step with the sidecars. The LIVE dashboard does
   not depend on them — the deploy regenerates them from the sidecars.*
   **Never push the sidecar without its `runs/<id>.js` payload in the same
   push** — even for a rejected/non-keeper probe, even to keep an API push
   call small. `build_manifest.py` skips a sidecar with no matching payload
   silently (no error, no warning surfaced anywhere), so a sidecar-only
   registration is a run that's on record but permanently invisible in the
   Run Explorer. This already happened to five probes (nyiso-54, nyiso-58,
   pjm-84, pjm-85, caiso-66). Run the parity check locally before every push
   (the CI gate that enforced it was removed 2026-07-14; only the Pages deploy
   workflow remains): `python scripts/check_registry_payload_parity.py`. Merging
   to main triggers the Pages deploy (`.github/workflows/deploy-pages.yml`,
   ~1 min), which rebuilds the manifest from the sidecars and publishes it — that
   is what makes the run show live. Report the
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

Unlike manifest.js/benchmark.js, **the status data is committed** (built where
the bundles live, not at deploy time): the C6 governance verdict reads each
bundle's `calibration_attestation.json`, which the Pages deploy's sparse
checkout does not fetch. Since 2026-07-19 both the keeper registry and the
status data are **sharded per ISO** — `keepers/<ISO>.json` +
`status/<ISO>.js` (+ the deterministic `status/shared.js` rubric block) — so
keeper promotions in DIFFERENT ISOs touch disjoint files and merge without
rebasing (the old monolithic `keepers.json`/`status.js` are retired and
gitignored; `bc-data.js` composes the shards client-side). So when a keeper
changes:

1. Update the current keeper run id in that ISO's shard,
   `frontend/data/backcast/keepers/<ISO>.json` (or:
   `python scripts/lib/keeper_store.py --set <ISO> <run-id>`).
2. **Run the keeper-text auditor.** Editing a keeper shard fires the
   `keeper-audit.sh` PostToolUse hook, which asks you to launch the
   `calibration-keeper-auditor` subagent (Agent tool, `subagent_type:
   calibration-keeper-auditor`). It runs `scripts/audit_keepers.py --iso <ISO>`
   to confirm the keeper's run-report header (its registry-sidecar
   `definition`) and the Calibration Status page still match the keeper's
   actual results, repairs any placeholder/stale text, and rebuilds that ISO's
   status part. You can also run it directly:
   ```bash
   python scripts/audit_keepers.py --iso <ISO>   # exits 1 on any FAIL
   ```
3. Regenerate + commit that ISO's status part (re-runs `calibration_verdict.py`
   for the keeper, so the page can never disagree with the gate):
   ```bash
   python scripts/build_status.py --iso <ISO>
   git add frontend/data/backcast/keepers/<ISO>.json \
           frontend/data/backcast/status/<ISO>.js
   ```
   Stage `status/shared.js` too ONLY if it changed (it only moves when the
   rubric/scorer constants changed). `python scripts/build_status.py --check
   [--iso <ISO>]` fails (exit 1) if a part is stale vs the current verdicts —
   a cheap CI/pre-commit guard. **Never touch another ISO's shard or status
   part in a promotion commit** — per-ISO lane isolation is what keeps
   parallel promotions conflict-free.
4. **Promotion completeness: the same PR carries all four records** (owner
   ruling R-BF, 2026-09-25). CI job `promotion-completeness` checks them for
   every ISO whose keeper shard changed, and FAILS your PR if any is missing:
   - **(a) Gate (a) re-keyed.** `frontend/data/forecast/program-status.json`
     `isos.<ISO>.gate.a_keeper_marker` cites the new keeper and the right
     `marker complete=… final=…`. Check with
     `python3 scripts/check_gate_a_provenance.py --iso <ISO>`.
   - **(b) Marker re-keyed.** If the ISO holds `complete`,
     `calibration-complete.json` `complete.<ISO>.keeper` names the new keeper.
     If the new keeper reads NOT-YET, raise Q5 (withdraw) with the owner
     rather than re-keying silently.
   - **(c) FR-22 clean.** `python3 scripts/check_forecast_parity.py --iso <ISO>`
     shows 0 UNACCOUNTED.
   - **(d) E13 clean.** The outgoing keeper is pruned
     (`scripts/prune_iso_runs.py --iso <ISO>`, rule 35), so
     `python scripts/audit_keepers.py --iso <ISO>` shows no E13 failure.

   Run all four at once before pushing:
   ```bash
   python3 scripts/check_promotion_completeness.py --base origin/main
   ```

`build_manifest.py` never regenerates the status parts — they are committed on
their own via `build_status.py` (above); the Pages deploy publishes the
committed `keepers/` + `status/` dirs as-is (unlike manifest.js/benchmark.js,
which the deploy rebuilds from the sidecars).

## Notes

- The dashboard pages load run data via `<script src>` +
  `DecompressionStream`, which needs a current browser. Serve locally over
  HTTP (`python -m http.server`) — `keepers.json` is fetched, so plain
  `file://` opening hits the CORS trap. Run `python scripts/build_manifest.py`
  first if `manifest.js`/`benchmark.js` aren't fresh in your checkout.
- Calibration-log entries go to the PER-ISO continuation logs
  (`docs/calibration-log/<iso>.md`, lowercase — e.g. `ercot.md`;
  cross-ISO/governance entries to `docs/calibration-log/governance.md`). The
  monolithic `docs/calibration-log.md` is frozen as the pre-2026-07-19
  archive — never append to it. Per-run findings belong in the run's sidecar
  definition or a `SUMMARY-*.md` inside the bundle dir; with the sharded
  keeper/status/log lanes, parallel sessions in different ISOs share no
  editable file at all.
- This is a **reporting** tool: it never edits the model or `config/`. The two
  capture metrics and the CHP behind-the-meter add-back live in the generator;
  don't second-guess them here.
- To change scope (years, ISO, plant filter), adjust the bundles passed, not
  the generated HTML/JSON.
