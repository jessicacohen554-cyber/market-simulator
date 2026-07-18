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

### W0-P1 `[FABLE]` — CO2-rate model design (CAMPD-history-conditioned) + emissions fix plan

*Owner direction 2026-07-04: CO2 is the priority pollutant (NOx/SO2 secondary). Forecast
emission rates for EXISTING units must be tied to historic measured CAMPD performance —
intake annual unit-level rates back to ~2018 and predict forward rates either as a
multi-year forecast average or conditioned on how the unit operates (starts/stops, total
generation) in the model year.*

```
Read CLAUDE.md (especially rules 1, 13, 14, 22), then docs/fable-repo-audit-2026-07.md §A
(EM-1…EM-8). Owner direction: CO2 accuracy is the objective; NOx/SO2 are secondary. For
existing units, forecast CO2 rates must be grounded in historic measured CAMPD plant
performance, not frozen pooled values and not generic heat-rate constants.

Your tasks:
1. DATA: inventory what data/raw/campd-unit-level and campd-facility-level already cover
   (years, columns — emissions, heat input, gross gen, op hours, start counts). Design the
   intake extension to annual unit-level CAMPD emissions + operations back to 2018
   (scripts/data/fetch_campd_unit_level.py is the existing fetcher; follow the data-intake skill
   conventions). HARD CONSTRAINT (rule 22): 2022 and H1-2026 are under FULL quarantine
   including data intake — the history is 2018-2021 + 2023-2025.
2. RATE MODEL: design and empirically compare, per unit, two forward-rate estimators:
   (a) a multi-year forecast average of annual CAMPD net CO2 intensity (choose and justify
   the weighting — gen-weighted vs recency-weighted), and
   (b) an operation-conditioned predictor: build per-unit annual observations
   (year, starts, total gen, CF, capacity-normalized op profile -> annual CO2 rate), then
   in a forecast year map the unit's MODEL-simulated operation (starts from run-length
   analysis of the dispatch solution, total gen, CF) to a predicted rate — nearest-neighbor
   on the statistically closest historical year (closest starts + closest total gen), or a
   simple per-unit (fallback per-class) regression rate = f(starts, CF). Option (b) is
   structurally preferred under rule 13 (regenerates from forward drivers AND responds to
   changed operating conditions — a unit the model cycles harder gets a worse rate);
   validate whether the data supports it per-unit or only per-class.
3. VALIDATE: leave-one-year-out within 2023-2025 — predict each backcast year's unit rates
   from the other years' history + that year's simulated operation, score vs actual CEMS,
   and compare both estimators against the current frozen pooled rate
   (use_plant_emission_rates, fleet.py:4555-4623). Use existing keeper bundles for the
   simulated-operation inputs; do NOT launch new multi-year calibration solves.
4. FOLD IN the remaining §A items, re-ranked for CO2-first: the tranche price-wall
   contamination fix (EM-4: emissions at physical heat rate, offers at bid heat rate —
   fleet.py:6298; still required since it hits CEMS-uncovered plants and ALL new entrants,
   whose class-default rates should now come from CAMPD class distributions rather than
   generic constants), the gross/net MWh basis check (EM-8), startup CO2 (EM-5 — bound
   materiality from an existing bundle's start counts), the carbon-price seam (EM-6), and
   CHP consistency (EM-7). NOx/SO2 (EM-1/EM-2): plan the cheap unit-contract bug fix and
   defer full wiring to a later wave — say so explicitly.
5. Resolve in writing the CLAUDE.md L21 vs rule-13 contradiction: measured CAMPD rates
   used this way are a reproducible physical input, admissible in forecast — update the
   CLAUDE.md wording proposal accordingly.
Produce docs/handoffs/emissions-co2-rate-plan-2026-07.md: the chosen rate-model design
with LOYO evidence, data-intake spec, ranked fixes with files/tests/expected impact, plus
a complete W2-P1 implementation prompt (single fenced block). Commit and push on a feature
branch. Do not implement the fixes themselves.
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
intake (scripts/data/process_eia860.py:64,239-243,310-313), forecast mode has no exogenous
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
IMPORTANT — reconcile with the two EXISTING workstreams instead of duplicating them:
(a) docs/audit-wiring-iso-gaps/ (gap-inventory + fix-plan + w1-w3 prompt pack, 2026-06-29)
patches parity gaps one mechanism at a time — determine which of its items already landed,
absorb the unfinished ones into your unified-pipeline stages (do NOT double-fix), and note
that the overlays drifted in AFTER its inventory (MISO firm imports, NEISO coldsnap, CAISO
bidir intertie/solar-shape/gas-coupling) prove per-mechanism patching doesn't converge —
your plan's value is eliminating the drift channel by construction. (b)
docs/iso-model-unification-plan.md targets a different axis (ISO-specific branching within
src/ — reserve co-opt functions, interchange, load shares); it never touches the
scripts-vs-package orchestrator split. Define the boundary and ordering between your
migration and that plan so the two refactors compose rather than collide.
Do not implement.
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

### W2-P1 `[OPUS]` — Implement the CO2-rate model + emissions fixes

```
Prerequisite: docs/handoffs/emissions-co2-rate-plan-2026-07.md exists (from W0-P1) — read
it first, then CLAUDE.md and docs/fable-repo-audit-2026-07.md §A. Implement the plan's
ranked fixes, CO2 first. Expected scope (defer to the plan where it differs): the CAMPD
2018+ annual unit-level emissions/operations intake (data-intake skill conventions;
rule-22 quarantine — no 2022/H1-2026 data); the plan's chosen forward CO2-rate estimator
(multi-year average or operation-conditioned predictor keyed on model-simulated
starts/gen) replacing the frozen pooled rate for existing units, with explicit
mode-gating; CAMPD-class-derived default rates for uncovered plants and new entrants;
separation of emission rates from offer heat rates so tranche pricing multipliers stop
contaminating CO2 (emissions at physical heat rate, offers at bid heat rate — separate
arrays); the tonnes-vs-lb NOx unit-contract bug fix; startup CO2 and the carbon-price
seam per the plan's decisions. Every fix ships with behavioral tests (1-gen trivial cases
first per CLAUDE.md), the rate estimator ships with the plan's leave-one-year-out
validation reproduced as a test or committed report, and the NOx unit contract gets an
end-to-end assertion test. After landing, re-solve ONE keeper
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
scripts/data/process_eia860.py (and the schema) to carry the retirement-status/confirmation
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
scripts/archive/run_statmode_probe.py lineage and apply_statistical_mode in
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

