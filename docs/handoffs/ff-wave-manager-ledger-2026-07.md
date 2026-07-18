# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `f637994` (2026-07-18, turn 6).
- **Plan base SHA:** `c95176e`.
- **⚠️ MAIN STILL BROKEN** as of `f637994` — the FF-1A `capacity.py` truncation
  (deleted `evolve_fleet` + CCS/new-entry/backstop/accredited-capacity; dangling at
  `runner.py:789`, `capacity.py:1106`, `runner.py:2096`) is **NOT fixed**. capacity.py
  is untouched since the truncation (still 2291 lines). Turn-6 follow-ups #2433/#2435
  (PJM/MISO R-NEW probe reports) + #2436 (harness/test rebase) landed MORE work on top of
  the broken tree without restoring it. **FF-1A-restore has no PR — not started.** NO
  downstream capacity work releases until it lands; the PJM/MISO probe reports are
  PROVISIONAL (runs predate/diverge from a working tree — re-validate after restore).

Status vocabulary: `not-sent` · `sent` · `landed` · `verified-pass` ·
`verified-issues` · `correction-sent`.

---

## Session status table

| FF id | Model | Wave | Lane | Gate | Status | Evidence |
|---|---|---|---|---|---|---|
| FF-0A | FABLE | 0 | L-VAL | ⛔ rubric | **verified-pass** | rubric #2414 + scorer #2419 |
| FF-0A-fix | OPUS | 0 | L-VAL | — | **verified-pass** | #2419: 73 tests pass |
| FF-0B | OPUS | 0 | L-VAL | — | superseded by FF-0B-redo | #2412 non-delivery |
| FF-0B-redo | OPUS | 0 | L-VAL | — | **correction-sent** (turn 2) | in flight — no PR |
| FF-0C | FABLE | 0 | L-CAP | — | **verified-pass** | #2418: R-NEW memo + owner box |
| FF-0D | OPUS | 0 | L-INP | — | **verified-pass** | #2413: audit, no source changes |
| FF-0E | OPUS | 0 | L-VAL | — | sent | in flight — no PR |
| FF-1A | FABLE | 1 | L-CAP | ⛔ owner-gated | **verified-issues — CRITICAL (rule-27), UNRESOLVED** | PR #2430 truncated capacity.py 3762→2291 (-39%): evolve_fleet + CCS/new-entry/backstop/accredited-capacity deleted, **main broken**. Turn-6 follow-ups #2433 (PJM probe report), #2435 (MISO probe report), #2436 (harness/test rebase) added MORE onto the broken tree — capacity.py STILL untouched. Probe reports provisional. |
| FF-1A-restore | FABLE | 1 | L-CAP | ⛔ | **correction-sent (turn 5) — NOT STARTED (no PR)** | revert-then-redo: restore capacity.py from 573350d, re-apply ONLY R-NEW+D2, blob-verify, green suite, re-validate PJM/MISO probes, complete real scorecard |
| FF-1B | FABLE | 1 | L-SCAR | — | **verified-pass** | PR #2423: correlated cold-event derate (default-off, measured CORRELATED_OUTAGE_CURVE from CAMPD, rule-25 no-op cross-ISO); in-year ORDC scarcity forms (Heather $4,968/MWh); CT screen 6.4→11.9 $/kW-yr (~17.5% of SOM 68); ≈56/66 residual handed to G-20/G-22 as a number (no adder); ORDC-sigma double-count seam documented. Did NOT touch capacity.py. |
| FF-1C | OPUS | 1 | L-INP | — | **verified-pass** | #2422: demand/DC currency + double-count fix + hydro-verify |
| FF-1D | OPUS | 1 | L-VAL | — | not-sent | blocked: FF-0E not landed |
| FF-1E | OPUS | 1 | L-INP | — | **sent** (turn 4) | in flight — no PR |
| FF-2A | FABLE | 2 | L-CAP | ⛔ | not-sent | **blocked: FF-1A verified-issues** — releases only after FF-1A-restore lands verified-pass |
| FF-2B | OPUS | 2 | L-CAP | — | not-sent | blocked: FF-2A |
| FF-2C | OPUS | 2 | L-CAP | owner-gated | not-sent | blocked: FF-2B + owner; FF-1A scorecard is its input |
| FF-2D | OPUS | 2 | L-VAL | ⛔ T1 gate | not-sent | blocked: W1/W2 |
| FF-3A | OPUS | 3 | L-VAL | ⛔ T2 | not-sent | blocked: FF-2D + owner |
| FF-3B | OPUS | 3 | L-CES | — | not-sent | blocked: W2 |
| FF-3C | FABLE | 3 | L-PERF | conditional | not-sent | trigger-gated |
| FF-3D | OPUS | 3 | L-CAP | owner-gated | not-sent | blocked: owner |
| FF-4A | OPUS | 4 | L-VAL | ⛔ owner-gated | not-sent | blocked: FF-3A + owner |
| FF-4B | FABLE | 4 | L-VAL | — | not-sent | blocked: FF-4A |
| FF-4C | OPUS | 4 | L-VAL | owner-gated | not-sent | blocked: FF-4A + owner |
| FF-5A | OPUS | 5 | L-DASH | — | not-sent | blocked: Wave 4 |

