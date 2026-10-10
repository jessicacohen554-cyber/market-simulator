# FINDING — the slim window: what HiGHS's presolve was removing, and taking it away exactly before the solve

Lane UC-SLIM (`session_01AFhyYxUC9rdRBBPYDZnDus`, Fable), 2026-10-10, chartered by UC-DESK
(`session_01WX9W5tgYMre3Z134LZoGF6`) under owner ruling **"Try 'slim window' first"**
(decision card, 2026-10-10; context D-2 "Keep 3×; fund speedup"). Branch
`claude/ucmilp-slim-r4d`. Starting point: UC-SPEED's L3 row
(`FINDING-ucmilp-speed-window-solve-profile-2026-10-09.md` §4): SPP 2020 at **7.10×** with
the lean preset, HiGHS MIP presolve **803 s of the 1,144 s stage (70 %)**, 2.2 s per window,
removing 63 % of each window's columns and 37 % of its rows. **Year LP solved in this
session: zero** (the census below is a zero-LP build of window 0 on a solve-less capture;
every window MILP solved in this container is diagnostic-only evidence under the UC-DESK
ruling of 2026-10-04; the numbers that count are the two shards of §3–§4).

## 0. Headline

**The columns HiGHS's presolve removes are not, in the main, the pinned ones.** On SPP 2020
window 0 (57,384 columns × 17,229 rows) HiGHS removes 38,159 columns in 2.3 s. Of these only
**8,504 (15 % of the model) are fixed by their bounds** or by what a bound forces (pinned
budget units, zero-availability units, zero-CF solar hours, 540 pinned `u`/`v`/`w` triples);
dropping them before HiGHS costs 37 ms and saves HiGHS almost nothing (presolve 2.3 → 2.0 s).
The other **27,600 (48 %) are PARALLEL columns** — generator `P` columns of one zone-balance
row at one offer (SPP's legacy heat-rate bins: 899 single-row `P` columns per hour fall into
268 (row, offer) groups; the largest holds 20 units at $31.65/MWh) — which HiGHS's "parallel
rows and columns" rule merges, but only after a full first presolve pass over all 48,803
columns. Merging them before HiGHS (an exact aggregation: the same rows and offer, so any
split of the merged value is feasible and costs the same) takes HiGHS's presolve from 2.3 s to
**1.1 s** and the window MILP from **2.9 s to 1.6 s** (−45 %) with the same objective to
1e-15 and the same `u`. What HiGHS still does on the slim model is probing (0.3–0.7 s,
1,478 columns) and its dominated-column / bound-propagation passes; `presolve=off` on the
slim model is not a lever either (the root LP pays it back).

`uc_slim_window` (default **True**, born there and registered there — no committed key
moves) does both reductions in `model/uc/slim.py`: fixed columns (with forcing rows,
singleton rows, redundant / emptied rows) and parallel continuous columns, iterated to a
fixpoint, vectorized over the whole model (rule 2), ~0.1 s per window, the slim model on its
own HiGHS handle and the full handle kept for the diagnosis, relaxation and dump paths.

**Gate (§3): PASS, twice.** On the same 62 window problems (SPP 2020 January + July) the
full model and the slim model return the same objective to the gap on every one (largest
relative delta 3.9e-4, 0 of 62 beyond 1e-3; where they differ the slim incumbent is the
better one), at **−40 % MILP seconds** in the same container (presolve −55 %, root LP and tail
unchanged). **Ceiling (§4): not reached.** The full-year L3 row reads **4.96×** the shard's
own P0 + P1 (first shard, 43 windows unreduced by a float-noise stand-down since fixed) and
**5.71×** on the rerun (every window reduced, a container ~30 % slower on every phase
including the Python side; the LP iteration count is identical) against 7.10× for the
full-model lean path. The stage's remaining seconds are HiGHS's own on the slim model —
presolve 0.9–1.2 s per window (probing half of it), the root LP 0.4 s, the tail 0.3 s — and
the arithmetic of §4.2 says no further exact reduction reaches ≤ 3×: the next card is the
owner's E10 month-parallel.

