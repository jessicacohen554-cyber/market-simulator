# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `bc46dc0` (2026-07-18, turn 11).
- **Plan base SHA:** `c95176e`.
- **turn 12 — owner decisions received; 2 sessions dispatched (no refresh).** Owner resolved 4
  gated calls: (1) **capacity-market clearing ON for all ISOs that have one = PJM/MISO/NYISO/
  NEISO/CAISO (all but ERCOT)** — the approved TARGET; FF-2C executes per-ISO by READINESS
  (PJM/MISO after FF-2A-integrate; NYISO after FF-3D; NEISO needs first cap-hindcast evidence;
  CAISO is RA-not-auction → RA-specific construction verified before flip). Rule 1: a flip that
  worsens fit is a root-cause bug, not a revert. (2) **NYISO R5a = Option B** (NYCA-wide static
  proxy; session downloads NYSRC App-D Table D.1.1). (3) **datacenter_load_path default = mid.**
  (4) **correlated_forced_outage default = ON.** #2439 owner says already handled → resolved.
  Dispatched **FF-3D [OPUS]** (R5a Opt B + download + NYISO curve-ON hindcast pair) and **FF-1F
  [OPUS]** (flip DC=mid + derate=ON defaults, backcast byte-identity, + record all 4 decisions
  in plan §2.1). FF-2C now owner-approved but still blocked on FF-2A-integrate.
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
- **turn 10 refresh:** **FF-1A-C LANDED** (#2448 + #2451) — 3 R-NEW legs solved at HEAD, scored
  with real T-R10/LOYO/BLK-10; **PJM blk10 fired 2.5 GW** (down from 6.43, still over 0.447 →
  FF-2A sizing warranted), T-R10 PASS, LOYO 2/3. capacity.py untouched. Rule-27 clip of
  score_capacity_hindcast.py self-caught + restored (52cb462). Summary doc synced by FF-1A-C2.
- **turn 9 refresh:** no new FF work. #2442 caiso-94 out-of-program. **FF-3D (NYISO R5a)** the
  only lane unlockable on an owner decision alone — now dispatched (turn 12, Option B).
- **turn 8 refresh:** capacity.py re-confirmed FIXED (byte-identical to #2438). #2439 dirty →
  owner handled (turn 12).
- **✅ MAIN RESTORED** (turn 7). PR **#2438** un-truncated `capacity.py` (2291→**3967** lines)
  and re-applied R-NEW; manager-verified byte-faithful. The FF-1A truncation blocker cleared.

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
| FF-1A-C2 | OPUS | 1 | L-CAP | — | **verified-pass** — LANDED #2454 | findings doc synced, 0 PENDING; only .gitignore + .md touched. FF-1A complete end-to-end. |
| FF-1B | FABLE | 1 | L-SCAR | — | **verified-pass** | PR #2423: correlated cold-event derate; in-year ORDC scarcity forms; residual to G-20/G-22. |
| FF-1C | OPUS | 1 | L-INP | — | **verified-pass** | #2422: demand/DC currency + double-count fix + hydro-verify |
| FF-1D | OPUS | 1 | L-VAL | — | not-sent | blocked: FF-0E not landed |
| FF-1E | OPUS | 1 | L-INP | — | **sent** (turn 4) | in flight — no PR (shares entry screen with FF-2A — rebase order) |
| FF-1F | OPUS | 1 | L-INP | — | **sent (turn 12)** | owner posture defaults: flip datacenter_load_path "off"→"mid" + correlated_forced_outage False→ON; backcast byte-identity; no ORDC double-count; T0 smoke; + record all 4 owner decisions in plan §2.1. Coordinates with FF-2A-integrate on scenarios.py. |
| FF-2A | FABLE | 2 | L-CAP | ⛔ | **verified-issues CRITICAL (non-integration)** — LANDED #2453 | Core mechanism committed as UNAPPLIED patch (ff2a-core.patch); capacity.py/runner.py byte-unchanged, config fields absent, modules dead, test fails (TypeError), sidecars unreproducible. → **FF-2A-integrate**. New modules/tests/reports OK (apply-forward). ERCOT solar still 0 (BLK-8 half-met) = finding. |
| FF-2A-integrate | FABLE | 2 | L-CAP | ⛔ | **correction-sent (turn 11)** | apply ff2a-core.patch to real source (Edit+push on-disk bytes, rule-27 blob-verify capacity.py); delete patch; green tests; re-run 3 legs + confirm reproduce; re-register; diagnose ERCOT solar=0. |
| FF-2B | OPUS | 2 | L-CAP | — | not-sent | blocked: FF-2A-integrate (capacity.py hand-off does not exist yet) |
| FF-2C | OPUS | 2 | L-CAP | — | not-sent | **owner-approved (turn 12): flip all-but-ERCOT**, staged by readiness (PJM/MISO first, NYISO post-FF-3D, NEISO needs evidence, CAISO RA-specific). Blocked only on **FF-2A-integrate** landing + FF-1A-C2 flip-gate scorecard (ready). Rule 1: worsened fit = root-cause, not revert. |
| FF-2D | OPUS | 2 | L-VAL | ⛔ T1 gate | not-sent | blocked: W1/W2 |
| FF-3A | OPUS | 3 | L-VAL | ⛔ T2 | not-sent | blocked: FF-2D + owner |
| FF-3B | OPUS | 3 | L-CES | — | not-sent | blocked: W2 (readiness R1 = FF-2A headline; would NO-GO now) |
| FF-3C | FABLE | 3 | L-PERF | conditional | not-sent | trigger-gated (T2 budget breach / I9-I10 FAIL) — inactive |
| FF-3D | OPUS | 3 | L-CAP | — | **sent (turn 12)** | Owner picked **R5a Option B**; session downloads NYSRC App-D Table D.1.1, implements NYCA-wide static-proxy pairing, runs NYISO fixed-vs-curve-ON hindcast pair, grades flip-gate. Leaves NYISO flip-ready (flip = FF-2C). Independent of Wave 2. |
| FF-4A | OPUS | 4 | L-VAL | ⛔ owner-gated | not-sent | blocked: FF-3A + owner |
| FF-4B | FABLE | 4 | L-VAL | — | not-sent | blocked: FF-4A |
| FF-4C | OPUS | 4 | L-VAL | owner-gated | not-sent | blocked: FF-4A + owner |
| FF-5A | OPUS | 5 | L-DASH | — | not-sent | blocked: Wave 4 |

Out-of-program / trivial: #2438 (restore), #2441 (FF-1A doc fill), #2442/#2444 (caiso-94),
#2445/#2449 (caiso-95), #2447 (miso-72), #2450 (ercot commitment-posture lever),
#2456 (caiso-96 startup-trajectory), #2437/#2443/#2446/#2452 (this ledger). #2439 handled.

---

## Owner decisions

**Received:**
- **D1 = B (R-NEW), by action** (2026-07-18): D1=B, D2=delete, D3=gas_cc-lag=1. Done.
- **Capacity-market flips (turn 12):** ON for every ISO with a real capacity market =
  PJM/MISO/NYISO/NEISO/CAISO (all but ERCOT). Target posture; FF-2C executes per-ISO by
  readiness. CAISO = RA-not-auction (RA-specific construction). Rule 1 governs (worsened fit
  → root-cause, not revert).
- **NYISO R5a = Option B** (turn 12) — NYCA-wide static proxy; FF-3D downloads NYSRC App-D
  Table D.1.1.
- **datacenter_load_path default = mid** (turn 12) — FF-1F applies.
- **correlated_forced_outage default = ON** (turn 12) — FF-1F applies (no ORDC double-count).
- **#2439** (turn 12) — owner says already handled → resolved.

**AWAITING (each changes what I dispatch next):**
- Entry-lookahead posture (FF-2A item 4 — comes back with FF-2A-integrate), golden freeze
  (FF-4A), PB-5 (FF-4C). No decision blocks any currently-dispatchable session.

---

## Corrections issued

1. **FF-0A-fix [OPUS]** (turn 2) — RESOLVED turn 3 (#2419).
2. **FF-0B-redo [OPUS]** (turn 2) — open, in flight.
3. **FF-1A-restore [FABLE]** (turn 5) — **RESOLVED turn 7 (#2438).**
4. **FF-1A-C [FABLE]** (turn 7; re-sent turn 9) — **LANDED turn 10 (#2448/#2451).** Doc-sync
   gap → FF-1A-C2.
5. **FF-1A-C2 [OPUS]** (turn 10) — **RESOLVED turn 11 (#2454), verified-pass.**
6. **FF-2A-integrate [FABLE]** (turn 11) — integrity breach fix (unapplied patch). Open.

---

## Turn log

- **turns 1–6.** Wave 0 dispatch + verify; FF-0A-fix/FF-0B-redo; FF-1B/1C/1E released; FF-1A
  truncated capacity.py (main broken) → FF-1A-restore; main stayed broken through turn 6.
- **turn 7 (refresh).** `→7d4b738`. **MAIN RESTORED** (#2438). FF-1A-restore verified-pass →
  FF-1A-C issued. FF-2A HELD.
- **turn 8 (refresh — "is calibration py fixed").** `→4bfb618`. Confirmed capacity.py FIXED.
- **turn 9 (refresh — "send next wave"/"anything unlocked").** `→ab69df3`. Wave 2 gated on
  FF-1A-C; surfaced FF-3D (owner R5a) + scoped-FF-2A.
- **turn 10 (refresh + dispatch).** `→ae754e2`. **FF-1A-C LANDED** (#2448/#2451). Verified-
  issues (doc-sync) → FF-1A-C2. Released **FF-2A** (Wave 2 opened).
- **turn 11 (refresh).** `→bc46dc0`. **FF-1A-C2 verified-pass** (#2454). **FF-2A verified-issues
  CRITICAL** (#2453 unapplied patch) → FF-2A-integrate; flagged owner in bold. Wave 2 stays
  gated; FF-2B held. Process note: no pytest CI on main.
- **turn 12 (owner decisions — no refresh).** Owner resolved the gated calls: capacity flips
  all-but-ERCOT (target, readiness-staged via FF-2C), NYISO R5a=Option B, DC default=mid,
  correlated derate default=ON, #2439 handled. Dispatched **FF-3D [OPUS]** (R5a Opt B +
  NYSRC App-D download + NYISO curve-ON hindcast pair) and **FF-1F [OPUS]** (posture-default
  flips + plan §2.1 record). FF-2C now owner-approved, still blocked on FF-2A-integrate.
  Explained the flip readiness-staging + CAISO-is-RA nuance to the owner. No new merges
  reviewed (owner gave decisions, not a refresh).
