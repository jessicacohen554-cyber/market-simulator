# FINDING — rewrite readiness: can the evidence record survive a history rewrite?

**Date:** 2026-08-12 · **Lane:** REWRITE-PREP (preparation only; **no history was
rewritten, nothing was force-pushed, no keeper or `data/raw` file was touched**)
· **Head at start:** `origin/main` @ `17e9ad5` (the charter quoted `f6381c5`;
main had advanced 4 commits, and advanced again mid-lane — see §8).

---

## 0. Headline

**The record CAN be made to survive — the mechanism works and is verified. But
the rewrite it would enable is not worth doing.**

Three findings drive that, in descending order of importance:

1. **A partial clone already solves the day-to-day symptom, completely and
   today.** A sparse blobless clone excluding `data/raw` is **715 MB** against
   **~17.6 GB** for a full one — a **24× reduction, with zero history rewriting**
   (§7.2). The rewrite's main practical payoff is available without it.
2. **Annotated tags do survive a rewrite — but the naive application of them
   silently lies.** Under filter-repo's *default* flags, a tag on a commit the
   filter empties, or on a PR merge the filter makes degenerate, is moved to the
   nearest surviving ancestor. It still resolves; it resolves to the **wrong
   commit**, with no error. Both were reproduced (§3.2–§3.3). Since this repo
   merges through PR merge commits and a data-intake PR touches only `data/raw`,
   this is the **common case for exactly the commits a `data/raw` strip would
   hit**, not a corner case.
3. **The tags cannot be published from a Claude Code session.** `refs/tags/*` is
   refused with HTTP 403 over every path tried — git transport from two
   repositories, and the GitHub Git Data API (§5.2). The 104-tag set is computed,
   named and committed as a manifest; publishing it is one owner command.

**Recommendation: NO-GO on a rewrite for size reasons; GO on partial clone plus
untracking `data/raw` going forward.** Preconditions if the owner charters one
anyway: §8.

---

## 1. T1 — the token inventory

Tooling: `scripts/audit_citation_tokens.py` (committed). It scans the
citation-bearing corpora, extracts every `\b[0-9a-f]{7,40}\b` token, and resolves
each against the object database.

**The working clone is SHALLOW — 263 of 12,024 commits.** This had to be solved
before anything could be classified: 93 % of cited commits do not resolve locally,
and a naive audit would have mislabelled them all as false positives. The lane
built a **commit-only mirror** (`git fetch --filter=tree:0`) — all 12,024 commits
in **7.5 MB**, no trees, no blobs — and classified against that.

*(This is a live limitation, not only a rewrite concern: the record already
acknowledges it — `frontend/data/backcast/keepers/MISO.json` notes a keeper's
`git_sha 6b05f058, NOT reachable in this shallow clone`.)*

Scanned **1,328 files** (docs/ 1,051 · `frontend/data/**/*.json` 270 · matrix
base + 6 shards): **6,109 occurrences**, **2,433 unique tokens**.

| Bucket | Unique | Occurrences | At risk from a rewrite? |
|---|---:|---:|---|
| **(a) real commit SHA** | **560** | **1,611** | **YES — the entire exposure** |
| (b) 16-char runtime/config key | 445 | 1,781 | No |
| (c) blob / tree hash | 24 | 31 | No — content-addressed (§3.4) |
| (d) other identifier | 435 | 731 | No |
| (e) false positive | 969 | 1,955 | No |

By corpus (unique tokens): docs/ `a=544, b=368, c=24, d=427, e=411` ·
frontend JSON `a=41, b=231, d=13, e=593` · matrix `a=40, b=66, d=9, e=2`.

**Bucket (e) is 969/969 digits-only** — decimal fragments of published numbers
(`191435844.4022851` → `4022851`). A clean, fully-explained bucket.

### 1.1 The 16-char tokens — verified safe, and not quite what the charter said