## 1. The zero-LP census (SPP 2020 window 0, keeper recipe inputs captured solve-less)

Capture: `uc_bench.capture_year("SPP", 2020, solve=False)` (zero LP; 1,300 fleet rows,
2 zones); window 0 built exactly as `rung_l1` builds it, the window LP relaxation standing in
for P0 (`_relaxation_as_p0`, a 36-hour LP, diagnostic-only; 23 budget-pinned generators, 92
integer clusters, 489 guard rows). The shards (§3–§4) carry the same census per window on
the real P0.

### 1.1 What is in the 63 %

| reduction | columns removed | rows removed | cost | exact? |
|---|---|---|---|---|
| HiGHS MIP presolve (`Highs.presolve()`, the same reductions the MIP log prints) | **38,159** (66 %) → 19,225 | **7,358** (43 %) → 9,871 | 2.3–2.5 s | — |
| **slim: bound-fixed columns** (`lower == upper`: `P` 6,840 of 46,800 — pinned budget units and zero-availability units; solar `S` 44 of 72; `u` 540 of 3,312 with their `v` / `w`) | 7,424 | — | | yes (constant, offset) |
| **slim: forcing rows** (the min-down / guard rows with `n − hist_w = 0`, logic rows of pinned clusters) | 555 | → redundant | | yes (feasible set) |
| **slim: singleton rows** (one unfixed column: a bound) | 525 | 560 | | yes |
| **slim: redundant rows** (activity range inside the row bounds) | — | 4,465 | | yes |
| **slim subtotal: fixed** | **8,504 (15 %)** | **5,025 (29 %)** | 37 ms | |
| **slim: parallel continuous columns** (same column of `A`, same offer; 9,792 groups) | **27,576 (48 %)** | — | ~60 ms | yes (exact aggregation) |
| **slim total** | **36,080 (63 %)** → 21,304 | **5,025 (29 %)** → 12,204 | 0.10–0.25 s | |
| HiGHS presolve on the slim model | 1,935 (probing 1,478) → 19,225 | 2,333 → 9,871 | 1.1–1.2 s | — |

HiGHS reaches the same 19,225 × 9,871 model from the full and from the slim window (the
reductions compose), so the slim window changes nothing about what HiGHS solves — only how
much of the way there it has to walk itself.

### 1.2 Which HiGHS rule, and what it costs (`presolve_rule_off` bitmask, `Highs.presolve()` only — zero LP)

| rule switched off | columns left after presolve | presolve s |
|---|---|---|
| none (baseline) | 19,225 | 2.42 |
| bit 13 **parallel rows and columns** | **47,089** | 2.25 |
| bit 15 **probing** | 20,795 | **1.62** |
| bit 9 doubleton equation | 19,233 | 2.33 |
| bit 14 sparsify | 19,261 | 2.23 |
| every other bit (6–8, 10–12, 16) | 19,225 | 2.2–2.4 |
| (integrality dropped: the LP relaxation) | 19,188 | 1.65 |

The parallel-column rule accounts for 28 k of the 38 k columns and is itself cheap; the
seconds are the presolve passes that run over those columns before the rule fires, plus
probing (0.7 s) once integrality is present. `Highs.presolve()` prints the rule table only with
`presolve_rule_logging` AND `log_dev_level ≥ 1` (the UC-SPEED `rulelog` arm had the former
only); the printed reductions on window 0 are "Sparsify 0.8 %", "Fixed 19 dominated columns",
"1841 probing evaluations: 1478 deleted columns".

### 1.3 Window 0 MILP, full vs slim (lean preset; diagnostic-only, same container, same window problem)

| model | columns × rows HiGHS receives | presolve s | root LP s | tail s | MILP s | objective | gap | `u` cells differ | reinsertion residual (col / row) |
|---|---|---|---|---|---|---|---|---|---|
| full (uc-1.1) | 57,384 × 17,229 | 2.45–2.52 | 0.40–0.42 | 0.01 | **2.90–3.00** | −4,399,639.8872 | 4.6e-5 | — | 2.8e-14 / 7.3e-12 |
| slim | 21,304 × 12,204 | 1.14–1.24 | 0.40 | 0.01 | **1.58–1.70** (+0.1–0.25 reduce) | −4,399,639.8872 (rel Δ 1.1e-15) | 4.6e-5 | **0** | 8.0e-11 / 7.3e-12 |
| LP relaxation, full / slim | | | | | 1.86–1.96 / **0.43–0.47** | −4,399,840.5748 both | | | |

