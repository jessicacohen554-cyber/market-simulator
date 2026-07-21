# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `71a610ca` (2026-07-21, turn 42 — manager session `ff-wave-manager-standing-e90gfj`).
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
  PR text):** (1) **FF-3E verified-pass** (#2691); (2) **FF-5A verified-pass** (#2703/#2708/#2710/
  #2713/#2715/#2717); (3) **FF-3F verified-pass** (#2700/#2704/#2706); (4) **FF-3G verified-pass**
  (#2701). **FF-3H (PB bands T1) = sent, NOT launched** at t39. **RULE-27 BASELINE MOVED
  (verified, NOT truncation):** `model/capacity.py` 4269→**32-line facade** aliasing the new
  `model/capacity_evolution/` package (retirements 1753 / new_entry 1225 / evolve 722 / ccs 407 /
  adequacy 361 / __init__ 285), pinned by `tests/test_capacity_evolution_facade.py`; `data/fuel/`
  package split (watch-set `config/fuel_trajectories.py` unchanged, 1050). 26 merges, ~18
  out-of-program. (Full t39 detail in prior ledger commits.)
- **turn 37 (manager `ff-wave-manager-7ra116`, NEW session — re-applies lost turn 36 + full loop).
  `5b9e79c2→f49cf768` (20 merges). FF-2D LANDED VERIFIED-PASS; FF-3E DISPATCHED.** All six ISOs
  read **HOLD / T2-ineligible**, FC-1 structural FAIL dominant; I4 "A1" capacity-accounting leak
  the dominant cross-ISO blocker (PJM+NEISO closest). Dashboard on the forecast-validation
  namespace (`frontend/data/hindcast/`). **RULE-27 BASELINE MOVED (verified):** `constants.py`
  split into a re-export FACADE (2,422) + `config/fuel_trajectories.py` (1,050) /
  `config/capacity_market.py` (2,392) / `config/ercot_envelopes.py` (1,960), guarded by
  `tests/test_constants_facade.py`. (Full t37 detail in prior ledger commits.)
- **turns 30–36 (manager `turn-1-anm4jn` / `ff-wave-manager-7ra116`, collapsed).** FF-2C
  verified-pass (#2645/#2647/#2649, flip {PJM,MISO,CAISO,NEISO}=ON, Wave 2 CLOSED); FF-2C-rig
  verified-pass (#2654/#2662); FF-3B verified-pass (#2613, W3-R NO-GO + CES POC machinery-proven);
  FF-2D dispatched+in-flight. Rule-27 clean throughout. (Full detail in prior ledger commits.)
- **turns 10–29 (collapsed — see prior ledger commits).** Wave 0/1 dispatch + verify; capacity.py
  truncation saga restored; FF-2A integration + posture=ON; FF-1E saga; FF-2B verified-pass (#2582/
  #2589, NEISO I7+I12 PASS); NYISO calibration-complete marker WITHDRAWN (t27). Rule-27 clean.

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
- **⚠ MINOR HOUSEKEEPING (surfaced t42, not stop-the-line):** #2730 left a stray
  `scripts/_rule27_push_staging/` dir (base64-chunked tarball + MANIFEST.md) on main — a worker's
  push-staging scratch artifact, like the turn-38 `.constants_push_stage.txt`. Cleanup candidate;
  out-of-program (not the manager's file to delete). Flag to owner.

---

## Corrections issued

1–12 (turns 2–35) — all RESOLVED/RETRACTED. Key: FF-0A-fix (#2419), FF-0B-redo (#2517),
   FF-1A-restore/C/C2 (#2438/#2448/#2454), FF-2A-integrate (#2486), FF-3D-run (#2471),
   FF-1E-complete RETRACTED (#2518), FF-2A-posture-redo (#2539, 3-non-delivery saga closed),
   FF-1E-policy (#2535+#2540), FF-2C-rig (#2654/#2662). Genuine non-deliveries total 3
   (FF-0B #2412, FF-2A #2453, FF-2A-posture #2522). Full detail in prior ledger commits.

---

## Turn log

- **turns 1–38 (collapsed — see prior ledger commits + the turn entries above for detail).** Waves 0/1
  dispatch+verify; capacity.py truncation saga restored; FF-1E saga; NYISO marker withdrawn (t27);
  FF-2B verified-pass (t28); FF-3B verified-pass (t30); FF-2C flip executed (t31/34) — Wave 2 CLOSED;
  FF-2C-rig (t35); FF-2D verified-pass all-6-HOLD (t37); FF-3E dispatched (t37) + LANDED #2691 (t38);
  owner decisions recorded (t38: §2.1b NOT authorized; keys public; FF-2B exception blessed; NEISO
  hold; stray file deleted `e87216e`).
- **turn 39 (`→08c831c9`).** **Active-wave build-out COMPLETE.** FF-3E + FF-5A + FF-3F + FF-3G all
  verified-pass; FF-3H sent-not-launched. Owner re-scope: “just build the infrastructure.” Rule-27
  baseline moved: capacity.py 4269→32 facade + `capacity_evolution/` package.
- **turn 40 (`→cf306c95`).** **FF-3H verified-pass (#2722) — the T1 INFRASTRUCTURE PROGRAM IS
  COMPLETE.** All four re-scoped T1-infra prompts (FF-5A/3F/3G/3H) + FF-3E landed verified-pass.
  Rule-27 clean (#2721 goldens, #2723 growth-only). NEISO hold-scope closed. Nothing dispatchable at
  T1 — only §2.1b-gated full campaigns remain (owner holding). `git fetch` timing out; GitHub API.
- **turn 41 (`→3cbf5b16`, clean refresh).** NO FF work landed; program AT REST. 3 merges, all
  out-of-program backcast lanes: #2725 (nyiso-downstate-reserve, json-only) + #2726 (caiso-110
  endogenous-wecc-west, +531/-0 all new files) + direct commits (nyiso-69 keeper, caiso-110 fleet).
  Rule-27 clean. Ledger pushed to branch `claude/ff-wave-manager-standing-e90gfj` (`f6a2be5`).
- **turn 42 (manager `ff-wave-manager-standing-e90gfj`, refresh. `3cbf5b16→71a610ca`, 10 PRs #2729-#2738
  + ~17 direct commits). NO FF-manager work landed; nothing dispatchable; program AT REST. Large
  out-of-program INFRA-REFACTOR + forecast-input batch — RULE-27 verified CLEAN.** (turn-41 ledger
  push `f6a2be5` not yet merged to main; carried forward on branch — this turn builds on it.)
  **Two sanctioned FACADE SPLITS (same pattern as capacity.py/constants.py — verified, NOT
  truncation):** #2729 `phase-refactor/config-model-layering` — `config/interchange_config.py`
  1919→~30-line facade (content → `model/interchange/spec.py` +1924 / `__init__` +168) and
  `config/reserve_config.py` 2928→~27-line facade (→ `model/reserves/spec.py` +2932 / `__init__`
  +188); both sys.modules-alias facades preserving every historical import/monkeypatch, pinned by
  `tests/test_config_model_layering.py` (+404) + 3e-before/3e-after regression-golden manifests
  (byte gate PASS, atol=rtol=0, byte-identical dispatch across keepers caiso-102 + miso-81); massive
  shrink merged → carried CI `intentional-shrink` label (file-integrity-guard passed). #2730
  `orchestrator-unification-refactor` — pipeline.api facade + new pipeline modules (flags/api/persist/
  year/ttc/reference/report/offer_curve_base), ADDITIVE (+2831/-44), scripts rerouted through
  `pipeline.api`; lane-before/after goldens. **WATCH SET (verified untouched/unshrunk):** scenarios.py
  8102 · constants.py-facade (GREW to ~2469 via #2735 +63/-16 datacenter config, net +47) · runner.py
  2470 · capacity.py-facade 32 + capacity_evolution/ · fuel_trajectories 1050 · capacity_market 2392 ·
  ercot_envelopes 1960. **NEW facades ADDED to watch set: `model/interchange/spec.py` (1924) +
  `model/reserves/spec.py` (2932)** — future shrink of these = stop-the-line. **Out-of-program
  forecast-input lanes (owner-launched, G-series category, NOT FF-manager dispatched):** #2731
  (sced-data-ercot), #2732 (capacity-accreditation-data), #2733 (uncurtailed-hsl), #2734
  (queue-caps-citation), #2735 (datacenter-load-miso-neiso), #2737 (pjm-rps-floor), #2738
  (aeo-fuel-wiring) + #2736 (extract-resolvers-sweeps refactor) — forecast-driver wiring/data intake,
  additive, consistent with "build infra, no full solves." **⚠ MINOR HOUSEKEEPING flagged to owner:**
  stray `scripts/_rule27_push_staging/` dir left on main by #2730 (cleanup candidate, not
  stop-the-line). **Nothing dispatchable** — §2.1b gate still owner-held; FF-3C trigger-gated
  inactive; all T1 infra verified-pass. `git fetch` still timing out; reviewed via GitHub API.
