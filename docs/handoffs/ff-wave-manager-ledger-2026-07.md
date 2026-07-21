# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `3cbf5b16` (2026-07-21, turn 41 — manager session `ff-wave-manager-standing-e90gfj`).
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
- **turn 39 (manager `ff-wave-manager-7ra116`, refresh). `b6ace721→08c831c9` (26 merges). FF-3E
  VERIFIED-PASS; the FULL active-wave build-out landed — FF-5A + FF-3F + FF-3G all verified-pass;
  FF-3H sent-not-launched. OWNER RE-SCOPE recorded.** **OWNER DIRECTIVE (turn 38-39, 2026-07-21):
  "I just want the infrastructure built." §2.1b gates full 25-yr SOLVES only — it does NOT gate
  building/T1-testing machinery. Prior framing of later waves as "blocked" was corrected. The
  deferred waves are re-scoped: their **T1-scale infrastructure halves are dispatchable NOW**
  (≤5 solve-years), only the full-horizon CAMPAIGN RUNS (CES 2026-2050 ladder, PB-5 full bands,
  T2/T3 certification) stay behind §2.1b.** Manager chartered three T1-infra prompts + FF-5A;
  owner launched FF-5A/FF-3F/FF-3G (FF-3H not yet). **Verifications (content-checked on disk, not
  PR text):** (1) **FF-3E verified-pass** (#2691) — closeout doc has all 11 sections (§2 per-ISO
  §2.1b scorecard, §6 wall/RSS "what would 10h buy", §8 honest-unfit absorbing FF-4B, §10
  owner-decision box); `scripts/ff_readiness_battery.py` has all 5 parts (walk_inputs / config
  round-trip / kill_resume_drill / project_full_horizon / schedulability guard) + `tests/
  test_ff_readiness_battery.py`; `run_full_horizon.py` guard `MAX_UNAUTHORIZED_SOLVE_YEARS=5`.
  (2) **FF-5A verified-pass** (#2703/#2708/#2710/#2713/#2715/#2717) — `register_forecast_run.py`
  the migrated ONE entry point (register_hindcast + register_forecast_baseline delegate; sidecars
  keep working; separate from CI-gated backcast registry); `forecast-runs.html` + `forecast-
  status.html` present, status page surfaces HOLD + honest-unfit truthfully (no green-wash).
  (3) **FF-3F verified-pass** (#2700/#2704/#2706) — F-3 fixed (`generate_financial_reports.py`
  runs on fresh checkout; was requiring hand-laid --eia860-path/--ownership-map), premium→surface
  signal reproduced at T1, forward numbers labeled STRUCTURAL not conclusions (`ff-ces-infra-t1-
  2026-07.md`). (4) **FF-3G verified-pass** (#2701) — all 8 FC categories resolve to valid tokens,
  §2.1b-gated instruments degrade to SKIPPED cleanly (correctly HOLDs T2), found+fixed I12
  mirror-constant coupling, synthetic t2 fixture + `test_forecast_verdict_t2.py`. **FF-3H (PB
  bands T1) = sent, NOT launched** (no branch/doc on origin). **RULE-27 BASELINE MOVED AGAIN
  (verified, NOT truncation):** `model/capacity.py` 4269→**32-line facade** (aliases `sys.modules`
  to the new `model/capacity_evolution/` package: retirements 1753 / new_entry 1225 / evolve 722 /
  ccs 407 / adequacy 361 / __init__ 285 = 4753 total > orig; monkeypatch/import semantics
  preserved; pinned by `tests/test_capacity_evolution_facade.py`) — #2709/#2711/#2714/#2716
  capacity-evolution-package refactor. Also `data/fuel/` package split (#2712/#2718) — but the
  WATCH-SET fuel file `config/fuel_trajectories.py` is unchanged (1050); data/fuel/ loaders are
  outside the watch set. **New watch set: capacity.py-facade (32) + capacity_evolution/ package
  (6 files) · scenarios.py 8102 · constants.py-facade 2422 · runner.py 2470 · fuel_trajectories
  1050 · capacity_market 2392 · ercot_envelopes 1960.** **⚠ OWNER FLAG — NEISO:** #2696 ("neiso-60:
  complete phantom-outage re-audit bundle + fix broken status") landed AFTER the turn-38 "don't do
  anything in NEISO" hold. It is a backcast-calibration housekeeping lane (out-of-program), not an
  FF NEISO solve/score/flip — but surfacing to owner to confirm the hold's scope. **Out-of-program
  (~18 merges):** #2694 (turn-38 ledger), #2695 (phase-refactor cachekey-tripwire-fix), #2696
  (neiso-60 — flagged above), #2697/#2698 (nyiso-keeper-missing-calibration), #2699/#2702/#2705/
  #2707 (caiso-import-gas-volume), #2709/#2711/#2714/#2716 (capacity-evolution-package refactor),
  #2712/#2718 (fuel-package-refactor), #2693 (caiso-108-gate-attribution). Next: dispatch/confirm
  FF-3H if owner wants it; amend plan §6/§9 to record the T1-infra re-scope (FF-3F/3G/3H rows,
  deferred-campaign split). Active-wave build-out is otherwise COMPLETE.
- **turn 37 (manager `ff-wave-manager-7ra116`, NEW session — re-applies lost turn 36 + full loop).
  `5b9e79c2→f49cf768` (20 merges). FF-2D LANDED VERIFIED-PASS; FF-3E DISPATCHED (last-but-one
  Phase-A rung). The turn-36 ledger push never reached origin (last push #2668 = turn-35 ledger),
  so this session re-verified FF-2D independently and records it here.** FIRST-ACTION check: ledger
  on main still showed last-reviewed `5b9e79c2` / FF-2D IN FLIGHT (turn-35 state) → turn 36
  re-applied. **FF-2D verification (all deliverables confirmed on disk at HEAD, not trusted from PR
  text):** (1) `docs/handoffs/ff-t1-gate-2026-07.md` (20,490 B) present; (2)
  `docs/handoffs/ff-t1-gate-verdicts.json` present + GENUINE — all six ISOs read **HOLD /
  T2-ineligible**, FC-1 structural FAIL the dominant gate; sample CAISO-t1f FC-1 = FAIL
  [I3,I4,I7,I9] (I4 gas_st off 1,333 MW = the FF-0B "A1" capacity-accounting leak; I7 base-year
  accredited-firm < requirement 2026/2027; I3 slack); ERCOT-t1f FC-1 = FAIL [I3] scarcity slack;
  ERCOT-t1x adds FC-2/FC-4 FAIL. (3) Dashboard registration confirmed on the **forecast-validation
  namespace** (`frontend/data/hindcast/`, kind `t1f`/`crossover`) — 6 ISO `*-2026-2030-ff-t1f-
  baseline.json` + `ercot/pjm-2023-2027-crossover.json`; NOT the backcast registry (correct — no
  keeper/holdout). Golden fixture disclosed **frozen-not-regenerated** (carried to FF-3E honest-unfit
  list). Branch `claude/t1-gate-scoring-zrc3xa` fully merged #2666/#2681/#2684/#2685. **Closest to
  the §2.1b gate: PJM + NEISO (I4 "A1" leak is their SOLE blocker).** **RULE-27 BASELINE MOVED
  (verified, NOT a truncation):** `constants.py` split into a re-export FACADE (2,422 lines) + three
  siblings — `config/fuel_trajectories.py` (1,050), `config/capacity_market.py` (2,392),
  `config/ercot_envelopes.py` (1,960); content preserved, guarded by `tests/test_constants_facade.py`
  (#2675/#2677/#2682). Watch set is now EIGHT files: capacity.py 4269 · scenarios.py 8102 ·
  constants.py-facade 2422 · runner.py 2470 · fuel_trajectories 1050 · capacity_market 2392 ·
  ercot_envelopes 1960 — all at expected baseline, no shrink. **FF-3E DISPATCHED** this turn (prompt
  re-emitted drift-clean at `f49cf768`; [OPUS], solo in L-VAL — no lane conflict). **Out-of-program
  (14 merges):** #2668 (turn-35 ledger push), #2670 (miso-80 direction-symmetric loss), #2667
  (nyiso-65 scr-edrp land2 — NYISO recovery, marker still WITHDRAWN), #2669/#2672 (caiso-dam
  intake), #2671/#2674/#2680 (phase-refactor calendar-callers), #2676/#2679 (phase-refactor
  ci-restoration), #2673/#2678/#2683 (intertie-elasticity-measurement — CAISO measurement lane),
  #2675/#2677/#2682 (constants-split-refactor infra — the rule-27 baseline move above). Next unlock:
  FF-5A (L-DASH close-out) when FF-3E lands verified-pass; FF-3C stays trigger-gated/inactive. No
  new merges beyond f49cf768 to review (turn 36 already saw through #2685).
- **turn 35 (manager `turn-1-anm4jn`, refresh). `15dfe15f→5b9e79c2` (16 merges). FF-2C-rig
  LANDED VERIFIED-PASS (#2654/#2662, branch `ff-2c-net-cone-curve-isos-mhn006`); FF-2D IN FLIGHT
  (branch `claude/t1-gate-scoring-zrc3xa` on origin, unmerged). No new dispatches — the wave is
  FF-2D running.** **FF-2C-rig verification (all 3 items ✓):** (1) `_net_cone_scalar` now
  preserves `demand_curve`/`net_cone_curve_per_kw_yr`/`seasonal_rbdc` and scales the CURVE anchor
  — registry AND per-delivery-year `MARKET_DESIGN_VINTAGES`; verified to move the PJM curve price
  EXACTLY 2.0× at 2×. Bonus defect fixed: all T1.7 rungs shared one solve cache — `make_rung_specs`
  now namespaces per rung. (2) economic-vs-exogenous retirement split via the RC-1B ledger reason
  field. (3) PJM T1.7 re-measured: economic retirements 0.797→0→0 GW — **T1.7a PASS**; exogenous
  flat 4.575 GW; ERCOT control byte-identical. Rig repair only, no tuning. **Out-of-program (13)**
  incl. **#2659/#2660 secrets remediation** (5 public data-portal keys untracked; owner CLOSED t38 —
  keys public). Rule-27 clean (4269/8102/7627/2470).
- **turns 30–34 (manager `turn-1-anm4jn`, collapsed).** t34: **FF-2C verified-pass** (#2645/#2647/
  #2649) — flip {PJM,MISO,CAISO,NEISO}=ON + R4 published anchors + byte-identity coercion; PJM/MISO
  curve hindcasts honest FAILs (routed, rule 1); T1.7 rig defect → FF-2C-rig; **FF-2D dispatched** —
  Wave 2 CLOSED. t30: **FF-3B verified-pass** (#2613) — W3-R NO-GO (R1/R2), CES POC machinery-proven
  3×5yr, F-3 found. t31: FF-2C flip sign-off delegated → APPROVED PJM/MISO/CAISO/NEISO, NYISO
  deferred. G-series (FF-G2/G3/G4/G5) = owner-launched forecast-input lanes (FF-2D attribution).
  Rule-27 clean throughout. (Full detail in prior ledger commits.)
- **turns 28–29 (manager `turn-1-anm4jn`).** t28: FF-2B LANDED verified-pass (#2582 bands-before-run
  + #2589 deliverable + source `96eac04`; NEISO I7+I12 PASS on Net ICR basis, CAISO/NYISO residuals
  routed to FF-1C, first NEISO pair FAILs T-R bands; ⚠ git-push deviation blob-verified, flagged).
  Dispatched FF-3B. t29: QUIET refresh; #2601 (storage-cost re-derivation, cited) flagged as FF-2D
  baseline-attribution input. Rule-27 clean. (Full detail in prior ledger commits.)
- **turns 10–27 (collapsed — see prior ledger commits for full detail).** Wave 0/1 dispatch + verify;
  capacity.py truncation saga (t6/t11/t14) restored; FF-2A integration (t15); FF-0F closed (t17);
  FF-0E→FF-1D (t19); FF-1E saga (t20–22/25); FF-2A-posture-redo 3-non-delivery saga CLOSED (t25);
  #2558 WITHDREW NYISO calibration-complete marker (t27, NEISO HOLDS). Rule-27 clean throughout.

Status vocabulary: `not-sent` · `sent` · `landed` · `verified-pass` ·
`verified-issues` · `correction-sent`.

---

## Session status table

| FF id | Model | Wave | Lane | Gate | Status | Evidence |
|---|---|---|---|---|---|---|
| FF-0A..FF-1F | — | 0–1 | — | — | **all verified-pass (Waves 0–1 CLOSED)** | See turns 2–25 + prior ledger commits. Rubric+scorer, 6-ISO T1-F baseline, crossover harness, benchmark-corridor, capacity-inversion fix, cold-event derate, demand/DC/hydro currency, ATB entry costs, IRA/ACP policy, DC=mid + derate=ON defaults. |
| FF-2A..FF-2A-posture-redo | — | 2 | L-CAP | — | **verified-pass** | Entry-lookahead posture ON (#2539); VRE cap-rev measurement. 3-non-delivery saga closed t25. |
| FF-2B | OPUS | 2 | L-CAP | — | **verified-pass (turn 28)** — #2582+#2589+#2591, source `96eac04` | NEISO I7+I12 PASS (Net ICR 0.1102, ER23-405-000), CAISO +3,371 MW cited (residual→FF-1C), NYISO basis-correct; Pass-1B + FIRST NEISO pair; T1-F sidecars. Bonus UNSET runner.py fix. ⚠ git-push deviation, blob-verified. |
| FF-2C | OPUS | 2 | L-CAP | — | **verified-pass (turn 34)** — #2645/#2647/#2649 | Flip {PJM,MISO,CAISO,NEISO}=ON + R4 published anchors + byte-identity coercion + tests. PJM/MISO curve hindcasts honest FAILs (routed). Wave 2 CLOSED (NYISO flip pends re-calibration). |
| FF-2C-rig | OPUS | 2 | L-CAP | — | **verified-pass (turn 35)** — #2654/#2662 | Curve-anchor scaling verified exactly 2.0×; rung-cache defect fixed; PJM T1.7a PASS monotone_down; ERCOT control clean. |
| FF-2D | OPUS | 2 | L-VAL | — | **verified-pass (turn 37)** — #2666/#2681/#2684/#2685 | T1 gate SCORED: all 6 ISOs HOLD / T2-ineligible; FC-1 structural FAIL dominant (CAISO [I3,I4,I7,I9], ERCOT [I3]) + 6 t1f baselines + 2 crossover legs on forecast-validation namespace. I4 "A1" leak dominant cross-ISO blocker; PJM+NEISO closest. Golden fixture frozen-not-regenerated (→ FF-3E). |
| FF-3A | — | 3 | L-VAL | ⛔ T2 | **WITHDRAWN-DEFERRED (owner 2026-07-19)** | T2 CERTIFICATION deferred behind §2.1b. NOTE: the T2 SCORER machinery was shaken out at T1 by FF-3G (turn 39) — only the full-horizon certified verdict is gated. |
| FF-3B | OPUS | 3 | L-CES | — | **verified-pass (turn 30)** — #2613 | W3-R = NO-GO (R1/R2 NOT MET, R3 MET, R4 partial; routed). POC = machinery-proven: 3×5yr legs, kind="ces-poc", premium moves full surface; wall/RSS ledger + nonlinear caution for FF-3E. |
| FF-3C | FABLE | 3 | L-PERF | conditional | not-sent | trigger-gated — inactive (only remaining FABLE prompt); trigger = active-tier breach (plan §6). |
| FF-3D / FF-3D-run | OPUS | 3 | L-CAP | — | **landed** (#2463 / #2471/#2473/#2478) | NYISO Option-B pairing + fixed/curve/realized pair registered. ⚠ pair evidence rule-11-tainted (pre-re-audit envelope) — regenerate before NYISO flip. |
| FF-3E | OPUS | 3 | L-VAL | ⛔ §2.1b evidence | **verified-pass (turn 39)** — #2691 | Readiness battery (`scripts/ff_readiness_battery.py`, 5 parts + test) + `run_full_horizon.py` guard `MAX_UNAUTHORIZED_SOLVE_YEARS=5` + POC close-out `docs/handoffs/ff-poc-closeout-2026-07.md` (11 sections: §2 per-ISO §2.1b scorecard, §6 wall/RSS, §8 honest-unfit absorbing FF-4B, §10 owner box). Content-verified on disk. |
| FF-3F | OPUS | 3 | L-CES | — | **verified-pass (turn 39)** — #2700/#2704/#2706 | CES infra hardening at T1. F-3 FIXED (`generate_financial_reports.py` runs on fresh checkout); premium-ladder harness + report pipeline exercised on ERCOT 2026-2030 ×{BAU,CES-20,CES-40}; premium→surface signal reproduced; forward numbers labeled STRUCTURAL, no W4 conclusions. `ff-ces-infra-t1-2026-07.md`. |
| FF-3G | OPUS | 3 | L-VAL | — | **verified-pass (turn 39)** — #2701 | T2 scorer shakeout (no solve). All 8 FC categories resolve to valid tokens on existing+synthetic bundles; §2.1b-gated instruments degrade to SKIPPED cleanly (correctly HOLDs T2); I12 mirror-constant coupling found+fixed; synthetic t2 fixture + `test_forecast_verdict_t2.py`. `ff-t2-scorer-shakeout-2026-07.md`. |
| FF-3H | OPUS | 3 | L-PB | — | **verified-pass (turn 40)** — #2722 | PB band machinery T1 exercise. Found+fixed a real gap: `ensemble._member_metric_values` hardcoded the 2026-2050 horizon → any T1 (sub-2050) ensemble crashed at aggregation; now derives horizon from run config (default byte-identical, PB-5 path unchanged) + regression tests. Real 5-draw ERCOT 2026-2030 fan emits bands + publishes `ercot-pb-bands-t1`; sampler seeded/reproducible, percentiles exactly HF7, n=5 disclosed as machinery-proof-not-forecast. ≤5-yr cap held (25 solve-yr, 29s/yr). Worker hit+fixed a base64 blob-verify catch (chunked). `ff-pb-bands-t1-2026-07.md`. |
| FF-5A | OPUS | 5 | L-DASH | — | **verified-pass (turn 39)** — #2703/#2708/#2710/#2713/#2715/#2717 | `register_forecast_run.py` = migrated ONE registration entry point (hindcast/baseline delegate, sidecars work, separate from CI-gated backcast registry); `forecast-runs.html` explorer + `forecast-status.html` status page (surfaces HOLD + honest-unfit truthfully). Active-wave build-out COMPLETE. |
| FF-4A | — | 4 | L-VAL | ⛔ | **WITHDRAWN (owner 2026-07-19)** | Prompt withdrawn outright; Wave 4 full-horizon campaign deferred behind §2.1b. Do not restore from history. |
| FF-4B | — | 4 | L-VAL | — | **WITHDRAWN-DEFERRED (owner 2026-07-19)** | Honest-unfit list delivered by FF-3E close-out; rest re-authored at gate-open. |
| FF-4C | — | 4 | L-VAL | owner-gated | **WITHDRAWN-DEFERRED (owner 2026-07-19)** | PB-5 full-horizon band RUN deferred (§2.1b). NOTE: PB band MACHINERY exercised at T1 by FF-3H (verified-pass t40) — only the full-horizon certified bands are gated. |

---

## Owner decisions

**Received:**
- **D1 = B (R-NEW)** (2026-07-18). Capacity-market flips: ON for PJM/MISO/NYISO/NEISO/CAISO (all but
  ERCOT); NYISO R5a = Option B; datacenter_load_path = mid; correlated_forced_outage = ON;
  entry-lookahead posture = ON. (turns 12–18; all executed.)
- **POC-first re-scope (2026-07-19):** Wave-4 prompts WITHDRAWN, FF-3A/T2 deferred, ≤5-solve-year
  cap, §2.1b gate installed; FF-3B re-scoped; FF-3E chartered. Golden freeze hardened into prompt
  withdrawal. Plan amended in place.
- **FF-2C flip sign-off (turn 31):** delegated to manager — APPROVED PJM/MISO/CAISO/NEISO, NYISO
  DEFERRED. EXECUTED + verified-pass turn 34 — Wave 2 closed.
- **“Just build the infrastructure” (turn 38-39, 2026-07-21):** §2.1b gates full 25-yr SOLVES only,
  NOT infrastructure. Deferred waves re-scoped — T1-scale infra halves dispatchable now (FF-3F/3G/3H
  chartered + FF-5A); only the full-horizon campaign RUNS stay gated. Manager corrected its prior
  “later waves blocked” framing. **ALL FOUR T1-infra prompts + FF-3E now verified-pass (t40).**

**RESOLVED (owner, turns 38–40):**
- **Key-rotation verification (#2659/#2660) — CLOSED, no action.** Keys are public/free-tier.
- **FF-2B git-push exception — BLESSED.** Narrow “small source-only `git push` + mandatory
  blob-verify” fallback for `push_files` large-file corruption; last-resort, blob-verify mandatory.
- **NEISO — HOLD, do nothing (t38); hold-scope question CLOSED (t40, owner: out of manager scope,
  do not track).** No FF holdout-equivalency sign-off / FF NEISO work until owner reopens;
  out-of-program backcast-calibration lanes are not the manager's concern.
- **Stray file cleanup — DONE turn 38** (`.constants_push_stage.txt` deleted, `e87216e`).

**AWAITING (each changes what I dispatch next):**
- **§2.1b gate-open per ISO** — NOT authorized (owner: “not running full solves yet”). FF-3E's
  closeout scorecard is the standing evidence; PJM/NEISO closest (I4 “A1” leak sole blocker).
  Re-surface only when owner initiates.
- **(nothing dispatchable at T1)** — all four T1-infra prompts landed verified-pass (FF-3E/5A/3F/3G/3H).
  The only remaining work is §2.1b-gated full-horizon campaigns (CES 2026-2050 ladder, PB-5 full
  bands, T2/T3 certification), which stay behind the owner-held gate. FF-3C trigger-gated inactive.

---

## Corrections issued

1–12 (turns 2–35) — all RESOLVED/RETRACTED. Key: FF-0A-fix (#2419), FF-0B-redo (#2517),
   FF-1A-restore/C/C2 (#2438/#2448/#2454), FF-2A-integrate (#2486), FF-3D-run (#2471),
   FF-1E-complete RETRACTED (#2518), FF-2A-posture-redo (#2539, 3-non-delivery saga closed),
   FF-1E-policy (#2535+#2540), FF-2C-rig (#2654/#2662). Genuine non-deliveries total 3
   (FF-0B #2412, FF-2A #2453, FF-2A-posture #2522). Full detail in prior ledger commits.

---

## Turn log

- **turns 1–36 (collapsed — see prior ledger commits + the turn entries above for detail).** Waves 0/1
  dispatch+verify; capacity.py truncation saga restored (t7/t15); FF-0F closed (t17); posture=ON
  (t18/25); FF-1E saga (t20–25); NYISO marker withdrawn (t27); FF-2B verified-pass (t28); FF-3B
  verified-pass (t30); FF-2C flip delegated+executed (t31/34) — Wave 2 CLOSED; FF-2C-rig (t35);
  FF-2D in flight (t35). turn 36 verified FF-2D but its ledger push never reached origin.
- **turn 37 (`→f49cf768`).** Re-applied lost turn 36: **FF-2D verified-pass** (#2666/#2681/#2684/#2685),
  all 6 ISOs HOLD; **FF-3E dispatched**; rule-27 baseline moved to constants.py facade split.
- **turn 38 (`→b6ace721`).** **FF-3E LANDED (#2691).** Owner decisions recorded: §2.1b NOT authorized;
  keys public; FF-2B exception blessed; NEISO hold; stray file deleted (`e87216e`).
- **turn 39 (`→08c831c9`).** **Active-wave build-out COMPLETE.** FF-3E + FF-5A + FF-3F + FF-3G all
  verified-pass (content-checked on disk); FF-3H sent-not-launched. Owner re-scope: “just build the
  infrastructure” — §2.1b gates full solves only, T1-infra halves dispatchable now. Rule-27 baseline
  moved again: capacity.py 4269→32 facade + `capacity_evolution/` package (verified legit, pinned by
  `test_capacity_evolution_facade.py`); data/fuel/ package split (watch-set fuel_trajectories.py
  unchanged). 26 merges, ~18 out-of-program.
- **turn 40 (`→cf306c95`).** **FF-3H verified-pass (#2722) — the T1 INFRASTRUCTURE PROGRAM IS
  COMPLETE.** All four re-scoped T1-infra prompts (FF-5A/3F/3G/3H) + FF-3E landed verified-pass.
  FF-3H found+fixed a real horizon-hardcode gap in `ensemble.py` (T1 ensembles crashed at
  aggregation; default byte-identical) + published `ercot-pb-bands-t1`; n=5 disclosed as
  machinery-proof. Rule-27 clean this batch: #2721 (fuel goldens only), #2723 (ff-g3 net-CONE fix —
  capacity_market +111 / scenarios +51 / constants +2, all GROWTH). Out-of-program: #2721, #2723
  (G-series lane), + dashboard band-payload uploads (FF-3H). NEISO hold-scope question CLOSED
  (owner: out of manager scope). Nothing dispatchable at T1 — only §2.1b-gated full campaigns
  remain (owner holding). `git fetch` was timing out; verified via GitHub API.
- **turn 41 (manager `ff-wave-manager-standing-e90gfj`, NEW session — clean refresh. `cf306c95→3cbf5b16`,
  3 merges + direct commits). NO FF work landed; nothing dispatchable; program AT REST.** FIRST-ACTION
  check: ledger on main confirmed at turn-40 state (last-reviewed `cf306c95`, FF-3H verified-pass) —
  turn-40 push merged via #2724, proceeded. **Merges since (all OUT-OF-PROGRAM backcast lanes, none FF):**
  #2724 (turn-40 ledger, our own); #2725 (nyiso-downstate-reserve-scarcity — NYISO keeper json + registry
  sidecar, +16/-1); #2726 (caiso-110 endogenous-wecc-west-zone — 4 NEW files: `data/wecc_west_fleet.py`
  + tests + probes, +531/-0). Direct-to-main commits: nyiso-69 keeper promotion (`cbea16e8`, dashboard
  metadata) + caiso-110 fleet builder commits (`86b60dcc`/`70ad5f0f`). All are default-off/additive
  backcast-calibration work — no FF solve/score/flip. **RULE-27 CLEAN:** no watch-set source file
  touched or shrunk; #2726 all-additive new files, #2725 json-only. Watch set unchanged (capacity.py-facade
  32 + capacity_evolution/ package · scenarios.py 8102 · constants.py-facade 2422 · runner.py 2470 ·
  fuel_trajectories 1050 · capacity_market 2392 · ercot_envelopes 1960). **Nothing dispatchable** — all
  T1 infra verified-pass, §2.1b gate held by owner (“not running full solves yet”), FF-3C trigger-gated
  inactive, Wave-4/T2/T3/CES-W4/PB-5 WITHDRAWN-DEFERRED. Program intentionally at rest pending an owner
  gate-open. `git fetch` still timing out; reviewed via GitHub API.
