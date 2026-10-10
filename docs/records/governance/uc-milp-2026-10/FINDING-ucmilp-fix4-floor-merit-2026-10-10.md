# FINDING — UC defect 6: the P1 floor was split pro rata into a plant's peak tranches

Lane UC-1-FIX-4 (`session_015ufz1xKsyr8tPZGkTk2MrL`, Opus), 2026-10-10, chartered by UC-DESK
(`session_01WX9W5tgYMre3Z134LZoGF6`). Pin `3a3c8695`; branch `claude/ucmilp-fix4-floor-merit`.
Defect report: UC-2-ERCOT-R2 (`RESULT-ucmilp-ercot-ab-2026-10-10.md` §3 W3), 2019 leg
`claude/ucmilp-ercot-d-2019` @ `dd7fe8a8`. Year LP solved in this session: **zero** (one repro
shard, §5).

## 0. Headline

**Root cause.** `UcStage.floor_and_ceiling` split the cluster floor `mlf·p̄·u` across the
cluster's members in proportion to `pmax·availability`. Under `use_campd_bins` a cluster's
members are the offer tranches of one plant's units (`_mustrun / _committed / _econ… /
_peak…_peak5`), so every committed hour forced a share of the floor onto the peak tranches.

**Why the uplift was $15 B, corrected.** R2 read the cause as "`uplift_from_bundle` prices at the
P1 offer, D-3 zeroes the markup but not the band". The leg in fact carried its own in-process
frame (`compute_uplift`, already at `mc_base`). The real point: **ERCOT's offer bands live in the
tranche heat rate**, so they are in `mc_base` itself. `data/offer_curves.py` sets `peak_hr =
base_hr × offer["peak"]`; the 2019 recipe has CC_REGULAR peak 151.0× and ST_GAS 105.6×. Pricing
at `mc_base` therefore still costs that energy at ≈ $2,800/MWh. **The merit fill is the fix**, and
the uplift basis change is housekeeping.

**Fix (engine `uc-1.3`; no new field, no tuning).**
1. **Merit fill.** `pipeline.uc.merit_floor_allocation` pours each integer cluster's floor into its
   members in ascending P1 offer (the final bid the hook reads; ties by fleet row). Each member is
   filled up to its ceiling `pmax·availability·u/n` and the remainder carries to the next. A floor
   above the summed ceiling is filled to the ceiling. Vectorised: one `lexsort` on the hour axis and
   a cumsum over a `(T, n_int, M)` block, where `M` is the most members any cluster has. There is no
   loop over hours or members. The pro-rata path is deleted (rule 26).
2. **Uplift basis.** `compute_uplift` is unchanged; it already prices at `mc_base` per DESIGN §2.6/§4.
   `uplift_from_bundle` is **deleted**: a bundle carries only the P1 offer (`unit_marginal.mc`),
   never `mc_base`. The compose script now reports a missing frame instead of repricing it.
3. **Pass-2 reuse.** `p1_fleet_prep` hashes everything `run()` reads (`uc_input_digest`, blake2b).
   That covers engine version, ISO/year/horizon, every `uc_*` field, solve options, cluster
   params, both fleets, demand, dispatch kwargs, `mc_base`, the final P1 bid, and P0
   dispatch/SOC/prices/flows. A stage whose digest equals the previous stage's adopts that
   stage's schedule instead of re-solving the windows. There is one slot per process. Arrays,
   containers, dataclasses, pandas objects and scipy sparse matrices are hashed by value. Any
   other type is named in `engine.input_digest_opaque_types` and **forfeits** reuse. The repro
   showed that a `repr` (here `csr_matrix`) can match for different contents, so a `repr` never
   certifies equality. That hardening landed after the repro (§5.2).

## 1. Phase 0 (zero LP)

| Question | Answer |
|---|---|
| Are a cluster's members ever distinct physical units of different mc? | No. A cluster is `(plant_code, family)` (`params.build_uc_cluster_params`). Under CAMPD binning, one LP unit per plant is split into tranches; under legacy bins every row is its own cluster (`-(row+1)` key, one member, so merit fill ≡ the old split up to the cap). No case was found where merit fill is wrong, so the stop condition did not fire. |
| Window floor row (b), `model/uc/window.py` ~L813 | `Σ_members P − mlf·p̄·a·u ≥ 0` is a cluster-SUM row; it allocates nothing. **Confirmed, unchanged.** |
| `model/uc/schedule.py:195` | `floor_mw = mlf·p̄·u` is a cluster total in the schedule frame; it allocates nothing. **Confirmed, unchanged** (docstring now says the P1 allocation caps it at the summed ceiling). |
| Where do ERCOT offer bands enter? | `fleet.heat_rate` per tranche (`offer_curves.py` band block; `assemble_mc`), so they are in both P0 `mc_base` and the P1 bid. The 2019 recipe has CC_REGULAR committed 0.998 / econ 0.723–1.324 / peak 151.0, and ST_GAS committed 0.91 / econ 1.02–1.2 / peak 105.6. |
| Where was R2's 2019 uplift computed? | In-process: the leg tree at `dd7fe8a8` carries `hourly/uc_uplift_2019.parquet`, so `compute_uplift` at `mc_base` produced it. Energy cost $19.14 B on 153.1 TWh ($125/MWh). |
| Does pass 2 read the same inputs? | Yes, by construction: the adaptive pass differs only in `p1_storage_discharge_cost`, which is merged into the P1 kwargs **after** the stage (`pipeline/solve.py` ~L967), and `r0` is reused when P1 was cold. The digest checks this; it does not assume it. |

**Per-ISO member layouts (UC-DESK request, after UC-2-NEISO #7236).** These counts come from the
committed `uc_solve_log` cluster rows (`members`, `plant_code`), zero LP:

| ISO (log) | clusters / integer | members per integer cluster | clusters with `plant_code ≤ 0` (legacy singleton key) |
|---|---|---|---|
| ERCOT 2024 | 139 / 61 | 3 (6), 4 (1), 12 (13), 17 (41) | 0 |
| NEISO 2022 | 69 / 35 | 7 (16), 8 (19) | 0 |
| MISO 2024 | 320 / 77 | 4 (20), 7 (19), 8 (37), 24 (1) | 0 |
| CAISO 2024 | 115 / 34 | 3 (1), 6 (2), 7 (14), 8 (2), 12 (15) | 0 |
| NYISO 2024 | 78 / 34 | **1 (7)**, 4 (11), 7 (6), 8 (10) | 0 |
| SPP 2024 | 221 / 83 | 3–12 | 0 |

Every armed ISO's integer cluster is one plant's set of offer tranches, keyed `(plant_code,
family)`. NEISO's "legacy bins" are per-plant tranches too (7–8 members). The pro-rata split
therefore floored every ISO's peak tranches, which matches the NEISO evidence: CC_REGULAR `peak`
ran 8,758–8,760 h in the arm against 14–467 h in control. One merit fill covers all of them. A
true legacy row (no plant code) is its own singleton cluster. There the fill is the old split up
to the member's ceiling, tested by `test_legacy_bin_rows_are_singleton_clusters_with_a_capped_floor`.
NYISO's seven single-member clusters are the same case.

**Make-whole convention.** The repo declares one: DESIGN-uc-milp-engine §2.6/§4, per cluster-day
`max(0, Σ mc_base·P1 + nl·u + su·p̄·v − Σ λ·P1)`. I follow it. It matches the ISO practice of
guaranteeing the **as-offered** three-part cost (start-up + no-load/minimum energy + the energy
offer curve at the scheduled MW, cost-capped or mitigated) against market revenue: PJM operating
reserve credits (Manual 28), MISO Revenue Sufficiency Guarantee (BPM-005) and ERCOT RUC
make-whole (Nodal Protocols §5.7). I did not re-verify those section numbers this session. In
this model `mc_base` is that as-offered energy curve, without the amortized start markup (paid
once in `start`) and without any P1-only bid adjustment.

## 2. Tests (unit first; `tests/unit/model/uc/test_floor_merit_fill.py`, 13 new: the 10 below, the legacy-bin singleton test (§1) and the two digest tests (§5.2))

Pure allocator, one cluster with 3 tranches over 24 h (offers $30 / $20 / $2,821; ceilings 50 / 30 / 20):
- **cheapest first:** a floor of 50 gives [20, 30, 0], and the peak tranche is never floored;
- **caps and remainder:** 90 gives [50, 30, 10]; 500 gives [50, 30, 20] (filled to the ceiling);
- **u = 0** gives an exactly zero floor;
- **ties** go by fleet row;
- **merit order is per hour** (the order flips at hour 12);
- **two clusters fill independently**, with members listed out of order.

Stage through `run_energy_solve` (1 CC plant = 3 tranche rows, uc-params n = 2, mlf 0.5, plus a CT):
- floors are econ 30·u, committed 20·u, peak 0, sum 50·u, under MECH 28;
- the scored P1 runs the peak tranche at 0 MW;
- **uplift at `mc_base`:** with a +$500 P1-only `mc_bid_adjust` on the cluster's rows, `energy_cost_usd` = Σ `mc_base`·P1 exactly;
- **pass-2 identity:** a second identical solve has `engine.reused_schedule` set, the same schedule object, the same digest, no opaque types, and identical P1 floors, dispatch and prices;
- **changed input re-solves:** demand +1 MW gives a new digest, no reuse and a new schedule.

Amended: `test_compose_span` (a leg without a frame is no longer repriced) and
`test_window_pinned_floor_guard` (asserts `UC_ENGINE_VERSION`, not a stored string). The conftest
clears the reuse slot per test.

**Fast lane** (`pytest -n auto -m "not slow and not integration and not fulldata"`) at
`5209ab90`: **11,685 passed**, 67 skipped, 3 xfailed, 0 failed. At the PR head: 11,687 passed and 1 transient failure, `test_committed_run_payloads_reencode_byte_identical`. That test ran while my local scoring payload sat under `frontend/data/backcast/runs/`; it passes once the payload was moved out.

## 3. G-OFF and G-DRIFT

Every changed source line is in `pipeline/uc.py`, `model/uc/uplift.py`, `model/uc/schedule.py`
(a docstring) and `scripts/probes/_ucmilp_compose_span.py`.

| Hunk | Class | Reason |
|---|---|---|
| `pipeline/uc.py` (allocator, digest, reuse, `floor_and_ceiling`, version) | INERT off | imported only inside `if getattr(config, "unit_commitment_milp", False)` (`pipeline/solve.py:675`), the drains (`run_calibration_full.py:7482`, `runner.py:4176`, both under the gate) and the bench |
| `model/uc/uplift.py` (deleted `uplift_from_bundle`, docstrings) | INERT off | reached only from `UcStage.artifacts` and the UC compose probe |
| `model/uc/schedule.py` | INERT | docstring only |
| `_ucmilp_compose_span.py` | INERT off | `write_uplift` runs only for an armed composite |

**G-OFF, zero LP, ISO-independent:** importing the whole off-path solve stack
(`pipeline.solve`, `pipeline.year`, `runner`, `scripts/run_calibration_full.py`,
`scripts/replay_keeper.py`) loads **none** of `market_sim.pipeline.uc` or `market_sim.model.uc.*`.
`test_gate_off_is_byte_identical_and_never_imports_the_stage` asserts the same at run time. No
changed byte is reachable with the gate off, for ERCOT, MISO or any ISO, so no per-ISO argument
capture and no golden shard is needed. No LIVE hunk is on the off path.

## 4. What changes on the armed path beyond ERCOT

Merit fill also caps a **single-member** cluster's floor at its ceiling `pmax·a·u/n`, i.e. at
`p̄·a·u`. Before, the pro-rata floor `mlf·p̄·u` could exceed a derated ceiling (`a < mlf`), and the
bridge tail (`_bridge_floored_fleet`) then raised availability to keep it feasible. That re-opened
a ceiling the schedule had closed. The fix removes this on every ISO's armed path. It is
correctness, not tuning; it bites only where `a < mlf`.

## 5. Repro shard — ERCOT 2019, R2 arm at uc-1.3

**Run.** Shard `session_0182rsShjTKUPJQyKZCufYTT` @ `5209ab90`, replaying `closeout_ercot_l1_span --years 2019`
with `unit_commitment_milp=true`, `ercot_gas_commitment_bridge=false`, the same arm as R2's 2019 leg.
Bundle `claude/ucmilp-fix4-ercot-2019` @ `6f61bdee`: 21 files, including `dispatch/2019_P1.parquet`
and all five UC artifacts. I fetched it, checked it out and verified it, then archived the shard.
Scoring: `calibration_verdict.py` rubric 3.20, through a local `dashboard_add_run.py --no-prune`.
The sidecar and payload were moved out of the tree and never committed (E13, the R2 procedure).
Forced-peak and uplift readings come from `fix4_readings.py` (zero LP; script, both readings and the FIX-4 verdict JSON in `data/fix4/`). Its metric is P1 MW on a
`_peak*` tranche of a committed integer cluster, in hours where the offer is above the zonal
LMP. It reproduces R2's 5.81 TWh exactly.

| 2019 reading | control (keeper) | R2 (uc-1.2, `dd7fe8a8`) | **FIX-4 (uc-1.3, `6f61bdee`)** |
|---|---|---|---|
| forced `_peak*` energy, TWh (CC / ST_GAS) | – | 5.807 (5.301 / 0.506), median offer $2,797 | **0.120** (0.116 / 0.004) |
| uplift $, and % of Σ λ·load | – | $14,977.7 M, 83.9 % | **$349.6 M, 1.65 %** |
| C3a mean LMP (actual RT $46.55) | $49.41, +6.2 % PASS | $46.58, +0.1 % PASS | **$55.16, +18.5 % FAIL** |
| C3b monthly NRMSE (band ≤ 0.20) | 0.216 FAIL | 0.078 PASS | **0.281 FAIL** |
| C1 CC_REGULAR (actual 132.2 TWh) | +9.21 FAIL | +8.31 FAIL | **+0.25 PASS** |
| C1 COAL_PRB (actual 61.3 TWh) | −10.79 FAIL | −9.15 FAIL | **−4.61 PASS** |
| C1 ST_GAS | +3.29 PASS | +1.23 PASS | +2.03 PASS |
| C8 ST_GAS forced share (< 30 %) | – | 28.0 % PASS | 25.8 % PASS |
| C8 CC_REGULAR forced share | – | 1.7 % PASS | 2.9 % PASS |
| tail hours (actual 106) | 90 | 76 | 111 |
| unserved MWh / NaN cells | – | 0 / 0 | 0 / 0 |
| UC windows | – | 365 Optimal ×2 passes | 365 Optimal, 0 TL; pass 2 **reused** (2.3 s) |
| wall: total / (P0+P1) | – | 18,756 s, **21.7×** | 8,302 s, **10.3×** (UC 7,337 s; P0 247; P1 562 both passes) |

**Schedule identity.** The reused `u` / `v` / `w` equal R2's cell for cell. R2 re-solved pass 2
from scratch, so the reuse produced the same schedule a re-solve does. This is the third
measurement of that, after the FIX-2 2020 gate and R2. The floor allocation is P1-only; the
windows never read it.

### 5.1 What the numbers say

The merit fill removes **98 %** of the forced peak-tranche energy and **97.7 %** of the uplift.
It also closes the keeper's long-standing 2019 CC over-run and PRB under-run (C1 CC +8.31 → +0.25,
PRB −9.15 → −4.61, both FAIL → PASS). The 5.8 TWh of peak-tranche energy R2 forced was
uneconomic must-run supply. It displaced coal and depressed prices (362 hours at or below $15
in R2, 52 in FIX-4).

**R2's near-perfect 2019 price fit (C3a +0.1 %, C3b 0.078) rested on that defect.** Remove it
and the mean LMP rises to $55.16 (+18.5 %), and C3b FAILs at 0.281, worse than the control's
0.216. Under rule 1 / rule 14 this is a discovered miss elsewhere, not a reason to keep the
pro-rata split. The structurally right allocation exposes a price-level gap that the forced
energy was masking. FIX-4 adds no lever for it. Candidate causes, unexamined here: the
injection floor sitting above the window's own row (§6.1), and the peak-band scarcity wall
(151×) now setting price in more hours (tail 111 h against 106 actual).

### 5.2 Digest hardening after the repro

The repro's log carried `input_digest_opaque_types: ['csr_matrix']`. A scipy sparse matrix's
`repr` names only shape and nnz, so two different matrices could digest alike. In this run the
inputs were truly identical: the reused schedule equals R2's re-solved one cell for cell. The
gap was still real, and it is closed in this PR:
- sparse matrices are hashed by value (CSR `data` / `indices` / `indptr` / shape);
- any remaining opaque type forfeits reuse.

The digest is now strictly finer, so the repro's reuse would still fire. Tests:
`test_digest_encodes_sparse_matrices_by_value`, `test_an_opaque_input_forfeits_reuse`.

## 6. Open questions for the desk

1. **Injection floor vs window row (b).** The window enforces `Σ P ≥ mlf·p̄·a·u` (availability-
   weighted). The P1 injection floors `mlf·p̄·u`, capped at the summed ceiling `p̄·a·u`. Where
   `mlf·a < mlf` (any derate), P1 is floored above what the window committed to. This predates
   FIX-4 and is unchanged here (charter: confirm, don't change). Aligning the injection to
   `mlf·p̄·a·u` is a one-line engine change, armed-path only, and I recommend it.
2. **No unbanded cost exists in the fleet.** If the desk wants uplift on the physical cost
   (`base_hr`, not the authorized band), `FleetArrays` needs a per-row unbanded heat rate. That is
   a new field and a separate decision. After merit fill the floor energy sits on committed/econ
   tranches (bands 0.72–1.36), so the distinction is now small.
3. **The 2019 price level after the fix.** C3a +18.5 % and C3b 0.281 FAIL at uc-1.3, while C1
   CC and PRB now PASS (§5.1). For any later ERCOT UC A/B, the fair baseline is FIX-4, not R2:
   R2's price PASS came from the defect. Whether the gap belongs to (1) above, to the peak-band
   wall, or to the UC's decommitment pattern (T1, wrong sign in R2) is a calibration-lane
   question. This lane names it and does not tune it.
