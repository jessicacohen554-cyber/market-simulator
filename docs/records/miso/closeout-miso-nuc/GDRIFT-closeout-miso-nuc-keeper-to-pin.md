# G-DRIFT: MISO keeper `2026-10-02-w0-miso-fix2` (solved @25da6022) vs `claude/closeout-miso-nuc-b` @64d1771e

Zero LP. Scope: `git diff 25da6022 64d1771e -- src/ scripts/replay_keeper.py scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib/replay_recipe.py configs/` (54 files, +1914/-412; `configs/` unchanged) plus every changed `data/raw` / `data/reference` path, plus the `scripts/data` / `scripts/lib` curators that build `data/clean`.

Keeper posture used for the "default-off" claims, read from `results/calibration/w0_miso_span/run_config_<Y>.json`. All 7 years are identical on these fields: `coal_fuel_inventory=True`, `coal_fuel_inventory_plant_grain=True`, `coal_fuel_inventory_take_floor=False`, `coal_fuel_inventory_monthly_pile=False`, `coal_monthly_pile_measured_receipts=False`, `spp_mmu_offer_unavailability=False`, `spp_mmu_offer_repair` absent, `nwpp_seam_measured_limits` absent, `nwpp_demand_plant_basis=False`, `caiso_ra_mustoffer=False`, `caiso_ra_min_load_frac=0.4`, `hydro_cascade_coupling=False`, `hydro_pondage_bound=False`, `soco_gas_st_campaign_commitment=False`, `neighbor_hr_forward_skill=None`, `hindcast=False`, `nuclear_unit_availability=True`, `mode=backcast`.

At HEAD, `replay_keeper.flipped_default_overlay` was evaluated against the bundle for each year 2019–2025. Every year returns only `{capacity_screen_peak_measured_hindcast: False}`. No new field gets armed: the two new fields, `spp_mmu_offer_repair` and `nwpp_seam_measured_limits`, both default to False and are absent from the keeper, which counts as equivalent.

