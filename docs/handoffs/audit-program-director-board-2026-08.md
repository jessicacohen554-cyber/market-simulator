# Model Audit Program — Director Status Board (2026-08)

> **STATUS: ACTIVE** — live rollup maintained by the program-director session,
> updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable
> event record; this board is the at-a-glance state). Completion figures are
> the director's estimate against each workstream's full DoD (A+B halves).

**Snapshot:** 2026-08-16 ~09:40 UTC · `origin/main` @ `8485325` ·
**PJM KEEPER RE-KEYED: `2026-08-15-pjm-162-inputclock`** (promoted at the
pjm-163 DEBUG-manager sitting on the owner's decision card; determination
re-verified per D-5(b): CALIBRATED, every criterion PASS, zero caveats).
G1 declared 2026-08-16 (#4006 on main).

## Workstream rollup

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991, gap register routed); AUDIT-B held (G3) | **In progress ~85%** | AUDIT-B at G3 |
| WS2 `DEBUG` | DEBUG-A ✓, DEBUG-B ✓, **pjm-162 PROMOTED** (O1 done; O2 resolved as a stale registration-time quote, debug-sweep Addendum A.1; O3 ≤2022 extension charter SIGNED same sitting); residue: clean-main re-verify GREEN + B2 folded + census updated (#4008 merged), sibling-import batch 2/2 = open PR #4009 | **In progress ~95%** | owner merges #4009; verify ≤2022 extension execution next refresh; duplication RESOLVED (promotion executed in the owner-launched session; redundant seeded session archived by the director 09:30 UTC) |
| WS3 `PERF` | PERF-A ✓; **PERF-B prompt issued 04:40 UTC — NOT yet launched**; its keeper-stability precondition is now SATISFIED (PJM promotion landed) | **In progress ~55%** | owner launches PERF-B (prompt unchanged, stands as issued) |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + #4005); DOCS-B held (G2) | **In progress ~60%** | DOCS-B at G2 |
| WS5 `SITE` | Held by design | **Not started** | gate **G3** |
| WS6 `BLOAT` | All prunes merged (B-1..B-5); **B-7 close-out = open PR #3995** | **In progress ~95%** | owner merges #3995 |
| — `GOLDEN-TIER-FIX` | **COMPLETED** — #3996 merged; authorized dispatch `31913648051` SPENT + GREEN | **Completed** | records PR #4000 still open (`dirty`) — owner: rebase-and-merge or close-with-note |

## Gates

- **G0** adopted ✓ (2026-08-13) · **G1 DECLARED ✓ (2026-08-16, #4006)**.
- **G2** — needs: PERF-B merged byte-green (NOT LAUNCHED yet); one completed
  fast-tier-green ci.yml run (PERF-B's sparse block enables it); **keepers
  settling** — still churning: pjm-162 promoted this cycle, CAISO caiso-197
  promotion open as PR #4010, miso-159 landed overnight, ERCOT lanes active;
  owner flips branch protection (memo ready); on declaration the PM notifies
  the FFR desk (Q.2 battery).
- **G3** — after G2: DOCS-B + the B-7 close-out (merge #3995); proof
  mechanism (golden tier) restored. Weekly cron's FIRST scheduled firing:
  Mon 2026-08-17 05:37 UTC — expect green; a red is a new finding.
- **G4** — SITE-A + AUDIT-B.

## Alerts / owner actions

1. **Launch PERF-B** — the prompt issued at the 04:40 UTC refresh stands
   unchanged; its PJM-keeper precondition is now satisfied. G2 is blocked on
   it.
2. **Open PRs to merge/disposition:** program — #4009 (DEBUG sibling-import
   batch 2/2), #3995 (BLOAT-B-7 close-out), #4000 (golden-tier twin records,
   dirty — rebase or close). Adjacent — #4010 (caiso-197 keeper promotion),
   #4007 (miso-159 staging cleanup).
3. **Decision-1 ack** (warm-start closed-overtaken) — recorded at G1; a
   one-word ack retires it from the queue.
4. Audit OWNER queue: **O1 DONE** (pjm-162 promoted), **O2 RESOLVED** (stale
   quote), **O3 SIGNED** (≤2022 extension charter; execution to verify).
   **O4–O8 stand** (holdout-freeze premise, NEISO legacy-P2, locked-test
   scheduling at G2, ERCOT P0 bit-identity, NEISO SMD DST-naive repair).

## Session roster (program lanes, at snapshot)

| Lane | Session | Model | Status |
|------|---------|-------|--------|
| Director | `session_01UXdTbfSK7gGxJyahrEsboM` | Fable | active; container git creds down this cycle — board pushed via API, ledger append deferred one cycle |
| DEBUG-MGR (owner-launched) | `fable-debug-manager-reissue-t8dg4w` | Fable | executed the pjm-162 promotion + residue (#4008 merged, #4009 open) — IDLE |
| DEBUG-MGR (seeded) | `session_01V4GocSVjMTBwSxVQEUMyTk` | Fable | ARCHIVED by director 09:30 UTC (redundant; nothing pushed) |
| PERF-B | not launched | Fable | prompt issued 04:40 UTC, stands |
| GOLDEN-TIER-FIX | `session_01St4QNz9jTnw3W5oSav1Tzi` (winner twin) | Fable | complete — archivable; seeded twin archived, its PR #4000 open |
| AUDIT-A / DOCS-A | seeded, delivered, archived | Fable / Opus | complete |

Adjacent (non-program) at snapshot: CAISO close-out (PR #4010 open),
MISO-159 landing (solve B in flight, #4007 open), ERCOT conduct Phase-0
(merged #4002; session review-ready), ERCOT reserve-basis Phase-0 (stuck on
a clone timeout — the known big-repo failure; relaunch with the shallow
recovery recipe if wanted), NYISO-137 (merged #4004; safe to archive) —
tracked only for keeper movement vs G2.

## Refresh protocol

On each owner "refresh", the director: (1) lists sessions + fetches fresh
`origin/main`, re-reads plan §8 and lane handoffs; (2) reports each
workstream as **not started / in progress with % / completed / pending
blockers**; (3) issues prompts for any lane whose gate has cleared, appends
the §8 ledger entry, and updates this board in the same pass.
