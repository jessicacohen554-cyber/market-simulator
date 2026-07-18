# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `4e9d63c` (2026-07-18, turn 15 — manager session `mhtoa0`).
- **Plan base SHA:** `c95176e`.
- **turn 15 (manager `mhtoa0`). MAIN IS GREEN — FF-2A integration MERGED (#2486 `e9f9d60`) +
  sidecars (#2491/#2492); FF-0F verified-pass; FF-1F defaults live (#2493). Wave-2 gates FIRE.**
  Refresh `0a11d48→0c2e84e→4e9d63c` (13 merges; #2486/#2492/#2493 landed mid-turn). **FF-0F =
  #2488 + #2490, verified-pass:** schema-first `benchmark-corridor` datatype (schema + registry
  modules + AEO2025 fetch/curate CLIs + loader + 13 tests) and FC-5 rewired to read anchors as
  CONTEXT ONLY (rule 13 explicit, anchors never gate); all **73 scorer tests pass** with the
  rewiring (re-run green at `4e9d63c`); fully additive, no defaults changed, no solve, no shrink.
  Remaining sources filed as intake rows M9–M15. **FF-2A-integrate round-3 = RESOLVED,
  verified-pass:** the mechanism merged inside #2486 ("scripts reorg", 818 files — its first
  commit `e9f9d60` is the integration, restoring the halves lost in the #2477 revert).
  Manager-verified at HEAD: capacity.py **4230** lines, ZERO functions lost vs the restored 3967
  blob (def-inventory diff empty), `evolve_fleet` signature accepts `entry_rate_caps_mw` +
  `entry_pipeline` and matches the runner.py:822 call site (AST-checked), config fields in
  ScenarioConfig (#2491's run-config fields now on-registry, rule 24 satisfied), **14
  harness-passthrough refs** in `scripts/run_capacity_hindcast.py` (turn-13 coordination item
  done), capacity.py/runner.py/scenarios.py/forecast_verdict.py all compile at HEAD. Sidecars:
  #2491 (PJM/MISO r2 hindcasts) + #2492 (ERCOT r2 reproduction leg — identical
  additions/retirements/BLK-10 on integrated code) are governance-clean (vintage-2020,
  2021+2023–2025 solved, 2022 BRIDGED not solved, `leakage_violations=[]`). Sidecars-before-source
  ordering noted as a process wart, cured by the merge. #2486's guard change (`-M`
  rename-following, shrink checked at the rename destination) is sound — it tightens, not
  weakens. My mid-turn FC-5-regression alarm was divergent-base diff noise — RETRACTED (#2486's
  merge-base predates #2490; forecast_verdict.py untouched by it). **FF-1F supplemental =
  #2493:** the owner-decided forecast-posture defaults are now LIVE (`datacenter_load_path`
  "off"→"mid", `correlated_forced_outage` False→True) with explicit backcast/hindcast
  byte-identity guards and plan §2.1 records — FF-1F fully closed. **Reorg drift check:** all
  FF-critical run/score scripts stayed at `scripts/` (only data tooling → `scripts/data/`,
  one-offs → `scripts/archive/`) — queued prompts need NO drift-patch. Out-of-program this
  window: #2483/#2487 (caiso-98), #2484/#2495 (miso-74), #2489 (ercot83), #2494 (ercot apr/may
  scarcity tooling), #2485 (ledger t14). **ONE housekeeping ask remains: delete/stand down the
  round-3 chunk branch `claude/ff2a-entry-stack-integration-6zd9zv`** (capacity.py PARTIAL at
  2295 there; a later merge would re-truncate — rule-27 hazard). Turn-14 `git revert 1341e2c`
  ask is RETRACTED (moot — forward-fix merged). **Gates now OPEN:** FF-0B-redo + FF-0E (green
  main) and FF-1E + FF-2B (round-3 merged) are launchable from their turn-14 prompts as issued;
  FF-2C stays owner-gated behind FF-2B; FF-2D after W1/W2 lands; FF-1D after FF-0E.
