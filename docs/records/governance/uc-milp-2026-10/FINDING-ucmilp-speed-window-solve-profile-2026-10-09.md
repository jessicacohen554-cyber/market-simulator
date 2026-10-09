# FINDING — where the UC window's seconds go, the lean solver path, and the paired equivalence gate

Lane UC-SPEED (`session_01KhMnMmEfydP4sHykH9xrCS`, Fable), 2026-10-09, chartered by UC-DESK
(`session_01WX9W5tgYMre3Z134LZoGF6`) under owner ruling **D-2 "Keep 3×; fund speedup"**
(decision card, 2026-10-09): the UC stage's total must stay ≤ 3× the ISO-year's own P0 + P1
wall before any keeper arms it. Branch `claude/ucmilp-speed-q8n`. Starting point: UC-2-SPP's
wall rows (`RESULT-ucmilp-spp-ab-2026-10-04.md` §0.2), SPP 2019–2025 at 5.1–10.2×, every
window solved at the root (nodes p50/p95 = 1/1), 3.0–3.4 k integers, 1 thread.
**LP solved in this session: zero** (three bench shards, rule 32; local probes on a synthetic
fleet only, marked as such).

## 0. Headline

**The window's seconds are HiGHS's own, not the model build.** On SPP 2020 January (31 rolling
36-hour windows, 160 s of `run()`), MIP presolve takes **49 %**, the post-root tail (rounding,
central rounding, sub-MIP, root restart with its second presolve) **33 %**, the root LP **9 %**,
the LP-free feasibility jump **7 %**; building the window model is 1.7 s per month (1 %). Plan
E6 (one HiGHS model per window shape) therefore cannot buy more than ~1 % and is **not
implemented**; plan E3's basis carry **cannot reach a MIP root** (HiGHS ignores a user basis
there — measured, identical iteration counts), and the `setSolution` incumbent it does accept
is kept (off: +8 % wall). **Presolve pays for itself** — with it off the root LP costs 4.5× and
the tail 1.5× more — so the fast path keeps it and drops what the profile shows as pure
overhead: the feasibility jump, the LP heuristics and the root restart. That is the new
registry default `uc_solver_preset = "lean"`; the uc-1.1 path survives as `"highs_default"`.
Four threads buy 2 % (no production knob). The 48 + 24 h horizon (E2) costs the same wall for
half the windows.

**The rolling schedule hash is not an equivalence gate.** Two solver paths that both stop
within `uc_mip_rel_gap` of the bound can take a within-gap tie differently; from that window
on every later window is a *different problem* (its carried state changed), so objectives and
schedules diverge for reasons that have nothing to do with the optimum. The gate this record
uses is **paired**: the arm solves the base run's exact window problems (same carried state,
`UcStage.run(pin=...)`) and must return the same objective to the gap on every one of them.
**Gate result (§3): the lean path returns the same optimum as the uc-1.1 path on all 62 paired
window problems** (largest relative objective delta 8.9e-4, 0 windows beyond the 1e-3 gap; July
identical to machine precision), at −23 % wall in January and −7 % in July.

**The ceiling is not reached (§4).** The full-year L3 row at the final SHA reads **7.10×** the
shard's own P0 + P1 (UC Σ 1,144.5 s over 365 windows, mean 3.07 s, every window Optimal at the
root), against 6.9× for the uc-1.1 path in the UC-2-SPP shard. Of the stage, **MIP presolve is
803 s (70 %)**, the root LP 157 s, the tail 138 s, the Python side 24 s. Presolve alone is 4× the
baseline, so no setting of the search (heuristics, restarts, threads, horizon) can reach 3×: the
stage cannot arm for SPP at this structure. The next lever is the presolve cost itself —
presolve removes 63 % of the window's columns and 37 % of its rows at 2.2 s per window; building
the window without those fixed columns (an exact transformation, inside `model/uc/window.py`)
is the in-lane candidate, E10 month-parallel the owner's (§4.2).

## 1. Facts

### 1.1 The profile shard (SPP 2020, January, 31 windows; shard `session_0151fzU7u47JRsH9vhuh24ir` at `84e928ef`, branch `claude/ucmilp-bench-spp-2020-L2-speed` `f213b765`)