The charter's warning is correct and now **empirically confirmed: zero of the 445
sixteen-char tokens resolve as a git object of any type.** The separation is
clean, so no transformation bounded to lengths {7,8,40} can touch one.

Hand-checking a sample (as the charter required before committing) refined the
characterisation: the 445 are **not** all cache keys.

- **390** are true hex config/dispatch keys — `"dispatch_hash": "00f21a40a0992046"`,
  bundle paths `results/hindcast/…/00d64a46ce67e38c`, matrix `ev` fields.
- **55** are **decimal float mantissas**, not hashes at all: `"reserve_ratio":
  1.0107056454834216` yields the 16-digit token `0107056454834216`.

Both must be left alone, so the safety rule is unchanged — but "the 792 16-char
tokens are cache keys" was an over-reading of the raw grep, and a length-only
heuristic is not the reason they are safe. **Resolution against the object DB is.**

*(The charter's docs/-only distribution — 2,851 tokens, 792 × 16-char — did not
reproduce: docs/ alone now yields 3,979 tokens, 1,179 × 16-char. The corpus grew,
and this lane counted three corpora rather than one. Method and per-bucket
resolution are what carry the conclusion, not the raw counts.)*

---

## 2. T2 — which citations are load-bearing

**Criterion.** A citation is load-bearing if breaking it breaks *a reproduction, a
governance determination, or an audit trail* — as opposed to a narrative aside
("HEAD at writing: `01b6a6a`"), which a rewrite degrades to a dead link, not to
broken work.

| Code | Criterion | Commits |
|---|---|---:|
| LB-1 | **Reproduction pin** — a reproducing session must check out this state | 68 |
| LB-2 | **Governance record** — keeper shard, `calibration-complete.json`, `docs/governance/` | 9 |
| LB-3 | **Rule-28 audit trail** — evidence in a mechanism-matrix cell | 39 |
| LB-4 | **Named incident** — the commit *is* the subject of standing rule guidance | 1 |
| LB-5 | **Integrity proof** — cited in a byte-identity / blob-verification table | 10 |

Of **560** cited commits: **104 distinct commits are load-bearing** (105 tokens,
deduped by full OID); **74** are borderline narrative ("HEAD at writing"
datestamps, kept in the finding but not tagged); **381** are plain narrative.
The 104 carry **601 of the 1,611** commit-citation occurrences.

The charter's required minimum is covered:

- **`3ae7465`** — FH-5's `src/` pin → `cite/fh5-src-pin` (19 citations, 18 files).
- **`c5593684`** — the lost-edit incident → `cite/lost-edit-matrix-union` (10 citations).
- **All 40** commits cited as `ev` evidence in the mechanism matrix — note **29 of
  them live in the base `mechanism-matrix.js`**, not the per-ISO shards (CAISO 4 ·
  MISO 9 · PJM 2 · ERCOT/NEISO/NYISO 1 each).
- **All 7** commits cited in keeper shards (`MISO`, `NEISO`, `PJM` × 2 each) plus
  `calibration-complete.json`.

**Promoted by the criteria beyond the charter's list:** 68 LB-1 reproduction pins
(frozen-HEAD A/B controls, `git diff <sha>` reproduction commands, "solved at"
provenance) and 10 LB-5 byte-identity proofs. The largest single at-risk file is
`docs/handoffs/ffr-owner-sitting-2026-08-02.md` — **96 cited commits**, followed by
`docs/forecast-readiness-prompt-pack-2026-07.md` (70) and
`docs/calibration-log/miso.md` (42).

---

## 3. T3 — empirical verification of the survival mechanism

Not taken on trust. `git-filter-repo` 2.47.0, on synthetic repositories that
reproduce this repo's exact shape (a `src/` tree, a `data/raw/` tree, PR merge
commits) and run the exact operation a rewrite lane would: `--invert-paths
--path data/raw`. Scripts: `t3_test.sh`, `t3b_test.sh`, `t3c_test.sh` (scratch).

