# PRECOMMIT — SPP-102: the SPP commitment posture (per-plant relaxed commitment state with min-up / min-down)

**Lane** SPP-102 · control = keeper `2026-09-28-spp-100-chp-scope`, bundle `results/calibration/spp100_arm_span`
(rule 29(b) form 4, no control solve). Written before any shard launched, and merged to `main` before launch.
**Owner ruling:** decision card 2026-09-29, *"Build relaxed-UC engine"*. This was against the lane's own
recommendation, which was to record the 2019–22 rows as limits; that recommendation stands in
`DESIGN-spp-102-cc-commitment-state-2026-09-29.md`.

## 1. What is built

**Field:** `spp_commitment_posture` (default off, SPP-only). It reuses ERCOT's standalone energy-only posture
(`_standalone_posture_pools`: rule 19, one construction). Per CC plant p (pooled **per plant**, the grain on which
SPP's min-load and min-run are measured), U[p,t] is the online capacity, and:

| row | form | source |
|---|---|---|
| headroom | Σ P ≤ U | existing (ERCOT) |
| min-load | Σ P ≥ 0.209·U | SPP CAMPD CC plant-basis min-load (`SPP_GAS_BRIDGE_MIN_LOAD_FRAC`, SPP-44) |
| startup | SU ≥ U[t] − U[t−1], cost $/MW | NREL/SR-5500-55433 class tables (24–64 $/MW on SPP's CCs) |
| **min-up** (new) | Σ_{k<15} SU[t−k] ≤ U[t] + (max Ucap window − Ucap[t]) | SPP CAMPD CC run-length p25 = 15 h (`SPP_GAS_BRIDGE_MIN_RUN_HOURS`) |
| **min-down** (new) | Σ_{k<8} SU[t−k] + U[t−8] ≤ max Ucap[t−8..t] | SPP MMU ASOM gas min-down = 8 h (`SPP_POSTURE_MIN_DOWN_HOURS`, new constant) |

- **Rule 19.** `pipeline.solve.zero_posture_markup` zeroes the P1 amortized startup markup on postured members, so
  the start is charged once, in the LP. The field is mutually exclusive with `spp_gas_commitment_bridge`. It is not a
  floor, so there is no D-2 id.
- **Rule 18.** Eligibility is by pool physics. CTs are exempt by the fast-start gate; CHP and ST are excluded (their
  state is owned by the CHP floors and ST mechanisms).
- **Rule 21.** Zero fitted parameters. Every number is a registered, measured or published constant.
- **Real fleet, zero LP** (2021): 23 per-plant pools, 85 CC_REGULAR members, startup 24.1–63.8 $/MW.
- **Tests:** `tests/iso/spp/test_spp_commitment_posture.py`, 13 cases. Among them: min-down holds a fully committed
  pool through a 6 h valley that a free start would cycle; an outage never makes the time rows infeasible; ERCOT's
  spec is unchanged.

**Arm = keeper + `spp_commitment_posture=true`. Nothing else.**

## 2. Prediction (zero LP, DESIGN §2.3)

A per-plant binary DP with the same physics, run against the keeper's own prices, is an **upper bound** on added
CC: ΔCC ≤ +1.05 / +1.17 / +0.93 / +0.11 / ≈0 / +0.44 / +0.82 TWh for 2019–2025.

The LP differs from that DP in two ways that pull in opposite directions:
- it is a relaxation, so its commitment is weaker than the DP's (fewer TWh);
- the P1 markup zeroing lowers CC offers, so CC is dispatched more in P1 (more TWh).

The net is not predicted to better than sign. The recommendation therefore never rests on it.

## 3. G-DRIFT (rule 29(b), form 4) — keeper `11b72265` → origin/main

Diffed over the rule-29(b) path set, from `11b72265` to `82cfdc3e` (the origin/main this lane merged).

| hunk family | verdict | reason |
|---|---|---|
| NWPP-NEXT-8/9 coal pile and measured receipts (`coal_fuel_inventory.py`, `run_calibration.py`, `scenarios.py`, `forecast_parity_registry.py`, `nwpp_plant_basis_energy.csv`) | INERT | Both fields default off, absent from SPP's recipe, and gated to `COAL_TAKE_FLOOR_ISOS` |
| R-ERCOT-14 SWCAP / shed penalty (`pipeline/spec.py::shed_penalty_voll`, `run_calibration.py`, `ercot_swcap_vintage`) | INERT | Returns `iso_config.voll` unchanged unless ERCOT and armed |
| R-ERCOT-14 plant exit (`ba_membership.py`, `arrays.py`, `constants.ISO_PLANT_EXITS`) | INERT | Registry is `{"ERCOT": {127: …}}`, so SPP's map is empty |
| R-ERCOT-14 Oklaunion dict rows (`coal.py` `COAL_PLANT_SUPPLY[127]`, `eia860.py` `COAL_PLANT_COMMISSION_YEAR[127]`, ERCOT `custom-bin-assignments.csv` / DAM crosswalk) | **INERT, measured** | Plant 127 IS in SPP's 2019/2020 fleet (EIA-860 codes it SWPP), so this family was tested rather than argued. The 2019 and 2020 thermal offer stacks (mc, cap, fuel, pmax, HR, class, code; 791 / 772 rows) were rebuilt with `fleet_only` at HEAD and at the pre-hunk base: **byte-identical**. The supply string reaches must-run only through `coal_{prb,lignite}_mustrun_override`, both `None` for SPP. The plant is absent from 2021+ fleets. |
| SOCO state weights, other-ISO data | INERT | Other ISOs' rows |
| This lane's hunks | LIVE only under `spp_commitment_posture` | Default off; the keeper key is unmoved (cache-key guard) |

All INERT for the keeper recipe, so **the committed keeper is the control**.

## 4. Solve plan (rule 36)

- Seven shards, one per year 2019–2025, pinned to this PRECOMMIT's merge SHA.
- Each shard runs `replay_keeper.py results/calibration/spp100_arm_span --years <Y> --set
  spp_commitment_posture=true`, then `scripts/probes/_spp102_shard_check.py`, and pushes its full bundle (incl.
  `dispatch/<Y>_P1.parquet`) to `claude/spp102-<Y>`.
- The parent solves nothing. It composes with `_rspp_compose.py --side arm --require spp_commitment_posture=true`,
  then regenerates legitimacy diagnostics, attests, registers and scores.

## 5. Expectations (fixed before any solve)

| # | expectation |
|---|---|
| E1 | Shard check PASS on all 7 legs (recipe = keeper + exactly the field; params 0.209 / 15 / 8; leg differs from keeper) |
| E2 | Every year solves Optimal within the 20-minute shard budget |
| E3 | No year's unserved energy rises by more than 500 MWh over the keeper |
| E4 | D-4: no D-4 FAIL row that the keeper does not carry (keeper: 7) |
| E5 | Train tier 2023–25 stays CALIBRATED; no C1/C3a/C3b/C4 status flip in 2023–25 |

**Reported, not gated:** ΔCC_REGULAR and ΔCOAL_PRB per year against §2's bound, and whether any 2019–22 row flips.

## 6. Recommendation rule (fixed)

- **RECOMMEND PROMOTE** iff E1–E5 hold. That is the structural test: real commitment physics on measured
  parameters, with no new defect (rule 1).
- 2019–22 movement is reported at full magnitude and never the basis.
- Otherwise **RECOMMEND AGAINST**, naming the failed item. The owner decides (rule 31).

## 7. Year set (rule 35(b))

SPP's registered years are 2019–2025, all on keeper `2026-09-28-spp-100-chp-scope`. This lane solves all seven.

## 8. Shard check, tested before launch

`scripts/probes/_spp102_shard_check.py` was run on three synthetic 2021 legs built from the keeper:
- the exact recipe with a perturbed price → **PASS**;
- the recipe plus a stray field (`hydro_pondage_bound`) → **FAIL** (RECIPE);
- the exact recipe with a leg identical to the keeper → **FAIL** (ARMED: the posture never reached the solve).

The shard prompt is `docs/handoffs/spp102/shard_prompt_template.txt`.

## Addendum A (2026-09-29, before any number was read) — calibration-path wiring

- **What stopped round 1.** The first seven shards (pinned `e66ef989`) stopped at their ARMED hard stop.
  `scripts/run_calibration.py` assembles its own dispatch kwargs and called only `apply_ercot_commitment_posture`,
  so the posture never reached the backcast solve. The shards correctly refused to push, and no solved number was
  seen.
- **The repair.** Add `apply_spp_commitment_posture` beside the ERCOT call. A source-level regression test
  (`TestCalibrationPathWiring`) now guards it.
- **Nothing else changes.** §1–§7 stand. The shards are relaunched on the repair's merge SHA.
