# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `48ae665` (2026-07-19, turn 24 — manager session `turn-24-3lfbsn`).
- **Plan base SHA:** `c95176e`.
- **turn 24 (manager `turn-24-3lfbsn`, refresh). `270f429→48ae665` (3 merges). QUIET — nothing FF
  landed, nothing unlocked.** My turn-23 ledger reached main (#2530). Other 2 merges out-of-program:
  #2531 (miso-zonal-loss-surface — data-intake: lmp-components schema + curate/fetch scripts +
  curation test; DATA-ONLY, no LP solve, governance-clean) and #2532 (caiso-99 storage-shape
  backcast keeper — bundle + dashboard registration). Rule-27 clean (all core files unchanged:
  capacity.py 4241, scenarios.py 7834, constants.py 7413, runner.py 2457). Active front UNCHANGED:
  **FF-2B + FF-2A-posture-redo + FF-1E-policy** (all sent, parallel-safe, awaiting worker launch —
  still NO branches on origin). Nothing to correct. No owner ask for prompt waves this turn. Watch
  next: the 3 active corrections/lanes land → verify; FF-2A completion full-verify still deferred.
- **turn 23 (manager `yjegie`, refresh + handoff). `37d3923→270f429` (5 merges). QUIET.** My t22
  ledger reached main (#2525). All 5 merges docs-only/out-of-program: #2526/#2529 (miso-76 keeper),
  #2527 (ercot price-formation design memo), #2528 (third-party peer-review doc, informational).
  Rule-27 clean. Active front unchanged. Owner requested a manager-handoff prompt (emitted).
- **turn 22 (manager `yjegie`, refresh). `a57194d→37d3923` (2 merges). FF-1E COMPLETION landed
  verified-pass (#2518) → my "FF-1E non-delivery" call CORRECTED; FF-1E-complete RETRACTED.**
  #2518 was the FF-1E worker's OWN second PR on the same branch (`entry-costs-atb-source`) — NOT a
  response to my correction. Completes FF-1E items 1/3/4: constants.py NEW_ENTRY_COSTS/
  TECH_COST_MULTIPLIERS now ATB-2024-v3.0.0-DERIVED + `test_atb_entry_cost_consistency.py` (rule 23);
  per-tech WACC OPTION `per_tech_wacc_enabled=False` (byte-identical default); findings doc. Rule-27
  clean (capacity.py 4230→4241, scenarios.py 7794→7834, constants.py 7281→7413 — all GREW
  additively). `entry_lookahead_reprice` correctly untouched. **ONLY item 2 (policy fixes) missing**
  → slim **FF-1E-policy [OPUS]** issued. **RECORD CORRECTION: genuine non-deliveries = 3 (FF-0B
  #2412, FF-2A #2453, FF-2A-posture #2522), NOT 4** — FF-1E #2515 was the first half of a two-PR
  lane; over-called at turn 20.
- **⚠️ turn 21 (`→a57194d`, 7 merges). 2 verified-pass + 3rd genuine NON-DELIVERY (FF-2A-posture)
  → escalated.** FF-0B-redo (#2517) verified-pass: 6-ISO T1-F baseline 2026-2030 (#2412 non-delivery
  FIXED). FF-1D (#2519) verified-pass: crossover ERCOT+PJM 2023→2027, quarantine holds by
  construction. FF-2A-posture (#2522) NON-DELIVERY: findings doc only, describes the scenarios.py
  flip AS IF APPLIED but scenarios.py UNCHANGED → FF-2A-posture-redo + escalated push-integrity
  pattern to owner.
- **turns 10–20 (collapsed).** t20 (`→cf1531d`): FF-1E #2515 read as non-delivery → FF-1E-complete
  (later RETRACTED t22). t19 (`→37b9136`): FF-0E verified-pass (#2514) → FF-1D released. t18
  (`→e5d6f29`): FF-2A measurement landed (#2506/#2509); FF-0E launched; posture=ON approved; golden
  freeze HELD. t17 (`→9b9b0d4`): #2503 stale-patch delete + #2505 FF-0F close; re-emitted 4 [OPUS].
  t15 (`mhtoa0`): FF-2A integration MERGED (#2486); FF-1F defaults live (#2493). t14 (`eulpj6`):
  capacity.py re-truncated (#2474/#2477) → owner-RESTORED (#2481). t13 (`→68e38db`): FF-3D landed
  (#2463) → FF-3D-run. t12: owner decisions (flips all-but-ERCOT, R5a=B, DC=mid, derate=ON). t11:
  FF-2A integrity breach (#2453) → FF-2A-integrate; FF-1A-C2 verified-pass. t10: FF-1A-C landed. t7:
  main restored (#2438).

Status vocabulary: `not-sent` · `sent` · `landed` · `verified-pass` ·
`verified-issues` · `correction-sent`.

---

## Session status table

| FF id | Model | Wave | Lane | Gate | Status | Evidence |
|---|---|---|---|---|---|---|
| FF-0A | FABLE | 0 | L-VAL | ⛔ rubric | **verified-pass** | rubric #2414 + scorer #2419 |
| FF-0A-fix | OPUS | 0 | L-VAL | — | **verified-pass** | #2419: 73 tests pass |
| FF-0B-redo | OPUS | 0 | L-VAL | — | **verified-pass (turn 21)** — #2517 | 6-ISO T1-F baseline 2026-2030: findings doc (invariant matrix + triage) + 6 real ISO sidecars + register_forecast_baseline.py. Findings-only; #2412 non-delivery FIXED. The BEFORE legs for Wave-1/2. Baselined at posture=False + old entry costs (flips land later as measured deltas). |
| FF-0C | FABLE | 0 | L-CAP | — | **verified-pass** | #2418: R-NEW memo + owner box |
| FF-0D | OPUS | 0 | L-INP | — | **verified-pass** | #2413: audit, no source changes |
| FF-0E | OPUS | 0 | L-VAL | — | **verified-pass (turn 19)** — #2514 | Crossover harness + score_crossover.py + 2 tests. New scenarios.py fields cache-neutral, fuel/runner crossover-gated, 21 passthroughs preserved, ≥2026 reads structurally refused (rule 22), vintage-2023 leakage test, no default changed. |
| FF-0F | OPUS | 0 | L-VAL/L-INP | — | **verified-pass, CLOSED (turn 17)** | #2488 + #2490 + #2505: benchmark-corridor datatype + loader + 13 tests + FC-5 context-only wiring; 73 scorer tests pass; additive. |
| FF-1A | FABLE | 1 | L-CAP | — | **verified-pass (complete)** | #2438 + #2448/#2451 + #2454. Inversion CLOSED; flip-gate scorecard complete. |
| FF-1A-restore | FABLE | 1 | L-CAP | — | **verified-pass** | #2438: capacity.py byte-exact restore. |
| FF-1A-C | FABLE | 1 | L-CAP | — | **verified-pass (via FF-1A-C2)** | #2448/#2451: 3 R-NEW legs scored. |
| FF-1A-C2 | OPUS | 1 | L-CAP | — | **verified-pass** — #2454 | doc synced, 0 PENDING. FF-1A complete. |
| FF-1B | FABLE | 1 | L-SCAR | — | **verified-pass** | #2423: correlated cold-event derate. |
| FF-1C | OPUS | 1 | L-INP | — | **verified-pass** | #2422: demand/DC currency + hydro. |
| FF-1D | OPUS | 1 | L-VAL | — | **verified-pass (turn 21)** — #2519 | Crossover ERCOT+PJM 2023→2027: input-gap doc + 2 crossover sidecars + 2 run reports. Governance exemplary — quarantine holds BY CONSTRUCTION (scorer raises on ≥2026 reads), leakage clean, no bridge year. |
| FF-1E | OPUS | 1 | L-INP | — | **verified-pass, items 1/3/4 (turn 22)** — #2515+#2518 | Two-PR lane: #2515 the derive script, #2518 the completion — constants.py ATB-derived (cited) + `test_atb_entry_cost_consistency.py` + per-tech WACC option (default-off, byte-identical) + findings. entry_lookahead_reprice untouched; rule-27 clean. **Item 2 (policy fixes) remains → FF-1E-policy.** |
| FF-1E-complete | OPUS | 1 | L-INP | — | **RETRACTED (turn 22)** | Superseded by #2518 (items 1/3/4 done). Replaced by the slim item-2-only **FF-1E-policy**. |
| FF-1E-policy | OPUS | 1 | L-INP | — | **sent (turn 22, slim)** | Item 2 only: FF-0D §4 IRA field/window fixes (policy/ira.py), STATE_RPS_TARGETS/ACP refresh, confirmed-retirement additions — all cited (rule 23). Lower urgency (blocks nothing; needed before FF-2D/golden freeze). Parallel-safe; blob-verify if constants.py touched. |
| FF-1F | OPUS | 1 | L-INP | — | **landed + defaults LIVE** (#2468/#2476/#2480 + #2493) | DC=mid, derate=ON with backcast byte-identity guards; plan §2.1 recorded. Closed. |
| FF-2A | FABLE | 2 | L-CAP | — | **COMPLETE (turn 18) — mechanism + measurement both landed** | Mechanism #2486 (t15); measurement #2506/#2509 (t18): findings doc + ERCOT/MISO/PJM `*-ff2a-r2` legs. VRE cap-rev near-pivotal, BLK-10 2.5→1.103 GW, PJM solar +84%→+48%, ERCOT solar zero → G-20/G-22. Full manager-verify pending. |
| FF-2A-integrate | FABLE | 2 | L-CAP | — | **verified-pass (turn 15, via #2486 + #2491/#2492)** | 0 fn loss, signature matches runner, fields on-registry, 14 harness refs, compiles. Sidecars governance-clean. Lane CLOSED. |
| FF-2A-posture | OPUS | 2 | L-CAP | — | **verified-issues, NON-DELIVERY (turn 21)** — #2522 | Committed ONLY the findings doc, which describes the flip AS IF APPLIED — but scenarios.py UNCHANGED (still False), plan not updated. Flip did not land. 3rd genuine non-delivery. → **FF-2A-posture-redo**. |
| FF-2A-posture-redo | OPUS | 2 | L-CAP | — | **sent (turn 21, correction)** | Land the EXACT change the #2522 dead doc specifies: scenarios.py entry_lookahead_reprice default False→True + `__post_init__` backcast coercion + plan §2.1a row e. BLOB-VERIFY scenarios.py contains it before touching the doc (push-integrity is the point). Parallel-safe (scenarios.py — disjoint from FF-2B/FF-1E-policy). |
| FF-2B | OPUS | 2 | L-CAP | — | **sent (turn 17) — in the parallel batch; not yet pushed** | Prereq FF-2A met, drift-clean. On the FF-2C critical path + produces the first NEISO cap-hindcast pair (NEISO evidence-free). CAISO/NEISO/NYISO I7 + NEISO Net ICR + first NEISO pair; bands pre-registered BEFORE the run. |
| FF-2C | OPUS | 2 | L-CAP | — | **issued (turn 14), owner-gated** | owner-approved flip all-but-ERCOT, staged by readiness. After FF-2A(done) + FF-2B. Rule 1: worsened fit = root-cause. |
| FF-2D | OPUS | 2 | L-VAL | ⛔ T1 gate | **issued (turn 14), gated** | runs after W1/W2 merges. Rubric verdicts + promotion table. |
| FF-3A | OPUS | 3 | L-VAL | ⛔ T2 | not-sent | blocked: FF-2D + owner |
| FF-3B | OPUS | 3 | L-CES | — | **issued (turn 14), gated** | W3-R readiness → GO/NO-GO → W4. R1 = FF-2A headline (solar recall). |
| FF-3C | FABLE | 3 | L-PERF | conditional | not-sent | trigger-gated — inactive (only remaining FABLE prompt) |
| FF-3D | OPUS | 3 | L-CAP | — | **verified-issues (incomplete)** — LANDED #2463 | Intake + Option-B pairing + pre-registered bands + curve-eligibility clean; flip-gate Basis PASSES. Also fixed the FF-2A-broken cap-hindcast harness. Pair run via FF-3D-run. |
| FF-3D-run | OPUS | 3 | L-CAP | — | **landed** (#2471/#2473/#2478 + `5bb0c9b`) | NYISO fixed/curve/realized pair registered. Closed. |
| FF-4A | OPUS | 4 | L-VAL | ⛔ owner-gated | **HELD by owner (turn 18)** | Golden freeze holds until backcast is calibrated on the testing (validation/locked) years. Do not dispatch. |
| FF-4B | FABLE | 4 | L-VAL | — | not-sent | blocked: FF-4A |
| FF-4C | OPUS | 4 | L-VAL | owner-gated | not-sent | blocked: FF-4A + owner |
| FF-5A | OPUS | 5 | L-DASH | — | not-sent | blocked: Wave 4 |

Out-of-program / trivial: #2530 (ledger t23), #2531 (miso-zonal-loss-surface data-intake, data-only),
#2532 (caiso-99 storage-shape backcast keeper), #2525 (ledger t22), #2526/#2529 (miso-76 backcast),
#2527 (ercot price-formation design memo), #2528 (third-party peer-review doc),
#2524 (miso-75 keeper promote), #2523 (ercot-lmp-scarcity backcast), #2520 (miso-75 Manitoba),
#2516/#2521 (ledger t19/t20 — reached main), #2512 (ercot-lmp-scarcity backcast calibration
+ ercot66-77 prune), #2513 (ledger t18), #2508 (miso-74),
#2511 (miso-75 Manitoba merit cap) MISO backcast,
#2507/#2510 (ledger t17), #2501 (ercot-84 offer-surface re-adjudication + probes),
#2504 (caiso-99 attestation), #2483/#2487 (caiso-98 probe/charter), #2484/#2495 (miso-74 seam +
attestation), #2489 (ercot83 posture backcast), #2494 (ercot apr/may scarcity tooling),
#2485 (ledger t14), #2502 (ledger t16), #2503 (delete stale ff2a-core.patch),
#2438 (restore), #2441 (FF-1A doc fill), and earlier caiso/miso/ercot backcast keepers +
ledger commits. #2439 handled.

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
- **Entry-lookahead posture = ON** (turn 18, 2026-07-18) — owner approved `entry_lookahead_reprice`
  default-ON. #2522 was a non-delivery (findings doc only) → **FF-2A-posture-redo** lands it.
- **Golden freeze HOLDS** (turn 18) — until backcast is calibrated on the testing years.
  FF-4A stays gated.
- **#2439** — owner handled → resolved.

**AWAITING (each changes what I dispatch next):**
- PB-5 (FF-4C, owner-gated, later wave). Golden freeze (FF-4A) is owner-confirmed HELD.
- Per-ISO FF-2C sign-off (after FF-2B lands verified-pass).

**RESOLVED (turn 17):** the turn-15 housekeeping ask — chunk branch
`claude/ff2a-entry-stack-integration-6zd9zv` is GONE + stale `ff2a-core.patch` deleted (#2503).

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
9. **FF-1E-complete [OPUS]** (turn 20) — **RETRACTED turn 22.** #2518 completed FF-1E items 1/3/4;
   #2515 was NOT a non-delivery, just the first half of a two-PR lane. Genuine non-deliveries = 3.
   Replaced by slim **FF-1E-policy [OPUS]** (item 2 only).
10. **FF-2A-posture-redo [OPUS]** (turn 21) — non-delivery fix. #2522 committed only a findings
    doc that DESCRIBES the flip as applied; scenarios.py unchanged (still False). Correction lands
    the exact scenarios.py flip + coercion + plan row, blob-verified. **3rd genuine non-delivery
    (FF-0B #2412, FF-2A #2453, FF-2A-posture #2522) — ESCALATED to owner.**
11. **FF-1E-policy [OPUS]** (turn 22) — slim item-2-only follow-up (NOT a non-delivery fix):
    FF-0D §4 IRA/RPS/ACP/confirmed-retirement policy-currency fixes. Lower urgency.

---

## Turn log

- **turns 1–16.** Wave 0/1 dispatch + verify; capacity.py truncation saga (t6/t11/t14) restored;
  FF-2A integration (t15); FF-0F closed (t17). See prior ledger commits for detail.
- **turn 17 (`→9b9b0d4`).** #2503 stale-patch delete + #2505 FF-0F close. Re-emitted 4 [OPUS];
  parallel-safe batch FF-0B-redo + FF-0E + FF-2B.
- **turn 18 (`→e5d6f29`).** FF-2A completion (measurement) landed. FF-0E launched. Posture=ON
  approved → FF-2A-posture dispatched; golden freeze HELD.
- **turn 19 (`→37b9136`).** FF-0E verified-pass → FF-1D released.
- **turn 20 (`→cf1531d`).** FF-1E #2515 read as non-delivery → FF-1E-complete (later retracted t22).
- **turn 21 (`→a57194d`).** FF-0B-redo (#2517) + FF-1D (#2519) verified-pass. FF-2A-posture (#2522)
  NON-DELIVERY → FF-2A-posture-redo + escalated push-integrity pattern to owner.
- **turn 22 (`→37d3923`).** FF-1E COMPLETION #2518 verified-pass (items 1/3/4). FF-1E-complete
  RETRACTED, non-deliveries corrected 4→3. Only item 2 remains → slim FF-1E-policy [OPUS].
- **turn 23 (`→270f429`).** QUIET refresh — nothing FF landed. My t22 ledger on main (#2525).
  Out-of-program: #2526/#2529 (miso-76), #2527 (ercot design memo), #2528 (peer-review doc).
  Emitted a manager-handoff prompt at owner request.
- **turn 24 (`→48ae665`).** QUIET refresh — nothing FF landed, nothing unlocked. My t23 ledger on
  main (#2530). Out-of-program: #2531 (miso-zonal-loss-surface data-intake, data-only/no-solve —
  governance-clean), #2532 (caiso-99 storage-shape backcast keeper). Rule-27 clean (capacity.py
  4241, scenarios.py 7834, constants.py 7413, runner.py 2457). Active front unchanged (FF-2B +
  FF-2A-posture-redo + FF-1E-policy — all sent, parallel-safe, still awaiting worker launch; no
  branches on origin). No owner ask for prompt waves. Nothing to correct.
