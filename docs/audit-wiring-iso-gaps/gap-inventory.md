# Gap Inventory: Backcast-Only Wiring & Cross-ISO Coverage Gaps

**Date:** 2026-06-29  
**Scope:** Every mechanism wired on the calibration path (`scripts/run_calibration.py`) but missing or inert on the forecast path (`src/market_sim/runner.py`), plus mechanisms gated to a single ISO when they are structurally general.

## Reading Guide

- **Gap type A** — Forecast wiring omission: mechanism in calibration `dispatch_kwargs` / fleet-build / post-build but absent from `runner.py`.
- **Gap type B** — Cross-ISO coverage gap: mechanism gated to one ISO whose logic is structurally general.
- **Gap type C** — Builder asymmetry: field one builder populates but its counterpart leaves at default.
- **Severity** — CRITICAL: wrong LP structure; HIGH: silently neutered forward mechanism; MEDIUM: secondary effect; LOW: cosmetic or latent.
- **Forward-native?** — Does the mechanism have a forward analogue (CLAUDE.md rule #12)? YES = must wire in forecast. NO = correctly backcast-only.

---

## Supersession notice (2026-07-06)

**15 of 16 actionable items are LANDED** (see `fix-plan.md`). The one remaining
open item — **A5 (ERCOT single-product reserve supply cap)** — is absorbed into
the orchestrator unification plan **Stage 2** (`reserve_config._ercot_design`),
tracked in the July gap register (`docs/gap-register-2026-07.md`) as **W1**. Do
not execute `prompt-pack/w2-ercot-supply-cap.md` as written; the fix target
(`runner.py` directly) is superseded by the shared-`reserve_config` path.

The July gap register is the master tracking document for all remaining work.

---

## Type A: Forecast Wiring Omissions

| ID | Mechanism | Files / Lines | Severity | Forward-native? | Effect when missing |
|----|-----------|--------------|----------|-----------------|---------------------|
| A1 | **Hydro monthly energy budget** — `hydro_monthly_energy` + `hydro_gen_idx` in `dispatch_kwargs` | cal: 3903–3904 (base dict) | CRITICAL | YES — `_hydro_fleet(forecast_budget=True)` uses normal-water-year climatology | Hydro dispatches as unconstrained thermal (pmin/pmax only, no monthly budget). Forecast LP has no hydro energy constraint at all. |
| A2 | **NEISO reserve co-optimization** — full `elif iso == "NEISO"` branch with 3-family RCPFs | cal: 4187–4239; runner: absent (chain ends at MISO, line 773) | HIGH | YES — published RCPF tariff params, forward-derivable | `energy_reserve_coopt=True` on NEISO forecast silently falls through. No reserve constraint, scarcity pricing is VOLL-only. |
| A3 | **PJM reserve supply cap** — `reserve_supply_cap` from `pjm_reserve_deliverable_supply_cap_mw()` | cal: 4093–4101; runner PJM block: absent | HIGH | YES — published reserve requirement formula | PJM ORDC vertical step never fires in forecast; cleared reserve vastly exceeds requirement → reserve dual always zero. |
| A4 | **PJM reserve online gating** — `reserve_online_gated` + `reserve_online_rho` | cal: 4112–4118; runner PJM block: absent | HIGH | YES — market-design constraint | Online-gating constraint never built in PJM forecast; the reserve supply includes offline headroom. |
| A5 | **ERCOT reserve supply cap (single-product path)** — `ercot_rtolcap_supply_cap_mw()` | cal: 4018–4031 (both modes); runner: only in multiproduct sub-branch (684–686) | MEDIUM | YES | Single-product ERCOT forecast omits the RTOLCAP cap → uncapped reserve headroom. |
| A6 | **Negative renewable offer floor** — `apply_negative_renewable_offer_floor()` | cal: explicit call; runner: absent | HIGH | YES — REC/PTC keep-running value has forward analogue | CAISO forecast can never produce negative midday prices. `negative_renewable_offers: true` silently ignored. |
| A7 | **Reference-price interface** — `build_reference_price_node` + `inject_reference_price_mc` + `inject_reference_price_firm_export` | cal: 2603–2657, 3603–3659; runner: absent | HIGH | YES — this IS the forecast-grade import mechanism per its docstrings | `reference_price_interface: true` silently ignored in forecast; gets static fitted tranches instead of gas-priced forward seam. |
| A8 | **CT/ST netload drag floors** — `apply_gas_st_netload_drag_floor()` + `apply_ct_netload_drag_floor()` | cal: 3088–3126; runner: absent | MEDIUM | YES — net-load-keyed, documented as "admissible in both backcast and forecast" | `gas_st_netload_drag: true` / `ct_netload_drag: true` silently ignored in forecast. No weather-driven min-gen floors. |
| A9 | **CAISO solar deliverability derate** — `_apply_caiso_solar_deliverability()` structural path | cal: 1870–1897; runner: absent | MEDIUM | YES — forward solar penetration signal, not measured outcome | CAISO forecast solar is uncurtailed by local congestion. The structural derate uses forward drivers. |
| A10 | **CAISO RA must-offer P2 trigger** — `caiso_ra` gate that enters P2 even with `commitment_enabled=False` | cal: 4327–4340; runner P2 block: only checks `commitment_enabled` | MEDIUM | YES — RA program is market design | CAISO forecast with `caiso_ra_mustoffer=True` but `commitment_enabled=False` silently skips the P2 midday bridge. |
| A11 | **Import node reconciliation (NYISO)** — `import_node_gen_idx` + `import_node_monthly_lo/hi` | cal: 3913–3917; runner: absent | LOW | PARTIAL — forecast mode exists (`forward_net_import_twh`), but backcast mode uses measured EIA-930 | Forecast NYISO runs with `nyiso_import_reconciliation=True` get no monthly band constraint on import node. |
| A12 | **Gas offer curve (non-CAMPD)** — `split_gas_tranches()` | cal: 3002–3003; runner non-CAMPD path: absent | LOW | YES — uses config HR multipliers, no measured data | `gas_offer_curve: true` silently ignored for non-CAMPD ISOs (SPP) in forecast. |
| A13 | **MISO reserve co-opt (calibration path)** — REVERSE gap: runner.py has MISO branch, calibration `_run_dispatch` does not | runner: 761; cal _run_dispatch: absent | MEDIUM | YES | MISO calibration run with `energy_reserve_coopt=True` falls through — no reserve constraint in backcast. |

## Type B: Cross-ISO Coverage Gaps

| ID | Mechanism | Currently gated to | Missing for | Severity | Notes |
|----|-----------|-------------------|-------------|----------|-------|
| B1 | SPP offer curve | ERCOT defaults (no SPP entry in offer-curve blocks) | SPP | LOW | SPP uncalibrated; inherits ERCOT-tuned ternary `else` values. |
| B2 | Reliability floor (temperature/net-load min-gen) | CAISO (ct_netload_drag), NYISO (ct/st floors), NEISO (temp dual-limb), MISO (temp dual-limb) | PJM, SPP | MEDIUM | PJM's dual-fuel switching partially covers winter but no summer CT floor. SPP uncalibrated. |
| B3 | `storage_vintage_ramp` (mid-year COD ramp) | CAISO, ERCOT, NEISO | PJM, MISO, NYISO, SPP | LOW | Comment says "flat until recalibrated." Overstates early-year storage for ISOs with big mid-year builds. |
| B4 | NYISO year-varying TTC | Calibration only (`_apply_iso_year_ttc`, `_apply_iso_monthly_ttc`) | Forecast (all ISOs) | LOW | Central-East AC Transmission upgrade invisible to forecast. Fix may belong in static topology. |
| B5 | `caiso_solar_deliverability` | CAISO only | Other ISOs (no solar congestion issue) | NOT A GAP | Structurally CAISO-specific (local-area congestion). No missing coverage for other ISOs. |

## Type C: Builder Asymmetries

| ID | Mechanism | Forecast builder | Calibration builder | Severity | Notes |
|----|-----------|-----------------|---------------------|----------|-------|
| C1 | Storage fleet source | `build_default_storage()` — parameterized lump-sum | `load_eia860_storage()` — EIA-860 actuals | BY DESIGN | Different sources appropriate for each mode. |
| C2 | Pumped storage | Not included in `build_default_storage` | Appended via `load_eia860_pumped_storage()` | MEDIUM | Forecast omits ~20 GW of existing PS dispatch. May or may not be compensated by other flex. |
| C3 | `storage_cap_profiles()` | Never called (1-D caps) | Called when `storage_vintage_ramp=True` (2-D time-varying caps) | LOW | Latent: no functional difference today since forecast builder never sets monthly fields. Becomes relevant once storage_vintage_ramp is wired. |
| C4 | `reserve_storage_as_power()` (ERCOT AS reservation) | Not called | Called when `storage_as_commitment=True` | BY DESIGN | Requires measured ERCOT AS data (no forward analogue). Forecast uses endogenous AS co-opt instead. |

## Confirmed Non-Gaps

These were investigated and confirmed as NOT gaps:

| Mechanism | Reason not a gap |
|-----------|------------------|
| `apply_plant_monthly_fuel_prices`, `apply_hub_basis_overlay`, `apply_nyiso_zonal_gas_basis`, `apply_ercot_zonal_gas_basis`, `apply_pjm_zonal_gas_basis`, `apply_dual_fuel_pricing` | All run inside `resolve_fuel_prices(apply_monthly=True)` in runner.py |
| `thermal_tranche_overrides` | Runner.py uses it implicitly in its `fleet_to_bins` branch |
| Post-solve ORDC scarcity overlay (ERCOT-only) | Structurally correct per market design (ERCOT is energy-only; others have capacity markets) |
| `check_hourly_dispatch_correlation`, `compute_emissions`, `hsl_potential_mw` | Pure diagnostics / calibration output, no dispatch effect |
| `dual_fuel_switch_mask` / `dual_fuel_oil_reattribution` | Post-solve fuel re-attribution only; actual dual-fuel pricing runs in both paths |
| `storage_as_commitment` / `reserve_storage_as_power` | Backcast-only measured ERCOT AS data; endogenous co-opt is the forward replacement |
| `coal_passthrough_by_supply` (tiered) | Calibration tuning lever gated by off-by-default booleans; base passthrough runs in both |
| `load_planned_additions` — forecast only | By design: forecast adds EIA-860 pipeline, backcast uses operable snapshot |
| `apply_plant_emission_rates` — forecast has it when flag on | Backcast uses CEMS-derived rates via a different path in `generators_to_fleet_arrays` |
