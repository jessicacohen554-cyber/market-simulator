> Status: PROPOSED (2026-10-03) — the testing protocol for the MILP unit-commitment program: the zero-LP benefit screen that ranks ISO-years, the wallclock ladder that prices the stage before any full-span shard, the equivalence gates the engine PR must pass, the A/B design, and the report formats. Every threshold below is a **declared default**: a lane's PRECOMMIT may tighten it or substitute a cited one, before any number exists, never after. Plan: `docs/uc-milp-program-plan-2026-10.md`.

# GATESPEC — testing protocol for the MILP UC stage

```
 UC-0  benefit screen (0 LP)  ──►  ranked board  ──►  UC-1 ladder (bench shards)  ──►  wall table  ──►  UC-2 A/B (7 shards per ISO)
        which ISO-years?                                 what does it cost?                             does it move the board, honestly?
```

## 1. Benefit screen — which ISO-years would gain most (zero LP, one research lane)

Inputs: the committed keeper bundles only (`results/calibration/<keeper>/dispatch/<y>_P1.parquet`, `hourly/*`, `run_config.json`), the committed actuals the scorer reads (EIA-923/930 class energy, RT prices, AS prices where present, CEMS unit hourly), and the fleet physics tables. No solve. Probe: `scripts/probes/_ucmilp_benefit_screen.py` → `results/phase0/xiso/_ucmilp_benefit_screen.json` + the FINDING with the board.

| Metric | Definition (per ISO-year; slow-start classes = CC, coal subclasses, ST_GAS; `*_CHP` excluded) | Direction of UC effect | Source |
|---|---|---|---|
| **M1 physics-violating cycling** | plant-level on/off from the keeper's P1 dispatch (on = output ≥ 1 % of available cap, the SPP-97 convention); energy inside on-runs shorter than the class min-up and off-gaps shorter than min-down (TWh, % of class energy); keeper starts vs CEMS starts per plant-year | fewer, longer runs; starts toward CEMS | `dispatch/<y>_P1.parquet`, `custom-bin-assignments.csv` / NREL tables, CEMS |
| **M2 part-load online gap** (both directions) | (a) CEMS online at ≤ (mlf + 0.10)·cap while the keeper is off → TWh at min-load (SPP-102 §2.1 generalized); (b) keeper on at ≤ pmin-ish output while CEMS is off → TWh | (a) up, (b) down | CEMS, keeper dispatch, mlf tables |
| **M3 trough price residual** | C3a decomposed by actual-price tercile: lower-tercile mean error ($/MWh) × hours = $·h; count ratio of model/actual hours ≤ $15 and < $0 | lower-tercile error toward 0; low/negative-hour ratio toward 1 | keeper `system.parquet`, RT price reference |
| **M4 reserve dormancy** | share of hours with model reserve MCP < $1 vs actual; mean model vs actual MCP (ISOs with an AS reference) | dormancy down | keeper reserve duals, `data/raw/<ISO>-AS` |
| **M5 price-taker DP bound** | `_spp102_commit_dp.py` generalized: per plant, binary UC by DP at the keeper's zonal P1 price with three-part costs (start, no-load, mlf, UT, DT), (i) perfect foresight, (ii) 36-h horizon; Δ class energy and Δ min-load MWh — an **upper bound** on the economic commitment effect at fixed prices | bounds M1/M2 reach | keeper price + stack dump |
| **M6 cluster census** | integer clusters per ISO (count, MW) under the E1 gate; integers per 36-h window | sizes the ladder | fleet tables |

**Ranking (declared default).** Primary score S1 = |M3 lower-tercile $·h| on years that fail C3a or C3b in the board; secondary S2 = M2(a) + M2(b) TWh; tiebreak M1. Eligibility: S2 ≥ 1.0 TWh or M4 dormancy gap ≥ 0.20. **Selection:** the top 3 ISO-years by S1 among eligible rows become the ladder's targets; **NEISO 2023 and NYISO 2024 are always controls** (CALIBRATED ISOs; the no-flip bar in §4 protects them). The board is published as a 9 × 7 table (S1 / S2 per cell, failing gates marked) before the engine lane is chartered, and the selection is written in the UC-1 PRECOMMIT.

