# PRECOMMIT: ERCOT coal per-plant econ cliff split (`coal_perplant_cliff_split`)

Lane `closeout-ERCOT-w3`, 2026-10-04. Written and pushed **before any shard launches**. Evidence: `FINDING-closeout-ercot-w3-phase0-2026-10-04.md` §§1–2.

## 1. Mechanism

ERCOT-144 (`coal_perplant_offer_level`, K) prices each CAMPD coal committed/econ tranche at the capacity-weighted mean of the plant's merged modal SCED TPO curve over the tranche's capability window. When the econ window contains a measured price step, that mean prices the cheap side of the step at a level no owner ever submitted. Fayette's econ tranche is the clearest case: the whole tranche sits at $80.13 in every year, while ~31 % of it was offered at ~$17.

**Arm.** `coal_perplant_cliff_split=True` splits the econ tranche of each curve-registry plant into `_econlo` and `_econhi`. The split point is the curve breakpoint inside the window with the largest price rise (`legacy_bins.coal_curve_cliff_boundary`). The window construction is unchanged, so each side is priced on its own side of the step.

- **Parameters:** zero. No threshold is used; the largest step is always taken, and a flat curve yields two rows at nearly the same price.
- **Inputs:** no new data and no level change. The ERCOT-144 curves are unchanged; only the grain at which they are represented changes.
- **Gates:**
  - Default off.
  - ERCOT only: any other ISO raises (rule 25).
  - Requires `coal_perplant_offer_level` and its resolved curves, otherwise it raises (rule 24).
  - The split is skipped when either side would fall under `MIN_TRANCHE_CAPACITY_MW`, so it cannot drop capacity.
  - `--no-coal-perplant-cliff-split` restores the pre-arm posture.
- **Rules:**
  - Rule 19: it is a refinement of the existing mechanism, not a second one. No other owner prices these rows.
  - Rule 13: it uses the same admitted measured conduct as the keeper.
  - Rule 20: it adds no floor.
  - Rule 21: it adds no DOF ledger entries.

**Zero-LP fleet proof** (2024 rebuild at the solve base, `scripts/lib/bundle_fleet.reconstruct_bundle_fleet`, off vs on). Eight plants split; San Miguel and Twin Oaks have no interior step and are unchanged. No other row's cost moves.

| Plant | Unsplit econ $/MWh | econlo MW @ $ | econhi MW @ $ |
|---|---|---|---|
| Fayette 6179 | 80.13 | 232.7 @ 16.99 | 527.8 @ 107.97 |
| Sandy Creek 56611 | 43.07 | 231.1 @ 33.92 | 96.5 @ 65.00 |
| Limestone 298 | 20.86 | 495.1 @ 19.21 | 429.8 @ 22.76 |
| Spruce 7097 | 18.47 | 630.5 @ 17.74 | 307.2 @ 19.96 |
| Parish 3470 | 21.12 | 109.8 @ 18.55 | 1532.3 @ 21.31 |
| Coleto Creek 6178 | 18.47 | 244.7 @ 18.29 | 35.4 @ 19.69 |
| Oak Grove 6180 | 9.42 | 413.1 @ 9.34 | 305.0 @ 9.52 |
| Martin Lake 6146 | 22.23 | 60.1 @ 22.20 | 1129.7 @ 22.23 |

## 2. Solve plan

