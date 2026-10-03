> Status: PROPOSED (2026-10-03) — feasibility assessment for a MILP unit-commitment (UC) stage. Zero LP spent; every number is read from committed records, keeper bundles, source, or a 0.01 s toy MIP run against the pinned `highspy==1.14.0` to verify the API. Nothing in `src/`, `scripts/`, the spec, `CLAUDE.md`, any keeper, matrix shard or rubric was touched. Companion: `docs/uc-milp-program-plan-2026-10.md` (the plan), `GATESPEC-uc-milp-testing-protocol-2026-10-03.md` (benefit screen, wallclock ladder, A/B gates), `CHARTER-uc-milp-desk-protocol-2026-10-03.md` (the orchestrator desk), `HANDOFF-uc-milp-desk-2026-10-03.md` (paste-whole prompts).

# FEASIBILITY — a MILP unit-commitment stage for the market simulator

## 0. Verdict in six lines

1. **Feasible with the pinned stack.** HiGHS 1.14 (`highspy`) is a MILP solver; integrality, gap/time options, warm start (`setSolution`) and fixed-integer re-solve for duals all work (§3). No new dependency; the stack rule (direct CSC → HiGHS, no Pyomo/PuLP) is untouched.
2. **Layer, do not rebuild.** The UC belongs at the existing P0→P1 seam as a third stage: P0 (annual LP) → **UC (rolling-horizon MILP, chooses the commitment)** → P1 (annual pricing LP, commitment injected as per-unit-hour bounds through the `p1_fleet_prep` hook the three commitment bridges already use). P0/P1, the bundle format, every diagnostic and rule 4 (prices = P1 duals) stay as they are (§4).
3. **A full-year MILP is out of reach; a rolling day-ahead window is not.** The annual LP is 22–30 M columns and takes 2–24 min per ISO-year at 4–13 GB (§5). A 36-hour window is ~90–120 k columns with 4–9 k integer columns; the one in-repo MIP bench solved 744 h × 40 binaries-per-hour to a 1.5e-7 gap in 68 s (§5).
4. **The integrality gap is the whole phenomenon the LP cannot express.** The posture family (the relaxed clustered UC already in `rows.py`) holds 3.7–4.2× the measured online capacity because fractional commitment is free; a no-load cost on a continuous online variable collapses to an energy adder and "cannot decommit by construction" (PJM decommit lane). Only integer state makes start and no-load costs fixed costs (§2).
5. **What it will and will not fix is partly known.** Price-taker binary DP bounds already show the *energy* effect of commitment physics is small for SPP CC 2021/22 and not year-discriminating for PJM coal 2019–21. The open promise is **price formation** (trough depth, body level, negative hours, reserve scarcity, uplift) and **forecast realism**, measured by the testing protocol before anything is armed (§6).
6. **Governance, not code, is the gate.** `CLAUDE.md` "Dispatch and commitment" and spec §1.6 state "pure LP, no MIP". That sentence needs an owner ruling and a rule-history entry before the engine lane is chartered (§7).

## 1. What the model does today (commitment)

| Layer | What it is | Where | Standing verdicts |
|---|---|---|---|
| P0 → markup → P1 | Two annual 8760 LPs, perfect foresight, `pmin = 0` on every tranche (DP-1); start cost enters P1 as an amortized $/MWh markup | `pipeline/solve.py::run_energy_solve` (`:342`), `model/lp/model.py` (`Highs()` `:677`, `h.run()` `:1392`, `row_dual` `:1479`) | THE scored run everywhere |
| Floors (`min_gen`) | 27 injector ids compose an `(n_gen, T)` hard floor; D-2 attributes energy at binding floors | `data/floor_mechanisms.py` (ids 1–27), `FleetArrays.min_gen` (`data/fleet/__init__.py:433`) | rule 17/19/20 governed |
| Commitment bridges | A *detector*: finds P0 run patterns, floors gaps shorter than min-down at measured min-load, injected at the seam via `p1_fleet_prep` | `pipeline/commitment.py` (CAISO `:328`, ERCOT `:516`, NYISO `:1193`, SPP `:1386`, PJM `:1512`), `model/commitment.py::caiso_ra_mustoffer_min_gen` | CAISO K (armed), ERCOT K, NYISO K, SPP R, PJM R |
| Posture family | In-LP **continuous** online capacity `U[p,t]`, start `SU[p,t]`, min-load, start counting; SPP adds min-up/min-down rows | `model/lp/rows.py::_build_posture_energy_rows` (`:1214`), `model/reserves/spec.py::_posture_pool_params` (`:1178`) | MISO R (3.7–4.2× measured online), ERCOT R (price-inert), PJM R (2.66–3.14× headroom), SPP R (unpaired); no keeper arms it |
| P2 (archived) | Heuristic screen between LP solves, availability zeroed in decommitted hours | behind `--enable-legacy-p2` | no keeper uses it |
| MIP bench (deleted) | `scripts/archive/diag_uc_mip_crossbench.py` built a true MIP on the captured LP for one ERCOT month | records survive: `docs/records/ercot/mip-uc-crossbench-ercot-2026-gas_cc-mlf{100,050}-2026-07-04.md` | diagnostic only |

