# PRE-DECLARATION — UC-0 benefit screen (zero LP): thresholds, ranking rule, selection rule

**Lane:** UC-0 (benefit screen), chartered by UC-DESK r01 (`session_01WX9W5tgYMre3Z134LZoGF6`, 2026-10-03; plan §12). **Session:** `session_013gHAT8qbNZwry6tA92gYNq`. **Model:** Fable.
**Branch:** `claude/ucmilp-0-benefit-screen-tx8t`, fresh off `origin/main` `cd7382f56f03f4ac240b392b2a9ceec0ca777395`.
**Date:** 2026-10-03. **DATA PROFILE:** `code` + the committed keeper bundles; the container arrived with the whole `data/raw` tree checked out (7.0 GB, `git sparse-checkout list` empty), so no `hydrate_data.py` call was made. The subtrees the probe reads are enumerated in §4.
**Pushed BEFORE any M1–M6 number exists.** Graded at full magnitude in `FINDING-uc-milp-benefit-screen-2026-10-03.md`, misses included.

**Preconditions, checked.** D-0 = charter (R1) and D-1 = sign (R2) are in plan §8.1 on both `origin/main` and `origin/claude/ucmilp-desk-r01` (`git show … | grep -n R1` → line 154 on both). Keepers re-read from `frontend/data/backcast/keepers/<ISO>.json` at start:

| ISO | keeper run id | bundle | years carried |
|---|---|---|---|
| ERCOT | `2026-10-02-closeout-l1-coal-fuel` | `closeout_ercot_l1_span` | 2019–2025 |
| PJM | `2026-10-03-closeout-pjm-nuc-keeper` | `closeout_pjm_nuc_full_span` | 2019–2025 |
| CAISO | `2026-10-02-closeout-caiso-w1-arm2` | `closeout_caiso_w1_a2_span` | 2019–2025 |
| NYISO | `2026-10-02-w0-nyiso` | `w0_nyiso_span` | 2021–2025 |
| NEISO | `2026-10-02-w0-neiso` | `w0_neiso_span` | 2019–2025 |
| MISO | `2026-10-03-closeout-miso-nuc-r` | `closeout_miso_nuc_span` | 2019–2025 |
| SPP | `2026-10-03-closeout-spp-nuc-keeper` | `closeout_spp_nuc_span` | 2019–2025 |
| SOCO | `2026-10-03-closeout-soco-3-coalpile` | `closeout_soco_3_span` | 2019–2025 |
| NWPP | `2026-10-03-nwpp-next-25-served` | `nwppnext25_span` | 2019–2025 |

The board is therefore 9 ISOs × 7 year columns = 61 ISO-year cells (NYISO carries five).

**NOTHING ARMS.** No mechanism is tested, no `src/`, keeper, matrix shard, plan, spec or rubric file is touched. The probe reads committed bundles and `data/raw` actuals only and solves no LP.

---

## 1. Thresholds, ranking rule, selection rule — verbatim from GATESPEC §1 (declared defaults, taken as written)

> **Ranking (declared default).** Primary score S1 = |M3 lower-tercile $·h| on years that fail C3a or C3b in the board; secondary S2 = M2(a) + M2(b) TWh; tiebreak M1. Eligibility: S2 ≥ 1.0 TWh or M4 dormancy gap ≥ 0.20. **Selection:** the top 3 ISO-years by S1 among eligible rows become the ladder's targets; **NEISO 2023 and NYISO 2024 are always controls** (CALIBRATED ISOs; the no-flip bar in §4 protects them).

> (§2) The screen can fail: if no ISO-year is eligible, the program records that the model's remaining misses are not commitment-shaped at the grain the keeper exposes, UC-1 is still built default-off (the structural capability and the forecast case stand on their own), and UC-2 runs on the two controls plus the highest-S1 row only.

Nothing above is tightened or substituted. The clauses GATESPEC leaves open are fixed below, before any number, with the reading each one takes.

## 2. Readings fixed for the open clauses

