# Fable Prompt Pack — 2026-07-04

Companion to `docs/fable-repo-audit-2026-07.md` (finding IDs like EM-1, RC-2, AR-1, TC-1
refer to that doc). This pack turns the audit into scheduled work: **Wave 0** is the set of
Fable planning sessions to run while Fable access remains (3 days); **Wave 1** runs in
parallel on execution models; **Waves 2-3** implement and validate against the Wave-0 plans.

## How to use

- **Run every Wave-0 prompt as its own fresh Fable session, in parallel.** Each produces a
  plan doc under `docs/handoffs/` plus a refined implementation prompt — Fable's job is
  judgment (diagnosis, methodology decisions, migration sequencing), not bulk code edits.
- **Wave 1 is independent of Wave 0** — start it immediately on Sonnet/Opus in parallel.
- **Wave 2 prompts consume the Wave-0 plan docs**; don't start one before its plan exists.
  Wave-2 items are mutually independent — parallelize freely across sessions.
- **Model key:** `[FABLE]` judgment-heavy planning/diagnosis (scarce — spend on these);
  `[OPUS]` complex implementation/refactors; `[SONNET]` well-scoped implementation, tests,
  docs, hygiene.
- Every session: work on a feature branch, commit and push per the CLAUDE.md
  "Git & Pushing" workflow (413 rules), and obey the non-negotiables — especially rule 1
  (structure first, never judge a mechanism by the residual), rules 13/14 (measured data
  admissibility), rule 22 (2022/H1-2026 holdout quarantine: no solves, no scoring, no data
  intake), and LP-only (no MIP, no Pyomo/PuLP).

### Dependency map

```
Wave 0 (Fable, parallel)          Wave 1 (parallel, independent)
  W0-P1 emissions plan     ──►      W1-P1 CI wiring            [SONNET]
  W0-P2 retirement plan    ──►      W1-P2 scoring-integrity    [SONNET]
  W0-P3 architecture plan  ──►      W1-P3 hygiene sweep        [SONNET]
  W0-P4 validation program ──►      W1-P4 rule-24 migration    [OPUS]
  W0-P5 capacity-econ plan ──►      W1-P5 LP hardening         [OPUS]
  W0-P6 scope2 roadmap     ──►      W1-P6 scope2 sync-docs     [SONNET]
       │
       ▼
Wave 2 (Opus, parallel, gated on the matching W0 plan)
  W2-P1 emissions fixes ◄ W0-P1        W2-P4 calibration-core lift ◄ W0-P3
  W2-P2 retirement channel ◄ W0-P2     W2-P5 invariants + hindcast ◄ W0-P4
  W2-P3 capacity-econ impl ◄ W0-P5
       │
       ▼
Wave 3 (validation & wrap; W3-P1/P2 need W2-P1 landed to be worth scoring)
  W3-P1 statmode ×5 ISOs   W3-P2 CAISO CT scrub   W3-P3 docs reorg   W3-P4 scope2 real run
```

Priority if time runs short: **W0-P1 > W0-P2 > W0-P4 > W0-P3 > W0-P5 > W0-P6**; and in
Wave 1, **W1-P1/W1-P2 first** (they protect every number the other waves produce).

---

## Wave 0 — Fable planning sessions (run all in parallel, one session each)

### W0-P1 `[FABLE]` — Emissions-integrity diagnosis and fix plan

```
Read CLAUDE.md, then docs/fable-repo-audit-2026-07.md §A (findings EM-1…EM-8). This model's
sole objective is asset-level emissions forecasting within ±10%, and the audit found the
emissions-rate path is its weakest link: NOx/SO2 tons are unwired (results/emissions.py:84
has no caller; results/export.py:121 exports CO2 only; SO2 computed nowhere), a likely
~2204x NOx unit bug (tonnes/MWh written at fleet.py:4577,4620, consumed as lb/MWh at
plant_financials.py:71-72,376), forecast rates frozen at pooled 2023-25 CEMS with no
mode-gating (scenarios.py:279, contradicting CLAUDE.md L21) and no retrofit/degradation
path to 2050, tranche price-wall multipliers contaminating CO2 for CEMS-uncovered plants
and all new entrants (fleet.py:6298 vs binning-methodology.md:148,196-200), startup
emissions unmodeled, a carbon-price backcast/forecast seam (policy/carbon.py:23,66-84),
CHP rate inconsistency (emissions.py:172-175), and a possible gross/net MWh-basis mismatch.

Your tasks:
1. Execute the audit's 9-step emissions-bias checklist empirically where cheap: (a) run one
   ERCOT keeper year with use_plant_emission_rates True vs False and diff annual CO2 by
   class (quantifies EM-3 reliance and EM-4 contamination); (b) unit-assert the NOx contract
   end-to-end on a known coal unit (~1.5 lb/MWh vs ~0.0007 t/MWh decides EM-2); (c) count
   starts x nominal per-start MMBtu from an existing P1 bundle to bound EM-5 materiality;
   (d) reconcile one coal plant's model CO2 vs CAMPD, decomposed into MWh error x rate
   error, to test EM-8. Use existing bundles/diagnostic probes — do NOT launch new
   multi-year calibration solves.
2. Decide (with justification against rules 1/13/14) the intended forecast emission-rate
   provenance: frozen measured CEMS vs heat-rate-derived vs measured-with-evolution hooks.
   Resolve the CLAUDE.md L21 vs rule-11 contradiction in writing.
3. Produce docs/handoffs/emissions-integrity-plan-2026-07.md: ranked fixes, each with
   mechanism design, files touched, test plan, and expected emissions impact; plus a
   complete implementation prompt for W2-P1 (single fenced block).
Deliverable: the plan doc + prompt, committed and pushed on a feature branch. Do not
implement the fixes themselves.
```

