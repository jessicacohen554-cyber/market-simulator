# Repo clone-bloat audit (2026-07)

*Standalone infra session. Diagnoses the recurring "cloning loop" (sessions
landing on stale/half clones; `git fetch` stalling; `git push` 413ing), stops the
forward bleed without touching history, makes the fast-clone pattern the standard,
and hands the owner a costed, owner-gated recommendation for any deeper cleanup.*

---

## TL;DR (lead with the numbers)

| Measure | Value |
|---|---|
| Server-side git pack (what a full clone downloads) | **11.49 GiB** (`GET /repos` `size` = 12,044,217 KB) |
| Current tracked tree, uncompressed | **12.03 GiB** across **9,728** files |
| `data/raw/` (immutable source data) | **11.69 GiB — 97% of the tree** (ERCOT alone 7.4 GiB) |
| Already-compressed binary (parquet 9.34 + zip 0.99 + xlsx 0.56 GiB) | **10.9 GiB** — git cannot shrink these |
| Confirmed-removable clutter (`scripts/_rule27_push_staging/`) | **0.365 MiB** (81 files) — **removed this session** |
| Regenerable dashboard JS (`manifest`/`benchmark`/`completeness.js`) | 0.629 MiB current; **~100+ historical versions of `benchmark.js` alone** |
| Reclaimable **history** bloat (deleted/superseded blobs) | **negligible — a few hundred MiB at most**, ~all of it regenerable payloads |

**Root cause of the loop is the clone *method*, not primarily repo size.** The
commit/tree graph is ~11 MiB and clones in ~2 s; only the file *blobs* (11.5 GiB,
97% immutable `data/raw/`) are heavy. A full-history clone / full `git fetch` has
to move all of it through the egress proxy, which stalls — leaving the session on
a stale or half-checked-out tree; the next full fetch stalls the same way and
`git push` 413s. A **blobless partial clone fixes this today with no history
change** (proven this session: full graph in 1.6 s, blobs fetched on demand).

**A history purge would reclaim almost nothing** — the 11.7 GiB of `data/raw/` is
*append-only* (each big file appears in exactly **1** commit; spot-checked), so it
is not duplicated across history. Only *removing `data/raw/` from git tracking*
(Git LFS or external object store, which still needs a history rewrite to drop the
single live copy from the pack) materially shrinks the repo. That is a big,
owner-gated, blast-radius change — **and only worth it if the 11.5 GiB itself is a
problem.** See §4.

---

## 1. Symptom & confirmation

The owner's read — "manual data uploads + committed push-scaffolding bloated the
repo" — is confirmed by the commit history and the size data:

- **Manual web-UI uploads.** Many commits are literally `Add files via upload`
  (committer `web-flow` = GitHub web UI). These added the large `data/raw/`
  parquet/xlsx/zip. They bloat the **current tree** (see §2), but because each
  file is uploaded once and never rewritten, they do **not** bloat history.
- **Committed push-scaffolding.** Dozens of commits — `Stage rule-27 payload part
  NN as verified pieces`, `Update staging manifest for the piece-split payload
  layout` — wrote a base64-chunked `rule27-bigfiles.tar.gz` under
  `scripts/_rule27_push_staging/` (81 `*.tar.gz.b64.part*.txt` files). Pure
  transport scaffolding for the API-413 workaround; never a repo artifact.
- **The friction is already logged.** Recent commit messages repeatedly record
  *"git push 413s"*, *"all git fetches disconnect through the proxy"*, *"ran on a
  1572-commit-stale clone (066fb98)"*, and the turn-43 ledger explicitly surfaced
  to the owner: *"staging-dir bloat, stranded PJM M-3 unapplied patch, recurring
  stale-clone/proxy friction."* This session is the response.
- **Stale-clone reproduced.** This environment's working copy started at
  `066fb98` while true `origin/main` was `a4a17c9` — i.e. the auto full clone
  landed ~1,500+ commits behind (it stalls during the 11.5 GiB blob transfer).
  The blobless clone reached true `a4a17c9` in **1.6 s**.

## 2. Diagnosis — where the weight is

