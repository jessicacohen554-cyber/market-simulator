# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `4bfb618` (2026-07-18, turn 8).
- **Plan base SHA:** `c95176e`.
- **turn 8 refresh:** capacity.py re-confirmed FIXED — 3967 lines, all symbols, parses
  clean, **byte-identical to the #2438 restore** (untouched). Only new merge since turn 7
  is PR **#2441** = the FF-1A scorecard doc fill (#2440's content; docs-only, did NOT touch
  capacity.py). So #2440 is now ON MAIN ⇒ **FF-1A-C prelude satisfied** (run against
  latest origin/main). PR **#2439 still open, now `dirty`/conflicting (51 files,
  +81,978/−1,531)** — a sprawling stale duplicate; CLOSE, do not merge (its dirty state
  blocks self-merge, lowering risk).
- **✅ MAIN RESTORED** (turn 7). PR **#2438** un-truncated `capacity.py` (2291→**3967**
  lines) and re-applied R-NEW. Manager-verified faithful: all 7 deleted symbols
  (`evolve_fleet`, `accredited_firm_capacity_mw`, `apply_ccs_retrofit`,
  `apply_economic_new_entry`, `apply_reserve_margin_build`, `capacity_reserve_position`,
  `resolve_reserve_margin_build_enabled`) back with byte-identical bodies; the last-good
  573350d content returned byte-for-byte + a localized R-NEW delta (302/97). The
  retirement pipeline (`_execution_lag_years`/`_apply_pipeline_retirements`/
  `apply_economic_retirements`) is **md5-identical** (`46b96a2…`) to the broken-tree
  version, so the PJM/MISO R-NEW probe reports (run on the truncated tree) exercised the
  same code and **remain valid** — the truncation only deleted forecast-evolution helpers
  the hindcast retirement probes don't drive. The #1 program blocker is **cleared**.

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
| FF-1A | FABLE | 1 | L-CAP | ⛔ owner-gated | **verified-issues — scorecard partial** | Code+restore LANDED (#2438, verified-pass). R-NEW implemented (`retirement_rule` pipeline, default legacy byte-identical), probes run. Scorecard findings doc on main (PR #2441/#2440) fills PJM+MISO measured (inversion CLOSED: gas_st false-retire 8.6→0 GW, recall→76%) but **ERCOT leg / LOYO folds / precise BLK-10 / dashboard registration = PENDING** (bundles absent, need re-solve). → correction **FF-1A-C**. |
| FF-1A-restore | FABLE | 1 | L-CAP | — | **verified-pass** | PR #2438: capacity.py 2291→3967 byte-exact restore + R-NEW re-apply + D2 delete; register_hindcast arm updated (staged-thin→r-new); 273-line test delta incl. `test_flag_off_is_byte_identical` / `test_staged_thinning_fields_are_deleted` / `test_pipeline_requires_year`. Main un-broken. |
| FF-1A-C | FABLE | 1 | L-CAP | ⛔ | **correction-sent (turn 7); prelude satisfied turn 8** | #2440 now on main. Run vs latest origin/main: solve ERCOT composition leg; compute LOYO folds + precise BLK-10 fired-MW (re-solve/re-score PJM+MISO R-NEW bundles); register 3 R-NEW legs on forecast-validation dashboard; fill §5/§7/§9 complete. Unblocks FF-2A (BLK-10) + FF-2C (flip-gate). |
| FF-1B | FABLE | 1 | L-SCAR | — | **verified-pass** | PR #2423: correlated cold-event derate (default-off, measured, rule-25 no-op cross-ISO); in-year ORDC scarcity forms (Heather $4,968/MWh); CT screen 6.4→11.9 $/kW-yr; ≈56/66 residual handed to G-20/G-22 as a number. Did NOT touch capacity.py. |
| FF-1C | OPUS | 1 | L-INP | — | **verified-pass** | #2422: demand/DC currency + double-count fix + hydro-verify |
| FF-1D | OPUS | 1 | L-VAL | — | not-sent | blocked: FF-0E not landed |
| FF-1E | OPUS | 1 | L-INP | — | **sent** (turn 4) | in flight — no PR |
| FF-2A | FABLE | 2 | L-CAP | ⛔ | not-sent | **blocked: FF-1A verified-issues** — BLK-10 re-measure + findings are its inputs; releases only after **FF-1A-C** lands verified-pass |
| FF-2B | OPUS | 2 | L-CAP | — | not-sent | blocked: FF-2A |
| FF-2C | OPUS | 2 | L-CAP | owner-gated | not-sent | blocked: FF-2B + owner; FF-1A scorecard (§6 flip-gate) is its input — needs FF-1A-C |
| FF-2D | OPUS | 2 | L-VAL | ⛔ T1 gate | not-sent | blocked: W1/W2 |
| FF-3A | OPUS | 3 | L-VAL | ⛔ T2 | not-sent | blocked: FF-2D + owner |
| FF-3B | OPUS | 3 | L-CES | — | not-sent | blocked: W2 |
| FF-3C | FABLE | 3 | L-PERF | conditional | not-sent | trigger-gated |
| FF-3D | OPUS | 3 | L-CAP | owner-gated | not-sent | blocked: owner |
| FF-4A | OPUS | 4 | L-VAL | ⛔ owner-gated | not-sent | blocked: FF-3A + owner |
| FF-4B | FABLE | 4 | L-VAL | — | not-sent | blocked: FF-4A |
| FF-4C | OPUS | 4 | L-VAL | owner-gated | not-sent | blocked: FF-4A + owner |
| FF-5A | OPUS | 5 | L-DASH | — | not-sent | blocked: Wave 4 |

Out-of-program / trivial this window: #2438 (restore, turn 7), #2441 (FF-1A scorecard doc
fill = #2440's content, turn 8), #2437 (this ledger, turn 6). One OPEN PR pending owner
action — see below.

---

## Open PRs pending owner action

- **PR #2440 — MERGED turn 8** (as PR **#2441**). FF-1A scorecard fill now on main:
  per-ISO gate scorecard with **measured** PJM+MISO R-NEW numbers; ERCOT leg / LOYO /
  precise BLK-10 / dashboard still PENDING (→ FF-1A-C). Docs-only; did NOT touch
  capacity.py.
- **PR #2439 — CLOSE (still open, do NOT merge).** Redundant duplicate of #2438; now
  `dirty`/conflicting against current main (51 files, +81,978/−1,531 — carries far more
  than a restore). #2438 already landed the restore + R-NEW; merging #2439 re-litigates it
  and invites a conflict mess. The dirty state blocks self-merge (good). Owner: close it.

---

## Owner decisions

**Received:**
- **D1 = B (R-NEW), by action** (2026-07-18): FF-1A launched implementing R-NEW + D2
  staged-thinning removal ⇒ D1=B, D2=delete, D3=gas_cc-lag=1. Implemented & restored;
  measured inversion-closure confirmed. Owner: correct me if D1≠B.

**AWAITING:**
- **PR triage:** close #2439 (#2440 already merged as #2441).
- **BAU DC posture** (`datacenter_load_path` `off` vs `mid`; FF-1C rec: mid). Gates FF-4A.
- Availability derate default (FF-1B — evidence in: 6.4→11.9 $/kW-yr, scarcity forms;
  owner may set ON-for-forecast), entry-lookahead posture (FF-2A), per-ISO flips (FF-2C),
  NYISO R5a (FF-3D), golden freeze (FF-4A), PB-5 (FF-4C).

---

## Corrections issued

1. **FF-0A-fix [OPUS]** (turn 2) — RESOLVED turn 3 (#2419).
2. **FF-0B-redo [OPUS]** (turn 2) — open, in flight.
3. **FF-1A-restore [FABLE]** (turn 5) — **RESOLVED turn 7 (#2438).** capacity.py
   byte-exact restored + R-NEW re-applied + D2 deleted; manager-verified faithful.
4. **FF-1A-C [FABLE]** (turn 7) — complete the FF-1A scorecard: ERCOT composition leg,
   LOYO folds, precise BLK-10 fired-MW, dashboard registration; fill §5/§7/§9. Prelude
   (#2440 merged, turn 8) **now satisfied** — runs against latest origin/main. Unblocks
   FF-2A + FF-2C. Open (no PR yet).

---

## Turn log

- **turn 1.** HEAD `f0da036`. Dispatched Wave 0.
- **turn 2.** `→6d6867b`. FF-0D pass; FF-0A/FF-0B issues → FF-0A-fix + FF-0B-redo. Released FF-1B+FF-1C.
- **turn 3.** `→fa6959e`. FF-0A-fix + FF-0C pass. FF-1A owner-gated on D1; box surfaced.
- **turn 4.** `→2144e12`. FF-1C pass. Released FF-1E. Staged FF-1A (keyed B). Surfaced DC posture.
- **turn 5 (refresh).** `→398c1f2`. FF-1B verified-pass. FF-1A verified-issues CRITICAL:
  R-NEW landed but truncated capacity.py (-39%, main broken) — issued FF-1A-restore.
- **turn 6 (refresh).** `→f637994`. Main STILL broken; FF-1A-restore not started. Turn-6
  FF-1A follow-ups #2433/#2435/#2436 piled onto the broken tree. Re-flagged; asked owner
  to stop merging FF-1A-branch PRs until the restore lands.
- **turn 7 (refresh).** `→7d4b738`. **MAIN RESTORED** — PR #2438 un-truncated capacity.py
  (2291→3967) + re-applied R-NEW; manager-verified byte-faithful (all 7 symbols back,
  retirement pipeline md5-identical ⇒ PJM/MISO probes stay valid). **FF-1A-restore
  verified-pass; #1 blocker cleared.** FF-1A downgraded to verified-issues (scorecard
  partial): open PR #2440 fills PJM+MISO measured (inversion CLOSED, gas_st 8.6→0 GW,
  recall→76%) but ERCOT leg / LOYO / BLK-10 / dashboard PENDING → issued FF-1A-C [FABLE]
  (solve-bearing). #2439 flagged redundant → close. FF-2A HELD (BLK-10/findings inputs
  incomplete until FF-1A-C). Frontier §1.2-1 rewrite **deferred to FF-1A-C** (inversion is
  measured-closed but the row can't fully close until the scorecard/flip-gate completes;
  avoids a full-file plan push mid-measurement — rule-27 caution). No downstream wave
  released (FF-1D still on FF-0E; Wave 2+ on FF-1A-C). In-flight unchanged: FF-0B-redo,
  FF-0E, FF-1E (no PRs).
- **turn 8 (refresh — owner asked "is calibration py fixed").** `→4bfb618`. **Confirmed:
  capacity.py FIXED** (3967 lines, all symbols, parses clean, byte-identical to the #2438
  restore — untouched). Only new merge: PR #2441 = FF-1A scorecard doc fill (#2440's
  content; docs-only). #2440 now on main ⇒ FF-1A-C prelude satisfied. PR #2439 still open
  but `dirty`/conflicting (51 files, +82k lines) — reconfirmed CLOSE. No new dispatches;
  FF-1A-C already issued (turn 7), everything downstream still held on it.
