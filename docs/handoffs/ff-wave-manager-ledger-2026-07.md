# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `9fa016b` (2026-07-19, turn 29 — manager session `turn-1-anm4jn`).
- **Plan base SHA:** `c95176e` (amended in place 2026-07-19 — POC-first re-scope, see directive entry below).
- **OWNER DIRECTIVE (2026-07-19, out-of-band — recorded by the directive's executing
  session, not a manager turn): POC-first re-scope of THE PLAN.** The plan is amended in
  place (§0 two-phase framing, new §2.1b full-solve authorization gate, §6 Waves 3–4
  re-cut): **FF-4A/FF-4B/FF-4C prompts WITHDRAWN** — Wave 4 deferred in full; the
  turn-18 "golden freeze HELD" hardens into outright prompt withdrawal (never restore
  from history). **FF-3A (T2) deferred with its tier** (prompt withdrawn). **FF-3B
  re-scoped** — W3-R readiness + a T1-scale (ERCOT 2026–2030) CES POC only; the W4
  2026–2050 campaign is deferred, so the issued turn-14 FF-3B prompt is **SUPERSEDED —
  re-emit from the amended plan §6 before any launch**. **FF-3E [OPUS] ⛔ chartered**
  (full-solve readiness battery + POC close-out; absorbs FF-4B's honest-unfit list;
  adds the run_full_horizon.py >5-solve-year guard). Hard cap: **≤5 solve-years per
  invocation, program-wide**. Long solves reopen per ISO only through §2.1b: backcast
  keeper + calibration-complete marker, T1 POC gates green, crossover input gap +
  readiness battery + projected cost, and an explicit per-campaign owner authorization.
  Status-table rows updated below; active front unchanged (FF-2B).
- **turn 29 (manager `turn-1-anm4jn`, refresh). `735e302→9fa016b` (10 merges). QUIET for FF —
  nothing FF landed beyond my t28 ledger (#2595 merged), nothing unlocked, no corrections.
  FF-3B still awaiting worker launch — no branch on origin.** Out-of-program (9): #2596 (NYISO
  fuel-mix curation, curate_generation.py +85), #2597/#2602 (ercot-89 shoulder-online probe +
  measurement + ercot86 hourly parquets), #2598 (phase-refactor reserve-req unify — per-ISO
  modules consolidated into shared `data/reserve_requirements.py`, genuine refactor, net +220),
  #2599/#2600/#2603 (backcast-artifacts refactor — new scripts/lib modules + tests incl.
  `holdout_policy.py`), **#2601 (capacity-cost-grounding-complete — constants.py +280/−103:
  Li-ion storage capex/FOM RE-DERIVED from the committed NREL ATB extract via
  derive_cost_benchmark_envelope.py + asserted by test, replacing hand-set values whose
  ATB/BNEF labels matched no published point; cited, rule-15-clean. FF-RELEVANT: moves storage
  entry economics → FF-2D's regression-vs-FF-0B-baseline must name this causal merge for any
  storage-entry metric shift)**, #2604 (NYISO SCR/EDRP demand-response intake + loader —
  FF-adjacent: a future cited NYISO DR supply credit could narrow its I7 hydro-dominated gap).
  Rule-27 clean: constants.py 7514→7604 (+90 net), capacity.py/scenarios.py/runner.py unchanged.
  Active front: FF-3B (sent, awaiting launch); FF-2C sign-off + FF-2D sequencing still on the
  owner's desk (unchanged from t28).
