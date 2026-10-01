# PRECOMMIT — R-ERCOT-17: pooled South-Texas gas basis, all seven years

Date 2026-09-29. Keeper `2026-09-28-r-16-oklaunion-hr` (bundle `results/calibration/r_ercot16_span`, 2019–2025, ISO NOT-YET). DATA PROFILE: ercot. Written before any solve.

## 1. Owner ruling (verbatim)

Decision card, 2026-09-29, answer: **"Pool South Texas (Recommended)"**. The option read: *"One qty-weighted South+South_Central Sch5 basis for every year: no threshold, no free parameter (rule 14 misalignment: 3 small plants priced 4.3 GW). Moves train years too (South -0.64/-0.15/-0.57 in 2023-25), so all 7 years are re-solved (~7 shards) and it may move 2024 C3a either way."*

## 2. The construction (zero DOF)

- New default-off flag `ercot_south_texas_pooled_basis` (`ScenarioConfig`, cache key, TIER 3, matrix row + a cell in every ISO shard).
- One seam: `apply_ercot_zonal_gas_basis` → `pool_ercot_south_texas_basis` puts South and South_Central on the same row **before** the EP reference and the recentring. Both member rows keep their EIA-923 `source`, so `ercot_zonal_spread_ep_referenced`'s F923 grouping is unchanged.
- The pooled row is new data, never an edit: `zone == "South_Texas_Pooled"` rows in `data/raw/ercot_zonal_gas_hub.csv`, written by `derive_ercot_zonal_gas_hub.py --pooled-south-texas` from the published EIA-923 Schedule 5 workbooks with the fleet's own plant→zone map. Weights are measured MMBtu. Fail-closed: no pooled row → member rows untouched (every forecast year).

### Reproduction first (the derive's `--validate`, same workbooks)

| Year | Workbook (sha256 prefix) | South | South_Central | North | Pooled (plants / MMBtu) |
|---|---|---|---|---|---|
| 2019 | M_12_2019_Final_Revision (`8a7144dd`) | +1.19 = | −0.05 = | −0.07 = | **+0.03** (16 / 162M) |
| 2020 | M_12_2020_Final_Revision (`0e5afa8f`) | +3.53 = | +0.64 = | +0.03 = | **+0.74** (16 / 156M) |
| 2021 | M_12_2021_Final_Revision (`8bf9004e`) | +4.36 = | +6.30 = | +6.12 = | **+6.19** (16 / 152M) |
| 2022 | M_12_2022_Final_Revision (`6d41d566`) | +1.20 = | +0.36 = | +0.41 = | **+0.42** (16 / 173M) |
| 2023 | M_12_2023_Final_Revision (`cec9a4b5`) | +1.20 vs 1.23 | +0.56 = | +0.15 vs 0.13 | **+0.59** (15 / 184M) |
| 2024 | M_12_2024_Final (`c7c4d3d3`) | +0.66 vs 0.63 | +0.49 vs 0.45 | +0.28 vs 0.21 ✗ | **+0.52** (17 / 218M) |
| 2025 | M_12_2025_Final (`95684212`) | +0.51 vs 0.59 ✗ | +0.07 vs −0.12 ✗ | +0.29 vs 0.43 ✗ | **+0.15** (17 / 196M) |

`=` exact at two decimals. 2019–2022 reproduce exactly; 2023–2024 South/South_Central within the derive's own ±0.05 tolerance.

**2025 is a vintage refresh as well as a pool.** The committed 2025 rows came from EIA's Feb-2026 early release (monthly reporters only: South_Central 7 plants / 120M MMBtu). That file is no longer published; EIA now serves only the 2025 Final (12 plants / 161M). The pooled 2025 row uses the Final, the only receipts that can be derived today (rule 14: the accurate source). Decomposition: pooling alone on the committed vintage would give ≈ +0.02; the Final gives +0.15. So of South_Central's 2025 move (−0.12 → +0.15), about half is the pool and half is the vintage refresh. North's 2025 row stays on the early release. Re-deriving the member rows from the Finals is a separate rule-23 data update (source changed), routed, not done here.