Reinsertion: the slim solution expanded into the full column space (fixed values reinserted,
merged members split) satisfies every full-model column and row bound to 8e-11 MW — the
solver's own tolerance — and reproduces the objective exactly (`slim.full_row_residuals`).

### 1.4 Reading

* **Why fixed columns alone could not pay:** HiGHS's "fixed column" rule is among the ones
  that cannot be switched off and runs first and cheaply (the log's first line, "48,803 cols
  0s", is the model after it). Taking 8.5 k columns away buys ~0.3 s of 2.3.
* **Why parallel columns pay:** HiGHS's first presolve pass (bound propagation, dominated
  columns, the parallel-column hash over every column) runs over 48,803 columns; after the
  slim merge it runs over 21,304. The merge is exact in the strictest sense — the slim
  feasible set is the projection of the full one and the objective is identical — and the
  per-member dispatch it discards is a quantity the full window itself leaves undetermined
  (an equal-cost tie HiGHS's own postsolve resolves arbitrarily).
* **The pin is exact by construction, not by tolerance.** A budget-pinned unit's `P` carries
  `min_gen = min(p_pin, pmax·avail)` and `ub = pmax·avail` with `avail = p_pin / pmax`; the two
  agree bit-for-bit in half the cases and by one ulp in the rest. The reduction fixes only
  `lower == upper` exactly, so a one-ulp pin stays a column (HiGHS fixes it inside its own
  tolerance); nothing in the window build was changed to force the equality.

### 1.5 The first shard pair, and the stand-down that was float noise

The first L3 shard (`180b4812`, §5) reduced 322 of 365 windows: every window of 2 April –
30 April and 20 September – 10 October (43 windows, two contiguous blocks) solved on the full
model because the reduction read one row as unsatisfiable by **3.9e-15**. Reproduced here
zero-LP (the keeper's committed P1 dispatch standing in for P0, the UC-1-FIX precedent): the
row is an output-coupling row (a) `Σ P − p̄·a·u ≤ 0` of a cluster with a budget-pinned
member, whose pinned `P` (`pmax · (p_pin / pmax)`) and the cluster's `p̄ · a · n` agree in real
arithmetic and differ by a few ulp in float — the activity minimum lands at +4e-15 against
an upper bound of 0. The contradiction test now carries `ROW_TOL = 1e-9` (relative; a miss
inside it is float noise: nothing is forced or dropped — those tests stay exact equalities —
the row simply stays for HiGHS; beyond it the full model is infeasible and the reduction
stands down, naming the reason in `uc_solve_log` through `slim.LAST_STAND_DOWN`). The ten
probed windows (April, October and controls) all reduce after the fix; the 62 windows of the
first L2 shard were all reduced before it (the fix touches no reduction they took), and both
rungs were re-run at the fixed SHA (§3–§4).

## 2. What landed (G-DRIFT: every hunk inside the gate-on path; goldens untouched)

* `model/uc/slim.py` (new): `reduce_lp` (fixed / forcing / singleton / redundant / empty, then
  `parallel_groups` — an exact lexicographic grouping of the padded `(nnz, cost, row, value, …)`
  key, no hashing), `SlimReduction.restrict` / `expand` / `slim_index`, `slim_handle`
  (`passModel` of the slim arrays with the offset, options copied from the full handle),
  `reduce_window`, `full_row_residuals` (the reinsertion check).
* `model/uc/window.py`: `UcWindowModel(slim=…)`, `h_solve`, `u_cols_full` / `u_cols_solve`,
  `set_u_integrality`, `to_solve_space` / `from_solve_space`; `WindowResult.slim_columns /
  slim_rows / slim_counts / slim_s`.
* `model/uc/solve.py`: solves on `window.h_solve`, restricts the warm start, expands the
  solution; the relaxation rung toggles integrality on the solving handle; the diagnosis
  relaxation stays on the full handle; `phase["slim_s"]`.
* `pipeline/uc.py`: `uc_slim_window` → the window; `windows[].slim` (reduced, columns, rows,
  census), `summary.slim_sums`, `phase_sums.slim_s`, `engine.fields.uc_slim_window`.
* `config/scenarios.py`: `uc_slim_window: bool = True`, registered in
  `_CACHE_KEY_OPTIONAL_FIELDS` at `'True'`, `TIER_TAGS` 1 — born at its value and dropped from
  the hash there, so **every committed key is unmoved** (G-KEYS; no keeper arms the gate).
* Matrix: the `unit_commitment_milp` row's `def` names the tenth sub-field (no new row: an
  exact model reduction is not a mechanism; `check_mechanism_matrix --base origin/main` ok;
  `check_cache_key_registration` ok).
* Bench: L2 arms `noslim` (the uc-1.1 full-model path, paired against a base at the registry
  default), `slim`, `slim_noprobe` (measurement only: HiGHS probing off on the slim model);
  `slim_sums` per month; `l2_profile.md` columns `slim Σ` and `solved cols`; the L3 row carries
  `slim_sums`.
* Tests (fast tier, `tests/unit/model/uc/test_slim.py`, 16): each reduction on a hand-built
  LP, the contradiction stand-down, the explicit-zero entry, parallel merge (integers never),
  restrict / expand round trip with a full-model feasibility check, HiGHS's offset in the
  objective and the MIP dual bound, the toy windows (no-load decommit, relaxation, carried
  min-down, warm start, storage boundary) slim = full in objective and `u` with the expanded
  solution feasible on the full model, an infeasible window diagnosed on the full model, the
  stage's 72-hour rolling schedule identical with the slim on and off, the field's
  registration. The 37 pre-existing UC tests pass unchanged.
* No engine-version bump: `uc-1.1`'s formulation is unchanged; the slim model is the same
  model.
* Rebased onto `main` at `dc3860be` (PR #7221's time-major transfer-limit slice, #7220's desk
  rulings, #7219's `coal_sync_floor_release`) before the PR: no conflict, every check green on
  the rebased head. The four shards ran at `180b4812` / `45b4f5dc` on the pre-#7221 window;
  the slim reduction is model-agnostic (it reads whatever the window builder hands HiGHS), so
  the gate and the census transfer, and the L3 wall row is the pre-#7221 window's.

## 3. The equivalence gate (paired; SPP 2020 January + July)

`base` = the registry default (slim on, lean), rolling, recording its handed-over state at
every 24-hour frontier; every other arm solves the base run's exact window problems
(`UcStage.run(pin=...)`) and is compared window by window. 62 windows (31 + 31); every base
window reduced (62 / 62). Container: 4 cores, `MARKET_SIM_HIGHS_THREADS=1`.

### 3.1 First pair (`180b4812`; shard `session_01XBNF3CEmmsoQJ9hcBKg5Pa`, branch `claude/ucmilp-bench-spp-2020-L2-slim` `b925e34e`; capture 213 s)

| arm | what | wall s Jan / Jul | MILP Σ s | presolve Σ | root LP Σ | tail Σ | slim Σ | solved cols (mean) | kept `u` = base | max rel Δobj | windows > gap | Σ (arm − base) objective |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **base = slim** | `uc_slim_window=True` | **106.5 / 86.5** | 175.5 | 94.1 | 37.1 | 40.3 | 10.3 | 22,745 | — | — | — | — |
| noslim | the uc-1.1 full-model path | 161.0 / 138.5 | 291.9 | 211.1 | 37.7 | 37.7 | 0.0 | 57,384 | 53 / 62 | **3.9e-4** | **0** | +$67 Jan, +$7,050 Jul |
| slim_noprobe | slim + HiGHS probing off (measurement) | 81.5 / 67.2 | 130.2 | 50.9 | 37.1 | 38.3 | 10.7 | 22,745 | 39 / 62 | 8.1e-4 | 0 | +$5,678 Jan, −$5,459 Jul |

Reading:

* **Gate: PASS.** On the same 62 window problems the full model and the slim model return the
  same objective to the declared gap (1e-3) on every one — the largest relative delta 3.9e-4,
  one January window and eight July windows differ at all, and where they differ the slim
  window's incumbent is the better one (the full model's objective sum is $7,117 higher over
  the two months). The kept `u` differs in 9 of 62 windows (59 cluster-hours): the within-gap
  ties UC-SPEED's gate describes, taken differently because HiGHS walks a different (smaller)
  model to the same bound.
* **Wall: slim −34 % (January) / −38 % (July)** against the full-model path in the same
  container; MILP seconds −40 % over the two months, presolve 211 → 94 s (−55 %), the root LP
  and the tail unchanged (37 s each), the reduction itself 10 s over 62 windows (0.17 s per
  window, of which the first window pays import-time warm-up).
* **Probing off is a further −23 % wall** (presolve 94 → 51 s), within the gap on every window
  but with 23 of 62 kept schedules differing from base and a two-sided objective delta
  (+$5.7 k January, −$5.5 k July): a solver-path change of the `uc_solver_preset` class, not a
  reduction, reported as a measurement for the desk — not armed, not a registry value.

### 3.2 Final pair (`45b4f5dc`, after the `ROW_TOL` fix of §1.5; shard `session_01WUhRgRyjXnKSPgdcaTMFJG`, branch `claude/ucmilp-bench-spp-2020-L2-slim2` `735018a5`; capture 150 s)

| arm | what | wall s Jan / Jul | MILP Σ s | presolve Σ | root LP Σ | tail Σ | slim Σ | solved cols (mean) | kept `u` = base | max rel Δobj | windows > gap | Σ (arm − base) objective |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **base = slim** | `uc_slim_window=True` | **79.0 / 63.9** | 129.3 | 66.9 | 28.3 | 31.2 | 7.4 | 22,745 | — | — | — | — |
| noslim | the uc-1.1 full-model path | 116.4 / 103.4 | 213.6 | 151.9 | 28.7 | 29.2 | 0.0 | 57,384 | 53 / 62 | **3.9e-4** | **0** | +$67 Jan, +$7,050 Jul |
| slim_noprobe | slim + HiGHS probing off (measurement) | 61.7 / 49.2 | 97.2 | 36.8 | 27.9 | 29.6 | 7.8 | 22,745 | 39 / 62 | 8.1e-4 | 0 | +$5,678 Jan, −$5,459 Jul |

The rerun reproduces the first pair exactly in every equivalence column (the same 53 / 62,
3.9e-4, 0; the same objective sums to the dollar: the `ROW_TOL` fix changes no reduction these
windows take) and reads every wall 25–30 % lower in a faster container — the cross-container
noise UC-SPEED reported. In-container: **slim −32 % / −38 % wall, −39 % MILP seconds, presolve
−56 %**; probing off a further −25 % wall. 62 / 62 base windows reduced.

## 4. The L3 wall row (SPP 2020, full year)

`replay_keeper.py results/calibration/closeout_spp_nuc_span --years 2020 --set
unit_commitment_milp=true` at the registry defaults (slim on, lean); 4 cores,
`MARKET_SIM_HIGHS_THREADS=1`; denominator = the shard's own P0 + P1 (the UC-2-SPP PRECOMMIT
§5 proxy).