Out-of-program / trivial this window (turn 6): #2429 pjm-115 keeper (out-of-program);
#2434 FF-1C session notes (superseded by #2422); #2431 FF-1B re-merge.

---

## Owner decisions

**Received:**
- **D1 = B (R-NEW), by action** (2026-07-18): FF-1A launched implementing R-NEW + D2
  staged-thinning removal ⇒ read as the owner launching the turn-4 staged Option-B prompt
  (= D1=B, D2=delete, D3=gas_cc-lag-1 assumed). The DECISION stands; the IMPLEMENTATION is
  broken (rule-27) and is being restored by FF-1A-restore. Owner: correct me if D1≠B.

**AWAITING:**
- **BAU DC posture** (`datacenter_load_path` `off` vs `mid`; FF-1C rec: mid). Gates FF-4A.
- Entry-lookahead (FF-2A), availability derate default (FF-1B — evidence now in: 6.4→11.9
  $/kW-yr, scarcity forms; owner may set ON-for-forecast), per-ISO flips (FF-2C), NYISO
  R5a (FF-3D), golden freeze (FF-4A), PB-5 (FF-4C).

---

## Corrections issued

1. **FF-0A-fix [OPUS]** (turn 2) — RESOLVED turn 3 (#2419).
2. **FF-0B-redo [OPUS]** (turn 2) — open, in flight.
3. **FF-1A-restore [FABLE]** (turn 5) — **rule-27 core-file truncation, main broken.**
   Restore capacity.py from last-good (573350d), re-apply ONLY R-NEW + D2, blob-verify,
   green the suite, THEN complete the deferred PJM/MISO/ERCOT measurement + real scorecard.
   **Turn 6: still NOT started (no PR); re-flagged.**

---

## Turn log

- **turn 1.** HEAD `f0da036`. Dispatched Wave 0.
- **turn 2.** `→6d6867b`. FF-0D pass; FF-0A/FF-0B issues → FF-0A-fix + FF-0B-redo. Released FF-1B+FF-1C.
- **turn 3.** `→fa6959e`. FF-0A-fix + FF-0C pass. FF-1A owner-gated on D1; box surfaced.
- **turn 4.** `→2144e12`. FF-1C pass. Released FF-1E. Staged FF-1A (keyed B). Surfaced DC posture.
- **turn 5 (refresh).** `→398c1f2` (FF-1A #2430, FF-1B #2423). **FF-1B verified-pass**
  (correlated derate, structurally clean). **FF-1A verified-issues CRITICAL**: R-NEW logic
  landed but truncated capacity.py (-39%, main broken) — flagged owner in bold, issued
  FF-1A-restore [FABLE] revert-then-redo. Recorded D1=B by action. FF-2A HELD (broken
  prereq). Process note: #2430 self-merged in 9s under a docs title, bypassing the
  integrity guard. Frontier §1.2-1 stays OPEN (retirement redesign not validly landed).
- **turn 6 (refresh).** `→f637994`. **MAIN STILL BROKEN** — capacity.py untouched since
  the truncation; FF-1A-restore never started (no PR). Turn-6 FF-1A follow-ups #2433 (PJM
  R-NEW probe report), #2435 (MISO R-NEW probe report), #2436 (run_capacity_hindcast.py +
  test_config rebase) landed MORE onto the broken tree without restoring it. Re-flagged in
  bold; re-issued FF-1A-restore as the #1 blocker; asked owner to stop merging FF-1A-branch
  PRs until the restore lands. Probe reports marked provisional. Out-of-program: #2429
  pjm-115 keeper. Trivial: #2434 FF-1C session notes (superseded by #2422), #2431 FF-1B
  re-merge. Nothing else released (all downstream still blocked on the restore / FF-0E).
