# Fast clone — avoiding the cloning loop

This repository legitimately tracks **~11.7 GiB of immutable source data under `data/raw/`**
(mostly near-incompressible parquet/zip/xlsx/pdf). A normal full-history clone must transfer all of
it, which over this environment's git proxy **hangs or disconnects** ("the cloning loop"), and
`git push` **413s** on large packs. None of that is fixable by deleting files — the data is
supposed to be there (see `docs/handoffs/repo-clone-bloat-audit-2026-07.md`). The fix is to **not
download blobs you don't need.**

## The one recipe to remember

```bash
ORIGIN=$(git remote get-url origin 2>/dev/null \
  || echo "https://github.com/jessicacohen554-cyber/market-simulator.git")

# Blobless partial clone: full commit/tree graph (~10.75 MiB), NO file blobs.
# Blobs for a file download lazily the first time you actually open it.
git clone --filter=blob:none "$ORIGIN" market-simulator
```

That is instant even though the repo is 11.5 GiB, because you get the metadata now and pull only the
handful of file blobs a session actually touches. A checkout of source/docs never pulls `data/raw/`.

### If even the blobless clone hangs

```bash
# depth-1 blobless: current tree only, no history, blobs still lazy
git clone --depth 1 --filter=blob:none "$ORIGIN" market-simulator
```

…and for anything you can't get that way, **read via the GitHub API instead of fetching** — it never
touches the pack:

```bash
TOK="${GITHUB_TOKEN:-$GH_TOKEN}"; O=jessicacohen554-cyber; R=market-simulator
# every tracked path + blob size at HEAD, one call:
curl -sS -H "Authorization: Bearer $TOK" \
  "https://api.github.com/repos/$O/$R/git/trees/main?recursive=1"
# one file's contents:
curl -sS -H "Authorization: Bearer $TOK" \
  "https://api.github.com/repos/$O/$R/contents/<path>?ref=main"
```

## Hard rules for this environment

- **Never `git fetch`/`git pull` over full history** — it hangs through the proxy. Fetch a single
  branch shallow (`git fetch --depth 1 origin <branch>`) or use the API.
- **Never `git push`** — it 413s. Push via `mcp__github__push_files` (adds/updates) or, for
  deletions/bulk commits, the GitHub **Git Data API** (server-side commit, no pack negotiation).
- **Do not trust the environment's auto-clone.** It can land stale (an old HEAD) and/or leave a
  partial-transfer `garbage` pack. If `git -C . count-objects -vH` shows a multi-GB `size-pack` and a
  stale `git log -1`, start your own blobless clone in scratch and work from that.

## Analyzing the repo without a full clone (how the audit was done)

- **Object graph, no blobs:** `git clone --filter=blob:none --no-checkout …` then
  `git rev-list --objects --all --missing=allow-any` (the `--missing` flag stops it lazily fetching
  and hanging). Note this lists only *present* blob paths — with `blob:none`, use the git-tree API
  for the authoritative current-tree file list.
- **Per-object pack size, local, no decompress:** `git show-index < .git/objects/pack/*.idx`, sort by
  offset, diff consecutive offsets. `git verify-pack -v` and `git cat-file --batch-all-objects`
  both **decompress** and time out on a multi-GB pack — avoid them here.
- **Total size:** repos API `size` (KB). **Current tree sizes:** git-tree API `?recursive=1`.

## Proposed setup-hook change (NOT merged — needs owner sign-off)

CLAUDE.md forbids editing workflows/setup without owner approval, so this is a proposal only.

Wherever the environment performs its **initial clone** (the container bootstrap / setup step that
produces `/home/user/market-simulator`), switch it to a partial clone:

```diff
- git clone "$ORIGIN" /home/user/market-simulator
+ git clone --filter=blob:none "$ORIGIN" /home/user/market-simulator
```

Optional, to also skip checking out the big data tree until a session asks for it (sessions that need
`data/raw/` run `git sparse-checkout disable` or add the path):

```bash
git clone --filter=blob:none --sparse "$ORIGIN" /home/user/market-simulator
cd /home/user/market-simulator
git sparse-checkout set --no-cone '/*' ':!/data/raw'   # everything except data/raw
```

This is a pure clone-time change — it does **not** rewrite history, change any tracked content, or
affect the Pages deploy (which already does its own blobless sparse checkout of `frontend/`+`scripts/`
only). Approve it and it lands in a follow-up commit alongside the location/diff for the actual
bootstrap file.

## Suggested CLAUDE.md addition (proposal for the remote-environment section)

> **Fast clone / cloning loop.** The repo tracks ~11.7 GiB of immutable `data/raw/` source, so a full
> clone hangs through the proxy and `git push` 413s. Always clone blobless
> (`git clone --filter=blob:none`), never full-fetch history (use `--depth 1` or the GitHub API), and
> push via `push_files` / the Git Data API. See `docs/fast-clone.md`.
