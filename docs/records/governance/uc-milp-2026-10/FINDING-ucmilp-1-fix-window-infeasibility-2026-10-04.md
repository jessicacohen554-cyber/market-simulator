# FINDING — the uc-milp window infeasibility under the kept SPP floors is a rolling-horizon carry defect, not the floors

Lane UC-1-FIX (`session_01UWCaF48NJuC3M2GeQGuwPk`, Fable), 2026-10-04, chartered by
UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`). Defect report: UC-2-SPP's
`RESULT-ucmilp-spp-ab-2026-10-04.md` §1 (branch `claude/ucmilp-2-spp-ab-r7qd` @
`02bcbbf3`): with `unit_commitment_milp=true` on the SPP keeper recipe
(`2026-10-03-closeout-spp-nuc-keeper`, `results/calibration/closeout_spp_nuc_span`), all
seven years 2019–2025 raised `UcWindowInfeasible` at engine pin `c8690022` after P0
solved normally. Year LP solved in this session: **zero** (every window built here is a
36-hour MILP on the keeper recipe's inputs; the year's P0/P1 ran only in the L1 shard).

## 0. Headline

**Root cause (proved on real data, two independent reproductions):** the carried min-up /
min-down history was enforced as a separate `u` column bound, while the in-window
Rajan–Takriti rows summed only the window's own starts / stops. Two constraints that the
physics requires in ONE inequality were enforced one at a time, so a window could stop a
unit still inside its min-up whenever another unit's earlier start satisfied the bound
alone (or restart a unit inside its min-down when a stop in history satisfied the bound).
The kept history then accumulated more starts within one min-up than the plant has units;
the next window's carried bound exceeded `n`, the bound repair `ub = max(ub, lb)` lifted
`u` above `n`, and the min-down row `w + u ≤ n` became contradictory in every hour the
bound reached. **UC-2-SPP's lead (the P0 floor-feasibility clip vs the floor-derived
`u` bound) is refuted**: the window already slices the same clipped `min_gen` P0 solves on,
and zero `(cluster, hour)` pairs in 8760 h × 92 clusters contradict the ceiling (§2).

**Fix (structural, no slack, no penalty, no tolerance):** the history enters the
Rajan–Takriti rows as right-hand-side constants (the rolling-horizon form of the rows), and
a look-ahead min-down guard row keeps a window from stopping a unit that a structural floor
it cannot yet see will need before the min-down expires. The floor-derived `u` bound is
computed from the LP-effective floor (`min_gen` clipped to `pmax·availability`, the clip
`bounds.build_variable_bounds` applies) and capped at `n`; the P1 injection composes the
upstream floors at that same effective level. Engine version `uc-1.1`.

## 1. Facts

| Item | Value |
|---|---|
| Failing recipe | SPP keeper, `--set unit_commitment_milp=true`; `coal_mustrun_per_plant`, `st_gas_mustrun_per_plant`, `cc_committed_per_plant`, `mustrun_commitment_feasibility_clip` all armed (owner ruling R5: keep both floors) |
| Shard evidence | 2020 relaunch `session_01MHWSyP87HaQpJXFJtiSu76`: P0 101.8 s; **about 10 minutes of UC stage before the raise** (UC-2's "window 0" was an inference from the column count, which every non-tail window shares) |
| Window census (this session, zero year LP) | SPP 2020: 219 clusters, 92 integer (401 fleet rows); window 0 = 57,384 columns × 16,740 rows — identical to the shard's counts |
| `units_needed_for_floor` vs ceiling, whole year | 0 of 92 × 8760 cells with Σ member floor > `cap·a` at `u = n`; 0 cells with raw floor need > `n`; `availability ≤ 1` everywhere |
| Window 0, keeper inputs, zero state | bound propagation: 0 contradictory rows, 0 bad column bounds; LP relaxation Optimal; MILP Optimal (1 node, 3.7 s, gap 1.4e-4) |
| Window 0, realistic P0 stand-in (keeper P1 `unit_marginal_2020` dispatch + `storage_2020` SOC, every pin / SOC / `u_prev` live) | MILP Optimal, gap 9.1e-5, warm start accepted |
| January, same stand-in, old engine | 31 windows Optimal (89 s) |
| **Year roll, same stand-in, old engine** | **infeasible at window 156 (t0 = 3744, 6 June)** and, in a separate segment, **window 284 (t0 = 6816, 11 Oct)**; Jan–Apr segment (122 windows) clean |
| Window 156 post-mortem | cluster k=40, plant **2965** (ST_GAS, `n = 2`, `dt = 12`, measured `ut = 84`): carried min-up bound **3.0 for hours 0–23** (3 starts within 83 h in the kept history), `u_prev = 2`, floor need 1; 24 min-down rows `w + u ≤ 2` with minimum activity 3; LP relaxation infeasible |
| Window 284 post-mortem | cluster k=31, plant **2817** (coal, `n = 2`, `dt = 16`, measured `ut = 217`): carried bound 3.0 over all 36 hours (3 starts within 216 h); 36 contradictory min-down rows |
| **Year roll, same stand-in, fixed engine** | **365 windows Optimal**, 0 time-limit hits, gap ≤ 9.8e-4, MILP p50 2.4 s / p95 3.8 s / max 18.2 s, nodes p50 1; joint min-up violations 0, joint min-down violations 0, `u > n` cells 0; guard rows p50 448–561 per window |
| Toy reproduction (`tests/unit/model/uc/test_window_carry_rows.py`) | against the pre-fix tree (`681b71cf`): the SPP-pattern stage test raises `UcWindowInfeasible` (90 columns, 54 rows, 1 integer cluster) and the look-ahead floor test raises it too; 7 of 7 new tests fail there and pass on the fix |

**Diagnostic-only evidence (UC-DESK ruling, 2026-10-04).** The window rolls in this record
(§1 "Year roll" rows, §2 step 4) solved 36-hour window MILPs in the lane container — not an
ISO-year LP, accepted under rule 32 as diagnosis evidence only — with the keeper's committed
**P1** dispatch and storage SOC standing in for the **P0** boundary (hydro / oil pins,
`u_prev`, SOC state). Their numbers (wall, gaps, nodes, guard-row counts) are evidence for
this FINDING and nothing else: no reading, no wall row, no matrix cell. The engine's proof on
the real P0 boundary is the L1 shard (§5, window 0 only) and UC-2-SPP's relaunch (every
window of every year).

## 2. The zero-LP diagnosis, in order

1. **Capture** the keeper recipe's LP inputs for SPP 2020 at the `run_energy_solve` seam
   (`scripts.lib.uc_bench.capture_year(..., solve=False)`, zero LP): fleet (1300 rows),
   demand, kwargs, config. No `p1_*` hook is armed, so the production `fleet_in` is the
   base `FleetArrays` — the same object whose `min_gen` carries the
   `mustrun_commitment_feasibility_clip` release. **The window slices that array; the clip
   is applied identically by construction.**
2. **Every a-priori check on window 0** passes: interval arithmetic over every row of the
   HiGHS model (production rows and the five UC families), `u_lb > n`, `u_lb > u_ub`,
   Σ member floor > `pbar·a·n`, mlf floor at `u_lb` > Σ available capacity — all zero.
   The LP relaxation and the MILP solve. The counts match the shard's, so the structure
   is the shard's.
3. **Nothing P0-dependent can break window 0.** `u ≡ n` is always feasible for the
   coupling rows (the P lower bounds are clipped to `pmax·availability` by
   `bounds.build_variable_bounds`, so Σ P_lb ≤ cap·a), slack and dump close every energy
   balance, pinned budget units are fixed inside their bounds, and P0's own SOC path is
   feasible under the window's storage rows. So the failure had to be in a LATER window's
   carried state — consistent with the shard's ten minutes of UC before the raise.
4. **Roll the year** with a realistic P0 stand-in (the keeper's committed P1 per-unit
   dispatch and storage SOC — no year LP), the production `UcStage.run` path, three
   parallel segments. The old engine fails at windows 156 and 284 (table above); the
   dumped window's bound propagation names 24 (resp. 36) min-down rows whose minimum
   activity (`u_lb = 3`) exceeds `n = 2`, and `hist_v = 3` for a two-unit plant.
5. **Mechanism.** Window `w` carries `lb = hist_v(τ)` (units started before `t0` still in
   their min-up) as a bound and writes `Σ_{window} v − u ≤ 0` as a row. A plant with unit
   A started in history (`lb = 1`) and unit B started in the window (`v = 1`) satisfies
   both with `u = 1` from the hour after B's start — physically both are inside their
   min-up. The window stops one, the next window re-starts it (its own history bound
   demands it), and after three such starts within one measured min-up (84 h, 217 h;
   `ut` is the plant's p25 run length) the carried bound reads 3 on a two-unit plant.
   The same split applies to stops vs. min-down (`ub = n − hist_w` and `Σ w + u ≤ n`
   separately), which lets a unit restart inside its min-down.

## 3. The fix (`src/market_sim/model/uc/window.py`, `params.py`, `solve.py`, `diagnose.py`; `pipeline/uc.py`)

| Change | Where | What |
|---|---|---|
| History inside the rows | `UcWindowModel._carry_history`, `_add_uc_rows` (d)/(e) | `Σ_{lag<UT} v_{τ−lag} − u_τ ≤ −hist_v(τ)` and `Σ_{lag<DT} w_{τ−lag} + u_τ ≤ n − hist_w(τ)`: the window's own and the carried starts (stops) in one inequality. The `u` bounds keep the history as the implied root-relaxation tightening |
| Look-ahead min-down guard (physics, rule 18: a unit stopped at `τ` is unavailable until `τ + DT`; a floor the year's inputs already fix at hour `h` is a known lower bound on the units online there, so stopping more than `n − floor_need(h)` units within `DT` of `h` is a decision the window's own physics forbids — the row only brings the known floor into the window's sight) | `_add_uc_rows` (f), `floor_need_ahead` | For every hour `h ∈ [t1, t1 + DT − 1)` with `floor_need(h) > 0`: `Σ_{τ∈window, h−τ<DT} w_τ ≤ n − floor_need(h) − hist_w(h)` — row (e) at an unseen hour with `u` at its known lower bound. A kept stop is never one a floor beyond the 12-hour look-ahead needs (coal `DT = 16 > L + 1`, 97 floor-need rises in SPP 2020). The stage computes the year's floor need once, zero LP (`units_needed_for_floor` on the year fleet) |
| LP-effective floor | `params.units_needed_for_floor(params, fleet, t0, t1)` | `min(min_gen, pmax·availability)` summed per cluster, `ceil(·/pbar)` capped at `n` — the clip `bounds.build_variable_bounds` applies to the P column, so the UC never asks for a unit the LP's own floor does not |
| Injection at the effective floor | `UcStage.inject` | The upstream `min_gen` is composed into P1 clipped to `pmax·availability`, so `_bridge_floored_fleet`'s availability raise never re-opens a ceiling the schedule closed |
| Instrumentation (gate-on path only) | `solve.solve_window`, `UcWindowInfeasible`, `diagnose.py`, `UcSolveOptions.debug_dump_dir` | The exception names the window (`window 156 [3744, 3780)`), re-solves the LP relaxation on the same handle and attaches the zero-LP report (bound propagation per row family, carried starts above `n`, floors above the carried min-down). `bench_uc_ladder.py --dump-dir` writes the model (`.mps`), state (`.npz`) and report (`.json`); never a registry field or an env knob |
| Engine version | `pipeline/uc.py` | `uc-1.1`; `uc_solve_log` windows carry `guard_rows` |

Not changed: the floor mechanisms, `model/lp`, `iso_configs`, any `ScenarioConfig` field
(no cache-key or mechanism-matrix row moves), the shards, the plan, the matrix.

## 4. Tests (fast tier, `tests/unit/model/uc/test_window_carry_rows.py`)

* `test_min_up_history_and_window_start_are_summed` — history start + window start: both stay on.
* `test_min_down_history_and_window_stop_are_summed` — history stop + window stop: no restart inside either min-down.
* `test_units_needed_for_floor_uses_the_lp_effective_floor` — `[2, 2, 1, 1, 2, 2]` for a 150 MW floor against 200 / 50 MW available.
* `test_infeasible_window_names_itself_and_dumps` — window index, hour range, relaxation status, diagnosis, three dump files.
* `test_spp_pattern_three_starts_within_one_min_up` — the SPP chain in miniature (`ut = 16`, W = 6, L = 3): raises on the pre-fix tree, completes with joint physics intact on the fix.
* `test_floor_beyond_the_horizon_is_guarded_against_min_down` — a floor past the horizon within the published min-down: raises on the pre-fix tree; the guard keeps the units on.
* `test_floor_above_availability_solves_gate_off_and_on` — the charter's toy: gate off and on both solve; the schedule and P1 honour the clipped floor (200 MW where available, 100 MW where not).
* `test_guard_adds_no_row_without_a_floor_past_the_horizon` — UC-DESK review point 3: no floor past the horizon (or one no window hour can reach) adds no guard row; the model equals one built with no look-ahead (same rows, same optimum).

The 19 pre-existing fast UC tests pass unchanged; `test_min_down_holds_after_a_stop` now
exercises the history through the row (same assertions).

## 5. Proof on real data — L1 shard

| Item | Value |
|---|---|
| Shard | `ucmilp-bench-spp-2020-L1`, `session_01WKCvTvVfE9Y5puqJLg6dqL` (claude-opus-5-5), HEAD `1c0a8b8f1e1a0ef91d745569ae6c19d2d0ac49a1`; every hard stop passed; 3.5 min of the 30 min budget |
| Report | branch `claude/ucmilp-bench-spp-2020-L1` @ `41de489e19c7c00e39013a51039fe5c7ed10b751` — `results/bench/uc/spp_2020_L1/l1.json` (blob `38877e42`, 1,141 B) and `stdout.txt` (blob `a206cd3a`); bytes fetched and read by the parent; no dump written (nothing was infeasible) |
| Capture (real P0 + P1 of the keeper recipe) | P0 102.8 s cold (78,773 simplex iterations), P1 31.9 s warm; year 196.0 s; peak 7.08 GiB |
| **Window 0 MILP** | **Optimal**, 4.20 s, 1 node, gap 5.07e-9 (≤ 1e-3), 3,312 integers, 57,384 columns, 17,229 rows (489 guard rows), RSS 5.40 GiB, warm start accepted, 16 starts |
| LP relaxation | Optimal, 1.56 s; integrality gap $190.24 |
| vs the P1 slice | committed energy −8,668 MWh; starts 16 vs 124 |
| Side note from the shard | a pre-existing non-fatal WARNING: `resolved_inputs` split-remap probe (`campd_split_remap_companions`) finds no SPP companion file; provenance only, not the LP, not this lane |

L1 solves window 0 on the real P0 boundary; the defect lived at windows 156 and 284, so
this line is necessary, not sufficient. The sufficient proof is UC-2-SPP's relaunch at
the merged SHA (every window of every year), with the diagnostic-only roll of §1 as the
lane's evidence.

## 6. G-DRIFT (rule 29)

Every hunk is on the gate-on path: `src/market_sim/model/uc/{window,params,solve,diagnose}.py`
are imported only by `pipeline/uc.py`, which `pipeline/solve.py` imports only inside
`if getattr(config, "unit_commitment_milp", False)`; `scripts/lib/uc_bench.py` and
`scripts/diagnostics/bench_uc_ladder.py` are the bench harness. No hunk under
`model/lp`, `data/`, `config/` or the floor mechanisms. The gate-off byte-identity test
(`test_gate_off_is_byte_identical_and_never_imports_the_stage`) passes; the goldens stay
valid. Classification: **INERT with the gate off, LIVE only with `unit_commitment_milp=true`
(no keeper arms it).**

## 7. What UC-2 should do next

Relaunch under its PRECOMMIT's Addendum rule at the merged SHA: same recipe, same single
`--set`, same readings. The fixed engine rolled every SPP 2020 window on the stand-in; the
arm's wall rows will come from the shards. The window-156 / 284 reproductions above are the
`U`-cell evidence that the kill was an engine defect, as UC-2 recorded.

## Log entry

- 2026-10-04 · UC-1-FIX `session_01UWCaF48NJuC3M2GeQGuwPk` (Fable) · branch `claude/ucmilp-1-fix-infeas-h2w` off `681b71cf` · zero year LP in the parent · window 0 of SPP 2020 feasible on the keeper inputs (clip lead refuted: 0 contradictory cells in 8760 h × 92 clusters) · year roll on a realistic stand-in reproduced the kill at windows 156 (plant 2965, carried min-up bound 3 > n = 2) and 284 (plant 2817) · root cause: carried min-up / min-down as a column bound separate from the window rows · fix: history on the Rajan–Takriti RHS + look-ahead min-down guard + LP-effective floor; engine `uc-1.1` · 365/365 windows Optimal on the fix · 7 new fast tests (7/7 fail on the pre-fix tree) · L1 shard `session_01WKCvTvVfE9Y5puqJLg6dqL` @ `1c0a8b8f`: window 0 Optimal, 4.20 s, 1 node, gap 5.07e-9, 489 guard rows (report `41de489e`); shard archived.
