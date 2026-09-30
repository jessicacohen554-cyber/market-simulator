# PRECOMMIT — R-ERCOT-19: South merchant over-run (EIA-923 basis) and the 2024/2025 zonal-gas Finals refresh

Date 2026-09-30. Keeper `2026-09-30-r-18-drag-index` (bundle `results/calibration/r_ercot18_span`, 2019–2025, ISO NOT-YET). DATA PROFILE: ercot. Written before any solve. Numbers: `docs/handoffs/r-ercot/r_ercot19_phase0.json`.

## 1. Phase 0 — the South over-run on the EIA-923 basis (zero LP)

Model = the r-18 legs' P1 per-plant dispatch. Actual = EIA-923 net generation, NG rows (`data/raw/eia-923-generation-fuel`). Scope is South merchant gas (CC_REGULAR, CT_PEAKER and ST_GAS; CHP excluded). Two joins were corrected against R-ERCOT-18's read:

- **55545 Hidalgo** (551 MW CC, 2.0–3.0 TWh/yr) has no benchmark-file row. It has no CAMPD data, but its EIA-923 rows are complete.
- **49392**, the Barney Davis steam split child, is folded into 4939: its MWh sit inside 4939's EIA-923 row.

| Year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Model TWh | 13.60 | 10.88 | 11.05 | 13.31 | 13.68 | 12.77 | 13.59 |
| EIA-923 TWh | 11.71 | 10.56 | 10.36 | 11.06 | 11.22 | 11.13 | 11.45 |
| Ratio | 1.16 | 1.03 | 1.07 | 1.20 | 1.22 | 1.15 | 1.19 |

**The CT-only caveat does not change the conclusion.** The totals reproduce R-ERCOT-17/18 (their "actual" was already the EIA-923 basis). Per plant, the excess over 2019–2025 (model − 923, TWh):

| Plant | Excess TWh |
|---|---|
| Nueces Bay 3441 | +4.57 |
| Barney Davis 4939 (+49392) | +3.45 |
| Gregory 55086 | +2.38 |
| Silas Ray 3559 | +1.75 |
| Sam Rayburn 3631 | +1.62 |
| Victoria 3443 | +0.94 |

- **Under-running:** Magic Valley 55123 (−0.79, except 2025) and the two reciprocating-engine plants, Pearsall 3630 (−1.73) and Red Gate 59391 (−1.33).
- **About on:** Hidalgo 55545 (0.99–1.10×).

**It is not South-specific. It is ISO-wide merit compression by heat rate.** Over every ERCOT CC_REGULAR plant with ≥ 0.05 TWh of EIA-923 generation:

| Year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| corr(measured 923 HR, log model/923) | 0.79 | 0.72 | 0.68 | 0.78 | 0.80 | 0.70 | 0.75 |
| model/923, HR ≤ 7.0 | 1.01 | 0.93 | 0.87 | 0.80 | 0.86 | 0.81 | 0.87 |
| model/923, HR > 9.0 | 2.55 | 4.20 | 1.71 | 1.63 | 2.98 | 4.38 | 4.96 |

The South has a concentration of old, small CCs, so the ISO-wide effect shows up there as a zone total.

**Not congestion.** South–Houston P1 price spread is $0 in 99.7 % of 2022 hours.

**The within-South merit order** (fleet-only rebuild of the keeper recipe, 2019/2022/2024):

- The CC `_committed` tranche is priced by `cc_committed_offer_margin` (ERCOT-139): `HR × (fuel − 2.2494) + 10.354`.
- Near the anchor, every CC's committed block therefore bids about the same. In 2024 South the range is **$12.6–13.9/MWh** for model heat rates 7.0–11.0 (implied fuel 1.08–1.52 vs 2.57 delivered).
- The `econ*` ramp keeps heat-rate scaling ($15.6–23.4 at econc00).
- The committed tranche is the largest single tranche for most plants, online 63–97 % of hours.

**Is the flat level real conduct? Measured, 2024–2025 60-Day DAM** (13 matched CC plants per year):

| Test | 2024 | 2025 |
|---|---|---|
| corr(HR, first-segment offer price relative to the hourly fleet median) | +0.19 | −0.16 |
| corr(HR, DAM ON share) | −0.60 | −0.34 |

- Real low-end offers are roughly heat-rate-flat, so the ERCOT-139 level is consistent with conduct *conditional on being online*.
- What does scale with heat rate in reality is **commitment**: inefficient plants are online less.