The closeout plan (`docs/backcast-closeout-plan-2026-10.md` §1) names the remaining misses the energy-only LP cannot express: *"commitment-state or operator-conduct phenomena … (PJM coal loading, SPP 2019–20 body, ERCOT 2023 ECRS era, MISO 2020 low-load margin)"*, and its wave 4 reserves a frontier statement *"naming the mechanism the model class lacks (commitment state / MIP …)"*. The NWPP block states the gap exactly: *"the commitment decision without MIP (a P1 bridge injects a detected state, not a chosen one)"* (`:267`).

## 2. What integrality changes, and what it does not

```
                    continuous U (posture, today)            integer u (MILP)
 min-load          P >= mlf·U, U free in [0, cap]           P >= mlf·p̄·u, u ∈ {0..n}
                   → LP sets U = P/p̄ exactly: floor never    → floor binds whenever on
                     binds, "fractional online for free"
 no-load $/h       cost·U ≡ (cost/p̄) $/MWh adder            fixed cost of being on
                   → "cannot decommit by construction"       → multi-day off spells optimal
 start $           SU counted on a continuous ramp of U      one start per unit, lumpy
 min-up/min-down   rows exist (SPP) but bind on fractions    bind on whole units
 online capacity   3.7–4.2× measured (MISO-43)               = Σ online units (the measured object)
 reserve headroom  every available MW counts as online       only online MW count → scarcity can bind
```

Evidence for each row: `docs/multi-iso/miso-scarcity-posture-design-2026-07.md` header (3.7–4.2×); `docs/records/spp/DESIGN-spp-102-cc-commitment-state-2026-09-29.md` §3A (*"the relaxation can commit 10 % of a plant and dispatch it at pmin·0.1, so the tight-formulation choice is load-bearing"*); `docs/records/pjm/closeout-pjm-decommit/FINDING-closeout-pjm-decommit-phase0-2026-10-03.md` §2 ((a0) friction posture *"cannot decommit by construction"*; (a1) three-part with measured no-load does); `docs/codebase-site/data/mechanism-matrix.js:1517` (*"Pure LP, no MIP — the shared root cause behind dormant reserve pricing in PJM/MISO/NEISO/CAISO (fractional online capacity at near-zero cost)"*); `RESULT-spp-96` §3 via the SPP closeout shard (*"all ~17 GW of available thermal counts as spinning, and a 2–3 GW reserve row never binds"*).

Two records state the boundary in one sentence each: PJM-82, *"Honest online-level collapse needs integer commitment… a representation boundary"* (`docs/records/pjm/pjm-commitment-posture-port-2026-07.md:144-153`); SOCO-92, *"A no-load cost can reach an LP price only through a commitment state"* (`docs/records/soco/r-soco/FINDING-soco-92-two-part-2026-09-30.md:10-31`).

**What integrality does not change.** Forecast error (the model commits on actual load; ISOs commit on a forecast), 5-minute scarcity (C3c tails), offer markups, and self-commitment at a loss (SPP MMU: 36/31/30 % of 2020–22 energy self-committed; PJM coal ran below going cost in 2023/24 as often as in 2019–21). A UC chooses the *economic* commitment; conduct beyond economics stays a frontier.

