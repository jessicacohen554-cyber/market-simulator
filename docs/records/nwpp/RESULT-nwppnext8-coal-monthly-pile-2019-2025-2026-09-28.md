# RESULT — NWPP-NEXT-8: monthly pile grain of the per-yard coal identity, 2019–2025 → KEEPER #15

**Run:** `2026-09-28-nwppnext8-coal-monthly-pile`, bundle `results/calibration/nwppnext8mp_span`.
**PRECOMMIT:** `docs/records/nwpp/PRECOMMIT-nwppnext8-coal-monthly-pile-2019-2025-2026-09-28.md`.
**Control:** keeper #14 `2026-09-27-nwppnext7-coal-take-floor`, compared against its committed bundle (G-DRIFT form 4,
PRECOMMIT §4). All hunks are inert.
**Solved by:** 7 year-isolated shards at pin `e7478536`. The parent ran no LP.
- 2019 was re-launched once: its first shard hit the parent's 100-min budget, with P0 at 43 min.
- Every leg passed hard stops 3 and 5, checked by the parent. The only config differences from keeper #14 are the arm
  key plus the G-DRIFT-audited default-valued fields.

**Status: PROMOTED** to NWPP keeper #15 on the owner's standing structure ruling.
- Keeper #14 was pruned (rule 35).
- `audit_keepers --iso NWPP` PASSES (E14 package-pin warnings only).

## 0. What was armed (owner decision cards, 2026-09-28)

| Card | Ruling |
|---|---|
| Floor grain | Monthly pile balance (reopens Q2 "annual") |
| Receipts | Flat ratable, C/12 |
| Sides | Both floor and ceiling |

- Each yard row becomes 12 cumulative month-end rows. Month 12 is exactly keeper #14's annual floor and ceiling.
- The soft floor's shortfall is paid once, across the running sums.
- Zero new free parameters; the DOF ledger is unchanged.

## 1. Determination

**NOT-YET on {dispatch_corr}, one record** (was four). C1, C2, C6 and C8 PASS. Price is UNSCORED (rubric v3.8).

**C4 dispatch_corr** (r / NRMSE; floors r ≥ 0.70, NRMSE ≤ 0.30)

| Record | Keeper #14 | Arm | Move |
|---|---|---|---|
| coal 2019 | 0.690 / 0.264 FAIL | **0.733 / 0.223 PASS** | fixed |
| gas 2019 | 0.699 / 0.243 FAIL | **0.750 / 0.224 PASS** | fixed |
| coal 2025 | 0.678 / 0.261 FAIL | **0.721 / 0.242 PASS** | fixed |
| coal 2023 | 0.693 / 0.289 FAIL | 0.695 / 0.283 FAIL | flat (predicted) |
| coal 2020 | 0.708 | 0.762 | improved |
| coal 2021 | 0.747 | 0.792 | improved |
| gas 2021 | 0.757 | 0.854 | improved |
| coal 2022 / 2024 | 0.720 / 0.734 | 0.741 / 0.739 | improved |
| gas 2020 / 2022 / 2023 / 2024 | 0.831 / 0.876 / 0.833 / 0.888 | 0.831 / 0.880 / 0.844 / 0.891 | flat or improved |
| **gas 2025** | 0.864 / 0.193 | **0.854 / 0.196** | **regression**, still PASS |

**C1 fuel-mix** (TWh, model − EIA-923; band ±8; all PASS):

| Class | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| CC_REGULAR | +1.82 → +0.86 | +3.03 → +2.22 | −0.93 → **−2.66** | −4.33 → −4.34 | −2.18 → −2.25 | +4.62 → +4.61 |
| COAL_BIT | −1.02 → −0.59 | −0.38 → +1.04 | +4.39 → +4.59 | +3.96 → +3.95 | +4.70 → +4.73 | −0.55 → −0.64 |
| COAL_PRB | +4.78 → +5.27 | +2.09 → +2.14 | +1.86 → **+3.73** | +5.81 → +5.81 | +4.02 → +4.00 | +3.59 → +3.51 |
| CT_PEAKER | −1.84 → −1.76 | +0.61 → +0.07 | −1.99 → −2.17 | −1.35 → −1.34 | −4.08 → −4.07 | −2.14 → −2.01 |

- 2021 moved furthest. Coal rose 2.0 TWh at the expense of CC_REGULAR, widening both residuals. They stay in band,
  and this is reported at full magnitude.
- 2025 is not gated on the preliminary EIA-923 vintage.

## 2. Mechanism signature

- **Annual coal moves little and the timing moves a lot.** Coal changes by −0.2 to +2.0 TWh per year and shifts from
  Nov–Mar into May–Oct, which is what the phase-0 census predicted (PRECOMMIT §3).
- Unserved energy equals keeper #14 in 2020 and 2021 (46.6 and 34.0 GWh); the arm does not touch the SNV residual.
- **Solve cost rises.** 2019 P0 took 43 min, and the whole 2019 leg ran about 3 h against about 80 min under keeper #14.
  The cause is the ~6.5× larger yard block.

## 3. Routed (for the next lane)

1. **C4 coal 2023 (r 0.695), the last failing record.** The monthly pile footprint in 2023 is ~0.1 TWh, and its winter
   over-burn (Jan–Mar model 5.5 / 4.8 / 4.6 vs EIA-930 4.4 / 3.4 / 3.4 TWh) sits inside the pile. This is NWPP-NEXT-5 Q6:
   what drives 2023 coal? Candidates are net load, hydro, WEIM, and unit outages at Colstrip, Bridger and Centralia.
2. **Colstrip 2020 available energy** (5.86 TWh vs 7.94 generated): an outage/availability input check.
3. **SNV residual shed** (2020: 46.6 GWh; 2021: 34.0).
4. **Internal-link over-flow**: a structural FINDING, and an owner question.
5. **Jim Bridger** has no measured coal tranche row.
6. **Solve time.** A pile-state formulation (12 carry variables per yard instead of cumulative rows) would cut the
   non-zeros. This is a performance lever only.

## 4. Retrievability (rule 34(e))

- The composite bundle (slim files and `hourly/`), its registry sidecar and its run payload land on `main` with this
  lane's PR.
- The 7 per-year legs are gitignored on local disk and do not survive the session.
- Leg SHAs are provenance only (rule 33(d)). Recovering a leg means a re-solve: 35–60 min per year, about 3 h for 2019.

| Year | Leg SHA |
|---|---|
| 2019 | `7d215d0a` |
| 2020 | `796dff0f` |
| 2021 | `4e87567a` |
| 2022 | `670fb1de` |
| 2023 | `0ff686f5` |
| 2024 | `a988f1d1` |
| 2025 | `adcacddb` |

- All 8 shard sessions are archived.
- **Leftover shard branches for the owner to delete** (a session cannot delete refs): `claude/nwppnext8mp-{2019..2025}`.
