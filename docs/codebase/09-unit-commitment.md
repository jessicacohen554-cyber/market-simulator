# 9. The MILP Unit-Commitment Stage

This page covers the optional UC stage between P0 and P1
(`ScenarioConfig.unit_commitment_milp`, default off): `model/uc/` (the window
MILP), `pipeline/uc.py` (the seam glue) and the one gated hunk in
`pipeline/solve.py::run_energy_solve`. Owner ruling R2 (2026-10-03) amended
CLAUDE.md "Dispatch and commitment" to admit it; the design record is
`docs/records/governance/uc-milp-2026-10/DESIGN-uc-milp-engine-2026-10-03.md`.
The MILP never prices (rule 4): P1 stays the scored LP and its duals stay the
prices.

```
 run_energy_solve                      gate off: unchanged objects, no import of pipeline/uc
   P0 LP ─► r0 ─► markup ─► zero_posture_markup
          ┌─ if config.unit_commitment_milp ───────────────────────────────────────────────┐
          │ stage = pipeline.uc.prepare_uc_stage(...)   # cluster params, integer set       │
          │ markup = stage.zero_markup(markup)          # rule 19: start paid once, in the UC│
          │ p1_fleet_prep = stage.p1_fleet_prep         # hook; reads the FINAL mc_bid       │
          └───────────────────────────────────────────────────────────────────────────────────┘
   mc_bid = mc_base + markup (+ P1-only adjustments)
   p1_fleet_arrays = p1_fleet_prep(r0) ─► rolling windows ─► schedule u[c,t] ─► bounds (MECH 28)
   P1 LP on the bounded fleet ─► prices = duals
```

## 9.1 Clusters and parameters — `model/uc/params.py`

`build_uc_cluster_params(fleet_arrays, iso)` returns the struct-of-arrays
`UcClusterParams` (rule 6). A cluster is one `(plant_code, family)` of the
thermal non-CHP fleet — every tranche row of the plant is a member — or one
row for a legacy bin (`plant_code == 0`). Families are the CAMPD unit-type
tokens of the `uc-params` data contract (`cc`, `ct`, `st_gas`, `coal`), mapped
from `plant_group` (`FAMILY_BY_GROUP`) or, absent a group, from the fuel.

| Parameter | Source order |
|---|---|
| `n_units`, `mlf`, `ut_h`, `dt_h`, `noload_mmbtu_h` | `data/clean/uc-params/<ISO>` (`scripts/data/derive_uc_cluster_params.py`, CAMPD unit-level pooled 2023–2025, frozen — rule 23) → class tables (`MIN_STABLE_PCT_PHYSICAL`, NREL `COMMITMENT_PARAMS_BY_FUEL`, coal bin durations) → the family's class-fallback row for no-load |
| `pbar_mw` | fleet capacity / `n_units` (never the CAMPD HSL) |
| `su_per_mw` | the capacity-weighted member lookup of `model/reserves/spec.py::_posture_pool_params` (NREL SR-5500-55433; coal `BIN_STARTUP_COST_PER_MW`) |
| `integer` (E1) | `integer_gate`: `dt_h > POSTURE_FAST_START_MIN_DOWN_H or su_per_mw >= POSTURE_FAST_START_STARTUP_PER_MW` — the posture fast-start exemption inverted (rule 18) |

`noload_cost_per_unit_h(fleet, mc_base)` prices the no-load heat input at
the anchor member's implied $/MMBtu, `(mc_base − vom) / heat_rate`, hourly.
Every cluster records the source it resolved to (`src_*`), written to
`uc_solve_log_<y>.json` `clusters[]`.

## 9.2 One window — `model/uc/window.py`

`slice_window_inputs(fleet, demand, kwargs, t0, t1, p0_dispatch)` slices every
array whose last axis is `T` (recursively through tuples, lists and
dataclasses), drops the annual/monthly budget families (`BUDGET_KWARGS`) and
pins their generators to the P0 dispatch (`uc_boundary_mode = "p0_targets"`).
`REFUSED_KWARGS` (the posture family, `hydro_cascade`) raise.

`UcWindowModel` builds the production `DispatchModel` on the slice (`model/lp`
untouched), installs the production cost vector (integer clusters at
`mc_base`, everything else at the P1 bid) and adds, on the HiGHS handle:

* columns `u[c,t] ∈ {0..n_c}` (integer), `v`, `w ∈ [0, n_c]` — hour-major,
  `U0 + t·n_int + k`;