Pooled minus the committed South row, re-derived from the receipts: 2019 −1.16, 2020 −2.79, 2021 +1.83, 2022 −0.78, 2023 −0.64, 2024 −0.11, 2025 −0.44. (The handoff's −0.15 / −0.57 for 2024/25 were computed on the csv's rounded counts and the old vintage.)

## 3. Phase 0 — arm fleet delta (zero LP, 14 fleet-only rebuilds)

`scripts/probes/_r_ercot17_south_pool_delta.py` rebuilds each year through `replay_keeper.run_year_kwargs` with that year's own `config_partition_overrides`, flag off vs on. Row sets identical; only gas rows (plus 11 coal peak rows on the shared gas anchor) move. Capacity-weighted delivered-fuel delta, $/MMBtu:

| Year | South (6.4 GW) | South_Central (11.6 GW) | North / Northeast / Houston (40 GW) | West |
|---|---|---|---|---|
| 2019 | −1.04 | +0.18 | +0.11 | +0.11 |
| 2020 | **−2.49** | +0.37 | **+0.27** | +0.28 |
| 2021 | +1.64 | −0.28 | −0.17 | −0.17 |
| 2022 | −0.70 | +0.13 | +0.07 | 0 |
| 2023 | −0.57 | +0.09 | +0.06 | 0 |
| 2024 | −0.11 | +0.07 | −0.002 | 0 |
| 2025 | −0.44 | +0.26 | −0.004 | 0 |

Median econ-tranche mc delta, South: 2020 ≈ −16 to −18 $/MWh, 2019 ≈ −7, 2021 ≈ +11, 2022 ≈ −5, 2023 ≈ −4, 2024 ≈ −0.8, 2025 ≈ −3. Peak rungs scale with the ×151 / ×434 carve-out peak bands, so their deltas run to hundreds of $/MWh (2019–2023 only).

**The side effect, stated before solving.** The keeper's spread is recentred to a capacity-weighted mean of zero (the level is the measured EP series). Pulling the South row down lowers that mean, so **every non-South gas unit rises** by the same constant: +0.27 $/MMBtu in 2020 (≈ +2 $/MWh on CC econ offers), +0.11 in 2019, −0.17 in 2021, +0.06–0.07 in 2022/23, ≈ 0 in 2024/25. This is the existing construction working as designed (the fleet level is fixed to the measured statewide series; the thin South row had been pulling everyone else below it), not something the pool adds. It will raise 2019/2020 prices.

## 4. G-DRIFT (rule 29(b)) — legs 3c398753 (2019–20), edbfdad5 (2021), 2af9ab74 (2022–25) → pinned SHA

See §8: ALL INERT. The keeper's committed legs are the control (form 4); no control solve.

## 5. Arm

Seven shards (rule 36), one per year, each `replay_keeper.py results/calibration/r_ercot16_span --years <Y> --set ercot_south_texas_pooled_basis=true`. Prompts: `docs/records/ercot/r-ercot/SHARD-PROMPTS-r-ercot-17.md`. Partition signatures unchanged (2019–22 swcap true / EP ref true / CC_REGULAR.peak 151.008; 2023 true / **false** / 151.008; 2024–25 false / true / 4.576).

## 6. Predictions (written before solving)

Keeper baseline (r-16): LW price 57.71 / 26.93 / 173.60 / 68.54 / 52.02 / 27.83 / 32.98; C3a +24.0 / +6.0 / +4.6 / −8.7 / −20.0 / −10.7 / −9.6 %.

