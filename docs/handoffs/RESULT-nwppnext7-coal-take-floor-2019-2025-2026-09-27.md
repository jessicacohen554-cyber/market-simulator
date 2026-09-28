# RESULT — NWPP-NEXT-7: per-coal-yard coal take floor, 2019–2025 → KEEPER #14

**Run:** `2026-09-27-nwppnext7-coal-take-floor`, bundle `results/calibration/nwppnext7sf_span`.
**PRECOMMIT:** `docs/handoffs/PRECOMMIT-nwppnext7-coal-take-floor-2019-2025-2026-09-27.md`. §9 is the soft-floor
addendum.
**Control:** keeper #13 `2026-09-26-nwppnext6-path76-ctrederive`, compared against its committed bundle (G-DRIFT form
4, PRECOMMIT §3). All hunks are inert.
**Solved by:** 7 year-isolated shards at pin `2162cef5`. The parent ran no LP. All 7 legs passed hard stops 1–8.
**Status: PROMOTED** to NWPP keeper #14 on the owner's standing structure ruling.
- Keeper #13 was pruned (rule 35).
- `audit_keepers --iso NWPP` PASSES (E14 package-pin warnings only).

## 0. What was armed (owner rulings, decision cards 2026-09-27)

- **Q1–Q5.**
  - The `coal_fuel_inventory_plant_grain` yard row gets a LOWER bound. NWPP is added to its ISO gate, and the ceiling
    is armed with it.
  - Annual floor.
  - Estimator B net: `max(0, Y-1 contract tons (C/NC/T) + Dec(Y-1) stock − max month-end stock ≤ Y-1) × hc`.
  - `coal_takeorpay_from_data` and `coal_committed_takeorpay_regulated` are retired (rule 19).
- **Soft-floor ruling** (after the hard floor failed in 4 of 7 years, PRECOMMIT §9):
  - Each yard row carries a shortfall column priced at the yard's own model coal fuel price. This is take-or-pay: an
    unmet take is paid for, never infeasible.
  - Zero free parameters. The DOF ledger is unchanged at 5 entries.

## 1. Determination

**NOT-YET on {dispatch_corr}**, down from {fuelmix, dispatch_corr}. Grade (target) goes 3 → 4 and fails go 2 → 1.
C2, C6 and C8 PASS. Price is UNSCORED (rubric v3.8).

**C1 fuel-mix: FAIL → PASS**

| Row | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| CC_REGULAR, keeper #13 | +7.77 | **+9.94 F** | −0.55 | −7.51 | −0.96 | **+8.30 F** |
| CC_REGULAR, arm | +1.82 | +3.03 | −0.93 | −4.33 | −2.18 | +4.62 |
| COAL_BIT, arm | −1.02 | −0.38 | +4.39 | +3.96 | +4.70 | −0.55 |
| COAL_PRB, arm | +4.78 | +2.09 | +1.86 | +5.81 | +4.02 | +3.59 |
| CT_PEAKER, arm | −1.84 | +0.61 | −1.99 | −1.35 | −4.08 | −2.14 |

TWh, model − EIA-923. Band ±8. 2025 is SKIPPED on the preliminary EIA-923 vintage; there the arm's CC_REGULAR delta
vs the keeper is −2.48 TWh.

**C4 dispatch_corr: FAIL → FAIL** (r / NRMSE)

| Record | Keeper #13 | Arm | Move |
|---|---|---|---|
| gas 2019 | 0.719 / 0.233 PASS | **0.699 / 0.243 FAIL** | regression |
| coal 2019 | 0.701 / 0.222 PASS | **0.690 / 0.264 FAIL** | regression |
| gas 2020 | 0.878 / 0.307 FAIL | 0.831 / 0.191 PASS | fixed |
| coal 2024 | 0.582 / 0.357 FAIL | 0.734 / 0.219 PASS | fixed |
| coal 2023 | 0.673 / 0.286 FAIL | 0.693 / 0.289 FAIL | improved |
| coal 2025 | 0.655 / 0.340 FAIL | 0.678 / 0.261 FAIL | improved |

- The two 2019 records are regressions and are reported at full magnitude.
- The FINDING-nwppnext5 prediction ("C4 flat to −0.1") was too pessimistic in 2023–25 and right in direction for 2019.

## 2. Mechanism signature

- **Unserved energy is identical to keeper #13 in every year**, since the floor does not touch the SNV residual.
- **Shortfall paid (shard reports):** about 1.2 TWh-equivalent in 2019 and about 1.35 TWh in 2020. Coal that could not
  be burned is paid, not forced.
- **Hard-floor failures:** the four failed years were exactly those where a yard's floor clipped to its ceiling or
  capacity. The soft form solved all 7 years, at 34–80 min per year.
- **Coal displaces CC and CT, not hydro.** Hydro is flat to within 0.04 TWh in every year.

## 3. Routed (for the next lane)

1. **C4 2019 gas and coal, which just regressed.** Diagnose zero-LP, by hour and zone, what moved between keeper #13
   and #14.
2. **C4 coal 2023 / 2025** (r 0.693 / 0.678): the NWPP-NEXT-5 Q6 question of what real NWPP coal swings with.
3. **Colstrip 2020 available energy** (5.86 TWh) is below its measured generation (7.94 TWh). This is an
   availability/outage input to check. The floor is capacity-clipped there.
4. **SNV residual shed** (2020: 46.6 GWh; 2021: 34.0).
5. **Internal-link over-flow** (structural FINDING, owner question).
6. **Jim Bridger** has no measured coal tranche row.

## 4. Retrievability (rule 34(e))

- The composite bundle (slim files and `hourly/`), its registry sidecar and its run payload land on `main` with this
  lane's PR.
- The 7 per-year legs are gitignored on local disk and do not survive the session.
- The leg SHAs below are provenance only (rule 33(d)). Recovering any leg means a re-solve at 35–80 min per year.

| Year | Leg SHA |
|---|---|
| 2019 | `8cf809d0` |
| 2020 | `ea5bea41` |
| 2021 | `b0e0899f` |
| 2022 | `258a5b64` |
| 2023 | `159668e1` |
| 2024 | `79032b3f` |
| 2025 | `31e10cde` |

- All shard sessions (7 hard-floor, 7 soft-floor) are archived.
- **Leftover shard branches for the owner to delete** (a session cannot delete refs):
  - `claude/nwppnext7tf-{2019,2021,2025}` (hard floor, superseded);
  - `claude/nwppnext7sf-{2019..2025}`.