| # | Clause | Reading (fixed ex ante) | Why |
|---|---|---|---|
| R-a | "years that fail C3a or C3b **in the board**" | The board is `scripts/calibration_verdict.py --run-id <keeper> --json` run on the committed bundles at this branch's base (rubric 3.20). A cell **fails** when its `price_mean` or `price_shape` record reads `FAIL`, **or** reads `CAVEAT` with a numeric reading outside the gate band (owner-signed exceptions and model-class-limitation caveats excuse the determination, not the number; GATESPEC says "failing gates marked"). `SKIPPED` / reference-coverage caveats with no number (CAISO 2019–2020, NWPP 2019–2022) are **unscoreable**: S1 is computed where a partial RT series exists and reported, but such a cell is never rankable. | the rule names the board, and the board on `main` today differs from the closeout plan §1 snapshot (PJM 2020 now passes C3a; PJM 2025, SPP 2024, ERCOT 2024, NWPP 2023–24 now fail) — the screen must read the live board, not the records' snapshot |
| R-b | S1 on a non-failing cell | reported for information; **not rankable** (S1 is defined only on failing cells) | verbatim rule |
| R-c | M3 tercile basis | terciles of the **actual RT hourly** price over the hours where it is finite; model system price = demand-weighted mean of the P1 zonal duals (`hourly/system_<y>.parquet`, external/interchange zones excluded by name `*_external*`, `*_ext_*`); error = model − actual; S1 = \|mean lower-tercile error\| × lower-tercile hours ($·h) | GATESPEC "C3a decomposed by actual-price tercile … × hours"; the sign is reported beside the magnitude |
| R-d | M4 "ISOs with an AS reference" | model reserve MCP per hour = max over the bundle's reserve families' duals (`hourly/reserve_family_<y>.parquet`) and the zonal `reserve_price`; actual series per ISO in §4 (PJM RTO synchronized reserve RT price; MISO Miso-Wide `GENSPINMCP` RT 2023–25; SPP RTBM `Spin` MCP hourly mean over reserve zones; NYISO RT `spin_10` zone mean; CAISO DAM `SR` clearing price `AS_CAISO_EXP`; ERCOT DAM RRS MCPC); dormancy = share of hours with MCP < $1; **gap = model dormancy − actual dormancy**; NEISO (payload gitignored, absent), SOCO and NWPP (no AS market) read **n/a**, never 0 | GATESPEC M4 definition; an ISO without a reference cannot clear the M4 leg of eligibility |
| R-e | M2 "pmin-ish" | keeper on at output ≤ (mlf + 0.10) × available plant capacity while CEMS is off; (a) mirrors it on the CEMS side at ≤ (mlf + 0.10) × nameplate; M2(a) TWh = Σ mlf × model available capacity over those plant-hours (the energy the keeper would carry at min-load) | SPP-102 §2.1 generalized, as the row says |
| R-f | on/off conventions | model on = plant output ≥ 1 % of available plant capacity (SPP-97); CEMS on = CF ≥ 5 % of nameplate (SPP-97) from the committed bench `campd` series (`frontend/data/backcast/bench/<ISO>/<y>.json.gz`, uint8 % of nameplate on the model clock — the SPP-102 instrument); plants with `nodata` or no `campd` are excluded from M1/M2 and counted | verbatim conventions |
| R-g | M5 price | the keeper's own P1 zonal dual for the plant's zone, held fixed (the SPP-102 upper-bound construction); on-state output = in-merit tranches at cap raised to mlf × available capacity at the cheapest offers; floor tranches (`mustrun`, `sync`) priced at the plant's committed offer (the closeout-PJM-decommit "floors replaced by priced MW" reading); start cost = S × plant peak available capacity; no-load $/h = CAMPD heat-input intercept × delivered fuel | the two instruments being generalized |
| R-h | M5 horizon form | (i) perfect foresight over 8760 h; (ii) rolling 36-h windows, commit 24 h, advance 24 h, initial state carried (plan §4 E2) | plan |
| R-i | M6 | integer clusters = slow-start plants under E1 (CC_REGULAR, coal subclasses, ST_GAS; `*_CHP` excluded): count, MW, and integers per 36-h window = clusters × 36 | GATESPEC M6 / plan E1 |
| R-j | selection size | exactly the top 3 eligible failing cells by S1 plus NEISO 2023 and NYISO 2024; if fewer than 3 are eligible, the shortfall is reported as such (GATESPEC §2 governs the zero case) | verbatim |

## 3. Physics parameters the DP (M5) and M1/M2 read — fixed ex ante, with the source per class

One value per ISO × class, never swept. Measured ISO-own values where a committed derive exists (rule 25), the published NREL/WWSIS-2 table otherwise; all read from `src/market_sim/config/constants.py`, `data/fleet/eia860.py` and `data/raw/_processed-legacy/`.

