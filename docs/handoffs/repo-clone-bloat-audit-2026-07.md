# Repo clone-bloat audit & remediation — 2026-07-22

**Session:** standalone repo/git-hygiene infrastructure (Opus). Branch
`claude/repo-clone-bloat-fix-3rvic7`.

**TL;DR.** The repository is **11.49 GiB** on GitHub (packed, all history). That
is why fresh full-history clones hang and `git fetch` disconnects through the
proxy — a container that tries to pull ~11.5 GB over the relay never finishes
(the auto-clone in this very session was found **stuck at 6.1 GB with an empty
working tree**). Almost none of the weight is code: the blobless commit+tree
graph is only **10.73 MiB**. The other ~99.9 % is **file-blob content** — mostly
gigabytes of immutable binary reference data under `data/raw/` (legit-keep), plus
a real layer of **history churn from 443 web-UI "Add files via upload" commits**
that dropped files in the wrong place (repo root, `inputs/raw-data/`) and later
relocated/deleted them, orphaning the blobs in every clone's pack.

**The fix that actually unsticks the loop is the partial/shallow clone recipe
(§3) — it needs no history change.** Untracking clutter (§2, done) stops
re-growth but reclaims only working-tree bytes, not pack size. Shrinking the pack
is a history rewrite (§4) and is **owner-gated** — diagnosed and costed below, not
executed.

---

## 1. Diagnosis

### 1a. Headline numbers (authoritative)

| Metric | Value | Source |
|---|---|---|
| **Repo size on GitHub (packed, all history)** | **11.49 GiB** (12,044,045 KB) | GitHub API `size` |
| Blobless clone metadata (commits + trees only) | 10.73 MiB / 48,717 objects | `git count-objects -vH` |
| Total commits | 9,123 | `git rev-list --count --all` |
| **"Add files via upload" web-UI commits** | **443** | commit-message scan |
| Current tracked files (HEAD) | 9,728 | `git ls-tree -r HEAD` |

The 10.73 MiB-vs-11.49 GiB gap is the whole story: **the repo is not
code-heavy, it is blob-heavy.** ~99.9 % of the pack is file content, current +
historical.

### 1b. Current-tree composition (HEAD)

By file type (current tree): 2,917 `.parquet`, 1,660 `.json`, 1,436 `.py`,
**1,135 `.xlsx`**, 871 `.md`, 657 `.csv`, **316 `.zip`**, 130 `.yaml`, 23
`.pdf`, 60 `.gz`. The heavy binaries are overwhelmingly under **`data/raw/`**
(4,906 files: all 316 zip, 2,574 parquet, 1,135 xlsx). A 1,132-blob sample
(11.6 % of HEAD, 0.887 GiB) is essentially 100 % `data/raw`; the biggest current
files are all immutable source:

```
 29.25 MiB  data/raw/caiso-curtailment/productionandcurtailmentsdata_2018.xlsx
 22.81 MiB  data/raw/NYISO/nyiso load reports 3.zip
 21.85 MiB  data/raw/caiso-curtailment/productionandcurtailmentsdata_2023.xlsx
 …(7 more CAISO curtailment xlsx, 20–22 MiB each)…
 13.76 MiB  data/raw/NYISO/NYISO-2025-SOM-Report__5-19-2026-final.pdf
 10.95 MiB  data/raw/PJM-AS/reserve_market_results_2025.parquet
```

**Estimated current-tree total ≈ 6–8 GiB**, dominated by `data/raw` immutable
binary source. (Estimate, not exact: measuring it precisely means fetching every
current blob, which re-triggers the clone hang and fills the session disk — so it
was deliberately not completed. The 11.49 GiB total is exact.)

### 1c. History bloat — the 443 web-UI upload commits

The owner's read is confirmed. The 443 `Add files via upload` commits touched
2,336 paths, rolled up:

| Destination | Path-touches | In HEAD now? | Verdict |
|---|---|---|---|
| `data/raw/…` | 2,108 | mostly yes | legit source (just uploaded via web UI) |
| **`inputs/raw-data/…`** | **187** | **0 (deleted)** | **orphaned in history** — pre-W1 path, relocated into `data/raw/`, `/inputs/` now gitignored |
| root-level `*.zip` | 22 distinct | **0 (deleted)** | **orphaned in history** — CAISO DAM/RTM LMP group zips uploaded to repo root (incl. `… 2.zip` duplicates), now `/*.zip`-ignored |
| `data/reference/…` | 19 | yes | legit |

`inputs/` was touched by **225 commits total** and is entirely deleted from HEAD.
Web-UI "Add files via upload" replaces rather than moves, so each relocation
created **new** blobs while the old ones stay reachable in history forever. This
is the churn layer on top of the immutable-source baseline.

Good news, confirmed by history scan: the truly-huge gitignored corpora
(`caiso-public-bids` ~0.5–0.9 GB, `pjm-energy-offers`, `NEISO-AS/da-energy-offers`
~1.4 GB, GHCN caches, NYISO damlbmp zips) were **never bulk-committed** — each
appears in exactly one commit (the README). That discipline held; they are *not*
in the pack.