A synthetic repo is the right instrument here — filter-repo's ref handling is a
property of the tool, not of this repo's content — and it is the only one that
fits: a second full clone of this repo does not fit on the session's disk.

### 3.1 CONFIRMED — tags survive

An annotated tag on a surviving commit was rewritten onto the new commit,
resolved correctly, **and survived a push to a bare remote and a fresh clone**:

```
BEFORE  cite/code-pin -> f58dfcd  "c3 code (the FH-5-like pin)"
AFTER   cite/code-pin -> 42eb439  "c3 code (the FH-5-like pin)"     (old SHA: GONE)
FRESH CLONE  cite/code-pin -> 42eb439  "c3 code (the FH-5-like pin)"
```

Lightweight tags survive equally, but carry no record — hence the annotated-only
rule in the convention.

### 3.2 DEFECT — a tag on a data-only commit silently re-points

The commit whose only content was `data/raw` was **pruned as empty**, and its tag
was **moved to an unrelated earlier commit**:

```
cite/data-only-pin -> efb6a2f  subject=[c1 code]     <-- WRONG COMMIT, no error
commit-map: e949b17… -> 0000000000000000000000000000000000000000   (pruned)
```

**Fix, verified:** `--prune-empty=never` preserves the commit (now empty) and the
tag stays truthful — `cite/data-only -> 1d58a2a "c2 DATA ONLY (cited!)"`.

### 3.3 DEFECT — the same happens to PR merge commits, which is most of the tag set

This is the more serious one, because **this repo merges through PR merge
commits** and most `cite/*` tags therefore sit on one. A merge whose branch
touched only `data/raw` becomes *degenerate* after the filter and is pruned by
default:

```
default flags                              -> cite/merge-pin -> "base"   *** SILENTLY RE-POINTED ***
--prune-empty never --prune-degenerate never -> cite/merge-pin -> "Merge pull request #999…"  TRUTHFUL
```

**Both flags are required.** `--prune-empty=never` alone does not save a
degenerate merge.

### 3.4 Content-addressed hashes are rewrite-invariant — a second, stronger handle

The `src` subtree hash was **byte-identical before and after** the rewrite
(`f0e5e62b91…`), because trees are content-addressed and `data/raw` is a sibling
path. So the 24 bucket-(c) blob/tree citations need **no protection at all**, and
FH-5 already contains an unconditionally durable handle it was not relying on:

```
3ae7465:src = 66d789dced7308dcaa837f2e6441d06de9f6454b
```

A reproducing session that cannot resolve `3ae7465` can verify a candidate
checkout with `git rev-parse HEAD:src`. This is stronger than the tag: it depends
on no ref, no remote, and no rewrite policy. §T5 records it in FH-5 itself.

### 3.5 Alternatives evaluated and rejected

| Mechanism | Verdict | Evidence |
|---|---|---|
| **`refs/replace`** | **Rejected — fails twice.** Destroyed by the filter-repo pass (`refs/replace` empty afterwards) *and* absent from a fresh default clone. | §3.1 run |
| **Committed old→new map** | **Rejected as primary.** Cannot exist until after the rewrite, so it protects nothing during it; needs a lookup step no reader will take; and a second rewrite needs a map-of-maps. Useful only as a post-hoc appendix. | design |
| **filter-repo's `.git/filter-repo/commit-map`** | **Rejected as primary, valuable as an audit artifact.** It is a local, uncloned `.git/` file, discarded with the container. But it is the **only** mechanism that reports a pruned commit *honestly* (all-zeros RHS) instead of silently re-pointing — so a rewrite lane must commit it. | §3.2 output |
| **Annotated tags** | **ADOPTED**, subject to §3.2–§3.3 flags. | §3.1 |

---

## 4. T4 — what was tagged

**104 annotated tags** created under the `cite/*` namespace, one per load-bearing
commit. Convention documented at **`docs/governance/citation-tags.md`** (rule 5
`[R-NO-MAGIC]`: where a future session will find it, not only in a commit
message). Manifest committed at **`docs/governance/citation-tags.json`**.

