# FINDING — UC defect 5: the look-ahead guard read a different fleet (and a different unit count) than the next window

Lane UC-1-FIX-2 (`session_01VQbdDQky4y91ytyky1UEge`, Opus), 2026-10-10, chartered by UC-DESK
(`session_01WX9W5tgYMre3Z134LZoGF6`). Defect report: UC-2-MISO
(`session_016bPoPZ6beefv8kJUn8sQFH`, pin `2f872a62`; arm = MISO keeper
`closeout_miso_nuc_span` + `unit_commitment_milp=true`, every floor kept) and UC-2-NEISO
(same pin; keeper `w0_neiso_span`). Mid-year windows raised `UcWindowInfeasible` with
the LP relaxation infeasible: MISO 2020 w129, 2021 w30, 2023 w227, 2025 w135; NEISO 2021
w259, 2023 w187; ERCOT 2020 w118 (UC-2-ERCOT, pin `dc3860be`). Year LP solved in this session: **zero**.

## 0. Headline

**Root cause.** The look-ahead min-down guard (uc-1.1, FINDING-ucmilp-1-fix §3) keeps a
window from stopping units that a floor past its horizon needs inside their min-down. It
read that need **(1) on the unpinned year fleet** and **(2) as `⌈Σ floor / p̄⌉`**. The
window that later covers those hours reads neither:

1. Every row of a dropped budget family (`BUDGET_GEN_IDX_KEYS`: MISO's per-yard coal
   budget `coal_fuel_inventory_plant_grain`, NEISO's `neiso_oil_burn_budget`, hydro, …) is
   pinned to P0 inside a window through `availability = P0/pmax` and `min_gen = P0`. On the
   year fleet those rows carry no such floor, so the guard saw none.
2. The window's output-coupling row (a) `Σ P ≤ p̄·a·u` carries `p̄·a` per unit, so the
   floor needs `⌈Σ floor / (p̄·a)⌉` units. For a pinned row `a` is the pinned output share,
   and the count is **every unit** whenever the pinned output is positive. `⌈floor/p̄⌉`
   under-counts wherever `a < 1`.

A window therefore stopped units the next window's rows needed while they were still inside
their min-down. Case 1 gives the `min_down` contradiction (MISO 2020/2021); case 2 adds the
`ceiling` contradiction (MISO 2023/2025). A one-cluster toy reproduces both signatures
verbatim on uc-1.1 (§3).

**Fix (engine `uc-1.2`; structural, no slack, no penalty, no new field).**
- `params.units_needed_for_floor` returns the count row (a) implies, on the same fleet hours:
  `⌈Σ effective floor / (p̄ · a_c)⌉`, capped at `n`. The effective floors sum to at most
  `n·p̄·a`, so the cap never binds.
- `window.window_fleet()` is factored out of `slice_window_inputs`. Every window's guard
  reads its need on `window_fleet` of the hours past its horizon
  (`UcStage._floor_need_ahead`). The fleet is hour-local, so the guard of window w and the
  rows of window w+1 agree hour by hour.

- **(Desk ruling, §6.)** A cluster whose members are all budget-pinned carries no integer
  (`params.demote_budget_pinned`), so its commitment is the identity's (P0's). This removes
  the pinned case at its source and fixes the UC→P1 seam (§5.1). The two changes above stay
  for partially pinned clusters and for derated floors.

Rule basis: rule 18 (physics by parameters: a stopped unit is unavailable for `DT`); rule 17
(the floor is the one the window's own driver states, nothing new); rule 19 (no new
mechanism, the guard row is unchanged). **Option (b), "the floor yields to physics", was not
added.** Once the guard reads the window's own need, no collision is reachable after a
year's first window (which carries no history), so a yield path would be dead code (rule
26) that silently releases floors.

## 1. Phase 0 (zero LP)

