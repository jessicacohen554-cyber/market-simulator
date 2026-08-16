# `cite/*` — durable citation handles

**Established:** 2026-08-12 (REWRITE-PREP lane) · **Status:** convention defined,
tag set computed and committed, **publication blocked** on credentials (§5).
**Evidence:** `docs/FINDING-rewrite-prep-2026-08-11.md`.

> **2026-08-16: the rewrite this doc prepared for HAPPENED — with zero tags
> published** (owner decision superseding Addendum AQ; run 31955205445;
> `docs/FINDING-history-rewrite-2026-08-16.md`). The manifest leg (§4) carried
> the protection: all 104 load-bearing commits survived, 95 under NEW shas.
> **The old→new translator is `docs/governance/citation-commit-map.txt`** —
> see §8. Every `oid` in `citation-tags.json` is a PRE-rewrite sha; translate
> before resolving. The tags remain unpublished and must be (re)generated
> against post-rewrite shas when they are.

## 1. The problem this solves

This repo's governance model is citation-based — *cite, never re-derive*. Rule 28
`[R-MECH-MATRIX]` requires an evidence citation per mechanism cell; keeper shards
cite the commits behind a promotion; handoffs cite the commit a result must be
reproduced at. **1,611 commit-SHA citations across 251 files** carry that record.

A history rewrite (filter-repo, BFG) assigns every commit a new SHA. Every one of
those citations silently becomes a dead reference — no error, no warning, no
detectable breakage. The evidence record would still *read* fine and be
unusable.

A **tag name** survives where a raw SHA does not: filter-repo rewrites refs,
tags included, onto the rewritten commits. The name is stable across the
rewrite; the SHA it resolves to changes underneath it. Verified empirically —
not assumed — in `docs/FINDING-rewrite-prep-2026-08-11.md` §3.

## 2. The namespace

```
cite/<slug>
```

Rules:

1. **The slug is semantic and SHA-free.** `cite/fh5-src-pin`, not
   `cite/3ae7465`. The whole point is a name that outlives the SHA; embedding
   the SHA in the name reintroduces the thing being routed around.
2. **Prefix by what makes the commit load-bearing** (§3), so the namespace is
   self-describing when listed:
   - `cite/gov-*` — governance record or named incident (LB-2, LB-4)
   - `cite/mx-*` — rule-28 mechanism-matrix evidence (LB-3)
   - `cite/repro-*` — reproduction pin or byte-identity proof (LB-1, LB-5)
   - *no prefix* — hand-named anchors whose importance is not their own commit
     subject (`cite/fh5-src-pin`, `cite/lost-edit-matrix-union`)
3. **Annotated, never lightweight.** The tag message is the self-documentation:
   what is pinned, why it is load-bearing, and every file:line that cites it.
   A lightweight tag survives a rewrite equally well but carries no record.
4. **Tags are append-only.** Never retarget or delete a published `cite/*` tag —
   it is a citation, and a citation that silently changes meaning is worse than
   one that breaks loudly.

## 3. What earns a tag

A citation is **load-bearing** if breaking it breaks a reproduction, a
governance determination, or an audit trail — as opposed to a narrative aside
("landed at `abc1234`"), which a rewrite degrades to a dead link rather than to
broken work.

| Code | Criterion |
|---|---|
| LB-1 | **Reproduction pin** — a session reproducing a published result must check out this state |
| LB-2 | **Governance record** — cited in a keeper shard, `calibration-complete.json`, or `docs/governance/` |
| LB-3 | **Rule-28 audit trail** — cited as evidence in a mechanism-matrix cell |
| LB-4 | **Named incident** — the commit *is* the subject of standing rule guidance |
| LB-5 | **Integrity proof** — cited in a byte-identity / blob-verification table |

Measured at 2026-08-12: **560** distinct commits are cited; **104** are
load-bearing under these criteria; the other **456** are narrative asides.

## 4. The manifest

`docs/governance/citation-tags.json` is the machine-readable tag set — one entry
per commit with its full OID, proposed slug, LB reasons, and every citing
file:line.

