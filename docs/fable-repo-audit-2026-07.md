# Fable Repo Audit — 2026-07-04

**Purpose.** Consolidated full-repo audit produced by an 8-way parallel crawl (data intake,
LP core, capacity expansion, dispatch/emissions methodology, testing/CI, docs/hygiene,
scope2 tool, prior-audit synthesis). It identifies where follow-up sessions should probe to
debug, refactor for efficiency, ensure consistency, and align data intake/processing with
intent. The companion prompt pack that turns these findings into scheduled work is
`docs/fable-prompt-pack-2026-07.md`.

**Relationship to prior audits.** This audit *extends* — does not repeat —
`docs/model-legitimacy-audit-2026-07.md`, `docs/model-audit-2026-06.md`,
`docs/forecast-methodology-gaps-2026-06.md`, and `docs/backcast-measured-data-audit-2026-06.md`.
Section J is a verified register of what those programs left open.

**Model intent (the yardstick for every severity call).** The main model is a deliberately
scaled-back LP-only hybrid (capacity expansion + production cost + dispatch) whose objective
is **asset-level emissions forecasting within ±10% in forecast years**, with honest
build/retirement economics, on runtimes far shorter than traditional tools. The segregated
`scope2-lce-portfolio` tool is an hourly-CFE-matching portfolio optimizer under
parameterized constraints. Findings are ranked by threat to those two objectives.

---

## Executive summary — top findings, ranked

1. **EM-1/EM-2: NOx and SO₂ are effectively unwired, with a likely ~2,000× NOx unit bug.**
   `results/export.py:121` exports CO₂ only; `compute_nox` (`results/emissions.py:84`) has no
   caller in `results/`; SO₂ tons are computed nowhere. `apply_plant_emission_rates` writes NOx
   in tonnes/MWh (`fleet.py:4577,4620`) while `plant_financials.py:71-72,376` consumes the field
   as lb/MWh. Two of the three target pollutants have no validated system output.
2. **EM-3: Forecast emission-rate provenance is frozen and self-contradictory.**
   `use_plant_emission_rates=True` (`scenarios.py:279`) is not mode-gated, so forecast years to
   2050 use pooled 2023-25 CEMS intensities forever (no SCR/scrubber retrofits, no degradation) —
   while CLAUDE.md L21 lists plant-specific CEMS rates as backcast-only. The doc and the code
   disagree; a provenance decision is needed.
3. **EM-4: Tranche "price-wall" heat-rate multipliers contaminate CO₂ rates.**
   `bins_to_fleet` books emissions at the tranche heat rate (`fleet.py:6298`), including the
   ×2.0–2.5 peak-pricing multiplier that `docs/binning-methodology.md:148,196-200` explicitly
   calls a pricing construct — biting every plant absent from the CEMS artifact, the legacy-bin
   fleet, and **all forecast new entrants**.
4. **RC-1: Retirement exogeneity is a fuel-type proxy, not the confirmed-vs-announced
   distinction the owner specified.** Fossil units ignore all EIA-860 announced dates by default
   (`capacity.py:196-235`, correct in spirit — announced retirements stay economic), but there is
   **no channel to force a genuinely confirmed fossil closure**, and the EIA-860
   retirement-status field is dropped at intake (`scripts/process_eia860.py:64,239-243,310-313`).
   COD/new-build handling is clean (construction-committed statuses only; month-precise COD ramp).
5. **TC-1: The CI-enforcement claims in CLAUDE.md rule 22 are aspirational.** No workflow runs
   pytest on PR (only `lint.yml`/ruff gates merges); `audit_keepers.py` and
   `legitimacy_diagnostics.py` implement the quarantine/D-9 gates correctly but are invoked by
   **zero** workflows. The emissions verdict scorer `score_co2`
   (`scripts/calibration_verdict.py:875`) — the headline metric — has zero test coverage.