- **turn 28 (manager `turn-1-anm4jn`, first turn of the successor manager). `30f546e→6b5b6c4`
  (30 merges). FF-2B LANDED VERIFIED-PASS — the active Wave-2 front closes; FF-3B dispatched
  (re-emitted from the amended plan §6); FF-2C/FF-2D sequencing decision surfaced to owner.**
  FF-program merges (8): #2560 (t27 ledger), #2581 (plan POC-first amendment — already recorded in
  the directive entry), #2584 (migration-ledger follow-ups: CES + PB plan docs), and the FF-2B set
  #2582 (NEISO bands pre-registered BEFORE the run ✓ merge order verified), #2586/#2588/#2590
  (patch → APPLY-SPEC → superseded-note: large-file transport fallback, resolved), #2589 (main
  deliverable, 16 files). **FF-2B verified against all 4 prompt items:** (1) CAISO/NEISO/NYISO I7
  reconciled on each ISO's own published basis — NEISO FAIL→PASS (I7 AND I12 clear, 0 FAIL/0 WARN),
  CAISO improved +3,371 MW cited DMM firm-RA imports (still FAIL — residual = hydro-exclusion
  ledger-structure gap, routed to FF-1C with a spec), NYISO unchanged (basis already correct via
  FF-3D; gap ≈ hydro, routed to FF-1C) — central finding: §1.2-5's single-basis-mismatch hypothesis
  holds for NEISO only; (2) NEISO Net ICR replaces the 0.157 NERC stand-in — 30,305/27,298−1 =
  0.1102, FERC ER23-405-000 cited in constants.py, + FCA-17 DR 2,940 MW + imports 567 MW; (3)
  Pass-1B re-score (`results/capacity-price-validation/ff2b-neiso-pass1b.md`) + FIRST NEISO
  hindcast pair 2021–2025 (2022 bridged), bands pre-registered in #2582 before the run; (4) T1-F
  base-year re-runs registered (3 adequacy sidecars in `frontend/data/hindcast/`), gap-register
  updated. Source: `_firm_import_mw()` resolver in capacity.py (additive, no double-count vs
  dispatch import nodes) + cited constants + `TestFF2BAdequacyBasis` (test_capacity.py:1843).
  Bonus: latent `UNSET` NameError on EVERY forecast run (miso-76 regression) fixed — the one-line
  runner.py import landed via `de29a45` (#2587). **⚠ Governance note (flag, not stop-the-line):**
  the worker landed the source commit `96eac04` via a small source-only `git push` after
  `push_files` corrupted the 345 KB constants.py on reproduction and the git-data API was
  proxy-blocked; bytes were exact-on-disk and blob-verified byte-identical local↔remote (rule-27
  intent honored; core files GREW — no truncation), but it deviates from the Git § API-only rule —
  owner may want to bless a narrow "small source-only pack + mandatory blob-verify" exception.
  **NEISO pair EVIDENCE (for FF-2C):** base-year adequacy basis now clean, but the pair FAILs
  T-R bands hard — thermal retirements +880% (gas_cc +4552% false-retire), wind +1681%/solar +311%
  additions overshoot; storage PASSes. NEISO flip-gate items 3–4 are now gradeable and grade FAIL.
  **Out-of-program (22):** #2559/#2561/#2567 (docs-index + backcast-artifact-contract), #2563/#2574
  (caiso-102 hourfix keeper), #2564/#2566/#2568/#2572 (refactor consolidation — scripts/lib only),
  #2565 (gas daily-shape interp fix, fuel.py + tests), #2569/#2570/#2575/#2580 (ercot-86/88 —
  #2569 adds gated+cited faststart-pool fields to constants/scenarios), #2571/#2578 (**NYISO
  refix: keeper pointer → nyiso-64 (owner-authorized), determination NOT-YET (2023 C3a/C3b),
  marker + frontier stay WITHDRAWN** — NYISO still NOT flip-ready; root cause was missing eastern
  AC seam landing, real fix in interchange_config.py), #2576 (pjm-dataminer refactor), #2577
  (stale-refs docs incl. CLAUDE.md architecture-tree refresh — content-accurate), #2579
  (environment-block repro recorder in run_calibration_full.py, additive), #2583/#2585/#2587
  (capacity-pricing-review: new-build cost-benchmark corroboration intake; FF-1E's ATB test
  relaxed exact→bracket WITH the invariant preserved (envelope equality asserted in the new
  test_cost_benchmark_envelope.py) — FF-adjacent, clean). **Rule-27 clean:** capacity.py 4241→4269,
  scenarios.py 7930→7962, constants.py 7434→7514, runner.py 2469→2470 — all growth, no shrink.
  **Dispatched this turn: FF-3B [OPUS]** (re-emitted from amended plan §6 — W3-R readiness +
  T1-scale ERCOT 2026–2030 CES POC only; W4 stays deferred). FF-2D still gated: its prereq
  "Wave-1/2 lane merges complete" leaves owner-gated FF-2C outstanding → sequencing decision
  surfaced (sign off flips now → FF-2C then FF-2D; or defer flips → FF-2D unlocks at HEAD).
  **Mid-turn addendum (`6b5b6c4→735e302`, 4 merges):** #2591 (FF-2B follow-up — commits the
  `results/ff2b-after/` base-year evolution ledgers + logs, the item-4 evidence artifacts;
  additive, folds into the verified-pass), #2592 (fable-capabilities-priority — out-of-program
  governance infra: calibration-log split per-ISO, keeper-audit hook/agent, CLAUDE.md refresh;
  core counts unchanged), #2593 (caiso-103 probes/asks, out-of-program), #2594 (NYISO fuel-mix
  raw intake 2018–2026 — out-of-program; spans out-of-training years, rule-22 intake channel —
  authorization log assumed in-session, verify next turn if questioned). Rule-27 re-checked at
  `735e302`: unchanged.