Container: 4 cores, `MARKET_SIM_HIGHS_THREADS=1`, ceiling 13.36 GiB, swap 10 GiB added; capture
(one P0 + P1 of SPP 2020) 158 s. Every arm 31 windows of the same month, rolling (each arm
carries its own state — see §3 for why the last three columns are not an equivalence verdict).

| arm | what it changes | wall s | MILP Σ s | presolve Σ | pre-root heur Σ | root LP Σ | tail Σ | LP iters | heur iters | nodes p95 | gap max |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **base** (uc-1.1 path) | — | **162.9** | 159.7 | 79.0 | 11.2 | 14.8 | 53.3 | 91,453 | 6,404 | 1 | 9.7e-4 |
| presolve off | `presolve=off` | 171.4 | 167.9 | 0.0 | 16.8 | **67.1** | **80.3** | 89,349 | 3,008 | 1 | 9.8e-4 |
| fj off | feasibility jump off | 156.6 | 153.0 | 83.2 | **0.8** | 15.4 | 52.4 | 91,453 | 6,404 | 1 | 9.7e-4 |
| lpheur off | RINS/RENS/root-rc off, effort 0 | 153.4 | 149.9 | 82.5 | 12.0 | 15.8 | **38.4** | 89,582 | 0 | 1 | 9.7e-4 |
| restart off | root restart off | 144.8 | 141.2 | 82.7 | 11.6 | 15.3 | **30.4** | 80,012 | 4,223 | 1 | 7.4e-4 |
| symmetry off | symmetry detection off | 168.6 | 164.9 | 82.1 | 10.5 | 15.0 | 56.0 | 91,453 | 6,404 | 1 | 9.7e-4 |
| warm off | no `setSolution` | 176.7 | 173.0 | 85.2 | 12.5 | 16.5 | 57.5 | 91,453 | 6,404 | 1 | 9.7e-4 |
| threads 4 | 4 threads, `parallel=on` | 160.4 | 156.9 | 82.5 | 11.4 | 15.8 | 45.9 | 91,453 | 6,404 | 1 | 9.7e-4 |
| prefix on (E5) | `uc_prefixing=true` (371 fixed on / 495 off of 2,852) | **130.4** | 126.7 | 75.1 | 10.4 | 13.9 | **26.1** | 79,220 | 3,560 | 1 | 7.6e-4 |
| lean (as shipped to the shard: presolve off + fj + lpheur off) | | 147.3 | 143.8 | 0.0 | 1.9 | 67.1 | 71.0 | 88,278 | 0 | 2 | 9.8e-4 |
| wide (E2: 48 + 24 h, 16 windows) | optimum-changing | 173.3 | 169.8 | 92.5 | 17.1 | 20.4 | 38.2 | 88,082 | 0 | 1 | 8.9e-4 |

Base phase sums in full: setup 80.1 (of which presolve 79.0), pre-root heuristics 11.2, root LP
14.8, tail 53.3, report 0.2; stage timers: slice 0.06, LP build 0.13, UC rows 1.52, warm vector
0.04, `setSolution` 0.20, extract 0.11, keep 0.00 — **the Python side is 2 s of 162**. LP
iterations 91,453 of which 1,107 separation and 6,404 heuristics. Incumbent sources (first
letter = first incumbent): `R` ×13, `RC` ×9, `RCL` ×3, `RL` ×1, `RR` ×1, `RRC` ×1, `RRCL` ×1,
`T` ×2 — HiGHS's randomized rounding supplies the first incumbent in 29 of 31 windows right
after the root LP; the user solution never did (`warm_feasible` 0 in every arm: the
P0-derived `u` guess violates min-up/min-down, so HiGHS's fixed-integer repair LP is
infeasible), yet removing it costs 8 % — it still steers the search.

### 1.2 Zero-ISO-data diagnostics (synthetic 92-cluster window, this container; evidence for the mechanism only, never a number in a table)

* A MIP root LP takes no user basis: `setBasis` from an identical solved model, then `run()`
  → 7,245 iterations both ways. Plan E3's "root LP basis from the previous window" is
  unreachable through the HiGHS API; only `setSolution` is.
* The LP relaxation of the same window with a carried basis solves in 0 iterations / 0.02 s
  against 9,038 / 0.76 s cold — the saving E3 would have bought had the MIP accepted it.