6. **AR-1: Forecast/backcast orchestrator split (D-5 parity) is the load-bearing architectural
   debt.** `run_calibration_full.py` imports its solve core from `run_calibration.py` (layered,
   not copied), but that ~4,000-line backcast orchestrator (`_calibration_config` + `run_year`)
   lives in `scripts/` parallel to `src/market_sim/runner.py`. Mechanisms drift between paths
   (e.g. several CAISO/MISO/NEISO overlays wired only in calibration; cross-year warm-start built
   but unused by the forecast runner).
7. **CX-1: Going-forward FOM retirement bars are ~1.5–2.5× below ATB** (`scenarios.py:146-162`:
   ct 8 / cc 12 vs ATB ~21 / ~30 $/kW-yr) → systematic fossil under-retirement → forecast
   emissions biased high. A no-code parameter fix, but it must be co-calibrated with the
   scarcity/AS revenue level to avoid double-counting.
8. **EM-6: Carbon-price seam.** CAISO/NYISO/NEISO backcasts run with measured CARB/RGGI carbon
   in the merit order; forecasts get 0 unless `carbon_price_path` is set
   (`policy/carbon.py:23,66-84`). The model is calibrated with a carbon-shifted merit order it
   does not forecast with.
9. **CX-2: One-pass myopia vs steep load growth.** Entry/exit key off prior-year prices only
   (`runner.py:379-385,1123-1130`); with ERCOT near-term growth ~5%/yr the fleet chronically lags
   the ramp and incumbent fossil fills the gap. Cheap partial-foresight fixes exist (EWMA price
   blend; growth-scaled lookahead) that stay one-pass LP-only.
10. **V-1: The validation centerpieces remain unbuilt/unrun** (prior-audit open items, verified):
    capacity hindcast (no script, no reports), statistical-mode backcast run for only ERCOT of
    six ISOs, forecast invariant checker absent, holdouts unscored (quarantine + 4-ISO data gap).

Counterweight findings (things in better shape than expected): matrix builders are genuinely
vectorized (no hour loops anywhere); docstring compliance ~100%; CHANGELOG current; capacity.py
and dispatch.py have strong behavioral tests; the scope2 tool is mature (238 tests green,
end-to-end run works) — its gap is real-data validation and stale prose, not implementation.

---

## A. Emissions accounting (EM) — highest-priority domain

Orientation: for zero-carbon-price ISOs the CO₂ rate is a pure reporting multiplier (not a
dispatch driver), so emissions error decomposes cleanly into MWh error × rate error, and rate
error passes through 1:1. The rate path is the dominant lever.

**Owner direction (2026-07-04):** CO₂ takes priority over NOx/SO₂. For existing units,
forecast CO₂ rates should be tied to historic measured CAMPD performance — intake annual
unit-level rates back to ~2018 (excluding quarantined 2022/H1-2026) and predict forward
rates either as a multi-year forecast average or conditioned on the unit's model-simulated
operation (starts/stops + total generation matched to the statistically closest historical
year). This resolves EM-3's provenance question in favor of measured-CAMPD-with-conditioning
(admissible under rule 13: regenerates from forward drivers, responds to changed operation);
prompt W0-P1 of the companion pack owns the design. EM-1/EM-2 (NOx/SO₂) are demoted to the
cheap unit-contract bug fix now, full wiring later.

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| EM-1 | HIGH | NOx/SO₂ tons unwired in results; CO₂-only export; nothing scores NOx/SO₂ on the dashboard | `results/emissions.py:84` (no caller), `results/export.py:121`, grep `so2_tons` empty |
| EM-2 | HIGH | NOx unit inconsistency, possible ~2204× error (tonnes/MWh written, lb/MWh consumed) | `fleet.py:4577,4620` vs `plant_financials.py:71-72,376` |
| EM-3 | MED-HIGH | Forecast rates = frozen pooled 2023-25 CEMS; not mode-gated; contradicts CLAUDE.md L21; no retrofit/degradation path to 2050 | `scenarios.py:279`, `fleet.py:4555-4623,6571-6572` |
| EM-4 | MED | Tranche pricing multipliers (×2.0–2.5 peak, ×0.92 committed) contaminate CO₂ rates for CEMS-uncovered plants, legacy bins, and all new entrants | `fleet.py:6298`, `docs/binning-methodology.md:148,196-200` |
| EM-5 | MED | Startup emissions entirely unmodeled (startup cost is amortized into bids; startup fuel/CO₂/NOx never booked) | `results/emissions.py:30`, `commitment.py:200-301` |
| EM-6 | MED | Carbon-price backcast/forecast seam (CARB/RGGI in calibration merit order, zero in forecast) | `policy/carbon.py:23,66-84` |
| EM-7 | MED | CHP must-run emissions use heat-rate-derived rate while grid tranches of the same plant use measured; forecast fallback fabricates BTM energy (`must_run_cf=0.85`) | `results/emissions.py:172-175` |
| EM-8 | LOW-MED | Gross/net basis: measured rates are per net MWh, bins derive from CAMPD gross; station-service bias ~2-4% gas / 7-10% coal if bases mismatch | `fleet.py:4576`, `egrid.py:66`, `binning-methodology.md:18` |