### W0-P2 `[FABLE]` — Confirmed-vs-announced retirement channel design

```
Read CLAUDE.md, then docs/fable-repo-audit-2026-07.md §B (RC-1…RC-5). Owner intent: only
CONFIRMED/actual retirements (already retired, or binding confirmed dates — settlements,
RTO deactivation acceptances) should be exogenous; ANNOUNCED future retirements must stay
with the model's economic retirement decision, because under current demand growth plants
scheduled for retirement keep staying online. Today the code approximates this with a fuel-
type proxy: fossil units ignore ALL EIA-860 announced dates (capacity.py:196-235, default
forecast_fossil_retirement_economic=True) — right spirit, but there is no channel to force
a genuinely confirmed fossil closure, the EIA-860 retirement-status field is dropped at
intake (scripts/process_eia860.py:64,239-243,310-313), forecast mode has no exogenous
confirmed-exit injector at all (runner.py:293-295, fleet.py:1990 are backcast-gated), and
non-fossil units force-retire even on speculative 2040-2072 EOL placeholder dates.

Your tasks:
1. Identify the authoritative confirmed-retirement signal: what EIA-860 status/columns are
   available in data/raw/eia-860 (inspect the raw files), and what external sources
   (RTO deactivation lists, consent decrees) would be admissible under rule 13's
   reproducible-forward-input test. Design the data intake per the data-intake skill
   conventions (schema-first, per-ISO registry, no if-iso ladders).
2. Verify empirically whether the economic screen retires the near-term (2026-2028, ~205
   units carry planned years) genuinely-confirmed subset on schedule, using an existing or
   cheap single-ISO forecast run.
3. Design the mechanism: a confirmed-exit injector for forecast mode (mirroring
   load_planned_additions' construction-committed philosophy), the confirmation gate for
   non-fossil placeholder dates, and the rename/doc fix for the "Known retirements" misnomer
   (RC-3). State how each regenerates for a forward year (rule 17-style forward story).
4. Produce docs/handoffs/confirmed-retirement-plan-2026-07.md + a complete W2-P2
   implementation prompt. Do not implement.
```

### W0-P3 `[FABLE]` — Forecast/backcast architecture unification plan (D-5 parity)

```
Read CLAUDE.md, then docs/fable-repo-audit-2026-07.md §E (AR-1…AR-6) and §J item T2 context.
The repo's largest architectural debt: the backcast orchestrator (_calibration_config
~850 lines + run_year ~2,600 lines in scripts/run_calibration.py, consumed by
run_calibration_full.py:100) parallels src/market_sim/runner.py (run_scenario_iso, ~1,020
lines), and mechanisms drift between the two paths — several ISO overlays (MISO firm
imports, NEISO coldsnap derate, CAISO bidir intertie/import-solar-shape/gas-coupling) are
wired only in the calibration path; cross-year warm-start (dispatch.py:1936-2589) is built
but unused by the forecast runner. scripts/legitimacy_diagnostics.py D-5 and
docs/audit-wiring-iso-gaps/ already catalogue parity gaps.

Your tasks:
1. Build the definitive parity matrix: every mechanism/overlay/flag instantiated in
   _calibration_config+run_year vs runner.py, classified backcast-only-by-design (per
   CLAUDE.md's overlay rules) vs accidental-drift vs forecast-only.
2. Design the staged migration that lifts the shared solve core into a package module
   (e.g. src/market_sim/calibration/): extraction order, what runner.py and
   run_calibration_full.py each become (thin front-ends), how getattr feature-flags fold
   into ScenarioConfig (AR-5, rule 24), where PriorYearResults (typed dataclass) and
   DispatchSpec/ReserveSpec land (AR-2, AR-5), and whether cross-year warm-start should be
   adopted by the forecast P0 (AR-6).
3. Define the regression guard: byte-identity (or tolerance-bounded) re-solve of one keeper
   bundle per ISO before/after each stage, plus the trivial-case tests. The migration must
   be provably dispatch-neutral stage by stage.
4. Produce docs/handoffs/orchestrator-unification-plan-2026-07.md with the stage sequence
   sized for separate sessions, + a complete W2-P4 implementation prompt for stage 1.
Do not implement. Reconcile with docs/iso-model-unification-plan.md if it overlaps.
```