### 4.1 GATESPEC §6.1 rows

| ISO-year | baseline P0+P1 s | P0 s | UC Σ s (windows, mean, p95 MILP s) | P1 s | total s | **ratio** | integers/window | nodes p50/p95 | gap p95 | time-limit hits | peak RSS GB |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SPP 2020 (slim, `180b4812`, first shard: 322 / 365 windows reduced) | 188.5 | 97.1 | 685.7 (365, 1.71, 2.80) | 91.4 | 935.4 | **4.96** | 3,312 | 1 / 1 | 5.4e-4 | 0 | 5.08 |
| SPP 2020 (slim, `45b4f5dc`, final: 365 / 365 windows reduced) | 199.9 | 103.4 | 863.7 (365, 2.11, 3.35) | 96.5 | 1,141.6 | **5.71** | 3,312 | 1 / 1 | 5.5e-4 | 0 | 5.08 |
| SPP 2020 (lean, full model, `5dc76955`, UC-SPEED) | 199.4 | 100.6 | 1,144.5 (365, 3.07, 4.28) | 98.8 | 1,415.0 | 7.10 | 3,312 | 1 / 1 | 5.5e-4 | 0 | 5.09 |
| SPP 2020 (uc-1.1 path, `ae224faf`, UC-2-SPP) | 198.9 | 97.7 | 1,106.9 (365, 2.97, 4.23) | 101.2 | 1,367.1 | 6.9 | 3,312 | 1 / 1 | 5.7e-4 | 0 | 5.09 |

