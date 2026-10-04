# G-DRIFT — closeout-MISO-w3: keeper legs f98c4564 → pin 90cea720 (zero LP)

Rule 29(b) zero-LP code audit. Control: the incumbent MISO keeper bundle
`results/calibration/closeout_miso_nuc_span` (legs solved at
`f98c456401918eba82c338676e303a90004bb94c`; recipe = `scenario_config` in
`run_config_<year>.json`, 2019–2025). Pin: `90cea7206f4f3daf56ecb7bf29989f534da7a14d`.
Scope: `git diff --stat f98c4564 90cea720 -- src scripts data/raw configs` (84 files;
`configs/` and `src/market_sim/config/iso_configs.py` unchanged, so `_miso_config`
`default_scenario_overrides` is identical at both ends). The probe's own working-tree
change is out of scope. No solver, runner or LP was invoked.

Keeper-recipe values relied on (identical in all seven `run_config_<year>.json`):
`iso=MISO`, `mode=backcast`, `miso_/pjm_/caiso_/nyiso_zonal_loss_surface=False`,
`reference_price_interface=True`, `coal_fuel_inventory=True`,
`coal_fuel_inventory_plant_grain=True`, `coal_fuel_inventory_take_floor=False`,
`coal_fuel_inventory_monthly_pile=False`, `coal_monthly_pile_measured_receipts=False`.
Every field added in the range (`zonal_loss_demand_reconciliation`,
`pjm_elliott_measured_outage_overlay`, `nwpp_coi_pnw_delivery_basis`,
`nwpp_served_schedule_zonal_attribution`, `nwpp_seam_in_service_vintage`,
`nwpp_path76_served_schedule`, `caiso_dsw_daytime_lateevening_unprinted_arm`) is
ABSENT from the keeper recipe and therefore takes its `scenarios.py` default, `False`
for all seven; none appears in any MISO override.