- **turn 27 (manager `turn-24-phaekh`, refresh). `0e5cbbe→30f546e` (3 merges). QUIET for FF —
  nothing FF landed, nothing unlocked, no corrections; but one governance-relevant backcast event.**
  My turn-26 ledger reached main (#2557, merge `0e5cbbe`). All 3 merges out-of-program: #2556
  (ercot-87-midband-basis-measurement — probe + 6.9k-line measurement json + design doc, ERCOT
  trough/spread lane), #2555 (miso-78-m4-congestion-charter — charter doc + probe), **#2558
  (pjm-neiso-nyiso phantom-outage re-audit — ERCOT-79 cross-ISO lane).** **⚠️ #2558 WITHDREW NYISO's
  calibration-complete marker** (2026-07-19): NYISO keeper nyiso-62 was calibrated against a
  stale/under-counted outage extract (1,598 vs 2,641 rows); on the consolidated detector the recipe
  re-solves VERBATIM to NOT-YET (C1/C3a/C3b FAIL) — rule-11 co-dependence on the inaccurate
  availability envelope. NYISO marker now in `withdrawn{}`; CI quarantine re-blocks all NYISO
  out-of-training solve/score; the 2019+H1-2026 locked test was NEVER spent and stays available.
  **NEISO HOLDS** (re-audit reproduced its determination byte-for-byte, TRAIN keeper → neiso-60
  corrected envelope). Current markers: **COMPLETE = {NEISO}; WITHDRAWN = {NYISO}** (CAISO/ERCOT/
  PJM/MISO carry no marker in this file). **Impact on FF:** FF-2B is NOT blocked — its ≤2021
  hindcast pair is NEISO-only (marker present ✓), and its CAISO/NYISO work is base-year forecast
  reconciliation + Pass-1B no-LP (no out-of-training solve). But **FF-2C NYISO flip readiness is now
  gone** — NYISO must re-calibrate before any per-ISO flip sign-off. Rule-27 clean (capacity.py 4241,
  scenarios.py 7930, constants.py 7434, runner.py 2469 — unchanged). **Active front UNCHANGED: FF-2B
  ONLY** (re-emitted drift-clean at HEAD this turn on owner request; still awaiting worker launch —
  no branch on origin).
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
| FF-2B | OPUS | 2 | L-CAP | — | **verified-pass (turn 28)** — #2582+#2586/#2588/#2590+#2589+#2591, source `96eac04` | All 4 items: NEISO I7+I12 PASS (Net ICR 0.1102, ER23-405-000), CAISO +3,371 MW cited (residual→FF-1C hydro), NYISO basis-correct (residual→FF-1C); Pass-1B + FIRST NEISO pair (bands pre-registered #2582 before run); T1-F base-year sidecars + gap-register. Bonus UNSET runner.py fix. ⚠ git-push deviation, blob-verified — owner note. |
| FF-2C | OPUS | 2 | L-CAP | — | **issued (turn 14), owner-gated — per-ISO sign-off NOW DECISION-READY (t28)** | FF-2A+FF-2B evidence in hand. NEISO: basis clean but pair FAILs T-R bands (over-retire/over-build) — items 3–4 grade FAIL. NYISO NOT flip-ready (nyiso-64 NOT-YET, marker withdrawn). Rule 1: worsened fit = root-cause. |
| FF-2D | OPUS | 2 | L-VAL | ⛔ T1 gate | **issued (turn 14), gated on FF-2C disposition** | Prereq "W1/W2 lane merges complete" leaves FF-2C outstanding. Owner picks: flips first (FF-2C→FF-2D) or defer flips (FF-2D unlocks at HEAD). Rubric verdicts + promotion table. |
| FF-3A | — | 3 | L-VAL | ⛔ T2 | **WITHDRAWN-DEFERRED (owner 2026-07-19)** | T2 deferred with its tier behind plan §2.1b; prompt re-authored at gate-open. Do not dispatch. |
| FF-3B | OPUS | 3 | L-CES | — | **sent (turn 28), awaiting worker launch — no branch on origin (t29)** | Re-emitted from amended plan §6, supersedes turn-14 prompt. W3-R readiness + T1-scale CES POC (ERCOT 2026-2030) ONLY; W4 campaign deferred (§2.1b). R1 = FF-2A headline (solar recall). Runs solo (L-CES; no other worker in flight). |
| FF-3C | FABLE | 3 | L-PERF | conditional | not-sent | trigger-gated — inactive (only remaining FABLE prompt); trigger re-worded to active-tier breach (plan §6) |
| FF-3D | OPUS | 3 | L-CAP | — | **verified-issues (incomplete)** — LANDED #2463 | Intake + Option-B pairing + pre-registered bands; flip-gate Basis PASSES. Pair run via FF-3D-run. |
| FF-3D-run | OPUS | 3 | L-CAP | — | **landed** (#2471/#2473/#2478 + `5bb0c9b`) | NYISO fixed/curve/realized pair registered. Closed. |
| FF-3E | OPUS | 3 | L-VAL | ⛔ §2.1b evidence | not-sent | NEW (owner 2026-07-19): full-solve readiness battery + POC close-out (absorbs FF-4B honest-unfit list; adds >5-yr CLI guard). After FF-2D. |
| FF-4A | — | 4 | L-VAL | ⛔ | **WITHDRAWN (owner 2026-07-19)** | Prompt withdrawn outright (was HELD t18); Wave 4 deferred behind §2.1b. Do not dispatch, do not restore from history. |
| FF-4B | — | 4 | L-VAL | — | **WITHDRAWN-DEFERRED (owner 2026-07-19)** | Honest-unfit list moved to FF-3E close-out; rest re-authored at gate-open. |
| FF-4C | — | 4 | L-VAL | owner-gated | **WITHDRAWN-DEFERRED (owner 2026-07-19)** | PB-5 deferred with Wave 4 (§2.1b). |
| FF-5A | OPUS | 5 | L-DASH | — | not-sent | blocked: active-wave close-out (deferred Wave 4 NOT a prerequisite — §2.1b) |

Out-of-program / trivial (turn 29): #2596 (NYISO fuel-mix curation), #2597/#2602 (ercot-89
shoulder-online), #2598 (reserve-req unify refactor), #2599/#2600/#2603 (backcast-artifacts
refactor libs + tests), #2601 (capacity-cost-grounding — cited constants.py storage-cost
re-derivation, FF-relevant for FF-2D baseline attribution), #2604 (NYISO DR intake + loader),
#2595 (ledger t28). (turn 28): #2559/#2561/#2567 (docs-index + artifact-contract docs),
#2563/#2574 (caiso-102 keeper), #2564/#2566/#2568/#2572 (refactor consolidation, scripts/lib),
#2565 (gas daily-shape fuel.py fix), #2569/#2570/#2575/#2580 (ercot-86/88 lanes — gated+cited
constants/scenarios fields), #2571/#2578 (NYISO refix — keeper→nyiso-64, NOT-YET, marker stays
withdrawn), #2576 (pjm-dataminer), #2577 (stale-refs docs incl CLAUDE.md refresh), #2579
(env-block repro recorder), #2583/#2585/#2587 (capacity-pricing-review cost-benchmark
corroboration — FF-adjacent; FF-1E test exact→bracket with invariant preserved; carries the
runner.py UNSET fix `de29a45`), #2592 (fable-capabilities-priority governance infra), #2593
(caiso-103 probes), #2594 (NYISO fuel-mix raw intake 2018–2026), #2560 (ledger t27). (turn 27): #2556 (ercot-87-midband-basis-measurement — probe + measurement
json + design doc), #2555 (miso-78-m4-congestion-charter — doc + probe), #2558 (pjm-neiso-nyiso
phantom-outage re-audit — **WITHDREW NYISO calibration-complete marker**, NEISO HOLDS), #2557 (ledger
t26). (turn 26): #2545 (caiso-charge-economics probes), #2547 (caiso-100/101
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
  FF-4A stays gated. **Superseded 2026-07-19: hardened into full Wave-4 prompt
  withdrawal + the plan §2.1b gate (directive entry above).**
