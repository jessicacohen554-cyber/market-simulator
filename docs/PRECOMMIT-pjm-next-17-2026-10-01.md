# PRECOMMIT — PJM-NEXT-17: arm C (`cc_mustrun_conduct_window`)

**Written before any solve.** Zero-LP evidence: `docs/FINDING-pjm-next-17-coal-response-and-cc-conduct-window-2026-10-01.md` §2.

**Owner rulings (2026-10-01, decision cards):**
- *"Design + build"*.
- After the zero-LP sizing: *"Build + solve anyway"*.

**Keeper / control:** `2026-09-30-pjm-next16-ovec` (bundle `pjmnext16_A_span`, solved at `6d4c7749`). The control is its committed bundle plus G-DRIFT (§4). There are no control solves (rule 29(b)).

## 1. Arm

| arm | out-dir | recipe | what it tests |
|---|---|---|---|
| **C** | `pjmnext17_C_<y>` | keeper recipe at the pinned SHA + `--set cc_mustrun_conduct_window=true` | Same `cc_mustrun_per_plant` window size, level and membership. Hours are ranked by each CC_REGULAR plant's own leave-one-year-out CAMPD month × hour-of-day online probability, ties broken by system load. |

- One shard per year, 2019–2025: 7 shards (rule 36).
- C − keeper isolates the flag, because G-DRIFT is all-INERT (§4).

## 2. Predictions (fixed now)

**Zero-LP floor delta** (`fleet_only` rebuild, `scripts/probes/_pjmnext17_conduct_fleet_delta.py`; filled before launch in §2a):
- only `MECH_CC_MUSTRUN_PER_PLANT` rows move;
- floored hours per plant are unchanged;
- floor MWh in metered-offline hours falls in every year.

**Census upper bound** (`_pjmnext17_cc_conduct_window.py`): committed-MW floor in metered-offline hours.

| TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| keeper | 23.33 | 18.47 | 25.54 | 24.07 | 22.58 | 18.12 | 21.82 |
| C | 21.88 | 16.88 | 25.35 | 22.66 | 19.96 | 16.12 | 19.42 |

**Solved:**
- **C1 CC_REGULAR:** |Δ| ≤ 2.0 TWh in every year, sign not predicted. The floor moves into hours the plant's own conduct says it runs, where it binds less often. No C1 status flip is predicted. 2023 (+8.48 vs ±8.00) can flip either way on a move of this size, and a flip there is reported, not claimed.
- **CC model-on / real-off energy** (NEXT-16 census, `_pjmnext16_cc_loading.py` on the arm payload): falls by ≤ 3.0 TWh in every year (the ON-cell ceiling, FINDING §2).
- **D-4 `cc_mustrun_per_plant` per-unit conduct rider:** failing plant-years do not increase (keeper 19 / 0.23 TWh).
- **COAL_BIT, CT_PEAKER, C3a/b/c:** |Δ C1| ≤ 1.5 TWh; C3a within ±1 pt.

## 3. Decision rule (fixed now; the owner rules on promotion, rule 31)

- C is a keeper candidate **on structure** (rule 17) only if both hold:
  - the D-4 rider does not worsen;
  - floored MWh in metered-offline hours falls in every year.
- Gate regressions are reported at full magnitude. Per the owner, a structural gain with gate regressions "may still be a keeper".
- C is **refused** if the D-4 rider worsens, or if any non-CC mechanism row moves in the fleet build. The latter would be a wiring defect.
- Nothing is swept. The cell grain was chosen by held-out conduct log-loss before this document.

## 4. G-DRIFT (rule 29(b)), keeper pin `6d4c7749` → this branch

**Base.** `6d4c7749` is no longer an object in the repository: the NEXT-16 branch was rebased before merge. Its rebased equivalent is `2f4af3b07`, which carries the same lane commits (OVEC join and bridge, compose scripts). The audit is `git diff 2f4af3b07 HEAD` over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/replay_keeper.py`, `scripts/lib`, `data/raw/_validation-source`, `data/raw/reference` and `thermal_tranches_PJM.csv`.

**Every hunk not from this lane is INERT for the PJM keeper recipe:**

| file(s) | change | why inert |
|---|---|---|
| `fuel/dual_fuel.py`, `fuel/resolve.py`, `fuel/__init__.py`, `run_calibration.py` (oil burn), `constants.py`, `paths.py`, `solve_surface_declared.py` (Part 75 rows) | soco-96 `dual_fuel_measured_oil_burn` | default off and absent from the keeper recipe; the applier returns `None` and the dual-fuel call is unchanged |
| `fleet/eia860.py`, `fleet/assembly.py`, `run_calibration.py` (kwarg rename), `constants.py` (removed CC floor) | NWPP-NEXT-14 `cc_subfloor_eia923_heat_rates` → `eia923_cc_family_heat_rates` | the keeper has `cc_subfloor_eia923_heat_rates=False`; the successor is default off |
| `fleet/campd_bins.py` (fuel-split selector) | NWPP-NEXT-14 per-unit fuel-split tag | only under `campd_per_unit_attribution` + `campd_unit_fuel_split`, both off in the keeper |
| `outages.py` `_CC_SITE_SIMPLE_CYCLE_UNITS`, `reference/master-plant-registry.csv`, `custom-bin-assignments.csv` | R-ERCOT-20 GT routing | ERCOT facilities only (3469, 7900, 56350) |
| `run_calibration.py` / `runner.py` / `pipeline/commitment.py` (PJM bridge prep, `preserve_absorption`) | PJM-NEXT-16 arm B | `pjm_gas_commitment_bridge=False` in the keeper; the prep returns `None` |
| `solve_surface_declared.py` `ISO_BA_JOINS` | declared line drops the PJM pre-arm hash | ledger declaration only; the OVEC row value the keeper solved on is unchanged |

**This lane's own hunks** (`scenarios.py`, `fleet/arrays.py`, `fleet/campd_bins.py::cc_conduct_profile`, `fleet/__init__.py`, the new artifact) are LIVE only under `cc_mustrun_conduct_window=True`. The unit test `test_default_off_never_reads_the_profile` shows the profile is not even read when off.

**Conclusion.** Form 4 is valid; the keeper's committed bundle is the control. Rule 36(d) warm-start knobs are default off, as at the keeper's solve.

## 5. Execution

- 7 shards at the pinned SHA, `permission_mode auto`, `clone_depth 1`, `blob_limit_kb 2048`. Each runs `replay_keeper.py results/calibration/pjmnext16_A_span --years <y> --out-dir results/calibration/pjmnext17_C_<y> --set cc_mustrun_conduct_window=true`.
- Hard stops:
  - `git rev-parse HEAD` must equal the pin;
  - the leg's `run_config_<y>.json` must show `cc_mustrun_conduct_window: true` and `cc_mustrun_per_plant: true`;
  - the solve log must show `cc_mustrun_conduct_window ARMED (PJM, excluded year <y>)`;
  - annual net `import` < −5 TWh.
- Each shard pushes its full bundle (including `dispatch/<y>_P1.parquet` and `hourly/unit_hourly_<y>.parquet`) via `.gitignore` negation plus a plain `git add` (rule 34).
- The parent composes, rebuilds the bench, attests, registers (`--no-prune`), scores, and asks the owner about promotion.