## Wave 0-B — Flagged-item planning prompts (parallel; from the Appendix FLAG list)

Run each as its own session, in parallel with each other and with Wave 0. F-1/F-3/F-4 are
Fable-grade; the rest run fine on Opus/Sonnet. None collide with the in-flight
wiring-gaps waves or the CAISO evening-merit thread.

### F-1 `[FABLE]` — Probability-bounds program plan

```
Read CLAUDE.md, docs/fable-repo-audit-2026-07.md §J-T4, docs/model-audit-2026-06.md
(§ on probabilistic machinery), and docs/model-audit-prompt-pack-2026-06.md PP-1.1/1.2/1.3.
Goal: give the emissions forecast a defensible probability band. Today
src/market_sim/ensemble.py varies weather only (n=3); no fuel/load/cost/policy
uncertainty and no structural-error term, so the +/-10% target carries no confidence
statement. Design, do not implement:
1. The scenario matrix (PP-1.1): which drivers (gas price path, load growth incl. the
   data-center block from W0-P5, capex/learning, policy path) at which discrete levels,
   sized for LP-only runtimes (rule 12 memory limits: sequential years, ~2 concurrent
   invocations).
2. The multivariate sampler (PP-1.2): LHS over correlated continuous drivers (copula or
   rank-correlation — cite the evidence source for gas-load coupling), how many draws are
   affordable, what is sampled vs scenario-switched, and where it hooks into ensemble.py.
3. The structural-error prior (PP-1.3): backcast residual distributions (later: hindcast
   skill from W2-P5) as an additive error term so reported band = parametric spread
   combined with structural error. State the assumptions honestly.
4. Output surface: how bands are computed, stored (parquet per scenario-year), displayed.
Produce docs/handoffs/probability-bounds-plan-2026-07.md + a model-assigned implementation
prompt pack. No solves touching 2022/H1-2026. Commit and push on a feature branch.
```

