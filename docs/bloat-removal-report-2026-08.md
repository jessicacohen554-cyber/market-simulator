# Bloat Removal Report — 2026-08 (BLOAT-B-6 close-out)

**Program:** Model Audit & Release-Finalization, WS6 · BLOAT
(`docs/model-audit-release-plan-2026-08.md` §3/WS6). **Session:** BLOAT-B-6,
the plan §8 close-out. **Branch:** `claude/bloat-b6-closeout-g5zi4q`.
**Measured at:** `315a24524a851566c3d32cc88668fa32dcbd1d74` (origin/main,
2026-08-15), compared against BLOAT-A's base `f2de3b0a83a0515567720967642e4ae94378c6d3`.

---

## 0. HEADLINE — the close-out found nothing to close out

**BLOAT-B never executed. No prune PR exists; not one itemized action from
`docs/bloat-removal-plan-2026-08.md` §3–§7 has been performed; the tip has
GROWN, not shrunk.**

| | Plan | Actual at `315a245` |
|---|---:|---:|
| Tip total | 10,080.0 MiB / 11,127 files (base `f2de3b0`) | **10,115.0 MiB / 11,214 files** |
| After PR-1..PR-4 (class-approved) | ≈ 8,110 MiB | **10,115.0 MiB** |
| Recovered | ≈ 1,970 MiB | **0.0 MiB** |
| Net change since BLOAT-A | — | **+35.2 MiB (+87 files)** |

This session's chartered work — quantify the dry run, produce the G3 evidence,
re-measure the recovery — was therefore performed **against an unpruned tip**.
The numbers below are real and useful, but they are a **pre-prune baseline**,
not a post-prune verification. Nothing in this report may be read as G3
evidence that a prune broke nothing, because there was no prune.

**Root cause is sequencing, not failure.** BLOAT-B is a **Wave-3** lane, held
until **G2 + an owner-signed deletion list** (release plan §2 gate table, §4.10:
"BLOAT-B — ⛔ held until G2 + owner-signed deletion list"). The program is still
in **Wave 1**: the §8 ledger's last entry is 2026-08-13, G1 has not been
declared, and G2 — which BLOAT-B waits on precisely so PERF-B's keeper
re-solves are not racing a `results/` prune — is two gates away. This close-out
session was dispatched out of sequence. **No corrective action is needed on the
plan itself; it needs its gates, in order.**

---

## 1. Proof of non-execution (measured, per PR batch)

Method: `GIT_NO_LAZY_FETCH=1 git ls-tree -r -l` over the tip tree, tree-only
reads — the same method as plan §2, re-validated in §3 below.

| PR | Items | Planned recovery | State at `315a245` | Recovered |
|---|---|---:|---|---:|
| **PR-1** | A1 SCED in-place slim + B1a | ≈ 1,545 MiB | `data/raw/ercot/SCED` = **1,025 files / 3,258.0 MiB**, unchanged; shards still 187/188-column raw (unslimmed). The 4 loose `60_DAY_SCED_DISCLOSURE_*` extracts = **208.6 MiB**, present | **0** |
| **PR-2** | B4 xlsx + B5 PDFs + B6 zips + B3 GUID hygiene | 361.8 MiB | `caiso-dam-outages` **1,094 xlsx / 155.0 MiB** present; committed PDFs **38 files / 153.2 MiB** (was 34 / 144.5 — *grew*, see §5); `nyiso load reports N.zip` **4 / 65.2 MiB** present | **0** |
| **PR-3** | C-5.1 non-keeper hourly prunes | 62.7 MiB (class-approved) | Every one of the 19 named bundles still carries its `hourly/`; **`results/calibration/**/hourly/` = 337 files / 137.3 MiB across 30 bundles** (plan measured 92.9 MiB — *grew*) | **0** |
| **PR-4** | D1 + D2 script rotation | ~0 (hygiene) | **83** top-level `gen_*_attestation.py` and **194** top-level `scripts/*.py` — byte-identical to the plan's §6 census. `run_foresight_ab.py`, `run_calibration_eia930.py`, `gen_nyiso130_keeper_ledger.py` all still at top level | **0** |
| **PR-5** | signed-item batch (B3 / B1b / A2) | ≈ 1,989 MiB | Not chartered; `lmp-data/CAISO` = **69 files / 586.6 MiB**, present | **0** |

Corroborating: `mcp__github__search_pull_requests` over the repo returns **six**
bloat-matching PRs, the most recent being **#3938 (BLOAT-A, merged
2026-08-14)** — the read-only plan itself. There is no PR-1..PR-5.

