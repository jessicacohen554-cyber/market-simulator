# Model Audit Program — Director Status Board (2026-08)

> **STATUS: ACTIVE** — live rollup maintained by the program-director session,
> updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable
> event record; this board is the at-a-glance state). Completion figures are
> the director's estimate against each workstream's full DoD (A+B halves).

**Snapshot (v6):** 2026-08-17 ~01:55 UTC · `origin/main` @ **`a4ef2a9`** ·
**ZERO open PRs** · a **third forced history rewrite** has landed since the v5
snapshot, so every pre-rewrite commit-sha citation outside
`docs/governance/citation-commit-map.txt` is dead or (for short prefixes)
possibly wrong.

**This is the first refresh in three cycles.** The v5 snapshot (2026-08-16
09:40 UTC @ `8485325`) was stale on every row; the standing deviation that
caused it — the director issues prompts only and does not push, so records
land via a dispatched lane — is recorded in §8 and in *Alerts* below. Two
prior dispatches of this records lane were never launched.

**Two corrections carried into this snapshot** (both detailed in the §8
entry `2026-08-17 (01:55 UTC director cycle)`):

1. **PERF-B was not dead.** The 19:35 UTC cycle reported its branch absent
   from the remote and nothing durable produced. Wrong — the branch existed,
   merged as **#4033**, and auto-deleted. PERF-B was ~**one ISO further
   along** than reported.
2. **Main had already moved past the dispatch snapshot.** The cycle was
   framed at `5f58324` with #4031 open; #4031 merged at 01:52 UTC and main
   is `a4ef2a9` with nothing open.