### W0-P4 `[FABLE]` — Forecast validation program design (hindcast, invariants, statmode sequencing)

```
Read CLAUDE.md (rules 16, 22 especially), then docs/fable-repo-audit-2026-07.md §F (TC-3)
and §J item T1, plus docs/forecast-validation-plan.md, docs/model-audit-prompt-pack-2026-06.md
(PP-0.x) and docs/out-of-sample-results-2026-07.md. Status: the capacity hindcast — called
the centerpiece of forecast validation by two prior programs — was never built (no
run_capacity_hindcast.py, no reports); statistical-mode backcast has run for ERCOT only;
no forecast invariant checker exists; test_runner.py stubs the LP so the 2026-2050
evolution loop has zero end-to-end coverage; holdouts 2022/H1-2026 are quarantined and
4 of 6 ISOs lack the holdout data anyway.

Your tasks:
1. Design the capacity hindcast concretely: which historical window is admissible under the
   holdout quarantine (e.g. initialize the fleet at 2018-2020 vintage EIA-860, evolve to
   2023-2025, score builds/retirements/mix against actuals — verify which vintage snapshots
   exist under data/raw/eia-860), what is scored (per-fuel GW built/retired, timing, zonal
   placement, resulting CO2), pass bands consistent with the +/-10% goal, and where results
   register (dashboard? new page?).
2. Specify the forecast invariant test suite (seed from audit §F: energy balance every
   year, no-NaN, CO2 monotone under rising carbon price, merit-order sign checks, economic-
   retirement sanity, reliability-floor never breached, planned-additions mode-gating,
   storage caps, RPS dual >= 0, one-pass assertion) and the golden-scenario band regression.
3. Sequence the whole program: what must land first (W1-P1 CI, W2-P1 emissions fixes change
   the scored quantity), when statistical-mode runs for the 5 remaining ISOs, what data
   intake unblocks D-6 (docs/out-of-sample §1.1 F1-F6) WITHOUT touching quarantined years,
   and the decision rule for eventually declaring an ISO calibration-complete.
4. Produce docs/handoffs/forecast-validation-program-2026-07.md + complete implementation
   prompts for W2-P5 (invariants+hindcast build) and W3-P1 (statmode runs).
Do not run any solve touching 2022 or 2026. Do not implement.
```

### W0-P5 `[FABLE]` — Capacity-economics recalibration design (FOM, foresight, floor, DC load)

```
Read CLAUDE.md, then docs/fable-repo-audit-2026-07.md §C (CX-1…CX-6). Four material items,
all LP-only: (1) going-forward FOM bars ~1.5-2.5x below ATB (scenarios.py:146-162: ct 8 /
cc 12 / coal 52 vs ATB ~21 / ~30 / ~45 $/kW-yr) -> systematic fossil under-retirement, but
raising them interacts with the understated scarcity/AS revenue the 2026-06 assessment
flagged — they must move together or retirement flips the other way; (2) one-pass myopia:
entry/exit see only prior-year prices (runner.py:379-385,1123-1130) so the fleet chronically
lags 5%/yr growth — candidate fixes are an EWMA price blend across solved years and/or a
growth-scaled lookahead pre-adjustment, both pre-solve signal construction; (3) the
reliability floor (capacity.py:553-569) accredits raw thermal nameplate (not ELCC/UCAP via
the existing accredited_firm_capacity_mw at capacity.py:1280), is non-locational, and can
non-economically retain coal — needs accreditation, emission-aware tie-breaking, and
floor-vs-economic attribution logging; (4) demand growth is a uniform scalar on a frozen
shape (constants.py:598-634, runner.py:116-131) — design an additive flat/high-CF
data-center MW block and optionally an electrification shape adder, separately
parameterized in ScenarioConfig.

Your tasks: for each item produce the concrete parameter/mechanism design with citations
(ATB values into docs/parameter-citations.md discipline), the joint FOM+scarcity
sensitivity protocol (so the two aren't tuned independently against the same residual —
rule 1), the A/B experiment design for foresight (does EWMA vs lookahead materially change
2030-2040 fossil dispatch on ERCOT-high-growth?), and expected emissions direction. Also
adjudicate CX-6 (nuclear RPS eligibility, uniform WACC, VRE flat-mean entry revenue) as
fix-now vs document-as-limitation. Produce
docs/handoffs/capacity-economics-plan-2026-07.md + a complete W2-P3 implementation prompt.
Do not implement.
```