| file | hunk (line range or function) | classification | reason (gate + MISO value, or why) |
|---|---|---|---|
| `src/market_sim/config/scenarios.py` | 7 new `ScenarioConfig` fields (`caiso_dsw_daytime_lateevening_unprinted_arm`, `pjm_elliott_measured_outage_overlay`, `zonal_loss_demand_reconciliation`, `nwpp_coi_pnw_delivery_basis`, `nwpp_served_schedule_zonal_attribution`, `nwpp_seam_in_service_vintage`, `nwpp_path76_served_schedule`) | INERT | All default `False`; absent from MISO recipe → `False`; not in `_miso_config` overrides (iso_configs.py unchanged). |
| `src/market_sim/config/scenarios.py` | `_CACHE_KEY_OPTIONAL_FIELDS` / `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` / `_BACKCAST_ONLY_OVERLAY_FIELDS` / `TIER_TAGS` entries | INERT | Cache-key/registry bookkeeping; each field is dropped from the hash at its default (`"False"`), so even the MISO cache key is unchanged. Not on the LP. |
| `src/market_sim/config/scenarios.py` | `__post_init__` validator (refuse `pjm_elliott_measured_outage_overlay` + `pjm_measured_outage_event_cap`) | INERT | Raises only when both are `True`; MISO: `False`/`False` (both PJM fields). |
| `src/market_sim/config/constants.py` | +`NWPP_MEMBER_LOCAL_TZ`, +`NWPP_SEAM_IN_SERVICE_UTC` (L5742–5772) | INERT | Read only in `envelopes._diba_legs_export` callers on NWPP paths (`nwpp_served_schedule_zone_interchange`, `nwpp_path76_served_zone_legs`, `nwpp_seam_priced_hours`) and `run_calibration.run_year` under `iso == "NWPP"`. Never read for MISO. |
| `src/market_sim/config/solve_surface_declared.py` | `DECLARED` +2 NWPP constants | INERT | Solve-surface fingerprint declarations for the two NWPP constants above; provenance/cache keying only, no LP input. |
| `src/market_sim/model/loss_demand.py` | new module (`receiving_zone_of_links`, `zonal_loss_dissipation`, `reconcile_loss_demand`) | INERT | Called only from `pipeline/solve.py` under the gate below. Consistent with R-59 (MISO closes at 0 for this term): MISO has no loss surface armed. |
| `src/market_sim/pipeline/solve.py` | `run_energy_solve` L748–774 (P1 demand reconciliation) | INERT | Gate `getattr(config,"zonal_loss_demand_reconciliation",False) and dispatch_kwargs.get("link_loss") is not None and ...`; MISO: flag `False` (and `miso_zonal_loss_surface=False`, so no `link_loss`). `p1_demand is demand`. |
| `src/market_sim/pipeline/solve.py` | `_warm_p1` / in-place floor / diagnostic route conditions (+`and p1_demand is demand`, new `elif p1_demand is not demand`) | INERT | With the flag off `p1_demand is demand` is `True`, so every route predicate evaluates exactly as at f98c4564. |
| `src/market_sim/pipeline/solve.py` | `DispatchModel(...)` / `solve_dispatch(...)` calls now pass `p1_demand`; `EnergySolveResult.loss_demand_netted` | INERT | `p1_demand` is the same object as `demand` when off; new result field is `None` and unused by the LP. |
| `src/market_sim/runner.py` | `_hindcast_measured_demand` (two NWPP raises + `nwpp_served_schedule_zonal_attribution` kwarg) | INERT | Raises gated on `nwpp_seam_in_service_vintage` / `nwpp_path76_served_schedule` (MISO `False`); kwarg passed as `False`. |
| `src/market_sim/pipeline/ttc.py` | `apply_nwpp_path76_link` new raise | INERT | Gate `iso == "NWPP" and ...`; MISO iso ≠ NWPP. |
| `src/market_sim/data/eia930/demand.py` | `load_demand` new kwargs, in-service raise, zonal-attribution block | INERT | Raise gated `nwpp_seam_in_service_vintage and (...)` (MISO `False`); path76 raise gated `nwpp_path76_served_schedule` (`False`); attribution gated `nwpp_served_schedule_zonal_attribution` (`False`); `seam_in_service_vintage` forwarded only inside the NWPP residual branch. MISO's `zone_interchange` path is untouched. |
| `src/market_sim/data/eia930/envelopes.py` | `_diba_legs_export` (+`tz` param, default `America/Los_Angeles`) | INERT | Default reproduces the old literal; only callers are NWPP priced-seam / served-schedule functions. |
| `src/market_sim/data/eia930/envelopes.py` | `nwpp_seam_priced_hours`, `nwpp_seam_priced_hours_model`, `nwpp_unpriced_residual_interchange` refactor, `nwpp_served_schedule_zone_interchange`, `nwpp_path76_served_zone_legs` | INERT | NWPP-only functions (`INTERFACE_NEIGHBORS["NWPP"]`, `_NWPP_BA_ZONES`); reached only via `load_demand` `iso == "NWPP"` branches / `run_year` `iso == "NWPP"`. MISO's interchange readers (L1420/L1541) read `_ISO_TO_HOURLY_BA["MISO"]`'s file, unchanged. |
| `src/market_sim/model/interchange/import_nodes.py` | `inject_reference_price_mc` (band/hurdle refactor, `export_delivery_basis`) | INERT | Runs for MISO (`reference_price_interface=True`, generic non-CAISO seam). With `export_delivery_basis=None` (the MISO call), `basis` is `None` and `mc[row,:] = band - hurdle` (export) / `band + hurdle + carbon_adder` (import), where `band` is the per-band price or the flat `aggregate` exactly as before — arithmetic identical to f98c4564 for both branches; `unpriced_rows` path unchanged. |
| `src/market_sim/model/interchange/import_nodes.py` | `apply_reference_price_seam_injections` (NWPP raise; `_export_basis` construction) | INERT | Both gated `config.nwpp_coi_pnw_delivery_basis and iso == "NWPP"`; MISO: `False`, iso MISO → `_export_basis=None`. |
| `src/market_sim/model/interchange/spec.py` | +`NWPP_SEAM_EXPORT_DELIVERY_TRANCHE`, +`CAISO_DSW_*_UNPRINTED_DEPTH_BY_YEAR` | INERT | Read only under the NWPP COI basis gate above and the CAISO unprinted-arm gate below. |
| `src/market_sim/model/interchange/caiso.py` | `inject_caiso_dsw_daytime_clean`, `inject_caiso_dsw_lateevening_clean`, `_caiso_dsw_unprinted_hours`, `apply_caiso_seam_injections` | INERT | `apply_caiso_seam_injections` registered only for `"CAISO"` (`model/interchange/registry.py:41`); also gated `caiso_dsw_daytime_lateevening_unprinted_arm` (default `False`). |
| `src/market_sim/data/fleet/arrays.py` | `_apply_outage_overlays` Elliott overlay block (L3072–3124) | INERT | Gate `_iso == "PJM" and config.pjm_elliott_measured_outage_overlay and config.mode == "backcast"`; MISO iso ≠ PJM, flag `False`. |
| `src/market_sim/data/pjm_elliott_outages.py` | new module | INERT | Imported only inside the PJM-gated block above. |
| `scripts/run_calibration.py` | `COAL_PLANT_GRAIN_ISOS` (+SOCO) | INERT | MISO already a member at f98c4564; membership unchanged. |
| `scripts/run_calibration.py` | `COAL_TAKE_FLOOR_ISOS` (+SOCO), `COAL_TAKE_FLOOR_MEASURED_ONLY_ISOS`, `resolve_coal_take_floor` new SOCO check | INERT | `resolve_coal_take_floor` returns `False` at its first line when `coal_fuel_inventory_take_floor` is `False` (MISO: `False`); the new check is after that return and SOCO-only. |
| `scripts/run_calibration.py` | `run_year` `load_demand(...)` +3 NWPP kwargs | INERT | Passed MISO values `False`, `False`, `False` (see demand.py row). |
| `scripts/run_calibration.py` | `run_year` NWPP seam in-service vintage cap block (L4327–4374) | INERT | Gate `getattr(config,"nwpp_seam_in_service_vintage",False) and iso == "NWPP"`; MISO `False`. |
| `scripts/run_calibration_full.py` | `solve_and_persist` +3 `_caiso_demand_flag(...)` NWPP kwargs to `load_demand` | INERT | Resolve to `False` for the MISO recipe; see demand.py row. |
| `scripts/run_calibration_full.py` | `main` `--pjm-elliott-outage-overlay`, `--zonal-loss-demand-reconciliation` args and `prb_overrides` entries | INERT | `default=None`; a `None` prb_override keeps the recipe value (`False`). Only live if the probe passes the flag explicitly. |
| `scripts/lib/solve_container.py` | `provision_swap` stale-swap reuse, `below_target_warning`, `free_disk_gib`, docstring | INERT | Memory/swap preflight infrastructure; changes swap provisioning and warning text only, not the LP or its optimum. |
| `scripts/prepare_solve_container.py` | docstring + below-target warning | INERT | Infrastructure; no LP effect. |
| `scripts/regenerate_clean.py` | `DATATYPES` +`pjm-elliott-forced-outages` | INERT | Adds a PJM-only datatype; not a MISO solve-profile input, read only behind the PJM Elliott gate. |
| `scripts/shard_prompt.py` | prompt template (prepare_solve_container first; PJM DA-virtuals fetch step) | INERT | Prompt text; `da_virtuals_fetch_reason` returns `None` for `iso != "PJM"`. Not on the solve path. |
| `scripts/calibration_verdict.py` | rubric v3.19 → v3.20 (C3c standing rule reordered last, R-58) | INERT | Scoring, not the solve path (out of G-DRIFT scope). Recorded zero-LP effect: 0 of 9 ISO determinations move. Note: re-scoring a MISO bundle at the pin uses v3.20. |
| `scripts/build_forecast_dof_ledger.py`, `scripts/forecast_verdict.py`, `scripts/register_forecast_run.py`, `scripts/render_data_dictionary.py` | various | INERT | Forecast ledger/verdict/registration and data-dictionary rendering; not on the backcast solve path. |
| `scripts/gen_nwppnext2{3..7}_attestation.py`, `scripts/data/curate_pjm_elliott_forced_outages.py`, `scripts/data/digitise_pjm_elliott_forced_outages.py` | new scripts | INERT | NWPP attestation generators and the PJM Elliott intake; not imported by the solve. |
| `scripts/probes/*` (35 files new/modified, incl. `_pjmnext26_compose_span.py`) | probes | INERT | Standalone probes; not imported by `run_calibration*.py` or `src/`. |
| `data/raw/coal-stocks/coal_stocks_{2015,2016,2017}.csv`, `README.md`, `SHA256SUMS.txt` | new years 2015–2017 | INERT | Traced: `load_coal_stocks` is read by `coal_fuel_inventory.build_coal_fuel_budget` → `opening_stock_tons(year)` = `[year-1]` only; `build_coal_plant_budget` → `load_coal_stocks([year-1])` (≥ 2018 for 2019–2025); the delivery rate (`coal_receipts.prior_years_delivery_rate`) reads coal-receipts, not stocks; `input_completeness` uses only `.empty`. The only all-years reader is `build_coal_take_floor` (`stocks["year"] <= year-1`, the S_max term), reached only when `resolve_coal_take_floor` is `True` — MISO `coal_fuel_inventory_take_floor=False` (and MISO ∉ `COAL_TAKE_FLOOR_ISOS`); `build_coal_monthly_pile` likewise gated by `coal_fuel_inventory_monthly_pile=False`. No MISO path reads stocks for years ≤ 2017. 2018–2024 CSVs unchanged (SHA256SUMS gains only the three 2015–2017 lines). |
| `data/raw/eia-930-interchange/{NEVP,NWMT,PACE,WAUW} interchange hourly.parquet`, `SOURCES-NWPP.md` | NWPP member per-DIBA files | INERT | Read only by the NWPP envelopes functions (`_diba_legs_export` reporter / `_NWPP_BA_ZONES` member loops). MISO reads its own BA file (`_ISO_TO_HOURLY_BA["MISO"]`), unchanged. |
| `data/raw/pjm-elliott-forced-outages/figure30_digitised.csv`, `.png` | new PJM intake | INERT | Read only by `data/pjm_elliott_outages.py` under the PJM gate. |