### 2a. Current tree (GitHub recursive tree API, exact per-blob sizes)

`data/raw/` is **11.69 GiB / 4,906 files = 97%** of the 12.03 GiB tree:

| sub-area | size | files |
|---|---:|---:|
| `data/raw/ercot` | 7,555 MiB | 1,839 |
| `data/raw/campd-unit-level` | 786 MiB | 308 |
| `data/raw/lmp-data` | 761 MiB | 213 |
| `data/raw/ercot-AS` | 599 MiB | 65 |
| `data/raw/zone-specific-demand` | 272 MiB | 89 |
| `data/raw/ercot-hsl` | 234 MiB | 54 |
| `data/raw/eia-930` | 196 MiB | 107 |
| `data/raw/caiso-dam-outages` | 164 MiB | 1,098 |
| `data/raw/caiso-curtailment` | 158 MiB | 9 |
| (…rest) | — | — |

By file type: **`.parquet` 9.34 GiB (2,917)**, `.zip` 0.99 GiB (316), `.csv`
766 MiB (657), `.xlsx` 562 MiB (1,135). The `.parquet`/`.zip`/`.xlsx` are already
internally compressed, so git's zlib gains almost nothing — this ~10.9 GiB is the
pack's hard floor.

Non-`data/raw/` is only ~0.34 GiB: `results/` 243 MiB (mostly
`results/calibration` keeper bundles, 239 MiB), `frontend/` 67 MiB (backcast
sidecars + runs), `docs/` 10 MiB, `scripts/` 9 MiB, `src/` 4.6 MiB,
`scope2-lce-portfolio/` 7 MiB.

### 2b. History bloat (near-zero, and it's the regenerable payloads)

The server pack (**11.49 GiB**) is essentially equal to the *packed current
tree* — the ~10.9 GiB of pre-compressed binary + ~0.3 GiB of compressible text.
There is no room left for a large mass of deleted/superseded blobs. Confirmed by
targeted `commits?path=` counts:

- Big `data/raw/` files — **1 commit each** (added once, never rewritten →
  append-only → **zero** history duplication). Spot-checked: the 63 MiB ERCOT
  SCED parquet, the 22 MiB CAISO curtailment xlsx, the eGRID xlsx, the 22 MiB
  NYISO zip — all `1 commit`.
- `frontend/data/backcast/benchmark.js` — **100+ commits** (rewritten on every
  keeper registration; ~0.6 MiB × 100+ versions ≈ tens of MiB of history). This
  is the *only* class that churns history, and it is exactly the **regenerable**
  dashboard payload the Pages deploy rebuilds.

So whatever reclaimable history bloat exists (a few hundred MiB at most) is the
regenerable/clutter category, **not** `data/raw/`.

*Method note:* a full `git rev-list --objects --all` blob→path map was attempted
in a blobless clone but is impractically slow in this CPU-throttled container
(~100 obj/s). It is unnecessary: the server-pack-vs-current-tree identity plus the
per-path commit counts bound the history bloat tightly.

### 2c. Classification

**(i) LEGIT-KEEP — do not touch.**
- `data/raw/` immutable source data — 11.69 GiB (CLAUDE.md: never delete).
- Committed keeper bundles — `results/calibration/<name>/` slim files (239 MiB),
  `frontend/data/backcast/registry/<id>.json`, `runs/<id>.js`, `bench/`,
  `status/`, `keepers/` (65 MiB) — the dashboard deliverables (CLAUDE.md rule 15).

**(ii) REMOVABLE-NOW — never needed in git.**
- `scripts/_rule27_push_staging/` — 81 files, 0.365 MiB. **Removed this session**
  (81 `delete_file` commits) + gitignored (`scripts/.gitignore`).
- `*.patch` files — 18 files, 0.208 MiB (e.g. `docs/handoffs/pjm-m3-gas-bridge.patch`).
  **Left in place** — these are session hand-off artifacts, not clone-loop
  drivers, and one (`pjm-m3-gas-bridge.patch`) is a still-relevant unapplied
  change the owner may want re-based. Owner call, not removed here.

