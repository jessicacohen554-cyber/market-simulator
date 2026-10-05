# PRECOMMIT: ERCOT coal warm-boiler committed band (`coal_warm_committed`) on the cliff-split recipe

Lane `closeout-ERCOT-w4`, 2026-10-05. Written and pushed **before any shard launches**. Evidence: `FINDING-closeout-ercot-w4-phase0-2026-10-05.md`.

## 1. Mechanism

In P1, `compute_monthly_markup` adds the $100/MW coal start, amortized over each month's P0 run length, to every coal `_committed` tranche. ERCOT's committed tranches sit on per-plant must-run floors that keep the boiler online (`coal_mustrun_per_plant`, `must_run_pct` 12–55 on every plant). So the committed tranche never pays a cold start, and the markup is not a real cost.

The markup also inverts the measured offer curve. The committed tranche bids above the plant's own econ tranche: Martin Lake $28.55 / $31.71 (2019/2020) against $22.20, and Sandy Creek $47.72 against $33.92. A real SCED TPO curve is monotone non-decreasing.

**Arm.** `coal_warm_committed=true`, the existing warm-boiler exemption (registered under `p1_bidcost_pass`, rule 28(c)).

- **Status elsewhere:** armed on the MISO keeper. ERCOT has never tested it, so it enters ERCOT as `U` (rule 28).
- **Parameters:** zero. No new data, no new floor and no new field.
- **Code:** none. The flag exists at the solve base.
- **Rules:**
  - Rule 18: commitment physics by parameters. The gate is the unit's own `must_run_pct`, not its class.
  - Rule 19: it removes a component from the one P1 markup owner; it does not stack a second mechanism.
  - Rule 13: there is no measured input.
  - Rule 21: no DOF ledger entry.

## 2. Solve plan

- **Solve revision:** `1283e27fe4427157af54157cc67478d7b8601281`, the same as the w3 legs (keeper pin `106d6bb7`, plus the cliff-split code, plus the keeper bundle as recipe). G-DRIFT against the control legs is empty.
- **Control:** the six w3 legs, at the full SHAs in w3 RESULT §1. They are the incumbent probe's bundles, so there are no control solves (rule 29b).
- **Recipe:** `replay_keeper.py results/calibration/closeout_ercot_l1_span --years Y --set coal_perplant_cliff_split=true --set coal_warm_committed=true`.
- **Years:** 2019, 2020, 2021, 2022, 2024 and 2025, one shard each (rules 32/34/36).
- **2023:** not solved. The owner carve-out stands (R-6, R-42/R-51, 2026-09-07), so the keeper leg composes byte-identical.
- **Compose:** `_closeout_ercot_w3_compose_span.py`, pattern with the arm key set extended to the two flags.

## 3. Pre-fixed readings (w3 arm → w4 arm)

The ranges are 0.6–0.9 of the static reach in FINDING §3. The CC_REGULAR ranges assume coal displaces CC_REGULAR for 60–90 % of its added MWh.

| Record | w3 arm | Predicted |
|---|---|---|
| Coal energy 2019 / 2020 | — | +1.6 … +2.3 / +2.2 … +3.3 TWh |
| C1 2019 COAL_PRB | −9.57 F | −7.3 … −8.0 (**FAIL → PASS expected**, centre ≈ −7.6) |
| C1 2020 COAL_PRB | −10.85 F | −7.8 … −8.9 (centre ≈ −8.3; still FAIL at the centre, flip possible) |
| C1 2019 CC_REGULAR | +8.45 F | +6.4 … +7.5 (**FAIL → PASS expected**) |
| C1 2020 CC_REGULAR | +9.60 F | +6.6 … +8.3 (centre ≈ +7.5; **FAIL → PASS expected**) |
| Martin Lake plant TWh | — | rises in every solved year: 2019/2020/2024 by ≥ +0.6 |
| C1 other class-years | PASS | stay PASS. COAL_PRB: 2021 −0.59, 2022 −0.54, 2024 +0.10, 2025 +2.33, each moves by ≤ +1.6. CC_REGULAR: 2022 −4.45 → no worse than −5.5; 2024 −4.93 → no worse than −6.8 |
| C3a 2019 / 2020 | +5.9 / +1.9 % P | lower by 0.3–1.0 pt each; stay PASS |
| C3a 2021 / 2022 | +0.7 / −8.4 % P | 2021 lower by ≤ 0.3; 2022 −8.5 … −8.9 (stays PASS) |
| C3a 2024 | −11.9 % F | −12.2 … −12.9 % (still FAIL, worse) |
| C3a 2025 | −9.9 % P | −10.0 … −10.3 % (**PASS → FAIL risk declared, more likely than not**) |
| C3b 2024 | 0.201 F | 0.201 … 0.206 (still FAIL) |
| C3b 2019 / 2020 | 0.217 / 0.209 F | ±0.01 (direction not called) |
| C3b 2021 / 2022 / 2025 | PASS | stay PASS |

Declared C1 PASS → FAIL flips: **none**. Declared price-gate PASS → FAIL risk: **2025 C3a**. As in w3, cheaper coal clears the 2025 load-weighted price slightly lower, and 2025 C3a sits $0.03 inside its line.

## 4. Kills (any one fails the arm)

- **K1 recipe.** A leg's `scenario_config` differs from the keeper's `run_config_<Y>.json` in anything other than `coal_perplant_cliff_split` and `coal_warm_committed`.
- **K2 shed.** VOLL slack or unserved energy changes in any year against the w3 leg (2021: 3,012.6 MWh).
- **K3 inert.** Martin Lake's `_committed` P1 median mc is more than $0.50 above its base cost in any leg, or coal energy moves by < 0.3 TWh in 2019 or in 2020.
- **K4 C1 / governance.** A C1 PASS → FAIL in any class-year, or a C6/C8 FAIL in any year.
- **K5 target.** The 2019 + 2020 COAL_PRB miss shrinks by < 1.5 TWh combined against the w3 arm.
- **K6 D-4.** A new D-4 legitimacy family. No floor is added, so any new family is a bug.

## 5. Decision rule

- **If K1–K6 pass:** the w4 arm is the more structurally faithful run (rule 1). It is recommended for promotion as cliff split + warm committed, superseding the w3 recommendation, even if 2025 C3a flips. A flip is reported at full size with its root cause.
- **If a kill fires:** the reading is recorded in the ERCOT `p1_bidcost_pass` cell evidence, and the w3 recommendation stands alone.
- **Who decides:** the lane does not promote; the desk takes the owner's ruling.
- **Matrix:** `coal_warm_committed` is a registered sub-scalar of `p1_bidcost_pass` (ERCOT `K` for the pass itself). The probe's verdict lands in that cell's evidence, and no new row is needed.
