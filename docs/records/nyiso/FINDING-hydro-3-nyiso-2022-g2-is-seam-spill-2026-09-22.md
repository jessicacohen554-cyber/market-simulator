# FINDING — hydro-3: the arm-B 2022 G2 miss is seam-price SPILL, not the nameplate clip

**Session** hydro-3 (ORCHESTRATOR, rule 32 `[R-SHARD]` (a)). **Date** 2026-09-22.
**Keeper** `2026-09-20-nyiso247-fuel-invariance-disarm`: **UNCHANGED.**
**LP spent: ZERO. No shard launched.** Everything below is phase 0 (a zero-LP budget build plus the
keeper's committed `hourly/class_hourly_<y>.parquet`).

## Verdict

1. **The handoff's premise is FALSIFIED at zero LP.** `docs/RESULT-hydro-1-2026-09-22.md` §2
   attributed arm B's 2022 G2 miss (−0.1229 %, 31.4 GWh) to the RoR flat level being clipped to
   nameplate. It named `hydro_budget_nameplate_aware=true` as the one-shard fix. The clip is real,
   but it is **1 plant-month and ~0.0 GWh in 2022**. The nameplate-aware water-fill
   **re-allocates 0.0 GWh** in 2022, so arming it leaves the 2022 LP essentially identical to the
   one arm B already solved. **Predicted G2 with both flags: ≈ −0.12 %, still FAIL.** The shard was
   not spent to confirm a predictable null.
2. **The miss is SPILL, and the keeper already spills.** The LP's hydro budget row is two-sided
   (`min ≤ Σ_month P ≤ budget`, `model/lp/rows.py::_build_hydro_rows`), so hydro can leave water
   unturbined. The keeper's own spill (EIA-923 budget minus P1 dispatched) tracks arm B's G2 miss
   year for year:

   | year | keeper spill | spill months (GWh) | arm B G2 |
   |---|---:|---|---:|
   | 2022 | **629.0 GWh** (2.4 %) | Mar 19 · Apr 141 · May 172 · Jun 71 · Oct 63 · Nov 162 | **−31.4 GWh FAIL** |
   | 2023 | 246.1 GWh | May 217 · Oct 18 · Nov 7 | −6.4 GWh pass |
   | 2024 | 7.3 GWh | none material | 0.0 pass |
   | 2025 | 3.7 GWh | none material | pass |

3. **The cause is already on the record: nyiso-237.** `docs/RESULT-nyiso237-hydro-negative-price-phase0-2026-09-16.md`
   localized the 2022–23 hydro G2 kills to hours the model **fabricates**. There, Upstate_West is
   priced ≤ $0 for 498 h in 2022 against 21–127 h real, because the Central-East link sits at its
   monthly cap in every hour and curtailed wind sets a −$26 PTC price. Forcing the RoR class flat puts
   more must-take water behind that congested seam, so the reservoir class spills a little more.
   **That is the same object, and its successor is the Central-East seam, which is owner-gated
   (nyiso-224, a topology change).**

## Numbers (zero LP)

Built with `market_sim.data.hydro.build_hydro_fleet("NYISO", y, zones, eia930_monthly=True,
min_flow_floor=True, ror_split=True, nameplate_aware_target=…)`. Classifier at HEAD `7c1fed78`:
`curate_hydro_plant_modes.py --iso NYISO` → **94 run-of-river-class / 70 reservoir-class** (repaired
SHA confirmed).

| year | RoR plants in LP | RoR share of budget | plant-months over nameplate | energy lost to clip | nameplate-aware re-allocation |
|---|---:|---:|---:|---:|---:|
| 2022 | 87 / 156 | 6.9 % | **1** | **~0.0 GWh** | **0.0 GWh** |
| 2023 | 85 / 154 | 7.8 % | 9 | 3.1 GWh | 3.8 GWh (14 plant-months) |
| 2024 | 80 / 147 | 7.2 % | 12 | ~0 GWh | 7.3 GWh (21 plant-months) |

Keeper spill = the same builder's annual budget (with the keeper's `hydro_backfill_year=2024`) minus
the Σ of `klass == "hydro"`, `pass == "P1"` in the keeper's `hourly/class_hourly_<y>.parquet`, binned by
calendar month.

## What this means for promoting `hydro_ror_split`

The mechanism is unchanged by this finding: 12 of 12 shape comparisons toward the measured actual,
and 7.3 % of NYISO hydro energy. What changes is the reading of G2. G2 was pre-registered as *"a
breach is a defect in my code, not a finding"* (`PRECOMMIT-hydro-1` §4). The 2022 breach is neither
a code defect nor a clip. It is the arm interacting with a **known, separately owned price defect**.
Re-writing G2 now to exclude spill hours would be a gate edited after its result (rule 1), so this
session does not do it. The decision goes to the owner.

- **Rule 31 `[R-RETAIN]`:** nothing solved in this session, nothing deleted.
- **Rule 28 `[R-MECH-MATRIX]`:** no mechanism was LP-tested here. The NYISO `hydro_budget_nameplate_aware`
  cell is not re-stamped, because a zero-LP input delta of 0.0 GWh is not a verdict on the mechanism.