| Question | Answer |
|---|---|
| Which kwargs are budget-pinned in MISO? | `coal_fuel_inventory: true`, `coal_fuel_inventory_plant_grain: true` (run_config of `closeout_miso_nuc_span`) → `coal_plant_gen_idx` pins every yard coal row |
| NEISO | `coal_fuel_inventory_plant_grain: true` (plus `neiso_oil_burn_budget: true`) in the run_config of `w0_neiso_span` |
| ERCOT (2020 w118, reported by UC-DESK at pin `dc3860be`) | `coal_fuel_inventory_plant_grain: true`, `coal_fuel_inventory_monthly_pile: true` in the run_config of `closeout_ercot_l1_span` |
| Which ISOs can arm the yard pin? | `scripts/run_calibration.py::COAL_PLANT_GRAIN_ISOS = (MISO, NEISO, NWPP, ERCOT, SOCO)`. All three failing keepers arm it. SPP is not in the list, consistent with SPP solving 365/365 on uc-1.1 |
| Can an UNPINNED floor give this signature on uc-1.1? | No. The guard and the next window then read the same `min_gen` and the same `⌈floor/p̄⌉`, and the guard covers the whole min-down reach. An unpinned floor on derated availability shows up instead as a `ceiling` contradiction (`⌈floor/(p̄·a)⌉ > ⌈floor/p̄⌉`), which uc-1.2's row-(a) count also closes |
| Can carried starts + carried stops exceed `n`? | No: the kept schedule satisfies the aggregate Rajan–Takriti rows, so `hist_v(τ) + hist_w(τ) ≤ n`. The diagnosis's `u_lower > n − hist_w` is therefore floor-driven |
| Could guard reach be short? | No: a stop at window hour `τ ≤ T_w − 1` reaches `h < τ + DT`; the guard covers `h' < DT − 1` past `t1`, i.e. exactly the reach |
| Why did January 2020 pass (L1)? | Window 0 carries no history; the collision needs a stop kept by an earlier window |

## 2. Shard evidence — the reproduction

**MISO 2021, engine uc-1.1 + the new diagnostics** (shard `session_018JgYx4Boi5ynK6htk2xt6d`
@ `e8507b79`, `bench_uc_ladder.py --rung L2 --months 1 --rolling --dump-dir`; branch
`claude/ucfix2-repro-miso-2021` @ `f33a0ab3`, `l2_infeasible.json` and
`dump/base/window_30_{diagnosis.json,state.npz}`; capture ~22 min, cgroup peak 13.36 GiB +
3 GiB swap). Windows 0–29 solved; window 30 raised, verbatim:

```
UC window 30 [720, 756) solve ended Infeasible with no feasible incumbent (147708 columns,
31068 rows, 161 integer clusters; solved as 147708 x 31068); LP relaxation: Infeasible;
a-priori contradictory rows: min_down=2; carried starts above n: 0; floor above min-down: 2
— floor above min-down at plant 6823 coal (n=1, dt=16, pinned 3/3 members, hours [12, 13])
```

The one flagged cluster (k = 89) is plant **6823**, coal, `n = 1`, `dt = 16`, measured
`ut = 91`, and **all 3 members are pinned by the yard budget**. Its carried `hist_w = 1`
through window hour 14 means the unit was stopped at hour 719, kept by window 29 [696, 732).
The window-30 bounds read:

| Window hour | 8–11 | **12–13** | 14 | 15 | 16–35 |
|---|---|---|---|---|---|
| `u_lower` / `u_upper` | 0 / 0 | **1 / 1** | 0 / 0 | 0 / 1 | 1 / 1 |
| `hist_w` | 1 | **1** | 1 | 0 | 0 |

The P0 dispatch this cluster is pinned to blips on for two hours (abs. 732–733) inside the
unit's 16-hour min-down; P0 is an LP and carries no min-down. Window 29's guard covered
exactly those hours (`[732, 747)`) but read them on the unpinned fleet, so it saw no floor
and kept the stop. Under uc-1.2 the same guard reads `u ≥ 1` at 732–733 (row (a) at the
pinned availability) and refuses any stop of plant 6823 in window 29 from hour 717 on.

## 3. Tests

`tests/unit/model/uc/test_window_pinned_floor_guard.py` (new, 6 tests):