Expected candidates from the records (to be confirmed by the screen, not assumed): SPP 2019/2020 (body over-price, thermal online at sub-cost), MISO 2020 (low-load margin, reserve dormancy), PJM 2020/2022 (commitment-cost representation), ERCOT 2019/2020 (coal vs CC through troughs), CAISO 2019–21 (bridge replacement). `ASSESSMENT` §6 has the per-row reading and what the records already rule out.

## 2. Pre-fixed readings for the screen itself

The screen can fail: if no ISO-year is eligible, the program records that the model's remaining misses are not commitment-shaped at the grain the keeper exposes, UC-1 is still built default-off (the structural capability and the forecast case stand on their own), and UC-2 runs on the two controls plus the highest-S1 row only.

## 3. Wallclock ladder — what the stage costs (bench shards; every rung a shard, rule 32)

Harness: `scripts/diagnostics/bench_uc_ladder.py --iso <ISO> --year <Y> --rung L1|L2|L3 --out results/bench/uc/<iso>_<y>_<rung>` built by the engine lane on the `bench_cold_solve.py` capture seam (the captured production LP rebuilt as `DispatchModel`, exactly as the deleted crossbench did). Container: the standard solve container (`prepare_solve_container.py` first; `MARKET_SIM_HIGHS_THREADS=1` unless the rung arms E7).

| Rung | What runs | Reports (per window unless stated) | Pass |
|---|---|---|---|
| **L0** toy (CI fast tier) | 1 cluster × 1 zone × 24 h; 2 clusters × 6 h | optimality, no-load decommit, UT/DT respected, warm start accepted at 0 nodes, integer-empty ≡ LP | always green |
| **L1** one window | the captured ISO-year LP sliced to hours 0–35, integer columns added; solved (a) MILP, (b) LP-relaxed, (c) P1 slice as-is | build s, MILP s, nodes, final gap, integers, columns, RSS; **integrality gap** = obj(a) − obj(b); Δ committed energy, Δ starts, Δ trough price vs (c) | solves; gap ≤ 1e-3 |
| **L2** one month | 31 rolling windows, Jan and Jul (two months, worst-case seasons); arms: warm start on/off (E3), pre-fixing on/off (E5), threads 1/4 (E7) | distribution (p50/p95/max) of MILP s and nodes; share of windows at 0 nodes; time-limit hits; solution equality across E5 arms (schedule hash) | p95 MILP s × 365 ≤ ceiling; E5 arms identical schedules |
| **L3** one year | the full stage (P0 → markup → UC → P1) on the ISO-year, one shard, `--years <y>` | **the wall table** (§6.1): P0 s, UC s (Σ, mean, p95), P1 s, total s, ratio vs the baseline row; schedule and uplift sidecars written; `uc_solve_log.json` | ratio ≤ ceiling (D-2); time-limit hits ≤ 1 % of windows; no infeasible window |