**Diagnosis.** The LP has no no-load/start coupling, so the below-cost committed block is available in every available hour. The model part-loads inefficient CCs through hours when they are really off, and under-commits efficient ones. This is the R-ERCOT-18 "commitment frequency" signature (model online 63–97 % vs metered 20–67 %, MW-when-on at or below the meter), now shown to be ISO-wide and heat-rate-ordered.

**No zero-DOF lever exists inside the offer fence.**

- A per-plant heat-rate-scaled level would contradict the DAM measurement.
- Offer multipliers are fenced (rule 1(c)).
- The structural answer is hour-eligibility of the committed block by the plant's own measured commitment. That is a new mechanism, so it goes to the owner as a decision card; nothing is built.

## 2. Phase 0 — the rule-23 data update (zonal-gas member rows)

- Re-derived with `scripts/data/derive_ercot_zonal_gas_hub.py --validate` on the published Finals:
  - `EIA923_Schedules_2_3_4_5_M_12_2024_Final.xlsx` (sha256 `c7c4d3d3…f8e395`, from `…/eia923/archive/xls/f923_2024.zip`)
  - `EIA923_Schedules_2_3_4_5_M_12_2025_Final.xlsx` (sha256 `95684212…cfd2c`, from `…/eia923/xls/f923_2025.zip`)
- The pooled `South_Texas_Pooled` rows the keeper reads for South and South_Central **already reproduce the Finals** (2024 0.52, 2025 0.15, OK).
- Updated, because the source changed:

| Row | 2024 | 2025 |
|---|---|---|
| North (+ Northeast proxy) | 0.21 → 0.28 | 0.43 → 0.29 |
| South (unpooled, not read by the keeper) | 0.63 → 0.66 | 0.59 → 0.51 |
| South_Central (unpooled, not read by the keeper) | 0.45 → 0.49 | −0.12 → 0.07 |

- New table sha256 `a6946073a1f4cce3a7a7939dcdc29cc959182f87b2a5012659f18509a470ec26`.
- Fleet-only delta through the real path: pmax, availability and min_gen are byte-identical. Mean gas mc by zone, $/MWh:

| Year | North | Northeast | Houston | South | South_Central | West |
|---|---|---|---|---|---|---|
| 2024 | +0.42 | +0.53 | −0.20 | −0.20 | −0.24 | 0 |
| 2025 | −0.84 | −0.88 | +0.41 | +0.39 | +0.47 | 0 |

- The shift is the mean-zero recentring (lesson from R-17/18). Non-gas mc moves ≤ $0.21 (the gas-keyed coal sigmoid).
- 2019–2023 rows are unchanged, so those years are byte-identical and are not solved.
- **Stated, not fixed:** the frozen `GAS_OFFER_MARGIN_ANCHOR_BY_ZONE` North/Northeast value (2.7178) was derived partly on the old 2024/2025 North rows. Its re-derivation is blocked by the routed non-reproduction item (rule 23), and is not done here.

## 3. Phase 0 — Task 2 and the residual D-4 rows

- **West Waha 2020/2021:** not buildable. The annual basis is not citable, and EIA's NGWU carries no Texas hub (ercot-160/224/265 surveys, re-confirmed by the standing record), so not every row the mechanism reads would be citable. Not started.
- **South CHP shortfall:** largely a basis artifact.
  - The bench compares the model's grid-delivered dispatch with total EIA-923 net.
  - Corpus Christi EC 55206 on the grid-delivered basis (e_ann − btm): 2019 1.29 / 2022 1.36 / 2024 1.64 TWh actual vs model 1.10 / 1.37 / 1.38.
  - The residual gap is 0.0–0.26 TWh. Six South CHP plants the model dispatches (10554, 55313, …) have no bench row.
  - Characterized, not fixed.