Namespace: `cite/<slug>`, semantic and SHA-free, prefixed by what makes the
commit load-bearing — `cite/gov-*`, `cite/mx-*`, `cite/repro-*`, plus hand-named
anchors (`cite/fh5-src-pin`, `cite/lost-edit-matrix-union`). Each message records
what is pinned, why, and every citing `file:line`, so the tag is self-documenting:

```
cite/fh5-src-pin - durable citation handle
Pins 3ae7465d8d94d6927c4762e4195e55f7a34f7d95
  (2026-08-10) Merge pull request #3860 from …/claude/miso-calibration-151-a5djd6
WHY PINNED:
  LB-1  reproduction pin - a session reproducing a published result must check out this state
  LB-5  integrity proof - cited in a byte-identity / blob-verification table
CITED AS 3ae7465 - 19 citation(s) across 18 file(s): …
```

Because the working clone is shallow, the tags had to be created in the
full-history mirror — `git tag` fails on 93 of the 104 in the working clone.
`scripts/apply_citation_tags.py` handles both cases and documents the mirror
recipe.

---

## 5. WHAT STILL BREAKS

Adversarial pass. Everything below was **checked, not assumed**.

### 5.1 Checked and SAFE

| Thing | Status |
|---|---|
| `.github/workflows/file-integrity-guard.yml` | **Rewrite-agnostic, confirmed.** `BASE_SHA: ${{ github.event.pull_request.base.sha \|\| github.event.before }}` — resolved from the PR event at runtime, never a stored SHA. **Not "fixed".** |
| SHA-pinned GitHub Actions | **None.** Zero `uses: …@<40-hex>` in `.github/`. |
| Submodules | **None.** No `.gitmodules`. |
| Other hex in `.github/` | Two tokens, **both narrative comments**, neither functional: `27c0152` (an incident reference in `ci.yml`) and `603c2498bf71d21d` (a 16-char cache key in a comment). |
| **PR / issue numbers** | **SAFE and this matters** — **1,269** `#NNNN` references in docs/. GitHub PR and issue numbers are metadata independent of commit SHAs, so the repo's dominant cross-reference idiom survives intact. |
| Blob / tree hash citations | **SAFE** — content-addressed (§3.4). Covers the byte-identity tables in `fh-5-phase-b`, `miso-93-keeper-reaudit-charter`, `README-neiso64`, and the `sha256` data-artifact citations. |

### 5.2 BREAKS — and the tags do not fix it

**The tags cannot be published from this session.** `refs/tags/*` is refused with
HTTP 403 on **four independent paths**:

1. `git push origin 'refs/tags/cite/*'` from the full-history mirror → 403
2. `git push origin refs/tags/<single>` from the working clone → 403
3. lightweight tag push (`<sha>:refs/tags/<name>`, no tag object) → 403
4. `POST /repos/{o}/{r}/git/tags` → *"Write access to this GitHub API path is not
   permitted through this proxy."*

A `--dry-run` push of the designated branch succeeds, so the restriction is
specifically the tag namespace, not credentials in general. **`git ls-remote
--tags origin` returns 0 tags — the namespace is still greenfield.** The manifest
and the apply script are committed, so this is one owner command:
`python3 scripts/apply_citation_tags.py --git-dir <full-history-repo> --push`.

**Consequence for sequencing: the tags must exist on the remote BEFORE any
rewrite runs.** A tag created after the rewrite pins a post-rewrite SHA and
proves nothing about the pre-rewrite record.

### 5.3 BREAKS — accepted losses

