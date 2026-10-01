# RESULT — NWPP-NEXT-5: EIA-860 standby (SB) units admitted by status alone, 2019–2025 → KEEPER #12

**Run:** `2026-09-26-nwppnext5-standby`, bundle `results/calibration/nwppnext5_span`.
**PRECOMMIT:** `docs/handoffs/PRECOMMIT-nwppnext5-standby-admission-2019-2025-2026-09-26.md`.
**Control:** keeper #11 `2026-09-26-nwppnext4-coal-nested`, using its committed bundle (G-DRIFT form 4, PRECOMMIT §2:
every hunk INERT).
**Solved by:** seven year-isolated shards at pin `19f2eace` (rule 36). The parent session ran no LP. The first 2021
shard died at container init ("Setup script failed") and was relaunched.
**Status: PROMOTED** to NWPP keeper #12 on the owner's standing structure ruling.
- Keeper #11 was pruned (rule 35).
- `audit_keepers --iso NWPP` PASSES (E14 package-pin warnings only).

## 1. Determination

- **NOT-YET on {fuelmix, dispatch_corr}**, the same set as keeper #11.
- C2, C6 and C8 PASS.
- Price is UNSCORED (rubric v3.8).

**Flips:** two criteria go FAIL → PASS and **none** go PASS → FAIL.

| Criterion | Keeper #11 → arm |
|---|---|
| C1 CC_REGULAR 2024 | +8.48 FAIL → **+7.67 PASS** |
| C4 coal 2019 | r 0.697 FAIL → **0.701 PASS** |

**Small regressions, reported at full magnitude.** All of these are rows that were already FAIL:

| Row | Keeper #11 → arm |
|---|---|
| C4 gas 2020 NRMSE | 0.303 → 0.310 |
| C4 coal 2023 r | 0.670 → 0.669 |
| C4 coal 2024 r | 0.593 → 0.586 |
| C4 coal 2025 r | 0.668 → 0.664 |
| C1 CC_REGULAR 2020 | +9.54 → +9.40 (still FAIL; improves) |

| Year | Unserved GWh, keeper → arm | CT_PEAKER ΔTWh | CC_REGULAR ΔTWh | Fredonia GWh (EIA-923) | Sun Peak GWh (EIA-923) | C1 CT_PEAKER vs bench |
|---|---|---|---|---|---|---|
| 2019 | 33.4 → 15.4 | +0.40 | −0.20 | 495 (196) | 25 (54) | −0.70 → −0.29 |
| 2020 | 193.7 → 118.8 | +0.58 | −0.14 | 431 (195) | 238 (119) | +3.05 → +3.63 |
| 2021 | 110.1 → 73.8 | +0.10 | — | 68 (386) | 52 (73) | −1.90 → −1.80 |
| 2022 | 73.4 → 37.8 | +0.25 | −0.19 | 247 (273) | 38 (34) | −1.78 → −1.53 |
| 2023 | 21.3 → 9.0 | +0.47 | −0.43 | 533 (967) | 35 (32) | −4.21 → −3.74 |
| 2024 | 45.7 → 27.1 | +1.35 | −0.81 | **1,610** (554) | 57 (36) | −0.04 → +1.31 |
| 2025 | 8.8 → 2.6 | +1.24 | −0.56 | **1,575** (110 partial) | 26 (35) | skipped (preliminary) |

**What the table shows:**
- Unserved energy falls in every year, by 34–70 %.
- In SNV the fall is 41–54 % in the years checked, inside the PRECOMMIT's 31–57 % upper bound for Sun Peak alone.
- Sun Peak's energy is close to EIA-923.

## 2. The regression to carry forward: Fredonia's heat rate

**Fredonia over-runs in 2019, 2020, 2024 and 2025**, reaching a capacity factor of about 0.65 in 2024–25. That is
2.5–2.9× EIA-923.
- This is the cost PRECOMMIT §1.4 stated before the solve.
- Its eGRID plant heat rate (4.918) is an undercount: CAMPD covers only CT3/CT4, while generation covers all four
  units. The fleet builder clamps it to the SPP-49 simple-cycle floor of 9.000, so a 1984 frame CT is priced like an
  efficient peaker.
- The admission itself is correct (rule 14). The operand it exposes is wrong.
- **Routed:** re-deriving `campd_ct_heat_rates_NWPP.csv` so its population follows the admitted fleet. That gives
  Fredonia CT3/CT4's measured loaded rate. Under rule 23 this needs an owner ruling, because the population change
  is not a source-data change.

## 3. Also routed (from PRECOMMIT §1.3)

- **WECC Path 76 "Alturas Project"** (Hilltop–Fort Sage 345 kV, 300 / 300 MW, catalogue p. 69) terminates in SNV and
  has no model link. It needs a terminal-ownership read before it is booked to NW or OR.
- **The served-NEVP-schedule import rigidity.** Southern Nevada's Path 81 SNTI (4,533 / 3,790 MW) enters only as the
  measured interchange schedule. It is the structural candidate for the SNV shed that remains.
- **Lever 1 (coal take obligation):** negative for C4. See `FINDING-nwppnext5-coal-take-obligation-design-2026-09-26.md`,
  owner questions Q1–Q6.

## 4. Retrievability (rule 34(e))

- The composite bundle (slim files and `hourly/`), its registry sidecar and its run payload land on `main` with this
  lane's PR.
- The per-year legs, including `dispatch/`, are gitignored on local disk.
- Leg SHAs are provenance only (rule 33(d)): 2019 `02fbe934`, 2020 `89f6a94a`, 2021 `8b5aa209`, 2022 `2452cf22`,
  2023 `484e3dcd`, 2024 `4bb637b5`, 2025 `9bef6c87`.
- All eight shard sessions are archived.
- **Leftover shard branches for the owner to delete** (a session cannot delete refs): `claude/nwppnext5-{2019..2025}`.
