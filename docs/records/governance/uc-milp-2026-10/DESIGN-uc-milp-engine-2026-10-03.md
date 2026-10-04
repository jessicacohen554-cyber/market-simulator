# DESIGN — the MILP unit-commitment engine (lane UC-1)

**Lane:** UC-1 · **Session:** `session_01TaYG9p5stirhcFVYgK3r6j` (Fable) · **Date:** 2026-10-03 · **Branch:** `claude/ucmilp-1-engine-mcst` off `origin/main` `fc83487f`.
**Charter:** `HANDOFF-uc-milp-desk-2026-10-03.md` block C, as issued by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`). **Plan:** `docs/uc-milp-program-plan-2026-10.md` §1, §2, §4, §5, §6. **Gates:** `GATESPEC-uc-milp-testing-protocol-2026-10-03.md` §3–§4. **Preconditions verified:** plan §8.1 R2 (D-1 signed); `origin/main:CLAUDE.md` carries the `unit_commitment_milp` clause (grep count 1).
**Status:** pushed before any code (task 1 of the charter). Every choice below is declared here first; the code implements it; nothing is tuned after a number exists. UC-0's FINDING (`FINDING-uc-milp-benefit-screen-2026-10-03.md`) is read from its branch `claude/ucmilp-0-benefit-screen-tx8t` (`a0558224`), not yet on `main` at the time of writing; §9 names what it changed here.

## 0. What is built, in one picture

```
 run_energy_solve (pipeline/solve.py)                               UNCHANGED unless unit_commitment_milp=True
   P0 ── annual LP, base cost ──► r0
   markup = compute_monthly_markup(...) ; markup = zero_posture_markup(...)
   ┌─ ONE HUNK (gated) ───────────────────────────────────────────────────────────────────────────────┐
   │ stage = pipeline.uc.prepare_uc_stage(config, fleet, fleet_arrays, demand, dispatch_kwargs,       │
   │                                      mc_base, r0, p1_fleet_prep)                                 │
   │ markup = stage.zero_markup(markup)            # integer clusters bid mc_base in P1 (rule 19)      │
   │ p1_fleet_prep = stage.p1_fleet_prep           # reads the final mc_bid at call time (late-bound)  │
   └──────────────────────────────────────────────────────────────────────────────────────────────────┘
   mc_bid = mc_base + markup (+ the P1-only adjustments, unchanged)
   p1_fleet_arrays = p1_fleet_prep(r0)   ──►  inside the hook, the UC stage runs:
        model/uc/params.py    cluster struct-of-arrays (rule 6) from data/clean/uc-params/<ISO> + the NREL tables
        model/uc/window.py    for w in 0..n_windows-1: slice every hourly kwarg to [t0, t0+W+L), build the window
                              DispatchModel (model/lp untouched), add u/v/w columns + logic/UT/DT/coupling rows,
                              pin boundaries (SOC, cascade, ramp, budget units), carry state from w-1
        model/uc/solve.py     HiGHS MILP (integrality, gap, time limit, warm start); log per window
        model/uc/schedule.py  keep the first W hours of u -> u[c,t] for all 8760 h; per-month checkpoint (E9)
        pipeline/uc.py        ceiling = avail·u/n, floor = mlf·p̄·u  ──► pipeline.commitment._bridge_floored_fleet(MECH 28)
   P1 ── annual LP, bid cost ──► THE scored run (prices = duals, rule 4) — unchanged builder, unchanged outputs
   sidecars IN THE BUNDLE via the orchestrators' drain: hourly/uc_schedule_<y>.parquet, hourly/uc_uplift_<y>.parquet (post-P1), uc_solve_log_<y>.json