### W0-P6 `[FABLE if available, else OPUS]` — Scope2 tool roadmap

```
Read scope2-lce-portfolio/PLAN.md, README.md, docs/, then
docs/fable-repo-audit-2026-07.md §I (S2-1…S2-5). The tool is mature (238 tests green,
end-to-end sample sweep works, disciplined ADR trail) but has never produced a real priced
result — everything to date runs on dummy LMPs and synthetic CF (real-forecast path ON HOLD
pending market-sim forecast readiness).

Your tasks:
1. Design the first real-data validation run: build per-ISO CF profiles via
   scripts/build_profiles.py from the market-sim EIA-930 tree, export a BACKCAST-year LMP
   (ADR 0015 permits backcast for validation) via scripts/export_lce_lmp.py, build the
   fossil-avg CO2 rate file, run one per-ISO sweep, and define sanity gates for the
   frontier, build mix, and residual CO2 (e.g. vs published 24/7 CFE study curves —
   Google/Princeton results give shape expectations: steeply rising premium past ~90%
   matching, storage+firm entering at high targets).
2. Adjudicate the methodology extensions: (a) optional marginal-emissions/emissionality
   mode (S2-3) — worth it now or after real-data validation? (b) reporting-solve uniqueness
   (S2-4: optional crossover or lexicographic least-cost re-solve at reported points only);
   (c) deliverability bounding (S2-5) — at minimum a quantified single-node smoothing-bias
   note. Sequence them.
3. Produce scope2-lce-portfolio/docs/roadmap-2026-07.md + a complete W3-P4 prompt for the
   real-data run. Do not implement; do not modify the main model.
```

---

## Wave 1 — Immediate execution (parallel, independent of Wave 0)

### W1-P1 `[SONNET]` — Wire the claimed CI enforcement

```
Read CLAUDE.md rule 22 and docs/fable-repo-audit-2026-07.md TC-1. The rule-22 claim ("CI
enforces the quarantine") is currently false: no workflow runs pytest on PR (only
lint.yml/ruff), and scripts/audit_keepers.py + scripts/legitimacy_diagnostics.py are
invoked by zero workflows despite correctly implementing the holdout-quarantine (H1/D-6)
and D-9 gates.

Implement, on a feature branch:
1. A pull_request workflow job running a fast pytest tier. pyproject.toml already declares
   pytest markers — pick/verify a fast subset (test_regression_smoke.py targets <10s;
   measure the actual runtime of the candidate tier and keep the job under ~10 min).
2. In the same workflow: python scripts/audit_keepers.py --check and
   python scripts/legitimacy_diagnostics.py --keepers, failing the PR on nonzero exit.
   Verify locally that both commands run green on the current repo BEFORE wiring them; if
   either fails on main, report the failure — do not silence it.
3. Promote clean-parity.yml's pytest subset from weekly cron to pull_request IF its own
   "promote once regenerate is known-stable" note is satisfiable — otherwise leave a
   comment explaining why not.
4. Update CLAUDE.md rule 22's wording only if needed to match what is now actually enforced.
Test the workflow YAML syntax. Commit and push; note run times in the PR/commit message.
```

### W1-P2 `[SONNET]` — Scoring-integrity test pack

```
Read docs/fable-repo-audit-2026-07.md TC-2 and the test-plan skeleton in §F. Every reported
backcast MAE flows through untested code in scripts/calibration_verdict.py and
scripts/audit_keepers.py. Write behavioral unit tests (tests/test_calibration_verdict.py
additions + new tests/test_audit_keepers.py), on a feature branch:
- _pct (verdict.py:259): zero-actual denominator, sign convention, empty pairs.
- _wmean (:266): empty and single-pair degenerate inputs.
- score_co2 (:875): within/outside the 10% band; positive-discharge basis per the rubric
  §C5c note. Also score_storage_shape (:931) status tokens.
- _ledger_match (:289), class_is_gated (:347), family_is_complete (:362), _agg_status
  (:1206): a completeness-map bug must not silently drop a class; a mis-scoped ledger
  exception must not waive an unrelated failure; _agg_status = worst-of-children.
- audit_keepers: H1 flags an out-of-window solve year; H1 respects the
  calibration-complete marker; NEW parity assertion audit_keepers.CALIBRATION_YEARS ==
  legitimacy_diagnostics.D6_CALIBRATION_YEARS and same marker path (the comment at
  audit_keepers.py:80 claims this test exists — it does not).
- A determinism guard: verdict determination stable under metric reordering.
Use synthetic payloads (the existing test_calibration_verdict.py pattern). Do NOT change
scoring behavior; if a test exposes a real bug, write the failing test, fix ONLY if the fix
is unambiguous, otherwise document it in the test as xfail with a comment and report it.
Run the full new tests + the existing verdict tests green. Commit and push.
```