* `mip_lp_solver` ipm / pdlp at the root: no faster than simplex (ipm 1.8× slower).
* HiGHS fixes its process-global scheduler's thread count at the first solve: a later `run()`
  with a different `threads` option returns `kError` / `Not Set` (the bench's threads arm now
  resets the scheduler around itself; a production thread knob would have to do the same
  around P1 — not built, E7 shows no gain).

## 2. Lever verdicts (plan §4, charter order)

| lever | verdict | evidence |
|---|---|---|
| **E6** incremental model | **not implemented — cannot help.** Build is 1.7 s of 162 s per month (SPP 2020 L1: 0.04 s build vs 4.2 s MILP). | §1.1 stage timers |
| **E3** warm start / basis carry | **basis: unreachable** (MIP root ignores a user basis). **Incumbent: kept** (`setSolution`; off +8 %). A feasible-by-construction warm vector (hold the previous window's `u` through the tail) would make it an incumbent but not a better one; not built. | §1.1 warm arm, §1.2 |
| **E5** pre-fixing | −21 % wall in January (tail 53 → 26 s; 30 % of cluster-windows fixed). Optimum-preservation: §3 (paired). Default stays `False`: flipping a registered default re-keys every keeper (`_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`, the W0 precedent) — an owner call; an A/B PRECOMMIT may arm it declared. | §1.1, §3 |
| **E7** threads | 4 threads −2 %: **no production knob**. Harness arm only (`UcSolveOptions.threads`, scheduler reset); the container pin stays. | §1.1 |
| presolve | **keep on** (off: +5 % wall; root LP 15 → 67 s). It is also half the window: the one remaining large lever, inside HiGHS (§4). | §1.1 |
| feasibility jump | **off** in `lean` (−4 %; never the incumbent). | §1.1 |
| LP heuristics (RINS/RENS/root reduced cost) | **off** in `lean` (−6 %; 6,404 heuristic LP iterations removed). | §1.1 |
| root restart | **off** in `lean` (−12 %; its second presolve is a third of the tail). | §1.1 |
| symmetry detection | keep (off +3 %). | §1.1 |
| **E2** wider window | 72-h windows cost the same wall for half the count (16 windows 170 s vs 31 windows 160 s): presolve and root LP scale with the window. Not a wall lever; it is an optimum-changing horizon declaration for a PRECOMMIT. | §1.1 wide |

`lean` as shipped to the profile shard had presolve off (the synthetic probe said presolve
was overhead; §1.2 is why that probe misled: a synthetic single-zone fleet has nothing for
presolve to remove, the real window has pinned budget units, dead availability and reserve
rows). The shipped composition is **presolve on, feasibility jump off, LP heuristics off, root
restart off, symmetry on** (`model/uc/solve.py::UC_SOLVER_PRESETS`); the arms' sum predicts
≈ 115–125 s for January against 160 (−25 %); the paired shard measures it (§3).

## 3. The equivalence gate (paired; SPP 2020 January + July at `5dc76955`)

Shard `session_01XQnF2Nmhz65LrZQ91JPgtc`, branch `claude/ucmilp-bench-spp-2020-L2-equiv`
`71f3f861`; capture 177 s. `base` = the registry default (`lean`), rolling, recording its
handed-over state at every 24-hour frontier; every other arm solves the base run's exact window
problems (`UcStage.run(pin=...)`) and is compared window by window. 62 windows (31 + 31).

| arm | what | wall s Jan / Jul | MILP Σ s | presolve Σ | pre-root Σ | root LP Σ | tail Σ | kept `u` = base | max rel Δobj | windows > gap | Σ (arm − base) objective |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **base = lean** | presolve on; fj, LP heuristics, restart off | **137.0 / 116.4** | 245.7 | 176.0 | 1.6 | 33.0 | 32.3 | — | — | — | — |
| legacy | the uc-1.1 path (`highs_default`) | 177.1 / 125.4 | 295.0 | 167.1 | 26.1 | 31.7 | 67.6 | 55 / 62 | **8.9e-4** | **0** | +$437 Jan, +$0.0 Jul |
| prefix | `uc_prefixing=true` (E5; 984 on / 580 off fixed) | 107.6 / 105.7 | 205.9 | 153.0 | 1.4 | 27.3 | 21.8 | 39 / 62 | 9.6e-4 | 0 | +$9,073 Jan, +$1,111 Jul |
| probelift | `mip_lifting_for_probing=0` | 341.0 / 289.3 | 621.9 | 203.2 | 1.5 | 128.0 | 286.2 | 1 / 62 | 36 | 61 | +$25.4 M Jan, +$230 M Jul |
| rulelog | `presolve_rule_logging=true` (+ raw log dump) | 137.6 / 112.6 | 242.0 | 170.9 | 1.7 | 33.4 | 33.2 | 62 / 62 | 0.0 | 0 | 0 |

Reading:

* **Gate: PASS.** On the same window problems the uc-1.1 path and the lean path return the same
  objective to the declared gap on every one of 62 windows (January: 5 windows differ, the
  largest by 8.9e-4 relative, the lean path's incumbent the better one by $437 over the month;
  July: bit-identical objectives). The kept `u` differs in 7 of 62 windows (58 cluster-hours) —
  the within-gap ties the headline describes. `rulelog` (the same path plus logging) reproduces
  base bit for bit, which is the harness's own control: a paired arm with an identical path
  reads 62/62, 0.0.
* **Wall: lean −23 % (January) / −7 % (July)** against the uc-1.1 path in the same container;
  MILP seconds −17 % over the two months. The saving is the tail (67.6 → 32.3 s) and the
  pre-root heuristics (26.1 → 1.6 s); presolve and the root LP are untouched.
* **E5 pre-fixing: within the gap, but one-sided.** 0 windows beyond the gap, yet the objective
  is worse than base in 22 of 62 windows and better in none (+$9,073 over January, +$1,111 over
  July; largest 9.6e-4 relative, just under the bar). Fixing a cluster on or off is a restriction,
  and it bites — the "reachability" rule is conservative to the gap tolerance, not exact. It is a
  wall lever (−16 % against lean here, −33 % against the uc-1.1 path), not an optimum-preserving
  one; the DESIGN's "schedule equality" bar is not met and the default stays `False`. Its arming
  is a declared PRECOMMIT choice for an A/B lane, with this one-sidedness stated.
* **`mip_lifting_for_probing=0` is a HiGHS anomaly, not a lever.** On the same window problems
  HiGHS 1.14.0 returns objectives 8–60 % WORSE than base while reporting a gap of 5.7e-7, i.e. it
  proves optimality of a worse point: the option changes what the presolved model is, not how it
  is searched. Wall 2.5× worse as well. Reported here so no later lane touches it; a HiGHS
  upstream report is the desk's call. (The `presolve_rule_logging` option printed no rule
  statistics in this HiGHS build; the raw log is on the shard branch.)
