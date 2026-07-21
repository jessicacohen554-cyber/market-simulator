# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `fe1fe5ce` (2026-07-21, turn 43 — manager session `ff-wave-manager-standing-e90gfj`).
- **Plan base SHA:** `c95176e` (amended in place 2026-07-19 — POC-first re-scope, see directive entry below).
- **OWNER DIRECTIVE (2026-07-19, out-of-band — recorded by the directive's executing
  session, not a manager turn): POC-first re-scope of THE PLAN.** The plan is amended in
  place (§0 two-phase framing, new §2.1b full-solve authorization gate, §6 Waves 3–4
  re-cut): **FF-4A/FF-4B/FF-4C prompts WITHDRAWN** — Wave 4 deferred in full; the
  turn-18 "golden freeze HELD" hardens into outright prompt withdrawal (never restore
  from history). **FF-3A (T2) deferred with its tier** (prompt withdrawn). **FF-3B
  re-scoped** — W3-R readiness + a T1-scale (ERCOT 2026–2030) CES POC only. **FF-3E
  [OPUS] chartered** (full-solve readiness battery + POC close-out). Hard cap: **≤5
  solve-years per invocation, program-wide**. Long solves reopen per ISO only through
  §2.1b: backcast keeper + calibration-complete marker, T1 POC gates green, crossover
  input gap + readiness battery + projected cost, and an explicit per-campaign owner
  authorization.