### W1-P3 `[SONNET]` — Repo hygiene sweep

```
Read docs/fable-repo-audit-2026-07.md DOC-1/DOC-2/DOC-4/DOC-6 and DA-3. On a feature
branch, mechanical cleanups only — no behavior changes:
1. Delete _szprobe.txt (inert base64 push-size probe, zero refs) and configs_nyiso_jacobian/
   (orphaned sweep scratch, zero refs). Relocate scratchpad_diag_evening.py to
   scripts/diagnostics/ (referenced by results/calibration/FINDING-caiso-evening-merit-
   2026-07-04.md — update that reference) and configs_run20/ into the run bundle or configs
   area its PJM handoff doc references (update docs/handoffs/pjm-cc-overgen-recommendation-
   2026-06.md accordingly). Relocate stray scripts/_caiso_class_lmp.py into scripts/probes/.
2. Fix CLAUDE.md "7-ISO topology" -> "6-ISO" (iso_configs.py registers exactly 6 builders).
3. Collapse CONVENTIONS.md to a short pointer at the CLAUDE.md sections it duplicates
   (naming, git, docstrings, raw-data immutability) — keep any content NOT in CLAUDE.md.
4. Archive the ~24 dead one-off scripts listed in audit DOC-6/agent findings (numbered
   run_ercot_2x/run_pjm5x-7x/run_caiso3x-4x drivers and the zero-ref scripts/probes/ set) —
   but FIRST re-grep each candidate across the whole repo INCLUDING scripts/probes/ itself
   (some probes chain-import each other); move survivors-with-refs nowhere. Prefer git rm
   (history preserves them) with a single commit listing each file and its zero-ref
   justification.
5. Document the six derive-owned datatypes (DA-3: border-lmp, fuel-basis, fuel-ercot-ep-gas,
   fuel-hub-monthly, fuel-takeorpay, fuel-zonal-hub) in docs/adding-new-data-types.md as a
   sanctioned derive_*-owned class, or note them as TODO-curate — one paragraph, whichever
   matches reality.
Run the fast test tier to confirm nothing imports what you removed. Commit and push.
```

### W1-P4 `[OPUS]` — Rule-24 off-registry literal migration

```
Read CLAUDE.md rule 24, then docs/fable-repo-audit-2026-07.md DA-1/DA-2/DA-4. Three
off-registry tuning channels live in data/ modules:
1. MIXED_FACILITY_STEAM_HR (fleet.py:467) — per-plant heat-rate literals feeding mc in the
   offer path. Move to a curated reference CSV under data/raw/reference/ with schema entry,
   loaded through the existing reference-loading seam; values unchanged, provenance comment
   (measured Ormond analog) preserved in the CSV/doc.
2. BIN_FORCED_DERATE_BY_YEAR (fleet.py:4320-4335) — per-plant/per-year availability derates
   (Martin Lake, V H Braunig, Sandy Creek 2025 events). These are outage events: migrate
   them into the outages datatype/overlay path (src/market_sim/data/outages.py + its data
   files) so they flow through the same admissibility gates, mode-gating, and run_config
   visibility as other outage windows.
3. _FLEET_GROUP_OVERRIDE (outages.py:466) — fold into the reference crosswalk
   (custom-bin-assignments / master-plant-registry pattern).
Constraints: results must be bit-identical for the current keepers — this is a plumbing
migration, not a retune. Verify by re-running the relevant fleet-construction unit tests
and diffing a fleet-arrays dump (or an existing cheap probe) before/after. Follow the
data-intake skill conventions for any new file (schema-first, tmp-CLEAN_DIR tests). Update
docs/parameter-citations.md entries. Commit and push.
```

### W1-P5 `[OPUS]` — LP solver hardening and memory