## 3. The solver (verified 2026-10-03, pinned `highspy==1.14.0`, toy 2-cluster × 6-h MIP, 0.01 s)

| Need | highspy 1.14 surface | Verified |
|---|---|---|
| integer columns on a CSC model | `changeColsIntegrality(n, idx, [HighsVarType.kInteger]*n)` | `kOk`, optimal, integer `U` returned |
| gap / time / tolerance control | `mip_rel_gap`, `time_limit`, `mip_feasibility_tolerance`, `threads` | all `kOk`; `getInfo().mip_gap`, `.mip_node_count` readable |
| warm start from the previous window | `setSolution(HighsSolution)` with `value_valid=True` | accepted; re-solve finished at 0 nodes |
| prices | a MIP returns **no duals** (`dual_valid=False`) | fix integers at their values, drop integrality, solve the LP → `dual_valid=True`, balance duals = the marginal unit's offer |
| stack rule | direct CSC → HiGHS, no modelling layer | unchanged; `uv.lock` unchanged |

The pricing fact is the architectural one: **the MILP cannot be the scored run** (rule 4 `[R-DUALS]`). A pricing LP with the commitment fixed is required, and P1 already is that LP once the commitment enters as bounds.

This is also what the standing "no MIP" position protects. Spec §1.9 calls pure LP *"the model's sharpest deliberate divergence from commercial UC practice, and it is what makes duals available everywhere"* (`model-methodology-spec.md:428-432`); the PJM frontier ruling restates it (*"(a) No MIP — the Stack mandate is untouched"*, `docs/calibration-log/governance.md:2730`); the October audit lists it as owner-ruled (`docs/audit/third-party-audit-2026-10.md:111-116`). The layered design keeps duals available everywhere because the MILP never prices: every price, REC, allowance and water value is still a P1 dual. The October audit's own comparison row says the same of ISOs: *"SCUC is a MIP and SCED is an LP with commitment fixed; prices are duals of that fixed-commitment LP"* (`docs/audit/2026-10/A-lp-dispatch-commitment.md:80-81`), and its open ask O-B (*"accept relaxed-LP pricing… or charter a convex-hull/uplift diagnostic"*, `:151-155`) is answered by the uplift sidecar in §4.

## 4. Layer or rebuild — the four forms

| Form | What changes | Tractable | Rule 4 | Verdict |
|---|---|---|---|---|
| **A. UC stage at the P0→P1 seam** | new `model/uc/` (window builder slicing the existing vectorized blocks + integer columns + MILP solve) and `pipeline/uc.py` producing a `p1_fleet_prep` hook; P0/P1 untouched | yes (§5) | yes — P1 duals, as today | **recommended** |
| B. P1 itself as a year-long MILP | 8760 × clusters × 3 integer columns on a 22–30 M column model | no (HiGHS, 4 vCPU / 15 GB) | no duals; needs A's pricing pass anyway | rejected |
| C. DA/RT two-settlement rebuild | new engine; every floor, bridge, diagnostic and governance object assumes P0/P1 | months of engine work | yes, eventually | deferred; A *is* the DA stage, an RT re-dispatch can be added later |
| D. make the posture `U` integer in-LP | pools are zone×class capacity, not unit counts; still a year-long MILP | no | no | rejected; its parameter plumbing (`_posture_pool_params`, mlf sources, fast-start gate, start tables) is reused by A |

How A sits in the existing pipeline:

```
 run_energy_solve (pipeline/solve.py)
   P0 ─ annual LP, base cost ───────────────► r0 (dispatch, duals, SOC, water values)
                                                 │
                        ┌────────────────────────┘
                        ▼
   UC stage (NEW, gated `unit_commitment_milp`)
     for each window w = [t0, t0+W+L):  slice the LP blocks (rule 2 kron), add u/v/w per slow-start cluster,
        boundary from r0 (SOC targets, cascade levels, annual duals as prices), initial state from w−1,
        warm start from w−1 → HiGHS MILP (gap ≤ uc_mip_rel_gap, time ≤ limit, log gap/nodes/s)
        keep the first W hours of u                          → schedule u[c,t] ∈ {0..n_c} for all 8760 h
                        │
                        ▼
   p1_fleet_prep(r0) ─ availability·(u/n) as the ceiling, mlf·p̄·u as min_gen (MECH id 28) ─► floored fleet
   P1 ─ annual LP, bid cost, warm from P0 basis ───────────► THE scored run (prices = duals, unchanged form)
   sidecars: hourly/uc_schedule_<y>.parquet, uc_solve_log.json, hourly/uc_uplift_<y>.parquet
```