- **POC-first re-scope (2026-07-19, out-of-band):** Wave-4 prompts WITHDRAWN, FF-3A/T2
  deferred, ≤5-solve-year cap, §2.1b gate installed; FF-3B re-scoped (W4 deferred,
  T1-scale CES POC); FF-3E chartered. Plan amended in place.
- **#2439** — owner handled → resolved.

**AWAITING (each changes what I dispatch next):**
- **§2.1b gate-open per ISO** (replaces the former FF-4A golden-freeze and PB-5 waits —
  both WITHDRAWN-DEFERRED 2026-07-19; conditions: backcast keeper + marker, T1 POC
  gates, crossover gap + FF-3E readiness + projected cost, per-campaign authorization).
- **Per-ISO FF-2C sign-off — DECISION-READY as of turn 28** (FF-2B verified-pass). Evidence on
  the desk: FF-1A flip-gate scorecard + FF-2B findings (`docs/handoffs/ff-2b-adequacy-basis-
  2026-07.md`) + first NEISO pair (FAILs T-R retirement/addition bands — items 3–4 grade FAIL).
  NYISO NOT flip-ready (nyiso-64 NOT-YET, marker withdrawn). Owner picks which of
  PJM/MISO/CAISO/NEISO flip now, and whether NEISO waits on its pair root-cause.