```
Read CLAUDE.md (LP layout, rule 2), then docs/fable-repo-audit-2026-07.md AR-3/AR-4/AR-6.
On a feature branch, in src/market_sim/model/dispatch.py:
1. Batch matrix assembly: build_constraints currently grows A with ~8 sequential
   sp.vstack calls (dispatch.py:1544-1684), re-copying the growing CSR each time. Collect
   blocks + bound vectors in lists, single vstack/concatenate at the end. Target: measurable
   peak-RSS/build-time reduction on a mid-size ISO-year; measure and report before/after.
2. Fix apply_cross_year_basis (dispatch.py:2585-2586): it materializes ~1.8M Python
   HighsBasisStatus enum objects, contradicting the int8 design note at 1929-1931. Check
   whether highspy setBasis accepts array-like statuses; otherwise minimize the conversion.
3. Pin HiGHS solver method and primal/dual feasibility tolerances explicitly
   (dispatch.py:2228-2244) for cross-version reproducibility — choose values matching
   current default behavior (verify a keeper-year re-solve is unchanged within tolerance).
4. Infeasibility diagnostics (dispatch.py:2418-2423): on non-optimal status, report max-
   slack zone/hour and basic model stats instead of a bare RuntimeError string.
5. Dual robustness (dispatch.py:2454): assert dual solution status before reading prices,
   and add a regression test asserting DispatchResult.prices equals a hand-computed LMP on
   the 1-gen/1-zone/24-hour trivial case (sign convention + marginal-unit price), plus a
   two-gen case where the second unit is marginal.
6. Small cleanups: rename the shadowing `cap` local in _build_reserve_rows (840 vs 1033);
   add the ttc_import/link_bidirectional ordering assertion (1794-1811); centralize the
   triplicated pmax*availability computation behind one helper.
Rule 2 applies: no Python loops over hours. Also vectorize the 365-iter daily-peak
list-comp at transmission.py:3050-3055 (reshape(n_days,24).max(axis=1)). Run the dispatch/
storage/transmission test files green, plus your new tests. Commit and push with the
measured memory/time numbers in the message.
```

### W1-P6 `[SONNET]` — Scope2 docs reconciliation

```
Work ONLY inside scope2-lce-portfolio/. Read docs/fable-repo-audit-2026-07.md S2-2. The
code outran its prose; reconcile (no behavior changes):
- config.py:99-104: additionality_only docstring claims "no effect on the LP" — false; it
  is fully implemented (lp.py:224-233,376-400,500-507). Rewrite to describe the actual
  mechanism.
- resources.py:231-232: hydro-budget docstring says the LP constraint "lands in PP-02b" —
  it landed (lp.py:346-374). resources.py:20: same for split-storage support.
- PLAN.md §9/§10 + README: "147 tests" -> current count (run pytest to get it, ~238);
  mark PP-09 reporting done (report.py ships and is tested); reconcile the data/emissions/
  dir (PLAN says removed per ADR 0013 but it exists with only .gitkeep — delete the dir or
  fix the PLAN text, whichever matches ADR 0013's actual decision).
- Note the tested-but-idle seams (intake.collapse_zonal_lmp, vendored
  capacity_weighted_collapse, vendored compute_fossil_avg_rate) as build-time/seam helpers
  in their docstrings so future readers don't think they're on the runtime path.
Run the scope2 test suite green (cd scope2-lce-portfolio && pytest tests/ -q). Commit, push.
```

---

## Wave 2 — Implementation (Opus, parallel; each gated on its Wave-0 plan doc)

### W2-P1 `[OPUS]` — Implement the emissions-integrity fixes

```
Prerequisite: docs/handoffs/emissions-integrity-plan-2026-07.md exists (from W0-P1) — read
it first, then CLAUDE.md and docs/fable-repo-audit-2026-07.md §A. Implement the plan's
ranked fixes. Expected scope (defer to the plan where it differs): wire NOx/SO2 tons
through results/emissions.py -> export.py with a single unit contract (write the unit into
the column name), fix the tonnes-vs-lb bug wherever the plan located it, apply the decided
forecast rate provenance with explicit mode-gating and a documented evolution hook, stop
tranche pricing multipliers from contaminating emission rates (emissions at physical heat
rate, offers at bid heat rate — separate arrays), book startup emissions if the plan's
materiality probe justified it, and close the carbon-price seam per the plan's decision.
Every fix ships with behavioral tests (1-gen trivial cases first per CLAUDE.md), and the
NOx unit contract gets an end-to-end assertion test. After landing, re-solve ONE keeper
year per affected ISO as a diagnostic probe (not a keeper) and report the CO2/NOx/SO2
deltas by class — expected and explained deltas only; do not retune anything to preserve
the old fit (rule 1: a structurally-correct fix stays in even if the backcast residual
moves). Commit and push; flag in the commit message that keeper re-gating (full-year
bundles, rule 16) is required downstream.
```

### W2-P2 `[OPUS]` — Implement the confirmed-retirement channel

```
Prerequisite: docs/handoffs/confirmed-retirement-plan-2026-07.md (from W0-P2) — read it,
then CLAUDE.md rules 13/14 and audit §B. Implement per the plan: extend
scripts/process_eia860.py (and the schema) to carry the retirement-status/confirmation
columns; add the forecast-mode confirmed-exit injector gated on confirmation status
(mirroring load_planned_additions' philosophy — construction-committed analog: only
binding/confirmed exits force-retire); add the confirmation gate for non-fossil placeholder
dates per the plan's decision; rename/annotate the "Known retirements" step so its fossil
no-op default is explicit in code comments, CLAUDE.md, and the methodology spec. Follow the
data-intake skill (schema-first, write_clean/read_clean seam, tmp-CLEAN_DIR tests, per-ISO
registry). Tests: injector honors confirmed dates, ignores announced-only dates, is
forecast-mode-only where designed, and the economic screen remains the sole channel for
unconfirmed fossil. Run the capacity/fleet test files green. Commit and push.
```