| Year | South merchant TWh (keeper → arm; actual) | LW price | C3a | C3b | Determination |
|---|---|---|---|---|---|
| 2019 | 8.37 → 9.5–11 (11.74) | +0.3 to +1.0 | +24.0 → +24.5 to +26 (FAIL, worse) | 0.539 ± 0.02 | NOT-YET (unch.) |
| 2020 | 1.32 → 5–9 (10.68) | +0.8 to +2.0 | +6.0 → +9 to +13 (**may cross +10 %**) | 0.241 → 0.23–0.27 | NOT-YET (unch.) |
| 2021 | 15.98 → 12–14.5 (10.46) | −1 to −4 | +4.6 → +2.5 to +4.5 | 0.067 ± 0.01 | CALIBRATED (unch.) |
| 2022 | 10.53 → 11–12 (11.23) | +0.1 to +0.5 | −8.7 → −8.0 to −8.6 | 0.167 ± 0.01 | CALIBRATED (unch.) |
| 2023 | 10.31 → 10.8–11.6 (11.29) | +0.1 to +0.4 | −20.0 → −19.3 to −19.9 | 0.293 ± 0.01 | NOT-YET (hold) |
| 2024 | 12.21 → 12.2–12.6 (11.28) | ±0.2 | −10.7 ± 0.3 (stays FAIL) | 0.189 ± 0.005 | NOT-YET (unch.) |
| 2025 | 11.82 → 12.0–12.8 (10.92) | ±0.3 | −9.6 → −9.0 to −9.9 (**near the −10 % edge**) | 0.127 ± 0.01 | CALIBRATED (at risk) |

- C1 CC_REGULAR: 2020 +9.1 → +8 to +9.5 (South CCs are mostly CC_REGULAR, so pooling mostly re-sites CC energy within the class; the dearer non-South gas shifts a little to coal). 2019 +8.7 → +8 to +9. COAL_PRB 2020 −13.1 → −12.5 to −13.1.
- The 2020 South shortfall is expected to close only partly: the gap is also commitment/availability, not only offer price.
- C3c hour counts move by a few; 2021 slack may move.

## 7. Decision rule

Rule 14 governs: the pool is kept on its identity (owner already ruled the construction), never on its scores. Promote under the standing instruction ("Is it an improvement? Then promote") if no train-year determination flips worse. If 2024 or 2025 flips CALIBRATED → NOT-YET (2025 is the live risk), do **not** promote on my own: decision card with the numbers, all bundles kept (rule 31). DOF ledger unchanged (the pool adds none).

## 8. G-DRIFT result — ALL INERT, form 4 valid (recorded before launch)

Ranges: `3c398753…` (2019–20) → `edbfdad5…` (2021) → `2af9ab74…` (2022–25) → `origin/main 0a5eb910…`, linear history. Every changed hunk on the backcast path classified (full table in the session record; summary):

- **New `ScenarioConfig` fields** (`campd_split_remap_companions`, `unit_outage_exit_cohort_repair`, `unit_outage_exit_ym_from_eia860`, `chp_steam_floor_conduct_scope`, `coal_fuel_inventory_monthly_pile`, `coal_monthly_pile_measured_receipts`, `caiso_*` clock repairs, `pjm_da_virtual_settle_financial`, `miso_gas_ecomin_online_floor`, `spp_commitment_posture`, `nyiso_ne_ac_*`): all default off, absent or pinned false in the keeper. INERT.
- **LP rows / reserves / commitment / storage / renewables** (`lp/rows.py` posture rows and coal-yard reshape, `reserves/spec.py`, `pipeline/commitment.py`, `model/storage.py`, `data/renewables.py`): SPP / MISO / CAISO / SOCO gated or behind off flags (`coal_fuel_inventory`, `ercot_commitment_posture` off). INERT.
- **`shed_penalty_voll`**: returns `iso_config.voll` unless `ercot_swcap_vintage`, which is unchanged since the 2019–21 legs and off in 2022–25. INERT.
- **Oklaunion (127) now present in the 2021–25 fleet, masked by `ISO_PLANT_EXITS`** — the one data/fleet change that reaches ERCOT. **Measured, not read:** 2022 fleet-only rebuild at `2af9ab74` vs HEAD — all 2,344 common rows byte-identical in mc, availability, pmax and pmin; the only difference is 4 new `COAL_North_p127_*` rows with availability 0 and min-gen 0 in every hour. The DAM plant-grain residual lands only on 127 (it is the sole unmapped coal plant in 2021–25 DAM data).
- **Sandy Creek commission-year re-key**: ages stay below the COAL WEFOR/derate onsets; measured identical in R-ERCOT-15.
- Replay note: the keeper recipe carries the deleted `nyiso_firm_imports`; `replay_keeper.build_kwargs` handles it (the §3 probe replayed all seven years through it without error).

The keeper's committed legs are the control. No control solve.
