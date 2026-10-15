# PRECOMMIT — UC-4-NYISO: arm U4 (UC-3 arm + every r13/r14 mechanism NYISO admits) at engine uc-1.7, every NYISO backcast year, 2026-10-15

**Written and pushed BEFORE any shard exists.** Lane `UC-4-NYISO` (Opus), branch `claude/ucmilp-4-nyiso` cut from main
`7dbfe20fc63a4a16e37640c2d587b93a7fdf3365` (uc-1.7). Chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`), desk log r14
(PR #7265). Addendum-by-reference to `PRECOMMIT-ucmilp-nyiso-ab-2026-10-10.md` ("UC-2") and
`PRECOMMIT-ucmilp3-nyiso-ab-2026-10-14.md` ("UC-3", incl. Addendum A): every bar, kill and verdict rule there is adopted
**unchanged** except where this file says otherwise. Nothing here was chosen from a result.

## 1. Recipe (exact)

| item | value |
|---|---|
| pin (every shard `source_revision`) | **`7dbfe20fc63a4a16e37640c2d587b93a7fdf3365`** (main, engine uc-1.7). Not this branch: the records here never reach a solve. |
| control | keeper `2026-10-02-w0-nyiso`, bundle `results/calibration/w0_nyiso_span` (rule 29(b): no control solve) |
| base arm | UC-3's only (and so structurally preferred) arm, the one UC-3 Addendum A solved at uc-1.5: `replay_keeper.py results/calibration/w0_nyiso_span --years <y>` + `unit_commitment_milp=true` + the nine bridge OFFs (`nyiso_gas_commitment_bridge=false`, `nyiso_gas_bridge_{da_horizon,min_run,online_hours,plant_exclusions,reserve_duty_exclusions,startup,startup_aware,state_floor_min_run}=false`) |
| **U4 additions** | (a) `uc_commitment_demand_source="da_forecast"` (r13 ruling 1) — the only new `--set`; (b) per-unit `ut_h` and `mlf` (epochs 2026-10-15a/b, #7262/#7264) — data, reached by regenerating `uc-params` at the pin, no field; (c) reserve co-optimization **as the keeper defines it** — `energy_reserve_coopt=true`, `nyiso_dynamic_reserve_requirements`, `nyiso_li_locational_reserve`, `nyiso_hydro_reserve_eligible`, `nyiso_scr_edrp_reserve_eligible` all `true` in the keeper recipe and replayed unchanged; the uc-1.6 u-gate (`model/uc/window.py::reserve_headroom_u_terms`) rides on it with no field |
| not armed | `spp_spinning_reserve_share` (SPP-only), `vlr_pocket_commitment` (MISO data only) — NYISO admits neither; nothing NYISO-specific added |
| `uc_*` | every other `uc_*` field at its declared default (`uc_slim_window=true`, `uc_solver_preset="lean"`, gap 1e-3, W/L 24/12, TL 600 s, `uc_prefixing=false`); none swept |
| kept floors | `reliability_floor` ST_GAS, `chp_steam`, nuclear/hydro — as UC-3 |
| years | 2021, 2022, 2023, 2024, 2025 — every year the keeper carries; one shard per year (rules 16, 34, 36) |

### 1.1 The DA forecast lowers NYISO's commitment demand (zero LP, declared before any shard)

EIA-930 `NYIS hourly` (blob `32ee3062`), `Demand forecast − Demand`, raw BA MW (before the loader's `td_loss_factor` gross-up),
data-QA cut `COMMITMENT_DF_DATA_ERROR_FRACTION` = 0.30 as the engine applies it:

| year | QA-dropped h | mean MW | median at the top-100 load hours MW | share of hours DF < actual |
|---|---|---|---|---|
| 2021 | 0 | −412 | −1,040 | 0.88 |
| 2022 | 0 | −399 | −649 | 0.89 |
| 2023 | 0 | −324 | −598 | 0.84 |
| 2024 | 49 | −431 | −297 | 0.88 |
| 2025 | 48 | −379 | −845 | 0.84 |

NYISO under-forecasts in ~85 % of hours (UC-DIAG cause 2: "NYISO −0.6 GW, would go the wrong way"). **U4 commits against a lower
demand than UC-3 did, by 0.3–1.0 GW at peak.** Declared expectation (not a bar): fewer units committed at peak, so the UC-3 uc-1.5
residual (ST_GAS decommit, imports fill) is not expected to close from this leg; the per-unit `ut_h` (shorter min-up) is expected
to raise starts toward CEMS; the u-gate is expected to be slack or near-slack (UC-DIAG: NYISO 2023 committed headroom 0.93 GW vs
0.655 GW spin). The shard's `uc_solve_log` `commitment_demand` row is the in-model check of this table.

## 2. G-DRIFT vs the keeper (zero LP)

The chain from the keeper's solve stands as recorded: UC-2 §10 (basis `306f2c00 → f2bf73bf`), UC-3 §2 (`f2bf73bf → 580c4fbf`),
UC-3 A.1 (`580c4fbf → 2dd69d5a`) — nothing LIVE for NYISO outside the UC stage, solve surface unmoved, keeper bundle and
`keepers/NYISO.json` byte-identical. Extension `2dd69d5a → 7dbfe20f` (18 commits; 6 non-merge touch `src/`/`scripts/`, 23 files):

| content | files | NYISO classification |
|---|---|---|
| uc-1.6 (#7253): integer members' reserve headroom on `u` | `model/uc/window.py`, `pipeline/uc.py` | **LIVE on the gate-on path only** (NYISO co-opts, so the gate is installed in every window); control INERT |
| UC-DATA-UT (#7262, #7264): `ut_h`/`dt_h`/`mlf` per unit, epochs 2026-10-15a/b | `scripts/lib/uc_params/__init__.py`, `model/uc/params.py` (comment), `results/cache.py` (epoch text), `config/solve_surface.py` (epoch gate `requires unit_commitment_milp`), `scripts/lib/clean_profiles.py` | **LIVE on the gate-on path only**; `uc-params` is read only by the UC stage; control INERT |
| UC-SPP-SPIN (#7261) | `model/reserves/spec.py` (`_spp_design` only; returns the old design unless `spp_spinning_reserve_share`), `model/lp/model.py` (`reserve_synchronized=None` default, no row change), `pipeline/solve.py` (`p1_kwargs_overrides`, inside the UC branch, `{}` unless a synchronized class exists) | **INERT for NYISO** (SPP-only builder; `None`/`{}` defaults) |
| UC-MISO-VLR (#7263) | `model/uc/pocket.py`, `data/vlr_pocket_groups.py`, `scripts/lib/vlr_pocket_groups/*`, `model/uc/diagnose.py`, `window.py` (pocket rows, 0 when off) | **INERT for NYISO** (field off; no NYISO groups) |
| uc-1.7 (#7260): commitment demand | `data/commitment_demand.py` (new), `pipeline/uc.py`, `data/eia930/demand.py` (`load_zone_weights` extracted — the identical code moved into a function, `load_demand` calls it: identity refactor), `eia930/__init__.py` (export) | **LIVE on the gate-on path only** at `"da_forecast"` (the arm); the P1 demand path is an identity refactor → control INERT |
| `scenarios.py`, `constants.py`, `solve_surface_declared.py`, `key_provenance.py` | new fields (registered at their declared defaults), new constants | INERT at default |
| `runner.py`, `replay_keeper.py`, `shard_prompt.py`, `calibration_verdict.py`, `legitimacy_diagnostics.py`, `_ucmilp_compose_span.py`, `results/calibration/w0_nyiso_span/**`, `keepers/NYISO.json` | unchanged (`git diff --stat` empty) | — |
| solve surface | `solve_surface_register.py --diff 2dd69d5a 7dbfe20f`: *"342 -> 345 names; 0 value(s) moved, 3 added, 0 removed … NO VALUE MOVED"* (added: `COMMITMENT_DF_DATA_ERROR_FRACTION`, `COMMITMENT_DF_SEASON_OF_MONTH`, `VLR_GROUP_MIN_COMMITTED_UNITS`) | no ISO's key reached |

No LIVE hunk on the control path → no control solve (rule 29(b)). The U4-vs-control delta is UC-only for 2022–2025 and UC + the UC-2
§9 `59490433` drift for 2021 (envelope unchanged: |ΔC3a| ≤ 1.1 pt, |ΔC1| ≤ 0.10 TWh per class not attributable).

## 3. Pass bars (fixed ex ante; unchanged from UC-2/UC-3)

| # | bar | gating |
|---|---|---|
| T1 | no PASS → FAIL flip on any year, criterion or class row vs the control (C3c/C6 attestation artefacts named, not counted; C8 read as printed AND without MECH 28, a flip only if both fail, the UC-3 A.1 reading) | yes (kill #3) |
| T2 | 2024 C3a ∈ [−1.8 %, +0.2 %] | yes |
| T3 | C1 CC_REGULAR PASS 2021–2024 | yes |
| ctl | every leg P1 Optimal; **unserved ≤ keeper + 500 MWh** per year (keeper 0 MWh → ≤ 500); no new D-4 FAIL row beyond the named per-unit rider (`reliability_floor × ST_GAS` plant 2480, ≤ 1.3 GWh) | yes |
| W2–W4 | TL hits ≤ 3/yr; uplift ≤ 2 % of energy cost; infeasible windows 0 | yes (W3 alone → "hold: uplift share") |

## 4. Reported (not gating)

- **Starts ÷ CEMS** per year for CC_REGULAR and ST_GAS (UC-3 S2 procedure; CEMS CC 797/727/740/649/804, ST_GAS 181/199/186/162/210),
  with the UC-3 uc-1.5 ratios (CC 0.52–0.62×, ST_GAS 0.35–0.54×) beside them.
- **Uplift** % and $M per year.
- **Commitment demand** row of `uc_solve_log` (mean, top-100 median, min/max increment, QA-dropped hours) vs §1.1.
- **u-gate**: whether the reserve rows bind in the windows (reserve dual / shortfall hours in the window log if present, else P1).
- **`ut_h`/`mlf` census** of NYISO's integer clusters at the pin (from the stage's census line) vs the plant-basis values UC-3 used.
- **U6: uc-1.5 (UC-3 A) → U4 per year**: price, C3a, CC_REGULAR / ST_GAS / imports TWh, uplift — from the slim span on main
  (`docs/records/nyiso/ucmilp/data/ucmilp35_nyiso_span/`), zero LP.
- T4/T5, S1, S4, S5, U1, U4 (price by sign and hour class) as UC-3; wall rows (GATESPEC §6.1) per year.

## 5. Kills (GATESPEC §5; any ⇒ record and stop, no re-tune)

1. An infeasible window / no incumbent / UC exception → that leg stops and reports verbatim; routed to UC-DESK; no `src/` patch here.
2. Schedule hash differs between two runs of the same recipe (exercised only if a relaunched leg and its predecessor both complete).
3. A control flip (T1).

## 6. Verdict rule (unchanged)

**K candidate** iff T1, T2, T3 and ctl met, no kill, every leg Optimal, W2–W4 within bars, **and all five years solved**. **R** on any
kill or T2/T3/ctl breach. **I** iff T1–T3 met and every scored row moves less than scorer precision. Mixed → worst reading decides.
A coverage gap (§7) caps the verdict at "hold: coverage" unless a solved year already gives R. 2021 flips inside the envelope are
"not attributable".

## 7. Execution (rule 32; the parent runs no LP)

- Prompts: `scripts/shard_prompt.py --iso NYISO --all-years --sha 7dbfe20fc63a4a16e37640c2d587b93a7fdf3365 --lane ucmilp4-nyiso
  --bundle results/calibration/w0_nyiso_span` + the ten UC-3 `--set`s + `uc_commitment_demand_source="da_forecast"` (shell-quoted in
  the emitted command so `replay_keeper` receives the JSON string), `--budget 720`, lane addendum appended; committed as
  `shard-prompts-ucmilp4-nyiso.txt`. Branches `claude/ucmilp4-nyiso-<y>`, out-dirs `results/calibration/ucmilp4_nyiso_<y>`.
- Launched serially, ~5 min apart. **Memory gate ≥ 22.4 GiB** (ceiling + swap from the `container preflight:` / `swap:` lines): a
  shard below it stops before the solve and reports; a blocked year gets ≤ 4 relaunches ~30 min apart, then is recorded as a
  coverage gap with the attempt log.
- Parent: fetch, `git ls-tree` non-empty incl. `dispatch/<y>_P1.parquet`, bytes in hand, then archive (rule 33). Compose
  (`_ucmilp_compose_span.py`, scratch copy as in UC-3 §3 if still needed — disclosed), score control and U4 with
  `calibration_verdict` on a local, discarded registration (E13: nothing registered), regenerate `legitimacy_diagnostics.json`.
- Deliver: RESULT + slim span `docs/records/nyiso/ucmilp/data/ucmilp4_nyiso_span/`, NYISO matrix cells `unit_commitment_milp` and
  `uc_commitment_demand_source`, one records-only PR (not merged; UC-DESK merges), report to UC-DESK.

## 8. DO NOT REDO

No `uc_*` value other than the defaults and the one ruled `uc_commitment_demand_source`; no second arm; no control solve; no
registration; no promotion; no tuning of anything (rule 1); no patch to `src/` or `scripts/` (a defect is reported, not repaired).
