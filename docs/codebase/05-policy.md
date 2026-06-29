# 5. Policy & Scarcity Pricing

Source: `src/market_sim/policy/` (IRA, RPS, carbon, EAC, constraints) and the
scarcity overlays in `src/market_sim/results/` (`scarcity.py`, `rcpf.py`). Most
policies enter the LP as **marginal-cost adjustments**; RPS enters as a constraint
whose dual is the REC price; scarcity overlays are **post-solve price adders**
(except reserve co-optimization, which is in-LP).

## 5.1 IRA tax credits (`ira.py`)

Credits reduce dispatch MC or LCOE — no constraint rows.

| Function | Effect |
|----------|--------|
| `h2_45v_credit_per_mmbtu(year, config)` | §45V hydrogen ($3.0/kg → $/MMBtu); 0 after `ira_h2_45v_last_year` |
| `ccus_45q_credit_per_mwh(co2_captured, year, config)` | §45Q CCUS ($85/tCO2 × capture rate); 0 after `ira_ccus_45q_last_year` |
| `compute_dispatch_credits(config, year)` | `(wind_mc, solar_mc)` dispatch adders. Wind gets a negative-MC PTC; solar gets 0 (its benefit is the ITC on capex). Binary on/off at the `ira_wind_solar_last_year` cliff (OBBBA), not graduated |
| `ira_phaseout_fraction(year, config)` | linear 100%→0% ramp between `ira_other_clean_last_full_year` and `ira_other_clean_phaseout_end` (geothermal, non-PTC hydrogen) |
| `apply_ira_credits_to_lcoe(tech, lcoe, year, config)` | reduces LCOE for capacity-economics decisions (wind binary PTC, geothermal phased PTC) |

## 5.2 RPS (`rps.py`)

`get_rps_target(iso, year)` looks up `STATE_RPS_FLOORS` and linearly interpolates
the required clean-energy fraction (0–1), or `None`. RPS is **not** a force-build
step — it is an annual LP constraint (`_build_rps_row` in `dispatch.py`):
`Σ(W + S + nuclear P) ≥ rps_target · Σ demand`. **Its dual is the REC/REC shadow
price** (`DispatchResult.rps_shadow_price`), which competes with exogenous EACs in
capacity economics (`max(eac_exogenous, rps_shadow_price)` — no stacking).

## 5.3 Carbon pricing (`carbon.py`)

`resolve_carbon_price(config, year)` resolves a `$/tCO2` price by priority:
1. flat `config.carbon_price` if non-zero;
2. else `state_carbon_price` (measured CA cap-and-trade / RGGI auction settlements,
   2023–2025, gated on `config.state_carbon_pricing`);
3. else interpolate the named `config.carbon_price_path` trajectory;
4. else 0.

It enters the dispatch objective as `carbon_price · emission_rate · generation`
added to each thermal unit's MC — no constraint row. CAISO unspecified imports
carry a border-carbon adjustment (`CARB_UNSPECIFIED_IMPORT_EF = 0.428 tCO2e/MWh`).

## 5.4 Environmental attribute credits (`eac.py`)

Exogenous per-resource credits (`$/MWh`), distinct from the endogenous RPS shadow
price (the two do not stack — one MWh = one certificate sold at the higher price):

| Function | Effect |
|----------|--------|
| `apply_eac_to_mc(mc, fleet, config)` | subtracts per-generator EAC from MC in place (nuclear, gas_cc_ccs, geothermal, offshore_wind) |
| `compute_eac_dispatch_credits(config)` | `(wind_mc, solar_mc, storage_mc)` zone-level adders (onshore wind/solar/storage discharge) |
| `apply_negative_renewable_offer_floor(...)` | when `negative_renewable_offers` on, floors wind/solar offers at `−renewable_keep_running_value` so curtailment produces negative LMPs in oversupply |
| `get_eac_price_for_new_entry(tech, config)` | EAC price for new-build / retirement economics |