Integration facts the engine lane inherits (explorer read of HEAD `dd28b645`): `FleetArrays` carries no min-up, min-down or start-cost field (`data/fleet/__init__.py:404-463`); `Generator.min_run_hours`/`min_down_hours`/`startup_cost_per_mw` exist on the committed anchor tranche only, from `data/raw/reference/custom-bin-assignments.csv` for ERCOT and from `BIN_STARTUP_COST_PER_MW` + NREL tables elsewhere (the EIA-860 path sets min-run = min-down = 0, `campd_bins.py:3424`); measured per-ISO artifacts exist (`data/raw/_processed-legacy/campd_gas_commitment_params[_plant]_{CAISO,NYISO,SPP,PJM,MISO}.csv`: LSL fraction and run-length percentiles; `thermal_tranches_*.csv`: committed_pct). So the UC stage needs its own struct-of-arrays of cluster parameters (rule 6) built by a frozen derive (rule 23). `pmin_mw` is 0 on every tranche (`assembly.py:1579`); min-load exists only through `min_gen`, which `_bridge_floored_fleet` composes by maximum and tags with a mechanism id (`pipeline/commitment.py:244-318`) — the UC injector follows that function exactly. Two row families couple adjacent hours and must carry the previous window's state: the ramp envelopes (`rows.py:993-1078`, armed in the PJM and NYISO keepers) and the posture/reserve online gates (`reserve_rows.py:263-284`, whose comment says the exact online gate *"needs an online binary"* — the UC supplies it). The LP is captured for benches by `scripts/diagnostics/bench_cold_solve.py` (pickles `(fleet, demand, build_kwargs, mc_base, mc_bid)` and rebuilds `DispatchModel` directly); the deleted crossbench added integrality to that same matrix, so the ladder's first rungs rebuild on this harness.

Rule 19: for the classes the UC commits, the P1 amortized start markup is zeroed (the `zero_posture_markup` precedent, `pipeline/solve.py:321`) and the commitment bridges / posture are refused at validation (the `spp_commitment_posture + spp_gas_commitment_bridge` refusal precedent, `scenarios.py:23815`). Fast-start CTs stay continuous with today's markup — the model's fast-start-pricing analogue. Start and no-load cost paid by committed units but not recovered in P1 prices is reported as uplift (make-whole), never added to the LMP.

## 5. Size and wall clock — what is known, what the ladder must measure

Known (wallclock baseline §WALLCLOCK 3a, main `d1aa877f`, 4 vCPU / 15 GB, HiGHS 1.14, one solve per box):

| ISO-year | P0 s | P1 s | total s | peak RSS GB | columns |
|---|---|---|---|---|---|
| NEISO 2023 | 80 | 27 | **135** | 4.3 | — |
| NYISO 2023 | 94 | 93 | **214** | 5.4 | — |
| SPP (2023–25 keeper) | — | — | ~**300–500** (order of NYISO) | — | — |
| PJM 2023 | 410 | 144 | **672** | 13.3 | — |
| MISO 2023 | 320 | 254 | **675** | 13.3 | 29.6 M |
| ERCOT 2024 | 298 | 575 | **979** | 12.8 | 21.8 M |
| CAISO 2024 | 638 | 738 | **1,428** | 8.1 | — |

(SPP row: no 3a entry; stated as an order of magnitude only, to be measured in the ladder.) Source: `docs/records/misc/wallclock-baseline-2026-07.md:1470-1486`; columns `docs/records/governance/FINDING-perfc-s2-p0-slim-2026-09-20.md:74`. Host noise on this container class is ±35 %, so phase structure and iteration counts are the signal, not seconds.