- **Coal stay-on:** fenced, untouched.
- **Residual `st_netload_drag` D-4 rows (3452, 3628, 3491):** they need a per-plant diurnal hour-eligibility design. That goes to the owner on the same decision card as §1, because it is the same design family (hour-eligibility by the plant's own measured commitment).

## 4. G-DRIFT (rule 29(b)): keeper legs `0bd29417` → HEAD `b405c49c`

23 solve-path files changed (51 commits). Every hunk is INERT for an ERCOT backcast:

| Change | Why inert |
|---|---|
| PJM-NEXT-13 `pjm_replacement_cost_fuel` (`fuel/basis/pjm*.py`, `fuel/resolve.py`, `run_calibration.py`, PJM reference csvs) | Returns `None` unless the default-off flag is set |
| SPP-104 `spp_ct_lole_efor` (`fleet/arrays.py`, `fleet/ct_lole_efor.py`, `constants.SPP_LOLE_GAS_EFOR_BY_SIZE`, `solve_surface_declared.py`) | Default-off flag; declared at its frozen value |
| NYISO-NEXT-15 `nyiso_import_landing_band` (`lp/rows.py`, `lp/model.py`, `pipeline/kwargs.py`, `run_calibration.py`, `interchange/nyiso.py`) | `iso == "NYISO"` gate, default off; `import_link_band=None` leaves the LP byte-identical |
| R-CAISO-15/16 clock repair (`eia930/demand.py`, `eia930/frames.py`, `run_calibration_full._bundle_caiso_clock_repair`, `constants` comment) | CAISO-only artifact and switch; benchmark rebuild returns False for non-CAISO |
| `scripts/lib/forecast_parity_registry.py` | Declaration only |
| `scenarios.py` | Three new default-off fields |

The keeper's committed legs are the control (form 4). No control solve.

## 5. Arm

- Two shards, one per year (rule 36): 2024 and 2025.
- Each runs `replay_keeper.py results/calibration/r_ercot18_span --years <Y> --out-dir results/calibration/r_ercot19_arm_<Y>` at the pinned SHA, which carries the refreshed table.
- No `--set`: the recipe is the keeper's, unchanged. Only the input file differs.
- Prompts: `docs/handoffs/r-ercot/SHARD-PROMPTS-r-ercot-19.md`.
- 2019–2023 are byte-identical and taken from the keeper's own legs (recomposed).

## 6. Predictions (before solving)

| | 2024 | 2025 |
|---|---|---|
| South merchant TWh | 12.77 → 12.8–13.2 (South gas cheaper) | 13.59 → 13.1–13.5 (South dearer) |
| C3a | −10.7 % → −11.2 to −10.2 % (stays FAIL; NOT-YET unch.) | −9.6 % → −10.3 to −9.1 % |
| LW price | ±0.4 $/MWh | ±0.5 $/MWh |
| C3b | ±0.01 | ±0.01 |
| C8 ST_GAS | ±1.5 pp | ±1.5 pp |
| Slack | unchanged (0) | unchanged (0) |

- **2025 risk, stated.** The North CC cohort is the largest price-setting block, and its mc falls $0.84. The C3a edge (−10 %) is live, so a 2025 CALIBRATED → NOT-YET flip is possible.
- C1 CC_REGULAR / ST_GAS move ≤ 0.3 TWh. Coal classes ≤ 0.1 TWh.

## 7. Decision rule

- **Promote** under the standing instruction ("Is it an improvement? Then promote") if no year's determination flips worse. The basis is rule 23/14 (the source was updated), not the residual.
- **If 2025 flips worse,** put a decision card to the owner and keep every bundle (rule 31). Rule 14 says the accurate input stays; the question is whether to promote now or hold until the price-side root cause is addressed.
- DOF ledger: unchanged (zero added; a data refresh).

---

## ADDENDUM A (written before the arm-B solves): owner ruling and the commitment-eligibility build

**Owner decision card, 2026-09-30.** Asked "Build it?" on §1's diagnosis; the answer, verbatim: **"Build commit eligibility (Recommended)"**. The card offered it as one design used twice: the CC committed block, and the residual `st_netload_drag` D-4 rows.

### A.1 Construction

Two default-off, backcast-only, zero-DOF sub-gates. Both read one frozen artifact: `scripts/data/derive_ercot_prior_year_commitment_profile.py` → `data/raw/_validation-source/ercot_prior_year_commitment_profile.csv`.

- The artifact is each plant's CAMPD online capacity share by month × hour-of-day (`opTime > 0`, unit-weighted by measured max gross load; CC = CT/CC units; ST = the drag derive's unit routing).
- Vintages 2019–2024 are read as Y−1 by 2020–2025.
- 37 of 42 CC_REGULAR plants and 10 drag-covered ST_GAS plants are metered. Unmetered plants are untouched (e.g. Hidalgo 55545 and Silas Ray 3559).

The two sub-gates:

- **`cc_committed_prior_year_commitment_eligibility`**
  - Construction: a sub-gate inside `cc_committed_offer_margin` (rule 19). `mc += q_p(t) × (level − HR×anchor − vom)`, where q = 1 is the keeper and q = 0 is the band's multiplier form.
  - Code: `offer_curves.apply_cc_committed_offer_margin(…, year)`. Only the backcast call site passes `year`.