A 9-step executable "forecast-mode emissions-bias checklist" (rate-source ablation, new-entrant
rate audit, unit assertions, startup materiality, carbon-seam A/B, floor-share repricing, CHP
consistency, gross/net reconciliation, derate-vs-outage convexity) is embedded in prompt
**W0-P1** of the prompt pack.

## B. Retirement / COD data intent (RC)

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| RC-1 | HIGH | Exogenous-retirement gate keys on fuel type, not confirmation status; no channel to force a confirmed fossil closure (settlement/RMR/deactivation notice) | `capacity.py:196-235`, `scenarios.py:119` |
| RC-2 | HIGH | EIA-860 retirement-status/confirmation signal dropped at intake — the distinction is unrepresentable downstream | `scripts/process_eia860.py:64,239-243,310-313` |
| RC-3 | MED | "Known retirements" label is a misnomer: for the entire fossil fleet it is a default no-op | CLAUDE.md capacity-evolution step 1, `capacity.py:6-12` |
| RC-4 | MED | Forecast mode has no exogenous channel for confirmed future retirements at all (within-window retiree injection and COD ramp are backcast-gated); near-term confirmed exits rely entirely on the economic screen firing on time | `runner.py:293-295`, `fleet.py:1990` |
| RC-5 | LOW | Non-fossil announced dates are always honored, including speculative 2040-2072 60-yr-EOL placeholders (558 units carry planned years, 2026→2072) | `capacity.py:231-234` |

What is **right**: fossil announced retirements left to economics matches the owner's demand-
growth reasoning; `load_planned_additions` admits only construction-committed statuses U/V/TS
and excludes P (`fleet.py:3726-3806`); COD is month-precise and centrally sourced
(`cod_ramp.py:144-323`); EIA-860 2025 Early Release is loaded (staleness OK).

## C. Capacity expansion vs professional practice (CX)

Scorecard verdict: architecture structurally sound; most 2026-06 revenue-stream gaps are now
closed in code (capacity + AS + REC revenue in retirement/entry screens `capacity.py:490-529`,
gas_ct entry, price-duration thermal entry margin, reserve backstop, duration-aware storage
ELCC). Remaining material items:

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| CX-1 | MATERIAL | FOM going-forward bars ~1.5-2.5× below ATB → systematic fossil under-retirement; must co-move with scarcity-revenue calibration | `scenarios.py:146-162` |
| CX-2 | MATERIAL | One-pass myopia: screens see only prior-year prices; chronic lag vs 5%/yr growth biases emissions high; EWMA/lookahead fixes stay LP-only | `runner.py:379-385,1123-1130`, `capacity.py:1052` |
| CX-3 | MATERIAL-when-binding | Reliability floor is non-locational, accredits raw thermal nameplate (not ELCC/UCAP), and can non-economically retain coal; needs floor-vs-economic attribution logging | `capacity.py:553-569,1280` |
| CX-4 | MATERIAL-for-input-level | Demand growth is a uniform scalar on a frozen shape; data-center (flat, high-CF) and electrification loads not separately parameterized | `constants.py:598-634`, `runner.py:116-131` |
| CX-5 | minor | Loss-year counter vs discounted multi-year going-forward NPV (can over-retire in a transient dip); entry/CCS use single-year margin / simple payback | `capacity.py:541-547,1223,1487` |
| CX-6 | minor | Nuclear counted RPS-eligible (`dispatch.py:363-366`) — suppresses REC dual → entry signal where real RPS exclude it; uniform WACC across techs; VRE entry uses flat mean price (shape-blind) | `capacity.py:850-855,916-944,1228-1243` |

