# FF-2A integration branch state (2026-07-18) — DO NOT MERGE YET

This branch is mid-way through the rule-27 append-chunk protocol for the
FF-2A core-file integration. **`src/market_sim/model/capacity.py` is an
incomplete prefix (lines 1–2295 of 4,230, every chunk byte-verified against
the locally tested tree)** — merging now would land a truncated core file
(the file-integrity-guard will also flag it).

## Why it is stuck

The integrated files exist complete and test-green in the session workspace
(local commits; `tests/test_entry_stack_ff2a.py` 8/8, all three FF-2A probe
legs re-solved and reproduced bit-identically). But every byte-exact push
channel is closed in this environment:

- `git push`: rejected (HTTP 413 on packs — standing CLAUDE.md prohibition).
- git Data API (`POST /git/blobs`) and contents API (`PUT /contents/...`):
  HTTP 403 — the egress proxy blocks GitHub API writes for session tokens
  ("An org admin must connect the Claude GitHub App for this organization").
- MCP `push_files`: works, but file content transits the model response,
  whose output ceiling is below the single-call size of
  `capacity.py` (202 KB), `docs/parameter-citations.md` (213 KB), and
  `src/market_sim/config/scenarios.py` (509 KB). The append-chunk protocol
  advanced `capacity.py` to line 2,295 but the final call must carry the
  whole file and cannot fit.

## What is already correct on main / this branch

- `src/market_sim/runner.py`: fully integrated, blob `76268af7` verified,
  merged to main via PR #2474.
- `src/market_sim/config/entry_config.py`, `data/build_throughput.py`,
  `tests/test_entry_stack_ff2a.py`, `scripts/run_capacity_hindcast.py`:
  already on main (pushed whole by the original FF-2A session).

## Exact bytes to finish with (verified local blobs)

| file | git blob SHA | lines |
|---|---|---|
| `src/market_sim/model/capacity.py` | `917195ee51a76fdd651da7fc161aaf722241eb8b` | 4,230 |
| `src/market_sim/config/scenarios.py` | `b923d3918bbe6a65c6a51a904fee0387b0af1b73` | 7,623 |
| `docs/parameter-citations.md` | `466f4311b7cf030cf36a863356e22f8d6a48d591` | 1,582 |

These are exactly `origin/main`'s versions of the four files with
`docs/handoffs/ff2a-core.patch` applied (the patch is in main's history —
`git show 'b74146c:docs/handoffs/ff2a-core.patch'` — and applies cleanly to
current main for capacity/scenarios/citations; runner.py's hunks are already
merged, `git apply` skips them with `--3way` or after excluding that hunk).

## Completion paths (either works)

1. **Enable API writes for Claude sessions** (org admin connects the Claude
   GitHub App per the 403 message). The session then pushes the exact
   on-disk bytes via the git Data API with blob-SHA verification in one
   minute (`scripts/ci_api_upload.py` pattern).
2. **Apply locally** (any clone with normal push access):
   `git fetch origin main && git checkout <this branch> && git show b74146c:docs/handoffs/ff2a-core.patch | git apply --3way -` then verify the three blob SHAs above with
   `git hash-object <file>` and push. Delete `docs/handoffs/ff2a-core.patch`
   if the apply resurrects it (it must stay deleted), and delete this marker
   file.

The FF-2A probe-leg re-registration files (new meta.json / score.json /
sidecars / reports, superseding cache keys `7b3fbd09f95eb416` PJM,
`11568f0a6602a7fa` MISO, `62a1923d1b9a2c00` ERCOT) follow once the core
files land.
