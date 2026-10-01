# FINDING — why five of six shards could not push their dispatch parquet (miso-255, 2026-09-12)

**One sentence:** `.gitignore` ignores `results/calibration/*/dispatch/` repo-wide on a
belief about the remote's 413 limit that is **false**, which forces every dispatch push
through `git add -f`, which the auto-mode classifier refuses — and asking for `-f`
hardened one session's permission state until even the plain `git add` that had worked
at solve time was denied.

This is a **prompt-and-gitignore defect, not a model defect and not a container-loss
event.** Every bundle survived. Nothing was lost to disk reclamation.

## 1. The causal chain, each link measured

| # | Link | Evidence |
|---|---|---|
| 1 | `.gitignore:651` ignores `results/calibration/*/dispatch/` for the whole repo | the line itself, present at pin `d0fec486` |
| 2 | Its stated reason is a size belief: *"dispatch/<year>_P1.parquet alone is ~80 MB and would trip the remote's 413 push limit"* | `.gitignore:610`, comment block |
| 3 | **That belief is FALSE.** | `claude/miso255-promote-2023` pushed **102,367,743 bytes** as a single-blob pack over plain `git push`, no 413, sha `974991e63dc019384b402c84e2ca4dd8f73d1c54`. `claude/miso255-promote-2025` pushed **94,467,628 bytes**, sha `c425a9fce1e29a8b8df946efcb665e3c969ff8db`. Both verified by `git ls-tree -r -l`. |
| 4 | Because of (1), any dispatch push needs `git add -f` | plain `git add` silently no-ops on an ignored path |
| 5 | The auto-mode classifier refuses `git add -f` | 2022 shard: *"git add denied by classifier [Modify Shared Resources]"* |
| 6 | After that refusal, **even plain `git add` was denied in that session** | 2022 shard, later turn: *"git add denied by Bash permission rules; needs Bash(git add:*) grant"* |
| 7 | Yet plain `git add` HAD worked in that same session at solve time | its slim 8-file bundle is committed at `74171ce23325f3cdb97b484f43423af51bb2202d`, `meta.timestamp` 2026-09-12T20:15:48 — before any `-f` request (21:11+) |

**Link 6→7 is the sharp edge: requesting `-f` cost the session the ability to do the
plain thing.** The escalation is one-way within a session. A prompt that never asks for
`-f` never triggers it.

## 2. What was NOT the cause

- **Not container loss.** All five D-generation shards still had their full bundles on
  disk when re-woken by `create_trigger` with `persistent_session_id` (186–209 MB each).
  Archiving a session releases its container but did not destroy the data here.
- **Not pack size.** See link 3. Three other lanes already carry committed dispatch
  parquets on `main`: `caiso275_B_gascoupling_{2022,2023,2024,2025}` at 45–49 MB each,
  and `nyiso_fuelvintage_H2/dispatch/2022_P1.parquet` at 21.4 MB.
- **Not a rule requiring the bundle be withheld.** Rule 29 `[R-SCREEN]` (c) governs what
  reaches `main`. A shard branch is not `main`. Rule 34 `[R-SHARD-PROMOTABLE]` (a) now
  says this explicitly.

## 3. The prompt defects that produced it (mine)

1. **I told the shards to gitignore their bundles.** Verbatim: *"`results/calibration/
   miso255_sil_<year>/` is GITIGNORED on purpose — leave it on disk, do NOT add it, do
   NOT delete it (rule 31)."* This is the rule-34(a) defect, and it is what made `-f`
   necessary later.
2. **I then told them the per-unit layer was not needed.** Verbatim: *"The per-unit layer
   is only needed for unit-level questions and is explicitly NOT required for
   registration."* False — `render_calibration_html.build_payload` reads
   `dispatch/<year>_P1.parquet` per year and raises `FileNotFoundError` without it. This
   cost a second round trip to every shard.
3. **I asserted a size limit without checking the repo.** I said ~100 MB packs were
   "unlicensed and unmeasured" and nearly forced a full six-year re-solve on that basis,
   with three counterexamples already committed on `main`.
4. **My verification grep was unscoped.** `git ls-tree -r --name-only <branch> | grep
   '2022_P1.parquet'` matches `caiso275_.../2022_P1.parquet` inherited from `main`, so I
   reported 2022 and 2025 as landed when neither had pushed. The correct check is
   `git diff --name-only --diff-filter=A <pin> <branch> -- <that bundle path>`, which is
   what `scripts/check_shard_bundles.py` does.

## 4. Prevention

- **Rule 34 `[R-SHARD-PROMOTABLE]` (a) needs a correction.** As written it prescribes
  `git add -f <its out-dir>` — *the exact command the classifier refuses*. It should
  instead have the shard append a `.gitignore` negation for its own out-dir and then use
  a **plain** `git add`:

  ```
  printf '\n!results/calibration/<out-dir>/**\n' >> .gitignore
  git add .gitignore
  git add results/calibration/<out-dir>
  ```

- **Reconsider `.gitignore:651`.** Its rationale is measurably false. Either correct the
  comment to say the exclusion is about repo *weight* (a defensible reason) rather than
  a 413 limit (not a real one), or carve a negation for bundle families that will be
  registered. Leaving a false technical claim in place is what made five shards fight
  their own tooling.

- **Verify retrievability with the guard, never with a bare grep** —
  `python scripts/check_shard_bundles.py --pin <sha> <refs>` (rule 34(d)).

## 5. Cost

Zero data lost. One year (2022) re-solved at ~745 s because its session's permission
state could not be recovered; the other five were retrieved by push. The avoidable cost
was ~2 h of round trips against a constraint that did not exist.

## 6. Recovered artifacts, by immutable sha (rule 33 `[R-SHARD-ARCHIVE]` (d))

```
git checkout f08aecdee1d6d093047f1e4c97ad98d76d0d71e2 -- results/calibration/miso255_promote_2020
git checkout 578f96617a8b6ba60f79e126d78c222e7ad52aea -- results/calibration/miso255_promote_2021
git checkout 974991e63dc019384b402c84e2ca4dd8f73d1c54 -- results/calibration/miso255_promote_2023
git checkout f5bf4c84c9cdb4268343954d97ad478759f430b9 -- results/calibration/miso255_promote_2024
git checkout c425a9fce1e29a8b8df946efcb665e3c969ff8db -- results/calibration/miso255_promote_2025
```

2022 is re-solving on branch `claude/miso255-promote-2022b`; its sha is appended when it
lands. The slim-only original stays at `74171ce23325f3cdb97b484f43423af51bb2202d`.
