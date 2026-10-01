# RESULT — R-ERCOT-14: Oklaunion joins ERCOT + the pre-2022 SWCAP vintage, PROMOTED; ISO still NOT-YET

PRECOMMIT: `docs/records/ercot/PRECOMMIT-r-ercot-14-oklaunion-swcap-2026-09-28.md` (pinned SHA `edbfdad5235eae5bacc2e8b0248024cae625a503`).
New keeper `2026-09-28-r-14-oklaunion-swcap` (`results/calibration/r_ercot14_span`, 2019–2025) supersedes `2026-09-28-r-13-2019-reserve`.
Owner decision card, answer verbatim: **"Promote B (Recommended)"**.

## Headline

- **Two zero-DOF structural corrections.** Offer multipliers are untouched (rule 1(c)); the DOF ledger is unchanged (12 / 7).
  1. **Oklaunion (ORIS 127, 650 MW coal) is in ERCOT's fleet for 2019 and Jan–Sep 2020.** ERCOT's 60-Day DAM lists `OKLA_OKLA_G1` (J01–J05) through 2020-09-30, and its output loads at 0.97 on EIA-930 ERCO coal; EIA-860 codes it SWPP. Rule 14.
  2. **`ercot_swcap_vintage`:** the pre-2022 offer cap, ORDC VOLL and shed penalty now sit on the one published $9,000 HCAP.
- **Validation years improve; 2022–2025 are byte-identical.**
  - 2019: C3a +41.4 % → **+24.0 %**, C3b 0.874 → **0.539**.
  - 2020: C3a **PASSES** (+6.0 %).
  - 2021: C3b 0.104 → **0.067**.
- **ISO stays NOT-YET**, on the 2023 carve-out (owner hold) and 2024 C3a −10.7 %, both unchanged.

## Per year (keeper → new keeper, P1; same scorer, same bench)

| Year | C3a | C3b | C3c (h > $200, model vs RT) | C1 CC_REGULAR | C1 COAL_PRB | C1 ST_GAS | LW price $/MWh | Shed MWh | h ≥ $1k | Determination |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | +41.4 → **+24.0 %** | 0.874 → **0.539** | 142 → 121 vs 106, PASS | +9.63 → +8.72 | −10.98 → −9.30 | +4.61 → +4.18 | 65.81 → 57.72 | 17.1 → 0 | 54 → 41 (26 act.) | NOT-YET → NOT-YET |
| 2020 | +11.3 → **+6.0 % PASS** | 0.343 → 0.242 | 42 → 39 vs 56, PASS | +9.56 → +9.12 | −13.94 → −13.12 | +7.12 → +6.92 | 28.27 → 26.93 | 0 → 0 | 5 → 3 | NOT-YET → NOT-YET (C1, C3b) |
| 2021 | +2.0 → +4.6 % | 0.104 → **0.067** | 667 vs 258, CAVEAT (unch.) | −1.52 (unch.) | −1.33 (unch.) | −0.60 (unch.) | 169.28 → 173.60 | 4,391 → 4,145 | 123 → 123 | CALIBRATED → CALIBRATED |
| 2022 | −8.7 % | 0.167 | 97 vs 196, CAVEAT | −7.96 | +5.90 | −0.41 | identical | 0 | — | CALIBRATED |
| 2023 | −20.0 % FAIL | 0.293 FAIL | 155 vs 181, PASS | +2.50 | −1.86 | −0.40 | identical | 0 | — | NOT-YET (owner hold) |
| 2024 | −10.7 % FAIL | 0.189 | 13 vs 53, CAVEAT | −1.35 | −1.22 | −1.27 | identical | 0 | — | NOT-YET |
| 2025 | −9.6 % | 0.127 | 0 vs 31, CAVEAT | skipped (prelim. 923) | +3.72 | skipped | identical | 0 | — | CALIBRATED |

**Benchmark note (read before quoting C1).** Once the bin sheet carries 127, the CAMPD backfill books Oklaunion's actual output into the 2019/2020 bench parts (COAL_PRB actual 2019 61.30 TWh). The "keeper" column above is the keeper **re-scored on that same bench**, so every row compares like with like. Against the old bench, the handoff quoted COAL_PRB 2019 at −8.15.

## Attribution

- **2019–2020 are all Oklaunion.** B = A byte-identically in both years. With 127 in, the energy price never nears the old clip: max λ $2,649 (2019) and $471 (2020).
  - Adding 650 MW of coal displaced gas CC: model coal +1.68 / +0.82 TWh, CC −0.92 / −0.44 TWh.
  - It removed most of the 2019 over-scarcity: shed 17 → 0; ≥ $1k hours 54 → 41.
- **2021 is all SWCAP.** 127 is masked all year. In the keeper, the 49 Uri shed zone-hours sat at λ = $5,000; B prices them at $9,000, the HCAP ERCOT actually cleared in EEA3. Shed falls 246 MWh because the rigid RRS/Reg-Up step is no longer cheaper than shedding.
- **2022–2025:** 127 is masked and the cap is $5,000, so both changes are inert. These years are the keeper's own R-ERCOT-12 legs, recomposed.

