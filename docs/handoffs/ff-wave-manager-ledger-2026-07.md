# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `bc46dc0` (2026-07-18, turn 11).
- **Plan base SHA:** `c95176e`.
- **🚨 turn 11 — FF-2A INTEGRITY BREACH (verified-issues CRITICAL).** FF-2A (#2453) committed
  its entire core mechanism as an **unapplied patch** (`docs/handoffs/ff2a-core.patch`, 635
  lines) instead of integrating it. On main: capacity.py + runner.py **byte-unchanged**;
  entry-stack config fields (`entry_vre_capacity_revenue`/`entry_rate_limits`/
  `entry_commissioning_lag`/`entry_throughput_window_years`) **absent**; `entry_config.py` +
  `build_throughput.py` **dead** (uncalled); `tests/test_entry_stack_ff2a.py` **fails**
  (TypeError on missing fields); harness arms broken; registered `*-ff2a` score.jsons **do not
  reproduce** from committed source (run with the patch applied locally — PJM solar 24.0→19.3
  proves it). Main not corrupted (apply-forward). Root cause: worker misread rule 27 (edit
  locally + push on-disk bytes) and committed a patch artifact. Slipped through because no
  pytest CI runs at origin/main and file-integrity-guard only checks shrinkage. → correction
  **FF-2A-integrate [FABLE]**. Also a real finding: ERCOT solar entry stayed 0.0 even with the
  mechanism (BLK-8 half-met) — diagnose, don't force. **FF-2A NOT verified — Wave 2 stays
  gated; FF-2B held.** **FF-1A-C2 (#2454) verified-pass** (doc synced, 0 PENDING). caiso-96
  (#2456) out-of-program.
- **turn 10 refresh:** **FF-1A-C LANDED** (#2448 + #2451) — all 3 R-NEW legs solved at HEAD,
  scored with real T-R10/LOYO/BLK-10 (`--flip-gate-extras` scorer added+tested), per-leg
  reports updated, dashboard sidecars registered. **PJM blk10 backstop fired 2.5 GW** (down
  from pre-R-NEW 6.43 GW, still over actual 0.447 GW → FF-2A sizing warranted), T-R10a/b PASS,
  LOYO holds 2/3. capacity.py UNTOUCHED. Rule-27: score_capacity_hindcast.py clipped then
  **self-caught + restored** (52cb462). Summary doc synced by FF-1A-C2 (turn 11).
- **turn 9 refresh:** no new FF work. #2442 caiso-94 out-of-program. Graph re-check: **FF-3D
  (NYISO R5a)** is the only lane unlockable on an owner decision alone (R5a A/B), independent
  of Wave 2; NYISO data + marker ready (Opt A immediate; Opt B needs 1 NYSRC manual DL).
- **turn 8 refresh:** capacity.py re-confirmed FIXED (byte-identical to #2438). #2441 = FF-1A
  doc fill (docs-only). #2439 still open, `dirty`/conflicting — CLOSE.
- **✅ MAIN RESTORED** (turn 7). PR **#2438** un-truncated `capacity.py` (2291→**3967** lines)
  and re-applied R-NEW; manager-verified byte-faithful (all 7 symbols back, retirement pipeline
  md5-identical). The FF-1A truncation blocker is **cleared**.

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
| FF-1A | FABLE | 1 | L-CAP | — | **verified-pass (complete)** | Code+restore (#2438) + measurement (#2448/#2451) + doc sync (#2454). Inversion CLOSED; 3 legs scored/registered; flip-gate scorecard complete (FF-2C input ready). |
| FF-1A-restore | FABLE | 1 | L-CAP | — | **verified-pass** | PR #2438: capacity.py 2291→3967 byte-exact restore + R-NEW + D2 delete. Main un-broken. |
| FF-1A-C | FABLE | 1 | L-CAP | — | **verified-pass (via FF-1A-C2)** | LANDED #2448/#2451: 3 R-NEW legs solved/scored/registered (real T-R10/LOYO/BLK-10). Doc-sync gap closed by FF-1A-C2 (#2454). |
| FF-1A-C2 | OPUS | 1 | L-CAP | — | **verified-pass** — LANDED #2454 | findings doc synced, 0 PENDING; only .gitignore + .md touched (no source change). FF-1A now complete end-to-end. |
| FF-1B | FABLE | 1 | L-SCAR | — | **verified-pass** | PR #2423: correlated cold-event derate; in-year ORDC scarcity forms; residual to G-20/G-22. |
| FF-1C | OPUS | 1 | L-INP | — | **verified-pass** | #2422: demand/DC currency + double-count fix + hydro-verify |
| FF-1D | OPUS | 1 | L-VAL | — | not-sent | blocked: FF-0E not landed |
| FF-1E | OPUS | 1 | L-INP | — | **sent** (turn 4) | in flight — no PR (shares entry screen with FF-2A — rebase order) |
| FF-2A | FABLE | 2 | L-CAP | ⛔ | **verified-issues CRITICAL (non-integration)** — LANDED #2453 | Core mechanism committed as UNAPPLIED patch (ff2a-core.patch); capacity.py/runner.py byte-unchanged, config fields absent, modules dead, test fails (TypeError), sidecars unreproducible. → **FF-2A-integrate [FABLE]**. New modules/tests/reports OK (apply-forward, not revert). ERCOT solar still 0 (BLK-8 half-met) = finding. |
| FF-2A-integrate | FABLE | 2 | L-CAP | ⛔ | **correction-sent (turn 11)** | apply ff2a-core.patch to real source (Edit+push on-disk bytes, rule-27 blob-verify capacity.py); delete patch; green tests; re-run 3 legs against integrated code + confirm reproduce; re-register; diagnose ERCOT solar=0 (don't force). |
| FF-2B | OPUS | 2 | L-CAP | — | not-sent | blocked: FF-2A-integrate (capacity.py hand-off does not exist yet) |
| FF-2C | OPUS | 2 | L-CAP | owner-gated | not-sent | blocked: FF-2A + owner; flip-gate scorecard (FF-1A-C2) is its input — now READY |
| FF-2D | OPUS | 2 | L-VAL | ⛔ T1 gate | not-sent | blocked: W1/W2 |
| FF-3A | OPUS | 3 | L-VAL | ⛔ T2 | not-sent | blocked: FF-2D + owner |
| FF-3B | OPUS | 3 | L-CES | — | not-sent | blocked: W2 (readiness R1 = FF-2A headline; would NO-GO now) |
| FF-3C | FABLE | 3 | L-PERF | conditional | not-sent | trigger-gated (T2 budget breach / I9-I10 FAIL) — inactive |
| FF-3D | OPUS | 3 | L-CAP | owner-gated | not-sent | **UNLOCKABLE NOW on owner R5a pick (A/B)** — independent of Wave 2; NYISO data+marker ready. Opt A immediate; Opt B needs 1 NYSRC manual DL. |
| FF-4A | OPUS | 4 | L-VAL | ⛔ owner-gated | not-sent | blocked: FF-3A + owner |
| FF-4B | FABLE | 4 | L-VAL | — | not-sent | blocked: FF-4A |
| FF-4C | OPUS | 4 | L-VAL | owner-gated | not-sent | blocked: FF-4A + owner |
| FF-5A | OPUS | 5 | L-DASH | — | not-sent | blocked: Wave 4 |

Out-of-program / trivial: #2438 (restore), #2441 (FF-1A doc fill), #2442/#2444 (caiso-94),
#2445/#2449 (caiso-95), #2447 (miso-72), #2450 (ercot commitment-posture lever),
#2456 (caiso-96 startup-trajectory), #2437/#2443/#2446/#2452 (this ledger). One OPEN PR
pending owner action — see below.

---

## Open PRs pending owner action

- **PR #2439 — CLOSE (still open, do NOT merge).** Redundant duplicate of #2438; `dirty`/
  conflicting (51 files, +81,978/−1,531). #2438 already landed the restore. Owner: close it.

---

## Owner decisions

**Received:**
- **D1 = B (R-NEW), by action** (2026-07-18): D1=B, D2=delete, D3=gas_cc-lag=1. Implemented,
  restored, measured, doc-complete. Owner: correct me if D1≠B.

**AWAITING (each changes what I dispatch next):**
- **FF-3D NYISO R5a pick** (Option A lagged model-derived vs Option B NYCA-wide static
  proxy). Unlocks FF-3D immediately (parallel to Wave 2). Opt B needs the NYSRC Appendix D
  Table D.1.1 manual download first.
- **PR triage:** close #2439.
- **BAU DC posture** (`datacenter_load_path` `off` vs `mid`; FF-1C rec: mid). Gates FF-4A.
- Availability derate default (FF-1B), entry-lookahead posture (FF-2A item 4), per-ISO flips
  (FF-2C — flip-gate scorecard now ready), golden freeze (FF-4A), PB-5 (FF-4C).

---

## Corrections issued

1. **FF-0A-fix [OPUS]** (turn 2) — RESOLVED turn 3 (#2419).
2. **FF-0B-redo [OPUS]** (turn 2) — open, in flight.
3. **FF-1A-restore [FABLE]** (turn 5) — **RESOLVED turn 7 (#2438).** capacity.py byte-exact
   restored + R-NEW + D2; manager-verified faithful.
4. **FF-1A-C [FABLE]** (turn 7; re-sent turn 9) — **LANDED turn 10 (#2448/#2451).** Measurement
   done; doc-sync gap → FF-1A-C2.
5. **FF-1A-C2 [OPUS]** (turn 10) — **RESOLVED turn 11 (#2454), verified-pass.** Findings doc
   synced, 0 PENDING.
6. **FF-2A-integrate [FABLE]** (turn 11) — **integrity breach fix.** FF-2A committed core
   changes as an unapplied patch; apply for real (Edit + push on-disk bytes, rule-27
   blob-verify capacity.py), delete the patch, green the tests, re-run + reproduce + re-register
   the 3 legs, diagnose ERCOT solar=0. Open.

---

## Turn log

- **turn 1.** HEAD `f0da036`. Dispatched Wave 0.
- **turn 2–6.** Wave 0 verify + corrections (FF-0A-fix, FF-0B-redo); FF-1B/1C/1E released; FF-1A
  truncated capacity.py (main broken) → FF-1A-restore issued, main stayed broken through turn 6.
- **turn 7 (refresh).** `→7d4b738`. **MAIN RESTORED** (#2438). FF-1A-restore verified-pass;
  FF-1A verified-issues (scorecard partial) → FF-1A-C. FF-2A HELD.
- **turn 8 (refresh — "is calibration py fixed").** `→4bfb618`. Confirmed capacity.py FIXED.
  #2441 FF-1A doc fill. #2439 dirty → close.
- **turn 9 (refresh — "send next wave"/"anything unlocked").** `→ab69df3`. No new FF. Wave 2
  substantively gated (gap-register §3.9 BLK-10). Surfaced FF-3D (owner R5a) + scoped-FF-2A.
- **turn 10 (refresh + dispatch — "refresh and send prompts").** `→ae754e2`. **FF-1A-C LANDED**
  (#2448/#2451): 3 R-NEW legs scored (PJM blk10 2.5 GW over-fire → FF-2A sizing warranted).
  Verified-issues (doc-sync) → FF-1A-C2 [OPUS]. Released **FF-2A [FABLE]** (Wave 2 opened).
- **turn 11 (refresh — owner: "refresh").** `→bc46dc0`. **FF-1A-C2 verified-pass** (#2454, doc
  synced). **FF-2A verified-issues CRITICAL** (#2453): core mechanism committed as an unapplied
  `ff2a-core.patch` — capacity.py/runner.py byte-unchanged, config fields absent, modules dead,
  `test_entry_stack_ff2a.py` fails (TypeError), `*-ff2a` sidecars unreproducible from source
  (patch applied locally only). Flagged owner in bold; issued **FF-2A-integrate [FABLE]**
  (apply-forward, not revert — main uncorrupted). ERCOT solar=0 even with mechanism = finding
  (BLK-8 half-met). **Wave 2 stays gated; FF-2B held** (no capacity.py hand-off). caiso-96
  (#2456) out-of-program. Process note: slipped through because origin/main has no pytest CI
  and file-integrity-guard only checks shrinkage — a patch-instead-of-integrate breach is
  invisible to both. Still awaiting owner: FF-3D R5a pick, close #2439, DC posture.
