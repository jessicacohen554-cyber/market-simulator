# FINDING — the ruff pre-push gate: a mechanical replacement for the lane checklists

**Date:** 2026-09-06 · **Scope:** `.claude/hooks/ruff-prepush-gate.sh`,
`.claude/settings.json`, the two lane checklists. **No solve, no scorer path, no
`ScenarioConfig` field — no determination moves.**

## 1. The incident this closes

Two ruff-format drifts reached `main` from two different desks within nine hours
on 2026-09-06:

| # | File | Landed | Cleared by |
|---|------|--------|-----------|
| 1 | `scripts/data/derive_caiso_offer_surface.py` | unformatted on `origin/main` (caiso-255) | another lane, `824f9567` — "port the base-branch fix so this PR's CI can be read" |
| 2 | `scripts/gen_caiso257_attestation.py` | added at `48bcd0ec` (caiso-257, PR #5162) | `claude/caiso-attestation-ruff-format-cs2luk` |

Both desks responded by writing a STANDING pre-push checklist into their own lane
doc — MISO `767e96fa`, then CAISO. **The MISO checklist landed 13 seconds before
`48bcd0ec`** (15:25:29 vs 15:25:42), so it could not have caught the second
drift. That is the argument for a hook in one line: a checklist binds only a
session that reads its lane doc first, and the two events were independent desks
hitting the same trap, not one desk's habit.

Severity is not cosmetic: `Ruff lint + format check` is **one of R-AE's six
required checks**, so a format-only miss holds the flip set below 6 of 6 and
blocks every lane behind it.

Root cause, in both cases: **both files were NEW**. `ruff-autofix.sh` is
`PostToolUse` on `Edit|Write`, scoped to the edited path (HOUSE-1). Bytes that
arrive via `mcp__github__push_files`, a Bash heredoc, a generated file or a merge
resolution never fire it — exactly the routes a calibration session uses for new
derive, attestation and probe scripts. **The hook's silence was never evidence of
a clean tree.**

## 2. What was built

`.claude/hooks/ruff-prepush-gate.sh`, a `PreToolUse` hook on
`Bash|mcp__github__push_files` (the repo's first `PreToolUse` hook). On a push it
runs the two commands CI runs (`ci.yml:411` lint, `ci.yml:413` format) against
**this branch's own changed `.py` files** and refuses the push if either fails,
naming the files and the fix.

Four design constraints, each load-bearing:

**(a) Check-only; it never writes.** `ruff-autofix.sh`'s header records why: it
originally ran `ruff format .` TREE-WIDE and caused the T.1 incident, rewriting
files the session never touched — a rule-27 `[R-PUSH]` full-file rewrite
(2026-08-05 `constants.py`, 3,960 → 9,508 lines; 2026-08-08
`tests/unit/data/test_outages.py`). A gate that only inspects and refuses cannot
reproduce that class at all.

**(b) Scoped to this branch, not the tree.** CI is tree-wide; this gate must not
be, because of the **ambient-red problem** (HOUSE-1 §3) — `main` periodically
carries format-red files you did not put there, drift #1 being exactly that. A
tree-wide *blocking* gate would wedge every session behind another lane's red,
converting a CI failure into a total inability to push, which is strictly worse
than the problem being solved. The set is `origin/main...HEAD` (merge-base →
HEAD, so only what this branch changed) plus staged and unstaged work.

**(c) It must cover `push_files`, which is why it is not a git hook.**
`mcp__github__push_files` commits server-side over the GitHub API and never
touches local git, so `.git/hooks/pre-push` physically cannot see it — and that
is the exact route the drifts took. A git-hook-only fix would miss the real
failure mode.

**(d) Fail-open by construction.** Missing `uv`/`jq`/git, an unreadable repo, or
ruff's own error exit all return "allow" with no output. It refuses only on a
genuine violation.

## 3. Measured facts behind the implementation

- **Ruff exit codes** (measured): `0` clean — *including when every path given is
  excluded* — `1` genuine violation, `2` error (e.g. a nonexistent path).
  The gate blocks on `1` only; blocking on `2` would wedge sessions over a
  deleted path.
- **`--force-exclude` is mandatory** when naming paths explicitly. Verified
  against the excluded `src/market_sim/config/constants.py`: plain
  `ruff format --check -- <path>` reports *"1 file already formatted"* (it read
  the excluded file), while `--force-exclude` reports *"No Python files found"*.
  Without it the gate would refuse pushes over `constants.py`, `scripts/probes`,
  `scripts/archive`, `results` and the R-AC capx probe scripts under
  `docs/handoffs`.
- **Cost:** tree-wide `ruff format --check .` is 0.284 s, so the gate is not a
  latency concern; the concern is that the `Bash` matcher fires on every call, so
  the non-push path exits before invoking `uv`.
- **Blocking contract:** exit 0 + JSON
  (`hookSpecificOutput.permissionDecision: "deny"` with
  `permissionDecisionReason`), not exit 2 — an unrelated nonzero exit from a
  script bug reads as an error rather than a decision, and malformed output fails
  open. Reason strings are built with `jq -n`, never concatenation.

## 4. Verification — all executed, all passing

| # | Test | Result |
|---|------|--------|
| 1 | NEGATIVE: own `.py` dirty + `git push` | **deny**, reason names the file + fix |
| 2 | POSITIVE: clean tree + `git push` | allow |
| 3 | **AMBIENT-RED**: a file this branch never touched is red; tree-wide ruff RED | **allow** — not wedged by another lane |
| 4 | `mcp__github__push_files`, dirty | **deny** (git hooks could not do this) |
| 5 | Non-push Bash (`ls`, `git status`), and `Edit` | allow, no ruff invoked |

Fail-open: no `jq` → allow; empty stdin → allow; malformed stdin → allow; missing
`tool_name` → allow. Deny payload validates against the schema.

Push-predicate correctness, 18 cases: matches `git push`, `git -C x push`,
`git -c k=v push`, `cd x && git push`, `a; git push`, `then/do` forms, `(git
push)`, pipelines; does **not** match `git status`, `git commit -m 'push it'`,
`git log --grep=push`, `echo git push`, `grep -rn 'git push' docs/`,
`git push-notes`, `git pushx`.

## 5. What this does NOT do

- It does not gate the tree, so a red file you did not touch still reaches CI —
  by design (b). CI remains the tree-wide authority.
- It does not replace `ruff-autofix.sh`; the two are complementary layers
  (autofix keeps your `Edit|Write` bytes clean, the gate catches every other
  route).
- It does not replace the lane checklists, which stay as the fallback for
  sessions running without hooks. Both were updated to point at the hook.
- A hook can be disabled. This raises the floor; it is not a proof.