Order: L1 → L2 on the top-ranked ISO-year first; L3 on each selected ISO-year and NEISO. A rung that fails its pass line stops the ladder for that ISO and names the lever (E2 wider window, E5, E7) tried next in a new bench shard; levers are never swept against gates (they change wall clock, not the optimum, and E5's equality check proves it).

Baseline rows (the denominators) come from `docs/records/misc/wallclock-baseline-2026-07.md` §WALLCLOCK 3a, re-measured in the same container class when the ISO has no row (SPP, SOCO, NWPP).

## 4. Equivalence and regression gates for the engine PR (UC-1)

| Gate | Statement | How |
|---|---|---|
| **G-OFF** byte-identity | with `unit_commitment_milp=False` every keeper recipe reproduces its committed bundle: objective, prices, dispatch at `atol = rtol = 0` | `capture_keeper_goldens.py` replay per ISO in a shard (9 shards, pinned recipe), golden-diff |
| **G-EMPTY** | gate on, integer set empty → schedule all-available → P1 identical to G-OFF except the markup zeroing (which is off when the set is empty) | toy + one captured window |
| **G-DRIFT** | every changed hunk on the backcast path classified INERT-with-reason or LIVE (rule 29); only `run_energy_solve`'s one hook hunk is LIVE and gated | PR description |
| **G-KEYS** | `cache_key()` of every keeper recipe unchanged (the new fields are dropped at their declared defaults) | `check_cache_key_registration.py` + the keeper-key test |
| **G-MATRIX** | row + cell per shard present | `check_mechanism_matrix.py --base` |
| **G-TESTS** | fast tier green; the `slow` window test green locally | CI + pre-push |

## 5. A/B design (UC-2, one PRECOMMIT per ISO, 7 shards)

| Element | Specification |
|---|---|
| control | the ISO's incumbent keeper bundle, every registered year (rule 29(b): no control solve) |
| arm | the keeper recipe + `unit_commitment_milp=true` + the rule-19 substitutions the ISO's census names (bridge off, posture off, markup zeroed on integer clusters) — **one logical delta**; `uc_*` fields at their declared defaults; `uc_window_time_limit_s` from the ladder |
| years | every year the keeper carries, one shard each (rules 16, 36); composed by `_ucmilp_compose_span.py`; diagnostics regenerated, never copied |
| **target readings** (fixed ex ante per ISO) | for each board row the screen named: the sign and a bar (default bar: half the distance to the gate band, the closeout plan's convention); for M4 ISOs: dormancy share and mean MCP direction |
| **control readings** | no PASS→FAIL flip on any registered year of this ISO; NEISO/NYISO spans re-solved once with the gate on: no flip, |ΔC3a| ≤ 1 pp |
| **structure readings** | D-2 energy under MECH 28 (reported; budgeted only if D-4 says so); starts per plant-year vs CEMS (M1 re-measured on the arm); online capacity vs the measured online series where one exists (SPP portal `hourly-gen-capacity-by-fuel-type`, MISO ASM cleared, ERCOT telemetered — comparators, never inputs) |
| **cost readings** | wall ratio ≤ the D-2 ceiling on every year; time-limit hits ≤ 1 %; uplift ≤ a declared share of energy cost (default 2 %, sanity) |
| **kills** (any ⇒ record and stop, no re-tune) | an infeasible window (engine defect, not a tuning invitation); schedule hash differs between two runs of the same recipe (non-determinism); a control flip |
| verdict → matrix | K (promoted), R (worsens a target or flips a control), I (|Δ| below the bar everywhere), with the RESULT cited in `mechanism-matrix/<ISO>.js` |

## 6. Report formats

### 6.1 The wall table (one row per ISO-year; the ladder's L3 and every A/B shard print it)

| ISO-year | baseline P0+P1 s | P0 s | UC Σ s (windows, mean, p95 MILP s) | P1 s | total s | **ratio** | integers/window | nodes p50/p95 | gap p95 | time-limit hits | peak RSS GB |
|---|---|---|---|---|---|---|---|---|---|---|---|

### 6.2 The benefit board (9 ISOs × 7 years; S1 / S2 per cell; failing gates marked; selected cells bold)

| ISO | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | clusters (M6) |
|---|---|---|---|---|---|---|---|---|

### 6.3 The A/B gate table (per ISO; one row per registered year)

| year | C1 (class rows) | C2 | C3a | C3b | C3c | C4 | C6 | C8 | D-2 MECH 28 share | wall ratio | reading met? |
|---|---|---|---|---|---|---|---|---|---|---|---|

## 7. Honesty clauses

1. A target reading not met is a verdict (`I` or `R` with evidence), not a reason to move a parameter; the `uc_*` fields are declared once and never swept against a gate (rule 1 (c) by analogy).
2. "The relaxation was already tight here" (L1 integrality gap ≈ 0 and L3 ≈ P1) is a legitimate and useful finding: it bounds what the model class was missing in that ISO.
3. A wall ratio above the ceiling is a cost finding, not a defeat: the stage stays default-off for that ISO and E10 goes to the owner.
4. No number from this protocol enters a keeper, a status part or the rubric until the owner rules D-6 for that ISO.
