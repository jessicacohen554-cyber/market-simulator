# run-config-debt — RECONSTRUCTED run_configs for the seven legacy forecast legs

**Every `run_config.json` under this directory is a RECONSTRUCTION, not an
original artifact.** Each carries a top-level `reconstruction` block stating
its status, method, evidence chain, verification, and what remains
unverified. Produced by lane capx-D8 (2026-08-30);  full method and per-leg
evidence: `docs/handoffs/FINDING-capx-d8-dof-ledger-2026-08-30.md` §4.

## Why this directory exists

The FFR-3A-3 / FFR-3A-4 wave (2026-08-04) solved seven forecast-family legs —
four T1-H realized hindcasts and three T1-X crossovers — whose bundles were
gitignored by design and whose harness-era `run_config.yaml` dumps died with
the containers. Their FC-7 rows in `frontend/data/forecast/ff-verdicts.json`
read FAIL `run_config.json absent` (an instrument-shape defect recorded at
the time: FFR-3A-2 handoff blocker 5 — the hindcast harness wrote YAML where
FC-7 required JSON, and the fix was deliberately deferred to an instrument
lane rather than authored after the score). These seven are the board-tracked
legs that still carry the debt; the D10/D14-era legs already comply
(committed `run_config.json` under `results/hindcast/`).

## How the reconstructions were made (zero solves)

`run_capacity_hindcast.build_config` was imported at the leg's recorded solve
sha (mapped across the 2026-08-16 history rewrite via
`docs/governance/citation-commit-map.txt`) in a sparse worktree and called
with the invocation documented in the committed record (all solve-affecting
flags omitted — the documented posture); the resolved `ScenarioConfig`
`asdict()` is the `scenario_config` block. No solve was run; no model surface
was touched.

Verification, per leg:

* all six FFR-3A-3 legs reproduce the six documented resolved posture flags
  exactly (ffr-3a3 handoff §1.3);
* the FFR-3A-4 MISO T1-X leg additionally reproduces its committed cache key
  `46954f417b6e18e2` (results/ffr3a4/RESULT header) **byte-for-byte** — the
  cache key hashes the full registered config payload, so the config surface
  is recovered exactly.

## What a consumer may and may not do with these

* A chartered FC-7 re-score MAY read them (`--run-config
  results/run-config-debt/<leg>/run_config.json`), and must surface the
  RECONSTRUCTED label in whatever it emits — they are never to be presented
  as original run artifacts.
* Each leg also carries a `dof_ledger.json` built FROM the reconstruction
  (labelled via its `basis` field) by `scripts/build_forecast_dof_ledger.py`.
* Nothing here changes any verdict by itself: the capx-D8 lane deliberately
  re-scored nothing (three in-flight lanes were writing the verdict/board
  files; the re-emission is a separately chartered follow-up).