## Verdict

ALL INERT for MISO 2019–2025. Every solve-path hunk in f98c4564..90cea720 is gated on a
field that is `False` in all seven MISO keeper `scenario_config`s (the new fields are
absent and take their `False` default; iso_configs.py and the MISO overrides did not
change), or on an ISO that is not MISO (NWPP, PJM, CAISO, SOCO). The two hunks that do
execute for MISO change nothing. The first is the `import_nodes.inject_reference_price_mc`
band/hurdle refactor under `reference_price_interface=True`: with
`export_delivery_basis=None` its arithmetic is identical to the old code. The second is
the `pipeline/solve.py` route predicates: with the reconciliation off,
`p1_demand is demand` is `True`, so the zonal-loss double-count repair does not run, as
R-59 found. Its gate needs `zonal_loss_demand_reconciliation=False` → `True` and an armed
loss surface (`miso_zonal_loss_surface=False`). The 2015–2017 coal-stock CSVs reach only
`build_coal_take_floor` (and the monthly pile), which MISO never arms
(`coal_fuel_inventory_take_floor=False`, MISO ∉ `COAL_TAKE_FLOOR_ISOS`). MISO's armed
budget paths read stocks only for `year-1` ≥ 2018. The memory-preflight changes in
`solve_container.py` are infrastructure. No LIVE hunk, so no control solve is earned.
The keeper legs remain the control for a probe at 90cea720. The probe's own working-tree
change is outside this audit. The rubric moved from v3.19 to v3.20; this is scoring only,
with 0 of 9 determinations moving.
