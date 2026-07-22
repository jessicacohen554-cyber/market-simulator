# Fast clone — avoiding the cloning loop

**Why this exists.** This repo is ~11.5 GB packed (mostly immutable binary
reference data under `data/raw/`; see
`docs/handoffs/repo-clone-bloat-audit-2026-07.md`). A full-history clone over the
session relay is slow and frequently **hangs mid-clone** ("the cloning loop"), and
`git fetch` over full history disconnects. Never wait on the container's auto
full-clone. Bootstrap your own **partial** clone instead.

## The recipe (do this first, every session that needs git history)

```bash
ORIGIN=$(git -C "$PWD" remote get-url origin 2>/dev/null || echo \
  "https://github.com/jessicacohen554-cyber/market-simulator.git")

# Blobless partial clone: full commit/tree graph, NO file blobs.
# Fast even on this repo — blobs are fetched lazily only when you check them out.
git clone --filter=blob:none --no-checkout "$ORIGIN" /tmp/mktsim && cd /tmp/mktsim

# Fallback if even that hangs: depth-1 blobless, use the GitHub API for the rest.
git clone --depth 1 --filter=blob:none "$ORIGIN" /tmp/mktsim-shallow
```

## Working inside a partial clone — do / don't

- **DON'T `git checkout` the whole tree**, and **DON'T `git fetch origin <branch>`
  over full history** — both lazily pull every blob and re-hang. Instead check out
  only what you need: `git sparse-checkout set <dir>` then `git checkout`, or read
  files through the GitHub API / MCP `get_file_contents`.
- **`git rev-list --objects --all` hangs** unless you add **`--missing=allow-any`**
  (otherwise it tries to fetch missing promisor blobs).
- **`git ls-tree -r HEAD`** (names) is free — trees are local. **`git ls-tree -r -l`**
  (sizes) is NOT — it fetches each blob; use the GitHub API for sizes instead.
- **Get sizes from the API, not blobs:** repo size via `search_repositories` →
  `size` (KB); per-file sizes via `get_file_contents` on a directory.

## Pushing (always API, never `git push`)

`git push` returns **HTTP 413** on this relay regardless of pack size — retries
just re-fail. Push server-side via the GitHub MCP tools:

- `mcp__github__push_files` — many files, one commit (create/update only).
- `mcp__github__create_or_update_file` — one file (needs its current blob SHA).
- `mcp__github__delete_file` — delete a path (also deletes a whole directory in a
  single commit).

## Proposed (owner-gated) permanent fix

If the container's initial-clone hook is configurable, switch it from a full
clone to `git clone --filter=blob:none` (optionally `--depth 1`). That stops the
container-start hang for every future session with no history rewrite. See the
audit doc §3 — this requires owner sign-off (CLAUDE.md forbids changing
setup/CI without approval).