* `test_pinned_row_needs_every_unit_the_unpinned_fleet_does_not`: pin 150 / 50 MW on 2 × 100 MW gives need `[0,2,2,2]`; the unpinned fleet gives `[0,0,0,0]` (the uc-1.1 guard's view).
* `test_window_fleet_is_hour_local`: the guard's slice equals the next window's.
* `test_window_bound_matches_row_a_under_a_pin`: `u` lower bound 2 at a 50 MW pin; a carried min-down raises with **the plant, its pinned members and the hours named** in the text.
* `test_all_pinned_cluster_carries_no_integer`: the stage over 72 h with the CC plant pinned to a P0 that restarts one hour past window 0's horizon. Before the demotion, uc-1.1 raised at window 1 with `min_down=2; floor above min-down: 2` (150 MW pin) and `ceiling=2, min_down=2` (50 MW pin), the MISO signatures. Under the ruling the cluster carries no integer: the stage logs plant 1 as demoted, runs with no integer cluster, and P1 keeps its markup.
* `test_partially_pinned_cluster_keeps_its_integer`: one unpinned member keeps the integer; all members pinned demotes it.
* `test_guard_keeps_units_a_later_derated_floor_needs`: no pin. A 50 MW floor past the horizon at availability 0.25 needs 2 units by row (a). With the uc-1.1 count (`⌈50/100⌉ = 1`) window 1 raises `ceiling=1` on plant 1 (verified by restoring the old count); on uc-1.2 no stop falls inside the floor hour's min-down.

Amended: `test_units_needed_for_floor_uses_the_lp_effective_floor` now expects `[2,2,2,2,2,2]`.
The uc-1.1 value of 1 unit at `a = 0.25` was a `u` row (a) cannot hold.

## 4. Diagnosis (UC-2-MISO could not name plants)

`diagnose_window` adds `clusters_floor_above_min_down` and `clusters_ceiling_contradiction`
(plant_code, family, n, dt_h, ut_h, pinned/total members, hours, the bound values). The
`UcWindowInfeasible` text carries them. `bench_uc_ladder.py --dump-dir` now also serves L2
(`l2_infeasible.json` plus a per-arm dump).

## 5. Results (validation @ `f2c7166a`, engine uc-1.2; reproductions @ `e8507b79`, uc-1.1 + diagnostics)

| ISO-year | Shard | uc-1.1 (repro) | uc-1.2 UC stage | uc-1.2 P1 |
|---|---|---|---|---|
| MISO 2021 | repro `018JgYx4`, val `01MEBNjx` | w30 raises: plant **6823** coal, n=1, dt=16, pinned 3/3 | **365/365 windows Optimal**, 0 time-limit hits, 2,568 s, MILP mean 6.4 s, nodes p50 1; w30 Optimal (1,178 guard rows) | **Infeasible**: `dispatch LP has no feasible primal solution` in `run_energy_solve` after the UC (§5.1) |
| MISO 2020 | val `01L2dDn4` | (UC-2-MISO: w129 raised) | 334 windows in the last checkpoint (through hour 8028), all Optimal, w129 Optimal; P1 then raised, so the UC stage finished | **Infeasible** (same error) |
| NEISO 2021 | repro `01G4RNti`, val `01Cpn1su` | w259 raises: plant **2364** coal, n=2, dt=16, pinned **8/8** | **365/365 Optimal**, 0 TL, 4,342 s, MILP mean 11.7 s / p95 42.0 s / max 103.5 s, gap ≤ 1.0e-3, guard rows Σ 11,677 / max 116; w259 Optimal | solved, 0 unserved; bundle `claude/ucfix2-val-neiso-2021` @ `e6c2c160` |
| NEISO 2023 | val `01DfRTmJ` | (UC-2-NEISO: w187 raised) | **365/365 Optimal**, 0 TL, 3,451 s, MILP mean 9.4 s / max 210.6 s, gap ≤ 1.0e-3; w187 Optimal | solved, 0 unserved; bundle `claude/ucfix2-val-neiso-2023` @ `5a6be899` |
| ERCOT 2020 | val `01M6wvBm` | (UC-2-ERCOT: w118 raised) | pending | pending |

Every reproduction names a **yard-pinned coal plant** (all of its members pinned), and every
uc-1.2 run clears the window that killed it. Defect 5 is closed.

### 5.0 Gate (UC-DESK, after ruling (a)) — engine uc-1.2 @ `e4a57362`, full year through P1

| ISO-year | UC windows | Time-limit hits | MILP mean / p95 / max s | Integer clusters (E1 gate → set) | P1 | Unserved MWh | Branch @ SHA |
|---|---|---|---|---|---|---|---|
| MISO 2021 | **365/365 Optimal** (w30, w129 Optimal) | 0 | 6.2 / 11.4 / 37.4 | **161 → 75** (86 all-budget-pinned demoted) | solved, objective $6.754 bn | **0** | `claude/ucfix2-gate-miso-2021` @ `37b8eeab` (`dispatch/2021_P1.parquet`, 102.7 MB, over GitHub's limit, held in the shard container only) |
| NEISO 2021 | **365/365 Optimal** (w259 Optimal) | 0 | 8.7 / 36.9 / 111.6 | **40 → 22** (18 demoted: yard coal and oil-budget dual-fuel ST/CT) | solved, objective $2.296 bn | **0** | `claude/ucfix2-gate-neiso-2021` @ `b756026e` (full bundle) |
| ERCOT 2020 | pass 1 (pre-slim-fix head `e4a57362`, from the log; the run was killed at the shard tool's 120-min ceiling inside UC pass 2): **365 windows solved** (w118 cleared: the stage raises on any infeasible window), 0 TL, MILP mean 14.6 s, nodes p50 17 | 0 | 14.6 / – / – | 61 integer after demotion (11 all-pinned demoted) | pass-1 P1 solved, objective $17.74 bn vs P0 $1.48 bn (ratio unexplained until unserved MWh is reported) | **pending**: end-to-end rerun at the PR head `7688a68a`, detached | – |
| ERCOT 2019 | pending (same 120-min ceiling) | | | | | | |

The desk ruled the demotion GENERIC, not coal-only: every `BUDGET_GEN_IDX_KEYS` row is pinned
to P0 inside a window, so the UC never decided its commitment, whatever the family. Each
A/B's D-6 card states how many clusters the UC acts on (`integer_set_size` of `integer_gate_size`).
NEISO 2021's `legitimacy_diagnostics` read FAIL on D-1 (COAL_PRB diurnal shape) and D-4 (plant 54605's
CHP floor binding outside its window). These are calibration readings for UC-2-NEISO, not
engine-gate items.

### 5.0a Two engine items found while gating (in this PR)

**Slim expand NaN (`model/uc/slim.py`, `SlimReduction.expand`).** A merged slim column is split
among its members with a running `cumsum` of member capacities over ALL merged groups. A member
with no finite upper bound (`cap = +inf`) turned every later member, in its own group and in
every later group, into `inf - inf = NaN`. On ERCOT every window warned at `slim.py:206`, and the
NaN could reach the kept dispatch (`dispatch_prev`) and the next window's ramp-boundary rows.
Fix: unbounded members sort last in their group and stay out of the running sum. Test:
`test_expand_fills_an_unbounded_member_last_and_never_returns_nan`, which raises
`FloatingPointError` on the old code. UC-DESK ruled it into this PR as a correctness defect on
the arm path of every lane.

**Per-window log line.** `UcStage.run` logs one INFO line per window (index, hours, status,
MILP s, nodes, gap), at UC-2-ERCOT's request.

**Cost finding (not changed here).** ERCOT's adaptive-expectation step re-solves P1 a second
time, and the second pass reruns the whole UC stage: UC pass 1 took 5,485 s, so the full year
is ≈195 min, about 2× the UC wall. Whether pass 2's integer schedule differs from pass 1's is
measured by the ERCOT 2020 end-to-end gate (§5.0). If the schedules are identical, reusing the
pass-1 schedule is a later speed lever.

### 5.1 A second, separate defect at the UC → P1 seam (MISO; open, not fixed here)

In MISO, P1 is infeasible after a complete UC stage. The NEISO P1s solve; NEISO has few yard
coal units. Working hypothesis, not verified (zero LP needs the P0 dispatch the failed
bundles did not write):
- the window decides `u` for a yard-pinned cluster from the P0 pin: all units online
  wherever `P0 > 0`, and, under the guard, online through short `P0 = 0` gaps inside
  their min-down;
- `UcStage.floor_and_ceiling` then floors P1 at `mlf·p̄·u` on PHYSICAL availability, so
  each such hour carries about `mlf × capacity` of output, however small (or zero) P0 was;
- P1 keeps the yard's ANNUAL energy budget (`coal_plant_budget`), and those floors can sum
  above it.

This is the §6 inconsistency at the P1 seam: inside a window a pinned row's commitment is
not a UC decision, yet P1 enforces it as one. It is not caused by uc-1.2; uc-1.1 never
reached P1 in these years. It belongs with the D-5 decision below.

## 6. The yard pin and commitment: ruled, option (a), in uc-1.2

**The UC cannot decommit pinned yard coal.** Wherever `coal_fuel_inventory_plant_grain` is
armed, a window pins every yard coal row to P0 through `availability = P0/pmax`. Row (a)
then requires `u = n` in every hour with `P0 > 0` and leaves `u` free (zero output) where
`P0 = 0`. Those clusters' commitment is therefore P0's on/off pattern; the window decides
nothing about it. Enforced in P1 as a `MECH_UC_SCHEDULE` floor (`mlf·p̄·u` on physical
availability), that pattern overran the yards' annual budget and made MISO P1 infeasible
(§5.1). The yard pin can be armed in `COAL_PLANT_GRAIN_ISOS = (MISO, NEISO, NWPP, ERCOT,
SOCO)`; the MISO, NEISO and ERCOT keepers arm it.

**UC-DESK ruling (2026-10-10, engine scope, folded into this PR):** option (a). A cluster
whose members are ALL budget-pinned carries no integer. Its commitment is the identity's
(DESIGN §2.1 pin): no `u`, no commitment rows, no `MECH_UC_SCHEDULE` floor, and P1 treats
it as the gate-off run does (markup kept). Partially pinned clusters keep their integers
under the uc-1.2 row-(a) guard. The desk ruled this engine correctness (rule 19: the yard
identity owns pinned coal), not a D-5 floor change, so no owner card.

Implementation: `params.demote_budget_pinned` (pure: integer mask cleared where every
member is in `window.budget_pinned_gens(dispatch_kwargs)`), applied once in `UcStage.__init__`.
`uc_solve_log.engine` gains `integer_gate_size` (the E1 gate's count) and
`integer_demoted_budget_pinned` (plant codes); `integer_set_size` is the count after
demotion. Tests: `test_all_pinned_cluster_carries_no_integer`,
`test_partially_pinned_cluster_keeps_its_integer`.

Consequence for reading UC benefit: in an ISO with the yard pin armed, the UC acts on gas and
unpinned coal only. Coal commitment there stays the fuel identity's.

## 7. ERCOT uc-params coverage (UC-DESK item, from UC-2-ERCOT: 52 of 139 clusters on class fallback)

Census zero LP, from UC-2-ERCOT's `uc_solve_log_2024.json` (`claude/ucmilp-2-ercot-ab-e4w1`;
139 clusters, 87 `uc-params`, 52 `none->1`) against `data/raw/campd-unit-level/TX_2023–2025`
and the crosswalk of record (`data.campd_crosswalk.crosswalk_of_record`):

| Cause | Clusters | Integer |
|---|---|---|
| Crosswalked, but no CAMPD record in the 2023–25 pool (sub-25 MW engines and CTs without CEMS; plant 127 retired 2020) | 43 | 4 (50127, 56233 CC; 127 coal; +1) |
| No crosswalk entry and not in CAMPD (34702, 49392 ST_GAS; 3 CT) | 5 | 2 |
| **Join miss: the plant files CEMS under a different CAMD id** (Hidalgo, EIA 55545 ← CAMD 7762; Arthur von Rosenberg, EIA 7512 ← CAMD 3612) | **2** | **2** |
| Out of the TX footprint (Kiamichi, EIA 55501, files under OK) | 1 | 1 |
| Same id, class mismatch (4195: a CAMPD boiler, a fleet CT) | 1 | 0 |

Most of the gap is real absence from the measured source. 43 of the 52 are CTs, and the E1
gate leaves CTs continuous, so they carry no integer. **The join defect is real but narrow:**
`scripts/lib/uc_params` groups by the raw CAMD `facilityId` and never maps to the EIA
plant code the fleet keys on, so a plant whose CEMS id differs is missed. In ERCOT that is 2
integer CC clusters; the other ISOs are not yet counted. The fix: map CAMD (facility, unit)
→ EIA plant through `crosswalk_of_record` and `campd.CAMPD_UNIT_PLANT_REMAP` before the
per-plant grouping, the identity the fleet's CAMPD binning already uses. The footprint
miss is the same kind of gap as the NV extension in `campd.ISO_STATES`. Both change the
frozen derive (rule 23: a code fix of the join, not a residual-driven re-derive) and
re-derive `uc-params` for every ISO, so they are proposed as a follow-up, not folded into
this PR (desk call).