## D. Dispatch & commitment methodology (DP)

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| DP-1 | MED | P1 (the scored/forecast path) has pmin=0 on every tranche — min-load behaviour is emergent, not enforced; under-books min-load emissions, over-books cycling | CLAUDE.md L149, `binning-methodology.md:139` |
| DP-2 | MED | Two disjoint offer-curve engines (ERCOT 6-slice per-plant tranches vs 3 flat generic bands elsewhere) change which unit is marginal, inconsistently across ISOs; D-9 polices multiplier neutrality, not granularity | `offer_curves.py:162-227` |
| DP-3 | MED | Reserve-driven min-load energy invisible to emissions total in the default path (ORDC is post-solve; co-opt gated and CAISO-skipped; AS-aware P2 diagnostic-only) | `results/scarcity.py:6-9`, `runner.py:802`, `ancillary.py:13-14` |
| DP-4 | CONFIRMED-UNFIXED | CAISO generic reliability floor still binds all 24h on flagged days (prior-audit §1.2(a)); netload-limb CSVs carry no start/end hour | `transmission.py:2896` |
| DP-5 | PARTIAL | WECC 7,500 MW fitted cap still the forecast-path default (superseded only when deliverability limits ON) — a live re-arm surface vs rule 26 | `iso_configs.py:320-333` |
| DP-6 | LOW | Forecast outages are smooth fractional derates (energy-conserving, correctly backcast-gated) — convexity bias only; hydro budget default-off (confirm keeper configs) | `fleet.py:959,1007-1018`, `hydro.py:14-15` |
| DP-7 | FIXED | RA startup bridge now physics-gated (min-down ≥ 4h economic bridging; fast CTs excluded); CAISO RA must-offer now has forecast parity | `commitment.py:802-820`, `runner.py:913-914` |

## E. Architecture & LP-core code quality (AR)

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| AR-1 | HIGH | Forecast/backcast orchestrator split (D-5): `_calibration_config`+`run_year` (~4,000 lines) in `scripts/run_calibration.py` parallel `runner.py`; overlays drift (MISO firm imports, NEISO coldsnap, CAISO bidir intertie/solar-shape/gas-coupling wired only in calibration); consolidation = lift core into `src/market_sim/calibration/` | `run_calibration_full.py:100`, `runner.py:528-535,971-977` |
| AR-2 | HIGH | `run_scenario_iso` is one ~1,020-line function; `prior_results` an untyped 12-key dict threaded across years | `runner.py:134-1153` |
| AR-3 | MED | Incremental `sp.vstack` growth in `build_constraints` re-copies the full matrix ~8×; basis-apply materializes ~1.8M Python enum objects contradicting the int8 design note | `dispatch.py:1544-1684,2585-2586,1929-1931` |
| AR-4 | MED | Solver interaction unhardened: no pinned method/tolerances, bare-RuntimeError infeasibility, raw dual read with no degeneracy guard, no LMP hand-check regression test | `dispatch.py:2228-2244,2418-2423,2454` |
| AR-5 | MED | ~40-parameter passthrough chain restated in four signatures (needs `DispatchSpec`/`ReserveSpec`); pervasive `getattr(config, flag, default)` vs rule 24 | `dispatch.py:1297-1333,1996-2050,2684-2742`; `runner.py:536-1079` |
| AR-6 | LOW | Cross-year warm-start fully built but unused by the forecast runner; P2 rebuilds the matrix instead of reusing P1's basis; `cap` local shadowing; availability logic triplicated | `dispatch.py:1936-2589`, `dispatch.py:840,1033,1152,1757` |

