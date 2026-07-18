# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `0a11d48` (2026-07-18, turn 14 — manager session `eulpj6`).
- **Plan base SHA:** `c95176e`.
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
| FF-0B-redo | OPUS | 0 | L-VAL | — | **re-issued (turn 14)** | T1-F 6-ISO baseline; runs on green main (the BEFORE leg for round-3). |
| FF-0C | FABLE | 0 | L-CAP | — | **verified-pass** | #2418: R-NEW memo + owner box |
| FF-0D | OPUS | 0 | L-INP | — | **verified-pass** | #2413: audit, no source changes |
| FF-0E | OPUS | 0 | L-VAL | — | **re-issued (turn 14)** | crossover harness build; prior session left no branch. Runs on green main; coordinate run_capacity_hindcast.py w/ round-3. |
| FF-0F | OPUS | 0 | L-VAL/L-INP | — | **sent (turn 14)** | FC-5 benchmark-corridor intake (AEO2025/StdScen/ISO planning docs → curated datatype + loader + forecast_verdict FC-5 context wiring). No capacity.py, no solve — safe now. |
| FF-1A | FABLE | 1 | L-CAP | — | **verified-pass (complete)** | #2438 + #2448/#2451 + #2454. Inversion CLOSED; flip-gate scorecard complete. |
| FF-1A-restore | FABLE | 1 | L-CAP | — | **verified-pass** | #2438: capacity.py byte-exact restore. |
| FF-1A-C | FABLE | 1 | L-CAP | — | **verified-pass (via FF-1A-C2)** | #2448/#2451: 3 R-NEW legs scored. |
| FF-1A-C2 | OPUS | 1 | L-CAP | — | **verified-pass** — #2454 | doc synced, 0 PENDING. FF-1A complete. |
| FF-1B | FABLE | 1 | L-SCAR | — | **verified-pass** | #2423: correlated cold-event derate. |
| FF-1C | OPUS | 1 | L-INP | — | **verified-pass** | #2422: demand/DC currency + hydro. |
| FF-1D | OPUS | 1 | L-VAL | — | **issued (turn 14), gated** | prompt issued; fires after FF-0E merges + green main. |
| FF-1E | OPUS | 1 | L-INP | — | **issued (turn 14), gated** | prompt issued; starts after FF-2A-integrate round-3 merges (shares capacity.py entry-cost + constants.py). |
| FF-1F | OPUS | 1 | L-INP | — | **landed** (#2468/#2476/#2480) | DC=mid + derate=ON defaults + plan §2.1 record; tests updated. Closed. |
| FF-2A | FABLE | 2 | L-CAP | ⛔ | **verified-issues CRITICAL (non-integration)** — #2453 | Mechanism committed as UNAPPLIED patch; also broke all-ISO capacity-hindcast harness. → FF-2A-integrate. |
| FF-2A-integrate | FABLE | 2 | L-CAP | ⛔ | **🚨 RE-TRUNCATED capacity.py (#2474/#2477) → owner-reverted (#2481)** | Chunked pushes cut capacity.py 3967→1348 again; owner reverted to full pre-FF-2A blob. Superseded by **FF-2A-integrate round-3 [FABLE]** (issued t14): re-land mechanism on capacity.py+runner.py + harness passthroughs, blob-verify EVERY ≥300-line push. |
| FF-2B | OPUS | 2 | L-CAP | — | **issued (turn 14), gated** | prompt issued; starts after round-3 merges. CAISO/NEISO/NYISO I7 + NEISO ICR + first NEISO pair. |
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

Out-of-program / trivial: #2438 (restore), #2441 (FF-1A doc fill), #2442/#2444 (caiso-94),
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
- **Restore target** (turn 14): confirm full pre-FF-2A (⇒ round-3 re-lands FF-2A) + land the
  runner.py revert (`git revert 1341e2c`) or authorize me to push it.
- Entry-lookahead posture (FF-2A item 4 — returns with round-3), golden freeze (FF-4A),
  PB-5 (FF-4C).

---

## Corrections issued

1. **FF-0A-fix [OPUS]** (turn 2) — RESOLVED turn 3 (#2419).
2. **FF-0B-redo [OPUS]** (turn 2) — re-issued turn 14 (runs on green main).
3. **FF-1A-restore [FABLE]** (turn 5) — **RESOLVED turn 7 (#2438).**
4. **FF-1A-C [FABLE]** (turn 7) — **LANDED turn 10 (#2448/#2451).** Doc-sync gap → FF-1A-C2.
5. **FF-1A-C2 [OPUS]** (turn 10) — **RESOLVED turn 11 (#2454), verified-pass.**
6. **FF-2A-integrate [FABLE]** (turn 11) — integrity breach fix. Re-truncated capacity.py again
   (#2474/#2477) → owner-reverted (#2481). Superseded by **round-3 [FABLE]** (turn 14).
7. **FF-3D-run [OPUS]** (turn 13) — **LANDED** (#2471/#2473/#2478 + `5bb0c9b`).
8. **runner.py orphan revert** (turn 14) — `git revert 1341e2c` handed to owner (server-side,
   rule 27). Greens main. Open until landed.

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