| Thing | Count | Effect |
|---|---:|---|
| **Narrative commit citations** | **456** commits / ~1,010 occurrences | Become dead references. Not tagged by design — tagging all 560 would make the namespace unusable. They date events whose artifacts live elsewhere. |
| **Doc-quoted git commands** | **19** | `git diff 226634b e94b9aa`, `git show bc78449`, `git diff 3ae7465` … These fail after a rewrite. Those on tagged commits can be rewritten to use the tag; the rest are lost. |
| **GitHub commit permalinks** | **1** | `…/commit/f4f139b0e7775b30b56515bb1d18c8e5c71c4fe0` — 404s once the old object is unreachable. |
| **`Claude-Session:` trailers** | 1 in docs/, plus every commit message | Session URLs are unaffected, but the trailers live *inside* commit messages, which a rewrite re-writes into new commits. Content preserved, SHAs not. |
| **Bundle/registry provenance** | — | `results/calibration/` and registry sidecars key on **run ids and config hashes**, not commit SHAs. Verified: **0 files** under `frontend/data/` contain a `git_sha` field. Evolution-ledger paths are keyed by 16-char runtime hash — **unaffected** (§1.1). |

### 5.4 The residual risk that has no mitigation

Nothing detects a broken citation. There is no CI check that a cited SHA
resolves, and (per the charter) this lane adds no workflow. After a rewrite the
456 untagged citations decay silently. **Recommendation, not implemented:** extend
`scripts/audit_citation_tokens.py` into the existing `ci.yml` governance job as a
warn-only step that reports unresolvable bucket-(a) tokens. That is a change to an
existing workflow, not a new one — but it is the owner's call, so it is filed
here rather than made.

---

## 6. Rule-28 compliance

This lane **tested no mechanism and edited no matrix cell** — the matrix shards
were read only, to harvest `ev` citations. `scripts/check_mechanism_matrix.py`
was run to prove it (§9).

---

## 7. T7 — the two cheap measurements

### 7.1 (a) How much of `results/calibration` is prunable — essentially nothing

`results/calibration` is **351 MB**: 109 bundle directories (334 MB) + 864 loose
files (16 MB, mostly `.md`/`.json` records). Matching each bundle against the
`bundle` field of all 66 registry sidecars:

| | Dirs | Size |
|---|---:|---:|
| Referenced by a registry sidecar | 66 | 304 MB |
| **Not referenced — prune candidates** | **43** | **30 MB** |

**Rule 15's top-15-per-ISO retention is already satisfied**: ERCOT 15 · MISO 15 ·
NYISO 15 · CAISO 15 · PJM 4 · NEISO 2 = 66 registered runs. There is **no
retention backlog**. The 30 MB of orphans is **0.3 % of the repo** — an ordinary
delete commit if someone wants it, but it moves nothing. *(Not performed, per the
charter.)*

### 7.2 (b) Partial clone — this is the actual answer to "repo too large"

Measured in this session, end to end:

| Clone | `.git` | Worktree | Total |
|---|---:|---:|---:|
| Full (what a session gets today) | 7.45 GB | 10.2 GB | **~17.6 GB** |
| `--depth=1 --filter=blob:none --sparse --no-checkout` | 628 KB | — | **628 KB** |
| …then sparse-checkout everything **except `data/raw`** | 182 MB | ~533 MB | **715 MB** |

**~24× smaller, 7,139 files, no history touched.** Recommended command for any
lane that does not run solves (docs, governance, dashboard, code review):

```bash
git clone --depth=1 --filter=blob:none --sparse --no-checkout \
  https://github.com/jessicacohen554-cyber/market-simulator
cd market-simulator
git sparse-checkout set --no-cone '/*' '!/data/raw'
git checkout
```

Caveats, stated plainly: `--depth=1` reproduces the shallow-clone limitation of
§1 (cited SHAs will not resolve — add `--filter=tree:0` history on demand, 7.5 MB,
recipe in `scripts/apply_citation_tags.py`); and a **solving** lane needs
`data/raw` and gets no benefit.

---

## 8. Go / no-go

### NO-GO on rewriting for size. Reasons, in order:

1. **The pack (7.45 GB) is smaller than the live tree (10.2 GB).** There is
   almost no dead history to strip. A rewrite's yield is bounded by what is
   *live*, and removing live data from history means also removing it from the
   working tree — a design change (LFS or re-fetch), not a cleanup.