- **turn 42 (`3cbf5b16→71a610ca`).** NO FF-manager work; program AT REST. Big out-of-program
  infra-refactor + forecast-input batch, RULE-27 CLEAN. **Two sanctioned FACADE SPLITS (verified,
  NOT truncation):** #2729 `config/interchange_config.py` 1919→~30 facade (→ `model/interchange/
  spec.py` 1924) + `config/reserve_config.py` 2928→~27 facade (→ `model/reserves/spec.py` 2932),
  pinned by `tests/test_config_model_layering.py` + byte-identical regression goldens + CI
  `intentional-shrink`; #2730 orchestrator-unification pipeline.api facade (ADDITIVE). **NEW
  facades ADDED to watch set: `model/interchange/spec.py` (1924) + `model/reserves/spec.py`
  (2932).** Forecast-input lanes (#2731-#2738, G-series category) additive. Flagged stray
  `scripts/_rule27_push_staging/` dir. (Full t42 detail in prior ledger commit `df13a4e`.)
- **turn 41 (`3cbf5b16`).** Clean refresh; 3 out-of-program backcast merges (#2725 nyiso-reserve,
  #2726 caiso-110 wecc-west, +nyiso-69/caiso-110 direct). Rule-27 clean. (Ledger `f6a2be5`.)
- **turn 40 (`cf306c95`).** **FF-3H verified-pass (#2722) — T1 INFRASTRUCTURE PROGRAM COMPLETE.**
  All four T1-infra prompts (FF-5A/3F/3G/3H) + FF-3E verified-pass. Nothing dispatchable at T1.
- **turn 39 (`08c831c9`).** Active-wave build-out COMPLETE (FF-3E/5A/3F/3G verified-pass). Owner
  re-scope "just build the infrastructure." capacity.py→32 facade + `capacity_evolution/` package.
- **turn 37-38 (`f49cf768`→`b6ace721`).** FF-2D verified-pass (all 6 ISOs HOLD, I4 "A1" leak
  dominant blocker; PJM+NEISO closest); FF-3E dispatched+LANDED (#2691). constants.py→facade split.
- **turns 10–36 (collapsed — see prior ledger commits).** Waves 0/1 CLOSED; FF-2A posture=ON;
  FF-2B verified-pass (#2582, NEISO I7+I12 PASS); FF-2C flip {PJM,MISO,CAISO,NEISO}=ON — Wave 2
  CLOSED; FF-2C-rig; FF-3B verified-pass (W3-R NO-GO + CES POC); NYISO marker WITHDRAWN (t27).

Status vocabulary: `not-sent` · `sent` · `landed` · `verified-pass` ·
`verified-issues` · `correction-sent`.

---

## Session status table

| FF id | Model | Wave | Lane | Gate | Status | Evidence |
|---|---|---|---|---|---|---|
| FF-0A..FF-1F | — | 0–1 | — | — | **all verified-pass (Waves 0–1 CLOSED)** | Rubric+scorer, 6-ISO T1-F baseline, crossover harness, benchmark-corridor, capacity-inversion fix, cold-event derate, demand/DC/hydro currency, ATB entry costs, IRA/ACP policy, DC=mid + derate=ON defaults. |
| FF-2A..FF-2A-posture-redo | — | 2 | L-CAP | — | **verified-pass** | Entry-lookahead posture ON (#2539); VRE cap-rev measurement. |
| FF-2B | OPUS | 2 | L-CAP | — | **verified-pass (t28)** — #2582+#2589+#2591 | NEISO I7+I12 PASS (Net ICR 0.1102, ER23-405-000), CAISO +3,371 MW cited (→FF-1C), NYISO basis-correct; first NEISO pair. ⚠ git-push deviation, blob-verified. |
| FF-2C | OPUS | 2 | L-CAP | — | **verified-pass (t34)** — #2645/#2647/#2649 | Flip {PJM,MISO,CAISO,NEISO}=ON + R4 anchors + byte-identity + tests. Wave 2 CLOSED (NYISO flip pends re-calibration). |
| FF-2C-rig | OPUS | 2 | L-CAP | — | **verified-pass (t35)** — #2654/#2662 | Curve-anchor scaling verified exactly 2.0×; rung-cache defect fixed; PJM T1.7a PASS. |
| FF-2D | OPUS | 2 | L-VAL | — | **verified-pass (t37)** — #2666/#2681/#2684/#2685 | T1 gate SCORED: all 6 ISOs HOLD / T2-ineligible; FC-1 structural FAIL dominant. I4 "A1" leak dominant cross-ISO blocker; PJM+NEISO closest. |
| FF-3A | — | 3 | L-VAL | ⛔ T2 | **WITHDRAWN-DEFERRED (owner 2026-07-19)** | T2 CERTIFICATION deferred behind §2.1b. T2 SCORER machinery shaken out at T1 by FF-3G. |
| FF-3B | OPUS | 3 | L-CES | — | **verified-pass (t30)** — #2613 | W3-R = NO-GO (R1/R2 NOT MET; routed). POC machinery-proven 3×5yr, premium moves full surface. |
| FF-3C | FABLE | 3 | L-PERF | conditional | not-sent | trigger-gated — inactive (only remaining FABLE prompt); trigger = active-tier breach (plan §6). |
| FF-3D / FF-3D-run | OPUS | 3 | L-CAP | — | **landed** (#2463 / #2471/#2473/#2478) | NYISO Option-B pairing registered. ⚠ pair evidence rule-11-tainted (pre-re-audit) — regenerate before NYISO flip. |
| FF-3E | OPUS | 3 | L-VAL | ⛔ §2.1b evidence | **verified-pass (t39)** — #2691 | Readiness battery (`scripts/ff_readiness_battery.py`, 5 parts + test) + `run_full_horizon.py` guard `MAX_UNAUTHORIZED_SOLVE_YEARS=5` + POC close-out `docs/handoffs/ff-poc-closeout-2026-07.md` (11 sections). |
| FF-3F | OPUS | 3 | L-CES | — | **verified-pass (t39)** — #2700/#2704/#2706 | CES infra hardening at T1. F-3 FIXED; premium-ladder harness exercised ERCOT 2026-2030 ×{BAU,CES-20,CES-40}; forward numbers labeled STRUCTURAL. |
| FF-3G | OPUS | 3 | L-VAL | — | **verified-pass (t39)** — #2701 | T2 scorer shakeout (no solve). All 8 FC categories resolve; §2.1b-gated instruments degrade to SKIPPED (correctly HOLDs T2); I12 coupling found+fixed. |
| FF-3H | OPUS | 3 | L-PB | — | **verified-pass (t40)** — #2722 | PB band machinery T1. Found+fixed `ensemble._member_metric_values` horizon-hardcode (T1 ensembles crashed; default byte-identical) + regression tests; published `ercot-pb-bands-t1`; n=5 disclosed machinery-proof. |
| FF-5A | OPUS | 5 | L-DASH | — | **verified-pass (t39)** — #2703/#2708/#2710/#2713/#2715/#2717 | `register_forecast_run.py` = migrated ONE entry point (separate from CI-gated backcast registry); `forecast-runs.html` + `forecast-status.html` (HOLD + honest-unfit truthful). |
| FF-4A | — | 4 | L-VAL | ⛔ | **WITHDRAWN (owner 2026-07-19)** | Prompt withdrawn outright; Wave 4 deferred behind §2.1b. Do not restore from history. |
| FF-4B | — | 4 | L-VAL | — | **WITHDRAWN-DEFERRED (owner 2026-07-19)** | Honest-unfit list delivered by FF-3E close-out. |
| FF-4C | — | 4 | L-VAL | owner-gated | **WITHDRAWN-DEFERRED (owner 2026-07-19)** | PB-5 full-horizon band RUN deferred (§2.1b). MACHINERY exercised at T1 by FF-3H. |

---

## Owner decisions

**Received:**
- **D1 = B (R-NEW)** (2026-07-18). Capacity-market flips ON for PJM/MISO/NYISO/NEISO/CAISO (all but
  ERCOT); NYISO R5a = Option B; datacenter_load_path = mid; correlated_forced_outage = ON;
  entry-lookahead posture = ON. (Executed.)
- **POC-first re-scope (2026-07-19):** Wave-4 WITHDRAWN, FF-3A/T2 deferred, ≤5-solve-year cap,
  §2.1b gate installed; FF-3B re-scoped; FF-3E chartered.
- **FF-2C flip sign-off (t31):** APPROVED PJM/MISO/CAISO/NEISO, NYISO DEFERRED. Executed t34.
- **“Just build the infrastructure” (t38-39):** §2.1b gates full 25-yr SOLVES only, NOT
  infrastructure. T1-infra halves dispatchable now; only full-horizon campaign RUNS stay gated.
  **ALL FOUR T1-infra prompts + FF-3E verified-pass (t40).**

**RESOLVED (owner, turns 38–40):**
- **Key-rotation (#2659/#2660) — CLOSED.** Keys public/free-tier.
- **FF-2B git-push exception — BLESSED** (narrow last-resort, blob-verify mandatory).
- **NEISO — HOLD; hold-scope CLOSED (t40, owner: out of manager scope, do not track).**
- **Stray file cleanup (t38)** — `.constants_push_stage.txt` deleted (`e87216e`).

**AWAITING (each changes what I dispatch next):**
- **§2.1b gate-open per ISO** — NOT authorized (owner: “not running full solves yet”). FF-3E's
  closeout scorecard is the standing evidence; PJM/NEISO closest (I4 “A1” leak sole blocker).
  Re-surface only when owner initiates.
- **(nothing dispatchable at T1)** — all T1-infra prompts verified-pass. Only §2.1b-gated
  full-horizon campaigns remain (owner-held). FF-3C trigger-gated inactive.
- **⚠ HOUSEKEEPING / infra-friction flags to owner (surfaced t43 — out-of-program, not stop-the-line):**
  (1) `scripts/_rule27_push_staging/` has BLOATED — the orchestrator-unification worker (session
  01DoiBA8) is committing a base64-chunked `rule27-bigfiles.tar.gz` across dozens of 1-line files
  (parts 03–08, ×00–09 sub-pieces + retries) via #2751/#2752/#2753/#2755. Push-scaffolding clutter,
  NOT a truncation (no source touched), but the dir should be cleaned once that refactor lands.
  (2) PJM M-3 gas-bridge (#2756) landed as an **UNAPPLIED** `docs/handoffs/pjm-m3-gas-bridge.patch`
  (836 lines) + status doc — mechanism is NOT in main; the authoring session ran on a 1572-commit-
  stale clone (066fb98) and couldn't sync (proxy disconnects) or push (413), so it left a stale-based
  patch needing re-basing by a fresh working-clone session. Stranded out-of-program PJM deliverable.
  (3) Recurring STALE-CLONE / proxy friction — multiple worker sessions (013PAHQQ, 01DoiBA8) and this
  manager are on stale clones with `git fetch` disconnecting + `git push` 413ing. Environment issue
  the owner may want to address (fresh working-clones for large-file sessions).

---

## Corrections issued

1–12 (turns 2–35) — all RESOLVED/RETRACTED. Genuine non-deliveries total 3 (FF-0B #2412, FF-2A
   #2453, FF-2A-posture #2522). Full detail in prior ledger commits.

---

## Turn log

- **turns 1–40 (collapsed — see prior ledger commits + entries above).** Waves 0/1 CLOSED; FF-2B/2C/
  2C-rig/2D verified-pass (Wave 2 CLOSED, all 6 ISOs HOLD); FF-3B verified-pass; FF-3E/5A/3F/3G/3H
  all verified-pass by t40 — **T1 INFRASTRUCTURE PROGRAM COMPLETE.** Rule-27 baselines moved via
  sanctioned facade splits (capacity.py, constants.py).
- **turn 41 (`→3cbf5b16`, clean refresh).** NO FF work; 3 out-of-program backcast merges. Ledger
  `f6a2be5`.
- **turn 42 (`→71a610ca`, refresh).** NO FF-manager work; RULE-27 CLEAN. Two sanctioned facade
  splits (#2729 interchange/reserve → model/ packages) + #2730 orchestrator-unification (additive) +
  forecast-input lanes #2731-#2738. NEW watch-set facades: interchange/spec, reserves/spec. Ledger
  `df13a4e`.
- **turn 43 (manager `ff-wave-manager-standing-e90gfj`, refresh. `71a610ca→fe1fe5ce`, 8 PRs #2749-#2756
  + ~20 direct commits). NO FF-manager work landed; nothing dispatchable; program AT REST. All
  out-of-program (backcast calibration + orchestrator refactor) — RULE-27 verified CLEAN.** (turn-42
  ledger `df13a4e` not yet merged to main; carried forward on branch.) **Merges/commits classified:**
  #2751/#2752/#2753/#2755 orchestrator-unification — touch ONLY `scripts/_rule27_push_staging/`
  (base64 tarball chunks, NO source); #2756 pjm-frontier-readiness — adds an UNAPPLIED
  `pjm-m3-gas-bridge.patch` (836L) + data json + doc (PJM M-3 mechanism NOT in main); #2754 ERCOT-94
  (season offer wall REJECTED as 2023-summer lever — real lane is ORDC/reserve scarcity-tail per
  ERCOT-95 handoff; calibration log + MEASURE probe, keeper unchanged, no solve); #2749 caiso-
  calibration-gaps + caiso-111 log (keeper caiso-102 unchanged); #2750 nyiso-calibration-scarcity;
  85eb73ff NYISO import tranches measured Q-Q derivation (rule-14, `model/interchange/spec.py`
  +55/-20 = **net GROWTH** on the t42 watch-set facade — no shrink); 6d8c1e1a fixed the nyiso-69
  PHANTOM keeper (re-pointed 69→68, dropped payload-less sidecar — the phantom I noted t41, now
  self-corrected). **RULE-27 CLEAN:** no watch-set file shrank; scenarios.py 8102 · constants.py-
  facade · runner.py 2470 · capacity.py-facade+package · fuel_trajectories 1050 · capacity_market
  2392 · ercot_envelopes 1960 · interchange/spec (grew) · reserves/spec — all intact. **THREE
  housekeeping/infra-friction flags surfaced to owner** (staging-dir bloat, stranded PJM M-3
  unapplied-patch, recurring stale-clone/proxy friction — see AWAITING §). **Nothing dispatchable** —
  §2.1b gate owner-held; FF-3C trigger-gated inactive; all T1 infra verified-pass. `git fetch` still
  timing out; reviewed via GitHub API.