```

The MILP never prices (rule 4). P1 is the same LP it is today with per-unit-hour bounds added through the same injector the three commitment bridges use.

## 1. Clusters (what carries an integer)

| Fleet type | Cluster | `n_c` (units) | `p̄_c` (MW per unit) | Members |
|---|---|---|---|---|
| EIA-860 per-plant fleets (every ISO but ERCOT) | one per `(plant_code, class family)` | `uc-params.n_units` for that plant and family; **1 when the plant has no uc-params row** | `Σ_members pmax / n_c` | every fleet row with that `plant_code` whose `plant_group` maps to the family |
| ERCOT CAMPD per-plant bins (`use_campd_bins`) | one per `(plant_code, class family)` across its tranches (must-run / committed / economic / peaking) | as above | as above | all tranche rows of the plant |
| legacy heat-rate bins (`plant_code == 0`) | one per fleet row | 1 | `pmax` | the row |

Class family from `plant_group`: `CC_REGULAR → cc`, `ST_GAS → st_gas`, `COAL_LIGNITE / COAL_PRB / COAL_BIT / COAL_WC → coal` (`plant_taxonomy.COAL_CLASSES`; there is no bare `COAL`), `CT_PEAKER → ct`. **Excluded from the candidate set** (never a cluster, rule 19: their committed state is owned by a physical floor or they have no commitment): `CC_CHP`, `CT_CHP`, `ST_CHP` (steam-host floors), nuclear, oil, hydro, renewables, storage, every interchange pseudo-unit (`pmax <= 0` or `pmin < 0`).

### 1.1 The E1 gate (integer set by physics, rule 18)

A candidate cluster carries `u` iff `dt_c > POSTURE_FAST_START_MIN_DOWN_H (2 h)` **or** `su_c >= POSTURE_FAST_START_STARTUP_PER_MW ($30/MW)` — the posture fast-start exemption of `model/reserves/spec.py::_posture_pool_params` inverted, read from the same two constants. `ct` clusters fail on their own physics (1 h, $12–25/MW, `CT_COMMITMENT_PARAMS`) and stay continuous with today's P1 start markup — the model's fast-start-pricing analogue. `uc_integer_scope = "physics"` is the only admissible value; a second scope is a new PRECOMMIT.

### 1.2 Parameters per cluster (all measured or published; rule 13/14/21/23)

| Symbol | Meaning | Source, in resolution order | Forward story |
|---|---|---|---|
| `n_c` | physical units | `uc-params.n_units` (CAMPD unit-level census, units with any operation in the pooled years) → 1 | unit census of the plant |
| `p̄_c` | MW per unit | fleet capacity / `n_c` (never the CAMPD HSL, so the LP bound and the coupling row agree) | fleet |
| `mlf_c` | min-stable fraction when online | `uc-params.mlf` (plant-basis LSL/HSL: p5 of online-hour plant load ÷ p99.5 plant load, the CAMPD WP-3 construction) → `MIN_STABLE_PCT_PHYSICAL[plant_group]` (WWSIS-2) | unit property |
| `su_c` | start cost $/MW | capacity-weighted member lookup exactly as `_posture_pool_params`: coal `BIN_STARTUP_COST_PER_MW[COAL_CLASSES[0]]`; gas `COMMITMENT_PARAMS_BY_FUEL[fuel]` by heat rate (NREL/SR-5500-55433) | class table |
| `nl_c,t` | no-load cost $/h per unit | `uc-params.noload_mmbtu_h / n_c` × the cluster anchor member's implied $/MMBtu, `(mc_base[g*,t] − vom[g*]) / heat_rate[g*]` (fuel + per-MMBtu emission charges, hourly); regression source = per-unit OLS intercept of CAMPD `heatInput` on `grossLoad` over online hours (closeout-PJM-decommit B0; UC-0 F7: R² median 0.96–0.99) → class fallback = the ISO's own fitted plants' capacity-weighted no-load MMBtu/h per MW of HSL (`uc-params` rows with `plant_code = 0`) | intercept is a unit property; re-priced by the forward fuel path |
| `ut_c` / `dt_c` | min-up / min-down h | `ut`: `uc-params.ut_h` (plant-basis run-length p25, CAMPD — an observed run bounds a min-run from above, the nyiso-90 / SPP-44 convention) → NREL class table `min_run_hours` (coal `COAL_BIN_MIN_RUN_HOURS` 36); `dt`: ALWAYS the published class value, NREL `min_down_hours` / `COAL_BIN_MIN_DOWN_HOURS` 16 (**amended 2026-10-03 before any shard**: the first NEISO window let CTs through the gate on their measured off-gap p25, which is how long a peaker chose to idle, not its restart bar; `uc-params.dt_h` stays a diagnostic column) | published physics |
| `a_c,t` | available fraction | capacity-weighted member `availability` | fleet |

`uc_noload_source = "campd_regression"` is the only admissible value. A cluster's resolved sources are written per cluster into `uc_solve_log_<y>.json` (`clusters[].src`), so the share of fallbacks is auditable in every bundle (DOF ledger row: no free parameter; the fallback share is reported).

### 1.3 The frozen derive (rule 23)

`scripts/data/derive_uc_cluster_params.py --iso <ISO>` reads `data/raw/campd-unit-level/<ST>_<year>.parquet` for the ISO's states (the fleet's `state` field union, pooled 2023–2025 as every CAMPD commitment derive in the repo) and writes `data/clean/uc-params/<ISO>` through `scripts/lib/clean_io.write_clean` under `data/dictionary/schema/uc-params.schema.yaml`. Columns: `plant_code, uc_class, n_units, hsl_mw, lsl_mw, mlf, ut_h, dt_h, noload_mmbtu_h, noload_units_fitted, noload_r2_median, online_frac, n_runs, years, source`. `uc_class` is the CAMPD unit-type family (`cc` = Combined cycle, `ct` = Combustion turbine, `st_gas` = boiler on gas/oil, `coal` = boiler on coal) — a data-contract token, never a model class. Class-fallback rows carry `plant_code = 0`. The derive re-runs only when the CAMPD source updates; the commit cites the data change.

## 2. The window formulation (plan §5, choices filled)

Per window `w`, hours `[t0, t1) = [24w, 24w + W + L)` clipped to `T`, with `W = uc_window_hours = 24`, `L = uc_lookahead_hours = 12` (the DA SCUC horizon, `DA_COMMITMENT_HORIZON_HOURS`, plus the plan's declared look-ahead). `n_windows = ceil(T / W)`; the last window is shorter.

```
min  Σ_t [ Σ_g mc_g,t·P_g,t + ε·(Chg+Dis) + dis_cost·Dis + VOLL·Slack + dump_cost·Dump + reserve terms ]   existing, sliced
     + Σ_c Σ_t [ su_c·p̄_c·v_c,t + nl_c,t·u_c,t ]                                                           NEW