## Workstream rollup

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991, gap register routed); AUDIT-B held | **In progress ~85%** | AUDIT-B at **G3** |
| WS2 `DEBUG` | **COMPLETED** — DEBUG-A ✓, DEBUG-B ✓, pjm-162 promoted, sibling-import residue retired (census **0 bare sites / 0 live files**), landing-verify green on merged main | **Completed** | none; no DEBUG-C continuation chartered |
| WS3 `PERF` | PERF-A ✓; **PERF-B stage-0 partially delivered — #4033 merged 01:44 UTC**: goldens manifest (`results/regression-goldens/perfb-stage0/manifest.json`) with **ERCOT captured** (keeper `ercot204`, clean-present, GTC-armed) + the `basis_sha` fidelity-oracle repair. **1 ISO of 6; none of the five changes landed.** First session stalled ~21:36; continuation dispatched 01:55 UTC | **In progress ~62%** | **THE SOLE G2 BLOCKER.** Continuation resumes from the merged manifest: five ISOs, then the five changes, then merged byte-green |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + #4005); DOCS-B held | **In progress ~60%** | DOCS-B at **G2** |
| WS5 `SITE` | Held by design | **Not started** | gate **G3** |
| WS6 `BLOAT` | Prunes B-1..B-8 merged; **BLOAT-2 CLOSED** — Class-E retention rule ADOPTED + point-4 bundle-parity sweep built (**#4032**); **BLOAT-3 ADJUDICATED** — signed verdict **O2 staged (a)-only GO** merged (**#4031**) | **In progress ~95%** | decisions are done; what remains is **execution** — the per-corpus §4.8 evidence passes, then untrack PRs for passing corpora only (prima facie ≈ 1,133 MiB) |
| — `GOLDEN-TIER-FIX` | **COMPLETED and independently verified** (#4014); authorized dispatch `31913648051` SPENT + GREEN | **Completed** | weekly cron's first scheduled firing **not yet due** — see *Watch* |

## Gates

- **G0** adopted ✓ (2026-08-13) · **G1** DECLARED ✓ (2026-08-16, #4006).
- **G2** — four legs outstanding:
  1. **PERF-B merged byte-green** — partially delivered (ERCOT only); the
     binding blocker.
  2. **One completed fast-tier-green `ci.yml` run** — unreachable until
     PERF-B's sparse block lands.
  3. **A keeper freeze** — **owner call, now outstanding across four
     director cycles.** Unreachable at this snapshot: caiso-200 launched
     01:50 UTC and is solving, caiso-199 awaits its NOT-YET ruling, and
     ERCOT / NYISO / MISO all moved this cycle (#4036 / #4034 / #4035).
  4. **Branch-protection flip** — owner action, memo ready.

  On declaration the PM notifies the FFR desk (Q.2 battery).
- **G3** — after G2: **DOCS-B** + the **BLOAT leg** (BLOAT-3's chartered
  follow-on execution; its *verdict* leg is satisfied — signed and merged).
  The **golden-tier proof leg is satisfied** (#4014 + green dispatch).
- **G4** — SITE-A + AUDIT-B.

## Watch

- **Golden-tier weekly cron — NOT YET FIRED at this snapshot.** First
  scheduled firing **2026-08-17 05:37 UTC**, ~3 h 40 m out. At 01:57 UTC
  `golden-data-tier.yml` shows **only `workflow_dispatch` runs**, latest
  `31913648051` (2026-08-15 23:01 UTC, `ccca569c`) **success**. **Next
  cycle must check it and record green/red — a red is a NEW finding, not a
  known state.**

## Alerts / owner actions

1. **No open PRs.** Nothing is waiting on a merge this cycle — the first
   snapshot in the program's history with an empty queue.
2. **Owner decision queue (all standing):**
   - **decision-1 ack** — warm-start closed-overtaken; a one-word ack
     retires it.
   - **BLOAT-3 verdict** — **SIGNED and MERGED (#4031)**; retired from the
     queue as a decision, tracked under WS6 as execution.
   - **caiso-199 NOT-YET ruling** — outstanding (#4037 landed the FINDING,
     matrix cell and log entry; the disposition is the owner's).
   - **keeper-freeze call** — outstanding **four cycles**; blocks G2.
   - **O4** holdout-freeze premise · **O5** NEISO legacy-P2 · **O6**
     locked-test one-shot scheduling at G2 · **O7** ERCOT P0 bit-identity ·
     **O8** NEISO SMD DST-naive repair charter.
3. **O6 standing guard — restated because G2 is where it bites.** 2019 and
   H1-2026 are **touch-once** and **no ISO has ever spent one**. **Never let
   a lane spend one**; the scheduling decision is the owner's alone.
4. **Standing deviation.** The director issues prompts only and does not
   push; board and ledger land via a dispatched records lane. Cost on the
   record: three cycles without a refresh, two undelivered dispatches.

## Session roster (live `list_sessions` read, 2026-08-17 01:57 UTC)

*Rebuilt from a live call — v5's roster is not carried forward.*

| Lane | Session | Model | Status |
|------|---------|-------|--------|
| Director | `session_01ByM3NG5RrYtPo5kamsP6y2` | Opus | IDLE (on `master`) |
| Records lane (this) | `session_01PmqoF4sDqsXJaQQh1GZD8N` | Opus | RUNNING — board v6 + §8 entry |
| **PERF-B (continuation)** | `session_01KUKpkmjHFgaTSH5hdLC3JR` | Fable | **RUNNING** — launched 01:55 UTC, resumes from the merged stage-0 manifest |
| PERF-B (first session) | `session_017rr6j76mRLU4NBTK77UL7K` | Fable | **IDLE / connected** — stopped producing ~21:36; delivered #4033 before stalling. *(Live read contradicts the dispatch's "container is gone"; the continuation stands regardless.)* |
| WS6 BLOAT-3 charter | `session_01MFmi3fQcxXggH2J7115Vpa` | Fable | ARCHIVED — verdict delivered, #4031 merged |
| WS6 BLOAT-2 / Class-E | `session_01KK9UiTsYhc7tTdrjcwFqN8` | Fable | ARCHIVED — #4032 merged |
| WS6 Class-E (successor) | `session_01E6ZDtke2F4XNewHer2Jg3C` | Opus | IDLE |
| WS6 BLOAT-B-8 aftercare | `session_01W3dL452ag9PfrgiKF5AhbE` | Fable | ARCHIVED — rewrite finding + commit map landed |
| WS2 DEBUG-MGR reissue #2 | `session_01GEfjCzTmPbbpmiPQsyiRBx` | Fable | IDLE — residue retired |
| WS2 DEBUG post-merge verify | `session_0125M5sNhjfSGS2rupUqXjbE` | Opus | ARCHIVED |

**Adjacent (non-program) — tracked only for keeper movement vs G2:**

| Lane | Session | Model | Status |
|------|---------|-------|--------|
| CAISO caiso-200 | `session_013tepkL6gSBDvYweJnrNLbD` | Fable | **RUNNING — solving** (launched 01:50 UTC); blocks the freeze |
| CAISO caiso-199 | `session_01Bc6V6yUUFCAjjcKAX9T46p` | Opus | ARCHIVED — #4037 merged; **NOT-YET, owner ruling outstanding** |
| ERCOT ercot-213 | `session_01M6fZBkTq338FDHPHMRrGB2` | Opus | RUNNING — #4036 merged (arm REJECTED-AS-ARMED, pair retained) |
| NYISO nyiso-140 | `session_01VU7XEb2jcT98YF8BjhfJfr` | Opus | RUNNING — #4034 merged (A/B hourly sidecars) |
| MISO miso-160 | `session_01EFDYVdbphHRUSTCLuhmvfp` | Fable | RUNNING — #4035 merged (close-out manifest refresh) |
| MISO close-out (successor) | `session_011E9zCydqN8yKYLwXdv8MtU` | Opus | RUNNING (launched 01:54 UTC) |

## Refresh protocol

On each owner "refresh", the director: (1) lists sessions + fetches fresh
`origin/main`, re-reads plan §8 and lane handoffs; (2) reports each
workstream as **not started / in progress with % / completed / pending
blockers**; (3) issues prompts for any lane whose gate has cleared, appends
the §8 ledger entry, and updates this board in the same pass.

**Under the standing deviation, steps (3)'s two write duties are dispatched
to a records lane rather than pushed by the director.** A refresh is not
complete until that lane has landed both files — and, per the v5→v6 gap, a
dispatch that is never launched leaves the board silently wrong. Verify the
landing before declaring a cycle done.