### W2-P3 `[OPUS]` — Implement capacity-economics recalibration

```
Prerequisite: docs/handoffs/capacity-economics-plan-2026-07.md (from W0-P5) — read it,
then CLAUDE.md and audit §C. Implement per the plan: (1) ATB-cited FOM going-forward
defaults in ScenarioConfig with docs/parameter-citations.md entries, executed together with
the plan's joint FOM+scarcity sensitivity protocol — run the protocol's probe matrix and
record results before committing the new defaults; (2) the chosen partial-foresight signal
(EWMA blend and/or growth-scaled lookahead) as pre-solve signal construction in runner.py,
behind a ScenarioConfig field, with the plan's A/B experiment executed and reported;
(3) reliability-floor accreditation on ELCC/UCAP firm capacity (reuse
accredited_firm_capacity_mw), emission-aware un-retirement tie-breaking, and floor-vs-
economic retirement attribution logging in outputs; (4) the additive data-center flat-load
block (+ optional electrification shape adder) as separately-parameterized ScenarioConfig
inputs summed onto base_demand. All values cited (rule 5); no magic numbers; every
mechanism carries its forward story. Behavioral tests for each (retirement flips at the
documented threshold; floor never binds when accredited capacity clears; DC block flattens
the net-load duration curve as expected). Commit and push.
```

### W2-P4 `[OPUS]` — Calibration-core lift, stage 1

```
Prerequisite: docs/handoffs/orchestrator-unification-plan-2026-07.md (from W0-P3) — read
it, then CLAUDE.md and audit §E. Execute exactly stage 1 of the plan (expected: lift the
shared solve core — _calibration_config, run_year, _commitment_pass, offer-curve delta and
TTC/deliverability helpers — from scripts/run_calibration.py into
src/market_sim/calibration/, with scripts/run_calibration.py re-exporting for backward
compatibility, and run_calibration_full.py imports updated). The stage MUST be dispatch-
neutral: before starting, capture the plan's regression baseline (keeper-bundle re-solve
per the plan's protocol); after the move, re-run and diff — any numeric change fails the
stage. Do not fold in behavior improvements, flag migrations, or overlay parity fixes in
this stage (they are later stages) — this is a pure mechanical relocation with import
hygiene. Run the full test suite. Commit and push with the baseline-diff evidence
summarized in the message. If the stage is too large for one session, land the plan's
sub-stage 1a and hand off cleanly with a status note in the plan doc.
```

### W2-P5 `[OPUS]` — Forecast invariant suite + capacity hindcast build

```
Prerequisite: docs/handoffs/forecast-validation-program-2026-07.md (from W0-P4) — read it,
then CLAUDE.md rules 16/22 and audit §F/§J-T1. Implement per the plan:
1. scripts/check_forecast_invariants.py + tests/test_forecast_invariants.py — the plan's
   invariant list (energy balance per year, no-NaN/inf, CO2 monotone under rising carbon
   price, merit-order sign response, economic-retirement sanity, reliability floor
   integrity, planned-additions mode-gating, storage caps, RPS dual >= 0, one-pass
   assertion), exercised on a short real-LP forecast horizon (e.g. one ISO 2026-2030;
   choose the smallest ISO-year the plan designates to keep runtime sane).
2. scripts/run_capacity_hindcast.py + scripts/score_capacity_hindcast.py per the plan's
   design (vintage initialization -> evolve -> score builds/retirements/mix/CO2 vs
   actuals), writing reports under the plan's designated location.
3. Run the hindcast for the plan's first designated ISO and register the result where the
   plan says. HARD CONSTRAINT: no solve, scoring, or data intake may touch 2022 or any
   2026 actuals (rule 22). If the hindcast window the plan chose conflicts with available
   vintage data, stop and record the blocker in the plan doc rather than improvising a
   quarantine-adjacent window. Commit and push.
```

---

## Wave 3 — Validation & wrap-up (after the relevant Wave-2 items land)

### W3-P1 `[SONNET]` — Statistical-mode backcasts for the five remaining ISOs

```
Prerequisite: W2-P1 (emissions fixes) landed, and the W0-P4 plan's statmode prompt — read
docs/handoffs/forecast-validation-program-2026-07.md first, plus CLAUDE.md rules 15/16/22.
Run the statistical-mode backcast (the D-7 protocol used for ERCOT — see
scripts/run_statmode_probe.py lineage and apply_statistical_mode in
run_calibration_full.py) for CAISO, PJM, MISO, NYISO, NEISO: all available years
(2023-2025) in one bundle per ISO. Launch separate-invocation runs as concurrent
background jobs capped at 2 simultaneous for per-plant multi-zone LPs (rule 12); years
within an invocation stay sequential. Register every completed run on the dashboard via
the calibration-report skill in the same session (rule 15) — these are diagnostic probes,
labeled per the plan, not keepers. Report the statmode-vs-keeper skill comparison per ISO
(the D-7 question: does the calibrated structure beat a statistical baseline?) in the
plan doc. No 2022/2026 years anywhere.
```

