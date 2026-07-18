# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `ae754e2` (2026-07-18, turn 10).
- **Plan base SHA:** `c95176e`.
- **turn 10 refresh:** **FF-1A-C LANDED** (#2448 + #2451) — all 3 R-NEW legs solved at HEAD,
  scored with real T-R10/LOYO/BLK-10 (`--flip-gate-extras` scorer added+tested), per-leg
  reports updated, dashboard sidecars registered. **PJM blk10 backstop fired 2.5 GW** (down
  from pre-R-NEW 6.43 GW, still over actual 0.447 GW → FF-2A sizing warranted), T-R10a/b PASS,
  LOYO holds 2/3. capacity.py UNTOUCHED (byte-identical). Rule-27: score_capacity_hindcast.py
  was clipped to a placeholder then **self-caught + restored** (52cb462) — resolved, noted.
  **Gap:** the summary findings doc `ff-retirement-rule-implementation-2026-07.md` was NOT
  synced (still 9 PENDING markers) — numbers live in score.jsons + reports. FF-1A-C =
  **verified-issues (doc-sync)** → issued FF-1A-C2 [OPUS] (doc-only). Real engineering gate
  met ⇒ **RELEASED FF-2A [FABLE]** (BLK-10 baseline in committed bundles). Out-of-program this
  window: #2444 caiso-94 promote, #2445/#2449 caiso-95 cc-underproduction, #2447 miso-72
  winter-fuel, #2450 ercot commitment-posture lever.
- **turn 9 refresh:** no new FF work landed since turn 8. Only new merge is **#2442
  caiso-94 daytime clean-import diagnostic** (out-of-program CAISO backcast diagnostic).
  Bottleneck unchanged: everything downstream waits on **FF-1A-C** producing a PR (still
  none). **Graph re-check finding:** the ONLY additional lane unlockable now is **FF-3D
  (NYISO R5a)** — gated on an OWNER DECISION alone (R5a Option A vs B), independent of
  FF-1A-C and all of Wave 2; NYISO hindcast data + calibration-complete marker already in
  place. Option A ready immediately; Option B needs one NYSRC Appendix D Table D.1.1 manual
  download. FF-3B would trivially NO-GO (its R1 = FF-2A's headline); FF-3C trigger inactive.
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
| FF-1A | FABLE | 1 | L-CAP | ⛔ owner-gated | **verified-issues — scorecard partial** | Code+restore LANDED (#2438). R-NEW implemented (`retirement_rule` pipeline, default legacy byte-identical). Measurement now complete via FF-1A-C (#2448/#2451): inversion CLOSED (gas_st 8.6→0 GW, recall→76%), 3 legs scored/registered. Summary doc sync pending (FF-1A-C2). |
| FF-1A-restore | FABLE | 1 | L-CAP | — | **verified-pass** | PR #2438: capacity.py 2291→3967 byte-exact restore + R-NEW + D2 delete; 273-line test delta. Main un-broken. |
| FF-1A-C | FABLE | 1 | L-CAP | — | **verified-issues (doc-sync gap)** — LANDED #2448/#2451 | 3 R-NEW legs solved/scored/registered at HEAD with real T-R10/LOYO/BLK-10 (PJM+MISO T-R10 PASS, LOYO holds 2/3; ERCOT gas_st FAIL = pre-declared honest limit; PJM blk10 fired 2.5 GW). Per-leg reports updated; scorer `--flip-gate-extras` added+tested; capacity.py untouched. Rule-27 clip of score_capacity_hindcast.py self-caught+restored (52cb462). **Summary findings doc NOT synced (9 PENDING)** → FF-1A-C2. |
| FF-1A-C2 | OPUS | 1 | L-CAP | — | **sent (turn 10)** | doc-only: sync ff-retirement-rule-implementation-2026-07.md §4/§5/§6/§7/§9 from committed score.jsons + reports; zero PENDING; no solve/source change. |
| FF-1B | FABLE | 1 | L-SCAR | — | **verified-pass** | PR #2423: correlated cold-event derate (default-off, measured); in-year ORDC scarcity forms; CT screen 6.4→11.9 $/kW-yr; residual to G-20/G-22. |
| FF-1C | OPUS | 1 | L-INP | — | **verified-pass** | #2422: demand/DC currency + double-count fix + hydro-verify |
| FF-1D | OPUS | 1 | L-VAL | — | not-sent | blocked: FF-0E not landed |
| FF-1E | OPUS | 1 | L-INP | — | **sent** (turn 4) | in flight — no PR (shares entry screen with FF-2A — rebase order) |
| FF-2A | FABLE | 2 | L-CAP | — | **sent (turn 10)** | RELEASED: FF-1A-C landed; BLK-10 baseline in committed bundles (PJM 2.5 GW over-fire → sizing warranted). Owns capacity.py this wave; sources FF-1A results from committed `*-rnew` sidecars/reports (summary doc lags until FF-1A-C2). Rebase onto FF-1E if it lands (shared entry screen). Headline: BLK-8 solar recall > 0. |
| FF-2B | OPUS | 2 | L-CAP | — | not-sent | blocked: FF-2A merges |
| FF-2C | OPUS | 2 | L-CAP | owner-gated | not-sent | blocked: FF-2A + owner; flip-gate scorecard (FF-1A-C2) is its input |
| FF-2D | OPUS | 2 | L-VAL | ⛔ T1 gate | not-sent | blocked: W1/W2 |
| FF-3A | OPUS | 3 | L-VAL | ⛔ T2 | not-sent | blocked: FF-2D + owner |
| FF-3B | OPUS | 3 | L-CES | — | not-sent | blocked: W2 (readiness R1 = FF-2A headline; would NO-GO now) |
| FF-3C | FABLE | 3 | L-PERF | conditional | not-sent | trigger-gated (T2 budget breach / I9-I10 FAIL) — inactive |
| FF-3D | OPUS | 3 | L-CAP | owner-gated | not-sent | **UNLOCKABLE NOW on owner R5a pick (A/B)** — independent of FF-1A-C + Wave 2; NYISO data+marker ready. Opt A immediate; Opt B needs 1 NYSRC manual DL. |
| FF-4A | OPUS | 4 | L-VAL | ⛔ owner-gated | not-sent | blocked: FF-3A + owner |
| FF-4B | FABLE | 4 | L-VAL | — | not-sent | blocked: FF-4A |
| FF-4C | OPUS | 4 | L-VAL | owner-gated | not-sent | blocked: FF-4A + owner |
| FF-5A | OPUS | 5 | L-DASH | — | not-sent | blocked: Wave 4 |

Out-of-program / trivial: #2438 (restore), #2441 (FF-1A doc fill), #2442/#2444 (caiso-94),
#2445/#2449 (caiso-95), #2447 (miso-72), #2450 (ercot commitment-posture lever),
#2437/#2443/#2446 (this ledger). One OPEN PR pending owner action — see below.

---

## Open PRs pending owner action

- **PR #2439 — CLOSE (still open, do NOT merge).** Redundant duplicate of #2438; now
  `dirty`/conflicting against current main (51 files, +81,978/−1,531 — carries far more
  than a restore). #2438 already landed the restore + R-NEW. The dirty state blocks
  self-merge (good). Owner: close it.

---

## Owner decisions

**Received:**
- **D1 = B (R-NEW), by action** (2026-07-18): D1=B, D2=delete, D3=gas_cc-lag=1. Implemented,
  restored, and now measured (inversion closed, 3 legs scored). Owner: correct me if D1≠B.

**AWAITING (each changes what I dispatch next):**
- **FF-3D NYISO R5a pick** (Option A lagged model-derived vs Option B NYCA-wide static
  proxy). Unlocks FF-3D immediately (parallel to Wave 2). Opt B needs the NYSRC Appendix D
  Table D.1.1 manual download first.
- **PR triage:** close #2439.
- **BAU DC posture** (`datacenter_load_path` `off` vs `mid`; FF-1C rec: mid). Gates FF-4A.
- Availability derate default (FF-1B — evidence in; owner may set ON-for-forecast),
  entry-lookahead posture (FF-2A item 4), per-ISO flips (FF-2C), golden freeze (FF-4A),
  PB-5 (FF-4C).

---

## Corrections issued

1. **FF-0A-fix [OPUS]** (turn 2) — RESOLVED turn 3 (#2419).
2. **FF-0B-redo [OPUS]** (turn 2) — open, in flight.
3. **FF-1A-restore [FABLE]** (turn 5) — **RESOLVED turn 7 (#2438).** capacity.py
   byte-exact restored + R-NEW re-applied + D2 deleted; manager-verified faithful.
4. **FF-1A-C [FABLE]** (turn 7; re-sent turn 9) — **LANDED turn 10 (#2448/#2451), verified-
   issues (doc-sync).** Solve/score/register done; summary doc not synced → FF-1A-C2.
5. **FF-1A-C2 [OPUS]** (turn 10) — doc-only sync of the findings scorecard from the committed
   score.jsons + reports (zero PENDING; no solve). Open.

---

## Turn log

- **turn 1.** HEAD `f0da036`. Dispatched Wave 0.
- **turn 2.** `→6d6867b`. FF-0D pass; FF-0A/FF-0B issues → FF-0A-fix + FF-0B-redo. Released FF-1B+FF-1C.
- **turn 3.** `→fa6959e`. FF-0A-fix + FF-0C pass. FF-1A owner-gated on D1; box surfaced.
- **turn 4.** `→2144e12`. FF-1C pass. Released FF-1E. Staged FF-1A (keyed B). Surfaced DC posture.
- **turn 5 (refresh).** `→398c1f2`. FF-1B verified-pass. FF-1A verified-issues CRITICAL:
  R-NEW landed but truncated capacity.py (-39%, main broken) — issued FF-1A-restore.
- **turn 6 (refresh).** `→f637994`. Main STILL broken; FF-1A-restore not started. Re-flagged.
- **turn 7 (refresh).** `→7d4b738`. **MAIN RESTORED** (#2438). FF-1A-restore verified-pass;
  FF-1A verified-issues (scorecard partial) → issued FF-1A-C. FF-2A HELD.
- **turn 8 (refresh — "is calibration py fixed").** `→4bfb618`. Confirmed capacity.py FIXED
  (byte-identical to #2438). #2441 = FF-1A doc fill (docs-only). #2440 on main ⇒ FF-1A-C
  prelude satisfied. #2439 dirty → close.
- **turn 9 (refresh — "send next wave"/"anything unlocked").** `→ab69df3`. No new FF; #2442
  caiso-94 out-of-program. Re-sent FF-1A-C. Established Wave 2 substantively gated (gap-
  register §3.9 BLK-10-re-measure-before-sizing). Surfaced FF-3D (owner R5a) + scoped-FF-2A
  options.
- **turn 10 (refresh + dispatch — owner: "refresh and send prompts").** `→ae754e2`. **FF-1A-C
  LANDED** (#2448/#2451): 3 R-NEW legs solved/scored/registered at HEAD with real
  T-R10/LOYO/BLK-10; PJM blk10 fired 2.5 GW (still over-fires → FF-2A sizing warranted),
  T-R10 PASS, LOYO 2/3; capacity.py untouched; rule-27 score_capacity_hindcast.py clip
  self-caught+restored. Verified-issues: summary findings doc not synced (9 PENDING) → issued
  **FF-1A-C2 [OPUS]** (doc-only). Engineering gate met ⇒ **RELEASED FF-2A [FABLE]** (Wave 2
  opens; BLK-10 baseline from committed bundles; owns capacity.py; rebase onto FF-1E if it
  lands). Out-of-program: #2444/#2445/#2447/#2449/#2450. Still awaiting owner: FF-3D R5a pick
  (parallel unlock), scoped-FF-2A-vs-hold now moot (full FF-2A released), close #2439, DC
  posture. FF-2B unblocks when FF-2A merges; FF-2C stays owner-gated (flip-gate scorecard
  from FF-1A-C2).
