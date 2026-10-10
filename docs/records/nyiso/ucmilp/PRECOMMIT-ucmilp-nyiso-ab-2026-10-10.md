# PRECOMMIT — UC-2-NYISO: pre-registered A/B of the MILP unit-commitment stage on every NYISO backcast year (a CALIBRATED CONTROL), 2026-10-10

**Written and pushed BEFORE any span shard exists.** Every reading, bar, kill and budget below is fixed here and fails
closed; nothing moves after a number comes in (GATESPEC §7.1, rule 1(c) by analogy). Lane `UC-2-NYISO`
(session `session_01HoVUBRJhqpY4TQdLq6NkPR`, Fable), branch `claude/ucmilp-2-nyiso-ab-y5h8` off `origin/main`
`2f872a62`. Chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`, 2026-10-10) under the owner's direction
*"launch shards for other ISOs to test"*. Protocol: `GATESPEC-uc-milp-testing-protocol-2026-10-03.md` §5–§7; plan
`docs/uc-milp-program-plan-2026-10.md` §3 (UC-2), §8.1 (R3–R6, the NYISO golden ruling). Structure copied from the
SPP precedent `docs/records/spp/ucmilp/PRECOMMIT-ucmilp-spp-ab-2026-10-04.md` (+ Addenda A–D) and its RESULT.

NYISO is a **control ISO** (GATESPEC §1: *"NEISO 2023 and NYISO 2024 are always controls"*): the question this A/B answers
is not "does the UC fix a failing gate" (none fails) but "does replacing the P0-detected gas commitment bridge by the
integer commitment stage leave a CALIBRATED ISO calibrated". The readings below are written for that question.

## 0. Preconditions (checked before this file was written; zero LP in this session)

| check | result |
|---|---|
| `git rev-parse origin/main` at charter = the pin | **`2f872a62a7cccadb6800555c11a73745dcdb89a4`** (merge of PR #7218, UC-SPEED; engine uc-1.1 + UC-1-FIX + `uc_solver_preset="lean"`); HEAD of this lane's branch is the pin + records only |
| `grep -c unit_commitment_milp src/market_sim/config/scenarios.py` at the pin ≥ 1 | yes (field, validator, `UC_REFUSED_ALWAYS`, cache-key registration) |
| the NYISO keeper's `run_config.json` arms a field in `UC_REFUSED_ALWAYS` | **yes — `nyiso_gas_commitment_bridge = True`**, the only one of the 15; `ScenarioConfig.with_overrides(unit_commitment_milp=True)` on the keeper's 2024 recipe is REFUSED by the validator (*"disarm: nyiso_gas_commitment_bridge"*), and is ACCEPTED with the §1 substitution set (checked zero-LP on the pin's tree) |
| the keeper bundle is byte-identical at the pin and on `origin/main` | yes (the pin IS `origin/main`) |
| NYISO golden (UC-1, gate off, `ec758d64`) | **engine-inert**; 2022–2025 bit-identical; 2021 differs by pre-existing main drift pinned to `59490433` (FINDING-ucmilp-golden-nyiso-main-drift-2026-10-04.md; desk ruling (A) in plan §8.1) — see §9 |
| D-2 (3× ceiling, "fund speedup"), D-3 (zero markup + uplift sidecar), D-4 (MECH 28 reported, not budgeted) | ruled (plan §8.1 R3–R4; D-2 2026-10-09) — ratios are REPORTED here, not judged |
| D-5 for NYISO | desk-set under the owner's direction (owner may override): the arm = keeper recipe + `unit_commitment_milp=true` + OFF for every `UC_REFUSED_ALWAYS` field the keeper arms **and its `nyiso_gas_bridge_*` legs**; every other floor KEPT (mirrors SPP arm 1 so results compare across ISOs) |
| **L1 GATE (charter task 0; new, from SPP's two engine defects)** | one bench shard at the pin, NYISO 2024, rung L1 + one rolled month (January), model `claude-opus-5-5`, budget 60 min: `session_01PbNTnQLYPvowX7bqgSH11a`, launched 2026-10-10 00:48Z, prompt committed as `shard-prompts-ucmilp-nyiso-bench.txt`. Pass line: window 0 Optimal AND 31/31 January windows Optimal (no `UcWindowInfeasible`, 0 time-limit hits, gap_max ≤ `uc_mip_rel_gap`). **Result: see §0.1** — the span shards launch only on a pass |
| clean data for the zero-LP compose / score steps | this container is a full clone (`data/raw` 7.0 GB present, `hydrate_data.py` a no-op); `regenerate_clean.py --solve-profile NYISO` run once (8 datatypes) for the benchmark-frame respan of §8 — no LP |

### 0.1 L1 gate result (filled from the bench shard's report before the span shards were launched)

_Pending at the time of writing; filled in Addendum A before any span shard is created. If the gate fails, no span shard
is launched and the RESULT records the engine defect (GATESPEC §5 engine-defect route; routed to UC-DESK)._

## 1. Control, pin, arm

- **Control (rule 29(b), no control solve):** NYISO's designated keeper `2026-10-02-w0-nyiso`, bundle
  `results/calibration/w0_nyiso_span`, five year-isolated legs 2021–2025 solved at
  `306f2c00b6268b791fb77c392c8d69a756959e76` (closeout-B W0 phase 3), solve-surface fingerprint `cb770a26d18f570f`.
  Its committed `metrics.json`, `legitimacy_diagnostics.json`, `hourly/*`, `calibration_attestation.json` and the status
  part `frontend/data/backcast/status/NYISO.js` (rubric 3.20, generated 2026-10-03) are the control readings.
  Determination: **CALIBRATED** (lone ledgered C3c caveat, rule 22). Note: `calibration_verdict.py` at the pin prints a
  *STALE BENCHMARK* alarm for the NYISO bench parts 2021–2025 (they do not reproduce under the builder at HEAD); see §8
  for how control and arm are scored on the same parts.
- **Pin (every shard):** `2f872a62a7cccadb6800555c11a73745dcdb89a4` = `origin/main`. `source_revision` is this full SHA,
  never a branch. The pin is not chased: a later main is a new Addendum, never a silent move.
- **Arm — ONE logical delta ("bridge family out, integer commitment in"):**
  `replay_keeper.py results/calibration/w0_nyiso_span --years <y> --set unit_commitment_milp=true` plus the nine OFFs below.
  Every `uc_*` field stays at its declared default and is **never swept**:

  | field | control (keeper `run_config_<y>.json`) | arm | source |
  |---|---|---|---|
  | `unit_commitment_milp` | False | **true** | the arm |
  | `nyiso_gas_commitment_bridge` | **True** | **false** | D-5 NYISO; `UC_REFUSED_ALWAYS` (validator) |
  | `nyiso_gas_bridge_da_horizon` | True | false | D-5 NYISO (leg) |
  | `nyiso_gas_bridge_min_run` | True | false | D-5 NYISO (leg) |
  | `nyiso_gas_bridge_online_hours` | True | false | D-5 NYISO (leg) |
  | `nyiso_gas_bridge_plant_exclusions` | True | false | D-5 NYISO (leg) |
  | `nyiso_gas_bridge_reserve_duty_exclusions` | True | false | D-5 NYISO (leg) |
  | `nyiso_gas_bridge_startup` | True | false | D-5 NYISO (leg) |
  | `nyiso_gas_bridge_startup_aware` | True | false | D-5 NYISO (leg) |
  | `nyiso_gas_bridge_state_floor_min_run` | True | false | D-5 NYISO (leg) |
  | `nyiso_gas_bridge_ct`, `nyiso_gas_bridge_plant_min_run` | False | False (unchanged) | not armed by the keeper |
  | `nyiso_gas_bridge_cc_min_load_frac` 0.523 / `_st_min_load_frac` 0.239 / `_cc_min_run_hours` 21 / `_st_min_run_hours` 13 / `_ct_*` | recorded values | unchanged | measured parameters of the (now unreached) detector, not arms; `uc-params` carries the UC's own measured physics |
  | `uc_window_hours` / `uc_lookahead_hours` | — | 24 / 12 | DESIGN §3 (E2) |
  | `uc_mip_rel_gap` | — | 1e-3 | DESIGN §3 (E4) |
  | `uc_window_time_limit_s` | — | 600 | DESIGN §3 declared placeholder |
  | `uc_integer_scope` / `uc_noload_source` / `uc_boundary_mode` | — | `physics` / `campd_regression` / `p0_targets` | DESIGN §1.1, §1.2, §2.2 |
  | `uc_prefixing` | — | false | DESIGN §2.3; UC-SPEED §3: one-sided, default stays off |
  | `uc_solver_preset` | — | `lean` | UC-SPEED (registry default at the pin; paired-equivalence PASS on 62/62 windows) |

  The eight boolean legs are read ONLY inside `pipeline/commitment.py::_nyiso_gas_bridge_floor`, whose single caller is
  gated `if not (config.nyiso_gas_commitment_bridge and iso == "NYISO"): return None` (`pipeline/commitment.py:1211`), so
  with the master off they are code-inert: switching them off changes no byte of the solve and makes the recorded recipe
  read "bridge family off" (the desk's D-5 wording). The delta is one logical delta either way; the nine `--set`s are
  listed so the cell's evidence and the shard prompts say exactly what the arm is.
- **Kept floors (D-5 "every other floor KEPT") — named now as the stacking risk SPP showed.** The keeper's D-2 rows:
  `reliability_floor` on **ST_GAS** (1.66 / 1.29 / 1.26 / 1.52 / 1.43 TWh = **21.9 / 14.4 / 10.9 / 13.3 / 11.5 %** of class
  energy, 2021–2025; `reliability_floor_layup_window_mask` on; per-zone `reliability_floor_overrides` as recorded),
  `chp_steam` (CC_CHP 0.05–0.84 TWh, CT_CHP ≤ 0.05; D-2 exempt), `nuclear_mustrun`, `hydro_min_flow`, `hydro_ror_flat`;
  `coal_mustrun_per_plant` is armed but NYISO has no coal row. **The risk:** in SPP the kept `st_gas_mustrun_per_plant`
  floor's own forced energy ROSE 1–1.2 TWh/yr under the UC (CC decommitted → the floored class fills) and pushed C8 ST_GAS
  over the 30 % cap in four years; here the analogue is `reliability_floor` ST_GAS (2021 sits at 22.1 % registered, 7.9 pp
  under the cap) and the displaced energy's destination is ST_GAS / CT_PEAKER / imports rather than coal. This is a
  pre-declared reading (§2 T5, §3), not a reason to switch the floor off: that is the owner's D-5 call, and the SPP D-6
  ruling ("Record R + test floors-off arm") already names a floors-off arm as a SEPARATE test.
- **Pricing (owner ruling R3, D-3):** markup zeroed on integer clusters; start and no-load paid once in the UC objective;
  make-whole reported in `hourly/uc_uplift_<y>.parquet`, never in the LMP (rule 4 untouched).
- **Rule 20 (owner ruling R4, D-4):** UC min-load energy REPORTED under MECH 28, not budgeted. The scorer at this pin still
  budgets `uc_schedule` energy inside the C8 share (SPP RESULT §1 note); C8 is therefore read twice — as the scorer prints it
  and with MECH 28 removed from the D-2 sum — and a flip that survives the removal is a real flip.
- **Not a matrix re-test (rule 28).** NYISO cells: `gas_commitment_bridge` **K** (ledgered 2026-10-02: the bridge's D-4
  conduct rows are a *P0-anchored-detection seam limitation*; *"Re-open only with an admissible P1-native commitment
  detector"*), `nyiso_incity_commitment_obligation` **R**, `online_capacity_envelope` **·** (never minted for NYISO),
  `reliability_floor` **K**. None is re-tested: the integer commitment state is a different object from a P0-detected
  bridge (plan §6, GATESPEC §5 "integer state is the new evidence") — and it is exactly the P1-native commitment object the
  K cell's re-open clause names, so this A/B is the licensed test of that clause, not a re-litigation. The cell this lane
  feeds is `unit_commitment_milp` (minted **U** for NYISO by UC-1), stamped from the RESULT as this lane's last commit.
  DO-NOT-REDO honoured (matrix §5.5): no measured offer surface, no CC winter capability, no temperature derate, no
  `nyiso_fg_split`, no in-city commitment obligation, no firm imports, no measured interface limits, no startup-cost or
  per-plant min-run retune, no offer-band move, no second arm.
- **DOF (rule 21):** zero free parameters added. Every UC parameter is measured or published (UC-0 FINDING §5): no-load =
  CAMPD per-unit intercept × delivered fuel (`uc-params`, class-mean-per-MW fallback share reported from
  `uc_solve_log_<y>.json clusters[].src`; UC-0 census: 4 of 21 CC plants on the fallback), UT/DT from the NYISO bridge's
  measured values (CC 21 / 6 h, ST_GAS 13 / 8 h), min-load 0.523 / 0.239 (CAMPD 2023–2025). The keeper's offer bands ride
  unchanged (rule 1(c)).

## 2. Target readings (fixed ex ante; a control ISO's targets are "stays calibrated")

Control values are the keeper's registered records (status part, rubric 3.20; identical to `calibration_verdict.py` on the
committed bundle at the pin). "met" is decided on the composed arm span's `calibration_verdict.py` output and the zero-LP
re-measurement of UC-0's M1/M3/M4 on the arm bundle (`scripts/probes/_ucmilp_benefit_screen.py::screen_year`, imported,
pointed at `results/calibration/ucmilp_nyiso_span` — the board's conventions).

| # | reading | control | bar (met iff) |
|---|---|---|---|
| **T1** | **no PASS → FAIL flip on any registered year, any criterion, any class row** (C1 per class, C2, C3a, C3b, C3c, C4, C6, C8) | CALIBRATED; every scored row PASS except C3c CAVEAT 2022–2025 (ledgered) | zero flips; a C3c CAVEAT → FAIL that is only the probe's missing attestation (C6 UNATTESTED) is an artefact, named as such (SPP Addendum D §3); C3c magnitudes compared directly |
| **T2** | **\|ΔC3a\| ≤ 1 pp on 2024** (the GATESPEC control bar) | 2024 C3a **−0.8 %** (model 39.27 vs 39.57 $/MWh) | arm 2024 C3a ∈ **[−1.8 %, +0.2 %]** |
| **T3** | **replacing the bridge must not move CC energy outside the C1 band** — C1 `CC_REGULAR` PASS in every scored year (2025 is SKIPPED by the scorer: preliminary EIA-923; its Δ TWh is reported) | +1.31 / +1.24 / +0.61 / +2.02 TWh (2021–2024), band ±3.76–3.98 TWh & ±3 pp share | PASS in 2021–2024; the Δ TWh vs control reported for all five years |
| T4 (reported) | M3 low-price-hour ratios (model/actual hours ≤ $15 and < $0) and lower-tercile mean error | ratio 0.00 / 0.00 in every year (actual ≤ $15 hours 689 / 50 / 450 / 171 / 136); lower-tercile error +$12.0 / +23.0 / +9.5 / +6.7 / +8.9 per MWh | sign: ratios rise, lower error falls — reported, not gating (the body-down effect that is the risk to T2 and §3) |
| T5 (reported) | the kept `reliability_floor` ST_GAS forced TWh and share, with and without MECH 28 in the D-2 sum | 1.66 / 1.29 / 1.26 / 1.52 / 1.43 TWh; 22.1 / 14.9 / 11.3 / 13.6 / 11.8 % (C8 as registered) | reported; C8 PASS/FAIL under both readings (R4) |

**Declared expectation, not a kill:** the SPP arm lowered the price body $0.4–2.9/MWh in every year. On NYISO's control the
same move lands on T2 (2024 −0.8 % has 1 pp of declared room either side) and on the §3 rows with the least headroom. A
body-down move that crosses them is the finding this A/B exists to measure on a calibrated ISO; it is recorded as such.

## 3. Control readings (fixed; a breach is a kill, §6)

**No PASS → FAIL flip on any registered NYISO year, any criterion, any class row** (`calibration_verdict.py` per-(criterion,
key, year) status diff vs the keeper, scored on the same bench parts — §8). The rows with the least headroom, named now so
the reading cannot be re-interpreted later:

| year | criterion | control | headroom | why it is tight |
|---|---|---|---|---|
| **2025** | **C3a** | **−7.7 % PASS** (63.89 vs 69.23) | **2.3 pts** | model-LOW already; a trough fix moves it toward the −10 % edge — the most likely flip |
| 2021 | C3a | +4.3 % PASS | 5.7 pts | body down helps |
| 2022 | C3a | −0.7 % PASS | 9.3 pts | 2022's lower-tercile excess is the largest (+$23/MWh): the biggest body move is expected here |
| 2023 | C3a | +2.0 % PASS | 8.0 pts | body down helps |
| 2024 | C3a | −0.8 % PASS | 9.2 pts to the band; **1.0 pt under T2** | the GATESPEC control bar |
| 2021–2025 | C3b | 0.117 / 0.149 / 0.129 / 0.118 / 0.148 PASS | 0.051–0.083 | shape may re-order (SPP: up in 4 of 7 years) |
| 2024 | C1 CC_REGULAR | +2.02 TWh (+2.2 pp) PASS | 1.96 TWh / 0.8 pp | the ISO's largest CC excess; the UC decommits CC in troughs (SPP: −5 to −8 TWh/yr) — here it may move the row TOWARD the band or past it in the other direction |
| 2023 | C1 CC_CHP | +2.81 TWh (+2.4 pp) PASS | 1.01 TWh / 0.6 pp | CHP is outside the integer set, but its energy is the residual of what the UC decommits |
| 2021 | C8 ST_GAS | 22.1 % PASS | 7.9 pp | the kept `reliability_floor` + UC stacking (§1); SPP's kept ST_GAS floor rose 8–14 pp |
| 2022–2025 | C3c | CAVEAT (ledgered, rule 22) | — | CAVEAT → FAIL is a flip only if the magnitude moves outside the band on the attested basis; the probe's UNATTESTED artefact is named, not counted |
| 2021 | every criterion | as registered | — | compared against the COMMITTED bundle with the §9 drift caveat; deltas classified per §9 |

Also gating: every leg's P1 `Optimal`; unserved energy up by ≤ 500 MWh in any year vs the keeper (control: 0 in every year);
no new D-4 FAIL row (control: 137 D-4 rows, 0 FAIL; the bridge's own ledgered conduct rows disappear with the bridge).

## 4. Structure readings (reported; the D-6 card reads them)

| # | reading | control | arm instrument |
|---|---|---|---|
| S1 | MECH 28 share of class energy per year (CC_REGULAR, ST_GAS) and ISO-wide; the bridge's D-2 rows (CC 0.19–0.32 TWh = 0.3–1.0 %, ST_GAS 0.01–0.04 TWh) vanish with the bridge | bridge rows as listed; MECH 28 = 0 | regenerated `legitimacy_diagnostics.json` D-2 rows, id 28 |
| S2 | starts per plant-year vs CEMS (UC-0 M1; on = 1 % of available cap) | CC_REGULAR 1,258 / 780 / 1,605 / 1,336 / 1,165 vs CEMS 797 / 727 / 740 / 649 / 804 (1.1–2.2×); ST_GAS 761 / 793 / 989 / 1,163 / 1,092 vs 181 / 199 / 186 / 162 / 210 (4–7×) | `screen_year` M1 on the arm; `uc_schedule_<y>.parquet` Σ`v` per cluster as the engine's own count. Expected: both classes toward CEMS (SPP: overshoot to 0.5–0.8× for CC) |
| S3 | online capacity vs a measured online series | NYISO has **no measured hourly online-capacity series on disk** (the ISO comparators GATESPEC §5 names are SPP / MISO / ERCOT) | SKIPPED and named; the arm's `online_mw` from `uc_schedule_<y>.parquet` is reported against the keeper's available MW (model-internal) |
| S4 | integer set and fallback shares | UC-0 M6: 32 NYISO plant clusters (21 CC 6.8 GW + 11 ST_GAS 7.7 GW = 14.5 GW); no-load fallback 4 CC plants | `uc_solve_log_<y>.json engine.*`, `clusters[].src` |
| S5 | M4 reserve dormancy (share of hours with model reserve MCP < $1 vs actual; mean MCP) | model 1.00 / 0.999 / 0.999 / 1.00 / 0.996 vs actual 0.85 / 0.79 / 0.83 / 0.83 / 0.68; mean MCP $0.0–0.2 vs $2.0–7.2 | `screen_year` M4 on the arm; direction reported (SPP: no move) |

## 5. Cost readings (reported; D-2 is ruled at 3× — the ratio is REPORTED, never judged here, plan §8.1)

| # | reading | bar |
|---|---|---|
| W1 | the GATESPEC §6.1 wall row per year: baseline P0+P1 s, P0 s, UC Σ s (windows, mean, p95 MILP s), P1 s, total s, ratio, integers/window, nodes p50/p95, gap p95, time-limit hits, peak RSS GB | reported for all five years |
| W1-denominator | the SPP proxy: baseline P0+P1 = the same shard's own `solve_p0 + solve_p1` from the `log_year_phase_timing` line, so ratio = total / (P0 + P1) in one container. The on-record NYISO LP walls (`wallclock-baseline-2026-07.md`, 2023/24/25 paired rows: P0 180 / 150 / 98 s, P1 171 / 173 / 100 s) are quoted beside it | stated as a proxy in every row |
| W2 | time-limit hits (`summary.time_limit_hits`) | ≤ 1 % of windows = **≤ 3 of 365** per year |
| W3 | uplift share = Σ `uplift_usd` ÷ Σ_t λ_P1 × load (from `hourly/system_<y>.parquet`) | ≤ **2 %** (sanity) |
| W4 | infeasible windows (`windows[].status`) | **0** (otherwise §6 kill) |

**Shard budget:** the charter rule is ceil(1.3 × the L1-month extrapolation), where the extrapolation = the bench's capture
wall (data prep + P0 + P1 + write) + 12 × the January L2 month wall + the stage's fixed overhead; **if the bench cannot
supply it, 90 min.** The number is fixed in Addendum A from the bench report before the span shards are generated. One shard
commit ≤ 20 min of runtime (rule 32); a shard approaching the budget with no artifact stops and reports.

## 6. Kills (GATESPEC §5) — any one ⇒ record it in the RESULT and STOP; no re-tune, no second arm

1. **An infeasible window** in any year (`windows[].status` infeasible, or the engine's hard stop "no incumbent"): an engine
   defect, routed to UC-DESK, never a tuning invitation.
2. **A non-deterministic schedule:** the schedule hash of `uc_schedule_<y>.parquet` differs between two completed runs of
   the same recipe-year. Exercised only if a relaunched shard (PENDING > 45 min rule) and its predecessor both complete;
   otherwise recorded "not exercised".
3. **A control flip** (§3) in any registered year — on a control ISO this is also the headline reading, so a kill here is
   recorded as the verdict `R` with the flipped rows named, not as a failed experiment.

## 7. Verdict rule (fixed) and the D-6 card

- **K candidate** — T1, T2, T3 met, no kill, every leg Optimal, W2–W4 within bars: recommend the owner's D-6 card read
  "promote on structure" (the lane never promotes; UC-4 is the desk's slot). If T1–T3 are met but W3 is breached, the card
  says so and the recommendation is "hold: uplift share".
- **R** — any kill (T1 is the kill), or T2 breached, or T3 breached.
- **I** — T1–T3 met and every scored row moves by less than its scorer precision (|ΔC3a| < 0.1 pt, |ΔC3b| < 0.001,
  |ΔC1| < 0.01 TWh in every year): "the relaxation was already tight here" (GATESPEC §7.2).
- Mixed: the worst reading decides, stated row by row. The determination (`iso_determination` CALIBRATED → ?) is reported
  beside it. 2021 is reported with the §9 caveat and its deltas classified; a 2021-only flip whose magnitude lies inside
  the §9 drift envelope is reported as "not attributable" and does NOT by itself make the verdict R (it is routed to the
  owner as part of the open 2021 re-solve question); a 2021 flip outside the envelope is a flip.
- The RESULT carries the D-6 card text verbatim-ready: promote on structure · record R/I with evidence · hold.

## 8. Solve plan (rules 16, 32–36) and the zero-LP scoring procedure

- **Five shards, 2021–2025**, one year each, `claude/ucmilp-nyiso-<y>`, out-dir `results/calibration/ucmilp_nyiso_<y>`,
  prompts from `scripts/shard_prompt.py --iso NYISO --all-years --sha 2f872a62a7cccadb6800555c11a73745dcdb89a4
  --lane ucmilp-nyiso --bundle results/calibration/w0_nyiso_span --set unit_commitment_milp=true` + the nine §1 OFFs
  `--budget <Addendum A> --note "ucmilp-nyiso: UC A/B"`, each appended with the SPP addendum (confirm
  `hourly/uc_schedule_<y>.parquet`, `hourly/uc_uplift_<y>.parquet`, `uc_solve_log_<y>.json`, `hourly/unit_marginal_<y>.parquet`
  in the pushed tree; report the §6.1 wall row verbatim; an infeasible window is a successful report, push nothing).
  Committed as `shard-prompts-ucmilp-nyiso.txt`. `create_session` per year: `source_revision` = the pin, model
  `claude-opus-5-5`, tag `ucmilp:UC-2-NYISO-shard`. PENDING > 45 min: archive and relaunch (kill #2 then becomes exercisable).
- **On each report:** fetch; `git ls-tree -r <sha> -- results/calibration/ucmilp_nyiso_<y>` non-empty; check out; verify
  `dispatch/<y>_P1.parquet` + the three UC files + `unit_marginal_<y>.parquet` (bytes in hand); THEN `archive_session` (rule 33).
- **Compose, zero LP, at the pin** with the two SPP Addendum-D workarounds, DISCLOSED: (1) `_ucmilp_compose_span.py`'s
  `PER_YEAR_FIELDS` lacks `gas_price_override`, which this keeper records per year (3.72 / 6.45 / 2.54 / 2.19 / 3.52) — the
  keeper's own composer `_w0_compose_span.py` declares `YEAR_INDEXED = {"weather_year", "gas_price_override"}`; the lane
  runs a SCRATCH copy of the UC composer with that one set extended (no repo script edited); (2) `results/calibration/_shared/
  NYISO/` does not exist on `main`, so the span's benchmark frames are rebuilt over the composite's own recipe with the W0
  composer's `_respan_shared_inputs` (content-addressed; the SPP case resolved to the keeper's own hashes) — this is the
  one data step the parent runs, zero LP. `legitimacy_diagnostics.json` is REGENERATED over the composite, never copied.
- **Score without registering (desk ruling on the SPP probe: E13 admits keepers and folded runs only).** The scorer reads a
  registry sidecar + run payload + bench parts, so `dashboard_add_run.py --no-prune` is run LOCALLY to produce them, the
  verdict is taken, and every file it wrote under `frontend/data/` is discarded before commit (`git checkout -- frontend/data`
  + removal of the new sidecar / payload); nothing is registered on `main`. Because registration rewrites the NYISO bench
  parts for 2021–2025 with the builder at HEAD (the STALE BENCHMARK alarm says the committed parts no longer reproduce),
  **control and arm are scored on the SAME refreshed parts**: the control is re-scored by `calibration_verdict.py` on its
  committed bundle with the refreshed parts in place, and flips are judged control-refreshed → arm. The
  control-registered → control-refreshed delta is reported separately and attributed to the part, never to the arm. The
  refreshed parts are discarded too (they are a keeper-promotion artefact).
- **What lands in the PR:** the PRECOMMIT (+ addenda), the RESULT, the shard prompts, the slim span under
  `docs/records/nyiso/ucmilp/data/ucmilp_nyiso_span/` (SPP precedent: `hourly/*` sidecars incl. `uc_schedule_<y>`,
  `uc_uplift_<y>`, `unit_marginal_<y>`; `uc_solve_log_<y>.json`; `meta.json`, `metrics.json`, `run_config*.json`;
  regenerated `legitimacy_diagnostics.json` — no `dispatch/`), the control and arm verdict JSONs, and the matrix cell.
  Full leg bundles stay on their shard branches (rule 31: nothing deleted; a session cannot delete a branch). ONE PR;
  UC-DESK merges.
- **Exit:** RESULT beside this file (`RESULT-ucmilp-nyiso-ab-<date>.md`: §6.3 gate table first, control → arm, every year,
  wall rows, every reading answered, kills checked, verdict, D-6 card, where each bundle is and what a promotion costs,
  `## Log entry`); `send_message` UC-DESK with the gate table first, then the wall rows.

## 9. The 2021 caveat (KNOWN: the keeper's 2021 leg does not reproduce at HEAD) and the classification rule

FINDING-ucmilp-golden-nyiso-main-drift-2026-10-04.md: at any SHA ≥ `59490433` (2026-10-02 08:45 UTC, 24 min after the
keeper's basis) the keeper recipe's 2021 leg differs from the committed bundle because `fleet_zone_vintage_coords=True`
admits eGRID-absent wind/solar to the renewable zone lookup → zonal `solar_cf` moves (5 of 7 zones, 5,088 daylight hours,
max |Δ| 0.0017) → P0 run lengths of ONE unit (`CT_CHP_NYC_p2493_committed`) → its May–June monthly markup −0.077 $/MWh →
P1. Measured consequence (golden): `system_2021.price` max |Δ| 2.72 $/MWh over 10,544 zone-hours; `class_*_2021.mw`
max |Δ| 70 MW; 2022–2025 bit-identical. The pin carries `59490433`, so the arm's 2021 leg carries this drift AND the UC.

**Rule (fixed now):** 2021 is reported arm vs the COMMITTED control bundle with this caveat. Every 2021 delta is classified:

| quantity | drift envelope (loose upper bound from the golden's maxima) | classification |
|---|---|---|
| C3a 2021 (annual mean over 7 zones × 8760 h, control mean 43.95 $/MWh) | 10,544 × 2.72 / (61,320 × 43.95) = **≤ 1.1 pt** | \|ΔC3a\| ≤ 1.1 pt: "inside the drift envelope — not attributable"; > 1.1 pt: UC-attributable |
| C1 class TWh 2021 | 70 MW × 1,464 h (May–June) = **≤ 0.10 TWh** per class | \|ΔTWh\| ≤ 0.10: not attributable; larger: UC-attributable |
| C3b, C4, C8, C3c 2021 | no envelope derivable from the golden's maxima | reported; a status change is classified by whether the C3a / C1 deltas of the same year are UC-attributable |

The 2021 drift itself is the owner's open question (re-solve / re-register the 2021 leg at a SHA ≥ `59490433`), routed by
the FINDING; this lane does not resolve it and runs no control solve (rule 29(b)).

## 10. G-DRIFT — `main` at the pin vs the keeper's basis `306f2c00`, on the NYISO backcast path (zero LP, on the objects)

705 commits on `main` between the basis and the pin; 79 non-merge commits touch `src/market_sim` or the solve scripts.
Two segments, each discharged by a different instrument:

**Segment A — `306f2c00 → e8570532` (the UC-1 golden's merge-base, 2026-10-03): discharged by the NYISO golden.** The golden
replayed the keeper recipe at `ec758d64` = `e8570532` + the UC-1 commits, gate off: *"313 recorded flags replayed identically;
scenario_config 947 matched, 0 drifted"*; 2022–2025 bit-identical in every hourly file and column; 2021 = the `59490433`
drift of §9 only (bisected zero-LP). Everything in this segment is therefore INERT for 2022–2025 and the one LIVE hunk for
2021 is known and bounded. This includes `4e01a53f8` (2026-10-02 10:27, *"Re-derive the NYISO gas-offer margin anchors on
the repaired gas basis"*: `GAS_OFFER_MARGIN_ANCHOR_BY_ISO["NYISO"]` 3.9046 → 3.8739 and the `_BY_ZONE` table) — a
NYISO-keyed solve-surface move, output-inert because the keeper arms none of `gas_offer_margin` /
`gas_offer_margin_zonal_anchor` / `gas_offer_margin_anchor_vintage` (golden-proved), and `e86fc2c5` (vectorised loaders,
`mc_base` identical across the three trees). The rule-26 deletion of `unit_outage_dispatched_bin_live_denominator`
(recorded `None` in this keeper) is handled by `replay_keeper.py`'s deleted-field registry (`("NWPP", (True, None))`): inert.

**Segment B — `e8570532 → 2f872a62` (2026-10-03 → 10-09): 20 non-merge commits, 31 files, every hunk classified.**

| content | files | NYISO classification |
|---|---|---|
| UC engine (UC-1 `ca33a51f`, `8c6ad646`, `75ea989f`, `d3aa55ed`, `4e7b54d5`), UC-1-FIX (`1c0a8b8f`), UC-SPEED (`84e928ef`, `5dc76955`) | `model/uc/*` (new), `pipeline/uc.py` (new), `pipeline/solve.py` (+27: the ONE hunk `if getattr(config, "unit_commitment_milp", False):`), `runner.py` / `run_calibration_full.py` drains (gated on the same field), `floor_mechanisms.py` MECH 28, `scenarios.py` (gate + nine `uc_*` fields, validator, `UC_REFUSED_ALWAYS`, cache-key registration at the declared defaults), `legitimacy_diagnostics.py` (none for 28) | **LIVE on the gate-on path = the arm itself; INERT for the control** (gate off; every new field registered at its default and ABSENT from the keeper recipe → dropped from `cache_key()`) |
| closeout-SOCO-w3 `6cfad57b` / `e64b41c2` | `diagnostic_coal_metered_online_floor` (default False, never promotable); `data/coal_metered_online.py` (new); `pipeline/commitment.py` +110 (`wrap_coal_metered_online_diagnostic_prep`: `return base_prep` when the flag is off); wrap calls in `pipeline/year.py`, `runner.py`, `run_calibration.py`; MECH 29 + a D-4 window for it | **INERT**: identity when off; ABSENT; no coal in NYISO |
| closeout-PJM-elliott `90cea720` | `pjm_elliott_measured_outage_overlay` (False); `data/pjm_elliott_outages.py` (new); `fleet/arrays.py` under `_iso == "PJM" and config.pjm_elliott_measured_outage_overlay and mode == "backcast"` | **INERT**: PJM-gated, default off, ABSENT |
| closeout-PJM-w3 `41a9e2d9` / `bc163dbc` | `nuclear_winter_capability_basis` (False); `fleet/arrays.py::_apply_nuclear_winter_basis` under `_iso == "PJM" and …`; `constants.NUCLEAR_MONTHLY_CF_UNCLIPPED_BY_YEAR` (PJM key only; declared, moves no key) | **INERT**: PJM-gated, default off, ABSENT |
| closeout-ERCOT-w3 `9d06ad03` | `coal_perplant_cliff_split` (False); `fleet/assembly.py::_coal_cliff_split_frac` returns None unless coal + flag (raises outside ERCOT); `legacy_bins.py` helper | **INERT**: default off, ERCOT-gated, ABSENT, no coal |
| closeout-MISO-w3 `72ed3d85` | `miso_seam_neighbour_hourly_full_span` (False); `interchange/spec.py` +97 (MISO ladder tables, 2019–2022); `interchange/miso.py` table merge under the flag; `run_calibration.py` rule-19 refusal | **INERT**: default off, consumed only by the MISO interchange path, ABSENT |
| NWPP-NEXT-27 `440ad144` | `nwpp_path76_served_schedule` (False); `eia930/demand.py`, `eia930/envelopes.py::nwpp_path76_served_zone_legs`, `pipeline/ttc.py`, `runner.py` refusals; `run_calibration*.py` plumbing | **INERT**: NWPP-only path, default off, ABSENT |
| closeout-CAISO-w6 `c0f78671` / ERCOT-w6 `6cf95135` | `caiso_chp_btm_measured`, `ercot_chp_btm_measured` (False); `data/chp.py` `measured_chp_btm_pct_for_iso` / `chp_btm_measured_armed`; `run_calibration_full.py::_btm_frame`: `if iso == "NYISO": measured_chp_btm_pct_nyiso()` → `if iso in ("NYISO","CAISO","ERCOT"): measured_chp_btm_pct_for_iso(iso)` with `_run_measured = nyiso_chp_btm_measured` for NYISO; `_run_config_mustrun_chp_btm` now also reads `scenario_config` | **INERT for NYISO**: the NYISO branch is an identity rewrite (same artifact, same flag); the keeper records `mustrun_chp_btm_holdout = False` in every block; `paths.EIA_923_DISPOSITION_*` is a derive input, unread by the solve |
| solve surface | `solve_surface_register.py --diff 306f2c00 2f872a62`: *"336 → 342 names; 3 moved, 6 added, 0 removed"* — moved: `GAS_OFFER_MARGIN_ANCHOR_BY_ISO` / `_BY_ZONE` (NYISO; segment A, golden-inert) and `NUCLEAR_MONTHLY_CF_BY_YEAR` (MISO/NWPP/PJM/SOCO/SPP; not NYISO); added: the PJM unclipped table + five NWPP seam/COI constants (declared; move no key) | the control's `cache_key()` therefore does NOT reproduce at the pin (2024: `6f4ac821dd2dc92f` at the basis → `552e9952bb26754b` at HEAD, every year moved) — a registry fact of segment A (the anchor re-derive + the deleted field), output-inert by the golden; the arm's key is computed at the pin and recorded in each leg's `run_config.json` |
| tooling | `shard_prompt.py`, `replay_keeper.py`, `calibration_verdict.py`, `legitimacy_diagnostics.py` (+8 for MECH 29 only), `_ucmilp_compose_span.py` present; `results/calibration/w0_nyiso_span/**`, `keepers/NYISO.json` as on `main` | control unchanged (rule 29(b)) |

Nothing in segment B is LIVE for NYISO outside the UC stage. The arm-vs-control delta is UC-only for 2022–2025 and
UC + the §9 drift for 2021.

## 11. DO NOT REDO

Everything in `docs/mechanism-testing-matrix.md` §5.5's DO-NOT-REDO list (§1); no `uc_*` value other than the declared
defaults; no second arm (a floors-off arm is the owner's separate D-6 follow-up, as ruled for SPP); no control solve; no
re-solve of the 2021 control leg (the owner's open question, §9); no registration on the dashboard; no promotion.

## Addendum A (2026-10-10 01:50Z, before any span shard exists) — the bench gate's first run hit a HARNESS defect; amended run

The bench shard (`session_01PbNTnQLYPvowX7bqgSH11a`) passed every hard stop and solved the NYISO 2024 capture
(`data_prep=24.6s solve_p0=145.4s markup=19.6s solve_p1=177.6s results_write=19.2s total=386.5s`; memory peak
cgroup 6.81 GiB), then stopped BEFORE the L1 window on:

```
File "scripts/lib/uc_bench.py", line 77, in save
    pickle.dump(self, fh, protocol=pickle.HIGHEST_PROTOCOL)
AttributeError: Can't pickle local object 'build_nyiso_gas_bridge_p1_prep.<locals>._fleet_prep'
```

- **Classification:** a bench-HARNESS defect, not an engine defect and not a kill (§6): `--save-capture` pickles the
  `YearCapture`, whose `hooks` carry the NYISO keeper recipe's bridge P1 hook — a closure defined inside
  `pipeline/commitment.py::build_nyiso_gas_bridge_p1_prep`, which `pickle` cannot serialise. Every ISO whose keeper arms a
  P1-prep closure (NYISO; CAISO's RA bridge, ERCOT's gas bridge by the same construction) hits it with `--save-capture`;
  SPP's keeper arms none, so the SPP ladder never saw it. The engine itself was never reached. Routed to UC-DESK for the
  engine lane (`scripts/lib/uc_bench.py`: strip non-picklable hooks in `YearCapture.save`, or hoist the closure); this lane
  edits no script (rule 32: a shard that stops with a clear report is a success).
- **Amended run (the shard is re-instructed in its warm container; one logical change — no saved capture):** L1 and L2 are
  run as two independent invocations, each capturing P0 + P1 itself (`--save-capture` and `--capture` dropped); every
  other argument — the nine `--set`s, `--months 1 --arms "" --rolling`, the out-dirs, the push list, the 60-min budget
  (restarted at the amendment) — is unchanged. The gate line (§0) is unchanged: window 0 Optimal AND 31/31 January
  windows Optimal, 0 time-limit hits, gap_max ≤ `uc_mip_rel_gap`, no `UcWindowInfeasible`.
- **Budget extrapolation (§5) now reads:** capture wall (the `total=` of the L2 rung's own timing line) + 12 × the January
  month wall + the stage's fixed overhead — computed from the amended run's report in Addendum B before the span prompts
  are generated.
