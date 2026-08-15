# Model Audit Program — Director Status Board (2026-08)

> **STATUS: ACTIVE** — live rollup maintained by the program-director session,
> updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable
> event record; this board is the at-a-glance state). Completion figures are
> the director's estimate against each workstream's full DoD (A+B halves).

**Snapshot:** 2026-08-15 ~21:20 UTC · `origin/main` @ `870c4c8` (post
BLOAT-B-3 #3982+#3983 and the NEISO-intake #3987 merges).

## Workstream rollup

| WS | State | Completion | Manager session (model) | Blockers / next |
|----|-------|------------|-------------------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **dispatched** 2026-08-15 21:13 UTC; AUDIT-B held (G3) | **In progress ~5%** | `session_01CKURpfSiq5Z55bWN8QhtU2` (Fable) | none for A (read-only Wave-1) |
| WS2 `DEBUG` | DEBUG-A **merged** (#3937); DEBUG-B **merged** (pjm-162 keeper CANDIDATE, bundle held from prune); manager **reissued** | **In progress ~75%** | `session_01V4GocSVjMTBwSxVQEUMyTk` (Fable) | owner cards: pjm-162 promotion + ≤2022 clock extension (served in-session); then residue (sibling-imports, clean-main re-verify) |
| WS3 `PERF` | PERF-A **merged** (perf-recheck + warm-start memo); PERF-B held | **In progress ~50%** | PERF-B not yet dispatched | gate **G1** (needs AUDIT-A + DOCS-A merged); owner ack of memo's close-decision-1 recommendation |
| WS4 `DOCS` | DOCS-A **dispatched** 2026-08-15 21:13 UTC; DOCS-B held (G2) | **In progress ~5%** | `session_01UTTocEnQLV6VdHotxwCfgB` (Opus) | none for A |
| WS5 `SITE` | Held by design | **Not started** | — | gate **G3** |
| WS6 `BLOAT` | BLOAT-A ✓; B-1 #3958 ✓, B-2 #3956 ✓, B-3 #3982+#3983 ✓, B-4 #3955 ✓, B-5 #3978/#3979 ✓; **B-6R/B-7 re-measured close-out open** | **In progress ~90%** | close-out not yet dispatched | waits on GOLDEN-TIER-FIX green (dispatch duty transferred there) |
| — `GOLDEN-TIER-FIX` (chartered sub-lane; **G2/G3 critical path**) | **dispatched** 2026-08-15 21:14 UTC | **In progress ~5%** | `session_01SYyqHxxsjkUD95E272svYh` (Fable) | owner merge when branch ready → single authorized golden-tier dispatch |

Recovered at tip by BLOAT-B so far: ≈ 3,737 MiB (B-1 739.8 + B-2 361.8 +
B-3 117.0 + B-5 2,518.5, per PR records); tip ≈ 6.4 GB.

## Gates

- **G0** adopted ✓ (2026-08-13).
- **G1** NOT declared — remaining legs: AUDIT-A + DOCS-A handoffs merged
  (both dispatched today; DEBUG-A / PERF-A / BLOAT-A already on main).
- **G2** — after G1: PERF-B (fast-tier sparse block + byte-gated wins),
  keepers settling, owner flips branch protection
  (`docs/governance/branch-protection-memo-2026-08.md` is ready). FFR Q.2
  battery commissions at this gate (cross-program notice due on declaration).
- **G3** — evidence-blocked until GOLDEN-TIER-FIX's green dispatch; then
  DOCS-B + the B-6R/B-7 close-out.
- **G4** — SITE-A + AUDIT-B after G3.

## Pending owner decisions (live)

1. **pjm-162 PJM keeper promotion** — card served in the DEBUG-MGR session
   (evidence: `docs/FINDING-debug-b-pjm-input-clock-2026-08-15.md` §9; the
   B-3 prune held the candidate bundle, so promotion needs no re-solve).
2. **≤2022 PJM input-clock extension charter** — second card in the same
   session (FINDING §6; interacts with the live pjm-2022 touchpoint ladder).
3. **Warm-start plan §6 decision 1** — PERF-A's memo recommends CLOSE as
   overtaken by events (D-9 flip + D-10 disarm already adjudicated); an owner
   ack retires it from the G1 checklist.
4. **BLOAT-B-5 session** (`session_01UCQgY2zZPNo4nhhfU4judg`) still flags
   need_input: "provide the 4 decision cards for the dispatch record" — the
   four verdicts are already recorded verbatim in plan §8 (A2 SIGNED / B1b
   SIGNED / B3 SIGNED / C VETOED); what it appears to want is the formal
   card documents for its dispatch record.

## Session roster (program lanes, 2026-08-15)

| Lane | Session | Model | Status at snapshot |
|------|---------|-------|--------------------|
| Director (this) | `session_01UXdTbfSK7gGxJyahrEsboM` | Fable | active |
| AUDIT-A | `session_01CKURpfSiq5Z55bWN8QhtU2` | Fable | launched 21:13 UTC |
| DOCS-A | `session_01UTTocEnQLV6VdHotxwCfgB` | Opus | launched 21:13 UTC |
| GOLDEN-TIER-FIX | `session_01SYyqHxxsjkUD95E272svYh` | Fable | launched 21:14 UTC |
| DEBUG-MGR (reissue) | `session_01V4GocSVjMTBwSxVQEUMyTk` | Fable | launched 21:14 UTC |
| BLOAT-B-3 | `session_01TF3fwo1E8LamFZqcbNjb5x` | Fable | complete (#3982 + #3983 merged) — archivable |
| BLOAT-B-5 | `session_01UCQgY2zZPNo4nhhfU4judg` | Fable | merged #3978/#3979; follow-up + need_input (see decisions #4) |

Program-lane sessions carry the tag `model-audit-program`. Adjacent
**non-program** sessions observed the same day (calibration program: CAISO /
MISO / ERCOT backcast, NYISO-136, NEISO H1-2026 intake, run-explorer pages)
are tracked only where they move keepers or collide with program surfaces.

## Refresh protocol

On each owner "refresh", the director: (1) lists sessions + fetches fresh
`origin/main`, re-reads plan §8 and lane handoffs; (2) reports each
workstream as **not started / in progress with % / completed / pending
blockers**; (3) dispatches any lane whose gate has cleared, appends the §8
ledger entry, and updates this board in the same pass.