## Prediction scorecard (PRECOMMIT §4)

| # | Prediction | Outcome |
|---|---|---|
| PA1 | coal +1.5–2.5 TWh (2019), +0.6–1.1 (2020) | **HIT** +1.68 / +0.82 |
| PA2 | CC_REGULAR 2019 → +7.5…+8.5; 2020 → +8.6…+9.2 | 2019 **MISS** (+8.72, smaller gain); 2020 **HIT** (+9.12) |
| PA2 | COAL_PRB does NOT close (benchmark gains 127 too) | **MISS, better:** on the same bench it narrows 1.68 / 0.82 TWh |
| PA3 | C3a 2019 +35…+41 %, 2020 +8…+11 %; C3b moves < 0.05 | **MISS, better:** +24.0 % / +6.0 %; C3b −0.335 / −0.101. The 650 MW sat in exactly the tight hours |
| PA4 | no train-year determination moves | **HIT** |
| PB1 | 2019–2021 ≥ $1k hours and C3a rise; 2021 may flip | **MISS:** inert in 2019/2020; 2021 C3a rose +2.6 pts but stays PASS; ≥ $1k count unchanged |
| PB2 | shed ≤ keeper every year | **HIT** (2019 0; 2021 4,145) |
| PB3 | annual C1 moves < 0.5 TWh | **HIT** (0 in 2019/2020; 2021 unchanged) |
| PB4 | 2020 moves least | **HIT** (0) |

## Committed / merged

- **Code:**
  - `ScenarioConfig.ercot_swcap_vintage` + `pipeline.spec.shed_penalty_voll`.
  - `constants.ISO_PLANT_EXITS` + `ba_membership.plant_exit_first_outside_row` + the fleet exit mask.
  - The `derive_eia860_coal_min_config.py` retired-plant vintage fallback.
  - `COAL_PLANT_SUPPLY[127]`, `COAL_PLANT_COMMISSION_YEAR[127]`.
  - Tests; the solve-surface pin advanced (ERCOT 237 → 238 rows).
  - A matrix row plus a cell in every shard.
- **Data:** the bin-sheet row; 5 DAM crosswalk rows; +1 `coal_min_config_ERCOT.csv` row; +4 `campd-unit-outages-hourgrain.csv` rows (every other row value-identical to a fresh re-derive).
- **Keeper and governance:**
  - Keeper bundle `r_ercot14_span` (rule-15 slim shape), its sidecar, run payload, and the 2019/2020 bench parts.
  - Re-keyed: `keepers/ERCOT.json`, `status/ERCOT.js`, `calibration-complete.json`, and `program-status.json` gate (a).
  - The superseded keeper pruned (rule 35).
- **Gates at promotion:**
  - `audit_keepers --iso ERCOT`: 0 failures, 0 warnings.
  - `check_promotion_completeness --iso ERCOT`: OK.
  - `stamp_config_partition --check`: OK.
  - `check_mechanism_matrix`: OK.

## Where the bytes are (rule 34(e))

- **On `main`:** `results/calibration/r_ercot14_span` (slim), plus its sidecar and payload.
- **Legs:** local, gitignored. Provenance only (rule 33(d)): A-2019 `cec0ae84`, A-2020 `ad3e3338`, B-2019 `cbb842a8`, B-2020 `af45bf0e`, B-2021 `9a8f3408`; 2022–2025 are the R-ERCOT-12 legs.
- **Re-solving any leg** costs ~17 min of LP.
- **Arm-A composite** (`r_ercot14_span_A`): local only. It was not promoted; the owner chose B.

## Routed (unchanged from PRECOMMIT §6, plus two new)

- **The 2019/2020 coal residual is conduct.**
  - Martin Lake, Sam Seymour and Sandy Creek sit at their must-run floor for 4,600–5,900 h while gas CC runs. COAL_PRB is still −9.30 / −13.12 TWh and CC_REGULAR +8.72 / +9.12.
  - The admissible levers are fenced: the coal offer cells are R or K, and the 2019–22 SCED corpus was declined.
  - **2020 C3b 0.242 is now the nearest-to-pass validation miss** (band 0.2 at the time of scoring).
- **SPP also carries Oklaunion** (SPP-48 `mid_vintage_exit_carry`). ERCOT market data places it in ERCOT; that is the SPP lane's call (rule 25).
- **Sandy Creek commission year** is keyed 56257 while the bin sheet uses 56611 (age-availability fallback to 2010).
- **`derive_campd_coal_heat_rates.py`** omits bin-sheet plants absent from the BA-filtered fleet (127 uses eGRID).
- **The R2 overlay cap composition** is untouched; the 2021 energy λ now reaches $9,000 in the 49 Uri shed zone-hours.
