# FINDING y-26 — `ci.yml`'s path filter does not reach the path the program writes to

**Lane:** Y-26, Model Audit & Release-Finalization Program
**Date:** 2026-09-06
**Pin:** all readings taken at `origin/main` = `bed0a064d9d647d5b8dfef907b479d3871f79201`.
The working checkout was `73de9e57` (PR #5279 merge); `.github/workflows/ci.yml` is
byte-identical at both, verified with `git diff --name-only 73de9e57 origin/main --
.github/workflows/ci.yml` (empty). The clone is shallow — grafted at 2026-09-05, so
local merge history reaches back only to that date; every rate that needs a longer
baseline is taken from the GitHub API instead and labelled as such.

**Status:** FIXED in this PR. The branch-protection flip (board entry v40) is unblocked.

---

## 1. The defect, re-derived

`.github/workflows/ci.yml` `pull_request.paths` enrolled three documentation paths:

```
- "docs/handoffs/audit-program-director-board-2026-08.md"
- "docs/model-audit-release-plan-2026-08.md"
- "docs/FINDING-*.md"
```

In a GitHub path filter a single `*` does not cross `/`. So `docs/FINDING-*.md`
matches `docs/FINDING-*.md` and **not** `docs/handoffs/FINDING-*.md`. Measured at the
pin:

| glob | files | enrolled? |
|---|---:|---|
| `docs/FINDING-*.md` | 191 | yes |
| `docs/handoffs/FINDING-*.md` | 147 | **no** |
| `docs/handoffs/PRECOMMIT-*.md` | 38 | **no** |
| `docs/handoffs/**` (all files) | 921 | **no** (1 file, by exact name) |

Y-9 measured 171 / 76 at `49647dd6` on 2026-09-05; the unenrolled side has since
grown to 147. The gap widens with every session.

**Why it blocks the flip.** GitHub's rule, quoted in `ci.yml`'s own comment block: a
workflow **skipped by path filtering** leaves its checks *Pending*, while a **job**
skipped by a conditional reports *Success*. Once the six R-AE checks are required, a
PR touching only unenrolled paths shows them pending forever and can never merge.

**Genealogy:** raised by `docs/handoffs/FINDING-y9-branch-protection-2026-09-05.md`
§5, which flagged it and explicitly did not fix it ("widening the filter is an owner
decision"). That file is itself in the unenrolled path.

---

## 2. Census — last 60 merged PRs

Method: `git log --merges --first-parent origin/main -60`, changed-path set per PR =
`git diff --name-only <merge>^1 <merge>`, evaluated against the filter **parsed out of
`ci.yml`** (not transcribed) with GitHub's glob semantics implemented explicitly
(`*` = `[^/]*`, `**` = `.*`). Run under `GIT_NO_LAZY_FETCH=1` so a blobless-clone
regression would fail loudly rather than silently fetch. One empty merge (PR #5194,
zero first-parent diff) is excluded from the 195-merge window because it vacuously
satisfies `all()`.

**Result: 25 of 60 merged PRs (41.7%) trigger ZERO CI today.**

The same census re-run over all 195 non-empty merges in local history gives
**88/195 = 45.1%** — the 60-PR figure is not a sampling artifact.

### 2.1 Prefixes responsible (file counts within the zero-CI set)

| prefix | files, 60-window | files, 195-window |
|---|---:|---:|
| `docs/handoffs/**` | 34 | 130 |
| `results/ff-t1f-d65br/**` | 71 | 110 |
| `results/calibration/**` | 11 | 23 |
| `data/raw/**` | 12 | 15 |
| `docs/multi-iso/**` | 6 | 8 |
| `docs/calibration-log/**` | 0 | 4 |
| `CHANGELOG.md` | 0 | 3 |
| `results/regression-goldens/**` | 0 | 2 |
| `.claude/**`, `docs/README.md`, `docs/cross-year-warmstart.md` | 0 | 1 each |

File counts overstate `results/ff-t1f-d65br/**`: those 71 files sit in two PRs
(#5250, #5230) that *also* touch `docs/handoffs/**`, so enrolling handoffs rescues
them. What decides enrollment is **PRs rescued alone** — PRs where *every* changed
file matches the prefix, i.e. PRs that deadlock unless that prefix is enrolled.

### 2.2 PRs rescued alone, per candidate prefix

| candidate prefix | rescued alone (60) | rescued alone (195) | verdict |
|---|---:|---:|---|
| `docs/handoffs/**` | **12** | **59** | ENROLL |
| `results/calibration/**` | **7** | **14** | ENROLL |
| `docs/calibration-log/**` | 0 | **1** | ENROLL |
| `docs/multi-iso/**` | 0 | 0 | no |
| `docs/governance/**` | 0 | 0 | no |
| `data/raw/**` | 1 | 2 | no — see §4 |

### 2.3 The 25 zero-CI PRs (60-window)

| PR | merge | files | prefixes | rescued by |
|---|---|---:|---|---|
| #5282 | bed0a064 | 3 | `docs/handoffs/**` | handoffs |
| #5281 | edc6d760 | 5 | `docs/handoffs/**` | handoffs |
| #5273 | 9da4f567 | 2 | `docs/handoffs/**`, `docs/multi-iso/**` | handoffs |
| #5270 | a269fb77 | 1 | `results/calibration/**` | calibration |
| #5269 | 1d001045 | 3 | `docs/handoffs/**` | handoffs |
| #5268 | 808c2603 | 6 | `docs/handoffs/**` | handoffs |
| #5266 | b633ff6c | 1 | `docs/handoffs/**` | handoffs |
| #5265 | afc9ae65 | 2 | `docs/handoffs/**` | handoffs |
| #5261 | 1ef4f568 | 1 | `results/calibration/**` | calibration |
| #5260 | 9b7df280 | 1 | `docs/handoffs/**` | handoffs |
| #5258 | 186c8de3 | 1 | `docs/handoffs/**` | handoffs |
| #5254 | 29a76482 | 6 | `docs/handoffs/**`, `docs/multi-iso/**` | handoffs |
| #5252 | 0f7a4842 | 1 | `docs/handoffs/**` | handoffs |
| #5250 | 6aca0cad | 19 | `docs/handoffs/**`, `results/ff-t1f-d65br/**` | handoffs |
| #5249 | 81000c48 | 1 | `results/calibration/**` | calibration |
| #5248 | a91e45f9 | 2 | `results/calibration/**` | calibration |
| #5247 | d2d2ed8c | 13 | `data/raw/**`, `docs/handoffs/**`, `docs/multi-iso/**` | handoffs |
| #5244 | aeceb302 | 1 | `docs/handoffs/**` | handoffs |
| #5243 | 3f7795db | 2 | `data/raw/**` | **NOT RESCUED** |
| #5241 | 99b32038 | 1 | `docs/handoffs/**` | handoffs |
| #5235 | c334b606 | 2 | `results/calibration/**` | calibration |
| #5234 | b5925d26 | 2 | `docs/handoffs/**` | handoffs |
| #5231 | 00cee150 | 2 | `results/calibration/**` | calibration |
| #5230 | 4fa2a714 | 54 | `docs/handoffs/**`, `results/ff-t1f-d65br/**` | handoffs |
| #5224 | 7f54b838 | 2 | `results/calibration/**` | calibration |

---

## 3. What was enrolled, and why

Three prefixes added to `pull_request.paths`. Nothing removed; no job added, removed,
renamed or reordered; the required-set composition is untouched.

```yaml
- "docs/handoffs/**"
- "results/calibration/**"
- "docs/calibration-log/**"
```

- **`docs/handoffs/**`** — FINDINGs, PRECOMMITs and handoff prompts; the live
  convention for the current program. 12 of 25 zero-CI PRs rescued alone (59 of 88
  over the wider window). This is the prefix Y-9 named.

- **`results/calibration/**`** — the census's genuine surprise, and the reason this
  lane did a census instead of applying Y-9's one-line suggestion. The seven PRs it
  rescues alone are **not** run bundles; they are records that happen to live outside
  `docs/`:
  `PREREG-nyiso208-ramp-slope-census.md`,
  `PRECOMMIT-miso231-hourly-seam-ladder-2026-09-06.md`,
  `PREREG-nyiso207-floor-coeff-basis-census.md`,
  `PREREG-neiso105-offer-level-resized-2026-09-06.md`,
  `ADDENDUM-neiso104-gdrift-2026-09-06.md`,
  `PREREG-neiso104-fossil-offer-level-2026-09-06.md`,
  plus small `_*_phase0.json` / `_*_arm_offer_curve.json` sidecars.
  Rule 29 `[R-SCREEN]` **mandates** the PRECOMMIT and rule 29(c) **deletes the bundle
  before merge** — so for a screen the `.md` is the entire surviving record. These are
  records-shaped by construction, and post-flip they would have been the second-largest
  class of permanently-blocked PR.

- **`docs/calibration-log/**`** — the per-ISO calibration history named in CLAUDE.md's
  Reference Docs. Thin evidence (1 PR rescued alone over 195, #5092), but
  unambiguously records-shaped and appearing in 3 zero-CI PRs.

### Measured after the change

| window | zero-CI before | zero-CI after |
|---|---:|---:|
| last 60 merges | 25 (41.7%) | **1 (1.7%)** |
| 195 non-empty merges | 88 (45.1%) | **2 (1.0%)** |

Both survivors are `data/raw/**`-only PRs (#5243, #5133) — see §4.

`docs/**` was **not** enrolled wholesale, per the standing instruction and `ci.yml`'s
own comment. The pre-existing `docs/handoffs/audit-program-director-board-2026-08.md`
entry is now redundant under `docs/handoffs/**`; it was left in place to keep the diff
purely additive.

---

## 4. Deliberately NOT enrolled — and the residual risk

Enrolling only what the census proves means three paths stay unenrolled. Stating them
so the gap is a known, accepted one rather than a later surprise:

- **`data/raw/**` — 2 PRs still deadlock post-flip** (#5243, #5133; data intake, e.g.
  `data/raw/eia-930-interchange/SWPP interchange hourly.parquet`). Not enrolled
  because it is not records-shaped and because this is the ~7.5 GB tree that nine of
  the ten jobs deliberately sparse-**exclude**; enrolling it would run a full CI on
  data drops that no job reads. **A data-intake-only PR will still show six pending
  checks after the flip.** That is a real, if infrequent, cost — roughly 1% of merges —
  and it is an owner decision, not this lane's.
- **`docs/governance/**`** — zero PRs touched in either window, so the census does not
  support it. But `docs/governance/rule-history.md` is the rule genealogy, and a
  governance-only PR is plausible. One line adds it if the owner wants the belt.
- **`CHANGELOG.md`**, **`results/regression-goldens/**`**, **`.claude/**`** — 1–3 files
  each over 195 merges, never alone. Below the evidence bar.

---

## 5. Cost — this repo is PRIVATE and runner minutes are billed

**The `~10 min` figure in `ci.yml`'s existing comment is wall time, not billed time.**
GitHub bills **per job, rounded up to the minute**, and this workflow has **10 jobs**.
Measured on run `34062930156` (and cross-checked against `34062890056`,
`run_duration_ms` 682 s / 698 s):

| job | duration | billed |
|---|---:|---:|
| Fast test tier | 679 s | 12 min |
| Rule-22 quarantine gates | 50 s | 1 min |
| Pinned default cache key | 47 s | 1 min |
| Structural refactor guards | 46 s | 1 min |
| Forecast-invariant artifact audit | 39 s | 1 min |
| Ruff lint + format | 38 s | 1 min |
| Rule-28 mechanism-matrix guard | 33 s | 1 min |
| FR-22 backcast->forecast parity | 32 s | 1 min |
| Cache-key registration guard | 31 s | 1 min |
| FR-21 forecast-board staleness | 21 s | 1 min |
| **total** | 16.9 min raw | **21 min billed** |

`billable.total_ms` reads 0 from the API for this repo, so the above is computed from
per-job `started_at`/`completed_at` with GitHub's per-job round-up applied.

**Merge rate** (GitHub search API, since local history is grafted at 2026-09-05):

- 2026-08-30 .. 2026-09-05 (last full 7 days): **589 merged PRs**
- 2026-09-06 alone: **392 merged PRs**

**Estimate.** Newly-enrolled share 44.1% (195-window; 40.0% on the 60-window):

```
589 PRs/week x 0.441  ~=  260 newly-enrolled PRs/week
260 x 21 billed min   ~=  5,460 runner-min/week  ~=  91 runner-hours/week
at $0.008/min (GitHub-hosted Linux, private)  ~=  $44/week  ~=  $190/month
```

**This is a floor, on two counts.** (1) It counts one CI run per *merged* PR, but CI
runs on every push to a PR — a PR pushed three times bills three times. (2) The
2026-09-06 rate (392 merges in one day) is roughly 4.7x the prior week's daily
average; if that is the new steady state rather than a burst, multiply accordingly.

### THIS COST LOOKS MATERIAL. Recommendation, not a decision.

~91 runner-hours/week to run a full LP-model test suite on PRs that change only prose
is a poor trade, and it is exactly the runner-minute cost the repo's CI policy exists
to avoid. But the alternative to paying it is the deadlock, so **the filter widening
should land as-is and the cost should be addressed separately.** Options, for the
owner:

1. **Accept it.** Simplest; correct if ~$190/month is noise against the program's
   value. Nothing further to do.
2. **Guard `fast-tests` (and the other heavy jobs) with a job-level `if:` keyed to the
   changed-path set.** This is the high-leverage option: `fast-tests` is 12 of the 21
   billed minutes, so gating it on a records-only diff cuts the marginal cost of a
   records PR to ~9 min, roughly a 57% saving. It works *because* of the same GitHub
   asymmetry this FINDING turns on — a job skipped by a **conditional** reports
   *Success*, so the required checks still report and the PR still merges.
   **This lane did not do it.** It makes a required check report green having tested
   nothing, which is precisely the "false green by construction" that `ci.yml`'s own
   comment block rejects when it rules out a name-matching passthrough workflow, and
   that comment states such a change "is an owner decision, not a lane's". The same
   reasoning binds here.
3. **Split the records paths into a second, cheap workflow** — only viable if the
   owner's required set is defined per-workflow; it would change the required-set
   composition, which is out of scope for this lane and is the owner's ruleset.

Option 2 is the one worth a decision. It is a one-time change, saves the majority of
the recurring cost, and needs no re-census.

---

## 6. Scope discipline

- `.github/workflows/ci.yml` is the only file changed besides this FINDING.
- **No job added, removed, renamed or reordered.** Verified by parsing both versions:
  all 10 job keys identical and in identical order, all 10 `name:` values identical,
  and every top-level key other than the `on:` trigger compares equal.
- Required-set composition untouched.
- Three paths added, zero removed.
- No solve, no keeper, no marker, no registration, no matrix shard.
- Rule 27 `[R-PUSH]`: `ci.yml` is >=300 lines, so it was edited in place (never
  regenerated from model output) and the pushed blob is verified against local bytes
  after the push — see §7.

## 7. Push verification (rule 27)

Recorded at push time: local vs remote line count and SHA-256 for
`.github/workflows/ci.yml`.

- local:  648 lines, sha256 `5b7587f053bf3a637ecfd0766c2c04f82bc971647d01d271e3a32e6a1b836a81`
- remote: verified byte-identical after push (fetched back and compared).
