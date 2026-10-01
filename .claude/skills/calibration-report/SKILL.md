---
name: calibration-report
description: Register a backcast calibration run on the results dashboard (a probe) or promote one to its ISO's keeper (the full chain in one command), then report the headline. Use when the user asks for "the calibration report", "the dashboard", to add a run, or to promote a keeper.
---
# Backcast results dashboard

The dashboard is two GitHub Pages views: `docs/codebase-site/backcast-runs.html`
(Run Explorer, `#iso=<ISO>&run=<id>`) and `calibration-status.html` (all-ISO
keeper summary, `#iso=<ISO>`). Data lives in `frontend/data/backcast/`: one
sidecar `registry/<id>.json`, one payload `runs/<id>.js`, per-(ISO, year)
`bench/` parts, the keeper shard `keepers/<ISO>.json`, the status part
`status/<ISO>.js`. The Pages deploy rebuilds `manifest.js` / `benchmark.js` /
`completeness.js` from the sidecars — never hand-commit those.

The bundle comes from an in-session shard solve (never CI). It needs
`meta.json`, `dispatch/<year>_P1.parquet` for every year, and the benchmark
parquets (`run_calibration_full.py --rebuild-benchmark DIR` rebuilds those
without a solve).

## Promote a keeper (the normal case)

```bash
python3 scripts/promote_keeper.py --iso <ISO> \
    --bundle results/calibration/<name> --label "<lane> <keyword>" \
    [--fold results/calibration/<touchpoint>="<lane> touchpoints"] \
    --attested-by "<lane>; owner ruling '<text>' <date>" \
    --note "<ISO> keeper #N: <what changed, why>"
```

One command: register → attest (DOF ledger) → designate → fold → re-key
`calibration-complete.json` and the forecast gate-(a) stamp → `build_status`
→ `audit_keepers --check` → prune the outgoing keeper → parity gate. It
refuses to shrink the ISO's registered year set and stops before the prune on
an audit FAIL (CLAUDE.md rule 35). It prints the `git add` list. Then: stamp
the keeper in `docs/codebase-site/data/mechanism-matrix/<ISO>.js`, add the
`docs/calibration-log/<iso>.md` entry, commit, push, PR.

## Register a probe (not a keeper)

```bash
python3 scripts/dashboard_add_run.py --label "<lane> <keyword> (PROBE)" \
    --bundle results/calibration/<name> --no-prune
```

Prints `RUN_ID=<id>` and the determination. A probe is pruned at the next
promotion (keeper-only retention, rule 15). Preview locally with
`python3 scripts/build_manifest.py` and `python -m http.server`.

## Report

Lead with the determination and the gate table (`scripts/calibration_verdict.py
results/calibration/<name>`). Numbers in a table. Link the Run Explorer deep
link. Ask the promotion question explicitly (rule 31).
