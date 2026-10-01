# DECISION CARD BLOAT-3 — the Stage-2 charter: untrack the residual, against WHICH recovery story?

**Session BLOAT-3, 2026-08-16.** Docs-only: **no untracking, no gitignore edit,
no data move, no workflow edit was executed by this session** — this card and
its two ledger entries are the whole deliverable. It serves the D-ledger item
**BLOAT-3** (`docs/bloat-removal-plan-2026-08.md` §9, resuming
`docs/refactor-consolidation-plan-2026-07.md` §9's D-8 supersession), whose
charter input was re-measured by the BLOAT-B-7 close-out
(`docs/bloat-removal-report-final-2026-08.md` §2, at `04d1cf0`).

> **VERDICT — ANSWERED IN-SESSION (owner, 2026-08-16, `AskUserQuestion`; all
> four rulings as recommended):**
>
> * **D1 — O2, STAGED (a)-ONLY GO.** Charter the §4.8 evidence passes now;
>   untrack ONLY corpora whose pass measures a stable archive (prima facie
>   `campd-unit-level` non-2023 692.6 + `eia-930` 190.3 + `lmp-data`
>   non-golden 143.5 + `PJM` 107.1 ≈ 1,133 MiB, plus whatever else passes).
>   Decaying/past-retention corpora stay tracked.
> * **D2 — story (a) ALONE is admitted.** (b) external archive: NOT admitted
>   at this sitting — no archive is chartered, and D5's salvage tie-in is
>   thereby moot here (the `refs/pull/*` salvage question stays open at
>   rewrite finding §7 item 3, unanswered by this card). (c) signed loss:
>   NOT admitted — no loss route exists; a corpus that fails its (a) pass
>   simply STAYS TRACKED. (d) pins: NOT granted — no no-further-rewrite
>   commitment; pins stay dead as a recovery story and `hydrate_data.py` pin
>   support is NOT built.
> * **D3 — evidence passes AUTHORIZED now** (the §4.8 BLOAT-A-equivalent
>   prerequisite, scope per §7-D3(i) incl. the rule-22 vintage question);
>   golden-tier proof for untrack PRs = **the weekly cron green** (first
>   firing 2026-08-17 05:37 UTC) — no new dispatch authorization spent.
> * **D4 — OUT.** The §4.2 DAM 2024+ subset does not re-enter with this
>   grant; it travels with a future (b)-archive decision. The 2023 quarters
>   stay NEVER-taken regardless.
>
> Net effect: **BLOAT-3 is SIGNED (O2).** Execution sequence: per-corpus
> §4.8 evidence passes → per-corpus untrack PRs (the §5 checklist, PR-2/PR-5
> idiom, `intentional-shrink`) for passing corpora only → cron green as the
> post-merge proof. Recorded in bloat plan §9 (BLOAT-3) and release-plan §8.

---

## 0. THE ASK, IN ONE SENTENCE

Authorize, stage, defer, or decline **Stage 2** — untracking the measured
**≈ 3,311.9 MiB / ≈ 1,311 files** takeable residual of `data/raw` (tip
≈ 6.4 → ≈ 3.0 GiB) — and, before any grant, **rule which recovery story the
untrack is executed against**, because the story Stage 2 was chartered on
(history-as-archive) was demonstrated non-durable on 2026-08-16.

## 1. WHY THE QUESTION CHANGED — the recovery story must be re-derived first

Stage 2 was chartered (plan §1) on the premise that wholesale untracking and
per-corpus conversion "share the *same recovery story* — history is kept, so
every untracked byte remains fetchable forever from the promisor remote at the
last-tracked sha." The §0ar-3 recovery command (`git restore --source=<pin>`)
and the corpus-README pin shas were that story's instruments.

**That premise is dead.** The 2026-08-16 history rewrite
(`cleanup-large-blobs.yml` run 31955205445, an explicit owner decision
superseding the Addendum AQ NO-GO) stripped 7,254 superseded blobs /
7,373.4 MiB — precisely the pool the conversion class's pins resolved into.
All three pins (`971eaa3`, `315a245`, `726f389d`) are dead, their rewritten
twins verified payload-free, and several converted payloads are now
**unrecoverable from this repository** (the 60 CAISO OASIS GRP dailies; the
pre-slim SCED raw columns; the pre-slim manifests). Full record:
`docs/FINDING-history-rewrite-2026-08-16.md` §5.

Two consequences bind this card:

1. **"History keeps the bytes" may never again be offered as a recovery
   contract unless the owner explicitly commits to no further rewrites** — and
   the 08-16 event shows that commitment is one owner decision away from
   revocation even when a signed NO-GO stands. A Stage-2 untrack immediately
   manufactures a NEW ≈ 3.3 GiB superseded-blob pool, which is exactly what
   the *next* rewrite strips.
2. **The benefit side moved too.** The clone stall that motivated the original
   RAW-UNTRACK charter is gone: a full bare clone now completes in 162 s
   (5.46 GiB pack), and the blobless partial clone (3.5 s / 13.7 MB) remains
   the standard session recipe. Stage 2 now pays out only in tip weight and
   per-ISO hydration weight — real, but no longer urgent.

## 2. THE OBJECT, RE-MEASURED (report §2 at `04d1cf0`; rewrite was tip-preserving — re-measure at execution)

| Stage-2 adjudication pool | MiB | Files |
|---|---:|---:|
| **Pool total** | **4,008.7** | **1,487** |
| — §4.2 KEEP: 60-day DAM parquets (2023 quarters irreplaceable — NEVER taken; the **2024+ subset re-enters only with Stage 2** — D4 below) | 367.2 | 29 |
| — §4.7 KEEP: holdout-equivalency intakes 290.1 + `ercot/cdr.*.zip` 39.5 — **irreplaceable, never taken under any option** | 329.5 | 147 |
| **— takeable remainder (the residual proper)** | **≈ 3,311.9** | **≈ 1,311** |

Per-corpus, with the **prima facie** recovery class (tree-only filename reads,
this session; none of this substitutes for the §4.8 evidence pass — see §3):

| Corpus | MiB | Source & retention (prima facie) | Prima facie story |
|---|---:|---|---|
| `campd-unit-level` non-2023 | 692.6 | EPA CAMPD API — stable federal archive, full history served | **(a) strong** |
| `ercot-AS` non-golden | 598.5 | ERCOT MIS 60-day disclosures — rolling retention, decaying; some vintages already aged out | (a) decaying → (b)/(c) |
| `CAISO-AS` | 535.8 | CAISO OASIS `asreq_*` windows **from 2018** — the ~39-month moving boundary (2023-04-22 as of 2026-08-04) means the 2018–2022 files are **already past retention**; 2023+ is decaying now | (a) partial; pre-2023 is (b)/(c) **only** |
| `ercot-hsl` non-golden | 428.3 | `np6/` raw shards + zonal derivations — MIS-family provenance, to be established by its pass | unknown — needs pass |
| `iso-specific-transmission` | 365.8 | mixed derived/source (§4.8); a `paths.py`-registered consumer directory (`ISO_TRANSMISSION_DIR`) | unknown — needs pass |
| `eia-930` bulk | 190.3 | EIA-930 API/bulk — stable federal archive | **(a) strong** |
| `storage-as-awards` | 165.2 | per-ISO split dir; CAISO quarterly storage-report xlsx (public publications) | (a) likely — verify durability |
| `lmp-data` non-golden (MISO/PJM) | 143.5 | MISO market reports / PJM Data Miner — long-lived public archives | **(a) likely** |
| `PJM` | 107.1 | PJM Data Miner series (`rt_hrl_lmps`, `gen_by_fuel`) | **(a) likely** |
| loose-`ercot` ORDC-adder/misc + tails | ~84 | per-item | unknown — needs pass |

**Two facts that harden the prerequisite.** First, unlike executed Class A
(derive-time-only consumers, verified), at least two residual directories are
`config/paths.py`-registered (`iso-specific-transmission`,
`storage-as-awards`) — consumer censuses are genuinely unbuilt here. Second,
several corpora carry **2019–2022 vintages that are plausibly holdout-tier
inputs under rule 22** (`[R-HOLDOUT]`: inputs applied consistently across ALL
years — e.g. `CAISO-AS` 2019–2022, `PJM` 2018–2022 LMPs, `eia-930` 2018–2022);
the §4.7 carve-out enumerated only ERCOT's. An untracked holdout input is not
*lost* under a working recovery story, but hydration-for-touchpoint-solves must
keep working — each pass must adjudicate this explicitly.

## 3. THE THREE ADMISSIBLE RECOVERY STORIES (the central ruling)

- **(a) Per-corpus re-fetch, evidence-passed.** The corpus is untracked only
  after a BLOAT-A-grade evidence pass (§4.8's named prerequisite: consumer
  census, golden/holdout overlap, **measured** retention window, working fetch
  script or verified URL table) and with README + `SHA256SUMS.txt` kept
  tracked as the identity record. Honest limit: **a decaying window converts
  (a) into (c) silently unless re-verified at execution** — the A2 precedent
  priced exactly this ("re-fetchable decays"), but A2 had history as its
  backstop and Stage-2 corpora would have none. (a) is therefore admissible
  ONLY for archives measured stable (federal APIs; PJM Data Miner-class), and
  the pass's retention measurement is the gate, not the corpus's reputation.
- **(b) External archive for the irreplaceable/decaying subset.** An
  owner-held mirror or object store receives the payload bytes, **verified
  against the tracked SHA256SUMS manifests BEFORE the untrack commit**. The
  only story that covers past-retention material (CAISO-AS pre-2023) and
  decaying MIS windows honestly. New infrastructure and owner custody; it
  also answers the standing `refs/pull/*` salvage question
  (rewrite finding §7 open item 3) — one archive serves both, and the salvage
  window is closing on GitHub's schedule, not ours.
- **(c) Explicit acceptance of loss.** Signed per corpus, recorded in the
  corpus README in the honest-retention-status idiom BLOAT-B-8 established
  ("unrecoverable from this repository since <date>"). Cheapest, irreversible,
  and only meaningful as an explicit owner signature — never a default.

**The dead story, named:** *(d) history-as-archive / pin-based recovery.*
Admissible again ONLY under an explicit standing owner commitment to no
further rewrites while pins are load-bearing. Without that commitment, pins
must never again be offered as a recovery contract, and `hydrate_data.py` pin
support (which does not exist today — hydration is tree-at-HEAD-derived) is
**not worth building**: it would be plumbing for a contract the record shows
can be burned. With the commitment, pin support becomes a legitimate small
build (restore an untracked corpus at `--source=<pin>` into the working tree).

## 4. WHAT STAGE 2 BUYS NOW — the diminished benefit, stated honestly

- **Tip:** ≈ 6.4 → ≈ 3.0 GiB logical (full untrack). Golden-tier CI checkout
  weight is UNTOUCHED (the kept 1,375.9 MiB golden block is disjoint from the
  residual by glob construction).
- **Hydration:** per-ISO calibration profiles shrink materially (e.g. the
  `ercot` profile sheds the non-golden `ercot-AS` 598.5 + `ercot-hsl` 428.3;
  `caiso` sheds `CAISO-AS` 535.8). Only lanes that hydrate ISO profiles pay
  today; `code` sessions already pay nothing.
- **Pack/clone: nothing, until the next rewrite.** Untracking removes bytes
  from the *tip*, not the pack — the bytes become superseded blobs. The clone
  path benefit is realized only by a subsequent rewrite, i.e. the exact
  operation that burns story (d) and stresses (a)/(b). A coherent end-state
  exists — untrack under (a)/(b), then rewrite deliberately with the archive
  verified first — but it must be *chosen*, not stumbled into.

## 5. §0ar-3 PRE-MERGE CHECKLIST — status walked at HEAD (2026-08-16)

| Checklist item | Status at HEAD | Execution duty if granted |
|---|---|---|
| (a) Workflows walk | 7 workflows. `golden-data-tier.yml`: sparse list needs **ZERO edits** — its globs already select exactly the kept files inside shared directories (`campd-unit-level/*_2023.parquet`, `eia-930/eia_generation_profiles.parquet`, the two `ercot-AS` award globs, `ercot-hsl` hourly glob, `lmp-data` CAISO-hourly/PJM-monthly), and sparse checkout tolerates absence (B5/B6 precedent, tier GREEN post-prune). `fetch-caiso-oasis-bulk.yml` stages raw CAISO-AS — its outputs become ignored, consistent with the corpus design, and the workflow becomes the (a)-instrument for CAISO-AS 2023+. `ci.yml` / `deploy-pages.yml` / `perf-a-ci-probe.yml` / `file-integrity-guard.yml`: no `data/raw` reads expected | Re-walk at execution HEAD; post-merge golden-tier GREEN is the proof — via the weekly cron (first firing 2026-08-17 05:37 UTC) or a newly authorized dispatch (decision 7's single dispatch is SPENT — D3 below) |
| (b) Golden-tier sparse list | Verified disjoint from the residual (above) | Assert ignore/keep semantics per payload class in-PR (the PR-5 idiom) |
| (c) Skip-when-absent tests | **NOT verified** — the container-death record says most skip; rule: verify, don't assume | Full suite in a `code`-profile worktree with the residual absent; enumerate and fix reds BEFORE the untrack merges |
| (d) CLAUDE.md data-contract + Git & Pushing rewrite | Unbuilt | Same-PR; CLAUDE.md is core ≥300 lines — rule 27 mechanics (edit local, push exact bytes, blob-verify) |
| (e) `hydrate_data.py` pin support | **Does not exist**; profiles are tree-derived and simply shrink when payloads leave the tree | Build ONLY if story (d)'s no-further-rewrite commitment is granted (D2); otherwise skip — nothing else in hydration depends on it |
| (f) Per-corpus manifests + README recovery documentation | Convention established (PR-2/PR-5 idiom) | README states the corpus's RULED story — (a) fetch command + measured window, (b) archive locator + verification date, or (c) the signed loss statement. Never a pin, absent D2's commitment |
| (g) `intentional-shrink` label | Data paths are outside `file-integrity-guard`'s `is_core` set | Label by G3 convention anyway (the PR-1/2/3/5 precedent) |

## 6. OPTIONS

- **O1 — DEFER.** Keep the residual tracked; revisit when a driver reappears
  (disk pressure, hydration pain, a chosen deliberate rewrite). Zero risk,
  zero work; carries ≈ 3.3 GiB at tip and the ISO-profile hydration weight.
- **O2 — STAGED GO under story (a) only** *(recommended)*. Charter the §4.8
  evidence passes now (read-only, BLOAT-A-grade, one session or a small
  batch), then untrack ONLY corpora whose pass measures a stable archive —
  prima facie `campd-unit-level` non-2023 692.6 + `eia-930` 190.3 +
  `lmp-data` non-golden 143.5 + `PJM` 107.1 ≈ **1,133 MiB**, plus whatever
  else passes (`storage-as-awards`, parts of `iso-specific-transmission`).
  Decaying/past-retention corpora stay tracked pending D2's (b) ruling. No
  new infrastructure; nothing becomes unrecoverable under any future rewrite.
- **O3 — FULL GO under (a) + (b).** Owner stands up the external archive;
  every corpus that fails (a) is archive-verified before untracking. Takes
  the full ≈ 3,311.9 (+ the D4 DAM re-entry if granted) → tip ≈ 3.0 GiB.
  The only option that also makes a FUTURE deliberate rewrite safe, and the
  archive can absorb the `refs/pull/*` salvage while the window lasts.
- **O4 — FULL GO with (c) for the un-archivable.** Full untrack; per-corpus
  signed loss for whatever fails (a) and is not archived. Cheapest and
  irreversible; pre-2023 CAISO-AS and any aged-out MIS vintages would be
  permanently gone the moment the next rewrite runs.

Under every option: the §4.7 holdout intakes and `cdr.*.zip` are **never
taken**, and the §4.2 2023 DAM quarters are **never taken**.

## 7. THE DECISIONS REQUESTED

- **D1 — Verdict on Stage 2:** O1 / O2 / O3 / O4.
  **Recommended: O2** — the urgent driver is resolved, the evidence passes
  are cheap and are prerequisite work for O3 anyway, and O2 recovers ~1.1+
  GiB with nothing rendered unrecoverable.
- **D2 — Recovery-story ruling (binding for all future untracking, not just
  Stage 2):** which of (a)/(b)/(c) are admissible; and is story (d) granted
  its no-further-rewrite commitment? **Recommended: admit (a) evidence-passed
  and (b); reserve (c) for explicit per-corpus signature; do NOT grant (d)**
  — leave pins dead and skip `hydrate_data.py` pin support.
- **D3 — If O2/O3/O4:** authorize (i) the §4.8 evidence-pass session(s) as
  the BLOAT-A-equivalent prerequisite (each pass: consumer census,
  golden/holdout overlap incl. the rule-22 vintage question, measured
  retention window, fetch instrument, manifest plan), and (ii) the
  golden-tier proof mechanism for the untrack PRs — name whether the weekly
  cron green suffices or a dispatch is newly authorized.
- **D4 — The §4.2 60-day-DAM 2024+ subset** (≈ 194 MiB of the 367.2): does it
  re-enter with this Stage-2 grant? **Recommended: NOT under O2** (its MIS
  window is decaying — it is (b)/(c) material, so it travels with the O3
  archive decision, not with the (a)-only stage).
- **D5 — The `refs/pull/*` salvage window** (rewrite finding §7 item 3): if
  (b) infrastructure is stood up under D2/D3, does it also receive the
  already-unrecoverable pre-rewrite payloads while GitHub's retention lasts?
  (No new analysis here — this card only notes the two decisions share one
  archive.)

## 8. WHAT THIS CARD DOES NOT DO

No untracking, no `.gitignore` edit, no data move, no workflow edit, no
evidence pass (chartered, not performed), no solve. Until D1 is answered,
**Stage 2 remains a standing option, not scheduled work** — exactly as the
plan's §9 left it.
