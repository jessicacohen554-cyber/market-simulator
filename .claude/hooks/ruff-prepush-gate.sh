#!/bin/bash
# PreToolUse hook on Bash|mcp__github__push_files — ruff pre-push REFUSAL gate.
#
# Refuses a push when the Python files THIS BRANCH changed are not ruff-clean.
# It is the mechanical replacement for the per-lane pre-push checklists in
# docs/calibration-log/{miso,caiso}.md, which remain as the fallback.
#
# WHY THIS EXISTS. Two ruff-format drifts reached main on 2026-09-06 from two
# different desks within nine hours: scripts/data/derive_caiso_offer_surface.py
# (caiso-255; cleared for that desk by another lane in 824f9567) and
# scripts/gen_caiso257_attestation.py (caiso-257, added at 48bcd0ec / PR #5162).
# Both desks wrote a STANDING checklist into their own lane doc — and the MISO
# checklist (767e96fa) landed THIRTEEN SECONDS before the CAISO drift commit,
# so it could not have caught it. A checklist only binds a session that reads
# its lane doc first. `Ruff lint + format check` is one of R-AE's six required
# checks, so a format-only miss holds the flip set below 6 of 6 and blocks every
# lane behind it, not just the offending desk's PR. Hence a hook.
#
# WHY NOT A GIT pre-push HOOK. `mcp__github__push_files` commits server-side
# over the GitHub API and NEVER TOUCHES LOCAL GIT, so .git/hooks/pre-push
# physically cannot see it. Both 2026-09-06 drifts were NEW files — precisely
# the route that arrives via push_files or a Bash heredoc and never fires the
# Edit|Write autofix hook. A git-hook-only solution would miss the actual
# failure mode. Do not "simplify" this into .git/hooks/pre-push.
#
# WHY CHECK-ONLY, NEVER AUTOFIX. Read the header of ruff-autofix.sh. That hook
# originally ran `ruff check --fix .` / `ruff format .` TREE-WIDE and caused the
# T.1 incident: whenever main itself carried format-red bytes it rewrote files
# the session never touched — a rule-27 [R-PUSH] full-file rewrite (2026-08-05
# constants.py, 3,960 -> 9,508 lines; 2026-08-08 tests/unit/data/test_outages.py).
# HOUSE-1 scoped it to the edited path. This gate only INSPECTS and REFUSES, so
# it cannot reproduce that class at all. It must never write to the tree, never
# `git add`, never touch the index.
#
# WHY SCOPED TO THIS BRANCH'S FILES, NOT THE TREE. CI is tree-wide; this gate
# must not be, because of the "ambient-red problem" (HOUSE-1 §3): main
# periodically carries format-red files you did not put there
# (derive_caiso_offer_surface.py was exactly this — unformatted on origin/main,
# owned by another lane). A tree-wide BLOCKING gate would wedge every session
# behind another lane's drift, converting a CI red into a total inability to
# push — strictly worse than the problem it solves. The file set is therefore
# `origin/main...HEAD` (merge-base -> HEAD, so only what this branch changed)
# plus staged and unstaged work. Tree-wide drift is reported as a NON-BLOCKING
# note and never refuses.
#
# FAIL-OPEN BY CONSTRUCTION. Every unexpected condition — missing uv/jq/git, an
# unreadable repo, ruff's own exit 2 (bad path, internal error) — exits 0 with
# no output, which lets the tool proceed through the normal permission flow.
# The gate refuses ONLY on ruff exit 1, a genuine violation. Ruff's exit codes,
# measured 2026-09-06: 0 clean (also when every path is excluded), 1 violation,
# 2 error. Blocking on 2 would wedge sessions over a deleted path.
#
# --force-exclude is MANDATORY when naming paths explicitly: without it ruff
# processes any path given on the command line regardless of pyproject's
# [tool.ruff] extend-exclude. Verified 2026-09-06 against constants.py — plain
# `ruff format --check -- <path>` reports "1 file already formatted" (i.e. it
# read the excluded file), while --force-exclude reports "No Python files found".
# Without it this gate would refuse pushes over constants.py, scripts/probes,
# scripts/archive, results and the R-AC capx probe scripts under docs/handoffs.
#
# CONTRACT: exit 0 + JSON on stdout (hookSpecificOutput.permissionDecision), not
# exit 2. Exit 2 is a coarser signal and an unrelated nonzero exit from a script
# bug reads as an error rather than a decision; JSON keeps the decision explicit
# and any malformed output fails open. Reason strings are built with `jq -n`,
# never string concatenation, so a filename can never break the payload.
set -uo pipefail

