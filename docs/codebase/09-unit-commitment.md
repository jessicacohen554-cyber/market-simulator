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
  carried `u_prev` in the `t0` RHS), Rajan–Takriti `Σ_{lag<UT} v ≤ u` and
  `Σ_{lag<DT} w + u ≤ n` with the sums clipped to the window;
* boundary edits: the cyclic SOC row's `SOC[s, T_w−1]` coefficient zeroed and
  its RHS set to the carried `SOC_init` (`_state_cyclic_rows` locates the row
  on the LP HiGHS holds), a one-sided terminal `SOC[s, t1−1] ≥ P0's`, one
  added ramp row block for the `t0` transition;
* `u` bounds: min-up / min-down carry from the kept `v`/`w` history
  (`_carry_bounds`), structural member floors (`units_needed_for_floor`),
  optional pre-fixing (`prefix_bounds`, `uc_prefixing`).

`warm_start_vector` shifts the previous window's incumbent and fills the tail
from P0; `extract` packages a HiGHS column vector as `WindowResult`.

## 9.3 Solve, stitch, inject — `solve.py`, `schedule.py`, `pipeline/uc.py`

`solve_window` sets `mip_rel_gap`, `time_limit`, `presolve on`, applies the
warm start and runs; `Optimal` or a time-limit stop with an incumbent is
accepted, anything else raises `UcWindowInfeasible` (an engine defect, never a
tuning invitation). `UcSchedule.keep` records the first `W` hours of each
window, `state_for` hands the next window its state, `checkpoint` writes
`checkpoint_<month>.npz` after every completed month (plan E9).

`UcStage.run` is the rolling loop (`t_start`/`t_end` for the ladder's monthly
rung); `floor_and_ceiling` turns the schedule into P1 bounds — ceiling
`availability·u/n` on every member, floor `mlf·p̄·u` split by available
capacity — and `inject` composes the floor through
`pipeline.commitment._bridge_floored_fleet(…, MECH_UC_SCHEDULE)`. Artifacts
land in `results/uc/<ISO>/<year>/` (`uc_schedule_<y>.parquet`,
`uc_solve_log_<y>.json`); `take_uc_stages()` hands the stage objects to a
harness. `model/uc/uplift.py` computes the make-whole sidecar post-P1 from the
bundle's own per-unit layer (`uplift_from_bundle`), never into a price.

## 9.4 Registry, refusals, tooling

Nine fields (`unit_commitment_milp`, `uc_window_hours` 24,
`uc_lookahead_hours` 12, `uc_mip_rel_gap` 1e-3, `uc_window_time_limit_s` 600,
`uc_integer_scope` `physics`, `uc_noload_source` `campd_regression`,
`uc_boundary_mode` `p0_targets`, `uc_prefixing` False), cache-key registered at
their defaults (TIER_TAGS 1). `__post_init__` refuses the gate beside every
commitment bridge, the posture family and `cc_mustrun_per_plant` (rule 19).
`data/floor_mechanisms.py::MECH_UC_SCHEDULE = 28` carries the D-2 attribution
with an ablation entry. Tooling: `scripts/diagnostics/bench_uc_ladder.py` +
`scripts/lib/uc_bench.py` (GATESPEC §3 rungs, the §6.1 wall table),
`scripts/probes/_ucmilp_compose_span.py` (per-year shard legs → one span,
UC sidecars folded, uplift written). Tests: `tests/unit/model/uc/`.
