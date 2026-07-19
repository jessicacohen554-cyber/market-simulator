# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `7544814` (2026-07-19, turn 26 — manager session `turn-24-phaekh`).
- **Plan base SHA:** `c95176e`.
- **turn 26 (manager `turn-24-phaekh`, refresh). `567ef3c→7544814` (8 merges). QUIET — nothing FF
  landed, nothing unlocked, no corrections.** My turn-25 ledger reached main (#2549). All 8 merges
  out-of-program: #2545 (caiso-charge-economics probes, 2 scripts), #2547 (caiso-100 cycling-cost +
  caiso-101 chp-steam backcast keepers — touches scenarios.py +53 with new **gated/cited** CHP-steam
  fields `p25_allhr_cf` etc, WP-3 rule-23 re-derivation, measured/on-registry, backcast train years —
  governance-clean), #2548 (ercot-86-rt-wall-2025 — ERCOT trough/spread lane, adds 66MB 2025 tail-days
  parquet + condbinned wall json + run bundles, train year), #2550 (miso-77-lane-selection, docs-only:
  calibration-log + M4 AFC-feasibility handoff), #2551 (**phase-refactor/root-cleanup** — deletes
  stray root zips/logs/probe-test file, moves docs, renames egrid file; only 2–4-line path updates in
  egrid.py/ownership.py/zone_assignment.py — no truncation), #2552 (**phase-refactor/retention-sweep**
  — 1982 files, **413,645 deletions**: prunes old calibration bundles run98*/run99* + updates
  dashboard_add_run.py/regen_dashboard.py/check_registry_payload_parity.py; **no src/ deletions, no FF
  frontend/backcast artifacts touched** — verified clean), #2553 (dead-inputs-paths-audit — 18 scripts,
  small path-guard additions, scripts-only), #2554 (caiso-inelastic-evening-merit — 3 probe scripts).
  Phase-refactor (#2551/#2552) + audit (#2553) are the codebase-refactor initiative (#2533 plan) in
  execution — separate from FF; the 413k-deletion retention sweep is large but clean — flag to owner
  for awareness. **Rule-27 clean:** capacity.py 4241 (=), scenarios.py 7930 (+7 vs 7923), constants.py
  7434 (=), runner.py 2469 (=) — no shrink. **Active front UNCHANGED: FF-2B ONLY** (still sent,
  awaiting worker launch — no branch on origin). No FF-2B/2C/2D branch appeared. Nothing to correct
  or unblock; FF-2C stays owner-gated pending FF-2B.
- **turn 25 (manager `turn-24-3lfbsn`, refresh). `48ae665→567ef3c` (12 merges). TWO FF LANES
  LANDED verified-pass; the 3-non-delivery saga on the posture flip is CLOSED.** FF-2A-posture-redo
  (#2539) = verified-pass: scenarios.py:1248 `entry_lookahead_reprice` default False→True +
  `__post_init__` backcast coercion + plan §2.1a **row e** + measured-cache-key byte-identity
  attestation (ERCOT backcast key `c44c3d9b7549de73` unchanged; forecast key shifts as intended) —
  4th attempt on this lineage finally landed the source change. FF-1E-policy (#2535 doc + #2540
  constants.py) = verified-pass, item 2 COMPLETE: IRA/OBBBA verified CURRENT (no-change = correct
  disposition); NEISO ACP `65.0→50.0` the sole runtime delta, cited verbatim (225 CMR 14.08); PJM
  load weights → primary Monitoring Analytics 2024; confirmed-retire re-query → no binding instrument.
  Backcast byte-identical by construction. Rule-27 clean. Out-of-program (8): miso-76, caiso-belly-charge,
  ercot-86-rt-wall, miso-zonal-loss-surface, #2533 codebase-refactor plan.
- **turn 24 (manager `turn-24-3lfbsn`). `270f429→48ae665` (3 merges). QUIET.** t23 ledger on main
  (#2530). #2531 (miso-zonal-loss-surface data-intake, data-only), #2532 (caiso-99 storage-shape
  keeper). Rule-27 clean.
- **turn 23 (manager `yjegie`). `37d3923→270f429` (5 merges). QUIET.** t22 ledger on main (#2525).
  #2526/#2529 (miso-76), #2527 (ercot design memo), #2528 (peer-review doc). Manager-handoff prompt
  emitted at owner request.
- **turn 22 (`→37d3923`).** FF-1E COMPLETION #2518 verified-pass (items 1/3/4). FF-1E-complete
  RETRACTED; genuine non-deliveries corrected 4→3. Only item 2 remained → slim FF-1E-policy [OPUS].
- **turn 21 (`→a57194d`, 7 merges).** FF-0B-redo (#2517) + FF-1D (#2519) verified-pass.
  FF-2A-posture (#2522) 3rd genuine NON-DELIVERY → FF-2A-posture-redo + escalated push-integrity
  pattern to owner.
- **turns 10–20 (collapsed).** t20: FF-1E #2515 read as non-delivery → FF-1E-complete (later
  RETRACTED t22). t19: FF-0E verified-pass (#2514) → FF-1D released. t18: FF-2A measurement landed
  (#2506/#2509); FF-0E launched; posture=ON approved; golden freeze HELD. t17: #2503 stale-patch
  delete + #2505 FF-0F close. t15: FF-2A integration MERGED (#2486); FF-1F defaults live (#2493).
  t14: capacity.py re-truncated (#2474/#2477) → owner-RESTORED (#2481). t13: FF-3D landed (#2463)
  → FF-3D-run. t12: owner decisions (flips all-but-ERCOT, R5a=B, DC=mid, derate=ON). t11: FF-2A
  integrity breach (#2453) → FF-2A-integrate; FF-1A-C2 verified-pass. t10: FF-1A-C landed. t7: main
  restored (#2438).

Status vocabulary: `not-sent` · `sent` · `landed` · `verified-pass` ·
`verified-issues` · `correction-sent`.

---

## Session status table

| FF id | Model | Wave | Lane | Gate | Status | Evidence |
|---|---|---|---|---|---|---|
| FF-0A | FABLE | 0 | L-VAL | ⛔ rubric | **verified-pass** | rubric #2414 + scorer #2419 |
| FF-0A-fix | OPUS | 0 | L-VAL | — | **verified-pass** | #2419: 73 tests pass |
| FF-0B-redo | OPUS | 0 | L-VAL | — | **verified-pass (turn 21)** — #2517 | 6-ISO T1-F baseline 2026-2030: findings doc + 6 real ISO sidecars + register_forecast_baseline.py. #2412 non-delivery FIXED. BEFORE legs for Wave-1/2. |
| FF-0C | FABLE | 0 | L-CAP | — | **verified-pass** | #2418: R-NEW memo + owner box |
| FF-0D | OPUS | 0 | L-INP | — | **verified-pass** | #2413: audit, no source changes |
| FF-0E | OPUS | 0 | L-VAL | — | **verified-pass (turn 19)** — #2514 | Crossover harness + score_crossover.py + 2 tests. ≥2026 reads structurally refused (rule 22), no default changed. |
| FF-0F | OPUS | 0 | L-VAL/L-INP | — | **verified-pass, CLOSED (turn 17)** | #2488 + #2490 + #2505: benchmark-corridor datatype + loader + 13 tests + FC-5 context-only wiring; additive. |
| FF-1A | FABLE | 1 | L-CAP | — | **verified-pass (complete)** | #2438 + #2448/#2451 + #2454. Inversion CLOSED; flip-gate scorecard complete. |
| FF-1A-restore | FABLE | 1 | L-CAP | — | **verified-pass** | #2438: capacity.py byte-exact restore. |
| FF-1A-C | FABLE | 1 | L-CAP | — | **verified-pass (via FF-1A-C2)** | #2448/#2451: 3 R-NEW legs scored. |
| FF-1A-C2 | OPUS | 1 | L-CAP | — | **verified-pass** — #2454 | doc synced, 0 PENDING. FF-1A complete. |
| FF-1B | FABLE | 1 | L-SCAR | — | **verified-pass** | #2423: correlated cold-event derate. |
| FF-1C | OPUS | 1 | L-INP | — | **verified-pass** | #2422: demand/DC currency + hydro. |
| FF-1D | OPUS | 1 | L-VAL | — | **verified-pass (turn 21)** — #2519 | Crossover ERCOT+PJM 2023→2027: input-gap doc + 2 crossover sidecars + 2 run reports. Quarantine holds BY CONSTRUCTION; leakage clean. |
| FF-1E | OPUS | 1 | L-INP | — | **verified-pass, items 1/3/4 (turn 22)** — #2515+#2518 | Two-PR lane: constants.py ATB-derived (cited) + `test_atb_entry_cost_consistency.py` + per-tech WACC option (default-off) + findings. entry_lookahead_reprice untouched; rule-27 clean. |
| FF-1E-complete | OPUS | 1 | L-INP | — | **RETRACTED (turn 22)** | Superseded by #2518. Replaced by slim item-2-only FF-1E-policy. |
| FF-1E-policy | OPUS | 1 | L-INP | — | **verified-pass, item 2 COMPLETE (turn 25)** — #2535+#2540 | IRA CURRENT (no-change = correct); NEISO ACP 65→50 sole runtime delta, cited (225 CMR 14.08); PJM weights refreshed; confirmed-retire no-add. Backcast byte-identical by construction. Closes FF-0D §7.2 P2. |
| FF-1F | OPUS | 1 | L-INP | — | **landed + defaults LIVE** (#2468/#2476/#2480 + #2493) | DC=mid, derate=ON with backcast byte-identity guards; plan §2.1 recorded. Closed. |
| FF-2A | FABLE | 2 | L-CAP | — | **COMPLETE (turn 18) — mechanism + measurement both landed** | Mechanism #2486 (t15); measurement #2506/#2509 (t18). VRE cap-rev near-pivotal → G-20/G-22. Full manager-verify pending (deferred). |
| FF-2A-integrate | FABLE | 2 | L-CAP | — | **verified-pass (turn 15, via #2486 + #2491/#2492)** | 0 fn loss, on-registry, compiles. Lane CLOSED. |
| FF-2A-posture | OPUS | 2 | L-CAP | — | **verified-issues, NON-DELIVERY (turn 21)** — #2522 | Doc-only; scenarios.py UNCHANGED. 3rd genuine non-delivery. → FF-2A-posture-redo. |
| FF-2A-posture-redo | OPUS | 2 | L-CAP | — | **verified-pass (turn 25)** — #2539 | Landed the flip #2522 only described: scenarios.py `entry_lookahead_reprice` False→True + backcast coercion + plan §2.1a row e + measured-cache-key byte-identity attestation. Closes the 3-non-delivery saga. |
| FF-2B | OPUS | 2 | L-CAP | — | **sent (turn 17), awaiting worker launch — no branch on origin (t26)** | Prereq FF-2A met, drift-clean. On the FF-2C critical path + produces the first NEISO cap-hindcast pair (NEISO evidence-free). CAISO/NEISO/NYISO I7 + NEISO Net ICR + first NEISO pair; bands pre-registered BEFORE the run. |
| FF-2C | OPUS | 2 | L-CAP | — | **issued (turn 14), owner-gated** | owner-approved flip all-but-ERCOT, staged by readiness. After FF-2A(done) + FF-2B. Needs per-ISO sign-off. Rule 1: worsened fit = root-cause. |
| FF-2D | OPUS | 2 | L-VAL | ⛔ T1 gate | **issued (turn 14), gated** | runs after W1/W2 merges. Rubric verdicts + promotion table. |
| FF-3A | OPUS | 3 | L-VAL | ⛔ T2 | not-sent | blocked: FF-2D + owner |
| FF-3B | OPUS | 3 | L-CES | — | **issued (turn 14), gated** | W3-R readiness → GO/NO-GO → W4. R1 = FF-2A headline (solar recall). |
| FF-3C | FABLE | 3 | L-PERF | conditional | not-sent | trigger-gated — inactive (only remaining FABLE prompt) |
| FF-3D | OPUS | 3 | L-CAP | — | **verified-issues (incomplete)** — LANDED #2463 | Intake + Option-B pairing + pre-registered bands; flip-gate Basis PASSES. Pair run via FF-3D-run. |
| FF-3D-run | OPUS | 3 | L-CAP | — | **landed** (#2471/#2473/#2478 + `5bb0c9b`) | NYISO fixed/curve/realized pair registered. Closed. |
| FF-4A | OPUS | 4 | L-VAL | ⛔ owner-gated | **HELD by owner (turn 18)** | Golden freeze holds until backcast is calibrated on the testing (validation/locked) years. Do not dispatch. |
| FF-4B | FABLE | 4 | L-VAL | — | not-sent | blocked: FF-4A |
| FF-4C | OPUS | 4 | L-VAL | owner-gated | not-sent | blocked: FF-4A + owner (PB-5) |
| FF-5A | OPUS | 5 | L-DASH | — | not-sent | blocked: Wave 4 |

Out-of-program / trivial (turn 26): #2545 (caiso-charge-economics probes), #2547 (caiso-100/101
backcast keepers — gated/cited scenarios.py CHP-steam fields, train years), #2548 (ercot-86-rt-wall-2025
— ERCOT trough/spread lane + 66MB 2025 tail-days parquet), #2550 (miso-77-lane-selection docs),
#2551 (phase-refactor/root-cleanup), #2552 (phase-refactor/retention-sweep — 413k deletions, no src/,
no FF artifacts), #2553 (dead-inputs-paths-audit scripts), #2554 (caiso-inelastic-evening-merit probes),
#2549 (ledger t25). Earlier: #2536 (ledger t24), #2544/#2542 (miso-76), #2543/#2537
(caiso-belly-charge), #2541/#2534 (ercot-86-rt-wall), #2538 (miso-zonal-loss-surface runner.py kwarg
gated/UNSET-off), #2533 (codebase-refactor-consolidation plan — separate initiative), #2530 (ledger
t23), #2531 (miso-zonal-loss-surface data-intake), #2532 (caiso-99 keeper), #2525 (ledger t22),
#2526/#2529 (miso-76), #2527 (ercot design memo), #2528 (peer-review doc), and earlier caiso/miso/ercot
backcast keepers + ledger commits.

---

## Owner decisions

**Received:**
- **D1 = B (R-NEW), by action** (2026-07-18). Done.
- **Capacity-market flips (turn 12):** ON for all ISOs with a real capacity market =
  PJM/MISO/NYISO/NEISO/CAISO (all but ERCOT). FF-2C executes per-ISO by readiness.
  CAISO = RA-not-auction. Rule 1 governs (worsened fit → root-cause, not revert).
- **NYISO R5a = Option B** (turn 12). FF-3D landed the intake.
- **datacenter_load_path default = mid** (turn 12). FF-1F applies.
- **correlated_forced_outage default = ON** (turn 12). FF-1F applies.
- **Entry-lookahead posture = ON** (turn 18, 2026-07-18). FF-2A-posture-redo LANDED it (turn 25, #2539).
- **Golden freeze HOLDS** (turn 18) — until backcast is calibrated on the testing years.
  FF-4A stays gated.
- **#2439** — owner handled → resolved.

**AWAITING (each changes what I dispatch next):**
- PB-5 (FF-4C, owner-gated, later wave). Golden freeze (FF-4A) is owner-confirmed HELD.
- Per-ISO FF-2C sign-off (after FF-2B lands verified-pass).

---

## Corrections issued

1. **FF-0A-fix [OPUS]** (turn 2) — RESOLVED turn 3 (#2419).
2. **FF-0B-redo [OPUS]** (turn 2) — re-issued turn 14/17. **LANDED verified-pass turn 21 (#2517).**
3. **FF-1A-restore [FABLE]** (turn 5) — **RESOLVED turn 7 (#2438).**
4. **FF-1A-C [FABLE]** (turn 7) — **LANDED turn 10 (#2448/#2451).** Doc-sync gap → FF-1A-C2.
5. **FF-1A-C2 [OPUS]** (turn 10) — **RESOLVED turn 11 (#2454), verified-pass.**
6. **FF-2A-integrate [FABLE]** (turn 11) — breach fix. Re-truncated (#2474/#2477) → owner-reverted
   (#2481). Superseded by round-3 — **RESOLVED turn 15** (#2486 + #2491/#2492).
7. **FF-3D-run [OPUS]** (turn 13) — **LANDED** (#2471/#2473/#2478 + `5bb0c9b`).
8. **runner.py orphan revert** (turn 14) — **RETRACTED turn 15.** #2486 forward-fixed it.
9. **FF-1E-complete [OPUS]** (turn 20) — **RETRACTED turn 22.** #2518 completed FF-1E items 1/3/4.
   Genuine non-deliveries = 3. Replaced by slim FF-1E-policy [OPUS].
10. **FF-2A-posture-redo [OPUS]** (turn 21) — non-delivery fix. **RESOLVED turn 25 (#2539),
    verified-pass.** Genuine non-deliveries stay 3 (FF-0B #2412, FF-2A #2453, FF-2A-posture #2522).
11. **FF-1E-policy [OPUS]** (turn 22) — slim item-2-only follow-up. **RESOLVED turn 25
    (#2535+#2540), verified-pass** — NEISO ACP 65→50 the sole cited runtime delta.

---

## Turn log

- **turns 1–16.** Wave 0/1 dispatch + verify; capacity.py truncation saga (t6/t11/t14) restored;
  FF-2A integration (t15); FF-0F closed (t17). See prior ledger commits for detail.
- **turn 17 (`→9b9b0d4`).** #2503 stale-patch delete + #2505 FF-0F close. Re-emitted 4 [OPUS].
- **turn 18 (`→e5d6f29`).** FF-2A completion landed. FF-0E launched. Posture=ON approved; golden
  freeze HELD.
- **turn 19 (`→37b9136`).** FF-0E verified-pass → FF-1D released.
- **turn 20 (`→cf1531d`).** FF-1E #2515 read as non-delivery → FF-1E-complete (later retracted t22).
- **turn 21 (`→a57194d`).** FF-0B-redo (#2517) + FF-1D (#2519) verified-pass. FF-2A-posture (#2522)
  NON-DELIVERY → FF-2A-posture-redo + escalated push-integrity pattern to owner.
- **turn 22 (`→37d3923`).** FF-1E COMPLETION #2518 verified-pass. FF-1E-complete RETRACTED;
  non-deliveries 4→3. → slim FF-1E-policy [OPUS].
- **turn 23 (`→270f429`).** QUIET. t22 ledger on main (#2525). Manager-handoff prompt emitted.
- **turn 24 (`→48ae665`).** QUIET. t23 ledger on main (#2530). #2531/#2532 out-of-program.
- **turn 25 (`→567ef3c`).** TWO FF LANES verified-pass: FF-2A-posture-redo (#2539) — posture flip
  finally landed, 3-non-delivery saga CLOSED; FF-1E-policy (#2535+#2540) — item 2 complete. Rule-27
  clean. 8 out-of-program.
- **turn 26 (`→7544814`).** QUIET refresh — nothing FF landed, nothing unlocked, no corrections.
  t25 ledger on main (#2549). 8 out-of-program merges: caiso-100/101 keepers (#2547, gated/cited
  scenarios.py), ercot-86-rt-wall-2025 (#2548), miso-77 docs (#2550), phase-refactor root-cleanup +
  retention-sweep (#2551/#2552 — 413k deletions, no src/, no FF artifacts), dead-inputs audit (#2553),
  caiso probes (#2545/#2554). Rule-27 clean (capacity.py 4241, scenarios.py 7930, constants.py 7434,
  runner.py 2469 — no shrink). Active front FF-2B only, awaiting worker launch. FF-2C stays
  owner-gated pending FF-2B.