* The paired harness is the reusable artifact: `rung_l2` with `paired=True` (the default) is how
  any later solver-path change proves it moved wall and not the optimum.

## 4. The L3 wall row (SPP 2020, full year, at `5dc76955`)

Shard `session_017j3ggXTYLqFXGm78xxXM2v`, branch `claude/ucmilp-bench-spp-2020-L3-speed`
`2c95fad3`; `replay_keeper.py results/calibration/closeout_spp_nuc_span --years 2020 --set
unit_commitment_milp=true` at the lean default; 4 cores, `MARKET_SIM_HIGHS_THREADS=1`.

### 4.1 GATESPEC §6.1 row (denominator = the shard's own P0 + P1, the UC-2-SPP PRECOMMIT §5 proxy)

| ISO-year | baseline P0+P1 s | P0 s | UC Σ s (windows, mean, p95 MILP s) | P1 s | total s | **ratio** | integers/window | nodes p50/p95 | gap p95 | time-limit hits | peak RSS GB |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SPP 2020 (lean, `5dc76955`) | 199.4 | 100.6 | 1,144.5 (365, 3.07, 4.28) | 98.8 | 1,415.0 | **7.10** | 3,312 | 1 / 1 | 5.5e-4 | 0 | 5.09 |
| SPP 2020 (uc-1.1 path, `ae224faf`, UC-2-SPP shard) | 198.9 | 97.7 | 1,106.9 (365, 2.97, 4.23) | 101.2 | 1,367.1 | 6.9 | 3,312 | 1 / 1 | 5.7e-4 | 0 | 5.09 |