| Class | Start $/MW | min-up UT (h) | min-down DT (h) | min-load mlf (plant basis) |
|---|---|---|---|---|
| CC_REGULAR | 50 (`BIN_STARTUP_COST_PER_MW`, NREL/SR-5500-55433) | ISO CAMPD plant-basis `run_hours_p25_capwtd`: SPP 15, PJM 11, MISO 14, CAISO 13 (`campd_gas_commitment_params_plant_<ISO>.csv`); NYISO 21 (`nyiso_gas_bridge_cc_min_run_hours`); ERCOT, SOCO, NWPP, NEISO: NREL f-class 8 (`CC_COMMITMENT_PARAMS`) | SPP 8 (`SPP_POSTURE_MIN_DOWN_HOURS`, MMU ASOM 2024); all others NREL f-class 6 | per-plant measured `committed_pct/100` (`thermal_tranches_<ISO>.csv`, CAMPD loading-when-on) when finite; else ISO class value: SPP 0.209, PJM 0.436, MISO 0.324, CAISO 0.259 (plant-basis derives), ERCOT 0.574 (`ercot_gas_bridge_min_load_frac`, DAM LSL/HSL), NYISO 0.523 (`nyiso_gas_bridge_cc_min_load_frac`); SOCO/NWPP/NEISO 0.52 (`MIN_STABLE_PCT_PHYSICAL`, WWSIS-2) |
| ST_GAS | 35 (`BIN_STARTUP_COST_PER_MW`) | ISO CAMPD plant-basis p25: SPP 5, PJM 11, MISO 9, CAISO 10; NYISO 13 (`nyiso_gas_bridge_st_min_run_hours`); others NREL efficient-steam 24 (`ST_GAS_COMMITMENT_PARAMS`) | NREL efficient-steam 8 | per-plant `committed_pct/100` when finite; else SPP 0.090, PJM 0.128, MISO 0.107, CAISO 0.104, NYISO 0.239; others 0.12 (WWSIS-2) |
| COAL_* (all four subclasses) | 100 (`BIN_STARTUP_COST_PER_MW`) | 36 (`COAL_BIN_MIN_RUN_HOURS`, NREL baseload) | 16 (`COAL_BIN_MIN_DOWN_HOURS`) | per-plant `committed_pct/100` when finite; else 0.40 (`MIN_STABLE_PCT_PHYSICAL`) |

No-load: per CAMPD unit in the same year, OLS `heatInput = a + b·grossLoad` on hours with `opTime ≥ 1`, `grossLoad > 0`, `heatInput > 0`, ≥ 200 points and load range ≥ 10 % of unit peak (closeout-PJM-decommit B0 construction); plant no-load MMBtu/h = Σ max(a, 0) over fitted units; $/h = × delivered fuel (EIA-923 own plant-month → own-year mean → state-month mean, `eia923_monthly_fuel_costs.parquet`; Natural Gas for CC/ST_GAS, Coal for coal). A plant with no fit takes the capacity-weighted mean no-load per MW of its ISO-year class (reported as a fallback share). M1 UT/DT are the same table.

## 4. Inputs the probe reads (committed bundles + `data/raw` actuals; nothing else)

- `results/calibration/<bundle>/hourly/unit_marginal_<y>.parquet` (per-unit `mw`, `cap_mw`, P1 `mc`, labels — the committed slim layer; `dispatch/<y>_P1.parquet` is gitignored at tip and is the same dispatch), `hourly/system_<y>.parquet`, `hourly/reserve_family_<y>.parquet`, `legitimacy_diagnostics.json` (D-2 rows), `run_config.json`.
- `data/raw/_validation-source/actual_lmp_hourly_<ISO>.parquet` (`rt`), `data/raw/campd-unit-level/<ST>_<y>.parquet`, `data/raw/_processed-legacy/{thermal_tranches_<ISO>.csv, campd_gas_commitment_params_plant_<ISO>.csv, eia923_monthly_fuel_costs.parquet}`, `frontend/data/backcast/bench/<ISO>/<y>.json.gz` (CEMS `campd` series).
- AS references: `data/raw/PJM-AS/ancillary_services_<y>.parquet`, `data/raw/MISO-AS/asm_rtmcp_zonal_<y>.parquet`, `data/raw/spp-or-mcp/RTBM_MCP_<y>.csv.zip`, `data/raw/NYISO-AS/NYISO_as_rt_<y>.csv`, `data/raw/CAISO-AS/asprc_sr_ALL_*.csv`, `data/raw/ercot/ercot_<y>_dam_as_mcpc_hourly.parquet` (2023–25) and the `RRS MCPC` column of the 60-day Gen Resource disclosures (2019–22, `data/raw/ercot-AS/`, reduced as `build_ercot_dam_as_mcpc.py` does: max across resources per hour).
- Known gaps, declared now: NEISO reserve prices (`data/raw/NEISO-AS/reserve-prices/rzpd_final_*.csv` gitignored and absent); CAISO RT price 2019–2020 absent and 2021 34.8 % NaN; NWPP RT 2019–2022 absent and 2023 41.4 % NaN (June start); MISO AS prices 2019–2022 unrecoverable (README); CAISO AS prices start 2020-03-31.

## 5. What is not done here

No LP. No parameter is chosen on any M-value. No `uc_*` field exists yet. No matrix cell changes. The rule-19 census (task 3) is read from the committed D-2 rows and the keeper `run_config.json` arms; the DOF draft (task 4) lists the parameter classes of §3 with their identification source. Everything else is in the FINDING.