| file | hunk (line/func) | class | reason / years |
|---|---|---|---|
| data/raw/nuclear-availability-MISO.csv | +6389 rows (2019–2022 NRC daily rows, Duane Arnold/Palisades pass-through) | **LIVE — INTENDED (R-43)** | 2019–2022 only. The loader `outages.nuclear_unit_availability_series` filters to `date.year == year`, and the 2023/2024/2025 rows are byte-identical and in the same order (checked with `cmp` after stripping 2019–22), so 2023–25 are numerically unchanged. |
| src/market_sim/config/constants.py | `NUCLEAR_MONTHLY_CF_BY_YEAR["MISO"]` +2019–2022 rows | **LIVE — INTENDED (R-43)** | 2019–2022 only: the monthly smear on uncovered dates moves from static `NUCLEAR_MONTHLY_CF`×(1−EFORD) to measured rows. The 2023–25 rows are unchanged. This row is declared, so the MISO surface hash moves (`moved` gains `NUCLEAR_MONTHLY_CF_BY_YEAR`). Expected size per FINDING-closeout-miso-2 §3–4: nuclear about +4.0 TWh in 2019, −1.0 to −2.3 in 2020, +2.3 in 2021, +1.2 to +1.8 in 2022. Displaced energy comes from gas steam, CC and coal: ST_GAS 2019 residual goes to about −9.1, C3b 2021 to 0.221, and CC_REGULAR 2021 may flip PASS→FAIL. |
| src/market_sim/config/solve_surface.py | `SOLVE_EPOCHS` += 2026-10-02e (SPP), 03a (NWPP), 03b (NWPP/PJM/SPP), 03c (SOCO), **03d (MISO backcast)** | INERT numerics; **KEY-MOVING** | 03d (INTENDED, R-43) adds a token to every MISO backcast key, 2019–2025, because there is no `reaches_year`. The other four are ISO-scoped away from MISO (verified: `applicable_epochs` for MISO backcast = [02c, 02d, 03d]). |
| src/market_sim/config/solve_surface_declared.py | +NWPP_COI_CAISO_SHARE / NWPP_COI_PATH_SERIES / NWPP_SEAM_LIMIT_SERIES | INERT | New names are declared at registration hash, so they never enter a key. The MISO `moved` set differs from the keeper only by NUCLEAR_MONTHLY_CF_BY_YEAR. |
| src/market_sim/config/constants.py | `NUCLEAR_MONTHLY_CF_BY_YEAR` PJM/SPP/NWPP/SOCO 2019–22 rows | INERT | ISO-keyed: MISO reads only the `"MISO"` row. |
| src/market_sim/config/constants.py | `NWPP_SEAM_LIMIT_SERIES`, `NWPP_COI_PATH_SERIES`, `NWPP_COI_CAISO_SHARE` | INERT | Read only by `transfer_interface_limits.nwpp_seam_limits_hourly`, which is NWPP-gated (see run_calibration row). |
| src/market_sim/config/scenarios.py | new fields `spp_mmu_offer_repair`, `nwpp_seam_measured_limits` (+cache-key optional/default registration, TIER_TAGS) | INERT | Default False and dropped from the hash at default. Absent in keeper, and replay resolves them to False (`_registered_after_solve`). No default flips and no deletions in this diff. |
| src/market_sim/config/scenarios.py | `__post_init__` raise if repair without unavailability | INERT | Both are False in MISO. |
| scripts/replay_keeper.py | `flipped_default_overlay` + call in `main` before `--set` | INERT (replay-fidelity) | For MISO it pins only `capacity_screen_peak_measured_hindcast=False`. That is the keeper's recorded value, and `__post_init__` coerces it to False anyway when `hindcast=False` (scenarios.py ~23320). Its only reader is the runner's hindcast seam. |
| scripts/lib/replay_recipe.py | `_json_default` (sets), `apply_config_overlay(flipped_default_overlay)`, `_registered_after_solve`, `_rule26_inert_recorded` | INERT | Replay-diff diagnostics and the same overlay as above. |
| scripts/run_calibration.py | `COAL_PLANT_GRAIN_ISOS` += ERCOT; new `COAL_PILE_CEILING_ISOS=("ERCOT",)`; `resolve_coal_monthly_pile` / `resolve_coal_measured_receipts` gate text | INERT | MISO was already in the plant-grain list. Pile and receipts are False in MISO, so `resolve_coal_monthly_pile` returns False first. |
| scripts/run_calibration.py | `load_coal_measured_receipts` extraction (~L759) and its two call sites | INERT | Same body as the inline code it replaces, and only reached under `_coal_meas_armed` (False). |
| scripts/run_calibration.py | `_coal_ceiling_pile` guard on the annual `reconcile_floors_to_yard_budget` (~L6786) | INERT | `_coal_pile_armed=False` makes `_coal_ceiling_pile` False, so the annual reconcile still runs for MISO, which is live because plant_grain=True. |
| scripts/run_calibration.py | new `elif _coal_pile_armed:` ceiling-only branch (~L6921) | INERT | `_coal_pile_armed=False`. |
| scripts/run_calibration.py | NWPP seam headroom block (~L4263) | INERT | `nwpp_seam_measured_limits` absent/False, and gated `iso == "NWPP"`. |
| scripts/run_calibration.py | SPP-107 pool append (~L4529) | INERT | `spp_mmu_offer_repair` False and `iso == "SPP"`. |
| scripts/run_calibration_full.py | `_model_class_for_unit` "emergency_band" | INERT | Scoring class map only, and MISO has no such unit. |
| src/market_sim/data/coal_fuel_inventory.py | `reconcile_floors_to_yard_budget(month_index=None)` | INERT (live path, identical) | MISO calls it with `(n,1)` budgets (`build_coal_plant_budget` L446). `shape[1]==1` takes the annual branch, which is byte-identical to 25da6022 (`float(budget[i,0])`). The added `np.asarray(float)` is a no-op on a float64 array. |
| src/market_sim/data/fleet/arrays.py | `_spp_mmu_repair_armed`, `_spp_mmu_cut`, `_row_cut`, `_apply_spp_mmu_bands(multiplicative)`, `_apply_spp_mmu_pool`, 2 call sites | INERT | All behind `_spp_mmu_armed` (`spp_mmu_offer_unavailability` and `iso=="SPP"`) or `_spp_mmu_repair_armed`. |
| src/market_sim/data/fleet/models.py | `FUEL_TYPE_MAP["emergency_band"]=17` | INERT | Appended code, so existing codes are unchanged. `FUEL_TYPE_NAMES` grows by one trailing entry. No `len()`-sized one-hot exists; the only `len(FUEL_TYPE_NAMES)` use is a bounds check. No MISO unit carries it. |
| src/market_sim/data/spp_mmu_unavailability.py | `build_spp_mmu_pool_generators` | INERT | SPP and repair gated, returns []. |
| src/market_sim/runner.py | SPP-107 pool in `run_scenario_iso` | INERT | Forecast runner, SPP-gated. |
| src/market_sim/results/export.py | exclude "emergency_band" from mix/emissions | INERT | Reporting only, and no such unit in MISO. |
| src/market_sim/data/transfer_interface_limits.py | `_fixed_pst_hour`, `_nwpp_cap_series`, `nwpp_seam_limits_hourly` | INERT | New NWPP-only functions. |
| src/market_sim/model/interchange/spec.py | `NeighborInterface.forward_heat_rate` field (default None) + SOCO seam values, SOCO_FPL `hr_by_year` | INERT | Every `forward_heat_rate=` and the FPL cells sit inside `INTERFACE_NEIGHBORS["SOCO"]` (L1994+). MISO seams keep None, so `neighbor_heat_rate` takes the unchanged branch (`neighbor_hr_forward_skill=None`). |
| src/market_sim/model/interchange/spec.py | `build_seam_limit_groups` | INERT | Only called from the NWPP block. |
| src/market_sim/data/neighbor_price.py | `neighbor_heat_rate` returns `forward_heat_rate` when set | INERT | None on every MISO seam. |
| src/market_sim/pipeline/backcast_config.py | `caiso_ra_min_load_frac` 0.26→0.570 for CAISO | INERT | MISO branch is still 0.40 (recorded 0.4), and the reader is gated `caiso_ra_mustoffer and iso=="CAISO"`. |
| src/market_sim/model/lp/layout.py + rows.py + reserve_rows.py | `kron_hours` replacing `sp.kron(eye(T),B,"csr")` at 23 sites (energy balance, interface, reserve, posture, storage-alloc, local-cap, gen-group rows) | INERT (refactor, live path) | Ran 300 random canonical blocks (float64/float32/int64 data, explicit zeros, T 1–50) plus one 30×400 block at T=8760 against `sp.kron` on scipy 1.17.1. `indptr`, `indices`, `data` and their dtypes were identical. Non-canonical or empty input falls back to `sp.kron`. |
| src/market_sim/model/lp/model.py | float32 flow-cap / reduced-cost copies via `ascontiguousarray`; `_BASIS_STATUS_ARR` fancy-index basis | INERT | Same float64→float32 rounding and the same `HighsBasisStatus` objects in the same order. The basis path is only P0-cache-hit / x-year seed, and `MARKET_SIM_WARMSTART_XYEAR` is off (rule 36). |
| src/market_sim/model/lp/hydro_cascade.py | return `rhs_flat` without the first copy | INERT | Cascade is unarmed in MISO (`hydro_cascade_coupling=False`, pondage False, so `kwargs` returns UNSET first). |
| src/market_sim/data/hydro.py | `_by_month` memo in `load_hydro_cascade` | INERT | Cascade only, and unarmed. Callers do not mutate the result (`nan_to_num` copies). |
| src/market_sim/model/commitment.py | `as_adequacy_commit` loop `order[he[h][order]]` | INERT | `he` is a bool ndarray, so the order and the break semantics are the same. Caller is NYISO/AS-gated. |
| src/market_sim/pipeline/commitment.py | `_soco_gas_st_campaign_floor` row index hoist | INERT | SOCO gate is False. Ascending g order is the same anyway. |
| src/market_sim/data/outages.py | `_outage_hour_bounds` + slice assignment in place of a full-year bool mask (7 functions) | INERT (refactor, live path) | Code read: the mask was exactly `[lo:hi]`, so `arr[mask] op x` equals `arr[lo:hi] op x` element for element, `denom[mask]` equals `denom[lo:hi]`, and `arr |= mask` equals `arr[lo:hi]=True`. |
| src/market_sim/data/outages.py | `ercot_thermal_dam_availability_hourly_series` `he_vals` | INERT | ERCOT only. Equivalent anyway. |
| src/market_sim/data/eia923.py | `plant_month_price_grid`, `state_month_price_grid` iterrows→zip | INERT (refactor, live: plant/state fuel pricing) | Same row order and the same `int()`/`float()` casts. Duplicate months: last write still wins. |
| src/market_sim/data/fuel/plant_prices.py | `_iso_monthly_fuel_prices`, `_NearbyFuelPrices` zone tier iterrows→zip | INERT (refactor) | Same float64 arithmetic and order. `int(plant_id)` is unchanged when the value is float-upcast. |
| src/market_sim/data/fleet/eia860.py | `_cc_steam_part_generators`, `_cc_block_summer_ratings`, `_apply_cc_block_summer_rating` (log), `ct_mustrun_floor_mwh_by_plant` | INERT (refactor, live: cc_steam_part_capacity/cc_block_summer_rating=True) | `raw` comes from `read_parquet` with a unique RangeIndex, so `uc.loc[cand.index]` / `year.loc[cand.index]` stay aligned. Tuple keys hash equal for np.int64 and int. Values and order are the same. |
| src/market_sim/data/emission_rates.py | `measured_plant_rates` (no `.copy()`, group on key Series); `load_announced_controls` zip | INERT (refactor) | No later mutation of `df`. The `groupby([plant_id, fuel_key])` sum equals the column version (NaN keys dropped both ways). The announced-controls path is forecast only. |
| src/market_sim/data/cod_ramp.py | `_plant_segments`/`_segment_sums` hoist; `_load_cod_map_clean` groupby→segment sums + `np.rint` | INERT (refactor) | Code read: `np.average` is sum(a·w)/sum(w) using pairwise contiguous sums. The segment gather reproduces those sums (the same helper was already used by `_reduce_cod_groups` before this diff). The equal-weight fallback (a·1.0) is exact. `round` and `rint` are both half-to-even. Plant order is ascending in both. |
| src/market_sim/data/coal.py | `coal_chp_overrides` min-monthly-avg precompute | INERT (refactor) | min over (plant, year) rows of the positive monthly averages. Zero and NaN map to inf, equivalent to the old filter-then-skip. |
| src/market_sim/data/campd.py | `compute_parasitic_factors` zip; `coal_share_by_plant` positional | INERT (refactor) | `_resolve` re-casts with `int()`/`float()`. The reindexed arrays are aligned. |
| src/market_sim/data/fleet/campd_bins.py | `_plant_gas_co2_per_mmbtu` zip | INERT (refactor) | Same values. |
| src/market_sim/data/eia930/envelopes.py | `_month_hod_buckets` / `_month_hod_percentile_table` (axis-0 percentile on aligned months, per-bucket fallback) in `measured_interchange_envelope`, `measured_gas_floor_profile`, 3 PJM envelopes; NWPP comment | INERT (refactor) | `np.percentile` along axis 0 of a (days,24) view gives the same order statistics and lerp as the per-bucket 1-D call. Misaligned or non-finite months use the old per-bucket path. Empty buckets stay 0. |
| src/market_sim/data/renewables.py | `_eia860_zone_solar_geometry` hoisted NaN masks / `set_index` | INERT (refactor) | Elementwise `where`/`isnan` commutes with the boolean selection. |
| src/market_sim/data/offer_curves.py | `committed_measured_basis` zip + early `df.empty` return | INERT (refactor) | An empty df gave {} before too. Values are the same. |
| src/market_sim/data/announced_retirements.py | `_iso_fossil_operable` apply→zip `_map_fuel_type` | INERT | Same mapper and arguments (`_fuel_of` called `_map_fuel_type(tech, es, pm)`). Runner capacity evolution only; a backcast runs none. |
| src/market_sim/data/fuel/hubs.py | `load_winter_gas_basis` zip | INERT (refactor) | Same values. |
| src/market_sim/data/fuel/basis/ercot.py, basis/nyiso.py | iterrows→zip | INERT | ERCOT/NYISO only, and equivalent. |
| src/market_sim/data/caiso_outages.py | `load_crosswalk` zip | INERT | CAISO only. |
| src/market_sim/data/nyiso_par_attribution.py, nyiso_seam_envelope.py | (month,hod) percentile table; `present` hoist | INERT | NYISO only. |
| src/market_sim/data/ferc714.py | `load_ferc714_system_lambda` memo (returns copy) | INERT | Same frame. Used by SOCO seams. |
| src/market_sim/data/benchmark_corridor.py | `corridor_context` iterrows→to_numpy | INERT | Scoring / benchmark context only. |
| src/market_sim/data/stb_ep724.py | new reader | INERT | Imported by nothing on the solve path (grep). |
| src/market_sim/model/storage.py | `_caiso_storage_envelope_clock_repaired` axis-0 quantile | INERT | CAISO only. Equivalent. |
| src/market_sim/results/emissions.py | `compute_must_run_emissions` apply→list | INERT | BTM emissions reporting. Same per-row arithmetic. |
| src/market_sim/results/scarcity.py | `ercot_as_plan_requirement_mw` scatter; reformatting | INERT | ERCOT only, otherwise formatting only. |
| src/market_sim/results/cache.py | epoch-ledger prose (02e, 03a–03d) | INERT | Docstring. |
| src/market_sim/pipeline/solve.py | docstring (warmstart default OFF) | INERT | Docstring. |
| src/market_sim/matrix.py | `_write_summary_md` zip | INERT | Forecast ensemble markdown. |
| data/raw/campd-unit-outages-shortgas-splitremap-SPP.csv | new | INERT | SPP-suffixed file, never referenced by name in src. MISO reads only `-MISO` files. |
| data/raw/nwpp-intertie-otc/*, data/raw/reference/nwpp_plant_basis_energy.csv | new / re-derived | INERT | NWPP mechanisms are off/absent in MISO. |
| data/raw/reference/caiso-storage-*.csv | new | INERT | CAISO only. |
| data/raw/stb-ep724/* | new | INERT | Intake only, no consumer. |
| data/raw/eia-860m/README.md, ferc-714/README.md | docs | INERT | Docs. |
| EIA-923 "Final 2025" | n/a | INERT for MISO | `data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv` is blob `c7ea8a36` at both 25da6022 and 64d1771e (it landed at 156f9075d, already an ancestor of the keeper's sha). `eia-860`, `coal-receipts`, `coal-stocks` and `campd-unit-outages-e923-MISO.csv` are also unchanged. The keeper already solved on it. |
| scripts/data/curate_hydro_plant_modes.py | `DEFAULT_ISOS` += SOCO | INERT | Per-ISO partition, so the MISO partition is unchanged. |
| scripts/lib/clean_profiles.py, scripts/regenerate_clean.py | `also_reads` (NWPP→CAISO), `stb-coal-loadings` datatype | INERT | No MISO partition content changes. |
| scripts/data/derive_thermal_tranche_online_frac_by_year.py, derive_neighbor_hr_by_year.py, derive_neighbor_forward_hr.py, others | PJM/SOCO/NWPP/CAISO derives | INERT | No MISO-read artifact changed (data/raw tree diff above). |
| scripts/data/derive_nuclear_availability.py | MISO re-derive | INTENDED (R-43) | Produced the CSV above. |

## (1) Solve-surface / composer

- MISO's fingerprint is **a4ebec6b29ae93a1** at the keeper (all 7 legs, epochs [02c, 02d]) and **32cf65618d245617** at HEAD (epochs [02c, 02d, 03d]; `moved` += NUCLEAR_MONTHLY_CF_BY_YEAR). Both changes hit every MISO backcast key, 2019–2025.
- `scripts/probes/_w0_compose_span.py::check_legs` aborts unconditionally when legs disagree on `solve_surface.fingerprint` ("legs disagree on solve_surface fingerprint"). `--inert-proof` only relaxes a mixed git sha, not a mixed fingerprint. The composer also needs per-year leg bundles (meta years == [Y]), and the keeper only has the composite.
- **So all 7 years must be re-solved.** 2023–2025 have no LIVE hunk, so those re-solves should reproduce the keeper's numbers. That is a free parity check: any 2023–25 difference flags a missed hunk or solver nondeterminism.

## (2) Unclassified

None. The classification holds only for 64d1771e. If the branch takes a merge from main, re-run G-DRIFT on the merge delta.

## Addendum: merge delta 64d1771e → pin f98c4564 (PR #7129 merge; main had moved)

`git diff 64d1771e f98c4564` on the solve path (`src/`, `pyproject.toml`, replay/run scripts, `configs/`, `data/raw`) touches four files. All four are INERT.

| file | hunk | class | reason |
|---|---|---|---|
| src/market_sim/data/egrid.py | `_load_egrid_plant_co2_raw`: `pd.read_excel(..., engine="calamine")` | INERT | The parent re-read every committed vintage (2018–2024) with openpyxl and with calamine at the pin. The frames are `DataFrame.equals` and have identical dtypes. |
| pyproject.toml / uv.lock | + `python-calamine==0.8.2` | INERT | Adds the reader backing the hunk above. The numeric stack pins are unchanged. |
| src/market_sim/pipeline/persist.py | `env_solve_choices`, `ENV_SOLVE_KNOBS`, `HIGHS_OPTION_DEFAULTS` in `environment_block` | INERT | Writes record metadata only. The function reads env vars and never sets them. |
| src/market_sim/data/caiso_as_requirements.py | loader changes | INERT | Its only caller, `reserves/spec.py::_caiso_locational_as_families`, sits under `caiso_locational_as_families`. That flag is False in every MISO keeper leg. |
