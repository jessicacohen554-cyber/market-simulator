# Market Simulation Model — Methodology & Build Specification

**Purpose:** Methodology specification for the LP-based electricity market dispatch model. This document governs the model’s mathematical formulation, computational patterns, scenario architecture, and performance requirements. It is the primary reference for how the model works; where this document and the code disagree, the **code is the source of truth** — open a `/sync-docs` pass to reconcile.

**Scope:** Multi-ISO hourly dispatch over a 2026–2050 forecast trajectory, with a historical-backcast mode for calibration. Six ISOs are registered in `config/iso_configs.py` — ERCOT (7 zones, 6 carry load), CAISO (3 zones + WECC import node), PJM (8 zones), MISO (6 zones), NYISO (5 zones) and NEISO (4 zones + HQ import node) — sharing one ISO-agnostic LP. ERCOT is the fully-calibrated reference; the others have topology and plant-to-zone assignment but varying data/backcast maturity (see `docs/multi-iso/`). Parameterized scenario system supporting batch sweeps and single custom runs.

**Forecast vs. backcast.** The model is fundamentally a **forecasting** tool (2026→2050). A *backcast* mode reruns a historical weather year against actuals (EIA-930, CAMPD, eGRID, EIA-923) to calibrate parameters. The switch is the explicit **`ScenarioConfig.mode`** field (`"forecast"` default / `"backcast"`, Tier 0) — never inferred from other parameters (it used to ride on `gas_price_override`, which wrongly flipped any pinned-gas forecast sensitivity into backcast behavior). Several mechanisms — historic outage overlays, F923 delivered fuel prices, **same-year** plant-specific CEMS emission rates, weather-year pinning — are **backcast/calibration devices only**; forecast runs use the statistical/parametric models (forecast-year CO2 rates for existing units are instead *derived from* multi-year CAMPD history, §3.3 — a measured input, not a same-year overlay). This distinction is called out throughout; do not conflate the two.

**Runtime:** Python 3.11+. Solver: HiGHS via `highspy`. No Pyomo, no PuLP, no scipy.optimize.

> **As-built note (reconciled with code).** This spec was originally written at Phase 0 as a pure-LP, two-ISO design. The model has since grown: an opt-in three-solve **unit-commitment** layer (still LP, not MIP — see §1.6), a **CAMPD per-plant binning** fleet representation with tranche-based rising offer curves (now the ERCOT default — see §3.3), config-driven retirement plus a **CCS-retrofit** pathway (§5), forecast/backcast **outage modelling** (§1.7), endogenous **EAC/REC** attribute credits, hydro monthly energy budgets, and five additional ISO topologies. The sections below reflect the as-built methodology.

-----

## 1. LP Formulation

### 1.1 Decision Variables

For a single ISO, single year (8,760 hours):

|Variable    |Dimensions        |Description                 |
|------------|------------------|----------------------------|
|`P[g,t]`    |generators × hours|Thermal dispatch (MW)       |
|`W[z,t]`    |zones × hours     |Wind dispatched (MW)        |
|`S[z,t]`    |zones × hours     |Solar dispatched (MW)       |
|`Chg[s,t]`  |storage × hours   |Storage charge (MW)         |
|`Dis[s,t]`  |storage × hours   |Storage discharge (MW)      |
|`SOC[s,t]`  |storage × hours   |State of charge (MWh)       |
|`Flow[l,t]` |links × hours     |Transmission flow (MW)      |
|`Slack[z,t]`|zones × hours     |Unserved energy (MW)        |
|`Dump[z,t]` |zones × hours     |Overgeneration absorbed (MW)|

Renewables are **decision variables on the LHS of the energy balance**, not netted from demand. This is critical — the LP decides how much renewable generation to dispatch. Curtailment = potential minus dispatched.

The dump variable absorbs overgeneration in hours where minimum generation (must-run nuclear with `Pmin > 0`, storage mid-discharge) exceeds demand. With negative-MC renewables (e.g., wind receiving PTC production credits), the LP could otherwise face infeasibility or game production credits by overproducing credited energy just to collect the subsidy on curtailed power. The dump variable makes the LP always feasible and its cost structure prevents credit gaming.

### 1.2 Objective Function

Minimize total system cost:

```
min  Σ_g Σ_t  mc[g,t] × P[g,t]
   + Σ_z Σ_t  0 × W[z,t]  +  0 × S[z,t]        # zero marginal cost
   + Σ_s Σ_t  ε × Chg[s,t] + (ε − eac_storage) × Dis[s,t]   # tiebreaker, less any storage attribute credit
   + Σ_z Σ_t  VOLL[z] × Slack[z,t]
   + Σ_z Σ_t  dump_cost × Dump[z,t]
```

The wind/solar terms are written as zero-MC here for clarity, but in code each renewable carries its own `mc` (often *negative* once IRA production credits apply — see §1.5/§1.4). Storage discharge carries the tiebreaker `ε` less any exogenous storage attribute credit (`eac_storage`), so a credited storage technology is nudged to deliver rather than sit idle.

Where `mc[g,t] = heat_rate[g] × fuel_price[g,t] + vom[g] + emission_rate[g] × carbon_price[t] + nox_rate[g] × nox_price[t] + <other adders>`

`dump_cost = max(ε, -min(wind_mc, solar_mc) + ε)`. When renewables have zero MC, dump_cost = ε (negligible). When renewables have negative MC (e.g., wind with PTC = -$26/MWh), dump_cost = $26.001/MWh — just above the absolute value of the production credit. This ensures the LP never profits from overproducing credited renewables into the dump.

The default wind dispatch offer is the FLAT `-ira_ptc_wind` on every MW while the credit is active (`policy.ira.compute_dispatch_credits`; solar's ITC is not production-linked, so its offer is $0). The optional `wind_ptc_vintage_offers` gate (ScenarioConfig, default off — ERCOT-65) scopes that credit to the vintages actually inside their 10-year §45 window: the offer becomes the per-zone-month `-PTC_statutory(year) × eligible_share[z, month]`, with the eligible share measured from EIA-860 vintages (`data.renewables.wind_ptc_eligible_monthly_share`) and the statutory per-year credit in `constants.WIND_PTC_STATUTORY_USD_PER_MWH`. `wind_mc`/`solar_mc` accept `(n_zones, T)` arrays, and the dump-cost guard follows the array minimum, so the scoping can only shrink the guard. Probe-adjudicated dispatch-inert on ERCOT 2023 (the wind bid's level never changes dispatch while every alternative supply is dearer); kept as recorded structure, not a keeper mechanism — diagnosis §9.

The marginal cost vector is assembled from parameters. Every cost component is a named parameter (Tier 1 or Tier 2). No hardcoded values in the cost calculation.

Storage tiebreaker `ε` = 0.001 $/MWh. Prevents degenerate solutions where the solver charges and discharges simultaneously. This is a standard trick — document it but don’t make it configurable.

### 1.3 Constraints

**Energy balance (per zone z, per hour t):**

```
Σ_{g∈z} P[g,t] + W[z,t] + S[z,t] + Σ_{s∈z} Dis[s,t] - Σ_{s∈z} Chg[s,t]
  + Σ_{imports to z} Flow[l,t] - Σ_{exports from z} Flow[l,t]
  + Slack[z,t] - Dump[z,t]
  = Demand[z,t]
```

The **dual variable on this constraint = zonal price ($/MWh)**. This is the model’s primary price output.

**Generator bounds:**

```
Pmin[g] ≤ P[g,t] ≤ Pmax[g] × availability[g,t]
```

Where `availability[g,t] = (1 - EFORd[g]) × seasonal_factor[g,month(t)]`. Must-run units have `Pmin > 0`.

**Renewable bounds:**

```
0 ≤ W[z,t] ≤ wind_cf[z,t] × wind_capacity[z]
0 ≤ S[z,t] ≤ solar_cf[z,t] × solar_capacity[z]
```

Capacity factor profiles sourced from EIA Hourly Grid Monitor (actual generation / installed capacity). These contain ~5% embedded historical curtailment — accepted as a known conservatism. The LP produces its own endogenous curtailment on top.

**Storage dynamics:**

```
SOC[s,t] = SOC[s,t-1] + η_chg[s] × Chg[s,t] - Dis[s,t] / η_dis[s]
0 ≤ SOC[s,t] ≤ energy_cap[s]
0 ≤ Chg[s,t] ≤ power_cap[s]
0 ≤ Dis[s,t] ≤ power_cap[s]
SOC[s,0] = SOC[s,8759]          # cyclic boundary
```

The SOC lower bound is optionally raised per unit-hour by a measured
ancillary-service sustain floor (`build_variable_bounds(storage_soc_min=…)`,
`dispatch.py`): under `caiso_storage_as_reservation` (GATED, default off,
backcast) CAISO battery SOC is floored at the tariff 30-minute sustain of the
measured spin/non-spin award and the battery power cap is derated by the
measured upward award (`model/storage.py::reserve_caiso_storage_as_power`,
the ERCOT `storage_as_commitment` pattern). The caiso-74 probe measured this
reservation **ex-ante inert** on CAISO's zone-aggregate fleet (the LP
discharges 3.7–6 GW below the nameplate cap), so it is not part of any keeper
recipe — see `results/calibration/FINDING-caiso74-storage-as-reservation-2026-07-11.md`.

No hard cycling-limit constraint, but cycling is no longer free: beyond the ε tiebreaker, each storage unit's discharge slot can carry a per-unit dispatch cost (`StorageUnit.vom` → `build_cost_vector(storage_discharge_cost=...)`, `model/dispatch.py`). Two reduced-form throughput costs use it, both standing in for real economics the energy-only LP otherwise ignores (cycling degradation plus ancillary-service/reserve opportunity cost): pumped storage *can* carry a per-ISO calibrated adder (`resolve_pumped_storage_dispatch_adder`, `constants.PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO`), though that registry is currently **empty** (`{}`) so every ISO resolves to 0.0 — the former PJM $10/MWh adder was retired per non-negotiable rule #12 (it had been fitted to a *mis-measured* residual; the in-code comment at `constants.py` documents the round-trip-loss vs. gross-discharge measurement error in full), and grid batteries carry `ScenarioConfig.battery_dispatch_adder` (Tier 3, default 0; the ERCOT backcast keeper sets $10/MWh, landing 2025 battery discharge within −1.5% of the EIA-930 measured 5.44 TWh where the un-priced LP over-cycled +48% — see `docs/calibration-log.md`, ERCOT E2 entry). The original "flag for future sensitivity if unrealistic cycling appears" fired and was resolved by these adders. Both solve paths (forecast `runner.py` and backcast `scripts/run_calibration.py`) pass `storage_discharge_cost=storage.vom`, so the throughput adders are active in all dispatch modes.

**Perfect-foresight limitation (known, accepted for now).** The full horizon is solved as one LP, so storage sees the entire year's prices at once and charges/discharges at the globally optimal hours its energy cap permits. A real operator has only ~day-ahead foresight and an imperfect price forecast, so the model is an *upper bound* on realized arbitrage and tends to over-flatten net load — which, in a backcast, can be absorbed into the thermal offer-curve parameters being calibrated against CAMPD. The `SOC ≤ energy_cap` bound keeps this small for the short-duration (≈4 h) li-ion fleet that dominates the 2023 backcast — such a battery physically cannot shift energy across days or seasons, so its only foresight advantage is picking the best in-day hours. The error grows with long-duration storage (12 h+, flow, CAES, iron-air).

Standard ways production-cost models bound storage foresight, cheapest-to-most-faithful:

1. **Daily/weekly SOC cycling caps** — force SOC back to an anchor each day (or cap daily energy throughput). Cheapest: keeps the single-LP structure, just adds rows. Kills cross-day arbitrage but leaves in-day foresight perfect. Good enough while the fleet is short-duration.
2. **Rolling (receding) horizon** — the PLEXOS/GridView/PROMOD default. Solve overlapping windows (e.g. 24–48 h with a look-ahead tail), fix the first day's decisions, carry end-of-window SOC into the next window. Caps foresight at the window length; the look-ahead tail stops the battery draining to zero at the artificial boundary. This is the most realistic option that stays deterministic, and the natural upgrade if/when LDES enters the fleet (the annual cyclic boundary becomes a per-window carried SOC).
3. **Day-ahead + real-time two-settlement** — commit on a forecast over ~24–36 h, then re-dispatch against actuals with limited foresight; captures forecast *error* explicitly. More faithful, more machinery.
4. **Price-taker arbitrage pass** — decouple storage: solve dispatch without storage → take the resulting prices → dispatch storage against them with a realistic foresight window → subtract from net load → re-solve (iterate). This is exactly the heuristic the *forward* new-entry screen already uses (`estimate_storage_revenue`), so the building block exists.
5. **Stochastic/robust optimization** — optimize over multiple price/load scenarios so no single known future can be exploited. The textbook-correct answer to foresight, rarely used in large PCMs because of cost.
6. **Empirical haircut** — accept perfect foresight, then derate storage output/efficiency to a fraction (≈80–90 %) of the theoretical-optimal spread. A pure calibration fudge, but common and cheap.

For this model, the pragmatic path is (1) as a guard once durations lengthen, escalating to (2) if a backcast shows storage materially mis-shaping net load. Option (1) is implemented today as the `storage_daily_cycling` config flag, honored by **both** the backcast script (CLI: `run_calibration_full.py --storage-daily-cycling`) and the forecast runner (`runner.py` passes `storage_daily_cycle_hours=24` to every solve when the flag is set — earlier only the backcast path was wired, so forecast runs silently kept full-year foresight regardless of the flag): when on, each storage unit's SOC must return to its day-start level every 24 h, so storage cannot bank energy across days and its arbitrage is bounded to within-day spreads. Off by default (annual-cyclic, full foresight).

**Transmission:**

```
-TTC[l] ≤ Flow[l,t] ≤ TTC[l]    # bidirectional (the default)
0 ≤ Flow[l,t] ≤ TTC[l]          # one-way link (TransferLink.is_bidirectional=False);
                                # a pair of opposite one-way links encodes an
                                # asymmetric interface rating (MISO's RDT 3,000
                                # N→S / 2,500 S→N). Wired via
                                # transmission.get_link_bidirectional_array →
                                # dispatch link_bidirectional in both runners.
```

**Aggregate interface groups** (`InterfaceLimit`, `iso_configs.py`): one row
per group per hour caps the **signed sum** of member-link flows. Each listed
``(from, to)`` pair pulls in EVERY link joining that zone pair — matching
orientation with sign +1, reversed with −1 — so the sum reads as the net
corridor flow in the listed direction, and an opposing one-way pair (the RDT)
contributes ``flow(a→b) − flow(b→a)`` from one listed pair. ``cap_mw`` bounds
the positive direction; the optional ``reverse_cap_mw`` sets an asymmetric
reverse bound (import CIL vs export CEL); caps may be scalars or hourly
``(T,)`` vectors (seasonal envelopes). Implemented in
`transmission.build_interface_groups` → `dispatch._build_interface_rows`.

The topology (zones, load shares, links, TTCs) is per-ISO data in `config/iso_configs.py`; the LP itself is ISO-agnostic and reads `n_zones`, `n_links`, the node–link `incidence` matrix, and per-link `ttc`. Current topologies:

- **ERCOT** — 7 zones (West, Panhandle, North, Northeast, Houston, South_Central, South; Panhandle carries 0 load), 9 links, with cited inter-zone TTCs. The reference calibration.
- **CAISO** — 3 in-state zones (NP15, ZP26, SP15) split on Path 15 / Path 26, **plus** a WECC import/export node (see below); 4 links + 1 interface limit.
- **PJM** — 8 aggregated zones (`PJM_ComEd`, `PJM_AEP_Ohio`, `PJM_ATSI`, `PJM_West_APS`, `PJM_Central_PA`, `PJM_Dominion`, `PJM_EMAAC`, `PJM_SWMAAC`), 11 links, rolling up PJM's 20+ transmission zones onto the chronic west→Mid-Atlantic congestion corridors.
- **MISO** — 6 zones drawn as whole EIA-930 sub-BA (LRZ-union) partitions — `MISO-West` (LRZ 1), `MISO-Plains` (LRZ 3+5), `MISO-Illinois` (LRZ 4), `MISO-Indiana` (LRZ 6), `MISO-East` (LRZ 2+7), `MISO-South` (LRZ 8+9+10) — 8 links: 6 deliberately non-binding internal pipes plus the RDT one-way contract-path pair (3,000 MW N→S / 2,500 MW S→N) attached to `MISO-Plains`. Internal congestion is carried by per-zone directional CIL/CEL `InterfaceLimit` groups from the MISO LOLE Study Reports (static PY2025-26 summer caps in config; backcasts replace them with per-season hourly vectors via `transmission.build_miso_deliverability_groups`). See `docs/multi-iso/miso-zonal-refinement-scope.md`.
- **NYISO** — 5 zones (Upstate_West, Capital_Hudson, Lower_Hudson, NYC, Long_Island) with nested downstate import cutsets.
- **NEISO** — 4 load zones (North, Central, Boston, Connecticut) **plus** an HQ import node; 7 links.

CAISO's WECC import/export node is modeled as **pseudo-generators on a stepped supply curve**:

- Import tranches: 3–4 blocks with increasing marginal cost and MW limits (e.g., PNW hydro cheap/limited, Desert SW CCGT mid, Desert SW CT expensive). These are `P[g,t]` variables assigned to the WECC “zone” with their own cost and capacity.
- Export: allow CAISO to push power to the import node at a cost of zero or small negative (represents dumping surplus solar).
- Aggregate limit: ~12–15 GW import, ~5 GW export. Derive from EIA-930 interchange data.

**Forward per-hub seam (forecast-native, 2026-06).** The static stepped ladder is a backcast fit. For a forecast the WECC node is split into the two real corridors (COI/Path-66 → Malin/WECC_PNW → NP15; Path-46/WOR → Palo Verde/WECC_DSW → SP15), each priced by the **reference-price interface** (the same construction PJM/MISO use): `per-hub price = (henry_hub[year] + gas_basis) × marginal_heat_rate × load_shape`, with the solar-driven desert-SW on a **net-load** shape so its midday price dips with the solar glut. The corridor import cap is a forward ATC = `TTC × posted-ATC fraction × forward solar derate` (not the measured p95 flow). Flags `caiso_intertie_reference_price` / `caiso_corridor_atc_forward` (require `caiso_per_hub_intertie`); the measured WECC hub LMP + p95 envelope are retained only as the backcast realization the formula is validated against. See `docs/forecast-methodology-gaps-2026-06.md` G8 and `data/neighbor_price.caiso_hub_reference_price` / `model/transmission.forward_corridor_atc_envelope`.