emit_allow() { exit 0; }   # no output => proceed through normal permission flow

command -v jq >/dev/null 2>&1 || emit_allow

payload=$(cat 2>/dev/null) || emit_allow
[ -n "$payload" ] || emit_allow

tool=$(printf '%s' "$payload" | jq -r '.tool_name // empty' 2>/dev/null) || emit_allow

# Decide whether this call is a push at all. Bash fires the matcher on EVERY
# call, so the non-push path must be cheap and must not invoke uv.
case "$tool" in
  mcp__github__push_files)
    : ;;                       # always a push
  Bash)
    cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null)
    [ -n "$cmd" ] || emit_allow
    # `git ... push` as a real command invocation: at a statement boundary,
    # allowing shell keywords and `git -C x`/`git -c k=v` options, and requiring
    # a non-word char after `push` so `git push-notes`/`git pushx` do not match.
    push_re='(^|[;&|(]|&&|\|\|)[[:space:]]*((then|do|else|\{)[[:space:]]+)*git([[:space:]]+-[^[:space:]]+([[:space:]]+[^[:space:]-][^[:space:]]*)?)*[[:space:]]+push([^[:alnum:]_-]|$)'
    printf '%s' "$cmd" | grep -qE "$push_re" || emit_allow
    ;;
  *)
    emit_allow ;;
esac

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}" 2>/dev/null || emit_allow
command -v uv >/dev/null 2>&1 || emit_allow
git rev-parse --git-dir >/dev/null 2>&1 || emit_allow

# This branch's own .py files: staged + unstaged + committed-vs-merge-base.
# --diff-filter=ACMR drops deletions, so no path handed to ruff is missing.
{
  git diff --name-only --cached --diff-filter=ACMR 2>/dev/null
  git diff --name-only --diff-filter=ACMR 2>/dev/null
  if git rev-parse --verify -q origin/main >/dev/null 2>&1; then
    git diff --name-only --diff-filter=ACMR origin/main...HEAD 2>/dev/null
  fi
} > /tmp/.ruff_gate_all.$$ 2>/dev/null || { rm -f /tmp/.ruff_gate_all.$$; emit_allow; }

mapfile -t files < <(sort -u /tmp/.ruff_gate_all.$$ 2>/dev/null | grep -E '\.py$' 2>/dev/null)
rm -f /tmp/.ruff_gate_all.$$

# Keep only paths that still exist on disk (a rename's old side, a race).
existing=()
for f in "${files[@]:-}"; do [ -n "$f" ] && [ -f "$f" ] && existing+=("$f"); done
[ ${#existing[@]} -gt 0 ] || emit_allow

fmt_out=$(uv run ruff format --check --force-exclude -- "${existing[@]}" 2>&1); fmt_rc=$?
chk_out=$(uv run ruff check --force-exclude -- "${existing[@]}" 2>&1); chk_rc=$?

# Refuse ONLY on a genuine violation (rc 1). rc 0 = clean; rc 2 = ruff error.
[ "$fmt_rc" = "1" ] || [ "$chk_rc" = "1" ] || emit_allow

reason="PUSH BLOCKED — ruff gate (.claude/hooks/ruff-prepush-gate.sh).

The Ruff lint + format check job is one of R-AE's six required checks, so
pushing this would turn CI red for every lane behind you, not just this PR.
Scope is THIS BRANCH's changed Python files only, so these are yours to fix."

if [ "$fmt_rc" = "1" ]; then
  reason="${reason}

--- uv run ruff format --check (FAILED) ---
${fmt_out}

Fix:  uv run ruff format --force-exclude -- <files above>
Then verify NO semantic change. \`git diff -w\` is NOT sufficient: -w ignores
whitespace within a line but not ruff's inserted newlines, magic trailing
commas or grouping parens. Compare parsed source instead —
  ast.dump(ast.parse(before)) == ast.dump(ast.parse(after))"
fi

if [ "$chk_rc" = "1" ]; then
  reason="${reason}

--- uv run ruff check (FAILED) ---
${chk_out}

Fix the lint findings, or \`uv run ruff check --fix --force-exclude -- <files>\`
for the safe autofixes. Never enable --unsafe-fixes to satisfy this gate."
fi

reason="${reason}

This gate is check-only and never edits your tree (rule 27 [R-PUSH]).
If it is wrong, the escape hatch is to disable the hook deliberately and say so
in the PR — do not work around it by reformatting files you do not own."

jq -n --arg r "$reason" '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: $r
  }
}'
exit 0
