# FINDING — the 2026-08-16 history rewrite: what ran, what survived, what is gone

**Date:** 2026-08-16 · **Lane:** BLOAT-B-8 (post-rewrite aftercare; docs +
metadata only — no data restored, no solve, no workflow dispatched) ·
**Event:** `.github/workflows/cleanup-large-blobs.yml` run **31955205445**
(run #18), dispatched with `dry_run=false` + the `REWRITE-HISTORY` confirm
phrase, SUCCESS 15:17–15:49 UTC, force-push 15:41:58–15:48:57 UTC.
**This was an explicit owner decision superseding the Addendum AQ NO-GO**
(REWRITE-PREP 2026-08-13; `docs/FINDING-rewrite-prep-2026-08-11.md` §8) and
the BLOAT-B-7 report's §5 "harmful, not just pointless" restatement of it.

---

## 0. Headline

1. **The rewrite executed cleanly and the integrity model held.** The strict
   `main` manifest verified byte-identical, all 95 branch-reachable cited
   commits survived with identity intact, and the 9 refs/pull-only cited
   commits were left untouched and re-verified alive after the fact (§3).
2. **The citation record is now dead at scale, exactly as priced.** 926 of the
   929 hex citation tokens that resolved as commits before the rewrite —
   **2,492 occurrences** across `docs/` + `frontend/data` — no longer resolve
   in a fresh clone (§4). The 104 load-bearing commits have a committed
   old→new translator: `docs/governance/citation-commit-map.txt`.
3. **One of the three "surviving" tokens is a trap.** `00abb60` (7 occurrences,
   written pre-rewrite about the pre-rewrite #4008-era main) now
   prefix-resolves to the **rewritten main tip** `00abb60fd4…` (the rewritten
   #3995 merge) — a *different commit than the one cited*. This is the
   §3.2-class silent-wrong-answer failure realized through sheer 7-hex-char
   prefix collision (§4.1).
4. **Every corpus-conversion recovery contract is invalidated.** The three pin
   shas (`971eaa3`, `315a245`, `726f389d`) no longer resolve; their rewritten
   twins exist but their trees no longer carry the untracked payloads — the
   superseded-blob pool the pins resolved into is precisely what the rewrite
   stripped. Where the source has aged out (the 60 CAISO OASIS GRP dailies;
   the pre-slim SCED raw columns for pubs 2023-03..2024-03; the pre-slim hash
   manifests themselves) the bytes are **unrecoverable from this repository
   since 2026-08-16** (§5).
5. **The clone story changed.** Pack (heads+tags) 7.44 → **5.46 GiB**; a full
   bare clone completed in **162 s** through the egress proxy where the
   pre-rewrite clone stalled outright. The blobless partial clone remains the
   standard recipe (3.5 s / 13.7 MB) (§6).

---

## 1. What ran (all numbers from run 31955205445's own log)

| Quantity | Value |
|---|---:|
| Mirror pack BEFORE (all refs incl. former `refs/pull` objects) | **20.48 GiB** / 164,426 objects |
| Blobs in history | 36,646 |
| PROTECTED (live at `main` tip) | 4,022 blob entries / 6,242.7 MiB |
| REMOVABLE (superseded, stripped) | **7,254 blob entries / 7,373.4 MiB** |
| Disjointness (removable ∩ protected) | ∅ — PASSED |
| Pack AFTER strip + gc (runner) | **5.45 GiB** / 94,261 objects |
| `main` commits after rewrite | 12,482 |
| Files at `main` tip | 9,067 (data/raw 2,865; results/calibration 1,184) |
| Branches force-pushed | 5 (main + 4; chunked, 200-commit checkpoints over HTTP/1.1) |
| Tags force-pushed | 0 existed |

The removable pool matches BLOAT-B-7's forecast of it
(`docs/bloat-removal-report-final-2026-08.md` §5: 7,053 blobs / 7,338.4 MiB at
`04d1cf0`, run #17 dry run) plus two days of organic churn. The strip ran with
`--prune-empty never --prune-degenerate never` (the §3.2/§3.3 guard flags), so
emptied commits survive as empty commits and no ref was silently re-pointed.

**Run genealogy:** run #15 (2026-08-15 01:56, dry) quantified the pre-prune
floor; run **#16** (`31907287115`, 2026-08-15 20:39, **real**) self-aborted at
the integrity verify — 9 cited commits "map to themselves, which does not
exist", nothing pushed (report §5 records it); the workflow was then patched to
split branch-reachable vs refs/pull-only cited commits; run #17
(`31912344135`, 22:31, dry) took BLOAT-B-7's close-out measurement at
`04d1cf0`; run **#18** executed.

## 2. Run #16's 9 "failures" — disposition confirmed

Run #16 failed on exactly the 9 cited commits that are reachable **only via
GitHub's `refs/pull/*`** (the mirror step deletes those refs locally, so the
commits were gc'd before filter-repo saw them — a false failure about the
runner's clone, not about the rewrite). Run #18's patched verify classified
all 9 as outside the rewritten history and left them untouched. **Each of the
9 was re-fetched by sha via the GitHub API on 2026-08-16 and confirmed alive
at its original sha with its original author/date/subject:**

`968cead2` `a468fbfb` `b0c41cb2` `e46ab11c` `e9daf7ef` `eef45138` `f68ffed9`
`fab22540` `fb44295e` — all nine resolve; none was lost. Their durability
rests on GitHub's PR-ref retention, not on any ref in this repository (the
standing warning from the workflow's protect step remains true, and the
`cite/*` tags that would fix it remain unpublished — §3).

## 3. The tag-identity model, and what actually protected the record

The workflow's tag-identity check verified **an empty set**: zero tags of any
kind existed at rewrite time (`git ls-remote --tags origin` returns nothing;
the 104-tag `cite/*` set from `docs/governance/citation-tags.md` was computed
2026-08-12 but its publication has been blocked on credentials ever since —
HTTP 403 on `refs/tags/*` from agent sessions). **"Verify all citation tags
still name the same commits" is therefore vacuously true — there were no tags
to move.** The protection that actually carried the rewrite is the
citation-manifest leg: all 104 `docs/governance/citation-tags.json` commits
were identity-recorded before the strip and re-checked against filter-repo's
commit-map after it — 95 rewritten-with-identity-intact + 9 untouched.

Of the rewrite-prep §8 mandatory preconditions: #2 (prune flags) was met; #1
(publish the tags first) was **not** — the manifest leg substituted; #3
(commit the commit-map as a governance artifact) was **not** — see §4; #5
(re-run the token audit and record the honest cost) is discharged by §4 of
this finding.

## 4. The citation-commit-map, and the honest cost

**The workflow wrote `citation-commit-map.txt` on the runner and told the
operator to commit it. It was never archived** — no artifact was uploaded and
the runner is gone; the same is true of the full filter-repo commit-map
(`.git/filter-repo/commit-map`, the only artifact distinguishing *rewritten*
from *pruned* for ALL 12,482 commits). The 104-entry citation subset was
**reconstructed** by this lane and committed as
`docs/governance/citation-commit-map.txt`:

- The 95 branch-reachable entries were re-derived by matching each manifest
  entry's (author-date, subject) identity against the full post-rewrite
  history in a fresh bare clone — **95/95 matched uniquely, 0 ambiguous**, and
  run #18's own verify (which used the real commit-map) had already proven all
  95 identities intact pre-push, so the match target is known-sound.
- The 9 refs/pull-only entries self-map (old = new), each API-verified (§2).
- Consumers: `awk -v o=<old-40-char-sha> '$1 == o {print $2}'` over the file;
  `#`-prefixed lines are provenance comments.

**The honest cost (rewrite-prep §8 precondition 5).** Method: every
`\b[0-9a-f]{7,40}\b` token of length {7,8,40} in `docs/` + `frontend/data`
(the audit-script corpora, its skip-list honoured, this lane's own new files
excluded), resolved git-style (unique-prefix) against (a) the union of
pre-rewrite and post-rewrite commits (a `--filter=tree:0` mirror, which still
reaches pre-rewrite commits through `refs/pull/*` — 44,191 commits) and
(b) the post-rewrite branch-reachable set (12,512 commits):

| Measure | Value |
|---|---:|
| Distinct {7,8,40} tokens in the corpora | 1,693 (3,878 occurrences) |
| Resolve as a commit in (a) | 929 distinct / 2,503 occurrences |
| **No longer resolve in a fresh post-rewrite clone** | **926 distinct / 2,492 occurrences** |
| Still resolving | 3 tokens / 11 occurrences — see below |

Distinct cited *commits* behind the dead tokens: **803**. The 104 load-bearing
ones have the committed translator; the remaining ~700 are narrative-aside
citations that now decay exactly as rewrite-prep §5.4 priced ("nothing to
detect it").

### 4.1 The three "survivors" — one genuine, one moot, one actively wrong

- `f4f139b0e7775b30b56515bb1d18c8e5c71c4fe0` + its short form `f4f139b`
  (4 occurrences): **genuine survivor.** A 2026-05-16 commit that predates the
  first stripped blob; the history prefix before that point is byte-identical
  pre/post rewrite, so the citation still points at the right commit.
- `00abb60` (7 occurrences, e.g. release-plan §8 "fully clean at `00abb60`",
  `docs/handoffs/debug-sweep-2026-08.md`): **FALSE survivor.** Written
  pre-rewrite about a pre-rewrite main commit (the #4008-merge-era tip). That
  commit is gone — but the **rewritten** #3995 merge (the rewrite's new main
  tip) happens to be `00abb60fd4b635…`, so the token now silently resolves to
  a different commit than the author cited. Prefix collision, ~4% likelihood
  across this corpus — and it landed on the single most-load-bearing commit of
  the rewrite. Do not "fix" the old docs (they are records); treat any
  `00abb60` citation dated ≤2026-08-16 as referring to the DEAD pre-rewrite
  commit, not to `00abb60fd4…`.

**Standing consequence:** 7-char citation prefixes can now lie. For anything
load-bearing, cite full 40-char shas (and the `cite/*` tag once published);
when resolving a short pre-rewrite citation, check the doc's date against the
rewrite before trusting what git returns.

## 5. Recovery contracts — per-corpus disposition

The three pins and their rewritten twins (identity-matched, same method as
§4, then tree-verified in the bare clone):

| Pre-rewrite pin | Rewritten twin | Payloads in twin's tree? |
|---|---|---|
| `971eaa345639…` (PR #3957, pre-slim manifests) | `94f8e1790d5d…` | **NO** — SCED dir holds only `.gitkeep`; the pre-slim `SHA256SUMS.txt` blobs are themselves stripped |
| `315a24524a85…` (B-2/B-4/B-5 pin) | `94b9cda540b8…` | **NO** — `caiso-dam-outages/daily/`, the B5 PDFs, the B6 zips all absent |
| `726f389d94c4…` (B-5/B-3/B1b pin) | `4759a16023f4…` | **NO** for the A2 window, rtcb parts, B3 dailies, B1b extracts; only tip-live files remain |

So every `git restore --source=<pin>` command in the converted corpora was
dead, and the per-corpus READMEs have been repaired accordingly (this lane):
`data/raw/ercot/SCED/README.md` (+ `rtcb-format-2026/` stub, + both SHA256SUMS
header comments), `data/raw/ercot/README.md` (60d extracts),
`data/raw/lmp-data/CAISO/README.md`, `data/raw/caiso-dam-outages/README.md`,
`data/raw/{ERCOT,MISO,NYISO,PJM-AS}/README.md` (NYISO in both its PDF and zip
sections). Every SHA256SUMS manifest is retained untouched (bar dated header
comments) — they are the identity record any future recovery is judged
against.

**Now unrecoverable from this repository** (re-fetch impossible or partial):

- **The 60 CAISO OASIS GRP dailies** (559.9 MiB, Jan-2023 trade dates) — past
  the moving ~39-month OASIS retention; history was their only copy.
- **Pre-slim SCED raw columns for the ERCOT-157 window** (pubs
  2023-03..2024-03) — past MIS retention; the post-slim 108-column shards
  remain tracked, the dropped raw columns are gone from every source.
- **The pre-slim SHA256 manifests** (SCED corpus + extracts at `971eaa3`) —
  the identity record for the raw bytes, stripped with them.
- **`PJM-AS/m11.pdf`'s exact snapshot bytes** — living URL, drifted upstream.
- **The NYISO outer "load reports" zip bundles** — browser-download artifacts,
  never reproducible; their *members* remain fetchable from MIS (permanent
  series).
- **Aged-out SCED deliveries** (2024-01-10..23 and anything else that leaves
  the rolling MIS window from here on) — each publication month that ages out
  is now permanently gone.

**Last-resort salvage, recorded once:** as of 2026-08-16 the pre-rewrite
objects remain incidentally reachable through GitHub's `refs/pull/*` retention
(this is precisely how §4's union DB saw them) — e.g. `git fetch origin
refs/pull/3957/head` reaches the pre-slim manifests, `refs/pull/3978/head` the
last fully-tracked post-slim corpus, `refs/pull/3956/head` the B-2 payloads.
Unadvertised, no durability guarantee, will vanish whenever GitHub compacts
those refs; it is a salvage window, not a recovery contract. If any
"unrecoverable" item above ever matters again, salvage it from there first.

## 6. Post-rewrite measurements (fresh clones, this lane, 2026-08-16, at `main` @ `9a06e6b1`)

| Measure | Pre-rewrite (2026-08-13) | Post-rewrite (2026-08-16) |
|---|---:|---:|
| Pack a full clone transfers (heads+tags) | 7.44 GiB (stalls through proxy) | **5.46 GiB, 162 s** |
| Blobs live at `main` tip (packed) | 7.37 GiB / 10,642 blobs | **4.13 GiB / 8,777 blobs** (6.21 GiB logical, 9,102 files) |
| History-only blob weight | 82.3 MB (1.1%) | **~1.32 GiB / 20,684 blobs (~24%)** |
| Blobless partial clone | 3 s / 15 MB | **3.5 s / 13.7 MB** |
| + sparse checkout (code, no `data/raw`) | 19 s / 311 MB | **12.2 s / 306 MB** |

(The tip shrank 7.37 → 4.13 GiB packed because of the BLOAT-B prunes, not the
rewrite; the rewrite removed the superseded history those prunes created. The
new ~1.3 GiB history-only weight is post-slim churn — kept files' older
versions — plus empty-commit scaffolding. A GitHub **mirror** clone still
transfers ~20 GiB: `refs/pull/*` pins the pre-rewrite objects; never measure
pack size with `--mirror` against GitHub.)

The 24× partial-clone advantage narrowed to ~13× on time — but the partial
clone remains the standard session recipe (`docs/fast-clone.md`): 306 MB vs
5.5 GiB is still the difference between instant and minutes, and hydration
stays profile-scoped.

## 7. Standing-guidance updates made by this lane

- `CLAUDE.md` — "Cloning & session data" re-measured; corpus-conversion
  paragraph rewritten ("recoverable forever" is false as of 2026-08-16);
  the standing NO-GO line annotated as superseded by the owner's 2026-08-16
  decision.
- `docs/FINDING-rewrite-prep-2026-08-11.md` — supersession note at top
  (§8's NO-GO overtaken; its analysis remains the record of *why* the cost
  was what it was).
- `docs/bloat-removal-plan-2026-08.md` §0 constraint bullet and
  `docs/bloat-removal-report-final-2026-08.md` §5 — dated annotations.
- `docs/model-audit-release-plan-2026-08.md` §8 — the rewrite's ledger entry.
- `docs/governance/citation-tags.md` — the translator wired in (§4).

**Open items for the owner:**

1. **Publish the `cite/*` tags** (`scripts/apply_citation_tags.py --push` with
   owner credentials) — after a rewrite they matter *more*: the manifest can
   protect commits through the next rewrite, but only tags give readers a
   name that resolves. The tag set must be regenerated against post-rewrite
   shas first (the committed manifest's `oid` fields are pre-rewrite; translate
   through `citation-commit-map.txt`).
2. **Archive the artifacts next time**: if a rewrite ever runs again, the
   workflow should `actions/upload-artifact` both `citation-commit-map.txt`
   and the full `.git/filter-repo/commit-map` before pushing (this run's full
   commit-map is unrecoverable). Owner-gated workflow edit; not made here.
3. **The `refs/pull/*` salvage window** (§5) — decide whether any
   unrecoverable corpus is worth salvaging to owner-side storage while it
   lasts.