**Estimated history-only (orphaned) bloat ≈ 3.5–5.5 GiB** = total (11.49) −
current-tree (~6–8), i.e. deleted `inputs/` + root zips + superseded churn of
calibration parquet and dashboard payloads.

### 1d. Keep / removable / regenerable classification

| Class | What | Size | Action |
|---|---|---|---|
| **(i) LEGIT-KEEP** | `data/raw/**` immutable source (xlsx/parquet/zip/pdf/csv) | ~6–8 GiB current | **Never touch** (task constraint + rule 13) |
| **(i) LEGIT-KEEP** | `results/calibration/<name>/` slim keeper bundles (meta/metrics/attestation/SUMMARY + sidecars) | small | Keep — dashboard deliverables (rule 15) |
| **(i) LEGIT-KEEP** | `frontend/data/backcast/registry/<id>.json` + `runs/<id>.js` | 65 MiB dir | Keep — committed sidecars (rule 15) |
| **(ii) REMOVABLE-NOW** | `scripts/_rule27_push_staging/` — 81 base64 tarball chunks (content landed on main, superseded) | 0.36 MiB (×30 history versions) | **Removed** (§2) |
| **(ii) REMOVABLE-NOW** | `tmp_bin_probe.bin` — 27-byte stray binary probe at root | 27 B | **Removed** (§2) |
| **(iii) REGENERABLE** | `frontend/data/backcast/{manifest,benchmark,completeness}.js` | part of 65 MiB | Rebuilt by Pages deploy; **kept** by policy (§6 preview fallback) — untracking is an owner option, not done here |
| **(iii) REGENERABLE** | `results/calibration/*/*.parquet` tracked despite `.gitignore` §8 (predate the rule) | 313 files | **Owner-review cleanup** (see §4) — not swept now (needs care to not touch a keeper) |
| **flag only** | `patches/pjm-m1-code.patch` (+README), `docs/handoffs/*.patch` — unapplied patches | ~20 KB | Left in place; remove only if owner confirms superseded |
| **flag only** | `scope2-lce-portfolio/` — a coherent sub-project (own `src/`, `tests/`, `data/`, `results/`, `pyproject.toml`), not referenced by CLAUDE.md | 194 files | Owner review — is it in scope for this repo? |

---

## 2. Stop the bleed — DONE (forward-only, no history rewrite)

Three commits on `claude/repo-clone-bloat-fix-3rvic7` (pushed via the GitHub
API — `git push` 413s here):

1. **Removed `scripts/_rule27_push_staging/`** (81 files) — the base64-chunked
   `rule27-bigfiles.tar.gz` relay. Verified safe: the 5 staged source files
   (`run_calibration_full.py`, `run_calibration.py`, `runner.py`,
   `backcast_config.py`, the orchestrator-unification plan) were assembled onto
   main and have since grown past the staged versions (current line counts
   9,578 > 9,166; 4,631 > 4,326; 2,470 > 2,292; 2,001 > 1,764), and commit
   `8d5a1cb4 docs: archive merged staging files` confirms the merge.
2. **Removed `tmp_bin_probe.bin`** — 27-byte binary test probe at repo root.
3. **Hardened `.gitignore` (new §11)** so the clutter can't re-enter the pack:
   `_*_push_staging/`, `*.tar.gz.b64.part*.txt`, and stray `*.bin` root probes.
   Byte-verified after push (blob SHA matches local `git hash-object`).

**Important:** `git rm --cached` / file deletion shrinks the working tree and
stops growth **but does not shrink the pack/history** — every removed blob is
still in every existing clone. Reclaiming pack size is §4.

---

## 3. Make fast clone the standard (this is what unsticks the loop)

No history change; every future session avoids the hang by **never doing a
full-history clone or `git fetch` over full history**. The recipe (also in
`docs/handoffs/fast-clone.md` and proposed for CLAUDE.md's remote-environment
section):

```bash
ORIGIN=$(git -C "$PWD" remote get-url origin 2>/dev/null || echo \
  "https://github.com/jessicacohen554-cyber/market-simulator.git")

# Blobless partial clone: full commit/tree graph, NO file blobs.
# Fast even on an 11.5 GB repo — blobs are fetched lazily only when checked out.
git clone --filter=blob:none --no-checkout "$ORIGIN" /tmp/mktsim && cd /tmp/mktsim

# If even that hangs, depth-1 blobless + rely on the GitHub API for the rest:
git clone --depth 1 --filter=blob:none "$ORIGIN" /tmp/mktsim-shallow
```

Rules for working inside a partial clone (learned the hard way this session):

- **Don't `git checkout` the whole tree** and **don't `git fetch origin <branch>`
  over full history** — both lazily fetch every blob and re-hang. Check out only
  what you need (`git sparse-checkout set <dir>`), or read files via the GitHub
  API / MCP `get_file_contents`.