### F-2 `[OPUS, FABLE if spare]` — Emissions mass-cap LP constraint plan

```
Read CLAUDE.md, src/market_sim/policy/constraints.py (get_active_policy_constraints
returns [] — a stub), policy/carbon.py, docs/model-audit-prompt-pack-2026-06.md PP-2.1,
and docs/fable-repo-audit-2026-07.md EM-6. Design cap-and-trade as an LP constraint:
annual (or compliance-period) CO2 mass-cap rows over member fleets (RGGI states within
NYISO/NEISO/PJM zone membership, CA cap-and-trade for CAISO) whose dual is the endogenous
allowance price, replacing/augmenting the exogenous carbon_price_path where a real cap
binds. Decide: interaction with the W0-P1 carbon-seam fix so backcast (measured price)
and forecast (endogenous dual or projected price) use ONE structure; zone-to-state
membership mapping; banking/borrowing simplification (LP-only — likely no banking,
document it); cap-trajectory data intake (RGGI/CARB published schedules — forecast-
reproducible per rule 13); leakage treatment (imports). Vectorized rows only (rule 2).
Produce docs/handoffs/emissions-mass-cap-plan-2026-07.md + implementation prompt.
Do not implement.
```

### F-3 `[FABLE]` — ERCOT multi-product AS co-optimization forward analogue plan

```
Read CLAUDE.md, docs/forecast-methodology-gaps-2026-06.md (G1/G3/G4),
docs/forecast-methodology-gaps-prompts-2026-06.md (P1/P1b/P5a/P5c/P4),
docs/ercot-multiproduct-as-coopt-2026-06.md, docs/ercot-as-forward-requirement-2026-06.md,
src/market_sim/model/ancillary.py, the reserve rows in model/dispatch.py, and the
2026-07-03 calibration-log entry on the REJECTED AS-aware P2 probe (ercot27: broad price
elevation, no scarcity-month signal). Goal: the forward analogue for ERCOT's measured
DAM-AS overlay — the flagship gap (audit §J-T6). Design:
1. Multi-product AS co-optimization (RegUp/RegDown/RRS/ECRS/NonSpin) inside the P1 LP,
   vectorized, no per-hour Python loops.
2. Requirement-setting rules that regenerate for forecast years (G3): requirements as
   citable functions of load/net-load/wind per ERCOT methodology documents.
3. Load-resource RRS participation (G4) and the HSL completion remainder (P4).
4. FIRST diagnose why ercot27 failed and design against that failure mode explicitly.
5. Validation protocol: backcast 2023-2025 with co-opt REPLACING the measured overlay,
   scored on the same benchmarks; keeper decision per rule 1 (structure stays even if the
   fit dips — root-cause the dip, never revert the mechanism for the residual).
Produce docs/handoffs/ercot-as-coopt-plan-2026-07.md + staged implementation prompts.
Do not implement.
```

### F-4 `[FABLE]` — Fitted-scalar remediation + ablation/diagnostics program plan

