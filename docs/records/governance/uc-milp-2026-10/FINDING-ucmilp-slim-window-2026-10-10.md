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
own HiGHS handle and the full handle kept for the diagnosis, relaxation and dump paths. The
gate (§3) is the paired equivalence run UC-SPEED established; the L3 row (§4) is the ratio.

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

## 3. The equivalence gate (paired; SPP 2020 January + July)

_Pending the L2 shard — filled in by the parent from `l2.json` / `l2_profile.md`._

## 4. The L3 wall row (SPP 2020, full year)

_Pending the L3 shard — filled in by the parent from `l3.json` / `wall_table.md`._

## 5. Shards (rule 33)

_Pending._

## Log entry

_Pending._
