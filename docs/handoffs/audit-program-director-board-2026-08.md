# Model Audit Program — Director Status Board (2026-08)

> **STATUS: ACTIVE** — live rollup maintained by the program-director session,
> updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable
> event record; this board is the at-a-glance state). Completion figures are
> the director's estimate against each workstream's full DoD (A+B halves).

**Snapshot:** 2026-08-15 ~22:45 UTC · `origin/main` @ `04d1cf0` ·
**AUDIT-A DELIVERED and merged (#3991).** Dispatch mechanics corrected by
owner directive: lanes are owner-launched from director-issued prompts; the
21:13–21:14 UTC director-seeded sessions are archived (AUDIT-A after
delivering; the other three without pushing a branch).

## Workstream rollup

| WS | State | Completion | Session | Blockers / next |
|----|-------|------------|---------|-----------------|
| WS1 `AUDIT` | **AUDIT-A COMPLETED — merged #3991** (`docs/audit/third-party-audit-2026-08.md` + positioning matrix, §8 gap register: 2 PERF ▸chartered, 2 DEBUG, 5 DOCS, 1 SITE ▸seeded, 8 OWNER rows); AUDIT-B held (G3) | **In progress ~85%** | seeded session delivered, archived | gap rows routed into lane prompts this sitting; AUDIT-B at G3 |
| WS2 `DEBUG` | DEBUG-A **merged** (#3937); DEBUG-B **merged** (pjm-162 keeper CANDIDATE, bundle held from prune); manager reissue prompt **issued for owner launch** (now incl. gap rows B1, B2 + O2 resolution) | **In progress ~75%** | owner launches (Fable) | owner cards on launch: pjm-162 promotion (paired with O2 attestation re-score) + ≤2022 clock extension; then residue |
| WS3 `PERF` | PERF-A **merged**; PERF-B held | **In progress ~50%** | PERF-B prompt staged | gate **G1 — one leg away** (DOCS-A merge) + owner ack of the warm-start memo closure |
| WS4 `DOCS` | DOCS-A prompt **issued for owner launch** (now incl. gap rows D1 priority surgical fix, D2 seed, D4, D5); DOCS-B held (G2) | **Not started** | owner launches (Opus) | none once launched — **last Wave-1 leg; G1 declares on its merge** |
| WS5 `SITE` | Held by design | **Not started** | — | gate **G3** (S1 hero-line two-line hotfix remains the owner's standing option) |
| WS6 `BLOAT` | BLOAT-A ✓; B-1..B-5 all merged; **B-6R/B-7 re-measured close-out open** | **In progress ~90%** | close-out prompt held | waits on GOLDEN-TIER-FIX green |
| — `GOLDEN-TIER-FIX` (chartered sub-lane; **G2/G3 critical path**; audit gap row P2) | prompt **issued for owner launch** | **Not started** | owner launches (Fable) | owner merge when branch ready → single authorized golden-tier dispatch |

Recovered at tip by BLOAT-B: ≈ 3,737 MiB (B-1 739.8 + B-2 361.8 + B-3 117.0
+ B-5 2,518.5, per PR records); tip ≈ 6.4 GB.

## Gates

- **G0** adopted ✓ (2026-08-13).
- **G1** — **one leg remaining: DOCS-A merged** (AUDIT-A #3991, DEBUG-A,
  PERF-A, BLOAT-A all on main), plus the §6 decision-1 (warm-start) ack.
- **G2** — after G1: PERF-B (fast-tier sparse block + byte-gated wins),
  keepers settling, owner flips branch protection (memo ready). FFR Q.2
  battery commissions at this gate.
- **G3** — evidence-blocked until GOLDEN-TIER-FIX's green dispatch; then
  DOCS-B + the B-6R/B-7 close-out.
- **G4** — SITE-A + AUDIT-B after G3.

## Pending owner decisions (live)

Near-term (cards served in the owner-launched DEBUG-MGR session):

1. **pjm-162 PJM keeper promotion** (audit row O1) — paired with the **O2
   C6-attestation discrepancy re-score** the manager resolves before serving
   the card (`status/PJM.js` C6 PASS vs the finding's UNATTESTED on the same
   bundle).
2. **≤2022 PJM input-clock extension charter** (audit row O3).
3. **Warm-start plan §6 decision 1** — PERF-A memo recommends CLOSE as
   overtaken; ack retires it from the G1 checklist.
4. **BLOAT-B-5 session** (`session_01UCQgY2zZPNo4nhhfU4judg`) need_input:
   the 4 formal decision-card docs for its dispatch record (verdicts already
   in plan §8: A2/B1b/B3 SIGNED, C VETOED).

Queued from the audit gap register (full text: audit doc §8 OWNER rows):
**O4** holdout-freeze premise (CAMPD economic-layup finding), **O5** NEISO
legacy-P2 anomaly (re-solve or document), **O6** locked-test one-shot
scheduling at G2, **O7** ERCOT P0 bit-identity forfeiture
(accept-or-restore), **O8** NEISO SMD 2018–2023 DST-naive vintage repair
charter (likely solve-affecting → [R-ALLYEARS] re-solve).

## Session roster (program lanes, 2026-08-15)

| Lane | Session | Model | Status at snapshot |
|------|---------|-------|--------------------|
| Director (this) | `session_01UXdTbfSK7gGxJyahrEsboM` | Fable | active |
| AUDIT-A | seeded `session_01CKURpfSiq5Z55bWN8QhtU2` | Fable | **delivered** (#3991 merged), archived |
| DOCS-A | owner launches — ID re-keyed at next refresh | Opus | prompt issued 22:45 UTC (seeded session usage-capped, no branch) |
| GOLDEN-TIER-FIX | owner launches — ID re-keyed at next refresh | Fable | prompt issued 22:45 UTC (seeded session usage-capped, no branch) |
| DEBUG-MGR (reissue) | owner launches — ID re-keyed at next refresh | Fable | prompt issued 22:45 UTC (seeded session stalled on interactive permission, no branch) |
| BLOAT-B-3 | `session_01TF3fwo1E8LamFZqcbNjb5x` | Fable | complete (#3982 + #3983 merged) — archivable |
| BLOAT-B-5 | `session_01UCQgY2zZPNo4nhhfU4judg` | Fable | merged #3978/#3979; follow-up + need_input (decisions #4) |

Operational notes: (a) two seeded sessions struck the account's five-hour
usage window before 22:00Z — if parallel launches trip it again, stagger
(DEBUG-MGR and GOLDEN-TIER-FIX first; they gate the most); (b) the earlier
"director branch deleted from origin" observation is RESOLVED benign — the
owner merged the branch as PR #3989 and GitHub auto-deleted it; (c) this
director container's `git push` is unreliable (hangs/500s; reads fine) —
director pushes fall back to the GitHub API when needed.

Adjacent **non-program** sessions (calibration program: CAISO / MISO / ERCOT
backcast, NYISO-136, NEISO H1-2026 intake, run-explorer pages) are tracked
only where they move keepers or collide with program surfaces.

## Refresh protocol

On each owner "refresh", the director: (1) lists sessions + fetches fresh
`origin/main`, re-reads plan §8 and lane handoffs; (2) reports each
workstream as **not started / in progress with % / completed / pending
blockers**; (3) issues prompts for any lane whose gate has cleared, appends
the §8 ledger entry, and updates this board in the same pass.
