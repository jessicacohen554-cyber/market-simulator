# FINDING — UC-1-FIX-9: the uc-1.7 NEISO window slowdown is the uc-1.6 reserve u-gate starving the `lean` preset's primal search; there is no tighter equivalent formulation

- **Lane:** UC-1-FIX-9 (Opus), chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`). Evidence from UC-4-NEISO
  (`session_01FoAQpHpMAwKdf4fmMqoZWT`): `claude/ucmilp-4-neiso` `2111cdfa` (2019 w0–119) and `be9fa22e` (2023 w0–63).
- **Defect (performance, not correctness):** the NEISO U4 windows (uc-1.7 at `7dbfe20f`) take 4.6× (2023 w0–63) and 7.4×
  (2019 w0–119) the MILP time of uc-1.5 on the same windows. 2019 and 2023 each have three 600 s time-limit hits. The
  cluster and integer sets are identical.
- **Verdict:** the cause is the **uc-1.6 reserve u-gate**. Removing it alone recovers the speed. The relaxation is not
  materially weaker. What the gate breaks is the tree's primal search under the registered `lean` preset, which has the
  LP heuristics off. Under the gate, node LPs stop coming out integral, and the gate roughly doubles the root gap left
  after cuts. The DA-forecast commitment demand (2019) and per-unit `mlf` (some windows) amplify the effect, but neither
  causes it alone. The `/n` aggregation is exact: no tighter formulation with the same integer set exists at the
  cluster level (§4). **The model-preserving remedy is a solver-path setting** (§5): turn the LP heuristics on in
  `lean`. UC-DESK ruled 2026-10-15 that this is not tuning (the gap, time limit and model are unchanged). It lands as
  engine **uc-1.8** with no new knob.

## 1. Method

- **Bench:** `uc_bench.capture_year` (keeper recipe `w0_neiso_span`, P0+P1 solved once per year in this lane's
  container; `ensure_solve_container` printed 22.4 GiB). Then one HiGHS window per probe through the production
  `UcStage.run(t_start=24w, t_end=24w+1)`, so the window and its state are built exactly as the stage builds them. The
  carried state comes from P0 at `t0−1`, not from the rolling chain. Registered options throughout (`lean`, gap 1e-3,
  600 s, 1 thread) unless an arm names a change.
- **Arms**, one factor at a time from U4 (`unit_commitment_milp`, `uc_commitment_demand_source="da_forecast"`, uc-params
  at epoch 2026-10-15b):

  | arm | change from U4 |
  |---|---|
  | −gate | `reserve_headroom_u_terms` returns no terms (the uc-1.5 window) |
  | uc-1.5 params | `uc-params` re-derived with `scripts/lib/uc_params` at `3b96390d^`. NEISO CC `mlf` p50 is 0.34 there vs 0.56 at U4; coal `ut_h` is 50 h vs 29 h |
  | actual | `uc_commitment_demand_source="actual"` |
  | uc-1.5 | all three reverted |
  | +LPH | U4 with the LP heuristics on (`UcSolveOptions.lp_heuristics=True`; otherwise `lean`) |
  | default | U4 with `uc_solver_preset="highs_default"` |

- **Caveat:** P0-state probes can be harder than the same window in the rolling chain. 2023 w31 times out in this
  bench even at uc-1.5. §3.3 therefore confirms the result on the rolling chain (w0–15, same container).
- The bench driver is a scratch harness over `scripts/lib/uc_bench.py`. No bench result is a sidecar, and no bundle was
  written.

## 2. Ablation (MILP seconds; TL = 600 s limit, with the gap at the limit)

**NEISO 2023**

| w | U4 | −gate | uc-1.5 params | actual | uc-1.5 | +LPH | default |
|---|---|---|---|---|---|---|---|
| 12 | TL 1.1e-2 | 106 | TL 5.6e-3 | TL 1.0e-2 | 42 | **40** | 40 |
| 31 | TL 6.7e-3 | TL 4.4e-3 | TL 3.5e-3 | TL 2.8e-3 | TL 3.8e-3 | **18** | 21 |
| 61 | TL 1.1e-2 | 336 | 519 | 149 | 51 | **231** | 307 |
| 6 | 305 | 117 | 248 | 186 | 56 | **90** | 103 |
| 25 | 88 | 48 | 44 | 211 | 14 | **81** | 119 |
| 33 | 3 | 6 | 1 | 1 | 1 | **2** | 2 |

**NEISO 2019**

| w | U4 | −gate | uc-1.5 params | actual | uc-1.5 | +LPH |
|---|---|---|---|---|---|---|
| 18 | 400 | 146 | TL 2.6e-3 | TL 1.8e-3 | 55 | **262** |
| 34 | 539 | 25 | 461 | 79 | 8 | **419** |
| 60 | TL 2.5e-3 | 80 | 190 | 148 | 78 | **304** |
| 6 | 129 | 107 | 108 | 173 | 95 | **30** |
| 29 | 110 | 29 | 95 | 31 | 3 | **12** |

Reading:

- **Removing the gate is the one single change that recovers speed.** It does so in 9 of 10 non-trivial probes; the
  exception is 2023 w31, a P0-state artefact that also times out at uc-1.5.
- **Reverting `mlf`/`ut_h` alone recovers nothing on the hard windows.** 2023 w12 still times out, 2019 w18 times out,
  and 2019 w34 drops only from 539 to 461 s.
- **Actual demand alone helps in 2019 only** (w34 539 → 79 s, w60 TL → 148 s). In 2023 it does not (w12, w31 still time
  out). ISO-NE's DA forecast runs below metered load (−189 MW mean in 2019), so less is committed for energy, and the
  reserve that the gate now prices onto `u` becomes the commitment driver more often.

## 3. Mechanism

### 3.1 The relaxation is not the problem

| probe | optimum − root LP (% of obj) | optimum − root after cuts |
|---|---|---|
| 2023 w12 U4 (run to optimality: 861 s, 9,777 nodes) | 0.59 | 0.27 |
| 2023 w12 −gate | 0.55 | 0.10 |
| 2019 w34 U4 | 0.69 | 0.26 |
| 2019 w34 −gate | 0.56 | 0.11 |
| 2019 w18 U4 / −gate | 0.93 / 0.84 | 0.15 / 0.10 |

- The LP relaxation bound moves by at most about 0.1 pp with the gate.
- The bound left after root cuts is about 2× wider. HiGHS's root cuts close less of a gated window's gap.

### 3.2 The primal side starves under `lean`

- **2023 w12 U4, 600 s:** the dual bound was within **0.08 %** of the true optimum (7,438,495 vs 7,444,330). The
  incumbent was the root randomized rounding at **+1.0 %**, and it never improved in 6,386 nodes.
- **Why the incumbent never improves:**
  - In every gated hard window, no node LP came out integral: the HiGHS log has no `T` rows.
  - Without the gate, `T` leaves supply the incumbents.
  - With the gate, a fractional `u` buys committed headroom for the 30-min reserve family. That family is 1,800 MW
    with an 8-step ORDC at $125–1,000/MW, and integer members are eligible only for reserve class 0. So node LPs keep
    `u` fractional.
- **What `lean` takes away.** `lean` turns off exactly the heuristics that find incumbents when leaves are not integral:
  RINS, RENS and root reduced cost (`mip_heuristic_effort` 0). That choice was a −6 % wall saving, profiled on
  ungated SPP 2020 January (FINDING-ucmilp-speed-window-solve-profile-2026-10-09 §1.1).
- **With the heuristics back on,** the same w12 window finds sub-MIP (`L`) incumbents at the root and solves in
  **40 s / 3 nodes**, at the same optimum (7,444,124).
- The carried warm start never helps. It is infeasible in **365/365** windows of every committed uc-1.5 log
  (`warm_feasible = 0`), because the P0-rounded `u` breaks the carried min-up/down. Repairing it to the Rajan–Takriti
  rows makes it feasible, but the incumbent is +26 %; the repaired w12 still times out (TL 3.0e-3). It is a latent
  defect, not this fix.

### 3.3 Rolling confirmation (w0–15, same container, registered options)

| | MILP Σ s | TL | nodes p50 | Σ objective |
|---|---|---|---|---|
| 2023 U4 (`lean`) | 2,578 | 1 (w12) | 724 | 117,209,937 |
| 2023 U4 + LPH | **717** | 0 | 1 | 117,211,361 (+0.001 %) |
| 2023 uc-1.5 | 937 | 0 | 63 | — |
| 2019 U4 (`lean`) | 1,831 | 0 | | |
| 2019 U4 + LPH | **523** | 0 | | |
| 2019 −gate | 847 | 0 | | |

This container runs about 1.3–1.7× slower than the UC-4 shards. The 2023 U4 w0–15 sum is 1,966 s in the UC-4-NEISO
shard log, and the uc-1.5 w0–15 sum is 563 s in the committed UC-3 log.

### 3.4 Not NEISO-only (one window each, 2023, P0-state)

- **NYISO** (`nyiso_gas_commitment_bridge` off, as UC requires): 144 gated rows.
  - w31: U4 129 s, −gate 32 s, +LPH 30 s (same signature).
  - w12: 4 s in every arm.
- **CAISO** (RA bridges off): the gate builds **0** rows (no integer member is in a capacity-anchored headroom row), so
  CAISO cannot regress from it.
  - w12: U4 = −gate = 258 s; +LPH 49 s.
- **SPP** (keeper recipe, ungated: 0 gated rows): w0, w12, w31, w200 all solve at the root. U4 and +LPH return the same
  objective in 2.6–4.9 s, and +LPH costs ≤ 0.2 s. The change does not slow an ungated ISO.

## 4. The `/n` question: the gated form is already the tight one

- **The per-member terms reproduce row (a).** Member `g` of integer cluster `c` enters its zone's headroom row with
  `pmax_g · a_g,t · u_c,t / n_c`. Summed over the members, that is `(Σ_g pmax_g a_g,t / n_c) · u = pbar_c · a_c,t · u`
  (`cluster_availability` is the capacity-weighted mean). This is the same capacity as output row (a), so the `/n`
  aggregation adds nothing and loses nothing.
- **Single hour.** `{(P, R, u) : mlf·C·u ≤ P, P + R ≤ C·u, 0 ≤ u ≤ n}` is the convex hull of its integer points: every
  point is `u · q` with `q` in the unit polytope.
- **Zone pooling.** The zone-pooled `R` with row (a) is the projection of the disaggregated system
  `{P_c + R_c ≤ C_c u_c, R_c ≥ 0}`.
- **Over the window.** With no startup ramps in the model, `{u ∈ RT polytope (integral), x_t ∈ u_t Q_t}` is integral.
- **So no equivalent formulation is tighter.** A per-unit binary or a disaggregated `R_c` gives the same relaxation, and
  the per-unit form adds symmetry. The remaining gap is system coupling (energy and reserve balance across clusters and
  hours). That is the economics the gate correctly adds, not a formulation artefact.

## 5. Remedies (none changes the model; the first two are solver paths)

1. **LP heuristics on for the UC windows** (RINS/RENS/root reduced cost, `mip_heuristic_effort` at HiGHS's 0.05).
   - **How:** either `uc_solver_preset = "highs_default"` (registry value) or the `lean` composition with
     `lp_heuristics=True` (engine table `UC_SOLVER_PRESETS`, uc-1.8, no new knob).
   - **What it leaves alone:** the same gap, the same time limit, the same model, the same integer set. The schedule may
     move within the 1e-3 gap, as any solver-path change does.
   - **Evidence:**
     - Rolling w0–15: 3.6× faster in 2023 and 3.5× in 2019 than U4 `lean`, and faster than uc-1.5 / −gate.
     - 2019 single-window probes: 1.3–9×. Some P0-state hard windows stay bound-limited (§3.1, root-after-cuts
       0.21–0.26 %).
     - The paired rolling gate (§7) bounds every window's objective delta.
   - **Status: landed as uc-1.8** (UC-DESK ruling 2026-10-15; §7).
2. **Warm-start repair** (§3.2): makes the carried incumbent feasible, but not useful as built. It is recorded as a
   **separate open item** (UC-DESK): `warm_feasible = 0` in 365/365 windows at uc-1.5 and since. Not fixed here.
3. **Not proposed:** a looser gap or time limit, or any change to the gate, `mlf` or the demand source (each is the
   model).

## 6. Not done

- No ScenarioConfig default moved (`uc_solver_preset` stays `"lean"`; its composition is the engine's).
- No full-year rolling run.
- The 2019 bound-side residual (§3.1) is open. Branching priority or cut-family work would be solver-path work for a
  later lane.