Phase timing line: `data_prep=16.7s solve_p0=100.6s markup=1164.4s solve_p1=98.8s
results_write=34.5s total=1415.0s (markup: seam=1147.6s …)`. 365 / 365 windows Optimal.

Where the 1,144.5 s go (`summary.phase_sums`): **presolve 803.0 s (70 %)**, root LP 157.3 s
(14 %), post-root tail 137.8 s (12 %; 5,665 separation and 1,231 strong-branching LP
iterations, 0 heuristic), pre-root 8.4 s, HiGHS setup/report 12.6 s, Python side 24.3 s (UC rows
15.5, slicing 4.4, `setSolution` 1.8, LP build 1.4, extract 1.1). Per window: presolve p50 2.20 s
/ p95 2.49 s; root LP p50 0.42 s; tail p50 0.008 s / p95 1.50 s; MILP p50 2.81 s / p95 4.27 s.
Incumbent sources: randomized rounding first in 318 of 365 windows, the node evaluation itself
in 44.

### 4.2 Reading, and the next lever

* **Target ≤ 3× not met; best measured ratio 7.10×.** The year-level number is not better than
  the uc-1.1 path's 6.9× measured in another container, although the paired in-container
  comparison (§3) puts the lean path 17 % faster on MILP seconds over two months. The two
  containers agree on P0 + P1 to 0.3 % but the identical January computation (uc-1.1 path,
  31 windows) took 159.7 s in the profile shard and 173.3 s in the equivalence shard (+8.5 %):
  cross-container noise is of the order of the lean saving, and the saving is on the smallest
  part of the stage.
* **The ceiling is structurally out of reach of any search setting.** Presolve alone (803 s) is
  4.0× the baseline; with the root LP and the tail at zero the stage would still read ≥ 5.1×. To
  reach 3× the stage must cost ≤ 399 s, i.e. ≤ 1.09 s per window, which means presolve must fall
  by ~4×. Nothing in the heuristic, restart, symmetry, thread or horizon space does that (§1.1,
  §3), and presolve off makes the root LP 4.5× dearer (§1.1).
* **Next lever, in-lane (recommended): the slim window.** Presolve removes 35,909 of 57,384
  columns (63 %) and 6,381 of 17,380 rows (37 %) from window 0 in 2.7 s (`rulelog` raw log) —
  the pinned budget units (bounds fixed at their P0 dispatch), zero-availability units,
  zero-CF renewable hours, and the rows those columns empty. Dropping fixed columns BEFORE
  HiGHS, with each fixed column's contribution moved into its rows' bounds, is an exact
  transformation (the same LP, the same optimum) that `model/uc/window.py` can do on the handle
  the production builder returns (`deleteCols` + `changeRowsBounds` + an index map for the
  extract and the warm vector) without touching `model/lp`. What it buys is a measurement for a
  shard, not a prediction: HiGHS would still presolve the remaining 21 k columns.
* **Next lever, owner card: E10 month-parallel** (rule-36 amendment), which multiplies
  throughput without changing the per-window cost. **Not** E2: a 72-hour window costs the same
  wall for half the windows (§1.1).
* **Not a lever:** `mip_lifting_for_probing` (§3), `presolve=off` (§1.1), threads (§1.1).

The L3 bundle (dispatch, sidecars) stayed in the shard container (a bench, never registrable);
only `uc_solve_log_2020.json`, `l3.json`, `wall_table.md` and the logs were pushed.

## 5. What landed (G-DRIFT: every hunk inside the gate-on path; goldens untouched)

* `model/uc/solve.py`: `UC_SOLVER_PRESETS`, `solve_options_from_config`, `apply_solver_options`,
  the HiGHS log callback + `parse_highs_mip_log` (phase profile), harness-only `threads`,
  `extra_highs_options`, `raw_log_dir`. `model/uc/window.py`: `lp_build_s`, `WindowResult.phase`.
  `model/uc/schedule.py`: `record_states` / `prev_states` / `keep_from` (paired runs).
  `pipeline/uc.py`: options from the preset, per-window `phase` + `paired` in `uc_solve_log`,
  `summary.phase_sums`, `run(record_states, pin)`.