- **turn 14 (manager `eulpj6`). capacity.py RE-TRUNCATED → RESTORED (#2481); runner.py orphan → fix handed to owner.**
  FF-2A-integrate's chunked pushes (#2474/#2477, `a4c3648`+`41c7ead`) cut capacity.py **3967→1348**
  (24 fns gone incl. `evolve_fleet`, `apply_economic_retirements`, `apply_economic_new_entry`,
  `apply_ccs_retrofit`, `compute_lcoe`, `wright_cost`) — turn-7 rule-27 mode again;
  `file-integrity-guard.yml` did NOT block the 71% shrink (INVESTIGATE: intentional-shrink label /
  direct-merge path). **Owner restored capacity.py via #2481** (revert to full pre-FF-2A blob, 3967).
  But the revert left **runner.py orphaned**: it calls `evolve_fleet(entry_rate_caps_mw=…,
  entry_pipeline=…)` (commit 1341e2c, +52 lines) which the reverted signature rejects → TypeError on
  EVERY forecast/hindcast solve → **main STILL RED**. Diagnosed + verified the fix (`git revert
  1341e2c`, runner.py-only, restores blob `b1b24f1`, `py_compile` + real import clean, evolve_fleet
  params then match the call site). **Handed to owner as a server-side revert** (rule 27 — NOT a
  2000-line API push). Closed since t13: **FF-1F** (#2468/#2476/#2480) + **FF-3D-run**
  (#2471/#2473/#2478+`5bb0c9b`). Issued for green main: **FF-2A-integrate round-3 [FABLE]** (re-land
  the mechanism on capacity.py + runner.py + re-add harness passthroughs; blob-verify EVERY
  ≥300-line push — the explicit anti-truncation prompt), **FF-0B-redo [OPUS]** (T1-F baseline = the
  BEFORE leg), **FF-0E [OPUS]** (crossover harness). **FF-0F [OPUS]** (FC-5 benchmark intake — no
  capacity.py/no solve) stands, runnable now. This ledger pushed on a fresh-from-main `…eulpj6`
  branch; runner.py NOT on it (owner reverts server-side). **AWAITING owner:** confirm restore
  target = full pre-FF-2A (⇒ round-3 re-lands FF-2A); land the runner.py revert (or authorize me).
- **turn 13 refresh (`→68e38db`).** **FF-3D LANDED** (#2463) — verified-issues (INCOMPLETE but
  clean): NYSRC App-D Table D.2 ICAP→UCAP intake landed with exact per-year citations (0.083→
  0.1321), Option-B pairing implemented, bands PRE-REGISTERED, NYISO set curve-eligible — flip
  memo's named binding blocker (Basis) now PASSES. BUT the fixed-vs-curve-ON hindcast **pair was
  NOT run** (honestly flagged, blocked in-session on clean-data regen; §5.3 gives exact
  commands). → **FF-3D-run [OPUS]**. **Important:** FF-3D also found the FF-2A patch (c48daca)
  had **broken the capacity-hindcast harness for EVERY ISO** (TypeError since it landed) and
  fixed it byte-identically — the FF-2A breach was worse than the turn-11 read (not just dead
  code; it blocked all capacity hindcasts). **Coordination:** FF-3D removed the 3 harness
  passthroughs → **FF-2A-integrate must re-add them** in run_capacity_hindcast.py when it wires
  the config fields (the patch doesn't cover the harness). Out-of-program this window: #2466
  miso-73 (rejected probe), #2465/#2462 caiso-97, #2461 ercot81 keeper, #2459 miso. FF-1F +
  FF-2A-integrate still in flight (no PR).
- **turn 12 — owner decisions received; 2 sessions dispatched (no refresh).** Owner resolved 4
  gated calls: (1) **capacity-market clearing ON for all ISOs that have one = PJM/MISO/NYISO/
  NEISO/CAISO (all but ERCOT)** — the approved TARGET; FF-2C executes per-ISO by READINESS
  (PJM/MISO after FF-2A-integrate; NYISO after FF-3D; NEISO needs first cap-hindcast evidence;
  CAISO is RA-not-auction → RA-specific construction verified before flip). Rule 1: a flip that
  worsens fit is a root-cause bug, not a revert. (2) **NYISO R5a = Option B** (NYCA-wide static
  proxy; session downloads NYSRC App-D Table D.1.1). (3) **datacenter_load_path default = mid**
  (data-center load IS modeled, moderate). (4) **correlated_forced_outage default = ON.** #2439
  handled. Dispatched **FF-3D [OPUS]** and **FF-1F [OPUS]** (flip DC=mid + derate=ON defaults +
  record all 4 decisions in plan §2.1). FF-2C owner-approved but blocked on FF-2A-integrate.
- **🚨 turn 11 — FF-2A INTEGRITY BREACH (verified-issues CRITICAL).** FF-2A (#2453) committed
  its core mechanism as an **unapplied patch** (`ff2a-core.patch`, 635 lines). capacity.py +
  runner.py byte-unchanged; config fields absent; modules dead; test fails; sidecars don't
  reproduce (patch applied locally — PJM solar 24.0→19.3). [turn 13: it ALSO broke the
  all-ISO capacity-hindcast harness.] → **FF-2A-integrate [FABLE]** (apply-forward). ERCOT solar
  0 even with mechanism = finding. **FF-1A-C2 (#2454) verified-pass.**
- **turn 10:** **FF-1A-C LANDED** (#2448/#2451) — 3 R-NEW legs scored; PJM blk10 fired 2.5 GW
  (still over-fires → FF-2A sizing warranted). Verified-issues (doc-sync) → FF-1A-C2. Released FF-2A.
- **turn 7:** **MAIN RESTORED** (#2438) — capacity.py un-truncated 2291→3967, byte-faithful.

Status vocabulary: `not-sent` · `sent` · `landed` · `verified-pass` ·
`verified-issues` · `correction-sent`.

---

## Session status table

| FF id | Model | Wave | Lane | Gate | Status | Evidence |
|---|---|---|---|---|---|---|
| FF-0A | FABLE | 0 | L-VAL | ⛔ rubric | **verified-pass** | rubric #2414 + scorer #2419 |
| FF-0A-fix | OPUS | 0 | L-VAL | — | **verified-pass** | #2419: 73 tests pass |
| FF-0B-redo | OPUS | 0 | L-VAL | — | **re-issued t14 — GATE OPEN (t15: main green)** | T1-F 6-ISO baseline; launchable now from the turn-14 prompt. |
| FF-0C | FABLE | 0 | L-CAP | — | **verified-pass** | #2418: R-NEW memo + owner box |
| FF-0D | OPUS | 0 | L-INP | — | **verified-pass** | #2413: audit, no source changes |
| FF-0E | OPUS | 0 | L-VAL | — | **re-issued t14 — GATE OPEN (t15: main green)** | crossover harness build; launchable now. run_capacity_hindcast.py coordination resolved (round-3 merged, passthroughs in place). |
| FF-0F | OPUS | 0 | L-VAL/L-INP | — | **verified-pass (turn 15)** | #2488 + #2490: benchmark-corridor datatype + loader + 13 tests + FC-5 context-only wiring; 73 scorer tests pass; additive; M9–M15 gaps filed. |
| FF-1A | FABLE | 1 | L-CAP | — | **verified-pass (complete)** | #2438 + #2448/#2451 + #2454. Inversion CLOSED; flip-gate scorecard complete. |
| FF-1A-restore | FABLE | 1 | L-CAP | — | **verified-pass** | #2438: capacity.py byte-exact restore. |
| FF-1A-C | FABLE | 1 | L-CAP | — | **verified-pass (via FF-1A-C2)** | #2448/#2451: 3 R-NEW legs scored. |
| FF-1A-C2 | OPUS | 1 | L-CAP | — | **verified-pass** — #2454 | doc synced, 0 PENDING. FF-1A complete. |
| FF-1B | FABLE | 1 | L-SCAR | — | **verified-pass** | #2423: correlated cold-event derate. |
| FF-1C | OPUS | 1 | L-INP | — | **verified-pass** | #2422: demand/DC currency + hydro. |
| FF-1D | OPUS | 1 | L-VAL | — | **issued (turn 14), gated** | prompt issued; fires after FF-0E merges + green main. |
| FF-1E | OPUS | 1 | L-INP | — | **issued t14 — GATE OPEN (t15: round-3 merged)** | launchable now (capacity.py entry-cost + constants.py base is settled at `4e9d63c`). |
| FF-1F | OPUS | 1 | L-INP | — | **landed + defaults LIVE** (#2468/#2476/#2480 + #2493) | #2493 flips `datacenter_load_path`→"mid", `correlated_forced_outage`→True with backcast byte-identity guards; plan §2.1 recorded. Closed. |
| FF-2A | FABLE | 2 | L-CAP | — | **RESOLVED via FF-2A-integrate (turn 15)** | #2453 breach history: unapplied patch + broke all-ISO harness. Mechanism now merged (#2486 `e9f9d60`) + sidecars #2491/#2492. Lane closed. |
| FF-2A-integrate | FABLE | 2 | L-CAP | — | **verified-pass (turn 15, via #2486 `e9f9d60` + #2491/#2492)** | Mechanism merged + manager-verified (0 fn loss, signature matches runner, fields on-registry, 14 harness refs, compiles). PJM/MISO/ERCOT r2 sidecars governance-clean. FF-2A lane CLOSED. Housekeeping: delete chunk branch `…6zd9zv` (partial capacity.py — re-truncation hazard). |
| FF-2B | OPUS | 2 | L-CAP | — | **issued t14 — GATE OPEN (t15: round-3 merged)** | launchable now. CAISO/NEISO/NYISO I7 + NEISO ICR + first NEISO pair. |
| FF-2C | OPUS | 2 | L-CAP | — | **issued (turn 14), owner-gated** | prompt issued; owner-approved flip all-but-ERCOT, staged by readiness. After round-3 + FF-2B. Rule 1: worsened fit = root-cause. |
| FF-2D | OPUS | 2 | L-VAL | ⛔ T1 gate | **issued (turn 14), gated** | prompt issued; runs after W1/W2 merges. Rubric verdicts + promotion table. |
| FF-3A | OPUS | 3 | L-VAL | ⛔ T2 | not-sent | blocked: FF-2D + owner |
| FF-3B | OPUS | 3 | L-CES | — | **issued (turn 14), gated** | prompt issued; W3-R readiness → GO/NO-GO → W4. R1 = FF-2A headline (solar recall). |
| FF-3C | FABLE | 3 | L-PERF | conditional | not-sent | trigger-gated — inactive |
| FF-3D | OPUS | 3 | L-CAP | — | **verified-issues (incomplete)** — LANDED #2463 | Intake (NYSRC ICAP→UCAP factors, cited) + Option-B pairing + pre-registered bands + curve-eligibility landed clean; flip-gate Basis PASSES. Also FIXED the FF-2A-broken capacity-hindcast harness (all-ISO). **Hindcast pair NOT run** (blocked on clean-data regen) → FF-3D-run. |
| FF-3D-run | OPUS | 3 | L-CAP | — | **landed** (#2471/#2473/#2478 + `5bb0c9b`) | NYISO fixed/curve/realized pair registered (`nyiso-2021-2025-*.json`). Closed. |
| FF-4A | OPUS | 4 | L-VAL | ⛔ owner-gated | not-sent | blocked: FF-3A + owner |
| FF-4B | FABLE | 4 | L-VAL | — | not-sent | blocked: FF-4A |
| FF-4C | OPUS | 4 | L-VAL | owner-gated | not-sent | blocked: FF-4A + owner |
| FF-5A | OPUS | 5 | L-DASH | — | not-sent | blocked: Wave 4 |

Out-of-program / trivial: #2483/#2487 (caiso-98 probe/charter), #2484/#2495 (miso-74 seam +
attestation), #2489 (ercot83 posture backcast), #2494 (ercot apr/may scarcity tooling),
#2485 (ledger t14),
#2438 (restore), #2441 (FF-1A doc fill), #2442/#2444 (caiso-94),
#2445/#2449 (caiso-95), #2447 (miso-72), #2450 (ercot commitment-posture lever),
#2456 (caiso-96), #2459 (miso), #2461 (ercot81 keeper), #2462/#2465 (caiso-97),
#2466 (miso-73 rejected probe), #2482 (miso-74 seam charter), #2481 (capacity.py restore),
#2437/#2443/#2446/#2452/#2460/#2464 (this ledger). #2439 handled.

---

## Owner decisions

**Received:**
- **D1 = B (R-NEW), by action** (2026-07-18). Done.
- **Capacity-market flips (turn 12):** ON for all ISOs with a real capacity market =
  PJM/MISO/NYISO/NEISO/CAISO (all but ERCOT). Target; FF-2C executes per-ISO by readiness.
  CAISO = RA-not-auction. Rule 1 governs (worsened fit → root-cause, not revert).
- **NYISO R5a = Option B** (turn 12) — NYCA-wide static proxy. FF-3D landed the intake.
- **datacenter_load_path default = mid** (turn 12) — DC load IS modeled (moderate). FF-1F applies.
- **correlated_forced_outage default = ON** (turn 12) — FF-1F applies (no ORDC double-count).
- **#2439** — owner handled → resolved.

**AWAITING (each changes what I dispatch next):**
- **Housekeeping (turn 15):** delete/stand down chunk branch
  `claude/ff2a-entry-stack-integration-6zd9zv` — it holds a PARTIAL capacity.py (2295 lines);
  a later merge would re-truncate (rule-27 hazard). The turn-14 `git revert 1341e2c` ask is
  RETRACTED (moot — #2486 forward-fixed the orphan).
- Entry-lookahead posture (FF-2A item 4 — round-3 merged; owner call still open), golden freeze
  (FF-4A), PB-5 (FF-4C).

---

## Corrections issued

1. **FF-0A-fix [OPUS]** (turn 2) — RESOLVED turn 3 (#2419).
2. **FF-0B-redo [OPUS]** (turn 2) — re-issued turn 14 (runs on green main).
3. **FF-1A-restore [FABLE]** (turn 5) — **RESOLVED turn 7 (#2438).**
4. **FF-1A-C [FABLE]** (turn 7) — **LANDED turn 10 (#2448/#2451).** Doc-sync gap → FF-1A-C2.
5. **FF-1A-C2 [OPUS]** (turn 10) — **RESOLVED turn 11 (#2454), verified-pass.**
6. **FF-2A-integrate [FABLE]** (turn 11) — integrity breach fix. Re-truncated capacity.py again
   (#2474/#2477) → owner-reverted (#2481). Superseded by **round-3 [FABLE]** (turn 14) —
   **RESOLVED turn 15** (#2486 `e9f9d60` + sidecars #2491/#2492, manager-verified).
7. **FF-3D-run [OPUS]** (turn 13) — **LANDED** (#2471/#2473/#2478 + `5bb0c9b`).
8. **runner.py orphan revert** (turn 14) — **RETRACTED turn 15.** Superseded by merging #2486
   (whose `e9f9d60` gives evolve_fleet the kwargs runner.py passes). Landing the revert now
   would re-orphan in the other direction.

---

## Turn log

- **turns 1–6.** Wave 0 dispatch + verify; FF-1A truncated capacity.py (main broken through t6).
- **turn 7.** `→7d4b738`. **MAIN RESTORED** (#2438). FF-1A-C issued. FF-2A HELD.
- **turn 8.** `→4bfb618`. capacity.py FIXED confirmed.
- **turn 9.** `→ab69df3`. Wave 2 gated; surfaced FF-3D (owner R5a) + scoped-FF-2A.
- **turn 10.** `→ae754e2`. FF-1A-C LANDED. Released FF-2A.
- **turn 11.** `→bc46dc0`. FF-1A-C2 verified-pass. **FF-2A verified-issues CRITICAL** (unapplied
  patch) → FF-2A-integrate. Wave 2 gated; FF-2B held.
- **turn 12 (owner decisions).** Flips all-but-ERCOT, R5a=B, DC=mid, derate=ON, #2439 handled.
  Dispatched FF-3D + FF-1F. Explained readiness-staging + CAISO-is-RA.
- **turn 13 (refresh — "refresh").** `→68e38db`. **FF-3D LANDED** (#2463), verified-issues
  INCOMPLETE: NYSRC ICAP→UCAP intake + Option-B pairing + pre-registered bands + curve-
  eligibility clean (flip-gate Basis PASSES); hindcast pair NOT run → **FF-3D-run [OPUS]**.
  FF-3D also fixed the FF-2A-broken capacity-hindcast harness (all-ISO TypeError since c48daca).
  Coordination: FF-2A-integrate must re-add the 3 harness passthroughs. Clarified for owner:
  DC=mid means data-center load IS modeled. Out-of-program: #2466/#2465/#2462/#2461/#2459. In
  flight: FF-1F, FF-2A-integrate, FF-0E, FF-0B-redo, FF-1E. Watch next: FF-3D-run +
  FF-2A-integrate.
- **turn 14 (manager `eulpj6`).** `→0a11d48`. capacity.py RE-TRUNCATED (#2474/#2477) →
  owner-RESTORED (#2481, full 3967); runner.py orphan (evolve_fleet kwargs, commit 1341e2c) →
  main still red → `git revert 1341e2c` handed to owner (rule 27, no 2000-line API push). FF-1F +
  FF-3D-run confirmed LANDED. Issued prompt pack: **FF-2A-integrate round-3 [FABLE]**,
  **FF-0B-redo**, **FF-0E**, **FF-0F** (FC-5 intake), and the gated queue **FF-1D/1E/2B/2C/2D/3B**.
  Ledger pushed on fresh-from-main `…eulpj6`; runner.py NOT on it. Watch next: runner.py revert
  lands → fire round-3 + FF-0B-redo.
- **turn 15 (manager `mhtoa0`, refresh).** `→0c2e84e→4e9d63c` (13 merges; #2486/#2492/#2493
  landed mid-turn). **MAIN GREEN.** FF-0F verified-pass (#2488/#2490; 73 scorer tests green at
  `4e9d63c`; curate tests static-verified — pandas absent in mgr env). **FF-2A-integrate
  round-3 RESOLVED verified-pass**: mechanism merged inside #2486 (`e9f9d60`) — manager-verified
  (AST signature match with runner.py:822, zero function loss vs 3967 blob, capacity.py 4230,
  fields in ScenarioConfig, 14 harness-passthrough refs, compiles at HEAD); sidecars #2491
  (PJM/MISO) + #2492 (ERCOT reproduction) governance-clean. FF-1F defaults LIVE via #2493
  (DC=mid, derate=ON, backcast byte-identity guards). FC-5-regression alarm retracted
  (divergent-base noise). Reorg drift-checked: run/score scripts unmoved — no prompt patches
  needed. Housekeeping ask: delete chunk branch `…6zd9zv`; 1341e2c revert ask retracted.
  **Gates OPEN:** FF-0B-redo, FF-0E, FF-1E, FF-2B launchable from turn-14 prompts. Watch next:
  those four land; then FF-1D (after FF-0E), FF-2C (owner-gated, after FF-2B), FF-2D (after
  W1/W2), FF-3B.
