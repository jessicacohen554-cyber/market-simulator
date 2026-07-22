# Fast clone — avoiding the "cloning loop"

**Problem.** This repo's git pack is ~11.5 GiB (≈97% of it is immutable
`data/raw/` source data — parquet/xlsx/zip that git cannot compress further, see
`docs/handoffs/repo-clone-bloat-audit-2026-07.md`). A **full-history clone** or a
full `git fetch` has to transfer all of it, which through this environment's
egress proxy is slow and frequently **stalls** — leaving sessions on a *stale or
half-checked-out clone*. A subsequent full `git fetch` stalls the same way, and
`git push` returns **HTTP 413** (pack too large). That is the "cloning loop."

**The fix is the clone *method*, not the repo size.** The full commit/tree graph
is tiny (~11 MiB); only the file *blobs* are heavy, and you rarely need all of
them. A **blobless partial clone** downloads the whole graph instantly and fetches
individual file blobs only when you actually check them out.

## Recipe — start every session with a partial clone

```bash
ORIGIN=$(git -C "$PWD" remote get-url origin 2>/dev/null || echo \
  "https://github.com/jessicacohen554-cyber/market-simulator.git")

# Blobless partial clone: full history graph, NO file blobs until touched.
# Completes in ~2s even though the repo is 11.5 GiB.
git clone --filter=blob:none "$ORIGIN" market-simulator
cd market-simulator
# Working tree checks out on demand; blobs for files you open are fetched lazily.
```

Variants:
- **Even lighter (analysis only, no working tree):** add `--no-checkout`.
- **Only need the tip:** `git clone --depth 1 --filter=blob:none "$ORIGIN"`.
- **Only need one subtree's files present:** after a `--no-checkout` blobless
  clone, `git sparse-checkout set src scripts docs` then `git checkout` — blobs
  are fetched only for those paths, so you never pull the 11.7 GiB `data/raw/`.

## Do NOT full-fetch; use the GitHub API for reads

A full `git fetch origin` (all history, all blobs) stalls through the proxy.
Instead:

- **Fast-forward to real `main` without pulling blobs:**
  ```bash
  git fetch --filter=blob:none origin main
  git checkout -B main origin/main        # or: git reset --hard origin/main
  ```
  This transfers only the commit/tree delta (small) — it does **not** hang like a
  full fetch, and it cures the "stale clone" symptom (a session that started on an
  old snapshot lands on true `origin/main`).
- **Read file contents / sizes without any clone:** hit the GitHub REST API
  (works with `$GITHUB_TOKEN`), e.g. the recursive tree with per-blob sizes:
  ```bash
  curl -sH "Authorization: Bearer $GITHUB_TOKEN" \
    "https://api.github.com/repos/jessicacohen554-cyber/market-simulator/git/trees/main?recursive=1"
  ```
  or `mcp__github__get_file_contents` for a single file/dir.

## Pushing — never `git push` (it 413s)

Push via the GitHub API only (`mcp__github__push_files` to add/update,
`mcp__github__delete_file` to remove). These commit server-side and bypass git's
pack negotiation, so they never 413 regardless of payload size. This is already
the standing rule in `CLAUDE.md` (Git & Pushing) and `docs/`.

## Proposed environment change (NOT merged — owner decision)

The initial clone is performed by the Claude-Code-on-the-web **environment**
before any repo hook runs, so no repo file controls it directly. Two levers, both
owner-gated:

1. **Environment clone setting.** If the environment supports a clone
   filter/depth, set it to `--filter=blob:none` (blobless partial) so *every*
   session starts fast. See the environment configuration docs at
   https://code.claude.com/docs/en/claude-code-on-the-web. This is the highest-
   leverage fix and needs no code change.

2. **Defensive `SessionStart` hook addition (described, not applied).** The
   existing `.claude/hooks/session-start.sh` runs *after* the clone, so it cannot
   prevent a slow initial clone — but it *can* cheaply repair a stale one. A
   proposed, reversible addition (append after `uv sync`), left for owner review:

   ```bash
   # Fast-forward a stale/partial web clone to real origin/main WITHOUT a full
   # blob fetch (a full fetch stalls through the proxy; a blobless one does not).
   if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
     git config remote.origin.promisor true 2>/dev/null || true
     git config remote.origin.partialclonefilter blob:none 2>/dev/null || true
     if git fetch --filter=blob:none --quiet origin main 2>/dev/null; then
       behind=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
       if [ "${behind:-0}" -gt 0 ]; then
         echo "session-start: fast-forwarding $behind commits to origin/main (blobless)"
         git merge --ff-only origin/main 2>/dev/null || true
       fi
     fi
   fi
   ```

   This is **not** applied in this change — it edits a hook that runs for every
   session, so it needs owner sign-off (CLAUDE.md's no-silent-infra-change rule).
   It is byte-safe to add and byte-safe to revert.