- **FF-2D sequencing (coupled to the above):** flips first (FF-2C executes, then FF-2D scores the
  T1 gate on flipped defaults) OR defer flips (FF-2D unlocks immediately at HEAD, scores pre-flip
  posture). Manager recommendation: decide flips first — a T1 battery immediately invalidated by
  a flip wastes the 6-ISO solve budget.
- **Rule-deviation note (FF-2B):** worker used a small source-only `git push` (blob-verified)
  when `push_files` corrupted 345 KB constants.py — bless a narrow documented exception, or
  direct an alternative large-file transport; no action needed on the landed bytes (verified).
- **(Out-of-FF-program, surfaced turn 27, flag only)** NEISO holdout-data-equivalency register
  sign-off — `docs/holdout-data-equivalency-register-2026-07.md` §NEISO is the owner exit gate before
  any NEISO one-shot (locked test) may be re-authorized (rule 22). Backcast/validation matter, not
  FF, but a genuine pending owner sign-off.

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
- **turn 27 (`→30f546e`).** QUIET refresh for FF (3 merges, all out-of-program). t26 ledger on main
  (#2557). ⚠️ #2558 phantom-outage re-audit WITHDREW NYISO's calibration-complete marker (rule-11
  co-dependence on under-counted outages); NEISO HOLDS. Markers now COMPLETE={NEISO}, WITHDRAWN=
  {NYISO}. FF-2B unaffected (NEISO-only ≤2021 hindcast); FF-2C NYISO flip readiness lost pending
  re-calibration. FF-2B re-emitted drift-clean on owner request; still awaiting launch. Rule-27 clean.
- **turn 28 (`→735e302`, successor manager `turn-1-anm4jn`).** 34 merges. **FF-2B LANDED
  verified-pass** (#2582 bands-before-run + #2589 deliverable + source `96eac04`; NEISO I7+I12
  PASS on Net ICR basis, CAISO/NYISO residuals routed to FF-1C hydro-ledger, first NEISO pair
  produced — FAILs T-R bands; ⚠ git-push deviation blob-verified, flagged). Plan amendment #2581 +
  follow-ups #2584 on main. NYISO refix (#2571/#2578): keeper→nyiso-64, NOT-YET, marker stays
  withdrawn. Rule-27 clean (all core files grew). **Dispatched FF-3B** (re-emitted from amended
  plan §6). FF-2C sign-off + FF-2D sequencing surfaced as coupled owner decisions. Wave 2 close-out
  now waits only on FF-2C disposition.
- **turn 29 (`→9fa016b`).** QUIET refresh. t28 ledger on main (#2595). 9 out-of-program merges;
  #2601 (storage-cost re-derivation in constants.py, cited) flagged as an FF-2D baseline-attribution
  input; #2604 (NYISO DR intake) noted as a potential future cited I7 credit. FF-3B still awaiting
  launch (no branch). Rule-27 clean. No dispatches, no corrections; owner decisions unchanged.