### W3-P2 `[OPUS]` — CAISO CT floor scrub (finish legitimacy S2)

```
Read CLAUDE.md rules 17-21, docs/model-legitimacy-audit-2026-07.md §1/S2, the caiso-52
diagnosis thread (docs + results/calibration FINDING notes), and audit DP-4. The all-24h
generic reliability-floor day gate is still live (transmission.py:2896 — netload-limb CSVs
carry no start/end hour, so the sub-daily window never engages), pinning ~half of modeled
CAISO CT energy flat (CV 0.000 vs 0.35-0.45 actual). Complete the scrub: give the netload
limbs their driver-consistent binding window (rule 17: driver, hours, forward story), apply
the D-2 forced-energy attribution to verify the peaker forced-share drops under the rule-20
budget (peakers <= 10%), and re-solve the CAISO keeper config across all years 2023-2025
in one bundle (rule 16). Judge the result by structural faithfulness, not the residual
(rule 1) — if the fit worsens, keep the fix and open the root-cause issue for the newly
exposed residual. Register the run on the dashboard in the same session (rule 15) and run
scripts/legitimacy_diagnostics.py on the bundle. If it qualifies as the new keeper, update
keepers.json and run the calibration-keeper-auditor agent.
```

### W3-P3 `[SONNET]` — Docs reorganization + sync-docs

```
Read docs/fable-repo-audit-2026-07.md DOC-3/DOC-4 and docs/code-docs-cleanup-plan.md
(reconcile with it — it owns this move if it prescribes one). Execute the reorg: create
docs/reference/, docs/sessions/2026-06/, docs/sessions/2026-07/, docs/audits/,
docs/calibration/ and move files per the audit's classification (dated session/probe notes
to sessions/, living references to reference/, audit docs to audits/, the living
calibration logs to calibration/). CRITICAL: before moving anything, grep the ENTIRE repo
(CLAUDE.md, model-methodology-spec.md, src/, scripts/, tests/, .github/, frontend/,
docs/ itself) for each moved path and update every reference in the same commit —
CLAUDE.md rules 13/22 and the legitimacy scripts cite docs by path. Add
docs/sessions/README.md stating these are frozen historical notes superseded by CHANGELOG
+ keeper attestations. Then trim CLAUDE.md's paragraph-length spec restatements (capacity
evolution, CCS, storage stack) to one-liners deferring to spec §5.x. Finish with the
/sync-docs skill to catch anything this and the recent waves drifted. Run the fast test
tier (path-sensitive tests exist). Commit and push.
```

### W3-P4 `[OPUS or SONNET]` — Scope2 first real-data validation run

```
Prerequisite: scope2-lce-portfolio/docs/roadmap-2026-07.md (from W0-P6) — read it first.
Execute its first-real-run design: build per-ISO CF profiles (scripts/build_profiles.py
from the market-sim EIA-930 tree), export the designated BACKCAST-year LMP via the main
repo's scripts/export_lce_lmp.py (backcast year per ADR 0015 — never a quarantined year),
build the fossil-avg CO2 rate file, run the per-ISO sweep via run_portfolio.py, and apply
the roadmap's sanity gates (frontier monotonicity, premium curve shape vs published 24/7
CFE literature, build-mix plausibility, residual-CO2 direction). Commit the results per
the tool's committed-results-store convention, update PLAN.md §10 checkboxes that this
closes, and write a short validation memo in scope2-lce-portfolio/docs/. If a gate fails,
diagnose whether the cause is tool-side or input-side (market-sim LMP quality) and record
it — do not tune the tool to pass.
```

---

## Session hygiene reminders (apply to every prompt above)

- Read CLAUDE.md before anything; the non-negotiables override convenience.
- One session, one prompt, one feature branch; commit+push before ending (413 workflow:
  small source-only commits may use `git push`; anything carrying dashboard payloads goes
  via the GitHub API `push_files`).
- Calibration solves: all available years in one bundle (rule 16); register every completed
  run on the dashboard in the same session (rule 15); parallel invocations capped at 2 for
  per-plant multi-zone LPs, years sequential within an invocation (rule 12).
- 2022 and H1-2026 are untouchable (rule 22) — no solves, no scoring, no data intake.
- Never tune to a residual; never revert a structurally-correct mechanism because the fit
  moved (rule 1). Measured data must pass the forward-reproducibility test (rules 13/14).