```
Read CLAUDE.md rules 19-26, docs/model-legitimacy-audit-2026-07.md §3 (Class-C register
C-1…C-18) and §7 (D-3, D-10…D-14), docs/legitimacy-scrub-prompts-2026-07.md S3, and
docs/out-of-sample-results-2026-07.md §2B (D-8: coal sigmoid params pinned by single
years; CAISO SP15 and PJM ComEd temp-limbs with sign-flipping rho out-of-training).
Design the remediation program for the ~230 residual-identified scalars:
1. A written decision rule, then triage every C-item into: re-derive from source data /
   replace with a structural mechanism / neutralize / document-and-keep with a DOF-ledger
   entry and open root-cause issue.
2. Prioritize the D-8 red flags (sign-flip limbs, single-year-pinned sigmoids) and any
   remaining cross-ISO band leakage (rule 25).
3. Design the unbuilt diagnostics: D-3 zero-forcing ablation twin as a standard
   calibration-report step for every keeper (rule 21), and D-10…D-14 per audit §7.
4. Sequence so every re-derivation cites a source-data change (rule 23), never a residual.
Produce docs/handoffs/scalar-remediation-plan-2026-07.md + a prompt pack batched by
ISO/mechanism with model assignments. Do NOT retune or change any value in this session.
```

### F-5 `[OPUS]` — Sensitivity tornado + one-time MIP diagnostic benchmark

```
Read CLAUDE.md (rules 2/5/12 and the LP-only stack rule), docs/model-audit-prompt-pack-
2026-06.md PP-3.1/PP-3.4, and docs/fable-repo-audit-2026-07.md DP-1. Two diagnostics —
plan AND implement if runtime allows, else land the tornado and leave the MIP design:
1. Sensitivity tornado (PP-3.1): scripts/run_sensitivity_tornado.py — one-at-a-time
   +/- band runs of the top ~15 parameters (gas price, load growth, FOM thresholds, ORDC
   params, sigmoid anchors, carbon path) on one small ISO-year; outputs a committed report
   (annual CO2 / avg price / retirements sensitivity, ranked). Feeds the DOF ledger.
   Respect rule 12 (sequential years; max ~2 concurrent solves).
2. MIP cross-benchmark (PP-3.4): a ONE-TIME diagnostic script (production stays pure LP)
   using highspy integrality on the existing constraint matrix for one month x one ISO
   with unit commitment binaries on the committed tranches — quantify the LP-relaxation
   commitment bias: min-load energy, start counts, CO2 delta vs the P1 LP. Clearly label
   diagnostic-only; no production code path may import it.
Deliver reports under docs/handoffs/, tests for the tornado runner. Commit and push.
```

### F-6 `[SONNET]` — multi-iso docs triage + MISO coverage question

```
Read CLAUDE.md rule 16, then docs/multi-iso/ (57 files). Tasks:
1. Triage every file: living protocol/reference vs dated superseded status notes; output
   a file-by-file table (keep-in-place / move-to-sessions-archive) that the docs-reorg
   session (W3-P3 of docs/fable-prompt-pack-2026-07.md) can execute — do not move files.
2. Answer why MISO is absent from rule 16's multi-year keeper list (CAISO/PJM/NEISO/NYISO
   -> 2023-2025): check MISO bench coverage (data/raw, frontend/data/backcast/bench),
   registered MISO runs/keepers (frontend/data/backcast/registry, keepers.json), and
   whether 2023-2025 is currently solvable for MISO. Conclude: needs data intake, needs a
   calibration push, or needs a rule-16 amendment — with evidence.
3. List any multi-iso protocol steps the newer ISOs skipped.
Deliver docs/handoffs/multi-iso-triage-2026-07.md. Read-only otherwise. Commit and push.
```

### F-7 `[SONNET]` — Holdout-quarantine policy reconciliation memo (owner decision)

```
Read CLAUDE.md rule 22, docs/out-of-sample-results-2026-07.md, and the 2026-07-03/04
holdout-intake merges (PRs #1298/#1300/#1304 — inspect via git log and the PR diffs).
Rule 22's text ("FULL quarantine: no solves, no scoring, and no data intake" for 2022 and
H1-2026 until calibration-complete) now diverges from practice: 2022+2026 Waha rows,
coal/CO2 overlays, ERCOT outage windows, and zonal gas data have been intaken. Write a
one-page decision memo:
(a) inventory exactly what holdout-year data now exists in-repo and what remains missing
    per ISO for the one-shot validation;
(b) contamination-risk assessment: grep/trace whether any calibration code path can read
    those years outside explicit holdout scoring (loader year filters, bench builders);
(c) two policy options for the owner: strict re-quarantine (holdout files behind an
    explicit gate CI blocks) vs amended rule text (intake allowed; solves/scoring still
    forbidden) — each with its CI-enforcement sketch;
(d) recommend one, but end with the explicit owner decision required.
Deliver docs/handoffs/holdout-policy-memo-2026-07.md. Do NOT solve or score anything with
holdout years. Commit and push.
```

