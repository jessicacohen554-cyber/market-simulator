# RESULT — NWPP-NEXT-4: coal committed band nested on must-run (owner card D3), 2019–2025 → KEEPER #11

**Run:** `2026-09-26-nwppnext4-coal-nested`, bundle `results/calibration/nwppnext4_span`.
**PRECOMMIT:** `docs/handoffs/PRECOMMIT-nwppnext4-coal-nested-2019-2025-2026-09-25.md`.
**Control:** keeper #10 `2026-09-25-nwppnext3-plant-basis`, using its committed bundle (G-DRIFT form 4, PRECOMMIT §4).
**Solved by:** seven year-isolated shards at pin `fac3d392` (rule 36). The parent session ran no LP.
**Status: PROMOTED** to NWPP keeper #11 on the owner's standing structure ruling. The gate regressions are reported
below at full magnitude.
- Keeper #10 was pruned (rule 35).
- `audit_keepers --iso NWPP` PASSES.

## 1. Determination

- **NOT-YET on {fuelmix, dispatch_corr}.** Keeper #10 read NOT-YET on {dispatch_corr} only.
- C2, C6 and C8 PASS.
- Price is UNSCORED (rubric v3.8).

| Year | C4 coal r: keeper → arm | Coal TWh: keeper → arm (EIA-930) | C1 CC_REGULAR vs bench: keeper → arm |
|---|---|---|---|
| 2019 | 0.759 → **0.697 FAIL** | 57.71 → 52.14 (54.55) | +3.16 → +7.61 |
| 2020 | 0.718 → **0.749** | 43.71 → 39.11 (51.94) | +6.84 → **+9.54 FAIL** |
| 2021 | 0.747 → 0.706 | 55.14 → 53.13 (50.14) | −2.38 → pass |
| 2022 | 0.769 → 0.753 | 60.77 → 60.48 (49.41) | −7.36 → pass |
| 2023 | 0.683 → 0.670 (FAIL) | 49.49 → 47.34 (42.27) | −2.57 → pass |
| 2024 | 0.617 → 0.593 (FAIL) | 36.98 → 29.43 (38.30) | +3.90 → **+8.48 FAIL** |
| 2025 | 0.689 → 0.668 (FAIL) | 35.93 → 31.52 (42.26) | skipped (preliminary vintage) |

**C4 gas, 2020:** r 0.864 → 0.877, but NRMSE 0.243 → **0.303, which FAILS** the 0.30 gate.

**Coal volume against the benchmark (C1 rows, all still PASS):**
- 2019 COAL_PRB: +4.84 → −0.08 TWh.
- 2021–2023 coal-long shrinks: 2023 BIT+PRB goes from +9.30 to +7.15 TWh.
- 2024 flips short: COAL_BIT −4.42 TWh.

**Unserved load:** unchanged from keeper #10 in every year (33.4 / 193.7 / 110.1 / 73.4 / 21.3 / 45.7 / 8.8 GWh).

**Hard stops:** every leg passed flags, offer sha `6a13731e…`, `hydro_backfill_year`, P1 demand (exact to 0.001 TWh)
and the arm-live check. Three legs had to be relaunched:
- **2022:** the session was archived before it solved.
- **2025:** it stopped on a non-coal North Valmy row. My check had not scoped to coal.
- **2019:** it stopped on Colstrip's 46.7 MW nested block. My 35 MW threshold assumed the 2020+ two-unit plant. Its
  first relaunch then went idle mid-solve.

## 2. What was predicted, and what it means

- PRECOMMIT §3 predicted, before any solve, that C4 would get worse, from a price-taker bracket of 2024 0.557–0.592.
  The measured 0.593 sits at the top of that bracket.
- The structural claim is confirmed on the plant data. Nesting puts each plant's cheap block on its CAMPD running p10.
- The claim is not a C4 fix. The coal the model loses is exactly the energy real plants produce above their minimum
  load, and in the model that energy now sits in econ bands that rarely clear.
- **Promoted under rule 14.** A measured input read correctly that worsens the fit points to a compensating error
  elsewhere, and the input is not restored. The NWPP-44 precedent applies.

## 3. The successor (the real C4 driver in 2023–25)

**What real PacifiCorp coal does:**
- It runs at about 40 % CF and swings within the day, even though its measured average delivered fuel cost sits above
  the model price.
- EIA-923 shows Hunter at $1.83 → $3.46/MMBtu and Huntington at $2.11 → $3.66 from 2022 to 2024.
- That is conduct under a **period fuel-take obligation**, which acts as an energy budget shaped into the best hours.
  The model has no mechanism for it.

**Constraints on any mechanism:**
- `coal_fuel_inventory` raises outside MISO.
- A budget sized from same-year receipts or burn is rule-13 forbidden.
- Admissible identification must come from prior-year contract data.

This needs an owner design ruling.

## 4. Retrievability (rule 34(e))

- The composite bundle (slim files and `hourly/`), its registry sidecar and its run payload land on `main` with this
  lane's PR.
- The per-year legs, including `dispatch/`, are gitignored on local disk.
- Leg SHAs are provenance only (rule 33(d)): 2019 `6a0ccd0b`, 2020 `375e536b`, 2021 `db23aaeb`, 2022 `9e50d5bb`,
  2023 `bf311536`, 2024 `2aec7bb6`, 2025 `69d99c56`.
- **Leftover shard branches for the owner to delete** (a session cannot delete refs): `claude/nwppnext4-{2019..2025}`.