2. **Partial clone delivers 24× today, with zero risk** (§7.2). The rewrite's
   practical benefit is already obtainable.
3. **The cost is a permanent, silent, one-way degradation of the evidence
   record.** Even fully executed, tags cover 601 of 1,611 commit-citation
   occurrences; the other ~1,010 decay with nothing to detect it (§5.4).
4. **The failure mode is silent re-pointing, not breakage** (§3.2–§3.3) — a tag
   that resolves to the wrong commit is worse than one that fails, in a
   governance model built on citations.

**GO on: untrack `data/raw` going forward** (stop adding to the live tree; keep
history as-is) **plus the partial-clone recipe as standard practice.** That
addresses the real symptom without spending the record.

### If the owner charters a rewrite anyway — mandatory preconditions

1. **Publish the `cite/*` tags first, and verify** — `git ls-remote --tags origin
   'refs/tags/cite/*'` returns 104. A tag created after the rewrite pins the
   wrong thing (§5.2).
2. **Run with `--prune-empty=never --prune-degenerate=never`.** Non-negotiable:
   without both, tags on data-only commits and on data-only PR merges silently
   re-point (§3.2–§3.3). **Verify after the pass** that every `cite/*` tag's
   target subject still matches the manifest's `subject` field — the manifest
   exists to make that a mechanical check.
3. **Commit `.git/filter-repo/commit-map`** into the repo as a governance
   artifact. It is the only record that distinguishes *rewritten* from *pruned*
   (§3.5), and it is otherwise discarded with the container.
4. **NO LANE MAY BE SOLVING.** A base moving under a running solve is exactly
   what cost FH-5 a leg (`fh-5-phase-b-2026-08-11.md` §3). Quiesce
   FFR-9C-PROMOTE / ARM-3-ARM / CAISO-VINTAGE-INTAKE and any successor first,
   and confirm zero open PRs — a rewrite invalidates every open branch.
5. **Re-run `scripts/audit_citation_tokens.py` after the rewrite** and record how
   many bucket-(a) tokens no longer resolve. That number is the honest cost, and
   it belongs in the record.
6. **Bound every regex to lengths {7,8,40}** if any citation rewriting is
   attempted, and hand-verify a sample — the 445 sixteen-char tokens must not be
   touched (§1.1).

---

## 9. Verification performed by this lane

- `scripts/check_mechanism_matrix.py` — matrix integrity, proving no cell changed (§6).
- 104 tags created and re-verified idempotent against the full-history mirror
  (`created 0 · already-present 104 · failed 0`).
- `git ls-remote --tags origin` → **0 tags**; the namespace is greenfield and the
  403 is a credential limit, not a collision.
- Hand-check of the 16-char sample before any commit, which is what caught the
  float-mantissa subclass (§1.1).

---

## 10. ADDENDUM 2026-08-12 — the rewrite tooling already existed, and it was unsafe

This finding was written as though a rewrite lane would be built from scratch. It
would not have been: **`.github/workflows/cleanup-large-blobs.yml` already
exists** — a `workflow_dispatch`-only history rewriter that strips superseded
blob versions under `data/raw/` and `results/calibration/` while protecting
everything live at `main`'s tip. It was missed by the original sweep because §5.1
asked only whether `.github/` *pins* a SHA, not whether anything in `.github/`
*rewrites* them.

It carried the §3.3 defect exactly as predicted:

```
git filter-repo --strip-blobs-with-ids "$REMOVABLE_SHAS" --force
```

No prune flags, so filter-repo's `auto` defaults applied — and the workflow ends
with `git push --force --tags origin`. It verified per-branch manifests rigorously
and **recorded nothing whatsoever about tags**: they were counted at clone time
and force-pushed at the end, with no check in between.