**NEISO measured seam ladders (2026-07-06, audit C-6 closure).** NEISO's static ladders are no longer residual-fitted: `IMPORT_TRANCHES[_BY_YEAR]["NEISO"]` / `EXPORT_TRANCHES[_BY_YEAR]["NEISO"]` are derived by a frozen formula (`scripts/derive_neiso_import_tranches.py`) from measured data only — per-seam Q-Q duration coupling of the measured ISO-NE DA hub LMP with the measured EIA-930 per-seam flows (HQT/NBSO/NYIS), rung capacities at the measured p98 per-seam depth (Highgate carved at its published ~225 MW rating), NYISO proxy-bus anchors (`NYISO_HQ` = HQ's opportunity cost, `NYISO_NPX` = NY-side interface price) reported per rung, and export sinks clamped below the cheapest import rung (the pooled `HQ_import` node cannot host wheel-through counterflow — rule #14 reconciliation). Backcast years resolve year-keyed ladders on BOTH sides of the node (`EXPORT_TRANCHES_BY_YEAR` mirrors `IMPORT_TRANCHES_BY_YEAR` through `get_interchange_spec` / `build_export_sinks`, interchange_config.py); forecast years carry the pooled 2023-2025 ladder. Rule-23 frozen: re-derive only when the source data extends.

**MISO measured seam ladders (2026-07-07, audit C-6 closure for MISO — the G-23-residual import-starvation fix).** Under `ScenarioConfig.miso_seam_measured_ladder` (backcast opt-in), every band of MISO's reference-price seams (PJM/SPP/South, import + export) is repriced by `transmission.inject_miso_seam_ladder_prices` to the measured per-year Q-Q ladder in `interchange_config.MISO_SEAM_LADDER_BY_YEAR` — the same NEISO construction (`scripts/derive_miso_seam_ladders.py`) on the existing 8-band grid: band *k*'s price is the measured MISO **DA** hub LMP quantile whose exceedance duration equals the measured EIA-930 duration of the seam flowing deeper than the band's midpoint (export side mirrored); no hurdle is added (the revealed thresholds embed delivery costs). Band capacities and the measured (month × hour-of-day) seam envelopes are unchanged. Why: the measured PJM+IESO seam flow is a firm/scheduled base — importing in ~98–100% of hours, hourly-uncorrelated with the spread (r ≈ +0.06), 2025 mean RT spread $0.00 while 28 TWh flowed — which the hurdle-gated spot-spread formula structurally deletes in a zero-spread year (`docs/multi-iso/miso-import-starvation-rootcause-2026-07.md`). The ladder never forces flow (contrast the rejected `miso_firm_import_floor` pin): every band clears economically against the model's own hourly price. Forecast years keep the gas-elastic reference-price formula (the `hr_by_year` two-track design; the pooled 2023–2025 ladder printed by the derive script is the forward story). Rule-23 frozen: re-derive only when the source data extends.

**Non-negativity:** All dispatch, charge, discharge, slack, dump, SOC ≥ 0. Flows can be negative (bidirectional) or modeled as two non-negative variables per link.

### 1.4 Policy Constraint Extension Point

Some policy parameters are **cost adders** (change the objective vector): carbon price, NOx price, SO2 price. These are handled by the marginal cost assembly — no structural change to the LP.

Some policy parameters are **constraints** (add rows to the LP): CO2/NOx emission mass caps, RPS minimums (minimum % clean generation), potentially others.

**Carbon: one channel, two price sources.** Every carbon path routes through the same `emission_rate[g] · m[g] · p_allowance` channel, where `m[g] ∈ [0,1]` is a per-generator membership weight (`m_zone[zone_idx[g]]`, the share of the generator's zone inside the program's member states; import/external nodes = 0). The unified resolver `policy/cap_and_trade.py::resolve_carbon_program` returns the membership plus **exactly one** price source: the exogenous **adder** (`p_allowance` known ex-ante — measured backcast auction price, or projected forecast program price) folded into MC, or a **mass-cap row** whose LP dual *is* `p_allowance`. This is deliberate (see §5's carbon note and `docs/handoffs/emissions-mass-cap-plan-2026-07.md`): RGGI/CARB clear in a banked, multi-sector market this power model does not contain, so their faithful representation is the *adder*; the endogenous row dual is a **power-sector, no-bank scenario** allowance price (EPA 111(d)/CSAPR or a user cap), never fitted to the observed $/ton. The registry `CAP_AND_TRADE_PROGRAMS` sets CAISO→CARB, NYISO→RGGI(NY), NEISO→RGGI(6 NE states) with `m_zone≡1` on load zones; PJM→RGGI with a fractional membership shipped OFF pending the EIA-860→state crosswalk; ERCOT/MISO have no program. Forecast RGGI/CARB now carries the *projected* program price (the last realized clearing price escalated at the published CARB 5%+CPI / RGGI CCR 7%/yr floor-band rate) instead of zero — the EM-6 seam fix.

**CO2 mass cap (active, GATED default off).** When `mass_cap_enabled` and a power-sector tonnage budget is configured, `_build_mass_cap_rows` appends one inequality per cap:

```
# CO2 mass cap (annual)
Σ_{g∈members} Σ_t  m[g] × emission_rate[g] × P[g,t]  ≤  cap_tons

Dual on this constraint = endogenous allowance price ($/tCO2),
reported as DispatchResult.co2_cap_price = −λ.
```

Import-node and inter-zone flow columns get a zero coefficient (in-region emissions only), so the leakage channel — a binding cap lifts the in-region price and pulls in uncapped imports up to the transmission limit — is *represented*, not suppressed. The block is appended after the import-node rows and immediately before the RPS row (end-anchored dual layout `[ … | mass_cap | rps | reserve ]`). No banking/borrowing across years: each year's cap binds independently (the sequential one-pass year loop forbids the multi-year coupling a true bank needs), so the dual is an upper bound on a banked price in a tight year and ~0 in a loose year. Budget schedules are landed as cited constants (`CARB_ALLOWANCE_BUDGET` in MMT CO2e; the regional `RGGI_STATE_CO2_BUDGET` in short tons), mirrored by the raw `carb-cap-schedule` / `rggi-co2-budgets` intake datatypes; `_power_sector_cap` sources the row's `cap_tons` (metric tonnes) from an explicit `config.mass_cap_tons` or, failing that, the published budget for the year (unit-converted). These region-/economy-wide budgets vastly exceed a single ISO's power-sector emissions, so on a real ISO the row is slack and its dual ~0 — the faithful power-sector, no-bank result; the binding mechanism is validated on a trivial fixture. No 2022/2026 rows are landed (holdout quarantine), so those years leave the row inert.

**Build rule:** Every policy parameter in the config is tagged `kind: "adder"` or `kind: "constraint"`. The LP builder checks for active constraint-type policies and appends rows.

**RPS (active):** When `rps_enabled` is set and the ISO has an RPS floor for the year, the dispatch LP appends one annual constraint row requiring wind, solar and nuclear generation to reach `rps_target` of total demand:

```
# RPS constraint (annual)
Σ_z Σ_t (W[z,t] + S[z,t]) + Σ_{g∈nuclear} Σ_t P[g,t]
    ≥ rps_target × Σ_z Σ_t Demand[z,t]

Dual on this constraint = REC price ($/MWh), which feeds into
the economic new entry screen as additional clean energy revenue.
```

The constraint creates a shadow price that raises clean revenue and compresses thermal margins, so clean additions and thermal retirements are driven entirely through the economic screens — no force-build in capacity evolution.

```
# NOx cap (same builder as the CO2 mass cap, nox_rate coefficient)
Σ_g Σ_t nox_rate[g] × P[g,t] ≤ nox_limit                              # annual
```

The CO2 mass cap above is the first realized constraint of this family; a NOx mass cap is the same `_build_mass_cap_rows` builder with `nox_rate` in place of `emission_rate` and is a trivial follow-on (out of the current scope). `policy/constraints.py::get_active_policy_constraints` is the wiring point that surfaces these specs to the dispatch builder.

### 1.5 Emerging Technologies

Emerging generation and storage technologies are a **parameter and data-layer extension**, not an LP formulation change. Every new technology enters as either a `Generator` (thermal dispatch) or a `StorageUnit` (charge/discharge/SOC) reusing the existing LP variable structure. Each technology becomes a new-entry candidate only once the simulation reaches its configured availability year.

#### 1.5.1 Hydrogen Dispatch Model

Hydrogen is **not modeled as storage**. H2 turbines (`hydrogen_ct`, `hydrogen_ccgt`) are thermal generators whose fuel cost is *derived* from renewable electricity economics rather than an exogenous price path:

```
h2_fuel_cost_$/MMBtu = min(wind_LCOE, solar_LCOE) / η_electrolyzer / 3.412
```

where 3.412 MMBtu = 1 MWh. The `min()` picks whichever renewable is cheapest in that ISO-year; dividing by the electrolyzer efficiency converts electricity to hydrogen; dividing by 3.412 converts $/MWh to $/MMBtu. Electrolyzer efficiency is a Tier 2 parameter that improves over time (linear interpolation between the 2026, 2035 and 2045 milestone years). This formulation:

- tracks Wright's-Law cost declines in renewables automatically — cheaper renewables mean cheaper hydrogen;
- needs no exogenous hydrogen price path;
- avoids circularity — the model never prices its own fuel.

H2 turbines then dispatch on `heat_rate × h2_fuel_cost` like any thermal unit. Direct CO2 emissions are zero (green hydrogen); NOx is non-zero because hydrogen burns hot. The IRA §45V clean hydrogen production tax credit ($3/kg ≈ $26/MMBtu) is applied as a fuel-cost reduction in the new-entry LCOE screen and expires after `ira_h2_45v_last_year` (default 2027).

#### 1.5.2 CCUS Dispatch Model

Carbon capture (`gas_cc_ccs`) is a **variant of the base gas CC plant**: it burns the same natural gas but carries a higher heat rate (parasitic capture load), a higher VOM (solvent costs), a reduced emission rate (capture rate applied), and a transport+storage cost for captured CO2. The marginal cost is:

```
mc = base_heat_rate × heat_rate_penalty × gas_price
   + base_vom + vom_adder
   + base_co2_rate × (1 − capture_rate) × carbon_price     # residual emissions
   + base_co2_rate × capture_rate × co2_transport_storage   # captured CO2 disposal
```

The captured-CO2 disposal term is a constant $/MWh and folds into the unit's VOM; the residual-emissions term is ordinary `emission_rate × carbon_price`, so standard marginal-cost assembly reproduces the formula with no special-casing. CCUS becomes **more competitive as carbon prices rise** — the residual term shrinks relative to the full carbon cost an unabated plant pays — and the model finds the carbon-price crossover endogenously. The IRA §45Q credit ($85/tCO2 stored) enters the new-entry LCOE screen as a variable-cost offset and expires after `ira_ccus_45q_last_year` (default 2032). (The IRA expiry is **not** a single `ira_expiry_year` switch — it is split per credit: `ira_wind_solar_last_year` 2027, `ira_other_clean_last_full_year` 2028 with phase-out to `ira_other_clean_phaseout_end` 2033, `ira_h2_45v_last_year` 2027, `ira_ccus_45q_last_year` 2032.)

#### 1.5.3 Enhanced Geothermal

Enhanced geothermal systems (`geothermal`, EGS) enter as zero-fuel dispatchable baseload generators with a high capacity factor (~90%). They are **not intermittent** — they do not follow wind/solar CF profiles. They can provide flexibility, turning down to a `pmin` of ~20% of rated capacity. A steep learning curve is assumed (analogous to early solar). Geothermal earns the same zero-emission production tax credit as wind.

#### 1.5.4 Offshore Wind

Offshore wind (`offshore_wind`) is a **separate renewable category** from onshore wind: higher and less variable capacity factors, higher costs, and distinct zone eligibility. By default it is a candidate only in CAISO (Pacific-coast floating); the Gulf-coast ERCOT potential is left as a future sensitivity. It is modeled as a **zero-marginal-cost `Generator`** (Option A), rather than as a new LP variable class — the LP dispatches it like any other generator and curtailment falls out of the capacity bound. This keeps the LP structure unchanged.

Offshore wind capacity factors are derived from the onshore wind profile for the same ISO by applying a physical smoothing window (default 6 hours, reflecting reduced ocean gustiness), a minimum CF floor (default 8%, reflecting persistent offshore resource), and rescaling to the target annual-average CF. This preserves the real temporal patterns (diurnal, synoptic, seasonal) from the EIA-930 data while producing a less variable, higher-average profile that matches offshore wind's physical characteristics. The derived profile is injected into the generator's hourly availability array, so dispatch varies realistically across hours.

#### 1.5.5 Additional Storage Durations

Three long-duration storage technologies — 12-hour lithium-ion, vanadium-redox flow batteries and adiabatic compressed-air — are added to the storage technology menu. They use the **same LP formulation** as the existing storage units (`power_cap`, `energy_cap`, `eta_chg`, `eta_dis`); only their economics differ, which drives different dispatch patterns.

### 1.6 Unit Commitment — Three-Solve LP Heuristic

The original spec said "no unit commitment." That changed: pure merit-order LP left fast-cycling units (notably ERCOT gas CT) badly under-dispatched because a single LP solve has no notion of start-up cost or minimum run length. The model now has an **opt-in commitment layer** (`model/commitment.py`, enabled by `ScenarioConfig.commitment_enabled`, default `False`). It stays **pure LP — there is no MIP and no binary variables**; commitment is a heuristic screen applied *between* LP solves by zeroing a unit's availability in hours it is decommitted, then re-solving. Three solves per year:

- **P0 (base):** solve with base marginal cost `mc_base = fuel + VOM + carbon + NOx + SO2` (the SO2 term defaults to 0; no start-up markup). Measure each unit's realized run lengths by month.
- **P1 (bid):** solve with `mc_bid = mc_base + start-up markup`, where the per-unit monthly markup amortizes `start_up_cost / avg_run_length` (ST_GAS spreads its start-ups across May–Sep). Clearing prices now embed cycling cost.
- **P2 (commitment, when enabled):** screen CC/CT units for profitable *runs* of in-merit hours (`P1_price[zone] − mc_base > 0`), then keep a run committed only if it clears all of:
  - a **start-up IRR hurdle** — the run's weighted margin exceeds `start_up_per_MW × (1 + commitment_irr_hurdle)` (default 7%);
  - **min-run / min-down** filters (drop runs shorter than the minimum; merge runs separated by less than the minimum down-time);
  - a **storage-weighted margin discount** — in hours when storage is net-charging the zone, the margin is discounted so a unit is not kept on merely to feed speculative battery charging, with a deep charging trough breaking the run.

  Coal is either pinned to its P1 dispatch (legacy/unscreened bins) or screened with a long (≈36 h) minimum run. An **adequacy backstop** restores decommitted units to their P1 fractions in any zone-hour where the screen would otherwise make P2 unable to reproduce P1 thermal output — commitment can never introduce unserved energy.

Commitment is off by default and used primarily for ERCOT calibration; the screen reads *base* MC (not bid MC) so start-up cost is not double-counted in the retirement/new-entry economics that consume these prices.

**P2 is ARCHIVED (per CLAUDE.md "Dispatch & Commitment").** The P2 pass described above is a legacy artifact, kept intact only as a last resort — it is hidden from the calibration CLI and its flags (`--commitment`, `--ercot-as-aware-commitment`, `--run-p2`, `--no-coal-p2`, `--persist-p2-state`, `--class-commitment-overrides`) hard-error unless `--enable-legacy-p2` is passed (`scripts/run_calibration_full.py`, `scripts/run_calibration.py`). No keeper uses it, and it is not part of any default or recommended configuration. The CAISO RA must-offer bridge formerly described as running through P2 is now applied P1-native (§1.6 above still reflects the machinery `pipeline/commitment.py::run_commitment_pass` retains for the `--enable-legacy-p2` path, not the production path).

**Startup CO2 (reporting-only, default off).** The P1 markup above amortizes start-up *cost* into the bid — it never adds a start-up *emissions* term to the dispatch LP. A separate, purely additive reporting figure, `results/emissions.py::startup_co2_tons` (`model_starts × measured startup_co2_kg` per plant), is computed only when `ScenarioConfig.startup_co2_reporting` is set (default `False`, Tier 3) and appended to the bundle's `plant_hourly_fit` output; it never feeds back into dispatch or pricing. Measured materiality is 0.015-0.018% of annual fleet CO2 (bounded ≤0.2% even at a 10× cycling error), which is why it ships off by default rather than as a live correction (EM-5, `docs/handoffs/emissions-co2-rate-plan-2026-07.md` §3, §5 R6).

**P1 — the no-commitment solve — is the model's MAIN run.** It is the production path, the forecast path, and what every keeper is scored on; P2 exists only as an opt-in diagnostic/screening layer and **never runs unless explicitly enabled** (`commitment_enabled`, or the ISO-specific opt-in `ercot_as_aware_commitment` — `caiso_ra_mustoffer` no longer triggers P2; it is applied P1-native, see below). Nothing in the model turns P2 on by default.

**P1-native commitment bridges (the production commitment-state mechanisms).** Two gated mechanisms inject a committed-state `min_gen` floor *before* the single scored P1 solve, detected from the model's own base-cost **P0** run pattern (`pipeline/commitment.py`, injected at the P0→P1 seam in `pipeline/solve.py::run_energy_solve`) — forward-derivable and condition-responsive by construction, no measured generation enters: **(a) the CAISO RA must-offer bridge** (`caiso_ra_mustoffer`, CAISO default-on — `caiso_ra_p1_floor_fleet`/`build_caiso_ra_p1_prep`, the midday-gap construction described under P2 above, now P1-native), and **(b) the ERCOT gas commitment bridge** (`ercot_gas_commitment_bridge`, default off, ERCOT-only — `ercot_gas_bridge_p1_floor_fleet`/`build_ercot_gas_bridge_p1_prep`): the same ISO-neutral detector (`model/commitment.py::caiso_ra_mustoffer_min_gen`) scoped to merchant gas-CC (`fuel_types=("gas_cc",)` — CT is physics-inert for the economic leg per the fast-start exclusion, ST_GAS is owned by its own drag mechanism), with `min_load_frac` = the measured ERCOT committed-CC LSL/HSL capacity-weighted p50 (0.574, 60-Day DAM disclosure 2023-2025, `ScenarioConfig.ercot_gas_bridge_min_load_frac`), the economic (≥ min-down) leg on the startup-restart inequality priced at the model's own P0 duals (`ercot_gas_bridge_startup`, default on with the gate) and bounded to one DA operating day (`ercot_gas_bridge_da_horizon`, default on — `DA_COMMITMENT_HORIZON_HOURS`). The CAISO startup-aware run screen is deliberately not exposed for the ERCOT bridge (dropped with cause — ERCOT-63, `docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §7). D-2 attribution ids: `ra_mustoffer_bridge` (7) and `gas_commitment_bridge` (17), each with a zero-forcing ablation entry and a cited D-4 window (`scripts/legitimacy_diagnostics.py`). The ERCOT bridge's hooks are built as a PAIR by `pipeline/commitment.py::build_ercot_gas_bridge_p1_preps` (the single-hook `build_ercot_gas_bridge_p1_prep` wrapper remains): when the companion gate `ercot_offer_surface_lowcurve_floorscoped` is on (ERCOT-64 — the measured committed-LSL bid applied via the `p1_bid_adjust_prep` seam ONLY in the bridge's own floored plant-hours; mutually exclusive with the tranche-wide `ercot_offer_surface_lowcurve` and hard-requiring the bridge, both fail loud), the bridge floor is computed ONCE per P0 result and shared by the fleet hook (the floor) and the bid hook (its hour mask), in both orchestrators. Probe verdict (ERCOT-64, 2026-07-13, diagnosis §8): the floor-scoped markdown is **provably inert** — the bridge floor clips at the committed tranche's own capacity on every bridged plant, so the tranche is exactly pinned in the markdown's whole window and its bid coefficient cannot move the LP solution or duals; both markdown variants stay default-off (the LSL price-side enumeration is closed; the committed-state inflexibility is carried by the bridge STATE alone).

A gated ERCOT variant (`ercot_as_aware_commitment`, requires the multi-product AS co-optimization) makes the opt-in P2 pass **commitment-state-aware for reserves**: the screen values a unit's AS revenue (the model's own P1 reserve duals × headroom) alongside energy margin, an AS-adequacy floor re-commits cheapest units up to the measured AS requirement, and the P2 reserve headroom is re-scoped by the commitment state — a decommitted plant's econ **and peak** tranches leave the shared-headroom RHS (`couple_peak`), online CTs join the synchronized (fast) product pool per-hour via the P2 availability, and offline quick-start capacity backs Non-Spin only through a reserve-only extra-cap term (`reserve_config.ercot_commitment_headroom_overrides`). A second gated ERCOT flag (`ercot_ecrs_conservative_deployment`) represents the published pre-reform ECRS deployment design on the ECRS demand curve — a **P1-level** mechanism (it changes the LP's reserve demand, no commitment pass involved): no price-based release from ECRS go-live (2023-06-10) through 2024-07-31 (a single demand step at the offer cap), reverting to the standing VOLL-anchored ramp from 2024-08-01 (see `docs/parameter-citations.md`, "ercot_ecrs_release_reform_*"). Both are default-off structural mechanisms. Probe verdict (`2026-07-02-ercot27-ordc-structure`, 2026-07-03 calibration-log entry): the 2023 scarcity-month improvement comes entirely from the **P1-level** structure (ECRS withholding + AS carve-outs); the AS-aware **P2 pass added no scarcity-month signal and only a broad all-month price elevation** (the exact-coverage adequacy-floor artifact) — it is not part of any recommended configuration. Dashboard scoring note: the run explorer scores a bundle's **primary** dispatch pass — P1 for every normal (P1-only) bundle, byte-identical to before; a P2-scored registration can only exist for a run that explicitly opted into a commitment pass.

### 1.7 Outage & Availability Modelling — Forecast vs. Backcast

A unit's hourly `availability[g,t]` multiplies its `Pmax`. Two regimes:

**Forecast (statistical — the default).** Availability `= 1 − WEFOR(age) − DERATE(age) − POF(shoulder only)`, from the per-plant-group `THERMAL_AVAILABILITY` table (`config/constants.py`):
- **WEFOR** (forced-outage rate) is flat year-round and escalates with age past an onset year.
- **Planned outages (POF)** are distributed across the year by a **historically-derived monthly maintenance shape** (`MAINTENANCE_MONTHLY_SHAPE`, `config/constants.py`) — a per-plant-group 12-month weight learned from the measured timing of spring/autumn maintenance in the CAMPD unit-outage extracts (all six ISOs, pooled — a forecast shape, *not* pinned to any one backcast year). Each group's weights are the planned-maintenance excess over its annual-minimum (forced-outage-floor) month, normalized to a month-length-weighted mean of 1, so the per-hour planned-maintenance derate is `POF · (shoulder_hours/8760) · w[group][month]`. Because the shape has a month-weighted mean of 1, the group's **annual POF budget (`POF · shoulder_hours`) is conserved exactly** — only its seasonal *distribution* is sharpened from the legacy flat five-month block to the measured curve (peaks Apr and Oct–Nov, ≈0 at the Jul/Aug summer peak, modest in winter). Applies in **forecast** mode (`ScenarioConfig.maintenance_monthly_shape`, default on); set it `False` to restore the legacy flat block over `_CC_SHOULDER_MONTHS = {3,4,5,10,11}`. Independently, in the **summer peak** (`{6,7,8,9}`) only a fraction (`_SUMMER_WEFOR_SHARE = 0.30`) of the forced-outage rate applies, with the displaced WEFOR redistributed into the shoulder, so firm capacity is available for the load peak. Derivation/verify: `scripts/derive_maintenance_shape.py`.
- **Seasonal capacity derate** (ambient): gas turbines lose ~10–12.5% of capacity in summer.
- Nuclear uses a monthly capacity-factor shape (NRC PRIS refuelling pattern), refuelling concentrated in spring/autumn.

The monthly maintenance shape is forecast-mode shaping (responds to forecast conditions through each group's `POF` budget) and is **distinct from the backcast overlay below** — it never reads a specific year's outage windows, only the pooled seasonal *shape*. Backcast runs (`outage_source == "historic"`) keep their measured overlay and are unaffected by the flag.

**Backcast (historic overlay — calibration only).** When a backcast config sets `outage_source == "historic"`, `data/outages.py` overlays *actual* sustained outage windows (CAMPD-derived, coal/CC plants, ≥48 h CF<5% gaps) onto the model's fixed 8760-hour clock, plus a unit-level derate from the ERCOT unit-outage extract and CAMPD partial-outage (CF-ceiling) plateaus. The statistical POF for overlaid groups is dropped (`coal_drop_pof`) to avoid double-counting. The family carries three gated companions: short (1-5 day) baseload-coal windows (`unit_outage_short_windows`), unit-grain partial-derate plateaus (`unit_partial_outage_windows`), the declared-event-window revealed derates (`unit_outage_maxgen_events` — CAMPD per-unit derates inside the `maxgen-events` registry's declared capacity-emergency windows only, class-agnostic, under the frozen identification guards of `scripts/derive_campd_maxgen_outages.py`: $150 DA in-merit certificate region-scoped, ±45-day capability basis with best-event-hour credit, disjointness vs the std/short extracts; the only channel that can carry the measured CT/CC event-window leg — built miso-69, default off, in no keeper recipe). The same registry also drives a *price-formation* companion outside the availability family: declared-window ELMP emergency-tier pricing (`maxgen_emergency_tier_pricing` — inside a registry window declared at Max Gen Warning or higher, the declared region's physical zones reprice the load slack from the ISO bid cap to min(voll, tier floor): $500 Tier 1 at Warning/Step 1, $1,000 Tier 2 at Step 2+, the SOM-footnoted ELMP emergency-supply offer floors; `data/maxgen_events.py`, the RBDC/zonal-ORDC curves are never edited and off-window the slack cost equals voll by construction — built miso-70, default off, backcast-only). **Forecast runs never use this overlay** — it exists to reproduce a specific historical year for calibration, and degrades gracefully to the statistical model when the extract is absent.

**Regulatory availability overlay — NYSDEC 227-3 (NYISO, `nysdec_peaker_rule_availability`, default off).** The DEC "peaker rule" (6 NYCRR Subpart 227-3) caps ozone-season (May 1–Sep 30) NOx from simple-cycle turbines in two phases (2023-05-01 / 2025-05-01); units whose compliance plan is ozone-season shutdown or reliability-only operation are unavailable to the energy market inside the window. The curated unit-level schedule (`data/raw/reference/nysdec-227-3-peaker-compliance.csv`, extracted from the NYISO Gold Book Tables IV-3..IV-6 across the 2023/2024/2025 vintages with per-unit citations) zeroes/derates each restricted unit's availability inside its effective windows (`data/outages.py:nysdec_peaker_restrictions`). Availability **only**, never an offer/price change — the same admissibility class as the CAMPD outage windows (an exogenous regulatory event with a forward story: the schedule extends through the 2030 NYPA small-plant phase-out), and unlike the historic overlay it is *not* gated on `outage_source` (the regulation binds in any mode). Units the NYISO STAR process designated to remain in operation past the compliance date (the Gowanus 2&3 / Narrows 1&2 barges, to 2027-05-01) are carried in the CSV for the audit record but never restricted.

**Fast-start tranche pricing (`tranche_startup_amortization`, + measured-run v3 `tranche_startup_measured_runs`, both default off).** The ISO-NE Order-825 / NYISO GT-hybrid fast-start pricing analogue: the fast-start-capable gas tranches (CT_PEAKER/CT_CHP econ+peak; the CC duct/quick-response peak band) carry the bin's NREL start cost, which `model/commitment.py:compute_monthly_markup` amortizes into the P1 bid — the fuel-price-invariant commitment-cost component of the real offer stack. v2 amortizes over each tranche's own P0 run lengths, which is circular when the offer level itself is wrong (too-cheap offers → long P0 blocks → ≈0 markup → the lever self-disables; the nyiso-44 probe finding). v3 (`tranche_startup_measured_runs`) instead uses the unit's **CAMPD-measured median start-to-stop run length** (`scripts/derive_campd_ct_run_lengths.py` → `data/raw/_processed-legacy/campd_ct_run_lengths_<ISO>.csv`, pooled 2023–25, ISO-class fallback) as the amortization-horizon **ceiling**: `markup = startup / max(1, min(P0_month_avg_run, measured_median))`, a month with no P0 runs amortizing over the measured horizon outright — the ex-ante expected-run basis real GT offers form on, with the endogenous run only ever *shortening* the horizon. The measured run length is a rule-#12-admissible measured market-behaviour parameter (same class as the CAMPD committed shares): it regenerates from the CAMPD pipeline for any vintage and re-derives only when its source data updates (rule #23). CC peak (duct) bands keep the v2 P0 basis — a duct burner's run is not a CEMS start-to-stop block.

> **Admissibility rule for measured data (claude.md Non-Negotiable Rule).** The outage overlay is the *canonical allowed* use of measured data: a unit outage is a **physical availability event** that enters as an input (`availability[g,t]`), is reproducible (the same window-detection logic runs on any year's CAMPD), and has a forward analogue (the roadmap statistical/historically-derived maintenance profile responds to forecast conditions). The discriminating test for any measured input is: *could the same quantity be produced for a forward year and respond to changed conditions?* Inputs that pass — outage windows, F923 delivered fuel prices, plant-specific CEMS emission rates, measured AS power reservations, temperature/net-load reliability-floor coefficients (§1.8) — are allowed even in backcast mode. **Forbidden** is feeding a measured *outcome* back to force the fit: pinning a unit to its observed CEMS generation (`ct_deployment_overlay`, `reliability_deployment_overlay`), an offset tuned to the price/volume residual (the former `ordc_reliability_deployment_mw`, **deleted outright 2026-07-04** per claude.md rule 26 — deprecated knobs that still parse are re-armable answer keys), or rescaling a potential so the model's *delivered* output lands on the actuals. Those have no forward analogue and are default-**off** diagnostic probes only — never keepers. The former per-plant EIA-923 must-run floor (`ct_mustrun_per_plant`) and CEMS deployment overlay (`ct_deployment_overlay`) are demoted to default-off diagnostic probes — they are measured-outcome floors with no forward analogue (the p97-CF ceiling used by the old reliability-floor mechanism is also removed). See `docs/backcast-measured-data-audit-2026-06.md` for the current compliance status.

### Calibration & Validation — cross-reference

This spec covers the LP formulation, commitment, and the forecast/backcast
outage-modelling split above; it does **not** cover how a backcast run is
scored, gated, or declared a keeper. For the calibration rubric (C1–C8),
holdout tiers (train/validation/locked-test), DOF ledgers, ablation twins,
and the calibration-frontier designation, see
`docs/calibration-and-validation-methodology.md` — the authoritative
narrative reference, companion to `docs/calibration-determination-rubric.md`
(the criterion-by-criterion rubric spec) and CLAUDE.md rules 16–26.

### 1.8 Dispatch-Time Reliability Floor — Temperature / Net-Load Commitment

An energy-only LP decommits thermal generators whenever their marginal cost exceeds the clearing price, even in hours where a real system operator would hold them online for local reliability or ramping reserve against weather-driven load spikes. The **temperature/net-load reliability floor** (`transmission.inject_reliability_floor`) corrects this by raising `FleetArrays.min_gen` — the hourly lower bound on dispatched power — for thermal units whose real-world commitment is temperature- or net-load-driven. The mechanism is structural (mirrors how UC models commit-then-enforce-Pmin), forward-reproducible, and ISO-agnostic.

**Registry.** Each ISO's floor is a list of per-(zone, plant_class, driver) limbs in `RELIABILITY_FLOOR_REGISTRY` (`config/iso_configs.py`), seeded from `data/raw/reference/reliability_floor_coeffs_<ISO>.csv` — one row per limb. All six ISOs have derived coefficient CSVs (~221 total limbs; ~30 enabled, the rest shipped `enabled=False` because their temperature response is too weak to warrant a floor). `ReliabilityFloorSpec` is a frozen dataclass with fields: `zone`, `plant_class`, `driver` (`"tmax"` / `"tmin"` / `"netload"`), `threshold` (°C or GW), `floor_pct`, `enabled`, `min_event_hours` (24 for fast-start; 48 for steam), `distribution` (`"cheapest_first"` or `"pro_rata"`).

**Day gate (no hour-of-day windows).** On each calendar day:
- `driver="tmax"`: flag all 24h if `tmax_c > threshold`
- `driver="tmin"`: flag all 24h if `tmin_c < threshold`
- `driver="netload"`: flag all 24h if the day's system peak net-load (GW) > threshold (net-load = demand − VRE availability, computed from exogenous scenario drivers, not endogenous dispatch, to avoid circularity)

On flagged days, `frac = floor_pct`; on unflagged days, `frac = 0`. The full-day step gate replaces the earlier hour-of-day window model — a committed boiler physically runs the whole day, not a 6-hour afternoon window.

**floor_pct = commit_frac × min_stable_pct.** Two physical/structural halves: `commit_frac` is the share of the class's capacity online on flagged days (from CAMPD `grossLoad > 0` — a commitment count, not a CF ceiling); `min_stable_pct` is the physical min-stable level of the class (Pmin/Pmax, from bin tranche data / turbine specs). The result is a floor the LP must meet; dispatch above it is economic. The deprecated p97-CF ceiling is removed.

**Coefficient derivation.** Per-(zone, class) limb coefficients are regressed from CAMPD daily CF vs zone daily TMAX/TMIN (`scripts/derive_reliability_coeffs.py`). A limb is `enabled=True` only when the temperature response is real — Spearman ρ ≥ threshold (e.g. 0.3), sample size `n` ≥ 30 flagged days, and `floor_pct` meaningfully above the mild-day baseline. Coefficients are **never** tuned to the price/volume residual; floor_pct is **never** set to a measured CF ceiling so output matches actuals. The same coefficients regenerate for a forward year and respond to changed weather (CLAUDE.md #9/#11).

**Steam-gas event bridging.** ST_GAS/ST_CHP limbs carry `min_event_hours=48` by default so an isolated flagged day bridges to adjacent flagged days — a committed boiler spans the whole multi-day heat-wave or cold-snap. `_bridge_flagged_runs()` merges isolated flagged runs separated by sub-event gaps. CT peakers keep single-day gates (`min_event_hours=24`).

**Distribution.** `"cheapest_first"` (default): `_distribute_group_floor()` sizes the hourly group target and fills it from cheapest units first (by heat rate). `"pro_rata"`: each in-scope unit is floored at `frac × its own available capacity`. Composed into `min_gen` via `np.maximum`.

**Config.** `ScenarioConfig.reliability_floor: bool` (master switch, default off). `ScenarioConfig.reliability_floor_overrides: dict` (per-limb overrides keyed `"<ZONE>:<CLASS>:<driver>"` → `{"enabled"?, "floor_pct"?, "threshold"?}`). `ScenarioConfig.class_commitment_overrides: dict` (per-ISO×class `min_run_hours`/`min_down_hours` for the P2 commitment screen). New ISOs/limbs require only a coefficient CSV row and a weather file — no code changes.

### 1.8 Benchmark basis — backcast scoring actuals (G-21/G-21b, all ISOs)

The backcast **actual side** (what a keeper is scored against) is constructed by three mechanisms that are the **go-forward default for every ISO** (owner directive 2026-07-12), unconditional — no flag, no env knob, no `getattr` fallback re-arms the retired basis (CLAUDE.md rule 24). They are pinned by `tests/test_benchmark_basis_default.py` and the per-mechanism unit tests, and specified in full in the determination rubric §0b (`docs/calibration-determination-rubric.md`). The governing invariant: **no raw EIA-930 per-fuel cell ever gates a scored class or family number** — EIA-930's BA-reported gas/coal attribution mis-splits vs CEMS by 7–21 TWh/yr, so it is trusted for the fossil *level* only, never the *split*.

1. **G-21 combined-fossil reconcile** (`scripts/render_calibration_html.py::reconcile_vintage_classes`): the EIA-923 row-level + CAMPD-backfilled fossil total reconciles to EIA-930 as **one combined gas+coal family** (level corrected both directions within `_VINTAGE_RECONCILE_FRAC = 0.97`; every fossil class scaled by the same factor, so the CEMS-validated 923 gas/coal split is preserved). The retired per-family reconcile scaled gas and coal each to their own unreliable 930 cell, manufacturing PJM's phantom "+21 TWh CC_REGULAR over-run."
2. **#2049 unit-class CAMPD backfill bucketing** (`scripts/run_calibration_full.py::_backfill_eia923_with_campd` × `_plant_class_shares`): a mixed non-ERCOT plant's CAMPD net splits across the classes physically at it by measured EIA-923 prime-mover class shares (mass-preserving). The retired last-generator-wins path double-counted minority-class plants (PJM Linden p2406 ≈9.5 → ≈4.8 TWh). ERCOT keeps its curated bin-sheet single-class path (`class_shares=None`), byte-identical.
3. **G-21b C2 preliminary-vintage split anchor** (`scripts/calibration_verdict.py::score_sysvol` + `_fallback_coal_anchor`): an incomplete family gates on the EIA-930 combined-fossil **level** with a CEMS-anchored coal/gas split (coal = CAMPD CEMS coal × the run's complete-vintage CEMS→923-grid ratio `k`; gas = 930 combined minus that coal anchor), never the raw 930 per-fuel cell. The `e930.coal_cems` anchor is built inside `render_calibration_html` (its sole writer; a post-hoc splice script was deleted 2026-07-12). All 18 committed bench parts carry `coal_cems`, so every re-score and new registration already takes the anchor path.

Determination flips under this basis are honest and stand (pjm-98 precedent); nothing may be tuned to un-flip them (CLAUDE.md rules 1/13/23). See `docs/calibration-log.md` (2026-07-11 "SCORER FIX (all ISOs)" + 2026-07-12 pjm-98), `docs/handoffs/pjm-cc-overrun-benchmark-basis-g21-2026-07.md`, and the staleness inventory `docs/handoffs/benchmark-basis-inventory-2026-07.md`.

-----

## 2. LP Construction Pattern — Block-Diagonal with Vectorized Assembly

This is the most performance-critical code in the model. **Do not build the constraint matrix with Python loops over hours and generators.** Use vectorized sparse matrix construction.

### 2.1 Matrix Structure

The LP for a single ISO-year has this block structure:

```
A = [ B_1   0    0   ...  0    L  ]    (energy balance + generator bounds, hour 1)
    [  0   B_2   0   ...  0    L  ]    (hour 2)
    [  0    0   B_3  ...  0    L  ]    (hour 3)
    [ ...                     ... ]
    [  0    0    0   ... B_T   L  ]    (hour T)
    [       S (storage SOC linkage)    ]    (inter-temporal coupling)
    [       Policy constraints         ]    (if any active)
```

Where:

- `B_t` is the per-hour constraint block (energy balance + gen bounds + renewable bounds + transmission). Structurally identical across hours — same sparsity pattern, different RHS values and potentially different coefficient values (fuel prices can vary hourly).
- `L` is the transmission flow coefficient matrix (same every hour for pipe-and-bubble).
- `S` is the storage SOC linkage — a banded matrix coupling `SOC[s,t]` to `SOC[s,t-1]`, `Chg[s,t]`, `Dis[s,t]`.

### 2.2 Construction Algorithm

```python
# PSEUDOCODE — the builder follows this pattern

def build_lp(fleet_arrays, demand, wind_cf, solar_cf, storage, transmission, params):
    """
    fleet_arrays: struct-of-arrays (see §3.1) — pmax, pmin, mc, zone_idx, etc.
    All inputs are numpy arrays. No Python objects in the hot path.
    """
    n_gen = len(fleet_arrays.pmax)
    n_zones = params.n_zones
    n_storage = len(storage.power_cap)
    n_links = len(transmission.ttc)
    T = 8760

    # --- Variable layout (column indices) ---
    # P[g,t]: n_gen × T columns     (thermal dispatch)
    # W[z,t]: n_zones × T           (wind dispatched)
    # S[z,t]: n_zones × T           (solar dispatched)
    # Chg[s,t]: n_storage × T       (charge)
    # Dis[s,t]: n_storage × T       (discharge)
    # SOC[s,t]: n_storage × T       (state of charge)
    # Flow[l,t]: n_links × T        (transmission)
    # Slack[z,t]: n_zones × T       (unserved energy)
    # Dump[z,t]: n_zones × T        (overgeneration absorbed)
    #
    # Total columns = T × (n_gen + 4*n_zones + 3*n_storage + n_links)

    vars_per_hour = n_gen + 4*n_zones + 3*n_storage + n_links

    # --- Cost vector (objective) ---
    # Assemble as a flat array. mc[g,t] varies by hour (fuel price changes).
    # Use np.tile for static components, element-wise for dynamic.
    cost = np.zeros(vars_per_hour * T)
    # ... fill thermal costs, storage epsilon, VOLL for slack ...

    # --- Per-hour block B_t (energy balance + bounds) ---
    # Build ONE prototype sparse block for the constraint structure,
    # then use scipy.sparse.block_diag or kron to replicate across hours.
    #
    # Energy balance: n_zones rows
    # Gen upper bound: n_gen rows   (P[g,t] ≤ Pmax × avail)
    # Gen lower bound: n_gen rows   (P[g,t] ≥ Pmin)  [or combine as two-sided]
    # Wind upper bound: n_zones rows
    # Solar upper bound: n_zones rows
    # Storage charge/discharge bounds: 2*n_storage rows
    # Transmission bounds: 2*n_links rows (or use variable bounds directly)

    # KEY INSIGHT: For the energy balance rows, the coefficient pattern
    # (which generators are in which zone) is the same every hour.
    # Build a zone-membership matrix once:
    zone_gen_map = sparse.csr_matrix(...)  # n_zones × n_gen, entry = 1 if gen g in zone z

    # The per-hour block's sparsity pattern is fixed. Only RHS values change.
    # Build the pattern once, then replicate.

    # --- Storage SOC linkage ---
    # SOC[s,t] - SOC[s,t-1] - η_chg × Chg[s,t] + Dis[s,t]/η_dis = 0
    # This is a banded submatrix linking adjacent hours.
    # Build with scipy.sparse.diags: main diagonal = +1, sub-diagonal = -1,
    # plus entries for Chg and Dis columns.
    # Cyclic boundary: SOC[s,0] - SOC[s,T-1] row wraps around.

    # --- Assemble full A matrix ---
    # Use scipy.sparse.bmat or vstack to compose blocks.
    # Convert to CSC format (HiGHS native) at the end.

    # --- Pass to HiGHS ---
    h = highspy.Highs()
    h.addVars(n_cols, cost, col_lower, col_upper)
    h.addRows(n_rows, row_lower, A_csc, row_upper)  # CSC matrix
    h.run()

    # --- Extract results ---
    primal = h.getSolution().col_value      # dispatch values
    dual = h.getSolution().row_dual         # prices from energy balance rows
    # Map back to named arrays using the variable layout offsets.
```

### 2.3 Critical Performance Rules for the Build Agent

1. **No Python loops over hours in matrix construction.** Use `np.tile`, `np.repeat`, `scipy.sparse.kron`, `scipy.sparse.block_diag`. If you find yourself writing `for t in range(8760):` in the matrix builder, stop and vectorize.
1. **Build the sparsity pattern once, fill values separately.** The CSC column pointers and row indices are the same for every hour-block. Compute them once, then fill the `data` array with vectorized operations.
1. **Struct-of-arrays for fleet data.** Convert Pydantic generator objects to parallel numpy arrays (`pmax_array`, `heat_rate_array`, `zone_idx_array`, `mc_array`) before entering the LP builder. The builder never touches Python objects.
1. **RHS vector assembly is also vectorized.** `Demand[z,t]` is a `(n_zones, T)` array. Generator availability bounds are `pmax[:, None] * availability[:, :]`. These are numpy broadcasts, not loops.
1. **Pre-allocate the CSC arrays.** Count nonzeros analytically (you know the structure), allocate `data`, `indices`, `indptr` arrays once, fill them.
1. **Target: matrix construction < 1 second, solve < 5 seconds, total < 10 seconds per ISO-year.**

-----

## 3. Data Layout & Struct-of-Arrays

### 3.1 Fleet Arrays

The fleet is loaded from EIA-860 data and internal parameters into Pydantic models for validation. Before LP construction, convert to:

```python
@dataclass
class FleetArrays:
    """Parallel arrays indexed by generator index g. All numpy."""
    pmax: np.ndarray          # (n_gen,) MW
    pmin: np.ndarray          # (n_gen,) MW — 0 for non-must-run
    heat_rate: np.ndarray     # (n_gen,) BTU/kWh
    vom: np.ndarray           # (n_gen,) $/MWh
    emission_rate: np.ndarray # (n_gen,) tCO2/MWh
    nox_rate: np.ndarray      # (n_gen,) lb NOx/MWh (or tons, be consistent)
    zone_idx: np.ndarray      # (n_gen,) int — which zone
    fuel_type: np.ndarray     # (n_gen,) int enum — for grouping/reporting
    availability: np.ndarray  # (n_gen, 8760) — EFORd × seasonal factor
    unit_id: np.ndarray       # (n_gen,) str — for result mapping back to names
```

### 3.2 Marginal Cost Assembly

```python
def assemble_mc(fleet: FleetArrays, fuel_prices: np.ndarray,
                carbon_price: np.ndarray, nox_price: np.ndarray,
                **adders) -> np.ndarray:
    """
    Returns (n_gen, 8760) marginal cost array.
    fuel_prices: (n_gen, 8760) or (n_fuel_types, 8760) mapped via fleet.fuel_type
    carbon_price: (8760,) or scalar
    All adders are keyword arguments — extensible for any future cost component.
    """
    mc = fleet.heat_rate[:, None] * fuel_prices + fleet.vom[:, None]
    mc += fleet.emission_rate[:, None] * carbon_price[None, :]
    mc += fleet.nox_rate[:, None] * nox_price[None, :]
    for name, (rate_array, price_array) in adders.items():
        mc += rate_array[:, None] * price_array[None, :]
    return mc
```

This is fully vectorized — no loops. Adding a new cost adder means adding a rate array to FleetArrays and a price trajectory to the scenario config.

### 3.3 Fleet Representation & Offer Curves

The thermal fleet can be built two ways; the LP and `FleetArrays` structure are identical either way (each tranche/bin is just another row `g`).

**Legacy equal-width heat-rate bins.** EIA-860 generators aggregated into a small number of representative heat-rate bins per fuel — the original method, still used for non-ERCOT ISOs and when `use_campd_bins=False`.

**CAMPD per-plant binning (ERCOT default, `use_campd_bins=True`).** Documented in full in `docs/binning-methodology.md`. Built from EPA CAMPD gross generation (2023–24) cross-referenced with eGRID net generation and EIA-860 characteristics. Each plant gets **its own LP unit** (`data/raw/reference/custom-bin-assignments.csv`), classified into one of seven dispatched groups (CC_CHP, CC_REGULAR, CT_CHP, CT_PEAKER, ST_GAS, ST_CHP, COAL — see `config/plant_taxonomy.py`) plus non-dispatchable OTHER. Each bin is split into **tranches** that form a *rising offer curve* rather than a single flat marginal cost:

- **Must-Run (MR%)** — sunk-fuel coal floor or CHP behind-the-meter steam (the latter is removed from the LP and reconstructed post-dispatch by `compute_must_run_emissions()`). A covered CHP plant's BTM CO2 books at the same measured v2 rate as its grid tranches (not a separate heat-rate-derived number), and the forecast-mode BTM generation estimate uses `measured_class_cf()` — a gen-weighted op-hours utilization per CHP class keyed off the CEMS steam-load signature (`steam_load_klbh_sum > 0`) — in place of a flat assumed capacity factor, falling back to the flat `must_run_cf` (default 0.85) only when no measured class CF is available (EM-7 fix). The BTM *sizing share* itself is likewise measured: forecast years size `mr_mw` off the `chp-btm-share` datatype (`data.chp.measured_btm_share_by_plant`, `(EIA-923 net class gen − CAMPD grid-net gen) / EIA-923 net`, pooled across history) rather than the sector-keyed `chp_btm_pct` default, falling back to the bin's own MR% when a plant is uncovered; backcast years keep sizing from `chp_btm_pct` directly.
- **Committed (MC%)** — minimum stable load; the only tranche the commitment screen (§1.6) acts on. Bids cheap (`base_hr × offer["committed"]`, no `pmin`). For CC the committed share is derived **per-plant from CAMPD** (P5 of online CF) when `cc_committed_per_plant` is set — the ERCOT default — not from the flat CSV share.
- **Economic** — incremental in-merit dispatch, rendered **by default** as an `offer_curve_smoothing_n`-slice (default 6) rising heat-rate ramp anchored on the plant's own `base_hr`, *not* a single flat block. CC/coal fold the peak band into the ramp top.
- **Peaking (PEAK%)** — duct-firing / steep cost, `pmin=0`, never screened out; for CC/coal it is the top of the economic ramp rather than a standalone tranche.

No CC tranche carries a `pmin` floor and no bin-weighted heat rate is used — each plant dispatches on its own `Plant_Avg_HR_MMBtu_MWh`. See `docs/binning-methodology.md`.

Two further refinements wired into marginal-cost assembly:
- **Coal take-or-pay tranches** — three slices at different fuel passthroughs (e.g. VOM-only / partial / full fuel cost), so a coal unit's offer rises with quantity.
- **Coal passthrough sigmoids (per supply chain, per ISO)** — each coal supply chain (PRB rail take-or-pay, subbituminous, bituminous, mine-mouth lignite) discounts or marks up its bid as a smooth (sigmoid) function of the monthly gas price, with its **own independently tunable curve**: basin, rank, delivery mode and contract structure shift where the coal-vs-gas-CC crossover sits. Curves are **region-dependent** (`COAL_SIGMOID_DEFAULTS[(iso, supply)]`) — an (ISO, supply) pair with no characterized curve stays at flat passthrough rather than borrowing another region's economics. ERCOT PRB additionally has a tiered follower-curve variant for load-following plants.

**Per-plant offer curves.** By default the tranche shares and band heat-rate *multipliers* are per-*group* (`offer_curve_by_group`), but they are always applied to each plant's **own** `base_hr`, and the economic block is already a per-plant rising N-slice ramp (above) — so the default is plant-specific in level even where the curve *shape* is shared. An optional per-plant override sheet (`data/raw/reference/plant-tranche-config.csv`, `ScenarioConfig.plant_tranche_config_path`, off by default) additionally lets each listed plant carry its own **five-slice rising offer curve** — Must-Run / Committed / Econ-Low / Econ-High / Peaking shares plus per-slice heat-rate multipliers — bypassing the group shape too. This is the calibration lever for shaping an individual flagship plant's dispatch without disturbing its class total (`docs/binning-methodology.md`). A companion flag `cc_peaking_per_plant` moves the duct-burner peak band's CF onset for selected F-class CCs.

When a bin maps to a single physical plant, its CO2/NOx can be overridden with **CAMPD CEMS plant-specific emission rates** instead of the fuel-class default. The CO2 rate is booked at the plant's **physical** heat rate, never the bid-tranche heat rate — the offer-curve pricing multipliers (peak ×2.0–2.5, committed ×0.92) shape the bid stack, not the plant's CO2/MWh (R2/EM-4 fix, `fleet.py` `bins_to_fleet`).

**Forward-mode source (v2, `use_plant_emission_rates_v2`, default off; `docs/handoffs/emissions-co2-rate-plan-2026-07.md`).** The per-plant CO2 rate is **mode-aware**: a **backcast** year books the target year's own measured CEMS rate (a reproducible physical input); a **forecast** year books the estimator base — the gen-weighted trailing average of the unit's multi-year CAMPD history, aggregated over only the CEMS units present in the target year's fleet (the unit-composition mask). This is wired end-to-end via `src/market_sim/data/fleet.py::apply_plant_emission_rates_v2` → `src/market_sim/data/emission_rates.py::measured_plant_rates`. The forward rate is *derived from* forward drivers and responds to changed operation (a retired unit drops out of the plant's composition mask), so it is rule-13-admissible in forecast — not the forbidden same-year pin. Rates are matched to each dispatch bin by `(plant_code, coarse fuel class)`, so a coal+gas facility (W A Parish 3470) gets **separate coal and gas rates** rather than the blended facility value — replacing the old `mixed`-plant exclusion.

`emission_rates.py::forward_plant_co2_rate` is the full four-piece estimator design (gen-weighted base + envelope-gated nearest-neighbor conditioning on simulated operation + the unit-composition mask + a class-distribution fallback, `class_median_rates`) and is certified by the leave-one-year-out harness `scripts/loyo_co2_rates.py` — never by a keeper's backcast fit. **Only the base + mask pieces are wired into the production dispatch path today** (`measured_plant_rates`, above); the envelope-gated NN conditioning and the class-median fallback are implemented and unit-tested (`tests/test_emission_rates.py`) but are called only from the LOYO harness and its tests, not from `fleet.py`/`runner.py`. Concretely: CEMS-uncovered plants still fall back to the generic `get_emission_rate(fuel, base_hr)` heat-rate default, and new entrants still take the static per-vintage `constants.CO2_RATES[tech][bin]` table — neither consults `class_median_rates`. The NN conditioning ships gated off (`constants.CO2_RATE_CONDITIONING_ENABLED = False`): the 7-year held-in LOYO (2018–2021 + 2023–2025, run 2026-07-05; plan §9.5) rendered the verdict — the envelope-gated sim-conditioned estimator never beat plain `a_gw` at any swept gate on ERCOT, the only ISO with persisted simulated operation — so the shipped estimator is the pure gen-weighted trailing average. The same sweep set the trailing window to the **most recent 2 years** of available history (`constants.CO2_RATE_TRAILING_WINDOW_YEARS = 2`): in the forward-chained direction (targets predicted from strictly-prior years, matching production use) the 2-year window won every per-target comparison on both ERCOT and PJM — measured plant rates drift with age/retrofits, so recent years are more predictive. Both constants are frozen against backcast residuals and re-derive only on a CAMPD data update (rule 23). Closing the class-fallback gap is tracked as a follow-on, not yet scheduled to a wave.

**NOx/SO2 ride the identical v2 path (plan §5 R7 full-wiring wave).** The v2 artifact carries `nox_kg`/`so2_kg` masses and their net-basis intensities alongside CO2; `measured_plant_rates(..., pollutant=...)` and `class_median_rates(..., pollutant=...)` select the mass column, and `apply_plant_emission_rates_v2` books all three (CO2, NOx, SO2) at the plant's measured tonnes/MWh-net rate under the same mode/composition-mask policy. CO2/NOx are overridden only when the measured rate is positive (keep the fuel default otherwise); SO2 is always set (zero is a legitimate gas value). NOx/SO2 are **secondary** — the wiring changes no CO2 rate and no merit order (the LP objective already carried `nox_rate`; SO2 defaults to a 0 price). The `scripts/score_backcast_shape_emissions.py` diagnostic scores model-vs-CAMPD NOx and SO2 masses beside CO2, using the same v2 intensities; the SO2 coal/gas split is the sharpest independent check on dispatch mix because coal SO2 intensity dwarfs gas.

**Forward control-retrofit channel (`control_retrofit_forward`, default off; `docs/handoffs/emission-control-retrofit-forward-channel-2026-07.md`).** The trailing-average estimator only absorbs a control's effect once it appears in measured history. This sibling channel adds the missing forward step: an **announced** EIA-860 environmental-control install (SCR/SNCR → NOx, FGD scrubber/DSI → SO2, from `eia860_enviro_assoc_emissions_control_equipment.parquet`) steps the covered unit's forward rate down at its committed **Inservice Year** — `post = pre × (1 − removal_fraction)`, the same form as the CCS retrofit screen (§5.6). The install *date* is the forward driver (not a residual), so the step is rule-13-admissible; it fires **forecast-only** (backcast books the year's own measured rate, which already reflects any operating control) and is byte-identical to the base estimator when off. With NOx/SO2 now on the same measured v2 path (the R7 wiring above), the channel steps **all three** pollutants per-plant via `_apply_forward_control_retrofits` — the default control map targets NOx and SO2, the pollutants the announced EIA-860 controls actually reduce. Carbon-capture/CO2 is intentionally excluded from the default control map — economically-triggered CCS is owned by the retrofit screen (§5.6, one-mechanism-per-phenomenon). The override function (`data/emission_rates.apply_control_retrofits`) and EIA-860 loader (`load_announced_controls`) stay pollutant-general.

-----

## 4. Scenario Architecture

### 4.1 Tiered Parameter System

Every model input is a named parameter with a default value and a tier assignment.

**Tier 0 — Structural.** Changes the LP’s shape or invalidates cross-scenario comparisons. Set once per model configuration.

Examples: weather year, ISO selection, zone topology, hourly resolution, VOLL by zone, storage technology menu (which types exist).

**Tier 1 — Scenario levers.** The parameters varied across runs. Define the uncertainty space.

Examples: gas price path, carbon price trajectory, NOx price, demand growth rate, renewable buildout pace, storage deployment, retirement aggressiveness.

`storage_deployment` sets the base-year (2026) storage fleet size. Subsequent years grow via economic screening.

**Tier 2 — Expert/sensitivity.** Changeable but normally held at defaults.

Examples: heat rates by unit, storage RTE, discount rate, forced outage rates, technology learning curves, CAISO import curve shape, VOM by technology.

**Tier 3 — Calibration.** Tuned during validation, then frozen.

Examples: renewable CF adjustment factors, seasonal availability patterns, basis differentials, WECC import tranche parameters.

**Implementation:**

```python
@dataclass
class ScenarioConfig:
    """Full model parameterization. Every field has a default.
    Tier tags are metadata — they don't affect runtime behavior."""

    # --- Tier 0: Structural ---
    weather_year: int = 2024
    iso: str = "ERCOT"              # or "CAISO"
    voll: float = 5000.0            # $/MWh
    # ...

    # --- Tier 1: Scenario levers ---
    gas_price_path: str = "mid"     # or array, or path to CSV
    carbon_price: float = 0.0       # $/ton — scalar or trajectory
    nox_price: float = 0.0
    demand_growth_rate: float = 0.01
    # ...

    # --- Tier 2: Expert ---
    storage_rte_4hr: float = 0.85
    discount_rate: float = 0.08
    # ...

    # --- Tier 3: Calibration ---
    # ...

    def cache_key(self) -> str:
        """Deterministic hash of the full config. Used for result caching."""
        return hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True).encode()
        ).hexdigest()[:16]
```

### 4.2 Single-Run Mode

CLI accepts a YAML file that overrides any parameter:

```bash
python -m market_sim run --config my_scenario.yaml
```

```yaml
# my_scenario.yaml — only specify overrides, everything else uses defaults
iso: ERCOT
gas_price_path: high
carbon_price: 45.0
nox_price: 2.5
demand_growth_rate: 0.025
storage_rte_4hr: 0.82   # testing sensitivity
```

Unspecified parameters use `ScenarioConfig` defaults. The full resolved config is logged with every run.

### 4.3 Batch Sweep Mode

A sweep definition specifies which Tier 1 parameters to vary and what values to test. The sweep generator produces a list of `ScenarioConfig` objects.

```yaml
# sweep_gas_carbon.yaml
sweep:
  gas_price_path: [low, mid, high]
  carbon_price: [0, 25, 50]
# All other parameters at defaults. This produces 9 scenarios.
```

```yaml
# sweep_demand_buildout.yaml
sweep:
  demand_growth_rate: [0.005, 0.015, 0.03]
  renewable_buildout_pace: [slow, mid, aggressive]
# 9 more scenarios, orthogonal to the gas×carbon sweep.
```

Sweeps can be composed (run multiple sweep files) or run independently. The runner deduplicates by cache key — if a scenario exists from a previous sweep, it’s skipped.

**No full factorial on all dimensions.** The user pairs parameters deliberately. The sweep generator supports `mode: factorial` (default), `mode: lhs` (Latin hypercube — future), or `mode: list` (explicit list of configs).

### 4.4 Caching

Each scenario-year result is stored as a **single Parquet file**:

```
results/
  {iso}/
    {cache_key}/
      year_2026.parquet
      year_2027.parquet
      ...
      year_2050.parquet
      config.yaml          # full resolved ScenarioConfig for reproducibility
```

Before running a scenario-year, check if the parquet exists. If yes, skip. This makes the system stop/resume capable and avoids recomputing validated results.

The Parquet contains all hourly outputs for that ISO-year: dispatch by unit, zonal prices, emissions, storage SOC, curtailment, flows, slack. Schema is fixed and documented in a data dictionary.

-----

## 5. Capacity Evolution — One-Pass Sequential

### 5.1 Architecture

Fleet evolves year-over-year within a scenario. Year N+1’s fleet depends on Year N’s dispatch and price results. **No within-year convergence iteration.** This is a deliberate simplification — the one-pass approach is standard in screening models and avoids instability.

```
For year in 2026..2050:
    (start with fleet from prior year, or base fleet for 2026)
    0. Apply CONFIRMED exits (binding public instruments — consent decree,
       statute, RTO deactivation acceptance, regulatory order, RMR end; any
       fuel; bypasses the reliability floor). GATED `confirmed_exits_enabled`
       (default on, flipped 2026-07-05 — docs/handoffs/confirmed-retirement-plan-2026-07.md
       §7), forecast-mode only. The ONLY exogenous fossil exit channel.
    1. Apply ANNOUNCED retirements (EIA-860 planned date) — fossil is a default
       no-op (deferred to the economic screen, step 2); NON-FOSSIL
       (nuclear/hydro/renewables/storage) honored only within the EIA-860 data
       horizon, beyond it only if the unit is in the confirmed registry
       (`forecast_fossil_retirement_economic`, `NONFOSSIL_ANNOUNCED_HORIZON_YEARS`)
    2. Apply economic retirement screen (fuel-type-aware, uses Year N-1 results;
       includes the accredited reliability floor)
    3. Apply known additions (EIA-860 under construction, signed PPAs)
    4. Apply CCS retrofit screen to existing gas-CC units (§5.6)
    5. Apply economic new entry screen (LCOE vs expected revenue, including
       the prior year's REC price as clean-energy revenue)
    6. Apply reserve-margin adequacy backstop: force-build firm capacity if the
       economic screen left the system below its planning reserve margin.
       GATED `reserve_margin_build_enabled`, default off.
    7. Assemble updated fleet → run dispatch LP (with RPS constraint) → cache results
```

The capacity-evolution mechanisms are steps 0–6. The RPS is no longer a force-build step: it is enforced as an LP constraint in the dispatch (step 7), and its shadow price feeds back into the economic new-entry screen the following year.

**Confirmed vs announced retirements.** Only *confirmed* exits — units bound by an enforceable public instrument (RTO deactivation acceptance, consent decree, statute, PUC/regulatory order, RMR end date) — are exogenous. They come from the hand-curated `confirmed-retirements` registry (one row per binding instrument, forward-reproducible per rule 13; superseded rows carry a cited counter-instrument and revert to the economic screen), read forecast-forward by `data.confirmed_retirements.load_confirmed_exits` and applied at step 0 (`apply_confirmed_exits`), which force-retires a unit-grain unit or derates a plant-binned tranche by the exiting unit's MW, bypassing the reliability floor. This is the ONLY exogenous fossil exit channel. *Announced* retirements (`apply_announced_retirements`, step 1) honor an EIA-860 self-reported planned date — but a coal/gas/oil unit's announced date is treated as an announcement, not a certainty, so **for the whole fossil fleet step 1 is a default no-op** and the economic screen (step 2) governs the phaseout, keeping the forecast condition-responsive (a fossil unit may exit early on losses or run past its announced date if it stays in-merit). Non-fossil announced dates (nuclear/hydro/renewables/storage — policy/contract/end-of-life exits) stay deterministic only within the EIA-860 data horizon (`EIA860_OPERABLE_VINTAGE + NONFOSSIL_ANNOUNCED_HORIZON_YEARS`, default 5); beyond the horizon a non-fossil date is honored only if the unit is in the confirmed registry, so speculative 2040-2072 relicense/EOL placeholders stop force-retiring (the horizon gate activates with the confirmed channel; off = honor all non-fossil dates). The splits are the `forecast_fossil_retirement_economic` and `confirmed_exits_enabled` flags. After the data horizon (~2030), the model is fully economics-driven.

### 5.2 Economic Retirement

A unit retires if its **net revenue < going-forward cost** for N consecutive years, where N varies by fuel type:

- **Coal:** 1 consecutive loss year (faster exit — reflects regulatory risk and carbon liability)
- **Gas CT:** 2 consecutive loss years
- **Gas CC:** 3 consecutive loss years (most patient — higher capital sunk, longer expected life)

Revenue and cost definitions:

- Net revenue = the **attainable (pro-forma) inframarginal margin** `Σ_t max(0, price[z,t] − mc[g,t], r[g,t]) × pmax[g] × availability[g,t]` plus attribute payments (`max(exogenous EAC, prior-year RPS/REC shadow price) × annual_gen`) and any capacity-market revenue, evaluated against the prior year's capacity-screen price signal. This is the unit's optimal per-hour response to the screen's own signal — the same price-duration pro-forma the Potomac SOM net-revenue tables are built from and the same basis the new-entry screen uses — **not** the prior LP's realized dispatch: the post-solve ORDC scarcity adder lifts the screen's prices in hours the pre-adder LP left an out-of-merit peaker idle, so a realized-dispatch margin structurally misses exactly the scarcity rent a peaker lives on (capacity-economics plan 2026-07 §5 step 2). `r[g,t]` is the hourly reserve-price signal (below); `mc` is the unit's *full* variable cost (fuel + VOM + emission prices) — not its bid: take-or-pay coal bids below fuel cost in dispatch because the fuel is sunk within the contract year, but on a retirement horizon the contract lapses, so fuel is avoidable and counts against the margin. (Two earlier formulations are superseded: *gross* energy revenue vs fixed cost let units "cover" FOM with money already spent on fuel; realized-dispatch margin under-collected scarcity ~40× on the SOM CT observable.) A profitable year resets the unit's consecutive-loss counter to zero.
- Reserve/AS valuation (`screen_reserve_value_enabled`, default on): each reserve-eligible unit's hourly value is its **best use** — energy margin or the reserve price, never both on the same MW (the co-optimization arbitrage condition). The signal is the reserve co-opt's own duals under `ercot_thermal_as_endogenous` (all-products tier for synchronized units, Non-Spin tier for offline-capable quick-starts, mirroring the co-opt's headroom cascade), else the post-solve ORDC scarcity adder — ERCOT pays real-time on-line/off-line reserves the same ORDC price the energy adder carries (RTORPA/RTOFFPA, Nodal Protocols §6.5.7.5). When the hourly signal is present it is the SOLE thermal AS pricing (rule 19); otherwise the screens fall back to the annual endogenous per-fuel rate or the calibrated exogenous flat rate, as before. Zero fitted parameters; the SOM CT/CC net-revenue tables are the external validity check, never a target.
- Going-forward cost = fixed O&M × FOM multiplier (not capital — sunk cost)
- FOM multipliers: coal = 1.3× (captures regulatory risk, carbon liability, ESG pressure), gas = 1.0×
- Retirement ordering: within each fuel class, least efficient (highest heat rate) retires first

These thresholds and multipliers are no longer hardcoded — they are `ScenarioConfig` fields (`retirement_years_{coal,gas_ct,gas_cc}` = 1/2/3, `retirement_fom_multiplier_{coal,gas_ct,gas_cc}` = 1.3/1.0/1.0), so retirement aggressiveness is a Tier-1 sensitivity lever. The defaults above are the as-built values. (`retirement_reserve_margin` was DELETED with the floor-accreditation rebuild — the floor and the build backstop now share `PLANNING_RESERVE_MARGIN_BY_ISO`.)

**Reliability floor (accredited basis):** the surviving fleet's `accredited_firm_capacity_mw` (thermal at its ISO's published basis via `thermal_accreditation_fraction` — UCAP = 1 − EFORd, PJM's ELCC class rating, or ERCOT's seasonal rating; wind/solar pools at their **penetration-indexed published ELCC** — see below; storage at duration-ELCC) cannot fall below the shared adequacy requirement (`resolve_adequacy_requirement_mw` — the published FPR where one exists, else `peak_demand × (1 + PLANNING_RESERVE_MARGIN_BY_ISO)`) — the same requirement the step-6 build backstop tests (one requirement, two verbs). If economic retirements would breach it, eligible units are un-retired cheapest-firm-adequacy-first ($/firm-MW-yr ascending, CO₂-rate tie-break), and every retention is recorded in the `floor_retention_log` persisted per year (`floor_retentions.json`).

**VRE accreditation (CR-3.1, penetration-indexed ELCC):** wind/solar (and any published VRE class) accredit through one resolver (`capacity.resolve_renewable_capacity_credit`, gate `ScenarioConfig.renewable_elcc_curves`, default **on**) with a three-step ladder: (1) the ISO's own published penetration-indexed ELCC curve (`RENEWABLE_ELCC_CURVES_BY_ISO`, digitized from the P-0B `capacity-market-elcc` datatype — PJM BRA final class ratings on an installed-MW axis, MISO's capacity-credit-vs-penetration-of-peak curve, NYISO's single-point CAFs), evaluated piecewise-linearly (flat-clamped beyond the published domain) at the **model's own installed share** — the class's ISO-wide nameplate (pools + fleet units) against the year's peak — so accreditation responds to modeled build and VRE saturates its own capacity value (rule 13, zero fitted parameters); (2) a published single-point per-ISO override (`RENEWABLE_CAPACITY_CREDIT_BY_ISO` — ERCOT's CDR ELCC basis, unchanged); (3) the generic flat constants (`RENEWABLE_CAPACITY_CREDIT`, wind 0.16 / solar 0.18) as the cited neutral fallback for ISOs with no ISO-published study (NEISO — third-party studies only; CAISO — the CPUC study publishes incremental-basis values misaligned to a fleet-average ledger). All four consumers move together off the one resolver: `accredited_firm_capacity_mw`, the reliability floor, the reserve-margin backstop, and the CR-1 reserve position. `renewable_elcc_curves=False` is the frozen-penetration byte-compat mode (pre-CR-3.1 flat credits — the capacity-hindcast baseline arm). Storage is deliberately untouched: its accreditation keeps its own single stack (duration-ELCC × entry-screen saturation derate × portfolio dilution, §5.5) — one mechanism per phenomenon (rule 19).

**Announced-retirement reversal supersession:** a plant whose confirmed-retirements registry rows are ALL `superseded` (a public counter-instrument reversed the exit outright — e.g. Byron/Dresden's 2021 announced dates reversed by IL CEJA, P.A. 102-0662) has its stale EIA-860 announced date ignored by step 1, any fuel; the unit stays with the economic screen. Data-driven and independent of `confirmed_exits_enabled` — honoring a documented reversal is a data correction on the announced channel, not an exit injection (`data.confirmed_retirements.load_announced_reversal_plants`).

**Design note:** Sigmoid retirement was considered and rejected in favor of fully economic retirement with fuel-type-aware thresholds. The economic approach is more transparent — every retirement is traceable to a revenue shortfall — and avoids the arbitrary sigmoid midpoint parameter. The coal FOM multiplier (1.3×) captures the non-economic pressures (regulatory risk, ESG) that the sigmoid was designed to model.

### 5.3 Economic New Entry

Screen by technology: if `expected_revenue > LCOE`, the technology is economic for entry.

- Expected revenue estimated from prior year’s price duration curve. Dispatchable thermal candidates use the price-duration integral `Σ_t max(0, price_t − var_cost, r_t)` — with the same hourly reserve-price signal the retirement screen sees (`screen_reserve_value_enabled`; a new CT is a Non-Spin-tier quick-start, a new CC synchronized), which then supersedes the annual AS credits (rule 19). Wind/solar candidates value their **build zone's hourly CF profile against that zone's prices** (shape-aware capture, incl. each tech's actual share of scarcity-priced hours — plan §6 CX-6c), falling back to the scalar base-CF screen when profiles are unavailable.
- LCOE from technology cost assumptions with learning curves (Tier 2 parameters)
- IRA credits reduce LCOE (PTC for wind, ITC for solar/storage — Tier 1 parameters)
- Annual build rate capped per technology (e.g., ERCOT ~12 GW/yr queue throughput)
- Clean technologies (wind, solar) earn the prior year's REC price — the RPS constraint's shadow price — as additional expected revenue, so a binding RPS pulls more of them across the LCOE hurdle
- Technology priority: ranked by revenue-minus-LCOE margin, highest first

**Technology availability gating.** The candidate set is not fixed. The classic four technologies (wind, solar, gas CC, nuclear) are always eligible, but each emerging technology (hydrogen turbines, CCUS, enhanced geothermal, offshore wind — see §1.5) joins the candidate pool only once the simulation year reaches its configured availability year (`h2_available_year`, `ccs_available_year`, `egs_available_year`, `offshore_wind_available_year`). Offshore wind additionally enters only in ISOs listed in `offshore_wind_eligible_isos`. The screening order is therefore: (1) build the year's eligible candidate set, (2) compute each candidate's LCOE and margin, (3) rank and build subject to queue caps. Hydrogen turbines and CCUS share the `gas_cc` per-tech queue cap (shared gas-turbine supply chain); geothermal and offshore wind have their own per-tech caps.

### 5.4 Known Pipeline

EIA-860 provides: units under construction (with expected online date), announced retirements (with expected date). These are deterministic — they happen regardless of economics. Transition point from known to modeled: ~2030 for near-term pipeline, model takes over for years beyond the data horizon.

**As built** (`data/fleet.py:load_planned_additions`, forecast mode only): proposed-generator rows with a construction-committed status (`U`/`V`/`TS` — `P` planned-with-permits is excluded as too speculative for a firm thermal unit, though the renewables capacity-ramp aggregation does count it), whose plant's balancing authority maps to the running ISO and whose `Effective Year` falls after the operable-snapshot vintage (`EIA860_OPERABLE_VINTAGE`, currently 2025 per the EIA-860 2025 Early Release), enter the fleet as `Generator`s (`unit_id` prefixed `planned_`) in their effective year. Wind/solar/storage rows are skipped — renewable growth lives in the zonal capacity pools and storage in its own screen, so adding them here would double-count. Zones come from the plant's EIA-860 lat/lon. Units already due by the first simulated year join the base fleet; later ones are injected by `evolve_fleet` step 3.

### 5.5 Storage New Entry

Storage enters via economics-based screening on a **value stack**, compared
against annualized cost (capex × CRF + FOM, with IRA ITC and a Wright's-Law
learning curve):

**1. Energy arbitrage** over **duration-sized windows**, net of cycling
degradation. The year is split into windows of `block_days = max(1,
ceil(duration_hr / 12))` days; in each window the unit charges its cheapest
`duration_hr` hours and discharges its dearest, for one cycle per window:

```
Revenue_energy = Σ_windows max(0, discharge_avg - charge_avg/RTE - degr) × duration
```

The window is sized so a full charge and full discharge never overlap
(`2 × duration ≤ 24 × block_days`). This matters: a **fixed 24-hour window
collapses the spread to zero for any duration at or beyond a day**, so
long-duration storage (iron-air, flow, CAES) would screen as worthless and
could never build. The duration-sized window lets multi-day assets realize
multi-day arbitrage. `degr` is a per-MWh cycling-degradation cost
(energy-capex slice over rated cycle life), which penalizes high-cycling
short-duration storage more than long-life chemistries.

**2. Capacity (resource-adequacy) value**, paid **only in capacity markets**.
Governed by a per-ISO `MarketDesign` switch (`MARKET_DESIGN`): energy-only
ERCOT pays nothing here (scarcity already flows through the ORDC/VOLL energy
price), while PJM/NYISO/ISO-NE and CAISO's RA pay
`capacity_price × ELCC(duration) × (1 − penetration)^k`, where `capacity_price`
is the **shared per-firm-MW seam** (§5.9 — the same `MarketDesign` price the
thermal retirement and new-entry screens use, so storage rides the ISO's one
demand curve with no screen-specific curve): the fixed net-CONE by default, or
the CR-1 sloped-curve price `VRR(reserve_position) × net_cone_curve` when
`config.capacity_market_clearing` is on. The ELCC capacity credit **rises with
duration**; the saturation derate **falls as storage approaches the deployment
ceiling**. Together they make short-duration capacity value collapse at high
penetration while long-duration retains its firm credit — the mechanism that
tilts new entry toward longer durations as storage saturates. The stack is
toggleable via `config.storage_capacity_value` and `config.storage_degradation`.

**3. Ancillary-service (AS) value** (ERCOT), the third value-stack slice —
~85% of 2023 ERCOT battery revenue and absent from the arbitrage + capacity
terms. **Exactly one mechanism supplies it (rule 19), keyed on
`ercot_storage_as_endogenous`:**

- **off (default / legacy / backcast-validation):** the calibrated *exogenous*
  rate `ancillary.as_revenue_per_mw_yr("storage", …)` — a per-kW $/kW-yr credit
  with a penetration-saturation decline (`ERCOT_AS_SATURATION_*`), gated on
  `as_revenue_enabled`.
- **on (forecast endogenous):** the AS duty is priced *inside the dispatch
  reserve co-optimization* (§below), so the exogenous rate is **suppressed** to
  avoid double-counting; the entry credit is instead **derived from the solved
  co-opt's own reserve duals** — `ancillary.realized_storage_as_revenue_per_mw_yr`
  = Σ_t (storage cleared reserve MW)_t × (binding AS price)_t / fleet MW,
  threaded from the prior year via `runner.prior_results`. It is forward-valid
  (responds to fleet growth, AS requirement and spreads; zero when the co-opt
  did not price reserve — no measured award anywhere). `ercot_storage_as_endogenous`
  requires `energy_reserve_coopt`; in forecast with the multi-product AS co-opt
  it also requires `ercot_as_forward_requirement` (else the AS requirement is
  the silent-zero measured-plan fallback). See
  `docs/storage-as-withholding-attribution-2026-07.md`.

The *withholding* itself is not a new LP structure: storage headroom
`cap − Dis + Chg` already backs upward reserve in the co-opt's shared-headroom
rows (`_build_reserve_rows`), and the ERCOT reserve design marks storage
`storage_eligible=True`, so once `energy_reserve_coopt` is on in the forecast
runner the battery trades energy against AS on its own power cap and cannot
dump its full cap into the top arbitrage hours it must back AS in. The measured
per-hour storage AS reservation (`storage.reserve_storage_as_power`) stays
**backcast/calibration-only** (rule 13).

**Thermal AS** carries the identical reconciliation under
`ercot_thermal_as_endogenous` (the thermal analogue of the storage flag). When
on, the thermal retirement and new-entry screens
(`capacity.apply_economic_retirements` / `apply_economic_new_entry`) see the
**hourly binding reserve price derived from the co-opt's own reserve duals**
(`reserve_price_signal` / `reserve_price_signal_slow`, threaded via
`PriorYearResults`) and value each unit's per-hour best use
`max(0, price − mc, r)` — energy or reserve, never both on the same MW —
superseding both the annual per-fuel rate
(`ancillary.realized_thermal_as_revenue_per_mw_yr_by_fuel`, retained as the
fallback for callers without the hourly arrays) and the exogenous flat rate:
exactly one mechanism prices thermal AS. Chosen over simply gating
the exogenous credit off because the co-opt lifts the energy price (already in the
screens' energy margin) but *not* the direct reserve payment on a unit's held
headroom; the hourly max restores that real income without the double-count the
old annual headroom rate carried against the pro-forma energy margin. When the
co-opt is not running, the same hourly-max valuation runs off the post-solve
ORDC scarcity adder (`screen_reserve_value_enabled`, §5.2). Forecast-only
(capacity evolution never runs in backcast); keepers are byte-identical; same
`energy_reserve_coopt` / `ercot_as_forward_requirement` guards as the storage
flag. See `docs/storage-as-withholding-attribution-2026-07.md`.

Profitable techs are ranked by total margin (energy + capacity + AS − cost) and
built in merit order, but no single tech may take more than
`STORAGE_TECH_BUILD_SHARE_CAP` of one year's budget, so the build diversifies
across durations rather than the top-margin tech monopolizing it. Builds are
attributed to each tech's own learning curve (li-ion durations share one
curve; iron-air/flow/CAES each have their own). Subject to annual build cap
and cumulative ceiling per ISO (both now defined for ERCOT, CAISO, PJM,
NYISO, ISO-NE). Base-year fleet set by `storage_deployment`; all subsequent
growth is endogenous.

### 5.6 CCS Retrofit Screen

Beyond *new* `gas_cc_ccs` entry (§1.5.2), existing gas-CC units can be **retrofitted** with post-combustion capture (`model/capacity.py`, gated on `ccs_retrofit_available_year`, default 2028). Each year, every gas-CC unit with at least `ccs_retrofit_min_remaining_life` (15) years of useful life left is screened on **simple payback**: annual savings = carbon avoided + EAC/45Q revenue − margin loss from the higher heat rate (`ccs_retrofit_hr_penalty` = 12%) − the capture VOM adder (`ccs_retrofit_vom_adder` = $8/MWh). A unit retrofits when payback is shorter than its remaining life. Retrofit capex (`ccs_retrofit_capex_kw` ≈ $900/kW) follows the same Wright's-Law learning curve as new CCS, the emission rate drops by `ccs_retrofit_capture_rate` (90%), and total retrofits are capped at `ccs_retrofit_max_gw_per_year` (3 GW/yr) per ISO. This is a distinct capacity-evolution mechanism from retirement and new entry — an existing asset changes its characteristics in place.

### 5.7 Hydro Energy Budgets

Hydro is not a free-running thermal unit. When `hydro_monthly_energy` is supplied, the dispatch LP adds, per hydro generator per month, a two-sided **energy-budget** constraint `hydro_min ≤ Σ_{t∈month} P[g,t] ≤ hydro_max` (plus an optional run-of-river minimum-flow floor). The unit chooses *when* within the month to generate, not *how much* in total — an inter-temporal coupling like storage SOC, but on a monthly horizon.

### 5.8 Locational Capacity Deliverability (gated)

`ScenarioConfig.capacity_deliverability_limits` (GATED, default **off**,
byte-identical when off) makes the capacity economics locational instead of
system-wide, mirroring how a real RA market prices a binding LCR/CETO. It
consumes the `capacity-deliverability` clean datatype — each ISO's published
locational parameters (PJM CETO/CETL, MISO LRR/LCR/CIL, NYISO LCR/TSL,
ISO-NE LSR/MCL, CAISO LCR/MIC) — crosswalked from native capacity areas
(LDA/LRZ/locality/local-area) onto model zones by
`config/capacity_area_crosswalk.py`'s per-ISO resolver registry. This is a
**structural mechanism** (repo rule #1): it belongs regardless of backcast
fit, is never fitted to the residual, and is **never enabled in a keeper** —
preferring the published limit over a calibrated scalar can move the
backcast (rule #12), and that is expected, not a reason to revert.

**Part A — seam import override**
(`model/transmission.apply_deliverability_seam_limit`, called once at run
setup in `runner.py`). Where an ISO publishes a per-area *seam* import
limit into its boundary (today: CAISO branch-group Maximum Import
Capability, summed by the crosswalk to the `WECC_import` node), that
measured value replaces the calibrated system-wide simultaneous-import
`InterfaceLimit` cap. The target interface is identified structurally — the
limit whose every link originates at the import node — so the override is
ISO-agnostic; it is a no-op wherever no seam-labeled area or import node
exists (PJM/MISO/NYISO/ISO-NE CETL/CIL are internal transfer limits, not
seam limits, and feed Part B instead).

**Part B — locational capacity gate**
(`model/capacity.deliverability_headroom_by_zone` / `_zone_is_long`, wired
into `apply_economic_retirements`, `apply_economic_new_entry`, and
`model/storage.apply_storage_new_entry`; headroom is computed once per year
by `evolve_fleet` and shared across the three screens). For each model zone
that carries a published requirement, `headroom = deliverable_firm −
requirement`, where deliverable firm capacity is the zone's accredited
in-zone capacity (thermal at `1 − EFORd`, renewables and storage at their
capacity credit) plus the crosswalked import_limit into it. A zone with
`headroom > 0` is **long** (RA-saturated): the marginal capacity payment
there collapses, so thermal retires more readily, new entry is not pulled
forward, and storage's capacity-value term (§5.5) is scaled down by the
load-share-weighted fraction of the build landing in long zones. A **short**
zone (`headroom < 0`) is unaffected — the existing system-wide screens
apply. The gate is a strict no-op (zero headroom entries) when the flag is
off, the ISO has no clean partition (ERCOT is energy-only), or no zone
carries a requirement.

Crosswalk granularity is documented, not guessed: nested sub-areas (e.g.
PJM ATSI-Cleveland ⊂ ATSI) and multi-zone super-areas (PJM MAAC, MISO
subregional North/South, NYISO G-J, ISO-NE SENE) are excluded from the
per-zone sum to avoid double-counting, and areas the reduced-zone topology
cannot resolve (CAISO's Stockton/Kern LCR pockets, which straddle a
Path-15/26 boundary) are left `unmapped` rather than assigned by guess. See
`docs/capacity-deliverability-wiring.md` for the full per-ISO mapping table
and `tests/test_capacity_area_crosswalk.py` /
`tests/test_capacity_deliverability_wiring.py` for the coverage tests.

### 5.9 Capacity-Market Revenue — Fixed Price and the CR-1 Sloped Demand Curve

In a capacity-market ISO a qualifying resource earns a resource-adequacy
payment *outside* the energy market (Module M1), which the three
capacity-evolution screens credit as revenue: economic retirement (§5.2),
thermal new entry (§5.3), and storage new entry (§5.5). All three price
adequacy through **one seam** — `MarketDesign.capacity_price_per_firm_mw_yr`
(rule 19, one curve per ISO, no screen-specific curves) — which returns a
per-firm-MW-yr price that each screen multiplies by its own accreditation
(thermal via `thermal_accreditation_fraction`; storage `× ELCC(duration) ×
saturation derate`). Energy-only ERCOT (and any ISO absent from `MARKET_DESIGN`)
pays **zero** in every mode — scarcity already flows through its ORDC/VOLL energy
price.

**Per-ISO published-basis consistency (P-2B Option A).** Each capacity-market
ISO's requirement, supply ledger, curve position, curve dollar anchor, and
per-unit payment all sit on **that ISO's own published accreditation basis**
(`docs/handoffs/accreditation-basis-memo-2026-07-12.md` §4.1). Thermal
accreditation is resolved once, for both the adequacy ledger and the payment, by
`thermal_accreditation_fraction(fuel_type, eford, iso)`
(`THERMAL_ACCREDITATION_BASIS_BY_ISO`): `1 − EFORd` (UCAP — NYISO/MISO, the
default), the published **ELCC class rating** (PJM's 2025/26 CIFP reform —
`THERMAL_ELCC_CLASS_RATING_BY_ISO`, e.g. coal 0.83 / gas-CC 0.74 / gas-CT 0.60,
with a UCAP fallback for any class the ISO does not publish), **claimed
capability** (ISO-NE's FCM — the 5-yr median Seasonal Claimed Capability with **no**
forced-outage derate, since individual forced-outage risk is priced ex post through
Pay-for-Performance rather than the accredited MW; R5b, pairing-adjudication
2026-07-15 §1 — numerically `1.0` like ERCOT's basis but kept a distinct string
because the *reason* differs), or the seasonal rating (ERCOT's CDR — nameplate,
though ERCOT is energy-only so it never reaches the payment). Because the ledger and the payment price a unit through the **same**
resolver, they cannot diverge (so a class differential like PJM's gas-CT 0.60 vs
its 0.94 UCAP is paid on the basis it is counted on). Storage likewise reads its
ISO's published duration→credit ratings where one exists
(`STORAGE_ELCC_BY_DURATION_BY_ISO`, PJM's 4h 0.50 / 6h 0.58 / 8h 0.62 / 10h 0.72),
else the generic table — one mechanism, no double-derate. The requirement is
devintaged onto the ISO's published **Forecast Pool Requirement** of the matching
delivery year where one is published (`resolve_adequacy_requirement_mw` prefers
`firm_peak × FPR`; PJM 2025/26 = 0.9380, 2026/27 = 0.9170, 2027/28 = 0.9260),
falling back to `firm_peak × (1 + PRM) × icap_to_ucap_ratio` otherwise — so an ISO
with no published FPR is byte-identical to the pre-migration construction.

**Fixed mode (default).** The seam returns the flat `net_cone_per_kw_yr × 1000`,
the same per-ISO net-CONE anchor (CAISO 90 / PJM 100 / NYISO 110 / ISO-NE 95 /
MISO 80 $/kW-yr) every qualifying MW has always earned. The price does not
respond to the fleet.

**CR-1 sloped demand curve** (`ScenarioConfig.capacity_market_clearing`, GATED,
default **off**, byte-identical when off). When on, the fixed price is replaced
by the market's own **net-CONE-anchored sloped demand curve** evaluated at the
model's own accredited reserve position:

```
reserve_position = accredited_firm_capacity_mw / requirement_mw
capacity_price   = VRR_iso(reserve_position) × net_cone_curve_iso
```

`VRR_iso` is the published, normalized piecewise-linear curve
(`MarketDesign.demand_curve`, dimensionless `(reserve_ratio,
price/net-CONE)` points, flat-extrapolated past both ends: the price cap on the
left, the zero-cross on the right); `net_cone_curve_iso` is the ISO's *published*
net-CONE on the basis the auction clears in (PJM's is the **UCAP** net-CONE
77.431 $/kW-yr = 212.14 $/MW-day × 365/1000 — R1, replacing the legacy ICAP-annual
60.396 that mis-scaled the UCAP curve by PJM's ~0.78 factor), kept distinct from
the legacy fixed `net_cone_per_kw_yr` anchor so the default (fixed) path stays
byte-identical until the P-2A default flip reconciles them. The
`requirement_mw` and the accreditation are the **exact same** ones the
retirement reliability floor and the reserve-margin backstop compute
(`capacity_reserve_position` calls `resolve_adequacy_requirement_mw` — published
FPR where available, else `(1 + PRM) × ratio` — and `accredited_firm_capacity_mw`
— one requirement, one basis, rule 19); the runner computes the position **once**
on the entering-year fleet and threads the one value into all three screens. So the capacity price now *responds to the fleet*
the way real markets do — it collapses toward zero when the system is long (RA
saturated) and rises toward the cap when short — which a fixed price structurally
cannot.

Every curve number is a **published market-design parameter** (rule 13 — never a
fit target), sourced from the `capacity-market-demand-curve` datatype
(`data/raw/capacity-market/demand-curve`): PJM's VRR points + Net CONE + price
cap (2026/2027 BRA), NYISO's ICAP demand curve (2025-2026 NYCA reference point +
12% curve length, modeled annually), ISO-NE's FCA Net CONE + starting price
(FCA 18) with the reserve-position geometry from FCA 11's published curve, and
MISO's PRA Net CONE + gross CONE (the **seasonal** RBDC — see below). CAISO has no
centralized auction, so it keeps the fixed proxy in **both**
modes (re-cited to the CPM soft-offer cap / CPUC RA report — the documented
low-fidelity registry member). The encoded constants are reconciled against the
datatype in `tests/test_capacity_demand_curve.py`.

**MISO seasonal RBDC grain (RC-1C, prereq 4a).** MISO alone clears a *seasonal*
PRA (four seasons, $/MW-day, under the Reliability-Based Demand Curve from
PY2025-26), and the market settles capacity as a seasonal **SUM**:
`Σ_season ACP_season[$/MW-day] × days_season`. The seam reproduces that
construction — when a MISO curve carries a `seasonal_rbdc`
(`SeasonalRBDC`/`seasonal_rbdc_price_per_firm_mw_yr`), the price is the sum over
the four seasons (Summer 92 / Fall 91 / Winter 90 / Spring 92 = 365 days,
recovered from the published seasonal gross-CONE ÷ annual gross CONE) of the
season's RBDC evaluated at the reserve position × its days, replacing the annual
approximation. Each season's requirement point is the **flat daily net-CONE**
(annual N/C net-CONE 79,800 ÷ 365 = 218.63 $/MW-day — MISO publishes the seasonal
gross-CONE caps and the annual net-CONE, not a separate seasonal net-CONE), and
its cap fraction is `seasonal_gross_cone_daily ÷ daily_net` (Summer's is ≈6.3× —
summer packs the full annual gross CONE into 92 days). At the requirement (1.0)
the sum returns **exactly** the annual net-CONE (reducing to the annual curve); a
short position lifts each season toward its own gross-CONE cap. **One-position
limit (documented, not a bug):** the model holds ONE annual accredited position
and feeds all four seasons — with no seasonal accreditation basis (seasonal firm
MW) it cannot reproduce the observed seasonal price *concentration* (PY2025-26
summer $666.50 vs $33-92 the other seasons), over-stating at a short annual
position and under-stating at a long one; seasonal fleet accreditation is
explicitly **not** invented (rule 13). Pre-RBDC MISO years (PY2009-10 .. PY2024-25)
were a **vertical** curve capped at CONE (FERC ER23-2977) — represented as a
near-vertical step anchored on gross CONE, not a sloped shape.

**Curve eligibility (RC-1C).** A governance gate layered on the clearing gate:
`resolve_capacity_curve_eligible(iso)` (`CAPACITY_CURVE_ELIGIBLE_BY_ISO`) blocks an
ISO from pricing on its sloped curve until its accreditation-pairing basis is
owner-signed. **NYISO is INELIGIBLE** — its ICAP→UCAP translation-factor pairing
(R5a) is adjudicated but not owner-signed (`nyiso-neiso-capacity-pairing-
adjudication-2026-07-15.md` §3) — so even with the gate on and a vintage resolved,
NYISO prices on its **fixed** anchor; PJM/NEISO/MISO are eligible. `iso=None`
(pre-RC-1C call sites) and any unlisted ISO default eligible, so default paths are
byte-identical. The gate is default-off, so eligibility only bites under a per-ISO
curve-ON probe.

**Per-delivery-year vintages (RC-1B).** The curve above is each ISO's *reference*
delivery year; a forecast pricing a specific `year` under the CR-1 gate reads that
year's own published curve through `resolve_demand_curve_vintage(iso, year)`
(`MARKET_DESIGN_VINTAGES`). The seam consults it **only** when both `iso` and `year`
are supplied — every non-storage caller passes neither, so the price is
byte-identical; storage new entry is the one wiring that threads a year. Resolution
is a step function of the delivery-period start year: hold-first below the earliest
vintage, hold-last above the latest (the forward-carry a forecast uses). Anchors and
cap fractions come off the same `capacity-market-demand-curve` datatype on each ISO's
own convention — PJM 2021/22-2027/28 (UCAP net-CONE × 365/1000), NYISO 2021/22-2025/26
(NYCA Annual Reference Value for 2023/24-2025/26; 2021/22 & 2022/23 published neither
an annual net-CONE nor a cap, so they are `()`-shape flat-anchor vintages priced on
the NYCA reference point × 12), ISO-NE 2020/21-2027/28 (net-CONE × 12 on FCA 11's
reserve-position geometry), MISO PY2021/22-2025/26 (the pre-RBDC years
PY2021/22-2024/25 are **vertical-at-CONE** vintages anchored on North/Central gross
CONE — the LRZ 1-7 mean — with `seasonal_rbdc=None`; PY2025-26 carries the seasonal
RBDC and its North/Central anchor; the per-LRZ-only PY2026-27 is omitted, held to
PY2025-26). A delivery year that
publishes a net-CONE anchor but no normalizable shape (pre-CIFP PJM's absolute-MW
points; PJM 2025/26's missing price cap) carries `demand_curve=()` and prices on its
flat anchor (rule 13 — never fabricate an unpublished point). The vintage equal to
the registry reference reuses its exact curve/anchor object, so pricing that year is
byte-identical to the fixed registry curve. Every vintage number is reconciled
against the datatype in `tests/test_capacity_demand_curve.py`.

Capacity revenue (fixed or curve, labeled by source) is also reported per plant
in `results/plant_financials.py` (`capacity_revenue` +
`capacity_revenue_source`). **This session lands the mechanism default-off
only**; flipping the default is gated on the CR-2 auction-history validation
(`docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md` §3.3).
Explicitly out of scope for CR-1 (revisit on CR-2 evidence): full supply-curve
auction clearing with unit offers, CP/PAI penalties, Y-3 forward lag, and
locational LDA-specific curves (composes later with §5.8 part B).

-----

## 6. Parallelism & Performance

### 6.1 Parallel Execution

Independent work units: `(scenario_config, iso)` pairs. Within each work unit, years run sequentially (capacity evolution dependency).

```python
from concurrent.futures import ProcessPoolExecutor

def run_scenario_iso(config: ScenarioConfig, iso: str):
    """Run all 25 years for one scenario × one ISO. Sequential."""
    fleet = load_base_fleet(iso, config)
    for year in range(2026, 2051):
        cache_path = get_cache_path(iso, config.cache_key(), year)
        if cache_path.exists():
            results = load_cached(cache_path)
        else:
            fleet = evolve_fleet(fleet, results_prev, year, config)
            inputs = assemble_inputs(fleet, year, config)
            results = solve_dispatch(inputs)
            save_parquet(results, cache_path)
        results_prev = results
    return config.cache_key()

# Main runner
with ProcessPoolExecutor(max_workers=N_CORES) as pool:
    futures = []
    for config in scenario_configs:
        for iso in config.isos:
            futures.append(pool.submit(run_scenario_iso, config, iso))
    for f in as_completed(futures):
        print(f"Completed: {f.result()}")
```

### 6.2 Performance Targets

|Operation                                             |Target      |
|------------------------------------------------------|------------|
|LP matrix construction (1 ISO, 1 year)                |< 1 second  |
|LP solve (HiGHS, 1 ISO, 1 year, 8760 hrs)             |< 5 seconds |
|Full scenario-year (evolve + assemble + solve + cache)|< 10 seconds|
|Single scenario × 1 ISO × 25 years                    |< 5 minutes|
|Memory per LP solve                                   |< 2 GB      |
|20 scenarios × 2 ISOs on 8 cores                      |< 30 minutes|

### 6.3 Memory Management

Each worker builds and discards the LP per year. Do not accumulate LP objects across years. The HiGHS instance should be created fresh per solve (or cleared with `h.clear()`). Only the result arrays (dispatch, prices, emissions) persist in memory during the year-loop, and they’re written to Parquet immediately.

-----

## 7. Build Agent Instructions

### 7.1 Rules

1. **No magic numbers.** Every numeric value comes from `ScenarioConfig` or `constants.py` with a citation comment.
1. **No Python loops in the LP builder.** Vectorize with numpy/scipy.sparse. If writing `for t in range(8760)`, stop and restructure.
1. **Every input is a parameter.** If you’re tempted to hardcode a value, add it to `ScenarioConfig` with a default and a tier tag.
1. **Struct-of-arrays before LP construction.** Convert fleet objects to `FleetArrays` numpy arrays. The LP builder’s only imports from the data layer are arrays and scalars.
1. **Test each phase independently.** Trivial test cases before scaling up: 1 generator, 1 zone, 24 hours. Then 2 generators. Then full fleet.
1. **Parquet for all result storage.** No CSV, no HDF5, no pickle. Parquet with PyArrow, column types documented in a schema file.
1. **YAML for all configuration.** Scenario configs, sweep definitions, ISO topology — all YAML with Pydantic validation on load.
1. **Cache key = hash of full resolved config.** Not a human-readable name. The config.yaml saved alongside results provides readability.
1. **Log the full resolved config at the start of every run.** If a run produces unexpected results, the first diagnostic is “what config was actually used.”
1. **Renewables are decision variables.** They appear on the LHS of energy balance with zero marginal cost and upper bound = CF × capacity. They are NOT subtracted from demand on the RHS.

### 7.2 What NOT to Build

These remain firm:

- **No MIP.** Still pure LP — no binary variables. The commitment layer (§1.6) is a *heuristic screen between LP solves*, not a mixed-integer program; fractional dispatch within a committed unit is acceptable.
- No inter-hour generator ramp-rate constraints. Flag as future enhancement. (Note: online/offline reserve *classes* and a co-optimized reserve requirement exist — see below — but true MW/min ramp limits between hours do not.)
- No separate pricing model. Prices are LP duals. Period.
- No representative weeks or days. Full 8760 always.
- No convergence iteration in capacity evolution. One pass per year.
- No web framework or API server. CLI + YAML + Parquet files.

Originally listed here but **since built** (kept as LP, no MIP):

- ~~No unit commitment~~ → opt-in three-solve commitment heuristic, §1.6 (default off).
- ~~No stochastic outages, deterministic derate only~~ → forecast still uses statistical/deterministic derate; backcast adds a *historic* CAMPD outage overlay for calibration, §1.7 (forecast runs do not use it).