- **`git rev-list --objects --all` hangs** in a blobless clone unless you pass
  **`--missing=allow-any`** (otherwise it tries to fetch promisor blobs).
- **Push only via `mcp__github__push_files` / `create_or_update_file` /
  `delete_file`** — `git push` 413s on this relay regardless of pack size.
- Get repo/file sizes from the **GitHub API** (`search_repositories` → `size`,
  `get_file_contents` → per-file `size`), not by fetching blobs.

**Proposed setup-hook change (NOT merged — CLAUDE.md forbids editing
workflows/setup without owner sign-off):** if the environment's initial-clone
step is configurable (the container clone hook), switch it from a full clone to
`git clone --filter=blob:none` (optionally `--depth 1`). That single change
prevents the container-start hang for every future session. Point of change: the
remote-environment clone/setup hook that provisions
`/home/user/market-simulator` at container start. **Owner to approve and wire
in** — this session did not modify any CI/setup file.

---

## 4. Owner-gated recommendation — history purge / LFS (DIAGNOSE + PROPOSE ONLY)

The pack does not shrink until history is rewritten. Two levers, both requiring
a **force-push to `main` that invalidates every existing clone and open branch**.
**Not executed. Owner decision required.**

### Option A — targeted history purge of orphaned/regenerable blobs (moderate)

Drop from *all* history the blobs that are already deleted from HEAD or are
regenerable: the push-staging tarball, the 187 `inputs/raw-data` files, the 22
root `*.zip` LMP uploads, and superseded calibration `*.parquet` / dashboard
payloads.

- **Estimated reclaim: ~3.5–5.5 GiB** → repo from 11.49 GiB to roughly **6–8 GiB**.
- **Keeps** `data/raw` current source and all keeper bundles intact.
- Exact commands (run on a full mirror, off this constrained relay):

```bash
git clone --mirror https://github.com/jessicacohen554-cyber/market-simulator.git
cd market-simulator.git
# requires git-filter-repo
git filter-repo --force \
  --path scripts/_rule27_push_staging/ \
  --path inputs/ \
  --path-glob '*.tar.gz.b64.part*.txt' \
  --path-glob '/*.zip' \
  --path tmp_bin_probe.bin \
  --invert-paths
git reflog expire --expire=now --all && git gc --prune=now --aggressive
# then, coordinated force-push (see blast radius):
git push --force --mirror
```

### Option B — migrate `data/raw` binaries to Git LFS (large reclaim, larger effort)

Rewrite history so `data/raw/**.{xlsx,parquet,zip,pdf,csv,gz}` live in LFS
pointers instead of pack blobs.

- **Estimated reclaim: the git pack drops to <1 GiB** (source only); the binary
  bytes move to LFS storage (billed separately, but not in every clone).
- Bigger change: needs `.gitattributes`, an LFS-enabled remote, and every
  collaborator/session to have `git-lfs` installed. `git clone --filter=blob:none`
  already gives most of the clone-speed benefit **without** LFS, so LFS is only
  worth it if the owner wants a genuinely small git repo.

```bash
git lfs migrate import --everything \
  --include='data/raw/**/*.{xlsx,parquet,zip,pdf,csv,gz}'
git push --force --all && git push --force --tags
```

### Blast radius (identical for A and B)

- **Force-push to `main` rewrites every commit SHA.** Every existing clone
  (including stuck container clones) and **all open branches** must be re-based
  onto the new history or re-cloned. Open PR branches at time of writing:
  `claude/ff-wave-manager-standing-e90gfj`,
  `claude/holdout-backcast-readiness-x8jf60`,
  `claude/orchestrator-unification-refactor-iyc472`,
  `claude/transmission-interchange-refactor-93bbm6`, plus this one.
- CI/Pages deploy re-runs against rewritten history.
- Must be done off this relay (needs a working `git push --force --mirror`).
- Coordinate a quiet window (no in-flight sessions) and re-base all live branches
  immediately after.

> ### ☐ OWNER DECISION
> - **☐ Do nothing further** — keep §2 + §3 (fast-clone standard already fixes
>   the hang; repo stays 11.5 GB). *Lowest risk, recommended if the clone hang is
>   the only pain.*
> - **☐ Option A** (targeted purge, ~6–8 GiB, moderate risk) — schedule a
>   coordinated force-push window.
> - **☐ Option B** (LFS migration, <1 GiB git, higher effort) — only if a small
>   git repo is explicitly wanted.
> - **☐ Approve the setup-hook switch to `--filter=blob:none`** (§3) so
>   container starts stop hanging.
> - **☐ Approve/decline the follow-up untracking sweeps** — `results/calibration/*/*.parquet`
>   that predate `.gitignore` §8 (313 files); the regenerable
>   `frontend/data/backcast/*.js`; `patches/`; `scope2-lce-portfolio/`.
