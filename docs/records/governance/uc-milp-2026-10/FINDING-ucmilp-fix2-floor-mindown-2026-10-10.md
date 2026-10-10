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

`tests/unit/model/uc/test_window_pinned_floor_guard.py` (new; 4 of 5 fail on uc-1.1):

* `test_pinned_row_needs_every_unit_the_unpinned_fleet_does_not`: pin 150 / 50 MW on 2 × 100 MW gives need `[0,2,2,2]`; the unpinned fleet gives `[0,0,0,0]` (the uc-1.1 guard's view).
* `test_window_fleet_is_hour_local`: the guard's slice equals the next window's.
* `test_window_bound_matches_row_a_under_a_pin`: `u` lower bound 2 at a 50 MW pin; a carried min-down raises with **the plant, its pinned members and the hours named** in the text.
* `test_guard_keeps_units_a_later_pin_needs[150.0|50.0]`: the stage over 72 h, W=24, L=2; the pin restarts one hour past window 0's horizon. On uc-1.1 the stage raises at window 1 with `min_down=2; floor above min-down: 2` (150 MW) and `ceiling=2, min_down=2` (50 MW), the MISO signatures. On uc-1.2 every window is Optimal and no stop falls inside the pin hour's min-down.

Amended: `test_units_needed_for_floor_uses_the_lp_effective_floor` now expects `[2,2,2,2,2,2]`.
The uc-1.1 value of 1 unit at `a = 0.25` was a `u` row (a) cannot hold.

## 4. Diagnosis (UC-2-MISO could not name plants)

`diagnose_window` adds `clusters_floor_above_min_down` and `clusters_ceiling_contradiction`
(plant_code, family, n, dt_h, ut_h, pinned/total members, hours, the bound values). The
`UcWindowInfeasible` text carries them. `bench_uc_ladder.py --dump-dir` now also serves L2
(`l2_infeasible.json` plus a per-arm dump).

## 5. Results

(filled from the shards)

## 6. Desk flag (D-5, not changed here)

Under the yard pin, a pinned MISO coal cluster must hold `u = n` in every hour with
`P0 > 0`; uc-1.1 already did this inside each window. The MILP therefore cannot decommit
MISO yard coal while `coal_fuel_inventory_plant_grain` is armed, and the UC's commitment
benefit for that coal is structurally close to nil. The same holds for any integer cluster
whose rows a budget family pins: the same yard pin is armed in NEISO and ERCOT.