Known MIP point: ERCOT 2026, 744 h, 40 CC committed tranches integer (29,760 binaries), 628,680 columns / 196,550 rows → optimal, gap 1.55e-7, **68 s** (`mip-uc-crossbench-…-mlf050-2026-07-04.md`). Integrality bias vs the tight LP relaxation on that month: −283 MWh and 0 starts; vs production P1: +963 GWh committed min-load energy and −598 starts. Reading: with a *tight per-unit* formulation the root relaxation was nearly integral on that month; with the *pooled* posture it is 3.7–4.2× loose. The gap is formulation-dependent and must be measured per ISO-year, not assumed.

Window arithmetic (estimate, to be replaced by the ladder):

| Quantity | Estimate | Basis |
|---|---|---|
| continuous columns per hour | 2.5–3.4 k | 21.8 M / 8760 (ERCOT), 29.6 M / 8760 (MISO) |
| window W + L = 24 + 12 h | 90–120 k continuous columns | above × 36 |
| slow-start clusters (plant × class, CC + coal + ST_GAS, CHP and fast-start excluded) | ERCOT ~100, PJM/MISO ~200–250, SPP/NYISO/NEISO/CAISO/SOCO/NWPP 30–70 | fleet census, to be printed by the benefit screen |
| integer columns per window | 1–9 k (`u` only; `v`/`w` continuous) | clusters × 36 |
| windows per year | 365 | W = 24 |
| UC stage wall | 365 × (build + MILP) s; **unknown until measured** | the ladder reports it per ISO |

Memory is not the constraint: a window model is tens of MB against the 4–13 GB annual LP. Wall clock is. The ladder (`TESTING-PROTOCOL` §3) measures one window → one month → one year per ISO and reports the increase against the table above before any full-span shard is launched.

## 6. Where a UC can and cannot move the board

| ISO-year rows | Record diagnosis | UC-addressable? | Note |
|---|---|---|---|
| **SPP** C3a 2019 +11.5 %, 2020 +27.5 %, C3b 2020 0.343 | thermal online at sub-cost in troughs (3.3 GW more than model in the 936 negative-price hours of 2020; 77–83 % utility/IPP CC+ST part-loaded); self-commits 36 % of 2020 energy | **partly** — the economic commitment (start, no-load, min-up) is UC; the self-commit share beyond economics is conduct | primary target for the price body |
| **MISO** C3a 2020 +11.6 %, C3b 2021 0.201; reserve demand curves never reach their steps | "the LP may re-time any unit's energy at zero commitment cost"; posture relaxation 3.7–4.2× loose | **yes in form** — integer online capacity is the measured object the relaxation missed | primary target for reserve pricing |
| **PJM** C3a 2020 +12.4 %, 2022 −11.5 %, C3b 2022 0.253 | "commitment-cost representation change" (owner card pending, closeout §6.2); CT 2021 92.8 % of balancing credits = out-of-merit commitment; PJM-NEXT-15: the CC committed rung marginal in 11 % of 2020 low-price hours, a "fractional-commitment artifact" | **partly** — uplift accounting becomes possible; reliability commitments are conduct; PJM's own log warns *"a MIP would not close"* the reserve gate (reserve floor ≈ 5× requirement is a fleet property, `docs/calibration-log/pjm.md:552-557`) | secondary |
| **PJM** C1 COAL_BIT 2019–21 +18.7/+11.9/+17.1 TWh | decommit lane: every form removes as much coal in 2023/24 controls; "not year-discriminating" | **no** — measured, do not promise | frontier (R-56) |
| **SPP** C1 CC 2021/22 −9.7/−10.8 TWh | DP bound of perfect commitment physics: +0.8–0.9 TWh 2021, +0.1 TWh 2022 | **no** — bounded below the row's need | frontier; benchmark-basis ruling W5 |
| **ERCOT** C1 2019/20 CC +8.9/+10.4, PRB −10.5/−11.8; C3b 0.219/0.221 | coal vs CC merit through troughs; coal floors are conduct-derived (`coal_mustrun_per_plant`, sync) | **maybe** — a coal UC with no-load and start replaces conduct floors with a decision; rule-19 census first | secondary |
| **ERCOT** C3a 2023 −24.2 % | ECRS-era scarcity/offer conduct; ERCOT-163: CC fleet 96.4 % committed at the gap hours; evening online headroom 15–17 GW vs 0.9–2.8 GW real "because the LP carries no integer commitment" (`docs/mechanism-testing-matrix.md:957-965`); the relaxed posture was price-inert (ercot83) | **possible, unproven** — the thinness hypothesis has never been tested in integer form; not promised | tertiary; measured by the screen |
| **CAISO** C1 CC 2019–21 +10.8/+17.6/+10.2, C4 gas 0.36–0.41 | RA must-offer bridge detects P0 runs; "reach question closed" | **form change** — the UC would *replace* the bridge (rule 19), same object | secondary |
| **NWPP** C4 coal 2023 r 0.669 | queue row 4: "coal commitment bridge by parameters" | **yes in form** | secondary; no price reference |
| **SOCO** 2019 coal/CC self-commitment | take-or-pay contracts under vertical integration (R-45 lane) | **no** | contract conduct |
| **NEISO, NYISO** CALIBRATED | — | — | **controls**: no PASS→FAIL flip allowed |