Clean bill: no `for t in range(8760)` in any matrix builder; SOC cyclic wrap correct; the
in-place/`del A` peak-RSS mitigations are right.

## F. Testing & CI (TC)

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| TC-1 | HIGH | No pytest on PR (only ruff); `clean-parity.yml` weekly-cron subset only; rule-22 quarantine gates (`audit_keepers.py:86`, `legitimacy_diagnostics.py:799`) invoked by zero workflows; D-9 likewise | `.github/workflows/` sweep |
| TC-2 | HIGH | `score_co2` (verdict.py:875), `_pct` (:259), `_wmean` (:266), gating helpers (`_ledger_match`, `class_is_gated`, `family_is_complete`, `_agg_status`) untested — a bug silently corrupts every reported MAE; no `test_audit_keepers.py`; claimed D6-parity test doesn't exist | `scripts/calibration_verdict.py`, `audit_keepers.py:80-86` |
| TC-3 | HIGH | Forecast mode (2026-2050 evolution loop) has no end-to-end test — `test_runner.py` stubs the LP entirely; zero `derive_*.py` parameter scripts tested (they emit the frozen calibrated constants) | `tests/test_runner.py:23-64` |
| TC-4 | MED | Magic-number rot: `test_ancillary.py` asserts calibrated anchors literally (`== 169_000.0`); sweep needed | `tests/test_ancillary.py:30,45,54` |
| TC-5 | LOW | No solve-time or peak-RSS regression guard anywhere | — |

Draft test-plan skeletons (forecast invariants, golden scenarios, AEO/ReEDS cross-benchmarks,
scoring-integrity cases) are embedded in prompts **W1-P2** and **W2-P5**.

## G. Data contract & hygiene (DA)

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| DA-1 | HIGH | Per-plant heat-rate literals in the offer path (`MIXED_FACILITY_STEAM_HR`) — rule-24 off-registry channel | `fleet.py:467` |
| DA-2 | MED | Per-plant/per-year forced derates hardcoded (`BIN_FORCED_DERATE_BY_YEAR` — Martin Lake/Braunig/Sandy Creek 2025); belongs in the outages datatype | `fleet.py:4320-4335` |
| DA-3 | MED | Six datatypes have schemas but no `curate_*.py` (border-lmp, fuel-basis, fuel-ercot-ep-gas, fuel-hub-monthly, fuel-takeorpay, fuel-zonal-hub) — derive-owned, contract undocumented | `data/dictionary/schema/` vs `scripts/` |
| DA-4 | LOW | `_FLEET_GROUP_OVERRIDE` classification literal; zonal-gas-hub coverage missing CAISO/NEISO (confirm import-priced is intentional); clean seam (`MARKET_SIM_USE_CLEAN`) default-OFF so the default path bypasses `data/clean` | `outages.py:466`, `eia_loader.py:225,268` |

No `Path(__file__).parents` violations anywhere in `src/` — all paths resolve through
`config/paths.py`.

## H. Docs & repo hygiene (DOC)

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| DOC-1 | LOW | One factual drift found in six spot-checks: CLAUDE.md "7-ISO topology" vs 6 registered builders | `iso_configs.py:875-882` |
| DOC-2 | LOW | Root clutter: delete `_szprobe.txt` (inert base64 push-size probe, 0 refs) and `configs_nyiso_jacobian/`; relocate `scratchpad_diag_evening.py` and `configs_run20/` | grep-verified |
| DOC-3 | MED | ~52 of 91 top-level docs are dated session notes, 35-45 superseded; reorg proposal (reference/sessions/audits/calibration) exists but any move must update hard-coded paths in CLAUDE.md/spec/CI in the same commit | docs census |
| DOC-4 | LOW | CONVENTIONS.md is a strict drift-prone subset of CLAUDE.md; CLAUDE.md restates spec §5.x at paragraph length; rules 17-26 dual-numbering offset is a drift trap | — |
| DOC-5 | INFO | CHANGELOG maintained (103 entries, current); docstring compliance ~100% (103/103 sampled); dashboard workflow documented in 4 places outside CLAUDE.md | AST check |
| DOC-6 | MED | ~24 dead one-off scripts (numbered `run_*` drivers, closed `probes/`) are archive candidates; `_caiso_class_lmp.py` stray at scripts top level | 0-ref grep |