### PM-1 `[SONNET]` — Program coordinator (repeatable status session)

```
You are the program coordinator for the market-simulator improvement program. Read
docs/fable-prompt-pack-2026-07.md end to end (waves, Wave 0-B, Appendix register), then
determine live status: git log/branch list/open PRs for each workstream (Wave 0/0-B plan
sessions -> docs/handoffs/*-plan-2026-07.md existence; Waves 1-3 items; the in-flight
wiring-gaps waves and CAISO evening-merit thread). Update the Appendix register statuses
in place (FLAG -> IN-FLIGHT -> ABSORBED/done) with evidence (commit/PR refs), flag any
collisions (two branches touching the same files, duplicated fixes), and report: a short
status table, blocked items with their blockers, and the recommended next 3-5 session
launches in priority order. Commit the register update and push. Do not start any of the
work yourself.
```

## Coordinator status board — updated 2026-07-04 (PM-1 run 3)

**Since run 2:** the CO2-rate emissions track (owner priority) moved plan → **implemented**
(PRs #1326/#1327/#1329): new `src/market_sim/data/emission_rates.py`, forward estimator +
LOYO harness (D3/D4), v2 per-plant rate artifact (ERCOT+5 ISOs), **R2** physical-HR CO2 basis
(EM-4 fix), **R7** NOx unit-contract fix (EM-2), R3 gross/net assertion, CAMPD 2018/2020
historical intake with quarantine guard, scope2 excess-headroom validation. Emissions
leftovers: **R4** carbon-seam (EM-6), **R5** CHP (EM-7), **R6** startup-CO2 (EM-5), full
NOx/SO2 export+verdict+dashboard wiring. **NEW top-priority consequence:** R2 changed every
unit's CO2 rate on a basis that feeds the merit order where carbon is priced → the six keepers'
CO2 verdicts are now on a superseded basis and must be re-scored (re-solved for CAISO/NYISO/
NEISO) under the new estimator (rules 15/16). W0-P2/P4/P5 plans and all of W1 remain OPEN.

## Coordinator status board — 2026-07-04 (PM-1 run 2)

Live status of every workstream against `origin/main` (all PRs #1307–#1325 merged; **no open
PRs**). Evidence in the Notes column is commit/PR refs.

**Headline: the planning layer is essentially DONE; the execution layer has barely started.**
All of Wave 0-B and most of Wave 0 produced merged plan docs, but Wave 1 (the CI/test/hygiene
guardrails that protect every number the plans will produce) is almost entirely untouched, and
three core Wave-0 plans were never written. Recommended next launches are at the bottom.

### Wave 0 — core planning (Fable)

| Item | Status | Notes |
|---|---|---|
| W0-P1 CO2-rate emissions plan | ✅ PLAN DONE | `emissions-co2-rate-plan-2026-07.md`; CAMPD intake landed (PR #1320). **Rate model NOT yet in src** (no `emission_rates` module) → W2-P1 open. |
| W0-P2 confirmed-retirement channel | ✅ PLAN DONE | `confirmed-retirement-plan-2026-07.md` (2026-07-05). Probe evidence: economic screen retires ZERO units 2026-29 in both ERCOT (floor-inert, CX-3) and PJM (profit-inert, CX-1); `bins_to_fleet` drops announced dates entirely. W2-P2 ready. |
| W0-P3 orchestrator unification | ✅ PLAN DONE | `orchestrator-unification-plan-2026-07.md` (PR #1324). Ready for W2-P4 stage-1. |
| W0-P4 forecast-validation program | ⛔ NOT STARTED | No plan doc. Blocks capacity hindcast + invariants (audit §J-T1, the biggest untouched program). |
| W0-P5 capacity-economics recalibration | ⛔ NOT STARTED | No plan doc. FOM/foresight/floor/DC-load (audit §C) unplanned. |
| W0-P6 scope2 roadmap | 🟡 PARTIAL/ADJACENT | No `roadmap-2026-07.md`, but scope2 storage-modeling audit + ADR 0017/0018 landed independently (PRs #1309/#1313). Roadmap doc still owed. |

### Wave 0-B — flagged items (all complete)

| Item | Status | Notes |
|---|---|---|
| F-1 probability-bounds plan | ✅ DONE | `probability-bounds-plan-2026-07.md` + prompts (PR #1319). |
| F-2 emissions mass-cap plan | ✅ DONE | `emissions-mass-cap-plan-2026-07.md` (PR #1321). |
| F-3 ERCOT AS co-opt plan | ✅ DONE | `ercot-as-coopt-plan-2026-07.md` + prompts (PR #1318). |
| F-4 scalar-remediation plan | ✅ DONE | `scalar-remediation-plan-2026-07.md` + prompts (PR #1317). |
| F-5 tornado + MIP diagnostic | ✅ **IMPLEMENTED** | Went past plan: `scripts/run_sensitivity_tornado.py` + ERCOT tornado report + MIP-UC crossbench artifacts (PR #1322). |
| F-6 multi-iso triage | ✅ DONE | `multi-iso-triage-2026-07.md` (PR #1314). |
| F-7 holdout-policy memo | ✅ DONE | `holdout-policy-memo-2026-07.md` (PR #1315) — **awaiting owner policy decision** (see FLAG). |

### Wave 1 — execution guardrails (almost entirely OPEN — the current gap)

| Item | Status | Notes |
|---|---|---|
| W1-P1 CI: pytest + gates on PR | ⛔ NOT STARTED | Only `lint.yml` triggers on `pull_request`; `audit_keepers`/`legitimacy_diagnostics` still in no workflow. Rule-22 CI claim still false. |
| W1-P2 scoring-integrity tests | ⛔ NOT STARTED | No `test_audit_keepers.py`; `score_co2` still untested. |
| W1-P3 hygiene sweep | ✅ DONE | `_szprobe.txt`/`configs_nyiso_jacobian/` deleted; `scratchpad_diag_evening.py` → `scripts/diagnostics/`; `configs_run20/` → `results/calibration/_configs/pjm_run20/`; `_caiso_class_lmp.py` → `scripts/probes/`; CLAUDE.md 6-ISO fix; CONVENTIONS.md collapsed; ~34 zero-ref scripts archived; DA-3 datatypes documented. |
| W1-P4 rule-24 literal migration | ⛔ NOT STARTED | — |
| W1-P5 LP solver hardening | ⛔ NOT STARTED | — |
| W1-P6 scope2 docs sync | 🟡 UNKNOWN | scope2 saw activity (PRs #1309/#1313); docstring reconciliation not confirmed. |

### Wave 2/3 — implementation & validation

| Item | Status | Notes |
|---|---|---|
| W2-P1 emissions CO2 impl | 🟡 PARTIAL | CAMPD intake done; forward rate model + NOx unit fix + tranche-decontamination not in src. |
| W2-P5 invariants + hindcast | 🟡 PARTIAL | Tornado delivered via F-5; **no `check_forecast_invariants.py`, no `run_capacity_hindcast.py`**. |
| W3-P1 statmode ×5 ISOs | 🟡 STARTED | MISO D-7 statmode probe landed (`2026-07-03-miso-statmode-d-7`); CAISO/PJM/NYISO/NEISO pending. |
| W3-P2 CAISO CT scrub | 🟡 IN-FLIGHT | See in-flight thread. |
| W2-P2/P3/P4, W3-P3/P4 | ⛔ NOT STARTED | Gated on W0-P2/P5/P3 plans + W1 guardrails. |

### In-flight threads (your active work — no coordinator action)

- **CAISO evening-merit (W3-P2 / legitimacy S2):** Levers A+B scored as PROBE, caiso-51 stays
  keeper (commit 1308b20); **ramp+LCR phase-1 REJECTED** — "ramp inert, drag D-2 FAIL"
  (b95369d), design merged awaiting owner review (PR #1323). The CT floor scrub is therefore
  still open — the rejection means the root cause isn't the ramp envelope.
- **NEISO winter fuel-inventory model** merged (PRs #1310/#1325), seasonal oil-burn budget.
- **Holdout-intake follow-ups** F1/F2/F5/F6 closed (PJM DataMiner 2026 + back-history, 25ea0fb).

### ⚠ Collisions / de-dup notes

1. **F-5 vs W2-P5 tornado** — F-5 already shipped the sensitivity tornado; **W2-P5 must drop the
   tornado and scope to invariants + capacity hindcast only.** (Register: absorbed.)
2. **F-4 scalar remediation vs CAISO evening-merit** — both touch CAISO drag/floor scalars; the
   ramp/LCR rejection (D-2 FAIL on drag) overlaps F-4's D-8 red-flag list. Sequence F-4's CAISO
   batch *after* the evening-merit thread settles a keeper, or they'll fight over the same limbs.
3. **F-2 mass-cap vs W0-P1 carbon-seam** — F-2 plan depends on the W0-P1 EM-6 decision; confirm
   the mass-cap plan references the CO2-rate plan's carbon-seam resolution before implementing.

### ▶ Recommended next launches (priority order)

1. **W0-P2 confirmed-retirement plan** `[FABLE]` — highest-value unstarted planning item; it's
   the owner's original data-intent question and nothing else covers it.
2. **W1-P1 + W1-P2 guardrails** `[SONNET ×2, parallel]` — every plan now queued will produce
   numbers that currently flow through untested scoring with no PR gate. Land these before the
   Wave-2 implementations, not after.
3. **W0-P4 forecast-validation program** `[FABLE]` — unblocks the capacity hindcast (the single
   biggest untouched validation program) and W2-P5.
4. **W0-P5 capacity-economics plan** `[FABLE]` — the §C material emissions-bias items (FOM,
   foresight, floor, DC-load) are unplanned.
5. **W1-P3 hygiene sweep** `[SONNET]` — cheap; clears the root clutter still on main.

Owner decision still pending: **F-7 holdout-quarantine policy** (strict re-quarantine vs amended
rule-22 text) — blocks the eventual one-shot validation gating.

---

## Appendix — Status of pre-existing plans: unfinished prompts still valid (flagged 2026-07-04)

Registered against repo intent (LP-only hybrid, ±10% asset-level emissions; scope2 = hourly
CFE matching). Verdicts: **FLAG** = still valid, not covered by any active wave or this
pack — needs an owner scheduling decision; **ABSORBED** = folded into a prompt above (don't
run separately); **IN-FLIGHT** = actively being worked on main; **STALE** = superseded,
archive. *(Update 2026-07-04 run 2: most FLAG items now have merged Wave 0-B plan docs and
moved to PLANNED — see the status board above; the table below is annotated in place.)*

### FLAG → mostly cleared by Wave 0-B (annotated)

| Source plan | Item | Current status |
|---|---|---|
| `model-audit-prompt-pack-2026-06.md` | **PP-1.1/1.2/1.3** scenario matrix + LHS/copula sampler + structural-error prior | ✅ PLANNED — F-1 `probability-bounds-plan-2026-07.md` (PR #1319). Implementation open; `ensemble.py` still weather-only. |
| `model-audit-prompt-pack-2026-06.md` | **PP-2.1** emissions mass-cap LP constraint | ✅ PLANNED — F-2 `emissions-mass-cap-plan-2026-07.md` (PR #1321). `get_active_policy_constraints` still `[]`; sequence after W0-P1 carbon-seam. |
| `model-audit-prompt-pack-2026-06.md` | **PP-3.1** tornado; **PP-3.4** MIP cross-benchmark | ✅ **DONE/IMPLEMENTED** — F-5 (PR #1322). Remove from open list. |
| `forecast-methodology-gaps-prompts-2026-06.md` | **P1/P1b/P5a/P5c/P4** ERCOT multi-product AS co-opt | ✅ PLANNED — F-3 `ercot-as-coopt-plan-2026-07.md` + prompts (PR #1318). Implementation open. |
| `legitimacy-scrub-prompts-2026-07.md` | **S3** Class-C ~230-scalar remediation | ✅ PLANNED — F-4 `scalar-remediation-plan-2026-07.md` + prompts (PR #1317). ⚠ collides with CAISO evening-merit limbs — sequence carefully. |
| `legitimacy-scrub-prompts-2026-07.md` | **D-3 ablation twins; D-10…D-14** | ✅ PLANNED — covered by F-4's diagnostics section. Implementation open. |
| `docs/multi-iso/` triage + MISO rule-16 gap | — | ✅ DONE — F-6 `multi-iso-triage-2026-07.md` (PR #1314). MISO coverage answered there. |
| CLAUDE.md rule 22 wording | Holdout intake-vs-text drift | 🟡 MEMO DONE, **owner decision pending** — F-7 `holdout-policy-memo-2026-07.md` (PR #1315). |

### ABSORBED into this pack (do not run the old prompt)

- `model-audit-prompt-pack-2026-06.md` PP-0.3 capacity hindcast, PP-0.1 statmode → **W0-P4/W2-P5/W3-P1**; PP-2.2/2.3 NPV entry-exit + revenue signal → partially landed in code (audit §C scorecard) + **W0-P5**; PP-2.4 startup emissions → **W0-P1/W2-P1**; PP-3.3 load-shape → the DC-block part of **W0-P5** (end-use reshaping remains a documented limitation).
- `forecast-validation-plan.md` Phases 1-5 → **W0-P4/W2-P5** (the plan doc should be marked superseded by the W0-P4 handoff when it exists). **Update:** the tornado/MIP part of W2-P5 is already delivered by F-5 (PR #1322) — W2-P5 now scopes to `check_forecast_invariants.py` + `run_capacity_hindcast.py` only.
- `legitimacy-scrub-prompts-2026-07.md` S2 CAISO CT scrub → **W3-P2** (and the in-flight caiso-evening-merit thread); S4 statmode → **W3-P1**.
- `code-docs-cleanup-plan.md` root/scripts hygiene + docs reorg → **W1-P3/W3-P3**; its C2 (python hygiene) and data-reorg W3-W5 remainders are minor — fold into W1-P3's session if time allows.
- scope2 `PLAN.md` §10 open items → **W0-P6/W3-P4**.

### IN-FLIGHT on main (2026-07-03/04 — no action, don't duplicate)

- `docs/audit-wiring-iso-gaps/fix-plan.md` waves (the active "market simulator audit"): note its June inventory predates the post-June drift overlays (MISO firm imports, NEISO coldsnap, CAISO bidir intertie/solar-shape/gas-coupling) — add them to the current wave's checklist or leave them for W0-P3's unified-pipeline stages.
- CAISO evening CT/CC merit thread: levers A (CC min-load SRMC floor) and B (DMM RA-import grounding) merged; ramp-envelope + LCR locational design awaiting owner review (PR #1306).
- Holdout-intake follow-ups F1/F5/F6 (`docs/out-of-sample-results-2026-07.md`); remaining: bench/fleet data for CAISO/MISO/NYISO/NEISO holdout years.

### STALE (verify-and-archive via W3-P3)

- Dated `*-session-prompt.md` / `*-handoff*.md` files under docs/ tied to keepers that have since been superseded (dam-offer-curve-tuning, ercot-2025-overshoot, ercot-lmp-cooling, ercot-offer-curve-merit-order, cross-year-warmstart-handoff) — confirm each thread's closing keeper/CHANGELOG entry, then move to `docs/sessions/`.

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