The forecast side is not on the board but is the product: start/no-load costs, lumpy cycling, min-load emissions and reserve scarcity change every forward year's prices and the retirement screens that read them (spec §5). The program measures forecast parity on one small ISO (TESTING-PROTOCOL §5).

## 7. Rules — compatibility, by rule

| Rule | Reading | Action the plan takes |
|---|---|---|
| 1 `[R-STRUCT]` | a UC is a structurally real mechanism; it stays in even if a fit worsens | arm per ISO on structure; readings fixed ex ante |
| 2 `[R-VECTOR]` | window blocks are sliced from the existing kron builders; no per-hour Python loop in LP construction; the loop over 365 windows is a loop over solves | state this reading in the PRECOMMIT; owner confirms |
| 4 `[R-DUALS]` | the MILP has no duals; P1 remains the pricing LP | §3, §4 |
| 5 / 24 | every UC knob is a ScenarioConfig field in `run_config.json`; no env-var knob | §8 field list |
| 8 `[R-8760]` | the windows cover all 8760 h; P1 is full-year | — |
| 10 `[R-ONE-PASS]` | UC is one pass per year, no within-year convergence loop | — |
| 12 | windows run sequentially inside one shard (initial state carries); ISOs in parallel shards | — |
| 13 / 14 / 21 / 23 | parameters measured or published, zero fitted: start $/MW (NREL SR-5500-55433 class tables, `CC_COMMITMENT_PARAMS` `constants.py:328`; PJM `energy-offers` hot/cold start and `no_load_cost_usd_per_h`, class-level), no-load (CAMPD `heatInput = a + b·grossLoad`, PJM decommit B0 PASS: R² 0.96–0.98), mlf (ERCOT 60-Day DAM LSL/HSL 0.574; CAMPD WP-3 reconstruction; `MIN_STABLE_PCT_PHYSICAL` `:580`), min-up/min-down (CAMPD run lengths, SPP ASOM) | DOF ledger entries drafted in the PRECOMMIT |
| 17 | not a floor: the window is the LP's own commitment | — |
| 18 `[R-PHYSICS]` | integer set by physics: pool min-down > 2 h or start ≥ $30/MW (the posture gate inverted); CTs never integer | — |
| 19 `[R-ONE-MECH]` | replaces bridges and posture for the classes it commits; markup zeroed on those classes; coexists only with physical floors (nuclear, CHP steam); the coal conduct floors are decided by a per-ISO census | refusal rules at validation |
| 20 | not forced energy (the LP chose it); D-2 attributes it under its own MECH id for transparency | owner rules whether it is budgeted (card 4) |
| 27 | engine lane is Opus/Fable | — |
| 28 | one row `unit_commitment_milp` (+ sub-fields) with a cell in every shard; SPP/MISO/ERCOT/PJM `R` cells on `online_capacity_envelope`/`spp_commitment_posture` are *not* re-tested — this is a different object (integer state), entered as `U` | matrix PR in UC-1 |
| 31–36 | every solve in a shard, one per ISO-year, full bundle pushed, composed by the parent; shard budget set from the ladder | DESK-PROTOCOL |
| 37 | no rubric change | — |
| **CLAUDE.md "Dispatch and commitment" + spec §1.6** | "Pure LP, no MIP" is a methodology statement | **owner ruling required before UC-1**; proposed text in the plan §7 |