---

## 2. `cleanup-large-blobs.yml` dry run — the standing owner option, quantified

Dispatched **dry-run only**, per the standing NO-GO on history rewrite (owner
decision AQ 2026-08-13; `docs/FINDING-rewrite-prep-2026-08-11.md` §8). The
confirm phrase `REWRITE-HISTORY` was **not supplied** — the dispatch passed
`dry_run=true` with `confirm=DRY-RUN-ONLY-NOT-A-REWRITE`, and the run's own step
record confirms the guard held: **`Validate confirmation` → skipped,
`Validate push token` → skipped, `Strip older blobs with git-filter-repo` →
never reached, `Force push cleaned history` → never reached.**

- Run: `31857841269` (run #15), head `315a245`, dispatched 2026-08-15 01:56 UTC.
- Prior dry run for comparison: `30071768814`, 2026-07-24, success.

<!-- DRYRUN_RESULTS -->

**How to read these numbers.** The workflow's protected set is *blobs live at
the tip of `main`*; everything else in `data/raw/` and `results/calibration/`
history is "removable". Because **no prune ran**, the removable figure here is
**pure historical churn** — superseded versions of files that were replaced or
deleted over the repo's life. It is **not** "what the prunes turned into
reclaim", which is what plan §8 chartered this measurement to produce; that
quantity is unmeasurable until the prunes exist. What this run does establish
is the **pre-prune floor**: any future post-prune dry run's removable total
minus this one is the reclaim attributable to the prune.

This also re-confirms the standing NO-GO's arithmetic from a second angle. The
`docs/fast-clone.md` finding — that 7.37 GiB of the 7.44 GiB pack is **live at
tip**, so a rewrite reclaims ~1% and does not fix clone time — is a statement
about the protected set, and the protected/removable split below is its direct
measurement.

---

## 3. Tip re-measurement (plan §2 method, re-validated)

The plan's method reproduces. Its load-bearing decomposition of `data/raw`,
re-evaluated at `315a245` by evaluating `golden-data-tier.yml`'s non-cone
sparse-checkout globs with gitignore semantics against the tip tree:

| Block | Plan @ `f2de3b0` | This session @ `315a245` |
|---|---:|---:|
| `data/raw` total | 9,766.7 MiB / 4,722 files | **9,780.0 MiB / 4,727 files** |
| Golden-tier-matched (KEEP-REQUIRED at tip) | 1,500.0 MiB / 1,038 files | **1,512.8 MiB / 1,043 files** |
| Candidate classes + residual | 8,266.7 MiB / 3,684 files | **8,267.2 MiB / 3,684 files** |

The golden-tier figure reproduces the plan's number to within the five files
added since (the five NYISO Gold Book PDFs of §5), and independently matches the
workflow's own "~1.5 GB" header comment — the method is sound and portable to
the post-prune measurement whenever it happens.

Whole-tip deltas since BLOAT-A's base:

| Tree | Δ MiB |
|---|---:|
| `results/calibration` | **+16.8** |
| `data/raw` | **+12.4** |
| `frontend/data` | **+4.8** |
| everything else | +1.2 |
| **total** | **+35.2** |

---

## 4. G3 evidence — `golden-data-tier.yml`

Plan §8 asks this session for a **post-prune** green dispatch as the G3 gate
evidence that the data-backed tier survived the prune. **That evidence cannot
exist yet** and this session did not manufacture it. What the dispatch does
supply is the tier's own baseline, which turns out to be worth having:

- **The tier has never completed a run.** Its only prior run — `31767823203`,
  2026-08-14, the first-ever dispatch (DEBUG-A, under release-plan §6 decision
  7) — is red, and the red is **infrastructure, not a test failure**: the job
  died at 09:41 elapsed during `curate_emissions.py --years 2023` with
  `The runner has received a shutdown signal … exit code 143`. No test ran; the
  loud-failure guard never executed. So there is **no green baseline** for the
  tier at any commit.
- This session dispatched run **`31857842156`** at `315a245`.

<!-- GOLDEN_RESULTS -->

**Consequence for G3.** G3's wording — "`golden-data-tier.yml` manually
dispatched once **post-prune** and green" — presumes a tier that is green
pre-prune, so that a post-prune red is attributable to the prune. Establishing
that pre-prune green is a prerequisite the program has not yet met, and it is
cheap to meet: it is one dispatch, and it should be done and recorded **before**
BLOAT-B's prunes land, not after, or G3's proof mechanism cannot discriminate.

---

## 5. Deviations and drift observed in passing

Findings from the measurement pass, recorded so BLOAT-B (whenever it runs) does
not re-derive them:

1. **The corpora BLOAT-B was chartered to convert kept growing while it
   waited.** Five NYISO Gold Books (`2018`–`2022`, **+12.4 MiB**) were added to
   `data/raw/NYISO/` after `f2de3b0`. That directory is item **B5**'s
   convert-group *and* a golden-tier sparse directory. The plan's "34 committed
   PDFs / 144.5 MiB" is now **38 / 153.2 MiB**; B5's `SOURCES.md` URL table must
   cover the new five.
2. **The C-5.1 prune target grew by ~44 MiB.** `results/calibration/**/hourly/`
   was 92.9 MiB across the plan's named bundles and is now **137.3 MiB across 30
   bundles**. The plan's per-bundle table is still accurate for the bundles it
   names (spot-checked: `pjm158_ctl_A` 6.3, `miso155_p0_C` 6.2,
   `neiso86_2022_corrected` 3.7 — all present); the growth is new bundles
   registered since. **PR-3's bundle list must be re-derived at execution time,
   not copied from the plan**, and each new bundle re-checked against the
   keeper/lane-hold criteria.
3. **`nyiso133_control` is not at tip under that name** — the plan's C-5.1 HOLD
   row names it, and no bundle by that name has an `hourly/`. `nyiso133_cod_arm`
   (3.6 MiB) is present. Resolve the name before pruning either.
4. **D-5 was closed by DEBUG-A, not by BLOAT.** The plan §9 records D-5
   (`patches/pjm-m1-code.patch`) as "UNTOUCHED by this plan — keep-required
   honored". Since then DEBUG-A archived it: the file is now
   `patches/archive/pjm-m1-code.patch` beside
   `patches/archive/ARCHIVED-2026-08-14-pjm-m1.md`, with the CHANGELOG recording
   *why* it must never be applied verbatim. Keep-required is still honored (the
   bytes are tracked, only moved). **§9's D-5 line is stale and should read
   CLOSED (DEBUG-A, 2026-08-14).**
5. **Decision 7's single golden-tier dispatch was already spent** by DEBUG-A on
   2026-08-14. Plan §8 separately authorizes BLOAT-B's re-dispatch, which is what
   this session used; flagged only so the PM's decision ledger reflects two
   dispatches, not one.

---

## 6. Executed / vetoed item ledger

Per plan §3–§7. **Status is uniform and it is not a judgement on any item** —
nothing was executed because BLOAT-B was never chartered.

| Item | Class | Planned | Status |
|---|---|---:|---|
| **A1** SCED in-place slim (1,023 + 27 rtcb shards) | class-approved | −≈1,450 MiB | **NOT EXECUTED** — corpus unslimmed at tip |
| **A2** SCED 2024+ window conversion | needs-sign-off | −≈1,280 MiB | **NOT EXECUTED** — not signed; plan recommends deferring into Stage 2 |
| **B1a** 4 loose SCED extracts, slim with A1 | class-approved | −95 MiB | **NOT EXECUTED** |
| **B1b** 4 loose SCED extracts, convert | needs-sign-off | −145.1 MiB | **NOT EXECUTED** — not signed |
| **B2** 21 loose 60-day DAM parquets | — | — | **VETOED IN PLAN** (§4.2 verified KEEP; removed from the candidate list before BLOAT-B). Standing — 28 such parquets / 367.2 MiB at tip, all keep |
| **B3** `lmp-data/CAISO` 60 dailies + GUID junk | needs-sign-off | −563.6 MiB | **NOT EXECUTED** — not signed |
| **B4** `caiso-dam-outages` 1,094 xlsx | class-approved | −155.0 MiB | **NOT EXECUTED** |
| **B5** 28 publication PDFs | class-approved | −≈137.9 MiB | **NOT EXECUTED** — and the group grew to 33 (§5.1) |
| **B6** 4 NYISO load-report zips | class-approved | −65.2 MiB | **NOT EXECUTED** |
| **§4.7** adjacent items | — | — | **VETOED IN PLAN** — verified KEEP, do not re-litigate |
| **C-5.1** non-keeper hourly, approved rows | class-approved | −62.7 MiB | **NOT EXECUTED** — list must be re-derived (§5.2) |
| **C-5.1** lane-hold rows (ercot193, miso155, nyiso133) | HOLD | −23.2 MiB | **NOT EXECUTED** — holds still live; `miso155_p0_C` is still read by `tests/test_miso155_p0_commitment_sidecar.py` |
| **C-5.1** touchpoint rows (neiso86, pjm2022) | needs-sign-off | −5.9 MiB | **NOT EXECUTED** — not signed |
| **§5.2** the four `_`-prefixed dirs | — | — | **VETOED IN PLAN** — citation check answered KEEP, all four |
| **D1** rotate 77 of 83 attestation generators | class-approved | ~0 | **NOT EXECUTED** — 83 still at top level |
| **D2** ~8 one-shot helpers | class-approved | ~0 | **NOT EXECUTED** |
| **E1** dashboard payload prune | nil-action | 0 | **N/A by design** — and re-verified clean this session: `check_registry_payload_parity.py` → **69 runs, 0 orphans** |
| **E2** Class-E retention rule | proposal | — | **PENDING OWNER ADOPTION** (proposed as BLOAT-2) |

---

## 7. Proposed D-ledger closures (for PM numbering)

Resuming `docs/refactor-consolidation-plan-2026-07.md` §9, per plan §9. Each
re-verified against `315a245` this session rather than carried forward on the
plan's word:

- **D-3 (retention sweep + prune-extension): CLOSE AS SHIPPED.** Re-verified
  live. `scripts/prune_iso_runs.py` deletes the registry sidecar, the
  `runs/<id>.js` payload and the mapped `results/calibration/<bundle>/` together
  (module docstring lines 20–21), with the immunity set intact — bundles still
  referenced by a surviving sidecar are never deleted (`live_bundles`, lines
  116–141). `scripts/check_registry_payload_parity.py` runs in CI
  (`.github/workflows/ci.yml:101`) and passes at tip: **"registry/payload parity
  OK (69 runs checked, 0 known-unsynced tolerated)"**. Zero orphans.
- **D-4 (root LMP zips): CLOSE AS EXECUTED.** Re-verified: **zero** root-level
  `*.zip` at tip. The moved dailies inside `lmp-data/CAISO` (586.6 MiB) remain
  as item B3, still needs-sign-off.
- **D-5 (`patches/pjm-m1-code.patch`): ALREADY CLOSED — by DEBUG-A, 2026-08-14,
  not by BLOAT.** See §5.4. Recorded here only to correct the bloat plan §9's
  stale "UNTOUCHED" line.
- **D-8 (data-in-git long-term, "Defer; document status quo"): SUPERSEDE**, per
  plan §9 — the deferral is spent, replaced by the §1 two-stage architecture.
  Proposed successors, unchanged from the plan and **all still open**:
  - **(new) BLOAT-1** — approve/veto the Stage-1 itemized list per class
    (§3–§7). This is the G1 review the plan exists for and **it has not
    happened**; it is the single thing blocking PR-1..PR-4.
  - **(new) BLOAT-2** — adopt the Class-E retention rule text (§7 E2).
  - **(new) BLOAT-3** — the Stage-2 charter decision: whether/when to untrack
    the measured ~3,562 MiB residual under the §0ar-3 checklist.

Numbering is left to the PM/owner, per the plan, to avoid colliding with ledger
numbers cited elsewhere.

---

## 8. What has to happen next

In order, and none of it is this session's to do:

1. **G1** — Wave-1 handoffs merged, owner decision queue signed.
2. **BLOAT-1** — the owner's item-level approve/veto over plan §3–§7. Without
   it there is no deletion list and PR-1..PR-4 cannot be written.
3. **G2** — final model state, after PERF-B. BLOAT-B waits here so a `results/`
   prune never races `capture_keeper_goldens.py`.
4. **A pre-prune green `golden-data-tier.yml` run**, recorded — the missing
   baseline G3's proof mechanism depends on (§4).
5. **BLOAT-B PR-1..PR-4**, re-deriving the C-5.1 bundle list and B5's PDF group
   at execution time rather than from the plan (§5.1–§5.3).
6. **This close-out, re-run**, against a tip that has actually been pruned.

---

## 9. Session provenance

- Read-only with respect to the repo: no data file, corpus, bundle, script or
  workflow was moved, slimmed, converted or deleted by this session.
- Two workflow dispatches, both chartered by plan §8: `cleanup-large-blobs.yml`
  **dry run** `31857841269` and `golden-data-tier.yml` `31857842156`.
- The `REWRITE-HISTORY` confirm phrase was never supplied, and the rewrite/push
  steps are recorded as never reached.
