# Repo clone-bloat audit & fast-clone standard (2026-07-22)

**Session:** standalone git-hygiene infra (Opus). **Branch:** `claude/repo-clone-bloat-fix-m4noyi`.
**Companion doc:** `docs/fast-clone.md` (the recipe that actually unsticks the cloning loop).

---

## TL;DR (lead with the numbers)

| Measure | Value | Source |
|---|---|---|
| **GitHub server-side repo size** | **11.49 GiB** (12,044,217 KB) | repos API `size` |
| **Current tracked tree** | **12.03 GiB across 9,728 files** (not truncated) | git-tree API @ `main` |
| **`data/raw/` (immutable source)** | **11.7 GiB, 4,906 files — 99.6 % of the tree** | git-tree API |
| `.parquet` files alone | 9.3 GiB, 2,917 files | git-tree API |
| History-only bloat (deleted/superseded blobs) | **modest — a few hundred MiB, not the driver** | pack analysis (below) |
| Removable clutter (staging tarball + 3 regenerable JS) | **1.0 MiB** — `.gitignore`-guarded now; physical removal is a 2-line local `git rm` / Step-4 (proxy blocks bulk delete here) | this session |

**The headline:** the repository is not bloated by junk. It is 11.5 GiB because it **legitimately
tracks 11.7 GiB of immutable market-data source** under `data/raw/` — overwhelmingly
near-incompressible binaries (parquet/zip/xlsx/pdf) uploaded over time via the GitHub web UI
("Add files via upload"). Those files are **LEGIT-KEEP** by CLAUDE.md (`data/raw/` is *"immutable
source downloads, NEVER modified in place — the single source root"*). Deleting clutter recovers
essentially nothing (~1 MiB). **The cloning loop is a data-volume problem, not a junk problem.**

**Two independent things follow, and they must not be conflated:**
1. **Fix the clone *experience* now, no history change** → make the **blobless/shallow partial
   clone** the standard (`docs/fast-clone.md`). This is what unsticks the loop. A blobless clone of
   this repo pulls **10.75 MiB** of metadata and is instant; the multi-GB blobs come down lazily
   only for files a session actually opens. **Already proven this session.**
2. **Shrink the repo on disk** → only two levers exist, **both rewrite history + force-push main**,
   both **owner-gated** (Step 4). A history purge of dead blobs recovers a few hundred MiB; a **Git
   LFS migration of `data/raw/` binaries** is the only lever that removes the ~9–11 GiB bulk from
   the git pack. **Neither is executed here — this is a diagnose-and-propose deliverable.**

---

## Step 0 — How this was measured without getting stuck

The environment's auto-clone is the exact failure the owner described: a **full, shallow-but-stale
clone** at `.git/` = **3.78 GiB pack + 1.03 GiB garbage** (an interrupted-transfer artifact),
parked at a stale HEAD (`066fb98`, PR #2341) while `main` is `a4a17c9` (PR #2766). Any `git fetch`
over that hangs through the proxy; `git push` 413s.

So all analysis ran off a **blobless partial clone** plus the **GitHub API**, never a full fetch:

```bash
git clone --filter=blob:none --no-checkout "$ORIGIN" /tmp/mktsim-blobless   # 10.75 MiB, instant
```

- **Current-tree sizes** (authoritative): `GET /repos/.../git/trees/main?recursive=1` → every path +
  blob size in one call (9,728 blobs, `truncated:false`).
- **Total server size**: `GET /repos/...` → `size` = 12,044,217 KB = 11.49 GiB.
- **Per-object pack bytes** (local, no network, no decompress): `git show-index < pack.idx`, sort by
  offset, diff consecutive offsets = each object's compressed size. `verify-pack`/`cat-file
  --batch-all-objects` both **time out** on the 3.8 GiB pack (they decompress) — `show-index` does not.

---

## Step 1 — Diagnosis

### 1a. Current tree — top offenders

Top individual files (all under `data/raw/`, all immutable source):

| Size | Path |
|---|---|
| 63.5 MiB | `data/raw/ercot/60_DAY_SCED_DISCLOSURE_..._2025_ercot86_tail_days.parquet` |
| 55.6 MiB | `data/raw/ercot/60_DAY_SCED_DISCLOSURE_..._2024_ercot74_tail_days.parquet` |
| 52.8 MiB | `data/raw/ercot/60_DAY_SCED_DISCLOSURE_..._2025_ercot75_control_days.parquet` |
| 36.7 MiB | `data/raw/ercot/60_DAY_SCED_DISCLOSURE_..._2024_ercot75_control_days.parquet` |
| 29.2 MiB | `data/raw/caiso-curtailment/productionandcurtailmentsdata_2018.xlsx` |
| 20–25 MiB ×~40 | ERCOT 60-day DAM/SCED disclosure parquets, CAISO curtailment xlsx, PJM interchange CSVs, NYISO load-report zips, egrid xlsx |

Rollup by top-level directory:

| Size | Files | Dir |
|---|---|---|
| **11,975 MiB** | 4,906 | **`data/raw/`** |
| 243 MiB | 2,094 | `results/` (calibration keeper bundles + already-gitignored scratch) |
| 67 MiB | 263 | `frontend/` (dashboard: `runs/` payloads 58.5 MiB + `bench/` 5.7 MiB, both keepers) |
| 10 MiB | 636 | `docs/` |
| 9 MiB | 1,005 | `scripts/` |
| 7 MiB | 194 | `scope2-lce-portfolio/` |
| 5 MiB | 162 | `src/` |
| 4 MiB | 340 | `tests/` |

`data/raw/` sub-families (where the 11.7 GiB lives):

| Size | Files | Sub-dir |
|---|---|---|
| 7,555 MiB | 1,839 | `data/raw/ercot/` (60-day SCED/DAM disclosures) |
| 786 MiB | 308 | `data/raw/campd-unit-level/` (CEMS) |
| 761 MiB | 213 | `data/raw/lmp-data/` |
| 599 MiB | 65 | `data/raw/ercot-AS/` |
| 272 MiB | 89 | `data/raw/zone-specific-demand/` |
| 234 MiB | 54 | `data/raw/ercot-hsl/` |
| 196 MiB | 107 | `data/raw/eia-930/` |
| 189 MiB | 45 | `data/raw/CAISO-AS/` |
| 187 MiB | 22 | `data/raw/iso-specific-transmission/` |
| … | | (CAISO outages, curtailment, NYISO/MISO SOM PDFs, PJM-AS, storage-AS, …) |

By extension: **`.parquet` 9,566 MiB / 2,917 files**, `.zip` 1,019 MiB, `.csv` 784 MiB,
`.xlsx` 575 MiB, `.gz` 146 MiB, `.pdf` 102 MiB. These barely compress, so the 11.49 GiB pack ≈ the
12.03 GiB tree.

### 1b. History bloat (deleted/superseded blobs still in the pack)

**Modest, and not the driver.** Because the current tree is near-incompressible and the server pack
(11.49 GiB) is *smaller* than the uncompressed current tree (12.03 GiB), the current tree alone
accounts for essentially the whole pack — leaving only a few hundred MiB of head-room for all
deleted/superseded history + commit/tree metadata.

Concretely, in the auto-clone's 211-commit shallow window, blobs on a path **no longer in the
current tree** total **217.6 MiB (5.7 % of a 3.79 GiB pack)** — superseded dashboard payloads
(`frontend/` 30 MiB, `results/` 37 MiB) and root-level LMP `.zip`s later relocated into
`data/raw/lmp-data/` (~150 MiB). Full-history commit/tree metadata is **10.75 MiB** (the entire
blobless clone). There is **no evidence of massive re-uploaded/superseded data** — sampled
`data/raw/` paths show **1 blob version each** (no re-upload churn).

### 1c. Classification of every offender

| Bucket | What | Size | Action |
|---|---|---|---|
| **(i) LEGIT-KEEP** | `data/raw/**` immutable source; `results/calibration/<keeper>/` slim bundles; `frontend/data/backcast/{registry,runs,bench,status,keepers}` keeper sidecars | ~11.9 GiB | **Never touch.** |
| **(ii) REMOVABLE-NOW** | `scripts/_rule27_push_staging/` — 81 base64 `*.part*.txt` chunks of `rule27-bigfiles.tar.gz`, orphaned push-scaffolding | 0.365 MiB | **`.gitignore`-guarded this PR**; physical removal → local `git rm` / Step-4 (verified safe — see box) |
| **(iii) REGENERABLE** | `frontend/data/backcast/manifest.js` / `benchmark.js` / `completeness.js` — assembled by the Deploy-Pages job from (i)'s sidecars | 0.63 MiB | **`.gitignore`-guarded this PR**; physical removal → local `git rm` / Step-4 |
| **(?) OWNER'S CALL** | `patches/pjm-m1-code.patch` (+README, 18 KB); `docs/handoffs/pjm-m3-gas-bridge.patch` (39 KB, unapplied); ~15 other `.patch` handoff artifacts (KB each) | ~0.2 MiB | **Left in place** — flagged, not removed (see below) |

> **Safety check performed before untracking `_rule27_push_staging/`.** Its `MANIFEST.md` warns the
> five staged source files (`run_calibration_full.py`, `run_calibration.py`, `runner.py`,
> `pipeline/backcast_config.py`, `orchestrator-unification-plan-2026-07.md`) *"are still at their
> pre-lane state until assembled."* I verified against `main`: all five are present at **0.94–1.13×**
> their MANIFEST target sizes — i.e. assembled long ago and since evolved. The blob SHAs differ from
> the MANIFEST (post-assembly edits), but the *sizes* confirm the work is on `main`. The chunks are
> therefore orphaned clutter, and no code references the directory. **Safe to untrack.**

> **Why untracking the 3 dashboard JS is safe.** `deploy-pages.yml` runs with `permissions:
> contents: read` and stages `manifest.js`/`benchmark.js`/`completeness.js` into the `_site`
> artifact via `build_manifest.py --site-dir _site` — it **never commits them back to `main`**. The
> LIVE site rebuilds them from the tracked `registry/`+`bench/` sidecars every deploy. The tracked
> copies were pure derived-file churn (`benchmark.js` ≈ 0.6 MB, re-written on every dashboard change)
> and a concurrent-session merge hazard. A local `file://` preview refreshes them with
> `python3 scripts/build_manifest.py`. (This corrects a now-stale `.gitignore` comment that claimed
> the deploy is "the single writer, pushing with GITHUB_TOKEN" — the current simplified deploy has
> `contents: read` and cannot.)

**Patches (owner's call — deliberately NOT removed):** they are small (~0.2 MiB total) and are
handoff artifacts, not clutter. `docs/handoffs/pjm-m3-gas-bridge.patch` is an unapplied 836-line
patch; per the task it stays unless you want it rebased/dropped. Say the word and a follow-up commit
removes any you name.

---

## Step 2 — Stop the bleed (this PR — forward-only, reversible, no history rewrite)

Committed on `claude/repo-clone-bloat-fix-m4noyi`:

1. **Added two per-directory `.gitignore` guards** so `scripts/_rule27_push_staging/` and the three
   regenerable dashboard JS files can never (re-)enter tracking — the achievable **stop-the-bleed**
   (blocks recurrence and makes the removal stick once done):
   - `scripts/.gitignore` → `*_push_staging/` (the push-scaffolding convention)
   - `frontend/data/backcast/.gitignore` → `manifest.js`, `benchmark.js`, `completeness.js`

   *Why per-directory and not the root `.gitignore`:* the repo already uses per-dir `.gitignore`s as a
   convention (7 exist, incl. under `data/raw/`), and CLAUDE.md **rule 27** forbids re-transmitting an
   existing ≥300-line file through a model response — the root `.gitignore` is 327 lines. Two tiny new
   files carry zero truncation risk and are byte-verifiable. (The now-stale "These ARE committed" note
   about the dashboard JS still living in the *root* `.gitignore` should be corrected during the
   Step-4 local work, where a working `git` makes root edits safe.)

**Environment constraint — why the *physical* untracking is not in this commit.** Removing the
already-tracked copies means deleting 84 files (81 staging chunks + 3 JS) from the tree. In this
session there is **no way to do that in one commit**: `push_files` only adds/updates (no delete), the
raw GitHub Git Data API is **write-blocked by the agent proxy** (`403: "Write access to this GitHub
API path is not permitted through this proxy"`), and `delete_file` is **one-commit-per-file** (84
commits — itself a hygiene regression). A tip-deletion also **would not shrink the pack** (the blobs
stay in history). So the physical removal is handed to the owner two ways, both listed in the
decision box:

- **Forward-only, no history rewrite** — run locally in any environment with working `git push`:
  ```bash
  git rm -r scripts/_rule27_push_staging/
  git rm --cached frontend/data/backcast/manifest.js \
                  frontend/data/backcast/benchmark.js \
                  frontend/data/backcast/completeness.js
  git commit -m "Remove push-staging; untrack regenerable dashboard JS"
  git push          # one normal commit; the .gitignore from this PR keeps them out
  ```
  (Or reply "delete them" and I'll do it here via 84 `delete_file` commits — squash-merge collapses
  the noise.)
- **Or folded into Step-4 Option A** — the purge command there already lists these exact paths, so a
  history purge removes them from the tree *and* every pack in one shot.

> **Neither the .gitignore nor any tree-deletion shrinks history.** They stop *growth*; the blobs
> remain in every existing pack. **On-disk repo size is unchanged by Step 2** — shrinking the pack is
> the Step-4 owner decision below.

---

## Step 3 — Make fast clone the standard (the actual unstick — no history change)

See **`docs/fast-clone.md`**. In one line:

```bash
git clone --filter=blob:none "$ORIGIN" market-simulator      # ~10.75 MiB metadata + lazy blobs
# fallback if even that hangs — depth-1 blobless, then lean on the GitHub API:
git clone --depth 1 --filter=blob:none "$ORIGIN" market-simulator
```

A blobless clone downloads the full commit/tree graph (10.75 MiB) and fetches file *blobs* on demand
— so a session that touches a handful of source files never pulls the 11.7 GiB of `data/raw/`. This
is why every analysis in this audit ran instantly while the auto-clone hung.

**Proposed (NOT merged — CLAUDE.md forbids editing workflows/setup without owner sign-off):** switch
the environment's initial-clone step to `--filter=blob:none` (+ optionally a `data/raw` sparse-checkout
exclusion). Exact location and diff are in `docs/fast-clone.md` §"Proposed setup-hook change". Approve
it and it goes in a follow-up commit.

---

## Step 4 — OWNER-GATED recommendation (diagnose + propose only — nothing executed)

To actually reduce the on-disk/clone size you must rewrite history and force-push `main`. Three
options, cheapest-blast-radius first:

### Option C (recommended first — **no history rewrite**): adopt Step 3, keep history
Make blobless/shallow the clone standard and stop the derived-file bleed (this PR). **Clone-time pain
disappears** without invalidating a single existing clone or branch. Repo stays 11.5 GiB server-side,
but nobody has to transfer it in full. **Cost: zero. Blast radius: none.** Do this regardless of A/B.

### Option A (modest shrink): purge dead blobs from history
Drop the orphaned staging tarball, regenerable dashboard payloads, and superseded/relocated blobs
from all history.

```bash
# fresh full mirror (one slow clone, off to the side)
git clone --mirror "$ORIGIN" mktsim.git && cd mktsim.git
git filter-repo \
  --path scripts/_rule27_push_staging/ --path-glob 'frontend/data/backcast/manifest.js' \
  --path-glob 'frontend/data/backcast/benchmark.js' --path-glob 'frontend/data/backcast/completeness.js' \
  --invert-paths
git push --force --mirror origin      # ⚠ rewrites ALL history
```
- **Estimated recovery: a few hundred MiB** (the ~218 MiB of dead blobs measured + metadata). Small,
  because history bloat is small.
- **Not worth the blast radius on its own.**

### Option B (the only real shrink): migrate `data/raw/` binaries to Git LFS
Move the ~9–11 GiB of parquet/zip/xlsx/pdf out of the git pack into LFS; clones then pull a **tiny**
pack + LFS objects on demand.

```bash
git clone --mirror "$ORIGIN" mktsim.git && cd mktsim.git
git lfs migrate import --everything \
  --include='data/raw/**/*.parquet,data/raw/**/*.zip,data/raw/**/*.xlsx,data/raw/**/*.pdf,data/raw/**/*.gz,data/raw/**/*.csv'
git push --force --mirror origin      # ⚠ rewrites ALL history
# then, in each working clone: git lfs install && git lfs pull
```
- **Estimated after-size: git pack drops to ~tens–hundreds of MiB**; the ~11 GiB moves to LFS
  storage. A blobless clone is already ~instant, but LFS also fixes full clones and `git push`.
- **Requires: a GitHub LFS storage+bandwidth budget** (11+ GiB stored; bandwidth per clone/pull that
  actually pulls the data). Confirm the plan's LFS quota first.
- **Interaction with the Pages deploy:** the deploy already does a blobless sparse checkout of
  `frontend/`+`scripts/` only, so it never touches `data/raw/` — **LFS does not affect the live
  dashboard.** ✅

### Blast radius shared by A and B (history rewrite)
- **Every existing clone and open branch/PR is invalidated** — all in-flight branches
  (`claude/ff-wave-manager-standing`, `claude/orchestrator-unification-refactor`,
  `claude/transmission-interchange-refactor`, and any others) must be **re-based onto the rewritten
  `main`** by their owners, or re-created.
- All commit SHAs change; any doc/log/issue referencing a SHA goes stale.
- Must be run when no other session is mid-push; coordinate a freeze window.
- Irreversible in practice once the old refs age out.

---

## OWNER DECISION BOX — please pick

- [ ] **C only** (adopt fast-clone standard; leave history as-is). *Zero risk. Recommended baseline —
      do this even if you also pick A or B.*
- [ ] **Physically untrack the 1.0 MiB clutter now, forward-only** (no history rewrite) — either run
      the 2-line `git rm` from Step 2 locally, or reply "delete them" and I'll do it here via per-file
      `delete_file` commits. Independent of A/B.
- [ ] **Also approve the setup-hook change** to `--filter=blob:none` (follow-up commit; touches env
      setup / no workflow file unless you also say so).
- [ ] **A — purge dead blobs** (recovers a few hundred MiB; rewrites history; I coordinate a
      branch-rebase freeze).
- [ ] **B — migrate `data/raw/` to Git LFS** (the real shrink to ~tens of MiB pack; rewrites history;
      **needs an LFS quota confirmation first**; I coordinate the freeze + rebases).
- [ ] **Remove specific patches** (name which of `patches/`, `docs/handoffs/*.patch` to drop).

Nothing in A/B is executed without an explicit "yes" here — no force-push, no touch of `main`
history, per the session constraints.
