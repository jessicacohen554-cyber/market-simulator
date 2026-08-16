# Model Audit Program — Director Status Board (2026-08)

> **STATUS: ACTIVE** — live rollup maintained by the program-director session,
> updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable
> event record; this board is the at-a-glance state). Completion figures are
> the director's estimate against each workstream's full DoD (A+B halves).

**Snapshot:** 2026-08-16 ~04:40 UTC · `origin/main` @ `0ad8d42` ·
**GATE G1 DECLARED** (all five Wave-1 handoffs merged; §6 queue signed;
decision 1 closed-overtaken per the PERF-A memo, owner ack requested).

## Workstream rollup

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991, gap register routed); AUDIT-B held (G3) | **In progress ~85%** | AUDIT-B at G3 |
| WS2 `DEBUG` | DEBUG-A ✓, DEBUG-B ✓; **pjm-162/163 promotion EXECUTING at snapshot** (keeper JSON still pjm-152 on main); residue open (B1 gate, clean-main re-verify, sibling-imports) | **In progress ~85%** | ⚠ TWO DEBUG-manager sessions live on the promotion surface — owner picks the executor, the other stands down to residue (see alerts) |
| WS3 `PERF` | PERF-A ✓; **PERF-B UNLOCKED by G1 — prompt issued for owner launch (Fable)** | **In progress ~55%** | owner launches PERF-B; capture stage-0 goldens only after the PJM promotion lands |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + follow-up #4005: user manual, methodology-finalization audit, gap rows D1/D4/D5); DOCS-B held (G2) | **In progress ~60%** | DOCS-B at G2 (executes the finalization checklist) |
| WS5 `SITE` | Held by design | **Not started** | gate **G3** |
| WS6 `BLOAT` | All prunes merged (B-1..B-5, ≈3,737 MiB; tip 6,405.7 MiB per B-7); **B-7 close-out = open PR #3995** | **In progress ~95%** | owner merges #3995 (golden-tier green now on record as its missing evidence) |
| — `GOLDEN-TIER-FIX` | **COMPLETED** — #3996 merged (peak 10.05→5.17 GiB, output byte-equivalent), authorized dispatch `31913648051` **SPENT + GREEN** (guard PASS, zero data-missing skips); G3 evidence mechanism restored | **Completed** | records PR #4000 (twin-lane collision) is `dirty` — owner: rebase-and-merge or close-with-note |

## Gates

- **G0** adopted ✓ (2026-08-13) · **G1 DECLARED ✓ (2026-08-16)**.
- **G2** — needs: PERF-B merged byte-green; one completed fast-tier-green
  ci.yml run (PERF-B's sparse block enables it); **keepers settling** —
  CAISO/MISO/ERCOT/NYISO all moved in the last 12 h, so the freeze window
  needs the calibration program to pause; owner flips branch protection
  (memo ready); on declaration the PM notifies the FFR desk (Q.2 battery).
- **G3** — after G2: DOCS-B + B-7 already-merged close-out; proof mechanism
  (golden tier) now works — first engineering-green on record. Weekly cron's
  first scheduled firing: Mon 2026-08-17 05:37 UTC.
- **G4** — SITE-A + AUDIT-B.

## Alerts (owner action)

1. **DEBUG duplication:** owner-launched `claude/fable-debug-manager-reissue-t8dg4w`
   session ("O2 resolved; both decision cards served" — waiting) AND the
   revived seeded `session_01V4GocSVjMTBwSxVQEUMyTk` ("pjm-163 attestation
   final; re-key keeper JSON + matrix shard" — executing) are BOTH live.
   Resolution: whichever session the owner signed promote in finishes the
   promotion; answer the other's cards with "already adjudicated — skip
   tasks 1–2, run residue only (B1, clean-main re-verify, sibling-imports)"
   or archive it. Watch: the seeded one may push the director's branch name
   (designated-branch inheritance).
2. **Open PRs:** #3995 (B-7 close-out — merge), #4000 (golden-tier twin
   records — dirty; rebase-and-merge or close; the material facts are
   already in the §8 ledger).
3. **Decision-1 ack** (warm-start closed-overtaken) — one word retires it.
4. Audit OWNER queue **O4–O8** stands (holdout-freeze premise, NEISO
   legacy-P2, locked-test scheduling at G2, ERCOT P0 bit-identity, NEISO
   SMD DST-naive repair charter).

## Session roster (program lanes, at snapshot)

| Lane | Session | Model | Status |
|------|---------|-------|--------|
| Director | `session_01UXdTbfSK7gGxJyahrEsboM` | Fable | active |
| DEBUG-MGR (owner-launched) | `…KzV9dpSGXTiygW2RbiunY7` (`fable-debug-manager-reissue-t8dg4w`) | Fable | cards served — awaiting owner |
| DEBUG-MGR (revived seeded) | `session_01V4GocSVjMTBwSxVQEUMyTk` | Fable | executing pjm-163 promotion — see alert 1 |
| PERF-B | owner launches — prompt issued 04:40 UTC | Fable | pending launch |
| GOLDEN-TIER-FIX (winner twin) | `session_01St4QNz9jTnw3W5oSav1Tzi` | Fable | complete — archivable |
| GOLDEN-TIER-FIX (seeded twin) | `session_01SYyqHxxsjkUD95E272svYh` | Fable | archived; its records PR #4000 open |
| AUDIT-A / DOCS-A | seeded, delivered, archived | Fable / Opus | complete |

Adjacent (non-program) at snapshot: MISO-159 promotion landing (solving),
CAISO close-out (hydrating), ERCOT reserve-basis Phase-0 (pending), ERCOT
conduct Phase-0 (merged #4002) — tracked only for keeper movement vs G2.

## Refresh protocol

On each owner "refresh", the director: (1) lists sessions + fetches fresh
`origin/main`, re-reads plan §8 and lane handoffs; (2) reports each
workstream as **not started / in progress with % / completed / pending
blockers**; (3) issues prompts for any lane whose gate has cleared, appends
the §8 ledger entry, and updates this board in the same pass.
