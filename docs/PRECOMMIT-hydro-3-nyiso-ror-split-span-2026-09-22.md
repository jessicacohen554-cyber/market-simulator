# PRECOMMIT — hydro-3: `hydro_ror_split` on the full NYISO span, for promotion (2026-09-22)

**Session** hydro-3 (ORCHESTRATOR, rule 32 `[R-SHARD]` (a); zero LP in this container).
**Owner ruling (verbatim reply "1")** to option 1 of
`docs/FINDING-hydro-3-nyiso-2022-g2-is-seam-spill-2026-09-22.md`: *promote `hydro_ror_split` now
under the "structure improves even if a gate regresses" standard, with the 2022 G2 miss reported at
full magnitude and attributed to the Central-East seam (nyiso-237).*

## 1. The arm: one delta

Incumbent keeper `2026-09-20-nyiso247-fuel-invariance-disarm` (bundle
`results/calibration/nyiso247_fuelinv_span`, solved @ `42d750537532c95d335286b63bca881e8a01c76b`)
**plus `hydro_ror_split=true`, and nothing else.** This is arm B of hydro-1, exactly as tested.
`hydro_budget_nameplate_aware` is **not** armed. The finding shows it moves 0.0 GWh in 2022, so it
would add a second delta without closing anything.

Classifier: `scripts/data/curate_hydro_plant_modes.py --iso NYISO` must report **94
run-of-river-class / 70 reservoir-class** in every shard before solving (verified in the parent at
`7c1fed78`).

## 2. G-DRIFT (rule 29 (b)): ALL INERT

Code-level audit of `git diff 42d75053 aaaaeb61 -- src/market_sim scripts/run_calibration*.py
scripts/replay_keeper.py scripts/lib data/raw/_validation-source data/raw/reference`
(26 files, +3518/−216). Every hunk is INERT for this recipe:

- the P0 cache is off unless `MARKET_SIM_P0_CACHE` is set, and nothing sets it;
- P0 slim extraction skips no HiGHS call, and P1 is untouched;
- the `rows.py` bounds refactor is byte-equivalent;
- the P1 basis seed is pinned to `0` by `replay_keeper.pin_determinism_env`;
- every new `ScenarioConfig` field defaults to `False`, is absent from the recipe, and adds no
  default flip;
- the coal, CHP-duty-window, dispatched-bin-denominator, SPP-curtailment and SOCO-CC hunks are
  flag- or ISO-gated;
- the pondage family is unarmed.

The only live change is the classifier repair, which is the arm itself. **Form 4 is valid: the
committed keeper bundle is the control, and no control solve is spent.**

## 3. The solve

Rule 36 `[R-YEAR-ISOLATION]`: **four shards, one per year (2022, 2023, 2024, 2025)**. Each is
pinned to this document's commit SHA, each runs
`scripts/replay_keeper.py results/calibration/nyiso247_fuelinv_span --years <Y> --set
hydro_ror_split=true --out-dir results/calibration/hydro3_nyiso_ror_<Y>`, and each pushes its FULL
bundle (rule 34 (a), `.gitignore` negation plus a plain `git add`). Both warm-start knobs stay OFF.

Rule 35 (b): the year union was read from `frontend/data/backcast/registry/` before any pruning and
is **{2022, 2023, 2024, 2025}**. All four are solved.

## 4. Checks, fixed before any number

- **R0, delta.** Each leg's resolved `scenario_config.hydro_ror_split == true` and
  `hydro_budget_nameplate_aware == false`. Otherwise the leg is refused.
- **R1, reproduction.** Hydro-1's arm-B statistics should reproduce within noise, since the drift
  is all inert: annual hydro, p05, p95 and top-decile per year. A material mismatch is reported
  before any promotion.
- **G1, liveness.** At least 400 MW of `MECH_HYDRO_ROR_FLAT` is stamped in each year.
- **G2.** Annual hydro Δ versus the keeper is reported per year at full magnitude. Per the owner's
  ruling, 2022's expected ≈ −0.12 % breach is a named caveat attributed to seam spill, **not** a
  refusal.
- **P-A.** The ISO tier (2023–2025) determination does not fall from CALIBRATED.
- **P-B.** C1 and C2 do not cross PASS→FAIL in any year.
- **P-C.** C3a, C3b and C3c are reported at full magnitude for every year.

**If P-A or P-B fails, the session stops before the promotion and pruning and reports.** The owner's
ruling covered a G2 caveat, not a determination drop.

## 5. Duties

- Rule 15: register the composed run.
- Rule 35: promote, audit (E1/E13) and prune the outgoing keeper, in this session.
- Rule 28 (b): the NYISO matrix cell for `hydro_ror_split`.
- Rule 33: archive the shards once their bytes are verified in the parent.
- Rule 31: delete nothing that the owner has not ruled on.
