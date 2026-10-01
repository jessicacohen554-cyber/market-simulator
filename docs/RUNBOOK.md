# Calibration lane runbook

The one page a calibration session needs. Every command here exists at HEAD;
the rules it enforces are the `[R-*]` IDs in `CLAUDE.md`. Read this, the
target ISO's keeper shard (`frontend/data/backcast/keepers/<ISO>.json`) and
its lever queue (`docs/mechanism-testing-matrix.md` §5), and start.

## 0. Session setup (5 minutes, zero LP)

```bash
uv sync                                   # the session-start hook already did this
python3 scripts/hydrate_data.py --profile <iso>     # only a lane that solves needs data
python3 scripts/regenerate_clean.py --solve-profile <ISO>   # falls back to the full rebuild if absent
git checkout -b claude/<lane> origin/main
```

`uv sync` is the only install route. Never `pip install -e .` — it resolves a
different HiGHS than the lock and the keeper's provenance moves with it.

## 1. Phase 0 (zero LP) — decide before you spend

Answer with files, not solves: a `fleet_only` rebuild, an offer-array delta,
a footprint census, or the keeper's committed hourlies
(`results/calibration/<keeper>/hourly/*.parquet`). Write the one-page
PRECOMMIT (`docs/records/<lane>/PRECOMMIT-<lane>-<date>.md`): the mechanism,
its measured driver and forward story (rule 13), the exact config delta, and
the pass/fail reading fixed **before** any number exists. Check the lever
queue first; a cell already `R`/`I`/`G` is not re-tested without new evidence.

## 2. Solve — one shard per year, never in this session

```bash
git push -u origin claude/<lane>                  # pin what the shards will clone
SHA=$(git rev-parse HEAD)
python3 scripts/shard_prompt.py --iso <ISO> --all-years --sha $SHA --lane <lane> \
    --bundle results/calibration/<keeper-bundle> --set <field>=<json> --note "<lane>: <what>"
```

Give each printed prompt to `mcp__claude-code-remote__create_session`
(`source_url` = this repo, `source_revision` = `$SHA`). The prompt carries the
hard stops, the full-bundle push and the report format. The parent session
never calls `run_calibration_full.py` or `replay_keeper.py` itself (rule 32).

When a shard reports: fetch its branch, `git checkout <sha> -- <out-dir>`,
confirm `dispatch/<year>_P1.parquet` is present, **then** archive the shard
(`archive_session`). A shard branch is transport, not storage (rule 33 (f)).

## 3. Compose and score (zero LP)

```bash
python3 scripts/probes/_miso260_compose_span.py --out results/calibration/<lane>_span \
    --leg results/calibration/<lane>_2023 --leg results/calibration/<lane>_2024 ...
python3 scripts/calibration_verdict.py results/calibration/<lane>_span
python3 scripts/legitimacy_diagnostics.py results/calibration/<lane>_span    # C8 / D-1 / D-2 / D-4
```

Read the verdict against the PRECOMMIT's pre-fixed reading. Write the RESULT
doc beside the PRECOMMIT with the gate table and the decision card for the
owner. **Do not delete any solved bundle** until the owner has ruled (rule 31);
the bundles live under `results/calibration/` and are gitignored until promoted.

## 4. Promote (one command, when the owner says promote)

```bash
python3 scripts/promote_keeper.py --iso <ISO> \
    --bundle results/calibration/<lane>_span --label "<lane> <keyword>" \
    [--fold results/calibration/<lane>_tp="<lane> touchpoints"] \
    --attested-by "<lane>; owner ruling '<text>' <date>" \
    --note "<ISO> keeper #N: <one line: what changed and why>"
```

It registers, attests (DOF ledger), designates the shard, folds touchpoints,
re-keys the `complete` marker and the forecast gate-(a) stamp, rebuilds the
status part, audits, prunes the outgoing keeper and runs the parity gate — in
that order, stopping before the prune on any audit FAIL (rule 35). It prints
the `git add` list. Two things remain yours:

* stamp the keeper and the tested cell in `docs/codebase-site/data/mechanism-matrix/<ISO>.js`;
* one entry in `docs/calibration-log/<iso>.md`.

Commit the bundle, sidecars, payload, keeper shard and status part in one
commit (`git push`, small pack); docs in another. Open the PR, merge it, archive
every shard, and report the branches the owner must delete (a session cannot;
`git push --delete` returns 403).

## 5. What a session reports

Lead with the determination and the gate table. Numbers in a table, not prose.
Name the bundles on disk and whether they are promotable without a re-solve.
Ask the promotion question explicitly. Nothing else is required.