* rows, each family one vectorized block (rule 2): coupling
  `mlf·p̄·a·u ≤ Σ P ≤ p̄·a·u`, logic `u_t − u_{t−1} − v_t + w_t = 0` (the
  carried `u_prev` in the `t0` RHS), Rajan–Takriti in rolling-horizon form
  `Σ_{lag<UT} v − u ≤ −hist_v` and `Σ_{lag<DT} w + u ≤ n − hist_w` (the
  window's own sums plus the carried starts / stops still inside their
  min-up / min-down, `_carry_history`, on the RHS — one inequality, so a
  window can never stop a unit inside its min-up because another unit's
  earlier start carried the bound alone), and the look-ahead min-down guard
  `Σ_{h−τ<DT} w[τ] ≤ n − floor_need[h] − hist_w[h]` for every hour `h` past
  the window that a structural floor needs units in (`floor_need_ahead`,
  the stage's zero-LP `units_needed_for_floor` over the year fleet);
* boundary edits: the cyclic SOC row's `SOC[s, T_w−1]` coefficient zeroed and
  its RHS set to the carried `SOC_init` (`_state_cyclic_rows` locates the row
  on the LP HiGHS holds), a one-sided terminal `SOC[s, t1−1] ≥ P0's`, one
  added ramp row block for the `t0` transition;
* `u` bounds: the carried history (implied by the rows; a root-relaxation
  tightening), structural member floors (`units_needed_for_floor`, on the
  LP-effective floor `min(min_gen, pmax·availability)` — the clip
  `bounds.build_variable_bounds` applies to the P column), optional
  pre-fixing (`prefix_bounds`, `uc_prefixing`).

An infeasible window raises `UcWindowInfeasible` carrying the window index
and hour range, the LP relaxation's status (re-solved on the same handle) and
the zero-LP `diagnose.py` report (bound propagation per row family, carried
starts above `n`, floors above the carried min-down); the bench harness's
`--dump-dir` writes the model, state and report (`UcSolveOptions.debug_dump_dir`,
never a registry field).

`warm_start_vector` shifts the previous window's incumbent and fills the tail
from P0; `extract` packages a HiGHS column vector as `WindowResult`.

**The slim window — `model/uc/slim.py` (`uc_slim_window`, default True).**
With the full model built, `UcWindowModel(slim=True)` reads it back from the
handle once (`diagnose.highs_lp_arrays`) and applies `reduce_lp`, an EXACT
reduction iterated to a fixpoint and vectorized over the whole model: every
column whose bounds pin it (`lower == upper`: pinned budget units,
zero-availability units, zero-CF renewable hours, `u`/`v`/`w` a floor or the
carried history fixes) leaves with its cost as the objective offset and its
contribution shifted into the row bounds; forcing rows fix their columns;
singleton rows become column bounds; redundant and emptied rows drop; and
parallel continuous columns (the same column of `A` and the same cost — the
generator `P` columns of one zone-balance row at one offer, which is what
HiGHS's own "parallel rows and columns" rule merges after a full presolve
pass) become one slim column with summed bounds. The slim model goes to a
fresh handle `h_solve` (`slim_handle`, options copied); the full handle `h`
stays for the diagnosis, relaxation and dump paths. `SlimReduction.restrict`
carries the warm start into the slim space, `expand` brings the solution
back (fixed values reinserted, merged members split in index order above
their lower bounds — a split the stage is indifferent to: a member's
dispatch feeds only the next window's warm start and its ramp-group sum). A
contradiction met on the way returns `None` and the window solves on the
full model, so the existing infeasibility report is what fires.
`WindowResult.slim_columns/rows/counts/slim_s` and `uc_solve_log`
(`windows[].slim`, `summary.slim_sums`, `phase_sums.slim_s`) carry the
census. SPP 2020 window 0: 57,384 × 17,229 → 21,304 × 12,204 (8.5 k columns
fixed, 27.6 k merged, 5.0 k rows dropped) in ~0.1 s; the MILP 2.9 s → 1.6 s,
the same objective and `u` (FINDING-ucmilp-slim-window-2026-10-10.md).

**VLR load-pocket rows — `model/uc/pocket.py` (`vlr_pocket_commitment`, default False).**
`build_pocket_requirement` maps the ISO's clean `vlr-pocket-groups` partition
(`data/vlr_pocket_groups.py`; MISO: the MTEP15 VLR study's Scenario-1C groups)
onto `(plant_code, family)` clusters through each unit's EIA-860 prime mover /
energy source. Groups on the same cluster set add their requirement (capped at
the set's units); overlapping sets are refused; a group with no fleet cluster is
logged `unmatched`. `UcWindowModel._add_pocket_rows` then adds, per set and
window hour, `sum_{c in set} u[c,t] >= min(N, sum_c min(u_upper[c,t],
ceil(n_c a[c,t])))` with `N = constants.VLR_GROUP_MIN_COMMITTED_UNITS` per
group: a u-floor that relaxes inside a carried min-down and on outage, so it
never makes a window infeasible by itself. The rows sit after the UC rows and
before the ramp rows (`diagnose` names them `vlr_pocket`). The stage logs
`engine.vlr_pocket` and `windows[].pocket_rows`, and hashes the requirement
into the pass-2 reuse digest (it is not a `uc_*` field). `__post_init__`
refuses the field without `unit_commitment_milp` and beside
`st_gas_mustrun_per_plant` (rule 19: it replaces that floor).

**Sector-1 ST_GAS self-commitment rows — `model/uc/selfcommit.py`
(`spp_selfcommit_sector1_st_gas`, default False, SPP only).**
`pipeline.uc.build_selfcommit_requirement_for_stage` reads each plant's EIA-860
Sector at the run's vintage (`eia860_plant_sectors`) and its pooled CEMS
`online_frac` from the thermal-tranche artifact the floor family reads
(`thermal_tranche_online_frac`, same selector arguments as `assembly.py`);
`build_selfcommit_requirement` keeps the integer `st_gas` clusters of plants in
`constants.UC_SELFCOMMIT_EIA860_SECTORS` with a positive share (every other
`st_gas` cluster is logged in `skipped` with its reason) and places each one's
window as `round(online_frac × T)` hours of whole operating days ranked by
mean P1 system load (`data/fleet/arrays.py::_commitment_day_order` /
`_mustrun_window_hours`, the SPP-64 / spp-27 placement).
`UcWindowModel._add_selfcommit_rows` adds one row per required cluster-hour,
`u[c,t] >= min(UC_SELFCOMMIT_MIN_UNITS_ONLINE, u_upper[c,t], ceil(n_c a[c,t]))`:
it relaxes on outage and inside a carried min-down (relaxed cells build no row
and are counted in `selfcommit_relaxed_hours`), and the online unit's MW is
free above the measured-mlf coupling row. The rows sit after the pocket rows
(`diagnose` names them `selfcommit`). The stage logs `engine.selfcommit` and
`windows[].selfcommit_rows` / `selfcommit_relaxed_hours`, and hashes the
requirement into the pass-2 reuse digest. `__post_init__` refuses the field
without `unit_commitment_milp`, outside `UC_SELFCOMMIT_ISOS` and beside
`st_gas_mustrun_per_plant` / `st_gas_mustrun_p25_level` (rule 19).

## 9.3 Solve, stitch, inject — `solve.py`, `schedule.py`, `pipeline/uc.py`

`solve_window` applies the registry options (`mip_rel_gap`, `time_limit`, the
`uc_solver_preset` solver path — `UC_SOLVER_PRESETS`: `highs_default` or
`lean`) on the handle that solves (`window.h_solve`: the slim model when the
reduction applied, else the full one), restricts the warm start to that
space, runs with HiGHS's log collected into the per-window phase profile
(`parse_highs_mip_log`), and expands the solution back to the full column
vector; `Optimal` or a time-limit stop with an incumbent is accepted,
anything else raises `UcWindowInfeasible` (an engine defect, never a tuning
invitation) with the relaxation re-solved on the FULL handle. `UcSchedule.keep` records the first `W` hours of each
window, `state_for` hands the next window its state, `checkpoint` writes
`checkpoint_<month>.npz` after every completed month (plan E9).

`UcStage.run` is the rolling loop (`t_start`/`t_end` for the ladder's monthly
rung); `floor_and_ceiling` turns the schedule into P1 bounds — ceiling
`availability·u/n` on every member, floor `mlf·p̄·u` split by available
capacity — and `inject` composes the floor through
`pipeline.commitment._bridge_floored_fleet(…, MECH_UC_SCHEDULE)`. The
artifacts reach the bundle through the orchestrators' two-line drain
(`take_uc_artifacts(p1_result)` → `write_uc_artifacts(run_dir, year, …)` in
`scripts/run_calibration_full.py` and `runner.py`, gated on the field):
`hourly/uc_schedule_<y>.parquet`, `hourly/uc_uplift_<y>.parquet` (the make-whole
frame, `model/uc/uplift.py`, priced from the P1 result and never into a price)
and `uc_solve_log_<y>.json`. Monthly checkpoints are scratch under
`results/uc-checkpoints/`.

**Commitment demand (uc-1.7) — `data/commitment_demand.py`.** The windows
balance against `UcStage.commit.demand`, not the P1 demand
(`uc_commitment_demand_source`; owner ruling UC-DESK r13). `"actual"` (default)
is the P1 demand object itself. `"da_forecast"` in a backcast adds the BA's
EIA-930 `Demand forecast − Demand`, read off the demand loader's own filled
frame (same model clock), split by `eia930.load_zone_weights` (the loader's
zone weights) and grossed up by `td_loss_factor`; hours with
`|DF − actual| > COMMITMENT_DF_DATA_ERROR_FRACTION · actual` (0.30, the UC-DIAG
data-QA cut) or a missing forecast add nothing. In forecast mode it is
realised load × (1 + `bias_frac`), the measured mean relative error by
meteorological season × local hour from the frozen `load-forecast-error`
partition (`scripts/data/derive_load_forecast_error.py`, rule 23). Only the
window energy balance moves: reserve rows, P0 targets and P1 are untouched,
and P1 clears on actual load (rule 4). Every hour the commitment exceeds what
actual load can absorb above the committed floors shows as P1 dump — the
over-commitment cost of a forecast error; P1 has no real-time decommitment.
`uc_solve_log.engine.commitment_demand` records the source, basis, QA-dropped
hours and the increment (mean, top-100-load-hour median, max, min).

**Reliability commitment (uc-1.9) — `UcStage.reliability_commitment`.**
`uc_reliability_commitment` (default off; needs `uc_commitment_demand_source =
"da_forecast"`; owner ruling R12; DESIGN-ucmilp-ruc-stage-2026-10-16). After P1
(“P1a”) `pipeline/solve.py`'s one RUC hunk asks the stage for a P1b fleet.
`ruc_trigger_hours` marks the hours whose P1a energy slack or largest
reserve-family ORDC shortfall exceeds HiGHS's own `primal_feasibility_tolerance`;
none → `None`, P1a is final (byte-identical to the arm without RUC). Otherwise
the triggered days' windows are re-solved on the same `UcWindowModel` with
`u_floor = u_DA` (add-only; the look-ahead guard reads `u_DA` past the horizon),
demand = `ruc_load_basis_demand` (`uc_ruc_load_basis`: `"actual"` only for now),
every dispatch column at `STORAGE_TIEBREAKER_EPSILON`, and a unit-hour costing
no-load + `mlf·p̄·a·max(mc_uc, 0)` (anchor) on top of the start cost; penalties are the
window LP's own. The first window of an episode carries P1a's dispatch / SOC at
`t0 − 1`; the sweep continues until the carried `u` and start / stop history equal
the DA schedule's. The final schedule replaces `schedule` (`schedule_da` keeps the
DA one), is injected through the same MECH 28 bounds, and P1b — solved cold on the
same bid, demand and kwargs — is the scored P1. `uc_solve_log.ruc` records the
trigger hours / days, episodes, windows, added unit-hours and floor MWh by class;
`uc_uplift` gains `ruc_added_units`, `ruc_start_usd` (net of the DA starts) and
`ruc_noload_usd`; `legitimacy_diagnostics.run_d4_uc_ruc` emits the D-4 sub-row
`uc_schedule × uc_ruc` (window = the swept hours).

**DA-schedule reuse across runs (R15).** `uc_da_schedule_reuse_bundle` names a
committed bundle; `UcStage.adopt_committed` reads its `uc_schedule_<y>` only when
that leg's `uc_solve_log.engine.input_digest` equals this run's, and raises
otherwise. `uc_input_digest` hashes `UC_DA_DIGEST_VERSION` (the DA windows' version,
`uc-1.8`) and omits the RUC-only fields (`UC_DIGEST_EXCLUDED_FIELDS`), so a uc-1.8
DA schedule of the same inputs is reusable; uc-1.7 legs are not (their solver
options differ).

## 9.4 Registry, refusals, tooling

Eleven fields (`unit_commitment_milp`, `uc_window_hours` 24,
`uc_lookahead_hours` 12, `uc_mip_rel_gap` 1e-3, `uc_window_time_limit_s` 600,
`uc_integer_scope` `physics`, `uc_noload_source` `campd_regression`,
`uc_boundary_mode` `p0_targets`, `uc_prefixing` False, `uc_solver_preset`
`lean` (lane UC-SPEED), `uc_slim_window` True (lane UC-SLIM)), cache-key
registered at their defaults (TIER_TAGS 1); the last two were born at their
fast values, so no committed key moved. `__post_init__` refuses the gate beside any
armed member of the two declared tuples `UC_REFUSED_ALWAYS` (every commitment
bridge and its legs, the posture family) and `UC_REFUSED_BY_RULING` (empty
until an owner D-5 ruling extends it) — rule 19 as data.
`data/floor_mechanisms.py::MECH_UC_SCHEDULE = 28` carries the D-2 attribution
with an ablation entry. Tooling: `scripts/diagnostics/bench_uc_ladder.py` +
`scripts/lib/uc_bench.py` (GATESPEC §3 rungs, the §6.1 wall table),
`scripts/probes/_ucmilp_compose_span.py` (per-year shard legs → one span,
UC sidecars folded, uplift written). Tests: `tests/unit/model/uc/`.
