# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `22cfd56a` (2026-07-22, turn 44 — manager session `ff-wave-manager-standing-atbiwx`).
- **Plan base SHA:** `c95176e` (amended in place 2026-07-19 — POC-first re-scope, see directive entry below).
- **Watch-set path prefix (confirmed t44):** source lives under `src/market_sim/` (e.g.
  `src/market_sim/config/scenarios.py`, `src/market_sim/model/reserves/spec.py`).
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
- **turn 43 (`71a610ca→fe1fe5ce`).** NO FF-manager work; program AT REST. 8 PRs #2749-#2756 +
  ~20 direct commits, all out-of-program (backcast calibration + orchestrator refactor), RULE-27
  CLEAN. Raised THREE housekeeping/infra-friction flags (staging-dir bloat, stranded PJM M-3
  patch, stale-clone/proxy friction). (Ledger `b7ea783`; stack `f6a2be5`/t41 → `df13a4e`/t42 →
  `b7ea783`/t43 all merged to main by t44.)
- **turns 40–42 (collapsed).** t40: FF-3H verified-pass (#2722) — **T1 INFRASTRUCTURE PROGRAM
  COMPLETE**, all four T1-infra prompts + FF-3E verified-pass. t41: clean refresh, 3 backcast
  merges. t42: RULE-27 CLEAN, two sanctioned FACADE splits (#2729 interchange/reserve →
  `model/interchange/spec.py` 1924 + `model/reserves/spec.py` 2932, added to watch set) + #2730
  orchestrator-unification (additive) + forecast-input G-series lanes. (Ledger commits `cf306c95`
  / `f6a2be5` / `df13a4e`.)
- **turns 37–39 (collapsed).** FF-2D verified-pass (all 6 ISOs HOLD, I4 "A1" leak dominant
  blocker; PJM+NEISO closest). Active-wave build-out COMPLETE (FF-3E/5A/3F/3G verified-pass).
  Owner re-scope "just build the infrastructure." capacity.py→32 facade + `capacity_evolution/`
  package; constants.py→facade split.
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

**RESOLVED (owner, turns 38–44):**
- **Key-rotation (#2659/#2660) — CLOSED.** Keys public/free-tier.
- **FF-2B git-push exception — BLESSED** (narrow last-resort, blob-verify mandatory).
- **NEISO — HOLD; hold-scope CLOSED (t40, owner: out of manager scope, do not track).**
- **Stray file cleanup (t38)** — `.constants_push_stage.txt` deleted (`e87216e`).
- **Staging-dir bloat [t43 flag 1] — RESOLVED (t44).** `scripts/_rule27_push_staging/` no longer
  exists on main (owner-ordered bloat purge, `07fee6e`). Cleaned.
- **Stale-clone/proxy friction [t43 flag 3] — OWNER ADDRESSING (t44).** SessionStart blobless
  fast-forward hook (`f72db66`) + `cleanup-large-blobs.yml` workflow (owner-direct) + repo bloat
  purge + ERCOT parquet slimming + gitignore hardening (#2775/#2777). ERCOT lane also reports
  "small git pushes proven" (413 is pack-size-dependent). Watch for residual friction; no manager
  action.

**AWAITING (each changes what I dispatch next):**
- **§2.1b gate-open per ISO** — NOT authorized (owner: “not running full solves yet”). FF-3E's
  closeout scorecard is the standing evidence; PJM/NEISO closest (I4 “A1” leak sole blocker).
  Re-surface only when owner initiates.
- **(nothing dispatchable at T1)** — all T1-infra prompts verified-pass. Only §2.1b-gated
  full-horizon campaigns remain (owner-held). FF-3C trigger-gated inactive.
- **⚠ HOUSEKEEPING flag still open (out-of-program, not stop-the-line):**
  (2) PJM M-3 gas-bridge (#2756) — `docs/handoffs/pjm-m3-gas-bridge.patch` (836L) remains an
  UNAPPLIED stale-based patch; the M-3 mechanism is NOT in main. Needs a fresh working-clone
  session to re-base + apply. With "small git pushes proven" this is now more tractable, but not
  yet done. Out-of-program PJM deliverable; keep visible.

---

## Corrections issued

1–12 (turns 2–35) — all RESOLVED/RETRACTED. Genuine non-deliveries total 3 (FF-0B #2412, FF-2A
   #2453, FF-2A-posture #2522). Full detail in prior ledger commits.

---

## Turn log

- **turns 1–40 (collapsed — see prior ledger commits + header entries).** Waves 0/1 CLOSED; FF-2B/
  2C/2C-rig/2D verified-pass (Wave 2 CLOSED, all 6 ISOs HOLD); FF-3B verified-pass; FF-3E/5A/3F/3G/3H
  all verified-pass by t40 — **T1 INFRASTRUCTURE PROGRAM COMPLETE.**
- **turns 41–43 (collapsed — three consecutive clean refreshes).** NO FF-manager work; program AT
  REST; RULE-27 CLEAN throughout. Out-of-program: backcast calibration lanes + two sanctioned facade
  splits (interchange/reserve → model/ packages, t42) + orchestrator-unification refactor + G-series
  forecast-input lanes. t43 raised three housekeeping flags. Ledger stack `f6a2be5`→`df13a4e`→
  `b7ea783`, all merged to main by t44.
- **turn 44 (`fe1fe5ce→22cfd56a`, refresh. NO FF-manager work landed; nothing dispatchable; program
  AT REST. All out-of-program — RULE-27 CLEAN.)** Reviewed ~40 commits since t43 HEAD, all
  out-of-program: (a) **owner-ordered repo bloat purge** (`07fee6e`: SCED corpus + monthly parts +
  zero-consumer DAM members + pre-7/14 calibration bundles/payloads deleted; findings .md kept, 35
  in-bundle findings restored `9d62252`) + ERCOT DAM disclosure parquet slimming (Fable, byte-
  identical derive verified) + `slim_ercot_dam_disclosure.py`; (b) **owner infra for stale-clone
  fix** — SessionStart blobless fast-forward hook (`f72db66`) + `cleanup-large-blobs.yml` workflow
  (owner-direct, 3 commits) + gitignore hardening (#2775/#2777); (c) **backcast calibration** —
  ERCOT-96 dam-hourly-grain keeper promotion (#2776/#2778/#2779/#2780, owner-promoted) + ERCOT-97
  charter; NYISO lever-3 hydro-reserve (#2781/#2782, nyiso-69 candidate NOT-YET, keeper nyiso-68
  unchanged); CAISO-113 L1a′ export-leg bound (#2783/#2784, B = REJECTED probe, keeper caiso-102
  unchanged). **RULE-27 CLEAN:** the only source-touching commit is NYISO lever-3 (`0375810`) —
  `config/scenarios.py` +23 / `model/reserves/spec.py` +13, ADDITIONS-ONLY gated flag
  `nyiso_hydro_reserve_eligible` (default-off) → GROWTH, no watch-set shrink. CAISO-113 source
  changes shipped as an UNAPPLIED patch (`caiso113-l1a-prime.patch`), scenarios.py not modified by
  it. No watch-set file shrank. **Turn-43 flags: (1) staging-dir bloat RESOLVED** (dir gone via
  purge); **(3) stale-clone/proxy friction OWNER-ADDRESSED** (SessionStart hook + cleanup workflow +
  purge + slimming); **(2) PJM M-3 unapplied patch still open.** Note: owner created a new Actions
  workflow (`cleanup-large-blobs.yml`) directly — owner repo-admin, not an FF-worker action, no
  violation. `git fetch` still hangs through proxy; reviewed entirely via GitHub API. **Nothing
  dispatchable** — §2.1b gate owner-held; FF-3C trigger-gated inactive; all T1 infra verified-pass.