* `config/scenarios.py`: `uc_solver_preset: str = "lean"` (validator over
  `UC_SOLVER_PRESET_NAMES`), registered in `_CACHE_KEY_OPTIONAL_FIELDS` at its declared
  `'lean'`, `TIER_TAGS` 1. Born at the fast value and dropped from the hash there, so **every
  committed key is unmoved** (G-KEYS). The one same-key class: a gate-on config at the uc-1.1
  path (only the registered PROBE `2026-10-05-ucmilp-spp-uc-b`, verdict R, a file artifact) and
  a gate-on config at the new default hash alike; shard containers cache nothing, every new
  bundle's `run_config.json` carries the field, and no keeper arms the gate.
* Matrix: the `unit_commitment_milp` row's `def` names the ninth sub-field (no new row: a
  solver path is not a mechanism; `check_mechanism_matrix --base origin/main` ok).
* Bench: `scripts/lib/uc_bench.py` L2 arms (`L2_ARMS`), paired mode (default; `--rolling`),
  per-arm phase sums, `l2_profile.md`; L3 reads P0/P1 seconds from the phase-timing line and
  fills the §6.1 row with the shard's own P0 + P1 as the denominator (the UC-2-SPP proxy).
* Tests (fast tier): both presets return the same toy schedule and objective within the gap;
  the phase profile sums to the solve; the log parser on a fixed transcript; the harness thread
  knob reaches the handle; a paired run advances along the pin and records agreement.
* No engine-version bump: `uc-1.1`'s formulation is unchanged; `uc_solve_log.engine` carries
  `solver_path`.

## 6. Shards (rule 33)

| shard | session | SHA | branch (transport) | state |
|---|---|---|---|---|
| L2 profile, Jan, 10 arms | `session_0151fzU7u47JRsH9vhuh24ir` | `84e928ef` | `claude/ucmilp-bench-spp-2020-L2-speed` `f213b765` | fetched, verified, archived |
| L2 paired equivalence, Jan + Jul | `session_01XQnF2Nmhz65LrZQ91JPgtc` | `5dc76955` | `claude/ucmilp-bench-spp-2020-L2-equiv` `71f3f861` | fetched, verified, archived |
| L3 full year | `session_017j3ggXTYLqFXGm78xxXM2v` | `5dc76955` | `claude/ucmilp-bench-spp-2020-L3-speed` `2c95fad3` | fetched, verified, archived |

Bench branches carry JSON, markdown and logs only (no dispatch bundle, no capture pickle; the
equivalence shard's `replay/` slim P1 sidecars of the capture, ~10 MB, rode along under the
block-D negation — a bench artefact, never registrable); the owner may delete the three
branches once this PR merges (a session cannot, 403). None left alive.

## Log entry

- 2026-10-09 · UC-SPEED `session_01KhMnMmEfydP4sHykH9xrCS` (Fable) · `claude/ucmilp-speed-q8n` · zero LP in the
  parent · three bench shards (L2 profile Jan 10 arms at `84e928ef`; L2 paired equivalence Jan + Jul at
  `5dc76955`; L3 full year at `5dc76955`) · **the window's seconds are HiGHS's: presolve 70 % of the year's
  stage, root LP 14 %, tail 12 %, build 1 %** · E6 not implemented (cannot help), E3 basis unreachable
  (incumbent kept), E5 within gap but one-sided (+$9 k/month, default stays off), E7 −2 % (no knob), E2
  same wall for half the windows · `uc_solver_preset` born at `lean` (presolve on; feasibility jump, LP
  heuristics, root restart off): paired gate PASS (max rel Δobj 8.9e-4, 0/62 beyond gap), −23 % / −7 %
  wall Jan / Jul in-container · **L3 SPP 2020 ratio 7.10× (target ≤ 3× not met; structural: presolve alone
  4.0× the baseline)** · `mip_lifting_for_probing=0` returns worse optima at gap 0 (HiGHS anomaly, do not
  use) · next lever: slim window (drop fixed columns before HiGHS, exact) in-lane; E10 month-parallel owner
  card · PR "uc-milp UC-SPEED: window model reuse (wall)" · no promotion, no registration.
