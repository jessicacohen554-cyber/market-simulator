# Fast clone — avoiding the "cloning loop"

**Problem.** A **full-history clone** or a full `git fetch` transfers the whole
pack, which through this environment's egress proxy is slow — historically it
frequently **stalled** outright ("*Cloning the git_repository source took
longer than the allowed time and was stopped*", the "cloning loop"), because
the pack was 7.44 GiB, ≈97% of it immutable `data/raw/` source data (see
`docs/handoffs/repo-clone-bloat-audit-2026-07.md`).

**Re-measured 2026-08-16**, after the BLOAT-B tip prunes AND the 2026-08-16
history rewrite (`cleanup-large-blobs.yml` run 31955205445, owner decision —
`docs/FINDING-history-rewrite-2026-08-16.md`):

| | 2026-08-13 (pre) | 2026-08-16 (post) |
|---|---:|---:|
| Pack a clone transfers (heads+tags) | 7.44 GiB | **5.46 GiB** |
| Full bare clone through the proxy | stalls | **162 s** |
| Blobs live at the tip of `main` (packed) | 7.37 GiB (10,642) | **4.13 GiB (8,777)** |
| History-only blob weight | 82.3 MB (1.1%) | ~1.32 GiB (~24%) |

The tip shrank because BLOAT-B untracked corpus payloads; the pack shrank
because the rewrite then stripped the superseded blobs those prunes created.
A full clone now completes — but takes minutes and 5.5 GiB where the partial
recipe below takes seconds and ~300 MB, so the partial clone stays the
standard. (Do NOT measure pack size with `git clone --mirror` against GitHub:
`refs/pull/*` still pins the pre-rewrite objects and transfers ~20 GiB.)
The former standing NO-GO on rewriting for size
(`docs/FINDING-rewrite-prep-2026-08-11.md` §8) was superseded by the owner's
2026-08-16 decision — see the history-rewrite section below.

**The fix is the clone *method*.** The commit/tree graph is tiny; only the file
*blobs* are heavy, and you rarely need all of them. A **blobless partial clone**
downloads the whole graph instantly and fetches file blobs only when a path is
actually checked out.

## Recipe — start every session with a partial clone

```bash
ORIGIN=https://github.com/jessicacohen554-cyber/market-simulator

# Blobless partial clone + the whole codebase, WITHOUT data/raw.
git clone --filter=blob:none --sparse --no-checkout "$ORIGIN" market-simulator
cd market-simulator
git sparse-checkout set --no-cone '/*' '!/data/raw/'
git checkout main
```

Measured end to end (2026-08-13; clone + checkout re-measured 2026-08-16
post-rewrite — essentially unchanged: 3.5 s / 13.7 MB, then 12.2 s / 306 MB):

| Step | Time | Cumulative |
|---|---:|---:|
| `git clone --filter=blob:none --no-checkout` | **3 s** | 15 MB |
| + checkout of everything except `data/raw` | **19 s** | **311 MB** |
| + `hydrate_data.py --profile miso` (1,492 files) | **157 s** | 2.2 GB |

That is a complete, working MISO calibration environment — all 2,261 Python
files, tests, docs, dashboard — in about **3 minutes**, against a full clone
that historically did not finish (post-rewrite: ~2.7 min for the bare clone
alone, before any checkout).

**A shallow clone is NOT the fix here, despite what the timeout message
suggests.** `--depth 1` still transfers the entire tip tree, which *is* the 7.37
GiB. Shallow clones help repos bloated by many commits; this one is bloated by a
single enormous tip. Use `--filter=blob:none`. (`--depth 1` may be *added* for
speed, but it reproduces the shallow-clone limitation that cited SHAs no longer
resolve — see `docs/FINDING-rewrite-prep-2026-08-11.md` §1.)

## Then hydrate only the data this session needs

`scripts/hydrate_data.py` pulls in `data/raw` subtrees on demand, per
`configs/data-profiles.yaml`. Attribution is derived from the tree at HEAD, so
new subtrees are picked up with no table to maintain.

```bash
python3 scripts/hydrate_data.py --list            # profiles and coverage
python3 scripts/hydrate_data.py --profile miso    # shared + MISO only
python3 scripts/hydrate_data.py --profile code    # drop data/raw again
```

| Profile | Files | Packed | Use |
|---|---:|---:|---|
| `code` | 0 | 0 | docs, governance, dashboard, code review, CI — anything that does not solve |
| `shared` | 1,241 | ~1.2 GB | cross-ISO data work (EIA, CAMPD, eGRID, fuel prices) |
| `miso` / `pjm` / `neiso` | ~1.3–1.4 k | ~1.3 GB | that ISO's calibration/forecast lane |
| `nyiso` | 1,442 | ~1.4 GB | ” |
| `caiso` | 2,610 | ~2.2 GB | ” |
| `ercot` | 2,718 | ~5.9 GB | ERCOT is 4.7 GB of `data/raw` on its own |
| `all` | 4,718 | ~7.2 GB | cross-ISO solves only |

Budget ~1.5× on disk (files check out uncompressed): `miso` is 1.3 GB packed,
1.9 GB on disk.

### Why hydration is chunked — three measured traps

Each cost a stalled run before it was understood; all three are guarded in the
script, and none is obvious from the git docs:

1. **Never read a blob you do not intend to download.** In a partial clone *any*
   command that resolves a missing blob silently fetches it. An innocuous
   `git cat-file --batch-check='%(objectsize:disk)'` over `data/raw` therefore
   downloads all 7.4 GB — the exact outcome the partial clone exists to prevent.
   The script reads **trees only** (`ls-tree` for paths,
   `cat-file --batch-all-objects` for sizes of what is already local) and runs
   every read-side git call under `GIT_NO_LAZY_FETCH=1` so a regression fails
   loudly instead of quietly costing 7 GB.
2. **Never follow `sparse-checkout` with `git checkout -- .`.** A pathspec
   checkout materializes skip-worktree entries, force-fetching blobs *outside*
   the profile — `.git` grew to 2.6 GB while hydrating a 1.3 GB profile.
3. **Apply one pattern per call.** Handing git ~115 non-cone patterns in a single
   `sparse-checkout set` degenerates into per-file fetches and did not finish in
   10 minutes; the same data applied a directory at a time batches into one fetch
   per call (29 MB in 2 s, 666 MB in 23 s).

Cone mode (`--cone`) is *not* usable here: it cannot express "the loose files at
`data/raw/` plus one ISO's subdirectory but not its siblings" — listing
`data/raw` in cone mode pulls everything under it.

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

## Pushing — choose the transport by PACK size

**Superseded 2026-07-25.** This doc previously said "never `git push` (it 413s)".
That is no longer the rule: the remote rejects large *packs*, not large *blobs*,
and a 434,784-byte single-blob dashboard commit pushed over `git push` with no
413 (PR #2878). `CLAUDE.md` (Git & Pushing) is authoritative:

- **`git push` is permitted** when the pack is small — start from a freshly
  fetched `origin/main` so the pack carries only your own objects. It is the
  only transport that can carry a dashboard run payload
  (`frontend/data/backcast/runs/<id>.js`, ~400 KB–1 MB), which exceeds
  `push_files`' ~457 KB payload cap. It is **not** licensed for a full bundle
  directory (~120 MB of parquet) or a divergent branch.
- **`mcp__github__push_files`** stays preferred for small multi-file commits —
  atomic, server-side, no pack negotiation at all.

A partial clone does not change this: pushes send only your new objects.

## Handoff prompts declare their data profile

**Every handoff prompt that opens a session states the profile that session
needs**, on its own line near the top, so the session hydrates once and does not
discover a missing subtree mid-solve:

```
DATA PROFILE: miso     # scripts/hydrate_data.py --profile miso
```

Choosing one:

- **`code`** — the default, and correct for most sessions. Docs, governance,
  dashboard/frontend, code review, refactors, CI, matrix updates. If the lane
  never runs `run_calibration_full.py`, it does not need `data/raw`.
- **`<iso>`** — a calibration or forecast lane for exactly one ISO. This is the
  common solving case; per rule 12 `[R-PARALLEL]` concurrent invocations are
  per-ISO anyway, so each session hydrates only its own.
- **`shared`** — cross-ISO data-contract, curation or schema work.
- **`all`** — genuinely cross-ISO solves only. Say why in the prompt.

A prompt that omits the line is read as `code`. A session that finds it needs
more can widen at any time (`--profile ercot`); hydration is incremental, so
already-fetched blobs are not re-fetched.

**PJM replay lanes: `--profile pjm` is NOT sufficient on its own** (audit
2026-08 gap row B2; measured by DEBUG-B,
`docs/FINDING-debug-b-pjm-input-clock-2026-08-15.md` §8). A fresh-clone PJM
keeper re-solve needs two inputs no profile can fetch, both gitignored:
(1) the derived `data/clean/` tree — `pjm_measured_interface_limits` raises
rather than no-ops, so budget the `scripts/regenerate_clean.py` rebuild
(~2 h wall on the 2026-08 container class); and (2) the licensed
`data/raw/pjm-da-virtuals/` feed — `pjm_da_virtual_bids` likewise refuses to
no-op, so budget the live DataMiner fetch
(`scripts/data/fetch_pjm_da_virtuals.py --years 2023 2024 2025 --feeds
hrl_da_incs_decs`, 36 monthly files; intermittent 502s through the egress
proxy are auto-resumed but make the run non-hermetic). Charter authors for
any rule-15 same-session-registration PJM lane must schedule both — that is
a material multi-hour scheduling fact, not a footnote.

## The history-rewrite action — it RAN on 2026-08-16

`.github/workflows/cleanup-large-blobs.yml` (`workflow_dispatch`-only) strips
*superseded* blob versions under `data/raw/` and `results/calibration/`. On
**2026-08-16 the owner executed it for real** (run 31955205445, superseding the
Addendum AQ NO-GO): 7,254 superseded blobs / 7,373.4 MiB stripped, integrity
verify passed (strict `main` manifest byte-identical; all cited load-bearing
commits survived), force-push landed. Full record, citation-map translator and
recovery-contract fallout: `docs/FINDING-history-rewrite-2026-08-16.md`.

Consequences for clones and citations:

- The pack numbers at the top of this doc are the post-rewrite reality; a
  fresh clone is mandatory after a rewrite (a pre-rewrite clone's history no
  longer matches the remote).
- **Pre-2026-08-16 commit-sha citations are dead in a fresh clone** (926 of
  929 formerly-resolving tokens; the 104 load-bearing ones translate via
  `docs/governance/citation-commit-map.txt`), and a short prefix can even
  resolve to the WRONG commit — check citation dates before trusting one.
- The corpus conversions' restore-from-pin recovery routes are gone; each
  corpus README now states its honest re-fetch/retention status.

Any **future** run remains owner-gated (`HISTORY_REWRITE_PAT` +
`REWRITE-HISTORY` confirm phrase) and must archive `citation-commit-map.txt`
and the full filter-repo commit-map as workflow artifacts before pushing —
this run's full commit-map was lost with the runner (finding §7).

The durable fix for clone time remains the partial clone above. The
*structural* fix — untracking `data/raw` going forward so the tip itself stops
growing — remains an owner decision with real reproducibility consequences,
and is **not** implemented.

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