s.t. energy balance, flows, storage SOC, renewables, reserve rows, ramp envelopes, LCR, interfaces            existing, sliced
     mlf_c·p̄_c·a_c,t·u_c,t ≤ Σ_{g∈c} P_g,t ≤ p̄_c·a_c,t·u_c,t                                               NEW coupling (2 rows per c,t)
     u_c,t − u_c,t−1 − v_c,t + w_c,t = 0            (t−1 = window state for t = t0)                          NEW logic
     Σ_{k=t−ut_c+1}^{t} v_c,k ≤ u_c,t ;   Σ_{k=t−dt_c+1}^{t} w_c,k ≤ n_c − u_c,t     (Rajan–Takriti; the pre-window part of each sum is the CARRIED history, entering as u bounds — §2.2)  NEW
     0 ≤ u_c,t ≤ n_c integer ;  0 ≤ v, w ≤ n_c                                                              NEW, integer set = E1
mc:  integer clusters at mc_base (start and no-load are explicit above); every other row at the final P1 bid mc_bid
keep u[c, t0 : t0+W]; advance W
```

The clustered-count form (`u ∈ {0..n_c}`) with continuous `v`/`w` is the compact tight formulation (plan E4). All rows are built as kron blocks over the window's hours (rule 2): the logic rows as `kron(I_T, D0) + kron(shift, D_prev)` (the posture-row construction in `rows.py::_build_posture_energy_rows` (c), without the cyclic wrap), the UT/DT rows as `kron(window_sum(width), selector)` per distinct width (its (d)/(e) construction), the coupling rows as `kron_hours(T_w, per_hour)` with the hourly `a_c,t` as a per-row scale. No Python loop over hours anywhere in LP construction; the loop over 365 windows is a loop over solves.

### 2.1 How the existing LP enters the window (model/lp untouched)

`model/uc/window.py::slice_window_inputs(fleet_arrays, demand, dispatch_kwargs, t0, t1)` returns the window `FleetArrays` (every `(n_gen, T)` field sliced), the window demand and the window kwargs, by one rule and one explicit table:

* **rule:** any `np.ndarray` whose last axis has length `T` (8760) is sliced on that axis — recursively inside tuples and lists (`interface_groups`, `local_capacity_specs`, `import_link_band`); scalars, `None`, per-unit arrays and per-link arrays pass through; `T=` is set to the window length;
* **dropped, replaced by a P0 pin (`uc_boundary_mode = "p0_targets"`):** the annual and monthly budget families — `hydro_monthly_energy/_min/_month_index/_period_hours/_gen_idx`, `oil_monthly_budget/*`, `coal_monthly_budget/*`, `coal_plant_budget/*` (+ `coal_plant_floor/_price`), `import_node_monthly_lo/_hi/_month_index/_gen_idx`, `hydro_envelope_*`, `storage_daily_cycle_hours`, `storage_alloc_*`, `mass_cap_*`, `rps_*`, `clean_region_*`. Every generator row governed by a dropped family is **pinned to its P0 dispatch** in the window (`min_gen = availability·pmax = P0 P[g,t]`): the LP's own perfect-foresight water/fuel/import allocation is the boundary condition, as plan §1 ("SOC, water values, duals → window boundaries"). The emission caps' and RPS rows' duals do not reach the window: `r0` is a slim P0 extract (PERF-C S2) that does not carry them, and the integer clusters' `mc_base` already carries every exogenous carbon/NOx price. Stated as the approximation it is; the UC-2 A/B reports storage cycles and budget-unit energy against P1.
* **refused** (validation, §5): posture kwargs (`posture_*`, `reserve_posture_*`) — the posture family cannot be armed with the UC.

The window `DispatchModel` is built from these slices (`model/lp/model.py`, the production builder on a 36-hour T). Then, on its HiGHS handle (`model._h`), `model/uc/window.py` adds the UC columns and rows with `addCols` / `addRows` and edits the boundary rows (§2.2). Nothing in `model/lp` is edited; `kron_hours`, `VariableLayout` offsets, `build_variable_bounds`, `build_constraints` and `build_cost_vector` are called as the public API they are.

### 2.2 Boundary handling

| Coupled state | Row today (cyclic over the year) | In the window |
|---|---|---|
| storage SOC | `SOC[s,0] − SOC[s,T−1] − η_c·Chg[s,0] + Dis[s,0]/η_d = 0` | located by its column pattern on the window LP (`getLp`), the `SOC[s,T_w−1]` coefficient zeroed (`changeCoeff`) and the row bounds set to `coef·SOC_init[s]`; **`SOC_init` = window w−1's SOC at its hour W−1** (self-consistent path), **first window: P0's `SOC[s, T−1]`**; **terminal:** `SOC[s, t1−1] ≥ P0 SOC[s, t1−1]` as a column lower bound (one-sided, so a window can never deplete the fleet below the LP's own plan; an upper pin would make a window infeasible for no physical reason) |
| hydraulic cascade pond volume `V[c,t]` (`hydro_cascade`) | same cyclic shape | same treatment; init from w−1 / P0, terminal lower bound at P0's level |
| ramp envelopes (`ramp_limits`) | rows for transitions 1..T−1, no wrap | sliced rows cover transitions inside the window; **one added row block for the t0 transition** with the previous hour's group dispatch in the RHS (`−RD_eff − P_prev ≤ Σ P[g,t0] ≤ RU_eff + P_prev`), `P_prev` = window w−1's kept dispatch at hour W−1, first window: P0's `P[g, T−1]` |
| commitment state `u` | — | `u_c,t0−1` = window w−1's kept `u` at hour W−1 (RHS of the t0 logic row); **first window:** `ceil(Σ_{g∈c} P0[g,T−1] / p̄_c)` clipped to `[0, n_c]` |
| min-up / min-down carry (**mandatory, rule 18 — UC-DESK review point 1; a start at hour 23 of window w can never be undone at hour 0 of w+1**; tested by `test_min_up_carries_across_the_window_boundary`) | — | from the kept `v`/`w` history of the last max(UT, DT)−1 committed hours. **Amended 2026-10-04 (UC-1-FIX, `FINDING-ucmilp-1-fix-window-infeasibility-2026-10-04.md`):** the history enters the Rajan–Takriti rows themselves as right-hand-side constants — `Σ_{lag<UT} v_c,τ−lag − u_c,τ ≤ −hist_v(τ)` and `Σ_{lag<DT} w_c,τ−lag + u_c,τ ≤ n_c − hist_w(τ)`, with `hist_v(τ) = Σ_{k=1}^{ut_c−1−τ} v_c,t0−k` and `hist_w(τ) = Σ_{k=1}^{dt_c−1−τ} w_c,t0−k` — so the carried and the in-window starts (stops) are summed in ONE inequality. The original design carried the history as **column bounds** `u ≥ hist_v`, `u ≤ n − hist_w` alongside window-only rows; the two constraints enforced separately let a window stop a unit still inside its min-up whenever another unit's earlier start satisfied the bound alone, the kept history accumulated more starts within one min-up than the plant has units, and a later window's bound exceeded `n` (every SPP year, UC-2-SPP kill #1). The bounds are kept as the implied root-relaxation tightening. **Added, same amendment — the look-ahead min-down guard:** for every hour `h ∈ [t1, t1 + DT_c − 1)` in which the structural floors need `floor_need_c(h) > 0` units, `Σ_{τ∈[t0,t1), h−τ<DT_c} w_c,τ ≤ n_c − floor_need_c(h) − hist_w(h)` — row (e) at an hour past the horizon with `u` replaced by its known lower bound, so a window never stops a unit that a floor it cannot see will need before the min-down expires (`floor_need_ahead`, zero LP, from the year fleet). Physics (rule 18): a stopped unit is unavailable for `DT` hours, and a structural floor is a known lower bound on the units online at `h`; the row brings a known input into the window's sight, it adds no new mechanism. A row exists only where `floor_need_c(h) > 0` and some window hour is within `DT` of `h` — with no floor past the horizon the family is empty and the model is the one built with no look-ahead (`test_guard_adds_no_row_without_a_floor_past_the_horizon`). First window: empty history |
| structural floors on members (`min_gen` from nuclear/CHP/coal must-run/reliability floors, all upstream of the hook) | column lower bounds, unchanged | kept as member lower bounds AND `u_c,t ≥ ceil(Σ_{g∈c} min_gen[g,t] / p̄_c)` as a column lower bound — a floor is an input the UC respects, never a decision it re-takes |

### 2.3 Warm start (E3) and pre-fixing (E5)

* **Warm start:** `setSolution` with a full column vector: hours shared with window w−1 take its incumbent shifted by W; new tail hours take P0's dispatch for the continuous blocks and `u = ceil(P0 cluster output / p̄_c)`, `v`/`w` from its differences. The root LP basis is not carried (a MIP re-solves its root). The log records nodes per window and the share of windows at 0 nodes. The ladder's L2 "warm on/off" arm toggles it through `solve_window(..., warm=False)`, a function argument, not a registry field: warm start cannot change the optimum, only the path, so it is not solve-affecting under the determinism pin (gap-tolerance ties excepted and measured by the L2 schedule hash).
* **Pre-fixing** (`uc_prefixing`, registry field, default **False** until L2 proves schedule equality): fix-ON when the cluster's P0 output is ≥ `UC_PREFIX_ON_LOAD_FRAC = 0.95` of its available capacity in every hour of the window **and** its P0 inframarginal rent over the window `Σ_t (λ_z,t − mc_g,t)·P0[g,t]` ≥ `su_c·p̄_c·n_c + Σ_t nl_c,t·n_c` (running clears a full restart plus the window's no-load); fix-OFF when `min_t mc_base[g*,t] ≥ max_t λ_P0[z,t] + UC_PREFIX_OFF_MARGIN_USD_PER_MWH = 10.0` and P0 ran the cluster at 0 in every hour. Both constants live in `model/uc/params.py` with their rationale (0.95 = the posture family's "ran at full output" reading, one tranche step below full; $10/MWh ≈ the largest P1 start markup a slow-start class carries, `compute_monthly_markup` on a 5-h CC run, so a cluster this far out of merit at base cost cannot enter at bid cost either). They are solver heuristics that cannot move a solution when correct; L2's schedule-hash equality across arms is the proof, and `uc_solve_log` records the count fixed per window.

### 2.4 Solve (E6, E7)

**As built (amended 2026-10-03, same lane, before any shard):** one fresh `DispatchModel` per window — the production builder on the slice, then the UC columns/rows added on its HiGHS handle. The incremental form (one model per window *shape* with `changeColsBounds` / `changeRowsBounds` / `changeColsCost` between windows) is **deferred**: reproducing the builder's kwargs→row-bounds mapping outside `model/lp` would duplicate 87 parameters of its contract, and the per-window build is logged (`windows[].build_s`) so rung L2 measures whether it matters before anything is duplicated. If `build_s` dominates `milp_s`, E6 is the next lever, declared in the ladder's PRECOMMIT. Options: `mip_rel_gap = uc_mip_rel_gap` (1e-3), `time_limit = uc_window_time_limit_s`, `threads` = `MARKET_SIM_HIGHS_THREADS` when the solve container pins it (the existing env, read exactly where `DispatchModel` reads it; the L2 threads arm sets it on the shard), `presolve` default (a MIP wants it; the annual LP's `presolve=off` reasoning does not transfer), `output_flag` off. **Time limit hit:** accept the incumbent, log the gap, count the hit; **no incumbent:** hard stop with the window named (GATESPEC §5 kill: an infeasible window is an engine defect). **Integer set empty** (G-EMPTY): no MILP is built; the schedule is "all available", the hook returns the input fleet object unchanged and the markup zeroing is a no-op — P1 is then the same object path as the gate-off run.

### 2.5 Stitching, checkpoint (E9), injection (MECH 28)

`schedule.py` keeps `u[c, t0:t0+W]` per window into an int16 `(n_c, T)` array plus `v`/`w`; after every completed calendar month the partial schedule and log are written to `results/uc/<ISO>/<year>/checkpoint_<month>.npz` so a shard near its budget always has an artifact (rule 32 stop rule). `pipeline/uc.py` turns the schedule into the P1 bounds:

* **ceiling:** `availability[g,t] · u_c,t / n_c` on every member of an integer cluster (the online share of the cluster's capacity); with `u = n_c` it is byte-identical to today's availability;
* **floor:** `min_gen[g,t] = mlf_c·p̄_c·u_c,t` allocated to the cluster's members in proportion to `pmax·availability` — a floor exists only where `u > 0`, so a floor binding where its own driver says the class is offline cannot occur (rule 17);
* composed by `pipeline.commitment._bridge_floored_fleet(fleet_arrays, floor, MECH_UC_SCHEDULE)` — maximum-composition with the id tagged where the composed floor strictly rose, availability raised to `min_gen/pmax` where needed, exactly as the bridges.

Order inside the hook: the chained upstream hook (if any survived validation — e.g. a PJM reserve kwargs hook's fleet half) runs first; the UC floor composes onto its result.

### 2.6 Markup zeroing (rule 19) and pricing (D-3 default)

`stage.zero_markup(markup)` zeroes the P1 amortized start markup on every fleet row that belongs to an **integer** cluster (the `zero_posture_markup` precedent, `pipeline/solve.py:321`); every other row keeps it. Integer clusters therefore bid `mc_base` (+ the P1-only additive adjustments, unchanged) in the scored run: their start and no-load costs were paid once, in the UC objective. Make-whole is reported, never priced: `uplift.py::compute_uplift(bundle, year, params, schedule)` is a zero-LP post-P1 function — per cluster-day, `max(0, Σ_t[mc_base·P1 + nl·u + su·p̄·v] − Σ_t λ_P1·P1)` — written as `uc_uplift_<y>.parquet` by the bench L3 harness and the compose script. D-3's alternative (keep the amortized markup on integer clusters) is not implemented; it would be a declared variant field in a later PRECOMMIT.

## 3. Registry (rule 5/24)

| Field | Default | Tier | Validation | Role |
|---|---|---|---|---|
| `unit_commitment_milp` | `False` | 1 | §5 refusals | the gate |
| `uc_window_hours` | `24` | 1 | `>= 1`, `<= hours` | W, the DA commitment horizon |
| `uc_lookahead_hours` | `12` | 1 | `>= 0`, `W + L <= hours` | L |
| `uc_mip_rel_gap` | `1e-3` | 1 | `0 < gap < 1` | HiGHS `mip_rel_gap` |
| `uc_window_time_limit_s` | `600.0` | 1 | `> 0` | HiGHS `time_limit`; **a placeholder until the ladder prints the wall table (D-2 re-declares it)**, large enough that L1/L2 measure the unconstrained solve |
| `uc_integer_scope` | `"physics"` | 1 | `in {"physics"}` | E1 |
| `uc_noload_source` | `"campd_regression"` | 1 | `in {"campd_regression"}` | §1.2 |
| `uc_boundary_mode` | `"p0_targets"` | 1 | `in {"p0_targets"}` | §2.1–2.2 |
| `uc_prefixing` | `False` | 1 | — | E5 |

Every field: `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` with the same source text, `TIER_TAGS`, the matrix row's `def` names all nine (`check_mechanism_matrix --base`), dropped from the key at their defaults so every committed `cache_key()` is unmoved (G-KEYS). No `--no-unit-commitment-milp` CLI flag in this PR: no ISO arms it in `iso_configs.py` (not mine to touch), so the pre-arm posture is the default; UC-2 arms via `replay_keeper.py --set` and the CLI flag lands with the first `iso_configs` arm.

## 4. Sidecar schemas

**Amended 2026-10-03 on the UC-DESK review (point 3; the desk granted two regions).** The engine hands its artifacts to the persisting orchestrator through `pipeline.uc.take_uc_artifacts(p1_result)` and the orchestrator writes them INTO THE BUNDLE with `pipeline.uc.write_uc_artifacts` — the two-line drain in `scripts/run_calibration_full.py` (the hourly-sidecar block, after `hydro_cascade`) and `src/market_sim/runner.py` (after `save_result`, flat cache layout), both under `if config.unit_commitment_milp` (G-DRIFT: INERT off, no statement runs). Paths: `<bundle>/hourly/uc_schedule_<y>.parquet`, `<bundle>/hourly/uc_uplift_<y>.parquet`, `<bundle>/uc_solve_log_<y>.json` (per year, so a composed span carries one per leg). Nothing is written under `results/uc/` any more; the monthly checkpoints (plan E9) are scratch under `results/uc-checkpoints/<ISO>/<year>/`, never a sidecar, never pushed. `scripts/probes/_ucmilp_compose_span.py` carries the hourly files with every other year-stamped sidecar, copies the log and computes the make-whole frame only for a leg that lacks it.

| File | Grain | Columns |
|---|---|---|
| `uc_schedule_<y>.parquet` | cluster × hour (long, zstd, delta-packed `hour`) | `year` int16, `hour` int32, `cluster` int32, `plant_code` int64, `uc_class` str, `u` int16 (units on), `n` int16, `v` int16 (starts), `w` int16 (stops), `online_mw` float32 (`u·p̄·a`), `floor_mw` float32 (`mlf·p̄·u`) |
| `uc_solve_log_<y>.json` | run + per window | `engine` {version, fields echoed, integer_set_size, n_clusters, integers_per_window}, `clusters[]` {cluster, plant_code, uc_class, n, pbar_mw, mlf, su_per_mw, ut_h, dt_h, noload_mmbtu_h, integer, src {n, mlf, ut_dt, noload}}, `windows[]` {w, t0, t1, build_s, milp_s, nodes, gap, status, time_limit_hit, incumbent_warm, fixed_on, fixed_off, objective, integers, columns, rows}, `summary` {uc_total_s, milp_s_mean/p95, nodes_p50/p95, gap_p95, time_limit_hits, windows_zero_nodes_share, peak_rss_gb, checkpoints_written} |
| `uc_uplift_<y>.parquet` | cluster × day | `year`, `day` int16, `cluster`, `plant_code`, `uc_class`, `energy_mwh`, `revenue_usd` (Σ λ_P1·P1), `energy_cost_usd` (Σ mc_base·P1), `noload_usd`, `start_usd`, `uplift_usd` = max(0, cost − revenue) |

Nothing here enters a price, a score or the rubric; the schedule enters P1 only as bounds.

## 5. Validators (`ScenarioConfig.__post_init__`, rule 19 by refusal)

**Amended 2026-10-03 on the UC-DESK review (point 2).** The refusal set is DATA: two declared tuples at module level in `config/scenarios.py`, `UC_REFUSED_ALWAYS` and `UC_REFUSED_BY_RULING`; `__post_init__` refuses any armed member of either when `unit_commitment_milp=True`.

* `UC_REFUSED_ALWAYS` (the plan §6 set): every `*_gas_commitment_bridge` (ERCOT, NYISO, SPP, PJM) and `miso_gas_ecomin_online_floor` (the same P0-detector object, so bridge class); `caiso_ra_mustoffer` with every `caiso_ra_*` leg that rides it (`caiso_ra_startup_bridge`, `caiso_ra_bridge_decommit`, `caiso_ra_mustoffer_quantity_gate`, `caiso_ra_bridge_startup_aware`, `caiso_ra_bridge_curtailment_release`, `caiso_ra_startup_trajectory`); the posture family (`ercot_commitment_posture`, `miso_commitment_posture`, `spp_commitment_posture`). The archived P2 is not a `ScenarioConfig` field (`commitment` is a `solve_and_persist` kwarg behind `--enable-legacy-p2`), so it is refused where it lives, by `run_calibration_full.enforce_legacy_p2_kwargs`, not here.
* `UC_REFUSED_BY_RULING`: **empty at birth**. Extended only by a commit citing an owner D-5 ruling for the ISO. Until then the A/B lane disarms the D-5 fields in its config delta.
* **Not refused by the engine** (owner card D-5, per ISO): UC-0 §4's "replace" recommendations `cc_mustrun_per_plant` and `soco_gas_st_campaign_commitment` and its hard cases (`st_gas_mustrun_per_plant`, `coal_mustrun` and its tranches, `ercot_coal_min_config_floor`, `miso_coal_night_floor`, the net-load drags); the physical floors (nuclear, CHP, hydro, imports, `reliability_floor`, `winter_fuelsec`). They compose by maximum through `_bridge_floored_fleet`; D-2 attributes each under its own id; the UC respects them as inputs (§2.2 last row).

## 6. Tests (docs/testing.md; trivial first) and benches

| Test | Where | Asserts |
|---|---|---|
| no-load → off spell | `tests/unit/model/uc/test_window_toy.py` | 1 cluster / 1 zone / 24 h, demand below `mlf·p̄` at night with a positive `nl`: `u = 0` in the trough, `u = 1` in the day; the LP relaxation puts fractional `u` there |
| UT / DT | same | a 2-hour price spike cannot start a `ut = 6` unit for 2 hours; a stop is held `dt` hours |
| warm start | same | re-solving the solved window with its own solution as `setSolution` finishes at 0 nodes |
| integer-empty ≡ LP | same | with every cluster failing E1, the window objective and dispatch equal the sliced LP's |
| off-gate byte-identity | `tests/unit/model/uc/test_offgate_identity.py` | `run_energy_solve` on a toy fleet with `unit_commitment_milp=False` returns `p1_fleet_arrays is fleet_arrays`, identical `mc_bid`, identical P1 arrays, with the stage never imported (a sentinel on the import) |
| injection bounds | `tests/unit/model/uc/test_injection.py` | ceiling `= avail·u/n`, floor `= mlf·p̄·u` allocated to members, mechanism id 28 where the floor rose, `u = n` ⇒ availability unchanged |
| compose | `tests/unit/model/uc/test_compose_span.py` | two toy legs → one bundle; sidecars folded; per-year `run_config_<y>.json` kept |
| captured window (`slow`) | `tests/unit/model/uc/test_window_captured.py` | NEISO 2023 hours 0–35 from the `bench_cold_solve.py` capture seam: the window builds, the MILP solves to the declared gap, the schedule injects, `requires_raw` |
| registry | `tests/unit/config/test_uc_fields.py` | armed key ≠ default key; every refusal above raises; defaults registered |

Benches (`scripts/lib/uc_bench.py`, `scripts/diagnostics/bench_uc_ladder.py --iso --year --rung L1|L2|L3 --bundle --out [--arms warm,prefix,threads]`): L1 one window with (a) MILP, (b) LP-relaxed, (c) the P1 slice; L2 Jan + Jul rolling with arms and schedule hashes; L3 the full stage through `run_energy_solve` on the keeper recipe with the GATESPEC §6.1 wall-table printer. This lane runs L0 (the toys) only; every rung is a shard. Bench order after merge (desk): SPP 2020, PJM 2022, SPP 2019; controls NEISO 2023 and NYISO 2024.

## 7. G-DRIFT classification claimed (rule 29; GATESPEC §4)

| Hunk | Path reached with the gate off? | Class |
|---|---|---|
| `pipeline/solve.py` — the one gated block after `zero_posture_markup` | `getattr(config, "unit_commitment_milp", False)` is `False` on every committed recipe; no statement inside runs; `markup` and `p1_fleet_prep` are the same objects | **LIVE, gated** (the only LIVE hunk) |
| `config/scenarios.py` — nine fields, cache-key/default/tier entries, `__post_init__` refusals | fields at their declared defaults are dropped from `cache_key()`; the refusals are under `if self.unit_commitment_milp:` | INERT |
| `data/floor_mechanisms.py` — `MECH_UC_SCHEDULE = 28`, name, ablation entry `{"unit_commitment_milp": False}` | a registry constant nothing reads on the off path; the ablation twin's overrides gain a no-op | INERT |
| `model/uc/*`, `pipeline/uc.py`, `scripts/**`, `tests/**`, docs, matrix | not imported on the off path | INERT |

Proof: nine golden shards (HANDOFF block E) at this branch's SHA with the gate off, golden-diff at `atol = rtol = 0` against each committed keeper bundle; the lines go in the PR body.

## 8. Routed to UC-DESK (named gaps, not hidden)

* **R1 — CLOSED by the desk's grant (review point 3):** the sidecars land in the bundle through the two orchestrator drains (§4). No `.gitignore` negation outside the bundle; `results/uc/` is gone.
* **R2 — the look-ahead and coal UT (UC-0 F6).** With `ut_coal = 36 h > W + L = 36 h`, a coal start never sees its full min-up inside one window; the rolling scheme re-decides it next window (the DA-SCUC behaviour), and the UT rows clip to the window. Whether UC-2 declares a longer `uc_lookahead_hours` for coal ISOs is a PRECOMMIT choice; the engine accepts any `W + L <= hours`.
* **R3 — `uc_window_time_limit_s = 600`** is a declared placeholder for D-2 (accepted by the desk, review point 4).
* **R4 — emission-cap / RPS duals** do not reach the window (slim P0 extract); stated in §2.1 (accepted by the desk as a known limitation, review point 4).
* **R5 — hydraulic cascade (`hydro_cascade`, NWPP) is refused by the window builder:** its lagged upstream terms wrap cyclically at the window edge and the slim P0 extract carries no pond levels to pin them to. An NWPP A/B needs either the P0 cascade extract (`hydro_cascade_storage`) or the pin-to-P0 treatment of the budget families extended to the cascade plants; neither is this PR.

## 9. What UC-0's FINDING changed here

Read from its branch (`a0558224`): the per-ISO substitution sets became the refusal list in §5 (`cc_mustrun_per_plant`, `soco_gas_st_campaign_commitment` and `miso_gas_ecomin_online_floor` were added to the plan §6 set); the hard cases are explicitly not refused; F6's horizon flag is R2; F7's no-load construction (B0, per-unit intercepts, class mean per MW fallback) is the derive's construction; F8's cluster census (155 PJM … 31 SOCO plant clusters) sizes nothing here (the design assumes no ranking) but is the expected integer count per window the log must reproduce.

## 10. Log entry

- 2026-10-03 · UC-1 `session_01TaYG9p5stirhcFVYgK3r6j` (Fable) · branch `claude/ucmilp-1-engine-mcst` off main `fc83487f` · DESIGN pushed before code · UC-0 FINDING read from `a0558224` (not on main) · formulation: plant×family clusters, E1 = posture gate inverted, 24+12 rolling, Rajan–Takriti clustered counts, P0-target boundaries with one-sided SOC terminal, state carried from w−1, warm start from w−1 + P0, pre-fixing default off · nine `uc_*` fields · MECH 28 · refusals = bridges + posture + `cc_mustrun_per_plant` + P2 · routed R1–R4.
- 2026-10-03 · UC-1 · desk review of DESIGN b974d2c9 folded: §2.2 carry stated as mandatory + fast test; §5 refusal set = two declared tuples (`cc_mustrun_per_plant` / SOCO campaign moved out, `caiso_ra_*` legs + `miso_gas_ecomin_online_floor` in); §4 sidecars into the bundle through the two granted orchestrator drains (R1 closed); §2.4 E6 as built; §1.2 min-down from the class table; R5 hydro_cascade refused. Golden shards relaunched at the SHA carrying the drains.