Reproduced on the workflow's *own* operation (`--strip-blobs-with-ids`, which §3
had not covered — §3.2–§3.3 tested `--invert-paths --path`). A data-intake PR adds
`f.parquet` v1, a later commit supersedes it with v2, and a governance tag pins the
intake merge:

| Configuration | Result |
|---|---|
| Workflow as-was (default prune flags) | **FAIL — tag silently re-pointed to `base`**, an unrelated commit |
| Workflow as patched | **PASS — tag still names the intake merge** |

**Fixed in this lane** (`scratchpad/t4_stripblobs.sh` is the harness):

1. The strip step now passes `--prune-empty never --prune-degenerate never`, with
   a comment recording why they are load-bearing. Cost: emptied commits survive as
   empty commits — commit objects only, so the blob savings are unchanged.
2. The protect step records a **per-tag identity** (author/email/date/subject hash)
   plus the target's out-of-scope tree hash.
3. `Verify branch integrity` is now `Verify branch and tag integrity` and fails the
   run — before any push — if a tag vanished, was re-pointed, or had out-of-scope
   content change at its target.

**This changes §8's arithmetic in one direction only.** Today's calibration prune
(85 bundle dirs, 240 MB) makes those blobs *superseded*, so this workflow can now
reclaim them from history — that is a genuine, targeted shrink that does **not**
require the full untrack-`data/raw` rewrite this finding recommends against, and
it never rewrites a blob that is live at tip. The NO-GO in §8 stands for the
wholesale rewrite; this narrower tool is a different, smaller proposition.

### 10.1 The tag check alone was not enough — it verified an empty set

The fix above protects *tags*. **Zero `cite/*` tags are published**, so as first
written it verified an empty set: the workflow would still have been free to
prune the very commits the evidence record cites. And publishing the tags is not
available to an agent lane — beyond the four transports in §5.2, the MCP GitHub
server was checked and exposes **no tag- or ref-creation tool at all**
(`create_branch` only branches from a branch tip, so it cannot pin 104 historical
commits).

So the protection was made **independent of whether any tag exists**, using the
one artifact that is already committed and therefore always present:
`docs/governance/citation-tags.json`.

- **Protect step** — reads the manifest from `main` and records the
  author/email/date/subject identity of all 104 load-bearing commits.
- **Verify step** — resolves each through filter-repo's `commit-map`. Mapping to
  all-zeros means *pruned*, which **fails the run before any push**; otherwise the
  new commit's identity must match. Absent from the map means untouched.
- It also writes **`citation-commit-map.txt`**, the old→new translation for the
  load-bearing set — which discharges §8 precondition 3 in the only form that
  survives the runner, and is the sole artifact that can turn a pre-rewrite
  citation into a post-rewrite SHA.

Verified on a synthetic repo **with zero tags present**
(`scratchpad/t5_manifest.sh`), a load-bearing data-intake PR merge named in the
manifest:

| Configuration | Result |
|---|---|
| Pre-fix workflow | **DETECTED — load-bearing commit pruned; run aborts before push** |
| Patched workflow | **PASS — survives with identity intact** |

Note what the two halves now do. The **manifest** check is the safety net: it
cannot make a citation resolve, but it guarantees no cited commit is silently
destroyed, and it works today. The **tags** remain the only thing that makes a
citation *resolvable by name* after a rewrite — so §8 precondition 1 still binds
for the full rewrite, and `citation-tags.json` is now load-bearing for this
workflow: deleting or emptying it silently removes the protection (the step warns,
it does not fail).

One precondition remains before anyone dispatches this workflow: the
`HISTORY_REWRITE_PAT` secret.

---

**Mid-lane base movement (reported per the charter's standing clause):**
`origin/main` advanced from `f6381c5` (charter) to `1526109` (session start) to
`17e9ad5` (fetched and fast-forwarded before any measurement). This lane ran no
solves, and **every measurement in this document was taken at `17e9ad5` or
later** — none predates the move, so none needed re-verification. The branch was
fast-forwarded, never rebased.