First shard, where the 685.7 s go (`summary.phase_sums`): **presolve 359.6 s (52 %)** (803 s
in UC-SPEED's run: −55 %), root LP 131.6 s (157), tail 118.6 s (138), pre-root 7.0, HiGHS
setup/report 7.4, the reduction 37.9 s (0.11 s per window p50), the rest of the Python side
22 s (UC rows 14.8, slicing 3.8, extract 1.7). 365 / 365 windows Optimal, 322 reduced (the
43 April / October windows of §1.5 solved on the full model: MILP p50 2.32 s against 1.36 s
for a reduced window). Phase timing line: `solve_p0=97.1s markup=704.1s solve_p1=91.4s
total=935.4s`. Census over the 322 reduced windows: 2.39 M columns fixed by bounds, 0.22 M by
forcing rows, 0.16 M by singleton rows, **8.41 M merged as parallel**, 1.51 M rows redundant,
0.17 M singleton; the solved model 26,682 columns × 12,595 rows on average.

Final shard (`session_01QKd8EhdSAb91BusFbeEe5r`, branch `claude/ucmilp-bench-spp-2020-L3-slim2`
`b7400b77`), where the 863.7 s go: presolve 429.6 s (50 %), root LP 176.6 s, tail 145.1 s,
pre-root 8.7, HiGHS setup/report 9.6, the reduction 64.7 s (0.14 s per window p50, 0.33 p95),
the rest of the Python side 27 s. 365 / 365 Optimal and reduced; presolve p50 1.17 s / p95
1.34 s; MILP p50 1.80 s / p95 3.35 s / max 4.16 s. Phase timing line: `solve_p0=103.4s
markup=883.8s solve_p1=96.5s total=1141.6s`. Census over 365 windows: 2.74 M columns fixed by
bounds, 0.24 M by forcing rows, 0.18 M by singleton rows, **9.52 M merged as parallel**,
1.70 M rows redundant, 0.19 M singleton; the solved model 22,579 columns × 12,018 rows on
average (of 57,384 × ~17,300).

### 4.2 Reading

* **Target ≤ 3× not met; best measured 4.96×, 5.71× at the final SHA.** The two L3 rows are
  not a regression between SHAs: the rerun does strictly less HiGHS work (365 reduced windows
  against 322; the same 854.9 k simplex iterations) and every phase, the pure-Python
  reduction included (37.9 → 64.7 s for the same numpy), is 25–35 % slower — the container,
  not the model. The paired L2 pairs (§3), which measure both paths in one container, are the
  clean number: the slim window takes **39–40 % of the MILP seconds** off the stage, all of it
  presolve (−55 %); UC-SPEED's full-model stage at 1,144 s would read ≈ 700 s in its own
  container, ≈ 5× its P0 + P1.
* **Why no exact reduction reaches 3×.** With every window reduced the stage is 864 s of
  which presolve 430, root LP 177, tail 145, Python 110 (reduction 65). The ceiling needs the
  stage ≤ 3 × 200 − 200 = 400 s. Root LP + tail + Python alone are 430 s — above the ceiling
  with presolve at zero — and they are not reducible by a model transformation that keeps the
  feasible set: the root LP solves the same relaxation on a smaller matrix in the same
  iterations (28.3 s vs 28.7 s over 62 windows, §3.2), the tail is the branch-and-bound to the
  gap. What remains in presolve is HiGHS's probing (half of it; `slim_noprobe` −25 % wall but
  a two-sided within-gap change of the schedule, a solver-path choice for the desk, not a
  reduction) and its bound-propagation / dominated-column passes.