- **Solve base.** `claude/closeout-ercot-w3-solvebase` @ `35ef9a1e36aeacae2ed98bbbc79bd659c45bce7c` is the keeper pin `106d6bb737488f4086151907b4dbc4a45ee17306` plus this lane's code commit, and nothing else. G-DRIFT (rule 29b) against the keeper legs is therefore exactly this diff. Every hunk is INERT with the flag off: a new default-off field, a new branch reached only when it is armed, a new helper, and a CLI flag. The only LIVE hunk is the armed branch.
- **Recipe.** `replay_keeper.py results/calibration/closeout_ercot_l1_span --years Y --set coal_perplant_cliff_split=true`. The per-year partition overlay is applied by `enforce_single_recipe_partition`. A zero-LP kwargs check at the solve base reproduces every year's recorded `scenario_config`, apart from the two keys the ERCOT-144 harness strips (as in the keeper's own legs).
- **Years.** 2019, 2020, 2021, 2022, 2024 and 2025 get one shard each (rules 32/34/36).
- **2023 is not solved.** The owner ruled the 2023 carve-out stays as it is (R-6, R-42/R-51, and the 2026-09-07 "leave the 2023 results be"). It is not armed there, so its leg composes byte-for-byte from the keeper. The drift for that year is INERT (flag off), and rule 29b means it earns no solve.

## 3. Pre-fixed readings (keeper → arm)

| Record | Keeper | Predicted |
|---|---|---|
| C1 2019 CC_REGULAR | +9.21 F | +7.4 … +8.4 (**FAIL → PASS** expected at the centre, ≈ +7.8) |
| C1 2019 COAL_PRB | −10.79 F | −8.9 … −9.8 (still FAIL) |
| C1 2020 CC_REGULAR | +10.17 F | +8.5 … +9.4 (still FAIL) |
| C1 2020 COAL_PRB | −11.85 F | −10.0 … −10.9 (still FAIL) |
| Fayette plant TWh vs EIA-923 | −2.2 … −3.9, every year | gap shrinks by ≥ 0.8 TWh in every solved year |
| C3a 2024 | −11.3 % F | −11.4 … −12.3 % (still FAIL, worse) |
| C3a 2025 | −9.2 % P | −9.3 … −10.1 % (**PASS → FAIL risk declared**) |
| C3a 2019 / 2020 | +6.2 / +2.5 % | lower by 0.5–1.7 pt (stays PASS) |
| C3b 2019 / 2020 | 0.216 / 0.208 F | ±0.01 (direction not called: summer over-pricing falls, shoulder under-pricing deepens) |
| C3b 2024 | 0.198 P | 0.195 … 0.205 (**PASS → FAIL risk declared**) |
| C3a/C3b 2021, 2022 | PASS | stay PASS (2022 C3a −8.4 → no worse than −9.3 %) |
| C1 every other class-year | PASS | stay PASS; COAL_PRB 2021/22/24/25 rise by ≤ +2.5 TWh |

Declared C1 PASS→FAIL flips: **none**. Declared price-gate PASS→FAIL risks: **2025 C3a and 2024 C3b**, both because cheaper coal clears at slightly lower prices.

## 4. Kills (any one fails the arm)

- **K1** Any leg's `scenario_config` differs from the keeper's `run_config_<Y>.json` in anything other than `coal_perplant_cliff_split`.
- **K2** VOLL slack or unserved energy changes in any year (2021 keeper: 3,012.6 MWh).
- **K3** The split is inert. Fayette's `_econlo` row is absent from a leg's `unit_marginal`, or Fayette TWh moves by < 0.5 TWh in any year.
- **K4** A C1 PASS → FAIL in any class-year, or C6/C8 governance FAILs in any year.
- **K5** The target misses: the 2019 + 2020 COAL_PRB miss shrinks by < 1.0 TWh combined.
- **K6** A new D-4 legitimacy family (rule 20): no binding-floor mechanism is added, so any new family is a bug.

## 5. Decision rule

If K1–K6 pass, the arm is the more structurally faithful run. Rule 1 says it is recommended for promotion even if a declared price-risk gate flips; the flip is then reported at full size and the root cause named. The lane does not promote. It sends the desk the scored flips and the promotion cost and requests the slot. If a kill fires, the cell is recorded `R` with the reading, and the lane takes the next candidate from FINDING §4.

The matrix row `coal_perplant_cliff_split` is added in this lane's PR: ERCOT `U` until scored, every other shard `.` (ERCOT-scoped, raises elsewhere).