Per-resource fields: `eac_price_nuclear / wind / solar / storage / gas_cc_ccs /
offshore_wind / geothermal`.

## 5.5 Reserve co-optimization (in-LP)

Several ISOs co-optimize energy and reserves inside the LP (the
`R[r,t]`/`ORDC[k,t]` columns of §2.5). Inputs are assembled per ISO:

- **ERCOT multi-product** (`scarcity.ercot_multiproduct_reserve_coopt_inputs`):
  RegUp / RRS / ECRS / Non-Spin with nested shared-headroom rows and ORDC demand
  steps (`ercot_ordc_demand_steps`). Forward AS requirements are formula-driven
  (load/ramp/VRE-share/forecast-error) or measured ASPLANNP433. Load-resource and
  storage AS credits net into supply; `ercot_rtolcap_supply_cap_mw` caps cleared
  reserve at measured reality.
- **PJM stepped ORDC** (`scarcity.load_pjm_ordc_curve`,
  `pjm_reserve_cascade_mcp`): a stepped (not smooth) curve; Synchronized ⊂ Primary
  ⊂ 30-min cascade; requirement = `1.5 × MSSC` (largest single contingency).
- **NYISO / MISO**: nested locational families / footprint-wide requirement,
  assembled in the runner's `*_reserve_coopt_inputs` helpers.

When co-optimization is on, the reserve clearing price lifts the energy LMP
endogenously and dispatch volumes change — so the post-solve ORDC overlay (below)
is skipped to avoid double-counting.

## 5.6 Post-solve scarcity overlays

When reserve co-optimization is **off**, scarcity is added after the solve. The LP
volumes/dispatch/emissions are untouched; only the price tail moves, and the
adjusted price is what feeds next year's capacity economics.

### ERCOT ORDC (`scarcity.py`)

Replicates ERCOT's real-time on-line reserve price adder (RTORPA) from a
loss-of-load-probability (LOLP) curve — scarcity emerges from reserve headroom,
not a tuned parameter:

```
LOLP(R) = 1                            if R ≤ MCL
        = 1 − Φ((R − MCL − μ_eff)/σ)   if R > MCL,   μ_eff = μ + shift·σ
RTORPA  = 0.5·(VOLL − λ)·LOLP(R_online + R_offline; μ, σ)
        + 0.5·(VOLL − λ)·LOLP(R_online; μ/2, σ/√2)
```

`reserve_headroom(...)` (line 364) splits operating reserves into online
(spinning) and offline (quick-start only) tiers — cold slow-start units contribute
to neither, removing the perfect-foresight LP's phantom reserve. `ordc_adder(...)`
(line 258) caps the adder so `λ + adder ≤ VOLL` and applies the OBDRR048
multi-step floor. Parameters are `ScenarioConfig` fields with published defaults
(`ordc_voll`, `ordc_mcl_mw`, `ordc_lolp_mu_mw/sigma_mw`, `ordc_lolp_shift_sigma`).
Measured backcast overlays (`ercot_rtordpa_overlay_series`,
`ercot_dam_as_overlay_series`) are scoped to the ORDC regime (off in RTC+B, 2026+).

### NYISO RCPF (`rcpf.py`)

Replicates NYISO's Reserve Constraint Penalty Factors — nested reserve-demand
curves where penalties **stack** as reserves fall deeper into shortage.
`reserve_demand_price` is the piecewise-linear curve per product;
`rcpf_adder` sums system-wide products (10-min spin ⊂ 10-min total ⊂ 30-min total);
`locational_zone_adders` adds nested regional curves (NYC ⊂ SENY ⊂ East ⊂ NYCA).

## 5.7 Policy constraint extension point (`constraints.py`)

`get_active_policy_constraints(config, year)` returns a list of LP constraint rows
for active policies. It is currently a placeholder (returns empty) — the wiring
point for future NOx caps and similar system-wide constraints. The RPS constraint
is wired directly in `dispatch.py` rather than here.
</content>