* **The owner's card is therefore the one the charter named: E10 month-parallel** (rule-36
  amendment), which divides the stage's wall by the parallelism without changing a window.
  With the slim window on, the stage per year is ≈ 700–860 s of single-thread MILP; two
  parallel months reach ≈ 2.6–3.1×, three ≈ 2.1–2.4×, against the ISO-year's own P0 + P1.
* **What the slim window is, for the record:** an exact transformation that stays on at no
  cost to the optimum (the same objective class in every paired window; the full `col_value`
  and per-unit dispatch reinserted), −40 % of the stage's MILP seconds, and the census that
  names what the window's columns are (a quarter pinned or fixed, half parallel duplicates of
  one offer in one zone row) — the structural fact behind UC-SPEED's "presolve removes 63 %".

## 5. Shards (rule 33)

| shard | session | SHA | branch (transport) | state |
|---|---|---|---|---|
| L2 paired equivalence, Jan + Jul (first pair) | `session_01XBNF3CEmmsoQJ9hcBKg5Pa` | `180b4812` | `claude/ucmilp-bench-spp-2020-L2-slim` `b925e34e` | fetched, verified, archived |
| L3 full year (first) | `session_01JC2FQPTUCpbRoEz6kvj3xG` | `180b4812` | `claude/ucmilp-bench-spp-2020-L3-slim` `9a4e2553` | fetched, verified, archived |
| L2 paired equivalence, Jan + Jul (final) | `session_01WUhRgRyjXnKSPgdcaTMFJG` | `45b4f5dc` | `claude/ucmilp-bench-spp-2020-L2-slim2` `735018a5` | fetched, verified, archived |
| L3 full year (final) | `session_01QKd8EhdSAb91BusFbeEe5r` | `45b4f5dc` | `claude/ucmilp-bench-spp-2020-L3-slim2` `b7400b77` | fetched, verified, archived |