## 8. Proposed registry surface (names only; defaults off; final in the UC-1 PRECOMMIT)

| Field | Default | Role |
|---|---|---|
| `unit_commitment_milp` | `False` | the gate; per-ISO arming via `iso_configs` overrides later, with `--no-unit-commitment-milp` |
| `uc_window_hours` / `uc_lookahead_hours` | 24 / 12 | DA commitment horizon; declared, never swept against gates |
| `uc_mip_rel_gap` | 1e-3 | HiGHS gap; a solve stopping on the gap is optimal to tolerance |
| `uc_window_time_limit_s` | declared from the ladder | on hit: accept the incumbent, log the gap; a window with no incumbent is a hard stop |
| `uc_integer_scope` | physics gate (min-down > 2 h or start ≥ $30/MW) | which clusters carry `u` |
| `uc_noload_source` | `campd_regression` | no-load identification source; class table fallback where no CAMPD unit matches |
| `uc_boundary_mode` | `p0_targets` | storage SOC / cascade levels pinned to P0 at window ends |

Every field: a matrix row/cell, a `solve_surface_declared.py` registration, a `cache_key` entry, a test asserting the off-posture is byte-identical to today's P1.

## 9. Risks, stated

| Risk | Likelihood | Mitigation |
|---|---|---|
| UC stage wall > 3× the ISO's current year wall | medium (PJM/MISO) | efficiency levers E1–E6 (plan §4); widen W to 48 h (183 windows); month-parallel UC sub-shards as a last resort |
| a window hits the time limit with a poor incumbent | low–medium in scarcity weeks | log + accept; the ladder reports the gap distribution; a declared gap ceiling fails the run honestly |
| boundary approximation (P0 SOC targets) distorts storage cycling | medium for CAISO/ERCOT | A/B reports storage cycles vs P1; alternative `uc_boundary_mode` tested only if the A/B shows it |
| the integer commitment *worsens* a passing control year | real (PJM decommit lane: 2023/24 moved away) | pre-fixed no-flip bars on controls; arm per ISO only on structure + no PASS→FAIL |
| stacking with an existing floor doubles a phenomenon | real | rule-19 census per ISO before arming; validation refusals |
| the benefit is in form only (prices move < $0.5/MWh) | possible | that is a finding, not a failure; the UC stays default-off, cells go `I`/`R` with the evidence |

## 10. Documentation drift noticed while reading (not fixed here; for `/sync-docs` in a lane that owns the files)

| Where | What |
|---|---|
| `docs/codebase-site/data/mechanism-matrix.js:1520`, `mechanism-matrix/NEISO.js:38` | `legacy_p2` still reads `K` for NEISO; neiso-99 moved the keeper off P2 (`docs/calibration-log/neiso.md:2877-2893`) |
| spec §1.9 (`:450-456`), matrix `:2134` | say no keeper arms `ramp_limits`; the PJM and NYISO keeper `run_config.json` carry it `true` |
| spec §1.6 `:348`, `docs/audit/2026-10/G2-posture-family-spec.md` | matrix line citations drifted (1759→1768, 1642→1651; SPP.js 148→151, ERCOT/MISO.js 73→76) |
| `DESIGN-spp-102` §3A | calls P2 "the archived MIP commitment path"; P2 was a heuristic screen, never a MIP |
| `docs/RUNBOOK.md` §3 | `--leg results/calibration/<lane>_2023` is not the composer's syntax (`YEARS=bundle`), and the composer is MISO-specific; lanes copy it (106 copies under `scripts/probes/*compose*`) |
| `docs/governance/rule-history.md` | rule 36 has no genealogy entry; §19 still records the per-year fan-out as banned |