> **This file is load-bearing — do not delete or empty it.**
> `.github/workflows/cleanup-large-blobs.yml` reads it to protect every
> load-bearing commit during a history rewrite, resolving each through
> filter-repo's `commit-map` and **failing the run before any push** if one was
> pruned. That protection works with zero tags published, which is the current
> state. If the file goes missing the workflow only *warns*, so its absence
> silently removes the safety net.

Regenerate the underlying inventory with:

```
python3 scripts/audit_citation_tokens.py
```

which classifies **every** hex token in the citation corpora against the object
database into: real commit SHA · 16-char runtime cache key · blob/tree hash ·
other identifier · numeric false positive.

> **16-char tokens are runtime/config cache keys, not SHAs** (e.g.
> `603c2498bf71d21d`). They are content hashes of a resolved config and survive a
> rewrite untouched. **Any transformation that touches one is a defect.** Verified
> 2026-08-12: zero of the 445 sixteen-char tokens resolve as git objects, so the
> separation is clean. Bound any regex over this corpus to lengths {7,8,40}.

## 5. Applying the tags

```
python3 scripts/apply_citation_tags.py          # create locally (dry run of push)
python3 scripts/apply_citation_tags.py --push   # create and publish
```

**This requires push rights on `refs/tags/*`, which Claude Code sessions do not
have** — the agent proxy refuses tag pushes with HTTP 403 (git transport and
GitHub Git Data API alike; four paths tested, §6 of the finding). The tags must
be published by the owner or a lane holding elevated credentials. Until then the
manifest is committed and the names are deterministic, so the tag set is one
command away from existing.

## 6. Preconditions on any future rewrite

Tags are necessary but **not sufficient**. A rewrite must run with:

```
--prune-empty=never --prune-degenerate=never
```

**Without both flags, tags silently lie.** filter-repo's default is to prune a
commit its filter empties, and to prune a merge whose parents collapse — and it
then moves any ref pointing there to the nearest surviving ancestor. The tag
still resolves; it resolves to the *wrong commit*, with no error. Since this
repo merges via PR merge commits and a data-intake PR touches only `data/raw`,
a `data/raw` filter turns exactly those merges degenerate — the common case,
not a corner case. Both behaviours were reproduced and both flags verified as
the fix (finding §3.2–§3.3).

## 7. Citation style

Cite the tag **alongside** the SHA, never instead of it:

```markdown
`3ae7465` (tag `cite/fh5-src-pin`)
```

The SHA stays correct until a rewrite happens and remains the more precise
reference today; the tag is the survivor. Where a **tree or blob hash** is
available it is stronger than both — content-addressed hashes are invariant
under any rewrite that does not change the content itself, so a `src/` tree hash
survives a `data/raw` strip unconditionally. Prefer it for byte-identity claims.

## 8. The 2026-08-16 rewrite — pre→post sha translation

The 2026-08-16 history rewrite (run 31955205445; full record and honest-cost
measurement: `docs/FINDING-history-rewrite-2026-08-16.md`) assigned new shas to
essentially every commit after 2026-05-16. **`docs/governance/citation-commit-map.txt`
is the committed translator for the 104 load-bearing commits** of this
manifest: one `old_sha new_sha` pair per line (the final 9 self-map — they are
refs/pull-only commits the rewrite never touched), `#` lines are provenance.

```
awk -v o=<old-40-char-sha> '$1 == o {print $2}' docs/governance/citation-commit-map.txt
```

Notes for consumers:

- The workflow's own runner-side `citation-commit-map.txt` and the full
  filter-repo commit-map were never archived; the committed file is a
  RECONSTRUCTION (unique author-date+subject identity match against the
  post-rewrite history, 95/95 unique, cross-checked against run #18's verify
  log). Non-manifest citations (~700 distinct commits, ~2,400 occurrences)
  have **no translator** and are dead links — the priced §5.4 loss.
- **Short pre-rewrite citations can now silently lie**: `00abb60` (cited in
  pre-rewrite docs for a dead #4008-era commit) prefix-resolves to the
  rewritten main tip `00abb60fd4…`, a different commit. Check a citation's
  date against 2026-08-16 before trusting what a 7-char prefix resolves to.