Bench branches carry JSON, markdown and logs only (no dispatch bundle, no capture pickle; each
L3 shard's bundle was moved to `/tmp` inside its container and dies with it — a bench
artefact, never registrable). The owner may delete the four branches once this PR merges (a
session cannot, 403).

## Log entry

- 2026-10-10 · UC-SLIM `session_01AFhyYxUC9rdRBBPYDZnDus` (Fable) · `claude/ucmilp-slim-r4d` · zero LP in the
  parent · four bench shards (L2 paired Jan + Jul and L3 full year at `180b4812`, both again at `45b4f5dc`) ·
  **the 63 % HiGHS presolve removes is 15 % bound-fixed columns (cheap) and 48 % parallel P columns (one
  zone row, one offer — the costly first presolve pass)** · `model/uc/slim.py`: fixed / forcing / singleton /
  redundant rows + exact parallel-column merge, ~0.1 s per window, slim handle + full handle kept ·
  `uc_slim_window` born at True (no committed key moves) · paired gate PASS twice (max rel Δobj 3.9e-4, 0/62
  beyond gap, slim incumbents the better ones), −40 % MILP seconds, presolve −55 % in-container · a 4e-15
  float residual on a budget-pinned cluster's coupling row stood the reduction down on 43 April/October
  windows of the first L3 → `ROW_TOL` · **L3 SPP 2020 ratio 4.96× (first) / 5.71× (final SHA, slower
  container); target ≤ 3× not met, and not reachable by an exact reduction (root LP + tail + Python alone
  exceed the ceiling)** · `slim_noprobe` −25 % wall, within gap, two-sided (desk's call) · next card: E10
  month-parallel (owner) · PR "uc-milp UC-SLIM: slim window" · no promotion, no registration.