- **`netload_drag_prior_year_hour_profile`**
  - Construction: a sub-gate inside `netload_drag_floors` (rule 19). Each metered plant's drag rows are multiplied by `q_p / mean q_p`, then rescaled per plant so its **delivered** floor energy equals the pro-rata path's (aggregate-neutral, the ercot-259 discipline).
  - Code: `fleet.floors._reshape_delivered`.

**Build correction, stated.** The first build preserved the *nominal* floor before the clip. The zero-LP delta then showed the 2022 delivered drag rising 6.70 → 8.60 TWh (the floor escaped the lay-up mask's windows), which would have raised forcing. The build was changed to delivered-preservation *before any solve*.

### A.2 Zero-LP delta through the real path

Record: `scripts/probes/_r_ercot19_commit_eligibility_delta.py` → `docs/handoffs/r-ercot/r_ercot19_commit_eligibility_delta.json`.

- **2019:** `mc` and `min_gen` byte-identical (fail-closed). The keeper's 2019 leg is reused; no solve.
- **2020–2025:** pmax, availability, every non-CC-committed `mc` row and every non-drag `min_gen` row are byte-identical (asserted).
- **CC committed bids** rise on 36 of 42 plants:

| Year | Mean rise $/MWh | Max rise $/MWh |
|---|---|---|
| 2020 | +3.35 | 15.6 |
| 2021 | +3.79 | 15.5 |
| 2022 | +3.80 | 14.6 |
| 2023 | +3.12 | 12.4 |
| 2024 | +3.10 | 13.1 |
| 2025 | +2.99 | 13.8 |

- **2022 examples:**

| Plant | Committed bid rise $/MWh |
|---|---|
| Gregory | +8.8 |
| Barney Davis | +6.9 |
| Sam Rayburn | +6.8 |
| Nueces Bay | +5.7 |
| T H Wharton | +14.6 |
| Efficient baseload CCs | +1.0–1.3 |

- **Drag:** delivered floor energy is identical per plant and in total, every year. Only the hours move.

### A.3 Tests and G-DRIFT

- Tests: `tests/unit/data/test_prior_year_commitment_profile.py` (11). The config/data suites show the identical failure set to main (7 base-red).
- G-DRIFT: §4 plus this branch's own code. The only LIVE hunks are the two sub-gates, and they are the arm.

### A.4 Arm B

Six shards (2020–2025) at the pinned SHA. Each runs:

`replay_keeper.py results/calibration/r_ercot18_span --years <Y> --set cc_committed_prior_year_commitment_eligibility=true --set netload_drag_prior_year_hour_profile=true`

- The table is the refreshed hub table, so arm B = keeper + hub refresh + commitment.
- Controls:
  - 2020–2023: the keeper legs (the hub rows are unchanged there).
  - 2024/2025: the arm-A (hub refresh) legs.

### A.5 Predictions (before solving)

| Year | C3a | C8 ST_GAS | Other |
|---|---|---|---|
| 2020 | +5.6 → +6 to +9 % (risk toward +10) | ±2 pp | CC_REGULAR C1 +12.4 → +8 to +11; COAL_PRB −11.6 → −11 to −9.5 |
| 2021 | +4.6 → +5 to +8 % | ±2 pp | |
| 2022 | −8.7 → −8 to −6 % | 30.1 % → 28–31 %; escape expected to hold (D-4 improves) | |
| 2023 | −19.8 → −19 to −17 % | ±2 pp | |
| 2024 | −10.7 → −10 to −8 %; **may flip to CALIBRATED** | ±2 pp | |
| 2025 | −9.6 → −9 to −7 % (off the edge) | ±2 pp | |

Across years:

- South merchant gas falls 5–12 %. The over-run ratio (1.15–1.22) moves toward 1.05–1.12. The heat-rate correlation (0.68–0.80) falls but stays positive, since the econ ramp is untouched.
- C3b ±0.03. Slack unchanged.
- D-4 `st_netload_drag` unit-conduct FAILs 8 → ≤ 4 (the two 2019 rows stay: fail-closed).

**Direction risk.** Dearer CC shoulder bids lift prices. That helps 2022–2025 (negative C3a) and hurts 2020/2021 (positive C3a).

### A.6 Decision rule

- **Promote** under the standing instruction if no year's determination flips worse and the South over-run falls.
- **Decision card, every bundle kept (rule 31),** if any year flips worse.
- DOF ledger: unchanged (zero added).
