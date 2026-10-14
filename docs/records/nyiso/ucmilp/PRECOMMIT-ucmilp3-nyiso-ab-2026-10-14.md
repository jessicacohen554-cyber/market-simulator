# PRECOMMIT — UC-3-NYISO: the UC A/B relaunched at the clean engine (uc-1.4), every NYISO backcast year, 2026-10-14

**Written and pushed BEFORE any shard exists.** This is an addendum-by-reference to
`PRECOMMIT-ucmilp-nyiso-ab-2026-10-10.md` (UC-2-NYISO, "the prior PRECOMMIT"): every reading, bar, kill and verdict rule there
(§2 T1–T5, §3 control readings, §4 S1–S5, §5 W1–W4, §6 kills, §7 verdict rule, §9 the 2021 drift rule) is adopted **unchanged**;
this file changes only the pin, the shard set and the readings the charter adds. Lane `UC-3-NYISO` (session
`session_01CQxD6oMjTSxFp8nDQKPKRs`, Opus), branch `claude/ucmilp-3-nyiso-ab` fresh from `580c4fbf`. Chartered by UC-DESK
(`session_01WX9W5tgYMre3Z134LZoGF6`) on the owner's ruling of 2026-10-14 (*"Go with your recommendations"*: decision 7 =
relaunch every UC-2 ISO at uc-1.4; NYISO's prior R is **held, not recorded**).

**Why.** The UC-2-NYISO span (pin `f2bf73bf`, engine uc-1.1+) predates uc-1.3. Engine defect 6 (FINDING-ucmilp-fix4-floor-merit
§0) split each integer cluster's floor pro rata across the plant's offer tranches, forcing `_peak*` tranches on; NYISO's 34
integer clusters are per-plant tranche sets (FINDING §1 table: 4/7/8 members, 7 singletons). Rule 1 [R-STRUCT]: the prior R is
not a structural rejection until the clean engine answers the same question.

## 1. Pin, control, arm

| item | value |
|---|---|
| pin (every shard) | this branch's head at launch (records only on top of `580c4fbf80b8bf970bc19acf14f614728de9d401` = main, uc-1.4); the full 40-char SHA is recorded in §5 and in every prompt. Not chased. |
| control | keeper `2026-10-02-w0-nyiso`, bundle `results/calibration/w0_nyiso_span` (rule 29(b): no control solve), byte-identical at `f2bf73bf` and `580c4fbf` (`git diff --stat` empty over the bundle and `keepers/NYISO.json`) |
| arm | **identical to the prior PRECOMMIT §1**: `replay_keeper.py results/calibration/w0_nyiso_span --years <y>` + `unit_commitment_milp=true` + the nine OFFs (`nyiso_gas_commitment_bridge=false` and its eight `nyiso_gas_bridge_*` legs). Every `uc_*` field at its declared default (`uc_slim_window=true`, `uc_solver_preset="lean"`, gap 1e-3, W/L 24/12, TL 600 s, `uc_prefixing=false`); none swept. Every other floor KEPT (`reliability_floor` ST_GAS, `chp_steam`, nuclear/hydro). |
| years | 2021, 2022, 2023, 2024, 2025 — every year the keeper carries; one shard per year (rules 16, 34, 36) |
| bench gate | none (charter design: straight to the span). A UC hard stop in any leg is kill #1 → that leg stops and reports, routed to UC-DESK with the repro; no `src/` patch in this lane. |

## 2. G-DRIFT `f2bf73bf → 580c4fbf` on the NYISO backcast path (zero LP)

70 commits; 7 non-merge commits touch `src/` or `scripts/`, 15 files. Every hunk classified:

| content | files | NYISO classification |
|---|---|---|
| uc-1.2 (#7230): min-down guard reads the pinned fleet (defect 5); ruling (a) — an all-budget-pinned cluster carries no integer; slim inf-cap NaN; per-window log; infeasible-window plant naming | `model/uc/window.py`, `slim.py`, `solve.py`, `diagnose.py`, `pipeline/uc.py` | **LIVE on the gate-on path only** (the arm); control INERT — `model/uc/*` and `pipeline/uc.py` are reached solely through `pipeline/solve.py`'s `if getattr(config, "unit_commitment_milp", False)` hunk, which is unchanged |
| FIX-3 (#7229): uc-params keyed by EIA plant code via `campd_crosswalk.camd_to_eia_plant` | `model/uc/params.py`, `scripts/lib/uc_params/*`, `data/campd_crosswalk.py` (+ `load_crosswalk(epa, pudl)`; `crosswalk_of_record()` = that function on the same canonical paths, identity), `scripts/lib/clean_profiles.py` (uc-params raw inputs) | **LIVE on the gate-on path only** (no-load / UT / DT params the UC reads); `crosswalk_of_record` identity-refactored; `camd_to_eia_plant` has one caller (`uc_params`). Control INERT |
| uc-1.3 (#7237): merit-order floor fill (defect 6), `uplift_from_bundle` deleted, pass-2 reuse by input digest | `pipeline/uc.py`, `model/uc/uplift.py`, `schedule.py`, `_ucmilp_compose_span.py` (uplift no longer recomputed), `uc_bench.py`, `bench_uc_ladder.py` | **LIVE on the gate-on path only** — the fix this relaunch exists for |
| uc-1.4 (#7238): P1 floor = the window's row (b) `mlf·p̄·a·u` | `pipeline/uc.py` | **LIVE on the gate-on path only** |
| `scenarios.py`, `constants.py`, `runner.py`, `pipeline/solve.py`, `run_calibration*.py`, `replay_keeper.py`, `shard_prompt.py`, `calibration_verdict.py`, `legitimacy_diagnostics.py` | unchanged | — |
| solve surface | `solve_surface_register.py --diff f2bf73bf 580c4fbf`: *"342 → 342 names; 0 value(s) moved, 0 added, 0 removed — NO VALUE MOVED"* | no ISO's key reached |

Nothing is LIVE for NYISO outside the UC stage. The prior PRECOMMIT's §10 G-DRIFT (basis `306f2c00` → `f2bf73bf`) stands,
extended by this table: the arm-vs-control delta is UC-only for 2022–2025 and UC + the §9 `59490433` drift for 2021 (same
envelope: |ΔC3a| ≤ 1.1 pt, |ΔC1| ≤ 0.10 TWh per class not attributable).

## 3. Readings — the prior PRECOMMIT's, unchanged, plus the charter's report rows

Gating (unchanged): **T1** no PASS → FAIL flip (any year, criterion, class row; C3c/C6 attestation artefacts named, not counted);
**T2** 2024 C3a ∈ [−1.8 %, +0.2 %]; **T3** C1 CC_REGULAR PASS 2021–2024; every leg P1 Optimal; unserved ≤ +500 MWh vs control;
no new D-4 FAIL row (a per-unit conduct rider is named with its GWh). Reported (unchanged): T4 (M3 ≤ $15-hour ratios, lower-tercile
error), T5 (`reliability_floor` ST_GAS TWh/share; C8 with and without MECH 28), S1–S5, W1–W4.

Added by the charter (reported, not gating):

| # | reading | instrument | expectation (declared, not a bar) |
|---|---|---|---|
| U1 | forced peak-tranche TWh: energy of `_peak*` / `peak` tranche rows of integer clusters in hours their cluster's MECH 28 floor binds | arm `unit_marginal_<y>` + `uc_schedule_<y>` (zero LP) | ~0 at uc-1.4 (ERCOT 2019 repro: 5.81 → 0.00 TWh) |
| U2 | per-year control → arm C1, C3a, C3b, C3c, C4, C8 (± MECH 28), unserved MWh, uplift %, CC / ST_GAS starts vs CEMS (NYISO has no coal row — reported "n/a"), wall ÷ (P0+P1), integer clusters / gate set, TL hits | prior §5–§8 procedure | — |
| U3 | uc-1.4 vs uc-1.1 (prior span) per year: same rows — what defect 6 was worth on NYISO | the prior slim span `docs/records/nyiso/ucmilp/data/ucmilp_nyiso_span/` | — |
| U4 | any price move diagnosed by sign and hour class: Δ load-weighted price by price tercile / peak vs off-peak, and which classes are marginal in the moved hours (`unit_marginal.marginal`) | committed sidecars, zero LP | — |

## 4. Kills and verdict (unchanged from the prior §6–§7)

Kill #1 infeasible window / no incumbent (engine defect → that leg stops, routed to UC-DESK; no patch here). Kill #2 schedule
non-determinism (exercised only if a relaunched leg and its predecessor both complete). Kill #3 a control flip (§3 of the prior
PRECOMMIT; on this control ISO it is the verdict `R` with the flipped rows named). Verdict: **K candidate** iff T1, T2, T3 met, no
kill, every leg Optimal, W2–W4 within bars (W3 alone breached → "hold: uplift share"); **R** on any kill or T2/T3 breach; **I** iff
T1–T3 met and every scored row moves less than scorer precision; mixed → the worst reading decides, row by row. 2021 flips inside
the §9 envelope are "not attributable".

## 5. Solve plan

- Five shards from `scripts/shard_prompt.py --iso NYISO --all-years --sha <branch head> --lane ucmilp3-nyiso --bundle
  results/calibration/w0_nyiso_span` + the ten `--set`s `--budget 360 --note "ucmilp3-nyiso: UC A/B at uc-1.4"`, lane addendum
  appended; committed as `shard-prompts-ucmilp3-nyiso.txt`. Branches `claude/ucmilp3-nyiso-<y>`, out-dirs
  `results/calibration/ucmilp3_nyiso_<y>`. Budget 360 min/shard (prior legs 25–107 min whole-shard at uc-1.1; ERCOT walls fell
  at uc-1.3/1.4; ≤ the charter's 720). Any file > 100 MB is split (`split -b 90m`) with its sha256 recorded before commit.
- Parent (zero LP): fetch, `git ls-tree` non-empty, check out, bytes in hand, then archive (rule 33). Compose with
  `_ucmilp_compose_span.py` (scratch copy if it still lacks `gas_price_override` in `PER_YEAR_FIELDS` — disclosed as in the prior
  RESULT §5), respan the benchmark frames, score control and arm on the same bench parts with a local, discarded registration
  (E13: nothing registered), regenerate `legitimacy_diagnostics.json`.
- Deliver: RESULT + slim span `docs/records/nyiso/ucmilp/data/ucmilp3_nyiso_span/`, matrix cell `unit_commitment_milp` (NYISO
  shard), one PR (not merged; UC-DESK merges), `send_message` to UC-DESK.

## 6. DO NOT REDO

Prior PRECOMMIT §11 verbatim: no `uc_*` value other than the defaults, no second arm (floors-off is a separate owner call), no
control solve, no 2021 control re-solve, no registration, no promotion, no tuning of anything (rule 1).
