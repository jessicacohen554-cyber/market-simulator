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
   stage's schedule instead of re-solving the windows. One slot per process; a type with no
   by-value encoding is named in `engine.input_digest_opaque_types` and can only forfeit reuse,
   never fake it.

## 1. Phase 0 (zero LP)

| Question | Answer |
|---|---|
| Are a cluster's members ever distinct physical units of different mc? | No. A cluster is `(plant_code, family)` (`params.build_uc_cluster_params`). Under CAMPD binning, one LP unit per plant is split into tranches; under legacy bins every row is its own cluster (`-(row+1)` key, one member, so merit fill ≡ the old split up to the cap). No case was found where merit fill is wrong, so the stop condition did not fire. |
| Window floor row (b), `model/uc/window.py` ~L813 | `Σ_members P − mlf·p̄·a·u ≥ 0` is a cluster-SUM row; it allocates nothing. **Confirmed, unchanged.** |
| `model/uc/schedule.py:195` | `floor_mw = mlf·p̄·u` is a cluster total in the schedule frame; it allocates nothing. **Confirmed, unchanged** (docstring now says the P1 allocation caps it at the summed ceiling). |
| Where do ERCOT offer bands enter? | `fleet.heat_rate` per tranche (`offer_curves.py` band block; `assemble_mc`), so they are in both P0 `mc_base` and the P1 bid. The 2019 recipe has CC_REGULAR committed 0.998 / econ 0.723–1.324 / peak 151.0, and ST_GAS committed 0.91 / econ 1.02–1.2 / peak 105.6. |
| Where was R2's 2019 uplift computed? | In-process: the leg tree at `dd7fe8a8` carries `hourly/uc_uplift_2019.parquet`, so `compute_uplift` at `mc_base` produced it. Energy cost $19.14 B on 153.1 TWh ($125/MWh). |
| Does pass 2 read the same inputs? | Yes, by construction: the adaptive pass differs only in `p1_storage_discharge_cost`, which is merged into the P1 kwargs **after** the stage (`pipeline/solve.py` ~L967), and `r0` is reused when P1 was cold. The digest checks this; it does not assume it. |

**Make-whole convention.** The repo declares one: DESIGN-uc-milp-engine §2.6/§4, per cluster-day
`max(0, Σ mc_base·P1 + nl·u + su·p̄·v − Σ λ·P1)`. I follow it. It matches the ISO practice of
guaranteeing the **as-offered** three-part cost (start-up + no-load/minimum energy + the energy
offer curve at the scheduled MW, cost-capped or mitigated) against market revenue: PJM operating
reserve credits (Manual 28), MISO Revenue Sufficiency Guarantee (BPM-005) and ERCOT RUC
make-whole (Nodal Protocols §5.7). I did not re-verify those section numbers this session. In
this model `mc_base` is that as-offered energy curve, without the amortized start markup (paid
once in `start`) and without any P1-only bid adjustment.

## 2. Tests (unit first; `tests/unit/model/uc/test_floor_merit_fill.py`, 10 new)

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
`5209ab90`: **11,685 passed**, 67 skipped, 3 xfailed, 0 failed.

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

PENDING.

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