## I. Scope2 CFE portfolio tool (S2)

State: **mature and working** — 238 tests pass in ~79s; sample sweep runs end-to-end with a
monotonic premium-vs-matching frontier; vendoring discipline (pinned upstream commits, parity
tests) is exemplary; LP is vectorized HiGHS IPM with documented ε-tiebreaks.

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| S2-1 | HIGH | No real priced result ever produced — all runs on dummy LMPs/synthetic CF; profiles dir empty; real-forecast path ON HOLD | `data/inputs/bau_lmp_2026_dummy.csv`, PLAN.md §10 |
| S2-2 | MED | Stale docstrings claim features are unimplemented that are live (`additionality_only` "no effect" — false, `lp.py:224-233,376-400`; hydro budget "lands in PP-02b" — landed `lp.py:346-374`; split storage; "147 tests" vs 238; `data/emissions/` "REMOVED" but present) | `config.py:99-104`, `resources.py:20,231-232` |
| S2-3 | MED | LP optimizes matching %, CO₂ is report-only attributional (defensible EnergyTag/GHG-P stance) — cannot answer "most-abatement portfolio"; marginal-rate/emissionality option is the natural extension | ADR 0013 |
| S2-4 | MED | Crossover-off IPM ⇒ non-unique build mix/duals on degenerate faces at reporting points | `lp.py:695-698,517-529` |
| S2-5 | MED | Single node per ISO — no deliverability/congestion, the credibility crux of 24/7 CFE | PLAN.md §2 |

## J. Prior-audit open-items register (verified 2026-07-04)

- **T1 Validation:** capacity hindcast unbuilt (no scripts, no reports dir); statistical-mode run
  ERCOT-only; forecast invariant checker (`check_forecast_invariants.py`) absent; holdouts
  unscored (quarantine + CAISO/MISO/NYISO/NEISO 2022/H1-2026 data gap; ERCOT+PJM intake landed
  2026-07-04).
- **T2 CAISO CT scrub (S2 of legitimacy pack):** still in diagnosis (caiso-52); all-24h floor
  limb live (`transmission.py:2896`); SP15 temp-limb ρ sign-flips unresolved.
- **T3 Fitted-scalar remediation:** ~230 Class-C scalars mostly untouched; diagnostics
  D-3/D-10…D-14 unbuilt.
- **T4 Probability machinery:** `ensemble.py` weather-only (no LHS/copula);
  `get_active_policy_constraints` returns `[]` (mass-cap unbuilt).
- **T5 Capacity fidelity:** below-ATB FOM (=CX-1); NPV/hysteresis entry-exit open.
- **T6 Forward analogues:** ERCOT flagship multi-product AS co-opt (G1/P1), AS
  requirement-setting (G3), load-resource RRS (G4), MISO neighbor-HR elasticity (G11).
- **T7 Data intake blocking validation:** 2022/H1-2026 bench+fleet for four ISOs; F1-F6 of
  `docs/out-of-sample-results-2026-07.md`.
- **T8 Governance:** CEMS-overlay re-armability; 439 needs-citation flags; `COAL_SIGMOID_DEFAULTS`
  invisible to the citation system.

---

*Produced 2026-07-04 by a Fable session (8 parallel repo-crawl agents + synthesis). Companion
prompt pack: `docs/fable-prompt-pack-2026-07.md`.*
