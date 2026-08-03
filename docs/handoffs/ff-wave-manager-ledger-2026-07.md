# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `29a5e8eb` (2026-07-22, turn 45 — manager session `ff-wave-manager-standing-atbiwx`).
- **⚠ HISTORY REWRITE EXECUTED (turn 45, 2026-07-22).** The owner ran `cleanup-large-blobs.yml`
  to success (run `29961034978`); it force-pushed a filtered history to ALL branches. **Every
  commit SHA in this ledger from turn 44 and earlier is now ORPHANED** (content preserved, hashes
  changed). Do NOT try to resolve old SHAs against main — treat pre-`29a5e8eb` SHAs as historical
  labels only. Integrity was machine-verified in-run: main's full file manifest byte-identical
  before/after (source untouched); only superseded `data/raw/` + `results/calibration/` blob
  versions stripped. All collaborators/sessions must RE-CLONE.
- **Plan base SHA:** `c95176e` (amended in place 2026-07-19 — POC-first re-scope, see directive entry below).
- **Watch-set path prefix:** source under `src/market_sim/` (e.g. `src/market_sim/config/scenarios.py`,
  `src/market_sim/model/reserves/spec.py`). **NEW sanctioned facade (t45): `src/market_sim/model/lp/`
  package** (dispatch.py split 4/5 + facade + golden byte-gate + `tests/test_dispatch_facade.py`, #2789).
- **OWNER DIRECTIVE (2026-07-19, out-of-band): POC-first re-scope of THE PLAN.** §0 two-phase framing,
  new §2.1b full-solve authorization gate, §6 Waves 3–4 re-cut: **FF-4A/4B/4C WITHDRAWN** (Wave 4
  deferred in full; never restore from history). **FF-3A (T2) deferred** (prompt withdrawn). **FF-3B
  re-scoped** (W3-R readiness + ERCOT 2026–2030 CES POC). **FF-3E [OPUS] chartered**. Hard cap: **≤5
  solve-years per invocation, program-wide**. Long solves reopen per ISO only via §2.1b (backcast
  keeper + calibration-complete marker, T1 POC gates green, crossover gap + readiness battery +
  projected cost, and explicit per-campaign owner authorization).
- **turns 40–44 (collapsed).** t40: FF-3H verified-pass (#2722) — **T1 INFRASTRUCTURE PROGRAM
  COMPLETE**, all four T1-infra prompts + FF-3E verified-pass. t41–43: three clean refreshes (program
  AT REST, RULE-27 CLEAN; backcast calibration + interchange/reserve facade splits t42 + orchestrator
  refactor + G-series forecast-input lanes). t44: clean refresh (`fe1fe5ce→22cfd56a`); owner repo
  bloat purge + ERCOT parquet slimming + stale-clone infra; NYISO lever-3 additive gated flag
  (rule-27 clean). Full detail in prior ledger commits + the turn log below.
- **turns 10–39 (collapsed — see prior ledger commits).** Waves 0/1 CLOSED; FF-2A posture=ON; FF-2B
  verified-pass (#2582, NEISO I7+I12 PASS); FF-2C flip {PJM,MISO,CAISO,NEISO}=ON — Wave 2 CLOSED;
  FF-2C-rig; FF-2D T1 gate (all 6 ISOs HOLD, I4 "A1" leak dominant); FF-3B verified-pass; FF-3E/5A/3F/3G
  verified-pass; capacity.py + constants.py facade splits; NYISO marker WITHDRAWN (t27).

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

### WAVE FI — forward-input deep-research grounding (added 2026-08-02 by FFR-3B; audit FR-21)

These four ran 2026-07-19/20 and were never entered in this ledger; the FF plan
§6 WAVE FI table carried "prompt issued" for all of them for thirteen days. Both
are corrected together. **G4 and G5 are memo/registry-only by charter — do not
read "landed" as "mechanism implemented".**

| FF id | Model | Wave | Lane | Gate | Status | Evidence |
|---|---|---|---|---|---|---|
| FF-G1 | FABLE | FI | L-INP | — | **landed (data half 2026-07-19, engine half 2026-07-26)** | Transmission-expansion registry + gated forward-TTC channel, default off. Engine half shipped as an unapplied patch and was applied under fast-tier escalation D2 (`fast-tier-triage-2026-07-26.md` §4-D2). `docs/transmission-expansion-methodology-2026-07.md`. T1-F A/B still pending before any flip. |
| FF-G2 | OPUS | FI | L-INP | — | **landed 2026-07-20** | `ff-g2-fuel-forward-2026-07.md` + `docs/fuel-forward-methodology-2026-07.md`. AEO2025→AEO2026 bump + STEO/strip triangulation. Its near-term-blend owner box was decided **D-4 = OPTION A (status quo, pure AEO)**, 2026-08-02. |
| FF-G3 | OPUS | FI | L-CAP | — | **landed 2026-07-20** | `ff-g3-net-cone-forward-2026-07.md` + `docs/capacity-price-forward-methodology-2026-07.md`. Its owner box became **D-3**: (b) 0.0 REAL CENTRAL and (c) vintage intake AUTHORIZED, signed 2026-08-02; **(a) forward-evolution mode still DEFERRED** (condition discharged by FFR-2E, not re-put). Currency follow-up FFR-2C. |
| FF-G4 | FABLE/OPUS | FI | L-INP | — | **landed 2026-07-20 — MEMO ONLY** | `ff-g4-load-shape-design-memo-2026-07.md`. No code, no default, by charter. The implementing session (audit §4 Phase 5, FR-16 "memo→code, NEISO→PJM first") is **NOT run**. |
| FF-G5 | OPUS | FI | L-INP | — | **landed 2026-07-20 — REGISTRY + MEMO ONLY** | `ff-g5-nuclear-registry-2026-07.md` + `docs/nuclear-fleet-forward-methodology-2026-07.md`; new datatype `nuclear-license-status`. **No mechanism code, no ScenarioConfig field.** Consuming it is FR-18/BLK-9, open. |

### FFR — forecast-readiness remediation program (added 2026-08-02 by FFR-3B)

Chartered by `docs/forecast-readiness-audit-2026-07.md` §4 and dispatched from
`docs/forecast-readiness-prompt-pack-2026-07.md`. Its waves are numbered
independently of the FF waves above.

| FFR id | Model | Wave | Lane | Gate | Status | Evidence |
|---|---|---|---|---|---|---|
| FFR-PA | — | P | L-INP | — | **landed 2026-07-31** | `ffr-pa-confirmed-retirements-refresh-2026-07-31.md` — confirmed-retirements registry re-query + Eddystone §202(c) adjudication. |
| FFR-PB | — | P | L-INP | — | **landed 2026-07-31** | `ffr-pb-atb-statute-intake-2026-07-31.md` — ATB intake landed as **v4.0.0 (there is no 2025/2026 edition)**; §45Y/48E closed against primary statute, values unchanged. What remains is the FFR-SC **re-derive**, not an intake. |
| FFR-1A | FABLE | 1 | L-CAP | — | **landed 2026-07-31** | `ffr-1a-confirmed-exit-accounting-2026-07-31.md` — closes FR-1/FR-2/FR-13; `confirmed_derates` rows now WRITTEN (the RC-1B schema previously had no writer). |
| FFR-1B | FABLE | 1 | L-SCAR | — | **landed 2026-08-01** | `ffr-1b-solve-year-availability-2026-08-01.md` — solve-year availability; measured events stay backcast-side. |
| FFR-1C | — | 1 | L-CAP | — | **landed 2026-07-31** | `ffr-1c-hydro-accreditation-2026-07-31.md` — closes FR-3: hydro enters `accredited_firm_capacity_mw` at published class factors. **I7 still FAILs in CAISO/MISO/NYISO** — residual filed, not closed. Findings **F-5** (`firm_clean_mw` display seam) and **F-6** (year threading) routed to FFR-3B. |
| FFR-1D | OPUS | 1 | L-VAL | — | **landed 2026-07-31** | `ffr-1d-enforcement-wave-2026-07-31.md` — enforcement wave (FR-24 CI wiring, the golden staleness waiver, forecast namespaces added to the CI path filters). |
| FFR-1E | — | 1 | L-VAL | — | **landed 2026-07-31** | `ffr-1e-forecast-parity-check-2026-07-31.md` — FR-22 standing backcast→forecast parity check + registry + the eight gaps it found. CI job landed at §W1-X. |
| FFR-§W1-X | — | 1 | — | — | **landed 2026-08-02 — WAVE 1 CLOSED** | `ffr-w1x-wave1-close-2026-08-02.md` — attestations, the single cache-epoch bump, the held parity CI job. **The epoch bump is why every pre-2026-07-31 forecast leg is a pre-epoch solve.** |
| FFR-2A | OPUS | 2 | L-VAL | — | **landed 2026-08-02 — WAVE 2 CLOSED** | `ffr-2a-crossover-seam-2026-08-02.md` — FR-9 fixed at call site + seam (`resolve_gas_scenario_path`, hold-flat) with the leakage guard extended; the MISO seam-KeyError hypothesis **REFUTED** (real but unreachable — `reference_price_interface` stays False in MISO's crossover config; the run simply never finished in-session); the two FF-2D L-VAL follow-ups folded in and `_ff2d_crossover_adapter.py` deleted; T1-X re-solved COLD for ERCOT/PJM/MISO at post-W1 HEAD, **HOLD ×3**, no keeper moved. **Carry to FFR-3A:** ERCOT's leg is scored against `2026-08-01-ercot149-gas-event-cap` (sidecar `keeper_run_id`), but the ERCOT keeper has since moved to `2026-08-02-ercot150b-zonal-anchor` — the comparator is one keeper stale. Statuses are unchanged (FAIL/PASS/PASS) and the HOLD does not depend on it, but the 2025 price input gap re-reads 0.98 → **1.07** against the current keeper. PJM/MISO comparators are still current. `check_forecast_staleness.py` does **not** track keeper-comparator drift — only commit distance and epoch spread. |
| FFR-2B | OPUS | 2 | L-CAP | — | **landed 2026-08-02** (PR #3277) | `ffr-2b-retirement-entry-evidence-2026-08-02.md` — the D-1/D-2 evidence base. Bar met for D-1; **only PARTLY met for D-2** (rate limit re-phases rather than reduces backstop MW; I12 WARN→FAIL as a disclosed change). Caveat: ran with `correlated_forced_outage` + `entry_lookahead_reprice` pinned OFF by the harness. |
| FFR-2C | OPUS | 2 | L-CAP | — | **landed 2026-08-02** | `ffr-2c-net-cone-currency-2026-08-02.md` — FR-19 net-CONE currency re-anchor + FF-G3 escalation evidence. Leaves constants-level epoch debt that FFR-3A must clear before its battery. |
| FFR-2D | OPUS | 2 | — | — | **landed 2026-08-02 → SITTING HELD** | `ffr-owner-sitting-2026-08-02.md`. **All eleven decisions SIGNED** (Addendum C). |
| FFR-2E | OPUS | 2 | L-CAP | — | **landed 2026-08-02** | `ffr-2e-shipped-capacity-posture-2026-08-02.md` — shipped-vs-fixed capacity posture. Discharged D-3a's defer condition mid-sitting; surfaced B1 (run_full_horizon's own FR-14 shape), the NYISO wrong-arm citation, and the pre-epoch-citation problem. |
| FFR-3A | OPUS | 3 | L-VAL | ⛔ | **not-sent (next)** | Executes signed D-1 (flip), D-2 (arm both dampers), D-6 (regenerate the NYISO pair as **shipped-vs-fixed**, not the force-ON probe pair), then re-scores the T1 battery and regenerates every board. Must clear FFR-2C's constants-level epoch debt first. |
| FFR-3B | OPUS | 3 | — | — | **landed 2026-08-02** | `ffr-3b-staleness-bookkeeping-2026-08-02.md` — executes signed D-5(a)/(b)/(c) + D-7(i); FR-21 staleness machinery (provenance stamps + WARN-level CI check); FR-27 forecast DOF-ledger stub; this bookkeeping reconciliation; closes FFR-1C **F-5**. |

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
  infrastructure. **ALL FOUR T1-infra prompts + FF-3E verified-pass (t40).**

**RESOLVED (owner, turns 38–45):**
- **Key-rotation (#2659/#2660) — CLOSED.** Keys public/free-tier.
- **FF-2B git-push exception — BLESSED** (narrow last-resort, blob-verify mandatory).
- **NEISO — HOLD; hold-scope CLOSED (t40, owner: out of manager scope, do not track).**
- **Stray file cleanup (t38)** — `.constants_push_stage.txt` deleted.
- **Staging-dir bloat [t43 flag 1] — RESOLVED (t44).** `scripts/_rule27_push_staging/` gone (bloat purge).
- **Stale-clone/proxy friction [t43 flag 3] — LARGELY RESOLVED (t45).** Owner ran the
  `cleanup-large-blobs.yml` history rewrite to SUCCESS (t45), on top of the t44 bloat purge +
  parquet slimming + SessionStart blobless fast-forward hook + gitignore hardening. Manager fixed
  the workflow's push (t44-45, #2790): chunked-checkpoint push (defeats the 4.76 GiB single-pack
  HTTP 500) + workflow-scoped PAT auth (`HISTORY_REWRITE_PAT`, defeats the GITHUB_TOKEN
  workflow-file push refusal). **Residual:** the LIVE tree still holds >50 MB parquets (GitHub LFS
  warnings in-run) — history rewrite cannot shrink the current footprint. **Durable fix recommended
  to owner (t45): Git LFS or external object store for `data/raw/` + `results/calibration/` binaries,
  and `--filter=blob:none` clones.** Owner may act; not manager-dispatchable FF work.

**AWAITING (each changes what I dispatch next):**
- **§2.1b gate-open per ISO** — NOT authorized (owner: “not running full solves yet”). FF-3E's
  closeout scorecard is the standing evidence; PJM/NEISO closest (I4 “A1” leak sole blocker).
  Re-surface only when owner initiates.
- **(nothing dispatchable at T1)** — all T1-infra prompts verified-pass. Only §2.1b-gated
  full-horizon campaigns remain (owner-held). FF-3C trigger-gated inactive.
- **⚠ HOUSEKEEPING flag still open (out-of-program, not stop-the-line):**
  (2) PJM M-3 gas-bridge (#2756) — `docs/handoffs/pjm-m3-gas-bridge.patch` (836L) remains an
  UNAPPLIED stale-based patch; the M-3 mechanism is NOT in main. Needs a fresh working-clone
  session to re-base + apply. Out-of-program PJM deliverable; keep visible.

---

## Corrections issued

1–12 (turns 2–35) — all RESOLVED/RETRACTED. Genuine non-deliveries total 3 (FF-0B #2412, FF-2A
   #2453, FF-2A-posture #2522). Full detail in prior ledger commits.

---

## Turn log

- **turns 1–43 (collapsed — see prior ledger commits + header entries).** Waves 0/1 CLOSED; FF-2B/
  2C/2C-rig/2D verified-pass (Wave 2 CLOSED, all 6 ISOs HOLD); FF-3B verified-pass; FF-3E/5A/3F/3G/3H
  all verified-pass by t40 — **T1 INFRASTRUCTURE PROGRAM COMPLETE.** t41–43 three clean refreshes
  (out-of-program calibration + facade splits + orchestrator refactor).
- **turn 44 (`fe1fe5ce→22cfd56a`, refresh).** NO FF-manager work; program AT REST; RULE-27 CLEAN.
  Out-of-program: owner bloat purge (`07fee6e`) + ERCOT parquet slimming + stale-clone infra
  (SessionStart hook, gitignore, cleanup workflow) + backcast calibration (ERCOT-96 keeper, NYISO
  lever-3 nyiso-69 NOT-YET, CAISO-113 rejected probe). Only source-touch = NYISO lever-3 additive
  gated flag (`config/scenarios.py` +23 / `model/reserves/spec.py` +13) — GROWTH, no shrink.
- **turn 45 (`22cfd56a→29a5e8eb`, refresh + owner-requested infra fix. NO FF-manager program work;
  program AT REST. RULE-27 CLEAN.)** Two threads: **(A) HISTORY REWRITE landed.** Owner merged the
  manager's cleanup-workflow fix (#2790) to main, then ran `cleanup-large-blobs.yml` to SUCCESS (run
  `29961034978`, 22:11): stripped superseded `data/raw/`+`results/calibration/` blob versions,
  in-run integrity verified (main manifest byte-identical, source untouched), force-pushed all
  branches, prime ref cleaned up. **All pre-`29a5e8eb` SHAs now orphaned; re-clone required.** The
  fix took THREE diagnosed failure modes: (1) 4.76 GiB single-pack HTTP 500 → chunked 200-commit
  checkpoint push to a throwaway `refs/blob-cleanup-tmp/prime` ref; (2) GITHUB_TOKEN refused
  workflow-file pushes → PAT auth via `HISTORY_REWRITE_PAT` (workflow scope) + early guard step; (3)
  under-scoped PAT (workflow-only, no repo/contents write) → owner re-issued with Contents+Workflows
  write. Manager also corrected a self-introduced transcription slip (CodeQL disk-reclaim path) mid-
  stream. **(B) Out-of-program merges since t44:** ERCOT-97 Lane A DAM→EIA plant crosswalk +
  default-off plant-grain flag (#2791, keeper unchanged, zero fitted params); dispatch.py → `model/lp/`
  **sanctioned facade split** (#2789: rows.py/model.py/__init__.py verbatim slices + facade + golden
  byte-gate + `tests/test_dispatch_facade.py`) — NOT truncation, added to watch set. **RULE-27
  CLEAN:** rewrite preserved source byte-for-byte (verified in-run); dispatch split is a facade with
  golden byte-identity; no watch-set shrink. **Residual/recommendation:** live tree still carries
  >50 MB parquets (GitHub LFS warnings) — recommended Git LFS / external store + blobless clones to
  the owner (see flag 3). **Nothing dispatchable** — §2.1b gate owner-held; FF-3C trigger-gated
  inactive; all T1 infra verified-pass. Manager branch #2790 merged → restarted from `29a5e8eb`.
