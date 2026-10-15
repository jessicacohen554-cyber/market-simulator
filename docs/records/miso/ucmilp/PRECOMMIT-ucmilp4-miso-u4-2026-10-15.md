# PRECOMMIT: UC-4-MISO, arm U4 (uc-1.7: DA-forecast commitment + per-unit `ut_h`/`mlf` + VLR, ST_GAS per-plant floor off)

**Written and pushed BEFORE any shard.** Every reading, bar, kill and budget is fixed here. Nothing is chosen from results.

- **Charter:** UC-DESK r14 (`session_01WX9W5tgYMre3Z134LZoGF6`), `docs/uc-milp-program-plan-2026-10.md` §11 r14, §12 row
  UC-4-MISO (PR #7265, `ca90d2e8`). Lane branch `claude/ucmilp-4-miso`.
- **Predecessors:** `RESULT-ucmilp3-miso-ab-2026-10-14.md` (UC-3: arm A R; arm B supports the un-stack, 2019–22) and
  `RESULT-ucmiso-vlr-2026-10-15.md` (arm V: R by kill #3, C4 gas 2021, a UC-stage flip; 2022–25 a memory coverage gap).
- **Pin:** engine uc-1.7 `7dbfe20fc63a4a16e37640c2d587b93a7fdf3365` (every shard's `source_revision` and HEAD).

## 1. Control and the one arm

- **Control** = the keeper's committed bundle `results/calibration/closeout_miso_nuc_span` (rule 29(b): no control solve).
- **Arm U4** = UC-3 arm B + every mechanism landed since that MISO admits:

  `replay_keeper.py results/calibration/closeout_miso_nuc_span --years <y>`
  `--set unit_commitment_milp=true --set st_gas_mustrun_per_plant=false --set vlr_pocket_commitment=true`
  `--set 'uc_commitment_demand_source="da_forecast"'`

| mechanism | how it enters U4 | source |
|---|---|---|
| MILP UC (MECH 28) | `unit_commitment_milp=true`; every other `uc_*` at its declared default | GATESPEC §5 |
| DA-forecast commitment demand | `uc_commitment_demand_source="da_forecast"`: windows commit on MISO's EIA-930 DF; P1 clears on actual (rule 4) | r13 ruling 1, #7260 |
| per-unit `ut_h` / `mlf` | automatic under the UC: `uc-params` epochs 2026-10-15a/b (`requires=unit_commitment_milp`) | r13 ruling 2, #7262/#7264 |
| reserve co-opt + u-gate | as the keeper defines it per year (co-opt every year; 2023–25 add `miso_measured_reserve_requirements` and `miso_reserve_online_gated`); the uc-1.6 u-gate rides on it | keeper recipe, #7253 |
| VLR pocket commitment | `vlr_pocket_commitment=true`, 4 sets (Amite South A, DSG B, Western F, WOTAB D+E; n_req 1/1/1/2) | r13 ruling 4, #7263 |
| ST_GAS per-plant floor | **off** (`st_gas_mustrun_per_plant=false`). Rule 19: VLR replaces it; the config refuses both together | UC-3 decision 6 |

- **Not admitted:** `spp_spinning_reserve_share` (SPP-only).
- **Known fleet gap (reported, not repaired):** Nelson 4 (EIA-860 operable, 592 MW NG steam) is absent from the fleet, so MTEP15
  group C (WOTAB:C) is unmatched and builds no row.
- **Recipe gate per leg:** every field the keeper's `run_config_<y>.json` records is equal, except `unit_commitment_milp`, the
  `uc_*` defaults, `st_gas_mustrun_per_plant=false`, `vlr_pocket_commitment=true`, `uc_commitment_demand_source="da_forecast"`,
  and default-off fields the keeper predates. Any other difference is a recipe break; that leg is not composed.

## 2. Zero-LP phase 0 (computed before this PRECOMMIT)

**2.1 DA-forecast increment.** MISO EIA-930 `Demand forecast − Demand`, the same QA as `commitment_demand.qa_forecast_error`
(`data/raw/eia-930-hourly/MISO hourly.parquet`, blob `c9092a02`), before the `td_loss_factor` gross-up:

| year | mean MW | top-100 load hours, median MW | p95 MW | TWh | QA-dropped h |
|---|---|---|---|---|---|
| 2019 | +2,313 | +2,858 | +4,893 | +20.3 | 6 |
| 2020 | +1,962 | +4,835 | +5,705 | +17.2 | 24 |
| 2021 | +1,316 | +3,516 | +4,629 | +11.5 | 26 |
| 2022 | +1,961 | +4,085 | +5,315 | +17.2 | 3 |
| 2023 | +2,083 | +5,452 | +4,972 | +18.3 | 0 |
| 2024 | +1,593 | +1,163 | +4,493 | +14.0 | 48 |
| 2025 | +1,471 | +1,666 | +4,077 | +12.9 | 1 |

The forecast exists every year (no armed source can no-op). The bias is positive and large at peak in 2020–23. This matches the
UC-DIAG cause-2 reading. Each leg's `engine.commitment_demand` must show `basis = "eia930_da_forecast"` and these QA-dropped
counts; the mean is the column above × (1 + `td_loss_factor`).

**2.2 G-DRIFT `3a55fa75` (arm V pin) → `7dbfe20f`** (4 commits: #7264, #7261, #7259 records, #7260). `git diff --stat` over
`src/ scripts/ configs/ data/dictionary/schema`, the control bundle and `keepers/MISO.json`: 21 files, none in the control bundle
or keeper shard.

| hunk | files | control (UC off) | U4 |
|---|---|---|---|
| uc-1.7 commitment demand | `data/commitment_demand.py`, `pipeline/uc.py`, `scenarios.py`, `constants.py`, `load-forecast-error` intake | INERT (default `actual`; refused without UC) | **LIVE** (the new delta) |
| `load_zone_weights` extracted from `load_demand` | `data/eia930/demand.py` | INERT (pure refactor: same weights, same call order) | same weights reused for the increment |
| per-unit `mlf`, epoch 2026-10-15b | `scripts/lib/uc_params`, `solve_surface.py`, `cache.py`, schema | INERT (`requires=unit_commitment_milp`) | **LIVE** |
| SPP spinning share; `reserve_synchronized`; `synchronized_reserve_overrides` | `reserves/spec.py` (SPP design), `lp/model.py`, `pipeline/solve.py`, `pipeline/uc.py` | INERT (default off, SPP-only) | INERT (MISO carries no synchronized class; overrides return `{}`) |

Earlier G-DRIFT links (keeper → `2dd69d5a` → `3a55fa75`) are in the UC-3 and VLR PRECOMMITs; all are UC-path only. **The control
stays the committed keeper bundle.** Nothing LIVE touches the control.

**2.3 Recipe confirmed zero-LP.** `parse --set` (JSON) gives `uc_commitment_demand_source = "da_forecast"`.
`ScenarioConfig` accepts the U4 set and refuses VLR with the per-plant floor (`scenarios.py:24763`).

## 3. Readings, fixed ex ante

Comparators:
- control (keeper) for every gate;
- **prior UC arm** for targets: arm V (uc-1.6, 2019–21) and arm B (uc-1.5, 2022).
- 2023–25 have no prior floor-off UC leg, so the targets there read vs control only.

**3.1 Binding.**

| id | reading | pass bar |
|---|---|---|
| U-1 | P1 unserved, every year | ≤ keeper + 500 MWh (2024 ≤ 8,856.9; other years ≤ 500) |
| U-2 | VLR set on-share (Σu ≥ 1) vs CEMS, DSG / WOTAB / Western | within ±0.15 of CEMS in every solved year (VLR Addendum 0 estimator) |
| U-3 | D-4 rider on the VLR rows (VLR Addendum 0) | 0 FAIL in DSG / WOTAB / Western; Amite South declared expected, reported |
| U-4 | C8 ST_GAS forced share (MECH 28 + VLR) | ≤ the rubric cap every year |
| U-5 | engine checks per leg | `engine.version = "uc-1.7"`; `fields.uc_commitment_demand_source = "da_forecast"`; `commitment_demand.basis = "eia930_da_forecast"`; `fields.vlr_pocket_commitment = true`; the 4 VLR sets as in §1, `unmatched_groups = ["WOTAB:C"]`; every window `pocket_rows > 0`, `pocket_sets_skipped = 0`. A failure is a recipe break; the leg is not composed |

**3.2 Targets** (sign and bar; bar = half the distance to the gate band, the close-out convention):

| id | reading | comparator | bar |
|---|---|---|---|
| T-1 | C1 CC_REGULAR (model − EIA-923) | prior UC arm: 2021 −10.10 (V), 2022 −9.44 (B); band ±8 TWh | 2021 ≥ −9.05, 2022 ≥ −8.72 TWh |
| T-2 | C3a mean LMP vs RT, model-high years | prior UC arm: 2019 +9.1 %, 2020 +13.8 % (V); band ±10 % | 2020 ≤ +11.9 %; 2019 stays ≤ +10 % |
| T-3 | C4 gas 2021 NRMSE | V 0.308; band 0.30 | ≤ 0.30 (removes the shared UC-stage flip) |

**3.3 Reported, not binding** (charter):
- **Starts ÷ CEMS** per class and year: CC_REGULAR, ST_GAS (all), ST_GAS pocket sets (the VLR V-3 reading; open min-run / rotation
  item, not a bar), coal. Prior: CC 0.30–0.45× (UC-3), pocket ST_GAS 0.15–1.12× (V).
- C1 ST_GAS vs keeper and vs EIA-923. This is a rule-19 replacement, so it is reported only (UC-3 Addendum-0 convention).
- C1 by class, C3b, C3c magnitude (> $200 h vs RT), price by load band.
- **Uplift:** `uc_uplift` total and pocket-plant make-whole, and the share of energy cost (GATESPEC sanity 2 %).
- `commitment_demand` increment row per leg; integer set size; time-limit hits; wall ÷ (P0 + P1); memory peak.
- Online CC capacity at the top-100 load hours, U4 vs control (the DA-forecast mechanism's own reading).

## 4. Kills (GATESPEC §5; any ⇒ record and stop, no re-tune)

1. An infeasible window or "no incumbent" hard stop (an engine defect, routed to UC-DESK).
2. The schedule hash differs across two completed runs of one recipe-year.
3. **A control flip:** PASS → FAIL vs the keeper on any solved year, on:
   - C1 (every class except ST_GAS);
   - C3a, C3b, C4 (gas, coal);
   - C8.
   C3c CAVEAT → FAIL rows from the unattested probe span are the known artefact and are read on magnitude (UC-2 §3).
4. U-1 breached in any year.

**A kill stops the verdict, not the evidence.** Legs already launched finish and are composed and scored zero-LP.

**Declared ex ante:** C4 gas 2021 flipped in arms A, B and V (0.310 / 0.306 / 0.308). If DA-forecast commitment does not move it
≤ 0.30, kill #3 fires again on that cell, and the verdict is R by the rule as written.

**No sweeps.** No `uc_*`, `vlr_*` or band value is touched (rule 1). No relaunch with a changed setting.

## 5. Verdict → matrix

Nothing is registered or promoted (E13); scoring uses a local probe registration that is never committed.
- **K candidate:** no kill, U-1…U-5 pass, T-1 and T-3 met, T-2 sign right. This is reported to UC-DESK; the lane never promotes.
- **R:** a kill fires, or U-2 / U-3 / U-4 fail, or a target moves the wrong way past its comparator.
- **I:** no kill, nothing wrong-signed, |Δ| below every target bar.
- **Mixed:** worst row, stated row by row. **Partial coverage** is stated with the verdict.

Matrix (`mechanism-matrix/MISO.js`): the `uc_commitment_demand_source` cell, citing the RESULT. `unit_commitment_milp` and
`vlr_pocket_commitment` are re-cited with the U4 evidence.

## 6. Solve plan (rules 16, 32–36)

- **7 shards**, one per year 2019–2025.
  - Lane `ucmilp4-miso-u4`; branches `claude/ucmilp4-miso-u4-<y>`; out-dirs `results/calibration/ucmilp4_miso_u4_<y>`.
  - Prompts: `shard-prompts-ucmilp4-miso.txt` (`scripts/shard_prompt.py` + lane addendum).
  - **Prompt defect, worked around in text:** `shard_prompt.py` echoes a JSON string `--set` unquoted, so bash strips the quotes
    and `replay_keeper`'s `json.loads` would exit. The prompts single-quote that one argument. The script is not edited here
    (reported to UC-DESK).
- `create_session`: `source_revision = 7dbfe20fc63a4a16e37640c2d587b93a7fdf3365`, model `claude-opus-5-5`, tag
  `ucmilp:UC-4-MISO-shard`. Launched **serially, ~5 min apart**.
- **Memory gate:** ceiling + swap ≥ 22.4 GiB, or the shard stops before any data step.
  - A gate-stopped year gets ≤ 4 relaunches, ~30 min apart.
  - After that it is a coverage gap, with the attempt log in the RESULT.
- **Budgets:** 180 min (2019–21, 2023–25), 720 min (2022), the UC-3 / VLR budgets.
- **Push:** the full bundle (rule 34). Files > 100 MB are split with a sha256 manifest.
- **On each report:** fetch the branch; check `git ls-tree -r <sha> -- <out-dir>` is non-empty; check out and verify:
  - `dispatch/<y>_P1.parquet` (reassembled if split);
  - `uc_schedule`, `uc_uplift`, `uc_solve_log`, `unit_marginal`;
  - the U-5 engine checks and the §1 recipe gate.

  THEN `archive_session` (rule 33).
- **Compose** with `scripts/probes/_ucmilp_compose_span.py`, then score zero-LP:
  - `calibration_verdict.py --json` on the control and U4;
  - `legitimacy_diagnostics.py` regenerated.
- The RESULT, the slim span and the readings go in a records-only PR. UC-DESK merges it.
