# PRECOMMIT — SPP-98: CEMS→EIA split-plant remap rows for SPP (Stall ← Arsenal Hill), benchmark adoption, zero LP

**Lane** SPP-98 (owner decision card "Crosswalk repair (Rec.)", 2026-09-28) · keeper
`2026-09-28-spp-94-curtail-rows` (`spp94_arm_span`) · written **before** the rows are added or the benchmark rebuilt.

## 1. Defect (rule 14 `[R-ACCURATE]`, rule 23 trigger = attribution defect, never a residual)

SWEPCO's J Lamar Stall CC (EIA 56565, 511 MW, 2010) files its two combustion turbines in CEMS under the
**Arsenal Hill** facility ORIS 1416 (units `CTG-6A` / `CTG-6B`). EIA-860 plant 1416 is a single 125 MW steam unit
(`5A`). The official EPA CAMD–EIA Power Sector Crosswalk (`data/raw/reference/camd-eia-crosswalk`, intaken by miso-277)
maps both turbines to 56565.

The keeper builds its benchmark by summing CEMS by facility. The consequences:

| where | effect |
|---|---|
| the CAMPD view (bench `campd` / `c_ann`) | Arsenal Hill ST_GAS reads 1.69 / 2.26 / 1.91 / 2.10 / 2.46 / 2.30 / 2.33 TWh (2019–25) on 125 MW, i.e. up to 225 % CF. Stall has no CEMS series. |
| the **scored C1** (`_backfill_eia923_with_campd`) | In 2020, 2021 and 2025, Arsenal Hill's EIA-923 falls below the backfill threshold, so its CEMS net (which is Stall's) is booked to ST_GAS **while Stall is already counted as CC through its own 923**. That is a double count of about 1.9–2.3 TWh. |
| derived artifacts | `thermal_tranches_SPP.csv` row 1416 reads a 150 % median CF. Stall has no measured outage windows. |

## 2. The fix is the existing mechanism (rule 19 `[R-ONE-MECH]`)

`market_sim.data.campd.CAMPD_UNIT_PLANT_REMAP` already carries these cases for CAISO (Alamitos, Huntington Beach,
El Segundo) and NYISO (Astoria II, including the same 150 %-CF tranche symptom). Rows are added from the EPA crosswalk
only, and every target EIA plant is verified to be in SPP's model fleet:

| CEMS (facility, unit) | EIA plant | CEMS TWh/yr 2019–25 |
|---|---|---|
| (1416, CTG-6A), (1416, CTG-6B) | 56565 J Lamar Stall (CC_REGULAR 511 MW) | 1.62–2.28 |
| (3006, 7), (3006, 8) | 55655 WFEC GenCo (CT_PEAKER 90 MW) | 0.06–0.15 |
| (762, 3), (762, 4) | 7546 Ponca City (CC 63 + CT 44 MW); 762 is not in the fleet | 0.01–0.07 |
| (63628, 5A-1 / 5A-2 / 5B-1 / 5B-2) | 2953 Mustang (CT_PEAKER 401 MW) | ≤ 0.02 |

## 3. Scope: benchmark only in this lane

- **Solve path.** The SPP keeper's only runtime reader of the table is the `ct_mustrun_per_plant` CEMS shape, which is
  **off** in the keeper recipe. SPP's committed derived artifacts do not change until they are re-derived. So the
  keeper's dispatch is **byte-identical**, and no shard is needed.
- **Other ISOs.** All ten target and source codes are SPP plants. The LA and OK CEMS rows are also read by MISO's
  benchmark, but none of these codes is in MISO's membership. Expect every other ISO's benchmark to be byte-identical;
  this is verified in §5.
- **Adoption.** `run_calibration_full.rebuild_benchmark(spp94_arm_span)` is the declared zero-LP route. The keeper is
  then re-registered under the same run id and re-scored.
- **Named successor (a solve, not this lane).** Re-derive SPP's CEMS artifacts under the new rows:
  - the tranche row for 1416 from unit 5A only, plus a Stall row;
  - Stall's outage windows;
  - Stall's CC heat rate stays eGRID, because its CEMS is CT-only and the boundary guard refuses it.

## 4. Expectations, fixed now

| # | expectation |
|---|---|
| X1 | Bench `c_ann` for 1416 falls to 5A only (≤ 0.21 TWh every year). 56565 appears with a CEMS series flagged CT-only (923 / CEMS > 1.1). |
| X2 | C1 ST_GAS actual falls by 1.6–2.4 TWh in **2020, 2021, 2025** and moves < 0.1 TWh in 2019 / 2022 / 2023 / 2024. |
| X3 | C1 CC_REGULAR actual moves < 0.15 TWh in every year (Stall's 923 is already in it). |
| X4 | Model dispatch, prices and every price criterion (C3a / C3b / C3c) are byte-identical. |
| X5 | No other ISO's benchmark frame changes (hash check on one MISO keeper year). |

## 5. Recommendation rule, fixed now

**ADOPT** (commit the rows and re-register the keeper) iff X1, X4 and X5 hold. Whatever the rebuilt benchmark does to
any C1 row, the determination is reported at full magnitude and is **not** a criterion (rule 1). A row that flips
either way is a scoring correction, not a model change. If X4 or X5 fails, **STOP**, because the table has reach this
PRECOMMIT did not declare.