**(iii) REGENERABLE — rebuilt by the Pages deploy.**
- `frontend/data/backcast/manifest.js` / `benchmark.js` / `completeness.js` —
  0.629 MiB current, but ~100+ historical `benchmark.js` versions.
  **Left tracked** this session: the root `.gitignore` §6 documents them as
  *intentionally committed* for the `file://` preview fallback, and untracking
  them (a) contradicts that documented policy, (b) breaks the local preview, and
  (c) reclaims <1 MiB from the current tree. This is a genuine but *small* owner
  decision — see the decision box.

## 3. What this session changed (Step 2 + Step 3 — no history rewrite)

All via the GitHub API (`git push` 413s here); all forward-only and reversible.

1. **Untracked `scripts/_rule27_push_staging/`** — 81 `delete_file` commits
   removing every `*.tar.gz.b64.part*.txt` chunk + `MANIFEST.md`. Verified gone
   (dir now 404 on the branch).
2. **Added `scripts/.gitignore`** — ignores `_rule27_push_staging/`,
   `*.tar.gz.b64.part*.txt`, `rule27-bigfiles.tar.gz` so the scaffolding can never
   be re-committed. (A scoped nested ignore, deliberately **not** a rewrite of the
   304-line root `.gitignore`, per CLAUDE.md rule-27 push-integrity.) Blob-verified
   after push (sha match).
3. **`docs/fast-clone.md`** — the fast-clone / anti-loop recipe (Step 3), incl. a
   *described-not-merged* `SessionStart` hook addition and the environment
   clone-filter proposal.

> **`git rm --cached` shrinks the working tree and stops growth, but does NOT
> shrink the pack / clone size** — the removed blobs remain in history. Pack
> reduction is the owner-gated §4 call. In this repo that distinction barely
> matters anyway: the removed clutter is 0.365 MiB.

## 4. Owner-gated recommendation (DIAGNOSE + PROPOSE only — nothing run)

### Recommendation, in priority order

**Option 0 — Adopt the fast partial-clone standard. Do this; it fully fixes the
loop. No history change, zero risk.**
The cloning loop is a clone-*method* problem. A `--filter=blob:none` clone of the
11.5 GiB repo is fast because it defers the blobs. Adopt it as the environment
default (and/or the `SessionStart` fast-forward in `docs/fast-clone.md`). **If the
11.5 GiB storage itself is not a concern, stop here — no history rewrite is
warranted.**

**Option A — Clutter/regenerable-only history purge. NOT recommended on its own.**
A `git filter-repo` dropping the staging chunks + the regenerable dashboard-JS
history reclaims only ~a few hundred MiB (**< 3%** of the pack) yet still forces a
full-history rewrite + force-push + re-clone of everyone. The blast radius dwarfs
the benefit. Only fold this in if you are already doing Option B.

**Option B — Move `data/raw/` out of git blobs. The only lever that materially
shrinks the repo (~11.5 GiB → ~0.5–1.5 GiB in git). Owner-gated; big blast
radius; must be run from a full clone outside Claude web sessions.** Two variants:

- **B1 — Git LFS.** Rewrite history replacing `data/raw/` large binaries with LFS
  pointers. Keeps *every byte* (in the LFS store), so it honours "never delete
  `data/raw/`." Post-migration git is ~0.5–1.5 GiB; clones pull pointers + fetch
  LFS objects on demand. **Costs:** GitHub LFS storage + bandwidth billing;
  force-push to `main`; every clone re-synced; all open branches rebased. **Risk
  to validate first:** LFS uses a separate batch/transfer protocol — given `git
  push` 413s and `git fetch` stalls through this proxy, **LFS transfers may not
  work from Claude web sessions at all**; the migration and day-to-day LFS pulls
  likely require a normal (non-proxied) environment.
- **B2 — External object store + gitignore + refetch.** Extend the pattern the
  repo *already uses* — `data/raw/pjm-energy-offers/`, `caiso-public-bids/`, the
  NYISO/NEISO archives are already gitignored with `scripts/fetch_*.py` + a
  README — to the heavy committed parquet. Move bytes to S3/GCS (or rely on the
  primary-source URLs), gitignore them, add fetch scripts, and `filter-repo` them
  out of history. **Costs:** same history rewrite/force-push/re-clone. **Risk:**
  some ERCOT 60-Day disclosure windows may no longer be re-fetchable from the
  primary source (rolling retention) — for those, B1 (which keeps the bytes) is
  safer than B2 (which trusts refetch).

