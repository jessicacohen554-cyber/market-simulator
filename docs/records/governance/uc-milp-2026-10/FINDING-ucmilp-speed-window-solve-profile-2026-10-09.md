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
Result: §3 (TBD-EQ). L3 wall row at the final SHA: §4 (TBD-L3).

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

TBD-EQ

## 4. The L3 wall row (SPP 2020, full year, at `5dc76955`)

TBD-L3

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
| L2 paired equivalence, Jan + Jul | `session_01XQnF2Nmhz65LrZQ91JPgtc` | `5dc76955` | `claude/ucmilp-bench-spp-2020-L2-equiv` | TBD-EQ |
| L3 full year | `session_017j3ggXTYLqFXGm78xxXM2v` | `5dc76955` | `claude/ucmilp-bench-spp-2020-L3-speed` | TBD-L3 |

Bench branches carry JSON, markdown and logs only (no dispatch bundle, no capture pickle);
the owner may delete them once this PR merges (a session cannot, 403).

## Log entry

TBD-LOG