### Exact commands for Option B (run from a FULL clone, NOT here — do not run)

```bash
# 0. Full mirror clone on a normal machine (NOT this proxied env).
git clone --mirror https://github.com/jessicacohen554-cyber/market-simulator.git
cd market-simulator.git
git count-objects -vH          # record the true "before" pack size

# --- B1: Git LFS ---------------------------------------------------------
#   migrate the heavy binary types in data/raw across ALL history to LFS
git lfs migrate import --everything \
  --include="data/raw/**/*.parquet,data/raw/**/*.zip,data/raw/**/*.xlsx,data/raw/**/*.csv.gz"
git count-objects -vH          # "after" (git side); LFS store holds the bytes
#   then force-push the rewritten refs (coordinated — see blast radius)

# --- B2: strip from history (external-store variant) ---------------------
#   pip install git-filter-repo
git filter-repo --path data/raw --path-glob 'data/raw/**' --invert-paths \
  --path scripts/_rule27_push_staging --invert-paths
#   (add the raw files to .gitignore + a fetch script BEFORE force-pushing)

# Clutter-only (Option A), if ever done standalone:
git filter-repo --invert-paths \
  --path-glob 'scripts/_rule27_push_staging/**' \
  --path-glob 'frontend/data/backcast/benchmark.js' \
  --path-glob 'frontend/data/backcast/manifest.js' \
  --path-glob 'frontend/data/backcast/completeness.js'
```

### Blast radius (applies to A and B — any history rewrite)

- **Every commit SHA changes** → every existing clone is invalidated and must
  re-clone; old SHAs referenced in `docs/`, `calibration-log.md`, PR bodies become
  dangling.
- **Force-push to `main`** required (this is the irreversible step).
- **All open branches rebased** onto the rewritten base. Currently on origin:
  `main`, `claude/ff-wave-manager-standing-e90gfj`,
  `claude/holdout-backcast-readiness-x8jf60`,
  `claude/orchestrator-unification-refactor-iyc472`,
  `claude/transmission-interchange-refactor-93bbm6` — plus any open PRs, which
  must be recreated/rebased.
- **Must be executed from a full clone in a normal environment** — the rewrite,
  the force-push, and (for B1) LFS transfers cannot be done from a Claude web
  session (proxy 413/stall).
- CI content checks (`file-integrity-guard`, `quarantine-gates`) are SHA-agnostic
  and unaffected; but re-clone everyone before the next session or they'll fork.

---

## 5. Owner decision box

Please pick one (the session already did Option 0's repo-side prep — the
fast-clone doc + clutter removal — regardless):

- [ ] **A — Fast-clone only (recommended default).** Keep `data/raw/` in git;
      adopt the partial-clone standard (and set the environment clone filter to
      `blob:none`). No history rewrite. Closes the loop. *Choose this unless the
      11.5 GiB pack size is itself a problem.*
- [ ] **B — Also shrink the repo via LFS/external-store migration of `data/raw/`
      (owner runs it from a full clone).** Reclaims ~11 GiB from git. Accept the
      force-push + re-clone-everyone + branch-rebase blast radius above.
      Sub-choice: [ ] B1 Git LFS (keeps bytes) · [ ] B2 external store + refetch.
- [ ] **Also apply the described `SessionStart` blobless fast-forward hook** in
      `docs/fast-clone.md` (I left it un-merged pending your sign-off).
- [ ] **Untrack the regenerable dashboard JS** (`manifest`/`benchmark`/
      `completeness.js`) and flip root `.gitignore` §6 — small (<1 MiB now, but
      it's the main history-churn file), and it changes the documented preview
      policy. Default: leave as-is.
- [ ] **Re-base or drop `docs/handoffs/pjm-m3-gas-bridge.patch`** (stranded
      unapplied 39 KiB patch) — separate lane, not a clone-loop driver.
